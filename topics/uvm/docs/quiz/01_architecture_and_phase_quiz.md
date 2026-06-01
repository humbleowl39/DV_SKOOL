# Quiz — Module 01: UVM 아키텍처 & Phase

본 모듈의 핵심 개념 이해도를 점검합니다. 정답은 펼치면 보입니다.

[← Module 01 본문으로 돌아가기](../01_architecture_and_phase.md)

---

## Q1. (Remember)

UVM Phase 중 **컴포넌트 인스턴스를 생성하는** Phase는 무엇이며, 어떤 순서로 실행되는가?

- [ ] A. `connect_phase`, top → down
- [ ] B. `build_phase`, top → down
- [ ] C. `build_phase`, bottom → up
- [ ] D. `run_phase`, 병렬

??? answer "정답 / 해설"
    **B**. `build_phase`가 top-down으로 실행되는 이유는 부모 컴포넌트가 먼저 존재해야 자식 인스턴스를 `type_id::create("child", this)`로 생성할 수 있기 때문입니다. 반대로 `connect_phase`가 bottom-up인 이유는, 하위 컴포넌트의 포트가 먼저 확정되어야 상위에서 TLM 연결을 완성할 수 있기 때문입니다. A는 connect_phase의 방향을 build_phase에 잘못 적용한 오답이고, C는 방향이 반대입니다. D의 `run_phase`는 병렬이 맞지만 컴포넌트 생성과는 무관합니다.

## Q2. (Understand)

`uvm_object`와 `uvm_component`의 핵심 차이 3가지를 짧게 답하세요.

??? answer "정답 / 해설"
    1. **Phase**: `uvm_component`만 build·connect·run 등의 phase callback을 가집니다. `uvm_object`는 phase 메커니즘에 참여하지 않으므로 sequence item처럼 "순간" 생성·소멸되는 데이터 컨테이너에 적합합니다.
    2. **계층**: component는 `parent` 인자를 통해 부모-자식 트리를 형성하고 `uvm_top.print_topology()`로 가시화됩니다. object는 독립적으로 생성되며 계층 트리에 나타나지 않습니다.
    3. **생명주기**: component는 시뮬레이션 내내 살아있어 환경의 구조를 이루고, object는 필요할 때 생성·소멸되므로 트랜잭션처럼 짧은 생명주기의 데이터에 어울립니다.

## Q3. (Apply)

다음 코드의 동작은? `phase.drop_objection(this, "done", 500);`

- [ ] A. 즉시 종료, 500은 무시
- [ ] B. 500ns drain time을 추가해 종료 지연
- [ ] C. 500 cycle 후 raise (의도와 반대)
- [ ] D. 500 ms 후 fatal

??? answer "정답 / 해설"
    **B**. `phase.drop_objection(this, "done", 500)`에서 세 번째 인자가 drain time(시뮬레이션 시간 단위)입니다. drop을 호출해도 즉시 종료되지 않고 500 시간 단위만큼 시뮬레이션을 추가 진행시켜, 마지막 트랜잭션이 DUT를 통과해 Scoreboard까지 도달할 여유를 줍니다. A는 세 번째 인자를 무시한다고 했지만 실제로는 drain time으로 해석됩니다. C와 D는 raise와 ms 해석을 혼동한 오답입니다.

## Q4. (Analyze)

다음 코드의 결과를 trace하세요.
```systemverilog
class my_test extends uvm_test;
  task run_phase(uvm_phase phase);
    phase.raise_objection(this);
    my_seq.start(env.agent.sqr);
    // drop_objection 누락
  endtask
endclass
```

??? answer "정답 / 해설"
    UVM의 `run_phase`는 모든 컴포넌트의 objection 카운트 합이 0이 되어야 종료됩니다. 이 코드에서 `raise_objection`을 호출해 카운트를 올렸지만, 시퀀스가 완료된 후 `drop_objection`을 호출하지 않아 카운트가 영원히 0이 되지 않습니다. 결과적으로 `run_phase`는 종료되지 않고 시뮬레이션이 hang 상태에 빠집니다. 수정 방법은 `my_seq.start(env.agent.sqr)` 직후에 `phase.drop_objection(this)`를 추가하는 것입니다.

## Q5. (Evaluate)

`run_phase`와 sub-phase(reset/configure/main/shutdown)를 **둘 다 사용하면 안 되는** 가장 큰 이유는?

- [ ] A. UVM 사양에서 금지
- [ ] B. run_phase와 sub-phase는 병렬 실행되어 타이밍이 직관적이지 않음
- [ ] C. 컴파일 에러 발생
- [ ] D. drain time이 적용 안 됨

??? answer "정답 / 해설"
    **B**. UVM 사양에서 `run_phase`와 reset/configure/main/shutdown 같은 sub-phase는 동시에(병렬로) 실행됩니다. 따라서 둘 모두에 코드를 넣으면 어떤 phase가 먼저 objection을 내리는지 예측하기 어렵고, 초기화 시퀀스와 main 트래픽이 뒤섞이는 race condition이 생깁니다. A(사양 금지)는 사실이 아니고, C(컴파일 에러)는 발생하지 않으며, D(drain time 무효화)는 관련 없습니다. 실무 권고는 sub-phase만 사용하거나 `run_phase`만 사용하고 둘을 혼용하지 않는 것입니다.
