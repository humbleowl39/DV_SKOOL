# Module 04 — Boot Device & Boot Mode

<!-- DV-SKOOL-CH-CTX:start -->
<div class="chapter-context" data-cat="soc">
  <a class="chapter-back" href="../">
    <span class="chapter-back-arrow">←</span>
    <span class="chapter-back-icon">🔐</span>
    <span class="chapter-back-text">SoC Secure Boot</span>
  </a>
  <span class="chapter-divider">›</span>
  <span class="chapter-marker">Module 04</span>
</div>
<!-- DV-SKOOL-CH-CTX:end -->

<!-- DV-SKOOL-CH-TOC:start -->
<div class="page-toc">
  <span class="page-toc-label">목차</span>
  <a class="page-toc-link" href="#1-why-care-이-모듈이-왜-필요한가">1. Why care?</a>
  <a class="page-toc-link" href="#2-intuition-비유와-한-장-그림">2. Intuition</a>
  <a class="page-toc-link" href="#3-작은-예-spi-nor-boot-한-건-fip-파싱-에서-bl2-jump-까지">3. 작은 예 — SPI NOR boot 한 건</a>
  <a class="page-toc-link" href="#4-일반화-boot-mode-우선순위와-fallback-그래프">4. 일반화 — Boot Mode 우선순위와 Fallback</a>
  <a class="page-toc-link" href="#5-디테일-디바이스별-초기화-fip-rpmb-usb-dl">5. 디테일 — 디바이스별 초기화 / FIP / RPMB / USB DL</a>
  <a class="page-toc-link" href="#6-흔한-오해-와-dv-디버그-체크리스트">6. 흔한 오해 + DV 디버그 체크리스트</a>
  <a class="page-toc-link" href="#7-핵심-정리-key-takeaways">7. 핵심 정리</a>
</div>
<!-- DV-SKOOL-CH-TOC:end -->

!!! objective "학습 목표"
    이 모듈을 마치면:

    - **Identify** 주요 boot device (eMMC, UFS, QSPI NOR, NAND, USB DL) 의 특성을 비교할 수 있다.
    - **Apply** Boot mode 결정의 OTP > Pinstrap > Default 우선순위를 적용할 수 있다.
    - **Plan** Fallback boot 경로 (primary fail → secondary → tertiary) 를 OTP 사전 설계 관점에서 계획할 수 있다.
    - **Distinguish** Cold boot, warm boot, recovery boot 의 흐름과 초기화 범위를 구별할 수 있다.
    - **Trace** SPI NOR / UFS / eMMC 부팅 시 한 cert + image 가 SRAM 까지 도달하는 경로를 추적할 수 있다.

!!! info "사전 지식"
    - [Module 01-03](01_hardware_root_of_trust.md) — RoT, chain, crypto
    - 스토리지 인터페이스 일반 (SPI, MMC bus, UFS UniPro/M-PHY, USB)

---

## 1. Why care? — 이 모듈이 왜 필요한가

### 1.1 시나리오 — _Pinstrap_ 으로 _Secure Boot 우회_

2018-2019: 다수 SoC 의 secure boot 우회 사례 발견. 패턴:

- **OTP**: Secure Boot ON (강).
- **Pinstrap**: USB boot mode 선택 시 _BootROM 의 default path_ 변경.
- **BootROM bug**: USB boot path 에서 _서명 검증 단계 누락_.

결과: 공격자가 _PCB pin 조합_ 만으로 _USB → 임의 image load_. _Secure boot_ 가 켜져 있는데도.

**문제의 본질**:
- Module 02-03 의 검증은 _"cert + image 가 SRAM 에 있다고 가정"_.
- 실제로는 _"어디서 어떻게 가져오는가"_ 도 _공격 표면_.
- _Boot mode × Boot device × OTP fuse_ 의 _모든 조합_ 이 검증돼야 함.

매트릭스:

| Boot mode | NOR | eMMC | USB | UFS |
|-----------|-----|------|-----|-----|
| Normal | ✓ verify | ✓ verify | ✓ verify | ✓ verify |
| Fallback | ✓ verify | ✓ verify | ✓ verify | - |
| Recovery | ✓ verify | ✓ verify | **누락 가능** | - |

_누락된 한 cell_ = 우회 가능.

Module 02-03 에서는 _cert + image 가 SRAM 에 와 있다고 가정_ 하고 검증 흐름을 봤습니다. 이번 모듈은 그 가정의 _뒷면_ — **누가 어디서 어떻게 cert + image 를 가져오는가**, 그리고 **그 가져오는 path 자체가 공격 surface 가 될 수 있는가**.

이 모듈을 건너뛰면 _서명 검증_ 만 검증하고 _이미지 도달 경로_ 검증을 빠뜨려 — Secure Boot 가 켜진 양산 칩에서 test/debug pin 조합으로 인증 우회되는 사고가 생깁니다 (실제 사례 다수). Boot mode × Boot device × OTP fuse 의 cross matrix 가 Module 07 의 DV coverage 핵심이고, 그 매트릭스의 모양을 이 모듈에서 잡습니다.

