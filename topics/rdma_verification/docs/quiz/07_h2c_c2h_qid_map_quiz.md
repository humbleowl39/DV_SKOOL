# Module 07 퀴즈 — H2C / C2H QID Reference

본문: [Module 07](../07_h2c_c2h_qid_map.md)

---

### Q1. (Remember) H2C QID 8 과 H2C QID 9 의 차이는?
**정답.** QID 8 = Requester payload fetch (Send/Write source), QID 9 = Responder payload fetch (Read Response source).
**Why.** QID 8과 9는 모두 Host→Card 방향의 payload를 가져오는 채널이지만 역할이 다르다. QID 8은 SEND나 WRITE 같이 송신 측이 initiator인 verb의 데이터를 fetch할 때 사용하고, QID 9는 Read의 경우 응답자(responder) 측이 Read Response로 보낼 데이터를 fetch할 때 사용한다. 이 차이를 모르면 "데이터 mismatch 발생, payload가 잘못됨"이라는 상황에서 어느 QID를 봐야 할지 방향을 잡지 못한다. 출처: `vrdma_defs.svh:75-76`.

### Q2. (Remember) C2H QID 10–11 (`COMP_C2H_QID`) 의 용도는?
**정답.** CQE write — DUT 가 host CQ 메모리에 Completion Queue Entry 를 쓰는 채널 (2채널).
**Why.** C2H QID 10-11은 DUT가 작업 완료를 host에게 알리는 채널이다. CQ polling이 아무리 기다려도 응답이 없을 때, 이 QID에 DMA 트랜잭션이 있는지 확인하면 "DUT가 CQE를 쓰려 했는가?"를 알 수 있다. 이 QID가 없다면 DUT의 completion engine이 CQE를 생성하지 못한 것이므로, CQ poll timeout 디버깅 시 Step 3의 핵심 증거가 된다.

### Q3. (Apply) "CQ Poll Timeout 발생, DUT 가 SQ doorbell 을 인식했나?" — 어느 QID 를 확인?
**정답.** H2C QID 14–17 (`RDMA_CMD_H2C_QID[0:3]`). 4 채널 모두 검색해야 함.
**Why.** SQ doorbell을 DUT가 인식했다면 SQ에서 WQE를 fetch하는 H2C 트랜잭션(QID 14-17)이 발생해야 한다. 이 QID에 트랜잭션이 없다면 doorbell 자체를 DUT가 못 받은 것이고, 있다면 WQE fetch는 성공했지만 이후 처리 단계에서 문제가 생긴 것이다. 4채널(14/15/16/17)을 모두 검색해야 하는 이유는 DUT가 라운드로빈 방식으로 채널을 사용할 수 있기 때문이다. 이 분석이 Module 09 트리아지 1행이다.

### Q4. (Apply) "C2H tracker 가 PA matching 실패. 어느 QP 의 데이터인가?" — 어느 QID 를 확인?
**정답.** C2H QID 8–9 (`RESP_C2H_QID[0:1]`). 두 채널 모두.
**Why.** C2H PA 매칭 실패는 DUT가 host 메모리에 데이터를 잘못된 주소에 쓴 경우다. DUT가 데이터를 쓰는 채널이 C2H QID 8-9이므로, 이 QID의 트랜잭션을 보면 어느 주소에 무슨 데이터가 쓰였는지 확인할 수 있다. 두 채널 모두 검색해야 하는 이유는 QP 또는 WQE에 따라 채널이 다를 수 있기 때문이다. 주소 값을 TB의 expected PA 큐와 비교하면 어느 QP의 데이터인지 특정 가능하다.

### Q5. (Analyze) "Recv 가 처리 안 되는 것 같다" — H2C QID 10–13 도 안 나오고 QID 8 도 안 나온다. 무엇을 의미하는가?
**정답.** Recv WQE fetch 자체가 안 됨 → DUT 가 RQ doorbell 인식 실패. RAL/BAR 의 RQ_DB 쓰기부터 추적해야 함.
**Why.** H2C QID 10-13은 Recv WQE fetch 채널이고, QID 8은 Requester payload fetch다. SEND verb 처리 흐름에서 Recv 측은 먼저 RQ에서 Recv WQE를 fetch(QID 10-13)해야 그 버퍼에 payload가 오는 것이다. 두 QID 모두 없다는 것은 DUT가 RQ에 Recv WQE가 있다는 사실 자체를 모른다는 뜻이다. 따라서 RQ doorbell 레지스터(RAL/BAR 주소)가 올바르게 쓰였는지부터 확인해야 한다.

### Q6. (Analyze) "QID 20 (`RDMA_MISS_PA_H2C_QID`)이 빈번하게 발생한다." 의미는?
**정답.** PTW miss 가 자주 발생 — page table walker 가 cache miss 를 자주 본다는 뜻. 정상이지만 트래픽 패턴이 page locality 가 낮거나 MR 이 매우 큰 경우. 성능 문제 의심.
**Why.** QID 20은 DUT의 PTW(Page Table Walker)가 IOVA→PA 변환 중 TLB 또는 캐시에서 miss가 발생해 host에서 PTE를 가져오는 채널이다. 가끔 발생하는 것은 정상이지만 빈번하면 두 가지를 의심해야 한다: (1) MR이 매우 넓어 page table entry가 많아 캐시 효율이 낮거나, (2) WQE가 page locality가 낮은 불연속 주소를 사용해 PTW miss가 반복되는 경우. 성능 최적화나 MR 크기 검토가 필요하다는 신호다.

### Q7. (Evaluate) "QID 만 보면 충분하니까 transaction 의 addr/size 는 안 봐도 된다" 를 평가하시오.
**정답.** 잘못됨. QID 는 어느 서브시스템인지 알려주지만 어느 주소에 쓰는지/얼마나 크게 쓰는지는 모름. PA matching 검증, ordering 검증, 크기 검증 모두 addr/size 가 필요.
**Why.** QID는 "어느 채널"인지는 알려주지만, 같은 채널을 통해 잘못된 주소에 데이터가 쓰였는지는 알 수 없다. C2H tracker의 PA 매칭 검증은 "DUT가 쓴 주소 == TB가 기대한 주소"를 확인해야 하므로 addr 없이는 불가능하다. 크기 검증도 마찬가지다 — QID가 맞더라도 transfer_size가 틀리면 DUT 버그다. QID는 트리아지의 첫 단계일 뿐, 최종 검증은 항상 addr/size 수준에서 이루어진다.

### Q8. (Create) Congestion Control 이벤트가 발생하지 않는 것 같다. 어느 QID 를 어떤 단계로 검사하는가?
**정답.**
1. C2H QID 14 (`CC_NOTIFY_C2H_QID`) — DMA 트랜잭션이 한 번이라도 발생했는가?
2. 발생했으면 addr/data 가 expected CC notification 형식과 일치하는가?
3. 발생 안 했으면 DUT 의 CC engine 이 enable 되었나, threshold 가 너무 높지 않은가 검사.
**Why.** CC 이벤트가 없을 때 가능한 원인은 두 가지다: DUT가 CC 이벤트를 아예 생성하지 않은 경우(QID 14 트랜잭션 없음)와, 이벤트는 생성했지만 내용이 잘못된 경우(QID 14 있지만 포맷 불일치). QID 유무를 먼저 확인해 두 경우를 분리해야 한다. QID 없음이면 DUT의 CC 엔진 설정(enable bit, threshold)을 확인하는 것이 다음 단계이며, QID 있음이면 payload 포맷 검증으로 진행한다.
