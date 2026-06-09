---
title: "Module 03 — Exception Level (EL0–EL3)"
---

:::tip[학습 목표]
이 모듈을 마치면:

- **Describe** EL0–EL3 네 특권 레벨과 각 레벨에서 무엇이 돌고 무엇을 할 수 없는지 기술할 수 있다.
- **Trace** EL0의 `SVC` 한 번이 어느 벡터 엔트리로 들어가고 HW가 ELR/SPSR/ESR을 어떻게 자동 저장하는지 단계별로 추적할 수 있다.
- **Explain** `SVC`/`HVC`/`SMC`/`ERET`이 어느 EL로 전환하며 `ERET`이 왜 한 명령으로 PC·PSTATE·EL을 복원하는지 설명할 수 있다.
- **Analyze** 벡터 테이블이 (소스 EL, 스택 선택, 예외 타입)으로 16개 엔트리 × 0x80 바이트로 인덱싱되는 구조를 분석할 수 있다.
- **Decode** ESR_ELx의 EC 필드로 예외 원인(SVC/data abort/sysreg trap)을 분기하는 핸들러 패턴을 해독할 수 있다.
:::
:::note[사전 지식]
- [Module 02 — 레지스터 & PSTATE](../02_registers_pstate/) (ELR/SPSR/ESR/FAR/VBAR, PSTATE의 DAIF)
- 인터럽트·시스템 콜의 일반 개념
:::
---

## 1. Why care? — "어느 권한에서 무엇이 허용되나"가 모든 trap의 출발점

### 1.1 시나리오 — 유저 앱이 `MSR`로 MMU를 끄려 하다 trap

검증 중인 SoC에서 EL0(유저 모드)의 테스트 코드가 `msr sctlr_el1, x0`로 MMU를 끄려 했더니, 그 명령이 실행되는 대신 EL1 커널로 예외가 튀어 ESR에 "MSR/MRS trap"이 기록되는 현상을 봤다고 합시다. 이것은 버그가 아니라 **특권 모델**이 정확히 의도대로 동작한 것입니다.

```
EL0 (user):  msr sctlr_el1, x0   // 시스템 레지스터 쓰기 시도
                  │
                  ▼  권한 없음 → trap
EL1 (kernel): VBAR_EL1 + 0x400   // "Lower EL Sync" 벡터로 진입
              ESR_EL1.EC = 0x18  // "MSR/MRS system register trap"
```

AArch64는 4개의 Exception Level을 두고, 숫자가 높을수록 높은 특권을 가집니다. 하위 EL은 상위 EL의 리소스(레지스터·메모리·인터럽트 설정)를 **직접** 건드릴 수 없고, 오직 동기 예외(`SVC`/`HVC`/`SMC`)나 비동기 이벤트(IRQ/FIQ/SError)로만 상위로 올라갑니다.

이 모듈은 검증에서 **거의 모든 trap·syscall·하이퍼바이저 동작의 기반**입니다. "이 명령이 왜 trap했나", "syscall이 어느 핸들러로 갔나", "VM이 어떻게 격리되나"를 EL 모델 없이는 설명할 수 없습니다. 펌웨어/OS가 끼인 SoC 검증에서 EL 전환 추적은 필수 능력입니다.

---

## 2. Intuition — 동심원의 권한, 그리고 한 장 그림

:::tip[💡 한 줄 비유]
**Exception Level** ≈ **건물의 출입 권한 등급**.<br>
EL0은 로비(누구나, 권한 없음), EL1은 사무실(직원=커널), EL2는 관리실(하이퍼바이저), EL3은 보안실(secure monitor). 위층으로 올라가려면 _정해진 문_(`SVC`/`HVC`/`SMC`)을 통해 _경비_(HW)에게 신원과 용건을 남기고(ELR/SPSR/ESR) 올라가야 하며, 내려올 땐 _한 번의 동작_(`ERET`)으로 원래 자리·상태로 복귀합니다.
:::
### 한 장 그림 — 네 EL과 전환 명령

```d2
direction: up

EL0: "**EL0** — User / App\n유저 프로세스 · 권한 없음\nSP_EL0, 모든 HW 요청은 SVC 경유" {
  style.fill: "#e8f0fe"
}
EL1: "**EL1** — OS Kernel\nLinux/RTOS · 드라이버\nSCTLR/TTBR/VBAR_EL1, syscall 디스패치" {
  style.fill: "#e6f4ea"
}
EL2: "**EL2** — Hypervisor\nKVM/Xen · stage-2 translation\nHCR_EL2, VTTBR_EL2, VMID" {
  style.fill: "#fef7e0"
}
EL3: "**EL3** — Secure Monitor\nTrustZone · TF-A · PSCI\nSCR_EL3.NS — 유일한 월드 스위치" {
  style.fill: "#fce8e6"
}

EL0 -> EL1: "SVC #imm (syscall)"
EL1 -> EL2: "HVC #imm (hypercall)"
EL0 -> EL3: "SMC #imm (any → EL3)"
EL1 -> EL0: "ERET (복귀)"
EL2 -> EL1: "ERET"
EL3 -> EL2: "ERET (월드 스위치 후)"
```

