# Ch05. Command·Truth Table·Burst Operation

<div class="chapter-context" data-cat="memory">
  <a class="chapter-back" href="../"><span class="chapter-back-arrow">←</span><span class="chapter-back-icon">📚</span> DRAM JEDEC Deep-Dive</a>
  <span class="chapter-divider">›</span>
  <span class="chapter-marker">CH 05</span>
</div>

## 🎯 Learning Objectives

- **Decode**: DDR5의 2-cycle command 인코딩 구조를 디코딩한다.
- **Compare**: DDR4의 1-cycle command와 DDR5의 2-cycle command를 monitor 설계 관점에서 비교한다.
- **Trace**: BL16/BL32 burst의 cycle-by-cycle data path를 추적한다.
- **Apply**: Command coverpoint, command-order SVA, burst-order scoreboard rule을 작성한다.

## Prerequisites

- [Ch04. Mode Register 깊이 분석](04_mode_registers.md)
- SystemVerilog enum, randomization, sequence_item 기초

## 1. Command Truth Table — DRAM 명령 체계

### 1.1 핵심 명령 7가지

DRAM이 받을 수 있는 명령은 *놀랍게도 적습니다*. 모든 동작은 이 명령들의 *조합*입니다.

| 명령 | 약어 | 기능 |
|---|---|---|
| Activate | ACT | row 활성화 (sense amp으로 row buffer 로드) |
| Read | RD | column 선택 후 DQ에 burst 출력 |
| Write | WR | DQ에서 burst 입력 후 column 기록 |
| Precharge | PRE | row buffer 닫고 bit line 복원 |
| Refresh | REF | 모든 bank 또는 per-bank refresh |
| Mode Register Write | MRW (또는 MRS) | MR 값 설정 |
| Mode Register Read | MRR | MR 값 읽기 (DDR5+) |

추가 명령:
- ZQCS/ZQCL: ZQ Calibration Short/Long
- NOP: No Operation
- DES: Deselect (CS_n high)
- SREF Entry/Exit, PD Entry/Exit: Self-Refresh / Power-Down
- RFM, DRFM, ARFM: Refresh Management (DDR5/LPDDR5)
- WCK2CK Sync (LPDDR5)

### 1.2 명령 인코딩 — Pin 신호의 조합

#### DDR4 (1-cycle)

DDR4에서 명령은 *RAS_n / CAS_n / WE_n / ACT_n + ADDR + BG + BA* 의 *조합*입니다. ACT_n이 LOW면 ACT 명령, HIGH면 RAS_n/CAS_n/WE_n이 다른 명령을 인코딩.

> 출처: JESD79-4D §4.1 Command Truth Table

#### DDR5 (2-cycle)

> 출처: JESD79-5C.01 v1.31 §4.1

DDR5는 *CA[6:0]* 7-bit 핀에 *2 클럭에 걸쳐* 인코딩:

```
Cycle 0 (CA[6:0]):  OPCODE 일부 + 일부 주소
Cycle 1 (CA[6:0]):  OPCODE 나머지 + 나머지 주소
```

CS_n이 LOW인 *2 cycles 동안*이 하나의 명령. DDR5의 *2-Cycle Command Cancel* (§4.1.1) 으로 명령이 *부분적으로* 발급된 상태를 *취소*하는 메커니즘도 있음.

!!! warning "DV 함정 — DDR5 monitor 설계"
    DDR5 명령은 *2 클럭 윈도우*로 보아야 합니다. monitor가 cycle 0 만 보고 명령을 reconstruct하면 *명령이 부분적*이고 ADDR이 잘못 인코딩됩니다.

---

## 2. DDR5 2-Cycle Command 인코딩 — 자세히

### 2.1 인코딩 구조 (개념)

DDR5의 각 명령은 *고정된 OPCODE pattern* + *주소 비트 분포*가 있습니다. 예시 (ACT — 가정 형식):

```
Cycle 0:
  CA[6]: ACT identifier
  CA[5:4]: BA[1:0]
  CA[3:1]: BG[2:0]
  CA[0]: ROW MSB ... (일부)

Cycle 1:
  CA[6:0]: ROW[16:0] 나머지 (인코딩 분할)
```