---

## 2. Intuition — 비유와 한 장 그림

!!! tip "💡 한 줄 비유"
    **Boot Device / Mode** ≈ **발전소의 다중 전원 입력**.<br>
    평상시 (NOR/UFS), 비상시 (eMMC/SD), 점검시 (USB DL) — 각 source 가 다른 path 로 연결돼 있고, 어떤 source 를 선택하느냐는 정문 (OTP, 양산 후 변경 불가) > 게이트 (Pinstrap, PCB 변경 가능) > default 의 우선순위로 결정.

### 한 장 그림 — Boot mode 결정 + boot device 선택

```d2
direction: down

POR: "Power-On Reset"
MODE: "Boot Mode 결정 (BootROM 초기 단계)\n① OTP[BOOT_MODE] != UNSET ? YES → OTP 모드 선택 / NO → ②\n② Pinstrap GPIO 읽기\n  pin == 11 → eMMC primary\n  pin == 10 → UFS primary\n  pin == 01 → USB DL\n  pin == 00 → ③ Default\n③ BootROM 하드코딩 default"
PRIMARY: "Primary Boot Device 시도\nUFS / eMMC / SPI NOR / USB DL 중 선택된 path 로\n1) Device init (PHY → link → transport)\n2) Boot Header / FIP ToC parsing\n3) BL2 image + cert 를 SRAM 으로 DMA\n4) Module 02-03 의 서명 검증 흐름으로 진입"
FALLBACK: "Secondary / Tertiary fallback (OTP 사전 설계된 list)\neMMC 실패 → USB DL Mode → 무한 대기 또는 timeout"
POR -> MODE
MODE -> PRIMARY
PRIMARY -> FALLBACK: "하나라도 실패\n→ Secondary 로 fallback"
```

### 왜 이 디자인인가 — Design rationale

세 가지 압력이 동시에 풀려야 했습니다.

1. **양산 후에도 부팅이 가능해야** — primary device 고장 시 brick 방지 → fallback 필수.
2. **그러나 fallback 자체가 attack surface 가 되면 안 됨** — pinstrap 만으로 fallback 강제하면 공격자가 핀 조작으로 USB DL 강제 가능. 따라서 _OTP > pinstrap_ 우선순위.
3. **부팅 source 마다 protocol 복잡도/속도/보안 기능이 다름** — SPI NOR 단순 / UFS 빠르지만 3계층 / RPMB 는 UFS-eMMC 만 — 한 size fits all 안 됨.

이 셋의 교집합이 (OTP 사전 설계된 fallback list) + (verify 는 모든 source 에서 동일하게 강제) 패턴.

---

## 3. 작은 예 — SPI NOR boot 한 건, FIP 파싱에서 BL2 jump 까지

가장 단순한 시나리오. OTP[BOOT_DEV_CFG] = SPI_NOR, primary 부팅 성공의 1 cycle.

```d2
shape: sequence_diagram

F: "SPI NOR Flash (외부)"
S: "Internal SRAM"
B: "BootROM (BL1)"

# Note over B: ① POR
# Note over B: ② OTP read\nBOOT_MODE = NORMAL\nBOOT_DEV = SPI_NOR
# Note over B: ③ SPI ctrl init
# Note over B: ⑥ Boot Header parse\nMagic == 0xAA640001 ?\nYES → FIP 위치 확보
# Note over B: ⑦ FIP ToC read\nUUID = BL2 ?\nYES → entry.offset/size
# Note over B: ⑩ Module 02-03 검증\nPK / sig / image hash
# Note over B: ⑪ jump BL2_entry ★
B -> F: "RDID (0x9F)"
F -> B: "④ JEDEC ID"
B -> F: "⑤ READ (0x03) + addr 0x0"
F -> S: "Boot Header (4 KB)"
F -> S: "FIP ToC (1 KB)"
F -> S: "⑧ BL2 image (2 MB) DMA → SRAM\n(Boot LU / partition)"
F -> S: "⑨ BL2 cert (~1 KB) DMA → SRAM"
```

| Step | 누가 | 무엇을 | 왜 |
|---|---|---|---|
| ① | SoC HW | POR → reset vector → BL1 | mask ROM 안 |
| ② | BL1 | OTP read 2 회 | OTP 가 boot mode + device 양쪽을 결정 |
| ③ | BL1 | SPI 컨트롤러 reg init (CPOL/CPHA, freq) | 초기는 저속 → 안정 후 고속 |
| ④ | BL1 | RDID (0x9F) 명령 | Manufacturer/Device ID 확보 → 용량/cap 인식 |
| ⑤ | BL1 | READ (0x03) + 24-bit addr 0x0 | 표준 read 명령. Quad SPI 면 QIOR (0xEB) |
| ⑥ | BL1 | Boot Header parse | Magic 비교 → 유효한 부팅 image 인지 |
| ⑦ | BL1 | FIP ToC entry 순회 | UUID 로 BL2 / BL2-cert 위치 확보 |
| ⑧ | BL1 + DMA | BL2 binary 를 internal SRAM 으로 | Flash 가 source, SRAM 이 destination |
| ⑨ | BL1 + DMA | BL2 cert 도 SRAM 으로 | image 와 cert 는 한 쌍 |
| ⑩ | BL1 + HW Crypto | Module 03 §3 의 검증 흐름 | PK + sig + image hash 모두 PASS |
| ⑪ | BL1 | branch BL2_entry | _이 시점부터 BL2 = trusted_ |

