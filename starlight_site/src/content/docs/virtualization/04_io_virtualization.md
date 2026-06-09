---
title: "Module 04 — I/O Virtualization"
---

:::tip[학습 목표]
이 모듈을 마치면:

- **Distinguish** Emulation, Paravirtualization (VirtIO), Passthrough (SR-IOV / VFIO) 3 가지 모델을 VM Exit 빈도 / Guest 수정 / 디바이스 공유 관점에서 구분할 수 있다.
- **Apply** SR-IOV 의 PF/VF 분리, IOMMU 의 역할을 적용할 수 있다.
- **Identify** VirtIO 의 vring + queue 메커니즘이 어떻게 batching 으로 VM Exit 을 일정하게 유지하는지 식별한다.
- **Trace** 한 패킷이 VirtIO front-end driver → vring → host vhost backend → wire 까지 흐르는 path 를 추적할 수 있다.
- **Describe** split ring 의 세 영역 (descriptor table / available ring / used ring) 과 네 index (`avail_idx`/`last_avail_idx`/`used_idx`/`last_used_idx`) 가 empty/full 을 어떻게 판정하는지 설명할 수 있다.
- **Differentiate** split ring 과 packed ring 을 cache locality / HW backend 적합성 관점에서 구분하고, PCI transport·feature negotiation·초기화 시퀀스의 역할을 설명할 수 있다.
- **Decide** 시나리오 (개발 / 범용 / 고성능 / 저지연) 에 따른 적합한 I/O 가상화 방식을 결정할 수 있다.
:::
:::note[사전 지식]
- [Module 01-03](../01_virtualization_fundamentals/)
- [MMU 코스의 IOMMU/SMMU](../../mmu/04_iommu_smmu/)
:::
---

## 1. Why care? — 이 모듈이 왜 필요한가

### 1.1 시나리오 — _100 Gbps NIC_ 의 _4 가지_ 가상화 모델

VM 에 100 Gbps **NIC**(Network Interface Card — 네트워크 카드)를 제공해야 한다면, 선택할 수 있는 I/O 가상화 모델에 따라 실제로 달성 가능한 **throughput**(단위 시간당 처리량 — 여기서는 초당 전송 데이터량)이 크게 달라집니다. 세 가지 모델 — **Emulation**(디바이스를 소프트웨어로 통째로 흉내), **VirtIO**(Guest 와 host 가 공유 큐로 통신하는 para-virtual 표준), **Passthrough**(디바이스를 VM 에 직접 통째로 할당), **SR-IOV**(물리 디바이스를 하드웨어가 여러 개로 분할) — 가 핵심입니다.

| 모델 | Throughput | CPU overhead | 구현 | 시나리오 |
|------|----------|------------|------|--------|
| **Emulation** (e.g., e1000) | 1-2 Gbps | 매우 큼 | 모든 register access → VM exit | _legacy_ |
| **VirtIO** | 10-20 Gbps | 중간 | shared ring buffer, batched events | _일반 VM_ |
| **Passthrough** (PCIe assign) | _100 Gbps_ | 작음 | NIC 완전 VM 소유 | _전용 VM, 단 1 VM_ |
| **SR-IOV** | _90+ Gbps_ | 작음 | 1 NIC → N VF → N VM | _128 VM 동시_ |

Emulation 은 기존 OS 드라이버를 그대로 쓸 수 있는 호환성이 최고지만, 레지스터 접근마다 VM Exit 을 유발하여 성능이 가장 낮습니다. VirtIO 는 shared ring buffer 와 batching 으로 VM Exit 횟수를 줄여 호환성과 성능을 균형 있게 제공합니다. Passthrough 는 bare metal 에 가장 가까운 성능을 내지만 NIC 하나를 단 하나의 VM 만 독점합니다. SR-IOV 는 NIC 하나를 여러 VF 로 분할하여 128 개 VM 이 동시에 쓸 수 있지만, NIC 자체가 SR-IOV 를 지원해야 하는 HW 의존성이 있습니다. 대규모 클라우드에서는 SR-IOV 가 사실상 필수입니다.

CPU + Memory 가상화는 _상태_ 의 격리이고, I/O 가상화는 _이벤트 + 데이터 흐름_ 의 격리입니다. 100 Gbps NIC, **NVMe**(고속 SSD 를 PCIe 로 직접 붙이는 스토리지 프로토콜) SSD, GPU 같은 _고대역폭 디바이스_ 의 throughput 은 거의 전적으로 I/O 가상화 모델 선택에서 결정됩니다. 여기서 핵심 비용 단위인 **VM Exit**(Guest 실행이 멈추고 hypervisor 로 제어가 넘어가는 전환 — 수백~수천 cycle)을 얼마나 줄이느냐가 모든 모델의 성능을 가릅니다.

이 모듈을 건너뛰면 — VirtIO 가 왜 빠른지, SR-IOV 가 어떻게 1 NIC 으로 128 VM 을 지원하는지, IOMMU 가 _그냥 보안 기능_ 이 아니라 가상화 자체의 전제 조건이라는 게 — 모두 외워야 하는 사실. 한 패킷의 1 cycle 추적과 VM Exit 산식만 잡으면 나머지는 변형입니다.

