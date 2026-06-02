---
title: "Quiz — Unit 5: Analog / Mixed-Signal"
---

[← Unit 5 본문으로 돌아가기](../../05_analog_mixed_signal/)

---

## Q1. (Compute)

Inverting op-amp 에서 Rf = 100 kΩ, Rin = 10 kΩ, Vin = +0.2V. Vout 은?

<details>
<summary>정답 / 해설</summary>

`Vout = −(Rf / Rin) × Vin = −(100k / 10k) × 0.2 = −2V`.

Inverting 구성에서 음의 피드백을 통해 V⁻ ≈ V⁺ = 0V(가상 단락)가 성립하므로 Rin에 흐르는 전류가 Rf에도 같은 방향으로 흐르고, 그 결과 출력 극성이 반전된다. 계산 결과 −2V가 실제로 유효하려면 op-amp의 power rail(예: ±5V 공급)이 −2V를 포함해야 한다. rail이 ±1.5V라면 출력이 negative rail에 saturation되어 −2V를 출력하지 못하고 선형 동작이 깨진다.

</details>
## Q2. (Remember)

NMOS small-signal model 에서 transconductance `gm` 의 정의는?

<details>
<summary>정답 / 해설</summary>

`gm = ∂I_D / ∂V_GS` (V_DS 고정).

Saturation 영역에서 `gm = μ_n C_ox (W/L)(V_GS − V_TH) = 2I_D / (V_GS − V_TH) = √(2 μ_n C_ox (W/L) I_D)`.

gm은 small-signal 입력(V_GS 변화)이 출력(drain current)으로 얼마나 효율적으로 변환되는지를 나타내는 핵심 파라미터다. gm이 클수록 같은 게이트 전압 변화로 더 많은 전류 변화를 만들어 증폭기의 gain `A_v = −gm × R_D`가 높아진다. W/L 비율을 키우거나 bias 전류를 높이면 gm이 증가하지만, 그에 따라 기생 커패시턴스도 늘어나 주파수 특성이 악화되는 trade-off가 있다.

</details>
## Q3. (Explain)

Channel length modulation 이 small-signal gain `A_v = −gm · (r_o ‖ R_L)` 에 미치는 영향은?

<details>
<summary>정답 / 해설</summary>

이상적인 MOSFET이라면 포화 영역에서 V_DS가 변해도 I_D가 변하지 않아 r_o = ∞가 된다. 그러면 gain `A_v = −gm × R_L`이고 R_L만 키우면 gain도 무한정 늘릴 수 있다. 그러나 실제로는 channel length modulation 효과로 r_o = 1/(λI_D)의 유한한 값을 가진다. 유효 부하 저항이 `R_L ‖ r_o`로 줄어들기 때문에 R_L을 아무리 크게 키워도 gain은 `gm × r_o`(intrinsic gain)에 수렴한다. 이 한계를 극복하려면 **cascode** 구조를 사용해 출력 임피던스를 gm×r_o² 수준으로 올리거나, differential pair와 current mirror를 결합해 유효 r_o를 높인다.

</details>
## Q4. (Design)

Bandgap reference 에서 *Vref ≈ 1.2V* 가 나오는 *물리적 근거* 는?

<details>
<summary>정답 / 해설</summary>

Vbe(T)는 온도에 따라 감소하는 CTAT 특성을 갖는다. T = 0 K로 외삽(extrapolation)하면 실리콘의 bandgap energy `E_g ≈ 1.12 eV`에 해당하는 약 1.205V에 수렴한다. Bandgap reference 회로는 CTAT 성분(Vbe)과 PTAT 성분(ΔVbe)을 적절한 비율로 합산해 온도 계수의 1차 항이 0이 되는 지점을 만드는데, 그 합이 바로 이 외삽 값인 ~1.2V다. 이 값은 회로 파라미터가 아니라 실리콘의 물리적 특성에서 유래하므로, 어떤 Si CMOS 공정에서 설계하더라도 bandgap reference 출력은 ~1.2V 근방에 수렴한다. GaAs(~1.42V), SiC(~3.26V) 등 다른 반도체는 bandgap energy가 다르므로 기준 전압도 달라진다.

</details>
## Q5. (Compare)

LDO 의 PMOS pass 와 NMOS pass — *dropout voltage* 측면 비교?

<details>
<summary>정답 / 해설</summary>

