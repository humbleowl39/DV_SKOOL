# Ch05. RNM with SystemVerilog — `nettype` · `real` · `wreal`

## 학습 목표

- **(Remember)** SV-2012의 `nettype` 키워드와 그 구성요소(데이터타입 + resolution function)를 진술할 수 있다
- **(Understand)** RNM 5단계 정확도 모델을 설명할 수 있다
- **(Apply)** 간단한 인버터와 DRAM cell을 RNM 코드로 작성할 수 있다
- **(Analyze)** UDN(User-Defined Nettype)이 multi-driver 상황에서 어떻게 동작하는지 분석할 수 있다
- **(Create)** charge sharing 같은 물리식을 RNM에 직접 매핑할 수 있다

## 1. RNM의 핵심 아이디어

> "Analog 동작을 SPICE로 풀지 말고, digital simulator 안에서 real-valued 함수로 근사하자."

```
[AMS]                              [RNM]

Digital sim                        Digital sim
    ↓                                  ↓
Connect module                     (no connect module needed)
    ↓                                  ↓
SPICE sim ← 느림                   Real-valued model in SV ← 빠름
    ↓                                  ↓
Transistor physics                 Behavioral approximation
```

## 2. RNM이 가능한 이유

- 디지털 시뮬레이터(VCS, Xcelium, Questa)도 **실수(real) 타입 지원** (SystemVerilog 표준)
- 신호값이 0/1이 아니라 0.0~0.9 같은 실수
- 시간은 여전히 **이벤트 기반** (수치적분 안 함) → **빠름**

DVCon 발표에 따르면 RNM 도입으로 **100~1000× 속도 향상**이 보고되었습니다 (PMIC SSD 사례, 2020).

## 3. `real` 데이터 타입 (SV-2001)

```systemverilog
real voltage;           // 실수 변수
real cap = 1.0e-15;     // 1 fF

initial begin
  voltage = 0.9;
  $display("Voltage = %0.3f V", voltage);  // 예제용 — 실 코드는 uvm_info 권장
end
```

- IEEE 754 double-precision
- 일반 변수처럼 사용 — `assign`, `always`, `function` 등 모두 가능
- 단, **net이 될 수 없음** → port 간 wire로 못 씀

## 4. `nettype` (SV-2012) — RNM의 핵심

`real`만으로는 net을 만들 수 없어 port 통신이 어려움 → `nettype`이 해결합니다.

### 4.1 기본 사용

```systemverilog
// 기본 정의
nettype real wreal;     // wreal 타입의 net은 real 값을 가짐

// 모듈에서 사용
module sense_amp(
  wreal bit_line_p,
  wreal bit_line_n,
  output logic data_out
);
  always @(*) begin
    data_out = (bit_line_p > bit_line_n) ? 1'b1 : 1'b0;
  end
endmodule
```

### 4.2 Resolution Function — 여러 driver 처리

같은 net에 여러 driver가 있으면? `nettype with resolution`:

```systemverilog
typedef struct packed {
  real voltage;
  real strength;
} drive_t;

// 가장 강한 driver 선택
function automatic drive_t resolve_max_strength(input drive_t drivers[]);
  drive_t result;
  result = drivers[0];
  foreach (drivers[i]) begin
    if (drivers[i].strength > result.strength)
      result = drivers[i];
  end
  return result;
endfunction

nettype drive_t wreal_resolved with resolve_max_strength;
```

→ 두 driver가 한 net에 동시에 값을 쓰면, `resolve_max_strength`가 호출되어 결합된 값을 net에 반영.

### 4.3 UDN — User-Defined Nettype 확장

DVCon (2020~2025) 사례들이 보여주는 활용:

- **EEnet (Cadence EE_pkg)**: `nettype` 안에 (voltage, impedance) 구조체 → 임피던스 인터랙션 모델링
- **Loading effects in power regulation**: structured UDN으로 multi-driver current/voltage summation
- **Scalable UVM-DMS**: 자동 type conversion + driver resolution

> **결론**: 단일 `wreal` (실수 한 개)로 부족한 상황(임피던스, current, drive strength)에서는 **구조체 UDN**으로 확장.

## 5. RNM 5단계 정확도 모델

복잡도를 어디까지 가져갈지 선택할 수 있습니다 — 같은 인버터:

| 단계 | 모델링 수준 | 속도 |
|------|----------|------|
| **Level 0** | 디지털 + delay만 (사실상 RNM 아님) | 매우 빠름 |
| **Level 1** | 실수값 출력 (high/low voltage 표현) | 빠름 |
| **Level 2** | + Ramp transition (rise/fall time) | 빠름 |
| **Level 3** | + Threshold, hysteresis, saturation | 중간 |
| **Level 4** | + Noise injection, jitter | 약간 느림 |
| **Level 5** | + Charge conservation (capacitance modeling) | 느림 |

DRAM 산업에서는 **Level 2~3** 일반. Critical block(sense amp 통계)만 Level 4~5 또는 SPICE.

## 6. RNM 모델 — CMOS 인버터 (Level 2)

