---
title: "Ch08. Deep Dive — IO Buffer · IBIS-AMI"
---

## 학습 목표

- **(Remember)** IO buffer의 5가지 핵심 특성(driver strength · slew · Z_out · ODT · ZQ cal)을 나열할 수 있다
- **(Understand)** Push-pull driver, termination, ZQ calibration의 동작 메커니즘을 설명할 수 있다
- **(Apply)** Driver strength · slew rate · ZQ cal · ODT를 RNM 코드로 구현할 수 있다
- **(Analyze)** Signal integrity 문제를 IO buffer 파라미터로부터 분석할 수 있다
- **(Evaluate)** ODT 설정과 IBIS-AMI 모델이 reflection·eye에 미치는 영향을 평가할 수 있다

## 1. IO Buffer가 왜 중요한가

**IO Buffer**는 칩 내부의 디지털 신호를 외부 **PCB**(Printed Circuit Board, 인쇄 회로 기판 — 칩들을 얹어 배선으로 잇는 보드)로 전송하거나, 외부 신호를 내부로 받아들이는 회로입니다.

DRAM 검증에서 IO buffer는 단순한 출력 드라이버 이상의 의미를 갖습니다. sense amplifier(미세 전압차를 0/1로 증폭하는 회로)까지는 완벽하게 데이터를 복원했어도, IO buffer를 거쳐 **PCB trace**(기판 위 신호 배선)와 package를 통과하는 과정에서 신호가 왜곡되면 결국 system error가 발생합니다. DDR5는 6400 Mbps/pin으로 동작하므로 1 비트의 시간이 약 156 ps밖에 되지 않습니다. 이 짧은 시간 안에 신호가 완전히 천이를 마쳐야 합니다. PCB trace는 **전송선(transmission line**, 길이가 신호 파장과 견줄 만해 전압이 시간뿐 아니라 위치에 따라서도 변하는 배선)으로 동작하기 때문에 임피던스 불일치가 있으면 **반사**(신호가 끝단에서 되튕겨 돌아오는 것)가 발생하고 **eye**(아이 다이어그램의 벌어진 정도)가 닫힙니다. ZQ calibration과 ODT 같은 동적 조정이 필수인 이유가 여기에 있습니다. DDR5와 PCIe Gen5+ 이상의 고속 인터페이스에서는 **IBIS-AMI 모델로 RX equalizer까지 표준화**되어 있어, 이 표준을 이해하지 못하면 system-level sign-off가 불가능합니다.

## 2. IO Buffer의 5가지 특성

IO buffer의 동작을 결정하는 다섯 가지 특성이 있습니다. 이것들이 서로 독립적이지 않고 함께 작용하므로, 하나씩 이해한 뒤 전체 그림을 보는 것이 중요합니다.

### 2.1 Driver Strength (구동 강도)

Driver strength는 **PMOS pull-up**(출력을 전원 쪽 1로 끌어올리는 p형 트랜지스터)과 **NMOS pull-down**(출력을 접지 쪽 0으로 끌어내리는 n형 트랜지스터) 트랜지스터의 크기로 결정됩니다. 트랜지스터가 클수록 **on-resistance**(켜졌을 때의 도통 저항)가 낮아 더 많은 전류를 흘릴 수 있고, 신호 천이가 빠릅니다. 그러나 전류가 크면 **EMI**(Electro-Magnetic Interference, 전자기 간섭 — 회로가 내뿜는 전자기 잡음)도 커집니다. DDR5에서는 트랜지스터 크기 대신 **34Ω, 40Ω, 48Ω** 같이 on-resistance의 임피던스로 강도를 표현합니다.

### 2.2 Slew Rate Control

Slew rate는 신호가 단위 시간당 얼마나 빠르게 전압을 변화시키는지(dV/dt)를 나타냅니다. 너무 빠르면 **ringing**(천이 후 전압이 목표값 주위로 출렁이는 것)과 **crosstalk**(옆 배선 신호가 결합해 생기는 간섭)이 심해지고, 너무 느리면 한 **UI**(Unit Interval, 한 비트가 차지하는 시간) 안에 천이를 마치지 못해 eye가 닫힙니다. DDR5+에서는 6400 Mbps 이상의 속도를 위해 슬루레이트를 매우 빠르게 설정해야 하는데, 이것이 **SI**(Signal Integrity, 신호가 왜곡 없이 전달되는 정도) 설계의 핵심 과제가 됩니다.

### 2.3 Output Impedance (Z_out)

출력 임피던스가 PCB trace의 특성 임피던스(보통 50Ω)와 매칭되어야 반사(reflection)가 최소화됩니다. 불일치가 있으면 신호가 끝단에서 반사되어 되돌아오고, 이것이 eye를 닫히게 합니다.

### 2.4 ODT (On-Die Termination)

수신 측에서 신호선 끝에 termination 저항을 칩 내부에 구현한 것이 ODT입니다. 외부에 종단 저항을 붙이는 대신 칩 안에서 처리하므로 시스템 설계가 단순해집니다. 60Ω, 80Ω, 120Ω, 240Ω 등을 선택할 수 있으며, 값에 따라 반사 억제 효과와 전력 소비가 달라집니다.

### 2.5 ZQ Calibration

