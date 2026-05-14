# Unit 5 — Analog / Mixed-Signal Design

!!! objective "학습 목표"
    이 모듈을 마치면:

    - **Analyze** RC 회로의 step response 와 high-pass / low-pass filter 의 transfer function 을 도출한다.
    - **Compute** ideal op-amp 구성(inverting, non-inverting, summing, integrator, differentiator) 의 closed-loop gain 을 계산한다.
    - **Explain** CMOS small-signal model (gm, ro, gmb, Cgs, Cgd) 과 channel length modulation, body effect, latch-up 의 물리적 근거를 설명한다.
    - **Design** PTAT + CTAT 결합으로 bandgap reference 의 1차 온도 보상 원리를 그림으로 그린다.
    - **Compare** Buck / Boost / Buck-Boost / LDO 의 topology 와 CCM / DCM / BCM 동작 모드, 그리고 PSRR / dropout / efficiency 트레이드오프를 비교한다.
    - **Evaluate** common-centroid / dummy / interdigitated layout 의 mismatch 감소 효과를 평가한다.

!!! info "사전 지식"
    - 학부 회로이론 (KCL/KVL, Thevenin/Norton, AC small-signal)
    - 반도체 물리 기본 (MOSFET I-V, threshold, depletion)

---

## 1. 기본 회로 — RC 와 필터

### 1.1 RC step response

```
   R
●──/\/\──┐
         │      Vc(t) = Vin · (1 - e^(-t/RC))
        ===C
         │      τ = RC  (시정수)
        GND
```

- 5τ 면 99.3% 도달. 인터뷰에서는 보통 *3τ ≈ 95%* 까지 회로 안정 시간으로 잡는다.

### 1.2 Low-pass vs High-pass

| Filter | 구조 | Transfer (s-domain) | Cutoff |
|--------|------|---------------------|--------|
| **RC LPF** | R series, C shunt | `H(s) = 1 / (1 + sRC)` | `f_c = 1 / (2π RC)` |
| **RC HPF** | C series, R shunt | `H(s) = sRC / (1 + sRC)` | `f_c = 1 / (2π RC)` |
| **RLC bandpass** | 직렬 RLC | `H(s) = (R/L)s / (s² + (R/L)s + 1/LC)` | `f_0 = 1/(2π√LC)` |

- LPF: DC pass, high freq reject. 노이즈 제거 / anti-aliasing.
- HPF: DC block, AC pass. AC coupling.

---

## 2. Op-Amp — Ideal Configurations

**Ideal op-amp 가정** — Infinite gain, infinite input impedance, zero output impedance, V+ = V− (negative feedback 시).

### 2.1 5가지 기본 구성

```
Inverting:           Vo / Vi = -Rf / Rin
Non-inverting:       Vo / Vi = 1 + Rf / Rg
Voltage follower:    Vo = Vi          (buffer, gain=1)
Summing:             Vo = -(Rf/R1·V1 + Rf/R2·V2 + ...)
Integrator:          Vo = -(1/RC) ∫ Vi dt
Differentiator:      Vo = -RC · dVi/dt
```

### 2.2 Non-ideal — Real-world 한계

| 비이상 | 영향 | 보완 |
|--------|------|------|
| **Finite GBW** (Gain-Bandwidth Product) | High freq gain ↓ | 한 stage 의 gain × bandwidth 일정 — 많은 단 사용 |
| **Slew rate** | 출력이 큰 폭 변화 시 속도 제한 (V/μs) | 큰 신호에 대해 GBW 와 별도 제약 |
| **Input offset voltage** | V+ = V− 가정 위반 (수 mV) | Chopper / auto-zero 회로 |
| **Input bias current** | Bias 전류가 input 으로 흘러 offset 유발 | FET input 사용, 대칭 임피던스 |
| **CMRR** (Common-Mode Rejection) | 공통 mode 신호 일부가 출력에 누설 | Differential pair tail 전류원 개선 |
| **PSRR** (Power Supply Rejection) | VDD ripple 이 출력으로 | Cascode, bandgap reference |

### 2.3 Miller Compensation

