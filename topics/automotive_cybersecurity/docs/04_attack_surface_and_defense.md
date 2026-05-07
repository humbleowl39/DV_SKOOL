# Module 04 — Attack Surface & Defense

## 학습 목표 (Learning Objectives)

이 모듈을 마치면:

1. (Remember) 차량의 주요 공격 표면(물리 OBD-II, 무선 V2X/BT/WiFi/Cellular, 공급망 FW)을 나열할 수 있다.
2. (Understand) Defense-in-Depth 가 왜 단일 방어보다 효과적인지 설명할 수 있다.
3. (Apply) 주어진 ECU의 공격 surface를 STRIDE/Threat-tree로 분해할 수 있다.
4. (Analyze) V2X 환경에서 Sybil/Replay/Message-injection 공격이 어떻게 결합되는지 분석할 수 있다.
5. (Evaluate) UN R155 / ISO 21434 의 요구사항을 자신의 시스템 방어 계층 매트릭스로 평가할 수 있다.

## 선수 지식 (Prerequisites)

- Module 01–03 (CAN, SoC 보안, Tesla 케이스)
- 일반 사이버보안 개념: STRIDE, threat modeling, attack tree
- PKI / 인증서 / CRL 의 기본 동작

## 왜 이 모듈이 중요한가 (Why it matters)

방어를 잘하려면 **공격자가 어디부터 들어오는지** 체계적으로 이해해야 한다. 차량은 외부(셀룰러, V2X), 근접(Bluetooth, WiFi, NFC, OBD-II), 내부(CAN, Ethernet), 공급망(ECU FW, OTA 서버) 등 광범위한 surface를 가지고 있다. 이 모듈은 각 surface를 **자산 → 위협 → 방어 계층**의 매트릭스로 정리해 학습자가 자신의 시스템에도 같은 표를 직접 그릴 수 있게 한다.

---

## 핵심 개념
**차량 보안은 단일 방어가 아닌 다중 계층(Defense in Depth)으로 설계해야 한다 — 물리적 접근(OBD), 무선 접근(V2X/BT/WiFi), 공급망(ECU FW)의 세 축을 모두 방어해야 한다.**

"Secure Boot가 BL1→BL2→BL3의 모든 단계를 검증하듯, 차량 보안도 물리 계층→통신 계층→어플리케이션 계층의 모든 단계를 검증해야 한다."

---

## 차량 공격 표면 전체 맵

```
                        +------------------+
                        |   Cloud / OTA    |
                        |  (Tesla Server)  |
                        +--------+---------+
                                 |
                            [Cellular/WiFi]
                                 |
+--------+              +--------v---------+              +---------+
| V2X    |---[DSRC]---->|   Telematics     |<---[BT]-----| Mobile  |
| (RSU)  |              |   Control Unit   |              | App     |
+--------+              +--------+---------+              +---------+
                                 |
                        +--------v---------+
                        | Central Gateway  |
                        +--+----+----+-----+
                           |    |    |
              +------------+    |    +------------+
              |                 |                 |
     +--------v----+   +-------v------+   +------v-------+
     | Powertrain  |   |   Chassis    |   | Infotainment |
     | Domain      |   |   /ADAS      |   | Domain       |
     +------+------+   +------+-------+   +------+-------+
            |                  |                  |
        [엔진 ECU]        [ADAS SoC]         [디스플레이]
        [변속기 ECU]       [브레이크]         [USB/BT]
                           [조향]             [OBD-II]
                                                 |
                                         <<<< 물리 접근 >>>>
```

---

## 공격 벡터 분류

### 축 1: 물리적 접근 공격

| 공격 | 진입점 | 기법 | 위험도 | 실제 사례 |
|------|--------|------|--------|----------|
| **CAN Injection** | OBD-II | 위조 CAN 프레임 주입 | ★★★★★ | Tesla FSD 탈옥 (2025-26) |
| **ECU Firmware Dump** | JTAG/SWD | 디버그 포트로 FW 추출 | ★★★★ | 2020 Tesla MCU 탈옥 |
| **Fault Injection** | 칩 직접 | 전압/클럭 글리치 → 보안 우회 | ★★★ | Pwn2Own 2026 Tesla 공격 |
| **Chip Decapping** | 칩 직접 | 물리적 키 추출 | ★★ | 연구 목적 (고비용) |
| **USB Exploit** | USB 포트 | 악성 USB 장치로 인포테인먼트 공격 | ★★★ | 다수 OEM |

