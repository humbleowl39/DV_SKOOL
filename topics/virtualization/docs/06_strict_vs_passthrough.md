# Module 06 — Strict vs Passthrough

<!-- DV-SKOOL-CH-CTX:start -->
<div class="chapter-context" data-cat="soc">
  <a class="chapter-back" href="../">
    <span class="chapter-back-arrow">←</span>
    <span class="chapter-back-icon">🪟</span>
    <span class="chapter-back-text">Virtualization</span>
  </a>
  <span class="chapter-divider">›</span>
  <span class="chapter-marker">Module 06</span>
</div>
<!-- DV-SKOOL-CH-CTX:end -->

<!-- DV-SKOOL-CH-TOC:start -->
<div class="page-toc">
  <span class="page-toc-label">목차</span>
  <a class="page-toc-link" href="#핵심-개념">핵심 개념</a>
  <a class="page-toc-link" href="#strict-system-상세">Strict System 상세</a>
  <a class="page-toc-link" href="#hypervisor-pass-through-상세">Hypervisor Pass-through 상세</a>
  <a class="page-toc-link" href="#관련-기술-스택-상세">관련 기술 스택 상세</a>
  <a class="page-toc-link" href="#strict-vs-pass-through-종합-비교">Strict vs Pass-through 종합 비교</a>
  <a class="page-toc-link" href="#현대-시스템-혼합-모델">현대 시스템: 혼합 모델</a>
  <a class="page-toc-link" href="#qa">Q&A</a>
  <a class="page-toc-link" href="#핵심-정리">핵심 정리</a>
  <a class="page-toc-link" href="#다음-단계">다음 단계</a>
</div>
<!-- DV-SKOOL-CH-TOC:end -->

!!! objective "학습 목표"
    이 모듈을 마치면:

    - **Distinguish** Strict (hypervisor 중재) vs Passthrough (직접 전달) trade-off
    - **Apply** IOMMU의 결정적 역할 (passthrough 격리)
    - **Plan** Hybrid 접근 — 일부 device는 strict, 일부는 passthrough

!!! info "사전 지식"
    - [Module 04](04_io_virtualization.md)
    - [IOMMU 코스](../../mmu/04_iommu_smmu/)

!!! tip "💡 이해를 위한 비유"
    **Strict vs Passthrough** ≈ **공유 프린터 (strict) vs 전용 프린터 (passthrough)**

    Strict 는 hypervisor 가 모든 IO 가로채서 emulate, passthrough 는 IOMMU 보호 하에 device 를 VM 에 직접 할당.

---

## 핵심 개념
**Strict System은 모든 HW 접근을 Hypervisor가 중재하여 보안/격리를 보장하지만 성능 오버헤드가 크다. Pass-through는 특정 디바이스에 대해 VM이 HW에 직접 접근하여 bare metal 수준 성능을 달성한다. 현대 시스템은 두 방식을 혼합하여 보안과 성능을 모두 확보한다.**

> 이 Unit은 DV TechForum #55 발표 내용을 기반으로 정리한 것이다.

!!! danger "❓ 흔한 오해"
    **오해**: IOMMU 가 자동으로 보안 제공

    **실제**: IOMMU 가 켜져도 page table 정확성 + DMA fault 처리 SW 가 정확해야 안전. 단순 "IOMMU on" 은 불충분.

    **왜 헷갈리는가**: "IOMMU = secure DMA" 마케팅 메시지의 단순화. 실제는 SW 정책 + HW 협업.
---

## Strict System 상세

### 아키텍처 (ARM v8 기준)

```
  ┌──────────┐  ┌──────────┐
  │   VM0    │  │   VM1    │
  │┌────────┐│  │┌────────┐│
  ││User SW ││  ││User SW ││  EL0
  ││(App)   ││  ││(App)   ││
  │├────────┤│  │├────────┤│
  ││  OS    ││  ││  OS    ││  EL1
  │└───┬────┘│  │└───┬────┘│
  └────┼─────┘  └────┼─────┘
       │ HVC         │ HVC
  ─────┴─────────────┴──────
        Hypervisor            EL2
  ──────────────────────────
        PE FW (HAL)
  ──────────────────────────
        Hardware
```

