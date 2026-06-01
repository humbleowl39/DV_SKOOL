# Quiz — Module 02: HCI Architecture

[← Module 02 본문으로 돌아가기](../02_hci_architecture.md)

---

## Q1. (Remember)

UTRD의 크기와 핵심 필드는?

??? answer "정답 / 해설"
    - **크기**: 32 bytes
    - **핵심 필드**: command UPIU pointer, response UPIU pointer, command descriptor base address (CDB), data buffer pointer, status word, OCS (Overall Command Status).

    UTRD가 32 bytes로 고정된 이유는 HCI가 리스트를 배열 인덱스로 순회할 때 오프셋 계산을 단순화하기 위해서입니다. 각 필드가 정답인 것은 HCI가 명령을 처리하는 전체 파이프라인을 커버하기 때문입니다. command UPIU pointer로 명령을 가져오고, data buffer pointer로 DMA를 수행하며, OCS로 최종 결과를 SW에 알립니다. 이 중 하나라도 잘못 설정되면 명령 실행이 실패하거나 silent corruption이 발생하므로 DV assertion의 핵심 체크 포인트입니다.

## Q2. (Understand)

Doorbell ring부터 명령 완료까지의 흐름을 4단계로 답하세요.

??? answer "정답 / 해설"
    1. **SW**: UTRD slot 작성 + UPIU 메모리 작성
    2. **SW**: UTRLDBR의 해당 slot 비트 set (doorbell ring)
    3. **HCI**: UTRD fetch → UPIU 추출 → UniPro로 전송 → device 응답 수신
    4. **HCI**: UTRD에 OCS 작성 + interrupt 발생 → SW가 응답 처리

    이 4단계의 순서가 중요한 이유는 각 단계 사이에 잠재적인 타이밍 버그가 존재하기 때문입니다. 특히 1단계(UTRD 작성)가 완료되기 전에 2단계(doorbell ring)가 발생하면 HCI가 미완성 UTRD를 fetch하는 경쟁 조건이 생깁니다. SW는 UTRD와 UPIU 메모리 기록이 모두 완료되었음을 보장한 후에야 doorbell을 울려야 하며, 이 memory ordering을 검증하는 것이 DV 관점에서 핵심 테스트 포인트입니다.

## Q3. (Apply)

Interrupt aggregation의 trade-off는?

??? answer "정답 / 해설"
    **장점**: 여러 명령 완료를 모아서 한 인터럽트로 → CPU overhead ↓ (특히 high-throughput).

    **단점**: 첫 완료 명령의 latency ↑ (timer/counter 대기). 실시간 sensitive 워크로드에는 부적합.

    **튜닝**: counter (N개 명령 모임) + timer (T시간 후 강제 trigger) 조합.

    interrupt aggregation이 trade-off인 이유를 이해하려면 두 가지 상충되는 목표를 생각해야 합니다. 처리량이 높은 순차 읽기·쓰기에서는 명령이 빠르게 완료되므로 매번 인터럽트를 올리면 CPU가 인터럽트 처리에 시간을 낭비합니다. 반면 데이터베이스나 OS 파일 시스템처럼 낮은 latency가 중요한 경우, 첫 번째 완료 명령이 counter나 timer를 기다리는 동안 응답이 늦어지면 성능이 저하됩니다. 따라서 올바른 설정은 워크로드 프로파일에 따라 달라지며, DV에서는 counter=1 (aggregation 없음)과 counter=N (최대 aggregation) 양쪽 극단을 모두 검증해야 합니다.

## Q4. (Analyze)

UFS HCI register 중 UTRLBA와 UTMRLBA의 역할 차이는?

??? answer "정답 / 해설"
    - **UTRLBA**: 일반 명령용 UTRD list base address. READ/WRITE 등 user data 명령.
    - **UTMRLBA**: Task Management용 UTRD list base address. ABORT, RESET 등 control 명령. Out-of-band처럼 정상 명령 큐와 격리되어 빠른 처리 가능.

    두 레지스터가 분리된 이유는 task management 명령이 일반 I/O 명령보다 우선순위가 높아야 하기 때문입니다. 예를 들어 특정 명령을 ABORT해야 하는 상황에서 ABORT 요청이 UTRL 큐 뒤에 줄을 서서 기다린다면 abort의 목적 자체가 훼손됩니다. 별도 큐를 두어 HCI가 UTMRL을 UTRL과 독립적으로 처리할 수 있게 함으로써, 비상 제어 명령이 데이터 I/O 명령에 막히지 않는 구조를 보장합니다.

## Q5. (Evaluate)

다음 중 silent corruption 위험이 가장 큰 시나리오는?

- [ ] A. Doorbell write가 늦게 도달
- [ ] B. UTRD의 Command UPIU pointer가 잘못된 메모리 주소
- [ ] C. UTRD list slot이 모두 사용 중
- [ ] D. Interrupt aggregation timer 만료

??? answer "정답 / 해설"
    **B**. HCI가 잘못된 UPIU를 fetch → 잘못된 SCSI command 발행 → 잘못된 LBA에 read/write → silent corruption. A/C/D는 throughput/latency 영향이지만 데이터 corruption 아님.

    B가 가장 위험한 이유는 오류가 즉시 드러나지 않기 때문입니다. 잘못된 주소의 UPIU를 fetch하면 HCI는 오류 없이 명령을 실행하지만, 의도하지 않은 LBA에 데이터를 읽거나 씁니다. 이는 파일 시스템 corruption이나 보안 침해로 이어질 수 있으면서도 인터럽트나 에러 로그에 나타나지 않습니다. 반면 A(doorbell 지연)는 명령 처리가 늦어질 뿐 데이터 무결성은 유지되고, C(큐 가득 참)는 새 명령을 거부하지만 기존 명령은 정상 처리되며, D(타이머 만료)는 인터럽트 처리 방식의 차이일 뿐입니다.
