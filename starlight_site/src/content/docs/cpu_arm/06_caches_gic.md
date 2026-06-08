---
title: "Module 06 — Caches & GIC (인터럽트)"
---

:::tip[학습 목표]
이 모듈을 마치면:

- **Differentiate** VIVT / VIPT / PIPT 인덱싱 방식과 ARM 의 Harvard L1 + Unified L2 캐시 계층을 구분할 수 있다.
- **Explain** PoU (Point of Unification) 와 PoC (Point of Coherency) 가 무엇이며, 왜 CMO (Cache Maintenance Operation) 가 필요한지 설명할 수 있다.
- **Apply** self-modifying code 와 DMA 송수신 상황에 맞는 CMO 시퀀스 (clean/invalidate + DSB) 를 적용할 수 있다.
- **Classify** GICv3 의 인터럽트를 SGI / PPI / SPI / LPI 로 INTID 범위에 따라 분류할 수 있다.
- **Trace** 인터럽트가 도착해 ISR 진입 → `ICC_IAR1` acknowledge → 처리 → `ICC_EOIR1` EOI 로 종료되기까지의 흐름을 추적할 수 있다.
- **Analyze** edge vs level triggered, maskable vs NMI 의 차이가 인터럽트 손실·폭풍 같은 버그로 어떻게 나타나는지 분석할 수 있다.
:::
:::note[사전 지식]
- [Module 01-05](../01_overview_isa/) — 특히 [M03 Exception Levels](../03_exception_levels/), [M05 MMU](../05_mmu_translation/)
- 캐시 일반 개념 (set/way/line, hit/miss) — 깊은 일반론은 [Computer Architecture 토픽](../../computer_architecture/)
- cache coherence 깊이는 [Cache Coherence 토픽](../../cache_coherence/) 참조
:::
---

## 1. Why care? — 캐시가 "메모리의 진실" 을 가린다

### 1.1 시나리오 — DMA 가 옛 데이터를 가져갔다

CPU 가 버퍼에 데이터를 써서 DMA 엔진에 넘겼는데, 장치가 읽어 간 값이 옛 데이터입니다. 코드는 분명히 버퍼에 새 값을 store 했는데도 말입니다.

원인은 **D-cache** 입니다. CPU 의 store 는 우선 D-cache 에만 들어가고 DRAM 에는 아직 반영되지 않을 수 있습니다 (write-back 캐시). DMA 엔진은 DRAM 을 직접 읽으므로 캐시 안의 새 값을 보지 못합니다. 반대로 DMA 가 버퍼를 채운 뒤 CPU 가 읽으면, CPU 의 D-cache 에 남은 _낡은 값_ 을 보게 됩니다 (arm/Cache).

이를 맞추는 것이 **CMO (Cache Maintenance Operation)** 입니다.

- DMA 로 버퍼를 넘기기 전: `DC CVAC` (**Clean** — dirty 라인을 DRAM 까지 밀어냄).
- DMA 가 버퍼를 채운 뒤: `DC IVAC` (**Invalidate** — 낡은 캐시 라인을 버리고 DRAM 에서 다시 읽게).

여기에 더해, 인터럽트 시나리오도 있습니다. 타이머가 만료되거나 NIC 가 패킷을 받으면 비동기 신호가 코어에 도착하는데, 이것을 받아 처리하는 표준 컨트롤러가 **GIC (Generic Interrupt Controller)** 입니다. 캐시 정합성을 놓치면 데이터가 silent 하게 어긋나고, 인터럽트 처리를 놓치면 시스템이 멈추거나 폭주합니다 — 둘 다 검증 환경에서 가장 잡기 어려운 부류의 버그입니다.

---

## 2. Intuition — 작업 책상과 비서실

