---
title: "07 — Hands-on 즉석 작성"
pagefind: false
---

:::tip[학습 목표]
이 모듈을 마치면:

- **Create** 스펙 한 장을 받고 15분 안에 UVM Agent 골격을 작성한다.
- **Create** 스펙 규칙 하나를 assertion + **짝지은 cover property**로 옮긴다.
- **Design** 동시성을 표현하는 covergroup을 `cross`·`illegal_bins`·transition bins로 설계한다.
- **Apply** `dist`·implication·`solve...before`를 쓴 제약을 작성하고 각 블록이 막는 위반을 말로 설명한다.
- **Create** 두 인터페이스를 동시에 구동하는 virtual sequence로 경합 시나리오를 만든다.
:::
:::note[사전 지식]
- [03 — Custom UVM Agent](../03_custom_uvm_agent/) — 여기서 설계한 것을 손으로 쓴다
- [05 — Coverage Closure](../05_vplan_process_coverage/) — bin 설계의 근거
- 전체 구현은 [HBM 검증 실무 Ch03·Ch09·Ch10](../../hbm_dv/03_custom_uvm_agent/)
:::

---

## 0. 이 구간의 평가 기준 — 코드가 아니라 말이다

공유 에디터나 화이트보드에서 즉석 작성을 시키는 이유는 **문법 능력을 보려는 것이 아니다.** 세미콜론이 빠져도 감점은 미미하다. 채점되는 것은 이것이다.

| 평가 항목 | 무엇을 보는가 |
|---|---|
| **순서** | 무엇부터 쓰는가 — 구조를 먼저 잡는가, 세부부터 쓰는가 |
| **근거** | 각 줄이 *무엇을 막는지* 말하는가 |
| **누락 인지** | 다 못 써도 "여기에 X가 더 필요합니다"를 말하는가 |
| **자기 검토** | 다 쓰고 나서 스스로 구멍을 찾는가 |

:::caution[가장 흔한 실패]
**침묵하며 코드만 친다.** 면접관은 화면이 아니라 설명을 듣고 있다. 한 블록 쓸 때마다 한 문장씩 말하라 — *"이 constraint는 정렬 위반을 막습니다"*, *"이 cover가 없으면 assertion이 공허하게 통과합니다"*.
:::

**공통 규칙.** `$display`/`$finish`/`$stop`를 쓰지 않는다 — `uvm_info`/`uvm_error`/`uvm_fatal`만 쓴다. 객체는 `type_id::create`로 만든다. 이 두 가지는 UVM 숙련도의 즉각적 신호다.

## 1. PART 1 — Agent 골격 (제한 시간 15분)

**문제.** "비표준 커맨드 인터페이스 스펙이 있습니다. `cmd_valid`/`cmd_ready` 핸드셰이크, 커맨드 종류는 ROW/COL, pseudo-channel ID와 주소를 실어 보냅니다. UVM Agent를 작성해 보세요."

### 쓰는 순서 — 이 순서를 지키는 것이 절반

```
 1) 타입 정의   →  2) item  →  3) config  →  4) driver
                                              →  5) monitor  →  6) agent 조립
```

### 1.1 타입 + item

```systemverilog
package ch_cmd_pkg;
  import uvm_pkg::*;
  `include "uvm_macros.svh"

  typedef enum bit { CMD_ROW, CMD_COL } cmd_kind_e;
  typedef enum bit [1:0] { RSP_OK, RSP_ERR, RSP_TIMEOUT } rsp_status_e;

  parameter int PC_W   = 5;    // 파라미터로 — 세대가 바뀌어도 재사용
  parameter int ADDR_W = 32;

  class ch_cmd_item extends uvm_sequence_item;
    // 요청: 시퀀스가 제어
    rand cmd_kind_e       kind;
    rand bit [PC_W-1:0]   pc_id;
    rand bit [ADDR_W-1:0] addr;
    // 응답: monitor가 채운다 (rand 아님)
    rsp_status_e          status;
    time                  issue_time;

    `uvm_object_utils(ch_cmd_item)
    function new(string name="ch_cmd_item"); super.new(name); endfunction
  endclass
endpackage
```

