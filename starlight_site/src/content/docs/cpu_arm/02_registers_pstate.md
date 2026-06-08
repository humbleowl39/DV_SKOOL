---
title: "Module 02 — 레지스터 & PSTATE"
---

:::tip[학습 목표]
이 모듈을 마치면:

- **Identify** X0–X30, SP, PC, XZR/WZR 각각의 역할과 W 뷰(32-bit)의 zero-extend 규칙을 식별할 수 있다.
- **Explain** PSTATE의 NZCV(조건 플래그)와 DAIF(인터럽트 마스크)가 무엇을 담고 언제 바뀌는지 설명할 수 있다.
- **Describe** 예외 처리 시스템 레지스터(ELR/SPSR/ESR/FAR/VBAR)가 예외 진입 시 무엇을 저장하는지 기술할 수 있다.
- **Apply** 함수 프롤로그/에필로그에서 `stp/ldp`와 pre/post-index로 FP·LR을 저장/복원하는 패턴을 적용할 수 있다.
- **Differentiate** PSTATE 필드(실행 중 값)와 banked 시스템 레지스터(EL별 사본)를 구분할 수 있다.
:::
:::note[사전 지식]
- [Module 01 — 개요 & ISA](../01_overview_isa/) (load-store RISC, 31 GPR 계약)
- 함수 호출 규약·스택 프레임의 기본 직관
:::
---

## 1. Why care? — 레지스터를 잘못 읽으면 디버깅의 첫 단추가 어긋난다

### 1.1 시나리오 — `W0`에 쓴 값이 `X0` 상위를 날려버리다

펌웨어 디버깅 중, 어떤 함수가 64-bit 포인터를 `X0`에 담아 넘겼는데 호출된 쪽에서 포인터의 상위 32-bit가 통째로 0이 되어 잘못된 주소를 참조하는 현상을 만났다고 합시다. 코드를 보니 중간에 누군가 `mov w0, #1` 한 줄을 넣었습니다. 버그의 원인은 AArch64의 핵심 규칙 하나입니다.

```
X0 = 0xFFFF_0000_DEAD_BEEF    // 64-bit 포인터
mov w0, #1                    // W0(하위 32-bit)에 쓰면
                              // → X0 상위 32-bit가 자동으로 0이 됨!
X0 = 0x0000_0000_0000_0001    // 상위가 날아감
```

`W` 레지스터(32-bit 뷰)에 쓰면 대응되는 `X` 레지스터의 **상위 32-bit가 자동으로 zero-extend**됩니다. 이 규칙을 모르면 "왜 멀쩡한 포인터의 상위가 사라졌지?"를 영원히 헤맵니다.

레지스터는 검증에서 **상태를 읽는 첫 창**입니다. waveform이나 ISS(instruction set simulator) 로그에서 레지스터 값을 비교할 때, X/W 뷰의 관계·XZR의 의미·PSTATE 플래그를 정확히 모르면 expected와 actual의 mismatch가 진짜 버그인지 읽는 법을 틀린 건지 구분하지 못합니다. 이 모듈은 그 창을 정확히 읽는 법입니다.

---

## 2. Intuition — 작업대 위의 도구들, 그리고 한 장 그림

:::tip[💡 한 줄 비유]
**레지스터 파일** ≈ **목공 작업대 위에 펼쳐 둔 도구들**.<br>
재료(메모리의 데이터)를 작업대(레지스터)로 가져와서 다듬고(연산) 다시 선반(메모리)에 넣습니다. 작업대가 넓을수록(31개 GPR) 재료를 자주 선반에 갖다 놓을(spill) 필요가 없습니다. **PSTATE**는 작업대 옆의 _계기판_ — 마지막 연산이 음수였는지(N), 0이었는지(Z), 지금 인터럽트를 받을지(DAIF)를 표시합니다.
:::
### 한 장 그림 — GPR · 특수 레지스터 · PSTATE · 시스템 레지스터

