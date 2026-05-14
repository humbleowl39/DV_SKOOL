# Quiz — Unit 5: Analog / Mixed-Signal

[← Unit 5 본문으로 돌아가기](../05_analog_mixed_signal.md)

---

## Q1. (Compute)

Inverting op-amp 에서 Rf = 100 kΩ, Rin = 10 kΩ, Vin = +0.2V. Vout 은?

??? answer "정답 / 해설"
    `Vout = −(Rf / Rin) × Vin = −(100k / 10k) × 0.2 = −2V`.

    실제 op-amp 의 power rail (예: ±5V) 안에 들어가야 saturation 없이 작동.

## Q2. (Remember)

NMOS small-signal model 에서 transconductance `gm` 의 정의는?

??? answer "정답 / 해설"
    `gm = ∂I_D / ∂V_GS` (V_DS 고정).

    Saturation: `gm = μ Cox (W/L) (V_GS − V_TH) = 2 I_D / (V_GS − V_TH) = √(2 μ Cox W/L · I_D)`.

## Q3. (Explain)

Channel length modulation 이 small-signal gain `A_v = −gm · (r_o ‖ R_L)` 에 미치는 영향은?

??? answer "정답 / 해설"
    Channel length modulation 으로 *r_o 가 유한* (1/λID). r_o = ∞ 이면 gain 이 R_L 만으로 결정되지만 실제로는 *gm · r_o* 가 *intrinsic gain* 한계. 큰 R_L 을 쓰더라도 r_o 가 작으면 ‖ 연산으로 gain 제한 → **cascode** 로 r_o 증가시켜 gain 확보.

## Q4. (Design)

Bandgap reference 에서 *Vref ≈ 1.2V* 가 나오는 *물리적 근거* 는?

??? answer "정답 / 해설"
    Vbe(T) 를 T = 0 K 로 extrapolation 하면 *Si 의 bandgap energy* `E_g ≈ 1.12 eV / q ≈ 1.205V` 에 도달. PTAT + CTAT 합으로 1차 미분 0 인 지점이 바로 이 extrapolated 값 → 모든 Si 기반 bandgap 이 ~1.2V.

    (GaAs, SiC 등 다른 반도체는 다른 값)

## Q5. (Compare)

LDO 의 PMOS pass 와 NMOS pass — *dropout voltage* 측면 비교?

??? answer "정답 / 해설"
    **PMOS pass** — Source 가 Vin, Gate 를 낮춰 turn-on → dropout 은 *PMOS 의 Rds(on) × I_load* 만큼. 매우 작음 (수십 mV).

    **NMOS pass** — Source 가 Vout, Gate 가 Vout + Vgs 가 되어야 함. 보통 Vin 만으로는 부족 → *charge pump* 또는 *별도 high-supply* 필요. Dropout 더 큼.

    *그러나* NMOS 는 *high freq PSRR 우수* — 두 측면 모두 trade-off.

## Q6. (Apply)

CCM Buck 컨버터: Vin = 12V, Vout = 5V. Duty cycle D 는?

??? answer "정답 / 해설"
    `Vout / Vin = D → D = 5/12 ≈ 0.417 = 41.7%`.

    실제 회로에서는 switch 의 Vds(on) 강하와 inductor DCR 손실로 D 가 약간 더 큼.

## Q7. (Analyze)

Layout 에서 *common-centroid* 배치가 mismatch 를 줄이는 메커니즘은?

??? answer "정답 / 해설"
    Wafer 의 *process gradient* (oxide 두께, dopant 농도 등) 는 *공간적으로 거의 선형* — 즉, 위치 (x, y) 에 비례. 두 transistor 의 *무게중심을 일치* 시키면 두 trans 가 *동일한 평균 영향* 을 받아 ratio mismatch 가 *gradient 의 1차 항* 까지 제거됨. 2차 항 (curvature) 만 남음.

    조합:
    ```
    A B B A    A 2 finger, B 2 finger
    B A A B    무게중심 ≡
    ```

## Q8. (Evaluate)

5V → 3.3V 변환에 *Buck 컨버터* vs *LDO* — 어느 것이 *센서 ADC reference* 에 더 적합한가?

??? answer "정답 / 해설"
    **LDO**. ADC reference 는 *noise 가 결과 정확도에 직접 영향* → switching noise (Buck) 는 치명적. LDO 의 *깨끗한 출력 + 높은 PSRR* 이 필요. 효율 손실 (5V→3.3V → 66%) 은 ADC 소비 전류가 작아 절대 손실이 적음.

    *주 power rail* 이라면 Buck (효율 90%+) 가 더 적합. **현실: Buck → LDO cascade** — Buck 으로 4V 까지 효율적으로 내리고, LDO 로 3.3V 까지 깨끗하게 다듬는다.
