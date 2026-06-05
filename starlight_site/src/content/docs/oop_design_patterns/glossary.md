---
title: "OOP & 디자인 패턴 용어집"
---

이 페이지는 본 코스에서 사용되는 OOP·SOLID·디자인 패턴 핵심 용어 정의 모음입니다. 항목은 ISO 11179 형식을 따릅니다 (**Definition / Source / Related / Example / See also**).

:::tip[검색 활용]
상단 검색창에 용어를 입력하면 본문에서의 사용처도 함께 찾을 수 있습니다.
:::
---

## A — Abstraction / Abstract Class

### Abstraction (추상화)

**Definition.** 객체의 본질적 특징만 노출하고 구현 세부와 구체 타입을 감추는 객체지향 기법.

**Source.** `oop_spec.md` §3.2 (The Four Pillars — Abstraction).

**Related.** Encapsulation, Polymorphism, Abstract Class.

**Example.**
```cpp
abstract class Shape {
    abstract double area();   // what, not how
}
```

**See also.** [Module 01 — OOP 4기둥 & 객체 관계](../01_oop_pillars_relationships/)

### Abstract Class (추상 클래스)

**Definition.** 직접 인스턴스화할 수 없고 상속을 통해서만 사용되는, 추상 메서드를 포함하는 클래스.

**Source.** `oop_spec.md` §7 (SV/UVM 매핑 — `virtual class uvm_object`).

**Related.** Abstraction, Inheritance, virtual class.

**Example.** SystemVerilog의 `virtual class uvm_object`는 직접 `new` 할 수 없고 상속해서만 씁니다.

**See also.** [Module 04 — OOP → SystemVerilog / UVM 매핑](../04_sv_uvm_mapping/)

---

## C — CAN-DO / Composition

### CAN-DO (인터페이스 / 역할 관계)

**Definition.** 상속 계층과 무관하게 클래스가 특정 능력·역할을 수행할 수 있음을 선언하는 객체 관계.

**Source.** `oop_spec.md` §4.3 (Object Relationships — CAN-DO).

**Related.** Interface, Mixin, do_copy/do_compare 콜백.

**Example.** `uvm_object`의 `do_copy`/`do_compare`/`do_pack` 콜백을 구현하면, 특별한 클래스를 상속하지 않고도 deep-copy·compare·pack을 *할 수 있게* 됩니다.

**See also.** [Module 01](../01_oop_pillars_relationships/)

### Composition (합성)

**Definition.** 소유 객체가 소유된 객체를 생성·파괴하여 둘의 수명주기가 묶이는 HAS-A 관계의 한 형태.

**Source.** `oop_spec.md` §4.2 (HAS-A 표 — Composition).

**Related.** HAS-A, Aggregation, Association.

**Example.** `uvm_agent`가 driver와 monitor를 합성 — agent가 파괴되면 driver·monitor도 함께 파괴됩니다.

**See also.** [Module 01](../01_oop_pillars_relationships/)

---

## D — Design Pattern / DIP / Dependency Injection

### Design Pattern (디자인 패턴)

**Definition.** 소프트웨어 설계에서 반복적으로 발생하는 문제에 대한 검증된 재사용 가능한 해법으로, 완성된 코드가 아니라 구조의 청사진.

**Source.** `design_pattern_onboarding.md` Overview.

**Related.** GoF 23, Creational, Structural, Behavioral, OOP 4기둥, SOLID.

**Example.** "여기 Factory 쓰자"처럼 한 구절로 설계 의도를 팀에 전달하는 공통 어휘 역할을 합니다.

**See also.** [Module 03 — GoF 23 디자인 패턴 개요](../03_gof_design_patterns/)

### DIP (Dependency Inversion Principle)

**Definition.** 고수준 모듈과 저수준 모듈이 모두 추상에 의존하도록 하여 구체 클래스에 대한 직접 의존을 제거하는 SOLID 원칙.

**Source.** `oop_spec.md` §5.5 (SOLID — DIP).

**Related.** SOLID, Abstraction, TLM Analysis Port, Dependency Injection.

**Example.** UVM의 `uvm_analysis_port`는 producer와 consumer를 추상 포트로 분리하는 DIP의 정석 구현입니다.

**See also.** [Module 02 — SOLID 설계 원칙](../02_solid_principles/)

### Dependency Injection (의존성 주입)

**Definition.** 객체가 필요로 하는 의존성을 스스로 생성하지 않고 외부에서 주입받는 설계 기법.

**Source.** `oop_spec.md` §7 (SV/UVM 매핑 — `uvm_config_db::set/get`).

**Related.** DIP, config_db, Virtual Interface.

**Example.** `uvm_config_db#(virtual my_if)::set/get`으로 driver에 virtual interface를 주입합니다.

**See also.** [Module 04](../04_sv_uvm_mapping/)

