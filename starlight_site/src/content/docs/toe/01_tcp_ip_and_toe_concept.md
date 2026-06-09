---
title: "Module 01 — TCP/IP & TOE Concept"
---

:::tip[학습 목표]
이 모듈을 마치면:

- **Trace** TCP/IP 스택 처리 단계와 host CPU 의 부하 발생 지점을 단계별로 추적할 수 있다.
- **Distinguish** Partial offload (checksum, segmentation) 와 Full offload (state machine 전체) 의 경계를 구분할 수 있다.
- **Quantify** 100 GbE 라인레이트에서 CPU 가 TCP 처리에 쓰는 cycle/packet 을 어림셈으로 계산할 수 있다.
- **Identify** TOE 의 등장 동기 (HPC, hyperscale data center, AI/storage 가속) 와 한계 영역을 식별한다.
- **Compare** Checksum/TSO/LRO/TOE/RDMA/DPDK 의 offload 범위 차이를 비교한다.
:::
:::note[사전 지식]
- TCP/IP 스택 (3-way handshake, ACK, sliding window, sk_buff)
- NIC 의 일반 동작 원리 (descriptor ring, DMA, IRQ)

처음 보는 약어가 많다면 아래 정의를 먼저 잡고 가세요. **TCP**(Transmission Control Protocol; 데이터를 순서대로·빠짐없이 전달하는 신뢰성 있는 통신 규약), **IP**(Internet Protocol; 패킷을 목적지 주소로 라우팅하는 규약), **NIC**(Network Interface Card; 컴퓨터를 네트워크에 연결하는 하드웨어 카드), **stack**(스택; TCP·IP·이더넷처럼 계층으로 쌓인 통신 프로토콜의 묶음), **packet**(패킷; 네트워크로 전송되는 데이터의 한 덩어리), **DMA**(Direct Memory Access; CPU 를 거치지 않고 장치가 메모리에 직접 데이터를 읽고 쓰는 방식), **IRQ**(Interrupt ReQuest; 장치가 "처리할 일이 생겼다"고 CPU 에 보내는 신호), **descriptor**(디스크립터; "이 메모리 주소의 이만큼을 보내라/받아라"를 적어 HW 에 넘기는 작업 지시서), **descriptor ring**(그 디스크립터들을 원형 큐로 늘어놓아 SW 와 HW 가 주고받는 자료구조), **sk_buff**(리눅스 커널이 패킷 하나를 담아 스택의 각 계층을 통과시키는 버퍼 자료구조).
:::
---

## 1. Why care? — 이 모듈이 왜 필요한가

### 1.1 시나리오 — 100 Gbps 에서 _CPU 코어 다 잃기_

당신의 서버가 100 Gbps NIC 를 달고 있는데, TCP/IP 처리를 전부 SW 에서 한다고 해봅시다. 측정 결과는 냉정합니다 (Mellanox WP, 2014). 100 Gbps 양방향 트래픽을 소화하려면 CPU 코어 4~8 개가 100 % 점유됩니다. 64 코어 서버라면 약 12 % 가 통신 처리에만 잠겨 버리고, 애플리케이션이 쓸 수 있는 코어는 56 개로 줄어듭니다.

이제 hardware offload (TOE) 로 바꿔봅시다. TCP segmentation, checksum, ACK 생성, 재전송 타이머를 모두 NIC HW 가 처리하면 CPU 부담은 ~0.5 코어 (connection 개설·해제 관리) 수준으로 내려가고, 애플리케이션에 돌아오는 코어는 63.5 개가 됩니다.

**5-7 코어 차이** = _수만 USD_ 의 서버 가치. Cloud 운영자는 _수십만 서버 fleet_ → 누적 절감 _수십억 USD_.

이게 TOE 가 _대규모 데이터센터_ 에서 _필수_ 인 이유.

이후 모든 TOE 모듈은 한 가정에서 출발합니다 — **"100 Gbps 라인레이트에서 host CPU 가 TCP/IP 를 처리하면 코어 여러 개가 100 % 점유되어 애플리케이션이 멈춘다"**. 왜 TOE 의 connection table 이 hardware 에 있어야 하는지, 왜 RTO 타이머가 SW timer 가 아니라 HW timer wheel 인지, 왜 DV TB 가 host agent 와 network agent 를 둘 다 두어야 하는지 — 전부 이 한 가정의 파생입니다.

이 모듈을 건너뛰면 이후의 모든 architecture/기능/검증 결정이 "그냥 외워야 하는 규칙" 으로 보입니다. 반대로 이 가정을 정확히 잡고 나면, 디테일을 만날 때마다 **"아, 이게 CPU cycle 을 줄이려는 거구나"** 처럼 _이유_ 가 보입니다.

---

