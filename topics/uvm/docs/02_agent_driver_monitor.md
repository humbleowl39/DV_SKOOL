# Module 02 — Agent / Driver / Monitor

<div class="learning-meta">
  <span class="meta-badge meta-level-advanced">📊 Advanced</span>
</div>

!!! objective "학습 목표"
    이 모듈을 마치면:

    - **Design** Active/Passive 모드 분리를 갖춘 Agent를 build_phase에서 분기 구현할 수 있다.
    - **Implement** `get_next_item` / `item_done` 짝을 사용하는 정상 Driver와 Pipelining Driver를 각각 작성할 수 있다.
    - **Distinguish** Driver(인가)와 Monitor(관찰)의 책임 경계를 코드 리뷰에서 식별할 수 있다.
    - **Connect** Virtual Interface를 top → config_db → Agent 경로로 전달해 Driver/Monitor에 연결할 수 있다.

!!! info "사전 지식"
    - [Module 01 — UVM 아키텍처 & Phase](01_architecture_and_phase.md) (Phase 흐름, 컴포넌트 생성)
    - SystemVerilog `interface`와 `modport`
    - `clocking block`의 의미 (signal sampling/driving timing)

## 왜 이 모듈이 중요한가

Agent는 **UVM 재사용의 최소 단위**입니다. 잘못 설계된 Agent는 모든 환경에 cascading failure를 만듭니다. 특히 Active/Passive 분리를 안 해 두면, 같은 인터페이스를 다른 위치에서(예: PCIe RC vs EP) 검증할 때 Agent를 새로 짜야 합니다. Driver와 Monitor의 책임 경계도 헷갈리기 쉬운 영역으로, **Monitor가 신호를 절대 driving하지 않는다**는 원칙은 격리/관찰의 본질입니다.

## 핵심 개념
**Agent = 하나의 인터페이스에 대한 검증 인프라 묶음 (Driver + Monitor + Sequencer). Active Agent는 자극 생성+관찰, Passive Agent는 관찰만. DUT의 프로토콜 인터페이스마다 1개 Agent를 배치하는 것이 원칙.**

---

## Agent 구조

```systemverilog
class my_agent extends uvm_agent;
  `uvm_component_utils(my_agent)

  my_driver    driver;
  my_monitor   monitor;
  my_sequencer sequencer;

  function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    monitor = my_monitor::type_id::create("monitor", this);

    if (get_is_active() == UVM_ACTIVE) begin
      driver    = my_driver::type_id::create("driver", this);
      sequencer = my_sequencer::type_id::create("sequencer", this);
    end
  endfunction

  function void connect_phase(uvm_phase phase);
    if (get_is_active() == UVM_ACTIVE) begin
      driver.seq_item_port.connect(sequencer.seq_item_export);
    end
  endfunction
endclass
```

### Active vs Passive

```
Active Agent (UVM_ACTIVE):
  +---+---+---+
  |Drv|Mon|Sqr|  → DUT에 자극 인가 + 관찰
  +---+---+---+
  용도: DUT 입력 인터페이스

Passive Agent (UVM_PASSIVE):
  +---+
  |Mon|  → DUT 신호 관찰만 (자극 없음)
  +---+
  용도: DUT 출력 관찰, 프로토콜 체크
```

---

## Driver — DUT에 자극 인가

```systemverilog
class my_driver extends uvm_driver #(my_item);
  `uvm_component_utils(my_driver)

  virtual my_if vif;  // Virtual Interface

  function void build_phase(uvm_phase phase);
    if (!uvm_config_db #(virtual my_if)::get(this, "", "vif", vif))
      `uvm_fatal("NOVIF", "Virtual interface not found")
  endfunction

  task run_phase(uvm_phase phase);
    forever begin
      // 1. Sequencer에서 트랜잭션 수신
      seq_item_port.get_next_item(req);

      // 2. Pin-level로 변환하여 DUT에 인가
      drive_item(req);

      // 3. 완료 알림
      seq_item_port.item_done();
    end
  endtask

  task drive_item(my_item item);
    @(posedge vif.clk);
    vif.valid <= 1'b1;
    vif.data  <= item.data;
    vif.addr  <= item.addr;
    @(posedge vif.clk);
    while (!vif.ready) @(posedge vif.clk);  // Handshake 대기
    vif.valid <= 1'b0;
  endtask
