---
title: "Ch03. SPICE / Fast SPICE 기초"
---

## 학습 목표

- **(Remember)** SPICE가 푸는 기본 법칙(KCL, KVL, element law)을 진술할 수 있다
- **(Remember)** SPICE의 5가지 분석 종류(.op/.dc/.ac/.tran/.noise)를 나열할 수 있다
- **(Understand)** Newton-Raphson 반복법이 왜 필요한지 설명할 수 있다
- **(Apply)** 간단한 CMOS 인버터의 SPICE netlist를 작성할 수 있다
- **(Analyze)** Fast SPICE의 5가지 가속 기법이 어떻게 정확도를 trade-off 하는지 분석할 수 있다

## 1. SPICE는 무엇인가

**SPICE** = **S**imulation **P**rogram with **I**ntegrated **C**ircuit **E**mphasis

SPICE를 배우는 이유는 단순합니다. mixed-signal 검증에서 RNM 모델이 SPICE를 "근사"한다고 했을 때, 그 근사의 기준이 되는 것이 SPICE이기 때문입니다. RNM 모델을 올바르게 작성하고 그 한계를 이해하려면, 먼저 SPICE가 무엇을 어떻게 계산하는지 알아야 합니다.

SPICE는 1973년 UC Berkeley의 Nagel이 박사학위 논문으로 개발했습니다(BCSC ERL Memo, 1975). 전기 회로의 동작을 수치적으로 시뮬레이션하는 도구로, HSPICE, Spectre, FineSim, Eldo 등 오늘날의 모든 상용 SPICE 시뮬레이터는 이 원조 Berkeley SPICE의 후예입니다.

## 2. SPICE가 푸는 것 — 회로 = 노드 + 컴포넌트

### 2.1 기본 법칙

SPICE가 풀어내는 것의 핵심은 세 가지 물리 법칙입니다. **KCL(Kirchhoff's Current Law)**은 모든 노드에서 들어오는 전류의 합과 나가는 전류의 합이 같다는 법칙이고, **KVL(Kirchhoff's Voltage Law)**은 임의의 폐회로에서 전압 강하의 합이 0이라는 법칙입니다. 그리고 각 소자는 자신만의 V-I 관계(**element law** — 전압과 전류의 관계식)를 가집니다. 저항은 V = IR이고, 캐패시터는 I = C·dV/dt이며, 인덕터는 V = L·dI/dt입니다. **MOSFET**(Metal-Oxide-Semiconductor FET — 게이트 전압으로 전류를 켜고 끄는 가장 기본적인 트랜지스터)은 훨씬 복잡해서 게이트·드레인·소스·벌크(트랜지스터의 네 단자) 전압과 트랜지스터 크기 및 BSIM(SPICE가 쓰는 표준 MOSFET 물리 모델) 모델 파라미터의 함수로 드레인 전류가 결정됩니다.

### 2.2 연립 비선형 방정식

회로 전체를 노드 voltage 변수로 표현하면 **연립 비선형 ODE**(Ordinary Differential Equation, 시간에 대한 미분이 포함된 상미분방정식) **시스템**:

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

저항과 캐패시터만 있는 선형 회로는 한 번의 행렬 연산으로 풀립니다. 그러나 MOSFET의 I-V 특성은 매우 비선형적이므로 반복법이 필요합니다. SPICE는 **Newton-Raphson** 방법을 씁니다. 먼저 노드 전압의 초기 추측 v⁰를 잡고, 회로 방정식의 잔차 F(v⁰)와 Jacobian J를 계산해 다음 추측값을 구합니다. 이것을 잔차가 허용 오차보다 작아질 때까지 반복합니다.

```
v^(k+1) = v^(k) - J^(-1)(v^(k)) · F(v^(k))
```

수렴하면 다음 timestep으로 넘어가고, 발산하면 timestep을 줄이고 재시도합니다.

