# Module 05 — Quick Reference Card

<!-- DV-SKOOL-CH-CTX:start -->
<div class="chapter-context" data-cat="soc">
  <a class="chapter-back" href="../">
    <span class="chapter-back-arrow">←</span>
    <span class="chapter-back-icon">🚗</span>
    <span class="chapter-back-text">Automotive Cybersec</span>
  </a>
  <span class="chapter-divider">›</span>
  <span class="chapter-marker chapter-quickref-marker">★ Quick Reference</span>
</div>
<!-- DV-SKOOL-CH-CTX:end -->

<!-- DV-SKOOL-CH-TOC:start -->
<div class="page-toc">
  <span class="page-toc-label">목차</span>
  <a class="page-toc-link" href="#1-why-care-이-카드가-왜-필요한가">1. Why care?</a>
  <a class="page-toc-link" href="#2-intuition-비유와-한-장-그림">2. Intuition</a>
  <a class="page-toc-link" href="#3-작은-예-secure-boot-와-자동차-보안의-개념-1-1-매핑">3. 작은 예 — Secure Boot ↔ Automotive 1:1 매핑</a>
  <a class="page-toc-link" href="#4-일반화-4-3-매트릭스-와-공격-방어-매핑">4. 일반화 — 4×3 매트릭스</a>
  <a class="page-toc-link" href="#5-디테일-비교표-defense-layer-타임라인-규제-키워드-맵">5. 디테일</a>
  <a class="page-toc-link" href="#6-흔한-오해-와-이-카드를-봐야-할-때">6. 흔한 오해 + 이 카드를 봐야 할 때</a>
  <a class="page-toc-link" href="#7-핵심-정리-key-takeaways">7. 핵심 정리</a>
</div>
<!-- DV-SKOOL-CH-TOC:end -->

!!! objective "학습 목표"
    이 모듈을 마치면:

    - **Recall** CAN / SecOC / HSM / Gateway / IDS / V2X 의 핵심 한 줄 정의를 즉시 떠올릴 수 있다.
    - **Apply** 면접 / 리뷰에서 차량 보안 토픽이 나왔을 때 30 초 안에 구조화해 답할 수 있다.
    - **Evaluate** 자기 시스템에 빠진 보안 계층이 무엇인지 cheat sheet 와 비교해 판별할 수 있다.

!!! info "사전 지식"
    - [Module 01](01_can_bus_fundamentals.md) ~ [Module 04](04_attack_surface_and_defense.md) 완료 — 이 모듈은 새 내용을 가르치지 않고 _압축_ 합니다.

---

## 1. Why care? — 이 카드가 왜 필요한가

복습 + 인터뷰 / 리뷰 / TARA workshop 직전 _즉시 꺼내볼 수 있는 1-page cheat sheet_ 가 필요합니다. 이 모듈은 학습한 내용을 **머릿속 인덱스** 로 굳히는 역할 — 4 개의 long-form 모듈을 거친 후 _세부는 모두 잊어도 cheat sheet 의 셀 하나만 보면 거기서 출발해 5 분 안에 깊은 답변을 재구성할 수 있는_ 압축 매핑.

이 카드의 가치는 _Tesla 사례를 읽은 5 분 후, 자기 ECU 의 layer 매핑을 정확히 그릴 수 있는가_ 의 효율로 측정됩니다.

---

## 2. Intuition — 비유와 한 장 그림

!!! tip "💡 한 줄 비유"
    **Automotive Security 마스터** ≈ **4×3 매트릭스를 머릿속에서 즉시 그릴 수 있는 사람**. 4 layer (HSM / SecOC / Gateway / IDS) × 3 surface (OBD / 무선 / 공급망) 의 12 셀 _각각이 어떤 attack 을 차단하는지_ 와 _trade-off 가 무엇인지_ 를 즉답할 수 있는 것이 마스터.

### 한 장 그림 — 4 layer × 3 surface 인덱스

