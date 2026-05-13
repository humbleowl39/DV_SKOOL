# Module 02 — HCI Architecture

<!-- DV-SKOOL-CH-CTX:start -->
<div class="chapter-context" data-cat="memory">
  <a class="chapter-back" href="../">
    <span class="chapter-back-arrow">←</span>
    <span class="chapter-back-icon">💿</span>
    <span class="chapter-back-text">UFS HCI</span>
  </a>
  <span class="chapter-divider">›</span>
  <span class="chapter-marker">Module 02</span>
</div>
<!-- DV-SKOOL-CH-CTX:end -->

<!-- DV-SKOOL-CH-TOC:start -->
<div class="page-toc">
  <span class="page-toc-label">목차</span>
  <a class="page-toc-link" href="#1-why-care-이-모듈이-왜-필요한가">1. Why care?</a>
  <a class="page-toc-link" href="#2-intuition-비유와-한-장-그림">2. Intuition</a>
  <a class="page-toc-link" href="#3-작은-예-utp-transfer-cycle-한-건">3. 작은 예 — UTP transfer cycle 한 건</a>
  <a class="page-toc-link" href="#4-일반화-utrd-doorbell-irq-의-한-주기-모델">4. 일반화 — UTRD/Doorbell/IRQ 모델</a>
  <a class="page-toc-link" href="#5-디테일-utrd-prdt-utmrd-uic-mcq">5. 디테일</a>
  <a class="page-toc-link" href="#6-흔한-오해-와-dv-디버그-체크리스트">6. 흔한 오해 + DV 디버그 체크리스트</a>
  <a class="page-toc-link" href="#7-핵심-정리-key-takeaways">7. 핵심 정리</a>
</div>
<!-- DV-SKOOL-CH-TOC:end -->

!!! objective "학습 목표"
    이 모듈을 마치면:

    - **Diagram** UFS HCI 의 핵심 요소 (UTRD, UTMRD, doorbell register, interrupt aggregator) 를 그릴 수 있다.
    - **Trace** SW driver 의 명령 제출 → UTRD 작성 → doorbell ring → HCI 처리 흐름을 추적한다.
    - **Apply** Interrupt aggregation, multi-queue 활용으로 throughput 최적화 시나리오를 설계한다.
    - **Identify** UFS HCI register map 의 핵심 영역 (HCS / IS / UTRLBA / UTMRLBA 등).
    - **Justify** HCE / UTRLRSR / Doorbell 의 분리가 왜 필요한지 (race / ordering 관점).

!!! info "사전 지식"
    - [Module 01](01_ufs_protocol_stack.md)
    - DMA / queue-based command 모델
    - register-based HW interface (PCIe / AHB 비슷)

---

## 1. Why care? — 이 모듈이 왜 필요한가

### 1.1 시나리오 — UTRD _1 bit_ 의 silent corruption

당신은 UFS storage. Driver 가 _UTRD descriptor_ 에 _data buffer address_ 작성:
```
UTRD field: data_addr[63:0] = 0x1000_0000_0000_0000
```

HCI 가 _bit 32_ 만 0 으로 해석:
```
실제 사용: 0x0000_0000_0000_0000
```

결과: data 가 _wrong physical address_ 에 write → memory corruption → 다른 process 데이터 깨짐.

증상:
- 일부 sector 만 corrupt.
- _시뮬에서 안 잡힘_ (test 가 _high address_ 안 씀).
- _Production_ 에서 _수 시간_ 후 발견.

UTRD parsing 의 _1 bit_ 가 _silent corruption_. JEDEC spec 의 _모든 field_ 정확히 해석돼야 안전.

**HCI 는 SW 와 UFS HW 사이의 _표준 contract_** (JEDEC JESD223) 입니다. 어떤 OS, 어떤 driver 를 쓰더라도 이 contract 만 지키면 명령이 통합니다. 그래서 HCI 를 검증한다는 것은 곧 **driver-side (register / UTRD) ↔ device-side (UPIU)** 양방향 contract 를 검증한다는 뜻입니다.

UTRD parsing 한 비트만 잘못 해석되면 storage 의 read/write 데이터가 silently 망가집니다. 그래서 register layout, UTRD field, doorbell 동작, interrupt 의미를 정확히 잡지 못하면 이후의 어떤 시나리오 / coverage / SVA 도 안전망이 못 됩니다. 이 모듈이 그 contract 의 어휘를 정착시키는 자리.

---

## 2. Intuition — 비유와 한 장 그림

