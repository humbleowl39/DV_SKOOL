# Appendix B. Code Examples (EN)

> Three runnable RNM examples — Inverter, DRAM cell + Sense Amp, PLL Lock indicator.
>
> Original source: `20260521_142844_PRATICE_MIXED_SIGNAL_LEARNING/examples/`
> Korean mirror: [appendix_b_code_examples_ko.md](appendix_b_code_examples_ko.md)

## Setup

```bash
# Environment
source set_env.sh   # provides VCS path, LM_LICENSE_FILE
cd <example_dir>
./run.sh
```

Requirements:

- VCS 2013+ (SystemVerilog `nettype` support)
- Linux (CentOS 7+, Ubuntu 20.04+)
- 4 GB RAM

## Example 1 — Inverter RNM

### Files

- `rnm_pkg.sv` — common `nettype real wreal` declaration
- `inverter_rnm.sv` — Level 2 RNM inverter (with ramp transition)
- `tb_inverter.sv` — Self-checking TB with PASS/FAIL report
- `run.sh` — VCS compile+run script

### Inverter Module (excerpt)

```systemverilog
`timescale 1ns/1ps

package rnm_pkg;
  nettype real wreal;
endpackage

module inverter_rnm
  import rnm_pkg::*;
(
  input  wreal vin,
  output wreal vout
);
  parameter real VDD   = 0.9;
  parameter real VTH   = 0.45;
  parameter real TPD   = 50.0;    // ps
  parameter real TRISE = 30.0;    // ps

  real vout_target;

  always @(vin) begin
    vout_target = (vin > VTH) ? 0.0 : VDD;
  end

  assign #(TPD * 1ps) vout = vout_target;
endmodule
```

### Testbench (excerpt)

```systemverilog
module tb_inverter
  import rnm_pkg::*;
;
  wreal vin, vout;
  reg pass = 1;

  inverter_rnm dut (.vin(vin), .vout(vout));

  initial begin
    vin = 0.0;
    #100ps;
    if (vout < 0.85) pass = 0;  // expect HIGH

    vin = 0.9;
    #100ps;
    if (vout > 0.05) pass = 0;  // expect LOW

    if (pass) $display("PASS: inverter RNM");
    else      $display("FAIL: inverter RNM");
    $finish;
  end
endmodule
```

### Expected Output

```
PASS: inverter RNM
```

## Example 2 — DRAM Cell + Sense Amp

### Files

- `tb_dram_read.sv` — Cell + Sense Amp RNM model + TB combined
- `run.sh`
- `README.md`
- `expected_output.txt`

### TB structure (excerpt)

```systemverilog
module dram_cell_rnm(
  input  logic     wl,
  inout  wreal     bl,
  input  logic     wdata,
  input  logic     we
);
  parameter real C_CELL = 30.0e-15;
  parameter real C_BL   = 100.0e-15;
  parameter real VDD    = 0.9;
  parameter real VPRE   = 0.45;

  real v_cell;
  real bl_drive;

  always @(posedge wl) begin
    if (we) v_cell = wdata ? VDD : 0.0;
  end

  always @(posedge wl) begin
    automatic real q_cell, q_bl, v_shared;
    if (!we) begin
      q_cell   = C_CELL * v_cell;
      q_bl     = C_BL   * VPRE;
      v_shared = (q_cell + q_bl) / (C_CELL + C_BL);
      bl_drive = v_shared;
      v_cell   = v_shared;  // destructive read
    end
  end

  assign bl = bl_drive;
endmodule

module sense_amp_rnm(
  input  logic sense_en,
  input  wreal bl,
  input  wreal bl_ref,
  output logic data_out
);
  parameter real VTH_DETECT = 0.005;
  always @(posedge sense_en) begin
    if (bl > bl_ref + VTH_DETECT)         data_out = 1'b1;
    else if (bl < bl_ref - VTH_DETECT)    data_out = 1'b0;
  end
endmodule
```

### Expected Output

```
[Write '1'] v_cell = 0.900
[Read]      v_shared = 0.5538, BL = 0.5538
[Sense]     BL > BL_ref + 5mV → data_out = 1
PASS
```

## Example 3 — PLL Lock Indicator

### Goal

Demonstrate basic PLL behavior:

- VCO frequency = K_VCO × V_ctrl
- Phase detector compares ref_clk vs feedback (divided VCO)
- Loop filter accumulates phase error → V_ctrl
- Lock detector: 16 consecutive cycles within ±5% of target

### Files

- `rnm_pkg.sv`
- `pll_rnm.sv`
- `tb_pll.sv`
- `run.sh`
- `README.md`
- `expected_output.txt`

### Module sketch

```systemverilog
module pll_rnm
  import rnm_pkg::*;
#(
  parameter real REF_FREQ_HZ = 100e6,   // 100 MHz
  parameter int  DIV         = 10,       // VCO = 1 GHz
  parameter real K_VCO       = 1e9,      // 1 GHz / V
  parameter real KP          = 0.01,
  parameter real KI          = 0.001
)(
  input  logic ref_clk,
  output logic vco_clk,
  output logic locked
);
  // ... PD + LF + VCO + divider + lock detect
endmodule
```

Full implementation: see `examples/03_pll_lock_indicator/` directory.

### Expected Output

```
[t=0]     V_ctrl = 0.500, freq = 500 MHz, target = 1000 MHz
[t=200ns] V_ctrl = 0.823, freq = 823 MHz
[t=500ns] V_ctrl = 0.991, freq = 991 MHz — within 1%
[t=600ns] V_ctrl = 1.000, freq = 1000 MHz — LOCKED
PASS: PLL locked at t = 600ns
```

## How to extend

- Add noise: `$dist_normal(seed, 0, sigma)` in `always @(posedge clk)`
- Add temperature drift: scale K_VCO by (1 - alpha × (T - 25))
- Add power supply sag: modulate VDD parameter at runtime

## See also

- [Korean mirror](appendix_b_code_examples_ko.md)
- [Ch05. RNM with SystemVerilog](05_rnm_systemverilog.md)
- [Ch07. DLL Deep Dive](07_deepdive_dll_rnm.md)
