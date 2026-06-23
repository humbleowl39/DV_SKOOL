---
pagefind: false
title: "Quiz — Module 04: Service Types & QP FSM"
---

[← Module 04 본문으로 돌아가기](../../04_service_types_qp/)

---

## Q1. (Remember)

RC, UC, UD 가 지원하는 OpCode 군을 비교하라.

<details>
<summary>정답 / 해설</summary>

| | RC | UC | UD |
|--|----|----|----|
| SEND | ✓ | ✓ | ✓ (only) |
| WRITE | ✓ | ✓ | ✗ |
| READ | ✓ | ✗ | ✗ |
| ATOMIC | ✓ | ✗ | ✗ |

이 제약의 근거는 신뢰성 메커니즘의 유무에서 온다. READ 와 ATOMIC 은 원격에서 데이터를 가져오거나 메모리를 조작하므로 반드시 ACK/NAK 으로 결과를 확인해야 한다. UC 는 connection 이 있지만 ACK/retry 가 없으므로 READ 나 ATOMIC 의 정합성을 보장할 수 없다. UD 는 connectionless 라 PSN 추적 자체가 없어 multi-packet 메시지조차 불가능하고, SEND 하나만 허용된다. 표에서 아래로 갈수록 기능이 줄어드는 것은 우연이 아니라 신뢰성 보장 수준이 낮아지는 순서다.

</details>
## Q2. (Understand)

QP FSM 7 state 를 나열하고, RX 가능 / TX 가능 상태를 표시하라.

<details>
<summary>정답 / 해설</summary>

| State | RX | TX |
|-------|----|----|
| Reset | ✗ | ✗ |
| Init | ✗ | ✗ |
| RTR (Ready-To-Receive) | ✓ | ✗ |
| **RTS** (Ready-To-Send) | ✓ | ✓ ← 정상 동작 |
| SQD (Send Queue Drain) | ✓ | (in-flight only) |
| SQErr | ✓ | ✗ |
| Err | ✗ | ✗ |

FSM 설계에서 중요한 패턴은 양방향 통신이 가능해지기 전에 수신 준비부터 완료해야 한다는 점이다. RTR 에서 rx_psn 등 상대방 측 정보를 먼저 설정하고 나서야 RTS 로 전이해 송신을 시작할 수 있다. 이 순서를 어기면 송신 중에 상대방의 ACK 를 처리할 수 없는 상태가 된다. SQErr 상태에서 RX 가 남아 있는 것은 이미 나간 패킷에 대한 응답(NAK/ACK)을 받을 여지를 주기 위해서다.

</details>
## Q3. (Apply)

RTR → RTS 전환에 필요한 attribute (RC) 를 5개 들어라.

<details>
<summary>정답 / 해설</summary>

1. `sq_psn` — sender 의 init PSN
2. `timeout` — Local ACK timeout 값
3. `retry_cnt` — 일반 retry 횟수
4. `rnr_retry` — RNR retry 횟수
5. `max_rd_atomic` — outstanding READ/ATOMIC 갯수 (sender 측)

추가로 sg_list size, max inline data 등도 가능.

</details>
## Q4. (Analyze)

UD QP 가 multi-packet message 를 보낼 수 있는가? 그렇지 않다면 그 제약은 어디에서 오는가?

<details>
<summary>정답 / 해설</summary>

**불가능**. UD 는 connectionless 이므로 양 끝의 PSN-기반 sequence 추적이 없고, 각 message = 단일 packet 으로 정의 (spec §9.8.2). 따라서 message 의 길이는 MTU − (Eth+IP+UDP+BTH+DETH+ICRC) 로 제한.

제약의 출처: UD 는 packet 단위 독립 datagram, 그래서 fragmentation 은 application 책임.

</details>
## Q5. (Evaluate)

"RC 는 reliable 하니 packet drop 은 발생하지 않는다 → 검증 시 drop 시나리오는 만들 필요 없다" 는 주장을 평가하라.

<details>
<summary>정답 / 해설</summary>

**틀림**.

RC 의 reliability 는 spec 이 packet drop 을 막는 게 아니라, **packet drop 이 일어나도 sender 의 retry 가 reliability 를 보장** 하는 메커니즘. 따라서:

- Drop 은 발생할 수 있고 spec 도 허용 (단지 retry 로 회복).
- 검증 관점에서 **drop 시나리오는 retry 로 회복되는지를 확인하기 위해 반드시 inject** 해야 함.
- RDMA-TB 의 `error_handling` vplan S1 (Local ACK timeout) 이 정확히 이 시나리오.

"drop 안 일어남" 으로 가정하면 retry 코드가 dead code 인지 확인 못 함.

</details>
