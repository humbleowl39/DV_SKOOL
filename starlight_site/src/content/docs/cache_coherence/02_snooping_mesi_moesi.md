---
title: "Module 02 — Snooping & MESI/MOESI"
---

:::tip[학습 목표]
이 모듈을 마치면:

- **Explain** bus snooping이 어떻게 peer 캐시를 자동으로 무효화/갱신하여 SWMR을 강제하는지 설명할 수 있다.
- **Differentiate** MESI 4상태(Modified/Exclusive/Shared/Invalid)의 의미와 전이 조건을 구분할 수 있다.
- **Explain** MOESI가 추가하는 Owned 상태가 왜 dirty-sharing(write-back 우회)을 가능하게 하는지 설명할 수 있다.
- **Trace** 한 store/load가 일으키는 상태 전이와 peer 무효화를 단계별로 추적할 수 있다.
:::
:::note[사전 지식]
- [Module 01 — Consistency vs Coherence](../01_consistency_vs_coherence/) (SWMR / Data-Value invariant)
- 캐시 write-back vs write-through, dirty bit
:::
---

## 1. Why care? — "누가 최신값을 들고 있나"를 매 접근마다 결정해야 한다

### 1.1 시나리오 — write 후 다른 코어가 stale를 읽는 고전 버그

Module 01의 무한 루프 버그(Core A가 `flag=1`을 썼는데 B가 0을 봄)를 하드웨어가 자동으로 막으려면, A의 store가 *발생하는 순간* B의 사본을 무효화하거나 갱신해야 합니다. snooping 프로토콜은 이를 **공유 버스(또는 broadcast 인터커넥트)** 위에서 모든 캐시가 서로의 트랜잭션을 *엿듣게(snoop)* 함으로써 달성합니다.

여기서 **cache line**(캐시가 메모리를 읽고 쓰는 최소 단위 블록 — 보통 64바이트, 한 변수만 써도 그 변수가 속한 line 전체가 통째로 오감)이 사본 관리의 단위입니다. 그리고 **dirty**(캐시에 쓴 값이 아직 메모리에 반영 안 돼 캐시본이 최신인 상태)란, write 정책 중 **write-back**(쓰기를 일단 캐시에만 반영하고 메모리 갱신은 그 line이 쫓겨날 때로 미루는 방식)을 쓸 때 생기는 상태입니다 — 매 쓰기를 즉시 메모리에도 반영하는 **write-through**(쓰기를 캐시와 메모리에 동시에 반영)와 대비됩니다.

문제는 단순 무효화만으로 끝나지 않는다는 점입니다. A가 dirty 데이터를 들고 있을 때 B가 그 line을 읽으려 하면, 메모리에는 옛 값밖에 없으므로 *A의 캐시에서 직접* 데이터를 끌어와야 합니다. 그리고 "지금 이 line을 내가 독점적으로 쓸 수 있나, 아니면 다른 캐시와 공유 중인가"를 매 접근마다 알아야 무효화 트래픽을 최소화할 수 있습니다. 이 정보를 line마다 들고 있는 것이 바로 **coherence state**(각 cache line이 "독점인지·공유인지·수정됐는지"를 나타내는 상태 표시)이고, MESI/MOESI는 그 state 인코딩의 표준입니다.

이 모듈을 건너뛰면 ACE의 snoop 응답이 왜 "데이터 동반"인지, 왜 어떤 read는 shared로 끝나고 어떤 read는 dirty 전송을 유발하는지 설명하지 못합니다.

---

## 2. Intuition — 동네 게시판, 한 장 그림

:::tip[💡 한 줄 비유]
**Snooping** ≈ 모두가 보는 **동네 게시판**. 한 사람이 "이 책 내가 수정할게(write)"라고 게시판에 붙이면, 같은 책을 들고 있던 나머지 사람은 *알아서* 자기 사본을 찢어버린다(invalidate). 사서가 일일이 찾아다니지 않아도 모두가 게시판을 *엿듣고* 있기 때문.
:::
### 한 장 그림 — 공유 버스 위의 snoop

