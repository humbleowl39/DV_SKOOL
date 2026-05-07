# Module 08 — SR-IOV, ATS, P2P, CXL

<div class="learning-meta">
  <span class="meta-badge meta-level-advanced">📊 Advanced</span>
</div>

!!! objective "학습 목표"
    이 모듈을 마치면:

    - **Diagram** SR-IOV 의 PF / VF 구조와 OS 가 VF 를 게스트에 직접 노출하는 흐름을 그릴 수 있다.
    - **Trace** ATS Translation Request → Completion 흐름과 PRI page-fault 처리를 추적한다.
    - **Apply** Peer-to-Peer (P2P) DMA 의 사용 사례 (GPU↔NIC) 와 ACS 정책의 영향을 시나리오에 매핑한다.
    - **Compare** CXL.io vs CXL.cache vs CXL.mem 의 의미와 PCIe 와의 관계를 비교한다.

!!! info "사전 지식"
    - Module 03 (TLP routing, P2P 가능성)
    - Module 06 (Capability list, Extended Cap)
    - 가상화 / IOMMU 기본

## 왜 이 모듈이 중요한가

**Modern 데이터센터 / AI / cloud 의 핵심 PCIe 기능들** 입니다 — SR-IOV (NIC 분할), ATS (IOMMU 캐시), P2P (GPU↔NIC), CXL (메모리 확장). 이들 없이는 hyperscale 워크로드의 효율을 달성 못 함. 검증/설계 결정의 영역도 점차 이쪽으로 이동.

!!! tip "💡 이해를 위한 비유"
    **SR-IOV** ≈ **건물 한 동을 여러 회사에 나눠 임대 (PF=관리사무소, VF=각 호실)**
    **ATS** ≈ **호텔 객실에 미리 키 발급 (IOVA→PA mapping cache)**
    **P2P** ≈ **같은 층 사무실끼리 직접 통화 (RC 거치지 않고 device ↔ device)**
    **CXL** ≈ **PCIe 위에 공유 메모리 / cache 일관성 프로토콜 추가**

## 핵심 개념

**(1) SR-IOV 는 한 PCIe device 가 여러 lightweight Virtual Function (VF) 을 expose 하고, 각 VF 가 별도 BDF + 별도 driver 가 가능 → hypervisor 가 VF 를 게스트에 직접 패스스루. (2) ATS 는 device 가 IOMMU/PTW 결과를 자체 cache 에 보관해 매번 IOMMU walk 회피. (3) P2P 는 두 EP 가 RC 거치지 않고 직접 DMA — ACS (Access Control Service) 가 정책 결정. (4) CXL 은 PCIe 의 PHY 위에 별도 transport (CXL.io/cache/mem) 를 올려 cache 일관성 + 메모리 확장 가능.**

!!! danger "❓ 흔한 오해"
    **오해**: "CXL 은 PCIe 의 새 버전이다."

    **실제**: CXL 은 **PCIe 의 PHY 와 일부 layer 를 공유** 하지만 별도 protocol family. 같은 cable + 같은 connector 로 두 모드 (PCIe / CXL) 중 하나로 동작 (alternate protocol). CXL device 는 CXL alt-protocol negotiation 후 **CXL.io (= PCIe 호환) + CXL.cache + CXL.mem** 을 사용. PCIe Base spec 만으로는 CXL 동작 안 함.

    **왜 헷갈리는가**: 둘이 같은 connector + 같은 PHY 를 쓰고 PCIe 6.0 / CXL 2.0 등 같은 시기 발표.

---

## 1. SR-IOV (Single-Root I/O Virtualization)

```
                   Host Memory
                       ▲
                       │
                       │ DMA
                       │
         ┌─────────────┴─────────────┐
         │       PCIe Device          │
         │                            │
         │   ┌──────┐  Physical Func  │ → BDF (B,D,0)
         │   │  PF  │  - 전체 device  │ → host hypervisor 가 사용
         │   │      │  - VF 생성/관리│
         │   └──────┘                  │
         │                            │
         │   ┌──────┐ ┌──────┐ ┌──────┐│
         │   │ VF 0 │ │ VF 1 │ │ VF N ││ → BDF (B,D,1), (B,D,2), …
         │   │      │ │      │ │      ││
         │   └──────┘ └──────┘ └──────┘│
         │   ↑ 각자 별도 BAR + Doorbell │
         │                            │
         └────────────────────────────┘

         VM₁ ── ATS+IOMMU ── VF 0     ← Hypervisor 가 VF 0 을 VM₁ 에 패스스루
         VM₂ ── ATS+IOMMU ── VF 1
         …
```

### 핵심 특징

