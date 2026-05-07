# Module 04 — I/O Virtualization

<!-- DV-SKOOL-CH-CTX:start -->
<div class="chapter-context" data-cat="soc">
  <a class="chapter-back" href="../">
    <span class="chapter-back-arrow">←</span>
    <span class="chapter-back-icon">🪟</span>
    <span class="chapter-back-text">Virtualization</span>
  </a>
  <span class="chapter-divider">›</span>
  <span class="chapter-marker">Module 04</span>
</div>
<!-- DV-SKOOL-CH-CTX:end -->

<!-- DV-SKOOL-CH-TOC:start -->
<div class="page-toc">
  <span class="page-toc-label">목차</span>
  <a class="page-toc-link" href="#핵심-개념">핵심 개념</a>
  <a class="page-toc-link" href="#io-가상화가-어려운-이유">I/O 가상화가 어려운 이유</a>
  <a class="page-toc-link" href="#방법-1-디바이스-에뮬레이션-full-emulation">방법 1: 디바이스 에뮬레이션 (Full Emulation)</a>
  <a class="page-toc-link" href="#방법-2-준가상화-io-virtio">방법 2: 준가상화 I/O (VirtIO)</a>
  <a class="page-toc-link" href="#방법-3-디바이스-pass-through">방법 3: 디바이스 Pass-through</a>
  <a class="page-toc-link" href="#io-가상화-방식-종합-비교">I/O 가상화 방식 종합 비교</a>
  <a class="page-toc-link" href="#qa">Q&A</a>
  <a class="page-toc-link" href="#핵심-정리">핵심 정리</a>
  <a class="page-toc-link" href="#다음-단계">다음 단계</a>
</div>
<!-- DV-SKOOL-CH-TOC:end -->

!!! objective "학습 목표"
    이 모듈을 마치면:

    - **Distinguish** Emulation, Paravirtualization (virtio), Passthrough (SR-IOV, VFIO) 3가지 모델
    - **Apply** SR-IOV의 PF/VF 분리, IOMMU의 역할
    - **Identify** virtio의 vring + queue 메커니즘
    - **Decide** 시나리오에 따른 적합한 I/O 가상화 방식

!!! info "사전 지식"
    - [Module 01-03](01_virtualization_fundamentals.md)
    - [MMU 코스 IOMMU/SMMU](../../mmu/04_iommu_smmu/)

!!! tip "💡 이해를 위한 비유"
    **I/O Virtualization** ≈ **공용 프린터 — 모두가 같은 프린터를 자기 것처럼 씀 (virtio) vs 전용 프린터 할당 (passthrough)**

    Virtio = front-end driver 가 ring 으로 hypervisor 와 통신, passthrough = device 를 한 VM 이 독점. Trade-off.

---

## 핵심 개념
**I/O 가상화 = 물리 디바이스를 여러 VM이 공유하거나, 특정 VM에 전용 할당하는 기술. 에뮬레이션(SW) → 준가상화(VirtIO) → 패스스루(SR-IOV/VFIO)로 발전하며, 성능과 격리의 트레이드오프를 다룬다.**

!!! danger "❓ 흔한 오해"
    **오해**: Passthrough 가 항상 빠름

    **실제**: Passthrough 는 throughput ↑, latency ↓. 그러나 live migration 불가, IOMMU 필수, density ↓. trade-off 정확히 평가 필요.

    **왜 헷갈리는가**: "direct = 빠름" 의 직관. 실제로는 multi-axis trade-off.
---

## I/O 가상화가 어려운 이유

CPU/메모리와 달리 I/O 디바이스는 본질적으로 **공유가 어렵다**:

```
CPU:  시분할(time-sharing)로 여러 VM에 할당 가능
메모리: 주소 변환(paging)으로 VM별 공간 분리 가능
I/O:  디바이스마다 인터페이스가 다르고,
      상태를 갖고 있으며(stateful),
      DMA로 메모리에 직접 접근함

  → 범용적인 HW 메커니즘으로 해결하기 어려움
  → 디바이스별 에뮬레이션 or 특수 HW 지원 필요
```

### DMA의 보안 문제

