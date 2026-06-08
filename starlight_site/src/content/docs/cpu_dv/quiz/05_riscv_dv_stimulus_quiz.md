---
title: "Quiz — Module 05: 제약 랜덤 명령 생성"
---

[← Module 05 본문으로 돌아가기](../../05_riscv_dv_stimulus/)

---

## Q1. (Remember)

`riscv-dv` 와 `force-riscv` 의 구현 언어를 올바르게 짝지은 것은?

- [ ] A. riscv-dv = C++, force-riscv = SystemVerilog
- [ ] B. riscv-dv = SystemVerilog, force-riscv = C++
- [ ] C. 둘 다 Python
- [ ] D. 둘 다 SystemVerilog

<details>
<summary>정답 / 해설</summary>

**B**. `riscv-dv`(Chips Alliance)는 UVM 제약 랜덤 기반 SystemVerilog ISG 로, 시뮬레이터의 constraint solver 와 자연스럽게 통합되고 ISA coverage 모델을 동봉합니다. `force-riscv`(Futurewei)는 C++ 엔진으로 명령·메모리·페이지 상태를 프로그램적으로 구성해 virtual memory·페이지 테이블 같은 복잡한 시스템 상태 시퀀스에 유연합니다.

</details>
## Q2. (Understand)

ISG(instruction stream generator)가 자극에서 보장하는 것과 보장하지 _않는_ 것을 구분하면?

<details>
<summary>정답 / 해설</summary>

ISG 가 보장하는 것은 _유효성_ 입니다 — 제약(유효 명령·정렬·레지스터 의존) 안에서 합법적인 명령 스트림을 생성합니다. 보장하지 _않는_ 것은 그 프로그램 실행의 _정답_ 입니다. ISG 는 "옳은 결과"를 모르므로, 정답 판정은 같은 ELF 를 실행하는 ISS(reference model)의 golden trace 가 합니다. 그래서 ISG 와 step-and-compare 는 항상 짝으로 동작합니다. 또한 분포 weight 는 확률 편향일 뿐, 특정 인접 조합의 등장을 _보장_ 하지 않습니다.

</details>
## Q3. (Apply)

coverage 리포트에서 "AMO(atomic) 명령 bin 이 0" 으로 나왔다. 가장 먼저 시도할 생성 측 조치는?

- [ ] A. 시드 수를 100배로 늘린다
- [ ] B. 명령 분포에서 ATOMIC weight 를 한시적으로 크게 올린다
- [ ] C. step-and-compare 를 끈다
- [ ] D. ISS 를 다른 것으로 바꾼다

<details>
<summary>정답 / 해설</summary>

**B**. bin 이 _0_ 이라는 것은 해당 명령이 분포에서 비활성이거나 weight 가 너무 작아 거의 생성되지 않는다는 신호입니다. 분포에서 ATOMIC weight 를 크게 올려 자극을 그쪽으로 편향하는 것이 가장 직접적입니다. A(시드 증가)는 _생성 자유도 자체_ 가 막혀 있으면 효과가 없습니다. C·D 는 생성과 무관(정답 판정/모델)이라 coverage hole 을 못 채웁니다. hole 이 채워지면 weight 를 원래 균형으로 되돌립니다.

</details>
## Q4. (Apply)

load-use hazard 를 directed 로 박지 _않고_ 생성기가 자연히 만들게 하려면 제약을 어떻게 열어야 하는가?

<details>
<summary>정답 / 해설</summary>

세 가지 자유도를 _열어두면_ 됩니다.
1. load 명령 다음에 ALU 명령이 인접할 수 있도록 명령 분포·순서 제약을 풀어둔다(load 와 ALU 둘 다 충분한 weight).
2. 레지스터 의존을 무작위화한다 — 즉 ALU 명령의 source 레지스터가 직전 load 의 destination 과 _같을 수 있도록_ 레지스터 선택을 제약하지 않는다.
3. 시드를 다양화한다 — 위 두 자유도가 열려 있으면 어떤 시드에서 우연히 `lw x5; add x6,x5,x7` 인접 쌍이 생성된다.

핵심은 엔지니어가 _쌍 자체를 쓰는 게 아니라_ 쌍이 _생길 수 있는 자유도_ 만 열고, 곱집합을 시드 다양성에 맡긴다는 점입니다. 그리고 transition/cross coverage 로 그 인접이 실제 발생했는지 측정합니다.

</details>
## Q5. (Analyze)

수천 시드를 돌렸지만 "supervisor 모드 진입" bin 이 여전히 0 이다. 시드를 10배 더 늘리는 것이 효과가 _없을_ 가능성이 높은 이유는?

- [ ] A. 시드가 많으면 시뮬레이터가 느려져서
- [ ] B. privilege 전환 시퀀스를 생성할 자유도(knob)가 애초에 꺼져 있으면 합집합이 커지지 않아서
- [ ] C. coverage 는 시드와 무관해서
- [ ] D. supervisor 모드는 formal 로만 검증 가능해서

<details>
<summary>정답 / 해설</summary>

**B**. bin 이 _0_ 이라는 것은 도달 가능 영역 안인데 운 나쁘게 안 나온 게 아니라, 애초에 privilege 전환 시퀀스가 _생성되지 않고 있을_ 가능성이 큽니다(privilege knob off 또는 weight 0). 생성기가 그 시퀀스를 만들 자유도 자체가 없으면, 시드를 아무리 늘려도 coverage 합집합은 커지지 않습니다. 따라서 시드 증가가 아니라 privilege 시퀀스 knob 을 켜고 재생성해야 하며, 그래도 안 나오면 코어가 supervisor 모드를 지원하는지(설계 제약)부터 확인합니다.

</details>
## Q6. (Evaluate)

coverage 곡선이 95% 에서 평탄해졌고, 남은 5% 중 일부 bin 은 끝내 안 채워진다. "랜덤 시드를 계속 늘린다" vs "directed 시퀀스로 보완한다" 중 어느 전략이 더 타당하며, 판단 기준은?

<details>
<summary>정답 / 해설</summary>

**directed 보완이 더 타당합니다 — 단, 미커버 bin 의 성격을 먼저 분류해야 합니다.**
- coverage 곡선이 평탄해졌다는 것은 _랜덤이 도달 가능한 영역을 거의 다 덮었다_ 는 신호입니다. 추가 시드는 한계 효용이 급감합니다.
- 남은 bin 은 둘 중 하나입니다. (a) 설계상 도달 불가능 → waive 처리. (b) 확률이 극히 낮은 코너 → 시드로는 비효율적이므로 분포 knob 편향, 그래도 안 되면 directed/직접 어셈블리로 명시적으로 박습니다.
- 판단 기준: "이 bin 이 설계상 가능한가?"를 먼저 확인하고(가능하면 (b), 불가능하면 (a)), 가능하지만 확률이 낮으면 랜덤 시드 증가가 아니라 _자극의 방향성_(knob/directed)으로 전환합니다.
- 요지: 평탄한 곡선에서 "더 많은 랜덤"은 비효율 — "더 정밀한 방향"이 답입니다.

</details>