```
          │ OBD (물리)        │ 무선             │ 공급망
──────────┼──────────────────┼─────────────────┼──────────────────
 HSM (L1) │ JTAG fuse,       │ 키 보호 → spoof │ FW 서명 root
          │ 키 봉인          │ 못함            │ key
──────────┼──────────────────┼─────────────────┼──────────────────
 SecOC(L2)│ CAN injection    │ MACsec / TLS    │ ECU 간 mutual
          │ 차단             │ → 무선 frame    │ auth
──────────┼──────────────────┼─────────────────┼──────────────────
 GW (L3)  │ OBD ↔ Safety    │ TCU ↔ CAN      │ 도메인 격리
          │ 격리             │ 방화벽           │
──────────┼──────────────────┼─────────────────┼──────────────────
 IDS (L4) │ CAN anomaly      │ 무선 anomaly    │ 행동 anomaly
          │ (주기, 빈도)     │ (V2X plausib.)  │ (서명 빈도)
```

이 12 셀 + Cloud (L5) + 물리 (L0) = 18 셀이 차량 보안의 _실용적 인덱스_.

### 왜 매트릭스 인지가 본질인가 — Rationale

면접관 / 리뷰어가 던지는 질문은 _하나의 셀에서 출발_ 합니다 — "GPS spoofing 어떻게 막죠?" 는 _SecOC × OBD_ 셀 하나. 그러나 좋은 답변은 _주변 셀과 함께_ 그립니다 — "L2 SecOC 가 1 차, L1 TEE 가 2 차, L4 IDS 가 탐지 보강" 의 3 셀 결합. 즉 _12 셀 매트릭스 자체가 답변의 골격_.

---

## 3. 작은 예 — Secure Boot 와 자동차 보안의 개념 1:1 매핑

cheat sheet 에서 가장 _자주 쓰는 시나리오_: 면접에서 "자동차 보안 모르는데 Secure Boot 는 안다" 면 어떻게 답하나? **개념 매핑 표 1 개로 5 분 안에 깊이 있는 답변 가능**.

### 매핑 표 — Secure Boot ↔ Automotive Security

| Secure Boot 개념 | Automotive Security 대응 | 공통 원리 | Tesla 사례 위치 |
|---|---|---|---|
| **HW RoT** (BootROM + OTP) | **HSM** (Isolated Core + Key Store) | 변경 불가한 신뢰 기반 | SCS = 이 자리 (Tesla 가 _가짐_) |
| **Chain of Trust** (BL1→BL2→BL3) | **SecOC 인증 체인** (모든 ECU 참여) | 한 단계 깨지면 전체 무효 | _없음_ — Tesla 의 빈 자리 |
| **서명 검증** (RSA / ECDSA) | **MAC 검증** (AES-CMAC) | 위조 불가 인증 | _없음_ — Tesla 의 빈 자리 |
| **Anti-Rollback** (OTP Counter) | **Freshness Value** (Replay 방어) | 재사용 공격 방지 | OTA 에는 적용, CAN 에는 없음 |
| **Secure Debug** (JTAG Lock) | **OBD-II Gateway** (진단 격리) | 디버그 인터페이스 통제 | _없음_ — Tesla flat CAN |
| **TrustZone** (Secure World) | **TEE** (GPS / 키 관리 격리) | 신뢰 실행 환경 분리 | _없음_ — GPS 가 Normal World |
| **Measurement** (PCR / Hash chain) | **VIN-bound Config 서명** | 부팅 후 상태 증명 | OTA Profile 에 적용 |

### 매핑의 5 step 활용 (면접 답변 골든 구조)

