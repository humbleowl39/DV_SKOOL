# Module 03 — Secure Boot Connection

<!-- DV-SKOOL-CH-CTX:start -->
<div class="chapter-context" data-cat="soc">
  <a class="chapter-back" href="../">
    <span class="chapter-back-arrow">←</span>
    <span class="chapter-back-icon">🛡️</span>
    <span class="chapter-back-text">ARM Security</span>
  </a>
  <span class="chapter-divider">›</span>
  <span class="chapter-marker">Module 03</span>
</div>
<!-- DV-SKOOL-CH-CTX:end -->

<!-- DV-SKOOL-CH-TOC:start -->
<div class="page-toc">
  <span class="page-toc-label">목차</span>
  <a class="page-toc-link" href="#1-why-care-이-모듈이-왜-필요한가">1. Why care?</a>
  <a class="page-toc-link" href="#2-intuition-비유와-한-장-그림">2. Intuition</a>
  <a class="page-toc-link" href="#3-작은-예-부팅-중-bl31-에서-bl33-으로-넘어갈-때-단-한-cycle-동안-일어나는-일">3. 작은 예 — BL31 → BL33 의 NS=0→1 한 cycle</a>
  <a class="page-toc-link" href="#4-일반화-boot-stage-별-el-ns-매트릭스-와-2-개의-검증-축">4. 일반화 — Boot stage 매트릭스 + 2 축</a>
  <a class="page-toc-link" href="#5-디테일-bl1-2-31-33-anti-rollback-measured-boot-dv-시나리오">5. 디테일</a>
  <a class="page-toc-link" href="#6-흔한-오해-와-dv-디버그-체크리스트">6. 흔한 오해 + DV 디버그 체크리스트</a>
  <a class="page-toc-link" href="#7-핵심-정리-key-takeaways">7. 핵심 정리</a>
</div>
<!-- DV-SKOOL-CH-TOC:end -->

!!! objective "학습 목표"
    이 모듈을 마치면:

    - **Trace** Secure Boot 단계와 ARM EL 의 매핑 (BL1=EL3, BL2=S-EL1, BL31=EL3 secure monitor 상주, BL33=NS-EL1/EL2) 을 추적할 수 있다.
    - **Apply** Secure World 자원 (TZPC/TZASC/GIC/SMMU 보안 설정) 이 어느 boot 단계에서 활성화되는지 적용할 수 있다.
    - **Identify** Boot 시 TZASC, TZPC, GIC 보안 설정의 책임 단계와 lock-down 시점을 식별할 수 있다.
    - **Distinguish** Verified Boot (서명 검증) 와 Architecture Enforcement (EL/TrustZone) 의 보완 관계를 구분할 수 있다.
    - **Justify** Anti-Rollback OTP counter 가 EL3 + TZPC 와 어떻게 결합돼야 의미 있는지 설명할 수 있다.

!!! info "사전 지식"
    - [Module 01 — Exception Level & TrustZone](01_exception_level_trustzone.md)
    - [Module 02 — World Switch & SoC Security Infra](02_world_switch_soc_infra.md)
    - [Module 02A — Secure Enclave & TEE Hierarchy](02a_secure_enclave_and_tee_hierarchy.md)
    - 일반 부팅 흐름 (BootROM → 1st-stage → kernel)

---

## 1. Why care? — 이 모듈이 왜 필요한가

Module 01-02A 에서 말한 _"NS bit 격리, EL3 단일 게이트, TZASC/TZPC/GIC/SMMU 의 5 축"_ 이 **언제부터 작동하는가?** 에 답이 없습니다. 답은 _부팅 시점_ — BL1 (BootROM, EL3) 이 모든 보안 인프라를 _초기화_ 하고, BL31 → BL33 전환 시점에 _NS=1_ 로 toggle 한 후부터입니다.

이 모듈을 건너뛰면 디버그 시 _"NS world 에서 secure 자원이 access 되는데 분명 TZASC 는 잠갔는데 왜?"_ 같은 상황을 만납니다 — 답은 보통 **lock-down 이 BL31 ERET 직전에 끝나지 않았기 때문**. 부팅 단계와 lock-down 시점을 정확히 알면, 첫 secure access 의 timing 만 보고도 어느 BL 단계에 문제가 있는지 좁힐 수 있습니다.

---

## 2. Intuition — 비유와 한 장 그림

!!! tip "💡 한 줄 비유"
    **Secure Boot ↔ ARM Security** ≈ _건물 입주 검수 (Secure Boot) + 입주 후 보안실 (TrustZone)_.<br>
    Boot 시 Chain of Trust 가 _"누가 입주해도 되는가"_ 를 확정하고 (서명 검증), runtime 의 TrustZone 이 _"입주민이 어떤 방을 쓸 수 있는가"_ 를 격리. 둘이 짝 — 검수 없이 입주만 막아도 공허하고, 검수만 통과시키고 격리 안 하면 한 입주민이 다른 방까지 다 봅니다.

