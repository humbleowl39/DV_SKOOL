---
title: "Unit 2 — Design Verification"
---

:::tip[학습 목표]
이 모듈을 마치면:

- **Explain** UVM 의 Phase 모델과 component 계층(Agent / Driver / Monitor / Sequencer / Scoreboard / Env / Test) 의 역할을 설명한다.
- **Apply** SystemVerilog constraint 로 dynamic array / queue distribution / 패턴 시퀀스를 생성한다.
- **Design** Monitor 가 sample 한 transaction 을 Scoreboard 가 reference model 과 비교하는 데이터 플로우를 설계한다.
- **Write** AXI / FIFO / arbiter 에 대한 핵심 SystemVerilog Assertion(SVA)을 작성한다.
- **Analyze** CDC 검증 시 잡아야 할 메타스테이빌리티 / data coherency / glitch 시나리오를 분류한다.
- **Evaluate** coverage-driven verification 의 hole 분석 결과를 보고 어떤 test 를 추가할지 우선순위를 결정한다.
:::
:::note[사전 지식]
- [Unit 1: Digital Design / RTL](../01_digital_rtl/) — RTL / valid-ready / CDC 기본
- SystemVerilog OOP — class, virtual, inheritance, polymorphism
- 시뮬레이터 사용 경험 (VCS / Questa / Xcelium)
:::
---

## 1. UVM — Phase + Component 계층

이 모듈은 설계 검증(DV)의 표준 방법론을 다룹니다. 먼저 토대 용어부터: **DUT**(Design Under Test, 검증 대상이 되는 설계 — 우리가 맞는지 확인하려는 RTL)와 **TB**(testbench, 테스트벤치 — DUT에 자극을 주고 출력을 확인하는 검증 환경)가 한 쌍입니다. **UVM**(Universal Verification Methodology, SystemVerilog 기반 검증 환경을 재사용 가능하게 짓는 표준 클래스 라이브러리·방법론)이 그 TB를 짓는 업계 표준입니다. **transaction**(트랜잭션 — "주소 X에 데이터 Y 쓰기" 같은, 신호 레벨보다 한 단계 추상화한 하나의 작업 단위)과 **component**(컴포넌트 — TB를 구성하는 재사용 블록; agent·driver 등)가 핵심 단위이고, **reference model**(ISA·스펙대로 "정답"을 계산하는 소프트웨어 모델 — golden reference)이 정답의 출처입니다.

### 1.1 Phase 모델 (한 줄)

```
build → connect → end_of_elaboration → start_of_simulation
  ↓ (시간 흐름)
run (parallel: pre_reset / reset / post_reset / pre_configure / configure / ... / shutdown)
  ↓
extract → check → report → final
```

- `build_phase` — **top-down**. 자식 component 인스턴스 생성. `uvm_config_db::get()` 로 설정 읽기.
- `connect_phase` — **bottom-up**. TLM(Transaction-Level Modeling, 신호가 아니라 트랜잭션 단위로 component끼리 데이터를 주고받는 연결 방식) 포트 연결.
- `run_phase` — **병렬**. 모든 component 의 `run_phase` 가 동시 실행. `raise_objection` / `drop_objection` 으로 종료 제어.
- `check_phase` / `report_phase` — 결과 집계.

### 1.2 Component 계층

```d2
direction: down
uvm_test -> uvm_env
uvm_env -> uvm_agent: "× N (protocol 별)"
uvm_agent -> uvm_sequencer
uvm_agent -> uvm_driver
uvm_agent -> uvm_monitor
uvm_env -> uvm_scoreboard
uvm_env -> uvm_subscriber
uvm_env -> uvm_coverage
```

위 계층의 각 component를 한 줄로 짚으면: **Test**(시나리오 하나를 정의하는 최상위 — 무엇을 검증할지 결정), **Env**(environment, agent·scoreboard 등을 모아 재사용 단위로 묶은 컨테이너), **Agent**(한 인터페이스를 담당하는 묶음), **Driver**(트랜잭션을 받아 실제 DUT 신호로 구동하는 component), **Monitor**(DUT 신호를 관찰해 트랜잭션으로 복원하는 수동 관찰자), **Sequencer**(시퀀스가 만든 자극을 driver로 흘려보내는 중계), **Scoreboard**(예상값과 실제값을 비교해 버그를 잡는 component), **Subscriber/Coverage**(관찰한 트랜잭션으로 커버리지를 수집)입니다.