### 왜 이 디자인인가 — Design rationale

세 가지 요구가 이 4단 모델을 만듭니다.

1. **유저 앱이 커널을 망가뜨리면 안 됨** → EL0/EL1 분리, EL0은 시스템 레지스터·MMU·인터럽트 설정 불가, HW 요청은 `SVC` 경유.
2. **한 물리 머신에 여러 OS를 격리해야**(클라우드) → EL2 하이퍼바이저 + **stage-2 translation**(게스트가 본 "물리 주소"를 한 번 더 번역).
3. **OS조차 신뢰할 수 없는 비밀이 있어야**(키, DRM) → EL3 secure monitor + **Secure/Non-secure 월드**(TrustZone). EL3만 `SCR_EL3.NS`로 월드를 가름.

각 요구가 한 층씩 쌓여 EL0(격리 대상) → EL1(OS) → EL2(가상화) → EL3(신뢰 루트)의 동심원이 됩니다.

:::note[AArch32 의 mode-banked vs AArch64 의 EL-banked — 왜 모델을 바꿨나]
AArch64 가 EL별 banked 레지스터(`SP_ELx`, `ELR_ELx` 등, M02)를 쓰는 것과 달리, 구식 AArch32(ARMv7)는 **processor mode 별 banked 레지스터** 모델이었습니다 — User/FIQ/IRQ/Supervisor/Abort 등 _모드_ 마다 일부 레지스터(특히 FIQ 모드는 r8–r14 를 전용으로 banking)를 따로 두어, 모드 전환 시 그 레지스터들이 자동으로 바뀌었습니다. FIQ 가 r8–r14 전용 사본을 가져 빠른 인터럽트 응답에서 레지스터 저장을 줄이려는 설계였습니다.

AArch64 가 이 _mode-banked_ 를 _EL-banked_ 로 바꾼 이유는, 격리의 기준이 "인터럽트 모드"가 아니라 "_특권 레벨_"이라는 데 있습니다. 가상화·보안이 EL2/EL3 로 계층화되면서, 무엇을 분리해야 하는지가 모드가 아니라 EL 경계가 됐고, EL별 banking 이 nested 예외에서 각 특권 레벨의 복귀 상태(ELR/SPSR)를 깔끔히 분리합니다(M02 Q2). 본 코스는 AArch64 에 집중하므로 mode-banked 는 "구식 모델이 있었고 EL-banked 로 진화했다"는 맥락까지만 잡으면 충분합니다.
:::

---

## 3. 작은 예 — `write()` 시스템 콜이 EL0에서 EL1로 들어가는 과정

가장 흔한 시나리오. 유저 앱이 `write(1, msg, 13)`을 호출하면 결국 `SVC`가 실행되어 커널로 진입합니다. 이 한 경로에 EL 전환의 모든 메커니즘이 담깁니다.

### 단계별 다이어그램

```d2
direction: down

USER: "**① EL0 — user**\nx8 = 64 (write 번호)\nx0/x1/x2 = 인자\nsvc #0"
HW: "**② HW 자동 (예외 진입)**\nELR_EL1 ← svc 다음 PC\nSPSR_EL1 ← PSTATE\nESR_EL1 ← {EC=0x15, ISS=imm16}\nDAIF←1111, SPSel←1, CurrentEL←01\nPC ← VBAR_EL1 + 0x400"
VEC: "**③ 벡터 엔트리 @ +0x400**\n(Lower EL, AArch64, Sync)\nkernel_entry: X0–X30 스택 저장"
DISP: "**④ ESR.EC 디코드**\nEC=0x15 → do_svc\nsys_call_table[x8] 호출"
RET: "**⑤ ret_to_user → ERET**\nELR/SPSR 복원\nPC←ELR_EL1, PSTATE←SPSR_EL1\nEL1 → EL0 복귀"

USER -> HW
HW -> VEC
VEC -> DISP
DISP -> RET
```

### 단계별 의미

