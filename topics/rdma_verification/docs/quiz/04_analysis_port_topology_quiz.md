# Module 04 퀴즈 — Analysis Port Topology

본문: [Module 04](../04_analysis_port_topology.md)

---

### Q1. (Remember) `vrdma_driver` 가 broadcasting 하는 5개 AP 를 나열하시오.
**정답.** `issued_wqe_ap`, `completed_wqe_ap`, `cqe_ap`, `qp_reg_ap`, `mr_reg_ap`.
**Why.** 이 5개 AP는 RDMA-TB의 모든 횡단 검증 컴포넌트가 구독하는 "공개 이벤트 스트림"이다. `issued_wqe_ap`는 WQE 발행 시점, `completed_wqe_ap`는 완료 시점, `cqe_ap`는 raw CQE, `qp_reg_ap`는 QP 등록/해제 이벤트, `mr_reg_ap`는 MR 등록/해제 이벤트를 전달한다. 이 5개의 이름과 역할을 외우면 "어떤 정보가 필요한가?"라는 질문에서 구독할 AP를 즉시 선택할 수 있다. 출처: `vrdma_driver.svh:56-61`.

### Q2. (Understand) `completed_wqe_ap` 가 ErrQP 의 WQE 를 broadcast 하지 않는 이유는?
**정답.** 에러 QP 의 WQE 는 검증 의미가 없어 scoreboard 에서 제외해야 정합성 검증 정확도가 보존됨. `if(!t_qp.isErrQP()) this.completed_wqe_ap.write(cmd);` 가 게이트(Module 04 / vrdma_driver.svh:1327).
**Why.** ErrQP는 `setErrState(1)` 이후 모든 verb가 driver에서 skip되거나 flush되는 상태다. 이 QP의 WQE 완료를 `completed_wqe_ap`로 broadcast하면 scoreboard가 "비교해야 할 데이터"로 받아 들여 잘못된 mismatch를 발생시킨다. 따라서 ErrQP의 WQE는 AP 게이트에서 차단하고 comparator에 도달하지 못하게 설계되어 있다. 이 게이트를 이해하지 못하면 에러 테스트 중 발생하는 spurious mismatch를 DUT 버그로 오해할 수 있다.

### Q3. (Apply) 새 RTT scoreboard 가 RTT probe send → response 매칭 latency 를 측정한다. 어느 AP 를 구독하는가?
**정답.** `drv.issued_wqe_ap` (probe send 시작) + `drv.completed_wqe_ap` 또는 `cq_handler.cqe_validation_cqe_ap` (응답 도착). 두 시점 차이로 RTT.
**Why.** RTT는 "요청 발행 시점"에서 "응답 수신 시점"까지의 시간이다. 발행 시점은 `issued_wqe_ap`에서, 응답 수신은 CQE가 도착하는 시점인 `completed_wqe_ap` 또는 디코딩된 `cqe_validation_cqe_ap`에서 포착할 수 있다. 기존 driver/handler 코드를 전혀 수정하지 않고 AP 구독만으로 RTT 측정 컴포넌트를 추가할 수 있다는 점이 DRY via AP 원칙의 실제 적용이다. 실제로 `lib/ext/component/congestion_control/ccmad/vrdma_rtt_scoreboard.svh`가 이 패턴으로 구현되어 있다.

### Q4. (Analyze) `qp_reg_ap` 와 `mr_reg_ap` 를 모두 구독해야 하는 컴포넌트는 어떤 것들인가? 왜?
**정답.** `c2h_tracker` 와 data scoreboard. C2H tracker 는 expected PA 큐를 만들기 위해 QP 와 MR(IOVA→PA 매핑)을 모두 알아야 함. scoreboard 도 마찬가지.
**Why.** C2H 검증에서 "DUT가 이 주소에 쓴 데이터가 올바른가?"를 판단하려면 두 가지를 알아야 한다: (1) 어느 QP의 WQE인가(`qp_reg_ap`로 QP 정보 수신), (2) 그 WQE의 IOVA가 어떤 PA로 매핑되는가(`mr_reg_ap`로 MR 정보 수신). 둘 중 하나라도 없으면 expected PA 큐를 만들 수 없어 매칭 자체가 불가능해진다. 이 의존성이 Module 04 토폴로지 그림의 핵심 정보다.

