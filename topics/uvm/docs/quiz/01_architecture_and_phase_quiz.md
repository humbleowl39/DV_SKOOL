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
    **B**. `build_phase`는 top-down으로 실행되어 부모가 먼저 생성된 후 자식을 만들 수 있게 합니다. `connect_phase`는 반대로 bottom-up.

## Q2. (Understand)

`uvm_object`와 `uvm_component`의 핵심 차이 3가지를 짧게 답하세요.

??? answer "정답 / 해설"
    1. **Phase**: component만 가짐, object는 없음.
    2. **계층**: component는 parent/child 트리, object는 독립적.
    3. **생명주기**: component는 시뮬 내내, object는 자유 생성/소멸.

## Q3. (Apply)

다음 코드의 동작은? `phase.drop_objection(this, "done", 500);`

- [ ] A. 즉시 종료, 500은 무시
- [ ] B. 500ns drain time을 추가해 종료 지연
- [ ] C. 500 cycle 후 raise (의도와 반대)
- [ ] D. 500 ms 후 fatal

??? answer "정답 / 해설"
    **B**. 두 번째 인자는 description, 세 번째 인자가 drain time(시뮬레이션 시간 단위). 마지막 트랜잭션 처리 여유 확보.

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
    `run_phase`의 raise는 있지만 drop이 없으므로 objection 카운트가 0이 되지 않음 → `run_phase` 영원히 종료 안 됨 → **시뮬레이션 hang**. `drop_objection`을 호출해야 함.

## Q5. (Evaluate)

`run_phase`와 sub-phase(reset/configure/main/shutdown)를 **둘 다 사용하면 안 되는** 가장 큰 이유는?

- [ ] A. UVM 사양에서 금지
- [ ] B. run_phase와 sub-phase는 병렬 실행되어 타이밍이 직관적이지 않음
- [ ] C. 컴파일 에러 발생
- [ ] D. drain time이 적용 안 됨

??? answer "정답 / 해설"
    **B**. `run_phase`와 sub-phase는 병렬 실행되므로 둘에 코드를 분산하면 누가 먼저 끝나는지 직관적이지 않고 race condition을 유발. 사양상 금지는 아니지만 실무 권장은 둘 중 하나만 사용.
