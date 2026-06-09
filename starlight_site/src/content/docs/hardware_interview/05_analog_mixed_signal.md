---
title: "Unit 5 — Analog / Mixed-Signal Design"
---

:::tip[학습 목표]
이 모듈을 마치면:

- **Analyze** RC 회로의 step response 와 high-pass / low-pass filter 의 transfer function 을 도출한다.
- **Compute** ideal op-amp 구성(inverting, non-inverting, summing, integrator, differentiator) 의 closed-loop gain 을 계산한다.
- **Explain** CMOS small-signal model (gm, ro, gmb, Cgs, Cgd) 과 channel length modulation, body effect, latch-up 의 물리적 근거를 설명한다.
- **Design** PTAT + CTAT 결합으로 bandgap reference 의 1차 온도 보상 원리를 그림으로 그린다.
- **Compare** Buck / Boost / Buck-Boost / LDO 의 topology 와 CCM / DCM / BCM 동작 모드, 그리고 PSRR / dropout / efficiency 트레이드오프를 비교한다.
- **Evaluate** common-centroid / dummy / interdigitated layout 의 mismatch 감소 효과를 평가한다.
:::
:::note[사전 지식]
- 학부 회로이론 (KCL/KVL, Thevenin/Norton, AC small-signal)
- 반도체 물리 기본 (MOSFET I-V, threshold, depletion)
:::
---

## 1. 기본 회로 — RC 와 필터

이 모듈은 디지털과 달리 연속적인 전압·전류를 다루는 아날로그/혼성신호 설계입니다. **Mixed-signal**(혼성신호 — 아날로그와 디지털 회로가 한 칩에 섞인 설계)이 그 이름의 뜻입니다. 자주 나오는 기본 용어: **R**(저항), **C**(커패시터, 전하를 저장하는 소자), **L**(인덕터, 전류 변화에 저항하는 코일), **transfer function**(전달 함수 — 입력 주파수에 따라 출력이 어떻게 바뀌는지 나타낸 수식), **gain**(이득 — 출력이 입력보다 몇 배 커지는지), **impedance**(임피던스 — 교류에 대한 저항 성분)입니다.

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

- **LPF**(Low-Pass Filter, 저역통과 필터 — 낮은 주파수는 통과, 높은 주파수는 차단): DC pass, high freq reject. 노이즈 제거 / anti-aliasing(샘플링 전에 너무 높은 주파수를 미리 깎아 가짜 신호 생성을 막는 것).
- **HPF**(High-Pass Filter, 고역통과 필터 — 높은 주파수만 통과): DC block, AC pass. AC coupling(DC 성분을 막고 변화하는 신호만 전달). **cutoff frequency**(차단 주파수 `f_c` — 통과와 차단이 갈리는 경계 주파수)가 둘의 기준점입니다.

---

## 2. Op-Amp — Ideal Configurations

**Op-amp**(operational amplifier, 연산 증폭기 — 두 입력의 전압 차를 매우 크게 증폭하는 아날로그의 핵심 빌딩블록)는 거의 모든 아날로그 회로의 기본 단위입니다.

**Ideal op-amp 가정** — Infinite gain(무한 이득), infinite input impedance(입력으로 전류가 안 흘러듦), zero output impedance, V+ = V− (negative feedback(음의 되먹임 — 출력 일부를 입력에 빼서 안정화) 시 두 입력 전압이 같아지는 *virtual short*(가상 단락) 특성).

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

여기서 **pole**(폴 — 주파수가 올라가며 gain이 꺾여 떨어지기 시작하는 지점), **phase margin**(위상 여유 — 피드백 회로가 발진하지 않고 안정한지 나타내는 여유; 보통 60° 이상이 안전), **dominant pole**(지배 폴 — 가장 낮은 주파수의 pole로, 전체 응답을 좌우)이 핵심입니다.

```
2단 op-amp 의 두 pole (p1, p2) 가 unity-gain 부근에 가까우면 phase margin 부족.
2단 사이에 Cc (compensation cap) → Miller effect 로 *p1 을 매우 낮은 주파수로 이동*
→ unity-gain crossover 이전에 p2 가 만나기 전 -20dB/dec 단일 pole 처럼 동작.
Phase margin 60° 이상 확보.
```

**Pole splitting** — Cc 가 p1 을 낮추고 동시에 p2 를 *높임* (좋은 부작용).

