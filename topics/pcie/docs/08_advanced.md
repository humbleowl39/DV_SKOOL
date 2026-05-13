# Module 08 — SR-IOV, ATS, P2P, CXL

<!-- DV-SKOOL-CH-CTX:start -->
<div class="chapter-context" data-cat="intercon">
  <a class="chapter-back" href="../">
    <span class="chapter-back-arrow">←</span>
    <span class="chapter-back-icon">🔌</span>
    <span class="chapter-back-text">PCI Express</span>
  </a>
  <span class="chapter-divider">›</span>
  <span class="chapter-marker">Module 08</span>
</div>
<!-- DV-SKOOL-CH-CTX:end -->

<!-- DV-SKOOL-CH-TOC:start -->
<div class="page-toc">
  <span class="page-toc-label">목차</span>
  <a class="page-toc-link" href="#1-why-care-이-모듈이-왜-필요한가">1. Why care?</a>
  <a class="page-toc-link" href="#2-intuition-임대-건물-비유와-한-장-그림">2. Intuition</a>
  <a class="page-toc-link" href="#3-작은-예-vm-의-vf-가-ats-로-iova-한-개를-번역-받는-한-사이클">3. 작은 예 — VF 가 ATS 로 IOVA 번역</a>
  <a class="page-toc-link" href="#4-일반화-가상화-3-축-sr-iov-ats-p2p-와-cxl-의-위치">4. 일반화 — 가상화 3 축 + CXL</a>
  <a class="page-toc-link" href="#5-디테일-sr-iov-cap-ats-tlp-acs-cxl-protocol-stack">5. 디테일</a>
  <a class="page-toc-link" href="#6-흔한-오해-와-dv-디버그-체크리스트">6. 흔한 오해 + DV 디버그 체크리스트</a>
  <a class="page-toc-link" href="#7-핵심-정리-key-takeaways">7. 핵심 정리</a>
</div>
<!-- DV-SKOOL-CH-TOC:end -->

!!! objective "학습 목표"
    이 모듈을 마치면:

    - **Diagram** SR-IOV 의 PF / VF 구조와 OS 가 VF 를 게스트에 직접 노출하는 흐름을 그릴 수 있다.
    - **Trace** ATS Translation Request → Completion 흐름과 PRI page-fault 처리 cycle 을 추적한다.
    - **Apply** Peer-to-Peer (P2P) DMA 의 사용 사례 (GPU↔NIC, NVMe↔GPU) 와 ACS 정책의 영향을 시나리오에 매핑한다.
    - **Compare** CXL.io vs CXL.cache vs CXL.mem 의 의미와 PCIe 와의 관계를 비교한다.
    - **Distinguish** MFD (Multi-Function Device) 와 SR-IOV VF 를 _목적·생성 시점·권한_ 세 축으로 구분한다.

!!! info "사전 지식"
    - [Module 03 — Transaction Layer & TLP](03_tlp.md) — TLP routing, AT field
    - [Module 06 — Configuration & Enumeration](06_config_enumeration.md) — Capability list, ARI, Extended Cap
    - 가상화 / IOMMU 기본 — guest VA → IOVA → PA 의 3 단계 변환

---

## 1. Why care? — 이 모듈이 왜 필요한가

### 1.1 시나리오 — _하나의 GPU_, _64 VM_

당신은 클라우드 운영자. NVIDIA A100 GPU 1 개를 _64 VM 에 분할_ 임대.

순진한 해법: VM 마다 _전체 GPU 시간 슬롯_ 할당. 결과: 95% 시간이 _idle_ — 한 VM 의 inference 작업이 GPU 의 1% 만 사용해도 나머지 99% 시간 동안 _다른 VM 차단_.

**해법: SR-IOV (Single Root I/O Virtualization)**:
- 한 _Physical Function (PF)_ + 64 _Virtual Functions (VFs)_.
- 각 VF 가 _독립적_ BAR + interrupt.
- IOMMU 가 _VF 별 격리_ — VF 끼리 메모리 안 보임.

결과: 64 VM 이 _동시에_ GPU 의 _다른 부분_ 사용. Utilization 80%+.

