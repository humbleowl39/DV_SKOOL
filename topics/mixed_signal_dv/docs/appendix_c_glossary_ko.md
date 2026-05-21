# 부록 C. 용어집 (KO, ISO 11179)

> 용어 정의는 ISO 11179 형식 — "그것이 무엇인가"를 단일 문장으로 기술하고, 예시·출처·관련 항목을 별도 필드로 분리.
>
> English mirror: [appendix_c_glossary.md](appendix_c_glossary.md)

## AMS (Analog Mixed-Signal Simulation)

**정의.** 디지털 이벤트 기반 시뮬레이션 엔진과 아날로그 연속시간 시뮬레이션 엔진을 동시에 구동하여 디지털·아날로그 회로를 동기화된 connect module을 통해 함께 검증하는 시뮬레이션 방식.

**출처.** Verilog-AMS LRM (IEEE 1364.1 / Accellera VAMS-2023).

**관련.** [[SPICE]], [[RNM]], [[Connect module]].

**예시.** Cadence AMS Designer는 Xcelium(디지털)과 Spectre(아날로그)를 결합하여 ADC 검증에 사용.

## A2D (Analog-to-Digital Connect Module)

**정의.** 연속시간 아날로그 신호의 threshold crossing을 감지하여 이산 디지털 logic 신호로 변환하는 connect module.

**출처.** Verilog-AMS LRM § Connect Module Rules.

**관련.** [[D2A]], [[Connect module]], [[Discipline]].

**예시.** `@(cross(V(in) - vth, +1)) out = 1'b1;` — rising-edge threshold detector.

## BSIM (Berkeley Short-channel IGFET Model)

**정의.** UC Berkeley에서 개발된 MOSFET의 short-channel effect, oxide tunneling, process variability를 표현하는 SPICE용 compact 모델 패밀리.

**출처.** UC Berkeley BSIM Research Group.

