---
title: "Quiz — 04: 일관성·메모리 모델"
---

본 모듈의 핵심 개념 이해도를 점검합니다. 정답은 펼치면 보입니다.

[← 04장 본문으로 돌아가기](../../04_coherence_and_memory_model/)

---

## Q1. (Understand)

다음 중 cache *coherence*와 memory *consistency*의 차이를 가장 정확히 요약한 것은?

- [ ] A. coherence는 순서, consistency는 값
- [ ] B. coherence는 단일 주소의 값 일치, consistency는 여러 주소 간 접근 순서
- [ ] C. 둘은 같은 개념의 다른 이름이다
- [ ] D. coherence는 프로그래머에게 보이고, consistency는 투명하다

<details>
<summary>정답 / 해설</summary>

**B**. "Coherence는 값, consistency는 순서"가 핵심 한 줄이다. coherence는 *단일 메모리 위치*의 사본을 모든 캐시에서 같은 값으로 맞추는 하드웨어 메커니즘이고, consistency는 *여러 주소*에 대한 로드/스토어가 어떤 순서로 관찰되는지를 규정하는 계약이다. A는 둘을 정확히 뒤바꾼 오답이다. C는 가장 위험한 오해로, coherence가 완벽해도 weak 모델에서는 barrier 없이 순서가 깨진다. D도 거꾸로다 — coherence가 ISA에 명령이 없는 *투명한* 메커니즘이고, consistency가 barrier/fence로 프로그래머에게 *노출*된다.

</details>

## Q2. (Remember)

MESI 4상태 중 "내가 유일하게 보유하고, 메모리와 값이 일치(clean)하는" 상태는?

- [ ] A. M (Modified)
- [ ] B. E (Exclusive)
- [ ] C. S (Shared)
- [ ] D. I (Invalid)

<details>
<summary>정답 / 해설</summary>

**B**. E(Exclusive)는 사본이 나뿐(독점)이면서 메모리와 일치하는 clean 상태다. A(M)도 독점이지만 *dirty*(메모리보다 최신)라 eviction 시 반드시 write-back해야 한다 — E와 M의 차이는 바로 이 메모리 일치 여부다. C(S)는 다른 캐시도 사본을 가질 수 있는 공유 clean 상태이고, D(I)는 사본이 없는 무효 상태다. E를 따로 둔 덕분에 read→write 패턴에서 무효화 broadcast를 생략할 수 있다는 점이 MESI의 효율 포인트다.

</details>

## Q3. (Apply)

Core0이 line X에 대해 `read miss → write → (Core1이 X read miss)` 순으로 접근한다. 다른 캐시에는 처음에 X 사본이 없었다. MESI 기준으로 Core0의 상태 전이는?

<details>
<summary>정답 / 해설</summary>

**I → E → M → S** 순이다. ① read miss인데 사본이 나뿐이라 shared 신호가 0 → **E**(독점 clean)로 받는다. ② 이미 E(독점)이므로 write 시 무효화 broadcast 없이 **M**(dirty)으로 간다 — *버스 트래픽 0*이 핵심이다. ③ Core1이 X를 read 요청하면 Core0이 dirty(M)를 보유 중이므로 메모리가 아닌 *Core0 캐시에서 직접* 데이터를 cache-to-cache로 공급하고, Core0은 **M → S**로 내려가며 메모리에 write-back한다(Core1은 I → S). 만약 MOESI라면 ③에서 write-back을 생략하고 Core0이 M → **O**로 가서 dirty를 보유한 채 공급한다.

</details>

## Q4. (Analyze)

한 멀티스레드 프로그램이 *기능적으로는 정확*한데, 코어 수를 늘릴수록 성능이 급격히 떨어진다. coherence 트랜잭션 카운터를 보니 특정 cache line의 invalidate가 비정상적으로 잦다. 가장 가능성 높은 원인과 검증 방법은?

<details>
<summary>정답 / 해설</summary>

**False sharing**이다. 서로 *논리적으로 무관한* 변수들이 같은 cache line(보통 64B)에 들어 있으면, 한 코어가 자기 변수만 write해도 line 전체가 무효화되어 다른 코어의 무관한 변수 접근이 miss를 일으킨다. 코어들이 같은 line의 다른 바이트를 번갈아 쓰면 invalidate ping-pong이 일어나 coherence 트래픽이 폭증한다 — *기능은 정상이지만 성능만 무너지는* 것이 특징적 증상이다. 검증/탐지는 두 갈래다: (1) 성능 카운터로 line당 invalidate 빈도가 비정상인지 보고, (2) coverage cross로 "서로 다른 코어가 동일 line 접근"을 잡는다. 수정은 변수를 다른 line으로 분리(cache line alignment/padding)하는 것이다. "기능 OK, 성능 급락"은 false sharing을 1순위로 의심하라.

</details>

## Q5. (Apply)

ARM(weak 모델)에서 producer가 데이터를 쓴 뒤 `ready=1` 플래그를 세우고, consumer가 `ready==1`을 본 뒤 데이터를 읽는 lock-free 핸드오프가 있다. barrier 없이 두면 어떤 버그가 나며, 어디에 무엇을 두어야 하나?

<details>
<summary>정답 / 해설</summary>

weak 모델은 store→store, load→load 재배치를 허용하므로, producer의 두 store(데이터, flag)가 *뒤바뀌어* consumer가 `ready=1`을 봤는데 데이터는 아직 옛 값일 수 있다(consumer 쪽에서도 데이터 load가 flag load를 추월 가능). 고치려면 짝으로 둔다: producer의 `ready` write를 **store-release(STLR)** — 앞선 데이터 store들을 release 뒤로 *가둔다*; consumer의 `ready` read를 **load-acquire(LDAR)** — 이후 데이터 load들을 acquire 앞으로 *가둔다*. 이 release/acquire 짝이 "데이터가 flag보다 먼저, 데이터 읽기가 flag 확인보다 나중"이라는 순서를 강제한다. x86(TSO)은 store→load만 완화라 이 패턴이 우연히 동작하기도 하지만, ARM에서는 명시 barrier가 *필수*다 — 그래서 "x86보다 ARM에서 barrier를 더 신경 쓴다"가 면접 단골이다.

</details>

## Q6. (Evaluate)

설계 리뷰에서 한 엔지니어가 "코어 수를 64개로 늘리는데, 기존 broadcast snooping을 그대로 쓰고 coherence deadlock은 timeout 회귀로 충분히 잡는다"고 주장한다. 이 계획을 평가하라.

<details>
<summary>정답 / 해설</summary>

두 가지 모두 부적절하다. **(1) 프로토콜 선택**: broadcast snooping은 모든 트랜잭션을 모든 캐시에 broadcast하므로 코어 64개에서는 버스/인터커넥트 대역폭이 병목이 된다 — 이 규모에서는 사본 보유자에게만 targeted snoop을 보내는 *directory* 기반(ARM CHI/ACE류, home node가 ordering point)으로 가야 확장된다. **(2) deadlock 검증**: coherence deadlock은 요청/응답/snoop 채널 간 순환 의존 + 버퍼 고갈에서 생기며, 상태공간이 깊어 *시뮬 timeout 회귀로는 모든 경로를 닿을 수 없다* — 통과해도 deadlock 부재를 증명하지 못한다. 올바른 접근은 (a) 설계 차원에서 virtual channel 분리(req/rsp/snoop) + credit 기반 흐름제어로 순환·고갈을 예방하고, (b) formal로 "모든 요청은 결국 응답을 받는다"는 liveness 속성을 증명하는 것이다. timeout 회귀는 보조일 뿐 sign-off 근거가 될 수 없다.

</details>
