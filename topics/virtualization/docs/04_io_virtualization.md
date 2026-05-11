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
  <a class="page-toc-link" href="#1-why-care-이-모듈이-왜-필요한가">1. Why care?</a>
  <a class="page-toc-link" href="#2-intuition-비유와-한-장-그림">2. Intuition</a>
  <a class="page-toc-link" href="#3-작은-예-virtio-net-한-패킷-tx-1-사이클">3. 작은 예 — VirtIO TX 1 사이클</a>
  <a class="page-toc-link" href="#4-일반화-3-가지-io-가상화-모델">4. 일반화 — 3 가지 모델</a>
  <a class="page-toc-link" href="#5-디테일-emulation-virtio-passthrough-iommu">5. 디테일</a>
  <a class="page-toc-link" href="#6-흔한-오해-와-dv-디버그-체크리스트">6. 흔한 오해 + DV 디버그 체크리스트</a>
  <a class="page-toc-link" href="#7-핵심-정리-key-takeaways">7. 핵심 정리</a>
</div>
<!-- DV-SKOOL-CH-TOC:end -->

!!! objective "학습 목표"
    이 모듈을 마치면:

    - **Distinguish** Emulation, Paravirtualization (VirtIO), Passthrough (SR-IOV / VFIO) 3 가지 모델을 VM Exit 빈도 / Guest 수정 / 디바이스 공유 관점에서 구분할 수 있다.
    - **Apply** SR-IOV 의 PF/VF 분리, IOMMU 의 역할을 적용할 수 있다.
    - **Identify** VirtIO 의 vring + queue 메커니즘이 어떻게 batching 으로 VM Exit 을 일정하게 유지하는지 식별한다.
    - **Trace** 한 패킷이 VirtIO front-end driver → vring → host vhost backend → wire 까지 흐르는 path 를 추적할 수 있다.
    - **Decide** 시나리오 (개발 / 범용 / 고성능 / 저지연) 에 따른 적합한 I/O 가상화 방식을 결정할 수 있다.

!!! info "사전 지식"
    - [Module 01-03](01_virtualization_fundamentals.md)
    - [MMU 코스의 IOMMU/SMMU](../../mmu/04_iommu_smmu/)

---

## 1. Why care? — 이 모듈이 왜 필요한가

CPU + Memory 가상화는 _상태_ 의 격리이고, I/O 가상화는 _이벤트 + 데이터 흐름_ 의 격리입니다. 100 Gbps NIC, NVMe SSD, GPU 같은 _고대역폭 디바이스_ 의 throughput 은 거의 전적으로 I/O 가상화 모델 선택에서 결정됩니다.

이 모듈을 건너뛰면 — VirtIO 가 왜 빠른지, SR-IOV 가 어떻게 1 NIC 으로 128 VM 을 지원하는지, IOMMU 가 _그냥 보안 기능_ 이 아니라 가상화 자체의 전제 조건이라는 게 — 모두 외워야 하는 사실. 한 패킷의 1 cycle 추적과 VM Exit 산식만 잡으면 나머지는 변형입니다.

---

## 2. Intuition — 비유와 한 장 그림

!!! tip "💡 한 줄 비유"
    **I/O Virtualization** = **공용 프린터 vs 전용 프린터** .<br>
    **Emulation** = 비서가 프린터를 대신 써 줌 (모든 인쇄 요청이 비서를 거침). **VirtIO** = 비서와 _공유 트레이_ 로 인쇄물을 한꺼번에 넘김 (batching). **Passthrough** = VM 이 프린터를 _혼자_ 가짐. **SR-IOV** = 한 프린터가 _여러 트레이_ 를 갖고 각 VM 이 자기 트레이로 직접 출력.

### 한 장 그림 — 4 가지 모델의 데이터 경로

