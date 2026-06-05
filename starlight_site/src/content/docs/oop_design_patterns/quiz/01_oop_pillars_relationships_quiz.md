---
title: "Quiz — Module 01: OOP 4기둥 & 객체 관계"
---

[← Module 01 본문으로 돌아가기](../../01_oop_pillars_relationships/)

---

## Q1. (Remember)

객체지향의 네 기둥(four pillars)에 해당하지 *않는* 것은?

- [ ] A. Encapsulation (캡슐화)
- [ ] B. Abstraction (추상화)
- [ ] C. Inheritance (상속)
- [ ] D. Compilation (컴파일)

<details>
<summary>정답 / 해설</summary>

**D**. 네 기둥은 Encapsulation, Abstraction, Inheritance, Polymorphism입니다 (`oop_spec.md` §3). Compilation은 언어 처리 과정일 뿐 OOP의 기둥이 아닙니다. 다형성(Polymorphism)이 빠지고 컴파일이 들어간 것이 함정입니다.

</details>
## Q2. (Understand)

캡슐화(Encapsulation)와 추상화(Abstraction)는 둘 다 "숨긴다"고 한다. 각각 무엇을 숨기는가?

<details>
<summary>정답 / 해설</summary>

캡슐화는 객체의 **내부 상태가 어떻게 저장·관리되는지**(구현 세부)를 숨기고, 추상화는 **지금 다루는 것이 어떤 구체 타입인지**를 숨깁니다 (`oop_spec.md` §3.2). 예를 들어 `BankAccount`가 balance를 어떻게 저장하는지 감추는 것은 캡슐화이고, driver가 `uvm_sequence_item`을 AXI인지 PCIe인지 모른 채 다루는 것은 추상화입니다. 둘은 배타적이지 않고 한 객체에서 함께 작동합니다.

</details>
## Q3. (Apply)

`Car HAS-A Engine`을 모델링하려 한다. 다음 중 옳은 접근은?

- [ ] A. `class Car extends Engine` — 상속으로 재사용
- [ ] B. `class Car { Engine engine; }` — 합성으로 보유
- [ ] C. Engine을 Car의 부모로 두기
- [ ] D. 둘을 하나의 클래스로 합치기

<details>
<summary>정답 / 해설</summary>

**B**. `Car HAS-A Engine`은 *보유* 관계이지 IS-A(상속) 관계가 아닙니다. Car는 Engine의 일종이 아니므로 상속(A, C)은 거짓 IS-A를 만들어 LSP를 위반합니다. 합성(composition)으로 Car가 Engine을 필드로 보유하는 것이 옳습니다 (`oop_spec.md` §3.3, §4.2). IS-A가 불분명하면 합성을 택하라는 원칙의 전형적 사례입니다.

</details>
## Q4. (Apply)

`uvm_agent`가 driver와 monitor를 생성·파괴하여 agent가 사라지면 함께 사라진다. 이 HAS-A 관계의 이름은?

- [ ] A. Association
- [ ] B. Aggregation
- [ ] C. Composition
- [ ] D. Inheritance

<details>
<summary>정답 / 해설</summary>

**C (Composition)**. 소유자(agent)가 소유물(driver/monitor)을 *생성·파괴*하여 수명주기가 묶이는 것이 composition입니다 (`oop_spec.md` §4.2). Association(A)은 둘이 독립적으로 존재하고, Aggregation(B)은 소유자가 없어도 소유물이 독립 존재할 수 있으며, Inheritance(D)는 HAS-A가 아니라 IS-A입니다.

</details>
## Q5. (Analyze)

한 클래스에 동사(메서드)가 지나치게 많을 때 이는 무엇의 신호이며, OOAD 휴리스틱상 어떻게 해야 하는가?

<details>
<summary>정답 / 해설</summary>

이는 **SRP(단일 책임 원칙) 위반의 신호**입니다 (`oop_spec.md` §6.1, §5.1). OOAD에서 요구사항의 명사는 후보 클래스/속성, 동사는 후보 메서드/책임으로 매핑되는데, 한 클래스가 동사를 너무 많이 가지면 책임이 여럿이라는 뜻이므로 **클래스를 분리**해야 합니다. 단, 무작정 줄 수를 줄이는 게 아니라 "바뀌는 이유"가 여럿일 때 그 축으로 나누는 것입니다.

</details>
## Q6. (Evaluate)

"코드 재사용을 위해 `LoggingMixin`이라는 기능을 가진 클래스를 상속해 logging 능력을 얻겠다"는 설계는 IS-A 관점에서 적절한가? 더 나은 대안은?

<details>
<summary>정답 / 해설</summary>

IS-A 관계가 거짓이면 **부적절**합니다 — 대상 클래스가 "is a logging-thing"이 아니라 단지 "can log"라면 상속은 거짓 IS-A를 만들어 부모 변경이 자식을 깨뜨립니다 (`oop_spec.md` §3.3). 더 나은 대안은 **CAN-DO 관계**(인터페이스/역할)로 모델링하는 것입니다 — `Loggable` 인터페이스를 구현해 "log할 수 있는" 능력만 선언하면, 상속 계층을 강제하지 않고도 능력을 부여할 수 있습니다 (`oop_spec.md` §4.3). SystemVerilog의 `do_copy`/`do_compare` 콜백이 이 방식입니다.

</details>
