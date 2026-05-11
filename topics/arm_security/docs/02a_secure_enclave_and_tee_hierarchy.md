# Module 02A — Secure Enclave & TEE Hierarchy

<div class="learning-meta">
  <span class="meta-badge meta-level-advanced">📊 Advanced</span>
</div>

<!-- DV-SKOOL-CH-CTX:start -->
<div class="chapter-context" data-cat="soc">
  <a class="chapter-back" href="../">
    <span class="chapter-back-arrow">←</span>
    <span class="chapter-back-icon">🛡️</span>
    <span class="chapter-back-text">ARM Security</span>
  </a>
  <span class="chapter-divider">›</span>
  <span class="chapter-marker">Module 02A</span>
</div>
<!-- DV-SKOOL-CH-CTX:end -->

<!-- DV-SKOOL-CH-TOC:start -->
<div class="page-toc">
  <span class="page-toc-label">목차</span>
  <a class="page-toc-link" href="#1-why-care-이-모듈이-왜-필요한가">1. Why care?</a>
  <a class="page-toc-link" href="#2-intuition-비유와-한-장-그림">2. Intuition</a>
  <a class="page-toc-link" href="#3-작은-예-결제-마스터-키가-trustzone-이-뚫려도-살아남는-경로">3. 작은 예 — 마스터 키 보호 경로</a>
  <a class="page-toc-link" href="#4-일반화-tee-계층-과-상호-불신-mutually-distrusting-모델">4. 일반화 — TEE 계층 + 상호 불신</a>
  <a class="page-toc-link" href="#5-디테일-internalexternal-enclave-drm-pipeline-mailbox-secure-channel">5. 디테일</a>
  <a class="page-toc-link" href="#6-흔한-오해-와-dv-디버그-체크리스트">6. 흔한 오해 + DV 디버그 체크리스트</a>
  <a class="page-toc-link" href="#7-핵심-정리-key-takeaways">7. 핵심 정리</a>
</div>
<!-- DV-SKOOL-CH-TOC:end -->

!!! objective "학습 목표"
    이 모듈을 마치면:

    - **Distinguish** TrustZone (CPU 공유 TEE) 와 Secure Enclave (전용 processor + RAM) 를 자원 공유 관점에서 구분할 수 있다.
    - **Identify** 주요 Secure Enclave (Apple SEP, Samsung Knox vault, Google Titan M, AWS Nitro) 의 구조적 공통점을 식별할 수 있다.
    - **Apply** Mutually distrusting 관계를 적용해 둘 중 하나가 침해됐을 때 다른 쪽의 영향 범위를 분석할 수 있다.
    - **Plan** TEE 계층 (REE → Hypervisor → TrustZone → Internal Enclave → External Enclave) 을 책임별로 분리해 설계할 수 있다.
    - **Justify** DRM Protected Media Pipeline 에서 TZASC + SMMU + TZPC + GIC + cache NS-bit 가 모두 필요한 이유를 설명할 수 있다.

!!! info "사전 지식"
    - [Module 01 — Exception Level & TrustZone](01_exception_level_trustzone.md)
    - [Module 02 — World Switch & SoC Security Infra](02_world_switch_soc_infra.md)
    - 일반 OS 의 process 격리, kernel 권한, syscall 흐름

---

## 1. Why care? — 이 모듈이 왜 필요한가

Module 01-02 에서 _"TrustZone 이 Secure World 를 격리한다"_ 라고 했지만, **TrustZone 자체가 뚫리면 어떻게 되는가?** 라는 질문에는 답이 없습니다. 실제 사례 — Spectre 류의 캐시 부채널, OP-TEE 의 RCE 취약점, 또는 Trusted OS bug — 가 발생하면 Secure World 의 _모든_ 키와 데이터가 노출됩니다.

이 모듈은 그 한 단계 위 — **TrustZone 도 신뢰하지 않는 별도 보안 계층** 인 Secure Enclave 와, 여러 TEE 가 _상호 불신_ 으로 공존하는 모델을 다룹니다. 이 모델을 이해하면, 마스터 키 같은 _최상위 비밀_ 은 왜 TrustZone 이 아닌 Enclave 에 보관되는지, 그리고 검증 시 Enclave 의 mailbox / 인증 토큰 / Secure Channel Protocol 을 어떻게 다뤄야 하는지가 보입니다.

