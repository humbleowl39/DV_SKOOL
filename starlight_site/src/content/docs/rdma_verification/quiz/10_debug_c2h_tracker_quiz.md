---
title: "Module 10 퀴즈 — C2H Tracker Error"
---

본문: [Module 10](../../10_debug_c2h_tracker/)

---

### Q1. (Remember) C2H tracker 의 3 분류 실패 ID prefix 를 답하시오.
**정답.** PA 매칭: `F-C2H-MATCH-0001/0002`. Ordering: `E-C2H-MATCH-0001`. 크기 초과: `F-C2H-MATCH-0003/0004/0005`.
**Why.** 3개 분류는 c2h_tracker가 검증하는 3가지 속성(주소 정확성, 순서, 크기)에 대응한다. PA 매칭 실패는 "잘못된 주소에 DMA가 발생"한 것이고, Ordering 실패는 "RC QP에서 FIFO 순서가 어긴" 것이며, 크기 초과는 "DMA 크기가 허용 범위를 벗어난" 것이다. 에러 ID만 보고 3가지 중 어느 속성이 위반됐는지 즉시 알 수 있어야 디버그 방향을 잡을 수 있다.

### Q2. (Understand) RC QP 와 OPS/SR QP 의 ordering 검증 차이는?
**정답.** RC = FIFO 강제(index 0 만 체크), OPS/SR = out-of-order 허용(전체 인덱스 범위 체크).
**Why.** RC(Reliable Connected)는 IBTA 스펙에서 packet ordering을 보장하도록 정의되어 있다. 따라서 RC QP의 C2H DMA는 반드시 WQE 발행 순서대로 도착해야 하며, `c2h_tracker`는 FIFO 큐에서 index 0(선두)만 체크해 순서 위반을 감지한다. OPS/SR(Out-of-order Packet Sending / Selective Repeat)은 성능 우선 프로토콜로 패킷이 재정렬될 수 있으므로, 전체 큐를 탐색해 매칭 여부를 확인한다. 이 차이를 모르면 OPS QP에서 ordering violation이 발생해도 RC QP의 기준으로 잘못 진단할 수 있다.

### Q3. (Apply) `F-C2H-MATCH-0002`: addr=0x1000, QP=5, node=node0. 진단 로그(`W-C2H-MATCH-*`)에서 expected PA 큐를 추출했다. 다음 단계 2 가지를 답하시오.
**정답.**
1. addr=0x1000 을 모든 QP 의 PA 큐와 cross-reference (다른 QP 의 PA 와 매칭되면 DUT QP routing 오류).
2. 어느 QP 와도 무관하면 TB `translateIOVA` 결과와 DUT PTW 결과를 비교 (변환 차이).
**Why.** `F-C2H-MATCH-0002`는 DUT가 쓴 주소(0x1000)가 QP 5의 expected PA 큐에 없다는 의미다. 이 상황의 원인은 두 가지다: 다른 QP의 PA와 매칭된다면 DUT가 데이터를 잘못된 QP로 라우팅한 것이고(QP routing 버그), 어느 QP와도 무관하다면 IOVA→PA 변환 자체가 틀린 것이다(PTW 버그 또는 TB MR 설정 오류). cross-reference를 먼저 수행해 두 경우를 분리하는 것이 효율적이다.

### Q4. (Analyze) RC QP 에서 `E-C2H-MATCH-0001` (ordering violation) 발생. 가능한 DUT 버그 두 가지는?
**정답.**
- DUT 의 RC packet ordering 로직이 OoO 로 처리 (스펙 위반).
- DUT 가 같은 RC 의 두 WQE 를 병렬 dispatch 하여 race 발생 (RC 인데 SQ dequeue 가 OoO).
**Why.** RC는 "Reliable Connected"로 IBTA 스펙상 packet 순서 보장이 필수다. ordering violation이 발생했다는 것은 이 스펙 요건이 위반된 것이므로 항상 DUT 버그다. 버그의 형태는 두 가지로 나뉜다: RC 패킷을 OoO로 처리하는 로직 버그와, SQ에서 두 WQE를 동시에 dispatch해 C2H DMA가 경쟁하는 병렬화 버그다. 두 경우 모두 IBTA RC semantics 위반이다.