### 핵심 원칙: Hypervisor Bypass 불허

| 자원 | 접근 방식 | 오버헤드 |
|------|----------|---------|
| **메모리** | 2-stage translation (VA→IPA→PA) | TLB miss 시 최대 25회 메모리 접근 |
| **CPU 명령어** | 특권 명령어 trap → Hypervisor emulate | VM Exit/Entry (수백~수천 cycle) |
| **I/O** | MMIO/PIO trap → Hypervisor 중재 | VM Exit + 디바이스 에뮬레이션 |
| **인터럽트** | Hypervisor가 수신 후 VM에 가상 주입 | 인터럽트 라우팅 지연 |

### 3대 성능 오버헤드

#### 1. HW Configuration 오버헤드

```
I/O 설정이 필요할 때:

  App (EL0) → SVC → Guest OS (EL1) → HVC → Hypervisor (EL2)
                                              │
                                              ▼ 실제 HW 설정
                                              │
  App (EL0) ← ERET ← Guest OS (EL1) ← ERET ← Hypervisor

  SVC + HVC = 2번의 exception level 전환
  각 전환마다: 레지스터 저장/복원, TLB 관련 처리
  메모리 접근: MMU@CPU의 2-stage translation 경유
```

#### 2. HW Memory Access 오버헤드

```
디바이스(HW 가속기 등)의 메모리 접근:

  HW Accelerator → IOMMU → 2-stage translation → DRAM
                            │
                            ├─ Stage 1: VA → IPA (최적화 가능)
                            └─ Stage 2: IPA → PA (최적화 어려움)

  Stage 2 문제:
    - Locality 낮음 → TLB miss 빈번
    - Page walk 비용 높음
    - 대역폭 민감 시스템에서 심각한 병목
```

#### 3. Interrupt Signaling 오버헤드

```
HW 인터럽트 발생 시 (Strict System):

  Hardware ──IRQ──> Hypervisor (EL2)
                        │
                        ▼ 어떤 VM에 전달할지 판단
                        │
                        ▼ 가상 인터럽트 (vIRQ) 주입
                        │
                    Guest OS (EL1)
                        │
                        ▼ 인터럽트 핸들러 실행

  추가 지연:
    - Hypervisor의 판단 로직
    - VM context 전환
    - 가상 인터럽트 주입 메커니즘
    
  고대역폭 시스템 (100Gbps NIC 등):
    초당 수백만 인터럽트 → Hypervisor가 병목
```

### Context Switching 상세 분석

TechForum 슬라이드의 instruction-level 흐름:

```
user instruction15  ←────────── (A) 유저 코드 실행 중
SVC                 ────────── context switch #1 (EL0→EL1)
VM.kernel instruction0
...
VM.kernel instruction4  ←───── (B) 커널이 HW 접근 필요
HVC                 ────────── context switch #2 (EL1→EL2)
Hypervisor instruction0
...
Hypervisor instructionx       (서비스 완료)
ERET                ────────── context switch #3 (EL2→EL1)
VM.kernel instruction5        // resume after (B)
...
ERET                ────────── context switch #4 (EL1→EL0)
user instruction16            // resume after (A)
```

**단일 I/O 요청에 4번의 context switch**. 각 switch마다:
- 레지스터 세트 저장/복원
- TLB/캐시 상태 영향
- 파이프라인 flush 가능성
- 수백~수천 CPU cycle 소비

---

## Hypervisor Pass-through 상세

### 아키텍처

