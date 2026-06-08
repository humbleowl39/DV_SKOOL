---
title: "Quiz — Module 06: Formal Processor Verification"
---

[← Module 06 본문으로 돌아가기](../../06_riscv_formal/)

---

## Q1. (Remember)

`riscv-formal`(YosysHQ)이 코어의 ISA 준수를 검사하기 위해 _코어로부터 입력받는_ 인터페이스는?

- [ ] A. AXI 버스
- [ ] B. RVFI
- [ ] C. JTAG
- [ ] D. PCIe TLP

<details>
<summary>정답 / 해설</summary>

**B**. RVFI(RISC-V Formal Interface)는 코어가 retire 시점에 명령의 architectural 정보(`rvfi_valid`, `rvfi_insn`, `rvfi_pc_*`, `rvfi_rd_*`, `rvfi_mem_*`)를 약속된 형식으로 노출하는 인터페이스입니다. riscv-formal 은 이 출력만 보고 ISA spec 을 인코딩한 property 로 검사하므로, 코어 내부 구조(파이프라인 깊이·forwarding)와 무관하게 같은 property 를 여러 코어에 재사용할 수 있습니다.

</details>

## Q2. (Understand)

"Simulation 은 표본, Formal 은 전수(bounded)" 라는 비유에서, formal 이 PASS·FAIL 일 때 각각 무엇을 보장하는지 설명하라.

<details>
<summary>정답 / 해설</summary>

- **PASS(BMC)**: reset 으로부터 _k 사이클 이내_ 에 해당 property 를 위반하는 입력 시퀀스가 _존재하지 않음_ 을 보장합니다(전수, 단 k 깊이까지). 시뮬레이션처럼 "특정 자극에 대해서만"이 아니라 그 깊이의 _모든_ 입력에 대해 위반이 없음을 의미합니다.
- **FAIL**: 솔버가 property 를 위반하는 _실제 입력 시퀀스_ 를 구성한 것이므로 _확실한 버그_ 입니다(false positive 없음). 게다가 그 반례는 _최소 길이_ 라 디버그가 쉽습니다.

핵심은 PASS 가 "k 깊이까지의 증명"이지 무한 깊이 증명이 아니라는 점입니다(완전 증명은 k-induction 필요).

</details>

## Q3. (Apply)

`add_correct` check 를 작성하는데, RISC-V 에서 `x0`(목적 레지스터가 0번)인 ADD 의 결과는 항상 0 이어야 한다. property 에서 이를 어떻게 반영하는가?

<details>
<summary>정답 / 해설</summary>

목적 레지스터 번호(`rvfi_rd_addr`)가 0 인 경우와 아닌 경우를 나눠 기대값을 분기합니다.
- `rvfi_rd_addr == 0` 이면 기대값은 _항상 0_ (`rvfi_rd_wdata == 0`).
- 그 외에는 두 source 의 합 (`rvfi_rd_wdata == rvfi_rs1_rdata + rvfi_rs2_rdata`).

즉 `(rvfi_rd_addr == 0) ? (rvfi_rd_wdata == 0) : (rvfi_rd_wdata == rvfi_rs1_rdata + rvfi_rs2_rdata)` 형태로, `rvfi_valid && is_add(rvfi_insn)` 일 때 이 등식을 assert 합니다. 이 한 property 가 "x0 에 쓴 값이 forwarding 경로로 0 아닌 값으로 새어나가는" 코너 버그를 잡아냅니다.

</details>

## Q4. (Apply)

riscv-formal 의 모든 check 가 사이클 0~1 에서 즉시 FAIL 한다. 반례를 보니 초기 상태가 비현실적이다. 가장 먼저 점검할 것은?

- [ ] A. k 를 더 키운다
- [ ] B. reset/초기 상태 assumption(`disable iff`, 초기 assume)이 빠졌는지 점검한다
- [ ] C. ISS 를 바꾼다
- [ ] D. 명령 분포 weight 를 조정한다

<details>
<summary>정답 / 해설</summary>

**B**. 모든 check 가 _사이클 0~1 에서 즉시_ FAIL 하고 반례의 초기 상태가 비현실적이라면, 솔버가 reset 으로 도달 불가능한 임의 초기 상태에서 시작했을 가능성이 큽니다. `disable iff (!resetn)` 또는 초기 상태에 대한 assume 이 빠지면 솔버가 _도달 불가능한_ 상태를 자유롭게 골라 가짜 위반을 만듭니다. k 를 키우거나(A) ISS·분포(C·D, formal 과 무관)를 바꾸는 것은 핵심이 아닙니다 — reset assumption 을 먼저 잡아야 합니다.

</details>

## Q5. (Analyze)

`add_correct` check 가 k=24 BMC 에서 PASS 했다. "이 코어의 ADD 는 완전히 검증됐다"고 말해도 되는가? 정확히 무엇이 보장됐는가?

<details>
<summary>정답 / 해설</summary>

**"완전히"라고 말하면 안 됩니다.** 보장된 것은 _reset 으로부터 24 사이클 이내_ 에 `add_correct` 를 위반하는 입력 시퀀스가 없다는 것뿐입니다.
- 25 사이클 이상 깊은 곳의 위반은 이 BMC 가 탐색하지 않았습니다. "모든 깊이"를 증명하려면 k-induction 으로 unbounded proof 를 닫아야 합니다.
- 또한 이 property 는 ADD 의 _결과값_ 만 봅니다 — PC 갱신·예외 상호작용 등은 다른 check(pc/liveness 등)가 따로 덮어야 합니다.
- 정확한 표현: "ADD 결과 정확성이 k=24 깊이까지 bounded-증명되었다."

</details>

## Q6. (Evaluate)

"리눅스를 부팅시켜 인터럽트·페이지폴트가 섞인 1억 사이클 워크로드에서 코어가 hang 하지 않음"을 검증하려 한다. formal 과 simulation 중 무엇이 적합하며 왜인가?

<details>
<summary>정답 / 해설</summary>

**Simulation 이 적합합니다.**
- 1억 사이클·OS 부팅 같은 _긴 시스템 시나리오_ 는 formal 의 state space 폭발 한계 때문에 비현실적입니다 — BMC 로 1억 사이클 깊이를 푸는 것은 사실상 불가능합니다.
- 시뮬레이션은 긴 시나리오를 실제 실행하므로 시스템 통합·성능·복합 인터럽트 시퀀스에 강합니다.
- 단, "hang 하지 않음(liveness)"의 _국소적_ 보장은 formal 의 liveness check 로 _짧은 깊이_ 에서 보강할 수 있습니다("어떤 상태에서도 결국 retire 한다").
- 결론: 긴 워크로드 전체는 simulation, 그 안의 국소적 liveness·명령 정확성은 formal 로 분업 — 둘을 상보적으로 쓰는 것이 sign-off 근거입니다.

</details>