```
                    ┌──────────┐
  VM0의 메모리      │ NIC      │
  0x1000~0x2000 ◄───┤ (DMA)   │ DMA가 VM0의 메모리에 직접 쓰기
                    │          │
  VM1의 메모리      │          │ 만약 NIC가 잘못된 주소에 쓰면?
  0x2000~0x3000 ◄───┤          │ → VM1의 메모리가 오염됨!
                    └──────────┘

해결: IOMMU가 DMA 주소도 변환/검증
      디바이스가 허가된 메모리 영역만 접근 가능하도록 보장
```

---

## 방법 1: 디바이스 에뮬레이션 (Full Emulation)

### 개념

Hypervisor가 물리 디바이스를 **SW로 완전히 모방**:

```
┌────────────┐     ┌────────────┐
│   VM0      │     │   VM1      │
│ Guest OS   │     │ Guest OS   │
│ (기존 NIC  │     │ (기존 NIC  │
│  드라이버) │     │  드라이버) │
└─────┬──────┘     └─────┬──────┘
      │ I/O 접근          │ I/O 접근
      │ (MMIO/PIO)        │
      ▼ VM Exit           ▼ VM Exit
┌─────────────────────────────────┐
│         Hypervisor              │
│  ┌──────────┐  ┌──────────┐    │
│  │가상 NIC 0│  │가상 NIC 1│    │  SW로 디바이스 동작 에뮬레이션
│  └────┬─────┘  └────┬─────┘    │
│       └──────┬──────┘          │
│              ▼                  │
│         물리 NIC 드라이버       │
└──────────────┬──────────────────┘
               ▼
          물리 NIC
```

### 동작 흐름

1. Guest OS가 가상 디바이스의 레지스터에 접근 (MMIO write)
2. **VM Exit** 발생 → Hypervisor가 trap
3. Hypervisor의 에뮬레이터가 해당 레지스터 접근을 해석
4. 필요 시 물리 디바이스에 실제 I/O 수행
5. 결과를 가상 디바이스 상태에 반영
6. **VM Entry** → Guest OS 재개

### 대표 구현: QEMU

```
QEMU가 에뮬레이션하는 디바이스 예시:
  - e1000 (Intel NIC)
  - IDE/AHCI (디스크 컨트롤러)
  - VGA (그래픽)
  - USB, 시리얼 포트, ...

Guest OS는 실제 e1000 드라이버를 사용
  → 수정 없이 동작 (Full Virtualization)
  → 하지만 매 I/O마다 VM Exit → 느림
```

### 성능 분석

```
네트워크 패킷 하나 전송:
  1. Guest: TX descriptor 쓰기 → VM Exit
  2. Hypervisor: descriptor 해석 → 물리 NIC에 전달
  3. 물리 NIC: 패킷 전송 완료 → 인터럽트
  4. Hypervisor: 인터럽트 수신 → 가상 인터럽트 주입
  5. Guest: 인터럽트 핸들러 실행

패킷당 VM Exit: 최소 2회 (TX + 인터럽트)
초당 100만 패킷이면: 200만 VM Exit/sec → CPU 상당 부분 소모
```

| 장점 | 단점 |
|------|------|
| Guest OS 수정 불필요 | 매 I/O마다 VM Exit (심각한 오버헤드) |
| 어떤 디바이스든 에뮬레이션 가능 | Hypervisor에 디바이스별 에뮬레이터 필요 |
| 디바이스 공유 용이 | 실제 HW 성능의 10~30% 수준 |

---

## 방법 2: 준가상화 I/O (VirtIO)

### 개념

Guest OS에 **가상화에 최적화된 드라이버**를 설치. 실제 HW를 흉내내지 않고, 효율적인 추상 인터페이스를 정의:

```
┌────────────┐     ┌────────────┐
│   VM0      │     │   VM1      │
│ Guest OS   │     │ Guest OS   │
│ (VirtIO    │     │ (VirtIO    │
│  드라이버) │     │  드라이버) │  ← 수정된 드라이버
└─────┬──────┘     └─────┬──────┘
      │ Virtqueue         │
      │ (공유 메모리 링)    │     ← VM Exit 최소화
      ▼                   ▼
┌─────────────────────────────────┐
│     Hypervisor (VirtIO backend) │
│          물리 NIC 드라이버       │
└──────────────┬──────────────────┘
               ▼
          물리 NIC
```

