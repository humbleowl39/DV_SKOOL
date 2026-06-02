---
title: "Module 02 — TOE Architecture"
---

:::tip[학습 목표]
이 모듈을 마치면:

- **Diagram** TOE 의 TX path, RX path, Connection Table, Timer Wheel, Memory hierarchy 의 블록 관계를 그릴 수 있다.
- **Trace** 한 TCP segment 가 RX path 의 6 단계를 거쳐 host buffer 에 도착하는 흐름을 추적할 수 있다.
- **Apply** Segmentation / Reassembly / Checksum / Flow control 이 어느 pipeline stage 에서 일어나는지 매핑한다.
- **Distinguish** Stateful vs Stateless offload 의 구조 차이를 connection state 의 위치 관점에서 구분한다.
- **Plan** 동시 connection 수 (수천~수백만) 를 위한 SRAM/DRAM hierarchy 와 LRU 정책을 설계한다.
- **Justify** 왜 RTO 타이머가 개별 카운터가 아니라 Timer Wheel 로 구현되는지 정당화할 수 있다.
:::
:::note[사전 지식]
- [Module 01](../01_tcp_ip_and_toe_concept/)
- TCP state machine (LISTEN/SYN_SENT/ESTABLISHED/FIN_WAIT 등)
:::
---

## 1. Why care? — 이 모듈이 왜 필요한가

### 1.1 시나리오 — _1 백만 연결_ 의 _RTO timer_

당신이 cloud server 를 운영한다고 해봅시다. 동시 활성 TCP 연결이 1 백만 개이고, 각 연결마다 독립적인 RTO timer 가 있어 응답이 안 오면 retransmit 해야 합니다.

가장 단순한 SW 모델은 매 cycle 마다 1 백만 개의 timer 를 전부 비교하는 것인데, 이러면 CPU 가 대부분의 시간을 timer 처리에 소진하게 됩니다.

TOE HW 의 Timer Wheel 은 이 문제를 구조적으로 풉니다. 1 ms 단위의 bucket 들로 시간을 분할하고, 각 timer 는 자신의 만료 시점에 해당하는 bucket 에 연결해 둡니다. 그러면 매 1 ms 마다 wheel 이 한 칸 돌아 현재 만료 bucket 의 timer 만 처리하면 됩니다 — 수십 개. 비용이 _O(전체 N)_ 에서 _O(만료 수)_ 로 내려갑니다.

여기에 더해 Connection Table 은 1 백만 연결의 4-tuple→state 매핑을 SRAM 에서 O(1) 로 꺼내 주고, 활성 연결은 빠른 SRAM 에, idle 연결은 느린 DRAM 에 두는 tier 구조가 메모리 비용을 현실적으로 만듭니다. 이 구조 없이 SW 로 처리하면 CPU 8 코어가 100 % 점유되지만, HW offload 면 0.5 코어로 줄어듭니다.

Module 01 에서 "TOE 는 stateful offload" 라는 한 줄을 잡았습니다. 이 모듈은 그 한 줄이 **실제 칩 안에서 어떻게 블록으로 나뉘는가** 를 보여줍니다. TX path 의 6 단계, RX path 의 6 단계, 그 사이를 잇는 Connection Table, 수백만 연결의 RTO 를 처리하는 Timer Wheel, SRAM/DRAM 하이어라키 — 이 다섯이 TOE 의 골격입니다.

이 모듈을 건너뛰면 Module 03 (Key Functions) 에서 "Checksum 이 어디서 일어나는지", "재전송 버퍼가 어디 있는지" 같은 위치 질문에 답할 수 없습니다. 또 Module 04 (DV) 의 scoreboard 와 monitor 가 어느 인터페이스에서 hook 되는지도 이 architecture 위에서만 의미가 있습니다.

---

## 2. Intuition — 비유와 한 장 그림

:::tip[💡 한 줄 비유]
**Connection Table** ≈ **은행 창구 번호표 시스템**.<br>
수백만 명의 고객 (TCP 연결) 이 각자 자기 순서 (Seq Number) 와 잔액 (Window) 을 갖고 있고, 창구 (TOE pipeline) 는 번호표 (4-tuple 해시) 로 해당 고객 파일을 O(1) 에 꺼내 처리한다. 활성 고객은 창구 옆 캐비넷 (SRAM) 에, 휴면 고객은 지하 보관소 (DRAM) 에.
:::
### 한 장 그림 — TOE 전체 블록 다이어그램

