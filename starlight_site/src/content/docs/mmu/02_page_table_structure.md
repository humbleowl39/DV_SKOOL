---
title: "Module 02 — Page Table Structure"
---

:::tip[학습 목표]
이 모듈을 마치면:

- **Explain** Single-level page table 의 메모리 비용 문제와 Multi-level 이 그것을 해결하는 원리를 설명할 수 있다.
- **Trace** 64-bit VA 를 ARMv8 4-level translation 으로 단계별 추적해 PA 를 도출할 수 있다.
- **Distinguish** 4 KB / 16 KB / 64 KB granule 과 각 granule 별 page level 깊이 / 주소 비트 분할을 식별할 수 있다.
- **Apply** Block descriptor (huge page) 와 Table descriptor 의 차이를 시나리오에 매핑할 수 있다.
- **Describe** Page Walk Cache (PWC) 가 walk 비용을 어떻게 줄이는지 설명할 수 있다.
:::
:::note[사전 지식]
- [Module 01](../01_mmu_fundamentals/) (VA → PA 변환의 큰 그림, TLB 와 walk 의 분리)
- 이진/16진 비트 마스킹, 인덱스 추출
:::
---

## 1. Why care? — 이 모듈이 왜 필요한가

### 1.1 시나리오 — 왜 _4-level_ page table?

48-bit virtual address. _순진하게_ flat page table:
- 4 KB page = offset 12 bit. VA 48 - 12 = 36 bit index.
- Table size: 2^36 × 8 byte (PTE) = **512 GB**.

**불가능**. 모든 process 가 512 GB page table 필요.

해법: **Multi-level (sparse) page table**:
- L0 (top): 9 bit index = 512 entries.
- L1: 9 bit = 512.
- L2: 9 bit = 512.
- L3 (leaf): 9 bit = 512 × 4 KB page.
- Total: 4 × 9 + 12 = 48 bit. ✓

**Sparse**: 실제 사용 안 하는 L0 entry 는 _NULL_ → 그 sub-tree 의 _수 GB_ table 안 만들어짐. _Process 의 1-10 MB page table_ 로 _entire 48-bit VA space_ 표현.

**Trade-off**: page table walk 이 _4 memory access_. 그래서 _TLB_ 가 필수, _huge page (2 MB / 1 GB)_ 가 _walk depth 감소_, _PWC (Page Walk Cache)_ 가 _intermediate level cache_.

**Page table walk 은 MMU 성능과 fault diagnosis 의 _공통 어휘_** 입니다. 이후 모든 모듈 — TLB invalidate by VA 의 효과, IOMMU Stage 1 + Stage 2, 성능 분석의 PWC, DV 의 reference model — 이 "어느 level 의 어느 PTE 가 어떻게 됐는가" 의 언어로 표현됩니다. 이 모듈의 비트 분할표가 후속 챕터의 _도면_ 입니다.

또한 4-level walk = 최대 4번의 메모리 access 라는 사실이 TLB 의 존재 이유, PWC 의 존재 이유, huge page 의 존재 이유를 모두 한 줄로 설명합니다. 이 _이유 사슬_ 을 잡지 못하면 후속 챕터들이 따로 노는 토픽처럼 느껴집니다.

---

## 2. Intuition — 도서관 색인 비유와 한 장 그림

:::tip[💡 한 줄 비유]
**다단계 Page Table** ≈ **도서관의 4단 색인 (대분류 → 중분류 → 소분류 → 책장 위치)**.<br>
L0 → L1 → L2 → L3 으로 좁혀가며 최종 4 KB page 위치에 도달. 각 단계 entry 가 _다음 색인 책의 어디를 펼치라_ 의 포인터를 담고 있어, 사용하지 않는 가지(branch) 는 통째로 비워둘 수 있습니다.<br>
**Block descriptor** = 중간 단계에서 _"이 동(2 MB / 1 GB) 은 통째로 같은 곳에 있다"_ 라고 선언하고 더 안 펼치는 단축 경로.
:::
### 한 장 그림 — 4-level walk 와 Block 의 분기

VA[63:48] sign-ext (TTBR0 vs TTBR1 결정), VA[47:39] = L0 idx, VA[38:30] = L1 idx, VA[29:21] = L2 idx, VA[20:12] = L3 idx, VA[11:0] = page offset (변환 X).

```d2
direction: down

TTBR: "TTBR0_EL1"
L0: "L0 Table\n(4 KB, 512×8B PTE)\nidx → L0 PTE"
L1: "L1 Table\nidx → L1 PTE"
L2: "L2 Table\nidx → L2 PTE"
L3: "L3 Table\nidx → L3 PTE\n= Page descriptor"
GB: "1 GB block 종료\nPA[47:30] || VA[29:0]"
MB: "2 MB block 종료\nPA[47:21] || VA[20:0]"
KB: "4 KB page (정상 종료)\nPA[47:12] || VA[11:0]"
TTBR -> L0
L0 -> L1: "Table desc"
L1 -> L2: "Table desc"
L1 -> GB: "Block desc (1 GB)"
L2 -> L3: "Table desc"
L2 -> MB: "Block desc (2 MB)"
L3 -> KB
```

### 왜 이 디자인인가 — Design rationale

세 가지 요구가 동시에 풀려야 했습니다.

