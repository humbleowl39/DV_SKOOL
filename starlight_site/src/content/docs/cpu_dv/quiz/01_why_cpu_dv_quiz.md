---
title: "Quiz — Module 01: 왜 CPU DV는 어려운가"
---

[← Module 01 본문으로 돌아가기](../../01_why_cpu_dv/)

---

## Q1. (Remember)

simulation-based processor DV 의 5 단계 중, "reference model 과 RTL 을 retire 시점에 나란히 비교"하는 단계는?

- [ ] A. Sanity / bring-up
- [ ] B. Directed ISA test
- [ ] C. Constrained random
- [ ] D. Step-and-compare

<details>
<summary>정답 / 해설</summary>

**D**. Step-and-compare(lockstep) 단계가 reference model(ISS) 과 RTL 코어를 같은 명령 스트림으로 실행하며 매 retire 마다 architectural state 를 비교하는 단계입니다. A 는 데이터패스·부팅이 사는지 보는 초기 단계, B 는 각 명령이 단독으로 맞는지 보는 directed 단계, C 는 명령 조합·정렬 코너를 노리는 랜덤 자극 단계입니다. step-and-compare 는 그 위에 얹혀 "모든 명령의 architectural 정합"을 자동 채점합니다.

</details>

## Q2. (Understand)

"directed test 가 모두 PASS 했으니 코어 검증이 끝났다"는 주장이 왜 틀린지 한 문장으로 설명하라.

<details>
<summary>정답 / 해설</summary>

directed test 는 사람이 의도한 명령·시나리오만 짚으므로 명령 _단위_ 커버리지만 보장할 뿐, CPU 버그의 다수가 숨어 있는 _명령 조합 × 파이프라인 정렬 × 예외 타이밍_ 의 곱 공간은 거의 건드리지 못하기 때문입니다. 즉 "모든 명령을 테스트함"과 "모든 경우를 테스트함"은 전혀 다른 명제입니다.

</details>

## Q3. (Apply)

다음 두 명령을 검증할 때, "명령 사이의 간격·의존성을 랜덤화"하는 것이 왜 중요한지 한 가지 코너 케이스를 들어 설명하라.
```asm
lw    x5, 0(x10)
add   x6, x5, x7
```

<details>
<summary>정답 / 해설</summary>

이 둘은 **load-use 의존성**을 가집니다. 두 명령 사이 간격(0 사이클 인접 vs nop 삽입)과 앞단 명령이 만드는 파이프라인 정렬(예: 앞 명령의 cache miss stall) 조합에 따라 코어 내부에서 forwarding 경로/타이밍이 달라집니다. 간격·의존성을 랜덤화해야 "load 직후 그 값을 즉시 사용하되, 앞단 stall 으로 정렬이 한 칸 밀린" 같은 드문 forwarding 코너에 확률적으로 도달할 수 있습니다. 간격을 고정한 directed 로는 그 정렬을 거의 만들 수 없습니다.

</details>

## Q4. (Analyze)

OoO 코어 scoreboard 를 "execution unit 이 결과를 낸 시점"에 비교하도록 짰더니 거의 모든 명령에서 mismatch 가 난다. 가장 가능성 높은 원인은?

- [ ] A. ISS 의 명령 의미 구현 버그
- [ ] B. execution 시점에는 폐기될 추측 실행 결과가 섞여 있어 ISS 와 구조적으로 어긋남
- [ ] C. DPI-C 연동 오류
- [ ] D. covergroup sample 누락

<details>
<summary>정답 / 해설</summary>

**B**. OoO 코어는 분기·메모리 추측으로 나중에 폐기될 수도 있는 결과를 execute 단계에서 만듭니다. ISS 는 추측하지 않으므로 execution 시점 값은 ISS 와 구조적으로 어긋나 거의 전부 mismatch 가 됩니다. architectural state 는 retire(commit) 시점에 프로그램 순서로 확정되므로 비교도 retire 시점에 해야 합니다. A·C 라면 특정 명령에 국한된 실패가 나고, D 는 coverage 0 으로 나타날 뿐 비교 mismatch 의 원인이 아닙니다.

</details>

## Q5. (Evaluate)

약한 메모리 모델(예: RISC-V RVWMO)을 가진 코어에서, scoreboard 가 load/store 를 프로그램 순서대로 in-order 비교한다. 이 설계를 평가하고 올바른 접근을 제시하라.

<details>
<summary>정답 / 해설</summary>

**문제: 약한 메모리 모델은 load/store 재정렬을 상당 부분 허용하므로, 정상 재정렬을 false fail 로 잡는다.** in-order 비교는 강한 순서 모델의 직관을 약한 모델에 잘못 적용한 것입니다. 올바른 접근은 ISA 메모리 모델이 _허용하는 순서 집합_ 과 비교하는 것 — 관찰된 순서가 그 집합 안에 있으면 PASS 로 처리해야 합니다. 이는 UVM 의 out-of-order scoreboard(정답이 여럿인 DUT 의 비교 전략)와 같은 사고방식입니다.

</details>
