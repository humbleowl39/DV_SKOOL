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
  <a class="page-toc-link" href="#학습-목표">학습 목표</a>
  <a class="page-toc-link" href="#선수-지식">선수 지식</a>
  <a class="page-toc-link" href="#왜-이-모듈이-중요한가">왜 이 모듈이 중요한가</a>
  <a class="page-toc-link" href="#can-bus-한줄-요약">CAN Bus 한줄 요약</a>
  <a class="page-toc-link" href="#핵심-정리">핵심 정리</a>
  <a class="page-toc-link" href="#프로토콜-비교표">프로토콜 비교표</a>
  <a class="page-toc-link" href="#공격방어-매트릭스">공격/방어 매트릭스</a>
  <a class="page-toc-link" href="#soc-보안-모듈-비교">SoC 보안 모듈 비교</a>
  <a class="page-toc-link" href="#tesla-fsd-탈옥-root-cause-한줄-정리">Tesla FSD 탈옥 — Root Cause 한줄 정리</a>
  <a class="page-toc-link" href="#defense-in-depth-6개-레이어">Defense in Depth — 6개 레이어</a>
  <a class="page-toc-link" href="#secure-boot와의-개념-대응">Secure Boot와의 개념 대응</a>
  <a class="page-toc-link" href="#면접-골든-룰">면접 골든 룰</a>
  <a class="page-toc-link" href="#흔한-실수와-올바른-답변">흔한 실수와 올바른 답변</a>
  <a class="page-toc-link" href="#차량-보안-역사-타임라인">차량 보안 역사 타임라인</a>
  <a class="page-toc-link" href="#면접-핵심-키워드-맵">면접 핵심 키워드 맵</a>
  <a class="page-toc-link" href="#규제-빠른-참조">규제 빠른 참조</a>
  <a class="page-toc-link" href="#핵심-정리">핵심 정리</a>
  <a class="page-toc-link" href="#다음-단계">다음 단계</a>
</div>
<!-- DV-SKOOL-CH-TOC:end -->

## 학습 목표

이 모듈을 마치면:

1. (Remember) CAN/SecOC/HSM/Gateway/IDS/V2X 의 핵심 한 줄 정의를 즉시 떠올릴 수 있다.
2. (Apply) 면접/리뷰에서 차량 보안 토픽이 나왔을 때 30초 안에 구조화해 답할 수 있다.
3. (Evaluate) 자기 시스템에 빠진 보안 계층이 무엇인지 cheat sheet 와 비교해 판별할 수 있다.

## 선수 지식

- Module 01 ~ 04 완료 — 이 모듈은 새 내용을 가르치지 않고 압축한다.

## 왜 이 모듈이 중요한가

복습 + 인터뷰/리뷰 직전 즉시 꺼내볼 수 있는 1-page cheat sheet 가 필요하다. 이 모듈은 학습한 내용을 **머릿속 인덱스**로 굳히는 역할을 한다.

---

## CAN Bus 한줄 요약
```
CAN(1983) = 브로드캐스트 버스, 무인증/무암호화 → OBD-II로 외부 접근 시 전체 위조 가능
```

---

!!! tip "💡 이해를 위한 비유"
    **Automotive Security 마스터 = 4-layer + 3-surface 의 매트릭스 인지** ≈ **차량 보안 아키텍트 — 모든 vector x layer 매핑 즉시 답변**

    OBD/무선/공급망 × HSM/SecOC/Gateway/IDS 의 4×3 매트릭스에서 각 cell 의 동작과 trade-off 를 즉시 그리는 것이 마스터.

---

!!! danger "❓ 흔한 오해"
    **오해**: 차량 보안 = 모든 차량이 동일

    **실제**: OEM 별로 (Tesla, Hyundai, BMW) 아키텍처 / 정책 / TARA 결과가 다름. 한 OEM 의 모범 사례가 다른 OEM 에 그대로 적용 안 됨.

    **왜 헷갈리는가**: "표준 = 동일 구현" 이라는 직관. 실제로는 R155 / 21434 이 "WHAT" 만 정의, "HOW" 는 OEM 자율.