**PMOS pass** — source가 Vin에 연결되고 gate를 낮춰서 turn-on하므로, 최소 dropout은 PMOS의 `V_SD(sat) ≈ Rds(on) × I_load`만큼이다. PMOS의 Rds(on)이 낮으면 수십 mV의 매우 작은 dropout이 가능하다. 배터리나 저전압 SoC에서 최소 dropout이 핵심인 경우 PMOS pass가 표준 선택이다.

**NMOS pass** — source가 Vout에 연결되고 turn-on을 위해 gate 전압이 `Vout + V_GS`까지 올라가야 한다. 이 전압은 Vin보다 높아야 하므로 charge pump나 별도 high-supply rail이 필요하고, 구현 복잡도와 dropout이 올라간다. 그러나 NMOS는 넓은 주파수 대역에서 PSRR(전원 잡음 제거비)이 우수해 NMOS pass LDO가 노이즈 성능 우선 애플리케이션에 쓰이기도 한다.

</details>
## Q6. (Apply)

CCM Buck 컨버터: Vin = 12V, Vout = 5V. Duty cycle D 는?

<details>
<summary>정답 / 해설</summary>

`Vout / Vin = D → D = 5/12 ≈ 0.417 = 41.7%`.

이 식은 CCM Buck 컨버터의 *volt-second balance*에서 유도된다. 스위치가 켜진 동안(DT) 인덕터 전압은 `Vin − Vout`이고 꺼진 동안((1−D)T)에는 `−Vout`이다. 정상 상태에서 한 주기 동안 인덕터 전류 변화의 합이 0이어야 하므로 `(Vin − Vout)·D = Vout·(1−D)`가 성립하고 정리하면 `Vout = D × Vin`이 된다. 실제 회로에서는 스위치 Vds(on) 전압 강하와 인덕터의 DC 저항(DCR) 손실로 인해 같은 출력 전압을 얻으려면 이상적 값보다 D가 약간 더 커야 한다.

</details>
## Q7. (Analyze)

Layout 에서 *common-centroid* 배치가 mismatch 를 줄이는 메커니즘은?

<details>
<summary>정답 / 해설</summary>

웨이퍼 표면의 process gradient(산화막 두께, 도핑 농도 등)는 공간적으로 거의 선형 분포를 가진다. 즉 어떤 파라미터 P(x, y) ≈ P₀ + αx + βy로 근사된다. 두 소자 A와 B의 무게중심이 동일하면 두 소자가 경험하는 P의 공간 평균이 같아져 1차 gradient 항에 의한 mismatch가 상쇄된다. 남는 오차는 2차 항(curvature)뿐이므로, 동일한 면적 소자로 단순히 인접 배치하는 것보다 훨씬 낮은 ratio error를 달성할 수 있다.

```
A B B A    A 2 finger, B 2 finger
B A A B    무게중심 ≡
```
이처럼 교차 배열로 무게중심을 일치시키는 것이 common-centroid의 핵심이다. current mirror, differential pair, DAC 커패시터 등 비율 정확도가 중요한 모든 소자에 적용된다.

</details>
## Q8. (Evaluate)

5V → 3.3V 변환에 *Buck 컨버터* vs *LDO* — 어느 것이 *센서 ADC reference* 에 더 적합한가?

<details>
<summary>정답 / 해설</summary>

**LDO**. ADC reference 전압의 noise는 비트 단위 분해능에 직접 영향을 미친다. Buck 컨버터의 스위칭 리플(수백 mV 수준이 필터 이후에도 수 mV 잔존)은 12-bit ADC의 1 LSB(5V/4096 ≈ 1.2mV)보다 클 수 있어 변환 정확도를 망가뜨린다. LDO는 고주파 PSRR로 VDD 노이즈를 억제하고 스위칭 없이 깨끗한 출력을 제공한다. 5V→3.3V에서 LDO 효율은 66%지만, ADC가 소비하는 전류 자체가 수 mA 수준이므로 절대 손실 전력이 작아 열 문제도 적다. 주 power rail처럼 수백 mA 이상이 흐르는 경우라면 Buck(효율 90%+)이 필수다. 현실의 최선은 **Buck→LDO cascade**: Buck으로 4V 수준까지 효율적으로 내리고 LDO가 최소 dropout으로 3.3V 깨끗하게 다듬는 구조다.

</details>
