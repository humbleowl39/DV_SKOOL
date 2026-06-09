---
title: "Module 04 — 메모리 모델 & 배리어"
---

:::tip[학습 목표]
이 모듈을 마치면:

- **Explain** ARM이 왜 weakly-ordered 메모리 모델을 택했고 x86(TSO)과 무엇이 다른지 설명할 수 있다.
- **Differentiate** DMB(관측 순서)·DSB(완료 대기)·ISB(파이프라인 재-fetch)를 보장 범위와 비용 기준으로 구분할 수 있다.
- **Apply** producer/consumer·MMIO·페이지테이블·자기수정코드 시퀀스에 알맞은 배리어와 옵션(ISH/SY/LD/ST)을 적용할 수 있다.
- **Compare** 양방향 DMB와 한 방향 acquire/release(LDAR/STLR)의 비용·의미 차이를 비교할 수 있다.
- **Analyze** LDXR/STXR(LL/SC) 루프와 LSE 단일 명령 atomic의 차이를 경쟁 상황에서 분석할 수 있다.
:::
:::note[사전 지식]
- [Module 02 — 레지스터 & PSTATE](../02_registers_pstate/) (`MSR`/`MRS`, 시스템 레지스터)
- [Module 03 — Exception Level](../03_exception_levels/) (`ERET`이 context sync를 포함하는 이유)
- 메모리 일관성(consistency)의 일반 개념 — [Cache Coherence](../../cache_coherence/)
:::
---

## 1. Why care? — x86에서 멀쩡하던 코드가 ARM에서 희귀하게 깨진다

### 1.1 시나리오 — producer/consumer 핸드오프가 쓰레기값을 읽다

두 코어가 공유 메모리로 데이터를 주고받는 lock-free 코드를 검증한다고 합시다. 생산자가 `data`를 쓰고 `ready=1`을 세팅하면, 소비자는 `ready`가 1이 될 때까지 기다렸다가 `data`를 읽습니다. x86에서는 완벽히 동작했는데, ARM에서 드물게 소비자가 쓰레기값을 읽습니다.

```
 Core 0 (생산자)              Core 1 (소비자)
   data = 42;                  while (ready == 0) {}
   ready = 1;                  print(data);   // ← 42? 아니면 쓰레기값?
```

ARM은 **weakly-ordered** 메모리 모델이라, Core 0의 두 store가 **순서가 뒤집혀** Core 1에 보일 수 있습니다 — `ready=1`이 먼저, `data=42`가 나중에 도달. 그래서 Core 1이 `ready`를 봤을 때 `data`는 아직 쓰레기입니다. x86은 TSO(Total Store Order)라 store-store 순서가 자동 보장되어 이 버그가 안 나지만, ARM에서는 **배리어**로 순서를 명시해야 합니다.

이 모듈은 검증에서 **가장 미묘하고 재현이 어려운 버그의 원천**을 다룹니다. weak memory의 재정렬은 대부분의 실행에서 우연히 in-order로 보이다가 특정 타이밍에서만 드러나, scoreboard mismatch가 간헐적으로 터집니다. ARM SMP·MMIO·페이지테이블이 끼인 DUT 검증에서 배리어 의미론은 필수 언어입니다.

---

## 2. Intuition — 교차로의 신호등, 그리고 한 장 그림

:::tip[💡 한 줄 비유]
**메모리 배리어** ≈ **교차로의 신호등**.<br>
평소엔 차(메모리 접근)들이 빈 길로 먼저 빠져나가도 됩니다(재정렬 = 성능). 하지만 _다른 도로의 차가 내 차의 순서를 봐야 하는_ 교차로에선 신호등(배리어)이 "이 차들이 먼저 지나간 뒤에 저 차들"이라고 순서를 강제합니다. **DMB**는 "관측 순서만" 정리하는 신호등, **DSB**는 "차가 실제로 교차로를 다 빠져나갈 때까지 대기", **ISB**는 "내 차선 자체를 새 지도로 다시 그림".
:::
### 한 장 그림 — weak ordering과 세 배리어

```d2
direction: down

WEAK: "**Weakly-Ordered**\n프로그램 순서 ≠ 관측 순서\nLoad/Store 재정렬 허용 (성능)"
NEED: "**순서가 중요한 순간**\n다른 코어/장치가 내 접근을 관측"
DMB: "**DMB** — Data Memory Barrier\n관측 순서만 보장\nCPU 멈추지 않음 (가벼움)\nSMP 공유 변수" {
  style.fill: "#e6f4ea"
}
DSB: "**DSB** — Data Sync Barrier\n이전 접근 완료까지 CPU 대기\n비쌈\nMMIO · CMO · TLBI 완료" {
  style.fill: "#fef7e0"
}
ISB: "**ISB** — Instruction Sync Barrier\n파이프라인 flush + 재-fetch\nSCTLR/TTBR/DAIF 변경 후" {
  style.fill: "#fce8e6"
}

WEAK -> NEED: "그대로 두면 버그"
NEED -> DMB: "관측 순서?"
NEED -> DSB: "완료 대기?"
NEED -> ISB: "실행 환경 변경?"
```