### 한 장 그림 — Boot stage 의 EL × NS 진행

```
   시간 ─────────────────────────────────────────────────────────────────►

   Stage:   BL1            BL2            BL31              BL32           BL33           Linux
            (BootROM)      (FSBL)         (Monitor)         (TEE)          (U-Boot)
   EL:      EL3            S-EL1          EL3 상주           S-EL1          NS-EL1/EL2     NS-EL1
   NS:      Secure         Secure         Secure             Secure         Non-Secure ⭐  Non-Secure
   하는 일:  HW init        BL3x load      runtime monitor    TEE OS         정상 OS load   사용자
            서명 검증      서명 검증      SMC handler        TA 관리        kernel 진입
            TZPC/TZASC      DRAM init                       ↑
            /GIC/SMMU                                       │
            초기 설정                                        │
            ↓                                                │
            Lock-down 시작 ─────────────────────────────────┘
                                                            ▲
                                          ⭐ 핵심 전환점: SCR_EL3.NS = 0 → 1
                                            이 시점부터 5 축의 보안 인프라가
                                            _실제로 차단_ 동작
```

### 왜 이렇게 설계됐는가 — Design rationale

세 가지 요구가 동시에 풀려야 했습니다.

1. **첫 명령어부터 신뢰의 root 가 있어야 한다** → BootROM (mask-ROM, 위변조 불가) 이 EL3 (최고 권한) 에서 시작 → 이후 단계의 _누구를_ 실행할지 결정.
2. **각 단계가 다음 단계를 검증해야 한다 (Chain of Trust)** → BL1 이 BL2 서명 검증, BL2 가 BL31/BL32/BL33 서명 검증, 한 단계라도 실패면 abort.
3. **검증된 image 라도 _최신_ 이어야 한다 (Anti-Rollback)** → 서명만 보면 v1.0 의 취약점도 다시 booting 가능 → OTP monotonic counter 가 _"version 이 충분히 높은가"_ 를 추가 검증.

이 세 요구의 교집합이 곧 **Verified Boot (서명) + Architecture Enforcement (EL/NS) + Anti-Rollback (OTP counter)** 의 3 메커니즘 결합입니다.

---

## 3. 작은 예 — 부팅 중 BL31 에서 BL33 으로 넘어갈 때, 단 한 cycle 동안 일어나는 일

가장 critical 한 시나리오. BL31 (EL3, Secure) 에서 BL33 (NS-EL1) 으로 ERET 하는 _그 한 cycle_ 에 무엇이 일어나는지. 이 한 cycle 직전까지 모든 secure 인프라가 lock-down 돼 있어야 하고, 한 cycle 후부터는 모든 NS access 가 차단돼야 합니다.

```
   Cycle:   t-3        t-2        t-1        t         t+1        t+2
   ─────────────────────────────────────────────────────────────────────►

   BL31 코드:
   t-3:  TZPC slave 분류 완료 (OTP=Secure, UART=NS, ...)
   t-2:  TZASC region 0 = Secure DRAM lock, region 1 = NS DRAM
   t-1:  GIC group 0/1S/1NS 분류 완료, GICD_CTLR enable
         SPSR_EL3 ← NS-EL1h, ELR_EL3 ← BL33 entry
         x0 = device tree blob ptr
   t:    SCR_EL3.NS = 1 set
         ┌─ 이 cycle 부터:
         │  - 모든 outgoing AxPROT[1] = 1
         │  - TZASC 가 secure region 의 NS access 차단 시작
         │  - TZPC 가 secure-only slave 의 NS access 차단 시작
         │  - GIC group 0/1S 가 NS write 무시 (RAZ/WI)
         └─ ERET 명령 (SPSR_EL3 → PSTATE, ELR_EL3 → PC, EL3→NS-EL1)
   t+1:  PC = BL33 entry, PSTATE.EL = 1, NS = 1
         BL33 첫 instruction 실행 (보통 zeroization 또는 console init)
   t+2:  BL33 가 secure DRAM read 시도 시 → TZASC DECERR
```

| Cycle | 누가 | 무엇을 | 의미 |
|---|---|---|---|
| t-3 | BL31 | TZPC 의 secure-only slave list 완성 | NS access 차단의 구체화 |
| t-2 | BL31 | TZASC region register set + lock | 이후 변경 금지 (SoC 마다 register 가 LOCK bit 또는 OTP 기반) |
| t-1 | BL31 | GIC group 분류 + SPSR/ELR 설정 | ERET 직전 준비 |
| **t** | EL3 HW | **SCR_EL3.NS ← 1**, ERET | _이 cycle_ 이 architecture 전체의 turning point |
| t+1 | BL33 | NS world 첫 instruction | 보안 인프라가 모두 작동 중 |
| t+2 | BL33 (오류 시도) | secure DRAM read → DECERR | TZASC 가 정확히 차단 |

