# Ch06 퀴즈 — DRAM Read Path 분해

## Q1. (Remember)
DRAM read 경로 7 stage를 순서대로 나열하시오.

## Q2. (Remember)
Read 동작에서 cell capacitor의 데이터가 어떻게 변하는지 한 단어로?

## Q3. (Understand)
"Mixed-signal 영역인가?"를 결정하는 1차 판단 기준은?

## Q4. (Understand)
tRCD margin 검증에서 RNM이 측정해야 하는 핵심 값은?

## Q5. (Apply)
다음 cell 조건에서 read '1' 시 BL의 변화량(ΔBL)을 계산하시오.
- V_cell('1') = 1.1 V, C_cell = 25 fF, C_bl = 200 fF, V_pre = 0.55 V.

## Q6. (Apply)
ZQ cal FSM에 적합한 패러다임 조합과 이유는?

## Q7. (Analyze)
WL load capacitance가 가장 큰 worst row에서 tRCD margin이 가장 작은 이유를 분석하시오.

## Q8. (Evaluate)
"전체 DRAM read 경로를 SPICE로 sign-off 하는 것이 가장 안전하다"는 주장을 평가하시오.

---

## 정답 및 해설

**Q1.** Row Decoder → WL Driver → Bit Cell → Bit Line → Sense Amp → Column Mux → IO Buffer.

**Q2.** Destructive (read 후 cell voltage가 v_shared로 바뀜 → write-back 필요).

**Q3.** 외부 핀에 닿는 신호인가, voltage·timing이 결과를 좌우하는가.

**Q4.** WL voltage trajectory(특히 발달 완료 시점)와 BL voltage 발달 곡선.

**Q5.**
```
q_cell = 25e-15 × 1.1 = 27.5e-15 C
q_bl   = 200e-15 × 0.55 = 110e-15 C
v_shared = (27.5 + 110)/225 ≈ 0.611 V
ΔBL = 0.611 - 0.55 = +0.061 V (+61 mV)
```

**Q6.** **Digital + RNM**. FSM은 디지털, 외부 240Ω 저항과의 임피던스 비교/조정 부분은 RNM (mock current/voltage divider).

**Q7.** WL load C가 크면 WL voltage가 천천히 발달 → 충분히 발달하기 전에 sense amp가 활성화될 위험 ↑ → BL 발달 시간 부족 → sense margin 손실 → tRCD를 더 늘려야 함.

**Q8.** **불가능 또는 비현실적**. ① DRAM 셀 수 10⁹ 이상은 SPICE로 며칠 ~ 수 년 소요 → tape-out 일정 불가. ② Functional 시나리오(시퀀스, refresh, training)는 SV TB가 필수 — SPICE는 stimulus 작성 한계. 산업 표준: **RNM 우선 + critical block SPICE Monte Carlo**.

[← 퀴즈 인덱스](index.md) · [본문 ↗](../06_dram_read_path_partitioning.md)
