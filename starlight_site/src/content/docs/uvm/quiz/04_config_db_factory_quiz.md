---
title: "Quiz — Module 04: config_db & Factory"
---

[← Module 04 본문으로 돌아가기](../../04_config_db_factory/)

---

## Q1. (Remember)

`uvm_config_db#(virtual apb_if)::set(this, "env.agent.*", "vif", vif);`에서 첫 번째 인자 `this`의 의미는?

- [ ] A. set이 적용될 자식 컴포넌트
- [ ] B. set의 시작 컨텍스트 (계층 경로의 baseline)
- [ ] C. 받는 컴포넌트의 부모
- [ ] D. virtual interface의 실제 인스턴스

<details>
<summary>정답 / 해설</summary>

**B**. `config_db::set`의 첫 번째 인자는 두 번째 인자(경로 문자열)의 기준점이 되는 컨텍스트입니다. `this`가 test 클래스 인스턴스이면 실제 full path는 `uvm_test_top.env.agent.*`로 해석됩니다. `null`을 전달하면 경로 문자열이 UVM 계층 최상위부터의 절대 경로로 동작합니다. A(set이 적용될 자식)는 두 번째 인자의 역할이고, C(받는 컴포넌트의 부모)와 D(virtual interface 인스턴스)는 이 인자와 무관합니다.

</details>
## Q2. (Understand)

`config_db::get`의 반환값을 무시하면 왜 위험한가?

<details>
<summary>정답 / 해설</summary>

`config_db::get`이 실패하면 함수는 0(false)을 반환하지만 이미 선언된 핸들 변수는 null 또는 기본값인 채로 남습니다. 반환값을 무시하면 이 사실을 알 방법이 없으므로, 이후 코드가 null 핸들로 트랜잭션을 drive하거나 virtual interface에 접근하다가 전혀 다른 위치에서 segfault나 UVM_ERROR로 나타납니다. 실제 원인(경로 불일치, set 누락)과 증상이 수십 줄 떨어져 있어 디버그가 매우 어려워집니다. `if (!uvm_config_db#(...)::get(this, "", "vif", vif)) \`uvm_fatal(...)`` 패턴으로 즉시 오류를 발생시키면 원인을 build_phase에서 바로 포착할 수 있습니다.

</details>
## Q3. (Apply)

모든 환경에서 `my_driver`를 `my_err_driver`로 한 번에 교체하려면?

- [ ] A. `set_inst_override_by_name`
- [ ] B. `set_type_override_by_type(my_driver::get_type(), my_err_driver::get_type())`
- [ ] C. `config_db#(my_driver)::set(...)`
- [ ] D. `uvm_factory::create("my_err_driver", "drv")`

<details>
<summary>정답 / 해설</summary>

**B**. Factory의 type override는 등록된 특정 타입을 생성하는 모든 `type_id::create` 호출에 일괄 적용됩니다. 따라서 환경 전체에 흩어진 `my_driver` 인스턴스를 전부 `my_err_driver`로 교체하려면 이 방법이 가장 간결합니다. A(instance override)는 특정 경로의 단일 인스턴스만 변경하므로 "모든 환경"이라는 요건에 맞지 않습니다. C(config_db)는 설정값 전달 용도이지 생성 타입을 변경하지 않습니다. D의 `uvm_factory::create` 형식은 UVM API에 존재하지 않는 잘못된 표기입니다.

</details>
## Q4. (Analyze)

`uvm_test_top.env.agent.*`로 set한 vif가 `env.apb_agent.driver`에서 get 실패합니다. 가장 가능성 높은 원인은?

- [ ] A. set 시점이 build_phase보다 늦음 (가능)
- [ ] B. agent의 인스턴스 이름이 `apb_agent`라서 set 경로 `env.agent.*`와 매칭 안 됨
- [ ] C. virtual interface 타입 mismatch
- [ ] D. 위 모두 가능 — set 시점, 인스턴스 이름, 타입 모두 점검 필요

<details>
<summary>정답 / 해설</summary>

**D**. config_db get 실패의 원인은 세 가지가 독립적으로 또는 복합적으로 작용합니다. 첫째, set 경로의 인스턴스 이름이 `agent`인데 실제 이름이 `apb_agent`이면 wildcard `*`가 있어도 중간 경로 불일치로 매칭이 안 됩니다. 둘째, set이 build_phase보다 늦게 호출되면 get 시점에 값이 아직 없습니다. 셋째, set과 get의 parameterized 타입이 다르면 타입 불일치로 silently 실패합니다. 디버그 시 `uvm_config_db::dump()`로 set 기록을 출력하고, `uvm_top.print_topology()`로 실제 인스턴스 이름을 확인하는 것이 가장 빠릅니다.

</details>
## Q5. (Evaluate)

다음 중 instance override가 적절하고 type override가 부적절한 시나리오는?

- [ ] A. 환경 전체의 모든 driver를 error-injecting 변형으로 한 번에 교체
- [ ] B. `env.cpu_agent.driver`에만 시그널 글리치를 주입하고 다른 driver는 정상 유지
- [ ] C. 모든 sequence item을 확장 클래스로 교체
- [ ] D. config_db로 전달되는 cfg 객체를 다른 타입으로 교체

<details>
<summary>정답 / 해설</summary>

**B**. instance override는 경로 문자열로 특정 컴포넌트 하나만 대상으로 삼기 때문에, `env.cpu_agent.driver`만 글리치 주입 버전으로 바꾸고 나머지 driver들은 원래 타입 그대로 유지할 수 있습니다. 만약 type override를 적용하면 환경 전체의 모든 `my_driver` 인스턴스가 교체되어 A의 시나리오가 됩니다. C(모든 sequence item 교체)와 D(config 객체 타입 교체)는 단일 인스턴스 격리가 필요 없으므로 type override가 더 적합합니다.

</details>