```c
// ②~⑨ 의 BootROM 측 의사코드. 검증 (⑩) 은 Module 03 verify_bl2_rsa2048 호출.
status_t bl1_load_bl2_from_spi_nor(void) {
    // ② boot mode/device 결정
    boot_cfg_t cfg = otp_read_boot_config();
    if (cfg.dev != BOOT_DEV_SPI_NOR) return FAIL_DEV_MISMATCH;

    // ③④ SPI init + JEDEC
    spi_init_low_speed();
    uint32_t jedec = spi_send_rdid();
    if (!is_known_flash(jedec)) return FAIL_UNKNOWN_FLASH;
    spi_switch_to_high_speed();

    // ⑤⑥ Boot Header
    boot_header_t hdr;
    spi_read(SPI_OFFSET_HEADER, &hdr, sizeof(hdr));
    if (hdr.magic != BOOT_HEADER_MAGIC) return FAIL_BAD_HEADER;

    // ⑦ FIP ToC + UUID 검색
    uint32_t bl2_off, bl2_len, cert_off, cert_len;
    if (fip_locate(hdr.fip_offset, UUID_BL2,      &bl2_off, &bl2_len) != OK) return FAIL_NO_BL2;
    if (fip_locate(hdr.fip_offset, UUID_BL2_CERT, &cert_off, &cert_len) != OK) return FAIL_NO_CERT;

    // ⑧⑨ DMA → SRAM
    spi_dma_read(bl2_off,  sram_bl2_buf,   bl2_len);
    spi_dma_read(cert_off, sram_cert_buf,  cert_len);

    // ⑩ → caller 가 verify_bl2_rsa2048() 호출
    return SUCCESS;
}
```

!!! note "여기서 잡아야 할 두 가지"
    **(1) Boot device 별로 ②③④ 의 _초기화 절차_ 가 다르다** — SPI NOR 는 RDID 한 번이지만 UFS 는 PHY → UniPro → SCSI 의 3 계층. 그러나 ⑩ 검증 단계는 device 무관 _완전히 동일_. 그래서 verify 는 device-agnostic, init 는 device-specific.<br>
    **(2) FIP 의 ToC 가 손상되면 ⑦ 단계에서 _negative path_ 진입** — Magic mismatch / 잘못된 offset / 초과 size / 중복 UUID 가 모두 검증 _이전_ 실패 surface. Module 07 의 negative scenario 의 절반이 여기.

---

## 4. 일반화 — Boot Mode 우선순위와 Fallback 그래프

### 4.1 Boot Mode 결정 우선순위

```
Power-On Reset
     |
     v
Boot Mode 결정 (BootROM 초기 단계)

  (1) OTP Boot Config (최우선)
      - Secure Boot 활성화 → OTP가 지배
      - 양산 칩: OTP로 고정

  (2) Boot Pinstrap (GPIO)
      - PCB 풀업/풀다운 저항
      - 개발 보드에서 유연하게 사용

  (3) Default (BootROM 하드코딩)
      - 위 둘 다 미설정 시 사용

  우선순위: OTP > Pinstrap > Default
```

**왜 OTP 가 최우선인가?**

> Pinstrap 은 보드 위의 GPIO → 물리적으로 조작 가능. 공격자가 핀을 변경하여 USB DL 모드를 강제하고 Secure Boot 를 우회할 수 있음. OTP 고정 Boot Mode 는 이 공격 벡터를 차단.

### 4.2 Fallback 그래프

```d2
direction: down

# unparsed: PRI["Primary: UFS"]
PRIQ: "UFS 초기화 성공?" { shape: diamond }
# unparsed: UBL2[BL2 로드]
UVRF: "검증 PASS?" { shape: diamond }
# unparsed: BOOT["Boot"]
# unparsed: SEC["Secondary: eMMC"]
SECQ: "eMMC 초기화 성공?" { shape: diamond }
# unparsed: EBL2["BL2 로드 → 검증"]
# unparsed: TER["Tertiary: USB DL Mode<br/>USB Enumeration 대기<br/>(무한 대기 또는 타임아웃)"]
PRI -> PRIQ
PRIQ -> UBL2: "YES"
UBL2 -> UVRF
UVRF -> BOOT: "PASS"
UVRF -> SEC: "FAIL"
PRIQ -> SEC: "NO (장치 없음/에러)"
SEC -> SECQ
SECQ -> EBL2: "YES"
SECQ -> TER: "NO"
# unparsed: NOTE["주의: Fallback 순서/허용 여부는 OTP 에 설정됨<br/>Secure Boot 는 USB DL 자체를 차단할 수도 있음"]
TER -> NOTE { style.stroke-dash: 4 }
```

