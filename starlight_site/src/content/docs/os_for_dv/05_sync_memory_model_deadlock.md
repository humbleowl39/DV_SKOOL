---
title: "Module 05 — 동기화 · 메모리 모델 · 데드락"
---

:::tip[학습 목표]
이 모듈을 마치면:

- **Explain** race condition 이 왜 생기는지(load→연산→store 의 interleaving)와 critical-section 의 세 요건(mutual exclusion/progress/bounded waiting)을 설명할 수 있다.
- **Differentiate** strongly-ordered 와 weakly-ordered 메모리 모델을 구분하고, memory barrier 가 무엇을 강제하는지 설명할 수 있다.
- **Implement** test-and-set / compare-and-swap atomic 명령으로 spinlock 을 구성하는 흐름을 코드로 표현할 수 있다.
- **Trace** reordering 이 Peterson 해법이나 `x`/`flag` 예제를 어떻게 깨뜨리는지 추적할 수 있다.
- **Evaluate** deadlock 네 필요조건 중 무엇을 깨면 prevention 이 되는지, banker's algorithm 이 어떻게 avoidance 를 하는지 판단할 수 있다.
:::
:::note[사전 지식]
- [Module 02](../02_process_scheduling/) — preemptive 스케줄링이 race 의 씨앗
- [Module 04](../04_storage_io_dma/) — interrupt/DMA 가 또 다른 동시성의 원천
- 컴퓨터 구조: out-of-order 실행, cache
- (출처) Silberschatz, *Operating System Concepts* 10th ed., Ch.6–8
:::
---

## 1. Why care? — weakly-ordered 메모리에서 barrier 누락은 silent 버그다

DV 엔지니어가 멀티코어·DMA·동시 행위자가 같은 메모리를 만지는 환경을 검증할 때, 가장 잡기 어려운 버그가 **순서(ordering)** 문제입니다. 성능을 위해 processor 나 compiler 가 데이터 의존성 없는 read/write 를 재배치하는데, single-thread 에서는 무해해도 공유 데이터를 다루는 multi-thread 에서는 치명적입니다. 이것이 weakly-ordered 메모리 모델의 본질이고, 우리가 검증하는 메모리 시스템·coherency·barrier 명령의 핵심입니다.

또 DMA 가 메모리를 고치는 동안 CPU cache 와의 일관성, lock 획득 순서가 엇갈려 생기는 deadlock 은 *특정 스케줄링에서만* 나타나 테스트로 재현하기 까다롭습니다(Ch.8.2). 이 모듈은 그 어려운 버그들의 *근본 메커니즘*을 줍니다 — race 가 왜 생기고, 무엇이 그것을 막으며, 그 도구를 잘못 쓰면 어떻게 deadlock 에 빠지는가.

---

## 2. Intuition — 한 줄 비유와 한 장 그림

:::tip[💡 한 줄 비유]
**Race condition** ≈ **두 사람이 같은 공책의 숫자를 동시에 +1 하기**.<br>
둘 다 "5"를 읽고(load), 각자 6 을 계산해(연산), 6 을 적으면(store), 실제로는 +2 가 아니라 +1 만 됩니다. 한 줄짜리 `count++` 가 기계어로는 *load→연산→store* 세 단계라, 그 사이가 섞이면 결과가 깨집니다.
:::
### 한 장 그림 — race 부터 도구까지의 계층

```d2
direction: down

PROB: "**문제**\nrace condition\n(critical-section problem)"
HW: "**하드웨어 받침**\nmemory barrier (순서)\natomic: test-and-set / CAS"
TOOL: "**그 위의 도구**\nmutex/spinlock → semaphore → monitor"
RISK: "**위험**\ndeadlock / starvation / livelock"

PROB -> HW: "무엇이 막나"
HW -> TOOL: "재료"
TOOL -> RISK: "잘못 쓰면"
```

### 왜 이 디자인인가 — Design rationale

