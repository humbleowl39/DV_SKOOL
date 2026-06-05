---
title: "Module 02 — 프로세스 · 스레드 · CPU 스케줄링"
---

:::tip[학습 목표]
이 모듈을 마치면:

- **Explain** program(수동적)과 process(능동적)의 차이, 그리고 process 의 다섯 상태와 PCB 의 역할을 설명할 수 있다.
- **Trace** 한 코어를 한 process 에서 다른 process 로 넘기는 context switch 의 state save/restore 경로를 추적할 수 있다.
- **Differentiate** concurrency 와 parallelism, preemptive 와 nonpreemptive 스케줄링을 구분할 수 있다.
- **Apply** FCFS / SJF / Round-Robin / Priority 스케줄링을 주어진 burst 패턴에 적용해 비교할 수 있다.
- **Explain** preemptive 스케줄링이 왜 race condition 의 씨앗이 되어 M05 의 동기화를 요구하는지 설명할 수 있다.
:::
:::note[사전 지식]
- [Module 01 — OS 개요](../01_os_overview/) — dual-mode, dispatcher 의 user-mode 전환
- interrupt 의 막연한 개념 (M04 에서 정식 정의)
- (출처) Silberschatz, *Operating System Concepts* 10th ed., Ch.3–5
:::
---

## 1. Why care? — 우리가 검증하는 interrupt 는 context switch 를 일으킨다

DV 엔지니어가 interrupt 컨트롤러나 DMA 완료 interrupt 를 검증할 때, 그 interrupt 가 시스템 수준에서 실제로 일으키는 일은 **context switch** 입니다. CPU 가 현재 process 의 상태를 PCB 에 저장하고 다른 process 로 넘어가는 것이죠. 또 현대 OS 가 대부분 **preemptive** 라는 사실은, 공유 데이터를 다루던 흐름이 임의 시점에 끊길 수 있다는 뜻이고, 이것이 곧 M05 에서 다룰 race condition 의 근본 원인입니다.

즉 "interrupt 가 온다"는 우리 testbench 의 한 줄 자극이, OS 관점에서는 실행 흐름 전체를 갈아끼우는 무거운 사건입니다. process/thread/스케줄링을 이해하면, 우리가 자극하는 신호가 시스템에 어떤 파급을 주는지, 그리고 왜 동기화가 필요한지가 보입니다.

---

## 2. Intuition — 한 줄 비유와 한 장 그림

:::tip[💡 한 줄 비유]
**Context switch** ≈ **한 책상을 여러 사람이 번갈아 쓰는 일**.<br>
한 사람(process)이 자리를 비울 때 자기 서류·펜 위치(register·program counter)를 사진 찍어 서랍(PCB)에 넣고, 다음 사람이 자기 사진(PCB)을 꺼내 책상을 그대로 복원합니다. 사진 찍고 꺼내는 시간은 *아무 일도 안 하는 순수 오버헤드*입니다.
:::
### 한 장 그림 — process 상태와 그 사이의 전이

```d2
direction: right

NEW: "new\n(생성 중)"
READY: "ready\n(코어 대기)"
RUN: "running\n(명령 실행)"
WAIT: "waiting\n(I/O 등 대기)"
TERM: "terminated\n(종료)"

NEW -> READY: "admit"
READY -> RUN: "dispatch (scheduler 선택)"
RUN -> READY: "interrupt (preempt)"
RUN -> WAIT: "I/O 요청"
WAIT -> READY: "I/O 완료 (interrupt)"
RUN -> TERM: "exit"
```

### 왜 이 디자인인가 — Design rationale

여러 process 를 메모리에 두고 CPU 활용도를 높이려는 것이 **multiprogramming** 이고, 자주 코어를 바꿔 사용자가 상호작용하게 하는 것이 **time sharing** 입니다(Ch.3.2). 한 코어에서는 한순간 하나만 running 일 수 있으므로, OS 는 ready queue 에서 다음 주자를 골라 코어를 넘겨야 합니다. 이 "넘기는 일"을 안전하게 하려면 각 process 의 실행 상태를 어딘가 보관해야 하고, 그 보관소가 **PCB(process control block)** 입니다.

---

## 3. 작은 예 — I/O 를 기다리는 process 가 코어를 양보하는 과정