```
   Emulation (느림)              VirtIO (중간)           SR-IOV (빠름)        Passthrough (최고)
   ──────────────────           ──────────────────      ─────────────────     ───────────────
   App                           App                     App                   App
    │ I/O syscall                 │ I/O syscall            │ I/O syscall         │ I/O syscall
    ▼                             ▼                        ▼                     ▼
   Guest OS (e1000 drv)         Guest OS (virtio drv)    Guest OS (vf drv)     Guest OS (full drv)
    │ MMIO write                   │ ring write             │ MMIO write          │ MMIO write
    ▼ ▶ VM Exit                    ▼                        │  (no exit)          │  (no exit)
   Hypervisor                    Virtqueue (shared mem)     │                      │
    │ "e1000 모방"                 │ batched                 │                      │
    ▼                             ▼ kick (1 회 exit)        │                      │
   Physical NIC                  vhost backend             │                      │
                                  │                         │                      │
                                  ▼                         ▼                     ▼
                                Physical NIC               VF (한 NIC 내)        Physical NIC
```

### 왜 이 디자인인가 — Design rationale

세 가지 요구가 동시에 풀려야 했습니다.

1. **Guest 미수정** (호환성) — 기존 OS 가 그대로 돌아야 한다.
2. **VM Exit 최소화** (성능) — I/O 당 VM Exit 이 1 회 이상이면 100 Gbps 가 안 된다.
3. **VM 격리** (보안) — DMA 가 다른 VM / host 메모리 침해 불가.

이 3 가지 vector 위에서 서로 다른 점을 잡은 것이 4 가지 모델입니다 — Emulation 은 (1) 만, VirtIO 는 (2) 부분 + (3), SR-IOV 는 (2) + (3) 둘 다, Passthrough 는 (2) 만. 현대 클라우드는 워크로드마다 다른 점을 골라 _혼합_ 합니다.

---

## 3. 작은 예 — VirtIO-net 한 패킷 TX 1 사이클

가장 단순한 시나리오. Guest 안 application 이 `send(fd, buf, 1500)` 한 번. 이 한 패킷이 VirtIO 의 ring 을 어떻게 흐르는지 step-by-step.

```
   ┌──────── Guest ────────┐                          ┌─── Host (vhost-net) ────┐
   │  App → send()         │                          │                         │
   │     │                 │                          │                         │
   │     ▼                 │                          │                         │
   │  socket → virtio_net  │                          │                         │
   │     │  ① pkt buffer 준비                          │                         │
   │     ▼                 │                          │                         │
   │  add_buf(virtqueue)   │                          │                         │
   │     │  ② descriptor table 에 [addr=guest IPA,   │                         │
   │     │    len=1500, flags=NEXT/WRITE] 한 entry   │                         │
   │     ▼                 │                          │                         │
   │  ③ avail_ring[head++] = desc_idx                │                         │
   │     ▼                 │                          │                         │
   │  ④ virtqueue_kick()   │                          │                         │
   │     = MMIO write to notify reg ━━━━━━━━━━━━━━━━━━━━━━▶│ ⑤ VM Exit (vhost 가  │
   │                       │                          │   eventfd 로 wake)      │
   │     │                 │                          │   ▼ ⑥ desc 읽기 (IOVA)  │
   │     │                 │                          │   ▼ ⑦ IOMMU 가 IOVA→PA │
   │     │                 │                          │   ▼ ⑧ 1500 byte read    │
   │     │                 │                          │   ▼ ⑨ TX to physical NIC│
   │     │                 │                          │   ▼ ⑩ DMA done callback │
   │     │                 │                          │   ▼ ⑪ used_ring 에 기록 │
   │     │                 │                          │   ▼ ⑫ vmI 에 IRQ 주입   │
   │     │                 │ ◀━━━━━━━━━━━━━━━━━━━━━━━━━│   (eventfd)            │
   │  ⑬ ISR 가 used_ring  │                          │                         │
   │     polling, buffer free                          │                         │
   │  ⑭ send() return      │                          │                         │
   └───────────────────────┘                          └─────────────────────────┘
```