협력하는 흐름이 데이터를 공유하면 동시 접근이 데이터를 깨뜨립니다(race). 막으려면 한 번에 하나의 흐름만 그 데이터를 만지게 **synchronize** 해야 합니다. 그런데 software 만으로 짠 해법(Peterson)은 *순서를 강제할 하드웨어 받침*이 없으면 reordering 에 무너집니다. 그래서 계층이 생깁니다 — 하드웨어가 **barrier**(순서)와 **atomic 명령**(나눌 수 없는 검사·수정)을 주고, 그 위에 OS 가 mutex·semaphore·monitor 를 얹습니다. 이 도구를 잘못 쓰면 deadlock 이라는 새 위험이 생깁니다.

---

## 3. 작은 예 — `count++` / `count--` 가 깨지는 과정

producer 가 `count++`, consumer 가 `count--` 하는 공유 변수를 봅시다(Ch.6.1). 고급 언어로는 한 줄이지만 기계어로는 세 단계입니다.

### 단계별 다이어그램

```d2
direction: down

A: "초기 count = 5"
P: "Producer: r1 = count (5)\nr1 = r1 + 1 (6)"
C: "Consumer: r2 = count (5)\nr2 = r2 - 1 (4)"
S: "interleaving 에 따라\ncount = store(r1)=6 또는 store(r2)=4\n→ 정답 5 가 아님"
A -> P
A -> C
P -> S
C -> S
```

### 단계별 의미

| 단계 | Producer | Consumer | 결과 |
|------|----------|----------|------|
| load | r1 = count (5) | r2 = count (5) | 둘 다 5 를 읽음 |
| 연산 | r1 = 6 | r2 = 4 | — |
| store | count = 6 | count = 4 | 나중 store 가 이김 → 4 또는 6 |

올바른 값은 5(=5+1−1)인데, interleaving 에 따라 4·5·6 중 무엇이든 될 수 있습니다. 이렇게 **여러 흐름이 같은 데이터를 동시에 다루고 결과가 실행 순서에 좌우되는 상황**이 race condition 입니다.

:::note[여기서 잡아야 할 두 가지]
**(1) critical section 으로 형식화한다.** 공유 데이터를 건드리는 코드 구간이 critical section 이고, 올바른 해법은 세 요건을 만족해야 합니다(Ch.6.2): **mutual exclusion**(한 번에 하나), **progress**(들어올 자를 무한히 미루지 않음), **bounded waiting**(무한정 굶지 않음).<br>
**(2) kernel 안에서도 흔하다** — 두 process 가 동시에 `fork()` 하며 같은 `next_available_pid` 를 읽으면 같은 PID 가 둘에게 배정될 수 있습니다(Ch.6.2). 그래서 preemptive kernel 은 세심한 동기화가 필요합니다(M02 연결).
:::
---

## 4. 일반화 — software 한계 · 메모리 모델 · atomic

### 4.1 Software 만으로는 부족하다: Peterson 과 reordering (Ch.6.3)

고전적 software-only 해법 **Peterson's solution** 은 `turn` 과 `flag[2]` 로 mutual exclusion·progress·bounded waiting 을 모두 만족시킵니다 — 알고리즘 자체는 옳습니다. 문제는 현대 하드웨어에서 *그대로는 보장되지 않는다*는 것입니다. processor/compiler 가 데이터 의존성 없는 read/write 를 재배치(reorder)하기 때문입니다.

책의 예: Thread 2 가 `x = 100; flag = true;` 를, Thread 1 이 `while(!flag); print x;` 를 할 때, `x` 와 `flag` 에 의존성이 없어 `flag = true` 가 `x = 100` 보다 먼저 보일 수 있고, 그러면 Thread 1 이 `x` 를 0 으로 출력합니다.

```d2
direction: right
T2: "Thread 2 (의도)\nx = 100\nflag = true"
RE: "reorder 가능\n(의존성 없음)"
BAD: "Thread 1 이 보는 순서\nflag = true 먼저\n→ x 는 아직 0"
T2 -> RE -> BAD
```

