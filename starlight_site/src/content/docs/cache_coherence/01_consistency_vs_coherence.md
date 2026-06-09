---
title: "Module 01 — Consistency vs Coherence (무엇 vs 어떻게)"
---

:::tip[학습 목표]
이 모듈을 마치면:

- **Differentiate** Memory Consistency(프로그래머에게 보이는 순서 계약)와 Cache Coherence(투명한 하드웨어 메커니즘)를 가시성·범위·역할 기준으로 구분할 수 있다.
- **Explain** SWMR(Single-Writer-Multiple-Reader)과 Data-Value invariant가 왜 coherence의 정의 그 자체인지 설명할 수 있다.
- **Trace** uniprocessor의 sequential illusion이 SMP로 넘어오며 어떻게 깨지는지, 그래서 왜 coherence가 필요해졌는지 추적할 수 있다.
- **Explain** HSA(CPU↔GPGPU) 예시에서 consistency가 프로그래머의 가정이고 coherence가 그 가정을 떠받치는 하드웨어 부담임을 설명할 수 있다.
:::
:::note[사전 지식]
- 캐시 기본: cache line, hit/miss, write-back, dirty bit
- 멀티코어의 shared address space 개념
- (선택) [AMBA 코스](../../amba_protocols/) — ACE/CHI가 언급됨
:::
---

## 1. Why care? — 두 코어가 같은 변수를 "다르게" 본다

### 1.1 시나리오 — Core A가 쓴 값을 Core B가 못 본다

두 코어가 하나의 물리 메모리를 공유하고, 각자 L1 캐시를 둡니다. Core A가 변수 `flag`를 1로 쓰는데, 그 쓰기가 A의 로컬 캐시에만 머무릅니다. 이때 Core B가 `flag`를 읽으면 자기 캐시(또는 DRAM)에 남아 있는 옛날 값 0을 읽습니다.

```
Core A:  flag = 1;   // A의 L1 캐시에만 반영 (dirty)
Core B:  while (flag == 0) { }   // B는 영원히 0을 봄 → 무한 루프
```

uniprocessor 시절에는 이런 일이 없었습니다. 캐시도 OoO 실행도 모두 "단일 스레드 입장에서 순차 실행처럼 보이도록" 설계되어, 그 illusion이 깨지지 않았기 때문입니다. 그런데 1980~90년대에 여러 코어가 단일 주소 공간을 공유하는 SMP로 넘어오면서 이 illusion이 산산조각 났습니다. Core A의 갱신이 Core B에게 자동으로 전파되지 않으면 데이터가 조용히 오염됩니다.

이 문제를 하드웨어가 자동으로 막아 주는 메커니즘이 **Cache Coherence**입니다. 그리고 "barrier를 실행하면 그 이후 다른 코어가 내 쓰기를 본다"처럼 프로그래머가 의존하는 *순서 규칙*은 **Memory Consistency**가 정의합니다. 이 둘을 섞으면 "coherence를 켰는데 왜 순서가 안 맞지?" 같은 잘못된 질문을 하게 됩니다.

---

## 2. Intuition — 사서와 사본, 한 장 그림

:::tip[💡 한 줄 비유]
**Consistency** ≈ 도서관의 **대출 규칙**(누가 어떤 순서로 책을 보고 반납하는지 — 이용자에게 *공표된* 계약).<br>
**Coherence** ≈ 여러 분관에 흩어진 **같은 책의 사본을 항상 같은 판본으로 맞춰 두는 사서의 일**(이용자는 사서가 뭘 하는지 *모르고* 그냥 최신 판본을 받음).
:::
### 한 장 그림 — 무엇(What) 위에 어떻게(How)가 받친다

```d2
direction: down

PROG: "**Programmer / ISA**\n로드·스토어 순서에 의존\nmemory barrier 사용" {
  style.fill: "#e8f0fe"
}
CONS: "**Memory Consistency (What)**\n순서 계약 — 가시적(visible)\n모든 주소에 대한 순서 규칙" {
  style.fill: "#fff4e5"
}
COH: "**Cache Coherence (How)**\n사본 동기화 — 투명(transparent)\n단일 주소(line)만 담당\nSWMR + Data-Value invariant" {
  style.fill: "#e6f4ea"
}
HW: "**Caches / Interconnect**\nL1/L2, snoop, directory, LLC"

PROG -> CONS: "관찰 / 의존"
CONS -> COH: "pipeline + protocol 이\n함께 모델을 만족"
COH -> HW: "사본을 무효화/전송"
```