:::tip[💡 한 줄 비유]
**D-cache** ≈ **내 책상 위 메모지**, **DRAM** ≈ **공용 캐비닛**.<br>
내가 메모지에 적은 내용(store)은 캐비닛에 옮겨 적기(clean) 전엔 남들(DMA, 다른 코어)이 못 봅니다. 남이 캐비닛을 갱신했어도 내 책상의 옛 메모지(stale line)를 버리고(invalidate) 다시 봐야 새 값을 압니다.<br>
**GIC** ≈ **회사 비서실** — 사방에서 오는 전화(인터럽트)를 우선순위대로 분류해 "지금 이 전화 받으세요" 라고 코어에 연결하고, 코어가 "처리 끝" (EOI) 을 알리면 다음 전화로 넘어갑니다.
:::
### 한 장 그림 — 캐시 정합성 지점과 GIC 구조

```d2
direction: right

CACHE: "Cache 정합성" {
  CPU: "CPU\nstore → D-cache"
  L2: "L2 (PoU)\nI/D 통합 지점"
  DRAM: "DRAM (PoC)\nDMA 도 보는 지점"
  CPU -> L2: "clean to PoU\n(self-modify)"
  L2 -> DRAM: "clean to PoC\n(DMA)"
}
GICBLK: "GICv3" {
  GICD: "Distributor (GICD)\nSPI 라우팅, priority"
  REDIST: "Redistributor\nPPI/SGI/LPI"
  CORE: "CPU iface\n(ICC_* regs)"
  GICD -> REDIST
  REDIST -> CORE: "deliver IRQ"
}
```

### 왜 이 디자인인가 — Design rationale

세 가지 요구의 교집합입니다.

1. **CPU 와 다른 관측자(DMA, 다른 코어, I-cache)가 같은 값을 봐야 한다** → coherency point (PoU/PoC) 개념 + 그 지점까지 데이터를 밀어내거나 버리는 CMO.
2. **인터럽트는 종류·우선순위·대상 코어가 다양하다** → 분류(SGI/PPI/SPI/LPI) + Distributor 가 라우팅 + Redistributor 가 코어별 전달.
3. **MSI 같은 대량 장치 인터럽트를 효율적으로 라우팅해야 한다** → GICv3 의 ITS (Interrupt Translation Service) 가 DeviceID+EventID 를 LPI 로 변환.

---

## 3. 작은 예 — self-modifying code 한 줄과 인터럽트 한 건

### 3.1 self-modifying code — I/D 캐시를 맞추기

JIT 컴파일러나 부트로더가 코드 영역을 다시 쓰면 문제가 생깁니다. `STR` 로 쓴 새 명령은 **D-cache** 에 들어가는데, CPU 가 명령을 fetch 할 때는 **I-cache** 를 봅니다. 둘은 물리적으로 분리돼 있어, 새 명령이 I-cache 에 반영되지 않으면 _옛 명령_ 이 실행됩니다 (arm/Cache).

```d2
direction: down
S1: "**① STR w_new, [x_addr]**\n새 명령이 D-cache 에 들어감"
S2: "**② DC CVAU, x_addr**\nD-cache clean → PoU 로 밀어 I-cache 가 볼 수 있게"
S3: "**③ DSB ISH**\nclean 완료 대기 (모든 코어)"
S4: "**④ IC IVAU, x_addr**\nI-cache invalidate → 옛 명령 버림"
S5: "**⑤ DSB ISH → ⑥ ISB**\ninvalidate 완료 + 파이프라인 flush"
S6: "**br x_addr**\n이제 새 코드로 안전하게 분기"
S1 -> S2 -> S3 -> S4 -> S5 -> S6
```

각 단계를 빼먹으면 (arm/Cache):

| 단계 | 빼먹으면? |
|------|-----------|
| ② `DC CVAU` | 새 명령이 D-cache 에만 머물러 I-cache 가 못 봄 |
| ③ `DSB ISH` | clean 진행 중에 다음 단계 시작 — race |
| ④ `IC IVAU` | I-cache 에 옛 명령이 남아 fetch 시 옛 값 |
| ⑤ `DSB ISH` | invalidate 진행 중 분기하면 다른 코어가 옛 명령 fetch |
| ⑥ `ISB` | 이미 파이프라인에 prefetch 된 옛 명령이 실행됨 |

