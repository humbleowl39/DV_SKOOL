# Module 11 퀴즈 — Unexpected Error CQE

본문: [Module 11](../11_debug_unexpected_err_cqe.md)

---

### Q1. (Remember) 정상 시뮬에서 발생 가능한 에러 CQE 두 가지를 답하시오.
**정답.** `WC_RETRY_EXC_ERR` (12), `WC_RNR_RETRY_EXC_ERR` (13). 둘 다 HW 리소스 부족.
**Why.** Module 11 §에러 발생 원칙.

### Q2. (Understand) `WC_WR_FLUSH_ERR` (5) 가 보였을 때 어디부터 디버깅?
**정답.** 이 에러는 항상 2차 영향 — flush 직전의 선행 에러부터 디버깅. 시간 거꾸로 가서 첫 에러 CQE 를 찾는다.
**Why.** Flush 의 정의 — outstanding 의 강제 정리.

### Q3. (Apply) `F-CQHDL-TBERR-0003` 발생 + `wc_status = 12 (WC_RETRY_EXC_ERR)`. 첫 액션은?
**정답.** RETRY 계열이므로 DUT 버그가 아닌 HW 성능 한계 의심. 트래픽 부하(동시 outstanding WQE 수, MTU 대비 burst), retry 설정(`timeout`, `retry_cnt`) 조절.
**Why.** Module 11 §Step 2A.

### Q4. (Apply) `F-CQHDL-TBERR-0003` 발생 + `wc_status = 4 (WC_LOC_PROT_ERR)`. 어떤 단계로 디버깅?
**정답.**
1. TB 가 발행한 WQE 의 lkey 확인 — 잘못된 lkey 가 발행되었나?
2. lkey 가 정상이면 DUT 의 lkey 검증 로직 의심 — DUT 가 정상 lkey 를 reject.
**Why.** Module 11 §Step 2B + Step 3 (TB 설정 배제).

### Q5. (Analyze) 에러 CQE 가 도착하면 TB state 5 가지가 자동 변화한다. 나열하시오.
**정답.**
1. QP `setErrState(1)` (이후 verb skip)
2. Outstanding WQE 전체 flush (`completeOutstanding`)
3. CQ polling 루프 즉시 종료 (`cmd.error_occured = 1`)
4. Scoreboard 차단 (에러 CQE 는 `cqe_ap` 로 안 감)
5. Sequencer 의 `wc_error_status[qp]`, `debug_wc_flag[qp]` 에 기록
**Why.** Module 11 §에러 발생 후 TB state.

### Q6. (Evaluate) "DUT 가 rkey 검증을 안 한다" 라는 결론을 내리려면 어떤 증거가 필요한가?
**정답.**
- TB 가 정상 rkey 로 read 발행했는데 `WC_REM_ACCESS_ERR` (10) 도착 (false positive 가능 — DUT bug)
- TB 가 잘못된 rkey 로 read 발행했는데 success CQE 도착 (false negative — 검증 누락)
- 둘 다 + DUT 의 rkey 검증 로직 fsdb trace
**Why.** Symmetric evidence — 양 방향 모두 봐야 단정 가능.

### Q7. (Apply) 의도된 RAE 시나리오에서 `expected_error=1` 을 안 걸면 무엇이 일어나는가?
**정답.** `F-CQHDL-TBERR-0003` (FATAL) 발생 → 시뮬 즉시 종료. `cmd.expected_error == 0` 조건이 충족되어 unexpected 로 처리.
**Why.** Module 11 §발생 조건.

### Q8. (Create) RNR retry exceed 시나리오를 의도적으로 발생시키는 시퀀스를 작성하시오 (개념 4 단계).
**정답.**
1. Receiver 측 RQ 에 Recv WQE 를 매우 적게 post (예: 1개).
2. Sender 측에서 다수의 SEND 발행 (예: 100개).
3. RNR retry 와 timeout 을 의도적으로 작게 설정 (`min_rnr_timeout` 작게, `retry_cnt` 작게 — `vrdmatb_error_handling_test_lib.svh:14-19`).
4. 마지막 SEND 의 `cmd.expected_error = 1` + 폴링 후 `wc_error_status[qp][0] == WC_RNR_RETRY_EXC_ERR` 검증.
**Why.** Error handling test cfg 의 의도된 적용.
