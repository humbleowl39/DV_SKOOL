# Quiz — Unit 6: Physical Design

[← Unit 6 본문으로 돌아가기](../06_physical_design.md)

---

## Q1. (Remember)

다음 backend flow 순서를 올바르게 배열하라:
**(a) Floorplan (b) Routing (c) CTS (d) Synthesis (e) Placement (f) Signoff**

??? answer "정답 / 해설"
    **d → a → e → c → b → f**

    1. Synthesis (RTL → netlist)
    2. Floorplan (die size, macro, PG)
    3. Placement (cell 위치)
    4. CTS (clock tree)
    5. Routing (signal routing)
    6. Signoff (STA / IR / EM / DRC / LVS)

## Q2. (Understand)

Setup violation 과 hold violation 중 *주파수 낮추기* 로 해결 가능한 것은? 이유는?

??? answer "정답 / 해설"
    **Setup**. 부등식 `t_ck→q + t_logic + t_su ≤ T_clk − t_skew` — T_clk 키우면 (= 주파수 ↓) 우변 증가 → 항상 만족.

    **Hold** 는 `t_ck→q + t_logic ≥ t_hold + t_skew` — T_clk 가 들어가지 않음 → 주파수 무관. *buffer 삽입* 으로 t_logic 늘려야 fix (setup 동시 악화 위험).

## Q3. (Apply)

다음 RTL 패턴이 합성에서 자동으로 *ICG (Integrated Clock Gating)* 로 변환되는 이유는?
```systemverilog
always_ff @(posedge clk) begin
  if (en) reg <= data;
end
```

??? answer "정답 / 해설"
    `if (en)` 의 *조건부 갱신* 패턴이 명시적 → 합성 도구가 *원래 flop + feedback MUX* 대신 *ICG (latch + AND gate) + 일반 flop* 으로 합성. ICG 가 en=0 일 때 clock 자체를 차단 → flop 의 dynamic clock power 절약.

    (도구 옵션: `set_clock_gating_style`)

## Q4. (Analyze)

Floorplan 직후 IR drop 이 hotspot 영역에서 nominal VDD 의 12% 초과 — 가능한 대응 방안 3가지?

??? answer "정답 / 해설"
    1. **PG mesh 보강** — Stripe density 증가 또는 metal layer 추가
    2. **Decap (decoupling cap) 추가** — 해당 영역에 분산 배치 → transient current peak 완화
    3. **Hotspot 의 switching 분산** — Cell placement 재조정 또는 high-activity flop 을 여러 영역으로 분산
    (보너스: Power gate 의 sleep-to-active rush current 가 원인이면 *sequential wakeup* 으로 단계적 활성화)

## Q5. (Distinguish)

OCV, AOCV, POCV 의 차이를 한 문장씩 답하라.

??? answer "정답 / 해설"
    - **OCV**: 단순 보정 — launch 와 capture 에 *고정 계수* (예: 1.05 / 0.95) 적용. 너무 보수적.
    - **AOCV**: Path 의 *stage 수* 와 *location* 에 따라 derating 변화. 짧은 path 일수록 더 큰 derate.
    - **POCV**: Cell 의 *statistical (μ, σ)* 모델로 path delay 의 sigma 를 RSS 합산. 가장 덜 보수적 + 정확.

## Q6. (Evaluate)

MBFF (Multi-bit Flip-Flop) 가 *적합하지 않은* 시나리오는?

??? answer "정답 / 해설"
    1. **비트들이 완전히 다른 source/destination** 으로 흩어지는 경우 → MBFF 가 한 곳에 강제 배치되면 routing 우회로 *오히려 wire delay ↑*.
    2. **Critical path 가 비트별로 다를 때** → 한 비트만 sizing 변경하고 싶은데 MBFF 는 일괄 → fix 자유도 ↓.
    3. **Power gating 영역 경계** — MBFF 가 두 영역에 걸쳐 있으면 isolation 어려움.

## Q7. (Apply)

Synthesis 결과 timing OK 였는데 P&R 후 fail 의 흔한 원인 3가지를 답하라.

??? answer "정답 / 해설"
    1. **Wire delay 가 zero / wire load model 가정** — 합성 단계는 placement 모름 → 실제 routing 길어지면 fail.
    2. **Clock skew = ideal 가정** — CTS 후 *실제 skew* 가 추가되어 setup margin 잠식.
    3. **Crosstalk (SI)** — Routing 후 인접 신호선의 coupling cap 으로 aggressor 가 victim delay 변화 → SI 분석에서 발견.

    (보너스: IR drop 에 의한 cell delay 증가도 가능)

## Q8. (Create)

Low-power 디자인에서 *clock gating + multi-Vt + power gating* 을 *언제 어디* 에 적용하는 가이드라인을 작성하라.

??? answer "정답 / 해설"
    | 기법 | 대상 | 효과 |
    |------|------|------|
    | **Leaf clock gating** | 모든 conditional update flop (`if(en) reg <= ...`) | Dynamic clock power |
    | **Coarse clock gating** | 큰 블록 (FIFO, RegFile) 입력 없을 때 | Dynamic clock power, 큰 절약 |
    | **Multi-Vt** | Non-critical path → HVT, critical path → LVT | Leakage |
    | **Power gating** | Idle 가능한 IP 블록 (GPU, accelerator) | Leakage (sleep 시 ~ 0) |
    | **DVFS** | Workload 기반 동적 변경 | Dynamic + Leakage 모두 |

    *Order*: 합성 단계에서 clock gating + multi-Vt 자동 적용, RTL 단계에서 power gating 영역 정의 (UPF), 펌웨어/OS 가 DVFS 제어.
