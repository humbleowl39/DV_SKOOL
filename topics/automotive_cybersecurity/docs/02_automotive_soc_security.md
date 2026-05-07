# Module 02 — Automotive SoC Security

## 학습 목표

이 모듈을 마치면:

1. (Remember) HSM, SecOC, Secure Gateway, IDS의 정의와 역할을 설명할 수 있다.
2. (Understand) 왜 CAN 자체로는 안전하지 않고 SoC 레벨 방어가 필수인지 설명할 수 있다.
3. (Apply) HSM 키 계층(Root → Master → Session)을 ECU 부팅·런타임에 적용할 수 있다.
4. (Analyze) SecOC의 MAC + Freshness 메커니즘이 막아주는 공격과 막지 못하는 공격을 구분할 수 있다.
5. (Evaluate) 차량 도메인 격리 방식(Central Gateway vs Zonal Architecture)의 장단점을 비교·평가할 수 있다.

## 선수 지식

- Module 01 — CAN Bus Fundamentals (CAN 프레임/Arbitration/구조적 약점)
- Secure Boot, Root of Trust, AES/HMAC 같은 기본 암호 개념
- ECU와 Gateway가 차량 네트워크에서 어떤 역할을 하는지에 대한 직관

## 왜 이 모듈이 중요한가

CAN Bus 자체는 1980년대에 설계되어 인증·암호화가 없다. 따라서 보안은 **SoC + ECU + Gateway 레벨에서 추가 계층으로** 구현된다. HSM이 키를 보호하지 못하거나 SecOC가 빠지면 한 노드 침해가 곧 차량 전체 침해로 이어진다. 이 모듈은 "프로토콜 위에 어떤 보안 스택을 올려야 하는가"를 결정하는 아키텍처 사고를 다룬다.

---

!!! tip "💡 이해를 위한 비유"
    **Automotive SoC Security 스택** ≈ **차량 보안 = 4단 케이크 (HSM + SecOC + Gateway + IDS)**

    각 layer 가 다른 attack 차단 — HSM=key, SecOC=메시지, Gateway=도메인 격리, IDS=anomaly. 한 layer 만으로는 부족.

---

## 핵심 개념
**CAN Bus의 구조적 결함은 프로토콜 자체로는 해결 불가 — SoC 레벨에서 HSM(키 관리) + SecOC(메시지 인증) + Secure Gateway(도메인 격리)로 방어해야 한다.**

"Secure Boot가 '부팅 체인의 무결성'을 보장하듯, SecOC는 '통신 체인의 무결성'을 보장한다 — 둘 다 하드웨어 RoT(HSM)에 뿌리를 두어야 한다."

!!! danger "❓ 흔한 오해"
    **오해**: HSM 이 있으면 자동 안전

    **실제**: HSM 이 있어도 (1) HSM 적용 범위 — Tesla 처럼 SCS 가 boot 만 보호하고 CAN 은 미적용 시 무력화 (2) HSM 사용 SW 정확성 → 둘 다 검증 필요.

    **왜 헷갈리는가**: "hardware security = full security" 의 marketing 단순화. 적용 범위와 SW 정확성이 critical.
---

## 방어 아키텍처 전체 구조

```
+================================================================+
|                  차량 SoC 보안 스택                              |
|                                                                |
|  Layer 4: OTA + Cloud Validation                               |
|    서버 측 VIN 인증, 텔레메트리 모니터링, 원격 비활성화          |
|                                                                |
|  Layer 3: Intrusion Detection System (IDS)                     |
|    CAN 트래픽 이상 탐지, 규칙 기반 + ML 기반                    |
|                                                                |
|  Layer 2: Secure Gateway + Domain Isolation                    |
|    도메인 간 방화벽, 메시지 라우팅/필터링, OBD-II 격리          |
|                                                                |
|  Layer 1: SecOC (Secure Onboard Communication)                 |
|    CAN 메시지 MAC 인증, Freshness 관리, Replay 방어            |
|                                                                |
|  Layer 0: HSM (Hardware Security Module)                       |
|    키 생성/저장, MAC 연산, Secure Boot, 물리적 변조 방지        |
+================================================================+
```

