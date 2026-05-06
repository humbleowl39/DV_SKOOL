# Module 03 — Tesla FSD Case Study

## 학습 목표 (Learning Objectives)

이 모듈을 마치면:

1. (Remember) 2023 Pwn2Own에서 공개된 Tesla FSD 탈옥 체인의 단계를 나열할 수 있다.
2. (Understand) "SoC에 SCS(보안 칩)가 있어도 CAN 인증이 없다면 무력화"되는 이유를 설명할 수 있다.
3. (Analyze) 탈옥 체인의 각 단계를 ① 기술적 결함 ② 정책적 결함 ③ 아키텍처 결함으로 분류할 수 있다.
4. (Evaluate) 같은 사건이 SecOC + Cloud 검증 기반 OEM에서 발생할 수 있는지 평가할 수 있다.
5. (Apply) Threat-modeling 시 Tesla 사례에서 얻은 교훈을 자기 프로젝트의 ECU에 적용할 수 있다.

## 선수 지식 (Prerequisites)

- Module 01 (CAN), Module 02 (HSM/SecOC/Gateway) 의 기본 어휘
- Bug bounty / responsible disclosure 절차에 대한 일반 상식
- 차량 OTA 업데이트 흐름 (서버 → 차량 → 인증 → 적용) 의 큰 그림

## 왜 이 모듈이 중요한가 (Why it matters)

이론으로 배운 보안 메커니즘이 실제 어디에서 깨지는지 가장 빠르게 배우는 방법은 **공개된 케이스 스터디 분석**이다. Tesla FSD 사례는 "비싼 보안 IP를 넣었는데도 한 줄 잘못된 가정 때문에 무력화"된 대표 예시다. 이 모듈은 학습자가 단순히 "이런 일이 있었다"가 아니라 **다음에 같은 실수를 반복하지 않도록 사고 패턴**을 만들어 준다.

---

## 핵심 개념
**Tesla FSD 탈옥은 CAN Bus 무인증 + GPS 기반 지오펜싱 + 로컬 Feature Flag 의존이라는 세 가지 약점의 교집합에서 발생했다. SoC에 보안 하드웨어(SCS)가 있었지만 CAN 통신 인증에 적용하지 않은 아키텍처 판단이 근본 원인이다.**

---

## 사건 타임라인

```
2019.04   HW3 (FSD Computer 1) 양산 시작 — SCS로 Secure Boot 적용, CAN 인증 미적용
2020.xx   HW3 MCU 탈옥 성공 (보안 연구자) — voltage glitching으로 Secure Boot 우회
2023.xx   HW4 (FSD Computer 2) 양산 시작 — 7nm 전환, 여전히 CAN 인증 미적용
2024.H1   Pwn2Own Automotive 2024 — Tesla 인포테인먼트 다수 취약점 발견
2024.H2   FSD 탈옥 동글 첫 등장 — 동유럽/중국 지하 시장에서 유통 시작
2025.Q1   탈옥 규모 확대 — 온라인 판매 증가, 유럽/아시아 비승인 지역 중심
2025.Q2   Tesla 텔레메트리로 대규모 탐지 시작 — GPS vs Cell Tower 불일치 패턴
2025.H2   Pwn2Own Automotive 2025 — FSD SoC 추가 취약점, Fault Injection 시연
2026.Q1   Tesla 원격 비활성화 — 10만+ 대 동시 FSD 차단, VIN 블랙리스트
2026.Q1   각국 규제 대응 — 한국 자동차관리법 집행 강화 (2년 징역/2천만 원)
2026.Q2   업계 파급 — SecOC 의무화 논의 가속, ISO 21434 구현 가이드라인 강화
```

**핵심 교훈**: SCS(Secure Boot + Cloud Auth)는 2019년부터 있었지만, CAN 통신 인증을 적용하지 않은 아키텍처 판단이 5년 후 10만 대 규모의 보안 사고로 이어졌다.

---

## 역사적 차량 해킹 사례 — FSD 탈옥과의 비교

Tesla FSD 탈옥은 차량 보안 역사에서 단독 사건이 아니다. 이전 사례들과 비교하면 공격 기법의 진화와 반복되는 패턴이 보인다.

### Jeep Cherokee 원격 해킹 (2015) — 차량 보안의 전환점