#### CAN Injection 상세

```
공격 장비: CAN 트랜시버 보드 ($20~$50) + OBD-II 커넥터

공격 시나리오:

1. Passive Sniffing (도청)
   [공격 장치] ── Listen ──> [CAN Bus]
   - 모든 CAN 프레임 수집
   - ID별 주기, 데이터 패턴 분석
   - 브레이크/조향/속도 프레임 식별

2. Replay Attack (재전송)
   [녹화된 프레임] ── Replay ──> [CAN Bus]
   - 과거 캡처한 유효 프레임을 재전송
   - Freshness 관리 없으면 ECU가 수용

3. Spoofing (위장)
   [위조 프레임] ── Inject ──> [CAN Bus]
   - 정상 ECU의 ID로 가짜 데이터 전송
   - Tesla FSD 탈옥: GPS ID로 가짜 좌표 전송

4. DoS (서비스 거부)
   [대량 프레임] ── Flood ──> [CAN Bus]
   - 높은 우선순위(낮은 ID) 프레임 대량 전송
   - 정상 ECU의 중재 패배 → 통신 마비

5. Bus-Off Attack
   [에러 프레임 유도] ──> [CAN Bus]
   - 특정 ECU의 에러 카운터 증가 유도
   - Error Passive → Bus-Off 상태 진입
   - 해당 ECU 통신 차단
```

#### Fault Injection 상세

```
대상: FSD SoC / HSM / Secure Boot 체인

전압 글리칭 (Voltage Glitching):
  정상 전압: 1.0V ──────────────────
  글리치:    1.0V ──┐    ┌──── 1.0V
                    └────┘
                    수 ns 전압 강하
                    → CPU가 조건 분기 오판
                    → Secure Boot 검증 스킵

클럭 글리칭 (Clock Glitching):
  정상 클럭: ┌┐┌┐┌┐┌┐┌┐┌┐┌┐
  글리치:    ┌┐┌┐┌┐┐┌┐┌┐┌┐┌  ← 여기서 extra edge
                   ^
                   추가 클럭 에지
                   → 인증 루프 조기 종료

EM Fault Injection:
  - 전자기 펄스로 칩 내부 회로 교란
  - 비접촉 — 패키지 개봉 불필요
  - Pwn2Own Automotive 2026에서 시연
```

### 축 2: 무선 접근 공격

| 공격 | 진입점 | 기법 | 위험도 |
|------|--------|------|--------|
| **Cellular Exploit** | TCU (Telematics) | 모뎀 펌웨어 취약점 | ★★★★★ |
| **WiFi/BT Exploit** | 인포테인먼트 | 프로토콜 스택 취약점 | ★★★★ |
| **GPS Spoofing** | GPS 안테나 | 위조 위성 신호 브로드캐스트 | ★★★ |
| **Key Fob Relay** | RF 315/433MHz | 키 신호 중계 → 차량 탈취 | ★★★★ |
| **V2X Spoofing** | DSRC/C-V2X | 위조 교통 정보 주입 | ★★★ |
| **Tire Pressure (TPMS)** | RF 433MHz | 위조 타이어 압력 경고 | ★★ |

#### Cellular / TCU 원격 공격 상세 — 가장 위험한 원격 벡터

TCU(Telematics Control Unit)는 차량의 "인터넷 관문"이다. 원격에서 물리 접근 없이 공격할 수 있는 가장 위험한 진입점이다.

```
TCU 아키텍처:
+----------------------------------------------+
|              TCU (Telematics Control Unit)     |
|                                                |
|  [Cellular Modem]  [WiFi/BT]  [GPS]           |
|  (LTE/5G 모듈)     (연결성)   (위치)           |
|       │                │          │            |
|       v                v          v            |
|  [Application Processor]                       |
|  (Linux/QNX 기반 OS)                           |
|       │                                        |
|       v                                        |
|  [CAN Interface] ──> CAN Bus ──> 차량 전체     |
+----------------------------------------------+
```

**Jeep Cherokee (2015) 공격 재현**:

```
[인터넷]                                      [차량]
   │                                             │
   ├── Sprint 3G 네트워크 스캔                    │
   │   → 차량 TCU의 IP 발견 (공인 IP 할당!)       │
   │                                             │
   ├── D-Bus 서비스 열거                          │
   │   → Uconnect 인포테인먼트의 열린 포트 발견    │
   │                                             │
   ├── 원격 코드 실행                             │
   │   → 인포테인먼트 OS에 셸 획득                │
   │                                             │
   ├── 내부 횡이동 (Lateral Movement)             │
   │   → CAN 게이트웨이 ECU(Renesas V850) 접근    │
   │   → 게이트웨이 FW에 서명 검증 없음!           │
   │   → 악성 펌웨어 업로드                       │
   │                                             │
   v                                             v
   CAN 프레임 직접 주입 → 조향, 브레이크, 가속 제어

방어 교훈:
  1. TCU에 공인 IP 할당 ✗ → 사설 IP + NAT/방화벽 필요
  2. 인포테인먼트 → 게이트웨이 직접 접근 ✗ → 도메인 격리
  3. 게이트웨이 FW 업데이트에 서명 없음 ✗ → Secure Boot
  4. TCU ↔ CAN 사이에 방화벽 없음 ✗ → Firewall + IDS
```

| 방어 계층 | 구현 | Jeep 당시 | 현대 차량 |
|----------|------|----------|----------|
| TCU 네트워크 격리 | 사설 IP + APN 격리 | ❌ 공인 IP | ✅ |
| TCU ↔ CAN 방화벽 | 화이트리스트 기반 메시지 필터 | ❌ | ✅ |
| 게이트웨이 FW 서명 | Secure Boot | ❌ | ✅ |
| IDS | CAN 이상 탐지 | ❌ | ✅ (대부분) |
| 도메인 격리 | Central Gateway | ❌ Flat 구조 | ✅ |

#### Key Fob Relay 공격 상세

키폭 릴레이 공격은 가장 흔한 차량 절도 기법 중 하나다.

```
정상 동작:
  [키폭] <──125kHz LF──> [차량]  (근거리, 수 m)
         ──315/433MHz RF──>       (응답)
  
  차량이 LF로 Challenge 전송 → 키폭이 RF로 Response → 인증 성공 → 도어 열림

릴레이 공격:
  [키폭]          [중계기 A]  ~~~~무선~~~~  [중계기 B]          [차량]
  (집 안에 있음)   (집 근처)    수십~수백m    (차량 근처)        (주차장)
      │               │                        │                │
      │  ← LF ────────│────── 무선 중계 ────────│── LF →         │
      │                │                        │                │
      │  RF 응답 ──────│────── 무선 중계 ────────│── RF → ────────│
      │               │                        │                │
      v               v                        v                v
  키폭은 차량이     신호를 증폭/중계           중계된 신호를     "키폭이 근처에
  바로 앞에 있다고                             차량에 전달      있다"고 판단
  생각하고 응답                                                → 도어 열림!

공격 장비: 중계기 2대 ($50~$200), 통신 거리 확장 최대 100m+
소요 시간: 10~30초
```

| 방어 기법 | 원리 | 채택 현황 |
|----------|------|----------|
| **UWB (Ultra-Wideband)** | 신호 비행 시간(ToF) 측정으로 정확한 거리 계산 → 중계 시 지연 감지 | Apple CarKey, BMW (2022~) |
| **모션 센서** | 키폭 내 가속도계 — 장시간 정지 시 LF 응답 비활성화 | Tesla (2019~), Ford |
| **PIN to Drive** | 키폭 인증 후 추가로 PIN 입력 필요 | Tesla (옵션), 일부 OEM |
| **RSSI 분석** | 수신 신호 강도로 거리 추정 — 부정확하지만 보조 수단 | 일부 OEM |
| **LF 신호 특성 분석** | 중계 시 신호 왜곡 패턴 감지 | 연구 단계 |

**UWB가 결정적 해결책인 이유**:
```
UWB 거리 측정:
  시간 분해능: ~65 피코초 → 거리 정확도: ~10cm
  빛의 속도: 30cm/ns
  
  릴레이 공격 시 추가 지연: 최소 수십 ns (중계 장비 처리 + 전파 지연)
  → UWB는 이 지연을 감지하여 "키폭이 실제로 2m 이내에 있는가?"를 확인
  → 중계 불가
```