지금까지의 PCIe 는 **"한 host 의 한 EP 가 host memory 와 직접 대화"** 라는 단일 모델이었습니다. 그런데 _modern 데이터센터·AI·cloud_ 의 워크로드는 그 모델로는 풀리지 않습니다 — ① 한 GPU 를 64 개 VM 이 나눠 써야 하고 (SR-IOV), ② DMA 마다 IOMMU walk 가 일어나면 latency 가 못 견디고 (ATS), ③ NIC RX 가 host memory 거치지 않고 GPU memory 로 바로 들어가야 하며 (P2P), ④ DDR 슬롯이 부족해 메모리를 PCIe 슬롯에 꽂아야 합니다 (CXL).

이 모듈을 건너뛰면 modern PCIe 검증의 _절반_ 이 빠집니다 — VF 별 BAR offset, ATS Invalidate timing, ACS 의 default-block 정책, CXL alternate protocol negotiation 모두 spec 의 별도 절(section)이고, 잘못 알면 silent failure (driver 가 capability 검증 누락 → 동작은 하는데 성능 0) 가 가장 흔합니다. 반대로 이 네 가지 메커니즘을 잡아 두면, `lspci -vvv` 의 `Capabilities: [xxx] Single Root I/O Virtualization` 한 줄을 보고 _"아, 이 device 는 PF 가 VF 256 개까지 derived BAR 로 expose 가능 + ARI enable 필수"_ 라고 즉시 해석됩니다.

---

## 2. Intuition — 임대 건물 비유와 한 장 그림

!!! tip "💡 한 줄 비유"
    **SR-IOV** ≈ **건물 한 동을 여러 회사에 나눠 임대** (PF = 관리사무소, VF = 각 호실, IOMMU = 출입 통제).<br>
    **ATS** ≈ **호텔 객실에 미리 키 발급** (IOVA→PA mapping 을 device 가 ATC 에 cache).<br>
    **P2P** ≈ **같은 층 사무실끼리 직접 통화** (RC 거치지 않고 device ↔ device).<br>
    **CXL** ≈ **PCIe 위에 공유 메모리·cache 일관성 프로토콜 추가** (같은 cable, 다른 layer).

### 한 장 그림 — VM·VF·IOMMU·ATS 가 한 PCIe link 위에 어떻게 얹히는가

```
       Guest VMs (각자 자기 VA 공간)
       ┌─────────┐ ┌─────────┐ ┌─────────┐
       │  VM₀    │ │  VM₁    │ │  VM₂    │
       │ driver  │ │ driver  │ │ driver  │
       └────┬────┘ └────┬────┘ └────┬────┘
            │  guest IOVA   │           │     ← 각 VM 이 자기 view 의 주소 사용
   Hypervisor + IOMMU (BDF + PASID 로 page table 분리)
            │           │           │
   ─ PCIe ──┴───────────┴───────────┴───────────────────────────
            │           │           │
        ┌───▼───┐   ┌───▼───┐   ┌───▼───┐
        │ VF₀   │   │ VF₁   │   │ VF₂   │      ← 각자 BDF + BAR + MSI-X
        │  ATC  │   │  ATC  │   │  ATC  │      ← ATS cache (IOVA → PA)
        └───────┘   └───────┘   └───────┘
            └─────────PF (관리)──────────┘      ← PF 가 VF 생성/삭제 권한
                  │  same silicon
                  │
                  ▼ host memory (PA)
```

### 왜 이렇게 설계됐는가 — Design rationale

세 가지 요구가 동시에 풀려야 했습니다.

1. **가상화 효율**: VM 마다 emulated NIC 을 쓰면 packet 1개에 VM-Exit 가 수십 번 → line rate 못 채움. 하드웨어가 _physical function 을 복제_ 해서 VM 에 직접 노출 (= **SR-IOV**).
2. **IOMMU latency**: 모든 DMA 가 IOMMU page walk 를 거치면 µs 단위 지연. Device 가 PTW 결과를 _자체 cache_ 에 보관 (= **ATS**).
3. **CPU-bypass topology**: GPU 가 NIC 의 RX buffer 를 read 할 때 host memory 를 거치지 않고 _RC 만 우회_ 하면 ~ 10× latency 단축 (= **P2P**), 단 보안을 위해 _명시적 허용_ (= **ACS**).
4. **메모리 확장**: DDR DIMM 슬롯이 부족, PCIe slot 으로 메모리 모듈을 꽂되 _CPU 가 자기 메모리처럼_ load/store 가능해야 (= **CXL.mem**).

