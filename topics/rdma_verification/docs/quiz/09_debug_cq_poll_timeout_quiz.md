# Module 09 퀴즈 — CQ Poll Timeout

본문: [Module 09](../09_debug_cq_poll_timeout.md)

---

### Q1. (Remember) 타임아웃 발동 두 조건을 답하시오.
**정답.** `try_cnt > timeout_count` AND `!c2h_tracker::active`. 둘 다 충족해야 발동.
**Why.** `vrdma_driver.svh:1484` exceptionTimeout 흐름.

### Q2. (Understand) 타임아웃 시 fatal 이 아니라 `uvm_shutdown_phase` 로 점프하는 이유는?
**정답.** Graceful 종료 시 outstanding 진단 정보(unprocessed wqe, PA queues 등)가 보존되어 디버깅 가능. fatal 이면 즉시 종료 → 진단 손실.
**Why.** Module 09 §대표 에러 메시지 + 동작.

### Q3. (Apply) 타임아웃 직전 `unprocessed wqe = 0` 인데도 timeout 이 발생했다. 의미는?
**정답.** 카운팅 오류 — `signaled` 비트 또는 `sq_sig_type` 설정으로 unsignaled WQE 가 폴링 대상에 포함되었거나 제외됨. CQ 가 expected entry 를 안 보고 있음.
**Why.** Module 09 §흔한 원인 표.

### Q4. (Analyze) c2h_tracker 가 active 인 동안 timeout 이 무한 지연된다. 이는 디버깅에 어떤 의미가 있나? (긍정 / 부정 모두)
**정답.**
- 긍정: DUT DMA 가 살아있다는 신호 — 어떤 작업은 진행 중.
- 부정: timeout 진단을 가린다 — 다른 문제(예: phase bit 동기화)는 timeout 으로 발견되지 않음.
**Why.** Module 09 §타임아웃 두 조건 핵심.

### Q5. (Apply) QID 14–17 fetch 가 0 회. 첫 가설과 다음 액션은?
**정답.** DUT 가 SQ doorbell 인식 실패. 다음: BAR4 의 SQ_DB 레지스터 쓰기 추적 → RAL config 가 정확한지 → DUT BAR decoding fsdb 추적.
**Why.** Module 09 §빠른 트리아지 1행.

### Q6. (Analyze) QID 14–17 OK, QID 8 OK, packet 송신 OK, 그러나 QID 10/11 (CQE write) 가 없다. 무엇을 의미?
**정답.** DUT 가 work 를 끝까지 처리했지만 completion engine 이 CQE 를 만들지 못함. completion FSM 버그 또는 CQ base addr 가 DUT 에 잘못 등록됨.
**Why.** Module 09 §빠른 트리아지 3행.

### Q7. (Evaluate) "timeout_count 를 100000 으로 늘리면 모든 timeout 이 사라진다" 를 평가하시오.
**정답.** 잘못됨. timeout 의 근본 원인은 DUT 가 work 를 처리하지 못하거나 CQE 가 도착하지 않는 것. 시간 늘려봐야 결과는 같음(또는 c2h_tracker active 가 끝나지 않으면 무한 대기). 진짜 해결은 root cause 추적.
**Why.** RDMA-TB 의 디버그 철학(Root cause first).

### Q8. (Create) 새 테스트가 한 시뮬에서 RDMA verb 5000 개 발행. CQ poll 이 4900 개에서 timeout. 가설 3개를 작성하고 각각의 검증 명령을 답하시오.
**정답.**
- 가설 1 — DUT 가 4900 개 후 stall (예: 큐 overflow). 검증: DUT 의 SQ pointer 시간 그래프 fsdb.
- 가설 2 — `unprocessed_cqe_cnt` 누적 오류. 검증: 각 cqe 의 signaled 필드 누적 vs expected.
- 가설 3 — Phase bit 토글이 wrap-around 시점에서 누락. 검증: 폴링 주기 로그에서 PHASE 값 추적, CQ depth 와 wrap 시점 비교.
**Why.** Module 09 §흔한 원인 매트릭스의 multiple-cause 분석.
