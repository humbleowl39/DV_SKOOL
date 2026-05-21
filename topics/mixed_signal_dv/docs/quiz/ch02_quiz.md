# Ch02 퀴즈 — 세 시뮬레이션 세계

## Q1. (Remember)
Digital · SPICE · RNM의 신호 표현 차이를 한 줄씩 쓰시오.

## Q2. (Remember)
RNM이 사용하는 시간 처리 방식은? (이벤트 기반 / 연속시간 / 양쪽)

## Q3. (Understand)
AMS와 RNM 두 통합 방식의 가장 큰 차이를 설명하시오.

## Q4. (Understand)
RNM이 DRAM 산업에서 표준이 된 가장 핵심적인 이유 두 가지를 쓰시오.

## Q5. (Apply)
다음 시나리오에 RNM/AMS/IBIS-AMI 중 적합한 것을 선택하시오.
a) PCIe Gen5 link training back-channel
b) PMIC buck regulator dynamic response
c) DDR5 PHY full-chip functional regression

## Q6. (Apply)
RNM 5단계 정확도 모델에서, DRAM 산업이 일반적으로 사용하는 단계는?

## Q7. (Analyze)
한 SerDes 검증에서 BER 1e-12를 달성해야 한다. 일반 RNM 시뮬레이션이 부족한 이유는?

## Q8. (Evaluate)
"AMS가 RNM보다 항상 정확하므로 AMS만 쓰면 된다"는 주장을 평가하시오.

---

## 정답 및 해설

**Q1.** Digital: logic 0/1/X/Z. SPICE: 실수 전압/전류 (연속). RNM: 실수값 (`real`, event-driven).

**Q2.** 이벤트 기반.

**Q3.** AMS는 두 시뮬레이터(digital + SPICE)를 결합해 connect module로 잇고, RNM은 하나의 digital simulator 안에서 real-valued 함수로 모든 것을 처리.

**Q4.** ① DRAM 셀 수가 너무 많아 SPICE 불가 ② `nettype`이 SV 표준이라 vendor lock-in 없음 (UVM과 공존).

**Q5.** a) IBIS-AMI  b) RNM + SPICE corner  c) RNM (only).

**Q6.** Level 2~3 (ramp transition + threshold/hysteresis).

**Q7.** 1e-12는 1조 sample이 필요 — 일반 RNM은 ~10⁶ sample 한계. **Statistical eye + IBIS-AMI**가 표준 해법.

**Q8.** AMS는 SPICE 부분이 병목 → 큰 칩 sim 불가능. 또한 칩 전체를 AMS로 돌리면 sign-off 한 번에 며칠 ~ 수 주 걸려 비현실적. RNM 우선 + AMS corner가 산업 표준.

[← 퀴즈 인덱스](index.md) · [본문 ↗](../02_three_worlds_spice_ams_rnm.md)