1. **48-bit VA 의 sparse 성** — 실제 process 가 쓰는 영역은 전체 256 TB 중 수십 MB 수준. 통짜 단일 테이블은 512 GB 가 필요해 _불가능_.<br> → Multi-level 로 _쓰는 가지만_ 할당.
2. **각 sub-table 이 정확히 1 page (4 KB) 가 되도록** — 운영체제가 page 단위로 자기 자료구조를 관리하기 가장 편함.<br> → 4 KB / 8 B = 512 entries / table → 9-bit index → 4 level × 9 + 12 offset = 48 bit 의 _필연적인_ 산수.
3. **대용량 영역 (frame buffer, MMIO, RDMA buffer) 은 walk 을 짧게**.<br> → Block descriptor 로 L1/L2 에서 walk 을 조기 종료, TLB 한 entry 가 1 GB / 2 MB 를 cover.

이 세 요구의 교집합이 ARMv8 / RISC-V Sv48 / x86-64 의 _거의 동일한_ 구조입니다. 용어만 다르고 산수는 같습니다.

---

## 3. 작은 예 — VA 0xFFFF_0000_0040_0ABC 의 4-level walk

가장 단순한 시나리오. ARMv8 EL1 에서 동작하는 kernel thread 가 **VA = 0xFFFF_0000_0040_0ABC** 를 읽습니다. 4 KB granule, ASID=1, TTBR1_EL1 = `0x0000_0009_0000_0000` (VA[63] = 1 이므로 TTBR1 사용). TLB 는 cold.

### 단계별 추적

```
   VA = 0xFFFF_0000_0040_0ABC
        │
        ├── VA[63:48] = 0xFFFF  (sign-ext, all-ones → TTBR1 영역)
        ├── VA[47:39] = 0x000   (L0 index = 0)
        ├── VA[38:30] = 0x000   (L1 index = 0)
        ├── VA[29:21] = 0x002   (L2 index = 2)
        ├── VA[20:12] = 0x000   (L3 index = 0)
        └── VA[11:0]  = 0xABC   (page offset)

   ┌────────────────────────────────────────────────────────────┐
   │ L0 read: 0x0000_0009_0000_0000 + 0×8                       │
   │   PTE = 0x0000_0009_1000_0003                              │
   │     [1:0] = 0b11 → Table descriptor                        │
   │     next-level = 0x0000_0009_1000_0000                     │
   ├────────────────────────────────────────────────────────────┤
   │ L1 read: 0x0000_0009_1000_0000 + 0×8                       │
   │   PTE = 0x0000_0009_2000_0003 → Table desc                 │
   ├────────────────────────────────────────────────────────────┤
   │ L2 read: 0x0000_0009_2000_0000 + 2×8 = ..._0010            │
   │   PTE = 0x0040_0000_0080_0741                              │
   │     [1:0] = 0b01 → Block descriptor (huge!)                │
   │     OutputAddr[47:21] = 0x000_0000_0040_0  (2 MB block)    │
   │     AP[7:6]=01, AF=1, AttrIdx=2 (Normal WB)                │
   │   → walk 조기 종료                                           │
   ├────────────────────────────────────────────────────────────┤
   │ PA 합성 (2 MB block):                                       │
   │   PA = OutputAddr[47:21] || VA[20:0]                       │
   │       = 0x0000_0000_0040_0_000 | 0x000_0ABC                │
   │       = 0x0000_0000_0040_0ABC                              │
   ├────────────────────────────────────────────────────────────┤
   │ TLB fill: (ASID=1, VPN, PPN, AP, AttrIdx, size=2MB)        │
   │   → 다음에 같은 2 MB block 내 어디든 TLB hit                │
   └────────────────────────────────────────────────────────────┘
```

### 단계별 의미

| Step | 누가 | 무엇을 | 왜 |
|---|---|---|---|
| ① | MMU walk engine | TTBR1 + L0 idx → L0 PTE | VA[63] = 1 이므로 TTBR0 가 아닌 TTBR1 사용 |
| ② | walk engine | PTE[1:0] 검사 → `0b11` Table | 다음 레벨로 내려감 |
| ③ | walk engine | L1 PTE 도 Table | 동일 |
| ④ | walk engine | L2 PTE 가 `0b01` Block | walk 조기 종료, 2 MB block |
| ⑤ | MMU | OutputAddr[47:21] 와 VA[20:0] 결합 | block 의 21-bit offset 통째로 사용 |
| ⑥ | TLB fill logic | size=2MB 로 캐싱 | 다음번에 이 block 내 다른 4 KB 접근도 hit |

### 만약 L1 PTE 의 V=0 이었다면?

- walk 가 L1 에서 멈춤 → **Translation Fault at Level 1**.
- ESR_EL1.DFSC[5:0] = `0b000101` (Translation fault, level 1).
- FAR_EL1 = 0xFFFF_0000_0040_0ABC (failed VA).
- HW 는 PTE 를 채우지 않음 — _SW (OS)_ 가 demand-paging 후 retry.

### 같은 VA 가 4 KB 매핑이었다면? (대조)

L2 PTE 가 Table descriptor 였다면 L3 까지 한 번 더 read → 총 4 mem access. Block 으로 끝나면 3 mem access. **Block descriptor 가 walk 비용을 아끼는 본질**입니다.

:::note[여기서 잡아야 할 두 가지]
**(1) PTE[1:0] 두 비트가 walk 의 _분기 신호_** — `0b11` (Table) 이면 다음 레벨, `0b01` (Block at L1/L2) 이면 종료, `0b11` (Page at L3) 이면 종료, `0b00` 이면 invalid → fault. 이 인코딩이 모든 walk 의 척추입니다. <br>
**(2) Block descriptor 의 PA 합성은 _block size 만큼_ VA 를 그대로 통과** — 4 KB 면 12 bit, 2 MB 면 21 bit, 1 GB 면 30 bit. TLB 한 entry 가 cover 하는 영역도 그만큼 커집니다. 이게 huge page 의 본질이자 PWC 의 보조 역할이 의미를 갖는 이유.
:::
---

