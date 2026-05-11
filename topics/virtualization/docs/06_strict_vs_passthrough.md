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
  <a class="page-toc-link" href="#1-why-care-이-모듈이-왜-필요한가">1. Why care?</a>
  <a class="page-toc-link" href="#2-intuition-비유와-한-장-그림">2. Intuition</a>
  <a class="page-toc-link" href="#3-작은-예-64-byte-수신-한-번을-virtio-와-sr-iov-에서-비교">3. 작은 예 — 64 B 수신을 두 path 로 비교</a>
  <a class="page-toc-link" href="#4-일반화-i-o-가상화-스펙트럼과-iommu-의-역할">4. 일반화 — I/O 스펙트럼 + IOMMU</a>
  <a class="page-toc-link" href="#5-디테일-strict-pass-through-관련-기술-스택-혼합-모델">5. 디테일</a>
  <a class="page-toc-link" href="#6-흔한-오해-와-dv-디버그-체크리스트">6. 흔한 오해 + DV 디버그 체크리스트</a>
  <a class="page-toc-link" href="#7-핵심-정리-key-takeaways">7. 핵심 정리</a>
</div>
<!-- DV-SKOOL-CH-TOC:end -->

!!! objective "학습 목표"
    이 모듈을 마치면:

    - **Distinguish** Strict (hypervisor 중재) 와 Passthrough (직접 전달) 의 I/O 경로 차이를 context switch 횟수로 구분할 수 있다.
    - **Trace** 같은 64-byte 패킷 수신을 emulated virtio path 와 SR-IOV passthrough path 로 각각 추적할 수 있다.
    - **Apply** IOMMU 가 passthrough 격리의 _전제 조건_ 인 이유를 DMA 공격 시나리오와 함께 적용한다.
    - **Plan** Hybrid I/O 전략 — 어떤 device 는 strict, 어떤 device 는 passthrough 인지 결정 기준을 설계한다.
    - **Evaluate** AWS Nitro 처럼 "보안은 HW 로, 성능은 passthrough 로" 의 현대 모델을 평가한다.

!!! info "사전 지식"
    - [Module 04](04_io_virtualization.md) — I/O 가상화 기본 (emulation / virtio / SR-IOV)
    - [IOMMU 코스](../../mmu/04_iommu_smmu/) — SMMU / VT-d 의 DMA 격리
    - [Module 05](05_hypervisor_types.md) — Type 1 / Type 2 / KVM 의 trap 경로

---

## 1. Why care? — 이 모듈이 왜 필요한가

I/O 가상화의 가장 큰 trade-off 는 한 문장입니다 — **"hypervisor 가 모든 I/O 를 가로채면 안전하지만 느리다. VM 이 device 에 직접 닿으면 빠르지만 IOMMU 없이는 보안이 깨진다."** 100 Gbps NIC · GPU · NVMe 같은 고대역폭 device 가 들어오면서 _전부 hypervisor 가 가로채는 strict 모델_ 은 throughput 의 _병목_ 이 됐고, 그래서 등장한 것이 SR-IOV / VFIO / pass-through. 그러나 device 가 VM 메모리에 직접 DMA 한다는 것은 **device 가 잘못 동작하거나 악의적이면 host kernel/다른 VM 메모리까지 침해 가능** 하다는 뜻 — 그래서 IOMMU 가 _없으면 안 되는_ 부품이 됐습니다.

이 모듈을 건너뛰면 이후 "왜 클라우드는 SR-IOV 를 쓰는가", "왜 GPU 는 항상 pass-through 인가", "Nitro 가 무엇을 바꿨는가" 같은 질문에 _그림 없이 단어로만_ 답하게 됩니다. 반대로 _두 path 의 hop 수와 IOMMU 의 위치_ 만 잡으면, 새로운 device (DPU, CXL accelerator 등) 가 와도 즉시 적절한 I/O 모델을 선택할 수 있습니다.

---

## 2. Intuition — 비유와 한 장 그림

!!! tip "💡 한 줄 비유"
    **Strict** = 호텔 1층에 **공용 프린터** — 모든 손님이 프런트(hypervisor) 에 출력 요청 → 프런트가 대신 출력 → 출력물 받아 옴. 안전하지만 줄 섬.<br>
    **Passthrough** = 객실(VM) 안에 **전용 프린터** — 손님이 직접 출력. 빠르지만 옆 객실에서 종이/잉크를 훔쳐 가지 않게 _프린터 자체에 잠금 (IOMMU)_ 이 있어야 함.

