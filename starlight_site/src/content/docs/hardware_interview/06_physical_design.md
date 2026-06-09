---
title: "Unit 6 — Physical Design"
---

:::tip[학습 목표]
이 모듈을 마치면:

- **Explain** synthesis → floorplan → placement → CTS → routing → signoff 의 backend flow 흐름을 설명한다.
- **Apply** clock gating, multi-Vt, voltage scaling 같은 low-power 기법을 *어디에 / 언제* 적용해야 효과적인지 결정한다.
- **Analyze** IR drop, EM(Electromigration), antenna effect 같은 reliability 이슈의 원인과 대응을 분석한다.
- **Distinguish** setup / hold derating, OCV (On-Chip Variation), AOCV / POCV 의 의미 차이를 설명한다.
- **Evaluate** multi-bit flip-flop, register-banking, leaf-level clock gating 의 area / power / timing 트레이드오프를 평가한다.
:::
:::note[사전 지식]
- [Unit 1: Digital RTL](../01_digital_rtl/) — setup/hold, skew, STA
- 합성/EDA flow 개념 (Genus, DC Compiler, Innovus, Fusion Compiler 등 도구 이름 정도)
:::
---

## 1. PD Flow — 한 장 그림

**Physical Design**(PD, 물리 설계 — RTL 같은 논리 기술을 칩 위 실제 트랜지스터·배선 도형으로 구현하는 backend 단계)의 전체 흐름입니다. 그림의 각 단계: **Synthesis**(합성 — RTL을 표준 셀들의 연결망인 netlist로 변환), **netlist**(논리 게이트와 그 연결을 적은 목록), **Floorplan**(칩 위 큰 블록의 자리 배치), **Placement**(표준 셀 하나하나의 위치 배치), **CTS**(Clock Tree Synthesis, 클럭을 모든 flop에 균등하게 분배하는 트리 구성), **Routing**(셀들을 실제 금속 배선으로 연결), **Signoff**(최종 검증 — 타이밍·전원·신뢰성 통과 확인). **std cell**(standard cell, 미리 설계·검증된 작은 논리 블록 라이브러리), **macro**(SRAM·PLL처럼 크고 미리 만들어진 IP 블록), **DRC**(Design Rule Check, 공정이 요구하는 배선 규칙 위반 검사)도 자주 나옵니다.

```d2
direction: right
grid-rows: 2
Synthesis -> Floorplan -> Placement -> CTS -> Routing -> Signoff
Synthesis.label: "Synthesis\n(RTL → netlist)"
Floorplan.label: "Floorplan\n(Die / macro)"
Placement.label: "Placement\n(Std cell)"
CTS.label: "CTS\n(H-tree / skew)"
Routing.label: "Routing\n(DRC clean)"
Signoff.label: "Signoff\n(STA/IR/EM)"
```

---

## 2. Floorplan & Power Plan

### 2.1 Floorplan 결정 사항

Floorplan 은 물리 설계의 첫 번째 공간 배치 결정으로, 이 단계의 선택이 이후 placement, CTS, routing 의 난이도를 좌우합니다. 면적 추정부터 시작해 macro 위치, IO 배치, routing 공간까지 순서대로 결정합니다.

1. **Die size** — 전체 cell 면적의 합을 utilization 목표(보통 60~80%) 로 나눠 die 크기를 산정합니다. Utilization 이 너무 높으면 routing congestion 이 심해지고, 너무 낮으면 면적 낭비입니다.
2. **Macro 배치** — SRAM, PLL, IP 블록은 크기가 크고 이동이 어렵기 때문에 먼저 고정합니다. 자주 통신하는 macro 는 가까이 두어 critical path 의 wire delay 를 줄입니다.
3. **IO ring** — Pad cell 은 ESD, signal, power pad 를 균등하게 분배해야 wire congestion 과 signal integrity 문제를 줄일 수 있습니다.
4. **Channel** — Macro 사이에 routing 공간을 충분히 확보해야 place-and-route 단계에서 병목이 생기지 않습니다.

### 2.2 Power Plan (PG mesh)

**PG mesh**(Power/Ground mesh — VDD(전원)와 VSS(접지)를 칩 전체에 그물처럼 깔아 모든 셀에 안정적으로 전력을 공급하는 금속 격자)를 설계하는 단계입니다.

