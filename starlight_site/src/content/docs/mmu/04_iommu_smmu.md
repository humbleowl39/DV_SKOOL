---
title: "Module 04 — IOMMU / SMMU"
---

:::tip[학습 목표]
이 모듈을 마치면:

- **Distinguish** CPU MMU 와 IOMMU/SMMU 의 위치/책임 차이를 SoC 다이어그램으로 식별할 수 있다.
- **Trace** Stage 1 (VA→IPA, OS) + Stage 2 (IPA→PA, hypervisor) translation 흐름을 추적할 수 있다.
- **Apply** StreamID / SubstreamID 로 device 격리와 multi-context 를 구현하는 시나리오를 설계할 수 있다.
- **Analyze** SVM (Shared Virtual Memory) 의 동작 원리와 ATS / PRI / PASID 의 역할을 분석할 수 있다.
- **Distinguish** IOMMU page fault 의 비동기 처리와 CPU 의 동기 fault 차이를 설명할 수 있다.
- **Differentiate** IOTLB / ATC / PWC / context·PASID 캐시의 계층적 caching 구조와 각 invalidation 책임을 구분할 수 있다.
- **Evaluate** interrupt remapping, ACS/IOMMU group, vIOMMU(nested), TDISP 가 DMA-attack 위협 모델에서 어떤 공격면을 닫는지 평가할 수 있다.
:::
:::note[사전 지식]
- [Module 01-03](../01_mmu_fundamentals/)
- DMA / device 마스터 개념
- Hypervisor / virtualization 기본 (Stage 2 이해 위해)
:::
---

## 1. Why care? — 이 모듈이 왜 필요한가

### 1.1 시나리오 — _USB stick_ 으로 _커널 메모리_ 읽기

2010 년대 보안 연구: **악의적 USB device** 가 _IOMMU 없는_ system 에서 **kernel memory 전체** 를 _DMA 로_ 읽을 수 있음.

작동 원리:
- USB controller 의 **DMA**(Direct Memory Access — CPU 를 거치지 않고 장치가 직접 메모리를 읽고 쓰는 기능) 가 _bus master_(버스 마스터 — 자기 주도로 버스에 메모리 요청을 내보낼 수 있는 주체) — 임의 physical address access 가능.
- 악의적 firmware(펌웨어 — 장치 안에 내장된 저수준 소프트웨어) → DMA 로 PA 0~∞ 영역 _read_.
- Kernel 의 _secret_ (encryption key, password) 노출.

**해법: IOMMU**.
- Device 의 모든 DMA 가 _IOMMU 의 page table_ 을 거침.
- OS 가 _device 마다_ 허용된 PA 영역만 _device VA → PA_ 매핑.
- 다른 영역 접근 시도 → IOMMU 가 _차단_ + fault.

오늘날 모든 PC/모바일 SoC 에 IOMMU/SMMU 가 _필수_ — _SoC 보안의 근간_.

**SMMU 는 SoC 보안의 토대**입니다. IOMMU 없는 SoC 는 DMA master (GPU/USB/NIC) 가 시스템 메모리를 _무제한_ access — 단일 device compromise → 전체 SoC compromise. 가상화 환경에서는 Stage 2 가 hypervisor 의 메모리 격리 메커니즘 그 자체.

또한 **SVM (Shared Virtual Memory) 은 GPU/AI accelerator 의 SoC 통합 표준 트렌드** — CPU 와 device 가 같은 page table 을 공유해 `malloc()` 포인터를 그대로 GPU 가 쓰는 모델. 검증에서는 ATS/PRI 시나리오가 점점 중요해지고, 사내 RDMA-IP 의 GPU peer-memory 매핑도 같은 패턴.

---

## 2. Intuition — 도어맨 비유와 한 장 그림

:::tip[💡 한 줄 비유]
**IOMMU (SMMU)** ≈ **건물 입구의 도어맨 + 층별 출입증**.<br>
Device(DMA) 가 host RAM 을 직접 접근하면 보안 무효 — 옥상까지 누구든 들어가는 셈. IOMMU 가 _device-side page table_ 을 두어 device 가 _자기 view 의 가상 주소_ 만 보게 하고, 도어맨 (StreamID 검사) + 출입증 (SubstreamID/PASID) 으로 _누가 어느 층_ 까지 가는지를 통제합니다.<br>
**2-Stage** = 1층(OS)과 빌딩 관리실(Hypervisor) 의 _이중_ 도어. Guest OS 는 IPA 까지만 알고, 실제 PA 는 hypervisor 의 도어맨이 결정.
:::
### 한 장 그림 — DMA path 의 IOMMU 통과

```d2
direction: down

# unparsed: DEV["Device (GPU / NIC / DMA / Accel)<br/>DMA req: (StreamID, SubstreamID, IOVA, R/W)"]
SMMU: "SMMU v3" {
  # unparsed: STEP1["① StreamID → Stream Table<br/>→ STE (config)"]
  # unparsed: STEP2["② SubstreamID →<br/>Context Descriptor (S1 PT base)"]
  # unparsed: STEP3["③ IOTLB lookup"]
  # unparsed: STEP4["④ Stage 1 walk (S1 PT) → IPA"]
  # unparsed: STEP5["⑤ Stage 2 walk (S2 PT, hypervisor) → PA"]
  # unparsed: STEP6["⑥ Permission check"]
  # unparsed: STEP7["⑦ IOTLB fill"]
  # unparsed: OUT["PA + perm"]
  # unparsed: CMDQ["Command Queue<br/>(SW → SMMU 명령)"]
  # unparsed: EVTQ["Event Queue<br/>(SMMU → SW: fault, PRI, etc.)"]
}
# unparsed: BUS["Bus Fabric<br/>→ Memory Controller → DRAM"]
STEP3 { style.stroke: "#27ae60"; style.stroke-width: 3 }
DEV -> STEP1
STEP1 -> STEP2
STEP2 -> STEP3
STEP3 -> OUT: "hit"
STEP4 { style.stroke: "#c0392b"; style.stroke-width: 2; style.stroke-dash: 4 }
STEP5 { style.stroke: "#c0392b"; style.stroke-width: 2; style.stroke-dash: 4 }
STEP3 -> STEP4: "miss"
STEP4 -> STEP5
STEP5 -> STEP6
STEP6 -> STEP7
STEP7 -> OUT
OUT -> BUS: "PA + AT=Translated (옵션)"
```

### 왜 이 디자인인가 — Design rationale

세 요구가 동시에 만족돼야 했습니다.

1. **Device 마다 독립 page table** — GPU 의 DMA 가 NIC 의 buffer 영역을 못 보게 → StreamID 별 STE → 각 device 의 자기만의 view.
2. **VM 격리 (가상화)** — Guest OS 가 Stage 1 만 통제, _진짜 PA_ 는 hypervisor 의 Stage 2 가 결정 → Guest 가 다른 VM 의 메모리에 DMA 못 함.
3. **Async fault recovery** — Device 의 DMA 는 atomic 하게 멈출 수 없음 → CPU 처럼 _즉시 exception_ 이 아니라 **Event Queue + Interrupt + retry** 의 비동기 모델.

이 세 요구의 교집합이 "SMMU = StreamID 라우팅 + 2-stage walk + Command/Event queue" 의 v3 구조입니다.

---

## 3. 작은 예 — GPU 가 IOVA = 0x4_0000_1000 에 DMA write 하는 한 사이클

가장 단순한 시나리오. Guest OS(게스트 OS — 가상 머신 안에서 도는 운영체제) 의 GPU driver 가 **IOVA**(I/O Virtual Address — 장치가 보는 가상 주소; CPU 의 VA 에 해당) **= 0x0000_0004_0000_1000** (4 KB 정렬, 256 byte write) 로 DMA 를 발사. **StreamID**(스트림 ID — "어느 장치인가"를 식별하는 번호) = 0x10 (GPU), **SubstreamID**(서브스트림 ID — 한 장치 안에서 "어느 process 인가"를 식별하는 번호; PASID 에 대응) = 0x05 (process 5). Stage 1 + Stage 2 모두 enable. **IOTLB**(I/O TLB — IOMMU 안의 변환 결과 캐시) cold. 변환에 쓰는 두 데이터 구조는 **STE**(Stream Table Entry — 장치별 설정 항목)와 **CD**(Context Descriptor — process별 page table 시작 주소를 담은 항목)입니다.

