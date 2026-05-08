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

---

## 추가 항목 (Phase 2 검수 완료)

### M-PHY

**Definition.** MIPI Alliance 가 정의한 고속 직렬 PHY 로, UFS 의 PHY 계층을 담당하며 HS-MODE / PWM-MODE 의 다중 gear 를 지원한다.

**Source.** MIPI M-PHY Specification.

**Related.** UniPro, gear, HS-MODE, PWM-MODE.

**See also.** [Module 01](01_ufs_protocol_stack.md)

### MCQ (Multi-Circular Queue)

**Definition.** UFS HCI 4.0+ 에서 도입된 다중 SQ/CQ 큐 모델로, host 가 다수 코어에서 동시에 명령을 발행할 수 있도록 lock contention 을 줄인다.

**Source.** JEDEC UFS HCI 4.0 (JESD223E).

**Related.** SQ, CQ, doorbell, command parallelism.

**See also.** [Module 02](02_hci_architecture.md)

### UTRLDBR (UTRL Doorbell Register)

**Definition.** Host 가 새로 추가한 UTRD slot 을 device 에 알리기 위해 set 하는 doorbell 레지스터로, 비트 위치가 UTRL slot 인덱스와 매핑된다.

**Source.** JEDEC UFS HCI Specification.

**Related.** UTRD, doorbell, slot mask.

**See also.** [Module 02](02_hci_architecture.md), [Module 03](03_upiu_command_flow.md)

### UIC (UFS Interconnect Layer)

**Definition.** Host 가 device 의 PHY/UniPro 동작을 제어하기 위해 표준화된 명령 인터페이스 (UIC command) 를 통해 접근하는 추상 계층.

**Source.** JEDEC UFS Specification.

**Related.** DME, UIC command (DME_GET, DME_SET, DME_LINKSTARTUP).

**See also.** [Module 01](01_ufs_protocol_stack.md), [Module 02](02_hci_architecture.md)

### DME (Device Management Entity)

**Definition.** UniPro stack 의 관리 엔티티로, layer 별 attribute 의 read/write 를 처리하며 host 의 UIC command 가 도달하는 endpoint 이다.

**Source.** MIPI UniPro Specification.

**Related.** UIC, UniPro, DME_GET, DME_SET.

**See also.** [Module 01](01_ufs_protocol_stack.md)

### HCE (Host Controller Enable)

**Definition.** UFS HCI 의 활성화 비트로, host 가 1 → 0 → 1 sequence 로 토글하면 controller 가 reset 후 ready 상태가 된다.

**Source.** JEDEC UFS HCI Specification.

**Related.** Reset sequence, IS register, controller initialization.

**See also.** [Module 02](02_hci_architecture.md)

### PRDT (Physical Region Description Table)

**Definition.** UTRD 가 가리키는 scatter-gather 리스트 테이블로, 각 entry 가 데이터 버퍼의 물리 주소와 byte count 를 기술한다.

**Source.** JEDEC UFS HCI Specification.

**Related.** UTRD, scatter-gather, DMA buffer.

**See also.** [Module 02](02_hci_architecture.md)

### RTT (Ready To Transfer UPIU)

**Definition.** Device 가 host 에게 write data 를 보낼 준비가 되었음을 알리는 UPIU 로, write transfer count 와 buffer offset 을 함께 전달한다.

**Source.** JEDEC UFS Specification — UPIU.

**Related.** UPIU, COMMAND, DATA OUT, write protocol.

**See also.** [Module 03](03_upiu_command_flow.md)

### UTP (UFS Transport Protocol)

**Definition.** UFS 가 SCSI command 를 UPIU 로 캡슐화해 device 에 전달하는 transport 계층으로, command / response / data UPIU 를 정의한다.

**Source.** JEDEC UFS Specification.

**Related.** SCSI, UPIU, command flow.

**See also.** [Module 01](01_ufs_protocol_stack.md), [Module 03](03_upiu_command_flow.md)



### HS-MODE & Gear (M-PHY)

**Definition.** UFS 의 M-PHY 가 제공하는 고속 전송 모드로, Gear 1~5 (HS-G1 ~ HS-G5) 와 Series A/B 의 조합으로 lane 당 raw data rate 가 결정된다 (예: HS-G4B = 11.6 Gbps/lane).

**Source.** MIPI M-PHY Specification.

**Related.** PWM-MODE, Gear, Series A/B, lane.

**See also.** [Module 01](01_ufs_protocol_stack.md)

### CDB (Command Descriptor Block)

**Definition.** SCSI command 의 표준 부호화 단위로, UFS 에서는 COMMAND UPIU 의 payload 영역에 그대로 캡슐화된다.

**Source.** SCSI Architecture Model (SAM-5); JEDEC UFS Specification.

**Related.** SCSI, COMMAND UPIU, opcode.

**See also.** [Module 03](03_upiu_command_flow.md)

### OCS (Overall Command Status)

**Definition.** UTRD 의 status 필드로, host controller 가 명령 처리 완료 시점에 SUCCESS / INVALID_COMMAND_TABLE_ATTRIBUTE / MISMATCH_DATA_BUFFER_SIZE 등의 코드를 기록한다.

**Source.** JEDEC UFS HCI Specification.

**Related.** UTRD, command status, response UPIU.

**See also.** [Module 02](02_hci_architecture.md)