:::note[PoU 와 PoC 의 구분]
**PoU (Point of Unification)** 는 한 코어의 I-cache 와 D-cache 가 같은 데이터를 보는 지점 — 보통 L2. 자기 수정 코드는 `DC CVAU` (to PoU) 면 충분합니다.<br>
**PoC (Point of Coherency)** 는 DMA 까지 포함한 모든 관측자가 동의하는 지점 — 보통 DRAM. 장치와 데이터를 주고받을 땐 `DC CVAC` (to PoC) 로 끝까지 밀어야 합니다.
:::

### 3.2 인터럽트 한 건 — ISR 진입과 종료

타이머 인터럽트가 도착했을 때 ISR 의 뼈대는 다음과 같습니다 (arm/GIC).

```asm
// IRQ vector 진입
  mrs   x0, ICC_IAR1_EL1    // ① Interrupt Acknowledge — 어떤 INTID 인지 읽음
  // ... dispatch & handle (타이머 reload, softirq 스케줄 등) ...
  msr   ICC_EOIR1_EL1, x0   // ② End Of Interrupt — 처리 완료 통보, priority drop
  eret                      // 복귀
```

`ICC_IAR1_EL1` 을 읽는 행위 자체가 인터럽트를 "acknowledge" 하며 어떤 INTID 가 발생했는지 알려 줍니다. 처리가 끝나면 `ICC_EOIR1_EL1` 에 그 INTID 를 써서 우선순위를 내리고 다음 인터럽트를 받을 수 있게 합니다.

---

## 4. 일반화 — 캐시 인덱싱 / coherency / GIC 분류

### 4.1 캐시 인덱싱 방식

캐시는 VA 로 index/tag 를 만드느냐 PA 로 만드느냐에 따라 세 가지가 있습니다 (arm/Cache).

| Type | Index | Tag | Trade-off |
|------|-------|-----|-----------|
| `VIVT` | VA | VA | 빠르지만 aliasing/homonym — 거의 안 씀 |
| `VIPT` | VA | PA | TLB lookup 과 병렬 가능 — 전형적 L1D/L1I |
| `PIPT` | PA | PA | aliasing 없음, TLB 먼저 — 전형적 L2/L3 |

L1 이 VIPT 인 이유는 TLB 변환과 cache index 를 _병렬_ 로 돌려 critical path 를 줄이기 위함입니다. page 크기 ≥ way 크기면 aliasing 이 없습니다.

### 4.2 Shareability 와 Coherency Point

- **Shareability domain**: Non-shareable (단일 코어) / Inner Shareable (같은 클러스터) / Outer Shareable (클러스터 간/시스템 전역). [M05 의 TLBI shareability](../05_mmu_translation/) 와 같은 개념 축입니다.
- **Coherency Point**: PoU (I/D 통합 지점, 보통 L2) / PoC (모든 마스터 동의 지점, 보통 DRAM).

CMO 니모닉은 **대상 · 동작 · 범위 · 기준점** 4요소의 약자입니다 (arm/Cache). 예: `DC CIVAC` = **D**ata cache, **C**lean+**I**nvalidate, by **VA**, to Po**C**. / `IC IVAU` = **I**-cache, **I**nvalidate, by **VA**, to Po**U**.

세 가지 기본 동작:

| 동작 | 하는 일 | 비유 |
|------|---------|------|
| **Invalidate** | 라인을 그냥 버림 (DRAM 반영 X) | "낡았을지 모르니 없는 걸로" |
| **Clean** (writeback) | dirty 라인을 DRAM 까지 밀어냄, 캐시엔 남김 | "쓴 내용을 저장소에 반영" |
| **Clean + Invalidate** | clean 후 invalidate | "저장하고 지운다" |

:::caution[CMO 는 DSB 로 마무리해야 한다]
CMO 명령은 발행만으로는 완료가 보장되지 않습니다. `DSB` 로 "실제 완료" 를 기다려야 후속 동작(DMA 킥, 코드 실행)이 안전합니다. 멀티코어면 `DSB ISH` (inner shareable, 모든 코어), 단일 코어면 `DSB NSH` 로 충분하지만 SMP 의 안전한 기본값은 ISH 입니다.
:::

### 4.3 GICv3 인터럽트 분류 — INTID 범위

