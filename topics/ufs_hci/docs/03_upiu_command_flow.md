# Module 03 — UPIU & Command Flow

<div class="learning-meta">
  <span class="meta-badge meta-level-advanced">📊 Advanced</span>
</div>

!!! objective "학습 목표"
    이 모듈을 마치면:

    - **Identify** UPIU의 6가지 종류 (Command/Response/Data In/Out/Task Mgmt/Query/NOP/Reject) 및 용도.
    - **Trace** READ / WRITE / QUERY UPIU의 전체 흐름을 host와 device 양측에서 추적.
    - **Apply** Task Tag (0-31)와 LUN으로 multi-command + multi-LU 시나리오를 작성.
    - **Distinguish** Sense Data, Response Code, Status Code의 의미와 fault 처리.

!!! info "사전 지식"
    - [Module 01-02](01_ufs_protocol_stack.md)
    - SCSI CDB 기본 (READ/WRITE/INQUIRY 등)

## 왜 이 모듈이 중요한가

**UPIU는 UFS의 통신 단위**. 모든 명령/응답/데이터가 UPIU로 캡슐화되므로 검증의 거의 모든 시나리오가 UPIU 정합성 + flow 정확성으로 귀결. **Task Tag 매칭 오류 = 잘못된 응답 매핑** — driver가 잘못된 command에 응답을 받으면 데이터 corruption 직결.

## 핵심 개념
**UPIU = UFS의 명령/데이터/응답을 담는 표준 패킷 형식. HCI가 SCSI CDB를 Command UPIU로 감싸서 전송하고, Device가 Response/Data UPIU로 응답. Task Tag(0~31)로 동시 32개 명령을 식별.**

---

## SCSI 명령과 UPIU 매핑

### 주요 SCSI 명령

| 명령 | CDB Opcode | 용도 | 데이터 방향 |
|------|-----------|------|-----------|
| READ(10) | 0x28 | 데이터 읽기 | Device → Host |
| WRITE(10) | 0x2A | 데이터 쓰기 | Host → Device |
| TEST UNIT READY | 0x00 | 디바이스 상태 확인 | 없음 |
| INQUIRY | 0x12 | 디바이스 정보 조회 | Device → Host |
| REQUEST SENSE | 0x03 | 에러 정보 조회 | Device → Host |
| SYNC CACHE | 0x35 | 캐시 플러시 | 없음 |
| UNMAP | 0x42 | 블록 해제 (TRIM) | Host → Device |
| START STOP UNIT | 0x1B | 전원 관리 | 없음 |

### READ 명령 UPIU 흐름

```
1. Command UPIU (Host → Device)
   +------------------------------------------+
   | Header:                                   |
   |   Transaction Type = 0x01 (Command)       |
   |   Task Tag = 5 (이 명령의 식별자)          |
   |   LUN = 0 (Boot LU 또는 User LU)         |
   | CDB:                                      |
   |   Opcode = 0x28 (READ_10)                |
   |   LBA = 0x1000 (읽을 위치)                |
   |   Transfer Length = 8 (8 블록 = 4KB)      |
   | Expected Data Length = 4096              |
   +------------------------------------------+

2. Data-In UPIU (Device → Host) × N개
   +------------------------------------------+
   | Header:                                   |
   |   Transaction Type = 0x02 (Data-In)       |
   |   Task Tag = 5 (같은 태그)                |
   | Data Segment:                             |
   |   읽은 데이터 (최대 PRDT 크기 단위)        |
   +------------------------------------------+

3. Response UPIU (Device → Host)
   +------------------------------------------+
   | Header:                                   |
   |   Transaction Type = 0x21 (Response)      |
   |   Task Tag = 5                            |
   |   Response = 0x00 (TARGET_SUCCESS)        |
   |   Status = 0x00 (GOOD)                   |
   | Residual Count = 0 (전부 전송 완료)       |
   +------------------------------------------+
```