### Q5. (Evaluate) "내가 필요한 정보는 `cq_handler` 안에 있으니 `cq_handler` 에 hook 코드를 추가하자" 는 제안을 평가하시오.
**정답.** 잘못됨. `cq_handler.cqe_validation_cqe_ap` 가 이미 디코딩된 CQE 를 broadcasting 하므로 그것을 구독해야 함(DRY). hook 추가는 Open-Closed + DRY 동시 위반.
**Why.** `cq_handler`는 디코딩된 CQE를 `cqe_validation_cqe_ap`로 이미 broadcast하고 있다. hook을 추가하는 것은 기존 컴포넌트를 수정하는 것으로, Open-Closed 원칙 위반이다. 또한 같은 CQE 정보를 여러 곳에서 독립적으로 처리하게 만들어 DRY 원칙도 깨진다. AP를 구독하는 방식은 `cq_handler` 코드를 한 줄도 건드리지 않고 새 기능을 추가하는 올바른 방법이다.

### Q6. (Apply) `vrdma_pkt_base_monitor::turn_off = 1` 로 하면 `ntw_env` 의 어떤 검증이 멈추는가? `data_env` 는?
**정답.** `ntw_env` 의 패킷 protocol checker(OPS/RC monitor 의 `turnOff()` 동작)가 멈춘다. `data_env` 는 별도 — comparator 는 driver AP 구독이라 무관.
**Why.** `vrdma_pkt_base_monitor`는 네트워크 패킷 레벨의 프로토콜 검증을 담당하는 `ntw_env` 컴포넌트다. `turn_off`는 이 모니터만 비활성화하며, `data_env`의 comparator는 driver AP를 구독하는 별개 경로로 동작하므로 영향을 받지 않는다. 컴포넌트별 독립 on/off가 가능한 이유가 바로 AP 구독 기반의 분리 설계 덕분임을 이해해야 한다.

### Q7. (Analyze) `issued_wqe_ap` 가 발행되는 순간(`vrdma_driver.svh:1195`)과 실제 DUT 가 WQE 를 SQ 에서 fetch 하는 순간 사이에 시간 차이가 있다. 이 차이를 어떻게 활용할 수 있는가?
**정답.** TB가 issue 를 broadcast 한 후 DUT 가 SQ doorbell 인식 → WQE fetch 까지 시간을 측정 가능. CQ poll timeout(M09) 디버깅 시 "DUT 가 doorbell 을 인식했는가?" 답을 낼 수 있다(QID 14-17 fetch 와 cross).
**Why.** `issued_wqe_ap` broadcast 시점은 TB가 SQ에 WQE를 써 넣고 doorbell을 울린 시점이다. 이후 DUT가 doorbell을 인식해 SQ를 fetch하기까지 H2C QID 14-17 트랜잭션이 발생해야 한다. CQ poll timeout이 발생했을 때 이 시간 구간에 QID 14-17 fetch가 없다면, DUT가 doorbell을 아예 인식하지 못했다는 결론을 내릴 수 있다. Module 09의 빠른 트리아지 1행이 바로 이 분석이다.

### Q8. (Create) 새 cqe coverage collector 가 wc_status 별 발생 빈도를 샘플링한다. 어떤 AP 를 구독해야 하는가? 디코딩 vs raw 중 무엇을 선호?
**정답.** `cq_handler.cqe_validation_cqe_ap` (디코딩된 CQE). `cqe_ap` (raw) 도 가능하지만 디코딩된 필드(`wc_status`, `debug_wc_flag`, `local_qid` 등)에 직접 접근하려면 validation 후 AP 가 더 적합.
**Why.** `cqe_ap`는 raw CQE 바이트 스트림이므로 collector가 직접 파싱해야 한다. 반면 `cqe_validation_cqe_ap`는 `cq_handler`가 이미 디코딩한 구조체를 전달하므로 `wc_status`, `local_qid` 같은 필드에 바로 접근할 수 있다. 파싱 로직을 collector에 중복해서 구현하지 않으려면 디코딩된 AP를 선택하는 것이 DRY 원칙에 부합한다.
