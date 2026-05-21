# 부록 B. 코드 예제 (KO)

> 실행 가능한 RNM 예제 3종 — Inverter, DRAM cell+Sense Amp, PLL Lock indicator.
>
> 원본: `20260521_142844_PRATICE_MIXED_SIGNAL_LEARNING/examples/`
> English mirror: [appendix_b_code_examples.md](appendix_b_code_examples.md)

## 환경 준비

```bash
# 환경 설정
source set_env.sh   # VCS 경로 + LM_LICENSE_FILE 제공
cd <example_dir>
./run.sh
```

요구사항:

- VCS 2013 이상 (SystemVerilog `nettype` 지원)
- Linux (CentOS 7+, Ubuntu 20.04+)
- 4 GB RAM

## 예제 1 — Inverter RNM

### 파일

- `rnm_pkg.sv` — 공통 `nettype real wreal` 선언
- `inverter_rnm.sv` — Level 2 RNM 인버터 (ramp transition 포함)
- `tb_inverter.sv` — Self-checking TB
- `run.sh` — VCS 컴파일·실행 스크립트

### 인버터 모듈 (발췌)

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

### Testbench (발췌)

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
    if (vout < 0.85) pass = 0;  // 기대: HIGH

    vin = 0.9;
    #100ps;
    if (vout > 0.05) pass = 0;  // 기대: LOW

    if (pass) $display("PASS: inverter RNM");
    else      $display("FAIL: inverter RNM");
    $finish;
  end
endmodule
```

### 기대 출력

```
PASS: inverter RNM
```

## 예제 2 — DRAM Cell + Sense Amp

### 파일

- `tb_dram_read.sv` — Cell + Sense Amp RNM 모델 + TB 통합
- `run.sh`
- `README.md`
- `expected_output.txt`

### TB 구조 (발췌)

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

  // Write
  always @(posedge wl) begin
    if (we) v_cell = wdata ? VDD : 0.0;
  end

  // Read — charge sharing
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

### 기대 출력

```
[Write '1'] v_cell = 0.900
[Read]      v_shared = 0.5538, BL = 0.5538
[Sense]     BL > BL_ref + 5mV → data_out = 1
PASS
```

## 예제 3 — PLL Lock Indicator

### 목표

기본 PLL 동작 시연:

- VCO 주파수 = K_VCO × V_ctrl
- Phase detector가 ref_clk 와 feedback(VCO 분주)을 비교
- Loop filter가 phase error를 누적 → V_ctrl
- Lock detector: 16 cycle 연속 ±5% 이내면 lock

### 파일

- `rnm_pkg.sv`
- `pll_rnm.sv`
- `tb_pll.sv`
- `run.sh`
- `README.md`
- `expected_output.txt`

### 모듈 스케치

```systemverilog
module pll_rnm
  import rnm_pkg::*;
#(
  parameter real REF_FREQ_HZ = 100e6,   // 100 MHz
  parameter int  DIV         = 10,       // VCO = 1 GHz target
  parameter real K_VCO       = 1e9,      // 1 GHz / V
  parameter real KP          = 0.01,
  parameter real KI          = 0.001
)(
  input  logic ref_clk,
  output logic vco_clk,
  output logic locked
);
  // PD + LF + VCO + divider + lock detect
endmodule
```

전체 구현은 `examples/03_pll_lock_indicator/` 디렉토리 참조.

### 기대 출력

```
[t=0]     V_ctrl = 0.500, freq = 500 MHz, target = 1000 MHz
[t=200ns] V_ctrl = 0.823, freq = 823 MHz
[t=500ns] V_ctrl = 0.991, freq = 991 MHz — within 1%
[t=600ns] V_ctrl = 1.000, freq = 1000 MHz — LOCKED
PASS: PLL locked at t = 600ns
```

## 확장 아이디어

- 노이즈 추가: `always @(posedge clk)` 안에 `$dist_normal(seed, 0, sigma)`
- 온도 drift: `K_VCO`를 `(1 - alpha × (T - 25))`로 scale
- 전원 sag: 런타임에 VDD parameter 변조

## 참고

- [English mirror](appendix_b_code_examples.md)
- [Ch05. RNM with SystemVerilog](05_rnm_systemverilog.md)
- [Ch07. DLL Deep Dive](07_deepdive_dll_rnm.md)
