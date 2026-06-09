---
title: "Quiz — Module 01: Consistency vs Coherence"
---

[← Module 01 본문으로 돌아가기](../../01_consistency_vs_coherence/)

---

## Q1. (Remember)

Cache Coherence의 가시성(visibility)에 대한 설명으로 옳은 것은?

- [ ] A. 프로그래머에게 ISA와 barrier로 노출되는 계약이다
- [ ] B. 프로그래머에게 완전히 투명한(transparent) 하드웨어 메커니즘이다
- [ ] C. 컴파일러가 명시적으로 제어한다
- [ ] D. OS 커널이 매 컨텍스트 스위치마다 설정한다

<details>
<summary>정답 / 해설</summary>

**B**. Cache Coherence는 순수한 하드웨어 최적화 메커니즘으로 프로그래머에게 완전히 투명(invisible)합니다. ISA에는 coherence 명령이 없습니다. A는 Memory *Consistency*의 특성(programmer-visible 계약)이며, coherence와 혼동하면 안 됩니다. C/D처럼 컴파일러나 OS가 직접 사본 무효화를 제어하지 않습니다.

</details>
## Q2. (Understand)

"Memory Consistency는 무엇(What), Cache Coherence는 어떻게(How)"라는 구분에서, *범위(scope)* 측면의 차이를 설명하라.

<details>
<summary>정답 / 해설</summary>

Memory Consistency는 *모든* 메모리 위치에 대한 로드/스토어의 *순서*를 다루는 계약입니다. 반면 Cache Coherence는 *단일* 메모리 위치(cache line)의 *사본 동기화*만 담당합니다. 즉 consistency는 여러 주소 간 순서를 정의하고, coherence는 한 주소의 여러 사본을 일치시킬 뿐 주소 간 순서는 정의하지 않습니다. 둘은 pipeline과 protocol이 함께 일해 프로그래머가 보는 consistency 모델을 만족시킵니다.

</details>
## Q3. (Apply)

HSA에서 CPU가 행렬을 메모리에 쓰고 sync barrier를 실행한 뒤 GPGPU가 그 포인터를 읽는다. 이때 "barrier 이후 GPU가 최신값을 본다"는 보장은 무엇이 책임지고, dirty 데이터를 DRAM 우회로 GPU에 전달하는 일은 무엇이 책임지는가?

<details>
<summary>정답 / 해설</summary>

"barrier 이후 GPU가 최신값을 본다"는 *순서 보장*은 **Memory Consistency 모델**이 책임집니다 — 프로그래머가 의존하는 가정입니다. 반면 CPU의 L1/L2에 dirty로 남은 행렬을 인터커넥트(ACE/CHI)가 snoop으로 추출해 DRAM을 우회하여 GPU로 직접 전달하는 일은 **Cache Coherence 메커니즘**(하드웨어)이 책임집니다. 소프트웨어는 이 복잡한 거래를 전혀 보지 못합니다.

</details>
## Q4. (Analyze)

어떤 시스템이 "임의의 순간, 같은 line에 대해 두 코어가 동시에 write 권한을 갖되 마지막에 머지한다"고 주장한다. 이 시스템이 위반하는 invariant는 무엇이며 왜인가?

- [ ] A. Data-Value invariant — 값이 머지되므로
- [ ] B. SWMR invariant — 동시 writer가 둘이므로
- [ ] C. 둘 다 만족 — 머지로 일관성 유지
- [ ] D. consistency 모델만 위반

<details>
<summary>정답 / 해설</summary>

**B**. SWMR(Single-Writer, Multiple-Reader) invariant는 임의의 순간 *한 코어만 write*하거나 *여러 코어가 read만* 하도록 요구합니다. "두 코어가 동시에 write 권한 보유"는 single-writer 조건을 정면으로 위반합니다. A의 Data-Value는 "새 epoch 시작값 = 직전 read-write epoch 종료값"으로 머지 여부가 아니라 무효화 후 최신값 보장에 관한 것입니다. 동시 write를 허용하는 시스템은 coherent하다고 부를 수 없습니다.

</details>
## Q5. (Evaluate)

"우리 칩은 coherence를 완벽히 구현했으니 멀티스레드 코드를 어떤 순서로 짜도 안전하다"는 주장을 평가하라.

<details>
<summary>정답 / 해설</summary>

틀린 주장입니다. coherence는 *단일 주소*의 사본만 일치시킬 뿐, *여러 주소 간 순서*는 consistency 모델이 정의합니다. weak consistency 모델에서는 coherence가 완벽해도 barrier 없이 store/load가 재배치될 수 있어, 다른 코어가 의도와 다른 순서로 관찰합니다. 안전을 위해서는 consistency 모델이 요구하는 barrier/fence를 명시해야 합니다. coherence와 consistency를 혼동한 전형적 오류입니다.

</details>