#### V2X (Vehicle-to-Everything) 보안 상세

V2X는 차량이 다른 차량(V2V), 인프라(V2I), 보행자(V2P), 네트워크(V2N)와 통신하는 기술이다.

```
V2X 통신 시나리오:
                    [RSU]  ← Road Side Unit (교통 신호)
                      │
                V2I (Infrastructure)
                      │
  [차량 A] ──V2V──> [차량 B] ──V2P──> [보행자 스마트폰]
                      │
                V2N (Network)
                      │
                   [Cloud]

두 가지 기술 경쟁:
┌─────────────────────────────────────────────────────┐
│  DSRC (802.11p)         │  C-V2X (3GPP)            │
│  WiFi 기반, 5.9GHz      │  Cellular 기반 (LTE/5G)  │
│  낮은 지연 (~2ms)        │  더 넓은 커버리지         │
│  미국/유럽 초기 채택      │  중국 주도, 점차 확산     │
│  전용 주파수 할당         │  기존 셀룰러 인프라 활용  │
│  IEEE 1609 보안           │  3GPP 보안               │
└─────────────────────────────────────────────────────┘
```

**V2X PKI 인프라 (SCMS)**:

```
SCMS (Security Credential Management System):

[Root CA]
    │
    ├── [Enrollment CA] ──> 차량 초기 등록 인증서 발급
    │
    ├── [Pseudonym CA] ──> 프라이버시 보호용 가명 인증서 발급
    │       │                 (20개씩 로테이션 → 추적 방지)
    │       v
    │   [차량] ──V2V 메시지──> {데이터 + 서명 + 가명 인증서}
    │                              │
    │                         [수신 차량]
    │                              │
    │                         서명 검증 → 유효? → 신뢰
    │
    ├── [Linkage Authority] ──> 부정 차량 식별 (프라이버시와 추적의 균형)
    │
    └── [Misbehavior Authority] ──> 악의적/고장 차량 인증서 폐기 (CRL)
```

**V2X 공격 시나리오**:

| 공격 | 방법 | 위험 | 방어 |
|------|------|------|------|
| **거짓 긴급 브레이킹** | 위조 BSM(Basic Safety Message): "전방 차량 급정거" | 후방 차량 불필요한 급정거 → 추돌 | PKI 서명 검증 + Misbehavior Detection |
| **유령 차량** | 존재하지 않는 차량의 BSM 생성 | 교통 혼란, ADAS 오동작 | Plausibility Check (물리적으로 가능한 위치/속도?) |
| **Sybil 공격** | 하나의 장치가 수십 대의 가상 차량 생성 | 교통 데이터 왜곡, 경로 조작 | 가명 인증서 수량 제한 + SCMS 모니터링 |
| **인증서 도용** | 정당한 인증서를 추출하여 악용 | 위조 메시지에 유효 서명 | HSM 기반 키 보호 + 이상 패턴 시 CRL 등록 |

#### GPS Spoofing — 두 가지 레벨

```
Level 1: CAN 내부 GPS Spoofing (Tesla FSD 탈옥 방식)
  [동글] ──OBD-II──> [CAN Bus] ──> [FSD SoC]
  - CAN 프레임으로 위조 좌표 주입
  - 물리적 접근 필요 (차량 내부)
  - 비용: €500~€2,000

Level 2: RF GPS Spoofing (위성 신호 위조)
  [SDR 장비] ──RF──> [GPS 안테나] ──> [GPS 수신기] ──> [CAN/SoC]
  - 위조 GPS L1/L2 신호를 무선으로 브로드캐스트
  - 물리적 접근 불필요 (수십 m 거리)
  - 비용: SDR $200~$1,000
  - 방어: Authenticated GNSS (Galileo OSNMA)

Tesla 탈옥은 Level 1을 사용 — 더 간단하고 확실
```

### 축 3: 공급망 공격

| 공격 | 대상 | 기법 | 위험도 |
|------|------|------|--------|
| **악성 ECU FW** | Tier-1 공급망 | 빌드 시스템 컴프로마이즈 | ★★★★★ |
| **백도어 칩** | 반도체 공급망 | HW 트로이 목마 삽입 | ★★★ |
| **위조 부품** | 애프터마켓 | 비인증 ECU/센서 교체 | ★★★★ |
| **OTA 하이재킹** | 업데이트 서버 | 서버 컴프로마이즈 → 악성 FW 배포 | ★★★★★ |

