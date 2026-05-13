# UFS HCI — 개요 및 컨셉 맵

## 학습 플랜
- **레벨**: Intermediate → Advanced (UFS HCI IP Lead × 2 프로젝트 경험 기반)
- **목표**: UFS 프로토콜 스택과 HCI 내부 동작을 설명하고, Coverage-driven 검증 전략을 논리적으로 전개할 수 있는 수준

## 핵심 용어집 (Glossary)

### UFS 프로토콜 스택

| 약어 | 풀네임 | 설명 |
|------|--------|------|
| **UFS** | Universal Flash Storage | 모바일/서버용 고속 스토리지 표준 (2.9GB/s+) |
| **HCI** | Host Controller Interface | SW Driver와 UFS Device 사이의 인터페이스 |
| **UTP** | UFS Transport Protocol | SCSI 명령을 UPIU로 변환하는 전송 계층 |
| **UPIU** | UFS Protocol Information Unit | UFS의 표준 패킷 형식 |
| **UniPro** | Unified Protocol | UFS 링크 계층 (CRC, ACK, 흐름 제어) |
| **M-PHY** | MIPI Physical Layer | UFS 물리 계층 (시리얼 고속 인터페이스) |
| **DME** | Device Management Entity | UniPro 최상위 제어 엔티티 |

### HCI 레지스터 & 구조

| 약어 | 풀네임 | 설명 |
|------|--------|------|
| **UTRD** | UTP Transfer Request Descriptor | 전송 명령 메타데이터 (32B) |
| **UTMRD** | UTP Task Management Request Descriptor | Task 관리 명령 메타데이터 |
| **UCD** | UTP Command Descriptor | 명령 UPIU + Response + PRDT를 포함하는 구조 |
| **PRDT** | Physical Region Description Table | DMA 버퍼 주소/크기 리스트 |
| **Doorbell** | UTRLDBR | SW가 HCI에 처리 요청을 알리는 레지스터 |
| **IS** | Interrupt Status | 인터럽트 상태 (W1C: Write-1-to-Clear) |
| **MCQ** | Multi-Circular Queue | UFS 4.0의 다중 큐 (NVMe 유사) |

### 명령 & 프로토콜

| 약어 | 풀네임 | 설명 |
|------|--------|------|
| **SCSI** | Small Computer Systems Interface | 저장 장치 명령 표준 (READ_10, WRITE_10 등) |
| **CDB** | Command Descriptor Block | SCSI 명령 블록 |
| **LUN** | Logical Unit Number | UFS Device 내 논리 저장 공간 |
| **RTT** | Ready To Transfer | Device가 데이터 수신 준비 완료를 알리는 UPIU |
| **Query** | Query Request | 디바이스 Descriptor/Attribute/Flag 접근 명령 |
| **NOP** | No Operation | 링크 상태 확인 ping 명령 |
| **UIC** | UFS Interconnect Command | UniPro DME 계층 제어 명령 |

### PHY & 성능

| 약어 | 풀네임 | 설명 |
|------|--------|------|
| **HS/PWM** | High Speed / Pulse Width Modulation | M-PHY 속도 모드: HS(고속) vs PWM(저전력) |
| **Gear** | — | M-PHY 속도 단계 (G1~G5, 1.46~23.2Gbps) |
| **AFC** | Ack Flow Control | UniPro 크레딧 기반 흐름 제어 |
| **CDR** | Clock Data Recovery | HS 모드에서 데이터 신호로부터 클럭 복원 |

### 부가 기능

| 약어 | 풀네임 | 설명 |
|------|--------|------|
| **RPMB** | Replay Protected Memory Block | HMAC 기반 보안 저장 영역 |
| **WB** | Write Booster | SLC 임시 Write 캐시 (UFS 3.0+) |
| **HPB** | Host Performance Booster | Host의 L2P 맵 캐싱 (UFS 3.1+) |
| **eMMC** | embedded MultiMediaCard | UFS 이전 모바일 스토리지 표준 (400MB/s) |

---

## 컨셉 맵

```d2
direction: down

# unparsed: SW["<b>SW Driver (UFSHCD)</b><br/>(Linux Kernel)"]
# unparsed: HCI["<b>UFS HCI (Host Controller IF)</b><br/>· UTP (SCSI → UPIU)<br/>· Task Mgmt<br/>· DMA Engine<br/>· Interrupt"]
# unparsed: UNI["<b>UniPro (Link)</b><br/>· DME / L3 ~ L1.5"]
# unparsed: PHY["<b>M-PHY (Physical)</b><br/>· HS / PWM Gear"]
# unparsed: DEV["UFS Device"]
SW -> HCI: "Register / Doorbell"
HCI -> UNI: "UPIU (UFS Protocol Info Unit)"
UNI -> PHY
PHY -> DEV
```

## 학습 단위 (Units)

| # | 단위 | 핵심 질문 |
|---|------|----------|
| 1 | **UFS 프로토콜 스택** | UFS의 3계층(UTP/UniPro/M-PHY)은 어떻게 동작하는가? |
| 2 | **UFS HCI 아키텍처** | Host Controller는 SW 명령을 어떻게 UFS 프로토콜로 변환하는가? |
| 3 | **UPIU와 명령 처리 흐름** | SCSI 명령이 UPIU로 어떻게 변환되고, 응답은 어떻게 돌아오는가? |
| 4 | **UFS HCI DV 검증 전략** | Coverage-driven으로 HCI를 어떻게 검증하는가? |

## 이력서 연결

| 이력서 항목 | 관련 Unit | 면접 시 활용 |
|------------|----------|-------------|
| UFS HCI Lead × 2 (S5P9855, V920) | Unit 2, 4 | HCI 아키텍처 이해 + 검증 전략 |
| Coverage-driven TB | Unit 4 | Covergroup 설계 + Closure 전략 |
| BootROM UFS boot | Unit 1 | Boot LU 접근 + 초기화 시퀀스 |


--8<-- "abbreviations.md"
--8<-- "_inc/topic_abbr.md"
