# Unit 1: Formal Verification 기본 개념

## 핵심 개념
**Formal Verification = 수학적 증명으로 설계의 모든 가능한 입력/상태에서 속성(Property)이 성립함을 보장. 시뮬레이션이 "샘플링"이라면, Formal은 "전수 검사".**

---

## Simulation vs Formal

```
Simulation:
  특정 테스트 시나리오 → DUT 실행 → 결과 확인
  커버리지 100%여도 "모든 상태"를 검사한 것이 아님

  입력 공간: ████████████████████████
  시뮬레이션: ▓▓▓░░░▓░░▓▓░░░▓░░░░▓▓░  (샘플링)
  → 빈 곳에 버그가 숨어 있을 수 있음

Formal:
  속성을 정의 → 수학적으로 모든 상태에서 검증
  반례가 없으면 PROVEN (증명됨)

  입력 공간: ████████████████████████
  Formal:    ████████████████████████  (전수 검사)
  → 증명되면 어떤 입력에서도 속성이 성립
```

| 항목 | Simulation | Formal |
|------|-----------|--------|
| 검증 범위 | 실행된 시나리오만 | **모든** 가능한 입력/상태 |
| 결과 | Pass/Fail (이 시나리오에서) | **PROVEN** / FAILED / BOUNDED |
| 버그 찾기 | 시나리오가 버그 경로를 지나야 | 자동으로 반례(Counterexample) 생성 |
| 확장성 | 큰 설계 가능 | 상태 폭발(State Explosion) 한계 |
| 적합 대상 | 전체 SoC, 대규모 설계 | 제어 로직, 프로토콜, 소규모 IP |
| 자극(Stimulus) | 직접 작성 (Sequence) | 불필요 (엔진이 자동 탐색) |
| 환경 | UVM TB 필요 | **TB 불필요** (Property만 작성) |

---

## Formal의 3가지 결과

```
1. PROVEN (증명됨)
   모든 가능한 입력/상태에서 Property 성립
   → 수학적 보장 → 가장 강력한 결과

2. FAILED (반례 발견)
   Property를 위반하는 구체적 입력 시퀀스(Counterexample) 발견
   → 파형으로 확인 가능 → 버그 확정

3. BOUNDED (제한적 증명)
   N cycle까지는 증명, 그 이후는 미검증
   → State Explosion으로 완전 증명 불가 시
   → "N cycle 이내에서는 안전" (실용적으로 충분할 수 있음)
```

---

## Formal이 강력한 영역

| 영역 | 이유 | 예시 |
|------|------|------|
| **프로토콜 준수** | 모든 프로토콜 위반을 잡아냄 | AXI handshake, FIFO overflow |
| **제어 로직** | FSM 상태 전이를 완전 검증 | Deadlock 부재 증명 |
| **데이터 무결성** | 모든 경로에서 데이터 보존 증명 | FIFO: 넣은 것 = 빼낸 것 |
| **리셋 동작** | 리셋 후 모든 상태가 올바른지 | 초기값 검증 |
| **보안 속성** | 특정 조건에서 접근 차단 증명 | "JTAG disabled → 접근 불가" |
| **Connectivity** | 신호 연결 정확성 | SoC 레벨 연결 검증 |

### Formal이 부적합한 영역

| 영역 | 이유 |
|------|------|
| 대규모 데이터 경로 | State Space 폭발 |
| 성능 검증 | Formal은 기능만, 타이밍/처리량 불가 |
| 복잡한 알고리즘 | 암호, 압축 등 → 상태 너무 많음 |
| 전체 SoC | 크기 한계 → 블록 단위 적용 |

---

## Formal Engine의 동작 원리

