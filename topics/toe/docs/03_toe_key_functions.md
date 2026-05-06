# Module 03 — TOE Key Functions

<div class="learning-meta">
  <span class="meta-badge meta-level-advanced">📊 Advanced</span>
</div>

!!! objective "학습 목표"
    이 모듈을 마치면:

    - **Apply** Checksum offload (IP/TCP/UDP), TSO (TCP Segmentation Offload), LRO (Large Receive Offload)를 시나리오에 매핑
    - **Implement** ARP table 관리 + cache miss 처리 흐름
    - **Distinguish** RSS (Receive Side Scaling)와 RPS의 책임 분리
    - **Trace** Retransmission timer + RTO 계산 + duplicate ACK 기반 fast retransmit

!!! info "사전 지식"
    - [Module 01-02](01_tcp_ip_and_toe_concept.md)
    - TCP/IP detail: window, ACK, RTT/RTO

## 핵심 개념
**TOE가 HW로 처리하는 5대 기능: Checksum, Segmentation/Reassembly, Retransmission, Flow Control, Congestion Control. 각각이 패킷마다 수행되므로 HW Offload의 효과가 극대화되는 영역.**

---

## 1. Checksum — 무결성 검증

### TCP Checksum 계산

```
TCP Checksum 대상:
  Pseudo Header (IP 정보 일부) + TCP Header + TCP Payload

Pseudo Header:
  +--------+--------+--------+--------+
  | Source IP Address (32 bit)        |
  +--------+--------+--------+--------+
  | Destination IP Address (32 bit)   |
  +--------+--------+--------+--------+
  | Zero   |Protocol| TCP Length      |
  +--------+--------+--------+--------+

계산:
  1. 대상 데이터를 16-bit 워드로 분할
  2. 모든 워드를 1의 보수 합산 (carry 포함)
  3. 결과의 1의 보수 → Checksum

HW 구현:
  - 파이프라인으로 16-bit 합산 → 1 cycle/word
  - 1500B 패킷: ~94 cycles (vs SW: 수백~수천 cycles)
```

### DV 검증 포인트

| 시나리오 | 확인 사항 |
|---------|----------|
| 정상 Checksum | TX: 올바른 Checksum 삽입, RX: 검증 PASS |
| Checksum 오류 | RX: 의도적 오류 → 패킷 폐기 |
| 0-length payload | 헤더만 있는 패킷 (ACK 등) → Checksum 정확 |
| 최대 크기 패킷 (Jumbo) | 9KB 패킷 → Checksum 정확 |

---

## 2. TCP Segmentation / Reassembly

### TX: Segmentation (TSO — TCP Segmentation Offload)

```
애플리케이션: 64KB 데이터 전송 요청

SW (TSO 없이):
  커널이 64KB를 MSS(1460B) 단위로 분할
  → 45개 세그먼트 각각에 TCP/IP 헤더 생성
  → CPU 부하 큼

HW (TOE Segmentation):
  64KB를 한 번에 TOE에 전달
  TOE HW가 자동 분할:
    Segment 1: seq=0,     data[0:1459]
    Segment 2: seq=1460,  data[1460:2919]
    ...
    Segment 45: seq=64240, data[64240:65535]
  각 세그먼트에 TCP/IP 헤더 자동 생성
```

### RX: Reassembly

```
문제: 네트워크에서 패킷이 순서대로 도착하지 않을 수 있음

  수신 순서:  seg3, seg1, seg5, seg2, seg4
  기대 순서:  seg1, seg2, seg3, seg4, seg5

  Out-of-Order Buffer:
    Seq 1460 도착 (seg1 기대 중에 seg2 도착) → 버퍼에 저장
    Seq 0 도착 (seg1) → seg1 전달 + 버퍼에서 seg2도 전달
    ...
    → 순서대로 재조합하여 호스트에 전달

  HW 구현:
    - Linked list 또는 Bitmap으로 수신된 범위 추적
    - 기대 Seq와 일치하면 즉시 전달
    - 불일치하면 OOO 버퍼에 저장
```

### DV 검증 포인트

| 시나리오 | 확인 사항 |
|---------|----------|
| 순차 수신 | 분할 없이 즉시 전달 |
| Out-of-Order | 재정렬 후 순서대로 전달 |
| 중복 세그먼트 | 중복 감지 + 폐기 |
| 갭 있는 수신 | 갭 이전까지만 전달, 나머지 대기 |

