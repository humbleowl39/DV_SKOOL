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

## 핵심 정리

1. RNM 핵심: **digital simulator 안에서 real-valued 함수로 analog 동작 근사**
2. SV 도구: `real` (SV-2001) + `nettype` (SV-2012) + UDN/UDR (DVCon 패턴)
3. 5단계 정확도 — DRAM에서 Level 2~3 일반
4. Multi-driver는 **resolution function**으로 처리
5. UVM은 stimulus 재사용 가능. **모델링 자체는 새로 학습.**

## 더 읽을거리

- 다음: [Ch06. DRAM Read Path — 어떤 블록을 어떤 방법으로?](06_dram_read_path_partitioning.md)
- DVCon paper: *"Novel Mixed Signal Verification Methodology using complex UDNs"*
- DVCon paper: *"Enabling Digital Mixed-Signal Verification of Loading Effects in Power Regulation Using SystemVerilog User-Defined Nettypes"*
- DVCon paper: *"Harnessing SV-RNM Based Modelling and Simulation Methodology for Verifying a Complex PMIC designed for SSD Applications"*
- IEEE 1800-2017 § 6.6.7 — nettype
- 퀴즈: [Ch05 퀴즈](quiz/ch05_quiz.md)
