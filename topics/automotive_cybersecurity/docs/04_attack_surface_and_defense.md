# Module 04 — Attack Surface & Defense

<!-- DV-SKOOL-CH-CTX:start -->
<div class="chapter-context" data-cat="soc">
  <a class="chapter-back" href="../">
    <span class="chapter-back-arrow">←</span>
    <span class="chapter-back-icon">🚗</span>
    <span class="chapter-back-text">Automotive Cybersec</span>
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
  <a class="page-toc-link" href="#3-작은-예-tara-한-사이클-fsd-ecu-에-iso-21434-적용">3. 작은 예 — TARA 한 사이클</a>
  <a class="page-toc-link" href="#4-일반화-3-축-attack-surface-와-defense-in-depth-매핑">4. 일반화 — 3-축 surface × Defense-in-Depth</a>
  <a class="page-toc-link" href="#5-디테일-축별-공격-기법-방어-layer-규제">5. 디테일</a>
  <a class="page-toc-link" href="#6-흔한-오해-와-dv-디버그-체크리스트">6. 흔한 오해 + DV 디버그 체크리스트</a>
  <a class="page-toc-link" href="#7-핵심-정리-key-takeaways">7. 핵심 정리</a>
</div>
<!-- DV-SKOOL-CH-TOC:end -->

!!! objective "학습 목표"
    이 모듈을 마치면:

    - **List** 차량의 3 축 공격 표면 (물리 OBD-II/JTAG / 무선 V2X·BT·WiFi·Cellular / 공급망 FW) 을 나열할 수 있다.
    - **Explain** Defense-in-Depth 가 단일 방어보다 효과적인 이유를 설명할 수 있다.
    - **Apply** 주어진 ECU 의 attack surface 를 STRIDE / threat-tree 로 분해하고 layer 매핑할 수 있다.
    - **Analyze** V2X 환경에서 Sybil / Replay / Message-injection 공격이 어떻게 결합되는지 분석할 수 있다.
    - **Evaluate** UN R155 / ISO 21434 의 요구사항을 자기 시스템 방어 매트릭스로 평가할 수 있다.

!!! info "사전 지식"
    - [Module 01–03](01_can_bus_fundamentals.md) (CAN, SoC 보안 스택, Tesla 사례)
    - 일반 사이버보안 개념: STRIDE, threat modeling, attack tree
    - PKI / 인증서 / CRL 의 기본 동작

---

## 1. Why care? — 이 모듈이 왜 필요한가

방어를 잘 하려면 **공격자가 어디부터 들어오는지** 체계적으로 알아야 합니다. 차량은 _외부_ (셀룰러, V2X), _근접_ (BT, WiFi, NFC, OBD-II), _내부_ (CAN, Ethernet), _공급망_ (ECU FW, OTA 서버) 등 광범위한 surface 를 가집니다. 이 모듈은 각 surface 를 **자산 → 위협 → 방어 계층** 매트릭스로 정리해, 학습자가 자기 시스템에도 같은 표를 직접 그릴 수 있게 합니다.

이 모듈은 ISO 21434 의 TARA (Threat Analysis & Risk Assessment) 사고를 _체화_ 하는 단계입니다. Module 03 의 Tesla 사례가 1 가지 surface (OBD) 의 1 가지 attack (CAN injection) 이었다면, 이 모듈은 _12 가지 attack × 6 layer_ 의 매트릭스로 시야를 넓힙니다.

---

## 2. Intuition — 비유와 한 장 그림

!!! tip "💡 한 줄 비유"
    **차량 attack surface** ≈ **성벽의 모든 출입구**. 정문 (OBD-II) 만 잠근다고 끝이 아니라 — 창문 (BT/WiFi), 굴뚝 (V2X), 비밀 통로 (공급망 FW), 옥상 (Cellular) 까지 동시에 방어해야 합니다. 한 곳이라도 열려 있으면 _제일 약한 출입구_ 가 전체 보안 수준을 결정합니다 (defense-in-depth).

### 한 장 그림 — 차량 공격 표면 전체 맵

```
                        +------------------+
                        |   Cloud / OTA    |
                        |  (OEM Server)    |
                        +--------+---------+
                                 │
                            [Cellular/WiFi]
                                 │
+--------+              +--------v---------+              +---------+
| V2X    |---[DSRC]---->|   Telematics     |<---[BT]-----| Mobile  |
| (RSU)  |              |   Control Unit   |              | App     |
+--------+              +--------+---------+              +---------+
                                 │
                        +--------v---------+
                        | Central Gateway  |
                        +--+----+----+-----+
                           │    │    │
              +------------+    │    +------------+
              │                 │                 │
     +--------v----+   +-------v------+   +------v-------+
     | Powertrain  |   |   Chassis    |   | Infotainment |
     | Domain      |   |   /ADAS      |   | Domain       |
     +------+------+   +------+-------+   +------+-------+
            │                  │                  │
        [엔진 ECU]        [ADAS SoC]         [디스플레이]
        [변속기 ECU]       [브레이크]         [USB / BT]
                           [조향]             [OBD-II]
                                                 │
                                         ◀── 물리 접근 ──▶
```

