# Quiz — Module 09: Quick Reference Card

[← Module 09 본문으로 돌아가기](../09_quick_reference_card.md)

---

## Q1. (Remember)

OpCode `0x06` 의 디코딩은? (BTH 8-bit 분해)

??? answer "정답 / 해설"
    `0x06` = `000_00110`

    - 상위 3-bit `000` = **RC (Reliable Connection)**
    - 하위 5-bit `00110` = **RDMA_WRITE_FIRST**

    → RC RDMA WRITE 첫 패킷, RETH 포함.

## Q2. (Understand)

RC SEND 와 UD SEND 의 packet layout 비교 (header 차이) 를 한 줄로 설명하라.

??? answer "정답 / 해설"
    RC SEND: BTH | (Payload) | ICRC
    UD SEND: BTH | **DETH** | (Payload) | ICRC

    UD 는 connectionless 라 매 packet 에 SrcQP + Q_Key (DETH) 가 필요. RC 는 connection 으로 sender 식별 가능하므로 DETH 없음.

## Q3. (Apply)

S6 (Remote MR bound violation) 시나리오의 Expected WC status 와 debug flag 는?

??? answer "정답 / 해설"
    - WC status: `WC_REM_ACCESS_ERR`
    - Debug flag: `WC_FLAG_RESP_RANGE`

    Trigger: NODE0 TX 에 length corrupt callback → packet 의 length 가 MR 범위 초과 → responder 가 NAK + Error CQ.

## Q4. (Analyze)

QP attribute `retry_cnt` 와 `rnr_retry` 의 차이를 분석하라.

??? answer "정답 / 해설"
    - **retry_cnt**: Local ACK timeout, PSN Sequence Error, Implied NAK 등 **transport-level retry** 의 횟수.
    - **rnr_retry**: RNR NAK 받은 후 receiver 의 RECV WR 가 준비되기를 기다리며 재시도하는 횟수. 7 = infinite.

    별도인 이유: RNR 은 receiver 의 application-level 사정 (RECV 큐 비어 있음) 이므로 transport 의 packet 손실과 분리해 별도 정책으로 처리해야 함. 한 카운터로 합치면 receiver 가 느릴 때 transport drop 시나리오에서 retry 가 부족해질 수 있음.

## Q5. (Evaluate)

"30-second mental checklist" 의 8개 항목 중 코드 리뷰에서 가장 자주 놓치는 것을 하나 선택하고 그 이유를 평가하라.

??? answer "정답 / 해설"
    **Modulo 2^24 비교 함수 사용** 이 가장 자주 놓침.

    이유:

    - PSN 은 24-bit modulo arithmetic 이라 `>` 단순 비교는 wrap 시점에 버그.
    - 일반 sequence number 검증 코드를 단순 옮겨오면 보통 `(a > b)` 또는 `(a - b) > threshold` 로 작성.
    - 검증 환경에서 wrap 까지 도달하는 데 정상 traffic 으로 시간이 오래 걸려, sanity test 에서는 잘 안 보임.
    - Wrap 발생 시점에 false fail / silent miss 둘 다 가능.

    → 리뷰 시 PSN 비교 helper 함수가 modulo-aware 인지 (e.g. `psn_cmp(a, b)`) 명시적으로 확인이 필요.