---

## 2. Intuition — 비유와 한 장 그림

!!! tip "💡 한 줄 비유"
    **TrustZone vs Secure Enclave** ≈ _같은 빌딩의 보안실 (TZ) vs 길 건너편 별관 (Enclave)_.<br>
    TZASC/SMMU/GIC 가 TZ 의 _경비원_ 이라면, Enclave 는 아예 _별도 건물_ — 건물 사이에도 출입증을 검사하고, 어느 한쪽이 화재가 나도 다른 쪽은 무사. 둘은 서로 _신뢰하지 않으며_ Mailbox + 인증 토큰으로만 대화합니다.

### 한 장 그림 — TEE 계층의 보안 레벨 사다리

```
   보안 레벨 (낮음 → 높음)
   ─────────────────────────────────────────────────────────────
                                                       │
                                                       │ 침해 시
                                                       │ 영향 범위
                                                       ▼

   ┌─────────────────────────────────┐
   │  REE  (Linux/Android, NS-EL0/1) │  최하        ← OS 해킹 = 일반 데이터 노출
   └─────────────────────────────────┘
                ▲
                │ stage 2 격리
   ┌─────────────────────────────────┐
   │  Non-Secure EL2 (Hypervisor/KVM)│              ← VM escape 시 NS world 전체
   └─────────────────────────────────┘
                ▲
                │ NS bit
   ╔═════════════════════════════════╗
   ║  TrustZone (S-EL0/1)            ║              ← TZ 뚫리면 Secure World 전체
   ║  Trusted OS + TA                ║                 (BUT enclave key 는 살아남음)
   ╚═════════════════════════════════╝
                ▲
                │ Mailbox + 인증 토큰
   ╔═════════════════════════════════╗
   ║  Internal Secure Enclave (on-die)║              ← 전용 processor + RAM
   ║  Apple SEP, Samsung SSP         ║                 사이드 채널/RCE 둘 다 무력
   ╚═════════════════════════════════╝
                ▲
                │ SPI Secure Channel (암호화 + MAC)
   ╔═════════════════════════════════╗
   ║  External Secure Enclave (별도 IC)║  최고      ← 물리 분리 → decapping 별도 필요
   ║  TPM, NXP SE050, Infineon SLE97 ║
   ╚═════════════════════════════════╝
```

### 왜 이렇게 설계됐는가 — Design rationale

세 가지 요구가 동시에 풀려야 했습니다.

1. **TrustZone 도 결국 같은 CPU/cache/DRAM 을 공유한다** → 캐시 부채널, speculative execution, Trusted OS RCE 의 표적이 됨 → 자원을 _물리적으로_ 분리한 별도 processor 가 필요.
2. **그러나 모든 secure 작업을 enclave 가 할 수는 없다** → enclave 는 작은 SRAM + 저성능 코어 → 마스터 키 같은 _작은 비밀_ 만 보관하고, 일반적인 TEE 작업은 TrustZone 이 담당.
3. **두 보안 레이어가 서로를 신뢰하면 약한 쪽이 강한 쪽을 끌어내림** → _상호 불신_ 모델: TrustZone 이 enclave 에 요청해도 enclave 는 인증 토큰을 검증해야 응답.

이 세 요구의 교집합이 곧 TEE 계층 + 상호 불신 + Mailbox 통신 모델입니다.

---

## 3. 작은 예 — 결제 마스터 키가 TrustZone 이 뚫려도 살아남는 경로

가장 직관적인 시나리오. OP-TEE (S-EL1) 가 RCE 로 장악된 상태에서, 공격자가 결제 마스터 키를 탈취하려 합니다. 마스터 키는 Internal Secure Enclave 의 Key Box 에 있고, S-EL1 은 키를 _직접_ 읽을 수 없으며 Mailbox 로만 _서명 결과_ 를 요청할 수 있습니다.

