---
title: "Module 05 — AArch64 MMU & 주소 변환"
---

:::tip[학습 목표]
이 모듈을 마치면:

- **Trace** 48-bit VA 한 개가 4KB granule 4-level (L0~L3) walk 를 거쳐 PA 로 풀리는 과정을 비트 슬라이싱과 함께 단계별로 추적할 수 있다.
- **Differentiate** `TTBR0_EL1` 과 `TTBR1_EL1` 의 역할, 그리고 stage-1 (OS) 과 stage-2 (hypervisor) 변환을 구분할 수 있다.
- **Explain** μTLB → main TLB → PWC → HW page walker 4단 계층이 왜 존재하는지, 각 단계의 miss 비용을 설명할 수 있다.
- **Apply** ASID / VMID 태깅이 context switch 시 TLB flush 를 어떻게 회피하는지 실제 PTE 의 `nG` 비트와 연결해 적용할 수 있다.
- **Analyze** 페이지 테이블 변경 후 `TLBI → DSB → ISB` 시퀀스에서 각 단계가 빠지면 어떤 stale-translation 버그가 생기는지 분석할 수 있다.
- **Evaluate** verification 환경에서 잘못된 변환·stale TLB 가 어떤 silent 한 mismatch 로 나타나는지 평가할 수 있다.
:::
:::note[사전 지식]
- [Module 01-04](../01_overview_isa/) — 특히 [M03 Exception Levels](../03_exception_levels/), [M04 Memory Model & Barriers](../04_memory_model_barriers/)
- 페이지 테이블의 일반 개념 (page, offset, level) — 깊은 일반론은 [MMU 토픽](../../mmu/) 참조
- 가상 메모리 기초 (VA / PA 분리, page fault)
:::
---

## 1. Why care? — 주소 한 비트가 어긋나면 디버깅 지옥이 열린다

### 1.1 시나리오 — 페이지 테이블을 바꿨는데 옛 매핑이 살아 있다

**MMU**(Memory Management Unit — 가상 주소(VA)를 물리 주소(PA)로 번역하고 접근 권한을 검사하는 하드웨어)가 이 모듈의 주인공입니다. 커널이 어떤 가상 주소의 매핑을 바꾸려고 PTE (page table entry, 가상→물리 한 페이지의 번역과 속성을 담은 항목) 를 새로 씁니다. 그리고 곧바로 그 주소에 접근하죠. 그런데 결과가 옛 PA 를 가리킵니다. 코드는 분명히 새 PTE 를 메모리에 store 했는데도 말입니다.

원인은 **TLB (Translation Lookaside Buffer)** 입니다. TLB 는 PTE 의 hot cache 인데, 페이지 테이블이 메모리에서 바뀌어도 그 사실을 _자동으로 추적하지 않습니다_. SW 가 명시적으로 `TLBI` (TLB Invalidate) 명령으로 옛 entry 를 버려 줘야 합니다. 게다가 store 가 메모리에 보이기 전에 invalidate 가 나가면 page walker 가 다시 옛 PTE 를 읽어 들이고, 다른 코어는 여전히 자기 TLB 의 옛 entry 로 동작합니다. 그래서 표준 시퀀스는 다음과 같이 다섯 단계로 못박혀 있습니다 (asm/MMU §②).

```asm
  str   x_new_pte, [x_pte]    // ① write new PTE
  dsb   ishst                 // ② PTE store가 메모리에 visible
  tlbi  vae1is, x_va          // ③ 모든 코어에서 그 VA invalidate
  dsb   ish                   // ④ invalidate 완료까지 대기
  isb                         // ⑤ 자기 파이프라인 re-fetch (새 매핑으로)
```

② 가 빠지면 page walker 가 옛 PTE 를 읽고, ④ 가 빠지면 다른 코어가 stale TLB 로 동작하며, ⑤ 가 빠지면 자기 파이프라인이 옛 매핑으로 prefetch 한 명령을 실행합니다. 한 단계만 빠져도 _간헐적_ 으로만 재현되는, 가장 잡기 어려운 부류의 버그가 됩니다.

이 메커니즘을 모르면 검증 환경에서 메모리 컨트롤러나 **IOMMU·SMMU**(I/O 장치에 주소 번역을 제공하는 MMU — ARM 의 System MMU) 를 검증할 때 "분명 PTE 는 맞는데 변환 결과가 틀린" 현상을 TB 버그로 오인하거나, 반대로 TB 가 barrier 없이 PTE 를 바꾸고 곧바로 비교해 spurious mismatch 를 만들게 됩니다.

---

## 2. Intuition — 4층 사전, 그리고 캐시된 단축 경로

