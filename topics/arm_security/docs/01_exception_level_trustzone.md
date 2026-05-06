# Unit 1: Exception Level & TrustZone

<div class="learning-meta">
  <span class="meta-badge meta-level-advanced">📊 Advanced</span>
</div>

## 핵심 개념
**ARM의 보안은 두 축으로 구성: (1) Exception Level (EL0~EL3) — 권한의 수직적 계층. (2) TrustZone (Secure/Non-Secure) — 월드의 수평적 분리. 이 두 축의 조합이 ARM SoC의 전체 보안 모델을 형성.**

---

## Exception Level (EL0 ~ EL3)

```
권한 높음
  ^
  |
EL3 ─── Secure Monitor (ATF/BL31, BootROM/BL1)
  |      - 최고 권한, Secure/Non-Secure 전환 관리
  |      - SMC (Secure Monitor Call)로 진입
  |      - 항상 Secure 상태
  |
EL2 ─── Hypervisor
  |      - VM (Virtual Machine) 관리
  |      - Secure EL2 (ARMv8.4+): Secure 가상화
  |      - Non-Secure EL2: 일반 가상화 (KVM 등)
  |
EL1 ─── OS Kernel
  |      - Secure EL1: TEE OS (OP-TEE, Trusty)
  |      - Non-Secure EL1: 일반 OS (Linux, Android)
  |
EL0 ─── Application
         - Secure EL0: Trusted App (결제, DRM, 생체)
         - Non-Secure EL0: 일반 앱
```

### 각 EL의 핵심 역할

| EL | 대표 SW | 핵심 권한 | Secure Boot 연결 |
|---|---------|----------|-----------------|
| **EL3** | ATF (BL31), **BootROM (BL1)** | 모든 시스템 레지스터 접근, 보안 상태 전환 | BL1이 EL3에서 실행 — 최초 신뢰점 |
| **EL2** | Hypervisor (KVM) | Stage 2 Translation, VM 격리 | BL33(U-Boot)이 EL2로 진입 가능 |
| **S-EL1** | OP-TEE, Trusty | Secure 메모리/디바이스 접근 | BL32가 S-EL1에서 실행 |
| **NS-EL1** | Linux, Android | 일반 커널 | OS가 NS-EL1에서 실행 |
| **S-EL0** | Trusted App | TEE 내 앱 격리 | 결제, DRM, 생체인증 |
| **NS-EL0** | 일반 앱 | 최소 권한 | 사용자 앱 |

---

## TrustZone — Secure / Non-Secure 분리

### 왜 두 개의 "월드"가 필요한가?

```
문제: 일반 OS가 해킹되면?
  → OS 커널 권한 탈취 → 모든 메모리/디바이스 접근 가능
  → 결제 정보, 암호 키, 생체 데이터 노출

TrustZone 해결:
  Secure World (TEE)          Normal World
  +-------------------+      +-------------------+
  | 결제 처리          |      | 일반 앱           |
  | 암호 키 저장       |      | 브라우저          |
  | 생체 인증          |      | 게임              |
  | DRM 복호화         |      | OS (Linux)        |
  +-------------------+      +-------------------+
         ↑ HW 격리                  ↑
         |                          |
  Normal World에서 Secure World 메모리 접근 불가 (HW 강제)
  → OS가 해킹되어도 Secure World의 키/데이터는 안전
```

### TrustZone의 HW 격리 메커니즘

```
모든 버스 트랜잭션에 NS (Non-Secure) 비트 추가:

  +--------+    +------+-------+------+
  | Master | →  | NS=0 | ADDR  | DATA |  Secure 접근
  +--------+    +------+-------+------+
                | NS=1 | ADDR  | DATA |  Non-Secure 접근
                +------+-------+------+

  NS=0 (Secure): Secure 메모리/디바이스 접근 가능
  NS=1 (Non-Secure): Secure 영역 접근 시 → 버스 에러 (차단)

  → NS 비트는 HW가 강제 — SW로 조작 불가능
  → EL3 (Secure Monitor)만 NS 비트를 변경할 수 있음
```

### SCR_EL3 (Secure Configuration Register)