```c
// BL31 의 마지막 부분 (개념 코드)
void bl31_to_bl33_transition(void) {
    /* t-3..t-2: 보안 인프라 final lock-down */
    tzpc_lockdown();        // OTP, Crypto = Secure-only
    tzasc_lockdown();       // Secure DRAM region locked
    gic_secure_lockdown();  // Group 0/1S configured

    /* t-1: ERET 준비 */
    write_spsr_el3(NS_EL1H_AARCH64);  // SPSR_EL3.M, .RW, .DAIF
    write_elr_el3(bl33_entrypoint);
    set_gpr(0, dtb_pa);

    /* t: NS=1 toggle + ERET (한 instruction sequence) */
    asm volatile(
        "msr scr_el3, %0  \n"   // SCR_EL3.NS = 1
        "isb              \n"   // 새 NS attribute propagation
        "eret             \n"   // ERET to BL33 (NS-EL1)
        :: "r"(scr_el3_with_ns_set)
    );
}
```

!!! note "여기서 잡아야 할 두 가지"
    **(1) Lock-down 은 ERET 이전에 _완료_ 돼야 한다.** ERET 후 BL33 은 NS world 인 채로 first instruction 을 실행하므로, 그 전에 모든 secure 인프라가 차단 모드여야 합니다. _한 cycle_ 의 misorder 가 곧 race window. <br>
    **(2) `MSR SCR_EL3, ...` 직후 `ISB` 가 필수** — instruction barrier 없이는 outgoing transaction 의 NS attribute 가 새 값으로 보장되지 않습니다.

---

## 4. 일반화 — Boot stage 별 EL/NS 매트릭스 와 2 개의 검증 축

### 4.1 Boot Stage 별 EL/NS 매트릭스

```
+------------------------------------------------------------------+
| Stage | EL  | S/NS | 왜 이 레벨인가?                              |
+-------+-----+------+---------------------------------------------+
| BL1   | EL3 | S    | 최초 보안 설정(TZPC/TZASC/SCR) 권한 필요     |
|       |     |      | 다음 단계의 EL과 보안 상태를 결정해야 함      |
+-------+-----+------+---------------------------------------------+
| BL2   | S-EL1| S   | DRAM 초기화에 EL3 권한 불필요                |
|       |     |      | Secure 유지: BL3x를 Secure 메모리에 로드      |
+-------+-----+------+---------------------------------------------+
| BL31  | EL3 | S    | Secure Monitor 상주 — 런타임 월드 전환        |
|       |     |      | PSCI, SMC 처리에 EL3 필수                    |
+-------+-----+------+---------------------------------------------+
| BL32  | S-EL1| S   | TEE OS — Trusted App 관리                    |
|       |     |      | Secure 메모리/디바이스 접근 필요              |
+-------+-----+------+---------------------------------------------+
| BL33  | NS-EL1| NS | Normal 부트로더 — Secure 접근 불필요          |
|       | /EL2 |     | 이 시점에서 Secure 자원 접근 차단 시작        |
+-------+-----+------+---------------------------------------------+
| Linux | NS-EL1| NS | 일반 OS — 최소 권한 원칙                     |
+-------+-----+------+---------------------------------------------+
```

### 4.2 두 개의 검증 축

```
   축 1. Verified Boot (Chain of Trust, 서명)
   ──────────────────────────────────────────
   BL1 ──verifies──► BL2 ──verifies──► BL31 / BL32 / BL33
   (BootROM = mask-ROM, immutable trust root)

   축 2. Architecture Enforcement (EL × NS)
   ──────────────────────────────────────────
   BL1 (EL3/S) → BL2 (S-EL1) → BL31 (EL3/S 상주) → BL32 (S-EL1) → BL33 (NS-EL1)
   (각 단계의 EL/NS 가 권한 범위를 결정)

   ┌────────────────────────────────────────────────┐
   │  두 축은 _직교_ — 한 축만 있으면 결함:          │
   │  - 서명만: 검증된 BL32 가 NS world 에 안 가둠   │
   │     → S-EL1 코드의 의도치 않은 키 노출 가능     │
   │  - EL/NS 만: 악성 BL32 가 S-EL1 에 그대로 진입  │
   │     → Secure 자원 자유롭게 접근                  │
   │  → 둘 다 있어야 완전                             │
   └────────────────────────────────────────────────┘
```

이 두 축의 결합이 ARM 보안 부팅의 본질 — _"무엇을 실행하는가" (서명) × "어떤 권한으로" (EL/NS)_.

### 4.3 Anti-Rollback 의 자리

