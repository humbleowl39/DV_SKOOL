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
    - **Sim 사고에서 벗어나기**: Formal은 "내가 생각한 시나리오 + 모든 시나리오"가 대상. 입력을 한정하지 말고 spec rule만 코드로 옮기기
    - **PROVEN ≠ 충분한 검증**: PROVEN이라도 SVA 자체가 잘못되었거나 너무 약하면 의미 없음. Coverage + 다른 검증과 조합
    - **Vacuous Pass 의심**: SVA가 너무 쉽게 PROVEN되면 antecedent가 false인지 항상 확인

!!! warning "흔한 함정"
    - **Over-constraint**: assume이 너무 강해 실제 DUT 입력 공간을 좁힘 → false PROVEN
    - **Vacuous pass**: implication의 LHS가 false → 항상 true → 의미 없는 PROVEN
    - **Blackbox 후 sign-off**: 블랙박스된 영역의 동작을 검증한 게 아님을 명시

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
