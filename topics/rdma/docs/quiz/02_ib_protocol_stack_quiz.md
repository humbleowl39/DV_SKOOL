# Quiz — Module 02: InfiniBand 프로토콜 스택

[← Module 02 본문으로 돌아가기](../02_ib_protocol_stack.md)

---

## Q1. (Remember)

IB 패킷의 일반 layout 을 순서대로 나열하라 (선택적 헤더는 `?` 표기).

??? answer "정답 / 해설"
    `LRH | GRH? | BTH | xTH? | Payload | ICRC | VCRC`

    LRH 와 BTH 는 필수, GRH 는 cross-subnet 또는 multicast 시, xTH 는 OpCode 별 0개 이상.

## Q2. (Understand)

ICRC 와 VCRC 가 분리된 이유는?

??? answer "정답 / 해설"
    라우터/스위치가 LRH 의 일부 (DLID 등) 를 정상적으로 변경할 수 있어야 한다.
    → 변경되는 영역을 빼고 계산되는 **ICRC 가 end-to-end 무결성** 을 보장.
    → 변경된 packet 의 link-level 무결성은 hop 마다 재계산되는 **VCRC** 가 보장.

## Q3. (Apply)

LRH 의 PktLen 필드가 nominal 0x0030 (=48) 일 때, 패킷의 실제 byte 길이는?

??? answer "정답 / 해설"
    **48 × 4 = 192 byte** (LRH 시작 ~ ICRC 끝까지). PktLen 의 단위는 4-byte word.

    VCRC (2 byte) 는 PktLen 에 포함되지 않음. 즉 wire 상의 실제 packet 은 192 + 2 = 194 byte.

## Q4. (Analyze)

GRH 가 들어가야 하는 두 조건은? 그리고 GRH 의 NxtHdr=0x1B 가 의미하는 것은?

??? answer "정답 / 해설"
    조건 (C8-1):

    1. Multicast packet
    2. Final destination 이 다른 subnet (cross-subnet)

    NxtHdr = 0x1B (= 27 in decimal) 는 "non-raw IBA transport — BTH 가 따라옴" 을 의미. RoCEv2 는 IP→UDP→BTH 체인을 사용하므로 이 값은 사용되지 않음.

## Q5. (Evaluate)

VL15 의 특별한 규칙을 3가지 이상 들고, 그 규칙들이 왜 그렇게 만들어졌는지 평가하라.

??? answer "정답 / 해설"
    1. **Flow control 의 대상이 아님** (C7-18) — management traffic 이 막히면 안 됨
    2. **Max payload 256 byte** (C7-27) — packet 크기 제한으로 buffer 부담 최소화
    3. **Switch buffer 최소 1 packet 필수** (C7-22) — 어떤 상황에서도 받을 수 있어야 함
    4. **Subnet 간 forwarding 금지** (C7-26) — management 는 subnet local
    5. **Preemptive scheduling** (C7-23) — data packet 보다 먼저

    **평가**: 모든 규칙이 "subnet management 가 끊기면 안 된다" 라는 단일 design 목적에서 파생. management plane 과 data plane 의 분리가 IB 의 운영 안정성의 근간.
