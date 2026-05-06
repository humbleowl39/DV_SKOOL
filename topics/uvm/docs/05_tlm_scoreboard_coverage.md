# Module 05 — TLM, Scoreboard, Coverage

<div class="learning-meta">
  <span class="meta-badge meta-level-advanced">📊 Advanced</span>
</div>

!!! objective "학습 목표"
    이 모듈을 마치면:

    - **Connect** Monitor의 `analysis_port`를 Scoreboard와 Coverage 양쪽에 1:N broadcast로 연결할 수 있다.
    - **Implement** in-order / out-of-order 트래픽에 맞는 Scoreboard 비교 로직을 작성할 수 있다.
    - **Define** covergroup with coverpoints, bins, cross로 의미 있는 functional coverage를 정의할 수 있다.
    - **Trigger** Monitor의 write 콜백에서 covergroup `sample()`을 호출해 sampling 시점을 명확히 할 수 있다.
    - **Plan** Coverage closure 전략 (시드 다양성 + 타겟 시퀀스 + cross 분석)을 설계할 수 있다.

!!! info "사전 지식"
    - [Module 01-04](01_architecture_and_phase.md)
    - SystemVerilog covergroup, coverpoint, cross 문법 (IEEE 1800 §19)

## 왜 이 모듈이 중요한가

TB의 **검증 가치**는 두 곳에서 생성됩니다: **비교(Scoreboard)** 로 결함을 발견하고, **커버리지(Coverage)** 로 검증 완전성을 측정합니다. 둘 다 TLM 위에서 동작하므로 Analysis Port 연결이 잘못되면 두 기능 모두 무력해집니다. 특히 OoO 응답을 가진 프로토콜(AXI ID, PCIe TLP tag)에서는 Scoreboard 매칭 로직 설계가 검증 신뢰성의 핵심입니다.

## 핵심 개념
**TLM = 컴포넌트 간 트랜잭션 레벨 통신. Analysis Port로 Monitor→Scoreboard/Coverage에 broadcast. Scoreboard는 DUT 출력과 기대값을 비교하여 Pass/Fail 판정. Coverage는 검증 완전성을 정량적으로 측정.**

---

## TLM (Transaction Level Modeling)

### Analysis Port (1:N Broadcast)

```
Monitor에서 수집한 Transaction을 여러 구독자에게 동시 전달:

  Monitor
    |
    | ap.write(item)
    |
    +──→ Scoreboard (비교)
    |
    +──→ Coverage Collector (커버리지 수집)
    |
    +──→ Protocol Checker (프로토콜 검증)

1:N 관계 — 구독자 추가/제거가 Monitor에 영향 없음
```

### TLM 포트 연결 (connect_phase)

```systemverilog
// Env의 connect_phase
function void connect_phase(uvm_phase phase);
  // Monitor → Scoreboard
  agent.monitor.ap.connect(scoreboard.expected_export);

  // Monitor → Coverage
  agent.monitor.ap.connect(coverage.analysis_export);
endfunction
```

### 주요 TLM 포트 타입

| 포트 | 방향 | 용도 |
|------|------|------|
| `uvm_analysis_port` | 송신 (write) | Monitor가 Transaction broadcast |
| `uvm_analysis_imp` | 수신 (write 구현) | Scoreboard/Coverage가 수신 |
| `uvm_analysis_export` | 중간 전달 | 계층 경유 시 사용 |
| `uvm_seq_item_port` | 양방향 | Sequencer ↔ Driver |

### uvm_tlm_analysis_fifo — 비동기 수신의 핵심

