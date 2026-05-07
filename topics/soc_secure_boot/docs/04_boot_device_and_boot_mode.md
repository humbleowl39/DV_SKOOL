# Module 04 — Boot Device & Boot Mode

<div class="learning-meta">
  <span class="meta-badge meta-level-advanced">📊 Advanced</span>
</div>

!!! objective "학습 목표"
    이 모듈을 마치면:

    - **Identify** 주요 boot device (eMMC, UFS, QSPI NOR, NAND) 특성 비교
    - **Apply** Boot mode strap (pinstrap) + OTP override 우선순위
    - **Plan** Fallback boot 경로 설계 (primary fail → secondary)
    - **Distinguish** Cold boot, warm boot, recovery boot 흐름 차이

!!! info "사전 지식"
    - [Module 01-03](01_hardware_root_of_trust.md)
    - 스토리지 인터페이스 일반

## 핵심 개념
**Boot Mode는 OTP > Pinstrap > Default 우선순위로 결정된다. 각 부팅 장치는 프로토콜 복잡도와 초기화 시간이 다르다. OTP는 양산 후 변경 불가이므로, Fallback 경로는 사전에 설계되어야 한다.**

---

## Boot Mode 결정

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

**왜 OTP가 최우선인가?**
> Pinstrap은 보드 위의 GPIO → 물리적으로 조작 가능. 공격자가 핀을 변경하여 USB DL 모드를 강제하고 Secure Boot를 우회할 수 있다. OTP 고정 Boot Mode는 이 공격 벡터를 차단한다.

---

## 부팅 장치 비교

| | UFS | eMMC | SD/MMC | USB DL | SPI NOR |
|--|-----|------|--------|--------|---------|
| 속도 | 최고 (2.9 GB/s) | 중간 (400 MB/s) | 느림 (104 MB/s) | 호스트 의존 | 느림 |
| 프로토콜 | SCSI+UniPro+M-PHY | MMC+eMMC 버스 | SD 버스 | USB 2.0/3.0 | SPI |
| 초기화 복잡도 | 높음 | 중간 | 낮음 | 높음 | 매우 낮음 |
| BootROM 코드 크기 | 큼 | 중간 | 작음 | 큼 | 작음 |
| 주요 용도 | 플래그십 모바일 | 중급/IoT | 개발/디버그 | FW 다운로드/복구 | MCU, 소형 SoC |
| Boot 파티션 | Boot LU (LUN) | Boot Area (1/2) | User 영역 | N/A (스트림) | 전체 |
| 보안 기능 | RPMB | RPMB | 없음 | 없음 | 없음 |

---

## 부팅 장치별 초기화 상세

### UFS Boot (가장 복잡)
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

### eMMC Boot
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

### USB Download Mode (복구/개발)
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

### SPI NOR Boot (가장 단순)
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

### 왜 UFS 초기화가 eMMC보다 복잡한가? (프로토콜 관점)

```
eMMC:   App ---- eMMC Bus ---- Card
        (단순 CMD/DATA)

UFS:    UTP ---- UniPro ---- M-PHY
        (SCSI)   (Link)     (Serial)

        ^ 3개 레이어 모두 초기화 필요 = 복잡
```

UFS는 3계층 프로토콜 스택을 가진다:
- **M-PHY** (물리 계층): 캘리브레이션과 CDR Lock 필요
- **UniPro** (링크 계층): 핸드셰이크와 Gear 협상 필요
- **UFS Transport** (전송 계층): SCSI 명령어 세트

M-PHY 캘리브레이션만으로도 PVT 변동에 대한 아날로그 튜닝으로 수 ms가 소요된다.

---

## Boot Image Format — FIP (Firmware Image Package)

BootROM이 Flash에서 BL2를 로드할 때, 이미지가 **어떤 구조**로 저장되어 있는지 알아야 한다. ARM TF-A의 표준 포맷은 FIP이다.

### FIP 구조

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

### BootROM의 FIP 파싱 흐름

```
1. Boot Device에서 Boot Header 읽기 (고정 오프셋)
2. Magic Number 검증 → 유효한 부팅 이미지인가?
3. FIP ToC Header 읽기
4. ToC Entry 순회 → UUID로 BL2 이미지 찾기
5. BL2 Certificate ToC Entry 찾기
6. BL2 + Certificate 로드
7. 서명 검증 → BL2 실행
```

### 왜 FIP 구조인가?

