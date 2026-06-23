---
pagefind: false
title: "Quiz — Module 09: Quick Reference Card"
---

[← Module 09 본문으로 돌아가기](../../09_quick_reference_card/)

---

## Q1. (Remember)

OpCode `0x06` 의 디코딩은? (BTH 8-bit 분해)

<details>
<summary>정답 / 해설</summary>

`0x06` = `000_00110`

- 상위 3-bit `000` = **RC (Reliable Connection)**
- 하위 5-bit `00110` = **RDMA_WRITE_FIRST**

→ RC RDMA WRITE 첫 패킷, RETH 포함.

BTH OpCode 의 8-bit 구조를 알면 어떤 opcode 값이라도 즉시 분해할 수 있다. 상위 3-bit 가 service type (000=RC, 001=UC, 010=RD, 011=UD) 을 나타내고, 하위 5-bit 가 operation + packet-position (FIRST/MIDDLE/LAST/ONLY) 을 인코딩한다. 따라서 `0x06` 이 왜 "RC WRITE FIRST"인지 모르겠다면 십진수로 변환(6)하지 말고 반드시 이진수로 분해해야 하며, 상위-하위 경계를 3/5 비트로 나누는 것이 핵심이다.

</details>
## Q2. (Understand)

RC SEND 와 UD SEND 의 packet layout 비교 (header 차이) 를 한 줄로 설명하라.

<details>
<summary>정답 / 해설</summary>

RC SEND: BTH | (Payload) | ICRC
UD SEND: BTH | **DETH** | (Payload) | ICRC

UD 는 connectionless 라 매 packet 에 SrcQP + Q_Key (DETH) 가 필요. RC 는 connection 으로 sender 식별 가능하므로 DETH 없음.

RC 에서 DETH 가 없어도 되는 이유는 QP 가 connect 시점에 이미 상대방 QP 번호를 교환했고, 이후 패킷은 BTH 의 DestQP 만으로 수신측이 어느 QP 로 배달할지 알 수 있기 때문이다. UD 는 stateless 이므로 패킷 하나만 봐도 "어디서 왔는지"를 알 수 있어야 하고, 또 Q_Key 검증도 매 패킷마다 필요하다. 검증 패킷 디코더를 짤 때 service type 을 먼저 확인하지 않으면 DETH 유무 파싱에서 offset 오류가 생긴다.

</details>
## Q3. (Apply)

S6 (Remote MR bound violation) 시나리오의 Expected WC status 와 debug flag 는?

<details>
<summary>정답 / 해설</summary>

- WC status: `WC_REM_ACCESS_ERR`
- Debug flag: `WC_FLAG_RESP_RANGE`

Trigger: NODE0 TX 에 length corrupt callback → packet 의 length 가 MR 범위 초과 → responder 가 NAK + Error CQ.

</details>
## Q4. (Analyze)

QP attribute `retry_cnt` 와 `rnr_retry` 의 차이를 분석하라.

<details>
<summary>정답 / 해설</summary>

- **retry_cnt**: Local ACK timeout, PSN Sequence Error, Implied NAK 등 **transport-level retry** 의 횟수.
- **rnr_retry**: RNR NAK 받은 후 receiver 의 RECV WR 가 준비되기를 기다리며 재시도하는 횟수. 7 = infinite.

별도인 이유: RNR 은 receiver 의 application-level 사정 (RECV 큐 비어 있음) 이므로 transport 의 packet 손실과 분리해 별도 정책으로 처리해야 함. 한 카운터로 합치면 receiver 가 느릴 때 transport drop 시나리오에서 retry 가 부족해질 수 있음.

</details>
## Q5. (Evaluate)

"30-second mental checklist" 의 8개 항목 중 코드 리뷰에서 가장 자주 놓치는 것을 하나 선택하고 그 이유를 평가하라.

<details>
<summary>정답 / 해설</summary>

**Modulo 2^24 비교 함수 사용** 이 가장 자주 놓침.

이유:

- PSN 은 24-bit modulo arithmetic 이라 `>` 단순 비교는 wrap 시점에 버그.
- 일반 sequence number 검증 코드를 단순 옮겨오면 보통 `(a > b)` 또는 `(a - b) > threshold` 로 작성.
- 검증 환경에서 wrap 까지 도달하는 데 정상 traffic 으로 시간이 오래 걸려, sanity test 에서는 잘 안 보임.
- Wrap 발생 시점에 false fail / silent miss 둘 다 가능.

→ 리뷰 시 PSN 비교 helper 함수가 modulo-aware 인지 (e.g. `psn_cmp(a, b)`) 명시적으로 확인이 필요.

</details>