---

## HSM (Hardware Security Module)

### SoC Secure Boot의 HW RoT와의 관계

```
[Secure Boot]                    [Automotive Security]
     │                                  │
  BootROM + OTP                      HSM + Secure Key Storage
  = 부팅 체인의 신뢰 기반            = 통신 체인의 신뢰 기반
     │                                  │
  ROTPK → BL 서명 검증               Symmetric Key → CAN 메시지 MAC
  비대칭키 (RSA/ECDSA)               대칭키 (AES-CMAC / AES-GCM)
```

### HSM의 구조

```
+-----------------------------------------------+
|              Automotive MCU/SoC                 |
|                                                 |
|  +-------------------+  +-------------------+   |
|  |   Application     |  |      HSM          |   |
|  |   Core (ARM)      |  |   (Isolated Core) |   |
|  |                   |  |                   |   |
|  |  FW / AUTOSAR OS  |  |  Secure Key Store |   |
|  |  Application SW   |  |  Crypto Engine    |   |
|  |  CAN Driver       |  |  RNG              |   |
|  |                   |  |  Secure Boot      |   |
|  +--------+----------+  |  Anti-Tamper      |   |
|           |              +--------+----------+   |
|           |   API Call           |               |
|           +-------->-------------+               |
|           |   MAC Result         |               |
|           +----------<-----------+               |
|                                                 |
|  ※ HSM 내부 키는 Application Core에서           |
|    절대 직접 접근 불가 — API로만 연산 요청        |
+-----------------------------------------------+
```

### 주요 Automotive HSM 칩

| 벤더 | 제품군 | HSM 이름 | 특징 |
|------|--------|---------|------|
| **Infineon** | AURIX TC4x | HSM4 | SHE 2.0 호환, AES-128/256, ECC, Secure Debug |
| **NXP** | S32K3, S32G | HSE (Hardware Security Engine) | PKCS#11 인터페이스, 키 관리 내장 |
| **ST** | Stellar | HSM + SHE | EVITA Full 준수, 하드웨어 격리 |
| **Renesas** | RH850/U2x | ICU-M (HSM) | ISO 21434 준수, 키 래더 |

### HSM 키 프로비저닝 라이프사이클

키가 어떻게 HSM에 들어가고, 운용되고, 폐기되는지의 전체 흐름:

```
Phase 1: 제조 시 키 주입 (Factory Provisioning)
+--------------------------------------------------+
|  ECU 제조 라인 (Secure Environment)               |
|                                                    |
|  [Key Management Server]                           |
|       │                                            |
|       ├── Master Key에서 ECU별 고유 키 파생         |
|       │   (KDF: Key Derivation Function)           |
|       │                                            |
|       v                                            |
|  [HSM Provisioning Tool] ──SWD/JTAG──> [ECU HSM]  |
|       │                                  │         |
|       ├── Device Unique Key (고유 키)     │         |
|       ├── SecOC MAC Key (통신 인증용)     │         |
|       ├── Secure Boot Key (부팅 검증용)   │         |
|       └── Certificate (클라우드 인증용)   │         |
|                                          v         |
|                                   [eFuse/OTP에 기록]|
|                                   (이후 변경 불가)  |
|                                                    |
|  ※ 주입 후 JTAG 포트는 eFuse로 영구 비활성화       |
+--------------------------------------------------+

Phase 2: 차량 출고 후 키 활성화
  OEM 서버 ←──TLS──> 차량 TCU ──> HSM
  - 차량 VIN + ECU ID로 키 활성화 요청
  - 서버가 키 활성화 토큰 발급
  - HSM이 토큰 검증 후 SecOC 키 활성화

Phase 3: 런타임 키 로테이션 (Key Rotation)
  주기: OEM 정책에 따라 수천~수만 km, 또는 시간 기반
  
  [현재 키 K_n]                    [다음 키 K_n+1]
       │                                │
       ├── 현재 SecOC 인증에 사용        │
       │                                ├── HSM 내부에서 KDF로 파생
       │                                │   또는 OTA로 서버에서 수신
       │                                │
       v                                v
  [키 전환 시점]
       │
       ├── 모든 ECU에 동기화된 키 전환 명령
       ├── Freshness Counter 리셋
       └── 이전 키 K_n은 HSM 내부에서 삭제

Phase 4: 키 폐기 / 갱신
  - ECU 교체 시: 새 ECU에 키 재주입 (정비소 보안 인증 필요)
  - 키 유출 의심 시: OTA로 긴급 키 로테이션
  - 차량 폐차 시: HSM의 키 영구 삭제 (Zeroization)
```