| 이점 | 설명 |
|------|------|
| **단일 이미지** | BL2, BL31, BL32, BL33 + 인증서를 하나의 파일로 패키징 |
| **UUID 기반 검색** | 오프셋 하드코딩 불필요 → 이미지 순서 변경에 유연 |
| **버전 관리** | 개별 이미지별 버전 + 전체 FIP 버전 이중 관리 가능 |
| **벤더 확장** | 벤더 고유 이미지를 UUID로 추가 가능 |

**DV 관점**: FIP 파싱 검증이 중요 — 손상된 ToC (잘못된 오프셋, 초과 크기, 중복 UUID), Magic Number 불일치, 잘린 이미지 등의 Negative 시나리오를 반드시 검증해야 한다.

---

## Boot Fallback 메커니즘

```
Primary: UFS
  |
  +-- UFS 초기화 성공?
  |     +- YES → BL2 로드
  |     |         +- 검증 PASS → Boot
  |     |         +- 검증 FAIL --+
  |     +- NO (장치 없음/에러) -+  |
  |                             |  |
  v                             v  v
Secondary: eMMC
  |
  +-- eMMC 초기화 성공?
  |     +- YES → BL2 로드 → 검증
  |     +- NO --+
  |             |
  v             v
Tertiary: USB DL Mode
  +-- USB Enumeration 대기
      (무한 대기 또는 타임아웃)

주의: Fallback 순서/허용 여부는 OTP에 설정됨
      Secure Boot는 USB DL 자체를 차단할 수도 있음
```

**치명적 OTP 설계 포인트**: OTP는 양산 후 변경 불가. Fallback 경로가 OTP에 사전 프로그래밍되지 않은 상태에서 Primary 부팅 장치가 실패하면 → 죽은 장치(brick). 모든 실패 시나리오가 OTP 프로그래밍 **이전에** 고려되어야 한다.

---

## Secure Boot 상태에서의 USB DL Mode

두 가지 설계 철학:

1. **USB DL 완전 차단**: OTP가 USB 부팅을 비활성화. 최대 보안이지만 현장 FW 복구 불가 → 벽돌 위험
2. **USB DL 허용 + 검증 강제**: USB로 수신한 이미지도 서명 검증 필수. 복구 가능, 변조된 FW는 차단.

대부분의 상용 SoC는 **#2를 선택** — 현장 FW 업데이트가 때때로 필요하기 때문.

---

## RPMB (Replay Protected Memory Block)

UFS/eMMC 내의 특수 보안 파티션. OTP 비트 소진 없이 보안 데이터를 저장할 수 있는 핵심 메커니즘.

### RPMB 인증 프로토콜

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

### RPMB 키 프로비저닝

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

### Write Counter의 리플레이 방지 원리

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

### RPMB 활용 사례

| 용도 | 설명 | OTP 대비 장점 |
|------|------|-------------|
| **Anti-Rollback Counter** | FW 버전 카운터 저장 | OTP 비트 소진 없음 (32비트 제한 해소) |
| **Secure Boot 상태** | 마지막 성공 부팅 설정 기록 | 업데이트 가능 |
| **TEE 보안 저장소** | 키/인증서/토큰 저장 | 대용량 저장 가능 (수 MB) |
| **Device Provisioning** | 양산 시 고유 데이터 기록 | 현장 업데이트 가능 |

### RPMB vs OTP 비교

| | OTP (eFuse) | RPMB |
|--|-------------|------|
| **변경 가능성** | 불가 (물리적 영구) | 인증된 쓰기 가능 |
| **용량** | 수 KB (비트당 비쌈) | 수 MB (저장장치 내) |
| **리플레이 방지** | 물리적으로 보장 | Write Counter로 보장 |
| **물리 공격 저항** | 높음 (온칩) | 중간 (외부 저장장치) |
| **가용성** | 칩 전원만 있으면 OK | Boot Device 초기화 필요 |
| **신뢰 수준** | 최고 (HW 불변) | 높음 (HMAC 의존) |

**면접 핵심**: "OTP는 불변성이 최고이지만 용량이 유한하다. RPMB는 HMAC 인증 + Write Counter로 리플레이를 방지하면서 용량 제한을 해소한다. Anti-Rollback에서 OTP가 메이저 버전을, RPMB가 마이너 버전을 관리하는 이중 구조가 일반적이다."

---

## DV 관점 — 부팅 장치 검증

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

## Q&A