```d2
direction: right
grid-rows: 3
"VDD ring" -> "VDD stripe" -> "VDD via stack" -> "VDD rail" -> "VSS rail" -> "VSS via stack" -> "VSS stripe" -> "VSS ring"
```

- **Ring** — 칩 가장자리 전원 분배
- **Stripe** — 일정 간격(예: 50 μm) 으로 수직/수평 띠
- **Via stack** — Top metal ↔ M1 까지 *연속* via array

**IR drop**(전원 그물의 저항 R에 전류 I가 흘러 생기는 국소 VDD 강하 — 자세히는 §6) 이 큰 영역 → stripe density 증가 또는 metal layer 추가.

---

## 3. Clock Tree Synthesis (CTS)

### 3.1 목표

- **Skew** ≤ target (예: 50ps)
- **Insertion delay** ≤ target (보통 1~3 ns)
- **Slew** (rise/fall transition time) ≤ target — flop reliability + STA accuracy

### 3.2 구조 종류

| 구조 | 설명 | 장단점 |
|------|------|--------|
| **H-tree** | 칩을 H 패턴으로 분기 | Symmetry → low skew. Macro 많으면 어려움 |
| **Clock mesh** | 상위 layer 메탈로 그물 | 매우 낮은 skew. Power ↑↑ |
| **Multi-source CTS** | 여러 시작점에서 동시 구동 | balance 쉬움, 도구 의존 |

### 3.3 Useful Skew

설계자가 *의도적으로* skew 를 줘서 setup margin 추가 확보. 예: launch 를 빠르게 (forward path), capture 를 늦게.

**위험** — hold violation 으로 *전이*. STA 도구가 자동으로 결정 (CTS during optimization).

### 3.4 Hold Fix

CTS 직후 hold violation 다수 발생 → **buffer 삽입** 으로 launch path 늘림. 합성 단계에서는 hold 가 *무시* 되고 CTS 후에 본격 fix.

**Risk** — buffer 가 setup 도 동시에 악화. 균형 fix 필요.

---

## 4. Low Power 기법

칩 소비 전력은 크게 **dynamic power**(동적 전력 — 신호가 0↔1로 토글할 때마다 쓰는 전력)와 **static/leakage power**(정적/누설 전력 — 토글이 없어도 트랜지스터가 미세하게 새는 전력)로 나뉩니다.

### 4.1 Dynamic Power = αCV²f

동적 전력은 `α·C·V²·f` 공식으로 결정됩니다. **α**(activity factor, 활동률 — 신호가 실제로 토글하는 빈도 비율), **C**(스위칭하는 커패시턴스), **V**(공급 전압), **f**(클럭 주파수)입니다.

| 변수 | 줄이는 법 |
|------|-----------|
| **α** (activity) | **Clock gating**(안 쓰는 동안 flop에 가는 클럭을 끊어 토글을 막음), operand isolation, glitch reduction |
| **C** (capacitance) | Multi-bit flop, downsizing, layer 분리 |
| **V²** | **DVFS**(Dynamic Voltage Frequency Scaling, 부하에 따라 전압·주파수를 실시간 낮춤), multi-VDD |
| **f** | Clock gating, frequency scaling |

### 4.2 Static (Leakage) Power

Sub-threshold + gate + junction leakage 의 합으로, 28nm 이하 공정에서는 총 소비전력의 30% 이상을 차지할 수 있어 무시할 수 없습니다.

**대응**:
Leakage 를 줄이는 핵심은 *필요한 곳에만 빠른 소자를 쓰고, 나머지는 느리고 새는 소자를 억제*하는 전략입니다. **Multi-Vt** 는 이를 가장 효과적으로 구현합니다. critical path 에는 threshold 가 낮아 속도는 빠르지만 leakage 가 많은 LVT(Low-Vt) 셀을 쓰고, timing 여유가 있는 non-critical path 는 threshold 가 높아 느리지만 leakage 가 적은 HVT(High-Vt) 셀로 채웁니다. **Power gating** 은 한 단계 더 나아가 사용하지 않는 블록의 전원을 sleep transistor 로 아예 차단하는 방법입니다. **Body biasing** 은 reverse body bias 를 인가해 threshold 를 높여 leakage 를 줄이는 회로 수준의 기법입니다.

- **Multi-Vt** — Critical path 는 LVT(빠름, 새기 많음), non-critical 은 HVT(느림, 새기 적음)
- **Power gating** — 사용 안 하는 블록의 *전원 자체 차단* (sleep transistor)
- **Body biasing** — Reverse body bias 로 Vth 증가

