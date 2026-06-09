---
title: "Module 01 — OOP 4기둥 & 객체 관계"
---

:::tip[학습 목표]
이 모듈을 마치면:

- **Explain** 객체지향이 절차적 코드의 어떤 문제를 풀려고 등장했는지와 "Flexible / Reusable / Maintainable" 세 목표를 설명할 수 있다.
- **Differentiate** 캡슐화(Encapsulation)와 추상화(Abstraction)가 각각 무엇을 숨기는지 구분할 수 있다.
- **Differentiate** IS-A / HAS-A / CAN-DO 관계와 association·aggregation·composition의 수명주기 차이를 구분할 수 있다.
- **Apply** 상속이 적절한 경우와 합성(composition)이 더 나은 경우를 IS-A 관계의 참/거짓으로 판단할 수 있다.
- **Trace** UVM 클래스 한 줄(`my_driver extends uvm_driver`)이 어떤 기둥·관계의 표현인지 추적할 수 있다.
:::
:::note[사전 지식]
- 함수·변수·자료구조를 다뤄 본 일반 프로그래밍 경험 (언어 무관)
- SystemVerilog `class` / `extends` 문법을 본 적 있으면 도움 (필수 아님)
:::
---

## 1. Why care? — 절차적 코드가 커지면 무너지는 이유

### 1.1 시나리오 — "이 데이터를 건드리는 함수가 어디 있더라?"

절차적 프로그래밍에서 프로그램은 데이터를 조작하는 명령의 나열입니다. 처음엔 깔끔하지만, 프로그램이 커지면 데이터와 그 데이터를 다루는 함수가 코드베이스 곳곳에 흩어집니다. 그래서 새 기능을 추가하려면 "이 데이터를 건드리는 함수가 전부 어디 있지?"를 추적해 한 곳씩 조심스럽게 패치해야 하고, 한 곳을 빠뜨리면 버그가 됩니다. 변경할 때마다 이 위험이 복리로 불어납니다 (`oop_spec.md` §1.1).

객체지향은 이 문제를 **데이터와 그 데이터를 다루는 연산을 하나의 단위(객체)로 묶어서** 해결합니다. 질문이 "어떤 함수가 이 데이터를 건드리지?"에서 "이 객체는 무엇을 *할 수 있지*?"로 바뀝니다. 이 관점의 전환이 대규모 코드베이스를 다룰 수 있게 만드는 핵심입니다 (`oop_spec.md` §1.1).

### 1.2 검증 환경에서 왜 중요한가

UVM(Universal Verification Methodology — SystemVerilog 클래스로 검증 환경을 짓는 산업 표준 라이브러리)은 처음부터 끝까지 객체지향으로 지어진 프레임워크입니다. driver(DUT에 입력 자극을 실제로 인가하는 컴포넌트)/monitor(DUT의 신호를 관찰해 트랜잭션으로 변환하는 컴포넌트)/scoreboard(기대값과 실제값을 비교해 정오답을 판정하는 컴포넌트)가 각각 자기 데이터와 동작을 캡슐화한 객체이고, 이들이 상속 계층과 합성 관계로 엮여 하나의 검증 환경을 이룹니다. 이 모듈의 4기둥과 관계를 모르고 UVM을 외우면, 코드는 따라 칠 수 있어도 "왜 이렇게 설계했는가"가 보이지 않습니다. 반대로 토대를 잡으면 UVM의 거의 모든 구조가 네 기둥과 세 관계의 조합으로 환원됩니다.

좋은 OO 설계의 시금석은 세 가지 목표입니다 — **Flexible**(한 부분을 바꿔도 다른 부분이 안 깨짐), **Reusable**(한 번 쓰고 여러 곳에 재사용), **Maintainable**(6개월 뒤에 봐도 구조만으로 의도가 드러남). 모든 설계 결정은 "이 변경이 코드를 더 유연·재사용·유지보수 가능하게 하는가?"로 검증됩니다 (`oop_spec.md` §1.2).

---

## 2. Intuition — 네 기둥이 떠받치는 한 채의 집