### 단계별 추적

```
   GPU DMA: write @ IOVA=0x4_0000_1000, len=256, StreamID=0x10, SubstreamID=0x05
        ▼
   ┌──────────────────────────────────────────────────────────────┐
   │ ① Stream Table lookup: STE_BASE + StreamID*STE_SIZE          │
   │    STE = { Valid=1, Config=S1+S2, S1ContextPtr=0x..., S2VMID=3, │
   │            S2VTTBR=0x... }                                    │
   ├──────────────────────────────────────────────────────────────┤
   │ ② Context Descriptor lookup: S1ContextPtr + SubstreamID*CD_SZ │
   │    CD = { ASID=12, TTBR0=0x9_0000_0000, TCR.granule=4KB }     │
   ├──────────────────────────────────────────────────────────────┤
   │ ③ IOTLB lookup (StreamID=0x10, ASID=12, VPN) → MISS           │
   ├──────────────────────────────────────────────────────────────┤
   │ ④ Stage 1 Walk (Guest OS 가 setup 한 PT)                       │
   │    L0 read @ 0x9_0000_0000 + idx*8                           │
   │    L1 read → L2 read → L3 read                               │
   │    → IPA = 0x0000_0002_C000_1000                              │
   │    → AP=01 (RW), AttrIdx=2 (Normal WB)                        │
   │  ※ 각 Stage 1 PTE read 의 _주소_ 도 IPA — Stage 2 walk 필요!   │
   │     실제로는 nested walk (S1 PTE addr → S2 walk → real DRAM)  │
   ├──────────────────────────────────────────────────────────────┤
   │ ⑤ Stage 2 Walk (Hypervisor 가 setup 한 PT)                     │
   │    VTTBR = 0x..., VMID = 3                                   │
   │    L0/L1/L2/L3 walk → PA = 0x0000_0008_8000_1000             │
   │    → S2 perm check: Guest 가 RW 요청, S2 도 RW 허용 → OK     │
   ├──────────────────────────────────────────────────────────────┤
   │ ⑥ Combined permission check                                   │
   │    S1 perm (RW) ∩ S2 perm (RW) = RW → 요청 W 허용             │
   ├──────────────────────────────────────────────────────────────┤
   │ ⑦ IOTLB fill: (StreamID=0x10, ASID=12, VMID=3, VPN, PA, perm)│
   ├──────────────────────────────────────────────────────────────┤
   │ ⑧ Bus issue: DMA write to PA=0x8_8000_1000, 256 byte          │
   └──────────────────────────────────────────────────────────────┘
```

### 단계별 의미

| Step | 누가 | 무엇 | 왜 |
|---|---|---|---|
| ① | SMMU | StreamID 로 STE fetch | Device-level routing — _이 device 가 어느 context 를 쓰는가_ |
| ② | SMMU | SubstreamID 로 CD fetch | Process-level routing — SVM 시 PASID 와 같은 역할 |
| ③ | SMMU IOTLB | (StreamID, ASID, VPN) 검색 | Cache hit 이면 ④~⑥ 생략 |
| ④ | walk engine | Stage 1 PT walk (Guest OS 관리) | IOVA → IPA |
| ⑤ | walk engine | Stage 2 PT walk (Hypervisor 관리) | IPA → PA. **각 S1 PTE read 도 IPA 라 S2 walk 필요** → 최악 5×4 = 20 mem access |
| ⑥ | SMMU | S1 ∩ S2 권한 결합 | 더 제한적인 쪽 적용 |
| ⑦ | IOTLB fill | 결과 캐싱 | 다음 같은 (StreamID, IOVA) 는 hit |
| ⑧ | bus | 실제 DMA write | AT=Translated 또는 ATC 흐름 (§5.1) 으로 확장 가능 |

### 만약 Stage 1 PTE 의 V=0 이면? (vs CPU fault)

- **CPU MMU**: Synchronous Translation Fault → 현재 instr abort → handler.
- **SMMU**: DMA stall (또는 abort) → **Event Queue**(이벤트 큐 — SMMU 가 fault 같은 사건을 SW 에 알리려고 메모리에 쌓는 순환 버퍼) **에 `TRANSLATION_FAULT` 기록** → SMMU 가 GIC(Generic Interrupt Controller — ARM 의 인터럽트 분배 컨트롤러) 로 interrupt → OS 가 event 를 polling → page allocate → **Command Queue**(커맨드 큐 — SW 가 SMMU 에 명령을 전달하는 순환 버퍼) 에 `PRI_RESP` (PRI 사용 시) 또는 STE/CD update + IOTLB invalidation → Device retry.
- 즉 **fault recovery 가 비동기**.

:::note[여기서 잡아야 할 두 가지]
**(1) S1 PTE 자체의 주소도 IPA 라서 S2 walk 가 _nested_ 로 일어난다** — 그래서 worst case 가 4×5 = 20 mem access. 이게 IOTLB 의 capacity 가 가상화 환경에서 결정적인 이유. <br>
**(2) Page fault 가 Synchronous 가 아니라 Asynchronous** — Device DMA 는 이미 멈춰 있고, OS 가 _나중에_ event queue 를 읽고 처리. Recovery path 는 PRI / Stall / Abort 의 세 가지 모드로 분기.
:::
:::note[walk 이전에 _identity resolution_ 자체가 추가 메모리 비용이다]
위 worked example 에서 ①~② 단계(StreamID → STE, SubstreamID → CD)는 흔히 "라우팅" 으로만 읽고 넘어가기 쉽지만, **그 둘은 page table walk 와 별개의 추가 메모리 읽기** 입니다. STE 는 Stream Table 에서, CD 는 Context Descriptor 배열에서 각각 _DRAM_ 으로부터 fetch 되기 때문입니다. 즉 cold 상태의 전체 비용은:

```
identity resolution:  STE fetch (1) + CD fetch (1)        = 2 access  ← walk "이전"
translation walk:     2-stage nested worst case            = 20 access (§4.5)
                                                            ─────────────
                                                            합계 ≈ 22 access
```

CPU MMU 에는 ①~② 에 해당하는 단계가 아예 없습니다(CPU 는 TTBR 를 레지스터에서 바로 읽음). IOMMU 는 "어느 device 의, 어느 process 의 table 인가" 를 먼저 _메모리에서_ 풀어야 하므로 walk 이전에 이 2 access 가 항상 선행합니다. 그래서 IOMMU 는 IOTLB(최종 매핑) 외에 **STE/CD(identity) 전용 cache 를 별도로** 둘 수밖에 없습니다 — 이 identity cache 가 없으면 IOTLB miss 마다 walk 의 20 에 더해 이 2 까지 매번 물게 됩니다(자세한 계층은 §5.5).
:::
---

## 4. 일반화 — SMMU 구조, 2-Stage, StreamID

### 4.1 IOMMU 없는 vs 있는 세계

**IOMMU 없이**:

```d2
direction: right

# unparsed: CPU["CPU"]
# unparsed: MMU["CPU MMU"]
# unparsed: DMA["DMA"]
# unparsed: DRAM[("DRAM")]
CPU -> MMU: "VA"
MMU -> DRAM: "PA"
DMA { style.stroke: "#c0392b"; style.stroke-width: 3; style.stroke-dash: 4 }
DMA -> DRAM: "PA 직접 접근"
```

문제:

1. DMA 가 물리 주소를 직접 사용 → 어떤 메모리든 접근 가능
2. 악성 디바이스가 커널 메모리를 읽거나 덮어쓸 수 있음
3. 디바이스 간 격리 없음 → 한 디바이스 버그가 전체 시스템 오염
4. DMA 에 연속 물리 메모리 필요 → 대용량 DMA 버퍼 할당 어려움

**IOMMU 있을 때**:

```d2
direction: right

CPU: "CPU"
MMU: "CPU MMU"
DMA: "DMA"
IOMMU: "IOMMU\nVA→PA 변환\n+ 권한 검사\n+ 디바이스 격리"
DRAM: "DRAM" { shape: cylinder }
CPU -> MMU
MMU -> DRAM
DMA -> IOMMU
IOMMU -> DRAM
```