| Step | 누가 | 무엇을 | 의미 |
|---|---|---|---|
| ①–③ | Guest virtio-net | Descriptor 채우고 avail_ring 갱신 | VM Exit _없음_. 그냥 메모리 write. |
| ④ | Guest | notify register MMIO write | _유일한 VM Exit_. 단 1 회. |
| ⑤ | Host (KVM) | EXIT_REASON 디스패치 → vhost-net eventfd 호출 | exit handler 가 backend 깨움 |
| ⑥ | vhost-net (kernel) | Guest 의 avail_ring 위치 (IPA) 의 desc 읽음 | shared memory 라 host 가 직접 read |
| ⑦ | IOMMU | IOVA (guest IPA) → host PA 변환 | DMA 격리 — 다른 VM 메모리는 못 봄 |
| ⑧ | vhost-net | 1500 byte payload 가져옴 | zero-copy (가능하면) |
| ⑨ | Physical NIC driver | TX descriptor 에 PA 적고 wire 로 송신 | bare metal 과 동일 |
| ⑩–⑪ | NIC IRQ → vhost-net | DMA done → used_ring 에 desc_idx 기록 | guest 가 다음에 polling 으로 회수 |
| ⑫ | vhost / KVM | guest 에 IRQ 주입 (eventfd) | guest 의 ISR 깨움 |
| ⑬–⑭ | Guest | used_ring polling → buffer free → return | 1 cycle 종료 |

```c
/* Step ②–④ 의 실제 Linux virtio-net 코드 (단순화) */
static netdev_tx_t virtnet_xmit(struct sk_buff *skb, struct net_device *dev) {
    struct virtnet_info *vi = netdev_priv(dev);
    struct send_queue *sq = &vi->sq[skb_get_queue_mapping(skb)];
    struct scatterlist sg[1];

    sg_init_one(sg, skb->data, skb->len);
    /* ② descriptor table 에 add */
    virtqueue_add_outbuf(sq->vq, sg, 1, skb, GFP_ATOMIC);
    /* ④ kick — VM Exit 발생 (단 1 회) */
    if (virtqueue_kick_prepare(sq->vq))
        virtqueue_notify(sq->vq);
    return NETDEV_TX_OK;
}
```

!!! note "여기서 잡아야 할 두 가지"
    **(1) 패킷 N 개를 _묶어_ ring 에 넣고 kick 1 회 하면 VM Exit 1 회로 N 패킷 처리** — Emulation 의 "패킷당 N 회 exit" 와의 결정적 차이. 이게 VirtIO 가 빠른 이유.<br>
    **(2) IOMMU 가 ⑦ 에서 IOVA → PA 를 _묵묵히_ 처리** — vhost 는 IOVA 만 쓰면 됨. 격리는 IOMMU 가 보장. 이게 SR-IOV / Passthrough 에서도 같은 메커니즘.

---

## 4. 일반화 — 3 가지 I/O 가상화 모델

### 4.1 한 장 비교

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
| **Emulation** | 낮음 | 불필요 | 가능 | 불필요 | 개발 / 테스트, 레거시 |
| **VirtIO** | 중간 | 드라이버 | 가능 | 불필요 | 범용 클라우드 |
| **SR-IOV** | 높음 | 드라이버 | VF 단위 | SR-IOV NIC | 고성능 네트워크 |
| **Pass-through** | 최고 | 불필요 | 불가 | IOMMU | GPU, NVMe, 전용 HW |

### 4.2 왜 I/O 가상화는 _어려운가_

CPU / 메모리와 달리 I/O 디바이스는 본질적으로 **공유가 어렵습니다**.

```
CPU:  시분할 (time-sharing) 로 여러 VM 에 할당 가능
메모리: 주소 변환 (paging) 으로 VM 별 공간 분리 가능
I/O:  디바이스마다 인터페이스가 다르고,
      상태를 갖고 있으며 (stateful),
      DMA 로 메모리에 직접 접근함

  → 범용적인 HW 메커니즘으로 해결하기 어려움
  → 디바이스별 에뮬레이션 or 특수 HW 지원 필요
```

#### DMA 의 보안 문제

