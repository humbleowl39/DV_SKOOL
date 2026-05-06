# Automotive Cybersecurity — 개요 및 컨셉 맵

## 학습 플랜
- **레벨**: Intermediate → Advanced (SoC Secure Boot / ARM Security 지식 기반, 차량 보안으로 확장)
- **목표**: 차량 내부 통신(CAN Bus)의 보안 한계와 SoC 레벨 방어 아키텍처를 화이트보드에 그리며, Tesla FSD 탈옥 사례를 공격/방어 관점에서 논리적으로 설명할 수 있는 수준

## 사전 지식 / 선수 학습

| 주제 | 필수/권장 | 참고 자료 |
|------|----------|----------|
| **SoC Secure Boot** | 필수 | `soc_secure_boot_ko/` — HW RoT, Chain of Trust, 서명 검증 |
| **ARM Security (TrustZone)** | 필수 | `arm_security_ko/` — EL, Secure/Non-Secure World, TEE |
| AMBA 버스 기초 | 권장 | `amba_protocols_ko/` — AXI/APB 트랜잭션 (Gateway SoC 이해에 필요) |
| 암호학 기초 | 권장 | `soc_secure_boot_ko/03_crypto_in_boot.md` — HMAC, 대칭키, PKI |

## 핵심 용어집 (Glossary)

학습 전 반드시 알아야 할 용어. 각 유닛에서 반복적으로 등장한다.

### 차량 구성 요소

| 약어 | 풀네임 | 설명 |
|------|--------|------|
| **ECU** | Electronic Control Unit | 차량의 전자 제어 장치. 엔진, 브레이크, 에어백 등 각 기능마다 별도 ECU가 존재. 현대 차량에는 70~100개 이상 탑재 |
| **MCU** | Microcontroller Unit | ECU의 핵심 칩. 임베디드 프로세서 + 메모리 + 주변장치가 하나의 칩에 통합 |
| **SoC** | System on Chip | MCU보다 고성능. CPU + GPU + NPU + 메모리 컨트롤러 등을 단일 칩에 집적. Tesla FSD 칩이 대표적 예 |
| **TCU** | Telematics Control Unit | 차량의 "인터넷 관문". 셀룰러(LTE/5G), WiFi, GPS 모듈을 포함하여 외부와 통신 |
| **ADAS** | Advanced Driver Assistance Systems | 첨단 운전자 보조 시스템. 자동 긴급 제동, 차선 유지, 적응형 크루즈 컨트롤 등 |
| **FSD** | Full Self-Driving | Tesla의 완전 자율주행 소프트웨어. 구독($99/월) 또는 일시불($8,000+) 모델 |
| **HSM** | Hardware Security Module | ECU/SoC 내부의 격리된 보안 코어. 암호키 저장 + 암호 연산 전담. Application Core에서 키에 직접 접근 불가 |
| **RSU** | Road Side Unit | 도로변에 설치된 V2X 통신 기지국. 교통 신호, 도로 상태 정보를 차량에 브로드캐스트 |
| **IMU** | Inertial Measurement Unit | 관성 측정 장치. 가속도계 + 자이로스코프로 차량의 움직임(가속, 회전)을 측정 |

### 통신 프로토콜 / 인터페이스

| 약어 | 풀네임 | 설명 |
|------|--------|------|
| **CAN** | Controller Area Network | 1983년 Bosch가 개발한 차량 내부 직렬 버스. 브로드캐스트 방식, 인증/암호화 없음 |
| **CAN-FD** | CAN with Flexible Data-rate | CAN 확장. payload 8B→64B, 속도 8Mbps. 보안은 여전히 없음 |
| **CAN-XL** | CAN Extra Long | 차세대 CAN. payload 2048B, 20Mbps, **CANsec** 보안 내장 |
| **OBD-II** | On-Board Diagnostics II | 법적 의무 장착(1996~ 미국)된 차량 진단 포트. 16핀 커넥터로 CAN Bus에 직접 연결 가능 |
| **V2X** | Vehicle-to-Everything | 차량 대 모든 것 통신. V2V(차량간), V2I(인프라), V2P(보행자), V2N(네트워크) 포함 |
| **DSRC** | Dedicated Short Range Communications | WiFi 기반 V2X 통신 (802.11p, 5.9GHz). 저지연(~2ms) |
| **C-V2X** | Cellular V2X | 셀룰러(LTE/5G) 기반 V2X. 3GPP 표준. 넓은 커버리지 |
| **AUTOSAR** | AUTomotive Open System ARchitecture | 차량 소프트웨어 표준 아키텍처. ECU 소프트웨어의 계층 구조와 인터페이스를 정의 |
| **OTA** | Over-The-Air | 무선 원격 소프트웨어 업데이트. 정비소 방문 없이 차량 FW 갱신 |

