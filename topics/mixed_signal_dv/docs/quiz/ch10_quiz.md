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

## Q9. (Apply)
RNM 회귀에서 ADC 입력 port가 driver bug로 한 cycle 동안 안 잡혔다. `code = 0`이 spec에 부합해 PASS가 나왔다면 이는 어떤 함정인가? 함정 이름과 안전 패턴을 쓰시오.

## Q10. (Analyze)
coverage가 87%에서 정체된다. 도달 못 한 13% bin을 분석할 때 첫 한 시간 안에 확인할 5가지 카테고리(escape analysis)를 나열하고 각 카테고리별 대응 1줄로 정리하시오.

## Q11. (Analyze)
scoreboard mismatch가 특정 seed에서만 발생한다. Debug 첫 한 시간 안에 좁힐 5가지 후보(triage)를 쓰고 각 후보의 1차 확인 방법을 매칭하시오.

## Q12. (Evaluate)
flaky test 한 개를 "가끔 fail이라 무시"하고 회귀에서 제외하자는 제안을 평가하시오. 추가 위험과 대안 절차는?

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

**Q9.** **함정 ① "real에는 X가 없다"** — `real` default = `0.0`이라 uninitialized = 0 V, `code = 0`이 spec 부합하면 false-PASS. 안전 패턴: 모든 RNM port에 `bit valid` 동반(`typedef struct { real V; bit valid; }`) + driver-presence assertion (`assert property (@(posedge clk) inp.valid)`).

**Q10.** ① **constraint 불충분** — random이 좁은 범위만 hit → weighted dist 추가, narrow range 명시. ② **의미상 도달 불가** — spec이 금지하는 조합 → `illegal_bins`/`ignore_bins`로 명시. ③ **solver hint 부족** — cross가 너무 광범위 → `solve before`로 ordering, sub-cross 분해. ④ **scenario 누락** — directed로만 도달 가능 → directed test 추가. ⑤ **tool bug** — vendor coverage 누락 → vendor 문의, workaround.

**Q11.** ① **RNM model bug** (특정 corner 출력 이상) — Spice cosim과 단일 vector 비교. ② **digital RTL bug** (register/FSM 어긋남) — RTL 단독 unit test 통과 여부. ③ **reference bug** (모든 seed 동일 패턴 mismatch) — spec example로 ref unit test. ④ **scoreboard tolerance** (borderline 위반 다수) — tol 한시 완화 → 패턴 변화 관찰. ⑤ **seed 미스코너** (특정 seed only) — seed 재현, sub-test 분리.

**Q12.** **제외 금지**. flaky test는 "가끔 fail"이 아니라 **"가끔 pass인 fail"** — tape-out에 가까울수록 더 위험. 추가 위험: ① 회귀 통계가 silently 약해져 pass rate trend 무의미 ② 실제 silicon에서 같은 race/노이즈 패턴이 reliably fail로 나타날 가능성. 대안: ① 즉시 isolate해서 별도 fix branch로 옮김 ② root cause 명시 전까지 main regression에 다시 넣지 않되 daily run에서는 계속 추적 ③ 가장 흔한 4가지 카테고리(race / FP 누적 / uninitialized real / jitter seed) 중 어디인지 우선 진단.

[← 퀴즈 인덱스](index.md) · [본문 ↗](../10_verification_methodology.md)
