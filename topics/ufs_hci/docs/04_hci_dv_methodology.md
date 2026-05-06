# Unit 4: UFS HCI DV 검증 전략

<div class="learning-meta">
  <span class="meta-badge meta-level-advanced">📊 Advanced</span>
</div>

## 핵심 개념
**UFS HCI 검증 = 레지스터 정확성 + UTRD/UPIU 변환 정확성 + DMA 무결성 + 명령 큐잉 + 에러 복구. SW Driver 관점의 인터페이스(레지스터/메모리)와 Device 관점의 프로토콜(UPIU)을 양 끝에서 동시에 검증.**

---

## 검증 환경 아키텍처

```
+------------------------------------------------------------------+
|                   UFS HCI UVM Env                                  |
|                                                                   |
|  +------------------+                    +------------------+     |
|  | Host Agent       |                    | Device Agent     |     |
|  | (SW Driver 모델) |                    | (UFS Device 모델)|     |
|  |                  |                    |                  |     |
|  | - UTRD 작성      |                    | - UPIU 응답 생성 |     |
|  | - Doorbell 셋    |                    | - RTT 제어       |     |
|  | - ISR 처리       |                    | - 에러 주입      |     |
|  | - Register R/W   |                    | - UniPro IF      |     |
|  +--------+---------+                    +--------+---------+     |
|           | AHB/AXI                        UniPro  |              |
|           v                                        v              |
|  +------------------------------------------------------------+  |
|  |                    DUT (UFS HCI IP)                         |  |
|  +------------------------------------------------------------+  |
|           |                                        |              |
|  +--------+----------------------------------------+---------+   |
|  |                    Scoreboard                              |   |
|  |  - UTRD → UPIU 변환 정확성                                |   |
|  |  - DMA 데이터 무결성 (PRDT)                               |   |
|  |  - 레지스터 상태 정확성                                    |   |
|  |  - 명령 완료 순서 / 상태                                   |   |
|  +------------------------------------------------------------+  |
|                                                                   |
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
| **초기화** | HCE Enable → HCI 활성화 | 레지스터 초기값, UTRL/UTMRL Ready |
| | UIC Command (DME_LINKSTARTUP) | UniPro 링크 수립 |
| **Transfer** | READ 단일 명령 | UTRD→Cmd UPIU→Data-In→Response→Status→IRQ |
| | WRITE 단일 명령 | UTRD→Cmd UPIU→RTT→Data-Out→Response |
| | 복수 명령 동시 (Queue Depth) | 32개 슬롯 동시 활용, 각각 정확 완료 |
| | 다양한 데이터 크기 | 1 블록 ~ 최대 PRDT 크기 |
| **Query** | Read/Write Descriptor | UPIU 변환 + 응답 데이터 정확 |
| | Read/Write Attribute | 값 정확 반영 |
| **Task Mgmt** | Abort Task | 해당 명령 취소, Doorbell 클리어 |
| | LUN Reset | 해당 LUN 모든 명령 취소 |
| **Interrupt** | Transfer 완료 IRQ | IS 비트 정확, IE 마스킹 동작 |
| | UIC Error IRQ | 링크 에러 → IS[UE] 셋 |

### Negative / 에러

| 카테고리 | 시나리오 | 검증 포인트 |
|---------|---------|-----------|
| **디바이스 에러** | Response Status = CHECK CONDITION | UTRD에 에러 상태 반영 |
| | Residual Count ≠ 0 | 불완전 전송 정확 보고 |
| **링크 에러** | UniPro CRC 에러 | 재전송 (HCI 투명) |
| | Link Down | IS[UE] 인터럽트, 복구 시퀀스 |
| **DMA 에러** | 잘못된 PRDT 주소 | 에러 플래그 + 인터럽트 |
| **타임아웃** | Device 무응답 | SW 타임아웃 → Task Mgmt |
| **SW 오류** | 잘못된 레지스터 접근 | 안전하게 무시 또는 에러 |
| | Doorbell 중복 셋 | 이미 진행 중인 슬롯 → 정의된 동작 |

### Stress

| 시나리오 | 측정 |
|---------|------|
| 32 슬롯 전부 활용 연속 | 큐 오버플로 없음, 모두 정확 완료 |
| READ/WRITE 혼합 최대 부하 | Doorbell 처리 속도, DMA 대역폭 |
| 빈번한 Abort + 새 명령 | Task Mgmt와 Transfer 동시 처리 |
| Power Mode 전환 중 명령 | 전환 완료 후 명령 정상 처리 |

---

## Coverage Model

```
[CG1] Command Coverage
  - cp_opcode: {READ_10, WRITE_10, INQUIRY, TEST_UNIT_READY,
                SYNC_CACHE, UNMAP, START_STOP_UNIT, ...}
  - cp_lun: {Boot_LU, User_LU_0, User_LU_1, RPMB_LU, W-LU}
  - cp_data_size: {ZERO, SMALL, MEDIUM, LARGE, MAX}
  - cp_direction: {NO_DATA, HOST_TO_DEVICE, DEVICE_TO_HOST}
  - cross: opcode × lun × data_size