| 문제 | IOMMU 의 해결 |
|------|-------------|
| 무제한 메모리 접근 | Page Table 로 허용 범위 제한 |
| 디바이스 격리 없음 | StreamID 별 독립 Page Table |
| 연속 물리 메모리 필요 | 가상 연속 → 물리 불연속 매핑 |
| DMA 공격 (DMA Attack) | 권한 검사로 비인가 접근 차단 |

### 4.2 ARM SMMU v3 구조

```d2
direction: down

# unparsed: DEV["Device"]
SMMU: "SMMU v3" {
  # unparsed: ST["Stream Table<br/>→ STE (Stream Table Entry)"]
  # unparsed: S1["Stage 1 Config<br/>(Device VA → IPA)"]
  # unparsed: S2["Stage 2 Config<br/>(IPA → PA, Hypervisor)"]
  # unparsed: IOTLB["IOTLB"]
  # unparsed: CMDQ["Command Queue<br/>(SW → SMMU 명령)"]
  # unparsed: EVTQ["Event Queue<br/>(SMMU → SW 에러/이벤트 보고)"]
}
DEV -> ST: "StreamID"
ST -> S1
S1 -> S2
S2 -> IOTLB
```

### 4.3 핵심 데이터 구조

SMMU 가 DMA 요청을 처리하는 흐름은 2단계 색인 구조로 이루어집니다. 먼저 StreamID 로 Stream Table 을 찾아 "이 디바이스가 어떤 변환 모드를 쓰는가" 를 결정하고(STE), SubstreamID 로 Context Descriptor 를 찾아 "이 프로세스의 page table 기저 주소가 어디인가" 를 얻습니다(CD). 그러면 나머지는 CPU MMU 의 4-level walk 와 동일한 형식의 page table 을 따라 내려갑니다.

| 구조 | 역할 | 인덱싱 |
|------|------|--------|
| Stream Table | 디바이스별 설정의 최상위 테이블 | StreamID |
| STE (Stream Table Entry) | 디바이스별 Stage 1/2 설정 | 1 entry per device |
| CD (Context Descriptor) | 프로세스별 Page Table 포인터 | SubstreamID (PASID) |
| Page Table | 실제 VA→PA 매핑 | VPN (CPU MMU와 동일 형식) |

### 4.4 Stream Table Entry (STE) 주요 필드

```
STE:
  +----+--------+--------+----------+---------+----------+
  |Valid| Config | S1 Ctx | S1 Table | S2 Ctx  | S2 Table |
  |    | (Bypass/| Desc   | Base     | Desc    | Base     |
  |    |  S1/S2/ | Ptr    |          | Ptr     |          |
  |    |  S1+S2) |        |          |         |          |
  +----+--------+--------+----------+---------+----------+

Config 모드:
  - Bypass: 변환 없이 PA 직접 통과 (Legacy 디바이스)
  - Stage 1 Only: VA → PA (디바이스 가상화 없이)
  - Stage 2 Only: IPA → PA (Hypervisor만 관리)
  - Stage 1 + 2: VA → IPA → PA (전체 가상화)
```

### 4.5 2-Stage Translation (가상화)

가상화 환경에서는 Guest OS 가 알고 있는 "물리 주소" 가 실제로는 Hypervisor 가 할당한 IPA(Intermediate Physical Address) 입니다. SMMU 는 이 사실을 두 단계로 다룹니다. Stage 1 에서 Guest OS 가 관리하는 page table 을 써서 디바이스의 VA 를 IPA 로 변환하고, Stage 2 에서 Hypervisor 가 관리하는 page table 로 IPA 를 진짜 PA 로 변환합니다. 이때 Stage 1 의 각 PTE 주소 자체도 IPA 이므로 Stage 2 walk 가 중첩되어 발생합니다. 그 결과가 4×5=20 번의 메모리 접근이라는 최악의 비용이고, 이것이 IOTLB 의 hit rate 가 SMMU 성능의 핵심 지표가 되는 이유입니다.

```
Stage 1 (Guest OS 관리):
  Device VA (DVA) → IPA (Intermediate Physical Address)
  → Guest OS의 IOMMU 드라이버가 Page Table 관리

Stage 2 (Hypervisor 관리):
  IPA → PA (Host Physical Address)
  → Hypervisor가 VM별 메모리 격리

예시:
  VM1의 디바이스: DVA 0x1000 → IPA 0x5000 → PA 0xA000
  VM2의 디바이스: DVA 0x1000 → IPA 0x5000 → PA 0xC000
  → 같은 DVA와 IPA이지만 다른 PA (VM 격리)
```

#### Stage 1 + Stage 2 결합의 Page Walk 비용

```
최악의 경우 (4-level S1 + 4-level S2):

  S1 Level 0 → S2 Walk (4 mem access) = 4
  S1 Level 1 → S2 Walk (4 mem access) = 4
  S1 Level 2 → S2 Walk (4 mem access) = 4
  S1 Level 3 → S2 Walk (4 mem access) = 4
  Final IPA → S2 Walk (4 mem access)  = 4

  총: 4 × 5 = 20 메모리 접근!
  → IOTLB Miss 시 ~2000ns → TLB의 중요성이 극대화
```

---

## 5. 디테일 — ATS, PRI, Queue, Page Fault, SVM, 벤더별 용어

### 5.1 PCIe ATS (Address Translation Service)

**문제**: 모든 DMA 요청이 IOMMU 를 거치면 → IOMMU 가 병목.

**해결**: ATS — 디바이스 자체에 Translation Cache (ATC) 를 두어 IOMMU 우회.

```d2
shape: sequence_diagram

DEV: "Device (+ATC)"
IOMMU
MEM: "Memory"

# Note over IOMMU: Page Walk
# Note over DEV: ATC 에 저장
# Note over IOMMU: IOTLB Walk 건너뜀\nPermission 재확인은 수행
DEV -> IOMMU: "Translation Request (VA + StreamID)"
IOMMU -> DEV: "Translation Response (PA)" { style.stroke-dash: 4 }
DEV -> MEM: "DMA (PA, AT=Translated)"
```

**ATS 흐름**:

1. 디바이스가 IOMMU 에 Translation Request (VA + StreamID)
2. IOMMU 가 Page Walk → PA 반환
3. 디바이스가 ATC 에 저장
4. 이후 같은 VA → ATC Hit → PA 로 직접 DMA (IOMMU 통과만, Walk 불필요)

**IOMMU 측**:

- AT=Translated 인 DMA 는 IOTLB Walk 을 건너뜀
- 단, Permission 재확인은 수행 (보안)

:::note[AT=Translated 가 _왜_ 보안을 깨지 않는가 — 기전]
"device 가 이미 변환된 PA 를 직접 들고 온다" 면, 악성 device 가 _아무 PA 나 위조_ 해서 AT=Translated 로 보내 host 메모리를 마음대로 건드릴 수 있는 것 아닌가? — 이 우려가 풀리는 지점이 ATS 보안의 핵심입니다. AT=Translated 가 건너뛰는 것은 **translation(주소 변환) 단계뿐** 이고, **access-control(소유권·권한 검증) 단계는 건너뛰지 않습니다**.

device 가 PA 를 위조해도, IOMMU 는 그 DMA 를 보낸 device 의 StreamID 를 알고 있으므로 "이 device(이 도메인)가 _그 PA 를 가질 자격이 있는가_" 를 자신의 설정으로 검증합니다. 구체적으로는 그 device 에 대해 ATS 가 애초에 허용됐는지, 그리고 해당 PA 영역이 그 device 의 domain(Stage 2 / 격리 정책)에 속하는지를 확인합니다. device 가 _자기 도메인 밖_ 의 PA 를 위조하면 이 access-control 검증에서 걸려 차단됩니다. 즉 ATS 는 "변환을 device 에 위임" 한 것이지 "검사를 면제" 한 것이 아니므로, 위조 PA 는 단순 우회가 되지 못합니다(흔한 오해 4 참조). 별도로 남는 위험은 PA 자체의 위조가 아니라 _ATC invalidation race_ 이며, 그것은 §5.5 의 invalidation 으로 다룹니다.
:::

### 5.2 PASID — 한 device 안의 여러 주소 공간

