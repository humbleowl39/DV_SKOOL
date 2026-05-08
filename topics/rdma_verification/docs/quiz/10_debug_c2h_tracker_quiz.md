# Module 10 퀴즈 — C2H Tracker Error

본문: [Module 10](../10_debug_c2h_tracker.md)

---

### Q1. (Remember) C2H tracker 의 3 분류 실패 ID prefix 를 답하시오.
**정답.** PA 매칭: `F-C2H-MATCH-0001/0002`. Ordering: `E-C2H-MATCH-0001`. 크기 초과: `F-C2H-MATCH-0003/0004/0005`.
**Why.** Module 10 §대표 에러 메시지.

### Q2. (Understand) RC QP 와 OPS/SR QP 의 ordering 검증 차이는?
**정답.** RC = FIFO 강제(index 0 만 체크), OPS/SR = out-of-order 허용(전체 인덱스 범위 체크).
**Why.** RC 의 reliable connected 본질 + OPS/SR 의 performance 우선.

### Q3. (Apply) `F-C2H-MATCH-0002`: addr=0x1000, QP=5, node=node0. 진단 로그(`W-C2H-MATCH-*`)에서 expected PA 큐를 추출했다. 다음 단계 2 가지를 답하시오.
**정답.**
1. addr=0x1000 을 모든 QP 의 PA 큐와 cross-reference (다른 QP 의 PA 와 매칭되면 DUT QP routing 오류).
2. 어느 QP 와도 무관하면 TB `translateIOVA` 결과와 DUT PTW 결과를 비교 (변환 차이).
**Why.** Module 10 §Step 2-3.

### Q4. (Analyze) RC QP 에서 `E-C2H-MATCH-0001` (ordering violation) 발생. 가능한 DUT 버그 두 가지는?
**정답.**
- DUT 의 RC packet ordering 로직이 OoO 로 처리 (스펙 위반).
- DUT 가 같은 RC 의 두 WQE 를 병렬 dispatch 하여 race 발생 (RC 인데 SQ dequeue 가 OoO).
**Why.** RC FIFO 강제 위반 = DUT 스펙 위반.

### Q5. (Apply) Zero-length write 가 등록 안 되어 매칭 실패. 어떻게 회피?
**정답.** Zero-length 는 `trackCommand` 단계에서 skip — 정상 동작. DUT 가 zero-length 에 대해 C2H 를 발생시키지 않아야 함. DUT 가 발생시킨다면 DUT 버그.
**Why.** Module 10 §흔한 원인 — Zero-length drop.

### Q6. (Analyze) Error QP 정리(`RDMAQPDestroy(.err(1))`) 직후 늦게 도착하는 C2H 가 fatal 을 일으키지 않는 메커니즘은?
**정답.** `vrdma_c2h_tracker.svh:346-349` 의 `is_err_qp_registered.size() > 0` 체크. ErrQP 가 deregister 된 후 도착하는 트랜잭션은 fatal 대신 silent skip.
**Why.** Module 06 + Module 10 cross-reference.

### Q7. (Evaluate) "MR re-register race" 가 의심되는 시나리오를 답하시오.
**정답.** 같은 MR 을 짧은 시간에 deregister → re-register 하면, DUT 의 PA cache 가 구버전 PA 를 들고 있고 TB 는 신버전을 expected 로 기대 → 매칭 실패. `gen_id` 추적으로 확인 가능 (Fast Register 시 gen_id 갱신).
**Why.** Module 10 §흔한 원인 표 + `gen_id` 의 의도.

### Q8. (Create) DUT QP routing 버그를 의심한다. 검증 절차 3단계 를 답하시오.
**정답.**
1. fatal 시점의 C2H QID(8/9) 와 addr 추출.
2. 원본 WQE (driver 의 `issued_wqe_ap` log) 에서 해당 데이터의 dest_qp 확인.
3. addr 를 dest_qp 의 PA 큐와 비교 — addr 가 다른 QP 의 PA 와 매칭되면 DUT 가 dest_qp 를 잘못 라우팅. fsdb 에서 RDMA opcode 의 dest_qp 필드 추적.
**Why.** Module 10 §Step 2 + §흔한 원인 매트릭스.
