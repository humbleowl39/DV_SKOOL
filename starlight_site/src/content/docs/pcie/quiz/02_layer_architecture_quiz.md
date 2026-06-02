---
title: "Quiz — Module 02: 3-Layer Architecture"
---

[← Module 02 본문으로 돌아가기](../../02_layer_architecture/)

---

## Q1. (Remember)

PCIe 의 3 layer 와 각 layer 의 packet 단위를 매칭하라.

<details>
<summary>정답 / 해설</summary>

| Layer | Packet |
|-------|--------|
| Transaction | TLP |
| Data Link | DLLP |
| Physical | Ordered Set + Symbol |

각 계층은 독립적인 역할을 담당하며 고유한 패킷 단위를 가진다. Transaction Layer 는 요청과 응답(TLP)을, Data Link Layer 는 신뢰성 제어(DLLP)를, Physical Layer 는 bit 수준의 동기화(Ordered Set)와 인코딩된 심볼을 다룬다. 이 매칭을 외울 때는 "계층의 목적 = 패킷의 목적"으로 연결하면 기억하기 쉽다.

</details>
## Q2. (Understand)

LCRC 와 ECRC 의 차이를 한 줄로 설명하라.

<details>
<summary>정답 / 해설</summary>

- **LCRC** (Link CRC, 32-bit): Data Link Layer, **link-by-link** (hop) 무결성. 각 router/switch 가 검증/재계산.
- **ECRC** (End-to-End CRC, 32-bit): Transaction Layer, **end-to-end** 무결성. 라우팅 노드를 통과해도 변경 안 됨, optional.

LCRC 는 한 hop 을 건널 때마다 수신 측이 검증하고 재계산하므로, Switch 를 여러 개 경유하면 그만큼 여러 번 검증된다. 반면 ECRC 는 TLP 를 처음 생성한 쪽에서 계산하고 최종 목적지에서만 검증하기 때문에 중간 라우팅 노드의 silent corruption 을 잡아낼 수 있다. ECRC 가 optional 인 이유는 LCRC 가 이미 hop 단위 보호를 제공하기 때문이고, 높은 신뢰성이 요구되는 환경에서 추가적으로 활성화한다.

</details>
## Q3. (Apply)

Packet trace 에서 LCRC error 가 빈번하게 보인다. 어느 layer 의 문제로 의심해야 하는가?

<details>
<summary>정답 / 해설</summary>

**PHY layer (signal integrity)**.

LCRC fail 의 원인은 packet 의 비트가 잘못 도달한 것 → PHY 의 BER 이 높음. 의심 포인트:

1. EQ 가 채널에 안 맞음 (Recovery 자주 빠짐)
2. PCB 손상 / 연결 불량
3. Power noise
4. 온도 변화

DLL 자체의 버그라기보다는 PHY 의 BER 이 거의 항상 원인.

LCRC 오류는 "패킷이 도중에 변조되었다"는 증거다. DLL 이 패킷을 잘못 구성했을 가능성은 매우 낮으며, 실제로는 PHY 가 비트를 잘못 전달했을 때 CRC 불일치가 발생한다. 따라서 빈번한 LCRC 실패는 PHY 계층의 BER 악화 신호로 해석하고, DLL 이나 TLP 포맷 버그를 의심하기 전에 채널 품질과 EQ 상태를 먼저 점검해야 한다.

</details>
## Q4. (Analyze)

송신 path 에서 layer 마다 추가되는 wrapper 를 순서대로 분석하라 (memory write 예).

<details>
<summary>정답 / 해설</summary>

1. **Application** : memory write 요청 (host PA, len, data)
2. **TL** : MWr TLP 생성 (header + payload), optional ECRC 추가
3. **DLL** : Sequence Number 부여 + LCRC 계산해 [Seq# + TLP + LCRC] 형식으로 wrap, Replay Buffer 에 저장
4. **PL** : Framing (STP/END token) + Scrambling + Encoding (128b/130b 등) + Lane stripe + SerDes → wire

수신 path 는 역순.

각 계층은 "자기 책임의 헤더/트레일러"만 추가한다는 원칙을 기억하면 순서를 쉽게 재구성할 수 있다. TL 은 요청 의미(무엇을, 어디에)를 담은 TLP header 를 만들고, DLL 은 재전송을 위한 Sequence # 와 무결성 검증을 위한 LCRC 를 붙이며, PHY 는 그 전체 비트열을 채널에 올릴 수 있는 형태로 변환한다. 수신 측은 이 과정을 정확히 역순으로 벗겨나간다.

</details>
## Q5. (Evaluate)

"PCIe 의 reliability 는 PHY 가 BER 낮으니까 보장된다" 는 주장을 평가하라.

<details>
<summary>정답 / 해설</summary>

**부적절**.

- PHY 의 BER 은 0 이 아님 (e.g. 1e-12 정도).
- Packet-level reliability 는 **DLL 의 ACK/NAK + Replay Buffer + Sequence Number** 가 보장.
- PHY 가 단일 비트를 잘못 전달해도 LCRC 검증 fail → NAK → 재송신 → 정상.

즉 reliability 는 layer 분담:
- PHY = "raw bit 운반, BER 가능한 한 낮게"
- DLL = "비트 오류 발생 시 재송신으로 packet 단위 신뢰성 보장"
- TL = "transaction (request → completion) 단위의 timeout / 처리"

"PHY 의 BER" 만으로 PCIe reliability 를 평가하는 것은 layer 분담을 무시하는 것.

PHY 는 비트 오류를 "줄이는" 역할이지 "없애는" 역할이 아니다. PCIe 의 신뢰성이 실제로 보장되는 이유는 DLL 이 LCRC 오류를 감지하면 NAK 를 보내고 Replay Buffer 에서 해당 TLP 를 재전송하기 때문이다. PHY BER 이 낮을수록 재전송 빈도가 줄어 성능이 좋아지는 것이지, PHY 가 신뢰성 그 자체를 보장하는 구조가 아니라는 점이 이 평가 문항의 핵심이다.

</details>