### 한 장 그림 — 같은 64-byte 패킷, 두 path

```
   Strict (emulated virtio)              Passthrough (SR-IOV VF)
   ──────────────────────────────       ──────────────────────────────
   ┌─── VM ────┐                        ┌─── VM ────┐
   │ App       │                        │ App       │
   │  │ recv() │                        │  │ recv() │
   │  ▼        │                        │  ▼        │
   │ virtio-net│ ← Guest driver         │ ixgbevf   │ ← VF driver (real)
   │  │        │   (가상 device)         │  │        │
   └──┼────────┘                        └──┼────────┘
      │ MMIO write to ring doorbell        │ MMIO write to ring doorbell
      ▼                                    │
   ─────────────────────────              │   (trap 없음 — IOMMU 가
   Hypervisor (EL2 / Ring -1)              │    BAR 영역만 VM 에 매핑)
     ① VM Exit (MMIO trap)                 │
     ② QEMU/vhost 가 ring 읽음              │
     ③ host kernel TAP/bridge 로 forward    ▼
     ④ 다시 VM-Entry                      ─────────────
   ─────────────────────────              IOMMU
        │                                    │ DMA addr → IOVA→PA
        ▼                                    │ (VM 메모리 외 차단)
   Physical NIC ◀──────── packet ───────▶  Physical NIC VF
   
   exits / packet:  ~수회 (ring batching)   exits / packet:  0회
   memcpy:          host kernel ↔ VM         memcpy:          없음
   IOMMU:           역할 작음 (hypervisor    IOMMU:           ★ 필수 격리
                    가 memory 정확성 보장)
```

두 path 의 차이는 _packet 한 개당 hop 수_ 입니다 — strict 는 hypervisor 가 _반드시_ 끼고, passthrough 는 _전혀 안 낍니다_. 대신 passthrough 는 hypervisor 가 해 주던 _보호 (다른 VM 메모리 침범 차단)_ 를 **IOMMU 라는 HW 가 대체** 합니다.

### 왜 이렇게 설계됐는가 — Design rationale

세 가지 요구가 동시에 풀려야 했습니다.

1. **격리** — VM A 의 device 가 VM B 의 메모리를 못 읽어야 함.
2. **성능** — 100 Gbps 라인레이트에서 packet 한 개당 80 ns. hypervisor 가 매번 끼면 라인레이트 불가능.
3. **device 공유** — 한 NIC 를 여러 VM 이 동시에 써야 함 (한 카드 / 한 VM 은 비용 비현실).

Strict 만으로는 1·3 은 풀리지만 2 가 깨지고, naive passthrough 만으로는 2·3 (한 device 1 VM 이라면) 은 풀리지만 1 이 깨집니다. **답은 "passthrough + IOMMU + SR-IOV 의 VF 분할"** — 셋이 동시에 만족돼야 의미가 있습니다. 이 한 줄이 데이터센터의 현재 I/O 모델을 결정한 _전제_.

---

## 3. 작은 예 — 64-byte 수신 한 번을 virtio 와 SR-IOV 에서 비교

가장 단순한 시나리오. NIC 가 **64-byte Ethernet frame** 한 개를 받고, VM 안의 `recv()` 가 그것을 회수합니다. emulated virtio path 와 SR-IOV passthrough path 에서 _같은 일_ 이 어떻게 다르게 처리되는지 step-by-step.