### VirtIO 아키텍처

```
┌─────────────────────────────────────────┐
│  VirtIO 표준 인터페이스                   │
├─────────┬───────────┬───────────────────┤
│virtio-net│virtio-blk│virtio-scsi  ...   │ 디바이스 타입
├─────────┴───────────┴───────────────────┤
│              Virtqueue                   │ 통신 메커니즘
│  ┌────────────────────────────────────┐ │
│  │  Descriptor Table                  │ │ 데이터 버퍼 포인터
│  │  Available Ring                    │ │ Guest→Host 알림
│  │  Used Ring                         │ │ Host→Guest 알림
│  └────────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

### 왜 빠른가?

```
에뮬레이션: 레지스터 접근 하나하나마다 VM Exit
VirtIO:     여러 요청을 Virtqueue에 모아서 한 번에 알림 (batching)

  Guest:
    1. 여러 패킷을 Descriptor Table에 등록
    2. Available Ring 업데이트
    3. 단 1번의 알림 (kick) → VM Exit 1회

  vs 에뮬레이션:
    1. 패킷마다 TX register 쓰기 → VM Exit
    2. 패킷마다 doorbell → VM Exit
    → 패킷 N개면 VM Exit N회 이상
```

| 장점 | 단점 |
|------|------|
| 에뮬레이션 대비 2~10배 성능 | Guest OS에 VirtIO 드라이버 필요 |
| VM Exit 최소화 (batching) | 비공개 OS는 드라이버 지원 필요 |
| 표준화된 인터페이스 | 물리 HW 대비 여전히 오버헤드 |
| 디바이스 공유 가능 | |

---

## 방법 3: 디바이스 Pass-through

### 개념

물리 디바이스를 **특정 VM에 직접 할당**. Hypervisor를 bypass:

```
┌────────────┐     ┌────────────┐
│   VM0      │     │   VM1      │
│ Guest OS   │     │ Guest OS   │
│ (물리 NIC  │     │ (VirtIO    │
│  드라이버) │     │  드라이버) │
└─────┬──────┘     └─────┬──────┘
      │                   │
      │ 직접 접근          │ Hypervisor 경유
      │ (no VM Exit)      ▼
      │              Hypervisor
      │                   │
      ▼                   ▼
   물리 NIC #0        물리 NIC #1

  VM0은 NIC #0에 bare metal처럼 직접 접근
  → Hypervisor 개입 없음
  → I/O 성능 = bare metal 수준
```

### VFIO (Virtual Function I/O)

Linux에서 디바이스 pass-through를 구현하는 프레임워크:

```
┌─────────────────────────────────────────────┐
│                User Space                    │
│  ┌──────────┐                               │
│  │ QEMU/VM  │ ← VFIO API로 디바이스 접근     │
│  └────┬─────┘                               │
│       │ open(/dev/vfio/...)                  │
├───────┼─────────────────────────────────────┤
│       ▼         Kernel Space                 │
│  ┌──────────┐                               │
│  │ VFIO     │ ← 디바이스 그룹 관리           │
│  │ Driver   │   IOMMU 설정                  │
│  └────┬─────┘   인터럽트 라우팅              │
│       │                                      │
│  ┌────▼─────┐                               │
│  │ IOMMU    │ ← DMA 주소 변환/격리           │
│  └────┬─────┘                               │
├───────┼─────────────────────────────────────┤
│       ▼                                      │
│   PCIe Device                                │
└─────────────────────────────────────────────┘
```

**IOMMU의 역할** (= I/O용 MMU):
- 디바이스의 DMA 주소를 변환 (디바이스 주소 → PA)
- 디바이스가 할당된 VM의 메모리만 접근하도록 격리
- 없으면 DMA가 아무 메모리나 접근 가능 → 보안 붕괴

---

### SR-IOV (Single Root I/O Virtualization)

물리 디바이스 하나를 **여러 가상 디바이스로 분할**하는 PCIe 스펙:

```
┌──────────────────────────────────────┐
│         물리 NIC (SR-IOV 지원)        │
├──────────────────────────────────────┤
│  PF (Physical Function)              │
│  - 디바이스 전체 관리/설정            │
│  - Host/Hypervisor가 소유            │
├──────────────────────────────────────┤
│  VF0    │  VF1    │  VF2    │ ...   │
│  (경량) │  (경량) │  (경량) │       │
│  VM0에  │  VM1에  │  VM2에  │       │
│  할당   │  할당   │  할당   │       │
└──────────────────────────────────────┘

