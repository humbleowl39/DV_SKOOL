# 부록 C. SVA / Coverage 예제 모음

<div class="chapter-context" data-cat="memory">
  <a class="chapter-back" href="./"><span class="chapter-back-arrow">←</span><span class="chapter-back-icon">📚</span> DRAM JEDEC Deep-Dive</a>
  <span class="chapter-divider">›</span>
  <span class="chapter-marker chapter-quickref-marker">부록 C</span>
</div>

!!! warning "주의 — 이 예제들은 학습용 스켈레톤입니다"
    아래 코드는 *컴파일 보장이 아닌* 학습용 스켈레톤입니다. 실제 사용 시:
    - EDA tool 버전 확인 (특히 `first_match`, `intersect`, `throughout` 등의 동작)
    - DUT의 실제 신호 이름·폭에 맞게 수정
    - timing 파라미터를 speed bin에 따라 parameter화
    - reset 처리와 race condition을 신중히

---

## C.1 SVA — Timing Violations

### C.1.1 tRCD

```systemverilog
// 같은 bank에서 ACT → RD/WR 사이 최소 tRCD nCK
// 출처: JESD79-5C.01 §3.1 + speed bin
property p_trcd;
    @(posedge clk) disable iff (!reset_n)
    (cmd_decoded == CMD_ACT) |->
        ##[TRCD_NCK : $]
        first_match(cmd_decoded inside {CMD_RD, CMD_WR, CMD_RDA, CMD_WRA}
                    && (bg == $past(bg)) && (ba == $past(ba)));
endproperty
a_trcd: assert property (p_trcd)
    else `uvm_error("SVA_TIMING", "tRCD violation: RD/WR too soon after ACT")
```

### C.1.2 tRP

```systemverilog
property p_trp;
    @(posedge clk) disable iff (!reset_n)
    (cmd_decoded == CMD_PRE) |->
        ##[TRP_NCK : $]
        first_match(cmd_decoded == CMD_ACT
                    && (bg == $past(bg)) && (ba == $past(ba)));
endproperty
a_trp: assert property (p_trp)
    else `uvm_error("SVA_TIMING", "tRP violation")
```

### C.1.3 tRAS — minimum row active time

```systemverilog
// ACT 후 같은 bank의 PRE 까지 최소 tRAS
property p_tras;
    @(posedge clk) disable iff (!reset_n)
    (cmd_decoded == CMD_ACT) ##[TRAS_NCK : $] (cmd_decoded == CMD_PRE) |->
        (bg == $past(bg)) && (ba == $past(ba));
    // 보다 엄밀한 형태는 bank state FSM과 연계 필요
endproperty
```

### C.1.4 tFAW — sliding window 4 ACT

```systemverilog
// 한 rank에 대해 tFAW 윈도우 내 ACT가 4를 넘으면 안 됨
int act_window_cnt;
time act_timestamps[$];

always @(posedge clk) begin
    if (cmd_decoded == CMD_ACT) begin
        // 윈도우 밖 timestamp 제거
        while (act_timestamps.size() > 0 &&
               ($time - act_timestamps[0]) > TFAW_PS)
            act_timestamps.delete(0);

        act_timestamps.push_back($time);

        if (act_timestamps.size() > 4)
            `uvm_error("SVA_TIMING",
                $sformatf("tFAW violation: %0d ACTs in %0d ps window",
                          act_timestamps.size(), TFAW_PS))
    end
end
```

### C.1.5 tCCD_L (same BG) / tCCD_S (different BG)

```systemverilog
// 같은 BG의 CAS→CAS 최소 tCCD_L
property p_tccd_l_same_bg;
    @(posedge clk) disable iff (!reset_n)
    (cmd_decoded inside {CMD_RD, CMD_WR}) ##0 1 |->
        ##[TCCD_L_NCK : $]
        first_match(cmd_decoded inside {CMD_RD, CMD_WR}
                    && bg == $past(bg))
        or  ##0 (cmd_decoded inside {CMD_RD, CMD_WR}
                 && bg != $past(bg));
    // (논리: 같은 BG이면 tCCD_L 이상, 다른 BG이면 무제한)