!!! tip "💡 한 줄 비유"
    **UFS HCI** = 음식점 주방 호출 시스템. 주문서(**UTRD**) 를 카운터(**system memory**) 위에 올려두고 호출벨(**doorbell register**) 을 한 번 누르면, 주방(**HCI engine**) 이 알아서 주문서를 읽고 요리 후 응답(**Response UPIU + IRQ**) 을 다시 카운터에 올림. 주문서 작성과 호출벨이 _분리_ 돼 있어 손님은 주문서 32 장을 먼저 다 적어두고 한 번에 누를 수도 있음 (= command queueing).

### 한 장 그림 — HCI 의 SW/HW 인터페이스

```d2
direction: down

HCI: "UFS HCI" {
  direction: down
  REG: "**Host Controller Registers** (SW Interface · AHB/AXI)\nCAP · HCE · IS · IE\nUTRLBA · UTRLDBR · UTMRLBA"
  XFER: "**UTP Transfer Request Engine**\n· UTRD 파싱\n· UPIU 생성\n· DMA (PRDT)\n· 완료 처리"
  TM: "**UTP Task Mgmt Request Engine**\n· UTMRD 파싱\n· Task Mgmt UPIU 생성"
  UPIU: "**UPIU Engine**\n· UPIU 패킷 조립 / 분해\n· Command / Response / Data 처리"
  IF: "**UniPro / M-PHY Interface**"
  REG -> XFER
  REG -> TM
  XFER -> UPIU
  TM -> UPIU
  UPIU -> IF
}
```

### 왜 이 디자인인가 — Design rationale

**SW/HW 분리의 비대칭성** 때문입니다. SW (driver) 는 명령 32 개를 빠르게 작성할 수 있지만, HW 가 명령을 처리하는 속도는 NAND latency / link gear 에 따라 변동이 큽니다. 그래서 두 가지를 분리해야 합니다.

1. **명령 작성 (메모리 write)** = SW 가 자유롭게 쌓아 두는 작업.
2. **처리 시작 (doorbell ring)** = SW 가 한 번 알리면 HW 가 알아서 fetch.
3. **완료 통지 (IRQ + UTRLDBR clear)** = HW 가 비동기로 SW 에 알림.

이 셋이 _별도 register_ (UTRLBA / UTRLDBR / IS) 로 나뉘어 있어 SW 가 명령을 batched 로 쌓고, HW 가 own pace 로 처리하고, 둘 사이의 race 를 register-level 로 검증할 수 있습니다.

---

## 3. 작은 예 — UTP transfer cycle 한 건

가장 단순한 시나리오. SW 가 slot=5 에 READ 명령을 발행 → HCI 가 처리 → ISR 에서 회수. 한 cycle 의 모든 register / memory transition 을 추적합니다.

```d2
shape: sequence_diagram

SW: "SW Driver (CPU)"
HCI: "HCI engine (HW)"

# Note over SW: 1. UTRD@slot=5 작성 in system memory\n(OCS=INVALID 0x0F)
# Note over SW: 2. mb() + UCD/PRDT fully visible
# Note over HCI: 4. doorbell sense\n5. UTRD DMA fetch (UTRLBA + 5*32B)\n6. UCD/PRDT fetch\n7. Cmd UPIU 조립 → UniPro TX
# Note over HCI: 8. Data-In UPIU × N\n→ DMA write to PRDT addr
# Note over HCI: 9. Response UPIU\n→ UTRD.OCS 갱신
# Note over HCI: 10. UTRLDBR[5] = 0 + IS[UTRCS] = 1
# Note over SW: 12. ISR: read IS\n→ check UTRLDBR\n→ read UTRD.OCS\n→ IS 에 W1C\n→ buffer 반환
SW -> HCI: "3. UTRLDBR |= (1<<5)  — ring"
HCI -> SW: "11. IRQ" { style.stroke-dash: 4 }
```

### 단계별 추적 표