```
Formal Engine은 수학적 알고리즘으로 회로의 모든 상태를 탐색한다.
시뮬레이션처럼 "실행"하는 것이 아니라, "논리적으로 추론"하는 것이다.

핵심 기술 2가지:

1. SAT (Boolean Satisfiability)
   - 회로를 Boolean 수식으로 변환
   - "이 Property를 위반하는 입력 조합이 존재하는가?"를 풀이
   - 존재하면 → FAILED (그 조합이 반례)
   - 존재하지 않으면 → PROVEN

   RTL →(변환)→ Boolean Formula →(SAT Solver)→ SAT(반례) / UNSAT(증명)

2. SMT (SAT + Theory)
   - SAT에 "이론(Theory)"을 추가: 비트벡터 연산, 배열, 산술 등
   - 32-bit 덧셈을 비트 단위가 아닌 산술 이론으로 처리 → 효율 ↑
   - 현대 Formal 도구(JasperGold 등)는 SAT + SMT 혼합 사용

비유:
  시뮬레이션 = "이 입력을 넣어보니 출력이 맞다"  (실험)
  Formal     = "어떤 입력을 넣어도 출력이 맞을 수밖에 없다" (증명)
```

---

## Induction — BOUNDED와 PROVEN의 차이를 이해하는 열쇠

```
Formal이 "모든 상태"를 증명하는 핵심 기법 = 수학적 귀납법(Induction)

Base Case (기초):
  리셋 직후(cycle 0) → Property 성립?    ✓

Inductive Step (귀납):
  "임의의 cycle N에서 Property가 성립한다고 가정하면,
   cycle N+1에서도 성립하는가?"              ✓

  Base + Inductive Step 모두 통과 → PROVEN (무한 cycle 증명)

BOUNDED란?
  Base Case는 통과했지만, Inductive Step을 증명 못한 경우.
  → "N cycle까지는 확인했지만, 그 이후는 모르겠다"
  → 엔진이 상태 공간을 다 탐색하지 못해 귀납 단계 실패

  ┌──────────────────────────────────────────┐
  │  cycle 0 ─── cycle N ───── cycle ∞      │
  │  ████████████████████░░░░░░░░░░░░░░░     │
  │  ← BOUNDED (N) →    ← 미검증 →          │
  │                                          │
  │  PROVEN이면:                              │
  │  ████████████████████████████████████     │
  │  ← 전체 증명 (무한 cycle) →              │
  └──────────────────────────────────────────┘

Induction 실패 원인과 대응:
  1. 도달 불가능 상태(Unreachable State)에서 귀납 실패
     → Helper Assertion 추가: 중간 상태 불변(invariant)을 명시
  2. 상태 공간이 너무 커서 탐색 한계
     → Abstraction / Assume으로 축소
  3. Property가 너무 복잡
     → 작은 sub-property로 분할 후 각각 증명
```

### 면접에서 이렇게 답하라

**Q: BOUNDED 결과가 나왔을 때 어떻게 하나?**
> "BOUNDED는 N cycle까지만 증명된 것이다. Inductive Step이 실패한 것이므로, (1) Helper Assertion을 추가하여 중간 상태 불변을 명시하거나, (2) Abstraction으로 상태 공간을 줄이거나, (3) Property를 분할하여 각각 증명한다. 실무적으로 BOUNDED depth가 충분히 크면(설계의 최대 latency보다 큰 경우) 실용적으로 수용하기도 한다."

---

## Formal의 핵심 기법

### 1. Assertion-Based (Property Checking) — 가장 핵심

```
SVA로 Property 작성 → Formal Engine(SAT/SMT)이 증명

  assert property (@(posedge clk) disable iff (rst)
    req |-> ##[1:3] ack);  // req 후 1~3 cycle 내 ack

  결과: PROVEN → 어떤 상황에서도 ack가 보장됨 (Induction 성공)
        FAILED → req 후 ack 없는 시나리오 반례 제공 (SAT 해 발견)
        BOUNDED → N cycle까지는 성립, 이후 미검증 (Induction 미완)

  워크플로:
  ┌──────────┐    ┌──────────┐    ┌──────────────┐    ┌──────────┐
  │ RTL 로드  │ → │ SVA 로드  │ → │ Engine 실행   │ → │ 결과 분석 │
  └──────────┘    └──────────┘    └──────────────┘    └──────────┘
                                   prove -all          PROVEN/FAILED/
                                                       BOUNDED
```

### 2. Equivalence Checking (동등성 검증)

