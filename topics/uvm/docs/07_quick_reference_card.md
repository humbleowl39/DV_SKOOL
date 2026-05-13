# Module 07 — Quick Reference Card

<!-- DV-SKOOL-CH-CTX:start -->
<div class="chapter-context" data-cat="core">
  <a class="chapter-back" href="../">
    <span class="chapter-back-arrow">←</span>
    <span class="chapter-back-icon">🧪</span>
    <span class="chapter-back-text">UVM</span>
  </a>
  <span class="chapter-divider">›</span>
  <span class="chapter-marker chapter-quickref-marker">★ Quick Reference</span>
</div>
<!-- DV-SKOOL-CH-CTX:end -->

<!-- DV-SKOOL-CH-TOC:start -->
<div class="page-toc">
  <span class="page-toc-label">목차</span>
  <a class="page-toc-link" href="#1-why-care-치트시트가-필요한-이유">1. Why care?</a>
  <a class="page-toc-link" href="#2-intuition-공구함-과-한-장-그림">2. Intuition</a>
  <a class="page-toc-link" href="#3-작은-예-한-장-치트시트로-자주-쓰는-시나리오-9-개">3. 작은 예 — 한 장 치트시트</a>
  <a class="page-toc-link" href="#4-일반화-7-주제-별-한-줄-요약">4. 일반화 — 7 주제 한 줄 요약</a>
  <a class="page-toc-link" href="#5-디테일-환경-구조-factory-phase-안티패턴-면접-룰-사내-연결">5. 디테일</a>
  <a class="page-toc-link" href="#6-흔한-오해-와-이-카드를-봐야-할-때">6. 흔한 오해 + 이 카드를 봐야 할 때</a>
  <a class="page-toc-link" href="#7-핵심-정리-key-takeaways">7. 핵심 정리</a>
</div>
<!-- DV-SKOOL-CH-TOC:end -->

!!! objective "사용 목적"
    이 페이지는 **참조용 치트시트** 입니다. 정독 자료가 아니라 _인터뷰 / 코드 리뷰 / 디버그_ 중에 빠르게 펴보는 용도. 새로 배우는 사람은 [Module 01-06](01_architecture_and_phase.md) 부터 보고 마지막에 이 페이지로 정리.

    이 카드를 마치면:

    - **Recall** UVM 핵심 매크로 / Phase / 패턴 이름을 즉시 떠올릴 수 있다.
    - **Reference** 면접 / 리뷰 중 한눈에 확인 (5-Whys 같은 골든 룰 포함).
    - **Identify** 안티패턴을 한눈에 식별하고 대체 패턴을 즉시 떠올릴 수 있다.

!!! info "사전 지식"
    - [Module 01-06](01_architecture_and_phase.md) 학습 완료 후 이 카드를 보면 효과 극대화

---

## 1. Why care? — 치트시트가 필요한 이유

UVM 의 Class 만 200 개 + 매크로 100 개. 외울 게 아니라 **"문제 → 해당 패턴 매핑"** 의 신호 인지가 마스터의 핵심입니다. 이 카드는 그 _인덱스_.

면접에서 5 분 안에 답해야 할 때, 코드 리뷰에서 _"이 부분 안티패턴인 것 같은데 어떤 거였더라"_ 의 순간, 디버그 중 _"raise/drop 의 정확한 패턴이 뭐였더라"_ 의 순간 — 이 한 페이지로 즉시 해결.

---

## 2. Intuition — 공구함, 과 한 장 그림

!!! tip "💡 한 줄 비유"
    **UVM 마스터 = 도구 인지** ≈ **공구함 — 어떤 도구를 언제 꺼낼지 아는 능력**.<br>
    UVM 의 가치는 _"어떻게 쓰는지"_ 보다 _"언제 어느 패턴을 꺼낼지"_ 의 직관. 이 cheat sheet 가 그 인덱스 역할.

### 한 장 그림 — UVM 환경 구조 한눈에

```d2
direction: down

TST: "uvm_test"
ENV: "uvm_env"
AGA: "uvm_agent (Active)"
DRV: "uvm_driver\n_DUT 에 자극_"
MON: "uvm_monitor\n_DUT 관찰 → AP_"
SQR: "uvm_sequencer\n_Sequence ↔ Driver 중개_"
AGP: "uvm_agent (Passive)"
MONP: "uvm_monitor\n_출력 관찰 → AP_"
SB: "uvm_scoreboard\n_기대값 vs 실제값 비교_"
SUB: "uvm_subscriber\n_Coverage 수집_"
TST -> ENV
ENV -> AGA
AGA -> DRV
AGA -> MON
AGA -> SQR
ENV -> AGP
AGP -> MONP
ENV -> SB
ENV -> SUB
```

