---
title: "Ch03 — Custom UVM Agent A-to-Z"
---

:::tip[학습 목표]
이 챕터를 마치면:

- **Derive** 인터페이스 스펙으로부터 sequence item의 필드 구성과 트랜잭션 경계를 도출할 수 있다.
- **Implement** driver·monitor·coverage·config를 갖춘 Custom UVM Agent를 구현할 수 있다.
- **Justify** driver가 응답을 기다리지 않는 구조와 monitor가 DUT 신호만으로 재구성하는 구조의 이유를 설명할 수 있다.
- **Design** 오류 주입 능력을 Agent 설계 단계에서 확보하는 방법을 설계할 수 있다.
:::

:::note[사전 지식]
- [부록 A — `hbm_ch_ctrl` 스펙](../appendix_a_hbm_ch_ctrl_spec/): A.4(CCI)와 A.6(동작 규칙). **이 챕터는 스펙을 계속 인용합니다**
- [Ch02 — Digital IP 검증 & Handoff](../02_ip_verification_handoff/): 도구가 없는 칸이 어디였는지
- [UVM 코스 Module 02 — Agent / Driver / Monitor](../../uvm/), [Module 03 — Sequence & Item](../../uvm/): **Agent의 구조와 동작 원리는 여기서 다룹니다.** 이 챕터는 그 구조에 무엇을 어떻게 채우는지만 씁니다
:::

---

## 1. Why care? — 템플릿을 복사하면 될 것 같은데

Ch02에서 경계표의 한 칸이 비어 있었습니다. CCI는 비표준 인터페이스라 **상용 VIP가 없습니다.** 만들어야 합니다.

"UVM agent 만들기"를 찾아보면 템플릿이 나옵니다. `sequence_item`, `sequencer`, `driver`, `monitor`, `agent` 다섯 개의 클래스 뼈대입니다. 복사해서 이름만 바꾸면 될 것 같습니다.

그래서 `cci_item`을 만들고 필드를 채우려는데, 손이 멈춥니다.

- `addr`와 `data`는 당연히 넣겠는데, `pc`·`len`·`id`·`par`는? 전부 필드입니까?
- 응답의 `rsp_err`는 어디에 둡니까? 같은 item입니까, 별도입니까?
- **일부러 틀린 패리티를 보내려면** 어떻게 합니까? 스펙 R12를 검증하려면 반드시 필요한데, 필드 어디에도 그런 자리가 없습니다
- 쓰기 데이터는 버스트라 여러 beat인데, item 하나에 배열로 넣습니까?

템플릿은 **구조**를 줍니다. 그러나 **무엇을 넣을지는 스펙이 정합니다.** 그리고 그 도출 과정이 직무 기술서가 말하는 *"Spec 기반 Custom UVM Agent A-to-Z"* 의 실체입니다. 템플릿을 채우는 일이 아니라, **스펙을 읽고 검증에 필요한 능력을 역산해 구조로 옮기는 일**입니다.

이 챕터는 [부록 A](../appendix_a_hbm_ch_ctrl_spec/)의 CCI 스펙 한 장에서 출발해 그 과정을 끝까지 갑니다.

---

## 2. 직관 — Item은 신호의 묶음이 아니다

### 순진한 시도 1 — 스펙의 신호를 그대로 필드로 옮긴다

CCI에는 세 채널에 걸쳐 신호가 있습니다. 전부 item 필드로 만듭니다.

**어디서 막히나?** 세 채널은 **타이밍이 다릅니다.** 요청은 한 번, 쓰기 데이터는 여러 beat, 응답은 나중에 (그것도 순서가 뒤바뀔 수 있게) 옵니다. 신호를 평평하게 나열하면 **driver가 언제 무엇을 몰아야 하는지** 알 수 없습니다.

게다가 방향이 섞입니다. `req_*`와 `wd_*`는 우리가 만들지만 `rsp_*`는 **DUT가 만드는 것**입니다. 같은 `rand` 필드로 두면 시퀀스가 응답을 "생성"하게 되어 의미가 무너집니다.

### 순진한 시도 2 — 채널마다 item을 따로 만든다

`req_item`, `wd_item`, `rsp_item` 셋으로 나눕니다. 타이밍 문제가 해결됩니다.

**어디서 막히나?** 이번엔 **의미가 흩어집니다.** "주소 X에 값 Y를 썼고 그 결과가 Z였다"는 하나의 사건인데 세 조각으로 나뉩니다. scoreboard는 매번 이들을 다시 이어 붙여야 하고, 그 이어 붙이는 로직이 결국 어딘가에 생깁니다.

### 일반화 — 경계는 "의미 단위"이고, 방향은 필드 속성으로 구분한다

> **Item의 경계는 신호가 아니라 트랜잭션의 의미 단위로 긋는다.**
> 하나의 요청과 그에 딸린 데이터, 그리고 그 결과가 **하나의 item**이다. 서로 다른 방향은 필드의 **속성**(`rand` 여부)으로 구분한다.