GIC 는 인터럽트를 INTID 범위로 분류합니다 (arm/GIC).

| Kind | INTID range | 설명 |
|------|-------------|------|
| **SGI** (Software Generated) | `0 – 15` | inter-core IPI |
| **PPI** (Private Peripheral) | `16 – 31` | core-local (예: generic timer) |
| **SPI** (Shared Peripheral) | `32 – 1019` | 일반 주변장치 |
| **LPI** (Locality-specific) | `8192+` | MSI — ITS 경유 (v3+) |

GICv3 는 세 계층으로 구성됩니다: **Distributor (GICD)** 가 SPI 를 라우팅하고 priority 를 관리하며, 코어별 **Redistributor** 가 PPI/SGI/LPI config 를 담당하고, 각 코어의 **CPU interface** (`ICC_*` 시스템 레지스터) 가 실제 전달을 처리합니다. **ITS (Interrupt Translation Service)** 는 DeviceID + EventID 를 LPI INTID 로 변환해 대량 MSI 를 효율적으로 라우팅합니다.

### 4.4 Interrupt · Exception · Trap — 같은 HW 경로

"하던 일을 멈추고 다른 핸들러로 점프" 하는 메커니즘은 모두 같은 HW 경로를 쓰고 원인만 다릅니다 (general/InterruptBasics).

```
event diversion
  ├── sync  — 명령어가 원인 (재현 가능)
  │     ├── exception : page fault, divide-by-zero, illegal instruction
  │     └── trap      : svc / brk (의도 — syscall, breakpoint)
  └── async — 외부 신호 (재현 불가, race 의 원천)
        └── interrupt  : keyboard, timer, NIC, IPI
```

ARM 은 이 셋을 모두 "exception" 으로 묶고, x86 은 "interrupt + exception", RISC-V 는 "trap" 으로 통칭합니다 — HW 경로가 같기 때문입니다.

---

## 5. 디테일 — CMO / DMA 시퀀스 / 인터럽트 처리 9단계 / edge·level

### 5.1 자주 쓰는 CMO 명령

```asm
IC   IALLU              // 이 코어의 I-cache 전부 invalidate (to PoU)
IC   IVAU, Xt           // 주소 Xt 의 I-cache 라인만 invalidate
DC   IVAC, Xt           // Invalidate D by VA to PoC (DMA-in 후)
DC   CVAC, Xt           // Clean by VA to PoC (DMA-out 전)
DC   CIVAC, Xt          // Clean+Invalidate (양방향 DMA)
DC   CVAU, Xt           // Clean to PoU (self-modifying code)
DC   ZVA, Xt            // 캐시 라인 통째로 zero (memset 가속)
```

### 5.2 DMA 송수신 표준 시퀀스

- **DMA-out (CPU → 장치)**: 버퍼를 `DC CVAC` 로 clean → `DSB` → DMA 킥. CPU 가 쓴 데이터가 DRAM 까지 내려가야 장치가 봄.
- **DMA-in (장치 → CPU)**: 장치가 DRAM 을 채운 뒤 CPU 가 읽기 _전_ 에 `DC IVAC` 로 invalidate. CPU 의 stale 캐시 라인을 버려 DRAM 에서 다시 읽게.

C/C++ 에서는 self-modifying code 의 경우 `__builtin___clear_cache(begin, end)` (GCC/Clang) 한 줄이 5단계 시퀀스를 전부 생성합니다.

### 5.3 인터럽트 처리 공통 9단계

x86/ARM/RISC-V 모두 거의 같은 9단계를 거칩니다 (general/InterruptBasics).

```
1. Request 도착   — 외부 핀 / fault / trap
2. Mask 검사      — 지금 받을 수 있나? (NMI 제외 거부 가능)
3. Priority 비교  — 현재 work 보다 높은가? → preempt
4. Pipeline drain — OoO/speculative 명령 squash, precise state 정리
5. Context save   — PC/status 자동 저장 (ARM: ELR_EL1/SPSR_EL1)
6. Vector lookup  — 원인별 handler 주소, privilege 격상
7. Handler 실행   — syndrome (ESR_EL1) decode, 실제 처리
8. EOI ack        — controller 에 완료 통보 (GIC: ICC_EOIR1)
9. Context restore→ eret 로 복귀
```