---

## E — Encapsulation

### Encapsulation (캡슐화)

**Definition.** 데이터와 그 데이터를 다루는 메서드를 하나의 단위로 묶고 내부 상태를 외부로부터 감추는 객체지향 기법.

**Source.** `oop_spec.md` §3.1 (The Four Pillars — Encapsulation).

**Related.** Abstraction, local/protected, Interface.

**Example.**
```systemverilog
class my_item extends uvm_sequence_item;
  protected int _tag;   // 외부 직접 접근 차단
endclass
```

**See also.** [Module 01](../01_oop_pillars_relationships/)

---

## F — Factory Method

### Factory Method (팩토리 메서드)

**Definition.** 객체 생성 인터페이스를 정의하되 어느 클래스를 인스턴스화할지는 서브클래스가 결정하도록 위임하는 Creational 디자인 패턴.

**Source.** `design_pattern_onboarding.md` Creational; `oop_spec.md` §7 (UVM factory = OCP).

**Related.** Creational, OCP, Abstract Factory, type_id::create.

**Example.** UVM의 `my_driver::type_id::create("drv", this)`는 생성을 factory에 위임하여 이후 override를 가능하게 합니다.

**See also.** [Module 03](../03_gof_design_patterns/) · [Module 04](../04_sv_uvm_mapping/)

---

## G — GoF

### GoF (Gang of Four)

**Definition.** 23개의 객체지향 디자인 패턴을 creational·structural·behavioral 세 그룹으로 분류해 정리한 패턴 카탈로그.

**Source.** `design_pattern_onboarding.md` The GoF 23 Classification.

**Related.** Design Pattern, Creational, Structural, Behavioral.

**Example.** Creational 5(Singleton, Factory Method, Abstract Factory, Builder, Prototype) + Structural 7 + Behavioral 11 = 23개.

**See also.** [Module 03](../03_gof_design_patterns/)

---

## H — HAS-A

### HAS-A (보유 관계)

**Definition.** 한 객체가 다른 객체의 참조를 보유하는 객체 관계로, 수명주기에 따라 association·aggregation·composition으로 나뉨.

**Source.** `oop_spec.md` §4.2 (Object Relationships — HAS-A).

**Related.** Composition, Aggregation, Association, IS-A.

**Example.** `uvm_agent HAS-A uvm_driver, uvm_monitor, uvm_sequencer`.

**See also.** [Module 01](../01_oop_pillars_relationships/)

---

## I — Inheritance / IS-A / ISP

### Inheritance (상속)

**Definition.** 서브클래스가 슈퍼클래스의 필드와 메서드를 획득하여 확장·재정의하는 객체지향 기법(IS-A 관계).

**Source.** `oop_spec.md` §3.3 (The Four Pillars — Inheritance).

**Related.** IS-A, Polymorphism, extends, Composition.

**Example.** `class my_driver extends uvm_driver#(my_item)`.

**See also.** [Module 01](../01_oop_pillars_relationships/)

### IS-A (상속 / 일반화 관계)

**Definition.** 서브클래스가 슈퍼클래스의 자리에 대체 가능한, 상속을 통한 일반화 객체 관계.

**Source.** `oop_spec.md` §4.1 (Object Relationships — IS-A).

**Related.** Inheritance, LSP, HAS-A.

**Example.** `my_axi_driver IS-A uvm_driver IS-A uvm_component IS-A uvm_object`.

**See also.** [Module 01](../01_oop_pillars_relationships/)

### ISP (Interface Segregation Principle)

**Definition.** 클라이언트가 사용하지 않는 인터페이스에 의존하도록 강요받지 않게 큰 인터페이스를 역할별 작은 인터페이스로 분리하는 SOLID 원칙.

**Source.** `oop_spec.md` §5.4 (SOLID — ISP).

**Related.** SOLID, Interface, SRP.

**Example.** 30개 메서드의 `IVipControl` 대신 `IConnectable`·`IResettable`·`IConfigurable`로 분리.

**See also.** [Module 02](../02_solid_principles/)

---

## L — LSP

### LSP (Liskov Substitution Principle)

**Definition.** 서브타입이 그 기반 타입을 대체해도 프로그램의 정확성이 유지되어야 한다는 SOLID 원칙.

**Source.** `oop_spec.md` §5.3 (SOLID — LSP).

**Related.** SOLID, IS-A, Inheritance.

**Example.** 버스를 구동하지 않는 `passive_driver`가 `uvm_driver`를 상속하면 active driver의 대체물이 아니므로 LSP를 위반합니다.

**See also.** [Module 02](../02_solid_principles/)

---

## O — OCP / Observer

### OCP (Open/Closed Principle)

**Definition.** 소프트웨어 엔티티가 확장에는 열려 있고 수정에는 닫혀 있어야 한다는 SOLID 원칙.