3 축 진입: (1) Cloud / 무선 (Cellular, V2X, BT), (2) 물리 (OBD, JTAG, USB), (3) 공급망 (FW 빌드 시스템, OTA 서버).

### 왜 Defense-in-Depth 인가 — Rationale

단일 layer 의존이 _Tesla 의 정확한 실패 패턴_ (Module 03 — 서버 보안만 강했음) 입니다. 다음 세 사실이 다층 방어를 강제합니다.

1. **공격자는 가장 약한 layer 를 노린다** — Tesla 는 L5 (서버) 가 강해도 L2 (CAN) 가 약해서 뚫림.
2. **각 layer 는 _다른 종류_ 의 attack 을 차단한다** — HSM 은 SW 키 추출, SecOC 는 메시지 위조, IDS 는 anomaly. 한 layer 가 다른 layer 를 대체할 수 없음.
3. **한 layer 의 false negative 를 다음 layer 가 커버** — IDS 가 놓쳐도 SecOC 가 차단, SecOC 가 놓쳐도 Gateway 가 도메인 격리.

이것이 Module 02 의 5-Layer 가 _쌓이는_ 이유입니다.

---

## 3. 작은 예 — TARA 한 사이클 (FSD ECU 에 ISO 21434 적용)

가장 단순한 시나리오. ISO 21434 의 6 step TARA 를 _자기 ECU 한 종류 (FSD SoC)_ 에 적용해 한 사이클 끝까지 가봅니다.

```
   Step 1 — Asset 식별
   ──────────────────────────────────────────
   FSD SoC 가 보호해야 할 자산:
     A1. FSD 소프트웨어 무결성
     A2. GPS 좌표 데이터
     A3. Region Code / Feature Flag
     A4. Tesla Cloud 인증서
     A5. 카메라 / 센서 raw data
   
   Step 2 — Threat 시나리오 (STRIDE 적용)
   ──────────────────────────────────────────
   T1 (Spoofing):    OBD-II 동글이 GPS frame 위조 주입
   T2 (Tampering):   Region Code NVM 변조
   T3 (Repudiation): 진단 로그 삭제
   T4 (Info disc):   카메라 데이터 sniff
   T5 (DoS):         CAN bus flood / Bus-Off attack
   T6 (Elev priv):   Feature Flag 변조로 미구매 기능 활성화
   
   Step 3 — Impact 평가 (4 dimension)
   ──────────────────────────────────────────
                    Safety   Financial  Op  Privacy
   T1 GPS 위조        High     Medium   Low    Low
   T2 Region 변조     Med      High     Med    Low
   T6 Feature 변조    Low      High     Low    Low
   
   Step 4 — Attack Feasibility (CVSS-like)
   ──────────────────────────────────────────
   T1 — 장비 €500 동글, 지식 중간, 시간 분
        Tools: easy (online 판매)
        Knowledge: medium (CAN 기본 + RE)
        Window of opportunity: high (OBD 항상 열림)
        → Feasibility: HIGH
   
   Step 5 — Risk Level (Impact × Feasibility)
   ──────────────────────────────────────────
   T1 = High × HIGH = ★★★★★ Very High
   T2 = Med  × HIGH = ★★★★  High
   T6 = High × HIGH = ★★★★★ Very High
   
   Step 6 — 보안 목표 + 대책 매핑
   ──────────────────────────────────────────
   T1 → SecOC (L2) + TEE GPS fusion (L1)
   T2 → Secure Boot Measurement 에 Region Code 포함 (L1)
   T6 → Server-side feature license + Heartbeat (L5)
        + Feature Flag 를 HSM 봉인 (L1)
```

| Step | 산출물 | 다음 단계 입력 |
|---|---|---|
| ① | Asset 5 개 목록 | Threat 매핑의 대상 |
| ② | STRIDE 6 카테고리 × 자산 = threat 행렬 | Impact / Feasibility 입력 |
| ③ | Safety / Financial / Op / Privacy 4 차원 점수 | Risk 곱셈 |
| ④ | Tools / Knowledge / Time / Window 4 요소 | Risk 곱셈 |
| ⑤ | Risk score (Impact × Feasibility) | 우선순위 결정 |
| ⑥ | Layer 매핑 (어느 layer 가 책임) | 구현 계획 |

```python
# Step ⑤ 의 의사 코드 — Risk 계산 (단순 곱셈 모델)
def risk(impact_score, feasibility_score):
    # impact:      Low=1, Med=2, High=3, Critical=4
    # feasibility: Low=1, Med=2, High=3, Very High=4
    return impact_score * feasibility_score

# T1 GPS 위조
print(risk(impact_score=3,       # High (safety)
           feasibility_score=3)) # HIGH
# → 9 / 16 = 56% → Risk Level: Very High → SecOC 필수
```

