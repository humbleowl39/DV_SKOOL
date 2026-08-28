---
title: "Ch09 — Assertion · Protocol Checker"
---

:::tip[학습 목표]
이 챕터를 마치면:

- **Classify** 검증 규칙을 사이클 단위·트랜잭션 단위·장기 상태의 세 성격으로 분류하고 각각에 맞는 수단을 배정할 수 있다.
- **Implement** CA 공유·핸드셰이크·설정 의존 타이밍 규칙을 SVA로 구현할 수 있다.
- **Design** Scoreboard가 주소 디코드를 독립 재현하여 DUT의 해석을 검증하도록 설계할 수 있다.
- **Diagnose** vacuous assertion을 식별하고 cover property로 방지할 수 있다.
:::

:::note[사전 지식]
- [Ch08 — Test Case & 시나리오](../08_testcase_scenarios/): *"시나리오는 자극만, 판정은 하지 않는다"* — 그 판정을 여기서 만듭니다
- [Ch03 — Custom UVM Agent A-to-Z](../03_custom_uvm_agent/): monitor의 미해결 테이블, 마무리 문제의 "두 경로 대조"
- [부록 A — 스펙](../appendix_a_hbm_ch_ctrl_spec/): 규칙 R1~R20이 이 챕터의 원본입니다
:::

---

## 1. Why care? — 규칙 20개를 assertion 20개로 옮기면 될까

Ch08은 계속 미뤘습니다. *"시나리오는 자극만 만들고 판정하지 않는다. 판정은 Ch09에서."*

이제 그 판정을 만듭니다. 스펙에 규칙이 R1부터 R20까지 있으니, 하나씩 assertion으로 옮기면 될 것 같습니다.

R1(valid 유지)부터 시작합니다. 쉽습니다. R2(payload 안정)도 됩니다. R3(CA 공유)도 한 줄로 나옵니다.

그런데 R6에서 막힙니다.

> *"같은 뱅크에서 `ACT` → `RD`/`WR` 사이 간격 ≥ **`MR_TIMING.tRCD_CYC`**"*

기준값이 **런타임에 바뀌는 설정값**입니다. 게다가 Ch08에서 그 값을 바꿔 가며 돌리는 시나리오까지 만들었습니다. assertion 안에 `8`이라고 쓸 수는 없습니다.

R9에서 또 막힙니다.

> *"`cci_rsp_id`는 아직 완료되지 않은 요청의 `cci_req_id` **중 하나**여야 한다"*

"집합의 원소인가"를 묻고 있습니다. 그 집합은 시간에 따라 변하고 크기도 변합니다. SVA로 표현할 수는 있지만 **자연스럽지 않습니다.**

R11에서는 아예 성격이 다릅니다.

> *"응답은 요청과 순서가 다를 수 있다. 단 같은 `id`의 beat들은 순서를 지킨다"*

**허용**을 규정하는 문장입니다. 무엇을 assert해야 할지조차 분명하지 않습니다.

**규칙과 assertion은 1:1이 아닙니다.** 규칙의 성격에 따라 적합한 수단이 다르고, 그 배정을 먼저 해야 합니다. 이 챕터는 그 분류에서 시작합니다.

---

## 2. 직관 — 규칙의 성격이 수단을 정한다

### 순진한 시도 1 — 규칙 20개를 SVA 20개로

**어디서 막히나?** 위에서 본 대로입니다. 일부 규칙은 SVA로 표현하기 어렵거나, 표현할 수는 있어도 **읽기 어렵고 디버깅이 힘든 형태**가 됩니다. 복잡한 SVA는 실패했을 때 무엇이 위반됐는지 파악하는 데 시간이 걸리고, 그러면 팀이 그 assertion을 신뢰하지 않게 됩니다.

### 순진한 시도 2 — 전부 절차적 checker로

Scoreboard나 monitor 안에서 코드로 검사합니다. 자유롭게 쓸 수 있고 집합·테이블 관리도 쉽습니다.

**어디서 막히나?** **매 사이클 감시가 필요한 규칙**을 놓칩니다. Scoreboard는 트랜잭션이 완성된 시점에 동작하므로, 그 사이에 일어난 사이클 단위 위반(핸드셰이크, CA 공유)은 관측 범위 밖입니다.

그리고 **위반 시점 추적**이 어렵습니다. SVA는 위반된 바로 그 사이클에서 신고하지만, 절차적 검사는 나중에 결과를 보고 역추적해야 합니다.

### 일반화 — 세 가지 성격, 세 가지 수단

> **규칙을 세 성격으로 분류하고 수단을 배정한다.**

