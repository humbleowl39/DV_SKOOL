---
title: "Module 11 퀴즈 — Unexpected Error CQE"
---

본문: [Module 11](../../11_debug_unexpected_err_cqe/)

---

### Q1. (Remember) 정상 시뮬에서 발생 가능한 에러 CQE 두 가지를 답하시오.
**정답.** `WC_RETRY_EXC_ERR` (12), `WC_RNR_RETRY_EXC_ERR` (13). 둘 다 HW 리소스 부족.
**Why.** 이 두 에러만이 "의도하지 않은" 에러가 아닐 수 있는 이유가 있다. `WC_RETRY_EXC_ERR`(12)는 ACK timeout 재시도 횟수 초과, `WC_RNR_RETRY_EXC_ERR`(13)는 수신자 버퍼 부족으로 인한 RNR NAK 재시도 초과인데, 둘 다 DUT 로직 버그가 아닌 HW 리소스 부족(타임아웃 설정 또는 RQ 버퍼 부족)에서 비롯된다. 나머지 모든 wc_status 값은 DUT 로직 버그를 의미하므로, 이 두 값을 구별해 아는 것이 에러 분류의 출발점이다.

### Q2. (Understand) `WC_WR_FLUSH_ERR` (5) 가 보였을 때 어디부터 디버깅?
**정답.** 이 에러는 항상 2차 영향 — flush 직전의 선행 에러부터 디버깅. 시간 거꾸로 가서 첫 에러 CQE 를 찾는다.
**Why.** `WC_WR_FLUSH_ERR`(5)는 QP가 에러 상태로 전이된 후 아직 처리되지 않은 WQE들이 강제 flush되면서 발생하는 secondary 에러다. flush 자체가 문제가 아니라 flush를 유발한 선행 에러가 근본 원인이다. 따라서 로그에서 시간을 거꾸로 올라가 `WC_WR_FLUSH_ERR` 이전에 어떤 에러 CQE가 먼저 도착했는지 찾아야 한다. 이 에러만 보고 DUT 데이터 경로를 의심하면 방향이 틀린 것이다.

### Q3. (Apply) `F-CQHDL-TBERR-0003` 발생 + `wc_status = 12 (WC_RETRY_EXC_ERR)`. 첫 액션은?
**정답.** RETRY 계열이므로 DUT 버그가 아닌 HW 성능 한계 의심. 트래픽 부하(동시 outstanding WQE 수, MTU 대비 burst), retry 설정(`timeout`, `retry_cnt`) 조절.
**Why.** `WC_RETRY_EXC_ERR`(12)는 재시도 횟수를 모두 소진했다는 의미다. 이는 DUT 로직 자체가 잘못된 것이 아니라, ACK가 timeout 안에 도착하지 않아서 재시도를 반복하다 한계에 도달한 것이다. 먼저 테스트의 트래픽 부하가 DUT 처리 용량 대비 너무 크지 않은지, `retry_cnt`와 `timeout` 설정이 시뮬 시간에 적합한지 확인해야 한다. DUT 코드를 먼저 들여다보는 것은 순서가 잘못된 접근이다.

### Q4. (Apply) `F-CQHDL-TBERR-0003` 발생 + `wc_status = 4 (WC_LOC_PROT_ERR)`. 어떤 단계로 디버깅?
**정답.**
1. TB 가 발행한 WQE 의 lkey 확인 — 잘못된 lkey 가 발행되었나?
2. lkey 가 정상이면 DUT 의 lkey 검증 로직 의심 — DUT 가 정상 lkey 를 reject.
**Why.** `WC_LOC_PROT_ERR`(4)는 local protection error로, lkey가 잘못되었거나 DUT가 lkey 검증에서 실패했다는 의미다. 진단 순서가 중요하다: TB가 의도적으로 bad_lkey를 발행한 것인지 먼저 확인해야 한다(Step 1이 TB 버그 배제). lkey가 정상임에도 DUT가 에러를 발생시켰다면, DUT의 lkey 검증 로직에 버그가 있는 것이다(Step 2가 DUT 버그 판정). TB 설정을 배제하지 않고 DUT 버그라 단정하면 근본 원인을 놓칠 수 있다.

