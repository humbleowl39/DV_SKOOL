# Appendix C. Glossary (EN, ISO 11179)

> Term definitions follow ISO 11179: a single sentence stating **what the concept IS**, with separate fields for examples and references.
>
> Korean mirror: [appendix_c_glossary_ko.md](appendix_c_glossary_ko.md)

## AMS (Analog Mixed-Signal Simulation)

**Definition.** A simulation methodology that concurrently runs a digital event-driven engine and an analog continuous-time engine on the same design through synchronized connect modules.

**Source.** Verilog-AMS LRM (IEEE 1364.1 / Accellera VAMS-2023).

**Related.** [[SPICE]], [[RNM]], [[Connect module]].

**Example.** Cadence AMS Designer combines Xcelium (digital) and Spectre (analog) for ADC verification.

## A2D (Analog-to-Digital Connect Module)

**Definition.** A connect module that converts a continuous-time analog signal into a discrete-time digital logic signal by detecting threshold crossings.

**Source.** Verilog-AMS LRM § Connect Module Rules.

**Related.** [[D2A]], [[Connect module]], [[Discipline]].

**Example.** `@(cross(V(in) - vth, +1)) out = 1'b1;` defines a rising-edge threshold detector.

## BSIM (Berkeley Short-channel IGFET Model)

**Definition.** A family of compact MOSFET models developed at UC Berkeley that captures short-channel effects, oxide tunneling, and process variability for use in SPICE simulation.

**Source.** UC Berkeley BSIM Research Group.