endproperty
```

### C.1.6 tREFI — refresh deferred 한계

```systemverilog
// 9 deferred REF 초과 시 위반
int deferred_ref_count;
time last_ref_time;

always @(posedge clk) begin
    time elapsed_tref = $time - last_ref_time;

    if (cmd_decoded == CMD_REF) begin
        deferred_ref_count = (deferred_ref_count + 1) - 1;
            // 한 번 발급 → -1 (defer 감소). 동시에 *expected* 도 진행 가정.
        last_ref_time = $time;
    end

    // 만약 expected가 *9 tREFI 이상 *지났는데* 발급 안 되면 violation
    if (elapsed_tref > 9 * TREFI_PS)
        `uvm_error("SVA_TIMING",
            "Refresh deferred more than 9 tREFI without REF")
end
```

---

## C.2 SVA — Command Order

### C.2.1 PRE 없이 ACT→ACT (same bank) 금지

```systemverilog
// 추적용 bank state (간소화)
bit  bank_active [256];        // bank 인덱스 = rank*32 + bg*4 + ba
function int bank_idx(int rank, int bg, int ba);
    return rank*32 + bg*4 + ba;
endfunction

always @(posedge clk) begin
    if (cmd_decoded == CMD_ACT) begin
        int idx = bank_idx(rank_decoded, bg_decoded, ba_decoded);
        if (bank_active[idx])
            `uvm_error("SVA_ORDER",
                $sformatf("ACT to already-active bank (rank=%0d bg=%0d ba=%0d)",
                          rank_decoded, bg_decoded, ba_decoded))
        bank_active[idx] = 1'b1;
    end
    else if (cmd_decoded == CMD_PRE) begin
        int idx = bank_idx(rank_decoded, bg_decoded, ba_decoded);
        bank_active[idx] = 1'b0;
    end
    else if (cmd_decoded == CMD_RDA || cmd_decoded == CMD_WRA) begin
        // Auto-precharge → 일정 cycle 후 자동 PRE
        // (실제로는 tRTP/tWR 이후의 future timestamp에 schedule)
    end
end
```

### C.2.2 RD→WR transition (tRTW)

```systemverilog
property p_rd_to_wr_trtw;
    @(posedge clk) disable iff (!reset_n)
    (cmd_decoded == CMD_RD) |->
        ##[TRTW_NCK : $] (cmd_decoded == CMD_WR);
endproperty
```

### C.2.3 WR→RD transition (tWTR_S, tWTR_L)

```systemverilog
// 다른 BG로 가면 tWTR_S, 같은 BG면 tWTR_L
property p_wr_to_rd;
    @(posedge clk) disable iff (!reset_n)
    (cmd_decoded == CMD_WR) |->
        ##[TWTR_S_NCK : $] (cmd_decoded == CMD_RD && bg != $past(bg))
        or
        ##[TWTR_L_NCK : $] (cmd_decoded == CMD_RD && bg == $past(bg));
