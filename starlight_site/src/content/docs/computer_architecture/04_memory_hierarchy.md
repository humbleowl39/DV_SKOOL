---
title: "Module 04 — 메모리 계층 (Cache & DRAM)"
---

:::tip[학습 목표]
이 모듈을 마치면:

- **Explain** Memory Wall 의 원인과, 작고 빠른 저장소를 크고 느린 저장소 앞에 두는 메모리 계층의 동기를 설명할 수 있다.
- **Apply** 물리 주소를 tag / index / block offset 으로 분해하고, S sets × W ways × B bytes 캐시 조직에 매핑할 수 있다.
- **Differentiate** 3C miss(compulsory / capacity / conflict)와 write-through / write-back 정책을 trade-off 기준으로 구분할 수 있다.
- **Describe** TLB 와 page table walk, page fault 처리가 가상→물리 주소 변환에서 하는 역할을 기술할 수 있다.
- **Analyze** DRAM 의 row hit vs row miss 비용 차이와, 메모리 컨트롤러가 왜 요청을 재정렬하는지 분석할 수 있다.
:::
:::note[사전 지식]
- [Module 02 — Pipeline & Hazard](../02_pipeline_hazard/) (cache miss = stall 원천)
- 이진수·비트 분해, 가중 평균(AMAT)
:::
---

## 1. Why care? — "재정렬은 버그가 아니다"를 증명하려면 메모리 계층을 알아야

### 1.1 시나리오 — 메모리 컨트롤러의 재정렬을 mismatch 로 오인

DMA 엔진이나 메모리 컨트롤러를 검증할 때, 발행한 요청 순서와 DRAM 에 도달하는 순서가 다르게 나타나는 경우가 흔합니다. 메모리 컨트롤러는 같은 DRAM row 를 노리는 요청을 모아 처리(row hit 최대화)하려고 의도적으로 순서를 바꿉니다. row hit(이미 열린 row)는 CAS 만으로 빠르지만, row miss 는 precharge + RAS + CAS 로 ~28–40 ns 가 더 듭니다. 이 비용 차이를 모르면 정상적인 성능 최적화(재정렬)를 프로토콜 위반이나 버그로 오인합니다.

또한 캐시를 검증할 때 "왜 같은 주소가 어떤 때는 빠르고 어떤 때는 느린가"를 설명하려면 3C miss(compulsory/capacity/conflict)와 write-back 의 dirty 라인 동작을 알아야 합니다. write-back 캐시는 hit 시 메모리를 갱신하지 않고 dirty bit 만 세우므로, eviction 전까지 메모리는 stale 합니다 — 이를 모르면 coherence 검증에서 기대값을 잘못 만듭니다.

이 모듈은 메모리 계층의 비용 구조를 세워, 검증에서 "정상 최적화"와 "진짜 버그"를 가르는 기준을 제공합니다.

---

## 2. Intuition — 책상·책장·도서관, 과 한 장 그림

:::tip[💡 한 줄 비유]
**메모리 계층** ≈ **책상 → 책장 → 도서관**.<br>
지금 보는 책은 책상 위(L1, 빠르지만 작음)에, 자주 보는 책은 책장(L2/L3)에, 나머지는 도서관(DRAM)에 둔다. 가까울수록 빠르고 작다. 캐시는 "방금 쓴 것/근처의 것을 또 쓸 것"이라는 _지역성(locality)_ 에 베팅한 자동 책상 정리이며, 베팅이 빗나가면 도서관까지 다녀와야 한다(miss).
:::
### 한 장 그림 — 지연/용량의 피라미드

```d2
direction: down

RF: "Register file\n~1 cycle / ~1 KB"
L1: "L1 cache\n~4 cycles / ~32–64 KB"
L2: "L2 cache\n~12 cycles / ~256 KB–1 MB"
L3: "L3 (LLC)\n~40 cycles / ~4–64 MB"
DRAM: "DRAM\n~100+ cycles / GBs"
NVMe: "Storage (NVMe)\n~10 µs / TBs"

RF -> L1 -> L2 -> L3 -> DRAM -> NVMe: "느려지고 커진다"
```

### 왜 계층인가 — Design rationale

