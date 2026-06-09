---
title: "Module 01 — ARM AArch64 개요 & ISA"
---

:::tip[학습 목표]
이 모듈을 마치면:

- **Explain** ARM이 load-store RISC 계열로서 fixed-length 명령·다수의 레지스터·weak memory를 택한 이유를 설명할 수 있다.
- **Classify** Cortex-A / Cortex-R / Cortex-M / Neoverse 프로파일을 용도와 특징으로 분류할 수 있다.
- **Identify** ARMv8.0부터 ARMv9까지 ISA 버전이 더한 핵심 기능(LSE, PAuth, MTE, SVE2 등)을 식별할 수 있다.
- **Differentiate** ARM AArch64 / RISC-V RV64 / x86-64를 명령 길이·레지스터·메모리 모델·특권 모델 축으로 구분할 수 있다.
- **Relate** ISA가 하드웨어/소프트웨어 계약이라는 관점에서 같은 ISA가 왜 수십 가지 마이크로아키텍처로 구현되는지 연관지을 수 있다.
:::
:::note[사전 지식]
- ISA·파이프라인의 일반 개념 — [Computer Architecture M01](../../computer_architecture/01_isa_riscv/)
- 레지스터 파일·명령 인출/디코드/실행에 대한 기본 직관
:::
---

## 1. Why care? — DUT 한복판에 앉은 코어의 "계약서"를 읽는 일

### 1.1 시나리오 — 같은 ELF가 한 칩에선 돌고 다른 칩에선 안 도는 이유

데이터센터 가속기 카드의 관리용 펌웨어를 검증한다고 합시다. 같은 C 소스를 한 **SoC**(System on Chip — CPU·메모리·주변장치를 한 칩에 통합한 시스템)의 Cortex-A 코어용으로 빌드한 바이너리는 잘 도는데, 다른 SoC의 Cortex-M 기반 **MCU**(microcontroller unit — 단순 제어용 소형 프로세서 칩)로 가져가니 부팅조차 못 합니다. 원인은 코드 버그가 아니라 **ISA**(Instruction Set Architecture, 명령어 집합 구조 — 하드웨어가 어떤 명령을 어떻게 실행하는지 규정한 계약) 프로파일이 다르다는 데 있습니다. Cortex-A는 **AArch64**(ARM의 64-bit 실행 상태와 그 명령 집합)에 **MMU**(memory management unit — 가상 주소를 물리 주소로 번역하는 하드웨어)를 갖춘 application 프로파일이지만, Cortex-M은 **Thumb-2**(코드 크기를 줄인 16/32-bit 혼합 ARM 명령 집합) 전용에 MMU가 없는 microcontroller 프로파일이라 64-bit AArch64 바이너리를 아예 실행할 수 없습니다.

```
같은 C 소스
  ├─ aarch64-linux-gnu-gcc  → AArch64 ELF  → Cortex-A: OK
  └─ arm-none-eabi-gcc      → Thumb-2 ELF  → Cortex-M:  OK
                              (서로 호환 안 됨)
```

ISA를 "명령어 표"가 아니라 **HW와 SW 사이의 계약**으로 읽으면 이런 문제가 즉시 보입니다. 어떤 명령이 존재하는가, 레지스터/메모리 모델이 어떤가, 예외·가상화·보안 경계가 어떻게 정의되는가 — 이 계약이 코어마다 다르면 같은 바이너리가 돌지 않습니다.

이 모듈을 건너뛰면 이후의 모든 모듈이 공중에 뜹니다. 레지스터(M02), 예외(M03), 메모리 모델(M04)은 전부 "AArch64라는 계약"의 조항들이기 때문입니다. ARM 검증 현장에서 "이 코어가 무엇을 보장하는가"를 ISA 레벨에서 먼저 못 박지 않으면, RTL 동작이 spec 준수인지 위반인지 판단할 기준 자체가 없습니다.

---

## 2. Intuition — 계약서, 그리고 한 장 그림