세 + 한 요구의 교집합이 이 모듈의 4 개 mechanism. 모두 **"CPU 의 매개를 줄인다"** 라는 한 줄로 정리됩니다.

---

## 3. 작은 예 — VM 의 VF 가 ATS 로 IOVA 한 개를 번역 받는 한 사이클

가장 단순한 시나리오. SR-IOV NIC 의 **VF₀** 가 VM₀ 에 패스스루되어 있음. VM₀ 의 driver 가 RX buffer 의 IOVA `0x4000_0000` 으로 packet 을 수신하려 함. VF 의 ATC 가 비어 있어 ATS Translation Request 한 번 발생.

```
   t (ns) │ Actor          │ Event                                      │ TLP type        │ AT field
   ──────┼────────────────┼─────────────────────────────────────────────┼─────────────────┼─────────
     0   │ VM₀ driver     │ post RX desc with IOVA=0x4000_0000          │ (no TLP)        │ —
    50   │ VF₀ HW         │ wire 에서 packet 수신, ATC lookup → miss     │ (no TLP)        │ —
    60   │ VF₀ HW         │ ① ATS Translation Request (IOVA=0x4000_0000,│ MRd-like        │ 01 (TR)
         │                │    PASID=guest₀, BDF=(B,D,F.VF0))            │   "TR Request"  │
   ─── upstream to RC ──▶
   100   │ RC + IOMMU     │ ② IOMMU page walk: guest IOVA → host PA      │ —               │ —
         │                │    PA = 0xABCD_0000                          │                 │
   150   │ RC + IOMMU     │ ③ ATS Translation Completion                 │ CplD-like       │ 10 (Translated)
         │                │    (PA=0xABCD_0000, R/W=both, N=0)           │   "TR Cpl"      │
   ◀──── downstream to VF ───
   200   │ VF₀ HW         │ ④ ATC 에 (0x4000_0000 → 0xABCD_0000) 캐시      │ —               │ —
   210   │ VF₀ HW         │ ⑤ packet 256B 를 PA 로 MWr 송신              │ MWr 4DW         │ 10 (Translated)
         │                │    (이번에는 IOMMU walk 우회)                 │                 │
   ─── upstream to RC ──▶
   260   │ RC             │ ⑥ IOMMU 가 AT=10 (Translated) 확인 → bypass  │ —               │ —
   270   │ Host DRAM      │ packet 256B 가 PA 0xABCD_0000 에 land        │ (DMA complete)  │ —
   280   │ VF₀ HW         │ ⑦ MSI-X 송신 (VF 별 vector)                  │ MWr 1 DW (MSI-X)│ 00 또는 10
   320   │ VM₀ driver     │ guest interrupt 수신 → packet 처리            │ —               │ —
```

### 단계별 의미

| Step | 누가 | 무엇을 | 왜 |
|---|---|---|---|
| ① | VF₀ HW | ATS Translation Request TLP 송신 (AT=01) | ATC miss → IOMMU 에 번역 요청 |
| ② | IOMMU | (BDF, PASID, IOVA) → host PA 변환 (page walk) | PASID 가 guest VM 의 page table 선택 |
| ③ | RC | TR Completion (PA + 권한 bit) 응답 | ATS 의 핵심 결과 |
| ④ | VF₀ ATC | (IOVA → PA) 항목 cache | 이후 같은 IOVA 는 walk 면제 |
| ⑤ | VF₀ HW | MWr (AT=10, Translated) 로 PA 직접 사용 | IOMMU 가 다시 walk 안 함 |
| ⑥ | RC + IOMMU | AT=10 이면 검증만 (또는 ACS 정책) | "이미 번역됐다" 신뢰 |
| ⑦ | VF₀ HW | MSI-X 로 guest IRQ | VF 별 vector, IOMMU 가 interrupt remap |

