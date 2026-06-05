---
title: "Quiz — Module 02: 프로세스·스레드·CPU 스케줄링"
---

[← Module 02 본문으로 돌아가기](../../02_process_scheduling/)

---

## Q1. (Remember)

process 의 다섯 가지 상태가 아닌 것은?

- [ ] A. ready
- [ ] B. running
- [ ] C. compiled
- [ ] D. waiting

<details>
<summary>정답 / 해설</summary>

**C**. process 의 다섯 상태는 new, ready, running, waiting, terminated 입니다(§3.1.2). "compiled" 는 program(disk 의 수동적 executable)의 단계이지 실행 중 process 의 상태가 아닙니다 — program 이 메모리에 적재돼 실행되어야 비로소 process 가 됩니다(§3.1).

</details>
## Q2. (Understand)

concurrency 와 parallelism 의 차이를 단일 코어/멀티코어 관점에서 설명하라.

<details>
<summary>정답 / 해설</summary>

(§4.2) **concurrency** 는 여러 작업이 *진행 중*인 상태로, 코어가 하나면 시간상 번갈아(interleaved) 실행됩니다 — 즉 한순간에는 하나만 실제 실행 중이지만 여러 작업이 동시에 진척됩니다. **parallelism** 은 여러 코어에서 *물리적으로 동시에* 실행되는 것입니다. 따라서 단일 코어에서도 concurrency 는 가능하지만, parallelism 은 멀티코어라야 가능합니다.

</details>
## Q3. (Apply)

세 process 가 거의 동시에 도착했고 CPU burst 가 P1=8, P2=4, P3=2 (시간 단위)다. SJF(nonpreemptive)로 스케줄할 때 실행 순서와 평균 waiting time 은?

<details>
<summary>정답 / 해설</summary>

SJF 는 다음 burst 가 가장 짧은 것을 먼저 실행합니다(§5.3.2). 순서는 **P3(2) → P2(4) → P1(8)**.
- P3 대기 0, P2 대기 2, P1 대기 6 → 평균 waiting = (0+2+6)/3 = **8/3 ≈ 2.67**.
- 비교로 FCFS(P1→P2→P3)면 대기 0+8+12=20 → 평균 6.67. SJF 가 평균 대기에서 최적임을 확인할 수 있습니다(다만 burst 예측이 필요).

</details>
## Q4. (Apply)

Round-Robin 스케줄링에서 time quantum 을 매우 크게(모든 burst 보다 크게) 설정하면 어떤 알고리즘과 사실상 같아지는가?

- [ ] A. SJF
- [ ] B. Priority
- [ ] C. FCFS
- [ ] D. 변화 없음

<details>
<summary>정답 / 해설</summary>

**C**. quantum 이 모든 process 의 burst 보다 크면 어떤 process 도 선점되지 않고 도착 순서대로 끝까지 실행되므로, Round-Robin 은 **FCFS** 와 같아집니다(§5.3.3). 반대로 quantum 이 너무 작으면 context switch 오버헤드가 폭증합니다 — quantum 크기가 RR 의 핵심 tuning 변수입니다.

</details>
## Q5. (Analyze)

어떤 kernel 코드가 single-core 에서는 멀쩡하다가 멀티코어로 옮기니 공유 자료가 간헐적으로 깨진다. preemptive 스케줄링과 연결해 원인을 분석하라.

<details>
<summary>정답 / 해설</summary>

현대 OS 는 대부분 **preemptive** 라, 공유 데이터를 다루던 흐름이 임의 시점에 선점될 수 있습니다(§5.1.3). single-core 에서는 공유 변수 수정 중 interrupt 를 막으면 선점이 없어 race 가 안 생기지만(§6.2), 멀티코어에서는 *다른 코어*가 동시에 같은 자료를 만질 수 있어 interrupt 차단만으로는 부족합니다. 따라서 race condition 이 발생하며, M05 의 atomic 명령/lock 으로 critical section 을 보호해야 합니다. 간헐적이고 재현이 어려운 이유는 깨짐이 *특정 interleaving* 에서만 나타나기 때문입니다.

</details>
## Q6. (Evaluate)

하드웨어가 register set 을 여러 벌 제공하면 context switch 가 빨라진다고 한다. 이 가속의 효과와 한계를 평가하라.

<details>
<summary>정답 / 해설</summary>

- **효과**: context switch 의 핵심 비용은 현재 process 의 register 를 PCB 에 save 하고 다음 것을 restore 하는 일입니다(§3.2.3). register set 이 여러 벌이면 메모리로 복사하는 대신 *bank 전환*만으로 상태를 바꿀 수 있어 switch 가 크게 빨라집니다.
- **한계**: register set 수가 유한하므로, 동시에 빠르게 전환할 수 있는 흐름 수가 제한됩니다. 그 수를 넘는 process 사이 전환은 여전히 메모리 save/restore 가 필요합니다.
- DV 평가: 이 register bank 전환 로직이 빠짐없이 모든 상태를 보존하는지가 검증 포인트 — 누락 시 복귀 후 데이터 오염이 발생합니다.

</details>
