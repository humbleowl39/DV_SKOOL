# PCIe 용어집

핵심 용어 ISO 11179 형식 정의.

---

## A — ACK / ACS / AER / ATS

### ACK (Acknowledge DLLP)

**Definition.** Receiver 의 Data Link Layer 가 LCRC 검증을 통과한 sequence number 를 누적하여 sender 에게 알리는 8-byte DLLP.

**Source.** PCIe Base Spec, Data Link Layer.

**Related.** NAK, Sequence Number, Replay Buffer.

**See also.** [Module 04](04_dllp_flow_control.md)

### ACS (Access Control Services)

**Definition.** Switch 와 Root Port 가 P2P TLP 를 redirect / block 할지 결정하는 Capability 의 정책 비트 집합.

**Source.** PCIe Base Spec, Extended Cap.

**Related.** P2P, IOMMU.

**See also.** [Module 08](08_advanced.md)

### AER (Advanced Error Reporting)

**Definition.** PCIe 의 표준 error reporting Extended Capability 로, error 를 Correctable / Uncorrectable Non-Fatal / Uncorrectable Fatal 로 분류해 Status / Mask / Severity register 에 기록한다.

**Source.** PCIe Base Spec, Extended Cap ID 0x0001.

**Related.** ERR_COR, ERR_NONFATAL, ERR_FATAL Message.

**See also.** [Module 07](07_power_aer_hotplug.md)

### ATS (Address Translation Service)

**Definition.** Device 가 IOMMU 에 IOVA→PA 변환을 미리 요청하고 결과를 자체 ATC (Address Translation Cache) 에 보관해 매번 IOMMU walk 를 회피하는 메커니즘.

**Source.** PCIe Base Spec, Extended Cap ID 0x000F.

**Related.** PASID, PRI, IOMMU, ATC.

**See also.** [Module 08](08_advanced.md)

### ASPM (Active State Power Management)

**Definition.** OS 개입 없이 link 자체가 idle 검출 후 L0s / L1 로 자동 진입하는 power management 메커니즘.

**Source.** PCIe Base Spec.

**Related.** L0s, L1, L1.1, L1.2.

**See also.** [Module 07](07_power_aer_hotplug.md)

---

## B — BAR / BDF

### BAR (Base Address Register)

**Definition.** Configuration Header 의 register (BAR0..BAR5) 로, device 의 MMIO / IO 영역의 base 주소와 size 를 SW 에 알리고 enumeration 시 SW 가 base 를 할당한다.

**Source.** PCIe Base Spec, Type 0/1 Configuration Header.

**Related.** BAR sizing, Type bit, Prefetchable.

**See also.** [Module 06](06_config_enumeration.md)

### BDF (Bus / Device / Function)

**Definition.** PCIe 트리 안에서 한 function 을 식별하는 16-bit 식별자 (Bus 8-bit + Device 5-bit + Function 3-bit; ARI 사용 시 Device 0 + Function 8-bit).

**Source.** PCIe Base Spec.

**Related.** Requester ID, ARI, Routing.

**See also.** [Module 03](03_tlp.md), [Module 06](06_config_enumeration.md)

---

## C — CRS / CXL

### CRS (Configuration Request Retry Status)

**Definition.** Device 가 link up 직후 enumeration 요청을 받았을 때 아직 ready 가 아니면 응답 status 로 보내는 코드 (0x2). SW 는 일정 시간 wait 후 재시도해야 한다.

**Source.** PCIe Base Spec, Completion Status.

**Related.** Boot hang, Vendor ID = 0xFFFF.

**See also.** [Module 06](06_config_enumeration.md)

### CXL (Compute Express Link)

**Definition.** PCIe 의 PHY 위에 별도 Link Layer + 3 transport (CXL.io / .cache / .mem) 를 정의해 cache-coherent accelerator 와 memory expansion 을 가능하게 하는 alternate protocol.

**Source.** CXL Consortium Specifications 1.1 / 2.0 / 3.0 / 3.1.

**Related.** Type 1/2/3, Alternate Protocol Negotiation.

**See also.** [Module 08](08_advanced.md)

### Configuration Space

**Definition.** 각 PCIe function 이 가지는 4 KB 의 register 영역으로, 첫 64 byte 의 표준 header (Type 0 또는 Type 1), 이후 PCI Capability list 와 Extended Capability list 로 구성된다.

**Source.** PCIe Base Spec.