프로세서 사이클 시간과 메모리 접근 시간은 1980년대 이후 100–1000× 로 벌어졌습니다(Memory Wall). 단일 메모리로는 빠르거나(작음) 크거나(느림) 둘 중 하나만 가능합니다. 계층은 세 요구의 교집합입니다. 첫째, 대부분의 접근을 빠르게 만들되 전체 용량은 커야 한다 → 빠른 작은 캐시 + 느린 큰 DRAM. 둘째, 프로그램은 시간/공간 지역성을 가지므로 최근/근처 데이터를 가까이 두면 적중률이 높다 → 블록 단위 캐싱. 셋째, 비용을 감당해야 한다 → 비싼 SRAM 은 작게, 싼 DRAM 은 크게. 이 균형이 곧 계층 구조의 디자인 결정입니다.

---

## 3. 작은 예 — 한 주소가 캐시에서 분해되어 hit/miss 되는 과정

가장 단순한 시나리오. 64-byte 블록, 256 set, 4-way 캐시에서 물리 주소가 어떻게 tag/index/offset 으로 쪼개지고 hit 판정되는지 봅니다.

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

## 4. 일반화 — 캐시 조직, 3C miss, write 정책, TLB, DRAM

### 4.1 캐시 조직 — S sets × W ways × B bytes

캐시는 S 개 set, 각 set 당 W 개 way(라인), 라인당 B byte 로 구성됩니다. **블록(캐시 라인)** 은 계층 간 전송 단위(보통 64 byte)로 spatial locality 를 활용합니다. **set** 은 같은 index 로 매핑되는 W 개 라인의 그룹이며, 새 블록은 그 set 의 어느 way 든 차지할 수 있습니다. **way(associativity)** 는 conflict miss 와 lookup 복잡도 사이의 균형입니다 — direct-mapped(W=1)는 빠르지만 충돌이 잦고, fully associative(W=전체)는 최적이지만 비쌉니다.

#### LLC(L3) 는 왜 생겼고, inclusion policy 가 무엇인가

피라미드 그림의 맨 아래 캐시인 **LLC(Last-Level Cache, 흔히 공유 L3)** 가 따로 존재하는 데는 두 가지 압력이 있습니다. 첫째, **off-chip bandwidth wall** — DRAM 으로 나가는 핀 대역폭은 코어 수만큼 늘릴 수 없으므로, 칩 위에 크고 느린 SRAM 한 층을 더 두어 DRAM 트래픽을 흡수합니다(L1/L2 보다 크지만 DRAM 보다 빠름). 둘째, **코어 간 공유** — 멀티코어가 공유 데이터를 각자의 사설 캐시에만 두면 중복·비효율이 크므로, 모든 코어가 공유하는 한 층(LLC)을 두어 공유 working set 을 한 번만 담고 코어 간 데이터 교환의 접점으로 씁니다.

여기서 갈리는 설계 선택이 **inclusion policy** — LLC 가 상위 캐시(L1/L2)의 내용을 어떻게 포함하느냐입니다.

- **Inclusive**: 상위 캐시에 있는 라인은 _반드시_ LLC 에도 있습니다. coherence 검증이 단순해집니다 — 다른 코어가 어떤 라인을 가졌는지 알려면 LLC 만 보면 되고(snoop filter 역할), LLC 에서 한 라인을 축출하면 상위 캐시에서도 그 라인을 _back-invalidate_ 해야 합니다.
- **Exclusive**: 한 라인은 상위 캐시 _또는_ LLC 중 한 곳에만 있어 중복을 없애 유효 용량을 키웁니다. 대신 라인 추적이 복잡해집니다.
- **NINE(Non-Inclusive Non-Exclusive)**: 둘을 강제하지 않는 중간 정책으로, 상위에 있는 라인이 LLC 에 있을 수도 없을 수도 있습니다.

inclusion policy 의 coherence 함의(왜 inclusive 가 snoop 을 줄이는지, exclusive 가 어떤 추가 추적을 요구하는지)는 깊은 주제이므로 여기서는 "셋이 존재하고 coherence 와 직결된다"까지만 짚고, 전체 treatment 는 [Cache Coherence M04 — I/O coherency & LLC](../../cache_coherence/04_io_coherency_llc/)에서 다룹니다.

### 4.2 3C miss

```d2
direction: right

C1: "**Compulsory**\n첫 접근(cold)\n불가피"
C2: "**Capacity**\nworking set > 용량\n→ 용량 늘려야"
C3: "**Conflict**\n같은 set 충돌·축출 반복\n→ associativity 높이면 감소"
```

