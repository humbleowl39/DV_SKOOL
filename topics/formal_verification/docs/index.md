# Formal Verification

<!-- DV-SKOOL-HERO:start -->
<div class="topic-hero" data-cat="core">
  <div class="topic-hero-mark">✅</div>
  <div class="topic-hero-body">
    <div class="topic-hero-title">Formal Verification</div>
    <p class="topic-hero-sub">Formal — SVA, JasperGold, 정형 증명 전략</p>
  </div>
</div>
<!-- DV-SKOOL-HERO:end -->

<!-- DV-SKOOL-TOC:start -->
<div class="page-toc">
  <span class="page-toc-label">목차</span>
  <a class="page-toc-link" href="#학습-목표">🎯 학습 목표</a>
  <a class="page-toc-link" href="#사전-지식">📋 사전 지식</a>
  <a class="page-toc-link" href="#개념-맵">🗺️ 개념 맵</a>
  <a class="page-toc-link" href="#학습-모듈">📚 학습 모듈</a>
  <a class="page-toc-link" href="#모듈-흐름">📊 모듈 흐름</a>
  <a class="page-toc-link" href="#관련-자료">📖 관련 자료</a>
  <a class="page-toc-link" href="#학습-팁">💡 학습 팁</a>
</div>
<!-- DV-SKOOL-TOC:end -->

시뮬레이션 기반 검증은 "설계자가 생각한 시나리오"만 테스트한다. 아무리 많은 랜덤 시드를 돌려도, 사람이 예상하지 못한 입력 조합 앞에서는 버그가 숨어 있을 수 있다. Formal Verification은 이 한계를 수학적으로 극복한다. 가능한 모든 입력과 상태를 자동으로 탐색해, "이 조건이 절대 위반되지 않는다"는 PROVEN을 얻거나, 위반을 일으키는 반례(CEX)를 구체적으로 제시한다. 이 과목을 배우지 않으면 protocol deadlock, arbiter starvation, reset sequence 오류처럼 특정 입력 패턴에서만 재현되는 간헐적 버그를 sign-off 후까지 놓칠 수 있다. 반대로 Formal을 익히면 FSM, 프로토콜 핸드셰이크, 권한 로직처럼 명세가 명확한 블록을 시뮬레이션 없이 수학적으로 증명할 수 있어, 검증 커버리지의 빈틈 없는 마감이 가능해진다.

## 🎯 학습 목표
- **Distinguish (분석)** Formal Verification과 Simulation의 본질적 차이(증명 vs 샘플)와 각 기법이 잡을 수 있는 버그 종류 구분
- **Implement (생성)** SVA(System Verilog Assertion)를 사용한 안전성·라이브니스 프로퍼티 작성
- **Apply (적용)** JasperGold App(JG-Apex/Functional/CDC/Coverage)을 시나리오에 맞게 적용
- **Diagnose (분석)** BOUNDED → PROVEN 수렴 전략 (Cut Point, Blackbox, Assume, Abstraction)
- **Critique (평가)** Vacuous Pass / Over-constraint 같은 흔한 함정 식별

## 📋 사전 지식
다음 항목을 알고 있어야 본문이 매끄럽게 읽힙니다:

- **SystemVerilog**: class, module, interface (IEEE 1800)
- **시뮬레이션 기반 검증 경험** (UVM 또는 directed test)
- **명제 논리 기본**: implication (`->`), 양화사 (∀, ∃) 개념
- **DUT 사양 문서 읽고 protocol 규칙을 추출하는 능력**

## 🗺️ 개념 맵
<div class="concept-dag">
  <div class="concept-dag-title">개념 의존성 — 순서대로 학습 권장</div>
  <div class="concept-dag-row">
    <a class="concept-dag-node" href="01_formal_fundamentals/">
      <span class="concept-dag-node-num">M01</span>
      <span class="concept-dag-node-title">Formal Fundamentals</span>
    </a>
    <span class="concept-dag-arrow">→</span>
    <a class="concept-dag-node" href="02_sva/">
      <span class="concept-dag-node-num">M02</span>
      <span class="concept-dag-node-title">SVA</span>
    </a>
    <span class="concept-dag-arrow">→</span>
    <a class="concept-dag-node" href="03_jaspergold_and_strategy/">
      <span class="concept-dag-node-num">M03</span>
      <span class="concept-dag-node-title">JasperGold & Strategy</span>
    </a>
    <span class="concept-dag-arrow">→</span>
    <a class="concept-dag-node" href="04_quick_reference_card/">
      <span class="concept-dag-node-num">Ref</span>
      <span class="concept-dag-node-title">Quick Reference</span>
    </a>
  </div>
  <div class="concept-dag-legend">각 노드 = 모듈 (클릭하여 이동) · 화살표(→) = 선수 지식 흐름</div>
</div>

