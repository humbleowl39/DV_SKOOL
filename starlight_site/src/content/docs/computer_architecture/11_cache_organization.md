---
title: "Module 11 — 캐시 조직 & miss"
---

:::tip[학습 목표]
이 모듈을 마치면:

- **Apply** 물리 주소를 tag / index / block offset 으로 분해하고, S sets × W ways × B bytes 캐시 조직에 매핑할 수 있다.
- **Differentiate** 3C miss(compulsory / capacity / conflict)와 write-through / write-back 정책을 trade-off 기준으로 구분할 수 있다.
- **Analyze** replacement policy(LRU/PLRU/random), store buffer, MSHR(non-blocking cache)이 miss·reordering·MLP 에 미치는 영향을 분석할 수 있다.
- **Apply** AMAT = HitTime + MissRate × MissPenalty 로 캐시 조직의 성능을 정량화할 수 있다.
:::
:::note[사전 지식]
- [Module 10 — 캐시는 왜 존재하는가](../10_why_cache/) (Memory Wall, 계층, 지역성, 블록)
- 이진수·비트 분해, 가중 평균(AMAT)
:::

:::note[이 모듈의 위치]
[M10](../10_why_cache/)에서 _왜_ 캐시가 필요한지 봤다면, **M11(지금)** 은 캐시의 _내부 조직_ 과 miss·write 동작을 뜯어봅니다. 가상 메모리(TLB)와 DRAM 은 [M12](../12_vm_and_dram/)로 이어집니다.
:::
---

## 1. 작은 예 — 한 주소가 캐시에서 분해되어 hit/miss 되는 과정

가장 단순한 시나리오. 64-byte 블록(캐시가 메모리와 주고받는 최소 전송 단위 = 캐시 라인), 256 set(주소로 직접 골라지는 캐시 칸 그룹), 4-way(한 set 안에 블록을 둘 수 있는 자리 수 = associativity)캐시에서 물리 주소가 어떻게 tag(어느 블록인지 식별하는 상위 비트)/index(어느 set 인지 고르는 비트)/offset(블록 안에서 몇 번째 바이트인지) 으로 쪼개지고 hit 판정되는지 봅니다.

### 단계별 — 주소 분해

블록 크기 B = 64 byte → offset = log₂(64) = 6 bit. set 수 S = 256 → index = log₂(256) = 8 bit. 나머지가 tag.

```d2
direction: right

ADDR: "**Physical Address (32-bit)**\n[ Tag (18) | Index (8) | Offset (6) ]"
IDX: "**Index → set 선택**\n256 set 중 하나"
WAYS: "**그 set 의 4 ways**\n각 way 의 tag 와 비교"
HIT: "**tag 일치 + valid**\n→ HIT (offset 으로 블록 내 바이트 선택)"
MISS: "**불일치**\n→ MISS (하위 계층에서 블록 fetch)"

ADDR -> IDX -> WAYS
WAYS -> HIT: "match"
WAYS -> MISS: "no match"
```

### 단계별 의미

| Step | 무엇을 | 왜 |
|---|---|---|
| Offset(6 bit) | 64-byte 블록 내 바이트 위치 | 블록이 전송 단위(spatial locality) |
| Index(8 bit) | 256 set 중 하나 선택 | 직접 인덱싱으로 빠른 lookup |
| Tag(18 bit) | 그 set 의 4 way tag 와 병렬 비교 | 어느 블록인지 식별 |
| Hit/Miss | tag 일치+valid → hit | miss 면 하위 계층 fetch + 한 way 에 적재 |

### 비트 계산 pseudo code

```c
// 64-byte block, 256 sets, 4-way set-associative, 32-bit addr
#define BLOCK 64          // offset bits = 6
#define SETS  256         // index  bits = 8
// tag bits = 32 - 8 - 6 = 18
unsigned offset = addr & 0x3F;            // [5:0]
unsigned index  = (addr >> 6) & 0xFF;     // [13:6]
unsigned tag    = addr >> 14;             // [31:14]
// set[index] 의 4 way 중 tag 일치 && valid 인 way 가 있으면 HIT
```

