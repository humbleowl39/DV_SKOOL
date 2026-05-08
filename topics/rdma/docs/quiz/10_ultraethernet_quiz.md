# Quiz — Module 10: Ultraethernet (UEC)

[← Module 10 본문으로 돌아가기](../10_ultraethernet.md)

---

## Q1. (Remember)

UEC 의 두 핵심 sublayer 는 무엇이며 각각 무엇을 담당하나?

??? answer "정답 / 해설"
    - **PDS (Packet Delivery Sublayer)** — 패킷 전송 신뢰성, ordering, multipath 분배.
    - **SES (Semantic Sublayer)** — libfabric API 호출을 PDS 패킷으로 변환, RMA · SEND · TAGGED · MPI 시맨틱 처리.

    출처: Confluence *Packet Delivery Sublayer* (id=198378057), *Semantic Sublayer* (id=200179723).

## Q2. (Remember)

PDS 가 정의하는 4 종 PSN 을 모두 들어라.

??? answer "정답 / 해설"
    `clear_psn`, `cumulative_psn`, `ack_psn`, `sack`.

    Confluence: *PSN handling in UEC* (id=201163262).

## Q3. (Understand)

UEC 가 RoCEv2 와 비교해 *lossless 가정* 을 폐기한 결과 검증 시나리오는 어떻게 달라지나?

??? answer "정답 / 해설"
    - PFC 비활성 환경에서도 정상 동작해야 한다 → packet drop 시 selective retransmission + multipath rerouting 검증이 필수.
    - RC 의 strict in-order assertion 을 그대로 적용하면 false fail. UEC 검증은 **message 단위 결과 정합성** + **SOM/EOM 1:1 일치** 가 우선.

## Q4. (Apply)

3-packet RDMA WRITE 메시지를 UEC 로 보낼 때 SOM, EOM, MID, Buffer Offset 의 값 패턴을 적어라.

??? answer "정답 / 해설"
    - Packet 1: SOM=1, EOM=0, MID=X, Buffer Offset = base offset (예: 0).
    - Packet 2: SOM=0, EOM=0, MID=X, Buffer Offset = same.
    - Packet 3: SOM=0, EOM=1, MID=X, Buffer Offset = same.

    SOM=1 인 packet 만 Header Data 가 의미를 갖는다. Buffer Offset 은 메시지 내내 동일, packet 별 위치는 *Header Data offset* (SOM=0 packet) 으로.

## Q5. (Apply)

송신측이 *큰* 메시지를 보낼 때 rendezvous 와 deferrable send 의 차이점은? 어느 쪽이 송신 시점에 결정되나?

??? answer "정답 / 해설"
    - **Rendezvous**: 송신 *전* 에 sender 가 rendezvous 모드로 결정. target 이 RECV post 한 뒤 read 트리거.
    - **Deferrable Send**: 모든 크기 가능. target 이 못 받을 상태면 *stop* 메시지 → 추후 *resume*. **수신측이 동적으로 defer 결정**.

## Q6. (Analyze)

UEC-CC 가 보장하기 위해 switch 에 요구하는 두 기능과, *선택적* 으로 도움이 되는 한 기능은?

??? answer "정답 / 해설"
    - 필수: (1) CoS 기반 traffic class 분류 (DSCP / PCP), (2) ECN marking.
    - 선택: **packet trimming** — 지원 시 UET-CC 가 더 빠르게 수렴.

    Confluence: *UET-CC, basic introduction* (id=162759072).

## Q7. (Evaluate)

IB / RoCEv2 의 *strict in-order* assertion 을 UEC 시나리오에 그대로 가져오면 어떻게 되며, 어떤 검증 단위로 대체해야 하는가?

??? answer "정답 / 해설"
    UEC 는 packet 단위 OOO 를 허용하므로 strict in-order 단정은 false fail 다발.
    대체: **per-message ordering** (같은 MID 내 SOM/EOM 순서 + Buffer Offset 일관성), **Modified Length == Request Length** 검증, **DC=1 시 global observability 후 ACK** 시퀀스.