---

## 3. Retransmission — 재전송

### 재전송이 필요한 경우

```
정상:
  TX: DATA(seq=100) →    RX: ACK(ack=600)
  → ACK 수신 → 재전송 버퍼에서 해당 데이터 해제

재전송 필요:
  TX: DATA(seq=100) →    (패킷 손실)    RX: (수신 못함)
  TX: (타이머 만료) → DATA(seq=100) 재전송

  또는:
  TX: DATA(100), DATA(600), DATA(1100) →
  RX: ACK(600), ACK(600), ACK(600)   ← Duplicate ACK 3개
  TX: → DATA(600) 즉시 재전송 (Fast Retransmit)
```

### HW 재전송 엔진

```
+--------------------------------------------+
| Retransmission Engine                       |
|                                             |
| 1. 재전송 버퍼                              |
|    - 전송한 세그먼트 사본 보관              |
|    - ACK 수신 시 해당 범위 해제             |
|                                             |
| 2. RTO 타이머 (Retransmission Timeout)      |
|    - 연결별 독립 타이머                     |
|    - RTT 기반 동적 계산                     |
|    - 타이머 만료 → 해당 세그먼트 재전송     |
|                                             |
| 3. Fast Retransmit                          |
|    - Duplicate ACK 3개 감지                 |
|    - 타이머 만료 전에 즉시 재전송           |
|                                             |
| 4. SACK (Selective ACK) 처리               |
|    - 손실된 세그먼트만 선택적 재전송        |
|    - 불필요한 재전송 방지                   |
+--------------------------------------------+
```

### RTO 계산 — Jacobson/Karn's Algorithm (RFC 6298)

TOE HW가 연결별로 RTO를 동적으로 계산해야 한다. SW에서는 커널이 하지만, TOE에서는 **고정소수점 연산으로 HW 구현**한다.

```
1. RTT 샘플 측정
   - 세그먼트 전송 시각 T1 기록
   - 해당 ACK 수신 시각 T2 기록
   - RTT_sample = T2 - T1

2. SRTT (Smoothed RTT) — EWMA 기반
   SRTT = (1 - α) × SRTT + α × RTT_sample     (α = 1/8)

3. RTTVAR (RTT Variance)
   RTTVAR = (1 - β) × RTTVAR + β × |SRTT - RTT_sample|  (β = 1/4)

4. RTO 계산
   RTO = SRTT + max(G, 4 × RTTVAR)
   (G = clock granularity, 보통 1ms)

5. RTO 제한
   RTO_min = 1초 (RFC 권장)
   RTO_max = 60초

Dry Run 예시:
  초기: SRTT=0, RTTVAR=0, RTO=1초(초기값)

  RTT_sample = 100ms (첫 번째 측정)
    SRTT    = 100ms
    RTTVAR  = 50ms (= RTT_sample / 2)
    RTO     = 100 + 4×50 = 300ms

  RTT_sample = 120ms (두 번째)
    SRTT    = (7/8)×100 + (1/8)×120 = 102.5ms
    RTTVAR  = (3/4)×50 + (1/4)×|102.5 - 120| = 41.875ms
    RTO     = 102.5 + 4×41.875 = 270ms

  RTT_sample = 80ms (세 번째 — RTT 감소)
    SRTT    = (7/8)×102.5 + (1/8)×80 = 99.7ms
    RTTVAR  = (3/4)×41.875 + (1/4)×|99.7 - 80| = 36.3ms
    RTO     = 99.7 + 4×36.3 = 244.9ms

HW 구현 포인트:
  - α=1/8, β=1/4 → 비트 시프트로 구현 가능 (÷8 = >>3, ÷4 = >>2)
  - 고정소수점 (예: Q16.16) 으로 정밀도 확보
  - 연결별 SRTT, RTTVAR 레지스터 → Connection Table에 저장
```

**Karn's Algorithm**: 재전송된 세그먼트의 ACK로는 RTT를 측정하지 않음 (어떤 전송의 ACK인지 모호). 재전송 시 RTO를 두 배로 증가 (Exponential Backoff).

### DV 검증 포인트 — Retransmission