## 2. Intuition — 비유와 한 장 그림

:::tip[💡 한 줄 비유]
**TCP** = 등기 우편. 원본을 보관하다가 ACK 가 안 오면 다시 보낸다.<br>
**CPU SW TCP** = 한 명의 우체부가 모든 등기 봉투의 송장 작성·체크섬·재전송 타이머·창구 응대를 _직접_ 수행 — 처리량이 라인레이트를 못 따라감.<br>
**TOE** = 등기 처리 전용 자동화 라인. 송장 작성·CRC·재전송·창구 응대를 전용 HW 가 처리하고, CPU 는 _연결 개설_ 같은 드문 결정만 한다.
:::
### 한 장 그림 — SW TCP path vs TOE path

```d2
direction: down

SW: "Software TCP — CPU 풀로드" {
  S1: "App"
  S2: "user buf"
  S3: "socket buf\n(sk_buff)"
  S4: "NIC → wire"
  S5: "socket buf"
  S6: "App (rcv)"
  S1 -> S2
  S2 -> S3: "copy · CPU"
  S3 -> S4: "hdr/chksum\nseg/retx · CPU"
  S4 -> S5: "IRQ · CPU"
  S5 -> S6: "reasm/copy · CPU"
}
TOE: "TOE — HW offload" {
  T1: "App"
  T2: "user buf"
  T3: "TOE TX queue"
  T4: "MAC → wire"
  T5: "TOE RX queue"
  T6: "App (rcv)"
  T1 -> T2
  T2 -> T3: "DMA desc"
  T3 -> T4: "HW seg/chksum\nhdr/RTO"
  T4 -> T5: "HW ACK"
  T5 -> T6: "HW reasm\nDMA"
}
SW -> TOE: { style.opacity: 0 }
```

빨간 박스가 SW TCP 에서는 packet 마다 발생하지만, TOE 에서는 모두 **HW pipeline** 안에서 처리됩니다. CPU 는 `connect()` / `accept()` / `close()` 같은 **연결당 1~2 회** 의 control path 만 담당.

### 왜 이렇게 설계됐는가 — Design rationale

100 Gbps 라인레이트에서 64 byte 패킷 도착 간격은 **~5.12 ns**. CPU 한 코어가 packet 하나에 쓸 수 있는 cycle 은 사실상 한 자릿수 — checksum 한 번 못 돌립니다. 즉 **CPU 가 packet 별로 끼는 한 라인레이트를 못 채웁니다**. 그래서 TOE 의 세 축 — **Data path 의 HW offload + Connection state 의 HW 보존 + Control path 의 SW 잔류** — 는 동시에 만족돼야 의미가 있고, 셋 중 하나라도 빠지면 전체가 의미를 잃습니다. 이 세 축이 곧 TOE 의 architecture, 기능 분배, 그리고 검증 환경의 구조를 결정합니다.

---

## 3. 작은 예 — 1 MB HTTP 응답이 TOE 를 거쳐 나가는 여정

가장 단순한 시나리오. 웹 서버가 클라이언트에게 **1 MB HTTP 응답** 을 보냅니다. 연결은 이미 **ESTABLISHED**(데이터를 주고받을 수 있도록 완전히 수립된 TCP 연결 상태) 상태, **MSS**(Maximum Segment Size; TCP 가 한 **segment**(TCP 가 데이터를 잘라 보내는 한 조각)에 실어 보낼 수 있는 payload 의 최대 바이트 수. 여기서 **payload**(페이로드; 헤더를 뺀 실제 전송하려는 데이터 본문)) = 1460 byte 라고 가정.

```d2
shape: sequence_diagram

App: "Server App"
TOE: "TOE Engine"
MAC: "MAC / wire"
Peer: "Client NIC"

# Note over TOE: ② HW Segmentation\n1 MB → 720 seg (MSS=1460)\n③ HW header build (TCP/IP)\n④ HW Checksum\n⑤ Retx buffer + RTO arm
# Note over TOE: ⑦ HW ACK 처리\nretx buffer 해제\n⑧ Window slide\n다음 seg burst
# Note over TOE: ⑨ 모든 byte ACK 완료
App -> TOE: "① descriptor post (1 MB, 단 1회)"
TOE -> MAC: "seg1, seg2, ..., seg720"
MAC -> Peer: "wire"
Peer -> MAC: "⑥ ACK(ack=N×1460)" { style.stroke-dash: 4 }
MAC -> TOE: "ACK" { style.stroke-dash: 4 }
TOE -> App: "descriptor done IRQ\n(write() return)" { style.stroke-dash: 4 }
```

