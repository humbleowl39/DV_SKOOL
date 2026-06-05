---
title: "Quiz — Module 03: GoF 23 디자인 패턴 개요"
---

[← Module 03 본문으로 돌아가기](../../03_gof_design_patterns/)

---

## Q1. (Remember)

GoF 23 패턴의 세 그룹과 각 개수가 올바르게 짝지어진 것은?

- [ ] A. Creational 5 / Structural 7 / Behavioral 11
- [ ] B. Creational 7 / Structural 5 / Behavioral 11
- [ ] C. Creational 11 / Structural 5 / Behavioral 7
- [ ] D. Creational 5 / Structural 11 / Behavioral 7

<details>
<summary>정답 / 해설</summary>

**A**. GoF 23은 Creational 5(Singleton, Factory Method, Abstract Factory, Builder, Prototype), Structural 7, Behavioral 11로 나뉩니다 (`design_pattern_onboarding.md` Classification). 5 + 7 + 11 = 23. 가장 많은 것이 행동 패턴(11)이라는 점을 기억하면 헷갈리지 않습니다.

</details>
## Q2. (Understand)

"디자인 패턴은 복붙해서 쓰는 완성된 코드다"라는 설명이 왜 틀렸는지 설명하라.

<details>
<summary>정답 / 해설</summary>

패턴은 완성된 코드가 아니라 **구조의 청사진(레시피)**입니다 — "이 상황에서는 이렇게 구조를 잡아라"는 지침이며, 실제 구현은 언어·문맥마다 다릅니다 (`design_pattern_onboarding.md` Overview). 책에 실린 예제 코드는 그 청사진의 한 가지 구현 예시일 뿐, 그 코드 자체가 패턴은 아닙니다. 패턴은 4기둥·SOLID 위에 앉아 주로 상속·인터페이스·합성으로 표현됩니다.

</details>
## Q3. (Apply)

"객체의 상태가 변하면 그에 의존하는 여러 객체에 자동으로 알려야 한다"는 요구에 맞는 패턴은?

- [ ] A. Singleton
- [ ] B. Adapter
- [ ] C. Observer
- [ ] D. Builder

<details>
<summary>정답 / 해설</summary>

**C (Observer)**. 일대다 의존을 정의해 상태 변화를 여러 객체에 방송하는 Behavioral 패턴입니다 (`design_pattern_onboarding.md` Behavioral). UVM의 analysis port 1:N broadcast가 그 실례입니다. Singleton(A)은 생성 제어, Adapter(B)는 인터페이스 호환, Builder(D)는 복잡 객체 단계별 생성으로 모두 다른 문제를 풉니다.

</details>
## Q4. (Apply)

"호환되지 않는 레거시 인터페이스를 새 시스템에 연결"하는 문제에 맞는 패턴과 그 그룹은?

- [ ] A. Strategy / Behavioral
- [ ] B. Adapter / Structural
- [ ] C. Prototype / Creational
- [ ] D. Mediator / Behavioral

<details>
<summary>정답 / 해설</summary>

**B (Adapter / Structural)**. Adapter는 호환되지 않는 인터페이스를 감싸 연결 가능하게 합니다 (`design_pattern_onboarding.md` Structural). "객체를 어떻게 조립/구조화하는가"의 문제이므로 structural 그룹입니다. UVM의 `uvm_reg_adapter`(reg 연산 ↔ 버스 트랜잭션 변환)가 이 패턴의 사례입니다(추론).

</details>
## Q5. (Analyze)

같은 "여러 객체가 관련된" 상황이라도 Singleton과 Observer는 서로 다른 *종류*의 문제를 푼다. 각각 어떤 종류인가?

<details>
<summary>정답 / 해설</summary>

**Singleton은 *생성*의 문제**(객체를 몇 개 만드나 — 정확히 하나, Creational)이고, **Observer는 *통신*의 문제**(상태 변화를 누구에게 알리나 — 1:N broadcast, Behavioral)입니다 (`design_pattern_onboarding.md` Creational/Behavioral). 패턴을 고를 때 "이건 생성/구조/행동 중 어느 문제인가"를 먼저 분류하면 후보가 좁혀진다는 점을 보여주는 대비입니다.

</details>
## Q6. (Evaluate)

값 하나를 한 번 읽어 쓰는 단순 설정 객체에 Builder 패턴을 도입하자는 제안을 평가하라.

<details>
<summary>정답 / 해설</summary>

**거절해야 합니다 — 패턴 과용**입니다. Builder는 *복잡한* 객체의 단계별 생성을 단순화하기 위한 것인데, 값 하나뿐인 설정에는 불필요한 구조를 더해 코드를 오히려 복잡하게 만들고 KISS/YAGNI를 위반합니다 (`design_pattern_onboarding.md` Why use them, Steps §4). 패턴 적용의 판단 기준은 항상 "이 문제가 정말 이 패턴이 푸는 문제인가, 더 단순한 방법은 없는가"입니다.

</details>