```
       Verified Boot (서명)              Anti-Rollback (OTP counter)
       ────────────────────              ─────────────────────────────
       "누가 만든 image 인가?"            "충분히 최신 version 인가?"

   서명 통과 + version 통과 → 부팅 OK
   서명 통과 + version 미달 → 부팅 ABORT (rollback 차단)
   서명 실패              → 부팅 ABORT (위변조 차단)

   둘이 같이 있어야 _과거의 정상 서명된 취약 version_ 으로 다운그레이드 불가.
```

---

## 5. 디테일 — BL1/2/31/33, Anti-Rollback, Measured Boot, DV 시나리오

### 5.1 BL1 → BL2 전환 상세

```
BL1 (BootROM, EL3):
  1. CPU Reset → PC가 BootROM 주소 → EL3 진입
  2. 보안 HW 초기화:
     - SCR_EL3 설정 (보안 정책)
     - TZPC 설정 (주변장치 보안)
     - TZASC 설정 (메모리 보안)
     - GIC 보안 설정
  3. BL2 서명 검증 (Secure Boot)
  4. BL2를 위한 환경 준비:
     - BL2 진입점 주소 설정
     - SPSR_EL3 설정 (BL2의 EL과 상태)
       SPSR_EL3.M = EL1h (S-EL1)
       SPSR_EL3.SS = Secure
     - SCR_EL3.NS = 0 유지 (Secure)
  5. ERET → S-EL1 (BL2 실행 시작)

핵심: BL1이 EL3 권한으로 SPSR/SCR을 설정하여
     BL2의 실행 EL과 보안 상태를 결정한다.
```

### 5.2 BL31 → BL33 전환 (핵심 보안 경계)

```
BL31 (Secure Monitor, EL3):
  1. BL33 (U-Boot) 진입점 확인
  2. Non-Secure 전환 준비:
     - SCR_EL3.NS = 1 (Non-Secure 전환!)
     - SCR_EL3.RW = 1 (AArch64)
     - SCR_EL3.HCE = 1 (EL2 활성화, 필요 시)
     - SPSR_EL3.M = EL2h 또는 EL1h
  3. ERET → NS-EL2 또는 NS-EL1

  이 순간 이후:
    BL33/Linux는 Secure 메모리 접근 불가 (TZASC 차단)
    BL33/Linux는 Secure 디바이스 접근 불가 (TZPC 차단)
    BL33/Linux는 EL3 레지스터 접근 불가
    → SMC로 EL3에 "요청"만 가능
```

### 5.3 Anti-Rollback — 버전 다운그레이드 방어

#### 롤백 공격이란?

```
시나리오:
  FW v1.0에 취약점 발견 → v2.0에서 패치
  공격자: v1.0 이미지를 Flash에 다시 기록
  → 서명은 유효함 (v1.0도 정상 서명된 이미지)
  → Secure Boot 통과!
  → 취약한 v1.0이 다시 실행 → 공격 성공

  Secure Boot만으로는 "이전 버전" 실행을 막을 수 없음
  → 서명 = "누가 만들었는가" 검증이지, "언제 만들었는가"는 아님
```

#### Monotonic Counter (Anti-Rollback Counter)

```
OTP (One-Time Programmable) 퓨즈에 단조 증가 카운터 저장:

  OTP Anti-Rollback Counter:
    +---+---+---+---+---+---+---+---+
    | 1 | 1 | 1 | 0 | 0 | 0 | 0 | 0 |  = 3 (3비트 blown)
    +---+---+---+---+---+---+---+---+
    → 한번 blow된 퓨즈는 되돌릴 수 없음 (단조 증가 보장)

  부팅 시 검증:
    1. BL1(EL3)이 BL2 이미지 헤더에서 version_number 읽기
    2. OTP에서 min_version 읽기 (EL3/Secure에서만 접근 가능)
    3. if (image_version < otp_min_version) → BOOT ABORT
    4. if (image_version > otp_min_version) → OTP 카운터 업데이트
    5. 서명 검증 진행

  FW 업데이트 시:
    v2.0 → v3.0 업데이트 성공 후
    OTP 카운터: 3 → 4 (퓨즈 하나 더 blow)
    → 이후 v2.0 이하 이미지는 부팅 불가

  보안 레벨 연결:
    → OTP는 TZPC에 의해 Secure Only — NS에서 카운터 변경 불가
    → 카운터 읽기/쓰기는 EL3(BootROM)에서만 수행
    → 공격자가 NS에서 OTP 카운터를 리셋하는 것은 물리적으로 불가능
```

### 5.4 Measured Boot & Remote Attestation

#### Secure Boot vs Measured Boot

```
Secure Boot:
  검증 실패 → 실행 차단 (Gate 역할)
  "이 코드를 실행해도 되는가?" → Yes/No
  결과: 부팅 성공 또는 실패

Measured Boot:
  각 단계를 측정(해시)하여 기록 (Observer 역할)
  "어떤 코드가 실행되었는가?" → 해시 값 기록
  결과: 항상 부팅, 나중에 측정값으로 무결성 판단

  둘은 배타적이 아님 — 함께 사용:
    Secure Boot로 기본 검증 + Measured Boot로 증명 기록
```

