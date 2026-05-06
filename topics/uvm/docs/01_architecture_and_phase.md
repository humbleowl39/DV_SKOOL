# Unit 1: UVM 아키텍처 & Phase

## 핵심 개념
**UVM = SystemVerilog 기반의 검증 방법론 프레임워크. 클래스 계층으로 재사용 가능한 검증 환경을 구축하고, Phase 메커니즘으로 빌드/연결/실행의 순서를 보장하며, Factory/config_db로 유연한 객체 생성/설정을 제공.**

---

## UVM 클래스 계층

```
uvm_void
  └── uvm_object
        ├── uvm_transaction
        │     └── uvm_sequence_item      ← 트랜잭션 데이터
        ├── uvm_sequence                  ← 자극 시나리오
        ├── uvm_reg_block                 ← RAL (레지스터 모델)
        └── uvm_component
              ├── uvm_monitor             ← DUT 신호 관찰
              ├── uvm_driver              ← DUT에 자극 인가
              ├── uvm_sequencer           ← Sequence ↔ Driver 중개
              ├── uvm_agent               ← Driver+Monitor+Sequencer 묶음
              ├── uvm_scoreboard          ← 결과 비교/검증
              ├── uvm_env                 ← Agent+Scoreboard 묶음
              └── uvm_test               ← 최상위, 시나리오 선택

핵심 구분:
  uvm_object:    데이터/트랜잭션 (Phase 없음, 생명주기 짧음)
  uvm_component: 검증 인프라 (Phase 있음, 시뮬레이션 내내 존재)
```

### Factory 등록 매크로

```systemverilog
// uvm_component 등록 (name + parent 필수)
class my_driver extends uvm_driver #(my_item);
  `uvm_component_utils(my_driver)

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction
endclass

// uvm_object 등록 (name만, parent 없음)
class my_item extends uvm_sequence_item;
  `uvm_object_utils(my_item)

  function new(string name = "my_item");
    super.new(name);
  endfunction
endclass

// 차이: component는 계층 구조에 속함(parent), object는 독립적
```

---

## UVM Phase

### Phase 실행 순서

```
Build Phases (Top → Down, 순차):
  ┌─ build_phase        ← 컴포넌트 생성, config_db 읽기
  ├─ connect_phase      ← TLM 포트 연결
  └─ end_of_elaboration_phase

Run Phases (Bottom → Up, 병렬):
  ┌─ start_of_simulation_phase
  ├─ run_phase           ← 메인 시뮬레이션 (task, 시간 소비)
  │   ├─ reset_phase
  │   ├─ configure_phase
  │   ├─ main_phase
  │   └─ shutdown_phase
  └─ (run_phase와 sub-phase 병렬)

Cleanup Phases (Bottom → Up, 순차):
  ├─ extract_phase       ← 결과 수집
  ├─ check_phase         ← 최종 검증
  └─ report_phase        ← 결과 보고
```

### Phase 핵심 규칙

| 규칙 | 설명 |
|------|------|
| Build: Top → Down | 부모가 먼저 build → 자식 생성 가능 |
| Connect: Bottom → Up | 자식이 먼저 포트 생성 → 부모가 연결 |
| Run: 병렬 실행 | 모든 컴포넌트의 run_phase가 동시 시작 |
| Objection | run_phase는 objection이 모두 drop되면 종료 |
| Phase 순서 보장 | build 완료 전 connect 불가, connect 완료 전 run 불가 |

### Objection — Phase 종료 제어

```systemverilog
class my_test extends uvm_test;
  task run_phase(uvm_phase phase);
    phase.raise_objection(this);  // "아직 끝나지 않음"

    // 테스트 시나리오 실행
    my_seq.start(env.agent.sequencer);

    phase.drop_objection(this);   // "이제 끝남"
    // 모든 컴포넌트의 objection이 drop되면 run_phase 종료
  endtask
endclass

주의:
  raise 없이 drop → 에러
  drop 안 하면 → 시뮬레이션 무한 대기 (hang)
  보통 test에서만 raise/drop (다른 컴포넌트는 하지 않음)
```

### Drain Time — 안전한 종료 보장