| 시나리오 | 확인 사항 |
|---------|----------|
| RTO 타이머 만료 | 정확한 시간에 재전송 발생, Exponential Backoff (2배 증가) |
| Fast Retransmit | Dup ACK 3개 시점에 즉시 재전송, 2개에서는 미발생 |
| SACK 기반 재전송 | 손실 구간만 선택적 재전송, 나머지는 불필요 재전송 없음 |
| ACK 수신 → 버퍼 해제 | Cumulative ACK로 해당 범위까지 버퍼 해제 |
| Karn's Algorithm | 재전송 세그먼트 ACK로 RTT 미측정 |
| RTO 계산 정확성 | SRTT/RTTVAR 갱신값이 RFC 6298 공식과 일치 |
| 최대 재전송 횟수 | 상한(보통 15회) 초과 시 연결 RST |
| 재전송 + OOO 동시 | 재전송 세그먼트가 OOO로 도착해도 정상 처리 |

---

## 4. Flow Control — 흐름 제어

### TCP Window 기반 흐름 제어

```
수신자가 Window Size로 "내 버퍼에 여유 공간이 이만큼 있다" 알림:

  RX → TX: ACK(ack=600, window=8192)
  → TX는 최대 8192 bytes까지 전송 가능

  RX 버퍼 가득 참:
  RX → TX: ACK(ack=600, window=0)   ← Zero Window!
  → TX 전송 중단, Window Probe 타이머 시작

  RX 버퍼 여유 생김:
  RX → TX: Window Update(window=4096)
  → TX 전송 재개
```

### DV 검증 포인트

| 시나리오 | 확인 사항 |
|---------|----------|
| Zero Window | TX 전송 중단 + Window Probe 전송 |
| Window Update | TX 전송 재개, 새 Window 크기 준수 |
| Window Shrink | Window 축소 시 이미 전송된 데이터 처리 |
| Sliding Window | 전송량이 Window를 초과하지 않음 |

---

## 5. Congestion Control — 혼잡 제어

```
TCP Congestion Control 상태 머신:

  +---> Slow Start (cwnd 지수 증가)
  |        |
  |     cwnd >= ssthresh?
  |        |
  |        v
  |     Congestion Avoidance (cwnd 선형 증가)
  |        |
  |     패킷 손실 감지?
  |        |
  |        v
  +---- Fast Recovery (cwnd 반감, SACK 기반 재전송)
         또는
         Timeout → cwnd = 1 MSS, Slow Start로 복귀

  cwnd (Congestion Window): 네트워크가 허용하는 전송량
  ssthresh: Slow Start 임계값
  실제 전송량 = min(cwnd, rwnd)  (rwnd = 수신자 Window)
```

### Congestion Control 알고리즘 비교

TOE 구현 시 어떤 알고리즘을 지원할지 결정해야 한다. 각각의 특성:

```
[ TCP Reno ] — 기본, 가장 단순
  Slow Start: cwnd 1 MSS에서 시작, ACK마다 1 MSS 증가 (지수적)
  Congestion Avoidance: RTT마다 1 MSS 증가 (선형)
  Loss 감지:
    - 3 Dup ACK → cwnd = cwnd/2, ssthresh = cwnd/2, Fast Recovery
    - Timeout → cwnd = 1 MSS, ssthresh = cwnd/2, Slow Start
  약점: 다중 패킷 손실 시 성능 급락 (한 번에 하나만 복구)

[ TCP NewReno ] — Reno 개선, 대부분의 구현
  Reno와 동일하지만 Fast Recovery 개선:
    - Partial ACK (일부만 확인) → Fast Recovery 유지, 다음 손실 복구
    - Full ACK (전부 확인) → Fast Recovery 종료
  장점: 다중 손실을 한 Recovery 주기에서 처리 가능
  HW 구현: Reno 대비 추가 로직 적음 — Partial ACK 감지 + Recovery 유지

[ TCP Cubic ] — Linux 기본, 현대 표준
  핵심: cwnd를 시간의 3차 함수(cubic function)로 증가
    W(t) = C × (t - K)³ + W_max
    K = ³√(W_max × β / C)  (β = 0.7, C = 0.4)
  특성:
    - 손실 직후: 빠르게 W_max의 70%까지 회복
    - W_max 근처: 조심스럽게 접근 (plateau)
    - W_max 초과: 다시 적극적 증가 (probing)
  장점: 높은 BDP(Bandwidth-Delay Product) 네트워크에서 대역폭 활용 극대화
  HW 구현: 3차 함수 → LUT 또는 근사 연산 필요, Reno보다 복잡

  Dry Run (Cubic cwnd 변화):
    W_max = 100 MSS (이전 손실 시점), β = 0.7
    → 손실 직후: cwnd = 100 × 0.7 = 70 MSS
    → K = ³√(100 × 0.3 / 0.4) ≈ 4.2초
    → t=1s: W(1) = 0.4×(1-4.2)³ + 100 = 0.4×(-32.8) + 100 = 86.9 MSS
    → t=4s: W(4) = 0.4×(4-4.2)³ + 100 = 0.4×(-0.008) + 100 ≈ 100 MSS
    → t=6s: W(6) = 0.4×(6-4.2)³ + 100 = 0.4×5.8 + 100 = 102.3 MSS (probing)
```