endclass
```

### Driver 설계 원칙

| 원칙 | 설명 |
|------|------|
| 프로토콜만 구현 | DUT 로직을 Driver에 넣지 않음 |
| Pin-level 변환 | Transaction → 신호 전환만 담당 |
| 타이밍 정확성 | 프로토콜 스펙의 타이밍을 정확히 준수 |
| Handshake 준수 | VALID/READY 규칙 (AXI: VALID은 READY 기다리지 않음) |
| Reusable | DUT 독립적 — 같은 프로토콜이면 재사용 가능 |

---

## Monitor — DUT 신호 관찰

```systemverilog
class my_monitor extends uvm_monitor;
  `uvm_component_utils(my_monitor)

  virtual my_if vif;
  uvm_analysis_port #(my_item) ap;  // Scoreboard/Coverage로 전달

  function void build_phase(uvm_phase phase);
    ap = new("ap", this);
    if (!uvm_config_db #(virtual my_if)::get(this, "", "vif", vif))
      `uvm_fatal("NOVIF", "Virtual interface not found")
  endfunction

  task run_phase(uvm_phase phase);
    forever begin
      my_item item = my_item::type_id::create("item");
      // 핸드셰이크 감지
      @(posedge vif.clk);
      if (vif.valid && vif.ready) begin
        item.data = vif.data;
        item.addr = vif.addr;
        ap.write(item);  // Analysis Port로 브로드캐스트
      end
    end
  endtask
endclass
```

### Monitor 설계 원칙

| 원칙 | 설명 |
|------|------|
| 관찰만 (Passive) | DUT 신호를 읽기만, 구동하지 않음 |
| 프로토콜 수준 재구성 | Pin-level → Transaction 변환 |
| Analysis Port | 수집한 Transaction을 Scoreboard/Coverage에 broadcast |
| Active/Passive 공통 | Agent 모드와 무관하게 항상 존재 |

---

## Response 핸들링 — Driver ↔ Sequence 양방향

```systemverilog
// 기본 Driver: 단방향 (Sequence → Driver)
//   get_next_item → drive → item_done

// Response Driver: 양방향 (Sequence ↔ Driver)
//   get_next_item → drive → put_response → item_done

class my_driver extends uvm_driver #(axi_item);
  task run_phase(uvm_phase phase);
    forever begin
      seq_item_port.get_next_item(req);

      // DUT에 인가
      drive_item(req);

      // Read 트랜잭션이면 Response 생성
      if (!req.wr_rd) begin
        axi_item rsp = axi_item::type_id::create("rsp");
        rsp.set_id_info(req);  // ★ 필수: transaction/sequence ID 매칭
        rsp.data = vif.rdata;  // DUT에서 읽은 값
        rsp.resp = vif.rresp;
        seq_item_port.put_response(rsp);
      end

      seq_item_port.item_done();
    end
  endtask
endclass
```

### Response 흐름 다이어그램

```
               Sequence                Sequencer/Driver
                  |                         |
  start_item(req) |─────────────────────────>|
  finish_item(req)|─────────────────────────>| → DUT 구동
                  |                         |
                  |      put_response(rsp)  |
                  |<─────────────────────────| ← DUT 응답
  get_response(rsp)|                        |
                  |      item_done()        |
                  |<─────────────────────────|

set_id_info가 없으면:
  → Sequencer가 Response를 올바른 Sequence에 전달할 수 없음
  → 여러 Sequence가 동시 실행 중일 때 Response가 엉뚱한 Sequence로 감
```

---

## Pipelining Driver — 고성능 구동

```systemverilog
// 문제: get_next_item → drive → item_done 루프는 직렬 처리
//       DUT가 파이프라인이면 이전 트랜잭션 완료 전에 다음을 보낼 수 있어야 함

// 해결: get_next_item 대신 try_next_item으로 비차단 폴링

class pipelined_driver extends uvm_driver #(axi_item);
  task run_phase(uvm_phase phase);
    forever begin
      @(posedge vif.clk);

      // 비차단: 새 item이 있으면 가져오고, 없으면 skip
      seq_item_port.try_next_item(req);

      if (req != null) begin
        // 새 트랜잭션 시작 (파이프라인 투입)
        vif.valid <= 1'b1;
        vif.addr  <= req.addr;
        vif.data  <= req.data;
        seq_item_port.item_done();
      end else begin
        // 새 item 없음 → idle
        vif.valid <= 1'b0;
      end

      // 파이프라인 완료 체크 (이전 트랜잭션)
      check_pipeline_completion();
    end
  endtask