```systemverilog
// 문제: drop_objection() 직후 run_phase가 종료되면
//       DUT 파이프라인에 아직 처리 중인 트랜잭션이 있을 수 있음
//       → Scoreboard에 expected는 있지만 actual이 안 옴 → false error

// 해결 1: drop_objection에 drain time 지정
class my_test extends uvm_test;
  task run_phase(uvm_phase phase);
    phase.raise_objection(this);

    my_seq.start(env.agent.sequencer);

    // 마지막 트랜잭션 전송 후 1000ns 동안 추가 대기
    phase.drop_objection(this, "test done", 1000);
    //                         ^desc       ^drain_time (time unit)
  endtask
endclass

// 해결 2: 명시적 대기 후 drop
class my_test extends uvm_test;
  task run_phase(uvm_phase phase);
    phase.raise_objection(this);

    my_seq.start(env.agent.sequencer);

    // DUT 파이프라인 flush 대기
    #(DUT_LATENCY * 2);
    // 또는 이벤트 기반: wait(scoreboard.all_matched);

    phase.drop_objection(this);
  endtask
endclass

// 해결 3: phase_ready_to_end 콜백 (컴포넌트 자율)
// → 아래 섹션 참조
```

### phase_ready_to_end — 컴포넌트 자율 종료 지연

```systemverilog
// 특정 컴포넌트가 "아직 처리 중인 데이터가 있다"고 알릴 수 있는 메커니즘
// run_phase의 모든 objection이 drop된 후, 종료 직전에 호출됨

class my_scoreboard extends uvm_scoreboard;
  `uvm_component_utils(my_scoreboard)

  my_item expected_queue[$];

  function void phase_ready_to_end(uvm_phase phase);
    // run_phase에서만 동작
    if (phase.get_name() != "run") return;

    // 아직 미매칭 항목이 있으면 종료 지연
    if (expected_queue.size() > 0) begin
      phase.raise_objection(this, "waiting for remaining items");

      fork begin
        // 최대 500ns 대기
        fork
          wait(expected_queue.size() == 0);
          #500ns;
        join_any
        disable fork;
        phase.drop_objection(this);
      end join_none
    end
  endfunction
endclass
```

### phase_ready_to_end 활용

```
호출 시점:
  run_phase의 모든 objection이 drop됨
    → UVM이 각 컴포넌트의 phase_ready_to_end() 호출
    → 컴포넌트가 추가 objection을 raise할 수 있음
    → 모든 추가 objection도 drop되면 비로소 run_phase 종료

용도:
  - Scoreboard: 미매칭 트랜잭션 대기
  - Monitor: 진행 중인 프로토콜 전송 완료 대기
  - Coverage: 마지막 샘플링 보장

Test의 drain time vs phase_ready_to_end:
  - drain time: Test가 전체 환경의 지연을 추정 (중앙 집중)
  - phase_ready_to_end: 각 컴포넌트가 자신의 완료를 관리 (분산)
  - 실무: 둘 다 사용 — drain time으로 기본 마진, phase_ready_to_end로 보험
```

---

### Sub-Phase (run_phase 세분화)

```
run_phase는 내부적으로 4개 sub-phase로 나뉨:

  run_phase (전체)
    ├── reset_phase      ← DUT 리셋 인가/해제
    ├── configure_phase   ← 레지스터 설정, 초기화
    ├── main_phase        ← 메인 트래픽, 테스트 시나리오
    └── shutdown_phase    ← 정리, 마지막 트랜잭션 완료 대기

실행 관계:
  run_phase와 sub-phase는 병렬로 실행됨
  즉, run_phase 안에서 코드를 작성하면 sub-phase와 동시에 동작

핵심: run_phase OR sub-phase 중 하나만 사용하는 것이 일반적
```

```systemverilog
// Sub-phase 활용 예시 (복잡한 테스트에서)
class complex_test extends uvm_test;
  // reset_phase: DUT 리셋
  task reset_phase(uvm_phase phase);
    phase.raise_objection(this);
    vif.rst_n <= 0;
    repeat(10) @(posedge vif.clk);
    vif.rst_n <= 1;
    repeat(5) @(posedge vif.clk);
    phase.drop_objection(this);
  endtask

  // configure_phase: 레지스터 초기화
  task configure_phase(uvm_phase phase);
    phase.raise_objection(this);
    reg_seq.start(env.reg_agent.sequencer);
    phase.drop_objection(this);
  endtask

  // main_phase: 메인 테스트 트래픽
  task main_phase(uvm_phase phase);
    phase.raise_objection(this);
    traffic_seq.start(env.data_agent.sequencer);
    phase.drop_objection(this);
  endtask

  // shutdown_phase: 파이프라인 flush
  task shutdown_phase(uvm_phase phase);
    phase.raise_objection(this);
    #(PIPELINE_DEPTH * CLK_PERIOD);
    phase.drop_objection(this);
  endtask