process P1 이 실행 중 I/O 를 요청하면, 그 사이 코어를 P2 에게 넘기는 것이 활용도 측면에서 이득입니다(Ch.5.1.1, CPU burst 와 I/O burst 의 교대).

### 단계별 다이어그램

```d2
direction: down

A: "① P1 running 중\nI/O 요청 (read)"
B: "② P1: running → waiting\nstate save → PCB(P1)"
C: "③ scheduler: ready queue 에서 P2 선택\ndispatcher 가 코어 넘김"
D: "④ state restore ← PCB(P2)\nuser mode 전환 + 점프"
E: "⑤ I/O 완료 interrupt\nP1: waiting → ready"

A -> B -> C -> D
D -> E: "(나중에)"
```

### 단계별 의미

| Step | 무엇이 | 무엇을 | 왜 |
|---|---|---|---|
| ① | P1 | I/O 요청 → 더 진행 불가 | CPU burst 끝, I/O burst 시작 (Ch.5.1.1) |
| ② | OS | P1 상태를 PCB(P1)에 save | context switch 의 전반 (Ch.3.2.3) |
| ③ | CPU scheduler | ready queue 에서 P2 선택 | 코어를 놀리지 않으려고 (Ch.3.2.1) |
| ④ | dispatcher | PCB(P2) restore + user mode 전환 + 점프 | dispatch latency (Ch.5.1.4) |
| ⑤ | 하드웨어 | I/O 완료 interrupt → P1 ready 로 | waiting→ready 전이 (Ch.3.1.2) |

:::note[여기서 잡아야 할 두 가지]
**(1) context switch 는 순수 오버헤드다.** state save/restore 동안 시스템은 유용한 일을 못 합니다(보통 수 microsecond; 하드웨어가 register set 을 여러 벌 제공하면 더 빠름, Ch.3.2.3). DV 관점에서 register set 다중화는 우리가 검증할 수 있는 하드웨어 가속의 한 예입니다.<br>
**(2) ④ 의 user mode 전환이 M01 의 dual-mode 와 맞물린다.** dispatcher 가 코어를 넘기며 mode bit 을 user 로 바꾸는 바로 그 지점입니다.
:::
---

## 4. 일반화 — 상태·PCB·thread·스케줄링 기준

### 4.1 Process 의 다섯 상태와 PCB (Ch.3.1.2–3.1.3)

process 는 실행되며 상태가 바뀝니다: **new**(생성 중), **ready**(코어 배정 대기), **running**(명령 실행 중), **waiting**(사건 대기), **terminated**(종료). 한 코어에서는 한순간 하나만 running 이고 나머지는 ready/waiting 에 머뭅니다.

OS 는 각 process 를 **PCB** 로 표현합니다. PCB 에 담기는 것: process state, program counter, CPU register, scheduling 정보, memory-management 정보(base/limit·page table), accounting, I/O 상태. 이 중 base/limit·page table 이 M03 의 주소공간과 직결됩니다.

process 는 자기 시간을 어디에 쓰느냐에 따라 I/O 를 주로 하는 **I/O-bound** 와 계산을 주로 하는 **CPU-bound** 로 나뉩니다(Ch.3.2).

### 4.2 Thread 와 concurrency vs parallelism (Ch.4.1–4.2)

한 process 가 여러 **thread** 를 가지면 동시에 여러 일을 할 수 있습니다. thread 의 이점은 네 가지(Ch.4.1.2): **responsiveness**(일부가 막혀도 반응), **resource sharing**(한 주소공간 공유), **economy**(process 보다 생성·switch 가 쌈), **scalability**(멀티코어 병렬).

여기서 두 개념을 구분해야 합니다(Ch.4.2):

```d2
direction: down

C: "**concurrency**\n여러 작업이 '진행 중'\n단일 코어면 interleaved\n(번갈아 실행)"
P: "**parallelism**\n여러 코어에서 '동시에'\n멀티코어라야 가능"
```

즉 단일 코어에서도 concurrency 는 가능하지만 parallelism 은 멀티코어라야 가능합니다.

### 4.3 스케줄링: 언제 결정하나 (Ch.5.1.3)

| 종류 | 언제 결정 | 특징 |
|------|----------|------|
| **Nonpreemptive (cooperative)** | running→waiting 또는 종료 때만 | 한 번 코어를 쥐면 스스로 놓을 때까지 유지 |
| **Preemptive** | 그 외(예: interrupt 로 running→ready)에도 끼어듦 | 현대 OS 대부분 (Windows·macOS·Linux·UNIX) |