### 4.2 메모리 모델과 barrier (Ch.6.4.1)

어떤 아키텍처가 메모리 변경의 가시성을 어떻게 보장하는지를 **memory model** 이라 합니다.

| 모델 | 의미 |
|------|------|
| **Strongly ordered** | 한 processor 의 수정이 다른 모든 processor 에 *즉시* 보임 |
| **Weakly ordered** | 즉시 보이지 않을 수 있음 |

model 은 processor 마다 달라 가시성을 함부로 가정할 수 없습니다. 그래서 변경을 모든 processor 로 전파하도록 강제하는 **memory barrier(memory fence)** 명령을 둡니다. barrier 를 만나면 이전의 모든 load/store 가 *완료*된 뒤에야 이후 load/store 가 수행되므로, §4.1 의 `x`/`flag` 예에서 올바른 순서를 강제할 수 있습니다.

:::note[weakly-ordered 가 _어디서_ 오는가 — store buffer 라는 마이크로아키텍처 근원]
"재배치가 일어난다" 의 가장 흔한 하드웨어 근원은 **store buffer** 입니다. core 가 store 를 실행하면 값을 곧장 메모리(또는 공유 캐시)에 반영하지 않고, _자기 core 안의 store buffer 에 잠시 쌓아 두고_ commit 을 지연합니다(그동안 core 는 멈추지 않고 다음 명령을 진행). 그래서 _다른 core_ 의 시점에서 보면, 이 core 의 store 가 _아직 보이지 않는_ 시간 창이 생기고, 그 사이 옛 값을 읽을 수 있습니다 — 이것이 weakly-ordered 가시성의 물리적 출발점입니다. (x86 처럼 비교적 강한 모델이 `x`/`flag` 류를 _우연히_ 통과시키곤 하는 것도, store→load 정도만 buffer 로 느슨하게 두고 나머지 순서는 더 강하게 보장하기 때문입니다.)

store buffer 의 _물리적 구조와 동작_ 자체는 캐시·메모리 계층의 주제이므로 여기서 다시 유도하지 않습니다 — [Computer Architecture: Memory Hierarchy](../../computer_architecture/04_memory_hierarchy/) 를 참조하세요. 이 모듈에서 중요한 것은 그 결과로 _SW 가 순서를 가정할 수 없게 되고, 그래서 barrier 가 필요해진다_ 는 OS/동기화 관점입니다.
:::

:::tip[💡 DV 연결]
이 strongly/weakly ordered 구분이 곧 메모리 일관성(consistency) 모델입니다. 동기화는 "순서를 어떻게 *강제*하나", 일관성은 "순서가 어떻게 *보장*되나" — 같은 동전의 양면입니다.
:::
### 4.3 Atomic 명령 (Ch.6.4.2–6.4.3)

많은 시스템이 한 word 를 *나눌 수 없는 한 단위로* 검사·수정·교환하는 하드웨어 명령을 제공합니다.

| 명령 | 동작 | 보장 |
|------|------|------|
| **test_and_set()** | 옛 값을 돌려주며 동시에 `true` 로 set | atomic — 두 core 동시 실행도 차례로 |
| **compare_and_swap() (CAS)** | `*value == expected` 일 때만 `new_value` 로, 항상 원래 값 반환 | atomic |

x86 에서는 `cmpxchg` 에 `lock` prefix 를 붙여 bus 를 잠가 atomic 을 보장합니다. CAS 는 보통 더 높은 도구의 *재료*로 쓰이며, **atomic variable**(예: atomic increment)이 그 위에 얹힙니다. 다만 atomic 변수는 *단일 변수 갱신*만 보장하므로, §3 의 `count` 를 atomic 으로 만들어도 그것을 검사하는 while loop 의 race 는 못 막습니다 — 더 일반적 상황엔 다음 절의 lock 이 필요합니다.

#### CAS 가 _왜_ lock-free 알고리즘의 재료가 되는가 — optimistic 갱신

