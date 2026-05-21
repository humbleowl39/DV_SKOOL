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

**Q2.** σ(ΔVth) = AVT / sqrt(W × L).

**Q3.** DRAM은 10⁹ ~ 10¹⁰ cell. 6-sigma 의 fail probability 2×10⁻⁹ 정도 → 칩당 fail cell이 redundancy로 repair 가능한 수준 (~수십 ~ 수백 cell).

**Q4.** MGG (Metal Gate Granularity), LER (Line Edge Roughness), RDF (Random Dopant Fluctuation)가 dominant variability source가 됨 — Pelgrom의 sqrt(WL) 모델 외 추가 변동.

**Q5.** sqrt(0.5 × 0.1) = sqrt(0.05) ≈ 0.224 μm. σ(ΔVth) = 4 / 0.224 ≈ **17.9 mV**.

**Q6.** 100 / 18 ≈ 5.56 σ. Q(5.56) × 2 ≈ 2.7 × 10⁻⁸. 10⁹ × 2.7×10⁻⁸ ≈ **27 cell**.

**Q7.** ① 같은 SA × 1000회 = 한 SA의 내부 noise/timing 분포 (instance-specific) → 통계 무의미 (offset 분포 본 게 아님). ② 1000개 다른 instance = mismatch 모집단의 statistical sample → fail rate 추정 가능 (의도한 Monte Carlo).

**Q8.** σ → σ/√4 = σ/2 = 9 mV. 100/9 = 11σ → P(fail) ≈ ~10⁻²⁸ → 사실상 fail 없음. **Trade-off**: ① Area 4× 증가 (DRAM density 손실) ② Cell capacitance 등 다른 parameter 영향 ③ Layout 복잡도 증가. 실제로는 **size 증가 + sense margin 조정 + offset calibration** 조합 사용.

[← 퀴즈 인덱스](index.md) · [본문 ↗](../09_deepdive_sense_amp_offset.md)