핵심 연결: **preemptive 는 공유 데이터를 다루다 선점되면 race condition 을 부른다**(Ch.5.1.3). 그래서 M05 의 동기화 도구가 필요해집니다.

---

## 5. 디테일 — 스케줄링 기준과 대표 알고리즘 (Ch.5.2–5.3)

### 5.1 비교 기준 (Ch.5.2)

| 기준 | 의미 | 방향 |
|------|------|------|
| CPU utilization | CPU 가 일하는 비율 | 높을수록 좋음 |
| Throughput | 단위시간당 완료 process 수 | 높을수록 좋음 |
| Turnaround time | 제출~완료 | 낮을수록 좋음 |
| Waiting time | ready queue 대기 합 | 낮을수록 좋음 |
| Response time | 첫 응답까지 | 낮을수록 좋음 |

### 5.2 대표 알고리즘 (Ch.5.3)

| 알고리즘 | 규칙 | 장점 | 단점 |
|----------|------|------|------|
| **FCFS** (§5.3.1) | 도착 순 | 단순 | 평균 대기 김 (convoy effect) |
| **SJF** (§5.3.2) | 다음 burst 가장 짧은 것 먼저 | 평균 대기 최적 | burst 예측 필요 |
| **Round-Robin** (§5.3.3) | time quantum 으로 돌려쓰기 (preemptive) | time-sharing 에 적합 | quantum 크기 민감 |
| **Priority** (§5.3.4) | 우선순위 순 | 중요 작업 우선 | 낮은 우선순위 starvation 가능 |

### 5.3 dispatcher 와 dispatch latency (Ch.5.1.4)

**CPU scheduler** 가 ready queue 에서 process 를 고르면, **dispatcher** 가 실제로 코어를 넘깁니다 — context switch + user mode 전환 + 프로그램 위치로 점프이며, 그 시간이 **dispatch latency** 입니다. DV 관점에서, register set 을 여러 벌 둔 하드웨어는 이 latency 를 줄이는 가속이며, 우리가 그 register bank 전환을 검증할 수 있습니다.

---

## 6. 흔한 오해 와 DV 디버그 체크리스트

### 흔한 오해

:::danger[❓ 오해 1 — 'concurrency 가 있으면 parallelism 도 있는 것이다']
**실제**: concurrency 는 작업들이 *진행 중*이라는 뜻일 뿐, 단일 코어에서는 시간상 번갈아(interleaved) 실행됩니다. 진짜 동시 실행(parallelism)은 멀티코어라야 가능합니다(Ch.4.2).<br>
**왜 헷갈리는가**: 사용자 눈에는 둘 다 "여러 일이 동시에 되는 것"처럼 보여서.
:::
:::danger[❓ 오해 2 — 'context switch 는 빠르니 비용을 무시해도 된다']
**실제**: context switch 동안 시스템은 *유용한 일을 못 하므로 순수 오버헤드*입니다(Ch.3.2.3). 너무 잦은 switch(작은 time quantum, 과도한 interrupt)는 throughput 을 깎습니다.<br>
**왜 헷갈리는가**: 한 번이 수 microsecond라 작아 보여서 — 빈도가 곱해지면 무시 못 함.
:::
:::danger[❓ 오해 3 — 'preemptive 스케줄링은 그냥 더 좋은 방식이다']
**실제**: preemptive 는 반응성을 얻지만, 공유 데이터를 다루다 임의 시점에 선점되면 **race condition** 을 만듭니다(Ch.5.1.3). 그래서 kernel 자료구조에 동기화(M05)가 필수가 됩니다 — 이득에는 대가가 따릅니다.<br>
**왜 헷갈리는가**: "더 잘 끼어든다 = 더 좋다"로 단순화해서.
:::
### DV 디버그 체크리스트

| 증상 | 1차 의심 | 어디 보나 |
|---|---|---|
| interrupt 후 복귀 시 register 값이 깨짐 | state save/restore(PCB) 불완전 | context switch 시 저장 대상 register 목록 |
| 우선순위 낮은 흐름이 영영 진행 안 됨 | priority scheduling 의 starvation | aging 메커니즘 유무 |
| 공유 자료 손상이 간헐적으로 발생 | preemptive 선점 중 race | M05 동기화, critical section 보호 |
| 다중 register bank 전환 시 오동작 | register set 다중화 로직 | bank select 신호, switch 시 저장/복원 경로 |