```d2
direction: down

BUS: "**Shared Bus / Broadcast Interconnect**\n모든 캐시가 트랜잭션을 snoop"
C0: "**Core 0 cache**\nline X: M/E/S/I"
C1: "**Core 1 cache**\nline X: M/E/S/I"
C2: "**Core 2 cache**\nline X: M/E/S/I"
MEM: "**Main Memory (DRAM)**"

C0 -> BUS: "BusRdX (write 의도)"
BUS -> C1: "snoop → X 무효화 (→ I)"
BUS -> C2: "snoop → X 무효화 (→ I)"
BUS -> MEM: "miss 시 fetch"
```

### 왜 이 디자인인가 — Design rationale

snooping이 답이 되는 이유는 세 요구의 교집합입니다.

1. **store가 즉시 peer 사본에 반영되어야** (SWMR) → 모든 캐시가 버스를 엿듣고 무효화 신호에 반응.
2. **dirty 데이터를 든 캐시가 메모리보다 우선 공급해야** (Data-Value) → snoop 응답에 데이터를 실어 보냄(**cache-to-cache transfer** — 메모리를 거치지 않고 한 캐시가 다른 캐시로 직접 데이터를 넘기는 전송).
3. **불필요한 무효화 트래픽을 줄여야** → line마다 state를 둬서 "이미 독점(E/M)인지, 공유(S)인지"를 알고 *공유 중일 때만* 무효화.

이 세 요구가 곧 **per-line state machine (MESI/MOESI) + broadcast snoop**의 설계 결정입니다.

---

## 3. 작은 예 — Core 0 write, Core 1 read의 상태 전이

가장 단순한 시나리오. Core 0이 line X를 쓰고(독점), 그다음 Core 1이 X를 읽습니다.

### 단계별 다이어그램

```d2
direction: down

S1: "**① Core0: read miss on X**\nBusRd → 다른 캐시 사본 없음\nX 상태: I → E (Exclusive)" {
  style.fill: "#e8f0fe"
}
S2: "**② Core0: write X**\n이미 E(독점)이므로 버스 신호 불필요\nX 상태: E → M (Modified, dirty)" {
  style.fill: "#fff4e5"
}
S3: "**③ Core1: read miss on X**\nBusRd → Core0이 M(dirty) 보유\nsnoop 응답으로 X 데이터 공급\nCore0: M → S (+메모리 write-back)\nCore1: I → S\n(MOESI면 write-back 생략, Core0: M → O)" {
  style.fill: "#e6f4ea"
}
S1 -> S2 -> S3
```

### 단계별 의미

| Step | 누가 | 무엇을 | state 전이 |
|---|---|---|---|
| ① | Core0 | read miss, 다른 사본 없음 | I → **E** |
| ② | Core0 | write (이미 독점) | E → **M** (버스 트래픽 0) |
| ③ | Core1 | read miss, Core0이 dirty 보유 | Core0 M→S, Core1 I→S; 데이터는 cache-to-cache |

E(Exclusive)의 가치가 ②에서 드러납니다. read miss 때 사본이 나뿐이면 E로 받아 두기 때문에, 곧이어 write할 때 *버스에 무효화 신호를 보낼 필요가 없습니다*(이미 독점). 이것이 MESI가 MSI 대비 트래픽을 줄이는 핵심입니다 (외부 표준 지식).

### MESI 상태 의미

| State | 뜻 | 다른 사본 | 메모리와 일치? |
|---|---|---|---|
| **M** (Modified) | 내가 유일 보유, *수정됨(dirty)* | 없음 | 불일치 (내가 최신) |
| **E** (Exclusive) | 내가 유일 보유, clean | 없음 | 일치 |
| **S** (Shared) | 여러 캐시가 공유, clean | 있을 수 있음 | 일치 |
| **I** (Invalid) | 무효 (사본 없음) | — | — |

