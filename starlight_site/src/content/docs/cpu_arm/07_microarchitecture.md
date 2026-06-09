---
title: "Module 07 — Microarchitecture (Frontend / OoO Backend / LSU)"
---

:::tip[학습 목표]
이 모듈을 마치면:

- **Explain** frontend (BPU → FTQ → I-cache → decode → micro-op crack) 가 backend 를 굶기지 않게 명령을 공급하는 구조와 decoupled fetch 의 역할을 설명할 수 있다.
- **Differentiate** 2-bit 포화 카운터, gshare, TAGE-SC-L, RAS, BTB 등 분기 예측 기법을 정확도·자원 기준으로 구분할 수 있다.
- **Trace** OoO backend 에서 한 명령이 rename → dispatch → issue → execute → in-order retire 로 흐르는 과정과 ROB 의 역할을 추적할 수 있다.
- **Analyze** LSU 의 LDQ/STQ, store-to-load forwarding, memory disambiguation, MSHR 이 메모리 IPC 를 어떻게 결정하는지 분석할 수 있다.
- **Evaluate** 같은 issue width 라도 PRF/ROB/MSHR 크기 차이가 실측 IPC 를 가르는 이유를 평가할 수 있다.
- **Apply** big.LITTLE / DynamIQ(DSU) 의 이종 코어 구조가 워크로드 배치에 주는 영향을 설명할 수 있다.
:::
:::note[사전 지식]
- [Module 01-06](../01_overview_isa/) — 특히 [M06 Caches & GIC](../06_caches_gic/) 의 precise exception, [M04 Memory Model](../04_memory_model_barriers/)
- 파이프라인·OoO 일반 개념 — 깊은 일반론은 [Computer Architecture 토픽](../../computer_architecture/)
- coherence 깊이는 [Cache Coherence 토픽](../../cache_coherence/) 참조
:::
---

## 1. Why care? — IPC 는 "가장 작은 자원" 이 결정한다

### 1.1 시나리오 — 같은 8-wide 인데 IPC 가 다르다

두 코어가 모두 8-wide decode 라고 광고합니다. 그런데 SPEC IPC 가 한쪽이 눈에 띄게 높습니다. 왜일까요?

여기서 **IPC**(Instructions Per Cycle — 한 클럭에 평균 몇 개의 명령을 끝내는가, 높을수록 빠름)가 성능의 핵심 지표입니다. 답은 **frontend**(명령을 가져와 해독해 공급하는 앞단) 와 **backend**(실제로 명령을 실행·완료하는 뒷단) 의 어느 자원이 먼저 saturate(포화) 되느냐 입니다. issue width(한 사이클에 실행에 보낼 수 있는 명령 수)만 같아도 **ROB**(Reorder Buffer — 명령을 순서 없이 실행해도 완료(retire)는 프로그램 순서로 되돌리는 큐), **PRF**(Physical Register File — 아키텍처 레지스터보다 훨씬 많은 실제 물리 레지스터 묶음), **IQ**(Issue Queue — 실행 준비된 명령을 고르는 대기열), **LDQ/STQ**(Load/Store Queue — 진행 중인 메모리 명령을 추적하는 큐), **MSHR**(Miss Status Handling Register — 진행 중인 캐시 miss를 추적하는 항목) 중 가장 작은 자원이 IPC 를 옭아맵니다. 예컨대 Apple Firestorm 은 ROB ~630, INT PRF ~354 로 같은 width 8 인 Cortex-X2 (ROB ~288) 보다 훨씬 큰 window 를 가져, cache miss 동안 더 많은 독립 명령을 찾아 실행함으로써 IPC 가 높습니다 (uarch/OoOBackend).

게다가 frontend 도 별도의 병목입니다. 실제 application 의 stall breakdown 에서 **Frontend Bound** 가 30~50% 를 차지하는 일이 흔한데, branch mispredict, I-cache miss, decode bottleneck 이 합쳐진 결과입니다 (uarch/Frontend).

검증·성능 분석 관점에서 이 구조를 모르면, "왜 이 워크로드에서 코어가 느린가" 를 단순히 "주파수가 낮아서" 로 오진하거나, OoO 코어의 retirement 순서와 execution 순서를 혼동해 잘못된 기대값을 만들게 됩니다.

---

## 2. Intuition — 주방 라인과 주문 순서

:::tip[💡 한 줄 비유]
**OoO 코어** ≈ **여러 화구를 둔 주방**.<br>
**Frontend** 는 주문을 받아 재료를 손질해 넘기는 홀(BPU 가 "다음 주문은 아마 이것" 이라 미리 예측). **Backend** 는 재료가 준비된 요리부터 순서 없이 먼저 익히되(OoO execute), **손님에게 내보낼 때(retire)는 반드시 주문 순서대로**(in-order) — 그래야 손님(OS)이 "어느 요리가 사고였나" 를 정확히 안다(precise exception). **LSU** 는 냉장고를 드나드는 동선 — 가장 붐비고 가장 자주 막히는 곳.
:::
### 한 장 그림 — Frontend → Backend → Retire

