---
title: "07 — 코딩·행동·영어 모의면접"
---

:::tip[학습 목표]
이 모듈을 마치면:

- **Apply** 비트 조작·해시·스택·LRU 같은 DV 면접 단골 알고리즘을 깔끔한 C++/Python으로 작성한다.
- **Demonstrate** "clarify → brute force → optimize → complexity → edge case → code → dry-run" 순서의 think-aloud 코딩 스크립트를 실행한다.
- **Construct** "가장 어려웠던 버그" 이야기를 first error·TB/DUT 분류·근본원인·고정 seed 재현·coverage 보강이 드러나는 STAR 구조로 설계한다.
- **Justify** "왜 DV·왜 CPU·왜 이 회사"와 의견 충돌 사례를 "증거로 설득" 원칙으로 정당화한다.
- **Demonstrate** intro·UVM·아키텍처·ARM·코딩·행동 라운드의 영어 답변을 자연스러운 구어체로 말한다.
- **Evaluate** 면접관에게 던질 질문을 골라 자신의 시니어리티와 적합도를 드러낸다.
:::
:::note[사전 지식]
- 면접 구조·갭 분석은 [01 — 역할·전략·갭 분석](./01_role_and_strategy/)에서 먼저 잡을 것
- 알고리즘 기초가 얕으면 [BigTech Algorithm](../bigtech_algorithm/)으로 보강
:::

---

## 1. DV 면접의 코딩 구간이 다른 이유

CPU DV 면접의 코딩 라운드는 일반 SWE 코딩 면접과 목적이 조금 다르다. 알고리즘 천재를 뽑으려는 게 아니라, *"이 사람이 자극 생성기·스코어보드·분석 스크립트를 직접 짤 수 있는가"*를 본다. 그래서 출제 빈도가 높은 건 화려한 DP가 아니라 **비트 조작**(레지스터·마스크·플래그를 다루므로), **해시/스택**(트랜잭션 매칭·괄호류 파싱), 그리고 **LRU 캐시 설계**(캐시 replacement를 직접 검증하는 직무와 직결)다. 핵심은 정답 코드보다 *사고 과정을 영어로 끊김 없이 말하는 능력*이다. 침묵은 감점이고, 틀린 길로 가더라도 소리 내어 자가수정하는 모습이 가산이다.

### 1.1 think-aloud 코딩 스크립트

어떤 문제가 나오든 이 7단계를 입에 붙여 두면 흐름이 끊기지 않는다. **brute force**(가장 단순한 무식한 풀이 — 일단 정답은 보장되는 기준선)를 먼저 말하고 최적화로 넘어가는 순서가 중요하다.

1. **입력·제약·반환 확인** — "unsigned인가? 크기 상한은? 빈 입력 가능?"
2. **예시로 이해 확인** — 작은 입력 하나로 출력을 맞춰 본다.
3. **brute force 언급 + 복잡도** — 기준선을 먼저 깔고 "이건 O(n²)" 식으로.
4. **최적화 아이디어** — 해시로 O(n), 비트 트릭으로 O(set bits) 등.
5. **코드 작성** — 깔끔하게, 변수명 의미 있게.
6. **dry-run 1케이스** — 한 입력을 손으로 추적해 정합성 확인.
7. **edge case** — 빈 입력, 오버플로우, 음수, 중복, 0.

## 2. 비트 조작 — 검증자 단골

레지스터·마스크를 매일 다루는 DV 직무라 비트 트릭은 거의 반드시 나온다. 토대 한 줄: **`n & (n-1)`은 정수에서 가장 낮은 set bit 하나를 지운다.** 이 한 줄에서 2의 거듭제곱 판정과 popcount가 모두 파생된다.

### 2.1 2의 거듭제곱 판정 / 최하위 set bit 분리

```cpp
bool isPow2(unsigned n){ return n && !(n & (n-1)); }   // O(1)
unsigned lowestSetBit(unsigned n){ return n & (-n); }   // isolate LSB
```

`isPow2`의 원리: 2의 거듭제곱은 set bit가 정확히 하나다(`1000...`). 그 수에서 1을 빼면 그 비트 아래가 전부 1이 되므로(`0111...`) AND하면 0이 된다. `n &&` 가드는 0을 거듭제곱으로 오판하지 않게 한다. `lowestSetBit`의 `n & (-n)`은 2의 보수에서 부호 반전이 최하위 set bit를 기준으로 위쪽 비트를 뒤집는 성질을 이용해 그 비트만 남긴다.

