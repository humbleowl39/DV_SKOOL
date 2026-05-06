# MMU 용어집

핵심 용어 ISO 11179 형식 정의.

---

## A — ASID / ATS

### ASID (Address Space Identifier)

**Definition.** Process별 가상 주소 공간을 구분하기 위한 TLB tag로, context switch 시 TLB 전체 flush를 회피하고 cold miss 폭증을 방지.

**Source.** ARMv8 ARM, §D5.

**Related.** VMID, TLB invalidation, context switch.

**Example.** ARMv8: 8 또는 16-bit ASID. Linux는 PID와 매핑.

**See also.** [Module 03 — TLB](03_tlb.md)

### ATS (Address Translation Services)

**Definition.** Device가 IOMMU에 사전 주소 변환을 요청해 변환 결과를 device 측에 캐싱하는 PCIe 표준 메커니즘.

**Source.** PCIe Spec, ATS extension.

**Related.** SVM, PRI, Device TLB.

**See also.** [Module 04 — IOMMU/SMMU](04_iommu_smmu.md)

---

## I — IOMMU / IPA

### IOMMU (Input-Output MMU)

**Definition.** Device의 메모리 access를 가상 주소로 관리하여 device 격리, DMA 보호, 가상화 지원을 제공하는 SoC-level MMU.

**Source.** ARM SMMU Spec, Intel VT-d Spec.

**Related.** SMMU, StreamID, Stage 2.

**Example.** GPU/NIC/DMA의 시스템 메모리 access 격리. 가상화 환경에서 VM 간 메모리 보호.

**See also.** [Module 04](04_iommu_smmu.md)

### IPA (Intermediate Physical Address)

**Definition.** Stage 1 translation의 결과로 OS가 보는 "물리" 주소이지만 실제 PA는 아닌 가상화 환경의 중간 주소.

**Source.** ARMv8 virtualization extension.

**Related.** Stage 1, Stage 2, VMID.

**Flow.** VA → (Stage 1, OS) → IPA → (Stage 2, hypervisor) → PA.

**See also.** [Module 04](04_iommu_smmu.md)

---

## P — Page Table / PTE / Page Walk / PWC

### Page Table

**Definition.** VPN(Virtual Page Number) → PPN(Physical Page Number) 매핑을 저장하는 메모리 내 자료구조로, multi-level 계층 구조로 메모리 효율을 확보.

**Source.** OS / CPU architecture textbooks.

**Related.** PTE, Page Walk, Multi-level.

**See also.** [Module 02 — Page Table Structure](02_page_table_structure.md)

### PTE (Page Table Entry)

**Definition.** 단일 page mapping을 표현하는 entry로 PFN, valid, R/W, U/S, ASID, dirty/access 등의 필드를 포함.

**Source.** ARMv8 ARM, §D4-D5.

**Related.** Page Table, Block Descriptor (Huge page).

**See also.** [Module 02](02_page_table_structure.md)

### Page Walk

**Definition.** TLB miss 시 HW Walk Engine 또는 SW Handler가 page table을 다단계로 traverse해 VA→PA 변환을 수행하는 과정.

**Source.** ARMv8 ARM.

**Related.** TLB Miss, PWC, Walk Engine.

**Cost.** 4-level walk = 4 memory accesses. PWC hit이면 1-2 access로 단축.

**See also.** [Module 02](02_page_table_structure.md), [Module 03](03_tlb.md)

### PWC (Page Walk Cache)

**Definition.** Page walk 중 중간 레벨 PTE를 캐싱하는 소형 하드웨어 캐시로, 인접한 VA의 walk 비용을 40-60% 절감.

**Source.** Modern CPU microarchitecture.

**Related.** Page Walk, TLB hierarchy.

**See also.** [Module 02](02_page_table_structure.md)

---

## S — SMMU / SVM / StreamID / Stage 1/2

### SMMU (System Memory Management Unit)

**Definition.** ARM의 IOMMU 표준으로, SoC 내 모든 device 마스터의 메모리 access를 단일 SMMU가 가상 주소로 관리.

**Source.** ARM SMMU Architecture v3 Spec.

**Related.** IOMMU, StreamID, Stage 1/2.

**See also.** [Module 04](04_iommu_smmu.md)

### SVM (Shared Virtual Memory)

**Definition.** Device가 CPU의 가상 주소 공간을 직접 사용해 pin/map 없이 같은 page table로 동작하는 메커니즘.

**Source.** Heterogeneous System Architecture (HSA), ARM SMMU SVA.

**Related.** ATS, PRI, Device TLB.

**Example.** GPU가 CPU의 malloc 포인터를 그대로 사용 (NUMA 페이지도 자동).

**See also.** [Module 04](04_iommu_smmu.md)

### StreamID

**Definition.** SMMU에서 device 마스터를 고유 식별하는 ID로, StreamID별 translation context를 적용.

**Source.** ARM SMMU Spec.

**Related.** SubstreamID (process within a device), Context Descriptor.

**See also.** [Module 04](04_iommu_smmu.md)

### Stage 1 / Stage 2 Translation

**Definition.** 가상화 환경의 두 단계 변환. Stage 1은 OS가 관리하는 VA→IPA, Stage 2는 hypervisor가 관리하는 IPA→PA.

**Source.** ARMv8 virtualization extension, SMMU Spec.

**Related.** IPA, VMID, Hypervisor.

**See also.** [Module 04](04_iommu_smmu.md)

---

## T — TLB / TLBI

### TLB (Translation Lookaside Buffer)

**Definition.** VA→PA 변환 결과를 캐싱하는 고속 하드웨어 캐시로, MMU 성능의 핵심 컴포넌트.

**Source.** ARMv8 ARM, §D5.

**Related.** ASID/VMID tagging, set-associative, replacement policy.

**Hierarchy.** micro-TLB (4-16 entries) → L1 TLB (수십) → L2 TLB (수천).

**See also.** [Module 03](03_tlb.md)

### TLBI (TLB Invalidate)

**Definition.** Stale TLB entry를 무효화하는 명령어로, page table 변경이나 ASID/VMID 재사용 시 필수.

**Source.** ARMv8 ARM, §D5.

**Related.** Stale TLB entry, TLB shootdown, IPI.

**Variants.** TLBI VAE1 (VA-by), TLBI ASIDE1 (ASID-by), TLBI VMALLE1 (full).

**See also.** [Module 03](03_tlb.md)

---

## V — VMID

### VMID (Virtual Machine Identifier)

**Definition.** VM별 가상 주소 공간을 구분하는 TLB tag로, 가상화 환경에서 ASID와 함께 사용.

**Source.** ARMv8 virtualization extension.

**Related.** ASID, Stage 2, hypervisor.

**See also.** [Module 03](03_tlb.md), [Module 04](04_iommu_smmu.md)

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