**Q: UFS 부팅 초기화가 eMMC보다 복잡한 이유는?**
> "근본적 차이는 프로토콜 스택 깊이이다. eMMC는 병렬 버스 + 단순 명령-응답으로 CMD0→CMD1이면 PHY 레벨 협상 없이 즉시 통신이 시작된다. UFS는 3계층 스택이다: M-PHY(물리, 캘리브레이션과 CDR Lock 필요), UniPro(링크, DME_LINKSTARTUP 핸드셰이크와 Gear 협상 필요), UFS Transport(SCSI 명령어). 3개 레이어가 순차적으로 초기화되어야 하므로 BootROM 코드 크기와 부팅 시간이 증가한다."

**Q: 양산 칩의 부팅 장치가 고장나면?**
> "OTP가 이미 고정되어 있으므로 양산 후 부팅 설정을 변경할 수 없다. 대응책은 사전 설계되어야 한다: (1) BootROM Fallback 목록 — 양산 전 OTP에 Primary + Secondary 장치를 프로그래밍 (예: 'UFS 실패 → USB DL 모드'). (2) Boot 재시도 + Watchdog — Primary에서 N번 재시도 후 Watchdog Reset으로 Secondary 전환. (3) 서명 검증이 포함된 USB DL — 보안을 유지하면서 PC를 통한 현장 복구."

**Q: 부팅 장치와 BootROM 코드 크기의 관계는?**
> "지원하는 부팅 장치 수가 많을수록 = BootROM 코드가 커짐 = 더 많은 ROM 면적 + 검증 복잡도. 양산 SoC는 OTP를 통해 불필요한 부팅 장치 지원을 비활성화하여 공격 표면을 최소화한다."

**Q: RPMB는 어떻게 리플레이 공격을 방지하는가?**
> "RPMB는 두 가지 메커니즘을 결합한다: (1) HMAC 인증 — 양산 시 1회 프로비저닝된 Authentication Key로 모든 Read/Write 요청에 HMAC을 생성하여 데이터 위변조를 방지. (2) 단조증가 Write Counter — 매 Write 성공 시 카운터 증가, 요청에 포함된 카운터가 현재 값과 일치해야만 Write 허용. 과거 요청의 재전송은 카운터 불일치로 자동 거부된다."

**Q: Boot Image의 FIP 포맷이 왜 중요한가?**
> "FIP(Firmware Image Package)는 BL2, BL31, BL32, BL33과 각각의 인증서를 하나의 패키지로 묶는 ARM TF-A 표준이다. UUID 기반 검색으로 이미지 오프셋 하드코딩 없이 유연하게 이미지를 찾을 수 있고, 벤더 확장도 가능하다. DV 관점에서는 FIP 파싱의 Negative 시나리오 — 손상된 ToC, 잘린 이미지, 잘못된 UUID — 가 중요한 검증 항목이다."

---

!!! warning "실무 주의점 — Secondary boot 경로의 검증 누락 (test mode pin 우회)"
    **현상**: Production silicon 에서 정상 boot 는 깨끗한데, test/debug 용 strap pin 을 특정 조합으로 묶으면 인증 검사를 건너뛰는 secondary boot 경로가 살아있어 임의 image 가 부팅된다.

    **원인**: BootROM 분기 중 production / test / fallback 경로마다 ROTPK 검증 hook 이 따로 있는데, 그중 하나에서 OTP `secure_enable` flag 를 읽지 않거나 우선순위 비교 로직이 빠져 있음. Boot mode 매트릭스의 corner 가 DV plan 에서 빠진 결과.

    **점검 포인트**: (boot mode × OTP secure flag × pinstrap override) 모든 조합에서 인증 단계까지 동일하게 도달하는가, 그리고 production fuse blow 후 test 경로가 닫히는지 silicon 등가의 시나리오로 확인했는가.

## 핵심 정리

- **Boot mode 우선순위**: OTP > Pinstrap > Default. OTP는 양산 후 변경 불가 → 신중히 설계.
- **Boot device**:
  - **QSPI NOR**: 가장 단순, 빠른 boot, 작은 capacity
  - **eMMC**: 모바일 표준, embedded
  - **UFS**: 고속 모바일/서버, 복잡한 protocol
  - **NAND raw**: 큰 capacity, ECC 필수
- **Fallback**: primary boot fail (서명 fail, device fail) → secondary 시도. 양산 후 recovery 가능.
- **Boot 종류**: Cold (POR + 전체 init), Warm (reset, DRAM 유지), Recovery (USB/SD에서 복구 image).

## 다음 단계

- 📝 [**Module 04 퀴즈**](quiz/04_boot_device_and_boot_mode_quiz.md)
- ➡️ [**Module 05 — Attack Surface & Defense**](05_attack_surface_and_defense.md)

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