:::tip[🤔 잠깐 — _VirtIO_ 의 _ring buffer_ 가 _왜_ 빠른가?]
Emulation 대비 VirtIO 가 10× 빠른 _구체적 이유_?

<details>
<summary>정답</summary>

**Batched events + Memory-mapped sharing**.

- **Emulation**: 매 register write 마다 VM Exit → ~1000 cycle.
- **VirtIO**:
  - Guest 와 host 가 _shared ring buffer_ 메모리 공유.
  - Guest 가 _100 packet_ 의 descriptor 작성 후 _한 번_ doorbell write → 1 VM Exit.
  - Host 가 100 packet 일괄 처리.
  - VM Exit per packet = 0.01.

100× 적은 VM Exit → 비례하는 성능 향상.

그래서 _modern 가상화_ 에서 _VirtIO 또는 vhost-net_ 이 default.

</details>
:::
---

## 2. Intuition — 비유와 한 장 그림

:::tip[💡 한 줄 비유]
**I/O Virtualization** = **공용 프린터 vs 전용 프린터** .<br>
**Emulation** = 비서가 프린터를 대신 써 줌 (모든 인쇄 요청이 비서를 거침). **VirtIO** = 비서와 _공유 트레이_ 로 인쇄물을 한꺼번에 넘김 (batching). **Passthrough** = VM 이 프린터를 _혼자_ 가짐. **SR-IOV** = 한 프린터가 _여러 트레이_ 를 갖고 각 VM 이 자기 트레이로 직접 출력.
:::
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

가장 단순한 시나리오. Guest 안 application 이 `send(fd, buf, 1500)` 한 번. 이 한 패킷이 VirtIO 의 ring 을 어떻게 흐르는지 step-by-step. 미리 깔아둘 용어: **MMIO**(Memory-Mapped I/O — 디바이스 레지스터를 메모리 주소처럼 읽고 써서 제어하는 방식), **doorbell**(Guest 가 "처리할 게 준비됐다"고 backend 를 깨우려 두드리는 notify 레지스터), **IOVA**(I/O Virtual Address — 디바이스가 쓰는 가상 주소로, IOMMU 가 실제 PA 로 변환), **ISR**(Interrupt Service Routine — 인터럽트가 오면 실행되는 처리 루틴).

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

:::note[여기서 잡아야 할 두 가지]
**(1) 패킷 N 개를 _묶어_ ring 에 넣고 kick 1 회 하면 VM Exit 1 회로 N 패킷 처리** — Emulation 의 "패킷당 N 회 exit" 와의 결정적 차이. 이게 VirtIO 가 빠른 이유.<br>
**(2) IOMMU 가 ⑦ 에서 IOVA → PA 를 _묵묵히_ 처리** — vhost 는 IOVA 만 쓰면 됨. 격리는 IOMMU 가 보장. 이게 SR-IOV / Passthrough 에서도 같은 메커니즘.
:::

:::caution[doorbell write 가 _왜_ VM Exit 을 일으키나 — MMIO trap-on-write 의 본질]
④ 의 "notify register MMIO write = VM Exit" 를 사실로만 받아들이면 batching 이 왜 이득인지의 절반을 놓칩니다. 핵심은 그 doorbell 레지스터가 _그냥 메모리가 아니라 trap 으로 설정된 주소_ 라는 점입니다.

descriptor·avail_ring 작성(①~③)은 **guest RAM** 에 대한 평범한 store 이므로 hypervisor 의 EPT/Stage-2 에서 _쓰기 가능한 일반 메모리_ 로 매핑되어 있고, 따라서 VM Exit 이 _일어나지 않습니다_. 반면 doorbell(notify) 레지스터가 위치한 MMIO 주소는 hypervisor 가 EPT/Stage-2 에서 **trap-on-write(쓰기 시 fault)** 속성으로 표시해 둡니다. guest 가 그 주소에 store 하는 순간 HW 가 EPT violation(또는 ARM 의 Stage-2 abort)을 일으켜 hypervisor 로 제어가 넘어오고, 이것이 곧 VM Exit 입니다. 즉 VM Exit 은 "MMIO 라서" 자동으로 생기는 게 아니라, _그 페이지가 trap 으로 표시되어 있어서_ 생깁니다 — backend 가 guest 의 의도를 알아채야 하는 단 한 지점만 trap 으로 만들고, 나머지(데이터 전부)는 trap 없는 공유 메모리로 둔 설계입니다.

여기서 batching 의 정체가 드러납니다. trap 은 _doorbell write 마다_ 한 번씩 발생하므로, 패킷 1 개당 doorbell 1 회면 패킷당 VM Exit 1 회입니다. 패킷 N 개를 ring 에 다 채운 뒤 doorbell 을 _1 회만_ 치면, trap 도 1 회 — N 패킷이 단 한 번의 exit 비용을 나눠 갖습니다. "batching 이 exit 을 줄인다" 는 곧 "trap-on-write 지점을 덜 건드린다" 와 같은 말입니다. emulation 이 느린 근본 이유도 같은 틀로 설명됩니다 — emulated NIC 은 _모든_ 제어 레지스터가 trap-on-write 라서, descriptor 쓰기·doorbell·status 읽기 하나하나가 전부 VM Exit 을 부르기 때문입니다.
:::
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