| 단계 | 보안 위협 | 대응 |
|------|----------|------|
| 제조 시 | 키 주입 과정 도청/유출 | Secure Room + HSM 직접 통신 |
| 출고 후 | OTA 키 전송 가로채기 | TLS + 키 암호화 전송 |
| 런타임 | 키 로테이션 중 불일치 | 동기화 프로토콜 + 이전 키 유예 기간 |
| 폐기 시 | 폐차 ECU에서 키 추출 | Zeroization + Anti-Tamper |

### SHE (Secure Hardware Extension) vs EVITA

| | SHE | EVITA Full |
|--|-----|-----------|
| **키 슬롯** | 11개 고정 | 가변 (수십~수백) |
| **알고리즘** | AES-128-CMAC only | AES, RSA, ECC, SHA |
| **비대칭키** | ❌ | ✅ |
| **용도** | 기본 CAN 인증 | 게이트웨이, ADAS, V2X |
| **비용** | 저렴 (수 mm² 추가) | 상대적으로 높음 |

---

## SecOC (Secure Onboard Communication)

### AUTOSAR SecOC 개요

SecOC는 AUTOSAR가 정의한 **CAN/CAN-FD/Ethernet 메시지 인증 모듈**이다.

```
송신 ECU:                          수신 ECU:
                                   
[App Data]                         [Secured PDU 수신]
    │                                  │
    v                                  v
[SecOC Module]                     [SecOC Module]
    │                                  │
    ├── HSM에 MAC 요청                 ├── HSM에 MAC 검증 요청
    │   Key ID + Data + FV            │   Key ID + Data + FV + MAC
    │                                  │
    ├── Freshness Value 생성           ├── Freshness Value 검증
    │   (카운터 or 타임스탬프)          │   (허용 범위 내?)
    │                                  │
    v                                  v
[Secured PDU]                      [인증 성공?]
 = Data + Truncated MAC + FV          ├── Yes → App에 전달
    │                                  └── No  → 폐기 + 에러 보고
    v
[CAN-FD 프레임으로 전송]
```

### SecOC PDU 구조

```
기존 CAN 프레임 (8B payload):
+------------------+
| Application Data |
| (8 bytes)        |
+------------------+
→ 인증 없음, 누구든 위조 가능

SecOC 적용 CAN-FD 프레임 (64B payload):
+------------------+----------------+-----------+
| Application Data | Truncated MAC  | Freshness |
| (48-56 bytes)    | (4-8 bytes)    | (2-4 bytes)|
+------------------+----------------+-----------+
→ MAC: HSM이 대칭키로 생성, 키 없이는 위조 불가
→ Freshness: 재전송 공격(replay) 방어
```

### 왜 Truncated MAC인가?

| MAC 크기 | 보안 강도 | CAN-FD 데이터 여유 | 선택 이유 |
|---------|----------|-------------------|----------|
| 16B (Full CMAC) | 2^128 | 48B payload | 이론적 최대 — 대역폭 비효율 |
| **8B (Truncated)** | **2^64** | **56B payload** | **AUTOSAR 권장 — 충분한 보안 + 합리적 대역폭** |
| 4B | 2^32 | 60B payload | 최소 — 저위험 메시지용 |

