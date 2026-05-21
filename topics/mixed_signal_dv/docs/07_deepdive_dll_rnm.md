# Ch07. Deep Dive — DLL Real Number Modeling

## 학습 목표

- **(Remember)** DLL의 4가지 핵심 구성요소(PD · LF · DL · Replica)를 나열할 수 있다
- **(Understand)** DLL이 lock을 잡는 메커니즘과 PLL과의 차이를 설명할 수 있다
- **(Apply)** 각 블록을 RNM 코드로 작성하고 jitter를 주입할 수 있다
- **(Analyze)** Harmonic/false lock 진단 패턴을 분석할 수 있다
- **(Evaluate)** 주어진 DLL 사양에서 lock 시간·jitter spec 달성 가능 여부를 판단할 수 있다

## 1. DLL이란 무엇인가

**DLL (Delay-Locked Loop)** — 입력 클록(REF_CLK)과 출력 클록(OUT_CLK)의 **위상 차이를 0으로 유지**하기 위해, **가변 delay line**을 자동으로 조절하는 폐회로(feedback loop) 시스템.

PLL과의 차이:

| 항목 | PLL | DLL |
|---|---|---|
| 출력 클록 주파수 | 새로 생성 (VCO) | 입력 그대로 전달 |
| 위상 조절 수단 | VCO frequency | Variable delay line |
| 핵심 컴포넌트 | VCO + charge pump | Delay line + replica |
| Stability 분석 | Bode plot, loop gain | 단순 (대부분 first-order) |
| 적용 | Clock multiplication, RF | Phase alignment, clock deskew |

DRAM에서 DLL의 역할:

- DDR DRAM은 외부 CK 클록을 내부 데이터 출력 stage까지 전달
- 내부 buffer/wire delay로 인해 외부 CK와 내부 DQ 출력 사이에 phase shift 발생
- **DLL이 이 delay를 보상**하여 DQ가 CK 엣지에 정확히 정렬되게 함
- DDR5는 WCK + DLL 조합으로 더 정밀한 alignment

## 2. DLL의 4가지 구성요소

```
       REF_CLK ──┬──→ ┌─────────────┐  delay_clk  ┌──────────┐  OUT_CLK
                 │    │ Delay Line  ├─────────────┤ Replica  ├────┬──→
                 │    │ (variable)  │             │ Delay    │    │
                 │    └─────────────┘             └──────────┘    │
                 │           ▲                                     │
                 │           │ ctrl                                │
                 │     ┌─────┴──────┐                              │
                 │     │ Loop       │                              │
                 │     │ Filter     │                              │
                 │     └─────┬──────┘                              │
                 │           ▲                                     │
                 │           │ up/down                             │
                 │    ┌──────┴────────┐                            │
                 │    │ Phase         │                            │
                 └────┤ Detector (PD) ├←───────────────────────────┘
                      └───────────────┘    feedback
```

| 블록 | 역할 |
|------|------|
| **Phase Detector (PD)** | REF_CLK와 feedback CLK의 위상 차이 감지 → up/down 신호 |
| **Loop Filter (LF)** | up/down 신호를 누적하여 delay control 값 생성 |
| **Delay Line (DL)** | 입력 클록을 가변 시간만큼 지연 |
| **Replica Delay** | 실제 출력 경로의 delay를 모사 (feedback path) |

## 3. 동작 시나리오

1. **초기**: delay line의 delay 값이 임의 (예: 0)
2. PD가 REF_CLK와 feedback CLK 비교:
   - feedback이 REF보다 빠르면 → "delay 더 늘려라" (UP)
   - feedback이 REF보다 느리면 → "delay 줄여라" (DOWN)
3. Loop filter가 매 cycle마다 control 값을 증감
4. 결국 delay line의 총 delay = `1 period - replica delay` 에 수렴
5. **Lock**: 위상 차이가 충분히 작아지면 안정

## 4. RNM 모델 — 전체 구조

```systemverilog
`timescale 1ns/1ps