> **말할 문장**: "응답 필드를 `rand`로 두지 않은 이유는, DUT가 만드는 값을 시퀀스가 지정하면 모순이 되기 때문입니다."

### 1.2 config + driver

```systemverilog
class ch_agent_cfg extends uvm_object;
  uvm_active_passive_enum is_active = UVM_ACTIVE;   // 처음부터 넣는다
  int unsigned            num_pc    = 32;
  `uvm_object_utils(ch_agent_cfg)
  function new(string name="ch_agent_cfg"); super.new(name); endfunction
endclass

class ch_driver extends uvm_driver #(ch_cmd_item);
  virtual ch_if vif;
  `uvm_component_utils(ch_driver)
  function new(string name, uvm_component parent); super.new(name, parent); endfunction

  task run_phase(uvm_phase phase);
    forever begin
      seq_item_port.get_next_item(req);
      drive(req);
      seq_item_port.item_done();      // 응답을 기다리지 않는다
    end
  endtask

  task drive(ch_cmd_item tr);
    @(posedge vif.clk);
    vif.cmd_valid <= 1'b1;
    vif.cmd_kind  <= tr.kind;
    vif.cmd_pc    <= tr.pc_id;
    vif.cmd_addr  <= tr.addr;
    do @(posedge vif.clk); while (!vif.cmd_ready);   // accept는 기다린다
    vif.cmd_valid <= 1'b0;
    `uvm_info("DRV", $sformatf("issued %s pc=%0d", tr.kind.name(), tr.pc_id), UVM_HIGH)
  endtask
endclass
```

> **말할 문장**: "`item_done`을 응답 전에 호출합니다. 응답까지 기다리면 요청이 직렬화되어 **outstanding 상황을 만들 수 없습니다.** 다만 `ready` 핸드셰이크는 지킵니다 — **수락과 응답은 다릅니다.**"

### 1.3 monitor — 독립 재구성

```systemverilog
class ch_monitor extends uvm_monitor;
  virtual ch_if vif;
  uvm_analysis_port #(ch_cmd_item) ap;
  `uvm_component_utils(ch_monitor)
  function new(string name, uvm_component parent);
    super.new(name, parent); ap = new("ap", this);
  endfunction

  task run_phase(uvm_phase phase);
    forever begin
      @(posedge vif.clk);
      if (!vif.rst_n) continue;
      if (vif.cmd_valid && vif.cmd_ready) begin
        ch_cmd_item tr = ch_cmd_item::type_id::create("tr");
        tr.kind       = cmd_kind_e'(vif.cmd_kind);   // DUT 신호만으로 재구성
        tr.pc_id      = vif.cmd_pc;
        tr.addr       = vif.cmd_addr;
        tr.issue_time = $time;
        ap.write(tr);
      end
    end
  endtask
endclass
```

> **말할 문장**: "driver가 만든 item을 재사용하지 않습니다. 재사용하면 scoreboard가 **자기 자신을 검사**하게 되어 어떤 버그도 잡지 못합니다."

### 1.4 agent 조립

