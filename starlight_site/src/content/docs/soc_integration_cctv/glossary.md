---
title: "SoC Integration (CCTV) 용어집"
---

핵심 용어 ISO 11179 형식 정의.

---

## C — CCTV / Common Task / CDC

### CCTV (Common Task Coverage Verification)

**Definition.** SoC 내 모든(또는 대부분의) IP에 공통으로 적용되어야 하는 검증 항목들이 빠짐없이 수행되었는지 추적하는 coverage 방법론.

**Source.** DVCon 2025 paper (ManGoBoost).

**Related.** Common Task, Coverage matrix, Virtual Sequencer.

**Example.** IP 축(X)과 Common Task 축(Y)으로 구성된 2차원 매트릭스에서 각 cell이 `covered` 또는 명시적 `N/A`가 될 때 sign-off 조건을 충족한다.

**See also.** [Module 02](../02_common_task_cctv/)

### Common Task

**Definition.** SoC 내 다수 IP에 공통으로 적용되는 검증 작업으로, 개별 IP의 고유 기능과 독립적으로 플랫폼 수준의 규칙(sysMMU, Security, DVFS, Clock Gating 등)이 각 IP에서 올바르게 동작하는지 확인하는 시나리오 단위.

**Source.** SoC verification methodology.

**Related.** CCTV, sequence library, Virtual Sequencer.

**Example.** `generic_dvfs_seq`를 GPU, DMA, NIC 각각의 sequencer에 `start()`하여 동일한 DVFS 전환 시나리오를 세 IP에 적용한다.

**See also.** [Module 02](../02_common_task_cctv/)

### CDC (Clock Domain Crossing)

**Definition.** 서로 다른 clock domain 간 신호 전달 시 발생하는 metastability 문제와 그 해결 메커니즘.

**Source.** Digital design literature.

**Related.** Synchronizer, FIFO, Gray code.

**Example.** 50 MHz domain의 신호를 200 MHz domain에서 직접 샘플링하면 setup/hold 위반으로 값이 불확정 상태에 빠질 수 있으며, 이를 방지하기 위해 2-stage synchronizer 또는 async FIFO를 삽입한다.

**See also.** [Module 01](../01_soc_top_integration/)

---

## D — DVFS

### DVFS (Dynamic Voltage and Frequency Scaling)

**Definition.** 워크로드에 따라 voltage와 clock frequency를 동적으로 조정해 전력을 절감하는 기법.

**Source.** Power management literature.

**Related.** Common Task, retention, Clock Gating.

**Example.** 영상 처리 부하가 높아지면 GPU 도메인의 주파수를 높이고 전압을 상승시키고, 유휴 상태에서는 낮은 주파수와 전압으로 전환하는 시나리오가 CCTV Common Task에 포함된다.

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

**Related.** Common Task, Security/Access Control.

**Example.** DMA 엔진이 물리 주소 0x8000_0000에 직접 접근하는 대신, sysMMU를 통해 가상 주소를 발급받아 페이지 테이블 기반으로 격리된 메모리 영역에만 접근하도록 제한하는 시나리오가 Common Task에 포함된다.

**See also.** [MMU Module 04](../../mmu/04_iommu_smmu/)

---

## V — Virtual Sequencer / Virtual Sequence

### Virtual Sequencer

**Definition.** UVM의 multi-agent 환경에서 sub-sequencer 핸들들을 보유하고, 시스템 레벨 시나리오를 조정하는 sequencer.

**Source.** UVM 1.2 Reference Manual.

**Related.** Virtual Sequence, Common Task, CCTV.

**Example.** `my_vsqr`가 `apb_sequencer reg_sqr`와 `axi_sequencer mem_sqr`를 멤버로 가지며, virtual sequence가 `p_sequencer.reg_sqr`와 `p_sequencer.mem_sqr`를 통해 두 인터페이스를 순서대로 구동한다.

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