```
공격 경로:
  [인터넷] ──Cellular──> [Uconnect 인포테인먼트 (Sprint 3G)]
       │
       ├── 인포테인먼트 OS 취약점으로 원격 코드 실행
       │
       v
  [D-Bus 내부 통신] ──> [V850 CAN 게이트웨이 ECU]
       │
       ├── 게이트웨이 펌웨어 리플래시 (인증 없음!)
       │
       v
  [CAN Bus] ──> 조향, 브레이크, 가속 제어 가능
```

| 항목 | Jeep Cherokee (2015) | Tesla FSD (2025-26) |
|------|---------------------|---------------------|
| **진입점** | Cellular (원격, 물리 접근 불필요) | OBD-II (물리 접근 필요) |
| **핵심 취약점** | 게이트웨이 FW 리플래시 무인증 | CAN 메시지 무인증 |
| **영향** | 조향/브레이크 물리 제어 → **안전 위협** | 기능 잠금 우회 → **매출 손실** |
| **규모** | 140만 대 리콜 | 10만+ 대 원격 비활성화 |
| **근본 원인** | 도메인 미격리 + FW 서명 없음 | CAN 인증 없음 + GPS 단일 의존 |
| **산업 영향** | 차량 보안 연구 폭발적 증가 | SecOC 의무화 논의 가속 |

### BMW ConnectedDrive 해킹 (2015)

```
공격: ADAC(독일자동차클럽)이 발견
  - BMW의 ConnectedDrive 시스템이 HTTP (비암호화)로 통신
  - MITM 공격으로 차량 도어 원격 잠금 해제
  - 220만 대 영향 (BMW, Mini, Rolls-Royce)

교훈: 차량-서버 간 통신에도 TLS가 필수
  → Tesla FSD 비교: Tesla는 서버 통신 보안은 강력 (TLS + 서명)
     but 차량 내부 CAN 통신이 무방비
```

### Tesla Model S Key Fob 클론 (2018)

```
공격 (KU Leuven 연구팀):
  - Tesla Model S의 키폭이 DST40 암호화 사용 (40-bit, 취약)
  - Proximity Reader ($600) + Raspberry Pi로 키폭 신호 캡처
  - 1.6초 만에 키 복제 → 차량 탈취

  [공격자 장비] ──RF──> [키폭 Challenge 전송] ──> [키폭 응답 캡처]
       │                                              │
       └── 40-bit 키를 테이블 룩업으로 복원 ──────────┘
           → 복제 키폭 생성 → 차량 잠금 해제 + 시동

교훈: 
  - 약한 암호 알고리즘(DST40)은 시간이 지나면 반드시 깨진다
  - Tesla 대응: AES-128 기반 키폭으로 교체 + PIN to Drive
  → FSD 비교: SCS의 AES는 강력하지만, CAN 통신에 적용하지 않음
```

### 사례들의 공통 패턴

```
반복되는 패턴:
  1. "여기는 안전하다"는 가정 → 가정이 무너짐
     - CAN: "폐쇄 네트워크" → OBD-II로 개방
     - Jeep: "인포테인먼트는 격리됨" → CAN 게이트웨이 직접 접근
     - Tesla FSD: "서버 인증이면 충분" → CAN 우회

  2. 보안은 가장 약한 고리에서 깨진다
     - Jeep: 게이트웨이 FW 서명 미적용이 약한 고리
     - BMW: HTTP 통신이 약한 고리
     - Tesla FSD: CAN 무인증이 약한 고리

  3. 사후 대응보다 사전 설계가 저렴하다
     - Jeep: 140만 대 리콜 비용 >> 게이트웨이 서명 구현 비용
     - Tesla: $118M+/년 매출 손실 >> $10~30/대 SecOC 비용
```

---

## Tesla FSD 하드웨어 아키텍처

### HW3 (FSD Computer 1, 2019~)

```
+--------------------------------------------------+
|              FSD Computer 1 (HW3)                 |
|                                                    |
|  +---------------------+  +---------------------+ |
|  | FSD Chip A (Turbo A)|  | FSD Chip B (Turbo B)| |
|  |                     |  |                     | |
|  | ARM Cortex-A72 x12  |  | (동일 구성)         | |
|  | Neural Processing   |  | Dual Redundancy     | |
|  | Unit (NPU) x2       |  | - A/B 독립 연산    | |
|  | GPU (Mali)          |  | - 결과 비교         | |
|  | ISP (Image Signal)  |  | - 불일치 시 경고    | |
|  |                     |  |                     | |
|  | +---+ +---+         |  |                     | |
|  | |SCS| |SMS|         |  |                     | |
|  | +---+ +---+         |  |                     | |
|  +---------------------+  +---------------------+ |
|                                                    |
|  SCS = Security Subsystem                          |
|    - Secure Boot (BL 서명 검증)                    |
|    - FMP Key (Firmware Protection)                 |
|    - Weight Encryption Key (모델 보호)             |
|    - Board Credentials (Cloud 인증)                |
|                                                    |
|  SMS = Safety Management System                    |
|    - Watchdog, ECC, 오류 복구                      |
+--------------------------------------------------+
        │                │
        │  PCIe/CAN      │
        v                v
   [Camera x8]    [Vehicle CAN Bus]
   [Radar]        [GPS Module]
   [Ultrasonic]   [IMU]
```

