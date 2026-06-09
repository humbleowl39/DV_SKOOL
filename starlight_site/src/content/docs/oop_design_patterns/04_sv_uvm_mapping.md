---
title: "Module 04 — OOP → SystemVerilog / UVM 매핑"
---

:::tip[학습 목표]
이 모듈을 마치면:

- **Implement** 4기둥 각각을 SystemVerilog 문법(`local`/`protected`, `virtual class`, `extends`, `virtual function`)으로 구현할 수 있다.
- **Trace** UVM 코드 한 줄이 어떤 OOP 개념·패턴의 표현인지 추적할 수 있다.
- **Apply** factory(`type_id::create`)와 config_db(`set`/`get`)를 OCP·의존성 주입 관점에서 적용할 수 있다.
- **Differentiate** subtype 다형성(`virtual function`)과 parametric 다형성(`#(REQ, RSP)`)을 UVM 코드에서 구분할 수 있다.
- **Evaluate** 주어진 UVM 컴포넌트가 어떤 SOLID 원칙/GoF 패턴을 구현하는지 평가할 수 있다.
:::
:::note[사전 지식]
- [Module 01](../01_oop_pillars_relationships/) · [Module 02](../02_solid_principles/) · [Module 03](../03_gof_design_patterns/)
- SystemVerilog `class`/`extends`/`virtual` 문법, UVM 기초([UVM 코스](../../uvm/) 권장)
:::
---

## 1. Why care? — UVM은 OOP가 옷을 갈아입은 것

### 1.1 시나리오 — "왜 driver는 uvm_driver를 상속하지?"

UVM 코드를 처음 보면 `class my_driver extends uvm_driver#(my_item)` 한 줄에도 질문이 쏟아집니다 — 왜 상속하나, `#(my_item)`은 뭔가, 왜 `run_phase`는 `virtual`인가, `type_id::create`는 왜 `new` 대신 쓰나. 이 질문들의 답은 모두 앞 세 모듈에 있습니다. UVM은 새로운 마법이 아니라, 4기둥·SOLID·GoF 패턴이 SystemVerilog 문법으로 구체화된 것입니다 (`oop_spec.md` §7).

### 1.2 매핑을 잡으면 얻는 것

OOP 원래는 소프트웨어 개념이었지만, SystemVerilog(IEEE 1800)가 class 기반 OO를 하드웨어 검증에 들여왔고 UVM이 그 대표적 산업 적용입니다 (`oop_spec.md` §7). 이 매핑을 손에 쥐면, UVM 코드를 읽을 때 "이 줄은 캡슐화, 저 줄은 다형성, factory는 OCP"라고 설계 의도를 즉시 해석할 수 있습니다. 외워서 쓰던 관용구가 *왜 그렇게 생겼는지* 보이기 시작합니다.

---

## 2. Intuition — 한 표로 보는 개념↔문법

:::tip[💡 한 줄 비유]
**UVM** ≈ **OOP 개념의 SystemVerilog 번역본**.<br>
영어 단어(개념)와 한국어 단어(SV 문법)가 일대일로 대응하는 사전처럼, OOP의 각 개념은 UVM에서 정해진 문법으로 번역됩니다.
:::
### 한 장 그림 — 개념에서 UVM 클래스 한 줄까지

```d2
direction: down

CONCEPT: "OOP 개념" {
  E: "캡슐화"
  AB: "추상화"
  IN: "상속 (IS-A)"
  PO: "다형성"
  HA: "합성 (HAS-A)"
}

SV: "SystemVerilog 문법" {
  L: "local / protected"
  VC: "virtual class"
  EX: "extends"
  VF: "virtual function/task"
  PA: "#(REQ, RSP)"
}

UVM: "UVM 한 줄" {
  C: "class my_driver\n  extends uvm_driver#(my_item)\n  virtual function run_phase(...)"
}

CONCEPT -> SV: "번역"
SV -> UVM: "조합"
```

### 왜 이렇게 대응하는가 — Design rationale