:::note[여기서 잡아야 할 두 가지]
**(1) tag/index/offset 비트 수는 외우지 말고 매번 계산한다.** offset=log₂(블록크기), index=log₂(set수), 나머지가 tag — 캐시 파라미터가 바뀌면 다 바뀐다.<br>
**(2) "way" 는 같은 index 의 충돌을 흡수하는 자리다.** 4-way 면 같은 set 에 매핑되는 블록 4 개까지 공존 — associativity 가 conflict miss 를 줄이는 이유.
:::
---

## 2. 캐시 조직 — S sets × W ways × B bytes

캐시는 S 개 set, 각 set 당 W 개 way(라인), 라인당 B byte 로 구성됩니다. **블록(캐시 라인)** 은 계층 간 전송 단위(보통 64 byte)로 spatial locality 를 활용합니다. **set** 은 같은 index 로 매핑되는 W 개 라인의 그룹이며, 새 블록은 그 set 의 어느 way 든 차지할 수 있습니다. **way(associativity)** 는 conflict miss 와 lookup 복잡도 사이의 균형입니다 — direct-mapped(W=1)는 빠르지만 충돌이 잦고, fully associative(W=전체)는 최적이지만 비쌉니다.

---

## 3. 3C miss

```d2
direction: right

C1: "**Compulsory**\n첫 접근(cold)\n불가피"
C2: "**Capacity**\nworking set > 용량\n→ 용량 늘려야"
C3: "**Conflict**\n같은 set 충돌·축출 반복\n→ associativity 높이면 감소"
```

miss 는 세 종류로 분류됩니다. **Compulsory(cold)** 는 블록의 첫 접근으로 피할 수 없습니다. **Capacity** 는 working set 이 캐시 용량을 초과해 생기며, 용량을 늘려야 줄어듭니다. **Conflict** 는 두 블록이 같은 set 에 매핑되어 서로를 반복 축출할 때이며, full associativity 로 제거되고 associativity 를 높이면 감소합니다. 이 분류는 캐시 검증에서 "이 miss 가 정상(cold)인지 설계 부족(conflict)인지"를 가르는 도구입니다.

### 3.1 replacement policy — 어느 way 를 축출하느냐가 conflict miss 를 좌우한다

associativity 가 "같은 set 에 W 개 블록이 공존할 수 있다"까지 정한다면, _그 set 이 꽉 찼을 때 어느 way 를 내보낼지_ 를 정하는 것이 **replacement policy** 입니다. 이 선택이 conflict miss 와 직결됩니다 — 곧 다시 쓸 블록을 축출하면 그 블록을 또 miss 로 가져와야 하기 때문입니다.

이상적 정책은 "가장 멀리 미래에 쓰일 블록을 축출"(Belady)이지만 미래를 모르므로, 실제로는 _과거로 미래를 근사_ 하는 **LRU(Least Recently Used)** — 가장 오래 안 쓴 way 를 축출 — 가 기준입니다. temporal locality 가정상 오래 안 쓴 것이 곧 쓸 가능성도 낮다는 베팅입니다.

문제는 **true LRU 의 비용**입니다. W-way set 의 정확한 사용 순서를 유지하려면 각 접근마다 way 들의 순위를 갱신해야 하고, 이는 way 수가 늘수록 비싸집니다(순서를 표현하는 비트와 갱신 논리가 빠르게 증가). 그래서 실제 하드웨어는 true LRU 대신 **pseudo-LRU(PLRU)** — 트리 형태의 적은 비트로 "대략 오래된" way 를 고르는 근사 — 를 흔히 쓰고, 일부는 아예 **random** 축출을 씁니다(논리 거의 0, 평균적으로 나쁘지 않음). 즉 replacement 도 "정확도 vs 하드웨어 비용"의 trade-off 이며, 검증에서 "같은 접근 패턴인데 miss 가 예상보다 많다"면 replacement 가 LRU 가 아니라 PLRU/random 이어서 특정 패턴에서 불리한 way 를 축출하는 경우일 수 있습니다.

---

## 4. write 정책

| 정책 | hit 시 | miss 시 | trade-off |
|---|---|---|---|
| Write-through | 캐시 + 메모리 갱신 | — | 단순; 항상 일관; write bandwidth 큼 |
| Write-back | 캐시만 갱신, dirty bit 세움 | 라인 할당, 축출 시 writeback | bandwidth 적음; eviction 시 coherence 필요 |

