---
title: "CPU DV 용어집"
---

이 페이지는 본 코스에서 사용되는 프로세서 검증 핵심 용어 정의 모음입니다. 항목은 ISO 11179 형식을 따릅니다 (**Definition / Source / Related / Example / See also**).

:::tip[검색 활용]
상단 검색창에 용어를 입력하면 본문에서의 사용처도 함께 찾을 수 있습니다.
:::
---

## A — Architectural State

### Architectural State

**Definition.** ISA 가 소프트웨어에 보이도록 정의한 프로세서의 상태 집합으로, program counter, 범용 레지스터 파일, CSR, privilege mode, 그리고 메모리로 구성된다.

**Source.** 일반 컴퓨터 구조/검증 관용 표현 (ISA 사양의 "programmer-visible state").

**Related.** Microarchitectural State, Retire, Golden Predictor.

**Example.** RV32I 의 architectural state 는 PC, x0–x31, 그리고 mstatus/mepc 등 구현된 CSR 들입니다. 파이프라인 레지스터나 reservation station 은 microarchitectural state 로, architectural state 에 포함되지 않습니다.

**See also.** [Module 01 — 왜 CPU DV는 어려운가](../01_why_cpu_dv/)

### ACT (Architectural Comparison Trace)

**Definition.** 한 명령이 retire 될 때 RTL 코어와 reference model 이 각각 갱신한 architectural state 를 비교 가능한 형태로 기록한 트레이스 항목.

**Source.** step-and-compare 검증 관용 표현 (추론 — 도구별 명칭 상이).

**Related.** Step-and-Compare, Retire, Divergence.

**Example.** retire 한 명령의 PC, 기록한 레지스터 번호와 값, 갱신한 CSR 를 한 레코드로 묶어 ISS 의 동일 단계 결과와 대조합니다.

**See also.** [Module 02 — Step-and-Compare Lockstep](../02_step_and_compare/)

---

## C — Commit / CSR

### Commit (Retire)

**Definition.** 프로세서가 한 명령의 실행 결과를 architectural state 에 되돌릴 수 없게 확정하는 시점.

**Source.** 일반 컴퓨터 구조 관용 표현. OoO 코어에서는 [ROB](../../computer_architecture/03_ooo_branch_prediction/) 의 in-order retire 와 동의.

**Related.** Retire, ROB, Precise Exception, Retire Monitor.

**Example.** OoO 코어는 명령을 순서 없이 실행(execute)하지만 commit/retire 는 프로그램 순서대로 일어나므로, architectural state 비교는 항상 retire 시점에 in-order 로 수행합니다.

**See also.** [Module 02](../02_step_and_compare/)

### CSR (Control/Status Register)

**Definition.** 프로세서의 제어·상태를 담는 특권 레지스터로, privilege mode·예외 처리·트랩 벡터·인터럽트 마스크 등을 설정·관찰하는 데 쓰인다.

**Source.** RISC-V Privileged ISA 사양 (외부 표준 지식). ARM 에서는 system register 가 대응.

**Related.** Privilege Mode, Precise Exception, Architectural State.

**Example.** RISC-V 의 mstatus, mepc, mcause, mtvec 등이 예외 진입 시 함께 갱신되며, 이 side-effect 의 순서·값이 흔한 CPU 버그 지점입니다.

**See also.** [Module 07 — Coverage & 특수 영역](../07_coverage_special_areas/)

---

## D — Divergence / DPI-C

### Divergence (Mismatch)

**Definition.** 동일 명령 스트림에 대해 RTL 코어와 reference model 의 architectural state 가 처음으로 불일치하는 retire 지점.

**Source.** step-and-compare 검증 관용 표현.

**Related.** Step-and-Compare, Golden Predictor, Retire.

**Example.** ADDI x5, x5, 1 을 retire 한 직후 RTL 의 x5 가 reference model 과 다르면 그 명령이 first divergent instruction 으로 즉시 flag 됩니다. 이후 명령은 cascading mismatch 이므로 무시합니다.

**See also.** [Module 02](../02_step_and_compare/)

### DPI-C

**Definition.** SystemVerilog 와 C/C++ 간 양방향 함수 호출을 가능하게 하는 표준 인터페이스로, golden predictor(ISS) 를 UVM scoreboard 에 연동하는 데 사용된다.

**Source.** IEEE 1800-2017, §35.

**Related.** Golden Predictor, ISS, Scoreboard, Reference Model.

**Example.** `import "DPI-C" function void iss_step(input longint pc, output longint next_pc);` 로 C 로 작성된 Spike-like 모델의 한 스텝을 SystemVerilog scoreboard 에서 호출합니다.

**See also.** [Module 04 — UVM 코어 검증 환경](../04_uvm_core_env/)