**Agent** 는 AXI master 와 같이 *한 인터페이스 단위*로 자극 생성과 관찰을 하나로 묶은 컨테이너입니다. `is_active` 속성에 따라 sequencer+driver+monitor 를 모두 가진 *Active* 모드 또는 monitor 만 가진 *Passive* 모드로 동작합니다. Passive agent 는 DUT 버스를 건드리지 않고 관찰만 하므로, 예를 들어 scoreboard 에 데이터를 공급하는 read side 모니터링에 유용합니다.

**Sequence** 는 component 트리에 고정 등록되지 않는 *transient object* 입니다. `uvm_sequence_item` 을 생성·제약·랜덤화한 뒤 sequencer 의 `.start()` 를 통해 driver 로 전달됩니다. 이 구조 덕분에 env 를 건드리지 않고 test 레이어에서만 자극 패턴을 바꿀 수 있습니다.

**Scoreboard** 는 reference model 이 계산한 *예상값*과 monitor 가 DUT 에서 캡처한 *실제값*을 비교해 mismatch 를 검출합니다. driver 가 sequencer 를 통해 DUT 를 자극하는 동시에 predictor 에도 같은 transaction 을 알리면, predictor 가 예상 결과를 계산해 scoreboard 의 큐에 올려두고, monitor 가 실제 응답을 잡으면 그때 비교가 일어납니다.

### 1.3 Factory + Override — *왜* 중요?

**Factory**(팩토리 — 객체를 `new` 대신 등록된 타입 테이블을 거쳐 생성해, 코드 수정 없이 생성 타입을 바꿔치기(override)할 수 있게 하는 UVM 메커니즘)는 UVM 재사용성의 핵심입니다.

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

**왜 코드 수정 없이 동작이 바뀌나 — factory 의 type table lookup.** 비결은 객체를 `new` 로 직접 생성하지 않고 `type_id::create()` 로 생성하는 데 있다. `create()` 는 곧장 그 타입을 만드는 대신, UVM factory 가 내부에 들고 있는 _type 매핑 테이블(override table)_ 을 먼저 _조회_ 한다 — "이 요청된 타입(base_seq)에 대해 등록된 대체 타입이 있는가?" 를 묻는 것이다. override 가 없으면 원래 타입을 그대로 만들지만, `set_type_override_by_type(base_seq, err_seq)` 가 그 테이블에 "base_seq → err_seq" 라는 한 줄을 심어 두면, 이후 모든 `base_seq::type_id::create()` 호출이 테이블 lookup 에서 err_seq 로 _치환_ 되어 생성된다. env 와 sequence 코드는 여전히 `base_seq` 만 요청하지만, factory 가 생성 시점에 매핑을 갈아끼우므로 _호출 코드를 한 줄도 고치지 않고_ 실제 생성 타입만 바뀌는 것이다. polymorphism(부모 핸들로 자식 객체를 다룸) 덕분에 env 는 치환 사실을 몰라도 정상 동작한다. 이것이 `new` 대신 항상 `create()` 를 써야 하는 이유다 — `new` 로 만든 객체는 factory 테이블을 거치지 않아 override 가 먹지 않는다.

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

**Constrained-random verification**(제약 기반 랜덤 검증 — 값을 무작위로 생성하되, **constraint**(제약 — `rand` 변수가 만족해야 할 조건 블록)로 유효 범위를 좁혀 현실적인 자극을 자동으로 대량 만드는 기법)이 현대 DV의 주력입니다. `rand`(매 randomize마다 새 무작위 값을 받는 변수 한정자)가 그 출발점입니다.

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

**SVA**(SystemVerilog Assertion — RTL이 시간에 걸쳐 지켜야 할 규칙(예: "valid가 뜨면 transfer까지 안 내린다")을 선언적으로 적어 시뮬레이션/formal에서 위반을 자동 검출하는 언어 기능)는 프로토콜·타이밍 검사의 핵심 도구입니다.

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