#### 측정 과정 (ARM PSA 관점)

```
Boot Stage별 측정:

  BL1 (BootROM, EL3):
    → BL1 자체는 ROM이므로 신뢰 (Immutable Root of Trust)
    → BL2 이미지의 해시 계산: H(BL2)
    → 측정값을 Secure 레지스터에 기록 (Platform Configuration)

  BL2:
    → BL31 해시 계산 → 기록: PCR = Hash(PCR_prev || H(BL31))
    → BL32 해시 계산 → 기록: PCR = Hash(PCR_prev || H(BL32))
    → BL33 해시 계산 → 기록: PCR = Hash(PCR_prev || H(BL33))

  측정값 체인:
    PCR_final = H(H(H(H(init) || H(BL2)) || H(BL31)) || H(BL32)) || H(BL33))
    → 어느 단계든 바뀌면 최종 PCR 값이 달라짐

  PCR (Platform Configuration Register):
    → TPM: 물리적 TPM 칩에 저장
    → ARM PSA: Secure World 내부 (EL3 또는 S-EL1)에 저장
    → fTPM: Firmware TPM (TEE 내에서 SW로 구현)
```

#### Remote Attestation

```
서버가 디바이스의 무결성을 원격으로 검증:

  디바이스                              서버
  +------------------+                +------------------+
  | 1. 부팅 (측정)    |                |                  |
  | 2. PCR 값 확정    |                | 3. Nonce 전송    |
  |                   | ←── Nonce ──── |                  |
  | 4. Attestation    |                |                  |
  |    Token 생성:    |                |                  |
  |    Sign(PCR+Nonce |                |                  |
  |    , DeviceKey)   |                |                  |
  |                   | ──→ Token ──→  | 5. Token 검증:   |
  |                   |                |    서명 확인      |
  |                   |                |    PCR 비교      |
  |                   |                |    → 신뢰 판단   |
  +------------------+                +------------------+

  활용 사례:
    DRM: 콘텐츠 서버가 디바이스 무결성 확인 후 키 전달
    기업 보안: MDM 서버가 단말 무결성 확인 후 접속 허용
    IoT: 클라우드가 디바이스 상태 확인 후 OTA 업데이트 배포

  보안 레벨 연결:
    → DeviceKey는 Secure World(EL3 또는 S-EL1)에서만 접근 가능
    → PCR 값은 Secure 메모리에 저장 — NS에서 변조 불가
    → Token 생성은 TEE 내부에서 수행
```

### 5.5 보안 레벨과 공격 방어의 연결

| 공격 | 보안 레벨 방어 | 메커니즘 |
|------|-------------|---------|
| OS 해킹 → 키 탈취 | TrustZone 격리 | NS에서 Secure 메모리 접근 불가 |
| DMA 공격 | TZASC + SMMU | NS DMA가 Secure DRAM 접근 차단 |
| JTAG 디버그 | EL3 + OTP | EL3에서 JTAG 비활성화, OTP로 영구 차단 |
| Privilege Escalation | EL 계층 | EL0→EL1은 Exception만, EL1→EL3은 SMC만 |
| 악성 부트로더 | Secure Boot + EL | 서명 실패 → 실행 차단, NS 전환 전에 검증 완료 |
| TEE 앱 간 격리 | S-EL0 + S-EL1 | TEE OS가 TA 간 메모리 격리 |
| VM 탈출 | EL2 | Stage 2 Translation으로 VM 간 격리 |
| FW 롤백 | OTP Counter + EL3 | Monotonic Counter를 EL3에서 관리, 이전 버전 차단 |
| 위장 디바이스 | Measured Boot + TEE | Remote Attestation으로 무결성 증명 |

#### 실제 공격 사례

```
(1) Nintendo Switch BootROM 취약점 (2018, "Fusée Gelée")
  공격: USB 복구 모드에서 BootROM의 DMA 버퍼 오버플로
    → BootROM(EL3) 코드 실행 권한 획득
    → TrustZone 설정 자체를 변경 가능 → 전체 보안 무력화
  교훈:
    → BootROM은 ROM이므로 패치 불가 — 하드웨어 리비전 필요
    → EL3 코드의 취약점 = 최고 수준 위험 (모든 보안 레벨 무력화)
    → DV 시사점: BootROM의 입력 검증 (USB, UART) 철저히 검증

(2) Qualcomm EDL (Emergency Download) 취약점 (2017~2020, 다수)
  공격: EDL 모드의 Firehose 프로그래머에서 인증 우회
    → Secure Boot 우회하여 임의 이미지 플래시
    → OTP 퓨즈 읽기까지 가능한 케이스도 존재
  교훈:
    → 복구/디버그 모드도 Secure Boot 체인에 포함해야 함
    → EDL 프로그래머의 서명 검증이 핵심
    → DV 시사점: 정상 부팅 경로뿐 아니라 복구 모드도 검증 대상

(3) ARM TrustZone 캐시 사이드 채널 (2017, "TruSpy")
  공격: Normal World에서 Flush+Reload로 Secure World 실행 패턴 관찰
    → NS-bit 태깅에도 불구하고, 타이밍 차이로 Secure 코드 실행 유추
    → AES 키 일부 비트 추출 성공
  교훈:
    → HW 격리가 타이밍 사이드 채널까지 완벽히 차단하지는 않음
    → Secure World 코드는 constant-time 구현 필요
    → DV 시사점: 실행 시간 일정성 (timing-invariant) 검증
```