SystemVerilog는 캡슐화를 위한 가시성 한정자(`local`/`protected`), 추상화를 위한 `virtual class`(직접 인스턴스화 불가), 상속을 위한 `extends`, subtype 다형성을 위한 `virtual` 메서드, parametric 다형성을 위한 파라미터화 클래스(`#(...)`)를 모두 갖췄습니다 (`oop_spec.md` §7 표). UVM은 이 문법들을 조합해 검증에 필요한 구조(component·item·env)를 만들고, 그 위에 factory·config_db·TLM이라는 패턴 계층을 얹습니다.

---

## 3. 작은 예 — sequence_item 하나에 4기둥 전부

가장 작은 UVM 객체인 sequence item으로 네 기둥이 SV 문법으로 어떻게 나타나는지 봅니다.

### 단계별 다이어그램

```d2
direction: down

OBJ: "virtual class uvm_object\n(추상화: 직접 인스턴스화 불가)"
ITEM: "class my_item\n  extends uvm_sequence_item\n(상속: IS-A)"
FIELDS: "protected/local 필드\n(캡슐화)"
CB: "virtual do_copy/do_compare\n(다형성 + CAN-DO 콜백)"

OBJ -> ITEM: "extends 체인"
ITEM -> FIELDS: "내부 상태 은닉"
ITEM -> CB: "override로 동작 정의"
```

### 단계별 의미

| 기둥 | SV 문법 | 코드 위치 |
|---|---|---|
| 추상화 | `virtual class uvm_object` (인스턴스화 불가) | 부모 |
| 상속 (IS-A) | `extends uvm_sequence_item` | 선언 |
| 캡슐화 | `local`/`protected` 필드 가시성 | 필드 |
| 다형성 + CAN-DO | `virtual do_copy/do_compare/do_pack` override | 콜백 |

### 실제 코드

```systemverilog
// 추상화: uvm_object는 virtual class — 직접 new 불가, 상속해서 씀
class my_item extends uvm_sequence_item;   // 상속 (IS-A)
  `uvm_object_utils(my_item)

  rand bit [31:0] addr;
  rand bit [31:0] data;
  protected int   _tag;                    // 캡슐화: 외부 직접 접근 차단

  function new(string name = "my_item");
    super.new(name);
  endfunction

  // 다형성 + CAN-DO: 콜백을 override 하면 "비교/복사할 수 있는" 능력 획득
  function bit do_compare(uvm_object rhs, uvm_comparer comparer);
    my_item that;
    if (!$cast(that, rhs)) return 0;
    return (addr == that.addr) && (data == that.data);
  endfunction
endclass
```

:::note[여기서 잡아야 할 것]
`do_compare`/`do_copy`/`do_pack`는 Module 01의 **CAN-DO 관계**(인터페이스/역할)의 SV 표현입니다 — 특별한 클래스를 추가로 상속하지 않고 콜백을 구현하기만 하면 "비교/복사/팩할 수 있는" 능력을 갖습니다 (`oop_spec.md` §4.3).
:::
---

## 4. 일반화 — OOP 개념 ↔ SV/UVM 매핑 종합표

`oop_spec.md` §7의 매핑 표를 그대로 따릅니다.

| OOP 개념 | SystemVerilog / UVM 표현 | (근거) |
|---|---|---|
| Class / Object | `class my_txn extends uvm_sequence_item` | `oop_spec.md` §7 |
| Encapsulation | `local` / `protected` 필드 가시성 | `oop_spec.md` §7 |
| Inheritance | `extends uvm_driver#(REQ)` | `oop_spec.md` §7 |
| Polymorphism | `virtual function void run_phase(uvm_phase phase)` | `oop_spec.md` §7 |
| Abstract class | `virtual class uvm_object` (직접 인스턴스화 불가) | `oop_spec.md` §7 |
| Interface (CAN-DO) | `uvm_object` 콜백: `do_copy`/`do_compare`/`do_pack` | `oop_spec.md` §7 |
| Dependency Injection | `uvm_config_db#(T)::set/get` | `oop_spec.md` §7 |
| Factory pattern | `uvm_factory` — 테스트 코드 변경 없이 런타임 override | `oop_spec.md` §7 |
| IS-A | `my_driver IS-A uvm_driver IS-A uvm_component IS-A uvm_object` | `oop_spec.md` §7 |
| HAS-A | `uvm_agent HAS-A uvm_driver, uvm_monitor, uvm_sequencer` | `oop_spec.md` §7 |