```
2단 op-amp 의 두 pole (p1, p2) 가 unity-gain 부근에 가까우면 phase margin 부족.
2단 사이에 Cc (compensation cap) → Miller effect 로 *p1 을 매우 낮은 주파수로 이동*
→ unity-gain crossover 이전에 p2 가 만나기 전 -20dB/dec 단일 pole 처럼 동작.
Phase margin 60° 이상 확보.
```

**Pole splitting** — Cc 가 p1 을 낮추고 동시에 p2 를 *높임* (좋은 부작용).

### 2.4 Slew rate vs Bandwidth — 차이

- **Bandwidth (GBW)** — *small-signal* 한계. 작은 신호 (수 mV) 에서 frequency response.
- **Slew rate** — *large-signal* 한계. 큰 step (수 V) 에서 dV/dt 한계 (current / capacitance).

큰 신호는 두 한계 *모두* 적용 — 더 엄격한 쪽이 작동.

---

## 3. CMOS Small-Signal Model

### 3.1 NMOS in saturation

$$ I_D = \frac{1}{2} \mu_n C_{ox} \frac{W}{L} (V_{GS} - V_{TH})^2 (1 + \lambda V_{DS}) $$

- **gm** (transconductance) = ∂ID/∂VGS = `μ Cox (W/L) (Vgs - Vth)` = `2 ID / (Vgs - Vth)` = `sqrt(2 μ Cox W/L · ID)`
- **ro** (output resistance) = 1 / (λ · ID) — *channel length modulation* 효과
- **gmb** (body transconductance) = γ · gm / (2 √(2Φ_F + V_SB)) — body effect

### 3.2 채널 길이 변조 (Channel Length Modulation)

VDS 가 커지면 *pinch-off* 지점이 source 쪽으로 이동 → effective channel 짧아짐 → ID 약간 증가. 1 + λVDS 의 *λ* 가 그 정도.

**의미**: *output impedance 가 무한대가 아니다* — finite ro. gain `gm·ro` 가 한계.

### 3.3 Body Effect

소스 ↔ 기판 간 전압 (VSB) 가 0 이 아닐 때 *VTH 가 증가*. Cascode 또는 stack 회로에서 흔히 발생.

$$ V_{TH} = V_{TH0} + \gamma (\sqrt{2\Phi_F + V_{SB}} - \sqrt{2\Phi_F}) $$

### 3.4 Latch-Up

CMOS 의 *p-substrate + n-well + p+ source* 가 parasitic *p-n-p-n* SCR 을 형성. 한 번 trigger 되면 high current 가 흘러 *chip 소손*.

**방지**:
- Guard ring (n+ in p-substrate, p+ in n-well) — 누설 전류 우회
- Substrate / well 강한 contact — beta 낮춤
- Latch-up test (JEDEC JESD78): I/O 에 over-voltage / over-current 인가 후 정상 복귀 확인

---

## 4. Bandgap Reference

### 4.1 PTAT + CTAT 결합

- **CTAT** (Complementary to Absolute Temperature) — `Vbe` 가 T 증가 시 *감소* (-2 mV/°C 정도).
- **PTAT** (Proportional to Absolute Temperature) — 두 BJT 의 *ΔVbe* 가 T 에 비례 (서로 다른 전류 밀도).

```
Vref = Vbe + α · ΔVbe
       ↑ CTAT        ↑ PTAT (× α 로 적절히 weight)
       => 1차 T 미분이 0 인 점 → ~ 1.2V (Si bandgap)
```

### 4.2 Brokaw / Widlar / Kuijk topology

- **Brokaw** — npn BJT 두 개를 *transistor area ratio* 8:1 로. 가장 흔함.
- **Widlar** — 저전류, 정밀.
- **Kuijk** — op-amp 사용, modern CMOS friendly.

### 4.3 인터뷰 빈출 디테일

- "Bandgap output 이 항상 ~1.2V 인 이유" → Si bandgap energy (1.12 eV / e) 와 일치 (실제로는 T=0 으로 extrapolation).
- "2차 곡률 보정" — PTAT² 항을 더해 더 평탄한 출력.

---

## 5. Power Converter — Buck / Boost / LDO

### 5.1 Topology 한 줄