```d2
direction: right

BPU: "**BPU**\nTAGE-SC-L + BTB + RAS\n다음 PC 예측"
FTQ: "**FTQ**\nfetch target queue\n(BPU 가 앞서 달림)"
IC: "**I-cache + Decode**\nmicro-op crack\nN-wide"
REN: "**Rename**\nsRAT + free list\nWAR/WAW 제거"
IQ: "**Issue Queue**\nwakeup-select\n(OoO)"
EX: "**Execute**\nALU/AGU/FPU"
LSU: "**LSU**\nLDQ/STQ + STLF\n+ MSHR"
ROB: "**ROB**\nin-order retire\nprecise exception"

BPU -> FTQ -> IC -> REN -> IQ -> EX
IQ -> LSU
EX -> ROB
LSU -> ROB
```

### 왜 이 구조인가 — Design rationale

세 가지 요구의 교집합입니다.

1. **실행 unit 이 굶지 않게 명령을 끊김 없이 공급** → decoupled fetch + **FTQ**(Fetch Target Queue — 예측한 미래 fetch 주소를 쌓아 두는 큐) 로 **BPU**(Branch Prediction Unit — 다음에 실행할 명령 주소를 미리 맞히는 분기 예측기) 가 I-cache 보다 앞서 달려 miss 를 prefetch 로 은폐.
2. **가짜 의존(WAR/WAW — 같은 레지스터 이름을 재사용해서만 생기는, 실제 데이터 흐름과 무관한 거짓 의존)을 없애 ILP(Instruction-Level Parallelism — 서로 독립적인 명령을 동시에 실행해 얻는 병렬성)를 끌어내되 예외는 정확히** → register rename (가짜 의존 제거) + ROB (OoO 실행, in-order retire 로 precise exception 보장).
3. **메모리 명령의 가변 latency 와 ordering 을 흡수** → LSU 의 LDQ/STQ + STLF + memory disambiguation + MSHR (MLP).

---

## 3. 작은 예 — `add x1,x2,x3` 한 명령의 backend 여정

### 3.1 rename — 가짜 의존 제거

아키텍처 레지스터 32개(`X0~X30`)를 물리 레지스터 200~600+ 개로 매핑하면 WAR/WAW 가짜 의존이 사라집니다 (uarch/OoOBackend).

```
// add x1, x2, x3 의 rename
(1) src lookup:   src1 = sRAT[x2] → P12,  src2 = sRAT[x3] → P15
(2) dst 새 PRF 할당: new = freelist.pop() → P42
(3) sRAT 갱신:     sRAT[x1] = P42
(4) ROB entry 에 옛 매핑 기록: old_phys = (이전 x1 매핑) — retire 때 free
```

같은 cycle 에 여러 명령을 rename 할 때, 두 번째가 첫 번째의 dst 를 src 로 쓰면 (`add x1,...; sub x4,x1,x5`) sRAT 갱신 전에 lookup 하면 옛 값이 나옵니다. 이 **cross-RAW** 를 cycle 안에서 처리하는 회로가 wide rename 의 핵심이며, N-wide 면 N(N-1)/2 비교가 필요해 O(N²) 입니다.

### 3.2 두 개의 RAT — 복구를 위한 이중화

```d2
direction: right
SRAT: "**Speculative RAT**\n(front-end)\nrename 마다 갱신\nin-flight 매핑"
RRAT: "**Retirement RAT**\n(architectural)\nretire 시에만 갱신\n확정 상태"
SRAT -> RRAT: "retire 시 확정"
RRAT -> SRAT: "mispredict/exception 시\nrollback (복원)"
```

분기 예측이 틀리거나 exception 이 나면, speculative RAT 을 retirement RAT 으로 되돌립니다. 분기마다 checkpoint(snapshot)를 저장해 두면 1-cycle 에 복원 가능 — 모던 high-perf 코어 표준입니다 (uarch/OoOBackend).

### 3.3 issue → execute → retire

| 단계 | 무엇을 | 핵심 |
|------|--------|------|
| Dispatch | IQ + ROB + (메모리면)LDQ/STQ entry 동시 할당 | 하나라도 비면 dispatch stall |
| Wakeup | 끝난 명령의 dst tag broadcast → IQ 의 src tag 와 CAM 비교 → ready | tag broadcast O(N²) 가 frequency 1순위 critical path |
| Select | ready entry 중 N 개 골라 execution port 로 | priority encoder (oldest-first) |
| Execute | ALU/AGU/FPU 에서 실행, writeback to PRF | bypass network 로 back-to-back |
| Retire | ROB head 가 ①완료 ②non-speculative 일 때만 in-order commit | precise exception 의 핵심 보장 |

