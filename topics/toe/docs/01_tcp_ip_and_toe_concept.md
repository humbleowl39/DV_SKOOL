# Module 01 — TCP/IP & TOE Concept

<!-- DV-SKOOL-CH-CTX:start -->
<div class="chapter-context" data-cat="network">
  <a class="chapter-back" href="../">
    <span class="chapter-back-arrow">←</span>
    <span class="chapter-back-icon">📡</span>
    <span class="chapter-back-text">TOE</span>
  </a>
  <span class="chapter-divider">›</span>
  <span class="chapter-marker">Module 01</span>
</div>
<!-- DV-SKOOL-CH-CTX:end -->

<!-- DV-SKOOL-CH-TOC:start -->
<div class="page-toc">
  <span class="page-toc-label">목차</span>
  <a class="page-toc-link" href="#왜-이-모듈이-중요한가">왜 이 모듈이 중요한가</a>
  <a class="page-toc-link" href="#핵심-개념">핵심 개념</a>
  <a class="page-toc-link" href="#tcpip-4계층-모델">TCP/IP 4계층 모델</a>
  <a class="page-toc-link" href="#tcp-핵심-기능-요약">TCP 핵심 기능 요약</a>
  <a class="page-toc-link" href="#왜-toe가-필요한가">왜 TOE가 필요한가?</a>
  <a class="page-toc-link" href="#toe-vs-다른-offload-기술">TOE vs 다른 Offload 기술</a>
  <a class="page-toc-link" href="#qa">Q&A</a>
  <a class="page-toc-link" href="#확인-퀴즈">확인 퀴즈</a>
  <a class="page-toc-link" href="#핵심-정리">핵심 정리</a>
  <a class="page-toc-link" href="#다음-단계">다음 단계</a>
</div>
<!-- DV-SKOOL-CH-TOC:end -->

!!! objective "학습 목표"
    이 모듈을 마치면:

    - **Trace** TCP/IP 스택 처리 단계와 host CPU의 부하 발생 지점 식별
    - **Distinguish** Partial offload (checksum, segmentation) vs Full offload (state machine 전체) 차이
    - **Quantify** 100GbE에서 TOE 없이 CPU가 처리해야 하는 cycle 수 계산
    - **Identify** TOE의 등장 동기 (HPC, RDMA, hyperscale data center)

!!! info "사전 지식"
    - TCP/IP 스택 (3-way handshake, ACK, sliding window)
    - NIC 동작 일반 원리

## 왜 이 모듈이 중요한가

**100GbE 시대에 host CPU는 TCP/IP만으로 압도**됩니다. TOE는 이를 HW로 옮겨 CPU를 다른 워크로드에 활용 가능하게 함. 검증의 출발점은 어떤 기능을 offload하는가(scope)와 host와의 interface 모델 이해.

!!! tip "💡 이해를 위한 비유"
    **TCP** ≈ **우체국 등기 우편**

    보내는 쪽이 수신 확인(ACK)을 받을 때까지 원본을 보관하고, 답신이 없으면 다시 보낸다(재전송). TOE는 이 등기 처리 과정을 CPU 대신 전용 직원(HW)이 맡아 처리하는 것이다.

## 핵심 개념
**TOE = TCP/IP 프로토콜 처리를 CPU에서 전용 HW로 이전(Offload)하여, CPU 부하를 줄이고 네트워크 처리량을 극대화하는 엔진. 100Gbps+ 서버 환경에서 CPU가 TCP 처리에 압도되는 문제를 해결.**

!!! danger "❓ 흔한 오해"
    **오해**: TOE는 모든 TCP 처리를 HW에서 완전히 처리하므로 CPU는 네트워크와 무관하다.

    **실제**: TOE는 stateful한 데이터 패스(Checksum, Segmentation, 재전송)만 offload한다. 연결 수립/해제 등 control path는 여전히 CPU(SW)가 담당한다.

    **왜 헷갈리는가**: "TCP offload"라는 표현이 TCP 전체를 HW가 처리한다는 인상을 주지만, 실제로는 HW/SW 역할이 Data Path와 Control Path로 분리되어 있다.