```d2
direction: down

HOST: "Host Interface (PCIe / AXI)"
DMA: "**DMA Engine**\n호스트 메모리 ↔ TOE 버퍼"
CT: "**Connection Table**\nTCP 연결별 상태\n(seq / ack / window / timer / state)\n수천 ~ 수백만 엔트리"
TX: "**TX Path**\nSegmentation\nChecksum Gen\nACK Process\nRetx Engine\nWindow Mgmt"
RX: "**RX Path**\nReassembly\nChecksum Ver\nACK Generate\nFlow Control\nSeq Validate"
MAC: "**MAC Interface**\nDCMAC / Ethernet MAC\n(Ethernet Frame TX/RX)"
HOST -- DMA
DMA -- CT
CT -- TX
CT -- RX
TX -- MAC
RX -- MAC
```

### 왜 이 디자인인가 — Design rationale

세 가지 요구가 동시에 풀려야 했습니다.

1. **Full-duplex 라인레이트** → TX path 와 RX path 가 _독립_ pipeline. 한쪽 stall 이 다른 쪽을 멈추지 않게.
2. **수백만 연결의 상태 보존** → Connection Table 이 모든 packet pipeline 의 _공통 노드_. 양쪽 path 가 lookup/update 함.
3. **연결당 RTO 타이머 + 메모리 효율** → Timer Wheel + SRAM/DRAM tiering. 모든 연결을 SRAM 에 올릴 수 없고, 모든 카운터를 매 cycle 검사할 수도 없음.

이 세 요구의 교집합이 위 그림 — TX/RX 양쪽 path + 중앙 Connection Table + Timer Wheel + Memory hierarchy.

---

## 3. 작은 예 — 한 TCP segment 가 RX path 에서 host 까지 가는 여정

가장 단순한 시나리오. peer 가 우리 server 의 ESTABLISHED 연결로 **256 byte TCP segment** 를 보냅니다 (seq=10000, len=256, ack=20000, window=65535).

```d2
direction: down

S1: "① DCMAC RX 인계"
S2: "② Checksum 검증"
S3: "③ Conn Lookup · 4-tuple → SRAM"
S4: "④ Seq 검증 · rcv_nxt 비교"
S5: "⑤ TCP State · rcv_nxt·snd_una 갱신"
S6: "⑥ Reassembly · OOO 버퍼"
S7: "⑦ DMA · TOE→Host"
S8: "⑧ Host 알림 · IRQ/polling"
APP: "App · read() 256"
S1 -> S2
S2 -> S3: "pass"
S3 -> S4: "hit"
S4 -> S5
S5 -> S6
S6 -> S7
S7 -> S8
S8 -> APP
```

| Step | 어느 블록 | 무엇을 | 의미 |
|---|---|---|---|
| ① | DCMAC → TOE | Ethernet Frame 의 payload (IP/TCP) 를 TOE RX 에 인계 | AXI-S 인터페이스, 백프레셔 가능 |
| ② | RX Checksum Verify | IP header + TCP pseudo header + payload 의 1's complement sum | 실패 시 silent drop + counter |
| ③ | Connection Lookup | {srcIP, srcPort, dstIP, dstPort} 의 hash → Connection Table entry | O(1) 평균 (충돌은 chaining) |
| ④ | Seq Validate | seg.seq == rcv_nxt → in-order. (≠ → OOO 버퍼 또는 drop) | 기대 범위 밖이면 DUP ACK |
| ⑤ | TCP State Update | rcv_nxt += len, snd_una 갱신, retx buffer 해제 | Connection Table 의 state RMW |
| ⑥ | Reassembly | in-order 라 직통, OOO 라면 buffer 에 저장 후 gap 채워질 때까지 대기 | 본 예시는 in-order |
| ⑦ | RX DMA | TOE 의 RX buffer → host memory descriptor 가 가리키는 영역 | descriptor ring 의 producer pointer 증가 |
| ⑧ | Host notify | IRQ 또는 polling 방식으로 app 이 read() 가능 신호 | NAPI / busy-poll 정책 |