:::tip[💡 한 줄 비유]
**ISA** ≈ **건축 규정(building code)**.<br>
규정은 "기둥은 이 하중을 견뎌야 한다"는 _계약_ 만 정하지, 콘크리트로 짓든 철골로 짓든 _구현 방법_ 은 건축가(마이크로아키텍처)에게 맡깁니다. 그래서 같은 AArch64 ISA가 작은 in-order A53부터 거대한 OoO Neoverse V2까지 _수십 가지_ 로 구현됩니다 — 계약은 하나, 구현은 여럿.
:::
### 한 장 그림 — ISA 계약 위에 얹힌 SW와 그 아래 구현

```d2
direction: down

SW: "**Software**\nOS · 펌웨어 · 유저 앱\n(컴파일된 AArch64 바이너리)"
ISA: "**ISA — AArch64 계약**\n명령 집합 · 31 GPR · PSTATE\nEL0–3 · weak memory · 예외 모델"
UA1: "**μarch A**\nCortex-A53\nin-order, 8-stage"
UA2: "**μarch B**\nNeoverse V2\nwide OoO, deep pipe"
HW: "**Silicon**\n게이트 · 캐시 · 인터커넥트"

SW -> ISA: "이 계약에만 의존"
ISA -> UA1: "구현 1"
ISA -> UA2: "구현 N"
UA1 -> HW
UA2 -> HW
```

위 그림의 ISA 상자에 적힌 용어를 미리 풀어두면: **GPR**(general-purpose register, 범용 레지스터 — 정수 값을 담는 일반 레지스터)은 AArch64에 31개 있고, **PSTATE**(Process State — 조건 플래그·인터럽트 마스크 등 코어의 실행 중 상태를 모은 논리적 집합)는 직전 연산 결과나 권한 상태를 담으며, **EL0–3**(Exception Level — 숫자가 클수록 권한이 높은 4단계 특권 레벨, EL0=유저앱 … EL3=보안 모니터)은 소프트웨어 계층을 격리합니다. **weak memory**(약한 메모리 순서 — 하드웨어가 성능을 위해 메모리 접근 순서를 프로그램 순서와 다르게 재배열할 수 있는 모델)는 M04에서 깊이 다룹니다.

### 왜 이 디자인인가 — Design rationale

ARM은 **Advanced RISC Machines**의 약자이고(1990년 창립, 칩을 직접 만들지 않고 IP를 라이선스), load-store RISC의 세 가지 원칙을 핵심 계약으로 삼습니다. 이 세 원칙은 우연이 아니라 서로 맞물린 설계 결정입니다.

1. **메모리는 LDR/STR로만 접근하고 연산은 레지스터끼리** → 디코더가 "이 명령이 메모리를 건드리나?"를 단순하게 판단 → 파이프라이닝이 깔끔.
2. **fixed-length 명령(A64는 32-bit 고정)** → 다음 명령 시작 위치를 항상 PC+4로 알 수 있음 → 인출/디코드가 가변 길이 x86보다 훨씬 단순.
3. **레지스터를 많이(AArch64는 31개 GPR)** → 값을 레지스터에 오래 머무르게 해 메모리 spill 부담 감소 → load/store 빈도가 줄어 1번과 시너지.

세 원칙이 곧 "**단순 디코드 + 파이프라인 친화 + 적은 메모리 접근**"이라는 RISC의 성능 논리이며, 이것이 ARM이 모바일의 전력 효율부터 서버 성능까지 같은 ISA 계약으로 커버하는 토대입니다.

---

## 3. 작은 예 — `c = a + b` 한 줄이 AArch64 명령이 되는 과정

가장 단순한 시나리오. C의 `c = a + b`가 load-store RISC에서 어떻게 풀리는지를 보면 ISA 계약의 세 원칙이 한눈에 들어옵니다.

### 단계별 다이어그램

```d2
direction: down

C: "**C 소스**\nint c = a + b;"
L1: "**① LDR**\nw0 ← [x_a]\n(메모리 → 레지스터)"
L2: "**② LDR**\nw1 ← [x_b]"
ADD: "**③ ADD**\nw2 = w0 + w1\n(레지스터끼리 연산)"
ST: "**④ STR**\nw2 → [x_c]\n(레지스터 → 메모리)"
C -> L1
L1 -> L2
L2 -> ADD
ADD -> ST
```