## 4. 일반화 — Multi-level 구조, Block vs Table, PWC

### 4.1 단일 레벨 page table 의 비용 (왜 multi-level 인가)

```
48-bit VA, 4KB Page의 경우:

  VPN = 48 - 12 = 36 bit
  Page Table 엔트리 수 = 2^36 = 약 687억 개
  PTE 크기 = 8 bytes
  Page Table 크기 = 687억 × 8 = 512 GB !

  → 프로세스 하나당 512 GB의 Page Table? 불가능.
```

### 4.2 Multi-level 의 산수

이 문제를 해결하는 핵심 관찰은 단순합니다. 대부분의 프로세스는 전체 256 TB 주소 공간 중 실제로는 수십 MB 정도만 사용합니다. 그렇다면 사용하지 않는 영역의 하위 테이블을 아예 만들지 않으면 됩니다. 이것이 sparse 구조의 본질이고, 각 레벨의 테이블 하나가 정확히 4 KB(하나의 page) 가 되도록 설계하면 OS 의 메모리 관리 체계와 자연스럽게 맞아떨어집니다.

#### 9-bit index 가 _필연_ 인 인과 방향

"512 = 9 bit" 라는 결과는 사실 거꾸로 따라 나온 것입니다. 인과의 출발점은 **"table 하나 = page 하나(4 KB)"** 라는 _제약을 먼저 두는 것_ 입니다. 이 제약을 둬야 page table 자체도 일반 page 처럼 할당/회수/swap 할 수 있어 OS 의 page allocator 를 그대로 재사용할 수 있기 때문입니다. 이제 산수가 한 방향으로 흘러갑니다:

```
제약 1:  table 하나 = 4 KB (one page)
제약 2:  PTE 하나 = 8 byte   ← 왜 8B 인가?
  → 한 table 의 entry 수 = 4096 / 8 = 512
  → index 폭 = log2(512) = 9 bit  (결과)
```

여기서 _왜 PTE 가 8 byte 인가_ 가 진짜 근원입니다. PTE 는 출력 물리 주소(최대 ~48-bit PA, 확장 시 52-bit)에 더해 valid/type/AP/AF/attr/SH 같은 메타비트까지 담아야 합니다. 48-bit 주소만 해도 4 byte(32-bit)에는 절대 안 들어가므로, 자연스러운 다음 워드 크기인 **8 byte(64-bit)** 가 PTE 크기로 강제됩니다. 즉 _64-bit PA 를 수용해야 한다_ → PTE = 8B → (4KB / 8B) = 512 → index = 9-bit 라는 사슬이고, 9-bit 가 먼저 정해진 게 아니라 _주소 폭과 page 크기가 9-bit 를 강요한 것_ 입니다. 그래서 4 level × 9 + 12 = 48 의 등식도 우연이 아니라 이 두 제약의 산술적 귀결입니다.

```
핵심 관찰:
  대부분의 프로세스는 전체 주소 공간의 극히 일부만 사용한다.
  → 사용하지 않는 영역의 하위 테이블을 할당하지 않으면 메모리 절약

  4-level Page Table (x86-64, ARMv8 4KB granule):
    Level 0: 512 entries → 각 엔트리가 512GB 영역 커버
    Level 1: 512 entries → 각 엔트리가 1GB 영역 커버
    Level 2: 512 entries → 각 엔트리가 2MB 영역 커버
    Level 3: 512 entries → 각 엔트리가 4KB 영역 커버 (최종 PPN)

  각 테이블 크기 = 512 × 8B = 4KB = 정확히 1 Page
```

### 4.3 ARMv8 4-Level Page Table (4 KB Granule) — 비트 분할

```
48-bit Virtual Address:

 63    48 47   39 38   30 29   21 20   12 11       0
+--------+-------+-------+-------+-------+----------+
| Sign   |  L0   |  L1   |  L2   |  L3   |  Offset  |
| Ext    | Index | Index | Index | Index | (12-bit) |
| (16bit)| (9bit)| (9bit)| (9bit)| (9bit)|          |
+--------+-------+-------+-------+-------+----------+
              |       |       |       |
              v       v       v       v
           Level 0  Level 1  Level 2  Level 3
           Table    Table    Table    Table
```

### 4.4 Walk 흐름 (4단계)

```d2
direction: down

TTBR: "TTBR\n(Translation Table Base Register)\n= Level 0 테이블의 물리 주소"
L0E: "Level 0 Table\nEntry[L0 Index]"
L1E: "Level 1 Table\nEntry[L1 Index]"
L2E: "Level 2 Table\nEntry[L2 Index]"
L3E: "Level 3 Table\nEntry[L3 Index]"
GB1: "1 GB Block\n(Block Descriptor)"
MB2: "2 MB Block\n(Block Descriptor)"
PPN: "4 KB Page 의\n물리 주소 (PPN)"
TTBR -> L0E
L0E -> L1E: "Level 1 테이블 주소"
L1E -> L2E: "Level 2 테이블 주소"
L1E -> GB1: "Block desc" { style.stroke-dash: 4 }
L2E -> L3E: "Level 3 테이블 주소"
L2E -> MB2: "Block desc" { style.stroke-dash: 4 }
L3E -> PPN
```

> 총 **4번** 의 메모리 접근 필요 → 이것이 TLB 가 필수적인 이유.

### 4.5 Block Descriptor — 중간 레벨 종료