**Related.** ECAM, Type 0, Type 1, Capability list.

**See also.** [Module 06](06_config_enumeration.md)

---

## D — DLLP

### DLLP (Data Link Layer Packet)

**Definition.** Data Link Layer 의 link-only 8-byte packet 으로, Ack / Nak / FC Init/Update / PM / Vendor 등의 type 을 가진다.

**Source.** PCIe Base Spec, Data Link Layer.

**Related.** ACK, NAK, FC Update, TLP.

**See also.** [Module 04](04_dllp_flow_control.md)

### D-state

**Definition.** Device 의 power state (D0 active / D1 / D2 / D3hot / D3cold) 로, OS / driver 가 PCI-PM Capability 를 통해 관리한다.

**Source.** PCIe Base Spec, PM Capability.

**Related.** L-state, PME.

**See also.** [Module 07](07_power_aer_hotplug.md)

---

## E — ECAM / ECRC / EP / Equalization

### ECAM (Enhanced Configuration Access Mechanism)

**Definition.** Configuration Space 4 KB 전체를 MMIO 영역으로 mapping 해 host SW 가 일반 load/store 로 access 하도록 하는 메커니즘.

**Source.** PCIe Base Spec.

**Related.** Configuration Space, BDF.

**See also.** [Module 06](06_config_enumeration.md)

### ECRC (End-to-End CRC)

**Definition.** Transaction Layer 의 optional 32-bit CRC 로, TLP header (변경 가능 field 제외) 와 payload 위로 계산되어 라우팅 노드를 통과해도 변경되지 않는다.

**Source.** PCIe Base Spec, Transaction Layer.

**Related.** LCRC, AER.

**See also.** [Module 03](03_tlp.md)

### Endpoint (EP)

**Definition.** PCIe 트리의 leaf device 로 Type 0 Configuration Header 를 가지며 NVMe / NIC / GPU 등 실제 기능을 제공한다.

**Source.** PCIe Base Spec.

**Related.** Type 0, Switch, Root Complex.

**See also.** [Module 01](01_pcie_motivation.md)

### Equalization

**Definition.** Gen3+ 의 Recovery 안의 4-phase 절차로, 양 끝의 Tx FFE coefficient 를 receiver 가 협상하여 channel BER 를 최적화한다.

**Source.** PCIe Base Spec, PHY Layer.

**Related.** Phase 0/1/2/3, Tx FFE, Rx CTLE/DFE, Preset.

**See also.** [Module 05](05_phy_ltssm.md)

---

## F — FC / FLIT / FLR

### FC (Flow Control)

**Definition.** Receiver 의 RX buffer 점유를 sender 에 advertise 하여 송신 속도를 조절하는 credit-based 메커니즘으로, Posted / Non-Posted / Completion 의 6 그룹 (Header + Data) 으로 구성된다.

**Source.** PCIe Base Spec, Transaction Layer + Data Link Layer.

**Related.** InitFC1/InitFC2, UpdateFC, VC.

**See also.** [Module 04](04_dllp_flow_control.md)

### FLIT (Flow Control unIT)

**Definition.** Gen6+ 의 고정 256-byte 프레임 단위로, TLP/DLLP 를 함께 담아 framing 단순화 + FEC 통합 + ACK/NAK 메커니즘 단순화를 달성한다.

**Source.** PCIe Base Spec 6.0.

**Related.** PAM4, FEC.

**See also.** [Module 04](04_dllp_flow_control.md), [Module 05](05_phy_ltssm.md)

### FLR (Function-Level Reset)

**Definition.** Device Control register 의 Initiate FLR bit 으로 트리거되어 한 function 만 logical reset 하는 메커니즘으로, in-flight TLP drop + 일부 register reset 후 100 ms 안에 다시 사용 가능해진다.

**Source.** PCIe Base Spec.

**Related.** Hot Reset, Secondary Bus Reset.

**See also.** [Module 06](06_config_enumeration.md)

---

## L — L-state / LCRC / LTSSM

### L-state

**Definition.** Link 의 LTSSM 상태 (L0 / L0s / L1 / L1.1 / L1.2 / L2) 로, 각자 다른 절전 수준과 exit latency 를 가진다.

**Source.** PCIe Base Spec, Physical Layer.

**Related.** ASPM, D-state.

**See also.** [Module 05](05_phy_ltssm.md), [Module 07](07_power_aer_hotplug.md)

### LCRC (Link CRC)