```
Step 1: 한 줄 핵심
   "Automotive 보안은 Secure Boot 의 _통신 버전_ 입니다."

Step 2: 왜 (배경)
   "CAN 은 1983 년 폐쇄 네트워크 가정으로 인증이 빠졌고,
    OBD-II 가 그 가정을 깼으니 Secure Boot 처럼 _체인_
    이 필요해졌습니다."

Step 3: 어떻게 (메커니즘 — §3 의 매핑 표 사용)
   "BootROM 자리에 HSM, BL 서명 자리에 SecOC MAC,
    TrustZone 자리에 TEE — 1:1 대응이 됩니다."

Step 4: 한계 / 트레이드오프
   "단, 통신 체인은 _노드 수가 수십~수백_ 이라 Secure
    Boot 보다 키 관리 / Freshness 동기화가 훨씬 복잡."

Step 5: Tesla 사례로 마무리
   "Tesla 는 BootROM (SCS) 만 있고 BL 서명 (SecOC) 이
    없는 구조였고, 그래서 OBD-II 동글에 뚫렸습니다."
```

!!! note "여기서 잡아야 할 두 가지"
    **(1) 기존 지식 (Secure Boot) 을 경량 매핑으로 변환** — 새 도메인에서 처음부터 외울 필요 없음. 7 행짜리 매핑 표 하나로 _시야의 폭_ 이 즉시 확장.<br>
    **(2) Tesla 사례가 _빈 자리_ 를 가시화** — 매핑 표의 우측에 "Tesla 가 가진 / 빠진" 을 표시하면 사례 분석이 자동으로 따라옴.

---

## 4. 일반화 — 4×3 매트릭스 와 공격/방어 매핑

### 4.1 핵심 정리 한 줄 요약

| 주제 | 핵심 포인트 |
|---|---|
| CAN 구조적 결함 | 무인증, 무암호화, 브로드캐스트, 무상태 — 1980 년대 폐쇄 네트워크 가정 |
| CAN-FD vs CAN-XL | FD = 큰 payload (64 B) / 보안 없음, XL = CANsec 내장 (AES-GCM) |
| HSM | ECU 내 격리된 보안 코어 — 키 저장 + MAC 연산, API 만 노출 |
| SecOC | AUTOSAR CAN 메시지 인증 — Data + Truncated MAC (4–8 B) + Freshness |
| Secure Gateway | 도메인 격리 + 메시지 라우팅/필터 + OBD-II 격리 |
| TEE (TrustZone) | Secure World 에서 GPS 무결성/키 관리 — Normal World CAN 위조 차단 |
| IDS | 규칙/주기/ML 기반 CAN 이상 탐지 — 방지가 아닌 탐지 |
| Tesla FSD 탈옥 | CAN injection (GPS spoofing) + Region Code 변조 — SecOC 부재가 원인 |
| 규제 | UN R155 (CSMS), ISO 21434, 자동차관리법 (2 년 징역 / 2 천만 원) |

### 4.2 공격/방어 매트릭스

| 공격 | 진입점 | 방어 수단 | 레이어 |
|---|---|---|---|
| CAN Injection | OBD-II | SecOC + Gateway 격리 | L0 + L2 |
| CAN Replay | OBD-II | Freshness Value (카운터/타임스탬프) | L2 |
| CAN DoS / Bus-Off | OBD-II | Rate Limiting + IDS | L3 |
| GPS Spoofing (CAN) | OBD-II | TEE 다중소스 검증 | L1 + L2 |
| GPS Spoofing (RF) | 무선 | Authenticated GNSS (Galileo OSNMA) | L1 |
| Cellular Exploit | TCU | 방화벽 + Gateway 격리 | L0 + L3 |
| FW Extraction | JTAG | Secure Debug + eFuse | L1 |
| Fault Injection | 칩 물리 | Anti-Tamper + 이중 검증 | L1 |
| OTA Hijack | 서버 | 코드 서명 + VIN 바인딩 + Anti-Rollback | L5 |
| Supply Chain | 공급망 | Secure Boot + FW 서명 | L1 + L5 |
| Key Fob Relay | RF | UWB ToF | L1 |
| V2X Sybil | DSRC/C-V2X | SCMS PKI + Misbehavior Detection | L5 + L4 |