retire 가 **in-order** 라는 점이 핵심입니다. execute 는 순서 없이 하더라도, 손님에게 내보내는 순서는 program order 라야 OS handler 가 "정확히 어느 명령이 사고였는지" 를 알 수 있습니다.

---

## 4. 일반화 — frontend / 분기 예측 / backend 자원 / LSU

### 4.1 Decoupled Fetch 와 FTQ

고전 코어는 BPU 와 I-cache 가 lock-step 으로 동작해, I-cache miss 시 BPU 도 같이 멈췄습니다(fetch bubble). 모던 코어는 둘을 분리합니다 (uarch/Frontend).

```
Decoupled:
  BPU:  P1 P2 P3 P4 P5 P6 P7 P8   (계속 달림)
  FTQ:  target stack 에 쌓임
  I$:   F1 F2 -- -- -- F3 F4 F5   (FTQ 에서 꺼냄, miss 때 prefetch 발사)
  → BPU 가 I$ 보다 앞서 달려 miss 를 prefetch 로 은폐
```

FTQ 가 비면 frontend 가 starve 되므로, BPU 정확도가 frontend 의 진짜 throughput 을 결정합니다. 그래서 wide 코어일수록 BPU 에 트랜지스터를 쏟아붓습니다.

또한 fetch group 안에 **taken branch 한 개** 만 있어도 그 뒤 명령은 버려집니다. 8-wide fetch 라도 평균 effective fetch 는 4~6 — branch density 가 fetch IPC 를 깎습니다.

#### instruction prefetch 와 frontend 의 상호작용 — frontend bound 완화

데이터 prefetch(M-computer_architecture)처럼 _명령_ 도 prefetch 합니다. §1 에서 application 의 30~50% 가 Frontend Bound 라 했는데, 그 큰 원인 하나가 **I-cache miss** 입니다 — 코드가 커서 명령이 I-cache 에 없으면 fetch 가 멈춥니다. 이를 가리는 두 수단이 frontend 구조와 맞물립니다.

- **next-line prefetch**: 현재 fetch 하는 라인의 _다음 라인_ 을 미리 I-cache 로 가져옵니다 — 순차 코드(분기 적은 직선 구간)에서 효과적.
- **BTB-directed prefetch**: 단순 next-line 은 분기를 만나면 빗나갑니다. 그래서 **decoupled fetch + FTQ**(§4.1) 구조에서 BPU 가 I-cache 보다 _앞서 달려_ 예측한 미래 fetch 주소들이 FTQ 에 쌓이는데, 이 _예측된 미래 주소_ 를 보고 그 라인을 미리 prefetch 합니다 — 분기를 건너뛴 _타겟 라인_ 까지 선제적으로 가져옵니다. BPU 가 정확할수록 prefetch 도 정확해집니다.

핵심 인과: decoupled fetch 가 BPU 를 앞세우는 이유가 단지 "fetch bubble 은폐"만이 아니라, _FTQ 에 쌓인 미래 주소_ 가 곧 **I-cache miss 를 미리 채울 prefetch 힌트** 가 되기 때문입니다. BPU 정확도가 높으면 prefetch 가 적시에 정확한 라인을 끌어와 Frontend Bound 의 I-cache miss 성분을 크게 줄입니다. 그래서 wide 코어가 BPU 에 트랜지스터를 쏟는 것은 _방향 예측 정확도_ 와 _명령 prefetch 정확도_ 를 동시에 사는 투자입니다. 검증·성능에서 Frontend Bound 가 높은데 BPU MPKI 는 낮다면 I-cache miss(코드 크기·prefetch 미작동)를 의심합니다.

### 4.2 분기 예측 — 단순에서 TAGE 까지

| 기법 | 자원 | 대략 정확도 |
|------|------|-------------|
| 항상 taken | 0 bit | ~70% |
| Static (방향 기반) | 0 bit | ~85% |
| 2-bit 포화 (bimodal) | 2 bit × N | ~93% |
| 2-level (gshare) | PHT + GHR | ~95% |
| TAGE-SC-L (현대 코어) | 수십 KB tagged tables | ~98~99% |

2-bit 포화 카운터는 `strongly-NT → weakly-NT → weakly-T → strongly-T` 네 상태로, "한 번 실수로는 예측을 안 바꿔" 변덕 분기에 강합니다. 그 위에 **TAGE** 는 서로 다른 길이의 global history 로 색인되는 여러 tagged table 을 쌓아, tag match 된 가장 긴 history table 을 provider 로 선택합니다. 분기 결과가 PC 뿐 아니라 "직전에 어떤 분기들을 지나왔는지(history)" 에 의존하기 때문입니다 (uarch/BranchPredictor).

