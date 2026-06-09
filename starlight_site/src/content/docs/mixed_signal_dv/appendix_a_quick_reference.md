---
title: "Appendix A. Quick Reference — 식·상수·표"
---

> 이 부록은 각 챕터에서 설명한 식·상수·문법을 한곳에 모은 빠른 참조표입니다. 처음 보는 용어(charge sharing, Pelgrom's law, Q-function 등)는 [Glossary](../appendix_c_glossary/) 또는 해당 챕터의 정의를 참고하세요.

## 1. 핵심 식

### Charge Sharing (DRAM read)

```
v_shared = (C_cell · v_cell + C_bl · V_pre) / (C_cell + C_bl)
ΔBL     = v_shared - V_pre
        = C_cell × (v_cell - V_pre) / (C_cell + C_bl)
```

### Pelgrom's Law

```
σ(ΔVth)     = AVT / sqrt(W × L)        [mV]
σ(Δβ/β)     = Aβ  / sqrt(W × L)        [%]
```

### Reflection Coefficient

```
Γ = (R_load - Z0) / (R_load + Z0)
```

### RC charging

```
V(t) = V_target + (V_initial - V_target) × exp(-t / RC)
τ    = R × C                          [s]
```

### KCL at a node (Thevenin equivalent of 2 sources)

```
V_node = (V1/R1 + V2/R2) / (1/R1 + 1/R2)
R_eq   = (R1 × R2) / (R1 + R2)
```

### DLL Lock Time

```
N_cycles = (target_delay - initial_delay) / step
t_lock   = N_cycles × T_ref + N_lock_stable × T_ref
```

### Slew Rate vs Transition Time

```
t_transition = V_swing / slew_rate
condition for valid eye: t_transition < UI (unit interval)
```

## 2. 핵심 상수 (참고)

### Process 별 Pelgrom AVT

| Process | AVT (mV·μm) |
|---|---|
| 250 nm | ~20 |
| 130 nm | ~10 |
| 65 nm | ~5 |
| 28 nm | ~4 |
| 16 nm FinFET | ~2.5 |
| 7 nm FinFET | ~2.0 |
| 5 nm FinFET | ~1.8 |
| 3 nm GAA | ~1.6 (추정 — MGG/RDF 비중 증가) |

### Gaussian Tail Probability (Q-function)

| σ ratio | Q(x) | P(|x| > σ) |
|---|---|---|
| 3 | 1.35e-3 | 2.7e-3 |
| 4 | 3.17e-5 | 6.3e-5 |
| 5 | 2.87e-7 | 5.7e-7 |
| 5.56 | 1.36e-8 | 2.7e-8 |
| 6 | 9.87e-10 | 2.0e-9 |
| 7 | 1.28e-12 | 2.6e-12 |
| 8 | 6.22e-16 | 1.2e-15 |

### DRAM 일반 capacitance (참고)

| Cap | 값 |
|---|---|
| C_cell (modern) | 20~40 fF |
| C_bl | 80~200 fF |
| C_load (IO) | 5~30 fF |

### Termination voltages

| 인터페이스 | VTT | VDDQ |
|---|---|---|
| DDR4 | 0.6 V | 1.2 V |
| DDR5 | 0.55 V | 1.1 V |
| LPDDR5 | 0.25 V | 0.5 V (VDDQ_LP) |

## 3. SystemVerilog RNM Cheat Sheet

```systemverilog
// 1. real 변수
real voltage;
real cap = 1.0e-15;

// 2. nettype 선언
nettype real wreal;

// 3. UDN with resolution
typedef struct packed {
  real voltage;
  real impedance;
} ee_t;

function automatic ee_t resolve_thevenin(input ee_t drivers[]);
  // ...
endfunction

nettype ee_t eenet with resolve_thevenin;

// 4. Module port
module sense_amp(
  input  wreal vp,
  input  wreal vn,
  output logic d
);
  always @(*) d = (vp > vn) ? 1'b1 : 1'b0;
endmodule

// 5. Random (Gaussian)
real x;
int  seed = 1;
initial x = $dist_normal(seed, 0, sigma);
```

## 4. Verilog-AMS Cheat Sheet

```verilog
`include "disciplines.vams"

module rc_lpf(in, out);
  input in; output out;
  electrical in, out;
  parameter real R = 1k;
  parameter real C = 1n;

  analog begin
    I(in, out) <+ (V(in) - V(out)) / R;
    I(out)     <+ C * ddt(V(out));
  end
endmodule

// Connect module
connectmodule d2a_simple(in_d, out_a);
  input in_d; output out_a;
  logic in_d;
  electrical out_a;
  parameter real vh = 0.9;
  analog V(out_a) <+ transition(in_d ? vh : 0, 0, 50p, 50p);
endmodule
```

## 5. SPICE Quick Reference

```spice
* Element types
R<name>  node1 node2 value          * Resistor
C<name>  node1 node2 value [IC=v]   * Capacitor
L<name>  node1 node2 value          * Inductor
V<name>  node1 node2 dc|ac|pulse|... * Voltage source
M<name>  drain gate source bulk model w=.. l=..  * MOSFET

* Sources
PULSE(low high delay rise fall width period)
SIN(offset amp freq)
DC value

* Analysis
.op
.dc V1 0 1 0.01
.ac dec 10 1k 1G
.tran step stop
.noise v(out) Vin dec 10 1 1G

* Measure
.measure tran tpd TRIG v(in) VAL=0.45 RISE=1 TARG v(out) VAL=0.45 FALL=1

* Process variation
.mc 1000 vary=all dist=gauss
```

## 6. 도구 매핑 빠른 표

| 검증 task | 추천 도구 |
|---|---|
| RNM only DRAM full-chip | VCS / Xcelium / Questa |
| AMS connect (RNM + SPICE) | VCS AMS / AMS Designer / Questa AMS |
| Fast SPICE for DRAM array | CustomSim / FineSim Pro |
| BGR Monte Carlo sign-off | HSPICE |
| DDR5 channel eye | MATLAB SerDes / ADS |
| PCIe Gen5 back-channel | MATLAB SerDes (IBIS 7.0+) |

## 7. Bloom 동사 빠른 표 (학습 목표 작성용)

| Level | Verbs |
|-------|-------|
| Remember | define, list, recall, identify, state, recognize, name |
| Understand | explain, describe, summarize, classify, interpret, paraphrase, compare |
| Apply | apply, use, implement, demonstrate, execute, simulate, configure |
| Analyze | analyze, differentiate, decompose, attribute, organize, debug, trace |
| Evaluate | evaluate, judge, critique, justify, validate, prioritize, defend |
| Create | design, construct, generate, plan, produce, derive, compose |

## 더 읽을거리

- [Glossary (EN)](../appendix_c_glossary/)
- [Code Examples (EN)](../appendix_b_code_examples/)