### HW4 (FSD Computer 2, 2023~)

| 항목 | HW3 | HW4 |
|------|-----|-----|
| 공정 | Samsung 14nm | Samsung 7nm |
| NPU | 2개 (칩당 1) | 2개 (성능 3~5x 향상) |
| 카메라 입력 | 8대 (1.2MP) | 최대 11대 (5MP) |
| Ethernet | 미지원 | 지원 (고속 카메라 데이터) |
| 보안 | SCS (Secure Boot + Cloud Auth) | SCS 강화 + 추가 Anti-Tamper |
| **CAN 인증** | **❌ 미적용** | **❌ 여전히 미적용** |

---

## FSD 기능 활성화 메커니즘

### 정상 활성화 흐름

```
[Tesla 서버] ──────────────────────────> [차량 FSD SoC]
     │                                       │
     ├── VIN 확인                             │
     ├── 구독/구매 상태 확인                   │
     ├── 지역 승인 확인 (미국, 캐나다 등)      │
     ├── 규제 버전 매칭                        │
     │                                       │
     v                                       v
[Configuration Profile]              [로컬 Configuration]
  - 암호학적 서명 (VIN 바인딩)          - Feature Flags
  - FSD Enable/Disable               - Region Code
  - Region Lock                      - GPS Geofence
  - SW Version                       - 서버 프로파일 캐시
```

### 취약점 발생 지점

```
                    서버 검증 ✓
                        │
                        v
              [Configuration Profile]
              서명 검증 후 로컬 캐시
                        │
                 ┌──────┴──────┐
                 │             │
            [Feature Flag]  [Geofence]
            로컬에 저장     GPS 기반 판단
                 │             │
                 │        ┌────┴────┐
                 │        │         │
                 │   [GPS Module]  [CAN Bus]
                 │        │         │
                 │        │    <<<< 여기가 공격 지점 >>>>
                 │        │         │
                 │        │   [탈옥 동글이 위조 GPS/
                 │        │    Region 프레임 주입]
                 │        │         │
                 v        v         v
              [FSD Software Stack]
              "미국에 있고, FSD 활성화됨" → 동작 시작
```

**핵심 약점 3가지**:

| # | 약점 | 설명 |
|---|------|------|
| 1 | **CAN 무인증** | GPS 모듈 → FSD SoC 간 CAN 메시지에 MAC 없음 → 외부 주입 구별 불가 |
| 2 | **GPS 단일 의존** | 지오펜싱이 GPS 좌표에만 의존 → spoofing 시 우회 |
| 3 | **로컬 캐시 의존** | 서버 검증 후 로컬에 저장된 설정으로 동작 → 오프라인 시 로컬 값만 참조 |

---

## 탈옥 기법 상세 분석

### 공격 장비

```
[탈옥 동글] — USB 크기, €500~€2,000
     │
     ├── MCU (ARM Cortex-M 또는 ESP32 기반)
     ├── CAN Transceiver (MCP2515 등)
     ├── OBD-II 커넥터
     └── 펌웨어 (CAN 프레임 생성 로직)

연결: OBD-II 포트 → CAN Bus 직접 접근
전원: OBD-II Pin 16 (+12V)에서 공급
```

### 공격 단계