예측 대상별로 별도 구조가 있습니다: **Direction**(분기를 갈지 말지) = TAGE-SC-L, **Target(direct)**(고정 분기 목적지) = **BTB**(Branch Target Buffer — 분기 명령의 목적지 주소를 캐싱해 미리 알려 주는 표) 계층(μBTB/L1/L2), **Target(indirect)**(간접 분기 목적지) = ITTAGE (가상 함수/switch), **Return**(함수 복귀 주소) = RAS (Return Address Stack — call 시 push, ret 시 pop 하는 LIFO).

:::caution[왜 99% 도 부족한가]
분기는 5~7 명령마다 하나. 1% 틀려도 파이프라인 flush 한 번이 15~20 cycle. 1000 명령 중 분기 150개 → 예측 실패 1.5개 → 30 cycle 손해. 0.1%p 차이가 IPC 수 % 를 가릅니다.
:::

### 4.2b micro-op fusion / macro-op fusion — crack 의 반대 방향

§1·M01 에서 본 micro-op **crack**(복잡 명령 하나 → 여러 micro-op)이 _분해_ 라면, 그 반대 방향인 **fusion**(인접한 명령 _둘 이상_ → 하나의 내부 연산)도 frontend 가 합니다. 목적은 동일 — _backend 가 처리할 연산 개수를 줄여_ 같은 자원으로 effective IPC 를 높이는 것입니다.

대표 예가 **compare-and-branch fusion** 입니다. `cmp` 다음에 그 결과로 분기하는 `b.cond` 가 _거의 항상 짝_ 으로 나타나는데(루프 조건 등), frontend 가 이 둘을 인식해 _하나의 내부 micro-op_ 으로 합칩니다. 그러면 ROB·IQ·실행 포트에서 두 칸이 아니라 한 칸만 차지하고, 한 번의 issue/execute 로 비교+분기가 끝나, _자원 점유와 실행 슬롯이 절반_ 이 됩니다. 8-wide 라고 광고해도 명령마다 한 슬롯씩 쓰면 금세 자원이 차지만, 자주 등장하는 쌍을 fusion 하면 _같은 width 로 더 많은 아키텍처 명령_ 을 소화합니다 — 그래서 광고된 width 와 _실측 effective IPC_ 사이에 fusion 이 또 하나의 변수가 됩니다.

핵심: crack 과 fusion 은 _반대 방향이지만 같은 목표_(backend 효율)를 위한 frontend 변환이며, "아키텍처 명령 수 = 내부 연산 수"라는 가정은 양쪽 모두 때문에 깨집니다(M01 의 micro-op crack 오해 방지와 짝). 성능 모델링에서 명령 수만으로 backend 압력을 추정하면 fusion 으로 줄어든 만큼 과대평가합니다.

### 4.3 Backend 자원 — 가장 작은 게 IPC 결정

uarch/OoOBackend, LoadStoreUnit 의 실측 비교입니다.

| 코어 | Rename | INT PRF | ROB | IQ | LDQ | STQ | L1D MSHR |
|------|--------|---------|-----|-----|-----|-----|----------|
| `Cortex-A710` | 5 | ~220 | ~160 | ~50 | ~60 | ~36 | ~16 |
| `Cortex-X2` | 8 | ~250 | ~288 | ~70 | ~90 | ~70 | ~24 |
| `Neoverse V2` | 8 | ~330 | ~320 | ~80+ | ~90+ | ~70+ | ~28 |
| `Apple Firestorm` | 8 | ~354 | ~630 | 큼 | ~130 | ~90+ | ~30+ |

핵심: **PRF 가 ROB 보다 먼저 fill 되는 경우가 흔합니다.** 그래서 ROB 만 키워도 IPC 가 안 오르고, backend 의 IPC 는 "가장 먼저 차는 자원" 이 결정합니다. wakeup-select 의 tag broadcast 가 O(entries×ports) 라 IQ 는 ~80 entry 부근이 실용 한계입니다.

#### Issue Queue 구조 — unified 통합형 vs distributed 분산형

위에서 IQ 를 단일체로 적었지만, _그 IQ 를 어떻게 배치하느냐_ 가 자원표 해석에 직접 영향을 줍니다. 두 극단이 있습니다.

