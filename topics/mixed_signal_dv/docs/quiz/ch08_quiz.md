# Ch08 퀴즈 — IO Buffer · IBIS-AMI

## Q1. (Remember)
IO buffer의 5가지 핵심 특성을 나열하시오.

## Q2. (Remember)
IBIS 7.0에서 추가된 두 가지 핵심 기능은?

## Q3. (Understand)
ZQ calibration이 왜 주기적으로 필요한지 설명하시오.

## Q4. (Understand)
Reflection coefficient Γ = 0이 되는 조건은?

## Q5. (Apply)
VDDQ=1.1V, R_pu=34Ω, ODT=60Ω, VTT=0.55V에서 data='1' 시 DQ voltage를 계산하시오.

## Q6. (Apply)
Slew rate 3 V/ns로 6.4 Gbps (UI=156 ps), full swing 1.1V를 전송할 때 eye 가능 여부를 판단하시오.

## Q7. (Analyze)
DDR5 같은 high-speed IO에서 단순 RNM driver/ODT 모델로 부족한 이유 3가지를 분석하시오.

## Q8. (Evaluate)
ODT를 60Ω 대신 120Ω으로 늘렸을 때 voltage swing과 reflection에 어떤 영향이 있을지 평가하시오.

---

## 정답 및 해설

**Q1.** Driver strength · slew rate · output impedance(Z_out) · ODT · ZQ calibration.

**Q2.** ① PAM modulation 지원 ② Back-channel link training.

**Q3.** Driver/ODT 저항이 process variation과 temperature drift로 변동 → 외부 정밀 ZQ pin 240Ω을 기준으로 주기적 재보정하여 임피던스 정확도 유지.

**Q4.** R_load = Z0 (load impedance가 transmission line characteristic impedance와 같을 때).

**Q5.**
```
(1.1 - V_DQ)/34 = (V_DQ - 0.55)/60
60(1.1 - V_DQ) = 34(V_DQ - 0.55)
84.7 = 94·V_DQ
V_DQ ≈ 0.901 V
```

**Q6.** 천이 시간 = 1.1 / 3 = **367 ps** > 156 ps → 한 UI 안에 천이 불가 → **eye 닫힘**. 더 빠른 slew (≥ 7~8 V/ns) 필요.

**Q7.** ① RX equalizer (CTLE/DFE) 표현 불가 ② Channel(PCB+package) 통과 후 ISI를 BER 1e-12 수준에서 검증 불가 ③ Back-channel link training 표현 불가. → IBIS-AMI 표준 모델 필요.

**Q8.** Voltage swing: ODT ↑ → divider 비율 변화로 swing 약간 감소 (driver Vs ODT 사이의 임피던스 비). Reflection: ODT(120Ω) ≠ Z0(50Ω) → Γ ≈ (120-50)/(120+50) ≈ 0.41 → reflection 증가. **결론**: 60Ω이 Z0=50Ω에 더 가까워 reflection 우수, 120Ω은 power 절감 가능하나 SI 손실.

[← 퀴즈 인덱스](index.md) · [본문 ↗](../08_deepdive_io_buffer_rnm.md)
