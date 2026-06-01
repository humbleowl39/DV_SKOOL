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

IO buffer의 신호 품질은 이 5가지 특성의 조합으로 결정된다. Driver strength는 얼마나 강하게 신호를 구동하는지, slew rate는 전압이 얼마나 빠르게 바뀌는지를 나타낸다. Z_out이 transmission line Z0와 맞지 않으면 근단 반사(near-end reflection)가 생긴다. ODT는 수신 측에서 반사를 흡수하고, ZQ calibration은 이들 저항 값이 process·온도 변화로 틀어지는 것을 주기적으로 보정한다. 이 5가지 중 하나라도 벗어나면 eye opening이 좁아진다.

**Q2.** ① PAM modulation 지원 ② Back-channel link training.

IBIS 7.0은 기존 NRZ(Non-Return-to-Zero) 모델에 더해 PAM4 같은 다중 레벨 변조를 지원하고, DDR5와 PCIe Gen5에서 요구하는 back-channel(receiver에서 transmitter로의 역방향) link training 알고리즘을 IBIS-AMI 모델 안에 포함시켰다. 이 두 기능이 없던 IBIS 5.x/6.x 모델은 최신 고속 인터페이스 검증에 쓸 수 없다.

**Q3.** Driver/ODT 저항이 process variation과 temperature drift로 변동 → 외부 정밀 ZQ pin 240Ω을 기준으로 주기적 재보정하여 임피던스 정확도 유지.

CMOS 회로의 저항은 fabrication process와 온도에 따라 10~20% 이상 변할 수 있다. 만약 ODT 목표 60Ω이 실제로 70Ω이 되면 Γ가 커져 reflection 증가, eye 손상이 생긴다. ZQ pin에 연결된 외부 정밀 저항(240Ω)은 process/온도와 무관하게 일정하므로, 이를 기준으로 내부 저항 코드를 주기적으로 다시 맞추면 impedance mismatch를 허용 범위 안으로 유지할 수 있다.

**Q4.** R_load = Z0 (load impedance가 transmission line characteristic impedance와 같을 때).

reflection coefficient Γ = (R_load - Z0) / (R_load + Z0)이다. R_load = Z0이면 분자가 0이 되어 Γ = 0, 즉 반사가 전혀 없다. ODT가 Z0와 정확히 같으면 전송선에서 오는 신호 에너지가 전부 흡수되고 반사파가 생기지 않아 eye opening이 최대가 된다. Z0가 보통 50Ω인 이유도 여기서 비롯된다.

**Q5.**
```
(1.1 - V_DQ)/34 = (V_DQ - 0.55)/60
60(1.1 - V_DQ) = 34(V_DQ - 0.55)
84.7 = 94·V_DQ
V_DQ ≈ 0.901 V
```

이 문제는 driver pull-up(R_pu = 34Ω, voltage = VDDQ = 1.1V)과 ODT(R_ODT = 60Ω, VTT = 0.55V) 사이의 전압 분배 문제다. 두 가지 전류 경로의 Kirchhoff 전류법칙(KCL)을 세우면 위 방정식이 나온다. 결과 V_DQ ≈ 0.901 V는 VDDQ의 82% 수준이며, data='1'일 때 수신 측에서 측정되는 전압이다.

**Q6.** 천이 시간 = 1.1 / 3 = **367 ps** > 156 ps → 한 UI 안에 천이 불가 → **eye 닫힘**. 더 빠른 slew (≥ 7~8 V/ns) 필요.

6.4 Gbps에서 1 UI = 1/6.4 Gbps ≈ 156 ps다. 신호가 0 V에서 1.1 V(full swing)로 전환하는 데 걸리는 시간 = swing / slew rate = 1.1 V / 3 V/ns ≈ 367 ps이다. 한 UI(156 ps) 안에 천이가 완료되어야 다음 bit를 안전하게 전송할 수 있는데, 천이 시간이 UI의 2배 이상이므로 eye가 완전히 닫힌다. 이 slew rate는 2 Gbps 이하 저속 인터페이스 수준이다.

**Q7.** ① RX equalizer (CTLE/DFE) 표현 불가 ② Channel(PCB+package) 통과 후 ISI를 BER 1e-12 수준에서 검증 불가 ③ Back-channel link training 표현 불가. → IBIS-AMI 표준 모델 필요.

단순 RNM driver/ODT 모델은 V-I 특성과 임피던스를 표현하는 수준이다. DDR5 같은 고속 인터페이스에서는 수 ns에 걸친 ISI(Inter-Symbol Interference) 제거를 위해 RX에서 CTLE(연속 시간 선형 등화기)와 DFE(결정 피드백 등화기)를 사용한다. 이 알고리즘의 영향을 포함한 channel simulation은 behavioral C/C++ 코드로 구현된 IBIS-AMI 모델이 아니면 처리할 수 없다.

**Q8.** Voltage swing: ODT ↑ → divider 비율 변화로 swing 약간 감소 (driver Vs ODT 사이의 임피던스 비). Reflection: ODT(120Ω) ≠ Z0(50Ω) → Γ ≈ (120-50)/(120+50) ≈ 0.41 → reflection 증가. **결론**: 60Ω이 Z0=50Ω에 더 가까워 reflection 우수, 120Ω은 power 절감 가능하나 SI 손실.

ODT를 높이면 두 가지 효과가 반대 방향으로 작용한다. voltage swing 측면에서는 driver(34Ω)와 ODT 사이의 분배비가 바뀌어 swing이 약간 감소할 수 있다. 반면 power 소비는 줄어든다. signal integrity 측면에서는 Z0 = 50Ω에서 멀어질수록 Γ가 커지고 반사파가 eye를 오염시킨다. 60Ω은 50Ω에 더 가까워 Γ ≈ 0.09로 작고, 120Ω은 Γ ≈ 0.41로 상당한 반사를 유발한다. 이것이 DDR5가 60~80Ω 범위를 주로 사용하는 이유다.

[← 퀴즈 인덱스](index.md) · [본문 ↗](../08_deepdive_io_buffer_rnm.md)