### 왜 이렇게 나뉘는가 — Design rationale

두 개념을 분리하는 이유는 책임의 경계가 다르기 때문입니다. consistency는 **프로그래머에게 공개된 계약**이라 ISA와 barrier로 노출되고, 여러 주소 사이의 *순서*를 다룹니다. coherence는 **순수한 하드웨어 최적화**라 프로그래머에게 완전히 투명하며, *단일 주소(cache line)* 의 사본들만 동기화합니다. 핵심은 둘이 *함께* 일한다는 점입니다 — 프로세서 파이프라인과 coherence 프로토콜이 한 팀이 되어, 프로그래머가 관찰하는 consistency 모델을 만족시킵니다.

흔한 오해 하나를 여기서 못박습니다: **coherence는 shared memory 동작을 정의하지 않습니다.** coherence는 *한* 메모리 위치의 사본만 맞출 뿐입니다.

---

## 3. 작은 예 — 한 store가 만드는 일, 두 관점으로 본다

Core A가 `X = 1`을 쓰는 단순 store 하나를, consistency 관점과 coherence 관점으로 나눠서 봅니다.

### 단계별 다이어그램

```d2
direction: down

A: "**Core A**\nstore X = 1"
COH_STEP: "**Coherence가 하는 일 (How)**\n① A가 X line을 쓰기 위해\n   write permission 획득\n② peer 캐시(B)의 X 사본 무효화\n③ B가 다음에 X를 읽으면\n   최신값(1)을 받음" {
  style.fill: "#e6f4ea"
}
CONS_STEP: "**Consistency가 보장하는 것 (What)**\nA가 X=1 쓴 뒤 barrier 실행 →\n그 이후 B의 로드는 1을 본다는\n*순서 계약* (모델에 따라 강/약)" {
  style.fill: "#fff4e5"
}
A -> COH_STEP: "hardware 자동"
A -> CONS_STEP: "programmer 가정"
```

### 단계별 의미

| 관점 | 무엇을 보장/수행 | 가시성 | 범위 |
|---|---|---|---|
| Consistency (What) | "barrier 이후 B는 X=1을 본다"는 순서 규칙 | 프로그래머에게 **보임** (ISA/barrier) | **모든** 주소 간 순서 |
| Coherence (How) | A의 쓰기가 B의 사본을 무효화 → B는 stale 안 봄 | 프로그래머에게 **투명** | **단일** 주소(line)만 |

### Coherence의 두 invariant — 정의 그 자체

coherence 프로토콜이 "원자적 메모리"의 추상을 제공하려면 두 가지 invariant를 강제합니다 (출처: A Primer on Memory Consistency and Cache Coherence (Sorin/Hill/Wood)).

- **SWMR (Single-Writer, Multiple-Reader):** 임의의 메모리 위치에 대해 임의의 순간, *한 코어만 쓰기/읽기*를 하거나 *여러 코어가 읽기만* 합니다. 쓰는 동안엔 다른 사본이 살아 있을 수 없습니다.
- **Data-Value Invariant:** 새 epoch 시작 시점의 값은 직전 read-write epoch 종료 시점의 값과 일치해야 합니다. 즉 무효화 후 다시 읽으면 *반드시 최신값*을 받습니다.

:::note[여기서 잡아야 할 핵심]
SWMR은 "동시에 쓰는 사본이 둘일 수 없다"를, Data-Value invariant는 "다음에 읽으면 최신값"을 보장합니다. 이 둘이 합쳐져 *마치 캐시가 없는 것처럼* 단일 원자 메모리의 환상을 만듭니다. coherence를 "사본 무효화 메커니즘"이라고만 외우면 *왜* 무효화하는지를 놓칩니다 — 답은 이 두 invariant입니다.
:::
---

## 4. 일반화 — 가시성·범위·역사

### 4.1 What vs How 정리

| 축 | Memory Consistency | Cache Coherence |
|---|---|---|
| 한 단어 | "무엇(What)" | "어떻게(How)" |
| 본질 | 하드웨어↔소프트웨어 **계약(contract)** | 하드웨어 **메커니즘(mechanism)** |
| 가시성 | 프로그래머에게 **visible** (ISA, barrier) | **transparent** (invisible) |
| 범위 | **모든** 메모리 위치의 *순서* | **단일** 위치(line)의 *사본 동기화* |
| 누가 만족시키나 | pipeline + protocol이 **함께** | coherence protocol 단독 |

### 4.2 역사 — 왜 snooping이 발명되었나