```c
// app 측 (변하지 않음 — 이 모든 과정이 socket API 뒤에 숨음)
ssize_t n = recv(sock, buf, 256, 0);   // returns 256
// SW TCP 라면 같은 recv() 가 내부에서 Step ②~⑧ 을 CPU 가 수행.
// TOE 라면 모두 HW. CPU 는 IRQ/polling 한 번만.
```

:::note[여기서 잡아야 할 두 가지]
**(1) Connection Table 이 모든 packet 의 통과점** — Step ③ 의 lookup 이 실패하면 그 packet 은 _그 어떤 처리도 받지 못함_. 즉 connection table 의 정확성이 RX path 의 모든 정확성을 좌우. <br>
**(2) State update 가 atomic 해야 한다** — Step ⑤ 의 rcv_nxt/snd_una/retx buffer 갱신이 partial 로 끝나면 다음 packet 이 잘못된 state 를 봅니다. HW 구현에서는 single-write atomicity + per-conn lock 이 필요.
:::
---

## 4. 일반화 — TOE 의 네 기둥

TOE architecture 는 다음 네 기둥으로 정형화됩니다.

### 4.1 데이터 패스 (TX/RX) — 반복 packet 처리

```
TX Path                                  RX Path
────────                                 ────────
1. Host DMA                              1. Checksum verify
2. TCP Segmentation                      2. Connection lookup
3. Header build (TCP/IP)                 3. Seq validate
4. Checksum gen                          4. State update (FSM, ACK)
5. Retx buffer + RTO arm                 5. Reassembly
6. To MAC                                6. RX DMA → host
```

TX 와 RX 는 대칭적인 구조를 가지지만, 두 path 모두 하나의 공통 지점에서 만납니다 — **Connection Table**. TX 는 header build 시 seq/ack 를 읽어 오는 read 위주 접근이고, RX 는 상태를 갱신하는 read+write 를 수행합니다. 이 공유 자원 때문에 동일 연결에 대한 TX/RX 의 접근 원자성이 중요해집니다.

### 4.2 컨트롤 패스 (CPU side) — 드문 결정

| 결정 | CPU 가 하는 이유 | 빈도 |
|---|---|---|
| `socket()` / `bind()` | OS file descriptor 와의 연결 | conn 당 1 회 |
| `connect()` / `accept()` | 3-way handshake 트리거, 정책 검사 (firewall, conntrack) | conn 당 1 회 |
| `setsockopt()` | TCP_NODELAY, SO_KEEPALIVE 등 정책 변경 | 드묾 |
| `close()` | FIN 시퀀스 시작, conn entry 회수 | conn 당 1 회 |
| Routing/ARP update | 외부 이벤트 (BGP, ARP refresh) | 분 단위 |

**원칙 재확인**: "자주 발생하는 Data Path 를 HW 로, 드문 Control Path 를 SW 로". Data path = ns~µs latency 요구, Control path = ms 단위 허용.

### 4.3 Connection Table — Stateful 의 본진

```d2
direction: right

PD: "PD-like layer\n(PCIe BAR + descriptor ring)"
DMA: "DMA Engine\nhost memory ↔ TOE buf"
CT: "Connection Table"
HOT: "Hot entries (SRAM)"
COLD: "Cold entries (DRAM, LRU)"
HASH: "4-tuple hash index"
PATH: "양쪽 path 가 read/write"
PD -> DMA
PD -> CT
CT -> HOT
CT -> COLD
CT -> HASH
CT -> PATH
```

Connection Table entry 가 담는 필드들이 곧 TOE 의 "stateful" 을 정의합니다. 각 연결마다 TCP FSM state (CLOSED/LISTEN/SYN_RCVD/ESTABLISHED/…), Sequence number 쌍 (snd_una, snd_nxt, rcv_nxt), Window 값 (snd_wnd, rcv_wnd, snd_wl1/wl2), 혼잡 제어 변수 (cwnd, ssthresh, dup_ack_count), RTT 추정치 (srtt, rttvar), Timer Wheel 의 slot 위치, 그리고 DRAM 상의 retx buffer 위치와 길이가 한 entry 에 기록됩니다. 이 정보가 모두 HW 에 있어야 packet 이 도착할 때마다 SW 개입 없이 올바른 응답을 만들 수 있습니다.

### 4.4 Timer Wheel + Memory hierarchy

