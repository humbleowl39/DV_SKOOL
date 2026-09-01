---
title: "부록 C — 검증 패턴"
description: 12개 장의 규격 제약을 SVA·covergroup·reference model·시퀀스로 옮긴 참조 패턴 모음
---

:::caution[사용 범위]
본 부록의 코드는 **규격 제약을 어떤 검증 구조로 옮기는가**를 보이기 위한 **참조 패턴**입니다. 특정 프로젝트의 구현이 아니며, 벤더 데이터시트 값과 DUT 인터페이스를 반영해야 실제 환경이 됩니다.

환경을 **어떻게 구성하고 계층화하는가**(Agent·VIP·env·V-Plan·회귀 운영)는 [`hbm_dv`](../../hbm_dv/)에서 다룹니다. 여기서는 **조문 하나가 어떤 코드가 되는가**까지입니다.

수치는 [부록 A](../appendix_a_quick_reference/)의 요약을 따르며, 근거는 각 패턴에 절 번호로 표시했습니다.
:::

:::note[인용 고지]
코드 주석의 절 번호는 **JESD270-4 (2025-04, WIP draft)** 를 가리킵니다. 규격 조문을 **요약·재구성**해 검증 의도를 밝힌 것이며 원문 복제가 아닙니다. 정밀 값과 인코딩은 **JEDEC 원문 우선**입니다.
:::

---

## 0. 이 부록을 읽는 법

패턴을 **네 부류**로 나눴습니다. 각 장의 `🔬 검증 적용` 절에서 본 4소절 구조와 대응합니다.

| 부류 | 패턴 | 답하는 질문 |
|---|---|---|
| **A. 기반** | 1–3 | 환경이 무엇을 알고 시작하는가 |
| **B. Checker** | 4–9 | 조문을 어떤 수단으로 옮기는가 |
| **C. Model** | 10–14 | 기대값을 어떻게 유지하는가 |
| **D. Stimulus** | 15–17 | 커버리지 구멍을 어떻게 메우는가 |

**수단 선택의 원칙**을 먼저 정리해 둡니다. 이 코스에서 반복해서 나온 판단 기준입니다.

| 규칙의 성격 | 수단 | 예 |
|---|---|---|
| 두 신호 사이의 **국소 시간 관계** | **SVA** | `tCCD`, ACT 후속 슬롯 |
| **누적 상태**가 만드는 조건 | **reference model** | RAA 카운터, DBIac 직전 상태 |
| **데이터 무결성** | **scoreboard** | 주소↔데이터 대응 |
| **명령 순서** 절차 | **프로토콜 checker** | lane repair, ECS 설정 순서 |
| **분포**로만 판정 가능 | **통계 collector** | SID별 레이턴시 균등성 |
| 기대값이 **존재하지 않음** | **자극 측 제약** | unspecified operation |

---

# A. 기반

## 1. 구성 객체 — 상수가 아니라 config

규격이 `vendor specific`으로 남긴 값은 전부 **환경 파라미터**여야 합니다. 상수로 박으면 다른 장치·다른 프로파일에서 조용히 틀린 기준이 됩니다.

```systemverilog
package hbm4_cfg_pkg;

  // ---- 구조 상수 (§1–3) — 이것들은 규격이 고정한다 -------------------------
  localparam int NUM_CH        = 32;
  localparam int NUM_PC        = 2;
  localparam int DQ_PER_CH     = 64;
  localparam int DQ_PER_PC     = 32;
  localparam int BL            = 8;      // 중단·절단 없음 (§6.3.3)
  localparam int PREFETCH_BITS = 256;    // PC당

  // ---- 주소 폭 (§3.2, Table 4) --------------------------------------------
  localparam int RA_W  = 14;   // RA[13:12] = 11 무효
  localparam int CA_W  = 5;    // BL8 의 8 UI 를 구분하지 않음 (Note 2)
  localparam int BA_W  = 4;
  localparam int SID_W = 2;    // 구성별 0/1/2 비트 사용

endpackage
```

```systemverilog
// 런타임에 확정되는 값. 상당수는 DEVICE_ID WDR 에서 읽어야 한다 (§13.5.11).
class hbm4_cfg extends uvm_object;
  `uvm_object_utils(hbm4_cfg)

  // ---- 구성 (부팅 시 DEVICE_ID 로 확정) ----------------------------------
  rand int unsigned stack_height;      // 4 / 8 / 12 / 16
  rand int unsigned density_gb;        // 24 / 32
  rand int unsigned sid_used_bits;     // 0 / 1 / 2
  rand int unsigned num_banks;         // 16 / 32 / 48 / 64

  // ---- DEVICE_ID 에서 읽는 벤더 지정값 — 상수로 박으면 안 되는 것들 -------
  int unsigned raaimt, raammt, raadec; // §6.3.2.5.3 — RAA 문턱
  bit          rfm_required;           // §6.3.2.5.3 Note 7
  bit          arfm_supported;         // §6.3.2.5.4
  bit          rxoffc_supported;       // §6.12.1
  int unsigned errth;                  // §6.9.5 Table 68 — CEs 필터 임계값
  int unsigned t_ccdr_ck;              // §10 Note 17 — 벤더 지정·주파수 의존
  int unsigned vsp_mv;                 // §4.1 — VDDC/VDDQ 마진, vendor specific

  // ---- 동작 조건 ----------------------------------------------------------
  rand int unsigned t_ck_ps;
  rand vddq_e       vddq;              // §7.2 — 네 전형값
  rand clk_rel_e    ch_clk_relation;   // §3.1 — 채널은 비동기일 수 있다

  // 규격이 정의한 조합만 유효하다 (Table 4)
  constraint c_valid_config {
    stack_height inside {4, 8, 12, 16};
    (stack_height == 4)  -> sid_used_bits == 0;
    (stack_height == 8)  -> sid_used_bits == 1;
    (stack_height >= 12) -> sid_used_bits == 2;
    num_banks == 16 * (stack_height / 4);
  }

  // DEVICE_ID 를 읽기 전에는 RAA 모델을 만들 수 없다 — 순서가 있다
  function bit device_id_loaded();
    return (raaimt != 0) && (raammt != 0);
  endfunction