각 VF는:
  - 독립된 PCIe Function (BAR, MSI-X 등)
  - 자체 TX/RX 큐
  - 독립 DMA 엔진
  → VM에 직접 할당 가능 (pass-through)
  → Hypervisor 개입 없이 I/O 수행
```

### SR-IOV vs 일반 Pass-through

| 항목 | 일반 Pass-through | SR-IOV |
|------|-------------------|--------|
| 물리 디바이스 | 1개 → 1 VM | 1개 → N VM (VF 분할) |
| 디바이스 공유 | 불가 | 가능 (VF 단위) |
| HW 지원 | IOMMU만 | IOMMU + SR-IOV NIC |
| 성능 | Bare metal | Bare metal에 근접 |
| 비용 | 디바이스 수 = VM 수 | 1개 디바이스로 다수 VM 지원 |

---

### DPDK (Data Plane Development Kit)

User-space에서 **커널을 완전히 bypass**하여 패킷을 처리:

```
[ 일반 네트워크 스택 ]          [ DPDK ]

  Application                    Application
      │                              │
      ▼                              │ 직접 접근
  Socket API                         │ (mmap)
      │                              │
      ▼                              │
  TCP/IP Stack (Kernel)              │
      │                              │
      ▼                              │
  NIC Driver (Kernel)                │
      │                              ▼
      ▼                          NIC (via VFIO/UIO)
     NIC

커널 경유: 시스템 콜 + 커널 복사 + 인터럽트 처리
DPDK: 모든 것을 user-space에서 처리 (polling 기반)
```

### DPDK가 빠른 이유

| 기존 커널 경유 | DPDK |
|--------------|------|
| 시스템 콜 오버헤드 | User-space에서 직접 디바이스 접근 |
| 인터럽트 기반 (Context switch) | **Polling 기반** (busy-wait, CPU 전용 할당) |
| 커널↔유저 간 데이터 복사 | **Zero-copy** (공유 메모리) |
| 범용 TCP/IP 스택 | 최적화된 패킷 처리 라이브러리 |

**사용 사례**: 고성능 네트워킹 — NFV, 패킷 브로커, 방화벽, 로드밸런서

---

## I/O 가상화 방식 종합 비교

```
성능    ◄────────────────────────────────────► 격리/공유
낮음                                           높음

  에뮬레이션        VirtIO         SR-IOV       Pass-through
  (10~30%)         (50~80%)       (90~98%)     (95~100%)

  ┌─────────┐    ┌─────────┐    ┌─────────┐   ┌─────────┐
  │ 모든 OS │    │드라이버 │    │ HW 지원 │   │ 1:1     │
  │ 수정 없음│    │필요     │    │ 필요    │   │ 전용    │
  │ 공유 OK │    │ 공유 OK │    │ 공유 OK │   │ 공유 불가│
  └─────────┘    └─────────┘    └─────────┘   └─────────┘
