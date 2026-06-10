---
title: "Quiz — Module 07: 왜 순서를 바꿔 실행하는가"
---

[← Module 07 본문으로 돌아가기](../../07_ooo_motivation/)

---

## Q1. (Remember)

OoO 코어의 명령 흐름 골격을 순서대로 나열한 것은?

- [ ] A. execute(in-order) → dispatch(OoO) → retire(OoO)
- [ ] B. dispatch(in-order) → execute(OoO) → retire(in-order)
- [ ] C. dispatch(OoO) → execute(in-order) → retire(OoO)
- [ ] D. fetch(OoO) → execute(OoO) → retire(OoO)

<details>
<summary>정답 / 해설</summary>

**B**. 명령은 program order 대로 ROB 에 들어가고(dispatch, in-order), operand 가 준비된 것부터 뒤섞여 실행되며(execute, out-of-order), 다시 program order 대로 완료 처리됩니다(retire, in-order). "들어올 땐 순서대로, 실행은 준비된 것부터, 나갈 땐 다시 순서대로" — 이 분리가 ROB 의 존재 이유이며, 검증 기대값은 항상 retire 순서를 기준으로 합니다.

</details>
## Q2. (Understand)

OoO 코어에서 "execution 은 out-of-order 인데 retirement 는 in-order" 라는 말의 의미는?

<details>
<summary>정답 / 해설</summary>

명령의 _실행_(issue/완료)은 operand 가 준비된 순서로 프로그램 순서와 무관하게 일어나지만, architectural state(레지스터·메모리의 관찰 가능한 값)를 갱신하는 _retire(commit)_ 는 ROB 가 program order 대로 수행한다는 뜻입니다. 그래서 cache-miss 한 load 뒤의 독립 명령이 먼저 실행 완료되어도, 최종 상태 변화는 program order 를 따릅니다. 검증에서 reference model 과 scoreboard 는 _완료 순서_ 가 아니라 _retire 순서_ 로 비교해야 하며, 이를 혼동하면 정상 동작을 mismatch 로 신고합니다.

</details>
## Q3. (Analyze)

`LW x1,0(x2)` 가 cache miss 로 100 사이클 대기하고, 바로 뒤 `ADD x3,x4,x5` 는 `x1` 과 무관하다. in-order 코어와 OoO 코어에서 ADD 의 운명이 어떻게 다른지, 그리고 그것이 왜 OoO 의 동기인지 분석하라.

<details>
<summary>정답 / 해설</summary>

in-order 코어에서는 ADD 가 LW 와 무관해도 LW 가 끝날 때까지 _함께 멈춥니다_ — 실행이 프로그램 순서에 묶여 있어 앞 명령이 stall 하면 뒤가 전부 막히기 때문입니다(100 사이클 낭비). OoO 코어는 LW 를 Reservation Station 에서 데이터 대기시킨 채, operand 가 준비된 ADD 를 _먼저 issue_ 해 functional unit 을 놀리지 않습니다. 단 ADD 가 먼저 실행 완료돼도 retire 는 LW→ADD 순서이므로 architectural state 는 program order 로 보존됩니다. "첫 해저드에서 독립 명령까지 멈추는 낭비를 없앤다" — 이것이 OoO 가 존재하는 이유입니다.

</details>