```systemverilog
// 문제: uvm_analysis_imp의 write()는 function → 시간 소비 불가
//       Scoreboard에서 비교 로직이 복잡하거나 시간이 필요한 경우?

// 해결: uvm_tlm_analysis_fifo로 버퍼링 후 task에서 처리
class my_scoreboard extends uvm_scoreboard;
  `uvm_component_utils(my_scoreboard)

  // FIFO: Analysis Port로부터 수신 → 내부 큐에 버퍼링
  uvm_tlm_analysis_fifo #(my_item) expected_fifo;
  uvm_tlm_analysis_fifo #(my_item) actual_fifo;

  function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    expected_fifo = new("expected_fifo", this);
    actual_fifo   = new("actual_fifo", this);
  endfunction

  // Env에서 연결:
  //   input_monitor.ap.connect(scoreboard.expected_fifo.analysis_export);
  //   output_monitor.ap.connect(scoreboard.actual_fifo.analysis_export);

  task run_phase(uvm_phase phase);
    my_item expected, actual;
    forever begin
      // blocking get — 데이터가 올 때까지 대기 (task이므로 가능)
      expected_fifo.get(expected);
      actual_fifo.get(actual);

      if (!actual.compare(expected)) begin
        `uvm_error("SB", $sformatf("Mismatch!\n  Exp: %s\n  Act: %s",
                   expected.convert2string(), actual.convert2string()))
      end
    end
  endtask
endclass
```

### analysis_imp vs analysis_fifo 비교

```
uvm_analysis_imp:
  ┌──────────┐     write()      ┌──────────┐
  │ Monitor  │ ───────────────→ │Scoreboard│
  └──────────┘   (function)     └──────────┘
  - write()는 function → 시간 소비(#, @) 불가
  - Monitor의 run_phase 안에서 직접 호출됨
  - 단순한 비교에 적합

uvm_tlm_analysis_fifo:
  ┌──────────┐     write()      ┌──────┐   get()   ┌──────────┐
  │ Monitor  │ ───────────────→ │ FIFO │ ────────→ │Scoreboard│
  └──────────┘   (function)     └──────┘  (task)    └──────────┘
  - FIFO가 중간에서 버퍼링
  - Scoreboard의 run_phase에서 get() (task) → 시간 제어 가능
  - Monitor와 Scoreboard가 완전 비동기 (디커플링)
  - ★ 실무에서 가장 많이 사용하는 패턴

사용 지침:
  - 단순 카운터/플래그 업데이트 → analysis_imp
  - 비교 로직, 순서 대기, 복잡한 처리 → analysis_fifo
  - 다중 포트 수신 후 매칭 → analysis_fifo (필수)
```

---

## Scoreboard — 결과 비교

### 기본 Scoreboard 구조

```systemverilog
class my_scoreboard extends uvm_scoreboard;
  `uvm_component_utils(my_scoreboard)

  // TLM 수신 포트
  uvm_analysis_imp #(my_item, my_scoreboard) actual_export;

  // 기대값 큐
  my_item expected_queue[$];

  function void build_phase(uvm_phase phase);
    actual_export = new("actual_export", this);
  endfunction

  // Reference Model로 기대값 추가
  function void add_expected(my_item item);
    expected_queue.push_back(item);
  endfunction

  // DUT 출력 수신 시 비교
  function void write(my_item actual);
    my_item expected;

    if (expected_queue.size() == 0) begin
      `uvm_error("SB", "Unexpected transaction received")
      return;
    end

    expected = expected_queue.pop_front();

    if (!actual.compare(expected)) begin
      `uvm_error("SB", $sformatf(
        "Mismatch!\n  Expected: %s\n  Actual:   %s",
        expected.sprint(), actual.sprint()))
    end else begin
      `uvm_info("SB", "Match!", UVM_HIGH)
    end
  endfunction

  // check_phase: 잔여 항목 확인
  function void check_phase(uvm_phase phase);
    if (expected_queue.size() > 0)
      `uvm_error("SB", $sformatf("%0d expected items remaining",
                                  expected_queue.size()))
  endfunction
endclass
```

### Dual-Port Scoreboard (입출력 비교)

```
Input Monitor → Scoreboard (기대값 생성)
Output Monitor → Scoreboard (실제값 수신)