### 2.2 popcount (Brian Kernighan)

```cpp
int popcount(unsigned n){ int c=0; while(n){ n &= n-1; ++c; } return c; }
```

`n &= n-1`이 매 반복마다 최하위 set bit를 하나씩 지우므로, 루프는 *set bit 개수만큼만* 돈다. 따라서 복잡도는 단순 32회 시프트의 O(32)가 아니라 **O(set bit 수)**다. edge: 0이면 루프를 한 번도 안 돌아 0 반환, unsigned로 두어 부호 확장 함정을 피한다.

## 3. 해시·스택·설계 문제

### 3.1 two-sum — 해시로 O(n)

```python
def two_sum(nums, target):       # O(n) time, O(n) space
    seen = {}
    for i, x in enumerate(nums):
        if target - x in seen:
            return [seen[target - x], i]
        seen[x] = i
    return []
```

brute force는 모든 쌍을 보는 O(n²). 해시맵에 "지금까지 본 값 → 인덱스"를 쌓으면 각 원소에서 보수(`target - x`)가 이미 있는지 O(1)로 확인해 전체 O(n)이 된다. 면접에서는 "공간을 써서 시간을 산다"는 trade-off를 한마디 덧붙인다.

### 3.2 유효 괄호 — 스택

```python
def valid(s):
    pairs = {')': '(', ']': '[', '}': '{'}
    st = []
    for c in s:
        if c in pairs.values():       # opening
            st.append(c)
        elif c in pairs:              # closing
            if not st or st.pop() != pairs[c]:
                return False
    return not st                     # leftover opens → invalid
```

여는 괄호는 push, 닫는 괄호는 top과 짝이 맞는지 확인 후 pop. edge: 빈 문자열(유효), 닫힘이 먼저 오는 경우(`st`가 비어 즉시 False), 끝에 열린 게 남은 경우(`return not st`가 잡음).

### 3.3 LRU 캐시 — DV 캐시 replacement와 연결

LRU(Least Recently Used)는 면접 단골이면서 동시에 *직무 직결*이다. 캐시 replacement 정책을 검증하는 직무이므로, "LRU를 코드로 짤 수 있다 = 캐시 동작을 이해한다"는 시너지 신호가 된다.

```python
from collections import OrderedDict

class LRUCache:
    def __init__(self, capacity):
        self.cap = capacity
        self.od = OrderedDict()       # key insertion/use order

    def get(self, key):               # O(1)
        if key not in self.od:
            return -1
        self.od.move_to_end(key)      # mark most-recently used
        return self.od[key]

    def put(self, key, value):        # O(1)
        if key in self.od:
            self.od.move_to_end(key)
        self.od[key] = value
        if len(self.od) > self.cap:
            self.od.popitem(last=False)   # evict LRU (front)
```

직접 구현이라면 **해시맵 + 이중 연결 리스트**다: 해시맵으로 키→노드 O(1) 조회, 연결 리스트로 최근 사용 노드를 head로 옮기고 꽉 차면 tail(가장 오래된 것)을 제거. 두 자료구조를 조합해 get/put 둘 다 O(1)을 달성한다는 점이 핵심 포인트다.

### 3.4 LeetCode 연습 세트

- **비트**: #191 popcount, #338 counting bits, #136 single number(XOR)
- **배열/해시**: #1 two-sum, #217 contains duplicate, #560 subarray sum equals K
- **스택**: #20 valid parens, #155 min stack
- **설계**: #146 LRU cache
- **문자열**: #3 longest substring, #49 group anagrams

## 4. 디버깅 스토리 — STAR로 설계하기

행동 면접에서 "가장 어려웠던 버그"는 거의 확정 출제다. 즉흥으로 말하면 산만해지므로 **STAR**(Situation·Task·Action·Result) 골격에 DV 디버깅의 핵심 키워드를 미리 박아 둔다. 면접관이 듣고 싶은 신호는 셋이다: *first error를 cascading에서 분리했는가*, *TB 버그인지 DUT 버그인지 분류했는가*, *근본 원인을 file:line으로 짚고 고정 seed로 재현했는가*.

### 4.1 모델 STAR 내러티브

