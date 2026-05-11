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
  <a class="page-toc-link" href="#1-why-care-이-카드가-왜-필요한가">1. Why care?</a>
  <a class="page-toc-link" href="#2-intuition-비유와-한-장-그림">2. Intuition</a>
  <a class="page-toc-link" href="#3-작은-예-mte-tag-mismatch-한-load-가-tag-fault-까지-가는-1-cycle">3. 작은 예 — MTE tag mismatch 1 cycle</a>
  <a class="page-toc-link" href="#4-일반화-arm-security-마스터의-2-개의-축-과-5-가지-매핑">4. 일반화 — 2 축 + 5 매핑</a>
  <a class="page-toc-link" href="#5-디테일-치트시트-전부">5. 디테일 — 치트시트 전부</a>
  <a class="page-toc-link" href="#6-이-카드를-봐야-할-때-와-흔한-오해">6. 이 카드를 봐야 할 때 + 흔한 오해</a>
  <a class="page-toc-link" href="#7-핵심-정리-key-takeaways">7. 핵심 정리</a>
</div>
<!-- DV-SKOOL-CH-TOC:end -->

!!! objective "사용 목적"
    이 카드는 **참조용 치트시트** — 면접/디버그/리뷰 중에 빠르게 펼쳐 보는 용도. 학습 목표는 _카드의 표를 _읽는 능력_ 이 아니라 _불러서 즉시 적용_ 하는 능력_:

    - **Recall** EL × NS 매트릭스 의 각 칸과 그 의미를 즉시 떠올릴 수 있다.
    - **Apply** "이 증상이 나오면 어느 표를 본다" 의 매핑을 즉시 적용할 수 있다.
    - **Justify** 면접 골든 룰 12 개를 _왜_ 그렇게 답하는지 1 줄로 설명할 수 있다.
    - **Compare** TZASC vs SMMU, Verified vs Measured Boot, Internal vs External Enclave 의 짝을 즉시 비교할 수 있다.

!!! info "사전 지식"
    - [Module 01-03](01_exception_level_trustzone.md) (모든 학습 모듈 완료 후 사용)

---

## 1. Why care? — 이 카드가 왜 필요한가

면접/리뷰/디버그의 _압축된 시간_ 에는 4 개 모듈을 다 펼쳐볼 수 없습니다. 하지만 _질문 한 줄_ → _답 한 줄_ 의 거리를 좁히려면 EL/NS 매트릭스, 5 축 인프라, world switch 흐름, boot stage 매핑, anti-rollback — 이 5 개 표가 머릿속에 정렬돼 있어야 합니다.

이 카드는 그 정렬된 형태를 _그대로_ 옮긴 것. Module 01-03 에서 다룬 모든 구조를 _질문 패턴 별_ 로 다시 묶어, 실무 상황 (debug, review, interview) 에서 즉시 호출 가능하게 만든 것이 이 모듈의 본질입니다.

---

## 2. Intuition — 비유와 한 장 그림

!!! tip "💡 한 줄 비유"
    **이 카드** ≈ _권한 매트릭스 전문가의 책상 위 한 장_.<br>
    EL0/1/2/3 × Secure/NS × Stage1/Stage2 = 다축 권한 모델. 각 조합에서 어떤 자원이 visible / accessible 한지 즉시 그리는 것이 마스터. 이 카드는 그 그림을 _접어 둔 형태_.

### 한 장 그림 — ARM Security 의 모든 어휘 한눈에

```
                        ┌─────────────── Trust Chain ────────────────┐
                        │                                              │
                        │   BootROM ▶ BL2 ▶ BL31 ▶ BL32 ▶ BL33 ▶ Linux │
                        │   (EL3/S)   (S-EL1) (EL3/S 상주)  (NS-EL1)    │
                        │                          │                    │
                        │              ┌───────────┴──────────┐         │
                        │              │ SCR_EL3.NS = 0 → 1   │         │
                        │              │ (turning point)       │         │
                        │              └───────────────────────┘         │
                        └──────────────────────────────────────────────┘
                                           │
                                           ▼
        ┌───────────── Runtime Architecture ───────────────┐
        │                                                   │
        │  EL3 BL31 (Secure Monitor 상주)                    │
        │   ▲ SMC                                           │
        │   │                                               │
        │  EL2 hypervisor   ─── Stage 2 (VM 격리) ──         │
        │   │                                               │
        │  EL1 OS kernel    ─── Stage 1 (VA→IPA) ──         │
        │   │                                               │
        │  EL0 application  (NS app | S TA)                 │
        │                                                   │
        │   × NS bit (0 = Secure / 1 = Non-Secure)          │
        │   = 7 mode (EL3 는 항상 Secure)                    │
        │                                                   │
        │  5 축 인프라:                                      │
        │   TZPC (peripheral) / TZASC (DRAM) / GIC (IRQ)     │
        │   SMMU (DMA stream) / Cache NS-tag                 │
        │                                                   │
        │  Beyond TZ:                                       │
        │   Internal Enclave  (Apple SEP / Samsung SSP)     │
        │   External Enclave  (TPM / SE050) — Mailbox 통신  │
        └───────────────────────────────────────────────────┘
```