```
   ┌──────── Secure World (S-EL1, OP-TEE — 이미 장악됨) ────────┐
   │                                                            │
   │  공격자 코드 (RCE)                                         │
   │      │ ① "마스터 키 줘"                                     │
   │      ▼                                                     │
   │  Enclave Mailbox driver                                    │
   │      │ ② mbox_write({op=GET_KEY, ...})  ─── 인증 토큰 없음  │
   │      ▼                                                     │
   └────────────────────────────────┬───────────────────────────┘
                                    │ APB / shared mailbox
                                    ▼
   ┌───────────── Internal Secure Enclave (전용 processor) ──────┐
   │   Mailbox handler                                          │
   │      │ ③ 토큰 검증 → 실패                                   │
   │      ▼                                                     │
   │   거부: ENCLAVE_ERR_AUTH                                    │
   │                                                            │
   │   (Mailbox handler 가 정상 토큰의 경우만 처리)               │
   │      ┌─────────────────────────────────────┐                │
   │      │ Crypto Accelerator                  │                │
   │      │   key_box[idx] → AES/RSA → ciphertext│                │
   │      │   (key 자체는 외부로 나가지 않음)    │                │
   │      └──────────────┬──────────────────────┘                │
   │                     │ ④ 결과 (서명/암호문) 만 반환            │
   └─────────────────────┼──────────────────────────────────────┘
                         │
                         ▼
            ⑤ S-EL1 받는 것: 키가 아니라 _결과_ 뿐
               → 마스터 키는 enclave 밖으로 나간 적 없음
               → 공격자는 _이번_ 요청의 결과만 얻을 수 있고,
                  키 자체로 영구 위조 불가
```

| Step | 누가 | 무엇을 | 의미 |
|---|---|---|---|
| ① | 공격자 (S-EL1 권한) | 마스터 키 직접 read 시도 | TrustZone 권한이지만 enclave 와는 별도 |
| ② | OP-TEE Mailbox driver | mbox_write 명령 | enclave 와의 _유일한_ 통신 경로 |
| ③ | Enclave processor | 인증 토큰 검증 | 토큰 = OEM-provisioned key 로 서명 — TrustZone 에 없음 |
| ④ | Crypto Accelerator | key_box[idx] 를 _내부 wire_ 로만 전달, 결과만 외부 출력 | 키가 시스템 버스에 노출되지 않음 |
| ⑤ | OP-TEE | 결과만 받음 | 공격자는 key 가 아닌 _이번 결과_ 만 얻음 |

```c
// Step ② 의 Mailbox 요청 (OP-TEE 측)
struct enclave_msg req = {
    .op       = ENCLAVE_OP_SIGN,    // 서명 요청 (키 직접 read 금지)
    .key_idx  = MASTER_KEY_IDX,
    .data     = {0xDE, 0xAD, ...},
    .auth_tag = compute_auth_tag(...),  // 정상 캐시된 토큰이 없으면 0
};
mbox_send(&req);
mbox_recv(&resp);
/* resp.status == ENCLAVE_ERR_AUTH (공격자가 정상 토큰 못 만듦) */
```

!!! note "여기서 잡아야 할 두 가지"
    **(1) TrustZone 이 100% 장악돼도 enclave 의 키는 살아남음** — 키가 enclave 의 _내부 wire_ 와 _전용 SRAM_ 밖으로 절대 나가지 않기 때문. 외부에 나가는 건 _결과_ 뿐. <br>
    **(2) 공격자는 _이번 요청_ 의 결과를 받을 수 있어도 키 자체로 위조 불가** — 영구 손상 vs 일시 도용의 차이가 enclave 의 본질적 가치.

---

## 4. 일반화 — TEE 계층 과 상호 불신 (Mutually Distrusting) 모델

### 4.1 TEE 다층 계층

Module 01 의 두 World (S/NS) 만으로는 부족했습니다. 실제 SoC 는 **여러 TEE 가 보안 레벨이 다른 채로 공존** 합니다.