Guest OS 가 가상 디바이스의 레지스터에 MMIO write 를 시도하면 VM Exit 이 발생하고 Hypervisor 가 trap 합니다. Hypervisor 의 에뮬레이터는 해당 레지스터 접근이 어떤 의미인지 해석한 뒤, 필요하면 물리 디바이스에 실제 I/O 를 수행하고 그 결과를 가상 디바이스 상태에 반영합니다. 그 후 VM Entry 로 Guest OS 가 재개됩니다. 이 과정에서 Guest OS 는 에뮬레이션이 끼어 있다는 사실을 알지 못합니다.

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

### 5.2.1 VirtIO 심화 — Virtqueue 의 내부 구조와 프로토콜

앞의 §3 에서 한 패킷이 ring 을 흐르는 _큰 그림_ 을 봤다면, 여기서는 그 ring 이 메모리 위에서 _실제로_ 어떻게 생겼고, driver 와 device 가 어떤 규칙으로 그것을 공유하는지를 풀어 설명합니다. DV 관점에서 virtio-net HW backend 를 검증하려면 이 자료구조의 byte-level 동작과 index 규칙을 정확히 알아야 합니다. TB 는 여기 기술된 virtqueue 프로토콜을 직접 구동하게 됩니다.

#### 왜 VirtIO 가 _표준_ 이 되었는가

VirtIO 이전에는 hypervisor 마다 (Xen, KVM, VMware) 자기만의 가상 디바이스 드라이버를 따로 출하했습니다. 같은 guest 커널이 KVM 위에서는 KVM 전용 NIC/disk 드라이버를, Xen 위에서는 또 다른 드라이버를 필요로 했기 때문에, "hypervisor × 디바이스 타입 × guest OS" 의 조합마다 드라이버가 폭발적으로 늘어났습니다. VirtIO 는 이 문제를 하나의 _표준 인터페이스_ 로 풀었습니다. guest 의 `virtio-net` 드라이버 하나가 KVM, Xen, QEMU, 그리고 virtio-net 스펙을 구현한 SmartNIC HW 까지 — 밑단 backend 가 무엇이든 — 그대로 동작합니다. "paravirtualized" 라는 말의 의미는, guest 드라이버가 자신이 가상 환경에 있음을 _알고_ host 와 협력한다는 것입니다. e1000 같은 full emulation 처럼 host 가 모든 레지스터 접근을 가짜로 흉내 낼 필요가 없습니다.

#### Split Ring 의 메모리 레이아웃

Split ring (v1.0 부터 필수, v1.2 에서도 지배적) 은 queue 하나당 _세 개_ 의 연속된 메모리 영역으로 구성됩니다. queue 크기 Q 는 반드시 2 의 거듭제곱이어야 합니다 (`queue_size`).

```d2
direction: down

DT: "**Descriptor Table** (Q × 16 byte)\nD[0] D[1] D[2] ... D[Q-1]\n각 entry: addr / len / flags / next\n→ 실제 데이터 버퍼를 가리키는 포인터 배열" {
  style.fill: "#e3f2fd"
}
AV: "**Available Ring** (driver 소유)\nflags / avail_idx / ring[0..Q-1]\nring[i % Q] = head descriptor index\n→ driver 가 '이거 처리해줘' 라고 올리는 곳" {
  style.fill: "#fff3e0"
}
US: "**Used Ring** (device 소유)\nflags / used_idx / {id, len}[0..Q-1]\nid = head desc index, len = 사용 byte 수\n→ device 가 '처리 끝났어' 라고 돌려주는 곳" {
  style.fill: "#e8f5e9"
}
DT -> AV: "driver 가 desc 작성 후\nhead index 를 avail 에 push"
AV -> US: "device 가 처리 후\n결과를 used 에 push"
US -> DT: "driver 가 used 회수 →\ndescriptor 해제 (재사용)"
```

세 영역이 분리된 이유는 _소유권_ 을 명확히 나누기 위해서입니다. Descriptor Table 은 데이터 버퍼의 포인터 배열이고, Available Ring 은 driver → device 방향의 작업 지시함, Used Ring 은 device → driver 방향의 완료 통지함입니다. 한 방향씩만 쓰는 single-writer 규칙 덕분에 lock 없이도 안전하게 공유됩니다.

#### 네 개의 Index — empty/full 판정의 핵심

이 프로토콜을 지배하는 것은 네 개의 index 입니다. 둘은 driver 가, 둘은 device 가 소유하며, 같은 ring 을 양쪽이 서로 다른 index 로 추적합니다.

| Index | 소유자 | 의미 |
|-------|--------|------|
| `avail_idx` | Driver | available ring 에 _다음에 쓸_ 슬롯. driver 가 desc 를 올릴 때마다 ++ |
| `last_avail_idx` | Device | available ring 에서 _다음에 읽을_ 슬롯. ring 에 안 보이는 device 내부 값 |
| `used_idx` | Device | used ring 에 _다음에 쓸_ 슬롯. device 가 완료할 때마다 ++ |
| `last_used_idx` | Driver | used ring 에서 _다음에 읽을_ 슬롯. driver 내부 값 |