**Definition.** Data Link Layer 가 TLP + Sequence # 위로 계산하는 32-bit CRC 로, hop-level (link 단일 segment) 무결성을 보장한다.

**Source.** PCIe Base Spec, Data Link Layer.

**Related.** ECRC, Replay Buffer.

**See also.** [Module 02](02_layer_architecture.md), [Module 04](04_dllp_flow_control.md)

### LTSSM (Link Training and Status State Machine)

**Definition.** Physical Layer 의 11-state state machine 으로 Detect → Polling → Configuration → L0 → L0s/L1/L2/Recovery/Disabled/Loopback/Hot Reset 의 link 상태 전이를 관리한다.

**Source.** PCIe Base Spec, Physical Layer.

**Related.** TS1/TS2, Equalization.

**See also.** [Module 05](05_phy_ltssm.md)

---

## M — MPS / MRRS / MSI / MSI-X

### MPS (Max Payload Size)

**Definition.** Device 가 한 TLP 로 보낼 수 있는 최대 data payload size 로, 128 / 256 / 512 / 1024 / 2048 / 4096 byte 중 link 양 끝의 capability 의 minimum 이 사용된다.

**Source.** PCIe Base Spec, PCIe Capability.

**Related.** MRRS, TLP Length.

**See also.** [Module 03](03_tlp.md)

### MRRS (Max Read Request Size)

**Definition.** Requester 가 한 번의 Memory Read Request 로 요청할 수 있는 최대 byte 로, MPS 와 별도로 설정된다.

**Source.** PCIe Base Spec, PCIe Capability.

**Related.** MPS, Tag.

**See also.** [Module 03](03_tlp.md)

### MSI / MSI-X

**Definition.** Memory Write TLP 형식의 in-band interrupt 메커니즘으로, MSI 는 1-32 vector, MSI-X 는 최대 2048 vector 와 vector 별 mask 를 지원한다.

**Source.** PCIe Base Spec, PCI Capability ID 0x05 / 0x11.

**Related.** Legacy INTx.

**See also.** [Module 06](06_config_enumeration.md)

---

## N — NAK / NP

### NAK (Negative Acknowledge DLLP)

**Definition.** Receiver 의 LCRC 검증 실패 또는 sequence number 위반 시 sender 에게 재송신을 요청하는 8-byte DLLP.

**Source.** PCIe Base Spec, Data Link Layer.

**Related.** Replay Buffer, Sequence Number.

**See also.** [Module 04](04_dllp_flow_control.md)

### Non-Posted (NP)

**Definition.** Completion (Cpl 또는 CplD) 응답이 필수인 TLP 카테고리로, MRd, IORd, IOWr, CfgRd/Wr, AtomicOp 가 해당된다.

**Source.** PCIe Base Spec.

**Related.** Posted, Completion, Credit groups.

**See also.** [Module 03](03_tlp.md)

---

## P — PASID / P2P / PHY / Posted / PRI

### PASID (Process Address Space ID)

**Definition.** TLP 의 PASID prefix/extension 으로 운반되는 20-bit 식별자로, IOMMU 가 device 의 DMA 를 어느 process 의 address space 로 매핑할지 결정하게 한다.

**Source.** PCIe Base Spec, Extended Cap ID 0x0023.

**Related.** ATS, IOMMU, SVM.

**See also.** [Module 08](08_advanced.md)

### P2P (Peer-to-Peer DMA)

**Definition.** 두 Endpoint 가 Root Complex 를 거치지 않고 Switch 안에서 직접 DMA 하는 traffic pattern.

**Source.** PCIe Base Spec.

**Related.** ACS, GPU↔NIC, NCCL.

**See also.** [Module 08](08_advanced.md)

### Physical Layer (PHY)

**Definition.** PCIe 의 최하위 계층으로 Framing / Encoding / Scrambling / SerDes / LTSSM / Equalization 을 담당한다.

**Source.** PCIe Base Spec, Physical Layer.

**Related.** PCS, PMA, Lane.

**See also.** [Module 02](02_layer_architecture.md), [Module 05](05_phy_ltssm.md)

### Posted (P)

**Definition.** TL-level 응답이 없는 TLP 카테고리 (MWr, MsgD) 로, DLL 의 ACK/NAK 은 받지만 application-level completion 은 별도이다.

**Source.** PCIe Base Spec.

**Related.** Non-Posted, Completion.

**See also.** [Module 03](03_tlp.md)

### PRI (Page Request Interface)