endclass
```

### get_next_item vs try_next_item

| 메서드 | 동작 | 사용 시점 |
|--------|------|----------|
| `get_next_item` | Blocking — item이 올 때까지 대기 | 직렬 프로토콜 (UART, SPI) |
| `try_next_item` | Non-blocking — 없으면 null 반환 | 파이프라인, 고속 인터페이스 |
| `get` | get_next_item + item_done 합친 것 | Response 불필요 시 단축 |

```
직렬 Driver:
  get_next_item → drive(10 clk) → item_done → get_next_item → ...
  [====drive====]                 [====drive====]
  → 처리량: 1 item / 10 clk

파이프라인 Driver:
  try_next_item → inject → try_next_item → inject → ...
  [inject][inject][inject][inject]
  → 처리량: 1 item / 1 clk (파이프라인 full)
```

---

## Sequencer Arbitration — 다중 Sequence 관리

```systemverilog
// 하나의 Sequencer에 여러 Sequence가 동시에 start()되면?
// → Arbitration 모드가 item 전달 순서를 결정

// 모드 설정 (보통 Env 또는 Test에서)
env.agent.sequencer.set_arbitration(UVM_SEQ_ARB_FIFO);
```

### Arbitration 모드 비교

| 모드 | 동작 | 용도 |
|------|------|------|
| `UVM_SEQ_ARB_FIFO` | 요청(start_item) 순서대로 | 기본값, 대부분의 경우 |
| `UVM_SEQ_ARB_WEIGHTED` | 우선순위 가중치 기반 확률적 선택 | 트래픽 믹스 비율 |
| `UVM_SEQ_ARB_RANDOM` | 랜덤 선택 | 랜덤 인터리빙 |
| `UVM_SEQ_ARB_STRICT_FIFO` | 높은 우선순위 먼저 → 같으면 FIFO | 긴급 트랜잭션 |
| `UVM_SEQ_ARB_STRICT_RANDOM` | 높은 우선순위 먼저 → 같으면 랜덤 | 우선순위 내 랜덤 |
| `UVM_SEQ_ARB_USER` | user_priority_arbitration() 오버라이드 | 커스텀 스케줄링 |

### 우선순위 설정

```systemverilog
// Sequence에서 우선순위 지정
class high_priority_seq extends uvm_sequence #(axi_item);
  task body();
    axi_item item;

    // 이 Sequence의 우선순위를 높게 설정 (기본 = -1)
    set_priority(100);

    repeat(5) begin
      item = axi_item::type_id::create("item");
      start_item(item);
      assert(item.randomize());
      finish_item(item);
    end
  endtask
endclass

// UVM_SEQ_ARB_STRICT_FIFO + set_priority(100) 조합:
//   priority 100인 Sequence의 item이 항상 먼저 처리됨
//   같은 priority 내에서는 FIFO 순서
```

### 실무 활용 예시

```
시나리오: 정상 트래픽 + 인터럽트 시뮬레이션

  normal_seq.start(sequencer);    // priority = -1 (기본)
  interrupt_seq.start(sequencer); // priority = 100

  UVM_SEQ_ARB_STRICT_FIFO 설정 시:
    → interrupt_seq의 item이 항상 우선 처리
    → 인터럽트 지연 시간을 현실적으로 모델링
```

---

## Virtual Interface — DUT 연결

```systemverilog
// 1. Interface 정의 (module level)
interface my_if(input logic clk, rst);
  logic        valid;
  logic        ready;
  logic [31:0] data;
  logic [15:0] addr;
endinterface

// 2. Top Module에서 DUT와 연결
module tb_top;
  logic clk, rst;
  my_if intf(clk, rst);
  my_dut dut(.clk(clk), .rst(rst),
             .valid(intf.valid), .ready(intf.ready),
             .data(intf.data), .addr(intf.addr));

  initial begin
    // 3. config_db에 등록
    uvm_config_db #(virtual my_if)::set(null, "*", "vif", intf);
    run_test();
  end
endmodule

// 4. Driver/Monitor에서 config_db로 가져오기
uvm_config_db #(virtual my_if)::get(this, "", "vif", vif);
```

**핵심**: Interface는 module 세계(RTL)와 class 세계(UVM)를 연결하는 브릿지. config_db를 통해 전달하여 하드코딩을 피함.

---

## 이력서 연결 — Custom Thin VIP, Active Driver

### Custom Thin VIP (MMU 검증)

```
일반 Agent:
  모든 프로토콜 기능 구현 + 히스토리 + 프로토콜 체커
  → 메모리 소비 큼