### 4.1 두 종류의 다형성 구분

UVM 코드에서 다형성은 두 형태로 나타납니다 (`oop_spec.md` §3.4).

```systemverilog
// (1) Parametric polymorphism — 타입 파라미터로 임의 타입에 동작
class uvm_driver #(type REQ = uvm_sequence_item,
                   type RSP = REQ) extends uvm_component;
  // REQ가 무엇이든 동일 골격으로 동작
endclass

// (2) Subtype polymorphism — virtual 메서드의 런타임 dispatch
class my_driver extends uvm_driver #(my_item);
  virtual task run_phase(uvm_phase phase);   // 스케줄러가 구체 타입 모른 채 호출
    // ...
  endtask
endclass
```

`#(REQ, RSP)`가 parametric, `virtual run_phase`가 subtype 다형성입니다. 스케줄러는 모든 컴포넌트의 `run_phase`를 *구체 타입을 모른 채* 호출하는데, 이것이 subtype 다형성의 정의 그대로입니다 (`oop_spec.md` §3.4).

:::note[`virtual`의 static binding 함정 — 무엇이 dispatch를 결정하는가]
`virtual` 한 단어가 dispatch 규칙을 정반대로 바꿉니다. **non-virtual 메서드는 *핸들의 선언 타입*(static type)으로 dispatch가 컴파일 시점에 고정**됩니다 — `uvm_driver` 핸들에 `my_driver` 객체가 담겨 있어도, 메서드가 non-virtual이면 `uvm_driver`의 구현이 불립니다(static binding). 반대로 **virtual 메서드는 *객체의 실제 타입*(dynamic type)으로 런타임에 dispatch**됩니다(Module 01의 vtable). UVM 스케줄러는 모든 컴포넌트를 `uvm_component` 핸들로 들고 phase 메서드를 호출하므로, `run_phase`가 virtual이어야만 *자식*의 구현이 불립니다. virtual을 빠뜨리면 스케줄러가 `uvm_component`의 (비어 있는) `run_phase`만 부르고 자식 동작은 조용히 무시됩니다 — 이것이 아래 오해 2의 기계적 근거입니다.

**parametric class는 파라미터 조합마다 *별개 타입*을 만든다.** `uvm_driver#(axi_item)`과 `uvm_driver#(pcie_item)`은 같은 템플릿에서 나왔지만 컴파일 시점에 *서로 다른 독립 타입*으로 특수화(specialization)됩니다 — 한쪽 핸들에 다른 쪽 객체를 담을 수 없습니다. 이 사실이 factory override와 타입 호환에 제약을 만듭니다(파라미터가 다르면 override 대상도 별개 타입). 같은 이유가 config_db의 type-key 매칭에도 그대로 작동합니다 — UVM 코스 [config_db & Factory](../../uvm/04_config_db_factory/)에서 "왜 `#(my_cfg)` set을 `#(uvm_object)` get으로 못 읽나"의 근본이 바로 이 "파라미터가 다르면 다른 타입"입니다.

**SV class 멤버의 기본 가시성은 *public*이다.** Java/C++의 일부 습관과 달리, SystemVerilog class의 필드·메서드는 `local`/`protected`를 명시하지 않으면 *외부에서 자유롭게 접근 가능*합니다. 즉 캡슐화는 기본값이 아니라 *명시적으로 닫아야* 얻어집니다 — `local`(자기 클래스만)·`protected`(자기+자식만)를 붙이지 않으면 외부 코드가 내부 필드를 직접 바꿀 수 있고, 이것이 아래 디버그 체크리스트의 "외부에서 내부 필드를 바꿔 버그"의 근본입니다.
:::

