# Ch11 퀴즈 — 도구 지형

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

**Q2.** Synopsys CustomSim XA · Synopsys FineSim Pro · Cadence UltraSim (또는 Siemens Eldo Premier).

**Q3.** Pure RNM은 `nettype` SV 표준 기능만 사용 → 별도 SPICE 엔진 라이센스 불필요. 기존 digital simulator 라이센스만으로 mixed-signal 검증 가능 → 추가 비용 0.

**Q4.** ① CTLE/DFE/CDR equalizer가 표준화되어 vendor가 모델 제공 ② IBIS 7.0에서 back-channel training 추가 ③ Channel(PCB+package)과 RX algorithm을 통합 분석 가능 — 단일 도구로 BER 1e-12 수준 statistical eye 검증.

**Q5.** a) VCS / Xcelium / Questa (Pure RNM) b) MATLAB SerDes Toolbox 또는 Keysight ADS c) HSPICE.

**Q6.** **Fast SPICE** (CustomSim XA, FineSim Pro 등). 1만 trans는 일반 SPICE로는 수 시간 소요.

**Q7.** Verilator는 `nettype` 일부 지원하지만 complete RNM(특히 UDN with resolution) 미흡 — 일반 SoC RNM 검증에는 상용 VCS/Xcelium/Questa 권장. 단순 학습/실험은 가능.

**Q8.** **부분적 사실**. ① Pure RNM(digital sim only)으로 80% 이상 검증 가능 — DDR5 PHY functional, PMIC DMS 등. ② 그러나 sign-off의 critical block(SA Monte Carlo, VCO phase noise, BGR variation)은 SPICE 필요. 결론: 학습/architectural 단계는 SPICE 없이 가능, sign-off는 SPICE 필요.

[← 퀴즈 인덱스](index.md) · [본문 ↗](../11_tools_ecosystem.md)
