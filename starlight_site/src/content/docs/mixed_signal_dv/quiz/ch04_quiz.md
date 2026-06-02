---
title: "Ch04 퀴즈 — AMS · Connect Module"
---

## Q1. (Remember)
Verilog-AMS의 4가지 핵심 키워드/연산자를 쓰시오.

## Q2. (Remember)
VAMS-2023의 발행 주체와 시기는?

## Q3. (Understand)
Connect module이 왜 필요한지 한 문장으로 설명하시오.

## Q4. (Understand)
A2D connect module의 핵심 메커니즘은 무엇인가?

## Q5. (Apply)
다음 RC LPF의 KCL을 `<+` 연산자로 표현하시오. R = 1 kΩ, C = 1 nF.

## Q6. (Apply)
D2A connect module을 작성할 때, `1'bX`를 어떻게 처리하는 게 안전한가?

## Q7. (Analyze)
AMS 시뮬레이션의 두 가지 병목 원인을 분석하시오.

## Q8. (Evaluate)
한 검증 task에서 sense amp의 voltage trajectory만 보면 된다. AMS와 RNM 중 어느 것이 적합하며 이유는?

---

## 정답 및 해설

**Q1.** `electrical`, `analog begin ... end`, `V(...)`, `I(...)`, `<+` (또는 `cross`, `transition`, `ddt`, `idt` 중 4개).

Verilog-AMS의 핵심은 analog domain을 표현하는 문법이다. `electrical`은 net의 discipline을 선언하고, `analog begin ... end` 블록 안에서만 continuous-time 방정식을 기술할 수 있다. `V(...)`와 `I(...)`는 노드 전압과 분기 전류를 접근하는 함수이며, `<+`는 기여(contribution) 연산자로 branch equation을 정의한다. 나머지 `cross`(threshold crossing 이벤트), `transition`(신호 천이 파형), `ddt`/`idt`(미분/적분)도 자주 쓰이는 키워드다.

**Q2.** Accellera, 2024년 2월 발행 (사실상 마지막 메이저 갱신).

Verilog-AMS(VAMS)는 IEEE가 아닌 Accellera가 관리하는 표준이다. VAMS-2023은 2024년 2월에 공개되어 마지막 메이저 갱신으로 간주된다. IEEE 1800 SystemVerilog와 혼동하기 쉬운데, SV의 `nettype`은 IEEE 1800-2012에서 도입된 별개의 기능이다.

**Q3.** 디지털 logic 신호(0/1)와 아날로그 voltage/current 신호 사이의 표현 차이를 자동으로 변환하기 위해.

디지털 simulator 안의 `1'b1`은 수치적으로는 단순한 1-bit 이진 값이지만, SPICE engine은 이것을 0.9 V의 실수 전압으로 받아야 한다. 반대로 SPICE가 계산한 0.6 V의 연속 전압을 디지털 측에 `1'b1`로 전달해야 할 수도 있다. Connect module은 이 변환을 경계에서 자동으로 처리한다. Connect module 없이는 AMS 시뮬레이션에서 두 도메인이 서로를 인식하지 못한다.

**Q4.** Threshold crossing 감지 (`cross(V(in) - vth, +1)` 등) — 입력 voltage가 정해진 임계값을 통과하는 순간 디지털 logic을 결정.

A2D connect module은 analog 측에서 `cross(V(in) - vth, +1)` 같은 이벤트 감지 함수를 써서 입력 voltage가 임계값을 통과하는 순간을 포착하고 그때 디지털 출력을 `1'b1`로 세팅한다. 단순히 매 time step마다 전압을 비교하는 것이 아니라, 교차 순간을 정밀하게 이벤트로 알려주는 것이 핵심이다. 이 메커니즘이 AMS simulation의 timing 정확도를 결정한다.

**Q5.**
```verilog
I(in, out) <+ (V(in) - V(out)) / R;
I(out)     <+ C * ddt(V(out));
```

`<+` 연산자는 branch에 전류를 기여(contribute)한다. 첫 줄은 저항의 옴 법칙으로 `in→out` 방향 전류를 정의하고, 두 번째 줄은 캐패시터의 `I = C·dV/dt` 관계를 `ddt` 함수로 표현한다. 두 식이 함께 RC LPF의 완전한 동작을 기술한다.

**Q6.** X를 mid-voltage(VDD/2)로 매핑하거나 fatal error로 시뮬레이션 중단. NaN propagation 방지가 핵심.

디지털 측에서 `1'bX`가 D2A connect module에 들어오면, 이를 그대로 아날로그 측에 전달할 방법이 없다. mid-voltage로 매핑하면 시뮬레이션은 계속되지만 의도하지 않은 아날로그 동작을 일으킬 수 있으며, fatal error로 중단하면 디버그가 쉽다. 어느 방법이든 NaN이나 예측 불가한 값이 아날로그 회로 전체로 퍼지는 것(NaN propagation)을 막아야 한다.

**Q7.** ① SPICE engine 자체가 느림 (analog 영역 크기에 비례) ② 두 simulator 간 동기화 오버헤드 (매 sync point마다 정보 교환).

AMS 시뮬레이션은 두 엔진이 병렬로 돌면서 주기적으로 신호를 주고받는 구조다. 아날로그 영역이 클수록 SPICE 계산 시간이 늘어나는 것이 첫 번째 병목이다. 두 번째 병목은 digital과 analog 엔진이 sync point에서 시간 맞춤을 위해 멈추고 데이터를 교환하는 오버헤드인데, 이 빈도가 높을수록 전체 시뮬레이션이 느려진다.

**Q8.** **RNM** — 단순 voltage trajectory는 SPICE-level 정확도 불필요. 빠른 RNM이 전체 시나리오 cover 가능. AMS는 SA의 transistor-level mismatch 통계 같은 정밀 검증에 적합.

"voltage trajectory만 보면 된다"는 전제가 중요하다. voltage가 어느 방향으로 얼마나 움직이는지, threshold를 언제 통과하는지를 확인하는 목적이라면 SPICE 수준의 정밀한 트랜지스터 모델은 과잉 사양이다. RNM의 `real` 변수로 충분히 표현 가능하고 시뮬레이션도 훨씬 빠르다. 반면 SA offset mismatch 통계처럼 수천 번의 Monte Carlo가 필요하거나 transistor-level kickback noise를 정량화해야 한다면 AMS/SPICE가 적합하다.

[← 퀴즈 인덱스](../) · [본문 ↗](../../04_ams_connect_modules/)