ATS 와 PRI 를 이야기하기 전에, 그 둘이 의미를 가지려면 먼저 "이 변환이 어느 process 의 것인가" 를 식별할 수 있어야 합니다. 그 식별자가 **PASID (Process Address Space ID)** 입니다. PCIe 에서 PASID 는 **최대 20 bit** 폭을 가지므로, 하나의 device 가 동시에 거의 100 만 개에 가까운 독립 주소 공간을 호스팅할 수 있습니다. SMMU 의 SubstreamID 가 바로 이 PASID 에 대응하며, Intel/AMD 는 그대로 PASID 라고 부릅니다.

PASID 가 결정적인 이유는, 이것이 device 의 한 변환 context 를 _CPU 의 특정 process page table_ 에 직접 묶을 수 있게 해 주기 때문입니다. Stage 1 table 의 base 를 그 process 가 이미 쓰고 있는 page table 로 가리키면, accelerator 는 application 과 _똑같은 포인터_ 를 dereference 하게 됩니다. 이것이 §5.7 에서 다루는 SVM/SVA 의 토대이고, CUDA Unified Memory, OpenCL SVM, oneAPI USM 같은 CPU↔accelerator 프로그래밍 모델이 모두 이 위에 서 있습니다.

```d2
direction: down

DEV: "Device (StreamID = 0x10)"
DEV.shape: rectangle
SPACE: "한 device, 여러 PASID context" {
  P0: "PASID 0\n→ CD0 → Process A page table"
  P5: "PASID 5\n→ CD5 → Process B page table (SVM)"
  P9: "PASID 9\n→ CD9 → 전용 IOVA 공간 (legacy DMA)"
}
DEV -> SPACE
```

| 벤더 | Device 식별 | Process(sub) 식별 | 식별 테이블 체인 |
|------|------------|------------------|------------------|
| ARM SMMUv3 | StreamID | SubstreamID | Stream Table → Context Descriptor |
| Intel VT-d (scalable) | Source ID (BDF) | PASID | Root Table → Context Table → PASID Table → first-level PT |
| AMD-Vi | DeviceID (BDF) | PASID | Device Table → I/O page tables |
| RISC-V IOMMU | device_id | process_id | Device Directory → Process Directory → S1/S2 |

여기서 한 가지를 분명히 해 둘 필요가 있습니다. **device identity 를 resolve 하는 lookup 자체도 memory access** 라는 점입니다. StreamID 로 STE 를, SubstreamID 로 CD 를 읽는 것은 page table walk 와는 별개의 추가 메모리 읽기입니다. 그래서 IOMMU 는 page table 만 캐싱하는 게 아니라 이 device/context/PASID lookup 결과도 캐싱하는데, 이 계층 구조는 §5.5 에서 정리합니다.

### 5.3 PRI (Page Request Interface)

**문제**: 디바이스가 접근한 페이지가 Swap-out 되었을 때 → IOMMU Page Fault → DMA 실패 → 디바이스 에러.

**해결**: PRI — 디바이스가 OS 에 "이 페이지를 준비해달라" 요청.

```d2
shape: sequence_diagram

DEV: "Device"
IOMMU
OS

DEV -> IOMMU: "DMA (VA)"
IOMMU -> IOMMU: "Page Fault (페이지 없음)" { style.stroke-dash: 4 }
IOMMU -> OS: "Event Queue 에 Page Request 기록"
OS -> OS: "페이지 할당 / Swap-in\nPage Table 업데이트"
OS -> IOMMU: "Command Queue 에 Page Response"
IOMMU -> DEV: "완료 통지"
DEV -> IOMMU: "DMA 재시도"
IOMMU -> DEV: "성공" { style.stroke-dash: 4 }
```

**핵심**: DMA 실패 대신 "잠시 대기 후 재시도" → 디바이스와 OS 간 협력. SVM (Shared Virtual Memory) 구현의 전제 조건.

#### ATS + PRI 의 DV 검증 포인트

| 항목 | 검증 내용 |
|------|----------|
| ATC Hit | 디바이스가 캐싱된 PA로 DMA → IOMMU Walk 미발생 확인 |
| ATC Invalidation | IOMMU가 ATC Invalidation 전송 → 디바이스 ATC 엔트리 제거 |
| PRI 흐름 | Page Fault → Request → OS 응답 → DMA 재시도 → 성공 |
| PRI Timeout | OS 응답 지연 시 디바이스 타임아웃 처리 |
| AT bit 위조 | 디바이스가 AT=Translated로 거짓 PA 전송 → IOMMU가 차단하는지 |

### 5.4 SMMU Command / Event Queue 상세

#### Command Queue (SW → SMMU)

```
OS/Hypervisor가 SMMU에 명령을 전달하는 원형 버퍼:

  +--Command Queue (메모리에 위치)--+
  | CMD 0: TLBI_NH_VA (VA Inval)   |
  | CMD 1: CFGI_STE (STE 업데이트) |
  | CMD 2: SYNC (완료 동기화)      |
  | CMD 3: PREFETCH_CONFIG         |
  | ...                            |
  +---------------------------------+

  SW → SMMU.CMDQ_PROD (Producer 포인터) 업데이트
  SMMU: Consumer 포인터에서 읽어 처리
  SYNC 명령: 이전 명령들이 모두 완료될 때까지 대기

주요 명령:
  - TLBI_*: TLB Invalidation (VA, ASID, VMID 등)
  - CFGI_*: Configuration Invalidation (STE, CD 변경 반영)
  - SYNC: Barrier (이전 명령 완료 보장)
  - PREFETCH_CONFIG: STE/CD 프리페치
  - ATC_INV: 디바이스 ATC 무효화 (ATS 사용 시)
  - PRI_RESP: PRI Page Response
```

#### Event Queue (SMMU → SW)

```
SMMU가 SW에 에러/이벤트를 보고하는 원형 버퍼:

  +--Event Queue (메모리에 위치)--+
  | EVT 0: TRANSLATION_FAULT      |
  | EVT 1: PERMISSION_FAULT       |
  | EVT 2: EXTERNAL_ABORT         |
  | ...                           |
  +--------------------------------+

  SMMU: 이벤트 발생 → EVT Queue에 기록 + SMMU.EVTQ_PROD 업데이트
  SW: Consumer 포인터에서 읽어 처리 + SMMU.EVTQ_CONS 업데이트

  인터럽트: SMMU → GIC에 이벤트 인터럽트 전송 → SW가 폴링

이벤트 정보:
  - StreamID (어떤 디바이스)
  - SubstreamID (어떤 프로세스)
  - 실패한 VA
  - Fault 타입 + 원인
```

**DV 핵심**: Command/Event Queue는 원형 버퍼이므로, Wrap-around, Full/Empty 경계, Producer/Consumer 포인터 동기화를 집중 검증해야 한다.

### 5.5 IOMMU caching 계층 — IOTLB 만 있는 게 아니다

address translation 이 현실적으로 가능한 유일한 이유는 거의 모든 lookup 이 어떤 cache 에 hit 하기 때문입니다. CPU MMU 가 TLB 한 종류로 끝나지 않듯, IOMMU 는 자신이 walk 하는 _구조마다_ 대응하는 cache 를 둡니다. 이 계층을 한 장으로 정리하면 다음과 같습니다.

```d2
direction: down

REQ: "Device DMA\n(StreamID, PASID, IOVA)"
DC: "**Device / Context cache**\nStreamID→STE, PASID→CD\nidentity resolution 캐싱"
IOTLB: "**IOTLB (paging cache)**\nIOVA → PA 최종 매핑\nthe hot path"
PWC: "**PWC (page-walk cache)**\n중간 레벨 descriptor(L4/L3/L2)\nnested walk 부분 재시작"
ATC: "**ATC (Address Translation Cache)**\ndevice 내부 cache (ATS)\nIOTLB 압력을 endpoint 로 분산"
MEM: "DRAM\n(STE / CD / page tables)" { shape: cylinder }

REQ -> DC: "miss"
DC -> IOTLB
IOTLB -> PWC: "leaf miss"
PWC -> MEM: "남은 레벨만 read"
REQ -> ATC: "ATS: device-local hit\n(IOMMU translate stage 우회)"
```

각 cache 의 역할은 다음과 같이 나뉩니다.