class dual_scoreboard extends uvm_scoreboard;
  `uvm_analysis_imp_decl(_input)
  `uvm_analysis_imp_decl(_output)

  uvm_analysis_imp_input  #(in_item, dual_scoreboard) in_export;
  uvm_analysis_imp_output #(out_item, dual_scoreboard) out_export;

  function void write_input(in_item item);
    // Reference Model로 기대 출력 계산
    out_item expected = ref_model.predict(item);
    expected_queue.push_back(expected);
  endfunction

  function void write_output(out_item actual);
    // 기대값과 비교
    ...
  endfunction
endclass
```

### In-Order vs Out-of-Order 비교 전략

```
In-Order Scoreboard:
  expected_queue[$]에 push_back → pop_front로 순서대로 비교
  → DUT가 입력 순서 = 출력 순서를 보장할 때 (FIFO, 단순 파이프라인)

Out-of-Order Scoreboard:
  expected를 Associative Array에 저장 → 키(ID/addr)로 매칭
  → DUT가 순서를 보장하지 않을 때 (AXI reordering, 캐시, 멀티포트)
```

```systemverilog
// --- Out-of-Order Scoreboard 구현 ---
class ooo_scoreboard extends uvm_scoreboard;
  `uvm_component_utils(ooo_scoreboard)

  // 키 = transaction ID, 값 = 기대 트랜잭션
  my_item expected_map[int];
  int match_count, mismatch_count;

  uvm_tlm_analysis_fifo #(my_item) exp_fifo;
  uvm_tlm_analysis_fifo #(my_item) act_fifo;

  function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    exp_fifo = new("exp_fifo", this);
    act_fifo = new("act_fifo", this);
  endfunction

  task run_phase(uvm_phase phase);
    fork
      collect_expected();
      compare_actual();
    join
  endtask

  task collect_expected();
    my_item exp;
    forever begin
      exp_fifo.get(exp);
      expected_map[exp.id] = exp;  // ID를 키로 저장
    end
  endtask

  task compare_actual();
    my_item act, exp;
    forever begin
      act_fifo.get(act);

      if (!expected_map.exists(act.id)) begin
        `uvm_error("SB", $sformatf("No expected item for ID=%0d", act.id))
        continue;
      end

      exp = expected_map[act.id];
      expected_map.delete(act.id);

      if (!act.compare(exp)) begin
        `uvm_error("SB", $sformatf("Mismatch ID=%0d\n  Exp: %s\n  Act: %s",
                   act.id, exp.convert2string(), act.convert2string()))
        mismatch_count++;
      end else begin
        match_count++;
      end
    end
  endtask

  function void check_phase(uvm_phase phase);
    if (expected_map.size() > 0)
      `uvm_error("SB", $sformatf("%0d unmatched expected items", expected_map.size()))
    `uvm_info("SB", $sformatf("Match=%0d, Mismatch=%0d", match_count, mismatch_count), UVM_LOW)
  endfunction
endclass
```

### Scoreboard 전략 선택 가이드

| DUT 특성 | Scoreboard 전략 | 키 |
|----------|----------------|-----|
| FIFO, 단순 파이프라인 | In-Order (Queue) | 순서 자체 |
| AXI (OOO 허용) | Out-of-Order (Map) | AXI ID |
| 캐시 | Out-of-Order (Map) | Address |
| DMA (채널별 순서 보장) | Per-Channel In-Order | Channel ID + Queue |
| 패킷 프로세서 | Out-of-Order (Map) | Packet ID / Hash |

---

## Functional Coverage

### Covergroup 기본