```d2
direction: down

GPR: "**General Purpose (31)**\nX0–X30 (64-bit)\nW0–W30 (하위 32-bit 뷰)\nX30 = LR (return addr)" {
  style.fill: "#e8f0fe"
}
SPEC: "**특수 레지스터**\nSP (stack pointer, EL별 banked)\nPC (branch로만 변경)\nXZR/WZR (읽으면 0, 쓰면 버림)" {
  style.fill: "#e6f4ea"
}
PSTATE: "**PSTATE (실행 중 값)**\nNZCV — 조건 플래그\nDAIF — 인터럽트 마스크\nCurrentEL · SPSel · nRW" {
  style.fill: "#fef7e0"
}
SYS: "**시스템 레지스터 (EL별 banked)**\nELR_ELx · SPSR_ELx\nESR_ELx · FAR_ELx · VBAR_ELx" {
  style.fill: "#fce8e6"
}

GPR -> SPEC: "함께 데이터패스"
SPEC -> PSTATE: "연산 결과가 플래그 갱신"
PSTATE -> SYS: "예외 진입 시\nSPSR로 저장됨"
```

### 왜 이 디자인인가 — Design rationale

세 가지 요구가 이 레지스터 구조를 만듭니다.

1. **32-bit 코드와 64-bit 코드가 같은 레지스터를 공유해야** → X(64) / W(32) **이중 뷰**. W에 쓰면 상위를 0으로 지워 "32-bit 결과는 항상 정의된 64-bit 값"이라는 일관성 확보.
2. **상수 0을 자주 써야**(비교, 클리어) → 별도 명령 없이 **XZR/WZR**(zero register)을 피연산자로 — `cmp x0, xzr`처럼.
3. **예외가 나도 하위 EL 상태가 오염되면 안 됨** → 예외 처리 레지스터를 **EL별 banked**로 하드웨어 분리.

---

## 3. 작은 예 — 함수 프롤로그가 FP·LR을 저장하는 과정

가장 흔한 시나리오. 함수가 호출되면 다른 함수를 또 호출하기 전에 자신의 복귀 주소(LR=X30)와 프레임 포인터(FP=X29)를 스택에 저장해야 합니다. 이 한 패턴에 레지스터 지식이 응축됩니다.

### 단계별 다이어그램

```d2
direction: down

ENTER: "**함수 진입**\nX30(LR) = 복귀 주소\nX29(FP) = 호출자 프레임"
PRO: "**① 프롤로그 stp**\nstp x29, x30, [sp, #-16]!\nSP -= 16, 그 위치에 두 레지스터 저장\n(pre-index)"
FP: "**② FP 설정**\nmov x29, sp\n현재 프레임 포인터 확정"
BODY: "**함수 본문**\n(다른 함수 호출 → X30 덮어씀)"
EPI: "**③ 에필로그 ldp**\nldp x29, x30, [sp], #16\n두 레지스터 복원 후 SP += 16\n(post-index)"
RET: "**④ ret**\nbranch to X30 (복귀)"

ENTER -> PRO
PRO -> FP
FP -> BODY
BODY -> EPI
EPI -> RET
```

### 단계별 의미

| Step | 명령 | 무엇을 | 왜 |
|---|---|---|---|
| ① | `stp x29, x30, [sp, #-16]!` | FP·LR을 한 번에 push, SP를 먼저 16 감소 | 본문이 X30을 덮어쓰기 전에 복귀 주소 보존 |
| ② | `mov x29, sp` | 프레임 포인터 확정 | 스택 트레이스·지역 변수 기준점 |
| ③ | `ldp x29, x30, [sp], #16` | 복원 후 SP 16 증가 | post-index: 접근 _후_ SP 조정 |
| ④ | `ret` | X30으로 분기 | LR이 복귀 주소를 담음 |

`stp`/`ldp`(store/load pair)는 두 레지스터를 한 명령으로 처리해 프롤로그/에필로그를 짧게 만듭니다. **pre-index**(`[sp, #-16]!`)는 접근 _전_ SP를 조정하고, **post-index**(`[sp], #16`)는 접근 _후_ 조정합니다 — `!`의 유무가 핵심 차이입니다.

### 실제 코드

```asm
foo:
    stp   x29, x30, [sp, #-16]!   // save FP, LR + SP -= 16 (pre-index)
    mov   x29, sp                 // set up frame pointer
    // ... function body (may BL into other functions) ...
    ldp   x29, x30, [sp], #16     // restore + SP += 16 (post-index)
    ret                           // branch to LR (x30)
```

