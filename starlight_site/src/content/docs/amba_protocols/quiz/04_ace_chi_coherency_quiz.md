---
title: "Quiz — Module 04: ACE / CHI Coherency"
---

[← Module 04 본문으로 돌아가기](../../04_ace_chi_coherency/)

---

## Q1. (Remember)

Cache Coherence 가 지키는 두 가지 핵심 invariant 의 이름은?

- [ ] A. SWMR (Single-Writer, Multiple-Reader) 와 Data-Value invariant
- [ ] B. In-order 와 Out-of-order
- [ ] C. Inclusive 와 Exclusive
- [ ] D. Read-after-Write 와 Write-after-Read

<details>
<summary>정답 / 해설</summary>

**A**. coherence 의 두 invariant 는 **SWMR(Single-Writer, Multiple-Reader)** 와 **Data-Value invariant** 입니다.

SWMR 은 임의 시점·임의 주소에 대해 "쓸 수 있는 코어가 하나뿐이거나, 읽기만 하는 코어가 여럿이거나" 둘 중 하나만 성립함을 보장합니다. Data-Value invariant 는 새 epoch 시작 시점의 값이 직전 read-write epoch 끝 시점의 값과 일치함을 보장합니다. B(in/out-of-order)는 AXI 응답 순서, C(inclusive/exclusive)는 LLC 캐시 정책, D(RAW/WAR)는 파이프라인 hazard 로 모두 다른 개념입니다.

</details>
## Q2. (Understand)

Memory Consistency 와 Cache Coherence 의 차이를 가시성(visibility)과 범위(scope) 기준으로 설명하세요.

<details>
<summary>정답 / 해설</summary>

**Consistency** 는 프로그래머에게 _보이는_(ISA·barrier 로 노출) ordering 계약이고 _모든_ 메모리 위치의 연산 순서를 규율합니다. **Coherence** 는 프로그래머에게 _투명한(invisible)_ 하드웨어 메커니즘이고 _단일_ 메모리 위치(캐시 라인)의 사본들만 동기화합니다.

핵심은 두 축입니다. (1) 가시성: consistency 는 프로그래머가 ISA 와 memory barrier 로 직접 다루지만, coherence 는 순수 하드웨어 최적화로 프로그래머에게 완전히 보이지 않습니다. (2) 범위: consistency 는 모든 주소에 걸친 전체 ordering 을, coherence 는 한 주소의 사본 동기화만 다룹니다. ACE/CHI 인터커넥트는 coherence 쪽 기계이며, 프로세서 파이프라인과 함께 프로그래머가 관찰하는 consistency 모델을 공동으로 만족시킵니다.

</details>
## Q3. (Apply)

CPU 가 주소 A 에 0x1234 를 써서 L2 에 dirty 로 보유 중이고, DRAM 의 A 에는 0x0000 이 있다. GPGPU 가 ACE 로 A 를 ReadShared 하면 받는 값과 그 출처는?

<details>
<summary>정답 / 해설</summary>

- 받는 값: **0x1234**
- 출처: **CPU L2 캐시** (DRAM 우회)

ACE coherent interconnect 는 GPGPU 의 read 를 가로채 snoop filter 로 A 를 보유한 CPU 를 찾고, CPU 에 snoop 을 발행합니다. CPU 가 dirty(Modified) 임을 응답하며 그 라인 데이터를 넘기면, interconnect 는 _DRAM 의 옛값(0x0000)을 우회_ 하고 CPU 에서 받은 최신값(0x1234)을 GPGPU 로 라우팅합니다(느린 main memory 를 완전히 우회). 동시에 CPU 의 라인 상태는 Modified→Shared 로 낮아져 SWMR 이 유지됩니다(이제 reader 가 둘). 이 때문에 scoreboard 가 DRAM 을 expected 로 잡으면 false mismatch 가 발생합니다.

</details>
## Q4. (Apply)

