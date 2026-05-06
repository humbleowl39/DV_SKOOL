# Automotive Cybersecurity 용어집

이 페이지는 **Automotive Cybersecurity** 코스의 핵심 용어 모음입니다. 각 항목은 ISO 11179 형식(Definition / Source / Related / Example / See also)을 따릅니다.

!!! tip "검색 활용"
    상단 검색창에 용어를 입력하면 본문에서의 사용처도 함께 찾을 수 있습니다.

---

## A

### AUTOSAR
- **Definition.** 차량 ECU 소프트웨어 아키텍처 표준으로, Classic Platform(MCU 기반 실시간)과 Adaptive Platform(POSIX 기반 고성능) 두 갈래의 사양을 정의한다.
- **Source.** AUTOSAR Consortium specification.
- **Related.** Classic Platform, Adaptive Platform, SecOC, BSW.
- **Example.** Classic AUTOSAR 의 SecOC 모듈은 CAN 메시지에 MAC 을 부착하여 인증한다.
- **See also.** [Module 02 — Automotive SoC Security](02_automotive_soc_security.md).

---

## C

### CAN (Controller Area Network)
- **Definition.** 차량 ECU 간 통신을 위해 설계된 멀티마스터 직렬 브로드캐스트 버스로, 11/29-bit ID 기반 비파괴적 우선순위 중재(arbitration) 방식을 사용한다.
- **Source.** ISO 11898-1.
- **Related.** Arbitration, OBD-II, CAN-FD.
- **Example.** ID 0x100 메시지가 ID 0x200 보다 우선하여 버스 점유.
- **See also.** [Module 01 — CAN Bus Fundamentals](01_can_bus_fundamentals.md).

### CAN-FD
- **Definition.** CAN 의 확장 프로토콜로, 데이터 페이로드를 최대 64바이트로 늘리고 데이터 phase 의 비트레이트를 더 높게 설정할 수 있게 한 것.
- **Source.** ISO 11898-1:2015.
- **Related.** CAN, SecOC, MAC truncation.
- **Example.** 64바이트 payload 덕에 16바이트 MAC 을 동봉할 여유가 생긴다.
- **See also.** [Module 01](01_can_bus_fundamentals.md), [Module 02](02_automotive_soc_security.md).

### CSMS (Cyber Security Management System)
- **Definition.** UN R155 가 OEM 에 요구하는 조직 차원의 사이버보안 관리 체계로, 위험 식별·통제·모니터링·사고 대응의 라이프사이클을 정의한다.
- **Source.** UN ECE R155.
- **Related.** SUMS, TARA, ISO/SAE 21434.
- **Example.** OEM 은 CSMS 인증을 받아야 신차 형식 승인을 받을 수 있다.
- **See also.** [Module 04](04_attack_surface_and_defense.md).

---

## D

### Defense in Depth
- **Definition.** 단일 보안 통제에 의존하지 않고 여러 독립적 계층(물리·통신·OS·앱·클라우드) 의 통제가 직렬로 작용하도록 설계하는 보안 원칙.
- **Source.** Common security architecture principle.
- **Related.** Layered Security, Threat Modeling.
- **Example.** Secure Boot(L1) → SecOC(L2) → Gateway(L3) → IDS(L4) 의 4계층 스택.
- **See also.** [Module 04](04_attack_surface_and_defense.md).

---

## F

### Freshness Value
- **Definition.** SecOC 메시지에 포함되는 단조 증가 카운터/타임스탬프로, 동일한 메시지의 재전송(replay) 을 수신측이 거부할 수 있게 해 주는 값.
- **Source.** AUTOSAR SecOC specification.
- **Related.** SecOC, MAC, Replay Attack.
- **Example.** 카운터가 이전 값보다 작거나 같은 메시지는 폐기.
- **See also.** [Module 02](02_automotive_soc_security.md).

---

## H

