# Quiz — Module 02: SVA

[← Module 02 본문으로 돌아가기](../02_sva.md)

---

## Q1. (Remember)

SVA의 3가지 명령어(directive)와 각 역할을 답하세요.

??? answer "정답 / 해설"
    - **assert** — Property를 검증 (위반 시 fail).
    - **assume** — Formal에서 입력 제약 (실제 환경 모델링).
    - **cover** — 특정 시나리오 도달성 확인 (Vacuous Pass 방지).

## Q2. (Understand)

`a |-> b`와 `a |=> b`의 차이는?

??? answer "정답 / 해설"
    - `a |-> b` (overlapped implication): a와 b가 **같은 cycle**에 평가
    - `a |=> b` (non-overlapped implication): a 다음 cycle(`a ##1 b`와 동등)에 b 평가

    구별 안 하면 timing 오류 또는 Vacuous Pass 위험.

## Q3. (Apply)

다음 자연어 사양을 SVA로 작성하세요: "valid가 1이면 1~5 cycle 내에 ready가 1이 되어야 한다."

??? answer "정답 / 해설"
    ```systemverilog
    ap_ready_within_5: assert property (
      @(posedge clk) disable iff (!rst_n)
      valid |-> ##[1:5] ready
    );
    ```

    `disable iff (!rst_n)`은 reset 중 비활성화 — 거의 모든 SVA에 권장.

## Q4. (Analyze)

다음 SVA가 Vacuous Pass를 일으키는 패턴인가? 그 이유는?

```systemverilog
ap_x: assert property (
  @(posedge clk) (state == IDLE) |-> (counter == 0)
);
```

??? answer "정답 / 해설"
    **잠재적으로 Vacuous Pass 가능**. `state == IDLE`이 한 번도 발생하지 않으면 antecedent가 항상 false → property는 자동 PASS, 하지만 사실상 검증 안 됨.

    방지: 짝지은 cover 작성:
    ```systemverilog
    cp_x: cover property (@(posedge clk) state == IDLE);
    ```

    cover가 UNCOVERED면 assert는 의미 없는 PASS — Vacuous Pass.

## Q5. (Apply)

Bind 사용의 가장 큰 장점을 한 문장으로 답하세요.

??? answer "정답 / 해설"
    **RTL을 수정하지 않고 외부에서 검증 모듈을 부착할 수 있어**, 검증과 설계를 격리하고 RTL 무결성을 유지하면서 SVA를 적용할 수 있다. 다중 인스턴스에 동일 SVA 일괄 적용도 가능.
