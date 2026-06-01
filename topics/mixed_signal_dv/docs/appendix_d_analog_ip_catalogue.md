# Appendix D. Analog IP Catalogue — RNM 모델·검증 시나리오·Coverage

본 부록은 SoC에서 가장 자주 등장하는 8가지 analog/mixed-signal IP에 대해 **spec 표 + 최소 RNM 모델 + 검증 시나리오 + coverage 골격 + 흔한 함정**을 한 페이지씩 정리한 카탈로그입니다. 각 IP의 deep dive는 별도 챕터(Ch07 DLL, Ch08 IO buffer, Ch09 sense amp)에서 다룹니다.

| IP | 검증 RNM 적합도 | 주 코너 도구 |
|---|---|---|
| [PLL](#1-pll--phase-locked-loop) | ◎ functional / lock | Spice (jitter) |
| [ADC](#2-adc--analog-to-digital-converter) | ◎ INL/DNL/monotonicity | Spice (ENOB, SNR) |
| [DAC](#3-dac--digital-to-analog-converter) | ◎ monotonicity/settling | Spice (glitch, SFDR) |
| [LDO](#4-ldo--low-dropout-regulator) | ◎ regulation/UVLO | Spice (PSRR, noise) |
| [Bandgap](#5-bandgap-reference) | ○ TC/line/trim | Spice (noise, dead-state) |
| [PMU](#6-pmu--power-management-unit) | ◎ sequencing/fault | Spice (ripple) |
| [Sensors](#7-sensors--comparator--temp-sensor--oscillator) | ○ functional | Spice (jitter, accuracy) |
| [SerDes PHY](#8-serdes-phy) | △ protocol만 | IBIS-AMI / Spice / scope |

---

## 1. PLL — Phase-Locked Loop

```d2
direction: down

g: {
  grid-rows: 2
  grid-gap: 70
  f_ref: "f_ref"
  f_out: "f_out"
  pfd: "PFD"
  div_n: "/N (div)"
  cp: "CP"
  lpf: "LPF"
  vco: "VCO"
}

g.f_ref -> g.pfd -> g.cp -> g.lpf -> g.vco -> g.f_out
g.vco -> g.div_n
g.div_n -> g.pfd: "feedback"
```

### spec

| 항목 | 의미 | RNM에서 |
|---|---|---|
| f_out range | VCO 동작 범위 (예: 200 MHz ~ 2 GHz) | O (Kvco · Vctrl) |
| lock time | step 이후 \|f_err\| < ε 도달까지 시간 | O (loop dynamics) |
| lock range | cycle slip 없이 lock 가능한 freq 범위 | O |
| divider ratio M, N | integer 또는 fractional | O (FSM/모듈로) |
| RMS jitter | cycle-to-cycle 위상 noise | X (Spice / behavioral noise) |
| spurs | 주파수 도메인 tone | X (Spice) |
| reference loss | ref 끊기면 어떻게 | O (digital handling) |
| fast-lock mode | 큰 step 시 loop bandwidth 변경 | O (mode FSM) |

> RNM은 PLL의 functional behavior만 봅니다. jitter spec(phase noise integration), spur 위치는 RNM이 못 봅니다 — Spice transient + noise simulation 또는 statistical PLL 모델 필요.

### 최소 RNM 모델

```systemverilog
module pll_rnm #(
  real KVCO     = 100e6,     // Hz/V
  real F_CENTER = 1.0e9,     // Hz at Vctrl_mid
  real VMID     = 0.5,
  real KPD      = 1.0,       // PFD/CP gain
  real R        = 1e3,
  real C        = 1e-9
)(
  input  bit       clk_ref,
  input  bit       en,
  input  [7:0]     div_n,
  output bit       clk_out
);
  real vctrl = 0.0, f_out, err_int;
  realtime t_prev; int div_cnt; bit clk_fb;

  always @(vctrl) f_out = F_CENTER + KVCO * (vctrl - VMID);

  always begin
    if (!en) begin #1ns; continue; end
    #( (0.5/f_out) * 1s ) clk_out = ~clk_out;
  end

  always @(posedge clk_out) begin
    div_cnt++;
    if (div_cnt >= div_n) begin clk_fb = ~clk_fb; div_cnt = 0; end
  end

  always @(posedge clk_ref or posedge clk_fb) begin
    real phase_err; realtime dt = $realtime - t_prev;
    phase_err = (clk_ref ? +1 : -1) * KPD;
    err_int   = err_int + phase_err * (dt * 1e-9);
    vctrl     = VMID + err_int / (R * C);
    t_prev    = $realtime;
  end
endmodule
```

### 검증 시나리오

- **Cold start lock** — power-on → enable → ref clock 안정 → lock_done 발생까지 시간
- **Frequency step** — 분주비 또는 ref 주파수 step → 재lock. step 크기 vs lock time 곡선
- **Vctrl sweep** — VCO 동작 범위 전수 확인. saturation 영역에서 lock 실패 명시
- **Reference loss** — ref clock 중단 → loss 검출 + fault → ref 복귀 시 re-lock
- **Mode switch** — fast-lock ↔ low-noise 전환
- **Divider modulation** — fractional N: modulator 동작, integer boundary spurs (RNM은 functional만)

### scoreboard 핵심

```systemverilog
// 1) lock 후 출력 주파수 정확도 100 ppm 이내
real f_meas = measure_f_out(N_avg);
`REAL_EQ(f_meas, f_target, f_target * 100e-6)

// 2) lock time 한계
assert (t_lock_done - t_step < spec.t_lock_max);

// 3) lock_done 정합성
assert property (@(posedge clk) lock_done |-> ($abs(f_meas - f_target) < eps));
```

### coverage

```systemverilog
covergroup cg_pll with function sample(int f_bin, int step_bin, bit lock_ok);
  cp_f:    coverpoint f_bin { bins low={0}; bins mid={1}; bins high={2}; }
  cp_step: coverpoint step_bin { bins small={0}; bins medium={1}; bins large={2}; }
  cp_l:    coverpoint lock_ok { bins ok={1}; bins fail={0}; }
  cx: cross cp_f, cp_step, cp_l;
endgroup
```

### 흔한 함정

- RNM-only로 jitter PASS 주장 금지 — Spice/스코프 영역
- Loop filter 1차 근사로 ringing/오버슈트 못 봄
- fractional spur는 RNM에서 안 나옴

---

## 2. ADC — Analog-to-Digital Converter

### Topology 종류

| 종류 | 속도 | 분해능 | 비고 |
|---|---|---|---|
| Flash | GS/s | 4~8 bit | 비교기 2^N개, 면적·전력 큼 |
| **SAR** | 10~100 MS/s | 10~16 bit | IoT/센서용 표준 |
| Pipeline | 100 MS/s~GS/s | 10~14 bit | stage별 SHA + flash |
| Sigma-Delta | kS/s~MS/s | 16~24 bit | oversampling + decimation |
| Integrating | 매우 느림 | 고정밀 | 정밀계측 |

### spec

| 항목 | 의미 | RNM |
|---|---|---|
| resolution N | 출력 비트 수 | O |
| Vref, full-scale | 입력 범위 | O |
| sample rate fs | 샘플링 주파수 | O |
| **INL · DNL** | code별 선형성 오차 | O (mismatch 주입 필요) |
| ENOB | effective number of bits | 제한 (noise 주입) |
| SNR · SNDR | 주파수 도메인 결과 | 제한 (FFT 후 계산) |
| offset · gain error | 전체 shift / scale | O |
| monotonicity | vin↑ → code↑ | O |
| latency | sample to code | O |

### 최소 RNM 모델

```systemverilog
module adc_rnm #(
  int  N        = 12,
  real VREF     = 1.8,
  real OFFSET   = 0.0,
  real GAIN_ERR = 0.0,
  real LSB_NOISE_LSB = 0.0
)(
  input  bit              clk,
  input  bit              start,
  input  wAnalog          vin,
  input  wAnalog          vref,
  output logic            eoc,
  output logic [N-1:0]    code
);
  real vsamp, noise; integer raw_code;
  always @(posedge clk) begin
    if (start) begin
      vsamp = vin.V + OFFSET;
      if (LSB_NOISE_LSB > 0.0) begin
        int n_int = $dist_normal(seed, 0, int'(LSB_NOISE_LSB * 1000));
        noise = real'(n_int) * (vref.V / (1<<N)) / 1000.0;
        vsamp = vsamp + noise;
      end
      vsamp = vsamp * (1.0 + GAIN_ERR);
      if      (vsamp <= 0.0)    raw_code = 0;
      else if (vsamp >= vref.V) raw_code = (1<<N) - 1;
      else                      raw_code = $rtoi(vsamp / vref.V * (1<<N) + 0.5);
      code <= raw_code[N-1:0];
      eoc  <= 1;
    end else eoc <= 0;
  end
endmodule
```

> OFFSET · GAIN_ERR · LSB_NOISE_LSB를 **parameter로 노출**해 한 모델로 ideal/realistic 양쪽 회귀가 가능하게. mismatch는 PVT corner index로 randomize, noise는 `noise_en` 모드로 토글.

### 검증 시나리오

- **DC sweep** — 0 → Vref 균등 step, 매 step에서 code 측정 → INL/DNL 후처리
- **Ramp test** — slow ramp. monotonicity 직접 관찰, missing code 검출
- **Sine input** — full-scale sine → FFT 후 SNR/SNDR/THD 계산
- **OOB inputs** — 음전압, Vref 초과: saturation, fault 신호
- **Vref 변화** — Vref drift 시 code shift, range 변화

### scoreboard

```systemverilog
// Ideal: ±1 LSB
expected = adc_ref(it.vin_volt, it.vref_volt, N);
assert ($abs(obs.code - expected) <= 1);

// monotonicity (run-aggregated)
foreach (codes[i]) if (i > 0)
  assert (codes[i] >= codes[i-1]) else `uvm_error("MONO", "non-monotonic")
```

### coverage

```systemverilog
covergroup cg_adc with function sample(int v_bin, int code, int pvt);
  cp_v: coverpoint v_bin {
    bins under={0}; bins low={[1:3]}; bins mid={[4:11]}; bins high={[12:14]}; bins over={15};
  }
  cp_c: coverpoint code {
    bins zero={0}; bins low={[1:(1<<10)-1]}; bins mid={[(1<<10):(1<<11)]};
    bins high={[(1<<11)+1:(1<<12)-2]}; bins fullscale={(1<<12)-1};
  }
  cp_pvt: coverpoint pvt { bins p[5] = {[0:4]}; }
  cx: cross cp_v, cp_c, cp_pvt;
endgroup
```

### 흔한 함정

- INL/DNL을 RNM ideal로만 보기 — mismatch 주입 없으면 항상 0
- `noise=0` default — ENOB가 ideal로 silicon과 큰 gap
- Vref drift 무시 — code가 영향 받지 않는다는 잘못된 가정
- FFT window — coherent sampling 아니면 spectral leakage로 SNR 오판

> RNM-only ENOB/SNR PASS 주장 금지. **RNM은 INL/DNL/missing code · monotonicity · latency만 자신감 있게 봅니다**. SNR/SNDR은 spec 한계의 ±20% sanity까지가 안전.

---

## 3. DAC — Digital-to-Analog Converter

### Topology

| 종류 | 속도 | 특징 |
|---|---|---|
| Current-steering | GS/s | RF/통신 |
| R-2R ladder | 중속 | 저렴, monotonicity 약점 |
| Binary-weighted | 중속 | 구조 단순, mismatch에 약함 |
| String / segmented | 중저속 | 본질적 monotonic, 면적 큼 |
| Sigma-Delta | audio | oversampling, noise shaping |

### spec

| 항목 | RNM |
|---|---|
| resolution N, full-scale range | O |
| **monotonicity, INL/DNL** | O (mismatch 주입) |
| settling time | 제한 (1차 RC 근사) |
| **glitch energy (major-carry)** | X (Spice) |
| output impedance | O (nettype Z) |
| SFDR | X (Spice) |

### 최소 RNM 모델 (안전 패턴 — 명시적 step)

```systemverilog
module dac_rnm #(
  int  N        = 10,
  real VMIN     = 0.0,  real VMAX = 1.8,
  real TAU_NS   = 5.0,
  real GAIN_ERR = 0.0,  real OFFSET = 0.0,
  real Z_OUT    = 50.0
)(
  input  bit              clk,
  input  logic [N-1:0]    code,
  output wAnalog          vout
);
  real target, current; analog_t drv;
  initial begin current = VMIN; drv.I=0.0; drv.Z=Z_OUT; end

  always @(code) begin
    real ideal = VMIN + (VMAX-VMIN) * real'(code) / real'((1<<N)-1);
    target = OFFSET + ideal * (1.0 + GAIN_ERR);
    fork settle_proc(target); join_none
  end

  task automatic settle_proc(real new_target);
    real v0 = current;
    for (int i = 1; i <= 200; i++) begin
      real t = i * 0.1;
      current = new_target - (new_target - v0) * $exp(-t / TAU_NS);
      drv.V = current; vout = drv;
      #(0.1 * 1ns);
    end
  endtask
endmodule
```

### 검증 시나리오

- **Full sweep** — 0 → 2^N-1 + monotonic check + INL/DNL 후처리
- **Code step** — 큰 step (midcode jump) settling 시간 측정
- **Major-carry transition** — MSB toggle worst-case glitch (Spice 권장)
- **Update rate** — fast update vs slow update — 출력이 따라잡는지
- **Load variation** — Z_OUT 작용

### scoreboard

```systemverilog
real expected_v = VMIN + (VMAX - VMIN) * real'(it.code) / real'((1<<N)-1);
expected_v += OFFSET; expected_v *= (1.0 + GAIN_ERR);
assert (`REAL_EQ(obs.v_settled, expected_v, 0.5 * LSB));

assert ((obs.t_settled - it.t_code_change) <= spec.t_settle_max);
assert (obs.dnl_min >= -0.5);   // DNL ≥ -0.5 LSB
```

### coverage

```systemverilog
covergroup cg_dac with function sample(int code, int step_size, int pvt);
  cp_c: coverpoint code {
    bins zero={0}; bins low={[1:(1<<8)]};
    bins mid_carry={(1<<(N-1))-1, (1<<(N-1))};      // major-carry boundary
    bins high={[(1<<8)+1:(1<<N)-2]}; bins fullscale={(1<<N)-1};
  }
  cp_step: coverpoint step_size {
    bins lsb={1}; bins mid={[2:(1<<(N-2))]}; bins large={[(1<<(N-2))+1:(1<<N)]};
  }
  cp_pvt: coverpoint pvt { bins p[5] = {[0:4]}; }
  cx: cross cp_c, cp_step, cp_pvt;
endgroup
```

### 흔한 함정

- 1차 RC settling 모델로는 ringing/오버슈트 못 봄
- glitch energy는 RNM에서 거의 0 → major-carry glitch는 Spice
- ideal RNM은 자동 monotonic — mismatch 주입 없이 PASS면 실위험 못 잡음
- Z_OUT vs Z_load 분압 무시하면 실제 출력보다 큰 값으로 PASS

> DAC는 ADC의 짝이라 testbench 재사용성이 높습니다. **같은 reference 함수 (code ↔ V) 한 곳**에 정의하면 ADC도 DAC도 사용 가능. 양방향 loop test (DAC → analog → ADC → code)도 흔한 검증 흐름.

---

## 4. LDO — Low-Dropout Regulator

```text
VIN ---> Pass FET ---+---> VOUT
              ^      |
              |      |  (feedback via R1/R2)
         Error Amp <-+
              ^
              | VREF (bandgap)
   feedback: VOUT * R2/(R1+R2) = VREF
```

### spec

| 항목 | RNM |
|---|---|
| VOUT nominal, dropout | O |
| line/load regulation | O |
| **PSRR** | X (Spice) |
| **output noise** | X (수동 주입만) |
| startup time, UVLO | O |
| quiescent current | O (model param) |
| load step (overshoot/undershoot) | 제한 (loop model) |

### 최소 RNM 모델

```systemverilog
module ldo_rnm #(
  real VOUT_NOMINAL = 1.2,
  real DROPOUT      = 0.20,
  real LINE_REG_PCT = 0.001,
  real LOAD_REG_PCT = 0.002,
  real TAU_NS       = 100.0,
  real Z_OUT        = 0.05,
  real UVLO_VIN     = 1.4
)(
  input  bit       en,
  input  wSupply   vin,
  output wSupply   vout
);
  real target, current; bit active; supply_t drv;
  initial begin current = 0.0; drv.valid = 0; end

  always @(*) begin
    if (!en || vin.V < UVLO_VIN) begin
      target = 0.0; active = 0;
    end else if (vin.V < VOUT_NOMINAL + DROPOUT) begin
      target = vin.V - DROPOUT;            // dropout 영역
      active = 1;
    end else begin
      target = VOUT_NOMINAL + LINE_REG_PCT * (vin.V - (VOUT_NOMINAL + DROPOUT)) * VOUT_NOMINAL;
      active = 1;
    end
  end

  initial forever begin
    real dt = 0.5, v0 = current;
    current = target + (v0 - target) * $exp(-dt / TAU_NS);
    drv.V = current; drv.valid = active; vout = drv;
    #(dt * 1ns);
  end
endmodule
```

### 검증 시나리오

- **Startup** — en=0 → en=1, 0 → nominal 도달 시간, inrush
- **Line regulation** — VIN ±20% slow ramp, VOUT 변화량
- **Load step** — I_load 0→max 급변, undershoot/overshoot/recovery
- **Dropout** — VIN을 nominal+dropout 아래로, 회복
- **UVLO** — VIN을 UVLO 아래로 → disable, latch/auto-enable

### scoreboard

```systemverilog
if (en && vin.V > VOUT_NOMINAL + DROPOUT) begin
  expected = VOUT_NOMINAL + LINE_REG_PCT * (vin.V - threshold) * VOUT_NOMINAL;
  assert (`REAL_EQ(vout.V, expected, 0.005));   // ±5 mV
end

assert property (@(posedge clk)
  (vin.V < UVLO_VIN) |-> ##[1:10] (vout.valid == 0));

assert ((t_settled - t_enable) <= spec.t_startup_max);
```

### coverage

```systemverilog
covergroup cg_ldo with function sample(int vin_bin, int iload_bin, int mode);
  cp_vin: coverpoint vin_bin {
    bins uvlo={0}; bins dropout={1}; bins low_reg={2}; bins nominal={3}; bins high={4};
  }
  cp_iload: coverpoint iload_bin {
    bins idle={0}; bins light={1}; bins normal={2}; bins heavy={3}; bins step={4};
  }
  cp_mode: coverpoint mode { bins on={1}; bins off={0}; }
  cx: cross cp_vin, cp_iload, cp_mode;
endgroup
```

### 흔한 함정

- PSRR/noise 정량 — RNM에서 의미 없음, Spice/measurement 영역
- 1차 모델로 load step overshoot 안 보임
- UVLO hysteresis 누락 → silicon oscillation
- Z_OUT=0 가정 → load resolution 잘못 합성

> LDO 회귀 PASS는 **regulation + startup + UVLO 동작**까지로 제한적 해석. PSRR · noise · transient overshoot 정량은 RNM 밖.

---

## 5. Bandgap Reference

SoC 전체의 reference voltage(보통 1.2 V 근처). CTAT(V_BE)와 PTAT(ΔV_BE)를 적절히 합쳐 온도/공급에 거의 independent. TC typical 20~50 ppm/°C.

```text
V_BE  (CTAT, ~-2 mV/C) ---+
                          +---> K1*V_BE + K2*dV_BE 가 TC=0
dV_BE (PTAT, ~+0.085 mV/C * ln(N)) ---+
```

### spec

| 항목 | RNM |
|---|---|
| V_REF nominal (1.20~1.25 V) | O |
| TC (ppm/°C) | O (T-dependent 모델) |
| line sensitivity | O |
| startup time | O |
| **dead-state stuck at 0 V** | O (FSM/latch 모델) |
| **output noise** | X (수동 주입) |
| trim range | O (trim code) |

### 최소 RNM 모델 — temperature-aware

```systemverilog
module bandgap_rnm #(
  real V_NOMINAL = 1.205,
  real TC_PPM    = 30.0,
  real LINE_SENS = 0.001,
  real TAU_NS    = 200.0,
  real UVLO_VDD  = 1.5,
  int  TRIM_BITS = 5
)(
  input  bit              en,
  input  real             T_celsius,
  input  wSupply          vdd,
  input  logic [TRIM_BITS-1:0] trim,
  output wAnalog          vref
);
  real target, current, trim_offset; bit active; analog_t drv;
  initial begin current = 0.0; drv.I = 0.0; drv.Z = 1e3; end

  always @(trim) begin
    int signed_trim = $signed({1'b0, trim}) - (1<<(TRIM_BITS-1));
    trim_offset = real'(signed_trim) * 0.0005;     // ±~8 mV
  end

  always @(*) begin
    if (!en || vdd.V < UVLO_VDD) begin target=0.0; active=0; end
    else begin
      target = V_NOMINAL * (1.0 + TC_PPM * 1e-6 * (T_celsius - 25.0))
             + LINE_SENS * (vdd.V - 1.8) * V_NOMINAL
             + trim_offset;
      active = 1;
    end
  end

  initial forever begin
    real dt = 1.0, v0 = current;
    current = target + (v0 - target) * $exp(-dt / TAU_NS);
    drv.V = current; vref = drv;
    #(dt * 1ns);
  end
endmodule
```

### dead-state stuck 모델 — startup assertion

```systemverilog
// 일부 회귀에서 random small offset 주입
initial seed_v = real'($urandom_range(0, 100)) / 1000.0;
// startup pulse가 없으면 0에 stuck

property p_startup;
  @(posedge clk) disable iff (!en)
    ##[1:1000] (vref.V > 0.8 * V_NOMINAL);   // 1 us 안에 80% 도달
endproperty
assert property (p_startup) else $error("bandgap stuck at startup");
```

> RNM은 본질적으로 deterministic이라 dead-state stuck이 잘 안 나옵니다. 검증 의미를 살리려면 일부 회귀에서 **startup 시 random offset / weak kick**을 명시적으로 주입하고 startup assertion으로 catch.

### 검증 시나리오

- **Temperature sweep** — T = -40 ~ 125 °C, V_REF curve, TC 계산
- **VDD sweep** — VDD nominal ±20%, line sensitivity 측정
- **Startup** — cold start, settled 도달, stuck 검출
- **Trim sweep** — trim code 0 ~ max, V_REF 변화
- **UVLO** — VDD를 UVLO 아래로, 복귀 시 restart

### coverage

```systemverilog
covergroup cg_bg with function sample(int t_bin, int v_bin, int trim_bin);
  cp_t:    coverpoint t_bin    { bins cold={[-40:-20]}; bins room={[-19:60]}; bins hot={[61:125]}; }
  cp_v:    coverpoint v_bin    { bins uvlo={0}; bins low={1}; bins nominal={2}; bins high={3}; }
  cp_trim: coverpoint trim_bin { bins neg_max={0}; bins mid={[1:14]}; bins pos_max={31}; }
  cx: cross cp_t, cp_v, cp_trim;
endgroup
```

### 흔한 함정

- RNM은 항상 startup 성공 — random seed-driven startup 모델 필요
- noise floor 무시 → ADC ENOB 보장 못 함
- 온도 입력 step — silicon 시간 상수 매우 길지만 RNM은 즉시
- trim code monotonicity — 직접 sweep test 필요

> Bandgap은 SoC의 모든 analog가 의존하는 root reference. **한 chip에 보통 한두 개**, 그 안정성이 전체 검증 신뢰도를 좌우합니다. `T_celsius`·`VDD` 두 knob을 **모든 IP env의 공통 config**로 두면 chip-level corner regression이 통일됩니다.

---

## 6. PMU — Power Management Unit

여러 supply rail을 **올바른 순서로** 켜고 끄는 책임. 잘못된 sequencing은 latch-up, ESD-like stress, signal mismatch를 일으키고, **silicon에 박히면 fix 거의 불가**.

### spec

| 항목 | RNM |
|---|---|
| sequencing order, inter-rail delay | O |
| UVLO/OVP threshold | O |
| power_good combo | O |
| fault response (retry/latch/shutdown) | O |
| **SMPS ripple** | X (Spice) |
| thermal shutdown | O (T 입력) |

### 모델 구조

PMU는 보통 **FSM + monitor + LDO/SMPS 인스턴스 묶음**. analog 자체는 LDO RNM 모델 재사용, sequencer FSM은 SV/RTL 또는 behavioral.

```systemverilog
module pmu_rnm (
  input  bit       en,
  input  wSupply   vin,
  input  real      T_celsius,
  output wSupply   vdd_core, vdd_io, vdd_pll,
  output bit       pg_chip,
  output bit       fault
);
  ldo_rnm #(.VOUT_NOMINAL(0.85), .UVLO_VIN(1.4)) u_core (.en(en_core), .vin(vin), .vout(vdd_core));
  ldo_rnm #(.VOUT_NOMINAL(1.80), .UVLO_VIN(2.0)) u_io   (.en(en_io),   .vin(vin), .vout(vdd_io));
  ldo_rnm #(.VOUT_NOMINAL(1.20), .UVLO_VIN(1.6)) u_pll  (.en(en_pll),  .vin(vin), .vout(vdd_pll));

  wire pg_core = vdd_core.valid && (vdd_core.V > 0.85*0.9);
  wire pg_io   = vdd_io.valid   && (vdd_io.V   > 1.80*0.9);
  wire pg_pll  = vdd_pll.valid  && (vdd_pll.V  > 1.20*0.9);

  typedef enum {S_OFF, S_IO, S_CORE, S_PLL, S_READY, S_FAULT} pmu_st_e;
  pmu_st_e st; realtime t_step;

  always @(posedge clk_pmu or negedge en) begin
    if (!en) begin st <= S_OFF; {en_io, en_core, en_pll} <= 0; end
    else case (st)
      S_OFF:   begin en_io   <= 1; st <= S_IO;   t_step <= $realtime; end
      S_IO:    if (pg_io   || ($realtime - t_step) > T_IO_TIMEOUT)
                 begin en_core <= 1; st <= S_CORE; t_step <= $realtime; end
      S_CORE:  if (pg_core || ($realtime - t_step) > T_CORE_TIMEOUT)
                 begin en_pll  <= 1; st <= S_PLL;  t_step <= $realtime; end
      S_PLL:   if (pg_pll) st <= S_READY;
      S_READY: if (!pg_io || !pg_core || !pg_pll) st <= S_FAULT;
      S_FAULT: ;        // latched
    endcase
  end

  assign pg_chip = (st == S_READY);
  assign fault   = (st == S_FAULT);
endmodule
```

### SVA — sequencing 강제

```systemverilog
// IO가 먼저 켜져야 CORE 켜진다
property p_io_before_core;
  @(posedge clk_pmu) $rose(en_core) |-> pg_io;
endproperty
assert property (p_io_before_core) else $error("CORE enabled without IO power-good");

// PG_chip은 모든 rail PG가 1일 때만
property p_pg_chip;
  @(posedge clk_pmu) pg_chip |-> (pg_io && pg_core && pg_pll);
endproperty
assert property (p_pg_chip);

// FAULT는 latch
property p_fault_latch;
  @(posedge clk_pmu) $rose(fault) |-> fault throughout (!reset[*1:$]);
endproperty
assert property (p_fault_latch);
```

### 검증 시나리오

- **Normal sequencing** — en=1 → 모든 rail spec 순서로 ON, PG_chip raise
- **Rail failure** — 한 rail timeout → FAULT latch
- **UVLO trip** — VIN을 UVLO 아래로 → rail disable → FAULT
- **Shutdown** — en=0 → 역순으로 OFF
- **Reset → retry** — FAULT 후 reset → 정상 재시작

### coverage

```systemverilog
covergroup cg_pmu_fsm with function sample(pmu_st_e st);
  cp: coverpoint st {
    bins normal_path     = (S_OFF => S_IO => S_CORE => S_PLL => S_READY);
    bins fault_from_io   = (S_IO   => S_FAULT);
    bins fault_from_core = (S_CORE => S_FAULT);
    bins fault_from_pll  = (S_PLL  => S_FAULT);
    bins ready_to_fault  = (S_READY => S_FAULT);
  }
endgroup
```

### 흔한 함정

- 동시 transition — 두 rail 동시 enable 시 resolution 비결정적
- FSM(cycle) ↔ analog(us) 시간 분리 — PG drop hysteresis 필요
- FAULT latch가 RNM에서 풀림 — reset 처리 모델링 주의
- 한 rail ripple이 다른 rail에 영향 — RNM 없음, Spice 영역

> PMU bug는 **tape-out 후 fix 거의 불가능**한 카테고리 (정확한 sequencing 위반 시 chip 파괴 가능). 항상 **conservative bias**로 — spec margin 좁히고, 모든 corner에서 timing/order 위반을 명시적 assertion으로 catch. functional pass ≠ silicon safety.

---

## 7. Sensors — Comparator · Temp Sensor · Oscillator

SoC에 산재한 작은 analog 블록. IP 단위로는 작지만 SoC 정합성에 영향 큼.

### 7.1 Comparator

```systemverilog
module comparator_rnm #(
  real V_TH     = 0.5,
  real V_HYST   = 0.01,
  real V_OFFSET = 0.0,
  real T_PROP   = 5.0    // ns
)(
  input  bit       en,
  input  wAnalog   vin,
  output logic     out
);
  bit  last; real eff_th;
  initial last = 0;

  always @(vin.V) begin
    if (!en) begin out <= 0; continue; end
    eff_th = V_TH + V_OFFSET + (last ? -V_HYST/2 : +V_HYST/2);
    if (vin.V > eff_th && !last) begin
      #(T_PROP * 1ns) out <= 1; last = 1;
    end else if (vin.V < eff_th && last) begin
      #(T_PROP * 1ns) out <= 0; last = 0;
    end
  end
endmodule
```

**시나리오**: threshold sweep, hysteresis up/down, propagation delay, enable toggle, noisy input chattering

### 7.2 Temperature Sensor

```systemverilog
module temp_sensor_rnm #(
  int  N         = 12,
  real GAIN      = 32.0,         // LSB/°C
  real OFFSET    = -40.0,
  real ACCURACY  = 2.0,          // ±2 °C
  real T_CONV_NS = 1_000_000.0   // 1 ms conversion
)(
  input  bit              start,
  input  real             T_celsius,
  output logic            eoc,
  output logic [N-1:0]    code
);
  int raw; real offset_err;
  initial offset_err = real'($urandom_range(0, 1000) - 500) / 1000.0 * ACCURACY;

  always @(posedge start) begin
    eoc <= 0;
    #(T_CONV_NS * 1ns);
    raw = $rtoi(GAIN * (T_celsius - OFFSET + offset_err) + 0.5);
    if (raw < 0) raw = 0;
    if (raw >= (1<<N)) raw = (1<<N) - 1;
    code <= raw; eoc <= 1;
  end
endmodule
```

**시나리오**: cold/room/hot sweep, linearity, conversion time, back-to-back, calibration trim

### 7.3 Oscillator (Ring / Crystal)

```systemverilog
module osc_rnm #(
  real F_NOMINAL       = 100e6,
  real TC_PPM_C        = 50.0,
  real V_SENS          = 0.001,
  real T_START_NS      = 10_000.0,
  real JITTER_SIGMA_PS = 5.0
)(
  input  bit       en,
  input  wSupply   vdd,
  input  real      T_celsius,
  output bit       clk_out
);
  real freq, period_ns; realtime t_en; bit started;
  initial begin started = 0; clk_out = 0; end

  always @(*) begin
    if (!en || !vdd.valid) freq = 0.0;
    else freq = F_NOMINAL * (1.0 + TC_PPM_C * 1e-6 * (T_celsius - 25.0))
                          * (1.0 + V_SENS   *       (vdd.V      - 1.8));
  end

  initial forever begin
    real f_eff;
    if (freq == 0.0) begin clk_out = 0; #1ns; continue; end
    if (!started) begin t_en = $realtime; started = 1; end
    f_eff = freq * (1.0 - $exp(-($realtime - t_en)/T_START_NS));
    period_ns = 1.0 / f_eff * 1e9;
    period_ns += real'($dist_normal(seed, 0, int'(JITTER_SIGMA_PS))) * 1e-3;
    #(period_ns * 0.5 * 1ns) clk_out = ~clk_out;
  end
endmodule
```

**시나리오**: frequency vs T sweep, startup time, VDD sweep, duty cycle, enable-disable 반복

### SoC 통합 시 정합성

- comparator → digital interrupt: chattering 없는 안정적 한 edge
- temp sensor → DVFS: temp 읽기 결과로 V/F 변경 트리거
- oscillator → PLL ref: startup 후 PLL 즉시 lock 시도하면 fail
- oscillator → watchdog: clock loss 검출, fallback

### 흔한 함정

- offset/mismatch 없는 RNM ideal로만 검증 → silicon spread 못 잡음
- comparator propagation delay 0 → IRQ race
- temp sensor 1 ms conversion을 실시간 시뮬 → 회귀 시간 폭발 (단축 옵션 필요)
- oscillator startup 즉시 stable 가정 → PLL이 비현실적으로 빨리 booting
- jitter Box-Muller seed를 driver와 공유 → 결정성 깨짐

> 작은 sensor류 IP는 검증 후순위가 되기 쉽지만 **SoC 정합성과 reliability의 단골 fail 카테고리**. spec ramp · mismatch · enable transition을 RNM에 명시적으로 넣고, SoC env 통합 직후 한 번 더 sanity sweep.

---

## 8. SerDes PHY

SerDes는 **analog signal integrity**(eye, jitter, equalization)와 **protocol**(link training)을 동시에 다룹니다. protocol은 RNM/UVM과 잘 맞지만 signal integrity는 **RNM의 한계가 매우 큰 영역**. spec PASS는 대부분 statistical sim + silicon measurement에 의존.

```d2
direction: down

g: {
  grid-rows: 4
  grid-gap: 50
  tx_side: "TX side"
  channel: "channel\n(diff pair, cable + PCB)"
  parallel_data: "parallel data\nencoder\n(8b/10b, 64b/66b)"
  ctle: "CTLE"
  ffe: "FFE"
  deser: "deser + CDR\ndecoder"
  rx_side: "RX side"
}

g.tx_side -> g.parallel_data
g.parallel_data -> g.ffe
g.ffe -> g.channel: "serial"
g.channel -> g.ctle
g.ctle -> g.deser
g.deser -> g.rx_side
```

### spec과 RNM 한계

| 항목 | RNM | 대안 |
|---|---|---|
| link training FSM | O | 그대로 검증 |
| polarity / lane reversal | O | OK |
| encoder/decoder (8b/10b) | O | OK |
| elastic buffer / clock comp | O | OK |
| CDR lock acquisition (functional) | 제한 | idealize: instant lock |
| **eye opening, BER** | X | statistical sim / scope |
| **RJ/DJ jitter** | X | statistical / Spice |
| FFE/CTLE/DFE 효과 | 제한 | S-parameter + statistical |
| crosstalk / coupling | X | EM simulation |

> SerDes 회귀의 PASS는 **protocol layer + lane management**까지로 명시적으로 제한. eye·jitter·BER PASS는 RNM 영역 밖. compliance test는 측정기 + scope + statistical 도구.

### protocol-level RNM (sweet spot)

PHY 검증 비중의 60~70%가 protocol/link training. analog는 ideal로 단순화하고 FSM·encoding·sync 집중.

```systemverilog
module serdes_tx_rnm (
  input  bit          clk_par,
  input  bit [9:0]    data_par,    // 8b/10b encoded
  output wAnalog      tx_p, tx_n
);
  bit serial; analog_t dp, dn;
  realtime tbit = 0.1ns;          // 10 Gbps = 100 ps UI
  initial begin dp.I=0.0; dp.Z=50.0; dn.I=0.0; dn.Z=50.0; end

  always @(posedge clk_par) begin
    for (int i = 9; i >= 0; i--) begin
      serial = data_par[i];
      dp.V = serial ? 0.6 : 0.4;   // ideal differential swing
      dn.V = serial ? 0.4 : 0.6;
      tx_p = dp; tx_n = dn;
      #tbit;
    end
  end
endmodule
```

### LTSSM / Training Sequence

PCIe LTSSM, USB LTSSM, SATA OOB 등 protocol 별 정해진 state machine. RNM에선 analog "ready" 신호를 ideal로 모델링.

```systemverilog
typedef enum {S_DETECT, S_POLLING, S_CONFIG, S_RECOVERY, S_L0, S_L0s, S_L1} ltssm_st_e;
ltssm_st_e st;
always @(posedge clk) case (st)
  S_DETECT:   if (rx_termination_ok) st <= S_POLLING;
  S_POLLING:  if (training_received)   st <= S_CONFIG;
  S_CONFIG:   if (config_complete)     st <= S_L0;
  S_L0:       if (recovery_trig) st <= S_RECOVERY;
              else if (l0s_trig) st <= S_L0s;
  S_RECOVERY: if (recovery_complete)   st <= S_L0;
  // ...
endcase
```

### protocol invariant SVA

```systemverilog
// S_L0 진입은 반드시 S_CONFIG 또는 S_RECOVERY 거쳐서만
property p_l0_from_config;
  @(posedge clk) $rose(st == S_L0) |-> $past(st) inside {S_CONFIG, S_RECOVERY};
endproperty
assert property (p_l0_from_config);

// DETECT 후 training 시도는 spec 시간 안
property p_detect_timeout;
  @(posedge clk) (st == S_DETECT) |-> ##[1:T_DETECT_MAX] (st != S_DETECT);
endproperty
```

### 검증 시나리오

- **Bring-up** — cold reset → link up → L0, timeout/retry
- **Polarity / lane swap** — PCB swap → PHY 자동 보정
- **Speed change** — Gen1 → Gen2 → Gen3, recovery
- **Lane width change** — x16 → x8 → x4 dynamic
- **Error injection** — encoder error, 8b/10b violation → decoder 검출, retry

### coverage

```systemverilog
covergroup cg_ltssm with function sample(ltssm_st_e st);
  cp: coverpoint st {
    bins detect_polling  = (S_DETECT  => S_POLLING);
    bins polling_config  = (S_POLLING => S_CONFIG);
    bins config_l0       = (S_CONFIG  => S_L0);
    bins l0_recovery     = (S_L0      => S_RECOVERY);
    bins l0_l0s          = (S_L0      => S_L0s);
    bins l0_l1           = (S_L0      => S_L1);
  }
endgroup
```

### signal integrity는 어떻게

eye·jitter·BER은 RNM 회귀로 PASS 주장 못 합니다. 실제 흐름:

- **IBIS-AMI / statistical** — TX/RX EQ를 statistical model로, channel response와 함께 eye opening 계산
- **Spice transient** — 특정 corner의 bit stream을 Spice transient로 → 직접 eye plot

### 흔한 함정

- "RNM에서 link up = 검증 끝" — protocol PASS는 SI PASS와 별개
- CDR ideal 가정 — RNM 회귀에선 항상 lock, lock failure는 별도 fault injection
- differential pair polarity 오모델 → common-mode 0 아님
- 8b/10b disparity — 인코더 bug 있어도 RNM PASS 가능, spec table-based unit test 필수
- elastic buffer overflow — rate mismatch 누적, long-run 시뮬에서만 드러남

> SerDes 검증은 **"무엇을 RNM에서 보고 무엇을 SI 도구에서 보는가"**를 처음부터 V-plan에 명시. 이 분리가 흐려지면 회귀 PASS의 신뢰 범위가 크게 잘못 해석됩니다.

---

## 참고: IP별 도구 매핑 요약

| IP | RNM 회귀 (nightly) | Spice corner | Statistical / EDA |
|---|---|---|---|
| PLL | functional lock, divider | jitter, phase noise | — |
| ADC | INL/DNL, monotonicity | ENOB, SNR Monte Carlo | — |
| DAC | settling, monotonicity | glitch, SFDR | — |
| LDO | regulation, UVLO | PSRR, transient overshoot, noise | — |
| Bandgap | TC, line, trim | dead-state, noise | — |
| PMU | sequencing, fault, PG | SMPS ripple | — |
| Sensors | functional, hysteresis | jitter, accuracy spread | — |
| SerDes | protocol, LTSSM | corner eye transient | IBIS-AMI, channel sim |

## 더 읽을거리

- Ch07: [DLL Deep Dive](07_deepdive_dll_rnm.md) — DLL의 phase detector·delay line·lock criteria
- Ch08: [IO Buffer Deep Dive](08_deepdive_io_buffer_rnm.md) — DDR PHY IO eye 모델
- Ch09: [Sense Amp Deep Dive](09_deepdive_sense_amp_offset.md) — DRAM sense amp Pelgrom Monte Carlo
- Ch12: [UVM × RNM Integration](12_uvm_rnm_integration.md) — env · agent · sequence · scoreboard