### 4.3 Clock Gating — 가장 효과적

```d2
direction: down
"Combinational en" -> Latch
Latch.label: "Latch\n(transparent during LOW)"
Latch -> AND
AND.label: "AND with clock"
AND -> "gated_clock to flops"
```

- **ICG cell** (Integrated Clock Gating) — Latch 통합 표준 셀, glitch-free.
- **Leaf-level gating** — flop 직전 gate (가장 흔함, 합성 자동).
- **Coarse gating** — 큰 블록 단위 (수동, 더 큰 절약).

**효과**: 사용하지 않는 flop 에 clock 이 공급되지 않으면, 그 flop 의 clock 네트워크 dynamic power 와 flop 내부의 switching 소비 모두 절약됩니다. 특히 대규모 register file 이나 data path 에서 clock gating 이 적용되면 전체 chip dynamic power 를 20~40% 줄이는 경우도 흔합니다.

**왜 가장 효과적인가 — §4.1 의 αCV²f 와 직접 연결.** Dynamic power `P = α·C·V²·f` 에서 clock gating 은 _두 항_ 을 동시에 0 으로 만든다. 첫째, gating 된 flop 의 입력단에서는 clock edge 가 안 오므로 그 flop 의 _activity factor α 가 0_ 이 되어 flop 내부 switching power 가 사라진다. 둘째, gate 아래의 _clock net 자체_ 가 토글하지 않으므로 그 clock 분배 네트워크(보통 칩에서 가장 toggle 이 잦은, 즉 α≈1 에 가까운 노드)의 `α·C·V²·f` 가 통째로 0 이 된다 — clock tree 가 dynamic power 의 큰 비중을 차지하기 때문에 이 두 번째 절약이 특히 크다. 즉 다른 기법이 C(MBFF)나 V²(DVFS)를 _줄이는_ 반면, clock gating 은 안 쓰는 동안 α 를 _0 으로 만들어_ 항 자체를 소거하므로 효율이 높다.

### 4.4 Multi-bit Flip-Flop (MBFF)

여러 single-bit flop 을 *공유 clock buffer + 공유 reset* 으로 묶음.

- 면적 ↓ ~10%
- Clock power ↓↓ (한 flop 당 clock cap 감소)
- 단점: placement 제약 ↑ (인접해야 함)

---

## 5. STA Signoff — Derating & OCV

**STA**(Static Timing Analysis, 정적 타이밍 분석 — Unit 1 참조)의 최종 signoff에서는 여러 조건에서 타이밍을 확인합니다. **Corner**(코너 — 공정·전압·온도(PVT)의 극단 조합 시나리오; 최악 조건에서도 동작하는지 검증), **derating**(디레이팅 — 편차를 반영해 셀 지연을 일부러 보수적으로 늘리거나 줄이는 보정 계수)이 핵심입니다.

### 5.1 Setup 과 Hold 의 분석 corner

표의 **Slow corner**(소자가 가장 느려지는 조건 — setup 검증용), **Fast corner**(가장 빨라지는 조건 — hold 검증용), **Typical**(기준 조건)입니다.

| Corner | Process | Voltage | Temp | 분석 |
|--------|---------|---------|------|------|
| **Slow** (ss / ssg) | Slow NMOS+PMOS | low VDD | high (or low) T | Setup |
| **Fast** (ff / ffg) | Fast NMOS+PMOS | high VDD | low T | Hold |
| **Typical** (tt) | nominal | nominal | room | Reference |

### 5.2 OCV (On-Chip Variation)

같은 칩 안에서도 *transistor 간* 속도 차이. 동일 corner 라도 launch path 와 capture path 가 서로 다른 정도로 변할 수 있음.

### 5.3 AOCV / POCV

- **AOCV** (Advanced OCV) — Path depth (stage 수) 와 location 에 따라 derating 변화. 짧은 path → 더 큰 derate.
- **POCV** (Parametric OCV) — 통계적 모델 (mean ± sigma). 더 정확하지만 도구 의존 ↑. 최근 표준.

### 5.4 Derating 의미

`launch_clock_derate = 1.05`, `capture_clock_derate = 0.95` → setup 분석 시 launch 5% 늦고 capture 5% 빠르게 가정 → *더 보수적*.

---

## 6. Reliability — IR Drop / EM / Antenna

### 6.1 IR Drop