### Freshness Value 관리

| 방식 | 동작 | 장점 | 단점 |
|------|------|------|------|
| **카운터 기반** | 송/수신 양쪽이 카운터 증가 | 간단, 동기화 용이 | 전원 Off 시 카운터 복구 필요 |
| **타임스탬프 기반** | 글로벌 시간 참조 | replay 윈도우 명확 | 시간 동기화 인프라 필요 |
| **Freshness Manager** | AUTOSAR FVM이 중앙 관리 | 유연한 정책 | 복잡도 증가 |

### SecOC의 한계와 엣지 케이스

SecOC는 강력하지만 만능이 아니다. 면접에서 장점만 나열하면 깊이가 없어 보인다.

#### 엣지 케이스 1: ECU 부팅 직후 취약 구간 (Cold Start Problem)

```
ECU 전원 ON → RTOS 부팅 → SecOC 초기화 → Freshness 동기화
                                              │
                                    이 구간이 취약! (수백 ms ~ 수 초)
                                              │
                                    Freshness Value를 아직 모름
                                    → MAC 검증 불가 → 메시지 수용? 폐기?

AUTOSAR 대응:
  Option A: "Authentication Build-Up" — 처음 N개 메시지는 인증 없이 수용
    → 편의성 ✓, 보안 ✗ (공격자가 부팅 직후 injection 가능)

  Option B: "Strict Mode" — 인증 전 모든 메시지 폐기
    → 보안 ✓, 기능 ✗ (안전 임계 메시지도 폐기 → 브레이크 미작동?)

  Option C: "Freshness Manager 우선 동기화"
    → Freshness Manager ECU가 최우선 부팅 → sync 메시지 배포 → 나머지 ECU 인증 시작
    → 현실적 타협점이지만, FM ECU가 단일 장애점(SPOF)이 됨
```

#### 엣지 케이스 2: 키 로테이션 중 통신 중단

```
[키 전환 명령] ──broadcast──> 모든 ECU

  ECU-A: K_new 적용 완료 ✓ (새 키로 MAC 생성)
  ECU-B: K_new 적용 완료 ✓
  ECU-C: 아직 K_old 사용 중 ✗ (키 전환 지연)
         │
         └── ECU-A의 메시지를 K_old로 검증 → MAC 불일치 → 폐기!
             = 정상 메시지가 인증 실패하는 역설적 상황

대응: 키 전환 유예 기간 (Grace Period)
  - 전환 후 일정 시간 동안 K_old와 K_new 모두 유효
  - 양쪽 키로 검증 시도 → 하나라도 성공하면 수용
  - 유예 기간 종료 후 K_old 폐기
  - 트레이드오프: 유예 기간 중 K_old 유출 시 위험
```

#### 엣지 케이스 3: 레거시 ECU 혼재 (Mixed Network)

```
현대 차량의 현실:
  +------ CAN Bus ------+
  |                      |
  [HSM ECU] [HSM ECU] [레거시 ECU]  [레거시 ECU]
  SecOC ✓   SecOC ✓   SecOC ✗       SecOC ✗
  MAC 생성   MAC 검증   MAC 이해 불가  MAC 이해 불가
  
  문제:
  1. 레거시 ECU는 MAC 필드를 데이터로 오인 → 오동작
  2. 레거시 ECU의 메시지는 MAC 없음 → 위조 구별 불가
  3. SecOC 적용 범위가 부분적 → 체인의 가장 약한 고리

대응 전략:
  - Gateway에서 도메인 분리: SecOC 도메인 / 레거시 도메인
  - 레거시 도메인은 Gateway가 대신 MAC 검증/생성 (Proxy SecOC)
  - 장기적으로 레거시 ECU 교체 — 하지만 차량 수명 15~20년
```

#### 엣지 케이스 4: Truncated MAC의 보안 강도 한계

