---
title: "Quiz — Module 04: OOP → SystemVerilog / UVM 매핑"
---

[← Module 04 본문으로 돌아가기](../../04_sv_uvm_mapping/)

---

## Q1. (Remember)

SystemVerilog에서 캡슐화(내부 상태 은닉)를 표현하는 키워드는?

- [ ] A. `virtual`
- [ ] B. `extends`
- [ ] C. `local` / `protected`
- [ ] D. `rand`

<details>
<summary>정답 / 해설</summary>

**C (`local` / `protected`)**. 가시성 한정자로 필드를 외부 직접 접근으로부터 닫는 것이 캡슐화입니다 (`oop_spec.md` §7 매핑 표). `virtual`(A)은 다형성, `extends`(B)는 상속, `rand`(D)는 랜덤화에 쓰입니다.

</details>
## Q2. (Understand)

UVM의 `uvm_object` 콜백 `do_copy`/`do_compare`/`do_pack`은 어떤 객체 관계의 표현인가? 왜 그런가?

<details>
<summary>정답 / 해설</summary>

**CAN-DO 관계(인터페이스/역할)**의 표현입니다 (`oop_spec.md` §4.3, §7). 특별한 클래스를 추가로 상속하지 않고도 이 콜백들을 *구현하기만 하면* "deep-copy/compare/pack할 수 있는" 능력을 갖게 되기 때문입니다. 상속 계층(IS-A)을 강제하지 않고 능력만 선언하는 것이 CAN-DO의 핵심이며, 이는 인터페이스/믹스인 패턴에 해당합니다.

</details>
## Q3. (Apply)

에러 주입 driver로 동작을 바꾸되 base env·test 코드를 한 줄도 고치지 않으려면 무엇을 써야 하는가? 전제 조건은?

<details>
<summary>정답 / 해설</summary>

**factory type override**를 씁니다 — test의 build_phase에서 `my_driver::type_id::set_type_override(err_driver::get_type())`를 등록합니다 (`oop_spec.md` §7). **전제 조건**은 base가 driver를 `my_driver::type_id::create(...)`로 생성해야 한다는 것입니다 — `new`로 직접 생성한 객체는 factory override 대상이 되지 못합니다. 이것이 테스트벤치 수준의 OCP로, 수정 없이(닫힘) 추가로 확장(열림)하는 정석입니다.

</details>
## Q4. (Apply)

`uvm_driver #(REQ, RSP)`의 `#(REQ, RSP)`와 `virtual task run_phase(...)`는 각각 어떤 종류의 다형성인가?

- [ ] A. 둘 다 subtype 다형성
- [ ] B. 둘 다 parametric 다형성
- [ ] C. `#(REQ,RSP)`는 parametric, `virtual run_phase`는 subtype
- [ ] D. `#(REQ,RSP)`는 subtype, `virtual run_phase`는 parametric

<details>
<summary>정답 / 해설</summary>

**C**. 타입 파라미터로 임의 타입에 동작하는 `#(REQ, RSP)`는 **parametric polymorphism**이고, 런타임에 vtable로 dispatch되어 스케줄러가 구체 타입을 모른 채 자식의 메서드를 호출하는 `virtual run_phase`는 **subtype polymorphism**입니다 (`oop_spec.md` §3.4, §7). 두 다형성은 UVM 한 클래스 안에 공존합니다.

</details>
## Q5. (Analyze)

factory override를 등록했는데 동작이 바뀌지 않는다. 가장 흔한 원인과 확인 방법은?

<details>
<summary>정답 / 해설</summary>

가장 흔한 원인은 대상 객체를 **`new`로 직접 생성해 factory를 우회**한 것입니다 (`oop_spec.md` §7). factory override는 `type_id::create`로 생성된 객체에만 적용되므로, `new`로 만든 객체는 override 대상이 못 됩니다. 확인 방법은 해당 컴포넌트 생성부를 `grep`해 `type_id::create`를 쓰는지 점검하는 것입니다. 부차적으로 override 등록 시점이 대상 생성 *이후*면 늦으므로, build_phase 순서(부모 → 자식, top-down)도 함께 확인합니다.

</details>
## Q6. (Evaluate)

"`uvm_analysis_port`는 DIP와 Observer 패턴을 동시에 구현한다"는 주장을 평가하라.

<details>
<summary>정답 / 해설</summary>

**타당합니다.** 두 측면이 동시에 성립합니다.
- **DIP**: producer(monitor)와 consumer(scoreboard/coverage)가 추상 포트로 분리되어 서로의 구체 타입을 모릅니다 — `oop_spec.md` §5.5가 TLM 포트를 DIP의 정석 표현으로 명시합니다.
- **Observer**: 한 상태(트랜잭션)를 여러 구독자에게 1:N broadcast하는 것은 GoF Observer의 정의 그대로입니다 (`design_pattern_onboarding.md` Behavioral, Module 03 §4.3).

한 메커니즘이 여러 원칙/패턴을 동시에 구현하는 것은 흔하며, 이는 패턴이 SOLID 위에 앉는다는 위계와도 일관됩니다.

</details>