:::tip[💡 한 줄 비유]
**객체지향** ≈ **부품으로 조립한 기계**.<br>
각 부품(객체)은 내부를 감춘 채 정해진 손잡이(인터페이스)만 노출하고(캡슐화), 손잡이만 보고 쓸 수 있으며(추상화), 기존 부품을 본떠 특화 부품을 만들고(상속), 같은 손잡이를 당겨도 부품마다 다르게 동작합니다(다형성).
:::
### 한 장 그림 — 4기둥과 세 관계

```d2
direction: down

OOP: "객체지향 (OOP)" {
  P1: "캡슐화\nEncapsulation\n내부 상태를 숨김"
  P2: "추상화\nAbstraction\n본질만 노출"
  P3: "상속\nInheritance\nIS-A 재사용/특화"
  P4: "다형성\nPolymorphism\n같은 호출 → 다른 동작"
}

REL: "객체 관계" {
  R1: "IS-A\n(상속/일반화)"
  R2: "HAS-A\n(합성/집약/연관)"
  R3: "CAN-DO\n(인터페이스/역할)"
}

GOALS: "세 목표" {
  G1: "Flexible"
  G2: "Reusable"
  G3: "Maintainable"
}

OOP -> GOALS: "달성 수단"
REL -> GOALS: "달성 수단"
```

### 왜 이 네 가지인가 — Design rationale

네 기둥은 따로 노는 개념이 아니라 하나의 목표를 향한 분업입니다. 캡슐화는 *내부 구현*을 숨겨 외부 의존을 끊고, 추상화는 *어떤 구체 타입*인지를 숨겨 호출 측이 본질만 보게 합니다. 상속은 공통을 한 곳에 모아 재사용·특화의 축을 만들고, 다형성은 그 축 위에서 호출 측이 구체 타입을 모른 채 동작을 갈아끼우게 합니다. 이 넷이 맞물려야 비로소 "한 곳을 바꿔도 다른 곳이 안 깨지는" 유연함이 생깁니다.

---

## 3. 작은 예 — Shape 하나로 네 기둥 전부 보기

가장 단순한 예. `Shape`라는 추상 개념과 그 구체 타입들(Circle, Rectangle)로 네 기둥을 한꺼번에 관찰합니다.

### 단계별 다이어그램

```d2
direction: down

ABS: "abstract Shape\narea() / perimeter()\n(추상화: '무엇'만, '어떻게'는 미정)"
C: "Circle extends Shape\n(상속: Circle IS-A Shape)\noverride area()"
R: "Rectangle extends Shape\n(상속)\noverride area()"
CALLER: "caller\nfor (Shape s : shapes)\n  s.area()\n(다형성: 런타임에 올바른 구현 dispatch)"

ABS -> C: "특화"
ABS -> R: "특화"
C -> CALLER: "Shape 핸들로 담김"
R -> CALLER
```

### 단계별 의미

| 기둥 | 코드에서 어디 | 무엇을 숨기거나 가능하게 하는가 |
|---|---|---|
| 캡슐화 | `Circle` 내부의 반지름 필드를 `private`로 | 내부 상태 — caller는 `area()`만 호출, 저장 방식 모름 |
| 추상화 | `abstract Shape { area(); }` | 구체 타입 — caller는 "넓이를 구할 수 있는 무언가"로만 다룸 |
| 상속 | `Circle extends Shape` | 공통 인터페이스 재사용 + 타입별 특화 |
| 다형성 | `s.area()`가 런타임에 Circle/Rectangle 구현으로 dispatch | 같은 호출이 타입에 따라 다른 동작 |

### 실제 코드 (네 기둥 한꺼번에)

```cpp
// 추상화 — '무엇'만 정의, '어떻게'는 미정
abstract class Shape {
    abstract double area();         // what, not how
    abstract double perimeter();
}

// 캡슐화 — 내부 상태(radius)를 숨기고 메서드만 노출
class Circle extends Shape {
    private double radius;          // 외부가 직접 못 건드림
    Circle(double r) { radius = r; }
    @Override double area()      { return 3.14159 * radius * radius; }
    @Override double perimeter() { return 2 * 3.14159 * radius; }
}

class Rectangle extends Shape {     // 상속 — Rectangle IS-A Shape
    private double w, h;
    Rectangle(double w, double h) { this.w = w; this.h = h; }
    @Override double area()      { return w * h; }
    @Override double perimeter() { return 2 * (w + h); }
}

// 다형성 — caller는 구체 타입을 모른 채 area() 호출
Shape[] shapes = { new Circle(5), new Rectangle(3, 4) };
for (Shape s : shapes)
    print(s.area());                // 런타임에 올바른 구현으로 dispatch
```