CAS 가 "재료" 라는 말의 실체는 그것이 **낙관적(optimistic) 갱신** 을 atomic 으로 보장한다는 데 있습니다. CAS 의 의미는 정확히 _"내가 _직전에 읽은_ 값(expected)이 여전히 그대로면, 그때만 새 값(new)으로 바꿔라. 아니면 바꾸지 말고 실패를 알려라"_ 입니다 — 이 "읽은 값이 안 바뀌었는지 확인 + 바꾸기" 가 _쪼개지지 않는 한 동작_ 이라는 게 핵심입니다.

이 한 줄짜리 보장 위에 lock 없이 도는 **retry loop** 를 세울 수 있습니다:

```
do {
    old = *p;                 // 1) 현재 값을 낙관적으로 읽고
    new = f(old);             // 2) 그것을 바탕으로 새 값을 계산 (lock 없이)
} while (!CAS(p, old, new));  // 3) 그 사이 아무도 안 바꿨으면 commit, 바꿨으면 재시도
```

흐름은 이렇습니다 — 일단 lock 을 잡지 않고 값을 읽어 계산해 둔 뒤, _마지막 순간_ CAS 로 "내가 읽은 이후 값이 변하지 않았음" 을 검사하며 교체를 시도합니다. 만약 그 사이 다른 흐름이 값을 바꿨다면 CAS 가 실패하고, 루프는 _새 값으로 다시_ 시도합니다. 충돌이 없으면(흔한 경우) 단 한 번에 성공하므로, **lock 의 acquire/release 도, 블로킹도, deadlock 가능성도 없이** 진행합니다 — 이것이 lock-free 자료구조(lock-free stack/queue, atomic counter 등)의 토대입니다. 즉 CAS 가 "본 값이 그대로면 교체" 라는 _조건부 원자 교체_ 를 주기에, lock 이라는 무거운 도구 없이도 일관성을 지킬 수 있는 것입니다.

---

## 5. 디테일 — 도구 계층과 deadlock

### 5.1 Mutex / spinlock / semaphore / monitor (Ch.6.5–6.7)

가장 단순한 것이 **mutex lock**(mutual exclusion) — critical section 전에 `acquire()`, 후에 `release()`. acquire/release 자체가 atomic 해야 해 CAS 로 구현됩니다.

:::note[lock 의 acquire 가 _왜_ atomic 명령을 필요로 하나 — 닭과 달걀]
lock 은 공유 데이터의 race 를 막는 도구인데, _그 lock 자신_ 도 공유 변수라서 똑같은 race 에 노출된다는 역설이 있습니다. 순진하게 lock 을 이렇게 짠다고 해 봅시다:

```
while (locked == 1)   // (A) test: 잠겨 있나 확인
    ;
locked = 1;           // (B) set: 내가 잠갔다고 표시
```

문제는 (A)와 (B) _사이_ 입니다. 두 흐름이 거의 동시에 (A)에서 `locked==0` 을 보고 둘 다 통과한 뒤, 둘 다 (B)에서 `locked=1` 을 써 버리면 — **둘 다 자기가 lock 을 획득했다고 믿습니다**. 이것은 §3 의 race condition 과 _완전히 같은_ 구조입니다(test 와 set 사이의 선점/interleaving). 즉 lock 을 만들려고 했는데 그 lock 구현 자체가 lock 을 필요로 하는 _닭과 달걀_ 상황입니다.

이 순환을 끊는 유일한 방법은 **test 와 set 을 _하나의 나눌 수 없는 명령_ 으로 합치는** 것입니다 — 그것이 바로 `test_and_set`(옛 값을 돌려주며 동시에 set)이나 CAS 입니다. 하드웨어가 "확인하고 잠그기" 를 한 동작으로 보장하면, 두 흐름이 동시에 시도해도 _하드웨어 차원에서 차례가 매겨져_ 한쪽만 성공합니다. 그래서 모든 lock 의 바닥에는 반드시 atomic primitive 가 있어야 하고, 이것이 §4.3 의 atomic 명령이 "동기화 도구의 재료" 인 근본 이유입니다.
:::

