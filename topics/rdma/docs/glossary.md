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

---

## Appendix A. 내부 IP / RDMA-TB 용어

!!! note "Internal (Confluence: RDMA IP architecture, High-Level Architecture Description)"
    이 절은 GPUBoost / RDMA-IP 의 사내 wrapper 명·자료형·내부 약어 정의입니다. Spec 표준 용어가 아닙니다. 출처는 각 항목에 표기.

### completer_frontend

**Definition.** Requester 측에서 응답 패킷(ACK/NAK/Read Response)을 처리해 WQE 완료·CQE 생성·retry 트리거를 담당하는 RDMA-IP 의 wrapper.

**Source.** Confluence: *Completer* (id=1212973064).

**Related.** completer_retry, info_arb, payload engine, mb_cqe.

**Example.** `s_comp_header_stream` 에서 incoming 응답 패킷을 받아 QP·QP-state metadata 를 read → drop1/drop2 신호 발행 → CQE 생성 + WQE 삭제.

**See also.** [Module 08](08_rdma_tb_dv.md), [Module 11](11_gpuboost_rdma_ip.md)

### completer_retry

**Definition.** Completer 내부에서 timer 만료·NAK·SACK 기반의 재전송을 결정하고 info_arb 에 fetch 명령을 보내는 sub-block.

**Source.** Confluence: *Completer*; *PSN handling & retransmission of RDMA*.

**Related.** completer_frontend, retry timer, RNR.

**See also.** [Module 06](06_data_path.md), [Module 11](11_gpuboost_rdma_ip.md)

### responder_frontend

**Definition.** Responder 측에서 incoming 요청 패킷을 처리해 메모리 access·ACK 생성·MSN 증가를 담당하는 RDMA-IP 의 wrapper.

**Source.** Confluence: *responder_frontend & completer_frontend analysis* (id=1229914213).

**Related.** completer_frontend, MSN, ePSN, payload engine.

**See also.** [Module 08](08_rdma_tb_dv.md), [Module 11](11_gpuboost_rdma_ip.md)

### info_arb

**Definition.** WQE metadata (`tx_info`) 를 보관하고 fetch/refresh 요청을 중재하는 RDMA-IP 의 SWQ 인터페이스 측 모듈.

**Source.** Confluence: *Completer* §2.4 Retry handling.

**Related.** SWQ, mb_mem_cmd, mb_swq_cmd, retry.

**See also.** [Module 11](11_gpuboost_rdma_ip.md)

### SWQ (Send Work Queue, internal)

**Definition.** RDMA-IP 내에서 WQE 메타데이터를 저장·재읽기하는 내부 큐 인프라로, 외부 spec 의 SQ 와는 독립적으로 다중 read port 를 노출한다.

**Source.** Confluence: *Completer* §1.3 (s_data_port_0/3/4), §1.4 (m_cmd_port_0/1/3/4).

**Related.** info_arb, mb_swq_cmd.

**See also.** [Module 08](08_rdma_tb_dv.md), [Module 11](11_gpuboost_rdma_ip.md)

### payload engine (RDMA-IP)

**Definition.** Completer/Responder 가 발행한 `mb_payload_cmd` 를 받아 payload 의 drop / DMA write 경로를 결정하는 데이터패스 엔진.

**Source.** Confluence: *Completer* §1.4 (m_comp_payload_cmd_stream).

**Related.** drop1/drop2/drop3, DMA write.

**See also.** [Module 11](11_gpuboost_rdma_ip.md)

### ePSN (expected PSN, internal)

**Definition.** Responder 가 다음에 받을 것으로 예상하는 PSN 값으로, incoming PSN < ePSN 이면 duplicate, > ePSN 이면 PSN sequence error.

**Source.** Confluence: *Completer* §3.1.3.1; *PSN handling & retransmission of RDMA*.

**Related.** PSN, duplicate, NAK PSN sequence error.

**See also.** [Module 06](06_data_path.md)

### SACK (Selective ACK, RDMA-TB)

**Definition.** 다중 outstanding 요청에 대해 일부만 성공·실패를 알리는 응답 패킷으로, RDMA-IP 가 retry 정밀도를 높이기 위해 사용한다.

**Source.** Confluence: *Completer* §1.4 (m_sack_info); *An_Out-of-Order_Packet_Processing_Algorithm_of_RoCE_Based_on_Improved_SACK*.

**Related.** completer_frontend, completer_retry, SACK info.

**See also.** [Module 06](06_data_path.md), [Module 11](11_gpuboost_rdma_ip.md)