### 왜 이 디자인인가 — Design rationale

ARM이 weak memory를 택한 것은 성능을 위해서입니다. 단일 스레드에선 컴파일러·CPU가 "결과가 같아 보이도록" Load/Store를 자유롭게 재정렬·병합·추측 실행해도 문제가 없습니다 — 더 많은 최적화 여지 = 더 빠름. 문제는 **다른 코어가 내 쓰기를 관측할 때**뿐이므로, ARM은 "기본은 자유, 필요할 때만 배리어로 순서 강제"라는 전략을 씁니다.

#### 재정렬은 어디서 오나 — store buffer (메커니즘은 computer_architecture 로)

"재정렬을 허용한다"의 _물리적 근원_ 은 **store buffer** 입니다. 코어는 retire 된 store 를 곧바로 캐시에 쓰지 않고 store buffer 에 넣고 다음 명령으로 진행하는데, 그 store 가 buffer 에 머무는 동안 _뒤따르는 load_ 가 buffer 를 우회해 먼저 나가면, 다른 코어 관점에서 store→load 순서가 뒤집혀 보입니다. x86 의 TSO 는 이 _store buffer 한 개가 만드는 store→load reorder 만_ 허용하고, ARM 의 weak model 은 여기서 더 나아가 네 종류 reorder 를 모두 기본 허용합니다. 이 store-buffer 메커니즘과 "TSO 가 왜 store→load 만 허용하는가", "barrier/fence 가 정확히 무엇을 drain 하는가"의 전체 유도는 [Computer Architecture M04 — 메모리 계층](../../computer_architecture/04_memory_hierarchy/)에 정리되어 있으니, 여기서는 _ARM 이 그 위에서 무엇을 허용/금지하고 어떤 배리어로 제어하는가_ 에 집중합니다.

#### weak memory 가 실제로 허용하는 reordering 4종 — x86 TSO 와의 정확한 대비

"Load/Store 재정렬 허용"을 한 덩어리로 뭉뚱그리면 ARM 과 x86 의 차이를 못 잡습니다. 두 메모리 접근의 _프로그램 순서상 앞→뒤_ 조합은 네 가지뿐이고, 메모리 모델은 _각 조합을 재정렬해도 되는지_ 를 정합니다.

| 앞 → 뒤 (program order) | x86 TSO | ARM (weak, 기본) |
|---|---|---|
| Load → Load | 금지(보존) | **허용** |
| Load → Store | 금지(보존) | **허용** |
| Store → Store | 금지(보존) | **허용** |
| Store → Load | **허용** | **허용** |

표가 보여주는 핵심: **x86 TSO 는 단 한 종류(store→load)만** 재정렬을 허용하고 나머지 셋은 하드웨어가 자동 보존합니다 — store buffer 하나가 만드는 그 한 경우뿐입니다. **ARM 은 네 종류 모두** 기본 허용하므로, store→store 순서조차 보장되지 않아 §1 의 `data; ready` 핸드오프가 깨집니다. 그래서 x86 에서 store-store 순서에 _암묵적으로 의존_ 하던 lock-free 코드가 ARM 으로 오면 명시적 배리어 없이는 동작하지 않습니다. ARM 에서 특정 조합만 막고 싶으면 배리어 옵션(§4.3 의 `LD`/`ST` 접미)으로 _그 방향만_ 좁혀 비용을 아낍니다 — 이 정밀한 제어가 가능한 이유가 애초에 네 종류가 _독립적으로_ 열려 있기 때문입니다.

여기서 세 배리어가 갈리는 이유는 "무엇을 보장할 것인가"가 다르기 때문입니다. **관측 순서**만 필요하면 가벼운 DMB, **실제 완료**까지 필요하면(장치가 받았는지) 무거운 DSB, **실행 환경 자체가 바뀌면**(MMU on) 파이프라인을 다시 채우는 ISB. 보장의 강도와 비용이 정확히 비례합니다.

---

## 3. 작은 예 — producer/consumer를 배리어로 고치는 과정

§1의 깨진 핸드오프를 두 방법으로 고칩니다. 같은 문제에 DMB 방식과 acquire/release 방식이 어떻게 다른지를 한눈에 봅니다.

### 단계별 다이어그램

