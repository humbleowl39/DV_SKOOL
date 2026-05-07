# Module 03 — JasperGold & DV Strategy

<div class="learning-meta">
  <span class="meta-badge meta-level-advanced">📊 Advanced</span>
</div>

!!! objective "학습 목표"
    이 모듈을 마치면:

    - **Apply** JasperGold 워크플로(elaborate → assume → assert → run → analyze)를 따라 단순 IP의 formal 검증을 실행할 수 있다.
    - **Identify** JasperGold의 주요 App(Apex/Functional/CDC/Coverage/Equivalence) 중 시나리오별 적합한 도구를 선택할 수 있다.
    - **Apply** Convergence 전략(Cut Point, Blackbox, Abstraction, Assume tightening)을 BOUNDED 결과에 대해 적용할 수 있다.
    - **Diagnose** Counterexample을 분석해 RTL 버그 vs Assume 부족(false negative)을 구분할 수 있다.
    - **Justify** Sign-off 기준(PROVEN/BOUNDED, Cover, Assume 감사, COI, Property 완전성)을 문서화 형식으로 설명할 수 있다.

!!! info "사전 지식"
    - [Module 01](01_formal_fundamentals.md), [Module 02](02_sva.md)
    - 시뮬레이션 기반 검증 워크플로 이해

## 왜 이 모듈이 중요한가

**Formal 도구 사용은 "PROVEN 받기"와 다릅니다**. 실무에서 BOUNDED를 PROVEN으로 만드는 작업이 시간의 80%를 차지하고, Assume 작성과 감사가 검증 신뢰성의 핵심입니다. **잘못된 Assume = silent false PROVEN** — Formal 엔지니어의 핵심 역량은 도구 조작이 아니라 **Convergence 전략 + Sign-off 책임**입니다.

## 핵심 개념
**JasperGold = Cadence의 Formal Verification 도구. Property Checking, Equivalence Checking, Connectivity Checking 등을 지원. 실무에서는 Formal을 "시뮬레이션 보완 전략"으로 위치시키고, 제어 로직/프로토콜/보안에 집중 적용.**

---

## JasperGold 워크플로

```
1. RTL + SVA 로드
   analyze -sv rtl/mapping_table.sv
   analyze -sv sva/mapping_table_sva.sv

2. Elaborate
   elaborate -top mapping_table

3. Clock / Reset 설정
   clock clk
   reset rst

4. Property 실행
   prove -all           // 모든 assert 증명 시도

5. 결과 확인
   Property p_no_hit_miss:  PROVEN      ← 증명됨
   Property p_data_integrity: PROVEN    ← 증명됨
   Property p_liveness:      BOUNDED 50 ← 50 cycle까지 증명
   Property p_corner_case:   FAILED     ← 반례 발견 → 파형 확인

6. 반례 분석
   visualize -property p_corner_case    // 파형 뷰어
   → 반례 시나리오를 파형으로 확인 → 버그 디버그
```

---

## JasperGold 주요 앱

| 앱 | 용도 | 적용 대상 |
|---|------|----------|
| **Formal Property Verification (FPV)** | SVA Property 증명 | 핵심 — 제어 로직, 프로토콜 |
| **Connectivity Verification (CON)** | SoC 레벨 연결 검증 | IP 간 신호 연결 |
| **Sequential Equivalence (SEQ)** | RTL 변경 전후 동일성 | 리팩토링 검증 |
| **X-Propagation** | X 전파 분석 | 리셋 후 X 상태 |
| **Coverage Unreachability** | 도달 불가 커버리지 식별 | 시뮬레이션 Coverage 보완 |
| **Security Path Verification** | 보안 경로 검증 | 접근 제어 |

---

## Convergence 전략 — BOUNDED에서 PROVEN으로

```
Formal을 돌렸는데 BOUNDED만 나오면? → Convergence 전략이 필요하다.
"Formal 엔지니어의 핵심 역량 = BOUNDED를 PROVEN으로 만드는 것"
```

