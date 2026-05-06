# SoC Integration (CCTV) 용어집

핵심 용어 ISO 11179 형식 정의.

---

## C — CCTV / Common Task / CDC

### CCTV (Common Task Coverage Verification)

**Definition.** SoC 내 모든(또는 대부분의) IP에 공통으로 적용되어야 하는 검증 항목들이 빠짐없이 수행되었는지 추적하는 coverage 방법론.

**Source.** DVCon 2025 paper (ManGoBoost).

**Related.** Common Task, Coverage matrix.

**See also.** [Module 02](02_common_task_cctv.md)

### Common Task

**Definition.** SoC 내 다수 IP에 공통으로 적용되는 검증 작업 (sysMMU access, Security 권한, DVFS, Clock Gating 등).

**Source.** SoC verification methodology.

**Related.** CCTV, sequence library.

**See also.** [Module 02](02_common_task_cctv.md)

### CDC (Clock Domain Crossing)

**Definition.** 서로 다른 clock domain 간 신호 전달 시 발생하는 metastability 문제와 그 해결 메커니즘.

**Source.** Digital design literature.

**Related.** Synchronizer, FIFO, Gray code.

**See also.** [Module 01](01_soc_top_integration.md)

---

## D — DVFS

### DVFS (Dynamic Voltage and Frequency Scaling)

**Definition.** 워크로드에 따라 voltage와 clock frequency를 동적으로 조정해 전력을 절감하는 기법.

**Source.** Power management literature.

**Related.** Common Task, retention.

---

## I — IP / Interconnect

### IP (Intellectual Property)

**Definition.** SoC를 구성하는 재사용 가능한 design block (CPU, GPU, DMA, peripheral 등).

### Interconnect

**Definition.** SoC 내 IP 간 통신을 매개하는 fabric (NoC, AMBA AXI bus 등).

---

## R — RAL

### RAL (Register Abstraction Layer)

**Definition.** UVM의 register 모델 추상화로, DUT의 register map을 SystemVerilog object로 표현해 SW 시뮬레이션 동등 access를 가능하게 함.

**Source.** UVM 1.2 Reference Manual, §18.

**Related.** uvm_reg_block, mirror, predict.

**See also.** [UVM Module 04](../../uvm/04_config_db_factory/)

---

## S — SoC / SubsystemID

### SoC (System-on-Chip)

**Definition.** CPU + GPU + memory controller + 다수 peripheral을 단일 silicon에 통합한 chip.

### sysMMU

**Definition.** SoC 레벨 IOMMU/SMMU. CPU 외 device 마스터의 memory access를 가상 주소로 격리.

**See also.** [MMU Module 04](../../mmu/04_iommu_smmu/)

---

## V — Virtual Sequencer / Virtual Sequence

### Virtual Sequencer

**Definition.** UVM의 multi-agent 환경에서 sub-sequencer 핸들들을 보유하고, 시스템 레벨 시나리오를 조정하는 sequencer.

**Source.** UVM 1.2 Reference Manual.

**See also.** [UVM Module 03](../../uvm/03_sequence_and_item/)

---

## 추가 약어

| 약어 | 풀네임 | 의미 |
|------|--------|------|
| **TB** | Testbench | 검증 환경 전체 |
| **DUT** | Device Under Test | 검증 대상 |
| **VIP** | Verification IP | 재사용 검증 IP |
| **NoC** | Network-on-Chip | 패킷 스위칭 인터커넥트 |
| **SCB** | Scoreboard | 결과 비교 컴포넌트 |
| **CG** | Covergroup | 기능 커버리지 단위 |
| **LLM** | Large Language Model | AI 자동화의 핵심 |
| **POR** | Power-On Reset | 시스템 첫 reset |
| **DFT** | Design For Test | scan/BIST 등 테스트 회로 |