!!! note "여기서 잡아야 할 두 가지"
    **(1) TARA 는 _주관적_ 이지만 _체계적_ 이어야 한다.** Step 3, 4 의 점수는 OEM/팀 내부 합의로 결정 — 그러나 _Asset → Threat → Impact → Feasibility → Risk → 대책_ 의 6 단계는 _건너뛰면 안 됨_. Tesla 가 빠뜨린 것은 Step 6 의 _layer 매핑_ 이었다고 추론할 수 있습니다 (T1 의 대책으로 SecOC 가 떠올랐어야 함). <br>
    **(2) Risk score 가 같아도 _layer 매핑_ 이 다르면 비용이 천 배 차이.** T1 을 IDS (L4) 로만 막으려 하면 우회 쉽고, SecOC (L2) 로 막으면 결정론적 차단. 이것이 Module 02 의 "layer 가 다른 attack 을 차단한다" 의 정확한 의미.

---

## 4. 일반화 — 3-축 attack surface 와 Defense-in-Depth 매핑

### 4.1 3 축 분류

```
┌──── 축 1: 물리적 접근 ────┐    ┌──── 축 2: 무선 접근 ────┐
│  OBD-II (CAN injection)   │    │  Cellular / TCU         │
│  JTAG/SWD (FW dump)       │    │  WiFi / BT (인포)       │
│  Fault Injection (chip)   │    │  GPS Spoofing (RF)      │
│  USB (인포테인먼트)       │    │  Key Fob Relay          │
│  Chip decapping (rare)    │    │  V2X (DSRC / C-V2X)     │
└───────────────────────────┘    │  TPMS (RF 433 MHz)      │
                                  └─────────────────────────┘

         ┌──── 축 3: 공급망 ────┐
         │  악성 ECU FW         │
         │  HW 백도어 (Trojan)  │
         │  위조 부품           │
         │  OTA 서버 hijack     │
         └──────────────────────┘
```

### 4.2 Defense-in-Depth — 6 Layer

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
|   SecOC (CAN MAC), MACsec (Eth), TLS                    |
+----------------------------------------------------------+
| Layer 1: Platform Security                                |
|   Secure Boot, HSM, TEE, Secure Debug, Anti-Tamper      |
+----------------------------------------------------------+
| Layer 0: Physical Security                                |
|   OBD 격리, 포트 비활성화, 물리적 접근 제어               |
+----------------------------------------------------------+
```

### 4.3 3 축 × 6 Layer 매트릭스 (요약)

| 공격 | 진입점 | 1차 방어 (어느 layer) |
|---|---|---|
| CAN Injection | OBD-II | L2 SecOC + L3 Gateway |
| CAN Replay | OBD-II | L2 Freshness Value |
| CAN DoS / Bus-Off | OBD-II | L3 Rate Limit + L4 IDS |
| GPS Spoofing (CAN) | OBD-II | L1 TEE + L2 SecOC |
| GPS Spoofing (RF) | 무선 | L1 Authenticated GNSS |
| Cellular Exploit | TCU | L0 사설 IP + L3 방화벽 |
| FW Extraction | JTAG | L1 Secure Debug + eFuse disable |
| Fault Injection | 칩 물리 | L1 Anti-Tamper + 이중 검증 |
| OTA Hijack | 서버 | L5 코드 서명 + Anti-Rollback |
| Supply Chain | 공급망 | L1 Secure Boot + L5 FW 서명 |
| Key Fob Relay | RF | L1 UWB Time-of-Flight |
| V2X Sybil | DSRC/C-V2X | L5 SCMS PKI + L4 Misbehavior Det. |

---

## 5. 디테일 — 축별 공격 기법, 방어 layer, 규제

### 5.1 축 1: 물리적 접근 공격

| 공격 | 진입점 | 기법 | 위험도 | 실제 사례 |
|---|---|---|---|---|
| **CAN Injection** | OBD-II | 위조 CAN frame 주입 | ★★★★★ | Tesla FSD 탈옥 (2025–26) |
| **ECU Firmware Dump** | JTAG/SWD | 디버그 포트로 FW 추출 | ★★★★ | 2020 Tesla MCU 탈옥 |
| **Fault Injection** | 칩 직접 | 전압/클럭 글리치 → 보안 우회 | ★★★ | Pwn2Own 2026 Tesla |
| **Chip Decapping** | 칩 직접 | 물리 키 추출 | ★★ | 연구 목적 (고비용) |
| **USB Exploit** | USB 포트 | 악성 USB 로 인포테인먼트 공격 | ★★★ | 다수 OEM |

#### CAN Injection 의 5 가지 공격 모드

```
공격 장비: CAN 트랜시버 보드 ($20–$50) + OBD-II 커넥터

