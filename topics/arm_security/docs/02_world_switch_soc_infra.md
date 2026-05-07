# Module 02 — World Switch & SoC Security Infra

<div class="learning-meta">
  <span class="meta-badge meta-level-advanced">📊 Advanced</span>
</div>

!!! objective "학습 목표"
    이 모듈을 마치면:

    - **Trace** SMC instruction → EL3 secure monitor → world switch 흐름
    - **Apply** TZPC, TZASC, GIC의 secure/non-secure 분할 설정
    - **Implement** Context save/restore 흐름 (world 전환 시 register 격리)
    - **Identify** SoC peripheral의 보안 인프라 적용 위치

!!! info "사전 지식"
    - [Module 01](01_exception_level_trustzone.md)
    - GIC (Generic Interrupt Controller) 기본

!!! tip "💡 이해를 위한 비유"
    **World Switch** ≈ **보안 출입 절차 — 신청서(SMC) + 신원 확인 + 개인 소지품 보관(register save)**

    Normal World ↔ Secure World 전환 시 EL3 monitor 가 register / state 보관 후 다른 world 로 jump. 비싼 operation.

---

## 핵심 개념
**월드 전환은 반드시 EL3(Secure Monitor)을 경유해야 하며, SMC 명령으로만 가능. SoC 레벨에서는 TZPC, TZASC, GIC 보안 설정으로 버스/메모리/인터럽트를 Secure/Non-Secure로 분할하여 HW 격리를 완성.**

---

## SMC (Secure Monitor Call) — 월드 전환

### 전환 흐름

```
Normal World (NS-EL1)                    Secure World (S-EL1)
+-------------------+                   +-------------------+
| Linux Kernel      |                   | OP-TEE            |
|                   |                   |                   |
| TEE 호출 요청     |                   |                   |
|   SMC #0 실행 ----+--→ EL3 ←---------+                   |
|                   |    |              |                   |
|                   |    | 1. 컨텍스트 저장 (NS 레지스터)   |
|                   |    | 2. SCR_EL3.NS = 0 (Secure 전환) |
|                   |    | 3. 컨텍스트 복원 (S 레지스터)    |
|                   |    | 4. ERET → S-EL1                 |
|                   |    |              |                   |
|                   |    |              | TEE 처리 수행     |
|                   |    |              | 결과 준비         |
|                   |    |              | SMC 반환 --------→|
|                   |    |              |                   |
|                   |    | 1. 컨텍스트 저장 (S 레지스터)    |
|                   |    | 2. SCR_EL3.NS = 1 (NS 전환)     |
|                   |    | 3. 컨텍스트 복원 (NS 레지스터)   |
|                   |    | 4. ERET → NS-EL1                |
|                   |    |                                  |
| 결과 수신 ←-------+----+                                  |
+-------------------+                   +-------------------+
```

### SMC 호출 규약 (SMCCC)

```
ARM SMC Calling Convention:

  입력:
    X0: Function ID (어떤 서비스 요청인지)
    X1~X7: 파라미터

  Function ID 분류:
    [31]:    0=Fast Call(즉시 반환), 1=Yielding Call(비동기)
    [30]:    0=SMC32, 1=SMC64
    [29:24]: Service Range
              0x00~0x01: ARM Architecture
              0x02~0x0F: SiP (Silicon Provider) — 삼성, 퀄컴 등
              0x30~0x31: Trusted OS
              0x32~0x3F: Trusted App
    [15:0]:  Function Number

  반환:
    X0: 상태/결과
    X1~X3: 반환 데이터

  예: PSCI (Power State Coordination Interface)
    SMC #0, X0=0xC4000003 (CPU_ON) → EL3가 코어 전원 관리
```

---

## SoC 보안 인프라 — 버스/메모리/인터럽트 분할

### TZPC (TrustZone Protection Controller)