| Step | 누가 | 무엇을 | 의미 |
|---|---|---|---|
| ① | App + driver | `write()` → 1 MB buffer 의 descriptor 1 개를 TOE 에 post | CPU 는 _한 번_ 만 개입. SW TCP 라면 720 회의 segment 처리가 필요 |
| ② | TOE HW | 1 MB → 720 개 segment (MSS = 1460) 로 분할 (TSO 의 full-offload 버전) | CPU 가 segmentation 안 함 — 핵심 cycle 절감 |
| ③ | TOE HW | segment 마다 TCP header (seq, ack, window, flags) 와 IP header (src, dst, length, ttl) 채움. 여기서 **header**(헤더; payload 앞에 붙어 출발지·목적지·순서 등 제어 정보를 담는 부분), **seq**(sequence number, 이 데이터가 stream 의 몇 번째 바이트부터인지), **ack**(acknowledgment number, 수신측이 "여기까지 잘 받았으니 다음은 이 번호부터"라고 알리는 값) | Connection table 에서 **4-tuple**(src IP, dst IP, src port, dst port 네 값 — TCP 연결 하나를 유일하게 식별하는 열쇠) lookup → 상태 가져옴 |
| ④ | TOE HW | TCP **checksum**(헤더+데이터를 더해 만든 무결성 검사값 — 전송 중 비트가 깨졌는지 검출) 계산: **pseudo header**(src/dst IP 등 IP 계층 정보를 임시로 끌어와 checksum 계산에만 쓰는 가상 헤더) + payload, IP checksum 계산해 헤더에 삽입 | pipeline 으로 1 cycle/word — 1500 B ≈ 94 cycle |
| ⑤ | TOE HW | **retransmission buffer**(보낸 segment 의 사본을 ACK 받을 때까지 보관하는 버퍼) 에 사본 보관 + 연결별 **RTO**(Retransmission Timeout; ACK 가 이 시간 안에 안 오면 재전송) 타이머 arm | ACK 가 안 오면 자동 재전송 |
| ⑥ | Peer NIC | ACK packet 송신 (**cumulative ACK**(개별 segment 가 아니라 "여기까지 연속으로 다 받았다"는 누적 확인 방식), 일정 간격) | 보통 두 segment 마다 1 ACK |
| ⑦ | TOE HW | RX path 에서 ACK 수신 → connection table 의 send_unacked (보냈지만 아직 ACK 못 받은 바이트 경계) 갱신 → retx buffer 해당 영역 해제 | 모두 HW 가 처리 |
| ⑧ | TOE HW | window slide (확인된 만큼 전송 가능 구간을 앞으로 미는 sliding window 동작) → 다음 burst 의 segment 송신 (**cwnd**(congestion window; 네트워크 혼잡을 피하려 한 번에 보낼 수 있게 허용된 양) × MSS 만큼) | Congestion control 도 HW 가 직접 |
| ⑨ | TOE HW | 마지막 byte ACK 도착 → descriptor 완료 IRQ 또는 polling completion | App 의 `write()` 가 return |

```c
// Step ① 의 SW 측 코드. 이 한 줄이 ②~⑨ 를 트리거.
ssize_t n = write(socket_fd, buf, 1024 * 1024);   // 1 MB
// SW TCP 라면 같은 write() 가 내부에서 720 회 segment 처리.
// TOE 라면 descriptor 1 개 post → HW 가 720 segment 자동 처리.
```

:::note[여기서 잡아야 할 두 가지]
**(1) CPU 개입 횟수의 비대칭** — SW TCP 는 packet 마다 (수백~수천 cycle), TOE 는 1 MB 당 1~2 회 (descriptor post + completion). 이게 TOE 의 본질. <br>
**(2) Connection state 가 HW 안에 있다** — Step ③ 의 header build 가 가능하려면 seq/ack/window/cwnd 가 HW 가 즉시 읽을 수 있는 곳에 있어야 함. 이게 다음 모듈의 Connection Table 이야기로 이어집니다.
:::
---

## 4. 일반화 — Offload 의 스펙트럼과 TOE 의 범위

### 4.1 Offload 의 4 단계 — 어디까지 HW 가 가져가나

| 단계 | Offload 항목 | 남는 SW 부담 | HW 복잡도 |
|---|---|---|---|
| **Stateless** | Checksum (IP/TCP/UDP) | Segmentation, retx, window, FSM 모두 SW | 낮음 |
| **Segment** | + TSO (TX), LRO (RX) | retx, window, FSM 은 여전히 SW | 중간 |
| **Stateful (TOE)** | + Connection state, retx, RTO, flow/cong control | 연결 setup/teardown 만 SW | 높음 |
| **Bypass (RDMA)** | TCP 자체를 우회, user-space 가 NIC 에 직접 명령 | TCP API 호환 안 됨 | 매우 높음 |

핵심: **TOE 는 "stateful offload"** — 연결 상태가 HW 에 있다는 점에서 TSO/LRO 와 본질적으로 다름.