```
   ┌─────────────────────────────────────┐
   │           REE (Rich EE)             │  ← 보안 레벨 최하
   │  일반 OS (Linux, Android)           │     NS-EL0/NS-EL1
   └─────────────────────────────────────┘
                    │
   ┌─────────────────────────────────────┐
   │       Non-secure EL2 (Hypervisor)   │  ← VM 간 격리
   │  가상 머신 관리, VM별 리소스 분리    │     여전히 Non-secure
   └─────────────────────────────────────┘
                    │
   ┌─────────────────────────────────────┐
   │       Secure (TrustZone)            │  ← CPU 기반 TEE
   │  Trusted OS + Trusted Applications  │     S-EL0/S-EL1
   │  키 관리, 인증, FW 검증             │     (Module 01-02 범위)
   └─────────────────────────────────────┘
                    │
   ╔═════════════════════════════════════╗
   ║    Secure Enclave (SoC Internal)    ║  ← SoC 내 최고 보안
   ║  전용 프로세서 + 전용 RAM            ║     CPU 클러스터와 독립
   ║  Key Box + Crypto Accelerator       ║
   ╚═════════════════════════════════════╝
                    │
   ╔═════════════════════════════════════╗
   ║    Secure Enclave (External IC)     ║  ← 물리적 분리
   ║  별도 보안 칩 (SPI 연결)             ║     Private Storage
   ║  사용자 비밀/프라이버시 저장          ║     최상위 Root of Trust
   ╚═════════════════════════════════════╝
```

### 4.2 ARM EL 과의 매핑 (Module 01 복습 + 확장)

```
         Non-secure                    Secure
      ┌──────────────────┐    ┌──────────────────┐
EL0   │  AArch64 App     │    │  Trusted Services │
      ├──────────────────┤    ├──────────────────┤
EL1   │  AArch64 Kernel  │    │  Trusted OS       │
      ├──────────────────┤    ├──────────────────┤
EL2   │  Hypervisor      │    │  Trusted Partition│  ← Secure EL2
      │                  │    │  Manager*         │    (ARMv8.4-A~)
      ├──────────────────┴────┴──────────────────┤
EL3   │         Firmware / Secure Monitor         │  ← 양쪽 전환 담당
      └──────────────────────────────────────────┘

  ※ Secure Enclave는 이 EL 체계 밖에 존재
    → CPU와 별개의 전용 프로세서에서 독립 실행
    → ARM EL이 아닌 자체 실행 모드
```

### 4.3 상호 불신 (Mutually Distrusting) 의 정의와 효과

!!! note "정의 (ISO 11179)"
    **Mutually Distrusting Trust Domains**: 동일 SoC/시스템 내 두 보안 도메인이 서로를 _신뢰 없는 외부_ 로 간주하고, 모든 통신에 대해 _독립적인 인증/암호화/검증_ 을 강제하는 보안 모델.

| 관계 | 위협 시나리오 | 상호 불신의 효과 |
|------|-------------|---------------|
| TrustZone → Enclave | Trusted OS 에 RCE 취약점 → Secure World 전체 장악 | Enclave 는 TrustZone 요청도 Mailbox + 인증 토큰으로만 수용 |
| Enclave → TrustZone | Enclave FW 버그로 잘못된 응답 반환 | TrustZone 은 Enclave 응답의 무결성을 독립 검증 |
| Internal ↔ External | External IC 가 물리적으로 교체/변조될 수 있음 | Secure Channel Protocol (SPI 위에 암호화 + MAC) |

→ 보안 부팅의 Chain of Trust 에서 "BL2 가 BL3 를 검증하듯" 각 TEE 가 상대방을 검증하는 구조.

---

## 5. 디테일 — Internal/External Enclave, DRM Pipeline, Mailbox, Secure Channel

### 5.1 Module 02 와의 관계

```
Module 02 에서 다룬 것:
  TrustZone 격리를 SoC HW가 강제하는 메커니즘
  → TZPC(APB 주변장치), TZASC(DRAM 영역), SMMU(DMA), GIC(인터럽트), Cache NS-bit

이 모듈에서 다루는 것:
  TrustZone 너머의 보안 계층 — Secure Enclave
  → TrustZone과 별개의 독립 실행 환경
  → 다층 TEE 구조에서의 상호 불신 관계
  → TEE의 실제 활용 사례 (DRM Protected Media Pipeline)
```

### 5.2 왜 TrustZone 만으로는 부족한가? — 한계 4 가지

| TrustZone 한계 | 원인 | 결과 |
|---------------|------|------|
| **Trusted OS 취약점** | Secure World 도 복잡한 OS 를 실행 (OP-TEE 등) | Trusted OS 가 뚫리면 Secure World 전체 컴프로마이즈 |
| **CPU/캐시 공유** | Secure 와 Non-secure 가 동일 CPU 코어 사용 | 캐시 부채널 공격 (Spectre 계열) 노출 |
| **컨텍스트 스위칭 오버헤드** | SMC 로 월드 전환 시 레지스터 저장/복원 | 빈번한 보안 연산에 성능 저하 |
| **공격 표면** | Trusted App 이 많아질수록 S-EL0 코드 증가 | 더 많은 공격 진입점 |

