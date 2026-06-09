---
title: "Ch05. Command·Truth Table·Burst Operation"
---

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

- [Ch04. Mode Register 깊이 분석](../04_mode_registers/)
- SystemVerilog enum, randomization, sequence_item 기초

## 1. Command Truth Table — DRAM 명령 체계

### 1.1 핵심 명령 7가지

DRAM이 받을 수 있는 명령은 놀랍게도 매우 적습니다. 메모리 컨트롤러가 수백 가지 복잡한 시나리오를 처리하는 것처럼 보여도, 결국 DRAM 핀 레벨에서 주고받는 명령은 아래 7개의 조합으로 표현됩니다. 이 명령들의 순서와 타이밍이 곧 DRAM 프로토콜입니다.

_왜 단 7개로 충분한가_ 는 DRAM 의 모든 접근이 하나의 패턴으로 환원되기 때문입니다. 1T1C 셀과 destructive read 라는 물리(Ch01) 때문에, 어떤 read 든 write 든 결국 **row 를 연다(ACT) → 그 안에서 column 을 골라 데이터를 주고받는다(RD/WR) → row 를 닫는다(PRE)** 라는 단일 시퀀스를 거칠 수밖에 없습니다. 여기에 capacitor 누설을 메우는 REF, 동작 모드를 설정·조회하는 MRW/MRR 만 더하면 DRAM 이 해야 할 일이 전부 덮입니다. SSD 처럼 "정렬·검색·매핑" 같은 고수준 의미 연산이 없고 — DRAM 은 그저 주소가 가리키는 셀을 충실히 열고 닫을 뿐이라 — 명령 집합이 이 한 패턴을 표현하는 최소한으로 작아지는 것입니다. (ZQ·power-down 같은 보조 명령은 이 핵심 패턴을 _유지_ 하기 위한 부수 동작입니다.)

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

DDR5는 CA[6:0] 7-bit 핀에 2 클럭에 걸쳐 인코딩합니다. DDR4가 17-bit row address, bank group, bank를 한 클럭에 넓은 address bus로 전달했다면, DDR5는 핀 수를 줄이는 대신 2 클럭을 활용하는 방식을 택했습니다. 이는 pin count를 낮추는 동시에 CA 핀 각각에서 더 정확한 signal integrity를 확보할 수 있는 장점이 있습니다.

```
Cycle 0 (CA[6:0]):  OPCODE 일부 + 일부 주소
Cycle 1 (CA[6:0]):  OPCODE 나머지 + 나머지 주소
```

**CS_n**(chip select, LOW일 때만 그 칩이 명령을 받아들이게 하는 선택 신호)이 LOW인 2 cycles 동안이 하나의 명령입니다. 중요한 예외 케이스가 있는데, DDR5의 2-Cycle Command Cancel(§4.1.1)은 1st cycle 발급 후 2nd cycle의 CS_n도 LOW로 유지되면 명령 자체를 취소하는 메커니즘입니다. 이는 **RCD**(registering clock driver, RDIMM에서 controller의 명령·주소를 받아 여러 DRAM 칩에 되실어 보내는 버퍼 칩)가 **CA parity**(명령·주소 신호의 패리티) error를 감지했을 때 발동됩니다.

:::caution[DV 함정 — DDR5 monitor 설계]
DDR5 명령은 *2 클럭 윈도우*로 보아야 합니다. monitor가 cycle 0 만 보고 명령을 reconstruct하면 *명령이 부분적*이고 ADDR이 잘못 인코딩됩니다.
:::
---

## 2. DDR5 2-Cycle Command 인코딩 — 자세히

### 2.1 인코딩 구조 (개념)

DDR5의 각 명령은 고정된 OPCODE pattern과 주소 비트 분포를 가집니다. spec의 §4.1.1에서 "CA1 비트가 1-cycle vs 2-cycle 명령의 식별자" 라고 명시하는데, 이는 monitor가 첫 cycle을 보자마자 2 클럭 윈도우가 필요한지를 판단할 수 있다는 의미입니다. 예시 (ACT — 가정 형식):

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