```
EL3에서 제어하는 핵심 보안 레지스터:

  SCR_EL3.NS  (bit[0]): 0=Secure, 1=Non-Secure
    → EL3가 하위 EL의 보안 상태를 결정

  SCR_EL3.IRQ (bit[1]): IRQ를 EL3로 라우팅
  SCR_EL3.FIQ (bit[2]): FIQ를 EL3로 라우팅
  SCR_EL3.SMD (bit[7]): SMC 명령 비활성화
  SCR_EL3.HCE (bit[8]): EL2 활성화
  SCR_EL3.RW  (bit[10]): 하위 EL의 AArch64/32 선택

  BootROM (EL3)이 SCR_EL3를 설정하여 보안 정책을 결정
  → BL2로 점프할 때 NS=0 (Secure) 유지
  → BL33으로 점프할 때 NS=1 (Non-Secure) 전환
```

---

## EL 전환 메커니즘 — 어떻게 EL을 오르내리는가?

### 전환 명령어

```
상향 전환 (Lower EL → Higher EL): Exception 발생
  EL0 → EL1:  SVC (Supervisor Call)    — 시스템 콜
  EL1 → EL2:  HVC (Hypervisor Call)    — Hypervisor 서비스 요청
  Any → EL3:  SMC (Secure Monitor Call) — 보안 서비스 / 월드 전환

  그 외 Exception:
    IRQ/FIQ:  GIC 설정에 따라 EL1/EL2/EL3로 라우팅
    Data Abort, Instruction Abort:  현재 EL 또는 상위 EL
    SError:  비동기 에러 → 설정에 따라 EL3까지 가능

하향 전환 (Higher EL → Lower EL): ERET 명령
  ERET:  Exception Return
    → SPSR_ELn에서 복귀할 EL과 PSTATE 복원
    → ELR_ELn에서 복귀 주소(PC) 복원
    → 항상 같은 EL이거나 더 낮은 EL로만 복귀 가능

주의: SW가 임의로 EL을 올릴 수 없음 — 반드시 Exception 경유
      → 이것이 보안의 핵심: 권한 상승은 HW가 통제
```

### Exception 발생 시 HW가 자동으로 하는 일

```
Exception 발생 (예: SMC 실행):
  ┌──────────────────────────────────────────────────┐
  │ 1. PSTATE → SPSR_EL3 (현재 프로세서 상태 저장)    │
  │ 2. 복귀 주소 → ELR_EL3 (돌아올 PC 저장)           │
  │ 3. PSTATE 변경:                                   │
  │    - PSTATE.EL = EL3 (EL 상승)                    │
  │    - PSTATE.SP = 1 (SP_EL3 사용)                  │
  │    - PSTATE.DAIF = 1111 (인터럽트 마스킹)          │
  │ 4. PC = VBAR_EL3 + offset (벡터 테이블로 점프)     │
  └──────────────────────────────────────────────────┘

ERET 실행 (복귀):
  ┌──────────────────────────────────────────────────┐
  │ 1. SPSR_EL3 → PSTATE (상태 복원, EL 포함)         │
  │ 2. ELR_EL3 → PC (복귀 주소로 점프)                │
  │ → 자동으로 하위 EL로 복귀됨                        │
  └──────────────────────────────────────────────────┘

핵심: SPSR/ELR은 해당 EL에서만 접근 가능
  → EL1은 SPSR_EL1만, EL3는 SPSR_EL3만
  → 하위 EL이 상위 EL의 복귀 상태를 조작할 수 없음
```

### Exception Vector Table (VBAR_ELn)