### 5.3 Secure Enclave 구조

```
┌─────────────────────────────────────────┐
│            SoC                           │
│                                         │
│  ┌───────────────────┐                  │
│  │ CPU Cluster        │                  │
│  │ (TrustZone 포함)   │                  │
│  │ NS-EL0/1/2, S-EL0/1│                  │
│  └────────┬───────────┘                  │
│           │                              │
│  ═════════╪═══ System Interconnect ══════│═
│           │                              │
│  ┌────────┴───────────────────────────┐  │
│  │ Internal Secure Enclave             │  │
│  │                                     │  │
│  │  ┌──────────┐  ┌────────────────┐  │  │
│  │  │Processor │  │ Private RAM    │  │  │  ← 전용 프로세서 + 전용 메모리
│  │  │(자체 ISA)│  │ (SRAM, 수 KB~) │  │  │     시스템 DRAM 사용 안 함
│  │  └──────────┘  └────────────────┘  │  │
│  │  ┌──────────┐  ┌────────────────┐  │  │
│  │  │Key Box   │  │Crypto Accel    │  │  │  ← 전용 HW 암호 엔진
│  │  │(키 저장) │  │(AES/RSA/ECC)   │  │  │     키가 버스에 노출 안 됨
│  │  └──────────┘  └────────────────┘  │  │
│  │  ┌──────────┐  ┌────────────────┐  │  │
│  │  │Mailbox   │  │ DMA            │  │  │  ← 외부 통신은 Mailbox로만
│  │  │(APB)     │  │                │  │  │
│  │  └──────────┘  └────────────────┘  │  │
│  └─────────────────────────────────────┘  │
│           │                              │
│           │ SPI (Secure Channel)         │
│           v                              │
│  ┌─────────────────────────┐  ┌───────┐ │
│  │ External Secure Enclave │──│Storage│ │  ← 별도 IC
│  │ (보안 칩)                │  │       │ │     Root of Trust
│  └─────────────────────────┘  └───────┘ │
└─────────────────────────────────────────┘
```

### 5.4 Internal vs External Secure Enclave

| | Internal Secure Enclave | External Secure Enclave |
|--|------------------------|------------------------|
| **위치** | SoC 내부 (on-die) | 별도 IC (SPI/I2C 연결) |
| **프로세서** | 전용 코어 (경량, 자체 ISA) | 자체 프로세서 |
| **메모리** | 전용 SRAM (수 KB ~ 수십 KB) | 자체 NVM + SRAM |
| **핵심 역할** | Key Box, Crypto Accelerator | Root of Trust, Private Storage |
| **부팅 주체** | 더 상위 보안 TEE 가 부팅 | 자체 BootROM (자립 부팅) |
| **물리 공격 저항** | SoC die 내부 → decapping 필요 | 별도 칩 → 독립적 anti-tamper |
| **대표 구현** | Apple SEP, Samsung SSP | TPM, NXP SE050, Infineon SLE97 |

### 5.5 핵심: TrustZone 과 Secure Enclave 의 상호 불신

```
                    ┌─────────────┐
                    │  TrustZone  │
                    │  (Secure    │
                    │   World)    │
                    └──────┬──────┘
                           │
                    서로 신뢰하지 않음
                    (mutually distrusting)
                           │
              ┌────────────┴────────────┐
              │                         │
     ┌────────┴────────┐     ┌─────────┴────────┐
     │ Internal Secure  │     │ External Secure   │
     │ Enclave          │     │ Enclave           │
     └─────────────────┘     └──────────────────┘
```

### 5.6 Module 02 개념과의 매핑

Module 02 에서 배운 HW 인프라가 Secure Enclave 에서도 동일하게 적용됩니다:

| Module 02 HW 인프라 | Secure Enclave 에서의 적용 |
|-----------------|-------------------------|
| **TZASC** (DRAM 영역 보호) | Enclave 전용 메모리 리전 → TZASC 가 TrustZone 접근도 차단하도록 설정 가능 |
| **SMMU** (DMA 접근 제어) | Enclave DMA 의 SMMU 설정은 Enclave 자체가 관리 → 외부 변경 불가 |
| **Cache NS-bit** | Enclave 메모리는 캐시 불가 (Non-cacheable) 로 설정하거나, 전용 캐시 사용 |
| **GIC** | Enclave 인터럽트 → Group 0 (EL3) 또는 Enclave 전용 IRQ |
| **TZPC** | Enclave 의 Mailbox/APB 레지스터 → 적절한 보안 레벨만 접근 |

### 5.7 Processing Element 의 보안 원칙

Secure Enclave 내부의 Processing Element (전용 프로세서) 가 외부와 통신할 때:

```
  Processing Element → 외부 메모리 기록 시:
  
  ┌─────────────────────────────────┐
  │ Enclave Processing Element      │
  │                                 │
  │  비밀 데이터 (평문)              │
  │       │                         │
  │       v                         │
  │  Crypto Accelerator             │  ← 내부에서 암호화 후
  │       │                         │
  │       v                         │
  │  AXI Master (AxPROT=Secure)     │  ← 암호화된 데이터만 외부로
  └────────┬────────────────────────┘
           │ 암호문만 DRAM에 기록
           v
        [DRAM]  ← 물리 덤프해도 평문 없음

  ※ 비밀 데이터가 버스/DRAM에 평문으로 절대 노출되지 않음
     → DRAM Protector + 암호화의 이중 방어
```

### 5.8 TEE 활용 사례: DRM Protected Media Pipeline

DRM (Digital Rights Management) 은 TEE 의 가장 직관적인 활용 사례. **복호화된 컨텐츠가 Non-secure World 에 절대 노출되지 않아야** 합니다.

#### ARM TZMP (TrustZone Multimedia Play) 흐름

```
┌─────────────┐   ┌──────────────┐   ┌──────────────────────────────────────┐
│ Non-secure  │   │   Secure     │   │       Protected Media Pipeline       │
│ World       │   │   World      │   │       (Secure 전용 HW 파이프라인)     │
│             │   │              │   │                                      │
│ ┌─────────┐ │   │ ┌──────────┐│   │ ┌──────┐ ┌────────┐ ┌────────────┐  │
│ │Encrypted│─┼──►│ │ Decrypt  ││──►│ │Decode│→│Picture │→│  Display   │──►Panel/
│ │Stream   │ │   │ │          ││   │ │      │ │Quality │ │  Engine    │  HDMI
│ └─────────┘ │   │ └──────────┘│   │ └──────┘ └────────┘ └────────────┘  │
│             │   │              │   │                                      │
│ ┌─────────┐ │   │              │   │  ※ 파이프라인의 모든 버퍼 메모리가   │
│ │Metadata │─┼─ ─┼─ ─ ─ ─ ─ ─ ─┼──►│    TZASC에 의해 Secure 전용으로 보호 │
│ └─────────┘ │   │              │   │    Non-secure 접근 시 DECERR         │
│             │   │              │   │                                      │
│ ┌─────────┐ │   │              │   │  Display Engine도 Secure Master로    │
│ │  OSD    │─┼─ ─┼─ ─ ─ ─ ─ ─ ─┼──►│  설정 → HDMI까지 보안 체인 유지     │
│ └─────────┘ │   │              │   │                                      │
└─────────────┘   └──────────────┘   └──────────────────────────────────────┘
```

#### HW 보안 인프라의 역할 (Module 02 연결)

| 단계 | 보호 메커니즘 | Module 02 대응 |
|------|-------------|------------|
| 복호화 키 저장 | Secure Enclave Key Box | — (이 모듈 신규) |
| 복호화 실행 | TrustZone Secure World | S-EL1 TEE OS |
| 복호화된 스트림 메모리 | TZASC Secure Region | Module 02 TZASC |
| 비디오 디코더 DMA | SMMU Secure Stream | Module 02 SMMU |
| 캐시된 비디오 데이터 | Cache NS-bit | Module 02 Cache NS-bit |
| Display Engine 접근 | TZPC Secure Peripheral | Module 02 TZPC |

#### TEE 없이 DRM 을 하면?

