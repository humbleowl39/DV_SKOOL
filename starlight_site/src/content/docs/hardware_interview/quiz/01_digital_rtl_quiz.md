---
title: "Quiz — Unit 1: Digital Design / RTL"
---

본 모듈의 핵심 개념 이해도를 점검합니다. 정답은 펼치면 보입니다.

[← Unit 1 본문으로 돌아가기](../../01_digital_rtl/)

---

## Q1. (Remember)

`always_ff` 블록에서 사용해야 하는 대입 연산자는?

- [ ] A. `=` (blocking)
- [ ] B. `<=` (non-blocking)
- [ ] C. `assign`
- [ ] D. `==`

<details>
<summary>정답 / 해설</summary>

**B**. `always_ff` 는 플립플롭을 모델링하는 블록으로, 같은 클럭 엣지에 트리거된 모든 대입이 *동시에* 완료되어야 회로의 동작을 올바르게 묘사한다. non-blocking `<=` 는 우변을 현재 사이클에 평가한 뒤 다음 델타 사이클에 좌변에 반영하므로, 병렬 플립플롭의 동시 갱신 의미를 그대로 표현한다. A(blocking `=`)를 쓰면 코드 순서대로 값이 덮어써져 시프트 레지스터가 콤비네이션 회로처럼 동작하는 시뮬-합성 불일치가 발생하고, C(assign)와 D(`==`)는 문법 자체가 다른 목적의 구문이다.

</details>
## Q2. (Understand)

Mealy 와 Moore FSM 의 가장 큰 *타이밍* 차이는?

<details>
<summary>정답 / 해설</summary>

**Moore**: 출력이 현재 `state` 만의 함수이므로 출력이 레지스터(flop)를 통해 나온다. 클럭 엣지에서만 변하므로 glitch가 없고, 입력 변화로부터 1-사이클 지연이 생긴다. **Mealy**: 출력이 `state + input`의 조합 함수이므로 입력 변화에 즉시 반응한다. 이는 지연이 없다는 장점이지만, 입력에 glitch가 있으면 출력에도 glitch가 전파된다는 타이밍 위험을 동반한다. 즉 Moore는 안전하고 느리며, Mealy는 빠르지만 glitch 위험이 있는 trade-off 관계다.

</details>
## Q3. (Apply)

Setup 부등식 `t_ck→q + t_logic + t_su ≤ T_clk − t_skew` 에서, *positive skew (capture clock 이 더 늦게 도착)* 가 setup margin 에 미치는 영향은?

- [ ] A. Setup margin 감소
- [ ] B. Setup margin 증가
- [ ] C. 영향 없음
- [ ] D. Hold 만 영향

<details>
<summary>정답 / 해설</summary>

**B**. Setup 부등식의 우변(`T_clk − t_skew`)에서 t_skew는 *positive skew일 때 음수*로 들어간다. 즉 capture clock이 늦을수록 우변이 커져 데이터가 도착할 수 있는 시간이 늘어나 setup margin이 증가한다. A는 반대의 논리다. C와 D는 틀렸는데, 같은 positive skew가 hold 부등식(`t_ck→q + t_logic ≥ t_hold + t_skew`)에서는 우변을 크게 만들어 hold margin을 *줄이는* 방향으로 작용하기 때문이다. 면접에서는 "setup에 좋은 skew가 hold에는 나쁘다"는 역관계를 반드시 함께 말해야 한다.

</details>
## Q4. (Analyze)

다음 코드의 버그는?
```systemverilog
always_ff @(posedge clk) begin
  q1 = d;
  q2 = q1;
end
```

<details>
<summary>정답 / 해설</summary>

`=`(blocking)를 사용했으므로 `q1 = d`가 먼저 실행 완료된 뒤 `q2 = q1`이 실행된다. 이 시점에 q1은 이미 새 값 d를 가리키므로, q2도 d와 같은 값이 된다. 결과적으로 2단 시프트 레지스터가 아니라 두 레지스터가 동일 사이클에 d로 동시에 갱신되는 것처럼 동작한다. 올바른 시프트 레지스터는 각 레지스터가 *이전 사이클 값*을 전달해야 하므로 non-blocking `<=`로 바꿔야 한다.

**수정**: `<=` 사용.
```systemverilog
always_ff @(posedge clk) begin
  q1 <= d;
  q2 <= q1;
end
```