> 위는 *학습용 가정* — 정확한 비트 매핑은 *JESD79-5C.01 §4.1 Command Truth Table* 을 *반드시* 확인하세요.

### 2.2 CS_n 의 역할 — 2 cycles 동안

CS_n은 *명령의 시작*을 표시:
- CS_n = LOW (cycle 0) + LOW (cycle 1) → 2-cycle command 의미
- CS_n = LOW (cycle 0) + HIGH (cycle 1) → 1-cycle command (예: NOP, DES)
- CS_n = HIGH for both cycles → no command

DDR5에서 *NOP*과 *DES (Deselect)* 처럼 1-cycle 인 것과 *ACT/RD/WR/PRE/REF/MRW* 같이 2-cycle인 것이 *섞여* 있습니다. monitor는 *각 cycle의 CS_n*을 보고 윈도우 길이를 결정합니다.

---

## 3. Burst Operation — BL16 / BL32

> 출처: JESD79-5C.01 §4.2 / JESD209-5C §7.4

### 3.1 Burst Length 옵션

| 표준 | BL 옵션 |
|---|---|
| DDR4 | BL8 (default), BC4 (Burst Chop 4) |
| DDR5 | **BL16 (default), BL32 (optional)** |
| LPDDR4 | BL16, BL32 |
| LPDDR5 | BL16, BL32 |

### 3.2 DDR5 BL16 동작

```
Time:           T0 T1 T2 T3 T4 T5 T6 T7 T8 T9 T10 T11 T12 T13 T14 T15
DQ (x8):        D0 D1 D2 D3 D4 D5 D6 D7 D8 D9 DA  DB  DC  DD  DE  DF
                ▲                                                     ▲
                burst start                                       burst end
                (CL clocks after RD command)
```

- DDR이므로 *each half-clock에 1 beat* → 16 beats = 8 nCK
- x8 device 기준: 16 × 8 = 128 bits = 16 bytes per access
- DDR5 channel 32-bit 환산: 16 beats × 32-bit = 512 bits = 64 bytes = 1 cache line

### 3.3 BL32 — 두 배 burst

BL32는 *동일한 명령으로* 32 beats 전송. DDR5 §4.2.1 *Burst Type and Burst Order for Optional BL32 Mode*.

```
RD with BL32:
  Time:  T0 ... T15 T16 ... T31
  DQ:    [first 16 beats] [second 16 beats]
```

장점: 큰 sequential read일 때 명령 overhead 감소.
단점: 중간 *interrupt 불가* — bank 전환이 늦어짐.

### 3.4 Burst Order

DDR4의 *interleaved* vs *sequential* burst order는 DDR5에서도 유지. 시작 column에 따라 데이터 순서가 정해짐:

| Mode | 시작 col=0의 burst order (BL16) |
|---|---|
| Sequential | 0,1,2,3,...,15 |
| Interleaved | 0,1,2,3,4,5,6,7 의 비트 순서 변경 (8-burst grouping) |

DDR5에서는 *sequential*이 일반적이지만, BL32와 함께 *옵션 설정*이 있을 수 있음 (§4.2.1).

---

## 4. DDR5 Preamble / Postamble (요약 — Ch06에서 상세)

> 출처: JESD79-5C.01 §4.4

- **Read Preamble**: DQS가 burst 전에 *정해진 패턴* (예: 0→1→0 sequence)을 보여 host receiver가 sample timing을 잡도록
- **Write Preamble**: host가 DQS를 burst 전에 *정해진 패턴*으로 전송
- **Postamble**: burst 종료 후 DQS 마감 패턴

MR8 (Preamble/Postamble) 에서 길이 설정. *DV 핵심*: monitor가 *preamble 패턴*을 정확히 인식해야 burst 시작점을 잡을 수 있음.

---

## 5. DV 적용 — Command Coverage 모델

### 5.1 Command opcode coverage