---

## G — Golden Predictor

### Golden Predictor

**Definition.** 명령 스트림에 대해 ISA 가 규정하는 정확한 architectural state 변화를 산출해 scoreboard 의 expected 값을 제공하는 검증용 reference model.

**Source.** 일반 검증 관용 표현 (reference model 의 프로세서 검증 특화 명칭).

**Related.** ISS, Reference Model, Scoreboard, Step-and-Compare.

**Example.** Spike(RISC-V ISS) 를 DPI-C 로 연동해, retire monitor 가 본 RTL 결과와 Spike 가 같은 명령에 대해 산출한 결과를 비교하는 scoreboard 의 채점 기준으로 사용합니다.

**See also.** [Module 04](../04_uvm_core_env/)

---

## I — ISA Coverage / ISS

### ISA Coverage

**Definition.** ISA 가 정의한 명령·피연산자·특권 상태·예외 조합이 검증 중 얼마나 실행되었는지를 측정하는 기능 커버리지.

**Source.** 일반 검증 관용 표현. RISC-V 진영에서는 ISACOV(riscv-dv/core-v-verif) 라는 표준 커버리지 모델이 존재.

**Related.** Functional Coverage, Cross, Privilege Mode, riscv-dv.

**Example.** opcode × privilege mode × 정렬되지 않은 주소 여부의 cross 를 covergroup 으로 정의해, 모든 명령이 모든 특권 레벨에서 정상/예외 경로로 실행되었는지를 추적합니다.

**See also.** [Module 07](../07_coverage_special_areas/)

### ISS (Instruction Set Simulator)

**Definition.** ISA 의 명령 의미만을 함수적으로 모델링해 architectural state 변화를 산출하는 소프트웨어 시뮬레이터로, 타이밍·파이프라인은 모델링하지 않는다.

**Source.** 일반 컴퓨터 구조/검증 관용 표현. RISC-V 의 대표 ISS 는 Spike(riscv-isa-sim).

**Related.** Golden Predictor, Reference Model, Step-and-Compare, DPI-C.

**Example.** Spike 는 한 명령을 받으면 PC·레지스터·CSR·메모리를 ISA 정의대로 갱신하지만, 그 명령이 몇 사이클 걸렸는지는 알지 못합니다 — 그래서 비교는 사이클이 아닌 retire 단위로 합니다.

**See also.** [Module 02](../02_step_and_compare/)

---

## L — Lockstep

### Lockstep (Step-and-Compare)

**Definition.** RTL 코어와 reference model 을 같은 명령 스트림으로 나란히 실행하며 매 retire 마다 architectural state 를 비교하는 동적 검증 기법.

**Source.** 일반 검증 관용 표현. Synopsys ImperasDV, OpenHW core-v-verif 가 대표 구현.

**Related.** Step-and-Compare, Golden Predictor, Retire, Divergence.

**Example.** RTL 이 한 명령을 retire 하면 reference model 을 한 스텝 진행시켜 두 architectural state 를 대조하고, 일치하면 다음 명령으로 넘어갑니다 — 두 모델이 보조를 맞춰(lockstep) 전진합니다.

**See also.** [Module 02](../02_step_and_compare/)

---

## P — Privilege Mode / Precise Exception

### Privilege Mode

**Definition.** 프로세서가 어떤 명령·CSR·메모리 영역에 접근할 수 있는지를 결정하는 실행 특권 레벨.

**Source.** RISC-V Privileged ISA / ARM Exception Level 사양 (외부 표준 지식).

**Related.** CSR, Precise Exception, ISA Coverage.

**Example.** RISC-V 의 M/S/U 모드(ARM 의 EL3–EL0 에 대응) 전이는 trap/return 시 CSR side-effect 를 동반하므로, 모드 전이 경로 자체가 별도의 coverage·검증 대상입니다.

**See also.** [Module 07](../07_coverage_special_areas/)

### Precise Exception

**Definition.** 예외가 보고될 때 그 이전 명령은 모두 완료되고 이후 명령은 하나도 architectural state 에 반영되지 않은 상태를 보장하는 예외 처리 모델.

**Source.** 일반 컴퓨터 구조 관용 표현. [ROB 기반 in-order retire](../../computer_architecture/03_ooo_branch_prediction/) 로 구현.

**Related.** Commit, ROB, Privilege Mode, CSR.

**Example.** load 가 page fault 를 일으키면 그 load 와 이후 모든 추측 실행 결과는 폐기되고 mepc 가 해당 PC 를 가리켜야 하며, reference model 도 동일 시점에 같은 예외를 산출해야 비교가 성립합니다.

**See also.** [Module 01](../01_why_cpu_dv/)