| Step | 누가 | 무엇을 | 왜 |
|---|---|---|---|
| ① | EL0 user | `x8`=syscall#, 인자 세팅 후 `svc #0` | syscall 진입 명령 |
| ② | HW (자동) | ELR/SPSR/ESR 저장, DAIF 마스크, EL 상승, PC←VBAR+0x400 | 복귀 정보 보존 + 안전한 진입 |
| ③ | 커널 핸들러 | X0–X30을 스택에 dump | HW는 4레지스터만 저장 — GPR은 SW 책임 |
| ④ | 커널 | `ESR.EC`로 분기, syscall 테이블 호출 | EC가 예외 종류를 분류 |
| ⑤ | 커널 → HW | `ERET` 한 명령으로 PC·PSTATE·EL 복원 | 우아한 단일 명령 복귀 |

### 실제 코드

```asm
// ① EL0 (user)
    mov   x8, #64             // syscall # (Linux aarch64: 64 = write)
    mov   x0, #1              // fd = stdout
    adr   x1, msg            // buf
    mov   x2, #13             // count
    svc   #0                 // → EL1 vector @ VBAR_EL1 + 0x400
    // returns: x0 = bytes written or -errno

// ④ EL1 (kernel) — dispatch
do_svc:
    mov   x21, x8                       // syscall #
    cmp   x21, #__NR_syscalls
    b.hs  invalid_syscall
    adrp  x22, sys_call_table
    add   x22, x22, :lo12:sys_call_table
    ldr   x22, [x22, x21, lsl #3]
    blr   x22                           // indirect call to sys_write
    b     ret_to_user                   // restores x0, ERET
```

```asm
// ② HW가 자동으로 하는 일 (pseudo code)
//   1. ELR_EL1  ← next PC          // address after SVC
//   2. SPSR_EL1 ← current PSTATE   // NZCV, DAIF, CurrentEL, SPSel ...
//   3. ESR_EL1  ← {EC=0x15, ISS=imm16}  // EC=0x15 = SVC from AArch64
//   4. PSTATE.DAIF ← 1111          // mask all interrupts
//   5. PSTATE.SPSel ← 1            // use SP_EL1
//   6. PSTATE.CurrentEL ← 01       // EL1
//   7. PC ← VBAR_EL1 + 0x400       // Lower-EL AArch64 Sync vector
```

:::note[여기서 잡아야 할 두 가지]
**(1) HW는 4개만 자동 저장한다 — ELR, SPSR, ESR (+ data/inst abort면 FAR).** X0–X30/V0–V31은 SW가 직접 저장해야 하므로, 벡터 엔트리의 첫 일이 GP 레지스터 dump입니다.<br>
**(2) `ERET` 한 명령이 PC=ELR, PSTATE=SPSR, EL 변경, 인터럽트 마스크 복원을 모두 한다.** 게다가 context sync까지 포함해 ISB가 불필요 — SW가 수동으로 플래그를 되돌릴 필요가 없습니다.
:::
---

## 4. 일반화 — 네 EL의 책임, 전환 명령, 벡터 테이블

### 4.1 네 EL의 역할

| EL | 무엇이 도나 | 할 수 없는 것 / 핵심 자원 |
|----|------------|--------------------------|
| **EL0** User | 유저 프로세스 (셸, 브라우저, DB) — `execve`가 로드한 ELF의 `_start` | 시스템 레지스터 접근·인터럽트 마스킹·MMU 설정 불가, HW 요청은 `SVC` 경유. `SP_EL0`, `TTBR0_EL1`(유저 VA)만 |
| **EL1** Kernel | 스케줄링·가상 메모리(stage-1)·드라이버·syscall 디스패치 | `SCTLR_EL1`, `TTBR0/1_EL1`, `TCR_EL1`, `MAIR_EL1`, `VBAR_EL1` |
| **EL2** Hypervisor | KVM/Xen·VM 관리·stage-2 translation(IPA→PA) | `HCR_EL2`(트랩 구성), `VTTBR_EL2`, VMID(VM 구분 TLB 태그), VHE(`E2H`) |
| **EL3** Secure Monitor | TrustZone·TF-A·PSCI·월드 스위치 | `SCR_EL3.NS`(유일한 월드 전환), `MDCR_EL3`, OTP 키 검증 = Root of Trust |

**TTBR 분리**가 EL1의 핵심 최적화입니다. `TTBR0_EL1`은 유저 공간(VA 상위 비트 0), `TTBR1_EL1`은 커널 공간(VA 상위 비트 1)이라, 컨텍스트 스위치 때 TTBR0만 바꾸면 되어 TLB invalidate가 경량화됩니다(ASID로 더 최적화). 페이지 테이블 일반 원리는 [MMU](../../mmu/), ARM stage-1/2 세부는 M05에서 다룹니다.

#### VHE(Virtualization Host Extensions) — 왜 호스트 커널을 EL2 에서 돌리나