**관련.** [[SPICE]], [[Pelgrom's Law]].

**예시.** BSIM4는 28 nm 까지의 bulk CMOS, BSIM-CMG는 FinFET용.

## Charge Sharing

**정의.** 스위치로 연결된 두 캐패시터 사이에 전하가 재분배되어 capacitance 비와 초기 전하에 의해 결정되는 공통 voltage가 발생하는 현상.

**출처.** Rabaey, *Digital Integrated Circuits*, DRAM chapter.

**관련.** [[Sense amplifier]], [[Bit line]], [[DRAM cell]].

**예시.** DRAM read 시 `v_shared = (C_cell·v_cell + C_bl·V_pre) / (C_cell + C_bl)`.

## Connect Module

**정의.** Verilog-AMS 또는 SystemVerilog-AMS에서 port 경계의 디지털·아날로그 discipline 간 신호 변환을 자동으로 수행하는 모듈.

**출처.** Verilog-AMS LRM.

**관련.** [[D2A]], [[A2D]], [[AMS]], [[Discipline]].

**예시.** logic `1'b1`을 50 ps rise time과 함께 0.9V로 매핑하는 D2A connect module.

## D2A (Digital-to-Analog Connect Module)

**정의.** 디지털 logic 신호를 rise/fall 천이 가능한 연속시간 아날로그 voltage로 변환하는 connect module.

**출처.** Verilog-AMS LRM § Connect Module Rules.

**관련.** [[A2D]], [[Connect module]].

**예시.** `V(out_a) <+ transition(in_d ? vh : vl, 0, trise, tfall);`

## Discipline

**정의.** Verilog-AMS의 net이 속한 도메인의 potential·flow 성질을 정의하는 명명된 선언.

**출처.** Verilog-AMS LRM § 3 Disciplines.

**관련.** [[Connect module]].

**예시.** `discipline electrical potential Voltage; flow Current; enddiscipline`

## DLL (Delay-Locked Loop)

**정의.** 가변 delay line을 조절하여 출력 클록의 위상을 reference 클록에 정렬하고 residual phase error가 lock threshold 이하가 되도록 유지하는 폐회로 제어 회로.

**출처.** Razavi, *Design of Analog CMOS Integrated Circuits*, Ch. 16.

**관련.** [[PLL]], [[Phase detector]], [[Loop filter]].

**예시.** DDR DRAM 내부 DLL이 외부 CK rising edge에 출력 DQ valid window를 정렬.

## DMS (Digital Mixed-Signal)

**정의.** 디지털 event-driven simulator 내부에서 real-valued net으로 아날로그 동작을 모델링하여 mixed-signal 시뮬레이션을 수행하는 검증 방법론.

**출처.** DVCon UVM-DMS papers.

**관련.** [[RNM]], [[AMS]], [[UDN]].

**예시.** SSD용 PMIC를 SV-RNM(DMS)으로 검증한 사례에서 AMS 대비 100×~1000× speedup 달성 (DVCon 2020).

## Eye Opening

**정의.** 디지털 데이터 신호의 stacked eye diagram에서 파형 overlap이 없는 voltage·timing margin 영역.

**출처.** IEEE 802.3 / JEDEC JESD79 series.

**관련.** [[Jitter]], [[Slew rate]], [[ODT]].

**예시.** DDR5 6.4 Gbps 신호는 eye height 200 mV 이상, eye width 0.4 UI 이상이 필요.

## Fast SPICE

**정의.** Matrix partitioning, table-based device 모델, event-driven analog, hierarchical isomorphism 등의 기법으로 정확도를 일부 희생하면서 1자리 이상 빠른 SPICE 변형.

**출처.** Synopsys CustomSim User Guide.

**관련.** [[SPICE]].

**예시.** Synopsys CustomSim XA가 일반 SPICE로 불가능한 DRAM full-chip 시뮬레이션을 가능하게 함.

## IBIS-AMI (IBIS Algorithmic Model Interface)

**정의.** IBIS 전기 모델과 C/C++ 알고리즘 블록을 결합하여 고속 SerDes 송수신 동작을 표현하는 vendor-neutral behavioral 모델 표준.

**출처.** IBIS Open Forum spec, IBIS 5.0+ (2008), IBIS 7.0+ (back-channel, PAM).

**관련.** [[Eye opening]], [[Jitter]], [[SerDes]].

**예시.** DDR5 SDRAM IBIS-AMI 모델이 CTLE/DFE/CDR 알고리즘을 VCS-AMS 또는 MATLAB SerDes Toolbox에서 호출 가능하게 제공.

## Loop Filter

**정의.** Phase-locked loop 또는 delay-locked loop에서 phase detector 출력을 적분하여 VCO 또는 delay line을 구동하는 제어 신호를 만드는 블록.

**출처.** Gardner, *Phaselock Techniques*, 3rd ed.

**관련.** [[DLL]], [[PLL]], [[Phase detector]].

**예시.** Type-II PLL은 PI(proportional-integral) loop filter로 정상상태 phase error를 0으로 만든다.

## Monte Carlo (mixed-signal 검증에서)

**정의.** Process 분포 가정에서 무작위 추출된 모델 파라미터로 다수의 시뮬레이션을 수행하여 yield 또는 fail rate를 추정하는 통계적 sampling 방법.

**출처.** Pelgrom et al., JSSC 1989.

**관련.** [[Pelgrom's Law]], [[Sense amplifier]].

**예시.** σ=18 mV, signal=100 mV 조건의 10,000-run RNM Monte Carlo가 DRAM SA의 10⁹ cell 중 약 27 cell fail을 예측.

## nettype (SystemVerilog)

**정의.** SystemVerilog 2012부터 도입된, 사용자가 net의 데이터 타입과 multi-driver resolution function을 정의할 수 있게 하는 키워드.

**출처.** IEEE 1800-2012 § 6.6.7.

**관련.** [[RNM]], [[Resolution function]], [[UDN]].

**예시.** `nettype real wreal;` 선언으로 RNM에서 흔히 쓰는 single-driver real 값 net 정의.

## ODT (On-Die Termination)

**정의.** 고속 I/O 라인의 신호 반사를 흡수하기 위해 receiver 측 die 위에 통합된 termination 저항.

**출처.** JEDEC JESD79-5 (DDR5 SDRAM Standard).

**관련.** [[Reflection coefficient]], [[Eye opening]].

**예시.** DDR5는 60Ω, 80Ω, 120Ω 등의 ODT 설정으로 trace impedance와 매칭.

## Pelgrom's Law

**정의.** 두 쌍 MOSFET의 threshold-voltage mismatch 표준편차가 채널 면적의 제곱근에 반비례한다는 경험적 모델.

**출처.** Pelgrom, Duinmaijer, Welbers, *"Matching properties of MOS transistors"*, IEEE JSSC, vol. 24, no. 5, 1989.

**관련.** [[Monte Carlo]], [[Sense amplifier]].

**예시.** AVT = 4 mV·μm, W·L = 0.05 μm² 일 때 σ(ΔVth) ≈ 17.9 mV.

## PLL (Phase-Locked Loop)

**정의.** Voltage-controlled oscillator, phase detector, loop filter를 통해 출력 클록의 주파수와 위상을 reference 클록에 정렬하는 폐회로 회로.

**출처.** Razavi, *Design of Analog CMOS Integrated Circuits*, Ch. 15.

**관련.** [[DLL]], [[VCO]], [[Loop filter]].

**예시.** SerDes의 PLL이 송신 symbol에 사용되는 GHz 단위 클록 생성.

## Resolution Function

**정의.** 한 net에 여러 driver가 있을 때 그 값들을 하나의 net 값으로 결합하는 사용자 정의 SystemVerilog 함수.

**출처.** IEEE 1800-2017 SystemVerilog LRM.

**관련.** [[nettype]], [[UDN]].

**예시.** `resolve_thevenin` 함수가 EEnet 위 여러 driver의 parallel-source Thevenin voltage를 반환.

## RNM (Real Number Modeling)

**정의.** 디지털 event-driven simulator 안에서 real-valued 신호로 아날로그 회로 동작을 근사하는 mixed-signal 모델링 방법.

**출처.** Bhattacharya, *"Real Number Modeling for Mixed-Signal Verification"*, DVCon.

**관련.** [[nettype]], [[DMS]], [[AMS]].

**예시.** DRAM bit-line voltage를 word-line activation 이벤트에서만 evaluate되는 `wreal`로 모델링.

## Sense Amplifier

**정의.** DRAM이나 SRAM에서 두 complementary line 사이의 작은 voltage 차이를 감지하여 full-swing 디지털 레벨로 증폭하는 differential amplifier 회로.

**출처.** Rabaey, *Digital Integrated Circuits: A Design Perspective*.

**관련.** [[Charge sharing]], [[Bit line]], [[Pelgrom's Law]].

**예시.** DDR5 sense amp가 bit line의 약 ±60mV 차이를 감지하여 VDDQ/0 V로 latch.

## SPICE (Simulation Program with Integrated Circuit Emphasis)

**정의.** Kirchhoff 법칙과 BSIM 같은 compact device 모델을 함께 수치적으로 풀어 transient, AC, DC, noise 응답을 계산하는 회로 시뮬레이터 패밀리.

**출처.** Nagel, *"SPICE2"*, UCB ERL Memo, 1975.

**관련.** [[BSIM]], [[AMS]], [[Fast SPICE]].

**예시.** Synopsys HSPICE는 sign-off 정확도의 industry "gold reference"로 간주됨.

## UDN (User-Defined Nettype)

**정의.** 사용자가 선언한 composite(주로 struct) 데이터 타입을 갖고, 사용자 resolution function으로 multi-driver 동작이 결정되는 SystemVerilog net.

**출처.** IEEE 1800-2017 § 6.6.7; EEnet/complex UDN DVCon papers.

**관련.** [[nettype]], [[Resolution function]], [[EEnet]].

**예시.** Cadence `EE_pkg::EEnet`이 노드를 `{voltage, impedance}`로 모델링하고 여러 driver를 Thevenin equivalent로 resolve.

## Verilog-AMS

**정의.** Verilog에 electrical discipline, 연속시간 아날로그 식, connect-module 규칙을 추가한 Accellera 발행 mixed-signal 하드웨어 기술 언어.

**출처.** IEEE 1364.1; Accellera VAMS-2023 (2024-02).

**관련.** [[AMS]], [[Connect module]], [[Discipline]].

**예시.** `analog begin` 블록 안의 `V(out) <+ gain * V(in);` — linear voltage amplifier 표현.

## ZQ Calibration

**정의.** 프로그래머블 I/O driver 및 termination 저항의 디지털 제어 코드를 외부 정밀 참조 저항(보통 ZQ pin 240Ω)과 매칭되도록 주기적으로 조정하는 on-chip 절차.

**출처.** JEDEC JESD79-5C (DDR5 SDRAM Standard) § ZQ Calibration.

**관련.** [[ODT]], [[Eye opening]].

**예시.** DDR5는 ZQCS(short) 명령을 128ms마다 실행하여 driver 저항의 process·temperature drift를 보상.

## 참고

- [English mirror](appendix_c_glossary.md)
- [Quick Reference](appendix_a_quick_reference.md)