---

## 방어 계층 (Defense in Depth)

### 계층별 방어 매트릭스

```
+----------------------------------------------------------+
| Layer 5: Cloud & OTA Security                             |
|   서버 인증, 코드 서명, VIN 바인딩, 텔레메트리            |
+----------------------------------------------------------+
| Layer 4: Application Security                             |
|   Secure Coding, Input Validation, Fuzzing               |
+----------------------------------------------------------+
| Layer 3: Network Security                                 |
|   IDS/IPS, Firewall, Rate Limiting, Anomaly Detection    |
+----------------------------------------------------------+
| Layer 2: Communication Security                           |
|   SecOC (CAN MAC), MACsec (Ethernet), TLS               |
+----------------------------------------------------------+
| Layer 1: Platform Security                                |
|   Secure Boot, HSM, TEE, Secure Debug, Anti-Tamper      |
+----------------------------------------------------------+
| Layer 0: Physical Security                                |
|   OBD 격리, 포트 비활성화, 물리적 접근 제어               |
+----------------------------------------------------------+
```

### Layer 0: 물리적 보안

| 방어 | 구현 | 효과 |
|------|------|------|
| **OBD-II 인증** | 진단 세션 시작 전 Challenge-Response | 비인증 장치 접근 차단 |
| **OBD 게이트웨이** | OBD → 진단 도메인만 접근, Safety 격리 | FSD 탈옥 유형 차단 |
| **디버그 포트 Fuse** | JTAG/SWD를 OTP로 영구 비활성화 | FW 추출 방지 |
| **Anti-Tamper 센서** | 개봉 감지 시 키 삭제 | 칩 물리 공격 방어 |

### Layer 1: 플랫폼 보안 (SoC 레벨)

```
+--------------------------------------------------+
|              Automotive SoC                       |
|                                                    |
|  Secure Boot Chain:                               |
|    BootROM → BL2 → RTOS → Application            |
|    (각 단계 서명 검증)                             |
|                                                    |
|  HSM:                                              |
|    +------------------------------------------+    |
|    | Isolated Core | Key Store | Crypto Engine|    |
|    | (ARM SC300)   | (eFuse)  | (AES/SHA/ECC)|    |
|    +------------------------------------------+    |
|    - 키는 HSM 외부로 나가지 않음                    |
|    - Application Core는 API만 호출                 |
|                                                    |
|  TEE (ARM TrustZone):                             |
|    Secure World: 키 관리, SecOC Core, GPS 검증     |
|    Normal World: AUTOSAR OS, CAN Stack             |
|                                                    |
|  Secure Debug:                                     |
|    - Debug Auth (Certificate 기반)                 |
|    - Life Cycle State (Open → Secure → RMA)       |
+--------------------------------------------------+
```

### Layer 2: 통신 보안

| 프로토콜 | 보안 메커니즘 | 인증 | 암호화 | 대상 |
|---------|-------------|------|--------|------|
| CAN 2.0 | SecOC (상위 계층) | CMAC (4~8B) | ❌ | 기존 ECU 통신 |
| CAN-FD | SecOC (상위 계층) | CMAC (4~8B) | ❌ | 고속 ECU 통신 |
| CAN-XL | CANsec (프로토콜 내장) | GCM Tag | AES-GCM | 차세대 ECU |
| Ethernet | MACsec (802.1AE) | GCM Tag | AES-GCM | ADAS, 카메라 |
| Ethernet | TLS 1.3 | Certificate | AES-GCM | 서버 통신 |

### Layer 3: 네트워크 보안 — IDS (Intrusion Detection System)

