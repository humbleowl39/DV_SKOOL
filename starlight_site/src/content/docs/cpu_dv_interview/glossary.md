---
title: "CPU DV Interview 용어집"
---

이 페이지는 본 코스에서 사용되는 핵심 용어 정의 모음입니다. 항목은 ISO 11179 형식을 따릅니다 (**Definition / Source / Related / Example / See also**). CPU 코어 검증(ISS step-and-compare·계층 인프라)과 ARM 아키텍처(EL·PSTATE·barrier·MMU)·일관성/메모리 모델·UVM 방법론 용어를 함께 묶었습니다.

:::tip[검색 활용]
상단 검색창에 용어를 입력하면 본문에서의 사용처도 함께 찾을 수 있습니다.
:::
---

## A — Acquire/Release / Amdahl's Law

### Acquire / Release

**Definition.** 한쪽 방향의 메모리 순서만 강제하는 반쪽 배리어로, acquire는 자신 이후의 접근이 앞당겨지지 못하게 하고 release는 자신 이전의 접근이 뒤로 밀리지 못하게 한다.

**Source.** ARM Architecture Reference Manual (AArch64) — LDAR/STLR.

**Related.** Memory Barrier, Weakly-Ordered, Memory Consistency Model.

**Example.** `STLR ready`(release) 뒤 `LDAR ready`(acquire)로 lock-free 핸드오프를 DMB 없이 구현.

