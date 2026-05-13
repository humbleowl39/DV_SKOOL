# Module 03 — JasperGold & DV Strategy

<!-- DV-SKOOL-CH-CTX:start -->
<div class="chapter-context" data-cat="core">
  <a class="chapter-back" href="../">
    <span class="chapter-back-arrow">←</span>
    <span class="chapter-back-icon">✅</span>
    <span class="chapter-back-text">Formal Verification</span>
  </a>
  <span class="chapter-divider">›</span>
  <span class="chapter-marker">Module 03</span>
</div>
<!-- DV-SKOOL-CH-CTX:end -->

<!-- DV-SKOOL-CH-TOC:start -->
<div class="page-toc">
  <span class="page-toc-label">목차</span>
  <a class="page-toc-link" href="#1-why-care-이-모듈이-왜-필요한가">1. Why care?</a>
  <a class="page-toc-link" href="#2-intuition-비유와-한-장-그림">2. Intuition</a>
  <a class="page-toc-link" href="#3-작은-예-bounded-fsm-property-를-helper-invariant-로-proven-시키기">3. 작은 예 — BOUNDED → PROVEN</a>
  <a class="page-toc-link" href="#4-일반화-jaspergold-워크플로-와-앱-라인업">4. 일반화 — 워크플로 + App 라인업</a>
  <a class="page-toc-link" href="#5-디테일-convergence-blackbox-debug-sign-off-mapping-table">5. 디테일 — Convergence, Blackbox, Sign-off</a>
  <a class="page-toc-link" href="#6-흔한-오해-와-dv-디버그-체크리스트">6. 흔한 오해 + 디버그</a>
  <a class="page-toc-link" href="#7-핵심-정리-key-takeaways">7. 핵심 정리</a>
</div>
<!-- DV-SKOOL-CH-TOC:end -->

!!! objective "학습 목표"
    이 모듈을 마치면:

    - **Apply** JasperGold 워크플로 (elaborate → assume → assert → run → analyze) 를 따라 단순 IP 의 formal 검증을 실행할 수 있다.
    - **Identify** JasperGold 의 주요 App (Apex/Functional/CDC/Coverage/Equivalence) 중 시나리오별 적합한 도구를 선택할 수 있다.
    - **Apply** Convergence 전략 (Cut Point / Blackbox / Abstraction / Assume tightening) 을 BOUNDED 결과에 대해 적용할 수 있다.
    - **Diagnose** Counterexample 을 분석해 RTL 버그 vs Assume 부족 (false negative) 을 구분할 수 있다.
    - **Justify** Sign-off 기준 (PROVEN/BOUNDED, Cover, Assume audit, COI, Property 완전성) 을 문서화 형식으로 설명할 수 있다.

!!! info "사전 지식"
    - [Module 01](01_formal_fundamentals.md), [Module 02](02_sva.md)
    - 시뮬레이션 기반 검증 워크플로 이해

---

## 1. Why care? — 이 모듈이 왜 필요한가

### 1.1 시나리오 — _False PROVEN_

당신은 JasperGold 로 _arbiter fairness_ 증명. 결과 **PROVEN**. Sign-off.

Silicon 후: _starvation bug_. 어떻게?

조사: 당신이 작성한 assume:
```
assume property (@(posedge clk) req[0] |=> $past(req[0]));
```
의도: "req[0] 가 _계속_ assert 됨" 가정.

실제 의미: **req[0] 가 한 cycle 후 _반드시_ assert** — _너무 강한_ 제약. Real spec: req[0] 가 _가끔만_ assert. 당신의 assume 이 _real world 보다 강한 가정_ 으로 입력 공간 _축소_ → arbiter 의 _real-world starvation 시나리오_ 가 _제외_ → PROVEN.

**이게 _silent false PROVEN_** — 가장 위험한 Formal 함정.

방어:
- **Assume audit**: 모든 assume 이 _real spec_ 과 _strictly weaker_ or _equal_ 인지 검토.
- **Cover** for each assume: assume 이 _real 가능한 입력_ 을 _제외하지 않는지_ 검증.
- **Assume reduction strategy**: 처음엔 약한 assume, BOUNDED 면 단계적 강화.

**Formal 도구 사용은 "PROVEN 받기" 와 다릅니다**. 실무에서 BOUNDED 를 PROVEN 으로 만드는 작업이 시간의 80% 를 차지하고, Assume 작성과 audit 가 검증 신뢰성의 핵심입니다. Module 01/02 에서 본 property 가 처음에는 거의 항상 BOUNDED 또는 false-CEX 로 시작합니다 — 이를 **Convergence 전략** 으로 수렴시키는 것이 Formal 엔지니어의 역량입니다.

또한 잘못된 Assume = silent false PROVEN — 도구가 PROVEN 을 보고하지만 실제로는 spec 보다 강한 가정으로 입력 공간을 너무 좁힌 결과. Sign-off 시 PROVEN/BOUNDED/Cover/Assume audit/COI 5 가지를 같은 비중으로 문서화하지 않으면 silicon 단계에서 사고가 납니다.

---