---

## TCP/IP 4계층 모델

```
+-------------------------------+
| 4. Application Layer          |  HTTP, FTP, SSH, NVMe-oF
|    (사용자 데이터)             |
+-------------------------------+
| 3. Transport Layer            |  TCP, UDP
|    (신뢰성, 흐름 제어)        |  ← TOE가 Offload하는 영역
+-------------------------------+
| 2. Internet Layer             |  IP, ICMP, ARP
|    (라우팅, 주소)             |  ← 일부 Offload
+-------------------------------+
| 1. Network Access Layer       |  Ethernet (MAC + PHY)
|    (물리 전송)                |  ← NIC/DCMAC이 처리
+-------------------------------+
```

---

## TCP 핵심 기능 요약

### TCP가 하는 일 (UDP와 차이)

| 기능 | TCP | UDP |
|------|-----|-----|
| 연결 | Connection-oriented (3-way handshake) | Connectionless |
| 신뢰성 | 보장 (ACK, 재전송) | 미보장 |
| 순서 보장 | Sequence Number로 보장 | 미보장 |
| 흐름 제어 | Window 기반 | 없음 |
| 혼잡 제어 | Slow Start, Congestion Avoidance | 없음 |
| 오버헤드 | 높음 (헤더 20B+, 상태 관리) | 낮음 (헤더 8B) |

### TCP 연결 수명 주기

```
연결 수립: 3-Way Handshake
  Client → SYN →         Server
  Client ← SYN+ACK ←     Server
  Client → ACK →         Server

데이터 전송:
  Client → DATA(seq=100, len=500) →   Server
  Client ← ACK(ack=600) ←            Server
  ...

연결 해제: 4-Way Handshake (또는 RST)
  Client → FIN →        Server
  Client ← ACK ←        Server
  Client ← FIN ←        Server
  Client → ACK →        Server
```

### TCP 헤더 구조

```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|          Source Port          |       Destination Port        |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                        Sequence Number                        |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                    Acknowledgment Number                      |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
| Offset| Rsv |N|C|E|U|A|P|R|S|F|         Window Size          |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|           Checksum            |       Urgent Pointer          |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                    Options (가변)                             |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

핵심 필드:
  Sequence Number: 바이트 단위 전송 위치 (순서 보장)
  ACK Number:      다음으로 기대하는 바이트 번호
  Window Size:     수신 버퍼 여유 공간 (흐름 제어)
  Flags:           SYN/ACK/FIN/RST/PSH (연결 상태 관리)
  Checksum:        헤더 + 데이터 무결성 검증
```

---

## 왜 TOE가 필요한가?

### CPU에서 TCP 처리 시 병목

```
100Gbps 네트워크에서 CPU TCP 처리:

  64B 패킷 기준: ~150M packets/sec
  각 패킷마다 CPU가:
    1. Checksum 계산/검증
    2. Sequence Number 관리
    3. ACK 생성/처리
    4. Window 크기 관리
    5. 재전송 타이머 관리
    6. 메모리 복사 (커널 → 유저 공간)

  결과:
    CPU 코어 여러 개가 TCP 처리에 100% 점유
    → 애플리케이션 처리 능력 없음
    → CPU가 "네트워크 프로세서"로 전락
```

### TOE의 효과

```
TOE 있을 때:

  NIC → TOE HW:
    - Checksum 계산/검증 (HW, 1 cycle)
    - TCP Segmentation (HW)
    - ACK 생성 (HW)
    - 재전송 관리 (HW)
    - 흐름 제어 (HW)

  CPU:
    - 연결 수립/해제만 관여 (Control Path)
    - 데이터 전달만 수행 (Data Path은 DMA)
    - → CPU 부하 80-90% 감소
    - → 애플리케이션에 CPU 할당 가능
```

### 성능 비교

