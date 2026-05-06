# UFS HCI 용어집

핵심 용어 ISO 11179 형식 정의.

---

## D — Doorbell

### Doorbell

**Definition.** SW driver가 UTRD를 메모리에 작성한 후 HCI에 처리 시작을 알리는 register write 메커니즘.

**Source.** JEDEC JESD223 (UFSHCI Spec).

**Related.** UTRLDBR, UTMRLDBR.

**Use.** SW가 UTRD slot에 명령 작성 → 해당 비트 set → HCI가 명령 fetch.

**See also.** [Module 02](02_hci_architecture.md)

---

## H — HCI

### HCI (Host Controller Interface)

**Definition.** SW driver와 UFS HW 사이의 표준 register/memory 인터페이스로, JEDEC JESD223이 정의.

**Source.** JEDEC JESD223 (UFSHCI Spec).

**Related.** UTRD, UTMRD, doorbell.

**See also.** [Module 02](02_hci_architecture.md)

---

## L — LU / LUN

### LU (Logical Unit) / LUN

**Definition.** UFS device의 storage 영역 분할 단위로, 각 LU는 독립적인 SCSI device처럼 동작.

**Source.** UFS Spec.

**Related.** Boot LU, RPMB LU, Normal LU.

**Example.** Boot LU = 부팅 이미지, RPMB LU = secure storage, Normal LU = user data.

**See also.** [Module 03](03_upiu_command_flow.md)

---

## M — M-PHY

### M-PHY

**Definition.** MIPI Alliance의 시리얼 PHY 표준으로, UFS의 physical layer.

**Source.** MIPI M-PHY Spec.

**Related.** UniPro, HS Gear, PWM.

**Speeds.** Gear 1-5 (HS), PWM-G1 to PWM-G5.

**See also.** [Module 01](01_ufs_protocol_stack.md)

---

## S — SCSI / Sense Data

### SCSI Command

**Definition.** UFS의 application layer 명령 표준으로, UPIU에 캡슐화되어 전송.

**Source.** SCSI standards (T10).

**Related.** CDB, sense data.

**Common commands.** READ(10/16), WRITE(10/16), INQUIRY, REPORT_LUNS.

### Sense Data

**Definition.** 명령 실패 시 device가 host에 반환하는 상세 fail 원인 정보 (sense key + ASC + ASCQ).

**Source.** SCSI standards.

**Related.** Response UPIU, error recovery.

---

## T — Task Tag

### Task Tag

**Definition.** 동시 발행된 명령을 식별하는 0-31 범위의 태그로, queue depth 32에 대응.

**Source.** UFS Spec.

**Related.** UTRD slot, UPIU header.

**Critical.** Response의 Task Tag로 매칭. 매핑 오류 = wrong response → 데이터 corruption.

**See also.** [Module 03](03_upiu_command_flow.md)

---

## U — UPIU / UTRD / UniPro

### UPIU (UFS Protocol Information Unit)

**Definition.** UFS의 명령/데이터/응답을 캡슐화하는 표준 frame.

**Source.** JEDEC JESD220 (UFS Spec).

**Related.** Command/Response/Data In/Out/Task Mgmt/Query/NOP/Reject UPIU.

**See also.** [Module 03](03_upiu_command_flow.md)

### UTRD (UTP Transfer Request Descriptor)

**Definition.** SW driver가 작성하는 32-byte 구조로, 명령 정보 + UPIU pointer + response pointer를 포함.

**Source.** JEDEC JESD223.

**Related.** UTMRD, doorbell, queue.

**See also.** [Module 02](02_hci_architecture.md)

### UniPro

**Definition.** MIPI의 link/network/transport layer 표준으로, UFS의 transport layer.

**Source.** MIPI UniPro Spec.

**Related.** M-PHY, UPIU, frame.

**See also.** [Module 01](01_ufs_protocol_stack.md)

---

## 추가 약어

| 약어 | 풀네임 | 의미 |
|------|--------|------|
| **UFS** | Universal Flash Storage | JEDEC 모바일/서버 스토리지 표준 |
| **UFSHCI** | UFS Host Controller Interface | SW-HW 인터페이스 표준 |
| **UTP** | UFS Transport Protocol | UFS의 transport layer |
| **CDB** | Command Descriptor Block | SCSI command 형식 |
| **UTRLBA** | UTRD List Base Address | UTRD 메모리 위치 register |
| **UTMRLBA** | UTMRD List Base Address | Task Management UTRD 위치 |
| **HCS** | Host Controller Status | HCI 상태 register |
| **IS** | Interrupt Status | 인터럽트 status register |
| **CAP** | Capabilities | HCI capability register |
| **EHS** | Extra Header Segment | UPIU 확장 헤더 |
| **NOP** | No Operation | UFS NOP UPIU (handshake용) |
| **RPMB** | Replay Protected Memory Block | secure storage LU |
