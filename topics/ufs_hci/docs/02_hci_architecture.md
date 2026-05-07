# Module 02 — HCI Architecture

<div class="learning-meta">
  <span class="meta-badge meta-level-advanced">📊 Advanced</span>
</div>

!!! objective "학습 목표"
    이 모듈을 마치면:

    - **Diagram** UFS HCI의 핵심 요소(UTRD, UTMRD, doorbell register, interrupt aggregator)를 그릴 수 있다.
    - **Trace** SW driver의 명령 제출 → UTRD 작성 → doorbell ring → HCI 처리 흐름을 추적.
    - **Apply** Interrupt aggregation, multi-queue 활용으로 throughput 최적화 시나리오를 설계.
    - **Identify** UFS HCI register map의 핵심 영역(HCS/IS/UTRLBA/UTMRLBA 등).

!!! info "사전 지식"
    - [Module 01](01_ufs_protocol_stack.md)
    - DMA / queue-based command 모델
    - register-based HW interface (PCIe/AHB 비슷)

## 왜 이 모듈이 중요한가

**HCI는 SW와 UFS HW 사이의 표준 contract** (JEDEC JESD223). HCI 검증은 driver-side와 device-side의 인터페이스 정확성 + queue 관리 + interrupt 효율을 모두 보장. **UTRD parsing 오류 = silent corruption** — driver가 보낸 명령을 HCI가 잘못 해석하면 storage write/read에 직접 영향.

!!! tip "💡 이해를 위한 비유"
    **UFS HCI** ≈ **음식점의 주방 호출 시스템 — 주문서(UTRD) + 호출벨(doorbell) + 응답(completion)**

    Host 가 UTRD 를 메모리에 적고 doorbell ring → device(주방) 가 처리 → completion. 호출벨이 핵심 sync point.

---

## 핵심 개념
**UFS HCI = SW Driver(UFSHCD)와 UFS 프로토콜 사이의 HW 인터페이스. SW가 레지스터/메모리를 통해 SCSI 명령을 제출하면, HCI가 UPIU로 변환하여 UniPro/M-PHY를 통해 UFS Device에 전달. JEDEC JESD223 표준.**

!!! danger "❓ 흔한 오해"
    **오해**: Doorbell ring 즉시 처리된다

    **실제**: Doorbell ring 후 device 가 UTRD 를 fetch 하고 처리하는 데 latency 존재. ring 과 처리 시작은 다른 시점.

    **왜 헷갈리는가**: "링 = 즉시 시작" 이라는 직관. 실제로는 device 의 UTRL fetch + arbitration latency 있음.
---

## HCI 블록 다이어그램

```
+------------------------------------------------------------------+
|                        UFS HCI                                    |
|                                                                   |
|  SW Interface (AHB/AXI)                                           |
|  +------------------------------------------------------------+  |
|  | Host Controller Registers                                   |  |
|  |  - CAP (Capability)                                        |  |
|  |  - HCE (Host Controller Enable)                            |  |
|  |  - IS  (Interrupt Status)                                  |  |
|  |  - IE  (Interrupt Enable)                                  |  |
|  |  - UTRLBA (Transfer Request List Base Addr)                |  |
|  |  - UTRLDBR (Doorbell Register)                             |  |
|  |  - UTMRLBA (Task Mgmt Request List Base Addr)              |  |
|  +------------------------------------------------------------+  |
|           |                                                       |
|  +--------+-------+    +------------------+                       |
|  | UTP Transfer   |    | UTP Task Mgmt    |                       |
|  | Request Engine |    | Request Engine   |                       |
|  |                |    |                  |                       |
|  | - UTRD 파싱    |    | - UTMRD 파싱     |                       |
|  | - UPIU 생성    |    | - Task Mgmt UPIU |                       |
|  | - DMA (PRDT)   |    |   생성           |                       |
|  | - 완료 처리    |    |                  |                       |
|  +--------+-------+    +--------+---------+                       |
|           |                      |                                |
|  +--------+----------------------+--------+                       |
|  |              UPIU Engine                |                       |
|  |  - UPIU 패킷 조립/분해                 |                       |
|  |  - Command/Response/Data 처리           |                       |
|  +--------+-------------------------------+                       |
|           |                                                       |
|  +--------+-------------------------------+                       |
|  |           UniPro / M-PHY Interface      |                       |
|  +----------------------------------------+                       |
+------------------------------------------------------------------+
```

