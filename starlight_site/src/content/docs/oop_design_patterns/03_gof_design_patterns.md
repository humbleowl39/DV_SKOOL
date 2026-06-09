---
title: "Module 03 — GoF 23 디자인 패턴 개요"
---

:::tip[학습 목표]
이 모듈을 마치면:

- **Explain** 디자인 패턴이 "코드"가 아니라 "청사진(레시피)"인 이유와 패턴이 4기둥·SOLID 위에 앉는 위계를 설명할 수 있다.
- **Classify** GoF 23 패턴을 creational(5) / structural(7) / behavioral(11)로 분류할 수 있다.
- **Differentiate** 각 그룹이 해결하는 문제 영역(생성 / 구조 / 책임·통신)을 구분할 수 있다.
- **Analyze** 주어진 설계 문제에 어떤 패턴이 적합한지, 그리고 패턴이 과용인지를 분석할 수 있다.
- **Evaluate** 패턴 도입 전 "더 단순한 방법이 없는가"를 기준으로 판단할 수 있다.
:::
:::note[사전 지식]
- [Module 01 — OOP 4기둥 & 객체 관계](../01_oop_pillars_relationships/)
- [Module 02 — SOLID 설계 원칙](../02_solid_principles/) (특히 OCP)
:::
---

## 1. Why care? — 같은 문제를 매번 처음부터 풀 것인가

### 1.1 시나리오 — "이거 전에도 풀었던 문제인데"

설계를 하다 보면 같은 종류의 문제가 반복해서 나타납니다 — "객체를 정확히 하나만 만들고 싶다", "호환 안 되는 인터페이스를 연결해야 한다", "상태가 바뀌면 여러 곳에 알려야 한다". 매번 처음부터 해법을 짜내면 시간이 들고 품질도 들쭉날쭉합니다. **디자인 패턴**은 수많은 개발자가 같은 문제에 부딪혀 다듬어 온 *검증된 재사용 해법*입니다 (`design_pattern_onboarding.md` Overview).

중요한 것은 패턴이 *복붙할 완성된 코드가 아니라*는 점입니다. 패턴은 "이 상황에서는 이렇게 구조를 잡아라"고 일러주는 **청사진**에 가깝습니다. 따라서 패턴은 4기둥(캡슐화·상속·추상화·다형성)과 SOLID 원칙 *위에* 앉으며, 주로 상속·인터페이스·합성으로 표현됩니다 (`design_pattern_onboarding.md` Overview).

### 1.2 왜 검증 엔지니어에게 중요한가

UVM 자체가 GoF(Gang of Four — 1994년 디자인 패턴 카탈로그를 펴낸 네 저자, 그리고 그들이 정리한 23개 패턴 모음) 패턴의 집합체입니다 — factory(객체 생성을 한 곳에 위임하는 중앙 생성기)는 Factory Method/Abstract Factory, sequence-driver는 Template Method, analysis port(트랜잭션을 여러 구독자에 뿌리는 추상 포트)는 Observer, config 객체로 동작을 바꾸는 것은 Strategy의 변형입니다. 패턴 어휘를 익히면 UVM 코드를 읽을 때 "이건 Observer다"라고 의도를 즉시 읽어낼 수 있고, 팀과 "여기 Factory 쓰자"는 한마디로 설계를 공유할 수 있습니다 — 이것이 패턴의 **공통 어휘** 가치입니다 (`design_pattern_onboarding.md` Why use them).

---

## 2. Intuition — 도구 → 사용법 → 레시피

:::tip[💡 한 줄 비유]
**디자인 패턴** ≈ **검증된 요리 레시피**.<br>
칼·냄비(4기둥)와 그 사용법(SOLID)을 안다고 좋은 요리가 나오진 않습니다. 자주 나오는 요리를 안정적으로 만들려면 *레시피*가 필요한데, 패턴이 바로 "자주 재발하는 설계 문제를 위한 레시피"입니다.
:::
### 한 장 그림 — 패턴이 앉는 위계와 세 분류

```d2
direction: down

STACK: "위계 (요리 비유)" {
  direction: down
  T: "도구 — 4기둥\n(캡슐화/상속/추상화/다형성)"
  U: "사용법 — SOLID 원칙"
  R: "레시피 — 디자인 패턴"
  T -> U -> R
}

GOF: "GoF 23 분류 (목적별)" {
  direction: down
  C: "Creational · 5\n객체를 '어떻게 생성'"
  S: "Structural · 7\n객체/클래스를 '어떻게 조립'"
  B: "Behavioral · 11\n책임·통신을 '어떻게 분배'"
}

STACK -> GOF: "패턴은 위계의 맨 위"
```

