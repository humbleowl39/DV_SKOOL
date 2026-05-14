# Unit 2 — Design Verification

!!! objective "학습 목표"
    이 모듈을 마치면:

    - **Explain** UVM 의 Phase 모델과 component 계층(Agent / Driver / Monitor / Sequencer / Scoreboard / Env / Test) 의 역할을 설명한다.
    - **Apply** SystemVerilog constraint 로 dynamic array / queue distribution / 패턴 시퀀스를 생성한다.
    - **Design** Monitor 가 sample 한 transaction 을 Scoreboard 가 reference model 과 비교하는 데이터 플로우를 설계한다.
    - **Write** AXI / FIFO / arbiter 에 대한 핵심 SystemVerilog Assertion(SVA)을 작성한다.
    - **Analyze** CDC 검증 시 잡아야 할 메타스테이빌리티 / data coherency / glitch 시나리오를 분류한다.
    - **Evaluate** coverage-driven verification 의 hole 분석 결과를 보고 어떤 test 를 추가할지 우선순위를 결정한다.

!!! info "사전 지식"
    - [Unit 1: Digital Design / RTL](01_digital_rtl.md) — RTL / valid-ready / CDC 기본
    - SystemVerilog OOP — class, virtual, inheritance, polymorphism
    - 시뮬레이터 사용 경험 (VCS / Questa / Xcelium)

---

## 1. UVM — Phase + Component 계층

### 1.1 Phase 모델 (한 줄)

```
build → connect → end_of_elaboration → start_of_simulation
  ↓ (시간 흐름)
run (parallel: pre_reset / reset / post_reset / pre_configure / configure / ... / shutdown)
  ↓
extract → check → report → final
```

- `build_phase` — **top-down**. 자식 component 인스턴스 생성. `uvm_config_db::get()` 로 설정 읽기.
- `connect_phase` — **bottom-up**. TLM 포트 연결.
- `run_phase` — **병렬**. 모든 component 의 `run_phase` 가 동시 실행. `raise_objection` / `drop_objection` 으로 종료 제어.
- `check_phase` / `report_phase` — 결과 집계.

### 1.2 Component 계층

```
uvm_test
└── uvm_env
    ├── uvm_agent (× N — protocol 별)
    │   ├── uvm_sequencer
    │   ├── uvm_driver
    │   └── uvm_monitor
    └── uvm_scoreboard / uvm_subscriber / uvm_coverage
```

- **Agent** = 한 인터페이스 (예: AXI master) 의 자극과 관찰 묶음. `is_active` 에 따라 *Active*(sqr+drv+mon) 또는 *Passive*(mon 만).
- **Sequence** 는 component 가 아니라 `uvm_sequence_item` 들을 생성하는 *transient object*. Sequencer 에 `.start()` 로 띄움.
- **Scoreboard** — Reference model 의 예상값과 monitor 가 잡은 실제값을 비교.

### 1.3 Factory + Override — *왜* 중요?

```systemverilog
// 기본 시퀀스
class base_seq extends uvm_sequence #(axi_item);
  `uvm_object_utils(base_seq)
  ...
endclass

// 에러 주입 시퀀스
class err_seq extends base_seq;
  `uvm_object_utils(err_seq)
  // 일부 필드를 illegal 값으로
endclass

// test 에서 한 줄로 override
class err_test extends base_test;
  function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    set_type_override_by_type(base_seq::get_type(), err_seq::get_type());
  endfunction
endclass
```

**효과** — `env` 코드를 *건드리지 않고* test 마다 다른 동작 주입. UVM 의 핵심 가치.

---

## 2. SystemVerilog OOP — DV 에서 자주 묻는 것

| 개념 | 정의 | DV 에서 용도 |
|------|------|-------------|
| Class | 데이터 + 메서드 | sequence_item, transaction |
| Inheritance | `extends` | 기본 item 에 illegal 필드 추가 |
| Polymorphism | `virtual function` | scoreboard 가 다양한 transaction 비교 |
| `rand` / `randc` | 랜덤 변수 | constraint randomization |
| `randomize() with { }` | inline constraint | 특정 test 에서만 제약 추가 |
| `uvm_object_utils` | factory 등록 매크로 | `create()` 로 생성 |