```systemverilog
class my_coverage extends uvm_subscriber #(my_item);
  `uvm_component_utils(my_coverage)

  covergroup cg;
    // Coverpoint: 관심 변수
    cp_opcode: coverpoint item.opcode {
      bins read  = {READ};
      bins write = {WRITE};
      bins burst = {BURST_READ, BURST_WRITE};
    }

    cp_size: coverpoint item.size {
      bins small  = {[1:64]};
      bins medium = {[65:512]};
      bins large  = {[513:4096]};
    }

    cp_addr_region: coverpoint item.addr[31:28] {
      bins low    = {[4'h0:4'h3]};
      bins mid    = {[4'h4:4'h7]};
      bins high   = {[4'h8:4'hF]};
    }

    // Cross: 조합 커버리지
    cx_opcode_size: cross cp_opcode, cp_size;
    cx_opcode_addr: cross cp_opcode, cp_addr_region;
  endgroup

  my_item item;

  function new(string name, uvm_component parent);
    super.new(name, parent);
    cg = new();
  endfunction

  function void write(my_item t);
    item = t;
    cg.sample();  // 커버리지 샘플링
  endfunction
endclass
```

### Covergroup Option — 세밀한 제어

```systemverilog
covergroup cg with function sample(my_item item);

  // --- Covergroup-level option ---
  option.per_instance = 1;     // 인스턴스별 개별 커버리지 추적
  option.goal = 95;            // 목표 커버리지 95% (기본 100)
  option.comment = "AXI Transaction Coverage";

  // --- Coverpoint-level option ---
  cp_opcode: coverpoint item.opcode {
    option.at_least = 10;      // 각 bin 최소 10회 hit 필요 (기본 1)
    option.auto_bin_max = 8;   // 자동 bin 최대 개수 제한

    bins read  = {READ};
    bins write = {WRITE};
  }

  cp_size: coverpoint item.size {
    option.weight = 2;         // 이 coverpoint의 가중치 2배
    bins small  = {[1:64]};
    bins medium = {[65:512]};
    bins large  = {[513:4096]};
  }
endgroup
```

### 주요 Covergroup/Coverpoint Option

| Option | Level | 기본값 | 설명 |
|--------|-------|--------|------|
| `at_least` | CG/CP | 1 | bin이 "hit"으로 인정되는 최소 샘플 수 |
| `auto_bin_max` | CG/CP | 64 | 명시적 bin 없을 때 자동 생성되는 최대 bin 수 |
| `goal` | CG/CP | 100 | 목표 커버리지 % (보고용) |
| `weight` | CG/CP | 1 | 전체 커버리지 계산 시 가중치 |
| `per_instance` | CG | 0 | 1이면 인스턴스별 독립 추적 |
| `cross_auto_bin_max` | CG | — | Cross의 자동 bin 수 제한 (폭발 방지) |

### Transition Coverage — 상태 전이 추적

```systemverilog
covergroup fsm_cg with function sample(state_e cur_state);

  // 단일 상태 커버리지
  cp_state: coverpoint cur_state {
    bins idle     = {IDLE};
    bins active   = {ACTIVE};
    bins burst    = {BURST};
    bins error    = {ERROR};
  }

  // ★ Transition bins — 상태 전이 경로 추적
  cp_transition: coverpoint cur_state {
    // 단일 전이: A → B
    bins idle_to_active  = (IDLE   => ACTIVE);
    bins active_to_burst = (ACTIVE => BURST);
    bins active_to_idle  = (ACTIVE => IDLE);
    bins error_to_idle   = (ERROR  => IDLE);

    // 연속 전이: A → B → C
    bins full_burst = (IDLE => ACTIVE => BURST);

    // 반복 전이: A → A (연속 N회)
    bins active_held = (ACTIVE [*3:5]);  // 3~5회 연속 ACTIVE

    // Wildcard 전이: 임의 → 특정
    bins any_to_error = (default => ERROR);

    // Illegal 전이: 발생하면 안 되는 전이
    illegal_bins idle_to_error = (IDLE => ERROR);
  }
endgroup

// 사용: 매 클럭마다 sample
always @(posedge clk) begin
  fsm_cg.sample(dut.current_state);