1. Passive Sniffing (도청)
   [공격 장치] ── Listen ──▶ [CAN Bus]
   - 모든 CAN frame 수집, ID 별 주기 / 데이터 패턴 분석

2. Replay Attack
   [녹화 frame] ── Replay ──▶ [CAN Bus]
   - 과거 캡처한 유효 frame 재송신
   - Freshness 없으면 ECU 가 수용

3. Spoofing
   [위조 frame] ── Inject ──▶ [CAN Bus]
   - 정상 ECU 의 ID 로 가짜 데이터 송신
   - Tesla FSD: GPS ID 로 가짜 좌표

4. DoS
   [대량 frame] ── Flood ──▶ [CAN Bus]
   - 높은 우선순위 (낮은 ID) frame 대량 송신
   - 정상 ECU 의 중재 패배 → 통신 마비

5. Bus-Off Attack (Module 01 §5.6 참조)
   [에러 유도] ──▶ [CAN Bus]
   - 특정 ECU 의 TEC 비대칭 누적 → Bus-Off
```

#### Fault Injection 상세

```
대상: FSD SoC / HSM / Secure Boot 체인

전압 글리칭 (Voltage Glitching):
  정상 전압: 1.0V ──────────────────
  글리치:    1.0V ──┐    ┌──── 1.0V
                    └────┘
                    수 ns 전압 강하
                    → CPU 가 조건 분기 오판
                    → Secure Boot 검증 스킵

클럭 글리칭 (Clock Glitching):
  정상 클럭: ┌┐┌┐┌┐┌┐┌┐┌┐┌┐
  글리치:    ┌┐┌┐┌┐┐┌┐┌┐┌┐┌  ← extra edge
                   ^
                   추가 클럭 에지
                   → 인증 루프 조기 종료

EM Fault Injection:
  - 전자기 펄스로 칩 내부 회로 교란
  - 비접촉 — 패키지 개봉 불필요
  - Pwn2Own Automotive 2026 시연
```

### 5.2 축 2: 무선 접근 공격

| 공격 | 진입점 | 기법 | 위험도 |
|---|---|---|---|
| **Cellular Exploit** | TCU | 모뎀 펌웨어 취약점 | ★★★★★ |
| **WiFi/BT Exploit** | 인포테인먼트 | 프로토콜 스택 취약점 | ★★★★ |
| **GPS Spoofing** | GPS 안테나 | 위조 위성 신호 브로드캐스트 | ★★★ |
| **Key Fob Relay** | RF 315/433 MHz | 키 신호 중계 → 차량 탈취 | ★★★★ |
| **V2X Spoofing** | DSRC/C-V2X | 위조 교통 정보 주입 | ★★★ |
| **Tire Pressure (TPMS)** | RF 433 MHz | 위조 타이어 압력 경고 | ★★ |

#### Cellular / TCU 원격 공격 — 가장 위험한 원격 vector

```
TCU 아키텍처:
+----------------------------------------------+
|              TCU (Telematics Control Unit)     |
|                                                |
|  [Cellular Modem]  [WiFi/BT]  [GPS]           |
|  (LTE/5G 모듈)     (연결성)   (위치)           |
|       │                │          │            |
|       ▼                ▼          ▼            |
|  [Application Processor]                       |
|  (Linux / QNX 기반 OS)                         |
|       │                                        |
|       ▼                                        |
|  [CAN Interface] ──▶ CAN Bus ──▶ 차량 전체     |
+----------------------------------------------+
```

**Jeep Cherokee (2015) 원격 공격 재현**:

```
[인터넷]                                      [차량]
   │                                             │
   ├── Sprint 3G 네트워크 스캔                    │
   │   → 차량 TCU 의 IP 발견 (공인 IP 할당)        │
   │                                             │
   ├── D-Bus 서비스 열거                          │
   │   → Uconnect 인포테인먼트의 열린 포트 발견    │
   │                                             │
   ├── 원격 코드 실행                             │
   │   → 인포테인먼트 OS 에 셸 획득               │
   │                                             │
   ├── 내부 횡이동 (Lateral Movement)             │
   │   → V850 CAN 게이트웨이 ECU 접근             │
   │   → 게이트웨이 FW 에 서명 검증 없음          │
   │   → 악성 펌웨어 업로드                       │
   │                                             │
   ▼                                             ▼
  CAN frame 직접 주입 → 조향, 브레이크, 가속 제어