### 왜 세 그룹인가 — Design rationale

GoF는 23개 패턴을 *목적*에 따라 세 그룹으로 나눕니다 (`design_pattern_onboarding.md` Classification). 설계에서 마주치는 질문이 크게 셋이기 때문입니다 — "객체를 어떻게 만들지(생성)", "객체들을 어떻게 큰 구조로 엮을지(구조)", "객체들이 책임과 통신을 어떻게 나눌지(행동)". 패턴을 외울 때 이 세 질문 중 어느 것을 푸는지를 먼저 잡으면 분류가 자연스럽게 따라옵니다.

---

## 3. 작은 예 — Singleton vs Observer로 "생성"과 "행동" 대비

가장 익숙한 두 패턴으로 creational과 behavioral의 차이를 봅니다.

### 단계별 다이어그램

```d2
direction: right

SINGLETON: "Singleton (Creational)" {
  direction: down
  G: "getInstance()"
  I: "유일 인스턴스\n(단 하나만 생성)"
  G -> I: "항상 같은 객체 반환"
}
OBSERVER: "Observer (Behavioral)" {
  direction: down
  SUB: "Subject\n(상태 보유)"
  O1: "Observer A"
  O2: "Observer B"
  SUB -> O1: "notify (1:N broadcast)"
  SUB -> O2
}
```

### 단계별 의미

| 패턴 | 그룹 | 푸는 문제 | UVM 대응 |
|---|---|---|---|
| Singleton | Creational | 클래스를 정확히 한 번만 생성하며 전역 접근 보장 | `uvm_factory`·`uvm_root` (전역 유일) |
| Observer | Behavioral | 상태 변화를 여러 객체에 일대다로 방송 | analysis port 1:N broadcast |

### 코드 스케치

```cpp
// Singleton — 생성을 통제 (Creational)
class Factory {
    static Factory* inst;
    Factory() {}                     // private 생성자
public:
    static Factory* getInstance() {  // 항상 같은 인스턴스
        if (!inst) inst = new Factory();
        return inst;
    }
};

// Observer — 책임·통신 분배 (Behavioral)
class Subject {
    list<Observer*> observers;
public:
    void attach(Observer* o) { observers.push_back(o); }
    void notify() {                  // 1:N broadcast
        for (auto o : observers) o->update();
    }
};
```

:::note[여기서 잡아야 할 것]
같은 "여러 객체가 관련된" 상황이라도, Singleton은 *생성*의 문제(몇 개를 만드나)이고 Observer는 *통신*의 문제(누구에게 알리나)입니다. 패턴을 고를 때 "이건 생성/구조/행동 중 어느 문제인가"를 먼저 분류하면 후보가 좁혀집니다.
:::
---

## 4. 일반화 — GoF 23 전체 카탈로그

아래 세 표의 한 줄 설명은 모두 `design_pattern_onboarding.md`의 분류 표를 따릅니다.

### 4.1 Creational — 5개 · *객체를 어떻게 생성하는가*

(`design_pattern_onboarding.md` Creational)

| 패턴 | 한 줄 의도 |
|---|---|
| Singleton | 클래스가 정확히 한 번만 인스턴스화되도록 보장하면서 전역 접근을 허용 |
| Factory Method | 객체 생성 인터페이스를 정의하되, 어느 클래스를 인스턴스화할지는 서브클래스가 결정 |
| Abstract Factory | 관련 객체들의 *family*를 생성하는 인터페이스를 제공하고 생성을 추상화 |
| Builder | 복잡한 객체의 생성을 단계별 단계로 분리해 단순화 |
| Prototype | 기존 객체(template)를 복제해 새 객체를 생성 |

### 4.2 Structural — 7개 · *객체/클래스를 어떻게 더 큰 구조로 조립하는가*

(`design_pattern_onboarding.md` Structural)

| 패턴 | 한 줄 의도 |
|---|---|
| Adapter | 호환되지 않는 인터페이스를 감싸 연결 가능하게 함 |
| Bridge | 추상과 구현을 분리해 둘이 독립적으로 변하게 함 |
| Composite | 개별 객체와 복합 객체를 동일하게 다뤄 트리 구조 구성 |
| Decorator | 객체에 책임을 동적으로 덧붙여 기능을 확장 |
| Facade | 복잡한 서브시스템에 단순한 진입 인터페이스를 제공 |
| Flyweight | 공유 가능한 객체로 메모리 사용을 최적화 |
| Proxy | 접근 제어·지연 로딩 등을 위해 대리자를 둠 |