| Step | 누가 | 무엇을 | 의미 / 검증 포인트 |
|---|---|---|---|
| ① | SW | UTRD slot 5 에 32 B 작성 (Cmd Type, Direction, OCS=0x0F, UCD ptr) | OCS 초기값이 INVALID 여야 — HCI 가 처리 후 갱신 |
| ② | SW | Memory barrier — UCD / PRDT 가 HCI 에서 보일 것 | TB 에서도 ordering monitor 필요 |
| ③ | SW | `UTRLDBR[5] = 1` (W1S — write-1-to-set) | 다른 비트 영향 없는지 확인 |
| ④ | HCI | Doorbell rising edge 감지 | $rose(UTRLDBR[5]) SVA |
| ⑤ | HCI | UTRD DMA fetch — `UTRLBA + 5×32` | 64-bit 모드면 UTRLBAU 도 사용 |
| ⑥ | HCI | UCD base + PRDT offset 으로 fetch | UCD 안의 layout 정합성 |
| ⑦ | HCI | Cmd UPIU 조립 → UniPro 로 hand-off | Task Tag = slot 5 |
| ⑧ | HCI | Data-In UPIU 받아 PRDT 주소로 DMA write | Scatter/gather 정확성 |
| ⑨ | HCI | Response UPIU 의 Status → UTRD.OCS 갱신 | OCS = 0x00 (SUCCESS) 또는 에러 코드 |
| ⑩ | HCI | UTRLDBR[5] auto clear + IS[UTRCS] set | atomicity 가 ⑪ 직전이어야 |
| ⑪ | HCI | IRQ 출력 (IE[UTRCS] 가 1 일 때만) | mask 동작 확인 |
| ⑫ | SW | ISR 에서 IS / UTRLDBR / UTRD.OCS 순서 read + IS W1C | race 시나리오의 핵심 |

```c
// SW 측 ① ~ ③ 의 골격
struct utp_transfer_req_desc *utrd = &utrl[slot];
build_utrd(utrd, /*cmd_type=*/SCSI, /*dir=*/D2H,
           /*ucd_paddr=*/ucd_phys, /*prdt_offset=*/..., /*prdt_len=*/1);
utrd->ocs = OCS_INVALID;                   // ①
wmb();                                      // ② memory barrier
hci_writel(BIT(slot), UTRLDBR);             // ③ doorbell
// ⑫ ISR
u32 is = hci_readl(IS);
if (is & IS_UTRCS) {
    u32 done = ~hci_readl(UTRLDBR) & active_mask;
    for_each_set_bit(s, &done, 32) handle_ocs(&utrl[s]);
    hci_writel(IS_UTRCS, IS);               // W1C
}
```

!!! note "여기서 잡아야 할 두 가지"
    **(1) UTRD 작성과 doorbell 사이의 _memory barrier_ 가 핵심 invariant** 다. HCI 가 UTRD 를 fetch 했을 때 UCD / PRDT 가 모두 visible 해야 함. TB 의 host agent 도 이 ordering 을 모델링해야 silent corruption 시나리오를 catch. <br>
    **(2) 완료 통지는 _두 곳_ 에서 동시에** 일어난다. (a) UTRLDBR slot bit clear, (b) IS[UTRCS] set + IRQ. ISR 은 _(b) 만 보고_ 동작하지 말고 (a) 도 함께 확인해야 어떤 슬롯이 완료됐는지 알 수 있다.

---

## 4. 일반화 — UTRD / Doorbell / IRQ 의 한 주기 모델

### 4.1 한 transfer 의 7 phase

| Phase | SW 측 register/memory | HCI 측 동작 |
|-------|----------------------|------------|
| **P1: Prepare** | UTRD 작성, OCS=INVALID | (idle) |
| **P2: Submit** | wmb() + UTRLDBR[s] = 1 | doorbell 감지 |
| **P3: Fetch** | (대기) | UTRD / UCD / PRDT DMA fetch |
| **P4: Transport** | (대기) | UPIU ↔ UniPro 송수신 |
| **P5: DMA** | (대기) | Data-In/Out 을 PRDT addr 로 DMA |
| **P6: Complete** | (대기) | OCS write, UTRLDBR[s] = 0, IS[UTRCS] = 1 |
| **P7: ISR** | IS read → UTRLDBR poll → OCS read → IS W1C | (idle) |

이 7 phase 가 **모든 transfer 명령** (READ/WRITE/QUERY/NOP) 의 공통 골격입니다. WRITE 만 P4 에 RTT → Data-Out 의 sub-step 이 추가되고, NOP 은 P5 가 생략됩니다 — 차이는 _UPIU 종류_ 뿐 phase 자체는 동일.

### 4.2 명령 큐잉 — 32 슬롯의 의미

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

큐잉의 의미 = **여러 transfer 가 P3 ~ P5 에서 시간적으로 _겹친다_**. 그래서 같은 slot 이 두 번 사용되지 않도록 SW 가 책임지며, 완료 순서는 HCI 가 결정 (out-of-order completion 가능).

### 4.3 HCE Enable / Disable 시퀀스

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

**HCE / UTRLRSR / Doorbell 이 분리된 이유** = 각자 다른 timing 에 작용. HCE 는 chip-wide reset, UTRLRSR 은 transfer accept 게이트, Doorbell 은 per-slot 트리거. 이 분리가 보장되지 않으면 Gear 변경/Hibernate/Reset 도중 명령이 실종됩니다.