```
APB 주변장치를 Secure/Non-Secure로 분류:

  +--------+     +------+     +-----------+
  | Master | →   | TZPC | →   | APB Slave |
  +--------+     +------+     +-----------+

  TZPC 설정:
    Slave 0 (OTP):    Secure Only     ← NS 접근 차단
    Slave 1 (Timer):  Non-Secure OK   ← 양쪽 접근 가능
    Slave 2 (Crypto): Secure Only     ← NS 접근 차단
    Slave 3 (UART):   Non-Secure OK

  → BootROM(EL3)이 TZPC를 초기 설정
  → OTP, Crypto Engine은 Secure에서만 접근 가능
  → Normal World에서 OTP 접근 시도 → 버스 에러
```

### TZASC (TrustZone Address Space Controller)

```
DRAM 영역을 Secure/Non-Secure로 분할:

  DRAM 물리 주소 공간:
  +------------------------------------------+
  | 0x0000_0000 ~ 0x3FFF_FFFF: Secure DRAM   | ← TEE OS, 암호 키
  | (NS 접근 차단)                            |
  +------------------------------------------+
  | 0x4000_0000 ~ 0xFFFF_FFFF: NS DRAM       | ← Linux, 일반 앱
  | (양쪽 접근 가능)                           |
  +------------------------------------------+

  TZASC 레지스터로 영역별 보안 속성 설정:
    Region 0: Base=0x0, Size=1GB, Security=Secure
    Region 1: Base=0x4000_0000, Size=3GB, Security=Non-Secure

  → NS Master(DMA, GPU)가 Secure DRAM 접근 → TZASC가 차단
```

### GIC (Generic Interrupt Controller) 보안

```
인터럽트도 Secure/Non-Secure 분류:

  GIC 설정:
    IRQ 0~31 (SGI/PPI): 코어별
    IRQ 32~1019 (SPI): 공유

    각 IRQ에 Group 설정:
      Group 0 (Secure, FIQ): EL3로 라우팅
      Group 1 Secure: S-EL1로 라우팅
      Group 1 Non-Secure: NS-EL1로 라우팅

  보안 의미:
    Crypto Engine 완료 인터럽트 → Group 0 (Secure)
    → Normal World에서 이 인터럽트를 가로채거나 마스킹 불가
    
    Timer 인터럽트 → Group 1 NS
    → 일반 OS가 처리
```

### GICv3 구조 상세 (ARMv8 표준)

```
GICv3 = Distributor + Redistributor + CPU Interface

  +---------+     +----------------+     +---------------+
  | SPI     | →   | Distributor    | →   | Redistributor | → CPU Interface → Core
  | (공유)  |     | (GICD)         |     | (GICR, 코어별) |
  +---------+     +----------------+     +---------------+
                       ↑                       ↑
  +---------+          |               +---------+
  | LPI     | ─────────┘               | SGI/PPI |
  | (MSI)   |                          | (코어별) |
  +---------+                          +---------+

  Distributor (GICD):
    - SPI/LPI의 Group(0/1S/1NS) 설정
    - 우선순위, 라우팅 대상 코어 설정
    - NS에서 Secure 인터럽트의 Group/Priority 변경 불가
    - GICD_CTLR로 전체 인터럽트 Enable/Disable

  Redistributor (GICR):
    - 코어별 하나씩 존재
    - SGI/PPI 관리 (코어 로컬 인터럽트)
    - LPI pending 테이블 관리

  CPU Interface:
    - GICv3부터 System Register로 접근 (Memory-mapped 아님)
    - ICC_SRE_ELn: System Register Enable
    - ICC_IAR1_EL1: 인터럽트 Acknowledge
    - ICC_EOIR1_EL1: End of Interrupt
    - ICC_PMR_EL1: Priority Mask

  Affinity Routing (MPIDR 기반):
    - GICv3는 MPIDR(Affinity 0~3)로 코어를 식별
    - GICD_IROUTERn 레지스터로 SPI의 대상 코어 지정
    - 1:N (특정 코어) 또는 Any-of-N (아무 코어) 라우팅

  보안 분리:
    Group 0:  Secure (FIQ) → EL3
    Group 1S: Secure (IRQ) → S-EL1
    Group 1NS: Non-Secure (IRQ) → NS-EL1
    → NS에서 Group 0/1S 인터럽트의 설정 변경/마스킹 불가
    → Secure 인터럽트는 Normal World 실행 중에도 선점(preempt) 가능
```