```d2
direction: down

PROB: "**문제**\nstore data; store ready\n→ 순서 뒤집혀 관측 가능"
DMBW: "**방법 A — DMB**\nproducer: str data; dmb ishst; str ready\nconsumer: ldr ready; dmb ishld; ldr data\n양방향 차단"
ACQ: "**방법 B — acquire/release**\nproducer: str data; stlr ready\nconsumer: ldar ready; ldr data\n한 방향만 차단 (더 가벼움)"
OK: "**보장**\nconsumer가 ready=1을 보면\ndata=42도 반드시 관측"

PROB -> DMBW
PROB -> ACQ
DMBW -> OK
ACQ -> OK
```

### 단계별 의미

| 방법 | producer | consumer | 비용 |
|------|----------|----------|------|
| A — DMB | `str data; dmb ishst; str ready` | `ldr ready; dmb ishld; ldr data` | 양방향 순서 강제 |
| B — LDAR/STLR | `str data; stlr ready` | `ldar ready; ldr data` | 한 방향만 — 더 빠름 |

### 실제 코드

```asm
// 방법 A — DMB ISH (양방향 배리어)
// Core 0 (producer)
    str   w1, [x_data]        // data = 42
    dmb   ishst               // the store above is observed before the store below
    mov   w2, #1
    str   w2, [x_ready]       // ready = 1
// Core 1 (consumer)
wait:
    ldr   w3, [x_ready]
    cbz   w3, wait
    dmb   ishld               // later loads must not move ahead of the ready read
    ldr   w4, [x_data]        // guaranteed 42 now
```

```asm
// 방법 B — LDAR / STLR (한 방향 배리어)
// Core 0 (producer)
    str   w1, [x_data]
    stlr  w2, [x_ready]       // release: prior stores observed before this store
// Core 1 (consumer)
wait:
    ldar  w3, [x_ready]       // acquire: later accesses observed after this load
    cbz   w3, wait
    ldr   w4, [x_data]        // guaranteed 42, no DMB needed
```

:::note[여기서 잡아야 할 두 가지]
**(1) `dmb ishst`는 store-store만, `dmb ishld`는 load 기준 이후 접근만 막는다.** 옵션(scope×direction)으로 차단 범위를 좁혀 성능을 확보 — full `dmb ish`를 남발하지 않습니다.<br>
**(2) LDAR/STLR은 한 방향만 막아 DMB보다 가볍다.** release(STLR)는 _이전_ 접근을, acquire(LDAR)는 _이후_ 접근을 — 각자 한 방향. C++의 `memory_order_acquire/release`가 이들로 매핑됩니다.
:::
---

## 4. 일반화 — 메모리 타입, 세 배리어, 옵션 다이얼

### 4.1 메모리 타입 — Normal vs Device

배리어를 논하기 전에, 메모리 영역이 어떤 타입으로 매핑됐는지가 먼저입니다.

| Type | 특성 | 용도 |
|------|------|------|
| `Normal` | Reorder / Merge / Speculate 가능, cacheable | 일반 RAM |
| `Device` | 순서 보장, cache 금지, speculate 제한 | MMIO (nGnRnE / nGnRE / nGRE / GRE) |

Device 타입의 접미(`nG` non-Gathering, `nR` non-Reordering, `nE` non-Early write ack)가 MMIO의 순서·병합 동작을 세밀하게 제어합니다. **MMIO를 Normal로 매핑하면** 배리어로도 막을 수 없는 재정렬·병합이 생기므로 반드시 Device로 매핑해야 합니다.

### 4.2 세 배리어 나란히

| | DMB | DSB | ISB |
|--|-----|-----|-----|
| 보장 | 메모리 접근 **관측 순서** | 메모리 접근 **완료** | 파이프라인 flush + 재-fetch |
| CPU 대기? | 아니오 (가벼움) | 예 (비쌈) | 예 (비쌈) |
| 주 용도 | SMP 공유 변수 순서 | MMIO, CMO, TLBI 완료 | SCTLR/TTBR/DAIF 변경 후, SMC 전 |
| 흔한 쌍 | 단독 또는 LDAR/STLR 대체 | + ISB 짝지어 | DSB 뒤에 따라옴 |

한 줄 결정 트리: **SMP 공유 변수 → DMB ISH(또는 LDAR/STLR), 장치/CMO/TLBI 완료 → DSB, 시스템 레지스터·코드 변경 → DSB + ISB.**

### 4.3 옵션 다이얼 — Scope × Direction

DMB와 DSB는 **범위(scope)** 와 **방향(direction)** 을 조합한 옵션을 받습니다.