**기하적 직관 — Jacobian 은 "접선의 기울기" 다.** 1변수로 줄여 보면 위 식은 `v^(k+1) = v^(k) − F(v^(k))/F'(v^(k))` 이고, 여기서 `F'`(다변수에서는 Jacobian J)가 _현재 추측점에서 곡선에 그은 접선의 기울기_ 다. Newton-Raphson 은 비선형 곡선 `F(v)=0` 의 해를, 현재 점에서 _접선을 그어 그 접선이 0 과 만나는 곳_ 을 다음 추측으로 삼는 방식이다 — 곡선을 매 step 직선으로 근사해 한 걸음씩 해에 다가간다. _왜 한 번에 안 되는가_: MOSFET I-V 가 비선형이라 접선(선형 근사)이 곡선과 한 점에서만 맞고 멀어질수록 어긋나므로, 근사→재선형화를 반복해야 한다(선형 회로라면 곡선이 곧 직선이라 1회로 끝난다). _왜 발산하는가_: 초기 추측이 동작점에서 멀면 그 지점의 접선이 해와 _엉뚱한 방향_ 을 가리켜 다음 추측이 더 멀어질 수 있고(특히 곡선이 평탄해 기울기 J 가 0 에 가까우면 `F/F'` 가 폭주), 그래서 `.ic` 로 좋은 출발점을 주거나 source ramp-up 으로 _가까운 동작점에서 시작_ 하는 것이 수렴의 열쇠다.

**수렴 실패**는 SPICE를 처음 쓸 때 가장 자주 만나는 오류입니다. 초기 bias 조건이 실제 동작점에서 너무 멀면 Newton-Raphson이 수렴하지 못하는데, 이런 경우 `.ic`로 초기 조건을 힌트하거나 source를 0에서 천천히 ramp-up하면 해결됩니다. 회로 자체에 latch-up이나 무한 loop gain 같은 불안정 구조가 있거나 `.option reltol`이 너무 빡빡하게 설정된 경우에도 수렴 실패가 일어납니다.

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

위 표의 용어: **bias**(정상상태에서 회로 각 노드가 갖는 정적 동작 전압/전류), **gain**(입력 대비 출력 신호가 커지는 배율), **bandwidth**(이득이 유지되는 주파수 범위), **phase margin**(피드백 회로가 발진하지 않고 안정할 여유), **Monte Carlo**(공정 편차를 무작위로 흔들어 통계 분포를 보는 분석), **transient**(시간에 따른 신호 파형을 보는 시간 영역 분석), **PSS/HB**(Periodic Steady State / Harmonic Balance — 주기 신호의 정상상태를 직접 푸는 RF 해석)입니다.

## 4. SPICE의 트랜지스터 모델 — BSIM

**BSIM** = **B**erkeley **S**hort-channel **I**GFET **M**odel.

MOSFET을 "단순 스위치"로 보지 않고 실제 물리 현상을 포함:

- Threshold voltage Vth (트랜지스터가 켜지기 시작하는 게이트 문턱 전압; process·온도·body 의존)
- Channel length modulation (CLM — 드레인 전압이 실효 채널 길이를 바꿔 전류가 약간 변하는 효과)
- Body effect (벌크 전압이 문턱 전압을 바꾸는 효과)
- Subthreshold conduction (gate 약간 켜져도 누설 — 문턱 아래에서도 흐르는 미세 누설 전류)
- Velocity saturation (전계가 세지면 캐리어 속도가 더 못 빨라져 전류가 포화)
- Short-channel effects (채널이 짧아질 때 생기는 비이상 효과; DIBL = Drain-Induced Barrier Lowering 등)
- Temperature dependence

대표 모델 버전:

- BSIM3 (1996) — long-channel 보강
- BSIM4 (2000s) — Short-channel 강화, 130nm 이하 표준
- BSIM-CMG (2012~) — FinFET(채널을 지느러미처럼 세워 게이트가 3면을 감싸는 최신 트랜지스터 구조) 전용
- BSIM-IMG (2010~) — Independent Multi-Gate

**Foundry**(반도체 위탁 생산 회사)는 **process node**(공정 세대 — 7nm, 28nm처럼 트랜지스터 최소 치수로 표기)별 BSIM 파라미터(`.lib` 파일)를 제공합니다.

## 5. SPICE Netlist 예시 — CMOS 인버터

**CMOS**(Complementary MOS — n형과 p형 트랜지스터를 짝지어 쓰는 저전력 회로 방식)로 만든 인버터의 netlist 예시입니다. **인버터**는 입력 0/1을 뒤집어 출력하는 가장 기본 게이트입니다.

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