:::tip[💡 한 줄 비유]
**Page table walk** ≈ **4권짜리 색인 사전을 차례로 펼치는 일**.<br>
VA 의 비트를 잘라 각 권(L0~L3)의 색인으로 쓰고, 한 권이 "다음 권 몇 페이지" 를 알려 주면 그쪽을 펼칩니다. 마지막 권(L3)이 진짜 물리 페이지를 줍니다. **TLB** 는 "방금 찾은 단어는 책상 위에 펼쳐 둔" 것 — 같은 VA 를 또 찾으면 사전을 다시 뒤지지 않습니다.
:::
### 한 장 그림 — VA 에서 PA 까지의 변환 계층

```d2
direction: right

CPU: "**Load/Store/Fetch**\nVA 발생"
UTLB: "**μTLB**\n(per-port, FA CAM)\n1-cycle hit"
MTLB: "**Main TLB**\n(set-assoc SRAM)\n2~4 cycle"
PWC: "**Page Walk Cache**\n중간 레벨 PTE\n(L0/L1/L2)"
WALK: "**HW Page Walker**\n4-level walk\nD-cache 통해 PTE fetch"
PA: "**PA**\n+ attrs (AP, AttrIndx, AF...)"

CPU -> UTLB: "VA"
UTLB -> MTLB: "miss" { style.stroke-dash: 4 }
MTLB -> PWC: "miss" { style.stroke-dash: 4 }
PWC -> WALK: "miss" { style.stroke-dash: 4 }
UTLB -> PA: "hit"
WALK -> PA: "leaf PTE"
```

### 왜 이 구조인가 — Design rationale

세 가지 요구의 교집합입니다.

1. **모든 메모리 접근이 1-cycle 안에 변환돼야 한다** → load/store/fetch 마다 변환이 critical path 에 있으므로, 작고 빠른 **μTLB**(micro-TLB — 가장 가까운 1단계 번역 캐시)를 **LSU**(Load/Store Unit — 메모리 접근 명령을 처리하는 실행 유닛) 포트마다 두어 1-cycle hit 을 보장 (uarch/TlbPtw).
2. **miss 해도 페널티를 흡수해야 한다** → miss 시 main TLB → **PWC**(Page Walk Cache — 페이지 테이블 walk 중간 레벨 항목을 캐싱하는 구조) → walker 로 단계적 fallback. PWC 가 중간 레벨 PTE 를 캐시해 walk latency 를 절반 이하로 줄임.
3. **context switch 비용을 낮춰야 한다** → 모든 entry 에 ASID/VMID 를 태깅해, 프로세스/VM 전환 시 TLB 를 통째로 flush 하지 않아도 cross-context 매칭이 자동 차단.

---

## 3. 작은 예 — VA `0x0000_8000_0123_4567` 을 손으로 walk 하기

4KB granule, 48-bit VA 의 가장 표준적인 구성을 따라가 봅시다 (asm/MMU §⑥). VA 를 9-bit 씩 네 조각과 12-bit offset 으로 자릅니다.

### 단계별 다이어그램

```d2
direction: down

S0: "**VA = 0x0000_8000_0123_4567**\nL0=0x101(257) L1=0 L2=9 L3=0x34(52)\noffset=0x567"
S1: "**① L0 (PGD)**\nbase = TTBR0_EL1 & ~0xFFF\nL0_table[257] → L1 table base"
S2: "**② L1 (PUD)**\nL1_table[0] → L2 table base\n(여기서 1GB block 가능)"
S3: "**③ L2 (PMD)**\nL2_table[9] → L3 table base\n(여기서 2MB block 가능)"
S4: "**④ L3 (PTE)**\nL3_table[52] → leaf 4KB page descriptor"
S5: "**⑤ PA**\nPA = (leaf.PA[51:12] << 12) | VA[11:0]\n= page_base | 0x567"
S0 -> S1 -> S2 -> S3 -> S4 -> S5
```

### 단계별 의미

| Step | 무엇을 | 비트 | 핵심 |
|------|--------|------|------|
| ① | `VA[47:39]` → L0 index | 9-bit (257) | base 는 `TTBR0_EL1` (low VA) — kernel 이면 `TTBR1_EL1` |
| ② | `VA[38:30]` → L1 index | 9-bit (0) | descriptor `[1:0]=11` → table, `01` → 1GB block 이면 여기서 종료 |
| ③ | `VA[29:21]` → L2 index | 9-bit (9) | `01` → 2MB block 이면 여기서 종료 |
| ④ | `VA[20:12]` → L3 index | 9-bit (52) | L3 의 `11` → 4KB page (leaf) |
| ⑤ | leaf PA + offset | offset 12-bit | `VA[11:0]` 는 변환되지 않고 그대로 |

### Descriptor 형식 (stage-1, 4KB)

leaf 인지 next-level 인지는 descriptor 하위 2비트가 결정합니다 (arm/MMU).

