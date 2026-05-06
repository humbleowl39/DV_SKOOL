# Unit 2: TOE 아키텍처

<div class="learning-meta">
  <span class="meta-badge meta-time">⏱ 17분</span>
  <span class="meta-badge meta-level-advanced">📊 Advanced</span>
</div>

## 핵심 개념
**TOE = TCP 상태 머신을 HW로 구현한 엔진. TX Path(송신)와 RX Path(수신)에서 각각 Segmentation/Checksum/흐름 제어를 처리하고, Connection Table로 수천~수백만 연결을 동시 관리.**

---

## TOE 전체 블록 다이어그램

```
+------------------------------------------------------------------+
|                          TOE Engine                               |
|                                                                   |
|  Host Interface (PCIe / AXI)                                      |
|  +----+----+                                                      |
|  | DMA     |  ← 호스트 메모리 ↔ TOE 버퍼 전송                    |
|  | Engine  |                                                      |
|  +----+----+                                                      |
|       |                                                           |
|  +----+--------------------------------------------+              |
|  |              Connection Table                    |              |
|  |  (TCP 연결별 상태: seq/ack/window/timer/state)   |              |
|  |  수천~수백만 엔트리                               |              |
|  +----+--------------------------------------------+              |
|       |                    |                                      |
|  +----+--------+    +-----+--------+                              |
|  | TX Path     |    | RX Path      |                              |
|  |             |    |              |                              |
|  | Segmentation|    | Reassembly   |                              |
|  | Checksum Gen|    | Checksum Ver |                              |
|  | ACK Process |    | ACK Generate |                              |
|  | Retx Engine |    | Flow Control |                              |
|  | Window Mgmt |    | Seq Validate |                              |
|  +----+--------+    +-----+--------+                              |
|       |                    |                                      |
|  +----+--------------------+----+                                 |
|  |       MAC Interface          |  ← DCMAC / Ethernet MAC        |
|  |    (Ethernet Frame TX/RX)    |                                 |
|  +------------------------------+                                 |
+------------------------------------------------------------------+
```

---

## TX Path (송신 경로)

```
애플리케이션 데이터 (예: 64KB)
         |
         v
+---------------------------+
| 1. DMA: 호스트 → TOE 버퍼 |
+---------------------------+
         |
         v
+---------------------------+
| 2. TCP Segmentation       |
|    64KB → MSS 단위 분할   |
|    MSS = 1460B (일반적)   |
|    → 약 45개 세그먼트     |
+---------------------------+
         |
         v
+---------------------------+
| 3. TCP 헤더 생성          |
|    - Seq Number 할당      |
|    - Window Size 삽입     |
|    - Flags 설정           |
+---------------------------+
         |
         v
+---------------------------+
| 4. IP 헤더 생성           |
|    - Src/Dst IP           |
|    - Total Length          |
|    - TTL, Protocol=TCP    |
+---------------------------+
         |
         v
+---------------------------+
| 5. Checksum 계산          |
|    - TCP Checksum         |
|    - IP Header Checksum   |
+---------------------------+
         |
         v
+---------------------------+
| 6. 재전송 버퍼에 사본 보관 |
|    (ACK 올 때까지 유지)   |
+---------------------------+
         |
         v
    MAC로 전송 (Ethernet Frame)
```

## RX Path (수신 경로)

```
MAC에서 Ethernet Frame 수신
         |
         v
+---------------------------+
| 1. IP/TCP Checksum 검증   |
|    불일치 → 폐기          |
+---------------------------+
         |
         v
+---------------------------+
| 2. Connection Lookup      |
|    (SrcIP:Port, DstIP:Port)|
|    → Connection Table에서  |
|      해당 연결 상태 조회   |
+---------------------------+
         |
         v
+---------------------------+
| 3. Sequence Number 검증   |
|    - 기대 범위 내?        |
|    - 중복? 순서 벗어남?   |
+---------------------------+
         |
         v
+---------------------------+
| 4. TCP 상태 처리          |
|    - ACK 처리 (TX 버퍼해제)|
|    - Window Update        |
|    - SYN/FIN/RST 처리     |
+---------------------------+
         |
         v
+---------------------------+
| 5. Reassembly             |
|    - 순서대로 조합         |
|    - Out-of-Order 버퍼링  |
+---------------------------+
         |
         v
+---------------------------+
| 6. DMA: TOE 버퍼 → 호스트 |
+---------------------------+
```

---

## Connection Table — 연결 상태 관리

### 엔트리 구조

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

### Connection Lookup 방법

