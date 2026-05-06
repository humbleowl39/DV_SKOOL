# Quiz — Module 01: Ethernet Fundamentals

[← Module 01 본문으로 돌아가기](../01_ethernet_fundamentals.md)

---

## Q1. (Remember)

Ethernet frame의 최소 / 최대 크기 (without preamble, with FCS)는?

??? answer "정답 / 해설"
    - **최소**: 64 bytes (DA 6 + SA 6 + Type 2 + Payload 46 + FCS 4 = 64)
    - **최대**: 1518 bytes (jumbo 미지원), 9018 bytes (jumbo, payload 9000)

## Q2. (Understand)

10GbE → 100GbE → 400GbE의 lane 수와 lane 속도는?

??? answer "정답 / 해설"
    - **10GbE**: 1 × 10G (NRZ)
    - **100GbE**: 4 × 25G (NRZ) 또는 2 × 50G (PAM4)
    - **400GbE**: 8 × 50G (PAM4) 또는 4 × 100G (PAM4)

## Q3. (Apply)

VLAN tag가 frame에 추가되면 길이는 어떻게 변하나?

??? answer "정답 / 해설"
    VLAN tag = **4 bytes**. Frame 길이 = 기본 + 4. 최대 1518 → 1522 (또는 jumbo 9022). MAC가 VLAN tag를 인식하지 못하면 잘못된 길이 해석 → drop.

## Q4. (Analyze)

Pause frame과 PFC의 차이는?

??? answer "정답 / 해설"
    - **Pause frame (802.3x)**: 모든 트래픽을 일괄 정지 — coarse, head-of-line blocking 발생
    - **PFC (802.1Qbb)**: 8개 priority 클래스별로 독립 pause — 우선순위 트래픽은 영향 없이 흐름

## Q5. (Evaluate)

Jumbo frame (9000+ bytes)의 trade-off는?

??? answer "정답 / 해설"
    **장점**: payload/overhead 비율 ↑ → throughput 효율 ↑ (특히 large file transfer).

    **단점**: latency variance ↑ (큰 frame 전송 중 작은 frame 대기), 모든 link에서 jumbo 지원 필요 (path 중간에 1500 limit이면 fragmentation 또는 drop), error 시 재전송 비용 ↑.