### 왜 BOUNDED가 나오는가?

```
1. 상태 공간이 너무 큼 → 엔진이 Inductive Step을 증명하지 못함
2. Property가 너무 복잡 → 엔진이 시간/메모리 한계에 도달
3. 도달 불가능 상태에서 귀납 반례 → Helper가 필요함
```

### Convergence 기법 체크리스트

```
┌──────────────────────────────────────────────────────────────┐
│  BOUNDED 결과를 받았을 때 순서대로 시도:                      │
│                                                              │
│  1. Blackboxing (가장 효과적, 가장 먼저)                      │
│     - 검증 대상이 아닌 서브모듈을 블랙박스로 교체             │
│     - 데이터 경로(MUL, ALU 등)를 우선 블랙박스 대상           │
│     - JasperGold: abstract -module <module_name>             │
│                                                              │
│  2. Counter/Data Abstraction                                 │
│     - 큰 카운터를 작은 범위로 축소                            │
│     - 넓은 데이터 버스를 좁은 폭으로 축소                    │
│     - JasperGold: abstract -counter, 또는 파라미터 재정의    │
│                                                              │
│  3. Helper Assertion (Induction 보조)                        │
│     - Induction 실패 원인: 도달 불가능 상태에서 귀납 반례    │
│     - 해결: 중간 상태 불변(invariant)을 assert로 추가        │
│     - 엔진이 "이 상태는 도달 불가능"임을 알게 됨             │
│                                                              │
│  4. Assume 추가 (주의: 최소한으로)                            │
│     - 입력 제약을 추가하여 탐색 공간 축소                    │
│     - 반드시 cover로 과도하지 않은지 검증                    │
│                                                              │
│  5. Property 분할                                            │
│     - 하나의 복잡한 Property를 여러 sub-property로 분할      │
│     - 각각 독립적으로 증명 → 조합하면 원래 property 증명     │
│                                                              │
│  6. Bounded Proof 수용 (마지막 수단)                         │
│     - Depth가 설계의 최대 latency보다 충분히 크면 수용       │
│     - 반드시 sign-off 문서에 BOUNDED 사유와 depth 기록       │
└──────────────────────────────────────────────────────────────┘
```

### Helper Assertion 예시

```systemverilog
// 원래 Property: FSM이 IDLE에서 시작하면 항상 IDLE로 돌아옴
// → BOUNDED — 왜? 엔진이 불가능한 중간 상태를 탐색함

// Helper: "state는 반드시 유효한 값만 가진다" (Induction 보조)
assert property (@(posedge clk) disable iff (rst)
  state inside {IDLE, SETUP, ACTIVE, DONE}            // helper
);

// Helper: "ACTIVE 상태에서 counter는 항상 > 0" (불변 명시)
assert property (@(posedge clk) disable iff (rst)
  state == ACTIVE |-> counter > 0                     // helper
);

// 이제 엔진이 불가능한 상태를 배제하고 Induction 성공 → PROVEN
```

---

## Blackboxing & Cut Point 상세

### Blackboxing

```
JasperGold에서 모듈을 블랙박스로 처리:

  # TCL
  abstract -module mul_32x32       # 32x32 곱셈기를 블랙박스
  abstract -module data_memory     # 데이터 메모리를 블랙박스

  블랙박스의 출력:
  - 모든 가능한 값을 자유롭게 생성 (unconstrained)
  - 필요시 assume으로 출력 제약:
    assume property (@(posedge clk) mul_out < 32'hFFFF_FFFF);

  블랙박스 대상 선정 기준:
  ┌───────────────────────────────────────────┐
  │ 블랙박스 적합           │ 블랙박스 부적합  │
  ├───────────────────────────────────────────┤
  │ 데이터 경로 (ALU, MUL)  │ 검증 대상 FSM    │
  │ 메모리 (SRAM, ROM)      │ 제어 로직        │
  │ 외부 IP (검증 완료)     │ 프로토콜 핸들러  │
  │ 아날로그 블록 모델      │ 타겟 Property와   │
  │                         │ 관련된 모듈      │
  └───────────────────────────────────────────┘
```