> 가로축: 자극 → 관찰 → 비교 → 커버리지<br>
> 세로축: build → connect → run → cleanup

---

## 3. 작은 예 — 한 장 치트시트로 자주 쓰는 시나리오 9 개

| # | 시나리오 | 패턴 / 매크로 | 한 줄 |
|---|---|---|---|
| 1 | 컴포넌트 생성 | `my_class::type_id::create("name", parent)` | factory override 가 적용 — `new()` 직접 호출 금지 |
| 2 | Object 생성 | `my_item::type_id::create("item")` | parent 없음 (uvm_object) |
| 3 | vif 전달 | top: `set(null, "*", "vif", intf)` / driver: `get(this, "", "vif", vif)` | 경로 매칭 + `if (!get(...)) uvm_fatal` |
| 4 | Active/Passive 분기 | `if (get_is_active() == UVM_ACTIVE) drv = ...` | Passive 시 driver/sequencer 안 만듦 |
| 5 | Sequence body | `start_item → randomize with → finish_item` | 3 단계 모두 필요 |
| 6 | Test 시나리오 | `phase.raise_objection(this); seq.start(env.agent.sqr); phase.drop_objection(this, "done", drain);` | drain time 으로 마지막 transaction 보장 |
| 7 | Monitor → SB / Coverage | `mon.ap.connect(sb.imp); mon.ap.connect(cov.analysis_export);` | 1:N broadcast — 새 subscriber 추가도 monitor 변경 없음 |
| 8 | Type override | `set_type_override_by_type(my_drv::get_type(), enh_drv::get_type())` | base_test 의 build_phase 에서 |
| 9 | Coverage sample | Monitor.write 콜백 안에서 `cg.sample()` | 호출 누락 시 coverage 0 |

!!! note "여기서 잡아야 할 두 가지"
    **(1) 모든 컴포넌트 / object 생성은 `type_id::create`** — `new()` 직접 호출은 factory override 우회.<br>
    **(2) `if (!get(...)) uvm_fatal(...)` 은 _패턴_ 이 아니라 _의무_** — silent failure 방지의 가장 중요한 한 줄.

---

## 4. 일반화 — 7 주제 별 한 줄 요약

| 주제 | 핵심 포인트 | 자세히 |
|------|------------|------|
| 클래스 계층 | `uvm_object` (데이터) / `uvm_component` (인프라, Phase 있음) | [M01](01_architecture_and_phase.md) |
| Phase 순서 | build (Top→Down) → connect (Bot→Up) → run (병렬) → check/report | [M01](01_architecture_and_phase.md) |
| Agent | Driver + Monitor + Sequencer, Active/Passive | [M02](02_agent_driver_monitor.md) |
| Driver | Transaction → Pin-level 변환만. DUT 로직 금지 | [M02](02_agent_driver_monitor.md) |
| Monitor | Pin-level → Transaction 변환 + Analysis Port broadcast | [M02](02_agent_driver_monitor.md) |
| Sequence | 시나리오 로직. `start_item → randomize → finish_item` | [M03](03_sequence_and_item.md) |
| Virtual Seq | 멀티 Agent Sequence 조합 (시스템 시나리오) | [M03](03_sequence_and_item.md) |
| config_db | set/get 으로 설정 전달. Config Object 패턴 권장 | [M04](04_config_db_factory.md) |
| Factory | `type_id::create` + Override 로 코드 수정 없이 교체 | [M04](04_config_db_factory.md) |
| TLM | Analysis Port (1:N broadcast), seq_item_port (Driver↔Sqr) | [M05](05_tlm_scoreboard_coverage.md) |
| Scoreboard | Reference Model + 비교 + check_phase 잔여 확인 | [M05](05_tlm_scoreboard_coverage.md) |
| Coverage | Covergroup + Coverpoint + Cross. Closure = 검증 완전성 | [M05](05_tlm_scoreboard_coverage.md) |

### 한 줄 요약

```
UVM = Factory (유연한 생성) + config_db (유연한 설정) + Phase (자동 순서) + TLM (컴포넌트 통신)
       위에 Agent / Scoreboard / Coverage 를 구축하는 _재사용 가능한 검증 프레임워크_.
```