### 보안 기술 / 모듈

| 약어 | 풀네임 | 설명 |
|------|--------|------|
| **SecOC** | Secure Onboard Communication | AUTOSAR가 정의한 CAN 메시지 인증 모듈. MAC + Freshness Value로 발신자 인증 |
| **TEE** | Trusted Execution Environment | 신뢰 가능한 격리 실행 환경. ARM TrustZone의 Secure World가 대표적 구현 |
| **IDS** | Intrusion Detection System | 침입 탐지 시스템. CAN 트래픽 이상을 탐지하지만 차단(prevention)은 하지 않음 |
| **SHE** | Secure Hardware Extension | 자동차용 기본 HSM 표준. AES-128-CMAC, 11개 키 슬롯 |
| **EVITA** | E-safety Vehicle Intrusion Protected Applications | 고급 자동차 HSM 표준. Medium/Full 등급, RSA/ECC/AES 지원 |
| **SCS** | Security Subsystem | Tesla FSD 칩의 보안 서브시스템. Secure Boot + Cloud Auth 담당 |
| **PKI** | Public Key Infrastructure | 공개키 기반 인프라. 인증서 발급/검증/폐기 체계 |
| **SCMS** | Security Credential Management System | V2X 전용 PKI. 가명 인증서로 프라이버시 보호 |

### 암호학 기본 용어

| 약어 | 풀네임 | 설명 |
|------|--------|------|
| **MAC** | Message Authentication Code | 메시지 인증 코드. 비밀키로 생성하는 태그 — 위조 감지용 (암호화와 다름!) |
| **AES** | Advanced Encryption Standard | 대칭키 암호 알고리즘. 128/256비트 키. 현대 차량 보안의 핵심 |
| **CMAC** | Cipher-based MAC | AES 기반 MAC 생성 방식. SecOC에서 CAN 메시지 인증에 사용 |
| **GCM** | Galois/Counter Mode | AES 암호화 + 인증을 동시에 수행하는 모드. CANsec/MACsec에서 사용 |
| **RSA/ECC** | — / Elliptic Curve Cryptography | 비대칭키 알고리즘. RSA(큰 키, 호환성), ECC(작은 키, 효율) |

### 규제 / 표준

| 약어 | 풀네임 | 설명 |
|------|--------|------|
| **UN R155** | UN Regulation No. 155 | 차량 사이버보안 관리 시스템(CSMS) 의무화. 2024~ 신차 적용 |
| **UN R156** | UN Regulation No. 156 | 소프트웨어 업데이트 관리 시스템(SUMS) 의무화 |
| **ISO 21434** | ISO/SAE 21434 | 차량 사이버보안 엔지니어링 국제 표준. TARA(위협 분석) 프레임워크 포함 |
| **TARA** | Threat Analysis and Risk Assessment | ISO 21434 요구 위협 분석 방법론. 자산→위협→영향→공격 가능성→위험도 평가 |

### 공격 기법 약어

| 약어 | 풀네임 | 설명 |
|------|--------|------|
| **DoS** | Denial of Service | 서비스 거부 공격. CAN에서는 대량 프레임 전송으로 통신 마비 |
| **MITM** | Man-in-the-Middle | 중간자 공격. 통신 중간에서 메시지를 가로채거나 변조 |
| **FI** | Fault Injection | 물리적 오류 주입. 전압/클럭 글리치로 CPU의 보안 검증 우회 |
| **SCA** | Side-Channel Attack | 부채널 공격. 전력 소모, 전자기 방출, 타이밍 차이에서 비밀 정보 추출 |
| **SDR** | Software-Defined Radio | 소프트웨어 정의 라디오. GPS spoofing 등에 사용되는 범용 무선 장비 |

### 기타 핵심 개념