> **Situation:** HLS 생성 datapath를 검증하던 중 constrained-random 테스트가 *간헐적으로* 실패했다.
> **Task:** 근본 원인을 찾고, TB 버그인지 DUT 버그인지 분류해야 했다.
> **Action:** 로그를 먼저 보고 타임스탬프로 *첫 번째* 에러를 격리했다 — 이후 에러들은 cascading이었기 때문이다. 실패 트랜잭션을 C++ 소스까지 역추적해 생성된 RTL 파이프라인과 대조했고, 특정 back-pressure 조건에서 생성된 설계의 stall 조건이 알고리즘과 divergence함을 찾았다.
> **Result:** 정확한 발생 조건과 함께 DUT 버그로 파일링했고, 고정 seed의 directed 테스트로 재현을 박제했다. 같은 back-pressure corner를 앞으로도 잡도록 coverage point를 추가했다.

키워드를 의식적으로 쓴다: "first error", "cascading", "root cause", "design vs testbench", "fixed seed to reproduce", "coverage". HLS 경험이 있다면 "C++가 spec이고 RTL이 구현 — 둘의 divergence를 추적했다"가 특히 강력하다.

### 4.2 hang/timeout 디버깅 접근

별도로 "시뮬레이션이 hang됐다, 어떻게?"가 나오면: 로그의 마지막 활동 지점 확인 → 어떤 컴포넌트가 대기 중인지(핸드셰이크 stuck, `ap_ready`/`ap_idle`류) → 의존 신호 역추적 → *자극이 응답을 안 받는지 vs DUT가 멈췄는지* 분리. 로그 우선, 필요할 때만 파형으로 escalation.

## 5. 행동 / Googleyness

### 5.1 왜 DV·왜 CPU·왜 이 회사

세 질문은 묶어서 준비한다. **DV**: "설계가 spec대로 동작함을 보장하는 마지막 방어선이자, 근본 원인을 추적하는 지적 매력." **CPU**: "가장 복잡하고 모든 소프트웨어가 의존하는 IP라 검증의 leverage가 가장 크다 — 한 버그가 위의 전부에 영향을 준다." **회사**: "AI·소프트웨어·하드웨어의 수직 통합과, 수억 사용자 제품에 들어가는 실리콘이라는 임팩트."

### 5.2 의견 충돌 — "사람이 아니라 데이터와 싸운다"

> 한 프로젝트에서 설계자와 "이게 버그냐, 아니면 spec이 모호한 거냐"로 충돌했다. 의견을 다투는 대신 관련 spec 섹션과 C++ reference를 꺼내 예상값 계산을 함께 따라가며 RTL이 어디서 divergence하는지 정확히 보여줬다. 논의가 의견이 아니라 증거로 옮겨가자 빠르게 합의했고, 모호함을 없애도록 spec을 갱신했다. 교훈은 *"argue with data, not with people"*이다.

### 5.3 실패/배움

놓친 coverage hole이 프로젝트 후반에야 발견된 사례가 좋다. 결론은 "coverage hole = 미검증 리스크"로 보게 됐고, 이후 vplan에 반영하고 자동화로 재발을 막았다는 학습으로 닫는다.

## 6. English Mock Interview

> Google 면접은 **영어로** 진행된다. 아래 [A]는 자연스러운 구어체 모범 답변이니 소리 내어 말하며 구조를 체화하라. 단어를 통째 외우지 말고, 구조를 익혀 자기 언어로.

### 6.1 Intro

**[Q]** Tell me about yourself.
**[A]** "I'm a design verification engineer with around four years of experience verifying ASIC designs using UVM and SystemVerilog on Synopsys VCS. Most of my work has been on HLS-generated RTL, where I analyze the C++ algorithm first and then map it to the generated hardware — the pipeline, the handshakes, the resource sharing. I build reusable UVM environments from scratch: agents, scoreboards, coverage models, and regression flows driven by Python tooling. What draws me to this role is moving from block-level verification toward CPU core verification, which is the most complex and foundational IP in any SoC."
**[Tip]** 30~40초. "HLS → 마이크로아키텍처 독해력" 연결을 자연스럽게, 끝은 "why this role"로.