endproperty
```

### C.2.4 CKE 가 LOW 일 때 MRW 금지

```systemverilog
property p_no_mrw_when_cke_low;
    @(posedge clk) (cmd_decoded == CMD_MRW) |-> (cke == 1'b1);
endproperty
a_no_mrw_cke_low: assert property (p_no_mrw_when_cke_low)
    else `uvm_error("SVA_ORDER", "MRW issued while CKE LOW")
```

### C.2.5 Init only MR 변경은 runtime에 금지

```systemverilog
// MR3 (DQS Training), MR13 (CS Geardown) 등은 init/SR 시점에만
property p_init_only_mr_runtime;
    @(posedge clk) disable iff (!reset_n)
    (cmd_decoded == CMD_MRW && mr_num inside {3, 13}) |->
        (current_state inside {STATE_INIT, STATE_SELF_REFRESH});
endproperty
```

---

## C.3 SVA — Training Protocol

### C.3.1 CBT entry 후 일반 traffic 금지

```systemverilog
// CBT entry MR write 발급 → CBT exit MR write 까지의 사이에는
// 일반 RD/WR/REF 등이 발급되어서는 안 됨
bit in_cbt_mode;

always @(posedge clk) begin
    if (cmd_decoded == CMD_MRW && mr_num == CBT_ENTRY_MR && mr_data == CBT_ENTRY_VAL)
        in_cbt_mode = 1'b1;
    if (cmd_decoded == CMD_MRW && mr_num == CBT_EXIT_MR && mr_data == CBT_EXIT_VAL)
        in_cbt_mode = 1'b0;

    if (in_cbt_mode &&
        cmd_decoded inside {CMD_RD, CMD_WR, CMD_REF, CMD_RFM})
        `uvm_error("SVA_TRAINING",
            $sformatf("Normal traffic (%s) issued in CBT mode", cmd_decoded.name()))
end
```

### C.3.2 WCK2CK Leveling 동안 RD/WR 금지

```systemverilog
property p_no_traffic_during_wck2ck;
    @(posedge clk) disable iff (!reset_n)
    (training_state == TR_WCK2CK_LVL) |->
        (cmd_decoded inside {CMD_NOP, CMD_DES} or cmd_decoded == CMD_MRW);
endproperty
```

### C.3.3 ZQCL 후 tZQinit 동안 명령 발급 금지

```systemverilog
time zqcl_time;
always @(posedge clk) begin
    if (cmd_decoded == CMD_ZQCL)
        zqcl_time = $time;
    if ((zqcl_time != 0) && ($time - zqcl_time < TZQINIT_PS) &&
        !(cmd_decoded inside {CMD_NOP, CMD_DES}))
        `uvm_error("SVA_TRAINING", "Command issued before tZQinit expired")
end
```

---

## C.4 Coverage — Command / Burst / BG

### C.4.1 Command opcode + BL + AP cross

```systemverilog
covergroup cmd_full_cg with function sample (
    ddr5_cmd_e cmd, int bl, bit ap
);
    cp_cmd: coverpoint cmd {
        bins basic[]    = {CMD_ACT, CMD_PRE, CMD_RD, CMD_WR, CMD_REF};
        bins auto_pre[] = {CMD_RDA, CMD_WRA};
        bins mr[]       = {CMD_MRW, CMD_MRR};
        bins refresh    = {CMD_RFM};
        ignore_bins idle = {CMD_DES, CMD_NOP};
    }
    cp_bl: coverpoint bl {
        bins bl16 = {16};
        bins bl32 = {32};
    }
    cp_ap: coverpoint ap;
    cx: cross cp_cmd, cp_bl, cp_ap;
endgroup
```

### C.4.2 BG / Bank / Row range / Col range

```systemverilog
covergroup addr_cg with function sample (
    bit [2:0] bg, bit [1:0] ba, bit [16:0] row, bit [9:0] col
);
    cp_bg: coverpoint bg { bins each[] = {[0:7]}; }
    cp_ba: coverpoint ba { bins each[] = {[0:3]}; }
    cp_row: coverpoint row {
        bins low  = {[0 : 17'h0_0FFF]};
        bins mid  = {[17'h0_1000 : 17'h0_EFFF]};
        bins high = {[17'h0_F000 : 17'h1_FFFF]};
    }
    cp_col: coverpoint col {
        bins low  = {[0 : 10'h0FF]};
        bins mid  = {[10'h100 : 10'h2FF]};
        bins high = {[10'h300 : 10'h3FF]};
    }
    cx_bg_ba: cross cp_bg, cp_ba;
endgroup
```

---

## C.5 Coverage — Timing Corners

```systemverilog
covergroup timing_corner_cg with function sample (
    int gap_cycles, string param
);
    cp_param: coverpoint param {
        bins trcd   = {"tRCD"};
        bins trp    = {"tRP"};
        bins tras   = {"tRAS"};
        bins trrd_l = {"tRRD_L"};
        bins trrd_s = {"tRRD_S"};
        bins tccd_l = {"tCCD_L"};
        bins tccd_s = {"tCCD_S"};
        bins twtr_l = {"tWTR_L"};
        bins twtr_s = {"tWTR_S"};
    }
    cp_gap: coverpoint gap_cycles {
        bins min_spec  = {[1:5]};
        bins normal    = {[6:30]};
        bins long_idle = {[31:1000]};
    }
    cx: cross cp_param, cp_gap;
endgroup
```

---

## C.6 Coverage — Mode Register Walk

```systemverilog
covergroup mr_walk_cg with function sample (bit [7:0] mr_num, bit is_write);
    cp_mr: coverpoint mr_num {
        bins basic[]    = {0, 1, 2, 3, 4, 5, 6, 7, 8};
        bins ecc[]      = {14, 15, 16, 17, 18, 19, 20};
        bins ppr[]      = {23, 24, 54, 55, 56, 57};
        bins odt[]      = {32, 33, 34, 35, 36, 37, 38, 39, 40};
        bins dca[]      = {42, 43, 44, 45, 46, 47, 48};
        bins refresh[]  = {4, 58, 59, 60};
        bins crc[]      = {50, 51, 52};
        bins training[] = {3, 11, 12, 25, 26, 27, 28, 29, 30, 31};
        bins dfe[]      = {21, 22, 70, 71, 72, 73, 74, 75,
                           111, 112, 113, 114, 115, 116};
        bins others     = default;
    }
    cp_rw: coverpoint is_write;
    cx: cross cp_mr, cp_rw;
endgroup
```

---

## C.7 Coverage — Refresh & RFM

```systemverilog
covergroup refresh_cg with function sample (
    int raa, bit rfm_issued, bit ext_temp, int deferred_ref
);
    cp_raa: coverpoint raa {
        bins below_half     = {[0 : 399]};
        bins approaching    = {[400 : 599]};
        bins near_threshold = {[600 : 799]};
        bins at_threshold   = {800};
        bins overflow_zone  = {[801 : $]};
    }
    cp_rfm: coverpoint rfm_issued;
    cp_temp: coverpoint ext_temp {
        bins normal_temp   = {0};
        bins extended_temp = {1};
    }
    cp_deferred: coverpoint deferred_ref {
        bins zero      = {0};
        bins one_to_4  = {[1:4]};
        bins five_to_8 = {[5:8]};
    }
    cx_raa_rfm: cross cp_raa, cp_rfm {
        ignore_bins illegal = binsof(cp_raa.overflow_zone) &&
                              binsof(cp_rfm) intersect {0};
    }
    cx_temp_def: cross cp_temp, cp_deferred;
endgroup
```

---

## C.8 Coverage — Training Steps + Fail Injection

```systemverilog
covergroup training_step_cg with function sample (
    lpddr5_training_state_e state, bit fail_injected, bit recovered
);
    cp_state: coverpoint state {
        bins zq            = {TR_ZQ_CAL};
        bins cbt_mode1     = {TR_CBT_MODE1};
        bins cbt_mode2     = {TR_CBT_MODE2};
        bins ca_vref       = {TR_CA_VREF};
        bins dq_vref       = {TR_DQ_VREF};
        bins wck2ck_lvl    = {TR_WCK2CK_LVL};
        bins dca           = {TR_DCA};
        bins read_training = {TR_READ_TRAINING};
        bins normal        = {TR_NORMAL};
        bins fail          = {TR_TRAINING_FAIL};
    }
    cp_fail_inj: coverpoint fail_injected;
    cp_recovery: coverpoint recovered;
    cx_fail: cross cp_state, cp_fail_inj, cp_recovery {
        ignore_bins not_meaningful = !binsof(cp_fail_inj) intersect {1};
    }
endgroup
```

---

## C.9 Coverage — ECC / CRC

```systemverilog
typedef enum {
    ECC_NO_ERROR,
    ECC_SINGLE_BIT_CORRECTED,
    ECC_DOUBLE_BIT_DETECTED,
    ECC_UNREPORTED_CORRUPTION,    // illegal (bug)
    CRC_ERROR,
    CRC_AUTO_DISABLE_THRESHOLD
} error_type_e;

covergroup ecc_cg with function sample (error_type_e err_type);
    cp: coverpoint err_type {
        bins no_error    = {ECC_NO_ERROR};
        bins single_corr = {ECC_SINGLE_BIT_CORRECTED};
        bins double_det  = {ECC_DOUBLE_BIT_DETECTED};
        bins crc_err     = {CRC_ERROR};
        bins crc_disable = {CRC_AUTO_DISABLE_THRESHOLD};
        ignore_bins illegal = {ECC_UNREPORTED_CORRUPTION};
    }
endgroup
```

---

## C.10 Coverage — PPR (DDR5/LPDDR5)

```systemverilog
typedef enum {
    PPR_HPPR_WRA,
    PPR_HPPR_WR,
    PPR_SPPR
} ppr_type_e;

covergroup ppr_cg with function sample (
    ppr_type_e ptype, bit guard_correct, bit ppr_pass
);
    cp_type: coverpoint ptype;
    cp_key: coverpoint guard_correct;
    cp_pass: coverpoint ppr_pass;

    cx_full: cross cp_type, cp_key, cp_pass {
        // Guard key 잘못된 채 PPR이 성공 = bug
        ignore_bins illegal_bypass = binsof(cp_key) intersect {0} &&
                                     binsof(cp_pass) intersect {1};
    }
endgroup
```

---

## C.11 LPDDR5 — WCK / DVFS / Link ECC 추가 coverage

```systemverilog
// WCK ratio
covergroup wck_ratio_cg with function sample (int ratio, bit aligned);
    cp_ratio: coverpoint ratio {
        bins ratio_2x = {2};
        bins ratio_4x = {4};
    }
    cp_align: coverpoint aligned;
    cx: cross cp_ratio, cp_align;
endgroup

// DVFS FSP transition
covergroup lpddr5_dvfs_cg with function sample (
    int from_fsp, int to_fsp, bit success, int transition_time_us
);
    cp_trans: coverpoint {from_fsp, to_fsp} {
        bins fsp0_to_1 = {{0, 1}};
        bins fsp1_to_0 = {{1, 0}};
        bins fsp0_to_2 = {{0, 2}};   // LPDDR5X
        bins fsp2_to_0 = {{2, 0}};
    }
    cp_success: coverpoint success;
    cp_time: coverpoint transition_time_us {
        bins fast    = {[0 : 10]};
        bins normal  = {[11 : 100]};
        bins slow    = {[101 : $]};
    }
    cx: cross cp_trans, cp_success, cp_time;
endgroup

// Link ECC scenario
covergroup link_ecc_cg with function sample (
    int bits_flipped, bit reported, bit corrected
);
    cp_bits: coverpoint bits_flipped {
        bins zero        = {0};
        bins single      = {1};
        bins double      = {2};
        bins three_plus  = {[3:$]};
    }
    cp_reported: coverpoint reported;
    cp_corrected: coverpoint corrected;
    cx: cross cp_bits, cp_reported, cp_corrected {
        // 0 flip 인데 reported = bug
        ignore_bins illegal_report = binsof(cp_bits.zero) && binsof(cp_reported) intersect {1};
        // 2-bit flip 인데 corrected = false report (실제 SECDED는 정정 못 함)
        ignore_bins illegal_correct = binsof(cp_bits.double) && binsof(cp_corrected) intersect {1};
    }
endgroup
```

---

## C.12 SVA `bind` 패턴 — 통합 예제

```systemverilog
// 파일: ddr5_protocol_check.sv
module ddr5_protocol_check #(
    parameter TRCD_NCK    = 28,
    parameter TRP_NCK     = 28,
    parameter TRAS_NCK    = 56,
    parameter TRRD_L_NCK  = 8,
    parameter TRRD_S_NCK  = 4,
    parameter TFAW_PS     = 13000,   // 13 ns in ps
    parameter TCCD_L_NCK  = 8,
    parameter TCCD_S_NCK  = 4,
    parameter TWTR_L_NCK  = 12,
    parameter TWTR_S_NCK  = 4,
    parameter TRTW_NCK    = 4,
    parameter TZQINIT_PS  = 512000,  // 1024 nCK × 0.5 ns
    parameter TREFI_PS    = 7800000  // 7.8 us
)(
    input bit clk,
    input bit reset_n,
    input bit cs_n,
    input bit cke,
    input ddr5_cmd_e cmd_decoded,
    input bit [2:0] bg_decoded,
    input bit [1:0] ba_decoded,
    input bit [2:0] rank_decoded,
    input bit [16:0] row_decoded,
    input bit [7:0] mr_num
);
    // C.1 Timing
    `include "sva_timing_checks.svh"
    // C.2 Command order
    `include "sva_command_order.svh"
    // C.3 Training protocol
    `include "sva_training_protocol.svh"
endmodule

// 바인딩 (DUT 외부)
bind ddr5_top ddr5_protocol_check #(
    .TRCD_NCK(28), .TRP_NCK(28), .TRAS_NCK(56),
    .TRRD_L_NCK(8), .TRRD_S_NCK(4),
    .TFAW_PS(13000),
    .TCCD_L_NCK(8), .TCCD_S_NCK(4),
    .TWTR_L_NCK(12), .TWTR_S_NCK(4),
    .TRTW_NCK(4)
) u_proto_check (
    .clk(clk),
    .reset_n(reset_n),
    .cs_n(ca_bus.cs_n),
    .cke(ca_bus.cke),
    .cmd_decoded(internal_cmd_decoded),
    .bg_decoded(internal_bg),
    .ba_decoded(internal_ba),
    .rank_decoded(internal_rank),
    .row_decoded(internal_row),
    .mr_num(internal_mr_num)
);
```

---

## C.13 Coverage 통합 — Test에서 sample 호출

```systemverilog
// 모든 covergroup을 ddr5_coverage component 안에 모으고, monitor의
// analysis_port에서 받은 transaction으로 sample 호출.

