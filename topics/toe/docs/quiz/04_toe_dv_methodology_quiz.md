# Quiz — Module 04: TOE DV Methodology

[← Module 04 본문으로 돌아가기](../04_toe_dv_methodology.md)

---

## Q1. (Remember)

TCP state machine의 11 state를 나열하세요.

??? answer "정답 / 해설"
    CLOSED, LISTEN, SYN_SENT, SYN_RCVD, ESTABLISHED, FIN_WAIT_1, FIN_WAIT_2, CLOSE_WAIT, CLOSING, LAST_ACK, TIME_WAIT.

    + (active vs passive open 분기, FIN 처리 분기로 구성).

## Q2. (Understand)

State coverage가 중요한 이유는?

??? answer "정답 / 해설"
    각 state에서 받을 수 있는 segment 종류 + state transition이 다름. 한 state라도 누락하면 그 transition 경로의 버그 catch 불가. 특히 TIME_WAIT, CLOSING 같은 edge state는 일반 traffic으로는 도달 어려움 → directed sequence 필요.

## Q3. (Apply)

Packet loss injection 후 검증해야 할 동작은?

??? answer "정답 / 해설"
    1. **Sender**: 일정 시간(RTO) 후 재전송 발생
    2. **Receiver**: dup ACK 발생 후 receiver buffer가 nope (loss는 receiver 입장에서 OOO)
    3. **Sender**: 3 dup ACK 받으면 fast retransmit
    4. **Both**: congestion window 축소 (cwnd reduction)
    5. **Connection**: 정상 복구 → throughput 회복

## Q4. (Analyze)

TOE 검증에서 reference model로 Linux kernel TCP를 쓰는 이점/단점은?

??? answer "정답 / 해설"
    **이점**: 가장 standard한 reference. RFC 준수 + production 검증된 구현. 다양한 OS와 호환성 확인.

    **단점**: Linux kernel은 매우 큼 → 시뮬에 통합 어려움. UM Linux를 시뮬 안에서 돌리는 등 복잡한 setup 필요. 대안: Python scapy, FreeBSD TCP, lightweight reference.

## Q5. (Evaluate)

다음 중 가장 catch 어려운 silent corruption 시나리오는?

- [ ] A. Connection close 후 segment 도착
- [ ] B. ACK number wrap-around (32-bit overflow)
- [ ] C. Out-of-order segment의 잘못된 reassembly
- [ ] D. Pause frame 미수신

??? answer "정답 / 해설"
    **B**. 32-bit sequence/ack number는 high BW에서 ~30초마다 wrap. Wrap 처리 버그는 정상 traffic에서 발견 안 됨, 30초 이상 long-duration 시나리오에서만 발현. PAWS (Protection Against Wrapped Sequences) 같은 방어 메커니즘이 있지만 검증이 까다로움.
