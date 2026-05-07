# Quiz — Module 02: 3-Layer Architecture

[← Module 02 본문으로 돌아가기](../02_layer_architecture.md)

---

## Q1. (Remember)

PCIe 의 3 layer 와 각 layer 의 packet 단위를 매칭하라.

??? answer "정답 / 해설"
    | Layer | Packet |
    |-------|--------|
    | Transaction | TLP |
    | Data Link | DLLP |
    | Physical | Ordered Set + Symbol |

## Q2. (Understand)

LCRC 와 ECRC 의 차이를 한 줄로 설명하라.

??? answer "정답 / 해설"
    - **LCRC** (Link CRC, 32-bit): Data Link Layer, **link-by-link** (hop) 무결성. 각 router/switch 가 검증/재계산.
    - **ECRC** (End-to-End CRC, 32-bit): Transaction Layer, **end-to-end** 무결성. 라우팅 노드를 통과해도 변경 안 됨, optional.

## Q3. (Apply)

Packet trace 에서 LCRC error 가 빈번하게 보인다. 어느 layer 의 문제로 의심해야 하는가?

??? answer "정답 / 해설"
    **PHY layer (signal integrity)**.

    LCRC fail 의 원인은 packet 의 비트가 잘못 도달한 것 → PHY 의 BER 이 높음. 의심 포인트:

    1. EQ 가 채널에 안 맞음 (Recovery 자주 빠짐)
    2. PCB 손상 / 연결 불량
    3. Power noise
    4. 온도 변화

    DLL 자체의 버그라기보다는 PHY 의 BER 이 거의 항상 원인.

## Q4. (Analyze)

송신 path 에서 layer 마다 추가되는 wrapper 를 순서대로 분석하라 (memory write 예).

??? answer "정답 / 해설"
    1. **Application** : memory write 요청 (host PA, len, data)
    2. **TL** : MWr TLP 생성 (header + payload), optional ECRC 추가
    3. **DLL** : Sequence Number 부여 + LCRC 계산해 [Seq# + TLP + LCRC] 형식으로 wrap, Replay Buffer 에 저장
    4. **PL** : Framing (STP/END token) + Scrambling + Encoding (128b/130b 등) + Lane stripe + SerDes → wire

    수신 path 는 역순.

## Q5. (Evaluate)

"PCIe 의 reliability 는 PHY 가 BER 낮으니까 보장된다" 는 주장을 평가하라.

??? answer "정답 / 해설"
    **부적절**.

    - PHY 의 BER 은 0 이 아님 (e.g. 1e-12 정도).
    - Packet-level reliability 는 **DLL 의 ACK/NAK + Replay Buffer + Sequence Number** 가 보장.
    - PHY 가 단일 비트를 잘못 전달해도 LCRC 검증 fail → NAK → 재송신 → 정상.

    즉 reliability 는 layer 분담:
    - PHY = "raw bit 운반, BER 가능한 한 낮게"
    - DLL = "비트 오류 발생 시 재송신으로 packet 단위 신뢰성 보장"
    - TL = "transaction (request → completion) 단위의 timeout / 처리"

    "PHY 의 BER" 만으로 PCIe reliability 를 평가하는 것은 layer 분담을 무시하는 것.