### Q5. (Apply) Zero-length write 가 등록 안 되어 매칭 실패. 어떻게 회피?
**정답.** Zero-length 는 `trackCommand` 단계에서 skip — 정상 동작. DUT 가 zero-length 에 대해 C2H 를 발생시키지 않아야 함. DUT 가 발생시킨다면 DUT 버그.
**Why.** zero-length write는 데이터 전송이 없는 verb이므로 C2H DMA도 발생하지 않아야 한다. `c2h_tracker`는 이 경우 `trackCommand` 단계에서 expected PA를 등록하지 않는다(skip). 따라서 DUT가 zero-length write에 대해 C2H DMA를 발생시키면, expected PA 큐에 해당 항목이 없어 매칭 실패(`F-C2H-MATCH-0001/0002`)가 생긴다 — 이는 DUT가 zero-length에 불필요한 DMA를 생성하는 버그다. 이 동작을 "TB 설정 오류"로 오해하지 않아야 한다.

### Q6. (Analyze) Error QP 정리(`RDMAQPDestroy(.err(1))`) 직후 늦게 도착하는 C2H 가 fatal 을 일으키지 않는 메커니즘은?
**정답.** `vrdma_c2h_tracker.svh:346-349` 의 `is_err_qp_registered.size() > 0` 체크. ErrQP 가 deregister 된 후 도착하는 트랜잭션은 fatal 대신 silent skip.
**Why.** RDMA 에러 복구 중에는 DUT 파이프라인에 아직 진행 중인 DMA가 남아 있을 수 있다. ErrQP로 선언되고 `deregisterQP`가 호출된 후에도 이미 시작된 C2H DMA가 나중에 도착할 수 있는데, 이를 fatal로 처리하면 정상적인 에러 복구 시나리오가 항상 실패한다. `is_err_qp_registered` 플래그가 set되어 있으면 이 지연 도착 C2H를 silent skip으로 처리해 에러 복구 테스트가 PASS를 낼 수 있게 한다. 출처: `vrdma_c2h_tracker.svh:346-349`.

### Q7. (Evaluate) "MR re-register race" 가 의심되는 시나리오를 답하시오.
**정답.** 같은 MR 을 짧은 시간에 deregister → re-register 하면, DUT 의 PA cache 가 구버전 PA 를 들고 있고 TB 는 신버전을 expected 로 기대 → 매칭 실패. `gen_id` 추적으로 확인 가능 (Fast Register 시 gen_id 갱신).
**Why.** MR re-register race는 DUT의 internal cache(TLB 또는 MR cache)가 stale entry를 들고 있을 때 발생한다. TB는 re-register 즉시 새 PA로 expected 큐를 갱신하지만, DUT는 구버전 PA를 캐시에서 사용해 C2H DMA를 구버전 주소로 보낸다. `gen_id`는 이 race를 추적하기 위해 MR 생성마다 부여하는 식별자로, 로그에서 `gen_id` 버전 차이가 보이면 re-register race를 확인할 수 있다.

### Q8. (Create) DUT QP routing 버그를 의심한다. 검증 절차 3단계 를 답하시오.
**정답.**
1. fatal 시점의 C2H QID(8/9) 와 addr 추출.
2. 원본 WQE (driver 의 `issued_wqe_ap` log) 에서 해당 데이터의 dest_qp 확인.
3. addr 를 dest_qp 의 PA 큐와 비교 — addr 가 다른 QP 의 PA 와 매칭되면 DUT 가 dest_qp 를 잘못 라우팅. fsdb 에서 RDMA opcode 의 dest_qp 필드 추적.
**Why.** QP routing 버그의 증거는 "다른 QP의 PA 주소에 데이터가 쓰였다"는 것이다. 이를 확인하려면 (1) 어느 주소에 C2H가 왔는지(QID 8/9 주소), (2) TB가 발행한 WQE의 의도된 목적지(dest_qp), (3) 그 주소가 실제로 어느 QP에 속하는지(PA 큐 cross-reference)를 순서대로 확인해야 한다. 세 단계를 모두 수행해야만 "DUT가 dest_qp를 잘못 해석해 다른 QP 버퍼에 썼다"는 결론을 내릴 수 있다.