:::note[메커니즘 — LRO (수신측 coalescing) 가 receive overhead 를 줄이는 방식]
TSO 가 송신측에서 큰 buffer 를 _쪼개는_ 것이라면, **LRO (Large Receive Offload)** 는 수신측에서 그 반대로 _합칩니다_. 100 Gbps 에서는 MSS 크기의 작은 segment 가 초당 수백만 개씩 도착하는데, 도착할 때마다 CPU 를 깨워 stack 을 한 번씩 통과시키면 per-packet overhead (인터럽트·헤더 파싱·소켓 큐 삽입) 가 누적돼 CPU 가 녹습니다. LRO 는 NIC HW 가 **같은 flow (같은 4-tuple) 에 속하고 sequence 가 연속인 여러 RX segment 를 _도착하는 즉시_ 하나의 큰 buffer 로 이어 붙입니다** — payload 를 연속으로 쌓고, 헤더는 대표 하나로 합치며(길이/ack 갱신), 그렇게 모은 _하나의 큰 chunk_ 를 SW 스택에 **1회만** 올립니다. 결과적으로 "N 개 segment → N 번 처리" 가 "N 개 segment → 1 번 처리" 로 줄어, _per-packet 고정비용_ 이 N 분의 1 로 떨어집니다. 이것이 수신 경로 CPU overhead 감소의 메커니즘이며, TOE 는 여기에 더해 ACK 생성·재전송 추적까지 HW 가 가져갑니다. (단, segment 를 합치므로 _패킷 경계 정보_ 가 사라져 일부 라우팅/방화벽 시나리오에서는 LRO 를 끄기도 합니다.)
:::

### 4.2 데이터 패스 vs 컨트롤 패스 — 분리의 원칙

```d2
direction: right

DP: "Data Path (HW) — 높은 빈도, ns~µs latency" {
  direction: down
  D1: "Checksum"
  D2: "Segmentation"
  D3: "Header build"
  D4: "ACK process"
  D5: "RTO retransmit"
  D6: "Window slide"
  D7: "Cong control update"
}
CP: "Control Path (SW) — 낮은 빈도, ms 단위 허용" {
  direction: down
  C1: "socket() / bind()"
  C2: "connect() / accept()"
  C3: "close() / shutdown()"
  C4: "setsockopt()"
  C5: "Routing table update"
  C6: "ARP resolution"
  C7: "Statistics polling"
}
```

**원칙**: "자주 발생하는 Data Path 는 HW 로, 드문 Control Path 는 SW 로." 이 한 줄이 TOE architecture 모든 결정의 근거입니다.

### 4.3 DMA / TSO / TOE / RDMA — 한 그림

```d2
direction: right

SW: "SW TCP" {
  direction: right
  SW1: "App"
  SW2: "sk_buff"
  SW1 -> SW2: "copy · CPU"
  SW3: "NIC"
  SW2 -> SW3: "stack · CPU"
  SW4: "wire"
  SW3 -> SW4: "DMA"
}
TSO: "TSO" {
  direction: right
  T1: "App"
  T2: "sk_buff (big)"
  T1 -> T2: "copy · CPU"
  T3: "wire"
  T2 <-> T3: "NIC TSO\n(HW segment)"
}
TOE: "TOE" {
  direction: right
  O1: "App"
  O2: "TOE buf"
  O1 -> O2: "DMA"
  O3: "wire"
  O2 <-> O3: "HW seg+chksum+retx\n(전부 HW)"
}
RDMA: "RDMA — TCP 자체 우회" {
  direction: right
  R1: "App buffer"
  R2: "HCA"
  R1 <-> R2: "MR\n(사전 등록)"
  R3: "wire"
  R2 <-> R3: "DMA\n(kernel bypass)"
}
```

오른쪽으로 갈수록 CPU 개입이 줄지만, _기존 socket API 호환성_ 도 같이 줄어듭니다 — RDMA 는 별도 verbs API. TOE 는 **socket API 를 유지하면서 가장 많은 cycle 을 줄이는 지점**.

---

## 5. 디테일 — TCP/IP 스택, TCP 기능, TOE 효과

### 5.1 TCP/IP 4 계층 모델

```d2
direction: down

L4: "**4. Application Layer**\nHTTP, FTP, SSH, NVMe-oF\n_(사용자 데이터)_"
L3: "**3. Transport Layer**\nTCP, UDP\n_(신뢰성, 흐름 제어)_\n← TOE 가 Offload 하는 영역"
L2: "**2. Internet Layer**\nIP, ICMP, ARP\n_(라우팅, 주소)_\n← 일부 Offload (checksum, fragment)"
L1: "**1. Network Access Layer**\nEthernet (MAC + PHY)\n_(물리 전송)_\n← NIC / DCMAC 이 처리"
L4 -- L3
L3 -- L2
L2 -- L1
```