- **Unified(통합형) RS**: 모든 실행 포트가 _하나의 큰 issue queue_ 를 공유합니다. 어떤 명령이든 어느 포트로든 갈 수 있어 _entry 활용이 유연_ 합니다 — 한 종류 명령이 몰려도 빈 entry 가 있으면 다 받습니다. 대가는 비용: 통합 IQ 는 _모든 포트의 wakeup tag_ 를 _모든 entry_ 가 비교해야 해 broadcast/select 회로가 커지고, entry 를 늘리면 wakeup latency 가 빠르게 증가해 주파수를 압박합니다.
- **Distributed(분산형) RS**: 포트(또는 포트 그룹)마다 _작은 별도 IQ_ 를 둡니다. 각 IQ 가 작아 wakeup-select 회로가 가벼워 _주파수에 유리_ 합니다. 대가는 경직성: 한 IQ 가 꽉 차면 다른 IQ 에 빈 자리가 있어도 그쪽 종류 명령을 dispatch 못 해 _entry 가 놀 수_ 있습니다(불균형 stall).

이 trade-off — _통합=유연하나 wakeup 비용↑, 분산=싸나 불균형 위험_ — 가 §4.3 자원표를 읽을 때 중요합니다. 같은 "IQ ~80" 이라도 그것이 한 덩어리인지 포트별로 쪼개진 합인지에 따라 _실제로 쓸 수 있는 깊이_ 가 다릅니다. 분산형은 명령 mix 가 한쪽으로 치우치면 표상 entry 수보다 일찍 막히고, 통합형은 표 수치를 거의 다 쓰지만 그 수치를 키우기가 회로상 더 어렵습니다. 그래서 "IQ 가 binding 인데 entry 는 남아 보인다"면 분산형의 _포트별 불균형_ 을 의심해야 합니다.

### 4.4 LSU — 가장 복잡한 backend block

**LSU**(Load/Store Unit — 메모리 접근 명령을 전담 처리하는 실행 유닛)는 주소 계산(**AGU**, Address Generation Unit — 메모리 접근 주소를 계산하는 회로) + TLB lookup + cache access + store-to-load forwarding + memory ordering + miss tracking 을 한 파이프에서 처리합니다. SPEC 등 일반 워크로드 stall 의 30~50% 가 메모리이므로 **LSU 가 곧 IPC** 입니다 (uarch/LoadStoreUnit).

- **Store-to-Load Forwarding (STLF)**: 같은 주소를 직전 store 했다가 곧 load 하는 패턴에서, 메모리까지 안 가고 STQ 에서 LDQ 로 직접 전달. 정렬·크기가 일치해야 forward 가능, partial overlap/misalignment 면 replay (값비쌈). _왜_ partial overlap 이 forward 불가인지는 아래에서 자세히 봅니다.
- **Memory Disambiguation**: 앞선 store 의 주소가 미정인데도 load 를 먼저 speculative 실행. 실제 충돌은 ~5% 미만이라 평균 이득. store 주소 결정 시 LDQ 를 CAM 검색해 충돌하면 squash+replay.
- **MSHR (Miss Status Handling Register)**: L1 miss 가 outstanding 인 동안 metadata 보관. 같은 라인의 secondary miss 를 합쳐 fill 한 번으로 다수 load service — **MLP (Memory-Level Parallelism)** 의 핵심. MSHR 가 차면 후속 load 가 모두 stall.

ARM 의 weak memory model 은 LSU 가 _다른 코어의 observation_ 까지 추적해야 합니다 — load 가 한 시점에 OK 였는데 다른 코어 store 가 도착하며 ordering 위반이면 replay. (x86 TSO 는 store→load reorder 만 허용하지만 ARM 은 load→load, load→store 까지 reorder 하므로 LSU 가 한 단계 더 추적.) 메모리 모델 자체는 [M04](../04_memory_model_barriers/) 를, coherence 프로토콜은 [Cache Coherence 토픽](../../cache_coherence/) 을 참조하세요.

---

## 5. 디테일 — wakeup-select / mispredict recovery / big.LITTLE

### 5.1 Wakeup-Select 회로 — frequency 의 1순위 병목

한 명령이 끝나면 그 dst tag 를 broadcast 하고, IQ 의 모든 src tag 와 CAM 비교해 match 된 entry 의 ready bit 를 세웁니다. 다음 cycle 에 ready entry 중 N 개를 priority encoder 로 골라 issue 합니다 (uarch/OoOBackend).

```
비용:  CAM lookup = entries × tag-bits  (broadcast)
       Select     = priority encoder log(entries)
       → IQ entry 를 늘리면 broadcast latency 증가 → frequency 강제 하락
```

load 의 latency 가 가변(L1 hit 4 cycle, L2 12, miss …)이라 IQ 는 L1 hit 가정으로 dependent 명령을 미리 wake 하고, miss 면 squash+replay 합니다(back-to-back load-use replay).

### 5.1b STLF 의 정렬 조건 — 왜 partial overlap 은 forward 불가인가