CCI에 적용하면 이렇게 됩니다.

| 구분 | 필드 | 누가 채우나 | `rand` |
|---|---|---|---|
| 요청 | `op`, `pc`, `addr`, `len`, `id` | 시퀀스 | ✅ |
| 쓰기 데이터 | `wdata[]` (len+1 beats) | 시퀀스 | ✅ |
| **오류 주입 제어** | `inject_req_par_err` 등 | 시퀀스 | ✅ |
| 응답 | `rdata[]`, `err` | **monitor** | ❌ |
| 관측 시각 | `t_req`, `t_rsp` | monitor | ❌ |

`id`가 요청과 응답을 잇는 열쇠입니다. 스펙 [R9·R11](../appendix_a_hbm_ch_ctrl_spec/)이 *"응답은 순서가 다를 수 있고 `rsp_id`로 대응된다"* 고 규정하므로, `id`는 단순한 필드가 아니라 **트랜잭션 정체성**입니다.

### 스펙에서 역산한 네 가지 설계 결정

Item 구조를 정하기 전에 스펙이 요구하는 **능력**을 먼저 뽑습니다. 이것이 A-to-Z의 핵심 단계입니다.

| 스펙 항목 | Agent가 가져야 할 능력 | 구조에 미치는 영향 |
|---|---|---|
| R12·R13 (패리티 오류 처리) | **의도적으로 틀린 패리티를 보낼 수 있어야** 함 | item에 **오류 주입 제어 필드** |
| R11 (응답 out-of-order) | 여러 요청을 **미해결 상태로 띄울 수 있어야** 함 | driver가 **응답을 기다리지 않음** |
| R9 (`rsp_id` 대응) | 요청·응답을 id로 **매칭**할 수 있어야 함 | monitor가 미해결 테이블 유지 |
| R16 (`EN=0`이면 거부) | CSR 접근과 데이터 요청을 **같은 채널로** 보낼 수 있어야 함 | `op`에 CSR 접근 포함 |
| A.2 (파라미터) | 폭이 바뀌어도 동작해야 함 | 클래스 **파라미터화** |

**이 표를 만드는 것이 Agent 설계의 첫 작업입니다.** 코드는 그 다음입니다.

---

## 3. 작은 예 — 스펙에서 Agent까지

:::note[UVM 버전과 코드 범위]
아래 코드는 **UVM 1.2와 IEEE 1800.2 양쪽에서 동작하는 교집합**으로 작성했습니다. phase·factory·config_db의 동작 원리는 [UVM 코스](../../uvm/)를 참고하세요. 컴파일 가능성을 목표로 했으나 **시뮬레이터 실행 검증은 이 코스의 범위 밖**입니다.
:::

### 3.1 공통 타입

스펙 A.4.1과 A.4.3의 인코딩을 그대로 옮깁니다.

```systemverilog
package cci_pkg;
  import uvm_pkg::*;
  `include "uvm_macros.svh"

  // 스펙 A.4.1 — cci_req_op
  typedef enum bit [1:0] {
    CCI_READ    = 2'd0,
    CCI_WRITE   = 2'd1,
    CCI_CSR_WR  = 2'd2,
    CCI_CSR_RD  = 2'd3
  } cci_op_e;

  // 스펙 A.4.3 — cci_rsp_err
  typedef enum bit [1:0] {
    CCI_OK       = 2'd0,
    CCI_PAR_ERR  = 2'd1,
    CCI_ADDR_ERR = 2'd2,
    CCI_INT_ERR  = 2'd3
  } cci_err_e;
endpackage
```

### 3.2 Sequence Item

```systemverilog
class cci_item #(
  parameter int DATA_W = 32,
  parameter int ADDR_W = 34,
  parameter int ID_W   = 4
) extends uvm_sequence_item;

  // ---- 요청: 시퀀스가 생성 ----
  rand cci_op_e           op;
  rand bit                pc;
  rand bit [ADDR_W-1:0]   addr;
  rand bit [3:0]          len;      // beat 수 - 1
  rand bit [ID_W-1:0]     id;
  rand bit [DATA_W-1:0]   wdata[];

  // ---- 오류 주입 제어: 스펙 R12/R13 검증에 필요 ----
  rand bit                inject_req_par_err;
  rand bit                inject_wd_par_err;

  // ---- 응답: monitor가 채움 (rand 아님) ----
  bit [DATA_W-1:0]        rdata[];
  cci_err_e               err;
  time                    t_req, t_rsp;

  // 쓰기 계열일 때만 wdata를 len+1 개 갖는다
  constraint c_wdata_size {
    if (op inside {CCI_WRITE, CCI_CSR_WR}) wdata.size() == len + 1;
    else                                   wdata.size() == 0;
  }

  // CSR 접근은 단일 beat (스펙 A.7)
  constraint c_csr_len {
    if (op inside {CCI_CSR_WR, CCI_CSR_RD}) len == 0;
  }

  // 오류 주입은 기본적으로 끈다 — 시퀀스가 명시적으로 켠다
  constraint c_no_inject_default {
    soft inject_req_par_err == 1'b0;
    soft inject_wd_par_err  == 1'b0;
  }

  `uvm_object_param_utils_begin(cci_item#(DATA_W, ADDR_W, ID_W))
    `uvm_field_enum(cci_op_e, op,    UVM_ALL_ON)
    `uvm_field_int (pc,               UVM_ALL_ON)
    `uvm_field_int (addr,             UVM_ALL_ON)
    `uvm_field_int (len,              UVM_ALL_ON)
    `uvm_field_int (id,               UVM_ALL_ON)
    `uvm_field_array_int(wdata,       UVM_ALL_ON)
    `uvm_field_array_int(rdata,       UVM_ALL_ON)
    `uvm_field_enum(cci_err_e, err,  UVM_ALL_ON)
  `uvm_object_utils_end

  function new(string name = "cci_item");
    super.new(name);
  endfunction

  // 스펙 A.4.1 — 요청 필드 전체에 대한 홀수 패리티
  function bit calc_req_par();
    return ~(^{op, pc, addr, len, id});
  endfunction

  function bit calc_wd_par(int beat);
    return ~(^wdata[beat]);
  endfunction
