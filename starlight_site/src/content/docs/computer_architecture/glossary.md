---
title: "Computer Architecture 용어집"
---

이 페이지는 본 코스에서 사용되는 컴퓨터 구조 핵심 용어 정의 모음입니다. 항목은 ISO 11179 형식을 따릅니다 (**Definition / Source / Related / Example / See also**).

:::tip[검색 활용]
상단 검색창에 용어를 입력하면 본문에서의 사용처도 함께 찾을 수 있습니다.
:::
---

## A — Amdahl's Law / Arithmetic Intensity

### Amdahl's Law

**Definition.** 프로그램의 병렬화 가능 비율 f 와 그 부분의 speedup S 로 전체 speedup 을 `1/((1−f)+f/S)` 로 산출하는 성능 상한 법칙.

**Source.** Hennessy & Patterson, *Computer Architecture: A Quantitative Approach*.

**Related.** 직렬 비율(1−f), 멀티코어 스케일링, 가속기 오프로드, Iron Law.

**Example.** f=0.95 면 S→∞ 라도 전체 speedup 은 1/(1−0.95)=20× 가 천장.

**See also.** [Module 05 — 성능 법칙 & 이종 SoC/DSA](../05_performance_laws_dsa/)

### Arithmetic Intensity (AI)

**Definition.** 커널이 수행하는 부동소수점 연산 수를 DRAM 트래픽 바이트 수로 나눈, FLOP/byte 단위의 연산 밀도 지표.

**Source.** Williams, Waterman & Patterson, *Roofline: An Insightful Visual Performance Model*.

**Related.** Roofline, memory-bandwidth bound, compute bound.

**Example.** 스트리밍 memcpy 는 AI ≈ 0.08 FLOP/byte 로 memory-bandwidth bound, dense matmul 은 AI ~ N/2 로 compute bound.

**See also.** [Module 05](../05_performance_laws_dsa/)

---

## C — Cache Line / CPI

### Cache Line (Block)

**Definition.** 캐시 계층 간 전송의 최소 단위가 되는 연속된 바이트 묶음(전형적으로 64 byte).

**Source.** Hennessy & Patterson, *Computer Architecture: A Quantitative Approach*.

**Related.** Spatial locality, set, way, tag/index/offset.

**Example.** 64-byte 라인은 한 워드 접근 시 인접 워드까지 함께 캐시에 적재해 공간 지역성을 활용.

**See also.** [Module 04 — 메모리 계층](../04_memory_hierarchy/)

### CPI (Cycles Per Instruction)

**Definition.** 한 명령을 완료하는 데 평균적으로 소요되는 클럭 사이클 수.

**Source.** Hennessy & Patterson, *Computer Architecture: A Quantitative Approach*.

**Related.** Iron Law, 파이프라인 해저드, cache miss, 분기 misprediction.

**Example.** 이상적 5-stage 파이프라인 CPI=1; load-use bubble·분기 페널티·cache miss 가 더해져 실제 CPI 는 1 보다 큼.

**See also.** [Module 02 — Pipeline & Hazard](../02_pipeline_hazard/), [Module 05](../05_performance_laws_dsa/)

---

## D — Data Hazard / DRAM Row Hit / DSA

### Data Hazard

**Definition.** 한 명령이 아직 write-back 되지 않은 이전 명령의 결과 레지스터에 의존할 때 발생하는 파이프라인 위험(RAW/WAW/WAR).

**Source.** Patterson & Hennessy, *Computer Organization and Design*.

**Related.** RAW, forwarding, load-use hazard, register renaming.

**Example.** `ADD x1,x2,x3` 직후 `SUB x4,x1,x5` 의 RAW 의존은 EX→EX forwarding 으로 stall 없이 해소.

**See also.** [Module 02](../02_pipeline_hazard/)

### DRAM Row Hit / Row Miss

**Definition.** 요청한 column 이 이미 활성화된 row 에 속하면 CAS 만으로 빠르게 접근(row hit)하고, 다른 row 면 precharge+RAS+CAS 가 필요해 느린(row miss) DRAM 접근 상태.

**Source.** Hennessy & Patterson, *Computer Architecture: A Quantitative Approach*.

**Related.** Bank, RAS, CAS, tRCD/CL/tRP, 메모리 컨트롤러 재정렬.

**Example.** DDR5 에서 row hit 은 CL(~14 ns)만, row miss 는 ~28–40 ns 추가 — 컨트롤러가 row hit 최대화를 위해 요청을 재정렬.

**See also.** [Module 04](../04_memory_hierarchy/)

### DSA (Domain-Specific Architecture)

**Definition.** 특정 워크로드에 맞춰 범용성 오버헤드를 제거해 에너지 효율을 극대화한 도메인 특화 하드웨어 아키텍처.

**Source.** Hennessy & Patterson, *Computer Architecture: A Quantitative Approach*.

**Related.** Dark silicon, Power Wall, TPU systolic array, Tensor Core.

