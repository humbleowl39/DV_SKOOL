---
title: "DRAM / DDR 용어집"
---

핵심 용어 ISO 11179 형식 정의.

---

## A — ACT

### ACT (Activate)

**Definition.** DRAM의 row 데이터를 sense amplifier로 옮기는 명령으로, 이후 RD/WR가 가능해진다.

**Source.** JEDEC DDR4/5 spec.

**Related.** PRE, tRCD, Bank.

**Timing.** ACT → RD/WR 사이 tRCD 만족 필요.

**See also.** [Module 01](../01_dram_fundamentals_ddr/)

---

## B — Bank / Bank Group

### Bank

**Definition.** DRAM cell의 독립 access 단위로, 동시에 다른 bank를 ACT/RD/WR 가능 → bank-level parallelism의 기반.

**Source.** JEDEC DDR4/5 spec.

**Related.** Bank Group, ACT, BLP.

**Count.** DDR4: 16 banks (4 BG × 4 banks). DDR5: 32 banks (8 BG × 4 banks).

### Bank Group (BG)

**Definition.** I/O 회로와 데이터 경로 일부를 공유하는 bank들의 논리적 그룹으로, DDR4에서 도입된 JEDEC 개념.

**Source.** JEDEC DDR4+.

**Related.** Bank, tCCD_S, tCCD_L, BLP.

**Example.** 같은 BG 내 연속 접근에는 tCCD_L(긴 간격)이, 다른 BG 간 접근에는 tCCD_S(짧은 간격)가 적용된다. 스케줄러가 요청을 다른 BG로 분산하면 tCCD_S를 활용해 throughput을 높일 수 있다.

**See also.** [Module 02](../02_memory_controller/)

---

## C — CAS / CL

### CAS (Column Access Strobe) / CL (CAS Latency)

**Definition.** RD/WR 명령 발행에서 첫 데이터까지의 cycle 수로, MR0에 프로그래밍.

**Source.** JEDEC.

**Related.** tCAS, CWL (CAS Write Latency).

**Example.** DDR4-3200 CL=22 → 22 cycle 후 첫 data.

**See also.** [Module 01](../01_dram_fundamentals_ddr/)

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

**See also.** [Module 03](../03_memory_interface_phy/)

### DFE (Decision Feedback Equalizer)

**Definition.** 이전에 수신·판정된 비트들의 결과를 피드백으로 사용해 현재 수신 비트에 얹힌 ISI 성분을 디지털적으로 제거하는 수신단 equalization 기법.

**Source.** Signal integrity literature.

**Related.** CTLE, ISI, eye opening.

**Example.** CTLE가 선형으로 전체 주파수 성분을 부스트하는 것과 달리, DFE는 이전 비트 패턴을 알고 있으므로 노이즈 증폭 없이 ISI만 선별 제거한다. PHY 수신단에서 CTLE + DFE를 함께 사용하는 경우가 많다.

**See also.** [Module 03](../03_memory_interface_phy/)

---

## E — ECC

### ECC (Error Correction Code)

**Definition.** 메모리 데이터의 비트 에러를 검출/수정하는 코드로, DDR5는 on-die SECDED + 외부 SECDED 조합 가능.

**Source.** JEDEC, Hamming code variants.

**Related.** SECDED, scrubbing, on-die ECC.

**Example.** SECDED = single-error correct, double-error detect.

**See also.** [Module 02](../02_memory_controller/)

---

## P — PHY / PRE

### PHY (Physical Layer)

**Definition.** MC와 DRAM 사이의 물리 신호 변환 + timing calibration을 담당하는 IP.

**Source.** Memory PHY spec (ARM, Synopsys, Cadence).

**Related.** DLL, training, ZQ.

**See also.** [Module 03](../03_memory_interface_phy/)

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

**See also.** [Module 02](../02_memory_controller/)

### Row Hit

**Definition.** 요청 주소가 해당 bank에 이미 활성화된 row에 속해 ACT 없이 tCAS만으로 접근이 완료되는 상태.

**Source.** Memory access patterns.

**Related.** Row Buffer, Locality, Row Miss, tCAS.

**Example.** 같은 캐시라인을 반복 접근하거나 순차 column 접근이 이어질 때 Row Hit가 연속 발생해 최고 throughput이 나온다. 반대로 다른 row로 전환하면 PRE + ACT 비용(tRP + tRCD)이 추가된다.

**See also.** [Module 02](../02_memory_controller/)

---

## T — Training

### Training

**Definition.** 전원 인가 또는 PVT 변화 후 PHY가 최적 timing margin을 찾기 위해 수행하는 일련의 캘리브레이션 절차.

**Source.** JEDEC PHY spec.

**Related.** ZQ Calibration, retraining, Write Leveling, CA Training, VREF Training.

**Example.** Write Leveling은 CK와 DQS의 위상을 정렬하고, Read DQ Training은 read eye의 중앙점을 탐색한다. Training이 marginal pass로 완료되면 정상 조건에서는 동작하지만 PVT stress에서 bit error가 발생하는 silent corruption 위험이 있다.

**See also.** [Module 03](../03_memory_interface_phy/)

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