endclass
```

:::caution[환경 구성 순서]
`DEVICE_ID`는 IEEE 1500 WDR에 있고, IEEE1500 명령은 `tINIT3` 이후에만 쓸 수 있습니다([03장](../03_init_reset_power/)). 따라서 **일부 구성은 `build_phase`가 아니라 `run_phase` 중에 확정**됩니다.

```
reset → tINIT3 → WRST_n HIGH → DEVICE_ID 읽기
   → 밀도 코드      → 주소 구성        ([02장](../02_addressing_bank_groups/))
   → RAAIMT/MMT/DEC → RAA 모델         ([06장](../06_row_commands/))
   → ARFM 지원      → MR8 값 결정      ([06장](../06_row_commands/))
   → ERRTH          → SEV 필터 모델    ([09장](../09_ecc_ecs_sev/))
   → 그 뒤에야 MR 프로그램과 트래픽
```

covergroup의 bin 경계가 이 값들에 의존한다면, **절대값 대신 상대 zone**으로 잡으세요(패턴 8).
:::

## 2. 라운딩 — 기대값 계산의 단일 출처

HBM4는 **0.5 nCK 해상도**를 갖습니다(§6.3.2.4). checker와 시퀀스가 각자 구현하면 언젠가 갈립니다.

```systemverilog
// §6.3.2.4 — nXX = 0.5 × RU(2 × tXX / tCK). 반사이클 정수 단위로 반환한다.
function automatic int hbm4_round_half(input int t_ps, input int tck_ps);
  return (2*t_ps + tck_ps - 1) / tck_ps;
endfunction

// 대상은 tRAS · tRTP · tWR · tRP. tRP 결과가 하강 에지면 +0.5 (§6.3.2.4)
function automatic int hbm4_trp_half(input int t_ps, input int tck_ps);
  int h = hbm4_round_half(t_ps, tck_ps);
  return (h % 2 == 1) ? h + 1 : h;      // 하강 에지 보정
endfunction

// 전통 공식과의 차이를 드러내는 검사 — 이식된 코드가 섞였는지 확인한다
function automatic void assert_not_legacy_rounding(int t_ps, int tck_ps);
  int legacy = ((t_ps + tck_ps - 1) / tck_ps) * 2;   // RU(t/tCK) 을 반사이클로
  int hbm4   = hbm4_round_half(t_ps, tck_ps);
  if (legacy != hbm4)
    `uvm_info("ROUNDING", $sformatf(
      "HBM4 라운딩이 전통 공식과 다르다 (%0d vs %0d 반사이클). 이 차이가 검증 대상이다",
      hbm4, legacy), UVM_HIGH)
endfunction
```

## 3. 반주기 커맨드 monitor

커맨드가 **0.5 / 1 / 1.5 사이클**로 나뉘므로(§2), 정수 사이클로 샘플링하는 monitor는 1.5 사이클 `ACT`를 놓치거나 두 번 셉니다. 검사가 아니라 **환경의 전제조건**이라, 틀려도 에러가 안 나고 **커버리지가 이유 없이 낮아지는** 형태로만 드러납니다.