- `.subckt`: 인버터를 **subcircuit**(재사용 가능한 회로 블록)으로 정의
- `M<name> drain gate source bulk <model> w=... l=...`: MOSFET (w=폭, l=채널 길이)
- `PULSE(low high delay rise fall width period)`: 펄스 자극
- `.tran <step> <stop>`: transient 분석
- `.measure`: **propagation delay**(입력 변화가 출력 변화로 나타나기까지의 지연 시간)를 출력으로 자동 계산

## 6. SPICE의 강점과 약점

SPICE의 가장 중요한 강점은 **트랜지스터 레벨 정확도**입니다. 실리콘에서 일어나는 노이즈, 공정 변동, 온도, 전원 노이즈, 크로스토크(crosstalk — 옆 배선의 신호가 결합해 간섭하는 현상) 같은 2차 효과까지 모두 분석할 수 있으며, 그 때문에 **tape-out**(제조용 데이터를 넘기는 최종 단계) 전 마지막 sign-off 기준으로 사용됩니다.

그러나 정확도에는 대가가 따릅니다. 계산 복잡도가 회로 크기 N에 대해 O(N²) ~ O(N³)인데, 이 복잡도는 _Newton-Raphson 매 반복마다 푸는 Jacobian 행렬 J 의 분해(LU factorization — 행렬을 상·하 삼각행렬의 곱으로 쪼개 연립방정식을 푸는 표준 기법)_ 에서 나옵니다 — N×N 연립방정식을 푸는 비용이 일반적으로 O(N³)(희소 행렬 최적화 시 더 낮음)이고, 이를 매 timestep × 매 Newton 반복마다 반복하기 때문입니다. 그래서 1만 트랜지스터를 넘어가면 시뮬레이션 시간이 비현실적으로 늘어납니다. 노드와 브랜치 수에 비례해 메모리도 폭발적으로 증가합니다. 수렴 문제도 빈도 있게 발생하며, 무엇보다도 디지털 시나리오를 SPICE netlist로 표현하기가 매우 불편합니다. "reset 후 1000 클록 랜덤 데이터 인가" 같은 시나리오를 SPICE로 쓰면 파일이 수천 줄이 됩니다. 이러한 약점들이 RNM이 필요한 구조적 이유입니다.

## 7. Fast SPICE — 속도의 벽을 넘기

### 7.1 문제 정의

전통적 SPICE로는 다음 검증이 불가능:

- DRAM array 1Gb (10억 cell)의 read/write 동작
- SoC 전체의 전원 무결성 분석
- 수만 라인의 메모리 인터페이스 timing 검증

### 7.2 5가지 가속 기법

Fast SPICE는 정확도를 크게 희생하지 않으면서 속도를 높이는 여러 기법을 조합합니다.

| 기법 | 설명 | 정확도 영향 |
|------|------|-----------|
| **Matrix partitioning** | 회로를 작은 부분으로 쪼개 독립적으로 풀기 | 작음 (경계 처리 주의) |
| **Event-driven analog** | 신호 변화가 있을 때만 노드 계산 | 작음 |
| **Table-based device model** | BSIM 식 대신 미리 계산된 lookup table 사용 | 보간 정확도 영향 |
| **Adaptive time step** | 신호가 안정적일 땐 큰 step, 변화 클 땐 작은 step | 일반 SPICE도 사용 |
| **Hierarchical isomorphism** | 동일 회로 반복 사용 시 한 번만 풀기 | 작음 (DRAM cell array에 매우 효과적) |

DRAM 검증에서 **hierarchical isomorphism**이 특히 효과적입니다. DRAM cell array는 수억 개의 동일한 구조가 반복됩니다. 한 셀의 특성을 한 번만 계산하고 나머지는 재사용하면 계산량이 극적으로 줄어듭니다. 이 기법들을 조합하면 DRAM 검증에서 **10~100× 속도 향상**이 가능합니다.

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

- 다음: [Ch04. AMS · Verilog-AMS · Connect Module](../04_ams_connect_modules/)
- Kenneth Kundert, *The Designer's Guide to SPICE and Spectre* — 깊이 있는 입문
- Nagel, *SPICE2: A Computer Program to Simulate Semiconductor Circuits* (UCB ERL Memo, 1975)
- 퀴즈: [Ch03 퀴즈](../quiz/ch03_quiz/)