전원 grid 의 저항 R 과 전류 I 로 인한 *지역 VDD 강하*. VDD 가 떨어지면 cell 이 *느려져* timing fail.

- **Static IR drop** — DC 분석. Power plan 평가.
- **Dynamic IR drop** — switching 시점에 transient 전류 폭증. Decoupling cap, switching activity 시뮬.

**Limit** — 보통 nominal VDD 의 5~10%.

### 6.2 Electromigration (EM)

**EM**(Electromigration, 전자이동 — 도선에 큰 전류가 오래 흐르면 전자가 금속 원자를 밀어내 배선이 끊기거나 단락되는 노화 현상)입니다. Metal 도선에 *너무 큰 전류 밀도* → 전자 충돌로 metal atom 이동 → 시간이 갈수록 *open 또는 short*. 신뢰성 (10 년 등) 보장 필요.

**대응**:
- 도선 *폭 증가*
- *복수 via* (single via 가 가장 약함)
- Current density limit 준수

### 6.3 Antenna Effect

**Antenna effect**(안테나 효과 — 제조 중 긴 금속 배선이 플라스마 전하를 모아, 거기 연결된 트랜지스터의 얇은 게이트 절연막(gate oxide)을 뚫어 망가뜨리는 문제)입니다. Plasma etch 중 *long metal segment* 가 charge 를 모아 gate oxide 파괴.

**대응**:
- *Diode* 추가 (충전된 전하 방전)
- 짧은 jog 로 long metal 분할
- Higher metal layer 로 우회

---

## 7. 합성 단계의 트레이드오프

### 7.1 Synthesis Checks

```bash
check_design          # netlist sanity (unconnected, multi-driver)
check_timing          # constraint coverage (unconstrained paths)
report_constraint     # SDC 잘못된 곳
report_qor            # quality of result (timing/area/power)
```

### 7.2 Cell Sizing — 자주 묻는 질문

**Cell sizing**(셀 크기 조정 — 같은 논리라도 더 크고 강한 셀을 쓰면 빠르지만 면적·전력이 늘어, 경로별로 적정 크기를 고르는 것)입니다. **drive strength**(구동 능력 — 셀이 얼마나 많은/무거운 부하를 빠르게 구동하는가), **fanout**(팬아웃 — 한 출력이 구동해야 하는 입력의 개수)이 기준입니다.

작은 cell → 면적/power ↓, drive strength ↓ → fanout 적은 곳만 OK.
큰 cell → fan-out 많이 받음, 빠름 → 면적/power ↑.

**합성 도구가 자동 sizing** 하지만 *critical path* 와 *high-fanout* 영역은 floorplan / placement 가 결과를 좌우.

### 7.3 Buffer Insertion

긴 wire 의 신호 weakening → buffer 로 *재구동*.

- **Repeater** 간격 = `sqrt(2 · t_buf / RC_per_unit)` 정도가 최적.
- 너무 많으면 power / area, 너무 적으면 timing fail.

---

## 8. 샘플 인터뷰 Q&A

<details>
<summary>Q1. (Explain) Setup 과 hold violation 중 어느 것이 *fix 가 더 어렵나*?</summary>

**Hold**. Setup 은 *주파수* 를 낮추면 거의 항상 fix 가능. Hold 는 *주파수 무관* — buffer 를 넣어 short path 를 늘려야 하는데, buffer 가 setup 을 동시에 악화. 균형 잡기 어려움.

**왜 hold 는 주파수와 무관한가 — 두 부등식을 나란히 보면 보인다.** setup 과 hold 부등식에서 _clock 주기 `T_clk` 가 어디에 들어가는지_ 가 결정적이다 ([Unit 1](../01_digital_rtl/) 의 STA 식):

$$ t_{ck \to q} + t_{logic,max} + t_{setup} + t_{skew} \le T_{clk} \quad \text{(Setup)} $$
$$ t_{ck \to q} + t_{logic,min} \ge t_{hold} + t_{skew} \quad \text{(Hold)} $$