부팅 흐름과 EL2 자원 표에 `VHE(E2H)` 가 등장하는데, 이것이 왜 도입됐는지를 인과로 풀면 가상화 구조가 명확해집니다. 문제는 **type-2 hypervisor**(호스트 OS 위에서 도는 KVM 같은 하이퍼바이저)의 위치였습니다. 원래 설계에서 호스트 OS 커널은 EL1, 하이퍼바이저 로직은 EL2 였습니다. 그런데 KVM 처럼 호스트 _커널의 일부_ 가 하이퍼바이저인 경우, 같은 커널이 일반 OS 일은 EL1 에서, 가상화 일은 EL2 에서 처리해야 해 **EL1↔EL2 를 빈번히 오가는** 구조가 됩니다. 이 전환마다 시스템 레지스터 컨텍스트를 바꾸는 비용이 누적됩니다.

**VHE(Virtualization Host Extensions, `HCR_EL2.E2H` 비트로 활성)** 는 이를 해결합니다 — 호스트 OS 커널 _전체를 EL2 에서 직접_ 돌릴 수 있게 합니다. VHE 가 켜지면 EL2 가 EL1 처럼 보이도록 시스템 레지스터 접근이 재매핑되어(예: 커널이 쓰는 `TTBR0_EL1` 류 접근이 EL2 의 대응 레지스터로 자동 라우팅), 호스트 커널을 거의 수정 없이 EL2 에서 실행하면서 _EL1↔EL2 왕복 자체를 없앱니다._ 결과적으로 type-2 하이퍼바이저의 전환 오버헤드가 크게 줄고, 게스트는 여전히 EL1/EL0 에서 격리되어 돕니다. 즉 VHE 는 "호스트 커널의 자연스러운 위치(EL1)와 하이퍼바이저의 권한 위치(EL2)가 어긋나 생기던 전환 비용"을 _호스트를 EL2 로 끌어올려_ 해소한 확장입니다.

### 4.2 EL 전환 명령

| Instruction | Target | Purpose |
|-------------|--------|---------|
| `SVC #imm` | EL0 → EL1 | Syscall (Linux syscall entry) |
| `HVC #imm` | EL1 → EL2 | Hypervisor call (KVM guest→host) |
| `SMC #imm` | Any → EL3 | Secure Monitor call (e.g. PSCI) |
| `ERET` | ELx → ELy | restore SPSR/ELR and return to a lower EL |

`SVC`/`HVC`/`SMC`는 모두 **SMCCC**(Arm Secure Monitor Call Calling Convention)라는 표준 ABI를 따릅니다 — function ID 인코딩, fast/yielding 구분 등. 단순한 레지스터 전달이 아니라 규약이 있다는 점이 핵심입니다.

#### trap 을 어느 EL 로 보낼지는 _설정 가능_ 하다 — HCR_EL2 / SCR_EL3

지금까지 "하위 EL 이 권한 없는 동작을 하면 상위로 trap 한다"고 했는데, 핵심은 **_어느_ 상위 EL 로 trap 할지가 비트로 설정 가능**하다는 점입니다. 이것이 가상화와 보안의 작동 원리 그 자체입니다. 특정 예외·명령·시스템 레지스터 접근을 어디서 가로챌지가 두 개의 제어 레지스터로 정해집니다.

- **`HCR_EL2`(Hypervisor Configuration Register)**: EL2(하이퍼바이저)가 _게스트(EL1/EL0)의 무엇을 가로챌지_ 를 비트별로 켭니다. 예를 들어 특정 비트를 켜면 게스트의 어떤 시스템 레지스터 접근·특정 명령·심지어 일반 IRQ 가 _EL1 대신 EL2 로_ trap 됩니다. 하이퍼바이저는 이렇게 _자기가 가상화하고 싶은 것만 선택적으로_ 가로채(emulate) 게스트에게는 진짜 하드웨어를 가진 것처럼 보이게 합니다 — 가로채지 않은 것은 게스트가 직접 처리해 빠릅니다.
- **`SCR_EL3`(Secure Configuration Register)**: EL3(secure monitor)가 _어떤 예외/인터럽트를 EL3 로 끌어올릴지_, 그리고 Secure/Non-secure 월드(`SCR_EL3.NS`)를 제어합니다. 보안에 민감한 이벤트를 EL3 로 라우팅해 신뢰 경계를 지킵니다.

이 "configurable routing"이 핵심 메커니즘인 이유: 만약 trap 대상이 고정이었다면 하이퍼바이저는 게스트의 _모든_ 특권 동작을 떠안거나 _아무것도_ 못 가로채는 양극단뿐이었을 것입니다. 비트 단위로 켜고 끌 수 있기에, 하이퍼바이저는 "타이머는 가상화하되 산술은 그대로 통과" 같은 _세밀한 가상화 정책_ 을 구현하고, secure monitor 는 "이 인터럽트만 secure 로" 같은 _보안 정책_ 을 구현합니다. §1 에서 EL0 의 `msr sctlr_el1` 이 EL1 로 trap 된 것도 이런 routing 규칙의 한 사례이며, 검증에서 "왜 이 동작이 _이_ EL 로 trap 됐나"가 의아하면 `HCR_EL2`/`SCR_EL3` 의 해당 trap-enable 비트를 봐야 합니다.