```c
// CAS 로 구현한 spinlock (개념)
typedef struct { volatile int locked; } spinlock_t;

void acquire(spinlock_t *l) {
    // available 이 풀릴 때까지 도는 busy wait = spinlock
    while (compare_and_swap(&l->locked, /*expected*/0, /*new*/1) != 0) {
        /* spin */
    }
}
void release(spinlock_t *l) { l->locked = 0; }
```

`available` 이 풀릴 때까지 도는 **busy wait** 락이 **spinlock** 입니다. spinlock 은 CPU 사이클을 태우지만 *context switch 가 없어*, 락을 아주 짧게(대략 context switch 2번보다 짧게) 쥘 때는 multicore 에서 오히려 유리합니다(Ch.6.5).

| 도구 | 방식 | 특징 |
|------|------|------|
| **mutex/spinlock** | busy wait | CPU 태움, 짧은 구간 유리, contention 시 성능 저하 |
| **semaphore** | 재웠다 깨움 (wait=P/signal=V) | busy wait 회피, Dijkstra |
| **monitor** | 언어 차원, 데이터+연산 묶음 + condition variable | 더 높은 추상 |

여기서 **condition variable**(조건 변수)은 monitor 안에서 "어떤 조건이 참이 될 때까지 기다렸다가, 다른 흐름이 깨워 주면 진행" 하게 해 주는 대기·통지 도구입니다(예: 버퍼가 비면 producer 를 깨움).

### 5.2 Deadlock: 네 필요조건 (Ch.8.3.1)

동기화 도구를 잘못 쓰면 **liveness**(살아 있음 — 시스템이 결국에는 진행을 이뤄낸다는 보장)가 깨집니다 — 대표가 **deadlock**(교착 상태 — 서로 상대가 쥔 자원을 기다리며 아무도 못 나아감). 책은 mutex/semaphore 가 *가장 흔한 deadlock 원천*이라 짚습니다(Ch.8.1). 전형적 예: thread one 이 `first→second` 순, thread two 가 `second→first` 순으로 lock 을 잡으려 하면 각자 하나씩 쥔 채 멈춥니다(Ch.8.2).

deadlock 은 다음 **네 조건이 동시에 성립할 때** 생깁니다:

1. **Mutual exclusion** — 적어도 하나의 자원이 비공유 모드.
2. **Hold and wait** — 자원을 쥔 *채로* 다른 자원을 기다림.
3. **No preemption** — 강제로 뺏을 수 없고 자발적으로 놓아야만 풀림.
4. **Circular wait** — 대기 thread 들이 원형으로 엮임.

**resource-allocation graph(RAG)** 로 판정: cycle 이 없으면 deadlock 없음. instance 가 type 당 하나뿐이면 cycle 은 deadlock 의 *필요충분*조건, 여럿이면 *필요하지만 충분하지 않음*(Ch.8.3.2).

비슷하지만 다른 실패가 **livelock** — 블록되진 않지만 실패 동작을 계속 재시도하며 못 나아감(보통 재시도를 무작위로 흩어 품; Ethernet backoff 와 같은 발상, Ch.8.2.1).

### 5.3 Deadlock 다루는 네 방법 (Ch.8.4–8.8)

| 방법 | 내용 | 누가 |
|------|------|------|
| **무시 (ignore)** | 없는 척; 드물면(월 1회) 다른 비용이 아까움 | 대부분의 OS(Linux·Windows) |
| **prevention** | 네 조건 중 *적어도 하나*가 성립 못 하게 자원 요청 제약 | (예: read-only 공유 자원은 mutual exclusion 없어 deadlock 불가) |
| **avoidance** | 사전 정보로 매 요청마다 **safe state** 판단 | banker's algorithm |

