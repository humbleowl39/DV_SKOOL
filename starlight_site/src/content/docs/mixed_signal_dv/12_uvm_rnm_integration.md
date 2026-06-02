---
title: "Ch12. UVM × RNM Integration — Env · Agent · Sequence · Scoreboard"
---

## 학습 목표

- **(Remember)** UVM-DMS env의 표준 토폴로지 (virtual sequencer + analog/reg/irq agent + DUT wrapper + scoreboard + ref model) 를 진술할 수 있다
- **(Understand)** analog agent의 driver/monitor 비대칭성과 virtual interface에 nettype을 노출하는 방법을 설명할 수 있다
- **(Apply)** sequence_item에 real 필드를 두고 inline interface helper task로 sub-event step을 만드는 패턴을 작성할 수 있다
- **(Analyze)** scoreboard fail이 발생했을 때 RNM model bug · reference bug · DUT bug · tolerance · seed corner 중 어디에 가까운지 좁힐 수 있다
- **(Create)** 한 UVM env가 RNM/Spice abstraction switching과 IP→SoC 재사용을 모두 지원하도록 설계할 수 있다

## 1. 한 UVM env 안에 두 도메인

> **용어 메모:** 이 챕터는 정확히 말하면 **"UVM-DMS"** (Digital Mixed-Signal, Ch10 §1 정의) — 즉 RNM 기반 mixed-signal의 UVM 통합 — 을 다룹니다. 산업 문헌·Accellera working group에서 같은 내용을 종종 **"UVM-AMS"** 로 부르는데, 거기서의 "AMS"는 Verilog-AMS 언어가 아니라 **mixed-signal 우산 용어**입니다. 두 용법의 차이는 Ch02 §5.1 참조.

digital UVM env에 익숙한 사람이 mixed-signal env로 처음 넘어올 때 가장 어색한 것은 **"같은 env 안에 시간 모델이 다른 두 종류의 agent가 공존한다"**는 사실입니다. digital agent는 클록 엣지 단위로 transaction을 처리합니다. 반면 analog agent는 "1.0 V를 100 ns에 걸쳐 ramp-up"처럼 연속적인 파형을 수백 개의 sub-event step으로 분해해서 생성합니다. 이 두 agent가 만든 신호를 한 scoreboard에서 시간 순서에 맞게 정렬하고 비교하는 것이 env topology 설계의 본질입니다. 이 비대칭을 이해하면 나머지는 디지털 DV의 연장선입니다.

### 1.1 표준 토폴로지

```d2
direction: down

uvm_test: "UVM TEST"
virt_seq: "virtual sequencer\n(analog + reg + irq)"

analog_agent: "analog_agent\n· sequencer\n· driver (rv)\n· monitor"
reg_agent: "reg_agent\n· RAL adapter\n· APB/AXI drv\n· APB/AXI mon"
irq_agent: "irq_agent\n· irq monitor\n· irq sample"

dut_wrapper: "DUT WRAPPER" {
  rnm_model: "RNM analog model"
  digital_rtl: "digital RTL\n(FSM, cal, DSP)"
  rnm_model <-> digital_rtl
}

scoreboard: "scoreboard\n← analog mon + reg mon + irq mon + ref model"
coverage: "coverage\n← functional cg + assertion cover"

uvm_test -> virt_seq
virt_seq -> analog_agent
virt_seq -> reg_agent
virt_seq -> irq_agent
analog_agent -> dut_wrapper
reg_agent -> dut_wrapper
irq_agent -> dut_wrapper
dut_wrapper -> scoreboard
dut_wrapper -> coverage
```

### 1.2 구성 요소별 책임

표준 토폴로지의 각 요소가 mixed-signal에서 어떤 역할을 담당하는지를 정리합니다. digital UVM과 동일한 이름의 컴포넌트라도 mixed-signal 특유의 포인트가 있습니다.

| 요소 | 역할 | MS-specific 포인트 |
|---|---|---|
| analog_agent | analog 신호 stim·sense | driver는 sub-event step, monitor는 trigger 기반 sample |
| reg_agent (RAL) | register read/write | analog 모델의 trim · enable bit도 RAL 안에 — 모델과 RTL이 동시에 본다 |
| int_agent | interrupt / status | analog event(lock, eoc 등)가 보통 IRQ로 옴 → 동기 필요 |
| virtual sequencer | cross-agent 시나리오 | analog stim 시작 → register write → IRQ 대기 같은 흐름을 한 sequence가 조율 |
| DUT wrapper | RNM + RTL 묶기 | swap-in/out: factory override로 Spice/RNM 교체 가능하게 abstract layer |
| scoreboard | 예상 vs 관측 비교 | analog tolerance, multi-rate 정렬, reference model 호출 |
| ref model | 예상값 계산 | SV / DPI / co-sim 중 택1, spec 수식 직접 코드화 |
| coverage | 도달도 정의 | real bin · spec corner cross · transition |

이 중 digital DV에서 가장 낯선 것은 **DUT wrapper의 swap-in 패턴**과 **scoreboard의 tolerance + multi-rate 동기**입니다. 다음 절들에서 각각을 집중적으로 다룹니다.

### 1.3 DUT wrapper의 swap-in 패턴

같은 testbench로 RNM 회귀와 Spice cosim spot check를 둘 다 돌리려면 DUT wrapper에서 모델을 **한 줄로 교체**할 수 있어야 합니다.

```systemverilog
module dut_wrapper (
  input  wSupply vdd,
  input  wAnalog vin,
  output wAnalog vout,
  /* ... digital RTL ports ... */
);
`ifdef RNM_MODEL
  rnm_analog u_core (.vdd(vdd), .vin(vin), .vout(vout), .*);