```
CAN IDS 탐지 방식:

1. 규칙 기반 (Rule-based)
   - 알려진 공격 패턴 시그니처 매칭
   - 예: "ID 0x318이 10ms 이내에 2회 이상 수신" → 비정상
   - 장점: 낮은 오탐률, 설명 가능
   - 단점: 알려지지 않은 공격 미탐지

2. 주기 기반 (Timing-based)
   - CAN 메시지의 주기적 패턴 학습
   - 예: "ID 0x201은 정상 시 100ms ± 5ms 주기"
   - 주기 벗어남 → injection 의심
   - Tesla 탈옥 동글 탐지 가능 (추가 프레임 = 주기 이상)

3. 통계/ML 기반 (Anomaly-based)
   - 정상 트래픽 프로파일 학습
   - 데이터 분포, 엔트로피, 시퀀스 패턴 모니터링
   - 장점: 미지의 공격 탐지 가능
   - 단점: 오탐률 관리 필요

4. 사양 기반 (Specification-based)
   - DBC/ARXML에서 정의된 신호 범위 검증
   - 예: "차속 신호는 0~250km/h 범위" → 초과 시 경고
   - GPS: "이전 위치에서 물리적으로 불가능한 이동" → spoofing 의심
```

### Layer 4-5: 어플리케이션 & 클라우드

| 방어 | 구현 | Tesla 적용 여부 |
|------|------|----------------|
| **Secure OTA** | 코드 서명 + 암호화 + 롤백 방지 | ✅ 업계 최고 수준 |
| **VIN-bound Config** | 설정이 VIN에 암호학적 바인딩 | ✅ |
| **Telemetry 모니터링** | GPS/IP/Cell 불일치 탐지 | ✅ (탈옥 탐지에 사용) |
| **Remote Kill** | 원격 기능 비활성화 | ✅ (10만 대 동시 처리) |
| **Secure Coding** | 정적 분석, Fuzzing | △ 부분적 |
| **Bug Bounty** | 외부 연구자 보안 취약점 보고 | ✅ |

---

## 규제 프레임워크

### 주요 규제/표준

| 규제/표준 | 범위 | 핵심 요구사항 | 시행 |
|----------|------|-------------|------|
| **UN R155** | 사이버보안 관리 시스템 (CSMS) | 위험 평가, 모니터링, 사고 대응 | 2024~ 신차 의무 |
| **UN R156** | 소프트웨어 업데이트 관리 시스템 | OTA 보안, 롤백 방지 | 2024~ |
| **ISO/SAE 21434** | 차량 사이버보안 엔지니어링 | 개발 프로세스 전체 보안 | 국제 표준 |
| **ISO 11452** | EMC 시험 | 전자기 내성 | 형식 승인 |
| **자동차관리법** (한국) | SW 무단 변경 | FSD 탈옥 = 2년 징역 / 2천만 원 벌금 | 2026~ 집행 강화 |

### TARA (Threat Analysis and Risk Assessment)

ISO 21434가 요구하는 위험 분석 프레임워크:

```
1. Asset 식별
   - FSD 소프트웨어, GPS 데이터, Feature Configuration
   
2. Threat 시나리오
   - "공격자가 OBD-II를 통해 CAN 프레임을 주입하여 GPS를 위조"
   
3. Impact 평가
   - Safety: 검증되지 않은 환경에서 자율주행 → 생명 위협
   - Financial: 구독 매출 손실
   - Operational: 대규모 원격 비활성화 필요
   
4. Attack Feasibility
   - 장비: €500 동글, 공개 판매
   - 지식: 중간 (CAN 기본 + 리버스 엔지니어링)
   - 시간: 수 분 (동글 연결만)
   - → Feasibility Rating: High
   
5. Risk Level
   - Impact: Critical × Feasibility: High = Risk: Very High
   
6. 보안 목표 및 대책
   - SecOC 적용, Gateway 격리, IDS 배치
```

---

## 대표 문제

### Q1. "Defense in Depth에서 어떤 레이어가 가장 중요한가?"

**사고 과정**:

1. "가장 중요한 레이어"라는 질문은 함정 — Defense in Depth의 핵심은 단일 레이어 의존 방지
2. Tesla 사례: Layer 5(Cloud)는 강력했지만 Layer 2(통신 보안)가 부재 → 뚫림
3. Secure Boot 비유: BootROM(Layer 1)이 가장 근본적이지만, OTP 없으면 의미 없음
4. 차량 특수성: 물리적 접근(OBD-II)이 가능 → Layer 0이 다른 IT 시스템보다 중요