```
   ┌──────────────────────── Strict: virtio-net ────────────────────────┐
   │                                                                     │
   │  ① Physical NIC: frame 수신 → IRQ                                   │
   │  ② Host kernel: IRQ handler → ixgbe driver → TAP/bridge             │
   │  ③ vhost-net (kernel thread): VM 의 virtio RX ring 에 descriptor 채움│
   │  ④ vhost-net 이 VM 에 vIRQ 주입 (EventFD → KVM → vmcs.intr_info)    │
   │  ⑤ KVM: VM-Entry. Guest 의 IDT 가 virtio-net IRQ handler 호출       │
   │  ⑥ Guest virtio-net driver: RX ring 의 desc → skb → netif_rx        │
   │  ⑦ Guest kernel: socket buffer → recv() syscall 깨움                │
   │                                                                     │
   │  hop:  HW → host kernel → vhost → KVM → Guest → app                 │
   │  데이터 복사:  NIC DMA → host RX ring → VM RX ring 으로 _복사 1회_  │
   └─────────────────────────────────────────────────────────────────────┘

   ┌──────────────────────── Passthrough: SR-IOV VF ─────────────────────┐
   │                                                                     │
   │  ① Physical NIC VF: frame 수신                                       │
   │     (VF 는 VM 의 IOVA 공간에 DMA 가능하도록 미리 IOMMU 에 등록됨)    │
   │  ② VF 가 _VM 의 메모리_ 에 직접 DMA — IOMMU 가 IOVA → HPA 변환 후    │
   │     해당 VM 의 RX ring buffer 영역만 허용                            │
   │  ③ VF 가 MSI-X interrupt 발사 — Posted Interrupt 로 _VM 의 vCPU_ 가  │
   │     hypervisor 경유 없이 직접 받음                                   │
   │  ④ Guest 의 ixgbevf driver: 직접 RX ring 폴/IRQ 처리                │
   │  ⑤ skb → recv() 깨움                                                │
   │                                                                     │
   │  hop:  HW → Guest → app  (host kernel/hypervisor 0 hop)             │
   │  데이터 복사:  없음 (DMA 가 _VM 메모리에 직접_)                       │
   └─────────────────────────────────────────────────────────────────────┘
```

| Step | virtio (strict) | SR-IOV (passthrough) |
|---|---|---|
| ① 수신 주체 | 물리 NIC 의 PF | NIC 의 VF (VM 전용) |
| ② DMA target | host kernel 의 RX ring | _VM 의 IOVA 공간_ → IOMMU 가 VM 메모리로 매핑 |
| ③ IRQ 종착지 | host kernel → vhost-net | VM 의 vCPU (Posted Interrupt) |
| ④ Hypervisor 경유 | 매 packet 또는 batch 마다 1회 이상 | **0회** (격리는 IOMMU 가 SetUp 시점에만) |
| ⑤ 데이터 복사 | host → VM 의 vring 복사 1회 (또는 zero-copy vhost) | **없음** (DMA 가 직접 VM 메모리에) |
| ⑥ Guest driver | virtio-net (가상 device) | ixgbevf (실제 device driver) |
| ⑦ exit/packet | ~수개 (batching 의존) | 0 |

**같은 1 packet 의 latency / CPU 비용 차이**: 일반적으로 virtio 는 host CPU 1-2 µs · VM Exit 수회, SR-IOV 는 host CPU 0 · VM Exit 0회. 100 Gbps 에서 packet 수가 분당 수억 개를 넘으면 이 차이가 라인레이트의 성패를 가릅니다.

```c
/* SR-IOV passthrough 의 핵심 setup 코드 (host 측 VFIO) — VF 를 VM 에 할당하기 전
   IOMMU 에 해당 VF 의 DMA 범위를 _VM 의 IOVA 공간으로만_ 묶는다. */
struct vfio_iommu_type1_dma_map map = {
    .argsz   = sizeof(map),
    .flags   = VFIO_DMA_MAP_FLAG_READ | VFIO_DMA_MAP_FLAG_WRITE,
    .vaddr   = (uintptr_t)vm_mem,    /* host 측에서 본 VM 메모리 시작 */
    .iova    = 0x0,                  /* VM 이 보는 IOVA (= guest PA) */
    .size    = vm_mem_size,
};
ioctl(container_fd, VFIO_IOMMU_MAP_DMA, &map);
/* 이 한 번의 ioctl 이후, VF 의 모든 DMA 는 IOMMU 가 자동으로 IOVA→HPA 변환.
   이 범위 밖의 host RAM 접근은 IOMMU 가 HW level 에서 차단 → DMA fault. */
```

