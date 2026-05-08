# Module 04 퀴즈 — Analysis Port Topology

본문: [Module 04](../04_analysis_port_topology.md)

---

### Q1. (Remember) `vrdma_driver` 가 broadcasting 하는 5개 AP 를 나열하시오.
**정답.** `issued_wqe_ap`, `completed_wqe_ap`, `cqe_ap`, `qp_reg_ap`, `mr_reg_ap`.
**Why.** `vrdma_driver.svh:56-61`.

### Q2. (Understand) `completed_wqe_ap` 가 ErrQP 의 WQE 를 broadcast 하지 않는 이유는?
**정답.** 에러 QP 의 WQE 는 검증 의미가 없어 scoreboard 에서 제외해야 정합성 검증 정확도가 보존됨. `if(!t_qp.isErrQP()) this.completed_wqe_ap.write(cmd);` 가 게이트(Module 04 / vrdma_driver.svh:1327).
**Why.** Error gate 의 정합성 보호.

### Q3. (Apply) 새 RTT scoreboard 가 RTT probe send → response 매칭 latency 를 측정한다. 어느 AP 를 구독하는가?
**정답.** `drv.issued_wqe_ap` (probe send 시작) + `drv.completed_wqe_ap` 또는 `cq_handler.cqe_validation_cqe_ap` (응답 도착). 두 시점 차이로 RTT.
**Why.** Module 05 #3 DRY via AP. 실제 구현이 `lib/ext/component/congestion_control/ccmad/vrdma_rtt_scoreboard.svh` 에 존재.

### Q4. (Analyze) `qp_reg_ap` 와 `mr_reg_ap` 를 모두 구독해야 하는 컴포넌트는 어떤 것들인가? 왜?
**정답.** `c2h_tracker` 와 data scoreboard. C2H tracker 는 expected PA 큐를 만들기 위해 QP 와 MR(IOVA→PA 매핑)을 모두 알아야 함. scoreboard 도 마찬가지.
**Why.** Module 04 의 토폴로지 그림.

### Q5. (Evaluate) "내가 필요한 정보는 `cq_handler` 안에 있으니 `cq_handler` 에 hook 코드를 추가하자" 는 제안을 평가하시오.
**정답.** 잘못됨. `cq_handler.cqe_validation_cqe_ap` 가 이미 디코딩된 CQE 를 broadcasting 하므로 그것을 구독해야 함(DRY). hook 추가는 Open-Closed + DRY 동시 위반.
**Why.** Module 05 #1, #3.

### Q6. (Apply) `vrdma_pkt_base_monitor::turn_off = 1` 로 하면 `ntw_env` 의 어떤 검증이 멈추는가? `data_env` 는?
**정답.** `ntw_env` 의 패킷 protocol checker(OPS/RC monitor 의 `turnOff()` 동작)가 멈춘다. `data_env` 는 별도 — comparator 는 driver AP 구독이라 무관.
**Why.** Module 06 §5 의 컴포넌트별 OFF.

### Q7. (Analyze) `issued_wqe_ap` 가 발행되는 순간(`vrdma_driver.svh:1195`)과 실제 DUT 가 WQE 를 SQ 에서 fetch 하는 순간 사이에 시간 차이가 있다. 이 차이를 어떻게 활용할 수 있는가?
**정답.** TB가 issue 를 broadcast 한 후 DUT 가 SQ doorbell 인식 → WQE fetch 까지 시간을 측정 가능. CQ poll timeout(M09) 디버깅 시 "DUT 가 doorbell 을 인식했는가?" 답을 낼 수 있다(QID 14-17 fetch 와 cross).
**Why.** Module 09 §Step 2 와 직접 연결.

### Q8. (Create) 새 cqe coverage collector 가 wc_status 별 발생 빈도를 샘플링한다. 어떤 AP 를 구독해야 하는가? 디코딩 vs raw 중 무엇을 선호?
**정답.** `cq_handler.cqe_validation_cqe_ap` (디코딩된 CQE). `cqe_ap` (raw) 도 가능하지만 디코딩된 필드(`wc_status`, `debug_wc_flag`, `local_qid` 등)에 직접 접근하려면 validation 후 AP 가 더 적합.
**Why.** Module 04 의 derived AP 의도(디코딩 후 분배).