class ddr5_coverage extends uvm_subscriber #(ddr5_transaction);
    `uvm_component_utils(ddr5_coverage)

    cmd_full_cg     cmd_cg;
    addr_cg         addr_cg_inst;
    timing_corner_cg tim_cg;
    mr_walk_cg      mr_cg;
    refresh_cg      ref_cg;
    training_step_cg train_cg;
    ecc_cg          ecc_cg_inst;
    ppr_cg          ppr_cg_inst;
    // LPDDR5 추가
    wck_ratio_cg    wck_cg;
    lpddr5_dvfs_cg  dvfs_cg;
    link_ecc_cg     linkecc_cg;

    function new(string name, uvm_component parent);
        super.new(name, parent);
        cmd_cg = new();
        addr_cg_inst = new();
        tim_cg = new();
        mr_cg = new();
        ref_cg = new();
        train_cg = new();
        ecc_cg_inst = new();
        ppr_cg_inst = new();
        // ... LPDDR5 ...
    endfunction

    virtual function void write(ddr5_transaction t);
        cmd_cg.sample(t.cmd, t.bl, t.ap);
        addr_cg_inst.sample(t.bg, t.ba, t.row, t.col);

        if (t.cmd inside {CMD_MRW, CMD_MRR})
            mr_cg.sample(t.mr_num, t.cmd == CMD_MRW);

        // timing은 별도 timing-aware monitor에서 호출
        // refresh / training / ecc도 각 시나리오에서 호출
    endfunction

    virtual function void report_phase(uvm_phase phase);
        `uvm_info("COVERAGE",
            $sformatf("cmd_cg=%0.1f%%", cmd_cg.get_inst_coverage()),
            UVM_MEDIUM)
    endfunction
endclass
```

---

<div class="chapter-nav">
  <a class="nav-prev" href="appendix_b_glossary_ko/">
    <div class="nav-label">← 이전</div>
    <div class="nav-title">부록 B. 용어집 (KO)</div>
  </a>
  <a class="nav-next" href="quiz/">
    <div class="nav-label">다음 →</div>
    <div class="nav-title">퀴즈 인덱스</div>
  </a>
</div>
