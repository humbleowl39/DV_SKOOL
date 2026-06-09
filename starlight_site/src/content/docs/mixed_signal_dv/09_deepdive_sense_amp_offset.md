---
title: "Ch09. Deep Dive — Sense Amp Offset · Pelgrom · Monte Carlo"
---

## 학습 목표

- **(Remember)** Sense amp offset의 3가지 source(random / systematic / operating)를 나열할 수 있다
- **(Understand)** Pelgrom's law가 transistor 크기와 σ(ΔVth) 사이의 관계를 어떻게 정의하는지 설명할 수 있다
- **(Apply)** Pelgrom's law 기반으로 RNM에 offset을 주입할 수 있다
- **(Analyze)** Monte Carlo 결과로부터 fail rate를 분석할 수 있다
- **(Evaluate)** Sense margin이 yield에 미치는 영향을 정량적으로 평가할 수 있다
- **(Create)** Correlated offset(process gradient) 모델을 설계하고 시뮬레이션할 수 있다

## 1. Offset이란 무엇이고 왜 중요한가

**Offset voltage (Vos)**는 **differential amplifier**(차동 증폭기 — 두 입력의 차이를 증폭하는 회로)의 두 입력에 같은 전압(**common-mode**, 두 입력에 공통으로 걸리는 전압)을 줬을 때 출력이 이상적인 중간 값이 아닌 한쪽으로 치우치는 현상입니다. 입력 환산 등가전압으로 표현합니다. 아래 그림의 **latch**는 sense amp가 미세 차이를 0 또는 1로 확정해 붙드는 동작을 가리킵니다.

```
   V+ = V- = Vcm  (common-mode)
   →  ideal:    Vout = 0 (또는 mid-swing)
   →  with offset: Vout = 한쪽 latch (예: '1')
   →  equivalent: V+ - V- = Vos
```

이것이 DRAM에서 치명적인 이유는 sense amplifier가 검출해야 하는 신호 자체가 매우 작기 때문입니다. bit cell의 charge sharing 후 BL 전압 변화 — 즉 DRAM이 읽어야 하는 "신호" — 는 약 60~100 mV 수준입니다(Ch06의 계산 참고). 만약 sense amp의 offset이 50 mV라면 실제 검출 가능한 범위는 100 - 50 = 50 mV로 줄어듭니다. offset이 110 mV라면 신호 방향과 반대로 라치되어 **read fail**이 발생합니다. 1Gb DRAM에는 10억 개의 sense amp가 있습니다. 모든 sense amp의 worst case offset이 sensing margin보다 작아야 **yield**(수율 — 만든 칩 중 정상 동작하는 비율)를 확보할 수 있습니다.

## 2. Offset의 3가지 Source

### 2.1 Random Mismatch (지배적)

sense amp의 핵심은 **차동 쌍(differential pair**, 입력을 나눠 받는 한 쌍의 트랜지스터)입니다. 두 NMOS 트랜지스터를 같은 레이아웃으로 제작해도 실리콘 제조 과정의 미세한 변동 때문에 두 소자의 특성이 조금씩 달라집니다. 이 차이가 offset의 주원인입니다. 가장 큰 기여를 하는 것은 **threshold voltage(Vth**, 트랜지스터가 켜지는 문턱 전압) mismatch이며, **transconductance parameter(β**, 게이트 전압 변화가 전류로 얼마나 잘 변환되는지를 나타내는 계수) mismatch, **oxide thickness**(게이트 산화막 두께) 변동, **doping**(반도체에 불순물을 주입한 농도) 변동이 추가됩니다.

이 현상을 정량화하는 식이 **Pelgrom's Law**(Pelgrom et al., JSSC 1989)입니다.

```
σ(ΔVth) = AVT / sqrt(W × L)
σ(Δβ/β) = Aβ / sqrt(W × L)
```

- AVT: process 의존 상수
- W, L: transistor 크기 (μm)

→ Transistor가 크면 mismatch ↓ (sqrt(WL) 분모).