| Cache | 무엇을 캐싱 | 왜 필요 | 누가 invalidate |
|-------|-----------|---------|----------------|
| Device/Context cache, PASID cache | StreamID→STE, PASID/SubstreamID→CD 의 identity lookup | miss 마다 STE/CD 를 DRAM 에서 다시 읽지 않기 위해 | STE/CD 변경 시 SW (`CFGI_STE`/`CFGI_CD`) |
| IOTLB (paging cache) | 최종 IOVA→PA + perm | 매 DMA 마다 walk 회피 — hot path | unmap/remap 시 SW (`TLBI_*`) |
| PWC (page-walk / paging-structure cache) | walk 의 _중간_ 레벨 descriptor | leaf miss 시 root 부터가 아니라 _도중부터_ 재시작 — 특히 nested(2-stage) walk 가 cold 일 때 ~20 access 를 크게 줄임 | 해당 레벨 매핑 변경 시 |
| ATC (device 측, ATS) | device 가 받아 둔 IOVA→PA | 중앙 IOTLB 의 병목을 endpoint 들로 분산 | unmap 시 device 에 `ATC_INV` (Invalidate Request) 전송 후 SYNC |

여기서 핵심 통찰은 **PWC 가 nested walk 의 비용을 직접 깎는다** 는 점입니다. §4.5 에서 2-stage cold walk 가 최악 4×5 = 20 memory access 였는데, PWC 에 상위 레벨 descriptor 들이 남아 있으면 walker 는 root 가 아니라 중간부터 다시 내려갈 수 있습니다. 그래서 가상화 환경에서는 IOTLB hit rate 뿐 아니라 _양쪽 stage_ 의 PWC, 그리고 huge page(2 MB/1 GB) block 매핑이 함께 성능을 결정합니다.

#### Invalidation — 가장 어려운 부분이자 보안의 핵심

CPU TLB 는 소유한 core 가 _스스로_ 무효화하지만, IOMMU 의 cache 들은 여러 주체가 공유하므로 **mapping 이 바뀔 때마다 SW 가 명시적으로 invalidate** 해야 합니다. 이것이 단순한 성능 문제가 아니라 _correctness 와 security 가 동시에 걸린_ 문제인 이유는 다음과 같습니다. 어떤 페이지를 device 에게서 unmap 했는데 IOTLB(또는 device 의 ATC)에 옛 IOVA→PA 매핑이 남아 있으면, 이미 해제(free)되어 다른 용도로 재할당된 물리 페이지를 그 device 가 여전히 DMA 로 건드릴 수 있습니다. 즉 **stale IOTLB entry = freed page 가 DMA 로 reachable** — use-after-free 형태의 메모리 침해입니다.

그래서 모든 unmap 은 다음 두 단계를 _반드시_ 짝지어야 합니다.

```
1. TLBI_* / ATC_INV  ← 해당 매핑을 IOTLB 와 (ATS device 면) ATC 에서 제거
2. SYNC              ← 위 invalidation 이 device 까지 완료됐음을 보장하는 fence
```

`SYNC` 가 완료되기 _전에_ 그 물리 페이지를 재할당하면 race 가 열립니다. 이 invalidation round-trip(특히 ATC 까지 가는 경우)이 **unmap latency** 의 실체이고, streaming networking 처럼 map/unmap 이 고빈도인 워크로드에서 IOMMU 의 가장 큰 성능 비용으로 나타납니다. 완화책은 deferred/batched unmap, persistent mapping, 그리고 pinning churn 을 줄이는 PRI 입니다.

:::caution[DV 검증 포인트 — invalidation race]
unmap 시나리오에서 `TLBI`/`ATC_INV` → `SYNC` 의 _순서와 짝_ 을 검증하라. 특히 (1) `SYNC` 없이 다음 명령이 진행되는 경우, (2) `ATC_INV` 의 completion 이 오기 전에 device 가 옛 PA 로 DMA 하는 경우, (3) page 재할당이 `SYNC` 완료 전에 일어나는 경우를 음성 시나리오로 주입해 stale-access 가 차단되는지 확인하라.
:::

### 5.6 IOMMU Page Fault 처리 — CPU Page Fault와의 차이

CPU 의 page fault 는 "지금 이 instruction 이 실패했다" 는 동기적 이벤트입니다. CPU 가 멈추고 handler 가 실행되고 복구되면 같은 instruction 을 재실행합니다. 그런데 디바이스 DMA 는 이미 수십~수백 byte 의 burst 를 시작한 상태에서 fault 가 걸립니다. 멈추고 재실행한다는 개념 자체가 맞지 않습니다. 그래서 IOMMU 는 fault 를 Event Queue 에 기록하고 interrupt 를 올리는 것으로 끝나고, OS 가 queue 를 polling 해 원인을 파악한 뒤 page 를 준비하거나 디바이스에 abort 를 알리는 비동기 모델을 씁니다.

:::note[DMA 가 "atomic 하게 못 멈춘다" 는 것의 물리적 근거]
비동기 fault 모델은 임의의 설계 선택이 아니라 _DMA 의 물리적 성질_ 에서 강제됩니다. CPU 명령은 retire 되기 전까지는 아키텍처 상태에 반영되지 않으므로 exception 시 그 명령을 _취소하고 재실행_ 할 수 있는 명확한 단위(instruction boundary)가 있습니다. 반면 device 의 DMA 는 PCIe 의 경우 **TLP(Transaction Layer Packet)** 단위로 쪼개져, fault 가 인지되는 시점엔 이미 여러 TLP 가 link 위(wire)에 올라가 fabric 을 통과 중인 _in-flight_ 상태입니다.

핵심은 이 in-flight burst 에는 CPU 명령 같은 **retire/replay 경계가 존재하지 않는다** 는 점입니다 — 이미 wire 에 나간 패킷을 "없던 일" 로 되돌릴 방법이 없고, 일부 byte 는 이미 메모리에 쓰였을 수도 있습니다. 따라서 "fault 났으니 burst 전체를 atomic 하게 멈추고 처음부터 다시" 라는 CPU식 모델이 물리적으로 성립하지 않습니다. 그래서 IOMMU 는 _부분 진행을 보존_ 하면서(Stall) 또는 _device 에게 처음부터 다시 시도할 책임을 넘기면서_(Abort) 비동기로 복구할 수밖에 없는 것입니다. 흔한 오해 3 의 "burst 재시작 시 byte 중복 write" 가 바로 이 retire 경계 부재의 직접적 귀결입니다.
:::

```
CPU Page Fault:
  CPU → Exception → 현재 명령어 중단 → OS Handler → 복구 → 명령어 재실행
  → 동기적 (synchronous): 현재 실행 흐름이 멈춤

IOMMU Page Fault:
  디바이스 DMA → IOMMU Fault → Event Queue에 기록 → 인터럽트
  → 비동기적 (asynchronous): 디바이스 DMA는 이미 실패/대기 중
  → OS가 Event Queue에서 읽고 처리 후 → 디바이스에 통지 필요

  복구 옵션:
  1. Stall 모드: DMA를 멈추고 대기 → OS가 페이지 할당 → DMA 재개
     (PRI와 유사하지만 SMMU 내부에서 Stall)
  2. Abort 모드: DMA 실패 → 디바이스에 에러 반환 → 디바이스가 재시도
  3. 무시: Fault를 Event Queue에만 기록 (디버그용)
```

| 항목 | CPU Page Fault | IOMMU Page Fault |
|------|---------------|-----------------|
| 동기성 | 동기적 (Exception) | 비동기적 (Event Queue + 인터럽트) |
| 처리 주체 | OS Handler (즉시) | OS (Event Queue 폴링) |
| 재시도 | CPU가 자동 재실행 | Stall 해제 또는 디바이스 재시도 |
| 복잡도 | 단순 (CPU 파이프라인 제어) | 복잡 (디바이스 동기화 필요) |
| DV 초점 | Fault → Handler → 재실행 | Fault → Event → OS 응답 → DMA 재개 |

### 5.7 SVM / SVA — Shared Virtual Memory