| 옵션 | 의미 | 전형적 상황 |
|------|------|-------------|
| `SY` | Full system — 모든 관측자 | MMIO, 외부 장치, 보수적 기본값 |
| `ISH` | Inner shareable — 같은 CPU 클러스터 | 멀티코어 공유 메모리 (Linux SMP 기본) |
| `OSH` | Outer shareable | 여러 소켓 / 큰 시스템 |
| `NSH` | Non-shareable — 자기 코어만 | UP 또는 self-modifying 한정 |
| `LD` 접미 | Load-Load + Load-Store만 순서 | 읽기 기준 acquire 쪽 |
| `ST` 접미 | Store-Store만 순서 | 쓰기 기준 release 쪽 — 가장 가벼움 |

**Shareability domain**은 캐시 일관성을 보장할 관측자 집합을 동심원처럼 계층화한 것입니다. NSH(자기 코어) ⊂ ISH(같은 클러스터의 코어들, SMP Linux 기본) ⊂ OSH(멀티소켓) ⊂ SY(외부 장치·MMIO까지). 한 줄로 "SMP 코어들끼리면 ISH, 외부 장치 관여하면 SY"입니다. `LD/ST` 접미는 이와 직교하는 방향 제어입니다.

#### DMB 의 정확한 정의 — 두 access set 사이에 순서를 거는 모델

`LD`/`ST` 접미가 무엇을 좁히는지 정확히 이해하려면 DMB 의 _형식적 모델_ 을 봐야 합니다. DMB 는 명령 시점을 기준으로 메모리 접근을 **두 그룹**으로 나눕니다 — DMB _이전_ 의 접근들(**source/before access set**)과 _이후_ 의 접근들(**destination/after access set**). DMB 가 거는 보장은 "**before set 의 접근이 after set 의 접근보다 먼저 관측된다**"는 _두 집합 사이의 순서_ 입니다. 한 집합 _내부_ 의 순서는 건드리지 않습니다.

그러면 `LD`/`ST` 접미의 의미가 분명해집니다 — 이들은 _두 access set 의 구성을 좁혀_ 비용을 줄입니다.

- **`DMB ISHST`(ST 접미)**: before set 과 after set 을 _store 로 한정_ 합니다. 즉 "이전 store 들이 이후 store 들보다 먼저 관측" 만 보장(store→store). producer 의 release 쪽(`str data; dmb ishst; str ready`)에 알맞습니다 — load 는 이 배리어에 묶이지 않아 더 자유롭습니다.
- **`DMB ISHLD`(LD 접미)**: before set 을 _load 로_ 한정하되 after set 은 load·store 모두입니다. 즉 "이전 load 가 이후의 모든 접근보다 먼저 관측"(load→load, load→store). consumer 의 acquire 쪽(`ldr ready; dmb ishld; ldr data`)에 알맞습니다.
- **`DMB ISH`(접미 없음)**: before/after set 모두 load·store 전부 — 가장 강하지만 비쌈.

핵심: DMB 는 "모든 접근을 줄 세우는" 게 아니라 _before/after 두 집합 경계에 순서를 긋는_ 것이고, `LD`/`ST` 는 그 집합을 한쪽 방향으로 좁혀 _필요한 순서만_ 걸어 성능을 확보합니다. §3 의 producer/consumer 가 `ishst`/`ishld` 를 짝지어 쓴 이유가 이것 — 각자 자기 쪽에 필요한 access set 만 좁혔습니다.

#### multi-copy atomicity — 한 코어의 store 가 모두에게 동시에 보인다

weak memory 가 reorder 를 다 열어 두었다면, 더 미묘한 질문이 남습니다 — _서로 다른 코어들이 같은 store 들을 다른 순서로 볼 수 있는가?_ 초기 weak 모델에서는 이런 "store 가 코어마다 다른 시점에 도달"이 가능해 추론이 극도로 어려웠습니다. ARMv8 은 이를 **(other-)multi-copy-atomic** 으로 강화했습니다 — 한 코어의 store 가 _자기 자신 외의 모든 코어에게는 동시에_ 보이게 됩니다(즉 어떤 코어 A 의 store 가 코어 B 엔 보이고 코어 C 엔 아직 안 보이는 "부분 전파" 상태가 없음).