miss 는 세 종류로 분류됩니다. **Compulsory(cold)** 는 블록의 첫 접근으로 피할 수 없습니다. **Capacity** 는 working set 이 캐시 용량을 초과해 생기며, 용량을 늘려야 줄어듭니다. **Conflict** 는 두 블록이 같은 set 에 매핑되어 서로를 반복 축출할 때이며, full associativity 로 제거되고 associativity 를 높이면 감소합니다. 이 분류는 캐시 검증에서 "이 miss 가 정상(cold)인지 설계 부족(conflict)인지"를 가르는 도구입니다.

#### replacement policy — 어느 way 를 축출하느냐가 conflict miss 를 좌우한다

associativity 가 "같은 set 에 W 개 블록이 공존할 수 있다"까지 정한다면, _그 set 이 꽉 찼을 때 어느 way 를 내보낼지_ 를 정하는 것이 **replacement policy** 입니다. 이 선택이 conflict miss 와 직결됩니다 — 곧 다시 쓸 블록을 축출하면 그 블록을 또 miss 로 가져와야 하기 때문입니다.

이상적 정책은 "가장 멀리 미래에 쓰일 블록을 축출"(Belady)이지만 미래를 모르므로, 실제로는 _과거로 미래를 근사_ 하는 **LRU(Least Recently Used)** — 가장 오래 안 쓴 way 를 축출 — 가 기준입니다. temporal locality 가정상 오래 안 쓴 것이 곧 쓸 가능성도 낮다는 베팅입니다.

문제는 **true LRU 의 비용**입니다. W-way set 의 정확한 사용 순서를 유지하려면 각 접근마다 way 들의 순위를 갱신해야 하고, 이는 way 수가 늘수록 비싸집니다(순서를 표현하는 비트와 갱신 논리가 빠르게 증가). 그래서 실제 하드웨어는 true LRU 대신 **pseudo-LRU(PLRU)** — 트리 형태의 적은 비트로 "대략 오래된" way 를 고르는 근사 — 를 흔히 쓰고, 일부는 아예 **random** 축출을 씁니다(논리 거의 0, 평균적으로 나쁘지 않음). 즉 replacement 도 "정확도 vs 하드웨어 비용"의 trade-off 이며, 검증에서 "같은 접근 패턴인데 miss 가 예상보다 많다"면 replacement 가 LRU 가 아니라 PLRU/random 이어서 특정 패턴에서 불리한 way 를 축출하는 경우일 수 있습니다.

### 4.3 write 정책

| 정책 | hit 시 | miss 시 | trade-off |
|---|---|---|---|
| Write-through | 캐시 + 메모리 갱신 | — | 단순; 항상 일관; write bandwidth 큼 |
| Write-back | 캐시만 갱신, dirty bit 세움 | 라인 할당, 축출 시 writeback | bandwidth 적음; eviction 시 coherence 필요 |

현대 L1/L2 는 거의 항상 **write-back** + **write-allocate**(write miss 가 블록을 캐시에 할당)입니다. write-back 에서는 hit 시 메모리를 갱신하지 않으므로 dirty 라인이 축출되기 전까지 메모리가 stale 합니다 — coherence 검증의 핵심 포인트입니다.

#### store buffer — 메모리 reordering 의 물리적 근원 (메모리 모델의 출발점)

write 정책이 "store 가 캐시/메모리에 _어떻게_ 반영되는가"를 정한다면, 그보다 _앞_ 에 store 가 잠시 머무는 곳이 있습니다 — **store buffer**(또는 write buffer)입니다. 이 구조는 단순한 성능 최적화처럼 보이지만, 실은 _현대 메모리 모델 전체가 여기서 출발_ 하므로 깊이 볼 가치가 있습니다.

**왜 store buffer 가 존재하나.** store 명령이 retire 될 때 그 값을 곧바로 캐시에 쓰려면 캐시 write 포트가 비어 있어야 하고, 해당 라인이 캐시에 없으면(miss) 라인을 가져올 때까지 _코어 전체가 멈춰야_ 합니다. 이건 낭비입니다 — store 의 결과는 _이 코어 자신_ 에게는 이미 확정이고, 그 값이 다른 코어에 _언제_ 보이는지만 늦으면 됩니다. 그래서 코어는 retire 된 store 의 (주소, 데이터)를 **store buffer 라는 FIFO 에 넣고 즉시 다음 명령으로 진행**합니다. store buffer 는 라인이 준비되는 대로 _순서대로_ 캐시로 drain 합니다. 그동안 이 코어가 _자기 store 한 주소를 읽으면_, 아직 캐시에 안 내려간 값이라도 store buffer 에서 직접 꺼내 줍니다(store-to-load forwarding) — 자기 자신에겐 일관성이 유지됩니다.

