# Module 03 — DCMAC DV Methodology

<div class="learning-meta">
  <span class="meta-badge meta-level-advanced">📊 Advanced</span>
</div>

!!! objective "학습 목표"
    이 모듈을 마치면:

    - **Design** DCMAC DV 환경 (UVM env + traffic generator + scoreboard + FEC injector)을 설계.
    - **Apply** Frame integrity (FCS), AXI-Stream protocol, Pause/PFC flow control 시나리오.
    - **Implement** RS-FEC error injection (within / beyond correction limit) 시나리오.
    - **Plan** Performance regression (line-rate throughput, IFG enforcement, latency).

!!! info "사전 지식"
    - [Module 01-02](01_ethernet_fundamentals.md)
    - [UVM](../../uvm/), [AXI-Stream](../../amba_protocols/03_axi_stream/)

## 왜 이 모듈이 중요한가

**DCMAC 검증은 라인 레이트 throughput + 무결성 동시 보장**. Multi-channel + RS-FEC 조합이 만드는 corner case가 많고, IFG 위반 같은 protocol 위반은 silent.

## 핵심 개념
**DCMAC 검증 = 프레임 무결성(FCS) + AXI-S 프로토콜 준수 + 흐름 제어(Pause/PFC) + 에러 처리 + E2E 데이터 패스. UVM 환경을 from scratch로 구축한 경험이 이력서 핵심.**

---

## 검증 환경 아키텍처