:::note[여기서 잡아야 할 두 가지]
**(1) X30(LR)을 저장하지 않고 다른 함수를 호출하면 복귀 주소를 잃는다.** `BL`이 X30을 새 복귀 주소로 덮어쓰기 때문 — 그래서 프롤로그가 먼저 LR을 스택에 옮긴다.<br>
**(2) pre-index와 post-index는 `!`로 구분된다.** 프롤로그는 보통 pre-index(공간 확보 후 저장), 에필로그는 post-index(복원 후 회수). 순서를 헷갈리면 스택 손상.
:::
---

## 4. 일반화 — GPR · PSTATE · 시스템 레지스터의 전체 지도

### 4.1 General Purpose Registers

AArch64는 총 31개의 범용 레지스터와 전용 레지스터를 둡니다. 32-bit 뷰는 `W` prefix를 씁니다.

```asm
X0  – X30    // 64-bit general purpose (31 regs)
W0  – W30    // low 32-bit view — writes auto zero-extend the upper 32 bits
X30 / LR     // Link Register — BL stores the return address here
XZR / WZR    // Zero Register — reads as 0, writes are discarded
SP           // Stack Pointer (banked per EL: SP_EL0/1/2/3)
PC           // Program Counter — not directly writable (branch only)
```

핵심은 네 가지입니다. **W 쓰기의 zero-extend**(§1의 함정), **X30이 곧 LR**(`BL`이 자동 사용), **XZR/WZR**(읽으면 0, 쓰면 버림 — 결과를 버리고 플래그만 원할 때 유용), **PC는 직접 쓸 수 없고** 분기 명령으로만 바뀝니다.

### 4.2 PSTATE — Process State

PSTATE는 별도 레지스터 파일이 아니라 코어의 **실행 중 상태**를 모은 것으로, 예외가 나면 통째로 SPSR로 저장됩니다.

| Field | Bits | Description |
|-------|------|-------------|
| `N, Z, C, V` | 4 | Negative / Zero / Carry / oVerflow — 조건 플래그 |
| `DAIF` | 4 | Debug · SError · IRQ · FIQ mask |
| `CurrentEL` | 2 | current Exception Level (0 ~ 3) |
| `SPSel` | 1 | select SP_EL0 vs SP_ELx |
| `nRW` | 1 | AArch64 vs AArch32 execution state |

**NZCV**는 비교/연산 결과에 따라 갱신되고 조건 분기(`b.eq`, `b.lt` 등)가 이를 읽습니다. **DAIF**는 인터럽트 마스크로, 비트가 1이면 해당 인터럽트(IRQ/FIQ/SError/Debug)를 막습니다 — 예외 진입 시 HW가 자동으로 전부 1로 세팅합니다(M03에서 확인). **CurrentEL/SPSel/nRW**는 현재 특권 레벨·스택 선택·실행 상태를 나타냅니다.

### 4.3 예외 처리 시스템 레지스터

예외가 발생하면 HW가 자동으로 채우는 레지스터들로, 전부 **EL별로 banked**됩니다(EL1·EL2·EL3가 각자 사본).

```asm
ELR_ELx   // Exception Link Register — PC at the moment of exception
SPSR_ELx  // Saved Program Status — PSTATE at the moment of exception
ESR_ELx   // Exception Syndrome Register — classifies the exception cause
FAR_ELx   // Fault Address Register — address for data/instruction abort
VBAR_ELx  // Vector Base Address — location of the exception vector table
```

이 다섯이 예외 처리의 핵심이며, M03에서 `SVC` 한 번이 이들을 어떻게 채우는지 단계별로 봅니다. 여기서는 "예외가 나면 복귀 PC는 ELR, 옛 PSTATE는 SPSR, 원인은 ESR, 폴트 주소는 FAR, 벡터 테이블 위치는 VBAR"라는 매핑만 잡으면 됩니다.

---

## 5. 디테일 — W 뷰, XZR, banked 레지스터의 실전

### 5.1 W 뷰의 zero-extend — 64-bit 연산과의 차이