ARM 은 step 5 에서 PC (`ELR_EL1`) 와 status (`SPSR_EL1`) 만 HW 가 자동 저장하고, 나머지 GP register 는 핸들러가 직접 push 합니다. 이 자동 저장 분량의 차이가 ISR 진입 비용의 큰 부분을 결정합니다.

### 5.4 Precise Exception 과 OoO

OoO 코어는 명령을 순서 없이 실행하지만, exception 이 발생하면 OS handler 가 "정확히 어느 명령에서 사고가 났는지" 를 알아야 합니다. 그래서 모든 모던 CPU 는 **precise exception** 을 보장합니다: fault 명령 _이전_ 은 모두 architecturally 완료, fault 명령 _자체와 이후_ 는 효과 0. 이것은 ROB (Reorder Buffer) 가 **OoO 실행 + in-order retire** 로 구현하며, 자세한 메커니즘은 [M07 Microarchitecture](../07_microarchitecture/) 에서 다룹니다.

### 5.5 Edge vs Level, Maskable vs NMI

인터럽트 신호는 두 모양으로 옵니다 (general/InterruptBasics).

- **Edge-triggered** — 0→1 같은 _전이_ 순간만 트리거. 펄스 한 번이면 되지만, controller 가 흡수 못 한 사이 두 번 발생하면 한 건으로 보임 (놓치면 끝). PCIe MSI/MSI-X 가 대표.
- **Level-triggered** — 신호선이 active level 인 _동안_ 계속 트리거. 놓치지 않지만, device 를 ack 해서 신호를 내리지 않으면 같은 IRQ 가 무한 발생 (**interrupt storm**). 전통 ISA IRQ, 일부 GIC SPI.

마스킹 측면에서, 대부분의 인터럽트는 OS 가 잠시 막을 수 있습니다 (ARM: `MSR DAIFSet`/`DAIFClr` 의 I bit). 그러나 **NMI** (watchdog, HW error/MCE, profiling, debug halt) 는 막을 수 없는 비상 신호이며, NMI handler 는 일반 lock 도 못 잡으므로 별도 stack 과 lock-free 자료구조만 써야 합니다.

---

## 6. 흔한 오해 와 DV 디버그 체크리스트

### 흔한 오해

:::danger[❓ 오해 1 — 'store 하면 DRAM 에 즉시 반영되니 DMA 가 본다']
**실제**: write-back D-cache 에서는 store 가 캐시에만 머물 수 있습니다. DMA-out 전에 `DC CVAC` 로 PoC 까지 clean 하지 않으면 장치가 옛 DRAM 값을 읽습니다.<br>
**왜 헷갈리는가**: "메모리에 썼다 = DRAM 에 있다" 는 단순 모델 때문에 — 캐시 계층을 생략한 사고.
:::
:::danger[❓ 오해 2 — 'self-modifying code 는 D-cache clean 만 하면 된다']
**실제**: `DC CVAU` 로 PoU 까지 clean 한 뒤 `IC IVAU` 로 I-cache 까지 invalidate + `ISB` 로 파이프라인 flush 가 필요합니다. clean 만 하면 I-cache 의 옛 명령이 남고, ISB 가 없으면 이미 prefetch 된 옛 명령이 실행됩니다.<br>
**왜 헷갈리는가**: I-cache 와 파이프라인 prefetch 라는 두 단계를 잊어서.
:::
:::danger[❓ 오해 3 — 'level-triggered 면 인터럽트를 놓칠 일이 없으니 안전하다']
**실제**: level 은 놓치진 않지만, handler 가 device 를 ack 해서 신호를 내리지 않으면 같은 IRQ 가 끝없이 재진입하는 interrupt storm 이 납니다. edge 는 반대로 놓침의 위험.<br>
**왜 헷갈리는가**: "안 놓침" 만 보고 "ack 안 하면 폭주" 라는 이면을 못 봐서.
:::
:::danger[❓ 오해 4 — 'ICC_IAR1 을 읽지 않아도 EOIR 만 쓰면 된다']
**실제**: `ICC_IAR1_EL1` read 가 인터럽트를 acknowledge 하고 INTID 를 알려 주는 동작입니다. 이걸 건너뛰면 어떤 INTID 인지 모르고, EOI 도 짝이 안 맞아 priority 가 꼬입니다.<br>
**왜 헷갈리는가**: IAR(acknowledge)와 EOIR(완료)이 짝이라는 것을 모르고 EOI 만 챙겨서.
:::
:::danger[❓ 오해 5 — 'NMI handler 도 일반 lock 으로 보호하면 된다']
**실제**: NMI 는 마스킹 불가이고 일반 인터럽트 핸들러가 잡고 있던 lock 을 또 잡으려 하면 deadlock 입니다. NMI 경로는 별도 stack, lock-free 자료구조, 즉시 panic/log 만 써야 합니다.<br>
**왜 헷갈리는가**: NMI 도 그냥 더 높은 우선순위의 인터럽트라고 생각해서.
:::
### DV 디버그 체크리스트 (이 모듈 내용으로 마주칠 첫 실패들)

