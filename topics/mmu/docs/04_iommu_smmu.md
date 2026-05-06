# Module 04 — IOMMU / SMMU

<div class="learning-meta">
  <span class="meta-badge meta-level-advanced">📊 Advanced</span>
</div>

!!! objective "학습 목표"
    이 모듈을 마치면:

    - **Distinguish** CPU MMU와 IOMMU/SMMU의 위치/책임 차이를 SoC 다이어그램으로 식별할 수 있다.
    - **Trace** Stage 1 (VA→IPA, OS) + Stage 2 (IPA→PA, hypervisor) translation 흐름을 추적할 수 있다.
    - **Apply** StreamID / SubstreamID로 device 격리와 multi-context를 구현하는 시나리오를 설계할 수 있다.
    - **Analyze** SVM (Shared Virtual Memory)의 동작 원리와 ATS/PRI의 역할을 분석할 수 있다.
    - **Distinguish** IOMMU page fault의 비동기 처리와 CPU의 동기 fault 차이를 설명할 수 있다.

!!! info "사전 지식"
    - [Module 01-03](01_mmu_fundamentals.md)
    - DMA / device 마스터 개념
    - Hypervisor / virtualization 기본 (Stage 2 이해 위해)

## 왜 이 모듈이 중요한가

**SMMU는 SoC 보안의 핵심**입니다. IOMMU 없는 SoC는 DMA 마스터(GPU/USB/NIC)가 시스템 메모리 무제한 access — 단일 device compromise → 전체 SoC compromise. 가상화 환경에서는 Stage 2가 hypervisor 격리의 토대. **SVM은 GPU/AI accelerator의 SoC 통합 트렌드**로, 검증에서는 ATS/PRI 시나리오가 점점 중요해집니다.

## 핵심 개념
**IOMMU/SMMU = 디바이스(GPU, DMA, NIC, 가속기)의 메모리 접근을 가상 주소로 관리하여, 디바이스 격리와 DMA 보호를 제공하는 SoC 레벨 MMU.**

---

## 왜 IOMMU가 필요한가?

### IOMMU 없는 세계의 위험

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

### IOMMU가 해결하는 것

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

| 문제 | IOMMU의 해결 |
|------|-------------|
| 무제한 메모리 접근 | Page Table로 허용 범위 제한 |
| 디바이스 격리 없음 | StreamID별 독립 Page Table |
| 연속 물리 메모리 필요 | 가상 연속 → 물리 불연속 매핑 |
| DMA 공격 (DMA Attack) | 권한 검사로 비인가 접근 차단 |

---

## ARM SMMU (System MMU) 아키텍처

### SMMU v3 구조

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

### 핵심 데이터 구조

| 구조 | 역할 | 인덱싱 |
|------|------|--------|
| Stream Table | 디바이스별 설정의 최상위 테이블 | StreamID |
| STE (Stream Table Entry) | 디바이스별 Stage 1/2 설정 | 1 entry per device |
| CD (Context Descriptor) | 프로세스별 Page Table 포인터 | SubstreamID (PASID) |
| Page Table | 실제 VA→PA 매핑 | VPN (CPU MMU와 동일 형식) |

### Stream Table Entry (STE) 주요 필드

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

---

## 2-Stage Translation (가상화)

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

### Stage 1 + Stage 2 결합의 Page Walk 비용

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

## IOMMU 용어 — 벤더별 차이

| 개념 | ARM (SMMU) | Intel (VT-d) | AMD (AMD-Vi) | Samsung (sysMMU) |
|------|-----------|-------------|-------------|-----------------|
| IOMMU 이름 | SMMU | VT-d IOMMU | AMD-Vi | sysMMU |
| Device ID | StreamID | Source ID (BDF) | DeviceID | Master ID |
| Process ID | SubstreamID | PASID | PASID | - |
| Stage 1 Table | Context Descriptor | - | - | - |
| Stage 2 Table | VTTBR | EPT (Extended PT) | NPT (Nested PT) | - |
| TLB | IOTLB | IOTLB | IOTLB | TLB |

**면접 팁**: 면접관이 "sysMMU"라고 하면 삼성, "SMMU"라고 하면 ARM 표준, "VT-d"라고 하면 Intel 환경임을 즉시 인식하라. 개념은 동일하되 용어만 다르다.

---

## PCIe ATS / PRI — 디바이스 측 주소 변환

### ATS (Address Translation Service)

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

### PRI (Page Request Interface)

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

### ATS + PRI의 DV 검증 포인트

| 항목 | 검증 내용 |
|------|----------|
| ATC Hit | 디바이스가 캐싱된 PA로 DMA → IOMMU Walk 미발생 확인 |
| ATC Invalidation | IOMMU가 ATC Invalidation 전송 → 디바이스 ATC 엔트리 제거 |
| PRI 흐름 | Page Fault → Request → OS 응답 → DMA 재시도 → 성공 |
| PRI Timeout | OS 응답 지연 시 디바이스 타임아웃 처리 |
| AT bit 위조 | 디바이스가 AT=Translated로 거짓 PA 전송 → IOMMU가 차단하는지 |

---

## SMMU Command / Event Queue 상세

### Command Queue (SW → SMMU)

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

### Event Queue (SMMU → SW)

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

---

## IOMMU Page Fault 처리 — CPU Page Fault와의 차이

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

---

## SVM / SVA — Shared Virtual Memory

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

---

## IOMMU 보안 기능

### DMA 공격 방어

```
DMA 공격 시나리오 (IOMMU 없이):

  악성 PCIe 디바이스 → DMA로 커널 메모리 직접 읽기/쓰기
  → 커널 코드 변조, 비밀 데이터 탈취

IOMMU 방어:
  악성 디바이스의 DMA 요청
    → IOMMU: StreamID 확인 → Page Table 검사
    → 허용 범위 밖 → Transaction Fault → 차단
```