```
  ┌──────────┐  ┌──────────┐
  │   VM0    │  │   VM1    │
  │┌────────┐│  │┌────────┐│
  ││User SW ││  ││User SW ││  EL0
  ││(App)   ││  ││(App)   ││
  │├────────┤│  │├────────┤│
  ││  OS    ││  ││  OS    ││  EL1
  │└───┬────┘│  │└───┬────┘│
  └────┼─────┘  └────┼─────┘
       │              │ HVC (일반 I/O)
       │ Pass-through │
       │ (직접 접근)   ▼
  ─────┼────── Hypervisor ──────  EL2
  ─────┼────────────────────────
       ▼
    Hardware (특정 디바이스)
```

### 핵심 메커니즘

```
Pass-through 설정 과정:

1. Hypervisor가 물리 디바이스를 VM에 "할당" 선언
2. IOMMU에 해당 디바이스 → VM 메모리 매핑 설정
3. 디바이스의 MMIO 영역을 VM의 주소 공간에 직접 매핑
4. 인터럽트를 VM에 직접 라우팅 (Posted Interrupt)

동작:
  VM의 Guest OS가 디바이스 레지스터에 접근
  → Hypervisor trap 없이 HW에 직접 도달
  → DMA도 IOMMU 경유하여 VM 메모리에 직접 접근
  → 인터럽트도 VM에 직접 전달
```

### Pass-through의 전제 조건

| 조건 | 이유 |
|------|------|
| **IOMMU** (Intel VT-d, ARM SMMU) | DMA 격리 — 디바이스가 할당된 VM 메모리만 접근하도록 보장 |
| **인터럽트 리맵핑** | 인터럽트를 올바른 VM에 직접 전달 |
| **디바이스 격리** | 하나의 디바이스가 하나의 VM에만 전용 할당 |
| **Huge Page** (선택) | 2-stage translation 오버헤드 최소화 |

### TechForum의 시나리오

```
STEP 1: Huge Page Allocation (1GB) to HPA
  - Hypervisor가 1GB 연속 물리 메모리를 VM에 할당
  - Stage 2 PT에서 1:1 또는 Huge Page 매핑
  - TLB 1 entry로 1GB 전체 커버

STEP 2: User-space Apps Working Directly on HPA
  - 애플리케이션이 Huge Page 영역에서 직접 동작
  - DPDK 등으로 디바이스에 직접 접근
  - 커널/Hypervisor bypass → bare metal 수준 성능
```

---

## 관련 기술 스택 상세

### SR-IOV 동작 흐름

```
┌──────────────────────────────────────────┐
│  물리 NIC (SR-IOV 지원)                   │
│                                           │
│  PF (Physical Function)                   │
│  ├── VF0 ──→ VM0에 pass-through          │
│  ├── VF1 ──→ VM1에 pass-through          │
│  └── VF2 ──→ VM2에 pass-through          │
│                                           │
│  각 VF는 독립된:                           │
│    - TX/RX 큐                             │
│    - DMA 엔진                             │
│    - MSI-X 인터럽트                        │
│    - PCIe BAR                             │
└──────────────────────────────────────────┘

VM0의 I/O 경로:
  App → Guest Driver → VF0 → 물리 네트워크
  (Hypervisor 개입 없음)
```

### DPDK + VFIO 조합

```
┌─────────────────────────────────┐
│          User Space              │
│  ┌───────────────────────┐      │
│  │ DPDK Application       │     │
│  │  - Poll Mode Driver    │     │ ← 인터럽트 대신 polling
│  │  - Ring Buffer 관리     │     │ ← 커널 bypass
│  │  - 패킷 처리 로직       │     │
│  └──────────┬────────────┘      │
│             │ mmap               │
│  ┌──────────▼────────────┐      │
│  │ VFIO                   │     │ ← 디바이스 접근 프레임워크
│  │  - IOMMU DMA 매핑      │     │
│  │  - 디바이스 BAR 매핑    │     │
│  └──────────┬────────────┘      │
├─────────────┼───────────────────┤
│             ▼  (bypass kernel)   │
│         NIC Hardware             │
└─────────────────────────────────┘

성능 이점:
  - 시스템 콜 없음 (커널 bypass)
  - 데이터 복사 없음 (zero-copy)
  - 인터럽트 없음 (polling → deterministic latency)
  - CPU 코어 전용 할당 → context switch 없음
```