### 왜 이 형식인가 — Design rationale

이 카드의 모든 표는 _"_질문 패턴_ → _답_"_ 한 jump 로 답변 가능하도록 정렬돼 있습니다.

- **"BootROM 이 왜 EL3?"** → §5 핵심 정리 표 → 답.
- **"NS 에서 Secure 접근하면?"** → §5 SoC 보안 인프라 표 → 답.
- **"TZASC vs SMMU?"** → §5 핵심 정리 표 → 답.

검색이 빠르려면 _표 1 개 = 질문 패턴 1 개_ 로 분할돼야 — 이게 quick reference 디자인의 본질.

---

## 3. 작은 예 — MTE tag mismatch 한 load 가 tag fault 까지 가는 1 cycle

ARMv8.5 의 MTE (Memory Tagging Extension) 는 메모리 안전성 (use-after-free, buffer overflow) 의 HW 방어. 한 load instruction 이 tag mismatch 로 fault 되는 _1 cycle_ 을 들여다보면, ARM 보안 모델의 _tag 비교 + EL/NS 결합_ 이 가장 압축된 형태로 나타납니다.

```
   Cycle:   t0          t1                t2
   ──────────────────────────────────────────────────►

   t0: NS-EL0 app 이 LDR x0, [x1]
       VA  = 0x_4_0000_0000_1000   (top 4 bit = address tag = 0x4)
       x1 = 0x_4_0000_0000_1000

   t1: HW 가
       (a) Stage 1 translate: VA → IPA
       (b) physical memory 의 tag (16-byte granule 별 4-bit) read
       (c) address tag (x1[59:56] = 0x4) vs memory tag 비교
       → memory tag = 0x7 → 4 != 7 → MISMATCH

   t2: HW 가 SError 또는 sync data abort with EC=0x11 (tag check fault)
       → exception entry to EL1 (NS-EL1, OS kernel)
       → kernel 이 SIGSEGV with si_code=SEGV_MTESERR 를 user 에게 전달
```

| Step | 누가 | 무엇을 | 의미 |
|---|---|---|---|
| t0 | NS-EL0 app | tag-check 가능한 load 발행 | TBI (Top Byte Ignore) 가 enable 된 영역 |
| t1.a | Stage 1 MMU | VA → IPA | 일반 paging |
| t1.b | MTE engine | 16B granule 의 4-bit tag fetch | DRAM 의 별도 영역 또는 inline ECC 활용 |
| t1.c | MTE engine | address tag vs memory tag 비교 | 1 cycle 비교, mismatch = fault |
| t2 | HW | sync exception (EC=0x11) | EL1 vector entry (NS-EL1) |

```c
// User 측 — MTE-aware free 가 tag 를 변경
void *p = malloc(64);
free(p);          // free 가 영역의 tag 를 무효 값으로 set
*(uint64_t *)p;   // ← 이 load 가 t0~t2 시퀀스를 트리거
                  //   tag mismatch → SIGSEGV (use-after-free 검출)
```

!!! note "여기서 잡아야 할 두 가지"
    **(1) MTE 도 EL/NS 모델 안에서 동작** — tag fault 는 현재 EL 의 vector 로 들어가고, NS world 의 fault 가 secure world 로 escalation 되지 않습니다. 즉 NS 의 use-after-free 가 secure 자원에 영향을 주지 않음.<br>
    **(2) MTE 는 "확률적 검출" (random 4-bit tag → 1/16 충돌 확률)** — 100% deterministic 방어가 아니라 _grading 도구_ 에 가깝습니다. constant-time critical 코드는 별도 mitigation 필요.