!!! note "여기서 잡아야 할 두 가지"
    **(1) packet 1 개당 hypervisor hop 수가 throughput 의 _상한_** — strict 는 hop 수만큼 ceiling 이 내려가고, passthrough 는 ceiling 이 wire speed. 라인레이트가 필요한 워크로드는 passthrough 가 _선택지가 아니라 필수_.<br>
    **(2) IOMMU 는 setup 시점에 _한 번_ 비용 지불, runtime 에는 0** — 매 packet 의 IOVA→HPA 변환은 HW 가 (IOMMU TLB 캐시 hit 시) ns 단위로 처리. 그래서 passthrough 의 "보안" 비용은 무시 가능. _없으면 격리 자체가 불가능_, _있으면 비용 0_.

---

## 4. 일반화 — I/O 가상화 스펙트럼과 IOMMU 의 역할

### 4.1 두 모델은 _스펙트럼의 양 끝_

Strict 와 Passthrough 는 binary 가 아니라 **스펙트럼의 양 끝점** 입니다. 그 사이에 virtio (준가상화) 와 SR-IOV (VF 단위 passthrough) 같은 중간 점이 있습니다.

```
성능   낮음 ◄──────────────────────────────────────────────► 높음
격리   높음 ◄──────────────────────────────────────────────► 낮음 (단, IOMMU 가 채움)

   Full Emulation     VirtIO           SR-IOV VF        Full Passthrough
   ────────────       ────────────     ─────────────    ────────────────
   QEMU 가 device      Guest 에 virtio  PF/VF 분할      device 1 개를
   동작을 SW 로        driver 설치 +     IOMMU 가 VF      VM 에 통째 할당
   완전 흉내           hypervisor 가     마다 격리         hypervisor 무관
                      ring 만 중재
   trap: every IO     trap: ring 단위   trap: 0          trap: 0
   share: 무제한       share: 무제한    share: VF 수      share: 불가 (1:1)
```

위치를 선택하는 기준은 _보통 워크로드의 packet rate / IO depth_:

| 워크로드 | 권장 위치 | 이유 |
|---|---|---|
| Linux GUI VM | Emulation / VirtIO | packet rate 낮음 |
| 일반 웹 서비스 | VirtIO | 적절한 balance |
| 100 Gbps NIC | SR-IOV VF passthrough | line rate 필요 |
| GPU compute | Full passthrough | DMA bandwidth + IRQ rate 모두 큼 |
| NVMe storage | NVMe pass-through 또는 VFIO | latency 민감 |

### 4.2 IOMMU — Passthrough 격리의 _전제_

Passthrough 가 "안전" 하려면 device 가 _허용된 메모리에만_ DMA 하게 강제해야 합니다. CPU 의 MMU 가 process 메모리 격리를 보장하듯, **IOMMU 가 device 메모리 격리를 보장** 합니다.

```
   IOMMU 가 없을 때                       IOMMU 가 있을 때
   ──────────────────────                ─────────────────────────
   VM A 의 driver                        VM A 의 driver
     │ DMA addr = "0xDEAD_BEEF"            │ DMA addr = IOVA 0x1000
     ▼                                     ▼
   NIC: PCIe TLP 발사 (target=0xDEADBEEF) NIC: PCIe TLP 발사 (target=IOVA 0x1000)
     │                                     │
     │                                     ▼
     │                                   IOMMU: VM A 의 page table 조회
     │                                     │ IOVA 0x1000 → HPA 0xABCD_0000
     │                                     │ ─ access 권한 OK? Y
     │                                     │ ─ VM A 의 영역 안인가? Y
     │                                     ▼
     ▼                                   HPA 0xABCD_0000 으로 DMA
   주소 그대로 → host RAM 어디든 가능
   = 다른 VM/host kernel 메모리 침해      = VM A 의 메모리만 접근, 그 외 차단 (DMA fault)
```

| Property | IOMMU 없음 | IOMMU 있음 |
|---|---|---|
| Device 가 보는 주소 | 물리 주소 (HPA) | IOVA (= 가상 주소) |
| Translation | 없음 | IOVA → HPA per-device page table |
| 권한 검사 | 없음 | R/W 별, valid 별 |
| 위반 시 | _침해 성공_ | DMA fault → device 분리 |
| 가상화 가능? | 위험 | 안전 |

이게 §1 의 "**IOMMU 없이는 보안이 깨진다**" 의 실체입니다. ARM 의 SMMU, Intel 의 VT-d, AMD 의 AMD-Vi 가 같은 일을 합니다.

### 4.3 운영 모델 — 거의 모든 production 은 hybrid