[CG2] Queue Coverage
  - cp_queue_depth: {1, 8, 16, 24, 32}
  - cp_slot_usage: {SEQUENTIAL, RANDOM, ALL_SLOTS}
  - cp_mix: {READ_ONLY, WRITE_ONLY, MIXED}

[CG3] Error/Recovery Coverage
  - cp_error_source: {DEVICE_RESP, LINK_ERR, DMA_ERR, TIMEOUT}
  - cp_recovery: {RETRY, ABORT_TASK, LUN_RESET, HOST_RESET}
  - cross: error_source × recovery

[CG4] Register Coverage
  - cp_register: 모든 R/W 레지스터
  - cp_access: {READ, WRITE, W1C}
  - cp_reset_value: 리셋 후 기본값 일치

[CG5] Power/Mode Coverage
  - cp_power_mode: {ACTIVE_HS, ACTIVE_PWM, HIBERNATE}
  - cp_gear: {G1, G2, G3, G4}
  - cp_lane: {1_LANE, 2_LANE}
  - cross: power_mode × gear × lane
```

---

## HCI 초기화 검증 시나리오

```
HCI 초기화 시퀀스는 엄격한 순서를 요구 — 검증 필수

주요 검증 항목:

  1. HCE Enable 시퀀스
     - HCE = 1 쓰기 → HCI 내부 리셋 수행 → HCS.UCRDY = 1 대기
     - HCS.UCRDY가 1이 되기 전 다른 레지스터 접근 → 정의된 동작?
     - HCE = 0 → 1 토글 (리셋 후 재활성화) → 깨끗한 상태 복구?

  2. UIC Command 시퀀스 (Link Startup)
     - DME_LINKSTARTUP 발행 → UniPro 링크 수립
     - 완료 대기: IS[UCCS] (UIC Command Completion Status)
     - Link Startup 실패 → IS[UE] + UICCMDARG 에러 코드 정확?

  3. NOP OUT → NOP IN (Device Ping)
     - 링크 수립 후 NOP OUT UPIU 전송 → NOP IN 응답 확인
     - 디바이스 생존(alive) 확인 용도
     - 타임아웃 시 → 에러 처리 경로

  4. Transfer Request List 설정
     - UTRLBA/UTRLBAU에 유효한 주소 설정
     - UTMRLBA/UTMRLBAU에 유효한 주소 설정
     - UTRLRSR = 1 (Run/Stop) → 전송 수락 시작
     - 설정 전에 Doorbell 셋 → 정의된 에러 동작?

  5. 첫 Query/Transfer
     - bBootLunEn Read Attribute → Boot LU 확인
     - 첫 READ/WRITE → 전체 데이터패스 검증

테스트 접근:
  - Golden Sequence: JEDEC JESD223 참조 초기화 시퀀스와 DUT 시퀀스 비교
  - 순서 위반 주입: HCE 전에 Doorbell 셋, UTRLRSR 전에 Transfer 시도 등
  - 타이밍 경계: Link Startup 최소/최대 대기 시간
