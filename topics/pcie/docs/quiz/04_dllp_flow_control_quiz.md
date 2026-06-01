# Quiz — Module 04: DLLP, Flow Control, ACK/NAK

[← Module 04 본문으로 돌아가기](../04_dllp_flow_control.md)

---

## Q1. (Remember)

DLLP 의 5 가지 type 을 들어라.

??? answer "정답 / 해설"
    1. **ACK** — 누적 sequence number 까지 OK 받음.
    2. **NAK** — 그 sequence number 부터 재송 요청.
    3. **InitFC1 / InitFC2** — Flow Control initialization.
    4. **UpdateFC** — Flow Control credit 갱신.
    5. **PM_xxx** — Power Management 관련 (Enter L1, Request_Ack, ...).
    6. (추가) **Vendor Specific**.

    DLLP 는 TLP 를 실어나르는 DLL 이 자신의 임무(신뢰성 보장, 흐름 제어, 전원 관리)를 수행하기 위해 사용하는 제어 패킷이다. ACK/NAK 은 신뢰성, InitFC/UpdateFC 는 흐름 제어, PM_xxx 는 전원 상태 협상이라는 세 축으로 묶어 기억하면 5가지를 자연스럽게 도출할 수 있다. Vendor Specific 은 보너스이며, 시험에서는 이 세 가지 축의 DLLP 를 묻는 것이 핵심이다.

## Q2. (Understand)

ACK 와 FC Update 의 차이는?

??? answer "정답 / 해설"
    - **ACK**: "이 Sequence Number 까지 LCRC 검증 OK 로 받았다" — DLL의 packet integrity 보고.
    - **FC Update**: "RX buffer 에서 이만큼 비웠다, 이 만큼 더 보내도 된다" — TL 의 buffer occupancy 보고.

    하나는 신뢰성, 다른 하나는 backpressure. 둘 다 receiver → sender 방향 DLLP 라 헷갈리지만 별개 메커니즘.

    ACK 가 "패킷이 망가지지 않고 도달했는가"를 묻는다면, FC Update 는 "상대방 버퍼에 공간이 있어 패킷을 더 받을 수 있는가"를 알려주는 것이다. 두 메커니즘은 목적이 다르기 때문에 독립적으로 동작하며, ACK 를 받았더라도 FC credit 이 없으면 다음 TLP 를 보낼 수 없다. 둘 다 receiver → sender 방향이라 같은 것처럼 보이지만, 근본적으로 해결하는 문제가 다르다는 점을 구분하는 것이 이 문항의 요점이다.

## Q3. (Apply)

Sender 의 FC credit: PH = 4, PD = 16. 다음 packet 송신 가능 여부를 판정하라.

a) MWr header (1 PH) + payload 32 byte (= 8 DW = 2 PD)
b) 그 직후 MWr header (1 PH) + payload 64 byte (= 16 DW = 4 PD)

??? answer "정답 / 해설"
    a) 송신 후 used_PH = 1, used_PD = 2. (PH=4, PD=16 한도 안 → OK)
    b) 송신 시도: used_PH 가 1+1=2 (≤ 4 OK), used_PD 가 2+4=6 (≤ 16 OK) → **송신 가능**.

    송신이 거부될 시점은 used_PH 가 4 도달 또는 used_PD 가 16 도달 시. UpdateFC 받으면 used 카운터가 감소.

    FC credit 은 Header 와 Data 두 가지를 동시에 만족해야 송신이 허용된다. 어느 한 쪽이라도 부족하면 해당 TLP 는 대기 상태가 된다. 이 문제처럼 연속 두 TLP 를 보내는 상황에서는 a) 송신 후 남은 크레딧에 b) 를 더해 계산하는 것이 핵심이다. UpdateFC 를 받으면 used 카운터가 줄어들어 크레딧이 회복되므로, 결국 흐름 제어는 버퍼 점유 상태를 실시간으로 알려주는 시스템이다.

## Q4. (Analyze)

Replay Buffer 가 작은 시스템에서 RTT 가 큰 link (long board / retimer) 가 사용되면 어떤 부작용이 생기는가?

??? answer "정답 / 해설"
    - Sender 가 송신 후 ACK 받기까지 RTT 만큼 buffer 점유.
    - RTT 가 크면 in-flight TLP 갯수가 커지고, Replay Buffer 의 size 가 그 한도에 도달 → sender 가 더 이상 송신 못 함 (stall).
    - 결과: throughput 의 cap 발생, link 의 raw bandwidth 미활용.

    해결: Replay Buffer 를 larger silicon area 로 늘리거나 (cost), 또는 ACK Coalescing factor 줄여 ACK 가 자주 와 buffer retire 빠르게.

    Replay Buffer 는 ACK 를 받기 전까지 재전송을 위해 모든 in-flight TLP 를 보관해야 한다. RTT 가 길면 ACK 가 돌아오기 전에 더 많은 TLP 가 공중에 떠 있으므로, Replay Buffer 가 꽉 차는 순간 sender 는 전송을 멈춰야 한다. 이것이 long-board 나 retimer 삽입 환경에서 성능이 예상보다 낮게 나오는 근본 이유이며, 설계 단계에서 "Replay Buffer ≥ RTT × 링크 대역폭"을 만족하는지 검토하는 것이 핵심이다.

## Q5. (Evaluate)

Gen6 의 FLIT mode 가 Gen5 이하의 ACK/NAK 메커니즘을 어떻게 단순화/개선하는지 평가하라.

??? answer "정답 / 해설"
    **개선점**:

    1. **고정 256-byte 프레임** → framing token (STP/END/SDP/EDS) 불필요, 디코딩 단순.
    2. **FLIT 단위 통합 ACK/NAK** → 매 frame 단위 ACK 가능, 늦은 ACK 으로 인한 Replay Buffer 부담 감소.
    3. **FEC 통합** → PAM4 의 BER 증가를 보완, single-bit 정정 가능 → NAK 발생 빈도 감소.
    4. **TLP/DLLP 가 같은 FLIT 안에** → packet boundary 처리 단순.

    **Trade-off**:
    - 검증 도구가 FLIT-aware 로 갱신 필요 (기존 packet trace 도구 호환 안 됨).
    - 짧은 메시지 1 개 보내려고 256-byte FLIT 차지 → 작은 traffic 의 효율은 NRZ 시대보다 낮을 수도.
    - Gen5 이하 backward compat 모드도 spec 에 정의되어 있지만 deprecated 방향.

    Gen5 이하에서는 TLP 마다 STP/END 토큰을 붙여 경계를 표시하고 ACK 가 여러 TLP 를 코얼레스(coalesce)해 늦게 올 수 있었다. Gen6 FLIT mode 는 이 모든 것을 256 byte 고정 프레임으로 통일해 경계 계산을 없앤다. FEC 가 PAM4 의 높아진 BER 을 하드웨어 수준에서 먼저 보정하므로 NAK → 재전송 빈도가 줄고, Replay Buffer 부담도 자연스럽게 감소한다. 반면 단순 쓰기 하나를 보내도 256 byte 프레임을 소비하므로 소량 트래픽 환경에서는 효율이 떨어지는 것이 trade-off 다.