핵심 규칙은 **index 가 wrap 하지 않고 단조 증가** 하며, 실제 슬롯은 `idx % Q` 로 계산한다는 것입니다. 이 덕분에 별도의 flag 없이도 ring 의 empty/full 을 판정할 수 있습니다. device 입장에서 처리할 게 남았는지는 `avail_idx != last_avail_idx` 한 줄로 알 수 있고, driver 입장에서 회수할 게 있는지는 `used_idx != last_used_idx` 로 압니다. §6 의 "virtio queue full silent drop" 오해가 바로 이 index 비교를 backend 가 어떻게 다루느냐와 직결됩니다.

#### Descriptor 의 4 필드

Descriptor Table 의 각 entry 는 16 byte 이고 다음 4 필드로 이루어집니다.

| 필드 | 폭 | 설명 |
|------|-----|------|
| `addr` | 64-bit | 버퍼의 **guest-physical address** (이 값을 IOMMU 가 host PA 로 변환 — §3 ⑦) |
| `len` | 32-bit | 버퍼 길이 (byte) |
| `flags` | 16-bit | `NEXT`=1 (chain 계속), `WRITE`=2 (device 가 쓰는 버퍼), `INDIRECT`=4 |
| `next` | 16-bit | `NEXT` 가 set 일 때 다음 descriptor 의 index |

여기서 `WRITE` flag 의 방향이 헷갈리기 쉽습니다. flag 는 _device 관점_ 입니다. virtio-net TX 에서 driver 가 보낼 패킷은 device 가 _읽어야_ 하므로 `WRITE` flag 가 없고 (device-readable), RX 에서 미리 깔아두는 빈 버퍼는 device 가 패킷을 _써넣어야_ 하므로 `WRITE` flag 를 답니다. virtio-net 의 TX descriptor chain 은 `[0] virtio_net_hdr (12 byte) + NEXT` → `[1] packet payload` 의 두 entry 로, RX 는 둘 다 `WRITE` flag 를 단 채 미리 게시됩니다. virtio-blk 는 `[0] 요청 헤더(READ/WRITE, sector) → [1] 데이터 버퍼 → [2] status byte(1 byte, WRITE)` 의 세 entry 한 chain 이 한 I/O 요청입니다.

#### Memory Barrier — weak-memory 아키텍처의 함정

§3 의 step ②–④ (descriptor 작성 → avail_ring 갱신 → kick) 사이에는 반드시 memory barrier 가 들어가야 합니다. ARM, RISC-V 같은 weak-memory 아키텍처에서는 CPU 가 store 순서를 재배열할 수 있어, barrier 가 없으면 device 가 `avail_idx` 증가를 먼저 관측하고도 descriptor 내용은 아직 옛 값인 상태를 읽을 수 있습니다. driver 는 (1) descriptor 작성 후 wmb, (2) avail_idx 증가 후 wmb, (3) 그 다음 doorbell kick 의 순서를 지켜야 합니다. device 측도 used_ring 작성과 used_idx 증가 사이에 wmb 를 넣습니다. 이 barrier 누락은 x86 (strong memory model) 에서는 _우연히 동작_ 하다가 ARM SmartNIC 으로 옮기면 깨지는 전형적 버그입니다.

#### Packed Ring — HW backend 를 위한 단일 ring

VirtIO 1.1 은 split ring 의 대안으로 **packed ring** 을 도입했습니다. 세 영역을 따로 두는 대신, descriptor 하나의 배열만 쓰고 available/used 상태를 각 entry 의 `flags` 안에 (`AVAIL`/`USED` 비트를 wrap counter 로 토글) 인라인으로 담습니다.

```d2
direction: right

SPLIT: "**Split Ring** (v1.0)" {
  D: "Descriptor Table"
  A: "Available Ring"
  U: "Used Ring"
  D -> A: "3개 영역\n별도 cache line"
  A -> U
}
PACKED: "**Packed Ring** (v1.1+)" {
  P: "단일 Descriptor Array\nflags 안에 AVAIL/USED 상태\n(wrap counter 로 toggle)"
}
SPLIT -> PACKED: "DMA 엔진이\n1개 연속 ring 만 읽음\n→ cache locality ↑"
```

split ring 은 한 요청을 처리하는 데 세 개의 분리된 메모리 구조를 건드려 cache pressure 가 큽니다. packed ring 은 DMA 엔진이 단일 연속 ring 만 읽으면 되므로 cache locality 가 좋아 **HW 구현 (SmartNIC) 에 특히 유리** 합니다. virtio-net HW backend 를 검증할 때 split/packed 양쪽 모드를 모두 커버해야 하는 이유가 여기에 있습니다.

#### PCI Transport — virtqueue 는 어떻게 _발견_ 되는가

VirtIO 는 transport 에 독립적입니다. 같은 virtqueue 구조가 PCI, MMIO (임베디드), Channel I/O (IBM s390) 위에서 동일하게 동작합니다. VM/SmartNIC 에서 가장 흔한 **PCI transport** 에서는 device 가 Vendor ID `0x1AF4` 로 식별되고, BAR 에 매핑된 다섯 개의 capability 구조로 자신을 노출합니다.