```systemverilog
typedef enum logic [3:0] {
    CMD_DES   = 4'h0,  // Deselect
    CMD_NOP   = 4'h1,  // No-op
    CMD_ACT   = 4'h2,
    CMD_PRE   = 4'h3,
    CMD_RD    = 4'h4,
    CMD_RDA   = 4'h5,  // RD with Auto-precharge
    CMD_WR    = 4'h6,
    CMD_WRA   = 4'h7,  // WR with Auto-precharge
    CMD_REF   = 4'h8,
    CMD_MRW   = 4'h9,
    CMD_MRR   = 4'hA,
    CMD_ZQCL  = 4'hB,
    CMD_ZQCS  = 4'hC,
    CMD_RFM   = 4'hD,
    CMD_PDE   = 4'hE,  // Power-Down Entry
    CMD_PDX   = 4'hF   // Power-Down Exit
} ddr5_cmd_e;

covergroup ddr5_cmd_cg with function sample (ddr5_cmd_e cmd);
    cp_cmd: coverpoint cmd {
        bins basic[]     = {CMD_ACT, CMD_PRE, CMD_RD, CMD_WR, CMD_REF};
        bins auto_pre[]  = {CMD_RDA, CMD_WRA};
        bins mr_access[] = {CMD_MRW, CMD_MRR};
        bins refresh_mgmt = {CMD_RFM};
        bins zq[]        = {CMD_ZQCS, CMD_ZQCL};
        bins power[]     = {CMD_PDE, CMD_PDX};
        ignore_bins idle = {CMD_DES, CMD_NOP};
    }
endgroup
```

### 5.2 Command transition (sequence) coverage

명령의 *순서*가 정상인지 검증:

```systemverilog
covergroup ddr5_cmd_seq_cg with function sample (ddr5_cmd_e prev, ddr5_cmd_e curr);
    cp_seq: coverpoint {prev, curr} {
        bins act_then_rd  = {{CMD_ACT, CMD_RD}};
        bins act_then_wr  = {{CMD_ACT, CMD_WR}};
        bins rd_then_pre  = {{CMD_RD, CMD_PRE}};
        bins wr_then_pre  = {{CMD_WR, CMD_PRE}};
        bins pre_then_act = {{CMD_PRE, CMD_ACT}};
        bins ref_after_pre_all = {{CMD_PRE, CMD_REF}};
        // illegal sequences는 ignore — SVA가 catch
        ignore_bins illegal = {{CMD_RD, CMD_RD},     // same bank back-to-back (depends)
                               {CMD_WR, CMD_RD}};    // tWTR 위반 가능
    }
endgroup
```

### 5.3 BL16 vs BL32 coverage

```systemverilog
covergroup burst_len_cg with function sample (int bl, ddr5_cmd_e cmd);
    cp_bl: coverpoint bl {
        bins bl16 = {16};
        bins bl32 = {32};
    }
    cp_cmd: coverpoint cmd {
        bins rd = {CMD_RD, CMD_RDA};
        bins wr = {CMD_WR, CMD_WRA};
    }
    cx_bl_cmd: cross cp_bl, cp_cmd;
endgroup
```

---

## 6. DV 적용 — Command Order SVA

### 6.1 ACT 후 같은 bank에 ACT는 *불법* (PRE 필요)

```systemverilog
// 같은 bank에서 ACT→ACT 사이에 반드시 PRE가 있어야 함
// 출처: JESD79-5C.01 §3.1 Simplified State Diagram
property p_act_after_act_needs_pre;
    @(posedge clk) disable iff (!reset_n)
    (cmd_decoded == CMD_ACT) |->
        not (##[1:$] (cmd_decoded == CMD_ACT && same_bank(bank, $past(bank))))
        intersect not (##[1:$] (cmd_decoded == CMD_PRE && same_bank(bank, $past(bank))));
endproperty
a_act_after_act: assert property (p_act_after_act_needs_pre)
    else `uvm_error("ASSERT", "ACT→ACT to same bank without PRE")
```

> 위 SVA는 *개념 설명용*입니다. 실제 작성 시 `same_bank()` function, `intersect`의 사용 등은 EDA tool과 시뮬레이션 환경에 맞게 다듬어야 합니다. 보다 robust한 표현은 *FSM 모델링 후 transition 검증*이 권장됩니다.

### 6.2 PRE 후 즉시 ACT는 *불법* (tRP 위반)

```systemverilog
// PRE 후 tRP 클럭 이내에 ACT 발급 금지
property p_pre_to_act_trp;
    @(posedge clk)
    (cmd_decoded == CMD_PRE && bank == B) |->
        ##[`TRP_NCK : $] (cmd_decoded == CMD_ACT && bank == B);