실제 cloud 의 VM 은 **두 path 를 한 VM 안에 동시에** 띄웁니다.

| Device 종류 | Path | 이유 |
|---|---|---|
| 관리용 NIC (eth0) | virtio | live migration · device share · 낮은 throughput |
| 데이터 NIC (eth1, 100 G) | SR-IOV VF | line rate 필요 |
| Boot disk | virtio-blk | image 관리 · snapshot 용이 |
| 데이터 disk (NVMe) | NVMe passthrough | latency 민감 |
| GPU | Full passthrough | 공유 불가능한 device |

이 hybrid 가 §5 의 **혼합 모델** 의 형식적 일반화입니다.

---

## 5. 디테일 — Strict / Pass-through / 관련 기술 스택 / 혼합 모델

### 5.1 Strict System 상세 (ARM v8 기준)

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

#### 핵심 원칙: Hypervisor Bypass 불허

| 자원 | 접근 방식 | 오버헤드 |
|------|----------|---------|
| **메모리** | 2-stage translation (VA→IPA→PA) | TLB miss 시 최대 25회 메모리 접근 |
| **CPU 명령어** | 특권 명령어 trap → Hypervisor emulate | VM Exit/Entry (수백~수천 cycle) |
| **I/O** | MMIO/PIO trap → Hypervisor 중재 | VM Exit + 디바이스 에뮬레이션 |
| **인터럽트** | Hypervisor가 수신 후 VM에 가상 주입 | 인터럽트 라우팅 지연 |

#### 3대 성능 오버헤드

##### 1. HW Configuration 오버헤드

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

##### 2. HW Memory Access 오버헤드

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

##### 3. Interrupt Signaling 오버헤드

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

#### Context Switching 상세 분석

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

### 5.2 Hypervisor Pass-through 상세

#### 아키텍처

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

#### 핵심 메커니즘

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

#### Pass-through 의 전제 조건

| 조건 | 이유 |
|------|------|
| **IOMMU** (Intel VT-d, ARM SMMU) | DMA 격리 — 디바이스가 할당된 VM 메모리만 접근하도록 보장 |
| **인터럽트 리맵핑** | 인터럽트를 올바른 VM에 직접 전달 |
| **디바이스 격리** | 하나의 디바이스가 하나의 VM에만 전용 할당 |
| **Huge Page** (선택) | 2-stage translation 오버헤드 최소화 |

#### TechForum 의 시나리오

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

> 이 Unit 은 DV TechForum #55 발표 내용을 기반으로 정리한 것이다.

### 5.3 관련 기술 스택 상세

#### SR-IOV 동작 흐름

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

#### DPDK + VFIO 조합

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

#### VirtIO vs Pass-through 선택 기준

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

### 5.4 Strict vs Pass-through 종합 비교

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

### 5.5 현대 시스템: 혼합 모델

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

#### 실제 사례: 클라우드 인스턴스

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

### 5.6 면접 단골 Q&A

**Q: Strict System 에서 I/O 요청 시 4 번의 context switch 를 설명하라.**
> "EL0→EL1(SVC, 시스템 콜), EL1→EL2(HVC, Hypervisor 호출), EL2→EL1(ERET, 서비스 완료 복귀), EL1→EL0(ERET, 결과 반환). 특히 EL1↔EL2 전환이 비용이 큰데, VMCS/Guest 상태 전체 저장/복원과 TLB flush로 수백~수천 cycle이 소요된다. Pass-through는 EL1↔EL2 전환을 제거하여 2회로 줄인다. 이 차이가 100Gbps 네트워킹처럼 고빈도 I/O에서 결정적이다."

**Q: Pass-through 에서 IOMMU 가 없으면 보안이 왜 붕괴되는가?**
> "IOMMU 없이 pass-through를 하면 DMA 엔진이 물리 주소를 그대로 사용하여 전체 메모리에 접근 가능하다. 공격 시나리오: 악의적 VM0이 NIC의 DMA descriptor에 VM1의 물리 주소를 설정하면 VM1의 데이터(암호키 등) 유출 또는 코드 변조가 가능하고, Hypervisor 메모리를 타겟팅하면 전체 시스템 장악까지 가능하다. IOMMU는 디바이스별 주소 변환 테이블로 할당 범위 밖 접근을 HW에서 차단하며 SW 우회가 불가능하다."