| 증상 | 1차 의심 | 어디 보나 |
|------|----------|-----------|
| DMA 가 옛 데이터를 읽음 | DMA-out 전 `DC CVAC` (clean to PoC) 누락 | DMA 킥 직전 CMO + `DSB` 시퀀스 |
| DMA 후 CPU 가 옛 값을 읽음 | DMA-in 후 `DC IVAC` (invalidate) 누락 | 버퍼 읽기 전 invalidate |
| JIT/패치 코드가 옛 명령 실행 | self-modify 5단계 시퀀스 불완전 (`IC`/`ISB` 누락) | `DC CVAU → DSB → IC IVAU → DSB → ISB` |
| CMO 했는데도 race | `DSB` 로 완료 대기 안 함 | CMO 뒤 `DSB ISH` 존재 여부 |
| 인터럽트 무한 재진입 (storm) | level-triggered 인데 device ack 누락 | handler 가 device status clear 하는지 |
| 인터럽트 한 번만 받고 멈춤 | `ICC_EOIR1` 미발행 → priority 안 내려감 | ISR 의 IAR/EOIR 짝 |
| 간헐적 인터럽트 손실 | edge-triggered + shared line | trigger mode 설정, line 공유 여부 |
| ISR 진입 직후 register 깨짐 | step 5 의 SW context save 누락 | 핸들러의 GP register push/pop |

---

## 7. 핵심 정리 (Key Takeaways)

- **캐시 인덱싱**: L1 은 보통 VIPT (TLB 와 병렬), L2/L3 는 PIPT (aliasing 없음). ARM 은 Harvard L1 + Unified L2.
- **PoU vs PoC**: PoU 는 I/D 통합 지점(self-modify 용), PoC 는 DMA 까지 보는 지점(장치 IO 용). CMO 의 기준점을 가른다.
- **CMO + DSB**: Clean(밀어냄)/Invalidate(버림)/Clean+Invalidate. 발행 후 반드시 `DSB` 로 완료 대기.
- **GICv3 분류**: SGI(0-15, IPI) / PPI(16-31, core-local) / SPI(32-1019, peripheral) / LPI(8192+, MSI via ITS). Distributor → Redistributor → CPU interface(`ICC_*`).
- **ISR 흐름**: `ICC_IAR1` read 로 acknowledge → 처리 → `ICC_EOIR1` write 로 EOI. 둘은 짝.
- **edge vs level / maskable vs NMI**: edge 는 놓침 위험, level 은 storm 위험. NMI 는 마스킹 불가 — 별도 안전 경로.

:::caution[실무 주의점]
- DMA 검증 시 송수신 방향에 맞는 CMO (clean/invalidate) 와 `DSB` 순서를 TB 자극에 반드시 포함 — 빠지면 데이터가 silent 하게 어긋남.
- level-triggered 인터럽트 모델링 시 device ack(신호 내림)을 반드시 시뮬레이션 — 안 하면 storm.
- ISR 시퀀스에서 IAR/EOIR 짝을 검증 — EOI 누락은 후속 인터럽트 차단으로 hang.
:::
### 7.1 자가 점검