### 단계별 의미

| Step | 명령 | 무엇을 | 왜 (어떤 ISA 원칙) |
|---|---|---|---|
| ① | `ldr w0, [x_a]` | a를 메모리에서 레지스터로 | 메모리는 LDR/STR로만 접근 |
| ② | `ldr w1, [x_b]` | b를 레지스터로 | 연산 전에 피연산자를 레지스터에 적재 |
| ③ | `add w2, w0, w1` | 레지스터끼리 더함 | ALU 연산은 register↔register만 |
| ④ | `str w2, [x_c]` | 결과를 메모리로 | 쓰기도 STR로만 |

x86이라면 `add eax, [b]`처럼 메모리 피연산자를 직접 더할 수 있지만, ARM은 ②와 ③을 강제로 분리합니다. 이 분리가 디코더를 단순하게 만들고 파이프라인을 균일하게 만드는 대가입니다.

### 실제 코드

```asm
// int add(int a, int b) { int c = a + b; return c; }
// AArch64 (a in w0, b in w1 per AAPCS64 calling convention)
add:
    add   w0, w0, w1          // w0 = a + b  — register↔register
    ret                       // branch to LR (x30); 결과는 w0로 반환
```

함수 인자가 이미 `w0`, `w1`에 와 있으므로(호출 규약 AAPCS64) 실제로는 load조차 필요 없이 `add` 한 줄로 끝납니다. 31개의 레지스터가 있기에 인자를 메모리에 올리지 않고 레지스터로 주고받는 이 규약이 성립합니다.

:::note[여기서 잡아야 할 두 가지]
**(1) 메모리 접근과 연산이 명령 레벨에서 분리된다.** 이 분리가 "RISC다움"의 핵심이며, 파이프라인의 MEM 단계와 EX 단계가 깔끔히 나뉘는 이유입니다.<br>
**(2) 명령 길이가 32-bit 고정이라 `ret` 다음 명령 위치를 항상 안다.** 가변 길이 디코드의 복잡성이 없다는 것이 ARM frontend가 단순해지는 출발점입니다.
:::
---

## 4. 일반화 — ARM 프로파일, ISA 버전, 그리고 세 ISA 비교

### 4.1 ARM 프로파일 — 같은 계약의 네 가지 용도별 변형

ARM은 하나의 브랜드 아래 용도가 전혀 다른 네 계열을 둡니다. 검증 대상 SoC가 어느 프로파일인지를 알면 MMU 유무·실시간성·전력 목표를 곧바로 추론할 수 있습니다.

| 프로파일 | 용도 | 특징 | 대표 코어 |
|----------|------|------|-----------|
| **Cortex-A** (Application) | OS 구동 고성능 | Android/Linux, SMP, MMU | A53, A76, A78, X925 |
| **Cortex-R** (Real-time) | 결정론적 응답 | 자동차·스토리지 컨트롤러, MPU 기반 | R5, R52, R82 |
| **Cortex-M** (Microcontroller) | 초저전력 MCU | Thumb-2 전용, No MMU, IoT | M0+, M4, M33, M85 |
| **Neoverse** (Infrastructure) | 서버·데이터센터 | AWS Graviton, NVIDIA Grace, Ampere | N2, V2, V3 |

검증 관점에서 이 분류는 곧 환경 가정으로 직결됩니다. Cortex-A/Neoverse라면 MMU·다단계 주소 번역·**SMP**(Symmetric Multi-Processing — 동등한 여러 코어가 같은 메모리를 공유하는 구성) coherence(여러 코어의 캐시가 같은 메모리 값을 일관되게 보도록 맞추는 것)를 전제해야 하고(M04–M06), Cortex-M이라면 그런 것들이 아예 없어 검증 시나리오가 단순해집니다.

### 4.2 ISA 버전 진화 — 계약에 조항이 추가되는 역사