### WRITE 명령 UPIU 흐름

```
1. Command UPIU (Host → Device)
   Opcode = 0x2A (WRITE_10), LBA, Length

2. RTT UPIU (Device → Host) — Ready to Transfer
   "데이터 보내도 좋다" 신호 + 전송 가능한 크기

3. Data-Out UPIU (Host → Device) × N개
   실제 쓰기 데이터

4. Response UPIU (Device → Host)
   완료 상태
```

---

## Well-Known LU (Logical Unit)

```
UFS Device는 여러 Logical Unit을 지원 — 각각 독립적인 "가상 디스크"

  +-----------------------------------------------+
  | UFS Device                                     |
  |                                                |
  | LUN 0: User LU 0 (주 저장 공간)               |
  | LUN 1: User LU 1 (옵션)                       |
  | LUN 2: User LU 2 (옵션)                       |
  | ...                                            |
  |                                                |
  | Well-Known LUs (특수 목적):                     |
  |   LUN 0xD0: Boot W-LU (Boot A)                |
  |   LUN 0xB0: RPMB W-LU                         |
  |   LUN 0x50: Device W-LU                        |
  +-----------------------------------------------+

Well-Known LU 상세:

  | W-LU | LUN | 용도 |
  |------|-----|------|
  | Boot W-LU A | 0xD0 (0x30+Well-Known) | Boot 이미지 저장 (Primary) |
  | Boot W-LU B | 0xD1 | Boot 이미지 저장 (Secondary/Recovery) |
  | RPMB W-LU | 0xB0 (0x44+Well-Known) | Replay Protected Memory Block — 보안 저장소 |
  | Device W-LU | 0x50 | 디바이스 레벨 설정 접근 |

Boot W-LU:
  - bBootLunEn Attribute로 활성화 여부 결정
  - Boot LU A 또는 B 선택 가능 (Fallback 용도)
  - BootROM이 READ 명령으로 BL2 이미지 로드

RPMB W-LU:
  - HMAC(SHA-256) 기반 인증된 Read/Write
  - Replay Attack 방지 (Write Counter)
  - Secure Storage 용도: 키, 인증서, 중요 설정
  - 일반 READ/WRITE가 아닌 SECURITY PROTOCOL IN/OUT 명령 사용
```

---

## NOP OUT / NOP IN 상세

```
NOP = No Operation — 링크 상태 확인 (Ping)

NOP OUT UPIU (Host → Device):
  +------------------------------------------+
  | Header:                                   |
  |   Transaction Type = 0x00 (NOP OUT)       |
  |   Task Tag = N                            |
  |   (나머지 필드는 Reserved/0)              |
  +------------------------------------------+
  | Data Segment: 없음                        |
  +------------------------------------------+

NOP IN UPIU (Device → Host):
  +------------------------------------------+
  | Header:                                   |
  |   Transaction Type = 0x20 (NOP IN)        |
  |   Task Tag = N (같은 태그)                |
  |   Response = 0x00 (SUCCESS)               |
  +------------------------------------------+
  | Data Segment: 없음                        |
  +------------------------------------------+

사용 시점:
  1. Link Startup 직후 — 디바이스 생존 확인
     → NOP IN 미응답 시 디바이스 비정상 → 재시도 또는 Fallback
  2. Idle 중 주기적 Ping — 링크 유지 확인
  3. Hibernate 복귀 후 — 링크 정상 동작 확인

흐름:
  SW: NOP OUT UTRD 작성 → Doorbell
  HCI: NOP OUT UPIU 전송 → Device
  Device: NOP IN UPIU 응답
  HCI: 완료 처리 → Interrupt
  SW: 응답 확인 (타임아웃 시 에러)
```

---

## Query 명령 — 디바이스 설정/상태

### Query UPIU 구조