**왜 Cc 하나가 두 pole 을 _반대 방향_ 으로 미나 — Miller effect 의 물리.** Cc 는 2단(gain 단)의 입력과 출력 사이에 걸린다. **Miller effect** 란, gain `−A_v` 를 가진 증폭단의 입력에서 본 feedback capacitor 가 _실제 용량의 (1+A_v) 배_ 로 _증폭되어_ 보이는 현상이다 — 출력이 입력의 반대로 크게 흔들리므로 Cc 양단 전압 변화가 커지고, 그만큼 입력단이 공급해야 할 전하가 늘어 입력에서는 `Cc·(1+A_v)` 짜리 거대한 capacitor 처럼 작동한다. pole 주파수는 `f = 1/(2π·R·C)` 라 C 가 커지면 주파수가 내려가므로, 이 _증폭된 입력 capacitance_ 가 1단 출력 노드의 pole p1 을 매우 낮은 주파수로 끌어내린다 (dominant pole 화).

동시에 p2(2단 출력 노드)는 _높아진다_. Cc 가 고주파에서 1단 출력과 2단 출력을 _단락(short)_ 처럼 연결해 2단의 출력 저항을 실효적으로 낮추는 효과(되먹임에 의한 출력 임피던스 감소)를 주기 때문이다 — `R` 이 작아지니 `f=1/(2πRC)` 의 p2 가 위로 밀린다. 결과적으로 p1↓·p2↑ 로 두 pole 의 _간격이 벌어져_(splitting), unity-gain crossover 전까지는 p1 하나만 작용하는 −20 dB/dec 단일-pole 처럼 보여 phase margin 이 확보된다. 즉 "한 capacitor 가 두 pole 을 반대로 민다" 는 직관의 근거는 _입력측에서는 Miller 증폭, 출력측에서는 고주파 단락_ 이라는 같은 Cc 의 두 얼굴이다.

### 2.4 Slew rate vs Bandwidth — 차이

- **Bandwidth (GBW)** — *small-signal* 한계. 작은 신호 (수 mV) 에서 frequency response.
- **Slew rate** — *large-signal* 한계. 큰 step (수 V) 에서 dV/dt 한계 (current / capacitance).

큰 신호는 두 한계 *모두* 적용 — 더 엄격한 쪽이 작동.

---

## 3. CMOS Small-Signal Model

**CMOS**(Complementary MOS — NMOS와 PMOS 트랜지스터를 짝지어 쓰는 표준 반도체 공정), **MOSFET**(전압으로 채널의 전류를 조절하는 트랜지스터; NMOS/PMOS 두 종류), **small-signal model**(소신호 모델 — 동작점 근처의 작은 변화에 대해 트랜지스터를 선형 소자로 근사한 분석 모델)이 아날로그 손계산의 토대입니다. **saturation**(포화 영역 — MOSFET이 증폭기로 동작하는 정상 영역)에서 주로 분석합니다.

### 3.1 NMOS in saturation

$$ I_D = \frac{1}{2} \mu_n C_{ox} \frac{W}{L} (V_{GS} - V_{TH})^2 (1 + \lambda V_{DS}) $$

- **gm** (transconductance) = ∂ID/∂VGS = `μ Cox (W/L) (Vgs - Vth)` = `2 ID / (Vgs - Vth)` = `sqrt(2 μ Cox W/L · ID)`
- **ro** (output resistance) = 1 / (λ · ID) — *channel length modulation* 효과
- **gmb** (body transconductance) = γ · gm / (2 √(2Φ_F + V_SB)) — body effect

### 3.2 채널 길이 변조 (Channel Length Modulation)

VDS 가 커지면 *pinch-off* 지점이 source 쪽으로 이동 → effective channel 짧아짐 → ID 약간 증가. 1 + λVDS 의 *λ* 가 그 정도.

**의미**: *output impedance 가 무한대가 아니다* — finite ro. gain `gm·ro` 가 한계.

### 3.3 Body Effect

소스 ↔ 기판 간 전압 (VSB) 가 0 이 아닐 때 *VTH(threshold voltage, 트랜지스터가 켜지기 시작하는 문턱 전압) 가 증가*. Cascode(트랜지스터를 위아래로 쌓아 출력 저항·이득을 높이는 구성) 또는 stack 회로에서 흔히 발생.

$$ V_{TH} = V_{TH0} + \gamma (\sqrt{2\Phi_F + V_{SB}} - \sqrt{2\Phi_F}) $$

### 3.4 Latch-Up