### SMMU (System MMU) — DMA 접근 제어

```
문제: TZASC는 물리 주소 기반으로 DRAM을 보호하지만,
     DMA Master(GPU, DSP, 주변장치)는 주소 변환이 필요할 수 있음.
     또한 디바이스별 세밀한 접근 제어가 필요.

SMMU 해결:
  디바이스의 DMA 트랜잭션에 주소 변환 + 접근 제어 적용

  +-------+     +------+     +--------+
  | GPU   | →   | SMMU | →   | DRAM   |
  | (DMA) |     |      |     |        |
  +-------+     +------+     +--------+
  | DSP   | →   |      |
  +-------+     +------+

  동작 원리:
    1. DMA Master가 트랜잭션 발행 (VA 또는 IOVA)
    2. SMMU가 Stream ID로 디바이스 식별
       Stream ID = 어떤 Master가 보냈는지 (HW적으로 결정)
    3. Stream ID → Context 매핑:
       각 디바이스(Stream)에 독립된 페이지 테이블 할당
    4. Stage 1: IOVA → IPA (디바이스 드라이버가 설정)
       Stage 2: IPA → PA (Hypervisor가 설정)
    5. 접근 권한 검사: R/W/X + Secure/Non-Secure

  보안 역할:
    - NS DMA Master → Secure DRAM 접근 시도 → SMMU가 차단 (Fault)
    - 디바이스별 격리: GPU는 자기 할당 메모리만 접근 가능
    - VM 격리: VM-A의 디바이스가 VM-B 메모리 접근 불가

  TZASC vs SMMU 비교:
    ┌─────────┬──────────────────┬──────────────────────┐
    │         │ TZASC            │ SMMU                 │
    ├─────────┼──────────────────┼──────────────────────┤
    │ 보호 단위│ 물리 주소 영역    │ 디바이스(Stream)별    │
    │ 변환    │ 없음 (PA 기반)   │ VA/IOVA → PA 변환    │
    │ 세밀도  │ 영역(Region) 단위│ 페이지(4KB) 단위     │
    │ 디바이스 │ 모든 Master 공통  │ Master별 개별 정책   │
    │ 구현    │ 메모리 컨트롤러   │ 버스 중간에 위치     │
    └─────────┴──────────────────┴──────────────────────┘

    → 둘 다 필요: TZASC가 큰 영역 보호, SMMU가 디바이스별 세밀 제어
```

### Cache / TLB의 NS-bit 태깅