4-level walk 를 항상 마지막 L3 까지 내려가야 할 이유는 없습니다. GPU 의 frame buffer 나 대용량 MMIO 영역처럼 수 GB 를 연속으로 매핑해야 하는 경우, L1 또는 L2 에서 walk 를 일찍 끝내는 Block Descriptor 를 쓰면 됩니다. PTE[1:0] 이 `0b01` 이면 "이 entry 가 바로 최종 PA 블록" 임을 의미하고, 그 순간 walk engine 은 나머지 레벨을 건너뜁니다. 결과적으로 TLB 한 entry 가 1 GB 또는 2 MB 전체를 커버하게 되어 hit rate 도 오르고 walk 비용도 줄어듭니다.

:::note[Block 의 output PA 는 _반드시 block 크기에 정렬_ 되어야 한다]
Block descriptor 의 output address 는 그냥 아무 PA 나 가리킬 수 없고, **그 block 크기의 배수(정렬)** 여야 합니다 — 2 MB block 이면 PA 가 2 MB 정렬(하위 21 bit = 0), 1 GB block 이면 1 GB 정렬(하위 30 bit = 0)이어야 합니다. _왜_ 그런가? PA 합성식이 `PA = OutputAddr[47:N] || VA[N-1:0]` 형태로, block 크기에 해당하는 하위 비트(2 MB면 [20:0])를 _VA 의 offset 으로 통째로 통과_ 시키기 때문입니다. 즉 walk engine 은 OutputAddr 의 그 하위 비트를 아예 읽지 않고 0으로 간주합니다. 만약 OS 가 2 MB 정렬이 아닌 PA(예: 하위 비트가 0이 아닌 값)를 block descriptor 에 넣으면, 그 하위 비트는 _하드웨어가 무시_ 하고 VA offset 으로 덮어써져 의도와 다른 PA 가 합성됩니다.

이것이 DV 에서 마주치는 **"block 사용 시 PA 가 1 MB(또는 그 배수) 어긋남"** 증상의 근본 원인입니다 — PTE 에 비정렬 OutputAddr 를 쓰면 정확히 그 어긋난 만큼의 주소 오류로 나타납니다.
:::

```
Level 1에서 Block Descriptor:
  1GB 블록을 하나의 엔트리로 직접 매핑
  → Level 2, 3 테이블 불필요
  → 대용량 연속 매핑에 유리 (MMIO, 프레임버퍼 등)

Level 2에서 Block Descriptor:
  2MB 블록을 하나의 엔트리로 직접 매핑
  → Huge Page (Linux에서 THP, Transparent Huge Pages)
```

### 4.6 PWC (Page Walk Cache) — Walk 비용 절감

```
문제: 4-level Walk = 4번 메모리 접근 (~400 ns)
관찰: 인접한 VA들은 상위 레벨 PTE를 공유한다

예시:
  VA 0x0000_0000_1000 (Page A)와 VA 0x0000_0000_2000 (Page B)
  → Level 0, 1, 2 인덱스가 동일! Level 3만 다름
  → Level 0~2의 PTE를 캐싱하면 Page B Walk 시 Level 3만 읽으면 됨

Page Walk Cache 구조:
  +--Level 0 Cache--+  +--Level 1 Cache--+  +--Level 2 Cache--+
  | VPN[47:39]→PTE  |  | VPN[47:30]→PTE  |  | VPN[47:21]→PTE  |
  | (~4 entries)    |  | (~8 entries)    |  | (~16 entries)   |
  +----------------+  +----------------+  +----------------+

  Walk 시 각 레벨 캐시 확인:
    Level 0 Hit → 1회 메모리 접근 생략 (3회로 단축)
    Level 0+1 Hit → 2회 생략 (2회로 단축)
    Level 0+1+2 Hit → 3회 생략 (1회로 단축!)

  효과:
    순차 접근 시 PWC Hit Rate 매우 높음 (같은 1GB/2MB 영역 내)
    → 평균 Walk 비용 40~60% 감소
```

**DV 포인트**: PWC의 정확성 검증 — Page Table 변경 후 PWC에 stale 데이터가 남으면 잘못된 PA가 생성될 수 있다. TLB Invalidation 시 PWC도 함께 무효화되는지 확인해야 한다.

#### PWC 가 _왜_ TLB 와 별개 구조여야 하는가

PWC 와 TLB 를 하나로 합치지 않는 이유는 둘이 캐싱하는 _대상의 성격_ 이 근본적으로 다르기 때문입니다. **TLB 는 leaf** 를 캐싱합니다 — 최종 (VPN → PPN) 매핑, 즉 _한 page(4 KB)_ 단위의 변환 결과입니다. 반면 **PWC 는 non-leaf** 를 캐싱합니다 — walk 도중 만나는 중간 PTE, 즉 _다음 레벨 table 의 base 주소_ 입니다. 같은 L2 PTE 하나는 그 아래 512개 page(= 2 MB 영역)의 walk 에서 공유되므로, PWC 엔트리 하나가 cover 하는 주소 공간 단위가 TLB 엔트리보다 훨씬 큽니다.

이 "cover 하는 주소공간 단위가 다르다" 는 점이 키와 무효화 정책의 차이를 강제합니다:

| 구조 | 캐싱 대상 | 키(key) | cover 단위 | 무효화 영향 범위 |
|---|---|---|---|---|
| **TLB** | leaf: VPN→PPN+perm+attr | 전체 VPN (+ASID/VMID) | 1 page (4 KB 등) | 그 page 의 매핑만 |
| **PWC** | non-leaf: 다음 table base | VPN 의 _상위 부분_ (level 별) | 1 GB / 2 MB 서브트리 | 그 서브트리 전체의 walk |