## 핵심 정리

| 주제 | 핵심 포인트 |
|------|------------|
| CAN 구조적 결함 | 무인증, 무암호화, 브로드캐스트, 무상태 — 1980년대 폐쇄 네트워크 가정 |
| CAN-FD vs CAN-XL | FD=큰 payload(64B)/보안 없음, XL=CANsec 내장(AES-GCM) |
| HSM | ECU 내 격리된 보안 코어 — 키 저장 + MAC 연산, API만 노출 |
| SecOC | AUTOSAR CAN 메시지 인증 — Data + Truncated MAC(4~8B) + Freshness |
| Secure Gateway | 도메인 격리 + 메시지 라우팅/필터 + OBD-II 격리 |
| TEE (TrustZone) | Secure World에서 GPS 무결성/키 관리 — Normal World CAN 위조 차단 |
| IDS | 규칙/주기/ML 기반 CAN 이상 탐지 — 방지가 아닌 탐지 |
| Tesla FSD 탈옥 | CAN injection(GPS spoofing) + Region Code 변조 — SecOC 부재가 원인 |
| 규제 | UN R155(CSMS), ISO 21434, 자동차관리법(2년 징역/2천만 원 벌금) |

---

## 프로토콜 비교표

| | CAN 2.0 | CAN-FD | CAN-XL | Auto Ethernet |
|--|---------|--------|--------|---------------|
| 속도 | 1Mbps | 8Mbps | 20Mbps | 100M~10Gbps |
| Payload | 8B | 64B | 2048B | MTU 1500B+ |
| 보안 내장 | ❌ | ❌ | ✅ CANsec | ✅ MACsec |
| SecOC 가능 | △ (공간부족) | ✅ | 불필요 (내장) | 불필요 |
| 용도 | 레거시 ECU | 고속 ECU | 차세대 | ADAS/카메라 |

---

## 공격/방어 매트릭스

| 공격 | 진입점 | 방어 수단 | 레이어 |
|------|--------|----------|--------|
| CAN Injection | OBD-II | SecOC + Gateway 격리 | L0+L2 |
| CAN Replay | OBD-II | Freshness Value (카운터/타임스탬프) | L2 |
| CAN DoS/Bus-Off | OBD-II | Rate Limiting + IDS | L3 |
| GPS Spoofing (CAN) | OBD-II | TEE 내 다중소스 검증 | L1+L2 |
| GPS Spoofing (RF) | 무선 | Authenticated GNSS (Galileo OSNMA) | L1 |
| Cellular Exploit | TCU | 방화벽 + Gateway 격리 | L0+L3 |
| FW Extraction | JTAG | Secure Debug + eFuse 비활성화 | L1 |
| Fault Injection | 칩 물리 | Anti-Tamper + 이중 검증 + 센서 | L1 |
| OTA Hijack | 서버 | 코드 서명 + VIN 바인딩 + Anti-Rollback | L5 |
| Supply Chain | 공급망 | Secure Boot + FW 서명 | L1+L5 |

---

## SoC 보안 모듈 비교

| | SHE | EVITA Medium | EVITA Full | Tesla SCS |
|--|-----|-------------|-----------|-----------|
| 대칭키 | AES-128 | AES-128/256 | AES-128/256 | AES |
| 비대칭키 | ❌ | ❌ | RSA, ECC | RSA, ECC |
| 키 슬롯 | 11 | 수십 | 수백 | 가변 |
| 용도 | 기본 CAN 인증 | ECU 보안 | 게이트웨이/ADAS | Boot + Cloud |
| CAN SecOC | ✅ | ✅ | ✅ | ❌ 미적용 |

---

## Tesla FSD 탈옥 — Root Cause 한줄 정리

```
SoC에 보안 HW(SCS)가 있었지만 CAN 통신 인증에 미적용
→ OBD-II 동글이 GPS/Region 위조 CAN 프레임 주입
→ FSD SoC가 위조 프레임을 정상으로 수용
→ 비승인 지역에서 FSD 동작

대응: SecOC(차단) + Gateway(격리) + IDS(탐지) = 원천 방어 가능
```