### TOE에서의 알고리즘 선택

| 알고리즘 | HW 복잡도 | 성능 | 일반적 선택 |
|---------|----------|------|-----------|
| Reno | 낮음 | 보통 | 기본 지원 (필수) |
| NewReno | 낮음~중간 | 좋음 | 대부분 지원 |
| Cubic | 중간~높음 | 최고 | 고성능 TOE에서 지원 |

실무: 대부분의 TOE는 **NewReno를 기본**, 고급 TOE는 **Cubic 추가 지원**. 알고리즘 선택을 SW 설정 가능하게 하는 경우도 있음.

### HW 구현의 핵심 과제

| 과제 | 설명 |
|------|------|
| 연결별 독립 cwnd | 수백만 연결 × cwnd 상태 = 대량 메모리 |
| 타이머 관리 | 연결별 RTO 타이머 → HW 타이머 배열 |
| RTT 추정 | EWMA 기반 RTT 계산 → 고정소수점 연산 |
| SACK 처리 | SACK 블록 파싱 + 선택적 재전송 결정 |
| Cubic 연산 | 3차 함수 → LUT/근사, W_max/K 연결별 저장 |

### DV 검증 포인트 — Congestion Control

| 시나리오 | 확인 사항 |
|---------|----------|
| Slow Start 지수 증가 | ACK마다 cwnd 1 MSS 증가, 실제 전송량 확인 |
| ssthresh 전환 | cwnd ≥ ssthresh에서 Congestion Avoidance로 전환 |
| Congestion Avoidance 선형 | RTT당 cwnd 1 MSS 증가, 지수적 증가 아님 |
| 3 Dup ACK → Fast Recovery | cwnd/ssthresh 반감, 즉시 재전송 |
| Timeout → Slow Start | cwnd=1 MSS, ssthresh=cwnd/2 |
| Partial ACK (NewReno) | Fast Recovery 유지 + 다음 손실 복구 |
| min(cwnd, rwnd) 준수 | 실제 전송량이 두 윈도우 중 작은 값 이하 |
| 초기 cwnd (IW) | RFC 6928: IW = min(10×MSS, max(2×MSS, 14600)) |

---

## 6. TCP Options — TOE가 처리해야 하는 확장

TCP 기본 헤더 외에 **Options 필드**를 통해 확장 기능을 협상한다. TOE HW는 이 옵션들을 파싱하고 처리해야 한다.

### 핵심 TCP Options

```
TCP Options (SYN 패킷에서 협상, 이후 데이터 패킷에서 사용):

+------+------+--------------------------+----------------------------------+
| Kind | Len  | Option                   | TOE HW 영향                       |
+------+------+--------------------------+----------------------------------+
|  2   |  4   | MSS (Max Segment Size)   | Segmentation 단위 결정            |
|  3   |  3   | Window Scale             | Window Size 확장 (최대 1GB)       |
|  4   |  2   | SACK Permitted           | SACK 지원 여부 협상               |
|  5   | 가변 | SACK Blocks              | 선택적 재전송 범위 정보           |
|  8   | 10   | Timestamps (TSopt)       | RTT 측정 + PAWS                  |
+------+------+--------------------------+----------------------------------+
```

### Window Scale (RFC 7323)

```
문제: TCP 헤더의 Window Size는 16비트 → 최대 65,535 bytes
  100Gbps에서 RTT=1ms → BDP = 12.5MB → 65KB Window로는 부족

해결: Window Scale 옵션
  3-way Handshake 시 SYN에서 Scale Factor 교환:
    Client → SYN (Window Scale = 7) → Server
    Server → SYN+ACK (Window Scale = 8) → Client

  이후 Window Size 해석:
    실제 Window = Header_Window × 2^Scale
    예: Window=1024, Scale=7 → 실제 = 1024 × 128 = 131,072 bytes

  HW 영향:
    - Connection Table에 Scale Factor 저장 (TX용, RX용 각각)
    - Window 계산 시 시프트 연산 추가
    - 최대 Scale=14 → Window 최대 1GB (= 65535 × 2^14)
```

