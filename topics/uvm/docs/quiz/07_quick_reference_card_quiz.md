# Quiz — Module 07: Quick Reference Card

이 페이지는 참조용 치트시트라 별도 종합 퀴즈로 진행합니다. 본 카드의 내용을 빠르게 떠올릴 수 있는지 확인하세요.

[← Module 07 본문으로 돌아가기](../07_quick_reference_card.md)

---

## Q1. (Remember)

UVM 환경 계층의 최상위는 무엇인가?

??? answer "정답 / 해설"
    최상위는 `uvm_test_top`입니다. 이것은 UVM 프레임워크가 `+UVM_TESTNAME=<class>` 인자를 받아 자동으로 생성하는 인스턴스 이름이며, 사용자가 `uvm_test`를 상속해 만든 test 클래스가 이 이름으로 인스턴스화됩니다. 그 아래로 Env → Agent → Driver/Monitor/Sequencer 순서로 계층이 내려갑니다. 이 계층 구조를 알아야 config_db의 경로 문자열이 `"uvm_test_top.env.agent.*"`처럼 어떻게 구성되는지 이해할 수 있습니다.

## Q2. (Recall)

다음 매크로의 차이를 한 줄씩 답하세요: `uvm_component_utils`, `uvm_object_utils`, `uvm_do`, `uvm_do_with`.

??? answer "정답 / 해설"
    - `uvm_component_utils(T)`: T 클래스를 Factory에 component로 등록합니다. `type_id::create("name", parent)` 호출 시 parent 인자를 받는 생성자가 필요하며, Phase callback과 계층 트리에 참여합니다.
    - `uvm_object_utils(T)`: T 클래스를 Factory에 object로 등록합니다. `type_id::create("name")` 형태로 생성하며 Phase가 없는 데이터 컨테이너용입니다.
    - `uvm_do(req)`: Sequence의 body() 안에서 item을 create → randomize → start_item → finish_item 순으로 한 번에 처리하는 편의 매크로입니다.
    - `uvm_do_with(req, { ... })`: `uvm_do`에 inline constraint를 추가해 randomize 범위를 그 자리에서 제한합니다.

## Q3. (Apply)

UVM 시뮬레이션이 hang일 때 **가장 먼저** 확인할 3가지는?

??? answer "정답 / 해설"
    1. **`drop_objection` 누락**: `run_phase`에서 `raise_objection`을 호출했는지, 그리고 모든 종료 경로에서 `drop_objection`이 반드시 실행되는지 확인합니다. Exception path나 조건 분기로 drop을 건너뛰면 hang이 됩니다.
    2. **`item_done` 누락**: Driver의 `forever` 루프에서 `get_next_item` 후에 `item_done`을 호출하지 않으면 Sequencer가 영원히 대기해 트랜잭션 공급이 멈춥니다.
    3. **`wait` 조건이 영원히 false**: `wait(vif.valid)`처럼 DUT의 특정 신호를 기다리는데, DUT 리셋이 완료되지 않았거나 자극이 인가되지 않아 해당 신호가 절대 변하지 않는 경우입니다. Waveform이 있다면 신호 변화 여부를 확인하고, 없다면 wait 앞에 timeout 로직을 추가합니다.

## Q4. (Apply)

config_db 경로가 의심될 때 디버그 명령은?

- [ ] A. `factory.print()`
- [ ] B. `uvm_top.print_topology()`
- [ ] C. `uvm_config_db::dump()`
- [ ] D. `uvm_report_object::print_state()`

??? answer "정답 / 해설"
    **C**. `uvm_config_db::dump()`는 현재까지 모든 `config_db::set` 호출 기록과 각 항목의 경로·타입·값을 출력합니다. 설정 경로가 의심될 때 이 출력을 보면 set된 경로와 get을 시도한 경로를 비교해 불일치를 즉시 찾을 수 있습니다. A(`factory.print()`)는 Factory에 등록된 타입과 override 설정을 보여주므로 타입 변경 문제에 유용하고, B(`uvm_top.print_topology()`)는 컴포넌트 계층 구조와 실제 인스턴스 이름을 보여줘 config_db 경로 검증에 보조로 활용합니다. D(`uvm_report_object::print_state()`)는 존재하지 않는 API입니다.

## Q5. (Evaluate)

다음 5-Whys 골든 룰 중 잘못된 것은?

- [ ] A. raise 없이 drop → UVM_ERROR
- [ ] B. component는 `type_id::create`로만 생성
- [ ] C. Monitor는 분석 포트로 broadcast하되 절대 driving 안 함
- [ ] D. Phase는 build → run → connect 순서

??? answer "정답 / 해설"
    **D**. "build → run → connect" 순서가 틀렸습니다. 정확한 UVM phase 순서는 **build → connect → end_of_elaboration → start_of_simulation → run → extract → check → report → final**입니다. `connect`는 반드시 `build` 직후에 와야 합니다. 이는 build에서 생성된 컴포넌트 인스턴스가 있어야 TLM 포트 연결이 가능하고, run phase가 시작되기 전에 모든 연결이 완료되어야 하기 때문입니다. 나머지 A·B·C는 UVM의 핵심 원칙으로 모두 올바른 진술입니다.