**여기서 reordering 이 태어난다.** 문제는 _다른 코어_ 의 관점입니다. 내 store 가 store buffer 에 머무는 동안 그 값은 _아직 메모리 시스템에 보이지 않습니다._ 그런데 그 store _뒤_ 에 오는 내 **load** 는 store buffer 를 우회해 캐시/메모리에서 _먼저_ 값을 가져올 수 있습니다(load 는 자기 데이터를 빨리 받아야 성능이 나므로 막지 않음). 그 결과 _프로그램 순서상 store 가 먼저인데, 다른 코어가 보기엔 그 코어의 load 가 store 보다 먼저 일어난 것처럼_ 보입니다. 이것이 **store→load reordering** 이고, 그 물리적 근원이 바로 "store 는 buffer 에서 지연되지만 load 는 앞질러 나간다"입니다.

**그래서 x86 TSO 가 store→load 만 허용한다.** x86 의 메모리 모델 **TSO(Total Store Order)** 는 "store buffer 한 개가 만드는 reordering 만 허용하고 나머지는 금지"로 정확히 요약됩니다. store buffer 가 _FIFO_ 라 store 들끼리는 들어간 순서대로 drain 되므로 **store→store 순서는 보존**되고, load 는 자기보다 앞선 load·store 를 추월하지 않게 막혀 **load→load, load→store 도 보존**됩니다. 유일하게 깨지는 것이 "내 load 가 내 _이전_ store(아직 buffer 에 있음)를 추월"하는 **store→load** 한 가지입니다 — 즉 TSO 가 store→load 만 허용하는 것은 철학적 선택이 아니라 _store buffer 라는 하나의 구조가 만드는 딱 그 한 종류의 reordering_ 을 그대로 노출한 결과입니다.

**barrier/fence 가 실제로 하는 일.** 그러면 메모리 **barrier(fence)** 가 무엇을 하는지가 분명해집니다. TSO 에서 store→load 순서를 강제해야 하는 드문 지점(예: Dekker 류 상호 배제)에 넣는 full fence 는 **store buffer 를 drain** 합니다 — 즉 "buffer 에 쌓인 내 store 들이 모두 메모리 시스템에 보일(coherence 관점에서 globally visible) 때까지 기다린 뒤에야 다음 load 를 진행"하게 만들어, load 가 이전 store 를 추월하는 경로 자체를 막습니다. fence 는 _계산을 더 하는_ 게 아니라 _기존 store 들의 가시성을 강제로 앞당겨_ reordering 창을 닫는 것입니다.

**약한 모델로의 연결.** ARM·RISC-V 같은 **weak memory model** 은 여기서 한 발 더 나갑니다 — store buffer 의 비-FIFO drain, load 의 더 공격적 추측, 코어별 독립적 가시성 등을 허용해 store→load 뿐 아니라 _네 종류 reordering 전부_(load→load, load→store, store→store, store→load)를 기본 허용하고, 필요할 때만 명시적 barrier 로 순서를 겁니다. 그래서 x86 에서 우연히 동작하던 lock-free 코드가 ARM 에서 깨집니다. 이 _4종 reordering 의 정확한 ARM 규칙·multi-copy atomicity·DMB/DSB/acquire-release_ 는 [ARM 메모리 모델 M04](../../cpu_arm/04_memory_model_barriers/)에서, 일관성 프로토콜 자체는 [Cache Coherence](../../cache_coherence/)에서 다룹니다. 핵심만 기억하면: **store buffer 가 reordering 을 낳고, fence 가 그 buffer 를 drain 한다.**

#### MSHR 과 non-blocking cache — miss 중에도 hit 을 서비스한다

지금까지 miss 를 "하위 계층에서 블록을 가져오는 것"으로만 봤지만, _그 가져오는 동안 캐시가 무엇을 하느냐_ 가 성능을 가릅니다. 단순한 **blocking cache** 는 miss 가 해소될 때까지(수십~수백 사이클) 그 캐시를 잠가, 뒤따르는 _hit 일 수도 있는_ 접근까지 전부 멈춥니다 — long-latency miss 한 번이 독립적인 후속 접근들을 모두 인질로 잡습니다.