각 계층의 핵심 용어: **layer**(레이어; 통신 기능을 역할별로 쌓은 계층 — 위 계층은 아래 계층이 보장하는 서비스 위에서 동작), **UDP**(User Datagram Protocol; TCP 와 달리 순서·재전송 보장 없이 빠르게 보내는 비신뢰 전송 규약), **MAC**(Media Access Control; 이더넷 프레임을 만들고 물리 매체 접근을 제어하는 L1/L2 계층), **PHY**(physical layer; 비트를 실제 전기/광 신호로 송수신하는 물리 회로), **DCMAC**(data-center MAC; 데이터센터용 고속 이더넷 MAC 블록). 위 계층(Transport)이 TOE 가 HW 로 가져가는 핵심 영역입니다.

### 5.2 TCP 의 핵심 기능 (UDP 와의 차이)

| 기능 | TCP | UDP |
|------|-----|-----|
| 연결 | Connection-oriented (3-way handshake) | Connectionless |
| 신뢰성 | 보장 (ACK, 재전송) | 미보장 |
| 순서 보장 | Sequence Number 로 보장 | 미보장 |
| 흐름 제어 | Window 기반 | 없음 |
| 혼잡 제어 | Slow Start, Congestion Avoidance | 없음 |
| 오버헤드 | 높음 (헤더 20B+, 상태 관리) | 낮음 (헤더 8B) |

UDP 는 헤더 8 B + 상태 관리 없음 → **CPU 부하가 작아 offload 효과 미미**. TCP 는 packet 마다 반복 연산이 많아 **HW offload 효과 극대화**.

### 5.3 TCP 연결 수명 주기

```d2
shape: sequence_diagram

C: "Client"
S: "Server"

# Note over C: 연결 수립 — 3-Way Handshake
# Note over C: 데이터 전송
# Note over C: 연결 해제 — 4-Way Handshake (또는 RST)
C -> S: "SYN"
S -> C: "SYN+ACK"
C -> S: "ACK"
C -> S: "DATA (seq=100, len=500)"
S -> C: "ACK (ack=600)"
C -> S: "FIN"
S -> C: "ACK"
S -> C: "FIN"
C -> S: "ACK"
```

위 다이어그램의 약어 해부 — TCP 의 제어 동작은 헤더의 **flag**(플래그; 1비트 켜짐/꺼짐으로 패킷의 종류·의도를 표시하는 표식) 비트로 나타냅니다. **SYN**(synchronize; 연결을 열며 시작 sequence number 를 맞추자는 신호), **ACK**(acknowledgment; "여기까지 받았다"는 확인 신호), **FIN**(finish; 보낼 데이터가 끝났으니 연결을 닫자는 신호), **RST**(reset; 연결을 즉시 강제 종료하라는 신호)입니다. **3-way handshake**(SYN → SYN+ACK → ACK 의 3단계 교환으로 양쪽이 서로의 시작 번호를 확인하며 연결을 여는 절차), **4-way handshake**(양쪽이 각각 FIN/ACK 를 주고받아 연결을 닫는 절차)가 이 flag 들의 조합입니다.

연결 setup/teardown 은 연결당 단 1 회 발생하지만, 데이터 전송 처리는 packet 이 올 때마다 매번 발생합니다. 빈도 격차가 100 만 배 이상 납니다. 이 비대칭이 HW/SW 분리의 근거입니다 — 자주 일어나는 일은 HW 로, 드물게 일어나는 일은 SW 로.

### 5.4 TCP 헤더 구조 (TOE HW 가 만들어야 하는 필드)

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

### 5.5 100 Gbps 에서 CPU 가 부담하는 비용 — 어림셈

100 Gbps 에서 64 B 패킷 기준 라인레이트는 약 150 M packets/sec 입니다. 이 패킷 하나하나에 대해 CPU 는 checksum 계산·검증, Sequence Number 관리, ACK 생성·처리, Window 크기 관리, 재전송 타이머 관리, 그리고 커널에서 유저 공간으로의 메모리 복사까지 수행해야 합니다. 이 연산들이 packet 마다 쌓이면 CPU 코어 여러 개가 TCP 처리에 100 % 점유되어 애플리케이션이 사용할 수 있는 CPU 가 사실상 없어지고, CPU 가 "네트워크 프로세서" 로 전락하게 됩니다.

### 5.6 TOE 적용 후 효과