---

## R — Retire / RVFI / RVVI / riscv-dv / riscv-formal

### Retire Monitor

**Definition.** 코어가 명령을 retire 하는 시점의 architectural state 변화를 관찰해 트랜잭션으로 변환하고 analysis port 로 브로드캐스트하는 UVM 컴포넌트.

**Source.** 일반 UVM/CPU 검증 관용 표현. 관찰 신호로 흔히 RVFI 를 사용.

**Related.** RVFI, Commit, Scoreboard, Analysis Port.

**Example.** retire monitor 는 rvfi_valid 가 1 인 사이클에 PC·기록 레지스터·CSR 변화를 샘플해 retire transaction 으로 만들고 scoreboard·coverage 로 fan-out 합니다.

**See also.** [Module 03 — RVFI & RVVI](../03_rvfi_rvvi/)

### RVFI (RISC-V Formal Interface)

**Definition.** 코어가 검증용으로 노출하는, 명령 retire 시점의 신호 집합 인터페이스로, 어떤 명령이 어떤 architectural state 변화를 일으켰는지를 알려준다.

**Source.** YosysHQ riscv-formal 프로젝트의 RVFI 사양 (외부 표준 지식, github.com/YosysHQ/riscv-formal).

**Related.** RVVI, Retire Monitor, riscv-formal, Commit.

**Example.** rvfi_valid, rvfi_insn, rvfi_pc_rdata/wdata, rvfi_rd_addr/wdata, rvfi_mem_addr 등의 신호로, 형식 검증기와 시뮬레이션 monitor 가 동일하게 retire 정보를 읽습니다.

**See also.** [Module 03](../03_rvfi_rvvi/)

### RVVI (RISC-V Verification Interface)

**Definition.** RTL 코어·reference model·트레이스 비교를 묶는 DV 서브시스템 통합을 표준화하기 위한 open standard 인터페이스.

**Source.** RVVI draft open standard (외부 표준 지식, github.com/riscv-verification/RVVI).

**Related.** RVFI, Step-and-Compare, Golden Predictor.

**Example.** RVVI 는 RVVI-TRACE(코어가 내보내는 retire 트레이스) 와 reference model 연동 API 를 정의해, 서로 다른 코어·ISS 를 같은 step-and-compare 하네스에 꽂을 수 있게 합니다.

**See also.** [Module 03](../03_rvfi_rvvi/)

### riscv-dv

**Definition.** 제약 랜덤으로 합법적인 RISC-V 명령 스트림을 생성해 코어 검증의 자극으로 쓰는 오픈소스 instruction generator.

**Source.** 오픈소스 프로젝트 riscv-dv (외부 지식). 같은 부류로 force-riscv 가 존재.

**Related.** Constrained Random, ISA Coverage, Golden Predictor.

**Example.** riscv-dv 는 register dependency·privilege 전이·정렬되지 않은 접근 같은 코너 케이스를 의도적으로 만드는 제약을 걸어, directed test 로는 닿기 힘든 상태 공간을 채웁니다.

**See also.** [Module 05 — riscv-dv 자극 생성](../05_riscv_dv_stimulus/)

### riscv-formal

**Definition.** RVFI 를 통해 코어의 retire 동작을 ISA 의 형식 모델과 명령 단위로 대조하는 RISC-V 형식 검증 프레임워크.

**Source.** YosysHQ riscv-formal (외부 표준 지식, github.com/YosysHQ/riscv-formal).

**Related.** RVFI, Formal Verification, BMC, Lockstep.

**Example.** riscv-formal 은 "임의의 상태에서 이 명령을 실행하면 결과가 ISA 모델과 일치한다"를 bounded model checking 으로 증명해, 시뮬레이션이 닿지 못한 상태도 커버합니다.

**See also.** [Module 06 — riscv-formal 형식 검증](../06_riscv_formal/)

---

## 추가 약어

| 약어 | 풀네임 | 한 줄 의미 |
|------|--------|-----------|
| **ISS** | Instruction Set Simulator | ISA 의미만 모델링하는 함수적 시뮬레이터 (golden predictor 로 사용) |
| **RVFI** | RISC-V Formal Interface | 코어가 노출하는 retire 시점 검증 신호 |
| **RVVI** | RISC-V Verification Interface | DV 서브시스템 통합 open standard |
| **ROB** | Reorder Buffer | OoO 실행 결과를 in-order 로 retire 하는 버퍼 |
| **CSR** | Control/Status Register | 특권 제어·상태 레지스터 |
| **ImperasDV** | — | Synopsys 의 상용 step-and-compare 검증 솔루션 |
| **core-v-verif** | — | OpenHW CORE-V 코어의 오픈 UVM 검증 환경 |