### 4.3 Behavioral — 11개 · *책임과 통신을 어떻게 분배하는가*

(`design_pattern_onboarding.md` Behavioral)

| 패턴 | 한 줄 의도 |
|---|---|
| Observer | 일대다 의존을 정의해 상태 변화를 여러 객체에 방송 |
| Strategy | 알고리즘을 캡슐화해 런타임에 교체·선택 가능하게 함 |
| Command | 요청을 객체로 캡슐화해 매개변수화·큐잉·로깅·지연 실행 |
| State | 객체의 상태를 캡슐화하고 전이를 관리 |
| Chain of Responsibility | 송신자와 처리자를 분리, 여러 처리자 중 하나가 요청 처리 |
| Visitor | 객체 구조를 순회하며 다양한 연산 수행 |
| Interpreter | 문법/언어 해석기를 제공해 그 언어로 표현된 문제를 해결 |
| Memento | 객체의 내부 상태를 포착·복원 |
| Mediator | 객체 간 상호작용을 캡슐화해 직접 통신을 막음(중재) |
| Template Method | 알고리즘의 골격을 정의하고 각 단계를 서브클래스에 위임 |
| Iterator | 컬렉션의 내부 구조와 무관하게 요소 접근을 표준화 |

### 4.4 패턴의 이점과 경계

패턴을 쓰면 재사용성·가독성·유지보수성·확장성(OCP)·안정성이 오르고, 무엇보다 **공통 어휘**가 생깁니다 — "여기 Factory 쓰자"가 설계 의도를 한 구절로 전달합니다 (`design_pattern_onboarding.md` Why use them). 그러나 패턴은 만능이 아닙니다. 더 단순한 방법이 있는데 패턴을 억지로 끼워 넣으면 코드만 복잡해집니다. 항상 *"이 문제에 정말 이 패턴이 필요한가?"*를 먼저 물어야 합니다 (`design_pattern_onboarding.md` Why use them, Steps §4).

---

## 5. 디테일 — UVM에 이미 박혀 있는 패턴들

UVM은 GoF 패턴을 따로 배우지 않아도 이미 쓰고 있는 프레임워크입니다. 대표 매핑을 봅니다 (UVM 매핑은 Module 04에서 코드로 심화).

| GoF 패턴 | 그룹 | UVM에서의 모습 | (근거) |
|---|---|---|---|
| Factory Method / Abstract Factory | Creational | `type_id::create` + `uvm_factory` override | factory = OCP |
| Singleton | Creational | `uvm_factory`·`uvm_root`의 전역 유일 인스턴스 | (추론 — 전형적 UVM 구조) |
| Observer | Behavioral | `uvm_analysis_port`의 1:N broadcast | TLM = DIP |
| Strategy | Behavioral | config 객체로 동작을 주입해 런타임 교체 | (추론 — config object 패턴) |
| Template Method | Behavioral | `run_phase` 골격 + 사용자 오버라이드 단계 | (추론 — phase 메서드 구조) |
| Adapter | Structural | `uvm_reg_adapter`가 reg 연산을 버스 트랜잭션으로 변환 | (추론 — RAL adapter 역할) |

:::caution[근거 표기]
위 표에서 (추론)으로 표시한 행은 UVM 구조에 대한 일반적 패턴 해석입니다. factory=OCP와 TLM=DIP 매핑은 SOLID 원칙에서 직접 도출되는 잘 알려진 대응입니다.
:::

세 개의 매핑은 결과만 적으면 외울 거리가 되지만, *왜 그 패턴인가*를 정의로 풀면 UVM 구조가 그대로 보입니다.

**Template Method가 UVM phase의 토대인 이유.** Template Method 패턴의 정의는 — *부모(base) 클래스가 알고리즘의 골격(단계의 순서와 흐름)을 고정하고, 각 단계의 구체 구현은 자식이 override로 채운다* — 입니다. UVM의 phase 메커니즘이 정확히 이 모양입니다. `uvm_component`(base)가 `build_phase → connect_phase → run_phase → ...`라는 단계의 *순서와 호출 흐름*을 고정해 두고, 사용자는 그중 `run_phase` 같은 개별 단계만 override해 자기 동작을 채웁니다. 단계가 *언제* 어떤 순서로 불릴지는 사용자가 정하지 않습니다 — 골격은 base가 쥐고, 빈칸만 자식이 메우는 것. 그래서 UVM의 phase 구조는 (추론이 아니라) Template Method의 교과서적 구현입니다.