### Q5. (Analyze) 에러 CQE 가 도착하면 TB state 5 가지가 자동 변화한다. 나열하시오.
**정답.**
1. QP `setErrState(1)` (이후 verb skip)
2. Outstanding WQE 전체 flush (`completeOutstanding`)
3. CQ polling 루프 즉시 종료 (`cmd.error_occured = 1`)
4. Scoreboard 차단 (에러 CQE 는 `cqe_ap` 로 안 감)
5. Sequencer 의 `wc_error_status[qp]`, `debug_wc_flag[qp]` 에 기록
**Why.** 5가지 state 변화가 자동으로 일어나는 이유는, 에러 CQE 수신이 단순한 결과 통보가 아니라 QP를 "에러 복구 필요" 상태로 전이시키는 사건이기 때문이다. `setErrState(1)`은 이후 모든 verb를 skip해 추가 피해를 막고, outstanding flush는 비교기가 이미 실패한 WQE를 기다리지 않도록 한다. `wc_error_status` 기록은 의도된 에러 테스트에서 예상한 에러가 맞는지 검증하는 증거를 남긴다. 이 5단계를 모르면 에러 복구 시나리오를 올바르게 작성할 수 없다.

### Q6. (Evaluate) "DUT 가 rkey 검증을 안 한다" 라는 결론을 내리려면 어떤 증거가 필요한가?
**정답.**
- TB 가 정상 rkey 로 read 발행했는데 `WC_REM_ACCESS_ERR` (10) 도착 (false positive 가능 — DUT bug)
- TB 가 잘못된 rkey 로 read 발행했는데 success CQE 도착 (false negative — 검증 누락)
- 둘 다 + DUT 의 rkey 검증 로직 fsdb trace
**Why.** "rkey 검증을 안 한다"는 결론은 단방향 증거로는 충분하지 않다. false positive(정상 rkey인데 에러)만 있다면 DUT가 rkey 검증을 과도하게 하는 버그일 수 있고, false negative(bad rkey인데 성공)만 있다면 rkey 검증 자체가 없는 버그다. 두 방향 모두를 테스트해야 "rkey 검증 로직"의 동작을 완전히 특정할 수 있으며, 최종 확인은 fsdb에서 rkey 검증 로직의 실제 동작을 추적해야 한다.

### Q7. (Apply) 의도된 RAE 시나리오에서 `expected_error=1` 을 안 걸면 무엇이 일어나는가?
**정답.** `F-CQHDL-TBERR-0003` (FATAL) 발생 → 시뮬 즉시 종료. `cmd.expected_error == 0` 조건이 충족되어 unexpected 로 처리.
**Why.** `cq_handler`는 에러 CQE를 수신했을 때 `cmd.expected_error` 플래그를 체크한다. `expected_error=0`(기본값)이면 "이 에러는 예상하지 않았다"는 의미이므로 즉시 fatal을 발생시킨다. 의도된 RAE(Remote Access Error) 시나리오는 "에러가 발생해야 PASS"인 테스트인데, `expected_error=1`을 설정하지 않으면 테스트 설계 의도와 정반대로 fatal로 종료된다. 에러 테스트를 작성할 때 `expected_error=1` 설정이 가장 먼저 해야 할 일인 이유다.

### Q8. (Create) RNR retry exceed 시나리오를 의도적으로 발생시키는 시퀀스를 작성하시오 (개념 4 단계).
**정답.**
1. Receiver 측 RQ 에 Recv WQE 를 매우 적게 post (예: 1개).
2. Sender 측에서 다수의 SEND 발행 (예: 100개).
3. RNR retry 와 timeout 을 의도적으로 작게 설정 (`min_rnr_timeout` 작게, `retry_cnt` 작게 — `vrdmatb_error_handling_test_lib.svh:14-19`).
4. 마지막 SEND 의 `cmd.expected_error = 1` + 폴링 후 `wc_error_status[qp][0] == WC_RNR_RETRY_EXC_ERR` 검증.
**Why.** RNR(Receiver Not Ready)은 수신자 RQ에 버퍼가 없을 때 발생하는 NAK이다. 의도적으로 발생시키려면 수신자 버퍼를 의도적으로 부족하게 만들어야 한다(단계 1-2). retry 설정을 작게 해야 빠르게 재시도 한계에 도달한다(단계 3). `expected_error=1` 없이는 단계 3 이후 즉시 fatal이 발생하므로, 마지막 SEND가 exceed를 유발할 것임을 미리 선언해야 한다(단계 4). `wc_error_status[qp][0]` 검증이 "예상한 에러가 올바르게 발생했는가"를 확인하는 최종 판정이다.