**치명적 OTP 설계 포인트**: OTP 는 양산 후 변경 불가. Fallback 경로가 OTP 에 사전 프로그래밍되지 않은 상태에서 Primary 부팅 장치가 실패하면 → 죽은 장치 (brick). 모든 실패 시나리오가 OTP 프로그래밍 _이전에_ 고려되어야 함.

### 4.3 Cold / Warm / Recovery boot

| 종류 | 트리거 | 초기화 범위 | DRAM 상태 |
|---|---|---|---|
| **Cold boot** | POR (Power-On Reset) | 전체 (PHY init, DRAM training, OTP load) | uninitialized |
| **Warm boot** | software/wdt reset (전원 유지) | 일부 (DRAM training skip 가능) | content 유지 가능 |
| **Recovery boot** | OTP/pinstrap = recovery | USB/SD 등에서 복구 image | DRAM training 필요 |

Warm boot 는 DRAM training 을 skip 할 수 있어 부팅 속도 큰 이득이지만, training 결과의 _신뢰_ 가 깨지지 않았는지 (전압/온도 변동) 검증 필요.

---

## 5. 디테일 — 디바이스별 초기화 / FIP / RPMB / USB DL

### 5.1 부팅 장치 비교

| | UFS | eMMC | SD/MMC | USB DL | SPI NOR |
|--|-----|------|--------|--------|---------|
| 속도 | 최고 (2.9 GB/s) | 중간 (400 MB/s) | 느림 (104 MB/s) | 호스트 의존 | 느림 |
| 프로토콜 | SCSI+UniPro+M-PHY | MMC+eMMC 버스 | SD 버스 | USB 2.0/3.0 | SPI |
| 초기화 복잡도 | 높음 | 중간 | 낮음 | 높음 | 매우 낮음 |
| BootROM 코드 크기 | 큼 | 중간 | 작음 | 큼 | 작음 |
| 주요 용도 | 플래그십 모바일 | 중급/IoT | 개발/디버그 | FW 다운로드/복구 | MCU, 소형 SoC |
| Boot 파티션 | Boot LU (LUN) | Boot Area (1/2) | User 영역 | N/A (스트림) | 전체 |
| 보안 기능 | RPMB | RPMB | 없음 | 없음 | 없음 |

### 5.2 부팅 장치별 초기화 상세

#### UFS Boot (가장 복잡)

```
1. PHY 초기화 (M-PHY 캘리브레이션)
2. UniPro Link Startup
   - DME_LINKSTARTUP → 핸드셰이크
   - Gear/Lane 설정 (HS-G1 ~ G4)
3. UFS Device 감지
   - NOP OUT → NOP IN (장치 생존 확인)
4. Boot LU 접근
   - QUERY: bBootLunEn 플래그 확인
   - READ(Boot LU) → BL2 이미지 로드
5. 서명 검증 → BL2 실행
```

#### eMMC Boot

```
1. CMD0 (GO_IDLE)
2. CMD1 (SEND_OP_COND) - 전압 협상
3. CMD2 (ALL_SEND_CID)
4. CMD3 (SET_RELATIVE_ADDR)
5. CMD7 (SELECT_CARD)
6. ECSD 읽기 → Boot 파티션 설정 확인
7. Boot Area → BL2 로드
8. 서명 검증 → BL2 실행

대안: eMMC Boot Mode (CMD 없이 자동 부팅 데이터 전송)
```

#### USB Download Mode (복구/개발)

```
1. USB PHY 초기화
2. USB Device Enumeration
   - BootROM이 USB Device로 동작
   - Host(PC)가 USB Host로 동작
3. 벤더 고유 프로토콜
   - Host가 BL2 이미지 전송
   - BootROM이 수신 + 검증
4. 서명 검증 → BL2 실행

주의: Secure Boot ON 상태에서도 USB DL 가능
      단, 서명 검증은 항상 수행됨
```

#### SPI NOR Boot (가장 단순)

```
1. SPI 컨트롤러 초기화
   - Clock Polarity/Phase 설정 (CPOL, CPHA)
   - 클럭 주파수 설정 (초기: 저속 → 이후 고속)

2. Flash 식별
   - RDID (Read ID, 0x9F) 명령 → Manufacturer/Device ID
   - 장치 존재 확인 + 용량/특성 파악

3. 상태 확인
   - RDSR (Read Status Register, 0x05) → WIP(Write In Progress) 비트 확인

4. BL2 이미지 읽기
   - READ (0x03) + 24-bit 주소 → 순차 읽기
   - 또는 Fast Read (0x0B) + Dummy Byte → 고속 읽기
   - Quad SPI: QIOR (0xEB) → 4배속

5. 서명 검증 → BL2 실행

SPI NOR 장점:
  - 프로토콜 단순 (Master-Slave, 단일 명령)
  - 초기화 시간 최소 (핸드셰이크 없음)
  - XIP (Execute-In-Place) 가능 → 일부 SoC에서 ROM 대용

SPI NOR 단점:
  - 용량 제한 (보통 1~256 MB)
  - 순차 접근 → 랜덤 접근 느림
  - 쓰기 속도 매우 느림 (Erase + Program)
```