```
Step 1: CAN Bus 스니핑
  - 정상 동작 시 GPS 관련 CAN 프레임 캡처
  - Arbitration ID, DLC, Data 패턴 분석
  - Region Code 전달 프레임 식별

Step 2: 프레임 역공학
  - GPS 좌표가 CAN 프레임에 어떻게 인코딩되는지 파악
  - Feature Flag / Region Code 프레임 구조 분석
  - DBC 파일 (CAN Database) 참조 또는 리버스

Step 3: 위조 프레임 주입
  ┌─────────────────────────────────────────┐
  │ 원본 GPS 프레임 (실제 위치: 서울)        │
  │ ID: 0x318  Data: [37.5665, 126.9780]    │
  │              ↓ 동글이 차단/대체           │
  │ 위조 GPS 프레임 (가짜 위치: 캘리포니아)   │
  │ ID: 0x318  Data: [37.3861, -122.0839]   │
  └─────────────────────────────────────────┘

Step 4: Region Code 변조
  - 차량 설정의 지역 코드를 US로 위조
  - FSD 소프트웨어가 "승인된 시장"으로 판단

Step 5: 지속적 주입
  - 동글이 상시 동작하며 위조 프레임 반복 전송
  - 정상 GPS ECU의 실제 프레임보다 높은 빈도로 전송
  - FSD SoC는 최신 수신 값을 사용 → 위조 값 채택
```

### 왜 동작했는가 — Root Cause 분석

```
Root Cause Tree:

[FSD가 비승인 지역에서 동작]
     │
     ├── [GPS 좌표가 위조됨]
     │       │
     │       ├── [CAN 프레임에 MAC 없음] ← 근본 원인 #1
     │       │     → SecOC 미적용
     │       │
     │       └── [GPS 수신기가 CAN 경유] ← 근본 원인 #2
     │             → SoC 직결이 아닌 CAN Bus 경유
     │
     ├── [Region Code가 변조됨]
     │       │
     │       └── [설정 프레임에 인증 없음] ← 근본 원인 #1과 동일
     │
     └── [서버 검증 우회]
             │
             ├── [오프라인 시 로컬 캐시 사용] ← 근본 원인 #3
             └── [텔레메트리 주기적 → 실시간 아님]
```

---

## Tesla의 대응 분석

### 사후 대응 (2026년 4월)

| 대응 | 방법 | 효과 | 한계 |
|------|------|------|------|
| **원격 비활성화** | OTA로 FSD 기능 차단 | 즉각적, 10만+ 대 동시 처리 | 사후 대응 — 이미 수개월 운행 |
| **텔레메트리 탐지** | GPS 궤적 vs 셀 타워/IP 위치 불일치 탐지 | 높은 탐지율 | 인터넷 미연결 시 탐지 지연 |
| **영구 FSD 차단** | VIN 블랙리스트, 보증 거부 | 강력한 억제 효과 | 합법적 중고차 구매자 피해 가능 |
| **법적 대응** | 각국 규제 기관과 협력 | 판매자 처벌 | 오픈소스 도구는 근절 어려움 |

### 기술적 대응의 약점

```
Tesla의 현재 방어:
  Server-side ← → Vehicle
  (강력)          (약함)

  서버: VIN 서명, 텔레메트리, OTA → ✓ 강력
  차량 내부: CAN 무인증, 로컬 캐시 → ✗ 취약

  = "성 밖은 견고하지만 성 안은 누구든 걸어 다닐 수 있는" 구조
```

---

## 교훈: "했어야 했던 것" vs "한 것"

### SoC 레벨 방어 — 비교

| 방어 수단 | Tesla가 한 것 | 했어야 한 것 |
|----------|-------------|------------|
| **Secure Boot** | ✅ SCS로 FW 서명 검증 | ✅ (이미 적용) |
| **Cloud Auth** | ✅ VIN 기반 서버 검증 | ✅ (이미 적용) |
| **CAN 메시지 인증** | ❌ 미적용 | ✅ SecOC + HSM |
| **도메인 격리** | ❌ Flat CAN 구조 | ✅ Secure Gateway |
| **GPS 무결성** | ❌ CAN 경유 GPS 신뢰 | ✅ TEE 내 다중 소스 검증 |
| **OBD-II 격리** | ❌ 전체 CAN 접근 허용 | ✅ 진단 도메인 분리 |
| **IDS** | △ 텔레메트리 기반 | ✅ 실시간 CAN IDS |

### 비용 분석 — SecOC 도입 비용 vs 탈옥 피해

| 항목 | 추정 비용 |
|------|----------|
| HSM 탑재 ECU 추가 비용 | $1~5 / ECU (대량 생산 시) |
| SecOC 펌웨어 개발 | 일회성 엔지니어링 비용 |
| 키 관리 인프라 | 서버 인프라 + PKI |
| **합계 (차량당)** | **$10~30 추정** |
| | |
| FSD 탈옥 피해 (10만 대) | $99/월 × 12개월 × 100,000 = **$118M+/년 매출 손실** |
| 브랜드/규제 리스크 | 정량화 불가 — 자율주행 신뢰도 훼손 |

---

## 다른 OEM과의 비교