현대 L1/L2 는 거의 항상 **write-back** + **write-allocate**(write miss 가 블록을 캐시에 할당)입니다. write-back 에서는 hit 시 메모리를 갱신하지 않으므로 dirty 라인이 축출되기 전까지 메모리가 stale 합니다 — coherence 검증의 핵심 포인트입니다.

### 4.1 store buffer — 메모리 reordering 의 물리적 근원 (메모리 모델의 출발점)

write 정책이 "store 가 캐시/메모리에 _어떻게_ 반영되는가"를 정한다면, 그보다 _앞_ 에 store 가 잠시 머무는 곳이 있습니다 — **store buffer**(또는 write buffer)입니다. 이 구조는 단순한 성능 최적화처럼 보이지만, 실은 _현대 메모리 모델 전체가 여기서 출발_ 하므로 깊이 볼 가치가 있습니다.

**왜 store buffer 가 존재하나.** store 명령이 retire 될 때 그 값을 곧바로 캐시에 쓰려면 캐시 write 포트가 비어 있어야 하고, 해당 라인이 캐시에 없으면(miss) 라인을 가져올 때까지 _코어 전체가 멈춰야_ 합니다. 이건 낭비입니다 — store 의 결과는 _이 코어 자신_ 에게는 이미 확정이고, 그 값이 다른 코어에 _언제_ 보이는지만 늦으면 됩니다. 그래서 코어는 retire 된 store 의 (주소, 데이터)를 **store buffer 라는 FIFO 에 넣고 즉시 다음 명령으로 진행**합니다. store buffer 는 라인이 준비되는 대로 _순서대로_ 캐시로 drain 합니다. 그동안 이 코어가 _자기 store 한 주소를 읽으면_, 아직 캐시에 안 내려간 값이라도 store buffer 에서 직접 꺼내 줍니다(store-to-load forwarding) — 자기 자신에겐 일관성이 유지됩니다.

**여기서 reordering 이 태어난다.** 문제는 _다른 코어_ 의 관점입니다. 내 store 가 store buffer 에 머무는 동안 그 값은 _아직 메모리 시스템에 보이지 않습니다._ 그런데 그 store _뒤_ 에 오는 내 **load** 는 store buffer 를 우회해 캐시/메모리에서 _먼저_ 값을 가져올 수 있습니다(load 는 자기 데이터를 빨리 받아야 성능이 나므로 막지 않음). 그 결과 _프로그램 순서상 store 가 먼저인데, 다른 코어가 보기엔 그 코어의 load 가 store 보다 먼저 일어난 것처럼_ 보입니다. 이것이 **store→load reordering** 이고, 그 물리적 근원이 바로 "store 는 buffer 에서 지연되지만 load 는 앞질러 나간다"입니다.

**그래서 x86 TSO 가 store→load 만 허용한다.** x86 의 메모리 모델 **TSO(Total Store Order)** 는 "store buffer 한 개가 만드는 reordering 만 허용하고 나머지는 금지"로 정확히 요약됩니다. store buffer 가 _FIFO_ 라 store 들끼리는 들어간 순서대로 drain 되므로 **store→store 순서는 보존**되고, load 는 자기보다 앞선 load·store 를 추월하지 않게 막혀 **load→load, load→store 도 보존**됩니다. 유일하게 깨지는 것이 "내 load 가 내 _이전_ store(아직 buffer 에 있음)를 추월"하는 **store→load** 한 가지입니다 — 즉 TSO 가 store→load 만 허용하는 것은 철학적 선택이 아니라 _store buffer 라는 하나의 구조가 만드는 딱 그 한 종류의 reordering_ 을 그대로 노출한 결과입니다.

