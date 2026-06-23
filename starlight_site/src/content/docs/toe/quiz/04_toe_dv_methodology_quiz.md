---
pagefind: false
title: "Quiz — Module 04: TOE DV Methodology"
---

[← Module 04 본문으로 돌아가기](../../04_toe_dv_methodology/)

---

## Q1. (Remember)

TCP state machine의 11 state를 나열하세요.

<details>
<summary>정답 / 해설</summary>

CLOSED, LISTEN, SYN_SENT, SYN_RCVD, ESTABLISHED, FIN_WAIT_1, FIN_WAIT_2, CLOSE_WAIT, CLOSING, LAST_ACK, TIME_WAIT.

+ (active vs passive open 분기, FIN 처리 분기로 구성).

11개 state는 크게 세 구간으로 기억하면 쉽다. 연결 수립 구간(CLOSED → SYN_SENT / LISTEN → SYN_RCVD → ESTABLISHED), 데이터 전송 구간(ESTABLISHED 유지), 그리고 연결 해제 구간(FIN_WAIT_1/2, CLOSE_WAIT, CLOSING, LAST_ACK, TIME_WAIT)이다. Active close 측이 FIN을 먼저 보내면 FIN_WAIT 경로를 밟고, Passive close 측은 CLOSE_WAIT → LAST_ACK 경로를 밟는다. DV 관점에서 CLOSING과 TIME_WAIT는 양쪽이 거의 동시에 FIN을 보내는 드문 경우에만 진입하므로 directed sequence가 없으면 커버리지 미달이 된다.

</details>
## Q2. (Understand)

State coverage가 중요한 이유는?

<details>
<summary>정답 / 해설</summary>

각 state에서 받을 수 있는 segment 종류 + state transition이 다름. 한 state라도 누락하면 그 transition 경로의 버그 catch 불가. 특히 TIME_WAIT, CLOSING 같은 edge state는 일반 traffic으로는 도달 어려움 → directed sequence 필요.

State coverage가 중요한 근본 이유는 TCP 처리 로직이 "현재 state가 무엇인가"에 따라 완전히 달라지기 때문이다. 예를 들어 ESTABLISHED에서 FIN을 받는 것과 FIN_WAIT_1에서 FIN을 받는 것은 전혀 다른 전이를 일으킨다. 검증되지 않은 state에 HW가 진입하면 존재하지 않는 전이가 undefined behavior로 이어질 수 있다. CLOSING 같은 state는 양쪽이 동시에 FIN을 보내야만 진입하므로, 랜덤 트래픽으로는 수천 개의 시나리오를 돌려도 한 번도 나타나지 않을 수 있다.

</details>
## Q3. (Apply)

Packet loss injection 후 검증해야 할 동작은?

<details>
<summary>정답 / 해설</summary>

1. **Sender**: 일정 시간(RTO) 후 재전송 발생
2. **Receiver**: dup ACK 발생 후 receiver buffer가 nope (loss는 receiver 입장에서 OOO)
3. **Sender**: 3 dup ACK 받으면 fast retransmit
4. **Both**: congestion window 축소 (cwnd reduction)
5. **Connection**: 정상 복구 → throughput 회복

Packet loss injection의 목적은 "잃어버린 패킷을 TOE가 스스로 발견하고 복구하는 전 과정"을 검증하는 것이다. RTO 경로와 fast retransmit 경로는 서로 다른 조건에서 진입하므로 두 경로를 모두 커버해야 한다. 특히 cwnd 축소 후 throughput이 회복되는 것까지 확인해야 혼잡 제어 로직도 함께 검증된다. 복구되지 않거나 connection이 RST로 끊기는 경우는 HW state machine 버그의 강력한 증거다.

</details>
## Q4. (Analyze)

TOE 검증에서 reference model로 Linux kernel TCP를 쓰는 이점/단점은?

<details>
<summary>정답 / 해설</summary>

**이점**: 가장 standard한 reference. RFC 준수 + production 검증된 구현. 다양한 OS와 호환성 확인.

**단점**: Linux kernel은 매우 큼 → 시뮬에 통합 어려움. UM Linux를 시뮬 안에서 돌리는 등 복잡한 setup 필요. 대안: Python scapy, FreeBSD TCP, lightweight reference.

Reference model로 Linux kernel을 선택하면 수십 년간 실제 트래픽으로 단련된 RFC 구현을 golden reference로 쓴다는 신뢰성 측면에서 최선이다. 그러나 Linux kernel을 HDL 시뮬레이터 환경에 올리려면 User Mode Linux나 SystemC co-simulation 같은 무거운 인프라가 필요하고, 빌드·부팅 시간이 시뮬 런타임에 더해진다. 이 비용을 줄이기 위해 Scapy 같은 Python 라이브러리로 패킷 레벨 reference만 구현하거나, 경량 FreeBSD TCP 스택을 C 모델로 포팅하는 절충안이 실무에서 자주 사용된다.

</details>
## Q5. (Evaluate)

다음 중 가장 catch 어려운 silent corruption 시나리오는?

- [ ] A. Connection close 후 segment 도착
- [ ] B. ACK number wrap-around (32-bit overflow)
- [ ] C. Out-of-order segment의 잘못된 reassembly
- [ ] D. Pause frame 미수신

<details>
<summary>정답 / 해설</summary>

**B**. 32-bit sequence/ack number는 high BW에서 ~30초마다 wrap. Wrap 처리 버그는 정상 traffic에서 발견 안 됨, 30초 이상 long-duration 시나리오에서만 발현. PAWS (Protection Against Wrapped Sequences) 같은 방어 메커니즘이 있지만 검증이 까다로움.

A(close 후 segment 도착)와 C(out-of-order reassembly)는 비교적 짧은 시뮬레이션에서도 재현할 수 있는 이벤트이지만, sequence number wrap-around는 10 Gbps 이상의 고속 전송에서 32비트 공간이 약 30초 만에 소진될 때만 발생한다. 시뮬레이션에서 30초를 실제 시간으로 돌리는 것은 사실상 불가능하므로, 시뮬 환경에서는 sequence number를 강제로 overflow 직전 값으로 세팅하는 directed test가 없으면 이 버그는 영원히 잠자고 있다가 프로덕션에서 처음 발현된다. D(pause frame 미수신)는 flow control 문제이지 데이터 무결성 문제가 아니므로 범주가 다르다.

</details>