endclass
```

**설계 근거 세 가지**

- `inject_*_par_err`가 **`rand` 필드**인 이유: 오류 주입을 시퀀스가 제어해야 하기 때문입니다. driver에 플래그를 두면 특정 트랜잭션만 골라 손상시킬 수 없습니다
- `soft` 제약으로 기본값을 0으로 둔 이유: 일반 시나리오에서는 오류가 없어야 하고, 오류 주입 시나리오만 이 제약을 덮어씁니다
- `rdata`·`err`가 `rand`가 **아닌** 이유: DUT가 만드는 값입니다. 시퀀스가 정할 수 있으면 안 됩니다

:::caution[필드 매크로에 대하여]
`uvm_field_*` 매크로는 `copy`/`compare`/`print`를 자동 생성해 주지만 실행 비용이 있습니다. 트랜잭션 수가 매우 많은 환경에서는 `do_copy`·`do_compare`·`convert2string`을 직접 구현하는 편이 낫습니다. 자세한 판단 기준은 [UVM 코스 Module 06 — 실무 패턴](../../uvm/)을 참고하세요.
:::

### 3.3 Agent Config

```systemverilog
class cci_agent_cfg extends uvm_object;
  `uvm_object_utils(cci_agent_cfg)

  uvm_active_passive_enum is_active       = UVM_ACTIVE;
  bit                     enable_coverage = 1'b1;
  int unsigned            max_outstanding = 8;   // 미해결 요청 상한

  virtual hbm_ch_ctrl_cci_if vif;

  function new(string name = "cci_agent_cfg");
    super.new(name);
  endfunction
endclass
```

`max_outstanding`이 설정값인 이유는 스펙 A.2의 `ID_W`가 파라미터이기 때문입니다 — 21항목 **#8(구성값 파라미터화)** 이 여기서 시작됩니다.

### 3.4 Driver — 응답을 기다리지 않는다

