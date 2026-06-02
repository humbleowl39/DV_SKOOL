---
title: "Module 06 퀴즈 — Error Handling Path"
---

본문: [Module 06](../../06_error_handling_path/)

---

### Q1. (Remember) 에러 처리 3-경로의 시작점을 나열하시오.
**정답.** (1) `RDMASQDestroy(.err(1))` driver 진입, (2) cq_handler 가 에러 CQE 수신, (3) 백그라운드 `monitorErrCQ` 의 ERR_CQ 폴링.
**Why.** 에러 처리 경로가 3개인 이유는 RDMA에서 에러가 발생하는 방식이 3가지이기 때문이다. 첫째는 TB가 능동적으로 QP를 에러 상태로 destroy할 때, 둘째는 DUT가 데이터 CQ에 에러 CQE를 올려서 `cq_handler`가 발견할 때, 셋째는 DUT의 ERR_CQ(별도 에러 전용 큐)에 에러가 쌓였을 때다. 3개 경로를 모르면 에러가 어떤 경로로 들어왔는지 파악하지 못해 디버깅 기점을 잡을 수 없다.

### Q2. (Understand) `cmd.expected_error` 와 `qp.isErrQP()` 와 static `err_enabled` 의 적용 범위 차이를 한 줄씩 설명하시오.
**정답.** `expected_error`: 단일 cmd / `isErrQP`: 단일 QP / `err_enabled`: 모든 QP, 한 컴포넌트.
**Why.** 세 게이트는 에러를 허용하는 범위가 다르다. `cmd.expected_error`는 가장 좁아서 특정 command 하나에만 적용되므로 의도된 에러 테스트에서 가장 정밀한 도구다. `isErrQP()`는 한 QP 전체에 적용되어 그 QP의 모든 이후 처리를 skip한다. `err_enabled`는 컴포넌트 전체(모든 QP)에 적용되므로 가장 광범위하다. 범위가 넓을수록 false-skip 위험이 커지므로, 가능한 한 좁은 게이트를 사용해야 검증 신뢰성이 보존된다.

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
**Why.** 4단계 각각이 필수적이다. (1) `expected_error=1`이 없으면 에러 CQE 수신 시 즉시 fatal이 된다. (2) `try_once(1)` 폴링으로 에러 CQE가 도착했는지 확인한다. (3) `err(1)` destroy로 모든 횡단 컴포넌트에게 "이 QP는 에러 처리됨"을 알려 flushQP를 트리거한다. (4) `clearErrorStatus`로 sequencer의 에러 이력을 정리해 다음 테스트가 오염되지 않도록 한다. 이 4단계 중 하나라도 빠지면 시뮬이 실패하거나 잔류 state가 남는다.

### Q4. (Analyze) `RDMAQPDestroy(.err(1))` 한 번에 `vrdma_1side_compare`, `vrdma_2side_compare`, `vrdma_imm_compare`, `vrdma_c2h_tracker` 가 모두 정리되는 메커니즘은?
**정답.** driver 가 `setErrState(1)` 호출 → 모든 횡단 컴포넌트가 `qp_reg_ap` 또는 자체 deregister hook 으로 ErrQP 인지 → comparator 는 `flushQP` 호출, c2h_tracker 는 `is_err_qp_registered = 1` 설정.
**Why.** `RDMAQPDestroy(.err(1))` 한 호출이 4개 컴포넌트를 동시에 정리하는 것은 AP 기반 event-driven 설계 덕분이다. driver가 `setErrState(1)`을 호출하고 `qp_reg_ap`로 broadcast하면, 이를 구독하는 모든 횡단 컴포넌트가 동시에 ErrQP 사실을 인지하고 각자의 cleanup 로직을 실행한다. 이 one-to-many 연쇄 정리가 가능한 이유가 Module 04의 AP 토폴로지를 설계한 이유이기도 하다.