endproperty
a_pre_to_act: assert property (p_pre_to_act_trp);
```

### 6.3 RD 후 즉시 WR은 *제약 있음*

```systemverilog
// RD에서 WR로 전환 시 최소 latency (tRTW) 보장
property p_rd_to_wr_trtw;
    @(posedge clk)
    (cmd_decoded == CMD_RD) |->
        ##[`TRTW_NCK : $] (cmd_decoded == CMD_WR);
endproperty
a_rd_to_wr: assert property (p_rd_to_wr_trtw);
```

---

## 7. Burst Order Scoreboard Rule

scoreboard가 RD burst와 WR burst의 데이터 순서를 *추적*해야 함:

```systemverilog
class ddr5_scoreboard extends uvm_scoreboard;
    `uvm_component_utils(ddr5_scoreboard)

    // Memory mirror — controller가 본 데이터를 추적
    bit [7:0] mem_model [longint];  // address → data

    uvm_analysis_imp #(ddr5_transaction, ddr5_scoreboard) wr_imp;
    uvm_analysis_imp #(ddr5_transaction, ddr5_scoreboard) rd_imp;

    function void write_wr(ddr5_transaction t);
        for (int i = 0; i < t.bl; i++) begin
            // burst order는 sequential 가정 (DDR5 default)
            longint addr = compute_addr(t.bg, t.ba, t.row, t.col + i);
            mem_model[addr] = t.data[i];
            `uvm_info("SB_WR", $sformatf("WR @0x%x = 0x%02x", addr, t.data[i]), UVM_HIGH)
        end
    endfunction

    function void write_rd(ddr5_transaction t);
        for (int i = 0; i < t.bl; i++) begin
            longint addr = compute_addr(t.bg, t.ba, t.row, t.col + i);
            if (!mem_model.exists(addr)) begin
                `uvm_warning("SB_RD", $sformatf("RD @0x%x: addr never written, comparing X", addr))
                continue;
            end
            if (mem_model[addr] !== t.data[i])
                `uvm_error("SB_MISMATCH",
                    $sformatf("RD @0x%x: expected 0x%02x, got 0x%02x",
                              addr, mem_model[addr], t.data[i]))
        end
    endfunction