```

| 방식 | 성능 | Guest 수정 | 디바이스 공유 | HW 지원 | 주 사용처 |
|------|------|-----------|-------------|---------|----------|
| **에뮬레이션** | 낮음 | 불필요 | 가능 | 불필요 | 개발/테스트, 레거시 |
| **VirtIO** | 중간 | 드라이버 | 가능 | 불필요 | 범용 클라우드 |
| **SR-IOV** | 높음 | 드라이버 | VF 단위 | SR-IOV NIC | 고성능 네트워크 |
| **Pass-through** | 최고 | 불필요 | 불가 | IOMMU | GPU, NVMe, 전용 HW |

---

## Q&A

**Q: VirtIO가 디바이스 에뮬레이션보다 빠른 이유는?**
> "에뮬레이션은 Guest OS가 가상 디바이스 레지스터에 접근할 때마다 VM Exit이 발생한다. 패킷 하나에 TX descriptor, doorbell 등 여러 MMIO 접근이 필요하고 각각 VM Exit을 유발한다. VirtIO는 Virtqueue 공유 메모리 링 버퍼를 사용하여, Guest가 여러 요청을 Descriptor Table에 등록한 후 단 1번의 kick으로 Hypervisor에 통보한다. 결과적으로 에뮬레이션은 I/O당 VM Exit이 선형 증가하지만, VirtIO는 batch 크기에 무관하게 거의 일정. 초당 수백만 I/O에서 차이가 극대화된다."

**Q: IOMMU 없이 디바이스 pass-through를 하면 어떤 보안 문제가 생기는가?**
> "IOMMU 없이는 DMA 엔진이 물리 메모리 전체에 접근 가능하다. 공격 시나리오: VM0에 할당된 NIC의 DMA descriptor에 VM1의 물리 메모리 주소를 설정하면, VM1의 데이터(암호키, 인증정보) 유출 또는 코드 변조가 가능하다. 더 심각하게는 Hypervisor 메모리를 DMA 대상으로 지정하여 전체 시스템 장악이 가능하다. IOMMU는 디바이스별 주소 변환 테이블로 할당된 VM의 메모리 범위만 접근 허용하며, HW 레벨 격리이므로 SW 우회 불가다."

**Q: SR-IOV의 PF/VF 차이와 일반 pass-through 대비 장점은?**
> "PF(Physical Function)는 물리 디바이스의 완전한 PCIe Function으로 초기화, VF 생성/삭제를 담당하며 Hypervisor가 관리한다. VF(Virtual Function)는 PF에서 파생된 경량 PCIe Function으로, 자체 BAR, MSI-X, TX/RX 큐를 갖지만 관리 기능은 없고 데이터 경로만 제공한다. 확장성: 일반 pass-through는 NIC 1개 = VM 1개이지만, SR-IOV는 NIC 1개에서 VF 128개 생성 가능. 각 VF가 HW 독립 데이터 경로를 가지므로 bare metal 근접 성능을 유지하면서 128개 VM을 지원한다."

---
!!! warning "실무 주의점 — virtio queue full 시 backend silent drop"
    **현상**: Guest 가 IO timeout/retransmit 만 인지하고, host 측 로그에는 명확한 error 가 없어 원인 파악이 늦어짐.

    **원인**: virtio vring 의 avail/used index 가 가득 찼을 때 backend(QEMU/vhost) 가 추가 descriptor 를 단순 무시하거나 notification 을 throttling 하여 guest 는 정상 enqueue 로 오해.

    **점검 포인트**: vhost stat 의 queue full counter, backend 의 notify suppression flag (`VIRTIO_F_EVENT_IDX`), guest 측 queue depth vs in-flight ratio.

## 핵심 정리

- **3 가지 모델**:
  1. **Emulation** — Hypervisor가 device 시뮬. 호환성 ↑, 성능 ↓ (모든 IO trap)
  2. **Paravirt (virtio)** — Guest driver + hypervisor 공유 ring. 성능 ↑, guest 인지 필요
  3. **Passthrough (SR-IOV/VFIO)** — Device를 VM에 직접 할당. 성능 = native, 격리는 IOMMU 책임
- **SR-IOV**: Single Root I/O Virtualization. PCIe device가 1 PF + N VF로 분할. 각 VF가 VM에 할당.
- **VFIO**: kernel-bypass IOMMU 기반 직접 device access.
- **IOMMU 필수**: passthrough 시 device DMA가 host 메모리 침해 못 하게 SMMU/IOMMU로 격리.

## 다음 단계

- 📝 [**Module 04 퀴즈**](quiz/04_io_virtualization_quiz.md)
- ➡️ [**Module 05 — Hypervisor Types**](05_hypervisor_types.md)

<div class="chapter-nav">
  <a class="nav-prev" href="../03_memory_virtualization/">
    <div class="nav-label">◀ 이전</div>
    <div class="nav-title">메모리 가상화</div>
  </a>
  <a class="nav-next" href="../05_hypervisor_types/">
    <div class="nav-label">다음 ▶</div>
    <div class="nav-title">Hypervisor 유형</div>
  </a>
</div>
