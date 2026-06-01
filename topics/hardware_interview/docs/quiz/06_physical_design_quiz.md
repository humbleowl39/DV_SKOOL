# Quiz — Unit 6: Physical Design

[← Unit 6 본문으로 돌아가기](../06_physical_design.md)

---

## Q1. (Remember)

다음 backend flow 순서를 올바르게 배열하라:
**(a) Floorplan (b) Routing (c) CTS (d) Synthesis (e) Placement (f) Signoff**

??? answer "정답 / 해설"
    **d → a → e → c → b → f**

    1. **Synthesis** — RTL을 gate-level netlist로 변환한다. 이 단계에서 timing constraint(SDC)를 적용하지만 실제 배선 지연은 모른다.
    2. **Floorplan** — die 크기, macro(SRAM/IP) 배치, power/ground(PG) 망을 계획한다. 이후 모든 단계의 품질이 floorplan 품질에 크게 의존한다.
    3. **Placement** — standard cell의 물리적 위치를 결정한다. 이 시점에 timing은 wire load model이 아닌 실제 위치 기반 추정치로 평가된다.
    4. **CTS** — clock tree를 합성해 모든 FF의 clock arrival skew를 최소화한다. CTS 이후 hold violation이 새로 생기는 경우가 흔하다.
    5. **Routing** — 신호선을 실제 금속 배선으로 완성한다. SI(crosstalk)와 DRC가 이 단계에서 확인된다.
    6. **Signoff** — STA(timing), IR drop, EM, DRC/LVS를 통과해야 tapeout이 가능하다.

## Q2. (Understand)

Setup violation 과 hold violation 중 *주파수 낮추기* 로 해결 가능한 것은? 이유는?

??? answer "정답 / 해설"
    **Setup**. Setup 부등식 `t_ck→q + t_logic + t_su ≤ T_clk − t_skew`에서 T_clk는 우변에만 나타난다. 주파수를 낮추면(T_clk 증가) 우변이 커지므로 데이터 경로가 가진 좌변의 지연이 아무리 커도 결국 만족시킬 수 있다.

    **Hold**는 `t_ck→q + t_logic ≥ t_hold + t_skew`로 T_clk 항이 전혀 없다. 주파수를 아무리 낮춰도 이 부등식에는 영향이 없다. Hold violation을 고치려면 데이터 경로에 buffer를 삽입해 `t_logic`을 늘려야 한다. 단, buffer 삽입은 해당 경로의 setup timing도 악화시키므로 setup margin과 동시에 점검해야 한다. 이 두 timing의 고치는 방법이 서로 다르다는 점이 면접 핵심이다.

## Q3. (Apply)

다음 RTL 패턴이 합성에서 자동으로 *ICG (Integrated Clock Gating)* 로 변환되는 이유는?
```systemverilog
always_ff @(posedge clk) begin
  if (en) reg <= data;
end
```

??? answer "정답 / 해설"
    `if (en)` 조건부 갱신 패턴은 합성 도구에게 "en=0일 때 이 레지스터의 값은 변하지 않아도 된다"는 의도를 명시적으로 전달한다. 도구는 두 가지 구현 중 하나를 선택할 수 있다. 하나는 "flop + feedback MUX" 구조로 clock이 항상 들어오고 en=0일 때 이전 값을 MUX가 재입력하는 방식이다. 다른 하나는 ICG(Integrated Clock Gating cell: latch + AND)로, en=0일 때 clock pulse 자체를 차단한다. ICG는 flop의 클럭 입력이 토글하지 않으므로 dynamic power(`C × V² × f` 중 clock activity 항)를 직접 제거한다. 합성 도구는 일반적으로 ICG를 선호하며, `set_clock_gating_style` 옵션으로 ICG 셀 타입과 적용 임계 개수를 제어한다.

## Q4. (Analyze)

Floorplan 직후 IR drop 이 hotspot 영역에서 nominal VDD 의 12% 초과 — 가능한 대응 방안 3가지?

??? answer "정답 / 해설"
    1. **PG mesh 보강** — 해당 hotspot 영역 위의 metal stripe density를 높이거나 상위 metal layer(저항 낮음)를 PG에 추가 할당한다. 저항 R이 줄면 I × R 강하가 직접 줄어든다.
    2. **Decap(decoupling cap) 추가** — 전류 피크가 발생하는 순간 인근 decap이 즉각적인 전하를 공급해 전압 강하의 transient 성분을 완화한다. decap은 switching cell 바로 옆 빈 공간에 배치할수록 효과적이다.
    3. **Switching 부하 분산** — 고활동도 플립플롭 그룹을 여러 영역으로 재배치해 한 점에 집중된 전류 피크를 공간적으로 분산시킨다. 이는 floorplan/placement 단계에서 해결해야 하며 라우팅 후에는 수정 비용이 크다.

    보너스: power gate된 블록의 wake-up rush current가 원인이면 sequential wakeup(flip 순서를 여러 사이클에 나눔)으로 피크 전류를 시간축으로 분산시킨다.