BL32는 동일한 명령으로 32 beats를 전송합니다. DDR5 §4.2.1 *Burst Type and Burst Order for Optional BL32 Mode*에 정의됩니다.

```
RD with BL32:
  Time:  T0 ... T15 T16 ... T31
  DQ:    [first 16 beats] [second 16 beats]
```

BL32를 쓰면 명령 overhead가 줄어든다는 장점이 있습니다. 같은 양의 데이터를 두 번의 BL16 명령으로 전송할 경우 두 번의 명령 overhead가 발생하지만, BL32 하나로 전송하면 명령 1회분의 overhead만 소모합니다. 대용량 sequential read, 예를 들어 DMA copy 같은 워크로드에서 유리합니다. 그러나 burst 도중 다른 bank에 접근하거나 burst를 중단하기가 어렵다는 단점이 있어, latency가 중요하거나 bank 전환이 잦은 경우에는 BL16이 더 적합합니다. DV는 두 모드 모두 coverage에 잡아야 합니다.

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

여기서 **tRTW**(read-to-write, RD 명령에서 WR 명령으로 전환할 때 데이터 버스 방향이 충돌하지 않도록 두는 최소 간격)와 짝이 되는 **tWTR**(write-to-read, WR 후 RD로 전환할 때의 최소 간격)을 알아 둡니다.

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

:::tip[Scoreboard 함정 — burst order]
DDR5 BL16에서 *sequential*이 default이지만, BL32 또는 *interleaved 옵션*에서는 burst order가 다릅니다. scoreboard의 `t.col + i` 계산이 *burst order에 따라* 달라져야 합니다 (MR0 또는 MR1 값 참조).
:::
---

## 8. 대표 문제 — DDR5 2-cycle command monitor reconstruct dry-run

:::tip[Q. 다음 8 cycles의 CS_n / CA[6:0) 신호를 보고, 몇 개의 명령이 발급되었는지 그리고 각 명령이 무엇인지 추적하라.]

```
Cycle:   0      1      2      3      4      5      6      7
CS_n:    LOW    LOW    HIGH   LOW    HIGH   LOW    LOW    HIGH
CA[6:0]: A0     A1     XX     B0     XX     C0     C1     XX
```

가정: 2-cycle command는 CS_n이 *2 cycles 연속 LOW*, 1-cycle command (NOP/DES)는 CS_n이 *cycle 0만 LOW*. cycle 4의 XX는 don't care.
:::
<details>
<summary>풀이 (사고 과정 + monitor logic)</summary>


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

**Step 3 — Monitor 구현 pseudo code**

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

</details>
---

## 9. LPDDR5 — CAS + WCK Sync Bits

> 출처: JESD209-5C §7.2.1.2

LPDDR5의 *CAS* 명령은 WCK Sync 비트를 *함께* 인코딩 — WCK가 CK와 *지속적으로* 동기화되는지 확인. DV는 *CAS 시점*과 *WCK toggle*을 cross-checking.

(LPDDR5 training 상세는 [Ch08](../08_training/) 참조)

---

## 10. PDF 정밀 인용 — DDR5 §4.1 Command Truth Table

> 출처: JESD79-5C.01 v1.31 §4.1, Table 30 (Command Truth Table)

### 10.1 Truth Table 구조 — §4.1 원문 설명

> §4.1 원문 인용:
> "To improve command decode time, the table has been **optimized to orient all 1-cycle commands together and all 2-cycle commands together**; **allowing CA1 to be used to identify the difference between a 1-cycle and a 2-cycle command**."

핵심:
- DDR5의 명령은 *1-cycle*과 *2-cycle*로 나뉨
- **CA1 비트**가 1-cycle vs 2-cycle 식별자
- 1-cycle 명령들이 한 블록, 2-cycle 명령들이 한 블록으로 정렬