| Version | 핵심 기능 | 대표 코어 |
|---------|-----------|-----------|
| `ARMv7-A` | 32-bit, Thumb-2, NEON SIMD, VFPv3/4 | A8, A9, A15 |
| `ARMv8.0-A` | **AArch64 도입**, 31 GPR, AArch32 호환 | A53, A57, A72 |
| `ARMv8.1~8.6` | LSE atomics, RAS, PAuth, BTI, MTE | A76, A78, N1 |
| `ARMv9.0+` | SVE2, CCA (Realm), 강화된 security | A710, X2, V2 |

여기서 검증에 직접 닿는 조항이 많습니다. **LSE**(Large System Extensions)는 LL/SC 루프 대신 단일 명령 atomic을 제공하고(M04에서 다룸), **PAuth**(Pointer Authentication)·**BTI**(Branch Target Identification)·**MTE**(Memory Tagging)는 보안 검증의 대상이며([ARM Security](../../arm_security/)로 연결), **SVE2**는 벡터 길이에 무관한(VL-agnostic) SIMD입니다.

### 4.3 세 ISA 나란히 — ARM / RISC-V / x86-64

ARM의 설계 결정을 객관적으로 보려면 다른 ISA와 대조하는 것이 가장 빠릅니다. 같은 load-store RISC 계열인 RISC-V와는 공통 원리가 많고, CISC인 x86-64는 세 번째 기준점이 됩니다.

| Axis | ARM AArch64 | RISC-V RV64 | x86-64 |
|------|-------------|-------------|--------|
| Instruction length | fixed 32-bit (+ SVE variant) | 32-bit base, 16-bit with `C` (RVC) | variable 1–15 bytes |
| GPR | 31 (+ SP/PC/ZR) | 31 (`x1-x31`) + `x0` (hardwired 0) | 16 (RAX–R15) |
| FP/Vector Register | 32 (`V0-V31`) | 32 (`f0-f31`) | 16 (XMM/YMM/ZMM) |
| Privilege | EL0 / EL1 / EL2 / EL3 | U / S / (HS) / M | Ring 0 / 1 / 2 / 3 |
| Memory Model | Weakly-ordered + acquire/release | RVWMO (weak) / Ztso (strict) | TSO (Total Store Order) |
| SIMD / Vector | NEON (128-bit), SVE/SVE2 (VL-agnostic) | RVV 1.0 (VL-agnostic) | SSE / AVX / AVX-512 |
| Atomic | LL/SC + LSE (v8.1+) | LR/SC + AMO (A ext) | LOCK prefix, XADD, CMPXCHG |
| Interrupt Ctrl | GIC (v2/v3/v4) | PLIC / CLIC / AIA | LAPIC + IOAPIC |
| License | proprietary IP (Arm Ltd) | open standard | proprietary (Intel/AMD) |

표에 처음 나온 용어 몇 개를 풀어두면: **acquire/release**(읽기 이후·쓰기 이전의 순서만 국소적으로 보장하는 가벼운 메모리 순서 표시), **LL/SC**(Load-Linked/Store-Conditional — "읽은 뒤 아무도 안 건드렸으면 쓰기 성공"으로 락 없는 갱신을 구현하는 명령 쌍), **GIC**(Generic Interrupt Controller — 인터럽트의 우선순위·라우팅·완료를 표준화해 관리하는 ARM 인터럽트 컨트롤러)입니다. 이 표의 행 하나하나가 이후 모듈의 주제입니다. Privilege 행은 M03(Exception Level), Memory Model 행은 M04(배리어), Interrupt Ctrl의 GIC는 M06으로 이어집니다.

#### ARM 은 왜 dedicated zero register 없이 31번을 SP/ZR 로 양분했나

표의 GPR 행을 자세히 보면 ARM 과 RISC-V 의 설계 철학 차이가 드러납니다. RISC-V 는 `x0` 을 _상시 hardwired zero_ 로 못 박아 32개 중 한 칸을 항상 0 전용으로 씁니다(M01 computer_architecture). ARM 은 그렇게 하지 않고, 레지스터 인코딩의 **31번 자리를 명령 문맥에 따라 SP(stack pointer) 또는 ZR(zero register)로 양분**합니다 — 즉 31번이 어떤 명령에서는 SP 로, 어떤 명령에서는 XZR/WZR 로 해석됩니다.