### Cut Point

```
신호를 "자유 입력"으로 교체하여 종속성 끊기:

  # 파이프라인의 중간 단계를 자유 입력으로 교체
  # → 앞단과 뒷단을 독립적으로 검증 가능

  Stage1 ──→ [Cut Point] ──→ Stage2
             (자유 입력)

  Stage1 검증: 입력 → Stage1 출력이 스펙과 일치?
  Stage2 검증: (자유 입력 + assume) → Stage2 출력이 스펙과 일치?

  주의: Cut Point의 assume이 Stage1의 실제 출력 범위를 포함해야 함
```

---

## Formal 디버깅 기법

### Counterexample (반례) 분석

```
FAILED 결과의 반례(Counterexample)는 Formal의 가장 큰 장점 중 하나.
시뮬레이션과 달리, 최소한의 입력 시퀀스로 버그를 재현한다.

  반례 분석 절차:
  1. JasperGold에서 반례 파형 열기 (visualize -property <name>)
  2. Antecedent(전제) 시점 확인 — Property 검사가 시작되는 시점
  3. 입력 시퀀스 추적 — 엔진이 생성한 입력의 의미 파악
  4. 위반 시점 확인 — 어느 cycle에서 Property가 깨지는가
  5. RTL 코드와 대조 — 해당 경로에서 어떤 로직이 잘못되었는가

  반례의 특성:
  - 최소 길이: 엔진이 가장 짧은 위반 경로를 찾음
  - 구체적: 모든 입력 값이 명시됨 → 시뮬레이션으로 재현 가능
  - 결정적: 같은 조건에서 항상 같은 반례
```

### 실제로는 버그가 아닌 FAILED — False Negative 대응

```
FAILED인데 실제 버그가 아닌 경우:

  1. Assume 부족: 실제 환경에서 불가능한 입력이 반례에 사용됨
     → assume 추가로 해당 입력 배제
     → 하지만 먼저 "정말 불가능한 입력인지" 스펙 확인!

  2. 초기화 부족: 리셋 후 일부 레지스터가 X/미초기화
     → RTL에서 초기값을 명시하거나, assume으로 초기 상태 제약

  3. Property 오류: SVA 자체가 잘못 작성됨
     → 반례를 보고 Property 의도와 대조
```

### BOUNDED 디버깅

```
BOUNDED depth를 늘리는 것만으로는 해결 안 됨 → 근본 원인 파악 필요.

  JasperGold 디버깅 명령:
  - check_coi -property <name>    # Cone of Influence 분석
    → 이 Property에 영향을 주는 로직 범위 확인
    → 불필요하게 큰 COI → 블랙박스 대상 식별

  - get_property_info              # Property별 상태 상세
  - visualize -bounded_trace       # BOUNDED 시점의 상태 확인
```

---

## Formal Sign-off 기준

```
Formal 검증을 "완료"로 선언하기 위한 체크리스트:

┌──────────────────────────────────────────────────────────────┐
│  Formal Sign-off Checklist                                   │
│                                                              │
│  □ 모든 assert property가 PROVEN 또는 정당한 BOUNDED         │
│    - BOUNDED인 경우: depth > 설계 최대 latency, 사유 문서화  │
│                                                              │
│  □ 모든 cover property가 COVERED                             │
│    - UNCOVERED인 cover 없음 (Vacuous Pass 가능성 배제)       │
│                                                              │
│  □ Assume 감사(Audit) 완료                                   │
│    - 모든 assume이 스펙/프로토콜에 근거함                    │
│    - 각 assume에 대응하는 cover가 COVERED                    │
│    - 과도한 assume 없음 확인                                 │
│                                                              │
│  □ Cone of Influence (COI) 검토                              │
│    - 블랙박스된 모듈이 Property에 영향 없음 확인             │
│                                                              │
│  □ Property 완전성(Completeness)                             │
│    - 설계 스펙의 모든 요구사항이 Property로 표현됨           │
│    - Coverage Unreachability 분석으로 사각지대 확인          │
│                                                              │
│  □ 결과 문서화                                               │
│    - Property 목록 + 결과(PROVEN/BOUNDED/waiver)             │
│    - Assume 목록 + 근거                                      │
│    - 블랙박스/Abstraction 목록 + 정당성                      │
└──────────────────────────────────────────────────────────────┘
```