```c
// VF 의 ATS Cap (Extended Cap ID 0x000F) 활성화 — host hypervisor 가 호출
void enable_ats(uint16_t bdf_vf) {
    uint16_t ats_off = find_ext_cap(bdf_vf, 0x000F);
    if (!ats_off) return; // ATS 미지원
    uint16_t ctrl = cfg_read16(bdf_vf, ats_off + 0x06);
    ctrl |= (1 << 15); // ATS Enable bit
    ctrl |= (32 & 0x1F); // Smallest Translation Unit (STU) hint
    cfg_write16(bdf_vf, ats_off + 0x06, ctrl);
}

// ATC Invalidate 처리 (host → device) — page 가 unmap 될 때
void ats_invalidate(uint16_t bdf_vf, uint64_t iova, uint32_t len) {
    // RC 가 ATS Invalidate Request TLP 송신, device 가 ATC entry drop
    // device 응답으로 ATS Invalidate Completion (모든 inflight 처리 후)
    // 이때 device 는 해당 IOVA 의 in-flight DMA 가 완료 또는 abort 됐음을 보장
}
```

!!! note "여기서 잡아야 할 두 가지"
    **(1) AT field 가 TLP 의 행동 규약을 바꾼다** — 같은 MRd/MWr 라도 AT=00 (Untranslated) 면 IOMMU 가 매번 walk, AT=10 (Translated) 면 IOMMU bypass. ATS 의 본질은 _device 가 이미 번역했음을 RC 에게 알려주는 신호_ 이고, RC 는 그 신호를 _믿어주는 대신 ACS 로 검증_ 합니다.<br>
    **(2) Invalidate 는 in-flight DMA 와 race 가 핵심** — OS 가 page 를 unmap 할 때 device 의 ATC 만 비우면 끝나는 게 아니라, 그 IOVA 를 사용 중인 _in-flight TLP_ 가 모두 끝날 때까지 Invalidate Completion 을 보내면 안 됨. 그래서 ATS 검증의 가장 어려운 corner case 는 Invalidate-during-DMA. RDMA 의 ODP (Module 05 of RDMA) 와 같은 원리.

---

## 4. 일반화 — 가상화 3 축 (SR-IOV, ATS, P2P) 와 CXL 의 위치

### 4.1 가상화의 3 축

| 축 | 무엇을 해결 | TLP 어휘 |
|---|---|---|
| **SR-IOV** | 한 device 의 _function 복제_ → VM 직접 패스스루 | PF/VF BDF, derived BAR |
| **ATS** | IOMMU walk 의 _latency_ | AT field, TR Req/Cpl, Invalidate |
| **P2P + ACS** | RC 우회 path 의 _허용 / 보안_ | ACS Cap, P2P Redirect |
| (보조) **PASID** | _process 분리_ (한 VF 안에서 여러 user) | PASID prefix |

### 4.2 SR-IOV 구조

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

### 4.3 ATS / PRI 의 두 경로

```
   Normal path (ATC hit) :
   Device ──MWr(AT=10, PA)──▶ RC ──▶ DRAM

   ATC miss path :
   Device ──TR Req(AT=01, IOVA)─▶ RC+IOMMU
            ◀─TR Cpl(PA)─────────  RC+IOMMU
   Device ──MWr(AT=10, PA)──▶ RC ──▶ DRAM

   Page fault path (PRI) :
   Device ──TR Req(AT=01, IOVA)─▶ RC+IOMMU
            ◀─TR Cpl(N=1, no PA)── RC+IOMMU   ← 매핑 없음 통보
   Device ──PRI Page Request────▶ OS via interrupt
            ◀─PRI Page Response── OS가 page-in 후 응답
   Device ──TR Req 재시도────────▶ ...
```

### 4.4 P2P 의 정책 결정자 = ACS

```
                  RC
                  │
        ┌────── Switch ──────┐    ← Switch 의 port 가 ACS bit 으로 정책 결정
        │                    │
       EP1 ◀── P2P DMA ───▶ EP2
```

→ 같은 switch 아래 두 EP 가 P2P 가능 여부는 _switch 의 ACS_ 가 결정. RC 의 ACS 도 별도 영향 (P2P Request Redirect).

### 4.5 CXL — PCIe 와의 관계

```
   같은 connector + 같은 PHY
            │
            ▼
   ┌────────────────────┐
   │ Alternate Protocol │   ← 협상 단계 (LTSSM 초기) 에서 결정
   └────────────────────┘
            │
   ┌────────┴──────────┐
   │                    │
 PCIe path          CXL path
 (Module 01~07)     ├─ CXL.io  : PCIe 호환 (Configuration, MMIO, DMA)
                    ├─ CXL.cache: device → host cache 일관성 참여
                    └─ CXL.mem  : host → device-attached memory
```