```
TEE 미적용:

  Encrypted Stream → [SW Decrypt in Normal World] → 메모리에 평문!
                                                          │
                                                    루트 권한 획득 시
                                                    /dev/mem로 평문 추출 가능

TEE 적용:

  Encrypted Stream → [Secure World Decrypt] → [TZASC Secure Region]
                                                      │
                                               Non-secure 접근 → DECERR
                                               메모리 덤프 → 평문 없음
                                               Display까지 Secure 파이프라인
```

#### SoC 보안과의 연결

DRM Pipeline 은 다음과 동일한 원리를 공유합니다:

| DRM 시나리오 | SoC 보안 대응 |
|-------------|-------------|
| 복호화된 영상이 메모리에 평문 노출 | Secure Boot 에서 복호화된 FW 가 SRAM 에만 존재하는 것과 동일 |
| Display 까지 보안 파이프라인 유지 | Chain of Trust 에서 BL1→BL33 까지 검증 체인 유지와 동일 |
| 복호화 키를 Enclave 에 저장 | ROTPK 를 OTP 에 저장하는 것과 동일 원리 |

### 5.9 Secure Channel Protocol — External Enclave 와의 통신

External Secure Enclave 는 SPI/I2C 같은 외부 버스로 SoC 와 연결됩니다. PCB 트레이스를 거치므로 _물리적 도청 / 변조 / IC 교체_ 가 가능 → Secure Channel Protocol 이 필수.

```
   SoC                                     External Secure IC
   ──────                                   ───────────────────
   Internal SE  ── encrypted + MAC ──→     External SE
                ←── encrypted + MAC ──

   - 암호화: AES-CCM/GCM (도청 차단)
   - 인증: CMAC/HMAC (변조/IC 교체 감지)
   - Freshness: 세션 키 + 시퀀스 번호 (재전송 차단)
   - 상호 인증: 양쪽이 서로의 정체를 검증
```

이것은 차량 보안의 SecOC (CAN 메시지에 MAC + Freshness) 와 동일한 원리를 물리 인터페이스 레벨에 적용한 것.

---

## 6. 흔한 오해 와 DV 디버그 체크리스트

### 흔한 오해

!!! danger "❓ 오해 1 — 'TEE = SGX / SEV 와 동일'"
    **실제**: TEE 는 _ARM TrustZone 기반_, SGX 는 _Intel enclave_ (runtime 격리 + memory 암호화), SEV 는 _AMD VM 단위 암호화_ — 카테고리가 다릅니다. 모델/위협/검증 방법이 모두 다릅니다.<br>
    **왜 헷갈리는가**: "보안 enclave" 라는 generic 용어가 다른 model 들 모두를 포괄해서.

!!! danger "❓ 오해 2 — 'TrustZone 이 뚫리면 enclave 도 끝'"
    **실제**: 두 도메인이 _상호 불신_ 으로 설계됐기 때문에, TrustZone 의 RCE 가 enclave 의 키를 자동으로 노출시키지 않습니다. enclave 는 mailbox 요청을 _인증 토큰_ 으로 검증, 키는 enclave 외부로 나가지 않음.<br>
    **왜 헷갈리는가**: "보안 도메인 = 신뢰 체인" 이라는 직관 (실제는 _불신 체인_).

!!! danger "❓ 오해 3 — 'Internal enclave 면 외부 enclave 는 불필요'"
    **실제**: 두 enclave 는 _다른 위협 모델_ 을 다룹니다. Internal 은 SW 공격 / 캐시 부채널 방어, External 은 _물리적 IC 교체 / decapping_ 방어. 각각이 독립적 anti-tamper 를 제공.<br>
    **왜 헷갈리는가**: "보안 칩이 두 개면 중복" 같은 인상.

!!! danger "❓ 오해 4 — 'Mailbox 면 자동으로 안전'"
    **실제**: Mailbox 는 _통신 경로_ 일 뿐. 인증 토큰 검증, replay 방어 (sequence number), TOCTOU 방어 (copy-then-validate) 가 모두 enclave FW 책임입니다. mailbox 가 있다고 보안이 끝난 게 아닙니다.<br>
    **왜 헷갈리는가**: "전용 채널 = 신뢰 가능" 이라는 직관.

!!! danger "❓ 오해 5 — 'External enclave 의 SPI 통신은 IC-to-IC 라 안전'"
    **실제**: SPI 는 PCB 트레이스에서 _오실로스코프 / 로직 분석기로 도청_ 가능, 물리 변조도 가능. Secure Channel Protocol (암호화 + MAC + sequence + 상호 인증) 없이는 평문 도청 / replay / IC 교체 모두 가능.<br>
    **왜 헷갈리는가**: "보드 안 = 안전" 이라는 인상.