---

## 명령 처리 흐름 (READ 명령 예시)

```
1. SW: UTRD 작성 (시스템 메모리)
   +------------------------------------------+
   | UTP Transfer Request Descriptor (UTRD)    |
   |                                           |
   | - Command Type: SCSI Command              |
   | - Data Direction: Device → Host (READ)    |
   | - Overall Command Status: Invalid (초기)  |
   | - Command UPIU Offset/Length              |
   | - Response UPIU Offset/Length             |
   | - PRDT Offset/Length                      |
   +------------------------------------------+
   | Command UPIU (메모리에 배치)               |
   |  - Task Tag, LUN, CDB(READ_10)           |
   |  - Expected Data Transfer Length          |
   +------------------------------------------+
   | PRDT (Physical Region Description Table)  |
   |  - DMA 대상 버퍼 주소 + 크기 목록         |
   +------------------------------------------+

2. SW: Doorbell Register에 해당 슬롯 비트 셋
   UTRLDBR |= (1 << slot_number);
   → HCI에게 "이 슬롯의 UTRD를 처리하라" 신호

3. HCI: UTRD를 메모리에서 DMA로 읽기
4. HCI: Command UPIU 생성 → UniPro → M-PHY → Device
5. Device: READ 수행 → Data-In UPIU + Response UPIU 반환
6. HCI: Data-In을 PRDT 주소에 DMA 쓰기
7. HCI: Response UPIU를 UTRD의 Response 영역에 쓰기
8. HCI: UTRD의 Overall Command Status 업데이트
9. HCI: Interrupt 발생 (IS 레지스터)
10. SW: ISR에서 완료 처리
```

```
시간 흐름:

  SW              HCI              UniPro/Device
  |                |                |
  |--UTRD 작성---->|                |
  |--Doorbell 셋-->|                |
  |                |--UTRD DMA 읽기->|
  |                |--Cmd UPIU----->|
  |                |                |--READ 수행-->
  |                |<--Data-In UPIU-|
  |                |--DMA 쓰기------>|
  |                |<--Resp UPIU----|
  |                |--Status 업데이트|
  |<--Interrupt----|                |
  |--ISR 처리----->|                |
```

---

## UTRD 상세 필드 레이아웃

```
UTP Transfer Request Descriptor (UTRD) — 32 bytes

  Byte Offset   필드                          크기   설명
  ─────────────────────────────────────────────────────────────
  [0]           Command Type                  1B     0x01=SCSI, 0x02=UFS Native
  [1]           Reserved                      1B
  [2]           Data Direction                1B     0x00=None, 0x01=H→D, 0x02=D→H
  [3]           Reserved                      1B
  [4:7]         DW1 — PRDT Length             4B     PRDT 엔트리 수 (0-based)
  [8:11]        DW2 — Overall Command Status  4B     OCS: 0x0F=Invalid, 0x00=Success,
                                                      0x01=CC, 0x02=Fatal, 0x03=DevErr,
                                                      0x04=DevFatalErr, ...
  [12:15]       DW3 — Reserved                4B
  [16:19]       DW4 — Command UPIU            4B     UCD Base Address (하위 32-bit)
                      Base Address
  [20:23]       DW5 — Command UPIU            4B     UCD Base Address (상위 32-bit)
                      Base Address Upper
  [24:25]       DW6 — Response UPIU           2B     UCD 내 Response UPIU Offset (DW 단위)
                      Offset
  [26:27]              Response UPIU Length    2B     Response UPIU 크기 (DW 단위)
  [28:29]       DW7 — PRDT Offset             2B     UCD 내 PRDT Offset (DW 단위)
  [30:31]              PRDT Length             2B     PRDT 크기 (DW 단위)

UCD (UTP Command Descriptor) 메모리 레이아웃:
  +---------------------------------------------+
  | Command UPIU (32 bytes 헤더 + CDB 등)       | ← UCD Base Address
  +---------------------------------------------+
  | Response UPIU 영역 (미리 할당)              | ← UCD Base + Response Offset
  +---------------------------------------------+
  | PRDT (Physical Region Description Table)    | ← UCD Base + PRDT Offset
  +---------------------------------------------+
```

### PRDT Entry 형식

