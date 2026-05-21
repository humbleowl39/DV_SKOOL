# Ch01 퀴즈 — 왜 Mixed-Signal Simulation인가

> 각 문항은 Bloom level 표시. 정답은 마지막에.

## Q1. (Remember)
Mixed-signal 칩의 예 5종을 나열하시오.

## Q2. (Remember)
순수 디지털 시뮬레이션이 표현할 수 있는 신호 값 4가지를 쓰시오.

## Q3. (Understand)
순수 SPICE 시뮬레이션의 두 가지 핵심 약점을 설명하시오.

## Q4. (Understand)
"Mixed-signal simulation"의 핵심 아이디어를 한 문장으로 정의하시오.

## Q5. (Apply)
다음 회로 블록을 적절한 패러다임(Digital / RNM / SPICE)에 매핑하시오.

a) AXI 디코더  b) ZQ cal FSM  c) PHY DLL  d) Refresh counter  e) DQ IO buffer

## Q6. (Apply)
"외부 핀에 닿는 신호 주변은 mixed-signal" 원칙에 따라, 다음 중 mixed-signal 영역에 속하지 않는 것은?
① DQ buffer  ② CK receiver  ③ Refresh counter  ④ DQS strobe path

## Q7. (Analyze)
SoC에서 mixed-signal 영역을 식별하는 1차 판단 기준 두 가지를 쓰시오.

## Q8. (Evaluate)
"SPICE만 쓰면 sign-off 충분하다"는 주장의 두 가지 결함을 평가하시오.

---

## 정답 및 해설

**Q1.** DRAM, ADC, SerDes, PLL, Power IC (또는 PMIC).

**Q2.** 0, 1, X, Z.

**Q3.** ① 매우 느림 — O(N²~N³) 복잡도, 큰 회로(>10⁴ trans) 비현실적. ② 수렴 실패 — Newton-Raphson이 발산하면 시뮬레이션 멈춤.

**Q4.** 디지털과 아날로그를 같은 시뮬레이션 안에서 동시에 돌리되, 각 영역에 맞는 알고리즘을 사용한다.

**Q5.** a) Digital  b) Digital + RNM  c) RNM (+ SPICE corner)  d) Digital  e) RNM 대량 / SPICE 정밀.

**Q6.** ③ Refresh counter — 칩 내부 디지털 로직, voltage 무관.

**Q7.** ① 외부 핀에 닿는가? ② Voltage/timing이 결과를 좌우하는가? (또는 회로 크기·트랜지스터 물리 의존성).

**Q8.** ① 시간 — 10⁶ trans 이상은 SPICE 사실상 불가. ② 비용 — sign-off에 수개월 ~ 수 년 걸려 tape-out 일정 무너짐.

[← 퀴즈 인덱스](index.md) · [본문 ↗](../01_why_mixed_signal.md)