```
Query Request UPIU (Host → Device):
  +------------------------------------------+
  | Header (12 bytes):                        |
  |   Transaction Type = 0x16 (Query Req)     |
  |   Task Tag = N                            |
  | Query Function (1B):                      |
  |   0x01 = Read Descriptor                  |
  |   0x02 = Write Descriptor                 |
  |   0x03 = Read Attribute                   |
  |   0x04 = Write Attribute                  |
  |   0x05 = Read Flag                        |
  |   0x06 = Set Flag                         |
  |   0x07 = Clear Flag                       |
  |   0x08 = Toggle Flag                      |
  | Descriptor Type / IDN (1B)                |
  | Index (1B)                                |
  | Selector (1B)                             |
  | Length (2B): 데이터 세그먼트 크기          |
  | Value (4B): Attribute 값 (Read/Write Attr)|
  +------------------------------------------+
  | Data Segment (가변):                       |
  |   Write Descriptor 시 → 쓸 Descriptor 데이터|
  +------------------------------------------+

Query Response UPIU (Device → Host):
  +------------------------------------------+
  | Header:                                   |
  |   Transaction Type = 0x36 (Query Resp)    |
  |   Task Tag = N                            |
  |   Query Response = 0x00 (Success)         |
  |                    0xF6 (Parameter Not Readable) |
  |                    0xFE (General Failure)  |
  | Value (4B): Attribute 값 (Read Attr 응답) |
  +------------------------------------------+
  | Data Segment (가변):                       |
  |   Read Descriptor 시 → 읽은 Descriptor 데이터|
  +------------------------------------------+
```

### Query 유형

| Query Function | 용도 | 예시 |
|---------------|------|------|
| Read Descriptor | 디바이스 정보 읽기 | Device Descriptor, Unit Descriptor |
| Write Descriptor | 디바이스 설정 변경 | Configuration Descriptor |
| Read Attribute | 속성 읽기 | bBootLunEn, bCurrentPowerMode |
| Write Attribute | 속성 변경 | bRefClkFreq |
| Read Flag | 플래그 읽기 | fDeviceInit, fPurgeEnable |
| Set/Clear/Toggle Flag | 플래그 변경 | fPurgeEnable 설정 |

### 부팅 관련 Query (BootROM 연결)

```
BootROM이 UFS 부팅 시 사용하는 Query:

  1. Read Attribute: bBootLunEn
     → Boot LU가 활성화되어 있는지 확인
     → 0이면 Boot 불가 → 다음 부팅 장치로 Fallback

  2. Read Descriptor: Unit Descriptor (Boot LU)
     → Boot LU의 크기, 블록 크기 확인

  3. READ(Boot LU): BL2 이미지 로드
```

---

## Task Management — 명령 제어

### Task Management 명령

| 명령 | 용도 | 시나리오 |
|------|------|---------|
| ABORT TASK | 특정 명령 중단 | 타임아웃된 명령 취소 |
| ABORT TASK SET | LUN의 모든 명령 중단 | LUN 단위 복구 |
| LOGICAL UNIT RESET | LUN 리셋 | LUN 오류 복구 |
| QUERY TASK | 명령 상태 조회 | 진행 상태 확인 |

```
Task Management 흐름:

  SW: UTMRD 작성 → UTMRLDBR 셋
  HCI: Task Mgmt UPIU 전송 → Device
  Device: 해당 명령 중단/리셋 → Task Mgmt Response
  HCI: UTMRD 업데이트 → Interrupt
  SW: ISR에서 완료 처리

  별도의 Doorbell(UTMRLDBR)과 별도의 Request List(UTMRL) 사용
  → Transfer Request와 독립적으로 처리
```

---

## 에러 처리 흐름