```c
// bits[1:0]:
//   00  Invalid   → walk 중 만나면 translation fault
//   01  Block     (L1=1GB, L2=2MB) — large mapping
//   11  Table     (L0~L2) — points to next-level table
//   11  Page      (L3)    — points to 4KB page

// Lower attributes (bits[11:2]): AF, SH[1:0], AP[2:1], NS, AttrIndx[2:0]
// Upper attributes (bits[63:51]): XN, PXN, Contiguous, nG
```

주요 attribute 비트의 의미 (asm/MMU §⑦):

- **AF (Access Flag)** — 처음 접근 시 0, OS 가 set. AF=0 이면 trap → 접근 추적.
- **AP (Access Permissions)** — 2-bit 권한: `00` EL1 RW, `01` EL0/1 RW, `10` EL1 RO, `11` EL0/1 RO.
- **AttrIndx** — `MAIR_EL1` 의 8개 슬롯 중 어느 것을 쓸지 가리키는 3-bit 인덱스. 실제 cacheability/Device 속성은 MAIR 가 정의.
- **XN / PXN** — eXecute Never (EL0) / Privileged eXecute Never (EL1). 1 이면 그 권한에서 fetch 차단 → W^X 강제.
- **nG (not Global)** — 1 이면 ASID-tagged (유저 매핑), 0 이면 global (커널 매핑).

:::note[여기서 잡아야 할 두 가지]
**(1) walk 은 중간에 끝날 수 있다.** L1 에서 block descriptor (1GB), L2 에서 block (2MB) 을 만나면 더 내려가지 않습니다. huge page 가 이렇게 구현됩니다.<br>
**(2) offset 은 변환되지 않는다.** 4KB page 면 `VA[11:0]`, 2MB block 이면 `VA[20:0]` 이 그대로 PA 의 하위 비트가 됩니다. page 크기가 클수록 변환되지 않는 비트가 많아집니다.
:::

---

## 4. 일반화 — granule / 2-stage / TLB 계층

### 4.1 Translation Granule 과 레벨 수

granule (페이지 기본 크기) 선택에 따라 walk 레벨 수와 VA 범위가 달라집니다 (arm/MMU).

| Granule | Level 구조 | VA size |
|---------|-----------|---------|
| 4 KB | L0 / L1 / L2 / L3 (최대 4 레벨) | 48-bit (또는 52-bit w/ LPA) |
| 16 KB | L0 ~ L3 | 48-bit |
| 64 KB | L1 ~ L3 (3 레벨) | 48-bit (또는 52-bit) |

64KB granule 은 레벨이 하나 적어 walk 이 짧지만 내부 단편화가 커집니다. 4KB 가 가장 흔한 기본값입니다.

### 4.2 MMU 제어 레지스터

MMU 의 동작은 몇 개의 시스템 레지스터로 정해집니다 (arm/MMU).

```c
TTBR0_EL1   // Translation Table Base 0 — 보통 user space (low VA)
TTBR1_EL1   // Translation Table Base 1 — 보통 kernel space (high VA)
TCR_EL1     // Translation Control — granule, TxSZ, cacheability
MAIR_EL1    // Memory Attribute Indirection — AttrIndx → 실제 attribute 매핑
SCTLR_EL1   // System Control — M bit = MMU enable
```

VA 의 상위 비트가 0 쪽(low) 인지 1 쪽(high) 인지에 따라 `TTBR0` 와 `TTBR1` 중 어느 base 를 쓸지 HW 가 자동 선택합니다. 그래서 user/kernel 분리가 한 주소 공간 안에서 자연스럽게 됩니다.

#### TCR_EL1 의 TxSZ — VA 폭이 48-bit 고정이 아닌 이유

"48-bit VA"라고 했지만 이것은 _고정값이 아니라 설정값_ 입니다. `TCR_EL1` 의 **T0SZ**(TTBR0 영역)와 **T1SZ**(TTBR1 영역) 필드가 _각 영역의 VA 비트 폭_ 을 정합니다. 정의는 "VA = (64 − TxSZ) 비트"입니다 — 예를 들어 T0SZ=16 이면 low 영역이 48-bit(`64−16`), T0SZ=25 면 39-bit, T0SZ=12 면 (LPA2 등 지원 시) 52-bit VA 가 됩니다. 즉 _하나의 숫자_ 로 주소 공간 크기를 줄이거나 늘립니다.

이 설정값이 단지 범위만 정하는 게 아니라 **walk 의 시작 레벨까지 바꿉니다.** VA 가 좁으면(예: 39-bit) 상위 인덱스 비트가 줄어 _L0 을 건너뛰고 L1 부터_ walk 를 시작할 수 있어 walk 단계가 하나 짧아집니다 — 작은 주소 공간이면 페이지 테이블 깊이도 얕아져 TLB miss 비용이 줍니다. 반대로 52-bit 처럼 넓히면 더 깊은 walk 나 확장된 디스크립터가 필요합니다. 그래서 "왜 48-bit 고정이 아닌가"의 답은 _주소 공간 크기와 walk 깊이를 워크로드에 맞게 trade-off 하라고_ TxSZ 를 설정 가능하게 둔 것입니다 — 임베디드는 39-bit 로 얕게, 대용량 서버는 48/52-bit 로. 검증에서 VA 범위·walk 시작 레벨이 예상과 다르면 `TCR_EL1.T0SZ/T1SZ` 값부터 확인해야 합니다.