따라서 어떤 VA 의 _leaf_ 매핑만 바꾸고 TLB 만 invalidate 했더라도, 그 변경이 중간 table 의 구조 변경(예: table → block 전환, table 재배치)을 동반한다면 PWC 에 남은 옛 next-level base 가 stale 가 됩니다. TLBI 가 PWC 까지 함께 무효화하도록 설계됐는지를 _별도로_ 검증해야 하는 이유가 바로 이 구조적 분리에서 나옵니다(흔한 오해 3 참조).

---

## 5. 디테일 — PTE 필드, Granule, ISA 비교, ASID/VMID

### 5.1 ARMv8 Level 3 Page Descriptor (4 KB)

```
 63    52 51   48 47          12 11  10  9  8  7  6  5  4  2  1  0
+--------+------+--------------+-----+--+--+--+--+--+--+-----+--+
|Upper   | Res  | Output Addr  | nG  |AF|SH|AP|NS|AI|  |Type | V|
|Attrs   |      | (PPN)        |     |  |  |  |  |  |  | =11 | =1|
+--------+------+--------------+-----+--+--+--+--+--+--+-----+--+
```

### 5.2 PTE 주요 필드

| 필드 | 비트 | 의미 |
|------|------|------|
| V (Valid) | [0] | 유효한 엔트리 여부 |
| Type | [1] | 0=Block, 1=Table/Page |
| AI (AttrIdx) | [4:2] | MAIR 레지스터의 캐시 속성 인덱스 |
| NS | [5] | Non-Secure (TrustZone 관련) |
| AP | [7:6] | Access Permission (RO/RW, EL0/EL1) |
| SH | [9:8] | Shareability (Inner/Outer/Non) |
| AF (Access Flag) | [10] | 접근된 적 있는 페이지인지 (OS 페이지 교체 힌트) |
| nG (not Global) | [11] | ASID 사용 여부 |
| Output Address | [47:12] | 물리 페이지 번호 (PPN) |
| Upper Attrs | [63:52] | XN(Execute-Never), PXN, Contiguous 등 |

### 5.3 Access Permission (AP) 인코딩

| AP[7:6] | EL1 (Kernel) | EL0 (User) |
|---------|-------------|-----------|
| 00 | RW | No Access |
| 01 | RW | RW |
| 10 | RO | No Access |
| 11 | RO | RO |

### 5.4 Contiguous Bit — TLB 효율 향상

```
ARMv8 Contiguous bit (PTE[52]):
  인접한 16개의 4KB 페이지가 물리적으로도 연속일 때
  → PTE에 Contiguous bit = 1 설정
  → TLB가 16개 PTE를 하나의 엔트리로 통합 (4KB × 16 = 64KB)

  +--TLB Entry (Contiguous)--+
  | VPN range: 0x10~0x1F     |  ← 16개 VA 페이지를 하나로
  | PPN base: 0x80           |
  | Size: 64KB (effective)   |
  +---------------------------+

효과:
  - TLB 엔트리 소모: 16개 → 1개 (16배 절약)
  - 4KB Granule이지만 64KB TLB 커버리지 효과
  - Huge Page(2MB)까지 갈 필요 없이 중간 크기 커버리지

제약:
  - 16개 페이지가 물리적으로 연속이어야 함
  - OS가 적극적으로 연속 할당해야 효과적
  - 일부만 unmap하면 Contiguous 해제 필요

DV 검증:
  - Contiguous 엔트리 내 개별 페이지 접근 시 정확한 PA 계산
  - Contiguous 영역 중간 페이지 unmap → 엔트리 분리 확인
  - Contiguous + non-contiguous 혼합 시 TLB 동작
```

Contiguous bit 가 _어떻게_ 16개를 하나로 줄이는지를 메커니즘으로 보면 이렇습니다. TLB 는 평소 한 page 의 PPN 을 그대로 들고 있지만, Contiguous bit 이 1로 표시된 entry 를 채울 때는 **"이 page 가 속한 16개 묶음은 PPN 이 연속이다"** 라는 _가정(hint)_ 을 single bit 으로 받아들입니다. 그러면 TLB 는 그 16개 중 어느 VA 가 들어와도 한 entry 의 base PPN 에 적절한 offset 을 더해 PA 를 즉석에서 만들어 줄 수 있어, 16개의 별도 TLB entry 대신 하나로 16개를 cover 합니다.

이 가정이 성립하려면 **OS 가 그 16개 page 를 물리적으로 연속(PPN 이 base, base+1, …, base+15)이면서 그 묶음 자체가 16-page 경계에 정렬되도록 할당** 해야 합니다. 즉 contiguous bit 는 "내가 약속을 지켰으니 너는 검사 없이 믿어라" 라는 OS→HW 계약이고, OS 가 약속을 안 지킨 채(불연속인데) bit 만 켜면 TLB 가 잘못된 PA 를 합성합니다. _왜 하필 16개_ 인가는 정렬 단위의 선택입니다 — 16 × 4 KB = 64 KB 가 되어, 4 KB granule 을 유지하면서도 64 KB granule 의 TLB reach 효과를 별도 page 크기 없이 얻으려는 _중간 단계_ 로 16이 정해졌습니다(추론).

### 5.5 Copy-on-Write (COW) 메커니즘

COW = `fork()` 시 물리 메모리 복사를 지연하는 최적화. `fork()` 전후와 Write 시 흐름:

```d2
shape: sequence_diagram

Parent
MMU
OS: "OS COW Handler"

# Note over Parent: fork() 전\nParent: VA 0x1000 → PA 0x8000 (RW)
# Note over Parent: fork() 직후\nParent/Child: VA 0x1000 → PA 0x8000 (RO 공유)
Parent -> MMU: "Write VA 0x1000"
MMU -> Parent: "Permission Fault (PTE = RO)" { style.stroke-dash: 4 }
Parent -> OS: "Fault handler 호출"
OS -> OS: "1. 새 물리 페이지 할당 (PA 0xC000)\n2. PA 0x8000 → PA 0xC000 복사\n3. Parent PTE 업데이트\n   VA 0x1000 → PA 0xC000 (RW)\n4. TLB Invalidation (stale RO 제거)"
OS -> Parent: "복귀 → Write 재실행" { style.stroke-dash: 4 }
Parent -> MMU: "Write VA 0x1000 (재실행)"
MMU -> Parent: "성공 (PA 0xC000, RW)" { style.stroke-dash: 4 }
```

**MMU/TLB 관점**:

- COW = Permission Fault 를 의도적으로 활용하는 메커니즘
- TLB 에 RO 엔트리 → Write 시도 → Fault → TLB Invalidation → RW 로 재채움
- DV 에서 Permission Fault → 복구 → TLB 상태 변화의 전체 흐름 검증 필요

### 5.6 RISC-V Page Table 비교 — Sv39 / Sv48

```
RISC-V는 Sv39 (3-level)과 Sv48 (4-level) 모드 지원:

Sv39 (3-Level, 39-bit VA):
  38    30 29    21 20    12 11       0
  +-------+-------+-------+----------+
  | VPN[2]| VPN[1]| VPN[0]|  Offset  |
  | (9bit)| (9bit)| (9bit)| (12-bit) |
  +-------+-------+-------+----------+
  가상 주소 공간: 512 GB (2^39)
  사용: 임베디드, 소형 시스템

Sv48 (4-Level, 48-bit VA):
  47    39 38    30 29    21 20    12 11       0
  +-------+-------+-------+-------+----------+
  | VPN[3]| VPN[2]| VPN[1]| VPN[0]|  Offset  |
  | (9bit)| (9bit)| (9bit)| (9bit)| (12-bit) |
  +-------+-------+-------+-------+----------+
  가상 주소 공간: 256 TB (2^48)
  사용: 서버, 대형 시스템
```

### 5.7 ARMv8 vs RISC-V vs x86-64 비교

| 항목 | ARMv8 (AArch64) | RISC-V (Sv48) | x86-64 |
|------|----------------|--------------|--------|
| VA 비트 | 48-bit | 48-bit | 48-bit (57 with LA57) |
| PT 레벨 | 4 (L0~L3) | 4 (L3~L0, 번호 반대) | 4 (PML4→PDP→PD→PT) |
| Granule | 4KB/16KB/64KB | 4KB | 4KB |
| 각 테이블 엔트리 수 | 512 (9-bit index) | 512 (9-bit index) | 512 (9-bit index) |
| PTE 크기 | 8 bytes | 8 bytes | 8 bytes |
| Huge Page | 2MB (L2), 1GB (L1) | 2MB (L1), 1GB (L0) | 2MB (PD), 1GB (PDP) |
| ASID | 8/16-bit | 16-bit | PCID 12-bit |
| 가상화 | Stage 1+2 | 2-stage (G-Stage) | EPT (Extended PT) |
| Table Base Reg | TTBR0/1_EL1 | satp | CR3 |

**면접 포인트**: 세 ISA 모두 구조적으로 유사하다 (512-entry × 4-level × 8B PTE). 차이는 용어와 세부 인코딩이며, 핵심 원리(multi-level walk, TLB caching)는 동일하다. "RISC-V도 다뤄봤느냐" 질문에 "구조는 ARMv8과 거의 동일하며, 검증 방법론은 그대로 적용 가능하다"고 답하면 된다.

### 5.8 ASID (Address Space Identifier)

#### 왜 필요한가?

```
컨텍스트 스위치 시 문제:

  Process A: VA 0x1000 → PA 0x8000
  Process B: VA 0x1000 → PA 0xA000

  Process A → B 전환 시:
  방법 1: TLB 전체 Flush → 모든 엔트리 무효화 → 성능 저하
  방법 2: ASID 사용 → TLB 엔트리에 ASID 태그 추가
          → ASID가 다르면 같은 VA도 다른 엔트리로 구분
          → TLB Flush 불필요!
```

#### ASID 동작

```
TLB Entry:
  +------+------+------+--------+
  | ASID | VPN  | PPN  | Attrs  |
  +------+------+------+--------+
  |  5   | 0x1  | 0x8  | RW     |  ← Process A
  |  7   | 0x1  | 0xA  | RO     |  ← Process B
  +------+------+------+--------+

  ASID = 5 (Process A) → TLB Hit → PA 0x8000
  ASID = 7 (Process B) → TLB Hit → PA 0xA000
  → 같은 VA 0x1000이지만 다른 PA로 변환
```

### 5.9 VMID (Virtual Machine Identifier) — 가상화

```
가상화 환경 (Stage 2 Translation):

  Guest OS → Stage 1: GVA → GPA (Guest Physical)
                |
                v
  Hypervisor → Stage 2: GPA → HPA (Host Physical)
                        (VMID로 VM 구분)

  TLB Entry (가상화):
    +------+------+------+------+--------+
    | VMID | ASID | VPN  | PPN  | Attrs  |
    +------+------+------+------+--------+

  → VMID + ASID + VPN으로 완전한 주소 식별
```

### 5.10 Page Table Walk 의 성능 비용