| Capability | 역할 |
|------------|------|
| `VIRTIO_PCI_CAP_COMMON_CFG` | feature bits, queue 선택, `device_status` 레지스터 |
| `VIRTIO_PCI_CAP_NOTIFY_CFG` | 큐별 doorbell 레지스터 (§3 의 ④ kick 이 쓰는 곳) |
| `VIRTIO_PCI_CAP_ISR_CFG` | legacy 인터럽트 상태 |
| `VIRTIO_PCI_CAP_DEVICE_CFG` | device 고유 config (virtio-net 의 MAC 주소 등) |
| `VIRTIO_PCI_CAP_PCI_CFG` | PCI config space 경유의 대체 레지스터 접근 |

§6 디버그 체크리스트의 "`virtqueue_kick` 후 응답 없음 → notify 주소 매핑" 항목이 바로 `VIRTIO_PCI_CAP_NOTIFY_CFG` 의 `queue_notify_off` 계산을 가리킵니다.

#### Feature Negotiation — 하위 호환의 메커니즘

초기화 중 driver 와 device 는 **feature bitmap** 을 협상합니다. (1) device 가 `device_feature_select`/`device_feature` 로 지원 feature 를 게시하고, (2) driver 가 읽어서 자기가 지원하는 집합으로 마스킹한 뒤 `driver_feature` 에 쓰고, (3) driver 가 `device_status` 에 `FEATURES_OK` 를 set 하면 device 가 여전히 set 인지 확인합니다. 만약 device 가 `FEATURES_OK` 를 clear 하면 협상된 집합이 지원 불가라는 뜻이므로 driver 는 중단해야 합니다. 이 메커니즘 덕분에 v1.2 device 가 v1.0 driver 와도 동작합니다 — v1.0 feature 만 협상하면 되기 때문입니다. §4.2 에서 다룬 `VIRTIO_F_EVENT_IDX`, packed ring 사용 여부, virtio-net 의 multiqueue(`VIRTIO_NET_F_MQ`) 도 모두 이 비트맵으로 켜집니다.

#### 초기화 시퀀스 — device_status 의 단계 진행

driver 는 `device_status` 레지스터에 정해진 순서대로 비트를 써넣어야 합니다. 이 순서를 어기면 device 가 I/O 를 받지 않습니다.

```d2
direction: right

R: "RESET (0)"
A: "ACKNOWLEDGE\n(driver 가 device 인식)"
D: "DRIVER\n(driver 가 구동법 앎)"
F: "(feature negotiation)"
FO: "FEATURES_OK\n(협상 집합 수락)"
DO: "DRIVER_OK\n(device live — I/O 시작 가능)"
R -> A -> D -> F -> FO -> DO
FO -> FAIL: "device 가 clear 하면" { style.stroke-dash: 4 }
FAIL: "FAILED → RESET 재시작" { style.fill: "#ffcdd2" }
```

`DRIVER_OK` 가 set 되기 _전_ 에 virtqueue 에 I/O 를 올리면 device 가 무시합니다. 검증 시 "init 직후 첫 패킷이 사라진다" 류의 증상은 이 시퀀스의 step 누락 (특히 `FEATURES_OK` 와 `DRIVER_OK` 사이) 을 먼저 의심해야 합니다.

#### VirtIO 의 trade-off — 공짜가 아니다

VirtIO 의 이점은 명확합니다. 하나의 통합 드라이버가 모든 hypervisor·SmartNIC·시뮬레이터에서 동작하고, 현대 `vhost-net`/`vhost-user` 에서는 버퍼를 guest-physical address 로 공유해 host 에서 데이터 복사가 없는 zero-copy I/O 가 가능하며, `AVAIL_NO_INTERRUPT`/`USED_NO_NOTIFY` flag 로 driver 와 device 가 알림 빈도를 독립적으로 조절할 수 있습니다. 그러나 대가도 있습니다. driver 와 device 가 _반드시_ 메모리 공간을 공유해야 하고 (VM 은 guest RAM, HW 디바이스는 host-mapped BAR 또는 peer DMA), 앞서 본 memory barrier 오버헤드가 weak-memory 아키텍처에서 발생하며, split ring 은 큐당 세 영역으로 cache pressure 가 큽니다 (이 마지막 항목이 packed ring 도입의 동기).

| 이점 | 대가 |
|------|------|
| 통합 드라이버 (hypervisor/HW/sim 무관) | driver↔device 메모리 공유 필수 |
| zero-copy (vhost-net/vhost-user) | weak-memory 에서 barrier 오버헤드 |
| 알림 빈도 독립 조절 (coalescing) | split ring 의 세 영역 cache pressure (→ packed ring) |

:::note[vhost 가 _왜_ 빠른가 — "driver 만 깔면 안 빠른" 의 근본]
§6 오해 2 가 "VirtIO 드라이버만 깔면 자동으로 빠른 게 아니다" 라고 했는데, 그 _이유_ 가 backend 가 어디서 도느냐에 있습니다.

기본 QEMU virtio backend 는 **user-space** 에서 돕니다. guest 가 doorbell 을 쳐서 VM Exit 이 나면, KVM(kernel) 이 그것을 받아 _다시 user-space 의 QEMU 프로세스로_ 넘기고, QEMU 가 ring 을 읽어 실제 패킷을 host network stack 으로 보냅니다. 이 경로에는 (1) kernel→user-space 로 나가는 context switch, (2) 다시 패킷을 보내려 user→kernel 로 들어오는 syscall, (3) 경우에 따라 데이터 복사가 끼어듭니다 — 패킷마다 이 왕복이 반복되면 batching 으로 줄인 VM Exit 이득을 user-space 왕복이 도로 까먹습니다.