여기서 **safe state**(안전 상태)는 어떤 순서로든 모든 thread 가 필요한 자원을 끝까지 받아 완료할 수 있는 자원 배분 상태이고, **banker's algorithm**(은행원 알고리즘)은 매 자원 요청을 허용하면 여전히 safe state 로 남는지 미리 따져 보고, 아니면 그 요청을 보류해 deadlock 을 피하는 기법입니다.
| **detect + recover** | 허용하되 탐지 후 복구 | database 등 |

세 방법은 자원 class 별로 골라 **조합**할 수도 있습니다.

---

## 6. 흔한 오해 와 DV 디버그 체크리스트

### 흔한 오해

:::danger[❓ 오해 1 — '코드 순서대로 메모리에 반영되니 barrier 는 불필요하다']
**실제**: weakly-ordered 메모리에서는 의존성 없는 load/store 가 재배치되어, 다른 processor 가 *다른 순서*로 볼 수 있습니다(Ch.6.4.1). barrier 가 없으면 §4.1 의 `x`/`flag` 처럼 silent 오류가 납니다.<br>
**왜 헷갈리는가**: single-thread 에서는 항상 결과가 같아 보여서 — multi-thread·멀티코어에서만 드러남.
:::
:::danger[❓ 오해 2 — 'atomic 변수 하나면 모든 race 가 해결된다']
**실제**: atomic 변수는 *단일 변수 갱신*만 보장합니다(Ch.6.4.3). `count` 를 atomic 으로 만들어도 그것을 검사하는 while loop(검사+행동의 복합)의 race 는 못 막아 — 더 일반적 상황엔 lock/semaphore 가 필요합니다.<br>
**왜 헷갈리는가**: "atomic = 안전"으로 과일반화해서.
:::
:::danger[❓ 오해 3 — 'deadlock 은 자주 나니 OS 가 항상 막아준다']
**실제**: deadlock 이 드물면(월 1회 등) prevention/avoidance 비용이 아까워, *대부분의 OS(Linux·Windows)는 그냥 무시*하고 개발자에게 맡깁니다(Ch.8.4). 막아주리라 믿으면 안 됩니다.<br>
**왜 헷갈리는가**: "OS 가 자원 관리자니 deadlock 도 관리"라는 기대 때문.
:::
:::danger[❓ 오해 4 — 'spinlock 은 CPU 를 태우니 항상 나쁘다']
**실제**: 락을 아주 짧게(대략 context switch 2번보다 짧게) 쥘 때는, context switch 가 없는 spinlock 이 multicore 에서 오히려 유리합니다(Ch.6.5).<br>
**왜 헷갈리는가**: "busy-wait = 낭비"라는 인상 — 구간이 짧으면 재우고 깨우는 비용이 더 큼.
:::
### DV 디버그 체크리스트

| 증상 | 1차 의심 | 어디 보나 |
|---|---|---|
| 멀티코어에서만 간헐적 데이터 깨짐 | weakly-ordered reordering, barrier 누락 | barrier/fence 명령 위치, 의존성 없는 store 순서 |
| 두 흐름이 영영 멈춤(재현 어려움) | lock 획득 순서 엇갈림 → deadlock | lock ordering, RAG cycle, hold-and-wait |
| 멈추진 않는데 진행도 안 됨 | livelock(재시도 반복) | trylock 후 재시도 로직, backoff 유무 |
| atomic 카운터인데도 race | 단일 변수 너머 복합 검사+행동 | critical section 경계, lock 필요 여부 |
| DMA 후 CPU 가 옛 값을 봄 | I/O coherency, ordering | DMA write 와 CPU read 사이 barrier/snoop (M04 연결) |
| spinlock 인데 성능 급락 | 높은 contention | 락 보유 시간, 자원 분할 |

---

## 7. 핵심 정리 (Key Takeaways)

