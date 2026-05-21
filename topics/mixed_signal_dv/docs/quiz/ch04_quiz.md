# Ch04 퀴즈 — AMS · Connect Module

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

**Q2.** Accellera, 2024년 2월 발행 (사실상 마지막 메이저 갱신).

**Q3.** 디지털 logic 신호(0/1)와 아날로그 voltage/current 신호 사이의 표현 차이를 자동으로 변환하기 위해.

**Q4.** Threshold crossing 감지 (`cross(V(in) - vth, +1)` 등) — 입력 voltage가 정해진 임계값을 통과하는 순간 디지털 logic을 결정.

**Q5.**
```verilog
I(in, out) <+ (V(in) - V(out)) / R;
I(out)     <+ C * ddt(V(out));
```

**Q6.** X를 mid-voltage(VDD/2)로 매핑하거나 fatal error로 시뮬레이션 중단. NaN propagation 방지가 핵심.

**Q7.** ① SPICE engine 자체가 느림 (analog 영역 크기에 비례) ② 두 simulator 간 동기화 오버헤드 (매 sync point마다 정보 교환).

**Q8.** **RNM** — 단순 voltage trajectory는 SPICE-level 정확도 불필요. 빠른 RNM이 전체 시나리오 cover 가능. AMS는 SA의 transistor-level mismatch 통계 같은 정밀 검증에 적합.

[← 퀴즈 인덱스](index.md) · [본문 ↗](../04_ams_connect_modules.md)