:::note[여기서 잡아야 할 핵심]
**E와 M의 분리**가 MESI의 영리함입니다. clean-독점(E)을 따로 두면, read 후 write로 이어지는 흔한 패턴에서 무효화 broadcast를 생략할 수 있습니다. 반대로 S에서 write하려면 *반드시* 다른 사본을 무효화(BusRdX/Upgrade)해야 SWMR을 지킵니다.
:::

:::note["다른 사본 없음" 을 누가 어떻게 판정하나 — shared signal]
①에서 read miss가 E로 끝나려면 "지금 이 line을 가진 다른 캐시가 정말 하나도 없다" 는 사실을 확인해야 합니다. 그런데 요청한 코어는 자기 캐시 밖을 직접 들여다볼 수 없습니다 — 이 판정을 대신해 주는 것이 **snoop 응답의 shared signal** 입니다. BusRd가 버스에 올라오면 모든 peer 캐시가 그 주소를 snoop하고, *그 line을 보유한* 캐시가 공용 **shared(또는 "copies-exist") wired-OR 신호** 를 assert합니다. 이 신호는 여러 캐시가 동시에 당겨도 "하나라도 보유하면 1" 이 되도록 wired-OR로 묶여 있어, 요청자는 단 하나의 비트로 "사본 존재 여부" 를 알 수 있습니다.

- shared signal이 **0** (아무도 assert 안 함) → 사본이 나뿐 → **E** 로 받음.
- shared signal이 **1** (누군가 보유) → 공유 상태 → **S** 로 받음.

즉 E 상태의 존재 자체가 이 shared signal에 의존합니다. 이 신호가 없거나 부정확하면, 사본이 있는데도 E로 받아 *조용히 무효화 없이 write* 하는 SWMR 위반이 생깁니다. 그래서 검증에서 "read miss → E 전이" 를 볼 때는, 그 시점에 정말 다른 캐시의 shared 응답이 0이었는지를 snoop 응답 로그로 확인해야 합니다.
:::
---

## 4. 일반화 — MESI에서 MOESI로

### 4.1 MOESI의 Owned 상태

MESI에서 ③번처럼 dirty line을 공유하려면 보통 *메모리에 write-back*한 뒤 둘 다 S가 됩니다. MOESI는 여기에 **O(Owned)** 상태를 추가해, dirty 데이터를 *메모리에 쓰지 않고도* 공유할 수 있게 합니다. Owner가 dirty 데이터를 계속 보유하면서 다른 캐시에 S로 공급하고, 최종적으로 메모리에 반영할 책임만 Owner가 집니다.

```d2
direction: right

MESI: "**MESI: dirty share**" {
  direction: down
  m1: "Core0: M"
  wb: "write-back to MEM"
  s1: "Core0: S, Core1: S\n(메모리가 최신)"
  m1 -> wb -> s1
}
MOESI: "**MOESI: dirty share (write-back 우회)**" {
  direction: down
  m2: "Core0: M"
  o2: "Core0: **O** (dirty 보유, owner)\nCore1: S"
  note: "메모리 갱신은 나중\nowner가 공급 책임"
  m2 -> o2 -> note
}
```

| State | M | O | E | S | I |
|---|---|---|---|---|---|
| dirty 가능? | O | **O** | X | X | — |
| 공유 가능? | X | **O** | X | O | — |
| 공급 책임 | self | **self(owner)** | self | (메모리/owner) | — |

### 4.2 왜 MOESI가 유리한가

MESI에서 dirty line을 여러 코어가 번갈아 읽기만 해도 매번 write-back이 발생해 메모리 대역폭을 소모합니다. MOESI의 Owned는 "dirty인 채로 공유"를 허용해 이 write-back을 지연/제거하므로, read-shared가 빈번한 워크로드(예: producer-consumer)에서 메모리 트래픽을 크게 줄입니다. 대신 owner를 추적하고 owner 교체 시 책임을 넘기는 로직이 추가되어 프로토콜이 복잡해집니다 (추론: trade-off는 일반 아키텍처 지식).