---

## 5. 디테일 — UTRD / PRDT / UTMRD / UIC / MCQ

### 5.1 UTRD 상세 필드 레이아웃

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

### 5.2 PRDT Entry 형식

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

### 5.3 Interrupt 종류별 분류

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

### 5.4 UIC Command 상세

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

### 5.5 핵심 레지스터 맵

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

### 5.6 MCQ (Multi-Circular Queue) — UFS 4.0+

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

```

```d2
direction: right

SQ0: "SQ 0 (Core 0)"
CQ0: "CQ 0"
SQ0 -> CQ0
SQ1: "SQ 1 (Core 1)"
CQ1: "CQ 1"
SQ1 -> CQ1
SQN: "SQ N (Core N)"
CQN: "CQ N"
SQN -> CQN
```

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

## 6. 흔한 오해 와 DV 디버그 체크리스트

### 흔한 오해

!!! danger "❓ 오해 1 — 'Doorbell ring 즉시 처리된다'"
    **실제**: Doorbell ring 후 HCI 가 해당 슬롯의 UTRD 를 fetch 하고 처리하기까지 **arbitration latency** 가 존재합니다. 다른 슬롯이 진행 중이면 그만큼 지연. ring 시점과 처리 시작 시점은 다른 transaction. SVA 의 timing 도 `##[1:N]` 으로 윈도우를 줘야지 `##1` 로 잡으면 false fail.<br>
    **왜 헷갈리는가**: "링 = 즉시 시작" 이라는 직관.

!!! danger "❓ 오해 2 — 'UTRD 작성하고 doorbell 만 누르면 끝'"
    **실제**: UTRD ↔ UCD ↔ PRDT 의 **3 단 메모리 구조** 가 모두 visible 해야 합니다. CPU 의 store 가 HCI 의 fetch path 에서 완전히 보이려면 _memory barrier_ 또는 _coherent dma alloc_ 이 필요. write-back cache + non-coherent DMA 환경에서는 cache flush 까지.<br>
    **왜 헷갈리는가**: register write 의 instantaneous 한 인상이 메모리 ordering 까지 같은 것처럼 보이게 함.

!!! danger "❓ 오해 3 — 'IS[UTRCS] 만 보면 어떤 슬롯이 완료됐는지 안다'"
    **실제**: IS[UTRCS] 는 _하나 이상의_ transfer 가 완료됐다는 _aggregated bit_ 입니다. 어떤 슬롯이 완료됐는지는 **UTRLDBR 의 어떤 비트가 0 으로 떨어졌는가** 로 알아야 합니다. ISR 은 둘 다 봐야 정확.<br>
    **왜 헷갈리는가**: NVMe 의 CQ entry 처럼 1:1 매핑된 통지 모델을 가정.

!!! danger "❓ 오해 4 — 'HCE = 0 → 1 한 번이면 깨끗한 상태'"
    **실제**: HCE 는 _internal reset 트리거_ 일 뿐, UniPro / M-PHY 까지 다시 link startup 하려면 DME_LINKSTARTUP 시퀀스가 필요합니다. UTRLBA / UTMRLBA / IE 도 0 으로 돌아가므로 모두 다시 program. 이 순서 (HCE → UCRDY 폴링 → DME_LINKSTARTUP → UTRLBA 등) 를 어기면 Doorbell 이 무시됩니다.<br>
    **왜 헷갈리는가**: "reset 한 번 = 모든 게 새로" 라는 직관.

!!! danger "❓ 오해 5 — 'MCQ 는 SDB 의 단순 확장'"
    **실제**: MCQ 는 doorbell register 자체가 사라지고 **SQ Tail Pointer** 가 doorbell 역할을 합니다. 완료 통지도 CQ entry write + interrupt 로 바뀌어 UTRLDBR poll 이 불필요. 완전히 다른 contract — driver 와 TB 모두 별도 path 가 필요.<br>
    **왜 헷갈리는가**: 이름은 같아도 register / 메모리 구조 / 완료 통지가 모두 다름.

### DV 디버그 체크리스트 (이 모듈 내용으로 마주칠 첫 실패)

