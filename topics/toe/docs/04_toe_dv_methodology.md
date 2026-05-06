# Unit 4: TOE DV 검증 전략

<div class="learning-meta">
  <span class="meta-badge meta-level-advanced">📊 Advanced</span>
</div>

## 핵심 개념
**TOE 검증 = 프로토콜 준수(TCP/IP RFC) + 기능 정확성(상태 머신, 데이터 무결성) + 성능(처리량, 지연) + 에러 복구(패킷 손실, 재전송). 네트워크 프로토콜의 비결정론적 특성(패킷 손실, 순서 변경, 지연)이 검증 난이도를 높이는 핵심 요인.**

---

## 검증 환경 아키텍처

```
+------------------------------------------------------------------+
|                    TOE UVM Verification Env                        |
|                                                                   |
|  +------------------+  +------------------+                       |
|  | Host Agent       |  | Network Agent    |                       |
|  | (TX/RX 요청)     |  | (Peer TCP 역할)  |                       |
|  |                  |  |                  |                       |
|  | - 데이터 생성    |  | - 패킷 응답     |                       |
|  | - 연결 제어      |  | - ACK 생성      |                       |
|  | - AXI 인터페이스 |  | - 패킷 손실주입 |                       |
|  +--------+---------+  | - OOO 주입      |                       |
|           |             | - AXI-S 인터페이스|                      |
|           |             +--------+---------+                       |
|           |                      |                                |
|           v                      v                                |
|  +------------------------------------------------------------+  |
|  |                    DUT (TOE Engine)                          |  |
|  +------------------------------------------------------------+  |
|           |                      |                                |
|           v                      v                                |
|  +------------------------------------------------------------+  |
|  |              Scoreboard / Protocol Checker                  |  |
|  |                                                             |  |
|  |  - 데이터 무결성: TX 데이터 == RX 데이터?                   |  |
|  |  - TCP 프로토콜: RFC 793/5681/7323 준수?                   |  |
|  |  - Seq/ACK 정확성: 기대 번호 vs 실제                       |  |
|  |  - TCP Reference Model (C/Python)                          |  |
|  +------------------------------------------------------------+  |
|           |                                                       |
|           v                                                       |
|  +------------------------------------------------------------+  |
|  |              Functional Coverage                             |  |
|  +------------------------------------------------------------+  |
+------------------------------------------------------------------+
```

---

## 핵심 테스트 시나리오

### Positive (정상 동작)

| 카테고리 | 시나리오 | 검증 포인트 |
|---------|---------|-----------|
| **연결** | 3-way handshake 정상 | SYN→SYN+ACK→ACK 상태 전이 |
| | 4-way handshake 해제 | FIN 시퀀스 + TIME_WAIT |
| **데이터** | 단일 세그먼트 전송 | Seq/ACK, Checksum, 데이터 일치 |
| | 대량 데이터 (Bulk) | Segmentation + 순서 보장 |
| | 양방향 동시 전송 | Full-duplex 정확 동작 |
| **흐름** | Window 기반 전송 제한 | Window 초과 전송 없음 |
| | Window Update 후 재개 | 업데이트 즉시 반영 |

### Negative / 에러 시나리오

| 카테고리 | 시나리오 | 검증 포인트 |
|---------|---------|-----------|
| **패킷 손실** | TX 패킷 드롭 | RTO 타이머 → 재전송 |
| | ACK 패킷 드롭 | Dup ACK or RTO → 재전송 |
| **순서** | Out-of-Order 수신 | Reassembly 정확 + ACK 정확 |
| | 중복 패킷 수신 | 중복 감지 + 폐기 |
| **무결성** | Checksum 오류 패킷 | 패킷 폐기, 재전송 유도 |
| | 잘린 패킷 (Truncated) | 정상 에러 처리 |
| **흐름** | Zero Window | 전송 중단 + Probe |
| | RST 수신 | 연결 즉시 해제 |
| **혼잡** | Dup ACK 3개 (Fast Retx) | 즉시 재전송 + cwnd 조정 |
| | Timeout (Slow Start 복귀) | cwnd=1 MSS, ssthresh 조정 |

### Stress / 성능 시나리오

| 시나리오 | 측정 항목 |
|---------|----------|
| 최대 동시 연결 | Connection Table 한계 |
| 라인 레이트 전송 | Throughput 100Gbps 도달? |
| 다수 연결 × 동시 전송 | 처리량 유지, 공정성 |
| 패킷 손실률 변화 (1%, 5%, 10%) | 재전송 효율, 처리량 변화 |