```

---

## Sequence 전략 — 계층적 설계

```
계층 구조:

  +----------------------------------------------------------+
  | Virtual Sequence (vseq)                                   |
  |   - 여러 Agent의 Sequence를 조율                          |
  |   - 시나리오 단위: "32개 READ 후 Abort 2개 동시 주입"     |
  +----------------------------------------------------------+
       |                              |
  +----+----+                  +------+------+
  | Host     |                  | Device      |
  | Sequence |                  | Sequence    |
  +----------+                  +-------------+
       |                              |
  +----+----+                  +------+------+
  | Host     |                  | Device      |
  | Driver   |                  | Driver      |
  +----------+                  +-------------+


Sequence 계층:

  Level 1: Base Sequence (단일 동작)
    - single_read_seq:  단일 READ 명령 (UTRD 작성 + Doorbell)
    - single_write_seq: 단일 WRITE 명령
    - query_seq:        단일 Query Request
    - nop_seq:          NOP OUT/IN

  Level 2: Directed Sequence (특정 시나리오)
    - init_seq:         HCE Enable → Link Startup → NOP → Query
    - multi_cmd_seq:    N개 명령 연속 제출 (Queue Depth 가변)
    - abort_seq:        명령 진행 중 Abort Task 발행
    - error_inject_seq: Device Agent에서 에러 응답 생성

  Level 3: Random Sequence (랜덤 조합)
    - random_traffic_seq:
        rand int unsigned num_cmds;   // 1~32
        rand cmd_type_e   cmd_mix[];  // READ/WRITE/QUERY 비율
        rand int unsigned data_sizes[]; // 각 명령의 데이터 크기
        constraint c_mix {
          cmd_mix.size() == num_cmds;
          foreach(cmd_mix[i]) cmd_mix[i] dist {READ:=50, WRITE:=40, QUERY:=10};
        }

  Level 4: Virtual Sequence (복합 시나리오)
    - stress_vseq:
        fork
          host_seq.start(host_sqr);     // Host: 32 슬롯 포화
          device_err_seq.start(dev_sqr); // Device: 랜덤 에러 응답
          abort_seq.start(host_sqr);     // Host: 간헐적 Abort
        join
    - power_transition_vseq:
        init_seq → traffic → hibernate_seq → resume_seq → traffic
```

### Config Object — 랜덤화 Knob

```
class ufs_hci_cfg extends uvm_object;
  // 명령 관련
  rand int unsigned max_queue_depth;     // 1~32
  rand int unsigned max_data_size;       // 블록 단위
  rand cmd_mix_e    cmd_distribution;    // READ_HEAVY, WRITE_HEAVY, BALANCED

  // 에러 관련
  rand bit          enable_device_error; // Device 에러 응답 활성화
  rand int unsigned error_rate;          // 0~100 (%)
  rand error_type_e error_types[];       // 주입할 에러 종류

  // 타이밍 관련
  rand int unsigned doorbell_delay;      // UTRD 작성 후 Doorbell까지 지연
  rand int unsigned inter_cmd_delay;     // 명령 간 간격

  // 모드 관련
  rand bit          use_mcq;             // MCQ 모드 사용 여부
  rand int unsigned num_queues;          // MCQ 큐 수 (1~8)

  constraint c_defaults {
    max_queue_depth inside {[1:32]};
    max_data_size   inside {[1:256]};  // 256 블록 = 128KB
    error_rate      inside {[0:30]};
    doorbell_delay  inside {[0:10]};
  }
