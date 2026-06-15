---
title: "04 — 일관성·메모리 모델"
---

:::tip[학습 목표]
이 모듈을 마치면:

- **Differentiate** cache coherence(값/단일 위치)와 memory consistency(순서/여러 위치)를 한 문장으로 구분하고 면접 꼬리질문을 막아낸다.
- **Trace** MESI 4상태 전이를 read miss·write·peer snoop 시나리오별로 단계 추적한다.
- **Explain** MOESI의 Owned 상태가 왜 write-back을 우회해 dirty-sharing을 가능하게 하는지 설명한다.
- **Analyze** snooping과 directory 중 코어 수에 따라 어느 쪽을 쓰는지, ARM CHI가 왜 directory류인지 분석한다.
- **Apply** acquire/release barrier를 lock-free 큐의 어느 지점에 두어야 하는지 weak 모델 기준으로 적용한다.
- **Evaluate** false sharing·coherence deadlock을 어떤 검증 corner(성능 카운터·coverage cross·formal liveness)로 잡을지 평가한다.
:::
:::note[사전 지식]
- [02 — CPU 마이크로아키텍처](./02_cpu_microarchitecture/) — 캐시·store buffer·OoO를 먼저 잡을 것
- [Cache Coherence & Consistency](../cache_coherence/) — 본 장은 그 코스를 *면접 답변 길이*로 압축·재배치한 것
:::

---

## 1. 면접관이 가장 먼저 묻는 한 줄

이 토픽의 모든 꼬리질문은 첫 한 줄에서 갈린다. 면접관이 "coherence와 consistency가 뭐가 다른가?"라고 물으면, 외워야 할 답은 단 한 줄이다.

> **Coherence는 값, consistency는 순서.**

좀 더 풀면 이렇다. **Cache Coherence**(여러 캐시에 흩어진 *한 주소*의 사본을 자동으로 맞춰 stale 값을 못 읽게 하는 하드웨어 메커니즘)는 *단일 메모리 위치*가 모든 캐시에서 같은 값으로 보이게 한다 — 쓰기를 전파하고 직렬화하는 캐시 사이의 문제다. 반면 **Memory Consistency**(로드/스토어가 *어떤 순서*로 보이는지를 규정하는, 프로그래머에게 공개된 계약)는 *여러 위치*에 대한 접근이 어떤 순서로 관찰되는가를 정의하는 시스템 전체의 순서 규칙이다.

왜 이 구분이 면접에서 결정적인가? 둘을 뭉뚱그리면 "coherence를 켰으니 멀티스레드가 안전하다"는 틀린 주장을 하게 되고, 면접관은 정확히 그 지점을 찌른다. coherence가 완벽해도 weak 모델에서는 barrier 없이 순서가 깨진다 — coherence는 한 주소의 *사본 일치*만, consistency는 여러 주소 사이의 *순서*만 책임지기 때문이다. 가시성도 다르다. coherence는 프로그래머에게 **투명**(ISA에 coherence 명령이 없음)하지만, consistency는 barrier/fence로 ISA에 **노출**된다.

| 축 | Coherence | Consistency |
|---|---|---|
| 한 단어 | 값(value) | 순서(order) |
| 범위 | 단일 주소(line)의 사본 | 모든 주소 간 접근 순서 |
| 가시성 | 투명(하드웨어 자동) | 가시(barrier로 노출) |
| 누가 만족시키나 | coherence 프로토콜 단독 | pipeline + 프로토콜이 함께 |

:::note[💡 검증 corner]
coherence checker와 consistency checker는 *다른 reference model*을 요구한다. coherence는 per-line scoreboard로 "한 line의 사본이 SWMR을 위반하나"를 보고, consistency는 litmus test로 "여러 주소 결과가 모델이 허용하는 outcome 집합 안인가"를 본다. "stale 읽음" 버그를 디버그할 때 가장 먼저 할 일은 *barrier 누락(consistency)인지 snoop 실패(coherence)인지 분류*하는 것이다 — 분류가 틀리면 엉뚱한 RTL을 본다.
:::

## 2. MESI — 4상태와 전이

### 2.1 네 상태의 의미

**MESI**(Modified/Exclusive/Shared/Invalid, 각 cache line의 사본 상태를 네 가지로 추적하는 코히런스 프로토콜)는 line마다 다음 상태를 둔다. 핵심은 *dirty 여부*와 *독점 여부*의 두 축이다.