```
Physical Region Description Table Entry — 16 bytes

  Byte Offset   필드                          크기   설명
  ─────────────────────────────────────────────────────────────
  [0:3]         DW0 — Data Base Address       4B     데이터 버퍼 주소 (하위 32-bit)
  [4:7]         DW1 — Data Base Address Upper  4B     데이터 버퍼 주소 (상위 32-bit)
  [8:11]        DW2 — Reserved                4B
  [12:15]       DW3 — Data Byte Count         4B     [17:0] = 데이터 크기 (0-based)
                                                      최대 256KB per entry

PRDT 사용 예시:
  128KB READ → PRDT Entry 1개 (Data Byte Count = 0x1FFFF)
  512KB READ → PRDT Entry 2개 (각 256KB씩)

  DMA는 PRDT 리스트를 순차 처리:
    Entry[0] → 첫 256KB DMA 전송
    Entry[1] → 다음 256KB DMA 전송
    → 비연속 물리 메모리에 Scatter/Gather 가능
```

---

## HCE Enable/Disable 시퀀스

```
HCI 활성화 (Power-on → Ready):

  1. SW: HCE = 1 쓰기
  2. HCI: 내부 리셋 수행 + UniPro/M-PHY 초기화
  3. SW: HCS 폴링 — UCRDY=1 대기 (UIC Command Ready)
     └ 타임아웃 (600ms) 시 에러 처리
  4. SW: UIC Command — DME_LINKSTARTUP 발행
     └ UICCMD 레지스터에 명령 코드 쓰기
     └ IS[UCCS] 대기 (UIC Command Completion)
  5. SW: HCS.DP=1 확인 (Device Present)
  6. SW: UTRLBA/UTRLBAU 설정 (Transfer Request List 주소)
  7. SW: UTMRLBA/UTMRLBAU 설정 (Task Mgmt List 주소)
  8. SW: UTRLRSR = 1 (Transfer Request 수락 시작)
  9. SW: IE 레지스터 설정 (필요한 인터럽트 활성화)
  10. Ready — Doorbell 가능

HCI 비활성화 (Reset):

  1. SW: 진행 중인 모든 명령 완료 대기 (또는 Abort)
  2. SW: UTRLRSR = 0 (새 명령 수락 중지)
  3. SW: HCE = 0 쓰기
  4. HCI: 내부 리셋 → 모든 Doorbell 클리어, 레지스터 초기값
  5. SW: HCE = 1 (필요 시 재활성화) → 위 시퀀스 반복
```

---

## Interrupt 종류별 분류

```
IS (Interrupt Status) 레지스터 — 비트별 의미:

  Bit    약어     의미                              분류
  ─────────────────────────────────────────────────────────
  [0]    UTRCS   Transfer Request Completion       정상 완료
  [1]    UDEPRI  UIC DME Endpointpri               DME
  [2]    UE      UIC Error                         에러
  [3]    UTMS    Task Management Completion        Task Mgmt
  [4]    UPMS    UIC Power Mode Status             전력
  [5]    UHXS    UIC Hibernate Exit Status         전력
  [6]    UHES    UIC Hibernate Enter Status        전력
  [7]    ULLS    UIC Link Lost Status              에러
  [8]    ULSS    UIC Link Startup Status           초기화
  [9]    UTMRCS  Task Management Request           Task Mgmt
                 Completion Status
  [10]   UCCS    UIC Command Completion Status     UIC
  [11]   DFES    Device Fatal Error Status         에러
  [12]   UTPES   UTP Error Status                  에러
  [16]   HCFES   Host Controller Fatal Error       치명적 에러
  [17]   SBFES   System Bus Fatal Error            치명적 에러
  [18]   CEFES   Crypto Engine Fatal Error         치명적 에러

  인터럽트 처리 흐름:
    1. IRQ 발생 → ISR 진입
    2. IS 레지스터 읽기 → 어떤 비트가 셋되었는지 확인
    3. 해당 이벤트 처리 (예: UTRCS → 완료된 슬롯 확인)
    4. IS에 Write-1-to-Clear (W1C) → 해당 비트 클리어
    5. 추가 인터럽트 없으면 ISR 종료

  IE (Interrupt Enable) 마스킹:
    IE[N] = 0 → IS[N]이 셋되어도 IRQ 출력 안 됨
    IE[N] = 1 → IS[N] 셋 시 IRQ 출력
    → SW가 관심 있는 인터럽트만 선택적 활성화
```