```systemverilog
class cci_driver #(parameter int DATA_W=32, ADDR_W=34, ID_W=4)
  extends uvm_driver #(cci_item#(DATA_W, ADDR_W, ID_W));

  `uvm_component_param_utils(cci_driver#(DATA_W, ADDR_W, ID_W))

  typedef cci_item#(DATA_W, ADDR_W, ID_W) item_t;
  cci_agent_cfg cfg;

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    if (!uvm_config_db#(cci_agent_cfg)::get(this, "", "cfg", cfg))
      `uvm_fatal("CCI_DRV", "cci_agent_cfg를 config_db에서 찾을 수 없습니다")
  endfunction

  task run_phase(uvm_phase phase);
    reset_signals();
    forever begin
      seq_item_port.get_next_item(req);
      drive_request(req);
      // 응답을 기다리지 않고 즉시 완료 처리한다 (근거는 아래 설명)
      seq_item_port.item_done();
    end
  endtask

  task reset_signals();
    cfg.vif.drv_cb.req_valid <= 1'b0;
    cfg.vif.drv_cb.wd_valid  <= 1'b0;
    cfg.vif.drv_cb.rsp_ready <= 1'b1;
  endtask

  task drive_request(item_t it);
    @(cfg.vif.drv_cb);
    cfg.vif.drv_cb.req_valid <= 1'b1;
    cfg.vif.drv_cb.req_op    <= it.op;
    cfg.vif.drv_cb.req_pc    <= it.pc;
    cfg.vif.drv_cb.req_addr  <= it.addr;
    cfg.vif.drv_cb.req_len   <= it.len;
    cfg.vif.drv_cb.req_id    <= it.id;
    // 오류 주입: 정상 패리티를 XOR로 뒤집는다 (스펙 R12 검증용)
    cfg.vif.drv_cb.req_par   <= it.calc_req_par() ^ it.inject_req_par_err;

    // 스펙 R1 — ready가 올 때까지 valid 유지
    do @(cfg.vif.drv_cb); while (cfg.vif.drv_cb.req_ready !== 1'b1);
    cfg.vif.drv_cb.req_valid <= 1'b0;

    if (it.op inside {CCI_WRITE, CCI_CSR_WR}) drive_wdata(it);

    `uvm_info("CCI_DRV",
              $sformatf("요청 발행 op=%s pc=%0d id=%0d len=%0d inject_par=%0b",
                        it.op.name(), it.pc, it.id, it.len, it.inject_req_par_err),
              UVM_HIGH)
  endtask

  task drive_wdata(item_t it);
    foreach (it.wdata[i]) begin
      @(cfg.vif.drv_cb);
      cfg.vif.drv_cb.wd_valid <= 1'b1;
      cfg.vif.drv_cb.wd_data  <= it.wdata[i];
      cfg.vif.drv_cb.wd_last  <= (i == it.wdata.size()-1);
      cfg.vif.drv_cb.wd_par   <= it.calc_wd_par(i) ^ it.inject_wd_par_err;
      do @(cfg.vif.drv_cb); while (cfg.vif.drv_cb.wd_ready !== 1'b1);
      cfg.vif.drv_cb.wd_valid <= 1'b0;
    end
  endtask
endclass
```

**왜 `item_done()`을 응답 전에 부르는가** — 이것이 이 Agent의 가장 중요한 설계 결정입니다.

driver가 응답까지 기다린 뒤 `item_done()`을 부르면, 시퀀스는 다음 요청을 그때서야 보낼 수 있습니다. 즉 **미해결 요청이 항상 1개**가 됩니다. 그러면:

- 스펙 **R11(응답 out-of-order)** 을 자극할 수 없습니다 — 요청이 하나뿐이니 순서가 뒤바뀔 여지가 없습니다
- 스펙 **R3(CA 공유 경합)** 도 자극하기 어렵습니다 — 두 pseudo-channel의 요청이 동시에 대기하는 상황이 만들어지지 않습니다
- 결국 선행 코스가 경고한 *"단일 채널 순차 시나리오만 돌리는"* 상태가 됩니다

응답을 기다리지 않으면 시퀀스가 요청을 연달아 띄울 수 있고, 응답 처리는 **monitor**가 맡습니다. **자극 능력이 곧 검증 가능 범위**이며, 그것이 driver 구조에서 결정됩니다.

### 3.5 Monitor — DUT 신호만으로 재구성한다

```systemverilog
class cci_monitor #(parameter int DATA_W=32, ADDR_W=34, ID_W=4)
  extends uvm_monitor;

  `uvm_component_param_utils(cci_monitor#(DATA_W, ADDR_W, ID_W))

  typedef cci_item#(DATA_W, ADDR_W, ID_W) item_t;
  cci_agent_cfg cfg;

  uvm_analysis_port #(item_t) ap;

  // 미해결 트랜잭션 테이블 — 스펙 R9(rsp_id 대응)를 위해
  protected item_t outstanding[bit [ID_W-1:0]];

  function new(string name, uvm_component parent);
    super.new(name, parent);
    ap = new("ap", this);
  endfunction

  function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    if (!uvm_config_db#(cci_agent_cfg)::get(this, "", "cfg", cfg))
      `uvm_fatal("CCI_MON", "cci_agent_cfg를 config_db에서 찾을 수 없습니다")
  endfunction

  task run_phase(uvm_phase phase);
    fork
      collect_requests();
      collect_responses();
    join
  endtask

  task collect_requests();
    item_t it;
    forever begin
      @(cfg.vif.mon_cb);
      if (cfg.vif.mon_cb.req_valid && cfg.vif.mon_cb.req_ready) begin
        it       = item_t::type_id::create("it");
        it.op    = cci_op_e'(cfg.vif.mon_cb.req_op);
        it.pc    = cfg.vif.mon_cb.req_pc;
        it.addr  = cfg.vif.mon_cb.req_addr;
        it.len   = cfg.vif.mon_cb.req_len;
        it.id    = cfg.vif.mon_cb.req_id;
        it.t_req = $time;

        if (outstanding.exists(it.id))
          `uvm_error("CCI_MON",
                     $sformatf("id=%0d가 미해결 상태인데 재사용되었습니다", it.id))

        outstanding[it.id] = it;
      end
    end
  endtask

  task collect_responses();
    item_t it;
    forever begin
      @(cfg.vif.mon_cb);
      if (cfg.vif.mon_cb.rsp_valid && cfg.vif.mon_cb.rsp_ready) begin
        // 스펙 R9 — rsp_id는 미해결 요청 중 하나여야 한다
        if (!outstanding.exists(cfg.vif.mon_cb.rsp_id)) begin
          `uvm_error("CCI_MON",
                     $sformatf("미해결 목록에 없는 rsp_id=%0d (스펙 R9 위반)",
                               cfg.vif.mon_cb.rsp_id))
          continue;
        end

        it = outstanding[cfg.vif.mon_cb.rsp_id];
        it.rdata = new[it.rdata.size() + 1](it.rdata);
        it.rdata[it.rdata.size()-1] = cfg.vif.mon_cb.rsp_data;
        it.err   = cci_err_e'(cfg.vif.mon_cb.rsp_err);

        if (cfg.vif.mon_cb.rsp_last) begin
          it.t_rsp = $time;
          ap.write(it);                       // 완성된 트랜잭션을 발행
          outstanding.delete(it.id);
        end
      end
    end
  endtask
endclass
```

**monitor가 driver의 item을 재사용하지 않는 이유** — 두 번째로 중요한 설계 결정입니다.

driver가 몰던 item 객체를 monitor가 그대로 받아 응답만 채우면 코드는 짧아집니다. 그러나 그렇게 하면 **DUT가 요청을 잘못 해석해도 알 수 없습니다.** driver가 `addr=0x100`을 몰았는데 DUT가 `0x200`으로 받아들였다면, 재사용된 item에는 여전히 `0x100`이 적혀 있습니다.

monitor는 **DUT의 실제 신호만 보고** 트랜잭션을 재구성해야 하며, 그래야 driver의 의도와 DUT가 본 것을 나중에 대조할 수 있습니다. 이것이 선행 코스의 "조용한 통과"를 막는 구조적 장치입니다.

:::note[🤔 잠깐 — 오류 주입 필드는 왜 item에 있습니까]
`inject_req_par_err`를 item의 `rand` 필드가 아니라 **driver의 설정값**으로 두면 어떻게 됩니까? 스펙 R12·R13을 검증하는 데 어떤 제약이 생깁니까?

<details>
<summary>정답 / 해설</summary>

**driver 설정값으로 두면 "특정 트랜잭션만 골라 손상시키는" 시나리오를 만들 수 없습니다.**

driver의 플래그는 켜져 있는 동안 **모든** 요청에 적용됩니다. 그런데 검증에 필요한 시나리오는 이런 것들입니다.

- 정상 요청 사이에 **오류 요청 하나**를 섞어, 오류가 그 트랜잭션만 실패시키고 나머지는 정상 처리되는지 확인 (R12)
- 두 pseudo-channel 중 **한쪽에만** 오류를 주입해 다른 쪽이 영향받지 않는지 확인
- `MR_ERR_EN.PAR_CHK_EN`을 끈 상태에서 오류를 주입해 **검사하지 않는지** 확인 (R13)
- 오류 발생 후 `MR_ERR_STS.PAR_ERR`이 sticky로 유지되고 **W1C로만 지워지는지** 확인 (R14)

전부 "어느 트랜잭션에 오류를 넣을지"를 시퀀스가 골라야 가능합니다. 그래서 **오류 주입은 item의 속성**이어야 합니다.

**더 일반적인 원리**: 검증에 필요한 능력은 **Agent 설계 단계에 구조로 확보**해야 합니다. 나중에 필요해져서 추가하려면 item·driver·시퀀스를 모두 고쳐야 하고, 이미 작성된 시나리오도 영향을 받습니다. 그래서 §2의 "스펙에서 역산한 설계 결정" 표를 **코드보다 먼저** 만드는 것입니다.

</details>
:::

### 3.6 Coverage와 Agent 조립

```systemverilog
class cci_coverage #(parameter int DATA_W=32, ADDR_W=34, ID_W=4)
  extends uvm_subscriber #(cci_item#(DATA_W, ADDR_W, ID_W));

  `uvm_component_param_utils(cci_coverage#(DATA_W, ADDR_W, ID_W))

  typedef cci_item#(DATA_W, ADDR_W, ID_W) item_t;
  item_t tr;

  covergroup cg_cci;
    cp_op  : coverpoint tr.op;
    cp_pc  : coverpoint tr.pc  { bins pc0 = {0}; bins pc1 = {1}; }
    cp_len : coverpoint tr.len { bins single = {0}; bins burst[] = {[1:15]}; }
    cp_err : coverpoint tr.err;
    // 오류 주입 여부와 실제 응답의 교차 — 스펙 R12/R13 확인용
    x_inject_err : cross cp_err, cp_op;
  endgroup

  function new(string name, uvm_component parent);
    super.new(name, parent);
    cg_cci = new();
  endfunction

  function void write(item_t t);
    tr = t;
    cg_cci.sample();
  endfunction
endclass
```

```systemverilog
class cci_agent #(parameter int DATA_W=32, ADDR_W=34, ID_W=4)
  extends uvm_agent;

  `uvm_component_param_utils(cci_agent#(DATA_W, ADDR_W, ID_W))

  typedef cci_item#(DATA_W, ADDR_W, ID_W) item_t;

  cci_agent_cfg                              cfg;
  uvm_sequencer #(item_t)                    sqr;
  cci_driver   #(DATA_W, ADDR_W, ID_W)       drv;
  cci_monitor  #(DATA_W, ADDR_W, ID_W)       mon;
  cci_coverage #(DATA_W, ADDR_W, ID_W)       cov;

  uvm_analysis_port #(item_t) ap;

  function new(string name, uvm_component parent);
    super.new(name, parent);
    ap = new("ap", this);
  endfunction

  function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    if (!uvm_config_db#(cci_agent_cfg)::get(this, "", "cfg", cfg))
      `uvm_fatal("CCI_AGT", "cci_agent_cfg를 config_db에서 찾을 수 없습니다")

    uvm_config_db#(cci_agent_cfg)::set(this, "*", "cfg", cfg);

    mon = cci_monitor#(DATA_W, ADDR_W, ID_W)::type_id::create("mon", this);

    if (cfg.is_active == UVM_ACTIVE) begin
      sqr = uvm_sequencer#(item_t)::type_id::create("sqr", this);
      drv = cci_driver#(DATA_W, ADDR_W, ID_W)::type_id::create("drv", this);
    end

    if (cfg.enable_coverage)
      cov = cci_coverage#(DATA_W, ADDR_W, ID_W)::type_id::create("cov", this);
  endfunction

  function void connect_phase(uvm_phase phase);
    super.connect_phase(phase);
    mon.ap.connect(ap);
    if (cfg.enable_coverage) mon.ap.connect(cov.analysis_export);
    if (cfg.is_active == UVM_ACTIVE) drv.seq_item_port.connect(sqr.seq_item_export);
  endfunction
endclass
```

**Passive 모드를 지원하는 이유**: 상위 계층(subsystem·full-chip)에서는 실제 상위 로직이 CCI를 구동하고 Agent는 관측만 합니다. `is_active`가 설정값인 덕분에 **같은 Agent를 계층마다 재사용**할 수 있습니다 — Ch06에서 이어집니다.

---

## 4. 일반화 — 다르게 만들 수도 있었던 지점

### 대안 A — 요청과 응답을 별개 item으로 분리했다면?

`cci_req_item`과 `cci_rsp_item`을 따로 두고 analysis port도 둘로 나누는 설계입니다.

**장점**: monitor가 단순해집니다. 미해결 테이블이 필요 없고, 관측한 것을 그대로 발행하면 됩니다.

**대가**: 매칭 로직이 사라지는 것이 아니라 **scoreboard로 이동**합니다. 그리고 요청·응답을 잇는 지식이 여러 곳으로 흩어져, 나중에 "이 트랜잭션의 지연 시간"이나 "미해결 개수" 같은 것을 보려 할 때마다 다시 이어 붙여야 합니다.

**판단**: 트랜잭션의 **의미**를 다루는 컴포넌트가 여럿이라면 매칭을 monitor에 한 번만 두는 편이 낫습니다. 반대로 요청 측 자극만 중요하고 응답은 단순 확인뿐이라면 분리도 합리적입니다. `hbm_ch_ctrl`은 R11(OoO)·성능 측정(#2)·지연 관측이 모두 필요하므로 **통합 쪽**을 택했습니다.

### 대안 B — Driver가 응답까지 처리했다면?

`item_done()`을 응답 수신 후에 부르고 `rsp`를 시퀀스로 돌려주는 구조입니다.

**장점**: 시퀀스가 응답을 직접 보고 다음 행동을 결정할 수 있습니다. 읽은 값에 따라 분기하는 시나리오가 자연스러워집니다.

**대가**: §3.4에서 본 대로 **미해결 요청이 1개로 제한**됩니다. R11·R3을 자극할 수 없습니다.

**판단**: 두 가지가 다 필요하면 **시퀀스 계층에서 해결**합니다 — driver는 non-blocking으로 두고, 응답이 필요한 시퀀스는 monitor의 analysis port를 구독하거나 별도 동기화 수단을 씁니다. **자극 능력을 희생하지 않는 쪽이 우선**입니다.

---

## 5. 디테일 — Agent를 잘못 만들면 벌어지는 일

### 실패 1 — Monitor가 driver의 item을 재사용한다

코드가 짧아지고 미해결 테이블도 필요 없어 매력적으로 보입니다.

**관측되는 증상**: **아무 증상이 없습니다.** DUT가 주소를 잘못 해석해도, 데이터를 잘못된 뱅크에 써도, item에는 driver가 의도한 값이 그대로 있으므로 scoreboard는 일치를 보고합니다. 선행 코스의 "조용한 통과"가 **테스트벤치 구조 때문에** 발생하는 경우입니다.

**원칙**: **monitor는 DUT의 신호만 본다.** driver와 monitor 사이에 객체를 공유하지 않습니다.

### 실패 2 — 자극 능력을 나중에 추가하려 한다

Agent를 단순하게 만들어 두고, 오류 주입이나 OoO 자극이 필요해지면 그때 확장하려는 계획입니다.

**관측되는 증상**: 확장 시점에 item·driver·시퀀스를 모두 고쳐야 하고, **이미 작성된 시나리오가 전부 영향**을 받습니다. 회귀가 한 번 깨지고, 그것을 복구하는 동안 검증 진도가 멈춥니다.

**원칙**: §2의 **"스펙에서 역산한 설계 결정" 표를 코드보다 먼저** 만듭니다. 스펙의 각 규칙에 대해 *"이것을 검증하려면 Agent가 무엇을 할 수 있어야 하는가"* 를 묻고, 그 답을 구조에 반영합니다.

### 실패 3 — 파라미터를 나중에 넣는다

`32`, `34`, `4` 같은 값을 직접 써 두고 나중에 파라미터로 바꾸려는 경우입니다.

**관측되는 증상**: 파생 제품이나 다음 세대에서 폭이 달라지면 **환경을 복사**하게 됩니다. 선행 코스가 세 챕터에 걸쳐 반복한 요구(#8)가 여기서 무시되는 것입니다. 복사된 환경은 이후 서로 다르게 수정되며 유지보수 비용이 제품 수에 비례해 늘어납니다.

**원칙**: 스펙 A.2에 파라미터 목록이 있다면 **처음부터 그대로** 클래스 파라미터로 옮깁니다.

---

## 6. 흔한 오해

| 오해 | 실제 |
|---|---|
| "Agent 만들기는 템플릿을 채우는 일" | 템플릿은 구조만 줍니다. **무엇을 넣을지는 스펙이 정합니다** |
| "Item은 인터페이스 신호의 묶음" | **트랜잭션의 의미 단위**입니다. 방향은 `rand` 속성으로 구분합니다 |
| "Monitor는 driver가 만든 item을 받아 완성하면 된다" | 그러면 DUT의 오해석을 못 잡습니다. **DUT 신호만으로 재구성**합니다 |
| "Driver는 응답을 받고 다음 요청을 보내야 안전" | 미해결이 1개가 되어 **OoO·경합을 자극할 수 없습니다** |
| "오류 주입은 나중에 추가하면 된다" | 구조 변경이 필요하고 기존 시나리오가 깨집니다. **처음부터 설계**합니다 |
| "Passive 모드는 나중에 필요하면 넣는다" | 상위 계층 재사용의 전제입니다. **처음부터 `is_active`로** 둡니다 |

---

## 🔧 이 문제를 이렇게 푼다

> **닫는 항목: #7 — 표준/커스텀 경계 식별 → Custom Agent 구간 확정**

### 1단계 — 경계 판정

경계표(Ch01)의 각 인터페이스에 대해 묻습니다.

| 질문 | 예 → | 아니오 → |
|---|---|---|
| 업계 표준 프로토콜인가? | 상용 VIP 조사 (Ch04) | **Custom Agent 대상** |
| 사내에 유사 Agent 자산이 있는가? | 재사용·확장 검토 | 신규 개발 |

CCI는 첫 질문에서 "아니오"이므로 **Custom Agent 구간**으로 확정됩니다.

### 2단계 — 스펙에서 능력을 역산

**코드보다 먼저** 이 표를 만듭니다. 이것이 A-to-Z의 실체입니다.

| 스펙 규칙 | 검증하려면 Agent가 무엇을 할 수 있어야 하나 | 구조 반영 |
|---|---|---|
| R12·R13 | 틀린 패리티 전송 | item의 `inject_*` 필드 |
| R11 | 다수 요청 동시 미해결 | driver non-blocking |
| R9 | 요청·응답 id 매칭 | monitor 미해결 테이블 |
| R16 | CSR 접근과 데이터 요청 혼재 | `op`에 CSR 포함 |
| A.2 | 폭 변경 대응 | 클래스 파라미터화 |

### 3단계 — 개발 공수 산정

Custom Agent는 **파일 하나가 아닙니다.** 계획에 다음을 항목으로 넣습니다.

| 산출물 | 비고 |
|---|---|
| 타입 정의 (enum 등) | 스펙 인코딩을 그대로 반영 |
| sequence item + 제약 | 능력 역산표의 결과 |
| config 클래스 | 파라미터·활성 모드 |
| driver | 자극 능력이 여기서 결정됨 |
| monitor | 독립 재구성 + 미해결 테이블 |
| coverage | 기본 축만. 동시성 축은 Ch10 |
| agent 조립 | active/passive |
| **기본 시퀀스 라이브러리** | Ch08에서 확장 |
| **문서** | 신호 매핑·사용법 |

### 검증 계획에 남기는 것

- 이 Agent가 **스펙의 어느 규칙을 자극할 수 있는지** 목록 — 자극할 수 없는 규칙이 있으면 그것은 **검증 불가 항목**이며 계획에 드러나야 합니다
- Agent 자체의 **자가 점검** 항목 — monitor가 재구성한 값이 driver의 의도와 일치하는지 확인하는 초기 시나리오(연결성 확인)

---

## 7. 핵심 정리

- Custom Agent 개발은 템플릿 채우기가 아니라 **스펙에서 필요 능력을 역산해 구조로 옮기는 일**이다
- **Item의 경계는 신호가 아니라 트랜잭션의 의미 단위**로 긋는다. 방향은 `rand` 속성으로 구분한다
- **오류 주입은 item의 `rand` 필드**여야 한다 — 시퀀스가 어느 트랜잭션을 손상시킬지 골라야 하므로
- **Driver는 응답을 기다리지 않는다** — 기다리면 미해결이 1개가 되어 OoO(R11)와 경합(R3)을 자극할 수 없다. **자극 능력이 곧 검증 가능 범위**다
- **Monitor는 DUT 신호만으로 재구성한다** — driver의 item을 재사용하면 DUT의 오해석을 원리적으로 못 잡는다
- 파라미터·active/passive는 **처음부터** 넣는다. 나중에 넣으면 환경 복사가 시작된다
- Agent는 파일 하나가 아니라 **9종의 산출물**이다. 공수 산정에 그대로 반영한다

:::note[🤔 마무리 자가 점검]
어떤 팀이 CCI Agent를 만들었는데, 다음과 같이 구현했습니다.

> "monitor는 driver가 보낸 item을 큐에 넣어 두고, 응답이 오면 그 item에 `rdata`와 `err`를 채워 analysis port로 발행합니다. 코드가 짧고 id 매칭도 간단합니다."

(a) 이 구조가 **원리적으로 놓치는** 결함은 무엇입니까? (b) 그런 결함이 실제로 있을 때 회귀 결과는 어떻게 보입니까?

<details>
<summary>정답 / 해설</summary>

**(a) DUT가 요청을 잘못 해석하는 모든 결함을 놓칩니다.**

monitor가 발행하는 item의 요청 필드(`op`·`pc`·`addr`·`len`·`id`)는 **driver가 의도한 값**입니다. DUT가 CCI 버스에서 무엇을 읽었는지가 아닙니다. 따라서 다음이 전부 관측 불가입니다.

- DUT가 `addr`를 잘못 래치 (예: 비트 순서 뒤바뀜)
- DUT가 `pc`를 무시하고 항상 pseudo-channel 0으로 처리
- DUT가 `len`을 잘못 해석해 beat 수를 틀리게 처리
- **오류 주입 시 DUT가 손상된 패리티를 못 보고 정상 처리** — R12 검증 자체가 무의미해짐

마지막 항목이 특히 치명적입니다. 오류 주입 시나리오를 열심히 만들어도, monitor가 driver의 의도만 보고 있으면 **DUT가 실제로 손상된 값을 받았는지조차 확인하지 못합니다.**

**(b) 회귀는 전부 초록색입니다.**

이것이 이 실패의 성격입니다. 테스트가 깨지지 않고, 커버리지도 정상적으로 채워지며, 오히려 **디버깅할 일이 없어 순조로워 보입니다.** 결함은 실리콘에서 드러납니다.

선행 코스가 정리한 네 번의 "조용한 통과"에 하나가 더해지는 셈입니다 — 이번에는 DUT나 모델이 아니라 **테스트벤치 자신의 구조**가 원인입니다. 그래서 원칙이 필요합니다.

> **monitor와 driver는 객체를 공유하지 않는다. monitor는 DUT의 신호만 본다.**

**보완책**: 두 경로를 **모두** 유지하는 방법도 있습니다 — driver의 의도를 담은 item과 monitor가 재구성한 item을 scoreboard에서 **대조**하는 것입니다. 이러면 "DUT가 무엇을 받았는가"까지 검증 대상이 됩니다. 이 대조는 Ch09에서 다룹니다.

</details>
:::

**다음 챕터**: [Ch04 — VIP 전략](../04_vip_strategy/)에서 반대편 문제를 다룹니다. DRAM 쪽에는 상용 VIP가 존재하는데, **사는 것과 만드는 것을 어떻게 판단**하며 산 것이 무엇을 검사해 주는지 어떻게 확인할까요.

**퀴즈**: [Ch03 퀴즈](../quiz/03_custom_uvm_agent_quiz/)

---

## 참고 자료

- [부록 A — `hbm_ch_ctrl` 스펙](../appendix_a_hbm_ch_ctrl_spec/) — A.4(CCI 신호), A.6(규칙 R1~R20)
- [UVM 코스 Module 02 — Agent / Driver / Monitor](../../uvm/) — Agent 구조와 active/passive의 원리
- [UVM 코스 Module 03 — Sequence & Sequence Item](../../uvm/) — item과 시퀀스의 기초
- [UVM 코스 Module 06 — 실무 패턴 & 안티패턴](../../uvm/) — 필드 매크로 vs 직접 구현 판단
- [HBM 아키텍처 Ch06 — Base Die = 미니 SoC](../../hbm/06_base_die_soc/) — Custom Agent가 필요해지는 구조적 배경