```

| 방어 계층 | 구현 | Jeep 당시 | 현대 차량 |
|---|---|---|---|
| TCU 네트워크 격리 | 사설 IP + APN 격리 | ❌ 공인 IP | ✅ |
| TCU ↔ CAN 방화벽 | 화이트리스트 메시지 필터 | ❌ | ✅ |
| 게이트웨이 FW 서명 | Secure Boot | ❌ | ✅ |
| IDS | CAN 이상 탐지 | ❌ | ✅ (대부분) |
| 도메인 격리 | Central Gateway | ❌ Flat | ✅ |

#### Key Fob Relay 공격

```
정상 동작:
  [키폭] ◀── 125 kHz LF ──▶ [차량]  (근거리 수 m)
         ── 315/433 MHz RF ──▶       (응답)
  
  차량 → LF Challenge → 키폭 → RF Response → 인증 → 도어 열림

릴레이 공격:
  [키폭]          [중계기 A]  ~~~~무선~~~~  [중계기 B]          [차량]
  (집 안)         (집 근처)    수십~수백 m   (차량 근처)        (주차장)
      │               │                        │                │
      │  ◀── LF ──────│────── 무선 중계 ────────│── LF ─▶        │
      │                │                        │                │
      │  RF 응답 ──────│────── 무선 중계 ────────│── RF ─▶ ───────│
      │
  키폭은 차량이      신호 증폭/중계         중계된 신호를     "키폭이 근처에
  바로 앞에 있다고                          차량에 전달      있다" → 도어 열림
  생각하고 응답

공격 장비: 중계기 2대 ($50–$200), 통신 거리 최대 100 m+
소요 시간: 10–30 초
```

| 방어 기법 | 원리 | 채택 현황 |
|---|---|---|
| **UWB (Ultra-Wideband)** | 신호 비행 시간 (ToF) 측정 → 중계 지연 감지 | Apple CarKey, BMW (2022~) |
| **모션 센서** | 키폭 가속도계 — 장시간 정지 시 LF 응답 비활성화 | Tesla (2019~), Ford |
| **PIN to Drive** | 키폭 인증 후 추가 PIN | Tesla (옵션), 일부 OEM |
| **RSSI 분석** | 수신 신호 강도로 거리 추정 (보조) | 일부 OEM |
| **LF 신호 특성 분석** | 중계 시 신호 왜곡 패턴 | 연구 단계 |

**왜 UWB 가 결정적인가**:
```
UWB 거리 측정:
  시간 분해능: ~65 피코초 → 거리 정확도: ~10 cm
  빛의 속도: 30 cm/ns
  
  릴레이 시 추가 지연: 최소 수십 ns (중계 처리 + 전파 지연)
  → UWB 가 이 지연을 감지 → "키폭이 실제로 2 m 이내에 있는가?" 직접 검증
  → 중계 불가 (물리 법칙)
```

#### V2X (Vehicle-to-Everything) 보안

```
V2X 통신 시나리오:
                    [RSU]  ← Road Side Unit (교통 신호)
                      │
                V2I (Infrastructure)
                      │
  [차량 A] ──V2V──▶ [차량 B] ──V2P──▶ [보행자 스마트폰]
                      │
                V2N (Network)
                      │
                   [Cloud]

두 가지 경쟁 기술:
┌─────────────────────────────────────────────────────┐
│  DSRC (802.11p)         │  C-V2X (3GPP)            │
│  WiFi 기반, 5.9 GHz     │  Cellular 기반 (LTE/5G)  │
│  낮은 지연 (~2 ms)       │  더 넓은 커버리지         │
│  미국/유럽 초기 채택      │  중국 주도, 점차 확산     │
│  전용 주파수 할당         │  기존 셀룰러 인프라 활용  │
│  IEEE 1609 보안           │  3GPP 보안               │
└─────────────────────────────────────────────────────┘
```

**SCMS — V2X PKI 인프라**:

```
SCMS (Security Credential Management System):

[Root CA]
    │
    ├── [Enrollment CA] ──▶ 차량 초기 등록 인증서 발급
    │
    ├── [Pseudonym CA] ──▶ 프라이버시 보호용 가명 인증서 발급
    │       │                 (20 개씩 로테이션 → 추적 방지)
    │       ▼
    │   [차량] ──V2V 메시지──▶ {데이터 + 서명 + 가명 인증서}
    │                              │
    │                         [수신 차량]
    │                              │
    │                         서명 검증 → 유효? → 신뢰
    │
    ├── [Linkage Authority] ──▶ 부정 차량 식별 (프라이버시와 추적의 균형)
    │
    └── [Misbehavior Authority] ──▶ 악의 / 고장 차량 인증서 폐기 (CRL)
