# Quiz — Module 04: config_db & Factory

[← Module 04 본문으로 돌아가기](../04_config_db_factory.md)

---

## Q1. (Remember)

`uvm_config_db#(virtual apb_if)::set(this, "env.agent.*", "vif", vif);`에서 첫 번째 인자 `this`의 의미는?

- [ ] A. set이 적용될 자식 컴포넌트
- [ ] B. set의 시작 컨텍스트 (계층 경로의 baseline)
- [ ] C. 받는 컴포넌트의 부모
- [ ] D. virtual interface의 실제 인스턴스

??? answer "정답 / 해설"
    **B**. 두 번째 인자(`"env.agent.*"`)가 첫 번째 인자 기준의 상대 경로. `this`가 test이면 실제 경로는 `uvm_test_top.env.agent.*`. `null`을 주면 절대 경로처럼 동작.

## Q2. (Understand)

`config_db::get`의 반환값을 무시하면 왜 위험한가?

??? answer "정답 / 해설"
    get이 실패해도 함수는 0을 반환하고 핸들은 NULL/default 그대로 둡니다. 이 상태에서 시뮬을 진행하면 silent default로 동작하다가 다운스트림에서 false error로 나타나 디버그가 어려워집니다. 항상 `if (!get(...)) `uvm_fatal(...)` 패턴 권장.

## Q3. (Apply)

모든 환경에서 `my_driver`를 `my_err_driver`로 한 번에 교체하려면?

- [ ] A. `set_inst_override_by_name`
- [ ] B. `set_type_override_by_type(my_driver::get_type(), my_err_driver::get_type())`
- [ ] C. `config_db#(my_driver)::set(...)`
- [ ] D. `uvm_factory::create("my_err_driver", "drv")`

??? answer "정답 / 해설"
    **B**. type override는 모든 인스턴스에 적용. instance override는 특정 경로만. 설정 전달이 아니라 *생성 타입 변경*이므로 config_db는 부적절.

## Q4. (Analyze)

`uvm_test_top.env.agent.*`로 set한 vif가 `env.apb_agent.driver`에서 get 실패합니다. 가장 가능성 높은 원인은?

- [ ] A. set 시점이 build_phase보다 늦음 (가능)
- [ ] B. agent의 인스턴스 이름이 `apb_agent`라서 set 경로 `env.agent.*`와 매칭 안 됨
- [ ] C. virtual interface 타입 mismatch
- [ ] D. 위 모두 가능 — set 시점, 인스턴스 이름, 타입 모두 점검 필요

??? answer "정답 / 해설"
    **D**. 모두 가능한 원인입니다. 디버그: `uvm_config_db::dump()` 호출, `factory.print()`, `uvm_top.print_topology()`로 가시화.

## Q5. (Evaluate)

다음 중 instance override가 적절하고 type override가 부적절한 시나리오는?

- [ ] A. 환경 전체의 모든 driver를 error-injecting 변형으로 한 번에 교체
- [ ] B. `env.cpu_agent.driver`에만 시그널 글리치를 주입하고 다른 driver는 정상 유지
- [ ] C. 모든 sequence item을 확장 클래스로 교체
- [ ] D. config_db로 전달되는 cfg 객체를 다른 타입으로 교체

??? answer "정답 / 해설"
    **B**. 특정 인스턴스만 변형하고 다른 동일 타입은 정상 유지하려면 instance override가 정답.