→ CXL 은 PCIe 의 _새 버전_ 이 아니라 _대안 프로토콜_. 같은 cable, 다른 transport.

---

## 5. 디테일 — SR-IOV Cap, ATS TLP, ACS, CXL protocol stack

### 5.1 SR-IOV 핵심 특징

- **PF (Physical Function)**: 전체 device 의 entry point, 일반적인 PCIe device 처럼 동작 + VF 생성/제거 권한.
- **VF (Virtual Function)**: lightweight, **자기만의 BDF + BAR + MSI-X**. Configuration register 일부만 지원.
- **VF 의 Configuration Space** 는 PF 의 SR-IOV Capability 에서 derived (VF BAR0 = PF SR-IOV BAR0 + VF index × stride).
- **IOMMU 가 VF 별 PASID 분리** → 게스트가 자기 메모리만 DMA 가능.

#### 사용 예: SR-IOV NIC

```
   호스트 → NIC PF → 트래픽 분류 (MAC/VLAN) → VF 0 / VF 1 / VF 2 RX queue
   각 VF 는 게스트 VM 에 패스스루 → VM 이 HW 레벨로 RX/TX
   → 가상화 overhead 거의 0, line rate 달성 가능
```

#### SR-IOV Capability (Extended Cap ID 0x0010)

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

### 5.2 ATS — TLP 흐름 상세

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

#### Translation TLP 흐름

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

#### Invalidate

OS 가 page mapping 변경 시:

```
   OS / IOMMU                                    Device
   ──────────                                    ──────
   ATS Invalidate Request (IOVA range)         ──▶
                                                 (Device ATC entry 무효화)
                                            ◀── ATS Invalidate Completion
```

→ TLB consistency 유지.

#### PRI (Page Request Interface)

ATS 가 처리 안 된 IOVA (page fault) 발생 시:

```
   Device 가 PRI Page Request 송신 (어느 IOVA 에 어떤 access)
   OS / IOMMU 가 page-in 처리
   PRI Page Response 로 device 에 알림
   Device 가 ATS 재시도
```

→ ODP (On-Demand Paging) 의 PCIe 측 메커니즘. RDMA 의 ODP 와 같은 원리.

### 5.3 PASID (Process Address Space ID)

```
   하나의 device 가 여러 process / VM 의 메모리에 동시 DMA 시:
       PASID 가 어느 address space 인지 식별 (20-bit)

   TLP 의 PASID prefix 또는 PASID extension 으로 전달
   IOMMU 가 (BDF, PASID) 쌍으로 page table 결정
```

→ Process-aware DMA. SVM (Shared Virtual Memory) 의 기반.

### 5.4 P2P (Peer-to-Peer) DMA

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

#### ACS (Access Control Services)

P2P 를 허용/차단하는 정책:

| ACS bit | 의미 |
|---------|------|
| **Source Validation** | TLP 의 Requester ID 가 진짜 그 port 에서 왔는가 |
| **Translation Blocking** | "Translated" AT TLP 의 정책 |
| **P2P Request Redirect** | P2P request 를 RC 로 redirect 강제 |
| **P2P Completion Redirect** | P2P completion 을 RC 로 redirect |
| **Upstream Forwarding** | Switch port 의 forward 정책 |

→ **Default 보안 정책은 P2P 차단** (RC 우회 가능 = security risk). 명시적으로 enable 해야 P2P 작동.

#### 사용 시나리오

| Workload | P2P 효과 |
|----------|---------|
| GPU + NIC 협업 (RDMA over GPU) | NIC RX → GPU 메모리 직접 (CPU 우회) |
| NVMe + GPU (직접 데이터 로드) | NVMe → GPU 메모리 직접 |
| Multi-GPU 통신 (NCCL P2P) | Switch 통해 GPU↔GPU |

### 5.5 CXL (Compute Express Link)

#### CXL 의 위치

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

#### 3 Protocol

| Protocol | 역할 |
|---------|------|
| **CXL.io** | PCIe 와 호환 — Configuration, MMIO, DMA. 모든 CXL device 의 baseline |
| **CXL.cache** | Device 가 host memory 의 cache 일관성 참여 (예: accelerator 가 host CPU cache line 을 공유) |
| **CXL.mem** | Host CPU 가 device-attached memory 를 자기 메모리처럼 access (예: CXL memory module) |