**vhost-net 은 이 backend 를 _kernel 안_ 으로 옮긴 것** 입니다. doorbell 이 깨우는 대상이 user-space QEMU 가 아니라 host kernel 의 vhost worker thread 이고, 이 thread 가 guest 의 ring 을 _직접_ 읽어 host network stack(역시 kernel)으로 곧장 넘깁니다. 즉 kernel↔user-space 왕복과 그 데이터 복사가 통째로 사라집니다(zero-copy 까지 가능). "driver 만 깔면 안 빠르다" 는 바로 이것입니다 — guest 의 virtio 드라이버는 똑같아도, host backend 가 user-space QEMU 면 왕복 비용이 남고 kernel vhost 면 사라지므로, _양 끝(guest driver + host backend)이 모두 fast path 일 때만_ 빨라집니다. (한 단계 더: `vhost-user` 는 backend 를 DPDK 같은 전용 user-space 프로세스에 두고 공유 메모리로 직접 연결해, kernel 도 거치지 않는 또 다른 fast path 입니다.)
:::

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
  - 독립된 PCIe Function (BAR=Base Address Register, 디바이스 레지스터가 매핑되는 주소 창; MSI-X 등)
  - 자체 TX/RX 큐
  - 독립 DMA 엔진
  → VM 에 직접 할당 가능 (pass-through)
  → Hypervisor 개입 없이 I/O 수행