- **PF (Physical Function)**: 전체 device 의 entry point, 일반적인 PCIe device 처럼 동작 + VF 생성/제거 권한.
- **VF (Virtual Function)**: lightweight, **자기만의 BDF + BAR + MSI-X**. Configuration register 일부만 지원.
- **VF 의 Configuration Space** 는 PF 의 SR-IOV Capability 에서 derived (VF BAR0 = PF SR-IOV BAR0 + VF index × stride).
- **IOMMU 가 VF 별 PASID 분리** → 게스트가 자기 메모리만 DMA 가능.

### 사용 예: SR-IOV NIC

```
   호스트 → NIC PF → 트래픽 분류 (MAC/VLAN) → VF 0 / VF 1 / VF 2 RX queue
   각 VF 는 게스트 VM 에 패스스루 → VM 이 HW 레벨로 RX/TX
   → 가상화 overhead 거의 0, line rate 달성 가능
```

### SR-IOV Capability (Extended Cap ID 0x0010)

```
   SR-IOV Cap Header
   Initial VFs        : 가능한 VF 갯수
   TotalVFs           : 현재 enable 한 VF 갯수
   NumVFs             : SW 가 활성화한 VF 갯수
   VF Stride          : VF 간 BDF 간격
   First VF Offset    : 첫 VF 의 PF 로부터 BDF offset
   VF Device ID       : VF 의 Device ID (PF 와 다름)
   VF BAR0..5         : VF 의 BAR (size 만 — base 는 enumeration 시 할당)
```

