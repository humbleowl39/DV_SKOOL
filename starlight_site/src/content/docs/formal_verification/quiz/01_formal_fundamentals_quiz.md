---
title: "Quiz — Module 01: Formal Fundamentals"
---

[← Module 01 본문으로 돌아가기](../../01_formal_fundamentals/)

---

## Q1. (Remember)

Formal Verification의 3가지 결과를 나열하고 각각의 의미를 한 문장으로 답하세요.

<details>
<summary>정답 / 해설</summary>

- **PROVEN**: 모든 입력에 대해 property 위반 불가 (수학적 증명).
- **BOUNDED**: N cycle 내에는 위반 없음, N+1 이후는 미증명.
- **CEX (Failed)**: property를 위반하는 입력 반례 발견.

세 결과는 서로 배타적이면서 검증의 신뢰 수준을 직접 나타낸다. PROVEN은 "이 DUT는 property를 영원히 지킨다"는 수학적 보증이고, BOUNDED는 "N 스텝까지는 확인했다"는 부분 보증이며, CEX는 "이 입력 순서에서 위반이 발생한다"는 구체적 증거다. CEX는 버그 수정의 출발점이 되므로 실패가 아니라 정보 획득이다. 시뮬레이션에서 "테스트 통과"는 PROVEN이 아니라 특정 시나리오에서의 BOUNDED에 불과하다는 점을 인식하는 것이 Formal 학습의 첫 걸음이다.

</details>
## Q2. (Understand)

Simulation과 Formal의 가장 본질적인 차이를 한 문장으로 표현하세요.

<details>
<summary>정답 / 해설</summary>

Simulation은 **시드/입력 조합을 일부 샘플링**하여 검증하고, Formal은 **모든 가능한 입력에 대해 명제를 증명**한다. 따라서 Sim은 corner case를 놓칠 수 있지만 Formal PROVEN은 무한 cycle 동안 안전.

이 차이는 "검사의 완전성"에서 나온다. 시뮬레이션은 설계자가 상상한 시나리오만 테스트하므로 상상 밖의 입력 조합은 영구히 미검증 상태로 남는다. Formal은 solver가 가능한 모든 입력 공간을 탐색하므로 "이 경우는 생각 못 했다"는 빈 틈이 없다. 단, Formal도 표현된 property 범위 안에서만 완전하기 때문에 SVA 자체가 spec을 잘못 표현하면 PROVEN은 여전히 틀릴 수 있다.

</details>
## Q3. (Apply)

다음 시나리오에서 Formal이 적합/부적합을 판단하세요:

| 시나리오 | 적합? |
|----------|-------|
| (a) Round-robin arbiter 4-port |
| (b) 64-bit × 64-bit 곱셈기 결과 |
| (c) AXI handshake protocol |
| (d) 1MB cache의 데이터 일관성 |

<details>
<summary>정답 / 해설</summary>

- (a) **적합** — 작은 FSM, starvation 부재 증명에 강력
- (b) **부적합** — data path, state space 폭발 (2^128 입력 조합)
- (c) **적합** — 프로토콜 규칙, deadlock/livelock 증명
- (d) **부적합 (또는 abstraction 필요)** — 메모리 크기 자체가 state explosion. 작은 모델로 abstract하면 가능.

Formal의 적합성은 **state space 크기**와 **spec 표현 가능성**으로 판단한다. (a) Round-robin arbiter는 상태 수가 적고 "모든 포트가 결국 grant를 받는다"는 liveness property를 명확히 표현할 수 있어 Formal에 최적이다. (b)처럼 64×64 곱셈기는 입력 공간이 2의 128승에 달해 solver가 수렴하지 못하므로 Formal 대신 equivalence checking이나 시뮬레이션이 적합하다. (c) AXI handshake는 valid/ready 조합이 유한하고 protocol rule이 명제로 쉽게 변환되어 (a)와 함께 Formal의 대표 사례다. (d)는 메모리 자체 크기가 state explosion을 일으키지만, 작은 캐시 라인 수로 abstract하면 일부 property는 검증 가능하다.

</details>
## Q4. (Analyze)

BOUNDED 결과가 PROVEN으로 전환되지 않을 때 가장 흔한 원인 두 가지는?

<details>
<summary>정답 / 해설</summary>

1. **State explosion** — DUT의 state space가 너무 커서 induction이 수렴 못함. 대응: Blackbox / Abstraction / Cut Point
2. **Inductive invariant 부족** — Inductive step에서 false invariant가 생성됨. 대응: 추가 assume 또는 helper assertion

BOUNDED가 PROVEN이 되지 않는 이유는 수학적 귀납법의 두 단계 중 하나가 성립하지 않기 때문이다. 첫 번째 원인인 state explosion은 DUT가 너무 많은 상태를 가져 solver가 탐색을 마치지 못하는 것이고, Cut Point나 Abstraction으로 탐색 범위를 줄이면 해결된다. 두 번째 원인인 inductive invariant 부족은 귀납 단계에서 "N cycle이 안전하면 N+1도 안전하다"를 증명할 때 충분한 불변조건이 없어 false counter-path가 생성되는 것이다. 이 경우 helper assertion으로 중간 불변조건을 명시하면 solver가 귀납을 완성할 수 있다.

</details>
## Q5. (Evaluate)

Formal PROVEN 결과를 받았을 때 sign-off 전에 추가로 확인해야 하는 것 두 가지는?

<details>
<summary>정답 / 해설</summary>

1. **Cover가 모두 COVERED인가** — UNCOVERED면 Vacuous Pass 가능성. assert는 사실상 의미 없음.
2. **Assume이 spec과 1:1 매핑되는가** — Over-constrained면 false PROVEN. 모든 assume에 대응 cover로 도달성 확인.

추가로 (3) Blackbox 영역이 property에 영향 없는지 (COI 검토), (4) 모든 spec 규칙이 property로 표현되었는지 (완전성).

PROVEN 결과 자체는 신뢰의 필요조건이지 충분조건이 아니다. Cover가 UNCOVERED이면 assert의 antecedent가 실제로 한 번도 활성화되지 않은 것으로, "아무것도 검증하지 않고 PASS한" vacuous 상태다. Assume 감사는 over-constraint 여부를 확인하기 위한 것으로, assume이 실제 환경보다 입력을 과도하게 제한하면 DUT가 버그를 가져도 PROVEN이 나올 수 있다. 이 두 가지를 확인하지 않은 PROVEN은 서명 전 결함을 놓칠 수 있는 가장 위험한 시나리오다.

</details>