```

:::note[MSI/MSI-X 가 "메모리 write 형태의 인터럽트" 라는 점 — 왜 IOMMU 의 interrupt remapping 이 필요한가]
위에서 각 VF 가 "자체 MSI-X" 를 갖는다고 했는데, MSI/MSI-X 가 _물리적으로 무엇인지_ 를 알면 왜 인터럽트에도 IOMMU 가 끼어드는지가 보입니다.

옛 방식(line-based IRQ)은 별도의 인터럽트 핀을 흔드는 것이었지만, **MSI(Message Signaled Interrupt)는 디바이스가 약속된 특정 주소에 약속된 값을 _memory write_ 하는 것** 이 곧 인터럽트입니다 — 즉 인터럽트가 DMA 와 똑같은 "주소로의 쓰기" 트랜잭션입니다. 이것이 passthrough/SR-IOV 에 직접적인 보안 문제를 만듭니다. VF 가 인터럽트를 "메모리 write" 로 만들 수 있다면, _어느 주소로_ 쓰느냐에 따라 다른 vCPU·다른 VM 을 겨냥한 인터럽트를 위조할 수 있기 때문입니다. 데이터 DMA 를 IOMMU 가 막아도, 인터럽트 write 를 막지 않으면 격리에 구멍이 남습니다.

그래서 IOMMU 는 데이터 변환과 별개로 **interrupt remapping** 을 합니다 — 디바이스가 보낸 인터럽트 메시지를 그대로 통과시키지 않고, _remapping table_ 을 거쳐 "이 디바이스가 보낼 수 있는 정당한 인터럽트인가, 어느 vCPU 로 가야 하는가" 를 다시 결정합니다. 디바이스가 주소를 위조해도 remapping table 이 그 디바이스에 허용된 entry 로만 라우팅하므로 cross-VM 인터럽트 주입이 차단됩니다. 이것은 [mmu 코스 §5.8 의 IOMMU 기능](../../mmu/04_iommu_smmu/) 과 같은 자료구조 계층(디바이스 식별 → table lookup)을 인터럽트에 적용한 것입니다 — 즉 IOMMU 는 "디바이스의 _데이터_ 접근" 과 "디바이스의 _인터럽트_" 를 같은 원리로 둘 다 검증합니다.
:::

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

:::danger[❓ 오해 1 — 'Passthrough 가 항상 빠르다']
**실제**: Passthrough 는 throughput ↑, latency ↓ 이지만 live migration 불가, IOMMU 필수, density ↓. trade-off 정확히 평가 필요.<br>
**왜 헷갈리는가**: "direct = 빠름" 의 직관. 실제로는 multi-axis trade-off.
:::
:::danger[❓ 오해 2 — 'VirtIO 드라이버만 깔면 자동으로 빠르다']
**실제**: Host 측 vhost backend (vhost-net, vhost-blk) 가 활성화되지 않으면 여전히 QEMU user-space 를 경유하는 full emulation 경로. Guest 측 driver _and_ host 측 backend 모두 필요.<br>
**왜 헷갈리는가**: "drivers installed → fast" 단순 매핑.
:::
:::danger[❓ 오해 3 — 'SR-IOV 가 있으면 IOMMU 가 불필요하다']
**실제**: SR-IOV 의 VF 도 DMA 를 함. IOMMU 가 없으면 VF 가 다른 VM / host 메모리 침해 가능. SR-IOV + IOMMU 가 항상 한 쌍.<br>
**왜 헷갈리는가**: "VF 가 격리된 PCIe Function" 이라는 단어의 단순화.
:::
:::danger[❓ 오해 4 — 'virtio queue 가 가득 차면 backend 가 알려준다']
**실제**: vring 의 avail/used index 가 가득 찼을 때 backend (QEMU/vhost) 가 추가 descriptor 를 silent 무시 / notification throttling 하여 guest 는 정상 enqueue 로 오해 → I/O timeout 만 보고 원인 파악 늦어짐.<br>
**왜 헷갈리는가**: bare metal 의 queue full 은 명확한 status bit 으로 알려짐.
:::
:::danger[❓ 오해 5 — 'Passthrough 시 live migration 은 그냥 어렵다 정도']
**실제**: HW 상태 (NIC TX ring index, GPU memory 등) 가 destination 에 그대로 옮겨가야 하는데 vendor 별로 dirty tracking / state extract 가 다르거나 미지원. Nitro 같은 사내 SmartNIC 모델이 이걸 풀려는 시도.<br>
**왜 헷갈리는가**: VM 마이그레이션 = "메모리만 복사" 라는 단순화.
:::
### DV 디버그 체크리스트 (I/O 가상화 brings up)

| 증상 | 1차 의심 | 어디 보나 |
|---|---|---|
| Guest 가 e1000 보는데 패킷 안 나감 | QEMU 의 NIC backend 미연결 | QEMU CLI `-netdev` 인자, host bridge / tap 설정 |
| VirtIO 설치 후에도 throughput 그대로 | host 측 vhost-net 미활성 | `lsmod | grep vhost`, `/sys/bus/virtio/drivers/` |
| `virtqueue_kick` 후 응답 없음 | notify 주소 / eventfd 매핑 잘못 | virtio config space 의 `queue_notify_off`, vhost ioeventfd |
| VF 생성은 OK 인데 VM 안에서 안 보임 | host 의 VFIO 바인딩 누락 | `lspci -k`, `dmesg | grep vfio`, qemu CLI `vfio-pci` |
| Passthrough device 가 host kernel panic 유발 | IOMMU off 또는 DMAR fault | `dmesg | grep "DMAR\|IOMMU"`, BIOS VT-d 옵션 |
| SR-IOV VF 가 random VM 메모리 corruption | IOMMU group 의 ACS(Access Control Services — 같은 PCIe 스위치 아래 디바이스 간 직접 통신을 막아 격리를 보장하는 기능) isolation 깨짐 | `/sys/kernel/iommu_groups/`, ACS override 패치 사용 여부 |
| virtio queue full 인데 silent drop | `VIRTIO_F_EVENT_IDX` notification suppression | vhost stat 의 queue full counter, notify suppression flag |
| Passthrough VM 의 DMA latency spike | IOMMU TLB miss → page walk | IOTLB hit rate, IOMMU hugepage 사용 |
| Live migration 후 NIC link down | VF state extract / restore 미지원 | vendor 의 migration support, virtio-net 으로 fallback |
| virtio init 직후 첫 패킷이 사라짐 | `device_status` 시퀀스 미완 (FEATURES_OK/DRIVER_OK 누락) | driver 의 device_status write 순서, FEATURES_OK 재확인 여부 |
| ARM SmartNIC 에서만 desc 내용이 옛 값 | driver 의 memory barrier 순서 누락 (x86 에선 우연히 통과) | desc write→wmb→avail_idx++→wmb→kick 순서, weak-memory model |
| HW backend 가 packed ring 모드에서 hang | split/packed feature 협상 불일치 | feature bitmap 의 packed ring 비트, COMMON_CFG 의 negotiated set |

---

## 7. 핵심 정리 (Key Takeaways)

- **3 가지 모델**: Emulation (호환 ↑, 성능 ↓) / VirtIO (batching 으로 VM Exit 일정) / Passthrough (bare metal 성능, IOMMU 필수).
- **VirtIO = vring + kick**: descriptor table 에 batch 로 채우고 notify 1 회 → VM Exit 1 회로 N 패킷.
- **Split ring = 3 영역 + 4 index**: descriptor table(포인터 배열) / available ring(driver→device) / used ring(device→driver), 그리고 `avail_idx`/`last_avail_idx`·`used_idx`/`last_used_idx` 의 `idx % Q` 비교로 empty/full 판정.
- **Packed ring** 은 단일 ring 에 AVAIL/USED 상태를 인라인 → cache locality ↑, HW/SmartNIC backend 에 유리.
- **PCI transport + 초기화 순서**: Vendor ID `0x1AF4`, 5 개 capability (COMMON/NOTIFY/ISR/DEVICE/PCI_CFG), `device_status` 의 RESET→ACK→DRIVER→FEATURES_OK→DRIVER_OK 단계. `DRIVER_OK` 전의 I/O 는 무시됨.
- **Feature negotiation** 으로 하위 호환 (`FEATURES_OK` 확인) — `VIRTIO_F_EVENT_IDX`, MQ, packed ring 모두 이 비트맵으로 협상.
- **SR-IOV**: 1 PCIe device → 1 PF + N VF. PF=관리, VF=데이터. NIC 1 개로 128 VM.
- **IOMMU = 가상화의 전제**: DMA 격리 + 주소 변환. 없으면 passthrough 가 보안 붕괴.
- **DPDK = 커널 bypass + polling + zero-copy**. 고성능 NFV / 패킷 브로커의 표준.
- **현대 클라우드 = 혼합** — 관리 NIC 은 VirtIO, 데이터 NIC 은 SR-IOV / Passthrough.

:::caution[실무 주의점]
- **virtio queue full silent drop** — `VIRTIO_F_EVENT_IDX` 와 backend 의 notify suppression 동작을 항상 검증.
- **IOMMU group 의 ACS** 가 깨져 있으면 같은 group 의 모든 device 가 한 VM 에 묶여야 함 — pass-through 단위가 의도와 달라질 수 있다.
- **vhost backend 의 user-space fallback** 이 silent — `lsmod | grep vhost` 로 첫 검증.
- **weak-memory barrier 순서** (desc write → wmb → avail_idx++ → wmb → kick) — x86 에서는 우연히 동작하다 ARM SmartNIC 에서 깨진다. virtio HW backend 검증 시 필수 점검.
- **`DRIVER_OK` 전 I/O 는 silent 무시** — 초기화 시퀀스 (RESET→ACK→DRIVER→FEATURES_OK→DRIVER_OK) 의 step 누락이 "첫 패킷 사라짐" 으로 나타난다.
:::
### 7.1 자가 점검

:::tip[🤔 Q1 — Emulation vs VirtIO vs SR-IOV (Bloom: Apply)]
100 Gbps NIC + 8 VM 분할. 어느 방식을 선택?
<details>
<summary>정답</summary>

SR-IOV 가 유일한 해법:
- **Emulation** (E1000 emulated): ~1 Gbps 한계 → 100 Gbps 불가능.
- **VirtIO**: 10–40 Gbps 가능, 단 vhost-net 의 single thread bottleneck → 100 Gbps 미달.
- **SR-IOV**: VF 8 개 생성 → 각 VM 이 HW VF 직접 사용 → 100 Gbps 분할 가능.
- 단점: live migration 어려움 (passthrough → state 캡처 불가), HW 의존 (NIC 가 SR-IOV 지원해야).
- 대안: SR-IOV + virtio fallback (migration 시 일시 전환).

</details>
:::
:::tip[🤔 Q2 — ACS 깨진 IOMMU group (Bloom: Evaluate)]
`lspci` 로 같은 group 에 GPU + NIC. GPU 만 VM 에 주고 싶다. 무엇이 문제?
<details>
<summary>정답</summary>

ACS (Access Control Services) 미보장 → group 단위로만 격리 보장:
- **이유**: PCIe topology 에서 같은 root port 의 device 끼리 peer-to-peer DMA 가능 → 격리 깨짐.
- **결과**: GPU 만 주려면 NIC 도 같이 줘야 (또는 host 가 둘 다 못 씀).
- **우회**: ACS override patch (보안 약화), 또는 다른 root port 로 NIC 이동 (HW 재배치).
- 양산 ROI: 단순히 "passthrough 가능" 으로 끝나지 않고 group topology 가 _허용_ 해야.

</details>
:::
:::tip[🤔 Q3 — virtqueue index 와 silent drop (Bloom: Analyze)]
HW virtio-net backend 를 검증하는데, driver 가 패킷을 enqueue 했다고 보고하지만 device 가 처리하지 않는다. split ring 의 어느 index 를 먼저 보겠는가?
<details>
<summary>정답</summary>

`avail_idx` 와 device 내부 `last_avail_idx` 의 관계를 본다:
- device 가 처리할 게 있는지는 `avail_idx != last_avail_idx` 로 판정. 둘이 같으면 device 는 "새 작업 없음" 으로 본다.
- **증상 1 (barrier 누락)**: driver 가 `avail_idx++` 를 했지만 descriptor 내용 write 가 weak-memory 에서 재배열돼 device 가 옛 desc 를 읽음 → driver 의 wmb 순서 (desc write → wmb → avail_idx++ → wmb → kick) 검증.
- **증상 2 (kick 누락/주소 오류)**: `avail_idx` 는 올라갔지만 doorbell (`VIRTIO_PCI_CAP_NOTIFY_CFG` 의 `queue_notify_off`) 이 잘못된 주소로 가 device 가 wake 안 됨.
- **증상 3 (init 미완)**: `DRIVER_OK` 가 set 되기 전 enqueue → device 가 모두 무시.
- DV 체크: `avail_idx`, `last_avail_idx`, `used_idx`, `last_used_idx` 4 개를 매 트랜잭션마다 로그/스코어보드로 추적하면 어느 단계에서 멈췄는지 즉시 드러난다.

</details>
:::
### 7.2 출처

- PCI-SIG *Single Root I/O Virtualization (SR-IOV) Specification*
- OASIS *Virtual I/O Device (VIRTIO) Version 1.2* — §3 (split ring), §5 (packed ring), §4.1 (PCI transport), §3 device init / feature negotiation
- Intel *VT-d* + ACS — DMA remapping + isolation

---

## 다음 모듈

→ [Module 05 — Hypervisor Types](../05_hypervisor_types/): CPU / Memory / I/O 가상화의 building block 은 잡았으니, 이제 _Hypervisor 자체_ 의 분류 — Type 1 / Type 2 / KVM 의 hybrid.

[퀴즈 풀어보기 →](../quiz/04_io_virtualization_quiz/)

