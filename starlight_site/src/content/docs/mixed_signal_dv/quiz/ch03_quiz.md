---
title: "Ch03 퀴즈 — SPICE / Fast SPICE 기초"
---

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

SPICE는 회로를 노드와 소자로 분해한 뒤 이 세 법칙을 연립 방정식으로 세워 수치 해를 구한다. KCL은 "한 노드에 들어오는 전류의 합 = 0", KVL은 "루프 전압의 합 = 0"이며, Element law는 각 소자(저항, 캐패시터, MOSFET 등)의 V-I 관계식이다. 세 가지가 빠짐없이 필요한 이유는 어느 하나만으로는 회로를 완전히 기술할 수 없기 때문이다.

**Q2.** `.op`, `.dc`, `.ac`, `.tran`, `.noise` (또는 `.mc` Monte Carlo, `.PSS/HB`).

이 5가지는 SPICE의 표준 분석 명령이다. `.op`는 직류 동작점 계산, `.dc`는 sweep 분석, `.ac`는 소신호 주파수 특성, `.tran`은 시간 영역 과도 분석, `.noise`는 잡음 해석이다. `.mc`(Monte Carlo)와 `.PSS`/`.HB`(Periodic Steady-State, Harmonic Balance)는 확장 명령이며, 기본 5종이 더 표준적이다.

**Q3.** MOSFET I-V는 매우 비선형이라 선형 시스템처럼 한 번에 풀 수 없음 → 반복 근사로 해를 수렴시키는 과정이 필요.

저항만 있는 선형 회로라면 연립방정식을 행렬로 한 번에 풀 수 있다. 그러나 MOSFET의 드레인 전류는 게이트/드레인 전압의 비선형 함수이므로, 현재 전압으로 I-V 관계를 선형화(야코비안 행렬)하고 그 해로 전압을 업데이트하는 반복 과정이 필요하다. 해가 충분히 변하지 않으면 수렴했다고 판단하고 종료한다.

**Q4.** ① Threshold voltage Vth ② Channel length modulation ③ Subthreshold conduction (또는 short-channel effect, body effect, velocity saturation 등).

단순 스위치 모델은 Vgs > Vth이면 도통, 아니면 차단의 2-state 근사에 불과하다. 반면 BSIM은 Vth가 Vds·바디 전압·채널 길이에 따라 변하고(short-channel effect), 채널 길이가 짧으면 출력 임피던스가 유한하며(channel length modulation), Vgs < Vth에서도 미약한 전류가 흐르는(subthreshold conduction) 효과를 모두 포착한다. 이 차이가 sub-28 nm 회로 시뮬레이션에서 결정적이다.

**Q5.** M1 = MOSFET 이름; out = drain; in = gate; vdd = source; vdd = bulk; pmos = model name; w=4u l=0.028u = 채널 width 4μm, length 28nm.

SPICE MOSFET 인스턴스의 노드 순서는 `drain gate source bulk`이다. pmos이므로 source와 bulk가 모두 VDD에 연결된다. 게이트가 `in`, 드레인이 `out`으로 인버터 PMOS 동작을 나타낸다. `w=4u`는 4 μm, `l=0.028u`는 28 nm로 현대 프로세스 노드 크기다.

**Q6.** 1만 trans × 10⁶ step × cost ~ N^1.5 → ~10¹¹ → 수 시간. **Fast SPICE 필요** (일반 SPICE는 며칠).

1 μs를 1 ps step으로 시뮬레이션하면 10⁶ time step이 필요하다. 1만 트랜지스터는 행렬 크기 ~10⁴이며 LU decomposition 비용은 대략 N^1.5 ~ N² 스케일이다. 이를 10⁶ step에 곱하면 일반 SPICE로는 며칠이 걸리는 수준이다. Fast SPICE는 matrix partitioning과 hierarchical isomorphism 등으로 이 비용을 1~2 자릿수 줄여 수 시간 이내로 줄인다.

**Q7.** ① `.ic` 명령으로 초기 노드 voltage 명시 ② Source ramp-up (전원을 0→VDD로 천천히) ③ `.option reltol=1e-3 abstol=1e-12` 완화 ④ 회로 안정성 점검 (latch-up 등).

`.op` 수렴 실패의 주된 원인은 Newton-Raphson 반복이 발산하는 것이다. 초기 조건(`.ic`)을 주면 반복의 시작점이 해에 가까워져 수렴이 빨라진다. Source ramp-up은 회로가 0 V에서 비교적 안정된 상태에서 시작하도록 한다. Tolerance 완화는 해가 완벽하지 않아도 수렴 판정을 내리게 해 임시방편으로 쓸 수 있다. 이들 방법을 써도 실패하면 회로 자체에 latch-up 같은 물리적 불안정 요소가 있는 것이다.

**Q8.** **Hierarchical isomorphism** — DRAM cell이 수 억 개 동일 회로 → 한 번만 풀고 나머지는 재활용 → 메모리·시간 모두 절약. 다른 기법보다 DRAM array에 압도적 효과.

DRAM cell array는 완전히 동일한 회로가 수억 번 반복된다. Hierarchical isomorphism은 이 동일한 회로를 한 번만 SPICE로 풀고 나머지 인스턴스의 동작을 재활용하는 기법이다. Table-based model(소자 I-V를 미리 테이블화), event-driven analog(활성 노드만 계산), matrix partitioning(부분 행렬만 반복 계산) 같은 다른 기법도 효과적이지만, DRAM처럼 동일 회로 반복 비율이 극단적으로 높은 구조에서는 hierarchical isomorphism의 효과가 압도적이다.

[← 퀴즈 인덱스](../) · [본문 ↗](../../03_spice_fundamentals/)
