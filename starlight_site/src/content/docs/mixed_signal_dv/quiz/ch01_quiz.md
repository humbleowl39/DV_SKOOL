---
title: "Ch01 퀴즈 — 왜 Mixed-Signal Simulation인가"
---

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

디지털 I/O를 가지면서도 내부에서 voltage·전류·임피던스를 직접 다루는 칩이 mixed-signal 범주에 들어간다. DRAM은 bit-line 전압 증폭, ADC는 analog-to-digital 변환, SerDes는 수 Gbps의 I/O, PLL은 위상 제어, Power IC는 스위칭 레귤레이터가 핵심이다. 순수 디지털 로직 칩(예: CPU 코어 단독)이나 순수 아날로그 칩은 이 목록에서 제외된다.

**Q2.** 0, 1, X, Z.

순수 디지털 시뮬레이터는 IEEE 1364/1800 logic value system에 따라 이 4가지만 표현한다. 0(강한 Low), 1(강한 High), X(unknown/충돌), Z(high-impedance)가 전부이므로, 0.6 V 같은 실수 전압이나 -5 mV 오버슈트는 표현 자체가 불가능하다. 이 한계가 mixed-signal 시뮬레이션이 필요한 근본 이유다.

**Q3.** ① 매우 느림 — O(N²~N³) 복잡도, 큰 회로(>10⁴ trans) 비현실적. ② 수렴 실패 — Newton-Raphson이 발산하면 시뮬레이션 멈춤.

SPICE는 회로 노드마다 KCL/KVL를 연립 방정식으로 세운 뒤 Newton-Raphson 반복으로 수치 해를 구한다. 트랜지스터 수 N이 늘면 행렬 크기가 커져 연산량이 N²~N³에 비례하므로, DRAM처럼 수억~수십억 개의 트랜지스터가 있는 회로는 현실적 시간 안에 풀 수 없다. 또한 MOSFET의 강한 비선형성 때문에 반복이 수렴하지 않고 발산할 수 있어 시뮬레이션 자체가 중단된다. 이 두 약점이 Fast SPICE와 RNM이 등장한 배경이다.

**Q4.** 디지털과 아날로그를 같은 시뮬레이션 안에서 동시에 돌리되, 각 영역에 맞는 알고리즘을 사용한다.

"각 영역에 맞는 알고리즘"이 핵심이다. 디지털 부분은 이벤트 기반 logic 엔진(빠름), 아날로그 부분은 continuous-time 수치 해석(정확)을 쓴다. 둘을 하나의 시뮬레이터 안에서 동기화하는 것이 mixed-signal의 아이디어이며, 각자 단일 패러다임만 쓰는 것과 구별된다.

**Q5.** a) Digital  b) Digital + RNM  c) RNM (+ SPICE corner)  d) Digital  e) RNM 대량 / SPICE 정밀.

a) AXI 디코더는 순수 logic 연산이므로 voltage 개념이 없다. d) Refresh counter도 같다. b) ZQ cal FSM은 로직 부분은 digital이지만 외부 저항과 임피던스를 비교·조정하는 부분이 voltage 의존이라 RNM이 필요하다. c) PHY DLL은 위상을 연속값으로 다루는 블록이어서 RNM이 적합하고, 정밀 sign-off는 SPICE corner로 보완한다. e) DQ IO buffer는 대량 scenario 검증에는 RNM, transmission-line·ISI 정밀 분석에는 SPICE를 쓴다.

**Q6.** ③ Refresh counter — 칩 내부 디지털 로직, voltage 무관.

Refresh counter는 DRAM 내부에서 refresh timing을 세는 순수 디지털 카운터로, 외부 핀과 연결되지 않고 voltage·analog 경계에 있지 않다. 나머지 보기인 DQ buffer(①), CK receiver(②), DQS strobe path(④)는 모두 칩 외부와 직접 연결되는 I/O 경계 블록이므로 mixed-signal 영역에 속한다.

**Q7.** ① 외부 핀에 닿는가? ② Voltage/timing이 결과를 좌우하는가? (또는 회로 크기·트랜지스터 물리 의존성).

"외부 핀"은 신호가 PCB·채널·다른 칩을 거쳐 왔다는 뜻이므로 정확한 voltage 레벨과 천이 타이밍이 동작에 결정적이다. 또한 sense amp처럼 내부에 있더라도 voltage 차이가 수십 mV에 불과해 mismatch·noise가 pass/fail을 결정한다면 mixed-signal 영역으로 분류해야 한다. 이 두 기준 중 하나라도 해당하면 RNM 이상이 필요하다.

**Q8.** ① 시간 — 10⁶ trans 이상은 SPICE 사실상 불가. ② 비용 — sign-off에 수개월 ~ 수 년 걸려 tape-out 일정 무너짐.

SPICE만으로 sign-off 한다는 주장은 정확도 면에서 이상적이지만, 현실 회로 규모에서는 성립하지 않는다. DRAM처럼 수십억 트랜지스터가 있는 경우 SPICE 시뮬레이션에 수 년이 걸릴 수 있어 tape-out 일정 자체가 불가능해진다. 나아가 functional regression(수천 시나리오)도 SPICE로는 현실적이지 않다. "충분한 정확도"와 "실현 가능한 시간·비용" 사이의 균형 때문에 RNM을 주 방법론으로 쓰고 SPICE는 critical block sign-off에만 사용하는 것이 산업 표준이다.

[← 퀴즈 인덱스](../) · [본문 ↗](../../01_why_mixed_signal/)