이 보장이 바뀌는 대표 사례가 **IRIW(Independent Reads of Independent Writes)** litmus 입니다 — 코어 0 이 X 에, 코어 1 이 Y 에 각각 store 하고, 코어 2 와 코어 3 이 X·Y 를 읽을 때, _multi-copy atomic 이 아니면_ 코어 2 는 "X 먼저, Y 나중"으로, 코어 3 은 "Y 먼저, X 나중"으로 _서로 모순된 순서_ 를 관측할 수 있습니다. ARMv8 의 multi-copy atomicity 는 이 모순된 관측을 _금지_ 합니다 — 모든 관측자가 store 들의 전파에 대해 일관된 그림을 봅니다(단, 같은 코어 내 reorder 는 여전히 별개 문제로 배리어가 필요). 이 강화 덕에 ARM 의 weak model 위에서 동시성 코드를 추론하기가 한결 수월해졌고, litmus 기반 모델 검증(M-cpu_dv 의 litmus test)에서 IRIW 류의 _허용/금지 결과_ 를 가르는 핵심 성질이 됩니다.

```asm
dmb  ishst    // SMP producer: store-store only, inner shareable
dmb  ishld    // SMP consumer: order later accesses against the load
dmb  ish      // full both-way, inner shareable
dsb  sy       // strongest — MMIO, debug
dsb  nshst    // self-modifying code: only this core's stores need to drain
```

### 4.4 acquire/release — 한 방향 배리어

```asm
LDAR  Wt, [Xn]    // Load-Acquire  — later accesses are observed after this load
STLR  Wt, [Xn]    // Store-Release — prior accesses are observed before this store
LDAPR Wt, [Xn]    // Load-AcquirePC (v8.3) — weaker acquire
```

DMB는 **양방향** 순서를 강제해 한쪽만 필요한데도 비용을 지불하지만, LDAR/STLR은 **한 방향**만 막아 CPU·컴파일러가 더 많이 최적화할 수 있습니다. 그래서 C++ `memory_order_acquire/release`의 native 매핑이며, 단순 핸드오프에선 DMB보다 권장됩니다.

---

## 5. 디테일 — 실전 시퀀스와 atomic

### 5.1 DSB — MMIO 쓰기 후 장치 동작 보장

```asm
// kick DMA: write start bit, then wait until the device sees it
    mov   w1, #1
    str   w1, [x_dma_ctrl]      // DMA_CTRL.START = 1
    dsb   sy                    // wait until the device has actually accepted the write
    bl    wait_for_dma_done
```

DMB는 순서만 정리할 뿐 **완료를 기다리지 않습니다**. 다음 명령이 장치의 응답을 기다려야 한다면 DSB가 필요합니다 — DMB만 쓰면 드물게 race가 나 디버깅 지옥이 됩니다.

### 5.2 DSB + TLBI — 페이지테이블 변경의 표준형

```asm
// after a page-table change
    str   x_new_pte, [x_pte]
    dsb   ishst                  // PTE write is visible in memory
    tlbi  vae1is, x_va            // inner shareable TLB invalidate
    dsb   ish                    // TLBI completes on all cores
    isb                          // pipeline re-fetches with the new mapping
```

이 시퀀스는 커널 페이지테이블 변경의 표준입니다. 한 명령이라도 빠뜨리면 stale TLB로 잘못된 페이지를 접근합니다. TLB·주소 번역 일반 원리는 [MMU](../../mmu/), ARM stage-1/2 세부는 M05에서 다룹니다.

### 5.3 ISB — 시스템 레지스터 변경 후

```asm
// enable MMU
    mrs   x0, sctlr_el1
    orr   x0, x0, #1            // SCTLR_EL1.M = 1 (MMU enable)
    msr   sctlr_el1, x0
    isb                          // required! later instructions fetched with MMU on
    // without ISB, the already-fetched next instruction runs with MMU off
```

`MSR`이 SCTLR을 바꾸는 시점에 **이미 파이프라인에 prefetch된 다음 명령**은 옛 SCTLR 상태로 디코드됩니다. ISB가 파이프라인을 비우고 새 컨텍스트로 재-fetch합니다. M03에서 본 `ERET`이 ISB를 포함하는 것과 같은 이유 — 실행 환경이 바뀌면 파이프라인을 다시 채워야 합니다.

### 5.4 자기 수정 코드 (Self-Modifying Code)

```asm
// JIT compiler, hot-patch, etc.
    str   w_new_insn, [x_code]    // write the new instruction into the code region
    dc    cvau, x_code            // clean data cache to PoU
    dsb   ish                     // clean complete
    ic    ivau, x_code            // invalidate instruction cache
    dsb   ish                     // invalidate complete
    isb                           // refresh this core's pipeline — new instruction safe to run
```

명령을 메모리에 쓰는 것만으로는 부족합니다. 데이터 캐시(쓴 명령이 머무는 곳)와 명령 캐시(CPU가 fetch하는 곳)가 분리되어 있어, 데이터 캐시를 PoU(Point of Unification)까지 clean하고 명령 캐시를 invalidate한 뒤 ISB로 파이프라인을 갱신해야 합니다. 캐시 계층(PoU/PoC)·CMO 세부는 M06에서 다룹니다.