**Definition.** Device 가 ATS 의 page fault 를 OS / IOMMU 에 알려 page-in 후 재시도하도록 하는 메커니즘.

**Source.** PCIe Base Spec, Extended Cap ID 0x0013.

**Related.** ATS, ODP.

**See also.** [Module 08](08_advanced.md)

---

## R — RC / Replay Buffer / Routing

### Root Complex (RC)

**Definition.** CPU ↔ PCIe 도메인의 게이트웨이로, Root Port 가 다운스트림 link 의 시작점이며 memory controller 와 합쳐진 경우가 많다.

**Source.** PCIe Base Spec.

**Related.** Switch, Endpoint, Bridge.

**See also.** [Module 01](01_pcie_motivation.md)

### Replay Buffer

**Definition.** Sender 의 Data Link Layer 가 ACK 받기 전까지 송신한 TLP 를 보관하는 buffer 로, NAK 시 그 sequence number 부터 재송신한다.

**Source.** PCIe Base Spec, Data Link Layer.

**Related.** ACK, NAK, Sequence Number.

**See also.** [Module 04](04_dllp_flow_control.md)

---

## S — SerDes / Sequence Number / SR-IOV / Switch

### SerDes (Serializer/Deserializer)

**Definition.** 병렬 데이터를 직렬 differential signal 로 변환 (Tx) 하고 직렬 신호를 병렬로 복원 (Rx) 하는 PHY 의 analog block.

**Source.** PCIe Base Spec, PHY.

**Related.** PMA, CDR.

**See also.** [Module 05](05_phy_ltssm.md)

### Sequence Number

**Definition.** Data Link Layer 가 송신 TLP 마다 부여하는 12-bit (modulo 4096) 순차 번호로, ACK / NAK / Replay Buffer 의 기준이 된다.

**Source.** PCIe Base Spec, Data Link Layer.

**Related.** ACK, NAK, Replay Buffer.

**See also.** [Module 04](04_dllp_flow_control.md)

### SR-IOV (Single-Root I/O Virtualization)

**Definition.** 한 PCIe device 가 여러 lightweight Virtual Function (VF) 을 expose 해, 각 VF 가 별도 BDF + 별도 BAR + 별도 MSI-X 를 가지고 hypervisor 가 게스트에 직접 패스스루할 수 있게 하는 메커니즘.

**Source.** PCIe Base Spec, Extended Cap ID 0x0010.

**Related.** PF, VF, ARI, IOMMU.

**See also.** [Module 08](08_advanced.md)

### Switch

**Definition.** PCIe 의 fan-out 디바이스로 upstream port 1 + downstream port N 을 가지고 TLP 를 라우팅한다.

**Source.** PCIe Base Spec.

**Related.** Type 1 Header, Bridge.

**See also.** [Module 01](01_pcie_motivation.md)

---

## T — Tag / TC / TLP / Type 0 / Type 1

### Tag

**Definition.** Non-Posted Request 마다 Requester 가 부여하는 8-bit (extended 시 10-bit) 식별자로, Completion 매칭에 사용된다.

**Source.** PCIe Base Spec, TLP Header.

**Related.** Outstanding NP, Cpl.

**See also.** [Module 03](03_tlp.md)

### TC (Traffic Class)

**Definition.** TLP header 의 3-bit 필드로 Virtual Channel (VC) 매핑에 사용되는 우선순위 식별자.

**Source.** PCIe Base Spec, TLP Header.

**Related.** VC, ATTR.

**See also.** [Module 03](03_tlp.md)

### TLP (Transaction Layer Packet)

**Definition.** Transaction Layer 의 packet 으로, header (3DW 또는 4DW) + payload (0..4096 byte) + optional ECRC 의 구조를 가진다.

**Source.** PCIe Base Spec, Transaction Layer.

**Related.** Fmt, Type, DLLP.

**See also.** [Module 03](03_tlp.md)

### Type 0 / Type 1 (Configuration Header)