레벨이 하나 늘어날수록 DRAM 접근이 한 번씩 더 추가됩니다. DDR4 기준으로 DRAM 한 번 접근이 약 100 ns 이므로 4-level walk 는 ~400 ns 가 됩니다. 반면 TLB Hit 는 ~1 cycle(~0.5 ns) 이니 miss 와 hit 의 차이가 800배에 달합니다. 이 숫자는 추상적으로 느껴지지만, TLB miss rate 가 1% 라고 해도 effective access time 이 히트만 있을 때의 9배가 된다는 뜻입니다.

| 레벨 수 | 메모리 접근 횟수 | 대략적 시간 (DDR4) |
|---------|----------------|-------------------|
| 2-level (32-bit) | 2회 | ~200 ns |
| 3-level | 3회 | ~300 ns |
| 4-level (64-bit) | 4회 | ~400 ns |
| 5-level (57-bit VA) | 5회 | ~500 ns |

**대비**: L1 캐시 접근 = ~1 ns, TLB Hit = ~1 cycle (~0.5 ns)

→ **TLB Miss 시 Page Walk는 TLB Hit 대비 수백 배 느리다** → TLB의 중요성

### 5.11 DV 관점 — Page Table 검증 포인트

| 검증 항목 | 설명 |
|----------|------|
| Multi-level Walk 정확성 | 각 레벨 인덱스 추출 + 다음 테이블 주소 계산 |
| Block Descriptor 처리 | Level 1/2에서 Block인 경우 Walk 조기 종료 |
| Invalid PTE 처리 | Valid=0인 경우 Page Fault 생성 |
| Permission Check | AP 필드 기반 RO/RW × EL0/EL1 조합 |
| ASID 매칭 | 같은 VA, 다른 ASID → 다른 PA 매핑 확인 |
| Attribute 적용 | Cacheable/Non-cacheable/Device 속성 정확 전파 |
| Walk 중 에러 | 중간 레벨 PTE가 Invalid인 경우 → Fault 정확 보고 |

---

## 6. 흔한 오해 와 DV 디버그 체크리스트

### 흔한 오해

:::danger[❓ 오해 1 — 'Page table walk 는 1번의 메모리 read 다']
**실제**: 4-level page table = _최대 4번_ 의 메모리 read (각 level 의 table 이 메모리에 있으므로). PWC hit 가 끼면 1~3번으로 줄어들고, Block descriptor 가 끼면 한 단계 더 짧아집니다. _상한_ 은 4 (3-level Stage 2 결합 시는 더 큼).<br>
**왜 헷갈리는가**: "L1 → 데이터" 의 1-단계 매핑 직관 때문에 — 실제로는 multi-level 이 hierarchy 마다 메모리 access 추가.
:::
:::danger[❓ 오해 2 — 'Block descriptor 는 huge page 와 정확히 같다']
**실제**: Block descriptor 는 _ARMv8 의 PTE 인코딩_ 이고 (`PTE[1:0]=0b01` at L1/L2), huge page 는 _OS 추상화_ (`MAP_HUGETLB`, THP) 입니다. 둘은 _구현 ↔ 정책_ 관계 — block descriptor 없는 huge page 는 불가능하지만, block descriptor 가 있어도 OS 가 안 쓰면 huge page 가 활용되지 않습니다.<br>
**왜 헷갈리는가**: 둘 다 "큰 page" 라서.
:::
:::danger[❓ 오해 3 — 'PWC 는 단순한 TLB 의 일부다']
**실제**: PWC 는 _intermediate-level_ PTE 를 캐싱하는 별도 구조. TLB 가 cache 하는 것은 (VA→PA) 의 _최종_ 매핑이고, PWC 가 cache 하는 것은 walk _중간_ 단계의 next-level table 주소입니다. 둘은 invalidate 정책도 다를 수 있어서, TLBI 가 PWC 를 함께 무효화하는지 별도 검증이 필요합니다.<br>
**왜 헷갈리는가**: 둘 다 walk 비용을 줄이는 보조 캐시라서.
:::
:::danger[❓ 오해 4 — 'ASID 만 있으면 TLB flush 가 영원히 불필요하다']
**실제**: ASID 는 _재활용_ 이 필요합니다 (8-bit = 256개, 16-bit = 65536개). 동시에 살아있는 process 가 한도를 넘으면 OS 가 ASID rollover 시 _전체 TLB flush_ 를 강제합니다. ASID 의 효과는 "flush 빈도가 낮다" 이지 "flush 가 없다" 가 아닙니다.<br>
**왜 헷갈리는가**: 광고 문구 "TLB flush 불필요" 의 단축.
:::
:::danger[❓ 오해 5 — 'AP=11 (RO/RO) 면 EL1 도 못 쓰니까 가장 안전하다']
**실제**: AP 는 _R/W_ 만 통제. _execute_ 는 별도 비트 (UXN/PXN). AP=11 인 page 도 PXN=0 이면 EL1 이 _실행_ 가능 — 그래서 W^X (Writable XOR Executable) 를 위해서는 AP + UXN/PXN 조합을 _둘 다_ 봐야 합니다.<br>
**왜 헷갈리는가**: AP 한 필드로 _모든_ 권한이 결정된다는 단순 모델.
:::
### DV 디버그 체크리스트 (이 모듈 내용으로 마주칠 첫 실패들)

