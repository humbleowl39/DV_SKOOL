# Module 04 — IOMMU / SMMU

<!-- DV-SKOOL-CH-CTX:start -->
<div class="chapter-context" data-cat="memory">
  <a class="chapter-back" href="../">
    <span class="chapter-back-arrow">←</span>
    <span class="chapter-back-icon">🧭</span>
    <span class="chapter-back-text">MMU</span>
  </a>
  <span class="chapter-divider">›</span>
  <span class="chapter-marker">Module 04</span>
</div>
<!-- DV-SKOOL-CH-CTX:end -->

<!-- DV-SKOOL-CH-TOC:start -->
<div class="page-toc">
  <span class="page-toc-label">목차</span>
  <a class="page-toc-link" href="#1-why-care-이-모듈이-왜-필요한가">1. Why care?</a>
  <a class="page-toc-link" href="#2-intuition-도어맨-비유와-한-장-그림">2. Intuition</a>
  <a class="page-toc-link" href="#3-작은-예-gpu-가-iova-0x1000-에-dma-write-하는-한-사이클">3. 작은 예 — GPU IOVA→PA 변환</a>
  <a class="page-toc-link" href="#4-일반화-smmu-구조-2-stage-streamid">4. 일반화 — SMMU + 2-Stage</a>
  <a class="page-toc-link" href="#5-디테일-ats-pri-queue-page-fault-svm-벤더별-용어">5. 디테일</a>
  <a class="page-toc-link" href="#6-흔한-오해-와-dv-디버그-체크리스트">6. 흔한 오해 + DV 디버그 체크리스트</a>
  <a class="page-toc-link" href="#7-핵심-정리-key-takeaways">7. 핵심 정리</a>
</div>
<!-- DV-SKOOL-CH-TOC:end -->

!!! objective "학습 목표"
    이 모듈을 마치면:

    - **Distinguish** CPU MMU 와 IOMMU/SMMU 의 위치/책임 차이를 SoC 다이어그램으로 식별할 수 있다.
    - **Trace** Stage 1 (VA→IPA, OS) + Stage 2 (IPA→PA, hypervisor) translation 흐름을 추적할 수 있다.
    - **Apply** StreamID / SubstreamID 로 device 격리와 multi-context 를 구현하는 시나리오를 설계할 수 있다.
    - **Analyze** SVM (Shared Virtual Memory) 의 동작 원리와 ATS / PRI 의 역할을 분석할 수 있다.
    - **Distinguish** IOMMU page fault 의 비동기 처리와 CPU 의 동기 fault 차이를 설명할 수 있다.

!!! info "사전 지식"
    - [Module 01-03](01_mmu_fundamentals.md)
    - DMA / device 마스터 개념
    - Hypervisor / virtualization 기본 (Stage 2 이해 위해)

---

## 1. Why care? — 이 모듈이 왜 필요한가

**SMMU 는 SoC 보안의 토대**입니다. IOMMU 없는 SoC 는 DMA master (GPU/USB/NIC) 가 시스템 메모리를 _무제한_ access — 단일 device compromise → 전체 SoC compromise. 가상화 환경에서는 Stage 2 가 hypervisor 의 메모리 격리 메커니즘 그 자체.

또한 **SVM (Shared Virtual Memory) 은 GPU/AI accelerator 의 SoC 통합 표준 트렌드** — CPU 와 device 가 같은 page table 을 공유해 `malloc()` 포인터를 그대로 GPU 가 쓰는 모델. 검증에서는 ATS/PRI 시나리오가 점점 중요해지고, 사내 RDMA-IP 의 GPU peer-memory 매핑도 같은 패턴.

---

## 2. Intuition — 도어맨 비유와 한 장 그림

!!! tip "💡 한 줄 비유"
    **IOMMU (SMMU)** ≈ **건물 입구의 도어맨 + 층별 출입증**.<br>
    Device(DMA) 가 host RAM 을 직접 접근하면 보안 무효 — 옥상까지 누구든 들어가는 셈. IOMMU 가 _device-side page table_ 을 두어 device 가 _자기 view 의 가상 주소_ 만 보게 하고, 도어맨 (StreamID 검사) + 출입증 (SubstreamID/PASID) 으로 _누가 어느 층_ 까지 가는지를 통제합니다.<br>
    **2-Stage** = 1층(OS)과 빌딩 관리실(Hypervisor) 의 _이중_ 도어. Guest OS 는 IPA 까지만 알고, 실제 PA 는 hypervisor 의 도어맨이 결정.