## Q5. (Distinguish)

OCV, AOCV, POCV 의 차이를 한 문장씩 답하라.

??? answer "정답 / 해설"
    - **OCV**: launch path와 capture path에 *고정 derating 계수*(예: late 1.05 / early 0.95)를 일괄 적용한다. 모든 path가 최악의 variation을 동시에 겪는다고 가정하므로 구현은 단순하지만 지나치게 비관적이어서 불필요하게 area/power를 낭비한다.
    - **AOCV**: variation이 path의 *stage 수*에 따라 통계적으로 평균화된다는 관찰을 반영한다. 긴 path일수록 random variation이 상쇄되어 더 작은 derate를, 짧은 path일수록 더 큰 derate를 적용한다. location 의존성도 함께 고려해 OCV보다 덜 비관적이다.
    - **POCV**: 각 cell delay를 평균 μ와 표준편차 σ의 *통계 분포*로 모델링하고, path delay의 sigma를 RSS(root-sum-square)로 합산한다. variation의 통계적 성질을 가장 정확히 반영하므로 세 방식 중 가장 덜 비관적이면서 신뢰성 높은 margin을 제공한다.

    면접 포인트: "왜 OCV에서 AOCV/POCV로 진화했는가"는 과도한 pessimism으로 인한 area/power 손실을 줄이면서도 충분한 timing margin을 유지하기 위함이다.

## Q6. (Evaluate)

MBFF (Multi-bit Flip-Flop) 가 *적합하지 않은* 시나리오는?

??? answer "정답 / 해설"
    MBFF는 여러 flop을 하나의 셀로 묶어 clock pin과 inverter를 공유함으로써 clock power와 area를 절감하는 기법이지만, 다음 상황에서는 그 이점이 손해로 뒤집힌다.

    1. **비트들이 서로 다른 source/destination으로 흩어지는 경우** — MBFF는 묶인 비트가 한 곳에 강제로 배치되므로, 각 비트가 멀리 떨어진 logic으로 연결되면 routing이 우회하면서 오히려 wire delay가 증가한다. clock power로 아낀 것보다 timing 손실이 커진다.
    2. **Critical path가 비트별로 다를 때** — 어떤 비트만 더 빠른(큰) flop으로 sizing하고 싶어도 MBFF는 묶인 비트를 일괄로만 변경할 수 있어 timing fix 자유도가 떨어진다.
    3. **Power gating 영역 경계** — MBFF가 두 power domain에 걸쳐 있으면 isolation cell 삽입과 retention 처리가 복잡해진다.

    면접에서는 "MBFF는 항상 좋다"가 아니라 "비트들이 공간적·시간적으로 응집되어 있을 때만 이득"이라는 조건부 판단을 보여야 한다.

## Q7. (Apply)

Synthesis 결과 timing OK 였는데 P&R 후 fail 의 흔한 원인 3가지를 답하라.

??? answer "정답 / 해설"
    합성 단계의 timing은 여러 이상화 가정 위에서 계산되므로, P&R 후 그 가정이 깨지면서 fail이 드러난다.

    1. **Wire delay 가정의 붕괴** — 합성은 cell 위치를 모르므로 wire load model(통계적 추정) 또는 zero wire delay를 가정한다. 실제 placement/routing 후 net이 예상보다 길어지면 wire delay가 추가되어 setup path가 fail한다.
    2. **Ideal clock 가정의 붕괴** — 합성 단계는 clock을 ideal(skew=0)로 본다. CTS 후 실제 insertion delay와 skew가 더해지면 setup margin이 잠식된다.
    3. **Crosstalk(SI) 등장** — 합성 시점에는 인접 배선이 없지만, routing 후 평행한 신호선 사이의 coupling capacitance가 aggressor→victim delay를 변화시킨다. 이는 SI-aware STA에서만 잡힌다.

    보너스: dynamic IR drop으로 인한 국부적 VDD 강하가 cell delay를 키워 timing fail을 유발할 수도 있다. 면접에서는 "합성 timing은 예측, P&R timing은 현실"이라는 프레임으로 답하면 깔끔하다.

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

    적용 순서와 책임 주체가 단계마다 다른 것이 핵심이다. Clock gating과 multi-Vt는 합성 도구가 자동으로 삽입·할당하므로 RTL 코딩 스타일(`if(en)` 패턴)과 라이브러리 설정이 좌우한다. Power gating은 어느 블록을 언제 끌지가 architectural 결정이므로 RTL/UPF 단계에서 power intent로 미리 정의해야 한다. DVFS는 정적 결정이 아니라 런타임 워크로드에 반응하는 제어이므로 펌웨어/OS의 power management가 담당한다. 즉 "정적으로 자동화할 수 있는 것(clock gating, multi-Vt) → 의도를 설계 단계에 명시해야 하는 것(power gating) → 런타임 소프트웨어가 동적으로 제어하는 것(DVFS)" 순으로 책임이 위로 올라간다.