| State | 뜻 | 다른 사본 | 메모리와 일치? |
|---|---|---|---|
| **M** (Modified) | 내가 유일 보유, 수정됨(dirty) | 없음 | 불일치 (내가 최신) |
| **E** (Exclusive) | 내가 유일 보유, clean | 없음 | 일치 |
| **S** (Shared) | 여러 캐시가 공유, clean | 있을 수 있음 | 일치 |
| **I** (Invalid) | 무효 (사본 없음) | — | — |

**dirty**(캐시에 쓴 값이 아직 메모리에 반영 안 돼 캐시본이 최신인 상태)란 write-back 정책에서 생기는 상태다. E와 M을 분리한 것이 MESI의 영리함인데, 이유는 2.3에서 드러난다.

### 2.2 전이 규칙 — read miss → E vs S, write → M

면접에서 "MESI 전이를 설명하라"는 질문엔 *세 가지 사건*으로 답하면 빠짐없다.

- **read miss**: 다른 캐시에 사본이 *없으면* **E**(독점 clean)로, *있으면* **S**(공유 clean)로 받는다. "사본이 있나"는 BusRd가 버스에 올라올 때 다른 캐시들이 당기는 wired-OR shared 신호로 판정한다.
- **write**: 반드시 **M**으로 간다. S에서 write하려면 *먼저* 다른 사본을 무효화(Upgrade/BusRdX)해야 SWMR을 지킨다. E에서 write하면 이미 독점이라 무효화 broadcast가 *불필요*하다.
- **peer가 내 M line을 read 요청**: 내 dirty 데이터를 snoop 응답에 실어 직접 공급하고(cache-to-cache), M → S로 내려간다(MOESI면 M → O, 4장 3절).

```
                 BusRdX (write 의도, 무효화)
        ┌──────────────────────────────────────┐
        ▼                                        │
  ┌──────────┐  read miss, 사본 없음  ┌──────────┐
  │    I     │ ─────────────────────▶ │    E     │
  │ (Invalid)│                        │(Exclusive)│
  └──────────┘                        └────┬─────┘
     │   ▲                                  │ local write
     │   │ peer BusRdX                      ▼ (버스 트래픽 0)
     │   │ (내 사본 무효화)            ┌──────────┐
     │   └──────────────────────────  │    M     │
     │     read miss, 사본 있음        │(Modified)│
     ▼ ───────────────────────────▶   └────┬─────┘
  ┌──────────┐  S→write: Upgrade/BusRdX     │ peer BusRd
  │    S     │ ───(다른 사본 무효화)──▶ M    │ (M line 공유 요청)
  │ (Shared) │ ◀──────────────────────────┘
  └──────────┘   M→S (+ MESI는 write-back)
```

### 2.3 왜 E가 비용을 아끼는가

read 후 곧 write하는 패턴(예: `x++`)을 보자. E가 없는 MSI라면 read miss를 S로 받으므로, 이어지는 write 전에 무효화 트랜잭션을 *반드시* 버스에 보내야 한다. MESI는 사본이 나뿐이면 E로 받아 두므로, write 시점에 이미 독점이라 무효화 broadcast가 *생략*된다 — 흔한 패턴에서 버스 트랜잭션 1회를 통째로 절약한다.

:::note[💡 검증 corner]
동시 write 경쟁이 1순위 corner다. 두 코어가 같은 line에 거의 동시에 BusRdX를 올리면 버스(또는 home node)가 직렬화해 한 winner만 M으로 가져가고, 진 쪽은 *그 결과를 본 뒤* 재획득한다. 검증에서 "read miss → E 전이"를 볼 때는 그 순간 정말 다른 캐시의 shared 응답이 0이었는지 snoop 로그로 확인해야 한다 — shared 신호가 부정확하면 사본이 있는데 E로 받아 *무효화 없이 조용히 write*하는 SWMR 위반이 생긴다.
:::

## 3. MOESI — Owned가 메모리 write-back을 우회한다

MESI에서 dirty line을 공유하려면 보통 *메모리에 write-back*한 뒤 둘 다 S가 된다. **MOESI**(Modified/Owned/Exclusive/Shared/Invalid, MESI에 Owned 상태를 더한 확장)는 **O**(Owned, dirty인 채로 공유 가능한 특수 상태)를 추가해, dirty 데이터를 *메모리에 쓰지 않고도* 공유한다. Owner가 dirty를 계속 보유하면서 다른 캐시에 S로 공급하고, 메모리에 최종 반영할 책임만 Owner가 진다.

| State | M | O | E | S | I |
|---|---|---|---|---|---|
| dirty 가능? | O | **O** | X | X | — |
| 공유 가능? | X | **O** | X | O | — |
| 공급 책임 | self | **self(owner)** | self | 메모리/owner | — |

