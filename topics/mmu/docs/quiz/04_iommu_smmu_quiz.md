# Quiz — Module 04: IOMMU / SMMU

[← Module 04 본문으로 돌아가기](../04_iommu_smmu.md)

---

## Q1. (Remember)

가상화 환경에서 Stage 1과 Stage 2 translation은 각각 누가 관리하고 무엇을 변환하는가?

??? answer "정답 / 해설"
    - **Stage 1**: **OS**가 관리, **VA → IPA** 변환 (guest OS 관점에서 "물리" 주소)
    - **Stage 2**: **Hypervisor**가 관리, **IPA → PA** 변환 (실제 하드웨어 주소)

    전체 흐름: VA → (Stage 1, OS) → IPA → (Stage 2, hypervisor) → PA

## Q2. (Understand)

IOMMU 없는 SoC가 보안상 위험한 이유는?

??? answer "정답 / 해설"
    DMA 마스터(GPU/USB/NIC/DMA controller)는 IOMMU 없이는 PA로 시스템 메모리에 직접 access 가능. 단일 device가 compromise되면 (firmware bug, supply chain attack 등):
    - 커널 메모리 read/write 가능 → root escalation
    - 다른 process 메모리 침해 → privacy leak
    - 무한 DMA로 시스템 hang

    IOMMU는 device를 가상 주소 공간에 격리해 위 공격을 차단.

## Q3. (Apply)

같은 SoC에 GPU(StreamID=10)와 NIC(StreamID=20)이 있을 때, 둘이 격리되는 메커니즘을 설명하세요.

??? answer "정답 / 해설"
    SMMU가 StreamID별 별도 **Context Descriptor (CD)**를 보유:
    - StreamID=10 → GPU의 page table base + ASID
    - StreamID=20 → NIC의 page table base + ASID

    GPU가 transaction을 발행하면 SMMU는 StreamID로 CD lookup → GPU page table로 변환. NIC도 동일하게 자기 page table만 사용. 둘은 같은 PA를 가질 수 없음(Stage 2 또는 별도 IPA 영역).

## Q4. (Analyze)

SVM(Shared Virtual Memory)의 동작에 ATS와 PRI가 각각 어떤 역할을 하는가?

??? answer "정답 / 해설"
    - **ATS (Address Translation Services)**: device가 IOMMU에 사전 변환 요청 → device-side TLB(Device TLB)에 PA 캐싱. 이후 transaction은 device가 변환된 PA를 직접 사용 → IOMMU 우회 가능 → 성능 ↑.
    - **PRI (Page Request Interface)**: device가 page fault 발생 시 OS에 협력 요청. 일반 device는 fault 처리 못 하지만 PRI로 OS가 페이지 할당 후 device 재시도 알림. SVM의 demand paging 가능하게 함.

## Q5. (Evaluate)

IOMMU page fault가 CPU page fault와 다르게 비동기로 처리되는 이유는?

??? answer "정답 / 해설"
    - **CPU**: 명령어 실행 중에만 fault 발생 → 명령어 stall + 핸들러 후 재실행. 동기 처리가 자연스러움.
    - **IOMMU**: device가 비동기적으로 transaction 발행. fault 시 device를 stall 시키기 어렵고, fault 처리 중에도 다른 device는 계속 동작해야 함. 따라서:
      1. Event Queue에 fault 기록
      2. Interrupt로 OS에 통지
      3. OS가 페이지 할당 후 device에 retry 알림 (PRI 또는 device-specific 메커니즘)

    동기 처리는 device 디자인 복잡도 + 성능 손실이 너무 큼.
