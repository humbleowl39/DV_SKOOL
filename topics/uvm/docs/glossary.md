# UVM 용어집

이 페이지는 본 코스에서 사용되는 UVM 핵심 용어 정의 모음입니다. 항목은 ISO 11179 형식을 따릅니다 (**Definition / Source / Related / Example / See also**).

!!! tip "검색 활용"
    상단 검색창에 용어를 입력하면 본문에서의 사용처도 함께 찾을 수 있습니다.

---

## A — Agent / Analysis Port

### Agent

**Definition.** Driver, Monitor, Sequencer를 묶어 단일 DUT 인터페이스의 자극 인가 및 관찰을 담당하는 UVM 컴포넌트.

**Source.** UVM 1.2 Reference Manual, §5.4 (uvm_agent).

**Related.** Driver, Monitor, Sequencer, Active mode, Passive mode.

**Example.**
```systemverilog
class apb_agent extends uvm_agent;
  `uvm_component_utils(apb_agent)
  apb_driver    drv;
  apb_monitor   mon;
  apb_sequencer sqr;
  // is_active=UVM_ACTIVE → drv/sqr 생성, UVM_PASSIVE → mon만
endclass
```

**See also.** [Module 02 — Agent / Driver / Monitor](02_agent_driver_monitor.md)

### Active / Passive Mode

**Definition.** Agent가 자극을 인가하는지(Active) 또는 관찰만 하는지(Passive)를 결정하는 구성 모드.

**Source.** UVM 1.2 Reference Manual, §5.4.4.

**Related.** Agent, is_active, build_phase 분기.

**Example.** PCIe Root Complex 검증에서 RC 측은 Active, EP 측은 Passive로 같은 Agent를 두 번 인스턴스화.

**See also.** [Module 02](02_agent_driver_monitor.md)

### Analysis Port

**Definition.** Monitor가 관찰한 트랜잭션을 Scoreboard, Coverage 등 여러 구독자에게 단방향 브로드캐스트하기 위한 TLM 포트.

**Source.** UVM 1.2 Reference Manual, §12.2.

**Related.** TLM, Subscriber, write() 콜백.

**Example.**
```systemverilog
uvm_analysis_port#(my_item) ap;
ap = new("ap", this);
ap.write(item);  // 모든 구독자의 write()로 전달
```

**See also.** [Module 05 — TLM, Scoreboard, Coverage](05_tlm_scoreboard_coverage.md)

---

## B — Build Phase

### build_phase

**Definition.** UVM 시뮬레이션에서 컴포넌트를 생성(`type_id::create`)하고 config_db를 읽어 자식을 구성하는 Phase.

**Source.** UVM 1.2 Reference Manual, §9.

**Related.** Phase, top-down 실행, Factory.

**Example.**
```systemverilog
function void build_phase(uvm_phase phase);
  super.build_phase(phase);
  drv = apb_driver::type_id::create("drv", this);
endfunction
```

**See also.** [Module 01 — UVM 아키텍처 & Phase](01_architecture_and_phase.md)

---

## C — config_db / Coverage / Constrained Random

### config_db

**Definition.** 계층(hierarchical path) 기반으로 설정값(virtual interface, parameter, config object)을 set/get하는 UVM의 전역 키-값 저장소.

**Source.** UVM 1.2 Reference Manual, §10.2 (uvm_config_db).

**Related.** Virtual Interface, Configuration Object, build_phase.

**Example.**
```systemverilog
uvm_config_db#(virtual apb_if)::set(null, "uvm_test_top.env.agent.*", "vif", apb_if);
// agent 내부에서:
uvm_config_db#(virtual apb_if)::get(this, "", "vif", vif);
```

**See also.** [Module 04 — config_db & Factory](04_config_db_factory.md)

### Constrained Random

**Definition.** Constraint(제약 조건) 만족 범위 내에서 필드 값을 무작위 생성하는 SystemVerilog의 검증 기법.

**Source.** IEEE 1800-2017, §18 (Constrained random sequences).

**Related.** randomize(), constraint, rand/randc.

**Example.**
```systemverilog
class my_item extends uvm_sequence_item;
  rand bit [31:0] addr;
  constraint c_addr { addr inside {[32'h1000:32'h1FFF]}; }
