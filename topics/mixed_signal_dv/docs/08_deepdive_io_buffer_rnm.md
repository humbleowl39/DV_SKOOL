# Ch08. Deep Dive — IO Buffer · IBIS-AMI

## 학습 목표

- **(Remember)** IO buffer의 5가지 핵심 특성(driver strength · slew · Z_out · ODT · ZQ cal)을 나열할 수 있다
- **(Understand)** Push-pull driver, termination, ZQ calibration의 동작 메커니즘을 설명할 수 있다
- **(Apply)** Driver strength · slew rate · ZQ cal · ODT를 RNM 코드로 구현할 수 있다
- **(Analyze)** Signal integrity 문제를 IO buffer 파라미터로부터 분석할 수 있다
- **(Evaluate)** ODT 설정과 IBIS-AMI 모델이 reflection·eye에 미치는 영향을 평가할 수 있다

## 1. IO Buffer가 왜 중요한가

**IO Buffer**: 칩 내부의 디지털 신호를 외부 PCB로 전송하거나, 외부 신호를 내부로 받아들이는 회로.

DRAM에서 특히 중요한 이유:

- DDR5 6400 Mbps/pin → 1 비트가 ~156 ps
- 신호가 PCB trace · package · 다른 chip을 거치며 왜곡됨
- Sense amp가 본 데이터는 깨끗했지만, IO buffer 거치며 변형되면 system error
- ZQ calibration, ODT 같은 동적 조정 필수
- DDR5/PCIe Gen5+ 이상은 **IBIS-AMI 모델로 RX equalizer까지 표준화**

## 2. IO Buffer의 5가지 특성

### 2.1 Driver Strength (구동 강도)

```
PMOS pull-up │ NMOS pull-down  →  output current
     W/L           W/L              ∝ transistor size
```

- 강한 driver: 빠른 천이, 큰 EMI
- 약한 driver: 느린 천이, 적은 EMI
- DDR5는 보통 **34Ω, 40Ω, 48Ω** 같이 임피던스 단위로 표현

### 2.2 Slew Rate Control

- dV/dt 제어
- 너무 빠르면 → ringing, crosstalk
- 너무 느리면 → eye 닫힘
- 보통 0.5 ~ 2 V/ns 범위 (DDR5+에서 더 빠름)

### 2.3 Output Impedance (Z_out)

- 50Ω, 40Ω, 34Ω 등
- PCB trace impedance와 매칭되어야 reflection 최소화

### 2.4 ODT (On-Die Termination)

- Receiver 쪽에서 적용
- 신호선 끝에 termination 저항 → reflection 흡수
- 60Ω, 80Ω, 120Ω, 240Ω 등 선택 가능

### 2.5 ZQ Calibration

- Driver/ODT 저항이 process/temp에 따라 변동
- 외부 정밀 저항(ZQ pin, 보통 240Ω)을 기준으로 internal R을 캘리브레이션
- 일반적으로 ZQCS (short) 매 128ms, ZQCL (long) 시동 시 + 정기적

## 3. IO Buffer 회로 구조

```
                          ┌── PMOS array ──┐  +VDDQ
                          │  W ratio: 1,2,4 │
                          │  digital select │
                          │                  │
        Internal data ────┤                  ├──── DQ pin
                          │                  │
                          │  NMOS array     │
                          │  W ratio: 1,2,4 │
                          └── NMOS array ──┘  -VSSQ
                                ▲
                                │
                          ┌─────┴────────┐
                          │ ZQ Cal       │
                          │ Controller   │
                          │ - up/down    │
                          │ - select     │
                          └──────────────┘
```

- Driver는 보통 여러 작은 transistor의 parallel 조합 (binary weighted)
- ZQ cal이 어떤 transistor를 켤지 선택
- 임피던스 = R_on (PMOS 또는 NMOS의 on resistance)

## 4. RNM 모델 — 기본 Push-Pull Driver

```systemverilog
`timescale 1ns/1ps

nettype real wreal;

