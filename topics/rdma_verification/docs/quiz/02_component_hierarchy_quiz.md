# Module 02 퀴즈 — Component 계층

본문: [Module 02](../02_component_hierarchy.md)

---

### Q1. (Remember) `lib/base/component/` 의 7개 직속 디렉토리를 나열하시오.
**정답.** `config`, `custom_phase`, `env`, `model`, `pool`, `test`, `util`.
**Why.** Confluence Component 표 + 코드 검증. Module 02 §1.

### Q2. (Understand) `agent/` 안의 driver / handler / sequencer 분리의 의도를 한 줄로 설명하시오.
**정답.** driver = stateful(WQE 발행, outstanding 추적), handler = stateless forwarder(opcode 별 라우팅), sequencer = per-QP state owner. 책임을 분리해 시퀀스 재사용·flush 시 stale state 누적을 방지.
**Why.** Module 02 §3 + Module 05 #4 (Stateless 보존).

### Q3. (Apply) `E-SB-MATCH-0003` 에러를 보았다. 어느 파일을 먼저 열어야 하는가?
**정답.** `lib/base/component/env/data_env/vrdma_1side_compare.svh` (또는 2side/imm 의 같은 ID — 컨텍스트로 분리). prefix `E-SB-MATCH` → comparator(data_env).
**Why.** 컴포넌트 → 에러 prefix 매핑(Module 02 표).

### Q4. (Analyze) `pool/vrdma_qpool.svh` 와 `pool/vrdma_pool.svh` 의 관계를 추론하시오.
**정답.** `vrdma_pool` 이 통합 풀(QP/MR/PD/CQ/SQ/RQ), `vrdma_qpool` 은 QP 만 별도로 lifecycle 을 자세히 다룬다고 추론(파일 분리 패턴 + Confluence 설명). 정확한 관계는 코드에서 확인 필요.
**Why.** 추론(inference) 임을 명시 — 가정을 단정으로 쓰지 않는 anti-hallucination 훈련.

### Q5. (Evaluate) "handler 는 어차피 forwarder 니까 driver 안에 인라인하자" 는 제안을 평가하시오.
**정답.** 잘못됨. Stateless forwarder 분리는 (1) 새 op type 추가 시 새 handler 만 추가하면 됨(Open-Closed), (2) handler 별 AP 구독자가 다를 수 있음(DRY via AP), (3) driver 가 비대해지지 않음. 인라인 하면 4 원칙 중 3 개 위반.
**Why.** Module 05 와 cross-validate.

### Q6. (Apply) `F-CQHDL-TBERR-0003` 에러 ID prefix 만 보고 어느 파일에서 발생했는지 답하시오.
**정답.** `vrdma_cq_handler.svh` (`F-CQHDL` = `vrdma_cq_handler`). 정확히 line 244.
**Why.** Module 02 §컴포넌트→에러 prefix 매핑.

### Q7. (Apply) `vrdma_sequencer::wc_error_status[5][0]` 가 의미하는 바는?
**정답.** QP 5 번의 첫(시간순 첫) 에러 CQE 의 `wc_status`. Module 11 의 expected_error 검증 패턴에서 활용.
**Why.** sequencer 의 per-QP state 구조 이해.

### Q8. (Create) 새 검증 컴포넌트 `vrdma_latency_collector` 를 추가해 issue→complete latency 를 수집한다. 어느 디렉토리에 두는가? 어떤 AP 를 구독하는가?
**정답.** `lib/ext/component/perf/` 또는 `lib/base/component/env/data_env/` (옵션이면 ext, 공통이면 base). 구독 AP: `drv.issued_wqe_ap` (start), `drv.completed_wqe_ap` (end). 두 transaction id 매칭으로 latency 산출.
**Why.** Module 04 (AP) + Module 05 (DRY 원칙) 적용 점검.