### 한 장 그림 — DMA path 의 IOMMU 통과

```
   Device (GPU / NIC / DMA / Accel)
        │ DMA req: (StreamID, SubstreamID, IOVA, R/W)
        ▼
   ┌────────────────────────────────────────────────────┐
   │                    SMMU v3                          │
   │                                                     │
   │   ① StreamID → Stream Table → STE (config)         │
   │                                                     │
   │   ② SubstreamID → Context Descriptor (S1 PT base)  │
   │                                                     │
   │   ③ IOTLB lookup ── hit ──▶ PA + perm ──┐         │
   │       │ miss                              │         │
   │       ▼                                   │         │
   │   ④ Stage 1 walk (S1 PT) → IPA           │         │
   │   ⑤ Stage 2 walk (S2 PT, hypervisor) → PA│         │
   │   ⑥ Permission check                     │         │
   │   ⑦ IOTLB fill                           │         │
   │       │                                   │         │
   │       └───────────────────────────────────┘         │
   │                                                     │
   │   Command Queue (SW → SMMU 명령)                     │
   │   Event Queue (SMMU → SW: fault, PRI, etc.)         │
   └─────────────────────┬───────────────────────────────┘
                         │ PA + AT=Translated (옵션)
                         ▼
                  Bus Fabric → Memory Controller → DRAM
```

### 왜 이 디자인인가 — Design rationale

세 요구가 동시에 만족돼야 했습니다.

1. **Device 마다 독립 page table** — GPU 의 DMA 가 NIC 의 buffer 영역을 못 보게 → StreamID 별 STE → 각 device 의 자기만의 view.
2. **VM 격리 (가상화)** — Guest OS 가 Stage 1 만 통제, _진짜 PA_ 는 hypervisor 의 Stage 2 가 결정 → Guest 가 다른 VM 의 메모리에 DMA 못 함.
3. **Async fault recovery** — Device 의 DMA 는 atomic 하게 멈출 수 없음 → CPU 처럼 _즉시 exception_ 이 아니라 **Event Queue + Interrupt + retry** 의 비동기 모델.

이 세 요구의 교집합이 "SMMU = StreamID 라우팅 + 2-stage walk + Command/Event queue" 의 v3 구조입니다.

---

## 3. 작은 예 — GPU 가 IOVA = 0x4_0000_1000 에 DMA write 하는 한 사이클

가장 단순한 시나리오. Guest OS 의 GPU driver 가 **IOVA = 0x0000_0004_0000_1000** (4 KB 정렬, 256 byte write) 로 DMA 를 발사. StreamID = 0x10 (GPU), SubstreamID = 0x05 (process 5). Stage 1 + Stage 2 모두 enable. IOTLB cold.

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
- **SMMU**: DMA stall (또는 abort) → **Event Queue 에 `TRANSLATION_FAULT` 기록** → SMMU 가 GIC 로 interrupt → OS 가 event 를 polling → page allocate → Command Queue 에 `PRI_RESP` (PRI 사용 시) 또는 STE/CD update + IOTLB invalidation → Device retry.
- 즉 **fault recovery 가 비동기**.

!!! note "여기서 잡아야 할 두 가지"
    **(1) S1 PTE 자체의 주소도 IPA 라서 S2 walk 가 _nested_ 로 일어난다** — 그래서 worst case 가 4×5 = 20 mem access. 이게 IOTLB 의 capacity 가 가상화 환경에서 결정적인 이유. <br>
    **(2) Page fault 가 Synchronous 가 아니라 Asynchronous** — Device DMA 는 이미 멈춰 있고, OS 가 _나중에_ event queue 를 읽고 처리. Recovery path 는 PRI / Stall / Abort 의 세 가지 모드로 분기.

---

## 4. 일반화 — SMMU 구조, 2-Stage, StreamID

### 4.1 IOMMU 없는 vs 있는 세계

```
IOMMU 없이:

  +-------+                  +--------+
  | CPU   | -- VA → MMU → PA → DRAM  |
  +-------+                  +--------+
                                 ^
  +-------+                      |
  | DMA   | -- PA 직접 접근 -----+
  +-------+

  문제:
  1. DMA가 물리 주소를 직접 사용 → 어떤 메모리든 접근 가능
  2. 악성 디바이스가 커널 메모리를 읽거나 덮어쓸 수 있음
  3. 디바이스 간 격리 없음 → 한 디바이스 버그가 전체 시스템 오염
  4. DMA에 연속 물리 메모리 필요 → 대용량 DMA 버퍼 할당 어려움
```