:::note[여기서 잡아야 할 두 가지]
**(1) 캡슐화와 추상화는 다른 것을 숨긴다.** 캡슐화는 *내부 상태가 어떻게 저장·관리되는지*를 숨기고, 추상화는 *지금 다루는 게 어떤 구체 타입인지*를 숨깁니다 (`oop_spec.md` §3.2).<br>
**(2) 다형성은 상속 위에서 산다.** `Shape` 핸들 하나로 Circle·Rectangle을 담을 수 있는 것은 둘이 모두 Shape를 상속(IS-A)했기 때문입니다. 상속이 없으면 다형성도 없습니다.
:::
---

## 4. 일반화 — 네 기둥과 세 관계의 전체 그림

### 4.1 네 기둥 요약

| 기둥 | 정의 | 무엇을 숨기는가 / 가능하게 하는가 | UVM 표현 |
|---|---|---|---|
| Encapsulation | 데이터+메서드를 한 단위로 묶고 내부 상태를 숨김 | 내부 구현 | `uvm_component`가 phase 머신을 숨김 (`oop_spec.md` §3.1) |
| Abstraction | 본질만 노출, 구현은 감춤 | 구체 타입 | `uvm_sequence_item`이 "트랜잭션"을 추상화 (`oop_spec.md` §3.2) |
| Inheritance | 부모의 필드·메서드를 자식이 획득(IS-A) | (재사용 축 제공) | `my_driver → uvm_driver` IS-A 체인 (`oop_spec.md` §3.3) |
| Polymorphism | 같은 인터페이스가 타입에 따라 다른 동작 | (동작 교체 가능) | `virtual run_phase()` dispatch (`oop_spec.md` §3.4) |

다형성에는 두 갈래가 있습니다. 런타임에 vtable로 dispatch되는 **subtype polymorphism**(대부분의 엔지니어가 "다형성"이라 부르는 것)과, 타입 파라미터로 임의 타입 T에 동작하는 **parametric polymorphism**(generics/template)입니다. UVM의 `uvm_driver#(REQ, RSP)`는 parametric, `run_phase()` 오버라이드는 subtype 다형성입니다 (`oop_spec.md` §3.4).

여기서 "런타임 dispatch"가 실제로 어떻게 일어나는지가 핵심입니다. `virtual`로 선언된 메서드는 컴파일 시점에 호출 대상이 고정되지 않습니다. 대신 각 객체는 자신의 실제 타입에 해당하는 **가상 함수 테이블(vtable)** — 메서드 이름 → 실제 구현 주소의 표 — 을 가리키고, `s.area()` 호출은 "*핸들*의 선언 타입"이 아니라 "*객체*의 실제 타입"의 vtable을 조회해 구현을 고릅니다. 그래서 `Shape` 핸들에 `Circle` 객체가 담겨 있으면 `Circle::area()`가 불립니다 — 호출 측이 구체 타입을 몰라도 됩니다. 반대로 `virtual`이 빠지면 dispatch가 *핸들의 선언 타입*에 따라 컴파일 시점에 고정되어, `Shape` 핸들로는 항상 `Shape::area()`만 불립니다. 이것이 Module 04에서 `virtual` 누락 시 다형성이 조용히 깨지는 메커니즘의 근본입니다.

추상화의 SV 표현인 `virtual class`도 같은 맥락에서 이해됩니다. `virtual class`는 "추상 타입" — 완성되지 않은(혹은 직접 인스턴스화를 금지한) 클래스라서 `new`로 직접 객체를 만들 수 없고, *상속한 구체 자식*만 인스턴스화할 수 있습니다. §3의 `abstract Shape`가 Java 풍이라면, SV에서는 `virtual class uvm_object`가 같은 역할을 합니다 — "넓이를 구할 수 있는 무언가"라는 추상만 정의하고 구현은 자식에게 위임하는 것입니다 (Module 04와 일관).