```
SVM (Shared Virtual Memory) / SVA (Shared Virtual Addressing):
  디바이스가 CPU와 같은 가상 주소 공간을 공유

  기존: CPU VA 세계 ↔ IOMMU VA 세계 (별개)
       → SW가 VA→PA 변환 후 PA를 디바이스에 전달 (pin + map)

  SVM: CPU와 디바이스가 같은 Page Table 공유
       → 디바이스가 CPU의 VA를 직접 사용
       → pinning/mapping 불필요 → 프로그래밍 모델 단순화

  전제 조건:
  - IOMMU가 CPU의 Page Table을 사용 (같은 형식)
  - ATS로 디바이스 측 Translation 캐싱
  - PRI로 Page Fault 시 OS 협력
  - ASID/PASID로 프로세스 구분

  활용:
  - GPU가 CPU의 malloc() 포인터를 직접 사용
  - 가속기가 OS 관리 메모리를 직접 접근
  - 별도 DMA 버퍼 할당/복사 불필요 → 성능 + 편의성
```

SVM 이 성립하려면 앞서 본 세 조각이 _모두_ 맞물려야 한다는 점을 다시 짚어 두는 게 좋습니다. PASID(§5.2)로 device 의 한 context 를 process 에 묶고, Stage 1 table 의 base 를 그 process 의 page table 로 가리켜 같은 포인터를 쓰게 하고, ATS(§5.1)로 변환을 device 측에 캐싱하고, PRI(§5.3)로 아직 메모리에 없는 페이지를 demand-page 합니다. 그래서 실무에서 "SVA 를 지원한다" 는 말은 사실상 **ATS + PRI + PASID 를 모두 구현했다** 는 뜻입니다.

### 5.8 Interrupt remapping, ACS, 그리고 confidential computing

IOMMU 가 막는 것은 DMA *데이터* 경로만이 아닙니다. device 가 일으키는 **interrupt** 역시 공격면입니다. MSI/MSI-X 인터럽트는 결국 device 가 특정 주소에 메모리 write 를 하는 형태이므로, 통제가 없으면 악성 device 가 _임의의 vector_ 를 _임의의 CPU_ 에 주입해 권한 상승이나 DoS 를 일으킬 수 있습니다. IOMMU 는 **Interrupt Remapping Table** 을 통해 MSI/MSI-X write 를 검증·재매핑하여 이 injection/escalation 경로를 닫습니다.

여기에 더해, IOMMU 의 격리가 _실제로_ 강제되려면 device 들 사이의 peer-to-peer 라우팅도 통제돼야 합니다. 두 function 이 IOMMU 를 거치지 않고 서로 직접 P2P 통신을 할 수 있으면 격리가 무의미해지기 때문입니다. PCIe **ACS (Access Control Services)** 가 이 P2P 라우팅을 제어하며, ACS 의 가능 여부가 곧 Linux 의 **IOMMU group** 단위를 결정합니다. IOMMU group 은 "독립적으로 한 VM 에 assign 할 수 있는 가장 작은 device 집합" 이고, ACS 가 부족하면 여러 device 가 한 group 으로 묶여 개별 passthrough 가 불가능해집니다.

```d2
direction: down

DEV: "Malicious / buggy device"
IRT: "Interrupt Remapping Table\n(MSI/MSI-X 검증·재매핑)"
ACS: "ACS\n(peer-to-peer 라우팅 통제\n→ IOMMU group 경계 결정)"
CPU: "CPU (허용된 vector 만)"
PEER: "다른 function\n(P2P 차단/허용 결정)"

DEV -> IRT: "MSI write"
IRT -> CPU: "검증된 vector 만 전달"
DEV -> ACS: "P2P 요청"
ACS -> PEER
```

마지막으로, hypervisor 자체를 신뢰할 수 없는 위협 모델(confidential computing)에서는 device-level 신뢰까지 확장하는 **TDISP (TEE Device Interface Security Protocol)** 가 등장합니다. 이때 IOMMU 는 hostile hypervisor 가 있더라도 confidential VM 의 DMA 가 격리되도록 보장하는 _trusted path_ 의 일부가 됩니다. DV 관점에서 이는 IOMMU 의 격리 검증 범위가 "버그 있는 device" 에서 "신뢰할 수 없는 상위 SW" 로 넓어진다는 의미입니다.

:::caution[DV 검증 포인트 — 인터럽트와 P2P]
(1) device 가 remapping table 에 없는 MSI vector 를 위조했을 때 IOMMU 가 차단하는지, (2) ACS 가 비활성인 두 function 사이의 P2P write 가 격리 정책을 우회하지 않는지, (3) pre-boot 구간처럼 IOMMU 가 _아직 프로그래밍되기 전_ 의 DMA window 가 노출되지 않는지를 음성 시나리오로 점검하라.
:::

### 5.9 vIOMMU 와 nested IOMMU translation

Guest 가 _자기 자신의_ IOMMU 를 갖고 싶을 때(예: guest 안에서 또 다른 DMA 보호를 하거나 nested device assignment 를 할 때) platform 은 **vIOMMU (virtualized IOMMU)** 를 노출합니다. 이때 guest 가 구성한 IOMMU page table 은 Stage 1 에 해당하고, 그것이 다시 host 의 Stage 2 로 변환됩니다 — 이것이 **nested IOMMU translation**, 즉 §4.5 의 2-stage CPU paging 의 I/O 판본입니다. 이 구조 덕분에 VM 이 passthrough 받은 device 를 _소유_ 하면서도 여전히 host 에 의해 격리될 수 있습니다.

```d2
direction: down

GUEST: "Guest IOMMU page tables\n(= Stage 1, guest 가 관리)"
HOST: "Host Stage 2\n(IPA → PA, hypervisor 가 관리)"
PA: "Host PA" { shape: cylinder }
GUEST -> HOST: "guest IOMMU table access 자체도\nIPA → host Stage 2 변환 대상"
HOST -> PA
```

핵심은 §4.5 의 nested CPU 2-stage 와 정확히 같은 비용 구조가 _device 측에서도_ 반복된다는 점입니다. guest 의 IOMMU table walk 의 각 단계가 다시 host Stage 2 로 변환되므로 walk depth 가 곱해지고, 그만큼 IOTLB/PWC 의 압력이 더 커집니다. DV 에서는 이 nested 구성에서 guest 가 host 또는 다른 VM 의 PA 에 닿을 수 없음을 (Stage 2 가 차단) 검증하는 것이 핵심 음성 시나리오입니다.

### 5.10 IOMMU 보안 기능 — 격리와 DMA 공격 방어

#### DMA 공격 방어

```
DMA 공격 시나리오 (IOMMU 없이):

  악성 PCIe 디바이스 → DMA로 커널 메모리 직접 읽기/쓰기
  → 커널 코드 변조, 비밀 데이터 탈취

IOMMU 방어:
  악성 디바이스의 DMA 요청
    → IOMMU: StreamID 확인 → Page Table 검사
    → 허용 범위 밖 → Transaction Fault → 차단
```

#### 디바이스 격리

```
Device A (NIC): StreamID = 5 → Page Table A → 자신의 DMA 버퍼만 접근 가능
Device B (GPU): StreamID = 7 → Page Table B → 자신의 VRAM/버퍼만 접근 가능

→ Device A의 버그/악성 동작이 Device B의 메모리에 영향 없음
```

#### Pre-boot DMA 보호 — IOMMU 가 켜지기 _전_ 의 구멍

IOMMU 가 모든 DMA 를 검사한다는 것은 _IOMMU 가 프로그래밍된 이후_ 에만 참입니다. 부팅 초기, firmware/bootloader 가 아직 IOMMU 의 translation table 을 세팅하기 전 구간에는 DMA 가 무방비로 노출됩니다. Thunderbolt/PCIe 를 통한 "evil maid" DMA 공격(외부에서 device 를 꽂아 부팅 직후 메모리를 덤프)이 노리는 지점이 바로 이 window 입니다. 그래서 현대 platform 은 pre-boot DMA protection(부팅 시작 시점부터 IOMMU 를 enable 한 상태로 두는 정책)을 둡니다. DV 관점에서는 reset 직후 STE/Device Table 이 _default-deny_ (모든 unmapped DMA 차단) 인지, 그리고 SW 가 명시적으로 매핑하기 전까지 그 상태가 유지되는지가 검증 포인트입니다.

### 5.11 IOMMU 용어 — 벤더별 차이