**non-blocking(lockup-free) cache** 는 이를 깨려고 **MSHR(Miss Status Handling Register)** 를 둡니다. miss 가 나면 "어느 라인을, 어느 명령을 위해, 어디로 채워야 하는지"의 메타데이터를 MSHR 한 항목에 기록하고 _그 라인 fetch 를 백그라운드로 진행_ 시킨 뒤, 캐시는 _다음 접근을 계속 서비스_ 합니다 — 후속이 hit 이면 즉시 처리하고, _다른_ 라인의 miss 면 또 다른 MSHR 항목을 잡아 _여러 miss 를 동시에 in-flight_ 로 둡니다. 같은 라인에 대한 두 번째 miss(secondary miss)는 기존 MSHR 항목에 합쳐져 한 번의 fill 로 둘 다 만족됩니다.

이 "여러 miss 를 겹쳐서 처리"가 곧 **MLP(Memory-Level Parallelism)** 입니다. MSHR 항목이 N 개면 동시에 N 개의 DRAM 왕복을 겹칠 수 있어, miss latency 가 _직렬로 합산_ 되지 않고 _병렬로 겹쳐_ 실질 지연이 크게 줄어듭니다. OoO 코어(M03)가 miss 한 load 를 건너뛰고 독립 명령을 실행하는 것과 MSHR 의 다중 miss 처리가 맞물려야 비로소 메모리 병렬성이 살아납니다 — MSHR 가 부족하면 코어가 아무리 OoO 라도 그만큼만 miss 를 겹칠 수 있어 거기서 막힙니다. 실측 MSHR 규모와 LSU 연계는 [ARM Microarchitecture M07](../../cpu_arm/07_microarchitecture/)에서 다룹니다.

### 4.4 TLB 와 주소 변환

가상 주소는 캐시 lookup 전(VIPT/PIPT 캐시)에 물리 주소로 변환되어야 합니다. **TLB(Translation Lookaside Buffer)** 는 최근 가상→물리 페이지 매핑의 작고 빠른 fully-associative 캐시입니다.

##### VIPT 가 TLB 변환과 병렬일 수 있는 이유, 그리고 aliasing 문제

캐시 lookup 은 두 일을 합니다 — index 로 set 을 고르고, tag 로 그 set 의 way 와 비교. 만약 index 와 tag 를 _물리 주소_ 로 만들면(PIPT), 반드시 TLB 변환이 _끝난 뒤_ 에야 lookup 을 시작할 수 있어 변환이 임계 경로에 직렬로 들어갑니다. 여기서 영리한 관찰이 하나 있습니다. 가상→물리 변환은 _페이지 단위_ 라, 주소의 하위 비트(page offset)는 변환되어도 _바뀌지 않습니다._ 그래서 **VIPT(Virtually-Indexed, Physically-Tagged)** 는 변환되지 않는 offset 비트로 set index 를 만들어 _TLB 변환과 동시에_ set 을 고르고, 같은 사이클에 TLB 가 내놓은 물리 주소로 tag 비교를 합니다 — 변환과 index 가 _병렬_ 이라 L1 의 임계 경로가 짧아집니다. L1 이 흔히 VIPT 인 이유가 이것입니다.

이 트릭에는 조건이 있습니다. index 가 page offset 안에서만 만들어지려면 **(way 크기) ≤ (page 크기)** 여야 합니다 — 즉 set 수 × 블록 크기가 한 페이지를 넘지 않아야 index 비트가 전부 변환 불변 영역에 들어갑니다. 이 조건이 깨지면(캐시가 커서 index 가 변환되는 상위 비트까지 침범) **aliasing(synonym) 문제**가 생깁니다. 서로 다른 가상 주소가 같은 물리 주소로 매핑되는데(공유 메모리·mmap), 그 두 가상 주소의 index 비트가 달라 _서로 다른 set 에 같은 물리 라인의 사본 두 개_ 가 생기는 것입니다. 한쪽을 갱신해도 다른 쪽이 stale 해져 일관성이 깨집니다. 이를 피하려고 하드웨어는 way 크기를 page 크기 이하로 제한하거나(가장 흔함), aliasing 가능한 비트를 별도로 검출·무효화하는 회로를 둡니다 — 즉 VIPT 의 속도 이점은 "캐시 크기를 키우기 어렵다"는 제약과 짝을 이룹니다. TLB miss 는 **page table walk** 를 유발해 하드웨어 PTW 가 다단계 페이지 테이블을 순회하며 PTE 를 찾고, **page fault**(PTE 부재) 시 OS 커널이 디스크/swap 에서 페이지를 로드하고 PTE 를 갱신한 뒤 실행을 재개합니다. 큰 working set(DB, ML)을 위해 **huge page**(2 MB, 1 GB)로 TLB 압력을 줄이며, 이는 큰 연속 DMA 버퍼를 다루는 SoC/가속기에 직접 관련됩니다.