### 4.2 세 가지 객체 관계

객체끼리 엮이는 방식은 세 갈래입니다 (`oop_spec.md` §4).

```d2
direction: right

ISA: "IS-A (상속)" {
  A: "uvm_component"
  B: "uvm_driver"
  C: "my_axi_driver"
  C -> B: "IS-A"
  B -> A: "IS-A"
}
HASA: "HAS-A (합성)" {
  E: "uvm_agent"
  D: "driver"
  M: "monitor"
  E -> D: "HAS-A"
  E -> M: "HAS-A"
}
CANDO: "CAN-DO (인터페이스/역할)" {
  T: "Transaction"
  S: "Serializable\n(do_pack)"
  L: "Comparable\n(do_compare)"
  T -> S: "implements"
  T -> L: "implements"
}
```

:::tip[기둥의 토대 — SV class 변수는 객체가 아니라 핸들(참조)이다]
네 기둥을 SystemVerilog로 옮기기 전에, 모든 것의 바닥에 깔린 한 가지 사실을 먼저 못박아야 합니다 — **SV에서 class 타입 변수는 객체 *자체*가 아니라 객체를 가리키는 핸들(handle, 곧 참조/포인터)입니다.** `my_item a = new();` 는 객체 하나를 힙에 만들고 그 위치를 `a`에 담습니다. 이어서 `my_item b = a;` 를 하면 *객체가 복사되지 않고 핸들만 복사*되어, `a`와 `b`는 **같은 하나의 객체**를 가리킵니다. 그래서 `b.addr = 99;` 는 `a.addr`도 99로 바꿉니다 — 둘이 같은 객체이기 때문입니다. (대조적으로 `int`/`bit` 같은 값 타입은 대입 시 값이 복제됩니다.)

이 reference semantics가 곧 **얕은 복사(shallow copy)와 깊은 복사(deep copy)** 의 구분을 낳습니다.

- **단순 대입(`b = a`)**: 핸들만 복사 — 객체는 하나, 완전히 공유됨.
- **얕은 복사(shallow copy)**: 객체를 새로 하나 만들고 *필드 값을 그대로* 복사. 그런데 필드가 또 다른 객체의 핸들이면, 그 *내부 핸들이 가리키는 객체는 여전히 공유*됩니다 — 껍데기만 새것이고 속은 공유.
- **깊은 복사(deep copy)**: 객체를 새로 만들고, 핸들 필드가 가리키는 객체들까지 *재귀적으로* 새로 복제. 원본과 사본이 어떤 객체도 공유하지 않음.

UVM의 `clone()` / `do_copy()` 가 정확히 이 deep copy를 보장하기 위해 존재합니다. 트랜잭션을 monitor가 scoreboard·coverage(어떤 시나리오·값 조합이 실제로 검증됐는지 누적 측정하는 컴포넌트) 등 여러 구독자에게 1:N으로 **broadcast**(한 데이터를 여러 수신자에게 동시에 뿌리는 것)할 때, 단순히 같은 핸들을 넘기면 모든 구독자가 *같은 객체*를 받습니다. 한 구독자가 그 객체를 수정하면 다른 구독자가 보는 값까지 바뀌는 오염이 생깁니다. 그래서 "broadcast된 트랜잭션을 mutate하지 말라", 그리고 보관·재전송 시 `clone()`으로 사본을 떠서 쓰라는 규칙이 나옵니다. 이 메커니즘은 UVM 코스의 [Sequence & Item](../../uvm/03_sequence_and_item/)과 [TLM/Scoreboard](../../uvm/05_tlm_scoreboard_coverage/)에서 `do_copy`/`clone` 구현으로 다시 등장합니다.
:::

**IS-A**는 자식이 부모 자리에 *대체 가능*해야 성립합니다(Liskov 치환 — 서브타입을 부모 타입 자리에 끼워 넣어도 프로그램이 여전히 옳게 동작해야 한다는 규칙. Module 02 §LSP). 설계 수명 내내 진짜로 참일 때만 모델링해야 합니다.