---

## 5. 디테일 — factory·config_db·TLM이 구현하는 SOLID/패턴

### 5.1 Factory = OCP의 정석 (Factory Method / Abstract Factory)

`oop_spec.md` §7은 **UVM factory를 검증에서 가장 강력한 OOP 패턴**으로 명시합니다. factory는 테스트벤치 수준에서 OCP를 구현합니다 — base env를 편집하지 않고 override 등록만으로 동작을 확장합니다.

```systemverilog
// 생성을 factory에 위임 (Factory Method): new 대신 type_id::create
class my_agent extends uvm_agent;
  function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    drv = my_driver::type_id::create("drv", this);  // factory 경유
  endfunction
endclass

// OCP: base 코드를 안 고치고 override 등록만으로 동작 교체
class err_test extends base_test;
  function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    my_driver::type_id::set_type_override(err_driver::get_type());
  endfunction
endclass
```

`new` 대신 `type_id::create`를 쓰는 이유가 바로 이것입니다 — 생성을 factory에 위임해 두면, 나중에 override 한 줄로 그 타입을 바꿀 수 있습니다. 직접 `new`로 만든 객체는 override 대상이 되지 못합니다.

이 위임이 작동하려면 *등록*이 먼저 있어야 합니다. `` `uvm_component_utils(my_driver) `` / `` `uvm_object_utils(my_item) `` 매크로가 하는 일이 바로 그 등록입니다 — 매크로가 클래스마다 `type_id`라는 **proxy(대리 생성자) 타입**을 만들어 factory의 전역 테이블에 "이 type-name → 이 proxy" 로 등록합니다. 그래서 생성과 override가 2단계로 갈립니다 — **(1) 등록**: 매크로가 proxy를 factory에 올려두고, **(2) 조회·생성**: `type_id::create`가 호출 시점에 factory 테이블에서 해당 type-name에 *현재* 걸려 있는 proxy(override가 있으면 교체된 proxy)를 찾아 그 proxy의 `new`를 호출합니다. `new`를 직접 부르면 이 테이블을 거치지 않으니 override가 끼어들 자리가 없습니다. 매크로가 *필수*인 이유가 이것 — 매크로 없이는 proxy 등록이 없어 factory가 그 타입을 모릅니다. `type_id::create`가 factory를 거쳐 proxy를 조회·생성하는 *간접 생성*의 전체 메커니즘은 UVM 코스 [config_db & Factory](../../uvm/04_config_db_factory/)에서 redirect table 관점으로 더 깊게 다룹니다.

### 5.2 config_db = 의존성 주입 (Dependency Injection)

`oop_spec.md` §7은 `uvm_config_db#(T)::set/get`(설정 값을 계층 경로로 등록(set)하고 꺼내(get) 쓰는 UVM의 전역 설정 저장소)을 **Dependency Injection**으로 매핑합니다. 컴포넌트가 필요한 설정(virtual interface — 클래스 기반 TB가 RTL 신호 다발에 접근하기 위한 핸들·config 객체)을 *직접 생성하지 않고* 외부에서 주입받습니다 — 이는 DIP와 짝을 이룹니다.

```systemverilog
// 주입하는 쪽 (test): 의존성을 외부에서 넣어줌
uvm_config_db#(virtual my_if)::set(null, "uvm_test_top.env.agent.*", "vif", my_if);

// 주입받는 쪽 (driver): 직접 만들지 않고 받기만 함
function void build_phase(uvm_phase phase);
  if (!uvm_config_db#(virtual my_if)::get(this, "", "vif", vif))
    `uvm_fatal("NOVIF", "vif missing")