| 증상 | 1차 의심 | 어디 보나 |
|---|---|---|
| Doorbell 이 무시됨 (HCI 가 처리 안 함) | UTRLRSR = 0, HCE 미활성, UTRLBA 미설정 | HCS.UTRLRDY, UTRLRSR, UTRLBA |
| UTRD.OCS = 0x0F 로 영원히 남음 | HCI 가 UTRD fetch 했는데 UCD ptr 잘못 | UTRD DW4/DW5 (UCD Base Addr) |
| 완료 IRQ 가 안 옴 | IE[UTRCS] = 0 (mask 닫힘) | IE 와 IS 비트 비교 |
| ISR 진입 후 어떤 슬롯인지 모름 | IS 만 읽고 UTRLDBR 안 읽음 | UTRLDBR 의 active vs cleared 비트 |
| 같은 slot 에 두 명령 발행 | SW 의 free-slot tracker 버그 | pending bitmap 과 UTRLDBR 비교 |
| HCE 토글 후 명령이 실종 | UTRLBA 재설정 안 함 | HCE rising edge 이후 UTRLBA write 시퀀스 |
| MCQ 모드인데 UTRLDBR poll | SDB 코드가 그대로 남음 | CAP.MCQS, 사용 중 path 확인 |
| Crypto Engine 활성 시 fatal 발생 | UTRD 의 Crypto Config Index 가 미할당 | CEFES bit, Crypto Config 영역 |

이 체크리스트의 모든 항목은 **register write 와 memory write 의 ordering** 또는 **mask/enable 비트의 닫힘** 두 가지로 분류됩니다.

---

## 7. 핵심 정리 (Key Takeaways)

- **HCI register map**: HCE / HCS / IS / IE / UTRLBA / UTRLDBR / UTMRLBA / UICCMD — _SW/HW contract_ 의 어휘.
- **UTRD (32 B)** = 명령 + UCD pointer + PRDT pointer + OCS. HCI 가 fetch → 처리 → OCS writeback.
- **Doorbell + UTRLDBR + IRQ** 의 분리 — 명령 작성, 처리 시작, 완료 통지가 별도 register 로 분리돼 race-aware 검증 가능.
- **PRDT** 는 scatter/gather DMA 의 entry list — 비연속 물리 메모리에 256 KB 단위로 분할 가능.
- **UIC Command** 가 HCI 에서 UniPro DME 로 가는 유일한 통로 — Gear / Hibernate / Link 관리 모두 여기.
- **MCQ (4.0+)** 는 NVMe-style SQ/CQ 분리. doorbell 이 사라지고 Tail Pointer 가 그 역할 — driver / TB 구조가 통째로 바뀜.

!!! warning "실무 주의점 — UTRLDBR 와 UTRLRSR race"
    **현상**: 명령을 doorbell 로 발행했는데 HCI 가 해당 슬롯을 무시해 명령이 실종된다.

    **원인**: UTRLDBR set 직후 UTRLRSR(Run/Stop) 의 busy 상태를 확인하지 않아, run-stop 토글 타이밍과 race 가 발생한다.

    **점검 포인트**: UTRLDBR write 전 UTRLRSR == 1 인지, UTRD 가 메모리에 fully visible 한지(memory barrier) 드라이버 시퀀스에서 확인.

### 7.1 자가 점검

!!! question "🤔 Q1 — 32-slot queueing (Bloom: Apply)"
    HCI 가 32 UTRD slot. 33번째 command 어떻게?

    ??? success "정답"
        - **Slot wait**: SW driver 가 _완료된 slot_ 까지 wait. CQ poll.
        - Slot 회수 → 새 command 발행.
        - 또는 **MCQ (UFS 4.0+)**: SQ/CQ ring → 32 한계 _제거_, driver 가 _수천_ outstanding 가능.

!!! question "🤔 Q2 — Doorbell ordering (Bloom: Analyze)"
    Driver: UTRD write → memory barrier → doorbell. _Memory barrier 누락_ 시?

    ??? success "정답"
        **UTRD 가 메모리에 fully visible 안 된 상태에서 HCI fetch**.

        - HCI 가 _doorbell_ 보고 _UTRD fetch_ 시도.
        - CPU 의 _write buffer_ 가 _UTRD 일부_ 만 commit → HCI 가 _partial UTRD_ 읽음 → garbage.

        SVA: doorbell write 시점에 UTRD memory write 가 _global visible_ 강제.

### 7.2 출처

**External**
- JEDEC JESD223 *UFS Host Controller Interface (HCI)*
- JEDEC JESD220 *UFS Specification*

---

## 다음 모듈

→ [Module 03 — UPIU & Command Flow](03_upiu_command_flow.md): UTRD 가 만들어내는 UPIU 들의 종류 (Command / Response / Data-In/Out / Query / Task Mgmt / NOP) 와 각 명령의 multi-UPIU sequence 전개.

[퀴즈 풀어보기 →](quiz/02_hci_architecture_quiz.md)

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


--8<-- "abbreviations.md"
--8<-- "_inc/topic_abbr.md"
