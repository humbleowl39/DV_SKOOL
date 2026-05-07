# RDMA 용어집

핵심 용어 ISO 11179 형식 정의. 각 항목은 단일 정의 문장 + Source + Related + 사용 예 + 참조 모듈로 구성.

---

## A — AETH

### AETH (ACK Extended Transport Header)

**Definition.** RC 의 ACK / NAK 패킷에 포함되는 4-byte extended transport header 로, syndrome 과 message sequence number 를 담는다.

**Source.** IB Spec 1.7, §9.5.

**Related.** ACK, NAK, syndrome, RNR.

**Example.** ACK 의 syndrome=0x00 + credit, NAK PSN Sequence Error syndrome=0x80.

**See also.** [Module 06](06_data_path.md)

### ATOMIC

**Definition.** 원격 메모리에 대해 atomic 하게 (1) Compare-and-Swap 또는 (2) Fetch-and-Add 를 수행하는 RDMA operation.

**Source.** IB Spec 1.7, §9.4.6.

**Related.** AtomicETH, AtomicAckETH, max_dest_rd_atomic.

**See also.** [Module 06](06_data_path.md)

---

## B — BTH

### BTH (Base Transport Header)

**Definition.** 모든 IBA transport packet 의 12-byte 필수 헤더로, OpCode/P_Key/DestQP/PSN/AckReq 등 transport 의 기본 정보를 담는다.

**Source.** IB Spec 1.7, §9.2.

**Related.** OpCode, PSN, P_Key.

**Example.** OpCode=0x04 (RC SEND_ONLY), PSN=0x000010, A=1.

**See also.** [Module 02](02_ib_protocol_stack.md), [Module 06](06_data_path.md)

---

## C — CNP

### CNP (Congestion Notification Packet)

**Definition.** RoCEv2 에서 receiver 가 sender 에 ECN-CE 마킹을 명시적으로 알리기 위해 송신하는 단방향 통지 패킷.

**Source.** IBTA, *Annex A17* §A17.9.

**Related.** ECN, DCQCN, BTH FECN/BECN.

**See also.** [Module 07](07_congestion_error.md)

### CQ (Completion Queue)

**Definition.** RDMA operation 완료 시 NIC 가 WC (Work Completion) 를 enqueue 하는 사용자/커널 가시 큐.

**Source.** IB Spec 1.7, §10.4.

**Related.** WC, ibv_poll_cq, Error CQ.

**See also.** [Module 01](01_rdma_motivation.md), [Module 04](04_service_types_qp.md)

---

## D — DCQCN

### DCQCN (Data Center Quantized Congestion Notification)

**Definition.** ECN/CNP 신호를 받은 sender 가 송신율을 단계적으로 감소시키고 안정 후 점진 회복시키는 RoCEv2 의 표준 congestion control 알고리즘.

**Source.** Zhu et al., "Congestion Control for Large-Scale RDMA Deployments", SIGCOMM 2015 + IBTA Annex.

**Related.** PFC, ECN, CNP.

**See also.** [Module 07](07_congestion_error.md)

### DETH (Datagram Extended Transport Header)

**Definition.** UD service 의 모든 패킷에 포함되는 8-byte ETH 로, Q_Key 와 SrcQP 를 담는다.

**Source.** IB Spec 1.7, §9.5.

**Related.** UD, Q_Key.

**See also.** [Module 04](04_service_types_qp.md)

---

## E — ECN

### ECN (Explicit Congestion Notification)

**Definition.** Switch 가 packet drop 대신 IP 헤더의 CE bit 를 set 해 congestion 을 알리는 RFC 3168 메커니즘.

**Source.** RFC 3168.

**Related.** CNP, DCQCN, FECN/BECN (in BTH).

**See also.** [Module 07](07_congestion_error.md)

---

## G — GRH

### GRH (Global Route Header)

**Definition.** Subnet 간 또는 multicast 시 IB 패킷에 포함되는 40-byte IPv6-format 헤더로, SGID/DGID/HopLmt/PayLen 등을 담는다.

**Source.** IB Spec 1.7, §8.4.

**Related.** GID, IPVer, FlowLabel.

**Example.** RoCEv2 에서 GRH 는 IPv4/IPv6 헤더로 매핑됨.