```
각 EL은 자신만의 벡터 테이블을 가짐:
  VBAR_EL1: EL1의 벡터 테이블 기준 주소
  VBAR_EL2: EL2의 벡터 테이블 기준 주소
  VBAR_EL3: EL3의 벡터 테이블 기준 주소

벡터 테이블 구조 (각 엔트리 = 128 bytes = 32 명령어):
  ┌────────────┬────────┬────────┬────────┬────────┐
  │            │ Sync   │ IRQ    │ FIQ    │ SError │
  ├────────────┼────────┼────────┼────────┼────────┤
  │ Current EL │ +0x000 │ +0x080 │ +0x100 │ +0x180 │
  │  SP_EL0    │        │        │        │        │
  ├────────────┼────────┼────────┼────────┼────────┤
  │ Current EL │ +0x200 │ +0x280 │ +0x300 │ +0x380 │
  │  SP_ELx    │        │        │        │        │
  ├────────────┼────────┼────────┼────────┼────────┤
  │ Lower EL   │ +0x400 │ +0x480 │ +0x500 │ +0x580 │
  │  AArch64   │        │        │        │        │
  ├────────────┼────────┼────────┼────────┼────────┤
  │ Lower EL   │ +0x600 │ +0x680 │ +0x700 │ +0x780 │
  │  AArch32   │        │        │        │        │
  └────────────┴────────┴────────┴────────┴────────┘

  예: NS-EL1에서 SMC 실행 → EL3 진입
    → VBAR_EL3 + 0x400 (Lower EL, AArch64, Sync)
    → 여기에 ATF의 SMC 핸들러 코드가 위치

  예: EL0에서 SVC 실행 → EL1 진입
    → VBAR_EL1 + 0x400 (Lower EL, AArch64, Sync)
    → 여기에 OS의 시스템 콜 핸들러가 위치

  BootROM은 VBAR_EL3을 설정하여 EL3 벡터를 등록
```

### 전환 흐름 종합 예시

```
사용자 앱이 결제 요청하는 전체 경로:

  NS-EL0 (앱)
    │  SVC #0 (시스템 콜)
    ▼
  NS-EL1 (Linux Kernel)
    │  optee_driver: SMC #0 실행
    ▼
  EL3 (ATF/BL31)  ← VBAR_EL3 + 0x400
    │  1. NS 컨텍스트 저장
    │  2. SCR_EL3.NS = 0
    │  3. S 컨텍스트 복원
    │  4. ERET → S-EL1
    ▼
  S-EL1 (OP-TEE)
    │  결제 TA 호출
    ▼
  S-EL0 (결제 Trusted App)
    │  결제 처리 완료
    ▼
  S-EL1 → EL3 → NS-EL1 → NS-EL0 (역순 복귀)

  총 EL 전환: 6회 (상향 3 + 하향 3)
```

---

## EL별 메모리 번역 체계 (Translation Regime)

### 왜 EL마다 별도의 페이지 테이블이 필요한가?

```
문제: 모든 EL이 같은 페이지 테이블을 쓴다면?
  → EL0(앱)이 EL1(OS)의 페이지 테이블 매핑을 볼 수 있음
  → 악의적 EL1이 EL2의 메모리를 매핑할 수 있음

해결: 각 EL이 독립된 Translation Regime을 가짐
  → 상위 EL이 하위 EL의 주소 공간을 통제
  → 하위 EL은 자신의 번역 결과만 볼 수 있음
```

### EL별 Translation Regime

```
+-------+-------------------+--------------------------------------+
| EL    | 레지스터           | 용도                                  |
+-------+-------------------+--------------------------------------+
| EL0/1 | TTBR0_EL1         | 유저 공간 (하위 주소, 앱별 매핑)       |
|       | TTBR1_EL1         | 커널 공간 (상위 주소, 공유)            |
|       | TCR_EL1           | 번역 제어 (granule, 범위 등)          |
+-------+-------------------+--------------------------------------+
| EL2   | TTBR0_EL2         | Hypervisor 자체 매핑                  |
|       | VTTBR_EL2         | Stage 2 번역 (VM의 IPA→PA)           |
|       | VTCR_EL2          | Stage 2 번역 제어                    |
+-------+-------------------+--------------------------------------+
| EL3   | TTBR0_EL3         | Secure Monitor 매핑                  |
|       | TCR_EL3           | EL3 번역 제어                        |
+-------+-------------------+--------------------------------------+
```

### Stage 1 vs Stage 2 Translation (EL2의 핵심)

