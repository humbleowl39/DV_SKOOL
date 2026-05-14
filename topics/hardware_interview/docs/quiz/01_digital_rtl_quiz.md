# Quiz — Unit 1: Digital Design / RTL

본 모듈의 핵심 개념 이해도를 점검합니다. 정답은 펼치면 보입니다.

[← Unit 1 본문으로 돌아가기](../01_digital_rtl.md)

---

## Q1. (Remember)

`always_ff` 블록에서 사용해야 하는 대입 연산자는?

- [ ] A. `=` (blocking)
- [ ] B. `<=` (non-blocking)
- [ ] C. `assign`
- [ ] D. `==`

??? answer "정답 / 해설"
    **B**. 순차 회로에서는 모든 flop 이 동일 클럭 엣지에 동시 갱신되어야 하므로 non-blocking `<=` 사용. blocking 사용 시 race / 시뮬-합성 불일치 위험.

## Q2. (Understand)

Mealy 와 Moore FSM 의 가장 큰 *타이밍* 차이는?

??? answer "정답 / 해설"
    **Moore**: 출력이 `state` 만의 함수 → 출력은 *flop* 에서 나옴 → glitch-free, 1-cycle 지연.
    **Mealy**: 출력이 `state + input` 의 *조합* → input 변화 즉시 반응, glitch 위험.

## Q3. (Apply)

Setup 부등식 `t_ck→q + t_logic + t_su ≤ T_clk − t_skew` 에서, *positive skew (capture clock 이 더 늦게 도착)* 가 setup margin 에 미치는 영향은?

- [ ] A. Setup margin 감소
- [ ] B. Setup margin 증가
- [ ] C. 영향 없음
- [ ] D. Hold 만 영향

??? answer "정답 / 해설"
    **B**. Capture 가 늦게 도착하면 데이터가 도착할 시간이 더 생긴다 → setup 여유 ↑. 단, hold 는 *악화* — 같은 skew 가 hold 분석에서는 반대로 작용.

## Q4. (Analyze)

다음 코드의 버그는?
```systemverilog
always_ff @(posedge clk) begin
  q1 = d;
  q2 = q1;
end
```

??? answer "정답 / 해설"
    `=` (blocking) 사용 → q1 즉시 갱신 후 q2 = q1 이 *이미 새 값* 을 읽음 → q2 도 d 와 같아짐 (shift register 가 안 됨).

    **수정**: `<=` 사용.
    ```systemverilog
    always_ff @(posedge clk) begin
      q1 <= d;
      q2 <= q1;
    end
    ```

## Q5. (Apply)

10 MHz 도메인의 1-bit done 신호를 100 MHz 도메인으로 전달하는 가장 안전한 회로는?

??? answer "정답 / 해설"
    **2-FF synchronizer**:
    ```systemverilog
    always_ff @(posedge clk_100M) begin
      {sync_q1, sync_q2} <= {async_done, sync_q1};
    end
    // 사용: sync_q2
    ```
    단, async pulse 가 100MHz 의 1 cycle 보다 짧으면 dst 도메인이 못 잡음 — source 도메인에서 *최소 2 cycle 이상* 유지하거나 pulse stretcher 추가.

## Q6. (Analyze)

Multi-bit bus 를 클럭 도메인 간 직접 sync 하면 안 되는 *근본 이유* 는?

??? answer "정답 / 해설"
    각 비트가 *비동기적으로 transition* 하므로 destination 클럭이 비트마다 *다른 cycle* 에 latch 할 수 있다 → 중간 값(예: 0x1000 ↔ 0x1FFF 사이의 0x10FF) 이 *잠시 보임* → 잘못된 데이터로 사용. **Handshake 또는 async FIFO + Gray code** 필요.

## Q7. (Evaluate)

AXI vs AHB 선택 — 다음 상황에서 어느 것을?

> "Cortex-M MCU 의 디버그 트레이스 버스. Single master(debug probe), peripheral 4 개, throughput 무관, 면적 우선."

??? answer "정답 / 해설"
    **AHB**. Single-master + 단순 burst 만 필요 → AXI 의 5-channel overhead 가 낭비. AHB 5 또는 AHB-Lite 가 면적/디버그 측면 우수.

    AXI 는 *multi-master + OOO + high-bandwidth* 가 진가를 발휘.

## Q8. (Create)

Async FIFO 의 empty 와 full 판정에 *Gray code pointer* 를 쓰는 이유를 한 문장으로 답하라.

??? answer "정답 / 해설"
    Multi-bit binary pointer 를 그대로 sync 하면 비트들이 *다른 시점* 에 latch 되어 잘못된 중간 값이 보이지만, Gray code 는 한 번에 1 비트만 변하므로 *중간 값* 도 *유효한 인접 pointer* 가 되어 empty/full 판정이 안전하다.
