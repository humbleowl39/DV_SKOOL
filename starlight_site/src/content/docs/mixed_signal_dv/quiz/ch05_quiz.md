---
title: "Ch05 퀴즈 — RNM with SystemVerilog"
---

## Q1. (Remember)
`nettype`은 SV 어느 버전(연도)에 도입되었나?

## Q2. (Remember)
RNM 5단계 정확도 모델의 단계별 핵심 추가 기능을 쓰시오.

## Q3. (Understand)
`wreal`과 일반 `real` 변수의 차이를 한 문장으로 설명하시오.

## Q4. (Understand)
Resolution function이 호출되는 상황은 언제인가?

## Q5. (Apply)
다음 RNM inverter 코드의 `VTH`를 변경하지 않고 출력의 propagation delay만 100ps로 늘리려면 어디를 수정해야 하는가?
```systemverilog
parameter real TPD = 50.0;
assign #(TPD * 1ps) vout = vout_target;
```

## Q6. (Apply)
DRAM cell에 `'1'`(0.9V)이 저장된 상태에서 charge sharing 결과 BL voltage를 계산하시오.
- C_cell = 30 fF, C_bl = 100 fF, V_pre = 0.45 V

## Q7. (Analyze)
다음 회로 블록 중 RNM으로 모델링하기에 **가장 부적합한** 것은?
① Inverter  ② NAND gate  ③ Bit line precharge  ④ **VCO**  ⑤ Mode register

## Q8. (Evaluate)
UDN(EEnet) 구조체 nettype이 단순 `wreal`보다 적합한 검증 task 2가지를 평가하시오.

## Q9. (Apply)
SVA에서 real 값에 `$rose`/`$fell`을 직접 적용할 수 없는 이유와 안전 패턴은?

## Q10. (Apply)
다음 covergroup이 vendor 호환성 문제를 일으킬 위험이 있다. 안전한 패턴으로 다시 쓰시오.
```systemverilog
covergroup cg_vin with function sample(real vin);
  cp_vin: coverpoint vin {
    bins q[16] = { [0.0 : 1.8] };   // real bin
  }
endgroup
```

## Q11. (Apply)
ADC 입력 코드를 12-bit randomize 후 V로 변환하는 sequence_item을 작성할 때 `rand real vin`을 직접 randomize하면 안 되는 이유와 표준 패턴은?

## Q12. (Analyze)
다음 두 비교는 의도가 같은데 결과가 다를 수 있다. 차이와 안전 매크로를 쓰시오.
```systemverilog
if (vout == 1.0) ...
if ($abs(vout - 1.0) < 1e-6) ...
```

## Q13. (Analyze)
RNM 회귀에서 `timeprecision 1ns`로 PLL jitter 검증을 돌렸더니 spec PASS가 나왔다. 결과의 신뢰성을 평가하시오.

---

## 정답 및 해설

**Q1.** SystemVerilog 2012 (IEEE 1800-2012 § 6.6.7).

`nettype`은 IEEE 1800-2012에서 처음 도입된 기능이다. 그 이전의 SV(IEEE 1800-2005, 2009)에는 없었으므로 "SV 어느 버전부터인가"라는 질문에서 2005나 2009를 선택하면 틀린다. 2017 LRM도 같은 조항을 유지하고 있어 현재도 표준 기능이다.

**Q2.** L0 digital+delay / L1 real 출력 / L2 + ramp / L3 + threshold·saturation / L4 + noise·jitter / L5 + charge conservation.

5단계 정확도 모델은 "필요한 만큼만 정확하게"라는 RNM 철학을 단계적으로 구현한다. L0는 디지털 delay만 있는 수준, L5는 charge 보존까지 포함한 거의 SPICE 수준이다. DRAM 산업에서 L2~3이 주로 쓰이는 이유는 bit-line ramp와 sense amp threshold를 표현해야 timing margin 검증이 가능하기 때문이다.

**Q3.** `real`은 일반 변수로 net이 될 수 없고, `wreal`은 `nettype real` 선언으로 만든 **net** — port를 통해 모듈 간 전달 가능.

SV에서 변수(variable)와 net은 근본적으로 다르다. `real` 변수는 `assign`이나 `always`로 값을 가질 수 있지만 net이 아니어서 다른 모듈의 port에 직접 연결할 수 없다. `wreal`은 `nettype real wreal`로 정의된 실수 값 net이므로 port connection이 가능하고, 모듈 간 continuous assignment도 허용된다. RNM 회로를 multi-module로 나눌 때는 반드시 `wreal`(또는 다른 user-defined nettype)을 써야 한다.

