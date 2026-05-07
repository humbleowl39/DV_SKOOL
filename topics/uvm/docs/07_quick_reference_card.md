# Module 07 — Quick Reference Card

<div class="learning-meta">
  <span class="meta-badge meta-level-advanced">📊 Advanced</span>
</div>

!!! objective "사용 목적"
    이 페이지는 **참조용 치트시트**입니다. 정독 자료가 아니라 인터뷰/코드 리뷰/디버그 중에 빠르게 펴보는 용도. 새로 배우는 사람은 [Module 01-06](01_architecture_and_phase.md)부터 보고 마지막에 이 페이지로 정리.

    **할 수 있게 되는 것:**

    - **Recall** UVM 핵심 매크로/Phase/패턴 이름을 즉시 떠올림
    - **Reference** 면접/리뷰 중 한눈에 확인 (5-Whys 같은 골든 룰 포함)

!!! info "사전 지식"
    - [Module 01-06](01_architecture_and_phase.md) 학습 완료 후 이 카드를 보면 효과 극대화

## 한줄 요약
```
UVM = Factory(유연한 생성) + config_db(유연한 설정) + Phase(자동 순서) + TLM(컴포넌트 통신) 위에 Agent/Scoreboard/Coverage를 구축하는 재사용 가능한 검증 프레임워크.
```

---

!!! danger "❓ 흔한 오해"
    **오해**: UVM 을 다 외우면 마스터다

    **실제**: UVM 의 Class 만 200 개 + 매크로 100 개. 외울 게 아니라 "문제 → 해당 패턴 매핑" 의 신호 인지가 마스터의 핵심.

    **왜 헷갈리는가**: 신입 시기에 "외워야 한다" 는 학습 패턴이 강해서. 실제로는 검색 능력 + 패턴 인지가 더 중요.

!!! warning "실무 주의점 — run_phase 와 sub-phase 혼용"
    **현상**: `run_phase` 안에서 `raise_objection` 했는데 시뮬레이션이 즉시 종료되거나, sub-phase(`main_phase`, `shutdown_phase` 등) 시퀀스가 한 번도 안 도는 경우가 있다.

    **원인**: `run_phase` 와 `main_phase`/`pre_main_phase`/... 같은 sub-phase 는 **같은 시간축에서 병렬 실행**된다. `run_phase` 에서 objection 을 안 잡거나 sub-phase 에서 잡지 않으면 어느 한쪽이 먼저 끝나고 시뮬레이션이 종료. 또 `forever` 루프를 둘 다에 두면 종료 조건이 영원히 안 만족된다.

    **점검 포인트**: 한 컴포넌트에서 `run_phase` 와 sub-phase 를 동시에 사용하지 말 것. drain time 이 0 이면 마지막 transaction 이 잘릴 수 있으므로 `phase.phase_done.set_drain_time(this, 100ns)` 명시.

!!! tip "💡 이해를 위한 비유"
    **UVM 마스터 = 도구 인지** ≈ **공구함 — 어떤 도구를 언제 꺼낼지 아는 능력**

    UVM 의 가치는 "어떻게 쓰는지" 보다 "언제 어느 패턴을 꺼낼지" 의 직관. 이 cheat sheet 가 그 인덱스 역할.

---

## 핵심 정리

| 주제 | 핵심 포인트 |
|------|------------|
| 클래스 계층 | uvm_object(데이터) / uvm_component(인프라, Phase 있음) |
| Phase 순서 | build(Top→Down) → connect(Bot→Up) → run(병렬) → check/report |
| Agent | Driver + Monitor + Sequencer, Active/Passive |
| Driver | Transaction → Pin-level 변환만. DUT 로직 금지 |
| Monitor | Pin-level → Transaction 변환 + Analysis Port broadcast |
| Sequence | 시나리오 로직. start_item → randomize → finish_item |
| Virtual Seq | 멀티 Agent Sequence 조합 (시스템 시나리오) |
| config_db | set/get으로 설정 전달. Config Object 패턴 권장 |
| Factory | type_id::create + Override로 코드 수정 없이 교체 |
| TLM | Analysis Port (1:N broadcast), seq_item_port (Driver↔Sqr) |
| Scoreboard | Reference Model + 비교 + check_phase 잔여 확인 |
| Coverage | Covergroup + Coverpoint + Cross. Closure = 검증 완전성 |

---

## UVM 환경 구조 빠른 참조