### VirtIO vs Pass-through 선택 기준

```
              성능 요구
              │
         높음 ┤  → Pass-through / SR-IOV / DPDK
              │
         중간 ┤  → VirtIO (충분한 성능 + 유연성)
              │
         낮음 ┤  → 에뮬레이션 (호환성 우선)
              │
              └──┬──────────┬──────────┬──→ 디바이스 공유 필요성
                 낮음       중간       높음
```

---

## Strict vs Pass-through 종합 비교

| 항목 | Strict System | Pass-through |
|------|--------------|-------------|
| **HW 접근** | Hypervisor가 모든 접근 중재 | VM이 디바이스에 직접 접근 |
| **격리** | 강함 (모든 VM 완전 격리) | 디바이스 단위 격리 (IOMMU 의존) |
| **보안** | 높음 (Hypervisor가 모든 것을 검증) | IOMMU/디바이스 펌웨어 신뢰 필요 |
| **I/O 성능** | 낮음 (VM Exit + 에뮬레이션) | Bare metal 수준 |
| **메모리 오버헤드** | 2-stage translation 전체 적용 | Huge Page로 최소화 가능 |
| **인터럽트** | Hypervisor 라우팅 (지연 있음) | 직접 전달 (Posted Interrupt) |
| **디바이스 공유** | 가능 (에뮬레이션/VirtIO) | 불가 (SR-IOV 사용 시 VF 단위 가능) |
| **Live Migration** | 용이 (상태가 SW에 있음) | 어려움 (HW 상태 이전 복잡) |
| **적용** | 범용 클라우드, 보안 중시 환경 | HPC, NFV, GPU, 저지연 시스템 |

---

## 현대 시스템: 혼합 모델

실제 프로덕션 환경에서는 **두 방식을 혼합**:

```
┌──────────────────────────────────────────────────┐
│                    VM                              │
│                                                    │
│  일반 I/O (디스크, 관리 NIC)                       │
│  → VirtIO (준가상화)                               │
│    - Hypervisor 경유, 디바이스 공유 가능             │
│    - Live Migration 지원                           │
│                                                    │
│  고성능 I/O (데이터 NIC, GPU)                       │
│  → SR-IOV Pass-through                             │
│    - Hypervisor bypass, bare metal 수준 성능        │
│    - 해당 디바이스만 VM에 전용 할당                  │
│                                                    │
│  결과: 보안/유연성 (VirtIO) + 성능 (Pass-through)   │
└──────────────────────────────────────────────────┘
```

### 실제 사례: 클라우드 인스턴스

```
AWS EC2 (Nitro System):
  - 관리 네트워크: Hypervisor 경유
  - ENA (Elastic Network Adapter): SR-IOV 기반 pass-through
  - EBS (Block Storage): NVMe 기반 pass-through
  → 거의 모든 데이터 경로가 pass-through

Azure:
  - 관리: 가상화 경유
  - AcceleratedNetworking: SR-IOV VF를 VM에 직접 할당
  - GPU: Pass-through (NVIDIA vGPU)
```

---

## Q&A

**Q: Strict System에서 I/O 요청 시 4번의 context switch를 설명하라.**
> "EL0→EL1(SVC, 시스템 콜), EL1→EL2(HVC, Hypervisor 호출), EL2→EL1(ERET, 서비스 완료 복귀), EL1→EL0(ERET, 결과 반환). 특히 EL1↔EL2 전환이 비용이 큰데, VMCS/Guest 상태 전체 저장/복원과 TLB flush로 수백~수천 cycle이 소요된다. Pass-through는 EL1↔EL2 전환을 제거하여 2회로 줄인다. 이 차이가 100Gbps 네트워킹처럼 고빈도 I/O에서 결정적이다."