---

## 5. 디테일 — 비교표, Defense Layer, 타임라인, 규제, 키워드 맵

### 5.1 CAN Bus 한 줄 요약
```
CAN(1983) = 브로드캐스트 버스, 무인증/무암호화 → OBD-II 로 외부 접근 시 전체 위조 가능
```

### 5.2 프로토콜 비교

| | CAN 2.0 | CAN-FD | CAN-XL | Auto Ethernet |
|--|---|---|---|---|
| 속도 | 1 Mbps | 8 Mbps | 20 Mbps | 100 M – 10 Gbps |
| Payload | 8 B | 64 B | 2048 B | MTU 1500 B+ |
| 보안 내장 | ❌ | ❌ | ✅ CANsec | ✅ MACsec |
| SecOC 가능 | △ (공간 부족) | ✅ | 불필요 (내장) | 불필요 |
| 용도 | 레거시 ECU | 고속 ECU | 차세대 | ADAS / 카메라 |

### 5.3 SoC 보안 모듈 비교

| | SHE | EVITA Medium | EVITA Full | Tesla SCS |
|--|---|---|---|---|
| 대칭키 | AES-128 | AES-128/256 | AES-128/256 | AES |
| 비대칭키 | ❌ | ❌ | RSA, ECC | RSA, ECC |
| 키 슬롯 | 11 | 수십 | 수백 | 가변 |
| 용도 | 기본 CAN 인증 | ECU 보안 | 게이트웨이 / ADAS | Boot + Cloud |
| CAN SecOC | ✅ | ✅ | ✅ | ❌ 미적용 |

### 5.4 Tesla FSD 탈옥 — Root Cause 한 줄 정리

```
SoC 에 보안 HW (SCS) 가 있었지만 CAN 통신 인증에 미적용
→ OBD-II 동글이 GPS / Region 위조 CAN 프레임 주입
→ FSD SoC 가 위조 프레임을 정상으로 수용
→ 비승인 지역에서 FSD 동작

대응: SecOC (차단) + Gateway (격리) + IDS (탐지) = 원천 방어 가능
```

### 5.5 Defense in Depth — 6 Layer

```
L5: Cloud / OTA — 서명, VIN 바인딩, 텔레메트리, 원격 비활성화
L4: Application — Secure Coding, Input Validation, Fuzzing
L3: Network — IDS / IPS, Firewall, Rate Limiting, Anomaly Detection
L2: Communication — SecOC (CAN), MACsec (Eth), TLS, CANsec (XL)
L1: Platform — Secure Boot, HSM, TEE, Anti-Tamper, Secure Debug
L0: Physical — OBD 격리, 포트 비활성화, 물리 접근 제어
```

### 5.6 Secure Boot 와의 개념 대응

§3 의 매핑 표를 그대로 보존 — 별도 위치 (디테일) 에 다시 두지 않습니다. §3 참조.

### 5.7 면접 골든 룰 8 가지

1. **CAN**: "무인증" 만 말하지 말고 — "1983 년 설계 가정 (폐쇄 네트워크) 이 OBD-II / 텔레매틱스로 무너졌다" 고 맥락 설명.
2. **SecOC**: "MAC 추가" 만 말하지 말고 — "HSM 키 → CMAC 생성 → Freshness 로 replay 방어" 의 전체 체인 설명.
3. **Gateway**: "방화벽" 만 말하지 말고 — "도메인 격리 + 화이트리스트 라우팅 + 프로토콜 변환" 3 기능 설명.
4. **Tesla 사례**: 비난이 아닌 **아키텍처 분석** — "서버 보안은 강했지만 차량 내부 통신 인증 부재".
5. **Defense in Depth**: 항상 Secure Boot 와 연결 — "부팅 체인의 무결성 = 통신 체인의 무결성과 같은 원리".
6. **공격자 관점 먼저**: "이런 방어를 한다" 가 아니라 "이런 공격이 가능하므로 → 이렇게 방어한다".
7. **트레이드오프**: SecOC 의 장점만이 아니라 "키 관리 복잡도, 레거시 호환성, 대역폭 오버헤드" 도 언급.
8. **규제 인식**: 기술뿐 아니라 UN R155, ISO 21434, TARA 프레임워크 언급.

