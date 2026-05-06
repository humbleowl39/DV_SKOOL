# DRAM / DDR 용어집

핵심 용어 ISO 11179 형식 정의.

---

## A — ACT

### ACT (Activate)

**Definition.** DRAM의 row 데이터를 sense amplifier로 옮기는 명령으로, 이후 RD/WR가 가능해진다.

**Source.** JEDEC DDR4/5 spec.

**Related.** PRE, tRCD, Bank.

**Timing.** ACT → RD/WR 사이 tRCD 만족 필요.

**See also.** [Module 01](01_dram_fundamentals_ddr.md)

---

## B — Bank / Bank Group

### Bank

**Definition.** DRAM cell의 독립 access 단위로, 동시에 다른 bank를 ACT/RD/WR 가능 → bank-level parallelism의 기반.

**Source.** JEDEC DDR4/5 spec.

**Related.** Bank Group, ACT, BLP.

**Count.** DDR4: 16 banks (4 BG × 4 banks). DDR5: 32 banks (8 BG × 4 banks).

### Bank Group (BG)

**Definition.** I/O 센스 앰프와 데이터 경로를 공유하는 bank들의 그룹으로, 같은 BG 내 연속 access는 tCCD_L (긴 간격), 다른 BG 간은 tCCD_S (짧음) 적용.

**Source.** JEDEC DDR4+.

**Use.** Scheduler가 다른 BG로 분산 access → bandwidth ↑.

**See also.** [Module 02](02_memory_controller.md)

---

## C — CAS / CL

### CAS (Column Access Strobe) / CL (CAS Latency)

**Definition.** RD/WR 명령 발행에서 첫 데이터까지의 cycle 수로, MR0에 프로그래밍.

**Source.** JEDEC.

**Related.** tCAS, CWL (CAS Write Latency).

**Example.** DDR4-3200 CL=22 → 22 cycle 후 첫 data.

**See also.** [Module 01](01_dram_fundamentals_ddr.md)

---

## D — DDR / DLL / DFE

### DDR (Double Data Rate)

**Definition.** 클럭의 상승/하강 엣지 모두에서 데이터를 전송해 동일 클럭 주파수에서 2배 throughput을 제공하는 SDRAM 표준.

**Source.** JEDEC DDR1-5.

**Related.** SDR, DDR4, DDR5, LPDDR5.

### DLL (Delay-Locked Loop)

**Definition.** 클럭과 데이터의 위상을 정렬하기 위한 지연 회로로, PHY의 핵심 timing 요소.

**Source.** Memory PHY architecture.

**Related.** PLL, DQS, training.

**See also.** [Module 03](03_memory_interface_phy.md)

### DFE (Decision Feedback Equalizer)

**Definition.** 이전 비트의 ISI를 디지털로 제거해 수신단 eye를 복원하는 equalization 기법.

**Source.** Signal integrity literature.

**Related.** CTLE, ISI, eye opening.

**See also.** [Module 03](03_memory_interface_phy.md)

---

## E — ECC

### ECC (Error Correction Code)

**Definition.** 메모리 데이터의 비트 에러를 검출/수정하는 코드로, DDR5는 on-die SECDED + 외부 SECDED 조합 가능.

**Source.** JEDEC, Hamming code variants.

**Related.** SECDED, scrubbing, on-die ECC.

**Example.** SECDED = single-error correct, double-error detect.

**See also.** [Module 02](02_memory_controller.md)

---

## P — PHY / PRE

### PHY (Physical Layer)

**Definition.** MC와 DRAM 사이의 물리 신호 변환 + timing calibration을 담당하는 IP.

**Source.** Memory PHY spec (ARM, Synopsys, Cadence).

**Related.** DLL, training, ZQ.

**See also.** [Module 03](03_memory_interface_phy.md)

### PRE (Precharge)

**Definition.** 활성화된 row를 close하고 다른 row를 ACT 가능 상태로 만드는 명령.

**Source.** JEDEC.

**Related.** ACT, tRP.

**Timing.** PRE → ACT 사이 tRP 만족 필요.

---

## R — REF / Row Hit

### REF (Refresh)

**Definition.** DRAM cell의 capacitor 누설을 보충하기 위해 주기적으로 row 내용을 다시 쓰는 명령.

**Source.** JEDEC.

**Related.** tREFI, tRFC, retention.

**Period.** tREFI 마다 1번 refresh. 64ms 내 모든 row가 한 번 이상.

**See also.** [Module 02](02_memory_controller.md)

### Row Hit

**Definition.** 이미 active 상태인 row에 RD/WR access — PRE-ACT 회피로 throughput ↑.

**Source.** Memory access patterns.

**Related.** Row Buffer, Locality.

**See also.** [Module 02](02_memory_controller.md)

---

## T — Training

### Training

**Definition.** PHY의 timing margin을 PVT 변동에 맞춰 보정하는 일련의 캘리브레이션 (Write Leveling, Read DQ, CA, VREF 등).

**Source.** JEDEC PHY spec.

**Related.** ZQ Calibration, retraining, BL2.

**See also.** [Module 03](03_memory_interface_phy.md)

---

## 추가 약어

| 약어 | 풀네임 | 의미 |
|------|--------|------|
| **MC** | Memory Controller | 메모리 access 스케줄러 |
| **MI** | Memory Interface | MC와 PHY를 묶은 단위 |
| **DRAM** | Dynamic RAM | capacitor 기반 휘발성 메모리 |
| **SDRAM** | Synchronous DRAM | 클럭 동기 DRAM |
| **MR** | Mode Register | DRAM 설정 저장 register |
| **MRS** | Mode Register Set | MR 프로그래밍 명령 |
| **ZQ** | — | impedance calibration 신호 |
| **DQ** | Data | 데이터 버스 |
| **DQS** | Data Strobe | 데이터 sample용 strobe |
| **CK** | Clock | 시스템 클럭 |
| **WCK** | Write Clock | LPDDR5의 데이터 전용 클럭 |
| **CA** | Command/Address | 명령/주소 버스 |
| **CKE** | Clock Enable | DRAM 클럭 입력 활성화 |
| **CTLE** | Continuous Time Linear Equalizer | 아날로그 equalization |
| **ISI** | Inter-Symbol Interference | 비트 간 간섭 |
| **PVT** | Process/Voltage/Temperature | 시리콘 변동 요인 |
| **tRCD** | Row to Column Delay | ACT→RD 최소 간격 |
| **tRP** | Row Precharge | PRE→ACT 최소 간격 |
| **tRAS** | Row Active Strobe | ACT→PRE 최소 시간 |
| **tRC** | Row Cycle | ACT→ACT 같은 row 간격 |
| **tREFI** | Refresh Interval | refresh 주기 |
| **tFAW** | Four ACT Window | 4 ACT 사이 시간 (LPDDR4+) |
| **tCCD_S/L** | CAS-to-CAS Short/Long | 같은/다른 BG cycle 간격 |