## 2. Intuition — 비유와 한 장 그림

!!! tip "💡 한 줄 비유"
    **JasperGold 워크플로** ≈ **법정 절차** — 사건 등록 → 가정 정리 → 주장 제기 → 판결.<br>
    elaborate (사건 등록) → assume (전제 정리) → assert (주장 제기) → run (판결 진행) → analyze (판결 결과 검토). 한 단계라도 빼면 신뢰 불가.

### 한 장 그림 — Property 한 개의 운명 흐름

```d2
direction: down

P: "property P"
R: "결과" { shape: diamond }
P -> R: "prove -all"
PV: "PROVEN"
R -> PV
BD: "BOUNDED"
R -> BD
CX: "CEX"
R -> CX
Q1: "cover 짝 covered?" { shape: diamond }
PV -> Q1
SO: "sign-off 후보" { style.stroke: "#27ae60"; style.stroke-width: 3 }
Q1 -> SO: "YES"
VC: "Vacuous\n(Module 02)" { style.stroke: "#c0392b"; style.stroke-width: 2 }
Q1 -> VC: "NO"
CONV: "Convergence 6 종\n① Blackbox\n② Abstraction\n③ Helper\n④ Assume\n⑤ Split\n⑥ accept bounded\n(Module 03 핵심)"
BD -> CONV
Q2: "실제 버그?" { shape: diamond }
CX -> Q2
RTL: "RTL 수정"
Q2 -> RTL: "Yes"
ASM: "assume 추가"
Q2 -> ASM: "No"
```

§3 에서는 BOUNDED → Helper invariant → PROVEN 의 한 사이클을, §5 에서는 6 가지 Convergence 기법과 5 가지 Sign-off 기준을 다룹니다.

### 왜 이렇게 설계됐는가 — Design rationale

Formal Engine 은 "모든 입력 자유도" 를 가정해서 출발합니다. 그 결과 (1) 입력이 제약 없으면 BOUNDED, (2) 데이터 경로가 크면 BOUNDED, (3) 도달 불가능 상태가 induction 반례를 만들면 BOUNDED — 즉 _첫 실행은 거의 항상 BOUNDED_. 이 BOUNDED 를 PROVEN 으로 끌어올리는 데에 (Blackbox, Helper, Assume, Cut, Split) 5 가지 도구가 정확히 필요합니다. JasperGold 의 명령어 set 도 이 5 가지에 1:1 대응됩니다.

---

## 3. 작은 예 — BOUNDED FSM property 를 Helper invariant 로 PROVEN 시키기

가장 단순한 시나리오. 4-state FSM 의 _liveness_ — `state == BUSY |-> s_eventually (state == IDLE)` — 이 처음에는 BOUNDED 50 으로 끝나고, Helper invariant 한 줄을 추가해 PROVEN 으로 수렴시키는 한 사이클.

```
    Step 0: Spec
    ────────────
    "BUSY 에 들어가면 결국 IDLE 로 돌아온다 (deadlock 없음)"

    Step 1: 첫 SVA + 첫 prove
    ─────────────────────────
    ap_liveness: assert property (
      @(posedge clk) disable iff (rst)
      state == BUSY |-> s_eventually (state == IDLE)
    );
    cp_busy:     cover property (state == BUSY);

    JG 결과:
       ap_liveness : BOUNDED 50
       cp_busy     : covered (trace 1)

    Step 2: 왜 BOUNDED?  (check_coi + visualize -bounded_trace)
    ──────────────────────────────────────────────────────────
    JG 가 inductive step 에서 "state 가 invalid encoding (예: 3'b101)" 인
    가짜 시작 상태를 시도 → 그 상태에서는 IDLE 로 돌아갈 수 없음 → step 실패.
    → 도달 불가능 상태에서의 induction 반례.

    Step 3: Helper invariant 추가
    ─────────────────────────────
    ap_helper_state_valid: assert property (
      @(posedge clk) disable iff (rst)
      state inside {IDLE, SETUP, BUSY, DONE}
    );

    이제 induction 시 "state 가 valid encoding 만 가짐" 을 알게 되어
    가짜 상태에서의 반례가 사라짐.

    Step 4: 다시 prove -all
    ───────────────────────
       ap_helper_state_valid : PROVEN
       ap_liveness           : PROVEN  ⭐
       cp_busy               : covered

    Step 5: Sign-off 체크리스트 (5종)
    ──────────────────────────────────
    □ assert: 전부 PROVEN  ✓
    □ cover : 전부 covered ✓
    □ assume audit : (이 IP 는 assume 0 개)  ✓
    □ COI   : black-box 없음 — 전체 RTL 포함  ✓
    □ 완전성: spec 의 4 가지 transition 규칙 모두 property 화  ✓
    → Sign-off 가능
```