| 시나리오 | MAC 크기 | Brute-force 시도 | 위험 |
|---------|---------|-----------------|------|
| 4B MAC | 2^32 | 고속 CAN: ~43억 프레임 ≈ 수 시간 | ★★★ 위험 |
| 8B MAC | 2^64 | 현실적으로 불가능 | ★ 안전 |
| Freshness 없이 4B MAC | 2^32 | Replay로 우회 가능 | ★★★★ 매우 위험 |

→ AUTOSAR는 최소 8B MAC을 권장하지만, 대역폭 압박으로 4B를 선택하는 OEM이 존재. 반드시 Freshness Value와 함께 사용해야 한다.

### Tesla FSD 탈옥에 SecOC가 있었다면?

```
[탈옥 동글] ──OBD-II──> [CAN Bus]
     │
     ├── GPS 위조 프레임 주입 (MAC 없음)
     │        │
     │        v
     │   [FSD SoC의 SecOC 모듈]
     │        │
     │        ├── MAC 검증 → 실패 (키 없음)
     │        └── 프레임 폐기 ✓
     │
     └── 결론: SecOC만으로 탈옥 동글 완전 차단 가능
```

---

## Secure Gateway (도메인 격리)

### 왜 게이트웨이가 필요한가?

SecOC가 메시지를 인증하더라도, **도메인 간 불필요한 통신 자체를 차단**하는 것이 방어의 기본이다.

```
기존 Flat CAN 아키텍처 (Tesla 초기):
+-----+-----+-----+-----+-----+
| 엔진| ABS | ADAS| 인포 | OBD |  ← 전부 하나의 CAN Bus
+--+--+--+--+--+--+--+--+--+--+
   |     |     |     |     |
   +-----+-----+-----+-----+---- Single CAN Bus
   → OBD에서 ADAS까지 직접 접근 가능!

현대적 Domain Gateway 아키텍처:
                  +------------------+
                  | Central Gateway  |
                  | SoC (NXP S32G)   |
                  |                  |
                  | +----+ +------+  |
                  | |HSM | | IDS  |  |
                  | +----+ +------+  |
                  | +----+ +------+  |
                  | | FW | |Route |  |
                  | +----+ +------+  |
                  +--+----+----+-----+
                     |    |    |
            +--------+  +-+   +--------+
            |            |             |
    +-------v----+ +-----v------+ +----v-------+
    | Powertrain | | Chassis/   | | Infotain-  |
    | Domain     | | Safety     | | ment       |
    | CAN Bus    | | Domain     | | Domain     |
    |            | | CAN-FD     | | Ethernet   |
    +-------+----+ +-----+------+ +----+-------+
            |            |             |
        [엔진 ECU]   [ADAS, ABS]   [디스플레이]
                                       |
                                   [OBD-II]
                                       │
                    OBD → Infotainment까지만
                    Chassis/Safety 도메인 접근 ❌
```

### Gateway 보안 기능

| 기능 | 설명 |
|------|------|
| **도메인 격리** | Powertrain / Chassis / Body / Infotainment 물리적 분리 |
| **메시지 라우팅 규칙** | 화이트리스트 기반 — 허용된 메시지만 도메인 간 전달 |
| **Rate Limiting** | 비정상 전송 빈도 탐지 및 차단 |
| **프로토콜 변환** | CAN ↔ CAN-FD ↔ Ethernet 간 보안 정책 유지 |
| **OBD-II 격리** | 진단 포트를 별도 도메인에 배치, Safety 접근 차단 |
| **SecOC 검증** | 도메인 경계에서 MAC 검증 후 전달 |

---

## TEE (Trusted Execution Environment) in Automotive

### ARM TrustZone의 차량 적용