endfunction
```

driver는 어떤 인터페이스 인스턴스가 주입될지 모른 채 추상(`virtual my_if`)에만 의존합니다 — 고수준이 저수준 구체에 묶이지 않는 DIP의 모습입니다.

### 5.3 TLM analysis port = DIP + Observer

`oop_spec.md` §5.5는 TLM 포트(`uvm_analysis_port` 등)를 **DIP의 정석 표현**으로 명시합니다. producer와 consumer가 추상 포트로 분리되어 서로의 구체 타입을 모릅니다. 동시에 이 1:N broadcast 구조는 GoF의 **Observer 패턴**(Module 03 §4.3)이기도 합니다.

```systemverilog
// monitor(producer)는 누가 듣는지 모른 채 broadcast — Observer + DIP
class my_monitor extends uvm_monitor;
  uvm_analysis_port #(my_item) ap;   // 추상 포트
  task run_phase(uvm_phase phase);
    forever begin
      // ... sample ...
      ap.write(item);                // 모든 구독자에게 일대다 방송
    end
  endtask
endclass
```

### 5.4 종합 — 한 env에 OOP 전부

| UVM 요소 | OOP/패턴 매핑 | 근거 |
|---|---|---|
| `extends uvm_component` | 상속 (IS-A) | `oop_spec.md` §7 |
| `local`/`protected` | 캡슐화 | `oop_spec.md` §7 |
| `virtual run_phase` | subtype 다형성 | `oop_spec.md` §7 |
| `#(REQ, RSP)` | parametric 다형성 | `oop_spec.md` §3.4 |
| agent가 drv/mon 보유 | 합성 (HAS-A) | `oop_spec.md` §7 |
| `do_compare`/`do_copy` | CAN-DO 인터페이스 | `oop_spec.md` §4.3, §7 |
| `type_id::create` + override | factory = OCP (Factory Method) | `oop_spec.md` §7 |
| `config_db::set/get` | 의존성 주입 (+DIP) | `oop_spec.md` §7, §5.5 |
| `analysis_port` | DIP + Observer | `oop_spec.md` §5.5 |

---

## 6. 흔한 오해 와 디버그 체크리스트

### 흔한 오해

:::danger[❓ 오해 1 — '`new`로 만들든 `type_id::create`로 만들든 결과는 같다']
**실제**: 결과 객체는 같아 보여도, `new`로 만든 객체는 **factory override 대상이 못 됩니다**. factory(OCP)의 이점을 쓰려면 반드시 `type_id::create`로 생성해야 합니다 (`oop_spec.md` §7).<br>
**왜 헷갈리는가**: 단일 테스트에서는 override를 안 써서 차이가 안 드러나서.
:::
:::danger[❓ 오해 2 — '`virtual` 키워드는 붙여도 그만 안 붙여도 그만이다']
**실제**: `virtual`이 없으면 subtype 다형성이 작동하지 않아, 부모 핸들로 호출 시 부모 메서드가 불립니다. 스케줄러가 자식의 `run_phase`를 호출하려면 `virtual`이 필수입니다 (`oop_spec.md` §3.4, §7).<br>
**왜 헷갈리는가**: 같은 클래스 핸들로 호출하면 `virtual` 유무와 무관하게 동작해서.
:::
:::danger[❓ 오해 3 — 'analysis port는 UVM 고유의 특수 기능이다']
**실제**: analysis port는 GoF **Observer 패턴 + DIP**의 SV 구현일 뿐입니다 — 1:N broadcast와 producer/consumer 분리라는 보편 개념의 구체화입니다 (`oop_spec.md` §5.5).<br>
**왜 헷갈리는가**: UVM 전용 API 이름이라 일반 OOP 개념과 동떨어져 보여서.
:::

### DV 디버그 체크리스트

| 증상 | 1차 의심 | 어디 보나 |
|---|---|---|
| factory override를 등록했는데 안 먹힘 | 대상 객체를 `new`로 생성 (factory 우회) | `type_id::create` 사용 여부 grep |
| 부모 핸들 호출 시 자식 동작이 안 나옴 | 메서드에 `virtual` 누락 | 메서드 선언의 `virtual` 키워드 |
| 외부에서 내부 필드를 바꿔 버그 | 캡슐화 미적용 (가시성 한정자 없음) | 필드 `local`/`protected` 여부 |
| driver가 vif를 못 받아 NOVIF fatal | 의존성 주입 경로 불일치 (config_db) | set/get 계층 경로 일치 ([UVM M04](../../uvm/04_config_db_factory/)) |
| monitor가 특정 scoreboard에 못 박힘 | 추상 포트 대신 구체 의존 (DIP 위반) | analysis_port 경유 연결 여부 |