**Q: AWS Nitro 같은 현대 클라우드가 Strict 대신 pass-through 를 채택한 이유는?**
> "성능: Strict System의 VM Exit 오버헤드가 100Gbps+ 네트워킹, NVMe에서 병목이 되었고, 클라우드 고객은 bare metal 대비 성능 격차를 허용하지 않는다. 보안: 전통적으로 pass-through = 보안 약화였으나, Nitro는 이를 HW로 해결했다. Nitro Card가 네트워크/스토리지/보안을 전용 칩에 오프로드하고, IOMMU + HW 격리로 pass-through에서도 강력한 보안을 유지한다. 핵심 전환: 보안을 SW 중재가 아닌 HW(IOMMU, Nitro Card)로 보장하면서 성능은 pass-through로 극대화하는 모델이다."

!!! warning "실무 주의점 — IOMMU disable 실수로 DMA 가 host RAM 직접 access"
    **현상**: Passthrough 된 device 가 VM 의 게스트 메모리 영역을 넘어 host kernel/다른 VM 메모리까지 read/write 가능 → 보안 격리 붕괴.

    **원인**: BIOS `Intel VT-d` / `AMD-Vi` 비활성, kernel cmdline 에 `intel_iommu=on` / `amd_iommu=on` 누락, 또는 `iommu=pt` (passthrough mode) 로 설정해 SVM 격리가 비활성화.

    **점검 포인트**: `dmesg | grep -i "DMAR\|IOMMU"`, `/sys/class/iommu/` 존재 여부, VFIO group 의 isolation, ATS/PRI 옵션과 ACS override 패치 사용 여부.

---

## 6. 흔한 오해 와 DV 디버그 체크리스트

### 흔한 오해

!!! danger "❓ 오해 1 — 'IOMMU 가 자동으로 보안 제공'"
    **실제**: IOMMU 가 켜져도 _page table 정확성_ 과 _DMA fault 처리 SW_ 가 정확해야 안전. 단순 "IOMMU on" 만으로는 부족 — 어떤 IOVA 가 어떤 device 에 할당됐는지, `iommu=pt` (passthrough mode) 같은 잘못된 옵션은 격리를 disable, BAR/MSI-X 리맵 누락 등 SW 정책이 critical.<br>
    **왜 헷갈리는가**: "IOMMU = secure DMA" 마케팅 메시지의 단순화. 실제는 SW 정책 + HW 협업.

!!! danger "❓ 오해 2 — 'Pass-through 는 항상 빠르다'"
    **실제**: Pass-through 자체는 hypervisor hop 0 이지만, _IOMMU TLB miss_ 가 잦으면 page walk 비용이 크고, _Posted Interrupt_ 가 비활성화되면 IRQ 마다 hypervisor 경유로 회귀합니다. Huge page · ACS override · Interrupt remapping 까지 같이 설정해야 실제 bare-metal 성능이 나옴.<br>
    **왜 헷갈리는가**: "직접 = 빠름" 의 단순 매핑.

!!! danger "❓ 오해 3 — 'Pass-through 면 live migration 불가능하다'"
    **실제**: 전통적으로는 device HW state 를 옮길 수 없어서 어려웠지만, **vDPA (Virtual Data Path Acceleration)** 와 **VFIO migration** API 로 SR-IOV VF 의 일부 state 를 SW 가 추출/복원 가능. 단, 모든 vendor driver 가 지원하는 것은 아님.<br>
    **왜 헷갈리는가**: 5년 전까지 사실이었던 명제가 그대로 굳어짐.

!!! danger "❓ 오해 4 — 'SR-IOV 의 VF 는 PF 와 동일한 device 이다'"
    **실제**: VF 는 PF 의 _데이터 경로_ 만 복제한 _얇은_ device — register 일부, 일부 capability 가 없거나 PF 를 통해서만 가능. 예: VLAN tagging, MAC filter 등은 PF 에서만 설정. VM 안에서 `ethtool -k` 가 PF 와 다른 capability 를 보이는 것이 정상.<br>
    **왜 헷갈리는가**: "VF" 도 PCIe function 이라 같은 device 로 인식.