왜 유리한가? producer가 한 번 쓰고 여러 consumer가 반복해서 읽는 워크로드(producer-consumer)에서, MESI는 공유할 때마다 메모리 write-back을 일으켜 대역폭을 소모한다. MOESI는 producer가 O로 dirty를 보유한 채 공급하므로 write-back을 지연/제거한다. 면접 꼬리질문 *"그럼 메모리는 언제 갱신되나?"*의 답은 **owner가 eviction(쫓겨남)될 때**다 — 그 전까지 메모리는 stale이고 owner가 최신값을 공급한다.

:::note[💡 검증 corner]
가장 위험한 MOESI 버그는 *owner의 write-back 누락*이다. O는 dirty이므로 owner가 eviction될 때 write-back을 하지 않으면 silent data loss다("공유 중이니 clean"이라는 오인이 흔하다). eviction 경로에서 O/M line의 write-back 발생 여부를 반드시 covergroup으로 닫아야 한다.
:::

## 4. Snooping vs Directory — 코어 수가 결정한다

snooping은 모든 캐시가 공유 버스를 *엿들어(snoop)* writer의 트랜잭션에 반응한다. 적은 코어 수에서 단순하고 빠르지만, 코어가 늘면 모든 트랜잭션을 broadcast해야 해 버스 대역폭이 병목이 된다. **directory**(누가 어느 line의 사본을 가졌는지 장부로 추적해 *해당 사본을 가진 캐시에만* targeted snoop을 보내는 방식)는 공유자 목록을 home node가 관리해 broadcast를 제거하므로 대규모 멀티코어/NoC로 확장된다 — 대신 directory 조회 지연과 저장 비용이 추가된다.

| 축 | Snooping | Directory |
|---|---|---|
| 무효화 방식 | broadcast (모두에게) | targeted (사본 보유자에게만) |
| 적합 규모 | 소수 코어 | 대규모 멀티코어/NoC |
| ordering point | 공유 버스 | home node |
| 대가 | 버스 대역폭 병목 | directory 지연·저장 비용 |

면접 포인트는 두 가지다. 첫째, "코어 수에 따른 선택"을 trade-off로 말할 것. 둘째, **ARM CHI**(Coherent Hub Interface, ARM의 차세대 coherent 인터커넥트로 directory류 구조)와 **ACE**(AXI Coherency Extensions, AMBA 버스에 coherence를 더한 확장)가 directory류라는 점을 짚을 것. snooping의 직렬화 지점이 버스였다면, directory에서는 home node가 그 ordering point 역할을 물려받는다.

## 5. 메모리 모델 — SC / TSO / Weak와 barrier 배치

"강/약"은 추상이고, 실제로는 하드웨어가 *어떤 재배치를 허용하느냐*로 모델이 갈린다.

| 모델 | 허용 재배치 | 직관 | 대표 |
|---|---|---|---|
| **SC** (Sequential Consistency) | 없음 — 모든 load/store가 하나의 전역 순서 | "프로그램 순서 그대로 모두가 같은 순서로 관찰" | 이론적 기준점 |
| **TSO** (Total Store Order) | store→load만 완화 | "store는 buffer에 잠깐, 그 뒤 load가 먼저 진행" | x86 |
| **weak / release** | store→store, load→load까지 완화 | "기본은 자유, barrier로만 순서 강제" | ARM, RISC-V |

왜 SC에서 점점 풀어 줬나? SC는 직관적이지만 *매 store가 전역에 보일 때까지 다음 명령을 못 진행*해 store latency가 그대로 stall이 된다. **store buffer**(코어가 쓴 값을 캐시에 곧장 넣지 않고 잠시 모아 두는 큐)를 도입하면 stall이 사라지는데, 그 순간 store→load 순서가 깨져 TSO로 내려간다. OoO·write coalescing을 더 얹으면 store끼리·load끼리 순서도 흔들려 weak가 된다. 즉 약한 모델은 결함이 아니라 *성능의 대가*이며, 그 반납분을 프로그래머가 **barrier**(이 지점 이전 메모리 접근이 모두 끝난 뒤 이후 접근을 진행하라고 강제하는 순서 명령)로 *필요한 지점에만* 되산다.

ARM은 weak 모델이라 barrier가 핵심이다. **DMB**(앞뒤 메모리 접근 순서 보장), **DSB**(완료까지 대기), **ISB**(파이프라인 flush, 명령 스트림 동기 — 시스템 레지스터 변경 후)가 큰 망치라면, **acquire/release**(LDAR/STLR, 한 방향 순서만 강제하는 가벼운 세밀 제어)가 lock-free 코드의 정밀 도구다.