| 항목 | SW TCP (CPU) | TOE (HW) |
|------|-------------|----------|
| Throughput | ~40Gbps (CPU 한계) | 100Gbps+ (라인 레이트) |
| Latency | ~10-50 μs (커널 경유) | ~1-5 μs (HW 직접) |
| CPU 사용률 | 80-100% (TCP 처리) | ~10% (제어만) |
| 연결 수 | 수만 (메모리/CPU 한계) | 수백만 (HW 상태 테이블) |
| 전력 | 높음 (CPU 풀로드) | 낮음 (전용 HW 효율) |

---

## TOE vs 다른 Offload 기술

| 기술 | Offload 범위 | 복잡도 | 성능 | 사용 사례 |
|------|-------------|--------|------|----------|
| **Checksum Offload** | Checksum만 | 낮음 | 약간 향상 | 거의 모든 NIC |
| **TSO/LSO** | TCP Segmentation만 | 중간 | 중간 향상 | 대부분의 NIC |
| **TOE** | TCP/IP 전체 | 높음 | 대폭 향상 | 서버, 가속기, 스토리지 |
| **RDMA** | TCP 우회 (직접 메모리 접근) | 매우 높음 | 최고 | HPC, 저지연 |
| **DPDK** | 커널 우회 (유저스페이스) | 높음 | 높음 | NFV, 라우터 |

```
Offload 수준:

  Checksum Offload ⊂ TSO ⊂ TOE
  (부분)            (중간)  (전체)

  RDMA: TCP 자체를 우회 → 다른 범주
  DPDK: SW이지만 커널을 우회 → Offload라기보다 최적화
```

---

## Q&A

**Q: TOE가 왜 필요한가?**
> "100Gbps 네트워크에서 CPU가 TCP/IP 프로토콜을 처리하면 코어 여러 개가 100% 점유되어 애플리케이션에 CPU를 할당할 수 없다. TOE는 Checksum, Segmentation, 재전송, 흐름 제어를 전용 HW로 Offload하여 CPU 부하를 80-90% 줄이고, 라인 레이트 처리량과 마이크로초 단위 지연을 달성한다."

**Q: TOE와 TSO/Checksum Offload의 차이는?**
> "Offload 범위의 차이다. Checksum Offload는 체크섬 계산만, TSO는 여기에 TCP Segmentation을 추가한다. TOE는 TCP/IP 전체 스택(연결 관리, 재전송, 흐름 제어까지)을 HW로 Offload한다. TSO는 대부분의 NIC에 이미 있지만 TOE는 전용 가속기가 필요하다."

**Q: TOE의 단점은?**
> "세 가지: (1) HW 복잡도 — TCP 상태 머신 전체를 HW로 구현해야 하므로 설계/검증 비용이 높다. (2) 유연성 — 프로토콜 변경 시 HW 수정이 필요(SW 스택은 패치로 해결). (3) 디버그 난이도 — HW 내부 TCP 상태를 관찰하기 어려움. 그러나 100Gbps+ 서버 가속기에서는 성능 이점이 이 단점을 압도한다."

---

## 확인 퀴즈

**Q1.** 100Gbps 네트워크에서 64B 패킷 기준 초당 약 몇 개의 패킷을 처리해야 하는가? 그리고 이것이 CPU에 어떤 문제를 일으키는가?

<details>
<summary>정답</summary>

약 **1억 5천만(~150M) packets/sec**. 각 패킷마다 Checksum, Seq 관리, ACK 처리, Window 관리, 재전송 타이머 등을 CPU가 수행하면 코어 여러 개가 100% 점유되어 애플리케이션에 CPU를 할당할 수 없다. CPU가 사실상 "네트워크 프로세서"로 전락하는 문제.
</details>

**Q2.** TCP와 UDP의 가장 근본적인 차이를 한 문장으로 설명하고, TOE가 TCP만 Offload하는 이유를 서술하라.

<details>
<summary>정답</summary>

