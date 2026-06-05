---
title: "Module 02 — SOLID 설계 원칙"
---

:::tip[학습 목표]
이 모듈을 마치면:

- **Explain** SOLID 다섯 원칙(SRP/OCP/LSP/ISP/DIP)이 각각 무엇을 보장하는지 한 문장으로 설명할 수 있다.
- **Differentiate** "수정으로 확장"(OCP 위반)과 "추가로 확장"(OCP 준수)의 차이를 구분할 수 있다.
- **Analyze** 주어진 클래스가 어떤 SOLID 원칙을 위반하는지 진단할 수 있다.
- **Apply** SOLID를 적용해 결합도를 낮추는 리팩터링(인터페이스 분리, 의존성 역전)을 수행할 수 있다.
- **Evaluate** UVM의 TLM port·factory·config_db가 어떤 SOLID 원칙의 구현인지 평가할 수 있다.
:::
:::note[사전 지식]
- [Module 01 — OOP 4기둥 & 객체 관계](../01_oop_pillars_relationships/) (특히 IS-A / 상속 vs 합성)
- 추상 클래스·인터페이스 개념
:::
---

## 1. Why care? — "잘 짠 코드"와 "확장 가능한 코드"는 다르다

### 1.1 시나리오 — scoreboard가 자꾸 손이 가는 이유

한 scoreboard 클래스가 기능 정확성 검사뿐 아니라 coverage 수집, 로그 포맷팅, 레지스터 모델 접근까지 떠안고 있다고 합시다. 처음엔 한 곳에 다 있어 편해 보이지만, coverage 정책이 바뀌면 scoreboard를 고쳐야 하고, 로그 포맷이 바뀌어도 scoreboard를 고쳐야 합니다. 즉 *바뀌는 이유가 여러 개*라서 손이 끊임없이 갑니다. 게다가 이 scoreboard를 다른 프로젝트에 재사용하려 하면 불필요한 coverage·레지스터 의존이 딸려옵니다 (`oop_spec.md` §5.1).

### 1.2 SOLID가 푸는 문제

SOLID는 클래스와 그 관계를 *확장·유지보수·테스트하기 쉽게* 설계하기 위한 다섯 원칙입니다 (`oop_spec.md` §5). 네 기둥이 "도구"이고 SOLID는 "그 도구를 쓰는 법"입니다 (`design_pattern_onboarding.md` cooking analogy). 검증 환경에서 SOLID를 지키면 VIP가 DUT에 독립적이 되고(재사용), 새 프로토콜을 기존 코드 수정 없이 추가할 수 있으며(확장), scoreboard·monitor가 추상 포트로 느슨하게 결합되어 테스트가 쉬워집니다.

---

## 2. Intuition — 다섯 글자가 가리키는 다섯 방향

:::tip[💡 한 줄 비유]
**SOLID** ≈ **잘 정돈된 공구함**.<br>
공구마다 한 가지 용도(SRP), 새 공구는 추가하되 기존 건 안 건드리고(OCP), 같은 규격이면 바꿔 끼울 수 있고(LSP), 필요한 공구만 꺼내 쓰며(ISP), 공구가 아니라 "규격"에 맞춰 설계합니다(DIP).
:::
### 한 장 그림 — 다섯 원칙의 한 줄 정의

```d2
direction: down

S: "S — SRP\nSingle Responsibility\n'바뀌는 이유는 하나'"
O: "O — OCP\nOpen/Closed\n'확장엔 열고, 수정엔 닫는다'"
L: "L — LSP\nLiskov Substitution\n'자식은 부모 자리에 대체 가능'"
I: "I — ISP\nInterface Segregation\n'안 쓰는 인터페이스에 의존 강요 금지'"
D: "D — DIP\nDependency Inversion\n'구체가 아닌 추상에 의존'"

S -> O -> L -> I -> D: "결합도 낮추기"
```

### 왜 이 다섯인가 — Design rationale