---

## Assume 전략 — Formal의 성패를 좌우

### Assume이 필요한 이유

```
DUT의 입력이 제약 없이 자유로우면:
  - Formal 엔진이 불가능한 입력 조합도 탐색
  - 실제로는 발생할 수 없는 시나리오에서 FAILED 보고 (False Negative)
  - 탐색 공간이 너무 커서 BOUNDED로 끝남

적절한 Assume:
  - 실제 환경에서 가능한 입력만으로 제한
  - 프로토콜 규칙 (예: valid 없이 data 변경 안 됨)
  - 물리적 제약 (예: 주소 범위)
```

### Assume 과다 위험

```
Assume이 너무 많으면:
  → 실제 발생 가능한 시나리오까지 배제
  → PROVEN이지만 실제 버그를 놓침 (False PROVEN!)

대응: Cover로 검증
  cover property (특정 시나리오);
  → COVERED면 assume이 이 시나리오를 배제하지 않음
  → UNCOVERED면 assume이 과도하다는 신호!
```

### 실무 Assume 가이드

| Assume 유형 | 예시 | 위험도 |
|------------|------|--------|
| 프로토콜 규칙 | `valid → stable(data)` | 안전 (프로토콜 스펙) |
| 물리적 제약 | `addr < MAX_ADDR` | 안전 (설계 제약) |
| 입력 상호 관계 | `!(wr_en && rd_en)` | **주의** — 실제로 동시 가능한가? |
| 상태 제약 | `state != ILLEGAL` | **위험** — 버그로 도달할 수도 |

---

## Mapping Table IP Formal 검증 (이력서 직결)

### Mapping Table이란?

```
Mapping Table:
  Key → Value 매핑을 저장하는 HW 테이블
  예: 가상 주소 → 물리 주소, 태그 → 데이터

  연산:
  - Lookup: Key로 검색 → Hit(Value 반환) / Miss
  - Insert: 새 Key-Value 쌍 추가
  - Delete: Key로 항목 삭제
  - Update: 기존 Key의 Value 변경
```

### Formal로 증명한 Property들

```systemverilog
// 1. Hit/Miss 상호 배타
assert property (@(posedge clk) disable iff (rst)
  !(hit && miss)
);

// 2. 데이터 무결성: Insert한 데이터가 Lookup에서 정확히 반환
assert property (@(posedge clk) disable iff (rst)
  (insert_en && key == K && value == V)
  |-> s_eventually (lookup_en && key == K && hit && result == V)
);

// 3. Delete 후 Miss
assert property (@(posedge clk) disable iff (rst)
  (delete_en && key == K) ##1 (lookup_en && key == K)
  |-> miss
);

// 4. Overflow 방지: 테이블이 Full이면 Insert 거부
assert property (@(posedge clk) disable iff (rst)
  table_full |-> !insert_success
);

// 5. 빈 테이블에서 모든 Lookup은 Miss
assert property (@(posedge clk) disable iff (rst)
  table_empty && lookup_en |-> miss
);
```

### Formal이 Mapping Table에 적합한 이유

| 이유 | 설명 |
|------|------|
| 상태 공간 관리 가능 | 테이블 크기가 제한적 (수십~수백 엔트리) |
| 기능 명세가 명확 | Insert/Lookup/Delete의 기대 동작이 수학적으로 정의 가능 |
| 시뮬레이션으로 놓치기 쉬운 코너 | Delete 직후 Lookup, Full 상태에서 Insert+Delete 동시 등 |
| 전수 검사 가치 높음 | 모든 Key 조합에서 정확성 보장 필요 |

