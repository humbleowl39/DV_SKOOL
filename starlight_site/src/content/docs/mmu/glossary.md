---
title: "MMU 용어집"
---

핵심 용어 ISO 11179 형식 정의.

---

## A — ASID / ATS

### ASID (Address Space Identifier)

**Definition.** Process별 가상 주소 공간을 고유하게 식별하기 위해 TLB entry에 부여되는 하드웨어 태그 값.

**Source.** ARMv8 ARM, §D5.

**Related.** VMID, TLB invalidation, context switch.

**Example.** ARMv8: 8 또는 16-bit ASID. Linux는 PID와 매핑. context switch 시 ASID를 변경하는 것만으로 TLB 전체 flush 없이 이전 프로세스의 entry와 격리된다.

**See also.** [Module 03 — TLB](../03_tlb/)

### ATS (Address Translation Services)

**Definition.** Device가 IOMMU에 사전 주소 변환을 요청해 변환 결과를 device 측에 캐싱하는 PCIe 표준 메커니즘.

**Source.** PCIe Spec, ATS extension.

**Related.** SVM, PRI, Device TLB.

**Example.** GPU가 ATS Translation Request를 IOMMU에 발행하면 IOMMU는 Translation Completion으로 PA를 반환하고, GPU는 이를 Device TLB에 저장해 이후 DMA에서 IOMMU를 우회한다.

**See also.** [Module 04 — IOMMU/SMMU](../04_iommu_smmu/)

---

## A2 — ATC

### ATC (Address Translation Cache)

**Definition.** ATS 를 통해 IOMMU 로부터 받은 IOVA→PA 변환 결과를 device 자체에 저장하는 device-측 translation cache.

**Source.** PCIe ATS Specification.

**Related.** ATS, IOTLB, invalidation.

**Example.** GPU 가 ATS Translation Request 로 받은 PA 를 ATC 에 캐싱한 뒤 AT=Translated DMA 를 발행하면 IOMMU 의 translation stage 를 우회한다. unmap 시 IOMMU 가 `ATC_INV`(Invalidate Request) 를 device 로 보내 ATC entry 를 제거하고 `SYNC` 로 완료를 보장해야 stale-access 가 차단된다.

**See also.** [Module 04 — IOMMU/SMMU](../04_iommu_smmu/)

---

## I — IOMMU / IOTLB / IPA

### IOMMU (Input-Output MMU)

**Definition.** Device의 메모리 access를 가상 주소로 관리하여 device 격리, DMA 보호, 가상화 지원을 제공하는 SoC-level MMU.

**Source.** ARM SMMU Spec, Intel VT-d Spec.

**Related.** SMMU, StreamID, Stage 2.

**Example.** GPU/NIC/DMA의 시스템 메모리 access 격리. 가상화 환경에서 VM 간 메모리 보호.

**See also.** [Module 04](../04_iommu_smmu/)

### IOTLB (I/O Translation Lookaside Buffer)

**Definition.** IOMMU 내부에서 device 의 IOVA→PA 변환 결과를 캐싱하는 고속 cache 로, device·PASID 식별자를 포함한 복합 키로 색인되는 IOMMU 의 hot path.

**Source.** ARM SMMU Spec, Intel VT-d Spec.

**Related.** IOTLB invalidation (`TLBI`), PWC, ATC, StreamID/PASID.

**Example.** (StreamID, ASID, VMID, VPN) 복합 키로 색인되며 entry size 도 4 KB/2 MB/1 GB 로 다양하다. stale IOTLB entry 는 freed page 가 DMA 로 reachable 한 보안 문제이므로 모든 unmap 은 `TLBI` → `SYNC` 짝으로 무효화해야 한다.

**See also.** [Module 04 — IOMMU/SMMU](../04_iommu_smmu/)

### IPA (Intermediate Physical Address)

**Definition.** Stage 1 translation의 결과로 OS가 보는 "물리" 주소이지만 실제 PA는 아닌 가상화 환경의 중간 주소.

**Source.** ARMv8 virtualization extension.

**Related.** Stage 1, Stage 2, VMID.

**Example.** 게스트 OS는 IPA를 자신의 물리 주소로 인식하며 page table을 구성한다. 하이퍼바이저는 Stage 2를 통해 IPA→PA 매핑을 관리하며, 변환 흐름은 VA → (Stage 1, OS) → IPA → (Stage 2, hypervisor) → PA이다.

