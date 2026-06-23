---
pagefind: false
title: "Quiz — Module 05: TOE Quick Reference"
---

[← Module 05 본문으로 돌아가기](../../05_quick_reference_card/)

---

## Q1. (Recall)

TCP 3-way handshake와 4-way close 흐름을 sequence로 답하세요.

<details>
<summary>정답 / 해설</summary>

**3-way open**: SYN → SYN/ACK → ACK
**4-way close**: FIN → ACK → FIN → ACK

Active close 측은 TIME_WAIT 상태로 2 × MSL (Maximum Segment Lifetime) 대기.

3-way handshake는 양쪽이 서로의 초기 sequence number(ISN)를 확인하는 최소한의 왕복 횟수다. 2-way로는 한쪽의 ISN 확인을 보장할 수 없어 3번이 최소치가 된다. 4-way close에서 FIN과 ACK가 분리되는 이유는 Passive close 측이 FIN을 받은 순간 아직 보낼 데이터가 남아 있을 수 있기 때문이다. ACK를 먼저 보내 "받았음"을 알린 뒤, 자기 데이터를 모두 보내고 나서야 자신의 FIN을 보내는 2단계 구조가 필요하다. TIME_WAIT 2×MSL 대기는 마지막 ACK가 유실돼 재전송된 FIN에 응답할 수 있도록 여유를 두는 것이다.

</details>
## Q2. (Recall)

5-tuple은 어떤 필드들로 구성되나?

<details>
<summary>정답 / 해설</summary>

**Source IP + Source Port + Destination IP + Destination Port + Protocol**. RSS hash, connection table key 등에 사용.

5-tuple은 인터넷상에서 하나의 transport 세션을 유일하게 식별하는 최소 필드 집합이다. IP 주소만으로는 한 호스트의 여러 프로세스를 구분할 수 없어 port가 추가되고, 같은 IP:Port 쌍이 TCP와 UDP로 동시에 열릴 수 있어 Protocol 필드가 더해진다. TOE connection table 조회, RSS의 큐 결정, 방화벽 세션 추적 모두 이 5-tuple을 키로 사용한다.

</details>
## Q3. (Apply)

MTU=1500일 때 TCP MSS는?

<details>
<summary>정답 / 해설</summary>

MSS = MTU - IP header (20) - TCP header (20) = **1460 bytes**. (옵션이 있으면 더 작아짐, e.g., timestamp option 12 bytes → MSS=1448).

MTU는 Ethernet frame의 payload 한도이고, IP와 TCP 헤더는 각각 기본 20 바이트를 고정적으로 차지한다. TSO를 설계할 때 HW가 대용량 버퍼를 분할하는 단위가 바로 이 MSS다. TCP timestamp option이 협상되면 옵션이 12 바이트 추가되어 MSS가 1448로 줄어드는데, 이처럼 MSS는 3-way handshake에서 양쪽이 협상하는 값이지 MTU에서 단순히 빼는 상수가 아니라는 점에 주의해야 한다.

</details>
## Q4. (Apply)

LRO를 적용 시 latency-sensitive 워크로드에 미치는 영향은?

<details>
<summary>정답 / 해설</summary>

LRO는 다수 segment를 합쳐서 SW로 한 번에 전달 → **latency 증가** (첫 segment가 다음 segment 대기). Throughput에는 유리하지만 RPC, real-time 워크로드는 LRO disable 권장.

LRO의 latency 증가 메커니즘을 직관적으로 이해하면, 첫 번째 segment가 도착해도 HW가 "다음 segment가 올 때까지 기다렸다가 합쳐서 올리자"고 판단하는 순간 이미 지연이 발생한다. Bulk 파일 전송처럼 어차피 많은 양의 데이터를 받아야 하는 경우에는 인터럽트 수를 줄여 CPU 효율이 올라가는 이점이 크다. 반면 RPC나 실시간 스트리밍처럼 작은 메시지에 즉각 반응해야 하는 워크로드는 수 마이크로초의 대기조차 응답 시간 목표를 위반할 수 있어 LRO를 끄는 것이 맞다.

</details>
## Q5. (Evaluate)

다음 중 Production NIC silicon에 가장 위험한 결함은?

- [ ] A. Throughput 5% 저하
- [ ] B. Connection table SRAM ECC 미적용
- [ ] C. RTO 10% 더 길게
- [ ] D. RSS distribution 약간 비균등

<details>
<summary>정답 / 해설</summary>

**B**. ECC 없이 SRAM bit flip → connection state corruption → silent data integrity 사고. Production data center에서 cosmic ray + 시간 = inevitable. 검증보다 ECC 적용이 mitigation. A/C/D는 성능 영향이지만 silent 아님.

"가장 위험한" 결함의 기준은 발생 사실을 모른 채 데이터 무결성이 침해되는가 여부다. ECC 미적용 SRAM은 우주 방사선이나 전압 글리치로 비트가 뒤집혀도 HW는 아무런 오류를 보고하지 않고 잘못된 state로 계속 동작한다. 데이터센터 규모에서 수만 개의 NIC가 수 개월을 운영되면 이런 사건은 통계적으로 피할 수 없다. 반면 A(throughput 저하)·C(RTO 지연)·D(RSS 불균등)는 모두 성능 지표로 측정되고 알림이 뜨므로 "silent"하지 않다. 따라서 ECC 미적용이 silicon 단계에서 반드시 수정해야 할 결함으로 분류된다.

</details>