### 5.1 Lock-free 큐 — barrier를 어디에 두나

producer가 데이터를 쓰고 `ready` 플래그를 세우면, consumer가 `ready`를 보고 데이터를 읽는 고전 패턴이다. weak 모델에서는 producer의 두 store(데이터, 플래그)가 *재배치*될 수 있어, consumer가 `ready=1`을 봤는데 데이터는 옛 값일 수 있다.

```systemverilog
// Producer (release): 데이터 store가 flag store보다 먼저 보이도록
//   STLR(store-release)이 "이전 store들이 다 보인 뒤에 flag가 보임"을 보장
//   data = payload;        // 일반 store
//   ready = 1;             // store-release (STLR) — 앞선 store들을 가둠
//
// Consumer (acquire): flag load 이후 데이터 load가 추월하지 않도록
//   while (LDAR(ready) == 0);   // load-acquire (LDAR) — 이후 load를 가둠
//   x = data;                   // flag를 본 뒤에야 진행 → 최신 data 보장
//
// 검증 monitor 예시 — ordering 위반 시 UVM_ERROR
if (obs_ready_seen == 1 && obs_data == STALE_VALUE) begin
  `uvm_error("ORDER", "consumer saw ready=1 but stale data — release/acquire 누락")
end
```

핵심 인과: **release는 "앞선 store들을 그 store-release 뒤로 가둔다"**, **acquire는 "이후 load들을 그 load-acquire 앞으로 가둔다"**. 둘이 짝을 이뤄 producer의 데이터 쓰기가 flag보다 먼저, consumer의 데이터 읽기가 flag 확인보다 나중에 보이도록 만든다. barrier를 양쪽 다 빼면 weak 모델에서 조용히 깨진다 — 그래서 "왜 x86(TSO)보다 ARM에서 barrier를 더 신경 쓰나"가 면접 단골이다(x86은 store→load만 완화라 이 패턴이 우연히 동작하는 경우가 많다).

:::note[💡 검증 corner]
consistency 검증은 directed로는 닿지 않는다. **litmus test**(여러 코어가 동시에 짧은 코드로 메모리에 접근해, 메모리 모델이 허용하는 결과만 나오는지 시험하는 표준 테스트)로 "관찰된 outcome이 모델 허용 집합 안인가"를 axiomatic model과 대조한다. barrier 위치 coverage(어느 store/load 쌍 사이에 barrier가 있었나)와 reorder 발생 cross가 핵심 coverage 항목이다.
:::

## 6. False sharing과 Coherence Deadlock — 두 함정

### 6.1 False sharing — "기능 OK, 성능 급락"

**false sharing**(서로 무관한 변수가 *같은 cache line*에 들어 있어, 한 코어가 자기 변수만 써도 line 전체가 무효화되어 다른 코어 접근이 miss를 일으키는 현상)은 기능은 정상인데 성능만 무너지는 교묘한 버그다. 코어들이 같은 line의 *다른 바이트*를 번갈아 write하면 불필요한 invalidate ping-pong이 일어나 coherence 트래픽이 폭증한다.

검증/탐지는 두 갈래다. 첫째, **성능 카운터**로 line당 invalidate 빈도·coherence 트랜잭션 수가 비정상적으로 높은지 본다. 둘째, **coverage cross**로 "서로 다른 코어가 동일 line 접근"을 covergroup으로 잡는다. 디버그 신호는 명확하다 — *"기능은 맞는데 느리다"면 false sharing을 1순위로 의심*하고 변수 주소 alignment를 본다.

### 6.2 Coherence deadlock — 채널 순환 의존

coherence 프로토콜의 deadlock은 **요청/응답/snoop 채널 간 순환 의존 + 버퍼 고갈**에서 생긴다. 예를 들어 응답을 받아야 버퍼가 비는데, 그 버퍼가 막혀 응답을 받지 못하면 서로를 기다리는 cycle이 닫힌다.

막는 방법은 세 가지가 짝을 이룬다.

- **virtual channel 분리**(req/rsp/snoop를 물리적으로 또는 논리적으로 분리해 한 채널의 정체가 다른 채널을 막지 않게 함) — 순환의 고리를 끊는다.
- **ordering 규칙** — 응답이 새 요청을 막지 않도록(응답은 항상 sink될 수 있어야) 보장한다.
- **credit 기반 흐름제어**(수신측이 받을 수 있는 만큼만 송신 허가 credit을 발급해 버퍼가 넘치지 않게 함) — 버퍼 고갈 자체를 예방한다.

:::note[💡 검증 corner]
deadlock은 시뮬 timeout으로 나타나지만, 상태공간이 깊어 시뮬로 모든 경로를 닿기 어렵다 — 그래서 **formal liveness** 속성이 적합하다. 프로토콜 FSM에 *"모든 요청은 결국 응답을 받는다"*(`req |-> ##[1:$] rsp` 류의 liveness/eventually 속성)를 걸어 데드락/라이브락 부재를 증명한다. timeout이 떴을 때는 마지막 진행 지점에서 어느 채널이 stuck인지(어느 버퍼가 full인지) 역추적해 순환을 찾는다.
:::