**Q: Pass-through에서 IOMMU가 없으면 보안이 왜 붕괴되는가?**
> "IOMMU 없이 pass-through를 하면 DMA 엔진이 물리 주소를 그대로 사용하여 전체 메모리에 접근 가능하다. 공격 시나리오: 악의적 VM0이 NIC의 DMA descriptor에 VM1의 물리 주소를 설정하면 VM1의 데이터(암호키 등) 유출 또는 코드 변조가 가능하고, Hypervisor 메모리를 타겟팅하면 전체 시스템 장악까지 가능하다. IOMMU는 디바이스별 주소 변환 테이블로 할당 범위 밖 접근을 HW에서 차단하며 SW 우회가 불가능하다."

**Q: AWS Nitro 같은 현대 클라우드가 Strict 대신 pass-through를 채택한 이유는?**
> "성능: Strict System의 VM Exit 오버헤드가 100Gbps+ 네트워킹, NVMe에서 병목이 되었고, 클라우드 고객은 bare metal 대비 성능 격차를 허용하지 않는다. 보안: 전통적으로 pass-through = 보안 약화였으나, Nitro는 이를 HW로 해결했다. Nitro Card가 네트워크/스토리지/보안을 전용 칩에 오프로드하고, IOMMU + HW 격리로 pass-through에서도 강력한 보안을 유지한다. 핵심 전환: 보안을 SW 중재가 아닌 HW(IOMMU, Nitro Card)로 보장하면서 성능은 pass-through로 극대화하는 모델이다."

---
!!! warning "실무 주의점 — IOMMU disable 실수로 DMA 가 host RAM 직접 access"
    **현상**: Passthrough 된 device 가 VM 의 게스트 메모리 영역을 넘어 host kernel/다른 VM 메모리까지 read/write 가능 → 보안 격리 붕괴.

    **원인**: BIOS `Intel VT-d` / `AMD-Vi` 비활성, kernel cmdline 에 `intel_iommu=on` / `amd_iommu=on` 누락, 또는 `iommu=pt` (passthrough mode) 로 설정해 SVM 격리가 비활성화.

    **점검 포인트**: `dmesg | grep -i "DMAR\|IOMMU"`, `/sys/class/iommu/` 존재 여부, VFIO group 의 isolation, ATS/PRI 옵션과 ACS override 패치 사용 여부.

## 핵심 정리

- **Strict**: 모든 IO를 hypervisor 중재 → 강한 격리 + 성능 ↓.
- **Passthrough**: device 직접 VM 할당 → near-native 성능, 격리는 IOMMU 책임.
- **IOMMU의 결정적 역할**: passthrough 시 device DMA를 가상 주소 격리. 없으면 device → host 메모리 침해.
- **Hybrid**: 보통 데이터센터는 GPU/NIC만 passthrough (성능 critical), 그 외 strict.
- **Trade-off**: 격리 강도 vs 성능 — 워크로드에 따라.

## 다음 단계

- 📝 [**Module 06 퀴즈**](quiz/06_strict_vs_passthrough_quiz.md)
- ➡️ [**Module 07 — Containers & Modern**](07_containers_and_modern.md)

<div class="chapter-nav">
  <a class="nav-prev" href="../05_hypervisor_types/">
    <div class="nav-label">◀ 이전</div>
    <div class="nav-title">Hypervisor 유형</div>
  </a>
  <a class="nav-next" href="../07_containers_and_modern/">
    <div class="nav-label">다음 ▶</div>
    <div class="nav-title">컨테이너와 현대 가상화</div>
  </a>
</div>


--8<-- "abbreviations.md"