§4.4 에서 STLF 가 "정렬·크기 일치 시에만 forward"라고 했는데, _그 하드웨어적 이유_ 가 store buffer 의 구조에 있습니다. STQ 엔트리는 store 의 (주소, 데이터, 크기)를 보관하지만, 이 데이터를 _임의의 바이트 경계로 잘라 재조합_ 하는 능력은 없습니다(또는 매우 제한적입니다). 즉 store buffer 는 **byte-granular merge** 를 빠르게 못 합니다 — load 가 원하는 바이트들을 _하나의 store 엔트리에서 그대로_ 꺼낼 수 있을 때만 한 사이클에 forward 가 성립합니다.

그래서 세 경우로 갈립니다.

- **완전 포함 + 정렬 일치**: load 가 원하는 모든 바이트가 _하나의 직전 store_ 안에 정렬되어 들어 있으면, 그 엔트리에서 곧장 forward — 빠름.
- **partial overlap**: load 범위의 _일부_ 만 직전 store 와 겹치고 _나머지는 메모리(또는 더 이전 store)_ 에서 와야 하면, 두 출처의 바이트를 _합쳐야_ 하는데 store buffer 가 이 merge 를 빠른 경로로 못 합니다.
- **misalignment / 크기 불일치**: 경계가 어긋나 바이트 추출 자체가 단순 슬라이스로 안 되면 마찬가지로 실패.

forward 가 안 되면 **store-to-load forwarding stall / replay** 가 발생합니다 — load 가 store 가 메모리에 _drain 될 때까지 기다렸다가_ 다시 실행하거나(여러 사이클), merge 를 위한 느린 경로를 타야 해 비용이 큽니다. 이것이 "구조체 일부 필드를 좁게 store 한 뒤 더 넓게 load"하거나 _misaligned 접근_ 이 성능을 깎는 이유입니다. 컴파일러·코드가 store 와 그 직후 load 의 _크기·정렬을 맞추면_ STLF 가 성립해 빠릅니다 — 검증·성능에서 "store-then-load 패턴이 유독 느림"이면 partial overlap/misalignment 로 STLF 가 replay 되는지 봐야 합니다(§6 체크리스트).

### 5.2 Mispredict Recovery 절차

```
mispredicted branch B 가 EX 에서 wrong 확정:
  ① ROB:    B 이후 모든 entry invalidate
  ② IQ:     B 이후 모든 entry flush
  ③ LDQ/STQ: B 이후 entry flush
  ④ sRAT:   checkpoint (B snapshot) 으로 복원
  ⑤ free list: 회수
  ⑥ frontend redirect → 올바른 PC 부터 re-fetch
  → Penalty = pipeline depth + recovery, 보통 12 ~ 20 cycle
```

### 5.3 PRF-based vs ROB-based

모던 wide 코어(Intel Sandy Bridge+, ARM, Apple)는 **PRF-based** 입니다 — 모든 결과는 PRF 에 있고 ROB 는 metadata 만 보관. 옛 P6~Nehalem 의 ROB-based (ROB entry 가 결과 저장, retire 시 ARF 로 copy) 와 대비됩니다 (uarch/OoOBackend).

### 5.4 big.LITTLE / DynamIQ (DSU)

고성능 + 저전력 코어를 혼합합니다. DynamIQ Shared Unit (DSU) 는 같은 클러스터 안에서 이종 코어를 섞고 L3/SLC 를 공유합니다 (arm/Cores).

```
┌────────── DynamIQ Shared Unit (DSU) ──────────┐
│         L3 / SLC, snoop filter, ACP           │
├──────┬──────┬──────┬──────┬──────┬────────────┤
│ X3   │ A715 │ A715 │ A715 │ A510 │ A510 │ ...  │
│(big) │(mid) │(mid) │(mid) │(LIT) │(LIT) │      │
└──────┴──────┴──────┴──────┴──────┴────────────┘
```

코어 종류별 마이크로아키텍처 깊이가 다릅니다 — A510 은 in-order(efficiency), A710 은 OoO mid, X 시리즈는 very wide OoO(peak single-thread), Neoverse 는 서버/HPC(SVE2, 큰 TLB/BTB). 같은 ISA 라도 frontend/backend 자원 규모가 크게 다르므로, 워크로드를 어느 코어에 배치하느냐가 성능·전력을 가릅니다.

---

## 6. 흔한 오해 와 DV 디버그 체크리스트

### 흔한 오해