## 📚 학습 모듈
<!-- DV-SKOOL-MODULES:start -->
<div class="module-grid">
  <a class="module-card" data-cat="core" href="01_formal_fundamentals/">
    <div class="module-num">01</div>
    <div class="module-body">
      <div class="module-title">Unit 1: Formal Verification 기본 개념</div>
    </div>
  </a>
  <a class="module-card" data-cat="core" href="02_sva/">
    <div class="module-num">02</div>
    <div class="module-body">
      <div class="module-title">SVA (SystemVerilog Assertions)</div>
    </div>
  </a>
  <a class="module-card" data-cat="core" href="03_jaspergold_and_strategy/">
    <div class="module-num">03</div>
    <div class="module-body">
      <div class="module-title">JasperGold & DV Strategy</div>
    </div>
  </a>
  <a class="module-card" data-cat="core" href="04_quick_reference_card/">
    <div class="module-num is-special" title="Quick Reference">★</div>
    <div class="module-body">
      <div class="module-title">Quick Reference Card</div>
    </div>
  </a>
</div>
<!-- DV-SKOOL-MODULES:end -->

## 📊 모듈 흐름
<div class="path-chain">
  <div class="path-pill tier-core">
    <div class="pill-num">M01</div>
    <div class="pill-title">Fundamentals</div>
  </div>
  <div class="path-arrow">▶</div>
  <div class="path-pill tier-core">
    <div class="pill-num">M02</div>
    <div class="pill-title">SVA</div>
  </div>
  <div class="path-arrow">▶</div>
  <div class="path-pill tier-adv">
    <div class="pill-num">M03</div>
    <div class="pill-title">JasperGold &amp; Strategy</div>
  </div>
  <div class="path-arrow">▶</div>
  <div class="path-pill tier-ref">
    <div class="pill-num">M04</div>
    <div class="pill-title">Quick Ref</div>
  </div>
</div>

## 📖 관련 자료
- 📚 [**용어집 (Glossary)**](glossary.md) — Formal 핵심 용어 ISO 11179 형식
- 📝 [**퀴즈 (Quizzes)**](quiz/index.md) — 챕터별 5문항 (Bloom mix)
- 📋 [**코스 개요 & 컨셉 맵**](_legacy_overview.md) — 학습 단위와 사용처

## 💡 학습 팁
!!! tip "효율적 학습"
    Formal을 처음 배울 때 가장 큰 전환점은 "시뮬레이션 사고"를 내려놓는 것이다. 시뮬레이션에서는 입력을 설계자가 정의하지만, Formal에서는 solver가 모든 가능한 입력을 탐색하므로 assume을 통해 환경 제약을 명확히 정의하는 역할로 전환해야 한다. 또한 PROVEN 결과가 나왔다고 검증이 충분하다고 결론 짓지 말고, SVA 자체가 spec을 정확히 표현했는지, cover가 모두 COVERED인지를 반드시 교차 검토해야 한다. SVA가 너무 쉽게 PROVEN된다면 antecedent(전제)가 실제로 활성화된 적이 없는 vacuous pass일 가능성을 먼저 의심하라.

!!! warning "흔한 함정"
    Over-constraint는 assume을 너무 강하게 설정해 실제 DUT가 받을 수 있는 입력 공간을 지나치게 좁히는 실수로, 이 상태에서 PROVEN을 받으면 실제 환경에서는 존재하는 버그를 놓친다. Vacuous pass는 implication의 antecedent가 단 한 번도 true가 되지 않아 검증 조건 자체에 진입하지 못한 채 PASS로 처리되는 패턴이며, 짝지은 cover가 UNCOVERED인지 확인해야만 탐지된다. Blackbox 처리 후 sign-off할 때는 해당 영역의 동작이 검증 범위에서 제외되었음을 명시적으로 기록해야 하며, 그 영역이 property에 영향을 줄 수 있는지 COI(Cone of Influence) 분석을 통해 확인해야 한다.

<!-- DV-SKOOL-RELATED-TOPICS:start -->

## 🔗 관련 토픽
<div class="course-grid">
  <a class="course-card" href="https://humbleowl39.github.io/DV_SKOOL/uvm/">
    <div class="course-card-num">🧪 관련</div>
    <div class="course-card-title">UVM</div>
    <div class="course-card-desc">검증 방법론, phase, agent, sequence</div>
  </a>
  <a class="course-card" href="https://humbleowl39.github.io/DV_SKOOL/amba_protocols/">
    <div class="course-card-num">🔄 관련</div>
    <div class="course-card-title">AMBA Protocols</div>
    <div class="course-card-desc">APB/AHB/AXI — 표준 버스 프로토콜</div>
  </a>
  <a class="course-card" href="https://humbleowl39.github.io/DV_SKOOL/soc_secure_boot/">
    <div class="course-card-num">🔐 관련</div>
    <div class="course-card-title">SoC Secure Boot</div>
    <div class="course-card-desc">RoT, chain of trust, BootROM DV</div>
  </a>
  <a class="course-card" href="https://humbleowl39.github.io/DV_SKOOL/" style="border-style:dashed;">
    <div class="course-card-num">🏠 HOME</div>
    <div class="course-card-title">DV SKOOL 홈</div>
    <div class="course-card-desc">전체 토픽 / 학습 경로 보기</div>
  </a>
</div>

<!-- DV-SKOOL-RELATED-TOPICS:end -->


--8<-- "abbreviations.md"