```systemverilog
`timescale 1ns/1ps

nettype real wreal;

module inverter_rnm(
  input  wreal vin,
  output wreal vout
);
  parameter real VDD   = 0.9;
  parameter real VTH   = 0.45;    // switching threshold
  parameter real TPD   = 50.0;    // propagation delay (ps)
  parameter real TRISE = 30.0;    // rise time (ps)

  real vout_target;

  always @(vin) begin
    vout_target = (vin > VTH) ? 0.0 : VDD;
  end

  // Ramp transition (Level 2 RNM)
  assign #(TPD * 1ps) vout = vout_target;
endmodule
```

`always @(vin)`이 SV의 모범 아니라는 점에 주의 — 실제 사용 시 `wreal` 변화 trigger를 지원하는지 simulator 확인 필요. 대안: `always @(*)` + change detection.

## 7. 더 정밀한 RNM — DRAM Cell Charge Sharing (Level 5)

DRAM cell이 bit line으로 신호를 흘리는 동작:

```systemverilog
`timescale 1ns/1ps

nettype real wreal;

module dram_cell_rnm(
  input  logic     wl,         // word line
  inout  wreal     bl,         // bit line
  input  logic     wdata,      // data to store
  input  logic     we          // write enable
);
  parameter real C_CELL = 30.0e-15;    // 30 fF
  parameter real C_BL   = 100.0e-15;   // 100 fF (bit line cap)
  parameter real VDD    = 0.9;
  parameter real VPRE   = 0.45;        // precharge voltage

  real v_cell;    // 내부 cell capacitor voltage
  real bl_drive_voltage;

  // Write
  always @(posedge wl) begin
    if (we) v_cell = wdata ? VDD : 0.0;
  end

  // Read — charge sharing
  always @(posedge wl) begin
    automatic real q_cell, q_bl, v_shared;
    if (!we) begin
      q_cell    = C_CELL * v_cell;
      q_bl      = C_BL   * VPRE;
      v_shared  = (q_cell + q_bl) / (C_CELL + C_BL);

      bl_drive_voltage = v_shared;
      v_cell           = v_shared;  // destructive read
    end
  end

  assign bl = bl_drive_voltage;
endmodule
```

실제 DRAM의 charge sharing 물리를 그대로 SV로 옮긴 것:

```
v_shared = (Q_cell + Q_bl) / (C_cell + C_bl)
         = (C_cell·v_cell + C_bl·VPRE) / (C_cell + C_bl)
```

## 8. UVM 사용자에게 친숙한가?

| UVM에서 익숙한 것 | RNM에서 비슷한 것 / 차이 |
|------------------|-------------------------|
| `uvm_sequence_item` | 없음 — RNM은 RTL/behavioral level |
| `uvm_driver` | 자극 생성용 SV 모듈로 대체 (inline TB) |
| `class extends ...` | 사용 가능 (stimulus 측) |
| `logic` 타입 | **`real`과 공존** |
| `always @(posedge clk)` | **`always @(vin)` — 값 변화에 반응** |
| Constrained random | **여전히 사용 가능 (자극 측)** |
| Functional coverage | 사용 가능. voltage는 bin으로 매핑 필요 |
| Factory / config_db | 거의 사용 안 함 — parameter override 중심 |

> **결론**: UVM 경험이 stimulus·coverage 측에서는 활용 가능하나, **RNM 모델 작성 자체는 새로운 학습** 필요.

## 9. 대표 문제 — Charge Sharing 결과 예측 (Dry-Run)

### 문제

DRAM cell이 `'0'`(0V)을 저장하고 있을 때:

- C_cell = 30 fF
- C_bl = 100 fF
- BL precharge = 0.45 V
- WL 활성화 후 charge sharing 결과 BL voltage는?

### 풀이

```
q_cell = 30e-15 × 0 = 0 C
q_bl   = 100e-15 × 0.45 = 45e-15 C
v_shared = (0 + 45e-15) / (30 + 100) × 1e-15
         = 45 / 130
         ≈ 0.346 V
```

→ BL이 precharge(0.45V) 보다 약 0.104V 낮아짐 → sense amp가 '0' 검출.

### 검증

`'1'`(0.9V) 저장 시:

```
q_cell = 30e-15 × 0.9 = 27e-15 C
q_bl   = 45e-15 C
v_shared = (27 + 45)/130 = 0.554 V
```

→ BL이 0.554V로 precharge보다 0.104V 높음 → '1' 검출.

**Sense margin = ±0.104 V**. 이 margin이 sense amp offset(σ ≈ 18mV)보다 충분히 커야 함.

## 10. 흔한 함정

| 함정 | 결과 | 대응 |
|------|------|------|
| `wreal`에 X 할당 | NaN propagation | 명시적 default `0.0` |
| Resolution function 누락 | multi-driver short | `with` 절 명시 |
| `always @(real_var)` 미지원 simulator | trigger 안 됨 | `always_comb` + 비교 |
| `real` precision | 1e-30 같은 값 underflow | scale 조정 |
| Charge 보존 무시 | Destructive read 누락 | `v_cell = v_shared` 명시 |