**Example.** Google TPU v1 은 matmul systolic array 와 on-chip weight SRAM 으로 DRAM 트래픽을 줄여 범용 CPU 대비 10–1000× 에너지 효율.

**See also.** [Module 05](../05_performance_laws_dsa/)

---

## F — Forwarding

### Forwarding (Bypassing)

**Definition.** EX 단계의 ALU 결과를 레지스터 파일을 거치지 않고 다음 명령의 EX 입력으로 직접 전달해 RAW stall 을 제거하는 파이프라인 기법.

**Source.** Patterson & Hennessy, *Computer Organization and Design*.

**Related.** Data hazard, load-use hazard, bubble.

**Example.** 산술→산술 RAW 는 EX→EX forwarding 으로 stall 0; 단 load-use 는 데이터가 MEM 끝에야 나와 1 bubble 불가피.

**See also.** [Module 02](../02_pipeline_hazard/)

---

## I — ISA / Iron Law

### ISA (Instruction Set Architecture)

**Definition.** programmer-visible 상태(레지스터·메모리 모델·특권 레벨), 명령 인코딩, 명령 의미를 규정하는 하드웨어와 소프트웨어 사이의 계약.

**Source.** *The RISC-V Instruction Set Manual, Volume I: Unprivileged ISA*; Patterson & Hennessy, *Computer Organization and Design*.

**Related.** RISC, RISC-V, architectural state, micro-op.

**Example.** RISC-V 의 `x0` hardwired zero, load/store 아키텍처는 ISA 가 규정하는 계약 조항으로, 같은 ISA 를 in-order/OoO 어느 구현으로도 만들 수 있음.

**See also.** [Module 01 — ISA & RISC-V](../01_isa_riscv/)

### Iron Law of Performance

**Definition.** CPU 실행 시간을 명령 수·CPI·클럭 사이클 시간의 곱(`CPU Time = IC × CPI × Cycle Time`)으로 분해하는 성능 정량화 식.

**Source.** Hennessy & Patterson, *Computer Architecture: A Quantitative Approach*.

**Related.** IC, CPI, Clock Frequency, Amdahl's Law, 파이프라인 깊이.

**Example.** IC 10% 감소·CPI 20% 증가·주파수 동일이면 상대 CPU Time = 0.9×1.2 = 1.08 → 성능 8% 악화.

**See also.** [Module 05](../05_performance_laws_dsa/)

---

## M — Memory Wall / Miss (3C)

### Memory Wall

**Definition.** 프로세서 사이클 시간과 메모리 접근 시간이 100–1000× 로 벌어져 메모리 지연이 성능을 지배하게 된 현상.

**Source.** Hennessy & Patterson, *Computer Architecture: A Quantitative Approach*.

**Related.** 메모리 계층, 캐시, AMAT, Roofline.

**Example.** L1 hit ~4 cycle 대 DRAM ~100+ cycle 의 격차를 메모리 계층(register→L1→L2→L3→DRAM)으로 완화.

**See also.** [Module 04](../04_memory_hierarchy/)

### Miss (3C: Compulsory / Capacity / Conflict)

**Definition.** 캐시 miss 를 발생 원인에 따라 첫 접근(compulsory), 용량 초과(capacity), set 충돌(conflict)로 분류하는 모델.

**Source.** Hennessy & Patterson, *Computer Architecture: A Quantitative Approach*.

**Related.** Associativity, working set, cache line.

**Example.** conflict miss 는 같은 set 에 매핑되는 블록들이 서로를 반복 축출할 때 발생하며 associativity 를 높이면 감소.

**See also.** [Module 04](../04_memory_hierarchy/)

---

## O — Out-of-Order Execution

### Out-of-Order (OoO) Execution

**Definition.** 명령 윈도우에서 operand 가 준비된 명령을 프로그램 순서와 무관하게 functional unit 에 issue 하되, retirement 는 in-order 로 유지하는 실행 방식.

**Source.** Hennessy & Patterson, *Computer Architecture: A Quantitative Approach*.

**Related.** Tomasulo, Reservation Station, Common Data Bus, ROB, register renaming.

**Example.** cache-miss 한 load 뒤의 독립 명령을 먼저 실행하되, architectural state 는 ROB 가 program order 로 commit.

**See also.** [Module 03 — OoO 실행 & 분기 예측](../03_ooo_branch_prediction/)

---

## R — Reorder Buffer / RISC / Roofline

### Reorder Buffer (ROB)

**Definition.** 명령을 dispatch 시 순서대로 넣고 retire 시 순서대로 빼서 out-of-order 실행 중에도 precise exception 과 speculation 을 가능케 하는 순환 버퍼.

**Source.** Hennessy & Patterson, *Computer Architecture: A Quantitative Approach*.

**Related.** OoO, precise exception, speculation, squash.

**Example.** 분기 misprediction 시 ROB 의 해당 분기 이후 모든 명령을 squash 해 architectural state 일관성 유지.