```asm
    mov   x0, #0xFFFFFFFFFFFFFFFF  // X0 = all ones
    add   w1, w0, #1              // W1 = 0x00000000 (32-bit overflow), X1 상위 = 0
    add   x2, x0, #1              // X2 = 0x0000000000000000 (64-bit overflow)
    // W 연산은 결과를 32-bit로 자른 뒤 상위 32-bit를 0으로 — X 연산과 결과가 다름
```

W 레지스터로 32-bit 연산을 하면 결과를 32-bit로 계산한 뒤 상위를 0으로 채웁니다. 32-bit 변수를 다루는 C 코드는 W를, 포인터·long을 다루는 코드는 X를 씁니다. 이 둘을 섞으면 §1의 포인터 절단 버그가 납니다.

### 5.2 XZR/WZR — 0을 만드는 별도 비용 없이

```asm
    cmp   x0, xzr            // compare x0 with 0 (XZR reads as 0)
    str   xzr, [x1]          // store 0 to memory (no need to load 0 first)
    add   x2, x3, xzr        // x2 = x3 (move via add)
```

XZR을 읽으면 항상 0, 쓰면 버려집니다. 0과 비교하거나 메모리를 0으로 클리어할 때 별도의 "0 적재" 명령이 필요 없어 코드가 짧아집니다. `mov x2, x3`이 실제로는 `orr x2, xzr, x3`로 인코딩되는 식으로 zero register가 ISA 곳곳에 쓰입니다.

### 5.3 banked 레지스터 — EL별 하드웨어 분리

같은 이름의 시스템 레지스터(`SP_ELx`, `ELR_ELx`, `SPSR_ELx` 등)가 EL마다 **하드웨어적으로 분리**되어, 상위 EL 상태가 하위 EL 진입/복귀에 오염되지 않습니다.

| Register | EL0 | EL1 | EL2 | EL3 | Purpose |
|----------|-----|-----|-----|-----|---------|
| `SP_ELx` | ✓ | ✓ | ✓ | ✓ | stack pointer (banked per EL) |
| `ELR_ELx` | — | ✓ | ✓ | ✓ | return PC |
| `SPSR_ELx` | — | ✓ | ✓ | ✓ | saved PSTATE |
| `ESR_ELx` | — | ✓ | ✓ | ✓ | exception cause (EC, ISS) |
| `FAR_ELx` | — | ✓ | ✓ | ✓ | fault address |
| `VBAR_ELx` | — | ✓ | ✓ | ✓ | vector-table base |
| `SCTLR_ELx` | — | ✓ | ✓ | ✓ | MMU / cache / endian control |
| `TTBR0_ELx` | — | ✓ | ✓ | ✓ | page-table base |
| `TCR_ELx` | — | ✓ | ✓ | ✓ | translation control |

EL0는 대부분 읽기조차 불가합니다. `CurrentEL`, `DAIF`, `NZCV`는 PSTATE의 일부로 별도 banking 없이 실행 중 값입니다. banking 덕분에 nested 예외(EL1 핸들러 도중 EL2로 trap)에서도 각 EL의 ELR/SPSR이 섞이지 않습니다.

### 5.4 시스템 레지스터 접근 — MRS/MSR

```asm
    mrs   x0, sctlr_el1      // MRS: 시스템 레지스터 → GPR (read)
    orr   x0, x0, #1         // SCTLR_EL1.M = 1 (MMU enable bit)
    msr   sctlr_el1, x0      // MSR: GPR → 시스템 레지스터 (write)
    isb                      // 필수! M04 참조 — 파이프라인 재-fetch
```

시스템 레지스터는 일반 GPR과 달리 `MRS`(읽기)/`MSR`(쓰기) 전용 명령으로만 접근하며, EL0에서는 대부분 차단됩니다. `MSR`로 MMU나 인터럽트 마스크 같은 실행 환경을 바꾼 직후에는 `ISB`가 필요한데(M04에서 상세), 이미 파이프라인에 fetch된 명령이 옛 컨텍스트로 실행되는 것을 막기 위함입니다.

---

## 6. 흔한 오해 와 DV 디버그 체크리스트

### 흔한 오해