```

**V2X 공격 시나리오**:

| 공격 | 방법 | 위험 | 방어 |
|---|---|---|---|
| **거짓 긴급 브레이킹** | 위조 BSM: "전방 차량 급정거" | 후방 차량 불필요한 급정거 → 추돌 | PKI 서명 + Misbehavior Detection |
| **유령 차량** | 존재하지 않는 차량의 BSM 생성 | 교통 혼란, ADAS 오동작 | Plausibility Check (물리적으로 가능한 위치/속도?) |
| **Sybil 공격** | 1 장치가 수십 대 가상 차량 생성 | 교통 데이터 왜곡, 경로 조작 | 가명 인증서 수량 제한 + SCMS 모니터링 |
| **인증서 도용** | 정당한 인증서 추출 후 악용 | 위조 메시지에 유효 서명 | HSM 키 보호 + 이상 패턴 시 CRL |

#### GPS Spoofing — 두 가지 레벨

```
Level 1: CAN 내부 GPS Spoofing (Tesla FSD 탈옥 방식)
  [동글] ──OBD-II──▶ [CAN Bus] ──▶ [FSD SoC]
  - CAN frame 으로 위조 좌표 주입
  - 물리적 접근 필요 (차량 내부)
  - 비용: €500–€2,000

Level 2: RF GPS Spoofing (위성 신호 위조)
  [SDR] ──RF──▶ [GPS 안테나] ──▶ [GPS 수신기] ──▶ [CAN/SoC]
  - 위조 GPS L1/L2 신호를 무선 브로드캐스트
  - 물리적 접근 불필요 (수십 m)
  - 비용: SDR $200–$1,000
  - 방어: Authenticated GNSS (Galileo OSNMA)

Tesla 탈옥은 Level 1 사용 — 더 간단·확실
```

### 5.3 축 3: 공급망 공격

| 공격 | 대상 | 기법 | 위험도 |
|---|---|---|---|
| **악성 ECU FW** | Tier-1 공급망 | 빌드 시스템 컴프로마이즈 | ★★★★★ |
| **백도어 칩** | 반도체 공급망 | HW 트로이 목마 삽입 | ★★★ |
| **위조 부품** | 애프터마켓 | 비인증 ECU/센서 교체 | ★★★★ |
| **OTA 하이재킹** | 업데이트 서버 | 서버 컴프로마이즈 → 악성 FW 배포 | ★★★★★ |

### 5.4 Layer 별 방어 상세

#### Layer 0 — 물리적 보안

| 방어 | 구현 | 효과 |
|---|---|---|
| **OBD-II 인증** | 진단 세션 시작 전 Challenge-Response | 비인증 장치 접근 차단 |
| **OBD 게이트웨이** | OBD → 진단 도메인만, Safety 격리 | FSD 탈옥 유형 차단 |
| **디버그 포트 Fuse** | JTAG/SWD 를 OTP 로 영구 disable | FW 추출 방지 |
| **Anti-Tamper 센서** | 개봉 감지 시 키 삭제 | 칩 물리 공격 방어 |

#### Layer 1 — 플랫폼 보안 (SoC 레벨)

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
|    | (ARM SC300)   | (eFuse)   | (AES/SHA/ECC)|    |
|    +------------------------------------------+    |
|    - 키는 HSM 외부로 나가지 않음                    |
|    - Application Core 는 API 만 호출               |
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

#### Layer 2 — 통신 보안

| 프로토콜 | 보안 메커니즘 | 인증 | 암호화 | 대상 |
|---|---|---|---|---|
| CAN 2.0 | SecOC (상위 계층) | CMAC (4–8 B) | ❌ | 기존 ECU |
| CAN-FD | SecOC (상위 계층) | CMAC (4–8 B) | ❌ | 고속 ECU |
| CAN-XL | CANsec (프로토콜 내장) | GCM Tag | AES-GCM | 차세대 |
| Ethernet | MACsec (802.1AE) | GCM Tag | AES-GCM | ADAS, 카메라 |
| Ethernet | TLS 1.3 | Certificate | AES-GCM | 서버 통신 |

#### Layer 3 — 네트워크 보안 (IDS)

```
CAN IDS 탐지 방식:

1. 규칙 기반 (Rule-based)
   - 알려진 공격 패턴 시그니처 매칭
   - 예: "ID 0x318 이 10 ms 이내 2 회 이상 수신" → 비정상
   - 장점: 낮은 오탐, 설명 가능 / 단점: 0-day 미탐지

2. 주기 기반 (Timing-based)
   - CAN 메시지의 주기적 패턴 학습
   - 예: "ID 0x201 은 정상 시 100 ms ± 5 ms"
   - 주기 벗어남 → injection 의심
   - Tesla 탈옥 동글 탐지 가능 (추가 frame = 주기 이상)

3. 통계/ML 기반 (Anomaly-based)
   - 정상 트래픽 프로파일 학습
   - 데이터 분포, 엔트로피, 시퀀스 패턴
   - 장점: 미지의 공격 / 단점: 오탐률 관리

4. 사양 기반 (Specification-based)
   - DBC/ARXML 의 신호 범위 검증
   - 예: "차속 0–250 km/h" → 초과 시 경고
   - GPS: "이전 위치에서 물리적으로 불가능한 이동" → spoofing 의심