**[Q]** Why do you want to work on CPU verification here?
**[A]** "Two reasons. First, the CPU is where every piece of software ultimately runs, so verifying it correctly has the highest leverage — a single bug can affect everything above it. Second, the custom silicon goes into products used by hundreds of millions of people, and the vertical integration of AI, software, and hardware is exactly the kind of full-stack challenge I want to be part of."
**[Tip]** 짧고 확신 있게. "highest leverage", "vertical integration" 키워드.

### 6.2 UVM / Methodology

**[Q]** Walk me through how you'd verify a new CPU core from scratch.
**[A]** "I'd build it in layers. At the unit level I verify blocks like the decoder, load-store unit, and branch predictor with directed and constrained-random stimulus, because they're easy to control and I can hit deep corners fast. At the core level, the key is a golden reference — an instruction set simulator. I run a random instruction generator into the DUT, capture the retire trace — committed PC, register writes, memory writes — and do a step-and-compare against the ISS in the scoreboard. At the subsystem level I add coherency and multi-core ordering. On top of all that I drive functional coverage — instruction types, exceptions, privilege transitions, pipeline states like ROB-full — and use formal for properties simulation can't reach, like deadlock freedom and the coherence protocol."
**[Tip]** 이 답이 **핵심 차별화**. layers → ISS step-and-compare → coverage → formal 4단계로, 손으로 계층 그리듯 천천히.

**[Q]** What's the difference between a uvm_component and a uvm_object?
**[A]** "A component lives in the testbench hierarchy and the phasing — things like drivers and monitors. It's built once, top-down, in the build phase, and it needs a name and a parent. An object is dynamic data — sequence items and sequences — created and destroyed at runtime, and it only needs a name. So the real distinction is lifecycle: components are the static structure, objects flow through it."
**[Tip]** "lifecycle"로 마무리하면 정리력 어필.

### 6.3 Computer Architecture

**[Q]** Why does an out-of-order processor need a reorder buffer?
**[A]** "Even though instructions execute out of order, the ROB forces them to retire — to commit their results to architectural state — in program order. That's what gives you precise exceptions and clean branch-misprediction recovery. Speculative results sit in the ROB and only become architectural state when the instruction reaches the head and retires. If there's an exception or a misprediction, everything after that point gets flushed."
**[Tip]** "retire in program order" → "precise exceptions" 인과를 분명히.

**[Q]** What happens on a branch misprediction, and what would you verify?
**[A]** "The processor flushes all the in-flight instructions on the wrong path and refetches from the correct target, so the penalty scales with how deep the speculation went. For verification, the interesting corners are a misprediction that coincides with an exception or interrupt, nested branches, the timing of BTB and BHT updates, and — importantly — making sure speculative memory accesses don't leave observable side effects, which is the whole Spectre class of issues."
**[Tip]** 끝에 보안(Spectre) 언급으로 깊이 어필.

### 6.4 ARM Architecture

**[Q]** Describe the ARM exception levels.
**[A]** "There are four. EL0 is unprivileged application code. EL1 is the OS kernel. EL2 is the hypervisor for virtualization. EL3 is the secure monitor that manages the switch between the secure and non-secure worlds in TrustZone. When an exception happens you move to a higher level — the hardware saves the return address in ELR and the processor state in SPSR — and you return with ERET."
**[Tip]** EL0→EL3 한 호흡, 끝에 ELR/SPSR/ERET 메커니즘.

**[Q]** ARM has a weakly-ordered memory model. What does that mean and why do barriers matter?
**[A]** "It means the hardware is allowed to reorder memory accesses for performance. That's fine for a single thread, but across cores or when talking to a device, you need ordering guarantees. That's what barriers are for: DMB orders memory accesses, DSB additionally waits for them to complete, and ISB flushes the pipeline so later instructions are refetched with updated context — for example after enabling the MMU. For finer-grained control there's acquire-release semantics with LDAR and STLR. This is exactly the kind of thing that's a major corner case in coherency verification."
**[Tip]** DMB/DSB/ISB를 *각각 다르게* 설명하는 게 핵심. x86 TSO 대비를 덧붙여도 좋다.

### 6.5 Coding (think aloud in English)