### 5.5 Atomic — LL/SC vs LSE

```asm
// LL/SC · Legacy (ARMv8.0) — retry loop
loop:
    ldxr  w1, [x0]            // load-exclusive
    add   w1, w1, #1
    stxr  w2, w1, [x0]        // store-exclusive; w2=0 if succeeded
    cbnz  w2, loop            // retry if another core won the race

// LSE · Large System Extensions (ARMv8.1+) — single instruction
    mov   w1, #1
    ldadd w1, w2, [x0]        // atomic add, far more efficient under high contention
```

**LL/SC**(Load-Linked / Store-Conditional, ARM에선 LDXR/STXR)는 exclusive monitor로 "내가 읽은 뒤 아무도 안 건드렸으면 쓰기 성공"을 구현하는데, 경쟁이 심하면 STXR이 반복 실패해 루프를 돕니다. **LSE**(v8.1+)의 `LDADD`/`SWP`/`CAS` 같은 단일 명령 atomic은 인터커넥트 레벨에서 처리되어 high contention에서 훨씬 효율적입니다 — M01에서 본 ISA 버전 진화의 실제 이득입니다. atomic·coherence 프로토콜 깊이는 [Cache Coherence](../../cache_coherence/)에서 다룹니다.

#### exclusive monitor 는 무엇을 추적하나 — granule 과 spurious fail

LDXR/STXR 의 "아무도 안 건드렸으면 성공"을 가능하게 하는 **exclusive monitor** 의 동작을 한 단계 들어가 봅니다. monitor 는 LDXR 이 읽은 주소에 대해 "이 코어가 독점 예약(exclusive)을 걸었다"는 상태를 기록하고, STXR 시점에 그 예약이 _아직 유효한지_ 를 확인해 유효하면 쓰고 성공(0 반환), 무효면 안 쓰고 실패(1 반환)를 돌려줍니다. 핵심은 monitor 가 _정확한 한 주소_ 가 아니라 **exclusives reservation granule** — 보통 _캐시 라인 크기_ 단위의 영역 — 을 추적한다는 점입니다.

이 granule 단위 추적이 **spurious(가짜) fail** 을 낳습니다. STXR 이 실패하는 정당한 이유(다른 코어가 같은 위치를 정말로 갱신)뿐 아니라, _granule 만 겹치고 실제 데이터는 다른_ 경우에도 예약이 깨져 실패할 수 있습니다.

- **false sharing**: 다른 코어가 _같은 캐시 라인의 다른 변수_ 를 건드려도, granule 이 라인 단위라 예약이 무효화됩니다 — 내 변수는 멀쩡한데 STXR 이 실패.
- **context switch / 예외**: LDXR 과 STXR 사이에 컨텍스트 스위치나 예외가 끼면, 아키텍처가 예약을 _보수적으로 무효화_ 할 수 있어 STXR 이 실패합니다.
- **다른 코어의 단순 접근**: 같은 granule 에 대한 다른 코어의 접근도 예약을 깰 수 있습니다.

그래서 LDXR/STXR 은 _반드시 retry 루프_(§5.5 의 `cbnz w2, loop`)로 감싸야 합니다 — spurious fail 은 "버그"가 아니라 _정상_ 이며, 한 번 실패하면 처음부터 다시 시도하면 됩니다. 검증에서 STXR 이 가끔 실패하는 것을 버그로 오인하면 안 되고, 반대로 _retry 루프가 없는_ LDXR/STXR 이야말로 버그입니다. high contention 에서 이 retry 가 잦아 성능이 나빠지므로, 그때 LSE 단일 명령 atomic 이 이득을 줍니다.

### 5.6 컴파일러 배리어도 잊지 말 것

HW 배리어 명령을 써도 **컴파일러가 load/store를 위아래로 옮기면** 무용지물입니다. 인라인 어셈블리에서 `asm volatile("dmb ish" ::: "memory")`의 `"memory"` 클로버가 컴파일러에게 "이 지점에서 메모리 재정렬 금지"를 알리는 핵심입니다. HW 배리어와 컴파일러 배리어는 서로 다른 두 계층이며 둘 다 필요합니다.

---

## 6. 흔한 오해 와 DV 디버그 체크리스트

### 흔한 오해