```
문제: CPU 캐시와 TLB는 Secure/Non-Secure 접근을 모두 캐싱.
     같은 물리 주소라도 S와 NS에서 다른 데이터를 가질 수 있음.
     → 구분하지 않으면 NS에서 Secure 데이터가 캐시 히트될 수 있음!

해결: 캐시 라인과 TLB 엔트리에 NS 비트를 태깅

  캐시 라인 구조:
    +----+------+------+------+
    | NS | TAG  | DATA | 상태 |
    +----+------+------+------+
    |  0 | 0x80 | key  | Valid|  ← Secure 접근의 캐시 라인
    |  1 | 0x80 | junk | Valid|  ← NS 접근의 캐시 라인 (같은 주소!)
    +----+------+------+------+

    → PA가 같아도 NS=0과 NS=1은 별도 캐시 엔트리
    → NS 접근은 NS=1 태그 라인만 히트
    → Secure 데이터가 NS 캐시 히트에 노출되지 않음

  TLB 엔트리:
    +----+------+------+------+--------+
    | NS | VA   | PA   | 속성 | VMID   |
    +----+------+------+------+--------+
    → 월드 전환 시 TLB flush 불필요 (NS 태그로 자동 분리)
    → 성능 이점: 월드 전환이 빈번해도 TLB 미스 최소화

  보안 의미:
    1. 캐시 사이드 채널 공격 완화:
       → NS에서 Secure 캐시 라인 접근 자체가 불가
       → Prime+Probe 공격의 난이도 증가
    2. 캐시 일관성 보장:
       → Secure World가 키를 변경해도 NS 캐시에 영향 없음
       → 역방향도 마찬가지: NS 공격자가 Secure 캐시 오염 불가
    3. 월드 전환 성능:
       → TLB/캐시 flush 없이 전환 가능 → SMC 오버헤드 감소

  주의: 완전한 방어는 아님
    → Spectre 계열 공격: 투기적 실행(speculative execution)으로
      NS에서 Secure 캐시 타이밍 차이를 관측 가능
    → 추가 HW 완화 필요 (speculation barrier 등)
```

### 월드 간 통신 메커니즘

```
Secure World와 Normal World는 격리되어 있지만 통신이 필요.
예: 일반 앱이 Secure World의 암호 서비스를 사용해야 할 때.

방법 1: SMC 레지스터 전달 (소량 데이터)
  → X0~X7 레지스터로 파라미터 전달 (최대 8×64bit = 64 bytes)
  → 간단한 요청/응답에 적합

방법 2: Shared Memory (대량 데이터)
  → 특정 메모리 영역을 양쪽에서 접근 가능하도록 설정
  → TZASC에서 해당 영역을 "NS-accessible" + "S-accessible"로 설정
  → 또는 Secure World가 일시적으로 NS 메모리를 읽기

  구조:
    +------------------------------------------+
    | Secure DRAM       | Shared Buffer | NS DRAM        |
    | (S-only)          | (양쪽 접근)    | (NS-only)      |
    +------------------------------------------+

  주의:
    → Shared Memory는 양쪽에서 접근 가능하므로 민감 데이터 금지
    → 무결성 검증 필요 (NS가 Shared Buffer를 변조할 수 있음)
    → TOCTOU 공격 주의: Secure가 검증 후 NS가 변조

방법 3: MHU (Message Handling Unit)
  → 전용 HW 메일박스
  → 한쪽이 메시지를 쓰면 상대방에게 인터럽트 발생
  → 레지스터 기반 — 메모리 공유 없이 통신 가능

  +----------+     +-----+     +----------+
  | Normal   | →   | MHU | →   | Secure   |
  | World    | ←   |     | ←   | World    |
  +----------+     +-----+     +----------+
                     ↕ IRQ

방법 4: FF-A (ARMv8.4+)
  → 표준화된 메시지 + 메모리 공유 프로토콜
  → SPM(S-EL2)이 라우팅 관리
  → 기존 SMC+Shared Memory의 표준화 버전
  (상세: Unit 1 Secure EL2 / FF-A 섹션 참조)
```

---

## Secure Boot에서 보안 레벨 변화 (요약)

```
(상세: Unit 3 참조)

  BL1(EL3/S) → BL2(S-EL1/S) → BL31(EL3/S, 상주) → BL33(NS-EL1/NS) → Linux(NS-EL1/NS)
                                                      ^^^^^^^^
                                              핵심 전환점: SCR_EL3.NS = 0 → 1

  SoC 인프라 관점에서의 의미:
    BL1(EL3)이 TZPC/TZASC/GIC/SMMU 보안 설정을 완료한 후,
    BL31→BL33 전환 시 SCR_EL3.NS=1로 변경.
    이 시점부터 위에서 설정한 모든 보안 인프라가 실제로 "작동"한다:
      → NS Master의 Secure 메모리 접근 → TZASC 차단
      → NS에서 OTP/Crypto 접근 → TZPC 차단
      → NS DMA → SMMU 차단
      → NS에서 Secure 인터럽트 마스킹 → GIC 차단
```