```
+----------------------------------------------+
|           Automotive Application SoC          |
|                                               |
|  +------------------+  +------------------+   |
|  | Non-Secure World |  | Secure World     |   |
|  | (Normal)         |  | (TrustZone)      |   |
|  |                  |  |                  |   |
|  | AUTOSAR OS       |  | TEE OS           |   |
|  | Application SW   |  | Secure Services: |   |
|  | CAN Stack        |  |  - Key Mgmt      |   |
|  | Infotainment     |  |  - SecOC Core    |   |
|  |                  |  |  - FW Update     |   |
|  |                  |  |  - GPS Integrity |   |
|  +--------+---------+  +--------+---------+   |
|           |      SMC Call       |              |
|           +-------->-----------+              |
|                                               |
|  ※ GPS 무결성 검증을 Secure World에서 수행하면 |
|    Normal World의 CAN 메시지로 위치를 속일 수   |
|    없다 — Tesla 탈옥의 핵심 방어              |
+----------------------------------------------+
```

### GPS 무결성 검증 — TEE 기반 접근

| 방법 | 구현 레벨 | 설명 |
|------|----------|------|
| **다중 소스 교차검증** | TEE 내부 | GPS + IMU + Wheel Speed + Camera VO를 Secure World에서 융합 |
| **Authenticated GNSS** | SoC + 안테나 | Galileo OSNMA — 위성 신호 자체에 서명 포함, SoC가 검증 |
| **CAN 독립 경로** | SoC 하드웨어 | GPS 수신기 → SoC 직결 (CAN 경유하지 않음) |
| **Geofence 서버 검증** | Cloud | 위치 정보를 서버에서 이중 확인 — 오프라인 시 동작 불가 |

---

## AUTOSAR 보안 스택 전체 구조

```
+-------------------------------------------------------+
|                    AUTOSAR Stack                       |
|                                                        |
|  +--------------------------------------------------+ |
|  | Application Layer                                 | |
|  |  SWC (Software Components)                        | |
|  +--------------------------------------------------+ |
|  | RTE (Runtime Environment)                         | |
|  +--------------------------------------------------+ |
|  | Service Layer                                     | |
|  |  +--------+  +--------+  +---------+  +--------+ | |
|  |  | SecOC  |  | Crypto |  |   CSM   |  |  IdsM  | | |
|  |  | Module |  | Service|  |(Crypto  |  |(IDS    | | |
|  |  |        |  | Mgr    |  | Service |  | Mgr)   | | |
|  |  |        |  |        |  | Mgr)    |  |        | | |
|  |  +---+----+  +---+----+  +----+----+  +---+----+ | |
|  |      |            |           |            |      | |
|  +------+------------+-----------+------------+------+ |
|  | ECU Abstraction Layer                             | |
|  |  +--------+  +----------+                         | |
|  |  | Crypto |  | CAN/ETH  |                         | |
|  |  | Driver |  | Driver   |                         | |
|  |  | (HSM)  |  |          |                         | |
|  |  +---+----+  +----+-----+                         | |
|  +------+-------------+-----------------------------+ |
|  | Hardware                                          | |
|  |  [HSM] [CAN Controller] [Ethernet MAC]            | |
|  +--------------------------------------------------+ |
+-------------------------------------------------------+

SecOC → CSM → Crypto Driver → HSM 하드웨어
= 메시지 인증 요청이 하드웨어 RoT까지 내려가는 체인
```

---

## 대표 문제

### Q1. "HSM이 있으면 CAN Bus 탈옥이 완전히 불가능한가?"

**사고 과정**:

1. HSM이 키를 보호하므로 외부 장치는 유효한 MAC을 생성할 수 없다
2. SecOC가 HSM의 키로 모든 CAN 메시지를 인증하면 → injection 차단
3. 하지만: HSM 자체의 물리적 공격(Side-channel, Fault Injection)은 가능
4. 또한: ECU 펌웨어 취약점으로 HSM API를 악용할 가능성 존재
5. 레거시 ECU(HSM 미탑재)가 혼재하면 인증 체인 끊김