### 4.3 2-stage 변환 — 가상화

가상머신 환경에서는 변환이 두 단계로 늘어납니다 (arm/MMU, uarch/TlbPtw).

```
Guest VA → Stage 1 (Guest OS) → IPA → Stage 2 (Hypervisor) → PA
```

- **IPA (Intermediate Physical Address)** — Guest OS 가 자기 stage-1 walk 끝에 얻는 "물리 주소" 같은 것. 진짜 PA 가 아니라, hypervisor 의 stage-2 walk 를 거쳐야 실제 PA 가 됨. Guest 는 IPA 를 진짜 PA 로 믿고 동작.
- **VMID (Virtual Machine ID)** — VM 마다 hypervisor 가 부여하는 8/16-bit 식별자. stage-2 PTE/TLB 에 태깅돼 VM 격리. `VTTBR_EL2` 에 인코딩.

nested walk 은 비쌉니다. stage-1 의 매 PTE fetch 마다 그 IPA 를 PA 로 풀기 위한 stage-2 walk 가 추가돼, 최악의 경우 단일 stage 의 4 PTE fetch 가 4×5 = 24 PTE fetch 까지 부풀어 오릅니다 (uarch/TlbPtw). 그래서 가상화 환경에서는 PWC 가 사실상 필수입니다.

#### stage-1 과 stage-2 의 메모리 속성은 어떻게 결합되나

2-stage 변환에서 _주소_ 만 두 번 번역되는 게 아니라, **메모리 속성(memory type, cacheability, shareability 등)도 두 stage 가 각각 정하고 그것이 결합(combine)** 됩니다. stage-1 은 게스트 OS 가 PTE 로 정한 속성, stage-2 는 하이퍼바이저가 정한 속성이며, 최종 접근에 적용되는 속성은 둘을 합친 결과입니다.

결합 규칙의 핵심 원리는 **하이퍼바이저(stage-2)가 더 제한적인 쪽으로 override 할 수 있다**는 것입니다 — 즉 두 속성 중 _더 보수적_ 인 것이 이깁니다. 가장 중요한 사례: 게스트가 어떤 페이지를 _Normal(cacheable, reorderable)_ 로 매핑했더라도, 하이퍼바이저가 그 IPA 를 stage-2 에서 _Device_ 로 매핑하면 최종 접근은 **Device 로 취급**됩니다. 게스트는 자기가 일반 RAM 을 다룬다고 믿지만 실제로는 MMIO 같은 device 시맨틱(순서 보장·캐시 금지)이 강제되는 것입니다.

왜 이 방향(제한적인 쪽 우선)인가. 하이퍼바이저는 게스트를 _신뢰하지 않으면서_ 격리해야 합니다. 만약 게스트가 device 영역(실제로는 passthrough 된 장치 MMIO)을 Normal cacheable 로 매핑해 캐싱·재정렬하도록 둔다면, 장치 동작이 깨지거나 다른 게스트에 영향을 줄 수 있습니다. stage-2 가 _최종 속성을 더 강하게 좁힐 권한_ 을 가져야 하이퍼바이저가 "게스트가 무엇으로 매핑하든 이 영역은 Device 로"처럼 _안전한 하한_ 을 보장할 수 있습니다. 검증에서 "게스트는 Normal 로 매핑했는데 접근이 device 처럼 순서·캐시 동작이 다르다"면 버그가 아니라 stage-2 의 속성 override 가 작동한 것일 수 있으므로, stage-2 PTE 의 메모리 속성을 함께 봐야 합니다.

### 4.4 TLB 4단 계층과 miss 비용

uarch/TlbPtw 가 제시하는 latency breakdown 입니다.

| Scenario | Latency (cycle) | 비고 |
|----------|-----------------|------|
| μTLB hit | 0 (LSU 안에 hidden) | 1-cycle, fully-assoc CAM |
| L2 (main) TLB hit | ~3 ~ 6 | SRAM access + size match |
| PWC hit (leaf walk only) | ~10 ~ 20 | L1 D$ 에서 leaf PTE fetch |
| Full walk, PTE in L2$ | ~30 ~ 50 | 4 fetch, 일부 cache 외 |
| Full walk, PTE in DRAM | ~100 ~ 300 | 각 fetch 마다 DRAM access |
| Nested walk, PWC miss | ~300 ~ 1000+ | 최악 — DRAM 까지 24 fetch |

