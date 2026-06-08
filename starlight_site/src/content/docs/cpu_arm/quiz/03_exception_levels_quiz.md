---
title: "Quiz — Module 03: Exception Level (EL0–EL3)"
---

[← Module 03 본문으로 돌아가기](../../03_exception_levels/)

---

## Q1. (Remember)

EL0 의 `SVC` 명령이 EL1 로 진입하면서 들어가는 벡터 테이블 오프셋(VBAR_EL1 기준)은?

- [ ] A. +0x000 (Current EL, SP0, Sync)
- [ ] B. +0x200 (Current EL, SPx, Sync)
- [ ] C. +0x400 (Lower EL, AArch64, Sync)
- [ ] D. +0x480 (Lower EL, AArch64, IRQ)

<details>
<summary>정답 / 해설</summary>

**C**. 벡터 테이블은 (소스 EL: Current vs Lower) × (스택 선택) × (예외 타입)으로 인덱싱됩니다. EL0 의 `SVC` 는 *Lower EL* + AArch64 + *Sync* 조합이라 +0x400 으로 들어갑니다. A/B 는 Current EL(같은 EL 에서 난 예외)용이고, D 는 같은 Lower EL 이지만 비동기 IRQ 용 오프셋입니다.

</details>
## Q2. (Understand)

예외 진입 시 HW 가 자동으로 저장하는 것과 SW(핸들러)가 저장해야 하는 것의 구분으로 옳은 것은?

- [ ] A. HW 가 X0–X30 까지 전부 저장
- [ ] B. HW 는 ELR/SPSR/ESR(+abort 면 FAR)만 저장, X0–X30/V0–V31 은 SW 책임
- [ ] C. SW 가 ELR/SPSR 까지 다 저장
- [ ] D. 아무것도 저장되지 않음

<details>
<summary>정답 / 해설</summary>

**B**. HW 는 ELR(복귀 PC), SPSR(옛 PSTATE), ESR(원인), 그리고 data/instruction abort 면 FAR(폴트 주소) — 이 4개만 자동 저장합니다. X0–X30/V0–V31 같은 범용 레지스터는 SW 가 직접 스택에 저장해야 하므로, 벡터 핸들러의 첫 일이 GPR dump 입니다. A 는 과대평가, C 는 HW 가 하는 일을 SW 로 넘긴 오답, D 는 틀렸습니다.

</details>
## Q3. (Apply)

EL0 유저 코드가 `msr sctlr_el1, x0` 로 MMU 를 끄려 하자 명령이 실행되지 않고 EL1 로 trap 했다. ESR_EL1.EC 값과 이 동작의 성격은?

- [ ] A. EC=0x15 — 정상적인 syscall
- [ ] B. EC=0x18 — MSR/MRS sysreg trap, 특권 모델이 의도대로 동작한 것(버그 아님)
- [ ] C. EC=0x24 — data abort, 메모리 버그
- [ ] D. EC=0x2F — SError, 하드웨어 결함

<details>
<summary>정답 / 해설</summary>

**B**. EL0(유저)는 시스템 레지스터에 직접 접근할 수 없으므로 `MSR sctlr_el1` 은 실행되지 않고 EL1 로 trap 하며 ESR_EL1.EC=0x18(MSR/MRS system register trap)이 기록됩니다. 이것은 버그가 아니라 특권 모델이 정확히 의도대로 하위 EL 의 권한 없는 동작을 막은 것입니다. A(0x15)는 SVC, C(0x24)는 data abort, D(0x2F)는 SError 로 모두 원인이 다릅니다.

</details>
## Q4. (Apply)

벡터 핸들러를 작성하는데 한 엔트리가 0x80 바이트(최대 32 명령)를 넘는 긴 핸들러가 필요하다. 올바른 패턴은?

- [ ] A. 엔트리에 모든 코드를 그대로 채운다
- [ ] B. 엔트리에서 레지스터 저장만 하고 `b c_handler` 로 점프한다
- [ ] C. 0x80 제한을 무시하고 다음 엔트리까지 침범한다
- [ ] D. ERET 으로 즉시 복귀한다

<details>
<summary>정답 / 해설</summary>

**B**. 각 벡터 엔트리는 0x80 바이트(최대 32 명령) 고정 슬롯이라 긴 핸들러를 통째로 넣으면 다음 엔트리를 침범합니다. 관례는 엔트리에서 GPR 저장(`kernel_entry`)만 하고 `b do_sync_handler` 처럼 C 핸들러로 점프하는 것입니다. C 는 정확히 침범 버그를 일으키고, A 는 그 원인, D 는 처리도 안 하고 복귀해 버리는 오답입니다.

</details>
## Q5. (Analyze)

EL1 커널이 실행 중 data abort(같은 EL)를 만나면 어느 벡터 오프셋으로 진입하며, EL0 의 `SVC`(+0x400)와 왜 다른지 분석하라.

<details>
<summary>정답 / 해설</summary>

EL1→EL1 data abort 는 **Current EL, SPx, Sync = +0x200** 으로 진입합니다. 벡터는 (소스 EL: Current vs Lower) × (스택: SP0 vs SPx) × (타입: Sync/IRQ/FIQ/SError)로 인덱싱됩니다. EL0 의 `SVC` 는 *Lower EL*(아래 EL 에서 올라옴) + AArch64 + Sync 라 +0x400 이고, EL1 자체의 data abort 는 *Current EL*(같은 EL 에서 발생) + SPx(EL1 은 보통 SP_EL1 사용) + Sync 라 +0x200 입니다. 핵심은 "어디서 왔나(소스 EL)" 가 Current/Lower 절반을 가르므로, 같은 예외 타입이라도 소스 EL 에 따라 다른 슬롯으로 간다는 점입니다. 진입 오프셋이 예상과 다르면 소스 EL 이나 SPSel 가정을 재검토합니다.

</details>
## Q6. (Evaluate)

`ERET` 이 PC·PSTATE·EL·인터럽트 마스크 복원을 여러 명령으로 나눠 수행한다면 어떤 위험이 생기는지, 단일 명령 설계가 왜 더 안전한지 평가하라.

<details>
<summary>정답 / 해설</summary>

여러 명령으로 나누면 **중간(partial) 상태에서 인터럽트/예외가 끼어 일관성이 깨질** 위험이 생깁니다. 예컨대 "PC 복원 → PSTATE 복원 → EL 변경" 을 별도 명령으로 하면, 그 사이 IRQ 가 들어올 때 PC 는 새 값인데 PSTATE/EL 은 옛 값인 *찢어진 상태* 가 노출됩니다. `ERET` 은 이 모두를 **원자적(atomic)** 으로 수행하고 context synchronization 까지 포함하므로(ISB 불필요), 중간 상태가 관측될 수 없고 새 컨텍스트로 즉시 일관되게 전환됩니다. 또한 SPSR 인코딩 검증(잘못된 목표 EL/실행 상태면 illegal exception return 으로 trap)도 한 지점에서 이뤄집니다. 결론적으로 단일 명령 설계는 atomicity 와 검증을 HW 에 위임해 SW 의 레이스·버그를 원천 차단하므로 더 안전합니다.

</details>