### 5.8 흔한 실수와 올바른 답변

| 실수 | 왜 위험한가 | 올바른 답변 |
|---|---|---|
| "CAN 에 암호화 추가하면 해결" | SecOC 는 인증이지 암호화 아님 | "SecOC 는 MAC 으로 발신자 인증 — 암호화 (기밀성) 와 인증 (무결성) 은 다른 목표" |
| "Tesla 가 보안을 무시했다" | SCS, Secure Boot, OTA 서명은 강력 | "서버 보안은 업계 최고, CAN 통신 인증이 빠진 것이 문제" |
| "HSM 이면 완벽" | 물리 공격, FW 취약점 존재 | "HSM 은 SW 공격 차단, 물리 공격 (FI/SCA) 은 별도 Anti-Tamper" |
| "IDS 가 공격을 막는다" | IDS 는 탐지, 방지 아님 | "IDS 는 탐지, SecOC 는 방지 — 둘 다 필요" |
| 공격 vector 1 개만 답변 | 시야 좁아 보임 | 물리 / 무선 / 공급망 3 축으로 분류 답변 |

### 5.9 차량 보안 역사 타임라인

```
1983  CAN Bus 개발 (Robert Bosch) — 보안 미고려, 폐쇄 네트워크 가정
1993  ISO 11898 표준화
1996  OBD-II 의무화 (미국 EPA) — CAN Bus 외부 접근점 생성
2010  실험적 CAN 해킹 논문 (UCSD/UW) — 학계 위험성 입증
2015  ★ Jeep Cherokee 원격 해킹 — 140 만 대 리콜, 차량 보안 전환점
2015  BMW ConnectedDrive HTTP 해킹 — 220 만 대, TLS 필수 인식
2016  AUTOSAR SecOC 사양 발표
2017  SHE 2.0 + EVITA 표준 확산 — HSM 기반 ECU 보안 본격화
2018  Tesla Model S Key Fob 클론 (KU Leuven) — DST40 취약
2019  Tesla HW3 (FSD Computer 1) 양산 — SCS 적용, CAN 인증 미적용
2020  Tesla HW3 MCU 탈옥 — Voltage Glitching 으로 Secure Boot 우회
2021  UN R155 / R156 채택 — 차량 사이버보안 / SW 업데이트 의무화
2022  UWB 기반 디지털 키 도입 (BMW) — Key Fob Relay 방어
2023  Tesla HW4 양산 — 7 nm, 여전히 CAN 인증 미적용
2024  Pwn2Own Automotive 2024 — Tesla 인포테인먼트 다수 취약점
2024  UN R155 / R156 신차 의무 시행 — 비준수 시 형식 승인 불가
2025  ★ Tesla FSD 탈옥 동글 대규모 유통 — CAN injection 으로 지오펜스 우회
2026  Tesla 10 만+ 대 원격 비활성화 — 한국 자동차관리법 집행 강화
2026  SecOC 의무화 논의 가속 — ISO 21434 구현 가이드라인 강화
```

### 5.10 면접 핵심 키워드 맵