endclass
```

### Sub-Phase 사용 판단

| 상황 | 권장 | 이유 |
|------|------|------|
| 대부분의 테스트 | `run_phase`만 사용 | 단순하고 직관적 |
| Reset이 여러 번 | sub-phase | reset_phase를 반복 호출 가능 |
| 단계별 동기화 필요 | sub-phase | 모든 컴포넌트가 reset 완료 후 configure |
| IP-level 검증 | `run_phase` | 단순한 환경에 sub-phase는 과도 |
| SoC-level 통합 검증 | sub-phase | 복수 Agent 간 단계 동기화 필수 |

---

## UVM 환경 계층 구조

```
+------------------------------------------------------------------+
|  uvm_test (my_test)                                               |
|    - 시나리오 선택, Sequence 실행, Factory Override                |
|                                                                   |
|  +------------------------------------------------------------+  |
|  |  uvm_env (my_env)                                           |  |
|  |    - Agent, Scoreboard, Coverage 인스턴스화/연결              |  |
|  |                                                              |  |
|  |  +-----------+  +-----------+  +-----------+  +----------+  |  |
|  |  | Agent_A   |  | Agent_B   |  | Scoreboard|  | Coverage |  |  |
|  |  |           |  |           |  |           |  |          |  |  |
|  |  | +-------+ |  | +-------+ |  | - 비교    |  | - CG     |  |  |
|  |  | |Driver | |  | |Driver | |  | - 판정    |  | - CP     |  |  |
|  |  | +-------+ |  | +-------+ |  +-----------+  +----------+  |  |
|  |  | +-------+ |  | +-------+ |                               |  |
|  |  | |Monitor| |  | |Monitor| |                               |  |
|  |  | +-------+ |  | +-------+ |                               |  |
|  |  | +-------+ |  | +-------+ |                               |  |
|  |  | |Seqr   | |  | |Seqr   | |                               |  |
|  |  | +-------+ |  | +-------+ |                               |  |
|  |  +-----------+  +-----------+                               |  |
|  +------------------------------------------------------------+  |
+------------------------------------------------------------------+

규칙:
  - test가 env를 생성
  - env가 agent, scoreboard, coverage를 생성
  - agent가 driver, monitor, sequencer를 생성
  - 각 레벨이 자신의 하위만 생성 (계층 원칙)
```

---

## Q&A

**Q: UVM의 Phase가 왜 필요한가?**
> "복잡한 검증 환경에서 컴포넌트 생성→연결→실행→정리의 순서를 자동으로 보장하기 위해서다. Phase 없이는 build 전에 connect를 시도하거나, 모든 컴포넌트가 준비되기 전에 시뮬레이션이 시작될 수 있다. Phase 메커니즘이 이 순서를 강제하므로, 개별 컴포넌트는 자신의 Phase 함수만 구현하면 전체 순서가 자동으로 맞춰진다."

**Q: uvm_component와 uvm_object의 핵심 차이는?**
> "세 가지: (1) Phase — component는 Phase 콜백이 있고 object는 없다. (2) 계층 — component는 parent/child 트리에 속하고 object는 독립적. (3) 생명주기 — component는 시뮬레이션 내내 존재하고 object는 생성/소멸이 자유롭다. Driver, Monitor, Env는 component, Sequence Item, Transaction은 object이다."

**Q: Objection 메커니즘의 목적은?**
> "run_phase의 종료 시점을 제어한다. 어떤 컴포넌트든 objection을 raise하면 run_phase가 유지되고, 모든 objection이 drop되면 종료된다. 보통 test에서만 raise/drop하여 전체 시나리오 완료를 관리한다. drop을 빠뜨리면 시뮬레이션이 무한 대기하므로 주의가 필요하다."

**Q: Drain time이 필요한 이유는?**
> "Sequence가 마지막 트랜잭션을 보낸 직후 drop_objection하면, DUT 파이프라인에 아직 처리 중인 데이터가 있을 수 있다. 이 상태에서 run_phase가 종료되면 Scoreboard에서 expected는 있지만 actual이 도착하지 않아 false error가 발생한다. drain time으로 DUT가 모든 출력을 완료할 시간을 확보한다. `drop_objection(this, \"done\", 1000)` 형태로 지정하거나, phase_ready_to_end에서 컴포넌트가 자율적으로 지연을 관리할 수 있다."

**Q: run_phase의 sub-phase를 실무에서 사용하는가?**
> "IP-level 검증에서는 대부분 run_phase만 사용한다. sub-phase는 SoC-level 통합 검증처럼 여러 Agent가 '모두 리셋 완료 후 설정 시작', '모두 설정 완료 후 트래픽 시작' 같은 단계별 동기화가 필요할 때 유용하다. sub-phase의 핵심 가치는 UVM이 모든 컴포넌트의 해당 phase 완료를 보장한 후 다음 phase로 넘어간다는 점이다. 단, run_phase와 sub-phase는 병렬 실행되므로 둘 중 하나만 사용하는 것이 혼란을 방지한다."