:::danger[❓ 오해 1 — 'OoO 코어는 결과도 순서 없이 내보낸다']
**실제**: execute 는 OoO 지만 **retire(commit)는 반드시 in-order** 입니다. ROB head 부터 program order 로 commit 해야 precise exception 이 보장됩니다. architectural state(레지스터/메모리)는 항상 순서대로 갱신됩니다.<br>
**왜 헷갈리는가**: "out-of-order" 라는 이름이 모든 단계에 적용된다고 오해해서.
:::
:::danger[❓ 오해 2 — 'issue width 가 같으면 IPC 도 비슷하다']
**실제**: PRF/ROB/IQ/LDQ/STQ/MSHR 중 가장 작은 자원이 IPC 를 옭아맵니다. 같은 8-wide 라도 ROB 630(Apple) vs 288(X2) 처럼 window 크기가 다르면 cache miss 흡수 능력이 달라 IPC 가 벌어집니다.<br>
**왜 헷갈리는가**: 광고되는 decode width 만 보고 backend window 를 안 봐서.
:::
:::danger[❓ 오해 3 — 'ROB 만 키우면 IPC 가 오른다']
**실제**: PRF 가 ROB 보다 먼저 fill 되는 경우가 흔합니다. ROB 에 빈 entry 가 있어도 할당할 물리 레지스터가 없으면 dispatch 가 멈춥니다. 자원을 균형 있게 키워야 합니다.<br>
**왜 헷갈리는가**: ROB 가 "window 크기" 의 대표로 자주 인용돼서.
:::
:::danger[❓ 오해 4 — 'fetch width 8 이면 매 cycle 8 명령을 가져온다']
**실제**: fetch group 안에 taken branch 한 개만 있어도 그 뒤는 버려집니다. branch density 때문에 effective fetch 는 평균 4~6. 그래서 BPU 정확도와 branch alignment 가 중요합니다.<br>
**왜 헷갈리는가**: nominal width 와 effective width 를 같게 봐서.
:::
:::danger[❓ 오해 5 — 'store 는 실행되면 즉시 메모리에 쓰인다']
**실제**: store 는 retire 전까지 메모리에 안 씁니다. STQ 가 (addr,data,size) 를 보관하다가 retire 후 store buffer → cache 로 drain 합니다. 그래서 직후 load 는 STLF 로 STQ 에서 forward 받습니다.<br>
**왜 헷갈리는가**: store 실행 = 메모리 쓰기 라고 단순화해서 — speculative store data 의 존재를 잊음.
:::
### DV 디버그 체크리스트 (이 모듈 내용으로 마주칠 첫 실패들)

| 증상 | 1차 의심 | 어디 보나 |
|------|----------|-----------|
| 기대값이 retire 순서와 안 맞음 | OoO execute 순서로 기대값을 만듦 | scoreboard 가 program-order(retire) 기준인지 |
| 특정 워크에서만 IPC 급락 | frontend bound (branch mispredict / I$ miss) | top-down 의 Frontend Bound, BPU MPKI |
| backend stall 인데 원인 불명 | PRF/IQ/ROB/LDQ/STQ/MSHR 중 binding 자원 | top-down 의 어느 자원이 먼저 차는지 |
| store-then-load 패턴이 느림 | STLF 실패 (misalign/partial) → replay | load/store 정렬·크기 일치 여부 |
| memory order violation 빈발 | speculative load 가 늦게 온 store 와 충돌 | LDQ CAM 검색, store-set predictor |
| cache miss 많은데 ILP 안 살아남 | MSHR depth 부족 (MLP 상한) | L1D MSHR entry 수 |
| 멀티코어에서만 load replay | ARM weak model — 다른 코어 store 도착 | LDQ 의 cross-core observation 추적 |

---

## 7. 핵심 정리 (Key Takeaways)

- **Frontend = BPU + FTQ + I-cache + Decode + micro-op crack**. decoupled fetch 로 BPU 가 앞서 달려 I$ miss 를 prefetch 로 은폐. taken branch 한 개로 fetch group 이 끊김.
- **분기 예측**: Direction=TAGE-SC-L, Target=BTB 계층, Indirect=ITTAGE, Return=RAS. 정확도 0.1%p 가 IPC 수 % 를 가른다.
- **OoO backend = Rename → Dispatch → IQ → Issue → Execute → ROB Retire**. rename 이 WAR/WAW 제거, ROB 가 OoO 실행 + **in-order retire** 로 precise exception 보장.
- **IPC 는 가장 작은 자원이 결정** — PRF 가 ROB 보다 먼저 차는 일이 흔하다. wakeup-select tag broadcast O(N²) 가 frequency 1순위 병목.
- **LSU 가 곧 IPC**: STLF(정렬 일치 필요), memory disambiguation(speculative load), MSHR(MLP 상한). ARM weak model 은 다른 코어 observation 까지 추적.
- **big.LITTLE/DSU**: 이종 코어를 한 클러스터에 섞고 L3 공유. 워크로드 배치가 성능/전력을 가른다.