| 방법 | 원리 | 속도 | 메모리 |
|------|------|------|--------|
| Hash Table | 4-tuple 해시 → 인덱스 | O(1) 평균 | 중간 |
| CAM (Content Addressable Memory) | 병렬 매칭 | O(1) 보장 | 큼 (비쌈) |
| TCAM | 와일드카드 매칭 가능 | O(1) 보장 | 매우 큼 |

**실무**: 대부분의 TOE는 **Hash Table** 사용 — 비용 효율적이고 충분히 빠름. 충돌은 체이닝으로 처리.

---

## 타이머 관리 아키텍처 — 수백만 연결의 RTO

TOE가 수백만 TCP 연결을 관리할 때, 각 연결별 RTO 타이머를 HW에서 어떻게 효율적으로 구현하는지가 핵심 설계 과제다.

### 순수 개별 타이머 (비현실적)

```
연결 100만 개 × 개별 타이머 = 100만 개 카운터
  - 매 클럭마다 100만 개 카운터 감소 검사 → 불가능
  - 면적/전력 폭발
```

### Timer Wheel (Hashed Timing Wheel) — 실무 표준

```
핵심 아이디어: 시간을 슬롯으로 나누고, 만료 시점에 해당하는 슬롯에 연결을 등록

  Timer Wheel 구조 (예: 256 슬롯, 1ms 해상도):

  현재 시각 포인터 (tick마다 1칸 전진)
       ↓
  [0] → conn_A → conn_D → NULL
  [1] → conn_B → NULL
  [2] → NULL
  [3] → conn_C → conn_E → NULL
  ...
  [255] → conn_F → NULL

  동작:
    1. 타이머 등록: RTO=300ms인 conn_X → 슬롯 (현재+300) % 256에 삽입
    2. Tick: 매 1ms마다 포인터 1칸 전진
    3. 만료 확인: 현재 슬롯의 연결 리스트 순회 → 만료된 연결 처리
    4. 갱신: ACK 수신 시 기존 슬롯에서 제거 → 새 슬롯에 삽입

  계층적 Timer Wheel (큰 RTO 범위 지원):
    Level 0: 1ms 해상도, 256 슬롯 (0~255ms)
    Level 1: 256ms 해상도, 256 슬롯 (0~65초)
    → Level 1 만료 → Level 0으로 재등록 (cascade)

  복잡도:
    등록/삭제: O(1)
    Tick당 처리: 평균 O(1) (슬롯당 연결 수가 균등 분포일 때)
    메모리: 슬롯 수 × 포인터 + 연결별 링크 (Connection Table에 통합)
```

### DV 검증 포인트 — 타이머

| 시나리오 | 확인 사항 |
|---------|----------|
| 정확한 만료 시점 | RTO 설정값과 실제 만료 시각 차이 ≤ 1 tick |
| ACK 수신 → 타이머 취소 | ACK 후 해당 연결의 재전송 미발생 |
| Exponential Backoff | 재전송마다 RTO 2배 증가 |
| 다수 연결 동시 만료 | 같은 슬롯에 여러 연결 → 모두 처리 |
| 타이머 갱신 (재시작) | 새 데이터 전송 시 타이머 리셋 |

---

## 메모리 아키텍처 — 버퍼와 테이블 배치

TOE 성능은 메모리 대역폭과 용량에 크게 의존한다. On-chip(SRAM)과 Off-chip(DRAM)을 적절히 분배하는 것이 설계 핵심.

```
메모리 계층:

  +--------------------------------------------------+
  |              On-Chip SRAM (빠름, 비쌈, 작음)       |
  |                                                    |
  |  Connection Table (Hot Entries)                    |
  |    - 활성 연결의 상태 (Seq/ACK/Window/Timer)      |
  |    - 빠른 조회 필수 → SRAM 또는 레지스터           |
  |    - 예: 활성 연결 1만 개 × 128B = ~1.2MB         |
  |                                                    |
  |  Timer Wheel                                       |
  |    - 슬롯 배열 + 포인터 → 소량 SRAM               |
  |                                                    |
  |  패킷 버퍼 (Small)                                |
  |    - 현재 처리 중인 패킷 (파이프라인 버퍼)        |
  |    - 수 KB ~ 수십 KB                               |
  +--------------------------------------------------+
                        |
                        | (Cache / Spill)
                        v
  +--------------------------------------------------+
  |            Off-Chip DRAM (느림, 저렴, 큼)          |
  |                                                    |
  |  Connection Table (Cold Entries)                   |
  |    - 비활성/대기 연결 → DRAM에 swap               |
  |    - 예: 전체 100만 연결 × 128B = ~128MB          |
  |                                                    |
  |  재전송 버퍼 (TX Retransmit Buffer)               |
  |    - ACK 대기 중인 세그먼트 사본                  |
  |    - 연결별 수 KB ~ 수 MB → 전체 수 GB            |
  |                                                    |
  |  RX Reassembly 버퍼                               |
  |    - Out-of-Order 세그먼트 임시 저장              |
  |    - 연결별 수 KB                                 |
  +--------------------------------------------------+

설계 트레이드오프:
  - SRAM 증가 → 성능↑, 면적/비용↑
  - DRAM 의존 → 비용↓, 지연↑ (메모리 컨트롤러 경유)
  - 캐싱 전략: 활성 연결을 SRAM에 유지, LRU로 교체
  - 100Gbps 달성: 재전송 버퍼 대역폭이 병목 → DRAM 채널 수 중요
```