다섯 원칙은 결국 하나의 적을 겨냥합니다 — *변경의 파급(coupling)*. SRP는 한 클래스가 바뀌는 이유를 하나로 줄여 변경 충격을 가두고, OCP는 변경을 "수정" 대신 "추가"로 돌려 기존 테스트를 보호하며, LSP는 상속 계층이 거짓 IS-A로 무너지지 않게 지키고, ISP는 뚱뚱한 인터페이스가 무관한 변경을 전파하지 못하게 막으며, DIP는 고수준 모듈이 저수준 구체에 직접 묶이는 것을 끊습니다. 다섯이 함께 작동해야 "한 곳을 바꿔도 다른 곳이 안 깨지는" 시스템이 됩니다.

---

## 3. 작은 예 — DIP 하나로 결합을 끊어 보기

가장 효과가 극적인 DIP를 예로, scoreboard가 구체 monitor에 묶인 코드를 추상에 의존하도록 바꿉니다.

### 단계별 다이어그램

```d2
direction: right

BEFORE: "위반 (구체 의존)" {
  direction: down
  SB1: "Scoreboard"
  AM1: "AxiMonitor\n(concrete)"
  SB1 -> AM1: "직접 의존\n→ AXI 전용으로 고정"
}
AFTER: "준수 (추상 의존)" {
  direction: down
  SB2: "Scoreboard"
  AP: "uvm_analysis_imp\n(abstraction / port)"
  M2: "AxiMonitor"
  M3: "PcieMonitor"
  SB2 -> AP: "추상에 의존"
  M2 -> AP: "연결"
  M3 -> AP: "연결 (교체 가능)"
}
```

### 단계별 의미

| Step | 무엇이 | 어떻게 바뀌나 |
|---|---|---|
| Before | Scoreboard가 `AxiMonitor` 타입을 직접 필드로 보유 | AXI 전용으로 고정 — PCIe monitor로 못 바꿈 |
| After | Scoreboard가 `uvm_analysis_imp`(추상 포트)에 의존 | 어떤 monitor든 포트에 연결만 하면 동작 — 고수준이 저수준 구체를 모름 |

### 실제 코드 (위반 → 준수)

```systemverilog
// ❌ DIP 위반 — 고수준(Scoreboard)이 저수준 구체 클래스에 직접 의존
class Scoreboard;
  AxiMonitor monitor;   // concrete dependency — AXI 전용으로 못 박힘
endclass

// ✅ DIP 준수 — 추상(analysis port)에 의존
class Scoreboard;
  uvm_analysis_imp #(axi_txn, Scoreboard) ap;  // abstraction
  function void write(axi_txn t);
    // 어떤 source가 보냈든 추상 트랜잭션으로만 처리
  endfunction
endclass
```

:::note[여기서 잡아야 할 핵심]
UVM의 TLM 포트(`uvm_analysis_port`, `uvm_blocking_put_port`)는 DIP의 정석적 표현입니다. producer와 consumer가 추상 포트 타입을 통해 분리되어, 어느 쪽도 상대의 구체 타입을 알지 못합니다 (`oop_spec.md` §5.5).
:::
---

## 4. 일반화 — 다섯 원칙 전체

각 원칙의 정의(인용)와 DV 예시를 정리합니다 (`oop_spec.md` §5.1–§5.5).

### 4.1 SRP — Single Responsibility Principle

> *클래스는 바뀌어야 할 이유를 단 하나만 가져야 한다.*

한 클래스가 비즈니스 로직과 영속화를 동시에 다루면, DB 스키마 변경이 비즈니스 로직 클래스까지 건드리게 됩니다 — 두 관심사가 하나로 결합된 것입니다. **DV 예시**: scoreboard는 기능 정확성 검사만 해야 합니다. coverage 수집·로깅·레지스터 모델 접근을 같은 클래스에 끌어들이면 SRP를 위반하고 재사용이 어려워집니다 (`oop_spec.md` §5.1).

### 4.2 OCP — Open/Closed Principle

> *소프트웨어 엔티티는 확장엔 열려 있고 수정엔 닫혀 있어야 한다.*

새 동작은 기존 클래스를 *편집*하지 말고 새 클래스를 *추가*해 더합니다. 편집은 기존 테스트를 깨고 회귀 위험을 들입니다. **구현**: 인터페이스·추상 클래스에 프로그래밍합니다. 새 프로토콜은 `my_new_driver extends uvm_driver`를 새로 쓰면 되고, 테스트 인프라는 바뀌지 않습니다 (`oop_spec.md` §5.2).