```systemverilog
class hbm4_cmd_monitor extends uvm_monitor;
  `uvm_component_utils(hbm4_cmd_monitor)
  virtual hbm4_if vif;
  uvm_analysis_port #(hbm4_cmd_item) ap;

  task run_phase(uvm_phase phase);
    fork
      sample_edge(1'b1);        // 상승 에지
      sample_edge(1'b0);        // 하강 에지 — 양쪽을 모두 봐야 한다
    join
  endtask

  // 커맨드/주소는 DDR 로 전송된다 (§2). 반 사이클이 자연스러운 단위다.
  task sample_edge(bit rising);
    forever begin
      if (rising) @(posedge vif.ck); else @(negedge vif.ck);
      collect_row_cmd(rising);
      collect_col_cmd(rising);
    end
  endtask

  // ACT 는 1.5 사이클이므로 상승에서 시작해 다음 상승에서 끝난다.
  // 그 사이 하강 에지는 패딩이며, Table 33 Note 9 의 제약을 받는다.
  task collect_row_cmd(bit rising);
    hbm4_cmd_item it = hbm4_cmd_item::type_id::create("it");
    it.edge_is_rising = rising;
    it.raw            = vif.r;
    it.cmd            = decode_row(vif.r, rising);
    // Note 5 — PC 로 선택되지 않은 pseudo channel 은 RNOP 을 수행한다.
    // 커맨드는 항상 양쪽에 도달한다.
    it.pc_selected    = vif.r[PC_BIT];
    ap.write(it);
  endtask
endclass
```

---

# B. Checker

## 4. ACT 후속 슬롯 — 짝 cover property가 필수인 이유

```systemverilog
// Table 33 Note 9 — ACT 두 번째 사이클 하강 에지에 허용되는 것은
// RNOP, 다른 뱅크 PREpb, 다른 PC PREab 셋뿐이다.
module hbm4_act_slot_chk (input logic ck, rst_n, act_vld,
                          input logic [5:0] act_bank, input logic act_pc,
                          input row_cmd_e row_cmd,
                          input logic [5:0] row_bank, input logic row_pc);
  import uvm_pkg::*;
  `include "uvm_macros.svh"

  property p_act_follow_slot;
    logic [5:0] b; logic pc;
    @(posedge ck) disable iff (!rst_n)
      (act_vld, b = act_bank, pc = act_pc) |-> ##1 @(negedge ck)
        ( (row_cmd == RNOP)
        || (row_cmd == PREPB && row_bank != b)
        || (row_cmd == PREAB && row_pc   != pc) );
  endproperty

  a_act_follow_slot: assert property (p_act_follow_slot)
    else `uvm_error("ACT_SLOT", $sformatf(
         "ACT 후속 하강 에지에 허용되지 않은 커맨드 %s (Table 33 Note 9)",
         row_cmd.name()))

  // ★ 셋을 각각 겪었는가. 이것이 없으면 assertion 은 RNOP 만 확인하고 통과한다.
  //   나머지 둘은 스케줄러가 그 최적화를 쓸 때만 나온다.
  c_slot_rnop : cover property (@(posedge ck) act_vld ##1 @(negedge ck) row_cmd == RNOP);
  c_slot_prepb: cover property (@(posedge ck) act_vld ##1 @(negedge ck) row_cmd == PREPB);
  c_slot_preab: cover property (@(posedge ck) act_vld ##1 @(negedge ck) row_cmd == PREAB);
endmodule
```

:::tip[assertion에는 짝 cover가 필요하다]
이 코스에서 반복해 나온 패턴입니다. **"위반 0건"은 검사가 유효했다는 뜻이 아닙니다.** 세 가지 이유로 0건이 나옵니다.

1. 실제로 위반이 없었다 ← 원하는 것
2. 그 조건이 **한 번도 발생하지 않았다** ← cover가 드러낸다
3. assertion 자체가 **잘못 쓰여 항상 참** ← cover가 간접적으로 드러낸다

`&`를 `|`로 잘못 쓴 assertion은 언제나 통과합니다. 짝 cover가 그 무력함을 드러냅니다.
:::

## 5. 그룹·SID 의존 타이밍 — 3택 판정

```systemverilog
// Table 6 + §10 Note 17
//   같은 그룹              → tCCDL
//   다른 그룹, 같은 SID    → tCCDS
//   다른 그룹, 다른 SID    → tCCDR   (READ 전용, 8/12/16-Hi 전용)
function automatic int unsigned ccd_min(input bit is_read,
                                        input bit same_group, input bit same_sid,
                                        input hbm4_cfg cfg);
  if (same_group) return T_CCDL;
  if (!is_read)   return T_CCDS;            // WRITE 는 SID 를 보지 않는다
  return same_sid ? T_CCDS : cfg.t_ccdr_ck; // 벤더 지정값 — cfg 에서 온다
endfunction

// 판정 상태는 PC 별로 유지한다. 채널 계층에 두면 PC0 의 접근이
// PC1 의 임계값 선택을 오염시킨다 (§3.1.2).
property p_ccd(bit is_read, int pc);
  int unsigned req;
  @(posedge ck) disable iff (!rst_n)
    (col_cmd_vld[pc] && (col_is_read[pc] == is_read),
       req = ccd_min(is_read, (bg[pc] == last_bg[pc]), (sid[pc] == last_sid[pc]), cfg))
      |-> (cycles_since_last_col[pc] >= req);
endproperty

// 세 분기를 각각 — ccdr 은 4-High 프로파일에서 성립하지 않는다
c_ccdl: cover property (@(posedge ck) col_cmd_vld && (bg == last_bg[pc]));
c_ccds: cover property (@(posedge ck) col_cmd_vld && (bg != last_bg[pc])
                                                  && (sid == last_sid[pc]));
c_ccdr: cover property (@(posedge ck) col_cmd_vld && col_is_read
                                                  && (bg != last_bg[pc])
                                                  && (sid != last_sid[pc]));
```

## 6. 시간 상한 검사 — `tINIT6`와 `tRAS(max)`

대부분의 타이밍은 최소값이지만 **최대 제약이 둘** 있습니다. 코드 형태가 반대가 됩니다 — "이만큼 기다렸는가"가 아니라 **"이 안에 끝났는가"**.

```systemverilog
// ① tINIT6 (§4.1, Table 7) — 최대 100 ns. 이 구간에는 CK 가 없으므로
//    시각 기반으로 쓴다. @(posedge ck) SVA 는 평가조차 되지 않는다.
always @(negedge reset_n) begin
  fork
    begin : watch_init6
      #(T_INIT6_MAX);
      if (!(rdqs_t == 1'b0 && rdqs_c == 1'b1 && !aerr && !derr))
        `uvm_error("INIT", "tINIT6(최대) 안에 출력이 정적 레벨에 도달하지 않았다")
    end
    begin @(posedge reset_n) disable watch_init6; end
  join_any
end

// ② tRAS(max) = 9 × tREFI (§10) — 행을 그보다 오래 열어 두면 안 된다.
//    "tRAS" 하면 최소를 떠올려서, 최대 검사가 빠진 환경이 흔하다.
generate for (genvar b = 0; b < NUM_BANKS; b++) begin : g_tras
  a_tras_max: assert property (@(posedge ck) disable iff (!rst_n)
      $rose(bank_active[b]) |-> ##[1:T_RAS_MAX] $fell(bank_active[b]))
    else `uvm_error("tRAS_MAX", $sformatf("뱅크 %0d 가 tRAS(max) 를 넘겨 열려 있었다", b))

  // 랜덤 트래픽은 경계 근처에 가지 못한다 — 도달 여부를 센다
  c_tras_near_max: cover property (@(posedge ck)
      bank_active[b] && (cycles_open[b] > (T_RAS_MAX * 9 / 10)));
end endgenerate
```

## 7. 관대 구간 — 규격이 시점을 열어 둔 경우

§6.4.1은 패리티 검사가 켜지는 시점을 **구간으로만** 규정합니다. 한쪽으로 못 박으면 **false FAIL** 아니면 **놓친 위반**이 됩니다.

```systemverilog
// MRS(enable) 다음 사이클 ~ tMOD 만료 사이 어디서든 켜질 수 있다 (§6.4.1)
typedef enum {PAR_OFF, PAR_TURNING_ON, PAR_ON, PAR_TURNING_OFF} par_state_e;

// 구간 밖에서만 엄격히 판정한다
a_parity_on : assert property (@(posedge ck) disable iff (!rst_n)
    (par_state == PAR_ON && bad_parity_injected) |-> ##[1:T_PARAC+1] aerr)
  else `uvm_error("CAPAR", "활성 구간의 패리티 오류가 AERR 로 보고되지 않았다")

a_parity_off: assert property (@(posedge ck) disable iff (!rst_n)
    (par_state == PAR_OFF) |-> !aerr)
  else `uvm_error("CAPAR", "비활성 상태인데 AERR 가 보고되었다")

// PAR_TURNING_ON 구간에는 assertion 을 두지 않는다. 대신 지나갔는지만 센다.
c_turning_on : cover property (@(posedge ck) par_state == PAR_TURNING_ON);
// 그 구간 안에서 커맨드를 발행해 봤는가 — 안 하면 비대칭은 미검증이다
c_cmd_in_window: cover property (@(posedge ck)
    (par_state == PAR_TURNING_OFF) ##0 any_cmd_vld);
```

:::tip[조동사가 수단을 정한다]
`shall` → **assertion**(위반하면 버그) · `may` → **coverage 축 + 관대 구간** · `vendor specific` → **config 파라미터**.

규격을 읽으면서 이 셋을 표시해 두면 V-Plan이 거의 자동으로 나옵니다.
:::

## 8. 문턱 대비 zone — bin 경계를 런타임에 정할 수 없을 때

`RAAIMT`·`RAAMMT`·`ERRTH`는 `DEVICE_ID`에서 옵니다. `build_phase`에서는 값을 모르므로 **절대값 bin을 만들 수 없습니다.**

```systemverilog
// 절대값 대신 문턱 대비 위치로 bin 을 잡는다
typedef enum {RAA_ZERO, RAA_BELOW_IMT, RAA_AT_IMT, RAA_BETWEEN, RAA_AT_MMT} raa_zone_e;

function automatic raa_zone_e raa_zone(int raa, int imt, int mmt);
  if (raa == 0)   return RAA_ZERO;
  if (raa <  imt) return RAA_BELOW_IMT;
  if (raa == imt) return RAA_AT_IMT;      // RFM 이 필요해지는 지점
  if (raa <  mmt) return RAA_BETWEEN;
  return RAA_AT_MMT;                       // ACTIVATE 금지 지점
endfunction

covergroup cg_raa with function sample(int raa, hbm4_cfg cfg);
  cp_zone : coverpoint raa_zone(raa, cfg.raaimt, cfg.raammt) {
    bins zero      = {RAA_ZERO};
    bins below     = {RAA_BELOW_IMT};
    bins at_imt    = {RAA_AT_IMT};
    bins between   = {RAA_BETWEEN};
    bins at_mmt    = {RAA_AT_MMT};        // ★ 랜덤 트래픽으로는 도달 불가
  }
endgroup
```

## 9. 프로토콜 checker — 펌웨어 절차를 검증한다

일부 규칙은 DUT가 아니라 **호스트 절차**에 대한 것입니다. 명령 스트림을 관측하는 checker로 잡습니다.

```systemverilog
// §4.4 + §6.7 — lane repair 절차
//   ① hard 데이터를 읽고 병합해야 한다 (읽지 않으면 퓨즈된 복구가 사라진다)
//   ② EXTEST 후에는 RESET_n 토글이 필수
//   ③ 한 UpdateWR 에 복구 벡터 하나 (전류 제약 — 시뮬에서 위반이 안 보인다)
//   ④ 복구 후 BYPASS 로 정상 모드 복귀
//   ⑤ CK 토글 이전에만 발행 가능
class lane_repair_protocol_chk extends uvm_subscriber #(ieee1500_item);
  `uvm_component_utils(lane_repair_protocol_chk)
  protected bit m_hard_read, m_extest_done, m_reset_after_extest, m_ck_toggling;
  protected int m_pending_repairs;

  function void write(ieee1500_item t);
    case (t.instr)
      EXTEST           : begin m_extest_done = 1; m_reset_after_extest = 0; end
      HBM_RESET        : m_reset_after_extest = 1;
      HARD_LANE_REPAIR : if (t.is_read) m_hard_read = 1;

      SOFT_LANE_REPAIR : begin
        if (m_ck_toggling)
          `uvm_error("LANE_REPAIR", "CK 토글 이후 발행 (§6.7)")
        if (!m_hard_read)
          `uvm_error("LANE_REPAIR",
            "hard 데이터를 읽지 않고 SOFT_LANE_REPAIR — 기존 퓨즈 복구가 덮어써진다 (§4.4)")
        if (m_extest_done && !m_reset_after_extest)
          `uvm_error("LANE_REPAIR", "EXTEST 후 리셋 토글 없이 복구 적용 (§4.4)")
        m_pending_repairs = count_non_Fh_fields(t.wdr_data);
      end

      UPDATE_WR : begin
        if (m_pending_repairs > 1)
          `uvm_error("LANE_REPAIR", $sformatf(
            "한 UpdateWR 에 복구 벡터 %0d 개. 전류 제약상 하나씩 (§6.7)", m_pending_repairs))
        m_pending_repairs = 0;
      end
      default: ;
    endcase
  endfunction
endclass
```

```systemverilog
// §6.9.4 — ECS 설정 순서. ECSCEM(OP6) 이 ECSREF/ECSSRF(OP[5:4]) 보다
// 먼저 또는 동시에. 첫 ECS 이후 변경 금지.
function void on_mr9_write(bit [7:0] val);
  bit cem = val[6], ref_en = val[5] | val[4];
  if (ref_en && !m_cem_programmed && cem == 1'b0)
    `uvm_error("ECS_ORDER", "ECSREF/ECSSRF 전에 ECSCEM 미프로그램 (§6.9.4)")
  if (m_ecs_started && (cem != m_cem_value))
    `uvm_error("ECS_ORDER", "첫 ECS 이후 ECSCEM 변경 — 후속 동작이 미정의 (§6.9.4)")
  m_cem_programmed = 1'b1; m_cem_value = cem;
endfunction
```

---

# C. Model

## 10. 주소 매핑 — 왕복 검사

주소 결함은 **데이터 미스매치로 위장**합니다. scoreboard는 "값이 다르다"고만 말하지 "주소가 틀렸다"고 말해 주지 않습니다.

```systemverilog
class hbm4_addr_model extends uvm_object;
  `uvm_object_utils(hbm4_addr_model)
  hbm4_cfg cfg;

  function hbm4_addr_t encode(bit [39:0] pa);
    // BL8 의 8 UI 를 고르는 하위 비트는 장치로 나가지 않는다 (Table 4 Note 2)
    bit [39:0] a = pa >> $clog2(BURST_BYTES);
    encode.ca  = a[CA_W-1:0];                     a = a >> CA_W;
    encode.ba  = a[BA_W-1:0];                     a = a >> BA_W;
    encode.sid = a[cfg.sid_used_bits-1:0];        a = a >> cfg.sid_used_bits;
    encode.ra  = a[RA_W-1:0];
  endfunction

  function bit [39:0] decode(hbm4_addr_t f);
    decode = f.ra;
    decode = (decode << cfg.sid_used_bits) | f.sid;
    decode = (decode << BA_W)              | f.ba;
    decode = (decode << CA_W)              | f.ca;
    decode = decode << $clog2(BURST_BYTES);
  endfunction

  // 왕복이 항등이어야 한다. 깨지는 대표 원인은 필드 폭의 합이 안 맞는 것이고,
  // 그 결함은 데이터 비교만으로는 "가끔 틀린다" 로만 보인다.
  function void check_roundtrip(bit [39:0] pa);
    bit [39:0] aligned = pa & ~((1 << $clog2(BURST_BYTES)) - 1);
    if (decode(encode(aligned)) !== aligned)
      `uvm_error("ADDR_MAP", $sformatf("왕복 불일치: %0h -> %0h",
                 aligned, decode(encode(aligned))))
  endfunction

  // 무효 조합은 모델이 아니라 핀에서 본다 — 모델은 무효 입력에도 답을 만든다
  function bit is_legal(hbm4_addr_t f);
    if (f.ra[13:12] == 2'b11)                        return 0;  // Note 5
    if (cfg.sid_used_bits == 2 && f.sid == 2'b11)    return 0;  // Note 6
    if (cfg.stack_height == 4 && f.sid[0])           return 0;  // Note 8
    return 1;
  endfunction
endclass
```

## 11. RAA — 같은 커맨드가 셋으로 갈린다

`RFMpb` 하나가 문맥에 따라 **무효과 · `DRFMpb` · 일반 `RFMpb`** 로 실행됩니다. 셋을 하나로 처리하면 RAA 예측이 반드시 어긋납니다.

```systemverilog
class raa_model extends uvm_object;
  `uvm_object_utils(raa_model)
  hbm4_cfg cfg;                          // 문턱값은 DEVICE_ID 에서 온다
  bit      mr0_drfm_en;                  // MR0 OP3
  bit [1:0] mr8_rfm_level;               // MR8 OP[5:4]

  protected int unsigned m_raa   [64];
  protected bit          m_drfm_v[64];   // 뱅크별 DRFM 주소 샘플 유효
  protected bit [13:0]   m_drfm_a[64];

  function void on_act(int bank, bit [13:0] row, bit drfm_bit);
    m_raa[bank]++;
    if (mr0_drfm_en && drfm_bit) begin   // §6.3.2.5.5 — 최신 샘플만 남는다
      m_drfm_a[bank] = row;
      m_drfm_v[bank] = 1'b1;
    end
  endfunction

  function void on_rfm_pb(int bank);
    // ① Note 7 — RFM 을 요구하지 않는 장치는 RNOP 을 실행한다. 오류가 아니다.
    if (!effective_rfm_enabled()) return;

    if (m_drfm_v[bank]) begin
      // ② DRFMpb 로 실행 — 이웃 행을 복원하지만 RAA 는 깎지 않는다
      m_drfm_v[bank] = 1'b0;
    end else begin
      // ③ 일반 RFMpb — RAAIMT 만큼 감소, 하한 0 (pull-in 금지)
      m_raa[bank] = (m_raa[bank] > cfg.raaimt) ? m_raa[bank] - cfg.raaimt : 0;
    end
  endfunction

  function void on_ref_pb(int bank);
    m_raa[bank] = (m_raa[bank] > cfg.raadec) ? m_raa[bank] - cfg.raadec : 0;
  endfunction

  // §6.3.2.5.3 — tRAASRF 이상 유지된 경우에만 0 이 된다.
  // 무조건 리셋으로 구현해도 긴 SR 만 도는 회귀는 통과한다.
  function void on_sref_exit(time held);
    if (held >= T_RAASRF) foreach (m_raa[b]) m_raa[b] = 0;
  endfunction

  // Table 40 — DEVICE_ID 두 비트와 MR8 레벨의 조합
  function bit effective_rfm_enabled();
    if (cfg.rfm_required)   return 1'b1;
    if (cfg.arfm_supported) return (mr8_rfm_level != 2'b00);   // ARFM override
    return 1'b0;
  endfunction

  function bit act_allowed(int bank); return (m_raa[bank] < cfg.raammt); endfunction
  function int get_raa   (int bank); return m_raa[bank];                endfunction
endclass
```

## 12. DBIac — 조합이 아니라 순차

전이 수 **4에서 직전 상태에 따라 갈립니다**(§6.2.1). 그리고 다음 비교의 기준은 원본이 아니라 **버스에 실린 반전 후 값**입니다.

```systemverilog
class dbi_model extends uvm_object;
  `uvm_object_utils(dbi_model)
  protected bit [7:0] m_prev_byte[8];
  protected bit       m_prev_dbi [8];
  protected bit       m_dpar_known;

  function void read_beat(input bit [7:0] raw[8], output bit [7:0] bus[8],
                                                  output bit       dbi[8]);
    foreach (raw[b]) begin
      int n = $countones(raw[b] ^ m_prev_byte[b]);
      unique case (1)
        (n <= 3) : dbi[b] = 1'b0;
        (n == 4) : dbi[b] = m_prev_dbi[b];   // ★ 히스테리시스 — 0 으로 쓰면
                                             //   진리표의 세 번째 행이 사라진다
        default  : dbi[b] = 1'b1;
      endcase
      bus[b]         = dbi[b] ? ~raw[b] : raw[b];
      m_prev_byte[b] = bus[b];               // ★ raw 가 아니라 bus
      m_prev_dbi [b] = dbi[b];
    end
  endfunction

  // §6.2.1.1 — 내부 DBIac 상태가 LOW 로 리셋되는 네 조건.
  // 그 밖의 이벤트에서는 유지된다.
  function void reset_dbi_state(dbi_reset_cause_e cause);
    // RESET_n · MRS · write-to-read 턴어라운드 · Self Refresh 종료
    foreach (m_prev_dbi[b]) begin m_prev_dbi[b] = 1'b0; m_prev_byte[b] = 8'h00; end
  endfunction

  // RDBI 비활성이어도 첫 READ 전 프리컨디셔닝은 수행된다 (§6.2.1.1)
  function void on_first_read_after_reset(bit rdbi_en);
    foreach (m_prev_byte[b]) m_prev_byte[b] = 8'h00;   // rdbi_en 과 무관
    // DPAR 은 DBI 계산에 포함되지 않고 프리컨디셔닝도 안 된다.
    // 초기 상태가 미정의이므로 "모름" 으로 두고 첫 비교에서 제외한다.
    m_dpar_known = 1'b0;
  endfunction
endclass
```

## 13. ECC — 실제 판정과 핀 값을 분리한다

`ERRTH` 필터 때문에 **모델이 아는 것과 핀에 보이는 것이 다릅니다**(Table 68). 이 분리가 없으면 필터를 표현할 수 없습니다.

```systemverilog
class ecc_array_model extends uvm_object;
  `uvm_object_utils(ecc_array_model)
  hbm4_cfg cfg;
  protected int m_cell_errors[bit [39:0]];
  protected int m_errcnt;

  function bit [255:0] on_read(bit [39:0] a, output sev_e actual);
    int n = m_cell_errors.exists(a) ? m_cell_errors[a] : 0;
    actual = (n == 0) ? SEV_NE : (n == 1) ? SEV_CES
           : (n <= SYMBOL_LIMIT) ? SEV_CEM : SEV_UE;
    if (actual != SEV_NE) m_errcnt++;
    // ★ m_cell_errors[a] 를 지우지 않는다.
    //   read 는 정정해서 반환하지만 배열에 되쓰지 않는다 (§6.9.2).
    return corrected_data(a);
  endfunction

  // ECS 만이 배열을 실제로 복원한다 (§6.9.4)
  function void on_ecs(bit [39:0] a);
    if (m_cell_errors.exists(a) && m_cell_errors[a] <= SYMBOL_LIMIT)
      m_cell_errors.delete(a);
  endfunction

  // Table 68 — ERRTH 이하의 CEs 는 NE 로 나간다. "NE ≠ 오류 없음".
  function sev_e to_pin(sev_e actual);
    if (actual == SEV_CES && m_errcnt <= cfg.errth) return SEV_NE;
    return actual;
  endfunction
endclass
```

```systemverilog
// Table 67 — SEV 는 버스트 후반부(4~7)에만 유효한 2비트 코드를 싣는다.
// 전 구간을 OR 로 샘플링하면 항상 NE 가 나오고,
// 오류 주입 테스트가 전부 "오류 없음" 으로 조용히 통과한다.
function automatic sev_e decode_sev(input bit [1:0] sev_by_ui[8]);
  unique case (sev_by_ui[4])
    2'b00 : return SEV_NE;
    2'b01 : return SEV_CES;
    2'b11 : return SEV_CEM;
    2'b10 : return SEV_UE;
  endcase
endfunction
```

## 14. 문맥 의존 신호 — `DERR` 3-way와 누적 불변식

```systemverilog
// DERR 은 세 가지 의미를 갖는다. monitor 가 MR 상태를 알아야 한다.
typedef enum {DERR_PARITY, DERR_PHASE, DERR_DUTY} derr_ctx_e;

function automatic derr_ctx_e derr_context(bit mr8_op3, bit mr6_op6);
  if (mr8_op3 && mr6_op6)
    `uvm_error("DERR_CTX", "WDQS2CK 와 DCM 동시 활성 — DERR 해석이 모호하다")
  if (mr6_op6) return DERR_DUTY;      // §6.11.3  — 듀티 측정 결과
  if (mr8_op3) return DERR_PHASE;     // §6.1.1   — 위상 검출기 판독
  return DERR_PARITY;                 // §6.4.2   — 데이터 패리티 오류
endfunction
```

```systemverilog
// §6.1 — preamble + postamble + 트레이닝 토글의 "합" 이 짝수여야 한다.
// 위반해도 마진이 있으면 데이터는 맞으므로 기능 검사로는 잡을 수 없다.
class wdqs_toggle_tracker extends uvm_component;
  `uvm_component_utils(wdqs_toggle_tracker)
  protected int unsigned m_toggles[2];        // DWORD0 / DWORD1

  function void count(int dword, int n); m_toggles[dword] += n; endfunction

  function void checkpoint(string where);
    foreach (m_toggles[d])
      if (m_toggles[d] % 2 != 0)
        `uvm_error("WDQS_PARITY", $sformatf(
          "%s: DWORD%0d 누적 토글 %0d 개로 홀수. 내부 WDQS/2 위상이 뒤집힌다 (§6.1)",
          where, d, m_toggles[d]))
  endfunction

  // ★ 리셋에서만 지운다. 시퀀스마다 초기화하면 각 시퀀스는 짝수인데
  //   합계는 홀수인 경우를 놓치고, 그것이 §6.1 이 금지하는 상황이다.
  function void on_reset(); foreach (m_toggles[d]) m_toggles[d] = 0; endfunction
endclass
```

---

# D. Stimulus

## 15. 문턱까지 밀어 올리기 — 랜덤으로 도달하지 못하는 곳

```systemverilog
// RAAMMT 도달. 랜덤 트래픽은 뱅크를 골고루 쓰므로 이 지점에 가지 못한다.
class seq_raa_climb extends uvm_sequence #(hbm4_cmd_item);
  `uvm_object_utils(seq_raa_climb)
  rand int unsigned target_bank;
  raa_model         model;

  virtual task body();
    while (model.get_raa(target_bank) < model.cfg.raammt) begin
      `uvm_do_with(req, { cmd == ACT;   bank == target_bank; })
      `uvm_do_with(req, { cmd == PREPB; bank == target_bank; })
    end
    check_act_blocked(target_bank);      // 여기서 ACTIVATE 는 금지되어야 한다
  endtask
endclass
```

```systemverilog
// tRAS(max) 근처. 행을 열고 그 뱅크를 건드리지 않은 채 방치한다.
class seq_tras_max_approach extends uvm_sequence #(hbm4_cmd_item);
  `uvm_object_utils(seq_tras_max_approach)
  virtual task body();
    `uvm_do_with(req, { cmd == ACT; bank == TARGET_BANK; })
    repeat (N) `uvm_do_with(req, { bank != TARGET_BANK; })   // 다른 뱅크로만
    wait_until_ratio(0.95);
    `uvm_do_with(req, { cmd == PREPB; bank == TARGET_BANK; })
  endtask
endclass
```

```systemverilog
// 뱅크 그룹 관계를 명시 축으로. 64뱅크에서 같은 그룹일 확률은 1/8 이라
// 순수 랜덤은 긴 쪽(tRRDL/tCCDL) 경로를 훨씬 덜 덮는다.
class seq_bank_group_walk extends uvm_sequence #(hbm4_cmd_item);
  `uvm_object_utils(seq_bank_group_walk)
  rand bit same_group;

  virtual task body();
    bit [5:0] b0 = $urandom_range(0, 63);
    bit [5:0] b1 = same_group ? {b0[5:3],  $urandom_range(0,7)}
                              : {~b0[5:3], $urandom_range(0,7)};
    `uvm_do_with(req, { cmd == ACT; bank == b0; })
    `uvm_do_with(req, { cmd == ACT; bank == b1; })
  endtask
endclass
```

## 16. 구성 자극 — 채널 비동기와 MR 이미지

```systemverilog
// §3.1 — 채널은 서로 동기일 필요가 없다. 세 관계를 모두 만든다.
// asynchronous bin 이 비면 CDC 경로는 한 번도 검증되지 않는다.
class ch_clk_cfg extends uvm_object;
  `uvm_object_utils(ch_clk_cfg)
  rand int unsigned period_ps[32];
  rand int unsigned phase_ps [32];
  rand clk_rel_e    relation;

  constraint c_relation {
    (relation == SYNC)  -> foreach (period_ps[i]) { period_ps[i] == period_ps[0];
                                                    phase_ps[i]  == 0; }
    (relation == PHASE) -> foreach (period_ps[i]) { period_ps[i] == period_ps[0];
                                                    phase_ps[i] inside {[0:period_ps[0]-1]}; }
    (relation == ASYNC) -> foreach (period_ps[i]) { period_ps[i] inside {[625:1250]}; }
  }
  // 채널 내 두 PC 는 CK 를 공유하므로 PC 별 항목은 두지 않는다 (§3.1)
endclass
```

```systemverilog
// MR 이미지 랜덤화. 두 가지를 반드시 제약해야 한다.
class mr_image_cfg extends uvm_object;
  `uvm_object_utils(mr_image_cfg)
  rand bit [7:0]    mr[20];
  rand int unsigned t_ck_ps;
  rand int unsigned channel;

  // ① RFU 비트는 0 (§5)
  constraint c_rfu { foreach (mr[i]) (mr[i] & RFU_MASK[i]) == 0; }

  // ② 타이밍 MR 은 RU{t/tCK} 이상. t_ck_ps 에 종속된다 —
  //    주파수를 흔들면서 MR 을 고정하면 자극이 스스로 규격을 벗어난다.
  constraint c_timing {
    mr[3] >= (T_WR_PS  + t_ck_ps - 1) / t_ck_ps;
    mr[4] >= (T_RAS_PS + t_ck_ps - 1) / t_ck_ps;
    mr[5] >= (T_RTP_PS + t_ck_ps - 1) / t_ck_ps;
  }

  // ③ ★ DA Port Lockout 은 랜덤화에서 제외한다 (§13.1.1).
  //    1 이 되면 전원 제거 전까지 풀리지 않아, 자극이 검증 환경 자신의
  //    관측 경로를 영구히 닫는다. 채널 0·4 에만 정의된 비트다.
  constraint c_no_accidental_lockout { mr[8][0] == 1'b0; }

  // ④ 경계값 편향 — 중간값은 결함을 드러내지 않는다
  constraint c_edge_bias {
    mr[2] dist { RL_MIN := 3, [RL_MIN+1 : RL_MAX-1] := 1, RL_MAX := 3 };
  }
endclass
```

## 17. 대비 시나리오 — "전후 차이"가 검사 지점인 것들

몇몇 성질은 **단일 관측으로는 확인할 수 없고**, 두 시점의 차이로만 드러납니다.

```systemverilog
// ① read 정정은 배열을 고치지 않는다 (§6.9.2) — ECS 전후 대비
task automatic check_no_writeback();
  inject_cell_error(A, .n_bits(1));
  repeat (4) read_and_expect(A, .sev(SEV_CES));   // 매번 같은 심각도
  trigger_ecs(A);
  read_and_expect(A, .sev(SEV_NE));               // ECS 후에는 NE
endtask

// ② soft vs hard lane repair (§6.7) — 전원 사이클 전후 대비
task automatic check_repair_persistence();
  apply_soft_lane_repair(L);  check_repaired(L, 1);
  power_cycle();              check_repaired(L, 0);   // 사라져야 한다
  apply_hard_lane_repair(L);  check_repaired(L, 1);
  power_cycle();              check_repaired(L, 1);   // 남아야 한다
endtask

// ③ 두 관측 경로의 독립성 (§6.9.4, §6.9.5) — 핀과 로그 대비
task automatic check_two_paths();
  inject_errors_below_errth();
  check_sev_pin(SEV_NE);            // 핀은 가려진다
  check_ecs_log_not_empty();        // 로그에는 남아 있다  ← 여기가 핵심
  inject_errors_above_errth();
  check_sev_pin(SEV_CES);           // 이제 핀에도 보인다
endtask

// ④ 재트레이닝 효과 (§10, [12장]) — 절차가 아니라 결과
task automatic check_retraining_effect();
  set_delay_profile(DELAY_SKEWED);   // 변동 계수 규모만큼 틀어 놓는다
  run_traffic(.expect_pass(0));      // 이 상태에서는 실패해도 정상
  run_full_training_sequence();
  run_traffic(.expect_pass(1));      // 회복되어야 한다
endtask

// ⑤ write parity 오염 추적 (§6.4.2) — 오염 전후 대비
task automatic check_poison_tracking();
  normal_write(A);            read_and_compare(A);      // 통과
  inject_write_parity_err(A); // DERR 보고, 데이터는 배열에 기록된다
  read_and_expect_skipped(A); // scoreboard 가 비교에서 제외해야 한다
  normal_write(A);            read_and_compare(A);      // 오염 해제 후 통과
endtask
```

:::caution[③이 이 부록에서 가장 중요한 시나리오다]
`ERRTH` 이하로 오류를 주입했을 때 **핀은 `NE`인데 로그에는 남아 있는 상태** — 이것이 두 관측 경로가 독립임을 증명하는 유일한 방법입니다.

이 시나리오가 없으면 `SEV`만 보는 환경과 로그까지 보는 환경이 **똑같이 통과**하고, 실리콘에서 "정정이 계속 일어나고 있었는데 아무도 몰랐다"가 됩니다.
:::

---

## 18. 패턴 → 장 대응

| 패턴 | 수단 | 규격 근거 | 장 |
|---|---|---|---|
| 1 구성 객체 · 런타임 config | 기반 | §1–3, §13.5.11 | [01](../01_landscape_organization/) · [11](../11_training_ieee1500/) |
| 2 라운딩 함수 | 기반 | §6.3.2.4 | [06](../06_row_commands/) |
| 3 반주기 커맨드 monitor | 기반 | §2, §6.3, Table 33 | [01](../01_landscape_organization/) · [06](../06_row_commands/) |
| 4 ACT 슬롯 + 짝 cover | SVA | Table 33 Note 9 | [06](../06_row_commands/) |
| 5 타이밍 3택 | SVA | Table 6, §10 Note 17 | [02](../02_addressing_bank_groups/) · [07](../07_column_commands/) |
| 6 시간 **상한** 검사 | SVA · 시각 기반 | §4.1 Table 7, §10 | [03](../03_init_reset_power/) · [12](../12_electrical_timing_package/) |
| 7 관대 구간 | SVA | §6.4.1 | [08](../08_parity/) |
| 8 문턱 대비 zone | Coverage | §6.3.2.5.3, Table 68 | [06](../06_row_commands/) · [09](../09_ecc_ecs_sev/) |
| 9 프로토콜 checker | 절차 | §4.4, §6.7, §6.9.4 | [03](../03_init_reset_power/) · [09](../09_ecc_ecs_sev/) · [10](../10_test_repair/) |
| 10 주소 왕복 검사 | Model | Table 4 Note 2·5·6·8 | [02](../02_addressing_bank_groups/) |
| 11 RAA 3분기 | Model | §6.3.2.5.3–5, Table 40 | [06](../06_row_commands/) |
| 12 DBIac 순차 | Model | §6.2.1, §6.2.1.1 | [05](../05_clocking_dbi/) |
| 13 ECC 판정/핀 분리 · SEV 디코드 | Model | §6.9.2, Table 67–68 | [09](../09_ecc_ecs_sev/) |
| 14 `DERR` 3-way · 토글 누적 | Model | §6.1, §6.4.2, §6.11.3 | [05](../05_clocking_dbi/) · [08](../08_parity/) · [11](../11_training_ieee1500/) |
| 15 문턱 도달 시퀀스 | Stimulus | §6.3.2.5.3, §10, Table 6 | [02](../02_addressing_bank_groups/) · [06](../06_row_commands/) · [12](../12_electrical_timing_package/) |
| 16 구성 자극 · MR 이미지 | Stimulus | §3.1, §5, §13.1.1 | [01](../01_landscape_organization/) · [04](../04_mode_registers/) · [11](../11_training_ieee1500/) |
| 17 대비 시나리오 | Stimulus | §6.4.2, §6.7, §6.9.2·4·5 | [08](../08_parity/) · [09](../09_ecc_ecs_sev/) · [10](../10_test_repair/) |

## 19. 이 부록이 다루지 않는 것

**디지털 회귀로 검증할 수 없는 항목**에는 패턴이 없습니다. [12장 §4](../12_electrical_timing_package/)의 종합표 ⑤를 참조하세요 — 전원 램프 부등식, lane repair 전류 제약, `ERRTH` 이하의 실제 정정, ESD, 변동 계수의 물리적 영향.

**환경 구조**(Agent 경계, VIP 채택, env 계층, V-Plan 운영, 회귀 전략)도 여기 없습니다. [`hbm_dv`](../../hbm_dv/)가 그것을 다룹니다.
