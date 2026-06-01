# Ch09 퀴즈 — Sense Amp Offset · Pelgrom · Monte Carlo

## Q1. (Remember)
SA offset의 3가지 source를 쓰시오.

## Q2. (Remember)
Pelgrom's law의 표준편차 공식은?

## Q3. (Understand)
DRAM이 6-sigma yield 기준을 사용하는 이유를 설명하시오.

## Q4. (Understand)
5nm 이하 노드에서 단순 Pelgrom 공식이 한계인 이유는?

## Q5. (Apply)
AVT = 4 mV·μm, W = 0.5 μm, L = 0.1 μm 조건에서 σ(ΔVth)를 계산하시오.

## Q6. (Apply)
σ = 18 mV, signal = 100 mV 조건에서 10⁹ cell 중 fail 개수를 추정하시오.

## Q7. (Analyze)
같은 SA의 Monte Carlo를 1000회 돌리는 것과 1000개 다른 SA instance를 돌리는 것의 차이를 분석하시오.

## Q8. (Evaluate)
Transistor size를 4배 늘리면 fail rate가 어떻게 변하며, 이 trade-off를 평가하시오.

---

## 정답 및 해설

**Q1.** ① Random mismatch (Pelgrom — Vth, β) ② Systematic mismatch (layout 비대칭) ③ Operating conditions (VDD, temperature, substrate noise).

세 가지 소스를 구분하는 것이 중요한 이유는 대응 방법이 각각 다르기 때문이다. Random mismatch는 Pelgrom의 법칙에 따라 transistor size를 키우면 줄일 수 있다. Systematic mismatch는 layout 단계에서 대칭 배치와 dummy 추가로 제어한다. Operating condition 변동은 supply voltage margin, 온도 range, substrate shielding 등으로 대응한다. 세 소스 모두를 동시에 고려하지 않으면 충분한 yield가 보장되지 않는다.

**Q2.** σ(ΔVth) = AVT / sqrt(W × L).

이 공식은 Pelgrom의 1989년 논문에서 제시된 관계로, transistor matching의 통계적 표준편차를 예측한다. AVT(mismatch parameter)는 공정에서 결정되는 상수이고, W와 L은 각각 채널 폭과 길이다. 중요한 점은 면적(W×L)의 제곱근에 반비례한다는 것인데, 이는 transistor를 4배 크게 만들면 σ가 절반으로 줄어든다는 것을 의미한다.

**Q3.** DRAM은 10⁹ ~ 10¹⁰ cell. 6-sigma 의 fail probability 2×10⁻⁹ 정도 → 칩당 fail cell이 redundancy로 repair 가능한 수준 (~수십 ~ 수백 cell).

6σ 기준은 DRAM 셀 수와 repair capacity를 고려한 설계 결정이다. 10⁹개의 cell 각각이 독립적으로 2×10⁻⁹ 확률로 fail한다면 통계적 기대 fail cell 수는 약 2개다. 실제로는 6σ 약간 아래에서도 수십~수백 개가 fail할 수 있지만, DRAM은 spare row/column redundancy를 갖춰 이 수준의 fail은 repair 가능하다. 3σ나 4σ 기준으로는 fail cell이 redundancy capacity를 초과하여 칩 전체가 불량이 된다.

**Q4.** MGG (Metal Gate Granularity), LER (Line Edge Roughness), RDF (Random Dopant Fluctuation)가 dominant variability source가 됨 — Pelgrom의 sqrt(WL) 모델 외 추가 변동.

5 nm 이하 노드에서는 트랜지스터의 채널에 도핑된 원자 수가 수십 개 수준으로 줄어들어 양자역학적 fluctuation이 지배적이 된다. 또한 fin/gate 패터닝의 가장자리 거칠기(LER)와 금속 게이트 결정립 크기(MGG)가 Vth 변동의 주된 원인이 된다. 이들은 Pelgrom의 1/sqrt(WL) 스케일링을 따르지 않아 기존 모델만으로는 충분히 설명되지 않는다.

**Q5.** sqrt(0.5 × 0.1) = sqrt(0.05) ≈ 0.224 μm. σ(ΔVth) = 4 / 0.224 ≈ **17.9 mV**.

공식 적용 시 단위를 일관되게 유지하는 것이 중요하다. W = 0.5 μm, L = 0.1 μm이므로 W×L = 0.05 μm², sqrt(0.05) ≈ 0.224 μm이다. AVT = 4 mV·μm를 sqrt(WL)로 나누면 약 17.9 mV가 나온다. 이 값은 Q6의 σ = 18 mV와 사실상 같은 수치이다.

**Q6.** 100 / 18 ≈ 5.56 σ. Q(5.56) × 2 ≈ 2.7 × 10⁻⁸. 10⁹ × 2.7×10⁻⁸ ≈ **27 cell**.

signal(100 mV)을 σ(18 mV)로 나누면 5.56σ 위치다. 가우시안 분포에서 5.56σ 이상의 tail 확률은 약 1.35×10⁻⁸이고, 양쪽 tail을 합치면 2.7×10⁻⁸이다. 이것이 한 cell의 fail probability이며, 10⁹ cell에 곱하면 약 27 cell이 예상 fail 수다. 이 계산이 DRAM yield 예측의 핵심 과정이다.

**Q7.** ① 같은 SA × 1000회 = 한 SA의 내부 noise/timing 분포 (instance-specific) → 통계 무의미 (offset 분포 본 게 아님). ② 1000개 다른 instance = mismatch 모집단의 statistical sample → fail rate 추정 가능 (의도한 Monte Carlo).

이 차이는 통계적으로 매우 중요하다. 같은 회로를 같은 파라미터로 1000번 돌리면 결과가 매번 같거나 noise만 달라지므로 offset 분포를 볼 수 없다. Monte Carlo의 목적은 fabrication 시 transistor 파라미터 변동을 가상으로 샘플링하는 것이므로, 각 run에서 Pelgrom 분포를 따르는 서로 다른 Vth offset을 주입한 1000개의 다른 instance를 시뮬레이션해야 한다.

**Q8.** σ → σ/√4 = σ/2 = 9 mV. 100/9 = 11σ → P(fail) ≈ ~10⁻²⁸ → 사실상 fail 없음. **Trade-off**: ① Area 4× 증가 (DRAM density 손실) ② Cell capacitance 등 다른 parameter 영향 ③ Layout 복잡도 증가. 실제로는 **size 증가 + sense margin 조정 + offset calibration** 조합 사용.

Pelgrom의 법칙에 따라 size 4배 증가 → σ가 절반인 9 mV로 줄어든다. 100/9 ≈ 11σ에서 fail probability는 극도로 낮아져 사실상 0이다. 그러나 DRAM에서 SA size 4배 증가는 cell array 면적의 상당 부분을 차지하는 SA 전체를 4배로 키운다는 의미이므로 die size와 제조 비용에 직접적인 영향을 준다. 이 때문에 실제 DRAM 설계는 transistor sizing, signal margin 조정, SA offset calibration 회로 추가를 복합적으로 사용하여 최소 면적에서 원하는 yield를 달성한다.

[← 퀴즈 인덱스](index.md) · [본문 ↗](../09_deepdive_sense_amp_offset.md)
