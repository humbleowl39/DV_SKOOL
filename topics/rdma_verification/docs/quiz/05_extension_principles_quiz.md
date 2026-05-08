# Module 05 퀴즈 — Adding New Components 4원칙

본문: [Module 05](../05_extension_principles.md)

---

### Q1. (Remember) 4 원칙의 이름을 나열하시오.
**정답.** Open-Closed / Interface Stability / DRY via Analysis Port Reuse / Stateless 보존.
**Why.** Confluence + Module 05.

### Q2. (Understand) "Interface Stability" 원칙에서 금지되는 단 하나의 변경은?
**정답.** 기존 port 시그니처(parameter 타입) 변경. 모든 연결 컴포넌트 수정 필요.
**Why.** Module 05 표.

### Q3. (Apply) 새 정보를 컴포넌트 간에 전달해야 한다. 권장 순서로 답하시오 (1순위→3순위).
**정답.** 1순위: 기존 transaction object(`vrdma_base_command`)에 필드 추가 / 2순위: 새 transaction class 정의 / 3순위: 새 analysis port 추가. (port 시그니처 변경은 항상 금지)
**Why.** Module 05 #2 표 — 영향 범위 최소화 순.

### Q4. (Analyze) `vrdma_top_sequence` 에 outstanding 카운터를 두면 어떤 4가지 문제가 발생하는가?
**정답.** (1) 시퀀스 재사용 시 stale state, (2) 멀티노드 cross-talk, (3) flush 누락, (4) state ownership 모호. Module 05 #4 의 4 이유와 정확히 대응 — 정답은 sequencer 에 두는 것.
**Why.** Stateless 보존 원칙의 핵심 사례.

### Q5. (Evaluate) 새 컴포넌트가 추가되었는데 기존 cfg 의 한 필드가 새 컴포넌트 enable 여부를 제어한다. 4 원칙 중 어떤 것을 위반할 수 있는가?
**정답.** 잠재적으로 Open-Closed — 기존 컴포넌트의 build_phase / connect_phase 가 그 cfg 를 분기로 사용한다면 위반. 새 컴포넌트가 자체 cfg subscription 으로 enable/disable 결정해야 안전.
**Why.** "기존 컴포넌트 수정 없이 추가 가능한가?" 체크리스트 항목.

### Q6. (Apply) 체크리스트 6 항목 중 가장 강력한 검증은?
**정답.** "새 컴포넌트를 제거해도 기존 TB 가 정상 동작하는가? (opt-in 구조)". 다른 5 항목을 모두 통과해도 이게 깨지면 의존이 새겼다는 증거.
**Why.** Module 05 체크리스트.

### Q7. (Analyze) Congestion Control(`lib/ext/component/congestion_control/ccmad/`) 추가가 4 원칙을 어떻게 지키는지 분석하시오.
**정답.** Opt-in (`lib/ext/`) → Open-Closed. AP 구독 → DRY. Stateless `*_handler` 는 손대지 않음 → Stateless 보존. driver port 시그니처 불변 → Interface Stability. 완벽한 4원칙 적용.
**Why.** Module 05 케이스 스터디.

### Q8. (Create) 다음 요구사항을 4원칙에 맞게 설계하시오: "각 QP 의 처음 100 개 WQE 의 latency 분포를 수집하고 싶다."
**정답.**
- 위치: `lib/ext/component/perf/vrdma_latency_collector.svh` (opt-in)
- 구독 AP: `drv.issued_wqe_ap` (start ts) + `drv.completed_wqe_ap` (end ts), `drv.qp_reg_ap` (per-QP 분리)
- State: 자체 `latency_histogram[qp_num][$]` (새 컴포넌트가 자체 state 관리 — sequencer/handler 건드리지 않음)
- 제거 가능성: `cfg.has_perf_collector` 로 enable/disable
- driver/handler/sequencer/scoreboard 코드 수정 0
**Why.** 모든 4원칙 동시 적용 + 체크리스트 6항목 통과.
