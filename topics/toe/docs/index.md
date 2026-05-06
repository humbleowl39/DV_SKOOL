# TCP Offload Engine (TOE) — 개요 및 컨셉 맵

## 학습 플랜
- **레벨**: Intermediate (TOE 검증 환경 Follow 경험 기반, 체계적 정리)
- **목표**: TOE의 존재 이유, 내부 아키텍처, 검증 포인트를 논리적으로 설명할 수 있는 수준

## 핵심 용어집 (Glossary)

### TCP/IP 기본

| 약어 | 풀네임 | 설명 |
|------|--------|------|
| **TCP** | Transmission Control Protocol | 신뢰성 있는 연결 기반 전송 프로토콜 (순서 보장, 재전송) |
| **IP** | Internet Protocol | 패킷 기반 네트워크 계층 프로토콜 |
| **MSS** | Maximum Segment Size | 한 TCP 세그먼트의 최대 데이터 크기 (보통 1460B) |
| **MTU** | Maximum Transmission Unit | 네트워크 프레임 최대 크기 (보통 1500B) |
| **Seq** | Sequence Number | TCP 바이트 순서 추적 번호 |
| **ACK** | Acknowledgment | 수신 확인 응답 |
| **CWND** | Congestion Window | 혼잡 제어를 위한 전송 윈도우 크기 |
| **RTT** | Round Trip Time | 왕복 시간 (송신→수신→응답) |
| **RTO** | Retransmission Timeout | 재전송 타이머 만료 시간 |

### TOE 아키텍처

| 약어 | 풀네임 | 설명 |
|------|--------|------|
| **TOE** | TCP/IP Offload Engine | CPU의 TCP/IP 처리를 HW로 오프로드하는 엔진 |
| **Offload** | — | CPU 작업을 전용 HW로 이전하여 CPU 부하 감소 |
| **FSM** | Finite State Machine | TCP 상태 머신 (11개 상태: LISTEN→ESTABLISHED→CLOSE 등) |
| **CAM** | Content Addressable Memory | 키 기반 병렬 매칭 검색 메모리 |
| **Connection Table** | — | 활성 TCP 연결 상태를 저장하는 테이블 (5-tuple 기반) |
| **Timer Wheel** | Hashed Timing Wheel | 수백만 타이머를 O(1)로 관리하는 자료구조 |

### 핵심 기능

| 약어 | 풀네임 | 설명 |
|------|--------|------|
| **Checksum** | — | 패킷 무결성 검증 (TCP/IP 헤더 + 데이터) |
| **Segmentation** | — | 대용량 데이터를 MSS 단위로 분할 |
| **Reassembly** | — | 수신 세그먼트를 원래 순서대로 재조합 |
| **OOO** | Out-of-Order | 순서 벗어난 세그먼트 수신 (재정렬 필요) |
| **TSO** | TCP Segmentation Offload | Segmentation만 HW로 오프로드 (부분 기능) |
| **Backpressure** | — | 수신 측이 처리 불가 시 송신을 제어하는 메커니즘 |

### 관련 기술

| 약어 | 풀네임 | 설명 |
|------|--------|------|
| **DCMAC** | Dual Channel MAC | AMD 100/200/400GbE MAC (TOE의 하위 계층) |
| **AXI-S** | AXI-Stream | TOE↔DCMAC 간 스트리밍 인터페이스 |
| **DMA** | Direct Memory Access | CPU 개입 없이 메모리 직접 접근 |
| **NIC** | Network Interface Card | 네트워크 인터페이스 카드 |
| **RDMA** | Remote Direct Memory Access | TCP 우회 직접 메모리 접근 (별도 기술) |
| **DPDK** | Data Plane Development Kit | 커널 우회 고성능 SW 패킷 처리 |

---

## 컨셉 맵

```
        +-------------------+
        |  Application      |
        |  (User Space)     |
        +--------+----------+
                 |
    기존: CPU가 전부 처리    TOE: HW가 TCP/IP 처리
                 |                    |
        +--------+----------+  +-----+--------+
        | TCP/IP Stack      |  | TOE Engine   |
        | (Kernel, SW)      |  | (HW Offload) |
        |                   |  |              |
        | - Segmentation    |  | - Checksum   |
        | - Retransmission  |  | - Segment    |
        | - Flow Control    |  | - Retx       |
        | - Checksum        |  | - Flow Ctrl  |
        +--------+----------+  +-----+--------+
                 |                    |
        +--------+--------------------+--------+
        |              NIC / MAC                |
        |         (Ethernet Frame)              |
        +---------------------------------------+
```

## 학습 단위 (Units)

| # | 단위 | 핵심 질문 |
|---|------|----------|
| 1 | **TCP/IP 기본 + TOE 개념** | TCP/IP 스택에서 병목이 어디이고, TOE가 왜 필요한가? |
| 2 | **TOE 아키텍처** | HW로 무엇을 Offload하고, SW와 어떻게 분리하는가? |
| 3 | **TOE 핵심 기능 상세** | Checksum, Segmentation, Retransmission, Flow Control이 HW에서 어떻게 동작하는가? |
| 4 | **TOE DV 검증 전략** | UVM으로 TOE를 어떻게 검증하고, 어떤 시나리오가 중요한가? |

## 이력서 연결 포인트

| 이력서 항목 | 관련 Unit | 면접 시 활용 |
|------------|----------|-------------|
| TOE 검증 환경 시나리오 추가 | Unit 4 | 새로운 테스트 시나리오 설계 근거 |
| Functional Coverage 확장 | Unit 4 | Coverage Model 설계 전략 |
| DCMAC 서브시스템 연동 | Unit 2 | Ethernet MAC ↔ TOE 인터페이스 |
| 100Gbps 서버급 가속기 | Unit 1 | 왜 TOE가 필수인지 성능 관점 |