**[Q]** Count the number of set bits in a 32-bit integer.
**[A]** *(말하면서)* "Let me clarify — it's an unsigned 32-bit value, and I want the population count. The naive way is to shift through all 32 bits, which is O(32). A nicer trick is `n &= n - 1`, which clears the lowest set bit each iteration, so it only loops as many times as there are set bits. Let me write that... *(writes)* ... and the complexity is O(number of set bits). Edge cases: zero returns zero, and I'm treating it as unsigned to avoid sign-extension issues."
```cpp
int popcount(unsigned n){ int c=0; while(n){ n &= n-1; ++c; } return c; }
```
**[Tip]** 영어로 사고과정 중계 연습이 핵심. "Let me clarify", "the complexity is", "edge cases" 같은 연결어를 입에 붙여라.

**Coding phrases to keep ready**
- "Can I assume the input is...?" / "What's the expected input size?"
- "Let me start with a brute-force approach and then optimize."
- "The time complexity is O(n) and space is O(n)."
- "Let me trace through one example to make sure it's correct."
- "One edge case I want to handle is..."

### 6.6 Behavioral

**[Q]** Tell me about the hardest bug you've debugged.
**[A]** *(STAR)* "**Situation:** I was verifying an HLS-generated datapath and a constrained-random test started failing intermittently. **Task:** I needed to find the root cause and tell whether it was a testbench bug or a design bug. **Action:** I went to the log first and isolated the *first* error by timestamp, because the later ones were cascading. I traced the failing transaction back to the C++ source, compared it against the generated RTL pipeline, and found the generated design had a pipeline stall condition that diverged from the algorithm under a specific back-pressure case. **Result:** I filed it as a design bug with the exact condition, added a directed test with a fixed seed to reproduce it, and the fix closed it. I also added a coverage point so we'd catch that back-pressure corner going forward."
**[Tip]** STAR 구조를 명시적으로. "first error", "root cause", "design vs testbench", "fixed seed to reproduce" 키워드.

**[Q]** Tell me about a disagreement with a colleague.
**[A]** "On one project a designer and I disagreed on whether a behavior was a bug or just an under-specified spec. Instead of arguing opinions, I pulled the relevant spec section and the C++ reference, walked through the expected value computation, and showed exactly where the RTL diverged. Once it was about evidence rather than opinion, we aligned quickly and updated the spec to remove the ambiguity. My takeaway is to argue with data, not with people."
**[Tip]** "argue with data, not with people"로 마무리.

### 6.7 Questions to ask the interviewer

- "Is the core you're verifying in-order or out-of-order, and which ARM architecture generation?"
- "How is the work split between pre-silicon and post-silicon for this role?"
- "How mature is the verification environment — are you doing ISS step-and-compare and formal already?"
- "What level — unit, core, or subsystem — would a new engineer typically own first?"

이 질문들은 단순한 호기심이 아니라 *직무를 정확히 이해하고 있다는 신호*다. in-order/OoO를 묻는 건 검증 난이도와 corner를 안다는 뜻이고, pre/post-silicon 비중을 묻는 건 공고의 4대 책임을 읽었다는 뜻이다.

## 7. 발음·전달 체크리스트

- [ ] 답변을 **녹음**해 들어보기 (속도·명료성).
- [ ] 핵심 키워드(retire in program order, weakly-ordered, step-and-compare, precise exception)를 또박또박.
- [ ] 막힐 때 침묵 대신: "Let me think about that for a second."
- [ ] 모르면 솔직히: "I haven't worked with that directly, but based on first principles I'd expect..."
- [ ] 코딩 중에는 사고 과정을 끊지 말 것 — 손과 입을 동시에.

## 핵심 요약

- DV 코딩 면접의 단골은 비트 조작·해시·스택·LRU다 — 정답보다 *영어 think-aloud*(clarify→brute→optimize→complexity→edge→code→dry-run)가 핵심.
- `n & (n-1)`은 최하위 set bit를 지운다 → isPow2·popcount가 여기서 파생, popcount 복잡도는 O(set bit 수).
- "가장 어려웠던 버그"는 STAR로: first error 격리·TB/DUT 분류·근본원인 file:line·고정 seed 재현·coverage 보강.
- 행동 면접은 "왜 DV/CPU/회사"와 "argue with data, not people"를 준비하고, 면접관 질문으로 직무 이해도를 드러낸다.
- 영어는 키워드를 또박또박, 막힐 땐 침묵 대신 연결어로 — 녹음 리허설이 가장 효과적이다.

→ 자기 점검: [퀴즈 — 07장](./quiz/07_coding_behavioral_english_quiz/)
