---
pagefind: false
title: "Quiz — Module 03: TOE Key Functions"
---

[← Module 03 본문으로 돌아가기](../../03_toe_key_functions/)

---

## Q1. (Remember)

TSO와 LRO의 차이는?

<details>
<summary>정답 / 해설</summary>

- **TSO (TCP Segmentation Offload)**: TX side. SW의 큰 buffer를 HW가 MTU 단위로 분할.
- **LRO (Large Receive Offload)**: RX side. HW가 연속 segment를 합쳐 SW에 한 번에 전달.

TSO와 LRO는 각각 송신·수신 방향에서 SW와 HW 사이의 데이터 단위 불일치를 해결한다. SW는 64 KB짜리 버퍼를 한 번에 넘기고 싶어 하지만 네트워크는 MTU(보통 1500 B) 단위로 패킷을 실어나른다. TSO는 이 "크게 보내고 싶은" 쪽의 요구를 HW에서 처리해 분할 비용을 줄이고, LRO는 반대로 "작은 조각을 합쳐서 한 번만 SW를 깨우고 싶은" 수신 측 요구를 해결한다. 이름에서 Segmentation(분할)과 Offload(위임), Large Receive(큰 수신 단위)라는 역할이 명확히 드러난다.

</details>
## Q2. (Understand)

RSS의 indirection table은 무엇인가?

<details>
<summary>정답 / 해설</summary>

5-tuple hash → queue 매핑 table. Hash 결과의 LSB N bit를 indirection table 인덱스로 사용해 target queue 결정. SW가 queue 구성을 변경할 때 hash 알고리즘 변경 없이 indirection table만 업데이트.

Indirection table이 필요한 이유는 hash 공간(2^N)과 실제 CPU 코어 수가 일치하지 않기 때문이다. 예를 들어 8비트 hash라면 256개 버킷이 생기지만 코어는 16개일 수 있다. Indirection table은 이 256개 버킷을 16개 큐에 어떻게 분배할지 SW가 제어하는 레이어다. 덕분에 특정 코어가 과부하일 때 해당 큐에 연결된 버킷 수를 줄이는 방식으로 HW hash 알고리즘 변경 없이 로드 밸런싱을 조정할 수 있다.

</details>
## Q3. (Apply)

Fast retransmit이 trigger되는 조건은?

<details>
<summary>정답 / 해설</summary>

**3개의 duplicate ACK 수신**. 같은 ACK number를 3번 받으면 receiver가 그 다음 segment를 못 받았다는 신호 → RTO 만료 기다리지 않고 즉시 재전송. RTO보다 빠른 복구 → throughput 유지.

Receiver는 순서에 맞지 않는 segment가 와도 이미 받은 마지막 연속 sequence까지만 ACK를 보낸다. Sender 입장에서는 같은 ACK가 반복된다는 것이 "그 ACK 이후 segment가 hole로 남아 있다"는 암묵적 신호다. 3번이라는 임계값은 단순 재정렬(reordering)로 인한 오탐을 막기 위한 경험적 기준이며, 이 조건이 충족되는 순간 RTO가 만료될 때까지 기다리지 않고 즉시 재전송하므로 긴 타임아웃 페널티 없이 빠르게 손실을 복구한다.

</details>
## Q4. (Analyze)

Checksum offload에서 TX와 RX의 동작 차이는?

<details>
<summary>정답 / 해설</summary>

- **TX**: SW가 checksum field를 0으로 채우고 보냄. HW가 TX 직전에 정확한 checksum 계산해 채움. → SW의 checksum 계산 비용 0.
- **RX**: HW가 incoming packet의 checksum 검증 후 결과를 status flag(또는 별도 register)에 보고. SW는 그 flag만 확인 → SW의 검증 cycle 절약.

TX와 RX에서 역할이 반전되는 이유를 이해하면 헷갈리지 않는다. TX는 데이터가 아직 메모리에 있고 실제 값을 알고 있는 HW가 wire로 내보내기 직전 한 번만 계산하면 된다. 반면 RX는 이미 wire를 통해 도착한 패킷이므로 HW가 전체를 스캔해 계산한 뒤, "정상/손상" 두 가지 결과를 flag 하나로 압축해 SW에 전달한다. SW는 수천 바이트를 다시 읽어 재계산할 필요 없이 flag 하나만 확인하면 되므로 CPU 사이클이 크게 줄어든다.

</details>
## Q5. (Evaluate)

다음 중 RSS 효과가 가장 큰 환경은?

- [ ] A. 단일 long-lived connection (file transfer)
- [ ] B. 다수 short-lived connection (web server)
- [ ] C. UDP only multicast
- [ ] D. RDMA RoCE

<details>
<summary>정답 / 해설</summary>

**B**. 다수 connection이 다양한 5-tuple → hash 분포 다양 → multi-core scale 가능. A는 single tuple → 한 queue만 사용 → multi-core 활용 불가. C는 RSS 적용 가능하지만 multicast 특성상 제한적. D는 RDMA가 자체 mechanism.

RSS의 가치는 서로 다른 5-tuple이 얼마나 다양하게 분포하느냐에 달려 있다. 웹 서버(B)는 수천 클라이언트가 제각각 다른 source port를 사용하므로 hash 결과가 고르게 퍼지고 모든 CPU 코어가 바쁘게 일한다. 반면 단일 파일 전송(A)은 처음부터 끝까지 동일한 4-tuple을 사용하므로 hash 결과가 항상 같은 큐로 향하고, 나머지 코어는 놀고 있다. C(UDP multicast)는 목적지가 동일한 그룹 주소여서 source 다양성이 부족하고, D(RoCE)는 RDMA 자체 Queue Pair 메커니즘으로 분산을 처리하므로 RSS 혜택이 제한적이다.

</details>