**barrier/fence 가 실제로 하는 일.** 그러면 메모리 **barrier(fence)** 가 무엇을 하는지가 분명해집니다. TSO 에서 store→load 순서를 강제해야 하는 드문 지점(예: Dekker 류 상호 배제)에 넣는 full fence 는 **store buffer 를 drain** 합니다 — 즉 "buffer 에 쌓인 내 store 들이 모두 메모리 시스템에 보일(coherence 관점에서 globally visible) 때까지 기다린 뒤에야 다음 load 를 진행"하게 만들어, load 가 이전 store 를 추월하는 경로 자체를 막습니다. fence 는 _계산을 더 하는_ 게 아니라 _기존 store 들의 가시성을 강제로 앞당겨_ reordering 창을 닫는 것입니다.

**약한 모델로의 연결.** ARM·RISC-V 같은 **weak memory model** 은 여기서 한 발 더 나갑니다 — store buffer 의 비-FIFO drain, load 의 더 공격적 추측, 코어별 독립적 가시성 등을 허용해 store→load 뿐 아니라 _네 종류 reordering 전부_(load→load, load→store, store→store, store→load)를 기본 허용하고, 필요할 때만 명시적 barrier 로 순서를 겁니다. 그래서 x86 에서 우연히 동작하던 lock-free 코드가 ARM 에서 깨집니다. 이 _4종 reordering 의 정확한 ARM 규칙·multi-copy atomicity·DMB/DSB/acquire-release_ 는 [ARM 메모리 모델 M04](../../cpu_arm/04_memory_model_barriers/)에서, 일관성 프로토콜 자체는 [Cache Coherence](../../cache_coherence/)에서 다룹니다. 핵심만 기억하면: **store buffer 가 reordering 을 낳고, fence 가 그 buffer 를 drain 한다.**

### 4.2 MSHR 과 non-blocking cache — miss 중에도 hit 을 서비스한다

지금까지 miss 를 "하위 계층에서 블록을 가져오는 것"으로만 봤지만, _그 가져오는 동안 캐시가 무엇을 하느냐_ 가 성능을 가릅니다. 단순한 **blocking cache** 는 miss 가 해소될 때까지(수십~수백 사이클) 그 캐시를 잠가, 뒤따르는 _hit 일 수도 있는_ 접근까지 전부 멈춥니다 — long-latency miss 한 번이 독립적인 후속 접근들을 모두 인질로 잡습니다.

**non-blocking(lockup-free) cache** 는 이를 깨려고 **MSHR(Miss Status Handling Register)** 를 둡니다. miss 가 나면 "어느 라인을, 어느 명령을 위해, 어디로 채워야 하는지"의 메타데이터를 MSHR 한 항목에 기록하고 _그 라인 fetch 를 백그라운드로 진행_ 시킨 뒤, 캐시는 _다음 접근을 계속 서비스_ 합니다 — 후속이 hit 이면 즉시 처리하고, _다른_ 라인의 miss 면 또 다른 MSHR 항목을 잡아 _여러 miss 를 동시에 in-flight_ 로 둡니다. 같은 라인에 대한 두 번째 miss(secondary miss)는 기존 MSHR 항목에 합쳐져 한 번의 fill 로 둘 다 만족됩니다.

이 "여러 miss 를 겹쳐서 처리"가 곧 **MLP(Memory-Level Parallelism)** 입니다. MSHR 항목이 N 개면 동시에 N 개의 DRAM 왕복을 겹칠 수 있어, miss latency 가 _직렬로 합산_ 되지 않고 _병렬로 겹쳐_ 실질 지연이 크게 줄어듭니다. OoO 코어(M07)가 miss 한 load 를 건너뛰고 독립 명령을 실행하는 것과 MSHR 의 다중 miss 처리가 맞물려야 비로소 메모리 병렬성이 살아납니다 — MSHR 가 부족하면 코어가 아무리 OoO 라도 그만큼만 miss 를 겹칠 수 있어 거기서 막힙니다. 실측 MSHR 규모와 LSU 연계는 [ARM Microarchitecture M07](../../cpu_arm/07_microarchitecture/)에서 다룹니다.

---

## 5. 디테일 — AMAT, write-back stale, prefetching

### 5.1 AMAT — 계층 성능의 정량화

평균 메모리 접근 시간(AMAT)은 계층을 가중 평균으로 묶습니다.

```
AMAT = Hit Time + Miss Rate × Miss Penalty
// 다단계:
AMAT = HitTime_L1 + MissRate_L1 × (HitTime_L2 + MissRate_L2 × (… DRAM …))
```