명령 약어:
- BG = Bank Group Address
- BA = Bank Address
- R = Row Address
- C = Column Address
- MRA = Mode Register Address
- OP = Op Code
- CID = Chip ID
- CW = Control Word
- X = Don't Care
- V = Valid (H or L, defined logic level)

### 10.2 Table 30 — 핵심 명령 인코딩 정밀 인용

각 명령은 *CS_n*과 *CA[13:0]* 으로 인코딩됨. **L = LOW, H = HIGH, V = Valid (defined), X = Don't Care**.

**Activate (ACT) — 2-cycle 명령**

| CS_n | CA0 | CA1 | CA2 | CA3 | CA4 | CA5 | CA6 | CA7 | CA8 | CA9 | CA10 | CA11 | CA12 | CA13 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| L (1st cycle) | L | L | R0 | R1 | R2 | R3 | BA0 | BA1 | BG0 | BG1 | BG2 | CID0 | CID1 | CID2 |
| H (2nd cycle) | R4 | R5 | R6 | R7 | R8 | R9 | R10 | R11 | R12 | R13 | R14 | R15 | R16 | CID3/R17 |

→ ACT는 BG, BA, ROW 비트를 2 cycle에 걸쳐 인코딩. CID0~CID3는 3DS stacking 식별.

**Mode Register Write (MRW) — 2-cycle**

| CS_n | CA0 | CA1 | CA2 | CA3 | CA4 | CA5 | CA6 | CA7 | CA8 | CA9 | CA10 | CA11 | CA12 | CA13 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| L | H | L | H | L | H | MRA0 | MRA1 | MRA2 | MRA3 | MRA4 | MRA5 | MRA6 | MRA7 | V |
| H | OP0 | OP1 | OP2 | OP3 | OP4 | OP5 | OP6 | OP7 | V | V | CW | V | V | V |

→ MRA0~MRA7 (8-bit MR 주소) + OP0~OP7 (8-bit payload) + CW (Control Word for RCD).

**Mode Register Read (MRR) — 2-cycle**

| CS_n | CA0 | CA1 | CA2 | CA3 | CA4 | CA5 | CA6 | CA7 | CA8 | CA9 | CA10 | CA11 | CA12 | CA13 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| L | H | L | H | L | H | MRA0 | MRA1 | MRA2 | MRA3 | MRA4 | MRA5 | MRA6 | MRA7 | V |
| H | V | V | V | V | V | V | V | V | V | V | CW | V | V | V |

**Write (WR) — 2-cycle**

| CS_n | CA0 | CA1 | CA2 | CA3 | CA4 | CA5 | CA6 | CA7 | CA8 | CA9 | CA10 | CA11 | CA12 | CA13 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| L | H | L | H | H | L | BL*=L | BA0 | BA1 | BG0 | BG1 | BG2 | CID0 | CID1 | CID2 |
| H | V | C3 | C4 | C5 | C6 | C7 | C8 | C9 | C10 | V | **H** (AP=H, no auto-pre) | WR Partial=L | V | CID3 |

> NOTE 15: "If CA5:BL*=L, the command places the DRAM into the alternate Burst mode described by MR0[1:0] instead of the default Burst Length 16 mode."

**Write w/ Auto-Precharge (WRA) — 2-cycle**

cycle 2의 CA10 위치에 **AP=L** (Auto-Precharge 활성). 나머지는 WR과 동일.

**Read (RD) — 2-cycle**

WR과 유사하지만 cycle 1의 CA0~CA4 = `H L H H H` (RD identifier 다름) + cycle 2의 *WR Partial 위치* 가 *Read DRFM=L* (Refresh Management Indication).

**Precharge (PREpb / PREsb / PREab) — 1-cycle**