---

## UIC Command 상세

```
UIC (UFS Interconnect) Command = UniPro DME 레이어 제어

  UICCMD 레지스터에 명령 코드 쓰기 → HCI가 UniPro에 DME 명령 전달

주요 UIC 명령:

  | 명령 코드 | 이름              | 용도                              |
  |----------|-------------------|-----------------------------------|
  | 0x01     | DME_GET           | UniPro 속성 읽기                  |
  | 0x02     | DME_SET           | UniPro 속성 쓰기                  |
  | 0x03     | DME_PEER_GET      | 상대측(Device) UniPro 속성 읽기   |
  | 0x04     | DME_PEER_SET      | 상대측(Device) UniPro 속성 쓰기   |
  | 0x10     | DME_POWERON       | M-PHY 전원 켜기                   |
  | 0x11     | DME_POWEROFF      | M-PHY 전원 끄기                   |
  | 0x12     | DME_ENABLE        | UniPro 링크 활성화                |
  | 0x16     | DME_LINKSTARTUP   | UniPro 링크 수립 시작             |
  | 0x17     | DME_HIBERNATE_ENTER | Hibernate 진입                  |
  | 0x18     | DME_HIBERNATE_EXIT  | Hibernate 복귀                  |
  | 0x20     | DME_ENDPOINTRESET | 상대측 리셋                       |

UIC Command 사용 흐름:

  1. SW: UICCMDARG1~3에 인자 설정
     - DME_GET/SET: MIB Attribute ID + Gen Selector Index
  2. SW: UICCMD에 명령 코드 쓰기 → 명령 시작
  3. HCI: UniPro DME에 명령 전달 → 결과 수신
  4. HCI: IS[UCCS] = 1 (UIC Command Completion)
  5. SW: UICCMDARG2에서 결과값 읽기 (GET의 경우)
  6. SW: UICCMDARG1에서 에러 코드 확인 (0=성공)

Gear 변경 예시 (HS-G1 → HS-G3):
  DME_SET(PA_TxGear, 3)        → TX Gear 3 설정
  DME_SET(PA_RxGear, 3)        → RX Gear 3 설정
  DME_SET(PA_HSSeries, 2)      → HS Series B
  DME_SET(PA_PWRMode, FAST)    → Power Mode 변경 트리거
  → IS[UPMS] 대기 (Power Mode Change 완료)
```

---

## 핵심 레지스터

| 레지스터 | 오프셋 | 역할 |
|---------|--------|------|
| **CAP** | 0x00 | 기능 정보 (슬롯 수, 64-bit 주소, MCQ 지원) |
| **VER** | 0x08 | HCI 스펙 버전 |
| **HCE** | 0x34 | Host Controller Enable (1=활성) |
| **HCS** | 0x30 | Host Controller Status (DP, UTRLRDY, UTMRLRDY) |
| **IE** | 0x38 | Interrupt Enable (비트별 인터럽트 활성) |
| **IS** | 0x20 | Interrupt Status (비트별 인터럽트 상태, W1C) |
| **UTRLBA** | 0x50 | Transfer Request List Base Address (하위 32-bit) |
| **UTRLBAU** | 0x54 | Transfer Request List Base Address (상위 32-bit) |
| **UTRLDBR** | 0x58 | Doorbell Register (비트 = 슬롯, SW가 셋 → HCI 처리) |
| **UTRLCLR** | 0x5C | Transfer Request List Clear |
| **UTMRLBA** | 0x70 | Task Management Request List Base Address |
| **UTMRLDBR** | 0x78 | Task Management Doorbell |
| **UICCMD** | 0x90 | UIC Command Register (UniPro DME 명령) |
| **UICCMDARG** | 0x94-9C | UIC Command Arguments |

### Doorbell 동작 원리

```
UTRLDBR (32-bit): 각 비트가 하나의 Transfer Request 슬롯

  bit[0] = slot 0
  bit[1] = slot 1
  ...
  bit[31] = slot 31

  SW가 bit[N] = 1 셋 → HCI가 slot N의 UTRD를 처리 시작
  HCI가 완료 → bit[N] = 0 클리어 + Interrupt

  명령 큐잉: 여러 비트를 동시에 셋 → 최대 32개 동시 처리
```

---

## MCQ (Multi-Circular Queue) — UFS 4.0+