### DV 검증 포인트 — 메모리

| 시나리오 | 확인 사항 |
|---------|----------|
| Connection Table 가득 참 | 새 연결 거부 또는 LRU 교체 정상 동작 |
| SRAM ↔ DRAM 스왑 | 비활성 연결 swap-out 후 재활성화 시 상태 일관성 |
| 재전송 버퍼 오버플로 | 버퍼 한계 시 오래된 데이터 폐기 정책 |
| OOO 버퍼 가득 참 | 추가 OOO 패킷 처리 (폐기 또는 ACK으로 재요청) |

---

## HW/SW 분리 — Control Path vs Data Path

```
+------------------------------------------------------------------+
|  Control Path (SW — CPU)         Data Path (HW — TOE)             |
|                                                                   |
|  - 연결 수립/해제               - Checksum 계산/검증              |
|    (3-way/4-way handshake)      - Segmentation/Reassembly        |
|  - 연결 정책 설정               - ACK 생성/처리                   |
|  - 예외 처리                    - 재전송 (타이머 + 재전송)        |
|  - 통계/모니터링                - 흐름/혼잡 제어                  |
|                                 - DMA 전송                        |
|                                                                   |
|  빈도: 연결당 1-2회             빈도: 패킷당 매번                 |
|  지연 허용: ms 단위             지연 요구: ns~μs 단위             |
+------------------------------------------------------------------+

핵심: "자주 발생하는 Data Path를 HW로, 드문 Control Path를 SW로"
```

---

## TOE와 DCMAC 연동 (이력서 연결)

```
MangoBoost 환경:

  +--------+     +---------+     +--------+
  | Host   | --> | TOE     | --> | DCMAC  | --> Ethernet
  | (CPU)  |     | Engine  |     | (MAC)  |    100Gbps+
  |        | <-- |         | <-- | (AMD)  | <--
  +--------+     +---------+     +--------+

  DCMAC (AMD):
    - 100/200/400Gbps Ethernet MAC
    - Ethernet Frame 송수신
    - FCS (Frame Check Sequence) 처리
    - Pause Frame (흐름 제어)

  TOE ↔ DCMAC 인터페이스:
    - AXI-Stream 기반
    - TX: TOE → DCMAC (TCP 세그먼트 → Ethernet Frame)
    - RX: DCMAC → TOE (Ethernet Frame → TCP 세그먼트)

  검증 포인트:
    - TOE와 DCMAC 간 AXI-S 핸드셰이크 정확성
    - Frame 크기, 정렬, 패딩 정확성
    - 백프레셔 (DCMAC busy 시 TOE 대기)
    - 에러 전파 (CRC 에러 → TOE에 통지)
```

---

## Q&A

**Q: TOE의 HW/SW 분리 원칙은?**
> "Data Path와 Control Path를 분리한다. 패킷마다 발생하는 반복 작업(Checksum, Segmentation, ACK, 재전송)은 HW로 Offload하고, 연결당 1-2회 발생하는 제어 작업(연결 수립/해제, 정책 설정)은 SW가 담당한다. 핵심은 '빈도 높은 것 = HW, 빈도 낮은 것 = SW'이다."

**Q: Connection Table이 중요한 이유는?**
> "TOE는 수천~수백만 TCP 연결을 동시에 관리해야 한다. 각 연결의 상태(Seq/ACK Number, Window, Timer, FSM State)를 Connection Table에 저장하고, 패킷 수신 시 4-tuple(Src/Dst IP:Port) 해시로 O(1)에 조회한다. 이 테이블의 크기와 조회 속도가 TOE의 동시 연결 처리 능력을 결정한다."

