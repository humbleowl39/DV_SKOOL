---
title: "Quiz — Module 03: 명령 한 줄의 일생"
---

[← Module 03 본문으로 돌아가기](../../03_life_of_an_instruction/)

---

## Q1. (Remember)

명령 하나가 실행되며 거치는 네 단계를 순서대로 나열한 것은?

- [ ] A. Decode → Fetch → Write-back → Execute
- [ ] B. Fetch → Decode → Execute → Write-back
- [ ] C. Execute → Fetch → Decode → Write-back
- [ ] D. Fetch → Execute → Decode → Write-back

<details>
<summary>정답 / 해설</summary>

**B**. Fetch(PC 가 가리키는 명령을 메모리에서 가져옴) → Decode(무슨 명령인지 해석 + 레지스터 값 읽기) → Execute(ALU 로 실제 연산) → Write-back(결과를 레지스터에 저장). 이 네 박자가 모든 명령의 공통 골격이며, 이 단계들을 여러 명령에 걸쳐 겹치면 파이프라인이 됩니다.

</details>
## Q2. (Apply)

`SUB x5, x6, x7` 은 무슨 일을 하는가? "동사 + 목적지 + 재료"로 설명하라.

<details>
<summary>정답 / 해설</summary>

동사 = SUB(빼라), 목적지 = `x5`(결과를 넣을 레지스터), 재료 = `x6` 과 `x7`. 즉 "`x6` 에서 `x7` 을 빼서(`x6 - x7`) 결과를 `x5` 에 넣어라"입니다. 산술 명령이므로 재료·목적지가 모두 레지스터이고, 이 명령도 fetch → decode(x6,x7 읽기) → execute(뺄셈) → write-back(x5 저장)의 네 박자를 거칩니다.

</details>
## Q3. (Understand)

PC(program counter)가 하는 일과, 분기(branch) 명령이 PC 와 어떻게 관련되는지 설명하라.

<details>
<summary>정답 / 해설</summary>

PC 는 "다음에 실행할 명령의 주소"를 담은 레지스터입니다. 명령 하나가 끝날 때마다 보통 다음 명령을 가리키도록 증가해 _순차 실행_ 을 만듭니다. 분기(branch) 명령은 이 PC 를 _다른 주소로 바꿔_ 실행 흐름을 점프시킵니다 — if 문이 조건에 따라 다른 코드로 가거나 반복문이 처음으로 되돌아가는 것이 모두 PC 변경으로 구현됩니다. 즉 프로그램의 모든 흐름 제어는 "PC 를 어떻게 갱신하느냐"로 귀결되며, 이 때문에 분기는 명령을 미리 당겨오는 빠른 CPU 에서 까다로운 문제가 됩니다([M06](../../06_pipeline_hazard/)·[M09](../../09_branch_prediction/)).

</details>