이 선택의 trade-off 는 이렇습니다. RISC-V 식 dedicated zero 는 _디코드가 단순_ 하지만(31번은 언제나 0) 범용 레지스터를 한 칸 _영구히_ 0 에 바칩니다. ARM 식 문맥 양분은 _zero register 의 표현력_(`cmp x0, xzr` 같은 0 관용구를 별도 명령 없이)을 누리면서도 그 인코딩 슬롯을 _SP 로도 재활용_ 해, 31개 범용 + SP + ZR 의 기능을 31개 인코딩 안에 욱여넣습니다. 대가는 디코드 복잡도입니다 — 어셈블러·디코더가 "이 명령에서 31번은 SP 인가 ZR 인가"를 명령별 규칙으로 판정해야 합니다(M02 오해3 에서 본 함정). 즉 ARM 은 _인코딩 공간 절약 + zero 관용구_ 를 디코드 규칙의 약간의 복잡도로 산 것입니다.

#### NZCV 와 conditional execution — ARM 이 branchless 를 선호하는 ISA 철학

표의 행에는 안 보이지만 ARM ISA 의 깊은 특징 하나가 **condition flag(NZCV) 중심 실행**입니다. ARM 의 많은 산술 명령은 결과에 따라 N/Z/C/V 플래그를 갱신할 수 있고, 그 플래그를 읽어 _분기 없이_ 동작을 바꾸는 명령군(`csel` conditional select, `b.cond` 조건 분기, AArch32 의 더 광범위한 predication)을 둡니다. 이것이 우연이 아니라 의도된 철학입니다.

근거는 M07 에서 볼 _분기 예측 실패의 비용_ 입니다. 짧고 데이터 의존적인 조건(예: `max(a,b)`)을 진짜 분기로 컴파일하면, 예측이 어려운 분기일수록 misprediction flush(수십 사이클)가 잦습니다. ARM 은 이런 조건을 **flag + conditional select** 로 바꿔 _분기 자체를 없애_(branchless) mispredict 위험을 제거하도록 ISA 레벨에서 지원합니다 — `cmp; csel` 두 명령이면 분기 없이 둘 중 하나를 고릅니다(M08 csel 패턴). 즉 NZCV 를 ISA 깊숙이 둔 것은 "조건을 분기로 풀지 말고 데이터플로우로 풀라"는 성능 철학의 표현이며, 컴파일러가 ARM 에서 branchless 코드를 적극적으로 내는 이유입니다.

:::note[CISC도 내부는 RISC — 단, RISC도 1:1은 아니다]
현대 x86 CPU도 복잡한 CISC 명령을 내부적으로 **micro-op**으로 분해(crack)해 RISC 스타일 backend로 실행합니다. 그래서 "CISC vs RISC" 구분은 ISA 표면(디코드 복잡도, 명령 길이)에만 남아 있고, 마이크로아키텍처 레벨에선 거의 같은 그림입니다. ARM이 표면에서부터 단순하다는 점이 frontend 면적·전력에서 이점입니다.

여기서 흔한 오해 하나를 미리 끊어야 합니다 — "ARM 은 RISC 니 모든 명령이 micro-op 하나(1:1)"가 아닙니다. ARM 도 _일부 복잡 명령_ 을 내부적으로 여러 micro-op 으로 crack 합니다. 대표적으로 두 레지스터를 한 명령으로 load/store 하는 **`LDP`/`STP`** 나 AArch32 의 다중 레지스터 전송 **`LDM`/`STM`** 은 메모리 접근을 여러 개 수행하므로 backend 에서 복수 micro-op 으로 쪼개지는 것이 보통입니다. RISC 의 이점은 "_대부분_ 의 명령이 단순해 평균 crack 비율이 낮다"이지 "_모든_ 명령이 1:1"이 아닙니다 — 그래서 ARM 코어도 frontend 에 micro-op crack 단계를 가집니다(M07 frontend). 검증·성능 분석에서 명령 수와 micro-op 수를 동일시하면 IPC/throughput 해석이 어긋납니다.
:::