| Function | CS_n | CA0 | CA1 | CA2 | CA3 | CA4 | CA5 | CA6 | CA7 | CA8 | CA9 | CA10 | CA11 | CA12 | CA13 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **PREab** (All) | L | H | H | L | H | L | CID3 | V | V | V | V | L | CID0 | CID1 | CID2 |
| **PREsb** (Same Bank) | L | H | H | L | H | L | CID3 | BA0 | BA1 | V | V | H | CID0 | CID1 | CID2 |
| **PREpb** (Per-Bank) | L | H | H | L | H | H | CID3 or DRFM=L | BA0 | BA1 | BG0 | BG1 | BG2 | CID0 | CID1 | CID2 |

**Refresh (REFab / REFsb / RFMab / RFMsb) — 1-cycle**

| Function | CA0 | CA1 | CA2 | CA3 | CA4 | CA5 | CA6 | CA7 | CA8 | CA9 | CA10 | CA11 | CA12 | CA13 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **REFab** | H | H | L | H | L | V or RIR | V or H | H | CID3 | CID0 | CID1 | CID2 | | |
| **RFMab** | H | H | H | L | L | CID3 or DRFM=L | V or RIR | V or H | H | CID0 | CID1 | CID2 | | |
| **REFsb** | H | H | L | H | H | CID3 | BA0 | BA1 | V or H | V or H | H | CID0 | CID1 | CID2 |
| **RFMsb** | H | H | H | L | H | CID3 or DRFM=L | BA0 | BA1 | V or H | H | CID0 | CID1 | CID2 | |

> (위 표의 **RIR** = Refresh Interval Rate indicator, refresh 간격 배율을 알려주는 비트.)
>
> NOTE 23: "When the Refresh Management Required bit is '0' (MR58 OP[0]=0), CA9 is only required to be valid ('V') for a REF command, and the DRAM will treat a RFM command as a REF command. If MR58 OP[0]=1, a REF command requires CA9=H."

**Self Refresh Entry / Power Down Entry — 1-cycle**

| Function | CA0 | CA1 | CA2 | CA3 | CA4 | CA5 | CA6 | CA7 | CA8 | CA9 | CA10 | CA11 | CA12 | CA13 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **SRE** | H | H | H | H | L | V | V | V | V | **H** (CKE-related) | L | V | V | V |
| **SREF** w/ Freq Change | H | H | H | H | H | V | V | V | V | H | L | V | V | V |
| **PDE** | H | H | H | L | H | V | V | V | V | V | V | V | V | V (ODT=L) |

### 10.3 §4.1.1 — 2-Cycle Command Cancel (정밀 인용)

> §4.1.1 원문 인용:
> "DDR5 DRAM commands **ACT, WRP, WRPA and MRW are 2-cycle commands without associated ODT control requirements**. The DRAM will not execute these 2-cycle commands if the CS_n is LOW on the 2nd cycle (command cancel)."
>
> "If the RCD detects a parity error on the 2nd cycle of two-cycle command, the CS_n will remain LOW for both 1st and 2nd cycle of the command. **If the command is either Read, Write or MRR**, then it will be converted to **non-target termination command** in the DRAM. **If the command is either ACT, WRP, WRPA or MRW**, then the erroneous command will be **canceled** in the DRAM."
>
> "Command cancel is not intended by the host rather it is a result of CA parity error detected by the RCD. So the relationship between canceled command and the next valid command shall not be illegal. For example, MRR cannot be issued after canceled ACT even with tCMD_cancel satisfied. **In that case, the host is supposed to issue PRE first before issuing MRR**."

**Table 31 — Command Cancel Timing**

| Parameter | Symbol | DDR5 3200~6400 (Min/Max) | DDR5 6800~8800 (Min/Max) | Unit |
|---|---|---|---|---|
| Command cancel timing for ACT, WRP, WRPA, MRW when CS_n is low on 2nd cycle | **tCMD_cancel** | **8 nCK** / - | **8 nCK** / - | nCK |