수백만 connection 의 RTO 타이머를 동시에 tick 마다 검사하는 것은 면적·전력 관점에서 불가능합니다. 그래서 Hashed Timing Wheel 자료구조로 각 타이머를 만료 슬롯에 등록해 두고, 매 tick 에는 현재 슬롯만 처리합니다 — O(1). 마찬가지로 수백만 connection 의 state 를 전부 SRAM 에 올릴 수도 없으므로, 활성 연결은 빠른 SRAM 에 두고 비활성 연결은 DRAM 으로 LRU swap 합니다.

이 두 결정이 TOE 의 _scale 을 결정_ 합니다. Timer Wheel 과 메모리 tier 설계 없이는 10K 연결 수준에서 멈추게 되고, 이 둘을 갖추어야 1M 연결 이상을 지원할 수 있습니다.

---

## 5. 디테일 — 블록 / TX-RX / Table / Timer / Memory

### 5.1 TX Path (송신 경로)

```d2
direction: down

APP: "App 데이터 (64KB)"
T1: "1. DMA · Host→TOE"
T2: "2. Segmentation · MSS 분할"
T3: "3. TCP Header · Seq/Win/Flags"
T4: "4. IP Header · Src/Dst/TTL"
T5: "5. Checksum · TCP+IP"
T6: "6. Retx 버퍼 · 사본 보관"
MAC: "MAC 전송"
APP -> T1
T1 -> T2
T2 -> T3
T3 -> T4
T4 -> T5
T5 -> T6
T6 -> MAC
```

### 5.2 RX Path (수신 경로)

```d2
direction: down

MAC: "MAC 수신"
R1: "1. Checksum 검증"
R2: "2. Conn Lookup · 4-tuple"
R3: "3. Seq 검증 · 범위/중복"
R4: "4. TCP State · ACK/Win/FSM"
R5: "5. Reassembly · OOO 버퍼링"
R6: "6. DMA · TOE→Host"
MAC -> R1
R1 -> R2
R2 -> R3
R3 -> R4
R4 -> R5
R5 -> R6
```

### 5.3 Connection Table — 엔트리 구조와 Lookup

#### 엔트리 구조

```
Connection Table Entry:

+------+------+------+------+--------+--------+-------+-------+
| Src  | Dst  | Src  | Dst  | State  | Seq    | Ack   | Window|
| IP   | IP   | Port | Port | (FSM)  | Number | Number| Size  |
+------+------+------+------+--------+--------+-------+-------+
| Retx Timer  | RTT Estimate | Congestion | Retx Buffer |
|             |              | Window     | Pointer     |
+-------------+--------------+------------+-------------+

State (TCP FSM):
  CLOSED → LISTEN → SYN_RCVD → ESTABLISHED
  ESTABLISHED → FIN_WAIT_1 → FIN_WAIT_2 → TIME_WAIT → CLOSED
```

#### Connection Lookup 방법

| 방법 | 원리 | 속도 | 메모리 |
|------|------|------|--------|
| Hash Table | 4-tuple 해시 → 인덱스 | O(1) 평균 | 중간 |
| CAM (Content Addressable Memory) | 병렬 매칭 | O(1) 보장 | 큼 (비쌈) |
| TCAM | 와일드카드 매칭 가능 | O(1) 보장 | 매우 큼 |

**실무**: 대부분의 TOE 는 **Hash Table** 사용 — 비용 효율적이고 충분히 빠름. 충돌은 체이닝으로 처리.

### 5.4 타이머 관리 아키텍처 — 수백만 연결의 RTO

TOE 가 수백만 TCP 연결을 관리할 때, 각 연결별 RTO 타이머를 HW 에서 어떻게 효율적으로 구현하는지가 핵심 설계 과제다.

#### 순수 개별 타이머 (비현실적)

```
연결 100만 개 × 개별 타이머 = 100만 개 카운터
  - 매 클럭마다 100만 개 카운터 감소 검사 → 불가능
  - 면적/전력 폭발
```

#### Timer Wheel (Hashed Timing Wheel) — 실무 표준

핵심 아이디어: 시간을 슬롯으로 나누고, 만료 시점에 해당하는 슬롯에 연결을 등록.