---

## 5. 디테일 — load-store가 만드는 코드 모양과 ISA 표면의 함정

### 5.1 왜 ARM과 RISC-V를 나란히 두는가

이 코스가 두 ISA를 자주 대조하는 데는 이유가 있습니다. 둘 다 load-store RISC라 공통 원리가 많아 대조 학습에 유리하고, ARM은 수십억 대 칩으로 배포된 설계라 구체적 TRM(Technical Reference Manual)과 설계 결정이 공개되어 있으며, RISC-V는 열린 표준이라 스펙 문서로 바로 확인할 수 있어 확장 구조가 학습용으로 깔끔합니다. x86-64는 세 번째 기준점으로만 표에 등장합니다.

### 5.2 fixed-length가 검증에 주는 것

명령 길이가 32-bit로 고정이라는 사실은 검증에서 의외로 큰 단순화를 줍니다. 명령 메모리에서 다음 명령의 경계가 항상 4바이트 정렬이므로, 명령 fetch를 관찰하는 monitor가 "명령 시작 위치"를 추측할 필요가 없습니다. x86처럼 1–15바이트 가변이면 어디까지가 한 명령인지 디코드 전에는 알 수 없어 monitor 모델링이 훨씬 까다롭습니다.

### 5.3 ARM의 두 실행 상태 — AArch64 vs AArch32

ARMv8 코어는 두 실행 상태를 가질 수 있습니다. **AArch64**는 64-bit 실행 상태로 A64 명령 집합(32-bit 고정 인코딩)을 쓰고, **AArch32**는 ARMv7 호환의 32-bit 실행 상태로 A32/T32(Thumb) 명령을 씁니다. 본 코스는 AArch64에 집중하지만, 한 코어가 EL마다 다른 실행 상태로 동작할 수 있다는 점(예: EL1은 AArch64, EL0은 AArch32)은 검증 시 환경 가정으로 반드시 확인해야 합니다.

#### interworking 의 비용 — 실행 상태는 EL 경계에서만 바뀐다

여기서 중요한 제약이 있습니다 — AArch64 와 AArch32 는 _같은 명령 스트림 안에서 자유롭게 섞어 쓸 수 없습니다._ x86 의 16/32/64-bit 모드 전환이나 ARMv7 의 `BX` 를 통한 ARM↔Thumb interworking 처럼 _함수 호출 단위로_ 상태를 바꾸는 것을, AArch64 는 허용하지 않습니다. **실행 상태 전환은 오직 EL 경계를 넘을 때만**(예외로 상위 EL 진입, 또는 `ERET` 로 하위 EL 복귀) 일어납니다. 예를 들어 EL1(AArch64) 커널이 EL0(AArch32) 응용을 실행하려면, EL0 로 내려가는 `ERET` 시점에 SPSR 의 실행 상태 비트로 AArch32 를 지정하는 식입니다.

하드웨어적 이유는 두 실행 상태가 _레지스터 모델·명령 인코딩·PSTATE 구성이 근본적으로 다르기_ 때문입니다. AArch64 는 31개 64-bit GPR + 분리된 PC/SP 를, AArch32 는 16개 32-bit 레지스터(PC=R15 포함) + 모드별 banked 레지스터를 씁니다. 한 명령 흐름 중간에서 이를 전환하려면 레지스터 파일과 디코더를 _명령마다_ 재해석해야 해 파이프라인이 감당하기 어렵습니다. 그래서 ARM 은 전환을 _드물고 명확한_ EL 경계로 한정해, 그 시점에만 상태를 한꺼번에 바꾸도록 설계했습니다 — 검증에서 "AArch32 코드가 AArch64 컨텍스트에서 직접 호출되어 도는" 시나리오는 _불가능_ 하며, 상태 혼용 의심이 들면 EL 전환 경계부터 확인해야 합니다.