### 4.3 LSP — Liskov Substitution Principle

> *서브타입은 그 기반 타입으로 대체 가능해야 한다.*

`S`가 `T`의 서브타입이면, 프로그램에서 `T` 객체를 `S` 객체로 바꿔도 프로그램의 정확성이 깨지면 안 됩니다. 위반은 *의미적으로 거짓인 IS-A*를 만듭니다 — `Square extends Rectangle`은 Square의 width를 설정하면 height도 바뀌어 Rectangle 계약을 깨므로 LSP 위반입니다. **DV 함의**: 버스를 절대 구동하지 않는 `passive_driver`가 `uvm_driver`를 상속하면 active driver의 진짜 대체물이 아니므로 LSP 위반 — 별도 `uvm_component`로 모델링해야 합니다 (`oop_spec.md` §5.3).

### 4.4 ISP — Interface Segregation Principle

> *클라이언트는 자신이 쓰지 않는 인터페이스에 의존하도록 강요받아선 안 된다.*

메서드가 많은 뚱뚱한 인터페이스는 구현 클래스에 필요 없는 메서드까지 제공하도록 강요합니다. 큰 인터페이스를 역할별 작은 인터페이스로 쪼갭니다. **DV 예시**: 메서드 30개짜리 단일 `IVipControl` 대신 `IConnectable`·`IResettable`·`IConfigurable`을 분리하면, VIP 리셋만 필요한 컴포넌트는 `IResettable`만 구현합니다 (`oop_spec.md` §5.4).

### 4.5 DIP — Dependency Inversion Principle

> *구체가 아닌 추상에 의존하라.*

고수준 모듈이 저수준 모듈을 직접 import하지 않고, 둘 다 추상(인터페이스/추상 클래스)에 의존하게 합니다. 이러면 교체와 테스트가 쉬워집니다. UVM의 TLM 포트가 정석 구현입니다 (§3 참고, `oop_spec.md` §5.5).

### 4.6 요약 표

| 원칙 | 한 줄 | 위반 신호 | DV 적용 |
|---|---|---|---|
| SRP | 바뀌는 이유는 하나 | 한 클래스가 여러 관심사 | scoreboard는 비교만 |
| OCP | 확장엔 열고 수정엔 닫음 | 새 기능마다 기존 클래스 편집 | 새 driver 추가 (factory) |
| LSP | 자식은 부모 자리에 대체 가능 | 자식이 부모 계약을 깸 | passive는 driver 상속 금지 |
| ISP | 안 쓰는 인터페이스 의존 강요 금지 | 뚱뚱한 인터페이스 | 역할별 인터페이스 분리 |
| DIP | 추상에 의존 | 고수준이 구체 클래스 import | TLM analysis port |

---

## 5. 디테일 — UVM이 곧 SOLID의 살아있는 예제

### 5.1 OCP의 결정판 — UVM Factory

`oop_spec.md` §7은 **UVM factory를 검증에서 가장 강력한 OOP 패턴**으로 꼽습니다. factory는 테스트벤치 수준에서 OCP를 구현합니다 — 동작을 바꾸려면 기존 env를 편집하지 않고 *override를 새로 등록*하면 됩니다.

```systemverilog
// 기존 env·test 코드를 한 줄도 안 고치고 driver 동작을 교체 (OCP)
class err_inject_test extends base_test;
  `uvm_component_utils(err_inject_test)
  function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    // 타입 override 등록 — base env는 그대로, 동작만 확장
    my_driver::type_id::set_type_override(err_driver::get_type());
  endfunction