## 11. UDN 사례 — 임피던스 인터랙션 (DVCon 패턴)

EEnet 스타일 UDN 예시:

```systemverilog
typedef struct packed {
  real voltage;
  real impedance;  // ohm. 작을수록 강한 driver
} ee_t;

function automatic ee_t resolve_parallel(input ee_t drivers[]);
  ee_t out;
  real g_sum = 0;
  real ig_sum = 0;
  foreach (drivers[i]) begin
    real g = 1.0 / drivers[i].impedance;
    g_sum  += g;
    ig_sum += drivers[i].voltage * g;
  end
  out.voltage   = ig_sum / g_sum;
  out.impedance = 1.0 / g_sum;
  return out;
endfunction

nettype ee_t eenet with resolve_parallel;
```

→ 두 driver가 parallel로 net을 구동하면 **Thevenin equivalent**를 자동 계산.

DVCon 2020/2021 발표에서 PMIC, power regulation, multi-supply switching 등에 활용.

## 12. real · shortreal · realtime — 세 실수 타입

analog 값을 담는 1차 도구. **전부 IEEE 754 부동소수점**이며 X/Z 상태가 없고, default는 `0.0`입니다. UVM/RNM 코드에서 99%는 `real` 한 가지만 쓰지만 세 타입의 차이는 알아둬야 합니다.

| 타입 | 크기 | 표현 범위 | 용도 |
|---|---|---|---|
| `real` | 64-bit (double) | ~±1.7e308, 15~17자리 | voltage, current, 시간 등 거의 모든 analog 변수 |
| `shortreal` | 32-bit (float) | ~±3.4e38, 7자리 | memory 절약이 critical할 때 — 거의 안 씀 |
| `realtime` | 64-bit (double과 동일) | real과 동일 | "시간 의미" 변수 — 가독성용 alias |

> `realtime`은 **의미적 alias**일 뿐 type checker가 시간/비시간을 구별하지 않습니다. 그래도 `realtime settle_time` vs `real voltage`처럼 코드 의도를 드러내는 데 도움이 됩니다.

### 12.1 선언과 default

```systemverilog
module rnm_signals;
  real    vdd;            // 초기값 0.0
  real    vin = 1.8;      // 명시적 초기화
  realtime t_lock;        // 시간 의미

  real    sample_buf[1024];   // 배열
  real    history[$];         // queue
  real    waveform[];         // dynamic array

  typedef struct { real V; real I; bit valid; } port_t;
  port_t pwr;                  // unpacked struct OK
  // typedef struct packed { real V; } bad_t;   // ❌ packed에는 real 못 들어감
endmodule
```

### 12.2 변환과 비트 재해석

```systemverilog
int  i;  real r;
r = real'(i);        // cast
i = $rtoi(r);        // truncate toward zero
i = $rtoi($floor(r));      // floor
i = $rtoi(r + (r >= 0 ? 0.5 : -0.5));   // round half away from zero

// 비트 패턴 재해석 (값 변환 아님)
bit [63:0] b;
b = $realtobits(r);
r = $bitstoreal(b);
```

### 12.3 내장 수학 함수

| 함수 | 의미 | 함수 | 의미 |
|---|---|---|---|
| `$abs(r)` | 절댓값 | `$sin/$cos/$tan(r)` | 삼각함수 (radian) |
| `$sqrt(r)` | 제곱근 (음수→NaN) | `$asin/$acos/$atan(r)` | 역삼각함수 |
| `$exp(r)` | e^r | `$atan2(y,x)` | 사분면 고려 atan |
| `$ln(r)` / `$log10(r)` | 자연/상용 로그 | `$sinh/$cosh/$tanh(r)` | 쌍곡함수 |
| `$pow(x,y)` | x^y | `$ceil/$floor(r)` | 상/하 정수 (반환 real) |
| `$hypot(x,y)` | sqrt(x²+y²) | | |

```systemverilog
// VCO 출력 주파수
real f_vco = f_center + Kvco * (vctrl - vmid);

// dB → linear gain
real gain_lin = $pow(10.0, gain_db / 20.0);

// Box-Muller 정규분포 noise
real u1 = $itor($urandom_range(1, 1<<30)) / (1<<30);
real u2 = $itor($urandom_range(0, 1<<30)) / (1<<30);
real n  = $sqrt(-2.0 * $ln(u1)) * $cos(2.0 * 3.141592653589793 * u2);
```

### 12.4 자주 놓치는 것

- **X 없음** — uninitialized는 `0.0`. false-pass 위험 (Ch10 함정 참고)
- **packed에 못 들어감** — register array는 unpacked로
- **`==` 금지** — 항상 tolerance 비교 (`$abs(a-b) <= eps`)
- **`%f`/`%g`/`%e` 정밀도** — default 6자리 부족할 수 있음, 명시적 폭 지정
- **NaN/Inf 전파** — `$sqrt(-1)` 같은 무효 연산이 silently NaN 전파, downstream 모두 false-pass 가능