---

## 3. Constraint Randomization

### 3.1 기본

```systemverilog
class axi_item extends uvm_sequence_item;
  rand bit [31:0] addr;
  rand bit [7:0]  len;
  rand bit [2:0]  size;

  constraint c_addr {
    addr inside {[32'h1000_0000 : 32'h1FFF_FFFF]};
    addr[1:0] == 2'b00;  // word-aligned
  }
  constraint c_burst {
    len inside {0, 1, 3, 7, 15};
    size <= 3;  // up to 8 bytes
  }
endclass
```

### 3.2 Distribution

```systemverilog
constraint c_dist {
  addr dist {
    [32'h0000_0000 : 32'h0FFF_FFFF] :/ 70,  // 70% in this range
    [32'h1000_0000 : 32'hFFFF_FFFF] :/ 30
  };
}
```

`:/` 는 *구간 가중치 분배*, `:=` 는 *각 값에 동일 가중치*.

### 3.3 Dynamic Array / Queue

```systemverilog
class seq_item extends uvm_sequence_item;
  rand bit [7:0] payload[];   // dynamic array
  rand int       size;
  constraint c_size { size inside {[1:64]}; payload.size() == size; }
  constraint c_data { foreach(payload[i]) payload[i] inside {[8'h20:8'h7E]}; }  // printable ASCII
endclass
```

### 3.4 인터뷰 빈출 — *Solve order*

```systemverilog
rand bit [7:0] addr;
rand bit       en;
constraint c { solve en before addr;  en -> addr inside {[0:15]}; }
```

`solve A before B` — A 를 먼저 해결 → B 의 분포가 A 에 의존적이지 않게.

---

## 4. SystemVerilog Assertion (SVA)

### 4.1 Immediate vs Concurrent

- **Immediate**: `assert (condition);` — procedural block 안, 그 시점에 평가.
- **Concurrent**: `property` + `assert property` — 클럭 기반 시퀀스, 시간에 걸쳐 평가. **인터뷰 대상은 이쪽**.

### 4.2 핵심 연산자

| 연산자 | 의미 |
|--------|------|
| `##1` | 다음 클럭 |
| `##[1:3]` | 1~3 클럭 후 |
| `\|->` | overlapping implication (antecedent 클럭에서 시작) |
| `\|=>` | non-overlapping implication (antecedent 다음 클럭에서 시작) |
| `[*N]` | repetition N 회 |
| `[*1:$]` | 1 회 이상 반복 (eventually) |
| `$rose(x)` | x 가 이번 클럭에 0→1 |
| `$past(x, N)` | N 클럭 전 x 값 |

### 4.3 AXI valid-ready 예시

```systemverilog
// 1. valid 가 raise 되면 transfer 까지 lower 되지 않는다
property p_valid_stable;
  @(posedge clk) disable iff (!rst_n)
    $rose(valid) |-> valid throughout (ready[->1]);
endproperty
assert property (p_valid_stable);

// 2. valid && ready 가 transfer 의 정의
property p_handshake;
  @(posedge clk) disable iff (!rst_n)
    (valid && ready) |=> $past(data) == captured_data;
endproperty
```

### 4.4 Cover Property — *왜 항상 짝* 으로 작성하나?

```systemverilog
cover property (@(posedge clk) (valid && ready));
cover property (@(posedge clk) (valid && !ready));   // backpressure 케이스
```

`assert` 는 *위반 검출*, `cover` 는 *해당 조건이 시뮬에서 발생했는가 확인*. 둘이 짝이 아니면 assertion 이 *영구히 트리거 안 됨* 인 것을 모름 (vacuous pass).

---

## 5. Monitor & Scoreboard

### 5.1 Monitor — Passive 관찰

```systemverilog
class axi_monitor extends uvm_monitor;
  virtual axi_if vif;
  uvm_analysis_port #(axi_item) ap;

  task run_phase(uvm_phase phase);
    forever begin
      @(posedge vif.clk iff (vif.valid && vif.ready));
      axi_item t = axi_item::type_id::create("t");
      t.addr = vif.addr;
      t.data = vif.data;
      ap.write(t);     // 모든 구독자에게 broadcast
    end
  endtask
endclass
```