TCP는 연결 지향(Connection-oriented)으로 신뢰성(ACK, 재전송, 순서 보장)을 제공하고, UDP는 비연결(Connectionless)으로 이를 제공하지 않는다. UDP는 헤더 8B에 상태 관리가 없어 CPU 부하가 작으므로 Offload 필요성이 낮다. 반면 TCP는 상태 머신, 재전송, 흐름/혼잡 제어 등 패킷마다 반복적 연산이 필요하여 HW Offload 효과가 크다.
</details>

**Q3.** TSO(TCP Segmentation Offload)와 TOE의 차이를 Offload 범위 관점에서 비교하라. TSO만으로 부족한 이유는?

<details>
<summary>정답</summary>

TSO는 Segmentation(대용량 데이터를 MSS 단위로 분할 + 헤더 생성)만 Offload한다. TOE는 Segmentation에 더해 Checksum, 재전송, 흐름 제어, 혼잡 제어, 연결 관리까지 TCP/IP 전체를 Offload한다. TSO만으로는 재전송 타이머 관리, 연결별 Window 추적, Congestion Control 등 나머지 반복 작업이 여전히 CPU에 남아 100Gbps에서 병목이 해결되지 않는다.
</details>

**Q4. (사고력)** RDMA는 TCP 자체를 우회하여 직접 메모리에 접근한다. 그렇다면 RDMA가 있는데도 TOE가 여전히 필요한 사용 사례는 무엇인가?

<details>
<summary>정답</summary>

RDMA는 양쪽 모두 RDMA NIC + 전용 SW 스택이 필요하고, 기존 TCP 기반 애플리케이션(HTTP, NVMe-oF over TCP, 일반 소켓 앱 등)과 호환되지 않는다. 또한 RDMA는 보통 손실 없는(lossless) 네트워크를 전제한다. 반면 TOE는 기존 TCP 소켓 API와 호환되면서 성능을 높이므로, 레거시 애플리케이션 호환이 필요하거나 일반 인터넷/데이터센터 환경(손실 가능)에서 사용된다.
</details>

---
!!! warning "실무 주의점 — Partial Checksum Offload와 부분 헤더 처리 오류"
    **현상**: RX 체크섬 오프로드를 활성화했을 때 특정 패킷에서만 IP/TCP 체크섬 오류가 보고되며, 동일 패킷을 SW 스택으로 처리하면 정상이다.
    
    **원인**: Partial offload는 IP/TCP 헤더가 단일 DMA 버퍼에 연속으로 존재한다고 가정한다. IP 옵션 필드가 있거나 TCP 헤더가 세그먼트 경계에 걸리면 HW가 헤더 끝 위치를 잘못 계산하여 체크섬 오류를 발생시킨다.
    
    **점검 포인트**: TB에서 IP Options(IHL>5) 패킷과 TCP Options(Data Offset>5) 패킷을 별도 시나리오로 구성. `csum_start`와 `csum_offset` 디스크립터 필드가 옵션 길이에 따라 정확히 갱신되는지 DMA 디스크립터 덤프에서 확인.

## 핵심 정리

- **TOE = TCP/IP HW offload**. Host CPU 부하 ↓ + throughput ↑.
- **Partial offload**: checksum, TSO/LRO (segment offload), simple cases. 일반 NIC도 지원.
- **Full offload**: connection state machine 전체 HW. RDMA / iWARP 등 특수 NIC.
- **동기**: 100GbE에서 packet rate가 1.5M pps/Gbps → CPU cycle/packet 한도 초과.
- **활용**: HPC, hyperscale (AWS Nitro, Azure SmartNIC), storage networks.

## 다음 단계

- 📝 [**Module 01 퀴즈**](quiz/01_tcp_ip_and_toe_concept_quiz.md)
- ➡️ [**Module 02 — TOE Architecture**](02_toe_architecture.md)

<div class="chapter-nav">
  <a class="nav-prev" href="../">
    <div class="nav-label">◀ 이전</div>
    <div class="nav-title">코스 홈</div>
  </a>
  <a class="nav-next" href="../02_toe_architecture/">
    <div class="nav-label">다음 ▶</div>
    <div class="nav-title">TOE 아키텍처</div>
  </a>
</div>