:::danger[❓ 오해 1 — 'x86에서 돌던 lock-free 코드는 ARM에서도 안전하다']
**실제**: x86은 TSO라 store-store 순서가 자동 보장되지만, ARM은 weakly-ordered라 재정렬됩니다. x86에서 통과하던 lock-free 코드가 ARM에서 희귀하게 깨집니다. C11 `atomic_*`나 acquire/release를 기본으로.<br>
**왜 헷갈리는가**: 대부분의 실행에서 우연히 in-order로 보여서 "되는 것처럼" 착각.
:::
:::danger[❓ 오해 2 — 'MMIO 뒤엔 DMB만 쓰면 된다']
**실제**: DMB는 **관측 순서만**, 완료를 기다리지 않습니다. 장치가 실제로 쓰기를 받았는지 다음 명령이 의존하면 **DSB**가 필요합니다. DMB만 쓰면 race가 드물게 발생.<br>
**왜 헷갈리는가**: "배리어=순서=완료"로 세 개념을 뭉뚱그려서.
:::
:::danger[❓ 오해 3 — '시스템 레지스터 바꾸면 다음 명령은 즉시 새 상태로 실행된다']
**실제**: `MSR` 후 이미 fetch된 파이프라인의 명령은 **옛 상태**로 실행됩니다. `msr; isb`를 관용구로 써야 새 컨텍스트가 적용됩니다.<br>
**왜 헷갈리는가**: 명령이 순차 실행된다는 단순 모델 — 실제로는 파이프라인에 미리 fetch됨.
:::
:::danger[❓ 오해 4 — 'dsb sy를 쓰면 항상 안전하니 기본으로 쓰자']
**실제**: `dsb sy`는 가장 보수적이지만 가장 느립니다. SMP 공유라면 `ish`로 충분하고, 커널 핫패스에서 SY를 남발하면 성능이 크게 떨어집니다 — 범위를 좁혀야.<br>
**왜 헷갈리는가**: "강할수록 안전"이라는 직관이 비용을 무시.
:::
:::danger[❓ 오해 5 — 'HW 배리어만 쓰면 컴파일러는 알아서 따라온다']
**실제**: 컴파일러는 HW 배리어 명령을 모르는 채 load/store를 재배치할 수 있습니다. 인라인 asm의 `"memory"` 클로버나 `atomic`으로 컴파일러에게도 알려야 합니다.<br>
**왜 헷갈리는가**: HW 배리어와 컴파일러 배리어가 같은 것이라는 혼동 — 별개의 두 계층.
:::

### DV 디버그 체크리스트 (이 모듈 내용으로 마주칠 첫 함정들)

| 증상 | 1차 의심 | 어디 보나 |
|---|---|---|
| 간헐적 mismatch (대부분 통과, 드물게 실패) | weak memory 재정렬, 배리어 누락 | 공유 변수 핸드오프에 DMB/LDAR-STLR 유무 |
| x86에선 통과, ARM에서만 실패 | TSO 가정한 lock-free 코드 | store-store 순서 의존 지점 |
| MMIO 쓰기 후 장치가 안 받음 | DMB만 쓰고 DSB 누락 | MMIO 시퀀스의 `dsb` 유무 |
| MMU/TTBR 변경 후 옛 매핑으로 접근 | ISB 누락 (또는 TLBI 시퀀스 불완전) | `msr` 후 `isb`, TLBI 후 `dsb;isb` |
| 페이지테이블 바꿨는데 stale TLB | `str pte; dsb; tlbi; dsb; isb` 중 누락 | 5.2의 표준 시퀀스 대조 |
| 자기수정코드가 옛 명령 실행 | I-cache invalidate / ISB 누락 | 5.4의 DC/IC/DSB/ISB 시퀀스 |
| atomic 카운터가 가끔 틀림 | LL/SC 루프의 retry 누락 또는 배리어 부재 | `stxr` 결과 체크(`cbnz`), 또는 LSE로 |
| `dsb sy`로 성능 저하 | scope 과다 (SY를 ISH로 좁힐 수 있음) | 관측자 집합 — SMP면 ISH 충분 |

---

## 7. 핵심 정리 (Key Takeaways)

- **weakly-ordered**: ARM은 Load/Store를 재정렬·병합·추측 실행한다(성능). 다른 코어/장치가 관측할 때만 문제 → 배리어로 명시.
- **세 배리어**: DMB(관측 순서, 가벼움)·DSB(완료 대기, 비쌈)·ISB(파이프라인 재-fetch). 보장 강도와 비용이 비례.
- **결정 트리**: SMP 공유 변수 → DMB ISH 또는 LDAR/STLR, MMIO → DSB SY, 페이지테이블 → DSB ISH + ISB, 시스템 레지스터 → MSR + ISB.
- **acquire/release(LDAR/STLR)** 는 한 방향만 막아 양방향 DMB보다 가볍다 — C++ memory_order의 native 매핑.
- **옵션**: scope(NSH⊂ISH⊂OSH⊂SY) × direction(LD/ST). SMP면 ISH, 외부 장치면 SY로.
- **atomic**: LL/SC(LDXR/STXR) 루프 vs LSE 단일 명령. high contention에선 LSE가 효율적(v8.1+).