#### 왜 UFS 초기화가 eMMC 보다 복잡한가? (프로토콜 관점)

```d2
direction: right

EMMC: "eMMC: 단순 CMD/DATA" {
  direction: right
  EA: "App"
  EB: "eMMC Bus"
  EC: "Card"
  EA -- EB
  EB -- EC
}
UFS: "UFS: 3개 레이어 모두 초기화 필요 = 복잡" {
  direction: right
  UA: "UTP\n(SCSI)"
  UB: "UniPro\n(Link)"
  UC: "M-PHY\n(Serial)"
  UA -- UB
  UB -- UC
}
```

UFS 는 3계층 프로토콜 스택을 가집니다:

- **M-PHY** (물리 계층): 캘리브레이션과 CDR Lock 필요
- **UniPro** (링크 계층): 핸드셰이크와 Gear 협상 필요
- **UFS Transport** (전송 계층): SCSI 명령어 세트

M-PHY 캘리브레이션만으로도 PVT 변동에 대한 아날로그 튜닝으로 수 ms 가 소요됩니다.

### 5.3 Boot Image Format — FIP (Firmware Image Package)

BootROM 이 Flash 에서 BL2 를 로드할 때, 이미지가 **어떤 구조**로 저장되어 있는지 알아야 합니다. ARM TF-A 의 표준 포맷이 FIP.

#### FIP 구조

```
Flash/UFS 내 부팅 이미지 레이아웃:

+--------------------------------------------------+
| Boot Header (벤더 고유, Flash 오프셋 0x0)          |
|  - Magic Number: 0xAA640001 등                    |
|  - FIP 시작 오프셋                                 |
|  - 체크섬 (선택)                                   |
+--------------------------------------------------+
| FIP (Firmware Image Package)                      |
|                                                   |
| +----------------------------------------------+ |
| | FIP Header                                    | |
| |  - ToC (Table of Contents) Header             | |
| |    - Name: "ToC\0"                            | |
| |    - Serial Number                            | |
| |    - Flags                                    | |
| +----------------------------------------------+ |
| | ToC Entry #0 (BL2)                            | |
| |  - UUID: 고유 식별자 (어떤 이미지인지)         | |
| |  - Offset: FIP 내 BL2 데이터 시작 위치        | |
| |  - Size: BL2 이미지 크기                       | |
| |  - Flags: 속성                                | |
| +----------------------------------------------+ |
| | ToC Entry #1 (BL2 Certificate)                | |
| |  - UUID, Offset, Size, Flags                  | |
| +----------------------------------------------+ |
| | ToC Entry #2 (BL31)                           | |
| | ToC Entry #3 (BL31 Certificate)               | |
| | ...                                           | |
| | ToC Entry #N (End Marker)                     | |
| +----------------------------------------------+ |
| | BL2 Binary Data        | BL2 Certificate     | |
| | BL31 Binary Data       | BL31 Certificate    | |
| | BL32 Binary Data       | ...                  | |
| +----------------------------------------------+ |
+--------------------------------------------------+
```

#### BootROM 의 FIP 파싱 흐름

```
1. Boot Device에서 Boot Header 읽기 (고정 오프셋)
2. Magic Number 검증 → 유효한 부팅 이미지인가?
3. FIP ToC Header 읽기
4. ToC Entry 순회 → UUID로 BL2 이미지 찾기
5. BL2 Certificate ToC Entry 찾기
6. BL2 + Certificate 로드
7. 서명 검증 → BL2 실행
```

#### 왜 FIP 구조인가?

| 이점 | 설명 |
|------|------|
| **단일 이미지** | BL2, BL31, BL32, BL33 + 인증서를 하나의 파일로 패키징 |
| **UUID 기반 검색** | 오프셋 하드코딩 불필요 → 이미지 순서 변경에 유연 |
| **버전 관리** | 개별 이미지별 버전 + 전체 FIP 버전 이중 관리 가능 |
| **벤더 확장** | 벤더 고유 이미지를 UUID 로 추가 가능 |

**DV 관점**: FIP 파싱 검증이 중요 — 손상된 ToC (잘못된 오프셋, 초과 크기, 중복 UUID), Magic Number 불일치, 잘린 이미지 등의 Negative 시나리오를 반드시 검증.

### 5.4 Secure Boot 상태에서의 USB DL Mode

두 가지 설계 철학:

1. **USB DL 완전 차단**: OTP 가 USB 부팅을 비활성화. 최대 보안이지만 현장 FW 복구 불가 → 벽돌 위험
2. **USB DL 허용 + 검증 강제**: USB 로 수신한 이미지도 서명 검증 필수. 복구 가능, 변조된 FW 는 차단