---

## 7. 핵심 정리 (Key Takeaways)

- **UVM = OOP의 SystemVerilog 번역본**: 4기둥·SOLID·GoF 패턴이 SV 문법으로 구체화된 것 (`oop_spec.md` §7).
- **4기둥의 SV 문법**: 캡슐화=`local`/`protected`, 추상화=`virtual class`, 상속=`extends`, 다형성=`virtual` + `#(...)`.
- **두 다형성**: `virtual` 메서드(subtype) vs 파라미터화 클래스 `#(REQ,RSP)`(parametric).
- **Factory = OCP**: `type_id::create` + override로 base 코드 변경 없이 동작 확장. `new`는 override 불가.
- **config_db = 의존성 주입**, **analysis port = DIP + Observer**.
- UVM 코드를 읽을 때 각 줄을 OOP 개념/패턴으로 환원하면 설계 의도가 드러납니다.

:::caution[실무 주의점]
- 컴포넌트 생성은 항상 `type_id::create`로 — factory의 OCP 이점을 포기하지 마세요.
- 오버라이드할 메서드에는 `virtual`을 빠뜨리지 마세요. 다형성이 조용히 깨집니다.
- config_db의 set/get 계층 경로 불일치는 가장 흔한 UVM 버그입니다 ([UVM Module 04](../../uvm/04_config_db_factory/) 참고).
:::
### 7.1 자가 점검

:::tip[🤔 Q1 — factory와 OCP (Bloom: Apply)]
에러 주입 driver로 동작을 바꾸고 싶다. base env·test를 한 줄도 안 고치려면 무엇을 쓰나?
<details>
<summary>정답</summary>

**factory type override** — `my_driver::type_id::set_type_override(err_driver::get_type())`를 test의 build_phase에 추가합니다 (`oop_spec.md` §7).
- 전제: base가 `my_driver::type_id::create`로 생성해야 override가 먹힙니다(`new`면 불가).
- 이것이 테스트벤치 수준의 OCP — 수정 없이(닫힘) 추가로 확장(열림)입니다.

</details>
:::
:::tip[🤔 Q2 — 매핑 (Bloom: Evaluate)]
"analysis port는 DIP와 Observer 둘 다의 구현"이라는 주장을 평가하라.
<details>
<summary>정답</summary>

**타당합니다.** 두 측면이 동시에 성립합니다.
- **DIP**: producer(monitor)와 consumer(scoreboard)가 추상 포트로 분리되어 서로의 구체 타입을 모릅니다.
- **Observer**: 상태(트랜잭션)를 여러 구독자에게 1:N broadcast하는 GoF Observer의 정의 그대로입니다 (Module 03 §4.3).
- 한 메커니즘이 여러 원칙/패턴을 동시에 구현하는 것은 흔합니다.

</details>
:::
### 7.2 출처

**External**
- IEEE 1800-2017 (SystemVerilog) — §8 클래스, §25.9 virtual interface, §35 DPI-C
- UVM 1.2 Reference Manual — §8 Factory, §10.2 config_db, §12 TLM
- Gang of Four. *Design Patterns* — Factory Method, Observer

---

## 다음 모듈

이 토픽의 마지막 모듈입니다. 개념을 굳히려면:

→ [용어집 (Glossary)](../glossary/) 에서 OOP·SOLID·패턴 핵심 용어를 ISO 11179 정의로 복습하고,<br>
→ UVM에서의 실제 적용은 [UVM 코스](../../uvm/) — 특히 [config_db & Factory](../../uvm/04_config_db_factory/) 와 [TLM/Scoreboard/Coverage](../../uvm/05_tlm_scoreboard_coverage/) 로 이어가세요.

[퀴즈 풀어보기 →](../quiz/04_sv_uvm_mapping_quiz/)