### SACK (Selective Acknowledgment, RFC 2018)

```
문제: Cumulative ACK만으로는 "어디까지 받았는지"만 알 수 있음
  → 하나 손실되면 그 뒤 전체를 재전송해야 할 수 있음

해결: SACK 옵션으로 수신한 범위를 명시적으로 알려줌
  수신 상태: [0-999 OK] [1000-1499 LOST] [1500-2999 OK] [3000-3499 LOST] [3500-4999 OK]
  ACK: ack=1000, SACK blocks = {1500-3000, 3500-5000}
  → TX는 1000-1499, 3000-3499만 재전송

  SACK 블록 구조 (Options 필드 내):
    +----------+----------+
    | Left Edge | Right Edge |  ← 수신된 연속 구간
    +----------+----------+
    최대 4개 블록 (Options 공간 제약: 40-12=28 bytes, 블록당 8 bytes)

  HW 영향:
    - SACK 블록 파싱 로직 (가변 길이)
    - 재전송 버퍼에서 손실 구간만 선별 전송
    - Scoreboard 자료구조로 수신/미수신 범위 추적
```

### Timestamps (RFC 7323)

```
Timestamps 옵션 — 두 가지 목적:
  1. RTTM (Round-Trip Time Measurement)
     → RTO 계산용 정밀 RTT 측정
  2. PAWS (Protection Against Wrapped Sequences)
     → 고속 네트워크에서 Sequence Number 중복 방지

  구조: TSval (송신 시각) + TSecr (에코 시각)
    TX → [TSval=1000, TSecr=500] → RX
    RX → [TSval=600, TSecr=1000] → TX
    RTT = 현재 시각 - TSecr = RTT 측정

  PAWS:
    100Gbps에서 Seq Number (32비트)가 ~17초에 한 바퀴 (wrap)
    → 이전 연결의 지연 패킷이 현재 연결에서 유효해 보일 수 있음
    → Timestamp가 단조 증가하므로, 오래된 패킷을 걸러냄

  HW 영향:
    - 패킷 송수신 시 Timestamp 삽입/추출
    - Connection Table에 TS_recent (최근 수신 Timestamp) 저장
    - PAWS 검증: 수신 TSval < TS_recent → 패킷 폐기
    - 자체 타이머 클럭 (보통 1ms 해상도)
```

### DV 검증 포인트 — TCP Options

| 시나리오 | 확인 사항 |
|---------|----------|
| MSS 협상 | SYN에서 MSS 교환 후 Segmentation 크기 반영 |
| Window Scale 적용 | Scale Factor 적용 후 실제 Window 크기 정확 |
| Window Scale=0 | 미사용 시 기본 16비트 Window 동작 |
| SACK 협상 | SYN에서 SACK Permitted 교환, 이후 SACK 블록 사용 |
| SACK 기반 선택적 재전송 | 손실 구간만 재전송, 나머지 미전송 |
| SACK 블록 4개 최대 | 5개 이상 블록 상황에서 우선순위 올바른지 |
| Timestamps RTT 측정 | TSecr 기반 RTT가 실제 왕복 시간과 일치 |
| PAWS 필터링 | 오래된 Timestamp 패킷 폐기 |
| Options 미지원 peer | 옵션 없는 SYN 수신 시 해당 기능 비활성화 |

---

## TCP 상태 머신 (FSM) — HW 구현

```
               CLOSED
                 |
        listen() | connect()
                 |
     +-----------+-----------+
     |                       |
   LISTEN              SYN_SENT
     |                       |
  SYN 수신               SYN+ACK 수신
     |                       |
  SYN_RCVD             ESTABLISHED ←---+
     |                   |   |         |
  ACK 수신           FIN 송신| FIN 수신|
     |                   |   |         |
  ESTABLISHED       FIN_WAIT_1  CLOSE_WAIT
                        |          |
                    ACK 수신    FIN 송신
                        |          |
                    FIN_WAIT_2  LAST_ACK
                        |          |
                    FIN 수신    ACK 수신
                        |          |
                    TIME_WAIT   CLOSED
                        |
                    2MSL 타이머
                        |
                      CLOSED

HW에서 이 FSM의 모든 전이를 정확하게 구현해야 함
→ 검증의 핵심 대상
```