### 2.2 Systematic Mismatch

random mismatch는 제조 공정의 무작위성에서 오지만, **systematic mismatch**(규칙적·재현되는 편차)는 레이아웃 설계의 비대칭성에서 옵니다. 두 트랜지스터가 레이아웃 상에서 다른 위치에 있으면 배선 길이 차이로 저항이 달라지거나, well proximity effect(소자가 well 경계에 가까울 때 특성이 변하는 효과), STI(Shallow Trench Isolation — 소자 간 절연을 위한 얕은 트렌치) 응력 비대칭 등이 발생합니다. 이를 줄이기 위해 **common centroid**(공통 무게중심 배치 — 두 소자를 교차 배치해 위치에 따른 편차를 상쇄) 배치를 사용하여 두 트랜지스터가 대칭적인 환경에 놓이도록 합니다.

### 2.3 Operating Conditions

VDD 변동, temperature gradient, substrate noise도 sense amp의 실효 offset에 영향을 줍니다. 이 요인들은 칩마다, 측정 시점마다 달라지므로 worst-case 검증 시 이 변동 범위를 포함해야 합니다.

## 3. Pelgrom AVT — Process 별 값

### 3.1 일반 CMOS (참고)

| Process node | AVT (mV·μm) | 비고 |
|---|---|---|
| 250 nm | ~20 | Vth ≈ 0.7V |
| 130 nm | ~10 | |
| 65 nm | ~5 | Bulk CMOS |
| 28 nm | ~4 | Bulk CMOS, low Vt |
| 16 nm FinFET | ~2.5 | FinFET 도입 효과 |
| 7 nm FinFET | ~2.0 | |
| 5 nm FinFET | ~1.8 | 단, MGG/RDF 비중 증가 |
| 3 nm GAA | ~1.6~2.0 (추정) | GAA — MGG·RDF·LER 지배적 |

> 5nm/3nm 영역에서는 단순 Pelgrom 공식이 한계 — **MGG (Metal Gate Granularity, 금속 게이트의 결정립 단위 편차)**, **LER (Line Edge Roughness, 패턴 가장자리의 미세 거칠기)**, **RDF (Random Dopant Fluctuation, 도핑 원자 수의 무작위 요동)**가 dominant variability source가 됩니다. (**GAA** = Gate-All-Around, 게이트가 채널을 사방에서 감싸는 최신 트랜지스터 구조. **TCAD** = 공정·소자를 물리 시뮬레이션하는 도구.)

### 3.2 28nm 기준 예시 — DDR5 sense amp

- AVT = 4 mV·μm
- W = 0.5 μm, L = 0.1 μm
- sqrt(W × L) = sqrt(0.05) = 0.224 μm
- **σ(ΔVth) = 4 / 0.224 ≈ 17.9 mV**

→ 입력 transistor 두 개의 Vth가 평균적으로 약 18mV 차이.

**1-sigma**: 68% 확률로 ±18 mV 이내
**3-sigma**: 99.7% 확률로 ±54 mV 이내
**6-sigma** (DRAM yield 기준 흔히 사용): ±108 mV

→ DRAM은 보통 6-sigma 또는 그 이상 margin 필요 (10⁹ 개 cell 중 fail 거의 없어야).

## 4. RNM에서 Offset 모델링하기

### 4.1 단순 random offset

```systemverilog
module sense_amp_with_offset_rnm (
  input  real  v_in_p,
  input  real  v_in_n,
  input  logic enable,
  output logic data_out
);
  parameter real OFFSET_SIGMA_MV = 18.0;  // Pelgrom-derived
  parameter int  SEED = 12345;

  real v_offset;

  initial begin
    // Compile-time random offset (instance-specific)
    v_offset = $dist_normal(SEED, 0, OFFSET_SIGMA_MV) * 1e-3;
    // mV → V
  end

  always @(posedge enable) begin
    real v_diff_eq;
    v_diff_eq = (v_in_p - v_in_n) + v_offset;

    if (v_diff_eq > 0) data_out = 1'b1;
    else                data_out = 1'b0;
  end
endmodule
```