```d2
direction: right

# unparsed: PTR(["현재 시각 포인터<br/>tick 마다 1칸 전진"])
S0: "[0]" { style.stroke: "#1a73e8"; style.stroke-width: 2 }
CA: "conn_A"
CD: "conn_D"
N0: "NULL"
S0 -> CA
CA -> CD
CD -> N0
S1: "[1]" { style.stroke: "#1a73e8"; style.stroke-width: 2 }
CB: "conn_B"
N1: "NULL"
S1 -> CB
CB -> N1
S2: "[2]" { style.stroke: "#1a73e8"; style.stroke-width: 2 }
N2: "NULL"
S2 -> N2
S3: "[3]" { style.stroke: "#1a73e8"; style.stroke-width: 2 }
CC: "conn_C"
CE: "conn_E"
N3: "NULL"
S3 -> CC
CC -> CE
CE -> N3
# unparsed: SX["[...]"]
S255: "[255]" { style.stroke: "#1a73e8"; style.stroke-width: 2 }
CF: "conn_F"
N255: "NULL"
S255 -> CF
CF -> N255
PTR -> S0 { style.stroke-dash: 4 }
```

Timer Wheel 구조 예: 256 슬롯, 1 ms 해상도.

동작:

1. **타이머 등록**: RTO=300ms 인 conn_X → 슬롯 `(현재 + 300) % 256` 에 삽입
2. **Tick**: 매 1 ms 마다 포인터 1 칸 전진
3. **만료 확인**: 현재 슬롯의 연결 리스트 순회 → 만료된 연결 처리
4. **갱신**: ACK 수신 시 기존 슬롯에서 제거 → 새 슬롯에 삽입

계층적 Timer Wheel (큰 RTO 범위 지원):

- Level 0: 1 ms 해상도, 256 슬롯 (0~255 ms)
- Level 1: 256 ms 해상도, 256 슬롯 (0~65 초)
- Level 1 만료 → Level 0 으로 재등록 (cascade)

복잡도:

- 등록 / 삭제: O(1)
- Tick 당 처리: 평균 O(1) (슬롯당 연결 수가 균등 분포일 때)
- 메모리: 슬롯 수 × 포인터 + 연결별 링크 (Connection Table 에 통합)

#### DV 검증 포인트 — 타이머

| 시나리오 | 확인 사항 |
|---------|----------|
| 정확한 만료 시점 | RTO 설정값과 실제 만료 시각 차이 ≤ 1 tick |
| ACK 수신 → 타이머 취소 | ACK 후 해당 연결의 재전송 미발생 |
| Exponential Backoff | 재전송마다 RTO 2배 증가 |
| 다수 연결 동시 만료 | 같은 슬롯에 여러 연결 → 모두 처리 |
| 타이머 갱신 (재시작) | 새 데이터 전송 시 타이머 리셋 |

### 5.5 메모리 아키텍처 — 버퍼와 테이블 배치

TOE 성능은 메모리 대역폭과 용량에 크게 의존한다. On-chip(SRAM)과 Off-chip(DRAM)을 적절히 분배하는 것이 설계 핵심.

```d2
direction: down

SRAM: "On-Chip SRAM — 빠름, 비쌈, 작음" {
  direction: down
  SR1: "**Connection Table (Hot Entries)**\n활성 연결의 상태 (Seq/ACK/Window/Timer)\n빠른 조회 필수 → SRAM / 레지스터\n예: 활성 1만 × 128B ≈ 1.2 MB"
  SR2: "**Timer Wheel**\n슬롯 배열 + 포인터 → 소량 SRAM"
  SR3: "**패킷 버퍼 (Small)**\n현재 처리 중인 패킷 (파이프라인 버퍼)\n수 KB ~ 수십 KB"
}
DRAM: "Off-Chip DRAM — 느림, 저렴, 큼" {
  direction: down
  DR1: "**Connection Table (Cold Entries)**\n비활성 / 대기 연결 → DRAM swap\n예: 전체 100만 × 128B ≈ 128 MB"
  DR2: "**재전송 버퍼 (TX Retransmit Buffer)**\nACK 대기 중인 세그먼트 사본\n연결별 수 KB ~ 수 MB → 전체 수 GB"
  DR3: "**RX Reassembly 버퍼**\nOut-of-Order 세그먼트 임시 저장\n연결별 수 KB"
}
SRAM -> DRAM: "Cache / Spill"
```