**See also.** [Module 03](../03_ooo_branch_prediction/)

### RISC (Reduced Instruction Set Computing)

**Definition.** 고정 길이 명령·load/store 아키텍처·대형 레지스터 파일·hardwired control 을 채택해 빠른 파이프라이닝을 가능케 한 ISA 설계 철학.

**Source.** Patterson & Hennessy, *Computer Organization and Design*.

**Related.** CISC, RISC-V, 파이프라인, micro-op.

**Example.** 현대 x86 은 외부적으로 CISC 이지만 내부적으로 RISC-like micro-op 으로 변환해 OoO 백엔드에서 실행.

**See also.** [Module 01](../01_isa_riscv/)

### Roofline Model

**Definition.** 커널의 성능 상한을 compute roof(peak FLOP/s)와 memory roof(arithmetic intensity × peak bandwidth)의 최솟값으로 특성화하는 시각적 성능 모델.

**Source.** Williams, Waterman & Patterson, *Roofline: An Insightful Visual Performance Model*.

**Related.** Arithmetic Intensity, compute bound, memory-bandwidth bound.

**Example.** AI 가 낮은 DMA copy 는 memory roof 에 막혀 compute 추가가 무익하므로 bandwidth(HBM/PIM)를 늘려야 함.

**See also.** [Module 05](../05_performance_laws_dsa/)

---

## S — Speculative Execution

### Speculative Execution

**Definition.** 분기 예측에 기반해 미해결 분기 너머의 명령을 미리 실행하고, 분기가 옳게 해결될 때만 ROB 에서 commit 하는 실행 방식.

**Source.** Hennessy & Patterson, *Computer Architecture: A Quantitative Approach*.

**Related.** 분기 예측, ROB, squash, Spectre/Meltdown.

**Example.** misprediction 시 architectural state 는 squash 로 복원되지만, speculative load 가 남긴 캐시 타이밍 흔적은 복원되지 않아 Spectre/Meltdown 의 누출 경로가 됨.

**See also.** [Module 03](../03_ooo_branch_prediction/)

---

## T — TLB / Tomasulo

### TLB (Translation Lookaside Buffer)

**Definition.** 최근 가상→물리 페이지 매핑을 저장하는 작고 빠른 fully-associative 캐시.

**Source.** Hennessy & Patterson, *Computer Architecture: A Quantitative Approach*.

**Related.** Page table walk, page fault, huge page, IOMMU.

**Example.** TLB miss 는 page table walk 를 유발하고, PTE 부재 시 page fault 로 OS 가 페이지를 로드 — huge page 로 TLB 압력 완화.

**See also.** [Module 04](../04_memory_hierarchy/)

### Tomasulo's Algorithm

**Definition.** Reservation Station, Common Data Bus, Register Renaming 을 사용해 동적으로 명령을 out-of-order 로 스케줄링하는 알고리즘.

**Source.** Hennessy & Patterson, *Computer Architecture: A Quantitative Approach*.

**Related.** Reservation Station, CDB, register renaming, OoO, WAR/WAW.

**Example.** functional unit 이 완료 시 결과+tag 를 CDB 로 방송하면 그 tag 를 기다리던 모든 RS 가 operand 를 capture.

**See also.** [Module 03](../03_ooo_branch_prediction/)

---

## W — Write-Back

### Write-Back (Cache Policy)

**Definition.** hit 시 캐시 라인만 갱신하고 dirty bit 를 세운 뒤 축출 시에만 하위 계층에 기록하는 캐시 쓰기 정책.

**Source.** Hennessy & Patterson, *Computer Architecture: A Quantitative Approach*.

**Related.** Write-through, write-allocate, dirty bit, cache coherence.

**Example.** write-back 캐시에서 dirty 라인이 축출되기 전까지 메모리는 stale 하며, 진짜 최신 값은 캐시에 존재 — coherence 검증의 핵심.

**See also.** [Module 04](../04_memory_hierarchy/)

---

## 추가 약어

| 약어 | 풀네임 | 한 줄 의미 |
|------|--------|-----------|
| **IC** | Instruction Count | 실행되는 명령 수 (Iron Law 의 한 축) |
| **ILP** | Instruction-Level Parallelism | 순차 명령 스트림에서 병렬 실행 가능한 정도 |
| **RS** | Reservation Station | functional unit 앞의 operand 대기 슬롯 |
| **CDB** | Common Data Bus | 완료 결과+tag 를 RS 들에 방송하는 버스 |
| **AMAT** | Average Memory Access Time | HitTime + MissRate × MissPenalty |
| **HBM** | High Bandwidth Memory | interposer 위 3D-stacked DRAM, DDR 대비 4–8× bandwidth |
| **PIM** | Processing-in-Memory | DRAM 배열 내 논리로 데이터 이동 없이 연산 |
| **PTW** | Page Table Walker | TLB miss 시 페이지 테이블을 순회하는 하드웨어 |
