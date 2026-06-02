---
title: "Quiz — Module 01: Ethernet Fundamentals"
---

[← Module 01 본문으로 돌아가기](../../01_ethernet_fundamentals/)

---

## Q1. (Remember)

Ethernet frame의 최소 / 최대 크기 (without preamble, with FCS)는?

<details>
<summary>정답 / 해설</summary>

- **최소**: 64 bytes (DA 6 + SA 6 + Type 2 + Payload 46 + FCS 4 = 64)
- **최대**: 1518 bytes (jumbo 미지원), 9018 bytes (jumbo, payload 9000)

**해설.** Ethernet 표준은 최소 프레임을 64 bytes로 규정한다. 이는 CSMA/CD 충돌 감지가 의미 있으려면 프레임이 wire를 채우는 시간이 최소한 왕복 지연(round-trip delay)을 커버해야 한다는 물리적 요구에서 비롯된 제약이다. Payload가 46 bytes 미만이면 PAD 필드로 채워 최소 길이를 맞춘다. 최대 1518 bytes는 표준 Ethernet의 제한이며, jumbo frame은 이를 9018 bytes(payload 9000 bytes + 헤더/FCS)까지 확장한다. 오답 후보로 "1500 bytes"를 고르는 경우가 있는데, 1500 bytes는 payload의 최대 크기(MTU)이고 FCS 4 bytes가 더해져야 비로소 표준 최대 프레임 크기가 된다는 점에 유의해야 한다.

</details>
## Q2. (Understand)

10GbE → 100GbE → 400GbE의 lane 수와 lane 속도는?

<details>
<summary>정답 / 해설</summary>

- **10GbE**: 1 × 10G (NRZ)
- **100GbE**: 4 × 25G (NRZ) 또는 2 × 50G (PAM4)
- **400GbE**: 8 × 50G (PAM4) 또는 4 × 100G (PAM4)

**해설.** 속도를 높이는 방법은 "lane 수를 늘리거나, lane당 속도를 높이거나" 두 가지다. NRZ는 bit당 1개의 신호 레벨을 사용하므로 lane당 최대 25G 수준이 실용 한계다. PAM4는 신호 레벨을 4개로 늘려 한 번에 2 bit를 실어 같은 물리적 채널로 50G 또는 100G/lane을 달성한다. 즉 400GbE를 8×50G로 구성하면 lane이 많아 배선이 복잡해지는 반면, 4×100G로 구성하면 lane이 절반이지만 PAM4 수신기 설계가 훨씬 까다롭다. "400GbE = 16 lane"이라고 답하는 오류는 100G 인터페이스 기준을 잘못 적용한 것이다.

</details>
## Q3. (Apply)

VLAN tag가 frame에 추가되면 길이는 어떻게 변하나?

<details>
<summary>정답 / 해설</summary>

VLAN tag = **4 bytes**. Frame 길이 = 기본 + 4. 최대 1518 → 1522 (또는 jumbo 9022). MAC가 VLAN tag를 인식하지 못하면 잘못된 길이 해석 → drop.

**해설.** VLAN tag(802.1Q)는 EtherType 앞에 삽입되는 4 byte 필드(TPID 2 bytes + TCI 2 bytes)로, 이것이 추가되면 프레임 전체 길이가 정확히 4 bytes 늘어난다. 이 사실이 중요한 이유는 VLAN을 인식하지 못하는 legacy MAC은 EtherType 위치가 4 bytes 밀렸다고 생각해 올바른 타입 해석에 실패하고 결국 프레임을 drop할 수 있기 때문이다. 검증 관점에서 "VLAN tag 있는 프레임"과 "없는 프레임"을 모두 통과시켜야 하며, 특히 1518 byte 경계 근처 프레임에서 tag 추가 후 1522 byte가 올바르게 허용되는지 확인해야 한다.

</details>
## Q4. (Analyze)

Pause frame과 PFC의 차이는?

<details>
<summary>정답 / 해설</summary>

- **Pause frame (802.3x)**: 모든 트래픽을 일괄 정지 — coarse, head-of-line blocking 발생
- **PFC (802.1Qbb)**: 8개 priority 클래스별로 독립 pause — 우선순위 트래픽은 영향 없이 흐름

**해설.** Pause frame은 "지금 멈춰"라는 단 하나의 신호를 보내기 때문에 지연 허용 불가 트래픽과 best-effort 트래픽이 섞인 환경에서는 latency-sensitive 트래픽까지 불필요하게 묶어버리는 head-of-line blocking 문제가 생긴다. PFC는 802.1Q의 8개 priority 클래스(CoS 0~7) 각각에 대해 독립적으로 pause 여부를 결정할 수 있어, 예를 들어 RoCE(RDMA over Converged Ethernet)와 같이 lossless가 필수인 트래픽만 pause하고 나머지는 흐르게 둘 수 있다. "PFC는 더 복잡하므로 항상 더 좋다"는 오해가 있는데, 단일 클래스 단순 환경에서는 Pause frame이 구현 비용이 낮아 적합한 선택일 수 있다.

</details>
## Q5. (Evaluate)

Jumbo frame (9000+ bytes)의 trade-off는?

<details>
<summary>정답 / 해설</summary>

**장점**: payload/overhead 비율 ↑ → throughput 효율 ↑ (특히 large file transfer).

**단점**: latency variance ↑ (큰 frame 전송 중 작은 frame 대기), 모든 link에서 jumbo 지원 필요 (path 중간에 1500 limit이면 fragmentation 또는 drop), error 시 재전송 비용 ↑.

**해설.** Jumbo frame의 핵심 장점은 같은 데이터를 전송할 때 필요한 프레임 수가 줄어들어 헤더/FCS 오버헤드 비율이 낮아지고 CPU 인터럽트 횟수도 감소한다는 것이다. 그러나 9000 byte 프레임이 전송되는 동안 같은 port를 쓰는 다른 소형 프레임은 그 시간 동안 대기해야 하므로 latency variance가 커진다. 가장 흔한 운영 실수는 end-to-end 경로의 모든 장비(스위치 포함)에서 jumbo를 활성화하지 않아 중간 노드에서 IP fragmentation이나 silently drop이 발생하는 경우다. 검증 환경에서는 9000 byte 경계 바로 아래와 위(8999, 9000, 9001 bytes)를 반드시 테스트해야 한다.

</details>