이 식이 보여주는 것은 _miss rate 를 줄이는 것_ 과 _miss penalty 를 줄이는 것_ 이 모두 유효한 최적화 축이라는 점입니다. associativity 를 높이면 conflict miss(=miss rate)가 줄지만 hit time 이 늘 수 있어, 두 항의 trade-off 를 봐야 합니다.

### 5.2 write-back 의 stale 메모리와 coherence

write-back 캐시는 hit 시 메모리를 갱신하지 않으므로, dirty 라인이 캐시에만 최신 값을 가집니다. 다른 agent(다른 코어·DMA·가속기)가 같은 주소를 읽으면 stale 한 메모리를 볼 수 있어, coherence 프로토콜이 dirty 라인을 snoop(다른 캐시들에 "이 주소 가진 곳 있나" 물어보는 조회)해 최신 값을 전달해야 합니다. 검증에서 reference model 은 "이 시점의 진짜 최신 값이 캐시(dirty)에 있는가 메모리에 있는가"를 추적해야 하며, 이는 [cache coherence 토픽](../../cache_coherence/)으로 이어집니다.

### 5.3 hardware prefetching — compulsory/capacity miss 를 선제적으로 줄이기

3C 분류에서 compulsory miss 를 "첫 접근이라 불가피"라고 했지만, 이는 _수동적으로 기다릴 때_ 의 이야기입니다. 현대 캐시 성능의 큰 축 하나가 **hardware prefetcher** — 미래에 쓸 라인을 _접근하기 전에 미리_ 가져와 miss 를 hit 으로 바꾸는 것입니다. "불가피한 첫 접근"도 _그 접근이 일어나기 전_ 에 미리 fetch 해 두면 latency 가 숨겨집니다.

원리는 접근 _패턴을 관찰해 다음 주소를 예측_ 하는 것입니다.

- **next-line / sequential**: 한 라인을 접근하면 곧바로 다음 라인도 가져옵니다 — 순차 스캔(배열 순회, memcpy)에 효과적.
- **stride prefetcher**: 접근 주소의 _간격(stride)_ 이 일정하면(예: 구조체 배열을 일정 stride 로 순회) 그 stride 를 학습해 여러 칸 앞을 미리 fetch.
- **stream prefetcher**: 여러 개의 순차 스트림을 동시에 추적해 각각 앞서 fetch.

이들이 compulsory miss(처음 보는 라인이라도 패턴상 곧 올 것을 예측)와 capacity miss(곧 쓸 데이터를 미리 끌어와 demand miss 시점 단축)를 _선제적으로_ 줄입니다. 다만 공짜는 아닙니다 — 예측이 틀리면 안 쓸 라인을 가져와 _유용한 라인을 축출_ (cache pollution)하고 대역폭을 낭비합니다. 그래서 prefetcher 는 정확도(useful prefetch 비율)와 적시성(너무 일러도 늦어도 안 됨)으로 평가됩니다. 검증·성능 분석에서 "접근 패턴은 똑같은데 miss rate 가 기대보다 낮다"면 prefetcher 가 동작 중인 것이고, 반대로 _불규칙 접근_(포인터 추적, 해시)에서 성능이 안 오르면 prefetcher 가 패턴을 못 잡아서일 수 있습니다.

---

## 6. 흔한 오해 와 DV 디버그 체크리스트

### 흔한 오해

:::danger[❓ 오해 1 — 'write-back 캐시면 메모리가 항상 최신이다']
**실제**: write-back 은 hit 시 캐시만 갱신하고 dirty bit 만 세웁니다. 축출 전까지 메모리는 stale 하며, 진짜 최신 값은 dirty 라인(캐시)에 있습니다. coherence 검증에서 이를 빠뜨리면 기대값이 틀립니다.<br>
**왜 헷갈리는가**: "쓰면 메모리에 반영" 이라는 write-through 직관을 write-back 에 잘못 적용해서.
:::
:::danger[❓ 오해 2 — 'associativity 를 높이면 무조건 빨라진다']
**실제**: associativity 증가는 conflict miss(miss rate)를 줄이지만 hit time 과 전력을 늘립니다. AMAT = HitTime + MissRate × MissPenalty 에서 두 항의 trade-off — 무한정 높이는 것이 답은 아닙니다.<br>
**왜 헷갈리는가**: "miss 가 줄면 빠르다" 만 보고 hit time 증가를 놓쳐서.
:::
### DV 디버그 체크리스트