endclass
```

이 한 줄이 OCP의 핵심을 보여줍니다 — `base_test`도 `env`도 수정 대상이 아니고(닫힘), 새 동작은 override 등록이라는 *추가*로 확장됩니다(열림).

### 5.2 SRP × 합성 — 책임을 쪼개 env를 조립

```systemverilog
// SRP: 각 컴포넌트가 단일 책임. env는 이들을 합성(HAS-A)만 함.
class my_env extends uvm_env;
  `uvm_component_utils(my_env)
  my_agent      agent;   // 자극/관찰 책임
  my_scoreboard sb;      // 비교 책임만
  my_coverage   cov;     // coverage 책임만

  function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    agent = my_agent::type_id::create("agent", this);
    sb    = my_scoreboard::type_id::create("sb", this);
    cov   = my_coverage::type_id::create("cov", this);
  endfunction

  // DIP: 추상 analysis port로 연결 — 누가 구독하는지 monitor는 모름
  function void connect_phase(uvm_phase phase);
    agent.mon.ap.connect(sb.actual_imp);          // 추상 포트
    agent.mon.ap.connect(cov.analysis_export);
  endfunction
endclass
```

이 짧은 env에 세 원칙이 동시에 들어 있습니다 — scoreboard·coverage가 각자 단일 책임(SRP), env가 이들을 합성(Module 01의 HAS-A), monitor가 추상 포트로 broadcast(DIP).

### 5.3 LSP를 지키는 상속 설계

passive 동작을 active driver의 서브타입으로 끼워 넣으면 LSP가 깨집니다. 올바른 설계는 driver의 *대체물이 아닌* 것을 driver로 만들지 않는 것입니다.

```systemverilog
// ❌ LSP 위반 — passive가 driver를 상속하나 구동 계약을 안 지킴
class passive_driver extends my_driver;
  task run_phase(uvm_phase phase);  /* 아무것도 구동 안 함 */ endtask
endclass

// ✅ 별도 컴포넌트로 모델링 — active와 substitutable 관계를 강요 안 함
class passive_observer extends uvm_component;
  `uvm_component_utils(passive_observer)
  // 관찰 전용 — driver 계약과 무관