| | Tesla | BMW/Mercedes (최신) | 현대/기아 (최신) |
|--|-------|-------------------|----------------|
| **CAN 인증** | ❌ | ✅ SecOC (부분 적용) | ✅ SecOC (신차) |
| **Gateway** | △ 부분적 | ✅ Central Gateway | ✅ ccGW |
| **HSM** | SCS (Boot용) | EVITA Full | SHE → HSE 전환 중 |
| **OBD 격리** | ❌ | ✅ | ✅ |
| **IDS** | 텔레메트리 | ✅ 차량 내 IDS | ✅ |
| **OTA 보안** | ✅ 업계 최고 | ✅ | ✅ |

**아이러니**: Tesla는 OTA와 클라우드 보안에서 업계를 선도하면서, 차량 내부 통신 보안에서는 전통 OEM보다 뒤처져 있었다.

---

## 대표 문제

### Q1. "Tesla는 왜 SecOC를 적용하지 않았는가?"

**사고 과정**:

1. Tesla는 2012년부터 차량 생산 — 초기 아키텍처 시점에 SecOC/AUTOSAR 미채택
2. Tesla는 AUTOSAR를 사용하지 않음 — 자체 소프트웨어 스택
3. 중앙집중 아키텍처(모든 ECU 자체 설계) → "내부는 안전하다"는 가정
4. SecOC는 키 관리 인프라 필요 → 운영 복잡도 증가
5. 서버 측 검증(OTA + 텔레메트리)이 충분하다고 판단

**핵심 답변**: "세 가지 이유가 복합적이다: (1) Tesla는 AUTOSAR 비채택으로 SecOC 에코시스템 밖에 있었다, (2) 모든 ECU를 자체 설계하는 중앙집중 구조에서 '내부 통신은 신뢰 가능'이라는 가정을 했다, (3) 서버 측 OTA 검증의 강점이 차량 내부 보안의 약점을 보상한다고 판단했다. 이는 Secure Boot에서 'BootROM만 있으면 되지, OTP는 왜 필요하냐'라고 묻는 것과 같다 — 두 레이어가 모두 있어야 한다."

### Q2. "이 사건이 자율주행 보안 규제에 미치는 영향은?"

**사고 과정**:

1. UN R155 (차량 사이버보안 관리 시스템) — 이미 2024년부터 신차 의무
2. ISO/SAE 21434 (차량 사이버보안 엔지니어링) — 개발 프로세스 표준
3. 한국: 자동차관리법 개정 — FSD 탈옥 2년 이하 징역
4. 이 사건으로 규제 집행이 가속화되고, CAN 인증 의무화 논의 촉진

**핵심 답변**: "규제 프레임워크(UN R155, ISO 21434)는 이미 존재하지만, 구현 수준의 세부 요구사항(SecOC 의무화 등)은 각국 재량이었다. Tesla FSD 탈옥은 10만 대 규모의 실증 사례로서 'CAN 인증 없이는 소프트웨어 정의 차량의 기능 잠금이 무의미하다'를 증명했고, 이는 각국의 구현 수준 규제 강화를 가속할 것이다."

---

## 확인 퀴즈

### Quiz 1. Tesla FSD 탈옥의 세 가지 근본 원인을 순서대로 설명하고, 각각 어떤 방어 수단이 대응되는지 연결하라.

<details>
<summary>정답 보기</summary>

| # | 근본 원인 | 대응 방어 수단 |
|---|----------|--------------|
| 1 | **CAN 메시지 무인증** — GPS/Region 프레임에 MAC이 없어 외부 주입과 정상 메시지를 구별할 수 없었다 | **SecOC** — HSM 기반 MAC으로 발신자 인증 |
| 2 | **GPS 단일 소스 의존** — 지오펜싱이 CAN 경유 GPS 좌표에만 의존하여 spoofing에 취약했다 | **TEE 내 다중 소스 교차검증** — GPS + IMU + Wheel Speed + Cell Tower를 Secure World에서 융합 |
| 3 | **로컬 캐시 의존** — 서버 검증 후 로컬에 저장된 설정으로 동작하여 오프라인 시 로컬 값만 참조했다 | **실시간 서버 검증 + Heartbeat** — 주기적 검증 실패 시 기능 비활성화 |

핵심: 세 가지가 **동시에** 존재했기 때문에 탈옥이 성공했다. 하나라도 방어되었으면 공격 난이도가 크게 상승했을 것이다.
</details>