endclass
```

---

## Scoreboard 알고리즘 상세

```
Scoreboard의 핵심 역할: Host 측 명령과 Device 측 UPIU의 정합성 검증

  +------------------+                    +------------------+
  | Host Monitor     |                    | Device Monitor   |
  | (AHB/AXI 관찰)  |                    | (UniPro IF 관찰) |
  +--------+---------+                    +--------+---------+
           |                                       |
      utrd_ap (analysis port)              upiu_ap (analysis port)
           |                                       |
           v                                       v
  +------------------------------------------------------------+
  |                    Scoreboard                               |
  |                                                             |
  |  1. UTRD→UPIU 변환 검증                                    |
  |     Host Monitor가 UTRD 캡처 → 예상 UPIU 생성              |
  |     Device Monitor가 실제 UPIU 캡처                         |
  |     비교: Task Tag, LUN, CDB, Data Length 일치?             |
  |                                                             |
  |  2. DMA 데이터 무결성                                       |
  |     WRITE: Host 메모리(PRDT 주소)의 데이터                  |
  |          == Device가 수신한 Data-Out UPIU 데이터?            |
  |     READ: Device가 송신한 Data-In UPIU 데이터               |
  |          == Host 메모리(PRDT 주소)에 DMA된 데이터?           |
  |                                                             |
  |  3. 완료 상태 정합성                                        |
  |     Response UPIU의 Status                                  |
  |       == UTRD의 Overall Command Status?                     |
  |     Transfer 완료 → Doorbell 비트 클리어?                   |
  |     IS[UTRCS] 인터럽트 발생?                                |
  |                                                             |
  |  4. 순서 검증                                               |
  |     같은 LUN 내 명령 → 순서 보장?                           |
  |     다른 LUN 명령 → Out-of-Order 허용?                      |
  +------------------------------------------------------------+
```

### Scoreboard SV Pseudo-code

```systemverilog
class ufs_hci_scoreboard extends uvm_scoreboard;
  `uvm_component_utils(ufs_hci_scoreboard)

  // Analysis port: Host Monitor → UTRD 트랜잭션
  uvm_analysis_imp #(utrd_txn, ufs_hci_scoreboard) utrd_ap;
  // Analysis port: Device Monitor → UPIU 트랜잭션
  uvm_analysis_imp_upiu #(upiu_txn, ufs_hci_scoreboard) upiu_ap;

  // 미완료 명령 추적: Task Tag → 예상 UPIU
  utrd_txn pending_cmds[int];  // key = task_tag

  // 통계
  int match_count, mismatch_count, timeout_count;

  // Host Monitor로부터 UTRD 수신 → 예상 UPIU 생성
  function void write(utrd_txn t);
    upiu_txn expected = predict_upiu(t);
    pending_cmds[t.task_tag] = t;
    `uvm_info("SCB", $sformatf("UTRD[tag=%0d] queued: %s LUN=%0d",
              t.task_tag, t.opcode.name(), t.lun), UVM_MEDIUM)
  endfunction

  // Device Monitor로부터 실제 UPIU 수신 → 비교
  function void write_upiu(upiu_txn actual);
    if (!pending_cmds.exists(actual.task_tag)) begin
      `uvm_error("SCB", $sformatf("Unexpected UPIU tag=%0d", actual.task_tag))
      return;
    end

    utrd_txn exp = pending_cmds[actual.task_tag];

    // 1. Command UPIU 필드 비교
    if (actual.txn_type == COMMAND) begin
      check_cmd_upiu(exp, actual);
    end
    // 2. Data UPIU 데이터 비교
    else if (actual.txn_type inside {DATA_IN, DATA_OUT}) begin
      check_data_integrity(exp, actual);
    end
    // 3. Response UPIU → 완료 처리
    else if (actual.txn_type == RESPONSE) begin
      check_response(exp, actual);
      pending_cmds.delete(actual.task_tag);
    end
  endfunction

  function void check_cmd_upiu(utrd_txn exp, upiu_txn actual);
    if (exp.lun !== actual.lun)
      `uvm_error("SCB", $sformatf("LUN mismatch: exp=%0d act=%0d", exp.lun, actual.lun))
    if (exp.cdb !== actual.cdb)
      `uvm_error("SCB", $sformatf("CDB mismatch for tag=%0d", exp.task_tag))
    // ... Expected Data Length, Flags 등 추가 비교
    match_count++;
  endfunction

  function void report_phase(uvm_phase phase);
    `uvm_info("SCB", $sformatf("Match=%0d Mismatch=%0d Timeout=%0d",
              match_count, mismatch_count, timeout_count), UVM_LOW)
    if (pending_cmds.size() > 0)
      `uvm_error("SCB", $sformatf("%0d commands never completed", pending_cmds.size()))
  endfunction
endclass
```