```
기존 (SDB — Single Doorbell):
  하나의 Doorbell 레지스터 → 최대 32 슬롯
  모든 명령이 하나의 큐 → 순서 제약
  완료 확인: IS[UTRCS] → UTRLDBR 폴링 → 어떤 슬롯이 완료되었는지 확인
  병목: 모든 코어가 하나의 Doorbell/IS를 공유 → Lock 경합

MCQ (UFS 4.0):
  복수의 독립 큐 (Submission Queue + Completion Queue)
  → NVMe와 유사한 구조
  → 큐별 독립 처리 → 병렬성 향상
  → 멀티코어 환경에서 큐별 코어 바인딩 가능 → Lock-free

  +------------------+     +------------------+
  | SQ 0 (Core 0)   | --> | CQ 0             |
  +------------------+     +------------------+
  | SQ 1 (Core 1)   | --> | CQ 1             |
  +------------------+     +------------------+
  | ...              |     | ...              |
  +------------------+     +------------------+
```

### SQ/CQ Entry 형식과 Head/Tail Pointer

```
Submission Queue (SQ) Entry = UTRD와 동일한 구조 (32 bytes)

  SW가 SQ에 엔트리 추가하는 방법:
    1. SQ[Tail Pointer] 위치에 UTRD 작성
    2. SQ Tail Pointer += 1 (Doorbell 레지스터에 쓰기)
    3. HCI가 SQ[Head Pointer]부터 Tail까지 처리
    4. HCI가 처리 완료 → Head Pointer 전진

  SQ 순환 구조:
    +---+---+---+---+---+---+---+---+
    | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | ← SQ Depth (예: 8)
    +---+---+---+---+---+---+---+---+
          ^           ^
          Head        Tail
          (HCI 처리)  (SW 추가)

    Tail == Head → 큐 비어있음
    Tail + 1 == Head → 큐 가득 참 (1개 엔트리 여유)

Completion Queue (CQ) Entry — 16 bytes:

  Byte Offset   필드                          크기
  ─────────────────────────────────────────────────
  [0:3]         DW0 — Overall Command Status  4B     OCS + 에러 코드
  [4:7]         DW1 — SQ ID + SQ Head Ptr     4B     어떤 SQ의 어떤 위치 명령인지
  [8:11]        DW2 — Response UPIU Info      4B     Response 상태 요약
  [12:15]       DW3 — Reserved                4B

  HCI가 CQ에 완료 엔트리 추가:
    1. CQ[CQ Tail Pointer]에 완료 정보 쓰기
    2. CQ Tail Pointer 전진 + 인터럽트
    3. SW가 CQ[CQ Head Pointer]에서 완료 정보 읽기
    4. SW가 CQ Head Pointer 전진 (CQ Doorbell에 쓰기)

SDB vs MCQ 비교:

  | 항목 | SDB (기존) | MCQ (UFS 4.0+) |
  |------|-----------|----------------|
  | 큐 수 | 1 | 최대 8+ (구현에 따라) |
  | 최대 명령 | 32 | 큐당 깊이 × 큐 수 |
  | 완료 확인 | IS[UTRCS] + UTRLDBR 폴링 | CQ Entry 직접 읽기 |
  | 멀티코어 | Lock 경합 | 큐별 코어 바인딩 (Lock-free) |
  | 오버헤드 | Doorbell 1회 쓰기 | Tail Pointer 1회 쓰기 |
  | 완료 정보 | OCS만 (UTRD 읽기 필요) | CQ Entry에 요약 포함 |
```

---

## Q&A

**Q: UFS HCI의 역할을 한마디로?**
> "SW Driver와 UFS 프로토콜 사이의 하드웨어 브릿지다. SW가 메모리에 UTRD(명령 디스크립터)를 작성하고 Doorbell을 누르면, HCI가 이를 DMA로 읽어 UPIU 패킷으로 변환하여 UniPro를 통해 디바이스에 전달하고, 응답을 받아 메모리에 DMA로 쓰고 Interrupt로 SW에 알린다."

**Q: Doorbell 메커니즘이 왜 중요한가?**
> "Doorbell은 SW→HW 명령 제출의 핵심 인터페이스다. SW가 UTRD를 메모리에 미리 작성해두고 Doorbell 비트만 셋하면 HCI가 처리를 시작한다. 이 분리(디스크립터 작성 ↔ 처리 시작 통지)가 명령 큐잉(최대 32개 동시)을 가능하게 한다. MCQ(UFS 4.0)는 이를 복수 큐로 확장하여 멀티코어 병렬성을 더욱 높인다."