setup 은 launch flop 의 데이터가 _다음_ clock edge(한 주기 뒤)까지 capture flop 에 도착해야 하므로 우변에 `T_clk` 가 있다 — 그래서 주파수를 낮춰(T_clk↑) 우변을 키우면 거의 항상 만족시킬 수 있다. 반면 hold 는 launch 와 capture 가 _같은(동시) clock edge_ 를 두고 벌이는 경합이다: 방금 launch 된 _새_ 데이터가 capture flop 의 hold window 가 닫히기 _전에_ 도착해 _현재_ 캡처를 오염시키면 안 된다는 조건이다. 이 "같은 edge" 비교에는 _다음 주기까지의 시간_ 이 개입할 여지가 없어 **부등식에 `T_clk` 가 아예 등장하지 않는다**. 따라서 주파수를 아무리 낮춰도 hold 부등식은 변하지 않고(주파수 무관), 오직 `t_logic,min` 을 키워야(=short path 에 buffer 삽입) 고칠 수 있다 — 그런데 그 buffer 는 setup 의 `t_logic,max` 도 키워 setup 을 악화시키므로 균형이 어렵다.

</details>
<details>
<summary>Q2. (Apply) Clock gating 의 *적절한 위치* 는?</summary>

- **Coarse gating** — 큰 블록 (FIFO, register file) 단위. 큰 절약, 수동 RTL 필요.
- **Leaf-level (flop-level) gating** — 합성 도구 자동. 흔한 패턴: `if (en) reg <= data;` → 도구가 자동으로 ICG 삽입.
- **나쁜 위치** — 너무 깊은 leaf gating 은 *clock skew 정렬 어려움*. STA balance 가 어려워짐.

</details>
<details>
<summary>Q3. (Analyze) IR drop 이 timing 에 미치는 영향을 트레이스해라.</summary>

1. Switching activity 가 *집중* 된 영역에서 dynamic IR drop ↑
2. 해당 cell 의 *effective VDD ↓*
3. Cell delay 가 *VDD-dependent* 이므로 ↑ (Vt 의 영향 커짐)
4. 이 cell 이 *capture* 측이면 setup margin ↓ (clock 도 늦게 도착)
5. 이 cell 이 *launch* 측이면 capture path 가 더 늦어져 setup 영향 약간, *hold margin 은 개선*

</details>
<details>
<summary>Q4. (Evaluate) Multi-bit FF 4-bit MBFF vs 4개 single-bit FF — 어느 것을 선호?</summary>

**선호 = MBFF** (대부분의 경우):
- **장점**: clock cap ↓, area ↓, layout 단순
- **단점**: 4 비트가 *같은 위치* 에 강제 → routing 제약, *서로 다른 timing path* 라면 fix 자유도 감소

*비추 케이스*: 4 비트 신호가 *완전히 다른 source/destination* 으로 흩어지는 경우. 또는 critical path 분리가 필요한 경우.

</details>
<details>
<summary>Q5. (Distinguish) Synthesis 결과 timing 은 OK 인데 P&R 후 fail — 흔한 원인 3가지?</summary>

1. **Wire delay 가 zero 가정** → 합성 단계는 wire load model 만 봄. 실제 routing wire 가 길면 fail.
2. **Clock skew 가 ideal 가정** → 합성은 ideal clock. CTS 후에 실제 skew 가 추가 → margin 잠식.
3. **Crosstalk** → 신호선 간 coupling cap 으로 *aggressor* 가 *victim* delay 를 변화. P&R 후 SI(Signal Integrity) 분석에서 발견.

</details>
---

## 9. 핵심 정리 (Key Takeaways)

1. PD flow = synth → floorplan → place → CTS → route → signoff. 각 단계의 *책임* 이 다름.
2. Setup fix 는 *느리게*, hold fix 는 *buffer 삽입* — buffer 가 setup 을 악화시킬 수 있음에 주의.
3. Low-power 핵심 = clock gating + multi-Vt + DVFS. Leakage 가 dynamic 보다 큰 시대.
4. IR drop / EM / Antenna 가 reliability 3총사. Power plan 과 layer 분배가 좌우.
5. OCV → AOCV → POCV 가 *시간이 흐를수록 정확* 한 derating 모델.
6. MBFF, useful skew, leaf clock gating 은 *power + timing 양쪽* 의 효과적 도구.

## 10. Further Reading

- *Constraint-Driven Synthesis and Optimization in IC Design* — SDC + synthesis
- *Static Timing Analysis for Nanometer Designs* (Bhasker & Chadha)
- Cadence Innovus / Synopsys Fusion Compiler User Guides
- Wikipedia: Electromigration / Antenna effect / Latch-up
- [Unit 6 퀴즈](../quiz/06_physical_design_quiz/) 로 자기 점검