```
에러 감지 경로:

  1. UniPro Layer 에러
     - CRC 에러 → NAK → 재전송 (HCI 투명)
     - Link Down → IS[UE] 인터럽트 → SW 복구

  2. UPIU 레벨 에러
     - Response Status ≠ GOOD
     - Residual Count ≠ 0 (불완전 전송)
     → SW가 Response UPIU 확인 → 재시도 또는 에러 보고

  3. HCI 레벨 에러
     - DMA 에러 (PRDT 주소 잘못) → IS 인터럽트
     - 타임아웃 (Device 무응답) → SW가 Task Mgmt로 복구

에러 복구 단계:
  Level 1: 명령 재시도
  Level 2: Abort Task
  Level 3: LUN Reset
  Level 4: Host Reset (HCE 토글)
  Level 5: Full Link Reset (UniPro 재초기화)
```

---

## Device-Initiated 동작

```
UFS는 Host-initiated가 기본이지만, Device가 자발적으로 알리는 메커니즘도 있음:

  1. Attention (예외 이벤트 통지)
     - Device가 Host에게 "확인해야 할 이벤트가 있다" 알림
     - UniPro 레벨의 인터럽트 → IS[UE] 또는 별도 메커니즘
     - Host가 Query로 Exception Event Status 읽기:
       → Urgent BKOPS needed (백그라운드 작업 긴급)
       → Excessive Write → Performance throttling
       → Device Life Time 경고

  2. Background Operations (BKOPS)
     - Device가 내부적으로 수행하는 Garbage Collection, Wear Leveling 등
     - bBackgroundOpsStatus Attribute로 상태 확인:
       0x00 = Not required
       0x01 = Non-critical (idle 시 수행)
       0x02 = Performance impacted (빨리 수행 필요)
       0x03 = Critical (즉시 수행 필요)
     - Host가 fBackgroundOpsEn Flag를 Set → Device가 BKOPS 시작
     - Critical 상태를 무시하면 → Write 성능 급격히 하락

  3. Write Booster Flush
     - SLC 버퍼의 데이터를 TLC/QLC로 이동
     - Device가 자동으로 Idle 시 수행
     - Host가 강제로 트리거 가능: fWriteBoosterBufferFlushEn Flag

이 동작들은 검증 시 Device Agent가 시뮬레이션해야 하며,
Host Agent가 적절히 응답하는 시나리오를 포함해야 함.
```

---

## Q&A

**Q: UPIU의 Task Tag 역할은?**
> "동시에 처리 중인 최대 32개 명령을 식별하는 고유 ID다. Host가 Command UPIU에 Task Tag를 부여하면, Device는 해당 명령의 Data-In/Response UPIU에 같은 Task Tag를 붙여 반환한다. HCI가 이 Tag로 어떤 UTRD 슬롯의 응답인지를 매칭한다. 명령 큐잉의 핵심 메커니즘이다."

**Q: READ와 WRITE의 UPIU 흐름 차이는?**
> "READ: Command UPIU → Device가 바로 Data-In UPIU로 데이터 반환 → Response UPIU. WRITE: Command UPIU → Device가 먼저 RTT(Ready to Transfer) UPIU로 수신 준비 알림 → Host가 Data-Out UPIU로 데이터 전송 → Response UPIU. WRITE에 RTT가 있는 이유는 Device의 내부 버퍼 준비 상태를 확인하여 데이터 손실을 방지하기 위해서다."

**Q: UFS HCI의 에러 복구 단계를 설명하라.**
> "5단계 에스컬레이션: (1) 명령 재시도 — 같은 명령 재전송. (2) Abort Task — 특정 명령 취소. (3) LUN Reset — 해당 LUN의 모든 명령 취소 + LUN 리셋. (4) Host Reset — HCE 레지스터 토글로 HCI 전체 리셋. (5) Full Link Reset — UniPro/M-PHY 재초기화. 낮은 단계에서 해결되면 상위로 올라가지 않으며, 각 단계에서 Task Management UPIU를 사용한다."

