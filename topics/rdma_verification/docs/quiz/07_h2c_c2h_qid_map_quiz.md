# Module 07 퀴즈 — H2C / C2H QID Reference

본문: [Module 07](../07_h2c_c2h_qid_map.md)

---

### Q1. (Remember) H2C QID 8 과 H2C QID 9 의 차이는?
**정답.** QID 8 = Requester payload fetch (Send/Write source), QID 9 = Responder payload fetch (Read Response source).
**Why.** `vrdma_defs.svh:75-76`.

### Q2. (Remember) C2H QID 10–11 (`COMP_C2H_QID`) 의 용도는?
**정답.** CQE write — DUT 가 host CQ 메모리에 Completion Queue Entry 를 쓰는 채널 (2채널).
**Why.** `vrdma_defs.svh:84`.

### Q3. (Apply) "CQ Poll Timeout 발생, DUT 가 SQ doorbell 을 인식했나?" — 어느 QID 를 확인?
**정답.** H2C QID 14–17 (`RDMA_CMD_H2C_QID[0:3]`). 4 채널 모두 검색해야 함.
**Why.** Module 07 §H2C 디버깅 표 + Module 09 Step 2.

### Q4. (Apply) "C2H tracker 가 PA matching 실패. 어느 QP 의 데이터인가?" — 어느 QID 를 확인?
**정답.** C2H QID 8–9 (`RESP_C2H_QID[0:1]`). 두 채널 모두.
**Why.** Module 07 §C2H 디버깅 표 + Module 10 Step 2.

### Q5. (Analyze) "Recv 가 처리 안 되는 것 같다" — H2C QID 10–13 도 안 나오고 QID 8 도 안 나온다. 무엇을 의미하는가?
**정답.** Recv WQE fetch 자체가 안 됨 → DUT 가 RQ doorbell 인식 실패. RAL/BAR 의 RQ_DB 쓰기부터 추적해야 함.
**Why.** Module 07 §디버깅 워크플로우 Case 1.

### Q6. (Analyze) "QID 20 (`RDMA_MISS_PA_H2C_QID`)이 빈번하게 발생한다." 의미는?
**정답.** PTW miss 가 자주 발생 — page table walker 가 cache miss 를 자주 본다는 뜻. 정상이지만 트래픽 패턴이 page locality 가 낮거나 MR 이 매우 큰 경우. 성능 문제 의심.
**Why.** QID 20 의 정의 — page table miss.

### Q7. (Evaluate) "QID 만 보면 충분하니까 transaction 의 addr/size 는 안 봐도 된다" 를 평가하시오.
**정답.** 잘못됨. QID 는 어느 서브시스템인지 알려주지만 어느 주소에 쓰는지/얼마나 크게 쓰는지는 모름. PA matching 검증, ordering 검증, 크기 검증 모두 addr/size 가 필요.
**Why.** Module 10 의 디버깅 단계가 모두 addr/size 의존.

### Q8. (Create) Congestion Control 이벤트가 발생하지 않는 것 같다. 어느 QID 를 어떤 단계로 검사하는가?
**정답.**
1. C2H QID 14 (`CC_NOTIFY_C2H_QID`) — DMA 트랜잭션이 한 번이라도 발생했는가?
2. 발생했으면 addr/data 가 expected CC notification 형식과 일치하는가?
3. 발생 안 했으면 DUT 의 CC engine 이 enable 되었나, threshold 가 너무 높지 않은가 검사.
**Why.** Module 07 §C2H 표 — CC 이벤트 미수신 디버깅.