### 5.6 DV 관점 — 보안 레벨 검증

#### 검증 시나리오 총괄

| # | 시나리오 | 검증 포인트 | 유형 |
|---|---------|-----------|------|
| 1 | BL1의 TZPC 초기 설정 | OTP, Crypto가 Secure Only로 설정되는가? | Positive |
| 2 | BL1의 TZASC 초기 설정 | Secure DRAM 영역이 올바르게 보호되는가? | Positive |
| 3 | BL1 → BL2 EL 전환 | SPSR_EL3가 S-EL1로 올바르게 설정되는가? | Positive |
| 4 | BL31 → BL33 NS 전환 | SCR_EL3.NS=1이 정확히 설정되는가? | Positive |
| 5 | NS에서 Secure 접근 시도 | 버스 에러 / 차단 발생하는가? | Negative |
| 6 | SMC 호출 정확성 | EL3 진입 → 서비스 처리 → 올바른 월드로 반환 | Positive |
| 7 | Anti-Rollback 검증 | 이전 버전 이미지 부팅 거부 | Negative |
| 8 | 전환 중간 상태 공격 | NS 전환 전 Secure 자원 접근 | Corner Case |
| 9 | 동시 SMC 멀티코어 | 다수 코어가 동시 SMC 호출 | Corner Case |

#### 검증 방법론 상세 — Stimulus → Check → Coverage

```
시나리오 4: BL31 → BL33 NS 전환 (핵심 보안 경계)

  Stimulus:
    - BL31 코드가 BL33 entry point를 설정하고 ERET 실행
    - 테스트는 BL31의 전환 시퀀스를 트리거

  Check:
    - SCR_EL3.NS가 정확히 1로 설정되었는가?
    - SPSR_EL3.M이 NS-EL1h 또는 NS-EL2h인가?
    - ERET 후 PC가 BL33 entry point인가?
    - ERET 후 CurrentEL이 EL1 또는 EL2인가?

  Coverage:
    - cp_scr_ns_transition: {0→1, 1→0} 전환 모두 커버
    - cp_spsr_target_el: {EL1h, EL2h} 모두 커버
    - cp_bl33_entry: entry point 주소 범위 커버

시나리오 5: NS에서 Secure 접근 시도 (Negative 테스트)

  Stimulus:
    - BL33(NS-EL1) 실행 중 Secure DRAM 주소에 Load/Store 발행
    - NS DMA Master가 Secure 영역에 접근 시도
    - NS에서 TZPC-protected 레지스터 접근 시도

  Check:
    - 접근 시 버스 에러(DECERR/SLVERR) 반환되는가?
    - Data Abort Exception 발생하는가?
    - Secure 메모리 내용이 NS에 노출되지 않는가? (읽기 값 = 0 or error)
    - 시스템이 정상 계속 동작하는가? (에러가 시스템 크래시를 유발하면 안 됨)

  Coverage:
    - cp_ns_secure_access: {DRAM, OTP, Crypto, GIC_Secure} 영역별
    - cp_access_type: {Read, Write}
    - cp_response: {DECERR, SLVERR, Data_Abort}

시나리오 7: Anti-Rollback 검증

  Stimulus:
    - OTP Counter = 3인 상태에서 version=2 이미지로 부팅 시도
    - OTP Counter = 3인 상태에서 version=3 이미지로 부팅 시도 (경계값)
    - OTP Counter = 3인 상태에서 version=4 이미지로 부팅 시도

  Check:
    - version < counter: 부팅 거부 (BOOT_ABORT)
    - version == counter: 부팅 성공, OTP 변경 없음
    - version > counter: 부팅 성공, OTP 카운터 업데이트

  Coverage:
    - cp_version_vs_counter: {below, equal, above}
    - cp_otp_update: {no_update, increment}
    - cp_boot_result: {abort, success}
```

#### SVA Assertion 예시