### 4.3 벡터 테이블 — 16 엔트리 × 0x80 바이트

`VBAR_ELx`가 가리키는 0x800 바이트 테이블로, 16개 엔트리가 각 0x80 바이트입니다. 엔트리는 **(소스 EL, 스택 선택, 예외 타입)** 조합으로 인덱싱됩니다.

```asm
// VBAR_EL1 + offset
0x000  Current EL, SP0, Sync
0x080  Current EL, SP0, IRQ
0x100  Current EL, SP0, FIQ
0x180  Current EL, SP0, SError
0x200  Current EL, SPx, Sync          // EL1→EL1 (data abort 등)
0x280  Current EL, SPx, IRQ
0x400  Lower EL (AArch64), Sync       // ← SVC from EL0 lands here
0x480  Lower EL (AArch64), IRQ
0x500  Lower EL (AArch64), FIQ
0x580  Lower EL (AArch64), SError
0x600  Lower EL (AArch32), Sync       // 32-bit guests
// ... 16 entries total, 0x80 bytes each (up to 32 instructions)
```

§3의 `SVC` from EL0이 정확히 `+0x400`(Lower EL, AArch64, Sync)로 들어가는 이유가 이 인덱싱입니다. 엔트리당 0x80 바이트(최대 32명령) 제한이 있어, 긴 핸들러는 여기서 레지스터 저장만 하고 `b`로 C 핸들러로 점프하는 것이 관례입니다.

#### 왜 슬롯 크기가 0x80 으로 고정인가 — 분기 없는 진입과 trampoline 강제

벡터 슬롯이 _가변_ 이 아니라 _고정 0x80 바이트_ 인 데는 인덱싱을 단순하게 만드는 인과가 있습니다. 예외가 났을 때 하드웨어는 "어느 핸들러로 갈지"를 _최대한 빨리, 분기 없이_ 정해야 합니다. 슬롯이 고정 크기면 진입 주소를 `VBAR_ELx + (슬롯번호 << 7)` 처럼 **단순 shift+add 로 계산**할 수 있습니다(0x80 = 128 = `1<<7`). 만약 슬롯 크기가 핸들러마다 다르면, 어디가 어느 핸들러의 시작인지 _테이블을 한 번 더 조회_ 하거나 분기 계산을 해야 해, 예외 진입이라는 critical 한 경로가 느려집니다. 고정 크기는 이 조회를 _산술 한 번_ 으로 대체합니다.

그 대가로 0x80 바이트(최대 32명령)라는 _좁은 공간_ 이 강제되고, 이것이 핸들러를 **trampoline 패턴**으로 몰아갑니다 — 슬롯 안에는 GPR 저장과 _진짜 핸들러로 점프하는 `b`_ 정도만 두고, 실제 처리 로직은 슬롯 바깥의 C 함수에 둡니다(§5.1 의 `kernel_entry` → `bl do_*` 구조가 정확히 이것). 즉 고정 슬롯 크기는 "진입을 분기 없는 산술로 빠르게"라는 이득과 "긴 핸들러를 못 담아 trampoline 으로 점프해야 함"이라는 제약을 동시에 만든 설계 결정이며, 검증에서 핸들러가 슬롯 경계(0x80)를 넘어 _다음 슬롯을 침범_ 하면 엉뚱한 예외 진입이 되므로 슬롯 크기 준수를 확인해야 합니다.

---

## 5. 디테일 — 핸들러 entry, ESR 디코드, ERET, 부팅 흐름

### 5.1 핸들러 entry 패턴 — 저장 후 분기

```asm
.macro kernel_entry
    sub   sp, sp, #272          // frame for X0~X30 + extras
    stp   x0, x1, [sp, #0]
    stp   x2, x3, [sp, #16]
    // ... save x4 ~ x29 ...
    stp   x29, x30, [sp, #240]
    mrs   x21, elr_el1
    mrs   x22, spsr_el1
    stp   x21, x22, [sp, #256]   // save ELR/SPSR for nested traps
.endm

vector_sync_lower_el64:
    kernel_entry
    mov   x0, sp                 // pass register frame to C
    bl    do_sync_handler
    b     ret_to_user
```

이 패턴이 Linux 커널 `arch/arm64/kernel/entry.S`의 본질입니다. `kernel_entry` 매크로(GPR + ELR/SPSR 저장) → C 핸들러 호출 → `kernel_exit` 복원 → `ERET`. ELR/SPSR을 스택에 추가 저장하는 이유는 nested trap(핸들러 도중 또 예외) 대비입니다.