- **race 의 근원은 load→연산→store 의 interleaving.** critical-section 해법은 mutual exclusion·progress·bounded waiting 세 요건을 만족해야 한다.
- **software 만으론 부족** — Peterson 도 reordering 에 무너진다. 하드웨어 받침이 필요: **memory barrier**(순서 강제)와 **atomic 명령**(test-and-set/CAS).
- **memory model 은 strongly vs weakly ordered.** weakly-ordered 에서 barrier 누락은 silent 버그. 동기화와 일관성은 같은 동전의 양면.
- **도구 계층**: atomic(재료) → mutex/spinlock → semaphore → monitor. spinlock 은 짧은 구간 multicore 에 유리.
- **deadlock 네 조건**(mutual exclusion·hold-and-wait·no preemption·circular wait)이 *모두* 성립해야 발생. 다루는 법: 무시(대부분 OS)/prevention/avoidance(banker's)/detect+recover.

:::caution[실무 주의점]
- 멀티코어·DMA 동시성 검증에서 weakly-ordered 가정 하에 barrier 가 올바른 위치에 있는지 확인하세요 — 가장 재현 어려운 버그입니다.
- deadlock 은 *특정 스케줄링에서만* 나타나니, lock ordering 을 정적으로 점검하고 RAG cycle 을 시나리오로 만들어 보세요.
:::
### 7.1 자가 점검

:::tip[🤔 Q1 — reordering 추적 (Bloom: Trace)]
weakly-ordered CPU 에서 Thread 2 가 `data = 42; ready = 1;` 을, Thread 1 이 `while(!ready); use(data);` 를 한다. barrier 없이 무엇이 잘못될 수 있고, 어디에 barrier 를 넣어야 하나?
<details>
<summary>정답</summary>

- `data` 와 `ready` 에 의존성이 없어, Thread 2 의 store 두 개가 **재배치**되어 다른 core 에 `ready=1` 이 `data=42` 보다 먼저 보일 수 있다(Ch.6.4.1).
- 그러면 Thread 1 이 `ready` 를 보고 루프를 나와 `use(data)` 하는데, `data` 는 아직 옛 값(예: 0) → silent 오류.
- 해법: Thread 2 에서 `data = 42;` **다음, `ready = 1;` 이전에 memory barrier** 를 넣어 data store 가 먼저 완료되게 강제. (대칭으로 Thread 1 의 load 사이에도 acquire barrier.)

</details>
:::
:::tip[🤔 Q2 — deadlock prevention (Bloom: Evaluate)]
두 thread 가 `first→second` vs `second→first` 순으로 두 mutex 를 잡아 deadlock 이 난다. 네 조건 중 어느 것을 깨는 prevention 이 가장 실용적이며, 왜인가?
<details>
<summary>정답</summary>

- 네 조건: mutual exclusion / hold-and-wait / no preemption / circular wait(Ch.8.3.1).
- 가장 실용적: **circular wait 를 깬다** — 모든 lock 에 *전역 순서*를 매겨 항상 낮은 번호부터 잡게 강제하면, 두 thread 모두 `first→second` 순이 되어 원형 대기가 불가능.
- 왜: mutual exclusion 은 자원 본성상 깨기 어렵고(공유 불가 자원 존재), no preemption 은 강제 회수가 비싸며, hold-and-wait 를 깨려면 모든 자원을 한 번에 잡아야 해 활용도가 떨어진다. lock ordering 은 구현이 단순하고 부작용이 적다.
- (Ch.8.5 prevention: 네 조건 중 하나를 성립 못 하게.)

</details>
:::
### 7.2 출처

**External**
- Silberschatz et al. *Operating System Concepts*, 10th ed. — **Ch.6 Synchronization Tools**(§6.1–2 race/critical section, §6.3 Peterson, §6.4 barrier/atomic, §6.5–7 lock/semaphore/monitor), **Ch.8 Deadlocks**(§8.1–2 model, §8.3 조건/RAG, §8.4–8 다루기)

---

## 다음 모듈

→ [Module 06 — 보호 · 보안: Ring · Domain · Access Matrix](../06_protection_security/): M01 의 dual-mode 를 일반화한 protection ring·domain·access matrix, least privilege, 그리고 device 격리(IOMMU) 관점.

[퀴즈 풀어보기 →](../quiz/05_sync_memory_model_deadlock_quiz/)