**See also.** [Module 04](../04_iommu_smmu/)

---

## P — PASID / Page Table / PTE / Page Walk / PWC

### PASID (Process Address Space ID)

**Definition.** 하나의 device 안에서 여러 독립 주소 공간(보통 CPU process 단위)을 구분하기 위해 부여되는 식별자로, PCIe 에서 최대 20 bit 폭을 가진다.

**Source.** PCIe PASID Specification; ARM SMMUv3 (SubstreamID).

**Related.** SVM/SVA, ATS, PRI, Context Descriptor, StreamID.

**Example.** ARM SMMUv3 의 SubstreamID 가 PASID 에 대응하며, PASID 로 device 의 한 context 를 특정 CPU process 의 page table 에 묶으면 accelerator 가 application 과 같은 포인터를 dereference 하는 SVM 이 성립한다. CUDA Unified Memory, OpenCL SVM, oneAPI USM 이 이 위에 선다.

**See also.** [Module 04 — IOMMU/SMMU](../04_iommu_smmu/)

### Page Table

**Definition.** VPN(Virtual Page Number) → PPN(Physical Page Number) 매핑을 저장하는 메모리 내 자료구조로, multi-level 계층 구조로 메모리 효율을 확보.

**Source.** OS / CPU architecture textbooks.

**Related.** PTE, Page Walk, Multi-level.

**See also.** [Module 02 — Page Table Structure](../02_page_table_structure/)

### PTE (Page Table Entry)

**Definition.** 단일 page mapping을 표현하는 entry로 PFN, valid, R/W, U/S, ASID, dirty/access 등의 필드를 포함.

**Source.** ARMv8 ARM, §D4-D5.

**Related.** Page Table, Block Descriptor (Huge page).

**See also.** [Module 02](../02_page_table_structure/)

### Page Walk

**Definition.** TLB miss 시 HW Walk Engine 또는 SW Handler가 page table을 다단계로 traverse해 VA→PA 변환을 수행하는 과정.

**Source.** ARMv8 ARM.

**Related.** TLB Miss, PWC, Walk Engine.

**Example.** 4-level walk(ARMv8 4KB granule) = 최소 4번의 메모리 읽기. 각 읽기가 DRAM에 도달하면 walk 한 번에 수백 cycle이 소요되며, PWC hit이면 1-2 access로 단축된다.

**See also.** [Module 02](../02_page_table_structure/), [Module 03](../03_tlb/)

### PWC (Page Walk Cache)

**Definition.** Page walk 중 중간 레벨 PTE를 캐싱하는 소형 하드웨어 캐시로, 인접한 VA의 walk 비용을 40-60% 절감.

**Source.** Modern CPU microarchitecture.

**Related.** Page Walk, TLB hierarchy.

**Example.** 좁은 VA 범위를 순차 접근하면 L0/L1 PTE가 PWC에 유지되어 walk 시 L2·L3만 메모리에서 읽으면 된다. 반대로 완전 랜덤 VA 접근 패턴에서는 PWC hit rate가 거의 0에 수렴한다.

**See also.** [Module 02](../02_page_table_structure/)

---

## R — Interrupt Remapping

### Interrupt Remapping

**Definition.** IOMMU 가 device 의 MSI/MSI-X 인터럽트 write 를 Interrupt Remapping Table 로 검증·재매핑하여 인가된 vector 만 지정된 CPU 로 전달하는 보안 기능.

**Source.** Intel VT-d Spec, ARM GIC/SMMU integration.

**Related.** MSI/MSI-X, ACS, DMA attack, IOMMU group.

**Example.** MSI 는 결국 device 의 메모리 write 이므로 통제 없이 두면 악성 device 가 임의 vector 를 임의 CPU 에 주입해 권한 상승/DoS 가 가능하다. remapping table 이 이 injection 경로를 닫는다.

**See also.** [Module 04 — IOMMU/SMMU](../04_iommu_smmu/)

---

## S — SMMU / SVM / StreamID / Stage 1/2

### SMMU (System Memory Management Unit)

**Definition.** ARM의 IOMMU 표준으로, SoC 내 모든 device 마스터의 메모리 access를 단일 SMMU가 가상 주소로 관리.

**Source.** ARM SMMU Architecture v3 Spec.

**Related.** IOMMU, StreamID, Stage 1/2.

