# DV_SKOOL 학습자료 용어집 점검 — 종합 리포트

각 토픽 본문에서 등장하는 약어를 추출해 glossary.md 와 비교했습니다.

- **MISSING (HIGH)**: 본문에 등장했지만 glossary 에 없음 → 신규 항목 추가 필요
- **LINKLESS (MED)**: glossary 에 있지만 본문에서 글로서리 링크 부재 → cross-link 삽입 권고
- **ORPHAN (LOW)**: glossary 에 있지만 본문 어디에도 안 나옴 → 사장(死藏) 항목, 검토 권고

- **Priority 점수**: `MISSING*3 + LINKLESS*1` (본문 사용성 영향 가중)


| 토픽 | Glossary | Body 약어 | MISSING (HIGH) | LINKLESS (MED) | ORPHAN (LOW) | Priority |
|---|---|---|---|---|---|---|
| [rdma](per_topic/rdma.md) | 68 | 323 | **271** | 52 | 18 | 865 |
| [amba_protocols](per_topic/amba_protocols.md) | 9 | 151 | **147** | 4 | 5 | 445 |
| [pcie](per_topic/pcie.md) | 43 | 169 | **138** | 31 | 16 | 445 |
| [soc_secure_boot](per_topic/soc_secure_boot.md) | 18 | 137 | **129** | 8 | 11 | 395 |
| [ufs_hci](per_topic/ufs_hci.md) | 10 | 124 | **119** | 5 | 5 | 362 |
| [automotive_cybersecurity](per_topic/automotive_cybersecurity.md) | 20 | 126 | **116** | 10 | 10 | 358 |
| [mmu](per_topic/mmu.md) | 14 | 112 | **101** | 11 | 3 | 314 |
| [virtualization](per_topic/virtualization.md) | 15 | 106 | **100** | 6 | 9 | 306 |
| [rdma_verification](per_topic/rdma_verification.md) | 32 | 88 | **81** | 7 | 27 | 250 |
| [arm_security](per_topic/arm_security.md) | 10 | 86 | **79** | 7 | 3 | 244 |
| [toe](per_topic/toe.md) | 9 | 76 | **69** | 7 | 2 | 214 |
| [dram_ddr](per_topic/dram_ddr.md) | 12 | 77 | **68** | 9 | 4 | 213 |
| [ethernet_dcmac](per_topic/ethernet_dcmac.md) | 10 | 75 | **66** | 9 | 1 | 207 |
| [ai_engineering](per_topic/ai_engineering.md) | 21 | 69 | **64** | 5 | 16 | 197 |
| [uvm](per_topic/uvm.md) | 24 | 45 | **43** | 2 | 22 | 131 |
| [soc_integration_cctv](per_topic/soc_integration_cctv.md) | 10 | 46 | **41** | 5 | 5 | 128 |
| [formal_verification](per_topic/formal_verification.md) | 13 | 30 | **27** | 3 | 10 | 84 |
| [bigtech_algorithm](per_topic/bigtech_algorithm.md) | 18 | 14 | **9** | 5 | 14 | 32 |

## Top MISSING terms (across all topics)

