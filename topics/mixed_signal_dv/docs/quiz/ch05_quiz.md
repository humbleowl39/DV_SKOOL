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

[← 퀴즈 인덱스](index.md) · [본문 ↗](../05_rnm_systemverilog.md)
