---
title: "Quiz — Module 02: Step-and-Compare Lockstep"
---

[← Module 02 본문으로 돌아가기](../../02_step_and_compare/)

---

## Q1. (Remember)

step-and-compare lockstep 에서 RTL 코어와 ISS 의 architectural state 를 비교하는 시점은?

- [ ] A. 매 클럭 사이클
- [ ] B. 명령 fetch 시점
- [ ] C. 명령 execute 시점
- [ ] D. 명령 retire(commit) 시점

<details>
<summary>정답 / 해설</summary>

**D**. architectural state 는 retire(commit) 시점에 프로그램 순서로 확정되므로 비교도 retire 시점에 합니다. A(매 사이클)는 ISS 가 타이밍을 모델링하지 않아 불가능하고, B(fetch)는 아직 실행 전이며, C(execute)에는 폐기될 수 있는 추측 실행 결과가 섞여 ISS 와 구조적으로 어긋납니다.

</details>

## Q2. (Understand)

ISS 가 명령의 실행 사이클 수를 모르는데도 RTL 과의 비교가 성립하는 이유를 한 문장으로 설명하라.

<details>
<summary>정답 / 해설</summary>

비교 단위가 사이클이 아니라 retire 라는 논리적 사건이기 때문입니다 — ISS 는 명령이 architectural state 를 어떻게 바꾸는지(값)는 정확히 알고, step-and-compare 는 RTL 이 한 명령을 retire 할 때마다 ISS 를 한 스텝 진행시켜 그 architectural 결과만 비교하므로 타이밍 무지가 비교에 영향을 주지 않습니다.

</details>

## Q3. (Apply)

RTL 이 retire 한 명령에 대해 ISS 를 끌고 갈 때, retire 정보로 ISS step 에 함께 전달해야 하는 비결정/구현정의 요소를 한 가지 들고 이유를 설명하라.

<details>
<summary>정답 / 해설</summary>

**비동기 인터럽트의 발생 시점(어느 명령 경계에서 받았는지)** 이 대표적입니다. ISS 는 ISA 의미만 알 뿐 RTL 이 인터럽트를 _언제_ 받았는지는 모르므로, RTL 이 "이 명령 경계에서 인터럽트/trap 발생"을 알려줘야 ISS 도 같은 경계에서 trap 을 산출해 mepc/mcause 등을 동일하게 갱신합니다. (이 외에 mcycle/minstret 같은 시간 CSR, 구현정의 reset 값도 동기화 대상입니다.)

</details>

## Q4. (Analyze)

긴 프로그램을 돌렸더니 mismatch 가 명령 #14237 부터 시작해 그 뒤 수천 개에서 전부 발생했다. 디버그를 위해 가장 먼저 집중해야 할 것은?

- [ ] A. mismatch 가 가장 많이 난 구간
- [ ] B. 첫 divergence 인 명령 #14237 단 하나
- [ ] C. 마지막 mismatch 명령
- [ ] D. mismatch 명령들의 평균 PC

<details>
<summary>정답 / 해설</summary>

**B**. 첫 divergence(#14237)가 root cause 이고, 그 이후 수천 개는 이미 어긋난 상태에서 실행된 cascading(오염 전파)입니다. 첫 명령의 종류·피연산자·직전 파이프라인 정렬만 보면 됩니다. A·C·D 는 모두 cascading 결과를 보는 것이라 원인 규명에 무의미하며, 이것이 step-and-compare 가 첫 divergence 에서 멈추거나 명확히 표시하는 이유입니다.

</details>

## Q5. (Evaluate)

"divergence 가 잡혔으니 무조건 RTL(DUT) 버그로 Jira 를 끊자"는 제안을 평가하라.

<details>
<summary>정답 / 해설</summary>

**성급합니다 — divergence 는 RTL 버그·reference model 버그·TB 동기화 버그 셋 다일 수 있습니다.** 특히 "인터럽트가 있는 모든 테스트가 일관되게 발산"처럼 _체계적_ 패턴이면 비결정 요소(인터럽트 시점, 시간 CSR) 동기화 누락이라는 TB 버그일 가능성이 높습니다. 올바른 순서는 (1) ISS 초기화·동기화가 RTL 과 일치하는지 확인, (2) 특정 명령·정렬에서만 _국소적으로_ 재현되는지 확인 후, 그래도 RTL 로직이 ISA 사양과 어긋나면 그때 DUT 버그로 분류해 file 하는 것입니다. Spike 같은 널리 검증된 ISS 라도 비결정 요소까지 알지는 못합니다.

</details>