**Q4.** 같은 net에 driver가 둘 이상 있을 때 — 그 값들을 하나의 net 값으로 결합할 때 자동 호출.

net은 여러 곳에서 동시에 driven 될 수 있다. 디지털 net의 `wor`, `wand`는 내장 resolution 함수의 예다. `nettype`으로 user-defined net을 만들면 custom resolution function을 지정할 수 있고, 이 함수는 driver가 둘 이상일 때 자동으로 호출되어 각 driver의 값을 하나의 net 값으로 합산한다.

**Q5.** `TPD` parameter 값을 100으로 변경 (또는 instance에 `#(.TPD(100.0))`로 override).

코드에서 propagation delay는 `#(TPD * 1ps)`로 파라미터화되어 있다. `VTH`를 건드리지 않고 delay만 늘리려면 `TPD`를 50에서 100으로 바꾸면 된다. 파라미터를 직접 수정하거나 instance에 `#(.TPD(100.0))`로 override하는 방법 모두 정답이다. `assign #100ps` 같은 하드코딩은 모듈 재사용성을 해치므로 권장하지 않는다.

**Q6.**
```
q_cell = 30e-15 × 0.9 = 27e-15 C
q_bl   = 100e-15 × 0.45 = 45e-15 C
v_shared = (27 + 45) / (30 + 100) = 72/130 ≈ 0.554 V
ΔBL ≈ +0.104 V
```

Charge sharing 공식 `v_shared = (q_cell + q_bl) / (C_cell + C_bl)`은 전하 보존 법칙의 직접 적용이다. DRAM read '1'에서 cell 전압(0.9 V)이 precharge 전압(0.45 V)보다 높아서 BL 전압이 올라간다. 이 ΔBL ≈ +104 mV가 sense amp의 감지 대상이 된다. 값이 크면 sense margin이 충분하고, 작으면 offset이나 noise에 취약해진다.

**Q7.** ④ **VCO** — 자체 발진 + jitter·phase noise의 정확한 모델링이 필수. RNM으로 표현은 가능하나 매우 어렵고 부정확. 보통 SPICE.

VCO는 제어 전압에 따라 주파수가 변하는 발진기로, 위상 누적과 jitter가 근본적인 특성이다. `real` 변수로 주파수를 표현하더라도 사이클마다 위상을 누적시키고 jitter를 주입하는 모델은 복잡도가 높고 SPICE 대비 신뢰도가 낮다. Inverter(①), NAND(②), Bit line precharge(③), Mode register(⑤)는 단순 logic 또는 threshold/ramp 모델로 충분히 표현되어 RNM에 적합하다.

**Q8.** ① Multi-driver power rail (impedance + voltage 동시 표현) — wreal 단독 불가. ② Loading effect를 가진 PMIC/regulator (driver 간 Thevenin 합산 필요).

`wreal`은 단일 실수 값만 전달하는 net으로, driver가 여럿일 때 resolution 방식이 단순 sum/average에 한정된다. power rail처럼 Thevenin 합산이 필요한 경우(각 driver의 impedance를 고려해야 함)는 `{voltage, impedance}` 쌍을 struct로 묶은 UDN이 필요하다. PMIC regulator에서 load regulation 효과를 모델링할 때도 마찬가지로 UDN이 더 정확한 resolution을 제공한다.

**Q9.** `$rose`/`$fell`은 **1-bit expression의 0→1/1→0**을 봅니다. `real` 직접 못 씀. 안전 패턴: threshold를 wire로 미리 빼고 그 wire에 `$rose` 적용 — `wire vsig_above = vsig.V > 0.9; ... $rose(vsig_above) |-> ...`. wave dump에도 잘 잡혀 debug가 쉬워짐.

`$rose`와 `$fell`은 정의상 비트 값의 전이를 감지하는 함수이므로 실수형 `real`에는 적용할 수 없다. 실수 신호의 threshold crossing을 SVA로 표현하려면 먼저 `wire thresh_met = (vsig.V > 0.9);`처럼 비교 결과를 1-bit wire로 뽑아내고, 그 wire에 `$rose`를 적용하는 간접 패턴을 써야 한다. 이 패턴은 wave dump에서도 threshold crossing 시점을 별도 신호로 볼 수 있어 디버그 편의성도 높다.