```
                    ┌──────────┐
  VM0 의 메모리      │ NIC      │
  0x1000~0x2000 ◄───┤ (DMA)   │ DMA 가 VM0 의 메모리에 직접 쓰기
                    │          │
  VM1 의 메모리      │          │ 만약 NIC 가 잘못된 주소에 쓰면?
  0x2000~0x3000 ◄───┤          │ → VM1 의 메모리가 오염됨!
                    └──────────┘

해결: IOMMU 가 DMA 주소도 변환 / 검증
      디바이스가 허가된 메모리 영역만 접근 가능하도록 보장
```

---

## 5. 디테일 — Emulation, VirtIO, Passthrough, IOMMU

### 5.1 방법 1: 디바이스 에뮬레이션 (Full Emulation)

#### 개념

Hypervisor 가 물리 디바이스를 **SW 로 완전히 모방**.

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
│  │가상 NIC 0│  │가상 NIC 1│    │  SW 로 디바이스 동작 에뮬레이션
│  └────┬─────┘  └────┬─────┘    │
│       └──────┬──────┘          │
│              ▼                  │
│         물리 NIC 드라이버       │
└──────────────┬──────────────────┘
               ▼
          물리 NIC
```

#### 동작 흐름

1. Guest OS 가 가상 디바이스의 레지스터에 접근 (MMIO write)
2. **VM Exit** 발생 → Hypervisor 가 trap
3. Hypervisor 의 에뮬레이터가 해당 레지스터 접근을 해석
4. 필요 시 물리 디바이스에 실제 I/O 수행
5. 결과를 가상 디바이스 상태에 반영
6. **VM Entry** → Guest OS 재개

#### 대표 구현: QEMU

```
QEMU 가 에뮬레이션하는 디바이스 예시:
  - e1000 (Intel NIC)
  - IDE / AHCI (디스크 컨트롤러)
  - VGA (그래픽)
  - USB, 시리얼 포트, ...

Guest OS 는 실제 e1000 드라이버를 사용
  → 수정 없이 동작 (Full Virtualization)
  → 하지만 매 I/O 마다 VM Exit → 느림
```

#### 성능 분석

```
네트워크 패킷 하나 전송:
  1. Guest: TX descriptor 쓰기 → VM Exit
  2. Hypervisor: descriptor 해석 → 물리 NIC 에 전달
  3. 물리 NIC: 패킷 전송 완료 → 인터럽트
  4. Hypervisor: 인터럽트 수신 → 가상 인터럽트 주입
  5. Guest: 인터럽트 핸들러 실행

패킷당 VM Exit: 최소 2 회 (TX + 인터럽트)
초당 100 만 패킷이면: 200 만 VM Exit/sec → CPU 상당 부분 소모
```

| 장점 | 단점 |
|------|------|
| Guest OS 수정 불필요 | 매 I/O 마다 VM Exit (심각한 오버헤드) |
| 어떤 디바이스든 에뮬레이션 가능 | Hypervisor 에 디바이스별 에뮬레이터 필요 |
| 디바이스 공유 용이 | 실제 HW 성능의 10~30% 수준 |

### 5.2 방법 2: 준가상화 I/O (VirtIO)

#### 개념

Guest OS 에 **가상화에 최적화된 드라이버** 를 설치. 실제 HW 를 흉내내지 않고, 효율적인 추상 인터페이스를 정의.

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

#### VirtIO 아키텍처

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

#### 왜 빠른가?

```
에뮬레이션: 레지스터 접근 하나하나마다 VM Exit
VirtIO:     여러 요청을 Virtqueue 에 모아서 한 번에 알림 (batching)

  Guest:
    1. 여러 패킷을 Descriptor Table 에 등록
    2. Available Ring 업데이트
    3. 단 1 번의 알림 (kick) → VM Exit 1 회

  vs 에뮬레이션:
    1. 패킷마다 TX register 쓰기 → VM Exit
    2. 패킷마다 doorbell → VM Exit
    → 패킷 N 개면 VM Exit N 회 이상
