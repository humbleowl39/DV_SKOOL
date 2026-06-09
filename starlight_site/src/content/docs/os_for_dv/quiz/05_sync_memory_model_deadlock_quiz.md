---
title: "Quiz — Module 05: 동기화·메모리 모델·데드락"
---

[← Module 05 본문으로 돌아가기](../../05_sync_memory_model_deadlock/)

---

## Q1. (Remember)

deadlock 이 발생하기 위한 네 가지 필요조건이 아닌 것은?

- [ ] A. Mutual exclusion
- [ ] B. Hold and wait
- [ ] C. Circular wait
- [ ] D. Bounded waiting

<details>
<summary>정답 / 해설</summary>

**D**. deadlock 네 조건은 mutual exclusion, hold and wait, no preemption, circular wait 이며 *모두* 동시에 성립해야 합니다(§8.3.1). "bounded waiting" 은 critical-section 해법의 세 요건 중 하나(§6.2)이지 deadlock 조건이 아닙니다.

</details>
## Q2. (Understand)

strongly-ordered 와 weakly-ordered 메모리 모델의 차이를 설명하고, memory barrier 가 왜 필요한지 말하라.

<details>
<summary>정답 / 해설</summary>

(§6.4.1) **strongly-ordered** 는 한 processor 의 메모리 수정이 다른 모든 processor 에 *즉시* 보이는 모델이고, **weakly-ordered** 는 즉시 보이지 않을 수 있는 모델입니다. weakly-ordered 에서는 데이터 의존성 없는 load/store 가 재배치(reorder)되어 다른 processor 가 다른 순서로 볼 수 있습니다. **memory barrier** 는 이전의 모든 load/store 가 완료된 뒤에야 이후 것이 수행되게 강제해, 재배치가 있어도 올바른 순서·가시성을 보장합니다.

</details>
## Q3. (Apply)

compare_and_swap(value, expected, new_value)로 spinlock 의 acquire 를 구현하려 한다. 핵심 로직을 pseudo code로 쓰고, 왜 atomic 이어야 하는지 설명하라.

<details>
<summary>정답 / 해설</summary>

```c
void acquire(spinlock_t *l) {
    while (compare_and_swap(&l->locked, 0, 1) != 0) {
        /* spin: 누군가 쥐고 있으면 0 이 아니므로 계속 시도 */
    }
}
```
(§6.4.2, §6.5) CAS 는 `*locked == 0`(풀림)일 때만 1 로 바꾸고 항상 원래 값을 반환합니다. 반환이 0 이면 *내가* 락을 잡은 것이고, 0 이 아니면 누가 쥔 것이라 계속 spin 합니다. **atomic 이어야 하는 이유**: 두 thread 가 동시에 0 을 보고 둘 다 1 로 쓰면 둘 다 락을 잡았다고 착각합니다. CAS 가 atomic 이라 두 core 가 동시에 실행해도 *차례로* 일어나, 한 쪽만 성공합니다. busy-wait 로 도는 이 락이 spinlock 입니다.

</details>
## Q4. (Apply)

`count` 를 atomic variable 로 만들면 producer/consumer 의 `count++`/`count--` race 는 막힌다. 그런데도 bounded-buffer 전체의 race 는 못 막을 수 있다. 왜인가?

<details>
<summary>정답 / 해설</summary>

(§6.4.3) atomic 변수는 *단일 변수의 갱신*만 보장합니다. `count++` 자체는 atomic 해져도, bounded-buffer 로직은 보통 "count 를 검사 → 버퍼에 넣기/빼기 → count 갱신" 처럼 *검사와 행동의 복합*입니다. 검사와 행동 사이에 다른 흐름이 끼어들면(예: 두 producer 가 동시에 "자리 있음"을 보고 같은 슬롯에 씀) race 가 남습니다. 그래서 단일 변수 너머의 일관성에는 mutex/semaphore 같은 더 일반적인 도구가 필요합니다.

</details>
## Q5. (Analyze)

두 thread 가 `first_mutex→second_mutex` 와 `second_mutex→first_mutex` 순으로 lock 을 잡아 멈췄다. resource-allocation graph(RAG)로 이 상황을 분석하고, 왜 테스트로 재현하기 어려운지 말하라.

<details>
<summary>정답 / 해설</summary>

(§8.2, §8.3.2) RAG 에서 thread one 은 first 를 쥐고(assignment edge) second 를 요청(request edge), thread two 는 second 를 쥐고 first 를 요청 → 두 thread·두 resource 가 **cycle** 을 이룹니다. 각 mutex 의 instance 가 하나뿐이므로 cycle 은 deadlock 의 *필요충분*조건 → deadlock 확정.
- **재현 어려움**: 이 deadlock 은 *특정 스케줄링*(두 thread 가 각자 첫 lock 을 잡은 뒤 둘째를 요청하는 정확한 타이밍 교차)에서만 나타납니다. 대부분의 실행에서는 한 thread 가 두 lock 을 다 잡고 끝나 cycle 이 안 생깁니다. 그래서 일반 테스트로는 좀처럼 안 걸립니다 — lock ordering 정적 점검이 필요합니다.

</details>
## Q6. (Evaluate)

deadlock 을 다루는 네 방법(무시/prevention/avoidance/detect+recover) 중, 대부분의 범용 OS(Linux·Windows)가 "무시"를 택하는 결정을 평가하라.

<details>
<summary>정답 / 해설</summary>

(§8.4) **무시(ignore)** 는 비현실적으로 들리지만 대부분의 OS 가 택합니다.
- **근거**: deadlock 이 드물게(예: 한 달에 한 번) 일어난다면, prevention(자원 요청 제약 → 활용도 저하)·avoidance(banker's algorithm → 매 요청마다 safe state 계산 비용)·detection(주기적 검사 비용)의 *상시 비용*이 드문 deadlock 의 피해보다 큽니다. 그래서 처리를 kernel·application 개발자 몫으로 남깁니다.
- **trade-off**: database 처럼 deadlock 이 잦거나 치명적인 시스템은 detect+recover 를 택하고, 안전이 중요한 곳은 prevention 을 씁니다. 자원 class 별로 방법을 조합할 수도 있습니다.
- 평가: "무시"는 게으름이 아니라 *발생 빈도 대비 비용*에 근거한 합리적 공학 결정입니다.

</details>