| Term | Total Freq | Topics |
|---|---|---|
| **DV** | 181 | ai_engineering, amba_protocols, arm_security, bigtech_algorithm, dram_ddr, ethernet_dcmac, formal_verification, mmu, pcie, rdma, soc_integration_cctv, soc_secure_boot, toe, ufs_hci, virtualization |
| **HW** | 178 | amba_protocols, arm_security, automotive_cybersecurity, mmu, pcie, rdma, rdma_verification, toe, ufs_hci, virtualization |
| **DMA** | 141 | amba_protocols, arm_security, dram_ddr, mmu, pcie, rdma, rdma_verification, soc_integration_cctv, soc_secure_boot, toe, ufs_hci, uvm, virtualization |
| **UVM** | 138 | ai_engineering, amba_protocols, dram_ddr, ethernet_dcmac, formal_verification, mmu, rdma, rdma_verification, soc_integration_cctv, soc_secure_boot, toe, ufs_hci, uvm |
| **TB** | 138 | ai_engineering, ethernet_dcmac, formal_verification, mmu, rdma, rdma_verification, soc_integration_cctv, soc_secure_boot, ufs_hci |
| **DUT** | 130 | ethernet_dcmac, formal_verification, mmu, pcie, rdma, rdma_verification, soc_secure_boot, toe, ufs_hci, uvm |
| **SW** | 123 | arm_security, automotive_cybersecurity, mmu, pcie, rdma, rdma_verification, soc_integration_cctv, soc_secure_boot, toe, ufs_hci, virtualization |
| **MMU** | 120 | amba_protocols, arm_security, dram_ddr, mmu, rdma, rdma_verification, soc_integration_cctv, uvm, virtualization |
| **CPU** | 114 | ai_engineering, amba_protocols, arm_security, dram_ddr, mmu, pcie, rdma, soc_integration_cctv, soc_secure_boot, toe, ufs_hci, virtualization |
| **VM** | 112 | arm_security, mmu, pcie, virtualization |
| **ACK** | 107 | automotive_cybersecurity, rdma, rdma_verification, toe |
| **ID** | 103 | amba_protocols, arm_security, automotive_cybersecurity, mmu, pcie, rdma, rdma_verification, soc_secure_boot, uvm, virtualization |
| **AI** | 101 | ai_engineering, amba_protocols, mmu, pcie, rdma, soc_integration_cctv |
| **DRAM** | 101 | amba_protocols, arm_security, dram_ddr, mmu, soc_integration_cctv, soc_secure_boot, toe, ufs_hci, virtualization |
| **UFS** | 100 | soc_integration_cctv, soc_secure_boot, ufs_hci, uvm |
| **IP** | 94 | ai_engineering, amba_protocols, automotive_cybersecurity, ethernet_dcmac, formal_verification, mmu, rdma_verification, soc_secure_boot, toe, uvm, virtualization |
| **IB** | 85 | rdma |
| **AXI** | 84 | dram_ddr, ethernet_dcmac, formal_verification, mmu, pcie, rdma, soc_integration_cctv, toe, ufs_hci, uvm, virtualization |
| **PA** | 81 | arm_security, mmu, pcie, rdma, rdma_verification, virtualization |
| **SVA** | 80 | amba_protocols, arm_security, dram_ddr, ethernet_dcmac, formal_verification, mmu, soc_integration_cctv, toe, ufs_hci |
| **SR** | 75 | pcie, rdma, rdma_verification, virtualization |
| **ARM** | 70 | amba_protocols, arm_security, automotive_cybersecurity, mmu, rdma, soc_secure_boot, virtualization |
| **EL3** | 69 | arm_security, soc_secure_boot |
| **QID** | 69 | rdma_verification |
| **IOV** | 62 | pcie, rdma, virtualization |
| **READ** | 62 | rdma, ufs_hci, uvm |
| **NAK** | 60 | rdma |
| **WRITE** | 59 | rdma, ufs_hci, uvm |
| **VA** | 58 | arm_security, mmu, virtualization |
| **L1** | 56 | automotive_cybersecurity, ethernet_dcmac, mmu, pcie, rdma, ufs_hci |
| **CQ** | 54 | rdma_verification, ufs_hci |
| **GPU** | 53 | ai_engineering, amba_protocols, arm_security, dram_ddr, mmu, pcie, rdma, virtualization |
| **EL1** | 53 | arm_security, mmu, soc_secure_boot, virtualization |
| **C2H** | 53 | rdma_verification |
| **TX** | 49 | amba_protocols, dram_ddr, ethernet_dcmac, pcie, rdma, toe, ufs_hci, virtualization |
| **IOMMU** | 48 | pcie, rdma, virtualization |
| **RX** | 46 | amba_protocols, dram_ddr, ethernet_dcmac, pcie, rdma, toe, ufs_hci, virtualization |
| **CRC** | 46 | automotive_cybersecurity, ethernet_dcmac, pcie, rdma, soc_secure_boot, toe, ufs_hci |
| **RDMA** | 46 | pcie, rdma_verification, toe |
| **SEND** | 46 | rdma |

## How to read

- Phase 2 진행 시 Priority 상위부터 batch 처리 권장.
- MISSING 후보는 false positive(코드 식별자, 일반 약어) 가 일부 섞여있을 수 있음 — 토픽별 상세 리포트(per_topic/) 의 등장 위치 확인 후 선별.
- ORPHAN 은 즉시 삭제하지 말고, 본문에서 의도적으로 안 쓴 항목인지 검토.