| 증상 | 1차 의심 | 어디 보나 |
|---|---|---|
| Translation Fault Level 이 항상 Level 0 | TTBR 의 base 자체가 unmapped 영역 | TTBR0/1_EL1 dump → DRAM 영역에 있는가 |
| 2 MB 영역인데 4 KB 단위로 walk 가 끝까지 감 | L2 PTE 가 Block (0b01) 이 아닌 Table (0b11) 로 잘못 셋업 | L2 PTE[1:0] 와 OutputAddr 의 [20:0] 이 0 인지 |
| Block descriptor 사용 시 PA 가 1 MB 어긋남 | PA 합성 시 OutputAddr mask 가 [47:21] 가 아닌 [47:20] | PA = OutputAddr[47:21] || VA[20:0] 공식 |
| 같은 VA 가 process 마다 다른 _PA_ 인데 TLB hit | TLB entry 에 ASID 가 안 실림 (구현 버그) 또는 nG=0 | TLB dump → ASID 필드, PTE.nG bit |
| PWC hit 후에도 walk 결과가 stale | TLBI 가 PWC 를 invalidate 안 함 | TLBI 후 PWC dump 또는 PWC invalidation 신호 |
| Huge page 와 4 KB 가 겹치는 영역에서 mismatch | TLB 가 두 size 를 동시 보유, 검색 우선순위 미정의 | TLB lookup 의 priority logic + size mask |
| AF=0 인 첫 접근에서 fault 가 두 번 발생 | HW AF update (FEAT_HAFDBS) 미지원, SW handler 가 AF 설정 누락 | ID_AA64MMFR1_EL1.HAFDBS, OS handler 의 PTE.AF=1 set |
| 4-level 인데 walk count 가 5 이상 | Stage 2 가 켜져 있어 각 stage 1 PTE read 도 stage 2 walk 필요 | VTCR_EL2.SL0 + Stage 2 가 활성인지 |

:::caution[실무 주의점 — Page Walk 중 Access Flag 미설정으로 반복 Fault]
**현상**: 처음 접근하는 페이지에서 Permission Fault가 아닌 반복적 Access Flag Fault가 발생하여 OS Handler가 무한 루프에 빠지거나 성능이 급격히 저하됨.

**원인**: ARMv8은 PTE의 AF(Access Flag) 비트가 0이면 Fault를 발생시켜 SW가 명시적으로 AF를 설정하도록 강제함. 페이지 테이블 초기화 시 AF=0으로 세팅하면 해당 페이지에 접근할 때마다 Fault가 반복 발생.

**점검 포인트**: PTE 생성 코드에서 AF 비트(bit[10]) 초기값 확인. Walk 로그에서 동일 VA에 대해 Fault → PTE 업데이트 → 재Fault가 반복되면 AF 누락 의심. `FEAT_HAFDBS`(HW AF 자동 관리) 미지원 환경에서는 SW Handler가 반드시 AF를 set해야 함.
:::
---

## 7. 핵심 정리 (Key Takeaways)

- **Multi-level 이 메모리 효율의 핵심**: Single-level 은 모든 VA 를 위해 page table 통째로 (TB 단위) 할당. Multi-level 은 사용 중인 영역의 sub-tree 만 할당.
- **ARMv8 4-level (4 KB granule)**: VA[63:48] sign-ext, [47:39] L0, [38:30] L1, [29:21] L2, [20:12] L3, [11:0] page offset. 9-bit × 4 + 12 = 48 의 _필연적_ 산수.
- **Granule trade-off**: 4 KB = 깊은 walk + fine grain, 64 KB = 얕은 walk + coarse grain. 보통 4 KB 표준, large dataset 은 16 KB / 64 KB.
- **Block descriptor (Huge page)**: 중간 레벨에서 변환 종료 → 2 MB / 1 GB 매핑. TLB 효율성 ↑ + walk 단축.
- **PWC**: 중간 레벨 PTE 캐싱 → 순차 access 의 walk 비용 40-60% 감소. 단, TLB 와 _별도_ 구조라 invalidation 정책 따로 챙겨야.
- **COW**: Write fault → OS 가 복사 + PTE update + TLBI. MMU 는 fault 감지 + 후속 walk 정확성 책임.

### 7.1 자가 점검

:::tip[🤔 Q1 — Granule 선택 (Bloom: Apply)]
4 KB / 16 KB / 64 KB 중 어느 _granule_?

<details>
<summary>정답</summary>

- **4 KB**: 표준. Fine grain, walk depth 4. 대부분 OS default.
- **16 KB**: macOS / iOS default (Apple Silicon). TLB efficiency ↑.
- **64 KB**: HPC / large dataset. Walk depth 3 (level 1 부터). TLB miss penalty ↓ but fragmentation ↑.

Trade-off: 큰 granule = 빠른 walk + 큰 TLB reach, 작은 granule = fine permission.

</details>
:::
:::tip[🤔 Q2 — Block descriptor (Bloom: Analyze)]
L2 의 _2 MB block descriptor_ vs L3 의 _4 KB page entry_. 어느 것?

<details>
<summary>정답</summary>

Workload 따라:
- **Sequential, large allocation** (예: GPU buffer): 2 MB block. Walk depth 3 (L0-L1-L2 만), TLB 한 entry 가 2 MB cover.
- **Sparse / small allocation**: 4 KB page. Block 의 _내부 4 KB_ 각각 다른 PA 필요한 경우 block 사용 불가.

</details>
:::
### 7.2 출처

**External**
- ARM ARM (Architecture Reference Manual) DDI 0487
- Intel SDM Volume 3 Chapter 4 Paging

---
## 다음 단계

- 📝 [**Module 02 퀴즈**](../quiz/02_page_table_structure_quiz/)
- ➡️ [**Module 03 — TLB**](../03_tlb/): Walk 결과를 어떻게 latency-friendly 하게 캐싱하는가, hit 1 cycle vs miss 400 ns 의 게임.