### 4.5 DRAM 기초 — bank / row / column

DRAM 은 각 비트를 capacitor 전하로 저장하며 bank(병렬 활성 가능한 독립 배열), row(page, RAS 로 활성화), column(CAS 로 선택)으로 구성됩니다.

```d2
direction: right

REQ: "memory request"
OPEN: "**row 이미 열림?**"
HIT: "**Row hit**\nCAS 만 → 빠름 (CL)"
MISS: "**Row miss**\nprecharge + RAS + CAS\n→ +28–40 ns"

REQ -> OPEN
OPEN -> HIT: "yes (same row)"
OPEN -> MISS: "no (different row)"
```

| 파라미터(DDR5 근사) | 의미 | 값 |
|---|---|---|
| tRCD | RAS→CAS delay (row 열기) | ~14 ns |
| CL | CAS latency (column→data) | ~14 ns |
| tRP | precharge (row 닫기) | ~14 ns |

row hit 은 CL 만으로 빠르지만 row miss 는 precharge + RAS + CAS 가 필요해 훨씬 비쌉니다. 그래서 page-policy-aware 메모리 컨트롤러는 DRAM 요청을 재정렬해 row hit 을 최대화하며, 이것이 DMA 중심 가속기 워크로드의 bandwidth 에 직접 영향을 줍니다.

---

## 5. 디테일 — AMAT, associativity trade-off, 재정렬과 검증

### 5.1 AMAT — 계층 성능의 정량화

평균 메모리 접근 시간(AMAT)은 계층을 가중 평균으로 묶습니다.

```
AMAT = Hit Time + Miss Rate × Miss Penalty
// 다단계:
AMAT = HitTime_L1 + MissRate_L1 × (HitTime_L2 + MissRate_L2 × (… DRAM …))
```

이 식이 보여주는 것은 _miss rate 를 줄이는 것_ 과 _miss penalty 를 줄이는 것_ 이 모두 유효한 최적화 축이라는 점입니다. associativity 를 높이면 conflict miss(=miss rate)가 줄지만 hit time 이 늘 수 있어, 두 항의 trade-off 를 봐야 합니다.

### 5.2 write-back 의 stale 메모리와 coherence

write-back 캐시는 hit 시 메모리를 갱신하지 않으므로, dirty 라인이 캐시에만 최신 값을 가집니다. 다른 agent(다른 코어·DMA·가속기)가 같은 주소를 읽으면 stale 한 메모리를 볼 수 있어, coherence 프로토콜이 dirty 라인을 snoop 해 최신 값을 전달해야 합니다. 검증에서 reference model 은 "이 시점의 진짜 최신 값이 캐시(dirty)에 있는가 메모리에 있는가"를 추적해야 하며, 이는 [cache coherence 토픽](../../cache_coherence/)으로 이어집니다.

### 5.3 hardware prefetching — compulsory/capacity miss 를 선제적으로 줄이기

3C 분류에서 compulsory miss 를 "첫 접근이라 불가피"라고 했지만, 이는 _수동적으로 기다릴 때_ 의 이야기입니다. 현대 캐시 성능의 큰 축 하나가 **hardware prefetcher** — 미래에 쓸 라인을 _접근하기 전에 미리_ 가져와 miss 를 hit 으로 바꾸는 것입니다. "불가피한 첫 접근"도 _그 접근이 일어나기 전_ 에 미리 fetch 해 두면 latency 가 숨겨집니다.

원리는 접근 _패턴을 관찰해 다음 주소를 예측_ 하는 것입니다.

- **next-line / sequential**: 한 라인을 접근하면 곧바로 다음 라인도 가져옵니다 — 순차 스캔(배열 순회, memcpy)에 효과적.
- **stride prefetcher**: 접근 주소의 _간격(stride)_ 이 일정하면(예: 구조체 배열을 일정 stride 로 순회) 그 stride 를 학습해 여러 칸 앞을 미리 fetch.
- **stream prefetcher**: 여러 개의 순차 스트림을 동시에 추적해 각각 앞서 fetch.