```
두 설계가 기능적으로 동일한지 검증:

  사용 시나리오:
  ┌───────────────────────────────────────────────────────────┐
  │ (a) RTL vs RTL (Sequential Equivalence, SEQ)              │
  │     - 리팩토링, 최적화, ECO 후 동일성 확인                │
  │     - "코드를 바꿨는데, 기능이 달라지지 않았는가?"        │
  │     - FSM 재인코딩, 파이프라인 단계 변경 등 검증 가능     │
  │                                                           │
  │ (b) RTL vs Netlist (Logic Equivalence, LEC)               │
  │     - 합성(Synthesis) 후 동일성 확인                      │
  │     - "합성 도구가 로직을 바꾸지 않았는가?"               │
  │     - Synopsys Formality, Cadence Conformal 등 사용       │
  │                                                           │
  │ (c) C/C++ vs RTL (HLS 검증)                               │
  │     - HLS 생성 RTL이 원본 C++ 알고리즘과 동일한지         │
  │     - 실무에서는 C-sim + Co-sim으로 대체하는 경우 많음    │
  └───────────────────────────────────────────────────────────┘

  핵심 개념 — Miter Circuit:
  ┌──────┐
  │Spec A│──→ out_A ─┐
  └──────┘           ├─ XOR ─→ 0이면 동일, 1이면 차이 발견
  ┌──────┐           │
  │Impl B│──→ out_B ─┘
  └──────┘
  같은 입력에 대해 두 설계의 출력이 항상 동일한지 수학적으로 증명
```

### 3. Connectivity Checking (연결성 검증)

```
SoC 레벨: IP 간 연결이 설계 의도(스펙 시트)와 일치하는지

  왜 필요한가?
  - SoC 통합 시 수천 개 신호 연결 → 수작업 실수 불가피
  - 잘못된 비트 순서, 빠진 연결, 교차 연결 등
  - 시뮬레이션으로는 모든 연결을 검증하기 비현실적

  동작 방식:
  1. 스펙(CSV/Excel)에서 연결 규칙 정의
     | Source           | Destination              |
     |------------------|--------------------------|
     | IP_A.irq         | IntCtrl.input[5]         |
     | DMA.addr[31:0]   | BusFabric.s2_addr[31:0]  |

  2. Formal Engine이 RTL에서 실제 연결 경로를 추적
  3. 스펙과 불일치하는 연결을 자동 보고

  JasperGold의 Connectivity Verification (CON) 앱이 이를 자동화.
  → SoC 통합 검증에서 가장 ROI가 높은 Formal 기법 중 하나
```

---

## State Explosion 문제와 대응 기법

```
Formal의 근본 한계:

  N-bit 레지스터 → 2^N 상태
  10개 × 32-bit 레지스터 → 2^320 상태 → 탐색 불가능

  이것이 Formal의 "설계 크기 한계"의 본질이다.
```

### 대응 기법 1: Abstraction (추상화)

```
불필요한 디테일을 제거하여 상태 공간을 줄이는 핵심 기법.

(a) Blackboxing — 모듈을 블랙박스로 치환
    검증 대상이 아닌 서브모듈을 "입출력만 있는 빈 박스"로 교체
    → 내부 상태가 제거되어 탐색 공간 대폭 축소

    예: 데이터 경로(곱셈기, ALU)를 블랙박스로 → 제어 FSM만 검증
    ┌────────────────────────────────┐
    │  DUT                           │
    │  ┌──────┐    ┌──────────────┐  │
    │  │ FSM  │←──→│ 곱셈기(32bit)│  │ ← 블랙박스 처리
    │  │ (검증)│    │ (블랙박스)   │  │    내부 상태 제거
    │  └──────┘    └──────────────┘  │
    └────────────────────────────────┘

    주의: 블랙박스 출력은 자유(unconstrained)가 됨
    → 필요시 assume으로 출력 범위 제한

(b) Data Abstraction — 데이터 폭 축소
    32-bit 데이터를 2~4-bit으로 축소하여 검증
    제어 로직의 정확성은 데이터 폭에 독립적인 경우 유효

    예: FIFO의 Overflow/Underflow → 데이터 내용이 아니라
        wr_en/rd_en/full/empty 관계가 핵심 → 데이터 폭 무관

(c) Counter Abstraction — 카운터 범위 축소
    32-bit 카운터를 3-bit으로 축소 → 8가지 상태로 검증
    "카운터가 0에서 MAX까지 간다"는 속성은 작은 범위에서도 동일

    예: 타이머가 0→N 카운트 후 이벤트 발생
        N=1000을 N=3으로 축소해도 제어 로직 검증 가능
```