```

| 장점 | 단점 |
|------|------|
| 에뮬레이션 대비 2~10 배 성능 | Guest OS 에 VirtIO 드라이버 필요 |
| VM Exit 최소화 (batching) | 비공개 OS 는 드라이버 지원 필요 |
| 표준화된 인터페이스 | 물리 HW 대비 여전히 오버헤드 |
| 디바이스 공유 가능 | |

### 5.3 방법 3: 디바이스 Pass-through

#### 개념

물리 디바이스를 **특정 VM 에 직접 할당**. Hypervisor 를 bypass.

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

  VM0 은 NIC #0 에 bare metal 처럼 직접 접근
  → Hypervisor 개입 없음
  → I/O 성능 = bare metal 수준
```

#### VFIO (Virtual Function I/O)

Linux 에서 디바이스 pass-through 를 구현하는 프레임워크.

```
┌─────────────────────────────────────────────┐
│                User Space                    │
│  ┌──────────┐                               │
│  │ QEMU/VM  │ ← VFIO API 로 디바이스 접근    │
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
│  │ IOMMU    │ ← DMA 주소 변환 / 격리         │
│  └────┬─────┘                               │
├───────┼─────────────────────────────────────┤
│       ▼                                      │
│   PCIe Device                                │
└─────────────────────────────────────────────┘
```

**IOMMU 의 역할** (= I/O 용 MMU):

- 디바이스의 DMA 주소를 변환 (디바이스 주소 → PA)
- 디바이스가 할당된 VM 의 메모리만 접근하도록 격리
- 없으면 DMA 가 아무 메모리나 접근 가능 → 보안 붕괴

### 5.4 SR-IOV (Single Root I/O Virtualization)

물리 디바이스 하나를 **여러 가상 디바이스로 분할** 하는 PCIe 스펙.

```
┌──────────────────────────────────────┐
│         물리 NIC (SR-IOV 지원)        │
├──────────────────────────────────────┤
│  PF (Physical Function)              │
│  - 디바이스 전체 관리 / 설정           │
│  - Host / Hypervisor 가 소유           │
├──────────────────────────────────────┤
│  VF0    │  VF1    │  VF2    │ ...   │
│  (경량) │  (경량) │  (경량) │       │
│  VM0 에  │  VM1 에  │  VM2 에  │       │
│  할당   │  할당   │  할당   │       │
└──────────────────────────────────────┘

각 VF 는:
  - 독립된 PCIe Function (BAR, MSI-X 등)
  - 자체 TX/RX 큐
  - 독립 DMA 엔진
  → VM 에 직접 할당 가능 (pass-through)
  → Hypervisor 개입 없이 I/O 수행
```

#### SR-IOV vs 일반 Pass-through

| 항목 | 일반 Pass-through | SR-IOV |
|------|-------------------|--------|
| 물리 디바이스 | 1 개 → 1 VM | 1 개 → N VM (VF 분할) |
| 디바이스 공유 | 불가 | 가능 (VF 단위) |
| HW 지원 | IOMMU 만 | IOMMU + SR-IOV NIC |
| 성능 | Bare metal | Bare metal 에 근접 |
| 비용 | 디바이스 수 = VM 수 | 1 개 디바이스로 다수 VM 지원 |

### 5.5 DPDK (Data Plane Development Kit)