**Related.** [[SPICE]], [[Pelgrom's Law]].

**Example.** BSIM4 covers bulk CMOS down to 28 nm; BSIM-CMG covers FinFET nodes.

## Charge Sharing

**Definition.** The redistribution of charge between two capacitors connected through a switch, resulting in a common voltage determined by the capacitance ratio and initial charges.

**Source.** Rabaey, *Digital Integrated Circuits*, DRAM chapter.

**Related.** [[Sense amplifier]], [[Bit line]], [[DRAM cell]].

**Example.** During DRAM read, `v_shared = (C_cell·v_cell + C_bl·V_pre) / (C_cell + C_bl)`.

## Connect Module

**Definition.** A Verilog-AMS or SystemVerilog-AMS module that performs automatic signal conversion between digital and analog disciplines at port boundaries.

**Source.** Verilog-AMS LRM.

**Related.** [[D2A]], [[A2D]], [[AMS]], [[Discipline]].

**Example.** A D2A connect module maps logic `1'b1` to 0.9 V with a 50 ps rise time.

## D2A (Digital-to-Analog Connect Module)

**Definition.** A connect module that converts a digital logic signal into a continuous-time analog voltage with configurable rise/fall transitions.

**Source.** Verilog-AMS LRM § Connect Module Rules.

**Related.** [[A2D]], [[Connect module]].

**Example.** `V(out_a) <+ transition(in_d ? vh : vl, 0, trise, tfall);`

## Discipline

**Definition.** A named declaration in Verilog-AMS that specifies the potential and flow nature of an electrical (or other) net domain.

**Source.** Verilog-AMS LRM § 3 Disciplines.

**Related.** [[Connect module]].

**Example.** `discipline electrical potential Voltage; flow Current; enddiscipline`

## DLL (Delay-Locked Loop)

**Definition.** A closed-loop control circuit that aligns the phase of an output clock to a reference clock by adjusting a variable delay line until the residual phase error is below a lock threshold.

**Source.** Razavi, *Design of Analog CMOS Integrated Circuits*, Ch. 16.

**Related.** [[PLL]], [[Phase detector]], [[Loop filter]].

**Example.** A DDR DRAM uses an internal DLL to align the output DQ valid window to the external CK rising edge.

## DMS (Digital Mixed-Signal)

**Definition.** A verification methodology that performs mixed-signal simulation entirely within a digital event-driven simulator by using real-valued nets to model analog behavior.

**Source.** DVCon papers on UVM-DMS methodology.

**Related.** [[RNM]], [[AMS]], [[UDN]].

**Example.** A PMIC for SSD verified end-to-end in SV-RNM (DMS) achieved 100×–1000× speedup over AMS (DVCon 2020 paper).

## Eye Opening

**Definition.** The internal area of a stacked eye diagram of a digital data signal, bounded vertically by voltage margin and horizontally by timing margin, that remains free of waveform overlap.

**Source.** IEEE 802.3 / JEDEC JESD79 series.

**Related.** [[Jitter]], [[Slew rate]], [[ODT]].

**Example.** A DDR5 6.4 Gbps signal requires sufficient eye height (e.g., > 200 mV) and eye width (e.g., > 0.4 UI) for reliable reception.

## Fast SPICE

**Definition.** A SPICE simulator variant that trades a small amount of accuracy for one or more orders of magnitude in runtime through matrix partitioning, table-based device models, event-driven analog evaluation, and hierarchical isomorphism.

**Source.** Synopsys CustomSim User Guide.

**Related.** [[SPICE]].

**Example.** Synopsys CustomSim XA enables full-chip DRAM array simulation that is infeasible with general-purpose SPICE.

## IBIS-AMI (IBIS Algorithmic Model Interface)

**Definition.** A vendor-neutral behavioral model standard for high-speed serializer-deserializer (SerDes) transceivers that combines an IBIS electrical model with C/C++ algorithmic blocks for transmitter and receiver equalization.

**Source.** IBIS Open Forum specification, IBIS 5.0+ (2008) and IBIS 7.0+ (back-channel, PAM).

**Related.** [[Eye opening]], [[Jitter]], [[SerDes]].

**Example.** A DDR5 SDRAM IBIS-AMI model provides CTLE, DFE, and CDR algorithms callable from VCS-AMS or MATLAB SerDes Toolbox.

## Loop Filter

**Definition.** The block in a phase-locked loop or delay-locked loop that integrates the phase detector output into a control signal driving the VCO or delay line.

**Source.** Gardner, *Phaselock Techniques*, 3rd ed.

**Related.** [[DLL]], [[PLL]], [[Phase detector]].

**Example.** A type-II PLL uses a proportional-integral loop filter to achieve zero steady-state phase error.

## Monte Carlo (in mixed-signal verification)

**Definition.** A statistical sampling method that runs many simulations with randomized model parameters drawn from process-distribution assumptions to estimate yield or failure rate.

**Source.** Pelgrom et al., *"Matching properties of MOS transistors"*, JSSC 1989.

**Related.** [[Pelgrom's Law]], [[Sense amplifier]].

**Example.** 10,000-run RNM Monte Carlo predicts a DRAM sense amp fail rate of ~27 cells out of 10⁹ given σ = 18 mV and a 100 mV signal.

## nettype (SystemVerilog)

**Definition.** A SystemVerilog 2012 keyword that lets users declare a net whose data type and multi-driver resolution function are both user-defined.

**Source.** IEEE 1800-2012 § 6.6.7.

**Related.** [[RNM]], [[Resolution function]], [[UDN]].

**Example.** `nettype real wreal;` declares a single-driver real-valued net commonly used in RNM.

## ODT (On-Die Termination)

**Definition.** A receiver-side termination resistor integrated on the chip die to absorb signal reflections on high-speed I/O lines.

**Source.** JEDEC JESD79-5 (DDR5 SDRAM Standard).

**Related.** [[Reflection coefficient]], [[Eye opening]].

**Example.** DDR5 typically uses 60 Ω, 80 Ω, or 120 Ω ODT settings to match the trace impedance.

## Pelgrom's Law

**Definition.** An empirical model stating that the standard deviation of threshold-voltage mismatch between two paired MOSFETs is inversely proportional to the square root of their channel area.

**Source.** Pelgrom, Duinmaijer, Welbers, *"Matching properties of MOS transistors"*, IEEE JSSC, vol. 24, no. 5, 1989.

**Related.** [[Monte Carlo]], [[Sense amplifier]].

**Example.** With AVT = 4 mV·μm, W·L = 0.05 μm², σ(ΔVth) ≈ 17.9 mV.

## PLL (Phase-Locked Loop)

**Definition.** A closed-loop circuit that generates an output clock whose frequency and phase are aligned to a reference clock through a voltage-controlled oscillator, phase detector, and loop filter.

**Source.** Razavi, *Design of Analog CMOS Integrated Circuits*, Ch. 15.

**Related.** [[DLL]], [[VCO]], [[Loop filter]].

**Example.** A SerDes uses a PLL to generate the gigahertz-range clock used to launch transmitted symbols.

## Resolution Function

**Definition.** A user-defined SystemVerilog function that combines the values of multiple drivers on a single net into a single resolved net value.

**Source.** IEEE 1800-2017 SystemVerilog LRM.

**Related.** [[nettype]], [[UDN]].

**Example.** A `resolve_thevenin` function returns the parallel-source Thevenin voltage of multiple drivers on an EEnet.

## RNM (Real Number Modeling)

**Definition.** A mixed-signal modeling methodology that approximates analog circuit behavior with real-valued signals inside an event-driven digital simulator.

**Source.** Bhattacharya, *"Real Number Modeling for Mixed-Signal Verification"*, DVCon.

**Related.** [[nettype]], [[DMS]], [[AMS]].

**Example.** A DRAM bit-line voltage modeled as `wreal` evaluated only on word-line activation events.

## Sense Amplifier

**Definition.** A differential amplifier circuit, typically used in DRAM and SRAM, that detects a small voltage difference between two complementary lines and amplifies it to full digital swing.

**Source.** Rabaey, *Digital Integrated Circuits: A Design Perspective*.

**Related.** [[Charge sharing]], [[Bit line]], [[Pelgrom's Law]].

**Example.** A DDR5 sense amp detects roughly ±60 mV on the bit line and latches it to VDDQ / 0 V.

## SPICE (Simulation Program with Integrated Circuit Emphasis)

**Definition.** A circuit simulator family that numerically solves Kirchhoff's laws together with compact device models such as BSIM to produce transient, AC, DC, or noise responses.

**Source.** Nagel, *"SPICE2: A Computer Program to Simulate Semiconductor Circuits"*, UCB ERL Memo, 1975.

**Related.** [[BSIM]], [[AMS]], [[Fast SPICE]].

**Example.** Synopsys HSPICE is widely treated as the industry "gold reference" for sign-off accuracy.

## UDN (User-Defined Nettype)

**Definition.** A SystemVerilog net whose data type is a user-declared composite (typically a struct) and whose multi-driver behavior is governed by a custom resolution function.

**Source.** IEEE 1800-2017 § 6.6.7; DVCon papers on EEnet, complex UDN.

**Related.** [[nettype]], [[Resolution function]], [[EEnet]].

**Example.** Cadence `EE_pkg::EEnet` models a node as `{voltage, impedance}` and resolves multiple drivers as a Thevenin equivalent.

## Verilog-AMS

**Definition.** An Accellera-published mixed-signal hardware description language that extends Verilog with electrical disciplines, continuous-time analog equations, and connect-module rules.

**Source.** IEEE 1364.1; Accellera VAMS-2023 (Feb 2024).

**Related.** [[AMS]], [[Connect module]], [[Discipline]].

**Example.** `V(out) <+ gain * V(in);` inside an `analog begin` block expresses a linear voltage amplifier.

## ZQ Calibration

**Definition.** A periodic on-chip procedure that adjusts the digital control codes of programmable I/O driver and termination resistors so that their effective impedance matches a precision external reference (typically 240 Ω on the ZQ pin).

**Source.** JEDEC JESD79-5C (DDR5 SDRAM Standard) § ZQ Calibration.

**Related.** [[ODT]], [[Eye opening]].

**Example.** A ZQCS (short) command runs every 128 ms in DDR5 to compensate for process and temperature drift in the driver resistance.

## See also

- [Korean mirror](appendix_c_glossary_ko.md)
- [Quick Reference](appendix_a_quick_reference.md)