---

## Q&A

**Q: Secure에서 Non-Secure로의 전환은 어떻게 이루어지는가?**
> "반드시 EL3(Secure Monitor)를 경유한다. (1) Normal World에서 SMC 명령으로 EL3 진입. (2) EL3가 Normal World 컨텍스트를 저장하고 SCR_EL3.NS를 0으로 설정. (3) Secure World 컨텍스트를 복원하고 ERET으로 S-EL1에 진입. 반대 방향도 동일하게 EL3를 경유한다. 이 단일 게이트 구조가 TrustZone 보안의 핵심이다."

**Q: TZASC와 TZPC의 차이는?**
> "보호 대상이 다르다. TZPC는 APB 주변장치(OTP, Crypto, 타이머)를 Secure/Non-Secure로 분류한다. TZASC는 DRAM 주소 영역을 분할하여 특정 메모리 범위를 Secure 전용으로 설정한다. 둘 다 BootROM(EL3)이 초기화하며, 설정 후에는 Non-Secure에서 변경 불가능하다."

**Q: SMMU와 TZASC의 차이는?**
> "보호 세밀도와 방식이 다르다. TZASC는 물리 주소 영역(Region) 단위로 DRAM을 Secure/Non-Secure로 분할한다 — 모든 Master에 공통 적용. SMMU는 디바이스(Stream ID)별로 독립된 페이지 테이블을 할당하여, 각 DMA Master가 접근할 수 있는 메모리를 페이지(4KB) 단위로 제어한다. 예: TZASC는 '0~1GB는 Secure'라고 전체 차단하고, SMMU는 'GPU는 이 페이지들만 접근 가능'이라고 디바이스별 제어한다. 둘 다 필요하다."

**Q: 캐시에서 NS-bit 태깅이 필요한 이유는?**
> "같은 물리 주소에 대해 Secure와 Non-Secure가 다른 데이터를 가질 수 있기 때문이다. 캐시 라인에 NS 비트를 태깅하여 PA가 같아도 별도의 캐시 엔트리로 관리한다. 이것이 없으면 NS 접근이 Secure 데이터의 캐시 라인을 히트하여 암호 키 같은 민감 정보가 노출될 수 있다. 부가 효과로 월드 전환 시 캐시/TLB flush가 불필요해져 SMC 성능이 향상된다."

**Q: 부팅 중 보안 레벨이 어떻게 변하는가?**
> "BL1(EL3/Secure) → BL2(S-EL1/Secure) → BL31(EL3/Secure, 상주) → BL33(NS-EL1/Non-Secure)으로 전환된다. 핵심 전환점은 BL31이 BL33에게 제어를 넘길 때 SCR_EL3.NS를 1로 설정하는 순간이다. 이후 Normal World에서는 Secure 자원 접근이 HW적으로 차단된다."

---

## 확인 문제

**문제 1: SoC 보안 인프라 역할 매칭**
> 다음 공격 시나리오 각각에 대해, 어떤 SoC 보안 인프라(TZPC, TZASC, SMMU, GIC 중)가 1차 방어를 담당하는지 매칭하고, 그 이유를 설명하라.
> - (A) 악성 GPU 드라이버가 DMA로 Secure DRAM의 암호 키를 읽으려 함
> - (B) Linux 커널이 OTP 퓨즈 레지스터를 읽으려 함
> - (C) 해킹된 OS가 Crypto Engine 완료 인터럽트를 마스킹하려 함
> - (D) Normal World 코드가 TEE OS 메모리를 직접 접근하려 함

<details>
<summary>풀이 과정</summary>

**사고 과정:**
각 공격의 특성을 파악 → 보호 대상(주변장치? 메모리? 인터럽트? DMA?)으로 분류

