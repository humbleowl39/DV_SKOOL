---
title: "TOE 용어집"
---

핵심 용어 ISO 11179 형식 정의.

---

## A — ARP

### ARP (Address Resolution Protocol)

**Definition.** IP 주소를 MAC 주소로 매핑하는 L2/L3 사이의 protocol로, NIC가 frame을 보내기 전에 next-hop MAC을 알아내기 위해 사용.

**Source.** RFC 826.

**Related.** ARP cache, ARP request/reply, Gratuitous ARP.

**Example.** TOE가 새 TCP connection을 열기 전, 목적지 IP의 MAC을 모르면 ARP request를 브로드캐스트하고 reply를 받아 Connection Table entry에 dst MAC을 채운다.

---

## C — Connection Table / Checksum Offload

### Connection Table

**Definition.** TOE에서 활성 TCP 연결의 4-tuple (src/dst IP+port)과 state를 저장하는 HW 자료구조.

**Source.** TOE design literature.

**Related.** 4-tuple, hash, state machine, ECC, LRU eviction.

**Example.** 1M connection 지원 TOE에서 on-chip SRAM에는 수천 개의 활성 entry만 유지하고 나머지는 off-chip DRAM으로 evict한다. 4-tuple hash miss 시 DRAM에서 fetch해 SRAM에 올린다.

**See also.** [Module 02](../02_toe_architecture/)

### Checksum Offload

**Definition.** IP/TCP/UDP 헤더의 checksum 계산을 HW가 수행하여 CPU 부하를 줄이는 partial offload 기법.

**Source.** NIC standard features.

**Related.** TX checksum, RX checksum verification, partial offload, TSO.

**Example.** TX: SW가 TCP checksum 필드를 0으로 두고 HW에 넘기면 HW가 wire 직전에 올바른 값을 채운다. RX: HW가 검증 결과를 descriptor status flag로 전달하면 SW는 flag만 읽는다.

**See also.** [Module 03](../03_toe_key_functions/)

---

## L — LRO

### LRO (Large Receive Offload)

**Definition.** HW가 같은 connection의 연속된 RX segment들을 합쳐 SW에 한 번에 전달하는 기법.

**Source.** Linux kernel networking.

**Related.** TSO, GRO (Generic Receive Offload).

**See also.** [Module 03](../03_toe_key_functions/)

---

## R — RSS / RTO

### RSS (Receive Side Scaling)

**Definition.** Incoming flow를 multiple queue로 분산해 multi-core CPU의 병렬 처리를 가능하게 하는 NIC 기법.

**Source.** Microsoft Network Driver Interface Specification.

**Related.** 5-tuple hash, indirection table, RPS (Receive Packet Steering).

**Example.** 16-core 서버에서 16개 RX queue를 구성하고 indirection table로 각 queue를 코어에 매핑하면, 서로 다른 5-tuple의 flow가 각 코어에서 독립적으로 처리된다.

**See also.** [Module 03](../03_toe_key_functions/)

### RTO (Retransmission Timeout)

**Definition.** Segment 송신 후 ACK 미수신 시 재전송까지 대기하는 시간으로, RTT 측정값에 기반해 적응적으로 조정.

**Source.** RFC 793, RFC 6298.

**Related.** RTT, SRTT (smoothed RTT), fast retransmit, dup ACK, congestion window.

**Example.** Linux 기본 초기 RTO는 1초이며, RTT 샘플이 쌓이면 Jacobson 알고리즘으로 SRTT와 RTTVAR를 갱신해 RTO = SRTT + 4×RTTVAR 로 계산한다. TOE DV에서는 RTO 발화 시점을 시뮬로 직접 검증하기 위해 RTT를 인위적으로 크게 줄이거나 타이머를 가속한다.

**See also.** [Module 03](../03_toe_key_functions/)

---

## T — TSO / TOE / TCP State Machine

### TSO (TCP Segmentation Offload)

**Definition.** 큰 buffer (64KB)를 SW가 보내면 HW가 MTU 단위로 자동 분할하여 segment 생성하는 기법.

**Source.** Linux kernel, NIC standard features.

**Related.** LSO (Large Send Offload), GSO (Generic Segmentation Offload), MSS, LRO.

**Example.** SW가 64 KB 버퍼를 하나의 descriptor로 넘기면 HW는 MSS=1460 기준으로 ~44개 segment를 생성하고 각각 TCP/IP 헤더를 붙여 wire로 내보낸다. SW 입장에서 send() 한 번이 wire에서는 44개 패킷이 된다.

**See also.** [Module 03](../03_toe_key_functions/)

### TOE (TCP/IP Offload Engine)

**Definition.** TCP/IP protocol stack 처리를 host CPU에서 NIC HW로 옮기는 엔진.

**Source.** TOE design literature.

**Related.** Partial offload, full offload, RDMA, SmartNIC, iWARP.

**Example.** AWS Nitro card는 host CPU의 VPC 네트워킹 처리를 전담하는 TOE로 볼 수 있으며, host CPU는 TCP/IP 처리를 전혀 하지 않고 사용자 워크로드에만 집중한다.

**See also.** [Module 01](../01_tcp_ip_and_toe_concept/)

### TCP State Machine

**Definition.** TCP 연결의 11개 state (CLOSED, LISTEN, SYN_SENT, SYN_RCVD, ESTABLISHED, FIN_WAIT_1/2, CLOSE_WAIT, CLOSING, LAST_ACK, TIME_WAIT)와 transition을 정의하는 RFC 표준 모델.

**Source.** RFC 793.

**Related.** state coverage, active/passive open, TIME_WAIT, 4-way close.

**Example.** DV에서 CLOSING state는 simultaneous close(양쪽이 동시에 FIN 전송) 시나리오에서만 진입하므로, 이 state 커버리지를 달성하려면 directed sequence로 양단을 동시에 FIN 전송하도록 조율해야 한다.

**See also.** [Module 02](../02_toe_architecture/)

---

## 추가 약어

| 약어 | 풀네임 | 의미 |
|------|--------|------|
| **TCP** | Transmission Control Protocol | 신뢰성 있는 stream protocol |
| **IP** | Internet Protocol | 패킷 라우팅 |
| **UDP** | User Datagram Protocol | 비신뢰 datagram |
| **NIC** | Network Interface Card | 네트워크 인터페이스 |
| **MTU** | Maximum Transmission Unit | 최대 전송 단위 (보통 1500) |
| **MSS** | Maximum Segment Size | TCP segment 최대 (MTU - 40) |
| **RTT** | Round Trip Time | 왕복 시간 |
| **CWND** | Congestion Window | 혼잡 제어 window |
| **RWND** | Receive Window | 수신 window |
| **iWARP** | Internet Wide Area RDMA Protocol | RDMA over TCP |
| **RoCE** | RDMA over Converged Ethernet | RDMA over Ethernet |