설계 트레이드오프는 명확합니다. SRAM 을 늘리면 성능은 올라가지만 면적과 비용도 함께 올라갑니다. 반대로 DRAM 에 의존하면 비용은 줄지만 메모리 컨트롤러를 경유하는 지연이 늘어납니다. 따라서 실무 설계는 활성 연결을 SRAM 캐시에 유지하고 LRU 로 교체하는 전략을 씁니다. 100 Gbps 를 달성하는 데에는 재전송 버퍼 접근 대역폭이 병목이 될 수 있으므로 DRAM 채널 수와 access pattern 을 함께 검토해야 합니다.

#### DV 검증 포인트 — 메모리

| 시나리오 | 확인 사항 |
|---------|----------|
| Connection Table 가득 참 | 새 연결 거부 또는 LRU 교체 정상 동작 |
| SRAM ↔ DRAM 스왑 | 비활성 연결 swap-out 후 재활성화 시 상태 일관성 |
| 재전송 버퍼 오버플로 | 버퍼 한계 시 오래된 데이터 폐기 정책 |
| OOO 버퍼 가득 참 | 추가 OOO 패킷 처리 (폐기 또는 ACK으로 재요청) |

### 5.6 HW/SW 분리 — Control Path vs Data Path

```d2
direction: right

CP: "Control Path — SW (CPU)" {
  direction: down
  C1: "연결 수립/해제\n(3-way / 4-way)"
  C2: "연결 정책\n설정"
  C3: "예외 처리"
  C4: "통계 / 모니터링"
  CN: "빈도: 연결당 1-2 회\n지연 허용: ms 단위"
}
DP: "Data Path — HW (TOE)" {
  direction: down
  D1: "Checksum\n계산/검증"
  D2: "Segmentation\nReassembly"
  D3: "ACK\n생성/처리"
  D4: "재전송\n(타이머+재전송)"
  D5: "흐름/혼잡\n제어"
  D6: "DMA 전송"
  DN: "빈도: 패킷당 매번\n지연 요구: ns~μs"
}
CP -> DP: { style.opacity: 0 }
```

핵심: "자주 발생하는 Data Path 를 HW 로, 드문 Control Path 를 SW 로".

### 5.7 TOE 와 DCMAC 연동 (이력서 연결)

```d2
direction: down
HOST: "Host\n(CPU)"
TOE: "TOE Engine"
DCMAC: "DCMAC\n(AMD MAC)"
ETH: "Ethernet\n100 Gbps+"
HOST <-> TOE
TOE <-> DCMAC: "AXI-Stream"
DCMAC <-> ETH
```

DCMAC (AMD):

- 100 / 200 / 400 Gbps Ethernet MAC
- Ethernet Frame 송수신
- FCS (Frame Check Sequence) 처리
- Pause Frame (흐름 제어)

TOE ↔ DCMAC 인터페이스는 AXI-Stream 기반입니다. TX 방향에서는 TOE 가 만든 TCP 세그먼트가 DCMAC 으로 전달되어 Ethernet Frame 으로 포장되고, RX 방향에서는 DCMAC 이 수신한 Ethernet Frame 을 TOE 로 넘겨 TCP 세그먼트를 꺼냅니다.

이 인터페이스의 검증 포인트는 크게 네 가지입니다. 먼저 AXI-S 핸드셰이크가 valid/ready 조건에서 모두 정확히 동작하는지 확인해야 합니다. 그 다음 Frame 크기와 정렬, 패딩이 규격대로인지 봅니다. DCMAC 이 busy 할 때 TOE 가 backpressure 를 받아 올바르게 대기하는지도 검증 대상입니다. 마지막으로 CRC 에러가 발생했을 때 DCMAC 이 TOE 에 이를 통지하고 TOE 가 적절히 처리하는 에러 전파 경로를 확인해야 합니다.

### 5.8 실무 주의점 — SYN Flood 시 Connection Table 고갈

:::caution[실무 주의점 — SYN Flood 시 Connection Table 고갈]
**현상**: SYN 패킷이 대량으로 유입될 때 정상 클라이언트의 연결 요청이 거부되며, `conn_table_full` 상태 비트가 set 된다.

**원인**: TOE의 Connection Table은 고정 크기(예: 64K entry)이다. Half-open 상태(SYN_RCVD)인 항목이 SYN-ACK 응답 없이 쌓이면 테이블이 포화된다. SYN Cookie 미지원 또는 Half-open 타임아웃이 너무 길게 설정된 경우 더욱 취약하다.