TOE 를 적용하면 checksum 계산·검증, TCP segmentation, ACK 생성, 재전송 관리, 흐름 제어를 NIC HW 가 모두 처리합니다. CPU 는 연결 수립·해제라는 Control Path 에만 관여하고, 데이터 전달은 DMA 가 맡습니다. 그 결과 CPU 부하가 80~90 % 감소하고, 절약된 코어를 애플리케이션에 돌릴 수 있게 됩니다.

| 항목 | SW TCP (CPU) | TOE (HW) |
|------|-------------|----------|
| Throughput | ~40 Gbps (CPU 한계) | 100 Gbps+ (라인 레이트) |
| Latency | ~10–50 µs (커널 경유) | ~1–5 µs (HW 직접) |
| CPU 사용률 | 80–100 % (TCP 처리) | ~10 % (제어만) |
| 연결 수 | 수만 (메모리/CPU 한계) | 수백만 (HW 상태 테이블) |
| 전력 | 높음 (CPU 풀로드) | 낮음 (전용 HW 효율) |

주목할 점은 throughput 숫자보다 **CPU 사용률** 과 **latency** 의 차이입니다. 일반 NIC + TSO 조합도 100 Gbps 라인레이트는 채울 수 있지만, CPU 점유율은 여전히 높습니다. TOE 의 진짜 가치는 그 CPU 를 애플리케이션에 돌려주는 데 있습니다.

### 5.7 TOE vs 다른 Offload 기술

| 기술 | Offload 범위 | 복잡도 | 성능 | 사용 사례 |
|------|-------------|--------|------|----------|
| **Checksum Offload** | Checksum 만 | 낮음 | 약간 향상 | 거의 모든 NIC |
| **TSO/LSO** | TCP Segmentation 만 | 중간 | 중간 향상 | 대부분의 NIC |
| **TOE** | TCP/IP 전체 | 높음 | 대폭 향상 | 서버, 가속기, 스토리지 |
| **RDMA** | TCP 우회 (직접 메모리 접근) | 매우 높음 | 최고 | HPC, 저지연 |
| **DPDK** | 커널 우회 (유저스페이스) | 높음 | 높음 | NFV, 라우터 |

Checksum Offload ⊂ TSO ⊂ TOE 로 포함관계가 성립합니다. 오른쪽으로 갈수록 더 많은 것을 HW 가 대신하지만, 구현 복잡도도 함께 높아집니다. RDMA 는 TCP 자체를 우회하므로 이 포함관계 바깥의 별도 범주이고, DPDK 는 SW 이지만 커널을 우회하는 최적화로 "offload" 라기보다는 "bypass" 에 가깝습니다.

### 5.8 실무 주의점 — Partial Checksum Offload 와 부분 헤더 처리 오류

:::caution[실무 주의점 — Partial Checksum Offload와 부분 헤더 처리 오류]
**현상**: RX 체크섬 오프로드를 활성화했을 때 특정 패킷에서만 IP/TCP 체크섬 오류가 보고되며, 동일 패킷을 SW 스택으로 처리하면 정상이다.

**원인**: Partial offload는 IP/TCP 헤더가 단일 DMA 버퍼에 연속으로 존재한다고 가정한다. IP 옵션 필드가 있거나 TCP 헤더가 세그먼트 경계에 걸리면 HW가 헤더 끝 위치를 잘못 계산하여 체크섬 오류를 발생시킨다.

**점검 포인트**: TB에서 IP Options(IHL>5) 패킷과 TCP Options(Data Offset>5) 패킷을 별도 시나리오로 구성. `csum_start`와 `csum_offset` 디스크립터 필드가 옵션 길이에 따라 정확히 갱신되는지 DMA 디스크립터 덤프에서 확인.
:::
---

## 6. 흔한 오해 와 DV 디버그 체크리스트

### 흔한 오해