```systemverilog
// SCR_EL3.NS 전환 타이밍 검증
// NS 전환 전에 모든 Secure 초기화가 완료되었는지 확인

// TZPC 초기화 완료 전 NS 전환 금지
property p_tzpc_before_ns_switch;
  @(posedge clk) disable iff (!rst_n)
  $rose(scr_el3_ns) |-> tzpc_init_done;
endproperty
a_tzpc_before_ns: assert property (p_tzpc_before_ns_switch)
  else $error("NS switch before TZPC initialization!");

// TZASC 초기화 완료 전 NS 전환 금지
property p_tzasc_before_ns_switch;
  @(posedge clk) disable iff (!rst_n)
  $rose(scr_el3_ns) |-> tzasc_init_done;
endproperty
a_tzasc_before_ns: assert property (p_tzasc_before_ns_switch)
  else $error("NS switch before TZASC initialization!");

// NS 전환 후 Secure 메모리 접근 차단 확인
property p_ns_secure_access_blocked;
  @(posedge clk) disable iff (!rst_n)
  (scr_el3_ns && bus_req_valid && is_secure_addr(bus_req_addr))
  |-> ##[1:3] bus_resp_error;
endproperty
a_ns_blocked: assert property (p_ns_secure_access_blocked)
  else $error("NS access to Secure memory not blocked!");

// Anti-Rollback: 이전 버전 부팅 차단
property p_anti_rollback;
  @(posedge clk) disable iff (!rst_n)
  (image_version_valid && image_version < otp_min_version)
  |-> ##[1:$] boot_abort;
endproperty
a_anti_rollback: assert property (p_anti_rollback)
  else $error("Rollback image not rejected!");

// 각 assertion에 대응하는 cover property
c_ns_switch:     cover property (p_tzpc_before_ns_switch);
c_tzasc_switch:  cover property (p_tzasc_before_ns_switch);
c_ns_blocked:    cover property (p_ns_secure_access_blocked);
c_anti_rollback: cover property (p_anti_rollback);
```

---

## 6. 흔한 오해 와 DV 디버그 체크리스트

### 흔한 오해

!!! danger "❓ 오해 1 — 'Secure Boot 와 TrustZone 은 별개'"
    **실제**: Secure Boot 의 ROTPK (Root-Of-Trust Public Key) 가 TrustZone 의 root key derivation 의 source 입니다. Boot 단계의 실패 (e.g., BootROM 취약점) 는 곧 runtime TrustZone 의 무력화. 둘은 _같은 trust chain 의 다른 단계_.<br>
    **왜 헷갈리는가**: 이름이 다르니 독립 기능이라는 직관.

!!! danger "❓ 오해 2 — '서명만 통과하면 안전'"
    **실제**: 서명은 _누가 만든 image 인가_ 만 보장합니다. _언제 만들어진 (= 충분히 최신 인) image 인가_ 는 Anti-Rollback OTP counter 가 별도 검증. 둘 다 통과해야 안전.<br>
    **왜 헷갈리는가**: "서명 = 신뢰" 라는 단순화.

!!! danger "❓ 오해 3 — 'BL31 이 종료되면 EL3 도 사라진다'"
    **실제**: BL31 은 _상주_ 합니다. boot 가 완료된 후 (Linux 가 NS-EL1 에서 돌아가는 동안) 도 BL31 은 EL3 메모리에 살아 있고, SMC 가 발생할 때마다 깨어납니다. _런타임 SMC handler_ 가 본업.<br>
    **왜 헷갈리는가**: BL1/BL2 처럼 stage-bootloader 라는 이름 패턴 때문에.

!!! danger "❓ 오해 4 — 'BL33 가 부팅되면 더 이상 secure 자원 접근 시도 안 함'"
    **실제**: BL33 / Linux / Linux user app 모두 secure 자원에 access 시도할 수 있습니다 (의도적 시험, 취약점 exploit). DV 의 **negative test** 는 정확히 이 시나리오 — _NS 에서 secure 자원 접근 시 차단되는가_ 를 검증.<br>
    **왜 헷갈리는가**: "정상 코드는 시도 안 함" 이라는 가정.

!!! danger "❓ 오해 5 — 'OTP fuse 영역은 자동으로 secure'"
    **실제**: OTP 도 SoC 의 한 peripheral 이며, _TZPC slave 분류_ 에서 Secure-only 로 명시해야 안전. mirror register (OTP 의 shadow copy) 도 별도 region 으로 잠가야 합니다. 누락 시 NS world 에서 fuse 값 (root key 포함) 을 read 가능.<br>
    **왜 헷갈리는가**: "OTP = 보안 fuse = 자동 보호" 라는 인상.

### DV 디버그 체크리스트 (Boot 검증에서 자주 보는 실패)