#### Device Type

| Type | 사용 protocol | 예 |
|------|--------------|---|
| **Type 1** | .io + .cache | Cache-coherent accelerator (without local memory) |
| **Type 2** | .io + .cache + .mem | Cache-coherent accelerator with attached memory (예: AI accelerator) |
| **Type 3** | .io + .mem | Memory expansion (DDR5 module on CXL link) |

#### CXL 2.0 / 3.0 / 3.1 핵심 추가

- **CXL 2.0**: Switching, Pooling (한 memory pool 을 여러 host 가 share)
- **CXL 3.0**: Fabric (multi-host with global memory), 강화된 cache 일관성
- **CXL 3.1**: Trusted execution, security 강화

→ **CXL 은 modern AI/cloud 의 메모리 확장 표준**. PCIe 검증자도 알아야 함.

### 5.6 PCIe 와 CXL 의 검증 영역 비교

| 영역 | PCIe | CXL |
|------|------|-----|
| PHY / LTSSM | 공통 (CXL 도 같은 LTSSM) | + Alternate Protocol Negotiation |
| Link Layer | DLLP, ACK/NAK | CXL Link Layer (다른 mechanism) |
| Transport | TLP | CXL.io = TLP, .cache/.mem = 별도 flit-based |
| Coherence | (없음) | .cache 의 MESI-like 프로토콜 |
| Memory model | (host 와 분리) | .mem 의 host coherence 통합 |

### 5.7 검증 시나리오 — Advanced 영역

#### SR-IOV

| 시나리오 | 목표 |
|---------|------|
| PF enable + VF 256 | TotalVFs/NumVFs setting, ARI 정상 |
| VF BAR access | VF 별 BAR offset 계산 정확 |
| MSI-X table 분리 | 각 VF 의 MSI-X vector 가 독립 |
| FLR on VF | VF 단독 reset, PF 영향 없음 |
| IOMMU 격리 | VM₁ VF 가 VM₂ 메모리 접근 시 차단 |

#### ATS

| 시나리오 | 목표 |
|---------|------|
| Translation Request → Completion | TLP 흐름 정상 |
| ATC hit / miss | Cache 동작 |
| Invalidate | OS 의 invalidate 받으면 entry drop |
| PRI page fault | Page Request → Response → 재시도 |
| Invalidate during in-flight DMA | in-flight 완료 보장 후 Cpl |

#### P2P / ACS

| 시나리오 | 목표 |
|---------|------|
| ACS disabled 시 P2P 동작 | EP1→EP2 직접 DMA |
| ACS Source Validation | spoofed BDF 거부 |
| Multi-GPU NCCL | Switch level P2P |

---

## 6. 흔한 오해 와 DV 디버그 체크리스트

### 흔한 오해

!!! danger "❓ 오해 1 — 'CXL 은 PCIe 의 새 버전이다'"
    **실제**: CXL 은 **PCIe 의 PHY 와 일부 layer 를 공유** 하지만 별도 protocol family. 같은 cable + 같은 connector 로 두 모드 (PCIe / CXL) 중 하나로 동작 (alternate protocol). CXL device 는 CXL alt-protocol negotiation 후 **CXL.io (= PCIe 호환) + CXL.cache + CXL.mem** 을 사용. PCIe Base spec 만으로는 CXL 동작 안 함.<br>
    **왜 헷갈리는가**: 둘이 같은 connector + 같은 PHY 를 쓰고 PCIe 6.0 / CXL 2.0 등 같은 시기 발표.

!!! danger "❓ 오해 2 — 'SR-IOV 의 VF 도 일반 PCI device 처럼 모든 Cap 을 가진다'"
    **실제**: VF 는 **lightweight** — Configuration Space 의 일부 (Type 0 header + 일부 Cap) 만 가지며, BAR 도 PF 의 SR-IOV Cap 에서 derived (`VF_BAR = PF SR-IOV BAR + VF_index × Stride`). VF 가 자기만의 AER Cap 을 _독립_ 으로 가지지 않을 수 있고, PM Cap 도 보통 PF 가 대행. Driver 가 VF 에 일반 device 처럼 모든 Cap 을 기대하면 silent failure.<br>
    **왜 헷갈리는가**: BDF 가 독립이라 완전히 별개 device 처럼 보여서.