---

## Defense in Depth — 6개 레이어

```
L5: Cloud/OTA — 서명, VIN 바인딩, 텔레메트리, 원격 비활성화
L4: Application — Secure Coding, Input Validation, Fuzzing
L3: Network — IDS/IPS, Firewall, Rate Limiting, Anomaly Detection
L2: Communication — SecOC(CAN), MACsec(Eth), TLS, CANsec(XL)
L1: Platform — Secure Boot, HSM, TEE, Anti-Tamper, Secure Debug
L0: Physical — OBD 격리, 포트 비활성화, 물리 접근 제어
```

---

## Secure Boot와의 개념 대응

| Secure Boot 개념 | Automotive Security 대응 | 공통 원리 |
|-----------------|------------------------|----------|
| HW RoT (BootROM + OTP) | HSM (Isolated Core + Key Store) | 변경 불가한 신뢰 기반 |
| Chain of Trust (BL1→BL2→BL3) | SecOC 인증 체인 (모든 ECU 참여) | 한 단계 깨지면 전체 무효 |
| 서명 검증 (RSA/ECDSA) | MAC 검증 (AES-CMAC) | 위조 불가한 인증 |
| Anti-Rollback (OTP Counter) | Freshness Value (Replay 방어) | 재사용 공격 방지 |
| Secure Debug (JTAG Lock) | OBD-II Gateway (진단 격리) | 디버그 인터페이스 통제 |
| TrustZone (Secure World) | TEE (GPS/키 관리 격리) | 신뢰 실행 환경 분리 |

---

## 면접 골든 룰

1. **CAN**: "무인증"이라고만 말하지 말고 — "1983년 설계 가정(폐쇄 네트워크)이 OBD-II/텔레매틱스로 무너졌다"고 맥락을 설명
2. **SecOC**: "MAC 추가"라고만 말하지 말고 — "HSM의 키 → CMAC 생성 → Freshness로 replay 방어"의 전체 체인 설명
3. **Gateway**: "방화벽"이라고만 말하지 말고 — "도메인 격리 + 화이트리스트 라우팅 + 프로토콜 변환"의 세 기능 설명
4. **Tesla 사례**: 비난이 아닌 **아키텍처 분석**으로 접근 — "서버 보안은 강했지만 차량 내부 통신 인증이 부재"
5. **Defense in Depth**: 항상 Secure Boot와 연결 — "부팅 체인의 무결성이 통신 체인의 무결성과 같은 원리"
6. **공격자 관점 먼저**: "이런 방어를 한다"가 아니라 "이런 공격이 가능하므로 → 이렇게 방어한다"
7. **트레이드오프**: SecOC의 장점만이 아니라 "키 관리 복잡도, 레거시 호환성, 대역폭 오버헤드"도 언급
8. **규제 인식**: 기술만이 아니라 UN R155, ISO 21434, TARA 프레임워크 언급으로 시야 확장

---

## 흔한 실수와 올바른 답변

| 실수 | 왜 위험한가 | 올바른 답변 |
|------|-----------|-----------|
| "CAN에 암호화 추가하면 해결" | SecOC는 인증이지 암호화가 아님 | "SecOC는 MAC으로 발신자 인증 — 암호화(기밀성)와 인증(무결성)은 다른 목표" |
| "Tesla가 보안을 무시했다" | SCS, Secure Boot, OTA 서명은 강력 | "서버 보안은 업계 최고, CAN 통신 인증이 빠진 것이 문제" |
| "HSM이면 완벽하다" | 물리 공격, FW 취약점 존재 | "HSM은 SW 공격 차단, 물리 공격(FI/SCA)은 별도 Anti-Tamper 필요" |
| "IDS가 공격을 막는다" | IDS는 탐지, 방지 아님 | "IDS는 탐지, SecOC는 방지 — 둘 다 필요" |
| 공격 벡터 하나만 답변 | 시야가 좁아 보임 | 물리/무선/공급망 3축으로 분류하여 답변 |

