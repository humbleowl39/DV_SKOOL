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

**Count.** LPDDR5: MR로 모드 선택 — BG 모드(4 BG × 4 = 16) / 8B 모드(8) / 16B 모드(16), 최대 16 banks. DDR5: 32 banks (8 BG × 4). LPDDR4: BG 없는 8 banks. DDR4: 16 banks (4 BG × 4).

### Bank Mode (LPDDR5)

**Definition.** LPDDR5에서 Mode Register로 bank 구성을 BG 모드(16뱅크)·8B 모드(8뱅크)·16B 모드(16뱅크) 중 하나로 선택하는 설정이다.

**Source.** JEDEC JESD209-5 (LPDDR5).

**Related.** Bank Group, tCCD_S, tCCD_L.

**Example.** BG 모드는 Bank Group 인터리빙으로 tCCD_S를 활용하고, 16B 모드는 BG 없이 16개 bank의 parallelism을 제공한다. DDR5의 고정 32뱅크(8 BG)와 달리 LPDDR5는 최대 16뱅크다.

**See also.** [Module 01](../01_dram_fundamentals_ddr/)

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

**Definition.** 메모리 데이터의 비트 에러를 검출/수정하는 코드.

**Source.** JEDEC, Hamming code variants.

**Related.** SECDED, scrubbing, On-die ECC, Link ECC.

**Example.** SECDED = single-error correct, double-error detect. DDR5/LPDDR5는 on-die ECC + 외부 SECDED 조합이 가능하다.

**See also.** [Module 02](../02_memory_controller/)

### On-die ECC

**Definition.** DRAM 칩 내부에서 셀에 저장된 워드의 단일 비트 에러를 자동 정정하는 ECC로, 호스트에게 투명하게 동작한다.

**Source.** JEDEC DDR5 / LPDDR5 spec.

**Related.** Link ECC, SECDED, ECC.

**Example.** DDR5 표준이며 LPDDR5도 디바이스에 따라 탑재한다. 워드 내 1-bit만 정정하므로 multi-bit/chipkill은 외부 SECDED가 필요하다. 보호 대상은 셀 내부 비트로, Link ECC(전송경로)와 직교한다.

**See also.** [Module 01](../01_dram_fundamentals_ddr/)

### Link ECC

**Definition.** DQ 전송경로(링크)에서 발생하는 비트 에러를 검출/정정하는 LPDDR5 고유의 ECC로, DDR5에는 없다.

**Source.** JEDEC JESD209-5 (LPDDR5).

**Related.** On-die ECC, ECC, DQ.

**Example.** On-die ECC가 셀 내부 비트를 보호하는 것과 달리 Link ECC는 채널/SI 결함을 담당하므로 둘은 직교한다. 저전압(VDDQ 0.5V) 고속 전송의 링크 신뢰성 확보가 목적이다.

**See also.** [Module 01](../01_dram_fundamentals_ddr/)

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

**Related.** tREFI, tRFC, retention, PASR.

**Period.** tREFI는 REF 명령의 평균 발행 간격(DDR4 ≈ 7.8 µs, DDR5/LPDDR5 ≈ 3.9 µs)이다. LPDDR5는 per-bank refresh + PASR로 미사용 array 영역의 refresh를 생략한다. DDR5는 same-bank refresh(REFsb), DDR4는 all-bank refresh.

**See also.** [Module 02](../02_memory_controller/)

### PASR (Partial Array Self-Refresh)

**Definition.** Self-refresh 시 실제로 사용 중인 array 영역만 refresh하고 미사용 영역은 생략하여 전력을 절감하는 LPDDR 고유 기능이다.

**Source.** JEDEC JESD209-5 (LPDDR5).

**Related.** REF, tREFI, Deep Sleep.

**Example.** DDR5에는 없는 LPDDR 고유 기능으로, 모바일 idle 상태에서 retention 전력을 크게 줄인다.

**See also.** [Module 01](../01_dram_fundamentals_ddr/)

### Prefetch (16n)

**Definition.** 한 번의 column access로 DRAM 내부에서 DQ당 n비트를 한꺼번에 읽어 외부 고속 클럭으로 직렬 전송하는 구조이다.

**Source.** JEDEC.

**Related.** Burst Length, WCK, DQ.

**Example.** LPDDR5·LPDDR4·DDR5는 16n(BL16), DDR4는 8n(BL8)이다. LPDDR은 LPDDR4부터 16n을 채택했고, LPDDR5는 BL16과 BL32를 지원한다.

**See also.** [Module 01](../01_dram_fundamentals_ddr/)

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

## W — WCK / WCK2CK / CBT / DVFSC

### WCK (Write Clock)

**Definition.** LPDDR5에서 명령 클럭(CK)과 분리되어 DQ 데이터 전송만 고속으로 동기화하는 데이터 전용 클럭이다.

**Source.** JEDEC JESD209-5 (LPDDR5).

**Related.** CK, DQ, WCK2CK, DVFSC.

**Example.** WCK:CK 비율은 gear에 따라 2:1 또는 4:1이며, 명령 버스는 저속 CK로 두고 데이터만 고속으로 돌려 전력을 절감한다. DDR5는 단일 CK + DQS 구조로 WCK가 없다.

**See also.** [Module 01](../01_dram_fundamentals_ddr/)

### WCK2CK (WCK-to-CK Leveling)

**Definition.** LPDDR5에서 WCK와 CK 사이의 위상을 정렬하는 training 단계로, DDR5에는 없는 항목이다.

**Source.** JEDEC JESD209-5 (LPDDR5).

**Related.** WCK, CK, Training, DVFSC.

**Example.** DVFSC로 gear가 전환되어 WCK:CK 비율이 바뀌면 WCK2CK 재정렬이 필요하다.

**See also.** [Module 01](../01_dram_fundamentals_ddr/)

### CBT (Command Bus Training)

**Definition.** LPDDR5에서 단일종단·다중사이클로 동작하는 CA[6:0] 명령/주소 버스의 핀 타이밍을 정렬하는 training 단계이다.

**Source.** JEDEC JESD209-5 (LPDDR5).

**Related.** CA, Training, WCK2CK, VREF.

**Example.** LPDDR5의 CA 버스는 단일종단 다중사이클이라 CBT(Mode1/2)가 필수이며, 내부 VREF를 사용한다. DDR5는 CA[13:0] 2-cycle 기반의 CA(CS) training을 쓴다.

**See also.** [Module 01](../01_dram_fundamentals_ddr/)

### DVFSC (Dynamic Voltage and Frequency Scaling — Clock)

**Definition.** LPDDR5에서 부하에 따라 런타임에 동작 주파수와 전압 gear(F0~F4 등)를 전환해 전력을 조절하는 기능이다.

**Source.** JEDEC JESD209-5 (LPDDR5).

**Related.** WCK, WCK2CK, gear.

**Example.** gear 전환 시 WCK:CK 비율이 바뀌므로 WCK2CK 재정렬 또는 저장된 training 값 복원이 필요하다.

**See also.** [Module 01](../01_dram_fundamentals_ddr/)

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
| **WCK2CK** | WCK-to-CK Leveling | LPDDR5 WCK·CK 위상 정렬 (DDR5에 없음) |
| **CBT** | Command Bus Training | LPDDR5 CA 버스 타이밍 정렬 |
| **DVFSC** | Dynamic Voltage/Freq Scaling Clock | LPDDR5 런타임 gear(F0~F4) 전환 |
| **PASR** | Partial Array Self-Refresh | 미사용 array만 refresh 생략 (LPDDR 고유) |
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