```
uvm_test
  └── uvm_env
        ├── uvm_agent (Active)
        │     ├── uvm_driver      ← DUT에 자극
        │     ├── uvm_monitor     ← DUT 관찰 → AP
        │     └── uvm_sequencer   ← Sequence ↔ Driver 중개
        ├── uvm_agent (Passive)
        │     └── uvm_monitor     ← 출력 관찰 → AP
        ├── uvm_scoreboard        ← 기대값 vs 실제값 비교
        └── uvm_subscriber        ← Coverage 수집
```

## Factory 등록 빠른 참조

```systemverilog
// Component (name + parent)
`uvm_component_utils(my_class)
function new(string name, uvm_component parent);

// Object (name만)
`uvm_object_utils(my_class)
function new(string name = "my_class");

// 생성
my_class obj = my_class::type_id::create("name", parent);  // component
my_class obj = my_class::type_id::create("name");           // object
```

## Phase 빠른 참조

```
build_phase     → 컴포넌트 생성, config_db get
connect_phase   → TLM 포트 연결
run_phase       → 메인 시뮬레이션 (task, objection)
check_phase     → 잔여 항목 확인
report_phase    → 최종 결과 보고
```

---

## 면접 골든 룰

1. **Phase 순서**: "build→connect→run→check — 순서 자동 보장이 핵심"
2. **Driver 역할**: "Pin-level 변환만 — DUT 로직 절대 넣지 않음"
3. **Factory**: "코드 수정 없이 컴포넌트 교체 — Override의 힘"
4. **config_db**: "Config Object 패턴 — 포팅의 핵심"
5. **Coverage Cross**: "단일 변수 100% ≠ 조합 100% — Cross가 버그를 찾음"
6. **Objection**: "Test에서만 raise/drop — 단일 제어점"
7. **재사용**: "Agent=프로토콜, Sequence=시나리오, Config=차이점 → 분리"

---

## 안티패턴 빠른 참조

```
✗ $display/$finish     → `uvm_info/`uvm_error/`uvm_fatal
✗ Driver에 DUT 로직    → Scoreboard Reference Model
✗ Sequence에 #delay    → 이벤트/핸드셰이크 기반
✗ 여러 곳에서 Objection → Test에서만
✗ config_db 경로 분산   → Config Object로 묶기
✗ new()로 직접 생성     → type_id::create() (Factory)
```

---

## 이력서 연결

| 항목 | 면접 질문 | 핵심 답변 |
|------|----------|----------|
| UVM (Advanced) | "UVM 수준은?" | From scratch 환경 × 5+ 프로젝트, 포팅, 재사용 설계 |
| From scratch | "환경을 어떻게 구축?" | 15단계 체크리스트 + Config Object + Parameterized Agent |
| Legacy → UVM | "전환 동기?" | Passive→Active, 수동 force→Sequence, 재사용성 확보 |
| 포팅 (Apple/Meta) | "어떻게 빠르게?" | Config Object + Agent 재사용 + OTP 추상화 = 3-5일 |
| Custom Thin VIP | "VIP 설계 원칙?" | 핵심 경로만 + Bounded Queue + 선택적 기능 ON/OFF |
| Coverage-driven | "Closure 전략?" | Directed→Sweep→Random→Hole분석→Edge = 점진적 |

---

## 전체 학습 자료와의 연결

```
uvm_ko = 모든 DV 자료의 "검증 방법론" 기반

  soc_secure_boot_ko Unit 7: UVM으로 BootROM 검증
  mmu_ko Unit 6:             UVM으로 MMU 검증
  toe_ko Unit 4:             UVM으로 TOE 검증
  ethernet_dcmac_ko Unit 3:  UVM으로 DCMAC 검증
  ufs_hci_ko Unit 4:         UVM으로 HCI 검증
  dram_ddr_ko Unit 4:        UVM으로 MC/MI 검증
  soc_integration_cctv_ko:   UVM TB Top 환경

→ uvm_ko가 방법론, 나머지가 도메인별 적용
```

---

## 코스 마무리

7개 모듈을 마치셨습니다. 다음을 권장합니다:

1. **퀴즈 풀어보기** — 챕터별 5-8문항으로 이해 점검: [퀴즈 인덱스](quiz/index.md)
2. **글로서리 스캔** — 모르는 용어 없는지: [용어집](glossary.md)
3. **실전 적용** — 본인의 검증 환경에서 안티패턴 3개 찾아 리팩터링 시도
4. **다른 토픽** — UVM은 도구. 실제 검증 대상에 적용하려면 [AMBA Protocols](../../amba_protocols/), [MMU](../../mmu/), [Formal Verification](../../formal_verification/) 등을 함께

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