---

## SVA (SystemVerilog Assertions) 예시 — HCI 프로토콜

```systemverilog
// UFS HCI 프로토콜 검증 SVA 예시
module ufs_hci_protocol_checker (
  input logic        clk,
  input logic        rst_n,
  // HCI 레지스터 인터페이스
  input logic        hce,           // Host Controller Enable
  input logic        hcs_dp,        // Device Present (HCS 비트)
  input logic        hcs_ucrdy,     // UIC Command Ready
  input logic        hcs_utrlrdy,   // Transfer Request List Ready
  input logic [31:0] utrldbr,       // Doorbell Register
  input logic [31:0] utrldbr_prev,  // 이전 클럭의 Doorbell
  input logic [31:0] is_reg,        // Interrupt Status
  input logic [31:0] ie_reg,        // Interrupt Enable
  input logic        irq,           // 인터럽트 출력
  // UPIU 인터페이스
  input logic        cmd_upiu_valid,
  input logic [7:0]  cmd_upiu_tag,
  input logic        rsp_upiu_valid,
  input logic [7:0]  rsp_upiu_tag,
  // 내부 상태
  input logic [31:0] utrd_status [32] // 각 슬롯의 OCS
);

  // ── P1: HCE 비활성 시 Doorbell 셋 금지 ──
  property p_no_doorbell_when_disabled;
    @(posedge clk) disable iff (!rst_n)
    (!hce) |-> (utrldbr == '0);
  endproperty

  assert_no_db_disabled: assert property (p_no_doorbell_when_disabled)
    else `uvm_error("HCI_SVA", "Doorbell set while HCE=0")
  cover_no_db_disabled: cover property (p_no_doorbell_when_disabled);

  // ── P2: Doorbell 셋 → Command UPIU 생성 (N 사이클 이내) ──
  localparam int MAX_CMD_LATENCY = 100;

  property p_doorbell_to_cmd_upiu(int slot);
    @(posedge clk) disable iff (!rst_n)
    ($rose(utrldbr[slot])) |->
      ##[1:MAX_CMD_LATENCY] (cmd_upiu_valid && cmd_upiu_tag == slot);
  endproperty

  // slot 0~31에 대해 generate로 인스턴스화
  generate
    for (genvar s = 0; s < 32; s++) begin : gen_db_to_cmd
      assert_db_to_cmd: assert property (p_doorbell_to_cmd_upiu(s))
        else `uvm_error("HCI_SVA",
          $sformatf("Slot %0d: No Cmd UPIU within %0d cycles after Doorbell", s, MAX_CMD_LATENCY))
      cover_db_to_cmd: cover property (p_doorbell_to_cmd_upiu(s));
    end
  endgenerate

  // ── P3: Response UPIU → Doorbell 클리어 + Interrupt ──
  property p_response_clears_doorbell(int slot);
    @(posedge clk) disable iff (!rst_n)
    (rsp_upiu_valid && rsp_upiu_tag == slot) |->
      ##[1:10] (!utrldbr[slot] && is_reg[0]); // IS[UTRCS] 셋
  endproperty

  generate
    for (genvar s = 0; s < 32; s++) begin : gen_rsp_clr
      assert_rsp_clr: assert property (p_response_clears_doorbell(s))
        else `uvm_error("HCI_SVA",
          $sformatf("Slot %0d: Doorbell not cleared after Response", s))
      cover_rsp_clr: cover property (p_response_clears_doorbell(s));
    end
  endgenerate

  // ── P4: Interrupt 출력 = IS & IE 논리곱 ──
  property p_irq_generation;
    @(posedge clk) disable iff (!rst_n)
    (|(is_reg & ie_reg)) |-> irq;
  endproperty

  assert_irq_gen: assert property (p_irq_generation)
    else `uvm_error("HCI_SVA", "IRQ not asserted when IS & IE non-zero")
  cover_irq_gen: cover property (p_irq_generation);

  // ── P5: HCE 토글 → 모든 Doorbell 클리어 ──
  property p_hce_reset_clears_doorbell;
    @(posedge clk) disable iff (!rst_n)
    ($fell(hce)) |-> ##[1:5] (utrldbr == '0);
  endproperty

  assert_hce_clr: assert property (p_hce_reset_clears_doorbell)
    else `uvm_error("HCI_SVA", "Doorbell not cleared after HCE disable")
  cover_hce_clr: cover property (p_hce_reset_clears_doorbell);

  // ── P6: UTRD OCS 상태 전이 (INVALID → SUCCESS 또는 에러) ──
  // OCS: 0x0F = Invalid, 0x00 = Success, others = error
  property p_ocs_valid_transition(int slot);
    @(posedge clk) disable iff (!rst_n)
    (utrd_status[slot] == 8'h0F && $rose(utrldbr[slot])) |->
      s_eventually (utrd_status[slot] != 8'h0F);
  endproperty

endmodule
```

```
SVA 설계 포인트:
  - 모든 assertion에 대응하는 cover property 필수
  - generate로 32개 슬롯 각각에 인스턴스 생성
  - disable iff(!rst_n) — reset 중 assertion 비활성
  - bind 모듈로 DUT에 비침투적 연결
  - 타이밍 파라미터(MAX_CMD_LATENCY 등)는 localparam으로 조정 용이
  - 실 프로젝트에서는 HCI 스펙의 정확한 latency 값 사용
```

---

## Protocol Checker — HCI 규약 검증

```
HCI Protocol Checker가 상시 감시하는 항목:

  1. Doorbell 규약
     - HCE=0 상태에서 Doorbell 셋 → 에러
     - UTRLRSR=0 (Run/Stop=Stop) 상태에서 Doorbell 셋 → 에러
     - 이미 active인 슬롯에 Doorbell 재셋 → 정의된 동작 확인

  2. UTRD 유효성
     - Command Type 필드가 유효한 값인지?
     - Data Direction 필드가 SCSI CDB와 일관성 있는지?
     - PRDT Offset/Length가 유효 범위 내인지?
     - 64-bit 주소 모드에서 상위 32-bit 주소가 올바른지?

  3. UPIU 프로토콜
     - Command UPIU 후 반드시 Response UPIU 수신
     - Task Tag가 유효 범위 내 (0~31)인지?
     - WRITE 시 RTT UPIU 없이 Data-Out 전송 → 프로토콜 위반
     - Data Transfer Length 불일치 → Residual Count 정확 보고

  4. Interrupt 규약
     - IS 비트 Write-1-to-Clear(W1C) 정확 동작?
     - IE 마스킹된 인터럽트 → IRQ 출력 없음?
     - IS 비트 셋 후 SW가 클리어하기 전 동일 이벤트 재발생 → 누락 없음?

  5. Task Management 규약
     - Abort 대상 Task Tag가 실제로 pending 상태인지?
     - LUN Reset 시 해당 LUN의 모든 pending 명령 취소?
     - Task Mgmt 완료 후 관련 Doorbell 비트 클리어?

  위반 시 → 즉시 UVM_ERROR + 위반 내용 + 시뮬레이션 시점 보고
```

---

## Error Injection 방법론

```
목적: DUT의 에러 핸들링 경로가 정확히 동작하는지 검증

에러 주입 지점과 방법:

  1. Device 응답 에러 (Device Agent에서 주입)
     +----------------------------------------------+
     | Response UPIU의 Status 필드 조작:             |
     |   - CHECK_CONDITION (0x02): Sense Data 포함   |
     |   - BUSY (0x08): 디바이스 바쁨                |
     |   - TASK_ABORTED (0x40): 명령 중단됨          |
     |                                               |
     | 검증: UTRD의 OCS에 정확히 반영?               |
     |       IS 인터럽트 정확 발생?                   |
     +----------------------------------------------+

  2. 불완전 전송 (Device Agent에서 주입)
     - READ: 요청한 크기보다 적은 Data-In UPIU 반환
       → Residual Count = (요청 크기 - 실제 전송 크기) 정확?
     - WRITE: RTT에서 요청한 크기보다 적은 버퍼 제공
       → Data-Out 전송량 제한 → Residual Count 정확?

  3. UniPro 링크 에러 (UniPro Agent에서 주입)
     - CRC 에러 → NAK → 자동 재전송 (HCI 투명)
       → 재전송 후 정상 완료 확인
     - Link Down → IS[UE] 인터럽트
       → SW 복구 시퀀스 (Host Reset → Link Re-startup)

  4. DMA 에러 (Host Agent에서 주입)
     - 잘못된 PRDT 주소 (접근 불가 영역)
       → DMA 에러 → IS 에러 비트 + OCS 에러 상태
     - PRDT Length 불일치
       → 데이터 부족/초과 → 정의된 에러 동작

  5. 타임아웃 (Device Agent에서 주입)
     - Response UPIU 의도적 지연 (무한 대기)
       → SW 타임아웃 → Abort Task → Task Mgmt 경로 검증
     - RTT UPIU 의도적 미전송 (WRITE 스톨)
       → WRITE 명령 타임아웃 → 복구 경로

에러 주입 시퀀스 예시:

  class error_inject_vseq extends uvm_sequence;
    task body();
      // 정상 명령 10개 후 에러 1개 패턴
      repeat(10) begin
        `uvm_do_on(normal_read_seq, host_sqr)
      end
      // Device Agent에 에러 응답 지시
      dev_cfg.inject_error = 1;
      dev_cfg.error_status = CHECK_CONDITION;
      `uvm_do_on(normal_read_seq, host_sqr)  // 이 명령에 에러 응답
      dev_cfg.inject_error = 0;
      // 에러 후 정상 명령 재개 확인
      repeat(5) begin
        `uvm_do_on(normal_read_seq, host_sqr)
      end
    endtask
  endclass
```

---

## Regression 전략

```
Regression 단계:

  Phase 1: Smoke (Directed, seed=0)
    - init_test:        HCI 초기화 → NOP → 첫 READ/WRITE
    - single_read_test: 단일 READ 전체 경로
    - single_write_test: 단일 WRITE 전체 경로
    - query_test:       Query Request/Response
    목표: 기본 데이터패스 정상 동작 확인

  Phase 2: Feature (Directed + Constrained-Random, 50 seeds)
    - queue_depth_test:  Queue Depth 1/8/16/24/32
    - multi_lun_test:    복수 LUN 동시 접근
    - task_mgmt_test:    Abort Task, LUN Reset
    - error_test:        각 에러 유형별 응답
    - power_mode_test:   Gear 전환, Hibernate 진입/복귀
    목표: 기능별 정확성 확인

  Phase 3: Stress (Random, 500+ seeds)
    - stress_test:      32 슬롯 포화 + 에러 주입 + Abort 혼합
    - long_running_test: 수만 개 명령 연속 (메모리 릭, 상태 누적 검증)
    목표: 코너 케이스 발견

  Phase 4: Coverage Closure (타겟 시드)
    - Coverage 리포트 분석 → 미커버 bin 식별
    - 해당 bin을 타겟하는 directed sequence 추가
    - 반복: Coverage ≥ 95% 목표

Regression 실행 예시:
  mrun regr --test_suite ufs_hci_smoke --max_parallel_run 8
  mrun regr --test_suite ufs_hci_feature --max_parallel_run 16
  mrun regr --test_suite ufs_hci_stress --max_parallel_run 16
```

---

## 이력서 연결 — UFS HCI 검증 기여

```
Resume:
  "UFS HCI IP Verification – Lead, 6 months" × 2 프로젝트 (S5P9855, V920)
  "Developed and updated coverage-driven testbenches for UFS HCI IP verification"

기여 포인트:
  1. Coverage-Driven TB 개발/업데이트
     - Command × LUN × Size 교차 커버리지 설계
     - Queue Depth 변화에 따른 동작 커버리지
     - Error/Recovery 교차 커버리지

  2. Lead로서 2개 프로젝트 진행
     - S5P9855: 초기 환경 구축 + 기본 시나리오
     - V920: 기존 환경 기반 확장 + 고급 시나리오 (MCQ 등)

  3. BootROM UFS 부팅과의 연결
     - HCI 초기화 시퀀스 검증 (BootROM에서 HCI를 통해 Boot LU 접근)
     - Boot LU Query + READ 시퀀스
```

---

## Q&A

**Q: UFS HCI 검증 환경을 어떻게 설계했나?**
> "양 끝에서 검증하는 구조다. Host Agent가 SW Driver를 모델링하여 UTRD 작성 + Doorbell + ISR 처리를 수행하고, Device Agent가 UFS Device를 모델링하여 UPIU 응답을 생성한다. Scoreboard가 (1) UTRD→UPIU 변환 정확성, (2) DMA 데이터 무결성, (3) 완료 상태 정확성을 검증한다. Coverage-driven으로 Command × LUN × Size, Queue Depth, Error × Recovery를 교차 커버했다."

**Q: Coverage-driven으로 어떤 Coverage를 설계했나?**
> "5개 Covergroup: (1) Command — SCSI Opcode × LUN × 데이터 크기 교차. (2) Queue — Queue Depth × 슬롯 사용 패턴 × R/W 혼합. (3) Error/Recovery — 에러 소스 × 복구 방법 교차. (4) Register — 모든 R/W 레지스터의 접근 패턴. (5) Power/Mode — Gear × Lane × Power Mode 조합. 이 구조로 미커버 영역을 체계적으로 식별하고 Closure를 달성했다."

**Q: UFS HCI 검증에서 SVA를 어떻게 활용했나?**
> "핵심 프로토콜 규약을 SVA로 상시 감시했다. (1) Doorbell→Command UPIU 생성 타이밍 — Doorbell 셋 후 N 사이클 이내 UPIU 전송 확인. (2) Response→Doorbell 클리어 — Response UPIU 수신 후 해당 슬롯 클리어 + IS 비트 셋 확인. (3) Interrupt 정합성 — IS & IE의 논리곱 결과와 IRQ 출력 일치 확인. (4) HCE 리셋 — HCE 비활성 시 모든 Doorbell 클리어 확인. generate로 32개 슬롯 각각에 인스턴스화하고 bind 모듈로 DUT에 비침투적으로 연결했다."

**Q: Scoreboard에서 무엇을 어떻게 비교하는가?**
> "4가지를 비교한다. (1) UTRD→UPIU 변환 — Host Monitor가 UTRD를 캡처하면 예상 UPIU를 생성하고, Device Monitor가 캡처한 실제 UPIU와 Task Tag/LUN/CDB/Data Length를 필드별 비교. (2) DMA 데이터 무결성 — WRITE는 Host 메모리 데이터와 Device 수신 데이터, READ는 Device 송신 데이터와 Host 메모리 DMA 결과를 비교. (3) 완료 상태 — Response UPIU의 Status와 UTRD의 OCS가 일치하는지. (4) 순서 — 같은 LUN 내 명령 순서 보장을 확인. Task Tag를 key로 pending 명령을 추적하여 response와 매칭한다."

**Q: Error Injection은 어떻게 수행하는가?**
> "에러는 TB의 Device Agent와 UniPro Agent에서 주입하며, DUT RTL은 절대 수정하지 않는다. (1) Device 응답 에러 — Response UPIU의 Status를 CHECK_CONDITION/BUSY로 조작. (2) 불완전 전송 — 요청 크기보다 적은 데이터 반환 → Residual Count 정확성. (3) 링크 에러 — UniPro CRC 에러 주입 → 재전송 투명성, Link Down → IS[UE]. (4) 타임아웃 — Response 의도적 지연 → Task Management 복구 경로. 정상→에러→정상 패턴으로 에러 후 복구까지 검증한다."

<div class="chapter-nav">
  <a class="nav-prev" href="03_upiu_command_flow.md">
    <div class="nav-label">◀ 이전</div>
    <div class="nav-title">UPIU와 명령 처리 흐름</div>
  </a>
  <a class="nav-next" href="05_quick_reference_card.md">
    <div class="nav-label">다음 ▶</div>
    <div class="nav-title">UFS HCI — Quick Reference Card</div>
  </a>
</div>