```
IOMMU 있을 때:

  +-------+              +--------+
  | CPU   | → CPU MMU → DRAM     |
  +-------+              +--------+
                             ^
  +-------+     +-------+   |
  | DMA   | → | IOMMU | →-+
  +-------+     +-------+
                 VA → PA 변환
                 + 권한 검사
                 + 디바이스 격리
```

| 문제 | IOMMU 의 해결 |
|------|-------------|
| 무제한 메모리 접근 | Page Table 로 허용 범위 제한 |
| 디바이스 격리 없음 | StreamID 별 독립 Page Table |
| 연속 물리 메모리 필요 | 가상 연속 → 물리 불연속 매핑 |
| DMA 공격 (DMA Attack) | 권한 검사로 비인가 접근 차단 |

### 4.2 ARM SMMU v3 구조

```
+------------------------------------------------------------------+
|                        SMMU v3                                    |
|                                                                   |
|  Device → [StreamID] → Stream Table → STE (Stream Table Entry)    |
|                                         |                         |
|                                    +----+----+                    |
|                                    |  Stage 1 | (Device VA → IPA)|
|                                    |  Config  |                   |
|                                    +----+----+                    |
|                                         |                         |
|                                    +----+----+                    |
|                                    |  Stage 2 | (IPA → PA)       |
|                                    |  Config  | (Hypervisor)     |
|                                    +----+----+                    |
|                                         |                         |
|                                    +----+----+                    |
|                                    |  IOTLB  |                    |
|                                    +---------+                    |
|                                                                   |
|  Command Queue (SW → SMMU 명령)                                   |
|  Event Queue (SMMU → SW 에러/이벤트 보고)                         |
+------------------------------------------------------------------+
```

### 4.3 핵심 데이터 구조

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

```
문제: 모든 DMA 요청이 IOMMU를 거치면 → IOMMU가 병목

해결: ATS — 디바이스 자체에 Translation Cache (ATC)를 두어 IOMMU 우회

  +--------+     +-------+     +--------+
  | Device |     | IOMMU |     | Memory |
  |  +ATC  |     |       |     |        |
  +---+----+     +---+---+     +---+----+
      |              |              |
      |--Translation Request-->|   |      ← ATC Miss 시 IOMMU에 요청
      |<--Translation Response-|   |      ← IOMMU가 PA 반환
      |  (ATC에 캐싱)          |   |
      |                         |   |
      |---DMA (PA, AT=Translated)-->|     ← ATC Hit → IOMMU 우회, PA 직접 사용
      |                         |   |

ATS 흐름:
  1. 디바이스가 IOMMU에 Translation Request (VA + StreamID)
  2. IOMMU가 Page Walk → PA 반환
  3. 디바이스가 ATC에 저장
  4. 이후 같은 VA → ATC Hit → PA로 직접 DMA (IOMMU 통과만, Walk 불필요)

IOMMU 측:
  - AT=Translated인 DMA는 IOTLB Walk을 건너뜀
  - 단, Permission 재확인은 수행 (보안)
```

### 5.2 PRI (Page Request Interface)

```
문제: 디바이스가 접근한 페이지가 Swap-out 되었을 때?
  → IOMMU Page Fault → DMA 실패 → 디바이스 에러

해결: PRI — 디바이스가 OS에 "이 페이지를 준비해달라" 요청

PRI 흐름:
  1. 디바이스 DMA → IOMMU에서 Page Fault (페이지 없음)
  2. IOMMU → Event Queue에 Page Request 기록
  3. OS: 페이지 할당/Swap-in → Page Table 업데이트
  4. OS → IOMMU Command Queue에 Page Response
  5. IOMMU → 디바이스에 완료 통지
  6. 디바이스: DMA 재시도 → 성공

핵심: DMA 실패 대신 "잠시 대기 후 재시도" → 디바이스와 OS 간 협력
→ SVM (Shared Virtual Memory) 구현의 전제 조건
```

#### ATS + PRI 의 DV 검증 포인트

| 항목 | 검증 내용 |
|------|----------|
| ATC Hit | 디바이스가 캐싱된 PA로 DMA → IOMMU Walk 미발생 확인 |
| ATC Invalidation | IOMMU가 ATC Invalidation 전송 → 디바이스 ATC 엔트리 제거 |
| PRI 흐름 | Page Fault → Request → OS 응답 → DMA 재시도 → 성공 |
| PRI Timeout | OS 응답 지연 시 디바이스 타임아웃 처리 |
| AT bit 위조 | 디바이스가 AT=Translated로 거짓 PA 전송 → IOMMU가 차단하는지 |