μTLB 가 fully-associative **CAM**(Content-Addressable Memory — 주소가 아니라 내용으로 모든 항목을 동시에 비교 검색하는 메모리) 인 이유는 **variable page size** 때문입니다. set-associative 는 set index 비트가 page size 에 따라 달라지는데, 4KB/16KB/64KB/2MB/1GB 를 동시에 지원하려면 모든 entry 를 동시 비교하는 CAM 이 필요합니다. 대신 작아야(~16~48 entry) 1-cycle 이 가능합니다.

---

## 5. 디테일 — walker / ASID / TLBI / AT

### 5.1 HW Page Walker 의 특성

main TLB miss 시 HW walker 가 4-level walk 을 수행합니다. 핵심 특성 네 가지 (uarch/TlbPtw):

- **Coherent walk** — walker 가 PTE 를 D-cache 를 통해 읽습니다. 일반 load 처럼 cache hierarchy 를 통과하므로 coherence 가 자동으로 보장됩니다 (ARM/x86 표준).
- **다중 in-flight** — 한 walk 이 메모리를 기다리는 동안 다른 walk 을 동시 진행 (보통 2~4 walker). wide OoO 에서 동시 TLB miss 처리에 필수.
- **HW Update (AF/DBM)** — ARMv8.1 부터 HW 가 PTE 의 access flag (AF) / dirty bit 를 자동 갱신. SW 개입 없이 atomic RMW.
- **Invalid PTE → Fault** — walk 도중 invalid descriptor 를 만나면 translation fault → exception (Data Abort / Instruction Abort). `FAR_EL1`/`ELR_EL1` 을 채우고 vector 로 분기.

### 5.2 Contiguous bit — 인접 엔트리를 한 TLB 엔트리로 합치기

descriptor 형식(§3)의 upper attribute 에 있던 **Contiguous** 비트의 동작을 풀면, TLB 압력을 줄이는 또 하나의 메커니즘이 보입니다. 보통 TLB 엔트리 하나는 페이지 하나(4KB granule 이면 4KB)를 매핑합니다. 그런데 OS 가 _주소·속성이 연속인 인접 페이지 묶음_(4KB granule 에서 보통 16개)을 만들고 각 PTE 의 Contiguous 비트를 세우면, 하드웨어에게 "이 16개는 연속이고 같은 속성"이라는 _힌트_ 를 줍니다.

이점은 **TLB coalescing** 입니다 — 하드웨어가 이 힌트를 활용해 16개 페이지를 _하나의 TLB 엔트리_ 로 합쳐 담을 수 있습니다. 같은 영역을 매핑하는 데 TLB 엔트리를 16개가 아니라 1개만 쓰므로, 한정된 TLB 용량으로 _16배 넓은 영역_ 을 커버해 TLB miss 가 줄어듭니다. huge page(2MB block)와 비슷한 효과를 내되, huge page 처럼 _정렬·크기 제약이 큰 하나의 큰 페이지_ 가 아니라 _일반 4KB 페이지 16개를 묶는_ 더 유연한 방식입니다(여전히 16-페이지 정렬·동일 속성 조건은 필요). 즉 Contiguous 비트는 "페이지 크기를 키우지 않고도 TLB reach 를 넓히는" 힌트이며, 큰 연속 버퍼(DMA 버퍼, 큰 배열)에서 TLB 압력 완화에 유용합니다. 검증에서 이 비트가 잘못 세팅되면(연속이 아닌데 Contiguous 표시) 하드웨어가 잘못 coalesce 해 변환 오류가 날 수 있으므로, 묶음의 연속성·정렬·속성 일치를 확인해야 합니다.

### 5.3 break-before-make — 살아있는 매핑을 바꿀 때의 규칙

§1 의 5단계 시퀀스는 _새 매핑을 추가_ 하는 경우였습니다. 더 까다로운 것은 **이미 살아 있는 매핑의 속성·크기·출력 주소를 바꾸는** 경우입니다. 이때 ARM 아키텍처는 **break-before-make(BBM)** 를 요구합니다 — 옛 매핑을 _먼저 invalid 로 바꾸고_(break), TLB invalidate 로 옛 엔트리를 제거한 _다음에야_ 새 매핑을 써야(make) 합니다. 즉 "유효한 옛 PTE → 유효한 새 PTE" 로 _직접_ 덮어쓰면 안 되고, 반드시 "유효 → invalid → (TLBI) → 새 유효"의 순서를 거쳐야 합니다.

```asm
// break-before-make: live 매핑의 속성/크기 변경
  str   xzr, [x_pte]           // ① break: PTE 를 invalid 로
  dsb   ishst                  //    store visible
  tlbi  vae1is, x_va           // ② 옛 TLB 엔트리 제거
  dsb   ish                    //    완료 대기
  str   x_new_pte, [x_pte]     // ③ make: 새 매핑 설치
  dsb   ishst
  isb
```

