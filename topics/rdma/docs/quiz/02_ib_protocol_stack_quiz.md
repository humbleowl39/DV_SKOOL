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

## Q6. (Apply — Confluence)

Confluence *Details of MSN field* 의 규칙에 따라 다음 시나리오의 MSN 추이를 답하라.

> 4 KB RDMA WRITE (MTU=1KB → 4 packet, SSN=10) 직후, requester 가 동일 RDMA WRITE 의 r2 (PSN=middle) 만 timeout 으로 재전송. 이후 4 packet 모두 도착.

??? answer "정답 / 해설"
    - 첫 4 packet 처리: MSN 은 last packet 에서만 증가 → 결과적으로 SSN=10 의 last 패킷에서 MSN += 1.
    - r2 만 재전송 → 이는 **duplicate request** 로 인식 → MSN **증가하지 않음**, responder 는 캐시된 ACK 를 재전송. last 패킷도 다시 도착하면 마찬가지로 duplicate, 변화 없음.

    Confluence: *Details of MSN field* + IB Spec 1.4 §C9-148.

## Q7. (Analyze — Confluence)

사내 IP 의 BTH default 정책 (MTU=1024, P_Key=0xFFFF, TVer=Reserved6=MigReq=0) 이 spec 자체와 어떻게 다르며, 검증 scoreboard 비교에는 어떤 영향이 있나?

??? answer "정답 / 해설"
    - Spec 은 MTU 256/512/1024/2048/4096 모두 허용, P_Key 도 가변.
    - 사내는 *deployment-level 결정* 으로 정적 default 를 잡음.
    - Scoreboard 가 BTH 비교를 단순 `==` 로 하면 MTU 협상 / multi-partition 시나리오 검증에서 false fail. 따라서 *internal-default-aware* 비교 또는 *don't-care mask* 가 필요.