→ 각 sense amp 인스턴스가 시뮬레이션 시작 시 자신의 offset을 random 결정.

### 4.2 Transistor 단위 mismatch 모델 (더 정밀)

Differential pair의 NMOS 두 개를 각각 모델링:

```systemverilog
module diff_pair_with_mismatch (
  input  real v_in_p,
  input  real v_in_n,
  input  real v_tail,
  output real i_out_p,
  output real i_out_n
);
  parameter real AVT_MV_UM = 4.0;
  parameter real W_UM      = 0.5;
  parameter real L_UM      = 0.1;
  parameter int  SEED      = 1;

  real vth_offset_p, vth_offset_n;
  real vth_p, vth_n;
  real vgs_p, vgs_n;

  initial begin
    real sigma_vth_v;
    sigma_vth_v = (AVT_MV_UM / $sqrt(W_UM * L_UM)) * 1e-3;
    vth_offset_p = $dist_normal(SEED,     0, sigma_vth_v);
    vth_offset_n = $dist_normal(SEED + 1, 0, sigma_vth_v);
    vth_p = 0.4 + vth_offset_p;
    vth_n = 0.4 + vth_offset_n;
  end

  always @(*) begin
    vgs_p = v_in_p - v_tail;
    vgs_n = v_in_n - v_tail;
    i_out_p = (vgs_p > vth_p) ? 0.5 * (vgs_p - vth_p) ** 2 : 0;
    i_out_n = (vgs_n > vth_n) ? 0.5 * (vgs_n - vth_n) ** 2 : 0;
  end
endmodule
```

→ 각 transistor의 Vth가 random. 두 Vth 차이가 입력 환산 offset.

## 5. Monte Carlo (RNM판)

SPICE Monte Carlo는 매우 느림. RNM에서 N번 random seed로 반복하면 빠르게 통계 분석.

```systemverilog
module sa_monte_carlo_tb;
  parameter int  N_RUNS          = 10000;
  parameter real SENSE_SIGNAL_MV = 100;

  integer pass_cnt, fail_cnt;
  real    offsets[];
  int     seed;

  initial begin
    offsets = new[N_RUNS];
    pass_cnt = 0;
    fail_cnt = 0;
    seed     = 1;

    for (int i = 0; i < N_RUNS; i++) begin
      real this_offset;
      real v_in_p, v_in_n;
      logic data_out;

      this_offset = $dist_normal(seed, 0, 18.0) * 1e-3;
      offsets[i]  = this_offset;

      v_in_p = 0.5 + SENSE_SIGNAL_MV/2 * 1e-3;
      v_in_n = 0.5 - SENSE_SIGNAL_MV/2 * 1e-3;

      data_out = ((v_in_p - v_in_n) + this_offset) > 0 ? 1 : 0;

      if (data_out === 1'b1) pass_cnt++;
      else                    fail_cnt++;
    end

    `uvm_info("MC", $sformatf("Runs=%0d Pass=%0d (%0.2f%%) Fail=%0d (%0.2f%%)",
              N_RUNS, pass_cnt, 100.0*pass_cnt/N_RUNS,
              fail_cnt, 100.0*fail_cnt/N_RUNS), UVM_LOW)

    print_stats(offsets);
  end

  function void print_stats(real arr[]);
    real sum = 0, mean, var = 0, sigma;
    foreach (arr[i]) sum += arr[i];
    mean = sum / arr.size();
    foreach (arr[i]) var += (arr[i] - mean) ** 2;
    var   = var / arr.size();
    sigma = $sqrt(var);
    `uvm_info("MC", $sformatf("Offset mean=%0.3f mV  sigma=%0.3f mV",
              mean*1000, sigma*1000), UVM_LOW)
  endfunction
endmodule
```

## 6. 대표 문제 — Fail Rate 예측

### 문제

