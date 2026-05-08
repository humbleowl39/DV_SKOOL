# Module 04 — Quick Reference Card

<!-- DV-SKOOL-CH-CTX:start -->
<div class="chapter-context" data-cat="soc">
  <a class="chapter-back" href="../">
    <span class="chapter-back-arrow">←</span>
    <span class="chapter-back-icon">🛡️</span>
    <span class="chapter-back-text">ARM Security</span>
  </a>
  <span class="chapter-divider">›</span>
  <span class="chapter-marker chapter-quickref-marker">★ Quick Reference</span>
</div>
<!-- DV-SKOOL-CH-CTX:end -->

<!-- DV-SKOOL-CH-TOC:start -->
<div class="page-toc">
  <span class="page-toc-label">목차</span>
  <a class="page-toc-link" href="#한줄-요약">한줄 요약</a>
  <a class="page-toc-link" href="#핵심-정리">핵심 정리</a>
  <a class="page-toc-link" href="#boot-stage별-보안-레벨">Boot Stage별 보안 레벨</a>
  <a class="page-toc-link" href="#월드-전환-빠른-참조">월드 전환 빠른 참조</a>
  <a class="page-toc-link" href="#el-전환-빠른-참조">EL 전환 빠른 참조</a>
  <a class="page-toc-link" href="#메모리-번역-빠른-참조">메모리 번역 빠른 참조</a>
  <a class="page-toc-link" href="#soc-보안-인프라">SoC 보안 인프라</a>
  <a class="page-toc-link" href="#면접-골든-룰">면접 골든 룰</a>
  <a class="page-toc-link" href="#이력서-연결">이력서 연결</a>
  <a class="page-toc-link" href="#기존-자료와의-연결">기존 자료와의 연결</a>
  <a class="page-toc-link" href="#코스-마무리">코스 마무리</a>
</div>
<!-- DV-SKOOL-CH-TOC:end -->

!!! objective "사용 목적"
    참조용 치트시트.

!!! info "사전 지식"
    - [Module 01-03](01_exception_level_trustzone.md)

## 한줄 요약
```
ARM 보안 = Exception Level(EL0~3, 권한 수직 계층) × TrustZone(S/NS, 월드 수평 분리). EL3만 월드 전환 가능. 모든 버스에 NS 비트로 HW 강제 격리.
```

---
!!! warning "실무 주의점 — Stage 2 translation 미설정으로 hypervisor 격리 실패"
    **현상**: VM-A 가 VM-B 또는 hypervisor 메모리를 그대로 read/write 할 수 있다.

    **원인**: EL2 진입 후 VTTBR_EL2/VTCR_EL2 에 Stage 2 page table 을 설정하지 않은 채 guest 를 ERET 하여, IPA→PA 변환이 identity 로 동작한다.

    **점검 포인트**: VM 부팅 전 VTCR_EL2.T0SZ/SL0 와 VTTBR_EL2 가 유효한 S2 table 을 가리키는지, guest 가 다른 VM IPA 영역 access 시 Stage 2 abort 가 발생하는지 SVA/coverage 로 확인.

!!! tip "💡 이해를 위한 비유"
    **ARM Security 마스터 = EL × NS × Stage 의 모든 조합 인지** ≈ **권한 매트릭스 전문가**

    EL0/1/2/3 × Secure/NS × Stage1/Stage2 = 다축 권한 모델. 각 조합에서 어떤 자원이 visible / accessible 한지 즉시 그리는 것이 마스터.

---

!!! danger "❓ 흔한 오해"
    **오해**: EL3 가 항상 활성화되어 있다

    **실제**: EL3 가 OEM 에 따라 disable 될 수 있음 (예: Cortex-A 에서 EL3 미사용 SoC). 그 경우 secure ↔ non-secure 전환은 EL2 / hypervisor 가 담당.

    **왜 헷갈리는가**: ARM 표준 spec 의 "EL3 가 monitor" 표현 때문에 항상 있다고 가정.

## 핵심 정리

