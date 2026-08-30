---
title: "부록 C — RTL 설계 패턴"
description: 12개 장의 규격 제약을 합성 가능한 SystemVerilog 구조로 옮긴 참조 패턴 모음
---

:::caution[사용 범위]
본 부록의 코드는 **규격 제약을 어떤 구조로 옮기는가**를 보이기 위한 **참조 패턴**입니다. 특정 제품의 구현이 아니며, 벤더 데이터시트 값과 시스템 요구를 반영해야 실제 설계가 됩니다.

이 코드는 **설계(RTL)** 이므로 검증용 UVM 매크로 대신 SVA와 `$error`를 씁니다. 검증 측 구현은 [`hbm_dv`](../../hbm_dv/)를 참고하세요.

수치는 [부록 A](../appendix_a_quick_reference/)의 요약을 따르며, 근거는 각 패턴에 절 번호로 표시했습니다.
:::

:::note[인용 고지]
코드 주석의 절 번호는 **JESD270-4 (2025-04, WIP draft)** 를 가리킵니다. 규격 조문을 **요약·재구성**해 설계 의도를 밝힌 것이며 원문 복제가 아닙니다. 정밀 값과 인코딩은 **JEDEC 원문 우선**입니다.
:::

---

## 1. 구성 파라미터 패키지

모든 패턴이 공유하는 토대입니다. **런타임 값과 컴파일 상수를 구분**하는 것이 핵심입니다.

```systemverilog
package hbm4_cfg_pkg;

  // ---- 구조 상수 (§1–3) ----------------------------------------------------
  localparam int NUM_CH        = 32;   // 채널 (완전 독립, 비동기 가능)
  localparam int NUM_PC        = 2;    // 채널당 pseudo-channel
  localparam int DQ_PER_CH     = 64;
  localparam int DQ_PER_PC     = 32;
  localparam int BL            = 8;    // 중단·절단 없음 (§6.3.3)
  localparam int PREFETCH_BITS = 256;  // PC당

  // ---- 주소 폭 (§3.2, Table 4) --------------------------------------------
  localparam int RA_W  = 14;   // RA[13:12] = 11 무효
  localparam int CA_W  = 5;    // BL8의 8 UI를 구분하지 않음 (Note 2)
  localparam int BA_W  = 4;
  localparam int SID_W = 2;    // 구성별 0/1/2 비트 사용

  // ---- 구성 의존 (부팅 시 DEVICE_ID로 확정) --------------------------------
  // 컴파일 상수로 박으면 이식성을 잃는다 (§13.5.11)
  typedef struct packed {
    logic [1:0]  sid_used;     // 0 / 1 / 2 비트
    logic [6:0]  num_banks;    // 16 / 32 / 48 / 64
    logic [3:0]  density_code; // DEVICE_ID [43:40]
    logic [15:0] raa_imt;      // RAAIMT
    logic [15:0] raa_mmt;      // RAAMMT
    logic [15:0] raa_dec;      // RAADEC
    logic        arfm_sup;     // ARFM 지원
    logic        rxoffc_sup;   // Rx offset calibration 지원
  } dev_cfg_t;

  // ---- 타이밍 (반 사이클 정수 단위) ---------------------------------------
  // HBM4 라운딩은 0.5 nCK 해상도를 가지므로 정수 반사이클로 다룬다 (§6.3.2.4)
  localparam int TW = 12;      // 타이밍 카운터 폭

  typedef struct packed {
    logic [TW-1:0] t_ras_half;   // tRAS  (min)
    logic [TW-1:0] t_ras_max;    // tRAS  (max) = 9 × tREFI  (§10)
    logic [TW-1:0] t_rtp_half;
    logic [TW-1:0] t_wr_half;
    logic [TW-1:0] t_rp_half;
    logic [TW-1:0] t_rrdl, t_rrds;
    logic [TW-1:0] t_ccdl, t_ccds, t_ccdr;   // tCCDR: READ 전용·SID 의존
    logic [TW-1:0] t_wtrl, t_wtrs;
    logic [TW-1:0] rl, wl, pl;               // MR2 / MR1
  } timing_cfg_t;

endpackage
```

**두 가지 판단이 들어 있습니다.**