DRAM의 sense amp offset σ = 18 mV (Gaussian). 검출 신호 = 100 mV. Fail 확률 및 10⁹ cell 중 fail 수?

### 풀이

**Step 1**: Fail 조건 = |Vos| > 100 mV (부호 반대 방향)

**Step 2**: 100 mV는 몇 σ?

```
100 / 18 ≈ 5.56 σ
```

**Step 3**: Gaussian tail probability (정규분포에서 평균에서 멀리 떨어진 꼬리 영역의 확률; **Q(x)** = 정규분포가 x·σ를 초과할 확률을 주는 함수)

```
P(|x| > 5.56σ) ≈ Q(5.56) × 2 ≈ 2.7 × 10⁻⁸
```

**Step 4**: 10⁹ cell 중 fail 수

```
10⁹ × 2.7 × 10⁻⁸ ≈ 27 cell fail
```

→ 27 cell이 fail → **repair**(불량 셀을 예비 셀로 교체) / **redundancy**(여분의 행·열을 미리 둬 불량을 대체하는 구조) 필요.

### 어떻게 fail rate를 줄일까?

1. **Sense margin 증가** (cell 또는 BL capacitance 조정)
2. **Transistor size 증가** → σ ↓ (Pelgrom)
3. **Common centroid layout** → systematic mismatch 감소
4. **Offset calibration** (training으로 offset 측정 후 보상)
5. **Redundancy + repair** (fail cell을 spare로 교체)

### Sense margin을 150 mV로 늘리면?

- 150 / 18 = 8.33 σ
- Q(8.33) ≈ 4 × 10⁻¹⁷
- 10⁹ × 4 × 10⁻⁸ ≈ 사실상 fail 없음

### Transistor size 4× 늘리면?

- σ → σ / sqrt(4) = 9 mV
- 100 / 9 = 11 σ
- 사실상 fail 없음

→ Pelgrom's law 보면 **transistor size 늘리는 게 효과적** (그러나 area cost).

## 7. RNM Monte Carlo의 한계와 SPICE의 보완 역할

### RNM Monte Carlo로 충분한 것

- Statistical fail rate 예측 (충분한 sample 수면)
- Architectural decisions (size, margin, repair strategy)
- Yield 예측

### RNM이 못 잡는 것 (SPICE 필요)

- **Transient mismatch**: 천이 중 발생하는 offset (kickback noise — sense amp가 latch될 때 입력 쪽으로 되튀는 잡음)
- **Process gradient**: Die(웨이퍼에서 잘라낸 칩 한 조각) 위 위치에 따른 systematic shift
- **Temperature dependence**: Offset이 temperature와 어떻게 변하는지
- **Stress effect**: BTI(Bias Temperature Instability), HCI(Hot Carrier Injection) 등 aging(시간이 지나며 특성이 열화되는) 효과
- **Differential charge injection, DIBL(Drain-Induced Barrier Lowering, 미세 채널에서 드레인 전압이 문턱을 낮추는 효과), stack effect**: 미세 노드에서 deviation 큼

### 산업 흐름

1. **RNM Monte Carlo** (10,000 runs in 10 분) → 1차 fail rate, design parameter 탐색
2. **SPICE Monte Carlo** (1,000 runs in 며칠) → 정밀 검증, sign-off
3. **실리콘 측정** (engineering sample, **ATE shmoo** — 자동 테스트 장비로 전압·타이밍을 격자로 쓸어 pass/fail 영역을 그린 plot) → 모델 calibration
4. **양산** (**BIST** = Built-In Self-Test, 칩 내부에 내장된 자가 검사 회로 + redundancy repair)

## 8. 변형 실습

### 실습 1: σ 변화에 따른 fail rate

| σ (mV) | Signal (mV) | σ ratio | P(fail) |
|--------|-------------|---------|---------|
| 10 | 100 | 10× | ~10⁻²³ |
| 15 | 100 | 6.67× | ~1.3 × 10⁻¹¹ |
| 20 | 100 | 5× | ~5.7 × 10⁻⁷ |
| 25 | 100 | 4× | ~3.2 × 10⁻⁵ |
| 30 | 100 | 3.33× | ~4.3 × 10⁻⁴ |