**See also.** [Module 02](02_ib_protocol_stack.md), [Module 03](03_rocev2.md)

### GID (Global ID)

**Definition.** IB 노드를 subnet 간에 식별하는 128-bit IPv6-format 주소.

**Source.** IB Spec 1.7, §4.1.1.

**Related.** GUID, IPv6 mapping.

---

## H — HCA

### HCA (Host Channel Adapter)

**Definition.** Host 시스템에 attach 되어 RDMA 를 지원하는 IB 디바이스 (NIC) 의 IB 표준 명칭.

**Source.** IB Spec 1.7, §17.

**Related.** RNIC (RoCE/iWARP), NIC.

**See also.** [Module 01](01_rdma_motivation.md)

---

## I — ICRC

### ICRC (Invariant CRC)

**Definition.** 라우팅 시 변경되는 영역을 제외하고 계산되어 end-to-end 보존되는 32-bit CRC 필드.

**Source.** IB Spec 1.7, §7.8.1; RoCEv2 IBTA Annex A17 (계산 input mask).

**Related.** VCRC, FCS.

**See also.** [Module 02](02_ib_protocol_stack.md), [Module 03](03_rocev2.md)

### IETH (Invalidate Extended Transport Header)

**Definition.** SEND_w_INV operation 에 포함되는 4-byte ETH 로, invalidate 대상 R_Key 를 담는다.

**Source.** IB Spec 1.7, §9.5.

**Related.** SEND_LAST_w_INV, SEND_ONLY_w_INV.

**See also.** [Module 06](06_data_path.md)

### IOVA (IO Virtual Address)

**Definition.** Device (NIC) 가 사용하는 가상 주소로, ATS/PTW/TLB 에 의해 host PA 로 변환된다.

**Source.** PCIe ATS spec / OS IOMMU.

**Related.** ATS, PTW, TLB, IOMMU/SMMU.

**See also.** [Module 05](05_memory_model.md)

---

## L — LRH

### LRH (Local Route Header)

**Definition.** IB 패킷의 8-byte link-level 헤더로, SLID/DLID/VL/SL/LNH/PktLen 등을 담는다.

**Source.** IB Spec 1.7, §7.7.

**Related.** SLID, DLID, VL, SL.

**Example.** RoCEv2 에서는 LRH 가 사라지고 Ethernet 헤더가 그 역할을 한다.

**See also.** [Module 02](02_ib_protocol_stack.md), [Module 03](03_rocev2.md)

### L_Key (Local Key)

**Definition.** Memory Registration 시 발급되어 같은 노드 내 sg_list 등 local 참조에서 MR 을 검증하는 식별자.

**Source.** IB Spec 1.7, §10.6.

**Related.** R_Key, MR, PD.

**See also.** [Module 05](05_memory_model.md)

---

## M — MR

### MR (Memory Region)

**Definition.** Memory Registration 으로 NIC 에 등록된 가상 주소 연속 영역과 access 권한, key, PD 의 묶음.

**Source.** IB Spec 1.7, §10.6.

**Related.** PD, L_Key, R_Key, access flag.

**See also.** [Module 05](05_memory_model.md)

### MW (Memory Window)

**Definition.** MR 의 부분 영역에 대해 일시적으로 별도의 R_Key 를 발급해 짧은 lifetime 의 권한 위임을 가능케 하는 객체.

**Source.** IB Spec 1.7, §10.6.7.

**Related.** Type 1 MW, Type 2 MW, R_Key.

**See also.** [Module 05](05_memory_model.md)

---

## P — PD

### PD (Protection Domain)

**Definition.** QP, MR 등 RDMA 객체들을 그룹으로 묶어 cross-domain 접근을 차단하는 보호 경계 식별자.

**Source.** IB Spec 1.7, §10.5.

**Related.** MR, QP, access flag.

**See also.** [Module 05](05_memory_model.md)

### PFC (Priority Flow Control)

**Definition.** Switch buffer 가 임계 초과 시 upstream 에 priority 별 PAUSE 프레임을 송신해 hop-by-hop 으로 송신을 일시 정지시키는 IEEE 802.1Qbb 메커니즘.