**핵심 답변**: "'가장 중요한 레이어'를 묻는 것은 '자물쇠와 경보기 중 뭐가 더 중요한가'를 묻는 것과 같다 — 답은 '둘 다 있어야 한다.' Tesla 사례가 정확히 이를 증명한다: 클라우드 보안(Layer 5)이 업계 최고였어도, 통신 보안(Layer 2)이 없으니 뚫렸다. 다만 아키텍처 관점에서 HSM(Layer 1)이 다른 모든 레이어의 **신뢰 기반**이므로, HSM 없이는 SecOC도 IDS도 의미가 없다 — Secure Boot에서 HW RoT가 Chain of Trust의 출발점인 것과 같은 논리다."

### Q2. "CAN IDS만으로 FSD 탈옥을 막을 수 있었는가?"

**사고 과정**:

1. IDS는 **탐지(detection)** 시스템이지 **방지(prevention)** 시스템이 아님
2. 주기 기반 IDS: 탈옥 동글의 추가 프레임을 탐지할 수 있음
3. 하지만: 동글이 정상 ECU와 동일한 주기로 프레임을 교체하면? → 탐지 어려움
4. IDS 탐지 후 대응: 경고만? FSD 자동 비활성화? → 정책 문제
5. SecOC는 **원천 차단** (MAC 없으면 폐기), IDS는 **사후 탐지** → 역할이 다름

**핵심 답변**: "IDS는 탐지하되 차단하지 않는다 — 이것이 IDS와 SecOC의 근본적 차이다. IDS가 탈옥 동글의 비정상 트래픽 패턴을 탐지할 수 있지만, 정교한 공격자가 정상 ECU의 주기와 패턴을 완벽히 모방하면 탐지가 어렵다. SecOC는 '유효한 MAC이 없으면 무조건 폐기'라는 결정론적 방어를 제공한다. 최적의 아키텍처는 SecOC(방지) + IDS(탐지) + Gateway(격리)의 조합이다 — Secure Boot에서 서명 검증(방지) + Watchdog(탐지) + Memory Protection(격리)을 조합하는 것과 동일한 철학이다."

---

## 확인 퀴즈

### Quiz 1. Jeep Cherokee(2015) 해킹에서 공격자가 인터넷에서 CAN Bus까지 도달한 경로를 4단계로 설명하라. 각 단계에서 어떤 방어가 빠져 있었는가?

<details>
<summary>정답 보기</summary>

| 단계 | 공격 | 빠진 방어 |
|------|------|----------|
| 1. **네트워크 진입** | Sprint 3G에서 TCU에 공인 IP 할당 → 인터넷에서 직접 접근 | TCU 네트워크 격리 (사설 IP + APN 격리) |
| 2. **인포테인먼트 장악** | Uconnect OS 취약점으로 원격 코드 실행 | 어플리케이션 보안 (Input Validation, Sandboxing) |
| 3. **게이트웨이 컴프로마이즈** | V850 CAN 게이트웨이 FW 리플래시 (서명 검증 없음) | Secure Boot + FW 서명 검증 |
| 4. **CAN 제어** | 게이트웨이를 통해 조향/브레이크 CAN 프레임 주입 | 도메인 격리 + SecOC + IDS |

핵심: **4개 레이어 모두에서 방어가 부재**했다. 하나라도 있었으면 공격 체인이 끊겼을 것이다 → Defense in Depth의 교과서적 실패 사례.
</details>

### Quiz 2. Key Fob Relay 공격을 UWB가 방어할 수 있는 물리적 원리는? RSSI 기반 거리 추정이 부족한 이유는?

<details>
<summary>정답 보기</summary>

**UWB 방어 원리**: UWB는 신호의 **비행 시간(Time of Flight)**을 피코초 단위로 측정한다. 빛의 속도(30cm/ns)로 계산하면 ~10cm 정확도로 거리를 알 수 있다. 릴레이 공격 시 중계 장비의 처리 지연 + 추가 전파 거리로 인해 반드시 수십 ns 이상의 추가 지연이 발생하고, UWB는 이를 감지하여 "키폭이 실제로 근처에 없다"고 판단한다.

**RSSI가 부족한 이유**: RSSI(수신 신호 강도)는 거리에 따라 감소하지만, 환경(벽, 반사, 간섭)에 따라 크게 변동한다. 공격자가 중계 장비의 송신 출력을 높이면 RSSI를 속일 수 있다. 또한 RSSI는 정확도가 수 m 수준이므로 "2m 이내에 있는가?"를 판단하기에는 부정확하다. ToF(시간 기반)는 전파 속도가 물리 상수이므로 속일 수 없다.
</details>