!!! danger "❓ 오해 5 — 'Hybrid 는 곧 strict 와 passthrough 의 _평균_ 성능을 낸다'"
    **실제**: Hybrid 의 핵심은 _데이터 경로_ (NIC, NVMe) 만 passthrough, _제어 경로_ (관리 NIC, boot disk) 만 strict. 데이터 throughput 은 passthrough 와 _동일_, 관리/migration 은 strict 와 _동일_. 평균이 아니라 _각각 그대로_.<br>
    **왜 헷갈리는가**: "혼합 = 가운데" 의 직관.

### DV 디버그 체크리스트 (Strict vs Passthrough 환경에서 자주 보는 실패)

| 증상 | 1차 의심 | 어디 보나 |
|---|---|---|
| Passthrough 된 NIC 가 packet drop 폭증 | IOMMU TLB miss 또는 IRQ steering 실패 | `perf stat -e iommu/events/`, `cat /proc/interrupts`, IRQ affinity |
| VFIO bind 가 `Group ... not viable` 에러 | 같은 IOMMU group 에 다른 device 존재 (ACS 부재) | `ls /sys/kernel/iommu_groups/*/devices/`, ACS override patch 필요성 |
| Guest 에서 device BAR mmap 후 read 가 `0xFFFF_FFFF` | BAR 매핑/EPT mapping 실패 또는 PCIe link down | `lspci -vvv`, Guest `dmesg`, hypervisor 의 EPT pointer |
| `Could not enable iommu=on` 경고 | BIOS VT-d/AMD-Vi 비활성 또는 cmdline 누락 | `dmesg | grep -iE 'DMAR|AMD-Vi'`, `cat /proc/cmdline` |
| Strict (virtio) path 에서 throughput 30% 만 | vhost backend 비활성 또는 ring 크기 부족 | `lsmod | grep vhost`, `ethtool -g`, vCPU pinning |
| Live migration 후 VF 가 reset 됨 | Migration 도중 VF state 손실 | vDPA / VFIO migration capability, vendor driver 버전 |
| 두 VM 이 같은 VF 를 동시에 보임 | SR-IOV VF 할당 leak | `lspci -d ::02xx | grep -i 'Virtual Function'`, libvirt domain XML |
| DMA fault 가 dmesg 에 도배 | Guest driver 가 매핑되지 않은 IOVA 사용 | `dmesg | grep -i 'DMAR.*fault'`, IOVA 범위, VFIO_DMA_MAP 로그 |

이 체크리스트는 §3 의 두 path 가 _setup 단계_ 또는 _runtime 단계_ 의 어느 hop 에서 깨질 수 있는지의 형식화입니다.

---

## 7. 핵심 정리 (Key Takeaways)

- **Strict**: 모든 IO 를 hypervisor 중재 → 강한 격리 + 성능 ↓. context switch 4 회/I/O.
- **Passthrough**: device 직접 VM 할당 → near-native 성능, 격리는 IOMMU 책임. context switch 2 회/I/O.
- **IOMMU 의 결정적 역할**: passthrough 시 device DMA 를 가상 주소 격리. 없으면 device → host 메모리 침해 가능. **격리의 _전제 조건_**.
- **스펙트럼**: Emulation → VirtIO → SR-IOV → Full passthrough — 같은 축의 다른 위치.
- **Hybrid (= production 표준)**: 보통 데이터센터는 데이터 NIC/GPU 만 passthrough (성능 critical), 관리/boot 는 strict. **혼합 ≠ 평균** — 각각 그대로의 성능.

!!! warning "실무 주의점"
    - **IOMMU 켰다고 끝이 아님** — page table / fault 처리 / ACS 까지 모두 SW 정책의 책임.
    - **Pass-through 자체 ≠ 빠름** — Huge page, Posted Interrupt, ACS override 가 동반돼야 실 성능.
    - **VF 는 PF 의 축소판** — vendor 별 capability 차이 큼. Guest driver 호환성 미리 확인.

---

## 다음 모듈

→ [Module 07 — Containers & Modern Virtualization](07_containers_and_modern.md): VM 격리의 무게가 부담스러운 워크로드를 위한 namespace/cgroup 기반 가벼운 격리와, "container 의 속도 + VM 의 격리" 를 노린 microVM.

[퀴즈 풀어보기 →](quiz/06_strict_vs_passthrough_quiz.md)

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