`elsif SPICE_MODEL
  // Spice subckt 호출 (vendor-specific)
`else
  // pure digital stub (PLL = clock divider 등)
`endif

  rtl_ctrl u_ctrl (.*);       // digital RTL은 항상 동일
endmodule
```

> `` `ifdef ``로 가르면 elaboration log에서 어떤 모델이 들어갔는지 한 줄로 보입니다 (예: `RNM_MODEL=1`). test config가 model 종류와 같이 갈 수 있게 **build option ↔ regression list**를 한 곳에서 관리하세요.

### 1.4 env_cfg 권장 항목

| 항목 | 예시 값 |
|---|---|
| model 종류 | `RNM` / `SPICE` / `STUB` |
| noise enable / seed | `bit noise_en` + `int noise_seed` |
| tolerance set | abs_tol/rel_tol/timing_tol per IP |
| ref model 종류 | `SV` / `DPI` / `COSIM_FILE` |
| scoreboard mode | `STRICT` / `RELAXED` |

### 1.5 IP env → SoC env 합성

IP 검증 env가 그대로 SoC 검증에 재사용되어야 model maintenance 비용이 통제됩니다. SoC env는 IP env들의 instance를 가지고, virtual sequencer만 chip-wide 시나리오를 작성하는 형태:

```systemverilog
class soc_env extends uvm_env;
  pll_env  u_pll;        // IP env 그대로 재사용
  adc_env  u_adc;
  pmu_env  u_pmu;

  virtual function void build_phase(uvm_phase phase);
    u_pll = pll_env::type_id::create("u_pll", this);
    u_adc = adc_env::type_id::create("u_adc", this);
    u_pmu = pmu_env::type_id::create("u_pmu", this);
    // soc-level virtual sequencer는 위 env의 sequencer를 모은 것
  endfunction
endclass
```

> env 설계가 IP-level의 사고에 갇히면 SoC 통합에서 큰 비용이 발생합니다. 처음부터 SoC 재사용을 가정하고 **config object와 virtual sequencer 인터페이스**를 명문화하세요.

## 2. Virtual Interface — nettype을 UVM에 노출

UVM의 `uvm_component`는 module hierarchy 바깥에 있습니다. DUT 신호와 연결하려면 **SV interface 인스턴스**를 component가 잡고 있어야 하는데, mixed-signal에서는 그 interface에 `nettype` 신호가 섞여 있어 선언·접근·sampling이 까다로워집니다.

### 2.1 mixed interface 선언

```systemverilog
interface adc_if (input bit clk);
  // analog (RNM nettype)
  wAnalog       vin;
  wAnalog       vref;

  // digital
  logic         start;
  logic         eoc;
  logic [11:0]  code;

  modport drv_mp (
    output vin,      output start,  output vref,
    input  eoc,      input  code,   input  clk
  );
  modport mon_mp (
    input  vin,      input  start,  input  vref,
    input  eoc,      input  code,   input  clk
  );

  // analog "method" — interface 안에 ramp generator 내장
  task automatic apply_ramp(real vstart, real vend, real T_ns, int steps);
    automatic real dt = T_ns / steps;
    automatic real dv = (vend - vstart) / steps;
    automatic analog_t drv;
    drv.I = 0.0; drv.Z = 50.0;
    for (int i = 0; i <= steps; i++) begin
      drv.V = vstart + dv * i;
      vin   = drv;
      #(dt * 1ns);
    end
  endtask
endinterface
```

> analog 파형 생성기를 **interface 안의 task**로 두는 패턴은 매우 강력합니다. driver는 sequence_item을 받아 `vif.apply_ramp(...)` 한 줄만 호출 — driver 코드가 깔끔해지고 vendor 호환성도 좋아집니다.

### 2.2 UVM에서 잡는 방법

```systemverilog
module tb_top;
  bit clk;
  adc_if vif (.clk(clk));

  initial uvm_config_db#(virtual adc_if)::set(null, "*", "vif", vif);
  initial uvm_pkg::run_test();
endmodule