**(A) GPU DMA → Secure DRAM:** **SMMU** (+ TZASC)
- GPU는 DMA Master → SMMU가 Stream ID로 GPU 식별
- SMMU의 페이지 테이블에 Secure DRAM 매핑이 없음 → Translation Fault
- TZASC도 물리 주소 레벨에서 추가 차단 (다층 방어)

**(B) Linux → OTP 퓨즈:** **TZPC**
- OTP는 APB 주변장치 → TZPC가 Secure Only로 설정
- NS Master의 OTP 접근 → 버스 에러 반환

**(C) OS → Secure 인터럽트 마스킹:** **GIC**
- Crypto 완료 IRQ는 Group 0 (Secure)으로 설정
- NS에서 Group 0 인터럽트의 Priority/Enable 변경 불가
- GICD 레지스터의 해당 비트가 NS 접근에 대해 RAZ/WI (Read-As-Zero/Write-Ignored)

**(D) NS 코드 → TEE 메모리:** **TZASC**
- TEE OS 메모리는 Secure DRAM 영역에 위치
- TZASC Region 설정에 의해 NS 접근 차단
- 버스 에러(DECERR) 반환

**핵심 포인트:**
- TZPC = APB 주변장치, TZASC = DRAM 영역, SMMU = DMA 디바이스별, GIC = 인터럽트
- 실제 SoC에서는 다층 방어: 하나가 뚫려도 다른 레벨에서 차단
</details>

**문제 2: SMC 월드 전환 시퀀스**
> Linux(NS-EL1)에서 OP-TEE(S-EL1)로 월드 전환이 일어날 때, EL3(Secure Monitor)가 수행하는 작업을 올바른 순서로 나열하라:
> (a) ERET 실행 (b) SCR_EL3.NS = 0 설정 (c) NS 레지스터 컨텍스트 저장 (d) Secure 레지스터 컨텍스트 복원 (e) SPSR_EL3에 S-EL1 복귀 정보 설정

<details>
<summary>풀이 과정</summary>

**사고 과정:**
1. 먼저 현재 상태(NS)의 컨텍스트를 잃지 않도록 저장해야 함
2. 보안 상태를 Secure로 전환해야 함
3. Secure World의 이전 컨텍스트를 복원해야 함
4. ERET으로 S-EL1으로 점프해야 함

**정답:** **(c) → (b) → (d) → (e) → (a)**

```
1. (c) NS 레지스터 컨텍스트 저장
   → X0~X30, SP_EL1, ELR_EL1, SPSR_EL1 등을 NS 컨텍스트 구조체에 저장
   → 이걸 먼저 안 하면 Secure 복원 시 NS 상태를 덮어씀

2. (b) SCR_EL3.NS = 0 설정
   → 이 시점부터 하위 EL은 Secure 상태
   → NS 비트 변경은 EL3에서만 가능

3. (d) Secure 레지스터 컨텍스트 복원
   → 이전에 저장해둔 S-EL1 컨텍스트(X0~X30, SP_EL1 등) 복원

4. (e) SPSR_EL3에 S-EL1 복귀 정보 설정
   → SPSR_EL3.M = EL1h, ELR_EL3 = OP-TEE 복귀 주소

5. (a) ERET 실행
   → SPSR_EL3 → PSTATE, ELR_EL3 → PC
   → S-EL1(OP-TEE)에서 실행 재개
```
</details>

**문제 3: Shared Memory 보안 위험**
> Secure World와 Normal World 간 Shared Memory 통신에서 TOCTOU (Time-of-Check-Time-of-Use) 공격이 어떻게 발생하는지 시나리오를 작성하고, 방어 방법을 제시하라.

<details>
<summary>풀이 과정</summary>

**사고 과정:**
1. Shared Memory는 양쪽에서 접근 가능 → NS가 데이터를 변조할 수 있음
2. Secure World가 데이터를 "검증"한 후 "사용"하기까지 시간 차이가 있음
3. 그 사이에 NS가 데이터를 바꾸면?