**Latch-up**(래치업 — CMOS 내부에 기생적으로 생긴 SCR(Silicon-Controlled Rectifier, 한 번 켜지면 스스로 계속 켜져 큰 전류를 흘리는 4층 소자)이 trigger되어 칩이 타버리는 현상)입니다. CMOS 의 *p-substrate + n-well + p+ source* 가 parasitic *p-n-p-n* SCR 을 형성. 한 번 trigger 되면 high current 가 흘러 *chip 소손*.

**방지**:
- Guard ring (n+ in p-substrate, p+ in n-well) — 누설 전류 우회
- Substrate / well 강한 contact — beta 낮춤
- Latch-up test (JEDEC JESD78): I/O 에 over-voltage / over-current 인가 후 정상 복귀 확인

---

## 4. Bandgap Reference

**Bandgap reference**(밴드갭 기준전압 — 온도가 변해도 거의 일정한 ~1.2V 기준 전압을 만드는 회로; 온도에 따라 반대로 변하는 두 성분을 더해 상쇄)는 ADC·LDO 등의 기준이 됩니다. 재료는 **BJT**(Bipolar Junction Transistor, MOSFET과 다른 종류의 트랜지스터로 그 `Vbe`가 온도에 잘 정의된 의존성을 가짐)입니다.

### 4.1 PTAT + CTAT 결합

- **CTAT** (Complementary to Absolute Temperature, 절대온도에 반비례) — `Vbe`(BJT의 베이스-에미터 전압) 가 T 증가 시 *감소* (-2 mV/°C 정도).
- **PTAT** (Proportional to Absolute Temperature, 절대온도에 비례) — 두 BJT 의 *ΔVbe* 가 T 에 비례 (서로 다른 전류 밀도).

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

전원 회로는 입력 전압을 회로가 필요로 하는 다른 전압으로 바꿉니다. **Switching converter**(스위칭 컨버터 — 스위치를 빠르게 켰다 껐다 하며 인덕터/커패시터로 전압을 변환 — 효율이 높음)와 **LDO**(Low-Dropout regulator, 스위칭 없이 전압을 떨어뜨리는 선형 레귤레이터 — 출력이 깨끗하지만 효율은 낮음)가 두 축입니다. **topology**(토폴로지 — 회로 소자들의 연결 구조/방식)에 따라 Buck/Boost 등으로 나뉩니다.

### 5.1 Topology 한 줄

표의 **Buck**(step-down, 전압을 낮춤), **Boost**(step-up, 전압을 높임), **switch**(스위치 — 빠르게 도통/차단하는 트랜지스터), **diode**(다이오드 — 한 방향으로만 전류를 흘리는 소자), **dropout**(LDO가 정상 동작하는 데 필요한 최소 Vin−Vout 차이)을 먼저 알아 둡니다.

| Converter | Vin → Vout | 핵심 |
|-----------|------------|------|
| **Buck** | 높은 V → 낮은 V (step-down) | High-side switch + diode + L + C |
| **Boost** | 낮은 V → 높은 V (step-up) | Low-side switch + diode + L + C |
| **Buck-Boost** | 양방향 (Vout > 또는 < Vin) | inverted 또는 SEPIC topology |
| **LDO** | 작은 dropout 으로 step-down | Pass transistor + 피드백 (스위칭 없음) |

### 5.2 CCM / DCM / BCM

스위칭 컨버터는 부하 전류에 따라 세 가지 동작 모드 중 하나로 구동됩니다. **CCM** 은 스위칭 주기 내내 inductor 전류가 0 이하로 내려가지 않는 상태로, 중부하~고부하 구간에서 ripple 이 작고 효율이 좋습니다. 부하가 줄어들면 inductor 전류의 ripple 범위가 상대적으로 커지다가 결국 **DCM** 으로 진입합니다. DCM 에서는 inductor 전류가 매 사이클마다 0 까지 내려갔다가 다시 올라오는데, 이 구간에는 스위치 동작이 없으므로 경부하에서의 효율이 오히려 높아집니다. 대신 전달 함수가 달라져 control 설계가 복잡해집니다. **BCM** (Boundary Conduction Mode) 은 정확히 0 에 도달하는 순간 다음 스위칭을 시작하는 경계 상태로, 주파수가 부하에 따라 가변됩니다.

- **CCM** (Continuous Conduction Mode) — Inductor 전류가 *0 아래로 안 내려감*. High load 에서. 효율 좋음, ripple 작음.
- **DCM** (Discontinuous Conduction Mode) — Inductor 전류가 *0 까지 내려감*. Light load. 효율은 light load 에서 좋음, control 복잡.
- **BCM** (Boundary Conduction Mode) — 정확히 0 에 도달 시 다음 스위칭. Variable freq.