이들이 compulsory miss(처음 보는 라인이라도 패턴상 곧 올 것을 예측)와 capacity miss(곧 쓸 데이터를 미리 끌어와 demand miss 시점 단축)를 _선제적으로_ 줄입니다. 다만 공짜는 아닙니다 — 예측이 틀리면 안 쓸 라인을 가져와 _유용한 라인을 축출_ (cache pollution)하고 대역폭을 낭비합니다. 그래서 prefetcher 는 정확도(useful prefetch 비율)와 적시성(너무 일러도 늦어도 안 됨)으로 평가됩니다. 검증·성능 분석에서 "접근 패턴은 똑같은데 miss rate 가 기대보다 낮다"면 prefetcher 가 동작 중인 것이고, 반대로 _불규칙 접근_(포인터 추적, 해시)에서 성능이 안 오르면 prefetcher 가 패턴을 못 잡아서일 수 있습니다.

### 5.4 DRAM 재정렬은 정상 — 검증 기대값 잡기

메모리 컨트롤러의 요청 재정렬은 row hit 을 노린 정상 최적화입니다. 따라서 메모리 인터페이스 scoreboard 는 _발행 순서_ 가 아니라 _주소·데이터의 정확성_ 으로 비교해야 하며, 같은 주소에 대한 read-after-write 순서 같은 의미적 제약만 검사해야 합니다. 이는 OoO 코어(M03)나 AXI OoO scoreboard([UVM M05](../../uvm/05_tlm_scoreboard_coverage/))와 동일한 원리 — "도착 순서가 아니라 의미로 매칭".

---

## 6. 흔한 오해 와 DV 디버그 체크리스트

### 흔한 오해

:::danger[❓ 오해 1 — '메모리 컨트롤러가 요청 순서를 바꾸면 버그다']
**실제**: row hit 을 최대화하기 위한 _정상_ 재정렬입니다. row miss 는 precharge+RAS+CAS 로 row hit 보다 ~28–40 ns 더 비싸므로, 같은 row 요청을 모으는 것이 bandwidth 를 높입니다. scoreboard 는 순서가 아니라 의미(주소/데이터 정확성)로 비교해야 합니다.<br>
**왜 헷갈리는가**: "발행 순서 = 처리 순서" 라는 in-order 가정 때문에.
:::
:::danger[❓ 오해 2 — 'write-back 캐시면 메모리가 항상 최신이다']
**실제**: write-back 은 hit 시 캐시만 갱신하고 dirty bit 만 세웁니다. 축출 전까지 메모리는 stale 하며, 진짜 최신 값은 dirty 라인(캐시)에 있습니다. coherence 검증에서 이를 빠뜨리면 기대값이 틀립니다.<br>
**왜 헷갈리는가**: "쓰면 메모리에 반영" 이라는 write-through 직관을 write-back 에 잘못 적용해서.
:::
:::danger[❓ 오해 3 — 'associativity 를 높이면 무조건 빨라진다']
**실제**: associativity 증가는 conflict miss(miss rate)를 줄이지만 hit time 과 전력을 늘립니다. AMAT = HitTime + MissRate × MissPenalty 에서 두 항의 trade-off — 무한정 높이는 것이 답은 아닙니다.<br>
**왜 헷갈리는가**: "miss 가 줄면 빠르다" 만 보고 hit time 증가를 놓쳐서.
:::
### DV 디버그 체크리스트

| 증상 | 1차 의심 | 어디 보나 |
|---|---|---|
| 메모리 scoreboard 가 순서로 mismatch | 재정렬을 in-order 로 기대 | 비교 기준을 주소/데이터 의미로 변경 |
| 같은 주소 다른 시점 다른 hit/miss | 3C 중 conflict(같은 set 축출 반복) | index 충돌하는 접근 패턴, associativity |
| 다른 agent 가 stale 값 읽음 | write-back dirty 라인 미반영(coherence) | snoop/dirty 추적, [cache coherence](../../cache_coherence/) |
| 주소 분해 오류로 잘못된 set 접근 | tag/index/offset 비트 폭 계산 오류 | 블록·set 크기로 비트 폭 재계산 |
| DMA bandwidth 가 기대 이하 | row miss 비율 높음(접근 패턴이 row 분산) | row hit율, 접근 stride vs row 크기 |

---

