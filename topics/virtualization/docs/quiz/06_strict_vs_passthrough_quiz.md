# Quiz — Module 06: Strict vs Passthrough

[← Module 06 본문으로 돌아가기](../06_strict_vs_passthrough.md)

---

## Q1. (Remember)

Strict와 Passthrough의 핵심 차이를 한 줄로?

??? answer "정답 / 해설"
    - **Strict**: 모든 IO를 **hypervisor가 중재** → 격리 ↑, 성능 ↓
    - **Passthrough**: device를 VM에 **직접 할당** → 성능 ↑, 격리는 IOMMU 책임

## Q2. (Understand)

Passthrough에서 IOMMU의 역할이 결정적인 이유는?

??? answer "정답 / 해설"
    Hypervisor가 IO를 중재 안 하므로 device의 DMA를 누가 격리? IOMMU가 그 책임. 없으면 device → host/다른 VM 메모리 직접 access 가능 → 모든 multi-tenant 보안 무용.

## Q3. (Apply)

Production data center가 hybrid 방식을 채택하는 전형적 시나리오는?

??? answer "정답 / 해설"
    - **Strict (대부분)**: NVMe storage (block emulation), generic NIC (virtio)
    - **Passthrough (일부)**: 100GbE NIC for high-throughput VMs, GPU for ML training, FPGA accelerator
    
    전체 효율 + critical workload 성능 동시 확보.

## Q4. (Analyze)

GPU passthrough의 challenge 3가지는?

??? answer "정답 / 해설"
    1. **Live migration 불가**: GPU 내부 state (memory, queue)를 다른 호스트에 옮길 수 없음 → VM down 시간 길어짐
    2. **IOMMU isolation**: GPU의 모든 DMA가 IOMMU 통과해야 다른 VM 보호
    3. **단일 VM 전용**: 1 GPU = 1 VM (또는 SR-IOV 지원 GPU만 분할). Density 낮음.

## Q5. (Evaluate)

다음 워크로드 중 strict + virtio로 충분한 것은?

- [ ] A. AI training (8 GPU 사용)
- [ ] B. Web server (10K req/s)
- [ ] C. RDMA NIC for HPC
- [ ] D. SR-IOV NIC가 부족한 server에서 일반 VM

??? answer "정답 / 해설"
    **B**. Web server는 throughput보다 connection 수 + latency 변동 작음 → virtio 충분. A/C는 throughput-critical → passthrough. D는 hybrid가 필요 (passthrough 자원 부족 시 virtio fallback).