---

## Q&A

**Q: TOE에서 가장 검증하기 어려운 기능은?**
> "재전송과 혼잡 제어다. 이유: (1) 상태 조합이 많음 — 연결 상태(FSM) × 타이머 상태 × cwnd/ssthresh × SACK 블록의 조합이 폭발적. (2) 타이밍 의존성 — RTO 타이머 만료, Fast Retransmit(Dup ACK 3개), RTT 추정이 모두 시간에 민감. (3) 에지 케이스 — Zero Window + 패킷 손실 + OOO 동시 발생 등 복합 시나리오."

**Q: Checksum Offload만으로는 부족한 이유는?**
> "Checksum은 CPU 부하의 일부에 불과하다. 100Gbps에서 진짜 병목은 Segmentation(패킷당 분할 + 헤더 생성), 재전송(타이머 관리 + 버퍼 관리), 흐름 제어(연결별 Window 추적)이다. 이 모든 것이 패킷마다 반복되므로 전체를 Offload하는 TOE가 필요하다."

**Q: TOE에서 RTO는 어떻게 계산하나?**
> "RFC 6298의 Jacobson Algorithm을 따른다. ACK 수신 시 RTT 샘플을 측정하고, EWMA로 SRTT와 RTTVAR를 갱신한 뒤 RTO = SRTT + 4×RTTVAR로 계산한다. HW에서는 α=1/8, β=1/4이 비트 시프트로 구현 가능하고, 고정소수점 연산을 쓴다. Karn's Algorithm으로 재전송 패킷의 RTT는 측정하지 않는다."

**Q: TCP Cubic이 Reno보다 나은 이유는?**
> "Reno는 선형 증가라서 높은 BDP(Bandwidth-Delay Product) 네트워크에서 대역폭을 채우는 데 오래 걸린다. Cubic은 cwnd를 시간의 3차 함수로 증가시켜, 손실 전 대역폭(W_max)까지 빠르게 회복하고 그 근처에서는 조심스럽게 접근한다. 100Gbps 환경에서 Cubic이 대역폭 활용률이 훨씬 높다."

**Q: SACK가 없으면 어떤 문제가 생기나?**
> "Cumulative ACK만으로는 '어디까지 연속으로 받았는지'만 알 수 있다. 다중 패킷 손실 시 한 번에 하나씩만 복구할 수 있어 RTT마다 하나의 손실만 해결된다. SACK는 수신 범위를 명시적으로 알려주므로 손실 구간만 선택적으로 재전송할 수 있어 복구 속도가 크게 향상된다."

---

## 확인 퀴즈

**Q1.** TCP Checksum 계산에서 "Pseudo Header"가 포함되는 이유는 무엇인가?

<details>
<summary>정답</summary>

Pseudo Header에는 Source IP, Destination IP, Protocol, TCP Length가 포함된다. 이를 Checksum에 포함시키는 이유는 IP 헤더의 주소가 전송 중 변조되어 패킷이 잘못된 호스트에 도달해도 TCP가 이를 감지할 수 있게 하기 위함이다. 즉, TCP Checksum이 IP 계층의 정보까지 보호하여 end-to-end 무결성을 강화한다.
</details>

**Q2.** 아래 상황에서 RX Reassembly 모듈의 동작을 추적하라(dry run).

```
기대 다음 seq = 0
수신 순서: seg(seq=1460), seg(seq=4380), seg(seq=0), seg(seq=2920)
```

<details>
<summary>정답</summary>

```
1. seg(seq=1460) 수신: 기대 seq=0 ≠ 1460 → OOO 버퍼에 저장
   버퍼: [1460-2919]  |  전달: 없음  |  ACK: ack=0 (기대 seq 변동 없음)

2. seg(seq=4380) 수신: 기대 seq=0 ≠ 4380 → OOO 버퍼에 저장
   버퍼: [1460-2919, 4380-5839]  |  전달: 없음  |  ACK: ack=0

3. seg(seq=0) 수신: 기대 seq=0 == 0 → 즉시 전달!
   seg(seq=0) 전달 → OOO 버퍼에서 연속 확인
   seg(seq=1460) 도 연속 → 전달!
   seg(seq=2920)은 없음 → 중단
   버퍼: [4380-5839]  |  전달: seg0+seg1460  |  ACK: ack=2920

4. seg(seq=2920) 수신: 기대 seq=2920 == 2920 → 즉시 전달!
   OOO 버퍼에서 연속 확인: seg(seq=4380) 연속 → 전달!
   버퍼: 비어있음  |  전달: seg2920+seg4380  |  ACK: ack=5840
```
</details>