Driver와 ODT의 저항값은 공정 변동과 온도에 따라 달라집니다. ZQ calibration은 외부 정밀 저항(ZQ pin, 보통 240Ω)을 기준으로 내부 저항을 보정하는 절차입니다. ZQCS(short) 캘리브레이션은 매 128ms마다, ZQCL(long)은 시동 시와 정기적으로 수행합니다. 이 캘리브레이션이 없으면 process/temperature corner에서 임피던스 매칭이 틀어져 signal integrity 마진이 줄어듭니다.

## 3. IO Buffer 회로 구조

```d2
direction: down

internal_data: "Internal data"
driver: "IO Driver" {
  pmos: "PMOS array\n(W ratio: 1,2,4)\n+VDDQ"
  nmos: "NMOS array\n(W ratio: 1,2,4)\n-VSSQ"
}
dq: "DQ pin"
zq_cal: "ZQ Cal Controller\n(up/down, select)"

internal_data -> driver
driver -> dq
zq_cal -> driver.nmos: "select"
```

- Driver는 보통 여러 작은 transistor의 parallel 조합 (**binary weighted** — 1·2·4·8…처럼 2의 거듭제곱 크기로 묶어 적은 비트로 넓은 범위를 조절)
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

- Characteristic impedance Z0 (특성 임피던스 — 전송선이 무한히 길 때 보이는 고유 임피던스, 보통 50Ω)
- Propagation delay td (신호가 배선 단위 길이를 지나는 데 걸리는 지연, 보통 6~7 ps/mm)
- 매칭 안 되면 reflection

### Reflection Coefficient

**반사 계수 Γ**(Gamma)는 끝단에서 얼마만큼이 되튕기는지를 나타내는 비율입니다.

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

ODT는 종단 저항을 **VTT**(Termination Voltage — 종단 저항이 연결되는 기준 전압, 보통 VDDQ의 절반)에 묶어 신호 반사를 흡수합니다. **VDDQ/VSSQ**는 IO 전용 전원/접지입니다.

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

**IBIS-AMI** = IBIS Algorithmic Model Interface (송수신단의 동작을 알고리즘으로 기술한 표준 SerDes 모델). IBIS 5.0 (2008) 도입, **IBIS 7.0 (2019)** 에서 **PAM**(Pulse Amplitude Modulation — 한 심볼에 여러 전압 레벨로 다중 비트를 싣는 변조) modulation과 **back-channel link training**(송수신단이 서로 신호를 주고받아 이퀄라이저 설정을 자동 최적화하는 협상) 지원 추가.

```d2
direction: down

ibis_sim: "IBIS-AMI Simulation" {
  tx: "TX AMI\n· FFE\n· pre-emphasis"
  rx: "RX AMI\n· CTLE\n· DFE\n· AGC\n· CDR"
  recovered: "recovered data"

  tx -> rx: "channel\n(pulse response)"
  rx -> tx: "back-channel\n(IBIS 7.0+)"
  rx -> recovered
}
```

### 11.2 핵심 알고리즘 (DDR5/PCIe Gen5+ RX)

| 알고리즘 | 역할 |
|---|---|
| **CTLE** (Continuous-Time Linear Equalization) | 채널 loss를 high-pass로 보상 |
| **FFE** (Feed-Forward Equalization) | TX에서 pre-emphasis(미리 고주파 성분을 키워 보내는 보정)로 ISI 사전 보상 |
| **DFE** (Decision-Feedback Equalization) | 결정된 비트를 feedback으로 ISI 제거 |
| **AGC** (Automatic Gain Control) | 입력 amplitude 일정하게 |
| **CDR** (Clock and Data Recovery) | 수신 데이터에서 clock 회복 |
| **Back-channel** (IBIS 7.0) | TX/RX 협상으로 link training |

### 11.3 RNM과의 관계

- IBIS-AMI는 **C/C++ DLL**(Dynamic-Link Library — 컴파일된 공유 코드 모듈; 여기서는 Ch07의 Delay-Locked Loop와 무관) + `.ami` 파일로 제공 → simulator(VCS, ADS, MATLAB SerDes Toolbox)가 호출
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
| Single-ended vs differential | 모델 잘못 선택 | DDR은 DQ single(한 선의 절대 전압으로 0/1), CK/DQS differential(두 선의 차이로 0/1 — 잡음에 강함) |
| IBIS-AMI 없이 BER sign-off | Statistical eye 불가 | IBIS-AMI + statistical method |

## 핵심 정리

1. IO buffer 5 특성: driver strength · slew · Z_out · ODT · ZQ cal
2. Voltage swing은 driver/ODT divider로 결정 — full VDDQ 아님
3. DDR5 6.4Gbps급은 slew rate ≥ 7~8 V/ns 필요
4. DDR5/PCIe Gen5+ RX는 **IBIS-AMI 표준 모델**로 검증 — CTLE/DFE/CDR + back-channel
5. RNM(설계 단계) + IBIS-AMI(system 검증) 조합이 산업 표준

## 더 읽을거리

- 다음: [Ch09. Deep Dive — Sense Amp Offset · Pelgrom · Monte Carlo](../09_deepdive_sense_amp_offset/)
- IBIS Open Forum: https://ibis.org
- JEDEC JESD79-5C (DDR5 IO)
- Howard Johnson, *High-Speed Digital Design*
- Eric Bogatin, *Signal and Power Integrity*
- Signal Integrity Journal: *"Back to Basics: IBIS/IBIS-AMI and the Path to (LP)DDR5"*
- 퀴즈: [Ch08 퀴즈](../quiz/ch08_quiz/)