## 7. 핵심 정리 (Key Takeaways)

- **Memory Wall** → 계층(register→L1→L2→L3→DRAM→storage): 가까울수록 빠르고 작다. 지역성에 베팅.
- **주소 분해**: offset=log₂(블록), index=log₂(set), 나머지=tag — 파라미터마다 매번 계산.
- **3C miss**: compulsory(cold, 불가피), capacity(용량 부족), conflict(set 충돌, associativity 로 완화).
- **write-back + write-allocate** 가 표준; hit 시 캐시만 갱신 → dirty 라인이 최신, 메모리는 stale.
- **TLB → page walk → page fault**: 가상→물리 변환; huge page 로 TLB 압력 완화(큰 DMA 버퍼).
- **DRAM row hit(CL) ≪ row miss(precharge+RAS+CAS)** → 컨트롤러의 재정렬은 정상 최적화, 순서 아닌 의미로 검증.

:::caution[실무 주의점]
- 메모리/DMA scoreboard 는 _순서_ 가 아니라 _의미(주소·데이터)_ 로 비교 — 재정렬을 버그로 오인 금지.
- write-back 캐시 검증은 dirty 라인이 "진짜 최신"이라는 점을 reference model 에 반영.
- coherence 가 얽히면 [cache coherence 토픽](../../cache_coherence/)으로 escalate.
:::
### 7.1 자가 점검

:::tip[🤔 Q1 — 주소 분해 (Bloom: Apply)]
128-byte 블록, 512 set, 8-way 캐시(40-bit 물리 주소)에서 tag/index/offset 비트 수는?
<details>
<summary>정답</summary>

offset = log₂(128) = 7 bit (블록 내 바이트). index = log₂(512) = 9 bit (set 선택). tag = 40 − 9 − 7 = 24 bit. way 수(8)는 _주소 분해에 영향을 주지 않습니다_ — 같은 index 의 8 way 는 tag 비교로 구분되며, way 수는 한 set 이 흡수할 수 있는 충돌 블록 수만 정합니다. 즉 [Tag 24 | Index 9 | Offset 7] = 40 bit. associativity 를 8 에서 16 으로 바꿔도(set 수 고정 시) 이 비트 분해는 동일하고, set 수를 바꾸면 index/tag 가 바뀝니다.

</details>
:::
:::tip[🤔 Q2 — DRAM 재정렬 (Bloom: Analyze)]
DMA scoreboard 가 "발행 순서와 다른 순서로 DRAM 접근이 일어난다"며 mismatch 를 낸다. 이것이 버그가 아닐 가능성과 올바른 검증 방법은?
<details>
<summary>정답</summary>

메모리 컨트롤러는 row hit 을 최대화하려고 같은 DRAM row 를 노리는 요청을 모아 처리하며, 이를 위해 요청 순서를 의도적으로 재정렬합니다. row hit 은 CAS(CL)만으로 빠르지만 row miss 는 precharge+RAS+CAS 로 ~28–40 ns 가 더 들기 때문입니다. 따라서 순서 차이 자체는 정상 최적화일 가능성이 높습니다. 올바른 검증은 (1) scoreboard 비교 기준을 발행 순서가 아니라 주소별 데이터 정확성으로 바꾸고, (2) 같은 주소에 대한 read-after-write 순서 같은 _의미적_ 일관성 제약만 검사하는 것입니다. OoO 코어(M03)나 AXI OoO scoreboard(UVM M05)와 동일하게 "도착 순서가 아니라 의미로 매칭"하는 원리입니다. 단, 의미적 일관성(같은 주소 RAW 순서)까지 깨지면 그때는 진짜 버그입니다.

</details>
:::
### 7.2 출처

**External**
- Hennessy & Patterson, *Computer Architecture: A Quantitative Approach* — 캐시, 3C, AMAT, DRAM
- Patterson & Hennessy, *Computer Organization and Design* — 캐시 조직, TLB, 가상 메모리

---

## 다음 모듈

→ [Module 05 — 성능 법칙 & 이종 SoC/DSA](../05_performance_laws_dsa/): 지금까지 본 파이프라인·OoO·캐시 기법이 성능에 주는 영향을 Iron Law·Amdahl·Roofline 으로 _정량화_ 하고, 왜 범용 스케일링이 끝나 도메인 특화 가속기(DSA)로 가는지 본다.

[퀴즈 풀어보기 →](../quiz/04_memory_hierarchy_quiz/)