| 성격 | 특징 | 수단 |
|---|---|---|
| **(가) 사이클 단위 시간 관계** | "A 다음 N 사이클 안에 B" / "동시에 X이면 Y" | **SVA** |
| **(나) 트랜잭션 단위 대응** | "이 요청의 결과가 이 값이어야" | **Scoreboard** |
| **(다) 장기 상태·집합 관계** | "미해결 집합의 원소인가" / "순서가 허용 범위인가" | **절차적 checker** |

`hbm_ch_ctrl`의 규칙을 실제로 배정하면:

| 규칙 | 내용 | 성격 | 수단 |
|---|---|---|---|
| R1·R2 | 핸드셰이크 유지·안정 | (가) | **SVA** |
| **R3** | **CA 공유 — `row_pc == col_pc`** | **(가)** | **SVA** ⭐ |
| R4·R5 | 뱅크 상태 전이 (IDLE↔ACTIVE) | (가) + 상태 추적 | **SVA + 보조 로직** |
| **R6·R7·R8** | **타이밍 — 설정값 의존** | **(가) + 동적 기준** | **SVA + 보조 카운터** ⭐ |
| R9 | `rsp_id`가 미해결 중 하나 | (다) | 절차적 |
| R10 | beat 수 = `len`+1 | (나) | Scoreboard |
| R11 | OoO 허용, 같은 id는 순서 | (다) | 절차적 |
| R12~R16 | 오류 응답 값 | (나) | Scoreboard |
| **R18** | **테스트 모드 중 커맨드 정지** | **(가)** | **SVA** |
| R17·R19·R20 | 모드 전이 절차 | (다) | 절차적 |
| — | **주소 디코드 정합** | (나) | **Scoreboard 독립 재현** ⭐ |

⭐ 표시가 이 챕터에서 코드로 다룰 항목입니다.

---

## 3. 작은 예 — 세 수단을 실제로 구현하기

:::note[Bind로 붙입니다]
Assertion은 DUT RTL을 수정하지 않고 **`bind`로 결합**합니다. 검증이 설계 코드를 건드리지 않는 것은 기본 원칙이며, RTL 변경 없이 checker를 켜고 끌 수 있다는 실용적 이점도 있습니다.
:::

### 3.1 SVA — 핸드셰이크와 CA 공유

```systemverilog
module hbm_ch_ctrl_sva #(
  parameter int NUM_BANK = 16
) (
  input logic clk,
  input logic rst_n,
  // CCI
  input logic req_valid, req_ready,
  input logic [1:0] req_op,
  input logic req_pc,
  // DCMD
  input logic row_cmd_valid, col_cmd_valid,
  input logic [1:0] row_cmd, col_cmd,
  input logic row_pc, col_pc,
  input logic [3:0] row_bank, col_bank,
  // 테스트 모드
  input logic test_mode_ack,
  // 설정값 — config로부터 주입 (아래 3.2 참고)
  input int unsigned cfg_trcd_cyc, cfg_trp_cyc, cfg_tras_cyc
);

  import uvm_pkg::*;
  `include "uvm_macros.svh"

  // ---- R1: valid는 ready까지 유지 ----
  property p_req_valid_stable;
    @(posedge clk) disable iff (!rst_n)
      (req_valid && !req_ready) |=> req_valid;
  endproperty

  a_req_valid_stable: assert property (p_req_valid_stable)
    else `uvm_error("SVA_R1", "req_valid가 ready 이전에 해제되었습니다 (스펙 R1)")

  // ---- R2: 대기 중 payload 안정 ----
  property p_req_payload_stable;
    @(posedge clk) disable iff (!rst_n)
      (req_valid && !req_ready) |=> $stable({req_op, req_pc});
  endproperty

  a_req_payload_stable: assert property (p_req_payload_stable)
    else `uvm_error("SVA_R2", "req 대기 중 payload가 변경되었습니다 (스펙 R2)")

  // ---- R3: CA 공유 — 이 IP의 핵심 규칙 ----
  property p_ca_share;
    @(posedge clk) disable iff (!rst_n)
      (row_cmd_valid && col_cmd_valid) |-> (row_pc == col_pc);
  endproperty

  a_ca_share: assert property (p_ca_share)
    else `uvm_error("SVA_R3",
           $sformatf("서로 다른 pseudo-channel의 커맨드가 같은 사이클에 발행되었습니다 — row_pc=%0d col_pc=%0d (스펙 R3)",
                     row_pc, col_pc))

  // ★ 이 규칙이 실제로 자극되었는지 확인 — vacuity 방지
  c_ca_share_exercised: cover property (
    @(posedge clk) disable iff (!rst_n) (row_cmd_valid && col_cmd_valid)
  );

  // ---- R18: 테스트 모드 중 커맨드 정지 ----
  property p_test_mode_quiet;
    @(posedge clk) disable iff (!rst_n)
      test_mode_ack |-> (!row_cmd_valid && !col_cmd_valid);
  endproperty

  a_test_mode_quiet: assert property (p_test_mode_quiet)
    else `uvm_error("SVA_R18", "테스트 모드 중 DRAM 커맨드가 발행되었습니다 (스펙 R18)")

  c_test_mode_entered: cover property (
    @(posedge clk) disable iff (!rst_n) $rose(test_mode_ack)
  );