**Source.** `oop_spec.md` §5.2 (SOLID — OCP); §7 (UVM factory = OCP).

**Related.** SOLID, Factory Method, Polymorphism.

**Example.** 새 프로토콜은 기존 코드 수정 없이 `my_new_driver extends uvm_driver`를 추가하거나 factory override를 등록해 확장합니다.

**See also.** [Module 02](../02_solid_principles/)

### Observer (옵저버 패턴)

**Definition.** 일대다 의존 관계를 정의하여 한 객체의 상태 변화를 의존하는 여러 객체에 자동으로 방송하는 Behavioral 디자인 패턴.

**Source.** `design_pattern_onboarding.md` Behavioral; `oop_spec.md` §5.5 (TLM = DIP).

**Related.** Behavioral, Analysis Port, DIP.

**Example.** UVM의 `uvm_analysis_port`가 한 트랜잭션을 scoreboard·coverage 등 여러 구독자에 1:N broadcast하는 것이 Observer 패턴입니다.

**See also.** [Module 03](../03_gof_design_patterns/) · [Module 04](../04_sv_uvm_mapping/)

---

## P — Polymorphism

### Polymorphism (다형성)

**Definition.** 같은 인터페이스 호출이 객체의 실제 타입에 따라 런타임에 다른 동작을 수행하는 객체지향 기법.

**Source.** `oop_spec.md` §3.4 (The Four Pillars — Polymorphism).

**Related.** Inheritance, virtual function, parametric polymorphism.

**Example.** `virtual function void run_phase(uvm_phase phase)`는 subtype 다형성, `uvm_driver#(REQ, RSP)`는 parametric 다형성입니다.

**See also.** [Module 01](../01_oop_pillars_relationships/) · [Module 04](../04_sv_uvm_mapping/)

---

## S — SOLID / SRP / Singleton

### SOLID

**Definition.** 클래스와 그 관계를 확장·유지보수·테스트하기 쉽게 설계하기 위한 다섯 가지 원칙(SRP·OCP·LSP·ISP·DIP)의 집합.

**Source.** `oop_spec.md` §5 (SOLID Design Principles).

**Related.** SRP, OCP, LSP, ISP, DIP, OOP 4기둥.

**Example.** 4기둥이 "도구"라면 SOLID는 "그 도구를 쓰는 법"에 해당합니다.

**See also.** [Module 02](../02_solid_principles/)

### SRP (Single Responsibility Principle)

**Definition.** 클래스가 변경되어야 할 이유를 단 하나만 가져야 한다는 SOLID 원칙.

**Source.** `oop_spec.md` §5.1 (SOLID — SRP).

**Related.** SOLID, Cohesion, Composition.

**Example.** scoreboard는 기능 정확성 검사만 담당해야 하며 coverage 수집·로깅·레지스터 접근을 끌어들이면 SRP를 위반합니다.

**See also.** [Module 02](../02_solid_principles/)

### Singleton (싱글톤 패턴)

**Definition.** 클래스가 정확히 한 번만 인스턴스화되도록 보장하면서 전역 접근을 허용하는 Creational 디자인 패턴.

**Source.** `design_pattern_onboarding.md` Creational.

**Related.** Creational, Global Access.

**Example.** UVM의 `uvm_factory`·`uvm_root`는 전역에서 유일한 인스턴스로 동작합니다(추론 — 전형적 UVM 구조).

**See also.** [Module 03](../03_gof_design_patterns/)

---

## 추가 약어 / 원칙

| 약어 | 풀네임 | 한 줄 의미 |
|------|--------|-----------|
| **KISS** | Keep It Simple, Stupid | 동작하는 가장 단순한 해법을 택하라 (`oop_spec.md` §2.1) |
| **DRY** | Don't Repeat Yourself | 모든 지식은 단 하나의 권위 있는 표현만 가진다 (`oop_spec.md` §2.2) |
| **YAGNI** | You Ain't Gonna Need It | 실제로 필요해지기 전엔 기능을 추가하지 않는다 (`oop_spec.md` §2.3) |
| **OOAD** | OO Analysis and Design | 요구→클래스 도출 과정 (명사→클래스, 동사→메서드) (`oop_spec.md` §6) |
| **Aggregation** | — | 소유자가 소유물 없이도 존재 가능한 HAS-A (`oop_spec.md` §4.2) |
| **Association** | — | 두 객체가 서로 독립적으로 존재하는 HAS-A (`oop_spec.md` §4.2) |
| **Strategy** | — | 알고리즘을 캡슐화해 런타임 교체 (Behavioral) (`design_pattern_onboarding.md`) |
| **Adapter** | — | 호환 안 되는 인터페이스를 감싸 연결 (Structural) (`design_pattern_onboarding.md`) |
