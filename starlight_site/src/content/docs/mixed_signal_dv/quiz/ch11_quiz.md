---
title: "Ch11 퀴즈 — 도구 지형"
---

## Q1. (Remember)
Synopsys / Cadence / Siemens EDA 각각의 AMS 도구 이름을 쓰시오.

## Q2. (Remember)
Fast SPICE 도구 3종(벤더 포함)을 쓰시오.

## Q3. (Understand)
Pure RNM의 vendor 독립성이 왜 비용 우위로 이어지는지 설명하시오.

## Q4. (Understand)
IBIS-AMI 모델이 DDR5/PCIe Gen5+ 검증에 표준이 된 이유는?

## Q5. (Apply)
다음 task에 적합한 도구를 추천하시오.
a) DDR5 PHY full-chip regression 5,000 testcase
b) PCIe Gen5 link training back-channel 검증
c) BGR voltage Monte Carlo sign-off

## Q6. (Apply)
1만 trans 회로의 transient 분석에 적합한 도구 카테고리는?

## Q7. (Analyze)
"Verilator로 RNM 시뮬레이션 가능?"에 대한 분석을 쓰시오.

## Q8. (Evaluate)
"SPICE 라이센스가 없어도 mixed-signal 검증이 가능하다"는 주장을 평가하시오.

---

## 정답 및 해설

**Q1.** Synopsys VCS AMS · Cadence AMS Designer · Siemens EDA Questa AMS.

세 대형 EDA 벤더가 각자의 AMS 솔루션을 보유하고 있다. Synopsys는 VCS에 AMS 기능을 통합하여 VCS AMS라는 이름으로 제공하고, Cadence는 AMS Designer를 별도 제품으로 운영한다. Siemens EDA(구 Mentor)는 Questa simulator에 AMS 기능을 추가했다. 이 세 도구는 각자 자사의 digital simulator와 analog engine을 결합한 것으로, 혼용하거나 벤더를 바꾸면 flow가 완전히 달라진다.

**Q2.** Synopsys CustomSim XA · Synopsys FineSim Pro · Cadence UltraSim (또는 Siemens Eldo Premier).

Fast SPICE 도구는 일반 SPICE보다 1~2자릿수 빠른 속도를 목표로 한다. Synopsys는 CustomSim XA(대형 회로)와 FineSim Pro(고속 분석)를 갖추고 있고, Cadence는 UltraSim을 제공한다. 이들은 일반 SPICE(HSPICE, Spectre)의 정확도를 일부 양보하는 대신 DRAM array 수준의 대형 회로를 현실적 시간 안에 시뮬레이션할 수 있게 한다.

**Q3.** Pure RNM은 `nettype` SV 표준 기능만 사용 → 별도 SPICE 엔진 라이센스 불필요. 기존 digital simulator 라이센스만으로 mixed-signal 검증 가능 → 추가 비용 0.

AMS 도구는 digital simulator 라이선스에 더해 analog/SPICE engine 라이선스를 별도로 구매해야 한다. 반면 `nettype`은 IEEE 1800-2012 표준에 정의된 SV 기능이므로 VCS, Xcelium, Questa 등 일반 digital simulator 라이선스만으로 사용 가능하다. 이는 mixed-signal 검증을 도입하는 팀의 비용 장벽을 크게 낮춘다.

**Q4.** ① CTLE/DFE/CDR equalizer가 표준화되어 vendor가 모델 제공 ② IBIS 7.0에서 back-channel training 추가 ③ Channel(PCB+package)과 RX algorithm을 통합 분석 가능 — 단일 도구로 BER 1e-12 수준 statistical eye 검증.

DDR5나 PCIe Gen5에서는 RX측 equalizer의 효과가 link budget의 핵심이다. 단순 RNM 모델은 equalizer의 adaptive 알고리즘을 표현할 수 없지만, IBIS-AMI의 C/C++ algorithmic block에는 CTLE, DFE, CDR을 vendor가 사전 구현하여 배포한다. 여기에 PCB와 패키지 채널 모델을 결합하면 실제 link에서의 BER을 statistical 방식으로 추정할 수 있다.

**Q5.** a) VCS / Xcelium / Questa (Pure RNM) b) MATLAB SerDes Toolbox 또는 Keysight ADS c) HSPICE.

a) DDR5 PHY regression은 수천 testcase를 빠르게 돌려야 하므로 Pure RNM이 유일한 선택이다. b) PCIe Gen5 back-channel은 link training 알고리즘과 channel model이 결합된 검증이므로 MATLAB SerDes Toolbox나 Keysight ADS 같은 SerDes 전용 도구가 적합하다. c) BGR은 transistor-level mismatch와 온도 특성이 핵심이므로 HSPICE Monte Carlo가 표준이다.

**Q6.** **Fast SPICE** (CustomSim XA, FineSim Pro 등). 1만 trans는 일반 SPICE로는 수 시간 소요.

1만 트랜지스터 규모는 일반 SPICE로도 수 시간이 걸릴 수 있는 경계 영역이다. 특히 1 μs를 1 ps step으로 시뮬레이션하면 시간이 더욱 길어진다. Fast SPICE는 matrix partitioning과 hierarchical isomorphism 등으로 이 시간을 현실적으로 줄일 수 있다. Pure RNM은 transistor 수준의 정확도가 없어 이 규모의 SPICE-accuracy 분석에 부적합하다.

**Q7.** Verilator는 `nettype` 일부 지원하지만 complete RNM(특히 UDN with resolution) 미흡 — 일반 SoC RNM 검증에는 상용 VCS/Xcelium/Questa 권장. 단순 학습/실험은 가능.

Verilator는 오픈소스 SV 시뮬레이터로 compile-time transformation 방식으로 동작한다. `nettype real` 기반 단순 wreal은 동작할 수 있지만, custom resolution function을 가진 UDN(EEnet 등)은 Verilator의 elaboration/simulation 엔진이 완전히 지원하지 않는 경우가 많다. production 검증보다는 학습이나 간단한 프로토타이핑에는 쓸 수 있다.

**Q8.** **부분적 사실**. ① Pure RNM(digital sim only)으로 80% 이상 검증 가능 — DDR5 PHY functional, PMIC DMS 등. ② 그러나 sign-off의 critical block(SA Monte Carlo, VCO phase noise, BGR variation)은 SPICE 필요. 결론: 학습/architectural 단계는 SPICE 없이 가능, sign-off는 SPICE 필요.

"SPICE 없이 mixed-signal 검증이 가능하다"는 맥락에 따라 맞기도 하고 틀리기도 한 주장이다. 기능 검증, timing margin 확인, 대부분의 scenario coverage는 Pure RNM만으로 달성 가능하다. 그러나 Pelgrom mismatch 통계, VCO phase noise, BGR의 온도 계수 같은 "analog-only" 특성은 SPICE의 compact device model 없이는 정확하게 검증할 수 없다. 따라서 최종 sign-off에는 SPICE가 필요하다는 것이 산업의 일관된 결론이다.

[← 퀴즈 인덱스](../) · [본문 ↗](../../11_tools_ecosystem/)