:::danger[❓ 오해 1 — 'TOE 는 TCP 전체를 HW 에서 처리한다']
**실제**: TOE 는 **stateful 한 데이터 패스** (Checksum, Segmentation, 재전송, Flow/Congestion control) 만 HW 가 처리합니다. **연결 수립/해제 같은 control path 는 여전히 CPU(SW)** 가 담당. <br>
**왜 헷갈리는가**: "TCP offload" 라는 표현이 _전부_ 라는 인상을 주지만, 실제 분배는 빈도 기준 (Data path = 빈번 → HW, Control path = 드묾 → SW).
:::
:::danger[❓ 오해 2 — 'TOE = 빠른 NIC']
**실제**: 일반 NIC + Checksum/TSO 도 100 Gbps 라인레이트 자체는 채울 수 있습니다. TOE 의 차별점은 **CPU 점유율** (보통 5–10× 감소) 과 **tail latency**. throughput 만 보면 큰 차이가 안 날 수도 있음. <br>
**왜 헷갈리는가**: 마케팅 자료가 "라인레이트" 만 강조해서.
:::
:::danger[❓ 오해 3 — 'TOE 가 있으면 항상 throughput 이 향상된다']
**실제**: TOE 가 효과 있는 워크로드는 **small packet, 다수 connection, CPU bound** 환경. **Large MTU**(Maximum Transmission Unit; 한 프레임에 담을 수 있는 최대 바이트 — 보통 1500, **jumbo frame**(MTU 를 9000 정도로 키운 큰 프레임)) **+ bulk transfer** 에서는 일반 NIC + GSO(Generic Segmentation Offload; 커널이 SW 적으로 segment 를 미루다 마지막에 나눠 처리하는 기법) 만으로도 충분하고, TOE 의 connection table lookup 오버헤드가 오히려 작은 손해를 줄 수도 있습니다.<br>
**왜 헷갈리는가**: "HW = 항상 빠름" 이라는 직관. 실제로는 workload-dependent.
:::
:::danger[❓ 오해 4 — 'Connection state 는 한번 만들어지면 영구 보존된다']
**실제**: TOE Connection Table 은 고정 크기 SRAM(on-chip 의 빠르지만 작은 메모리). **TIME_WAIT**(연결을 닫은 뒤에도 늦게 오는 패킷 처리를 위해 일정 시간 entry 를 붙들어 두는 종료 직전 상태) 만료, RST, idle timeout 등으로 entry 가 회수되며, 비활성 connection 은 **LRU**(Least Recently Used; 가장 오래 안 쓴 항목부터 내보내는 교체 정책) 로 DRAM 에 swap-out 됩니다. 재접근 시 swap-in 지연이 발생. <br>
**왜 헷갈리는가**: "stateful" 이 _상태가 무한히 유지된다_ 로 들려서.
:::

:::note[메커니즘 — connection state 의 SRAM↔DRAM tiering (swap-in/out)]
수백만 connection 의 state 를 전부 on-chip SRAM 에 둘 수는 없습니다 (SRAM 은 빠르지만 작고 비쌈). 그래서 TOE 는 메모리를 **2-tier** 로 둡니다 — _자주 쓰는 active connection 의 state 는 빠른 SRAM_ 에, _당장 트래픽이 없는 idle connection 의 state 는 큰 DRAM_ 에 보관합니다. 동작은 cache 와 같습니다: 패킷이 도착하면 HW 가 그 패킷의 **4-tuple (src IP, dst IP, src port, dst port)** 로 SRAM connection table 을 lookup 합니다. ① **SRAM hit** 이면 즉시 state 를 읽어 처리 (빠른 경로). ② **miss** 면 — 그 connection 은 DRAM 으로 swap-out 돼 있는 것이므로 — HW 가 DRAM 에서 해당 state 를 **fetch (swap-in)** 해 SRAM 슬롯에 올리고, 자리가 없으면 가장 오래 안 쓴(LRU) entry 를 DRAM 으로 **swap-out** 해 자리를 비웁니다. 이 swap-in 은 DRAM 왕복 지연을 더하므로, _오래 idle 했다 다시 깨어나는 connection_ 의 첫 패킷에서 latency 가 튑니다 (오해 4 의 "재접근 시 지연"). 검증 관점에서는 active set 을 SRAM 용량 이상으로 늘려 swap 경로를 _강제로_ 타게 하는 시나리오가 핵심입니다. (이 tiering 구조는 [Module 02](../02_toe_architecture/) 에서 자세히.)
:::
:::danger[❓ 오해 5 — 'UDP 도 TOE 가 처리해야 한다']
**실제**: UDP 는 헤더 8 B + 상태 관리 없음. 즉 packet 당 CPU 부담이 작아 offload 의 ROI 가 낮습니다. TOE 가 UDP 의 checksum 정도는 도와줄 수 있어도, "TCP Offload Engine" 이름에서 보듯 핵심은 TCP. <br>
**왜 헷갈리는가**: "프로토콜 스택 전체 = TCP+UDP" 이미지 때문.
:::
### DV 디버그 체크리스트 (TOE 개념 단계에서 마주칠 첫 실패들)