**핵심 답변**: "HSM + SecOC는 소프트웨어적 CAN injection을 거의 완전히 차단한다. 하지만 '완전 불가능'은 아니다 — 세 가지 잔여 리스크가 있다: (1) HSM에 대한 물리적 공격(fault injection, SCA), (2) 정상 ECU의 펌웨어를 먼저 컴프로마이즈한 후 HSM API 악용, (3) SecOC 미지원 레거시 ECU와의 혼재. Secure Boot에서 Chain of Trust가 한 단계라도 깨지면 전체가 무효인 것처럼, SecOC도 모든 노드가 참여해야 의미가 있다."

### Q2. "SecOC의 성능 오버헤드는 얼마나 되는가?"

**사고 과정**:

1. CAN 2.0 (8B payload): MAC 추가 시 데이터 공간이 거의 없음 → 별도 프레임 필요 → 대역폭 2배
2. CAN-FD (64B payload): 8B MAC + 4B FV 추가해도 52B 데이터 가능 → 실용적
3. HSM의 AES-CMAC 연산: 하드웨어 가속 시 수 μs — CAN 프레임 간격(수백 μs~ms) 대비 무시 가능
4. Freshness Value 동기화: 주기적 sync 메시지 필요 — 추가 대역폭 소모
5. 키 관리: 초기 프로비저닝 + 런타임 키 로테이션의 운영 복잡도

**핵심 답변**: "CAN-FD 기준으로 SecOC의 직접 오버헤드는 미미하다: MAC 연산은 하드웨어 HSM이 수 μs에 처리하고, 64B payload에서 8~12B를 인증에 할당해도 실용적 데이터 크기를 유지한다. 실제 비용은 성능보다 **운영 복잡도** — 키 프로비저닝, Freshness 동기화, 레거시 호환성 관리 — 에 있다. 이것이 Tesla가 SecOC 대신 서버 측 검증만 의존한 이유로 추정된다."

---

## 확인 퀴즈

### Quiz 1. HSM의 키는 왜 Application Core에서 직접 읽을 수 없는가? 이 설계가 보안에 주는 이점은?

<details>
<summary>정답 보기</summary>

HSM은 Application Core와 **물리적으로 격리된 별도 코어**에서 동작하며, 키는 HSM 내부의 Secure Key Store(eFuse/OTP)에만 존재한다. Application Core는 HSM API를 통해 "이 데이터의 MAC을 계산해줘"라고 **연산 요청만** 할 수 있고, 키 자체를 읽어올 수 없다.

**이점**: Application Core의 펌웨어가 완전히 컴프로마이즈되더라도 (예: 원격 코드 실행 취약점), 공격자는 키를 추출할 수 없다. MAC 생성은 할 수 있지만(HSM API 악용), 키를 다른 장치에 복제하거나 오프라인 분석은 불가능하다. Secure Boot의 BootROM이 OTP에 저장된 ROTPK를 외부에 노출하지 않는 것과 같은 원리.
</details>

### Quiz 2. SecOC의 Freshness Value가 없으면 어떤 공격이 가능한가? 카운터 기반과 타임스탬프 기반 각각의 약점은?

<details>
<summary>정답 보기</summary>

Freshness Value 없이 MAC만 있으면 **Replay Attack**이 가능하다. 공격자가 과거의 유효한 CAN 프레임(정상 MAC 포함)을 녹화해두었다가 재전송하면, MAC은 여전히 유효하므로 수신 ECU가 수용한다.

약점:
- **카운터 기반**: ECU 전원 Off/On 시 카운터가 리셋되면, 이전에 캡처한 프레임의 카운터 값이 다시 유효해질 수 있다. 대응: NVM(비휘발 메모리)에 카운터 저장, 하지만 NVM 쓰기 수명과 속도 문제.
- **타임스탬프 기반**: 모든 ECU 간 시간 동기화가 필요하며, 시간 오차 허용 윈도우 내에서는 replay가 가능하다. 대응: 윈도우를 좁히되, 너무 좁히면 정상 메시지도 시간차로 폐기됨.
</details>