```
EL2가 없을 때 (베어메탈):
  VA ──Stage 1──→ PA
  (가상 주소)       (물리 주소)

EL2가 있을 때 (가상화):
  VA ──Stage 1──→ IPA ──Stage 2──→ PA
  (가상 주소)       (중간 물리 주소)    (물리 주소)

  Stage 1: Guest OS(EL1)가 관리 — VM 내부 매핑
  Stage 2: Hypervisor(EL2)가 관리 — VM 간 격리

  왜 2단계인가?
    → Guest OS는 자신이 물리 메모리를 직접 관리한다고 "착각"
    → 실제로는 Hypervisor가 Stage 2로 물리 메모리를 격리
    → VM-A가 VM-B의 메모리에 접근 불가 (Stage 2가 차단)
    → 이것이 VM 탈출(VM Escape) 공격을 막는 HW 기반 방어

  TrustZone과의 결합:
    Stage 2 테이블에도 NS 속성 존재
    → Hypervisor가 VM에 Secure 메모리를 매핑하는 것 자체를 차단
    → EL2도 NS 상태이면 Secure PA 매핑 불가
```

---

## EL3가 항상 Secure인 이유

```
EL3 = Secure Monitor = 보안 월드 전환의 유일한 게이트

  Non-Secure World                    Secure World
  +------------------+              +------------------+
  | NS-EL1 (Linux)   |              | S-EL1 (OP-TEE)  |
  |                   |   SMC 호출   |                  |
  |   결제 요청 ------+------→ EL3 →-+--- 결제 처리     |
  |                   |   결과 반환   |                  |
  |   결과 수신 ←-----+------← EL3 ←-+--- 결과 반환     |
  +------------------+              +------------------+

  EL3가 Non-Secure가 될 수 있다면?
    → Normal World에서 EL3를 장악 → 보안 전환 조작 가능
    → TrustZone 전체 무력화

  따라서 EL3는 항상 Secure — ARM 아키텍처 수준에서 강제
```

---

## Secure EL2 (ARMv8.4+) — Secure 가상화

```
ARMv8.4 이전:
  Secure World에는 Hypervisor 없음
  → Secure OS (S-EL1)가 하나만 존재
  → 복수의 TEE를 격리할 수 없음
  → 하나의 TEE가 전체 Secure 메모리 접근 가능 → 보안 위험

ARMv8.4+:
  Secure EL2 추가
  → Secure Hypervisor가 복수의 Secure Partition(SP)을 격리
  → FF-A (Firmware Framework for Arm) 표준으로 통신

  +-----+-----+-----+       +----------+
  | SP0 | SP1 | SP2 |       | NS-VM    |
  |(TEE)|(DRM)|(...) |       | (Linux)  |
  +-----+-----+-----+       +----------+
        |                         |
  +-----+-----+           +------+------+
  | S-EL2     |           | NS-EL2     |
  | (Secure   |           | (KVM)      |
  |  Partition|           |            |
  |  Manager) |           |            |
  +-----------+           +------------+
        |                         |
  +-----+-------------------------+-----+
  |              EL3 (Monitor)          |
  +-------------------------------------+
```

### FF-A (Firmware Framework for Arm) — Secure Partition 통신 표준

```
문제: SP끼리, 또는 Normal World↔SP 간 통신 방법이 필요
  기존: SMC로 EL3 경유 → 오버헤드 크고, 표준 없음

FF-A 해결:
  표준화된 메시지 전달 인터페이스
  → 메시지 기반 통신 (Direct / Indirect)
  → 메모리 공유 프로토콜 (Lend, Share, Donate)
  → Partition Discovery (어떤 SP가 존재하는지 조회)

  통신 유형:
    Direct Message:  호출자 → SPM → 대상 SP (동기, 즉시 응답)
    Indirect Message: Shared Memory에 메시지 저장 → 알림 (비동기)

  메모리 공유:
    FFA_MEM_SHARE: 메모리를 양쪽에서 접근 가능 (공유)
    FFA_MEM_LEND:  메모리를 빌려줌 (빌려준 쪽은 접근 불가)
    FFA_MEM_DONATE: 메모리 소유권 완전 이전

SPM (Secure Partition Manager):
  S-EL2에서 실행되는 Secure Hypervisor
  → 각 SP를 S-EL0 또는 S-EL1에서 격리 실행
  → Stage 2 Translation으로 SP 간 메모리 격리
  → Reference 구현: Hafnium (Google 오픈소스)

  Hafnium 역할:
    - SP 로드 및 초기화
    - FF-A 메시지 라우팅
    - SP 간 메모리 격리 (Stage 2)
    - SP 스케줄링
```