:::tip[🤔 Q1 — CMO 기준점 선택 (Bloom: Apply)]
JIT 컴파일러가 코드를 패치한 직후와, 네트워크 패킷을 DMA 로 보내기 직전 — 각각 어떤 CMO 기준점(PoU/PoC)을 써야 하나?
<details>
<summary>정답</summary>

- **JIT 패치 (self-modifying code)**: `DC CVAU` (Clean **to PoU**). I-cache 와 D-cache 가 통합되는 지점(L2)까지만 밀면 I-cache 가 새 명령을 볼 수 있습니다. 이어서 `IC IVAU` + `ISB` 로 마무리.
- **DMA-out (장치로 송신)**: `DC CVAC` (Clean **to PoC**). DMA 엔진은 DRAM 을 직접 읽으므로 데이터가 coherency 의 끝점(DRAM)까지 내려가야 합니다.

핵심: PoU 는 "내 I/D 캐시끼리 맞추기", PoC 는 "DMA·다른 마스터까지 맞추기". 잘못 고르면(예: DMA 인데 PoU 만 clean) 데이터가 L2 에 머물러 장치가 못 봅니다.

</details>
:::
:::tip[🤔 Q2 — 인터럽트 storm 진단 (Bloom: Analyze)]
한 SPI 인터럽트가 발생한 뒤 같은 ISR 이 끝없이 재진입한다. level-triggered 라고 가정할 때 가장 가능성 높은 원인과, edge-triggered 였다면 증상이 어떻게 달랐을지?
<details>
<summary>정답</summary>

**level-triggered 의 storm 원인**: handler 가 device 의 인터럽트 소스를 clear (status register 를 ack) 하지 않아 신호선이 active level 에 머물러 있습니다. GIC 입장에선 인터럽트가 계속 pending 이므로 EOI 후에도 즉시 다시 deliver 됩니다. 수정은 handler 안에서 device 를 ack 해 신호를 내리는 것.

**edge-triggered 였다면**: 전이 순간만 트리거하므로 storm 대신 _반대 문제_ 가 생깁니다 — handler 처리 중 같은 device 가 다시 펄스를 보냈는데 controller 가 흡수 못 한 사이면 그 두 번째 이벤트가 한 건으로 합쳐지거나 손실될 수 있습니다. 즉 level=storm 위험, edge=손실 위험. shared line 은 보통 level 로 설계하는 이유이기도 합니다.

</details>
:::
### 7.2 출처

**Internal (DV_SKOOL)**
- ARM AArch64 학습 소스 `arm/Cache` — 캐시 계층, VIVT/VIPT/PIPT, PoU/PoC, CMO 니모닉, self-modify 시퀀스
- `arm/GIC` — INTID 분류, GICv3 구조(GICD/Redist/CPU iface/ITS), `ICC_*` 레지스터, ISR 진입/종료
- `general/InterruptBasics` — interrupt/exception/trap, 9단계 처리, precise exception, edge/level, maskable/NMI
- coherence 깊이: [Cache Coherence 토픽](../../cache_coherence/), 캐시 일반: [Computer Architecture 토픽](../../computer_architecture/)

**External**
- *Arm Generic Interrupt Controller Architecture Specification* (GIC v3/v4) — INTID 범위, Distributor/Redistributor/ITS (외부 표준 지식)
- *Arm Architecture Reference Manual for A-profile* (ARM DDI 0487) — cache maintenance, `ICC_*` 시스템 레지스터 (외부 표준 지식)

---

## 다음 모듈

→ [Module 07 — Microarchitecture](../07_microarchitecture/): frontend(fetch/decode)와 분기 예측, rename/OoO backend/ROB, LSU(LDQ/STQ), 그리고 big.LITTLE/DSU 의 이종 코어 구조.

[퀴즈 풀어보기 →](../quiz/06_caches_gic_quiz/)