**Q: RPMB(Replay Protected Memory Block)란 무엇이고 왜 중요한가?**
> "RPMB는 UFS Device 내의 보안 저장 영역(Well-Known LU)이다. 일반 READ/WRITE가 아닌 SECURITY PROTOCOL IN/OUT 명령으로 접근하며, HMAC(SHA-256) 인증과 Write Counter로 Replay Attack을 방지한다. 키, 인증서, 부팅 무결성 값 등 보안 데이터를 저장하는 데 사용되며, 인증 없이는 읽기/쓰기가 불가능하다. BootROM의 Secure Boot에서 OTP 대안으로 활용되기도 한다."

**Q: Query Request UPIU와 Command UPIU의 차이는?**
> "용도가 다르다. Command UPIU는 SCSI CDB를 전달하여 데이터 R/W를 수행하고, Query Request UPIU는 디바이스의 Descriptor/Attribute/Flag를 읽거나 변경한다. 구조적으로 Command UPIU는 16B CDB를 담지만, Query UPIU는 Query Function(Read/Write/Set/Clear) + IDN + Index + Selector + Value 형식이다. 데이터패스가 아닌 제어패스(컨트롤 플레인)에 해당한다."

**Q: WRITE에서 RTT(Ready to Transfer) UPIU가 필요한 이유는?**
> "Device의 내부 Write 버퍼 관리를 위해서다. Host가 일방적으로 데이터를 밀어넣으면 Device 버퍼 오버플로가 발생할 수 있다. RTT는 Device가 '이 만큼의 데이터를 보내도 된다'고 허가하는 흐름 제어 메커니즘이다. RTT의 Data Transfer Count 필드가 허용 크기를 지정하며, 대용량 WRITE는 여러 번의 RTT→Data-Out 반복으로 진행된다. READ에는 RTT가 없는 이유는 Host가 PRDT로 DMA 버퍼를 미리 할당해놓기 때문이다."

---

!!! warning "실무 주의점 — Task Tag 재사용 시점 오해"
    **현상**: 다른 LU 로 보낸 명령이 엉뚱한 LU 의 응답과 매칭되어 scoreboard mismatch 가 발생한다.

    **원인**: Response UPIU 수신만으로 Task Tag 를 재사용 가능하다고 판단했지만, 실제로는 OCS clear + UTRLDBR slot bit clear 까지 끝나야 free 상태다.

    **점검 포인트**: pending_tag table 을 OCS write-back 시점에만 갱신하는지, 같은 Tag 가 두 LU 로 동시에 발행되지 않는지 sequence-level assertion 으로 확인.

## 핵심 정리

- **UPIU 6종**: Command, Response, Data In/Out, Task Management, Query, NOP, Reject. 모든 명령은 UPIU로 캡슐.
- **UPIU 헤더**: Transaction Type, Flags, LUN, Task Tag, Command Set Type, Total EHS Length 등.
- **Task Tag (0-31)**: queue depth 32 — Task Tag로 동시 명령 식별. response의 Task Tag로 매칭.
- **READ flow**: Command UPIU (host→device) → Data In UPIU N개 (device→host) → Response UPIU.
- **WRITE flow**: Command UPIU → Ready-To-Transfer UPIU (device→host) → Data Out UPIU N개 (host→device) → Response UPIU.
- **QUERY**: device 속성 read/write (descriptor, attribute, flag).
- **Sense Data**: 명령 실패 시 상세 fail 원인. SCSI sense key + ASC/ASCQ.

## 다음 단계

- 📝 [**Module 03 퀴즈**](quiz/03_upiu_command_flow_quiz.md)
- ➡️ [**Module 04 — DV Methodology**](04_hci_dv_methodology.md)

<div class="chapter-nav">
  <a class="nav-prev" href="../02_hci_architecture/">
    <div class="nav-label">◀ 이전</div>
    <div class="nav-title">UFS HCI 아키텍처</div>
  </a>
  <a class="nav-next" href="../04_hci_dv_methodology/">
    <div class="nav-label">다음 ▶</div>
    <div class="nav-title">UFS HCI DV 검증 전략</div>
  </a>
</div>