## 샘플 Q&A

답을 가린 채 스스로 답해 본 뒤 펼쳐 확인하라.

**Q. "coherence와 consistency의 차이를 한 줄로?"**

<details>
<summary>모범 답변 방향</summary>

"Coherence는 값, consistency는 순서." coherence는 *단일 주소*의 사본을 모든 캐시에서 같은 값으로 맞추는 하드웨어 메커니즘(투명)이고, consistency는 *여러 주소* 접근이 어떤 순서로 관찰되는지를 정의하는 프로그래머에게 공개된 계약(barrier로 노출)이다. 꼬리질문 방어: "coherence가 완벽해도 weak 모델에서는 barrier 없이 순서가 안 보장된다"를 함께 말한다.
</details>

**Q. "MESI에서 read miss가 E로 끝날 때와 S로 끝날 때를 가르는 건?"**

<details>
<summary>모범 답변 방향</summary>

다른 캐시에 사본이 있느냐다. BusRd가 올라올 때 사본을 가진 캐시가 wired-OR shared 신호를 assert한다. 0이면(아무도 없음) E로 독점 수령, 1이면(누군가 보유) S로 공유 수령. E의 가치는 이어지는 write에서 무효화 broadcast를 생략할 수 있다는 점이다. 검증에서는 E 전이 시점에 shared 응답이 정말 0이었는지 snoop 로그로 확인해야 SWMR 위반(사본 있는데 E로 받아 조용히 write)을 막는다.
</details>

**Q. "MOESI의 O가 왜 추가됐고, 메모리는 언제 갱신되나?"**

<details>
<summary>모범 답변 방향</summary>

MESI는 dirty line을 공유하려면 매번 메모리에 write-back해야 한다. O(Owned)는 *dirty인 채로 공유*를 허용해 write-back을 지연/제거하므로 producer-consumer 워크로드의 메모리 대역폭을 아낀다. 메모리 갱신 시점은 *owner가 eviction될 때*다 — 그 전까지 메모리는 stale, owner가 공급 책임. 대가는 owner 추적·책임 이전 로직으로 인한 프로토콜 복잡도다.
</details>

**Q. "ARM weak 모델에서 lock-free 핸드오프가 깨지는 이유와 고치는 법은?"**

<details>
<summary>모범 답변 방향</summary>

weak 모델은 store→store, load→load 재배치를 허용하므로, producer의 데이터 store와 flag store가 뒤바뀌어 consumer가 flag=1을 봤는데 데이터는 옛 값일 수 있다. 고치려면 producer의 flag write를 store-release(STLR)로, consumer의 flag read를 load-acquire(LDAR)로 짝지어, release가 앞선 store들을 가두고 acquire가 이후 load들을 가두게 한다. x86(TSO)은 store→load만 완화라 이 패턴이 우연히 동작하기도 하지만, ARM에서는 명시 barrier가 필수다.
</details>

## 핵심 요약

- **Coherence는 값, consistency는 순서** — 첫 한 줄을 외우되, "coherence 완벽해도 weak 모델은 barrier 필요"를 항상 덧붙인다.
- **MESI**: read miss는 사본 유무로 E(독점)/S(공유), write는 항상 M(S에서는 먼저 무효화). E가 read→write 패턴의 무효화 broadcast를 절약한다.
- **MOESI의 O**: dirty인 채 공유 → write-back 우회. 메모리 갱신은 owner eviction 시. owner write-back 누락 = silent data loss.
- **Snooping vs directory**: 코어 수가 결정. ARM CHI/ACE는 directory류 — home node가 ordering point.
- **SC→TSO→weak**: store buffer·OoO가 성능을 얻은 대가로 순서를 반납, 프로그래머가 acquire/release로 필요한 곳만 되산다.
- **검증 corner**: false sharing은 성능 카운터+coverage cross로, coherence deadlock은 virtual channel/credit으로 막고 formal liveness("모든 요청은 응답 받음")로 증명.

→ 자기 점검: [퀴즈 — 04장](./quiz/04_coherence_and_memory_model_quiz/)