| 증상 | 1차 의심 | 어디 보나 |
|---|---|---|
| BL31→BL33 직후 NS world 가 secure DRAM read 성공 | TZASC lock-down 이 ERET 직전에 미완료 | BL31 의 lockdown sequence 와 ERET 의 cycle-level 순서 |
| 부팅은 성공하는데 SMC 가 안 됨 | SCR_EL3.SMD 가 잘못 set (SMC disable) | SCR_EL3 dump |
| version=v1 정상 부팅, v3 후 다시 v1 도 부팅 됨 | OTP counter update 누락 (퓨즈 blow 안 함) | OTP write 코드 + 실제 fuse register dump |
| OTP fuse 의 root key 가 NS 에서 read 됨 | mirror register secure 분류 누락 | TZPC slave 표 + mirror address range |
| BL2 서명 실패해도 BL3 가 진행됨 | BL2 의 verify 결과 처리 (`if (!verify) abort`) 누락 | BL2 verify 코드 |
| ERET 후 EL 이 잘못됨 (EL3 그대로) | SPSR_EL3.M 잘못 (EL3h 로 set) | SPSR.M 디코드 + 의도된 target EL |
| Measured Boot PCR 이 매번 다름 | non-deterministic 데이터가 hash 입력에 포함 (e.g., 시간) | hash 입력 영역 + image header 의 measured area |
| Recovery / EDL 모드 진입 시 Secure Boot 우회 | 복구 모드의 별도 trust chain 미구현 | recovery entry point 의 verify 코드 |

---

!!! warning "실무 주의점 — ROM/HSM 키 fuse 가 NS world 에서 read 가능"
    **현상**: NS world 에서 OTP/eFuse mirror 레지스터를 읽었더니 root key 또는 HUK 가 그대로 노출된다.

    **원인**: 키가 저장된 fuse mirror 가 secure-only 영역으로 매핑되지 않아, TZPC/TZASC filter 가 해당 주소를 secure 로 lock 하지 못한다.

    **점검 포인트**: BL1/BL2 가 키 fuse 영역을 secure-only 로 잠그는지, 그리고 NS world 에서 해당 주소 read 시 BusError/zero 반환되는지 boot 직후 부정 시나리오로 검증.

## 7. 핵심 정리 (Key Takeaways)

- **두 메커니즘의 결합**: Verified Boot = "무엇을 실행하는가" (서명 검증), Architecture Enforcement = "어떤 권한으로" (EL + TrustZone). 둘 다 있어야 완전.
- **Boot ↔ EL 매핑**: BL1 (EL3/S, BootROM) → BL2 (S-EL1/S) → BL31 (EL3/S, _상주_) → BL32 (S-EL1/S) → BL33 (NS-EL1 또는 EL2/NS). 핵심 전환점은 BL31→BL33 의 NS=1 set.
- **보안 인프라 활성화 시점**: BL1/BL2 가 TZASC/TZPC/GIC/SMMU 설정. BL31 도달 시점에는 secure infra 가 모두 lock-down. ERET 직전에 lock-down 완료가 critical invariant.
- **EL3 = 영구 secure monitor**: BL31 이 boot 완료 후에도 EL3 에 영구 거주, runtime 의 SMC handler / world switch 처리.
- **Anti-Rollback + Measured Boot**: Verified Boot 만으로는 _과거의 정상 서명 취약 version_ 을 막을 수 없음 → OTP counter (롤백 차단) + PCR (원격 증명) 으로 보강.

!!! warning "실무 주의점"
    - BL31 의 lock-down 시퀀스 (TZPC → TZASC → GIC → SMMU 순서) 는 _ERET 직전에 모두 완료_ 돼야 합니다. SVA 로 `$rose(scr_el3_ns) |-> all_init_done` 강제.
    - OTP fuse 의 _mirror register_ 도 secure-only 로 잠가야 합니다 — 사내 실무 주의점 참조.
    - 복구 / EDL / JTAG 같은 _alternate boot path_ 도 동일한 trust chain 에 포함돼야 — 정상 path 만 검증하는 건 미완.

---

## 다음 모듈

→ [Module 04 — Quick Reference Card](04_quick_reference_card.md): 지금까지의 모든 모듈을 면접/디버그용 1 페이지 치트시트로 정리. EL × NS 매트릭스, world switch, 5 축 인프라, boot stage, anti-rollback 의 빠른 참조.

[퀴즈 풀어보기 →](quiz/03_secure_boot_connection_quiz.md)

<div class="chapter-nav">
  <a class="nav-prev" href="../02a_secure_enclave_and_tee_hierarchy/">
    <div class="nav-label">◀ 이전</div>
    <div class="nav-title">Unit 2A: Secure Enclave & TEE 계층 구조</div>
  </a>
  <a class="nav-next" href="../04_quick_reference_card/">
    <div class="nav-label">다음 ▶</div>
    <div class="nav-title">ARM Security Architecture — Quick Reference Card</div>
  </a>
</div>


--8<-- "abbreviations.md"