- **`dev_cfg_t`는 런타임 구조체**입니다. 밀도·RAA 문턱값·기능 지원 여부는 `DEVICE_ID`에서 읽어야 하므로 파라미터로 고정할 수 없습니다 → [11장](../11_training_ieee1500/)
- **타이밍은 반 사이클 정수**입니다. 0.5를 실수로 다루면 합성되지 않습니다 → [06장](../06_row_commands/)

## 2. HBM4 라운딩

```systemverilog
// nXX = 0.5 × RU(2 × tXX / tCK)   대상: tRAS, tRTP, tWR, tRP  (§6.3.2.4)
// 반환 단위는 "반 사이클"이다.
function automatic int hbm4_round_half(input int t_ps, input int tck_ps);
  return (2*t_ps + tck_ps - 1) / tck_ps;      // RU(2·t/tCK)
endfunction

// tRP 예외: 결과 슬롯이 하강 에지(홀수 반사이클)이면 상승 에지로 올린다.
// precharge를 어느 에지에 발행했는지에 따라 최종 위치가 달라진다.
function automatic int rp_slot_half(input int issue_half, input int n_rp_half);
  int s = issue_half + n_rp_half;
  return (s[0] == 1'b1) ? s + 1 : s;          // 홀수(하강) → +0.5 nCK
endfunction
```

:::tip[전통 공식과의 차이]
전통 공식 `RU(t/tCK)`는 항상 상승 에지로 올림하므로 **같거나 더 보수적**입니다. 규격 위반은 아니지만 **성능을 버립니다.** 반대로 새 공식을 쓰면서 `tRP` 예외를 빠뜨리면 **하강 에지에 ACTIVATE를 발행하는 위반**이 됩니다.
:::

## 3. 반주기 커맨드 디코더

`ACT`가 3개의 반주기에 걸치므로 **양쪽 에지에서 캡처하는 구조**가 필요합니다.

