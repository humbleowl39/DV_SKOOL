# Hardware Interview 용어집

이 페이지는 본 코스에서 사용되는 핵심 용어 정의 모음입니다. 항목은 ISO 11179 형식을 따릅니다 (**Definition / Source / Related / Example / See also**).

!!! tip "검색 활용"
    상단 검색창에 용어를 입력하면 본문에서의 사용처도 함께 찾을 수 있습니다.

---

## A — AHB / AOCV / AXI / Antenna Effect

### AHB

**Definition.** ARM AMBA 의 single-master, fixed-pipeline 버스 프로토콜로, hready/hresp 신호로 transfer 완료를 표시한다.

**Source.** ARM AMBA Specification, AHB 2.0 / AHB 5.

**Related.** AMBA, AXI, APB, Bus.

**Example.** SoC 의 펌웨어 / 디버그 영역 인터커넥트.

**See also.** [Unit 1 — Protocols](01_digital_rtl.md#5-protocols--interfaces--1줄-요약)

### AOCV (Advanced On-Chip Variation)

**Definition.** Static Timing Analysis 에서 path depth 와 location 에 따라 derating 계수가 달라지는 보정 방식.

**Source.** Synopsys / Cadence STA tool documentation.

**Related.** OCV, POCV, Derating, Signoff STA.

**Example.** 5-stage path 는 10% derate, 20-stage path 는 5% derate.

**See also.** [Unit 6 — STA Signoff](06_physical_design.md#5-sta-signoff--derating--ocv)

### Antenna Effect

**Definition.** Plasma 식각 공정 중 긴 metal segment 가 모은 전하로 gate oxide 가 파괴되는 신뢰성 문제.

**Source.** Foundry Design Rule Manual.

**Related.** Reliability, DRC, Diode insertion.

**Example.** Long metal3 routing 이 *antenna ratio limit* 초과 → diode 추가 또는 metal 분할.

**See also.** [Unit 6 — Reliability](06_physical_design.md#6-reliability--ir-drop--em--antenna)

### AXI (Advanced eXtensible Interface)

**Definition.** ARM AMBA 5 의 5-channel(AR/R/AW/W/B), ID 기반 OOO, burst 지원 고성능 버스 프로토콜.

**Source.** ARM AMBA 5 AXI Specification.

**Related.** AHB, APB, valid-ready handshake, Burst.

**Example.** 메모리 컨트롤러 ↔ CPU NoC 인터페이스.

**See also.** [DV SKOOL — AMBA Protocols](https://humbleowl39.github.io/DV_SKOOL/amba_protocols/)

---

## B — Bandgap Reference / Blocking / BTB

### Bandgap Reference

**Definition.** Vbe (CTAT) 와 ΔVbe 기반 PTAT 의 가중합으로 온도 1차 의존성을 상쇄해 ~1.2V 의 안정된 전압을 생성하는 회로.

**Source.** Razavi, *Design of Analog CMOS Integrated Circuits*, Ch. 11.

**Related.** PTAT, CTAT, Brokaw topology.

**Example.** ADC reference, LDO reference, PLL VCO bias.

**See also.** [Unit 5 — Bandgap Reference](05_analog_mixed_signal.md#4-bandgap-reference)

### Blocking Assignment

**Definition.** Verilog 의 `=` 대입으로, 순차적으로 평가/대입되어 조합 회로 합성에 사용되는 대입 방식.

**Source.** IEEE 1800-2017 SystemVerilog Standard, §10.4.

**Related.** Non-blocking, always_comb, always_ff.

**Example.** `always_comb begin a = b + c; d = a * 2; end`

**See also.** [Unit 1 — Blocking vs Non-Blocking](01_digital_rtl.md#12-blocking-vs-non-blocking--가장-빈출-질문)

### BTB (Branch Target Buffer)

**Definition.** Branch instruction 의 PC 를 key 로 *예측 target address* 와 taken/not-taken 을 저장하는 cache.

**Source.** Hennessy & Patterson, *Computer Architecture: A Quantitative Approach*.

**Related.** Branch Prediction, gshare, RAS.

**Example.** IF stage 에서 BTB hit 시 다음 fetch address 즉시 결정.

**See also.** [Unit 4 — Branch Prediction](04_computer_architecture.md#4-branch-prediction)

---

## C — Cache Coherency / CCM / CDC / Clock Gating / CMRR / Constraint

### Cache Coherency

**Definition.** Multi-core 시스템에서 *같은 메모리 주소* 의 캐시 사본이 일관된 값을 유지하도록 보장하는 프로토콜.

**Source.** Hennessy & Patterson, *Computer Architecture: A Quantitative Approach*.

**Related.** MESI, MOESI, Snooping, Directory.

**Example.** 코어 A 가 line X 를 write → 다른 코어의 X 사본을 *Invalidate*.

**See also.** [Unit 3 — Cache & Coherency](03_embedded_firmware.md#6-cache--coherency--펌웨어-관점)

### CCM (Continuous Conduction Mode)

**Definition.** 스위칭 컨버터에서 inductor 전류가 한 스위칭 주기 동안 0 아래로 떨어지지 않는 동작 모드.

**Source.** Erickson, *Fundamentals of Power Electronics*.

**Related.** DCM, BCM, Buck converter.

**Example.** Heavy load 의 Buck/Boost 컨버터 정상 동작 모드.

**See also.** [Unit 5 — Power Converter](05_analog_mixed_signal.md#52-ccm--dcm--bcm)

### CDC (Clock Domain Crossing)

**Definition.** 서로 다른 비동기 클럭 도메인 사이를 신호가 횡단하는 RTL 구조.

**Source.** Cummings, *Clock Domain Crossing (CDC) Design & Verification Techniques* (SNUG 2008).

**Related.** Metastability, 2-FF Synchronizer, Async FIFO, Gray code.

**Example.** 10MHz 도메인의 1-bit done 신호를 100MHz 도메인이 받음.

**See also.** [Unit 1 — CDC](01_digital_rtl.md#4-clock-domain-crossing-cdc)

### Clock Gating

**Definition.** Latch 와 AND gate 로 구성된 ICG cell 로 *enable=0* 인 동안 flop 그룹의 클럭 공급을 차단해 dynamic power 를 줄이는 기법.

**Source.** Industry-standard low-power design practice.

**Related.** ICG cell, Leaf-level gating, Dynamic power.

**Example.** `if (en) reg <= data;` RTL 패턴이 합성에서 자동으로 ICG 로 변환.

**See also.** [Unit 6 — Low Power](06_physical_design.md#43-clock-gating--가장-효과적)

### CMRR (Common-Mode Rejection Ratio)

**Definition.** Op-amp 가 differential 신호 대비 common-mode 신호를 얼마나 잘 거부하는지를 나타내는 비율 (dB).

**Source.** Sedra & Smith, *Microelectronic Circuits*.

**Related.** Differential pair, Op-amp non-idealities.

**Example.** 80 dB CMRR 의 op-amp 는 common-mode 1V 가 출력에 0.1 mV 정도 누설.

**See also.** [Unit 5 — Op-Amp Non-Ideal](05_analog_mixed_signal.md#22-non-ideal--real-world-한계)

### Constraint (SystemVerilog)

**Definition.** SystemVerilog class 의 `rand` 변수에 대해 무작위 값 생성 시 만족해야 할 조건을 선언하는 코드 블록.

**Source.** IEEE 1800-2017, §18.

**Related.** randomize(), solve before, dist.

**Example.** `constraint c_addr { addr inside {[0:'h1000]}; addr[1:0] == 0; }`

**See also.** [Unit 2 — Constraint Randomization](02_design_verification.md#3-constraint-randomization)

---

## D — Dead-time / Derating / Dropout Voltage / DVFS

### Dead-time

**Definition.** Half-bridge 컨버터에서 high-side 와 low-side switch 가 동시에 켜져 short 가 발생하지 않도록 *둘 다 off* 상태를 강제하는 짧은 시간 구간.

**Source.** Power electronics common practice.

**Related.** Shoot-through, Body diode, Switching loss.

**Example.** GaN HEMT 의 dead-time 은 보통 ns 단위, Si MOSFET 은 수십 ns.

**See also.** [Unit 5 — Power Converter](05_analog_mixed_signal.md#55-dead-time)

### Derating

**Definition.** Static Timing Analysis 에서 process / voltage / temperature variation 을 반영해 cell delay 를 보수적으로 (느리게 또는 빠르게) 보정하는 계수.

**Source.** STA tool documentation.

**Related.** OCV, AOCV, POCV.

**Example.** `set_timing_derate -early 0.95 -late 1.05`.

**See also.** [Unit 6 — STA Signoff](06_physical_design.md#5-sta-signoff--derating--ocv)

### Dropout Voltage

**Definition.** LDO 가 정상 regulation 을 유지할 수 있는 최소 Vin − Vout 차이.

**Source.** LDO datasheet.

**Related.** LDO, PMOS pass, PSRR.

**Example.** PMOS LDO 의 dropout 은 100 mV, NMOS LDO 는 보통 300 mV 이상.

**See also.** [Unit 5 — LDO Design](05_analog_mixed_signal.md#6-ldo-design)

### DVFS (Dynamic Voltage Frequency Scaling)

**Definition.** 워크로드에 따라 VDD 와 클럭 주파수를 런타임에 조정해 dynamic power 를 줄이는 기법.

**Source.** Industry-standard low-power technique.

**Related.** Multi-VDD, Clock Gating, Power Domains.

**Example.** Mobile SoC 가 light load 시 VDD 0.7V / 500MHz, heavy 시 1.0V / 2GHz.

**See also.** [Unit 6 — Low Power](06_physical_design.md#4-low-power-기법)

---

## E — Electromigration

### Electromigration (EM)

**Definition.** 도선의 높은 전류 밀도가 metal atom 을 점진적으로 이동시켜 시간이 지나면 open 또는 short 를 유발하는 신뢰성 문제.

**Source.** Black's equation, foundry reliability rules.

**Related.** Current density limit, Via array, Reliability.

**Example.** Power rail 의 EM violation → metal 폭 증가 또는 layer 분산.

**See also.** [Unit 6 — Reliability](06_physical_design.md#62-electromigration-em)

---

## F — Factory / FIFO / FSM / Forwarding

### Factory (UVM)

**Definition.** UVM 의 객체 생성을 *type 또는 instance override* 가능한 형태로 통합 관리하는 메커니즘.

**Source.** UVM 1.2 Reference Manual, §8.

**Related.** uvm_object_utils, set_type_override, create().

**Example.** `set_type_override_by_type(base_seq::get_type(), err_seq::get_type())` 한 줄로 모든 base_seq 가 err_seq 로 생성.

**See also.** [Unit 2 — Factory + Override](02_design_verification.md#13-factory--override--왜-중요)

### FIFO (First-In First-Out)

**Definition.** 입력 순서가 출력 순서와 동일하게 유지되는 큐 구조의 메모리 또는 자료구조.

**Source.** Common digital design pattern.

**Related.** Circular buffer, Async FIFO, Gray code pointer.

**Example.** Async FIFO 가 두 클럭 도메인 사이 데이터를 안전하게 전달.

**See also.** [Unit 1 — CDC](01_digital_rtl.md#4-clock-domain-crossing-cdc), [Unit 3 — Circular Buffer](03_embedded_firmware.md#32-circular-buffer)

### FSM (Finite State Machine)

**Definition.** 입력에 따라 정해진 유한한 상태 집합을 천이하며 출력을 생성하는 순차 회로.

**Source.** Harris & Harris, *Digital Design and Computer Architecture*.

**Related.** Mealy, Moore, State encoding.

**Example.** AHB master 의 IDLE → BUSY → NONSEQ → SEQ 천이.

**See also.** [Unit 1 — FSM](01_digital_rtl.md#2-상태기계-fsm--mealy-vs-moore)

### Forwarding (Bypassing)

**Definition.** Pipeline 에서 이전 명령의 EX 결과를 *다음 사이클의 EX 입력* 으로 직접 연결해 RAW data hazard 를 stall 없이 해결하는 기법.

**Source.** Hennessy & Patterson, *Computer Architecture*.

**Related.** Data Hazard, Pipeline Stall, Load-use Hazard.

**Example.** `ADD r1,r2,r3; SUB r4,r1,r5` 에서 EX→EX forward 로 stall 0.

**See also.** [Unit 4 — Hazard](04_computer_architecture.md#32-hazard-3종)

---

## G — Gate-Bandwidth Product / Gray Code / Gshare

### GBW (Gain-Bandwidth Product)

**Definition.** Op-amp 의 *open-loop gain × 그에 해당하는 frequency* 가 상수임을 나타내는 small-signal 한계.

**Source.** Sedra & Smith, *Microelectronic Circuits*.

**Related.** Slew rate, Phase margin, Miller compensation.

**Example.** GBW = 10MHz 의 op-amp 를 gain=100 으로 쓰면 BW = 100 kHz.

**See also.** [Unit 5 — Op-Amp Non-Ideal](05_analog_mixed_signal.md#22-non-ideal--real-world-한계)

### Gray Code

**Definition.** 인접한 정수 두 값이 정확히 1 비트만 다른 binary 인코딩 방식.

**Source.** Frank Gray, *Pulse Code Communication*, 1953.

**Related.** Async FIFO, CDC, State encoding.

**Example.** 3-bit Gray: 000, 001, 011, 010, 110, 111, 101, 100.

**See also.** [Unit 1 — CDC](01_digital_rtl.md#43-multi-bit-bus--두-가지-정석)

### Gshare

**Definition.** Global branch history 를 PC 와 XOR 하여 prediction counter table 의 index 로 사용하는 dynamic branch predictor.

**Source.** McFarling, *Combining Branch Predictors*, DEC WRL TN-36, 1993.

**Related.** Bimodal, TAGE, BTB.

**Example.** 8-bit global history × 256-entry table = 95% 수준 정확도.

**See also.** [Unit 4 — Branch Prediction](04_computer_architecture.md#41-종류--진화-순서)

---

## I — I2C / Inclusive Cache / IR Drop

### I2C

**Definition.** SDA + SCL 두 개의 open-drain 선으로 multi-master / multi-slave 통신을 제공하는 직렬 프로토콜.

**Source.** Philips/NXP I2C-bus Specification (UM10204).

**Related.** SDA, SCL, START/STOP, Clock stretching.

**Example.** 온도 센서 ↔ MCU 의 100kbps 통신.

**See also.** [Unit 3 — I2C 디테일](03_embedded_firmware.md#21-i2c--가장-자주-묻는-디테일)

### Inclusive Cache

**Definition.** 상위 레벨 캐시 (L1) 의 모든 라인이 하위 레벨 캐시 (L2) 에도 반드시 존재함을 보장하는 캐시 구조.

**Source.** Hennessy & Patterson, *Computer Architecture*.

**Related.** Exclusive cache, NINE, Snoop filter.

**Example.** Intel x86 의 L2-L3 inclusive 정책 → snoop 효율 ↑.

**See also.** [Unit 4 — Inclusive vs Exclusive](04_computer_architecture.md#16-inclusive-vs-exclusive-vs-nine)

### IR Drop

**Definition.** 전원 grid 의 resistance R 과 흐르는 current I 의 곱으로 발생하는 지역적 VDD 강하 현상.

**Source.** Power integrity analysis literature.

**Related.** PG mesh, Decoupling cap, Dynamic IR.

**Example.** 칩 중앙 hotspot 에서 nominal VDD 1.0V 가 0.92V 로 강하 → 8% IR drop.

**See also.** [Unit 6 — Reliability](06_physical_design.md#61-ir-drop)

---

## L — Latch-up / LDO / LRU

### Latch-up

**Definition.** CMOS 의 p-substrate + n-well + p+ source 가 형성하는 parasitic SCR 이 trigger 되어 high current 가 흘러 칩이 소손되는 현상.

**Source.** CMOS reliability literature.

**Related.** Guard ring, Substrate contact, ESD.

**Example.** I/O 핀 over-voltage 가 latch-up 을 trigger → 칩 영구 손상.

**See also.** [Unit 5 — Latch-Up](05_analog_mixed_signal.md#34-latch-up)

### LDO (Low Dropout Regulator)

**Definition.** Pass transistor 와 error amp 의 closed-loop 으로 작은 Vin−Vout 차이에서 안정된 출력을 제공하는 linear regulator.

**Source.** Texas Instruments / Analog Devices LDO application notes.

**Related.** PMOS pass, PSRR, Dropout voltage.

**Example.** Buck 컨버터 출력 1.0V 를 LDO 로 다시 0.9V analog supply 로 변환.

**See also.** [Unit 5 — LDO Design](05_analog_mixed_signal.md#6-ldo-design)

### LRU (Least Recently Used)

**Definition.** 캐시에서 가장 오랫동안 접근되지 않은 라인을 eviction 후보로 선택하는 replacement policy.

**Source.** Computer architecture textbooks.

**Related.** Pseudo-LRU, FIFO, Replacement policy.

**Example.** 4-way set associative cache 에서 access order 추적 후 eviction.

**See also.** [Unit 4 — Replacement Policy](04_computer_architecture.md#14-replacement-policy)

---

## M — Mealy / Metastability / MESI / Miller Compensation / Mutex

### Mealy Machine

**Definition.** 출력이 현재 상태와 입력의 함수인 FSM 모델로, 입력 변화에 즉시 반응한다.

**Source.** G. H. Mealy, *A Method for Synthesizing Sequential Circuits*, 1955.

**Related.** Moore, FSM, Output flop.

**Example.** 자동판매기에서 동전 투입 즉시 음료 응답.

**See also.** [Unit 1 — FSM](01_digital_rtl.md#2-상태기계-fsm--mealy-vs-moore)

### Metastability

**Definition.** Flip-flop 의 setup 또는 hold 위반 시 출력이 정해지지 않은 중간 전압에서 진동하는 비안정 상태.

**Source.** CDC literature.

**Related.** CDC, 2-FF Synchronizer, MTBF.

**Example.** 비동기 신호를 직접 flop 에 입력 시 setup/hold 위반 가능성 → 다음 stage 가 0/1 다르게 인식.

**See also.** [Unit 1 — CDC](01_digital_rtl.md#41-metastability-의-본질)

### MESI

**Definition.** Cache line 을 Modified / Exclusive / Shared / Invalid 4 상태로 관리하는 cache coherence 프로토콜.

**Source.** Papamarcos & Patel, ISCA 1984.

**Related.** Cache Coherency, Snoop, MOESI.

**Example.** 코어 A 가 S → M 으로 transition 시 다른 코어 사본을 I 로 invalidate.

**See also.** [Unit 3 — Cache & Coherency](03_embedded_firmware.md#63-mesi-의-직관)

### Miller Compensation

**Definition.** 2단 op-amp 의 두 stage 사이에 compensation cap (Cc) 을 삽입해 Miller effect 로 dominant pole 을 낮추어 phase margin 을 확보하는 기법.

**Source.** Razavi, *Design of Analog CMOS Integrated Circuits*, Ch. 10.

**Related.** Pole splitting, Phase margin, GBW.

**Example.** Cc = 1 pF 삽입으로 dominant pole 이 kHz 영역으로 이동 → 60° PM.

**See also.** [Unit 5 — Miller](05_analog_mixed_signal.md#23-miller-compensation)

### Mutex

**Definition.** 한 시점에 한 thread/task 만 critical section 에 진입하도록 강제하는 binary 동기화 primitive 로, lock 한 자만 unlock 할 수 있는 소유권 개념을 가진다.

**Source.** Operating systems textbooks.

**Related.** Semaphore, Atomic, Priority Inversion.

**Example.** Shared `g_counter` 를 두 task 가 갱신할 때 mutex 로 보호.

**See also.** [Unit 3 — Concurrency](03_embedded_firmware.md#42-mutex-vs-semaphore)

---

## N — Non-Blocking / NMOS body effect

### Non-Blocking Assignment

**Definition.** SystemVerilog 의 `<=` 대입으로, 우변을 같은 시간 슬롯에서 모두 평가한 후 다음 슬롯에서 좌변에 동시 대입되어 순차 회로 합성에 사용되는 대입 방식.

**Source.** IEEE 1800-2017, §10.4.

**Related.** Blocking, always_ff, Shift register.

**Example.** `always_ff @(posedge clk) begin q1 <= d; q2 <= q1; end` — 정상 shift.

**See also.** [Unit 1 — Blocking vs Non-Blocking](01_digital_rtl.md#12-blocking-vs-non-blocking--가장-빈출-질문)

---

## O — OCV / Op-Amp / Out-of-Order

### OCV (On-Chip Variation)

**Definition.** 같은 칩 내 transistor 의 process variation 으로 인한 cell delay 의 분산을 STA 에서 모델링하기 위한 derating 개념.

**Source.** STA / EDA tool documentation.

**Related.** AOCV, POCV, Derating.

**Example.** Launch path 1.05× 늦게, capture path 0.95× 빠르게 가정.

**See also.** [Unit 6 — STA Signoff](06_physical_design.md#52-ocv-on-chip-variation)

### Op-Amp (Operational Amplifier)

**Definition.** 매우 큰 open-loop gain 의 differential input / single-ended output 증폭기로, 음의 피드백 시 V+ = V− 의 가상 단락 특성을 가진다.

**Source.** Sedra & Smith, *Microelectronic Circuits*.

**Related.** GBW, Slew rate, Miller compensation.

**Example.** Inverting amp 의 Vo/Vi = −Rf/Rin.

**See also.** [Unit 5 — Op-Amp](05_analog_mixed_signal.md#2-op-amp--ideal-configurations)

### Out-of-Order (OoO)

**Definition.** 명령을 program order 와 다른 순서로 실행하되 ROB 의 in-order commit 으로 가시적 순서를 유지하는 microarchitecture 기법.

**Source.** Hennessy & Patterson, *Computer Architecture*.

**Related.** Tomasulo, Register renaming, ROB.

**Example.** 큰 cache miss 동안 후속 독립 명령을 먼저 실행.

**See also.** [Unit 4 — Tomasulo](04_computer_architecture.md#33-out-of-order-execution--tomasulo)

---

## P — Phase Margin / PIPT / POCV / PSRR / Power Gating / PTAT

### Phase Margin

**Definition.** Open-loop transfer 의 gain crossover 주파수에서 phase 가 −180° 까지 남은 여유 (degree).

**Source.** Control theory / op-amp design textbooks.

**Related.** GBW, Miller compensation, Stability.

**Example.** PM = 60° 이면 안정적, 30° 미만이면 ringing.

**See also.** [Unit 5 — Op-Amp](05_analog_mixed_signal.md#22-non-ideal--real-world-한계)

### PIPT (Physically Indexed Physically Tagged)

**Definition.** 캐시의 index 와 tag 모두에 physical address 를 사용하는 캐시 구조로, alias 가 없지만 TLB 접근이 hit 경로에 포함된다.

**Source.** Hennessy & Patterson, *Computer Architecture*.

**Related.** VIPT, VIVT, TLB.

**Example.** 현대 L2 / L3 캐시는 거의 PIPT.

**See also.** [Unit 4 — VIPT vs PIPT](04_computer_architecture.md#53-vipt-vs-pipt-vs-vivt)

### POCV (Parametric On-Chip Variation)

**Definition.** Cell delay 의 mean ± sigma 통계 모델을 사용해 path delay 의 통계적 합산으로 derating 을 계산하는 STA 기법.

**Source.** Synopsys / Cadence STA tool documentation (post-2015).

**Related.** OCV, AOCV, Statistical STA.

**Example.** 10-stage path 의 sigma 합산이 √10 배 → 보수적 AOCV 대비 덜 비관적.

**See also.** [Unit 6 — STA Signoff](06_physical_design.md#53-aocv--pocv)

### PSRR (Power Supply Rejection Ratio)

**Definition.** Voltage regulator 또는 op-amp 가 VDD 변동(ripple) 을 출력으로 얼마나 적게 전달하는지를 나타내는 비율 (dB).

**Source.** LDO / op-amp application notes.

**Related.** LDO, Cascode, Bandgap.

**Example.** 80 dB PSRR LDO 는 VDD 100 mV ripple 을 출력에서 10 μV 로 감쇄.

**See also.** [Unit 5 — LDO](05_analog_mixed_signal.md#63-psrr-power-supply-rejection-ratio)

### Power Gating

**Definition.** 사용하지 않는 회로 블록의 VDD 또는 VSS rail 을 sleep transistor 로 차단해 leakage power 를 제거하는 저전력 기법.

**Source.** UPF/CPF low-power design specifications.

**Related.** Multi-VDD, Retention flop, Isolation cell.

**Example.** Mobile SoC 의 GPU 블록을 idle 시 power gate → leakage 0.

**See also.** [Unit 6 — Low Power](06_physical_design.md#42-static-leakage-power)

### PTAT (Proportional to Absolute Temperature)

**Definition.** 두 BJT 의 ΔVbe (서로 다른 전류 밀도) 가 절대 온도에 비례한다는 성질을 이용해 만든 정전류 또는 전압 신호.

**Source.** Razavi, *Design of Analog CMOS Integrated Circuits*.

**Related.** CTAT, Bandgap reference.

**Example.** Bandgap reference 의 양의 온도 계수 성분으로 사용.

**See also.** [Unit 5 — Bandgap Reference](05_analog_mixed_signal.md#41-ptat--ctat-결합)

---

## R — RAS / Register Renaming / Reservation Station / RTOS

### RAS (Return Address Stack)

**Definition.** Function call/return 의 return address 를 stack 으로 push/pop 하여 ret instruction 의 target 을 정확히 예측하는 분기 예측 보조 구조.

**Source.** Hennessy & Patterson, *Computer Architecture*.

**Related.** Branch prediction, BTB, Call/ret.

**Example.** 8~16 entry RAS 로 nested function call 의 99%+ 예측.

**See also.** [Unit 4 — Branch Prediction](04_computer_architecture.md#43-ras-return-address-stack)

### Register Renaming

**Definition.** Architectural register 이름을 별도의 physical register 로 매핑해 WAR / WAW false dependency 를 제거하고 OoO 실행을 가능하게 하는 기법.

**Source.** Tomasulo, IBM Journal of R&D, 1967.

**Related.** Tomasulo, ROB, Out-of-Order.

**Example.** `r1 = ... ; r1 = ...` 두 번째 r1 을 p47 같은 새 physical reg 로 매핑.

**See also.** [Unit 4 — Tomasulo](04_computer_architecture.md#33-out-of-order-execution--tomasulo)

### Reservation Station

**Definition.** OoO 코어에서 dispatch 된 명령이 operand 가 준비될 때까지 대기하다 Functional Unit 으로 issue 되는 대기 버퍼.

**Source.** Tomasulo's algorithm.

**Related.** CDB, Tomasulo, Dynamic scheduling.

**Example.** RS slot 이 operand-ready 되면 그 사이클에 ALU 로 issue.

**See also.** [Unit 4 — Tomasulo](04_computer_architecture.md#33-out-of-order-execution--tomasulo)

### RTOS (Real-Time Operating System)

**Definition.** Task scheduling, priority preemption, deterministic latency 를 제공하는 임베디드 운영체제.

**Source.** FreeRTOS / Zephyr / VxWorks documentation.

**Related.** Task, Mutex, Priority inversion.

**Example.** 1ms 주기 sensor task + UART command task 의 동시 실행.

**See also.** [Unit 3 — RTOS](03_embedded_firmware.md#12-rtos-vs-bare-metal)

---

## S — SDC / Setup/Hold / Skew / Slew Rate / SVA / Synchronizer

### SDC (Synopsys Design Constraints)

**Definition.** 클럭 정의, IO timing, false path, multi-cycle path 등 STA 와 합성에 필요한 제약을 기술하는 표준 TCL 기반 포맷.

**Source.** Synopsys SDC specification, IEEE 1801 (subset).

**Related.** STA, Synthesis, Multi-cycle path.

**Example.** `create_clock -period 5.0 -name clk [get_ports clk]`.

**See also.** [Unit 6 — Synthesis](06_physical_design.md#71-synthesis-checks)

### Setup / Hold Time

**Definition.** Flip-flop 의 D 입력이 clock edge 기준 일정 시간 *이전* 부터 안정해야 하는 시간 (setup) 과 *이후* 까지 안정해야 하는 시간 (hold).

**Source.** Digital design textbooks / standard cell library docs.

**Related.** STA, Metastability, Skew.

**Example.** tsu = 0.1 ns, th = 0.05 ns 인 flop.

**See also.** [Unit 1 — STA](01_digital_rtl.md#3-static-timing-analysis-sta)

### Skew

**Definition.** 두 flop 사이에서 launch clock 과 capture clock 의 insertion delay 차이.

**Source.** STA literature.

**Related.** Insertion delay, Useful skew, CTS.

**Example.** Skew = 100 ps → setup margin 100 ps 추가 또는 hold margin 100 ps 손실.

**See also.** [Unit 1 — STA](01_digital_rtl.md#32-clock-insertion--skew--uncertainty)

### Slew Rate

**Definition.** Op-amp 또는 driver 의 출력 전압이 큰 신호 step 에 대해 변화할 수 있는 최대 속도 (V/μs).

**Source.** Sedra & Smith, *Microelectronic Circuits*.

**Related.** GBW, Large-signal, Op-amp.

**Example.** SR = 10 V/μs op-amp 는 10V step 에 1μs 소요.

**See also.** [Unit 5 — Op-Amp](05_analog_mixed_signal.md#24-slew-rate-vs-bandwidth--차이)

### SVA (SystemVerilog Assertion)

**Definition.** Sequence 와 property 를 정의해 RTL 의 시간적 동작이 의도된 사양을 만족하는지 시뮬레이션 또는 formal 에서 검사하는 SystemVerilog 언어 기능.

**Source.** IEEE 1800-2017, §16.

**Related.** assert property, cover property, Concurrent assertion.

**Example.** `assert property (@(posedge clk) $rose(valid) |-> valid throughout (ready[->1]));`

**See also.** [Unit 2 — SVA](02_design_verification.md#4-systemverilog-assertion-sva)

### Synchronizer (2-FF)

**Definition.** 비동기 1-bit 신호를 destination 클럭에 안전하게 전달하기 위해 2단 이상의 flip-flop chain 을 사용하는 회로.

**Source.** Cummings, CDC SNUG 2008.

**Related.** Metastability, CDC, MTBF.

**Example.** `{sync_q1, sync_q2} <= {async, sync_q1}` — q2 가 사용.

**See also.** [Unit 1 — 2-FF Synchronizer](01_digital_rtl.md#42-1-bit-신호--2-ff-synchronizer)

---

## T — TLB / Tomasulo

### TLB (Translation Lookaside Buffer)

**Definition.** Virtual-to-physical address 매핑을 캐시하는 fully-associative 또는 set-associative buffer.

**Source.** Hennessy & Patterson, *Computer Architecture*.

**Related.** Page table, Virtual Memory, ASID.

**Example.** 64-entry L1 TLB + 1024-entry L2 TLB 구조가 현대 ARM Cortex 흔함.

**See also.** [Unit 4 — Virtual Memory](04_computer_architecture.md#5-virtual-memory--os), [DV SKOOL — MMU](https://humbleowl39.github.io/DV_SKOOL/mmu/)

### Tomasulo

**Definition.** 1967 년 IBM 에서 제안된 OoO 실행 알고리즘으로 reservation station, common data bus, register renaming 을 통해 dynamic scheduling 을 구현한다.

**Source.** Tomasulo, IBM Journal of R&D, 1967.

**Related.** OoO, RS, CDB, Register renaming, ROB.

**Example.** 현대 ARM/x86 CPU 의 OoO core 가 Tomasulo 의 발전된 형태.

**See also.** [Unit 4 — Tomasulo](04_computer_architecture.md#33-out-of-order-execution--tomasulo)

---

## V — Valid-Ready Handshake / VIPT / Volatile

### Valid-Ready Handshake

**Definition.** Sender 의 valid 와 receiver 의 ready 가 같은 클럭에서 모두 1 일 때 transfer 가 일어나며, valid 는 raise 후 transfer 까지 lower 되어선 안 되고 ready 는 자유롭게 변할 수 있는 핸드셰이크 규약.

**Source.** ARM AMBA AXI Specification.

**Related.** AXI, Backpressure, Deadlock.

**Example.** AXI AR / R / AW / W / B 모든 채널의 핸드셰이크.

**See also.** [Unit 1 — Valid-Ready](01_digital_rtl.md#51-valid-ready-핸드셰이크--axiamba-의-핵심)

### VIPT (Virtually Indexed Physically Tagged)

**Definition.** Cache 의 index 는 virtual address 비트로, tag 는 TLB 변환 후 physical address 로 비교하는 캐시 구조.

**Source.** Hennessy & Patterson, *Computer Architecture*.

**Related.** VIVT, PIPT, Alias.

**Example.** Index 비트가 page offset 내에 있으면 alias-free → cache size ≤ way × page_size.

**See also.** [Unit 4 — VIPT vs PIPT](04_computer_architecture.md#53-vipt-vs-pipt-vs-vivt)

### Volatile

**Definition.** C/C++ 에서 컴파일러가 해당 변수에 대해 캐싱이나 register 보관 같은 최적화를 하지 못하도록 강제하는 type qualifier.

**Source.** ISO C11, §6.7.3.

**Related.** Memory-mapped I/O, ISR, Atomic.

**Example.** `#define UART_STATUS (*(volatile uint32_t *)0x4000_0008)`.

**See also.** [Unit 3 — volatile](03_embedded_firmware.md#51-volatile--컴파일러에게-최적화-금지)

---

## Z — Zero-Skew Clock

### Zero-Skew Clock

**Definition.** CTS 의 ideal 목표로, 모든 flop 의 clock pin 도착 시간이 동일한 상태.

**Source.** CTS literature.

**Related.** Useful skew, H-tree, Clock mesh.

**Example.** Multi-source CTS 가 0 skew 에 근접한 분배 제공.

**See also.** [Unit 6 — CTS](06_physical_design.md#3-clock-tree-synthesis-cts)
