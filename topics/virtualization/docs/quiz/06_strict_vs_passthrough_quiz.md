# Quiz — Module 06: Strict vs Passthrough

[← Module 06 본문으로 돌아가기](../06_strict_vs_passthrough.md)

---

## Q1. (Remember)

Strict와 Passthrough의 핵심 차이를 한 줄로?

??? answer "정답 / 해설"
    - **Strict**: 모든 IO를 **hypervisor가 중재** → 격리 ↑, 성능 ↓
    - **Passthrough**: device를 VM에 **직접 할당** → 성능 ↑, 격리는 IOMMU 책임

    이 두 방식의 차이는 "누가 IO를 검사하는가"로 요약됩니다. Strict 방식에서는 모든 IO가 hypervisor를 반드시 통과하므로 hypervisor가 정책 위반이나 악의적 접근을 소프트웨어로 차단할 수 있습니다. Passthrough 방식은 hypervisor가 IO 경로에서 빠지므로 소프트웨어 정책 적용이 불가능하고, 격리를 전적으로 IOMMU 하드웨어에 의존합니다. 따라서 passthrough의 보안 수준은 "IOMMU가 얼마나 신뢰할 수 있는가"에 직결됩니다.

## Q2. (Understand)

Passthrough에서 IOMMU의 역할이 결정적인 이유는?

??? answer "정답 / 해설"
    Hypervisor가 IO를 중재 안 하므로 device의 DMA를 누가 격리? IOMMU가 그 책임. 없으면 device → host/다른 VM 메모리 직접 access 가능 → 모든 multi-tenant 보안 무용.

    Strict 방식에서는 hypervisor가 SW로 모든 IO를 검사하므로 격리가 hypervisor 코드 수준에서 보장됩니다. Passthrough에서는 이 소프트웨어 게이트키퍼가 제거되므로, device의 DMA 접근 범위를 제한하는 역할이 전적으로 IOMMU 하드웨어로 넘어갑니다. IOMMU가 없으면 passthrough된 device는 물리 주소 공간 어디든 DMA를 보낼 수 있으므로, 한 VM의 device 펌웨어 취약점 하나가 다른 모든 VM과 hypervisor를 위협하는 결정적 보안 구멍이 됩니다.

## Q3. (Apply)

Production data center가 hybrid 방식을 채택하는 전형적 시나리오는?

??? answer "정답 / 해설"
    - **Strict (대부분)**: NVMe storage (block emulation), generic NIC (virtio)
    - **Passthrough (일부)**: 100GbE NIC for high-throughput VMs, GPU for ML training, FPGA accelerator
    
    전체 효율 + critical workload 성능 동시 확보.

    현실의 데이터센터가 hybrid를 선택하는 이유는 passthrough 자원이 물리적으로 제한적이기 때문입니다. 대다수 VM은 웹 서빙, DB, 마이크로서비스처럼 네트워크 IO가 수 Gbps 이내이므로 virtio로도 충분합니다. 그러나 ML 학습이나 HPC 클러스터처럼 처리량이 결정적인 소수 워크로드는 소프트웨어 IO 경로의 지연이 전체 실행 시간에 직접 영향을 주기 때문에 passthrough를 선택합니다. 이 분리를 통해 한정된 passthrough 자원을 가장 필요한 곳에 집중하면서 전체 인프라 밀도도 유지합니다.

## Q4. (Analyze)

GPU passthrough의 challenge 3가지는?

??? answer "정답 / 해설"
    1. **Live migration 불가**: GPU 내부 state (memory, queue)를 다른 호스트에 옮길 수 없음 → VM down 시간 길어짐
    2. **IOMMU isolation**: GPU의 모든 DMA가 IOMMU 통과해야 다른 VM 보호
    3. **단일 VM 전용**: 1 GPU = 1 VM (또는 SR-IOV 지원 GPU만 분할). Density 낮음.

    이 세 가지 challenge는 각각 다른 운영 측면에서 문제가 됩니다. Live migration 불가는 물리 호스트 유지보수나 장애 대응 시 GPU를 쓰는 VM을 무중단으로 옮길 수 없게 하므로 가용성이 떨어집니다. IOMMU isolation은 GPU가 학습 데이터나 모델 파라미터를 DMA로 대량 처리하기 때문에 격리 실패 시 다른 VM의 데이터가 노출될 수 있어 멀티테넌트 환경에서 필수입니다. 단일 VM 전용 문제는 GPU 비용이 높은데 한 VM만 사용하면 자원 이용률이 낮아지므로, SR-IOV 지원 GPU나 소프트웨어 기반 vGPU 기술이 대안으로 등장한 배경입니다.

## Q5. (Evaluate)

다음 워크로드 중 strict + virtio로 충분한 것은?

- [ ] A. AI training (8 GPU 사용)
- [ ] B. Web server (10K req/s)
- [ ] C. RDMA NIC for HPC
- [ ] D. SR-IOV NIC가 부족한 server에서 일반 VM

??? answer "정답 / 해설"
    **B**. Web server는 throughput보다 connection 수 + latency 변동 작음 → virtio 충분. A/C는 throughput-critical → passthrough. D는 hybrid가 필요 (passthrough 자원 부족 시 virtio fallback).

    정답이 B인 이유는 초당 10,000 요청의 웹 서버 워크로드가 요구하는 네트워크 처리량이 virtio의 성능 범위 안에 충분히 들어오기 때문입니다. A의 AI 학습은 8개 GPU를 활용하는 만큼 GPU passthrough가 필수이고, C의 RDMA NIC는 커널 바이패스로 극저지연을 실현하는 기술 특성상 소프트웨어 IO 경로를 거칠 수 없어 passthrough가 필요합니다. D는 SR-IOV 자원이 부족한 상황 자체가 passthrough만으로는 해결할 수 없음을 전제하므로 hybrid 접근이 불가피합니다. 결국 B만이 성능 요건과 virtio 능력이 일치하는 유일한 시나리오입니다.