!!! danger "❓ 오해 3 — 'ATS 를 enable 하면 모든 DMA 가 자동으로 빨라진다'"
    **실제**: ATS 의 효과는 _같은 IOVA 의 재사용 빈도_ 에 의존. 매 DMA 마다 다른 IOVA (예: random scatter-gather) 면 매번 TR Req 발생 → walk + TR latency 가 오히려 추가. ATS 가 의미가 있는 워크로드 = _hot working set 이 ATC 크기 안에 들어옴_. 게다가 Invalidate 중에는 in-flight DMA 처리 race 가 발생해 오히려 latency tail 이 늘 수 있음.<br>
    **왜 헷갈리는가**: "cache = 빠르다" 단순 매핑.

!!! danger "❓ 오해 4 — 'P2P 는 enable 만 하면 동작한다'"
    **실제**: ACS 의 _default_ 는 P2P 를 _차단_ 합니다 (보안 정책 — RC 가 모든 TLP 를 보지 못하면 spoofing 가능). P2P 가 동작하려면 (a) 두 EP 사이의 모든 switch port 의 ACS 가 P2P 허용으로 설정, (b) RC 자체가 P2P 를 capability 로 지원해야 함. 일부 enterprise CPU 의 RC 는 P2P 자체를 지원 안 함 — IO die 가 강제로 redirect.<br>
    **왜 헷갈리는가**: NVIDIA GPU/Mellanox NIC 처럼 _이미 BIOS/driver 가 ACS 를 자동 설정해주는_ 환경에 익숙해져서.

!!! danger "❓ 오해 5 — 'PASID 가 ATS 와 같이 enable 되면 OS 가 자동 처리'"
    **실제**: PASID 는 _별도 Extended Cap (0x0023)_ 이고 device 가 명시적으로 지원해야 함. PASID-aware device 를 PASID 미지원 IOMMU 위에 두면 _silently fail_ — TLP 의 PASID prefix 는 무시되고 모든 DMA 가 같은 page table 로 갑니다. Driver 가 두 Cap 의 presence 를 _쌍으로_ 검증해야 함.<br>
    **왜 헷갈리는가**: ATS 와 PASID 가 _보통_ 같이 enable 되어 한 묶음으로 인식.

### DV 디버그 체크리스트 (이 모듈 내용으로 마주칠 첫 실패들)

| 증상 | 1차 의심 | 어디 보나 |
|---|---|---|
| VF enable 후 `lspci` 에 VF 가 안 보임 | PF SR-IOV Cap 의 NumVFs 미설정 or ARI off | `setpci -s <PF_BDF> ECAP10.W=...` 의 NumVFs 필드, `lspci -vvv` 의 SR-IOV 줄 |
| VF BAR access 시 `0xFFFFFFFF` read | VF BAR base 가 미할당 | PF SR-IOV BAR + VF_index × Stride 계산 후 자원 풀에 alloc 됐는지 |
| VM 안에서 VF 가 RX 0 packet | IOMMU 의 (BDF, PASID) → guest IOVA mapping 누락 | `dmesg \| grep -i iommu`, host 의 VFIO/iommu group 설정 |
| ATS Translation Request 가 안 가는 듯 | ATC 가 항상 hit (또는 Cap enable bit 0) | ATS Cap (0x000F) 의 Enable bit, ATC 의 invalidation 시점 |
| ATC stale data 사용 (CV mismatch) | Invalidate Completion 전 reuse | OS 의 invalidate-then-unmap 순서, device 의 inflight tracking |
| P2P MWr 가 RC 까지 올라옴 (Redirect 발생) | Switch port 의 ACS P2P Request Redirect set | `lspci -vvv \| grep -A5 ACSCap`, ACSCtl 값 |
| PRI page fault 받은 후 device hang | OS 가 PRI Page Response 안 보냄 또는 Response Code 가 fail | IOMMU 의 PRI 큐 backlog, `dmesg` 의 PRI 메시지 |
| CXL device 가 PCIe 모드로만 동작 | Alt-protocol negotiation 실패 | LTSSM trace 의 Modified TS1/TS2 (CXL flag), board 의 strap 설정 |
| `cat /sys/kernel/iommu_groups/*` 에 device 들이 한 group 으로 묶임 | ACS 비활성화 (또는 미지원) → IOMMU 가 격리 못 함 | switch port 의 ACS Cap presence, kernel 의 `pci=acs_override` 옵션 |