세 시대로 정리됩니다.

1. **Uniprocessor 시대:** 순차 실행. OoO와 캐시를 도입했지만 단일 스레드의 sequential illusion을 보존하도록 설계.
2. **SMP의 부상 (late 80s~90s):** 여러 코어가 단일 주소 공간 공유 → illusion 붕괴 → 하드웨어 **snooping 프로토콜(MESI, MOESI)** 발명으로 peer 캐시를 자동 무효화/갱신.
3. **Multi-Core SoC & 이종(HSA) 시대:** CPU·GPGPU·NPU가 한 칩에 → 단순 bus snooping을 넘어 **directory 기반**과 인터커넥트 주도(ARM **ACE**, **CHI**) 구조로 진화.

### 4.3 HSA 예시 — consistency는 가정, coherence는 부담

CPU와 GPGPU가 같은 물리 메모리와 가상 주소 공간(Shared Virtual Memory)을 공유하는 HSA에서 분리가 가장 선명해집니다.

- **프로그래머의 가정 (Consistency):** 과거엔 CPU→GPU 워크로드 핸드오프에 명시적 cache flush + DMA copy가 필요했습니다. HSA에서는 OpenCL/CUDA 코드가 consistency 모델에 의존해 단순히 가정합니다 — *"CPU가 행렬을 메모리에 쓰고 sync barrier를 실행하면, GPGPU는 그 포인터를 즉시 읽어 갱신된 값을 본다."*
- **하드웨어의 부담 (Coherence):** 그 가정이 깨지지 않도록, 인터커넥트(ACE/CHI)가 무거운 일을 합니다. GPGPU가 행렬을 읽으려 하면 인터커넥트가 트랜잭션을 가로채 CPU의 L1/L2를 snoop하고, dirty 사본이 있으면 그걸 추출해 *DRAM을 우회*하여 GPGPU로 직접 전달합니다. 소프트웨어는 이 복잡한 거래를 전혀 보지 못합니다.

---

## 5. 디테일 — 경계가 흐려지는 지점

consistency와 coherence는 개념적으로 분리되지만 구현에서는 한 팀으로 묶입니다. 예를 들어 store buffer는 consistency 모델(쓰기를 지연시켜 순서를 완화)에 영향을 주지만, 그 buffer가 drain되어 캐시에 반영될 때는 coherence 프로토콜이 SWMR을 강제합니다. 약한(weak) consistency 모델일수록 하드웨어는 더 공격적으로 재배치할 수 있고, 프로그래머는 더 많은 barrier로 순서를 *명시적으로* 요구해야 합니다. 강한(예: SC, sequential consistency) 모델일수록 하드웨어가 더 보수적으로 동작합니다.

### 5.1 consistency 모델 스펙트럼 — SC, TSO, weak

"강/약" 은 추상적 표현이고, 실제로는 하드웨어가 *어떤 재배치를 허용하느냐* 에 따라 구체적인 모델들이 자리잡습니다. 핵심 세 지점만 보면 왜 하드웨어가 점점 약한 모델로 흘러갔는지가 보입니다.

| 모델 | 허용하는 재배치 | 직관 | 대표 사례 |
|---|---|---|---|
| **SC** (Sequential Consistency) | **없음** — 모든 코어의 load/store가 하나의 전역 순서로 보임 | "프로그램 순서 그대로, 모두가 같은 순서로 관찰" | 이론적 기준점 |
| **TSO** (Total Store Order) | **store→load 만** 완화 (이후 load가 앞선 store를 추월 가능) | "store는 buffer에 잠깐 머물고, 그 뒤 load는 먼저 진행" | x86 계열 |
| **weak / release** | store→store, load→load 까지 폭넓게 완화 (barrier로만 순서 강제) | "기본은 자유, 필요한 곳에만 fence/acquire-release" | ARM, RISC-V 계열 |

왜 SC에서 시작해 점점 풀어 줬을까요? SC는 프로그래머에게 가장 직관적이지만, 하드웨어 입장에서는 *매 store가 전역에 보일 때까지 다음 명령을 못 진행* 하게 만들어 store latency가 그대로 파이프라인 stall이 됩니다. store buffer를 도입해 "store는 buffer에 넣고 곧장 다음 명령 진행" 을 허용하면 stall이 사라지는데, 그 순간 store→load 순서가 깨져 모델이 SC에서 **TSO**로 내려갑니다. 여기에 OoO 실행·write coalescing 같은 최적화를 더 얹으면 store끼리·load끼리의 순서도 흔들려 **weak** 모델이 됩니다. 즉 모델이 약해진 것은 결함이 아니라, store buffer와 OoO로 *성능* 을 얻은 대가로 프로그래머에게 순서 보장을 일부 반납한 결과입니다 — 그 반납분을 프로그래머가 barrier로 *필요한 지점에만* 되사는 구조입니다.