---

## 5. 디테일 — 환경 구조 / Factory / Phase / 안티패턴 / 면접 룰 / 사내 연결

### 5.1 Factory 등록 빠른 참조

```systemverilog
// Component (name + parent)
`uvm_component_utils(my_class)
function new(string name, uvm_component parent);

// Object (name 만)
`uvm_object_utils(my_class)
function new(string name = "my_class");

// 생성
my_class obj = my_class::type_id::create("name", parent);  // component
my_class obj = my_class::type_id::create("name");           // object
```

### 5.2 Phase 빠른 참조

```
build_phase     → 컴포넌트 생성, config_db get
connect_phase   → TLM 포트 연결
run_phase       → 메인 시뮬레이션 (task, objection)
check_phase     → 잔여 항목 확인
report_phase    → 최종 결과 보고
```

### 5.3 면접 골든 룰

1. **Phase 순서**: "build → connect → run → check — 순서 자동 보장이 핵심"
2. **Driver 역할**: "Pin-level 변환만 — DUT 로직 절대 넣지 않음"
3. **Factory**: "코드 수정 없이 컴포넌트 교체 — Override 의 힘"
4. **config_db**: "Config Object 패턴 — 포팅의 핵심"
5. **Coverage Cross**: "단일 변수 100% ≠ 조합 100% — Cross 가 버그를 찾음"
6. **Objection**: "Test 에서만 raise/drop — 단일 제어점"
7. **재사용**: "Agent = 프로토콜, Sequence = 시나리오, Config = 차이점 → 분리"

### 5.4 안티패턴 빠른 참조

```
✗ $display / $finish     → `uvm_info / `uvm_error / `uvm_fatal
✗ Driver 에 DUT 로직     → Scoreboard Reference Model
✗ Sequence 에 #delay     → 이벤트 / 핸드셰이크 기반
✗ 여러 곳에서 Objection  → Test 에서만
✗ config_db 경로 분산    → Config Object 로 묶기
✗ new() 로 직접 생성     → type_id::create() (Factory)
✗ super.build_phase 누락 → 모든 derived 의 첫 줄에 super.<phase>(phase)
```

### 5.5 run_phase 와 sub-phase 혼용 주의

!!! warning "실무 주의점 — run_phase 와 sub-phase 혼용"
    **현상**: `run_phase` 안에서 `raise_objection` 했는데 시뮬레이션이 즉시 종료되거나, sub-phase (`main_phase`, `shutdown_phase` 등) 시퀀스가 한 번도 안 도는 경우가 있다.

    **원인**: `run_phase` 와 `main_phase` / `pre_main_phase` / ... 같은 sub-phase 는 **같은 시간축에서 병렬 실행** 된다. `run_phase` 에서 objection 을 안 잡거나 sub-phase 에서 잡지 않으면 어느 한쪽이 먼저 끝나고 시뮬레이션이 종료. 또 `forever` 루프를 둘 다에 두면 종료 조건이 영원히 안 만족된다.

    **점검 포인트**: 한 컴포넌트에서 `run_phase` 와 sub-phase 를 동시에 사용하지 말 것. drain time 이 0 이면 마지막 transaction 이 잘릴 수 있으므로 `phase.phase_done.set_drain_time(this, 100ns)` 명시.

### 5.6 사내 자료 (이력서) 연결

| 항목 | 면접 질문 | 핵심 답변 |
|------|----------|----------|
| UVM (Advanced) | "UVM 수준은?" | From scratch 환경 × 5+ 프로젝트, 포팅, 재사용 설계 |
| From scratch | "환경을 어떻게 구축?" | 15 단계 체크리스트 + Config Object + Parameterized Agent |
| Legacy → UVM | "전환 동기?" | Passive → Active, 수동 force → Sequence, 재사용성 확보 |
| 포팅 (Apple/Meta) | "어떻게 빠르게?" | Config Object + Agent 재사용 + OTP 추상화 = 3-5일 |
| Custom Thin VIP | "VIP 설계 원칙?" | 핵심 경로만 + Bounded Queue + 선택적 기능 ON/OFF |
| Coverage-driven | "Closure 전략?" | Directed → Sweep → Random → Hole 분석 → Edge = 점진적 |

### 5.7 전체 학습 자료와의 연결

```
uvm = 모든 DV 자료의 "검증 방법론" 기반

  soc_secure_boot Unit 7: UVM 으로 BootROM 검증
  mmu Unit 6:             UVM 으로 MMU 검증
  toe Unit 4:             UVM 으로 TOE 검증
  ethernet_dcmac Unit 3:  UVM 으로 DCMAC 검증
  ufs_hci Unit 4:         UVM 으로 HCI 검증
  dram_ddr Unit 4:        UVM 으로 MC/MI 검증
  soc_integration_cctv:   UVM TB Top 환경

