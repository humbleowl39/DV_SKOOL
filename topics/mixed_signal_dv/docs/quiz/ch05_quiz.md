# Ch05 퀴즈 — RNM with SystemVerilog

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

**Q2.** L0 digital+delay / L1 real 출력 / L2 + ramp / L3 + threshold·saturation / L4 + noise·jitter / L5 + charge conservation.

**Q3.** `real`은 일반 변수로 net이 될 수 없고, `wreal`은 `nettype real` 선언으로 만든 **net** — port를 통해 모듈 간 전달 가능.

**Q4.** 같은 net에 driver가 둘 이상 있을 때 — 그 값들을 하나의 net 값으로 결합할 때 자동 호출.

**Q5.** `TPD` parameter 값을 100으로 변경 (또는 instance에 `#(.TPD(100.0))`로 override).

**Q6.**
```
q_cell = 30e-15 × 0.9 = 27e-15 C
q_bl   = 100e-15 × 0.45 = 45e-15 C
v_shared = (27 + 45) / (30 + 100) = 72/130 ≈ 0.554 V
ΔBL ≈ +0.104 V
```

**Q7.** ④ **VCO** — 자체 발진 + jitter·phase noise의 정확한 모델링이 필수. RNM으로 표현은 가능하나 매우 어렵고 부정확. 보통 SPICE.

**Q8.** ① Multi-driver power rail (impedance + voltage 동시 표현) — wreal 단독 불가. ② Loading effect를 가진 PMIC/regulator (driver 간 Thevenin 합산 필요).

**Q9.** `$rose`/`$fell`은 **1-bit expression의 0→1/1→0**을 봅니다. `real` 직접 못 씀. 안전 패턴: threshold를 wire로 미리 빼고 그 wire에 `$rose` 적용 — `wire vsig_above = vsig.V > 0.9; ... $rose(vsig_above) |-> ...`. wave dump에도 잘 잡혀 debug가 쉬워짐.

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

**Q11.** `rand real` 직접 지원은 simulator마다 제한적이고 솔버는 정수 CSP 기반이라 real-domain constraint 표현력 한정. 표준 패턴: `rand bit[11:0] vin_code; constraint c { vin_code inside {[0:4095]}; }` 후 `function void post_randomize(); vin_volt = real'(vin_code) / 4096.0 * 1.8; endfunction`. 호환성·솔버 속도 모두 유리.

**Q12.** IEEE 754 라운딩 누적으로 `0.1+0.2 != 0.3` 같은 false-fail이 거의 항상 발생 — 절대 동등성 성립 불가. 표준 매크로: `` `define REAL_EQ(a,b,eps) ($abs((a)-(b)) <= (eps)) ``. scoreboard·SVA·log 모두 이 매크로로 통일하면 tolerance 정책이 한 곳에서 관리됨.

**Q13.** **신뢰성 낮음 — 결과 무효**. PLL jitter는 ps 단위 timing 효과인데 timeprecision 1ns는 ps 단위 변화를 silently round-off 합니다 (1 ps = 0.001 ns로 버려짐). mixed-signal env는 **timeprecision을 1ps 또는 더 작게** 잡아야 안전. spec PASS는 실제로는 정밀도 부족으로 fail 신호가 안 잡힌 것일 가능성이 매우 높음.

[← 퀴즈 인덱스](index.md) · [본문 ↗](../05_rnm_systemverilog.md)