| 주제 | 필수 키워드 (빠지면 감점) | 차별화 키워드 (있으면 가산점) |
|---|---|---|
| **CAN Bus** | 브로드캐스트, 무인증, Arbitration ID, OBD-II | Error Counter, Bus-Off, 설계 가정 변화 |
| **CAN 진화** | CAN-FD (64 B), CAN-XL (CANsec), 프로토콜 vs 어플리케이션 계층 | AES-GCM, BRS (Bit Rate Switch) |
| **HSM** | 격리 코어, 키 저장, API 만 노출, 외부 접근 불가 | SHE vs EVITA, 키 프로비저닝 라이프사이클 |
| **SecOC** | AUTOSAR, Truncated MAC, Freshness Value, Replay 방어 | Cold Start Problem, 레거시 혼재, Proxy SecOC |
| **Gateway** | 도메인 격리, 화이트리스트 라우팅, OBD-II 격리 | Rate Limiting, 프로토콜 변환 |
| **TEE** | TrustZone, Secure / Normal World, SMC Call | GPS 다중소스, OSNMA |
| **IDS** | 탐지 ≠ 방지, 규칙/주기/ML | 사양 기반 (DBC), 오탐률, SecOC 와 역할 구분 |
| **Tesla FSD** | CAN 무인증, GPS spoofing, 서버 vs 내부 보안 | SCS 아키텍처, $10–30/대 vs $118 M 매출 손실 |
| **Defense-in-Depth** | 다중 계층, 단일 layer 의존 금지, HSM = 신뢰 기반 | TARA, Secure Boot 매핑 |
| **V2X** | DSRC vs C-V2X, PKI / SCMS, 가명 인증서 | Sybil, Misbehavior Detection |
| **규제** | UN R155 (CSMS), ISO 21434, TARA | 자동차관리법 (한국), 형식 승인 연계 |
| **Key Fob** | Relay Attack, UWB (ToF), 신호 중계 | PIN to Drive, RSSI 한계, 피코초 분해능 |

#### 답변 구조 골든 템플릿

```
기술 질문 답변:

  1. [한 문장 핵심 답변] ← 결론 먼저
  2. [왜? 배경/원인] ← 설계 가정, 역사적 맥락
  3. [어떻게? 기술 메커니즘] ← 구체적 동작 (다이어그램 그리면 가산)
  4. [한계/트레이드오프] ← 완벽하지 않은 이유 (깊이 증명)
  5. [Secure Boot 연결] ← 기존 지식과 연결 (시야 증명)

  예시: "SecOC 란?"
  1. "CAN 메시지에 MAC 을 추가해 발신자를 인증하는 AUTOSAR 모듈."
  2. "CAN 은 1983 년 폐쇄 네트워크 가정으로 인증이 빠졌고..."
  3. "HSM 이 대칭키로 AES-CMAC 을 생성하고, Freshness Value 로..."
  4. "단, Cold Start 취약 구간과 레거시 ECU 혼재 문제가 있다."
  5. "Secure Boot 의 Chain of Trust 와 같은 원리 — 모든 노드 참여 필수."
```

### 5.11 규제 빠른 참조

| 규제 | 대상 | 핵심 | 위반 시 |
|---|---|---|---|
| UN R155 | 전 세계 신차 | CSMS (사이버보안 관리 시스템) | 형식 승인 불가 |
| UN R156 | 전 세계 신차 | SUMS (SW 업데이트 관리 시스템) | 형식 승인 불가 |
| ISO 21434 | 개발 프로세스 | TARA + 보안 엔지니어링 | 인증 불가 |
| 자동차관리법 (한국) | 차량 소유자 | SW 무단 변경 금지 | 2 년 징역 / 2 천만 원 |

---

## 6. 흔한 오해 와 이 카드를 봐야 할 때

### 흔한 오해 (cheat sheet 사용 시 자주 빠지는 함정)

!!! danger "❓ 오해 1 — 'cheat sheet 만 보면 면접 답변 끝'"
    **실제**: cheat sheet 는 _인덱스_ 일 뿐. 셀 하나에 _Module 01–04 의 어느 단원_ 이 매핑되는지 즉시 펼칠 수 있어야 의미가 있습니다. cheat sheet 를 _깊이 없이_ 외우면 답변이 표면적이라는 인상을 줍니다. <br>
    **왜 헷갈리는가**: 압축 자료가 _그대로_ 답변이 될 것이라는 기대.