**Q3.** RTO 계산에서 α=1/8, β=1/4를 사용하는 이유가 "HW 구현 용이성"이라고 했다. 구체적으로 HW에서 어떻게 구현되는가?

<details>
<summary>정답</summary>

1/8 = 2^(-3), 1/4 = 2^(-2)이므로 나눗셈 대신 **비트 우측 시프트(>>3, >>2)**로 구현 가능하다.
- `SRTT = SRTT - (SRTT >> 3) + (RTT_sample >> 3)` — 곱셈/나눗셈 없이 시프트+가감산만
- `RTTVAR = RTTVAR - (RTTVAR >> 2) + (|SRTT - RTT_sample| >> 2)`
- 고정소수점(예: Q16.16)으로 소수점 이하 정밀도 확보
- 연결별 SRTT, RTTVAR를 Connection Table에 저장하고, ACK 수신 시 갱신
</details>

**Q4. (사고력)** TCP Cubic에서 cwnd가 W_max 근처에서 "조심스럽게" 접근하는 것이 왜 중요한가? Reno처럼 선형으로 계속 증가하면 어떤 문제가 생기나?

<details>
<summary>정답</summary>

W_max는 이전에 패킷 손실이 발생한 지점이므로, 네트워크 용량의 상한에 가깝다. 이 근처에서 적극적으로 cwnd를 증가시키면 다시 손실이 발생할 확률이 높다. Cubic은 W_max 근처에서 증가율을 3차 함수의 변곡점으로 최소화하여 "안전 탐색"하고, W_max를 넘어서면 다시 적극적으로 probing한다. Reno는 선형이라 W_max 근처에서도 동일한 속도로 증가하여 손실이 반복될 수 있고, W_max까지 도달하는 데도 오래 걸린다(높은 BDP에서 수십 초~분).
</details>

**Q5.** SACK 블록이 최대 4개로 제한되는 이유를 TCP 헤더 구조 관점에서 설명하라.

<details>
<summary>정답</summary>

TCP Options 필드는 최대 40바이트(헤더 최대 60B - 고정 20B). Timestamps 옵션이 10B + 2B(NOP 패딩) = 12B를 사용하면 SACK에 남는 공간은 28B. SACK 옵션 헤더가 2B(Kind+Length), 각 블록이 8B(Left Edge 4B + Right Edge 4B)이므로 (28-2)/8 = 3.25 → 최대 3개(Timestamps 사용 시) 또는 4개(Timestamps 미사용 시). 따라서 물리적 공간 제약으로 4개가 상한이다.
</details>

---

## 핵심 정리

- **5대 기능**: Checksum, Segmentation/Reassembly, Retransmission, Flow Control, Congestion Control.
- **Checksum offload**: IP/TCP/UDP 모두. TX는 zero-fill 후 HW가 채움, RX는 HW가 검증 → status에 보고.
- **TSO (Large Send)**: SW가 큰 buffer (64KB) 보내면 HW가 MTU 단위(1500)로 자동 분할. CPU SW segmentation 회피.
- **LRO (Large Receive)**: HW가 연속된 segment를 합쳐 SW에 한 번에 전달. Receive overhead ↓.
- **RSS**: incoming flow를 multi-queue로 분산. 5-tuple hash로 queue 결정 → multi-core scale.
- **Retransmission**: RTO timer expire 또는 3 dup ACK → fast retransmit.

## 다음 단계

- 📝 [**Module 03 퀴즈**](quiz/03_toe_key_functions_quiz.md)
- ➡️ [**Module 04 — DV Methodology**](04_toe_dv_methodology.md)

<div class="chapter-nav">
  <a class="nav-prev" href="../02_toe_architecture/">
    <div class="nav-label">◀ 이전</div>
    <div class="nav-title">TOE 아키텍처</div>
  </a>
  <a class="nav-next" href="../04_toe_dv_methodology/">
    <div class="nav-label">다음 ▶</div>
    <div class="nav-title">TOE DV 검증 전략</div>
  </a>
</div>