```

#### Layer 4–5 — 어플리케이션 & 클라우드

| 방어 | 구현 | Tesla 적용 여부 |
|---|---|---|
| **Secure OTA** | 코드 서명 + 암호화 + 롤백 방지 | ✅ 업계 최고 |
| **VIN-bound Config** | 설정이 VIN 에 암호 바인딩 | ✅ |
| **Telemetry 모니터링** | GPS/IP/Cell 불일치 탐지 | ✅ (탈옥 탐지) |
| **Remote Kill** | 원격 기능 비활성화 | ✅ (10 만 대 동시) |
| **Secure Coding** | 정적 분석, Fuzzing | △ 부분적 |
| **Bug Bounty** | 외부 연구자 보고 | ✅ |

### 5.5 규제 프레임워크

| 규제/표준 | 범위 | 핵심 요구 | 시행 |
|---|---|---|---|
| **UN R155** | CSMS (사이버보안 관리 시스템) | 위험 평가, 모니터링, 사고 대응 | 2024~ 신차 의무 |
| **UN R156** | SUMS (SW 업데이트 관리) | OTA 보안, 롤백 방지 | 2024~ |
| **ISO/SAE 21434** | 차량 사이버보안 엔지니어링 | 개발 프로세스 전체 보안 | 국제 표준 |
| **ISO 11452** | EMC 시험 | 전자기 내성 | 형식 승인 |
| **자동차관리법 (한국)** | SW 무단 변경 | FSD 탈옥 = 2 년 징역 / 2 천만 원 | 2026~ 집행 강화 |

### 5.6 TARA 적용 — Tesla FSD 사례

§3 의 작은 예를 OEM 시점으로 확장하면:

```
1. Asset 식별
   - FSD 소프트웨어, GPS 데이터, Feature Configuration
   
2. Threat 시나리오
   - "공격자가 OBD-II 를 통해 CAN frame 을 주입하여 GPS 를 위조"
   
3. Impact 평가
   - Safety: 검증 안 된 환경에서 자율주행 → 생명 위협
   - Financial: 구독 매출 손실
   - Operational: 대규모 원격 비활성화 필요
   
4. Attack Feasibility
   - 장비: €500 동글, 공개 판매
   - 지식: 중간 (CAN 기본 + RE)
   - 시간: 수 분 (동글 연결만)
   - → Feasibility Rating: High
   
5. Risk Level
   - Impact: Critical × Feasibility: High = Risk: Very High
   
6. 보안 목표 및 대책
   - SecOC 적용, Gateway 격리, IDS 배치, TEE GPS fusion