### Quiz 3. 레거시 ECU(HSM/SecOC 미탑재)가 혼재하는 CAN 네트워크에서 보안을 확보하는 현실적 방법은?

<details>
<summary>정답 보기</summary>

**Gateway 기반 Proxy SecOC**가 현실적 방법이다:
1. 네트워크를 도메인별로 물리 분리 (SecOC 도메인 / 레거시 도메인)
2. Central Gateway가 레거시 도메인의 메시지를 수신하면, Gateway 내부 HSM으로 MAC을 생성하여 SecOC 도메인으로 전달
3. 반대 방향도 동일 — Gateway가 MAC을 제거하고 레거시 ECU에 전달
4. 레거시 도메인은 Gateway의 Rate Limiting + IDS로 보호

한계: 레거시 도메인 내부에서의 injection은 여전히 방어 불가 → 장기적으로 ECU 교체가 유일한 해결책. 차량 수명이 15~20년이므로 완전 전환에는 상당한 시간이 필요하다.
</details>

---
!!! warning "실무 주의점 — SecOC 미지원 레거시 ECU와 혼재 시 보안 구멍"
    **현상**: SecOC가 적용된 신형 ECU와 미지원 레거시 ECU가 같은 CAN 버스에 공존하면, 레거시 ECU는 MAC 없이 메시지를 전송하므로 공격자가 해당 ID를 스푸핑해도 탐지되지 않는다.

    **원인**: SecOC는 수신 ECU가 MAC 검증을 하지 않으면 all-or-nothing 보호가 깨진다. 레거시 ECU 교체 일정이 차량 수명(15~20년)보다 짧지 않아 혼재 기간이 길어진다.

    **점검 포인트**: 네트워크 매트릭스에서 SecOC 미적용 송신자 ID 목록을 추출하고, Gateway의 Rate Limiter가 해당 ID에 대한 버스트 주입(동일 ID 연속 전송)을 차단하는지 `candump` 로그로 확인.

## 핵심 정리

- **HSM = 차량 내 Root of Trust** — Secure Boot 키, SecOC 세션 키, OTA 서명 키 모두 HSM에서 봉인된다.
- **SecOC = 메시지 무결성 + 프레시니스** — MAC만으로는 부족하며, 카운터/타임스탬프로 replay를 차단해야 한다.
- **Secure Gateway = 도메인 격리** — Powertrain / Chassis / Infotainment 사이에 화이트리스트 라우팅 + Rate Limiting을 강제한다.
- **IDS = 다층 방어의 최상단** — 시그니처/룰 기반 + ML 기반 이상 탐지로 0-day와 logic abuse를 잡는다.
- **레거시 호환성 ↔ 보안의 트레이드오프** — Proxy SecOC, 도메인 분리로 점진적 마이그레이션 필요.

## 다음 단계

- 다음 모듈: [Tesla FSD Case Study →](../03_tesla_fsd_case_study/) — 실제 Pwn2Own 2023 탈옥 체인을 따라가며 SoC 보안의 실패 지점을 분석한다.
- 퀴즈: [Module 02 Quiz](../quiz/02_automotive_soc_security_quiz/) — HSM 키 계층, SecOC, Gateway 격리에 대한 5문항.
- 실습: ISO/SAE 21434 표준 문서를 읽고, 현재 다루는 ECU 한 종류를 골라 위협 모델(자산/공격 surface/완화책)을 한 페이지로 작성해 보라.

<div class="chapter-nav">
  <a class="nav-prev" href="../01_can_bus_fundamentals/">
    <div class="nav-label">◀ 이전</div>
    <div class="nav-title">CAN Bus Fundamentals (차량 내부 통신의 구조와 한계)</div>
  </a>
  <a class="nav-next" href="../03_tesla_fsd_case_study/">
    <div class="nav-label">다음 ▶</div>
    <div class="nav-title">Tesla FSD Case Study (탈옥 사례 분석)</div>
  </a>
</div>