</details>
## Q5. (Apply)

10 MHz 도메인의 1-bit done 신호를 100 MHz 도메인으로 전달하는 가장 안전한 회로는?

<details>
<summary>정답 / 해설</summary>

**2-FF synchronizer**:
```systemverilog
always_ff @(posedge clk_100M) begin
  {sync_q1, sync_q2} <= {async_done, sync_q1};
end
// 사용: sync_q2
```
1단 플립플롭만으로는 setup/hold 위반 시 metastability가 해소될 시간이 없어 다음 스테이지에 잘못된 값이 전파될 수 있다. 2단 구조는 첫 번째 플립플롭이 metastable 상태에 빠지더라도 한 사이클 안에 확정 전압으로 수렴할 확률이 매우 높고, 두 번째 플립플롭이 이미 안정된 값을 받는 구조다. 단, source 도메인 펄스가 destination 클럭(100MHz) 1사이클(10ns)보다 짧으면 첫 번째 플립플롭이 아예 샘플링을 못 할 수 있으므로 source에서 최소 2사이클 이상 유지하거나 pulse stretcher를 추가해야 한다.

</details>
## Q6. (Analyze)

Multi-bit bus 를 클럭 도메인 간 직접 sync 하면 안 되는 *근본 이유* 는?

<details>
<summary>정답 / 해설</summary>

1-bit 신호는 2-FF 동기화로 처리할 수 있지만, multi-bit 버스에서는 각 비트의 전파 지연과 transition 시점이 서로 다르다. destination 클럭이 전환 도중의 어느 한 순간을 샘플링하면 비트마다 *다른 사이클에 latch*된 값이 섞이는 "torn read"가 발생한다. 예를 들어 0x0FFF → 0x1000 전환 중 0x10FF 같은 존재하지 않는 중간 값이 수신 측에 보일 수 있다. 이것이 잘못된 주소나 데이터로 해석되면 심각한 기능 오류가 된다. 해결책은 req/ack **handshake**(source가 모든 비트를 안정시킨 뒤 req 신호를 동기화)이거나, 카운터 포인터라면 **Gray code + 2-FF 동기화**, 데이터 버퍼라면 **async FIFO**를 사용하는 것이다.

</details>
## Q7. (Evaluate)

AXI vs AHB 선택 — 다음 상황에서 어느 것을?

> "Cortex-M MCU 의 디버그 트레이스 버스. Single master(debug probe), peripheral 4 개, throughput 무관, 면적 우선."

<details>
<summary>정답 / 해설</summary>

**AHB**. 이 시나리오는 단일 master, 소수의 peripheral, 낮은 throughput 요구사항이므로 AXI의 5채널 구조(AR/R/AW/W/B)가 오히려 면적·전력 낭비다. AHB(-Lite)는 단일 master를 위한 단순 파이프라인 구조로 구현 비용이 낮다. AXI가 진가를 발휘하는 상황은 multi-master, OOO(out-of-order) 응답, 고대역폭 burst가 동시에 필요한 메모리 컨트롤러나 NoC 인터커넥트다. 면접에서는 단순히 "AHB가 더 작다"가 아니라 "single-master + low-bandwidth에서 AXI의 5채널 overhead가 ROI가 없다"는 논거를 제시해야 한다.

</details>
## Q8. (Create)

Async FIFO 의 empty 와 full 판정에 *Gray code pointer* 를 쓰는 이유를 한 문장으로 답하라.

<details>
<summary>정답 / 해설</summary>

Binary 포인터는 한 번에 여러 비트가 동시에 변할 수 있다(예: 0111 → 1000은 4비트 변경). CDC를 건너는 순간 각 비트가 서로 다른 타이밍에 latch되면 존재하지 않는 중간 포인터 값이 생기고, 이를 읽은 수신측은 full이나 empty를 잘못 판정한다. Gray code는 인접한 두 값 사이에서 반드시 1비트만 변하므로, 전환 도중 어느 타이밍에 샘플링되더라도 직전 또는 직후의 유효한 포인터 값만 관찰된다. 이로 인해 empty/full 판정의 최악 결과는 "1사이클 늦게 알아채는 것"이지 잘못된 데이터 판정이 아니다. 이것이 async FIFO 설계에서 Gray code pointer가 사실상 표준인 이유다.

</details>