:::note[왜 store buffer는 coherence가 아니라 consistency를 흔드나]
store buffer가 만드는 핵심 효과는 **비대칭 가시성** 입니다 — 내가 buffer에 넣은 store를, *나는* (자기 load가 buffer를 forwarding으로 들여다보니) 곧바로 보지만, *남* 은 그 store가 buffer를 빠져나와 캐시에 반영되기 전까지 못 봅니다. "내가 먼저 보고, 남은 나중에 본다" 는 이 시간차가 바로 *순서* 를 흔드는 원인입니다 — store→load 재배치가 여기서 나옵니다. 그래서 store buffer는 consistency(여러 동작 사이의 순서 계약)에 영향을 줍니다.

그런데 같은 store buffer가 coherence(한 주소의 사본 일관성)는 *깨지 않습니다*. buffer 안의 store는 아직 한 곳(내 코어)에만 있고, 그게 캐시에 commit되어 다른 사본을 만나는 순간에는 여전히 coherence 프로토콜이 SWMR을 강제하기 때문입니다 — commit 시점에 다른 Shared 사본을 invalidate하고, 한 주소에 동시 writer가 둘이 되지 않도록 막습니다. 즉 store buffer는 "한 주소의 사본이 서로 다른 값을 갖게" 만들지 않고, 다만 "그 값이 *언제* 남에게 보이느냐의 순서" 만 늦춥니다. coherence는 *어느 시점에 보든 사본들이 일관* 하다는 single-address 속성이고, store buffer가 건드리는 것은 *서로 다른 동작 간 순서* 라는 multi-operation 속성이라, 둘은 같은 buffer를 두고도 서로 다른 층위에서 영향을 받습니다.
:::

검증 관점에서 이 경계는 중요합니다. coherence checker는 "단일 line의 사본이 SWMR/Data-Value invariant를 위반하는가"를 보고, consistency checker(예: litmus test 기반)는 "여러 주소에 걸친 로드/스토어 결과가 모델이 허용하는 outcome 집합 안에 있는가"를 봅니다. 둘은 서로 다른 reference model을 요구합니다 (추론).

| 구분 | Coherence 검증 | Consistency 검증 |
|---|---|---|
| 대상 | 단일 line 사본의 상태/값 | 멀티-주소 로드/스토어 결과 순서 |
| 전형적 기법 | 상태 전이 모델 + SWMR 모니터 | litmus test, axiomatic model 비교 |
| reference | per-line scoreboard | 허용 outcome 집합 (추론) |

---

## 6. 흔한 오해 와 DV 디버그 체크리스트

### 흔한 오해

:::danger[❓ 오해 1 — 'coherence가 shared memory 동작을 정의한다']
**실제**: coherence는 *단일* 메모리 위치의 사본만 동기화합니다. 여러 주소 간 *순서*는 consistency 모델이 정의합니다. coherence만으로는 "barrier 이후 순서"를 보장하지 못합니다.<br>
**왜 헷갈리는가**: 둘 다 "멀티코어가 올바른 메모리 뷰를 갖게 한다"는 같은 목표를 향하므로 하나로 뭉뚱그려짐.
:::
:::danger[❓ 오해 2 — 'coherence를 켜면 프로그래머가 순서를 신경 안 써도 된다']
**실제**: coherence가 완벽해도 weak consistency 모델에서는 barrier 없이 순서가 보장되지 않습니다. coherence는 *사본 일치*를, consistency는 *순서*를 책임집니다.<br>
**왜 헷갈리는가**: HSA에서 "그냥 포인터 읽으면 된다"는 경험이 *coherence 덕분*으로 보이지만, 실제로는 consistency 모델 + barrier가 그 가정을 뒷받침함.
:::
:::danger[❓ 오해 3 — 'coherence는 프로그래머가 직접 제어한다']
**실제**: coherence는 **transparent** — ISA에 coherence 명령은 없습니다. 프로그래머가 제어하는 것은 barrier/fence(=consistency)와 (IO 경우) cache maintenance op이지, 사본 무효화 자체가 아닙니다.<br>
**왜 헷갈리는가**: cache flush 명령을 coherence 제어로 오인. flush는 coherence가 *없을 때* 소프트웨어가 떠안던 우회책.
:::
### DV 디버그 체크리스트 (이 모듈 내용으로 마주칠 첫 실패들)