### 4.3 snooping의 트랜잭션 종류 (개념)

| 트랜잭션 | 의미 | 결과 |
|---|---|---|
| BusRd | read miss (읽기 의도) | 사본 없으면 E, 있으면 S |
| BusRdX | read-for-ownership (write 의도) | 다른 사본 무효화 후 M |
| Upgrade / Invalidate | S에서 write 전, 다른 사본 무효화 | S → M |
| Writeback | dirty line을 메모리로 | M/O → (eviction — 새 line 자리를 만들려고 기존 line을 캐시에서 쫓아냄) |

:::note[snooping이 성립하려면 — bus가 트랜잭션을 직렬화하는 ordering point여야]
snooping의 정확성은 한 가지 숨은 전제 위에 서 있습니다 — **모든 캐시가 트랜잭션을 *같은 순서* 로 관찰한다**. 공유 버스는 한 순간에 단 하나의 트랜잭션만 통과시키므로(arbitration으로 한 winner만 선택), 모든 캐시가 그 단일 순서를 똑같이 엿듣습니다. 이 "전역 단일 순서" 가 곧 coherence의 **ordering point(serialization point)** 입니다.

왜 이게 필수일까요? 두 코어가 같은 line X에 거의 동시에 write하려 한다고 합시다. 둘의 BusRdX가 버스로 들어오면, 버스는 둘 중 하나를 *먼저* 통과시키고 다른 하나를 뒤로 미룹니다. 먼저 이긴 쪽이 X를 M으로 가져가고, 진 쪽의 BusRdX는 *그 결과를 본 뒤* 다시 무효화·재획득을 거칩니다. 만약 버스가 이렇게 직렬화하지 않고 두 write가 *서로 다른 캐시에 다른 순서로* 보이면, 어떤 캐시는 "A가 마지막 writer", 다른 캐시는 "B가 마지막 writer" 라고 믿어 SWMR이 깨집니다. 즉 snooping이 SWMR을 강제할 수 있는 근본 이유는 무효화 신호 자체가 아니라, *모든 경쟁 트랜잭션을 하나의 전역 순서로 줄 세우는 직렬화 지점* 이 존재하기 때문입니다. (Module 03에서 보겠지만, 버스가 사라진 directory 구조에서는 home node가 이 ordering point 역할을 물려받습니다.)
:::

---

## 5. 디테일 — 무효화 vs 갱신, false sharing

snooping 프로토콜은 크게 **invalidate 기반**과 **update 기반**으로 나뉩니다. invalidate 기반(MESI/MOESI 포함 대부분)은 writer가 peer 사본을 *무효화*하고 다음 read 때 새 값을 받게 합니다. update 기반은 writer가 새 값을 peer에 *직접 갱신*해 줍니다. 현대 시스템은 거의 invalidate 기반인데, update는 한 번 쓰고 안 읽는 데이터에 불필요한 트래픽을 만들기 때문입니다 (외부 표준 지식).

:::note[왜 invalidate가 표준이 되었나 — 주소만 broadcast + write-once 지배]
invalidate가 현대의 사실상 표준이 된 데에는 두 가지 더 깊은 이유가 있습니다.

첫째, **broadcast 트래픽의 양 자체** 가 다릅니다. invalidate는 peer에게 "이 *주소* 를 버려라" 만 알리면 되므로, 버스에 실리는 것은 데이터가 아니라 *주소(coherence 명령)* 뿐입니다. 반면 update는 매 write마다 *새 데이터 값* 을 모든 사본에 실어 보내야 합니다 — write가 burst로 몰리면 데이터 트래픽이 그대로 coherence 트래픽으로 변합니다. cache line은 64B인데 주소는 그보다 훨씬 작으니, invalidate가 broadcast 대역폭 면에서 구조적으로 유리합니다.