### HSM (Hardware Security Module)
- **Definition.** 키 생성·저장·암호 연산을 위해 메인 CPU 와 격리된 보안 코프로세서로, 키가 평문 상태로 외부에 노출되지 않도록 하드웨어로 보호한다.
- **Source.** EVITA / SHE specifications.
- **Related.** Root of Trust, Secure Boot, SecOC.
- **Example.** SecOC MAC 연산은 HSM 내부에서 수행되어 세션 키가 외부로 나가지 않는다.
- **See also.** [Module 02](02_automotive_soc_security.md).

---

## I

### IDS (Intrusion Detection System) — Automotive
- **Definition.** 차량 네트워크의 트래픽 패턴을 모니터링하여 시그니처 또는 ML 모델로 비정상 메시지를 탐지하는 시스템.
- **Source.** Common automotive security architecture.
- **Related.** SecOC, Gateway, V-SOC.
- **Example.** 정상 주기 100ms 인 메시지가 갑자기 1ms 주기로 발생 → 이상 탐지.
- **See also.** [Module 02](02_automotive_soc_security.md), [Module 04](04_attack_surface_and_defense.md).

### ISO/SAE 21434
- **Definition.** 차량 사이버보안 엔지니어링 라이프사이클을 정의하는 국제 표준으로, TARA(Threat Analysis & Risk Assessment) 를 핵심 활동으로 요구한다.
- **Source.** ISO/SAE 21434:2021.
- **Related.** TARA, UN R155, CSMS.
- **Example.** 콘셉트 단계 TARA → 개발 단계 보안 요구사항 → 검증 단계 침투 테스트.
- **See also.** [Module 04](04_attack_surface_and_defense.md).

---

## M

### MAC (Message Authentication Code)
- **Definition.** 메시지의 무결성과 발신자 인증을 동시에 보장하기 위해 공유 키와 메시지로부터 계산되는 짧은 고정 길이의 검증값.
- **Source.** Common cryptography (HMAC, CMAC 등).
- **Related.** SecOC, Freshness Value, HMAC, AES-CMAC.
- **Example.** SecOC 는 truncated CMAC 24~64bit 를 CAN 메시지에 첨부.
- **See also.** [Module 02](02_automotive_soc_security.md).

---

## O

### OBD-II
- **Definition.** 1996 년 미국에서 의무화된 차량 진단 표준 커넥터/프로토콜로, 차량 내부 CAN 버스에 직접 접근할 수 있는 외부 포트를 제공한다.
- **Source.** SAE J1962, ISO 15765.
- **Related.** CAN, Diagnostic, Attack Surface.
- **Example.** OBD-II 동글을 통해 외부 공격자가 CAN 메시지를 주입.
- **See also.** [Module 01](01_can_bus_fundamentals.md), [Module 04](04_attack_surface_and_defense.md).

---

## R

### Replay Attack
- **Definition.** 정상적으로 발생했던 인증된 메시지를 캡처하여 후일 재전송함으로써 시스템을 잘못된 상태로 유도하는 공격.
- **Source.** Common security taxonomy.
- **Related.** Freshness Value, MAC, SecOC.
- **Example.** "도어 잠금 해제" 메시지를 녹음 후 재전송하여 차량을 다시 연다.
- **See also.** [Module 02](02_automotive_soc_security.md).

### Root of Trust (RoT)
- **Definition.** 시스템 보안의 모든 신뢰 사슬이 시작되는 변경 불가능한 하드웨어 구성요소로, 일반적으로 ROM 코드 + HSM 의 봉인된 키로 구현된다.
- **Source.** TCG Root of Trust definitions.
- **Related.** Secure Boot, HSM, Attestation.
- **Example.** OTP 에 봉인된 OEM 공개키 해시가 부팅 검증의 시작점.
- **See also.** [Module 02](02_automotive_soc_security.md).

---

## S

### Secure Boot
- **Definition.** 부팅 시 각 단계의 펌웨어/이미지를 다음 단계가 시작되기 전에 디지털 서명으로 검증하여, 변조된 코드가 실행되지 않도록 보장하는 메커니즘.
- **Source.** TCG / EVITA / NIST SP 800-193.
- **Related.** Root of Trust, HSM, Chain of Trust.
- **Example.** ROM → BL1 → BL2 → BL3 단계마다 서명 검증, 실패 시 boot halt.
- **See also.** [Module 02](02_automotive_soc_security.md).