### MSN (Message Sequence Number)

**Definition.** AETH 에 포함되는 24-bit 카운터로, responder 가 성공적으로 완료한 새 request message 마다 1 증가하며 duplicate 에는 증가시키지 않는다.

**Source.** IB Spec 1.4 §C9-147..149; Confluence: *Details of MSN field*.

**Related.** AETH, ACK coalescing, RDMA READ.

**Example.** WRITE/SEND 다중 패킷의 경우 last 패킷에서 MSN 증가, READ 는 validation 직후 증가 가능.

**See also.** [Module 06](06_data_path.md)

### CNP (RDMA-IP m_notify_cnp_qpn)

**Definition.** RoCEv2 ECN-based CC 에서 receiver 가 송신측에 ECN-CE 마킹을 알리는 단방향 패킷이며, RDMA-IP 의 `m_notify_cnp_qpn` 출력은 이 통지를 발생시킬 QPN 을 congestion control 모듈로 전달한다.

**Source.** Annex A17; Confluence: *Completer* §1.4.

**See also.** [Module 07](07_congestion_error.md)

### MPE (Memory Placement Extensions)

**Definition.** RDMA WRITE 시 receiver 측 cache placement / persistence (FLUSH, RDMA WRITE with partial flush) 를 제어하기 위한 IBTA 확장.

**Source.** IBTA Annex A19 (MPE); Confluence: *Memory Placement Extensions (MPE)* (id=217808945).

**Related.** RDMA Write, FLUSH, ATOMIC WRITE, persistent memory.

**See also.** [Module 05](05_memory_model.md)

### MW (Memory Window)

**Definition.** 기존에 등록된 MR 의 부분 영역을 일시적인 R_Key 와 함께 노출하는 경량 메모리 객체로, MR 재등록 비용 없이 fine-grained access control 을 가능하게 한다.

**Source.** IB Spec §11.5; Confluence: *Memory Window (feat. DH)* (id=155812337).

**Related.** MR, ibv_alloc_mw, ibv_bind_mw, Local/Remote Invalidation.

**See also.** [Module 05](05_memory_model.md)

### Local/Remote Invalidation

**Definition.** R_Key 또는 MW 의 유효성을 즉시 무효화시키는 RDMA 동작으로, Local Invalidate 는 SQ 의 verb, Remote Invalidate 는 SEND_WITH_INVALIDATE 패킷이 트리거한다.

**Source.** IB Spec §11.5.6; Confluence: *Local/Remote Invalidation* (id=155844886).

**See also.** [Module 04](04_service_types_qp.md), [Module 05](05_memory_model.md)

### APM (Automatic Path Migration)

**Definition.** 한 QP 에 alternate path 정보를 미리 등록해두고 primary path 장애 시 hardware 가 자동으로 alternate path 로 전환하는 IB 기능.

**Source.** IB Spec §17.2.8; Confluence: *Automatic Path Migration* (id=151552238).

**See also.** [Module 04](04_service_types_qp.md)

### CCMAD

**Definition.** Congestion Control Management Datagram. CC 파라미터를 SM(Subnet Manager)·노드 간 교환하기 위한 IB MAD 클래스.

**Source.** IB Spec §13.6.4; Confluence: *CCMAD Protocol* (id=290127949).

**See also.** [Module 07](07_congestion_error.md)

### ECE (Enhanced Connection Establishment)

**Definition.** RDMA-CM 핸드셰이크에서 양 단이 지원하는 확장 기능(예: MPE, AETH variant) 을 협상하는 메커니즘.

**Source.** Confluence: *ECE (Enhanced Connection Establishment)* (id=265552106).

**Related.** RDMA-CM, REQ/REP private data.

**See also.** [Module 03](03_rocev2.md), [Module 04](04_service_types_qp.md)

---

## Appendix B. Ultraethernet (UEC) 용어

!!! note "Internal (Confluence: Ultraethernet)"
    이 절은 UEC v1 spec 와 사내 *Ultraethernet* 페이지의 발췌 정의입니다. UEC 용어는 IB / RoCEv2 와 다른 용어계를 사용하므로 매칭 표를 함께 둡니다.

### UEC (Ultra Ethernet Consortium)

**Definition.** Lossy Ethernet 위에서 RDMA · MPI · NCCL 워크로드를 효율적으로 운반하기 위한 차세대 transport spec 을 제정하는 산업 컨소시엄.

**Source.** UEC Specification v1; Confluence: *Ultraethernet* (id=162726259).

**Related.** RoCEv2, lossless 가정 제거, in-network selective retransmission.

