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

## Q2. (Understand)

ACK 와 FC Update 의 차이는?

??? answer "정답 / 해설"
    - **ACK**: "이 Sequence Number 까지 LCRC 검증 OK 로 받았다" — DLL의 packet integrity 보고.
    - **FC Update**: "RX buffer 에서 이만큼 비웠다, 이 만큼 더 보내도 된다" — TL 의 buffer occupancy 보고.

    하나는 신뢰성, 다른 하나는 backpressure. 둘 다 receiver → sender 방향 DLLP 라 헷갈리지만 별개 메커니즘.

## Q3. (Apply)

Sender 의 FC credit: PH = 4, PD = 16. 다음 packet 송신 가능 여부를 판정하라.

a) MWr header (1 PH) + payload 32 byte (= 8 DW = 2 PD)
b) 그 직후 MWr header (1 PH) + payload 64 byte (= 16 DW = 4 PD)

??? answer "정답 / 해설"
    a) 송신 후 used_PH = 1, used_PD = 2. (PH=4, PD=16 한도 안 → OK)
    b) 송신 시도: used_PH 가 1+1=2 (≤ 4 OK), used_PD 가 2+4=6 (≤ 16 OK) → **송신 가능**.

    송신이 거부될 시점은 used_PH 가 4 도달 또는 used_PD 가 16 도달 시. UpdateFC 받으면 used 카운터가 감소.

## Q4. (Analyze)

Replay Buffer 가 작은 시스템에서 RTT 가 큰 link (long board / retimer) 가 사용되면 어떤 부작용이 생기는가?

??? answer "정답 / 해설"
    - Sender 가 송신 후 ACK 받기까지 RTT 만큼 buffer 점유.
    - RTT 가 크면 in-flight TLP 갯수가 커지고, Replay Buffer 의 size 가 그 한도에 도달 → sender 가 더 이상 송신 못 함 (stall).
    - 결과: throughput 의 cap 발생, link 의 raw bandwidth 미활용.

    해결: Replay Buffer 를 larger silicon area 로 늘리거나 (cost), 또는 ACK Coalescing factor 줄여 ACK 가 자주 와 buffer retire 빠르게.

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
