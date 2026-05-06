# Quiz — Module 03: TOE Key Functions

[← Module 03 본문으로 돌아가기](../03_toe_key_functions.md)

---

## Q1. (Remember)

TSO와 LRO의 차이는?

??? answer "정답 / 해설"
    - **TSO (TCP Segmentation Offload)**: TX side. SW의 큰 buffer를 HW가 MTU 단위로 분할.
    - **LRO (Large Receive Offload)**: RX side. HW가 연속 segment를 합쳐 SW에 한 번에 전달.

## Q2. (Understand)

RSS의 indirection table은 무엇인가?

??? answer "정답 / 해설"
    5-tuple hash → queue 매핑 table. Hash 결과의 LSB N bit를 indirection table 인덱스로 사용해 target queue 결정. SW가 queue 구성을 변경할 때 hash 알고리즘 변경 없이 indirection table만 업데이트.

## Q3. (Apply)

Fast retransmit이 trigger되는 조건은?

??? answer "정답 / 해설"
    **3개의 duplicate ACK 수신**. 같은 ACK number를 3번 받으면 receiver가 그 다음 segment를 못 받았다는 신호 → RTO 만료 기다리지 않고 즉시 재전송. RTO보다 빠른 복구 → throughput 유지.

## Q4. (Analyze)

Checksum offload에서 TX와 RX의 동작 차이는?

??? answer "정답 / 해설"
    - **TX**: SW가 checksum field를 0으로 채우고 보냄. HW가 TX 직전에 정확한 checksum 계산해 채움. → SW의 checksum 계산 비용 0.
    - **RX**: HW가 incoming packet의 checksum 검증 후 결과를 status flag(또는 별도 register)에 보고. SW는 그 flag만 확인 → SW의 검증 cycle 절약.

## Q5. (Evaluate)

다음 중 RSS 효과가 가장 큰 환경은?

- [ ] A. 단일 long-lived connection (file transfer)
- [ ] B. 다수 short-lived connection (web server)
- [ ] C. UDP only multicast
- [ ] D. RDMA RoCE

??? answer "정답 / 해설"
    **B**. 다수 connection이 다양한 5-tuple → hash 분포 다양 → multi-core scale 가능. A는 single tuple → 한 queue만 사용 → multi-core 활용 불가. C는 RSS 적용 가능하지만 multicast 특성상 제한적. D는 RDMA가 자체 mechanism.