---

## Formal + Simulation 병행 전략

```
+------------------------------------------------------------------+
|  Verification Strategy                                            |
|                                                                   |
|  Formal (JasperGold):                                             |
|    - 제어 로직 (FSM, Arbiter, Scheduler)                         |
|    - 프로토콜 준수 (AXI handshake, FIFO)                         |
|    - 보안 속성 (접근 제어, 보안 상태)                             |
|    - 리셋 동작 (초기값)                                           |
|    - Connectivity (SoC 레벨)                                      |
|                                                                   |
|  Simulation (UVM):                                                |
|    - 데이터 경로 (E2E 데이터 무결성)                              |
|    - 성능 (처리량, 지연)                                          |
|    - 복잡한 시나리오 (멀티 에이전트 상호작용)                     |
|    - Coverage Closure                                             |
|    - 대규모 통합 검증                                             |
|                                                                   |
|  공유: SVA를 Bind로 작성 → 양쪽에서 재사용                       |
+------------------------------------------------------------------+
```

---

## Q&A

**Q: Mapping Table IP에 Formal을 적용한 경험을 설명하라.**
> "JasperGold FPV로 Mapping Table의 핵심 속성 5가지를 증명했다: (1) Hit/Miss 상호 배타 (2) Insert-Lookup 데이터 무결성 (3) Delete 후 Miss (4) Full 시 Insert 거부 (5) Empty 시 모든 Lookup Miss. Formal이 적합했던 이유는 테이블 크기가 제한적이어서 State Space가 관리 가능했고, 시뮬레이션으로는 모든 Key 조합을 커버하기 어려운 코너 케이스(Delete 직후 같은 Key Lookup 등)를 전수 검사할 수 있었기 때문이다."

**Q: Formal과 시뮬레이션을 어떻게 병행하는가?**
> "역할을 분리한다. Formal은 제어 로직, 프로토콜, 보안, 리셋 등 '모든 상태에서 반드시 참'인 속성을 증명한다. 시뮬레이션은 데이터 경로 E2E, 성능, 대규모 통합 등 Formal이 State Explosion으로 처리 못하는 영역을 커버한다. SVA를 Bind 모듈로 작성하면 같은 Assertion을 두 환경에서 재사용할 수 있어 효율적이다."

**Q: Assume이 잘못되면 어떤 문제가 생기는가?**
> "Assume이 과도하면 실제 발생 가능한 시나리오를 배제하여 PROVEN이 나와도 실제로는 버그가 있는 False PROVEN이 발생할 수 있다. 이를 방지하려면 모든 Assume에 대응하는 Cover를 작성하여 '이 시나리오가 여전히 도달 가능한가'를 확인해야 한다. Cover가 UNCOVERED이면 Assume이 과도하다는 신호이다."

**Q: BOUNDED 결과를 PROVEN으로 만들려면 어떻게 하는가?**
> "Convergence 전략을 순서대로 적용한다. (1) Blackboxing — 검증 대상이 아닌 서브모듈을 블랙박스로 교체하여 상태 공간을 줄인다. (2) Counter/Data Abstraction — 큰 카운터나 넓은 데이터 폭을 축소한다. (3) Helper Assertion — Induction이 실패하는 원인인 도달 불가능 상태를 중간 불변(invariant)으로 배제한다. (4) Property 분할 — 복잡한 Property를 작은 sub-property로 나눠 각각 증명한다. 이 모든 방법으로도 안 되면, BOUNDED depth가 설계 최대 latency보다 충분히 큰지 확인하고 정당한 BOUNDED로 수용한다."