| 용어 | 설명 |
|------|------|
| **Freshness Value** | Replay(재전송) 공격 방어용 일회성 값. 카운터 또는 타임스탬프. SecOC의 핵심 구성 요소 |
| **Arbitration** | CAN 버스에서 동시 전송 시 우선순위 결정 과정. ID가 낮을수록 우선. Dominant(0) > Recessive(1) |
| **Defense in Depth** | 다중 계층 방어 전략. 단일 레이어 돌파 시에도 다음 레이어가 방어 |
| **VIN** | Vehicle Identification Number. 차량 고유 식별 번호 (17자리) |
| **Geofence** | GPS 좌표 기반 가상 지리적 경계. Tesla FSD는 이를 통해 승인 지역만 허용 |
| **Feature Flag** | 소프트웨어 기능의 활성화/비활성화 스위치. Tesla FSD 탈옥의 공격 대상 |

---

## 컨셉 맵

```
+================================================================+
|              Automotive Cybersecurity                           |
|                                                                |
|  +---------------------------+  +---------------------------+  |
|  |   In-Vehicle Network      |  |   SoC Security            |  |
|  |                           |  |                           |  |
|  |  CAN Bus (1980s, 무인증)  |  |  HSM (키 저장 + MAC)      |  |
|  |  CAN-FD (더 큰 payload)   |  |  SecOC (메시지 인증)      |  |
|  |  CAN-XL (CANsec 내장)     |  |  Secure Gateway (격리)    |  |
|  |  Automotive Ethernet      |  |  TEE (TrustZone)         |  |
|  +------------+--------------+  +------------+--------------+  |
|               |                              |                 |
|               +-------------+----------------+                 |
|                             |                                  |
|               +-------------v--------------+                   |
|               |    Attack & Defense         |                  |
|               |                            |                  |
|               |  CAN Injection / Spoofing  |                  |
|               |  GPS Spoofing              |                  |
|               |  Fault Injection           |                  |
|               |  Replay Attack             |                  |
|               |  IDS / Firewall / OTA      |                  |
|               +-------------+--------------+                   |
|                             |                                  |
|               +-------------v--------------+                   |
|               |    Case Study              |                   |
|               |    Tesla FSD Jailbreak     |                   |
|               |    (2025-2026)             |                   |
|               +----------------------------+                   |
+================================================================+
```

## 학습 단위 (Units)

| # | 단위 | 핵심 질문 |
|---|------|----------|
| 1 | **CAN Bus Fundamentals** | 차량 내부 통신은 어떻게 동작하고, 왜 구조적으로 취약한가? |
| 2 | **Automotive SoC Security** | SoC 레벨에서 CAN 통신을 어떻게 보호하는가? (HSM, SecOC, Gateway) |
| 3 | **Tesla FSD Case Study** | FSD 탈옥은 어떤 취약점을 악용했고, 어떤 방어가 빠졌는가? |
| 4 | **Attack Surface & Defense** | 차량 보안의 전체 공격 표면과 방어 계층은 무엇인가? |
| 5 | **Quick Reference Card** | 면접 직전 빠른 복습용 요약 카드 |

## 학습 의존성 흐름

```
Unit 1 (CAN Bus) ─────────────────────────────┐
  "차량 내부 통신의 구조와 한계"                  │
     │                                          │
     v                                          │
Unit 2 (SoC Security) ───┐                     │
  "SoC가 제공하는 방어 수단"│                     │
     │                    │                     │
     v                    v                     v
Unit 3 (Tesla Case)   Unit 4 (Attack/Defense)
  "실제 사례 분석"       "체계적 공격/방어 분류"
     │                    │
     +────────────────────+
                │
                v
         Unit 5 (Quick Reference)
           "면접/복습 요약"
```

## Secure Boot / ARM Security와의 연결

```
[soc_secure_boot_ko]          [arm_security_ko]
  HW RoT, Chain of Trust        TrustZone, TEE
  서명 검증, Anti-Rollback       EL3/S-EL1 격리
        \                        /
         \                      /
          +-----> [이 모듈] <---+
                  Automotive에서의 적용:
                  - HSM = HW RoT의 차량 버전
                  - SecOC = Chain of Trust의 메시지 버전
                  - Secure Gateway = TrustZone의 버스 버전
```