둘째, 실제 워크로드의 접근 패턴이 **write-once / write-burst 후 한 reader** 에 가깝습니다. 한 코어가 어떤 line을 여러 번 연속으로 쓰는 동안(예: 루프에서 누산), update 방식은 *매 write마다* peer를 갱신하지만 그 중간값들은 대개 아무도 안 읽습니다 — 순수 낭비입니다. invalidate는 첫 write에서 peer를 한 번 무효화하면 그 코어가 line을 독점(M)하므로, 이후 연속 write는 버스 트래픽 0으로 끝납니다. 다른 코어가 *실제로 다시 읽을 때* 만 단 한 번 최신값을 가져갑니다. 즉 "쓸 때마다 미리 뿌리는" update보다 "필요할 때만 끌어가는" invalidate가, 데이터가 아닌 주소만 broadcast하면 되고 중간 write를 공짜로 만든다는 두 효과로 대부분의 워크로드에서 이깁니다.
:::

검증에서 자주 마주치는 함정은 **false sharing**입니다. 서로 다른 변수가 *같은 cache line*에 들어 있으면, 한 코어가 자기 변수만 써도 line 전체가 무효화되어 다른 코어의 (논리적으로 무관한) 변수 접근이 miss를 유발합니다. 기능은 정상이지만 성능이 무너지고, coherence 트래픽이 폭증합니다. 성능 회귀를 디버그할 때 "기능은 맞는데 느리다"면 false sharing을 의심해야 합니다 (외부 표준 지식).

| 방식 | writer가 하는 일 | 장점 | 단점 |
|---|---|---|---|
| Invalidate | peer 사본 무효화 | write-once 데이터에 효율적 | 다음 read가 miss |
| Update | peer 사본 직접 갱신 | 빈번한 read에 유리 | write 트래픽 과다 |

---

## 6. 흔한 오해 와 DV 디버그 체크리스트

### 흔한 오해

:::danger[❓ 오해 1 — 'E와 M은 사실상 같다 (둘 다 독점)']
**실제**: E는 **clean-독점**(메모리와 일치), M은 **dirty-독점**(메모리보다 최신). 차이는 eviction 시 드러납니다 — E line은 그냥 버려도 되지만 M line은 *반드시* write-back해야 데이터 손실이 없습니다.<br>
**왜 헷갈리는가**: 둘 다 "사본이 나뿐"이라 같아 보이지만, 메모리 일치 여부가 다름.
:::
:::danger[❓ 오해 2 — 'S 상태에서 바로 write하면 된다']
**실제**: S는 다른 캐시도 사본을 가질 수 있는 상태이므로, write 전에 *반드시* 다른 사본을 무효화(Upgrade/BusRdX)해 M으로 가야 SWMR을 지킵니다. S에서 무효화 없이 쓰면 두 writer가 공존해 invariant 위반.<br>
**왜 헷갈리는가**: "내 캐시에 있으니 그냥 쓰면 되지"라는 단순 모델 때문.
:::
:::danger[❓ 오해 3 — 'MOESI의 O는 메모리와 일치한다']
**실제**: Owned는 *dirty*입니다 — 메모리는 stale이고 owner가 최신값을 들고 공유합니다. 그래서 owner가 eviction되면 write-back 책임이 따라옵니다.<br>
**왜 헷갈리는가**: "공유(S처럼) 중이니 clean"으로 오인. O는 "공유 가능한 dirty"라는 특수 상태.
:::
### DV 디버그 체크리스트

| 증상 | 1차 의심 | 어디 보나 |
|---|---|---|
| write 후 peer가 stale 읽음 | 무효화(BusRdX/Upgrade) 누락 또는 지연 | snoop 트랜잭션 로그, 무효화 completion 타이밍 |
| dirty line이 eviction 후 데이터 소실 | M/O line의 write-back 누락 | eviction 경로의 write-back 발생 여부 |
| 기능 정상인데 성능 급락 | false sharing (한 line에 무관 변수들) | 변수 주소 alignment, line당 무효화 빈도 |
| read miss인데 메모리가 옛 값 공급 | dirty 보유 캐시의 snoop 데이터 응답 누락 | cache-to-cache transfer 동작, snoop hit 시 데이터 동반 여부 |
| S에서 write 후 두 코어가 다른 값 | S→M 전 무효화 생략 (SWMR 위반) | Upgrade 트랜잭션 존재 확인 |