### 5.3 Buck 의 Duty Cycle (CCM)

**Duty cycle**(듀티 사이클 `D` — 한 스위칭 주기에서 스위치가 켜져 있는 시간의 비율; 출력 전압을 정하는 손잡이)입니다.

$$ \frac{V_{out}}{V_{in}} = D \quad \text{(buck)} $$

$$ \frac{V_{out}}{V_{in}} = \frac{1}{1-D} \quad \text{(boost)} $$

### 5.4 Compensation (Type II / Type III)

스위칭 컨버터의 control loop:
- **Voltage mode** — Vout 만 sense, type-III compensation (3 pole + 2 zero) 필요.
- **Current mode (peak/avg)** — Inductor 전류도 sense, type-II (1 pole + 1 zero) 로 충분. 응답 빠름.

### 5.5 Dead-time

**Dead-time**(데드타임 — 위/아래 스위치가 동시에 켜져 전원이 단락(shoot-through, 관통 전류)되는 것을 막으려 둘 다 끄는 짧은 구간)이 그 안전장치입니다. High-side 와 low-side switch 가 *동시에 켜지면 short → shoot-through current*. Dead-time 으로 둘 다 off 인 짧은 구간 보장.

**디테일**: Dead-time 이 너무 길면 *body diode(트랜지스터에 기생하는 다이오드) 통해 전류 흐름 → 효율 저하 + EMI(Electromagnetic Interference, 회로가 내뿜는 전자기 간섭 잡음)*.

### 5.6 GaN vs Si — 인터뷰 핵심

스위치 소자의 재료 비교입니다. **Si**(Silicon, 실리콘 — 전통적이고 저렴한 MOSFET 재료), **GaN**(Gallium Nitride, 갈륨 나이트라이드 — 더 빠르고 효율 높지만 비싼 차세대 재료; **HEMT**는 그 트랜지스터 구조), **Rdson**(켜졌을 때의 채널 저항 — 작을수록 도통 손실 적음), **Qg**(게이트 충전 전하 — 작을수록 빠른 스위칭)이 비교 지표입니다.

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

```d2
direction: down
Vin -> PT: S/D
PT.label: "Pass Transistor\n(PMOS/NMOS)"
PT -> Vout
Vout -> Load
Vout -> FB
FB.label: "Feedback divider"
FB -> EA
EA.label: "Error Amp"
Vref -> EA
Vref.label: "Vref (bandgap)"
EA -> PT: G
```

위 그림의 구성요소: **pass transistor**(패스 트랜지스터 — 입력에서 출력으로 전류를 흘리며 그 저항을 조절해 출력 전압을 잡는 소자), **error amp**(오차 증폭기 — 출력과 기준전압의 차이를 증폭해 pass transistor를 제어하는 op-amp), **feedback divider**(피드백 분압기 — 출력 전압을 저항으로 나눠 기준과 비교할 값을 만듦)입니다.

### 6.2 PMOS vs NMOS pass

LDO 의 pass transistor 로 PMOS 를 쓸지 NMOS 를 쓸지는 dropout 전압, 회로 복잡도, PSRR 간의 트레이드오프입니다. PMOS 는 게이트를 출력보다 낮게 구동하기만 하면 되므로 추가 공급 전원 없이 단순하게 구성되고 dropout 도 수십 mV 수준으로 매우 낮습니다. 반면 NMOS 는 소스가 출력단에 연결되므로 게이트를 `Vin + Vgs` 수준으로 높여야 해 charge pump 나 추가 supply 가 필요하지만, PSRR 이 높아 고주파 노이즈 차폐 성능이 좋습니다.

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

LDO 는 *부하 cap (Cload) 의 ESR(Equivalent Series Resistance, 커패시터에 딸린 기생 직렬 저항)* 이 zero(전달함수에서 gain을 다시 끌어올리는 주파수 지점)를 만들어 안정성 결정.
- ESR 너무 작음 (예: 세라믹 cap 0.001Ω) → unstable
- ESR 너무 큼 → ripple 증가

**Modern cap-less LDO** — internal compensation 으로 외부 cap ESR 의존 제거.

---

## 7. Layout — Mismatch Reduction