**Q: 수백만 연결의 RTO 타이머를 HW에서 어떻게 관리하나?**
> "Timer Wheel 자료구조를 사용한다. 시간을 슬롯으로 나누고, 각 연결의 RTO 만료 시점에 해당하는 슬롯에 등록한다. 매 tick마다 포인터가 1칸 전진하면서 해당 슬롯의 연결만 확인하므로, 연결 수와 무관하게 tick당 O(1) 처리가 가능하다. 큰 RTO 범위는 계층적 Timer Wheel(cascade)로 지원한다."

**Q: TOE의 메모리를 어떻게 설계하나?**
> "On-chip SRAM과 Off-chip DRAM을 계층적으로 사용한다. 활성 연결의 Connection Table과 파이프라인 버퍼는 SRAM에 두어 빠른 조회를 보장하고, 비활성 연결과 재전송 버퍼는 DRAM에 둔다. 활성/비활성 연결을 LRU로 교체하는 캐싱 전략이 핵심이다. 100Gbps 달성을 위해 DRAM 대역폭(특히 재전송 버퍼)이 병목이 되지 않도록 다중 채널을 사용한다."

---

## 확인 퀴즈

**Q1.** TX Path에서 애플리케이션 64KB 데이터가 MAC으로 나가기까지 거치는 6단계를 순서대로 나열하라.

<details>
<summary>정답</summary>

1. DMA: 호스트 메모리 → TOE 버퍼 전송
2. TCP Segmentation: 64KB → MSS(1460B) 단위 약 45개 세그먼트로 분할
3. TCP 헤더 생성: Seq Number, Window Size, Flags 할당
4. IP 헤더 생성: Src/Dst IP, Total Length, TTL, Protocol
5. Checksum 계산: TCP Checksum + IP Header Checksum
6. 재전송 버퍼에 사본 보관 (ACK 대기) → MAC으로 전송
</details>

**Q2.** Connection Lookup에서 Hash Table과 CAM(Content Addressable Memory)의 트레이드오프를 설명하고, 실무에서 Hash Table이 더 많이 사용되는 이유를 서술하라.

<details>
<summary>정답</summary>

Hash Table: 4-tuple 해시로 O(1) 평균 조회, 메모리 비용 중간, 충돌 시 체이닝으로 O(n) 최악. CAM: 병렬 매칭으로 O(1) 보장, 하지만 면적/전력/비용이 매우 높음. 실무에서는 Hash Table이 비용 효율적이고 수백만 연결에도 충분히 빠르며, 해시 충돌은 통계적으로 드물어 체이닝으로 해결 가능하므로 대부분의 TOE가 Hash Table을 선택한다.
</details>

**Q3.** Timer Wheel의 동작 원리를 설명하라. 연결 100만 개의 RTO 타이머를 개별 카운터로 관리하면 안 되는 이유는?

<details>
<summary>정답</summary>

개별 카운터: 매 클럭마다 100만 개 카운터를 감소/만료 검사해야 하므로 면적/전력이 폭발적으로 증가한다. Timer Wheel: 시간을 슬롯으로 나누어 만료 시점의 슬롯에 연결을 등록한다. 매 tick마다 포인터가 1칸 전진하면서 해당 슬롯의 연결만 처리하므로 tick당 O(1)(평균). 등록/삭제도 O(1). 큰 RTO 범위는 계층적(cascade) 구조로 지원한다.
</details>

**Q4. (사고력)** TOE의 Connection Table이 SRAM에 1만 엔트리만 들어가는데, 실제 연결이 100만 개라면 어떤 문제가 발생하고 어떻게 해결하나?

<details>
<summary>정답</summary>

활성 연결이 SRAM 용량을 초과하면 DRAM에 swap-out해야 한다. LRU(Least Recently Used) 정책으로 최근 사용되지 않은 연결을 DRAM으로 내리고, 패킷 수신 시 해당 연결이 SRAM에 없으면 DRAM에서 swap-in한다. 이때 DRAM 접근 지연(수백 ns)이 발생하므로 패킷 처리 파이프라인에 스톨이 생긴다. 이를 완화하기 위해 prefetch(다음 패킷의 연결을 미리 로드)나 DRAM 다중 채널로 대역폭을 확보한다. 검증에서는 swap 빈번 발생 시나리오에서 상태 일관성과 성능 저하 정도를 확인해야 한다.
</details>

<div class="chapter-nav">
  <a class="nav-prev" href="01_tcp_ip_and_toe_concept.md">
    <div class="nav-label">◀ 이전</div>
    <div class="nav-title">TCP/IP 기본 + TOE 개념</div>
  </a>
  <a class="nav-next" href="03_toe_key_functions.md">
    <div class="nav-label">다음 ▶</div>
    <div class="nav-title">TOE 핵심 기능 상세</div>
  </a>
</div>