| 개념 | ARM (SMMU) | Intel (VT-d) | AMD (AMD-Vi) | Samsung (sysMMU) |
|------|-----------|-------------|-------------|-----------------|
| IOMMU 이름 | SMMU | VT-d IOMMU | AMD-Vi | sysMMU |
| Device ID | StreamID | Source ID (BDF) | DeviceID | Master ID |
| Process ID | SubstreamID | PASID | PASID | - |
| Stage 1 Table | Context Descriptor | - | - | - |
| Stage 2 Table | VTTBR | EPT (Extended PT) | NPT (Nested PT) | - |
| TLB | IOTLB | IOTLB | IOTLB | TLB |

**면접 팁**: 면접관이 "sysMMU"라고 하면 삼성, "SMMU"라고 하면 ARM 표준, "VT-d"라고 하면 Intel 환경임을 즉시 인식하라. 개념은 동일하되 용어만 다르다.

여기에 개방형 **RISC-V IOMMU** 표준을 더하면 이 디자인이 ISA 를 넘어 _수렴_ 했음이 분명해집니다. RISC-V IOMMU 도 동일하게 device-directory → process-directory(PASID) → Stage 1/Stage 2 의 체인을 정의합니다. 즉 "device 식별 테이블 → process(PASID) 식별 테이블 → 2-stage page table" 이라는 구조는 ARM/Intel/AMD/RISC-V 가 모두 같으며, 벤더 간 차이는 이름과 비트 레이아웃에 국한됩니다. DV 입장에서 이 수렴은 한 IOMMU 에서 익힌 검증 패턴(identity-resolution 검증, 2-stage 격리 음성 시나리오, invalidation race)이 다른 벤더에도 거의 그대로 이식된다는 뜻입니다.

### 5.12 SoC 통합 관점 — sysMMU (삼성)

SoC 내부 IP 구성:

```d2
direction: right

IPA: "IP_A\n(예: DMA)"
IPB: "IP_B\n(예: GPU)"
SMA: "sysMMU\n(A용)"
SMB: "sysMMU\n(B용)"
BUS: "Bus Fabric"
MEM: "Memory" { shape: cylinder }
IPA -> SMA
SMA -> BUS
BUS -> MEM
IPB -> SMB
SMB -> BUS
```

특징:

- IP 별로 독립적인 sysMMU 인스턴스
- 각 sysMMU 가 해당 IP 의 주소 변환 + 접근 제어
- 커널 드라이버가 각 sysMMU 의 Page Table 관리

#### SoC 검증에서 sysMMU 의 중요성 — 공통 인프라 IP 의 원리

sysMMU 같은 IOMMU 류는 **SoC 의 거의 모든 DMA-capable IP 에 공통으로 연결되는 인프라 IP** 라는 특성을 가집니다. NIC, GPU, 코덱, DMA 엔진처럼 서로 다른 기능 블록이 _저마다_ sysMMU 를 거쳐 메모리에 닿기 때문에, sysMMU 는 한 IP 의 기능이 아니라 _전체 SoC 가 공유하는 횡단(cross-cutting) 관심사_ 입니다. Security/Access Control, DVFS(전력) 같은 다른 공통 IP 들도 같은 성격을 갖습니다.

이 "공통성" 이 검증에서 함정이 되는 이유는 분명합니다. 각 IP 팀은 _자기 블록_ 의 기능 검증에 집중하느라, 그 블록이 sysMMU 를 _올바르게_ 통과하는지(매핑·권한·invalidation)는 누구의 명시적 책임도 아닌 _틈_ 에 빠지기 쉽습니다. 그 결과 개별 IP 단위 검증은 모두 통과해도, **integration 단계에서 비로소 DMA 변환 오류·접근 실패가 한꺼번에 드러나는** 패턴이 반복됩니다. 그래서 공통 인프라 IP 는 IP-level 검증과 별개로 _SoC-level integration 검증_ 에서 모든 master 의 sysMMU 경로를 체계적으로 sweep 하는 것이 원칙입니다 — 누락이 "사람이 빠뜨리기 쉬운 공통 경로" 에서 나오기 때문입니다.

---

## 6. 흔한 오해 와 DV 디버그 체크리스트

### 흔한 오해

:::danger[❓ 오해 1 — 'IOMMU = MMU 의 단순 복제']
**실제**: IOMMU 는 추가로 **StreamID 라우팅**, **2-stage 결합**, **ATS / PRI**, **Command/Event queue**, **PASID 기반 multi-context** 등 device-side 특화 기능을 가집니다. 단순 복제가 아니라 _device 영역 특화 변형_. SMMU spec (IHI 0070) 은 ARMv8 ARM 과 별도 문서.<br>
**왜 헷갈리는가**: "이름이 같은 패밀리 = 동일 동작" 이라는 가정.
:::
:::danger[❓ 오해 2 — 'Stage 2 만 켜면 Guest 가 자기 PA 를 자유롭게 쓸 수 있다']
**실제**: Stage 2 만 켜고 Stage 1 을 bypass 하면 _Guest 가 IPA = PA 처럼 직접 다룸_ — 즉 _Guest 가 host PA 를 알게 됨_. Hypervisor 격리가 Stage 2 의 _존재_ 만으론 안 되고, _Stage 1 도 적절히 통제_ 되거나, Bypass mode 가 안전한 device 에만 허용돼야 합니다.<br>
**왜 헷갈리는가**: "S2 = hypervisor 격리" 라는 단순화.
:::
:::danger[❓ 오해 3 — 'IOMMU page fault 도 CPU 처럼 instr 단위 retry 가능']
**실제**: Device 의 DMA 는 _atomic instruction 단위가 아닌 burst_. Fault 시 처음부터 다시 시작하면 이미 transfer 한 byte 가 _두 번_ 쓰일 수 있음. 그래서 PRI / Stall 모드가 _부분 진행_ 을 보존하면서 OS 협력으로 복구하는 모델을 정의합니다. Abort 모드는 device 의 driver 가 _처음부터_ 재시도하는 책임을 짐.<br>
**왜 헷갈리는가**: CPU exception model 의 mental projection.
:::
:::danger[❓ 오해 4 — 'ATS 가 켜져 있으면 보안이 떨어진다']
**실제**: ATS 의 AT=Translated 는 _IOTLB 우회_ 일 뿐, **Permission check 는 항상 IOMMU 에서 수행** (또는 ATC 가 cache 한 perm 으로). 디바이스가 거짓 AT=Translated 를 보내도 IOMMU 가 access control reg 로 검증 가능. 따라서 ATS 자체는 보안 약점이 아님 — 단, ATC invalidation race 는 _별도_ 검증 필요.<br>
**왜 헷갈리는가**: "IOMMU 통과 안 함" 을 "검사 안 함" 으로 단축.
:::
:::danger[❓ 오해 5 — 'IOTLB 는 그냥 작은 TLB']
**실제**: IOTLB 는 (StreamID, SubstreamID, ASID, VMID, VPN) 의 _복합 키_ 로 indexing — CPU TLB (ASID, VMID, VPN) 보다 키 폭이 큼. 또 _entry size_ 도 다양 (4 KB, 2 MB, 1 GB) 이고 device traffic pattern (sequential burst) 가 CPU 와 달라 _replacement 정책_ 도 다른 게 보통. "그냥 TLB" 가 아닙니다.<br>
**왜 헷갈리는가**: 이름이 비슷.
:::
### DV 디버그 체크리스트 (이 모듈 내용으로 마주칠 첫 실패들)

| 증상 | 1차 의심 | 어디 보나 |
|---|---|---|
| Bypass mode 에서 DMA 가 fault | STE.Config 가 Bypass 가 아닌 S1 또는 S2 로 잘못 셋업 | STE dump 의 Config field |
| Stage 1 정상이지만 PA 가 다른 VM 의 영역 | Stage 2 가 bypass 또는 미설정 | STE.S2_CFG, VTTBR 값, VMID |
| Event queue overflow → fault 손실 | EVTQ_PROD 가 wrap 후 SW 가 못 따라옴 | EVTQ_CONS 갱신, IRQ rate |
| ATC invalidation 후에도 device 가 옛 PA 사용 | ATC_INV 의 SYNC 누락 | Command queue 의 `ATC_INV ...; SYNC` 짝 |
| PRI page response 후에도 device 가 retry 안 함 | PRI_RESP 의 ResponseCode field 가 Failure | PRI_RESP body, OS 의 page allocation 결과 |
| 같은 Process 의 다른 device 가 다른 ASID 사용 | StreamID 별 CD 가 SubstreamID 매핑이 incon | CD dump, OS 의 PASID alloc 정책 |
| GPU SVM 에서 host page 가 swap 후 GPU stall | PRI 미사용 + page fault on stall mode | STE.S1_CFG 의 PRI Enable, OS handler |
| Multi-VM 에서 한 VM 의 IOTLB invalidation 이 다른 VM 영향 | TLBI 가 VMID scope 안 씀 | `TLBI_NH_*` vs `TLBI_S2_*` 명령 종류 |