---

## 차량 보안 역사 타임라인

```
1983  CAN Bus 개발 (Robert Bosch) — 보안 미고려, 폐쇄 네트워크 가정
1993  ISO 11898 표준화 — CAN 프로토콜 국제 표준
1996  OBD-II 의무화 (미국 EPA) — CAN Bus에 외부 접근점 생성
2010  실험적 CAN 해킹 논문 발표 (UCSD/UW) — 학계에서 위험성 최초 입증
2015  ★ Jeep Cherokee 원격 해킹 — 140만 대 리콜, 차량 보안의 전환점
2015  BMW ConnectedDrive HTTP 해킹 — 220만 대 영향, 차량-서버 TLS 필수 인식
2016  AUTOSAR SecOC 사양 발표 — CAN 메시지 인증 표준화
2017  SHE 2.0 + EVITA 표준 확산 — HSM 기반 ECU 보안 본격화
2018  Tesla Model S Key Fob 클론 (KU Leuven) — DST40 암호 취약점
2019  Tesla HW3 (FSD Computer 1) 양산 — SCS 적용, CAN 인증 미적용
2020  Tesla HW3 MCU 탈옥 — Voltage Glitching으로 Secure Boot 우회
2021  UN R155/R156 채택 — 차량 사이버보안/SW 업데이트 관리 의무화
2022  UWB 기반 디지털 키 도입 (BMW) — Key Fob Relay 방어
2023  Tesla HW4 양산 — 7nm, 여전히 CAN 인증 미적용
2024  Pwn2Own Automotive 2024 — Tesla 인포테인먼트 다수 취약점
2024  UN R155/R156 신차 의무 시행 — 비준수 차량 형식 승인 불가
2025  ★ Tesla FSD 탈옥 동글 대규모 유통 — CAN injection으로 지오펜스 우회
2026  Tesla 10만+ 대 원격 비활성화 — 한국 자동차관리법 집행 강화
2026  SecOC 의무화 논의 가속 — ISO 21434 구현 가이드라인 강화
```

---

## 면접 핵심 키워드 맵

각 주제를 설명할 때 **반드시 포함해야 할 키워드**를 정리. 이 키워드가 빠지면 "깊이가 부족하다"는 인상을 준다.

| 주제 | 필수 키워드 (빠지면 감점) | 차별화 키워드 (있으면 가산점) |
|------|------------------------|--------------------------|
| **CAN Bus** | 브로드캐스트, 무인증, Arbitration ID, OBD-II | Error Counter, Bus-Off, 설계 가정 변화 |
| **CAN 진화** | CAN-FD(64B), CAN-XL(CANsec), 프로토콜 vs 어플리케이션 계층 | AES-GCM, BRS(Bit Rate Switch) |
| **HSM** | 격리 코어, 키 저장, API만 노출, 외부 접근 불가 | SHE vs EVITA, 키 프로비저닝 라이프사이클 |
| **SecOC** | AUTOSAR, Truncated MAC, Freshness Value, Replay 방어 | Cold Start Problem, 레거시 혼재, Proxy SecOC |
| **Gateway** | 도메인 격리, 화이트리스트 라우팅, OBD-II 격리 | Rate Limiting, 프로토콜 변환 |
| **TEE** | TrustZone, Secure/Normal World, SMC Call | GPS 다중소스 검증, OSNMA |
| **IDS** | 탐지(detection) ≠ 방지(prevention), 규칙/주기/ML 기반 | 사양 기반(DBC), 오탐률, SecOC와 역할 구분 |
| **Tesla FSD** | CAN 무인증, GPS spoofing, 서버 보안 vs 내부 보안 | SCS 아키텍처, $10~30/대 vs $118M 매출 손실 |
| **Defense in Depth** | 다중 계층, 단일 레이어 의존 금지, HSM=신뢰 기반 | TARA 프레임워크, Secure Boot 대응 관계 |
| **V2X** | DSRC vs C-V2X, PKI/SCMS, 가명 인증서 | Sybil 공격, Misbehavior Detection |
| **규제** | UN R155(CSMS), ISO 21434, TARA | 자동차관리법(한국), 형식 승인 연계 |
| **Key Fob** | Relay Attack, UWB(ToF), 신호 중계 | PIN to Drive, RSSI 한계, 피코초 분해능 |