### 5.2 Scoreboard — 비교

```systemverilog
class sb extends uvm_scoreboard;
  uvm_analysis_imp #(axi_item, sb) ap_imp;
  axi_item expected_q[$];

  // monitor 에서 write() 호출 → 자동으로 이 메서드 트리거
  function void write(axi_item t);
    axi_item exp;
    if (expected_q.size() == 0) `uvm_error("SB", $sformatf("Unexpected: %s", t.sprint()))
    else begin
      exp = expected_q.pop_front();
      if (!exp.compare(t))
        `uvm_error("SB", $sformatf("Mismatch: exp=%s got=%s", exp.sprint(), t.sprint()))
    end
  endfunction
endclass
```

- **TLM 1.0** — `analysis_port` (broadcast) + `analysis_imp` (subscriber). 시뮬 시간 *소비 안 함*.
- 데이터 플로우: `driver` 가 `predictor` 에도 알리고 (또는 `monitor` 가 양쪽 모두 잡음), `predictor` 가 reference model 돌려 `expected_q` 에 push, `monitor` 가 실제 transaction 잡으면 비교.

---

## 6. CDC Verification

| 시나리오 | TB 에서 잡는 방법 |
|----------|-------------------|
| Pulse 가 dst clock 보다 짧음 | Coverage: pulse width < N, 의도적 random pulse 시퀀스 |
| Multi-bit bus 직접 연결 | RTL CDC tool 정적 분석 (Spyglass-CDC, Conformal-CDC) |
| Async FIFO empty/full glitch | SVA: empty 와 full 동시에 1 이면 fatal |
| Handshake REQ/ACK race | SVA: REQ↑ → ACK↑ → REQ↓ → ACK↓ 순서 강제 |

### 6.1 RTL CDC tool 의 한계

- *정적* 분석 → false positive 많음. 모든 cross 에 sync 가 *있는지* 만 본다.
- *값* 의 coherency 까지는 못 본다 → 시뮬레이션 / formal 추가 필요.

---

## 7. Bus / Interconnect 검증

### 7.1 자주 묻는 verification feature

- **AXI async clock crossing** — 두 다른 클럭 도메인의 AXI port 사이 어댑터. ID 보존 / OOO 보존 / outstanding count 모두 검증.
- **Merging / splitting** — 다중 master ↔ 다중 slave. Arbitration, ID 충돌 방지(ID prefix 추가) 검증.
- **Register slicing** — 타이밍 closure 용 forward/backward register. valid/ready 핸드셰이크 보존 검증.

### 7.2 Arbiter 검증

| 항목 | 검증 포인트 |
|------|-------------|
| Round-robin 공정성 | 모든 요청자가 일정 횟수 내 grant 받는다 |
| Priority arbiter | 높은 priority 요청 시 낮은 priority 가 *반드시* 양보 |
| Starvation | 낮은 priority 요청자가 *영구히* grant 못 받는 시나리오 |
| Deadlock | Multi-stage arbiter 에서 cycle 형성 가능 여부 |

---

## 8. Coverage — Functional vs Code

### 8.1 Functional Coverage (사용자 정의)

```systemverilog
covergroup cg_axi @(posedge clk iff (valid && ready));
  cp_addr  : coverpoint addr {
    bins low  = {[0:'h1000]};
    bins mid  = {['h1001:'h1_0000]};
    bins high = default;
  }
  cp_len   : coverpoint len {
    bins single = {0};
    bins burst  = {[1:7]};
    bins long   = {[8:255]};
  }
  cross_addr_len : cross cp_addr, cp_len;
endgroup
```

### 8.2 Code Coverage (자동)

- **Line**: 각 라인 실행됨
- **Branch / Condition**: if/case 의 각 분기
- **Toggle**: 신호가 0→1, 1→0 모두 발생
- **FSM**: 모든 state, 모든 transition

**인터뷰 정답**: "Code coverage 100% 는 *최소 조건*. Functional coverage 가 *진짜 검증 완성도*."

### 8.3 Coverage Closure 전략