| 주제 | 핵심 포인트 |
|------|------------|
| EL3 | 최고 권한, 항상 Secure, BootROM + ATF 실행 |
| EL2 | Hypervisor, VM 격리 (ARMv8.4+: Secure EL2 / FF-A) |
| S-EL1 / NS-EL1 | TEE OS / 일반 OS |
| S-EL0 / NS-EL0 | Trusted App / 일반 앱 |
| TrustZone | NS 비트로 HW 격리, SW 조작 불가 |
| EL 전환 | SVC(→EL1), HVC(→EL2), SMC(→EL3), ERET(하향) |
| VBAR_ELn | 각 EL의 Exception Vector Table 기준 주소 |
| 메모리 번역 | EL별 TTBR, Stage 1(VA→IPA) + Stage 2(IPA→PA) |
| SMC | 유일한 월드 전환 경로, EL3 경유 필수, SMCCC 규약 |
| TZPC | APB 주변장치 Secure/NS 분류 |
| TZASC | DRAM 영역(Region) Secure/NS 분할, 물리 주소 기반 |
| SMMU | DMA Master별 주소 변환 + 접근 제어, Stream ID 기반 |
| GIC (v3) | 인터럽트 Group 0(EL3)/1S(S-EL1)/1NS(NS-EL1) 분류 |
| Cache NS-bit | 캐시/TLB에 NS 태그 → 같은 PA도 S/NS 별도 엔트리 |
| Secure Enclave | CPU 독립 전용 프로세서+RAM — TrustZone과 상호 불신, Key Box + Crypto |
| Internal Enclave | SoC on-die, 최고 보안 — Apple SEP, Samsung SSP |
| External Enclave | 별도 IC (SPI), Root of Trust + Private Storage — 물리 분리 |
| DRM Pipeline | Secure 복호화 → Secure 버퍼(TZASC) → Secure Display — 평문 미노출 |
| SCR_EL3 | NS 비트 = 보안 상태 결정, EL3만 변경 가능 |
| Anti-Rollback | OTP Monotonic Counter, EL3에서 관리, 이전 버전 차단 |
| Measured Boot | 각 단계 해시 측정 → PCR 누적 → Remote Attestation |

---

## Boot Stage별 보안 레벨

```
BL1(BootROM) → BL2(FSBL) → BL31(Monitor) → BL32(TEE) → BL33(U-Boot) → Linux
  EL3/S        S-EL1/S       EL3/S(상주)    S-EL1/S     NS-EL1/NS     NS-EL1/NS
                                                          ^^^^^^^^
                                                    핵심 전환점: NS=1 설정
```

## 월드 전환 빠른 참조

```
NS→S: Normal World에서 SMC 호출 → EL3 → SCR.NS=0 → ERET → S-EL1
S→NS: Secure World에서 SMC 반환 → EL3 → SCR.NS=1 → ERET → NS-EL1
항상 EL3 경유 — 직접 전환 불가
```

## EL 전환 빠른 참조

```
상향: SVC(EL0→1), HVC(EL1→2), SMC(any→3), IRQ/FIQ/Abort(→설정 EL)
하향: ERET (SPSR→PSTATE, ELR→PC)
벡터: VBAR_ELn + offset (4×4 매트릭스: Source×Type)
HW 자동: PSTATE→SPSR 저장, PC→ELR 저장, 인터럽트 마스킹, PC→VBAR+offset
```

## 메모리 번역 빠른 참조

```
EL0/1: TTBR0_EL1(유저) + TTBR1_EL1(커널) — Stage 1
EL2:   TTBR0_EL2(자체) + VTTBR_EL2(Stage 2, VM 격리)
EL3:   TTBR0_EL3(Secure Monitor)
가상화: VA → Stage1 → IPA → Stage2 → PA (2단계 번역)
```

## SoC 보안 인프라

```
TZPC:    APB Slave 보호 (OTP=Secure, UART=NS)
TZASC:   DRAM 영역 보호 (Region 단위, 물리 주소 기반)
SMMU:    DMA Master별 보호 (Stream ID, 페이지 단위, 주소 변환 포함)
GIC(v3): IRQ 보호 (Group 0→EL3, 1S→S-EL1, 1NS→NS-EL1)
Cache:   NS-bit 태깅 (같은 PA도 S/NS 별도 캐시 라인)
```