User-space 에서 **커널을 완전히 bypass** 하여 패킷을 처리.

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
DPDK: 모든 것을 user-space 에서 처리 (polling 기반)
```

#### DPDK 가 빠른 이유

| 기존 커널 경유 | DPDK |
|--------------|------|
| 시스템 콜 오버헤드 | User-space 에서 직접 디바이스 접근 |
| 인터럽트 기반 (Context switch) | **Polling 기반** (busy-wait, CPU 전용 할당) |
| 커널 ↔ 유저 간 데이터 복사 | **Zero-copy** (공유 메모리) |
| 범용 TCP/IP 스택 | 최적화된 패킷 처리 라이브러리 |

**사용 사례**: 고성능 네트워킹 — NFV, 패킷 브로커, 방화벽, 로드밸런서.

### 5.6 면접 단골 Q&A

**Q: VirtIO 가 디바이스 에뮬레이션보다 빠른 이유는?**

> "에뮬레이션은 Guest OS 가 가상 디바이스 레지스터에 접근할 때마다 VM Exit 이 발생한다. 패킷 하나에 TX descriptor, doorbell 등 여러 MMIO 접근이 필요하고 각각 VM Exit 을 유발한다. VirtIO 는 Virtqueue 공유 메모리 링 버퍼를 사용하여, Guest 가 여러 요청을 Descriptor Table 에 등록한 후 단 1 번의 kick 으로 Hypervisor 에 통보한다. 결과적으로 에뮬레이션은 I/O 당 VM Exit 이 선형 증가하지만, VirtIO 는 batch 크기에 무관하게 거의 일정. 초당 수백만 I/O 에서 차이가 극대화된다."

**Q: IOMMU 없이 디바이스 pass-through 를 하면 어떤 보안 문제가 생기는가?**

> "IOMMU 없이는 DMA 엔진이 물리 메모리 전체에 접근 가능하다. 공격 시나리오: VM0 에 할당된 NIC 의 DMA descriptor 에 VM1 의 물리 메모리 주소를 설정하면, VM1 의 데이터 (암호키, 인증정보) 유출 또는 코드 변조가 가능하다. 더 심각하게는 Hypervisor 메모리를 DMA 대상으로 지정하여 전체 시스템 장악이 가능하다. IOMMU 는 디바이스별 주소 변환 테이블로 할당된 VM 의 메모리 범위만 접근 허용하며, HW 레벨 격리이므로 SW 우회 불가다."

**Q: SR-IOV 의 PF/VF 차이와 일반 pass-through 대비 장점은?**

> "PF (Physical Function) 는 물리 디바이스의 완전한 PCIe Function 으로 초기화, VF 생성 / 삭제를 담당하며 Hypervisor 가 관리한다. VF (Virtual Function) 는 PF 에서 파생된 경량 PCIe Function 으로, 자체 BAR, MSI-X, TX/RX 큐를 갖지만 관리 기능은 없고 데이터 경로만 제공한다. 확장성: 일반 pass-through 는 NIC 1 개 = VM 1 개이지만, SR-IOV 는 NIC 1 개에서 VF 128 개 생성 가능. 각 VF 가 HW 독립 데이터 경로를 가지므로 bare metal 근접 성능을 유지하면서 128 개 VM 을 지원한다."

---

## 6. 흔한 오해 와 DV 디버그 체크리스트

### 흔한 오해

!!! danger "❓ 오해 1 — 'Passthrough 가 항상 빠르다'"
    **실제**: Passthrough 는 throughput ↑, latency ↓ 이지만 live migration 불가, IOMMU 필수, density ↓. trade-off 정확히 평가 필요.<br>
    **왜 헷갈리는가**: "direct = 빠름" 의 직관. 실제로는 multi-axis trade-off.

!!! danger "❓ 오해 2 — 'VirtIO 드라이버만 깔면 자동으로 빠르다'"
    **실제**: Host 측 vhost backend (vhost-net, vhost-blk) 가 활성화되지 않으면 여전히 QEMU user-space 를 경유하는 full emulation 경로. Guest 측 driver _and_ host 측 backend 모두 필요.<br>
    **왜 헷갈리는가**: "drivers installed → fast" 단순 매핑.

!!! danger "❓ 오해 3 — 'SR-IOV 가 있으면 IOMMU 가 불필요하다'"
    **실제**: SR-IOV 의 VF 도 DMA 를 함. IOMMU 가 없으면 VF 가 다른 VM / host 메모리 침해 가능. SR-IOV + IOMMU 가 항상 한 쌍.<br>
    **왜 헷갈리는가**: "VF 가 격리된 PCIe Function" 이라는 단어의 단순화.

!!! danger "❓ 오해 4 — 'virtio queue 가 가득 차면 backend 가 알려준다'"
    **실제**: vring 의 avail/used index 가 가득 찼을 때 backend (QEMU/vhost) 가 추가 descriptor 를 silent 무시 / notification throttling 하여 guest 는 정상 enqueue 로 오해 → I/O timeout 만 보고 원인 파악 늦어짐.<br>
    **왜 헷갈리는가**: bare metal 의 queue full 은 명확한 status bit 으로 알려짐.

!!! danger "❓ 오해 5 — 'Passthrough 시 live migration 은 그냥 어렵다 정도'"
    **실제**: HW 상태 (NIC TX ring index, GPU memory 등) 가 destination 에 그대로 옮겨가야 하는데 vendor 별로 dirty tracking / state extract 가 다르거나 미지원. Nitro 같은 사내 SmartNIC 모델이 이걸 풀려는 시도.<br>
    **왜 헷갈리는가**: VM 마이그레이션 = "메모리만 복사" 라는 단순화.

### DV 디버그 체크리스트 (I/O 가상화 brings up)

| 증상 | 1차 의심 | 어디 보나 |
|---|---|---|
| Guest 가 e1000 보는데 패킷 안 나감 | QEMU 의 NIC backend 미연결 | QEMU CLI `-netdev` 인자, host bridge / tap 설정 |
| VirtIO 설치 후에도 throughput 그대로 | host 측 vhost-net 미활성 | `lsmod | grep vhost`, `/sys/bus/virtio/drivers/` |
| `virtqueue_kick` 후 응답 없음 | notify 주소 / eventfd 매핑 잘못 | virtio config space 의 `queue_notify_off`, vhost ioeventfd |
| VF 생성은 OK 인데 VM 안에서 안 보임 | host 의 VFIO 바인딩 누락 | `lspci -k`, `dmesg | grep vfio`, qemu CLI `vfio-pci` |
| Passthrough device 가 host kernel panic 유발 | IOMMU off 또는 DMAR fault | `dmesg | grep "DMAR\|IOMMU"`, BIOS VT-d 옵션 |
| SR-IOV VF 가 random VM 메모리 corruption | IOMMU group 의 ACS isolation 깨짐 | `/sys/kernel/iommu_groups/`, ACS override 패치 사용 여부 |
| virtio queue full 인데 silent drop | `VIRTIO_F_EVENT_IDX` notification suppression | vhost stat 의 queue full counter, notify suppression flag |
| Passthrough VM 의 DMA latency spike | IOMMU TLB miss → page walk | IOTLB hit rate, IOMMU hugepage 사용 |
| Live migration 후 NIC link down | VF state extract / restore 미지원 | vendor 의 migration support, virtio-net 으로 fallback |

---

## 7. 핵심 정리 (Key Takeaways)

- **3 가지 모델**: Emulation (호환 ↑, 성능 ↓) / VirtIO (batching 으로 VM Exit 일정) / Passthrough (bare metal 성능, IOMMU 필수).
- **VirtIO = vring + kick**: descriptor table 에 batch 로 채우고 notify 1 회 → VM Exit 1 회로 N 패킷.
- **SR-IOV**: 1 PCIe device → 1 PF + N VF. PF=관리, VF=데이터. NIC 1 개로 128 VM.
- **IOMMU = 가상화의 전제**: DMA 격리 + 주소 변환. 없으면 passthrough 가 보안 붕괴.
- **DPDK = 커널 bypass + polling + zero-copy**. 고성능 NFV / 패킷 브로커의 표준.
- **현대 클라우드 = 혼합** — 관리 NIC 은 VirtIO, 데이터 NIC 은 SR-IOV / Passthrough.

!!! warning "실무 주의점"
    - **virtio queue full silent drop** — `VIRTIO_F_EVENT_IDX` 와 backend 의 notify suppression 동작을 항상 검증.
    - **IOMMU group 의 ACS** 가 깨져 있으면 같은 group 의 모든 device 가 한 VM 에 묶여야 함 — pass-through 단위가 의도와 달라질 수 있다.
    - **vhost backend 의 user-space fallback** 이 silent — `lsmod | grep vhost` 로 첫 검증.

---

## 다음 모듈

→ [Module 05 — Hypervisor Types](05_hypervisor_types.md): CPU / Memory / I/O 가상화의 building block 은 잡았으니, 이제 _Hypervisor 자체_ 의 분류 — Type 1 / Type 2 / KVM 의 hybrid.

[퀴즈 풀어보기 →](quiz/04_io_virtualization_quiz.md)

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


--8<-- "abbreviations.md"