**HAS-A**는 한 객체가 다른 객체의 참조를 *보유*하는 관계이며, 수명주기에 따라 세 가지로 나뉩니다 (`oop_spec.md` §4.2):

| 종류 | 수명주기 | 예시 |
|---|---|---|
| Association | 둘이 서로 독립 — 어느 쪽이 없어도 존재 | `Driver`가 `Sequencer`를 사용 |
| Aggregation | 소유자가 소유물 없이도 존재 가능 | `uvm_env`가 agent들을 집약 |
| Composition | 소유자가 소유물을 생성·파괴 | `uvm_agent`가 driver+monitor를 합성 — agent 파괴 시 함께 파괴 |

(여기서 `Sequencer`는 자극 시나리오(sequence)를 만들어 driver에 흘려보내는 컴포넌트, `uvm_agent`는 한 인터페이스를 담당하는 driver·monitor·sequencer를 한 묶음으로 보유하는 컨테이너 컴포넌트, `uvm_env`는 여러 agent와 scoreboard를 합쳐 전체 검증 환경을 이루는 최상위 컨테이너입니다.)

**CAN-DO**는 *역할/능력*을 선언하는 관계입니다. 상속 계층 어디에 있든, 어떤 클래스가 특정 역할을 수행할 *수 있으면* 그 인터페이스를 구현합니다. SystemVerilog에서는 `uvm_object`의 콜백(`do_copy`/`do_compare`/`do_print`/`do_pack`)이 이 패턴 — 특별한 클래스를 상속하지 않고도 deep-copy·compare·pack을 *할 수 있게* 됩니다 (`oop_spec.md` §4.3).

### 4.3 상속 vs 합성 — IS-A가 참인가로 결정

상속을 단지 코드 재사용 목적으로 오용해 IS-A 관계가 거짓인데도 `extends`를 쓰면, 부모 변경이 모든 자식을 깨뜨리는 깨지기 쉬운 계층이 됩니다. IS-A가 불분명하면 합성을 택하는 것이 원칙입니다. `Car HAS-A Engine`은 `Car extends Engine`보다 합성으로 모델링하는 것이 옳습니다 (`oop_spec.md` §3.3).

---

## 5. 디테일 — 코딩 원칙(KISS/DRY/YAGNI)과 요구→클래스 도출

### 5.1 일상 코딩을 지배하는 세 원칙

설계 이전에, 매일의 코딩 결정을 지배하는 세 원칙이 있습니다 (`oop_spec.md` §2).