---

## 면접 골든 룰

1. **두 축**: "EL(권한 수직) × TrustZone(월드 수평) = ARM 보안 모델"
2. **EL3 = 게이트**: "유일한 월드 전환점 — EL3가 뚫리면 TrustZone 전체 무력화"
3. **NS 비트**: "HW 강제, SW 조작 불가 — EL3만 변경 가능"
4. **BootROM 이유**: "최초 보안 설정(TZPC/TZASC/SCR)에 EL3 필수"
5. **전환점**: "BL31→BL33에서 SCR.NS=0→1 — 이후 Secure 접근 불가"
6. **Secure Boot 연결**: "서명=무엇을 실행, TrustZone=어떤 권한으로 — 둘 다 필요"
7. **EL 전환 HW 보장**: "Exception으로만 상향, ERET으로만 하향 — SPSR/ELR은 해당 EL에서만 접근"
8. **Stage 2**: "Hypervisor의 VM 격리 핵심 — Guest가 물리 주소를 '착각', Stage 2가 실제 매핑 제어"
9. **SMMU vs TZASC**: "TZASC=영역, SMMU=디바이스별 — 다층 방어"
10. **Anti-Rollback**: "OTP Counter로 버전 역행 방지 — Secure Boot + 버전 검증 = 완전한 이미지 보호"
11. **Secure Enclave**: "TrustZone의 한계(캐시 부채널, Trusted OS 취약점)를 전용 HW로 제거 — 대체가 아닌 보완"
12. **상호 불신**: "TrustZone↔Enclave는 서로 신뢰하지 않음 — Chain of Trust처럼 각 계층이 상대를 검증"

---

## 이력서 연결

| 항목 | 면접 질문 | 핵심 답변 |
|------|----------|----------|
| BootROM EL3 | "BootROM이 왜 EL3인가?" | 최초 보안 설정(SCR/TZPC/TZASC) 권한 + 다음 단계 EL 결정 |
| Secure Boot | "Boot와 보안 레벨 관계?" | BL1(EL3/S)→BL2(S-EL1/S)→BL31→BL33(NS), 핵심 전환점=NS=1 |
| 보안 공격/방어 | "TrustZone이 방어하는 공격?" | OS 해킹→키 탈취(Secure 메모리 격리), DMA 공격(TZASC+SMMU) |
| OTP/JTAG | "보안 인프라 설정은?" | BootROM(EL3)이 TZPC로 OTP=Secure, JTAG=OTP Blow |
| EL 전환 메커니즘 | "EL 전환이 어떻게 동작하는가?" | SVC/HVC/SMC(상향) + ERET(하향), VBAR 벡터 테이블, SPSR/ELR HW 자동 저장 |
| DV 보안 검증 | "보안 레벨을 어떻게 검증하는가?" | Positive(정상 전환) + Negative(NS→Secure 차단) + SVA assertion |

---

## 기존 자료와의 연결

```
soc_secure_boot_ko Unit 2: Boot Stage에서 EL 간략 언급
  → arm_security_ko: EL/TrustZone/SMC/TZPC/TZASC 상세 보충

soc_secure_boot_ko Unit 5: 공격과 방어
  → arm_security_ko Unit 2: 보안 인프라가 방어하는 메커니즘

soc_secure_boot_ko Unit 7: BootROM DV
  → arm_security_ko Unit 3: 보안 레벨 전환 검증 시나리오
```

---

## 코스 마무리

[퀴즈](quiz/index.md) · [용어집](glossary.md) · 다음: [Secure Boot](../../soc_secure_boot/), [Virtualization](../../virtualization/) (EL2 hypervisor).

<div class="chapter-nav">
  <a class="nav-prev" href="../03_secure_boot_connection/">
    <div class="nav-label">◀ 이전</div>
    <div class="nav-title">Secure Boot에서의 보안 레벨 적용</div>
  </a>
  <a class="nav-next" href="../quiz/">
    <div class="nav-label">다음 ▶</div>
    <div class="nav-title">퀴즈로 이동</div>
  </a>
</div>


--8<-- "abbreviations.md"