| Step | 누가 | 무엇을 | 왜 |
|---|---|---|---|
| ① | DV 엔지니어 | spec 에서 liveness 요구사항 추출 | "BUSY 에 갇히면 안 됨" → property 후보 |
| ② | DV 엔지니어 | `s_eventually` 로 SVA 작성 + `cover (state == BUSY)` 짝 | Module 02 의 짝 규칙 |
| ③ | JG | elaborate → clock/reset → `prove -all` | 첫 실행 |
| ④ | JG | 결과: BOUNDED 50, cover covered | induction step 미완 — 가짜 상태 의심 |
| ⑤ | DV 엔지니어 | `check_coi -property ap_liveness` 로 영향 범위 확인 | state 변수와 transition logic 만 포함 — 큰 데이터 경로 없음 → blackbox 불필요 |
| ⑥ | DV 엔지니어 | `visualize -bounded_trace` 로 BOUNDED 시점 상태 확인 | state == 3'b101 (잘못된 encoding) 에서 반례 → 도달 불가능 상태 |
| ⑦ | DV 엔지니어 | Helper invariant 추가: `state inside {IDLE, SETUP, BUSY, DONE}` | 도달 불가능 상태를 induction 가정에서 배제 |
| ⑧ | JG | 재실행 → ap_liveness PROVEN | induction step 성공 |
| ⑨ | DV 엔지니어 | Sign-off 5 가지 항목 체크 + 문서화 | §5.5 의 체크리스트 1:1 대응 |

```tcl
# Step ③ ~ ⑧ 의 실제 JG TCL 흐름 (요약)
analyze -sv rtl/fsm.sv
analyze -sv sva/fsm_sva.sv
elaborate -top fsm
clock clk
reset rst
prove -all
# → BOUNDED 50

# 분석
check_coi -property ap_liveness
visualize -bounded_trace -property ap_liveness

# Helper 추가 후 재실행
analyze -sv sva/fsm_sva_helper.sv
elaborate -top fsm
prove -all
# → PROVEN
```

!!! note "여기서 잡아야 할 두 가지"
    **(1) BOUNDED 의 가장 흔한 원인은 _도달 불가능 상태_ 의 induction 반례** — Blackbox/Abstraction 으로 가기 전에 Helper invariant 한 줄로 풀리는 경우가 많다.<br>
    **(2) Sign-off 는 PROVEN 만으로 끝나지 않는다** — cover covered, assume audit, COI 검토, property 완전성까지 5 항목 모두 문서화. 이 흐름이 §5 와 §6 의 모든 디테일을 결정합니다.

---

## 4. 일반화 — JasperGold 워크플로 와 App 라인업

### 4.1 JasperGold 워크플로 (5 단계)

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
   Property p_no_hit_miss:    PROVEN      ← 증명됨
   Property p_data_integrity: PROVEN      ← 증명됨
   Property p_liveness:       BOUNDED 50  ← 50 cycle 까지 증명
   Property p_corner_case:    FAILED      ← 반례 발견 → 파형 확인

6. 반례 분석
   visualize -property p_corner_case    // 파형 뷰어
   → 반례 시나리오를 파형으로 확인 → 버그 디버그
```

### 4.2 JasperGold 주요 앱

| 앱 | 용도 | 적용 대상 |
|---|------|----------|
| **Formal Property Verification (FPV / Apex)** | SVA Property 증명 | 핵심 — 제어 로직, 프로토콜 |
| **Connectivity Verification (CON)** | SoC 레벨 연결 검증 | IP 간 신호 연결 |
| **Sequential Equivalence (SEQ)** | RTL 변경 전후 동일성 | 리팩토링 검증 |
| **X-Propagation** | X 전파 분석 | 리셋 후 X 상태 |
| **Coverage Unreachability** | 도달 불가 커버리지 식별 | 시뮬레이션 Coverage 보완 |
| **Security Path Verification** | 보안 경로 검증 | 접근 제어 |

### 4.3 BOUNDED 가 나오는 3가지 원인

```
1. 상태 공간이 너무 큼 → 엔진이 Inductive Step 을 증명하지 못함
2. Property 가 너무 복잡 → 엔진이 시간/메모리 한계에 도달
3. 도달 불가능 상태에서 귀납 반례 → Helper 가 필요함 (§3 의 케이스)
```

이후 §5 의 Convergence 기법 6 종이 이 3 가지에 1:1 대응합니다.

---

## 5. 디테일 — Convergence, Blackbox, Debug, Sign-off, Mapping Table

### 5.1 Convergence 기법 체크리스트 (BOUNDED → PROVEN)

```
┌──────────────────────────────────────────────────────────────┐
│  BOUNDED 결과를 받았을 때 순서대로 시도:                      │
│                                                              │
│  1. Blackboxing (가장 효과적, 가장 먼저)                      │
│     - 검증 대상이 아닌 서브모듈을 블랙박스로 교체             │
│     - 데이터 경로 (MUL, ALU 등) 를 우선 블랙박스 대상         │
│     - JasperGold: abstract -module <module_name>             │
│                                                              │
│  2. Counter/Data Abstraction                                 │
│     - 큰 카운터를 작은 범위로 축소                            │
│     - 넓은 데이터 버스를 좁은 폭으로 축소                    │
│     - JasperGold: abstract -counter, 또는 파라미터 재정의    │
│                                                              │
│  3. Helper Assertion (Induction 보조)                        │
│     - Induction 실패 원인: 도달 불가능 상태에서 귀납 반례    │
│     - 해결: 중간 상태 불변 (invariant) 을 assert 로 추가     │
│     - 엔진이 "이 상태는 도달 불가능" 임을 알게 됨            │
│                                                              │
│  4. Assume 추가 (주의: 최소한으로)                            │
│     - 입력 제약을 추가하여 탐색 공간 축소                    │
│     - 반드시 cover 로 과도하지 않은지 검증                   │
│                                                              │
│  5. Property 분할                                            │
│     - 하나의 복잡한 Property 를 여러 sub-property 로 분할    │
│     - 각각 독립적으로 증명 → 조합하면 원래 property 증명     │
│                                                              │
│  6. Bounded Proof 수용 (마지막 수단)                         │
│     - Depth 가 설계의 최대 latency 보다 충분히 크면 수용     │
│     - 반드시 sign-off 문서에 BOUNDED 사유와 depth 기록       │
└──────────────────────────────────────────────────────────────┘
```

#### Helper Assertion 예시 (§3 와 동일 패턴 재사용)

```systemverilog
// 원래 Property: FSM 이 IDLE 에서 시작하면 항상 IDLE 로 돌아옴
// → BOUNDED — 왜? 엔진이 불가능한 중간 상태를 탐색함