- **KISS (Keep It Simple, Stupid)** — 동작하는 가장 단순한 해법을 택합니다. 복잡한 코드는 읽기·테스트·수정이 모두 어렵습니다. 단순한 설계가 요구를 만족하면 영리한 설계보다 단순한 쪽을 고릅니다.
- **DRY (Don't Repeat Yourself)** — 모든 지식은 코드베이스에 *단 하나의 권위 있는 표현*만 가져야 합니다. 중복은 수정할 곳이 둘, 버그가 생길 곳도 둘이 됩니다. 반복 로직은 함수·메서드·기반 클래스로 추출합니다.
- **YAGNI (You Ain't Gonna Need It)** — 실제로 필요해지기 전엔 기능을 추가하지 않습니다. 쓰이지 않을 "예상 기능"은 복잡도만 늘리고 개발을 느리게 하며, 정작 필요한 설계를 막기도 합니다.

### 5.2 요구사항에서 클래스를 도출하는 휴리스틱

OOAD는 요구에서 설계로 가는 가벼운 과정을 제시합니다. 핵심 휴리스틱은 명사와 동사를 읽는 것입니다 (`oop_spec.md` §6.1).

```d2
direction: down
REQ: "요구사항 (자연어)"
N: "명사 → 후보 클래스 / 속성"
V: "동사 → 후보 메서드 / 책임"
CHK: "검사: 동사가 너무 많은 클래스?\n→ SRP 위반 → 분리"
REQ -> N
REQ -> V
N -> CHK
V -> CHK
```

설계의 중심 질문은 *"무엇이 가장 자주 바뀌는가?"*입니다. 자주 바뀌는 부분(volatile concretion — 프로토콜별 subclass)을 안정된 부분(stable abstraction — 기반 클래스/인터페이스)에서 격리합니다. 검증 환경에서 `uvm_env` 토폴로지는 안정적이고 DUT별 sequence 라이브러리는 휘발성이므로, 둘을 별도 패키지로 분리하면 env를 DUT 개정판마다 재사용할 수 있습니다 (`oop_spec.md` §6.2).

### 5.3 UVM으로 본 IS-A / HAS-A 체인

```systemverilog
// IS-A 체인 (상속): 깊은 계층
//   my_driver IS-A uvm_driver IS-A uvm_component IS-A uvm_object
class my_axi_driver extends uvm_driver #(axi_item);
  `uvm_component_utils(my_axi_driver)
  // ...
endclass

// HAS-A (합성): agent가 하위 컴포넌트를 보유
class my_agent extends uvm_agent;
  `uvm_component_utils(my_agent)
  my_axi_driver drv;     // HAS-A driver (composition)
  my_monitor    mon;     // HAS-A monitor
  uvm_sequencer #(axi_item) sqr; // HAS-A sequencer

  function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    mon = my_monitor::type_id::create("mon", this);
    if (get_is_active() == UVM_ACTIVE) begin
      drv = my_axi_driver::type_id::create("drv", this);
      sqr = uvm_sequencer#(axi_item)::type_id::create("sqr", this);
    end
  endfunction
endclass
```

`uvm_agent HAS-A uvm_driver, uvm_monitor, uvm_sequencer`이고, 동시에 `my_axi_driver IS-A uvm_driver IS-A uvm_component`입니다. 한 클래스가 IS-A(부모로부터 상속)와 HAS-A(자식을 보유)를 동시에 갖는 것이 정상입니다 (`oop_spec.md` §7).

---

## 6. 흔한 오해 와 디버그 체크리스트

### 흔한 오해

:::danger[❓ 오해 1 — '상속은 코드 재사용 도구다']
**실제**: 상속의 본질은 *IS-A 관계 모델링*이지 재사용이 아닙니다. IS-A가 거짓인데 재사용만을 위해 `extends`를 쓰면 부모 변경이 모든 자식을 깨뜨립니다. 재사용이 목적이라면 합성(HAS-A)을 택하세요 (`oop_spec.md` §3.3).<br>
**왜 헷갈리는가**: 상속이 부모 코드를 "공짜로" 가져다 주는 것처럼 보여서.
:::
:::danger[❓ 오해 2 — '캡슐화와 추상화는 같은 말이다']
**실제**: 둘 다 "숨긴다"지만 *무엇을* 숨기는지가 다릅니다. 캡슐화는 내부 상태가 *어떻게* 관리되는지를, 추상화는 *어떤 구체 타입*을 다루는지를 숨깁니다 (`oop_spec.md` §3.2).<br>
**왜 헷갈리는가**: 둘 다 `private`/`abstract` 같은 키워드로 표현되어 표면이 비슷해 보여서.
:::
:::danger[❓ 오해 3 — 'aggregation과 composition은 둘 다 HAS-A니까 똑같다']
**실제**: 수명주기가 다릅니다. Composition은 소유자가 소유물을 *생성·파괴*하므로 함께 죽고, aggregation은 소유자가 없어도 소유물이 독립적으로 존재할 수 있습니다 (`oop_spec.md` §4.2).<br>
**왜 헷갈리는가**: UML 표기로는 둘 다 "선으로 연결"처럼 보여서.
:::

### DV 디버그 체크리스트 (이 모듈 내용으로 마주칠 첫 함정들)

| 증상 | 1차 의심 | 어디 보나 |
|---|---|---|
| 부모 클래스 한 줄 수정에 여러 자식이 깨짐 | IS-A가 거짓인데 재사용 목적으로 상속함 | `extends` 관계가 진짜 "is a"인지 점검 → 합성으로 |
| 내부 필드를 외부에서 직접 바꿔 버그 | 캡슐화 위반 (`local`/`protected` 미사용) | 필드 가시성 한정자 확인 |
| 한 클래스가 너무 많은 일을 함 | 동사가 과다 → SRP 위반 신호 | 요구의 동사 수 세기 → 분리 (Module 02) |
| 같은 로직이 여러 곳에 복붙됨 | DRY 위반 | 공통을 기반 클래스/함수로 추출 |
| 쓰지도 않는 설정·기능이 복잡도만 늘림 | YAGNI 위반 | 실제 요구에 매핑 안 되는 코드 제거 |

---

## 7. 핵심 정리 (Key Takeaways)

- **객체지향의 출발점**은 데이터와 연산을 객체로 묶어, "어떤 함수가 이 데이터를 건드리나"를 "이 객체는 무엇을 할 수 있나"로 바꾸는 것입니다.
- **네 기둥**: 캡슐화(내부 상태 은닉) · 추상화(구체 타입 은닉) · 상속(IS-A 재사용/특화) · 다형성(같은 호출, 다른 동작).
- **세 관계**: IS-A(상속, 대체 가능해야), HAS-A(합성/집약/연관 — 수명주기로 구분), CAN-DO(역할/능력 선언).
- **상속 vs 합성**: IS-A가 진짜 참일 때만 상속, 불분명하면 합성. "재사용 목적 상속"은 안티패턴.
- **코딩 원칙 KISS/DRY/YAGNI**가 설계 이전의 일상 결정을 지배합니다.
- **설계의 중심 질문**: "무엇이 가장 자주 바뀌는가" — 안정된 추상화에서 휘발성 구현을 격리.

:::caution[실무 주의점]
- 상속을 쓰기 전 "이 자식은 부모 자리에 *대체 가능*한가?"를 먼저 물으세요 (LSP — Module 02).
- 필드는 기본적으로 `local`/`protected`로 닫고, 필요한 인터페이스만 여세요(캡슐화).
- "나중에 필요할 것 같아서" 추가하는 코드는 YAGNI 위반일 가능성이 높습니다.
:::
### 7.1 자가 점검

:::tip[🤔 Q1 — 캡슐화 vs 추상화 (Bloom: Analyze)]
`uvm_sequence_item`을 driver가 다룰 때 작동하는 것은 캡슐화인가 추상화인가?
<details>
<summary>정답</summary>

주로 **추상화**입니다. driver는 그 item이 AXI burst인지 PCIe TLP인지 *구체 타입*을 모른 채 `uvm_sequence_item`이라는 추상으로만 다룹니다 — 추상화는 "어떤 구체 타입인지"를 숨깁니다 (`oop_spec.md` §3.2).
- 동시에 item 내부 필드가 `local`/`protected`로 닫혀 있다면 그 부분은 캡슐화입니다.
- 둘은 배타적이지 않고 한 객체에서 함께 작동합니다.

</details>
:::
:::tip[🤔 Q2 — 상속 vs 합성 (Bloom: Evaluate)]
"passive monitor가 코드 재사용을 위해 active driver를 `extends`한다"는 설계는 옳은가?
<details>
<summary>정답</summary>

**옳지 않습니다.** monitor는 driver의 *대체물이 아니므로* IS-A 관계가 거짓입니다. 재사용 목적의 상속은 부모(driver) 변경이 monitor를 깨뜨리는 취약한 계층을 만듭니다.
- 공통 로직을 공유하고 싶다면 별도 헬퍼 클래스를 두고 합성(HAS-A)하거나, 진짜 공통 부모(`uvm_component`)를 각자 상속하세요.
- 이는 다음 모듈의 LSP(Liskov 치환)와 직접 연결됩니다.

</details>
:::
### 7.2 출처

**External**
- McLaughlin, Pollice, West. *Head First Object-Oriented Analysis and Design*. O'Reilly, 2006.
- IEEE 1800 (SystemVerilog) — class-based OO

---

## 다음 모듈

→ [Module 02 — SOLID 설계 원칙](../02_solid_principles/): 네 기둥과 관계를 *어떻게 잘 쓰는가*. 클래스와 그 관계를 설계하는 다섯 원칙(SRP/OCP/LSP/ISP/DIP).

[퀴즈 풀어보기 →](../quiz/01_oop_pillars_relationships_quiz/)