| 증상 | 1차 의심 | 어디 보나 |
|---|---|---|
| 두 마스터가 같은 주소를 다른 값으로 읽음 | SWMR 위반 — 두 writer 동시 존재 | per-line state 추적, snoop 응답 로그 |
| 무효화 후에도 stale 값 반환 | Data-Value invariant 위반 | invalidation completion vs 다음 read 타이밍 |
| consistency litmus test 실패인데 coherence는 정상 | 순서 문제 — coherence가 아닌 모델/barrier | reorder/barrier 위치, store buffer drain |
| HSA에서 GPU가 옛 값 읽음 | barrier 누락(consistency) 또는 snoop miss(coherence) | barrier 실행 여부 먼저, 그다음 snoop 경로 |

---

## 7. 핵심 정리 (Key Takeaways)

- **Consistency = 무엇(What)**: 프로그래머에게 보이는 *순서 계약*, 모든 주소 대상. **Coherence = 어떻게(How)**: 투명한 하드웨어 메커니즘, 단일 line 사본만 담당.
- coherence의 정의는 두 invariant로 압축됨: **SWMR**(동시에 쓰는 사본 하나)과 **Data-Value**(무효화 후 다음 read는 최신값).
- 둘은 *함께* 일한다 — pipeline + protocol이 한 팀이 되어 프로그래머가 보는 consistency 모델을 만족시킴.
- 역사: uniprocessor의 sequential illusion → SMP에서 붕괴 → snooping(MESI/MOESI) 발명 → multi-core SoC/HSA에서 directory·ACE/CHI로 진화.
- HSA가 분리를 가장 선명하게 보여줌: 프로그래머는 consistency를 *가정*하고, 인터커넥트는 coherence로 그 가정을 *떠받침*(dirty 데이터를 DRAM 우회로 GPU에 전달).

:::caution[실무 주의점]
- coherence checker와 consistency checker는 *다른* reference model을 요구한다 — 하나로 합치려 하지 말 것.
- "stale 읽음" 버그는 먼저 consistency(barrier 누락)인지 coherence(snoop/무효화 실패)인지 *분류*부터 — 분류가 틀리면 엉뚱한 곳을 본다.
:::
### 7.1 자가 점검

:::tip[🤔 Q1 — What vs How (Bloom: Analyze)]
"coherence를 완벽히 구현했으니 우리 멀티스레드 프로그램은 어떤 순서로 짜도 안전하다"는 주장은 왜 틀렸나?
<details>
<summary>정답</summary>

coherence는 *단일 주소*의 사본만 일치시킬 뿐, *여러 주소 간 순서*는 consistency 모델이 정의합니다. weak 모델에서는 coherence가 완벽해도 barrier 없이 store/load 순서가 재배치될 수 있어, 다른 코어가 의도와 다른 순서로 관찰할 수 있습니다. 안전을 위해선 consistency 모델이 요구하는 barrier/fence를 명시해야 합니다.
</details>
:::
:::tip[🤔 Q2 — SWMR (Bloom: Evaluate)]
한 시스템이 "여러 코어가 동시에 같은 line에 write 가능하지만, 마지막에 값을 머지한다"고 주장한다. 이게 coherence 정의를 만족하는가?
<details>
<summary>정답</summary>

만족하지 않습니다. SWMR invariant는 임의의 순간 *한 코어만 write*하거나 *여러 코어가 read만* 하도록 요구합니다. "동시 write 후 머지"는 두 writer가 동시에 존재하는 상태이므로 SWMR을 정면으로 위반합니다. 그런 시스템은 coherent하다고 부를 수 없습니다 (출처: A Primer on Memory Consistency and Cache Coherence (Sorin/Hill/Wood)).
</details>
:::
### 7.2 출처

**External**
- *A Primer on Memory Consistency and Cache Coherence* (Nagarajan, Sorin, Hill, Wood), Morgan & Claypool — §1, §2 (consistency vs coherence, SWMR)

---

## 다음 모듈

→ [Module 02 — Snooping & MESI/MOESI](../02_snooping_mesi_moesi/): "어떻게(How)"의 첫 구현 — 버스 스누핑이 SWMR/Data-Value invariant를 실제 상태 전이로 어떻게 강제하는가.

[퀴즈 풀어보기 →](../quiz/01_consistency_vs_coherence_quiz/)
