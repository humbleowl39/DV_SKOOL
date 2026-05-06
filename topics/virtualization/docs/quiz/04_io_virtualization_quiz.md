# Quiz — Module 04: I/O Virtualization

[← Module 04 본문으로 돌아가기](../04_io_virtualization.md)

---

## Q1. (Remember)

I/O 가상화 3가지 모델은?

??? answer "정답 / 해설"
    1. **Emulation** — Hypervisor가 device 시뮬
    2. **Paravirtualization (virtio)** — Guest driver + hypervisor 공유 ring
    3. **Passthrough (SR-IOV/VFIO)** — Device 직접 VM 할당

## Q2. (Understand)

SR-IOV의 PF와 VF 차이는?

??? answer "정답 / 해설"
    - **PF (Physical Function)**: Full-featured PCIe device. Driver가 모든 기능 사용. Host가 보유.
    - **VF (Virtual Function)**: Lightweight 변형. PF 자원의 일부 (queue, MMIO BAR 등)를 가지고 VM에 할당. 주요 fast-path만 직접 access.
    
    예: SR-IOV NIC → 1 PF (host) + 8 VF (8 VM 각각).

## Q3. (Apply)

다음 시나리오에 적합한 모델은?

| 시나리오 | 적합 모델 |
|----------|----------|
| (a) 100Gbps NIC for HPC VM | ? |
| (b) Legacy DOS VM | ? |
| (c) Generic VM with throughput needs | ? |
| (d) GPU compute (CUDA) | ? |

??? answer "정답 / 해설"
    - (a) **Passthrough (SR-IOV)** — line rate 필요
    - (b) **Emulation** — DOS는 modern driver 없음
    - (c) **virtio** — 호환성 + 성능 균형
    - (d) **Passthrough (VFIO)** — GPU는 보통 1 VM에 전용

## Q4. (Analyze)

Passthrough 환경에서 IOMMU 없으면 어떤 위험이 있는가?

??? answer "정답 / 해설"
    Device가 DMA로 host 메모리 무제한 access 가능. VM에 할당된 device가 compromise되면:
    1. Hypervisor 메모리 read → host secret leak
    2. Hypervisor 메모리 write → host kernel compromise
    3. 다른 VM 메모리 access → cross-tenant attack

    IOMMU가 device의 DMA를 가상 주소로 격리해 위 모두 차단.

## Q5. (Evaluate)

Modern data center에서 모든 device를 passthrough 하지 않는 이유는?

??? answer "정답 / 해설"
    1. **Resource ratio**: SR-IOV VF는 한정 (e.g., 8-128). 수천 VM 호스팅 어려움.
    2. **Live migration**: passthrough device는 migration 어려움 (state in HW).
    3. **격리 trade-off**: passthrough는 IOMMU 의존이라 IOMMU bug = 전체 보안 risk.
    4. **Density**: virtio는 software로 무한 multiplex 가능.

    Hybrid 접근이 최적 — performance-critical만 passthrough.