Thin Agent:
  Driver: 핵심 핸드셰이크만 (tdata/tvalid/tready)
  Monitor: 핵심 트랜잭션만 수집 (히스토리 제한)
  → Bounded Queue, Sliding Window → 메모리 수십 MB
```

### Active Driver — force/release (BootROM 보안)

```
일반 Driver: DUT 인터페이스 핀으로만 자극
Security Driver: force/release로 DUT 내부 신호에 직접 접근

  task drive_attack(security_item item);
    #(item.inject_time);
    force dut.verify_result = item.force_value;
    #(item.hold_cycles);
    release dut.verify_result;
  endtask

→ Fault Injection, TOCTOU 등 보안 공격 시뮬레이션
→ Passive Monitor로는 불가능 → Active Driver 필수
```

---

## Q&A

**Q: Agent를 Active/Passive로 나누는 이유는?**
> "역할 분리와 재사용성이다. DUT 입력에는 Active Agent(자극 생성+관찰), 출력에는 Passive Agent(관찰만). 같은 Agent 클래스를 is_active 설정만 바꿔서 양쪽에 사용할 수 있다. 또한 Passive Agent는 Driver/Sequencer를 생성하지 않으므로 메모리와 시뮬레이션 시간을 절약한다."

**Q: Virtual Interface를 왜 사용하는가?**
> "SystemVerilog에서 module(RTL/Interface)과 class(UVM)는 다른 세계이다. Virtual Interface가 이 둘을 연결하는 유일한 표준 방법이다. config_db를 통해 전달하면 Driver/Monitor가 DUT와의 물리적 연결에 독립적이 되어 재사용성이 높아진다."

**Q: Driver에 DUT 로직을 넣으면 안 되는 이유는?**
> "Driver는 프로토콜 변환(Transaction → Pin-level)만 담당해야 한다. DUT 로직을 넣으면 (1) 같은 버그를 Driver와 DUT 양쪽에 구현하여 검출 불가. (2) DUT가 변경될 때마다 Driver도 수정 필요. (3) 다른 DUT에 재사용 불가. DUT 동작 예측은 Scoreboard의 Reference Model이 담당한다."

**Q: Pipelining Driver가 필요한 경우는?**
> "DUT가 파이프라인 구조여서 이전 트랜잭션 완료 전에 다음 트랜잭션을 받을 수 있는 경우이다. 일반 Driver의 get_next_item → drive → item_done 루프는 하나의 트랜잭션이 완전히 끝나야 다음을 시작한다. 이러면 DUT 파이프라인이 항상 비어있어 실제 동작을 검증하지 못한다. try_next_item으로 비차단 폴링하면 매 클럭마다 새 item을 투입할 수 있어 파이프라인을 꽉 채운 상태에서의 동작(back-pressure, stall, hazard)을 검증할 수 있다."

**Q: Sequencer Arbitration을 실무에서 어떻게 활용하는가?**
> "두 가지 주요 활용이 있다. (1) 트래픽 믹스 — UVM_SEQ_ARB_WEIGHTED로 Read 70%, Write 30% 같은 현실적인 트래픽 비율을 구현한다. (2) 인터럽트 모델링 — UVM_SEQ_ARB_STRICT_FIFO로 인터럽트 Sequence에 높은 우선순위를 부여하면, 정상 트래픽 중간에 인터럽트가 즉시 끼어들어 DUT의 인터럽트 처리를 현실적으로 검증할 수 있다. 기본값 UVM_SEQ_ARB_FIFO는 단일 Sequence 실행에 충분하다."

**Q: set_id_info를 빠뜨리면 어떤 문제가 발생하는가?**
> "여러 Sequence가 동시에 같은 Sequencer에서 실행될 때 문제가 된다. Driver가 put_response(rsp)를 호출하면 Sequencer가 rsp 내부의 sequence_id를 보고 해당 Sequence에 전달한다. set_id_info가 없으면 sequence_id가 기본값(0)이라 Sequencer가 올바른 Sequence를 매칭할 수 없다. 단일 Sequence만 실행한다면 우연히 동작할 수 있지만, 멀티 Sequence 환경에서 즉시 깨지는 잠재 버그이다."

---

## 연습문제

!!! question "Exercise 1 (Apply, ★)"
    `is_active` 플래그를 사용해 Active/Passive 모드를 build_phase에서 분기하는 Agent를 작성하세요. Passive 모드에서는 Driver와 Sequencer가 생성되지 않아야 합니다.

    ??? answer "모범 답안"
        ```systemverilog
        class apb_agent extends uvm_agent;
          `uvm_component_utils(apb_agent)
          apb_driver    drv;
          apb_monitor   mon;
          apb_sequencer sqr;

          function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            mon = apb_monitor::type_id::create("mon", this);  // 항상 생성
            if (get_is_active() == UVM_ACTIVE) begin
              drv = apb_driver::type_id::create("drv", this);
              sqr = apb_sequencer::type_id::create("sqr", this);
            end
          endfunction

          function void connect_phase(uvm_phase phase);
            super.connect_phase(phase);
            if (get_is_active() == UVM_ACTIVE)
              drv.seq_item_port.connect(sqr.seq_item_export);
          endfunction
        endclass
        ```