### Quiz 3. V2X에서 Sybil 공격(하나의 장치가 수십 대의 가상 차량 생성)을 SCMS가 어떻게 방어하는가?

<details>
<summary>정답 보기</summary>

SCMS는 **가명 인증서(Pseudonym Certificate)** 시스템으로 Sybil 공격을 제한한다:

1. **인증서 수량 제한**: 각 차량은 Enrollment CA에서 초기 등록 후, Pseudonym CA에서 일정 수(예: 20개)의 가명 인증서만 발급받는다. 로테이션하며 사용하지만, 동시에 사용할 수 있는 수가 제한되어 "수십 대의 가상 차량"을 만들 수 없다.

2. **Linkage Authority**: 가명 인증서들이 같은 차량의 것인지 추적할 수 있는 메커니즘을 제공한다 (프라이버시 보호 하에). 하나의 차량에서 비정상적으로 많은 BSM이 발생하면 추적 가능.

3. **Misbehavior Detection**: 수신 차량/인프라가 물리적 타당성(Plausibility)을 검증한다. 예: "같은 위치에 20대의 차량이 있는데 카메라/레이더에는 안 보인다" → Sybil 의심 → Misbehavior Authority에 보고 → 해당 인증서 폐기(CRL).
</details>

---

!!! warning "실무 주의점 — V2X Sybil 공격 임계값 설정 오류"
    **현상**: V2X Misbehavior Detection의 물리 타당성(Plausibility) 임계값이 느슨하면 Sybil 차량이 소수의 위장 메시지만으로 전방 정체 또는 긴급 제동 신호를 위조할 수 있다. 반대로 너무 엄격하면 정상 밀집 구간(교차로, 주차장)에서 오탐이 발생한다.

    **원인**: 임계값은 차량 밀도 시뮬레이션 기반으로 설정하지만, 실도로 엣지 케이스(대형 주차장, 터널 출구 밀집)를 커버하지 못하는 경우가 많다.

    **점검 포인트**: BSM(Basic Safety Message) 수신 로그에서 동일 위치 좌표를 공유하는 Certificate가 임계 개수(예: 3개) 이상 있는지 확인. Misbehavior Authority 보고 API 호출 여부와 CRL 갱신 주기가 실시간에 준하는지 검토.

## 핵심 정리 (Key Takeaways)

- **3축 공격 표면** — 물리(OBD/USB), 무선(BT/WiFi/Cellular/V2X), 공급망(ECU FW/Tier-1).
- **Defense-in-Depth** — 한 계층이 뚫려도 다음 계층(인증/필터/IDS/Cloud 검증)이 차단해야 한다.
- **V2X 보안 = PKI + Misbehavior Detection** — Sybil/Replay 방어는 인증서 수량 제한과 물리 plausibility 검증의 조합.
- **공급망 보안** — Code-signing, SBOM, OTA 검증이 빠지면 단 하나의 Tier-1 침해가 전 차량 fleet으로 확산된다.
- **표준 = 체크리스트가 아닌 사고 도구** — UN R155, ISO/SAE 21434 는 매트릭스를 직접 그리게 만드는 도구.

## 다음 단계 (Next Steps)

- 다음 모듈: [Quick Reference Card →](../05_quick_reference_card/) — 모듈 1~4를 한 장으로 압축한 cheat sheet.
- 퀴즈: [Module 04 Quiz](../quiz/04_attack_surface_and_defense_quiz/) — 공격 surface, V2X PKI, defense-in-depth 5문항.
- 실습: 자신의 차량/ECU에서 한 가지 surface(예: BT)를 골라 attack tree를 작성하고, 각 leaf에 대응하는 방어 계층을 표로 매핑한다.

<div class="chapter-nav">
  <a class="nav-prev" href="../03_tesla_fsd_case_study/">
    <div class="nav-label">◀ 이전</div>
    <div class="nav-title">Tesla FSD Case Study (탈옥 사례 분석)</div>
  </a>
  <a class="nav-next" href="../05_quick_reference_card/">
    <div class="nav-label">다음 ▶</div>
    <div class="nav-title">Automotive Cybersecurity — Quick Reference Card</div>
  </a>
</div>