| Converter | Vin → Vout | 핵심 |
|-----------|------------|------|
| **Buck** | 높은 V → 낮은 V (step-down) | High-side switch + diode + L + C |
| **Boost** | 낮은 V → 높은 V (step-up) | Low-side switch + diode + L + C |
| **Buck-Boost** | 양방향 (Vout > 또는 < Vin) | inverted 또는 SEPIC topology |
| **LDO** | 작은 dropout 으로 step-down | Pass transistor + 피드백 (스위칭 없음) |

### 5.2 CCM / DCM / BCM

- **CCM** (Continuous Conduction Mode) — Inductor 전류가 *0 아래로 안 내려감*. High load 에서. 효율 좋음, ripple 작음.
- **DCM** (Discontinuous Conduction Mode) — Inductor 전류가 *0 까지 내려감*. Light load. 효율은 light load 에서 좋음, control 복잡.
- **BCM** (Boundary Conduction Mode) — 정확히 0 에 도달 시 다음 스위칭. Variable freq.

### 5.3 Buck 의 Duty Cycle (CCM)

$$ \frac{V_{out}}{V_{in}} = D \quad \text{(buck)} $$

$$ \frac{V_{out}}{V_{in}} = \frac{1}{1-D} \quad \text{(boost)} $$

### 5.4 Compensation (Type II / Type III)

스위칭 컨버터의 control loop:
- **Voltage mode** — Vout 만 sense, type-III compensation (3 pole + 2 zero) 필요.
- **Current mode (peak/avg)** — Inductor 전류도 sense, type-II (1 pole + 1 zero) 로 충분. 응답 빠름.

### 5.5 Dead-time

High-side 와 low-side switch 가 *동시에 켜지면 short → shoot-through current*. Dead-time 으로 둘 다 off 인 짧은 구간 보장.

**디테일**: Dead-time 이 너무 길면 *body diode 통해 전류 흐름 → 효율 저하 + EMI*.

### 5.6 GaN vs Si — 인터뷰 핵심

| 항목 | Si MOSFET | GaN HEMT |
|------|-----------|----------|
| Switching speed | ~ 10s ns | ~ 1 ns |
| Rdson × Qg | 높음 | **낮음** → 고효율 |
| 가격 | 저렴 | 비쌈 |
| Gate drive | 12V 흔함 | 5~6V (낮음), 정밀 필요 |
| 적용 | 일반 | 고주파 (MHz~) 컨버터, RF |

GaN 의 gate 는 *Schottky-like*, threshold 가 낮고 gate charge 적다 → 빠른 스위칭 + 효율.

---

## 6. LDO Design

### 6.1 기본 구조

```
[Vin] --|S/D| Pass Transistor (PMOS or NMOS)  ---- [Vout] ---- Load
              |G                                       |
              +-- Error Amp <----- Feedback divider ---+
                       ^
                       +-- Vref (bandgap)
```

### 6.2 PMOS vs NMOS pass

| 측면 | PMOS pass | NMOS pass |
|------|-----------|-----------|
| Dropout | **매우 낮음** (수십 mV) | 더 높음 (Vgs 필요) |
| 회로 복잡도 | 단순 | Charge pump 또는 추가 supply 필요 |
| PSRR (high freq) | 낮음 (Cgd 결합) | 높음 |
| Stability | 부하 cap 큰 값 필요 | 더 안정 |

### 6.3 PSRR (Power Supply Rejection Ratio)

VDD ripple 이 Vout 에 얼마나 누설되는가 (dB). High PSRR 이 *깨끗한 supply* 의 핵심.

**저주파 PSRR** — 주로 *error amp gain* 으로 결정.
**고주파 PSRR** — pass transistor 의 *parasitic Cgd* 와 *output cap* 으로 결정.

### 6.4 Stability — Phase margin

LDO 는 *부하 cap (Cload) 의 ESR* 이 zero 를 만들어 안정성 결정.
- ESR 너무 작음 (예: 세라믹 cap 0.001Ω) → unstable
- ESR 너무 큼 → ripple 증가

**Modern cap-less LDO** — internal compensation 으로 외부 cap ESR 의존 제거.

---

## 7. Layout — Mismatch Reduction

### 7.1 Common-Centroid

두 trans 의 평균이 *같은 무게중심* 에 오도록 *교차* 배치. Process gradient (e.g. oxide thickness 변화) 평균 제거.

```
A B B A     A 2개, B 2개의 무게중심 동일
B A A B
```

