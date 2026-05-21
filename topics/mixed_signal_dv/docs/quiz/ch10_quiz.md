# Ch10 퀴즈 — 검증 방법론 통합

## Q1. (Remember)
DMS와 AMS의 차이를 한 줄로 쓰시오.

## Q2. (Remember)
DVCon paper들이 보고한 SV-RNM 대비 AMS 속도 향상 범위는?

## Q3. (Understand)
단순 `wreal`이 부족한 상황 2가지를 설명하시오.

## Q4. (Understand)
UVM-DMS 환경에서 scoreboard가 추가로 검사해야 하는 것은?

## Q5. (Apply)
EEnet 같은 UDN에서 두 driver의 Thevenin equivalent voltage 공식을 쓰시오.

## Q6. (Apply)
Abstraction switching이 가능한 SA module을 SV `define` 으로 구현 sketch 하시오.

## Q7. (Analyze)
DMS-only 환경의 limit을 분석하시오. 어떤 상황에서 AMS/SPICE 보완이 필수인가?

## Q8. (Evaluate)
"단일 nightly regression으로 RNM + SPICE 모두 cover" 전략의 장단점을 평가하시오.

---

## 정답 및 해설

**Q1.** DMS는 digital simulator만으로 RNM 기반 mixed-signal, AMS는 digital + SPICE 결합.

**Q2.** 100×~1000× (DVCon 2020 PMIC SSD 사례 등).

**Q3.** ① Multi-driver impedance interaction (예: 두 driver가 같은 power rail에 동시 contribute) ② Load regulation 효과 표현.

**Q4.** Digital scoreboard에 더해 **voltage threshold 검사** (예: power rail이 spec 범위 안에 있는가, sense margin이 충분한가) + voltage bin coverage.

**Q5.**
```
V_thevenin = (V1/R1 + V2/R2) / (1/R1 + 1/R2)
R_eq      = R1·R2 / (R1 + R2)
```

**Q6.**
```systemverilog
`ifdef SA_MODE_SPICE
  // SPICE netlist instance
`elsif SA_MODE_AMS
  // Verilog-AMS behavior
`else
  sense_amp_rnm u_sa(...);
`endif
```

**Q7.** RNM 모델은 SPICE-extracted 함수에 의존 → process/temp corner 변경 시 재추출 필요. 또한 transistor-level transient mismatch, kickback noise, Pelgrom statistical sign-off는 RNM이 잡지 못함 → SPICE Monte Carlo 필수.

**Q8.** **장점**: 일관된 fail 보고 + coverage 통합. **단점**: SPICE 영역이 들어가면 한 regression이 수 시간 ~ 수 일 — 빠른 feedback 불가. **권장**: nightly RNM-only(빠름) + weekly RNM+SPICE corner(sign-off) 분리.

[← 퀴즈 인덱스](index.md) · [본문 ↗](../10_verification_methodology.md)