class adc_agent extends uvm_agent;
  virtual adc_if vif;
  function void build_phase(uvm_phase phase);
    if (!uvm_config_db#(virtual adc_if)::get(this, "", "vif", vif))
      `uvm_fatal("CFG", "adc_if not set")
  endfunction
endclass
```

### 2.3 modport로 driver/monitor 권한 분리

- `drv_mp`: 신호를 **출력**으로 본다 → driver가 잡을 수 있음
- `mon_mp`: 모두 **입력** → 실수로 monitor가 driving하는 사고 방지
- nettype 신호는 modport에서 입출력 명시 가능. 단, simulator마다 nettype + inout 처리에 미묘한 차이가 있어 **단방향 권장**

```systemverilog
class adc_driver extends uvm_driver#(adc_item);
  virtual adc_if.drv_mp vif;       // drv_mp만 access
endclass

class adc_monitor extends uvm_monitor;
  virtual adc_if.mon_mp vif;       // mon_mp만 access — 안전
endclass
```

### 2.4 clocking block과 real — 호환성 안전 패턴

digital UVM에서는 `clocking` block으로 race를 피합니다. RNM에서도 동일하게 쓰고 싶지만 — `real`/nettype 신호의 clocking 지원은 **vendor마다 다릅니다**. 안전 패턴은 **별도 always 블록에서 sample**한 뒤 monitor가 그 sample을 transaction화하는 것:

```systemverilog
// 호환성 최선: 명시적 always sample
real vin_sampled;
always @(posedge clk) vin_sampled <= vif.vin.V;

// (시도 가능, vendor 확인 필수)
clocking cb @(posedge clk);
  default input #1step output #0;
  input  real vin_v;            // 일부 simulator만 OK
  input  logic [11:0] code;
endclocking
```

### 2.5 Power-aware interface — supply 분리

analog IP의 동작은 `vdd`에 강하게 의존합니다. supply rail은 별도의 `wSupply` nettype으로 두고 같은 interface에서 노출해두면, driver가 supply ramp를 직접 흔들 수 있습니다.

```systemverilog
interface adc_if (input bit clk);
  wSupply vdd;       // 공급 rail (V + valid + bit on)
  wAnalog vin;       // 신호

  task automatic apply_supply_ramp(real V_target, real T_ns, int steps);
    automatic supply_t drv;
    automatic real dt = T_ns / steps;
    automatic real V0 = vdd.V;
    automatic real dv = (V_target - V0) / steps;
    drv.valid = 1;
    for (int i = 0; i <= steps; i++) begin
      drv.V = V0 + dv * i;
      vdd   = drv;
      #(dt * 1ns);
    end
  endtask
endinterface
```

### 2.6 setup 시 자주 만나는 함정

- **config_db에서 vif 못 찾음** — set/get path 또는 instance name 오류. `uvm_top.print_topology()`로 확인
- **nettype 신호의 driver가 두 곳** — interface 안과 외부에서 동시 drive하면 resolution function 결과가 비결정적
- **clocking에 real 넣었더니 elaboration warning** — 위처럼 always 블록 sample로 분리
- **modport 안에 task 호출 권한** — `modport drv_mp (import apply_ramp);` 명시 필요

## 3. Analog Agent — 비대칭 Driver/Monitor

디지털 agent는 driver와 monitor가 대칭입니다. driver는 클록 엣지마다 신호를 구동하고, monitor는 같은 클록 엣지마다 신호를 샘플링합니다. analog agent는 이 대칭이 깨집니다. **driver는 sub-event step으로 연속 파형을 생성하고, monitor는 trigger 이벤트 기반으로 의미 단위 transaction을 수집합니다.** 이 비대칭을 이해하지 못하면 analog agent를 잘못 구현하게 됩니다.

```d2
direction: down

digital_agent: "Digital agent (대칭)" {
  d_driver: "driver\ntransaction → cycle 단위 신호"
  d_dut: "DUT"
  d_monitor: "monitor\nDUT의 cycle 단위 신호 → transaction"
  d_driver -> d_dut
  d_dut -> d_monitor
}

analog_agent: "Analog agent (비대칭)" {
  a_driver: "driver\ntransaction → 시간×값 sub-event 시퀀스\n(수 ns/sample)"
  a_dut: "DUT"
  a_monitor: "monitor\nDUT 신호 → trigger 검출 → 의미 단위 transaction\n(zero-cross, settled, eoc 등)"
  a_driver -> a_dut
  a_dut -> a_monitor
}
```

driver는 "0.0 V에서 1.8 V로 100 ns에 걸쳐 선형 ramp" 같은 파라미터화된 의도(intent)를 sub-event step으로 풀어냅니다. monitor는 "BL 전압이 threshold를 지나는 시점", "출력이 settled 된 시점", "ADC의 eoc 신호가 올라오는 시점" 같은 trigger에 반응해 의미 있는 transaction을 만듭니다. 이 비대칭이 모든 구현 결정에 영향을 줍니다.

### 3.1 sequence_item에 "의도(kind) + 파라미터" 패턴

sequence_item이 "DC 1.2 V 인가" 또는 "0.5 V 진폭 1 MHz sine 100 cycle"이면, driver가 그 의미를 sub-event step으로 풉니다. **driver는 wave 생성 알고리즘을 직접 갖고 있지 않고** — interface helper 또는 별도 BFM library에 위임합니다.

```systemverilog
typedef enum {ADC_DC, ADC_RAMP, ADC_SINE, ADC_STEP} adc_kind_e;

class adc_item extends uvm_sequence_item;
  rand adc_kind_e kind;
  rand real       vin_volt;      // for DC
  rand real       vstart, vend;  // for RAMP/STEP
  rand real       ampl, bias, freq_hz;   // for SINE
  rand real       T_ns;
  rand int        steps;
  // ...
endclass

class adc_driver extends uvm_driver#(adc_item);
  virtual adc_if.drv_mp vif;

  task run_phase(uvm_phase phase);
    forever begin
      adc_item it;
      seq_item_port.get_next_item(it);
      drive_one(it);
      seq_item_port.item_done();
    end
  endtask

  task drive_one(adc_item it);
    case (it.kind)
      ADC_DC:    vif.apply_dc(it.vin_volt);
      ADC_RAMP:  vif.apply_ramp(it.vstart, it.vend, it.T_ns, it.steps);
      ADC_SINE:  vif.apply_sine(it.ampl, it.bias, it.freq_hz, it.T_ns, it.steps);
      ADC_STEP:  vif.apply_step(it.vstart, it.vend, it.T_ns);
      default:   `uvm_warning("DRV", $sformatf("unknown kind %0d", it.kind))
    endcase
  endtask
endclass
```

> sequence_item에 **"의도(kind) + 파라미터"**를 담고 driver가 매핑하면, 같은 driver로 DC/ramp/sine/step 모두 cover됩니다. 파형 종류별로 driver class를 따로 만들면 factory override가 폭발합니다.

### 3.2 Monitor의 3가지 sampling 전략

**① Threshold cross** — "`vsig`가 0.9 V를 지날 때마다" — comparator 모델, zero-crossing, ADC start

```systemverilog
real prev;
always @(vif.vsig.V) begin
  if (prev < 0.9 && vif.vsig.V >= 0.9) publish_event(THRESH_UP);
  prev = vif.vsig.V;
end
```

**② Periodic sample** — "`Tclk`마다 sample" — ADC 출력 회수, scope-like monitor

```systemverilog
always @(posedge vif.clk) begin
  trans = adc_obs::type_id::create("o");
  trans.code = vif.code;
  trans.vin  = vif.vin.V;
  ap.write(trans);
end
```

**③ Settled detector** — "변화량 < eps이 N cycle 유지"

```systemverilog
task automatic wait_settled(real eps, int N);
  real last = vif.vsig.V; int hold = 0;
  forever begin
    @(posedge vif.clk);
    if ($abs(vif.vsig.V - last) < eps) hold++;
    else                                hold = 0;
    if (hold >= N) return;
    last = vif.vsig.V;
  end
endtask
```

### 3.3 active vs passive — is_active

UVM의 `is_active`로 같은 agent를 stim 가능 모드와 monitor-only 모드로 전환. SoC 통합 시 IP-level driver는 비활성화하고 chip-wide stimulus만 통과시킵니다.

```systemverilog
class adc_agent extends uvm_agent;
  adc_driver    drv;
  adc_monitor   mon;
  adc_sequencer sqr;

  function void build_phase(uvm_phase phase);
    mon = adc_monitor::type_id::create("mon", this);
    if (is_active == UVM_ACTIVE) begin
      drv = adc_driver::type_id::create("drv", this);
      sqr = adc_sequencer::type_id::create("sqr", this);
    end
  endfunction
  function void connect_phase(uvm_phase phase);
    if (is_active == UVM_ACTIVE)
      drv.seq_item_port.connect(sqr.seq_item_export);
  endfunction
endclass
```

### 3.4 driver와 monitor가 같은 net을 잡지 마라

한 nettype net에 **외부 driver와 IP 내부 driver**가 동시에 잡히면 resolution function이 합성해버려 의도와 다른 파형이 나옵니다. analog agent는 보통 다음 두 가지 분리를 유지:

- 외부 stim은 high-impedance driver (Z 큼) — DUT 내부 결과를 덮지 않게
- testbench가 vin/vout을 명확히 분리: vin은 외부 drive, vout은 sense only

### 3.5 한 IP에 여러 agent — 의미 단위 분리

한 ADC IP에도 보통 여러 agent가 붙습니다 — analog input agent, vref agent, register agent, irq agent. agent끼리는 **cross-talk 없이 독립적**이고, scoreboard 또는 virtual sequence가 cross-domain 조율을 합니다.

```systemverilog
class adc_env extends uvm_env;
  adc_input_agent  ain;       // analog input (vin, vref)
  adc_reg_agent    reg_a;     // APB/AXI to ADC regs (RAL)
  adc_irq_agent    irq_a;     // eoc IRQ
  adc_output_mon   omon;      // code stream (passive)
  adc_scoreboard   sb;
  adc_virt_seq     vseq;      // 시나리오 조율
endclass
```

> agent를 너무 잘게 쪼개면 wiring 복잡도가 폭증합니다. **"하나의 의미 단위 인터페이스 = 한 agent"**를 기준으로, analog signal과 register는 서로 다른 의미라 분리합니다.

## 4. Sequence Layering — Virtual + Cross-Domain

mixed-signal 시나리오는 보통 **여러 도메인의 동기**가 필요합니다. "register write → analog ramp 시작 → settled까지 대기 → 결과 읽기" 같은 흐름을 한 sequence가 다 짊어지면 가독성·재사용성이 나빠집니다.

```d2
direction: down

vseq: "virtual sequence\n(scenario)"
reg_seq1: "reg seq\n\"trim_bg = 0x12\""
analog_seq: "analog seq\n\"apply 1 MHz sine, 0.5 V\""
reg_seq2: "reg seq\n\"enable = 1\""
wait_irq: "wait IRQ \"eoc\""

vseq -> reg_seq1
vseq -> analog_seq
vseq -> reg_seq2
vseq -> wait_irq
```

### 4.1 4가지 계층

| 계층 | 역할 | 예시 |
|---|---|---|
| primitive sequence | 한 agent에 1 transaction | "vin = 1.2 V" 한 줄 |
| compound sequence | 한 agent에 여러 transaction | "0 V → 1.8 V ramp 1 ms" |
| **virtual sequence** | 여러 agent 조율 | "trim → ramp → eoc 대기" |
| test sequence | chip-wide 시나리오 | "power-on → boot → ADC bring-up" |

### 4.2 Virtual sequence — 여러 도메인 동기

virtual sequence는 **여러 agent의 sequencer 핸들**을 들고 있고, 각 sub-seq를 적절한 sequencer로 보냅니다.

```systemverilog
class adc_bringup_vseq extends uvm_sequence;
  virtual adc_env_cfg cfg;          // env config (sequencer 핸들 포함)

  task body();
    reg_write_seq w;
    adc_ramp_seq  r;
    irq_wait_seq  i;

    // 1) trim 값 셋업 (register agent)
    w = reg_write_seq::type_id::create("w_trim");
    w.addr = ADC_TRIM_ADDR; w.data = 'h12;
    w.start(cfg.reg_sqr);

    // 2) enable=1, start=0
    w = reg_write_seq::type_id::create("w_en");
    w.addr = ADC_CTRL_ADDR; w.data = 'b01;
    w.start(cfg.reg_sqr);

    // 3) analog ramp 시작 (analog agent) — 백그라운드
    r = adc_ramp_seq::type_id::create("r_ramp");
    r.vstart = 0.0; r.vend = 1.8; r.T_ns = 100_000; r.steps = 200;
    fork r.start(cfg.adc_sqr); join_none

    // 4) 1 μs 후 start bit 토글
    #1us;
    w = reg_write_seq::type_id::create("w_start");
    w.addr = ADC_CTRL_ADDR; w.data = 'b11;
    w.start(cfg.reg_sqr);

    // 5) eoc IRQ 대기 (irq agent)
    i = irq_wait_seq::type_id::create("i_eoc");
    i.start(cfg.irq_sqr);
  endtask
endclass
```

> virtual sequence에서 sequencer 핸들은 **env_cfg에 모아둡니다**. test가 env_cfg만 채워주면 sub-seq는 어느 sequencer로 갈지 자동. `uvm_config_db`를 sequence에서 직접 fetch하지 말고 cfg object로 inject하는 것이 추적이 쉽습니다.

### 4.3 fork/join 패턴 — 병렬 자극

"supply ramp"와 "analog stim"이 동시에 진행되는 시나리오가 흔합니다.

```systemverilog
task body();
  fork
    begin: SUPPLY
      supply_ramp_seq sr = supply_ramp_seq::type_id::create("sr");
      sr.V_target = 1.8; sr.T_ns = 50_000;
      sr.start(cfg.pwr_sqr);
    end
    begin: STIM
      wait (vif.vdd.V > 1.6);   // supply가 90% 이상 올라온 뒤 시작
      adc_dc_sweep_seq sw = adc_dc_sweep_seq::type_id::create("sw");
      sw.start(cfg.adc_sqr);
    end
  join
endtask
```

> `fork/join_none`으로 백그라운드에 둘 때 sub-seq의 **완료 동기화**를 잊기 쉽습니다. UVM의 `raise_objection/drop_objection`이 모든 sub-seq에 걸려 있어야 phase가 일찍 끝나지 않습니다.

### 4.4 Sequence library와 default

UVM의 `uvm_sequence_library`로 sequence 풀에서 weight 기반 random 선택:

```systemverilog
class adc_seq_lib extends uvm_sequence_library#(adc_item);
  function new(string name = "adc_seq_lib");
    super.new(name);
    selection_mode = UVM_SEQ_LIB_RAND;
    min_random_count = 5;
    max_random_count = 20;
    add_typewide_sequence(adc_dc_seq::get_type());
    add_typewide_sequence(adc_ramp_seq::get_type());
    add_typewide_sequence(adc_sine_seq::get_type());
  endfunction
endclass
```

### 4.5 soft constraint로 default 시나리오

```systemverilog
class adc_item extends uvm_sequence_item;
  rand bit  noise_en;
  rand int  steps_per_cycle;
  constraint c_default {
    soft noise_en        == 0;
    soft steps_per_cycle == 100;
  }
endclass

// noise_test에서 override
class noise_test extends uvm_test;
  task run_phase(uvm_phase phase);
    adc_sine_seq s = adc_sine_seq::type_id::create("s");
    if (!s.randomize() with { noise_en == 1; steps_per_cycle == 200; }) ...;
  endtask
endclass
```

### 4.6 Sequencer arbitration

analog agent의 sequencer가 한 시점에 한 transaction씩만 처리하므로 **여러 sequence가 같은 sequencer에 동시 start**되면 arbitration이 필요합니다.

| 모드 | 동작 |
|---|---|
| `SEQ_ARB_FIFO` | 도착 순서 (default) |
| `SEQ_ARB_WEIGHTED` | sequence priority weight |
| `SEQ_ARB_USER` | 사용자 정의 arbiter |

```systemverilog
adc_sqr.set_arbitration(SEQ_ARB_WEIGHTED);
my_seq.set_priority(200);    // default 100
```

### 4.7 Good vs Bad 패턴 한 표

| 패턴 | OK | NG |
|---|---|---|
| cross-domain 시나리오 | virtual sequence + env_cfg | 한 sequence가 직접 config_db 검색 |
| analog stim 종류 분기 | sequence_item의 kind enum | sequence class를 종류별로 폭증 |
| 병렬 자극 | fork + raise objection 동기 | fork_none 후 wait 없음 → race |
| default 동작 | soft constraint | 매 test마다 모든 필드 명시 |
| random 회귀 | uvm_sequence_library + weight | top test가 직접 random 호출 |

## 5. Reference Model — Spec → 예상값

같은 입력에 대해 **spec이 기대하는 출력**을 계산하는 코드. scoreboard가 DUT 관측값과 이걸 비교합니다. digital에선 ISS·golden RTL이 이 자리에 있습니다. mixed-signal에서는 spec의 analog 수식 또는 floating-point 알고리즘이 reference가 됩니다.

### 5.1 세 가지 reference 패턴

| 패턴 | 구현 | 장점 | 단점 |
|---|---|---|---|
| **inline SV** | SV function/task 안에 spec 수식 | self-contained, 빠름, debug 쉬움 | 복잡한 numerical은 부담 |
| **DPI-C** | C 함수 호출, `pure` import | 표준 C 수학 라이브러리, FFT/필터 가능 | 빌드 의존성, debug 복잡 |
| **co-sim** | MATLAB / Python / external sim | 알고리즘 그대로 사용 | regression overhead, sync 비용 |

### 5.2 inline SV — 가장 단순한 ref

```systemverilog
// ADC ideal code = round(vin / Vref × 2^N)
function automatic int adc_ref(real vin, real vref, int N);
  real q;
  if (vin <= 0.0) return 0;
  if (vin >= vref) return (1<<N) - 1;
  q = (vin / vref) * (1<<N);
  return $rtoi(q + 0.5);
endfunction

// PLL 출력 주파수 = f_ref * (M/N)
function automatic real pll_ref(real f_ref, int M, int N);
  return f_ref * real'(M) / real'(N);
endfunction
```

장점은 명료성. **spec 한 줄 = 코드 한 줄**이라 scoreboard fail 시 비교가 쉽습니다. 단점은 LPF, FFT 같은 복잡 알고리즘이 들어가면 코드가 길어지고 numerical 정확도 관리가 어렵습니다.

### 5.3 DPI-C — 수학 라이브러리 활용

```systemverilog
// ref.h:  double adc_filter_ref(double *in, int n, double fc_norm);

import "DPI-C" pure function real adc_filter_ref(input real in_arr[],
                                                  input int  n,
                                                  input real fc_norm);

real samples[1024];
real out = adc_filter_ref(samples, 1024, 0.1);
```

> `import "DPI-C" **pure**`는 부작용 없는 순수 함수임을 simulator에 알립니다 (cache 가능, 결정성 보장). 상태가 있는 ref(시간 누적 필터)는 `pure`를 빼고 race-free 보장을 별도로 합니다.

### 5.4 co-sim ref — MATLAB / Python

DSP 알고리즘이 MATLAB/Python으로 이미 작성된 경우, 그 코드를 그대로 reference로 쓰면 spec → ref → DUT 동등성 체인이 짧아집니다. 대신 inter-process 통신 overhead가 발생합니다.

**옵션 A: 사전 산출** — seed별로 입력 파형을 MATLAB으로 미리 돌려 csv 출력 → SV가 file read

```systemverilog
int ref_codes[];
$readmemh("ref/adc_ref_seed_42.hex", ref_codes);
foreach (ref_codes[i]) begin
  adc_item it = adc_item::type_id::create($sformatf("it_%0d", i));
  it.code_expected = ref_codes[i];
  // ...
end
```

regression overhead 없음 (사전 계산만). 새 stimulus pattern마다 사전 계산 필요.

### 5.5 analog spec 수식의 numerical 한계

spec의 수식을 SV로 그대로 옮기면 **round-off · catastrophic cancellation**이 발생할 수 있습니다. 결과의 의미가 spec과 같아도 ref가 잘못된 숫자를 뱉으면 DUT가 옳아도 mismatch.

- 두 큰 값의 빼기 — `(1e9 + 1.0) - 1e9`가 0이 될 수 있음
- log/exp 누적 — `$log10(1 + x)`는 `log1p` 패턴이 안전 (DPI-C로 처리)
- 삼각함수 인자가 큰 정수 배수 → phase wrap 누적
- divide by zero 보호 (`vref < eps`로 가드)

### 5.6 Per-corner reference

spec이 process / voltage / temperature에 따라 다른 값을 갖는 경우 (gain, offset 등), ref도 PVT corner 정보를 받아야 합니다.

```systemverilog
typedef enum {SS_LO_LO, TT_TYP, FF_HI_HI} pvt_e;

function automatic int adc_ref_pvt(real vin, real vref, int N, pvt_e pvt);
  real offset;
  case (pvt)
    SS_LO_LO: offset = -2.0e-3;
    TT_TYP:   offset =  0.0;
    FF_HI_HI: offset = +1.5e-3;
  endcase
  return adc_ref(vin + offset, vref, N);
endfunction
```

### 5.7 Reference의 own bug — safety net

scoreboard fail의 30~50%가 실제로는 reference 또는 scoreboard bug라고 보고됩니다 (DVCon paper 평균치). 안전장치:

- 두 reference 구현(SV inline + DPI)을 cross-check하는 회귀를 둠
- spec 수식 직접 인용을 코드 주석에 남김 (page/equation 번호)
- known-good vector(spec example)로 reference 단독 unit test
- reference도 PR 리뷰의 대상

### 5.8 Spec reference vs Golden Spice — 헷갈리지 말 것

UVM scoreboard는 보통 **spec reference**(이상적 동작) 기준으로 비교하고, **golden Spice**(실측에 가까운 모델)는 별도 corner spot check에서 RNM의 신뢰 범위를 확인하는 데 씁니다. 둘을 한 scoreboard에 섞지 마세요.

```d2
direction: right

inputs: "Inputs\n(sequence_item)"
reference: "reference\n(spec 수식)"
dut_rnm: "DUT (RNM model)"
dut_spice: "DUT (Spice netlist, opt)"
expected: "expected"
observed_rnm: "observed_rnm\n← nightly regression"
observed_spice: "observed_spice\n← spot check only"

inputs -> reference -> expected
inputs -> dut_rnm -> observed_rnm
inputs -> dut_spice -> observed_spice
```

> reference 검증은 **verification의 검증**입니다. 새 IP를 받으면 가장 먼저 reference만으로 spec example sweep을 돌리고 결과를 spec PDF의 표·그래프와 손으로 비교하는 것이 첫 단계. 이걸 생략하면 모든 회귀 결과의 의미가 불확실해집니다.

## 6. Scoreboard — Tolerance · Multi-rate · Ref 통합

digital scoreboard는 `==` 한 줄로 끝납니다. analog는 다릅니다. 모든 비교에 **tolerance + 시간 정렬 + reference 변환**이 필요하고, `==`를 쓰면 fail이 폭발합니다. 좋은 mixed-signal scoreboard는 다음 4가지를 갖춥니다.

- **① Tolerance compare** — spec의 abs/rel tolerance를 명시. `$abs(exp-obs) ≤ abs_tol + rel_tol × |exp|`
- **② Multi-rate sync** — analog mon은 trigger-driven, register mon은 cycle-driven. 두 stream을 시간/시퀀스로 정렬
- **③ Reference model 통합** — 입력 transaction → predicted 출력. SV/DPI/co-sim 중 하나로
- **④ Queue hygiene** — overflow와 timeout 명시

### 6.1 기본 구조

```systemverilog
class adc_scoreboard extends uvm_scoreboard;
  `uvm_component_utils(adc_scoreboard)

  uvm_analysis_imp_in #(adc_item, adc_scoreboard) imp_in;
  uvm_analysis_imp_out#(adc_obs,  adc_scoreboard) imp_out;

  adc_item expected_q[$];        // ref model 예측 결과
  adc_obs  observed_q[$];        // monitor가 잡은 결과

  int unsigned matched, mismatched, ignored;

  real abs_tol = 1e-3;           // 1 mV
  real rel_tol = 5e-3;           // 5 ‰

  function void write_in(adc_item it);
    adc_item pred = predict(it);
    expected_q.push_back(pred);
    try_match();
  endfunction

  function void write_out(adc_obs o);
    observed_q.push_back(o);
    try_match();
  endfunction

  function void try_match();
    while (expected_q.size() && observed_q.size())
      compare_one(expected_q.pop_front(), observed_q.pop_front());
  endfunction
endclass
```

### 6.2 비교 함수 — tolerance + reason

```systemverilog
function void adc_scoreboard::compare_one(adc_item e, adc_obs o);
  real diff  = $abs(e.vin_volt - o.vin_sampled);
  real allow = abs_tol + rel_tol * $abs(e.vin_volt);
  int  code_diff = e.code_expected - o.code;

  if (diff > allow) begin
    mismatched++;
    `uvm_error("SB",
      $sformatf("VIN exp=%0.6f obs=%0.6f diff=%0.6f allow=%0.6f",
                e.vin_volt, o.vin_sampled, diff, allow))
  end else if ($abs(code_diff) > 1) begin
    mismatched++;
    `uvm_error("SB",
      $sformatf("CODE exp=%0d obs=%0d diff=%0d", e.code_expected, o.code, code_diff))
  end else begin
    matched++;
  end
endfunction
```

> 비교 실패 메시지에 항상 **expected · observed · tolerance · 시간**을 동시에 출력하세요. debug 첫 단서가 줄어듭니다. `%0.6f`로 precision 명시 — default `%f`는 6자리 라운딩으로 fail 원인을 가립니다.

### 6.3 Multi-rate 동기 — analog와 register stream

analog monitor는 zero-cross/settled 같은 sparse event, register agent는 매 access마다 transaction. 한 scoreboard 안에서 두 stream을 정렬하려면 **matching key**가 필요합니다 — 보통 시간 또는 일련번호.

```systemverilog
class pll_scoreboard extends uvm_scoreboard;
  pll_lock_obs lock_q[$];
  reg_obs      reg_q[$];

  function void try_match();
    while (lock_q.size() && reg_q.size()) begin
      // "register write 이후 첫 lock 이벤트가 100 us 안에 들어와야"
      if (lock_q[0].t_ns < reg_q[0].t_ns) begin
        `uvm_error("SB", "lock without prior trigger")
        void'(lock_q.pop_front());
      end else if (lock_q[0].t_ns - reg_q[0].t_ns < 100_000) begin
        check_lock(lock_q.pop_front(), reg_q.pop_front());     // matched
      end else begin
        `uvm_error("SB", "register write but no lock in time")
        void'(reg_q.pop_front());
      end
    end
  endfunction
endclass
```

### 6.4 Queue overflow와 timeout

- 한쪽 queue가 한없이 자라면 ref model이 못 따라가거나 monitor가 죽었다는 신호 → 임계치(예: 1000개) 초과 시 fatal
- match가 일정 시간 안에 안 오면 timeout fail — analog는 sparse event라 timeout이 매우 흔한 fail 원인
- phase 종료 직전 두 queue가 비어있는지 check — drain phase에서 fail 보고

```systemverilog
function void adc_scoreboard::check_phase(uvm_phase phase);
  if (expected_q.size() > 0)
    `uvm_error("SB", $sformatf("%0d expected without observed at EOT", expected_q.size()))
  if (observed_q.size() > 0)
    `uvm_error("SB", $sformatf("%0d observed without expected at EOT", observed_q.size()))
  `uvm_info("SB",
    $sformatf("Final: matched=%0d mismatched=%0d ignored=%0d",
              matched, mismatched, ignored), UVM_LOW)
endfunction
```

### 6.5 Ordering 가정의 위험

위험 가정 — sequence n번째 → observed n번째 — analog drop/추가 한 번이면 모두 어긋남.

```systemverilog
// id 기반 hash matching
adc_item expected_h[int];
adc_obs  observed_h[int];

function void try_match_by_id();
  foreach (expected_h[id])
    if (observed_h.exists(id)) begin
      compare_one(expected_h[id], observed_h[id]);
      expected_h.delete(id);
      observed_h.delete(id);
    end
endfunction
```

### 6.6 Pass/Fail 정의의 명시화

분석 endpoint에서 단순한 mismatch count만 보는 것은 위험합니다.

- **mismatch_count == 0** 이상으로, **최소 hit count**도 확인
- **OOB 입력**은 ignore할지 fail할지 명시
- **noise 회귀**는 mismatch 허용 범위가 다르므로 별도 mode
- **functional coverage** 100%도 동시에 충족 — 도달도 + 검증도 합의

```systemverilog
function void adc_scoreboard::report_phase(uvm_phase phase);
  bit pass = 1;
  if (mismatched > 0)            pass = 0;
  if (matched < 100)             pass = 0;     // 회귀 의미 sanity
  if (cg.get_coverage() < 95.0)  pass = 0;
  if (pass) `uvm_info("RES", "PASS", UVM_NONE)
  else      `uvm_error("RES", "FAIL")
endfunction
```

> analog scoreboard는 **fail의 책임 소재**가 모호할 수 있습니다 — DUT bug? RNM model bug? reference 수식 오류? scoreboard tolerance 잘못? fail 시 빠르게 좁히려면 **같은 입력으로 다른 reference에 돌렸을 때 결과**를 cross-check할 도구가 있어야 합니다 — Ch10 §8.5의 5가지 실험 표를 scoreboard fail 대응 SOP로 두세요.

## 7. 대표 문제 — ADC IP env 설계 한 페이지

### 문제

다음 요구의 ADC IP env를 설계하시오:

- 12-bit SAR ADC, Vref = 1.8 V, sample rate 1 MHz
- 입력 시나리오: DC sweep, ramp, sine (1k Hz ~ 100 kHz), noise on/off
- DUT 모델: RNM (default) / Spice cosim (corner spot check) swap 가능
- Register: trim(8b), enable(1b), start(1b), eoc IRQ
- Scoreboard: tolerance 1 LSB 또는 vin tolerance ±2 mV
- Coverage: vin bin, code bin, transition, PVT cross

### 풀이 (skeleton)

```systemverilog
// env_cfg
class adc_env_cfg extends uvm_object;
  rand bit               noise_en;
  rand int               noise_seed;
  rand pvt_e             pvt;
  string                 model_kind;   // "RNM" / "SPICE"
  real                   abs_tol = 2e-3;
  real                   rel_tol = 0;
  adc_sequencer          adc_sqr;       // virtual sequencer가 보는 핸들
  uvm_sequencer          reg_sqr;
  uvm_sequencer          irq_sqr;
endclass

// env
class adc_env extends uvm_env;
  adc_env_cfg     cfg;
  adc_input_agent ain;
  reg_agent       reg_a;
  irq_agent       irq_a;
  adc_output_mon  omon;
  adc_scoreboard  sb;
  adc_virt_seq    vseq;

  function void build_phase(uvm_phase phase);
    uvm_config_db#(adc_env_cfg)::get(this, "", "cfg", cfg);
    // ... factory create + config_db pass-down
  endfunction
endclass

// virtual sequence: bringup → sweep
class adc_full_vseq extends uvm_sequence;
  virtual adc_env_cfg cfg;
  task body();
    // power-on + trim + enable (reg_agent)
    // DC sweep 32 points → ramp 1ms → sine 1MHz (analog_agent)
    // eoc IRQ 대기 (irq_agent)
  endtask
endclass

// scoreboard
class adc_scoreboard extends uvm_scoreboard;
  function void compare_one(...);
    // abs_tol = 2 mV, code |diff| ≤ 1
    // fail message: exp/obs/diff/allow/time
  endfunction
  function void report_phase(...);
    // mismatch==0 && matched>=100 && cg>=95% && coverage cross 통과
  endfunction
endclass
```

핵심 설계 결정:

- **DUT wrapper의 RNM/SPICE swap**은 `+define+ADC_MODEL_RNM` 같은 build option, env_cfg.model_kind는 메시지/로그용
- **virtual sequence가 chip-wide 시나리오 한 곳에 모음** — 각 sub-seq는 작은 단위로 재사용
- **interface 안에 ramp/sine/step helper task** — driver는 한 줄 호출, vendor 호환성도 좋아짐
- **scoreboard fail SOP** — Ch10 §8.5의 5가지 실험 표를 scoreboard 코드 주석에 링크해서 첫 한 시간 안에 책임 소재 좁히기

## 8. 핵심 정리

1. UVM-DMS env = digital UVM env + **analog agent · DUT wrapper · ref model · tolerance scoreboard**
2. Virtual interface에 nettype 신호 + **inline helper task** (ramp/sine/step) 모음
3. Analog agent는 **driver/monitor 비대칭** — sequence_item에 kind enum, driver는 vif task에 위임
4. Virtual sequence가 cross-domain 시나리오 조율 — sequencer 핸들은 env_cfg에 모아둠
5. Reference model 3 패턴: inline SV / DPI-C / co-sim. **safety net 의무** (spec example unit test)
6. Scoreboard는 **tolerance + multi-rate sync + queue hygiene + 명시적 pass criteria**
7. IP env → SoC env 합성을 처음부터 가정, config object로 외부 override 가능하게
8. DUT wrapper는 RNM/Spice/stub abstraction switching 가능하게 작성

## 더 읽을거리

- 이전: [Ch11. 도구 지형](../11_tools_ecosystem/)
- 함정·debug·coverage 전략: [Ch10. RNM/AMS 검증 방법론](../10_verification_methodology/)
- 언어 도구 (real · nettype · SVA on real): [Ch05. RNM with SystemVerilog](../05_rnm_systemverilog/)
- 다음: [Appendix D. Analog IP Catalogue](../appendix_d_analog_ip_catalogue/)
- 퀴즈: [Ch12 퀴즈](../quiz/ch12_quiz/)
