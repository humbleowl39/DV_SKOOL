# Quiz — Module 02: SVA

[← Module 02 본문으로 돌아가기](../02_sva.md)

---

## Q1. (Remember)

SVA의 3가지 명령어(directive)와 각 역할을 답하세요.

??? answer "정답 / 해설"
    - **assert** — Property를 검증 (위반 시 fail).
    - **assume** — Formal에서 입력 제약 (실제 환경 모델링).
    - **cover** — 특정 시나리오 도달성 확인 (Vacuous Pass 방지).

    세 directive는 Formal 검증의 삼각 구조를 이룬다. assert는 DUT가 반드시 만족해야 할 규칙이고, assume은 환경(외부 입력)이 따를 것으로 가정하는 제약이며, cover는 그 규칙들이 실제로 "활성화된 적 있는가"를 보장한다. assert만 있고 cover가 없으면 vacuous pass를 감지할 수 없고, assume이 없거나 잘못되면 엔진이 불가능한 입력 조합을 시도해 false CEX가 나온다. 세 directive가 균형 있게 존재할 때 비로소 의미 있는 PROVEN을 얻는다.

## Q2. (Understand)

`a |-> b`와 `a |=> b`의 차이는?

??? answer "정답 / 해설"
    - `a |-> b` (overlapped implication): a와 b가 **같은 cycle**에 평가
    - `a |=> b` (non-overlapped implication): a 다음 cycle(`a ##1 b`와 동등)에 b 평가

    구별 안 하면 timing 오류 또는 Vacuous Pass 위험.

    implication 연산자 선택은 "응답이 같은 클록 에지에서 일어나느냐, 다음 에지에서 일어나느냐"에 대한 설계 의도의 직접 표현이다. 예를 들어 combinational logic처럼 req와 ack이 동일 사이클에 성립한다면 `|->` 가 맞지만, 파이프라인 레지스터를 거쳐 다음 사이클에 결과가 나오는 구조라면 `|=>` 또는 `##1`을 써야 한다. `|->`를 써야 할 곳에 `|=>`를 쓰면 1사이클 여유가 추가되어 실제 타이밍 위반이 PASS로 통과되고, 반대로 `|=>`를 써야 할 곳에 `->`를 쓰면 같은 사이클에서 b가 성립하지 않아 불필요한 CEX가 발생한다.

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

    자연어 사양을 SVA로 옮길 때 핵심은 세 가지다: 트리거 조건(valid), 시간 범위(1~5 사이클), 결과 조건(ready). `##[1:5]`는 exactly 1에서 5 사이 어느 사이클에서든 ready가 1이 되면 되므로 "1~5 cycle 내에"라는 표현에 정확히 대응한다. `disable iff (!rst_n)`을 빠뜨리면 reset 활성화 중에도 assertion이 동작해 reset 해제 직후 불필요한 CEX가 발생하므로 거의 모든 동기 assertion에 포함시켜야 한다. 이 assertion을 작성한 후에는 반드시 `cp_valid: cover property (@(posedge clk) valid);` 같은 cover를 짝지어 valid가 실제로 활성화되는지 확인해야 한다.

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

    Vacuous Pass가 위험한 이유는 결과만 보면 PROVEN이나 PASS처럼 보여 설계자가 안심하기 때문이다. implication `A |-> B`에서 A(antecedent)가 단 한 번도 true가 되지 않으면, 논리적으로 implication 전체는 항상 참이 되어 어떤 B도 검증하지 않은 채 PASS한다. 이를 탐지하는 유일한 방법이 cover이며, cover의 결과가 UNCOVERED라면 "assert가 한 번도 실질적으로 동작하지 않았다"는 신호다. 따라서 implication 형태의 모든 assert에는 antecedent를 목표로 하는 cover를 반드시 짝지어야 한다.

## Q5. (Apply)

Bind 사용의 가장 큰 장점을 한 문장으로 답하세요.

??? answer "정답 / 해설"
    **RTL을 수정하지 않고 외부에서 검증 모듈을 부착할 수 있어**, 검증과 설계를 격리하고 RTL 무결성을 유지하면서 SVA를 적용할 수 있다. 다중 인스턴스에 동일 SVA 일괄 적용도 가능.

    bind의 핵심 가치는 RTL 소스를 보호하면서도 원하는 신호를 직접 참조할 수 있다는 점이다. 검증 엔지니어가 RTL 파일을 수정하면 설계 히스토리가 오염되고, 검증 assertion이 제품 코드에 섞이는 위험이 생기지만, bind를 사용하면 검증 모듈은 별도 파일로 관리되고 RTL은 원본 그대로 유지된다. 또한 동일한 IP가 여러 곳에 인스턴스화된 설계에서 bind 한 줄로 모든 인스턴스에 일괄 적용할 수 있어, 인스턴스마다 SVA를 복사할 필요가 없다.
