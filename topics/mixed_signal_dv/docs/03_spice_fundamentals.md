# Ch03. SPICE / Fast SPICE 기초

## 학습 목표

- **(Remember)** SPICE가 푸는 기본 법칙(KCL, KVL, element law)을 진술할 수 있다
- **(Remember)** SPICE의 5가지 분석 종류(.op/.dc/.ac/.tran/.noise)를 나열할 수 있다
- **(Understand)** Newton-Raphson 반복법이 왜 필요한지 설명할 수 있다
- **(Apply)** 간단한 CMOS 인버터의 SPICE netlist를 작성할 수 있다
- **(Analyze)** Fast SPICE의 5가지 가속 기법이 어떻게 정확도를 trade-off 하는지 분석할 수 있다

## 1. SPICE는 무엇인가

**SPICE** = **S**imulation **P**rogram with **I**ntegrated **C**ircuit **E**mphasis

- 1973년 UC Berkeley의 Nagel이 박사학위 논문으로 개발 (BCSC ERL Memo, 1975)
- 전기 회로의 동작을 수치적으로 시뮬레이션하는 도구
- 모든 상용 SPICE (HSPICE, Spectre, FineSim, Eldo 등)는 원조 Berkeley SPICE의 후예

## 2. SPICE가 푸는 것 — 회로 = 노드 + 컴포넌트

### 2.1 기본 법칙