:::caution[실무 주의점]
- scoreboard 의 기대값은 OoO execute 순서가 아니라 **retire(program) 순서** 로 만들어야 — 안 그러면 spurious mismatch.
- 성능 분석은 top-down 으로 "어느 자원이 binding 인가" 를 먼저 — issue width 만 보면 오진.
- store 의 architectural 효과는 retire 후 — store-then-load 검증 시 STLF 경로와 ordering 을 같이 본다.
:::
### 7.1 자가 점검

:::tip[🤔 Q1 — in-order retire 의 이유 (Bloom: Analyze)]
OoO 코어가 execute 는 순서 없이 하면서 retire 만 in-order 로 하는 이유는? 만약 retire 도 OoO 면 무슨 일이?
<details>
<summary>정답</summary>

retire 를 in-order 로 하는 이유는 **precise exception** 입니다. exception/interrupt 가 났을 때 OS handler 는 "fault 명령 이전은 모두 완료, 그 명령과 이후는 효과 0" 인 깨끗한 architectural state 를 봐야 재실행이 가능합니다. ROB head 부터 program order 로만 commit 하면 이 상태가 항상 정확합니다.

retire 도 OoO 면: 뒤 명령이 앞 명령보다 먼저 architectural state 를 갱신할 수 있어, exception 시점에 어떤 명령까지 끝났는지 불분명해집니다(imprecise). handler 가 어디부터 재시작할지 모르고, mispredict 시 rollback 할 깨끗한 경계도 사라집니다. 그래서 80~90년대 일부 imprecise CPU 는 디버깅·OS 가 어려워 대부분 폐기됐습니다.

</details>
:::
:::tip[🤔 Q2 — 자원 병목 진단 (Bloom: Evaluate)]
두 코어 A, B 가 모두 8-wide rename. A 는 ROB 288/PRF 250, B 는 ROB 630/PRF 354. cache miss 가 많은 워크로드에서 어느 쪽이 유리하며 그 이유는? ROB 만 288→630 으로 키운 가상의 코어 C(PRF 는 250 유지)는?
<details>
<summary>정답</summary>

**B 가 유리합니다.** cache miss 가 많으면 miss 가 해소되기를 기다리는 동안 그 뒤의 독립 명령을 계속 찾아 실행해야 IPC 가 유지됩니다. 이 "찾을 수 있는 범위" 가 instruction window 이고, ROB+PRF+LDQ 등이 함께 그 크기를 정합니다. B 는 ROB 630/PRF 354 로 window 가 훨씬 커서 long-latency miss 를 더 많이 흡수합니다(MLP↑).

**가상 코어 C (ROB 630, PRF 250)**: ROB 만 키워도 별 효과가 없을 가능성이 큽니다. **PRF 가 ROB 보다 먼저 fill 되기** 때문입니다 — 결과를 담을 물리 레지스터가 없으면 ROB 에 빈 entry 가 있어도 dispatch 가 멈춥니다. 즉 IPC 는 가장 작은 자원(여기선 PRF 250)이 옭아맵니다. 자원은 균형 있게 키워야 한다는 것이 핵심 교훈입니다.

</details>
:::
### 7.2 출처

**Internal (DV_SKOOL)**
- ARM AArch64 학습 소스 `uarch/Frontend` — decoupled fetch, FTQ, micro-op crack, fetch group, 실측 코어 비교
- `uarch/BranchPredictor` — 2-bit/gshare/TAGE-SC-L, BTB/ITTAGE/RAS, MPKI, 보안(BTI/CSV2)
- `uarch/OoOBackend` — rename(sRAT/RRAT), wakeup-select, PRF/ROB, mispredict recovery, 실측 자원 표
- `uarch/LoadStoreUnit` — AGU, LDQ/STQ, STLF, memory disambiguation, MSHR, ARM weak model
- `arm/Cores` — Cortex-A/Neoverse/Cortex-M 라인업, big.LITTLE/DynamIQ(DSU)
- precise exception: [M06](../06_caches_gic/), 메모리 모델: [M04](../04_memory_model_barriers/), 일반 OoO: [Computer Architecture 토픽](../../computer_architecture/)

**External**
- *Arm Cortex-X2 / Neoverse V2 Technical Reference Manual* — 파이프라인 자원 규모 (외부 표준 지식)
- Chips and Cheese, AnandTech 마이크로아키텍처 분석 — Apple Firestorm / Cortex 코어 window 크기 (외부 분석, 추론 기반 수치)

---

## 다음 모듈

→ [Module 08 — Assembly Patterns](../08_assembly_patterns/): AArch64 asm 관용구(branchless csel, tail call, vtable), NEON/SVE SIMD, C→asm 컴파일 패턴, 그리고 AAPCS64 함수 호출 규약.

[퀴즈 풀어보기 →](../quiz/07_microarchitecture_quiz/)