module io_driver_rnm (
  input  logic data_in,
  input  logic oe,
  input  real  vddq,
  input  real  vssq,
  input  real  rdrv_pu_ohm,
  input  real  rdrv_pd_ohm,
  input  real  slew_rate_v_per_ns,
  output wreal dq_voltage,
  output real  i_load_a
);
  parameter real DQ_HIZ_VOLTAGE = 0.0;

  real v_drive_target;
  real v_drive;
  realtime last_time;

  always @(*) begin
    if (!oe)             v_drive_target = DQ_HIZ_VOLTAGE;
    else if (data_in)    v_drive_target = vddq;
    else                  v_drive_target = vssq;
  end

  initial begin
    v_drive   = (vddq + vssq) / 2;
    last_time = 0;
  end

  always @(v_drive_target) begin
    real dt_ns, dv, max_dv;
    dt_ns  = ($realtime - last_time) / 1e3; // ps → ns
    dv     = v_drive_target - v_drive;
    max_dv = slew_rate_v_per_ns * 0.05;     // 50ps step
    if (dv > max_dv)       v_drive = v_drive + max_dv;
    else if (dv < -max_dv) v_drive = v_drive - max_dv;
    else                    v_drive = v_drive_target;
    last_time = $realtime;
  end

  assign dq_voltage = v_drive;
  assign i_load_a   = 0;
endmodule
```

## 5. 더 정교한 Slew Rate 모델 (RC charging)

실제 IO buffer는 driver R + load C의 RC charging:

```
V(t) = V_target + (V_initial - V_target) × exp(-t/RC)
```

```systemverilog
module io_driver_rc_rnm(
  input  logic data,
  input  real  rdrv_ohm,
  input  real  c_load_ff,
  output real  vout
);
  parameter real VDDQ = 1.1;
  real v_target, v_start;
  real tau_ps;
  realtime t_start;

  always @(*) v_target = data ? VDDQ : 0.0;

  always @(v_target) begin
    v_start = vout;
    t_start = $realtime;
    tau_ps  = rdrv_ohm * c_load_ff * 1e-3;  // ohm × fF = ps
  end

  initial forever begin
    #10ps;
    if (tau_ps > 0) begin
      real dt_ps;
      dt_ps = ($realtime - t_start);
      vout  = v_target + (v_start - v_target) * $exp(-dt_ps/tau_ps);
    end
  end
endmodule
```

→ τ = RC가 작을수록 빠른 천이.

## 6. Transmission Line + Reflection

```
   Driver ──[R_drv]──┬──────[PCB trace]──────┬──[R_term]── Receiver
                     C_pkg_drv             C_pkg_rx
```

PCB trace는 transmission line으로 동작:

- Characteristic impedance Z0 (보통 50Ω)
- Propagation delay td (보통 6~7 ps/mm)
- 매칭 안 되면 reflection

### Reflection Coefficient

```
Γ = (R_load - Z0) / (R_load + Z0)
```

- R_load = Z0 → Γ = 0 (no reflection)
- R_load = ∞ (open) → Γ = +1 (full positive reflection)
- R_load = 0 (short) → Γ = -1 (full negative reflection)

### RNM 모델 (간략 단방향)

```systemverilog
module tline_rnm(
  input  wreal in_voltage,
  output wreal out_voltage
);
  parameter real Z0 = 50;
  parameter real TD_NS = 0.5;   // 500ps propagation
  parameter real R_TERM = 50;

  real gamma;
  initial gamma = (R_TERM - Z0) / (R_TERM + Z0);

  always @(in_voltage)
    out_voltage <= #(TD_NS * 1ns) in_voltage;
  // 정확한 reflection은 bidirectional + wave addition 필요 → IBIS-AMI