---

## 7. 핵심 정리 (Key Takeaways)

- **SR-IOV** = 한 device 의 여러 VF, 각 VF 가 별도 BDF + 게스트 직접 패스스루. PF 가 관리 권한, VF 는 데이터 통로.
- **ATS** = device 의 IOVA→PA cache. _재사용 IOVA_ 만 의미 있음. Invalidate-during-DMA 가 가장 어려운 corner.
- **PASID** = process 별 address space, SVM 의 기반. 별도 Cap 으로 _device + IOMMU_ 양쪽 모두 지원해야.
- **P2P + ACS** = device ↔ device DMA + 허용 정책. Default 는 _차단_. GPU↔NIC, NVMe↔GPU 의 핵심.
- **CXL** = PCIe PHY 공유 + 별도 Link Layer + (.io/.cache/.mem). Type 1/2/3 device. _PCIe 의 새 버전 아님_.

!!! warning "실무 주의점"
    - SR-IOV VF 갯수 = **silicon resource 의 함수**. spec 상 256 까지지만 실제 device 가 4 / 16 / 64 등 제한.
    - ATS Invalidate latency 가 IOMMU 와 device 의 latency 합 — 그동안의 stale TLB 사용 시점 = security/correctness risk.
    - P2P 사용 시 ACS 의 default 차단 정책 모르면 "왜 P2P 안 됨?" hang. 일부 IOMMU/RC 는 P2P 자체를 capability 로 지원 안 함.
    - CXL 은 PCIe 와 같은 connector 라 hot swap 했을 때 PCIe ↔ CXL 협상 다시 발생. 양쪽 모드 모두 검증 필요.
    - PASID 가 enabled 안 된 IOMMU 위에 PASID-aware device 두면 **silently fail** — driver 가 capability 검증 필수.
    - SR-IOV + ATS + PASID 의 stacked 검증이 가장 어려움 — 각 축의 단독 검증 통과 후 _조합 시나리오_ 가 별도 sign-off.

### 7.1 자가 점검

!!! question "🤔 Q1 — ATS Invalidate race (Bloom: Analyze)"
    IOMMU 가 page unmap → ATS Invalidate 발송. Device 의 ATC (cache) 가 _아직 cache 응답_ → invalidate _도착 전_ DMA 사용. Race?

    ??? success "정답"
        Spec: ATS Invalidate 의 **Completion** 받기 _전_ IOMMU 는 _unmap 완료 보고_ 못함.

        - IOMMU: unmap 요청 후 ATS Invalidate 전송.
        - 도착할 때까지: device 의 ATC stale TLB 가능.
        - Completion 수신 후: ATC 무효화 확정 → OS 가 _page free_ 안전.

        DV: ATS Invalidate completion latency 측정 → IOMMU 의 _unmap 응답 wait_ SVA.

!!! question "🤔 Q2 — SR-IOV + ATS + PASID stack (Bloom: Evaluate)"
    셋 조합. _가장 흔한 silent fail_?

    ??? success "정답"
        **PASID capability mismatch**:
        - Device: PASID-aware (예: GPU).
        - IOMMU: PASID 미지원.
        - Driver: capability 검증 누락.

        결과: device 가 _PASID-tagged TLP_ 보냄 → IOMMU 가 _ignore_ → 모든 DMA 가 _wrong context_.

        Driver 가 _`pci_pasid_features`_ 같은 capability 검증 필수.

### 7.2 출처

**External**
- PCIe SR-IOV / ATS / PASID specifications
- CXL Consortium spec
- *Linux IOMMU subsystem*

---

## 다음 모듈

→ [Module 09 — Quick Reference Card](09_quick_reference_card.md): 모든 모듈의 핵심을 한 페이지에 압축. 검증/리뷰 시 보조 자료.

[퀴즈 풀어보기 →](quiz/08_advanced_quiz.md)


--8<-- "abbreviations.md"
--8<-- "_inc/topic_abbr.md"