**점검 포인트**: 시뮬레이션에서 SYN only 시퀀스를 1K회 이상 인가하여 `conn_table_used` 카운터가 포화에 도달하는 사이클을 측정. 이후 정상 SYN이 DROP 되는지 확인하고, half-open 타임아웃 레지스터를 최솟값으로 설정 후 재시험.
:::
---

## 6. 흔한 오해 와 DV 디버그 체크리스트

### 흔한 오해

:::danger[❓ 오해 1 — 'Connection State 는 한번 만들어지면 영구 보존된다']
**실제**: Connection Table 은 고정 크기. TIME_WAIT 만료, RST, idle timeout 등으로 entry 가 회수되며, 비활성 connection 은 LRU 로 DRAM 에 swap-out 됩니다. 재접근 시 swap-in 지연.<br>
**왜 헷갈리는가**: "stateful offload" 가 _상태가 무한히 유지된다_ 로 들려서.
:::
:::danger[❓ 오해 2 — 'TX path 와 RX path 는 같은 Connection Table 을 동시에 쓰니 conflict 이 자주 난다']
**실제**: 같은 연결의 TX/RX 가 같은 entry 를 만지지만, 보통 _서로 다른 필드_ (TX 는 snd_*, RX 는 rcv_*). 그래도 atomicity 는 필요해서 entry 단위 single-write 또는 per-conn lock 으로 보호. 충돌 자체는 드뭄. <br>
**왜 헷갈리는가**: "shared resource = 항상 contention" 이라는 직관.
:::
:::danger[❓ 오해 3 — 'Hash Table 은 충돌 때문에 CAM 보다 느리다']
**실제**: 잘 설계된 hash + 충분히 큰 bucket 이면 평균 O(1), 충돌은 통계적으로 드물어 chaining 으로 충분. CAM 은 면적/전력 비용이 100~1000× 높아서 실무에서 꺼립니다.<br>
**왜 헷갈리는가**: 교과서가 "최악 O(n)" 을 강조해서.
:::
:::danger[❓ 오해 4 — '모든 RTO 타이머를 매 cycle 검사하면 된다']
**실제**: 100 만 카운터 × 매 cycle 비교는 면적/전력 폭발. Timer Wheel 로 _현재 슬롯_ 만 검사 → tick 당 평균 O(1). 핵심 발명. <br>
**왜 헷갈리는가**: "per-conn timer = per-conn counter" 라는 매핑이 직관적이라.
:::
:::danger[❓ 오해 5 — '재전송 버퍼는 SRAM 에 있어야 빠르다']
**실제**: Retx buffer 는 연결별 수 KB~MB → 전체 수 GB 단위 → SRAM 불가. 반드시 DRAM. SRAM 은 _state_ 만 저장 (수십 byte/conn). 데이터 자체는 DRAM. <br>
**왜 헷갈리는가**: "빠른 path = 모두 SRAM" 이라는 단순화.
:::
### DV 디버그 체크리스트 (Architecture 검증에서 자주 보는 실패)

| 증상 | 1차 의심 | 어디 보나 |
|---|---|---|
| 같은 4-tuple 인데 entry 가 두 개 | Connection lookup hash 충돌 처리 버그 | Hash bucket chain 의 4-tuple equal check |
| RX path 가 valid packet 을 drop | Connection lookup miss (state 가 CLOSED 로 보이거나) | Connection Table 의 conn_id 와 state 필드 |
| TX path 가 stall (descriptor 처리 안 됨) | Connection Table 의 snd_wnd = 0 (peer 가 zero window) | snd_wnd 와 peer 의 ACK window 필드 |
| Timer Wheel 의 같은 슬롯에서 일부 conn 만 만료 | List traversal 도중 stop 또는 LRU 로 DRAM 에 swap-out 된 entry 누락 | Timer Wheel slot 의 list iteration 로직 |
| RTO 가 의도한 값보다 길게 발생 | Timer Wheel 의 cascade (level 1 → level 0) 시 정확도 손실 | level 1 만료 시 level 0 재등록 슬롯 계산 |
| Connection 다수 생성 후 일부 random 하게 reset | Connection Table eviction 정책이 active conn 도 evict | LRU 의 timestamp 갱신 누락 |
| OOO 버퍼 overflow 후 packet drop 안 함 | RX path 의 backpressure 가 MAC 까지 전파 안 됨 | AXI-S `tready` 신호의 흐름 |
| TX retx buffer 가 free 안 됨 → throughput 점진 하락 | RX path 의 ACK 처리가 retx buffer pointer 갱신 누락 | ACK 도착 시 snd_una 와 retx buffer release pointer |
| `tcpdump` 로 packet 정상인데 host app 못 받음 | RX DMA descriptor ring 의 producer pointer 안 올라감 | RX descriptor ring 의 head/tail pointer |
| DCMAC 백프레셔 시 TX 가 hang | TOE 의 AXI-S `tready` 응답 누락 | TOE-DCMAC 인터페이스의 valid/ready handshake |