### 5.2 ESR_ELx 디코드 — EC가 분기의 핵심

ESR_ELx은 **EC**(Exception Class, 6-bit) + **IL**(Instruction Length) + **ISS**(Instruction-Specific Syndrome, 25-bit)로 구성됩니다. EC가 큰 분류, ISS가 그 안의 세부입니다.

| EC | 의미 | ISS 활용 |
|----|------|----------|
| `0x15` | SVC from AArch64 (syscall) | imm16 = syscall # |
| `0x16` | HVC from AArch64 | hypercall # |
| `0x17` | SMC from AArch64 | secure-call # |
| `0x18` | MSR/MRS/system register access trap | which register |
| `0x20 / 0x21` | Instruction abort (lower / same EL) | FAR_EL1 = faulting address |
| `0x24 / 0x25` | Data abort (lower / same EL) | FAR_EL1, DFSC = fault code |
| `0x2F` | SError | impl-defined |

```asm
do_sync_handler:
    mrs   x0, esr_el1
    lsr   x1, x0, #26            // EC = ESR[31:26]
    cmp   x1, #0x15
    b.eq  do_svc
    cmp   x1, #0x24
    b.eq  do_data_abort
    // ... cascade or jump-table dispatch ...
```

data abort(EC=0x24/0x25)면 ISS 안에 다시 **DFSC**(Data Fault Status Code, 6-bit)가 들어 있어 fault 종류(translation/access flag/permission/alignment)를 식별합니다. 읽는 순서는 "ESR >> 26 = EC로 분기 → ISS & 0x3F = DFSC로 페이지 폴트 종류"입니다.

```asm
do_data_abort:
    mrs   x0, esr_el1
    mrs   x1, far_el1           // faulting VA
    and   x2, x0, #0x3F         // ISS.DFSC — fault status code
    //   0x04~0x07  Translation fault (level 0~3)
    //   0x08~0x0B  Access flag fault
    //   0x0C~0x0F  Permission fault
    //   0x21       Alignment fault
    bl    handle_mm_fault       // VMA lookup, on-demand alloc, etc.
```

### 5.3 ERET — 한 명령 복귀

```asm
ret_to_user:
    ldp   x21, x22, [sp, #256]
    msr   elr_el1, x21          // PC to return to
    msr   spsr_el1, x22         // PSTATE to restore
    // ... restore X0~X30 ...
    add   sp, sp, #272
    eret                        // PC ← ELR_EL1, PSTATE ← SPSR_EL1, EL drops
```

`ERET`의 우아함은 **한 명령으로** PC + PSTATE 복원 + EL 변경 + 인터럽트 마스크 복구 + context sync를 모두 한다는 데 있습니다(ISB 불필요). 잘못된 SPSR로 `ERET`하면 **illegal exception return**이 되어 또 trap합니다.

### 5.4 부팅 흐름 — EL을 가로지르는 여정

```asm
// Reset → EL3 → ... → EL0
//  EL3 / BL1 (BootROM)      : CPU/memory bring-up, verify BL2
//  EL3 / BL2                : init DRAM, load BL31/BL33
//  EL3 / BL31 (resident)    : install PSCI + world-switch, ERET → NS EL2
//  EL2 / BL33 (U-Boot/UEFI) : load kernel image
//  EL2 / Linux head         : (stays under VHE) KVM init or drop to EL1
//  EL1 / start_kernel       : execve init process
//  EL0 / /sbin/init → systemd → userland
```

부팅은 최고 특권 EL3에서 시작해 점점 낮은 EL로 내려갑니다(`ERET`로). EL3의 TF-A(Arm Trusted Firmware)가 PSCI(전원 제어)와 월드 스위치를 상주시켜 이후 `SMC`를 서비스합니다 — EL3가 신뢰 부팅 체인의 최상단(Root of Trust)인 이유입니다. 보안 부팅 심화는 [ARM Security](../../arm_security/)에서 다룹니다.

### 5.5 GIC 인터럽트 경로 — 비동기 진입의 예

```asm
vector_irq_lower_el64:          // IRQ from EL0 lands @ +0x480
    kernel_entry
    mrs   x0, ICC_IAR1_EL1      // acquire INTID (interrupt acknowledge)
    cmp   w0, #1023
    b.eq  spurious              // 1023 = no pending
    bl    handle_irq
    msr   ICC_EOIR1_EL1, x0     // EOI: drop priority
    b     ret_to_user
```