이유는 **TLB conflict** 입니다. 멀티코어에서 서로 다른 코어가 _같은 VA_ 에 대해 _옛 매핑과 새 매핑_ 을 각자의 TLB 에 동시에 들고 있으면, 하드웨어가 같은 VA 에 대해 _서로 다른 두 변환_ 을 발견해 동작이 architecturally 정의되지 않습니다(특히 크기가 다른 매핑이 겹칠 때). 일부 구현은 이를 **TLB conflict abort** 로 fault 시킵니다. BBM 은 "옛 매핑을 완전히 제거한 뒤 새 것을 넣어" _어느 순간에도 두 유효 변환이 공존하지 않게_ 보장합니다. 그래서 살아있는 매핑을 _제자리에서_ 바꾸는 검증 시퀀스가 conflict abort 를 내면, BBM 을 건너뛰고 유효→유효로 직접 덮어썼는지부터 의심해야 합니다.

### 5.4 ASID — context switch 에서 TLB flush 회피

ASID (Address Space IDentifier) 는 프로세스마다 부여되는 8/16-bit 식별자로, TLB entry 에 함께 저장됩니다. 다른 ASID 의 entry 는 자동으로 매칭되지 않으므로 context switch 시 TLB 를 flush 할 필요가 없습니다 (asm/MMU §③).

```asm
// context switch on AArch64 — new process: TTBR0_EL1 base + ASID
  orr   x1, x_new_pgd, x_new_asid_lsl_48
  msr   TTBR0_EL1, x1
  isb                          // new translation regime active
// no TLBI required! — TLB entries are tagged with ASID
```

ASID 를 쓰지 않으면 매 context switch 마다 `TLBI VMALLE1IS` 가 필요하고, 다음 프로세스의 첫 N 개 접근이 전부 walk 가 되어 큰 성능 손실이 납니다. ASID 풀이 고갈되면 (16-bit = 65536 프로세스) allocator 가 wrap-around 하며 그때만 flush 합니다.

`nG` 비트가 ASID 매칭 여부를 가릅니다. 커널 매핑은 `nG=0` (global) 으로 ASID 무시, 유저 매핑은 `nG=1` 로 ASID 격리됩니다.

### 5.5 TLBI 변형과 표준 시퀀스

TLBI 니모닉은 **대상 EL · 범위 · 매개변수 · shareability** 의 조합입니다. `VAE1IS` = "VA-based, EL1, Inner Shareable" (asm/MMU §①).

| 명령 | 의미 | 전형적 사용 |
|------|------|-------------|
| `TLBI VMALLE1` | 이 코어의 EL1 stage-1 전부 invalidate | PT 교체 |
| `TLBI VMALLE1IS` | 위 + inner shareable (모든 코어) | SMP 페이지 교체 |
| `TLBI VAE1IS, Xt` | VA Xt, EL1, IS (모든 코어) | SMP 단일 매핑 변경 (가장 흔함) |
| `TLBI ASIDE1, Xt` | ASID 매칭 entries 전부 | 프로세스 종료 시 |
| `TLBI IPAS2E1IS, Xt` | IPA 단위 (stage-2, hypervisor) | VM 메모리 reclaim |

shareability 접미가 broadcast 범위를 정합니다. `NSH` 는 이 코어만, `IS` 는 inner-shareable domain 의 모든 코어 (SMP 의 디폴트), `OS` 는 outer-shareable (멀티소켓). ARM 의 강점은 TLBI 가 AMBA CHI/ACE 의 **DVM (Distributed Virtual Memory)** message 로 coherent fabric 을 통해 모든 코어에 자동 broadcast 된다는 점입니다 — x86 은 SW 가 직접 IPI 를 보내 다른 코어에서 INVLPG 를 실행시키는 "TLB shootdown" 으로 OS 부담이 더 큽니다 (uarch/TlbPtw).

### 5.6 AT — Address Translation 디버그 명령

HW page walker 에게 "이 VA 를 변환해 보라" 고 직접 시키는 명령입니다. 결과는 `PAR_EL1` 에 들어옵니다 (asm/MMU §⑤).

```asm
  at    s1e1r, x_va            // stage-1, EL1, read access
  isb
  mrs   x0, PAR_EL1
  tbnz  x0, #0, .Lfault        // bit 0 = 1 이면 translation fault
  // PAR_EL1[51:12] = PA[51:12]; VA[11:0] 와 합쳐 full PA
```

커널 디버거나 검증 환경에서 "이 VA 가 어떤 PA 로 가는지, 어떤 fault 가 나는지" 를 확인하는 데 유용합니다. `S1E0R/W` (EL0 관점), `S12E1R/W` (stage-1+2 결합) 등 변형이 있어 fault 종류를 `PAR_EL1` 에서 decode 할 수 있습니다.

---

## 6. 흔한 오해 와 DV 디버그 체크리스트

### 흔한 오해