:::danger[❓ 오해 1 — 'W0에 쓰면 X0의 상위 32-bit는 그대로 남는다']
**실제**: W 레지스터에 쓰면 대응 X 레지스터의 **상위 32-bit가 자동으로 0**이 됩니다. 64-bit 포인터를 들고 있던 X에 실수로 W를 쓰면 상위 주소가 통째로 날아갑니다.<br>
**왜 헷갈리는가**: x86의 32-bit 레지스터(EAX)도 RAX 상위를 0으로 하지만, AArch32(ARMv7)는 그렇지 않아 ARM 경험자가 더 헷갈림. AArch64는 zero-extend가 규칙.
:::
:::danger[❓ 오해 2 — 'PC를 직접 레지스터처럼 쓸 수 있다']
**실제**: AArch64에서 PC는 GPR이 아니며 직접 쓸 수 없습니다. 분기 명령(`B`, `BL`, `BR`, `RET`)으로만 바뀝니다. (AArch32에서는 PC=R15로 직접 조작이 가능했어서 혼동.)<br>
**왜 헷갈리는가**: ARMv7 경험 + "PC도 레지스터"라는 일반론.
:::
:::danger[❓ 오해 3 — 'XZR과 SP는 같은 인코딩이라 항상 같다']
**실제**: 인코딩 번호(31)는 공유하지만 명령에 따라 31번이 XZR로 해석되기도 SP로 해석되기도 합니다. `add x0, x1, x31`은 문맥상 SP일 수도, ZR일 수도 — 어셈블러가 명령별 규칙으로 결정합니다.<br>
**왜 헷갈리는가**: 둘 다 "31번"이라 같은 레지스터로 착각.
:::
:::danger[❓ 오해 4 — 'ELR/SPSR은 소프트웨어가 채워야 한다']
**실제**: 예외 진입 시 HW가 ELR(복귀 PC)과 SPSR(옛 PSTATE)을 **자동으로** 채웁니다. 소프트웨어는 nested 예외에 대비해 이를 스택에 추가 저장할 뿐입니다(M03).<br>
**왜 헷갈리는가**: "저장은 SW 책임"이라는 일반화 — 실제로는 이 4개는 HW 자동.
:::

### DV 디버그 체크리스트 (이 모듈 내용으로 마주칠 첫 함정들)

| 증상 | 1차 의심 | 어디 보나 |
|---|---|---|
| 64-bit 포인터의 상위가 0이 됨 | W 레지스터 쓰기로 인한 zero-extend | 해당 레지스터에 `mov w`, `add w` 등 W 연산 |
| 조건 분기가 의도와 반대로 감 | NZCV 플래그 갱신 시점/명령 오해 (`cmp` 후 `adds`로 덮어씀) | 분기 직전 플래그를 set하는 명령 |
| 예외 핸들러에서 복귀 주소가 이상 | ELR을 읽기 전에 다른 예외/명령이 덮음, 또는 EL 혼동 | `ELR_ELx`의 x가 진입 EL과 일치하는지 |
| 컨텍스트 스위치 후 스택 깨짐 | SP_ELx banking 혼동 (SPSel 설정) | PSTATE.SPSel, 사용 중인 SP가 EL0인지 ELx인지 |
| `MSR` 후 동작이 안 바뀜 | ISB 누락으로 옛 컨텍스트 실행 | `msr` 다음에 `isb`가 있는지 (M04) |
| EL0에서 sysreg 읽기가 트랩 | EL0는 대부분 시스템 레지스터 접근 불가 | 해당 레지스터의 최소 접근 EL |

---

## 7. 핵심 정리 (Key Takeaways)

- **X(64) / W(32) 이중 뷰**: W에 쓰면 상위 32-bit가 자동 zero-extend — 포인터 절단 버그의 단골 원인.
- **X30 = LR**: `BL`이 복귀 주소를 여기 저장. 함수 프롤로그가 다른 호출 전에 LR을 스택으로 옮기는 이유.
- **XZR/WZR**: 읽으면 0, 쓰면 버림 — 0 비교·클리어·move를 별도 비용 없이.
- **PSTATE**: NZCV(조건 플래그)·DAIF(인터럽트 마스크)·CurrentEL/SPSel/nRW. 예외 시 통째로 SPSR로 저장.
- **예외 5레지스터**: ELR(복귀 PC)·SPSR(옛 PSTATE)·ESR(원인)·FAR(폴트 주소)·VBAR(벡터 베이스) — HW 자동, EL별 banked.
- **`stp/ldp` + pre/post-index**: 두 레지스터 한 번에, `!`로 pre/post 구분 — 프롤로그/에필로그의 표준형.

