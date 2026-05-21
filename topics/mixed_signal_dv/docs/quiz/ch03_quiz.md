# Ch03 퀴즈 — SPICE / Fast SPICE 기초

## Q1. (Remember)
SPICE가 푸는 3가지 기본 법칙을 쓰시오.

## Q2. (Remember)
SPICE 5종 분석 명령을 나열하시오.

## Q3. (Understand)
Newton-Raphson 반복법이 SPICE에 왜 필요한지 설명하시오.

## Q4. (Understand)
BSIM이 단순 스위치 모델과 다른 점 3가지를 쓰시오.

## Q5. (Apply)
CMOS 인버터 SPICE netlist에서 `M1 out in vdd vdd pmos w=4u l=0.028u`의 5개 노드/파라미터를 해석하시오.

## Q6. (Apply)
다음 회로의 시뮬레이션이 어떤 패러다임에 적합한지 결정하시오 (정량 추정):
- 1만 트랜지스터, 1 μs sim, 1 ps step.

## Q7. (Analyze)
SPICE `.op` 수렴 실패 시 시도할 수 있는 3가지 대응을 분석하시오.

## Q8. (Evaluate)
Fast SPICE 5가지 가속 기법 중 DRAM cell array 검증에 가장 효과적인 것은 무엇이며 그 이유는?

---

## 정답 및 해설

**Q1.** ① KCL (Kirchhoff's Current Law) ② KVL (Kirchhoff's Voltage Law) ③ Element law (V-I 관계).

**Q2.** `.op`, `.dc`, `.ac`, `.tran`, `.noise` (또는 `.mc` Monte Carlo, `.PSS/HB`).

**Q3.** MOSFET I-V는 매우 비선형이라 선형 시스템처럼 한 번에 풀 수 없음 → 반복 근사로 해를 수렴시키는 과정이 필요.

**Q4.** ① Threshold voltage Vth ② Channel length modulation ③ Subthreshold conduction (또는 short-channel effect, body effect, velocity saturation 등).

**Q5.** M1 = MOSFET 이름; out = drain; in = gate; vdd = source; vdd = bulk; pmos = model name; w=4u l=0.028u = 채널 width 4μm, length 28nm.

**Q6.** 1만 trans × 10⁶ step × cost ~ N^1.5 → ~10¹¹ → 수 시간. **Fast SPICE 필요** (일반 SPICE는 며칠).

**Q7.** ① `.ic` 명령으로 초기 노드 voltage 명시 ② Source ramp-up (전원을 0→VDD로 천천히) ③ `.option reltol=1e-3 abstol=1e-12` 완화 ④ 회로 안정성 점검 (latch-up 등).

**Q8.** **Hierarchical isomorphism** — DRAM cell이 수 억 개 동일 회로 → 한 번만 풀고 나머지는 재활용 → 메모리·시간 모두 절약. 다른 기법보다 DRAM array에 압도적 효과.

[← 퀴즈 인덱스](index.md) · [본문 ↗](../03_spice_fundamentals.md)