---

## Q&A

**Q: Exception Level이 4개인 이유는?**
> "각 레벨이 다른 보안/격리 요구를 충족한다: EL0(앱 격리 — 앱끼리 접근 불가), EL1(OS 커널 — 하드웨어 직접 관리), EL2(Hypervisor — VM 격리), EL3(Secure Monitor — 보안 월드 전환). 레벨이 적으면 격리가 부족하고, 많으면 HW 복잡도가 불필요하게 증가한다. 4개가 실용적 균형이다."

**Q: TrustZone의 HW 격리는 어떻게 동작하는가?**
> "모든 버스 트랜잭션에 NS(Non-Secure) 비트가 HW적으로 추가된다. NS=1인 트랜잭션은 Secure 영역 접근 시 버스 에러로 차단된다. 이 NS 비트는 EL3만 변경할 수 있으며, SW로는 조작이 불가능하다. 따라서 일반 OS가 해킹되어도 Secure World의 메모리/디바이스에 접근할 수 없다."

**Q: BootROM이 EL3에서 동작하는 이유는?**
> "BootROM은 시스템의 최초 신뢰점(Root of Trust)이므로, 가장 높은 권한(EL3)에서 실행되어야 한다. EL3에서만 (1) 보안 상태(Secure/Non-Secure)를 설정할 수 있고, (2) 보안 레지스터(SCR_EL3 등)를 초기화할 수 있으며, (3) 이후 단계(BL2)의 보안 레벨을 결정할 수 있다. 더 낮은 EL에서는 이러한 보안 초기화가 불가능하다."

**Q: EL 전환 시 HW가 자동으로 하는 일은?**
> "상향 전환(Exception) 시 HW가 자동으로 (1) 현재 PSTATE를 SPSR_ELn에 저장, (2) 복귀 주소를 ELR_ELn에 저장, (3) PSTATE를 변경(EL 상승, 인터럽트 마스킹), (4) PC를 VBAR_ELn + offset으로 설정하여 벡터 핸들러로 점프한다. 하향 전환(ERET) 시에는 SPSR_ELn에서 PSTATE를 복원하고 ELR_ELn에서 PC를 복원한다. 핵심은 SPSR/ELR이 해당 EL에서만 접근 가능하므로, 하위 EL이 상위 EL의 복귀 상태를 조작할 수 없다는 점이다."

**Q: Stage 2 Translation이 왜 필요한가?**
> "VM 격리를 위해서다. Guest OS(EL1)는 Stage 1으로 VA→IPA 번역을 자체 관리하지만, IPA가 실제 물리 주소가 아니다. Hypervisor(EL2)가 Stage 2로 IPA→PA 번역을 관리하여, 각 VM이 다른 VM의 물리 메모리에 접근하지 못하도록 격리한다. Guest OS는 자신이 물리 메모리를 직접 관리한다고 '착각'하지만, 실제로는 Hypervisor가 Stage 2 테이블로 모든 메모리 접근을 통제한다. 이것이 VM Escape 공격을 HW 수준에서 막는 메커니즘이다."

---

## 확인 문제

**문제 1: EL 전환 경로 추적**
> 사용자 앱(NS-EL0)이 Secure World의 암호화 서비스를 호출하려 한다. 이때 거치는 EL 전환 경로를 순서대로 나열하고, 각 단계에서 사용되는 명령어(SVC/HVC/SMC/ERET)를 명시하라.

<details>
<summary>풀이 과정</summary>

**사고 과정:**
1. NS-EL0(앱)은 직접 SMC를 호출할 수 없다 — EL0에서는 SVC만 가능
2. SVC로 NS-EL1(OS 커널)에 진입 → 커널의 TEE 드라이버가 SMC 호출
3. SMC로 EL3(Secure Monitor) 진입 → 컨텍스트 전환
4. ERET으로 S-EL1(OP-TEE) 진입 → TA 호출
5. 반환은 역순

