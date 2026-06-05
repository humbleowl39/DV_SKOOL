---
title: "Quiz — Module 02: SOLID 설계 원칙"
---

[← Module 02 본문으로 돌아가기](../../02_solid_principles/)

---

## Q1. (Remember)

"소프트웨어 엔티티는 확장에는 열려 있고 수정에는 닫혀 있어야 한다"는 어느 SOLID 원칙인가?

- [ ] A. SRP
- [ ] B. OCP
- [ ] C. LSP
- [ ] D. DIP

<details>
<summary>정답 / 해설</summary>

**B (OCP, Open/Closed Principle)**. 새 동작은 기존 코드를 *편집*하지 말고 새 클래스를 *추가*해 더하라는 원칙입니다 (`oop_spec.md` §5.2). SRP(A)는 "바뀌는 이유는 하나", LSP(C)는 "자식은 부모 자리에 대체 가능", DIP(D)는 "추상에 의존"입니다.

</details>
## Q2. (Understand)

`Square extends Rectangle` 계층이 LSP를 위반하는 이유를 설명하라.

<details>
<summary>정답 / 해설</summary>

Square의 width를 설정하면 height도 함께 바뀌어야 하는데, 이는 "width와 height를 독립적으로 설정할 수 있다"는 Rectangle의 계약을 깨뜨립니다 (`oop_spec.md` §5.3). 따라서 Rectangle을 기대하는 코드에 Square를 넣으면 정확성이 깨지므로, Square는 Rectangle의 대체물이 될 수 없고 IS-A 관계가 의미적으로 거짓입니다. 컴파일은 통과해도 LSP는 *의미적 계약* 차원의 원칙임을 보여주는 고전적 예입니다.

</details>
## Q3. (Apply)

새 응답 코드가 추가될 때마다 scoreboard의 `case`문에 분기를 직접 *편집*해 넣고 있다. 이를 어떤 원칙에 맞게 리팩터링하나?

- [ ] A. SRP에 맞게 — 클래스를 더 잘게 쪼갠다
- [ ] B. OCP에 맞게 — 응답 처리를 추상 핸들러로 빼고 새 코드는 새 핸들러를 추가
- [ ] C. LSP에 맞게 — 상속 관계를 점검
- [ ] D. ISP에 맞게 — 인터페이스를 분리

<details>
<summary>정답 / 해설</summary>

**B (OCP)**. 새 동작을 기존 코드 *수정*으로 처리하는 것은 OCP 위반이며, 매번 기존 테스트를 깰 위험이 있습니다 (`oop_spec.md` §5.2). 응답 처리를 추상 핸들러/전략으로 추출하고 새 코드는 새 핸들러 클래스를 *추가*하면, 기존 scoreboard를 건드리지 않고 확장할 수 있습니다. 이는 Strategy 패턴(Module 03)과 직접 연결됩니다.

</details>
## Q4. (Apply)

driver가 특정 monitor 구체 클래스(`AxiMonitor`)에 직접 의존하지 않게 하려면 무엇을 매개로 의존해야 하는가?

- [ ] A. 또 다른 구체 monitor 클래스
- [ ] B. 추상 포트(`uvm_analysis_imp`/`uvm_analysis_port`)
- [ ] C. 전역 변수
- [ ] D. `$display` 로그

<details>
<summary>정답 / 해설</summary>

**B**. DIP는 고수준·저수준 모두 *추상*에 의존하게 합니다 (`oop_spec.md` §5.5). UVM의 analysis port가 producer(monitor)와 consumer(scoreboard)를 추상 포트로 분리하므로, 어느 쪽도 상대의 구체 타입을 몰라도 됩니다. 구체 클래스(A)에 의존하면 여전히 DIP 위반이고, 전역 변수(C)나 로그(D)는 의존성 해결과 무관합니다.

</details>
## Q5. (Analyze)

scoreboard 하나가 (1) 기능 비교, (2) coverage 수집, (3) 로그 포맷팅, (4) 레지스터 모델 접근을 모두 담당한다. 어떤 원칙을 위반하며, 가장 직접적인 부작용은?

<details>
<summary>정답 / 해설</summary>

**SRP(단일 책임 원칙) 위반**입니다 (`oop_spec.md` §5.1). 바뀌어야 할 이유가 넷(비교 로직, coverage 정책, 로그 포맷, 레지스터 맵)이므로, 어느 하나가 바뀌어도 같은 클래스를 건드려야 합니다. 가장 직접적인 부작용은 **재사용 불가** — 다른 프로젝트에 scoreboard를 가져가려 하면 불필요한 coverage·레지스터 의존이 딸려옵니다. 각 책임을 별도 컴포넌트로 분리하고 env가 합성해야 합니다.

</details>
## Q6. (Evaluate)

"OCP를 제대로 지키려면 설계 초기에 가능한 모든 확장점을 인터페이스로 열어 두어야 한다"는 주장을 평가하라.

<details>
<summary>정답 / 해설</summary>

**과도한 해석으로, 부적절**합니다. 모든 것을 추상화하면 쓰이지 않을 확장점이 복잡도만 늘려 **YAGNI를 위반**합니다 (`oop_spec.md` §6.2, Module 01 §5.1). OCP는 *예상되는 변경 축*에만 추상화를 두라는 뜻입니다 — 설계의 중심 질문은 "무엇이 가장 자주 바뀌는가"이고, 그 축에 한해 확장에 열어 두는 것이 균형점입니다. KISS/YAGNI와 OCP는 "자주 바뀌는 곳만 유연하게"라는 지점에서 만납니다.

</details>