**Source.** IEEE 802.1Qbb.

**Related.** Lossless Ethernet, deadlock, ECN.

**See also.** [Module 07](07_congestion_error.md)

### P_Key (Partition Key)

**Definition.** BTH 에 포함되는 16-bit 키로, IB subnet 내 partition 내 멤버임을 검증한다.

**Source.** IB Spec 1.7, §9.2.5.

**Related.** Subnet Manager (IB only).

**Example.** RoCEv2 에서 P_Key 는 BTH 에 남지만 enforcement 는 implementation-defined.

**See also.** [Module 02](02_ib_protocol_stack.md)

### PSN (Packet Sequence Number)

**Definition.** RC 의 BTH 에 포함되는 24-bit 순차 식별자로, packet 단위 순서와 retransmit 의 기준이 된다.

**Source.** IB Spec 1.7, §9.7.2.

**Related.** AckReq, AETH, ePSN, retry timer.

**See also.** [Module 06](06_data_path.md)

### PTW (Page Table Walker)

**Definition.** IOVA 의 TLB miss 시 page table 을 다단계로 walk 해 PA 를 찾는 NIC/IOMMU 의 하드웨어 모듈.

**Source.** PCIe ATS / OS page table 형식.

**Related.** TLB, ATS, MMU.

**See also.** [Module 05](05_memory_model.md), [Module 08](08_rdma_tb_dv.md)

---

## Q — QP

### QP (Queue Pair)

**Definition.** RDMA 의 endpoint 단위로, Send Queue 와 Receive Queue 의 쌍과 service type, state 의 집합으로 정의된다.

**Source.** IB Spec 1.7, §10.3.

**Related.** SQ, RQ, RC/UC/UD/XRC, FSM (Reset/Init/RTR/RTS/SQD/SQErr/Err).

**See also.** [Module 04](04_service_types_qp.md)

### Q_Key

**Definition.** UD service 의 DETH 에 포함되어 unprivileged Q_Key (high bit 0) 와 privileged Q_Key (high bit 1) 를 구분하고, receive 측에서 검증되는 key.

**Source.** IB Spec 1.7, §9.5.

**Related.** UD, DETH.

**See also.** [Module 04](04_service_types_qp.md)

---

## R — RC

### RC (Reliable Connection)

**Definition.** 1:1 connection 기반의 신뢰성 있는 message 전달 service type 으로, PSN/ACK/NAK/retry 가 hardware 에 의해 보장된다.

**Source.** IB Spec 1.7, §9.7.

**Related.** UC, UD, XRC, retry_cnt, rnr_retry.

**See also.** [Module 04](04_service_types_qp.md)

### RETH (RDMA Extended Transport Header)

**Definition.** RDMA WRITE FIRST/ONLY 와 READ Request 패킷에 포함되는 16-byte ETH 로, remote_va, length, R_Key 를 담는다.

**Source.** IB Spec 1.7, §9.5.

**Related.** R_Key, RDMA WRITE, RDMA READ.

**See also.** [Module 06](06_data_path.md)

### R_Key (Remote Key)

**Definition.** 원격 노드가 RDMA WRITE/READ/ATOMIC 의 RETH/AtomicETH 에 넣어 보내, responder side 가 MR 접근을 검증하는 식별자.

**Source.** IB Spec 1.7, §10.6.

**Related.** L_Key, MR, MW.

**See also.** [Module 05](05_memory_model.md)

### RDMA-CM (Connection Manager)

**Definition.** RoCEv2 에서 TCP 위에서 동작하는 RDMA connection establishment 프로토콜로, IB 의 CM (over MAD) 을 대체한다.

**Source.** OFED librdmacm.

**Related.** CM (IB), QP modify.

**See also.** [Module 03](03_rocev2.md)

### RNR (Receiver Not Ready)

**Definition.** RC SEND 가 도착했으나 receiver 의 RQ 에 사용 가능한 RECV WR 이 없을 때 responder 가 보내는 NAK syndrome.

**Source.** IB Spec 1.7, §9.7.5.

**Related.** rnr_retry, min_rnr_timer.

**See also.** [Module 06](06_data_path.md), [Module 07](07_congestion_error.md)

### RoCEv2