**vacuous pass 의 정확한 메커니즘.** implication `A |-> B` 는 논리적으로 "A 가 참이면 B 도 참이어야 한다" 이다. 그런데 _A(antecedent)가 한 번도 참이 아니면_, "거짓이면 무엇이든 참 (false implies anything)" 이라는 논리 규칙에 따라 property 전체가 _자동으로 참_ 으로 평가된다 — 이것이 **vacuous(공허한) pass** 다. 예컨대 `$rose(valid) |-> ... ready ...` 에서 테스트가 `valid` 를 한 번도 띄우지 않으면, consequent(ready 검사)는 _실행조차 되지 않은 채_ assertion 이 매 사이클 PASS 로 집계된다. 즉 "PASS" 가 "검증됨" 이 아니라 "검증할 기회가 없었음" 을 뜻하는데, 로그에는 똑같이 통과로 보여 위험하다. 그래서 antecedent 조건(`valid && ready` 등)을 그대로 `cover property` 로 함께 두어, _antecedent 가 실제로 발생했는지_ 를 독립적으로 확인해야 한다 — cover 가 0 hit 이면 그 assert 의 PASS 는 전부 공허한 것이므로 자극(stimulus)을 보강해야 한다는 신호다.

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

**CDC**(Clock Domain Crossing, 클럭 도메인 횡단 — 서로 비동기인 클럭 영역 사이로 신호가 건너가는 구조; 자세한 회로는 Unit 1 참조) 검증은 문제가 *시뮬레이션마다 재현되지 않을 수 있다*는 점에서 일반 기능 검증보다 훨씬 까다롭습니다. 잘못된 동기화로 인한 오류는 특정 타이밍 조건에서만 나타나기 때문에 단순 directed test 로는 놓치기 쉽습니다. 아래 시나리오별로 TB 에서 어떤 방법으로 잡는지를 정리합니다.

| 시나리오 | TB 에서 잡는 방법 |
|----------|-------------------|
| Pulse 가 dst clock 보다 짧음 | Coverage: pulse width < N, 의도적 random pulse 시퀀스 |
| Multi-bit bus 직접 연결 | RTL CDC tool 정적 분석 (Spyglass-CDC, Conformal-CDC) |
| Async FIFO empty/full glitch | SVA: empty 와 full 동시에 1 이면 fatal |
| Handshake REQ/ACK race | SVA: REQ↑ → ACK↑ → REQ↓ → ACK↓ 순서 강제 |

### 6.1 RTL CDC tool 의 한계

- *정적* 분석 → false positive 많음. 모든 cross 에 sync 가 *있는지* 만 본다.
- *값* 의 coherency(서로 다른 사본·경로의 데이터가 일관된 값을 유지하는 성질) 까지는 못 본다 → 시뮬레이션 / formal(formal verification, 입력을 무작위로 넣어 보는 대신 수학적으로 모든 경우를 증명/반증하는 검증) 추가 필요.

---

## 7. Bus / Interconnect 검증

### 7.1 자주 묻는 verification feature

- **AXI async clock crossing** — 두 다른 클럭 도메인의 AXI port 사이 어댑터. ID 보존 / OOO(out-of-order, 요청 순서와 다른 순서로 응답이 와도 ID로 짝지음) 보존 / outstanding count(아직 응답을 못 받고 진행 중인 요청 수) 모두 검증.
- **Merging / splitting** — 다중 master ↔ 다중 slave. Arbitration, ID 충돌 방지(ID prefix 추가) 검증.
- **Register slicing** — 타이밍 closure 용 forward/backward register. valid/ready 핸드셰이크 보존 검증.

### 7.2 Arbiter 검증

**Arbiter**(중재기 — 여러 요청자가 동시에 자원(버스 등)을 원할 때 누구에게 줄지(grant) 정하는 회로)의 대표 검증 포인트입니다.