---

## 7. 핵심 정리 (Key Takeaways)

- **program 은 수동적, process 는 능동적.** disk 의 executable 이 메모리에 올라 PC·자원을 갖고 실행되면 process. 다섯 상태(new/ready/running/waiting/terminated)를 오간다.
- **PCB 가 process 의 모든 실행 상태를 담는다** — state·PC·register·scheduling·memory(base/limit·page table)·I/O. context switch 는 PCB 로 state save/restore.
- **context switch 는 순수 오버헤드** — interrupt 가 계기이며, register set 다중화로 가속할 수 있다.
- **concurrency ≠ parallelism** — 전자는 진행 중(단일 코어 interleaved 가능), 후자는 동시 실행(멀티코어 필요).
- **preemptive 스케줄링이 race 의 씨앗** — 그래서 M05 의 동기화 도구가 필요하다. 대표 알고리즘: FCFS/SJF/RR/Priority.

:::caution[실무 주의점]
- DMA 완료 interrupt 같은 우리 자극이 시스템 수준에서 context switch 를 유발한다는 점을 testbench 시나리오에 반영하세요.
- preemptive 환경에서 공유 레지스터/메모리를 다루는 시퀀스는 선점 가능성을 가정하고 동기화를 검증해야 합니다.
:::
### 7.1 자가 점검

:::tip[🤔 Q1 — context switch 경로 (Bloom: Analyze)]
P1 이 실행 중 interrupt 가 들어와 P2 로 전환된다. 이때 OS 가 PCB(P1)에 저장해야 하는 핵심 항목과, 하나라도 빠지면 생기는 문제는?
<details>
<summary>정답</summary>

저장 항목(Ch.3.1.3): process state, **program counter**, **CPU register**, scheduling 정보, memory-management 정보(base/limit·page table), I/O 상태.
- 빠지면: PC 가 빠지면 P1 이 다시 running 될 때 *어디서부터 실행할지* 모름 → 잘못된 명령 실행. register 가 빠지면 연산 중간값 손실 → 데이터 오염.
- DV 포인트: context switch 하드웨어 가속(register bank)이 저장/복원 대상을 빠짐없이 다루는지가 검증 포인트.

</details>
:::
:::tip[🤔 Q2 — preemptive 와 race (Bloom: Evaluate)]
어떤 kernel 이 single-core 에서는 잘 돌다가 multi-core 로 옮기니 공유 자료가 간헐적으로 깨진다. 왜이며, single-core 의 단순 해법이 왜 multi-core 엔 안 통하나?
<details>
<summary>정답</summary>

- single-core 에서는 공유 변수 수정 중 **interrupt 를 막으면** 선점이 없어 race 가 안 생긴다(Ch.6.2).
- multi-core 에서는 *다른 코어*가 동시에 같은 자료를 만질 수 있어, interrupt 차단만으론 부족하다 — 모든 core 에 메시지를 돌려야 해 비싸고 비현실적(Ch.6.2).
- 그래서 preemptive kernel 은 atomic 명령/lock(M05)으로 세심히 보호해야 한다.
- 평가: 이것이 preemptive·멀티코어의 *대가* — 반응성·확장성을 얻는 대신 동기화 부담을 진다.

</details>
:::
### 7.2 출처

**Internal (HDG)**
- `os_processes_concurrency_spec.md` — process/thread, context switch, concurrency vs parallelism, 스케줄링 (Ch.3–5 정독 요약)
- `os_concepts_guide.md` — 시리즈 1번 "무엇이 도는가"

**External**
- Silberschatz et al. *Operating System Concepts*, 10th ed. — **Ch.3 Processes**(§3.1 상태/PCB, §3.2 context switch), **Ch.4 Threads & Concurrency**(§4.1–4.2), **Ch.5 CPU Scheduling**(§5.1 preempt/dispatcher, §5.2 기준, §5.3 알고리즘)

---

## 다음 모듈

→ [Module 03 — 메인 메모리 · Paging · TLB](../03_memory_paging_tlb/): process 가 올라앉는 공간 — 주소가 언제 정해지고, 하드웨어(MMU)가 어떻게 logical→physical 로 번역하며, TLB 가 왜 필요한가.

[퀴즈 풀어보기 →](../quiz/02_process_scheduling_quiz/)