### 5.3 SMMU Command / Event Queue 상세

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

### 5.4 IOMMU Page Fault 처리 — CPU Page Fault와의 차이

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

### 5.5 SVM / SVA — Shared Virtual Memory

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

### 5.6 IOMMU 보안 기능

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

### 5.7 IOMMU 용어 — 벤더별 차이

| 개념 | ARM (SMMU) | Intel (VT-d) | AMD (AMD-Vi) | Samsung (sysMMU) |
|------|-----------|-------------|-------------|-----------------|
| IOMMU 이름 | SMMU | VT-d IOMMU | AMD-Vi | sysMMU |
| Device ID | StreamID | Source ID (BDF) | DeviceID | Master ID |
| Process ID | SubstreamID | PASID | PASID | - |
| Stage 1 Table | Context Descriptor | - | - | - |
| Stage 2 Table | VTTBR | EPT (Extended PT) | NPT (Nested PT) | - |
| TLB | IOTLB | IOTLB | IOTLB | TLB |

**면접 팁**: 면접관이 "sysMMU"라고 하면 삼성, "SMMU"라고 하면 ARM 표준, "VT-d"라고 하면 Intel 환경임을 즉시 인식하라. 개념은 동일하되 용어만 다르다.

### 5.8 SoC 통합 관점 — sysMMU (삼성)

```
SoC 내부 IP 구성:

  +--------+     +--------+
  | IP_A   +---->| sysMMU +----> Bus Fabric ---> Memory
  | (예:DMA)|     | (A용)  |
  +--------+     +--------+

  +--------+     +--------+
  | IP_B   +---->| sysMMU +----> Bus Fabric ---> Memory
  | (예:GPU)|     | (B용)  |
  +--------+     +--------+

특징:
  - IP별로 독립적인 sysMMU 인스턴스
  - 각 sysMMU가 해당 IP의 주소 변환 + 접근 제어
  - 커널 드라이버가 각 sysMMU의 Page Table 관리
```

#### SoC 검증에서 sysMMU 의 중요성 (이력서 연결)

Resume의 Technical Challenge #3에서 언급:
> "recurring post-integration bugs caused by human oversight in verifying common IPs (e.g., **sysMMU**, Security/Access Control, DVFS)"

→ sysMMU는 SoC의 **모든 IP**에 공통적으로 연결되는 인프라 IP. 누락 시 post-integration에서 DMA 오류, 메모리 접근 실패가 발생한다.

---

## 6. 흔한 오해 와 DV 디버그 체크리스트

### 흔한 오해

!!! danger "❓ 오해 1 — 'IOMMU = MMU 의 단순 복제'"
    **실제**: IOMMU 는 추가로 **StreamID 라우팅**, **2-stage 결합**, **ATS / PRI**, **Command/Event queue**, **PASID 기반 multi-context** 등 device-side 특화 기능을 가집니다. 단순 복제가 아니라 _device 영역 특화 변형_. SMMU spec (IHI 0070) 은 ARMv8 ARM 과 별도 문서.<br>
    **왜 헷갈리는가**: "이름이 같은 패밀리 = 동일 동작" 이라는 가정.

!!! danger "❓ 오해 2 — 'Stage 2 만 켜면 Guest 가 자기 PA 를 자유롭게 쓸 수 있다'"
    **실제**: Stage 2 만 켜고 Stage 1 을 bypass 하면 _Guest 가 IPA = PA 처럼 직접 다룸_ — 즉 _Guest 가 host PA 를 알게 됨_. Hypervisor 격리가 Stage 2 의 _존재_ 만으론 안 되고, _Stage 1 도 적절히 통제_ 되거나, Bypass mode 가 안전한 device 에만 허용돼야 합니다.<br>
    **왜 헷갈리는가**: "S2 = hypervisor 격리" 라는 단순화.

!!! danger "❓ 오해 3 — 'IOMMU page fault 도 CPU 처럼 instr 단위 retry 가능'"
    **실제**: Device 의 DMA 는 _atomic instruction 단위가 아닌 burst_. Fault 시 처음부터 다시 시작하면 이미 transfer 한 byte 가 _두 번_ 쓰일 수 있음. 그래서 PRI / Stall 모드가 _부분 진행_ 을 보존하면서 OS 협력으로 복구하는 모델을 정의합니다. Abort 모드는 device 의 driver 가 _처음부터_ 재시도하는 책임을 짐.<br>
    **왜 헷갈리는가**: CPU exception model 의 mental projection.