| 항목 | 검증 포인트 |
|------|-------------|
| Round-robin 공정성 | (요청자에게 차례를 돌아가며 주는 방식) 모든 요청자가 일정 횟수 내 grant 받는다 |
| Priority arbiter | 높은 priority 요청 시 낮은 priority 가 *반드시* 양보 |
| Starvation | (특정 요청자가 계속 밀려 영영 자원을 못 받는 굶주림) 낮은 priority 요청자가 *영구히* grant 못 받는 시나리오 |
| Deadlock | (서로가 서로를 기다려 전체가 멈춤) Multi-stage arbiter 에서 cycle 형성 가능 여부 |

---

## 8. Coverage — Functional vs Code

**Coverage**(커버리지 — 검증이 설계의 어떤 부분/시나리오를 실제로 건드렸는지 정량적으로 측정한 지표; "얼마나 빠짐없이 봤는가")는 검증 완성도의 척도입니다. 사용자가 "이런 시나리오를 봤어야 한다"를 직접 정의하는 **functional coverage**(기능 커버리지)와, 도구가 코드 실행을 자동 집계하는 **code coverage**(코드 커버리지)로 나뉩니다. functional coverage는 **covergroup**(측정 묶음), **coverpoint**(관찰할 신호/값), **bins**(값을 구간으로 나눈 칸), **cross**(두 coverpoint의 조합)로 기술합니다.

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

**Coverage closure**(커버리지 클로저 — 정의한 커버리지 목표를 100%에 도달시켜 "검증이 충분하다"고 선언할 수 있게 만드는 작업; 이후 **sign-off**(테이프아웃 전 검증 완료 승인) 판단의 근거)는 일회성 작업이 아니라 *반복 루프*입니다. 먼저 functional coverage 리포트에서 hit 되지 않은 bin 을 식별하고, 그 bin 을 trigger 할 수 있는 constrained-random test 를 작성합니다. 제약만으로도 안 닫히는 bin 은 해당 조건을 직접 만들어주는 directed test 나 formal verification 으로 보완합니다. 마지막으로 설계 자체가 해당 상태에 도달할 수 없다고 확인된 bin 은 exclude 처리하되, 반드시 *왜 도달 불가능한지* 주석으로 정당화해야 리뷰어나 나중에 자신이 다시 볼 때 혼란이 없습니다.

1. Functional cov 의 *un-hit bin* 식별
2. 해당 bin 을 trigger 할 *constrained-random* test 작성
3. 그래도 안 닫히면 *directed test* 또는 *formal*
4. *정말* 도달 불가능한 bin 은 *exclude* 와 주석으로 정당화

---

## 9. 샘플 인터뷰 Q&A

<details>
<summary>Q1. (Understand) `uvm_object` 와 `uvm_component` 의 차이?</summary>

- `uvm_component` — *phase 가짐*, 계층 트리, 시뮬 시작~끝 존속. (env, agent, driver, monitor)
- `uvm_object` — phase 없음, 자유 생성/소멸. (sequence, sequence_item, config object)

</details>
<details>
<summary>Q2. (Apply) 시퀀스 100개 중 70% 는 read, 30% 는 write 로 자극을 인가하는 코드를 짜라.</summary>

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

</details>
<details>
<summary>Q3. (Analyze) Scoreboard 가 false negative (실제 버그를 놓침) 를 일으키는 흔한 원인 3가지?</summary>

1. **Monitor 가 transaction 을 *놓침*** — `@(posedge clk iff valid && ready)` 가 아니라 `@(posedge clk)` 를 사용 → race.
2. **Reference model 의 *비결정성*** — random 또는 외부 정보 사용 → expected 가 흔들림.
3. **Compare 가 *부분 필드* 만 비교** — `id` 누락 → 다른 ID 의 응답이 매칭됨.

</details>
<details>
<summary>Q4. (Evaluate) Code coverage 99%, Functional coverage 75% — sign-off 가능?</summary>

**불가**. Code cov 는 *기본 위생*. Functional cov 75% 는 *25% 의 시나리오를 본 적도 없다는 뜻* — 가장 큰 risk. Functional hole 분석 + 추가 test 가 필요.

</details>
<details>
<summary>Q5. (Create) Async FIFO 검증을 위한 covergroup 을 설계해라.</summary>

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

</details>
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
- [Unit 2 퀴즈](../quiz/02_design_verification_quiz/) 로 자기 점검