---

## Coverage Model

```
[CG1] TCP FSM Coverage
  - cp_state: {CLOSED, LISTEN, SYN_SENT, SYN_RCVD, ESTABLISHED,
               FIN_WAIT_1, FIN_WAIT_2, CLOSE_WAIT, LAST_ACK, TIME_WAIT}
  - cp_transition: 모든 유효한 상태 전이 쌍
  → 모든 FSM 전이가 커버되었는가?

[CG2] Data Transfer Coverage
  - cp_segment_size: {MIN(1B), TYPICAL(1460B), MSS, JUMBO(9000B)}
  - cp_direction: {TX_ONLY, RX_ONLY, BIDIRECTIONAL}
  - cp_data_volume: {SINGLE_SEG, SMALL(<10KB), MEDIUM, LARGE(>1MB)}
  - cross: segment_size × direction × data_volume

[CG3] Error/Recovery Coverage
  - cp_error_type: {PKT_LOSS, DUP_ACK, CHECKSUM_ERR, OOO, RST, TIMEOUT}
  - cp_recovery: {RETX_RTO, FAST_RETX, PKT_DROP, CONN_RESET}
  - cross: error_type × recovery

[CG4] Flow/Congestion Coverage
  - cp_window_state: {NORMAL, ZERO_WINDOW, WINDOW_UPDATE, SHRINK}
  - cp_congestion_state: {SLOW_START, CONG_AVOID, FAST_RECOVERY}
  - cross: window_state × congestion_state

[CG5] Connection Scale Coverage
  - cp_num_connections: {1, 10, 100, 1000, MAX}
  - cp_concurrent_activity: {IDLE, LOW, MEDIUM, HIGH, FULL}
```

---

## Reference Model — TCP 동작의 기준 모델

Scoreboard가 DUT 출력을 비교하려면 **기대값(expected)**이 필요하다. TCP는 프로토콜 자체가 복잡하므로, 별도의 Reference Model이 기대값을 생성한다.

```
Reference Model 구조:

  +------------------+        +------------------+
  | Host Agent       |        | Network Agent    |
  | (TX/RX 요청)     |        | (Peer TCP 역할)  |
  +--------+---------+        +--------+---------+
           |                           |
           v                           v
  +------------------------------------------------------------+
  |                    DUT (TOE Engine)                          |
  +------------------------------------------------------------+
           |                           |
           v                           v
  +------------------------------------------------------------+
  |                     Scoreboard                              |
  |  +--------------------------------------------------+      |
  |  | TCP Reference Model (C/C++ or SystemVerilog DPI) |      |
  |  |                                                  |      |
  |  |  입력: Host Agent가 보내는 TX 요청               |      |
  |  |        Network Agent가 보내는 수신 패킷          |      |
  |  |  내부: TCP 상태 머신 시뮬레이션                   |      |
  |  |        Seq/ACK 추적, Window 관리, 재전송 로직    |      |
  |  |  출력: 기대 TX 패킷 (seq, ack, flags, data)     |      |
  |  |        기대 RX 데이터 (호스트에 전달될 데이터)   |      |
  |  +--------------------------------------------------+      |
  |                                                             |
  |  비교:                                                      |
  |    DUT TX 패킷 vs Reference TX 패킷                        |
  |    DUT RX 데이터 vs Reference RX 데이터                    |
  |    허용 범위: 타이밍 차이 OK, 데이터/프로토콜 차이 FAIL    |
  +------------------------------------------------------------+

구현 방식:
  1. C/C++ 모델 + DPI-C: Linux TCP 스택 축소판, DPI로 SV에서 호출
     장점: 기존 TCP 코드 재사용, 정밀
     단점: 유지보수 복잡

  2. SystemVerilog 모델: SV로 TCP FSM + Seq/ACK 로직 직접 구현
     장점: 디버그 용이 (같은 시뮬레이터)
     단점: 개발 비용 높음

  3. Python 모델 + Socket: Python Scapy 등으로 패킷 생성/파싱
     장점: 빠른 개발, 유연
     단점: co-simulation 오버헤드

실무에서 가장 흔한 조합: C++ Reference Model + DPI-C
```

---