대부분의 상용 SoC 는 **#2 를 선택** — 현장 FW 업데이트가 때때로 필요하기 때문.

### 5.5 RPMB (Replay Protected Memory Block)

UFS/eMMC 내의 특수 보안 파티션. OTP 비트 소진 없이 보안 데이터를 저장할 수 있는 핵심 메커니즘.

#### RPMB 인증 프로토콜

```
SoC (BootROM/TEE)                    UFS/eMMC RPMB 컨트롤러
      |                                       |
      |  1. RPMB Write Request                |
      |    - Address, Data                    |
      |    - Write Counter (현재값)            |
      |    - HMAC(Key, Addr||Data||Counter)   |
      |  ──────────────────────────────────→  |
      |                                       |
      |     2. RPMB 컨트롤러 검증:             |
      |        - HMAC 검증 (Key 일치?)        |
      |        - Write Counter 검증            |
      |          (요청 == 저장된 카운터?)       |
      |        - 통과 → 데이터 기록            |
      |        - Write Counter++              |
      |                                       |
      |  3. RPMB Write Response               |
      |    - Result (성공/실패)                |
      |    - HMAC(Key, Result||Counter)       |
      |  ←──────────────────────────────────  |
```

#### RPMB 키 프로비저닝

```
양산 과정 (1회만 수행):

1. SoC가 RPMB Authentication Key 생성
   - 보통 HW Unique Key에서 파생 (KDF)
   - 또는 OTP의 RPMB Key 필드에서 읽기

2. RPMB Key Program 명령 전송
   - UFS/eMMC가 키를 내부에 저장
   - 1회 프로그래밍 → 이후 변경 불가

3. Write Counter = 0으로 초기화

주의: RPMB Key가 유출되면 RPMB 보호가 무력화
      → Key는 반드시 HW 보안 영역에서만 접근
```

#### Write Counter 의 리플레이 방지 원리

```
정상 시퀀스:
  Write #1: Counter=0, HMAC(data, 0) → 성공, Counter→1
  Write #2: Counter=1, HMAC(data, 1) → 성공, Counter→2

리플레이 공격:
  공격자가 Write #1의 패킷을 그대로 재전송:
  Write #1 재전송: Counter=0, HMAC(data, 0)
                   → RPMB: "현재 Counter=2인데 0이 왔다?" → 거부!

  → 단조증가 카운터가 과거 요청의 재사용을 원천 차단
```

#### RPMB 활용 사례

| 용도 | 설명 | OTP 대비 장점 |
|------|------|-------------|
| **Anti-Rollback Counter** | FW 버전 카운터 저장 | OTP 비트 소진 없음 (32비트 제한 해소) |
| **Secure Boot 상태** | 마지막 성공 부팅 설정 기록 | 업데이트 가능 |
| **TEE 보안 저장소** | 키/인증서/토큰 저장 | 대용량 저장 가능 (수 MB) |
| **Device Provisioning** | 양산 시 고유 데이터 기록 | 현장 업데이트 가능 |

#### RPMB vs OTP 비교

| | OTP (eFuse) | RPMB |
|--|-------------|------|
| **변경 가능성** | 불가 (물리적 영구) | 인증된 쓰기 가능 |
| **용량** | 수 KB (비트당 비쌈) | 수 MB (저장장치 내) |
| **리플레이 방지** | 물리적으로 보장 | Write Counter 로 보장 |
| **물리 공격 저항** | 높음 (온칩) | 중간 (외부 저장장치) |
| **가용성** | 칩 전원만 있으면 OK | Boot Device 초기화 필요 |
| **신뢰 수준** | 최고 (HW 불변) | 높음 (HMAC 의존) |

**면접 핵심**: "OTP 는 불변성이 최고이지만 용량이 유한하다. RPMB 는 HMAC 인증 + Write Counter 로 리플레이를 방지하면서 용량 제한을 해소한다. Anti-Rollback 에서 OTP 가 메이저 버전을, RPMB 가 마이너 버전을 관리하는 이중 구조가 일반적이다."

### 5.6 DV 관점 — 부팅 장치 검증 항목

| 검증 항목 | 설명 | 방법 |
|----------|------|------|
| 프로토콜 준수 | UFS/eMMC 프로토콜 스펙 준수 | VIP Protocol Checker |
| 부팅 이미지 로딩 | 올바른 파티션, 올바른 크기 | Scoreboard 주소/크기 비교 |
| 서명 검증 PASS/FAIL | 정상 + 변조 이미지 모두 | Positive + Negative 시나리오 |
| Fallback 동작 | Primary 실패 → Secondary 전환 | 에러 주입 (장치 무응답) |
| Boot Mode 선택 | OTP/Pinstrap 조합 → 올바른 장치 | OTP Abstraction Layer sweep |
| 타임아웃 처리 | 장치 무응답 → 무한대기 없음 | Watchdog + 타임아웃 검증 |
| 엣지 케이스 | 불완전 이미지, CRC 에러, 전원 글리치 | Corner Case 시퀀스 |

---

## 6. 흔한 오해 와 DV 디버그 체크리스트