// Helper: "state 는 반드시 유효한 값만 가진다" (Induction 보조)
assert property (@(posedge clk) disable iff (rst)
  state inside {IDLE, SETUP, ACTIVE, DONE}            // helper
);

// Helper: "ACTIVE 상태에서 counter 는 항상 > 0" (불변 명시)
assert property (@(posedge clk) disable iff (rst)
  state == ACTIVE |-> counter > 0                     // helper
);

// 이제 엔진이 불가능한 상태를 배제하고 Induction 성공 → PROVEN
```

### 5.2 Blackboxing & Cut Point 상세

#### Blackboxing

```
JasperGold 에서 모듈을 블랙박스로 처리:

  # TCL
  abstract -module mul_32x32       # 32x32 곱셈기를 블랙박스
  abstract -module data_memory     # 데이터 메모리를 블랙박스

  블랙박스의 출력:
  - 모든 가능한 값을 자유롭게 생성 (unconstrained)
  - 필요시 assume 으로 출력 제약:
    assume property (@(posedge clk) mul_out < 32'hFFFF_FFFF);

  블랙박스 대상 선정 기준:
  ┌───────────────────────────────────────────┐
  │ 블랙박스 적합           │ 블랙박스 부적합  │
  ├───────────────────────────────────────────┤
  │ 데이터 경로 (ALU, MUL)  │ 검증 대상 FSM    │
  │ 메모리 (SRAM, ROM)      │ 제어 로직        │
  │ 외부 IP (검증 완료)     │ 프로토콜 핸들러  │
  │ 아날로그 블록 모델      │ 타겟 Property 와 │
  │                         │ 관련된 모듈      │
  └───────────────────────────────────────────┘
```

#### Cut Point

신호를 "자유 입력" 으로 교체하여 종속성 끊기:

파이프라인의 중간 단계를 자유 입력으로 교체 → 앞단과 뒷단을 독립적으로 검증 가능.

```d2
direction: right

IN: "입력"
S1: "Stage 1"
IN -> S1
CP: "[Cut Point]\n자유 입력" { style.stroke: "#c0392b"; style.stroke-width: 3; style.stroke-dash: 4 }
S1 -> CP
S2: "Stage 2"
CP -> S2
OUT: "출력"
S2 -> OUT
```

- **Stage1 검증**: 입력 → Stage1 출력이 스펙과 일치?
- **Stage2 검증**: (자유 입력 + assume) → Stage2 출력이 스펙과 일치?

주의: Cut Point 의 assume 이 Stage1 의 실제 출력 범위를 포함해야 함.

### 5.3 Formal 디버깅 기법

#### Counterexample (반례) 분석

```
FAILED 결과의 반례 (Counterexample) 는 Formal 의 가장 큰 장점 중 하나.
시뮬레이션과 달리, 최소한의 입력 시퀀스로 버그를 재현한다.

  반례 분석 절차:
  1. JasperGold 에서 반례 파형 열기 (visualize -property <name>)
  2. Antecedent (전제) 시점 확인 — Property 검사가 시작되는 시점
  3. 입력 시퀀스 추적 — 엔진이 생성한 입력의 의미 파악
  4. 위반 시점 확인 — 어느 cycle 에서 Property 가 깨지는가
  5. RTL 코드와 대조 — 해당 경로에서 어떤 로직이 잘못되었는가

  반례의 특성:
  - 최소 길이: 엔진이 가장 짧은 위반 경로를 찾음
  - 구체적: 모든 입력 값이 명시됨 → 시뮬레이션으로 재현 가능
  - 결정적: 같은 조건에서 항상 같은 반례
```

#### 실제로는 버그가 아닌 FAILED — False Negative 대응

```
FAILED 인데 실제 버그가 아닌 경우:

  1. Assume 부족: 실제 환경에서 불가능한 입력이 반례에 사용됨
     → assume 추가로 해당 입력 배제
     → 하지만 먼저 "정말 불가능한 입력인지" 스펙 확인!

  2. 초기화 부족: 리셋 후 일부 레지스터가 X/미초기화
     → RTL 에서 초기값을 명시하거나, assume 으로 초기 상태 제약

  3. Property 오류: SVA 자체가 잘못 작성됨
     → 반례를 보고 Property 의도와 대조
```

#### BOUNDED 디버깅

```
BOUNDED depth 를 늘리는 것만으로는 해결 안 됨 → 근본 원인 파악 필요.

  JasperGold 디버깅 명령:
  - check_coi -property <name>    # Cone of Influence 분석
    → 이 Property 에 영향을 주는 로직 범위 확인
    → 불필요하게 큰 COI → 블랙박스 대상 식별

  - get_property_info              # Property 별 상태 상세
  - visualize -bounded_trace       # BOUNDED 시점의 상태 확인
```

### 5.4 Assume 전략 — Formal 의 성패를 좌우

#### Assume 이 필요한 이유

```
DUT 의 입력이 제약 없이 자유로우면:
  - Formal 엔진이 불가능한 입력 조합도 탐색
  - 실제로는 발생할 수 없는 시나리오에서 FAILED 보고 (False Negative)
  - 탐색 공간이 너무 커서 BOUNDED 로 끝남

적절한 Assume:
  - 실제 환경에서 가능한 입력만으로 제한
  - 프로토콜 규칙 (예: valid 없이 data 변경 안 됨)
  - 물리적 제약 (예: 주소 범위)
```

#### Assume 과다 위험

```
Assume 이 너무 많으면:
  → 실제 발생 가능한 시나리오까지 배제
  → PROVEN 이지만 실제 버그를 놓침 (False PROVEN!)

대응: Cover 로 검증
  cover property (특정 시나리오);
  → COVERED 면 assume 이 이 시나리오를 배제하지 않음
  → UNCOVERED 면 assume 이 과도하다는 신호!
```

#### 실무 Assume 가이드

| Assume 유형 | 예시 | 위험도 |
|------------|------|--------|
| 프로토콜 규칙 | `valid → stable(data)` | 안전 (프로토콜 스펙) |
| 물리적 제약 | `addr < MAX_ADDR` | 안전 (설계 제약) |
| 입력 상호 관계 | `!(wr_en && rd_en)` | **주의** — 실제로 동시 가능한가? |
| 상태 제약 | `state != ILLEGAL` | **위험** — 버그로 도달할 수도 |

### 5.5 Formal Sign-off 기준

```
Formal 검증을 "완료" 로 선언하기 위한 체크리스트:

┌──────────────────────────────────────────────────────────────┐
│  Formal Sign-off Checklist                                   │
│                                                              │
│  □ 모든 assert property 가 PROVEN 또는 정당한 BOUNDED        │
│    - BOUNDED 인 경우: depth > 설계 최대 latency, 사유 문서화 │
│                                                              │
│  □ 모든 cover property 가 COVERED                            │
│    - UNCOVERED 인 cover 없음 (Vacuous Pass 가능성 배제)      │
│                                                              │
│  □ Assume 감사 (Audit) 완료                                  │
│    - 모든 assume 이 스펙/프로토콜에 근거함                   │
│    - 각 assume 에 대응하는 cover 가 COVERED                  │
│    - 과도한 assume 없음 확인                                 │
│                                                              │
│  □ Cone of Influence (COI) 검토                              │
│    - 블랙박스된 모듈이 Property 에 영향 없음 확인            │
│                                                              │
│  □ Property 완전성 (Completeness)                            │
│    - 설계 스펙의 모든 요구사항이 Property 로 표현됨          │
│    - Coverage Unreachability 분석으로 사각지대 확인          │
│                                                              │
│  □ 결과 문서화                                               │
│    - Property 목록 + 결과 (PROVEN/BOUNDED/waiver)            │
│    - Assume 목록 + 근거                                      │
│    - 블랙박스/Abstraction 목록 + 정당성                      │
└──────────────────────────────────────────────────────────────┘
```

### 5.6 Mapping Table IP Formal 검증 (이력서 직결)

#### Mapping Table 이란?

```
Mapping Table:
  Key → Value 매핑을 저장하는 HW 테이블
  예: 가상 주소 → 물리 주소, 태그 → 데이터

  연산:
  - Lookup: Key 로 검색 → Hit (Value 반환) / Miss
  - Insert: 새 Key-Value 쌍 추가
  - Delete: Key 로 항목 삭제
  - Update: 기존 Key 의 Value 변경
```

#### Formal 로 증명한 Property 들

```systemverilog
// 1. Hit/Miss 상호 배타
assert property (@(posedge clk) disable iff (rst)
  !(hit && miss)
);

// 2. 데이터 무결성: Insert 한 데이터가 Lookup 에서 정확히 반환
assert property (@(posedge clk) disable iff (rst)
  (insert_en && key == K && value == V)
  |-> s_eventually (lookup_en && key == K && hit && result == V)
);

// 3. Delete 후 Miss
assert property (@(posedge clk) disable iff (rst)
  (delete_en && key == K) ##1 (lookup_en && key == K)
  |-> miss
);

// 4. Overflow 방지: 테이블이 Full 이면 Insert 거부
assert property (@(posedge clk) disable iff (rst)
  table_full |-> !insert_success
);

// 5. 빈 테이블에서 모든 Lookup 은 Miss
assert property (@(posedge clk) disable iff (rst)
  table_empty && lookup_en |-> miss
);
```

#### Formal 이 Mapping Table 에 적합한 이유

| 이유 | 설명 |
|------|------|
| 상태 공간 관리 가능 | 테이블 크기가 제한적 (수십~수백 엔트리) |
| 기능 명세가 명확 | Insert/Lookup/Delete 의 기대 동작이 수학적으로 정의 가능 |
| 시뮬레이션으로 놓치기 쉬운 코너 | Delete 직후 Lookup, Full 상태에서 Insert+Delete 동시 등 |
| 전수 검사 가치 높음 | 모든 Key 조합에서 정확성 보장 필요 |

### 5.7 Formal + Simulation 병행 전략

```
+------------------------------------------------------------------+
|  Verification Strategy                                            |
|                                                                   |
|  Formal (JasperGold):                                             |
|    - 제어 로직 (FSM, Arbiter, Scheduler)                          |
|    - 프로토콜 준수 (AXI handshake, FIFO)                          |
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
|  공유: SVA 를 Bind 로 작성 → 양쪽에서 재사용                      |
+------------------------------------------------------------------+
```

### 5.8 면접 골든 답변 6종

**Q: Mapping Table IP 에 Formal 을 적용한 경험을 설명하라.**
> "JasperGold FPV 로 Mapping Table 의 핵심 속성 5가지를 증명했다: (1) Hit/Miss 상호 배타 (2) Insert-Lookup 데이터 무결성 (3) Delete 후 Miss (4) Full 시 Insert 거부 (5) Empty 시 모든 Lookup Miss. Formal 이 적합했던 이유는 테이블 크기가 제한적이어서 State Space 가 관리 가능했고, 시뮬레이션으로는 모든 Key 조합을 커버하기 어려운 코너 케이스 (Delete 직후 같은 Key Lookup 등) 를 전수 검사할 수 있었기 때문이다."

**Q: Formal 과 시뮬레이션을 어떻게 병행하는가?**
> "역할을 분리한다. Formal 은 제어 로직, 프로토콜, 보안, 리셋 등 '모든 상태에서 반드시 참' 인 속성을 증명한다. 시뮬레이션은 데이터 경로 E2E, 성능, 대규모 통합 등 Formal 이 State Explosion 으로 처리 못하는 영역을 커버한다. SVA 를 Bind 모듈로 작성하면 같은 Assertion 을 두 환경에서 재사용할 수 있어 효율적이다."

**Q: Assume 이 잘못되면 어떤 문제가 생기는가?**
> "Assume 이 과도하면 실제 발생 가능한 시나리오를 배제하여 PROVEN 이 나와도 실제로는 버그가 있는 False PROVEN 이 발생할 수 있다. 이를 방지하려면 모든 Assume 에 대응하는 Cover 를 작성하여 '이 시나리오가 여전히 도달 가능한가' 를 확인해야 한다. Cover 가 UNCOVERED 이면 Assume 이 과도하다는 신호이다."

**Q: BOUNDED 결과를 PROVEN 으로 만들려면 어떻게 하는가?**
> "Convergence 전략을 순서대로 적용한다. (1) Blackboxing — 검증 대상이 아닌 서브모듈을 블랙박스로 교체하여 상태 공간을 줄인다. (2) Counter/Data Abstraction — 큰 카운터나 넓은 데이터 폭을 축소한다. (3) Helper Assertion — Induction 이 실패하는 원인인 도달 불가능 상태를 중간 불변 (invariant) 으로 배제한다. (4) Property 분할 — 복잡한 Property 를 작은 sub-property 로 나눠 각각 증명한다. 이 모든 방법으로도 안 되면, BOUNDED depth 가 설계 최대 latency 보다 충분히 큰지 확인하고 정당한 BOUNDED 로 수용한다."

**Q: Formal 검증의 Sign-off 기준은?**
> "다섯 가지이다. (1) 모든 assert 가 PROVEN 또는 정당한 BOUNDED. (2) 모든 cover 가 COVERED — Vacuous Pass 가능성 배제. (3) Assume 감사 — 모든 assume 이 스펙에 근거하고, 대응 cover 가 COVERED. (4) COI 검토 — 블랙박스가 Property 에 영향 없음 확인. (5) Property 완전성 — 스펙의 모든 요구사항이 Property 로 표현됨. 이 다섯 가지를 문서로 남기는 것이 Sign-off 이다."

**Q: Formal 디버깅에서 Counterexample 을 어떻게 활용하는가?**
> "Counterexample 은 Formal 의 가장 큰 장점이다. 엔진이 Property 위반을 유발하는 최소 입력 시퀀스를 자동 생성하므로, (1) 반례 파형에서 위반 시점을 확인하고, (2) 엔진이 생성한 입력의 의미를 파악하고, (3) RTL 코드에서 해당 경로의 로직을 추적하여 버그를 확정한다. 단, FAILED 인데 실제 버그가 아닌 경우 (False Negative) 도 있다 — 이는 Assume 부족으로 불가능한 입력이 사용된 것이므로, 스펙을 확인한 후 assume 을 추가한다."

---

## 6. 흔한 오해 와 DV 디버그 체크리스트

### 흔한 오해

!!! danger "❓ 오해 1 — 'Blackbox 는 항상 좋다 (state space ↓)'"
    **실제**: Blackbox 는 그 모듈 출력을 "any value" 로 가정 → 종종 false counterexample. assume 으로 spec 동작을 모델링하지 않으면 가짜 fail 만 보고됨.<br>
    **왜 헷갈리는가**: "복잡도 ↓ = 항상 좋다" 는 직관 + blackbox 의 부작용 (over-approximation) 을 첫 학습 때 잘 못 인지.

!!! danger "❓ 오해 2 — 'Assume 을 많이 넣으면 PROVEN 이 빨리 나옴 → 좋다'"
    **실제**: Assume 이 spec 보다 강하면 (over-constraint) PROVEN 이 빨리 나오지만 false PROVEN. 도구는 알려주지 않음 — 모든 assume 마다 spec 항목 1:1 매핑 + 대응 cover covered 여야 함.<br>
    **왜 헷갈리는가**: PROVEN 의 색깔이 초록색이라 "좋은 결과" 로 보이고, audit 가 정성 작업이라 정량 지표만 보는 습관.

!!! danger "❓ 오해 3 — 'Property 완전성은 PROVEN 100% 이면 충족'"
    **실제**: PROVEN 100% 라도 spec 의 일부 요구사항을 property 로 표현 안 했으면 그 영역은 미검증. 완전성 = "spec 의 모든 항목이 property 가 있는가" — 정량 지표로는 안 보임.<br>
    **왜 헷갈리는가**: % PROVEN 이 dashboard 의 메인 metric 으로 표시되어 그 수치만 보면 충분하다고 느낌.

!!! danger "❓ 오해 4 — 'CEX 가 나오면 무조건 RTL 버그'"
    **실제**: CEX 의 입력 시퀀스가 spec 상 도달 불가능한 입력이면 false negative — Assume 부족이 원인. CEX 분석의 1번 step 은 "이 입력이 spec 상 가능한가" 확인.<br>
    **왜 헷갈리는가**: CEX 의 파형이 너무 구체적이어서 "버그" 처럼 보이고, RTL 디버그 본능이 먼저 발동.

!!! danger "❓ 오해 5 — 'BOUNDED depth 만 늘리면 결국 PROVEN 됨'"
    **실제**: BOUNDED 는 induction step 실패의 증상. depth 를 늘려도 step 이 풀리지 않으면 BOUNDED 가 더 큰 N 으로 끝날 뿐. 근본 해결은 Helper invariant 또는 abstraction.<br>
    **왜 헷갈리는가**: depth 가 숫자로 보여서 "더 많이 = 더 좋게" 의 직관이 작동.

### DV 디버그 체크리스트 (JasperGold 운용 시)

| 증상 | 1차 의심 | 어디 보나 |
|---|---|---|
| 첫 prove 후 모두 BOUNDED | 입력 자유도 과다 + Helper 부재 | `check_coi -property` 로 영향 범위 → 큰 datapath blackbox 후보 |
| Helper 추가 후에도 BOUNDED | 도달 불가능 상태가 더 깊은 nesting | `visualize -bounded_trace` 의 state 값을 RTL spec 과 대조하여 추가 invariant 추출 |
| Blackbox 후 갑자기 FAIL (이전엔 PROVEN) | blackbox 출력에 대한 spec 동작 미모델링 | blackbox 모듈의 출력에 대해 spec 동작 `assume` 추가 (handshake protocol, output range) |
| CEX 의 입력 시퀀스가 spec 상 불가능 | Assume 부족 (false negative) | CEX 입력 파형 → spec 의 입력 제약 1:1 매핑 → 누락된 assume 추가 |
| Assume 추가 후 cover 가 UNCOVERED | over-constraint — 실제 가능 시나리오까지 배제 | assume 의 조건을 약화 또는 spec 재검토 |
| 모든 cover 가 COVERED 인데 sim 에서 같은 property 위반 | over-constraint assume 또는 BOUNDED 를 PROVEN 으로 오해 | sign-off 5 항목 audit 재실행 — 특히 assume 의 spec 근거 점검 |
| `s_eventually` 가 자꾸 BOUNDED | 무한 시간 검증인데 induction 만으로는 불가능 | bounded liveness 로 변경 (`##[1:N] ack`) 또는 fairness assume 추가 |
| Connectivity 검증 시 false fail | spec CSV 와 RTL 신호 이름 mismatch | spec table 의 source/destination 신호명을 RTL 의 hierarchy 와 정확히 일치 |

---

## 7. 핵심 정리 (Key Takeaways)

- **JasperGold 워크플로**: elaborate → assume (입력 제약) → assert (spec 규칙) → run → analyze. 5 단계 모두 trace 가능해야 sign-off.
- **App 선택**: 일반 property 는 JG-Apex/FPV, RTL2RTL 은 Equivalence Checking, CDC 검증은 CDC App, Connectivity 는 Connectivity App.
- **BOUNDED → PROVEN (6 단계)**: Blackbox → Abstraction → Helper → Assume (최소) → Property 분할 → Bounded 수용.
- **CEX 분석 3단계**: 위반 시점 확인 → 엔진 입력 의미 파악 → RTL 경로 추적. False negative 의심되면 Assume 부족인지 점검.
- **Sign-off 5 기준**: (1) assert PROVEN/BOUNDED 정당성, (2) cover COVERED, (3) Assume 감사, (4) COI 검토, (5) Property 완전성. 5 개 모두 문서화.
- **Assume 의 양면성**: 실제 환경 제약 모델링은 필요하지만 over-constraint 는 false PROVEN. Spec 과 1:1 매핑 + 대응 cover 작성.

!!! warning "실무 주의점 — Blackbox 후 false counterexample"
    **현상**: state-explosion 을 풀려고 sub-module 을 blackbox 했더니 갑자기 reasonable 한 property 가 fail 하면서 이상한 counterexample (CEX) 가 등장한다. 시간을 들여 디버그하다 보면 blackbox 출력에 "임의 값" 이 들어와서 발생한 가짜 violation 이다.

    **원인**: blackbox 는 해당 모듈의 출력에 대한 모든 가정을 제거한다. 즉 tool 은 "blackbox 출력이 어떤 값이든 가질 수 있다" 고 가정하고 worst case 를 찾는다. 실제로 그 출력은 spec 에 의해 제약되지만 그것을 명시하지 않으면 false CEX 가 나온다.

    **점검 포인트**: blackbox 사용 시 반드시 그 모듈의 spec 동작을 `assume` 으로 모델링 (예: handshake protocol, output range). Over-constraint 가 되지 않도록 simulation 에서 같은 assume 들이 위반되지 않는지 cross-check. 의심되는 CEX 는 blackbox 입출력 신호의 trace 부터 확인.

### 7.1 자가 점검

!!! question "🤔 Q1 — Convergence 전략 (Bloom: Apply)"
    Property BOUNDED. 어떻게 PROVEN?

    ??? success "정답"
        4 가지 시도 (순서):
        1. **Helper invariant**: 작은 보조 property → tool 이 _state space 좁힘_ 가능.
        2. **Blackbox unrelated module**: state explosion 의 원인 module 격리.
        3. **Cut point**: 특정 신호를 _free input_ 으로 → state 감소.
        4. **Time bound 조정**: max bound 명시 + sign-off 위험 문서화 (마지막 수단).

        각 시도 후 simulation cross-check (over-constraint 방어).

!!! question "🤔 Q2 — Assume audit (Bloom: Analyze)"
    Sign-off 시 _모든 assume_ audit 어떻게?

    ??? success "정답"
        각 assume 마다:
        1. **Spec 1:1 매핑**: 해당 assume 이 _spec 의 어느 줄_ 과 일치하는지 추적.
        2. **Cover 짝**: assume 의 condition 이 _real-world 에서 도달 가능_ 한지 cover 로 확인.
        3. **Simulation cross-check**: simulation 에서 _이 assume 이 위반되지 않는지_ runtime check.
        4. **Reviewer signature**: spec 작성자가 _내 spec 과 일치_ 확인.

!!! question "🤔 Q3 — Sign-off 5 기준 (Bloom: Evaluate)"
    Sign-off 시 _어떤 5 가지_ 를 보고서에 포함?

    ??? success "정답"
        1. **PROVEN list**: 수학적 보장된 property.
        2. **BOUNDED list**: bound + 그 bound 가 _운영 시간 cover_ 함.
        3. **Cover hit list**: 모든 assert 의 antecedent _도달_.
        4. **Assume audit**: 모든 assume _spec 매핑 검증_.
        5. **COI (Cone of Influence)**: 검증되지 않은 영역 명시.

        5 가지 모두 _문서_ → reviewer 가 _가정 + 결과_ 모두 검토 가능.

### 7.2 출처

**External**
- Cadence JasperGold User Guide
- Synopsys VC Formal Reference
- *Formal Verification Methodology Cookbook* — Cadence
- ISSCC / DAC formal verification papers

---

## 다음 모듈

→ [Module 04 — Quick Reference Card](04_quick_reference_card.md): SVA 연산자, Convergence 순서, Sign-off 5 기준의 한 페이지 치트시트 — 면접/코드리뷰/디버그 중 빠른 확인용.

[퀴즈 풀어보기 →](quiz/03_jaspergold_and_strategy_quiz.md)

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


--8<-- "abbreviations.md"