### 대응 기법 2: Assume (환경 제약)

```
입력 공간을 실제 환경에 맞게 제한하여 탐색 공간 축소.

  assume property (@(posedge clk) addr < 256);       // 주소 범위
  assume property (@(posedge clk) mode inside {0,1,2}); // 유효 모드

  ⚠ 과도한 Assume → False PROVEN 위험 (Unit 3에서 상세)
```

### 대응 기법 3: Cut Point (분할 검증)

```
큰 설계를 작은 블록으로 분할하여 각각 Formal 적용.

  ┌────────────────────────────────────────┐
  │  대규모 SoC                             │
  │  ┌─────┐  ┌─────┐  ┌─────┐  ┌─────┐   │
  │  │블록A │──│블록B │──│블록C │──│블록D │   │
  │  └─────┘  └─────┘  └─────┘  └─────┘   │
  └────────────────────────────────────────┘

  각 블록을 독립적으로 Formal 검증:
  - 블록A의 출력 스펙 → 블록B의 Assume으로 사용
  - 블록 간 인터페이스만 정확하면, 전체가 정확

  = Compositional Verification (합성적 검증)
```

### 대응 기법 4: Bounded Proof (제한적 증명)

```
완전 증명이 불가능할 때의 실용적 타협.

  N cycle까지 증명 → "설계의 최대 latency보다 크면 실용적으로 충분"

  예: 파이프라인 depth = 5 stage
      → BOUNDED 20이면 파이프라인 4회 통과 검증 → 실용적으로 안전

  단, BOUNDED는 PROVEN이 아님을 항상 명시해야 한다.
```

---

## Q&A

**Q: Formal Verification이 시뮬레이션보다 나은 점은?**
> "Formal은 모든 가능한 입력/상태를 수학적으로 검증한다 — '전수 검사'이다. 시뮬레이션은 실행된 시나리오만 검증하므로, 테스트하지 않은 코너 케이스에 버그가 숨어 있을 수 있다. Formal에서 PROVEN이면 어떤 시나리오에서도 해당 속성이 성립함을 수학적으로 보장한다. 반면 Formal은 State Explosion으로 큰 설계에 적용이 어렵고, 성능 검증은 불가능하다. 따라서 Formal과 시뮬레이션은 **상호 보완적**으로 사용한다."

**Q: Formal은 어떤 IP에 적합한가?**
> "상태 공간이 관리 가능한 크기의 제어 로직이 최적이다. 구체적으로: (1) FSM — Deadlock/Livelock 부재 증명. (2) 프로토콜 인터페이스 — AXI/AHB handshake 준수. (3) FIFO/Buffer — Overflow/Underflow 부재, 데이터 순서 보존. (4) Arbiter — Starvation 부재, 공정성. (5) 보안 로직 — 접근 제어 규칙. Mapping Table IP는 테이블 조회 로직의 정확성을 Formal로 증명하기에 적합했다."

**Q: Formal Engine은 내부적으로 어떻게 동작하는가?**
> "RTL을 Boolean 수식으로 변환한 뒤 SAT/SMT Solver로 풀이한다. 'Property를 위반하는 입력이 존재하는가?'를 질문하여, 존재하면 FAILED(반례), 불가능하면 PROVEN이다. 증명에는 수학적 귀납법(Induction)을 사용한다 — Base Case(리셋 직후)와 Inductive Step(N→N+1 cycle)을 모두 통과하면 무한 cycle에 대해 증명된다. Inductive Step이 실패하면 BOUNDED 결과가 나온다."

**Q: State Explosion은 어떻게 대응하는가?**
> "핵심은 상태 공간 축소이다. (1) Blackboxing — 검증 대상이 아닌 모듈을 빈 박스로 교체. (2) Data/Counter Abstraction — 데이터 폭이나 카운터 범위를 축소. (3) Assume — 입력을 실제 환경 범위로 제한. (4) Cut Point — 큰 설계를 블록 단위로 분할하여 각각 증명. 이 기법들을 조합하여 Formal이 수렴(PROVEN)하도록 만드는 것이 Formal 엔지니어의 핵심 역량이다."