!!! danger "❓ 오해 4 — 'ATS 가 켜져 있으면 보안이 떨어진다'"
    **실제**: ATS 의 AT=Translated 는 _IOTLB 우회_ 일 뿐, **Permission check 는 항상 IOMMU 에서 수행** (또는 ATC 가 cache 한 perm 으로). 디바이스가 거짓 AT=Translated 를 보내도 IOMMU 가 access control reg 로 검증 가능. 따라서 ATS 자체는 보안 약점이 아님 — 단, ATC invalidation race 는 _별도_ 검증 필요.<br>
    **왜 헷갈리는가**: "IOMMU 통과 안 함" 을 "검사 안 함" 으로 단축.

!!! danger "❓ 오해 5 — 'IOTLB 는 그냥 작은 TLB'"
    **실제**: IOTLB 는 (StreamID, SubstreamID, ASID, VMID, VPN) 의 _복합 키_ 로 indexing — CPU TLB (ASID, VMID, VPN) 보다 키 폭이 큼. 또 _entry size_ 도 다양 (4 KB, 2 MB, 1 GB) 이고 device traffic pattern (sequential burst) 가 CPU 와 달라 _replacement 정책_ 도 다른 게 보통. "그냥 TLB" 가 아닙니다.<br>
    **왜 헷갈리는가**: 이름이 비슷.

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

!!! warning "실무 주의점 — Stage 2 미설정 시 Guest 메모리 격리 무효화"
    **현상**: 가상화 환경에서 Guest OS가 Stage 2 변환 없이 IPA를 그대로 PA로 사용하게 되어, 다른 Guest 또는 Hypervisor 메모리 영역에 DMA 접근 가능.

    **원인**: SMMU의 Two-Stage 변환에서 Stage 1(Guest OS 제어)만 활성화하고 Stage 2(Hypervisor 제어)를 bypass 상태로 두면 Guest가 임의의 PA를 지정한 DMA로 시스템 전체 메모리에 접근할 수 있음. Hypervisor 초기화 시 모든 Stream에 대해 Stage 2 Context Descriptor를 설정해야 함.

    **점검 포인트**: SMMU CD(Context Descriptor)에서 `S2_CFG` 필드가 `0b00`(bypass)이 아닌지 확인. DV 시나리오에서 Guest DMA 주소에 Hypervisor 메모리 범위 PA를 주입했을 때 SMMU가 Abort를 생성하는지 검증.

---

## 7. 핵심 정리 (Key Takeaways)

- **SMMU = SoC-level MMU**: DMA master (GPU/NIC/DMA/가속기) 의 system memory access 를 _가상화·격리_. 없으면 단일 device 가 전체 SoC 를 위협.
- **Two-stage translation**: Stage 1 (OS, VA→IPA) + Stage 2 (hypervisor, IPA→PA). 가상화 환경의 표준. 최악 5×4 = 20 mem access.
- **StreamID + SubstreamID 로 device + process 식별**: SoC 내 모든 device master 가 고유 StreamID, 한 device 의 여러 process 는 SubstreamID/PASID 로 구분.
- **SVM**: device 가 CPU 의 VA 를 그대로 사용 — pin/map 불필요. ATS (주소 변환 caching), PRI (page fault 협력) 로 구현. GPU/Accel 트렌드.
- **Page fault 는 비동기**: CPU 와 달리 event queue + interrupt + retry. Stall / Abort / PRI 의 세 모드. Recovery path 가 _device-OS 협력_ 으로 길어짐.
- **벤더 용어 매핑**: ARM SMMU StreamID = Intel SourceID = AMD DeviceID. 개념은 같고 이름만 다름.

## 다음 단계

- 📝 [**Module 04 퀴즈**](quiz/04_iommu_smmu_quiz.md)
- ➡️ [**Module 05 — Performance Analysis**](05_performance_analysis.md): 지금까지 배운 walk + TLB + IOTLB 가 _얼마나 빨라야 하는가_ 의 정량 분석.

<div class="chapter-nav">
  <a class="nav-prev" href="../03_tlb/">
    <div class="nav-label">◀ 이전</div>
    <div class="nav-title">TLB (Translation Lookaside Buffer)</div>
  </a>
  <a class="nav-next" href="../05_performance_analysis/">
    <div class="nav-label">다음 ▶</div>
    <div class="nav-title">MMU 성능 분석 및 최적화</div>
  </a>
</div>


--8<-- "abbreviations.md"
