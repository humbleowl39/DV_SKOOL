# TOE 용어집

핵심 용어 ISO 11179 형식 정의.

---

## A — ARP

### ARP (Address Resolution Protocol)

**Definition.** IP 주소를 MAC 주소로 매핑하는 L2/L3 사이의 protocol로, NIC가 frame을 보내기 전에 next-hop MAC을 알아내기 위해 사용.

**Source.** RFC 826.

**Related.** ARP cache, ARP request/reply.

---

## C — Connection Table / Checksum Offload

### Connection Table

**Definition.** TOE에서 활성 TCP 연결의 4-tuple (src/dst IP+port)과 state를 저장하는 HW 자료구조.

**Source.** TOE design literature.

**Related.** 4-tuple, hash, state machine.

**See also.** [Module 02](02_toe_architecture.md)

### Checksum Offload

**Definition.** IP/TCP/UDP 헤더의 checksum 계산을 HW가 수행하여 CPU 부하를 줄이는 partial offload 기법.

**Source.** NIC standard features.

**Related.** TX checksum, RX checksum verification.

**See also.** [Module 03](03_toe_key_functions.md)

---

## L — LRO

### LRO (Large Receive Offload)

**Definition.** HW가 같은 connection의 연속된 RX segment들을 합쳐 SW에 한 번에 전달하는 기법.

**Source.** Linux kernel networking.

**Related.** TSO, GRO (Generic Receive Offload).

**See also.** [Module 03](03_toe_key_functions.md)

---

## R — RSS / RTO

### RSS (Receive Side Scaling)

**Definition.** Incoming flow를 multiple queue로 분산해 multi-core CPU의 병렬 처리를 가능하게 하는 NIC 기법.

**Source.** Microsoft Network Driver Interface Specification.

**Related.** 5-tuple hash, indirection table.

**See also.** [Module 03](03_toe_key_functions.md)

### RTO (Retransmission Timeout)

**Definition.** Segment 송신 후 ACK 미수신 시 재전송까지 대기하는 시간으로, RTT 측정값에 기반해 적응적으로 조정.

**Source.** RFC 793, RFC 6298.

**Related.** RTT, fast retransmit, dup ACK.

**See also.** [Module 03](03_toe_key_functions.md)

---

## T — TSO / TOE / TCP State Machine

### TSO (TCP Segmentation Offload)

**Definition.** 큰 buffer (64KB)를 SW가 보내면 HW가 MTU 단위로 자동 분할하여 segment 생성하는 기법.

**Source.** Linux kernel, NIC standard features.

**Related.** LSO, GSO.

**See also.** [Module 03](03_toe_key_functions.md)

### TOE (TCP/IP Offload Engine)

**Definition.** TCP/IP protocol stack 처리를 host CPU에서 NIC HW로 옮기는 엔진.

**Source.** TOE design literature.

**Related.** Partial offload, full offload, RDMA.

**See also.** [Module 01](01_tcp_ip_and_toe_concept.md)

### TCP State Machine

**Definition.** TCP 연결의 11개 state (CLOSED, LISTEN, SYN_SENT, SYN_RCVD, ESTABLISHED, FIN_WAIT_1/2, CLOSE_WAIT, CLOSING, LAST_ACK, TIME_WAIT)와 transition을 정의하는 RFC 표준 모델.

**Source.** RFC 793.

**See also.** [Module 02](02_toe_architecture.md)

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