end
```

### Wildcard, Illegal, Ignore Bins 실전 예제

```systemverilog
covergroup protocol_cg;
  cp_cmd: coverpoint item.cmd {
    // Wildcard bins: 비트 패턴 매칭 (? = don't care)
    wildcard bins write_any = {4'b01??};  // 0100, 0101, 0110, 0111
    wildcard bins read_any  = {4'b10??};  // 1000, 1001, 1010, 1011

    // Illegal bins: 발생 시 시뮬레이션 에러
    illegal_bins reserved = {4'b1111, 4'b0000};
    // → 프로토콜에서 금지된 값 검출 (자동 assertion 역할)

    // Ignore bins: 커버리지 계산에서 제외
    ignore_bins debug_only = {4'b1110};
    // → 디버그 모드 전용 명령은 커버리지 목표에서 제외
  }

  cp_resp: coverpoint item.resp {
    bins okay   = {RESP_OKAY};
    bins exokay = {RESP_EXOKAY};
    bins slverr = {RESP_SLVERR};
    bins decerr = {RESP_DECERR};

    // illegal_bins로 DUT 에러 자동 검출
    illegal_bins undefined = default;
    // → 정의된 4개 이외의 값이 나오면 에러
  }

  // Cross에서 특정 조합 제외
  cx_cmd_resp: cross cp_cmd, cp_resp {
    ignore_bins write_exokay = binsof(cp_cmd.write_any) &&
                               binsof(cp_resp.exokay);
    // → exclusive access가 아닌 write에서 EXOKAY는 불가
  }
endgroup
```

### Coverage 설계 원칙

| 원칙 | 설명 |
|------|------|
| 의미 있는 Bin | 프로토콜/기능 관점에서 의미 있는 분류 |
| Cross 필수 | 단일 변수보다 **조합**이 버그를 찾음 |
| Illegal Bin | `illegal_bins`로 불법 값/전이 자동 검출 (assertion 대용) |
| Ignore Bin | `ignore_bins`로 불필요한 조합 제외 (커버리지 목표 현실화) |
| 경계값 포함 | min, max, 경계 ±1 |
| Transition 필수 | FSM 상태 전이, 프로토콜 시퀀스 검증 |
| at_least 조정 | 중요 시나리오는 `at_least > 1`로 반복 검증 |
| Cross 폭발 방지 | `cross_auto_bin_max`, `ignore_bins`로 불필요 조합 제거 |

### Coverage Closure 전략

```
1. Directed Smoke (seed=0) → 기본 경로 확인 → ~30%
2. Configuration Sweep → 설정 조합 자동 생성 → ~60%
3. Constrained Random (100+ seeds) → 코너 케이스 → ~85%
4. Coverage Hole 분석 → 미커버 bin 확인 → Directed 추가 → ~95%
5. Edge Case Directed → 경계값, 에러 → ~100%

미도달 Coverage 분석:
  - Unreachable: 설계상 불가능 → waive
  - Missing scenario: Sequence 추가
  - Constraint 과다: Constraint 완화
```

---

## Q&A

**Q: Analysis Port를 왜 사용하는가?**
> "1:N broadcast가 핵심이다. Monitor가 한 번 write하면 Scoreboard, Coverage, Protocol Checker 등 모든 구독자가 동시에 수신한다. 구독자 추가/제거가 Monitor 코드에 영향을 주지 않으므로 독립적으로 확장 가능하다. 또한 TLM은 Pin-level이 아닌 Transaction-level 통신이므로 시뮬레이션 속도도 빠르다."

**Q: Coverage Cross가 왜 중요한가?**
> "단일 변수의 Coverage 100%는 조합의 Coverage를 보장하지 않는다. 예를 들어 opcode={READ,WRITE} × size={SMALL,LARGE} 각각 100%여도, READ+LARGE 조합이 한 번도 테스트되지 않았을 수 있다. Cross가 이 조합을 추적하여 미커버 조합을 식별한다. 실제 버그는 대부분 특정 조합에서 발생하므로 Cross가 필수적이다."

**Q: Scoreboard에서 check_phase가 필요한 이유는?**
> "시뮬레이션 종료 시 expected_queue에 남아있는 항목이 있으면, DUT가 응답을 생성하지 않았다는 의미이다. run_phase에서는 이를 감지할 수 없고(아직 올 수 있으므로), 모든 시뮬레이션이 끝난 check_phase에서 잔여 항목을 검사해야 한다."

**Q: uvm_analysis_imp 대신 uvm_tlm_analysis_fifo를 쓰는 이유는?**
> "analysis_imp의 write()는 function이므로 시간을 소비할 수 없다. 실무에서 Scoreboard가 두 개 이상의 포트(입력/출력)로부터 데이터를 받아 매칭해야 하는 경우, 한쪽이 먼저 도착하면 다른 쪽을 기다려야 한다. 이 '기다림'은 task에서만 가능하다. analysis_fifo가 중간에서 버퍼링하면 Scoreboard의 run_phase(task)에서 get()으로 blocking 대기할 수 있다. Monitor와 Scoreboard가 완전히 디커플링되는 것도 장점이다."

**Q: In-Order와 Out-of-Order Scoreboard를 어떻게 선택하는가?**
> "DUT의 출력 순서 보장 여부로 결정한다. FIFO나 단순 파이프라인처럼 입력 순서 = 출력 순서이면 In-Order(Queue 기반). AXI처럼 ID별 reordering이 허용되거나 캐시처럼 hit/miss에 따라 출력 순서가 달라지면 Out-of-Order(Associative Array 기반)가 필수이다. 키 선택이 핵심 — AXI는 ID, 캐시는 Address, DMA는 Channel ID가 매칭 키가 된다."

**Q: Transition Coverage가 왜 필요한가?**
> "단순 상태 커버리지는 '모든 상태를 방문했는가'만 확인한다. 하지만 버그는 특정 전이 경로에서 발생한다. 예를 들어 IDLE과 ERROR 상태 모두 커버되더라도, IDLE→ERROR 직접 전이가 한 번도 테스트되지 않았을 수 있다. Transition coverage가 이 경로를 추적하며, illegal transition bins로 FSM 프로토콜 위반도 자동 검출할 수 있다."

**Q: illegal_bins의 실무 활용은?**
> "두 가지 용도가 있다. (1) 프로토콜 위반 검출 — reserved 명령 코드, 정의되지 않은 응답 값 등이 DUT에서 나오면 즉시 에러를 발생시킨다. SVA를 별도로 작성하지 않아도 coverage model 안에서 자동 검증이 된다. (2) illegal transition으로 FSM의 불법 전이를 검출한다. 예를 들어 IDLE에서 ERROR로 직접 전이하면 안 되는 스펙이면, `illegal_bins idle_to_error = (IDLE => ERROR)`로 잡는다."

---

## 연습문제

!!! question "Exercise 1 (Apply, ★)"
    Monitor 1개를 Scoreboard와 Coverage 양쪽에 broadcast 연결하는 코드를 작성하세요.

    ??? answer "모범 답안"
        ```systemverilog
        // monitor
        uvm_analysis_port#(my_item) ap;
        function void build_phase(uvm_phase phase);
          super.build_phase(phase);
          ap = new("ap", this);
        endfunction

        // scoreboard
        uvm_analysis_imp#(my_item, my_sb) actual_imp;
        function void build_phase(uvm_phase phase);
          super.build_phase(phase);
          actual_imp = new("actual_imp", this);
        endfunction
        function void write(my_item it);
          // 비교 로직
        endfunction

        // coverage subscriber
        class my_cov extends uvm_subscriber#(my_item);
          covergroup cg;
            cp_addr: coverpoint item.addr { bins low={[0:'h3FF]}; bins high={['hC00:'hFFF]}; }
          endgroup
          function void write(my_item t);
            this.item = t; cg.sample();
          endfunction
        endclass

        // env connect_phase
        agent.mon.ap.connect(sb.actual_imp);
        agent.mon.ap.connect(cov.analysis_export);
        ```

!!! question "Exercise 2 (Analyze, ★★)"
    in-order Scoreboard(큐 pop_front 비교)를 OoO 트래픽(AXI ID 기반)에 그대로 적용하면 어떤 증상이 나타나는지, 어떻게 수정해야 하는지 답하세요.

    ??? answer "모범 답안"
        - **증상**: Master는 ID=0,1,2 순으로 보냈지만 Slave가 ID=2,0,1 순으로 응답하면 첫 비교부터 mismatch → spurious UVM_ERROR.
        - **수정**: 큐 1개가 아니라 **ID별 큐**(associative array `expected[id][$]`)를 두고, 응답이 오면 `expected[id].pop_front()`와 비교. AXI는 ID 단위 in-order, ID 간 OoO이므로 이 모델이 정합.
        - 일반화: ID/tag/seq_no 같은 매칭 키가 있으면 **per-key 큐**, 없으면 모델로 비교(reference model이 모든 가능 출력 시뮬).

!!! question "Exercise 3 (Create, ★★★)"
    AXI write 트랜잭션에 대해 `addr_region` × `burst_len` cross coverage를 정의하세요. 4 region, burst_len bins {1, [2:4], [5:16]}.

    ??? answer "예시 답안"
        ```systemverilog
        covergroup cg_axi_write;
          cp_region: coverpoint item.addr {
            bins r0 = {[32'h0000_0000:32'h3FFF_FFFF]};
            bins r1 = {[32'h4000_0000:32'h7FFF_FFFF]};
            bins r2 = {[32'h8000_0000:32'hBFFF_FFFF]};
            bins r3 = {[32'hC000_0000:32'hFFFF_FFFF]};
          }
          cp_burst: coverpoint item.burst_len {
            bins single = {1};
            bins short  = {[2:4]};
            bins long   = {[5:16]};
          }
          cross_region_burst: cross cp_region, cp_burst;  // 4 × 3 = 12 bins
        endgroup
        ```

## 핵심 정리

- **Analysis Port = 1:N broadcast**. Monitor 한 곳에서 send → 여러 구독자(SB, Coverage)가 각자 처리.
- **Scoreboard 비교 모델**: in-order는 단일 큐, OoO는 per-key 큐(또는 ID별), 복잡 DUT는 reference model + 출력 비교.
- **Covergroup sampling 시점**: Monitor의 write 콜백에서 `cg.sample()` 호출이 표준. trigger source 명시 안 하면 의도와 다른 시점에 샘플링.
- **Cross coverage**는 단순 합집합이 아니라 곱집합(N × M bins) — 의미 있는 조합만 정의해야 폭발 방지.
- **Coverage closure 전략**: (1) 시드 다양화로 baseline, (2) 타겟 시퀀스로 hole 채움, (3) cross 분석으로 미커버 조합 식별.
- **Pitfall**: Scoreboard는 잡지만 covergroup이 trigger 안 되면 coverage가 0으로 남음 — 둘은 독립이지만 같은 ap에서 fan-out.

## 다음 단계

- 📝 [**Module 05 퀴즈**](quiz/05_tlm_scoreboard_coverage_quiz.md)
- ➡️ [**Module 06 — 실무 패턴 & 안티패턴**](06_practical_patterns.md)

<div class="chapter-nav">
  <a class="nav-prev" href="04_config_db_factory.md">
    <div class="nav-label">◀ 이전</div>
    <div class="nav-title">config_db & Factory</div>
  </a>
  <a class="nav-next" href="06_practical_patterns.md">
    <div class="nav-label">다음 ▶</div>
    <div class="nav-title">UVM 실무 패턴 & 안티패턴</div>
  </a>
</div>