**Definition.** Type 0 = Endpoint 의 64-byte Configuration Header (BAR0..5 등), Type 1 = Bridge / Switch port 의 64-byte Configuration Header (Sec/Sub Bus #, Mem/IO Base/Limit 등).

**Source.** PCIe Base Spec.

**Related.** BDF, BAR.

**See also.** [Module 06](06_config_enumeration.md)

---

## V — VC

### VC (Virtual Channel)

**Definition.** 물리 link 위에서 독립적인 buffer + flow control credit 을 가지는 가상 채널로, 0..7 의 ID 를 가진다 (대부분 시스템은 VC0 만 사용).

**Source.** PCIe Base Spec, Extended Cap ID 0x0002.

**Related.** TC, FC.

**See also.** [Module 04](04_dllp_flow_control.md)

---

## 추가 항목 (Phase 2 검수 완료)

### IOV (I/O Virtualization)

**Definition.** PCIe 디바이스를 다수의 가상 머신에 분할 노출하는 가상화 기술 군의 총칭으로, SR-IOV / MR-IOV 등을 포함한다.

**Source.** PCIe SIG IOV ECN; PCIe Base Spec ATS/PRI Annex.

**Related.** SR-IOV, VF, PF, ATS.

**See also.** [Module 03](03_tlp.md), [Module 06](06_config_enumeration.md)

### SR-IOV (Single-Root I/O Virtualization)

**Definition.** 단일 PCIe Root Complex 하의 디바이스가 PF 1개와 다수 VF 를 제공해 hypervisor 우회 (kernel bypass) 가상화를 지원하는 표준.

**Source.** PCI SIG, *SR-IOV 1.1 Specification*.

**Related.** PF, VF, IOV, BAR, ATS.

**See also.** [Module 06](06_config_enumeration.md)

### FEC (Forward Error Correction)

**Definition.** PCIe Gen6 이상에서 PAM4 신호의 BER 를 보상하기 위해 송신측이 redundancy 코드를 추가하고 수신측이 정정하는 link-layer 기능.

**Source.** PCIe Base Spec 6.0, §4.5 (Flit Mode FEC).

**Related.** PAM4, Flit Mode, LCRC, ECRC.

**See also.** [Module 05](05_phy_ltssm.md), [Module 08](08_advanced.md)

### CDR (Clock-Data Recovery)

**Definition.** Receiver 가 incoming serial bitstream 의 transition 으로부터 sampling clock 을 복원하는 PHY block.

**Source.** PCIe Base Spec — Physical Layer; common SerDes terminology.

**Related.** Equalization, Deskew, Symbol/Block Alignment.

**See also.** [Module 05](05_phy_ltssm.md)

### ARI (Alternative Routing-ID Interpretation)

**Definition.** 단일 device function 수를 8 → 256 으로 확장하기 위해 BDF 의 Device 필드를 Function 필드로 재해석하는 PCIe Capability.

**Source.** PCIe Base Spec — ARI Capability.

**Related.** BDF, SR-IOV, PF, VF.

**See also.** [Module 06](06_config_enumeration.md)



### PAM4 (4-level Pulse Amplitude Modulation)

**Definition.** 한 심볼에 2비트를 매핑(00/01/10/11)하여 동일 baud rate 에서 데이터율을 두 배로 늘리는 PCIe Gen6 의 신호 변조 방식.

**Source.** PCIe Base Spec 6.0, §4.

**Related.** NRZ, FEC, Flit Mode, link training.

**See also.** [Module 05](05_phy_ltssm.md), [Module 08](08_advanced.md)

### LTSSM (Link Training and Status State Machine)

**Definition.** PCIe Physical Layer 가 link 의 detect / polling / configuration / L0 / L1 / recovery 등 상태 전이를 관리하는 표준 FSM.

**Source.** PCIe Base Spec — Physical Layer LTSSM.

**Related.** TS1, TS2, Recovery, Polling, Detect, L0, L0s.

**See also.** [Module 05](05_phy_ltssm.md)

### IOMMU (I/O Memory Management Unit)

**Definition.** PCIe / AMBA 디바이스의 DMA 주소를 시스템 메모리의 가상 주소 → 물리 주소로 변환하고 보호 검사를 수행하는 하드웨어 유닛으로, 가상화·보안 모두에 사용된다.

**Source.** Intel VT-d, AMD-Vi, ARM SMMU spec.

**Related.** ATS, PRI, SR-IOV, MMU.

**See also.** [Module 06](06_config_enumeration.md)

### MMIO (Memory-Mapped I/O)

**Definition.** 디바이스 레지스터를 시스템 메모리 주소 공간에 매핑하여 일반 load/store 명령으로 접근하도록 하는 방식.

**Source.** PCIe Base Spec — Configuration & BAR.

**Related.** BAR, Type 0/1 Header, prefetchable region.

**See also.** [Module 06](06_config_enumeration.md)