!!! danger "❓ 오해 2 — '차량 보안 = 모든 차량이 동일'"
    **실제**: OEM 별로 (Tesla / Hyundai / BMW) 아키텍처 / 정책 / TARA 결과가 다릅니다. 한 OEM 의 모범 사례가 다른 OEM 에 그대로 적용 안 됨 — Module 03 의 Tesla 사례 표가 정확한 증거. <br>
    **왜 헷갈리는가**: "표준 = 동일 구현" 이라는 직관. 실제로는 R155 / 21434 가 _WHAT_ 만 정의, _HOW_ 는 OEM 자율.

!!! danger "❓ 오해 3 — '키워드 맵의 차별화 키워드만 외우면 가산점'"
    **실제**: 차별화 키워드를 _맥락 없이_ 던지면 오히려 _얕다_ 는 인상을 줍니다. 예: "OSNMA" 만 던지고 _그것이 왜 GPS spoofing 을 막는가_ 를 못 설명하면 감점. 차별화 키워드는 _맥락 + 한 줄 설명_ 과 함께만 의미가 있음. <br>
    **왜 헷갈리는가**: "차별화 = 더 어려운 단어" 라는 단순화.

!!! danger "❓ 오해 4 — 'Defense-in-Depth 는 _모든_ 것을 다 적용해야 한다'"
    **실제**: TARA 결과에 따라 _리스크 우선순위_ 가 다르고, 모든 layer 를 만점으로 채우는 것은 비현실적입니다. cheat sheet 의 6-layer 표는 _체크리스트_ 가 아니라 _사고 도구_ — 자기 시스템의 risk profile 에 맞춰 layer 를 선택. <br>
    **왜 헷갈리는가**: "다층 = 다 채워야" 라는 강박.

!!! danger "❓ 오해 5 — 'Tesla 사례를 비난조로 답변'"
    **실제**: 면접/리뷰에서 Tesla 를 _비난_ 하면 부정적 인상. Tesla 의 _아키텍처 결정 이유_ 를 추론하고 _더 나은 대안_ 을 제시하는 것이 프로 답변. <br>
    **왜 헷갈리는가**: "사고 사례 = 잘못된 회사" 의 단순화.

### 이 카드를 봐야 할 때

| 상황 | 카드의 어느 부분 |
|---|---|
| 면접 직전 1 분 review | §4.1 핵심 정리 한 줄 + §5.7 골든 룰 8 |
| Tesla 사례 묻는 질문 | §3 Secure Boot 매핑 + §5.4 Root Cause |
| "당신 시스템에서 X 공격은?" 질문 | §4.2 공격/방어 매트릭스 |
| TARA workshop 직전 | §5.10 키워드 맵 + Module 04 §3 |
| ECU 인수 회의 | Module 04 §6 의 8 가지 자가진단 + §5.5 6-Layer |
| 레퍼런스 / 스펙 문서 작성 | §5.2~5.3 비교표 + §5.11 규제 |

---

## 7. 핵심 정리 (Key Takeaways)

- **CAN 자체는 무인증** — 외부 접근 (OBD-II) 시 모든 메시지 위조 가능.
- **SecOC + HSM + Gateway + IDS = 4-layer 표준 스택** — 한 layer 만으로는 부족.
- **Tesla 사례 = 외부만 방어하고 내부는 신뢰한 결과** — L1, L5 강함, L2, L3 비어 있음.
- **표준 = R155 / R156 / 21434** — CSMS / SUMS / TARA 가 핵심 키워드.
- **답변은 5 step** — 핵심 → 왜 → 어떻게 → 한계 → Secure Boot 연결.