```systemverilog
class ch_agent extends uvm_agent;
  ch_agent_cfg  cfg;
  ch_driver     drv;
  ch_monitor    mon;
  uvm_sequencer #(ch_cmd_item) sqr;
  `uvm_component_utils(ch_agent)
  function new(string name, uvm_component parent); super.new(name, parent); endfunction

  function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    if (!uvm_config_db#(ch_agent_cfg)::get(this, "", "cfg", cfg))
      `uvm_fatal("CFG", "ch_agent_cfg not set")
    mon = ch_monitor::type_id::create("mon", this);
    if (cfg.is_active == UVM_ACTIVE) begin
      drv = ch_driver::type_id::create("drv", this);
      sqr = uvm_sequencer#(ch_cmd_item)::type_id::create("sqr", this);
    end
  endfunction

  function void connect_phase(uvm_phase phase);
    if (cfg.is_active == UVM_ACTIVE)
      drv.seq_item_port.connect(sqr.seq_item_export);
  endfunction
endclass
```

> **말할 문장**: "monitor는 항상 만들고 driver/sequencer만 조건부로 만듭니다. 이래야 상위 계층에서 **passive로 재사용**됩니다."

## 2. PART 2 — Assertion + 짝지은 Cover

**문제.** "스펙 규칙: *row 커맨드와 column 커맨드가 동시에 유효하면 같은 pseudo-channel을 가리켜야 한다.* SVA로 옮겨 보세요."

```systemverilog
module ch_sva #(parameter int TRCD = 4) (
  input logic clk, rst_n,
  input logic row_cmd_valid, col_cmd_valid,
  input logic [PC_W-1:0] row_pc, col_pc
);

  // --- 규칙 본체 ---
  property p_ca_share;
    @(posedge clk) disable iff (!rst_n)
    (row_cmd_valid && col_cmd_valid) |-> (row_pc == col_pc);
  endproperty

  a_ca_share: assert property (p_ca_share)
    else `uvm_error("SVA_CA", $sformatf("pc mismatch: row=%0d col=%0d", row_pc, col_pc))

  // --- 짝지은 cover: 선행 조건이 실제로 발생했는가 ---
  c_ca_share_exercised: cover property (
    @(posedge clk) disable iff (!rst_n) (row_cmd_valid && col_cmd_valid)
  );

endmodule
```

> **말할 문장 (여기가 가산점)**: "assertion만 두면 `row_cmd_valid && col_cmd_valid`가 **한 번도 참이 아닐 때 자동으로 통과**합니다. 그래서 선행 조건이 실제로 발생했는지를 **cover property로 따로 셉니다.** 이게 없으면 assertion 개수는 안심의 근거가 못 됩니다."

### 타이밍 규칙 — local variable로 안전하게

**문제.** "ACT 이후 tRCD 동안 같은 뱅크에 column 커맨드가 오면 안 된다."

```systemverilog
property p_trcd;
  bit [BANK_W-1:0] b;
  @(posedge clk) disable iff (!rst_n)
  (act_valid, b = act_bank) |=> (!(col_valid && col_bank == b))[*TRCD-1];
endproperty

a_trcd: assert property (p_trcd)
  else `uvm_error("SVA_TRCD", $sformatf("tRCD violation on bank %0d", col_bank))

c_trcd_tight: cover property (            // 경계값이 실제로 나왔는가
  @(posedge clk) disable iff (!rst_n)
  act_valid ##TRCD (col_valid)
);
```

> **말할 문장**: "뱅크 번호를 **local variable로 캡처**했습니다. `$past`로 되짚으면 시점이 어긋나기 쉽습니다. 그리고 cover는 **경계값(정확히 tRCD 후)** 이 실제로 발생했는지를 봅니다 — 여유 있게만 돌면 규칙이 검증된 게 아닙니다."

## 3. PART 3 — Covergroup

**문제.** "채널 동시성을 커버리지로 표현해 보세요."

**함정을 먼저 말하는 것이 답이다.**

> "채널 인덱스만으로 bin을 나누면 '모든 채널을 써봤다'는 100%가 나오지만, 실제 결함은 **CA 버스를 공유하는 pseudo-channel 쌍의 동시 요청**에서 납니다. 그래서 **동시성 자체를 축으로** 잡겠습니다."

```systemverilog
class ch_coverage extends uvm_subscriber #(ch_cmd_item);
  `uvm_component_utils(ch_coverage)

  bit                  row_v, col_v;
  bit [PC_W-1:0]       row_pc, col_pc;
  cmd_kind_e           prev_kind, cur_kind;

  covergroup cg_concurrency;
    option.per_instance = 1;

    // 동시성 축 — 이 bin이 핵심
    cp_concur: coverpoint {row_v, col_v} {
      bins none     = {2'b00};
      bins row_only = {2'b10};
      bins col_only = {2'b01};
      bins both     = {2'b11};          // ← 여기가 결함이 사는 곳
    }

    // 동시 발행일 때의 pc 쌍
    cp_row_pc: coverpoint row_pc iff (row_v && col_v) { bins pc[] = {[0:NUM_PC-1]}; }
    cp_col_pc: coverpoint col_pc iff (row_v && col_v) { bins pc[] = {[0:NUM_PC-1]}; }
    x_pc_pair: cross cp_row_pc, cp_col_pc;

    // 커맨드 전이 — 순서 의존 결함
    cp_kind_tr: coverpoint cur_kind {
      bins row2col = (CMD_ROW => CMD_COL);
      bins col2row = (CMD_COL => CMD_ROW);
      bins row2row = (CMD_ROW => CMD_ROW);
    }
  endgroup

  function new(string name, uvm_component parent);
    super.new(name, parent); cg_concurrency = new();
  endfunction

  function void write(ch_cmd_item t);
    cur_kind = t.kind;
    cg_concurrency.sample();
  endfunction
endclass
```

> **말할 문장 세 개**
> 1. "`cp_concur`의 `both` bin이 이 covergroup의 존재 이유입니다."
> 2. "`x_pc_pair`는 **동시 발행일 때만** 샘플링되도록 `iff`를 걸었습니다. 안 걸면 의미 없는 조합이 채워집니다."
> 3. "전이 bin을 넣은 이유는 **순서 의존 결함**이 단일 상태 bin으로는 안 잡히기 때문입니다."

:::note[꼬리질문]
- *"`illegal_bins`은 언제 쓰나요?"* → **발생하면 안 되는** 값에 쓴다. 발생 시 즉시 오류가 난다. "발생 가능하지만 관심 없는" 값은 `ignore_bins`다. **이 둘을 구분해 말하는 것이 포인트.**
- *"cross bin이 너무 많아지면?"* → `binsof`/`intersect`로 의미 있는 부분집합만 남긴다. 무작정 cross를 걸면 도달 불가 조합이 hole로 남아 closure를 방해한다.
:::

## 4. PART 4 — Constraint

**문제.** "커맨드를 랜덤화하되, 90%는 정상·10%는 에러 주입, 주소는 정렬, pseudo-channel은 전 범위에 고르게."

```systemverilog
class ch_cmd_item_rand extends ch_cmd_item;
  rand bit        inject_err;
  rand bit [2:0]  err_code;
  rand int unsigned size;      // 1,2,4,8 바이트

  `uvm_object_utils(ch_cmd_item_rand)
  function new(string name="ch_cmd_item_rand"); super.new(name); endfunction

  constraint c_pc    { pc_id inside {[0:NUM_PC-1]}; }
  constraint c_size  { size inside {1, 2, 4, 8}; }
  constraint c_align { addr % size == 0; }                    // 정렬 위반 방지

  constraint c_err_dist { inject_err dist {0 := 90, 1 := 10}; }
  constraint c_err_code {
    inject_err  -> err_code inside {[1:5]};
    !inject_err -> err_code == 0;                             // 모순 방지
  }

  // size를 먼저 정해야 addr 분포가 편향되지 않는다
  constraint c_order { solve size before addr; }
endclass
```

> **말할 문장**
> - "`c_align`이 없으면 unaligned 전송이 생겨 DUT가 거부하거나 데이터가 어긋납니다."
> - "`!inject_err -> err_code == 0`을 **양방향으로** 적은 이유는, 정상인데 err_code가 살아 있는 모순을 막기 위해서입니다."
> - "`solve size before addr`이 없으면 solver가 addr을 먼저 정해 **size 분포가 1로 쏠립니다.** 정렬 제약이 있는 상태에서 addr이 홀수면 size는 1밖에 못 되기 때문입니다."

:::tip[여기서 점수가 갈린다]
`solve...before`의 **이유를 해 공간으로 설명**하는 지원자는 드물다. "분포가 편향돼서"까지는 많이 말하지만, *왜 그 방향으로 편향되는지*를 말하면 확실히 구분된다.
:::

## 5. PART 5 — Virtual Sequence (경합 시나리오)

**문제.** "두 pseudo-channel이 CA 버스를 동시에 요청하는 상황을 만들어 보세요."

```systemverilog
class ch_concur_vseq extends uvm_sequence;
  `uvm_object_utils(ch_concur_vseq)
  `uvm_declare_p_sequencer(ch_vsequencer)
  function new(string name="ch_concur_vseq"); super.new(name); endfunction

  rand bit [PC_W-1:0] pc_a, pc_b;
  constraint c_distinct { pc_a != pc_b; }

  task body();
    ch_row_seq row_s;
    ch_col_seq col_s;
    row_s = ch_row_seq::type_id::create("row_s");
    col_s = ch_col_seq::type_id::create("col_s");
    row_s.pc_id = pc_a;
    col_s.pc_id = pc_b;

    `uvm_info("VSEQ", $sformatf("concurrent request pc_a=%0d pc_b=%0d", pc_a, pc_b), UVM_LOW)

    // 동시 발행 — 순차로 돌리면 경합이 만들어지지 않는다
    fork
      row_s.start(p_sequencer.row_sqr);
      col_s.start(p_sequencer.col_sqr);
    join
  endtask
endclass
```

> **말할 문장 (핵심)**: "`fork...join`이 이 시나리오의 전부입니다. 순차로 돌리면 **아무리 시드를 늘려도** 동시 요청은 만들어지지 않습니다. **시드 개수는 시나리오 구조의 결함을 보완하지 못합니다.**"

:::caution[반드시 덧붙일 것]
"판정은 이 시퀀스가 하지 않습니다. **self-checking은 scoreboard와 assertion**에 둡니다. 시퀀스 안에서 비교하면 그 검사는 이 시나리오에서만 동작하고 재사용되지 않습니다."

*"체크를 시퀀스에 넣지 않는 이유"* 는 거의 반드시 물어보는 꼬리질문이다.
:::

## 6. 작성 중 말할 문장 템플릿

손이 멈췄을 때 쓸 수 있는 문장들이다. **침묵보다 훨씬 낫다.**

| 상황 | 말할 문장 |
|---|---|
| 시작할 때 | "먼저 구조를 잡고 세부를 채우겠습니다. 타입 → item → config → driver → monitor 순서로 가겠습니다." |
| 막혔을 때 | "여기 문법이 정확히 기억나지 않는데, 의도는 ~입니다. 실제로는 문서를 확인하겠습니다." |
| 다 못 썼을 때 | "시간상 여기까지 썼고, 추가로 필요한 것은 ①~ ②~ 입니다." |
| 다 썼을 때 | "한 번 검토하겠습니다 — 이 구조의 약점은 ~이고, 실무에서는 ~를 더 넣겠습니다." |

**마지막 항목이 가장 중요하다.** 스스로 구멍을 지적하는 지원자는 코드가 완벽한 지원자보다 높게 평가된다.

## 7. 자주 나오는 지적과 대응

| 면접관 지적 | 대응 |
|---|---|
| "이 assertion, 조건이 안 뜨면 통과하는데요?" | "네, 그래서 **cover property를 짝지었습니다**" (이미 썼다면 완승) |
| "covergroup에 hole이 남으면요?" | "자극 부족/도달 불가/bin 오설계로 **분류**하고, 도달 불가는 근거와 함께 exclusion합니다" |
| "driver가 응답을 안 기다리면 순서는요?" | "tag로 매칭합니다. 수락과 응답은 다른 이야기입니다" |
| "이거 실제로 컴파일되나요?" | "문법 세부는 확인이 필요합니다. **의도는 ~입니다**" — 정직하게 |

## 핵심 정리

- 평가되는 것은 코드가 아니라 **순서 · 근거 · 누락 인지 · 자기 검토**다.
- **침묵하지 마라.** 한 블록마다 한 문장.
- `$display` 금지, `type_id::create` — UVM 숙련도의 즉각 신호.
- **assertion 하나에 cover property 하나.** 타이밍 규칙은 **local variable**로 캡처.
- covergroup은 **동시성 자체를 축으로.** 채널 인덱스만 나누면 결함 공간을 못 덮는다.
- `illegal_bins`(발생하면 안 됨) ≠ `ignore_bins`(관심 없음).
- `solve...before`는 **해 공간으로** 설명한다.
- 경합은 `fork...join`. **판정은 시퀀스가 아니라 scoreboard/assertion**에 둔다.
- 마지막에 **스스로 약점을 지적**하는 것이 최고의 마무리다.

:::note[다음 단계]
기술 축은 여기까지다. 이제 경험을 서사로 바꾼다 — [08 — 프로젝트 재포지셔닝 · 디버깅 STAR](../08_project_star/). 이해도 확인은 [퀴즈](../quiz/07_handson_writing_quiz/).
:::