## Scoreboard 설계 — 트랜잭션 레벨 비교

```
TOE Scoreboard 핵심 비교 항목:

class toe_scoreboard extends uvm_scoreboard;

  // 비교 큐: DUT 출력 vs Reference Model 기대값
  uvm_tlm_analysis_fifo #(tcp_segment) dut_tx_fifo;     // DUT가 송신한 패킷
  uvm_tlm_analysis_fifo #(tcp_segment) ref_tx_fifo;     // Reference가 예측한 패킷
  uvm_tlm_analysis_fifo #(tcp_data)    dut_rx_data_fifo; // DUT가 호스트에 전달한 데이터
  uvm_tlm_analysis_fifo #(tcp_data)    ref_rx_data_fifo; // Reference 예측 데이터

  task compare_tx();
    tcp_segment dut_seg, ref_seg;
    forever begin
      dut_tx_fifo.get(dut_seg);
      ref_tx_fifo.get(ref_seg);

      // 1. 데이터 무결성
      assert(dut_seg.payload == ref_seg.payload)
        else `uvm_error("SB", $sformatf("TX payload mismatch: seq=%0d", dut_seg.seq))

      // 2. TCP 헤더 필드
      assert(dut_seg.seq_num  == ref_seg.seq_num)   // Sequence Number
      assert(dut_seg.ack_num  == ref_seg.ack_num)   // ACK Number
      assert(dut_seg.flags    == ref_seg.flags)      // SYN/ACK/FIN/RST
      assert(dut_seg.window   == ref_seg.window)     // Window Size

      // 3. Checksum (DUT가 계산, Reference가 예측)
      assert(dut_seg.checksum == ref_seg.checksum)

      // 4. 타이밍은 정확 일치 불필요 — 허용 범위 내 확인
      assert(abs(dut_seg.time - ref_seg.time) < TIMING_TOLERANCE)
    end
  endtask

비교 전략:
  - 데이터 무결성: byte-by-byte 정확 일치 (허용 오차 없음)
  - 프로토콜 필드: Seq/ACK/Flags 정확 일치
  - 타이밍: 허용 범위 내 (HW 파이프라인 지연 고려)
  - 순서: 재전송 패킷의 순서는 유연하게 처리 (out-of-order 허용)
```

---

## SVA (SystemVerilog Assertions) — 프로토콜 준수 검증

Coverage Model이 "어떤 상황을 겪었는지" 추적한다면, SVA는 "매 순간 규칙을 지키는지" 감시한다.

```systemverilog
// === TCP 프로토콜 준수 SVA 예시 ===

module toe_protocol_checker (
  input logic        clk, rst_n,
  input logic        tx_valid, tx_ready,
  input logic [31:0] tx_seq_num, tx_ack_num,
  input logic [15:0] tx_window,
  input logic [5:0]  tx_flags,  // {URG, ACK, PSH, RST, SYN, FIN}
  input logic        rx_valid,
  input logic [31:0] rx_seq_num, rx_ack_num,
  input logic [15:0] rx_window
);

  // 1. SYN에는 반드시 ACK가 응답 (3-way handshake)
  //    SYN 수신 후 일정 시간 내 SYN+ACK 송신
  property syn_gets_synack;
    @(posedge clk) disable iff (!rst_n)
    (rx_valid && rx_flags[1] && !rx_flags[4])  // SYN 수신 (SYN=1, ACK=0)
    |-> ##[1:SYN_RESPONSE_TIMEOUT]
        (tx_valid && tx_flags[1] && tx_flags[4]); // SYN+ACK 송신
  endproperty
  assert property (syn_gets_synack)
    else `uvm_error("SVA", "SYN received but no SYN+ACK response");

  // 2. Zero Window 시 데이터 전송 금지
  property no_data_on_zero_window;
    @(posedge clk) disable iff (!rst_n)
    (peer_window == 0 && tx_valid && tx_payload_len > 0)
    |-> (tx_flags[1] || tx_flags[0]);  // Zero Window에서 허용: ACK, FIN만
  endproperty
  assert property (no_data_on_zero_window)
    else `uvm_error("SVA", "Data sent during Zero Window");

  // 3. ACK Number는 단조 증가 (같은 연결 내)
  logic [31:0] prev_ack;
  always_ff @(posedge clk)
    if (tx_valid && tx_flags[4]) prev_ack <= tx_ack_num;

  property ack_monotonic_increase;
    @(posedge clk) disable iff (!rst_n)
    (tx_valid && tx_flags[4] && prev_ack != 0)
    |-> (tx_ack_num >= prev_ack);  // Wrap-around은 별도 처리 필요
  endproperty
  assert property (ack_monotonic_increase)
    else `uvm_error("SVA", $sformatf("ACK decreased: %0d -> %0d", prev_ack, tx_ack_num));

  // 4. Retransmission: Dup ACK 3개 후 Fast Retransmit 발생
  int dup_ack_count;
  always_ff @(posedge clk)
    if (rx_valid && rx_ack_num == prev_rx_ack && rx_flags[4])
      dup_ack_count <= dup_ack_count + 1;
    else
      dup_ack_count <= 0;

  property fast_retransmit_on_3_dup_ack;
    @(posedge clk) disable iff (!rst_n)
    (dup_ack_count == 3)
    |-> ##[1:FAST_RETX_TIMEOUT]
        (tx_valid && tx_seq_num == prev_rx_ack); // 손실 지점부터 재전송
  endproperty
  assert property (fast_retransmit_on_3_dup_ack)
    else `uvm_error("SVA", "No Fast Retransmit after 3 Dup ACKs");

  // 5. 각 assertion에 대응하는 cover property
  cover property (syn_gets_synack);
  cover property (no_data_on_zero_window);
  cover property (ack_monotonic_increase);
  cover property (fast_retransmit_on_3_dup_ack);