**Definition.** Ethernet (L2) | IPv4/IPv6 (L3) | UDP dest port 4791 (L4) | BTH 의 stack 으로 IB transport 를 그대로 사용하는 데이터센터 표준 RDMA 프로토콜.

**Source.** IBTA, *Annex A17 RoCEv2*.

**Related.** RoCEv1, IB, iWARP.

**See also.** [Module 03](03_rocev2.md)

---

## S — SL

### SL (Service Level)

**Definition.** LRH 의 4-bit 필드로, subnet 내 QoS 클래스를 식별하며 SL→VL 매핑에 사용된다.

**Source.** IB Spec 1.7, §7.6.5.

**Related.** VL, QoS.

**See also.** [Module 02](02_ib_protocol_stack.md)

### SQ / RQ

**Definition.** QP 의 송신 큐 (Send Queue) 와 수신 큐 (Receive Queue). 각각 Send WR 과 Recv WR 가 enqueue 됨.

**Source.** IB Spec 1.7, §10.3.

**Related.** WR, WQE.

**See also.** [Module 04](04_service_types_qp.md)

---

## T — TLB

### TLB (Translation Lookaside Buffer)

**Definition.** IOVA→PA 변환 결과를 캐시해 매번 page table walk 를 피하는 device-side cache.

**Source.** PCIe ATS.

**Related.** PTW, ATS, invalidate.

**See also.** [Module 05](05_memory_model.md), [Module 08](08_rdma_tb_dv.md)

---

## U — UC / UD

### UC (Unreliable Connection)

**Definition.** 1:1 connection 이지만 신뢰성 (ACK/retry) 이 보장되지 않는 service type.

**Source.** IB Spec 1.7, §9.8.1.

**Related.** RC, packet drop.

### UD (Unreliable Datagram)

**Definition.** Connectionless 한 service type 으로, 한 message 가 한 packet (≤ MTU − header) 으로 제한되며 multicast 가 가능하다.

**Source.** IB Spec 1.7, §9.8.2.

**Related.** DETH, Q_Key, multicast.

---

## V — VCRC / VL / Verbs

### VCRC (Variant CRC)

**Definition.** IB 패킷의 link-level 무결성 보장을 위한 16-bit CRC 로, hop 마다 재계산된다.

**Source.** IB Spec 1.7, §7.8.2.

**Related.** ICRC, Eth FCS (RoCEv2 대체).

**See also.** [Module 02](02_ib_protocol_stack.md)

### VL (Virtual Lane)

**Definition.** IB 링크 위에서 독립적인 buffer 와 credit 을 가지는 가상 채널로, 0..15 까지 정의되며 VL15 는 management 전용이다.

**Source.** IB Spec 1.7, §7.6.

**Related.** SL, flow control, PFC (Ethernet 대체).

**See also.** [Module 02](02_ib_protocol_stack.md)

### Verbs

**Definition.** RDMA 객체를 사용자/커널이 조작하기 위한 abstract API 로, libibverbs / OFED 가 표준 구현.

**Source.** IB Spec 1.7, §11; OFED.

**Related.** ibv_reg_mr, ibv_post_send, ibv_poll_cq.

**See also.** [Module 01](01_rdma_motivation.md)

---

## W — WC / WQE

### WC (Work Completion)

**Definition.** WQE 처리 결과를 알리는 CQ 의 entry 로, status, opcode, byte count, source QP 등을 포함한다.

**Source.** IB Spec 1.7, §10.4.

**Related.** CQ, ibv_poll_cq, WC status enum.

### WQE (Work Queue Element)

**Definition.** 사용자가 SQ 또는 RQ 에 enqueue 하는 RDMA operation 의 디스크립터로, opcode, sg_list, RETH 등을 포함한다.

**Source.** IB Spec 1.7, §10.4.

**Related.** WR, WC.

---

## X — XRC

### XRC (eXtended Reliable Connection)

**Definition.** 한 receive side QP 를 여러 sender QP 가 공유하는 service type 으로, hyperscale 환경의 N×N QP 비대칭 증가를 완화한다.

**Source.** IB Spec 1.2.1+.

**Related.** SRQ, scaling.

**See also.** [Module 04](04_service_types_qp.md)