### 디바이스 격리

```
Device A (NIC): StreamID = 5 → Page Table A → 자신의 DMA 버퍼만 접근 가능
Device B (GPU): StreamID = 7 → Page Table B → 자신의 VRAM/버퍼만 접근 가능

→ Device A의 버그/악성 동작이 Device B의 메모리에 영향 없음
```

---

## SoC 통합 관점 — sysMMU (삼성)

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

### SoC 검증에서 sysMMU의 중요성 (이력서 연결)

Resume의 Technical Challenge #3에서 언급:
> "recurring post-integration bugs caused by human oversight in verifying common IPs (e.g., **sysMMU**, Security/Access Control, DVFS)"

→ sysMMU는 SoC의 **모든 IP**에 공통적으로 연결되는 인프라 IP. 누락 시 post-integration에서 DMA 오류, 메모리 접근 실패가 발생한다.

---

## Q&A

**Q: IOMMU/SMMU가 왜 필요한가?**
> "네 가지 이유: (1) DMA 보호 — 디바이스의 무제한 물리 메모리 접근 차단. (2) 디바이스 격리 — StreamID별 독립 Page Table로 디바이스 간 영향 차단. (3) 메모리 유연성 — 가상 연속 / 물리 불연속 매핑으로 DMA 버퍼 할당 용이. (4) 가상화 — Stage 2로 VM별 디바이스 메모리 격리."

**Q: 2-Stage Translation의 성능 비용은?**
> "최악의 경우 4-level S1 × 4-level S2 = 20번의 메모리 접근이 필요하다. DRAM 접근 ~100ns 기준 ~2000ns로, TLB Hit의 수천 배이다. 이것이 IOTLB의 크기와 효율이 가상화 환경에서 극도로 중요한 이유다. 실제로는 Page Walk Cache(중간 레벨 캐시)로 완화하지만, 여전히 IOTLB Miss는 심각한 성능 저하를 유발한다."

**Q: SMMU와 CPU MMU의 핵심 차이는?**
> "세 가지: (1) 디바이스 식별 — CPU MMU는 ASID로 프로세스를, SMMU는 StreamID로 디바이스를 구분. (2) 인터페이스 — CPU MMU는 CPU 파이프라인에 통합, SMMU는 버스 패브릭에 독립 IP로 존재. (3) 지연 허용 — CPU는 매 명령어마다 변환이 필요하여 지연에 극도로 민감, SMMU는 DMA 버스트 단위이므로 상대적으로 지연 허용이 넓지만 처리량(throughput)이 중요하다."

**Q: PCIe ATS란 무엇이고 왜 필요한가?**
> "ATS(Address Translation Service)는 디바이스 자체에 Translation Cache(ATC)를 두어 IOMMU의 병목을 줄이는 메커니즘이다. 디바이스가 IOMMU에 Translation Request를 보내 PA를 받아 ATC에 캐싱하면, 이후 같은 VA에 대해 ATC Hit으로 IOMMU Walk을 건너뛴다. 고대역폭 디바이스(GPU, SmartNIC)에서 IOTLB 경쟁을 줄이고 처리량을 높이는 데 핵심적이다."

**Q: SVM(Shared Virtual Memory)이란?**
> "디바이스가 CPU와 같은 가상 주소 공간을 공유하는 기술이다. 기존에는 SW가 VA→PA 변환 후 PA를 디바이스에 전달하고 DMA 버퍼를 pin/map해야 했다. SVM에서는 IOMMU가 CPU의 Page Table을 직접 사용하여 디바이스가 CPU의 VA를 그대로 사용한다. ATS로 디바이스 측 캐싱, PRI로 Page Fault 시 OS 협력이 전제되며, GPU가 CPU의 malloc 포인터를 직접 사용하는 것이 대표적 활용이다."

**Q: IOMMU Page Fault는 CPU Page Fault와 어떻게 다른가?**
> "가장 큰 차이는 동기성이다. CPU Page Fault는 동기적 Exception으로 현재 명령어가 즉시 멈추고 OS Handler가 처리한 뒤 재실행한다. IOMMU Page Fault는 비동기적으로, Event Queue에 기록되고 인터럽트로 OS에 통지된다. 디바이스 DMA는 이미 실패/대기 중이므로, OS가 페이지를 할당한 뒤 Stall 해제 또는 디바이스 재시도를 통해 복구한다. 디바이스 동기화가 필요하여 처리가 더 복잡하다."

---

## 핵심 정리

- **SMMU = SoC-level MMU**: DMA 마스터(GPU/NIC/DMA/가속기)의 시스템 메모리 access를 가상화·격리.
- **Two-stage translation**: Stage 1 (OS, VA→IPA) + Stage 2 (hypervisor, IPA→PA). 가상화 환경의 표준.
- **StreamID로 device 식별**: SoC 내 모든 device 마스터가 고유 StreamID. SMMU가 StreamID별 translation context 적용.
- **SVM (Shared Virtual Memory)**: device가 CPU의 VA를 그대로 사용 — pin/map 불필요. ATS(주소 변환 caching), PRI(page fault 협력)로 구현.
- **Page fault는 비동기**: CPU와 달리 event queue + interrupt. device는 이미 실패/대기 → OS가 복구 후 재시도.
- **보안 토대**: IOMMU 없으면 device compromise → 전체 시스템 메모리 침해 가능.

## 다음 단계

- 📝 [**Module 04 퀴즈**](quiz/04_iommu_smmu_quiz.md)
- ➡️ [**Module 05 — Performance Analysis**](05_performance_analysis.md)

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
