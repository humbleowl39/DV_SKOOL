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

이름이 유사해서 혼동하기 쉽다. DMS(Digital Mixed-Signal)는 digital simulator 한 개만 사용하고, `nettype real`로 아날로그 동작을 근사한다. AMS(Analog Mixed-Signal)는 digital engine과 SPICE analog engine 두 개가 connect module을 통해 연결된 구조다. 속도와 라이선스 비용은 DMS가 유리하고, 정확도는 AMS가 높다.

**Q2.** 100×~1000× (DVCon 2020 PMIC SSD 사례 등).

이 수치는 DVCon 2020의 실제 사례에 근거한다. PMIC SSD 검증에서 AMS 대비 SV-RNM(DMS)으로 전환했을 때 100배에서 최대 1000배의 속도 향상이 보고되었다. 이 범위가 넓은 이유는 회로 크기, analog 영역 비율, simulation scenario 길이에 따라 개선 폭이 크게 달라지기 때문이다.

**Q3.** ① Multi-driver impedance interaction (예: 두 driver가 같은 power rail에 동시 contribute) ② Load regulation 효과 표현.

단순 `wreal`은 값(voltage)만 전달하며 resolution function이 sum 또는 average 수준에 머문다. 두 driver가 각기 다른 source impedance로 같은 rail을 구동할 때의 Thevenin 합산이나 부하가 변할 때 전압이 떨어지는 load regulation 효과를 표현하려면 voltage와 impedance를 쌍으로 갖는 struct 기반 UDN이 필요하다.

**Q4.** Digital scoreboard에 더해 **voltage threshold 검사** (예: power rail이 spec 범위 안에 있는가, sense margin이 충분한가) + voltage bin coverage.

일반 digital TB의 scoreboard는 logic level 비교만 수행한다. mixed-signal 환경에서는 "신호가 어느 logic level인가"에 더해 "실제 voltage가 spec 범위 안에 있는가", "sense amp에 충분한 전압 차이가 왔는가" 같은 실수 값 비교가 필요하다. 이를 위한 voltage threshold 검사와 어떤 voltage 구간이 얼마나 exercise되었는지를 추적하는 voltage bin coverage가 mixed-signal scoreboard의 추가 책임이다.

**Q5.**
```
V_thevenin = (V1/R1 + V2/R2) / (1/R1 + 1/R2)
R_eq      = R1·R2 / (R1 + R2)
```

두 독립 voltage source(V1, V2)가 각각 내부 저항(R1, R2)을 통해 같은 net에 연결될 때, Norton 전류 합산 후 Thevenin 등가 변환으로 이 공식을 유도한다. UDN resolution function에서 이 수식을 구현하면 multi-driver power rail을 물리적으로 정확하게 해결할 수 있다.

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

이 패턴은 compile-time 옵션으로 sense amp 모델의 정확도를 바꿀 수 있게 한다. fast regression에서는 default(RNM)로 속도를 얻고, sign-off 단계에서는 SA_MODE_SPICE나 SA_MODE_AMS로 정밀한 검증을 수행한다. 같은 TB 파일이 모든 모드를 지원하므로 시나리오 재작성 없이 전환이 가능하다.

**Q7.** RNM 모델은 SPICE-extracted 함수에 의존 → process/temp corner 변경 시 재추출 필요. 또한 transistor-level transient mismatch, kickback noise, Pelgrom statistical sign-off는 RNM이 잡지 못함 → SPICE Monte Carlo 필수.

RNM 모델의 동작 함수(예: delay vs. voltage 룩업 테이블)는 특정 PVT corner에서 SPICE simulation으로 추출된 것이다. 따라서 corner가 바뀌면 함수를 재추출해야 한다. 더 근본적으로, RNM은 transistor 두 개 사이의 Vth offset을 확률 분포로 샘플링하는 Pelgrom mismatch를 직접 표현할 수 없고, sense amp 내부에서 발생하는 kickback noise도 추상화 수준에서 사라진다. 이런 현상들은 SPICE Monte Carlo만이 포착할 수 있다.

**Q8.** **장점**: 일관된 fail 보고 + coverage 통합. **단점**: SPICE 영역이 들어가면 한 regression이 수 시간 ~ 수 일 — 빠른 feedback 불가. **권장**: nightly RNM-only(빠름) + weekly RNM+SPICE corner(sign-off) 분리.