| 증상 | 1차 의심 | 어디 보나 |
|---|---|---|
| 같은 주소 다른 시점 다른 hit/miss | 3C 중 conflict(같은 set 축출 반복) | index 충돌하는 접근 패턴, associativity, replacement |
| 다른 agent 가 stale 값 읽음 | write-back dirty 라인 미반영(coherence) | snoop/dirty 추적, [cache coherence](../../cache_coherence/) |
| 주소 분해 오류로 잘못된 set 접근 | tag/index/offset 비트 폭 계산 오류 | 블록·set 크기로 비트 폭 재계산 |
| 같은 패턴인데 miss 가 예상보다 많음 | replacement 가 LRU 아닌 PLRU/random | replacement policy, 특정 패턴의 불리한 축출 |
| long-latency miss 가 후속 hit 까지 막음 | blocking cache 또는 MSHR 고갈 | MSHR 항목 수, non-blocking 동작 |

---

## 7. 핵심 정리 (Key Takeaways)

- **주소 분해**: offset=log₂(블록), index=log₂(set), 나머지=tag — 파라미터마다 매번 계산. way 수는 분해에 무관.
- **3C miss**: compulsory(cold, 불가피), capacity(용량 부족), conflict(set 충돌, associativity·replacement 로 완화).
- **write-back + write-allocate** 가 표준; hit 시 캐시만 갱신 → dirty 라인이 최신, 메모리는 stale.
- **store buffer** 가 store→load reordering 의 물리적 근원; fence 가 buffer 를 drain 해 순서를 강제.
- **MSHR(non-blocking cache)** 가 여러 miss 를 겹쳐 MLP 를 살린다; OoO 와 맞물려야 효과.
- **AMAT = HitTime + MissRate × MissPenalty** — miss rate 와 miss penalty 둘 다 최적화 축.

:::caution[실무 주의점]
- write-back 캐시 검증은 dirty 라인이 "진짜 최신"이라는 점을 reference model 에 반영.
- coherence 가 얽히면 [cache coherence 토픽](../../cache_coherence/)으로 escalate.
- "같은 패턴 다른 miss"는 replacement(PLRU/random) 또는 MSHR 고갈을 의심.
:::
### 7.1 자가 점검

:::tip[🤔 Q1 — 주소 분해 (Bloom: Apply)]
128-byte 블록, 512 set, 8-way 캐시(40-bit 물리 주소)에서 tag/index/offset 비트 수는?
<details>
<summary>정답</summary>

offset = log₂(128) = 7 bit (블록 내 바이트). index = log₂(512) = 9 bit (set 선택). tag = 40 − 9 − 7 = 24 bit. way 수(8)는 _주소 분해에 영향을 주지 않습니다_ — 같은 index 의 8 way 는 tag 비교로 구분되며, way 수는 한 set 이 흡수할 수 있는 충돌 블록 수만 정합니다. 즉 [Tag 24 | Index 9 | Offset 7] = 40 bit. associativity 를 8 에서 16 으로 바꿔도(set 수 고정 시) 이 비트 분해는 동일하고, set 수를 바꾸면 index/tag 가 바뀝니다.

</details>
:::
### 7.2 출처

**External**
- Hennessy & Patterson, *Computer Architecture: A Quantitative Approach* — 캐시, 3C, AMAT, replacement, MSHR
- Patterson & Hennessy, *Computer Organization and Design* — 캐시 조직, write 정책

---

## 다음 모듈

→ [Module 12 — 가상 메모리 & DRAM](../12_vm_and_dram/): 캐시 lookup 전에 가상 주소를 물리 주소로 바꾸는 TLB·page walk·page fault, 그리고 그 아래 DRAM 의 row hit/miss 비용과 메모리 컨트롤러의 재정렬을 본다.

[퀴즈 풀어보기 →](../quiz/11_cache_organization_quiz/)