### 답변 구조 팁

```
기술 질문 답변의 골든 구조:

  1. [한 문장 핵심 답변] ← 결론 먼저
  2. [왜? 배경/원인] ← 설계 가정, 역사적 맥락
  3. [어떻게? 기술 메커니즘] ← 구체적 동작 (다이어그램 그리면 가산)
  4. [한계/트레이드오프] ← 완벽하지 않은 이유 (깊이 증명)
  5. [Secure Boot 연결] ← 기존 지식과 연결 (시야 증명)

  예시: "SecOC란 무엇인가?"
  1. "CAN 메시지에 MAC을 추가하여 발신자를 인증하는 AUTOSAR 모듈이다."
  2. "CAN은 1983년 폐쇄 네트워크 가정으로 설계되어 인증이 없었고..."
  3. "HSM이 대칭키로 AES-CMAC을 생성하고, Freshness Value로..."
  4. "단, Cold Start 취약 구간과 레거시 ECU 혼재 문제가 있다."
  5. "Secure Boot의 Chain of Trust와 같은 원리 — 모든 노드가 참여해야 유효하다."
```

---

## 규제 빠른 참조

| 규제 | 대상 | 핵심 | 위반 시 |
|------|------|------|---------|
| UN R155 | 전 세계 신차 | CSMS (사이버보안 관리 시스템) | 형식 승인 불가 |
| UN R156 | 전 세계 신차 | SUMS (SW 업데이트 관리 시스템) | 형식 승인 불가 |
| ISO 21434 | 개발 프로세스 | TARA + 보안 엔지니어링 | 인증 불가 |
| 자동차관리법 (한국) | 차량 소유자 | SW 무단 변경 금지 | 2년 징역 / 2천만 원 벌금 |

---
!!! warning "실무 주의점 — OTA 검증 단계 누락 시 fleet 전체 위험"
    **현상**: OTA 업데이트 패키지에 서명 검증만 적용하고 버전 다운그레이드 방지(Anti-Rollback)를 빠뜨리면, 공격자가 구 취약 버전 서명 패키지를 재배포해 fleet 전체를 취약 상태로 되돌릴 수 있다.

    **원인**: 서명 검증(무결성)과 버전 단조성(Monotonic Counter) 검증은 별도 구현 항목이라 후자가 빠지는 경우가 빈번하다.

    **점검 포인트**: HSM 내 Monotonic Counter 값이 업데이트 후 증가하는지, 그리고 이전 버전 패키지를 재주입했을 때 ECU가 거부(NACK)하는지 벤치 테스트로 확인. R156(SUMS) 요구 항목의 "Rollback Prevention" 체크박스가 TARA에 포함되어 있는지 검토.

## 핵심 정리

- **CAN 자체는 무인증** — 외부 접근(OBD-II) 시 모든 메시지 위조 가능.
- **SecOC + HSM + Gateway + IDS = 4-layer 표준 스택**.
- **Tesla 사례 = 외부만 방어하고 내부는 신뢰한 결과**.
- **표준 = R155/R156/21434** — CSMS/SUMS/TARA 가 핵심 키워드.

## 다음 단계

- 퀴즈로 마무리: [전체 Quiz Index](../quiz/) — 5개 모듈 각 5문항씩, 총 25문항.
- 심화: 회사 내 ECU 한 종류를 골라 본 cheat sheet 의 모든 키워드를 매핑해 보는 표를 작성한다.
- 추가 자료: ISO/SAE 21434, UN R155/R156, AUTOSAR SecOC, NHTSA Cybersecurity Best Practices.

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