DV 적용 — 2-cycle cancel SVA:
```systemverilog
// 출처: JESD79-5C.01 §4.1.1 Table 31
// 2-cycle 명령의 1st cycle 후 2nd cycle CS_n이 LOW면 cancel
// cancel 후 *tCMD_cancel* 이상 지나야 다음 valid 명령 가능
property p_cmd_cancel_recovery;
    @(posedge clk)
    (cs_n_2cycle_cmd_cancel_detected) |->
        ##[`TCMD_CANCEL_NCK : $]
        first_match(cmd_decoded != CMD_NOP && cmd_decoded != CMD_DES);
endproperty
a_cmd_cancel: assert property (p_cmd_cancel_recovery);

// 위반 케이스: ACT cancel 후 PRE 없이 MRR 발급
covergroup cmd_cancel_cg with function sample (
    ddr5_cmd_e canceled_cmd, ddr5_cmd_e next_cmd
);
    cp_cancel: coverpoint canceled_cmd {
        bins act = {CMD_ACT};
        bins wrp = {CMD_WRP};
        bins mrw = {CMD_MRW};
    }
    cp_next: coverpoint next_cmd {
        bins pre  = {CMD_PRE};       // recommended
        bins mrr  = {CMD_MRR};       // illegal after canceled ACT
        bins desn = {CMD_NOP, CMD_DES};
    }
    cx: cross cp_cancel, cp_next;