### Quiz 2. Jeep Cherokee(2015)와 Tesla FSD(2025-26) 해킹의 결정적 차이점은 무엇이고, 왜 Tesla FSD가 업계에 더 큰 파급을 미치는가?

<details>
<summary>정답 보기</summary>

**결정적 차이**:
- Jeep Cherokee: **원격 공격**(Cellular) → 조향/브레이크 **물리 제어** → 직접적 **안전 위협** (Safety)
- Tesla FSD: **물리 접근 필요**(OBD-II) → 기능 잠금 **우회** → 직접적 **매출 손실** (Financial)

**Tesla FSD가 더 큰 파급을 미치는 이유**:
1. **규모**: 10만+ 대로 Jeep(개별 시연)보다 실제 피해 규모가 압도적
2. **비즈니스 모델 위협**: 자동차 산업의 "소프트웨어 정의 차량(SDV)" + "구독 모델"이라는 미래 수익 모델을 근본적으로 위협
3. **재현 용이성**: €500 동글이면 누구나 가능 vs Jeep은 고도의 기술 필요
4. **산업 방향 전환**: CAN 인증이 "있으면 좋은 것"에서 "비즈니스 존속을 위한 필수"로 인식 전환
</details>

### Quiz 3. Tesla의 SCS(Security Subsystem)는 Secure Boot과 Cloud Auth를 지원하는데, 왜 같은 하드웨어로 CAN 인증을 하지 않았다고 추정되는가?

<details>
<summary>정답 보기</summary>

세 가지 복합적 이유:
1. **아키텍처 철학**: Tesla는 AUTOSAR를 채택하지 않고 자체 SW 스택을 사용 → SecOC 에코시스템(AUTOSAR SecOC 모듈, Freshness Manager 등) 밖에 있었으므로, 자체 구현이 필요했다.
2. **설계 가정**: 모든 ECU를 자체 설계하는 중앙집중 구조에서 "내부 CAN은 신뢰 가능"이라는 가정을 했다. SCS는 **외부와의 경계**(Boot, Cloud)를 보호하는 데 집중.
3. **비용 대비 효과 판단**: 수백 개의 CAN 메시지에 실시간 MAC 연산 + 키 관리 + Freshness 동기화의 운영 복잡도를 서버 측 텔레메트리로 대체할 수 있다고 판단.

이 판단이 틀렸음이 증명된 것이다 — **외부 경계(서버)만 방어하고 내부 경계(CAN)를 방어하지 않으면, 물리 접근 시 내부는 무방비**라는 교훈.
</details>

---

## 핵심 정리 (Key Takeaways)

- **외부 방어 ≠ 내부 방어** — Secure Boot로 부팅 체인을 지켜도 CAN 인증이 없으면 물리 접근에 그대로 노출된다.
- **Feature Flag = 정책일 뿐, 보안 경계가 아니다** — 로컬 플래그를 신뢰하면 차량이 곧 정책 결정자가 된다.
- **GPS 같은 외부 신호는 spoof 가능하다** — 지오펜스를 단독 보안 통제로 쓰면 안 된다.
- **자체 SW 스택의 함정** — AUTOSAR/SecOC 에코시스템 밖이면 같은 기능을 자체 구현해야 하며, 누락 위험이 크다.
- **케이스 스터디는 위협 모델의 출발점** — 공개된 익스플로잇 체인은 자체 ECU의 가정을 검증하는 가장 빠른 도구다.

## 다음 단계 (Next Steps)

- 다음 모듈: [Attack Surface & Defense →](../04_attack_surface_and_defense/) — 외부/내부/공급망 공격 표면을 체계화하고 각 계층의 방어 매핑을 정리한다.
- 퀴즈: [Module 03 Quiz](../quiz/03_tesla_fsd_case_study_quiz/) — 탈옥 체인, 근본 원인, 구조적 교훈에 대한 5문항.
- 실습: 자신의 회사/팀 ECU 한 종류를 골라 Tesla 사례의 5단계를 그대로 적용해 "여기서 같은 일이 가능한가?" 표로 정리해 본다.

<div class="chapter-nav">
  <a class="nav-prev" href="../02_automotive_soc_security/">
    <div class="nav-label">◀ 이전</div>
    <div class="nav-title">Automotive SoC Security (차량 SoC 보안 아키텍처)</div>
  </a>
  <a class="nav-next" href="../04_attack_surface_and_defense/">
    <div class="nav-label">다음 ▶</div>
    <div class="nav-title">Attack Surface & Defense (공격 표면과 방어 계층)</div>
  </a>
</div>