---

## 4. 일반화 — ARM Security 마스터의 2 개의 축 과 5 가지 매핑

### 4.1 두 개의 축

```
   축 1. EL (수직, 권한 계층)
   ───────────────────────────
   EL0 → EL1 → EL2 → EL3
   상승은 Exception 으로만, 하강은 ERET 으로만.

   축 2. NS (수평, 월드)
   ─────────────────────
   Secure (NS=0) ↔ Non-Secure (NS=1)
   EL3 만 NS bit toggle 가능, 전환은 SMC 로만.

   곱 = EL × NS = 8 mode (EL3 는 항상 Secure → 실용 7 mode).
```

### 4.2 5 가지 매핑 (외워둘 핵심 짝)

```
   ① EL ↔ SW              EL3=BL31, S-EL1=OP-TEE, NS-EL1=Linux, NS-EL0=app
   ② NS ↔ 자원            NS=0 → secure DRAM/OTP/Crypto/Group0 IRQ
                          NS=1 → 일반 DRAM/timer/Group1NS IRQ
   ③ Stage ↔ 단계         Stage1 = VA→IPA (Guest OS), Stage2 = IPA→PA (Hypervisor)
   ④ Boot ↔ EL/NS         BL1/BL31 = EL3/S, BL2/BL32 = S-EL1, BL33 = NS-EL1
   ⑤ 5 축 ↔ 보호 단위     TZPC=peripheral, TZASC=DRAM region, SMMU=stream id,
                          GIC=IRQ, Cache=line tag
```

이 5 매핑이 머릿속에 _즉시 호출_ 되면, 어떤 질문이든 1 jump 안에 정리됩니다.

---

## 5. 디테일 — 치트시트 전부

### 5.1 한줄 요약

```
ARM 보안 = Exception Level(EL0~3, 권한 수직 계층) × TrustZone(S/NS, 월드 수평 분리). EL3만 월드 전환 가능. 모든 버스에 NS 비트로 HW 강제 격리.
```

### 5.2 핵심 정리표

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

### 5.3 Boot Stage별 보안 레벨

```
BL1(BootROM) → BL2(FSBL) → BL31(Monitor) → BL32(TEE) → BL33(U-Boot) → Linux
  EL3/S        S-EL1/S       EL3/S(상주)    S-EL1/S     NS-EL1/NS     NS-EL1/NS
                                                          ^^^^^^^^
                                                    핵심 전환점: NS=1 설정
```

### 5.4 월드 전환 빠른 참조

```
NS→S: Normal World에서 SMC 호출 → EL3 → SCR.NS=0 → ERET → S-EL1
S→NS: Secure World에서 SMC 반환 → EL3 → SCR.NS=1 → ERET → NS-EL1
항상 EL3 경유 — 직접 전환 불가
```

### 5.5 EL 전환 빠른 참조

```
상향: SVC(EL0→1), HVC(EL1→2), SMC(any→3), IRQ/FIQ/Abort(→설정 EL)
하향: ERET (SPSR→PSTATE, ELR→PC)
벡터: VBAR_ELn + offset (4×4 매트릭스: Source×Type)
HW 자동: PSTATE→SPSR 저장, PC→ELR 저장, 인터럽트 마스킹, PC→VBAR+offset
```

### 5.6 메모리 번역 빠른 참조

```
EL0/1: TTBR0_EL1(유저) + TTBR1_EL1(커널) — Stage 1
EL2:   TTBR0_EL2(자체) + VTTBR_EL2(Stage 2, VM 격리)
EL3:   TTBR0_EL3(Secure Monitor)
가상화: VA → Stage1 → IPA → Stage2 → PA (2단계 번역)
```

### 5.7 SoC 보안 인프라

```
TZPC:    APB Slave 보호 (OTP=Secure, UART=NS)
TZASC:   DRAM 영역 보호 (Region 단위, 물리 주소 기반)
SMMU:    DMA Master별 보호 (Stream ID, 페이지 단위, 주소 변환 포함)
GIC(v3): IRQ 보호 (Group 0→EL3, 1S→S-EL1, 1NS→NS-EL1)
Cache:   NS-bit 태깅 (같은 PA도 S/NS 별도 캐시 라인)
```

### 5.8 면접 골든 룰

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