```asm
// A64 (AArch64) — 32-bit fixed, 64-bit 레지스터
    add   x0, x1, x2          // 64-bit add
    add   w0, w1, w2          // 32-bit add (상위 32-bit는 zero로)

// A32 (AArch32) — 다른 인코딩, 다른 레지스터 모델 (r0-r15)
    add   r0, r1, r2
```

---

## 6. 흔한 오해 와 DV 디버그 체크리스트

### 흔한 오해

:::danger[❓ 오해 1 — 'ARM 바이너리는 모든 ARM 코어에서 돈다']
**실제**: 프로파일과 실행 상태가 맞아야 합니다. AArch64 바이너리는 AArch64를 지원하는 코어에서만 돌고, Cortex-M(Thumb-2 전용)에서는 아예 실행 불가입니다. 같은 "ARM"이라도 계약이 다릅니다.<br>
**왜 헷갈리는가**: 브랜드가 하나라서 ISA도 하나일 거라는 착각 — 실제로는 A/R/M/Neoverse 네 프로파일 + AArch64/AArch32 두 실행 상태의 조합.
:::
:::danger[❓ 오해 2 — '레지스터가 많으면 무조건 빠르다']
**실제**: 레지스터가 많으면 spill이 줄지만, 그만큼 컨텍스트 스위치/예외 진입 시 저장할 레지스터도 많아집니다. 31개 GPR + 32개 V 레지스터를 예외 핸들러가 저장하는 비용은 M03에서 봅니다 — 이점과 비용이 함께 옵니다.<br>
**왜 헷갈리는가**: "spill 감소"라는 한쪽 이점만 보고 컨텍스트 저장 비용을 잊어서.
:::
:::danger[❓ 오해 3 — 'fixed-length면 코드 크기가 항상 작다']
**실제**: 32-bit 고정 명령은 디코드는 쉽지만, 작은 상수를 다루는 경우 x86의 짧은 명령보다 코드가 커질 수 있습니다. 그래서 ARM은 코드 밀도를 위해 Thumb(16/32-bit mixed)을, RISC-V는 `C` 확장(16-bit)을 둡니다.<br>
**왜 헷갈리는가**: "단순=작다"로 단순화해서 — 디코드 단순성과 코드 밀도는 별개의 축.
:::

### DV 디버그 체크리스트 (이 모듈 내용으로 마주칠 첫 함정들)

| 증상 | 1차 의심 | 어디 보나 |
|---|---|---|
| 펌웨어가 부팅조차 안 됨 | 프로파일/실행 상태 불일치 (AArch64 바이너리를 Cortex-M에) | 빌드 타깃(`-march`)과 코어 TRM의 프로파일 |
| 같은 코드가 한 코어에선 빠르고 다른 코어에선 느림 | 같은 ISA, 다른 마이크로아키텍처 (in-order A53 vs OoO V2) | 코어 모델명 → μarch 특성 |
| LSE atomic 명령이 illegal instruction | ARMv8.0 코어에서 v8.1+ 명령 사용 | 코어 ISA 버전과 명령 요구 버전 대조 |
| SVE 코드가 트랩 | ARMv9 미만 또는 SVE 미지원 코어 | `ID_AA64PFR0_EL1`의 SVE 필드 |
| MMIO 영역 접근이 reorder됨 | Normal 메모리로 매핑 (Device여야) | 페이지 속성 — M04 참조 |

---

## 7. 핵심 정리 (Key Takeaways)

- **ISA = HW/SW 계약**. AArch64는 명령·레지스터·예외·메모리 모델을 못 박고, 구현(마이크로아키텍처)은 같은 계약 위에서 수십 가지로 갈린다.
- **load-store RISC 세 원칙**: 메모리는 LDR/STR로만, 연산은 register↔register, 레지스터는 많이(31 GPR). 세 원칙이 단순 디코드·파이프라인 친화·적은 메모리 접근으로 맞물린다.
- **fixed-length 32-bit** 명령이 frontend를 단순하게 만든다 — 다음 명령 경계가 항상 PC+4.
- **네 프로파일**(A/R/M/Neoverse)은 같은 브랜드의 다른 계약. 프로파일을 알면 MMU·실시간성·전력 목표가 추론된다.
- **ISA 버전**(v8.0→v9)은 계약에 조항을 더한다: LSE, PAuth, BTI, MTE, SVE2 — 다수가 검증 대상.
- **세 ISA 비교**의 각 행(privilege, memory model, interrupt)이 곧 이후 모듈의 주제다.