**Strategy와 config-object의 동작 교체 기전.** Strategy 패턴의 정의는 — *알고리즘을 별도의 객체로 캡슐화해, 런타임에 그 객체를 갈아끼움으로써 동작을 교체* — 입니다. 핵심은 "동작이 *별도 객체*로 빠져나가 있고, 그 객체 참조를 바꾸면 동작이 바뀐다"는 점입니다. UVM에서 어느 쪽이 진짜 Strategy인지 구분이 중요합니다. config 필드로 `if (cfg.mode == A) ... else ...` 식으로 *분기*하는 것은 Strategy가 아니라 조건 분기일 뿐입니다 — 동작이 객체로 캡슐화되지 않았고 새 동작 추가 시 분기를 *편집*해야 하므로 오히려 OCP 위반입니다. config 객체에 *동작을 담은 핸들(정책 객체/콜백)* 을 넣어 컴포넌트가 그 핸들을 호출하는 형태라야 비로소 Strategy입니다. 한편 factory override(`set_type_override`)는 *타입 자체*를 통째로 바꾸는 것이라 구조적 교체에 가깝습니다 — 이 "config로 동작 주입 vs factory로 타입 교체"의 결정은 Module 04와 UVM 코스의 [config_db & Factory](../../uvm/04_config_db_factory/)에서 다시 다룹니다.

**Observer의 push vs pull.** Observer는 1:N broadcast이지만, *데이터가 어느 방향으로 흐르는가*로 두 형태가 갈립니다. **push형**은 subject가 상태 변화를 구독자에게 *밀어 넣습니다*(subject가 `update(data)`를 호출). **pull형**은 구독자가 필요할 때 subject에서 *당겨옵니다*(구독자가 `get()`을 호출). UVM의 `analysis_port`는 monitor(subject)가 `ap.write(item)`으로 트랜잭션을 구독자에게 *밀어주는* push형 Observer입니다. 대조적으로 cocotb의 `Queue`는 소비자 coroutine이 `await queue.get()`으로 *당겨가는* pull형입니다([cocotb M02](../../cocotb/02_coroutine_cosimulation/)). 같은 1:N 통신이라도 push냐 pull이냐가 누가 흐름의 주도권을 쥐는지를 가릅니다.
### 5.1 학습 순서 — 토대 → 분류 → 적용

패턴은 *토대 → 분류 → 적용* 순으로 익히는 것이 가장 자연스럽습니다. 이는 요리 비유 그대로입니다 — 도구와 사용법을 먼저 잡고 레시피로 넘어갑니다.

1. **토대 먼저** — 4기둥과 SOLID([Module 01](../01_oop_pillars_relationships/), [Module 02](../02_solid_principles/)). 이 위에 패턴이 서므로, 없으면 패턴이 *왜 그 모양인지* 안 보입니다.
2. **분류별로** — §4의 세 표를 creational → structural → behavioral 순으로 훑되, 각 패턴은 "이게 푸는 문제 한 줄"만 머리에 담습니다.
3. **흔한 것부터 깊게** — Singleton·Factory·Observer·Strategy처럼 실무에서 자주 쓰는 것부터 구현을 따라가 봅니다.
4. **과용 경계** — 적용 전 항상 "더 단순한 방법이 없는가"를 묻습니다 (`design_pattern_onboarding.md` Steps §4).

---

## 6. 흔한 오해 와 디버그 체크리스트

### 흔한 오해

:::danger[❓ 오해 1 — '디자인 패턴은 복붙할 코드 조각이다']
**실제**: 패턴은 완성된 코드가 아니라 *청사진/레시피*입니다 — "이 상황에선 이렇게 구조를 잡아라"는 지침이며, 구현은 언어·문맥마다 다릅니다 (`design_pattern_onboarding.md` Overview).<br>
**왜 헷갈리는가**: 책마다 예제 코드가 함께 실려 있어 "그 코드가 곧 패턴"처럼 보여서.
:::
:::danger[❓ 오해 2 — '패턴을 많이 쓸수록 좋은 설계다']
**실제**: 패턴은 만능이 아닙니다. 더 단순한 해법이 있는데 패턴을 강제하면 코드가 *더* 복잡해집니다. 적용 전 "정말 이 패턴이 필요한가"를 먼저 물어야 합니다 (`design_pattern_onboarding.md` Why use them).<br>
**왜 헷갈리는가**: 패턴을 많이 아는 것이 곧 잘 설계하는 것이라는 착각.
:::
:::danger[❓ 오해 3 — '패턴만 알면 OOP 기초는 몰라도 된다']
**실제**: 패턴은 4기둥·SOLID *위에* 앉습니다. 토대가 없으면 패턴이 왜 그렇게 생겼는지 이해할 수 없고 오용하게 됩니다 (`design_pattern_onboarding.md` Overview, Steps §1).<br>
**왜 헷갈리는가**: 패턴이 더 "고급"이라 토대를 건너뛰어도 될 것 같아서.
:::