**Q10.** real coverpoint는 simulator마다 지원이 다르므로 **real을 int로 미리 변환**하는 패턴이 호환성 안전:
```systemverilog
function automatic int real_to_bin(real x, real lo, real hi, int N);
  if (x <= lo) return 0;
  if (x >= hi) return N-1;
  return $rtoi((x-lo)/(hi-lo) * N);
endfunction
covergroup cg_vin with function sample(int b);
  cp: coverpoint b { bins all[16] = { [0:15] }; }
endgroup
always @(posedge sample_clk) cg.sample(real_to_bin(vin.V, 0.0, 1.8, 16));
```

SV LRM은 real coverpoint를 허용하지만 실제 simulator 구현은 벤더마다 차이가 있어, `bins q[16] = { [0.0 : 1.8] }` 같은 실수 범위 bin은 한 simulator에서는 동작해도 다른 simulator에서는 elaboration 오류가 날 수 있다. 실수 값을 정수 인덱스로 변환한 뒤 정수 coverpoint를 사용하면 모든 주요 simulator에서 동일하게 동작한다.

**Q11.** `rand real` 직접 지원은 simulator마다 제한적이고 솔버는 정수 CSP 기반이라 real-domain constraint 표현력 한정. 표준 패턴: `rand bit[11:0] vin_code; constraint c { vin_code inside {[0:4095]}; }` 후 `function void post_randomize(); vin_volt = real'(vin_code) / 4096.0 * 1.8; endfunction`. 호환성·솔버 속도 모두 유리.

SV 랜덤 해석기(constraint solver)는 내부적으로 정수 constraint satisfaction problem(CSP)을 푼다. `rand real` 타입은 표준 문법상 허용되지만, 실수 영역 constraint(`vin inside {[0.0:1.8]}` 등)는 solver가 정밀하게 처리하지 못하거나 벤더마다 다르게 동작한다. 정수 코드로 randomize한 뒤 post_randomize에서 실수로 변환하면 모든 constraint solver에서 일관되게 동작하고 속도도 빠르다.

**Q12.** IEEE 754 라운딩 누적으로 `0.1+0.2 != 0.3` 같은 false-fail이 거의 항상 발생 — 절대 동등성 성립 불가. 표준 매크로: `` `define REAL_EQ(a,b,eps) ($abs((a)-(b)) <= (eps)) ``. scoreboard·SVA·log 모두 이 매크로로 통일하면 tolerance 정책이 한 곳에서 관리됨.

컴퓨터의 부동소수점 연산은 IEEE 754 표준에 따라 이진 근사값으로 저장되므로, 수학적으로 같은 값도 연산 경로가 다르면 최하위 비트에서 차이가 생긴다. `if (vout == 1.0)`은 이 미세한 차이를 false negative(틀린 fail)로 오판할 수 있다. 반면 `$abs(vout - 1.0) < 1e-6`은 허용 오차(epsilon) 범위 안에 들면 같다고 판단해 물리적으로 의미 있는 비교를 수행한다. epsilon 값을 매크로 한 곳에서 관리하면 tolerance 정책 변경도 용이하다.

**Q13.** **신뢰성 낮음 — 결과 무효**. PLL jitter는 ps 단위 timing 효과인데 timeprecision 1ns는 ps 단위 변화를 silently round-off 합니다 (1 ps = 0.001 ns로 버려짐). mixed-signal env는 **timeprecision을 1ps 또는 더 작게** 잡아야 안전. spec PASS는 실제로는 정밀도 부족으로 fail 신호가 안 잡힌 것일 가능성이 매우 높음.

PLL jitter는 수십 ps 단위의 clock edge 변동을 측정하는 것이 핵심이다. timeprecision이 1 ns이면 시뮬레이터는 시간을 1 ns 단위로 반올림하므로, 예를 들어 50 ps jitter는 0 ns로 버려지고 "jitter = 0"처럼 관측된다. 결과적으로 실제로는 spec을 위반하고 있더라도 시뮬레이션에서는 PASS가 나올 수 있다. 이는 false-pass로, 실리콘 테스트에서 예상치 못한 타이밍 실패로 이어질 수 있어 가장 위험한 종류의 검증 오류다.

[← 퀴즈 인덱스](../) · [본문 ↗](../../05_rnm_systemverilog/)
