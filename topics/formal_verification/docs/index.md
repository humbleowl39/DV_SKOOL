# Formal Verification

> **정형 검증 마스터 코스** — SVA, JasperGold, Convergence 전략. 시뮬레이션이 못 잡는 corner case를 수학적으로 증명하는 방법론.

<div class="course-header">
  <div class="course-stats">
    <div class="stat-item"><strong>3</strong>개 모듈 + Quick Ref</div>
    <div class="stat-item"><strong>심화 (Advanced)</strong> 난이도</div>
  </div>
</div>

## 이 코스에서 얻는 것

- **Distinguish (분석)** Formal Verification과 Simulation의 본질적 차이(증명 vs 샘플)와 각 기법이 잡을 수 있는 버그 종류 구분
- **Implement (생성)** SVA(System Verilog Assertion)를 사용한 안전성·라이브니스 프로퍼티 작성
- **Apply (적용)** JasperGold App(JG-Apex/Functional/CDC/Coverage)을 시나리오에 맞게 적용
- **Diagnose (분석)** BOUNDED → PROVEN 수렴 전략 (Cut Point, Blackbox, Assume, Abstraction)
- **Critique (평가)** Vacuous Pass / Over-constraint 같은 흔한 함정 식별

## 사전 지식

이 코스는 **심화** 과정입니다.

- **SystemVerilog**: class, module, interface (IEEE 1800)
- **시뮬레이션 기반 검증 경험** (UVM 또는 directed test)
- **명제 논리 기본**: implication (`->`), 양화사 (∀, ∃) 개념
- **DUT 사양 문서 읽고 protocol 규칙을 추출하는 능력**

## 학습 모듈

<div class="course-grid">
  <a class="course-card" href="01_formal_fundamentals/">
    <div class="course-card-num">Module 01</div>
    <div class="course-card-title">Formal Fundamentals</div>
    <div class="course-card-desc">Sim vs Formal, 3가지 결과(PROVEN/BOUNDED/CEX), Induction, State Explosion</div>
  </a>
  <a class="course-card" href="02_sva/">
    <div class="course-card-num">Module 02</div>
    <div class="course-card-title">SVA</div>
    <div class="course-card-desc">SVA 구조, 시퀀스/프로퍼티, 핵심 연산자, 실무 패턴, Bind, Vacuous Pass</div>
  </a>
  <a class="course-card" href="03_jaspergold_and_strategy/">
    <div class="course-card-num">Module 03</div>
    <div class="course-card-title">JasperGold &amp; Strategy</div>
    <div class="course-card-desc">JasperGold 워크플로, Convergence 전략, Blackbox/Cut Point, Sign-off 기준</div>
  </a>
  <a class="course-card" href="04_quick_reference_card/">
    <div class="course-card-num">Module 04</div>
    <div class="course-card-title">Quick Reference Card</div>
    <div class="course-card-desc">SVA 연산자, 패턴, Convergence 순서, 면접 골든 룰</div>
  </a>
</div>

## 학습 경로

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

## 관련 자료

- 📚 [**용어집 (Glossary)**](glossary.md) — Formal 핵심 용어 ISO 11179 형식
- 📝 [**퀴즈 (Quizzes)**](quiz/index.md) — 챕터별 5문항 (Bloom mix)
- 📋 [**코스 개요 & 컨셉 맵**](_legacy_overview.md) — 학습 단위와 사용처

## 학습 팁

!!! tip "효율적 학습"
    - **Sim 사고에서 벗어나기**: Formal은 "내가 생각한 시나리오 + 모든 시나리오"가 대상. 입력을 한정하지 말고 spec rule만 코드로 옮기기
    - **PROVEN ≠ 충분한 검증**: PROVEN이라도 SVA 자체가 잘못되었거나 너무 약하면 의미 없음. Coverage + 다른 검증과 조합
    - **Vacuous Pass 의심**: SVA가 너무 쉽게 PROVEN되면 antecedent가 false인지 항상 확인

!!! warning "흔한 함정"
    - **Over-constraint**: assume이 너무 강해 실제 DUT 입력 공간을 좁힘 → false PROVEN
    - **Vacuous pass**: implication의 LHS가 false → 항상 true → 의미 없는 PROVEN
    - **Blackbox 후 sign-off**: 블랙박스된 영역의 동작을 검증한 게 아님을 명시