endgroup
```

### 10.4 §4.2 — Burst Type and Order (정밀 인용)

> §4.2 원문 인용:
> "Accesses within a given burst is currently **limited to only sequential, interleaved is not supported**. The ordering of accesses within a burst is determined by the burst length and the starting column address as shown in Table . The burst length is defined by bits OP[1:0] of Mode Register MR0. Burst length options include **BC8 OTF, BL16, BL32 (optional) and BL32 OTF**."

→ **DDR5는 sequential 만 지원**. DDR4의 interleaved option 폐기.

_왜 interleaved burst 를 폐기했는가_ — interleaved 순서는 옛 시절의 수요에서 나온 것인데 그 수요가 사라졌기 때문입니다. interleaved order 는 본래 시작 주소가 cache line 한가운데를 가리킬 때(misaligned), CPU 가 _가장 급한 word(critical word)_ 를 먼저 받고 나머지를 뒤섞인 순서로 채우도록 고안된 방식이었습니다. 그러나 현대 시스템에서는 cache line 이 항상 그 크기에 **정렬(aligned)** 되어 전송되고, DDR5 의 BL16 한 burst 가 정확히 64 B = 1 cache line 에 맞아떨어집니다 — 시작점이 늘 line 경계라 "한가운데부터 뒤섞어 시작" 할 이유가 없어진 것입니다. interleaved 를 빼면 controller·DRAM 양쪽의 burst 순서 디코딩 로직이 단순해지고 검증 표면도 줄어드므로, 수요가 사라진 기능을 정리해 sequential 하나로 통일한 것입니다.

### 10.5 Table 32 — Burst Order for READ (BL16, BC8)

> 출처: JESD79-5C.01 §4.2 Table 32

**BC8 SEQ**:

| Burst Length | C3 | C2 | C1 | C0 | Cycle 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9~16 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| BC8 | 0 | 0 | V | V | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | T (RTT_PARK) |
| BC8 | 0 | 1 | V | V | 4 | 5 | 6 | 7 | 0 | 1 | 2 | 3 | T |
| BC8 | 1 | 0 | V | V | 8 | 9 | A | B | C | D | E | F | T |
| BC8 | 1 | 1 | V | V | C | D | E | F | 8 | 9 | A | B | T |

**BL16 SEQ**:

| Burst Length | C3 | C2 | C1 | C0 | Cycle 1 | 2 | 3 | ... | 16 |
|---|---|---|---|---|---|---|---|---|---|
| BL16 | 0 | 0 | V | V | 0 | 1 | 2 | ... | F |
| BL16 | 0 | 1 | V | V | 4 | 5 | 6 | 7 | 0 1 2 3 C D E F 8 9 A B |
| BL16 | 1 | 0 | V | V | 8 | 9 | A | ... | 7 |
| BL16 | 1 | 1 | V | V | C | D | E | F | 8 9 A B 4 5 6 7 0 1 2 3 |

> NOTE 1: T = Output driver for data and strobes are in RTT_PARK.
> NOTE 2: V = A valid logic level (0 or 1), but respective buffer input ignores level on input pins.

핵심 통찰:
- **Starting column address (C3, C2)** 가 burst order의 *block ordering*을 결정
- C1, C0는 *Don't care* (V) — DDR5는 16-byte aligned burst만
- BL16의 모든 데이터를 4-block (0~3, 4~7, 8~B, C~F) 단위로 *rotation*

### 10.6 Table 36 — Precharge Encodings

> 출처: JESD79-5C.01 §4.3.1

| Function | Abbrev | CS_n | CA0 | CA1 | CA2 | CA3 | CA4 | CA5 | CA6 | CA7 | CA8 | CA9 | CA10 | CA11~13 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **Precharge All** | PREab | L | H | H | L | H | L | CID3 | V | V | V | V | L | CID0/1/2 |
| **Precharge Same Bank** | PREsb | L | H | H | L | H | L | CID3 | BA0 | BA1 | V | V | H | CID0/1/2 |
| **Precharge** (Per-Bank) | PREpb | L | H | H | L | H | H | CID3 | BA0 | BA1 | BG0 | BG1 | BG2 | CID0/1/2 |

DDR5의 **3가지 Precharge mode**:
1. **PREab (All)**: 모든 bank group의 모든 bank precharge
2. **PREsb (Same Bank)**: 모든 bank group에서 *같은 bank number* 만 precharge
3. **PREpb (Per-Bank)**: 정확히 하나의 bank 만 precharge

→ DV는 *3가지 PRE mode 모두* cover해야 함. PREsb는 DDR4에 없던 신기능 — 동기적 precharge 필요할 때.

_왜 DDR5 에서 PREsb(same-bank precharge)가 새로 필요해졌는가_ 는 DDR5 가 도입한 **same-bank 단위 동작들과 짝을 이루기** 때문입니다. DDR5 는 REFsb(same-bank refresh)처럼 "모든 bank group 에서 _같은 번호의 bank_ 만" 골라 동작시키는 메커니즘을 새로 들였습니다 — 한 bank 번호 집합만 묶어 refresh 하는 동안 나머지 bank 는 계속 쓰게 해 refresh stall 을 줄이려는 것입니다. 그런데 이런 same-bank 동작을 걸려면, 그 대상이 되는 same-bank 집합을 _한 명령으로 동시에_ precharge 해 일관된 출발 상태로 만들 수단이 필요합니다. bank 하나씩 PREpb 로 닫으면 타이밍이 어긋나 동기성이 깨지고, PREab 로 전부 닫으면 살려 두고 싶은 다른 bank 까지 닫혀 버립니다. PREsb 는 정확히 "여러 BG 에 걸친 같은 번호 bank 만 한꺼번에 precharge" 를 제공해, REFsb 같은 bank-그룹 단위 동작과 동기적으로 맞물리도록 한 신규 명령입니다.

### 10.7 §4.3 — Precharge Behavior (원문 인용)

> §4.3 원문 인용:
> "The PRECHARGE command is used to deactivate the open row in a particular bank or the open row in all banks. The bank(s) shall be available for a subsequent row activation a specified time (tRP) after the PRECHARGE command is issued."
>
> "If CA10 on the 2nd pulse of a Read or Write command is LOW, (shown as AP=L in the command truth table) then the **auto-precharge function is engaged**. This feature allows the precharge operation to be partially or completely hidden during burst read cycles (dependent upon CAS latency) thus improving system performance for random data access."
>
> "**The precharge to precharge delay is defined by tPPD** in the core timing tables. tPPD applies to any combination of precharge commands (PREab, PREsb, PREpb). tPPD also applies to any combination of precharge commands to a different die in a 3DS DDR5 SDRAM."

DV 적용:
```systemverilog
// tPPD — precharge to precharge minimum delay
property p_tppd;
    @(posedge clk)
    (cmd_decoded inside {CMD_PREab, CMD_PREsb, CMD_PREpb}) |->
        ##[`TPPD_NCK : $]
        first_match(cmd_decoded inside {CMD_PREab, CMD_PREsb, CMD_PREpb});