endclass
```

---

## 6. 흔한 오해 와 디버그 체크리스트

### 흔한 오해

:::danger[❓ 오해 1 — 'OCP를 지키려면 처음부터 모든 확장점을 인터페이스로 열어야 한다']
**실제**: 그것은 YAGNI 위반으로 이어집니다. OCP는 *예상되는 변경 축*에만 추상화를 두라는 뜻이지, 모든 것을 추상화하라는 게 아닙니다. "무엇이 자주 바뀌는가"를 먼저 식별하세요 (Module 01 §5.2, `oop_spec.md` §6.2).<br>
**왜 헷갈리는가**: "확장에 열려야 한다"를 "모든 것에 열려야 한다"로 과대 해석해서.
:::
:::danger[❓ 오해 2 — '컴파일만 되면 LSP는 지켜진 것이다']
**실제**: LSP는 *문법*이 아니라 *의미적 계약*입니다. `passive_driver extends my_driver`는 컴파일되지만 driver의 "구동한다"는 계약을 어겨 LSP를 위반합니다. 타입 체커는 이를 못 잡습니다 (`oop_spec.md` §5.3).<br>
**왜 헷갈리는가**: `extends`가 통과하면 관계가 정당해 보여서.
:::
:::danger[❓ 오해 3 — 'SRP는 클래스를 잘게 쪼개라는 뜻이다']
**실제**: SRP는 *바뀌는 이유*를 하나로 줄이라는 것이지, 줄 수를 줄이라는 게 아닙니다. 같은 이유로 함께 바뀌는 코드는 한 클래스에 있어야 합니다. 무작정 쪼개면 응집도가 깨집니다 (`oop_spec.md` §5.1).<br>
**왜 헷갈리는가**: "단일 책임"을 "작은 클래스"로 오역해서.
:::

### DV 디버그 체크리스트

| 증상 | 1차 의심 | 어디 보나 |
|---|---|---|
| 새 프로토콜 추가 때마다 env/test 코드를 고쳐야 함 | OCP 위반 — factory override 대신 직접 편집 | `set_type_override` 사용 여부 |
| scoreboard를 다른 프로젝트에 못 가져감 | SRP 위반 — coverage/log/RAL이 섞임 | scoreboard 클래스의 책임 수 |
| 자식 컴포넌트가 부모 동작 기대를 깨서 silent 오작동 | LSP 위반 | `extends` 관계가 진짜 substitutable인지 |
| 컴포넌트가 안 쓰는 메서드까지 구현 강요됨 | ISP 위반 | 인터페이스가 역할별로 분리됐는지 |
| scoreboard가 특정 monitor 타입에 못 박힘 | DIP 위반 | 구체 클래스 대신 analysis port 의존 여부 |

---

## 7. 핵심 정리 (Key Takeaways)

- **SOLID는 변경의 파급(coupling)을 줄이는 다섯 방향**입니다 — 네 기둥이 도구라면 SOLID는 도구 쓰는 법.
- **SRP**: 바뀌는 이유는 하나. scoreboard는 비교만.
- **OCP**: 확장엔 열고 수정엔 닫음. UVM factory override가 정석 구현.
- **LSP**: 자식은 부모 자리에 대체 가능. 컴파일이 아니라 *의미적 계약*. passive를 driver로 상속하지 말 것.
- **ISP**: 뚱뚱한 인터페이스를 역할별로 분리.
- **DIP**: 구체가 아닌 추상에 의존. UVM TLM 포트가 정석 구현.

:::caution[실무 주의점]
- SOLID는 *적용 자체*가 목적이 아닙니다. 결합도가 실제로 문제일 때 적용하고, 과하면 KISS/YAGNI 위반이 됩니다.
- LSP 위반은 컴파일러가 못 잡으므로, 상속 설계 시 "부모 계약을 자식이 어기지 않는가"를 사람이 검토해야 합니다.
:::
### 7.1 자가 점검

:::tip[🤔 Q1 — OCP 진단 (Bloom: Analyze)]
새 응답 코드를 추가할 때마다 `case`문에 분기를 *편집*해 넣는 scoreboard는 어떤 원칙을 위반하나?
<details>
<summary>정답</summary>

**OCP 위반**입니다. 새 동작을 *추가*가 아니라 기존 코드 *수정*으로 처리하고 있어, 매번 기존 테스트를 깰 위험이 생깁니다 (`oop_spec.md` §5.2).
- 개선: 응답 처리를 추상 핸들러/전략으로 빼고, 새 코드는 새 핸들러 클래스를 추가(이는 Module 03의 Strategy 패턴과 연결).

</details>
:::
:::tip[🤔 Q2 — DIP와 UVM (Bloom: Evaluate)]
"UVM analysis port가 DIP의 구현"이라는 주장의 근거는?
<details>
<summary>정답</summary>

producer(monitor)와 consumer(scoreboard/coverage)가 **추상 포트 타입을 통해 분리**되어, 어느 쪽도 상대의 구체 클래스를 알지 못하기 때문입니다 (`oop_spec.md` §5.5).
- 고수준(scoreboard)이 저수준(특정 monitor)에 직접 의존하지 않고 둘 다 추상(port)에 의존 — 이것이 DIP의 정의 그대로입니다.
- 덕분에 monitor를 다른 구현으로 교체해도 scoreboard 코드는 불변입니다.

</details>
:::
### 7.2 출처

**Internal (HDG / Confluence)**
- `oop_spec.md` (Object-Oriented Programming Overview) — §5 SOLID (§5.1 SRP ~ §5.5 DIP), §6.2 Design for Change, §7 UVM factory = OCP
- `design_pattern_onboarding.md` — cooking analogy (도구/사용법/레시피 위계)
- Confluence: *OOP* (SOLID bullet list)

**External**
- McLaughlin, Pollice, West. *Head First Object-Oriented Analysis and Design*. O'Reilly, 2006.
- Robert C. Martin. *Clean Code / Agile Principles* — SOLID 원전
- UVM 1.2 User's Guide §8 (Factory) — Accellera

---

## 다음 모듈

→ [Module 03 — GoF 23 디자인 패턴 개요](../03_gof_design_patterns/): 네 기둥(도구)과 SOLID(사용법) 위에 올라가는 *레시피*. 같은 문제를 반복해 풀어 온 23가지 검증된 해법.

[퀴즈 풀어보기 →](../quiz/02_solid_principles_quiz/)