---

## 7. 핵심 정리 (Key Takeaways)

- **Snooping**: 모든 캐시가 공유 버스를 엿들어, writer의 트랜잭션에 반응해 자기 사본을 무효화/갱신 → SWMR을 하드웨어로 강제.
- **MESI 4상태**: M(dirty 독점), E(clean 독점), S(공유 clean), I(무효). E의 존재가 read→write 패턴에서 무효화 broadcast를 절약.
- **MOESI의 O(Owned)**: dirty인 채로 공유 가능 → write-back을 지연/우회. owner가 공급·최종 반영 책임.
- **Invalidate vs Update**: 현대 시스템은 거의 invalidate 기반 (write-once 데이터에 효율적).
- **false sharing**: 무관 변수가 같은 line에 있으면 불필요 무효화로 성능 붕괴 — "기능 OK, 성능 급락" 시 1순위 의심.

:::caution[실무 주의점]
- M/O line eviction 경로의 write-back은 *데이터 정확성*의 문제 — 누락 시 silent data loss.
- "S에서 write"는 반드시 무효화를 동반해야 한다 — 이 트랜잭션 누락이 가장 위험한 coherence 버그.
- MESI/MOESI의 정확한 상태 인코딩은 대상 인터커넥트(ACE/CHI)의 사양으로 *재확인* 필요 (ARM IHI 0022 ACE / IHI 0050 CHI).
:::
### 7.1 자가 점검

:::tip[🤔 Q1 — E의 가치 (Bloom: Analyze)]
MSI(E 없음)와 MESI를 비교할 때, "read miss 후 곧 write"하는 흔한 패턴에서 MESI가 절약하는 것은?
<details>
<summary>정답</summary>

MSI에서는 read miss 시 S로 받으므로, 이어지는 write 전에 다른 사본 무효화(Upgrade/BusRdX) 트랜잭션을 *반드시* 버스에 보내야 합니다. MESI는 read miss 때 사본이 나뿐이면 E(독점)로 받으므로, 곧이어 write할 때 이미 독점 상태라 무효화 broadcast가 *불필요*합니다. 즉 MESI는 이 패턴에서 버스 트랜잭션 1회를 절약합니다.
</details>
:::
:::tip[🤔 Q2 — Owned (Bloom: Evaluate)]
producer가 한 번 쓰고 여러 consumer가 반복해서 읽는 워크로드에서, MESI 대비 MOESI가 줄이는 것은 무엇이고 그 대가는?
<details>
<summary>정답</summary>

MESI에서는 dirty line을 공유하려면 매번 메모리로 write-back해야 둘 다 S가 됩니다(메모리 대역폭 소모). MOESI는 producer가 O(Owned)로 dirty를 *보유한 채* consumer에게 S로 공급하므로 write-back을 지연/제거해 메모리 트래픽을 줄입니다. 대가는 owner 추적·owner 교체 시 공급 책임 이전 등 프로토콜 복잡도 증가입니다.
</details>
:::
### 7.2 출처

**External**
- *A Primer on Memory Consistency and Cache Coherence* — snooping coherence 장
- Sweazey & Smith, "A Class of Compatible Cache Consistency Protocols" (MOESI 분류 원전)

---

## 다음 모듈

→ [Module 03 — Directory & 확장성](../03_directory_scalability/): broadcast snooping이 코어 수에 따라 버스를 막는 문제와, directory(snoop filter)로 targeted snoop을 보내 확장성을 회복하는 방법.

[퀴즈 풀어보기 →](../quiz/02_snooping_mesi_moesi_quiz/)