:::caution[실무 주의점]
- waveform/ISS 로그 비교 시 **X 뷰와 W 뷰를 혼동하지 말 것** — 32-bit 결과는 상위가 0인 64-bit 값.
- 예외 디버그 시 **ELR/SPSR의 EL 인덱스**가 진입 EL과 맞는지 먼저 확인 — `ELR_EL1`과 `ELR_EL2`는 다른 레지스터.
- `MSR`로 시스템 레지스터를 바꾸면 동작 확인 전에 **ISB 유무**를 본다(M04).
:::
### 7.1 자가 점검

:::tip[🤔 Q1 — W 뷰 zero-extend (Bloom: Analyze)]
`X0 = 0x1234_5678_9ABC_DEF0`인 상태에서 `add w0, w0, #0` 한 줄을 실행하면 X0은 어떻게 되나? 왜?
<details>
<summary>정답</summary>

`X0 = 0x0000_0000_9ABC_DEF0`이 됩니다.
- `add w0, w0, #0`은 W0(하위 32-bit = `0x9ABC_DEF0`)에 0을 더해 W0에 다시 씁니다.
- W 레지스터 쓰기는 대응 X의 **상위 32-bit를 0으로 zero-extend** → 상위 `0x1234_5678`이 날아감.
- "0을 더하니 변화 없겠지"가 함정 — 값이 아니라 _뷰_ 가 바뀌어 상위가 지워짐.
- 검증 단서: 포인터(X)에 의도치 않게 W 연산이 끼면 상위 주소가 0이 되는 mismatch.

</details>
:::
:::tip[🤔 Q2 — banked 레지스터의 가치 (Bloom: Evaluate)]
ELR/SPSR이 EL별로 banked되지 않고 전 EL이 하나를 공유한다면 어떤 문제가 생기나?
<details>
<summary>정답</summary>

nested 예외에서 복귀 정보가 파괴됩니다.
- EL1 핸들러 실행 중 EL2로 trap(예: hypervisor)이 나면, 공유 ELR이라면 EL2 진입이 EL1의 복귀 PC를 덮어씀 → EL2에서 돌아올 때 EL1이 자기 복귀 주소를 잃음.
- banking 덕분에 `ELR_EL1`과 `ELR_EL2`가 별개라서 각 EL이 자기 복귀 정보를 독립 보존.
- 대안(공유 + SW 저장)도 가능하지만, 진입마다 SW가 저장/복원해야 해 비용·버그 위험 증가. HW banking이 이를 자동화.
- 결론: banking은 nested trap의 정확성을 HW가 보장하는 메커니즘.

</details>
:::
### 7.2 출처

**Internal**
- [Module 01 — 개요 & ISA](../01_overview_isa/) — 31 GPR을 택한 RISC 설계 근거
- [Module 03 — Exception Level](../03_exception_levels/) — ELR/SPSR/ESR이 예외 진입 시 채워지는 흐름

**External**
- *Arm Architecture Reference Manual for A-profile (ARM ARM, DDI 0487)* §C5 (System registers), §C1.2 (PSTATE) — (외부 표준 지식)
- *Procedure Call Standard for the Arm 64-bit Architecture (AAPCS64)* — Arm Ltd. (프롤로그/에필로그·인자 규약)

---

## 다음 모듈

→ [Module 03 — Exception Level](../03_exception_levels/): EL0–EL3 특권 모델과 `SVC`/`HVC`/`SMC`/`ERET` — 이 모듈의 ELR/SPSR/ESR/VBAR이 예외 진입 시 _어떻게_ 채워지고 핸들러가 _어떻게_ 복귀하는지를 본다.

[퀴즈 풀어보기 →](../quiz/02_registers_pstate_quiz/)