**See also.** [03 — ARM 아키텍처](../03_arm_architecture/#53-acquirerelease--한-방향-배리어)

### Amdahl's Law

**Definition.** 전체 작업 중 일부만 가속될 때 얻을 수 있는 전체 속도 향상의 상한을, 가속 불가능한 비율이 결정한다는 성능 법칙.

**Source.** Hennessy & Patterson, *Computer Architecture: A Quantitative Approach*.

**Related.** IPC, CPI, Pipeline.

**Example.** 95%를 무한히 가속해도 5%가 직렬이면 전체는 최대 20배까지만 빨라진다.

**See also.** [02 — CPU 마이크로아키텍처](../02_cpu_microarchitecture/#23-amdahl-법칙--부분-가속의-한계)

---

## B — Branch Prediction (BTB/BHT)

### BHT (Branch History Table)

**Definition.** 분기 명령의 PC를 인덱스로 과거 taken/not-taken 경향을 저장해 분기 *방향*을 예측하는 테이블.

**Source.** Hennessy & Patterson, *Computer Architecture*.

**Related.** BTB, 2-bit saturating counter, Branch Prediction, Speculative Execution.

**Example.** 각 엔트리가 2-bit saturating counter로 strongly/weakly taken·not-taken 4상태를 추적.

**See also.** [02 — CPU 마이크로아키텍처](../02_cpu_microarchitecture/#62-분기-예측의-두-축-방향과-타깃)

### Branch Prediction

**Definition.** 분기 결과가 확정되기 전에 방향(taken 여부)과 타깃 주소를 추측해 control hazard로 인한 stall을 없애는 기법.

**Source.** Hennessy & Patterson, *Computer Architecture*.

**Related.** BTB, BHT, Speculative Execution, Pipeline Hazard.

**Example.** mispredict 시 추측 경로의 in-flight 명령을 flush하고 올바른 타깃에서 refetch.

**See also.** [02 — CPU 마이크로아키텍처](../02_cpu_microarchitecture/#6-control-hazard와-분기-예측)

### BTB (Branch Target Buffer)

**Definition.** 분기 명령의 PC를 key로 예측 *타깃 주소*를 캐싱해 IF 단계에서 다음 fetch 주소를 즉시 결정하게 하는 테이블.

**Source.** Hennessy & Patterson, *Computer Architecture*.

**Related.** BHT, Branch Prediction, RAS.

**Example.** BTB hit 시 분기 해석 전에 다음 fetch 주소를 미리 가져옴.

**See also.** [02 — CPU 마이크로아키텍처](../02_cpu_microarchitecture/#62-분기-예측의-두-축-방향과-타깃)

---

## C — Cache / Coherence vs Consistency / config_db / Constraint / Covergroup

### Cache (Set-Associative)

**Definition.** 한 set 안에 여러 way를 두어 한 주소가 들어갈 수 있는 자리를 늘림으로써 충돌 미스를 줄인, 지역성을 활용해 평균 메모리 접근 시간을 단축하는 작고 빠른 메모리 계층.

**Source.** Hennessy & Patterson, *Computer Architecture*.

**Related.** Write-Back/Write-Through, LRU, MESI, False Sharing.

**Example.** 4-way set-associative 캐시에서 set이 꽉 차면 replacement policy가 한 라인을 eviction.

**See also.** [02 — CPU 마이크로아키텍처](../02_cpu_microarchitecture/#7-캐시--set-associative와-writeback)

### Coherence vs Consistency

**Definition.** Coherence는 *한 주소*의 캐시 사본이 같은 값으로 보이도록 하는 메커니즘이고, Consistency는 *여러 주소*에 대한 접근이 어떤 순서로 관찰되는지를 규정하는 시스템 전체의 순서 규칙이다.

**Source.** Sorin, Hill & Wood, *A Primer on Memory Consistency and Cache Coherence*.

**Related.** MESI, Memory Consistency Model, Memory Barrier, Snooping.

**Example.** "Coherence는 값, consistency는 순서" — coherence가 완벽해도 weak 모델에선 barrier 없이 순서가 깨진다.

**See also.** [04 — 일관성·메모리 모델](../04_coherence_and_memory_model/#1-coherence-vs-consistency--한-줄-구분)

### config_db (UVM)

**Definition.** Component 트리 어디서든 계층 경로·타입·이름으로 설정 값을 set/get 하는 UVM의 전역 설정 채널.

**Source.** UVM 1.2 Reference Manual.

**Related.** Factory, Virtual Interface, RAL.

**Example.** RVFI virtual interface·ISS 핸들·hart 수를 주입하며, get 실패 시 silent miss를 막기 위해 `uvm_fatal`로 가드한다.

**See also.** [05 — CPU DV 방법론](../05_cpu_dv_methodology/#13-config_db--silent-miss-를-잡는-습관)

### Constraint (solve-before)

**Definition.** SystemVerilog의 `rand` 변수가 무작위 값 생성 시 만족해야 할 조건을 선언하는 코드 블록으로, `solve A before B`는 두 변수의 해 분포 편향을 잡기 위해 A를 먼저 결정하도록 솔버 순서를 지정하는 절이다.

**Source.** IEEE 1800-2017 SystemVerilog Standard, §18.

**Related.** Covergroup, Random Instruction Generator, Virtual Sequence.

**Example.** `constraint c { solve op before imm; if (op == LOAD) imm inside {[0:4095]}; }`

**See also.** [05 — CPU DV 방법론](../05_cpu_dv_methodology/#4-cpu-coverage--무엇을-bin-으로-둘까)

### Covergroup

**Definition.** SystemVerilog에서 coverpoint와 cross의 bin을 정의해 자극이 의도한 상태·조합을 얼마나 쳤는지 functional coverage로 수집하는 구조.

**Source.** IEEE 1800-2017, §19.

**Related.** Constraint, Cross Coverage, Coverage Hole.

**Example.** retire stream에서 명령 타입 × 예외 × EL 전환을 cross bin으로 샘플.

**See also.** [05 — CPU DV 방법론](../05_cpu_dv_methodology/#4-cpu-coverage--무엇을-bin-으로-둘까)

---

## D — Directory-Based Coherence

### Directory-Based Coherence

**Definition.** 각 메모리 라인의 공유자 목록을 중앙 디렉터리에 기록해, 브로드캐스트 대신 해당 사본을 가진 코어에게만 coherence 메시지를 보내는 확장성 높은 일관성 방식.

**Source.** Hennessy & Patterson, *Computer Architecture*.

**Related.** Snooping, MESI, MOESI, Coherence vs Consistency.

**Example.** 코어 수가 많으면 snoop 브로드캐스트가 폭증하므로 ARM CHI 같은 directory류 프로토콜을 쓴다.

**See also.** [04 — 일관성·메모리 모델](../04_coherence_and_memory_model/#4-snooping-vs-directory)

---

## E — Exception Level (EL0–EL3)

### Exception Level (EL0–EL3)

**Definition.** AArch64에서 권한을 4단계(숫자가 클수록 높은 권한)로 나눈 실행 특권 등급으로, 하위 EL은 동기 예외나 비동기 이벤트로만 상위 EL로 올라갈 수 있다.

**Source.** ARM Architecture Reference Manual (AArch64).

**Related.** PSTATE, TrustZone, MMU, Precise Exception.

**Example.** EL0(User)·EL1(Kernel)·EL2(Hypervisor)·EL3(Secure Monitor)이며, EL0의 권한 위반은 EL1로 trap된다.

**See also.** [03 — ARM 아키텍처](../03_arm_architecture/#4-exception-level--el0el1el2el3)

---

## F — Factory / False Sharing / Forwarding / Formal Verification

### Factory (UVM)

**Definition.** UVM 객체 생성을 type 또는 instance override가 가능한 형태로 통합 관리해, 소스 수정 없이 구조를 교체하게 하는 메커니즘.

**Source.** UVM 1.2 Reference Manual.

**Related.** config_db, RAL, Virtual Sequence.

**Example.** `type_id::create()`로 만든 scoreboard를 `set_type_override`로 변형 버전으로 교체.

**See also.** [05 — CPU DV 방법론](../05_cpu_dv_methodology/#15-factory--ral--재사용과-csr)

### False Sharing

**Definition.** 서로 다른 코어가 같은 캐시 라인의 *다른 바이트*만 각자 쓰는데도 coherence가 라인 단위로 동작해 불필요한 invalidate ping-pong이 반복되는 성능 저하 현상.

**Source.** Hennessy & Patterson, *Computer Architecture*.

**Related.** Cache, MESI, Coherence vs Consistency.

**Example.** 결과 값은 항상 정확하므로 기능 스코어보드가 못 잡고, coherence/성능 카운터로만 관측된다.

**See also.** [02 — CPU 마이크로아키텍처](../02_cpu_microarchitecture/#73-write-back-vs-write-through--trade-off)

### Forwarding (Bypassing)

**Definition.** Pipeline에서 이전 명령의 EX 결과를 다음 명령의 입력으로 직접 연결해 RAW data hazard를 stall 없이 해소하는 기법.

**Source.** Hennessy & Patterson, *Computer Architecture*.

**Related.** Pipeline Hazard, Store-to-Load Forwarding, ROB.

**Example.** load 결과는 MEM 끝에 나오므로 forwarding이 완비돼도 load-use는 1 stall이 불가피하다.

**See also.** [02 — CPU 마이크로아키텍처](../02_cpu_microarchitecture/#3-pipeline-hazard-3종과-forwarding)

### Formal Verification

**Definition.** 무작위 입력으로 상태 공간을 샘플하는 대신 수학적으로 모든 경우를 증명하거나 반증하는 검증 방식.

**Source.** common DV usage.

**Related.** Covergroup, SVA, Coverage Hole.

**Example.** 깊은 상태나 "절대 일어나면 안 됨" 류 불변식(데드락 부재·coherence 불법 전이 부재)에 적합하다.

**See also.** [05 — CPU DV 방법론](../05_cpu_dv_methodology/#6-cpu-에서-formal-이-적합한-곳)

---

## G — GIC

### GIC (Generic Interrupt Controller)

**Definition.** 장치 인터럽트를 받아 우선순위를 매기고 대상 코어로 분배·전달하는 ARM의 표준 인터럽트 컨트롤러.

**Source.** ARM Generic Interrupt Controller Architecture Specification.

**Related.** PSTATE (DAIF), Exception Level, Precise Exception.

**Example.** 장치 → Distributor → CPU Interface/Redistributor → 코어 경로로 흐르며, 인터럽트는 SGI/PPI/SPI로 나뉜다.

**See also.** [03 — ARM 아키텍처](../03_arm_architecture/#7-gic--인터럽트가-코어에-닿는-흐름)

---

## I — IPC / ISS

### IPC (Instructions Per Cycle)

**Definition.** 한 클럭 사이클당 평균적으로 retire되는 명령 수로 측정하는 마이크로아키텍처 성능 지표.

**Source.** Hennessy & Patterson, *Computer Architecture*.

**Related.** CPI, Amdahl's Law, Pipeline, Out-of-Order.

**Example.** IPC·파이프라인 stall·캐시 미스율을 성능 카운터로 측정해 pre/post-silicon에서 비교.

**See also.** [02 — CPU 마이크로아키텍처](../02_cpu_microarchitecture/#22-cpi--ipc)

### ISS (Instruction Set Simulator)

**Definition.** 명령어 집합을 스펙대로 한 명령씩 실행해 "정답" 아키텍처 상태를 내놓는 소프트웨어 golden reference.

**Source.** common DV usage.

**Related.** Step-and-Compare, RVFI/Retire Trace, Precise Exception.

**Example.** RTL이 한 명령을 retire할 때마다 ISS를 한 스텝 끌고 가 architectural state를 비교(lockstep).

**See also.** [05 — CPU DV 방법론](../05_cpu_dv_methodology/#3-iss-step-and-compare--cpu-dv-의-심장)

---

## M — Memory Barrier / Memory Consistency Model / MESI / MMU / MOESI

### Memory Barrier (DMB/DSB/ISB)

**Definition.** 약한 순서 모델에서 메모리 접근이나 명령의 순서·완료·재-fetch를 명시적으로 강제하는 동기화 명령.

**Source.** ARM Architecture Reference Manual (AArch64).

**Related.** Acquire/Release, Memory Consistency Model, Weakly-Ordered.

**Example.** DMB는 관측 순서만, DSB는 이전 접근의 완료까지 대기, ISB는 파이프라인 flush 후 재-fetch를 보장한다.

**See also.** [03 — ARM 아키텍처](../03_arm_architecture/#52-dmb--dsb--isb--셋이-왜-별개인가)

### Memory Consistency Model (SC/TSO/Weak)

**Definition.** 멀티프로세서에서 로드/스토어가 어떤 순서로 관찰될 수 있는지를 프로그래머에게 규정하는 계약으로, SC는 모든 순서를 보존하고 TSO는 store→load만 허용하며 weak는 네 종류 재정렬을 모두 허용한다.

**Source.** Sorin, Hill & Wood, *A Primer on Memory Consistency and Cache Coherence*.

**Related.** Memory Barrier, Acquire/Release, Coherence vs Consistency.

**Example.** x86은 TSO, ARM은 weak이라 x86에서 동작하던 lock-free 코드가 ARM에선 barrier 없이 간헐적으로 깨진다.

**See also.** [04 — 일관성·메모리 모델](../04_coherence_and_memory_model/)

### MESI

**Definition.** 각 캐시 라인의 사본을 Modified/Exclusive/Shared/Invalid 4상태로 추적하며 dirty 여부와 독점 여부 두 축으로 관리하는 cache coherence 프로토콜.

**Source.** Papamarcos & Patel, ISCA 1984.

**Related.** MOESI, Snooping, Directory-Based Coherence, Cache.

**Example.** 코어 A가 S → M으로 전이하면 다른 코어의 사본을 I로 invalidate.

**See also.** [04 — 일관성·메모리 모델](../04_coherence_and_memory_model/#2-mesi--4상태와-전이)

### MMU Translation

**Definition.** Virtual address를 page table walk로 physical address와 권한·메모리 속성으로 변환하는, MMU가 수행하는 주소 번역 과정.

**Source.** ARM Architecture Reference Manual (AArch64).

**Related.** TLB, Stage-1/Stage-2 Translation, Exception Level.

**Example.** TTBR가 최상위 테이블을 가리키고 HW가 다단계 walk로 PA를 구한 뒤 결과를 TLB에 채운다.

**See also.** [03 — ARM 아키텍처](../03_arm_architecture/#6-mmu--vapa-번역과-stage-1stage-2)

### MOESI

**Definition.** MESI에 Owned 상태를 추가해, dirty 라인을 메모리에 write-back하지 않고도 다른 캐시와 공유(dirty-sharing)할 수 있게 한 cache coherence 프로토콜.

**Source.** AMD64 Architecture / coherence literature.

**Related.** MESI, Snooping, Directory-Based Coherence.

**Example.** Owner가 dirty 데이터를 메모리 대신 요청 코어에 직접 공급해 write-back 트래픽을 줄인다.

**See also.** [04 — 일관성·메모리 모델](../04_coherence_and_memory_model/#3-moesi--owned-상태의-의미)

---

## P — Pipeline Hazard / Precise Exception / PSTATE

### Pipeline Hazard

**Definition.** 파이프라인에서 다음 명령이 다음 사이클에 정상 실행되지 못하게 하는 상황으로, 자원 충돌(structural)·데이터 의존(data)·분기(control) 세 종류로 분류된다.

**Source.** Hennessy & Patterson, *Computer Architecture*.

**Related.** Forwarding, Branch Prediction, Out-of-Order.

**Example.** load-use data hazard는 forwarding이 완비돼도 1 stall이 필요하다.

**See also.** [02 — CPU 마이크로아키텍처](../02_cpu_microarchitecture/#3-pipeline-hazard-3종과-forwarding)

### Precise Exception

**Definition.** 예외 발생 시 그 직전 명령까지는 아키텍처 상태에 전부 반영되고 그 이후 명령은 전혀 반영되지 않은, 재개 가능한 깨끗한 상태를 보장하는 성질.

**Source.** Hennessy & Patterson, *Computer Architecture*.

**Related.** ROB, Out-of-Order, Speculative Execution, Exception Level.

**Example.** 실행은 OoO여도 ROB가 in-order retire를 강제하므로, 예외 명령이 ROB head에 도달한 시점에 이후 명령을 전부 flush해 precise성을 얻는다.

**See also.** [02 — CPU 마이크로아키텍처](../02_cpu_microarchitecture/#52-precise-exception이-보장되는-메커니즘)

### PSTATE (NZCV/DAIF)

**Definition.** 프로세서의 현재 상태를 담는 필드 집합으로, NZCV(조건 플래그)·DAIF(인터럽트 마스크)·CurrentEL·SPSel 등을 포함하며 AArch32의 CPSR을 필드별로 분리·계승한 것이다.

**Source.** ARM Architecture Reference Manual (AArch64).

**Related.** Exception Level, Precise Exception, Branch Prediction.

**Example.** 예외 진입 시 PSTATE 전체가 SPSR_ELx로 저장되고 `ERET`이 복원하며, NZCV는 조건 분기의 입력이다.

**See also.** [03 — ARM 아키텍처](../03_arm_architecture/#3-pstate--옛-cpsr을-분리계승한-프로세서-상태)

---

## R — RAL / Random Instruction Generator / Register Renaming / Reservation Station / ROB / RVFI

### RAL (Register Abstraction Layer)

**Definition.** 레지스터를 `uvm_reg` 모델로 추상화해 mirror/desired 값·frontdoor/backdoor 접근·자동 체크를 제공하는 UVM 계층.

**Source.** UVM 1.2 Reference Manual.

**Related.** config_db, Factory, Covergroup.

**Example.** CSR(mstatus·mepc 등) 변화를 `predict()`로 mirror에 반영하고 RO/WARL 접근 정책을 검증.

**See also.** [05 — CPU DV 방법론](../05_cpu_dv_methodology/#15-factory--ral--재사용과-csr)

### Random Instruction Generator

**Definition.** 제약을 만족하는 명령 시퀀스(또는 ELF 프로그램)를 무작위로 생성해 CPU의 방대한 상태 공간을 자극하는 도구.

**Source.** common DV usage.

**Related.** Constraint, ISS, Covergroup, RVFI/Retire Trace.

**Example.** X0–X30·SP·LR를 자극하되 호출 규약을 지켜 self-check가 성립하도록 제약한다.

**See also.** [05 — CPU DV 방법론](../05_cpu_dv_methodology/)

### Register Renaming

**Definition.** Architectural register 이름을 별도의 physical register로 매핑해 WAR/WAW 가짜 의존을 제거하고 OoO 실행을 가능하게 하는 기법.

**Source.** Tomasulo, IBM Journal of R&D, 1967.

**Related.** Out-of-Order, ROB, Reservation Station.

**Example.** 같은 r1에 대한 두 번의 쓰기를 서로 다른 물리 레지스터(p10, p11)에 매핑해 이름 충돌을 없앤다.

**See also.** [02 — CPU 마이크로아키텍처](../02_cpu_microarchitecture/#42-register-renaming--가짜-의존-제거)

### Reservation Station

**Definition.** 피연산자가 모두 준비될 때까지 명령을 대기시켰다가 준비되면 실행 유닛으로 발행하는, OoO 코어의 대기 버퍼.

**Source.** Tomasulo's algorithm.

**Related.** Out-of-Order, Register Renaming, ROB.

**Example.** 기다리던 피연산자가 broadcast되면 그 결과를 받아채고 실행 유닛이 비는 대로 issue.

**See also.** [02 — CPU 마이크로아키텍처](../02_cpu_microarchitecture/#43-reservation-station--준비되면-발사)

### ROB (Reorder Buffer)

**Definition.** OoO로 실행된 명령을 프로그램 순서대로 정렬해 두고 head부터 in-order로 commit해 아키텍처 상태를 항상 일관된 지점으로 유지하는 버퍼.

**Source.** Hennessy & Patterson, *Computer Architecture*.

**Related.** Precise Exception, Out-of-Order, Store Buffer, Register Renaming.

**Example.** 예외 명령이 ROB head에 도달하면 이전은 전부 retire·이후는 전부 flush → precise exception.

**See also.** [02 — CPU 마이크로아키텍처](../02_cpu_microarchitecture/#5-rob--in-order-retire와-precise-exception)

### RVFI / Retire Trace

**Definition.** Commit된 명령의 PC·레지스터·메모리 쓰기를 노출하는 표준 retire 인터페이스(RISC-V Formal Interface)로, 이를 통해 step-and-compare와 SVA 불변식 검사를 수행한다.

**Source.** RISC-V Formal Interface (RVFI) specification.

**Related.** ISS, Step-and-Compare, SVA, config_db.

**Example.** monitor가 retire trace(committed PC/regs/mem writes)를 뽑아 ISS와 대조하고 RVFI 불변식을 SVA로 검사.

**See also.** [05 — CPU DV 방법론](../05_cpu_dv_methodology/#3-iss-step-and-compare--cpu-dv-의-심장)

---

## S — SC / Snooping / Speculative Execution / Stage-1·Stage-2 / Step-and-Compare / Store Buffer / Store-to-Load Forwarding / SVA

### Snooping

**Definition.** 모든 캐시가 공유 버스의 트랜잭션을 감시(snoop)하다가 자신이 가진 라인에 관련된 요청이 보이면 상태를 갱신하거나 데이터를 공급하는 브로드캐스트형 coherence 방식.

**Source.** Hennessy & Patterson, *Computer Architecture*.

**Related.** Directory-Based Coherence, MESI, MOESI.

**Example.** 코어 수가 적을 때 효율적이며, 코어가 많아지면 브로드캐스트 트래픽 폭증으로 directory 방식에 자리를 내준다.

**See also.** [04 — 일관성·메모리 모델](../04_coherence_and_memory_model/#4-snooping-vs-directory)

### Speculative Execution

**Definition.** 분기 결과나 의존이 확정되기 전에 명령을 미리 실행하고, 추측이 맞으면 결과를 확정·틀리면 폐기하는 기법.

**Source.** Hennessy & Patterson, *Computer Architecture*.

**Related.** Branch Prediction, ROB, Store Buffer, Precise Exception.

**Example.** 추측 load가 폐기돼도 캐시 상태 변화가 남아 Spectre류 부작용으로 이어질 수 있다.

**See also.** [02 — CPU 마이크로아키텍처](../02_cpu_microarchitecture/#6-control-hazard와-분기-예측)

### Stage-1 / Stage-2 Translation

**Definition.** 가상화 환경에서 주소 번역을 두 단계로 나눈 것으로, stage-1은 게스트의 VA→IPA를 ASID로, stage-2는 하이퍼바이저의 IPA→PA를 VMID로 번역한다.

**Source.** ARM Architecture Reference Manual (AArch64).

**Related.** MMU Translation, TLB, Exception Level.

**Example.** 게스트 OS가 본 "물리" 주소는 IPA일 뿐이고 stage-2가 IPA→PA로 한 번 더 번역해 게스트를 격리한다.

**See also.** [03 — ARM 아키텍처](../03_arm_architecture/#61-stage-1-vs-stage-2--가상화의-2단-번역)

### Step-and-Compare

**Definition.** RTL이 한 명령을 retire할 때마다 ISS를 정확히 한 스텝 진행시켜 두 모델의 architectural state를 명령 단위로 비교하는 CPU DV 검증 기법.

**Source.** common DV usage.

**Related.** ISS, RVFI/Retire Trace, Precise Exception.

**Example.** 명령 #14237에서 RTL x5=0x40 vs ISS x5=0x41 첫 divergence를 즉시 flag.

**See also.** [05 — CPU DV 방법론](../05_cpu_dv_methodology/#3-iss-step-and-compare--cpu-dv-의-심장)

### Store Buffer

**Definition.** 아직 commit되지 않은 store 값을 메모리에 쓰기 전까지 보관하는 큐로, 해당 store가 retire될 때만 메모리에 반영한다.

**Source.** Hennessy & Patterson, *Computer Architecture*.

**Related.** Store-to-Load Forwarding, ROB, Speculative Execution, Memory Consistency Model.

**Example.** 추측 store가 mispredict로 무효화되면 store buffer의 그 엔트리를 그냥 버려 메모리 오염을 막는다.

**See also.** [02 — CPU 마이크로아키텍처](../02_cpu_microarchitecture/#53-store-buffer--speculative-store가-메모리를-오염시키지-않는-법)

### Store-to-Load Forwarding

**Definition.** 아직 메모리에 쓰이지 않은 store 값을 같은 주소의 후속 load에 store buffer에서 직접 넘겨 메모리 접근을 생략하는 최적화.

**Source.** Hennessy & Patterson, *Computer Architecture*.

**Related.** Store Buffer, Forwarding, ROB.

**Example.** 주소가 부분만 겹치는(partial overlap) 경우 잘못 forwarding하면 데이터 corruption이 생기므로 stall해야 한다.

**See also.** [02 — CPU 마이크로아키텍처](../02_cpu_microarchitecture/#8-store-to-load-forwarding과-partial-overlap의-함정)

### SVA (SystemVerilog Assertion)

**Definition.** Sequence와 property로 RTL의 시간적 동작이 의도된 사양을 만족하는지 시뮬레이션 또는 formal에서 검사하는 SystemVerilog 언어 기능.

**Source.** IEEE 1800-2017, §16.

**Related.** Formal Verification, RVFI/Retire Trace, Covergroup.

**Example.** RVFI 불변식(retire 시점 PC 단조 증가 등)을 concurrent assertion으로 검사.

**See also.** [05 — CPU DV 방법론](../05_cpu_dv_methodology/)

---

## T — TLB / TrustZone

### TLB (Translation Lookaside Buffer)

**Definition.** 최근 VA→PA 번역 결과를 캐싱해 매 접근마다 page table walk를 반복하지 않게 하는 작은 캐시.

**Source.** ARM Architecture Reference Manual (AArch64).

**Related.** MMU Translation, Stage-1/Stage-2 Translation, Exception Level.

**Example.** 페이지테이블을 바꾼 뒤 `str pte; dsb; tlbi; dsb; isb` 시퀀스가 빠지면 stale TLB로 잘못된 페이지를 접근한다.

**See also.** [03 — ARM 아키텍처](../03_arm_architecture/#6-mmu--vapa-번역과-stage-1stage-2)

### TrustZone

**Definition.** secure 월드와 non-secure 월드를 EL3의 Secure Monitor가 전환·격리하는 ARM의 하드웨어 보안 분리 기술.

**Source.** ARM Architecture Reference Manual (AArch64).

**Related.** Exception Level, MMU Translation.

**Example.** `SCR_EL3.NS` 비트가 유일한 월드 스위치이자 Root of Trust 역할을 한다.

**See also.** [03 — ARM 아키텍처](../03_arm_architecture/#41-네-레벨의-역할)

---

## V — Virtual Sequence

### Virtual Sequence

**Definition.** 자체 driver 없이 여러 하위 sequencer를 한 sequence에서 조율해 멀티-에이전트 시나리오(예: 멀티코어·메모리 응답·인터럽트 주입)를 한 시점에서 조정하는 UVM sequence.

**Source.** UVM 1.2 Reference Manual.

**Related.** Factory, config_db, Random Instruction Generator.

**Example.** 코어 agent는 passive로 retire만 관찰하고, virtual sequence가 메모리 응답·인터럽트 주입 sequence를 조율한다.

**See also.** [05 — CPU DV 방법론](../05_cpu_dv_methodology/#14-sequence--driver-핸드셰이크--cpu에서-비대칭)

---

## W — Write-Back / Write-Through / Weakly-Ordered

### Weakly-Ordered

**Definition.** 성능을 위해 HW가 Load→Load·Load→Store·Store→Store·Store→Load 네 종류의 메모리 재정렬을 모두 기본 허용하는 메모리 순서 모델.

**Source.** ARM Architecture Reference Manual (AArch64).

**Related.** Memory Consistency Model, Memory Barrier, Acquire/Release.

**Example.** ARM은 weakly-ordered라 공유 변수 핸드오프에 명시적 barrier가 없으면 다른 코어가 순서를 뒤집어 관측할 수 있다.

**See also.** [03 — ARM 아키텍처](../03_arm_architecture/#5-weakly-ordered-메모리-모델과-배리어)

### Write-Back / Write-Through

**Definition.** Write-back은 변경된 라인을 dirty로 표시했다가 eviction 시에만 하위 계층에 기록하는 정책이고, write-through는 모든 쓰기를 즉시 하위 계층까지 전파하는 정책이다.

**Source.** Hennessy & Patterson, *Computer Architecture*.

**Related.** Cache, MESI, False Sharing.

**Example.** write-back은 반복 쓰기를 흡수해 대역폭을 아끼지만 dirty 추적·snoop 응답으로 코히런시 로직이 복잡하다.

**See also.** [02 — CPU 마이크로아키텍처](../02_cpu_microarchitecture/#73-write-back-vs-write-through--trade-off)