:::danger[❓ 오해 1 — 'PTE 를 메모리에 쓰면 다음 접근부터 새 매핑이 적용된다']
**실제**: TLB 가 옛 entry 를 캐시하고 있으면 `TLBI` 로 명시적으로 버리기 전까지 옛 매핑이 그대로 쓰입니다. PTE store 만으로는 부족하고 `STR → DSB ISHST → TLBI → DSB ISH → ISB` 5단계가 모두 필요합니다.<br>
**왜 헷갈리는가**: "메모리에 썼으니 즉시 보인다" 는 단순 모델 때문에 — TLB 라는 별도 캐시의 존재를 잊음.
:::
:::danger[❓ 오해 2 — 'walk 은 항상 L3 까지 4단계를 거친다']
**실제**: L1 의 block descriptor (1GB) 나 L2 의 block (2MB) 을 만나면 walk 이 거기서 종료됩니다. huge page 가 이렇게 구현되며, offset 으로 변환되지 않는 비트가 그만큼 많아집니다.<br>
**왜 헷갈리는가**: 4-level 이라는 이름이 항상 4단계를 의미한다고 오해해서.
:::
:::danger[❓ 오해 3 — 'context switch 마다 TLB 를 flush 해야 한다']
**실제**: ASID 태깅 덕분에 flush 가 필요 없습니다. `TTBR0_EL1` 에 새 ASID 를 인코딩해 쓰기만 하면 다른 ASID 의 entry 는 자동으로 매칭 안 됩니다. flush 는 ASID 풀 고갈 시에만.<br>
**왜 헷갈리는가**: ASID 없는 옛 아키텍처의 mental model 이 남아서.
:::
:::danger[❓ 오해 4 — 'peek 으로 본 IPA 가 진짜 물리 주소다']
**실제**: 가상화 환경에서 Guest 의 stage-1 walk 결과는 IPA 일 뿐이고, hypervisor 의 stage-2 walk 를 거쳐야 진짜 PA 가 됩니다. Guest 는 IPA 를 PA 로 믿지만 host 입장에선 한 단계 더 남았습니다.<br>
**왜 헷갈리는가**: 단일 stage 시스템에서는 stage-1 결과가 곧 PA 라서.
:::
:::danger[❓ 오해 5 — 'TLBI 한 번이면 모든 코어가 즉시 새 매핑을 본다']
**실제**: `TLBI` 발행 후 `DSB ISH` 로 모든 코어의 invalidate 완료를 기다리지 않으면, 다른 코어는 아직 옛 TLB 로 동작할 수 있습니다. invalidate 의 완료는 비동기입니다.<br>
**왜 헷갈리는가**: TLBI 가 명령 한 줄이라 즉시 완료될 것 같아서 — 실제로는 fabric broadcast + 완료 대기가 필요.
:::
### DV 디버그 체크리스트 (이 모듈 내용으로 마주칠 첫 실패들)

| 증상 | 1차 의심 | 어디 보나 |
|------|----------|-----------|
| PTE 는 맞는데 변환 결과가 옛 PA | TLBI 누락 또는 DSB/ISB 시퀀스 불완전 | PTE 변경 코드의 5단계 시퀀스 존재 여부 |
| 변환이 간헐적으로만 틀림 (멀티코어) | `TLBI` 가 IS variant 아님 (이 코어만 invalidate) | TLBI 의 shareability 접미 (`IS` vs `NSH`) |
| 같은 VA 가 프로세스마다 다른 PA — 그런데 가끔 섞임 | ASID 충돌 또는 wrap-around 후 flush 누락 | ASID allocator, `nG` 비트 설정 |
| 변환 결과 권한 오류 (write 인데 RO) | PTE 의 `AP` 비트 오설정 | descriptor 의 `AP[2:1]` |
| 첫 접근마다 trap | `AF=0` 인데 HW AF update 미지원 | `TCR_EL1` 의 HA/HD 비트, descriptor AF |
| huge page 인데 offset 이 안 맞음 | block descriptor 인식 실패 (L1/L2 stop 안 함) | descriptor `[1:0]` 와 stop level |
| 가상화에서 변환 latency 폭발 | nested walk + PWC miss | stage-2 walk 동반 여부, PWC 동작 |

---

## 7. 핵심 정리 (Key Takeaways)

- **4KB granule, 48-bit VA = 4-level (L0~L3) walk**. VA 를 9-bit 씩 잘라 각 레벨 index 로 쓰고, leaf PTE 의 PA 와 12-bit offset 을 합쳐 PA 를 만든다.
- **walk 은 중간 종료 가능** — L1 block(1GB), L2 block(2MB) 으로 huge page 구현. offset 비트가 그만큼 늘어난다.
- **TLB 4단 계층**: μTLB (per-port FA CAM, 1-cycle) → main TLB (SA SRAM) → PWC (중간 PTE) → HW walker. miss 비용이 단계마다 폭증.
- **ASID/VMID 태깅**으로 context switch / VM switch 시 flush 회피. `nG` 비트가 ASID 매칭 여부를 가른다.
- **PTE 변경 시퀀스**: `STR → DSB ISHST → TLBI → DSB ISH → ISB`. 한 단계라도 빠지면 stale translation 버그.
- **ARM 의 DVM** 으로 TLBI 가 fabric 통해 모든 코어에 broadcast — x86 의 SW shootdown 보다 우월.