### DV 디버그 체크리스트 (Enclave + DRM 검증에서 자주 보는 실패)

| 증상 | 1차 의심 | 어디 보나 |
|---|---|---|
| TZ RCE 시뮬에서 enclave key 가 그대로 노출 | enclave mailbox 의 인증 토큰 검증이 disable | enclave FW 의 token verify 코드 + DV stimulus |
| DRM 복호화 후 NS world 가 평문 video buffer read | TZASC region 이 NS-accessible 로 잘못 설정 | TZASC region register dump + access map |
| Enclave Mailbox 가 응답 안 함 (timeout) | Mailbox IRQ 가 GIC Group 1NS 로 잘못 라우팅 | GICD_IGROUPRn + enclave IRQ id |
| External SPI 통신 중간에 SoC 가 비정상 응답 수용 | Secure Channel Protocol 의 sequence number 검증 누락 | enclave FW 의 SPI 메시지 검증 코드 |
| Display Engine 이 NS DMA 로 동작 | TZPC 가 display peripheral 을 NS 로 분류 | TZPC slave 분류 표 |
| Cache flush 후에도 secure data 가 NS 캐시에서 hit | cache controller 의 NS tag bit 가 비활성 | cache line dump + NS tag column |
| Spectre PoC 가 secure key 를 추출 | enclave 와 무관 (CPU 부채널) → constant-time 코드 + speculation barrier | 의심 가는 secure crypto 코드의 timing analysis |
| TOCTOU: shared buffer 의 ptr 변조로 secure 메모리 read | secure 측 input sanitization 누락 | TA 의 pointer validation + bounce buffer 사용 |

---

## 7. 핵심 정리 (Key Takeaways)

- **TrustZone 한계**: CPU/cache/DRAM 공유 → side-channel (Spectre/Meltdown), Trusted OS 취약점, 자원 경합 latency.
- **Secure Enclave**: 별도 processor + 전용 RAM + 전용 crypto engine → 물리적 격리. Side-channel 차단.
- **주요 사례**: Apple SEP (T-series chip), Samsung Knox vault, Google Titan M (Pixel), AWS Nitro.
- **Mutually distrusting**: TrustZone 과 Enclave 는 서로 신뢰 안 함 — Mailbox + 인증 토큰 + Secure Channel Protocol 로만 통신.
- **TEE 계층**: OP-TEE / Trusty (TrustZone TEE OS) → Knox (Samsung) → SEP (Apple) — 각 layer 가 독립 보호. DRM, biometric, payment 의 _마스터 비밀_ 은 enclave 에 보관.

!!! warning "실무 주의점"
    - Enclave key 는 enclave _밖으로 나간 적이 없어야_ — DV 시 mailbox 응답에 raw key 가 등장하면 _즉시 fail_.
    - DRM Pipeline 은 5 축 (TZPC + TZASC + SMMU + GIC + cache NS-bit) 이 _모두_ 정확해야 — 한 축의 misconfig 가 곧 전체 무력화.
    - External enclave 와의 SPI 통신에서 Secure Channel Protocol (암호화 + MAC + sequence) 이 빠지면, 보드 도청만으로 키 탈취 가능.

---

## 다음 모듈

→ [Module 03 — Secure Boot Connection](03_secure_boot_connection.md): TrustZone / Enclave 의 _존재 자체_ 가 부팅 시점에 어떻게 establish 되는가. Chain of Trust + ROTPK + Anti-Rollback + Measured Boot.

[퀴즈 풀어보기 →](quiz/02a_secure_enclave_and_tee_hierarchy_quiz.md)

<div class="chapter-nav">
  <a class="nav-prev" href="../02_world_switch_soc_infra/">
    <div class="nav-label">◀ 이전</div>
    <div class="nav-title">보안 상태 전환 & SoC 보안 인프라</div>
  </a>
  <a class="nav-next" href="../03_secure_boot_connection/">
    <div class="nav-label">다음 ▶</div>
    <div class="nav-title">Secure Boot에서의 보안 레벨 적용</div>
  </a>
</div>


--8<-- "abbreviations.md"