IRQ는 동기 예외(`SVC`)와 달리 명령과 무관하게 _비동기_ 로 발생하지만, 벡터 테이블 진입·자동 저장·`ERET` 복귀의 메커니즘은 동일합니다. `EOIR1`로 처리 완료(EOI)를 신호하지 않으면 GIC가 다음 우선순위 IRQ를 못 보내 dead-lock — GIC 세부는 M06에서 다룹니다.

---

## 6. 흔한 오해 와 DV 디버그 체크리스트

### 흔한 오해

:::danger[❓ 오해 1 — '예외가 나면 HW가 모든 레지스터를 저장한다']
**실제**: HW는 **ELR, SPSR, ESR (+ abort면 FAR) 네 개만** 자동 저장합니다. X0–X30/V0–V31은 SW(벡터 핸들러)가 직접 스택에 저장해야 합니다 — 그래서 벡터 엔트리 첫 일이 GPR dump.<br>
**왜 헷갈리는가**: x86의 일부 자동 push나 "예외=전체 컨텍스트 저장"이라는 일반론 때문에.
:::
:::danger[❓ 오해 2 — '벡터 엔트리에 긴 핸들러를 둘 수 있다']
**실제**: 한 엔트리는 **0x80 바이트(최대 32명령)** 제한입니다. 긴 핸들러는 여기서 저장만 하고 `b c_handler`로 점프해야 합니다 — 넘치면 다음 엔트리를 침범.<br>
**왜 헷갈리는가**: "벡터=핸들러 코드"라는 단순화. 실제로는 테이블의 고정 슬롯.
:::
:::danger[❓ 오해 3 — 'ERET 전에 ISB가 필요하다']
**실제**: `ERET` 자체가 **context synchronization event**라 별도 ISB가 불필요합니다. 반면 `MSR`로 시스템 레지스터를 바꾼 뒤 `ERET` 없이 계속 실행할 땐 ISB가 필요(M04).<br>
**왜 헷갈리는가**: "컨텍스트 바뀌면 ISB"라는 규칙을 ERET에도 기계적으로 적용해서.
:::
:::danger[❓ 오해 4 — 'IRQ는 syscall과 완전히 다른 경로다']
**실제**: 진입 메커니즘(벡터 테이블·ELR/SPSR 자동 저장·`ERET` 복귀)은 동일합니다. 다른 것은 _벡터 오프셋_(IRQ는 +0x480/+0x080)과 _비동기 발생_ 뿐입니다.<br>
**왜 헷갈리는가**: 동기/비동기라는 구분이 메커니즘까지 다를 거라는 추정.
:::

### DV 디버그 체크리스트 (이 모듈 내용으로 마주칠 첫 함정들)