```

**`a_ca_share` 바로 아래의 `c_ca_share_exercised`가 중요합니다.**

R3의 assertion은 `row_cmd_valid && col_cmd_valid`가 참일 때만 무언가를 확인합니다. 만약 회귀 내내 **두 커맨드가 한 번도 동시에 발행되지 않았다면**, 이 assertion은 단 한 번도 실질적으로 평가되지 않고 **항상 통과**합니다.

이것이 **vacuous assertion**이며, 이 코스가 반복해 온 "조용한 통과"의 assertion 판입니다. cover property가 없으면 **assertion이 일하고 있는지 놀고 있는지 구분할 수 없습니다.**

> **규칙: 모든 assertion에는 그 전제(antecedent)가 실제로 발생했는지 확인하는 cover property를 짝지어 둔다.**

### 3.2 설정 의존 타이밍 — 보조 로직 + SVA

R6~R8의 기준값은 런타임 설정값입니다. 해법은 **경과 사이클을 보조 로직으로 세고, assertion은 그 카운터를 보는 것**입니다.

:::note[아래 코드는 §3.1 모듈의 계속입니다]
지면상 나눴을 뿐 `hbm_ch_ctrl_sva` **하나의 모듈**이며, 아래 블록 끝의 `endmodule`이 §3.1에서 연 `module`을 닫습니다.
:::

```systemverilog
  // ---- 뱅크별 상태·경과 카운터 (보조 로직) ----
  typedef enum logic { BANK_IDLE, BANK_ACTIVE } bank_state_e;

  bank_state_e bank_state [NUM_BANK*2];   // pc 2개 × 뱅크
  int unsigned since_act  [NUM_BANK*2];
  int unsigned since_pre  [NUM_BANK*2];

  function automatic int idx(logic pc, logic [3:0] bank);
    return int'(pc) * NUM_BANK + int'(bank);
  endfunction

  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      for (int i = 0; i < NUM_BANK*2; i++) begin
        bank_state[i] <= BANK_IDLE;
        since_act[i]  <= '0;
        since_pre[i]  <= '0;
      end
    end
    else begin
      // 경과 카운터는 매 사이클 증가 (포화)
      for (int i = 0; i < NUM_BANK*2; i++) begin
        if (since_act[i] < 32'hFFFF) since_act[i] <= since_act[i] + 1;
        if (since_pre[i] < 32'hFFFF) since_pre[i] <= since_pre[i] + 1;
      end

      if (row_cmd_valid) begin
        int i = idx(row_pc, row_bank);
        case (row_cmd)
          2'd1: begin bank_state[i] <= BANK_ACTIVE; since_act[i] <= '0; end  // ACT
          2'd2: begin bank_state[i] <= BANK_IDLE;   since_pre[i] <= '0; end  // PRE
          default: ;
        endcase
      end
    end
  end

  // ---- R4: IDLE 뱅크에 RD/WR 금지 ----
  property p_col_needs_active;
    @(posedge clk) disable iff (!rst_n)
      (col_cmd_valid && col_cmd inside {2'd1, 2'd2})
        |-> (bank_state[idx(col_pc, col_bank)] == BANK_ACTIVE);
  endproperty

  a_col_needs_active: assert property (p_col_needs_active)
    else `uvm_error("SVA_R4",
           $sformatf("IDLE 뱅크에 column 커맨드 발행 — pc=%0d bank=%0d (스펙 R4)",
                     col_pc, col_bank))

  // ---- R6: ACT → RD/WR 간격 ≥ tRCD_CYC (설정 의존) ----
  property p_trcd;
    @(posedge clk) disable iff (!rst_n)
      (col_cmd_valid && col_cmd inside {2'd1, 2'd2})
        |-> (since_act[idx(col_pc, col_bank)] >= cfg_trcd_cyc);
  endproperty

  a_trcd: assert property (p_trcd)
    else `uvm_error("SVA_R6",
           $sformatf("tRCD 위반 — pc=%0d bank=%0d 경과=%0d 기준=%0d (스펙 R6)",
                     col_pc, col_bank,
                     since_act[idx(col_pc, col_bank)], cfg_trcd_cyc))

  // 설정값이 여러 개 사용되었는지 — Ch08의 설정 효과 시나리오와 짝
  c_trcd_values: cover property (
    @(posedge clk) disable iff (!rst_n)
      (col_cmd_valid && col_cmd inside {2'd1, 2'd2})
  );

endmodule
```

```systemverilog
// DUT RTL을 수정하지 않고 결합
bind hbm_ch_ctrl hbm_ch_ctrl_sva #(.NUM_BANK(16)) u_sva (
  .clk           (clk),
  .rst_n         (rst_n),
  .req_valid     (cci_req_valid),
  // ... 신호 연결 ...
  .cfg_trcd_cyc  (u_csr.mr_timing_trcd),   // 현재 설정값을 그대로 참조
  .cfg_trp_cyc   (u_csr.mr_timing_trp),
  .cfg_tras_cyc  (u_csr.mr_timing_tras)
);
```

**설정값을 어디서 가져오는가**가 판단 지점입니다. 두 가지 방법이 있습니다.

| 방법 | 장점 | 위험 |
|---|---|---|
| **DUT의 CSR 레지스터를 직접 참조** | 항상 현재 값 | DUT가 설정을 잘못 저장하면 **assertion도 함께 틀린다** |
| **테스트벤치가 기대하는 값을 주입** | DUT와 독립 | 설정 변경 시점 동기화 필요 |

**권장은 후자입니다.** DUT의 값을 그대로 쓰면, `SCHED_MODE`나 타이밍 값을 DUT가 무시하거나 잘못 저장해도 assertion이 **DUT의 오해를 그대로 따라가** 위반을 잡지 못합니다. Ch03에서 monitor가 driver의 item을 재사용하면 안 됐던 것과 **같은 구조의 함정**입니다.

*(위 `bind` 예시는 이해를 돕기 위해 CSR 참조 방식을 보였습니다. 실제로는 테스트벤치의 기대값을 주입하고, 두 값이 일치하는지를 별도 항목으로 확인하는 편이 안전합니다.)*

### 3.3 Scoreboard — 주소 디코드 독립 재현 (#15)

선행 코스 Ch04가 제기한 문제입니다.

> write-then-read는 주소 X가 잘못된 곳으로 가도 **읽을 때 같은 잘못된 곳**으로 가므로 통과한다.

해법은 **테스트벤치가 목적지를 스스로 계산해 DUT의 실제 접근과 대조**하는 것입니다. Ch03 마무리 문제에서 *"두 경로를 모두 유지해 대조"* 라고 예고한 것의 구현입니다.

```systemverilog
class hbm_ch_ctrl_scoreboard #(parameter int DATA_W=32, ADDR_W=34, ID_W=4)
  extends uvm_scoreboard;

  `uvm_component_param_utils(hbm_ch_ctrl_scoreboard#(DATA_W, ADDR_W, ID_W))

  typedef cci_item#(DATA_W, ADDR_W, ID_W) cci_item_t;

  `uvm_analysis_imp_decl(_cci)
  `uvm_analysis_imp_decl(_dcmd)

  uvm_analysis_imp_cci  #(cci_item_t,  hbm_ch_ctrl_scoreboard#(DATA_W,ADDR_W,ID_W)) cci_imp;
  uvm_analysis_imp_dcmd #(dcmd_item,   hbm_ch_ctrl_scoreboard#(DATA_W,ADDR_W,ID_W)) dcmd_imp;

  hbm_dv_cfg cfg;

  // 기대 목적지 — id로 보관
  typedef struct {
    bit          pc;
    bit [3:0]    bank;
    bit [15:0]   row;
    bit [9:0]    col;
  } dest_t;
  protected dest_t expected_dest [bit [ID_W-1:0]];

  function new(string name, uvm_component parent);
    super.new(name, parent);
    cci_imp  = new("cci_imp",  this);
    dcmd_imp = new("dcmd_imp", this);
  endfunction

  // ---- 우리가 직접 계산한다. DUT의 계산을 쓰지 않는다 ----
  protected function dest_t decode_addr(bit [ADDR_W-1:0] addr);
    dest_t d;
    // 환경 설정(cfg)을 근거로 한 독립 디코드
    d.col  = addr[9:0];
    d.bank = addr[13:10];
    d.pc   = addr[14];
    d.row  = addr[30:15];
    return d;
  endfunction

  // CCI 요청 관측 → 기대 목적지 계산
  function void write_cci(cci_item_t t);
    if (t.op inside {CCI_READ, CCI_WRITE})
      expected_dest[t.id] = decode_addr(t.addr);
    check_error_response(t);
  endfunction

  // DCMD 관측 → 실제 목적지와 대조
  function void write_dcmd(dcmd_item d);
    dest_t exp;
    if (!expected_dest.exists(d.id)) begin
      `uvm_error("SB_DEC",
                 $sformatf("기대 목적지가 없는 DCMD 접근 — id=%0d", d.id))
      return;
    end
    exp = expected_dest[d.id];

    if (d.pc !== exp.pc || d.bank !== exp.bank || d.row !== exp.row) begin
      `uvm_error("SB_DEC",
        $sformatf("주소 디코드 불일치 — id=%0d | 기대 pc=%0d bank=%0d row=0x%0h | 실제 pc=%0d bank=%0d row=0x%0h",
                  d.id, exp.pc, exp.bank, exp.row, d.pc, d.bank, d.row))
    end
  endfunction

  // R12~R16 — 오류 응답 판정
  protected function void check_error_response(cci_item_t t);
    bit expect_par_err = t.inject_req_par_err && cfg_par_chk_enabled();

    if (expect_par_err && t.err != CCI_PAR_ERR)
      `uvm_error("SB_ERR",
        $sformatf("패리티 오류를 주입했으나 응답이 %s입니다 (스펙 R12)", t.err.name()))

    if (!expect_par_err && t.err == CCI_PAR_ERR)
      `uvm_error("SB_ERR", "오류를 주입하지 않았는데 PARITY_ERR가 반환되었습니다")
  endfunction
endclass
```

**핵심은 `decode_addr`이 DUT와 독립적으로 계산한다는 점**입니다. DUT가 `pc` 비트를 잘못 잡으면 `expected_dest`와 실제 DCMD 접근이 어긋나 즉시 드러납니다. write-then-read로는 원리적으로 잡히지 않던 결함입니다.

:::note[🤔 잠깐 — 수단을 배정하세요]
다음 세 규칙에 대해 (가) SVA / (나) Scoreboard / (다) 절차적 checker 중 무엇을 쓸지 정하고, 그 이유를 말하세요.

- **(A)** R10 — *"응답 beat 수는 `cci_req_len + 1`과 같고, 마지막 beat에서만 `rsp_last`가 1"*
- **(B)** R20 — *"`TEST_MODE_REQ`를 0으로 쓰면 `TEST_MODE_ACK`가 0이 되고 mission mode로 복귀"*
- **(C)** R11 — *"응답은 순서가 다를 수 있다. 단 같은 `id`의 beat들은 순서를 지킨다"*

<details>
<summary>정답 / 해설</summary>

**(A) R10 → (나) Scoreboard** — 다만 일부는 SVA로 보강

beat 수를 세려면 **트랜잭션 전체가 끝나야** 판정할 수 있으므로 Scoreboard가 자연스럽습니다. monitor가 이미 미해결 테이블을 유지하며 beat를 모으고 있으므로(Ch03), 완성 시점에 `rdata.size() == len+1`을 확인하면 됩니다.

**SVA로 보강할 부분**: *"마지막 beat에서만 `rsp_last`가 1"* 은 사이클 단위 성질이므로, `rsp_last`가 1인데 그 뒤에 같은 id의 beat가 더 오는 상황을 SVA로 잡을 수 있습니다. **한 규칙이 두 수단에 걸치는 경우**입니다.

**(B) R20 → (가) SVA로 상당 부분 가능**

*"REQ를 0으로 쓰면 ACK가 0이 된다"* 는 **신호 간 시간 관계**입니다.

```
$fell(test_mode_req) |-> ##[1:N] $fell(test_mode_ack)
```

형태로 표현할 수 있습니다. 다만 *"mission mode로 복귀"* 가 무엇을 의미하는지 — 복귀 후 요청이 정상 처리되는가 — 는 **(다) 절차적**으로 확인해야 합니다. R17~R20 전체를 하나의 전이 시퀀스로 보고 절차적 checker가 상태를 추적하는 편이 낫습니다.

**(C) R11 → (다) 절차적 checker**

R11은 **허용을 규정**합니다 — "순서가 달라도 된다". 허용은 assert할 것이 없습니다.

실제로 검사해야 할 것은 그 안에 숨은 **제약**입니다.
1. 같은 `id`의 beat들이 순서를 지키는가
2. 응답이 미해결 요청에 대응하는가 (R9)

둘 다 **집합·테이블 관리**가 필요하므로 절차적이 자연스럽습니다. monitor의 미해결 테이블(Ch03)에 검사를 얹으면 됩니다.

**공통 원리**: 규칙 문장에서 *"~해야 한다"*(제약)와 *"~할 수 있다"*(허용)를 구분하세요. **허용은 검사 대상이 아니며, 그 안에 숨은 제약을 찾아야 합니다.**

</details>
:::

---

## 4. 일반화 — 두 극단의 대가

### 대안 A — 전부 절차적 checker로

**왜 부족한가**: 사이클 단위 규칙을 놓치고, 위반 시점 추적이 어렵습니다. 그리고 검사 코드가 monitor·scoreboard 안에 섞여 **규칙이 어디 있는지 찾기 어려워집니다.**

SVA의 실질적 이점 하나를 짚으면, **위반된 바로 그 사이클에서 신고**하므로 파형에서 원인 지점이 즉시 보입니다. 절차적 검사는 결과를 보고 역추적해야 합니다.

### 대안 B — 전부 SVA로

**왜 부족한가**: 표현이 어색해지는 규칙이 있고(R9·R11), 복잡한 SVA는 **디버깅 비용이 큽니다.** 실패했을 때 어느 조건이 깨졌는지 파악하기 어려우면, 팀은 그 assertion을 끄거나 무시하기 시작합니다. **읽히지 않는 checker는 없는 것과 같습니다.**

**판단 기준**

| 물어볼 것 | 답이 "예"면 |
|---|---|
| 매 사이클 감시가 필요한가 | SVA |
| 트랜잭션이 끝나야 판정 가능한가 | Scoreboard |
| 집합·테이블 관리가 필요한가 | 절차적 |
| SVA로 쓰면 3줄을 넘고 읽기 어려운가 | 절차적을 검토 |

---

## 5. 디테일 — Checker 운영에서 실제로 벌어지는 일

### 실패 1 — Vacuous assertion

전제(antecedent)가 회귀 내내 한 번도 참이 되지 않아 assertion이 실질적으로 평가되지 않는 경우입니다.

**관측되는 증상**: **없습니다.** Assertion은 통과로 집계되고, 리포트에는 "0 failures"가 찍힙니다. R3처럼 특정 동시성 조건이 필요한 규칙일수록 위험합니다 — 시나리오가 그 조건을 만들지 못하면 assertion은 **놀고 있으면서 일하는 것처럼 보입니다.**

**처방**: **모든 assertion에 전제 발생을 확인하는 cover property를 짝짓습니다.** 그리고 회귀 리포트에서 **cover가 채워졌는지**를 assertion 통과 여부와 함께 봅니다. 채워지지 않은 cover는 *"이 규칙은 아직 검증되지 않았다"* 는 뜻입니다.

이것은 Ch07 V-Plan의 항목 상태와도 이어집니다 — cover가 비어 있으면 그 행은 "통과"가 아니라 **"미측정"** 입니다.

### 실패 2 — Assertion이 설정 변화를 따라가지 못한다

타이밍 기준값을 assertion 안에 상수로 써 둔 경우입니다.

**관측되는 증상**: Ch08의 설정 효과 시나리오(`tRCD`를 8 → 16으로 변경)를 돌리면 **오탐이 쏟아지거나**(기준을 8로 고정해 뒀는데 16으로 동작), **위반을 놓칩니다**(기준을 16으로 고정해 뒀는데 8 구간에서 위반). 어느 쪽이든 assertion을 신뢰할 수 없게 됩니다.

**처방**: 설정 의존 규칙은 **보조 로직 + 동적 기준**으로 구현합니다(§3.2). 그리고 기준값의 출처는 **DUT의 레지스터가 아니라 테스트벤치의 기대값**이어야 합니다 — DUT가 설정을 잘못 저장하면 assertion도 함께 틀리기 때문입니다.

### 실패 3 — Scoreboard가 DUT의 해석을 신뢰한다

DUT가 계산한 목적지 정보를 그대로 받아 비교하거나, monitor가 재구성하지 않고 driver의 값을 쓰는 경우입니다.

**관측되는 증상**: 선행 코스 Ch04에서 본 그대로 — **아무 증상이 없습니다.** 주소 디코드가 틀려도 쓰기와 읽기가 같은 잘못된 곳으로 가므로 데이터는 일치합니다.

**처방**: Scoreboard가 **독립적으로 디코드를 재현**하고 DCMD 관측과 대조합니다(§3.3). 그리고 그 디코드 로직의 근거는 **스펙과 환경 설정**이지 DUT RTL이 아닙니다.

---

## 6. 흔한 오해

| 오해 | 실제 |
|---|---|
| "규칙 하나에 assertion 하나" | 성격에 따라 수단이 다르고, **한 규칙이 두 수단에 걸치기도** 합니다 |
| "Assertion이 통과하면 그 규칙은 검증됐다" | **Vacuous일 수 있습니다.** cover property로 전제 발생을 확인해야 합니다 |
| "SVA로 쓸 수 있으면 SVA가 낫다" | 읽기 어려운 SVA는 **무시되기 시작합니다.** 3줄을 넘으면 절차적을 검토합니다 |
| "타이밍 기준값은 상수로 두면 된다" | 설정이 바뀌면 오탐 또는 미검출입니다. **동적 기준**이어야 합니다 |
| "기준값은 DUT의 CSR에서 읽으면 정확" | DUT가 잘못 저장하면 **assertion도 함께 틀립니다.** TB 기대값을 씁니다 |
| "허용 규정도 assert해야 한다" | 허용(R11)은 검사 대상이 아닙니다. **그 안에 숨은 제약**을 찾습니다 |
| "Assertion은 RTL에 넣는 게 편하다" | **`bind`로 붙입니다.** 검증이 설계 코드를 건드리지 않습니다 |

---

## 🔧 이 문제를 이렇게 푼다

> **닫는 항목: #3 — 커맨드 타이밍·순서 규칙 상시 감시 / #13 — 공유 CA 버스의 경합·중재 규칙 / #14 — row/column 병렬 흐름 간 순서 규칙 / #15 — Scoreboard가 주소 디코드를 독립 재현**

### 1단계 — 규칙을 수단에 배정

| 판정 질문 | 수단 |
|---|---|
| 매 사이클 감시가 필요한가 | **SVA** |
| 트랜잭션 완성 후 판정 가능한가 | **Scoreboard** |
| 집합·테이블·장기 상태가 필요한가 | **절차적 checker** |
| SVA가 3줄을 넘고 읽기 어려운가 | 절차적로 이동 검토 |

규칙 문장에서 **제약("~해야 한다")과 허용("~할 수 있다")** 을 구분합니다. 허용은 검사 대상이 아니며 그 안의 제약을 찾습니다.

### 2단계 — #3·#13·#14: SVA 구현

- **#13(CA 공유)**: `(row_cmd_valid && col_cmd_valid) |-> (row_pc == col_pc)` — 이 IP의 핵심 규칙
- **#14(row/col 순서)**: 뱅크 상태를 보조 로직으로 추적하고, column 커맨드가 ACTIVE 뱅크를 향하는지 확인 (R4·R5)
- **#3(타이밍)**: 경과 카운터 + **동적 기준값**. 기준은 TB 기대값에서 (DUT CSR 아님)
- 전부 **`bind`로 결합** — RTL 무수정

### 3단계 — #15: Scoreboard 독립 재현

- 주소 → (pc, bank, row, col) 디코드를 **스펙과 환경 설정 근거로 직접 구현**
- CCI 요청에서 **기대 목적지**를 계산해 id로 보관
- DCMD 관측과 **대조**하여 불일치를 보고
- DUT가 계산한 값을 절대 신뢰하지 않음

### 4단계 — Vacuity 방지 (모든 항목 공통)

- **모든 assertion에 전제 cover property를 짝짓는다**
- 회귀 리포트에서 **assertion 통과 + cover 충족**을 함께 확인
- **cover가 비어 있으면 V-Plan 상태는 "통과"가 아니라 "미측정"** (Ch07)

### Assertion 작성 규칙

| 규칙 | 이유 |
|---|---|
| `disable iff (!rst_n)` 필수 | 리셋 중 오탐 방지 |
| 메시지에 **컨텍스트 포함** (pc·bank·실제값·기준값) | 디버깅 시간 단축 |
| `uvm_error` 사용 (`$display`·`$finish` 금지) | 리포팅 일관성 |
| `bind`로 결합 | RTL 무수정 |
| 설정 의존 규칙은 **보조 로직 + 동적 기준** | 설정 변경 대응 |
| **cover property 짝** | vacuity 방지 |

---

## 7. 핵심 정리

- **규칙과 assertion은 1:1이 아니다.** 성격에 따라 수단이 정해진다 — 사이클 단위는 SVA, 트랜잭션은 Scoreboard, 집합·장기 상태는 절차적
- 규칙 문장에서 **제약과 허용을 구분**한다. 허용(R11)은 검사 대상이 아니며 그 안의 제약을 찾는다
- **Vacuous assertion은 assertion 판의 "조용한 통과"** 다. 전제가 한 번도 참이 안 되면 항상 통과한다
- **모든 assertion에 cover property를 짝짓는다.** cover가 비면 그 규칙은 **미측정**이다
- 설정 의존 규칙은 **보조 로직 + 동적 기준**으로 구현하고, 기준값은 **TB 기대값**을 쓴다 (DUT CSR 아님)
- **Scoreboard는 주소 디코드를 독립 재현**한다. DUT의 해석을 신뢰하면 write-then-read가 잡지 못하는 결함이 그대로 남는다
- Assertion은 **`bind`로 붙인다.** 검증이 설계 코드를 건드리지 않는다
- **읽히지 않는 checker는 없는 것과 같다.** SVA가 복잡해지면 절차적을 검토한다

:::note[🤔 마무리 자가 점검]
회귀 리포트가 이렇게 나왔습니다.

> ```
> Assertions:  a_req_valid_stable  PASS (12,483 hits)
>              a_ca_share          PASS (0 hits)
>              a_trcd              PASS (8,201 hits)
>              a_test_mode_quiet   PASS (0 hits)
> Cover:       c_ca_share_exercised     0%
>              c_test_mode_entered      0%
>              c_trcd_values          100%
> ```

(a) 이 리포트에서 **실제로 검증된 규칙**은 무엇입니까? (b) 문제의 원인은 어디에 있습니까? (c) 무엇을 해야 합니까?

<details>
<summary>정답 / 해설</summary>

**(a) 실제로 검증된 것은 R1(핸드셰이크)과 R6(tRCD) 두 가지뿐입니다.**

`a_ca_share`와 `a_test_mode_quiet`는 **PASS로 표시되지만 hits가 0**입니다. 전제가 한 번도 참이 되지 않았다는 뜻이며, cover도 0%로 그것을 확인해 줍니다. **R3와 R18은 미검증입니다.**

cover property가 없었다면 이 리포트는 *"assertion 4개 전부 통과"* 로 읽혔을 것입니다. **cover가 vacuity를 드러낸 것**이 이 리포트의 핵심입니다.

**(b) 원인은 assertion이 아니라 시나리오에 있습니다.**

- `c_ca_share_exercised` 0% → **row/col 커맨드가 동시에 발행되는 상황이 만들어지지 않았습니다.** 원인 후보: 미해결 요청이 충분히 쌓이지 않음(driver가 blocking?), 트래픽이 한 pseudo-channel에 몰림, 뱅크 다양성 부족
- `c_test_mode_entered` 0% → **테스트 모드 진입 시나리오를 돌리지 않았습니다.** Ch08에서 예고한 "뒤로 밀리는" 시나리오가 실제로 밀린 것입니다

Assertion은 정상입니다. 자극이 없었을 뿐입니다.

**(c) 해야 할 일**

1. **V-Plan 상태를 정정한다** — R3·R18 행을 "통과"에서 **"미측정"** 으로 되돌립니다. 이것이 가장 먼저입니다. 잘못된 상태가 보고에 남으면 나머지 판단이 전부 어긋납니다
2. **시나리오를 만든다** — 동시 요청이 쌓이는 부하 시나리오(Ch08의 `perf_load_seq`가 부분적으로 기여), 두 pseudo-channel 분산 트래픽, 테스트 모드 진입·복귀 시나리오
3. **cover를 회귀 게이트에 넣는다** — assertion 통과만으로 게이트를 통과시키지 않고, **핵심 규칙의 cover 충족을 조건으로** 겁니다. 그러면 이런 상황이 다음부터는 자동으로 드러납니다
4. **`c_trcd_values` 100%도 다시 본다** — 이 cover는 "column 커맨드가 발행됨"만 확인합니다. Ch08의 설정 효과 시나리오처럼 **여러 tRCD 값에서** 발행됐는지는 이 cover로 알 수 없습니다. cover의 정의 자체가 충분한지 점검이 필요합니다

**교훈**: **Assertion을 잘 쓰는 것과 그것이 일하게 만드는 것은 다른 문제입니다.** 전자는 이 챕터, 후자는 시나리오(Ch08)와 커버리지(Ch10)의 몫이며, 셋이 맞물려야 규칙이 실제로 검증됩니다.

</details>
:::

**다음 챕터**: [Ch10 — Coverage Closure & Regression](../10_coverage_regression/)에서 이 챕터가 남긴 질문 — *"cover가 채워졌는가"* — 을 커버리지 모델 전체로 확장합니다.

**퀴즈**: [Ch09 퀴즈](../quiz/09_assertion_checker_quiz/)

---

## 참고 자료

- [부록 A — `hbm_ch_ctrl` 스펙](../appendix_a_hbm_ch_ctrl_spec/) — 규칙 R1~R20 원본
- [Ch03 — Custom UVM Agent A-to-Z](../03_custom_uvm_agent/) — monitor 독립 재구성, 미해결 테이블
- [Ch08 — Test Case & 시나리오](../08_testcase_scenarios/) — 자극과 판정의 분리
- [HBM 아키텍처 Ch04 — 채널 · Pseudo-channel](../../hbm/04_channels_addressing/) — CA 공유와 주소 디코드 문제의 출처
- [HBM 아키텍처 Ch05 — 인터페이스 프로토콜](../../hbm/05_interface_protocol/) — 감시 대상 분류표
- [UVM 코스 Module 05 — TLM·Scoreboard·Coverage](../../uvm/) — scoreboard 구조와 analysis port
- [Formal Verification 코스](../../formal_verification/) — SVA 문법과 속성 작성 심화
