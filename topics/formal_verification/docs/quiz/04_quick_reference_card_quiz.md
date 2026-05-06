# Quiz — Module 04: Formal Quick Reference

[← Module 04 본문으로 돌아가기](../04_quick_reference_card.md)

---

## Q1. (Recall)

다음 SVA 연산자의 의미를 한 줄로:

- `##N`
- `##[1:N]`
- `[*N]`
- `[->N]`
- `throughout`

??? answer "정답 / 해설"
    - `##N` — 정확히 N cycle 후
    - `##[1:N]` — 1~N cycle 사이 어딘가에서
    - `[*N]` — 정확히 N번 연속 발생
    - `[->N]` — N번 발생할 때까지 (비연속 가능)
    - `throughout` — 표현식이 시퀀스 전체 동안 참 (예: `req throughout (##[1:5] ack)`)

## Q2. (Understand)

PROVEN 결과를 받았는데 cover가 UNCOVERED라면 어떻게 해석해야 하는가?

??? answer "정답 / 해설"
    **Vacuous Pass 의심**. Property의 antecedent에 도달하지 못한 것 → assert는 검사할 게 없어서 PASS. 사실상 무의미한 증명.

    행동: cover가 UNCOVERED인 이유 분석 → assume이 너무 강해 antecedent 차단했는지, 또는 RTL/spec에 모순이 있는지 확인.

## Q3. (Apply)

BOUNDED N=20을 받았다. PROVEN으로 만들기 위해 첫 번째로 시도할 기법은?

??? answer "정답 / 해설"
    **Cut Point** 또는 **Abstraction** 먼저 — 가장 적은 위험으로 state space를 축소하는 기법.

    Blackbox는 그 영역 동작을 검증 안 한 것이므로 sign-off 시 명시 필요. Assume tightening은 over-constraint 위험이 있으므로 마지막 수단.

## Q4. (Analyze)

다음 두 SVA 중 어느 것이 데이터 캡처가 필요한가?

```systemverilog
// (a)
a1: assert property (req |-> ##5 ack);

// (b)
a2: assert property (write |-> ##[1:10] (read && rdata == wdata));
```

??? answer "정답 / 해설"
    **(b)**. write 시점의 wdata를 read 시점에 비교해야 하므로 **Local Variable**이 필요.

    수정:
    ```systemverilog
    a2: assert property (
      logic [31:0] saved;
      (write, saved = wdata) |-> ##[1:10] (read && rdata == saved)
    );
    ```

## Q5. (Evaluate)

다음 중 Formal이 **가장 강력한** 적용 영역은?

- [ ] A. 1MB SRAM의 모든 셀 read-back
- [ ] B. AXI handshake protocol compliance
- [ ] C. 큰 곱셈기의 출력 정확성
- [ ] D. CPU 실행 trace 검증

??? answer "정답 / 해설"
    **B**. Protocol 검증은 작은 control logic + 명확한 spec rule → Formal의 sweet spot.

    A: state space 폭발(2^(8M)). C: data path, abstraction 필요. D: 실행 trace는 시뮬레이션 영역.
