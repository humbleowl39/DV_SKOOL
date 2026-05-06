# Quiz — Module 03: UPIU & Command Flow

[← Module 03 본문으로 돌아가기](../03_upiu_command_flow.md)

---

## Q1. (Remember)

UPIU의 종류 6가지 이상을 답하세요.

??? answer "정답 / 해설"
    1. **Command UPIU** — SCSI 명령
    2. **Response UPIU** — 명령 완료 응답
    3. **Data In UPIU** — device → host 데이터
    4. **Data Out UPIU** — host → device 데이터
    5. **Task Management Request UPIU** — abort, reset 등
    6. **Task Management Response UPIU**
    7. **Query Request/Response UPIU** — descriptor/attribute/flag access
    8. **NOP UPIU** — handshake/keep-alive
    9. **Reject UPIU** — 잘못된 UPIU 거부

## Q2. (Understand)

WRITE 명령의 UPIU 흐름을 시퀀스로 답하세요.

??? answer "정답 / 해설"
    1. **Command UPIU** (host→device): WRITE 명령 + LBA + length
    2. **Ready-To-Transfer UPIU** (device→host): "데이터 보내라" 신호
    3. **Data Out UPIU** N개 (host→device): 실제 데이터
    4. **Response UPIU** (device→host): 완료 + status

    READ는 RTT가 없고 Data In UPIU가 host로 옴.

## Q3. (Apply)

Task Tag 0-31 중 동시에 11개 명령을 발행하면, queue depth는?

??? answer "정답 / 해설"
    **Queue depth = 11**. Task Tag는 식별자, 동시 발행 가능한 명령 수가 queue depth. UFS spec 최대 32. 11이면 32 capacity 중 11 사용 중.

## Q4. (Analyze)

Task Tag 매칭 오류가 위험한 이유는?

??? answer "정답 / 해설"
    Driver가 Task Tag=5 명령에 대한 응답을 기다리는데, HCI가 Task Tag=3의 응답을 5로 잘못 라우팅하면:
    - Driver는 명령 5의 결과로 명령 3의 데이터를 받음 → 다른 LBA의 데이터를 잘못 처리
    - 명령 3의 진짜 응답은 사라짐 → driver가 무한 대기 또는 timeout
    → silent data corruption + hang. 검증의 critical path.

## Q5. (Evaluate)

Sense Data의 Sense Key, ASC, ASCQ의 역할 차이는?

??? answer "정답 / 해설"
    - **Sense Key (4-bit)**: 에러의 broad category — Hardware Error, Illegal Request, Aborted Command 등 16종
    - **ASC (Additional Sense Code)**: 더 구체적 원인 — LBA out of range, parameter list length error 등
    - **ASCQ (ASC Qualifier)**: ASC 내 세부 구분 — 같은 ASC라도 sub-type 구분

    Driver는 이 셋을 조합해 fail 원인을 정확히 파악 + 적절한 복구 동작 결정.