### Q5. (Evaluate) "에러 테스트는 그냥 `enable_error_cq_poll = 0` 으로 끄면 다 해결된다" 를 평가하시오.
**정답.** 잘못됨. `enable_error_cq_poll` 은 ERR_CQ 백그라운드 폴링만 끔. 데이터 CQ 에서 발견되는 에러 CQE (`F-CQHDL-TBERR-0003` 경로 A)는 그대로 fatal. per-cmd `expected_error` 가 정확한 도구.
**Why.** `enable_error_cq_poll = 0`은 경로 3(ERR_CQ 백그라운드 폴링)만 비활성화한다. 에러 CQE가 데이터 CQ에 올라오는 경로 2(`cq_handler`에서 발견되는 `F-CQHDL-TBERR-0003`)는 별개 메커니즘으로, `enable_error_cq_poll`과 무관하다. "flag 하나로 모든 에러를 막을 수 있다"는 생각은 3경로 구조를 이해하지 못한 데서 비롯된다. 각 경로마다 적합한 게이트 도구가 다름을 알아야 한다.

### Q6. (Apply) `vrdma_2side_compare::err_enabled = 1` 로 설정하면 어떤 일이 일어나는가? 정상 QP 에는 영향이 있는가?
**정답.** 모든 QP 가 deregister 될 때 (정상이든 에러든) `flushQP` 호출. 정상 QP 에도 영향 — pending send/recv tracker 가 flush 됨. 에러 시나리오에 광범위하게 쓸 때만 사용해야 함(false-skip 위험).
**Why.** `err_enabled`는 static 플래그이므로 컴포넌트의 모든 QP에 동일하게 적용된다. 정상 검증 중인 QP가 deregister될 때도 pending 데이터가 flush되어 버리면, 실제로 비교해야 할 데이터를 검사하지 않고 넘어가는 false-skip이 발생한다. 이것은 DUT 버그를 놓칠 수 있는 검증 약화다. 따라서 `err_enabled`는 "모든 QP에 에러가 예상되는 넓은 에러 스트레스 테스트"에만 사용하고, 일반 테스트에서는 per-cmd나 per-QP 게이트를 사용해야 한다.

### Q7. (Analyze) ErrQP 의 WQE 가 `completed_wqe_ap` 로 전달되지 않는데(`vrdma_driver.svh:1327`), 그러면 scoreboard 의 outstanding 카운터는 어떻게 정리되는가?
**정답.** comparator/tracker 가 `flushQP` 로 자체 큐를 비움. `completeOutstanding(cmd)` 자체는 호출되지만 AP write 만 게이트 — outstanding 정리는 driver 자체에서 수행. scoreboard 는 flush 시점에 expected/actual 모두 0 으로 동기화.
**Why.** "AP에 write되지 않으면 scoreboard의 카운터는 어떻게 되나?"는 중요한 질문이다. 답은 두 레벨에서 정리가 이루어진다는 것이다: driver가 내부적으로 `completeOutstanding`을 호출해 자신의 outstanding 큐를 정리하고, comparator/tracker는 `flushQP` 호출로 자신의 expected 큐를 비운다. AP write 게이트는 "scoreboard에게 비교 요청을 보내지 않는" 것이지, outstanding 자체를 무시하는 게 아니다.

### Q8. (Create) 한 테스트에서 노드 0 에서만 의도된 에러를 발생시키고, 노드 1 은 정상 검증을 유지하고 싶다. 어떤 게이트를 어떻게 사용하는가?
**정답.** static `err_enabled` 는 사용 금지(모든 QP 에 영향). 대신:
- 노드 0 의 에러 verb 에만 `cmd.expected_error = 1`
- 노드 0 의 해당 QP 만 `RDMAQPDestroy(.err(1))` (per-QP `isErrQP` gate)
- 노드 1 은 손대지 않음 — comparator/tracker 가 정상 검증 지속
**Why.** `err_enabled`를 켜면 노드 1의 정상 QP 검증도 비활성화되어 버린다. 멀티노드 테스트에서 한 노드만 에러를 의도하는 경우, 노드 격리가 의미를 갖는 것은 이 게이트 선택의 차이에서 드러난다. per-cmd `expected_error`로 특정 verb만, per-QP `RDMAQPDestroy(.err(1))`로 특정 QP만 에러 처리해야 노드 1의 comparator가 여전히 정상 데이터를 검증할 수 있다. 이 구분이 Module 01의 노드 격리 설계가 가져다주는 실질적 이점이다.