- **KCL (Kirchhoff's Current Law)**: 노드에 들어오는 전류의 합 = 나가는 전류의 합
- **KVL (Kirchhoff's Voltage Law)**: 폐회로에서 전압 강하의 합 = 0
- **Element law**: 각 컴포넌트의 V-I 관계
    - 저항: V = IR
    - 캐패시터: I = C·dV/dt
    - 인덕터: V = L·dI/dt
    - MOSFET: I_D = f(V_GS, V_DS, V_BS, W, L, model) — BSIM

### 2.2 연립 비선형 방정식

회로 전체를 노드 voltage 변수로 표현하면 **연립 비선형 ODE 시스템**:

```
G·v(t) + C·dv(t)/dt = i_source(t)
```

여기서:

- `G`: conductance matrix (선형 부분)
- `C`: capacitance matrix
- `v(t)`: 노드 voltage vector
- `i_source(t)`: 입력 자극
- 비선형 부분(MOSFET)은 `G·v` 안에 함수로 포함

### 2.3 Newton-Raphson — 비선형 풀이

선형 시스템은 한 번에 풀리지만, MOSFET I-V는 매우 비선형 → **반복법** 필요:

```
v^(k+1) = v^(k) - J^(-1)(v^(k)) · F(v^(k))
```

매 timestep:

1. 초기 추측 v⁰ 선택
2. F(v⁰) 계산 (회로 식의 잔차)
3. J (Jacobian) 계산 후 선형 시스템 풀이
4. v¹로 갱신
5. ||F|| < tolerance가 되면 수렴 — 다음 timestep으로
6. 발산하면 timestep 축소 후 재시도

**수렴 실패** = SPICE의 가장 흔한 오류. 원인:

- 초기 bias가 너무 멀리 있음 (`.ic` 또는 source ramp-up으로 해결)
- 회로에 latch-up · 무한 loop gain 등 불안정 구조
- numerical tolerance가 너무 빡빡 (`.option reltol=1e-3` 등 완화)

## 3. SPICE 분석 5종

| 분석 | 명령 | 용도 |
|------|------|------|
| **DC Operating Point** | `.op` | 회로의 정상상태 bias 계산. 가장 먼저 풀어야 함 |
| **DC Sweep** | `.dc V1 0 1 0.01` | 입력 voltage를 sweep하면서 출력 — I-V curve |
| **AC Analysis** | `.ac dec 10 1k 1G` | 작은 신호 주파수 응답 — gain, bandwidth, phase margin |
| **Transient** | `.tran 1p 10n` | **시간 영역 응답** — 가장 흔히 씀 |
| **Noise** | `.noise v(out) V1 dec 10 1 1G` | 출력에 보이는 노이즈 |
| **Monte Carlo** | `.mc 1000` (HSPICE 확장) | Process variation 기반 통계 분석 |
| **PSS / HB** | Spectre/SpectreRF | 주기적 정상상태 (RF 시뮬레이션) |

## 4. SPICE의 트랜지스터 모델 — BSIM

**BSIM** = **B**erkeley **S**hort-channel **I**GFET **M**odel.

MOSFET을 "단순 스위치"로 보지 않고 실제 물리 현상을 포함:

- Threshold voltage Vth (process·온도·body 의존)
- Channel length modulation (CLM)
- Body effect
- Subthreshold conduction (gate 약간 켜져도 누설)
- Velocity saturation
- Short-channel effects (DIBL 등)
- Temperature dependence

대표 모델 버전:

- BSIM3 (1996) — long-channel 보강
- BSIM4 (2000s) — Short-channel 강화, 130nm 이하 표준
- BSIM-CMG (2012~) — FinFET 전용
- BSIM-IMG (2010~) — Independent Multi-Gate

Foundry는 process node별 BSIM 파라미터(`.lib`)를 제공.

## 5. SPICE Netlist 예시 — CMOS 인버터

```spice
* CMOS Inverter Simulation
.include "tsmc_028nm.sp"   * Process model (foundry-provided)

* Subcircuit definition
.subckt inverter in out vdd vss
  M1 out in vdd vdd pmos w=4u l=0.028u
  M2 out in vss vss nmos w=2u l=0.028u
.ends

* Top level
V_vdd vdd 0 0.9
V_vss vss 0 0
V_in  in  0 PULSE(0 0.9 1n 50p 50p 5n 10n)

Xinv in out vdd vss inverter

C_load out 0 10f

* Analysis
.tran 0.01n 50n
.measure tran tpdr TRIG v(in)  VAL=0.45 RISE=1  TARG v(out) VAL=0.45 FALL=1
.measure tran tpdf TRIG v(in)  VAL=0.45 FALL=1  TARG v(out) VAL=0.45 RISE=1

.print v(in) v(out)
.end
```

구문 해석:

- `.subckt`: 인버터를 subcircuit으로 정의
- `M<name> drain gate source bulk <model> w=... l=...`: MOSFET
- `PULSE(low high delay rise fall width period)`: 펄스 자극
- `.tran <step> <stop>`: transient 분석
- `.measure`: propagation delay를 출력으로 자동 계산

## 6. SPICE의 강점과 약점

### 강점

- **트랜지스터 레벨 정확도** — Silicon에 가장 가까움
- 모든 회로 현상 분석 가능 (노이즈, 공정 변동, 온도, 전원 noise, crosstalk)
- **Sign-off 기준** — Tape-out 전 마지막 검증

### 약점

- **느림**: O(N²) ~ O(N³). 1만 트랜지스터 이상은 비현실적
- **메모리 사용량 큼**: 노드/branch 수에 비례
- **수렴 문제**: 빈도 있게 발생
- **stimulus 표현 한계**: 복잡한 디지털 시나리오 못 씀

## 7. Fast SPICE — 속도의 벽을 넘기

### 7.1 문제 정의

전통적 SPICE로는 다음 검증이 불가능:

- DRAM array 1Gb (10억 cell)의 read/write 동작
- SoC 전체의 전원 무결성 분석
- 수만 라인의 메모리 인터페이스 timing 검증

### 7.2 5가지 가속 기법

| 기법 | 설명 | 정확도 영향 |
|------|------|-----------|
| **Matrix partitioning** | 회로를 작은 부분으로 쪼개 독립적으로 풀기 | 작음 (경계 처리 주의) |
| **Event-driven analog** | 신호 변화가 있을 때만 노드 계산 | 작음 |
| **Table-based device model** | BSIM 식 대신 미리 계산된 lookup table 사용 | 보간 정확도 영향 |
| **Adaptive time step** | 신호가 안정적일 땐 큰 step, 변화 클 땐 작은 step | 일반 SPICE도 사용 |
| **Hierarchical isomorphism** | 동일 회로 반복 사용 시 한 번만 풀기 | 작음 (DRAM cell array에 매우 효과적) |

→ DRAM 검증에서 **10~100× 속도 향상**.

### 7.3 Fast SPICE 도구

| 도구 | 벤더 | 강점 |
|------|------|------|
| **CustomSim XA** | Synopsys | DRAM full-chip, post-layout |
| **FineSim Pro** | Synopsys | Fast + accurate 균형 |
| **UltraSim** | Cadence | Spectre 호환 |
| **Eldo Premier** | Siemens EDA | Foundry corner |

## 8. 대표 문제 — SPICE 시뮬레이션 시간 예측

### 문제

다음 회로들의 SPICE 시뮬레이션 시간을 추정하시오. 시뮬레이션 시간 ≈ O(N^1.5 ~ N²) × stop_time / time_step 으로 근사.

- A: 100 trans, 10 ns sim, 1 ps step
- B: 10,000 trans, 100 ns sim, 1 ps step
- C: 1,000,000 trans, 1 μs sim, 1 ps step (full-chip ARM core)
- D: DRAM 1Gb cell array (10⁹ trans), 100 ns

### 풀이

총 step 수 = stop_time / time_step. 각 step의 cost ∝ N^1.5 가정:

| 회로 | N | step 수 | cost ∝ | 추정 시간 |
|------|---|--------|--------|----------|
| A | 100 | 10,000 | 10⁷ | 수 초 |
| B | 10⁴ | 100,000 | 10¹¹ | 수 시간 |
| C | 10⁶ | 10⁶ | 10¹⁵ | **수 년 — 불가능** |
| D | 10⁹ | 10⁵ | 10¹⁸·⁵ | **수십 년 — 절대 불가능** |

### 통찰

- 10⁴ trans 이상은 **Fast SPICE 필수**
- 10⁶ trans 이상은 **RNM/AMS 필요**
- 10⁹ trans 이상(DRAM)은 **반드시 RNM** + corner SPICE

## 9. 흔한 함정

| 함정 | 증상 | 대응 |
|------|------|------|
| `.op` 수렴 실패 | bias 못 잡음 | `.ic` 명시, source ramp-up |
| `reltol` 너무 빡빡 | 매 step convergence fail | `.option reltol=1e-3 abstol=1e-12` |
| `.tran` step 너무 큼 | Fast transient 놓침 | `.tran 0.1p 10n maxstep=1p` |
| 잘못된 BSIM 버전 | 결과 비현실적 | foundry `.lib` 정확한 corner 사용 |
| 노이즈 시뮬 후 무시 | Final noise 미평가 | `.noise` 후 `.measure` 추가 |

## 핵심 정리

1. SPICE = KCL + KVL + element law + Newton-Raphson + BSIM transistor model
2. 5종 분석: `.op`, `.dc`, `.ac`, `.tran`, `.noise` (+ Monte Carlo)
3. 강점: 정확도. 약점: 속도. → Fast SPICE가 보완.
4. 10⁴ trans 이상은 Fast SPICE, 10⁶ 이상은 RNM/AMS로 escalate
5. 수렴 실패가 빈도 있는 오류 — initial condition · tolerance 조절 필수

## 더 읽을거리

- 다음: [Ch04. AMS · Verilog-AMS · Connect Module](04_ams_connect_modules.md)
- Kenneth Kundert, *The Designer's Guide to SPICE and Spectre* — 깊이 있는 입문
- Nagel, *SPICE2: A Computer Program to Simulate Semiconductor Circuits* (UCB ERL Memo, 1975)
- 퀴즈: [Ch03 퀴즈](quiz/ch03_quiz.md)