endproperty
a_tppd: assert property (p_tppd);
```

### 10.8 핵심 NOTE 인용 (Table 30 — 안전 관련)

- **NOTE 7**: "The Precharge command applies to a single bank as specified by bank address and bank group bits."
- **NOTE 9**: "The SRE command places the DRAM in self refresh state."
- **NOTE 10**: "The PDE command places the DRAM in power down state."
- **NOTE 11**: "Two cycle commands with no ODT control (ACT, MRW, WRP). **DRAM does not execute the command if it receives CS as LOW on 2nd cycle**." → 2-cycle cancel mechanism
- **NOTE 12**: "WR command with WR_Partial (WR_P) = Low indicates a partial write command. This is to help DRAM start an internal read for 'read modify write'."
- **NOTE 13**: "If CW=Low during the MRW command then DRAM should execute the command, Mode Register will be written. **If CW=HIGH then DRAM ignores the MRW command, and the Mode Register is not changed**." → RCD Control Word 분기
- **NOTE 26**: "Unlike DES, **NOP is considered a *valid command***, and timing from a preceding valid command must satisfy any associated command timings."

→ DV 시사점:
- **NOP ≠ DES**: NOP는 *valid 명령*으로 *timing 제약*에 포함됨. DES는 *non-command* (idle).
- **CW (Control Word)**: MRW의 마지막 cycle CA10에서 `CW=H` 면 DRAM은 명령 무시 (RCD만 처리).
- **WR_Partial = L**: read-modify-write 모드. internal read 발생.

## 11. 핵심 정리 (Key Takeaways)

- DRAM 명령은 본질적으로 7개 (ACT/RD/WR/PRE/REF/MRW/MRR) + 보조 (ZQ, NOP, DES, PDE/PDX).
- DDR5는 *2-cycle command* — CA[13:0]에 2 클럭에 걸쳐 인코딩. **CA1 비트가 1-cycle vs 2-cycle 식별자**. CS_n의 *2-cycle 윈도우*가 핵심.
- BL16이 default, BL32는 옵션 (sequential 대량 전송 시 유리). **DDR5는 sequential burst 만 지원** (interleaved 폐기).
- DDR5의 **3 PRE 모드**: PREab (All), PREsb (Same Bank), PREpb (Per-Bank). DDR4의 PREsb는 신규.
- **2-Cycle Command Cancel**: ACT/WRP/WRPA/MRW는 2nd cycle CS_n LOW면 cancel. **tCMD_cancel = 8 nCK** 이후에 다음 명령. 단, cancel 후 *legal sequence*는 host가 보장 (예: ACT cancel 후 PRE 없이 MRR 불가).
- **NOP vs DES**: NOP는 valid 명령 (timing 제약 적용), DES는 non-command.
- **CW (Control Word)**: MRW에서 CW=H면 DRAM 무시 — RCD만 처리.
- Command coverage는 *opcode + sequence + BL × cmd cross + cancel scenario* 의 다축.
- SVA로 *불법 명령 순서* + *2-cycle cancel timing* + *tPPD* + *Refresh Required 처리 (MR58 OP[0])* 모두 catch.

## 12. Further Reading

- 이전: [Ch04. Mode Register 깊이 분석](../04_mode_registers/)
- 다음: [Ch06. Timing·Preamble·Postamble](../06_timing_preamble/)
- 부록 C: [SVA / Coverage 예제 모음](../appendix_c_sva_coverage_examples/)
- 퀴즈: [Ch05 퀴즈](../quiz/ch05_quiz/)
- 추가: JESD79-5C.01 §4.1 Table 30 — 모든 명령 인코딩 (이 챕터는 *주요 명령 발췌*)