```

---

## 6. 흔한 오해 와 DV 디버그 체크리스트

### 흔한 오해

!!! danger "❓ 오해 1 — '외부 무선만 막으면 안전'"
    **실제**: 차량은 무선 외 OBD-II (물리), supply chain (Tier-1 FW), JTAG, USB 등 _다축_ surface. 무선만 보면 _⅓ 만_ 본 것입니다. Tesla FSD 탈옥은 무선이 아니라 _물리 (OBD)_ — 가장 단순한 vector. <br>
    **왜 헷갈리는가**: 마케팅이 "커넥티드카" 위협 강조해서 무선이 가장 가시적.

!!! danger "❓ 오해 2 — 'IDS 가 공격을 차단한다'"
    **실제**: IDS 는 _Intrusion Detection_ — 탐지일 뿐 차단 아님. anomaly 발견 _후_ 알람만 올리며, 그 사이 injection 메시지는 이미 처리됨. SecOC = 결정론적 차단 (방지), IDS = 휴리스틱 탐지 — _둘 다 필요_. <br>
    **왜 헷갈리는가**: "IDS = security 솔루션" 이라는 IT 광고의 단순화.

!!! danger "❓ 오해 3 — 'V2X PKI 만 있으면 Sybil 차단'"
    **실제**: PKI (서명 검증) 는 _identity_ 만 보장. 유효한 인증서를 _많이_ 발급받은 공격자는 그 인증서들을 동시에 사용해 가짜 차량 fleet 생성 가능. 그래서 SCMS 는 (a) 가명 인증서 _수량 제한_, (b) Misbehavior Detection (plausibility check), (c) Linkage Authority 의 3 단을 _모두_ 갖춰야 함. <br>
    **왜 헷갈리는가**: "PKI = 인증 = 모든 공격 차단" 의 단순화.

!!! danger "❓ 오해 4 — 'Defense-in-Depth 의 가장 중요한 layer 가 있다'"
    **실제**: 함정 질문입니다. _다층 방어의 핵심은 단일 layer 의존 방지_. Tesla 사례가 정확한 증명 — L5 (Cloud) 가 업계 최고였어도 L2 (CAN) 가 비어 있어 뚫림. 굳이 우선순위를 매긴다면 L1 (HSM) 이 _다른 모든 layer 의 신뢰 뿌리_ 라는 의미에서 _기반_. <br>
    **왜 헷갈리는가**: "최고 우선순위 = 가장 중요한 1 개" 의 단순화.

!!! danger "❓ 오해 5 — 'Key Fob Relay 는 RSSI 로 막을 수 있다'"
    **실제**: RSSI (수신 신호 강도) 는 환경 (벽, 반사, 간섭) 에 따라 크게 변동하고, 공격자가 송신 출력을 높이면 _쉽게 속일 수 있음_. UWB 의 ToF (Time of Flight) 는 _빛의 속도_ 라는 물리 상수에 기반하므로 우회 불가 — 이것이 BMW / Apple 이 UWB 를 채택한 이유. <br>
    **왜 헷갈리는가**: "RSSI 로 거리 추정" 이 직관적이라 충분해 보임.

### DV 디버그 체크리스트 (attack surface 점검 — ECU 인수 / TARA workshop 시)

| 증상 / 자가진단 질문 | 1차 의심 | 어디 보나 |
|---|---|---|
| OBD-II 에 동글 꽂으면 모든 ECU 와 통신 가능한가? | Gateway whitelist default = ALLOW | Gateway routing table, default policy |
| ECU 의 JTAG/SWD 핀이 양산 후에도 살아 있는가? | eFuse fuse 미적용 | Lifecycle state register, eFuse status |
| TCU 가 공인 IP 를 가지는가? | 네트워크 격리 부재 | APN 설정, 사설 IP 풀 사용 여부 |
| Cellular 모뎀 펌웨어가 OEM 검증 없이 갱신되는가? | 모뎀 FW 서명 부재 | 모뎀 firmware update path |
| 차량 내부 IDS 가 _실시간_ 으로 동작하는가? | telemetry 만 있고 IDS 부재 | IDS component 존재, latency 측정 |
| 키폭이 100 m 떨어진 곳에서도 동작하는가? | UWB 미적용 | 키폭 사양 (UWB chip 유무) |
| V2X 의 가명 인증서 _수량 제한_ 이 있는가? | Sybil 방어 부재 | SCMS 발급 정책 |
| OTA 패키지에 _Anti-Rollback_ 카운터가 있는가? | downgrade attack 가능 | HSM Monotonic Counter |
| GPS 가 CAN 만 거치는가? (다른 source 와 fusion 안 됨) | TEE multi-source 부재 | sensor fusion 코드 위치 (Normal vs Secure World) |

---

## 7. 핵심 정리 (Key Takeaways)

- **3 축 attack surface** — 물리 (OBD/JTAG/USB), 무선 (BT/WiFi/Cellular/V2X), 공급망 (ECU FW / Tier-1).
- **Defense-in-Depth 6 Layer** — L0 물리 / L1 플랫폼 / L2 통신 / L3 네트워크 / L4 어플 / L5 클라우드. 단일 layer 의존 금지.
- **TARA 6 step** — Asset → Threat (STRIDE) → Impact → Feasibility → Risk → 대책 매핑. 한 단계도 건너뛰면 안 됨.
- **V2X 보안 = PKI + Misbehavior Detection + 인증서 수량 제한** 의 3 단 — 하나라도 빠지면 Sybil 가능.
- **공급망 보안** — Code-signing, SBOM, OTA Anti-Rollback. 하나의 Tier-1 침해가 전체 fleet 으로 확산 가능.
- **표준 = 사고 도구** — UN R155 / R156 / ISO 21434 는 매트릭스를 _직접 그리게_ 만드는 도구이지 체크리스트가 아님.

!!! warning "실무 주의점 — V2X Sybil 공격 임계값 설정 오류"
    **현상**: V2X Misbehavior Detection 의 물리 타당성 (Plausibility) 임계값이 느슨하면 Sybil 차량이 소수의 위장 메시지만으로 전방 정체 또는 긴급 제동 신호를 위조할 수 있다. 반대로 너무 엄격하면 정상 밀집 구간 (교차로, 주차장) 에서 오탐이 발생한다.

    **원인**: 임계값은 차량 밀도 시뮬레이션 기반으로 설정하지만, 실도로 엣지 케이스 (대형 주차장, 터널 출구 밀집) 를 커버하지 못하는 경우가 많다.

    **점검 포인트**: BSM (Basic Safety Message) 수신 로그에서 동일 위치 좌표를 공유하는 Certificate 가 임계 개수 (예: 3 개) 이상 있는지 확인. Misbehavior Authority 보고 API 호출 여부와 CRL 갱신 주기가 실시간에 준하는지 검토.

---

## 다음 모듈

→ [Module 05 — Quick Reference Card](05_quick_reference_card.md): 모듈 1–4 를 한 장으로 압축 + 면접/리뷰 직전 cheat sheet.

[퀴즈 풀어보기 →](quiz/04_attack_surface_and_defense_quiz.md)

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


--8<-- "abbreviations.md"