**Q: UTRD, UCD, PRDT의 관계는?**
> "3계층 메모리 구조다. UTRD(32B)가 명령의 메타데이터(Command Type, Direction, OCS)를 담고, UCD(UTP Command Descriptor)의 Base Address를 가리킨다. UCD 안에 Command UPIU(SCSI CDB 포함), Response UPIU 공간, PRDT가 순서대로 배치된다. PRDT는 DMA 대상 버퍼의 주소+크기 목록으로, 비연속 물리 메모리에 Scatter/Gather 전송을 가능하게 한다. HCI는 Doorbell을 받으면 UTRD→UCD→PRDT 순으로 메모리를 DMA 읽기한다."

**Q: SDB에서 MCQ로 전환된 이유와 핵심 차이는?**
> "멀티코어 환경에서의 Lock 경합 해소가 핵심이다. SDB는 하나의 Doorbell 레지스터를 모든 코어가 공유하므로 Lock이 필요하고, 완료 확인도 IS+UTRLDBR 폴링으로 비효율적이다. MCQ는 NVMe처럼 큐별 독립 Submission/Completion Queue를 두어 코어별 큐 바인딩이 가능하고 Lock-free로 동작한다. 완료 정보도 CQ Entry에 직접 담겨 UTRD 재읽기가 불필요하다."

**Q: UIC Command로 Gear를 변경하는 과정을 설명하라.**
> "UIC Command는 HCI가 UniPro DME 레이어를 제어하는 인터페이스다. Gear 변경 과정: (1) DME_SET으로 PA_TxGear, PA_RxGear를 원하는 Gear 값으로 설정. (2) DME_SET으로 PA_PWRMode를 FAST로 설정하면 UniPro가 M-PHY Gear 전환을 시작. (3) IS[UPMS] (Power Mode Status) 인터럽트 대기. (4) HCS에서 새로운 Power Mode 확인. 각 DME_SET마다 IS[UCCS]로 완료를 확인해야 하며, Gear 전환 중에는 명령 발행을 자제해야 한다."

---
!!! warning "실무 주의점 — UTRLDBR 와 UTRLRSR race"
    **현상**: 명령을 doorbell 로 발행했는데 HCI 가 해당 슬롯을 무시해 명령이 실종된다.

    **원인**: UTRLDBR set 직후 UTRLRSR(Run/Stop) 의 busy 상태를 확인하지 않아, run-stop 토글 타이밍과 race 가 발생한다.

    **점검 포인트**: UTRLDBR write 전 UTRLRSR == 1 인지, UTRD 가 메모리에 fully visible 한지(memory barrier) 드라이버 시퀀스에서 확인.

## 핵심 정리

- **HCI register map**: HCS (status), IS (interrupt), UTRLBA (UTRD list base), UTMRLBA (Task Management list base), CAP (capabilities).
- **UTRD (UTP Transfer Request Descriptor)**: SW가 작성하는 32-byte 구조 — 명령 + UPIU pointer + response pointer.
- **UTMRD**: Task Management 명령용 (abort, reset 등).
- **Doorbell**: SW가 UTRD 작성 후 doorbell register write로 HCI에 알림.
- **Interrupt aggregation**: 여러 명령 완료를 모아서 한 인터럽트로 → CPU overhead 감소. Counter / timer 기반 trigger.
- **Multi-queue**: UFS는 queue depth 32. HCI가 동시에 32 명령 처리 가능.

## 다음 단계

- 📝 [**Module 02 퀴즈**](quiz/02_hci_architecture_quiz.md)
- ➡️ [**Module 03 — UPIU & Command Flow**](03_upiu_command_flow.md)

<div class="chapter-nav">
  <a class="nav-prev" href="../01_ufs_protocol_stack/">
    <div class="nav-label">◀ 이전</div>
    <div class="nav-title">UFS 프로토콜 스택</div>
  </a>
  <a class="nav-next" href="../03_upiu_command_flow/">
    <div class="nav-label">다음 ▶</div>
    <div class="nav-title">UPIU와 명령 처리 흐름</div>
  </a>
</div>