endmodule
```

SVA 설계 원칙:
- **프로토콜 불변량**: 항상 참이어야 하는 규칙 (Zero Window 시 미전송)
- **인과 관계**: 이벤트 A → 이벤트 B (SYN → SYN+ACK)
- **타이밍 제약**: `##[min:max]`로 HW 파이프라인 지연 허용
- **모든 assertion에 cover**: assertion 미위반 ≠ 미테스트, cover로 실제 동작 확인

---

## Network Agent 설계 — 에러 주입

```
Network Agent가 Peer TCP 역할을 하면서 의도적으로 에러를 주입:

class network_agent extends uvm_agent;

  // 에러 주입 설정
  rand int   pkt_loss_rate;     // 0-100% 패킷 손실률
  rand int   ooo_rate;          // Out-of-Order 확률
  rand int   dup_rate;          // 중복 패킷 확률
  rand bit   corrupt_checksum;  // Checksum 오류 주입
  rand int   delay_min, delay_max; // 응답 지연 범위

  constraint reasonable {
    pkt_loss_rate inside {[0:10]};
    ooo_rate      inside {[0:20]};
    dup_rate      inside {[0:5]};
  }

핵심: 네트워크의 비결정론적 특성을 Constrained Random으로 모델링
→ 실제 네트워크에서 발생 가능한 모든 조합을 커버
```

### Network Agent 동작 흐름 — 상세

```
Network Agent의 실제 동작은 Driver + Responder 패턴:

  ┌─────────────────────────────────────────────────────────────┐
  │                  Network Agent                               │
  │                                                              │
  │  Sequence                                                    │
  │  ├── 연결 수립: SYN → SYN+ACK 응답 생성                     │
  │  ├── 데이터 응답: 수신 데이터에 ACK 생성                     │
  │  └── 연결 종료: FIN → ACK+FIN 응답 생성                     │
  │                                                              │
  │  Driver (TX → DUT)                                           │
  │  ├── 패킷을 AXI-Stream으로 DUT에 주입                       │
  │  ├── 에러 주입 결정 (loss/ooo/dup/corrupt)                  │
  │  │   ├── Loss: 패킷을 전송하지 않음 (drop)                  │
  │  │   ├── OOO: 패킷 순서를 재배열 (reorder queue)            │
  │  │   ├── Dup: 같은 패킷을 2회 전송                          │
  │  │   └── Corrupt: Checksum 필드 변조                         │
  │  └── 지연 주입: delay_min~delay_max 사이 랜덤 대기          │
  │                                                              │
  │  Monitor (RX ← DUT)                                          │
  │  ├── DUT가 송신한 패킷 캡처                                  │
  │  ├── TCP 헤더 파싱 (seq, ack, flags, window, options)       │
  │  ├── analysis_port로 Scoreboard에 전달                      │
  │  └── 수신 패킷에 대한 응답 트리거 (Reactive Agent)          │
  │                                                              │
  │  Responder (핵심 — Reactive 동작)                            │
  │  ├── DUT TX 패킷 수신 → 자동으로 적절한 응답 생성          │
  │  │   ├── DATA 수신 → ACK 생성 (ack = seq + len)            │
  │  │   ├── SYN 수신 → SYN+ACK 생성                           │
  │  │   ├── FIN 수신 → ACK + FIN 생성                          │
  │  │   └── RST 수신 → 연결 정리                               │
  │  └── 에러 주입은 응답 생성 후 Driver에서 적용               │
  └─────────────────────────────────────────────────────────────┘

핵심 설계 결정:
  - Reactive Agent: Monitor가 DUT 출력을 보고 Responder가 응답 생성
  - 에러 주입은 Sequence/Driver 레벨에서 적용 (Responder 자체는 정상 응답 생성)
  - config_db로 에러율 조절 → 테스트마다 다른 네트워크 환경 시뮬레이션
```