!!! warning "실무 주의점 — OTA 검증 단계 누락 시 fleet 전체 위험"
    **현상**: OTA 업데이트 패키지에 서명 검증만 적용하고 버전 다운그레이드 방지 (Anti-Rollback) 를 빠뜨리면, 공격자가 구 취약 버전 서명 패키지를 재배포해 fleet 전체를 취약 상태로 되돌릴 수 있다.

    **원인**: 서명 검증 (무결성) 과 버전 단조성 (Monotonic Counter) 검증은 별도 구현 항목이라 후자가 빠지는 경우가 빈번하다.

    **점검 포인트**: HSM 내 Monotonic Counter 값이 업데이트 후 증가하는지, 그리고 이전 버전 패키지를 재주입했을 때 ECU 가 거부 (NACK) 하는지 벤치 테스트로 확인. R156 (SUMS) 요구 항목의 "Rollback Prevention" 체크박스가 TARA 에 포함되어 있는지 검토.

### 7.1 자가 점검

!!! question "🤔 Q1 — 4-layer 스택 적용 (Bloom: Apply)"
    "OBD-II 포트로 진단 메시지 위조 가능". 4-layer 중 어느 layer 가 빠진 결과?
    ??? success "정답"
        L1 (SecOC) 부재:
        - **SecOC**: CAN message 에 MAC + Freshness Value 추가 → 위조 메시지는 MAC 검증 실패로 drop.
        - **HSM 만**: ECU 내 키 보호는 되지만 메시지 wire 단계는 무방비.
        - **Gateway 만**: domain 간 차단은 되지만 같은 domain 내 위조는 통과.
        - 결론: OBD-II → CAN → critical ECU 의 message wire 자체가 SecOC 로 보호되어야.

!!! question "🤔 Q2 — Tesla 사례 평가 (Bloom: Evaluate)"
    Tesla 가 외부 (L1, L5) 만 강하고 내부 (L2, L3) 가 약한 _구조적 이유_?
    ??? success "정답"
        Internet-first 보안관:
        - **외부 우선의 이유**: 원격 attack surface (Wi-Fi/Cellular) 가 가장 명확 → 미디어/규제 압박.
        - **내부 약한 이유**: 한 차에 ECU 50–100 개. 모두 SecOC 적용 = HW HSM 비용 폭증.
        - **사고 사례**: Pwn2Own 2023 — 외부 Wi-Fi 침투 후 _내부 CAN_ 으로 lateral → infotainment → autopilot 의 일부 노출.
        - 정답: defense in depth. 외부 _도_ 강함 + 내부 _도_ 강함이 21434 표준의 의도.

### 7.2 출처

**Internal (Confluence)**
- `Automotive Threat Model` — 4-layer 매핑
- `OTA Update Security` — Rollback Prevention 사례

**External**
- ISO/SAE 21434 *Road vehicles — Cybersecurity engineering*
- UN R155 (CSMS) / R156 (SUMS)
- AUTOSAR *Specification of Secure Onboard Communication (SecOC)*

---

## 다음 단계

- 퀴즈로 마무리: [전체 Quiz Index](../quiz/) — 5 개 모듈 각 5 문항씩, 총 25 문항.
- 심화: 회사 내 ECU 한 종류를 골라 본 cheat sheet 의 모든 키워드를 매핑해 보는 표를 작성한다.
- 추가 자료: ISO/SAE 21434, UN R155 / R156, AUTOSAR SecOC, NHTSA Cybersecurity Best Practices.

<div class="chapter-nav">
  <a class="nav-prev" href="../04_attack_surface_and_defense/">
    <div class="nav-label">◀ 이전</div>
    <div class="nav-title">Attack Surface & Defense (공격 표면과 방어 계층)</div>
  </a>
  <a class="nav-next" href="../quiz/">
    <div class="nav-label">다음 ▶</div>
    <div class="nav-title">퀴즈로 이동</div>
  </a>
</div>


--8<-- "abbreviations.md"