module dll_rnm #(
  parameter real PERIOD_NS    = 1.0,      // 1 GHz reference
  parameter real REPLICA_DELAY_NS = 0.2,
  parameter int  CTRL_BITS    = 8,
  parameter real DELAY_STEP_PS = 5.0      // 5ps per LSB
) (
  input  logic ref_clk,
  output logic out_clk,
  output logic locked
);
  // Internal
  logic [CTRL_BITS-1:0] ctrl;
  logic fb_clk;
  logic delay_clk;
  real  current_delay_ps;

  // 1) Delay line
  always @(*) current_delay_ps = ctrl * DELAY_STEP_PS;
  always @(ref_clk) delay_clk <= #(current_delay_ps * 1ps) ref_clk;

  // 2) Replica delay (output path 모사)
  always @(delay_clk) fb_clk <= #(REPLICA_DELAY_NS * 1ns) delay_clk;

  // out_clk = delay_clk
  assign out_clk = delay_clk;

  // 3) Phase Detector + Loop Filter
  realtime t_ref_rise, t_fb_rise;
  real     phase_err_ps;

  always @(posedge ref_clk) t_ref_rise = $realtime;
  always @(posedge fb_clk)  t_fb_rise  = $realtime;

  always @(posedge ref_clk) begin
    automatic real diff;
    diff = (t_fb_rise - t_ref_rise) * 1e3; // ns → ps
    // phase wrap-around 처리
    if (diff > PERIOD_NS * 500)  diff -= PERIOD_NS * 1e3;
    if (diff < -PERIOD_NS * 500) diff += PERIOD_NS * 1e3;

    phase_err_ps = diff;

    // 적분형 P-controller
    if (phase_err_ps > 0 && ctrl > 0)
      ctrl <= ctrl - 1;
    else if (phase_err_ps < 0 && ctrl < (1<<CTRL_BITS)-1)
      ctrl <= ctrl + 1;
  end

  // 4) Lock detector
  parameter real LOCK_THRESHOLD_PS = 10.0;
  integer lock_cnt;
  always @(posedge ref_clk) begin
    if (phase_err_ps > -LOCK_THRESHOLD_PS && phase_err_ps < LOCK_THRESHOLD_PS) begin
      if (lock_cnt < 16) lock_cnt <= lock_cnt + 1;
    end else
      lock_cnt <= 0;
  end
  assign locked = (lock_cnt >= 16);

endmodule
```

## 5. 각 블록의 RNM 모델링 세부

### 5.1 Phase Detector (PD)

```systemverilog
// Type 1: XOR-based PD
always @(ref_clk or fb_clk)
  pd_out = ref_clk ^ fb_clk;
// pd_out의 duty cycle이 phase error에 비례

// Type 2: Phase-Frequency Detector (PFD) — 더 정확
always @(posedge ref_clk) up <= 1;
always @(posedge fb_clk)  down <= 1;
always @(*) if (up && down) {up, down} = 0;
```

RNM에서는 더 추상화 가능:

```systemverilog
real phase_err_ps;  // 시간 차이를 실수로 직접 표현
```

### 5.2 Loop Filter

연속시간:

```
V_ctrl(s) = (1 + s/wz) / (s · C) × I_cp(s)
```

이산 RNM (PI controller):

```systemverilog
real v_ctrl;
real Kp = 0.01;    // proportional gain
real Ki = 0.001;   // integral gain
real err_int = 0;  // integral accumulator

always @(posedge ref_clk) begin
  err_int <= err_int + phase_err_ps;
  v_ctrl  <= Kp * phase_err_ps + Ki * err_int;
end
```

### 5.3 Delay Line

```systemverilog
real delay_ns;
always @(in_clk) out_clk <= #(delay_ns * 1ns) in_clk;
```

**주의**: SV의 `#delay`는 컴파일 타임에 결정되는 게 일반적. 런타임 가변 delay는 일부 simulator에서 문제 → 대안:

```systemverilog
logic delayed_clk;
realtime trigger_time;

always @(in_clk) begin
  trigger_time = $realtime + delay_ns;
  #(delay_ns * 1ns);
  if ($realtime == trigger_time) delayed_clk = in_clk;
end
```

### 5.4 Lock Detector

```systemverilog
integer consec_lock;
always @(posedge ref_clk) begin
  if (|phase_err_ps| < LOCK_TH) begin
    if (consec_lock < 16) consec_lock++;
  end else
    consec_lock = 0;
end
assign locked = (consec_lock >= 16);
```

## 6. Jitter 모델링

실제 DLL은 jitter(위상 노이즈)가 있습니다. RNM에서 추가:

```systemverilog
real jitter_sigma_ps = 2.0;  // 2 ps RMS
int  jitter_seed = 1;

always @(posedge ref_clk) begin
  automatic real jitter;
  jitter = $dist_normal(jitter_seed, 0, jitter_sigma_ps);
  out_clk_delayed = #(delay_ns * 1ns + jitter * 1ps) ref_clk;
end
```

Jitter 종류:

| 종류 | 원인 | RNM 모델링 |
|------|------|-----------|
| Random jitter (RJ) | Thermal noise | Gaussian random |
| Deterministic jitter (DJ) | Power supply, crosstalk | Sinusoidal 또는 periodic |
| Data-dependent jitter | ISI | 데이터 패턴 의존 |
| Duty cycle distortion (DCD) | Asymmetric rise/fall | Rise/fall delay 분리 |

## 7. Harmonic / False Lock — 산업의 실 문제

DLL이 가장 자주 fail 하는 mode: **harmonic lock** (한 cycle이 아닌 N cycle 거리에 lock) 및 **false lock**.

### 7.1 Harmonic Lock 메커니즘

```
REF: |---|---|---|---|---|
        T   2T  3T  4T

FB (잘못된 lock):
     |       |       |
       ↑       ↑       ← lock to 2T instead of T

OK lock:
     |   |   |   |   |
       ↑   ↑   ↑   ↑   ← lock to T (correct)
```

### 7.2 산업 표준 해결책 (USPTO 12316334, JSSC 1996 등 기반)

```
[Wide-range DLL의 lock 절차]
1. Initial delay = 최소값으로 시작 (start control circuit)
2. Coarse search: 큰 step (예: 50 ps)로 빠르게 근접
3. Fine adjust: 작은 step (예: 1 ps)로 정밀
4. Harmonic detector: REF/N 분주 클록 비교 → N=2,3 lock 감지
5. False lock 시 ctrl reset → restart from min delay
```

### 7.3 검증 시나리오

| Case | 초기 ctrl | 기대 lock | 검증 |
|------|---------|---------|------|
| Normal | mid | 1 cycle | RNM functional |
| Long delay path | high | 1 cycle (역방향 sweep) | RNM corner |
| Harmonic risk | very high | should not lock to 2T | RNM + harmonic detector |
| Power-on | random | safely converge | RNM with random init |

## 8. 대표 문제 — DLL Lock Behavior Dry-Run

### 문제

DLL 사양:

- REF_CLK: 1 ns 주기 (1 GHz)
- Replica delay: 0.2 ns
- 목표 = 1 - 0.2 = 0.8 ns
- 초기 delay: 0 ns
- Step: 5 ps/cycle
- Lock criterion: 16 consecutive cycles within ±10 ps

**(a)** Lock 도달 시간은? **(b)** Step을 1 ps로 줄이면? **(c)** Replica delay = 0.5 ns이면?

### 풀이

(a) 기본:

- 필요 step 수 = 800 / 5 = 160
- 1 cycle = 1 ns → 160 ns 후 도달
- + 16 cycle 안정 = 16 ns
- **총 ≈ 176 ns**

(b) Step 1 ps:

- 800 / 1 = 800 cycle = **816 ns**
- → 너무 느림. 실제로는 coarse + fine 2단계 lock 알고리즘 사용

(c) Replica 0.5 ns:

- 목표 = 1 - 0.5 = 0.5 ns
- 500 / 5 = 100 cycle = **116 ns**
- → Replica delay가 크면 lock 빠름 (필요 delay 작음)

### 통찰

- Lock 시간 = (목표 delay - 초기 delay) / step + 16 cycle
- DDR5처럼 PERIOD가 짧으면 (≤ 1 ns) replica delay 비율이 커서 ctrl saturation 위험
- 산업에서는 **coarse + fine** 또는 **binary search** 기반 lock 알고리즘이 일반적

## 9. Lock Failure 진단 시나리오

### 9.1 시나리오 1 — Ctrl 값 saturate

- 증상: ctrl이 max value (예: 255)에 도달했는데도 phase_err가 negative
- 원인: Delay line의 최대 delay < 필요 delay
- 해결: Delay line 단수 증가 또는 step 증가

### 9.2 시나리오 2 — Limit cycle oscillation

- 증상: ctrl이 두 값 사이를 계속 왔다갔다
- 원인: Step 크기가 너무 큼 → resolution 부족
- 해결: Dead zone 추가

```systemverilog
if (phase_err_ps > DEAD_ZONE && ctrl > 0)
  ctrl <= ctrl - 1;
else if (phase_err_ps < -DEAD_ZONE && ctrl < MAX)
  ctrl <= ctrl + 1;
// else: hold
```

### 9.3 시나리오 3 — Harmonic lock (false lock)

- 증상: 1 cycle 대신 2 cycle delay에 lock
- 원인: 초기 delay가 너무 커서 다음 cycle 엣지에 lock
- 해결:
  1. Start control circuit (initial delay = 최소값)
  2. Harmonic detector 추가 (분주 클록 비교)
  3. Coarse search 단계에서 큰 step으로 빠르게 통과

## 10. 검증 체크리스트

| Item | 검증 방법 | 패러다임 |
|------|---------|---------|
| Lock 시간 | sim에서 측정 | RNM |
| Lock accuracy (phase error) | scoreboard | RNM |
| Lock range (freq min/max) | sweep | RNM |
| Jitter spec | $dist_normal + 통계 | RNM |
| Harmonic lock 방지 | adversarial 초기 ctrl | RNM |
| Process corner | SS/FF | RNM corner + SPICE |
| Temperature drift | -40°C ~ 125°C | RNM + SPICE |
| Power supply noise | sinusoidal injection | RNM |

## 11. 흔한 함정

| 함정 | 설명 | 대응 |
|------|------|------|
| Phase wrap-around | -π~π 경계 처리 안 함 | 차이가 ±period/2 넘으면 wrap |
| Initial condition | ctrl 초기값 missing | initial block에서 명시 |
| Sampling timing | PD가 양 edge에 반응 vs posedge만 | 모델 명확화 |
| Replica delay 불일치 | 실제 output path와 다름 | Process/temp variation 반영 |
| Loop bandwidth | Filter 계수 부적절 | Bode plot 분석 |
| Harmonic lock 미검증 | 실리콘에서 fail | 의도적 worst-case sim |

## 핵심 정리

1. DLL = PD + LF + DL + Replica delay 4 블록
2. RNM으로 lock behavior · jitter · harmonic lock 검증 가능
3. Lock 시간 = (목표 - 초기) / step + 안정 cycle
4. 산업 실 문제: **harmonic lock** — start control + harmonic detector 필수
5. Sign-off는 SPICE corner — jitter accumulation, supply noise sensitivity

## 더 읽을거리

- 다음: [Ch08. Deep Dive — IO Buffer · IBIS-AMI](08_deepdive_io_buffer_rnm.md)
- Razavi, *Design of Analog CMOS Integrated Circuits*, Ch16 (PLL/DLL)
- Maneatis, *"Low-Jitter Process-Independent DLL and PLL Based on Self-Biased Techniques"*, JSSC 1996
- USPTO 12316334 — DLL harmonic lock detection
- JEDEC JESD79-4/5 — DDR4/5 DLL specs
- 퀴즈: [Ch07 퀴즈](quiz/ch07_quiz.md)