→ uvm 이 방법론, 나머지가 도메인별 적용
```

### 5.8 디버그 escalation 빠른 참조

| 증상 | 시작 레벨 | 보는 곳 |
|---|---|---|
| `UVM_FATAL build` 또는 connect | L1 (log) | build_phase 의 super 호출, config_db set/get 경로 |
| `UVM_ERROR run` 중간 | L2 (`/debug-log`) | UVM phase correlation, failing component ID |
| Scoreboard mismatch | L2 → L3 | expected_queue size, ID 매칭 |
| Timeout / hang | L3 (`/root-cause`) | objection count, fifo size, sub-phase 혼용 |
| Compile error | `/auto-fix` | 매크로 / class hierarchy / package import |

---

## 6. 흔한 오해 와 이 카드를 봐야 할 때

### 흔한 오해

!!! danger "❓ 오해 1 — 'UVM 을 다 외우면 마스터다'"
    **실제**: UVM 의 Class 만 200 개 + 매크로 100 개. 외울 게 아니라 **"문제 → 해당 패턴 매핑"** 의 신호 인지가 마스터의 핵심. 검색 능력 + 패턴 인지가 더 중요.<br>
    **왜 헷갈리는가**: 신입 시기에 "외워야 한다" 는 학습 패턴이 강해서. 실제로는 _컨텍스트 → 패턴_ 의 매핑이 본질.

!!! danger "❓ 오해 2 — '면접 골든 룰만 외우면 인터뷰 통과'"
    **실제**: 골든 룰은 _시작 신호_ 일 뿐. 면접관은 보통 _"왜 그렇게 됐는가"_ 를 묻고, 그 _왜_ 에 대한 깊이 (Module 01-06 의 design rationale) 가 답에 보여야 합니다. 룰은 _지표_, 깊이는 _자료_.<br>
    **왜 헷갈리는가**: 답안의 _길이_ 를 줄이려는 욕망 때문에 — 짧은 룰만 외우면 후속 질문에서 깨짐.

!!! danger "❓ 오해 3 — '안티패턴 빠른 참조만 보고 코드 리뷰 가능'"
    **실제**: 안티패턴 식별만 가능하고 _대체 패턴_ 을 즉시 떠올리지 못하면 리뷰가 _부정적인 지적_ 으로 끝납니다. 좋은 리뷰는 안티패턴 + _구체적인 리팩터링 제안_ 이 한 묶음. 그래서 Module 06 의 패턴 / 안티패턴이 짝지어 등장.<br>
    **왜 헷갈리는가**: 안티패턴 표가 _간결해서_ 그것만으로 충분해 보여서.

!!! danger "❓ 오해 4 — 'cheat sheet 만 보고 환경 구축 가능'"
    **실제**: 치트시트는 _기억을 빠르게 끄집어내는 도구_ 이지 _학습 도구_ 가 아닙니다. Module 01-06 의 _why_ 가 머릿속에 없으면 새 상황에서 _어느 패턴을 꺼낼지_ 결정 못 함. 치트시트는 _index_, 본문은 _content_.<br>
    **왜 헷갈리는가**: 표 형식이 _완결되어 보여서_.

### 이 카드를 봐야 할 때 (Trigger 매핑)

| 상황 | 이 카드의 어느 절 | 그 다음 |
|---|---|---|
| 면접에서 "UVM Phase 가 뭔가요?" | §5.2 Phase 빠른 참조 | M01 §3 의 worked example 한 사이클 설명 |
| 면접에서 "Driver 와 Monitor 차이?" | §5.3 면접 골든 룰 #2 | M02 §3 의 transaction flow |
| 코드 리뷰에서 `$display` 발견 | §5.4 안티패턴 #1 | M06 §5.8 의 GOOD 패턴 |
| 디버그 중 시뮬 hang | §5.8 디버그 escalation | M01 §6 의 디버그 체크리스트 + objection 검사 |
| 환경 from-scratch 시작 | §5.6 이력서 연결 + 15 단계 | M06 §5.10 |
| 새 SoC 포팅 | §5.6 의 "포팅 (Apple/Meta)" | M04 §5.4 OTP Abstraction Layer |
| Coverage closure 시작 | §4 의 Coverage 행 | M05 §5.9 closure 전략 |
| 멀티 sequencer 동기화 필요 | §3 의 #6, §4 의 Virtual Seq | M03 §5.2 Virtual Sequence 코드 |

---

## 7. 핵심 정리 (Key Takeaways)

- **외우지 말고 _찾을 수 있게_** — UVM 마스터의 본질은 _문제 → 패턴 매핑_ 의 신호 인지.
- **면접 7 골든 룰** + **6 안티패턴** + **15 단계 체크리스트** 가 코어 인덱스.
- **`type_id::create` + `if (!get(...)) uvm_fatal` + `super.<phase>(phase)`** 은 모든 코드의 _기본 습관_.
- **이 카드는 _index_, Module 01-06 이 _content_** — 치트시트만 보고 환경 구축 시도 금지.
- **트리거 매핑 (§6)** 으로 어느 상황에 어느 절을 보면 되는지 즉시 결정.

### 7.1 자가 점검

!!! question "🤔 Q1 — 카드 trigger 매핑 (Bloom: Apply)"
    "신규 agent 작성 직전". 카드의 어디부터?
    ??? success "정답"
        §5.1 Factory 등록 → §5.4 안티패턴:
        - **§5.1**: `type_id::create(...)` + `uvm_component_utils` 매크로 등록 → 누락 시 factory override 무력.
        - **§5.4**: Driver `item_done` 누락 / Monitor 가 `vif.sig <= ...` write / `new()` 직접 호출 등 검증 1차 reject 사유.
        - 본문 점프: Module 02 (Agent/Driver/Monitor).
        - 안티패턴: 카드 안 보고 작성 → review 에서 6 안티패턴 모두 hit.

!!! question "🤔 Q2 — 환경 구축 한계 (Bloom: Evaluate)"
    "카드만 보고 env 구축 시도" 가 _명백히_ 실패하는 이유?
    ??? success "정답"
        Cheatsheet 의 본질:
        - 카드는 _이미 아는 사람_ 의 _재인_ 용. _학습_ 용 아님.
        - **누락 항목**: phase 의 _순서 이유_, config_db hierarchy 의 _전파 메커니즘_, sequence/sequencer/driver 의 _handshake protocol_.
        - 카드의 한 줄 = 본문 1–2 페이지의 압축 → 본문 이해 없이는 한 줄에서 "무엇이 빠진지" 모름.
        - 결론: M01–M06 본문 학습 후 카드 = 강력한 도구. 그 전에는 _덫_.

### 7.2 출처

**Internal (Confluence)**
- `UVM Curriculum` — M01–M06 + 카드 매핑
- `Code Review Checklist` — 6 안티패턴 + 15 단계

**External**
- *UVM 1.2 User's Guide* — Accellera
- IEEE 1800.2-2020 *UVM Reference Manual*
- *UVM Cookbook* (Mentor)

!!! warning "코스 마무리"
    7 개 모듈을 마치셨습니다. 다음을 권장합니다:

    1. **퀴즈 풀어보기** — 챕터별 5-8 문항으로 이해 점검: [퀴즈 인덱스](quiz/index.md)
    2. **글로서리 스캔** — 모르는 용어 없는지: [용어집](glossary.md)
    3. **실전 적용** — 본인의 검증 환경에서 안티패턴 3 개 찾아 리팩터링 시도
    4. **다른 토픽** — UVM 은 도구. 실제 검증 대상에 적용하려면 [AMBA Protocols](../../amba_protocols/), [MMU](../../mmu/), [Formal Verification](../../formal_verification/) 등을 함께

---

## 다음 모듈

이 카드가 마지막입니다. → [퀴즈로 이동](quiz/index.md)

<div class="chapter-nav">
  <a class="nav-prev" href="../06_practical_patterns/">
    <div class="nav-label">◀ 이전</div>
    <div class="nav-title">UVM 실무 패턴 & 안티패턴</div>
  </a>
  <a class="nav-next" href="../quiz/">
    <div class="nav-label">다음 ▶</div>
    <div class="nav-title">퀴즈로 이동</div>
  </a>
</div>


--8<-- "abbreviations.md"