1. Functional cov 의 *un-hit bin* 식별
2. 해당 bin 을 trigger 할 *constrained-random* test 작성
3. 그래도 안 닫히면 *directed test* 또는 *formal*
4. *정말* 도달 불가능한 bin 은 *exclude* 와 주석으로 정당화

---

## 9. 샘플 인터뷰 Q&A

??? question "Q1. (Understand) `uvm_object` 와 `uvm_component` 의 차이?"
    - `uvm_component` — *phase 가짐*, 계층 트리, 시뮬 시작~끝 존속. (env, agent, driver, monitor)
    - `uvm_object` — phase 없음, 자유 생성/소멸. (sequence, sequence_item, config object)

??? question "Q2. (Apply) 시퀀스 100개 중 70% 는 read, 30% 는 write 로 자극을 인가하는 코드를 짜라."
    ```systemverilog
    class rd_wr_seq extends uvm_sequence #(axi_item);
      rand int n;
      constraint c_n { n == 100; }
      task body();
        repeat (n) begin
          axi_item it = axi_item::type_id::create("it");
          assert(it.randomize() with {
            kind dist { READ := 70, WRITE := 30 };
          });
          start_item(it);
          finish_item(it);
        end
      endtask
    endclass
    ```

??? question "Q3. (Analyze) Scoreboard 가 false negative (실제 버그를 놓침) 를 일으키는 흔한 원인 3가지?"
    1. **Monitor 가 transaction 을 *놓침*** — `@(posedge clk iff valid && ready)` 가 아니라 `@(posedge clk)` 를 사용 → race.
    2. **Reference model 의 *비결정성*** — random 또는 외부 정보 사용 → expected 가 흔들림.
    3. **Compare 가 *부분 필드* 만 비교** — `id` 누락 → 다른 ID 의 응답이 매칭됨.

??? question "Q4. (Evaluate) Code coverage 99%, Functional coverage 75% — sign-off 가능?"
    **불가**. Code cov 는 *기본 위생*. Functional cov 75% 는 *25% 의 시나리오를 본 적도 없다는 뜻* — 가장 큰 risk. Functional hole 분석 + 추가 test 가 필요.

??? question "Q5. (Create) Async FIFO 검증을 위한 covergroup 을 설계해라."
    ```systemverilog
    covergroup cg_afifo @(posedge clk);
      cp_state : coverpoint {full, empty, almost_full, almost_empty} {
        bins empty_only       = {4'b0001};
        bins full_only        = {4'b1000};
        bins almost_empty     = {4'b0011};
        bins almost_full      = {4'b1100};
        bins mid              = {4'b0000};
        illegal_bins both_ef  = {4'b1001};  // full && empty 동시 → bug
      }
      cp_wr_pressure : coverpoint wr_en iff (full);     // full 시 wr 시도
      cp_rd_pressure : coverpoint rd_en iff (empty);    // empty 시 rd 시도
    endgroup
    ```

---

## 10. 핵심 정리 (Key Takeaways)

1. UVM 의 핵심은 *factory override* — env 를 안 건드리고 동작 변경.
2. Constraint 의 `dist` 와 `solve before` 가 가장 빈출.
3. SVA 는 `assert` + `cover` 짝으로 — vacuous pass 방지.
4. Monitor 는 *passive*, Scoreboard 는 *predictor 결과와 비교*.
5. CDC 검증은 *정적 (CDC tool) + 동적 (random) + formal* 3 단계.
6. Coverage 종료 기준은 *functional* 이지 code 가 아니다.

## 11. Further Reading

- *UVM 1.2 Reference Manual* (Accellera)
- *SystemVerilog for Verification* (Spear & Tumbush)
- [DV SKOOL — UVM 토픽](https://humbleowl39.github.io/DV_SKOOL/uvm/) — phase / agent / sequence / factory 심화
- [DV SKOOL — AMBA Protocols](https://humbleowl39.github.io/DV_SKOOL/amba_protocols/) — 검증 대상 프로토콜
- [DV SKOOL — Formal Verification](https://humbleowl39.github.io/DV_SKOOL/formal_verification/)
- [Unit 2 퀴즈](quiz/02_design_verification_quiz.md) 로 자기 점검