!!! question "Exercise 2 (Analyze, ★★)"
    Driver의 `forever` 루프에서 `get_next_item()`만 호출하고 `item_done()`을 빠뜨리면 어떤 증상이 나타나는지, Sequencer 측 동작 관점에서 설명하세요.

    ??? answer "모범 답안"
        **증상**: 첫 트랜잭션은 정상 인가되지만 두 번째 트랜잭션이 영원히 대기 → 시뮬레이션 hang.

        **이유**: Sequencer는 `get_next_item` / `item_done`을 lockstep으로 관리. `item_done` 호출 전까지 sequencer는 "현재 item이 아직 처리 중"이라고 판단해 다음 item을 driver에게 주지 않음.

!!! question "Exercise 3 (Evaluate, ★★★)"
    Pipelining Driver가 적절한 시나리오와 단순 Driver가 충분한 시나리오를 각각 한 가지씩 들고, throughput / 응답 매칭 복잡도 관점에서 설명하세요.

    ??? answer "예시 답안"
        - **Pipelining 적절**: AXI write 채널 — AW/W 독립, outstanding 4+ 정상. 단순 driver는 throughput 측정 불가, OoO 응답 커버 불가.
        - **단순 driver 충분**: APB — outstanding 개념 없음(매 트랜잭션 SETUP→ACCESS→IDLE 순차). Pipelining 도입 시 오히려 protocol 위반.

!!! warning "실무 주의점 — `item_done()` 누락 시 두 번째 트랜잭션부터 hang"
    **현상**: 첫 번째 트랜잭션은 정상 구동되지만 이후 `get_next_item()`이 영원히 block되어 시뮬이 hang 또는 타임아웃.

    **원인**: `get_next_item()`과 `item_done()`은 lock-step 짝이다. `item_done()`을 빠뜨리면 Sequencer는 이전 item이 아직 처리 중이라고 판단해 다음 item을 보내지 않는다. `drive_item()` 안에서 예외 경로(에러 처리, early return)가 있을 때 한 쪽 분기에서 `item_done()` 호출이 빠지는 경우가 가장 흔하다.

    **점검 포인트**: 로그에서 `[get_next_item]` 메시지 이후 `[item_done]` 메시지가 나오는지 확인. Driver `run_phase`의 모든 분기(if/case)에서 `item_done()`이 반드시 호출되는지 코드 경로 추적. `try_next_item` 사용 시에도 non-null이면 반드시 `item_done()` 필요.

## 핵심 정리

- **Agent = Driver + Monitor + Sequencer** 묶음. Active/Passive 모드 분기로 재사용성 확보.
- **Driver는 인가, Monitor는 관찰**. Monitor가 DUT 신호 driving은 비침투적 관찰 원칙 위배.
- **`get_next_item` / `item_done`은 lockstep 짝**. 누락 시 두 번째 트랜잭션부터 hang.
- **Virtual Interface 전달은 config_db**: top → set, Driver/Monitor → get. 경로 일치 필수.
- **Pipelining Driver**는 throughput 검증에 필요하지만 응답 매칭(ID/queue) 책임 추가.
- Sequencer Arbitration은 다중 sequence 동시 실행 시 정책 결정 (FIFO / Strict-FIFO / Random / Weighted).

## 다음 단계

- 📝 [**Module 02 퀴즈**](quiz/02_agent_driver_monitor_quiz.md)
- ➡️ [**Module 03 — Sequence & Sequence Item**](03_sequence_and_item.md)

<div class="chapter-nav">
  <a class="nav-prev" href="../01_architecture_and_phase/">
    <div class="nav-label">◀ 이전</div>
    <div class="nav-title">UVM 아키텍처 & Phase</div>
  </a>
  <a class="nav-next" href="../03_sequence_and_item/">
    <div class="nav-label">다음 ▶</div>
    <div class="nav-title">Sequence & Sequence Item</div>
  </a>
</div>
