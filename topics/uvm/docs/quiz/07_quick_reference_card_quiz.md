# Quiz — Module 07: Quick Reference Card

이 페이지는 참조용 치트시트라 별도 종합 퀴즈로 진행합니다. 본 카드의 내용을 빠르게 떠올릴 수 있는지 확인하세요.

[← Module 07 본문으로 돌아가기](../07_quick_reference_card.md)

---

## Q1. (Remember)

UVM 환경 계층의 최상위는 무엇인가?

??? answer "정답 / 해설"
    `uvm_test_top` (UVM 자동 인스턴스명) — `uvm_test`를 상속한 사용자 test 클래스의 인스턴스. **Test → Env → Agent → Driver/Monitor/Sequencer**.

## Q2. (Recall)

다음 매크로의 차이를 한 줄씩 답하세요: `uvm_component_utils`, `uvm_object_utils`, `uvm_do`, `uvm_do_with`.

??? answer "정답 / 해설"
    - `uvm_component_utils(T)` — component 클래스를 Factory에 등록 (parent 인자 있는 생성자)
    - `uvm_object_utils(T)` — object 클래스를 Factory에 등록 (name만 있는 생성자)
    - `uvm_do(req)` — sequence 안에서 `create + randomize + send` 한 번에
    - `uvm_do_with(req, { ... })` — `uvm_do`에 in-line constraint 추가

## Q3. (Apply)

UVM 시뮬레이션이 hang일 때 **가장 먼저** 확인할 3가지는?

??? answer "정답 / 해설"
    1. **`drop_objection` 누락** — `run_phase`의 raise/drop 짝 검사
    2. **`item_done` 누락** — Driver의 forever 루프 + sequencer item 흐름
    3. **wait 조건이 영원히 false** — `wait(condition)`의 condition이 변하지 않는 케이스

## Q4. (Apply)

config_db 경로가 의심될 때 디버그 명령은?

- [ ] A. `factory.print()`
- [ ] B. `uvm_top.print_topology()`
- [ ] C. `uvm_config_db::dump()`
- [ ] D. `uvm_report_object::print_state()`

??? answer "정답 / 해설"
    **C**. `uvm_config_db::dump()`는 모든 set 기록과 매칭 상태를 출력. 보조: `factory.print()` (등록된 type + override), `uvm_top.print_topology()` (컴포넌트 트리).

## Q5. (Evaluate)

다음 5-Whys 골든 룰 중 잘못된 것은?

- [ ] A. raise 없이 drop → UVM_ERROR
- [ ] B. component는 `type_id::create`로만 생성
- [ ] C. Monitor는 분석 포트로 broadcast하되 절대 driving 안 함
- [ ] D. Phase는 build → run → connect 순서

??? answer "정답 / 해설"
    **D**. 정확한 순서는 **build → connect → end_of_elaboration → start_of_simulation → run → extract → check → report → final**. `connect`는 build와 run 사이.