:::caution[실무 주의점 — Stage 2 미설정 시 Guest 메모리 격리 무효화]
**현상**: 가상화 환경에서 Guest OS가 Stage 2 변환 없이 IPA를 그대로 PA로 사용하게 되어, 다른 Guest 또는 Hypervisor 메모리 영역에 DMA 접근 가능.

**원인**: SMMU의 Two-Stage 변환에서 Stage 1(Guest OS 제어)만 활성화하고 Stage 2(Hypervisor 제어)를 bypass 상태로 두면 Guest가 임의의 PA를 지정한 DMA로 시스템 전체 메모리에 접근할 수 있음. Hypervisor 초기화 시 모든 Stream에 대해 Stage 2 Context Descriptor를 설정해야 함.

**점검 포인트**: SMMU CD(Context Descriptor)에서 `S2_CFG` 필드가 `0b00`(bypass)이 아닌지 확인. DV 시나리오에서 Guest DMA 주소에 Hypervisor 메모리 범위 PA를 주입했을 때 SMMU가 Abort를 생성하는지 검증.
:::
---

## 7. 핵심 정리 (Key Takeaways)

- **SMMU = SoC-level MMU**: DMA master (GPU/NIC/DMA/가속기) 의 system memory access 를 _가상화·격리_. 없으면 단일 device 가 전체 SoC 를 위협.
- **Two-stage translation**: Stage 1 (OS, VA→IPA) + Stage 2 (hypervisor, IPA→PA). 가상화 환경의 표준. 최악 5×4 = 20 mem access.
- **StreamID + SubstreamID 로 device + process 식별**: SoC 내 모든 device master 가 고유 StreamID, 한 device 의 여러 process 는 SubstreamID/PASID 로 구분.
- **SVM = ATS + PRI + PASID**: device 가 CPU 의 VA 를 그대로 사용 — pin/map 불필요. PASID(최대 20 bit)로 device 의 한 context 를 process page table 에 묶고, ATS 로 변환 caching, PRI 로 demand paging. CUDA UVM/OpenCL SVM/oneAPI USM 의 토대.
- **caching 은 계층적**: IOTLB(최종 매핑)만이 아니라 PWC(중간 레벨 — nested walk 비용 절감), device/context/PASID cache(identity lookup), ATS 의 ATC(device 측 분산 cache)가 함께 동작.
- **invalidation = correctness + security**: stale IOTLB/ATC entry = freed page 가 DMA 로 reachable(use-after-free). 모든 unmap 은 `TLBI`/`ATC_INV` → `SYNC` 짝이 필수이고, 이 round-trip 이 unmap latency 의 실체.
- **Page fault 는 비동기**: CPU 와 달리 event queue + interrupt + retry. Stall / Abort / PRI 의 세 모드. Recovery path 가 _device-OS 협력_ 으로 길어짐.
- **데이터 경로 너머의 방어**: interrupt remapping(MSI 위조 차단), ACS/IOMMU group(P2P 통제·assign 단위), vIOMMU/nested(guest IOMMU 를 host Stage 2 로 다시 변환), pre-boot DMA protection, TDISP(hostile hypervisor 모델).
- **벤더 용어 매핑·수렴**: ARM SMMU StreamID = Intel SourceID = AMD DeviceID = RISC-V device_id. device-dir → process-dir(PASID) → S1/S2 구조가 모든 ISA 에 수렴 — 개념은 같고 이름만 다름.

### 7.1 자가 점검

:::tip[🤔 Q1 — Two-stage translation 비용 (Bloom: Analyze)]
SMMU two-stage (S1 + S2) 의 worst-case page walk 가 _5×4 = 20_ memory access 인 이유?
<details>
<summary>정답</summary>

Nested page walk:
- S1 walk: 4 level → 4 memory access (VA → IPA).
- 그러나 각 S1 PT 의 PA 도 _IPA_ → 각 S1 단계마다 S2 walk 필요 → 4 + 1 (final IPA→PA) = 5 IPA 가 S2 walk 필요.
- 각 S2 walk = 4 memory access → 5 × 4 = 20.
- 그래서 IOTLB / PWC / Caching translation 가 _필수_ 최적화 — 매 access 마다 20 mem 은 unacceptable.
- 결론: SMMU 성능 KPI = IOTLB hit rate.

</details>
:::
:::tip[🤔 Q2 — Stage 2 bypass 위험 (Bloom: Evaluate)]
Guest VM 의 SMMU CD 에서 `S2_CFG = bypass`. 어떤 보안 사고가?
<details>
<summary>정답</summary>

Guest 가 host RAM 직접 접근:
- **공격 시나리오**: Guest 의 DMA 가 IPA → _S2 변환 없음_ → IPA 가 그대로 PA 로 해석 → host kernel memory 영역 PA 주입 시 host RAM 침해.
- **격리 무력화**: Guest 가 hypervisor 메모리 또는 _다른 VM_ 의 RAM 을 읽기/쓰기.
- **검증 의무**: Guest DMA 주소 == hypervisor 영역 PA 시 SMMU Abort 발생하는지 음성 시나리오.
- **방어**: SMMU CD 의 S2_CFG 가 _절대_ bypass 되지 않도록 hypervisor 코드 audit + DV SVA.

</details>
:::
:::tip[🤔 Q3 — Stale IOTLB 의 보안 의미 (Bloom: Analyze)]
어떤 페이지를 device 에서 unmap 한 직후 그 물리 페이지가 다른 용도로 재할당됐다. IOTLB(또는 device 의 ATC)에 옛 매핑이 남아 있으면 무슨 일이 생기며, 이를 막는 명령 시퀀스는?
<details>
<summary>정답</summary>

stale entry = freed page 가 여전히 DMA 로 reachable:
- **위협**: unmap 했어도 IOTLB/ATC 에 옛 IOVA→PA 가 남으면, device 가 이미 해제·재할당된 물리 페이지를 그 IOVA 로 계속 read/write — use-after-free 형태의 메모리 침해이자 정보 유출.
- **그래서 invalidation 은 성능이 아니라 correctness/security 문제** — CPU TLB 와 달리 owner 가 스스로 비우지 않으므로 SW 가 명시적으로 무효화해야 함.
- **올바른 시퀀스**: `TLBI_*`(IOTLB) + ATS device 면 `ATC_INV`(device 측) → 그 다음 `SYNC` 로 device 까지 완료를 fence. _이 SYNC 가 완료된 뒤에야_ 물리 페이지를 재할당해야 race 가 닫힌다.
- **검증**: `SYNC` 누락, `ATC_INV` completion 이전의 옛-PA DMA, SYNC 전 재할당의 세 가지를 음성 시나리오로 주입.

</details>
:::
### 7.2 출처

**External**
- ARM *SMMUv3 Architecture Specification* (IHI 0070)
- Intel *VT-d Specification* — Root/Context/PASID Table, EPT nested translation, interrupt remapping
- AMD *I/O Virtualization Technology (IOMMU) Specification* — Device Table, NPT
- PCI-SIG *ATS / PRI / PASID Specification* — SVM + page fault 협력, ACS
- *RISC-V IOMMU Architecture Specification* — device-directory → process-directory → S1/S2

## 다음 단계

- 📝 [**Module 04 퀴즈**](../quiz/04_iommu_smmu_quiz/)
- ➡️ [**Module 05 — Performance Analysis**](../05_performance_analysis/): 지금까지 배운 walk + TLB + IOTLB 가 _얼마나 빨라야 하는가_ 의 정량 분석.

