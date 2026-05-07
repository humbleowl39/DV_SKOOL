# Quiz — Module 04: Service Types & QP FSM

[← Module 04 본문으로 돌아가기](../04_service_types_qp.md)

---

## Q1. (Remember)

RC, UC, UD 가 지원하는 OpCode 군을 비교하라.

??? answer "정답 / 해설"
    | | RC | UC | UD |
    |--|----|----|----|
    | SEND | ✓ | ✓ | ✓ (only) |
    | WRITE | ✓ | ✓ | ✗ |
    | READ | ✓ | ✗ | ✗ |
    | ATOMIC | ✓ | ✗ | ✗ |

## Q2. (Understand)

QP FSM 7 state 를 나열하고, RX 가능 / TX 가능 상태를 표시하라.

??? answer "정답 / 해설"
    | State | RX | TX |
    |-------|----|----|
    | Reset | ✗ | ✗ |
    | Init | ✗ | ✗ |
    | RTR (Ready-To-Receive) | ✓ | ✗ |
    | **RTS** (Ready-To-Send) | ✓ | ✓ ← 정상 동작 |
    | SQD (Send Queue Drain) | ✓ | (in-flight only) |
    | SQErr | ✓ | ✗ |
    | Err | ✗ | ✗ |

## Q3. (Apply)

RTR → RTS 전환에 필요한 attribute (RC) 를 5개 들어라.

??? answer "정답 / 해설"
    1. `sq_psn` — sender 의 init PSN
    2. `timeout` — Local ACK timeout 값
    3. `retry_cnt` — 일반 retry 횟수
    4. `rnr_retry` — RNR retry 횟수
    5. `max_rd_atomic` — outstanding READ/ATOMIC 갯수 (sender 측)

    추가로 sg_list size, max inline data 등도 가능.

## Q4. (Analyze)

UD QP 가 multi-packet message 를 보낼 수 있는가? 그렇지 않다면 그 제약은 어디에서 오는가?

??? answer "정답 / 해설"
    **불가능**. UD 는 connectionless 이므로 양 끝의 PSN-기반 sequence 추적이 없고, 각 message = 단일 packet 으로 정의 (spec §9.8.2). 따라서 message 의 길이는 MTU − (Eth+IP+UDP+BTH+DETH+ICRC) 로 제한.

    제약의 출처: UD 는 packet 단위 독립 datagram, 그래서 fragmentation 은 application 책임.

## Q5. (Evaluate)

"RC 는 reliable 하니 packet drop 은 발생하지 않는다 → 검증 시 drop 시나리오는 만들 필요 없다" 는 주장을 평가하라.

??? answer "정답 / 해설"
    **틀림**.

    RC 의 reliability 는 spec 이 packet drop 을 막는 게 아니라, **packet drop 이 일어나도 sender 의 retry 가 reliability 를 보장** 하는 메커니즘. 따라서:

    - Drop 은 발생할 수 있고 spec 도 허용 (단지 retry 로 회복).
    - 검증 관점에서 **drop 시나리오는 retry 로 회복되는지를 확인하기 위해 반드시 inject** 해야 함.
    - RDMA-TB 의 `error_handling` vplan S1 (Local ACK timeout) 이 정확히 이 시나리오.

    "drop 안 일어남" 으로 가정하면 retry 코드가 dead code 인지 확인 못 함.
