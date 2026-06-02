---
title: "Quiz — Module 03: UPIU & Command Flow"
---

[← Module 03 본문으로 돌아가기](../../03_upiu_command_flow/)

---

## Q1. (Remember)

UPIU의 종류 6가지 이상을 답하세요.

<details>
<summary>정답 / 해설</summary>

1. **Command UPIU** — SCSI 명령
2. **Response UPIU** — 명령 완료 응답
3. **Data In UPIU** — device → host 데이터
4. **Data Out UPIU** — host → device 데이터
5. **Task Management Request UPIU** — abort, reset 등
6. **Task Management Response UPIU**
7. **Query Request/Response UPIU** — descriptor/attribute/flag access
8. **NOP UPIU** — handshake/keep-alive
9. **Reject UPIU** — 잘못된 UPIU 거부

이 9가지가 정답인 이유는 UFS가 데이터 전송뿐만 아니라 장치 관리, 오류 처리, 연결 유지라는 세 가지 역할을 UPIU 하나의 프레임 형식 안에서 모두 처리하도록 설계되었기 때문입니다. Command/Response/Data는 I/O 경로, Task Management는 큐 제어 경로, Query는 장치 설정 경로, NOP는 링크 상태 확인, Reject는 프로토콜 위반 처리를 담당합니다. UPIU 종류를 외우는 것은 단순 암기가 아니라 어떤 동작이 어느 경로를 통해 이루어지는지 추론하는 기반이 됩니다.

</details>
## Q2. (Understand)

WRITE 명령의 UPIU 흐름을 시퀀스로 답하세요.

<details>
<summary>정답 / 해설</summary>

1. **Command UPIU** (host→device): WRITE 명령 + LBA + length
2. **Ready-To-Transfer UPIU** (device→host): "데이터 보내라" 신호
3. **Data Out UPIU** N개 (host→device): 실제 데이터
4. **Response UPIU** (device→host): 완료 + status

READ는 RTT가 없고 Data In UPIU가 host로 옴.

WRITE에 RTT(Ready-To-Transfer)가 필요한 이유는 device가 내부 버퍼 준비 상태를 host에 알려야 하기 때문입니다. host가 RTT를 기다리지 않고 바로 Data Out을 보내면, device 버퍼가 가득 찬 상태에서 데이터를 수신하지 못하는 상황이 발생할 수 있습니다. READ의 경우 device가 데이터를 준비하는 주체이므로 준비가 되었을 때 Data In UPIU를 보내면 충분하며, host의 허가를 별도로 받을 필요가 없습니다. 이 비대칭 흐름을 이해하면 DV에서 WRITE와 READ에 서로 다른 커버리지 포인트가 필요한 이유가 명확해집니다.

</details>
## Q3. (Apply)

Task Tag 0-31 중 동시에 11개 명령을 발행하면, queue depth는?

<details>
<summary>정답 / 해설</summary>

**Queue depth = 11**. Task Tag는 식별자, 동시 발행 가능한 명령 수가 queue depth. UFS spec 최대 32. 11이면 32 capacity 중 11 사용 중.

"queue depth = 11"이 정답인 이유는 queue depth가 Tag 범위의 크기가 아니라 현재 미완료 상태로 진행 중인 명령의 수를 의미하기 때문입니다. Task Tag 0-31은 최대 32개를 식별할 수 있는 용량이지만, 실제로 동시에 발행된 명령이 11개라면 그 순간의 queue depth는 11입니다. Tag 범위(32)와 현재 활성 명령 수(11)를 혼동하지 않는 것이 핵심이며, DV에서는 0~32 전 범위의 queue depth를 커버리지 bin으로 나누어 각각을 검증해야 합니다.

</details>
## Q4. (Analyze)

Task Tag 매칭 오류가 위험한 이유는?

<details>
<summary>정답 / 해설</summary>

Driver가 Task Tag=5 명령에 대한 응답을 기다리는데, HCI가 Task Tag=3의 응답을 5로 잘못 라우팅하면:
- Driver는 명령 5의 결과로 명령 3의 데이터를 받음 → 다른 LBA의 데이터를 잘못 처리
- 명령 3의 진짜 응답은 사라짐 → driver가 무한 대기 또는 timeout
→ silent data corruption + hang. 검증의 critical path.

Task Tag 매칭 오류가 특히 위험한 점은 두 가지 피해가 동시에 발생한다는 것입니다. 첫째, 잘못 라우팅된 응답을 받은 명령은 오류 없이 완료 처리되지만 실제로는 다른 LBA의 데이터를 처리했으므로 파일 시스템 또는 사용자 데이터가 조용히 손상됩니다. 둘째, 원래 응답을 기다리던 명령은 응답을 받지 못해 timeout 또는 hang 상태에 빠집니다. 에러 신호 없이 두 명령이 동시에 피해를 입으므로, 이 버그는 실리콘 테이프아웃 이전에 반드시 scoreboard 수준의 Tag 매칭 검증으로 잡아야 하는 critical path입니다.

</details>
## Q5. (Evaluate)

Sense Data의 Sense Key, ASC, ASCQ의 역할 차이는?

<details>
<summary>정답 / 해설</summary>

- **Sense Key (4-bit)**: 에러의 broad category — Hardware Error, Illegal Request, Aborted Command 등 16종
- **ASC (Additional Sense Code)**: 더 구체적 원인 — LBA out of range, parameter list length error 등
- **ASCQ (ASC Qualifier)**: ASC 내 세부 구분 — 같은 ASC라도 sub-type 구분

Driver는 이 셋을 조합해 fail 원인을 정확히 파악 + 적절한 복구 동작 결정.

세 필드가 계층 구조로 나뉜 이유는 드라이버가 에러에 대응하는 방식이 에러의 범주마다 다르기 때문입니다. Sense Key만으로 "Hardware Error"임을 알면 드라이버는 재시도 정책을 적용할지 결정할 수 있고, ASC로 "LBA out of range"임을 알면 요청 자체의 파라미터를 수정해야 함을 알 수 있습니다. ASCQ는 동일한 ASC 상황에서도 세부 원인이 다를 때 복구 방법을 분기하기 위한 추가 정보입니다. DV scoreboard에서 Sense Data를 검증할 때는 이 세 필드의 조합이 spec에 정의된 시나리오와 정확히 일치하는지 확인해야 합니다.

</details>