```
+------------------------------------------------------------------+
|                 DCMAC Subsystem UVM Env                            |
|                                                                   |
|  +------------------+                    +------------------+     |
|  | TX Traffic Gen   |                    | RX Traffic Gen   |     |
|  | (Host Side)      |                    | (Line Side)      |     |
|  |                  |                    |                  |     |
|  | - 프레임 생성    |                    | - Ethernet Frame |     |
|  | - 크기 랜덤화    |                    | - FCS 정상/오류  |     |
|  | - VLAN/PFC 태그  |                    | - Runt/Oversize  |     |
|  +--------+---------+                    +--------+---------+     |
|           |                                       |               |
|           v (AXI-S TX)                  (Line IF) v               |
|  +------------------------------------------------------------+  |
|  |                    DUT (DCMAC IP)                           |  |
|  +------------------------------------------------------------+  |
|           |                                       |               |
|  (AXI-S RX) v                           (Line IF) v              |
|  +------------------+                    +------------------+     |
|  | RX Monitor       |                    | TX Monitor       |     |
|  | + Checker         |                    | + Checker         |     |
|  +--------+---------+                    +--------+---------+     |
|           |                                       |               |
|           v                                       v               |
|  +------------------------------------------------------------+  |
|  |                    Scoreboard                               |  |
|  |  - TX: 입력 데이터 == Line 출력 데이터? (FCS 추가 확인)     |  |
|  |  - RX: Line 입력 데이터 == AXI-S 출력 데이터? (FCS 결과)   |  |
|  |  - 통계 카운터 일치?                                        |  |
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

### Positive

| 카테고리 | 시나리오 | 검증 포인트 |
|---------|---------|-----------|
| **프레임** | 최소 크기 (64B) | 패딩 정확, FCS 정확 |
| | 최대 크기 (1518B / 9022B Jumbo) | Segmentation 없이 단일 프레임 |
| | 랜덤 크기 | 모든 크기에서 정확 동작 |
| | VLAN 태그 포함 | VLAN 삽입/제거 정확 |
| **AXI-S** | Back-to-back 프레임 | IFG 준수, 연속 전송 정확 |
| | 백프레셔 (tready toggle) | 데이터 손실 없음 |
| | 단일 beat 프레임 | tlast + tkeep 정확 |
| **흐름 제어** | Pause Frame 수신 | TX 일시 중단 + 재개 |
| | PFC 특정 우선순위 | 해당 우선순위만 중단 |

### Negative / 에러

| 카테고리 | 시나리오 | 검증 포인트 |
|---------|---------|-----------|
| **FCS** | Bad CRC 프레임 수신 | 폐기 + tuser bad 표시 + 카운터 증가 |
| **크기** | Runt 프레임 (<64B) | 폐기 + 카운터 증가 |
| | Oversize 프레임 (>MTU) | 설정에 따라 폐기 또는 통과 |
| **프로토콜** | 잘못된 Preamble | 프레임 무시 |
| | IFG 부족 | 정상 처리 또는 에러 플래그 |
| **AXI-S** | tlast 없는 프레임 | 타임아웃 또는 에러 처리 |

### Stress / 성능

| 시나리오 | 측정 |
|---------|------|
| 라인 레이트 연속 전송 (100Gbps) | 드롭 없이 처리 |
| 최소 크기 연속 (최대 pps) | 최대 프레임 레이트 달성 |
| TX/RX 동시 라인 레이트 | Full-duplex 처리량 |
| Pause 후 재개 반복 | 재개 시 즉시 라인 레이트 복구 |

---

## 시퀀스 전략

### Sequence Item 설계

```
class dcmac_frame_item extends uvm_sequence_item;
  // 프레임 필수 필드
  rand bit [47:0]  dst_mac;
  rand bit [47:0]  src_mac;
  rand bit [15:0]  ether_type;
  rand bit [7:0]   payload[];
  rand int unsigned frame_size;    // 64 ~ 9022

  // 프레임 옵션
  rand bit          has_vlan;
  rand bit [11:0]   vlan_id;
  rand bit [2:0]    vlan_pcp;
  rand bit          inject_fcs_err;  // 의도적 bad FCS

  // AXI-S 전송 제어
  rand int unsigned inter_frame_gap;  // IFG 사이클 수
  rand bit          insert_backpressure;

  // 기본 제약
  constraint c_size { frame_size inside {[64:9022]}; }
  constraint c_payload { payload.size() == frame_size - 18; } // Header(14) + FCS(4)
  constraint c_etype { ether_type >= 16'h0600; }             // EtherType, not Length
endclass
```

### 시퀀스 라이브러리 구조

```
seq_lib/
  ├── dcmac_base_seq.sv           // 공통 로직 (send_frame, wait_response)
  ├── dcmac_single_frame_seq.sv   // 단일 프레임 (directed smoke)
  ├── dcmac_random_frame_seq.sv   // 랜덤 크기/타입 프레임 연속 전송
  ├── dcmac_burst_seq.sv          // Back-to-back 연속 전송 (라인 레이트)
  ├── dcmac_error_inject_seq.sv   // FCS/Runt/Oversize 에러 주입
  ├── dcmac_pause_seq.sv          // Pause/PFC 프레임 생성
  ├── dcmac_vlan_seq.sv           // VLAN/QinQ 태그 프레임
  └── dcmac_mixed_traffic_seq.sv  // 정상 + 에러 + Pause 혼합

vseq_lib/
  ├── dcmac_tx_only_vseq.sv       // TX 경로만 검증
  ├── dcmac_rx_only_vseq.sv       // RX 경로만 검증
  ├── dcmac_bidir_vseq.sv         // TX + RX 동시 (Full-Duplex)
  ├── dcmac_e2e_vseq.sv           // TOE ↔ DCMAC E2E
  ├── dcmac_flow_ctrl_vseq.sv     // 트래픽 중 Pause/PFC 삽입
  └── dcmac_stress_vseq.sv        // 라인 레이트 + 에러 + Pause 동시
```

### Virtual Sequence 설계 원칙

```
Virtual Sequence가 필요한 이유:
  - DCMAC에는 TX(Host Side) + RX(Line Side) + Reg(AXI-Lite) 3개 Agent가 있음
  - 여러 Agent를 조율하는 시나리오 (예: TX 전송 중 Pause 삽입)는
    단일 Sequence로 구현 불가 → Virtual Sequence로 오케스트레이션

  class dcmac_flow_ctrl_vseq extends dcmac_base_vseq;
    task body();
      fork
        // TX Agent: 연속 프레임 전송
        tx_seq.start(p_sequencer.tx_sqr);
        // Line Agent: 일정 시간 후 Pause Frame 주입
        begin
          #100us;
          pause_seq.start(p_sequencer.line_sqr);
        end
      join
    endtask
  endclass

  Scoreboard 검증:
  → Pause 수신 후 TX가 실제로 멈추는지 (전송 갭 확인)
  → Pause 해제 후 TX가 재개되는지
```

---

## Constraint-Random 전략

### 제약 조건 계층화

```
Layer 1: Sequence Item 기본 제약 (항상 적용)
  constraint c_valid_size { frame_size inside {[64:9022]}; }
  constraint c_valid_mac  { src_mac != 48'h0; }

Layer 2: 시나리오별 제약 (Sequence에서 override)
  // 에러 주입 시퀀스
  constraint c_error_mode {
    inject_fcs_err dist {0 := 80, 1 := 20};  // 20% 확률 bad FCS
    frame_size dist {[64:64] := 10, [65:1517] := 70, [1518:9022] := 20};
  }

  // 스트레스 시퀀스
  constraint c_stress {
    inter_frame_gap == 0;           // 최소 IFG → 라인 레이트
    frame_size inside {[64:128]};   // 짧은 프레임 → 최대 pps
  }

Layer 3: 테스트별 제약 (Test class에서 factory override 또는 config)
  // config_db로 제약 모드 전달
  uvm_config_db#(dcmac_frame_cfg)::set(this, "env.tx_agent*", "cfg", stress_cfg);
```

### 분포 전략 (Distribution)

```
커버리지 홀에 따른 분포 조정:

초기 (탐색):
  frame_size dist {
    [64:64]     := 10,    // MIN
    [65:127]    := 20,    // SMALL
    [128:1023]  := 30,    // MEDIUM
    [1024:1517] := 20,    // LARGE
    [1518:1518] := 10,    // MAX
    [1519:9022] := 10     // JUMBO
  };

후기 (커버리지 홀 타겟팅):
  // Cross coverage (JUMBO × BROADCAST)가 비어있다면:
  constraint c_target_hole {
    frame_size inside {[1519:9022]};
    dst_mac == 48'hFFFF_FFFF_FFFF;
  }
```

---

## RAL (Register Abstraction Layer) 전략

```
레지스터 검증 구조:

  +------------------+    AXI-Lite    +-------------------+
  | RAL Model        | ←── adapter ──→ | DCMAC Registers   |
  | (UVM Register)   |    (Frontdoor)  | (실제 HW)         |
  +------------------+                 +-------------------+
         |
    Backdoor (hdl_path)
         |
    RTL 시뮬레이션 내부 직접 접근

검증 항목:
  1. Reset Value Test
     - 모든 레지스터가 리셋 후 기본값과 일치
     - RAL: reg_model.reset("HARD"); → mirror check

  2. Read/Write Test
     - RW 필드: Write → Read back → 일치 확인
     - RO 필드: Write 시도 → 값 변경 없음 확인
     - WO 필드: Write → Read 시 0 반환 확인
     - W1C 필드: Write 1 → Clear 동작 확인

  3. Frontdoor vs Backdoor 일치
     - 동일 레지스터를 양쪽으로 읽어 값 일치 확인

  4. 통계 카운터 검증
     - 프레임 N개 전송 후 tx_frames 카운터 == N 확인
     - FCS 에러 M개 주입 후 rx_fcs_errors == M 확인
     - Read-on-Clear 동작: 읽기 후 카운터 0인지 확인

  5. Config 적용 시점 검증
     - MTU 변경 후 즉시/다음 프레임에서 적용되는지
     - TX Enable=0 시 진행 중인 프레임 완료 후 멈추는지

RAL 패키지 구조:
  dcmac_ral_pkg.sv
    ├── dcmac_reg_block.sv          // Top-level register block
    ├── dcmac_global_cfg_reg.sv     // 개별 레지스터 정의
    ├── dcmac_tx_cfg_reg.sv
    ├── dcmac_rx_cfg_reg.sv
    ├── dcmac_stats_reg.sv
    └── dcmac_axi_lite_adapter.sv   // AXI-Lite ↔ RAL Adapter
```

---

## SVA / Assertion 전략

```
프로토콜 어설션 분류:

[A1] AXI-Stream Protocol Assertions
  // tvalid가 올라간 후 tready 전에 떨어지면 안 됨
  assert property (@(posedge clk) disable iff (!rst_n)
    tx_axis_tvalid && !tx_axis_tready |=> tx_axis_tvalid
  ) else $error("AXI-S: tvalid dropped before tready");

  // tlast 후 tkeep이 유효해야 함
  assert property (@(posedge clk) disable iff (!rst_n)
    tx_axis_tvalid && tx_axis_tlast |-> (tx_axis_tkeep != 0)
  ) else $error("AXI-S: tkeep zero on tlast beat");

  // tdata는 tvalid 동안 안정적이어야 함
  assert property (@(posedge clk) disable iff (!rst_n)
    tx_axis_tvalid && !tx_axis_tready |=>
      $stable(tx_axis_tdata) && $stable(tx_axis_tkeep)
  ) else $error("AXI-S: tdata/tkeep changed while waiting");

[A2] Frame Integrity Assertions
  // 프레임 최소 크기
  assert property (@(posedge clk)
    frame_complete |-> (frame_byte_count >= 64)
  ) else $error("Frame smaller than minimum 64 bytes");

  // IFG 최소 간격
  assert property (@(posedge clk)
    frame_end |-> ##[12:$] next_frame_start
  ) else $error("IFG violation: less than 12 bytes");

[A3] Flow Control Assertions
  // Pause 수신 후 TX 멈춤
  assert property (@(posedge clk)
    pause_received && (pause_quanta > 0) |=>
      !tx_frame_start [*1:$] ##1 (pause_timer == 0)
  ) else $error("TX did not stop after Pause");

[A4] Configuration Assertions
  // TX Enable=0이면 새 프레임 시작하지 않음
  assert property (@(posedge clk)
    !tx_enable |-> !tx_frame_start
  ) else $error("TX started frame while disabled");

Bind Module 구조:
  // RTL을 수정하지 않고 외부에서 어설션 바인드
  module dcmac_sva_bind;
    bind dcmac_tx_engine dcmac_tx_sva u_tx_sva (.*);
    bind dcmac_rx_engine dcmac_rx_sva u_rx_sva (.*);
    bind dcmac_axi_stream dcmac_axis_sva u_axis_sva (.*);
  endmodule
```

---

## Coverage Model

```
[CG1] Frame Coverage
  - cp_frame_size: {MIN(64), SMALL(<128), MEDIUM, LARGE(>1024), MAX(1518), JUMBO(9022)}
  - cp_frame_type: {UNICAST, MULTICAST, BROADCAST}
  - cp_vlan: {NO_VLAN, SINGLE_VLAN, DOUBLE_VLAN(QinQ)}
  - cross: frame_size × frame_type
  - cross: frame_size × vlan  // 모든 크기에서 VLAN 조합

[CG2] FCS/Error Coverage
  - cp_fcs_result: {GOOD, BAD}
  - cp_error_type: {NONE, CRC_ERR, RUNT, OVERSIZE, BAD_PREAMBLE}
  - cp_direction: {TX, RX}
  - cross: error_type × direction  // 모든 에러가 양방향에서 검증

[CG3] AXI-S Protocol Coverage
  - cp_backpressure: {NONE, OCCASIONAL, HEAVY, EXTREME}
  - cp_burst_length: {SINGLE_BEAT, SHORT, LONG, MAX}
  - cp_tkeep_pattern: {ALL_VALID, PARTIAL_LAST}
  - cp_tuser_bits: {NORMAL, POISON, BAD_FCS, VLAN_TAGGED}
  - cross: backpressure × burst_length

[CG4] Flow Control Coverage
  - cp_pause_type: {NONE, PAUSE, PFC}
  - cp_pfc_priority: {0, 1, ..., 7, MULTI}
  - cp_pause_duration: {SHORT, MEDIUM, LONG, INFINITE}
  - cp_pause_timing: {IDLE, MID_FRAME, BACK_TO_BACK}  // Pause 시점
  - cross: pause_type × pfc_priority (PFC일 때만)

[CG5] Statistics Counter Coverage
  - cp_counter_type: {FRAMES, BYTES, ERRORS, PAUSE}
  - cp_counter_overflow: {NORMAL, NEAR_MAX, OVERFLOW}
  - cp_counter_access: {SINGLE_READ, CONSECUTIVE_READ, READ_DURING_TRAFFIC}

[CG6] Configuration Coverage (추가)
  - cp_speed_mode: {100G, 200G, 400G}
  - cp_mtu_setting: {STANDARD(1518), JUMBO(9022), CUSTOM}
  - cp_tx_enable: {ENABLED, DISABLED, TOGGLE_MID_TRAFFIC}
  - cp_promiscuous: {ON, OFF}
  - cross: speed_mode × frame_size

[CG7] Reset / Init Coverage (추가)
  - cp_reset_type: {HARD_RESET, SOFT_RESET}
  - cp_reset_timing: {IDLE, MID_FRAME, MID_PAUSE}
  - cp_post_reset: {IMMEDIATE_TRAFFIC, DELAYED_TRAFFIC}
```

### 커버리지 클로저 전략

```
Phase 1: 기본 커버리지 (Constrained-Random)
  - 랜덤 시퀀스 1000+ 프레임 × 100 시드
  - 목표: CG1~CG5의 single coverpoint 90%+

Phase 2: Cross 커버리지 타겟팅
  - Uncovered cross bin 식별
  - Directed constraint로 hole 타겟팅
  - 예: JUMBO × BROADCAST × HEAVY_BP가 비어있으면 전용 시퀀스 작성

Phase 3: Corner Case 보완
  - 에러 + Pause 동시 발생
  - Reset 직후 즉시 트래픽
  - 통계 카운터 오버플로우 경계값

Sign-off 기준: 전체 functional coverage 95%+, cross 90%+
```

---

## E2E 데이터 무결성 검증

```
TX E2E:
  Host 데이터 (AXI-S TX) → DCMAC → Line Side 출력
  Scoreboard: AXI-S 입력 데이터 == Line 출력 Payload?
              FCS가 올바르게 추가되었는가?

RX E2E:
  Line Side 입력 (Ethernet Frame) → DCMAC → AXI-S RX 출력
  Scoreboard: Line 입력 Payload == AXI-S 출력 데이터?
              FCS 검증 결과가 tuser에 정확히 반영?

TOE ↔ DCMAC E2E (서브시스템):
  Host → TOE → DCMAC → Line → DCMAC → TOE → Host
  Scoreboard: Host 전송 데이터 == Host 수신 데이터?
              TCP/Ethernet 프로토콜 모두 정확?
```

---

## 리셋 / 초기화 검증

```
리셋 종류:
  1. Hard Reset (글로벌 리셋)
     - 전체 DCMAC 블록 리셋
     - 모든 레지스터 → 기본값
     - 진행 중인 프레임 폐기
     - FSM → IDLE 상태

  2. Soft Reset (포트별 리셋)
     - 특정 포트만 리셋
     - 다른 포트는 영향 없음
     - 해당 포트의 카운터만 클리어

검증 시나리오:
  +---------------------------------------------------+
  | 시나리오             | 검증 포인트               |
  |---------------------+---------------------------|
  | IDLE 시 리셋        | 레지스터 기본값 복원      |
  | TX 프레임 전송 중 리셋| 프레임 중단, 잔여 데이터 없음|
  | RX 프레임 수신 중 리셋| 수신 중단, partial 프레임 폐기|
  | Pause 활성 중 리셋   | Pause 상태 해제          |
  | 리셋 직후 트래픽     | 첫 프레임 정상 처리      |
  | 리셋 반복 (stress)   | N회 반복 후 정상 동작    |
  +---------------------------------------------------+

초기화 시퀀스:
  1. Hard Reset Assert (최소 N 클럭)
  2. Hard Reset Deassert
  3. 레지스터 기본값 확인 (RAL mirror)
  4. MAC 주소, MTU, 속도 모드 설정
  5. TX/RX Enable
  6. Link Status 확인 (PCS Lock)
  7. 트래픽 시작
```

---

## CDC (Clock Domain Crossing) 고려사항

```
DCMAC의 클럭 도메인:

  +------------+    +------------+    +-------------+
  | AXI-S CLK  |    | Core CLK   |    | SerDes CLK  |
  | (User IF)  |    | (MAC 내부) |    | (Line Side) |
  +------------+    +------------+    +-------------+
       |                  |                  |
  tx_axis_aclk       core_clk          gt_txusrclk2
  rx_axis_aclk                         gt_rxusrclk2

  +------------+
  | AXI-L CLK  |
  | (Register) |
  +------------+
       |
  s_axi_aclk

CDC 경계:
  1. AXI-S CLK ↔ Core CLK: 비동기 FIFO (프레임 데이터)
  2. Core CLK ↔ SerDes CLK: 비동기 FIFO (인코딩된 데이터)
  3. AXI-Lite CLK ↔ Core CLK: CDC 동기화 (레지스터 접근)

DV에서의 CDC 검증 접근:
  - 클럭 비율 변경 시나리오 (정수비 / 비정수비)
  - FIFO full/empty 경계 조건
  - 레지스터 읽기 중 값 변경 시 일관성 (특히 64bit 카운터의 상/하위 32bit)
  - CDC 관련 경고: 시뮬레이터의 CDC check 옵션 활용 (VCS: -Xcheck=cdc)
  - 실무: CDC formal verification은 별도 도구 (Questa CDC, Spyglass CDC)로 수행
    → 시뮬레이션에서는 비동기 FIFO의 기능적 정확성 위주로 검증
```

---

## DCMAC 디버그 방법론

```
디버그 레벨 (DCMAC 특화):

  L1: 기본 로그 분석
    - UVM_ERROR 메시지에서 프레임 번호, 방향(TX/RX) 확인
    - Scoreboard 미스매치: expected vs actual 바이트 비교
    - "첫 번째 에러"를 찾는 것이 핵심 (cascading error 주의)

  L2: 프로토콜 레벨 분석
    - AXI-S 트랜잭션 로그: tdata, tkeep, tuser 값 확인
    - 프레임 경계(tlast) 위치가 맞는지
    - FCS 수동 계산과 비교

  L3: 신호 레벨 분석 (파형)
    - 핵심 관찰 신호:
      tx_axis_tvalid, tx_axis_tready (핸드셰이크 정상?)
      rx_axis_tuser (FCS 결과 정확?)
      pause_req, pause_val (흐름 제어 동작?)
      stat counters (카운터 증가 시점?)
    - IFG 타이밍 측정
    - Pause 수신 → TX 중단 사이의 레이턴시

  L4: 내부 상태 분석
    - MAC Engine FSM 상태 추적
    - 내부 FIFO 레벨 모니터링
    - PCS lock 상태, alignment marker 감지

흔한 실패 패턴과 원인:

  | 증상 | 가능한 원인 |
  |------|-----------|
  | Scoreboard mismatch (데이터) | tkeep 해석 오류, 바이트 순서(endian) |
  | FCS always bad | CRC 계산 범위 오류, 바이트 패딩 누락 |
  | TX 멈춤 (hang) | tready가 영구 low, 데드락 |
  | 프레임 누락 | FIFO 오버플로우, 백프레셔 미처리 |
  | 카운터 불일치 | Read-on-Clear 타이밍, CDC 관련 |
  | Pause 후 미재개 | Pause timer 리셋 로직 오류 |
```

---

## 이력서 연결 — DCMAC 서브시스템 기여

```
Resume: "Verified DCMAC-integrated subsystems by architecting and
         implementing end-to-end UVM environments from scratch."

기여 포인트:
  1. UVM 환경 From Scratch 구축
     - DCMAC AXI-S Agent (TX/RX)
     - Line Side Agent (Ethernet Frame 생성/검증)
     - Scoreboard (E2E 데이터 비교)
     - Coverage Model 설계

  2. TOE ↔ DCMAC 연동 검증
     - AXI-S 핸드셰이크 정확성
     - FCS 에러 전파 경로
     - 백프레셔 동작

  3. E2E 데이터 패스 검증
     - Host → TOE → DCMAC → Network (전체 경로)
     - 프레임 무결성, 프로토콜 준수, 성능
```

---

## Q&A

**Q: DCMAC 서브시스템 검증 환경을 어떻게 설계했나?**
> "UVM 환경을 from scratch로 구축했다. 핵심 컴포넌트: (1) AXI-S Agent — TX/RX 양방향, 랜덤 크기/타입 프레임 생성 + 백프레셔 모델링. (2) Line Side Agent — Ethernet Frame 레벨 트래픽 생성 + FCS 에러 주입. (3) Scoreboard — TX/RX 양방향 E2E 데이터 비교 + FCS 결과 검증 + 통계 카운터 일치 확인. Coverage는 프레임 크기/타입, FCS 결과, AXI-S 프로토콜, 흐름 제어 상태를 교차 커버했다."

**Q: E2E 검증에서 가장 중요한 포인트는?**
> "두 가지: (1) 데이터 무결성 — Host에서 보낸 바이트가 Network 끝에서 정확히 나오는지, 한 비트도 변경 없이. DCMAC이 추가하는 Preamble/FCS/IFG를 제외한 Payload가 정확히 일치해야 한다. (2) 에러 전파 — Line Side에서 FCS 에러가 발생하면 DCMAC이 tuser로 정확히 표시하고, TOE가 이를 감지하여 패킷을 폐기하는 전체 경로가 올바른지 검증."

**Q: DCMAC 검증에서 가장 어려웠던 시나리오는?**
> "Pause Frame과 라인 레이트 트래픽이 동시에 발생하는 시나리오였다. TX가 프레임 전송 중간에 Pause를 받으면 현재 프레임은 완료해야 하고, 다음 프레임부터 멈춰야 한다. 그런데 Pause quanta가 짧으면 멈추기도 전에 해제되는 경우가 있고, PFC에서는 특정 우선순위만 멈추면서 나머지는 계속 전송해야 한다. 이걸 검증하려면 Virtual Sequence로 TX와 Line Side Agent를 정밀하게 조율하고, Scoreboard에서 Pause 기간 중 전송 갭을 시간 기반으로 확인해야 했다."

**Q: Constraint-random 전략은 어떻게 설계했나?**
> "3-layer 접근이다. Layer 1은 Sequence Item의 기본 제약(유효 크기, 유효 MAC), Layer 2는 시나리오별 제약(에러 주입 확률, 크기 분포), Layer 3는 테스트별 제약(config_db로 주입). 초기에는 균등 분포로 탐색하고, 커버리지 결과를 보면서 비어있는 cross bin을 타겟팅하는 directed constraint를 추가했다. 예를 들어 JUMBO × BROADCAST cross가 안 채워지면 해당 조합만 생성하는 전용 시퀀스를 만들었다."

**Q: 레지스터 검증은 어떻게 접근했나?**
> "UVM RAL을 구축하고 세 가지를 검증했다. (1) Reset Value — 모든 레지스터의 리셋 후 값이 스펙과 일치하는지 RAL mirror로 자동 확인. (2) Access Policy — RW/RO/W1C 등 각 필드의 접근 정책이 올바른지. (3) Functional — 통계 카운터가 실제 트래픽과 일치하는지, Config 변경이 올바른 시점에 적용되는지. 특히 통계 카운터의 Read-on-Clear 특성 때문에 읽기 순서/타이밍 검증이 까다로웠다."

---

!!! warning "실무 주의점 — Statistics Counter Clear-on-Read 레이스 컨디션"
    **현상**: 회귀 테스트에서 통계 카운터(rx_frame_count, rx_error_count 등) 값이 읽을 때마다 달라지거나 0으로 리셋된 것처럼 보인다.
    
    **원인**: DCMAC 통계 레지스터는 Read-on-Clear 방식이 많다. Scoreboard와 Coverage 수집 루틴이 동일 카운터를 서로 다른 타임스텝에서 각각 읽으면 첫 번째 읽기에서 카운터가 클리어되어 두 번째 읽기값이 0이 된다.
    
    **점검 포인트**: RAL task 내에서 통계 읽기를 단일 atomic 시퀀스로 묶고, Scoreboard/Checker가 동일 레지스터를 중복 읽지 않도록 구현. `stat_snapshot` 방식으로 전체 카운터를 한 번에 래치한 뒤 비교하는 패턴을 채택할 것.

## 핵심 정리

- **검증 4축**: Frame integrity (FCS), AXI-S protocol, Flow control (Pause/PFC), Error handling.
- **Traffic generator**: random + directed (min frame, max frame, jumbo, VLAN, pause). Line-rate 시나리오.
- **Scoreboard**: TX frame을 capture → RX에서 FCS 검증, ordering, payload match.
- **RS-FEC injection**: within correction limit (수정 가능, hidden), beyond limit (drop, error counter ↑).
- **Performance**: line-rate throughput, IFG enforcement, multi-channel parallelism.

## 다음 단계

- 📝 [**Module 03 퀴즈**](quiz/03_dcmac_dv_methodology_quiz.md)
- ➡️ [**Module 04 — Quick Reference Card**](04_quick_reference_card.md)

<div class="chapter-nav">
  <a class="nav-prev" href="../02_dcmac_architecture/">
    <div class="nav-label">◀ 이전</div>
    <div class="nav-title">DCMAC 아키텍처</div>
  </a>
  <a class="nav-next" href="../04_quick_reference_card/">
    <div class="nav-label">다음 ▶</div>
    <div class="nav-title">Ethernet & DCMAC — Quick Reference Card</div>
  </a>
</div>
