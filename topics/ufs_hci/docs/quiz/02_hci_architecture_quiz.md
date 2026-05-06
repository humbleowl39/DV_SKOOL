# Quiz — Module 02: HCI Architecture

[← Module 02 본문으로 돌아가기](../02_hci_architecture.md)

---

## Q1. (Remember)

UTRD의 크기와 핵심 필드는?

??? answer "정답 / 해설"
    - **크기**: 32 bytes
    - **핵심 필드**: command UPIU pointer, response UPIU pointer, command descriptor base address (CDB), data buffer pointer, status word, OCS (Overall Command Status).

## Q2. (Understand)

Doorbell ring부터 명령 완료까지의 흐름을 4단계로 답하세요.

??? answer "정답 / 해설"
    1. **SW**: UTRD slot 작성 + UPIU 메모리 작성
    2. **SW**: UTRLDBR의 해당 slot 비트 set (doorbell ring)
    3. **HCI**: UTRD fetch → UPIU 추출 → UniPro로 전송 → device 응답 수신
    4. **HCI**: UTRD에 OCS 작성 + interrupt 발생 → SW가 응답 처리

## Q3. (Apply)

Interrupt aggregation의 trade-off는?

??? answer "정답 / 해설"
    **장점**: 여러 명령 완료를 모아서 한 인터럽트로 → CPU overhead ↓ (특히 high-throughput).

    **단점**: 첫 완료 명령의 latency ↑ (timer/counter 대기). 실시간 sensitive 워크로드에는 부적합.

    **튜닝**: counter (N개 명령 모임) + timer (T시간 후 강제 trigger) 조합.

## Q4. (Analyze)

UFS HCI register 중 UTRLBA와 UTMRLBA의 역할 차이는?

??? answer "정답 / 해설"
    - **UTRLBA**: 일반 명령용 UTRD list base address. READ/WRITE 등 user data 명령.
    - **UTMRLBA**: Task Management용 UTRD list base address. ABORT, RESET 등 control 명령. Out-of-band처럼 정상 명령 큐와 격리되어 빠른 처리 가능.

## Q5. (Evaluate)

다음 중 silent corruption 위험이 가장 큰 시나리오는?

- [ ] A. Doorbell write가 늦게 도달
- [ ] B. UTRD의 Command UPIU pointer가 잘못된 메모리 주소
- [ ] C. UTRD list slot이 모두 사용 중
- [ ] D. Interrupt aggregation timer 만료

??? answer "정답 / 해설"
    **B**. HCI가 잘못된 UPIU를 fetch → 잘못된 SCSI command 발행 → 잘못된 LBA에 read/write → silent corruption. A/C/D는 throughput/latency 영향이지만 데이터 corruption 아님.