endmodule
```

## 7. ZQ Calibration RNM 모델

```systemverilog
module zq_cal_rnm (
  input  logic        clk,
  input  logic        zq_cal_start,
  input  real         r_external_ohm,    // 240Ω external precision R
  input  real         r_drv_unit_ohm,    // process variation 반영
  output logic [5:0]  pu_cal_code,
  output logic [5:0]  pd_cal_code,
  output logic        zq_done
);
  parameter real R_TARGET = 40.0;

  logic [5:0] code;
  real        r_actual;

  initial pu_cal_code = 6'h20;

  always @(posedge clk) begin
    if (zq_cal_start) begin
      // Pull-up code 증가시키면 R 감소
      r_actual = r_drv_unit_ohm * 64.0 / (code + 1);

      if (r_actual > r_external_ohm) begin
        if (code < 6'h3F) code <= code + 1;
      end else if (r_actual < r_external_ohm) begin
        if (code > 6'h00) code <= code - 1;
      end else begin
        zq_done <= 1;
      end

      pu_cal_code <= code;
    end
  end
endmodule
```

## 8. ODT (On-Die Termination) RNM 모델

```systemverilog
module odt_rnm (
  input  logic odt_en,
  input  real  r_odt_ohm,
  inout  wreal dq_voltage,
  output real  i_term_a
);
  parameter real VTT = 0.55;   // 보통 VDDQ/2

  always @(*) begin
    if (odt_en)
      i_term_a = (dq_voltage - VTT) / r_odt_ohm;
    else
      i_term_a = 0;
  end
endmodule
```

## 9. 대표 문제 — Driver + Termination Voltage 계산

### 문제

다음 조건에서 DQ pin의 정상상태 voltage를 계산:

- VDDQ = 1.1V, VSSQ = 0V
- Pull-up driver: 34Ω (data='1' 활성)
- ODT: 60Ω, termination voltage VTT = 0.55V
- PCB trace: 무시 (DC 상태)

### 풀이

```
VDDQ(1.1V) ──[R_pu=34Ω]── DQ ──[R_odt=60Ω]── VTT(0.55V)
```

KCL at DQ:

```
(VDDQ - V_DQ) / R_pu = (V_DQ - VTT) / R_odt
(1.1 - V_DQ) / 34 = (V_DQ - 0.55) / 60
60(1.1 - V_DQ) = 34(V_DQ - 0.55)
66 - 60·V_DQ = 34·V_DQ - 18.7
84.7 = 94·V_DQ
V_DQ ≈ 0.901 V
```

### 검증

- '1' 출력 시 V_DQ ≈ 0.90 V (이상적 1.1V 아님 — divider 효과)
- '0' 출력 시: VDDQ 대신 0V로 풀다운 → V_DQ ≈ 0.55 × 34/(34+60) ≈ 0.199V
- Swing = 0.90 - 0.20 = **0.70 V** (eye 높이)
- Receiver threshold = VTT (0.55V)
- 0.90 > 0.55 → '1' 검출 ✓
- 0.20 < 0.55 → '0' 검출 ✓

## 10. 대표 문제 — Eye Opening with Slew Rate

### 문제

Driver slew rate 1 V/ns, data rate 6.4 Gbps (UI = 156 ps)일 때 eye height는?

### 풀이

- 한 비트 시간 = 156 ps
- 천이에 필요한 시간 (full swing 0V → 1.1V) = 1.1V / 1 V/ns = **1.1 ns = 1100 ps**
- 한 비트 안에 천이 안 끝남 → eye = 0!

**Slew rate 3 V/ns 재계산**:

- 천이 시간 = 1.1 / 3 = 367 ps > 156 ps → 여전히 부족

**Slew rate 8 V/ns**:

- 천이 시간 = 1.1 / 8 = 138 ps < 156 ps ✓
- Settling 후 약간의 안정 시간

→ DDR5 6.4 Gbps급 IO는 **매우 빠른 slew rate** 필요.

## 11. IBIS-AMI — RX Equalization 표준 모델

DDR5/PCIe Gen5+ 같은 고속 인터페이스는 단순 driver/ODT 모델로 부족 → **IBIS-AMI** 표준이 RX equalizer까지 포함합니다.

### 11.1 IBIS-AMI는 무엇인가

**IBIS-AMI** = IBIS Algorithmic Model Interface. IBIS 5.0 (2008) 도입, **IBIS 7.0 (2019)** 에서 PAM modulation과 **back-channel link training** 지원 추가.

```
┌──────────────────────────────────────────────────────────────┐
│                  IBIS-AMI Simulation                          │
│                                                                │
│  ┌──────────┐   channel    ┌──────────┐                       │
│  │ TX AMI   │ ───────────→ │ RX AMI   │ → recovered data      │
│  │ - FFE    │   pulse      │ - CTLE   │                       │
│  │ - pre-em │   response   │ - DFE    │                       │
│  │          │              │ - AGC    │                       │
│  │          │              │ - CDR    │                       │
│  │          │ ←─────────── │          │                       │
│  │          │ back-channel │          │                       │
│  └──────────┘ (IBIS 7.0+)  └──────────┘                       │
└──────────────────────────────────────────────────────────────┘
```

### 11.2 핵심 알고리즘 (DDR5/PCIe Gen5+ RX)

| 알고리즘 | 역할 |
|---|---|
| **CTLE** (Continuous-Time Linear Equalization) | 채널 loss를 high-pass로 보상 |
| **FFE** (Feed-Forward Equalization) | TX에서 pre-emphasis로 ISI 사전 보상 |
| **DFE** (Decision-Feedback Equalization) | 결정된 비트를 feedback으로 ISI 제거 |
| **AGC** (Automatic Gain Control) | 입력 amplitude 일정하게 |
| **CDR** (Clock and Data Recovery) | 수신 데이터에서 clock 회복 |
| **Back-channel** (IBIS 7.0) | TX/RX 협상으로 link training |

### 11.3 RNM과의 관계

- IBIS-AMI는 **C/C++ DLL** + `.ami` 파일로 제공 → simulator(VCS, ADS, MATLAB SerDes Toolbox)가 호출
- RNM은 **자체 모델**, IBIS-AMI는 **표준 벤더 모델**
- 두 가지 흐름:
    1. 칩 설계 단계: RNM으로 자체 driver/RX 모델
    2. System 검증: IBIS-AMI로 PCB · package 채널 통합 분석

### 11.4 검증 시나리오 분담

| 검증 task | RNM | IBIS-AMI |
|---|---|---|
| 단일 비트 driver eye | ✓ | ✓ |
| Slew rate sensitivity | ✓ | △ |
| Channel 통과 후 eye (BER 1e-12) | ✗ | ✓ |
| RX equalizer 효과 | △ | ✓ |
| Back-channel training | ✗ | ✓ |

## 12. 변형 실습

1. 위 RNM driver/ODT 모델을 컴파일하고 시뮬레이션
2. **실습**: Slew rate를 1·3·8 V/ns로 변화시키며 eye height 측정
3. **실습**: ODT를 60·80·120Ω으로 변경하며 voltage swing 비교
4. **Challenge**: Pre-emphasis (high-freq boost) 추가
5. **Challenge**: 인접 line의 crosstalk RNM 모델

## 13. 흔한 함정

| 함정 | 설명 | 대응 |
|------|------|------|
| Driver impedance only | Load 무시한 voltage 계산 | KCL/Thevenin 풀이 |
| Slew rate 부족 | 1 V/ns로 6.4Gbps 시도 | UI 안에 천이 가능한지 확인 |
| ZQ cal 빈도 | Process drift 미반영 | Periodic recalibration |
| ODT를 driver와 별개 모델 | Voltage divider 효과 무시 | 함께 풀어야 |
| Single-ended vs differential | 모델 잘못 선택 | DDR은 DQ single, CK/DQS differential |
| IBIS-AMI 없이 BER sign-off | Statistical eye 불가 | IBIS-AMI + statistical method |

## 핵심 정리

1. IO buffer 5 특성: driver strength · slew · Z_out · ODT · ZQ cal
2. Voltage swing은 driver/ODT divider로 결정 — full VDDQ 아님
3. DDR5 6.4Gbps급은 slew rate ≥ 7~8 V/ns 필요
4. DDR5/PCIe Gen5+ RX는 **IBIS-AMI 표준 모델**로 검증 — CTLE/DFE/CDR + back-channel
5. RNM(설계 단계) + IBIS-AMI(system 검증) 조합이 산업 표준

## 더 읽을거리

- 다음: [Ch09. Deep Dive — Sense Amp Offset · Pelgrom · Monte Carlo](09_deepdive_sense_amp_offset.md)
- IBIS Open Forum: https://ibis.org
- JEDEC JESD79-5C (DDR5 IO)
- Howard Johnson, *High-Speed Digital Design*
- Eric Bogatin, *Signal and Power Integrity*
- Signal Integrity Journal: *"Back to Basics: IBIS/IBIS-AMI and the Path to (LP)DDR5"*
- 퀴즈: [Ch08 퀴즈](quiz/ch08_quiz.md)