**정답:**
```
NS-EL0 ──SVC──→ NS-EL1 ──SMC──→ EL3 ──ERET──→ S-EL1 ──(TA 처리)
S-EL1 ──SMC──→ EL3 ──ERET──→ NS-EL1 ──ERET──→ NS-EL0
```

**핵심 포인트:**
- EL0에서는 SVC만 사용 가능 (SMC는 EL1 이상에서만)
- 월드 전환은 반드시 EL3 경유 — 직접 NS-EL1→S-EL1 전환 불가
- 각 ERET 시 HW가 SPSR에서 복귀할 EL을 결정
</details>

**문제 2: VBAR 오프셋 계산**
> Linux 커널(NS-EL1, AArch64)에서 SMC #0을 실행했을 때, CPU가 점프하는 벡터 테이블 주소는 VBAR_EL3 + 얼마인가? 이유도 설명하라.

<details>
<summary>풀이 과정</summary>

**사고 과정:**
1. SMC는 Synchronous Exception이다
2. NS-EL1은 EL3 입장에서 "Lower EL"이다
3. NS-EL1이 AArch64 모드이다
4. 벡터 테이블에서 해당 위치를 찾는다:
   - Lower EL, AArch64, Synchronous = +0x400

**정답:** `VBAR_EL3 + 0x400`

**벡터 테이블에서의 위치:**
```
Lower EL (AArch64) 행:
  Sync: +0x400  ← SMC는 여기
  IRQ:  +0x480
  FIQ:  +0x500
  SError: +0x580
```

**핵심 포인트:**
- "Lower EL"은 Exception을 발생시킨 EL이 타겟 EL보다 낮다는 의미
- AArch64/AArch32 구분이 있는 이유: 호출자의 실행 모드에 따라 컨텍스트 저장 방식이 다름
</details>

**문제 3: Stage 2 Translation 시나리오**
> VM-A(Guest Linux)가 물리 주소 0x8000_0000에 쓰기를 시도한다. 이 주소는 실제로 VM-B에 할당된 물리 메모리다. (1) 이 접근이 차단되는 과정을 Stage 1/Stage 2 번역 흐름으로 설명하고, (2) 만약 Stage 2가 없다면 어떤 보안 문제가 발생하는지 설명하라.

<details>
<summary>풀이 과정</summary>

**사고 과정:**
1. VM-A의 Guest OS는 VA를 관리하고 Stage 1 번역으로 IPA를 생성한다
2. VM-A가 "물리 주소 0x8000_0000"이라고 생각하는 것은 실제로 IPA이다
3. Hypervisor의 Stage 2 테이블이 이 IPA를 실제 PA로 번역한다
4. VM-A의 Stage 2 테이블에 0x8000_0000 매핑이 없으면 → Abort

**(1) 차단 과정:**
```
VM-A 내부:
  VA (0xFFFF_0000) ──Stage 1──→ IPA (0x8000_0000)
    Stage 1은 VM-A의 Guest OS가 관리 — 여기까지는 성공

Hypervisor Stage 2:
  IPA (0x8000_0000) ──Stage 2──→ ???
    VM-A의 Stage 2 테이블에 IPA 0x8000_0000 매핑이 없음!
    → Stage 2 Translation Fault 발생
    → Hypervisor(EL2)로 Exception 전달
    → Hypervisor가 잘못된 접근으로 판단, VM-A에 에러 주입
```

**(2) Stage 2 없으면:**
- Guest OS가 물리 주소를 직접 지정 가능
- VM-A가 VM-B의 메모리를 읽고/쓸 수 있음
- VM Escape: 악성 Guest가 호스트 메모리까지 접근 가능
- Hypervisor의 격리 보장이 SW 수준에 의존 → 취약점 하나로 전체 무력화
</details>

<div class="chapter-nav">
  <a class="nav-prev" href="../">
    <div class="nav-label">◀ 이전</div>
    <div class="nav-title">코스 홈</div>
  </a>
  <a class="nav-next" href="../02_world_switch_soc_infra/">
    <div class="nav-label">다음 ▶</div>
    <div class="nav-title">보안 상태 전환 & SoC 보안 인프라</div>
  </a>
</div>