---

## 이력서 연결 — TOE 검증 기여

```
Resume: "Enhanced the TCP Offload Engine verification environment
         by developing new test scenarios and expanding functional coverage"

기여 포인트:
  1. 새로운 테스트 시나리오 개발
     - 복합 에러 시나리오 (패킷 손실 + OOO + Zero Window 동시)
     - DCMAC 연동 에러 (MAC CRC 에러 → TOE 에러 처리)
     - 대규모 연결 스트레스 (Connection Table 한계)

  2. Functional Coverage 확장
     - TCP FSM 전이 커버리지 (이전에 미커버된 전이 식별)
     - Error/Recovery 교차 커버리지 추가
     - Flow/Congestion 상태 조합 커버리지 추가

  3. DCMAC 서브시스템 연동 검증
     - TOE ↔ DCMAC AXI-S 인터페이스 검증
     - End-to-End 데이터 무결성 (Host → TOE → DCMAC → 외부)
```

---

## Q&A

**Q: TOE 검증에서 가장 어려운 점은?**
> "네트워크의 비결정론적 특성이다. 패킷 손실, 순서 변경, 지연이 랜덤하게 발생하므로 모든 조합을 커버해야 한다. 특히 재전송 + 혼잡 제어 + OOO가 동시에 발생하는 복합 시나리오에서 TCP 상태 머신이 올바르게 전이하는지 검증하기가 가장 까다롭다. Constrained Random으로 네트워크 특성을 모델링하되, 특정 코너 케이스는 Directed로 보완한다."

**Q: TOE 검증 환경에 어떤 기여를 했나?**
> "세 가지: (1) 복합 에러 시나리오 — 패킷 손실 + OOO + Zero Window 동시 발생 같은 실제 네트워크 상황을 재현하는 테스트를 개발. (2) Coverage 확장 — TCP FSM 전이, Error/Recovery 교차, Congestion 상태 조합 커버리지를 추가하여 미커버 영역을 식별. (3) DCMAC 연동 — TOE와 DCMAC 간 AXI-S 인터페이스의 End-to-End 데이터 무결성을 검증."

**Q: TOE Reference Model은 어떻게 구성하나?**
> "C/C++로 TCP 프로토콜 스택의 축소판을 구현하고 DPI-C로 SystemVerilog와 연동한다. Reference Model은 Host Agent의 TX 요청과 Network Agent의 수신 패킷을 입력받아, 기대되는 TX 패킷(seq, ack, flags)과 RX 데이터를 출력한다. Scoreboard에서 DUT 출력과 비교하되, 데이터/프로토콜은 정확 일치, 타이밍은 허용 범위 내로 판정한다."

**Q: Network Agent를 어떻게 설계했나?**
> "Reactive Agent 패턴이다. Monitor가 DUT TX 패킷을 캡처하면 Responder가 자동으로 적절한 응답(ACK, SYN+ACK 등)을 생성한다. 에러 주입(패킷 손실, OOO, 중복, Checksum 변조)은 Responder가 정상 응답을 생성한 후 Driver 단에서 적용한다. 에러율은 config_db로 테스트마다 조절하여 다양한 네트워크 환경을 시뮬레이션한다."