**See also.** [Module 10](10_ultraethernet.md)

### PDS (Packet Delivery Sublayer)

**Definition.** UEC transport 의 하위 계층으로, packet ordering / reliability / multipath 분배를 담당한다.

**Source.** UEC v1 §3; Confluence: *Packet Delivery Sublayer* (id=198378057).

**Related.** PDC, PSN handling, multipath.

**See also.** [Module 10](10_ultraethernet.md)

### PDC (Packet Delivery Context)

**Definition.** 두 endpoint 사이에 존재하는 PDS-level 의 connection-like 객체로, PSN 공간·재전송 상태·flow control 상태를 보유한다.

**Source.** UEC v1 §3.2; Confluence: *PSN handling in UEC* (id=201163262).

**See also.** [Module 10](10_ultraethernet.md)

### Semantic Sublayer (UEC)

**Definition.** PDS 위에서 RDMA / MPI / Collective 의 메시지 시맨틱을 정의하는 UEC 계층.

**Source.** UEC v1 §4; Confluence: *Semantic Sublayer* (id=200179723).

**Related.** RDMA verbs, MPI, NCCL.

**See also.** [Module 10](10_ultraethernet.md)

### FEP / IEP (UEC)

**Definition.** Fabric End Point / Inner End Point. UEC 노드의 end-to-end 식별자로, IB 의 GID 와 유사한 역할을 한다.

**Source.** UEC v1 *Background: Terminology*; Confluence: id=200179752.

**See also.** [Module 10](10_ultraethernet.md)

---

## Appendix C. Industry / Research CC 용어

!!! note "Internal (Confluence: Congestion Control 하위)"

### HPCC

**Definition.** In-network telemetry (INT) 를 활용해 link load 를 직접 측정하고 송신율을 갱신하는 CC 알고리즘.

**Source.** Li et al., "HPCC: High Precision Congestion Control", SIGCOMM 2019; Confluence: *HPCC* (id=80216498).

**See also.** [Module 07](07_congestion_error.md)

### CORN

**Definition.** Cloud-Optimized RDMA Networking. 멀티-테넌트 클라우드 환경에서 RDMA 의 fairness 와 isolation 을 강화하기 위한 CC + scheduling 프레임워크.

**Source.** Confluence: *CORN: Cloud-Optimized RDMA Networking* (id=204865845).

**See also.** [Module 07](07_congestion_error.md)

### RTTCC / ZTR (Zero-touch RoCE)

**Definition.** RTT 측정만으로 송신율을 갱신해 PFC 비활성 환경에서도 RoCE 를 안정 운용하는 CC 방식 (Microsoft Azure).

**Source.** Gangidi et al., "Empowering Azure Storage with RDMA"; Confluence: *Zero-touch RoCE and RTTCC* (id=255132439).

**See also.** [Module 07](07_congestion_error.md)

### Falcon

**Definition.** Google 의 hardware-offloaded reliable transport for RDMA. PSP, swift CC, multipath 를 hardware 로 통합한다.

**Source.** Confluence: *Falcon specification* (id=52953427).

**See also.** [Module 07](07_congestion_error.md), [Module 13](13_background_research.md)

### Swift / Programmable CC

**Definition.** Google · Microsoft 의 송신측 CC 알고리즘으로, RTT/ECN 신호를 hardware 또는 firmware 에서 실시간 평가해 송신율을 결정한다.

**Source.** Confluence: *Google's CC* (id=82608297); *Programmable CC* (id=75759859).

**See also.** [Module 07](07_congestion_error.md)

### CX SR-IOV / RCCL / FIO

**Definition.** Mellanox ConnectX SR-IOV (가상 함수 분배), AMD RCCL (collective comms library), FIO (block I/O 벤치). 검증·튜닝에서 자주 언급되는 호스트측 도구·드라이버.

**Source.** Confluence: *CX SR-IOV QoS Functionality Test*; *How to run RCCL*; *How to run fio*.

**See also.** [Module 12](12_fpga_proto_manuals.md)

### MI325X

**Definition.** AMD Instinct MI325X GPU. 사내 RDMA-TB 가 RCCL 검증의 host 환경으로 사용하는 GPU 플랫폼.

**Source.** Confluence: *SKRP/rccl-tests on MI325X nodes*; *MI325X mapping bdf and physical pcie slots*.

**See also.** [Module 12](12_fpga_proto_manuals.md)


---

## 추가 항목 (Phase 2 검수 완료)

### CQE (Completion Queue Entry)

