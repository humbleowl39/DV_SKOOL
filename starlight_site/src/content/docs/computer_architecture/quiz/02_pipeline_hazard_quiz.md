---
title: "Quiz — Module 02: 5-Stage Pipeline & Hazard"
---

[← Module 02 본문으로 돌아가기](../../02_pipeline_hazard/)

---

## Q1. (Remember)

전형적 5-stage RISC 파이프라인의 단계 순서는?

- [ ] A. ID → IF → EX → WB → MEM
- [ ] B. IF → ID → EX → MEM → WB
- [ ] C. IF → EX → ID → MEM → WB
- [ ] D. IF → ID → MEM → EX → WB

<details>
<summary>정답 / 해설</summary>

**B**. IF(Instruction Fetch) → ID(Instruction Decode/Register Read) → EX(Execute/Address Calculate) → MEM(Memory Access) → WB(Write Back). 명령을 읽고(IF), 디코드하며 레지스터를 읽고(ID), ALU 연산/주소 계산(EX), 메모리 접근(MEM), 결과 기록(WB)의 자연스러운 순서입니다. 메모리 접근(MEM)이 실행(EX) _뒤_ 에 오는 이유는 EX 에서 load/store 의 유효 주소를 계산한 뒤 그 주소로 접근해야 하기 때문입니다.

</details>
## Q2. (Understand)

RAW(Read After Write) 해저드가 가장 흔한 데이터 해저드인 이유는?

<details>
<summary>정답 / 해설</summary>

RAW 는 _진짜 의존성(true dependency)_ 입니다 — 명령 N 이 명령 N-1 이 계산하는 레지스터 값을 실제로 필요로 하는 경우로, 프로그램의 데이터 흐름 자체에서 자연스럽게 발생합니다. 반면 WAW(같은 레지스터에 두 번 쓰기)와 WAR(이전 명령이 읽기 전에 쓰기)는 _이름만 같은_ 가짜 의존성이라, 순서대로 쓰기가 일어나는 in-order 5-stage 파이프라인에서는 WAR 이 불가능하고 WAW 도 드뭅니다. RAW 는 대부분 forwarding(EX→EX bypass)으로 해소되지만, load-use 의 경우만 1 bubble 이 남습니다.

</details>
## Q3. (Apply)

`LW x1, 0(x2)` 직후 `ADD x3, x1, x4` 가 올 때 forwarding 이 있어도 몇 사이클 bubble 이 필요한가?

- [ ] A. 0 (forwarding 으로 완전 해소)
- [ ] B. 1
- [ ] C. 2
- [ ] D. 3

<details>
<summary>정답 / 해설</summary>

**B**. load-use 해저드입니다. load 의 데이터는 MEM 단계가 _끝나야_ 준비되는데, ADD 가 한 사이클 뒤따라오면 ADD 의 EX 가 LW 의 MEM 과 같은 사이클에 놓여 `x1` 이 아직 없습니다. 따라서 ADD 의 EX 를 한 사이클 늦춰(1 bubble) LW 의 MEM 결과를 다음 사이클 EX 입력으로 forward 해야 합니다. 산술→산술 RAW 라면 EX→EX forwarding 으로 0 bubble(A)이 되지만, load→use 는 데이터 가용 시점이 한 단계 늦어 1 bubble 이 구조적으로 불가피합니다.

</details>
## Q4. (Analyze)

단순 in-order 5-stage 파이프라인에서 WAR 해저드가 발생하지 않는 이유를 분석하라.

<details>
<summary>정답 / 해설</summary>

WAR(Write After Read)는 뒤 명령이 앞 명령이 _읽기 전에_ 같은 레지스터에 쓰는 경우입니다. in-order 5-stage 파이프라인에서는 모든 명령이 같은 단계 순서(ID 에서 읽기, WB 에서 쓰기)를 거치고 _프로그램 순서대로_ 진행하므로, 앞 명령의 레지스터 읽기(ID)는 항상 뒤 명령의 쓰기(WB)보다 먼저 일어납니다(앞 명령이 파이프라인에 먼저 들어왔으므로). 즉 쓰기가 읽기를 추월할 구조적 경로가 없습니다. WAR 이 진짜 문제가 되는 것은 명령이 _순서를 벗어나_ 실행되는 OoO(M03)에서이며, 그곳에서 register renaming 으로 이름 충돌을 제거합니다.

</details>
## Q5. (Evaluate)

분기가 많고 예측이 어려운 워크로드에서 파이프라인을 더 깊게 만드는 것이 좋은 선택인지 평가하라.

<details>
<summary>정답 / 해설</summary>

대체로 나쁜 선택입니다. 깊은 파이프라인은 각 단계 논리 깊이를 줄여 클럭 주파수(Iron Law 의 1/Cycle Time)를 높이지만, 분기가 늦은 단계에서 해결되므로 misprediction 시 flush 해야 할 잘못 fetch 된 명령이 늘어 분기 페널티가 커집니다 — 이는 CPI 를 증가시킵니다. CPU Time = IC × CPI × Cycle Time 에서 Cycle Time 감소(이득)와 CPI 증가(손해)가 충돌하는데, 분기가 많고 예측이 어려우면 misprediction 빈도가 높아 CPI 증가가 주파수 이득을 상쇄하거나 압도합니다. 따라서 이런 워크로드에는 깊은 파이프라인보다, 정확한 분기 예측기(M03 의 TAGE 등)나 적당한 깊이가 더 효과적입니다. 워크로드의 분기 특성에 따라 최적 파이프라인 깊이가 존재한다는 것이 Iron Law 의 trade-off 입니다.

</details>