**Q: SVA로 TOE에서 어떤 프로토콜 규칙을 검증하나?**
> "크게 네 가지: (1) 인과 관계 — SYN 수신 후 SYN+ACK 응답 (2) 프로토콜 불변량 — Zero Window에서 데이터 미전송 (3) 단조성 — ACK Number 단조 증가 (4) 재전송 규칙 — Dup ACK 3개 후 Fast Retransmit. 모든 assertion에 대응하는 cover property를 두어, assertion이 위반되지 않은 것이 '테스트 안 됨'이 아니라 '통과'임을 보장한다."

---

## 확인 퀴즈

**Q1.** TOE 검증 환경에서 Host Agent와 Network Agent의 역할 차이를 설명하라.

<details>
<summary>정답</summary>

**Host Agent**: TOE의 호스트 인터페이스(PCIe/AXI) 쪽에서 동작. 애플리케이션 역할로 TX 데이터 생성, 연결 수립/해제 제어 요청, DMA를 통한 데이터 전달을 수행한다. **Network Agent**: TOE의 MAC 인터페이스(AXI-Stream) 쪽에서 동작. Peer TCP(상대방 서버/클라이언트) 역할로 패킷 응답(ACK, SYN+ACK), 에러 주입(패킷 손실, OOO, 중복, Checksum 변조)을 수행한다. 즉 Host Agent는 "내부 사용자", Network Agent는 "외부 네트워크 환경"을 시뮬레이션한다.
</details>

**Q2.** SVA에서 모든 assertion에 대응하는 cover property를 두는 이유를 설명하라. "assertion이 한 번도 fail하지 않았다"와 "assertion이 검증되었다"의 차이는?

<details>
<summary>정답</summary>

Assertion이 한 번도 fail하지 않은 것은 두 가지 가능성이 있다: (1) 실제로 규칙이 잘 지켜졌거나, (2) 해당 조건이 한 번도 발생하지 않아 assertion이 평가조차 되지 않았거나(vacuous pass). Cover property는 assertion의 선행 조건(antecedent)이 실제로 발생했음을 확인한다. Cover hit이 0이면 해당 시나리오가 테스트되지 않은 것이므로 테스트를 추가해야 한다.
</details>

**Q3.** Reference Model이 C/C++ + DPI-C로 구현되는 경우의 장단점을 서술하고, Scoreboard에서 "타이밍은 허용 범위, 데이터는 정확 일치"로 비교하는 이유를 설명하라.

<details>
<summary>정답</summary>

**장점**: Linux TCP 스택 등 기존 C 코드를 재사용할 수 있고, TCP 프로토콜을 정밀하게 모델링 가능. **단점**: DPI-C 인터페이스 유지보수 복잡, 시뮬레이터와 C 코드 간 동기화 이슈, 디버그 시 두 도메인을 오가야 함. **비교 전략 이유**: 데이터 무결성(payload, Seq/ACK/Flags)은 프로토콜 정확성의 핵심이므로 1비트 차이도 허용하면 안 된다. 반면 타이밍은 HW 파이프라인 깊이, 중재(arbitration), 메모리 접근 지연에 따라 Reference Model과 수 클럭 차이가 나는 것이 정상이므로 허용 범위를 둔다.
</details>

**Q4. (사고력)** Network Agent가 "Reactive Agent" 패턴으로 설계된다고 했다. 만약 Reactive가 아니라 모든 패킷을 미리 생성(pre-programmed)하면 어떤 문제가 생기나?

<details>
<summary>정답</summary>

TCP는 상태 기반 프로토콜이므로, Network Agent의 응답은 DUT의 출력에 의존한다. 예를 들어 ACK의 ack_num은 DUT가 실제로 보낸 seq_num + len이어야 한다. Pre-programmed 방식은 DUT의 실제 동작을 예측해서 미리 만들어야 하는데, DUT가 재전송/OOO/Window 조정 등을 할 경우 예측이 불가능하다. Reactive 패턴은 DUT 출력을 Monitor가 관찰하고 Responder가 실시간으로 적절한 응답을 생성하므로, DUT의 어떤 동작에도 유연하게 대응할 수 있다.
</details>

<div class="chapter-nav">
  <a class="nav-prev" href="../03_toe_key_functions/">
    <div class="nav-label">◀ 이전</div>
    <div class="nav-title">TOE 핵심 기능 상세</div>
  </a>
  <a class="nav-next" href="../05_quick_reference_card/">
    <div class="nav-label">다음 ▶</div>
    <div class="nav-title">TOE — Quick Reference Card</div>
  </a>
</div>