"단일 nightly regression에 모두 넣는다"는 아이디어는 일관성 면에서 매력적이지만, SPICE simulation이 포함된 regression은 한 run에 수 시간이 걸려 밤사이 완료하기 어렵다. 개발 사이클에서 빠른 피드백이 없으면 버그 수정 속도가 떨어진다. nightly RNM(빠른 functional coverage)과 weekly SPICE corner(정밀 margin sign-off)로 분리하는 것이 속도와 품질을 모두 확보하는 현실적 접근이다.

**Q9.** **함정 ① "real에는 X가 없다"** — `real` default = `0.0`이라 uninitialized = 0 V, `code = 0`이 spec 부합하면 false-PASS. 안전 패턴: 모든 RNM port에 `bit valid` 동반(`typedef struct { real V; bit valid; }`) + driver-presence assertion (`assert property (@(posedge clk) inp.valid)`).

digital signal에는 X(unknown) 상태가 있어 "이 신호가 아직 driven 되지 않았다"는 것이 자연스럽게 표현된다. 반면 `real` 타입은 초기화되지 않아도 기본값 0.0을 갖는다. 만약 ADC 입력 driver에 버그가 있어 신호가 실제로 연결되지 않은 상태라도 `vin.V == 0.0 V`이고, ADC code = 0이 spec 범위 안에 있으면 scoreboard는 PASS를 낸다. `valid` 비트를 함께 전달하고 assertion으로 매 cycle 확인하는 것이 이 함정을 막는 안전 패턴이다.

**Q10.** ① **constraint 불충분** — random이 좁은 범위만 hit → weighted dist 추가, narrow range 명시. ② **의미상 도달 불가** — spec이 금지하는 조합 → `illegal_bins`/`ignore_bins`로 명시. ③ **solver hint 부족** — cross가 너무 광범위 → `solve before`로 ordering, sub-cross 분해. ④ **scenario 누락** — directed로만 도달 가능 → directed test 추가. ⑤ **tool bug** — vendor coverage 누락 → vendor 문의, workaround.

87% 정체는 나머지 13%의 bin이 왜 hit되지 않는지를 카테고리로 구분해 분석하지 않으면 효율적으로 해결할 수 없다. 각 카테고리는 전혀 다른 대응을 요구한다. 특히 "의미상 도달 불가" bin을 ignore하지 않고 계속 목표로 삼으면 아무리 test를 추가해도 100%에 도달할 수 없어 시간을 낭비한다.

**Q11.** ① **RNM model bug** (특정 corner 출력 이상) — Spice cosim과 단일 vector 비교. ② **digital RTL bug** (register/FSM 어긋남) — RTL 단독 unit test 통과 여부. ③ **reference bug** (모든 seed 동일 패턴 mismatch) — spec example로 ref unit test. ④ **scoreboard tolerance** (borderline 위반 다수) — tol 한시 완화 → 패턴 변화 관찰. ⑤ **seed 미스코너** (특정 seed only) — seed 재현, sub-test 분리.

"특정 seed에서만 발생"이라는 단서가 중요하다. 모든 seed에서 발생한다면 reference bug나 scoreboard 로직 오류가 유력하다. 특정 seed에서만 발생한다면 timing race, 특정 voltage corner hit, RNM 모델의 경계 조건(boundary case)이 의심된다. 5가지 후보를 논리적으로 좁혀나가면 첫 한 시간 안에 범위를 2~3가지로 줄일 수 있다.

**Q12.** **제외 금지**. flaky test는 "가끔 fail"이 아니라 **"가끔 pass인 fail"** — tape-out에 가까울수록 더 위험. 추가 위험: ① 회귀 통계가 silently 약해져 pass rate trend 무의미 ② 실제 silicon에서 같은 race/노이즈 패턴이 reliably fail로 나타날 가능성. 대안: ① 즉시 isolate해서 별도 fix branch로 옮김 ② root cause 명시 전까지 main regression에 다시 넣지 않되 daily run에서는 계속 추적 ③ 가장 흔한 4가지 카테고리(race / FP 누적 / uninitialized real / jitter seed) 중 어디인지 우선 진단.

flaky test를 제외하는 것은 단기적으로는 pass rate가 올라 보여서 편해 보이지만, 실제로는 버그가 숨은 채로 tape-out에 접근하는 위험한 결정이다. 실리콘에서는 온도·전압·aging 등이 worst case로 수렴하므로, 시뮬레이션에서 "가끔" 나타나던 fail이 reliably 나타날 수 있다. isolation하여 원인을 찾고 수정하는 것이 유일한 올바른 대응이다.

[← 퀴즈 인덱스](index.md) · [본문 ↗](../10_verification_methodology.md)