endclass
```

**See also.** [Module 03 — Sequence & Sequence Item](03_sequence_and_item.md)

### Covergroup

**Definition.** 기능 커버리지(functional coverage) 수집 단위를 정의하는 SystemVerilog 컨테이너로, Coverpoint와 Cross를 포함.

**Source.** IEEE 1800-2017, §19.5.

**Related.** Coverpoint, Cross, Bin.

**Example.**
```systemverilog
covergroup cg_addr;
  cp_addr: coverpoint item.addr {
    bins low  = {[0:'h3FF]};
    bins high = {['hC00:'hFFF]};
  }
endgroup
```

**See also.** [Module 05](05_tlm_scoreboard_coverage.md)

### Coverpoint

**Definition.** 단일 변수/표현식의 값을 bin 단위로 분류해 관찰하는 covergroup의 구성 요소.

**Source.** IEEE 1800-2017, §19.5.

**Related.** Covergroup, Cross.

**Example.** `coverpoint item.burst_len { bins single={1}; bins burst={[2:16]}; }`

**See also.** [Module 05](05_tlm_scoreboard_coverage.md)

### Cross

**Definition.** 둘 이상의 Coverpoint 값 조합을 동시에 관찰해 교차 커버리지를 수집하는 covergroup 구성 요소.

**Source.** IEEE 1800-2017, §19.6.

**Related.** Covergroup, Coverpoint.

**Example.** `cross cp_addr, cp_burst_len;`

**See also.** [Module 05](05_tlm_scoreboard_coverage.md)

---

## D — Driver / Drain Time / DPI-C

### Driver

**Definition.** Sequence가 생성한 트랜잭션을 받아 DUT의 물리 신호로 변환해 인가하는 UVM 컴포넌트.

**Source.** UVM 1.2 Reference Manual, §5.5 (uvm_driver).

**Related.** Sequencer, Sequence Item, Virtual Interface.

**Example.**
```systemverilog
task run_phase(uvm_phase phase);
  forever begin
    seq_item_port.get_next_item(req);
    drive_to_dut(req);
    seq_item_port.item_done();
  end
endtask
```

**See also.** [Module 02](02_agent_driver_monitor.md)

### Drain Time

**Definition.** 마지막 자극을 인가한 후 DUT가 잔여 트랜잭션을 처리하도록 시뮬레이션을 추가로 진행시키는 대기 시간.

**Source.** UVM 1.2 Reference Manual, §9.4 (Phase objection / drain).

**Related.** Objection, run_phase 종료, phase.phase_done.set_drain_time().

**See also.** [Module 01](01_architecture_and_phase.md)

### DPI-C

**Definition.** SystemVerilog와 C/C++ 간 양방향 함수 호출을 가능하게 하는 표준 인터페이스.

**Source.** IEEE 1800-2017, §35.

**Related.** Reference Model, import "DPI-C", export "DPI-C".

**Example.** `import "DPI-C" function int c_model_check(int data);`

**See also.** [Module 05](05_tlm_scoreboard_coverage.md)

---

## F — Factory

### Factory

**Definition.** 객체 생성을 타입 이름 또는 인스턴스 경로로 위임해 type/instance override를 통한 동작 변경을 가능하게 하는 UVM 패턴.

**Source.** UVM 1.2 Reference Manual, §8.

**Related.** type_id::create, set_type_override_by_type, set_inst_override_by_name.

**Example.**
```systemverilog
// 타입 등록
`uvm_component_utils(my_driver)
// 생성
drv = my_driver::type_id::create("drv", this);
// override
my_driver::type_id::set_type_override(my_special_driver::get_type());
```

**See also.** [Module 04](04_config_db_factory.md)

---

## M — Monitor

### Monitor

**Definition.** DUT의 인터페이스 신호를 관찰해 트랜잭션 객체로 변환하고 Analysis Port로 브로드캐스트하는 비침투적 컴포넌트.

**Source.** UVM 1.2 Reference Manual, §5.6 (uvm_monitor).

**Related.** Analysis Port, Virtual Interface, Subscriber.

**Example.**
```systemverilog
task run_phase(uvm_phase phase);
  forever begin
    @(posedge vif.clk iff vif.valid && vif.ready);
    item = my_item::type_id::create("item");
    item.data = vif.data;
    ap.write(item);
  end
endtask
```

**See also.** [Module 02](02_agent_driver_monitor.md)

---

## O — Objection

### Objection

**Definition.** run_phase의 종료 시점을 컴포넌트들이 협상하는 메커니즘으로, raise/drop을 통해 시뮬레이션 종료를 지연.

**Source.** UVM 1.2 Reference Manual, §9.4.

**Related.** Phase, Drain Time, run_phase.

**Example.**
```systemverilog
task body();
  uvm_test_done.raise_objection(this);
  // 자극 인가...
  uvm_test_done.drop_objection(this);
endtask
```

**See also.** [Module 01](01_architecture_and_phase.md)

---

## P — Phase

### Phase

**Definition.** UVM 시뮬레이션의 실행 단계 (build → connect → end_of_elaboration → start_of_simulation → run → extract → check → report → final).

**Source.** UVM 1.2 Reference Manual, §9.

**Related.** build_phase, run_phase, top-down vs bottom-up.

**Example.** Phase 별 책임 분리 — build에서 컴포넌트 생성, connect에서 TLM 연결, run에서 시간 소비.

**See also.** [Module 01](01_architecture_and_phase.md)

---

## R — RAL / Reference Model / Regression

### RAL

**Definition.** Register Abstraction Layer — DUT의 레지스터 맵을 SystemVerilog 객체로 모델링해 read/write/mirror/predict를 자동화하는 UVM 추상화.

**Source.** UVM 1.2 Reference Manual, §18.

**Related.** uvm_reg, uvm_reg_block, uvm_reg_field, predict/mirror.

**Example.**
```systemverilog
class my_reg extends uvm_reg;
  rand uvm_reg_field f_ctrl;  // [3:0] CTRL
  rand uvm_reg_field f_stat;  // [7:4] STAT (RO)
endclass
```

**See also.** [Module 04](04_config_db_factory.md)

### Reference Model

**Definition.** DUT의 기대 동작을 추상적으로 모델링한 검증용 레퍼런스 (SystemVerilog 또는 C/C++ via DPI-C).

**Source.** 일반 검증 관용 표현 (UVM 사양에는 명시 없음).

**Related.** Scoreboard, DPI-C, Predictor.

**See also.** [Module 05](05_tlm_scoreboard_coverage.md)

### Regression

**Definition.** 다수의 테스트를 다양한 시드로 반복 실행해 커버리지를 누적하고 회귀 결함을 찾는 검증 운영 프로세스.

**Source.** 검증 일반 관용 표현.

**Related.** Coverage Closure, Seed, Test Suite.

**See also.** [Module 05](05_tlm_scoreboard_coverage.md)

---

## S — Scoreboard / Sequence / Sequencer / Sequence Item

### Scoreboard

**Definition.** DUT 출력과 Reference Model의 기대값을 비교해 통과/실패를 판정하는 UVM 컴포넌트.

**Source.** UVM 1.2 Reference Manual, §5.7 (uvm_scoreboard).

**Related.** Reference Model, Analysis Port, uvm_in_order_comparator.

**Example.**
```systemverilog
class my_sb extends uvm_scoreboard;
  uvm_analysis_imp#(my_item, my_sb) actual_imp;
  function void write(my_item it);
    if (it != expected_q.pop_front())
      `uvm_error("MISMATCH", ...)
  endfunction
endclass
```

**See also.** [Module 05](05_tlm_scoreboard_coverage.md)

### Sequence

**Definition.** 트랜잭션 생성 시나리오를 정의하는 클래스로, body() task 안에서 sequence item을 시간 순으로 생성.

**Source.** UVM 1.2 Reference Manual, §14.

**Related.** Sequencer, Sequence Item, Virtual Sequence.

**Example.**
```systemverilog
class my_seq extends uvm_sequence#(my_item);
  task body();
    repeat (10) `uvm_do_with(req, { req.addr inside {[0:'hFF]}; })
  endtask
endclass
```

**See also.** [Module 03](03_sequence_and_item.md)

### Sequencer

**Definition.** Sequence와 Driver 사이에서 트랜잭션 흐름을 중개하며 Arbitration을 담당하는 컴포넌트.

**Source.** UVM 1.2 Reference Manual, §15.

**Related.** Driver, Sequence, Arbitration mode.

**See also.** [Module 03](03_sequence_and_item.md)

### Sequence Item

**Definition.** 하나의 트랜잭션 데이터 단위로, uvm_sequence_item을 상속하며 rand 필드와 constraint를 포함.

**Source.** UVM 1.2 Reference Manual, §14.4.

**Related.** Sequence, Driver, Constrained Random.

**Example.**
```systemverilog
class my_item extends uvm_sequence_item;
  `uvm_object_utils(my_item)
  rand bit [31:0] addr;
  rand bit [31:0] data;
endclass
```

**See also.** [Module 03](03_sequence_and_item.md)

---

## T — TLM

### TLM

**Definition.** Transaction Level Modeling — 컴포넌트 간 통신을 비트가 아닌 트랜잭션 단위로 추상화하는 검증 프레임워크 통신 모델.

**Source.** UVM 1.2 Reference Manual, §12.

**Related.** Analysis Port, put/get/peek, FIFO, Imp.

**See also.** [Module 05](05_tlm_scoreboard_coverage.md)

---

## V — Virtual Interface / Virtual Sequence

### Virtual Interface

**Definition.** SystemVerilog interface의 핸들로, UVM class 세계에서 RTL 신호 세계로 접근하는 브릿지.

**Source.** IEEE 1800-2017, §25.9.

**Related.** Interface, modport, config_db.

**Example.**
```systemverilog
virtual apb_if vif;
@(posedge vif.clk);
vif.psel <= 1'b1;
```

**See also.** [Module 02](02_agent_driver_monitor.md)

### Virtual Sequence

**Definition.** 여러 Agent의 Sequencer 위에서 동작하며 시스템 레벨 시나리오를 조정하는 상위 시퀀스.

**Source.** UVM 1.2 Reference Manual, §14.6.

**Related.** Sequence, Sequencer, p_sequencer.

**Example.** AXI Master + APB Slave + Interrupt Agent 셋을 동시에 조율하는 부팅 시나리오 시퀀스.

**See also.** [Module 03](03_sequence_and_item.md)

---

## 추가 약어

| 약어 | 풀네임 | 한 줄 의미 |
|------|--------|-----------|
| **DUT** | Device Under Test | 검증 대상 RTL 설계 |
| **VIP** | Verification IP | 재사용 가능한 검증 컴포넌트 묶음 |
| **TB** | Testbench | 검증 환경 전체 |
| **uvm_env** | — | Agent + Scoreboard + Coverage를 담는 컨테이너 |
| **uvm_test** | — | 최상위 테스트 클래스 (시나리오 선택 + 환경 구성) |
| **grab/lock** | — | Sequence가 Sequencer를 독점 사용하는 메커니즘 |