**Q: Formal 검증의 Sign-off 기준은?**
> "다섯 가지이다. (1) 모든 assert가 PROVEN 또는 정당한 BOUNDED. (2) 모든 cover가 COVERED — Vacuous Pass 가능성 배제. (3) Assume 감사 — 모든 assume이 스펙에 근거하고, 대응 cover가 COVERED. (4) COI 검토 — 블랙박스가 Property에 영향 없음 확인. (5) Property 완전성 — 스펙의 모든 요구사항이 Property로 표현됨. 이 다섯 가지를 문서로 남기는 것이 Sign-off이다."

**Q: Formal 디버깅에서 Counterexample을 어떻게 활용하는가?**
> "Counterexample은 Formal의 가장 큰 장점이다. 엔진이 Property 위반을 유발하는 최소 입력 시퀀스를 자동 생성하므로, (1) 반례 파형에서 위반 시점을 확인하고, (2) 엔진이 생성한 입력의 의미를 파악하고, (3) RTL 코드에서 해당 경로의 로직을 추적하여 버그를 확정한다. 단, FAILED인데 실제 버그가 아닌 경우(False Negative)도 있다 — 이는 Assume 부족으로 불가능한 입력이 사용된 것이므로, 스펙을 확인한 후 assume을 추가한다."

---

!!! warning "실무 주의점 — Blackbox 후 false counterexample"
    **현상**: state-explosion 을 풀려고 sub-module 을 blackbox 했더니 갑자기 reasonable 한 property 가 fail 하면서 이상한 counterexample (CEX) 가 등장한다. 시간을 들여 디버그하다 보면 blackbox 출력에 "임의 값" 이 들어와서 발생한 가짜 violation 이다.

    **원인**: blackbox 는 해당 모듈의 출력에 대한 모든 가정을 제거한다. 즉 tool 은 "blackbox 출력이 어떤 값이든 가질 수 있다" 고 가정하고 worst case 를 찾는다. 실제로 그 출력은 spec 에 의해 제약되지만 그것을 명시하지 않으면 false CEX 가 나온다.

    **점검 포인트**: blackbox 사용 시 반드시 그 모듈의 spec 동작을 `assume` 으로 모델링 (예: handshake protocol, output range). Over-constraint 가 되지 않도록 simulation 에서 같은 assume 들이 위반되지 않는지 cross-check. 의심되는 CEX 는 blackbox 입출력 신호의 trace 부터 확인.

## 핵심 정리

- **JasperGold 워크플로**: elaborate → assume(입력 제약) → assert(spec 규칙) → run → analyze.
- **App 선택**: 일반 property는 JG-Apex, RTL2RTL은 Equivalence Checking, CDC 검증은 CDC App, Connectivity는 Connectivity App.
- **BOUNDED → PROVEN**: Cut Point로 분할, Blackbox로 무관 영역 제거, Abstraction으로 카운터/데이터 축소, Assume tightening으로 입력 공간 축소.
- **CEX 분석 3단계**: 위반 시점 확인 → 엔진 입력 의미 파악 → RTL 경로 추적. False negative 의심되면 Assume 부족인지 점검.
- **Sign-off 기준**: (1) assert PROVEN/BOUNDED 정당성, (2) cover COVERED, (3) Assume 감사, (4) COI 검토, (5) Property 완전성. 5개 모두 문서화.
- **Assume의 양면성**: 실제 환경 제약 모델링은 필요하지만 over-constraint는 false PROVEN. Spec과 1:1 매핑 + 대응 cover 작성.

## 다음 단계

- 📝 [**Module 03 퀴즈**](quiz/03_jaspergold_and_strategy_quiz.md)
- ➡️ [**Module 04 — Quick Reference Card**](04_quick_reference_card.md)

<div class="chapter-nav">
  <a class="nav-prev" href="../02_sva/">
    <div class="nav-label">◀ 이전</div>
    <div class="nav-title">SVA (SystemVerilog Assertions)</div>
  </a>
  <a class="nav-next" href="../04_quick_reference_card/">
    <div class="nav-label">다음 ▶</div>
    <div class="nav-title">Formal Verification — Quick Reference Card</div>
  </a>
</div>