### 5.9 이력서 연결

| 항목 | 면접 질문 | 핵심 답변 |
|------|----------|----------|
| BootROM EL3 | "BootROM이 왜 EL3인가?" | 최초 보안 설정(SCR/TZPC/TZASC) 권한 + 다음 단계 EL 결정 |
| Secure Boot | "Boot와 보안 레벨 관계?" | BL1(EL3/S)→BL2(S-EL1/S)→BL31→BL33(NS), 핵심 전환점=NS=1 |
| 보안 공격/방어 | "TrustZone이 방어하는 공격?" | OS 해킹→키 탈취(Secure 메모리 격리), DMA 공격(TZASC+SMMU) |
| OTP/JTAG | "보안 인프라 설정은?" | BootROM(EL3)이 TZPC로 OTP=Secure, JTAG=OTP Blow |
| EL 전환 메커니즘 | "EL 전환이 어떻게 동작하는가?" | SVC/HVC/SMC(상향) + ERET(하향), VBAR 벡터 테이블, SPSR/ELR HW 자동 저장 |
| DV 보안 검증 | "보안 레벨을 어떻게 검증하는가?" | Positive(정상 전환) + Negative(NS→Secure 차단) + SVA assertion |

### 5.10 기존 자료와의 연결

```
soc_secure_boot_ko Unit 2: Boot Stage에서 EL 간략 언급
  → arm_security_ko: EL/TrustZone/SMC/TZPC/TZASC 상세 보충

soc_secure_boot_ko Unit 5: 공격과 방어
  → arm_security_ko Module 02: 보안 인프라가 방어하는 메커니즘

soc_secure_boot_ko Unit 7: BootROM DV
  → arm_security_ko Module 03: 보안 레벨 전환 검증 시나리오
```

---

## 6. 이 카드를 봐야 할 때 + 흔한 오해

### 이 카드를 봐야 할 때

| 상황 | 어느 표를 보나 |
|---|---|
| 면접에서 "BootROM 이 왜 EL3?" 같은 _1 줄 답_ 이 필요할 때 | §5.8 면접 골든 룰 #4 |
| Code review 중 _SCR_EL3 / SPSR / TZASC register_ 의미 확인 | §5.2 핵심 정리표 |
| 디버그 시 _증상_ 으로 _원인 영역_ 추정할 때 | §5.7 SoC 보안 인프라 (5 축 → 보호 단위) |
| Boot trace 분석 — _이 단계가 어느 EL/NS_ ? | §5.3 Boot Stage 표 |
| World switch 디버그 — _SMC 후 NS bit 가 언제 toggle_ ? | §5.4 월드 전환 + Module 02 §3 |
| TZASC fail 인지 SMMU fail 인지 헷갈릴 때 | §5.7 + §5.8 #9 |
| 신입 교육 / 위키 작성 시 1 페이지 요약이 필요할 때 | §5.1 한줄 요약 + §5.2 |

### 흔한 오해 (Quick reference 사용 시 자주 잡히는 함정)

!!! danger "❓ 오해 1 — 'EL3 가 항상 활성화되어 있다'"
    **실제**: EL3 가 OEM 에 따라 disable 될 수 있음 (예: Cortex-A 에서 EL3 미사용 SoC, R-class). 그 경우 secure ↔ non-secure 전환은 EL2 / hypervisor 가 담당하거나, 단일 world 모델로 동작.<br>
    **왜 헷갈리는가**: ARM 표준 spec 의 "EL3 가 monitor" 표현 때문에 항상 있다고 가정.

!!! danger "❓ 오해 2 — '치트시트의 표만 외우면 끝'"
    **실제**: 표는 _질문 → 답_ 의 jump 를 빠르게 만드는 도구일 뿐, _왜 그런가_ 의 reasoning 은 Module 01-03 의 본문에 있습니다. Quick ref 만 외운 답은 follow-up 질문 ("그럼 EL3 가 없으면?", "TZASC 와 SMMU 가 conflict 하면?") 에 대답 못 합니다.<br>
    **왜 헷갈리는가**: "표 = 정답" 이라는 단순화.

!!! danger "❓ 오해 3 — 'Stage 2 가 NS world 만의 기능'"
    **실제**: Stage 2 는 Secure 와 NS 양쪽 EL2 모두에서 사용 가능합니다. ARMv8.4+ 의 Secure EL2 (SPM/Hafnium) 도 Stage 2 로 SP 들 끼리 격리합니다.<br>
    **왜 헷갈리는가**: 일반 가상화 = NS-EL2 (KVM) 라는 인상.