이 체크리스트는 Module 03 (Key Functions) 와 Module 04 (DV) 에서 더 정교하게 다시 나옵니다. 지금 단계에서는 "Architecture 실패 = (Connection lookup, State atomicity, Timer wheel, DMA descriptor) 4 곳 중 하나" 라는 분류만 기억하세요.

---

## 7. 핵심 정리 (Key Takeaways)

- **TX/RX Path 분리**: 독립 pipeline → full-duplex. 한쪽 stall 이 다른 쪽을 멈추지 않음.
- **Connection Table**: 4-tuple (src/dst IP+port) → connection state. Hash 기반 lookup, O(1) 평균. **모든 packet 의 통과점**.
- **Stateful**: TCP 상태 머신을 HW 가 직접 관리 (LISTEN→SYN→ESTABLISHED→...). Reordering buffer, retransmission timer 도 HW.
- **Timer Wheel**: 수백만 RTO 를 O(1) tick 으로 처리. 개별 카운터 방식은 면적/전력 폭발.
- **Memory hierarchy**: 활성 connection state 는 SRAM, idle 은 DRAM, retx/reassembly buffer 는 DRAM. Cache hit rate 가 throughput 좌우.
- **AXI host interface**: descriptor ring (TX/RX), interrupt, doorbell. control path 는 SW, data path 는 DMA.

:::caution[실무 주의점]
- Connection Table SRAM 크기 = 동시 _활성_ 연결 수의 상한. 그 이상은 DRAM swap → latency 변동.
- Timer Wheel cascade 의 정확도는 level 1 → level 0 재등록 시 slot 계산이 핵심.
- Retx buffer 의 DRAM 대역폭은 종종 throughput 의 병목 — 채널 수와 access pattern 검토 필수.
:::
### 7.1 자가 점검

:::tip[🤔 Q1 — Timer Wheel level 설계 (Bloom: Analyze)]
TOE 가 _RTO 100ms~60s_ 처리. Single-level vs Multi-level wheel?

<details>
<summary>정답</summary>

**Multi-level cascade**.

Single-level @ 1ms tick: 60000 slot. 메모리 큼.

Multi-level:
- L0: 1ms tick × 1000 slot.
- L1: 1s tick × 60 slot.
- Cascade: L1 timer 가 _만료 1초 전_ L0 으로 _재등록_.

총 1060 slot, single 보다 _57× 적음_.

</details>
:::
:::tip[🤔 Q2 — SRAM/DRAM hierarchy (Bloom: Apply)]
100만 connection, _10만 active_. SRAM/DRAM 크기?

<details>
<summary>정답</summary>

- **Active 10만**: SRAM. 1 state ~200 byte × 100K = **20 MB SRAM**.
- **Idle 90만**: DRAM. 200 × 900K = **180 MB DRAM**.

Active 변화 시 SRAM ↔ DRAM swap. Cache hit rate 가 throughput 결정.

</details>
:::
### 7.2 출처

**External**
- IETF RFC 793 *TCP*
- *A Hierarchical Timer Wheel* — academic
- Chelsio Terminator TOE architecture

---

## 다음 단계

→ [Module 03 — TOE Key Functions](../03_toe_key_functions/): 위 architecture 위에서 5 대 기능 (Checksum / Segmentation+Reassembly / Retransmission / Flow Control / Congestion Control) 이 어떻게 동작하는지.

- 📝 [**Module 02 퀴즈**](../quiz/02_toe_architecture_quiz/)