**TOCTOU 공격 시나리오:**
```
  Shared Buffer: [cmd=ENCRYPT, key_id=3, data_ptr=0x1000, len=256]

  시간 →
  Secure World:  검증(cmd 유효?)  ←OK→  사용(data_ptr에서 읽기)
                      ↑                       ↑
  Normal World:       │      data_ptr 변조!    │
                      │   0x1000 → 0xDEAD_0000 │
                      │  (Secure 내부 주소로!)  │

  결과: Secure World가 의도하지 않은 Secure 메모리를 읽어서
       Normal World에 반환 → 키 유출!
```

**방어 방법:**
1. **Copy-then-Validate**: Shared Buffer를 Secure 전용 메모리에 복사한 후 검증+사용
   → NS가 복사 후 원본을 변조해도 영향 없음
2. **Bounce Buffer**: NS가 쓴 데이터를 Secure 측이 한 번에 복사 (memcpy) 후 원본 무시
3. **Input Sanitization**: 포인터/주소 파라미터는 Secure World가 무조건 재검증
   → data_ptr이 NS 메모리 범위인지 확인 (Secure 메모리 참조 차단)
4. **FF-A Memory Lending**: 메모리를 빌려주면(FFA_MEM_LEND) 빌려준 쪽의 접근 권한 제거 → TOCTOU 원천 차단
</details>

---

!!! danger "❓ 흔한 오해"
    **오해**: World switch 는 단순 instruction 한 번

    **실제**: SMC instruction 한 번이지만 monitor 가 GPR / FP / vector / system register 모두 save/restore 필요. 잘못하면 secure state 누설.

    **왜 헷갈리는가**: "call = 단순" 이라는 직관. 실제는 context save 의 정확성이 critical.

!!! warning "실무 주의점 — SMC 후 register save/restore 부족으로 secure state 누설"
    **현상**: NS world 가 secure key/credential 의 일부를 GPR/SIMD 레지스터에서 읽어낸다.

    **원인**: SMC 호출 후 BL31 이 GPR x0~x30 만 save 하고 NEON/FP/SVE/sysreg 일부를 누락해, 이전 secure context 의 잔여 값이 NS world ERET 후에도 그대로 남는다.

    **점검 포인트**: world switch 진입/탈출 시 SIMD/FP, TPIDR_EL*, vector regs 까지 모두 zeroize 또는 save/restore 하는지 BL31 context 코드와 register dump 로 확인.

## 핵심 정리

- **World switch는 EL3 강제**: SMC instruction → EL3 trap → secure monitor (BL31)이 context save → world switch → 새 world로 ERET.
- **Context isolation**: 각 world는 독립 register set. SMC 시 secure monitor가 모든 register save/restore.
- **TZPC (TrustZone Protection Controller)**: peripheral마다 secure/non-secure 설정.
- **TZASC (TrustZone Address Space Controller)**: DRAM 영역을 secure/non-secure 분할.
- **GIC v3**: 인터럽트마다 group (Group 0 secure, Group 1 non-secure), 우선순위.
- **sysMMU StreamID + Stage 2**: device 마스터가 secure 메모리 access 시도하면 차단.

## 다음 단계

- 📝 [**Module 02 퀴즈**](quiz/02_world_switch_soc_infra_quiz.md)
- ➡️ [**Module 02A — Secure Enclave & TEE**](02a_secure_enclave_and_tee_hierarchy.md)

<div class="chapter-nav">
  <a class="nav-prev" href="../01_exception_level_trustzone/">
    <div class="nav-label">◀ 이전</div>
    <div class="nav-title">Exception Level & TrustZone</div>
  </a>
  <a class="nav-next" href="../02a_secure_enclave_and_tee_hierarchy/">
    <div class="nav-label">다음 ▶</div>
    <div class="nav-title">Unit 2A: Secure Enclave & TEE 계층 구조</div>
  </a>
</div>