### 흔한 오해

!!! danger "❓ 오해 1 — 'Production mode 만 검증하면 충분'"
    **실제**: Test/Debug mode 가 production 에서도 활성화되어 있으면 (mode pin 미고정) 공격자가 그 path 로 우회 가능. Secondary path 의 _인증 단계까지 동일하게 도달하는가_ 가 critical. boot mode × OTP × pinstrap 의 cross matrix 전수가 검증 대상.<br>
    **왜 헷갈리는가**: "제품 = production path" 만 보는 mindset. 공격자는 secondary 노립니다.

!!! danger "❓ 오해 2 — 'Fallback 만 있으면 brick 안 된다'"
    **실제**: Fallback 자체가 OTP 에 사전 프로그래밍 _되어야_ 동작. OTP 가 비어 있는 상태에서 primary 가 실패하면 default 만 시도 후 brick. 모든 fallback 시나리오는 _provisioning 시점에_ 결정.<br>
    **왜 헷갈리는가**: BootROM 코드만 보고 "fallback 함수가 있다 = OK" 의 직관. 실제로는 OTP 의 fallback list 가 함수의 입력.

!!! danger "❓ 오해 3 — 'USB DL 은 무조건 차단해야 안전'"
    **실제**: 대부분의 상용 SoC 는 USB DL 허용 + 서명 검증 강제. 완전 차단 시 현장 brick 시 복구 불가능 → 차라리 검증 강제로 안전을 _경로 안에서_ 확보. Secure Boot ON + USB DL ON + verify 강제가 표준.<br>
    **왜 헷갈리는가**: "어떤 path 가 적을수록 안전" 의 단순화.

!!! danger "❓ 오해 4 — 'RPMB 가 OTP 를 대체한다'"
    **실제**: RPMB 는 OTP 의 _보조_. RPMB key 자체는 HW unique key 에서 KDF 또는 OTP 의 RPMB key field — 즉 RPMB 의 root 는 여전히 HW. OTP 가 메이저 버전, RPMB 가 마이너 카운터의 _이중 구조_ 가 일반적.<br>
    **왜 헷갈리는가**: RPMB 가 "Replay Protected" 라는 이름 때문에 OTP 와 동급으로 보임.

!!! danger "❓ 오해 5 — 'Anti-rollback 만 있으면 downgrade 차단'"
    **실제**: ARC 가 OTP 가 아닌 OTP-emulated (rewriteable EEPROM/flash 영역) 에 있으면 우회 가능. counter 의 _진짜 immutable_ 여부가 critical. RPMB 도 attacker 가 storage 자체를 갈아끼우면 monotonicity 가 깨질 수 있어서 OTP 가 메이저 버전을 책임져야 함.<br>
    **왜 헷갈리는가**: "기능 이름 = 동작 보장" 의 직관. 실제 구현 storage 가 더 중요.

### DV 디버그 체크리스트 (Boot device / mode 검증에서 자주 보는 실패)

| 증상 | 1차 의심 | 어디 보나 |
|---|---|---|
| Production silicon 에서 test pin 으로 인증 우회 부팅 | Secondary path 의 ROTPK 검증 hook 누락 | (boot mode × OTP secure flag × pinstrap) 매트릭스 — 모든 path 가 verify 단계까지 도달하나 |
| UFS bring-up 만 실패, eMMC 는 OK | M-PHY 캘리브레이션 또는 UniPro DME_LINKSTARTUP | UFS init log 의 stage 별 done flag, gear/lane 협상 결과 |
| FIP 로드 시 random offset 에서 hang | ToC entry 의 offset/size 가 device 용량 초과 | FIP ToC dump → entry size sum vs device capacity |
| Magic 일치 안 함 | endian 또는 vendor-specific header byte order | 빌드 시 byte order vs ROM 의 read byte order |
| Anti-RB counter rollback 성공 | counter 가 RPMB 단독 — RPMB 영역 백업/복원 공격 | counter backing storage = OTP fuse 인지 확인 |
| Cold boot OK, warm boot fail | warm path 가 DRAM training skip 했는데 voltage 변동 | warm boot 의 retraining policy + temperature sensor |
| USB DL 강제 시 cert 검증 skip 됨 | USB path 가 boot device path 와 다른 verify hook | USB DL 의 verify 함수 = primary path 의 verify 함수 인지 |
| Recovery boot 후 lifecycle 가 dev 로 | recovery image 가 dev key 로 서명 + production OTP 가 dev key 도 허용 | OTP[ROTPK_HASH_LIST] 가 dev 키 hash 를 포함하는지 |