| 증상 | 1차 의심 | 어디 보나 |
|---|---|---|
| 명령이 실행 안 되고 EL1로 trap | EL0에서 권한 없는 동작(sysreg/MMU) | `ESR_EL1.EC`=0x18(sysreg trap) 등 |
| 잘못된 벡터 엔트리로 진입 | (소스 EL, 스택, 타입) 인덱싱 오해 | 진입 EL·예외 타입 → 오프셋 표 대조 |
| 핸들러에서 GPR이 깨짐 | X0–X30 저장 누락 (HW는 안 함) | 벡터 entry의 `stp` 시퀀스 |
| `ERET` 후 또 trap | illegal SPSR (잘못된 EL/실행 상태 인코딩) | `SPSR_ELx` 값, illegal-exception-return |
| syscall이 엉뚱한 핸들러로 | `ESR.EC` 디코드 또는 syscall 테이블 인덱스 오류 | EC=0x15 확인, `x8`(syscall#) 범위 |
| page fault 종류 오판 | ISS.DFSC 비트 해석 오류 | `FAR_EL1` + `ESR.ISS & 0x3F`(DFSC) |
| IRQ가 한 번만 오고 멈춤 | EOI(`ICC_EOIR1_EL1`) 누락 → GIC dead-lock | ISR 끝의 EOI 명령 (M06) |

---

## 7. 핵심 정리 (Key Takeaways)

- **EL0–EL3 동심원**: 숫자가 높을수록 높은 특권. 하위는 상위 자원에 직접 접근 불가, 동기 예외(`SVC`/`HVC`/`SMC`)나 비동기 이벤트로만 상승.
- **EL별 책임**: EL0(유저)·EL1(커널, stage-1·syscall)·EL2(하이퍼바이저, stage-2·VMID)·EL3(secure monitor, `SCR_EL3.NS`·Root of Trust).
- **예외 진입 자동 저장 4개**: ELR(복귀 PC)·SPSR(옛 PSTATE)·ESR(원인)·FAR(폴트 주소). GPR은 SW 책임.
- **벡터 테이블**: 16 엔트리 × 0x80 바이트, (소스 EL, 스택 선택, 예외 타입)으로 인덱싱. EL0의 `SVC`는 +0x400.
- **ESR.EC**가 분기의 핵심: 0x15(SVC)·0x24/25(data abort)·0x18(sysreg trap). data abort는 ISS.DFSC로 fault 종류.
- **`ERET`**: 한 명령으로 PC·PSTATE·EL·인터럽트 마스크 복원 + context sync(ISB 불필요).

:::caution[실무 주의점]
- 벡터 핸들러는 **GPR 저장을 직접** 해야 한다 — HW 자동 저장은 ELR/SPSR/ESR/FAR뿐.
- 예외 디버그는 **`ESR.EC` → `FAR`/`DFSC` 순**으로 읽는다(분류 먼저, 세부 다음).
- `ERET`이 또 trap하면 **SPSR 인코딩**(목표 EL/실행 상태)을 의심한다 — illegal exception return.
- 보안(EL3/TrustZone) 깊이는 [ARM Security](../../arm_security/), 주소 번역 깊이는 [MMU](../../mmu/)·M05로.
:::
### 7.1 자가 점검

:::tip[🤔 Q1 — 벡터 인덱싱 (Bloom: Analyze)]
EL1 커널이 실행 중 data abort(같은 EL)를 만나면 어느 벡터 오프셋으로 진입하나? EL0의 `SVC`(+0x400)와 왜 다른가?
<details>
<summary>정답</summary>

EL1→EL1 data abort는 **Current EL, SPx, Sync = +0x200**으로 진입합니다.
- 벡터는 (소스 EL: Current vs Lower) × (스택: SP0 vs SPx) × (타입: Sync/IRQ/FIQ/SError)로 인덱싱.
- EL0의 `SVC`는 _Lower EL_ + AArch64 + Sync → +0x400.
- EL1 자체의 data abort는 _Current EL_ + SPx(EL1은 보통 SP_EL1 사용) + Sync → +0x200.
- 핵심: "어디서 왔나(소스 EL)"가 Current/Lower 절반을 가르고, 같은 예외라도 소스 EL에 따라 다른 슬롯.
- 검증 단서: 진입 오프셋이 예상과 다르면 소스 EL이나 SPSel 가정을 재검토.

</details>
:::
:::tip[🤔 Q2 — ERET의 단일성 (Bloom: Evaluate)]
`ERET`이 PC·PSTATE·EL·마스크 복원을 _여러 명령_ 으로 나눠서 하면 어떤 위험이 생기나? 단일 명령이 왜 더 안전한가?
<details>
<summary>정답</summary>

중간 상태(partial state)에서 인터럽트/예외가 끼면 일관성이 깨집니다.
- 만약 "PC 복원 → PSTATE 복원 → EL 변경"을 별도 명령으로 하면, 그 사이에 IRQ가 들어오면 PC는 새 값인데 PSTATE/EL은 옛 값인 _찢어진 상태_ 가 노출됨.
- `ERET`은 이 모두를 **원자적(atomic)** 으로 수행 + context sync 포함 → 중간 관측 불가, 새 컨텍스트로 즉시 일관되게 전환.
- 또한 SPSR 인코딩 검증(illegal return 체크)도 한 지점에서 — 잘못된 목표 EL/상태면 즉시 trap.
- 결론: 단일 명령이 atomicity와 검증을 HW에 위임해 SW 버그·레이스를 원천 차단.

</details>
:::
### 7.2 출처

**Internal**
- [Module 02 — 레지스터 & PSTATE](../02_registers_pstate/) — ELR/SPSR/ESR/FAR/VBAR과 PSTATE.DAIF
- [ARM Security](../../arm_security/) — EL3/TrustZone·secure boot 심화
- [MMU](../../mmu/) — TTBR/stage 번역 일반 원리

**External**
- *Arm Architecture Reference Manual for A-profile (ARM ARM, DDI 0487)* §D1 (AArch64 Exception model), §D13 (vector table) — (외부 표준 지식)
- *Arm SMC Calling Convention (SMCCC, DEN 0028)* — `SVC`/`HVC`/`SMC` ABI
- *Trusted Firmware-A (TF-A) Documentation* — Arm Ltd. (부팅 흐름·PSCI)
- Linux kernel `arch/arm64/kernel/entry.S` — 핸들러 entry 패턴 (오픈소스 참조)

---

## 다음 모듈

→ [Module 04 — 메모리 모델 & 배리어](../04_memory_model_barriers/): EL 전환과 시스템 레지스터 변경 뒤에 왜 `ISB`가 필요한지, 그리고 weakly-ordered 메모리에서 DMB/DSB와 acquire/release가 _어떤 순서_ 를 보장하는지를 본다.

[퀴즈 풀어보기 →](../quiz/03_exception_levels_quiz/)