**Layout**(레이아웃 — 트랜지스터·배선을 칩 위 실제 도형으로 배치하는 단계)에서 **mismatch**(미스매치 — 똑같이 설계한 두 소자가 공정 편차로 실제 특성이 달라지는 것; 아날로그 정밀도를 깎는 주범)를 줄이는 기법들입니다.

아날로그 회로의 정밀도는 결국 소자 간 *매칭* 품질에 달려 있습니다. 동일하게 설계된 두 트랜지스터라도 공정 편차(process gradient), 가장자리 효과, 도펀트 분포 차이로 인해 실제 특성이 달라질 수 있습니다. 이를 최소화하기 위한 레이아웃 기법 세 가지를 살펴봅니다.

### 7.1 Common-Centroid

두 trans 의 평균이 *같은 무게중심* 에 오도록 *교차* 배치. Process gradient (e.g. oxide thickness 변화) 평균 제거.

```
A B B A     A 2개, B 2개의 무게중심 동일
B A A B
```

### 7.2 Interdigitated (or finger)

긴 transistor 를 *작은 finger 여러 개* 로 나누고 두 트랜지스터의 finger 가 *교차*되도록 배치합니다. Common-centroid 의 단순 1D 버전으로, 한 방향의 process gradient 를 평균화하는 효과가 있습니다.

### 7.3 Dummy device

배열의 *가장자리*에는 실제로 동작하지 않는 dummy 소자를 추가합니다. 가장자리 트랜지스터는 etch 균일도와 dopant proximity 효과가 내부 트랜지스터와 달라 특성이 틀어지기 쉬운데, dummy 가 그 *가장자리 위치*를 대신 맡아줌으로써 실제 동작하는 트랜지스터들이 모두 동일한 주변 환경에 놓이게 됩니다.

### 7.4 Guard ring

n+ in p-sub (또는 반대) ring 으로 회로를 둘러쌈. *substrate noise* 와 *latch-up* 동시 방지.

---

## 8. 샘플 인터뷰 Q&A

<details>
<summary>Q1. (Compute) Inverting amp Vo/Vin = -Rf/Rin. Rf=10k, Rin=1k, Vin=0.5V. Vo=?</summary>

`Vo = -(10k/1k) · 0.5 = -5V`. Power rail 이 ±5V 이상이면 OK, 그보다 작으면 saturation.

</details>
<details>
<summary>Q2. (Explain) Channel length modulation 이 *DC gain* 에 미치는 영향?</summary>

Small-signal gain `Av = -gm · (ro || R_load)`.
채널 변조가 *없으면* ro = ∞ → gain 이 R_load 만으로 결정.
실제로는 ro 가 *유한* → gain 이 *gm·ro* 로 제한. Cascode 로 ro 증가시켜 보상.

</details>
<details>
<summary>Q3. (Design) 1.2V bandgap 의 *온도 1차 미분이 0* 이 되는 조건?</summary>

`Vref = Vbe + α · ΔVbe`
Vbe 의 ∂T = −2 mV/°C, ΔVbe 의 ∂T = +0.085 mV/°C (대략).
α = 2 / 0.085 ≈ 23.5 일 때 합산 미분 = 0.

</details>
<details>
<summary>Q4. (Compare) Buck CCM vs DCM 의 efficiency 곡선?</summary>

- **CCM** — Heavy load 에서 효율 *최대*. Light load 에서 *switching loss* 가 conduction loss 보다 크게 차지하면서 효율 ↓.
- **DCM** — Light load 에서 *switching loss 감소* (전류 0 일 때 switch 안 함) → 효율 ↑. Heavy load 에서는 RMS current 가 커서 효율 ↓.
- 현대 컨버터는 *light load 자동 DCM 전환* (PFM, Pulse Skipping) 으로 두 영역 모두 최적.

</details>
<details>
<summary>Q5. (Evaluate) LDO 와 Buck — 5V → 3.3V 변환에 어느 게 좋은가?</summary>

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

**결론**: 디지털 main 은 Buck, sensitive analog block (PLL(Phase-Locked Loop, 기준 클럭에 위상을 맞춰 안정된 주파수를 만드는 회로)의 VCO(Voltage-Controlled Oscillator, 전압으로 주파수를 조절하는 발진기), ADC(Analog-to-Digital Converter, 아날로그를 디지털로 바꾸는 변환기) reference) 은 LDO 로 cascade(여러 단을 직렬로 이어 붙임).

</details>
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
- [Unit 5 퀴즈](../quiz/05_analog_mixed_signal_quiz/) 로 자기 점검