:::caution[실무 주의점]
- 간헐적 mismatch는 **weak memory 재정렬을 먼저 의심** — 대부분 통과하다 드물게 실패하는 패턴이 신호.
- MMIO는 **Device로 매핑** + 완료 의존이면 **DSB** (DMB로는 부족).
- 시스템 레지스터·페이지테이블·코드 변경 후 **ISB**를 관용구로.
- **HW 배리어와 컴파일러 배리어(`"memory"`)** 는 둘 다 필요 — 별개의 두 계층.
:::
### 7.1 자가 점검

:::tip[🤔 Q1 — 배리어 선택 (Bloom: Apply)]
다음 각 상황에 알맞은 배리어(+옵션)는? (a) SMP 두 코어가 공유 플래그로 데이터 핸드오프 (b) DMA 시작 비트를 MMIO에 쓰고 장치가 받았는지 의존 (c) `MSR`로 인터럽트 마스크를 바꾼 직후 다음 명령이 이를 봐야 함
<details>
<summary>정답</summary>

- **(a)** `dmb ish`(또는 더 가벼운 `dmb ishst`/`ishld` 페어, 혹은 LDAR/STLR). SMP 코어들끼리이므로 scope는 ISH로 충분.
- **(b)** `dsb sy`. MMIO는 외부 장치(관측자 = 전체 시스템)이고 _완료_ 까지 기다려야 하므로 DSB + SY. DMB는 순서만이라 부족.
- **(c)** `isb`. 시스템 레지스터 변경은 실행 환경 변경 → 이미 fetch된 명령을 옛 상태로 실행하지 않도록 파이프라인 재-fetch. `msr daifset, #2; isb`.
- 핵심 분류: 관측 순서(DMB) / 완료(DSB) / 실행 환경(ISB).

</details>
:::
:::tip[🤔 Q2 — DMB vs acquire/release (Bloom: Evaluate)]
producer/consumer 핸드오프에서 `dmb ish` 페어 대신 LDAR/STLR을 쓰면 무엇이 더 좋은가? 항상 더 좋은가?
<details>
<summary>정답</summary>

대부분의 단순 핸드오프에서 LDAR/STLR이 더 좋지만 만능은 아닙니다.
- **이점**: DMB는 _양방향_ 순서를 강제해 한쪽만 필요해도 비용 지불. STLR(release)은 _이전_ 접근만, LDAR(acquire)은 _이후_ 접근만 막아 → CPU·컴파일러가 더 많이 재정렬 가능 → 빠름. 또 한 명령에 메모리 접근 + 순서가 결합되어 코드도 짧음.
- **한계**: acquire/release는 _특정 주소 접근에 결합_ 된 단방향 배리어라, "임의의 두 메모리 그룹 사이 양방향 펜스"가 필요한 복잡한 패턴(예: 독립된 여러 변수에 대한 full fence)에는 DMB가 더 직접적. 또 release/acquire 의미가 코드 의도와 정확히 맞아야 함.
- **결론**: 단일 플래그 핸드오프 → LDAR/STLR 권장. 복잡한 다중 변수 ordering → DMB 또는 명시적 분석 필요.

</details>
:::
### 7.2 출처

**Internal**
- [Module 02 — 레지스터 & PSTATE](../02_registers_pstate/) — `MSR`/`MRS`와 ISB의 필요성
- [Module 03 — Exception Level](../03_exception_levels/) — `ERET`이 context sync를 포함하는 이유
- [Cache Coherence](../../cache_coherence/) — atomic primitive·MESI 등 일관성 프로토콜
- [MMU](../../mmu/) — TLBI·페이지테이블 일반 원리

**External**
- *Arm Architecture Reference Manual for A-profile (ARM ARM, DDI 0487)* §B2 (Memory model), §C6 (barrier instructions) — (외부 표준 지식)
- *Arm Cortex-A Series Programmer's Guide — Memory Ordering* — Arm Ltd.
- *C++ Standard — memory_order (acquire/release/seq_cst)* — ISO/IEC 14882 (acquire/release 매핑)
- *RISC-V Unprivileged Spec — RVWMO* — 대조용 weak memory 모델

---

## 다음 모듈

→ [Module 05 — MMU & 주소 번역](../05_mmu_translation/): 이 모듈의 TLBI/DSB 시퀀스가 무엇을 무효화하는지 — TTBR0/1, granule, 다단계 페이지 워크, stage-1/2 번역을 ARM AArch64 관점에서 본다.

[퀴즈 풀어보기 →](../quiz/04_memory_model_barriers_quiz/)