### 7.2 Interdigitated (or finger)

긴 transistor 를 *작은 finger 여러 개* 로 나누고 두 트랜스의 finger 가 *교차*. Common-centroid 의 단순 1D 버전.

### 7.3 Dummy device

배열 *가장자리* 에 *실제 동작 안 하는 dummy* 추가. 가장자리의 *etch / dopant proximity* 가 다른 영향을 본 transistor 가 받지 않게.

### 7.4 Guard ring

n+ in p-sub (또는 반대) ring 으로 회로를 둘러쌈. *substrate noise* 와 *latch-up* 동시 방지.

---

## 8. 샘플 인터뷰 Q&A

??? question "Q1. (Compute) Inverting amp Vo/Vin = -Rf/Rin. Rf=10k, Rin=1k, Vin=0.5V. Vo=?"
    `Vo = -(10k/1k) · 0.5 = -5V`. Power rail 이 ±5V 이상이면 OK, 그보다 작으면 saturation.

??? question "Q2. (Explain) Channel length modulation 이 *DC gain* 에 미치는 영향?"
    Small-signal gain `Av = -gm · (ro || R_load)`.
    채널 변조가 *없으면* ro = ∞ → gain 이 R_load 만으로 결정.
    실제로는 ro 가 *유한* → gain 이 *gm·ro* 로 제한. Cascode 로 ro 증가시켜 보상.

??? question "Q3. (Design) 1.2V bandgap 의 *온도 1차 미분이 0* 이 되는 조건?"
    `Vref = Vbe + α · ΔVbe`
    Vbe 의 ∂T = −2 mV/°C, ΔVbe 의 ∂T = +0.085 mV/°C (대략).
    α = 2 / 0.085 ≈ 23.5 일 때 합산 미분 = 0.

??? question "Q4. (Compare) Buck CCM vs DCM 의 efficiency 곡선?"
    - **CCM** — Heavy load 에서 효율 *최대*. Light load 에서 *switching loss* 가 conduction loss 보다 크게 차지하면서 효율 ↓.
    - **DCM** — Light load 에서 *switching loss 감소* (전류 0 일 때 switch 안 함) → 효율 ↑. Heavy load 에서는 RMS current 가 커서 효율 ↓.
    - 현대 컨버터는 *light load 자동 DCM 전환* (PFM, Pulse Skipping) 으로 두 영역 모두 최적.

??? question "Q5. (Evaluate) LDO 와 Buck — 5V → 3.3V 변환에 어느 게 좋은가?"
    **Buck (스위칭)**:
    - 효율 90%+ (Vout/Vin 무관, 스위칭 loss 만)
    - EMI / ripple
    - 인덕터 면적
    - 비교적 *느린* transient

    **LDO**:
    - 효율 = Vout/Vin = 66% (33% 가 열로)
    - 깨끗한 출력 (PSRR 높음)
    - 작은 면적
    - *빠른* transient

    **결론**: 디지털 main 은 Buck, sensitive analog block (PLL VCO, ADC reference) 은 LDO 로 cascade.

---

## 9. 핵심 정리 (Key Takeaways)

1. Op-amp 는 ideal (V+=V−, infinite gain) 가정으로 *수식부터* 풀고 GBW/SR 로 검증.
2. CMOS small-signal: `gm`, `ro`, `gmb` 3개 + λ (CLM), γ (body). 이 5개로 거의 모든 회로 분석.
3. Latch-up = parasitic SCR. Guard ring + 강한 substrate contact 으로 방지.
4. Bandgap = PTAT + CTAT 합으로 1차 T 보정 → ~1.2V.
5. Buck > LDO 효율, LDO > Buck 노이즈. 보통 둘을 *cascade*.
6. Layout mismatch = common-centroid + dummy + guard ring 의 3종 세트.

## 10. Further Reading

- *Design of Analog CMOS Integrated Circuits* (Razavi) — 정석
- *Analog Integrated Circuit Design* (Johns & Martin)
- *Fundamentals of Power Electronics* (Erickson) — Buck/Boost 심화
- Texas Instruments Application Notes (LDO, Bandgap)
- [Unit 5 퀴즈](quiz/05_analog_mixed_signal_quiz.md) 로 자기 점검
