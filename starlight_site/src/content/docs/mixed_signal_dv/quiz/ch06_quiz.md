---
title: "Ch06 퀴즈 — DRAM Read Path 분해"
---

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

이 7-stage 경로는 DRAM read 동작의 물리적 흐름이다. Row Decoder가 주소를 받아 해당 Word Line을 선택하면, WL Driver가 WL을 full swing으로 올려 Bit Cell의 access transistor를 켠다. 그러면 cell capacitor와 Bit Line 사이에 charge sharing이 일어나고, Sense Amp가 미세한 전압 차이를 감지·증폭한다. Column Mux가 원하는 bit를 선택하고 IO Buffer가 외부로 전달한다. 순서를 잘못 쓰면(예: SA보다 Column Mux가 먼저) DRAM 물리 동작을 오해한 것이다.

**Q2.** Destructive (read 후 cell voltage가 v_shared로 바뀜 → write-back 필요).

DRAM cell은 access transistor를 통해 BL과 연결되는 순간 charge sharing으로 cell 전압이 변한다. read '1'이었다면 원래 VDD에 가까운 전압이었지만 charge sharing 후에는 v_shared(약 0.55 V 근처)로 낮아진다. 이 상태로 access transistor를 닫으면 cell 데이터가 훼손되므로, sense amp가 BL을 full swing으로 증폭한 뒤 cell에 다시 써주는 write-back 동작이 반드시 이어진다.

**Q3.** 외부 핀에 닿는 신호인가, voltage·timing이 결과를 좌우하는가.

Ch01에서 제시된 2가지 기준이 여기서도 그대로 적용된다. IO Buffer는 외부 핀과 직접 연결(첫 번째 기준), Sense Amp는 내부에 있지만 수십 mV의 voltage 차이가 pass/fail을 결정(두 번째 기준)하므로 두 블록 모두 mixed-signal 영역이다. Row Decoder나 Refresh counter 같은 pure 디지털 로직 블록은 두 기준 모두 해당하지 않아 digital paradigm으로 충분하다.

**Q4.** WL voltage trajectory(특히 발달 완료 시점)와 BL voltage 발달 곡선.

tRCD는 RAS(row access strobe) 이후 WL이 충분히 발달하고 BL에 sense-able한 전압이 형성될 때까지의 최소 시간이다. RNM에서 이 margin을 검증하려면 WL이 full swing에 도달하는 시점과 그에 따라 BL 전압이 얼마나 발달하는지를 `real` 값으로 추적해야 한다. WL trajectory와 BL curve 없이는 tRCD margin 계산이 불가능하다.

**Q5.**
```
q_cell = 25e-15 × 1.1 = 27.5e-15 C
q_bl   = 200e-15 × 0.55 = 110e-15 C
v_shared = (27.5 + 110)/225 ≈ 0.611 V
ΔBL = 0.611 - 0.55 = +0.061 V (+61 mV)
```

이전 Q6(Ch05)의 30 fF / 100 fF 예제보다 C_bl이 훨씬 크다(200 fF). C_bl이 클수록 ΔBL이 작아지는 것에 주목하라. 여기서 ΔBL ≈ +61 mV는 cell '1'을 읽을 때 BL이 precharge 전압보다 61 mV 올라간다는 의미다. 이 값이 sense amp의 최소 감지 한계(수십 mV)보다 커야 read가 성공한다.

**Q6.** **Digital + RNM**. FSM은 디지털, 외부 240Ω 저항과의 임피던스 비교/조정 부분은 RNM (mock current/voltage divider).

ZQ cal FSM은 "현재 driver/ODT 저항 설정이 기준 저항과 가까운가"를 판단하는 로직을 포함한다. 이 판단의 근거가 되는 voltage divider 비교, 즉 외부 정밀 저항과 내부 programmable 저항 사이의 current/voltage를 `real` 값으로 표현하는 부분이 RNM이다. FSM state transition 자체는 digital이므로 두 패러다임의 조합이 맞다.

**Q7.** WL load C가 크면 WL voltage가 천천히 발달 → 충분히 발달하기 전에 sense amp가 활성화될 위험 ↑ → BL 발달 시간 부족 → sense margin 손실 → tRCD를 더 늘려야 함.

WL은 긴 word line 배선을 통해 수백~수천 개의 cell access transistor 게이트를 동시에 구동한다. 가장 먼 row의 cell은 배선 저항과 capacitance(RC) 지연이 가장 커서 WL이 늦게 발달한다. sense amp가 너무 이르게 활성화되면 BL이 충분히 발달하지 않은 상태에서 감지가 시작되어 fail risk가 높아진다. 따라서 worst-case WL load를 가진 row에서 tRCD margin이 가장 작다.

**Q8.** **불가능 또는 비현실적**. ① DRAM 셀 수 10⁹ 이상은 SPICE로 며칠 ~ 수 년 소요 → tape-out 일정 불가. ② Functional 시나리오(시퀀스, refresh, training)는 SV TB가 필수 — SPICE는 stimulus 작성 한계. 산업 표준: **RNM 우선 + critical block SPICE Monte Carlo**.

"가장 안전하다"는 말이 기술적으로 일면 맞지만, 실현 불가능한 방법은 사실상 안전하지 않다. DRAM 전체를 SPICE로 sign-off하면 수 년이 걸릴 수 있고, 그동안 버그 발견이 늦어지면 오히려 더 위험하다. 또한 SPICE는 회로 해석에 특화되어 있어 "주소 XX에 WRITE 후 READ, 그 다음 refresh" 같은 functional stimulus를 표현하는 능력이 SV TB에 비해 극도로 부족하다. 산업 표준은 functional을 RNM+SV로 광범위하게 검증하고 SPICE는 SA, VCO 같은 critical analog block의 통계적 sign-off에만 집중하는 것이다.

[← 퀴즈 인덱스](../) · [본문 ↗](../../06_dram_read_path_partitioning/)