**See also.** [Module 04](../04_iommu_smmu/)

### SVM (Shared Virtual Memory)

**Definition.** Device가 CPU의 가상 주소 공간을 직접 사용해 pin/map 없이 같은 page table로 동작하는 메커니즘.

**Source.** Heterogeneous System Architecture (HSA), ARM SMMU SVA.

**Related.** ATS, PRI, Device TLB.

**Example.** GPU가 CPU의 malloc 포인터를 그대로 사용 (NUMA 페이지도 자동).

**See also.** [Module 04](../04_iommu_smmu/)

### StreamID

**Definition.** SMMU에서 device 마스터를 고유 식별하는 ID로, StreamID별 translation context를 적용.

**Source.** ARM SMMU Spec.

**Related.** SubstreamID (process within a device), Context Descriptor.

**See also.** [Module 04](../04_iommu_smmu/)

### Stage 1 / Stage 2 Translation

**Definition.** 가상화 환경의 두 단계 변환. Stage 1은 OS가 관리하는 VA→IPA, Stage 2는 hypervisor가 관리하는 IPA→PA.

**Source.** ARMv8 virtualization extension, SMMU Spec.

**Related.** IPA, VMID, Hypervisor.

**See also.** [Module 04](../04_iommu_smmu/)

---

## T — TLB / TLBI

### TLB (Translation Lookaside Buffer)

**Definition.** VA→PA 변환 결과를 캐싱하는 고속 하드웨어 캐시로, MMU 성능의 핵심 컴포넌트.

**Source.** ARMv8 ARM, §D5.

**Related.** ASID/VMID tagging, set-associative, replacement policy.

**Example.** micro-TLB (4-16 entries, 1-cycle 접근) → L1 TLB (수십 entries) → L2 TLB (수천 entries). L1 miss가 L2 hit으로 해결되면 page walk를 회피할 수 있다.

**See also.** [Module 03](../03_tlb/)

### TLBI (TLB Invalidate)

**Definition.** Stale TLB entry를 무효화하는 명령어로, page table 변경이나 ASID/VMID 재사용 시 필수.

**Source.** ARMv8 ARM, §D5.

**Related.** Stale TLB entry, TLB shootdown, IPI.

**Example.** 단일 PTE 변경 시 `TLBI VAE1`으로 해당 VA만 무효화하는 것이 `TLBI VMALLE1`(전체 flush)보다 훨씬 저렴하다. ASID 재사용 시에는 `TLBI ASIDE1`으로 해당 프로세스의 모든 entry를 한 번에 제거한다.

**See also.** [Module 03](../03_tlb/)

---

## V — VMID

### VMID (Virtual Machine Identifier)

**Definition.** VM별 가상 주소 공간을 구분하는 TLB tag로, 가상화 환경에서 ASID와 함께 사용.

**Source.** ARMv8 virtualization extension.

**Related.** ASID, Stage 2, hypervisor.

**See also.** [Module 03](../03_tlb/), [Module 04](../04_iommu_smmu/)

---

## 추가 약어

| 약어 | 풀네임 | 의미 |
|------|--------|------|
| **MMU** | Memory Management Unit | CPU 내장 주소 변환 유닛 |
| **VA** | Virtual Address | 가상 주소 |
| **PA** | Physical Address | 물리 주소 |
| **VPN** | Virtual Page Number | VA의 page 부분 |
| **PPN** | Physical Page Number | PA의 frame 부분 |
| **TTBR** | Translation Table Base Register | Page Table base 주소 레지스터 |
| **TCR** | Translation Control Register | Translation 설정 |
| **MAIR** | Memory Attribute Indirection Register | 메모리 속성 |
| **NS** | Non-Secure | TrustZone non-secure 표시 |
| **PRI** | Page Request Interface | IOMMU의 SVM page fault 협력 |
| **PASID** | Process Address Space ID | device 내 process별 주소 공간 식별 (≤20bit) |
| **ATC** | Address Translation Cache | ATS 의 device-측 translation cache |
| **IOTLB** | I/O TLB | IOMMU 내부 IOVA→PA cache |
| **ACS** | Access Control Services | PCIe P2P 라우팅 통제 (IOMMU group 경계) |
| **TDISP** | TEE Device Interface Security Protocol | confidential computing 의 device 신뢰 확장 |
| **vIOMMU** | virtualized IOMMU | guest 전용 IOMMU (nested translation) |