:::caution[실무 주의점]
- PTE 를 바꾸고 곧바로 비교/접근하는 검증 시퀀스는 반드시 barrier 시퀀스를 넣어야 — 안 그러면 stale TLB 로 spurious mismatch.
- 멀티코어 환경에서는 `TLBI` 의 `IS` 접미가 필수. `NSH` 는 자기 코어 한정.
- `AT` 명령 + `PAR_EL1` 으로 "이 VA 가 어디로 가는가" 를 확인 — 변환 디버그의 핵심 도구.
:::
### 7.1 자가 점검

:::tip[🤔 Q1 — walk 비트 슬라이싱 (Bloom: Apply)]
4KB granule, 48-bit VA 에서 `VA = 0x0000_0040_0080_1000` 의 L0/L1/L2/L3 index 와 page offset 은?
<details>
<summary>정답</summary>

VA 를 비트로 자릅니다 (`L0=[47:39], L1=[38:30], L2=[29:21], L3=[20:12], offset=[11:0]`).
- `0x0000_0040_0080_1000` = bit 패턴으로 bit 30 (L1), bit 23 (L2), bit 12 (L3) 가 set.
- `VA[47:39]` = 0 → **L0 index = 0**
- `VA[38:30]` = bit 30 만 → **L1 index = 1**
- `VA[29:21]` = bit 23 만 (= bit 23-21 = 4) → **L2 index = 4**
- `VA[20:12]` = bit 12 만 → **L3 index = 1**
- `VA[11:0]` = 0 → **offset = 0** (page-aligned)

핵심은 각 9-bit 필드가 0~511 범위의 독립 index 라는 점, 그리고 offset 이 변환되지 않고 그대로 PA 하위 12비트가 된다는 점입니다.

</details>
:::
:::tip[🤔 Q2 — TLBI 시퀀스 분석 (Bloom: Analyze)]
멀티코어 시스템에서 PTE 를 바꾼 뒤 `STR; TLBI VAE1IS; ISB` 만 했다 (`DSB` 둘 다 누락). 어떤 증상이 나타날 수 있나?
<details>
<summary>정답</summary>

두 가지 race 가 동시에 가능합니다.
- **`DSB ISHST` 누락** → PTE store 가 메모리에 visible 되기 전에 `TLBI` 가 나가고, 그 사이 다른 코어의 page walker 가 invalidate 직후 다시 walk 하면서 _옛 PTE_ 를 읽어 TLB 에 재적재할 수 있음.
- **`DSB ISH` 누락** → `TLBI` 의 invalidate 가 다른 코어에서 완료되기 전에 `ISB` 와 후속 접근이 진행 → 다른 코어가 stale TLB entry 로 옛 매핑 사용.
- 증상은 **간헐적·코어 의존적인 stale translation** — 같은 코드가 어떤 실행에선 맞고 어떤 실행에선 틀림. 가장 재현이 어려운 부류. 수정은 `STR → DSB ISHST → TLBI VAE1IS → DSB ISH → ISB` 의 5단계 복원.

</details>
:::
### 7.2 출처

**Internal (DV_SKOOL)**
- ARM AArch64 학습 소스 `arm/MMU` — 2-stage translation, granule, descriptor 형식, MMU 제어 레지스터
- `asm/MMU` — TLBI 변형 표, 5단계 시퀀스, ASID/nG, AT 명령, 수동 walk 추적
- `uarch/TlbPtw` — μTLB/main TLB/PWC/walker 계층, miss latency, DVM vs IPI
- 일반 페이지 테이블: [MMU 토픽](../../mmu/), 메모리 모델/barrier: [M04](../04_memory_model_barriers/)

**External**
- *Arm Architecture Reference Manual for A-profile* (ARM DDI 0487) — D-stage translation, TLB maintenance, system registers (외부 표준 지식)
- *Arm Cortex-A Series Programmer's Guide* — TLBI/DSB/ISB 시퀀스 (외부 표준 지식)

---

## 다음 모듈

→ [Module 06 — Caches & GIC](../06_caches_gic/): 캐시 계층과 coherency point, 그리고 ARM 표준 인터럽트 컨트롤러 GICv3 의 SGI/PPI/SPI/LPI 와 인터럽트 진입 흐름.

[퀴즈 풀어보기 →](../quiz/05_mmu_translation_quiz/)