### 실습 2: Offset calibration 효과

- Calibration 정확도: ±5 mV
- Calibrated σ ≈ 5 mV
- Fail rate 비교

### 실습 3 (Challenge): Correlated offset (process gradient)

인접 SA들이 process gradient 때문에 correlated(상관됨 — 한쪽이 크면 다른 쪽도 같이 큰 경향). ρ(rho, 상관계수 — 0이면 무관, 1이면 완전 비례) = 0.3 ~ 0.7. 아래는 **bivariate normal**(두 변수가 함께 정규분포를 이루는 이변량 정규분포)에서 상관된 난수를 만드는 코드입니다:

```systemverilog
// Bivariate normal — generate correlated random
real x1, x2;
real z1, z2;
real rho = 0.5;
z1 = $dist_normal(seed1, 0, sigma);
z2 = $dist_normal(seed2, 0, sigma);
x1 = z1;
x2 = rho * z1 + $sqrt(1 - rho*rho) * z2;
```

→ x1, x2가 ρ만큼 양의 상관. Spatial Pelgrom 시뮬레이션.

## 9. 통계적 검증 흐름 — DRAM Sign-off

```
[1차: RNM Monte Carlo]
  → 10,000~100,000 runs
  → 1차 fail rate 추정
  → architectural margin 결정
      ↓
[2차: SPICE Monte Carlo]
  → 1,000~5,000 runs
  → critical corner (SS, FF, hot, cold)
  → sign-off margin 확정
      ↓
[3차: 실리콘 측정]
  → Engineering sample
  → ATE shmoo plot
  → 모델 calibration
      ↓
[양산]
  → BIST + redundancy repair
  → 통계적 yield 검증
```

→ RNM은 **architectural 선택**과 **broad sweep**에 매우 강력. SPICE는 **정밀 검증**에 필수.

## 10. 흔한 함정

| 함정 | 설명 |
|------|------|
| Single-instance Monte Carlo | 한 SA의 여러 trial이 아니라 여러 SA 모집단 |
| Seed 재사용 | 같은 시드면 같은 offset → 통계 무의미 |
| 정규분포 가정 한계 | 실제는 heavy-tail(정규분포보다 극단값이 더 자주 나오는 두꺼운 꼬리) (rare extreme outlier) |
| Temperature 무시 | 25°C와 -40°C, 125°C는 offset 분포 다름 |
| Aging 무시 | 1년, 10년 후 offset이 더 커짐 |
| 5nm 이하 Pelgrom 단순 적용 | MGG/RDF 비중 증가 — TCAD 결과 반영 필요 |

## 핵심 정리

1. SA offset의 main source: **random Vth mismatch** (Pelgrom)
2. Pelgrom: `σ(ΔVth) = AVT / sqrt(W × L)` — transistor 크면 mismatch ↓
3. 5nm 이하는 MGG/RDF/LER이 dominant → 단순 Pelgrom 한계
4. 100 mV signal + 18 mV σ → 5.56 σ → 10⁹ cell 중 ~27 fail
5. Sign-off는 RNM MC + SPICE MC + 실리콘 측정 3단계

## 더 읽을거리

- 다음: [Ch10. RNM/AMS 검증 방법론 통합](../10_verification_methodology/)
- Pelgrom et al., *"Matching properties of MOS transistors"*, JSSC 1989
- Razavi, *Design of Analog CMOS Integrated Circuits* — Mismatch chapter
- Kinget, *"Device Mismatch and Tradeoffs in the Design of Analog Circuits"*, JSSC 2005
- Lim et al., *"Modeling of Statistical Variation Effects on DRAM Sense Amplifier Offset Voltage"*, Micromachines (MDPI) 2021
- JEDEC JESD79-5C (DDR5) — yield specs
- 퀴즈: [Ch09 퀴즈](../quiz/ch09_quiz/)