!!! warning "실무 주의점 — Secondary boot 경로의 검증 누락 (test mode pin 우회)"
    **현상**: Production silicon 에서 정상 boot 는 깨끗한데, test/debug 용 strap pin 을 특정 조합으로 묶으면 인증 검사를 건너뛰는 secondary boot 경로가 살아있어 임의 image 가 부팅된다.

    **원인**: BootROM 분기 중 production / test / fallback 경로마다 ROTPK 검증 hook 이 따로 있는데, 그중 하나에서 OTP `secure_enable` flag 를 읽지 않거나 우선순위 비교 로직이 빠져 있음. Boot mode 매트릭스의 corner 가 DV plan 에서 빠진 결과.

    **점검 포인트**: (boot mode × OTP secure flag × pinstrap override) 모든 조합에서 인증 단계까지 동일하게 도달하는가, 그리고 production fuse blow 후 test 경로가 닫히는지 silicon 등가의 시나리오로 확인했는가.

---

## 7. 핵심 정리 (Key Takeaways)

- **Boot mode 우선순위**: OTP > Pinstrap > Default. OTP 양산 후 변경 불가 → 신중히 설계.
- **Boot device 4 형태**: SPI NOR (단순/소형) / eMMC (모바일 표준) / UFS (고속 3계층) / NAND (대용량 + ECC).
- **Fallback 은 OTP 사전 설계** — primary fail → secondary list 가 OTP 에 박혀 있어야 brick 회피.
- **Boot 종류 3 가지** — Cold (POR + 전체 init), Warm (reset, DRAM 유지), Recovery (USB/SD 에서 복구 image).
- **RPMB 는 OTP 의 _보조_** — HMAC + Write Counter 로 replay 방지하면서 OTP 비트 소진 없이 카운터 확장. Root 는 HW key.

!!! warning "실무 주의점 (요약)"
    - Secondary boot 의 verify hook 이 primary 와 _문자 그대로 동일_ 한가 — 같은 함수를 호출하는가, 분기마다 별도 사본인가.
    - USB DL 도 verify 강제 — completely closed 보다 verified-allowed 가 양산 brick 회피에 안전.
    - ARC counter 의 backing storage 가 OTP 인지 RPMB 인지 OTP-emulated 인지 — 이름이 같아도 immutability 가 다름.

### 7.1 자가 점검

!!! question "🤔 Q1 — OTP > Pinstrap 우선순위 (Bloom: Analyze)"
    Boot mode 결정 우선순위가 OTP > Pinstrap > Default 인 _보안_ 근거?
    ??? success "정답"
        OTP 우선의 보안 이유:
        - **Pinstrap = 외부 핀**: 공격자가 ROHS jig 또는 fault injection 으로 핀 값 변경 가능 → 신뢰 불가.
        - **OTP = silicon 내부**: blown fuse 는 칩 분해 + FIB 공격이 필요 → 비용 압도적으로 높음.
        - **양산 정책**: production lifecycle 진입 후에는 OTP 가 모든 선택을 _override_ → pinstrap 으로 secure → debug 전환 차단.
        - default 가 최저 우선순위인 이유: bring-up 단계의 fallback 일 뿐, 양산에서는 OTP 가 반드시 양수.

!!! question "🤔 Q2 — RPMB vs OTP counter (Bloom: Evaluate)"
    Anti-rollback counter 에 RPMB 를 쓰면 OTP fuse 소진을 피할 수 있다. _단점_ 은?
    ??? success "정답"
        RPMB counter 의 trade-off:
        - **HMAC key 의존**: HMAC key 가 침해되면 counter 위조 가능 → key derivation 보안 = anti-rollback 보안.
        - **eMMC/UFS 펌웨어 침해**: device firmware bug 로 RPMB write counter monotonicity 가 깨지는 사례 존재.
        - OTP fuse: 물리적 비가역 → 펌웨어 침해와 무관.
        - 결론: RPMB 는 _대용량_ counter (수십만 개) 에 유리, OTP 는 _최후 anchor_ (수십 개) — 둘은 보완 관계지 대체 관계 아님.

### 7.2 출처

**Internal (Confluence)**
- `Boot Mode Selection` — OTP/Pinstrap 우선순위 매트릭스
- `RPMB Anti-Rollback` — HMAC key derivation + counter 관리

**External**
- JEDEC JESD220 *UFS Specification* — RPMB region 명세
- JEDEC JESD84-B51 *eMMC Specification* — RPMB partition + Write Counter
- ARM TBBR-CLIENT — Boot Source + Fallback 정의

## 다음 단계

- 📝 [**Module 04 퀴즈**](quiz/04_boot_device_and_boot_mode_quiz.md)
- ➡️ [**Module 05 — Attack Surface & Defense**](05_attack_surface_and_defense.md): 위에서 본 모든 path 를 _공격자 관점_ 으로 다시 — FI, side-channel, TOCTOU, JTAG.

<div class="chapter-nav">
  <a class="nav-prev" href="../03_crypto_in_boot/">
    <div class="nav-label">◀ 이전</div>
    <div class="nav-title">Secure Boot 암호학 — 서명 검증과 키 관리</div>
  </a>
  <a class="nav-next" href="../05_attack_surface_and_defense/">
    <div class="nav-label">다음 ▶</div>
    <div class="nav-title">공격 표면과 방어</div>
  </a>
</div>


--8<-- "abbreviations.md"
--8<-- "_inc/topic_abbr.md"