**Definition.** RDMA operation 완료 시 NIC 가 CQ 에 enqueue 하는 64-byte (또는 vendor 정의 크기) 항목으로, opcode·status·byte_len·QP·WR_ID 등 완료 정보를 담는다.

**Source.** IB Spec 1.7, §11.4.2.

**Related.** CQ, WC, ibv_poll_cq, Error CQE.

**Example.** opcode=IBV_WC_RDMA_WRITE, status=IBV_WC_SUCCESS, qp_num=0x12, wr_id=0xdead.

**See also.** [Module 06](06_data_path.md)

### RTR (Ready To Receive)

**Definition.** Reliable QP state 머신의 한 상태로, INIT → RTR 천이 후 receive WR 를 게시할 수 있고 incoming PSN 이 설정된다.

**Source.** IB Spec 1.7, §10.3 (QP State Machine).

**Related.** INIT, RTS, ibv_modify_qp, dest_qp_num.

**See also.** [Module 04](04_service_types_qp.md)

### RTS (Ready To Send)

**Definition.** RTR → RTS 천이 후 비로소 send WR 를 처리할 수 있는 QP 의 활성 상태.

**Source.** IB Spec 1.7, §10.3.

**Related.** RTR, sq_psn, max_rd_atomic.

**See also.** [Module 04](04_service_types_qp.md)

### DSCP (Differentiated Services Code Point)

**Definition.** IPv4 ToS / IPv6 Traffic Class 필드 상위 6 비트로, RoCEv2 에서 PFC priority / ECN 정책의 라우팅 키로 사용된다.

**Source.** RFC 2474; IBTA Annex A17.

**Related.** ECN, PFC, Traffic Class, priority queue.

**See also.** [Module 03](03_rocev2.md), [Module 07](07_congestion_error.md)

### NRT (Non-RDMA Traffic)

**Definition.** RDMA QP 가 아닌 일반 TCP/IP 트래픽으로, 본 강의에서는 RDMA 검증 시 격리/우회 대상으로 다룬다.

**Source.** 강의 컨벤션.

**Related.** RDMA Traffic, PFC, lossless lane.

**See also.** [Module 01](01_rdma_motivation.md)

### SRQ (Shared Receive Queue)

**Definition.** 다수 QP 가 공유하는 단일 receive queue 로, RC 외 service type 에서도 receive WR 의 fan-in 을 줄이는 데 사용한다.

**Source.** IB Spec 1.7, §10.2.9.

**Related.** RQ, ibv_create_srq, srq_limit.

**See also.** [Module 04](04_service_types_qp.md)

### IMM (Immediate Data)

**Definition.** SEND_WITH_IMM / RDMA_WRITE_WITH_IMM operation 에서 페이로드와 별도로 receiver CQE 에 노출되는 32-bit 사용자 메타데이터.

**Source.** IB Spec 1.7, §9.4.2.

**Related.** SEND_WITH_IMM, RDMA_WRITE_WITH_IMM, ImmDt.

**See also.** [Module 06](06_data_path.md)

### ODP (On-Demand Paging)

**Definition.** MR 의 가상 주소 영역을 사전 pin 없이 페이지 폴트 시점에 NIC 가 OS 와 협업해 매핑하는 메모리 관리 방식.

**Source.** Mellanox/NVIDIA RDMA programming guide; IB Spec extension.

**Related.** MR, mlx5_ib_advise_mr, page fault.

**See also.** [Module 05](05_memory_model.md)

### RDMA Opcodes (READ / WRITE / SEND / RECV)

**Definition.** RDMA RC service 의 4가지 핵심 operation 으로, READ 는 원격 메모리에서 가져오기, WRITE 는 원격 메모리에 쓰기, SEND 는 원격 RQ 에 메시지 enqueue, RECV 는 RQ slot 게시이며 multi-packet 시 FIRST/MIDDLE/LAST/ONLY 변형을 갖는다.

**Source.** IB Spec 1.7, §9.4 (RC Operations).

**Related.** OpCode, BTH, RC, WR, multi-packet.

**Example.** RC RDMA_WRITE_FIRST → MIDDLE → LAST 의 PSN 연속, AckReq 는 LAST 에서 set.

**See also.** [Module 06](06_data_path.md)

### DLID (Destination Local ID)

**Definition.** IB Link Layer 의 16-bit destination identifier 로, IB subnet 내 endpoint 라우팅에 사용된다.

**Source.** IB Spec 1.7, §17 (Subnet Management) — LID assignment.

**Related.** SLID, LID, GID, GRH.

**See also.** [Module 02](02_ib_protocol_stack.md)