endclass
```

!!! tip "Scoreboard 함정 — burst order"
    DDR5 BL16에서 *sequential*이 default이지만, BL32 또는 *interleaved 옵션*에서는 burst order가 다릅니다. scoreboard의 `t.col + i` 계산이 *burst order에 따라* 달라져야 합니다 (MR0 또는 MR1 값 참조).

---

## 8. 대표 문제 — DDR5 2-cycle command monitor reconstruct dry-run

!!! question "Q. 다음 8 cycles의 CS_n / CA[6:0] 신호를 보고, 몇 개의 명령이 발급되었는지 그리고 각 명령이 무엇인지 추적하라."

    ```
    Cycle:   0      1      2      3      4      5      6      7
    CS_n:    LOW    LOW    HIGH   LOW    HIGH   LOW    LOW    HIGH
    CA[6:0]: A0     A1     XX     B0     XX     C0     C1     XX
    ```

    가정: 2-cycle command는 CS_n이 *2 cycles 연속 LOW*, 1-cycle command (NOP/DES)는 CS_n이 *cycle 0만 LOW*. cycle 4의 XX는 don't care.

???+ answer "풀이 (사고 과정 + monitor logic)"

    **Step 1 — CS_n 윈도우 분석**

    | Cycle | CS_n | 분석 |
    |---|---|---|
    | 0 | LOW | 명령 시작 — 2-cycle 명령일 가능성 |
    | 1 | LOW | 명령 계속 — 2-cycle 명령 확정 |
    | 2 | HIGH | (cycle 0-1)의 명령 완료, idle |
    | 3 | LOW | 새 명령 시작 |
    | 4 | HIGH | (cycle 3) 이 *1-cycle* 명령 (NOP/DES) |
    | 5 | LOW | 새 명령 시작 |
    | 6 | LOW | 2-cycle 명령 계속 |
    | 7 | HIGH | (cycle 5-6)의 명령 완료, idle |

    **Step 2 — 명령 reconstruct**

    - **Command #1** (cycles 0-1): CA[6:0]={A0, A1}, 2-cycle 명령
    - **Command #2** (cycle 3): CA[6:0]={B0}, 1-cycle 명령 (NOP/DES)
    - **Command #3** (cycles 5-6): CA[6:0]={C0, C1}, 2-cycle 명령

    총 **3개의 명령** (2개의 2-cycle + 1개의 1-cycle)

    **Step 3 — Monitor 구현 의사코드**

    ```systemverilog
    // Monitor — DDR5 command capture
    always @(posedge clk) begin
        if (cs_n_curr == 1'b0) begin
            if (waiting_for_2nd_cycle) begin
                // 2nd cycle of 2-cycle command
                cmd_cycle1 <= ca;
                emit_command({cmd_cycle0, ca});  // analysis_port에 publish
                waiting_for_2nd_cycle <= 0;
            end else begin
                cmd_cycle0 <= ca;
                waiting_for_2nd_cycle <= 1;
            end
        end else begin
            if (waiting_for_2nd_cycle) begin
                // 직전 cycle은 1-cycle 명령 (CS_n HIGH가 2nd cycle을 부정)
                emit_command({cmd_cycle0});  // NOP/DES 등
                waiting_for_2nd_cycle <= 0;
            end
            // else: idle
        end
    end
    ```

    **Step 4 — DV 함의**

    - Monitor의 `waiting_for_2nd_cycle` 상태가 *항상 reset 시 0*인지 확인 (race condition)
    - 명령 publish 시 *cycle 단위 시점* (`$time`) 도 포함해 timing checker 와 일치
    - covergroup에 cycle 0/1 인코딩 *각각*을 cover (1-cycle vs 2-cycle 비율)
    - SVA: `waiting_for_2nd_cycle == 1` 인 상태에서 `reset_n == 0` 이 들어오면 *복구* 검증

---

## 9. LPDDR5 — CAS + WCK Sync Bits

> 출처: JESD209-5C §7.2.1.2

LPDDR5의 *CAS* 명령은 WCK Sync 비트를 *함께* 인코딩 — WCK가 CK와 *지속적으로* 동기화되는지 확인. DV는 *CAS 시점*과 *WCK toggle*을 cross-checking.

(LPDDR5 training 상세는 [Ch08](08_training.md) 참조)

---

## 10. 핵심 정리 (Key Takeaways)

- DRAM 명령은 본질적으로 7개 (ACT/RD/WR/PRE/REF/MRW/MRR) + 보조 (ZQ, NOP, DES, PDE/PDX).
- DDR5는 *2-cycle command* — CA[6:0]에 2 클럭에 걸쳐 인코딩. CS_n의 *2-cycle 윈도우*가 핵심.
- BL16이 default, BL32는 옵션 (sequential 대량 전송 시 유리).
- Command coverage는 *opcode 단순 cover* + *sequence (transition) cover* + *BL × cmd cross* 의 3축.
- SVA로 *불법 명령 순서* (ACT→ACT without PRE, tRP 위반 등) 즉시 catch.
- Scoreboard의 burst order 계산은 *MR0/MR1 설정에 의존* — burst order MR 변경 시 scoreboard 로직도 따라가야 함.

## 11. Further Reading

- 이전: [Ch04. Mode Register 깊이 분석](04_mode_registers.md)
- 다음: [Ch06. Timing·Preamble·Postamble](06_timing_preamble.md)
- 부록 C: [SVA / Coverage 예제 모음](appendix_c_sva_coverage_examples.md)
- 퀴즈: [Ch05 퀴즈](quiz/ch05_quiz.md)

<div class="chapter-nav">
  <a class="nav-prev" href="../04_mode_registers/">
    <div class="nav-label">← 이전</div>
    <div class="nav-title">Ch04. Mode Register</div>
  </a>
  <a class="nav-next" href="../06_timing_preamble/">
    <div class="nav-label">다음 →</div>
    <div class="nav-title">Ch06. Timing·Preamble</div>
  </a>
</div>