!!! danger "❓ 오해 4 — 'SMC 와 HVC 가 비슷한 명령'"
    **실제**: 가는 곳이 다릅니다. HVC → EL2 (hypervisor service), SMC → EL3 (secure monitor). SMC 만이 월드 전환을 트리거.<br>
    **왜 헷갈리는가**: 둘 다 "...VC" 명령이고 비슷한 trap 메커니즘이라.

### DV 디버그 체크리스트 (이 카드 사용 중에 자주 보는 분류 실수)

| 증상 | 1차 의심 | 어디 보나 |
|---|---|---|
| NS world 가 secure DRAM 읽음 | TZASC region 잘못 vs NS attribute 미전파 | §5.7 + Module 02 §6 |
| GPU DMA 가 secure 영역 도달 | SMMU stream id 매핑 누락 | §5.7 SMMU 행 + Module 02 §5.5 |
| OTP fuse 가 NS 에서 read | TZPC slave 분류 + mirror register 누락 | §5.7 TZPC 행 + Module 03 §6 |
| Stage 2 미설정으로 VM escape | VTTBR_EL2/VTCR_EL2 미설정 | §5.6 + Module 01 §5.7 |
| SMC 후 NS world 에 secure 잔여 register | BL31 context save 누락 (NEON/SVE) | §5.4 + Module 02 §6 |
| Anti-Rollback 우회 (구 version 부팅 됨) | OTP counter blow 누락 | §5.2 Anti-Rollback + Module 03 §6 |
| Spectre 류 사이드 채널로 secure key 추출 | NS tag 만으로 부족 — constant-time 코드 필요 | §5.2 Cache + Module 02 §5.6 (주의 항) |
| Enclave key 가 mailbox 응답에 포함 | mailbox API 가 raw key 노출 (잘못 설계) | §5.2 Secure Enclave + Module 02A §3 |

---

!!! warning "실무 주의점 — Stage 2 translation 미설정으로 hypervisor 격리 실패"
    **현상**: VM-A 가 VM-B 또는 hypervisor 메모리를 그대로 read/write 할 수 있다.

    **원인**: EL2 진입 후 VTTBR_EL2/VTCR_EL2 에 Stage 2 page table 을 설정하지 않은 채 guest 를 ERET 하여, IPA→PA 변환이 identity 로 동작한다.

    **점검 포인트**: VM 부팅 전 VTCR_EL2.T0SZ/SL0 와 VTTBR_EL2 가 유효한 S2 table 을 가리키는지, guest 가 다른 VM IPA 영역 access 시 Stage 2 abort 가 발생하는지 SVA/coverage 로 확인.

## 7. 핵심 정리 (Key Takeaways)

- **2 축 + 7 mode 매트릭스** 가 ARM Security 의 어휘 — 모든 질문은 어느 mode 의 _resource visibility_ 인가로 환원 가능.
- **5 축 인프라 (TZPC/TZASC/GIC/SMMU/Cache)** 가 _보호 단위_ 별로 같은 NS bit 를 해석. 디버그 시 증상 → 5 축 중 하나 매핑.
- **두 메커니즘 결합 (Verified Boot + Architecture Enforcement) + Anti-Rollback + Measured Boot** 이 보안 부팅의 4 다리.
- **TrustZone 너머의 Secure Enclave** 는 _상호 불신_ 모델로 TZ 의 한계 (캐시 부채널, RCE) 를 보완.
- **이 카드는 진입점일 뿐** — _왜 그런가_ 가 필요하면 Module 01-03 본문으로.

!!! warning "실무 주의점"
    - 면접에서 _golden rule_ 만 답하면 follow-up 에 무너짐 — 각 rule 의 _근거_ 를 본문에서 짚어 둘 것.
    - SoC 마다 EL3 implementation 여부 / TZASC 의 lock bit / SMMU 의 secure stream 지원이 다름 — _우리 SoC 의 spec 부터 확인_.
    - Stage 2 미설정 / NS attribute 미전파 / OTP mirror 누락 / BL31 context 누락 — 이 4 가지가 사내 실무 주의점에 직접 등장. _negative test_ 로 강제 검증.

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