→ **ARI** (Module 06) 가 enable 되어야 256 개 VF 를 지원 (Function # 8-bit 확장).

!!! example "SR-IOV 가 등장한 배경 — 가상화의 hypervisor overhead"
    상황: 100 Gbps NIC 1 장 + VM 100 대.

    **SR-IOV 이전 (Full Emulation)**:

    - VM 의 게스트 OS 는 옛날 NIC (예: Intel e1000) 인 척 속는 **emulated device** 와 통신.
    - VM driver 가 가짜 register 에 access 할 때마다 CPU 가 **Trap (VM-Exit)** → Hypervisor 로 제어 넘어감 → Hypervisor 가 명령 해석 후 실제 PF driver 로 전달.
    - **packet 1 개 송신에 trap 수십 번** → 극도로 느림.

    **VirtIO (반가상화)**:

    - VM 이 자기가 가상이라는 사실을 인정하고 VirtIO driver 사용.
    - VM 과 hypervisor 사이에 **Virtqueue (Ring Buffer)** 공유 메모리.
    - VM 이 packet 50 개를 ring buffer 에 쌓아두고 trap 1 번 (Hypercall) → batching → 효율 ↑.

    **SR-IOV (VF)**:

    - 위 단계를 **하드웨어로 해결** — VF 가 직접 VM 에 패스스루.
    - VM driver 가 VF BAR 에 직접 access → Trap 없음 (IOMMU 가 검증).
    - **packet 1 개 송신에 trap 0 번** — line rate 가능.

    **vDPA (최신)**:

    - VM 안에서는 표준 **VirtIO driver** 그대로.
    - 실제 동작은 SmartNIC 같은 하드웨어가 ring buffer 를 직접 read.
    - **VirtIO 의 driver 표준화 + SR-IOV 의 성능** 결합.

    | 방식 | CPU Trap | Live Migration | 드라이버 표준화 |
    |------|----------|---------------|----------------|
    | Full Emulation | 매우 많음 | 쉬움 | 표준 |
    | VirtIO | 중간 (batching) | 쉬움 | 표준 |
    | SR-IOV (VF) | 거의 없음 | 어려움 | 벤더 종속 |
    | vDPA | 거의 없음 | 가능 | 표준 |

!!! note "MFD vs SR-IOV — 헷갈리기 쉬운 두 가상화 개념"
    둘 다 "한 device 에 여러 function" 이지만 **목적 / 생성 방식 / 권한** 모두 다름.

    | 비교 | MFD (Multi-Function Device) | SR-IOV |
    |------|----------------------------|--------|
    | 기능의 종류 | **이질적** (NIC + Sound 등 서로 다름) | **동질적** (NIC 의 복제) |
    | 생성 시점 | **정적** — 공장에서 HW 고정 | **동적** — 소프트웨어로 실시간 생성/제거 |
    | 권한 | 각 Function 이 독립적 설정 권한 | PF 만 글로벌 권한, VF 는 데이터 통로만 |
    | 목적 | 단가 절감, 공간 절약 | 가상화 성능 극대화 (hypervisor 우회) |
    | Configuration Space | Function 별 full | PF full + VF lightweight |

    **핵심 차이**: MFD 의 Function 들은 **별개의 기능** 을 묶은 것 (예: 한 칩에 NIC + audio). SR-IOV 의 VF 는 **같은 기능의 복제** (예: NIC 1 개의 100 개 가상 NIC).

---

## 2. ATS (Address Translation Service)

```
   기존 (without ATS):
   Device DMA 할 때마다 IOMMU 가 page table walk
   → 모든 transaction 마다 latency + IOMMU 부하

   With ATS:
   1) Device 가 ATS Translation Request 송신 (IOVA 포함)
   2) IOMMU 가 PA 응답 (TR Completion)
   3) Device 가 (IOVA → PA) 를 자기 ATC (Address Translation Cache) 에 저장
   4) 이후 같은 IOVA 의 DMA 는 device 가 PA 직접 사용
   → IOMMU walk 회피, 매번 cache hit
```

### Translation TLP 흐름

```
   Device                                       IOMMU / RC
   ──────                                       ──────────
   ATS Translation Request (with IOVA, PASID)  ──▶
                                                 (IOMMU walk)
                                            ◀── ATS Translation Completion
                                                 (PA, valid bits)

   Device 가 PA 받음, ATC 갱신
   이후:
   Memory Read/Write (with AT field = "Translated") ──▶
                                                 (IOMMU bypass — 이미 PA)
```

→ TLP 의 **AT field** (3-bit) 가 "Untranslated", "Translation Request", "Translated" 표시.

### Invalidate

OS 가 page mapping 변경 시:

```
   OS / IOMMU                                    Device
   ──────────                                    ──────
   ATS Invalidate Request (IOVA range)         ──▶
                                                 (Device ATC entry 무효화)
                                            ◀── ATS Invalidate Completion
```

→ TLB consistency 유지.

### PRI (Page Request Interface)

ATS 가 처리 안 된 IOVA (page fault) 발생 시:

```
   Device 가 PRI Page Request 송신 (어느 IOVA 에 어떤 access)
   OS / IOMMU 가 page-in 처리
   PRI Page Response 로 device 에 알림
   Device 가 ATS 재시도
```

→ ODP (On-Demand Paging) 의 PCIe 측 메커니즘. RDMA 의 ODP (Module 05) 와 같은 원리.

---

## 3. PASID (Process Address Space ID)

```
   하나의 device 가 여러 process / VM 의 메모리에 동시 DMA 시:
       PASID 가 어느 address space 인지 식별 (20-bit)

   TLP 의 PASID prefix 또는 PASID extension 으로 전달
   IOMMU 가 (BDF, PASID) 쌍으로 page table 결정
```

→ Process-aware DMA. SVM (Shared Virtual Memory) 의 기반.

---

## 4. P2P (Peer-to-Peer) DMA

```
            ┌── RC ──┐
            │         │
            │         │
       ┌────┴───┐ ┌───┴────┐
       │ Switch │ │  Switch│
       └─┬───┬──┘ └────┬───┘
         │   │         │
       ┌─┴─┐│  ┌──┐    │
       │EP1│ │  │EP2│   │
       └───┘ │  └──┘    │
             ▲           ▲
             └────────── │  P2P: EP1 → EP2 직접 DMA
                          └  RC 거치지 않음

   사용 예: GPU 가 NIC RX buffer 직접 read → RDMA over GPU
            NVMe 의 DMA 가 GPU memory 직접 access
```

### ACS (Access Control Services)

P2P 를 허용/차단하는 정책:

| ACS bit | 의미 |
|---------|------|
| **Source Validation** | TLP 의 Requester ID 가 진짜 그 port 에서 왔는가 |
| **Translation Blocking** | "Translated" AT TLP 의 정책 |
| **P2P Request Redirect** | P2P request 를 RC 로 redirect 강제 |
| **P2P Completion Redirect** | P2P completion 을 RC 로 redirect |
| **Upstream Forwarding** | Switch port 의 forward 정책 |

→ **Default 보안 정책은 P2P 차단** (RC 우회 가능 = security risk). 명시적으로 enable 해야 P2P 작동.

### 사용 시나리오

| Workload | P2P 효과 |
|----------|---------|
| GPU + NIC 협업 (RDMA over GPU) | NIC RX → GPU 메모리 직접 (CPU 우회) |
| NVMe + GPU (직접 데이터 로드) | NVMe → GPU 메모리 직접 |
| Multi-GPU 통신 (NCCL P2P) | Switch 통해 GPU↔GPU |

---

## 5. CXL (Compute Express Link)

### CXL 의 위치

```
   ┌─────────────────────┐
   │  PCIe PHY (공유)     │ ← 같은 SerDes, 같은 connector
   ├─────────────────────┤
   │  Alternate Protocol │ ← 협상 단계에서 PCIe vs CXL 결정
   ├─────────────────────┤
   │  CXL Link Layer     │  (PCIe DLL 와 다름)
   ├─────────────────────┤
   │  CXL.io / .cache /  │
   │   .mem              │
   └─────────────────────┘
```

### 3 Protocol

| Protocol | 역할 |
|---------|------|
| **CXL.io** | PCIe 와 호환 — Configuration, MMIO, DMA. 모든 CXL device 의 baseline |
| **CXL.cache** | Device 가 host memory 의 cache 일관성 참여 (예: accelerator 가 host CPU cache line 을 공유) |
| **CXL.mem** | Host CPU 가 device-attached memory 를 자기 메모리처럼 access (예: CXL memory module) |

### Device Type

| Type | 사용 protocol | 예 |
|------|--------------|---|
| **Type 1** | .io + .cache | Cache-coherent accelerator (without local memory) |
| **Type 2** | .io + .cache + .mem | Cache-coherent accelerator with attached memory (예: AI accelerator) |
| **Type 3** | .io + .mem | Memory expansion (DDR5 module on CXL link) |

### CXL 2.0 / 3.0 / 3.1 핵심 추가

- **CXL 2.0**: Switching, Pooling (한 memory pool 을 여러 host 가 share)
- **CXL 3.0**: Fabric (multi-host with global memory), 강화된 cache 일관성
- **CXL 3.1**: Trusted execution, security 강화

→ **CXL 은 modern AI/cloud 의 메모리 확장 표준**. PCIe 검증자도 알아야 함.

---

## 6. PCIe 와 CXL 의 검증 영역 비교

| 영역 | PCIe | CXL |
|------|------|-----|
| PHY / LTSSM | 공통 (CXL 도 같은 LTSSM) | + Alternate Protocol Negotiation |
| Link Layer | DLLP, ACK/NAK | CXL Link Layer (다른 mechanism) |
| Transport | TLP | CXL.io = TLP, .cache/.mem = 별도 flit-based |
| Coherence | (없음) | .cache 의 MESI-like 프로토콜 |
| Memory model | (host 와 분리) | .mem 의 host coherence 통합 |

---

## 7. 검증 시나리오 — Advanced 영역

### SR-IOV

| 시나리오 | 목표 |
|---------|------|
| PF enable + VF 256 | TotalVFs/NumVFs setting, ARI 정상 |
| VF BAR access | VF 별 BAR offset 계산 정확 |
| MSI-X table 분리 | 각 VF 의 MSI-X vector 가 독립 |
| FLR on VF | VF 단독 reset, PF 영향 없음 |
| IOMMU 격리 | VM₁ VF 가 VM₂ 메모리 접근 시 차단 |

### ATS

| 시나리오 | 목표 |
|---------|------|
| Translation Request → Completion | TLP 흐름 정상 |
| ATC hit / miss | Cache 동작 |
| Invalidate | OS 의 invalidate 받으면 entry drop |
| PRI page fault | Page Request → Response → 재시도 |

### P2P / ACS

| 시나리오 | 목표 |
|---------|------|
| ACS disabled 시 P2P 동작 | EP1→EP2 직접 DMA |
| ACS Source Validation | spoofed BDF 거부 |
| Multi-GPU NCCL | Switch level P2P |

---

## 핵심 정리 (Key Takeaways)

- **SR-IOV** = 한 device 의 여러 VF, 각 VF 가 별도 BDF + 게스트 직접 패스스루.
- **ATS** = device 의 IOVA→PA cache + Invalidate + PRI (page fault) 통합.
- **PASID** = process 별 address space, SVM 의 기반.
- **P2P** = device ↔ device DMA, ACS 가 정책. GPU↔NIC, NVMe↔GPU 의 핵심.
- **CXL** = PCIe PHY 공유 + 별도 Link Layer + (.io/.cache/.mem). Type 1/2/3 device.

!!! warning "실무 주의점"
    - SR-IOV VF 갯수 = **silicon resource 의 함수**. spec 상 256 까지지만 실제 device 가 4 / 16 / 64 등 제한.
    - ATS Invalidate latency 가 IOMMU 와 device 의 latency 합 — 그동안의 stale TLB 사용 시점 = security/correctness risk.
    - P2P 사용 시 ACS 의 default 차단 정책 모르면 "왜 P2P 안 됨?" hang. 일부 IOMMU/RC 는 P2P 자체를 capability 로 지원 안 함.
    - CXL 은 PCIe 와 같은 connector 라 hot swap 했을 때 PCIe ↔ CXL 협상 다시 발생. 양쪽 모드 모두 검증 필요.
    - PASID 가 enabled 안 된 IOMMU 위에 PASID-aware device 두면 **silently fail** — driver 가 capability 검증 필수.

---

## 다음 모듈

→ [Module 09 — Quick Reference Card](09_quick_reference_card.md)