```systemverilog
// NaN 방어 매크로
`define REAL_FINITE(x) (!$isunknown(x) && (x) == (x) && $abs(x) < 1e300)
```

## 13. nettype Resolution Function 심화

§4에서 본 기본을 넘어서, 실무에서 자주 쓰는 4가지 합성 패턴과 호출 규약을 정리합니다.

### 13.1 호출 규약

- simulator가 각 driver의 **현재 값**을 모아 unpacked array로 함수에 전달
- 한 driver만 있어도 **배열 길이 1**로 같은 함수 호출 (단순 pass-through 가능)
- driver 중 하나라도 값이 바뀌면 자동 재호출
- 함수는 반드시 `automatic` + side-effect 없어야 race-free
- 반환 타입 = nettype의 payload 타입

> 한 net에 **"이 driver는 지금 끄고 싶다"**를 표현하려면 high-impedance 값(`Z = ∞` 또는 매우 큰 수)으로 보내야 합니다. struct 안에 `bit drive_en`을 두고 resolution에서 걸러내는 패턴도 자주 씁니다.

### 13.2 네 가지 전형적 resolution 패턴

**① Thevenin (전압 합성)** — 전압 source가 임피던스 통해 한 net을 잡을 때. supply rail, bias 모델의 표준.

```systemverilog
function automatic analog_t res_thevenin(input analog_t d[]);
  real sum_VoZ = 0.0, sum_1oZ = 0.0;
  foreach (d[i]) if (d[i].Z > 0.0 && d[i].Z != `MAX_R) begin
    sum_VoZ += d[i].V / d[i].Z;
    sum_1oZ += 1.0     / d[i].Z;
  end
  if (sum_1oZ == 0.0) begin res_thevenin.V = 0.0; res_thevenin.Z = `MAX_R; end
  else                begin res_thevenin.V = sum_VoZ / sum_1oZ; res_thevenin.Z = 1.0 / sum_1oZ; end
  res_thevenin.I = 0.0;
endfunction
```

**② Norton (전류 합성)** — 전류 source들이 한 node에 들어올 때 (KCL). V = (ΣI) / (Σ1/Z), 정의역만 다릅니다.

**③ Wired-OR / Wired-AND** — open-drain · open-collector 모델.

```systemverilog
typedef struct { real V; bit pull_low; } od_t;
function automatic od_t res_od(input od_t d[]);
  res_od.V = 1.8; res_od.pull_low = 0;     // pull-up rail
  foreach (d[i]) if (d[i].pull_low) begin
    res_od.V = 0.0; res_od.pull_low = 1;
  end
endfunction
nettype od_t wOD with res_od;
```

**④ Custom** — 도메인 특수 합성 (예: thermal node sum, current limit). 직접 정의.

### 13.3 nettype 선언 위치와 가시성

- **package** 안에 정의 → import해서 어디서나 사용 (**권장**)
- module 안에 정의 → 그 module 내부에서만
- $unit (compilation unit) 안에 정의 → 한 파일 안에서만 (권장 안 함)

```systemverilog
package rnm_pkg;
  typedef struct { real V; real I; real Z; } analog_t;
  function automatic analog_t res_thevenin(input analog_t d[]); /* ... */ endfunction
  nettype analog_t wAnalog with res_thevenin;

  typedef struct { real V; bit valid; } supply_t;
  function automatic supply_t res_supply(input supply_t d[]); /* ... */ endfunction
  nettype supply_t wSupply with res_supply;
endpackage
```

> 한 IP의 모든 analog port에 **같은 nettype 한 종류만 쓰지 마세요**. supply, bias, signal은 의미가 달라 resolution도 달라야 합니다. 하나로 통일하면 false convergence가 발생합니다 (예: supply rail noise floor가 signal path에도 동일하게 합쳐짐).

### 13.4 vendor 호환성

- VCS / Xcelium / Questa 모두 SV-2012 nettype 지원
- struct payload 깊이/array가 깊으면 elaborate 시간이 길어지는 사례 보고
- resolution function이 무거우면 (loop iteration 큰 경우) 회귀 시간 영향 — branch 단순화, inline 권장
- nettype의 `chandle`, class instance payload는 vendor마다 지원 차이 — 호환성 가장 좋은 건 struct of real/int
- VAMS `wreal` ↔ nettype 자동 변환은 vendor-specific (보통 추가 directive 필요)

## 14. 시간 함수와 timeprecision

digital 검증은 cycle 단위 정수 시간으로 충분하지만 RNM에서는 **아날로그 ramp · settle · jitter** 같은 연속 시간 효과를 흉내내야 합니다. SV는 그 자리를 위해 `$realtime` · real delay · `$abstime`(VAMS)를 제공합니다. 선택과 단위 정밀도 관리를 잘못하면 simulation이 **silently 잘못된 시간 해상도**로 돕니다.

### 14.1 시간 시스템 함수 비교

| 함수 | 타입 | 단위 | 용도 |
|---|---|---|---|
| `$time` | 64-bit integer | 현재 `timeunit` | digital, log timestamp |
| `$stime` | 32-bit integer | 위와 동일 lower 32-bit | 거의 안 씀 |
| `$realtime` | real | 현재 `timeunit` (소수점) | **RNM의 표준 시간 변수** |
| `$abstime` | real | 초(seconds), 고정 | Verilog-AMS continuous 도메인 |

```systemverilog
// `timescale 1ns/1ps;
initial begin
  #1.5 $display("$time     = %0d",   $time);      // → 2 (반올림)
       $display("$realtime = %0.3f", $realtime);  // → 1.500
end
```

### 14.2 timeunit · timeprecision

한 모듈의 시간 해상도를 정하는 두 가지. RNM에서 **특히 timeprecision**이 ramp/jitter 해상도를 결정합니다.

```systemverilog
timeunit      1ns;        // 코드에 등장하는 #1 = 1ns
timeprecision 1ps;        // simulator 내부 해상도 = 1ps
// 또는 한 줄: `timescale 1ns/1ps
```

> PLL · ADC sample · jitter 검증을 **1ns 정밀도**로 돌리면 ps 단위 timing 효과가 silently round-off됩니다. mixed-signal env는 **timeprecision을 1ps 또는 더 작게** 잡는 것이 안전한 출발점입니다.

### 14.3 real delay와 연속 시간 흉내내기

```systemverilog
// real expression delay (SV-2005+)
real T_period = 1.0 / f_hz * 1e9;   // ns
realtime delay_ns = T_period / 2.0;
#(delay_ns) toggle = 1;

// 단위가 헷갈리면 literal time unit을 곱하라
real settle = 12.34;            // ns로 의도
#(settle * 1ns) done = 1;       // 어떤 timeunit이든 절대 12.34 ns 대기

// ramp · sine · exponential은 항상 이산 step의 합
task automatic ramp_linear(ref real sig, real V_target, real T_ns, int steps);
  real V0 = sig, dt = T_ns / steps, dv = (V_target - V0) / steps;
  for (int i = 1; i <= steps; i++) begin
    #(dt * 1ns);
    sig = V0 + dv * i;
  end
endtask

// 1차 LPF 응답 (지수 ramp): v(t) = V_target - (V_target - V0) * exp(-t/τ)
task automatic ramp_rc(ref real sig, real V_target, real tau_ns, real total_ns, int steps);
  real V0 = sig, dt = total_ns / steps;
  for (int i = 1; i <= steps; i++) begin
    real t = i * dt;
    #(dt * 1ns);
    sig = V_target - (V_target - V0) * $exp(-t / tau_ns);
  end
endtask
```

### 14.4 step 개수 결정 가이드

| 관심 효과 | 해상도 기준 | step 권장 |
|---|---|---|
| functional ramp (lock, settle) | spec 시간의 1% | 50~200 steps |
| sine zero-crossing 검출 | cycle 당 ≥ 100 step | 주기 / 0.5° |
| PLL jitter 정량 | jitter 단위의 1/10 | RNM 한계 — Spice 권장 |
| ADC sampling 시점 | 설계 sample 주기와 동기 | step ≤ Tsample/10 |

> step 수를 늘리면 정확도와 시뮬 시간이 함께 늘어납니다. **spec tolerance를 한 줄로 명시**하고 step 수가 그 tolerance를 만족하는 최소값임을 testbench 주석으로 기록하세요. 후임자가 step을 줄이며 false-pass를 만들기 쉽습니다.

### 14.5 시간 디버깅 팁

- log message에 항상 `%0t` 또는 `$realtime`을 같이 — race 분석의 첫 단서
- FSDB / VCD dump에 `real`도 포함되도록 dump 옵션 명시 (vendor마다 default 다름)
- 같은 시간에 여러 event가 발생할 때 NBA region과 `#0` 동작이 vendor마다 미묘 → race-sensitive 구간은 명시적 delay
- `$timeformat(-9, 3, " ns", 12)`로 출력 형식 통일

## 15. SVA on real — bound · slew · settle

SVA의 boolean expression은 임의의 SV expression이 올 수 있습니다. `real` 비교, `inside` range, 산술 결과 모두 가능 — analog spec("VDD는 0.95~1.05 V를 항상 만족", "slew는 1 V/μs 이하")을 SVA로 옮기는 것이 자연스럽습니다.

### 15.1 가장 단순한 bound check

```systemverilog
property p_supply_bound;
  @(posedge clk) disable iff (!por_n)
    vdd.V inside {[0.95 : 1.05]};
endproperty
assert property (p_supply_bound)
  else $error("[%0t] VDD = %0.3f out of [0.95,1.05]", $realtime, vdd.V);
```

`inside`의 range는 real에서도 동작 — 닫힌 구간 `[lo:hi]`로 양 끝 포함.

### 15.2 `$past`와 변화량

`$past(expr)` · `$stable(expr)`은 expression type을 보존합니다. real 값의 직전 sample을 가져와 slew rate · 변화량을 검증.

```systemverilog
// slew rate ≤ 1 V/μs (clk 주기 = 10 ns이라 가정)
// per-clk 변화량 한계 = 1 V/μs × 10 ns = 0.01 V
property p_slew;
  @(posedge clk) $abs(vsig.V - $past(vsig.V)) <= 0.01;
endproperty
assert property (p_slew);

// settling 완료 후 안정성: 변화량 < 1 mV가 100 cycle 유지
property p_settled;
  @(posedge clk) settled_flag |-> ($abs(vsig.V - $past(vsig.V)) < 1e-3 [*100]);
endproperty
```

### 15.3 `$rose`/`$fell`은 threshold를 거쳐 boolean으로

`$rose`·`$fell`은 **1-bit expression의 0→1/1→0**을 봅니다. real에 직접 못 쓰므로 threshold를 거쳐 boolean으로 변환.

```systemverilog
wire vsig_above = vsig.V > 0.9;

property p_crossing;
  @(posedge sample_clk) $rose(vsig_above) |-> done_flag within 1us;
endproperty
```

> **threshold를 wire/logic으로 미리 빼두는 것**이 RNM SVA의 가장 자주 쓰는 트릭. SVA 안에 비교식을 직접 쓰지 말고 별도 `wire`로 정의하면 wave dump에도 잘 잡혀 debug가 쉬워집니다.

### 15.4 tolerance 매크로 — scoreboard · SVA · log 일관성

```systemverilog
`define REAL_EQ(a, b, eps)   ($abs((a) - (b)) <= (eps))
`define REAL_LE(a, b, eps)   ((a) <= (b) + (eps))
`define REAL_GE(a, b, eps)   ((a) >= (b) - (eps))

property p_vref;
  @(posedge clk) `REAL_EQ(vref.V, 0.6, 5e-3);    // 600 mV ± 5 mV
endproperty
```

### 15.5 재사용 가능한 property 라이브러리

```systemverilog
property p_bounded (real lo, real hi);
  @(posedge clk) sig.V inside {[lo : hi]};
endproperty

property p_slew_le (real max_per_clk);
  @(posedge clk) $abs(sig.V - $past(sig.V)) <= max_per_clk;
endproperty

property p_settle (real target, real eps, int T);
  @(posedge clk) $fell(busy) |-> ##[1:T] `REAL_EQ(sig.V, target, eps);
endproperty

assert property (p_bounded(0.95, 1.05))   else $error("VDD bound");
assert property (p_slew_le(0.01))          else $error("slew");
assert property (p_settle(0.6, 5e-3, 200)) else $error("settle");
```

### 15.6 SVA에 넣지 말 것

- **긴 sequence 비교** — 100 sample 평균, FFT — SVA 안에 두면 디버깅 불가. scoreboard로
- **conditional 로직이 복잡** — implication 중첩보다 task/function이 가독성 우위
- **numerical accumulation** — RMS·평균·variance는 always 블록에서 계산하고 final value만 SVA로 체크

> SVA는 **local property**에 강합니다 — "이 시점에 이 조건". 시퀀스 누적 분석은 task/function에서 하고 결과만 SVA로 검증하세요. 섞으면 fail 시 어디서 깨졌는지 추적이 매우 어렵습니다.

### 15.7 cover property로 도달도 확인

```systemverilog
cover property (@(posedge clk) $rose(vsig.V > 1.0))
  $info("VSIG crossed 1.0 V");

cover property (@(posedge clk) (vin.V > 1.5) && (vin.V < 1.6))
  $info("VIN sampled in [1.5, 1.6]");
```

절대 도달 여부만 보고 충분 검증으로 해석하면 안 됩니다 — sanity check 용도.

## 16. Coverage on real — int 매핑이 핵심

`covergroup`의 `coverpoint`는 **정수 expression만** 받습니다. real 신호 그대로는 coverpoint가 될 수 없어 "어떻게 real을 정수 bin에 매핑할까"가 모든 작업의 첫 단계입니다. 매핑이 잘못되면 coverage 100%가 의미 없을 수 있습니다.

### 16.1 표준 패턴 — `sample()`에 real을 인자로

```systemverilog
covergroup cg_adc with function sample(real vin, int code);
  cp_vin: coverpoint vin {                      // simulator마다 real coverpoint 지원 다름
    bins low   = { [-0.10 : 0.30] };
    bins mid   = { [ 0.30 : 1.50] };
    bins high  = { [ 1.50 : 1.80] };
    bins over  = { [ 1.80 : 2.00] };
    illegal_bins extreme = { [-1.0:-0.10], [2.0:5.0] };
  }
  cp_code: coverpoint code {
    bins q[16] = { [0:4095] };
  }
  cx: cross cp_vin, cp_code;
endgroup

cg_adc cg = new();
always @(posedge sample_clk) cg.sample(vin.V, last_code);
```

> `sample(args)` 시그니처를 `function` 키워드로 정의하면 covergroup의 `coverpoint`가 **함수 인자**를 받습니다. 일반 variable이 아니라 매 sample 호출 인자가 bin을 결정 — race 없이 결정적.

### 16.2 호환성 안전 패턴 — int 변환

LRM은 정수 bin만 명시하므로 호환성을 위해 **real을 int로 미리 변환**하는 패턴이 안전합니다.

```systemverilog
function automatic int real_to_bin(real x, real lo, real hi, int N);
  int b;
  if (x <= lo) return 0;
  if (x >= hi) return N - 1;
  b = $rtoi((x - lo) / (hi - lo) * N);
  if (b < 0)  b = 0;
  if (b >= N) b = N - 1;
  return b;
endfunction

covergroup cg_vin with function sample(int b);
  cp: coverpoint b { bins all[16] = { [0:15] }; }
endgroup

always @(posedge sample_clk) cg.sample(real_to_bin(vin.V, 0.0, 1.8, 16));
```

### 16.3 의미 있는 binning — 균등 분할 ≠ 의미 있는 도달도

| 분할 방식 | 장점 | 위험 |
|---|---|---|
| 균등 N bin | 단순, 솔버 친화 | spec 경계 무시, 한 corner에만 hit 몰림 |
| **spec 경계 기반** | tape-out 위험 corner 직접 보임 | bin 수 늘어남, 솔버 hint 필요 |
| 로그 스케일 | 전류/이득 등 dynamic range 큰 변수 | 0 근처 처리, 단위 일관성 주의 |
| OOB illegal bin | spec 위반 즉시 fail 처리 | 잘 정의 안 하면 noise 한계까지 fail |

> spec 경계점을 bin edge에 두는 것이 의미 있는 coverage 정의의 기본.

### 16.4 transition / cross coverage

```systemverilog
covergroup cg_seq with function sample(int b);
  cp: coverpoint b {
    bins lo  = { 0 };
    bins mid = { [1 : 14] };
    bins hi  = { 15 };
    bins t_lo_mid = (lo  => mid);
    bins t_mid_hi = (mid => hi);
    bins t_round  = (lo  => mid => hi => mid => lo);   // 한 사이클
  }
endgroup

covergroup cg_pll_cal with function sample(int v_bin, int t_bin, int p_bin);
  cp_v: coverpoint v_bin { bins v[4] = { [0:3] }; }
  cp_t: coverpoint t_bin { bins t[3] = { [0:2] }; }
  cp_p: coverpoint p_bin { bins p[3] = { [0:2] }; }
  cx_pvt: cross cp_v, cp_t, cp_p {
    ignore_bins skip = binsof(cp_v) intersect {3}
                    && binsof(cp_t) intersect {[0:1]};
  }
endgroup
```

### 16.5 coverage anti-patterns

- **100%인데 무의미** — 16 bin에 hit 1 by 1. 솔버가 "한 번씩만" 채우고 끝. **transition · cross · sample count threshold**로 보완
- **noise 영역까지 100% 요구** — 솔버 시간 폭발. `illegal_bins` / `ignore_bins`로 명시
- **bin 경계 = spec 경계 아님** — 균등 분할이 1.0 V를 두 bin에 걸치면 "정확히 1.0 V"가 어떤 bin에도 우선 표시 안 됨

> mixed-signal coverage는 **도달도 정의에 검증 의도**가 따라야 합니다. "bin 16개 100%"가 spec의 어떤 위험을 막는지를 coverpoint 옆 주석으로 적어두세요 — coverage 정의 자체가 verification plan의 일부.

## 17. Randomization on real — int + post_randomize

IEEE 1800-2023부터 `rand real`이 LRM에 명시되긴 했지만, **simulator 지원과 솔버 한계** 때문에 표준 패턴은 `rand bit[N:0]` 또는 `rand int`를 뽑고 post-randomize로 real로 변환하는 것입니다.

| 접근 | 호환성 | 제약 표현력 | 비고 |
|---|---|---|---|
| `rand real` 직접 | simulator 의존, 제한적 | 한정 (linear 위주) | vendor 매뉴얼 확인 필수 |
| **`rand int` + 변환** | 전체 지원 | linear, range, weighted | **현실의 99%** |
| `$urandom` 후처리 | 전체 | constraint 없음 | 가장 단순, 코드 길어짐 |
| DPI random | 전체 | 임의 분포 | 외부 C 모델, debug 어려움 |

### 17.1 표준 패턴

```systemverilog
class adc_item extends uvm_sequence_item;
  rand int unsigned vin_code;        // 12-bit 입력 코드
  rand int unsigned settle_ns;

  real vin_volt;
  real settle_time;

  constraint c_range  { vin_code  inside { [0 : (1<<12)-1] }; }
  constraint c_settle { settle_ns inside { [10 : 1000] }; }
  constraint c_dist   {
    vin_code dist {
      [0 : 100]                  :/ 5,    // OOB lower
      [101 : (1<<12)-200]        :/ 80,   // normal range
      [(1<<12)-200 : (1<<12)-1]  :/ 15    // OOB upper
    };
  }

  function void post_randomize();
    vin_volt    = real'(vin_code) / (1<<12) * 1.8;
    settle_time = real'(settle_ns) * 1e-9;
  endfunction
endclass
```

> **resolution을 미리 정해 정수 비트 수로 표현**하는 것이 핵심. 12-bit = ~440 μV 해상도면 ADC 검증에 충분. 그 이상 필요하면 비트 수만 늘리면 됩니다 (16-bit, 24-bit). 솔버는 여전히 정수 CSP를 풀어 빠릅니다.

### 17.2 distribution — dist + post_randomize

```systemverilog
// 균등 + corner weighting
constraint c_typical {
  vin_code dist {
    0                       := 10,        // 정확히 0 (rail floor)
    [1 : (1<<12)-2]         :/ 80,        // 균등 분포
    (1<<12)-1               := 10         // saturation
  };
}

// 진짜 Gaussian은 dist로 못 표현 → post-randomize로
function void post_randomize();
  real u1 = real'($urandom_range(1, 1<<30)) / (1<<30);
  real u2 = real'($urandom_range(0, 1<<30)) / (1<<30);
  vin_code = 2048 + int'(400 * $sqrt(-2.0 * $ln(u1)) * $cos(2.0 * 3.141592653589793 * u2));
  if (vin_code < 0)         vin_code = 0;
  if (vin_code >= (1<<12))  vin_code = (1<<12) - 1;
  vin_volt = real'(vin_code) / (1<<12) * 1.8;
endfunction
```

### 17.3 의존 변수와 soft constraint

```systemverilog
class pll_test_item extends uvm_sequence_item;
  rand int          f_target_khz;
  rand int unsigned vctrl_code;

  constraint c_correlated {
    solve f_target_khz before vctrl_code;       // ordering hint
    if (f_target_khz < 500_000) vctrl_code inside { [0 : 1500] };
    else                        vctrl_code inside { [1500 : 4095] };
  }
endclass

// soft: default는 noise off, 특정 test에서만 override
class adc_item extends uvm_sequence_item;
  rand bit  noise_en;
  constraint c_noise_default { soft noise_en == 0; }
endclass
// noise_test: it.randomize() with { noise_en == 1; }
```

### 17.4 solver 친화 vs 의미

- **좁은 range 우선**: `inside`로 좁히면 솔버 빨라짐
- **dependent vars 명시**: `solve A before B`로 backtrack 줄임
- **complex constraint 분해**: 한 거대한 것보다 여러 작은 것으로
- **illegal 영역은 inside 음의**: `!(x inside {...})` 또는 분기 if

### 17.5 real randomization 시나리오

| 시나리오 | 패턴 |
|---|---|
| 입력 sweep | 12-bit 코드 → post_randomize에서 V로 |
| Corner sampling | PVT를 enum/int corner index로, model param을 후처리에서 set |
| Time-domain stim | freq · ampl · duty · jitter를 int로, sequence에서 sine 생성기에 전달 |
| Reference shift | Vref · bias를 randomize해서 calibration/trim 검증 |
| Mismatch 모델 | ADC LSB · offset · gain error를 정규분포로 후처리에서 부여 |

> **seed에 의존하지 않는 random은 functional pass 신뢰도가 낮습니다.** UVM regression에서 매 seed의 결과가 재현 가능해야 디버깅 가능 — `$random`을 직접 호출하지 말고 `uvm_root::get().set_seed()`를 통한 관리 권장.

## 핵심 정리

1. RNM 핵심: **digital simulator 안에서 real-valued 함수로 analog 동작 근사**
2. SV 도구: `real` (SV-2001) + `nettype` (SV-2012) + UDN/UDR (DVCon 패턴)
3. 5단계 정확도 — DRAM에서 Level 2~3 일반
4. Multi-driver는 **resolution function**으로 처리 (Thevenin / Norton / Wired-OR / Custom)
5. UVM은 stimulus 재사용 가능. **모델링 자체는 새로 학습**
6. **`==` 금지** — 항상 tolerance 비교. NaN 방어 `REAL_FINITE` 매크로
7. timeprecision은 ps 이하로 — 1ns 정밀도는 silently round-off
8. SVA on real: threshold는 wire로 미리 빼고, `$past`로 slew 검증, 누적 분석은 task/function으로
9. Coverage on real: real→int 변환 패턴이 vendor 호환성 표준. spec 경계가 bin edge
10. Randomization on real: `rand int` + `post_randomize`가 솔버·호환성 모두 유리

## 더 읽을거리

- 다음: [Ch06. DRAM Read Path — 어떤 블록을 어떤 방법으로?](06_dram_read_path_partitioning.md)
- DVCon paper: *"Novel Mixed Signal Verification Methodology using complex UDNs"*
- DVCon paper: *"Enabling Digital Mixed-Signal Verification of Loading Effects in Power Regulation Using SystemVerilog User-Defined Nettypes"*
- DVCon paper: *"Harnessing SV-RNM Based Modelling and Simulation Methodology for Verifying a Complex PMIC designed for SSD Applications"*
- IEEE 1800-2017 § 6.6.7 — nettype
- 퀴즈: [Ch05 퀴즈](quiz/ch05_quiz.md)