### Secure Gateway
- **Definition.** 차량 내부의 도메인(Powertrain/Chassis/Body/Infotainment) 사이에서 메시지 라우팅, 화이트리스트 필터링, 레이트 리미팅을 수행하는 중앙 ECU.
- **Source.** Common automotive E/E architecture.
- **Related.** Domain Isolation, IDS, OBD-II Gateway.
- **Example.** Infotainment 도메인에서 Powertrain 도메인으로의 비허용 메시지를 drop.
- **See also.** [Module 02](02_automotive_soc_security.md).

### SecOC (Secure Onboard Communication)
- **Definition.** AUTOSAR 가 정의한 차량 내부 통신 보안 모듈로, 메시지에 truncated MAC 과 Freshness Value 를 부착하여 인증과 replay 방어를 제공한다.
- **Source.** AUTOSAR SecOC specification.
- **Related.** MAC, Freshness Value, HSM.
- **Example.** 16바이트 payload 중 4바이트를 truncated MAC 으로 사용.
- **See also.** [Module 02](02_automotive_soc_security.md).

### SUMS (Software Update Management System)
- **Definition.** UN R156 이 요구하는 차량 소프트웨어 업데이트 라이프사이클 관리 체계로, OTA 패키지의 무결성·롤백·차량별 적합성을 관리한다.
- **Source.** UN ECE R156.
- **Related.** OTA, CSMS, Code Signing.
- **Example.** 업데이트 패키지가 차량 VIN 기반 정책에 맞을 때만 적용.
- **See also.** [Module 04](04_attack_surface_and_defense.md).

### Sybil Attack
- **Definition.** 한 공격자가 다수의 가짜 신원(노드) 을 만들어 다대다 시스템(예: V2X) 의 신뢰 모델을 왜곡하는 공격.
- **Source.** Common distributed systems security taxonomy.
- **Related.** V2X, Pseudonym Certificate, Misbehavior Detection.
- **Example.** 한 차량이 20개의 가짜 차량으로 위장하여 가짜 정체 정보 broadcast.
- **See also.** [Module 04](04_attack_surface_and_defense.md).

---

## T

### TARA (Threat Analysis & Risk Assessment)
- **Definition.** ISO/SAE 21434 가 요구하는 활동으로, 자산 식별 → 위협 시나리오 → 영향/실현가능성 평가 → 위험 등급 산정 → 처리 방안 결정의 절차.
- **Source.** ISO/SAE 21434:2021.
- **Related.** STRIDE, Attack Tree, Threat Modeling.
- **Example.** "OBD-II 포트를 통한 CAN 메시지 주입" 위협에 대해 영향=High/실현가능성=Medium → Risk=Medium.
- **See also.** [Module 04](04_attack_surface_and_defense.md).

---

## U

### UN R155 / R156
- **Definition.** UNECE 가 정의한 차량 사이버보안(R155) 및 SW 업데이트(R156) 형식 승인 규제로, 2024 년부터 신차 출시에 사실상 필수 요건이 된다.
- **Source.** UNECE WP.29.
- **Related.** CSMS, SUMS, ISO/SAE 21434.
- **Example.** R155 인증 없이는 EU 시장 신차 등록 불가.
- **See also.** [Module 04](04_attack_surface_and_defense.md).

---

## V

### V2X (Vehicle-to-Everything)
- **Definition.** 차량과 다른 차량(V2V), 인프라(V2I), 보행자(V2P), 네트워크(V2N) 간의 무선 통신을 통칭하는 용어로, DSRC 또는 C-V2X 기술을 사용한다.
- **Source.** SAE J2945, ETSI ITS-G5.
- **Related.** SCMS, Pseudonym Certificate, Misbehavior Detection.
- **Example.** 교차로 진입 차량이 BSM 으로 주변에 위치/속도 broadcast.
- **See also.** [Module 04](04_attack_surface_and_defense.md).
