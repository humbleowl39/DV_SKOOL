---
title: "Module 05 퀴즈 — Adding New Components 4원칙"
---

본문: [Module 05](../../05_extension_principles/)

---

### Q1. (Remember) 4 원칙의 이름을 나열하시오.
**정답.** Open-Closed / Interface Stability / DRY via Analysis Port Reuse / Stateless 보존.
**Why.** 이 4원칙은 "기존 코드를 건드리지 않고 새 기능을 추가할 수 있는가?"라는 질문을 각 측면에서 검사하는 체크리스트다. Open-Closed는 기존 컴포넌트를 수정하지 않아야 한다는 원칙, Interface Stability는 기존 port 시그니처를 변경하지 않아야 한다는 원칙, DRY는 기존 AP 구독으로 정보를 얻어야 한다는 원칙, Stateless는 sequence에 state를 두지 말아야 한다는 원칙이다. 네 이름을 순서대로 기억하는 것이 체크리스트 활용의 출발점이다.

### Q2. (Understand) "Interface Stability" 원칙에서 금지되는 단 하나의 변경은?
**정답.** 기존 port 시그니처(parameter 타입) 변경. 모든 연결 컴포넌트 수정 필요.
**Why.** port 시그니처를 변경하면 그 port에 연결된 모든 analysis_export/analysis_imp를 찾아서 타입을 맞춰야 한다. 이는 연쇄 수정을 유발해 수십 개 파일을 동시에 고쳐야 하는 상황으로 이어질 수 있다. 반면 port를 추가하거나 새 transaction 필드를 추가하는 것은 기존 연결에 영향을 주지 않으므로 허용된다. "변경해도 되는 것(추가)"과 "절대 안 되는 것(시그니처 수정)"을 명확히 구분하는 것이 Interface Stability의 핵심이다.

### Q3. (Apply) 새 정보를 컴포넌트 간에 전달해야 한다. 권장 순서로 답하시오 (1순위→3순위).
**정답.** 1순위: 기존 transaction object(`vrdma_base_command`)에 필드 추가 / 2순위: 새 transaction class 정의 / 3순위: 새 analysis port 추가. (port 시그니처 변경은 항상 금지)
**Why.** 기존 transaction에 필드를 추가하는 것은 기존 구독자들이 그 필드를 무시하면 되므로 영향 범위가 가장 좁다. 새 transaction class를 만들면 새 AP가 필요할 수도 있지만, 기존 AP와 기존 구독자는 건드리지 않아도 된다. 새 AP를 추가하는 것은 connect_phase에서 새 연결을 설정해야 하므로 일부 기존 파일 수정이 불가피하다. 항상 "가장 적은 코드를 바꾸는 방법"부터 시도하는 것이 Interface Stability의 실천이다.

### Q4. (Analyze) `vrdma_top_sequence` 에 outstanding 카운터를 두면 어떤 4가지 문제가 발생하는가?
**정답.** (1) 시퀀스 재사용 시 stale state, (2) 멀티노드 cross-talk, (3) flush 누락, (4) state ownership 모호. Module 05 #4 의 4 이유와 정확히 대응 — 정답은 sequencer 에 두는 것.
**Why.** sequence 오브젝트는 create→start→finish 후 destroy되거나 재사용될 수 있어, 카운터가 이전 실행의 값을 그대로 들고 있으면 다음 테스트가 오염된다(stale state). 멀티노드 환경에서 하나의 시퀀스 인스턴스를 두 노드가 동시에 실행하면 두 노드의 카운터가 같은 변수를 공유해 cross-talk가 발생한다. flush가 필요한 시점(ErrQP 선언, 시뮬 종료 등)에 sequence 단계에서는 그 시점을 알 수 없어 cleanup이 불가능하다. `vrdma_sequencer`는 노드별로 하나씩 존재하고 lifetime이 시뮬 전체이므로 이 모든 문제를 피할 수 있다.