### DV 디버그 / 설계 체크리스트

| 증상 | 1차 의심 | 어떻게 |
|---|---|---|
| 단순한 문제에 인터페이스·추상 클래스가 잔뜩 | 패턴 과용 (KISS/YAGNI 위반) | "더 단순한 방법" 재검토 |
| 같은 생성 로직이 여러 곳에 복붙 | Factory Method 후보 | 생성을 한 곳으로 위임 |
| 상태 변화를 여러 곳에 일일이 알림 호출 | Observer 후보 | 1:N broadcast로 분리 |
| 호환 안 되는 두 인터페이스를 억지로 맞물림 | Adapter 후보 | 어댑터 계층 도입 |
| `if/case`로 알고리즘을 분기하며 계속 편집 | Strategy 후보 (OCP 위반 신호) | 알고리즘을 전략 객체로 |

---

## 7. 핵심 정리 (Key Takeaways)

- **디자인 패턴 = 검증된 레시피**: 복붙 코드가 아니라 "이 상황엔 이렇게 구조를 잡아라"는 청사진.
- **위계**: 4기둥(도구) → SOLID(사용법) → 패턴(레시피). 패턴은 토대 위에 앉는다.
- **GoF 23 = 5 + 7 + 11**: Creational(생성) / Structural(구조) / Behavioral(책임·통신).
- **패턴 고르기**: "이건 생성/구조/행동 중 어느 문제인가"를 먼저 분류하면 후보가 좁혀진다.
- **공통 어휘**: "여기 Factory 쓰자"가 설계 의도를 한 구절로 전달.
- **과용 경계**: 적용 전 "더 단순한 방법이 없는가"를 항상 먼저 묻는다.

:::caution[실무 주의점]
- UVM의 factory·analysis port·sequence-driver는 이미 패턴의 구현체입니다 — 새로 짜기 전에 UVM이 제공하는 메커니즘을 먼저 보세요.
- 패턴 이름을 안다고 적용해도 된다는 뜻은 아닙니다. 문제가 그 패턴이 푸는 문제와 *정말 같은지* 확인하세요.
:::
### 7.1 자가 점검

:::tip[🤔 Q1 — 분류 (Bloom: Analyze)]
"호환되지 않는 레거시 인터페이스를 새 시스템에 연결"하는 문제는 어느 그룹의 어떤 패턴인가?
<details>
<summary>정답</summary>

**Structural 그룹의 Adapter**입니다 — 호환되지 않는 인터페이스를 감싸 연결 가능하게 합니다 (`design_pattern_onboarding.md` Structural).
- "객체를 어떻게 *조립/구조화*하는가"의 문제이므로 structural로 분류됩니다.
- UVM의 `uvm_reg_adapter`(reg 연산 ↔ 버스 트랜잭션 변환)가 이 패턴의 실제 사례입니다(추론).

</details>
:::
:::tip[🤔 Q2 — 과용 판단 (Bloom: Evaluate)]
값 하나를 한 번만 읽어 쓰는 단순 설정에 Builder 패턴을 도입하자는 제안, 어떻게 평가하나?
<details>
<summary>정답</summary>

**거절해야 합니다 — 패턴 과용**입니다. Builder는 *복잡한* 객체의 단계별 생성을 단순화하기 위한 것인데, 값 하나뿐인 단순 설정엔 오히려 불필요한 구조를 더해 KISS/YAGNI를 위반합니다 (`design_pattern_onboarding.md` Why use them, Steps §4).
- 판단 기준: "이 문제가 정말 이 패턴이 푸는 문제인가, 더 단순한 방법은 없는가."

</details>
:::
### 7.2 출처

**External**
- Gamma, Helm, Johnson, Vlissides (Gang of Four). *Design Patterns: Elements of Reusable Object-Oriented Software*. Addison-Wesley, 1994.
- refactoring.guru — Design Patterns
- Freeman et al. *Head First Design Patterns*. O'Reilly.

---

## 다음 모듈

→ [Module 04 — OOP → SystemVerilog / UVM 매핑](../04_sv_uvm_mapping/): 지금까지의 4기둥·SOLID·패턴이 SystemVerilog 문법과 UVM 메커니즘(상속·virtual·factory·config_db·TLM)에서 *정확히 어떤 코드*로 나타나는지 매핑.

[퀴즈 풀어보기 →](../quiz/03_gof_design_patterns_quiz/)