```systemverilog
module hbm4_row_decoder
  import hbm4_cfg_pkg::*;
(
  input  logic            ck,
  input  logic            rst_n,
  input  logic [9:0]      r_rise,      // CK 상승 에지 캡처
  input  logic [9:0]      r_fall,      // CK 하강 에지 캡처
  output logic            act_valid,
  output logic            act_pc,
  output logic [SID_W-1:0] act_sid,
  output logic [BA_W-1:0]  act_ba,
  output logic [RA_W-1:0]  act_ra,
  output logic            act_drfm     // ACT의 DRFM 비트 (§6.3.2.5.5)
);

  typedef enum logic [1:0] { S_IDLE, S_ACT_FALL, S_ACT_RISE2 } dec_e;
  dec_e state_q;

  logic [RA_W-1:0] ra_q;
  logic            drfm_q;

  // ---- 상승 에지 슬롯 ------------------------------------------------------
  always_ff @(posedge ck or negedge rst_n) begin
    if (!rst_n) begin
      state_q   <= S_IDLE;
      act_valid <= 1'b0;
    end else begin
      act_valid <= 1'b0;
      unique case (state_q)
        S_IDLE:
          if (r_rise[3:0] == 4'b0110) begin        // ACT opcode (예시 인코딩)
            act_pc  <= r_rise[3];
            act_sid <= r_rise[5:4];
            act_ba  <= r_rise[9:6];
            state_q <= S_ACT_FALL;
          end
        S_ACT_RISE2: begin
          ra_q[7:0] <= r_rise[9:2];                // 세 번째 반주기
          act_ra    <= {ra_q[RA_W-1:8], r_rise[9:2]};
          act_drfm  <= drfm_q;
          act_valid <= 1'b1;
          state_q   <= S_IDLE;
        end
        default: ;
      endcase
    end
  end

  // ---- 하강 에지 슬롯 ------------------------------------------------------
  always_ff @(negedge ck or negedge rst_n) begin
    if (!rst_n)
      state_q <= S_IDLE;
    else if (state_q == S_ACT_FALL) begin
      ra_q[RA_W-1:8] <= r_fall[8:2];               // RA[13:8]
      drfm_q         <= r_fall[9];                 // DRFM 비트
      state_q        <= S_ACT_RISE2;
    end
  end

  // ---- 무효 주소 조합 검사 (Table 4 Note 5·6·8) ----------------------------
`ifndef SYNTHESIS
  a_ra_valid: assert property (@(posedge ck) disable iff (!rst_n)
    act_valid |-> (act_ra[13:12] != 2'b11))
    else $error("RA[13:12]=11 is invalid");

  a_sid_valid: assert property (@(posedge ck) disable iff (!rst_n)
    act_valid |-> (act_sid != 2'b11))
    else $error("SID[1:0]=11 is invalid");
`endif

endmodule
```

**주의**: opcode 인코딩은 예시입니다. 실제 값은 규격 Table 33을 따라야 합니다.

## 4. ACT 후속 슬롯 제약

```systemverilog
// ACT 두 번째 사이클 하강 슬롯에는 세 가지만 허용된다 (Table 33 Note 9)
//   RNOP / 다른 뱅크 PREpb / 다른 PC PREab
module hbm4_act_slot_check
  import hbm4_cfg_pkg::*;
(
  input logic             ck, rst_n,
  input logic             in_act_second_fall,
  input logic [2:0]       fall_cmd,       // CMD_RNOP / CMD_PREPB / CMD_PREAB / ...
  input logic             fall_pc,
  input logic [SID_W-1:0] fall_sid,
  input logic [BA_W-1:0]  fall_ba,
  input logic             act_pc,
  input logic [SID_W-1:0] act_sid,
  input logic [BA_W-1:0]  act_ba,
  output logic            slot_violation
);

  localparam logic [2:0] CMD_RNOP = 3'd0, CMD_PREPB = 3'd1, CMD_PREAB = 3'd2;

  wire ok_rnop  = (fall_cmd == CMD_RNOP);
  wire ok_prepb = (fall_cmd == CMD_PREPB)
                && ({fall_sid, fall_ba} != {act_sid, act_ba});   // 다른 뱅크
  wire ok_preab = (fall_cmd == CMD_PREAB) && (fall_pc != act_pc); // 다른 PC

  assign slot_violation = in_act_second_fall & ~(ok_rnop | ok_prepb | ok_preab);

`ifndef SYNTHESIS
  a_act_slot: assert property (@(negedge ck) disable iff (!rst_n)
    !slot_violation)
    else $error("Illegal command in ACT second-cycle falling slot");
`endif

endmodule
```

## 5. 뱅크 그룹 · SID 의존 타이밍 선택

```systemverilog
// 뱅크 인덱스 = {SID, BA}, 그룹 = 상위 비트 (연속 8뱅크 = 1그룹, §3.2.1)
// READ→READ만 3택이다 — tCCDR은 SID가 다를 때 (§10 Note 17)
module hbm4_timing_select
  import hbm4_cfg_pkg::*;
(
  input  timing_cfg_t     tcfg,
  input  logic [SID_W-1:0] cur_sid,  last_sid,
  input  logic [BA_W-1:0]  cur_ba,   last_ba,
  output logic [TW-1:0]    t_rrd, t_ccd_rd, t_ccd_wr, t_wtr
);

  wire [SID_W+BA_W-1:0] cur_idx  = {cur_sid,  cur_ba};
  wire [SID_W+BA_W-1:0] last_idx = {last_sid, last_ba};

  // 그룹은 인덱스의 상위 비트 (하위 3비트가 그룹 내 위치)
  wire same_group = (cur_idx[SID_W+BA_W-1:3] == last_idx[SID_W+BA_W-1:3]);
  wire same_sid   = (cur_sid == last_sid);

  assign t_rrd    = same_group ? tcfg.t_rrdl : tcfg.t_rrds;
  assign t_wtr    = same_group ? tcfg.t_wtrl : tcfg.t_wtrs;
  assign t_ccd_wr = same_group ? tcfg.t_ccdl : tcfg.t_ccds;   // WRITE: 2택

  // READ: 3택 — 그룹만 보면 tCCDR을 놓친다
  assign t_ccd_rd = same_group ? tcfg.t_ccdl
                  : same_sid   ? tcfg.t_ccds
                               : tcfg.t_ccdr;
endmodule
```

## 6. 뱅크 상태 머신과 `tRAS` 최대

**상태 머신은 뱅크마다 한 벌**입니다([02장](../02_addressing_bank_groups/)). 그리고 `tRAS`에는 **최대 제약**이 있습니다([12장](../12_electrical_timing_package/)).

```systemverilog
module hbm4_bank_fsm
  import hbm4_cfg_pkg::*;
#(parameter int BANK_ID = 0)
(
  input  logic        ck, rst_n,
  input  timing_cfg_t tcfg,
  input  logic        act_i, rd_i, wr_i, pre_i,
  output logic        bank_active,
  output logic        force_precharge   // tRAS 최대 만료 임박
);

  typedef enum logic [2:0] {
    B_IDLE, B_ACTIVATING, B_ACTIVE, B_READING, B_WRITING, B_PRECHARGING
  } bank_e;

  bank_e                bank_q;
  logic [TW-1:0]        open_cnt_q;      // 행이 열린 뒤 경과 (반 사이클)

  always_ff @(posedge ck or negedge rst_n) begin
    if (!rst_n) begin
      bank_q     <= B_IDLE;
      open_cnt_q <= '0;
    end else begin
      unique case (bank_q)
        B_IDLE:        if (act_i) begin bank_q <= B_ACTIVATING; open_cnt_q <= '0; end
        B_ACTIVATING:  bank_q <= B_ACTIVE;
        B_ACTIVE: begin
          if      (rd_i)  bank_q <= B_READING;
          else if (wr_i)  bank_q <= B_WRITING;
          else if (pre_i) bank_q <= B_PRECHARGING;
        end
        B_READING, B_WRITING: if (pre_i) bank_q <= B_PRECHARGING;
        B_PRECHARGING: bank_q <= B_IDLE;
        default: bank_q <= B_IDLE;
      endcase

      // 열려 있는 동안 계수 — tRAS 최대(9 × tREFI) 감시용 (§10)
      if (bank_q inside {B_ACTIVATING, B_ACTIVE, B_READING, B_WRITING})
        open_cnt_q <= open_cnt_q + 1'b1;
      else
        open_cnt_q <= '0;
    end
  end

  assign bank_active     = (bank_q != B_IDLE) && (bank_q != B_PRECHARGING);
  // 만료 전에 닫아야 한다. 페이지 정책보다 우선한다.
  assign force_precharge = bank_active && (open_cnt_q >= (tcfg.t_ras_max - TW'(8)));

`ifndef SYNTHESIS
  a_tras_max: assert property (@(posedge ck) disable iff (!rst_n)
    (open_cnt_q < tcfg.t_ras_max))
    else $error("tRAS max (9 x tREFI) exceeded on bank %0d", BANK_ID);
`endif

endmodule
```

## 7. RAA 카운터와 DRFM 주소 레지스터

```systemverilog
// RAA는 뱅크별. 문턱값은 DEVICE_ID에서 읽은 런타임 값이다 (§6.3.2.5.3)
// DRFM 유효 샘플이 있는 RFMpb는 DRFMpb로 실행되며 RAA를 감소시키지 않는다 (§6.3.2.5.5)
module hbm4_raa_drfm
  import hbm4_cfg_pkg::*;
#(parameter int NUM_BANKS = 64)
(
  input  logic            ck, rst_n,
  input  dev_cfg_t        dcfg,
  input  logic            drfm_enabled,        // MR0 OP3
  input  logic            act_valid,
  input  logic [$clog2(NUM_BANKS)-1:0] act_bank,
  input  logic            act_drfm,            // ACT의 DRFM 비트
  input  logic [RA_W-1:0] act_ra,
  input  logic            rfmab_i, rfmpb_i, refab_i, refpb_i,
  input  logic [$clog2(NUM_BANKS)-1:0] cmd_bank,
  input  logic            sref_held_ge_trasrf, // tRAASRF 이상 유지
  output logic            act_blocked          // RAAMMT 도달
);

  logic [15:0]     raa_q        [NUM_BANKS];
  logic [RA_W-1:0] drfm_addr_q  [NUM_BANKS];
  logic            drfm_valid_q [NUM_BANKS];

  // 유효 샘플이 있으면 DRFMpb — RAA 감소 없음
  wire is_drfmpb = rfmpb_i && drfm_valid_q[cmd_bank];

  always_ff @(posedge ck or negedge rst_n) begin
    if (!rst_n) begin
      for (int b = 0; b < NUM_BANKS; b++) begin
        raa_q[b]        <= '0;
        drfm_valid_q[b] <= 1'b0;
      end
    end else begin
      for (int b = 0; b < NUM_BANKS; b++) begin
        if (sref_held_ge_trasrf)
          raa_q[b] <= '0;                                   // tRAASRF 이상일 때만
        else if (act_valid && (act_bank == b))
          raa_q[b] <= raa_q[b] + 16'd1;
        else if (rfmab_i || (rfmpb_i && (cmd_bank == b) && !is_drfmpb))
          raa_q[b] <= (raa_q[b] > dcfg.raa_imt)             // 하한 0, pull-in 금지
                    ? (raa_q[b] - dcfg.raa_imt) : 16'd0;
        else if (refab_i || (refpb_i && (cmd_bank == b)))
          raa_q[b] <= (raa_q[b] > dcfg.raa_dec)
                    ? (raa_q[b] - dcfg.raa_dec) : 16'd0;
      end

      // DRFM 주소 캡처 — 뱅크마다 최신 샘플만 유지
      if (act_valid && act_drfm && drfm_enabled) begin
        drfm_addr_q [act_bank] <= act_ra;
        drfm_valid_q[act_bank] <= 1'b1;
      end
      if (is_drfmpb)
        drfm_valid_q[cmd_bank] <= 1'b0;                     // 서비스 후 소진
    end
  end

  assign act_blocked = (raa_q[act_bank] >= dcfg.raa_mmt);

`ifndef SYNTHESIS
  a_no_pullin: assert property (@(posedge ck) disable iff (!rst_n)
    (raa_q[cmd_bank] <= dcfg.raa_mmt))
    else $error("RAA exceeded RAAMMT");
`endif

endmodule
```

## 8. WDQS 토글 패리티 감시

**1비트면 충분합니다.** 전체 개수를 셀 필요가 없습니다 → [05장](../05_clocking_dbi/)

```systemverilog
// preamble + postamble + 모든 트레이닝 토글의 합이 짝수여야 한다 (§6.1)
// 분주기 재초기화 3시점(SR exit / power-up / PD exit)에 함께 리셋한다.
module hbm4_wdqs_parity (
  input  logic ck, rst_n,
  input  logic wdqs_toggle,          // WDQS 펄스 1개당 1펄스
  input  logic divider_reload,       // SR exit / power-up / PD exit
  input  logic seq_done,             // 시퀀스(버스트·트레이닝) 종료
  output logic parity_bad
);

  logic parity_q;

  always_ff @(posedge ck or negedge rst_n) begin
    if (!rst_n)            parity_q <= 1'b0;
    else if (divider_reload) parity_q <= 1'b0;     // 분주기 리셋과 정렬
    else if (wdqs_toggle)  parity_q <= ~parity_q;
  end

  assign parity_bad = seq_done & parity_q;         // 종료 시 홀수면 위반

`ifndef SYNTHESIS
  a_wdqs_even: assert property (@(posedge ck) disable iff (!rst_n)
    seq_done |-> (parity_q == 1'b0))
    else $error("WDQS toggle count is odd - internal WDQS/2 phase inverted");
`endif

endmodule
```

## 9. DBIac 인코더·디코더

```systemverilog
// 전이 수 4에서 직전 DBI 상태를 참조하는 히스테리시스가 있다 (Table 32)
// ECC·SEV·DPAR은 대상이 아니다 (§6.2.1)
function automatic logic dbi_decide(
    input logic [7:0] cur_byte,
    input logic [7:0] prev_byte,
    input logic       prev_dbi);
  int unsigned n = $countones(cur_byte ^ prev_byte);
  if      (n > 4)  return 1'b1;          // 5~8 : 반전
  else if (n == 4) return prev_dbi;      // 4    : 직전 상태 유지
  else             return 1'b0;          // 0~3 : 반전 안 함
endfunction

module hbm4_dbi_state (
  input  logic ck, rst_n,
  input  logic reset_n_deassert,   // RESET_n 비어서트
  input  logic mrs_received,       // MRS 수신
  input  logic wr_to_rd_turn,      // write→read 턴어라운드
  input  logic sref_exit,          // Self Refresh 종료
  input  logic rd_data_valid,
  input  logic dbi_sig,
  output logic dbi_state
);

  // 리셋 조건 네 가지 (§6.2.1.1)
  wire state_reset = reset_n_deassert | mrs_received | wr_to_rd_turn | sref_exit;

  logic dbi_state_q;
  always_ff @(posedge ck or negedge rst_n) begin
    if (!rst_n)            dbi_state_q <= 1'b0;
    else if (state_reset)  dbi_state_q <= 1'b0;          // LOW로 리셋
    else if (rd_data_valid) dbi_state_q <= dbi_sig;      // 마지막 UI가 다음 시드
  end

  assign dbi_state = dbi_state_q;
endmodule
```

## 10. CA 패리티 생성

```systemverilog
// 대상: R[9:0] + C[7:0] + ARFU + APAR, 짝수 패리티, 양 에지 각각 (§6.4.1)
// ARFU를 빼먹으면 안 된다 (§11.1 — 미사용 범프지만 패리티에 참여)
function automatic logic ca_parity(
    input logic [9:0] r, input logic [7:0] c, input logic arfu);
  return ^{r, c, arfu};          // APAR을 더해 전체가 짝수가 되도록
endfunction

// 패리티 활성 구간은 비대칭이다 (§6.3.3.4, §6.4.1)
//   켤 때 : MRS(enable) 다음 커맨드부터
//   끌 때 : MRS(disable) + tMOD 만료 후부터
module hbm4_parity_window #(parameter int T_MOD = 32) (
  input  logic ck, rst_n,
  input  logic mrs_capar_enable,
  input  logic mrs_capar_disable,
  output logic parity_required
);
  logic                    required_q, disable_pending_q;
  logic [$clog2(T_MOD):0]  tmod_q;

  always_ff @(posedge ck or negedge rst_n) begin
    if (!rst_n) begin
      required_q <= 1'b0; disable_pending_q <= 1'b0; tmod_q <= '0;
    end else if (mrs_capar_enable) begin
      required_q <= 1'b1;                         // 즉시 다음 커맨드부터
    end else if (mrs_capar_disable) begin
      disable_pending_q <= 1'b1;
      tmod_q            <= T_MOD;
    end else if (disable_pending_q) begin
      if (tmod_q == 0) begin
        required_q        <= 1'b0;                // tMOD 만료 후에야 해제
        disable_pending_q <= 1'b0;
      end else
        tmod_q <= tmod_q - 1'b1;
    end
  end

  assign parity_required = required_q;
endmodule
```

## 11. SEV 디코더

```systemverilog
// SEV는 BL8의 후반부(위치 4~7)에만 유효한 2비트 코드를 싣는다 (Table 67)
// 전반부를 함께 샘플링하면 언제나 NE가 나온다.
module hbm4_sev_decoder (
  input  logic       rdqs, rst_n,
  input  logic       burst_start,
  input  logic [1:0] sev_i,          // {SEV1, SEV0}
  output logic [1:0] sev_code,
  output logic       sev_valid
);
  typedef enum logic [1:0] {
    SEV_NE = 2'b00, SEV_CES = 2'b01, SEV_UE = 2'b10, SEV_CEM = 2'b11
  } sev_e;

  logic [2:0] pos_q;
  logic [1:0] code_q;
  logic       valid_q;

  always_ff @(posedge rdqs or negedge rst_n) begin
    if (!rst_n) begin
      pos_q <= '0; code_q <= SEV_NE; valid_q <= 1'b0;
    end else begin
      pos_q <= burst_start ? 3'd0 : (pos_q + 3'd1);
      if (pos_q == 3'd4) begin                     // 후반부 첫 위치에서 캡처
        code_q  <= sev_i;
        valid_q <= 1'b1;
      end else if (burst_start)
        valid_q <= 1'b0;
    end
  end

  assign sev_code  = code_q;
  assign sev_valid = valid_q;
endmodule
```

:::caution[`SEV_NE`를 무오류로 해석하지 말 것]
`ERRCNT`가 `ERRTH` 이하이면 CEs가 NE로 보고됩니다(§6.9.5). 상위 로직은 **NE를 "보고 임계 미만"으로 취급**하고, 실제 정정 발생 여부는 **ECS 로그**로 확인해야 합니다 → [09장](../09_ecc_ecs_sev/)
:::

## 12. `DERR` 모드 디코딩

```systemverilog
// DERR는 세 가지 의미를 갖는다 (§6.4.2, §6.1.1, §6.11.3)
module hbm4_derr_mux (
  input  logic ck, rst_n,
  input  logic mr6_op6,        // DCM 활성
  input  logic mr8_op3,        // WDQS-to-CK 트레이닝 활성
  input  logic derr_i,
  output logic parity_error,
  output logic phase_early,
  output logic duty_ge_50
);
  assign duty_ge_50   =  mr6_op6            & derr_i;
  assign phase_early  = ~mr6_op6 &  mr8_op3 & derr_i;
  assign parity_error = ~mr6_op6 & ~mr8_op3 & derr_i;

`ifndef SYNTHESIS
  // 두 트레이닝을 동시에 켜면 DERR 해석이 모호해진다
  a_single_mode: assert property (@(posedge ck) disable iff (!rst_n)
    !(mr6_op6 && mr8_op3))
    else $error("DCM and WDQS-to-CK training both enabled - DERR ambiguous");
`endif
endmodule
```

## 13. 초기화 FSM 골격

시간 단위와 클럭 단위 타이머를 **분리**하는 것이 요령입니다 → [03장](../03_init_reset_power/)

```systemverilog
module hbm4_init_fsm #(
  parameter int T_INIT1_US   = 200,     // ≥ 200 µs
  parameter int T_INIT3_US   = 4000,    // ≥ 4 ms   ← 지배적
  parameter int T_INIT5_NS   = 200,     // ≥ 200 ns
  parameter int T_INIT4_NCK  = 10,
  parameter int T_INIT7_NCK  = 2
)(
  input  logic ck, rst_n,
  input  logic us_tick,                 // 1 µs 틱
  input  logic power_ramp_done,
  output logic reset_n_o, wrst_n_o,
  output logic [3:0] r_cmd_o,           // R[3:0]
  output logic [2:0] c_cmd_o,           // C[2:0]
  output logic init_done, ieee1500_ready
);

  typedef enum logic [3:0] {
    I_PWR, I_RST_LOW, I_CK_STATIC, I_RELEASE, I_HOLD_PDE,
    I_FUSE_CAL, I_CK_STABLE, I_PDX, I_PRE_MRS, I_MRS, I_DONE
  } init_e;

  init_e             state_q;
  logic [15:0]       us_cnt_q;          // ms 단위까지 담는다
  logic [4:0]        nck_cnt_q;         // nCK 단위 제약 전용

  localparam logic [3:0] R_PDE = 4'b1010;   // H,L,H,L
  localparam logic [3:0] R_PDX = 4'b1111;
  localparam logic [2:0] C_CNOP = 3'b111;

  always_ff @(posedge ck or negedge rst_n) begin
    if (!rst_n) begin
      state_q <= I_PWR; us_cnt_q <= '0; nck_cnt_q <= '0;
    end else begin
      unique case (state_q)
        I_PWR:        if (power_ramp_done) begin state_q <= I_RST_LOW; us_cnt_q <= '0; end
        I_RST_LOW:    if (us_tick) begin
                        if (us_cnt_q >= T_INIT1_US) begin state_q <= I_CK_STATIC; us_cnt_q <= '0; end
                        else us_cnt_q <= us_cnt_q + 1'b1;
                      end
        I_CK_STATIC:  state_q <= I_RELEASE;                    // tINIT2는 ns 단위
        I_RELEASE:    begin state_q <= I_HOLD_PDE; nck_cnt_q <= '0; end
        I_HOLD_PDE:   if (nck_cnt_q >= T_INIT7_NCK) begin state_q <= I_FUSE_CAL; us_cnt_q <= '0; end
                      else nck_cnt_q <= nck_cnt_q + 1'b1;
        I_FUSE_CAL:   if (us_tick) begin                       // ← tINIT3, 4 ms
                        if (us_cnt_q >= T_INIT3_US) begin state_q <= I_CK_STABLE; nck_cnt_q <= '0; end
                        else us_cnt_q <= us_cnt_q + 1'b1;
                      end
        I_CK_STABLE:  if (nck_cnt_q >= T_INIT4_NCK) state_q <= I_PDX;
                      else nck_cnt_q <= nck_cnt_q + 1'b1;
        I_PDX:        state_q <= I_PRE_MRS;
        I_PRE_MRS:    state_q <= I_MRS;                        // tINIT5는 ns 단위
        I_MRS:        state_q <= I_DONE;                       // 20개 MR 기록은 상위에서
        default: ;
      endcase
    end
  end

  assign reset_n_o      = !(state_q inside {I_PWR, I_RST_LOW});
  assign wrst_n_o       = reset_n_o;                     // 기능 리셋은 포트 리셋 동반 (§4)
  assign ieee1500_ready = (state_q >= I_CK_STABLE);      // tINIT3 이후
  assign init_done      = (state_q == I_DONE);

  // R[0]은 동기 신호 — 조합 논리로 구동하면 tIS 위반 (§4.1 step 5)
  always_ff @(posedge ck) begin
    if (state_q inside {I_RELEASE, I_HOLD_PDE, I_FUSE_CAL, I_CK_STABLE})
      r_cmd_o <= R_PDE;
    else if (state_q >= I_PDX)
      r_cmd_o <= R_PDX;
    c_cmd_o <= C_CNOP;
  end

endmodule
```

## 14. 채널 경계 CDC

채널은 **비동기일 수 있습니다**(§1). 다만 **채널 내 두 PC는 CK를 공유**하므로 그 사이에는 CDC가 필요 없습니다 → [01장](../01_landscape_organization/)

```systemverilog
// 채널마다 독립 클럭 도메인. PC 사이에는 CDC를 두지 않는다.
module hbm4_ch_cdc #(parameter int W = 64) (
  input  logic         host_clk, host_rst_n,
  input  logic         ch_clk,   ch_rst_n,
  input  logic         req_valid,
  input  logic [W-1:0] req_data,
  output logic         req_ready,
  output logic         ch_valid,
  output logic [W-1:0] ch_data
);
  // 비동기 FIFO 또는 2-flop 동기화 + 핸드셰이크.
  // 여기서는 인터페이스 경계만 보인다 — 실제 구현은 프로젝트 표준을 따른다.
  // 주의: 32채널이면 이 인스턴스가 32개다. PC별로 복제하면 64개가 되어 낭비다.
endmodule
```

## 15. 패턴 → 장 대응

| 패턴 | 규격 근거 | 장 |
|---|---|---|
| 구성 파라미터 · 런타임 구조체 | §1–3, §13.5.11 | [01](../01_landscape_organization/) · [11](../11_training_ieee1500/) |
| 라운딩 함수 | §6.3.2.4 | [06](../06_row_commands/) |
| 반주기 커맨드 디코더 | §6.3, Table 33 | [06](../06_row_commands/) |
| ACT 슬롯 검사 | Table 33 Note 9 | [06](../06_row_commands/) |
| 타이밍 3택 선택 | Table 6, §10 Note 17 | [02](../02_addressing_bank_groups/) · [07](../07_column_commands/) |
| 뱅크 FSM · `tRAS` 최대 | §3.3, §10 | [02](../02_addressing_bank_groups/) · [12](../12_electrical_timing_package/) |
| RAA · DRFM | §6.3.2.5.3–5 | [06](../06_row_commands/) |
| WDQS 토글 패리티 | §6.1 | [05](../05_clocking_dbi/) |
| DBIac | §6.2.1, Table 32 | [05](../05_clocking_dbi/) |
| CA 패리티 · 활성 구간 | §6.4.1, §6.3.3.4 | [08](../08_parity/) |
| SEV 디코더 | Table 67–68 | [09](../09_ecc_ecs_sev/) |
| `DERR` 모드 먹스 | §6.4.2 · §6.1.1 · §6.11.3 | [11](../11_training_ieee1500/) |
| 초기화 FSM | §4 | [03](../03_init_reset_power/) |
| 채널 CDC | §1, §3.1 | [01](../01_landscape_organization/) |