### Q5. (Evaluate) 새 컴포넌트가 추가되었는데 기존 cfg 의 한 필드가 새 컴포넌트 enable 여부를 제어한다. 4 원칙 중 어떤 것을 위반할 수 있는가?
**정답.** 잠재적으로 Open-Closed — 기존 컴포넌트의 build_phase / connect_phase 가 그 cfg 를 분기로 사용한다면 위반. 새 컴포넌트가 자체 cfg subscription 으로 enable/disable 결정해야 안전.
**Why.** 기존 cfg에 필드를 추가하는 것 자체는 Interface Stability 관점에서는 허용될 수 있다. 그러나 기존 컴포넌트(예: `vrdmatb_top_env`)의 `build_phase`에서 새 필드를 보고 분기하는 코드가 추가된다면, 기존 컴포넌트가 수정된 것이므로 Open-Closed 위반이다. 새 컴포넌트가 `uvm_config_db`를 통해 자체적으로 enable 여부를 결정하도록 설계하면, 기존 컴포넌트를 전혀 건드리지 않아도 된다.

### Q6. (Apply) 체크리스트 6 항목 중 가장 강력한 검증은?
**정답.** "새 컴포넌트를 제거해도 기존 TB 가 정상 동작하는가? (opt-in 구조)". 다른 5 항목을 모두 통과해도 이게 깨지면 의존이 새겼다는 증거.
**Why.** 나머지 5가지 체크 항목이 설계 의도를 검사한다면, 이 마지막 항목은 실제 구현이 의도대로 동작하는지 검증하는 smoke test다. 새 컴포넌트를 `lib/ext`에 두고 opt-in으로 설계했다고 해도, 실수로 `lib/base`의 connect_phase에 포인터 참조가 남아 있으면 새 컴포넌트 없이는 null 접근이 발생한다. 이 테스트를 통과해야만 "진짜 opt-in"이라고 확신할 수 있다.

### Q7. (Analyze) Congestion Control(`lib/ext/component/congestion_control/ccmad/`) 추가가 4 원칙을 어떻게 지키는지 분석하시오.
**정답.** Opt-in (`lib/ext/`) → Open-Closed. AP 구독 → DRY. Stateless `*_handler` 는 손대지 않음 → Stateless 보존. driver port 시그니처 불변 → Interface Stability. 완벽한 4원칙 적용.
**Why.** Congestion Control 모듈은 4원칙을 동시에 만족하는 교과서적 사례다. `lib/ext`에 배치함으로써 기존 `lib/base` 코드를 한 줄도 수정하지 않았고(Open-Closed), `drv.issued_wqe_ap`와 `completed_wqe_ap` 구독으로 RTT/BW를 측정해 정보를 중복 수집하지 않았다(DRY). 기존 handler의 stateless 특성을 유지하면서 CC 전용 scoreboard를 별도로 만들었고(Stateless 보존), driver AP 시그니처를 변경하지 않았다(Interface Stability). 새 컴포넌트 추가 시 이 사례를 레퍼런스로 삼아야 한다.

### Q8. (Create) 다음 요구사항을 4원칙에 맞게 설계하시오: "각 QP 의 처음 100 개 WQE 의 latency 분포를 수집하고 싶다."
**정답.**
- 위치: `lib/ext/component/perf/vrdma_latency_collector.svh` (opt-in)
- 구독 AP: `drv.issued_wqe_ap` (start ts) + `drv.completed_wqe_ap` (end ts), `drv.qp_reg_ap` (per-QP 분리)
- State: 자체 `latency_histogram[qp_num][$]` (새 컴포넌트가 자체 state 관리 — sequencer/handler 건드리지 않음)
- 제거 가능성: `cfg.has_perf_collector` 로 enable/disable
- driver/handler/sequencer/scoreboard 코드 수정 0
**Why.** 4원칙을 동시에 만족하는 설계다. `lib/ext` 배치와 `cfg.has_perf_collector` 플래그로 기존 TB를 수정하지 않고 opt-in을 구현했다(Open-Closed). AP 구독만으로 타임스탬프를 얻어 중복 계측 로직을 피했다(DRY). latency 히스토그램을 새 컴포넌트 내부에만 두어 기존 sequencer나 handler의 state를 오염시키지 않았다(Stateless 보존). 기존 driver AP 시그니처는 그대로다(Interface Stability). 6항목 체크리스트에서 "컴포넌트를 제거해도 기존 TB 정상 동작"도 통과한다.
