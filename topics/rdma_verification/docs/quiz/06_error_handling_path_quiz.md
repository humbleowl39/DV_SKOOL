# Module 06 퀴즈 — Error Handling Path

본문: [Module 06](../06_error_handling_path.md)

---

### Q1. (Remember) 에러 처리 3-경로의 시작점을 나열하시오.
**정답.** (1) `RDMASQDestroy(.err(1))` driver 진입, (2) cq_handler 가 에러 CQE 수신, (3) 백그라운드 `monitorErrCQ` 의 ERR_CQ 폴링.
**Why.** Module 06 §1-4.

### Q2. (Understand) `cmd.expected_error` 와 `qp.isErrQP()` 와 static `err_enabled` 의 적용 범위 차이를 한 줄씩 설명하시오.
**정답.** `expected_error`: 단일 cmd / `isErrQP`: 단일 QP / `err_enabled`: 모든 QP, 한 컴포넌트.
**Why.** Module 06 §적용 범위 비교 표.

### Q3. (Apply) 의도된 RAE(Remote Access Error) 시나리오를 작성하라 — 핵심 4 라인.
**정답.**
```systemverilog
read_cmd.expected_error = 1;          // 1) per-cmd gate
this.start_item(read_cmd, .sequencer(t_seqr));
assert(read_cmd.randomize() with { rkey == bad_key; });
this.finish_item(read_cmd);
this.RDMACQPoll(.t_seqr(seqr), .cq_num(cq), .try_once(1));  // 2) 단발 폴링
this.RDMAQPDestroy(.t_seqr(seqr), .qp_num(qp), .err(1));    // 3) flushQP
t_seqr.clearErrorStatus(qp_num);                            // 4) cleanup
```
**Why.** Module 06 §에러 테스트 패턴.

### Q4. (Analyze) `RDMAQPDestroy(.err(1))` 한 번에 `vrdma_1side_compare`, `vrdma_2side_compare`, `vrdma_imm_compare`, `vrdma_c2h_tracker` 가 모두 정리되는 메커니즘은?
**정답.** driver 가 `setErrState(1)` 호출 → 모든 횡단 컴포넌트가 `qp_reg_ap` 또는 자체 deregister hook 으로 ErrQP 인지 → comparator 는 `flushQP` 호출, c2h_tracker 는 `is_err_qp_registered = 1` 설정.
**Why.** Module 06 §컴포넌트별 동작.

### Q5. (Evaluate) "에러 테스트는 그냥 `enable_error_cq_poll = 0` 으로 끄면 다 해결된다" 를 평가하시오.
**정답.** 잘못됨. `enable_error_cq_poll` 은 ERR_CQ 백그라운드 폴링만 끔. 데이터 CQ 에서 발견되는 에러 CQE (`F-CQHDL-TBERR-0003` 경로 A)는 그대로 fatal. per-cmd `expected_error` 가 정확한 도구.
**Why.** Module 06 §경로 분리.

### Q6. (Apply) `vrdma_2side_compare::err_enabled = 1` 로 설정하면 어떤 일이 일어나는가? 정상 QP 에는 영향이 있는가?
**정답.** 모든 QP 가 deregister 될 때 (정상이든 에러든) `flushQP` 호출. 정상 QP 에도 영향 — pending send/recv tracker 가 flush 됨. 에러 시나리오에 광범위하게 쓸 때만 사용해야 함(false-skip 위험).
**Why.** static flag 의 적용 범위.

### Q7. (Analyze) ErrQP 의 WQE 가 `completed_wqe_ap` 로 전달되지 않는데(`vrdma_driver.svh:1327`), 그러면 scoreboard 의 outstanding 카운터는 어떻게 정리되는가?
**정답.** comparator/tracker 가 `flushQP` 로 자체 큐를 비움. `completeOutstanding(cmd)` 자체는 호출되지만 AP write 만 게이트 — outstanding 정리는 driver 자체에서 수행. scoreboard 는 flush 시점에 expected/actual 모두 0 으로 동기화.
**Why.** Driver 와 횡단 컴포넌트의 분리된 정리 책임.

### Q8. (Create) 한 테스트에서 노드 0 에서만 의도된 에러를 발생시키고, 노드 1 은 정상 검증을 유지하고 싶다. 어떤 게이트를 어떻게 사용하는가?
**정답.** static `err_enabled` 는 사용 금지(모든 QP 에 영향). 대신:
- 노드 0 의 에러 verb 에만 `cmd.expected_error = 1`
- 노드 0 의 해당 QP 만 `RDMAQPDestroy(.err(1))` (per-QP `isErrQP` gate)
- 노드 1 은 손대지 않음 — comparator/tracker 가 정상 검증 지속
**Why.** Per-cmd / per-QP gate 의 정확한 적용.
