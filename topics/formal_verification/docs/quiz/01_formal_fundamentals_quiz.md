# Quiz — Module 01: Formal Fundamentals

[← Module 01 본문으로 돌아가기](../01_formal_fundamentals.md)

---

## Q1. (Remember)

Formal Verification의 3가지 결과를 나열하고 각각의 의미를 한 문장으로 답하세요.

??? answer "정답 / 해설"
    - **PROVEN**: 모든 입력에 대해 property 위반 불가 (수학적 증명).
    - **BOUNDED**: N cycle 내에는 위반 없음, N+1 이후는 미증명.
    - **CEX (Failed)**: property를 위반하는 입력 반례 발견.

## Q2. (Understand)

Simulation과 Formal의 가장 본질적인 차이를 한 문장으로 표현하세요.

??? answer "정답 / 해설"
    Simulation은 **시드/입력 조합을 일부 샘플링**하여 검증하고, Formal은 **모든 가능한 입력에 대해 명제를 증명**한다. 따라서 Sim은 corner case를 놓칠 수 있지만 Formal PROVEN은 무한 cycle 동안 안전.

## Q3. (Apply)

다음 시나리오에서 Formal이 적합/부적합을 판단하세요:

| 시나리오 | 적합? |
|----------|-------|
| (a) Round-robin arbiter 4-port |
| (b) 64-bit × 64-bit 곱셈기 결과 |
| (c) AXI handshake protocol |
| (d) 1MB cache의 데이터 일관성 |

??? answer "정답 / 해설"
    - (a) **적합** — 작은 FSM, starvation 부재 증명에 강력
    - (b) **부적합** — data path, state space 폭발 (2^128 입력 조합)
    - (c) **적합** — 프로토콜 규칙, deadlock/livelock 증명
    - (d) **부적합 (또는 abstraction 필요)** — 메모리 크기 자체가 state explosion. 작은 모델로 abstract하면 가능.

## Q4. (Analyze)

BOUNDED 결과가 PROVEN으로 전환되지 않을 때 가장 흔한 원인 두 가지는?

??? answer "정답 / 해설"
    1. **State explosion** — DUT의 state space가 너무 커서 induction이 수렴 못함. 대응: Blackbox / Abstraction / Cut Point
    2. **Inductive invariant 부족** — Inductive step에서 false invariant가 생성됨. 대응: 추가 assume 또는 helper assertion

## Q5. (Evaluate)

Formal PROVEN 결과를 받았을 때 sign-off 전에 추가로 확인해야 하는 것 두 가지는?

??? answer "정답 / 해설"
    1. **Cover가 모두 COVERED인가** — UNCOVERED면 Vacuous Pass 가능성. assert는 사실상 의미 없음.
    2. **Assume이 spec과 1:1 매핑되는가** — Over-constrained면 false PROVEN. 모든 assume에 대응 cover로 도달성 확인.

    추가로 (3) Blackbox 영역이 property에 영향 없는지 (COI 검토), (4) 모든 spec 규칙이 property로 표현되었는지 (완전성).