캐시가 없는 DMA 컨트롤러를 IO-coherent 하게 통합하려 한다. full ACE 와 ACE-Lite 중 무엇을 선택하고, 그렇게 하면 소프트웨어 측에서 무엇이 사라지는가?

<details>
<summary>정답 / 해설</summary>

- 선택: **ACE-Lite** (one-way / IO coherency)
- 사라지는 것: **수동 cache flush/clean 명령** (드라이버의 cache maintenance 코드)

DMA 는 자기 캐시가 없으므로 snoop 을 _수신_ 할 라인이 없습니다. 필요한 것은 "남의(CPU) 캐시를 snoop 해서 최신 데이터를 받는" one-way coherency 뿐이므로 ACE-Lite 가 적합합니다. 과거에는 CPU 가 캐시에 준비한 데이터를 DMA 가 읽기 전에 소프트웨어가 명시적으로 cache flush 를 실행해야 했습니다. IO-coherent 포트에 DMA 를 붙이면 interconnect 가 read 시 자동으로 CPU 캐시를 snoop 해 dirty 데이터를 끌어오므로, 드라이버에서 cache maintenance 코드가 사라지고 성능이 오르며 코드가 단순해집니다.

</details>
## Q5. (Analyze)

멀티코어 SoC 에서 snoop 트래픽이 폭증해 인터커넥트가 포화 상태다. 1차로 의심할 메커니즘과, 정상이라면 트래픽을 줄여주는 LLC 의 두 가지 동작은?

<details>
<summary>정답 / 해설</summary>

- 1차 의심: snoop 이 **broadcast** 되고 있음 (snoop filter 미동작)
- LLC 의 트래픽 절감 동작: **Snoop Filter(Directory) 기반 Targeted Snoop** 과 **back-invalidation 으로 inclusive 유지** (orphan 데이터 제거)

코어가 많을 때 모든 L1/L2 에 "이 데이터 있니?" 를 broadcast 하면 버스가 막힙니다. 정상 시스템에서는 LLC 가 snoop filter(directory)를 들고 어느 upstream 캐시가 어느 라인을 가졌는지 추적해, 요청이 오면 _해당 캐시에만_ targeted snoop 을 보냅니다 — 이것이 트래픽을 급감시키는 핵심입니다. 따라서 트래픽 폭증은 directory 가 동작하지 않아 broadcast 로 떨어진 정황을 의심해야 합니다. 또한 strictly inclusive LLC 는 라인 evict 시 back-invalidation 으로 upstream 사본을 함께 버려 수직 coherency 를 유지합니다.

</details>
## Q6. (Evaluate)

AXI 시절의 scoreboard(expected = DRAM 모델값)를 ACE/CHI DUT 에 그대로 재사용했더니 대량의 mismatch 가 발생했다. 이것이 DUT 버그인지 TB 문제인지 판단하고, 올바른 expected 계산을 설명하세요.

<details>
<summary>정답 / 해설</summary>

**TB 문제(non-coherent scoreboard 재사용)** 일 가능성이 높습니다. coherent read 의 정답은 DRAM 값이 아니라 _dirty 를 들고 있는 다른 master 의 캐시 값_ 입니다. DRAM 을 expected 로 잡으면 dirty holder 가 있을 때마다 false mismatch 가 납니다.

올바른 coherent scoreboard 는 (1) 모든 cached master 의 라인 상태를 모델링하고, (2) read 가 오면 해당 주소를 dirty 로 보유한 master 가 있으면 그 캐시 값을, 없으면 DRAM 값을 expected 로 계산하며, (3) write 가 오면 다른 모든 Shared 사본을 Invalid 로 전이시켜 SWMR 을 유지해야 합니다. 단, 이렇게 보정한 뒤에도 mismatch 가 남는다면(예: write 후 다른 master 의 사본이 invalidate 되지 않음) 그때는 진짜 DUT 의 coherency 버그를 의심합니다 — 즉 TB 를 먼저 coherent 하게 바로잡은 뒤에야 DUT 판정이 의미를 가집니다.

</details>
