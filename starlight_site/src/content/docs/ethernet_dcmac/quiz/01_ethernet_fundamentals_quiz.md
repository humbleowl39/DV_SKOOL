---
pagefind: false
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

## Q6. (Understand)

OSI 7 계층에서 DCMAC(Ethernet MAC + PHY)은 어느 계층(들)에 해당하며, 위쪽 인터페이스로 들어오는 payload는 어떻게 다뤄야 하나?

<details>
<summary>정답 / 해설</summary>

- **계층**: L2 (Data Link) + L1 (Physical). MAC 부분이 L2, PCS/PMA/PMD 가 L1.
- **payload 취급**: L3(IP)/L4(TCP)가 이미 캡슐화해 넘긴 **불투명한 바이트 덩어리** → scoreboard는 **byte-exact** 로만 비교, 내용을 IP/TCP로 해석하지 않는다.

**해설.** OSI 모델은 각 계층이 자기 역할만 책임지고 바로 위·아래 계층과만 대화하는 관심사의 분리를 핵심으로 한다. 캡슐화(encapsulation) 과정에서 데이터는 송신 시 7계층을 아래로 내려가며 각 계층의 헤더를 덧붙이는데, DCMAC의 AXI-Stream으로 들어오는 payload에는 이미 L4 TCP 헤더와 L3 IP 헤더가 다 붙어 있다. DCMAC(L2)은 그 바깥에 Ethernet 헤더(DA/SA/Type)와 FCS만 두르고, L1에서 bit stream으로 내보낸다. 따라서 검증에서 payload 내부의 IP checksum 같은 상위 계층 무결성은 DCMAC의 책임 밖이며, 이 경계를 흐리면 검증 범위가 무한히 번진다. 디버그 시에도 "항상 L1부터 위로" 원칙에 따라 lane lock(L1) → frame 무결성/CRC(L2) 순으로 격리한다.

</details>

## Q7. (Analyze)

현대 switched/full-duplex Ethernet에서도 CSMA/CD가 충돌을 감지하며, 데이터센터에서 PFC가 "필수"인 이유는 단지 Pause frame보다 세밀하기 때문이다 — 이 두 진술을 각각 평가하라.

<details>
<summary>정답 / 해설</summary>

- **CSMA/CD 진술**: 틀림. 1992년 full-duplex와 switch 도입으로 충돌 자체가 사라져 현대 Ethernet에 CSMA/CD는 사실상 없다. 64-byte 최소 frame 등 일부 규칙만 호환성 유물로 남았다.
- **PFC 진술**: 불완전/틀림. PFC가 데이터센터 필수인 진짜 이유는 **RoCE(RDMA over Converged Ethernet)의 무손실 요구**다.

**해설.** Ethernet은 1973년 Metcalfe의 CSMA/CD(공유 매체에서 충돌을 감지·재전송)로 시작했지만, full-duplex와 switch가 등장하면서 각 링크가 점대점 전이중이 되어 충돌이 원천적으로 사라졌다. 그래서 현대 Ethernet은 "이름만 같은 다른 프로토콜"에 가깝다. PFC(802.1Qbb)는 단순히 Pause frame(802.3x)을 priority별로 쪼갠 개선이 아니라, east-west 트래픽 폭증으로 도입된 RDMA가 Ethernet 위 RoCE로 정착하면서 loss-sensitive한 RoCE 트래픽에 lossless를 보장해야 했기 때문에 PFC+ECN이 구조적 전제 조건이 된 것이다. Pause frame은 포트 전체를 멈춰 head-of-line blocking을 일으키므로, RoCE만 보호하고 best-effort는 흐르게 하려면 priority별 PFC가 필요하다. DCMAC이 PFC를 정확히 구현·검증해야 하는 동기가 바로 이 데이터센터 무손실 네트워크 요구다.

</details>
