---
title: "Quiz — Module 07: Microarchitecture"
---

[← Module 07 본문으로 돌아가기](../../07_microarchitecture/)

---

## Q1. (Remember)

OoO 코어에서 명령이 retire(commit)되는 순서는?

- [ ] A. 실행이 끝나는 순서대로 (out-of-order)
- [ ] B. program order 대로 (in-order)
- [ ] C. 우선순위가 높은 순서대로
- [ ] D. 무작위

<details>
<summary>정답 / 해설</summary>

**B**. execute 는 OoO(순서 없이) 하더라도 retire 는 반드시 **in-order** — ROB head 부터 program order 로 commit 합니다. 이것이 precise exception 의 핵심 보장입니다. A 는 execute 단계의 특성을 retire 로 잘못 옮긴 것, C/D 는 틀렸습니다.

</details>
## Q2. (Understand)

decoupled fetch 에서 FTQ(fetch target queue)와 BPU 의 관계를 가장 정확히 설명한 것은?

- [ ] A. BPU 와 I-cache 가 lock-step 으로 함께 멈춘다
- [ ] B. BPU 가 I-cache 보다 앞서 달려 FTQ 에 target 을 쌓아, I-cache miss 를 prefetch 로 은폐한다
- [ ] C. FTQ 는 retire 된 명령을 저장한다
- [ ] D. BPU 는 backend 의 일부다

<details>
<summary>정답 / 해설</summary>

**B**. 모던 코어는 BPU 와 I-cache 를 분리(decouple)해 BPU 가 앞서 달리며 FTQ 에 fetch target 을 쌓습니다. 덕분에 I-cache miss 가 나도 BPU 가 멈추지 않고 miss 를 prefetch 로 은폐할 수 있습니다. FTQ 가 비면 frontend 가 starve 되므로 BPU 정확도가 실제 throughput 을 결정합니다. A 는 분리하지 않은 고전 코어, C/D 는 FTQ/BPU 의 위치를 잘못 설명한 오답입니다.

</details>
## Q3. (Apply)

같은 8-wide rename 코어 A(ROB 288 / PRF 250)와 B(ROB 630 / PRF 354)가 있다. cache miss 가 많은 워크로드에서 어느 쪽이 유리하며 그 이유는?

- [ ] A. A — ROB 가 작아 빠르다
- [ ] B. B — 더 큰 instruction window 로 long-latency miss 동안 더 많은 독립 명령을 찾아 실행(MLP↑)
- [ ] C. 둘이 동일 — issue width 가 같으므로
- [ ] D. A — PRF 가 작아 전력이 낮다

<details>
<summary>정답 / 해설</summary>

**B**. cache miss 가 많으면 miss 해소를 기다리는 동안 그 뒤의 독립 명령을 계속 찾아 실행해야 IPC 가 유지됩니다. 이 "찾을 수 있는 범위" 가 instruction window 이고 ROB+PRF+LDQ 등이 함께 그 크기를 정합니다. B 는 ROB 630/PRF 354 로 window 가 훨씬 커서 long-latency miss 를 더 많이 흡수합니다(MLP↑). C 는 흔한 오해 — issue width 가 같아도 backend window 가 다르면 IPC 가 벌어집니다.

</details>
## Q4. (Apply)

scoreboard 의 기대값을 OoO 코어의 *execute 완료 순서* 로 만들었더니 멀쩡한 DUT 에서 spurious mismatch 가 났다. 올바른 수정은?

- [ ] A. DUT 를 버그로 보고한다
- [ ] B. 기대값을 retire(program) 순서 기준으로 만든다
- [ ] C. issue width 를 줄인다
- [ ] D. 캐시를 비활성화한다

<details>
<summary>정답 / 해설</summary>

**B**. architectural state(레지스터/메모리)는 항상 retire(program) 순서로만 갱신되므로, scoreboard 의 기대값도 execute 순서가 아니라 **retire 순서** 로 만들어야 합니다. execute 순서로 만들면 OoO 로 먼저 끝난 명령의 결과를 먼저 기대해 spurious mismatch 가 납니다. 따라서 DUT 버그(A)가 아니라 TB 측 기대값 모델링 문제이고, C/D 는 무관합니다.

</details>
## Q5. (Analyze)

어떤 코어가 이론상 8-wide 인데 실측 fetch IPC 가 평균 4~6 에 머문다. frontend 측 원인을 분석하라.

<details>
<summary>정답 / 해설</summary>

핵심 원인은 **branch density 와 fetch group 의 taken-branch 절단** 입니다. fetch group 안에 taken branch 가 *하나만* 있어도 그 뒤의 명령은 버려집니다 — 분기 다음 명령들은 fall-through 가 아니라 target 으로 가야 하기 때문입니다. 분기는 평균 5~7 명령마다 하나꼴이라, 8-wide fetch 라도 effective fetch 가 평균 4~6 으로 깎입니다. 여기에 branch mispredict(flush 15~20 cycle)와 I-cache miss 가 더해져 Frontend Bound 가 전체 stall 의 30~50% 를 차지하기도 합니다. 그래서 wide 코어일수록 BPU 정확도(TAGE-SC-L 등)와 branch alignment 에 투자하며, nominal width 와 effective width 를 구분해 분석해야 합니다.

</details>
## Q6. (Evaluate)

가상의 코어 C 가 기존 코어의 ROB 만 288→630 으로 키우고 PRF 는 250 으로 유지했다. 이 변경이 IPC 를 얼마나 끌어올릴지 평가하라.

<details>
<summary>정답 / 해설</summary>

**별 효과가 없을 가능성이 큽니다.** 핵심은 IPC 가 "가장 먼저 차는(binding) 자원" 에 의해 결정된다는 점입니다. 실제로 **PRF 가 ROB 보다 먼저 fill 되는 경우가 흔합니다** — dispatch 시 명령은 ROB entry 뿐 아니라 결과를 담을 물리 레지스터(PRF)도 할당받아야 하는데, PRF 가 250 으로 묶여 있으면 ROB 에 빈 entry 가 630 개 있어도 PRF 가 바닥나는 순간 dispatch 가 멈춥니다. 따라서 ROB 만 두 배로 키운 효과는 PRF 한계에 가로막혀 미미합니다. 교훈은 자원을 균형 있게(ROB/PRF/IQ/LDQ/STQ/MSHR 을 함께) 키워야 한다는 것이며, 성능 분석 시 top-down 으로 "어느 자원이 binding 인가" 를 먼저 봐야 issue width 나 ROB 크기만 보고 오진하지 않습니다.

</details>