:::caution[실무 주의점]
- 검증 환경을 세울 때 **프로파일 + ISA 버전 + 실행 상태(AArch64/AArch32)** 를 먼저 못 박는다 — 이게 모든 가정의 출발점.
- 명령이 illegal로 트랩하면 코어 ISA 버전과 명령 요구 버전을 대조한다(LSE는 v8.1+, SVE2는 v9).
- 같은 코드의 성능 차이는 보통 ISA가 아니라 μarch 차이 — 코어 모델명으로 추적.
:::
### 7.1 자가 점검

:::tip[🤔 Q1 — load-store 분리 (Bloom: Analyze)]
x86은 `add eax, [mem]`처럼 메모리 피연산자를 직접 더할 수 있는데, ARM은 왜 load와 add를 강제로 분리할까?
<details>
<summary>정답</summary>

파이프라인 단순화와 균일성 때문입니다.
- **디코드 단순화**: "이 명령이 메모리를 건드리나?"가 명령 종류(LDR/STR vs ALU)로 곧바로 갈림 → 디코더가 단순.
- **파이프라인 균일성**: 메모리 접근(MEM 단계)과 연산(EX 단계)이 다른 명령으로 분리되어 각 단계의 책임이 명확 → stall/forwarding 로직이 깔끔.
- **대가**: 명령 수가 늘 수 있음(load 2개 + add 1개). 하지만 31개 레지스터로 값을 오래 머무르게 해 load 빈도를 줄여 상쇄.
- 검증 관점: monitor가 "이 트랜잭션은 메모리 접근"인지를 명령 종류만으로 판정 가능.

</details>
:::
:::tip[🤔 Q2 — 계약 vs 구현 (Bloom: Evaluate)]
"A53과 Neoverse V2는 같은 AArch64라서 검증을 한 번만 하면 된다"는 주장의 문제는?
<details>
<summary>정답</summary>

ISA 계약은 같지만 마이크로아키텍처가 전혀 다릅니다.
- **계약(ISA) 동일**: 명령 의미, 레지스터, 메모리 모델의 _아키텍처적 보장_ 은 같음 → 기능적 정확성 테스트는 상당 부분 공유 가능.
- **구현(μarch) 상이**: A53은 in-order, V2는 wide OoO. 타이밍·재정렬 가시성·캐시 동작·분기 예측이 달라 _성능_ 과 _코너 케이스_ (특히 weak memory의 관측 순서)가 다르게 나타남.
- **결론**: 기능 검증은 공유하되, 타이밍/ordering/마이크로아키텍처 의존 시나리오는 코어별로 재검증 필요. "한 번만"은 위험한 단순화.

</details>
:::
### 7.2 출처

**Internal**
- [Computer Architecture M01 — ISA & RISC-V](../../computer_architecture/01_isa_riscv/) — ISA를 HW/SW 계약으로 보는 일반 관점
- [ARM Security](../../arm_security/) — PAuth/BTI/MTE 보안 확장 심화

**External**
- *Arm Architecture Reference Manual for A-profile (ARM ARM, DDI 0487)* — AArch64 ISA 정의 (외부 표준 지식)
- *Cortex-A/R/M Series Technical Reference Manuals* — Arm Ltd. (프로파일별 구현 세부)
- *RISC-V Unprivileged/Privileged Specification* — RISC-V International (대조용)

---

## 다음 모듈

→ [Module 02 — 레지스터 & PSTATE](../02_registers_pstate/): AArch64 계약의 첫 조항인 _레지스터 파일_ — X0–X30/SP/PC/XZR, W 뷰의 zero-extend, PSTATE의 NZCV/DAIF, 그리고 예외 처리용 시스템 레지스터를 본다.

[퀴즈 풀어보기 →](../quiz/01_overview_isa_quiz/)