| 증상 | 1차 의심 | 어디 보나 |
|---|---|---|
| `write()` 가 빨라졌는데 throughput 이 그대로 | TOE descriptor 가 너무 작게 분할 (1 MB 가 1024 개 1 KB descriptor 로) | host driver 의 SG list, descriptor count |
| TOE 활성화했더니 small packet workload 가 _느려짐_ | connection table lookup latency > 절약된 CPU cycle | 워크로드 통계: pkt size 분포, conn 수 |
| Checksum offload 켰더니 특정 패킷만 fail | IP options 또는 TCP options 가 있어 헤더 길이 가변 | §5.8 의 csum_start/csum_offset 갱신 |
| iperf 결과 SW vs TOE 가 같은 값 | TSO 가 이미 동작 중이라 추가 offload 효과 없음 | `ethtool -k` 로 features 확인 |
| Connection 다수 생성 시 새 conn 거부 | Connection Table full 또는 TIME_WAIT 누적 | conn table used count, half-open count |
| ACK 가 늦게 오는 듯한 latency 증가 | CPU 가 ACK process 까지 하느라 대기 큐 누적 (TOE 가 ACK offload 안 켜진 경우) | TOE config 의 ack offload flag |
| `tcpdump` 로는 정상인데 app 이 데이터 못 받음 | RX path DMA descriptor lookup 실패 | host RX ring 의 producer/consumer pointer |
| RDMA-aware app 이 TOE 를 안 씀 | RDMA 는 TCP 자체를 우회 → TOE 와 다른 범주 | app 의 socket family (AF_INET vs AF_RDMA) |

이 체크리스트는 이후 모듈에서 더 정교한 형태로 다시 나옵니다. 지금 단계에서는 "TOE 효과 = (workload 가 small packet + many conn + CPU bound) ✕ (TOE config 가 stateful offload 켜져 있음)" 만 기억하세요.

---

## 7. 핵심 정리 (Key Takeaways)

- **TOE = TCP/IP HW offload**. Host CPU 부하 ↓ + throughput ↑ + tail latency ↓.
- **Partial offload**: checksum, TSO/LRO (segment offload). 일반 NIC 도 지원.
- **Full offload (= TOE)**: connection state machine 전체 HW. RDMA / iWARP 등 특수 NIC.
- **동기**: 100 GbE 에서 packet rate 가 1.5 M pps/Gbps → CPU cycle/packet 한도 초과.
- **활용**: HPC, hyperscale (AWS Nitro, Azure SmartNIC), storage networks (NVMe-oF).
- **HW/SW 분리 원칙**: 빈도 높은 Data Path = HW, 드문 Control Path = SW. 이 한 줄이 TOE 모든 설계 결정의 근거.

:::caution[실무 주의점]
- "TOE = 빠르다" 는 **CPU 점유율 / tail latency** 의 이야기. throughput 만 보면 일반 NIC + TSO 도 라인레이트 가능.
- **Workload dependence**: small packet + many conn + CPU bound 일 때 효과 큼. bulk + jumbo 는 효과 작음.
- **Connection state 유한**: Table full, TIME_WAIT 누적 시 새 연결 거부 가능 → 검증의 핵심 abnormal scenario.
:::
### 7.1 자가 점검

:::tip[🤔 Q1 — TOE vs TSO/LRO (Bloom: Apply)]
NIC 옵션:
- (a) Plain NIC + SW TCP.
- (b) NIC + TSO (Segmentation) + LRO (Receive Coalescing) — partial offload.
- (c) Full TOE — connection state, retry, timer 모두 HW.

어느 워크로드에 어느 것?

<details>
<summary>정답</summary>

- **Bulk transfer** (큰 file): (b) TSO/LRO 충분. Full TOE 의 _connection 비용_ 정당화 안 됨.
- **Many small connections** (HTTP, RPC): **(c) Full TOE** — 수천 connection 의 _SW overhead_ 가 큼.
- **Low CPU budget**: (c) — CPU 점유율 minimize.

Full TOE 는 _design 복잡_, _interop_ 어려움 → bulk 워크로드에는 보통 (b) 가 cost-effective.

</details>
:::
:::tip[🤔 Q2 — Stateful offload 검증 어려움 (Bloom: Analyze)]
Stateless offload (TSO) 보다 stateful (TOE) 검증이 _왜 어려운가_?

<details>
<summary>정답</summary>

- **State space 폭발**: connection state (open, established, fin_wait, ...) × 동시 연결 수 × abnormal scenario.
- **Interop**: 각 OS / driver / peer 가 다른 TCP 변형. RFC 의 모든 corner 정확.
- **Long-tail bug**: 수 시간 운영 후만 보이는 state corruption. 짧은 시뮬에서 _안 잡힘_.

해법: random workload + long simulation + state coverage cross.

</details>
:::
### 7.2 출처

**External**
- IETF RFC 793 *TCP*, RFC 5681 *TCP Congestion Control*
- RFC 2018 *SACK*, RFC 1323 *PAWS*
- *Sockets Direct Protocol* — IBTA WP
- Chelsio TOE technical specifications

---

## 다음 단계

→ [Module 02 — TOE Architecture](../02_toe_architecture/): TOE 의 가정 위에서 TX/RX path, Connection Table, Timer Wheel, Memory hierarchy 가 어떻게 그려지는지.

- 📝 [**Module 01 퀴즈**](../quiz/01_tcp_ip_and_toe_concept_quiz/)

