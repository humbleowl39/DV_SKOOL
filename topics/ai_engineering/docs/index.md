# AI Engineering

<!-- DV-SKOOL-HERO:start -->
<div class="topic-hero" data-cat="applied">
  <div class="topic-hero-mark">🤖</div>
  <div class="topic-hero-body">
    <div class="topic-hero-title">AI Engineering</div>
    <p class="topic-hero-sub">LLM, 프롬프트 엔지니어링, RAG, agent, DV 활용</p>
  </div>
</div>
<!-- DV-SKOOL-HERO:end -->

<!-- DV-SKOOL-TOC:start -->
<div class="page-toc">
  <span class="page-toc-label">목차</span>
  <a class="page-toc-link" href="#사전-지식">📋 사전 지식</a>
  <a class="page-toc-link" href="#개념-맵">🗺️ 개념 맵</a>
  <a class="page-toc-link" href="#학습-모듈">📚 학습 모듈</a>
  <a class="page-toc-link" href="#관련-자료">📖 관련 자료</a>
  <a class="page-toc-link" href="#개요-컨셉-맵">🗺️ 개요 & 컨셉 맵</a>
</div>
<!-- DV-SKOOL-TOC:end -->

## 📋 사전 지식
Python, 머신러닝/딥러닝 개요, API 호출 경험

## 🗺️ 개념 맵
<div class="concept-dag dag-long">
  <div class="concept-dag-title">개념 의존성 — 순서대로 학습 권장</div>
  <div class="concept-dag-row">
    <a class="concept-dag-node" href="01_llm_fundamentals/">
      <span class="concept-dag-node-num">M01</span>
      <span class="concept-dag-node-title">LLM Fundamentals</span>
    </a>
    <span class="concept-dag-arrow">→</span>
    <a class="concept-dag-node" href="02_prompt_engineering/">
      <span class="concept-dag-node-num">M02</span>
      <span class="concept-dag-node-title">Prompt Engineering</span>
    </a>
    <span class="concept-dag-arrow">→</span>
    <a class="concept-dag-node" href="03_embedding_vectordb/">
      <span class="concept-dag-node-num">M03</span>
      <span class="concept-dag-node-title">Embedding & Vector DB</span>
    </a>
    <span class="concept-dag-arrow">→</span>
    <a class="concept-dag-node" href="04_rag/">
      <span class="concept-dag-node-num">M04</span>
      <span class="concept-dag-node-title">RAG</span>
    </a>
  </div>
  <div class="concept-dag-row">
    <span class="concept-dag-arrow">↪</span>
    <a class="concept-dag-node" href="05_agent_architecture/">
      <span class="concept-dag-node-num">M05</span>
      <span class="concept-dag-node-title">Agent Architecture</span>
    </a>
    <span class="concept-dag-arrow">→</span>
    <a class="concept-dag-node" href="06_strategy_selection/">
      <span class="concept-dag-node-num">M06</span>
      <span class="concept-dag-node-title">Strategy Selection</span>
    </a>
    <span class="concept-dag-arrow">→</span>
    <a class="concept-dag-node" href="07_dv_application/">
      <span class="concept-dag-node-num">M07</span>
      <span class="concept-dag-node-title">DV Application</span>
    </a>
    <span class="concept-dag-arrow">→</span>
    <a class="concept-dag-node" href="08_quick_reference_card/">
      <span class="concept-dag-node-num">Ref</span>
      <span class="concept-dag-node-title">Quick Reference</span>
    </a>
  </div>
  <div class="concept-dag-legend">각 노드 = 모듈 (클릭하여 이동) · 화살표(→) = 선수 지식 흐름</div>
</div>

## 📚 학습 모듈
<!-- DV-SKOOL-MODULES:start -->
<div class="module-grid">
  <a class="module-card" data-cat="applied" href="01_llm_fundamentals/">
    <div class="module-num">01</div>
    <div class="module-body">
      <div class="module-title">LLM Fundamentals</div>
    </div>
  </a>
  <a class="module-card" data-cat="applied" href="02_prompt_engineering/">
    <div class="module-num">02</div>
    <div class="module-body">
      <div class="module-title">Prompt Engineering & In-Context Learning</div>
    </div>
  </a>
  <a class="module-card" data-cat="applied" href="03_embedding_vectordb/">
    <div class="module-num">03</div>
    <div class="module-body">
      <div class="module-title">Embedding & Vector DB</div>
    </div>
  </a>
  <a class="module-card" data-cat="applied" href="04_rag/">
    <div class="module-num">04</div>
    <div class="module-body">
      <div class="module-title">RAG (Retrieval-Augmented Generation)</div>
    </div>
  </a>
  <a class="module-card" data-cat="applied" href="05_agent_architecture/">
    <div class="module-num">05</div>
    <div class="module-body">
      <div class="module-title">Agent Architecture</div>
    </div>
  </a>
  <a class="module-card" data-cat="applied" href="06_strategy_selection/">
    <div class="module-num">06</div>
    <div class="module-body">
      <div class="module-title">Strategy Selection (Prompt vs RAG vs Fine-tune)</div>
    </div>
  </a>
  <a class="module-card" data-cat="applied" href="07_dv_application/">
    <div class="module-num">07</div>
    <div class="module-body">
      <div class="module-title">DV/EDA Application</div>
    </div>
  </a>
  <a class="module-card" data-cat="applied" href="08_quick_reference_card/">
    <div class="module-num is-special" title="Quick Reference">★</div>
    <div class="module-body">
      <div class="module-title">Quick Reference Card</div>
    </div>
  </a>
</div>
<!-- DV-SKOOL-MODULES:end -->


## 📖 관련 자료
- 📚 [**용어집 (Glossary)**](glossary.md) — 핵심 용어 정의 및 교차 참조
- 📝 [**퀴즈 (Quizzes)**](quiz/index.md) — 챕터별 이해도 점검

## 🗺️ 개요 & 컨셉 맵
코스 전체의 컨셉 맵과 깊이 있는 개요는 다음 문서를 참고하세요:

→ [**코스 개요 & 컨셉 맵**](_legacy_overview.md)


<!-- DV-SKOOL-RELATED-TOPICS:start -->

## 🔗 관련 토픽
<div class="course-grid">
  <a class="course-card" href="https://humbleowl39.github.io/DV_SKOOL/bigtech_algorithm/">
    <div class="course-card-num">📐 관련</div>
    <div class="course-card-title">BigTech Algorithm</div>
    <div class="course-card-desc">Big-O, 자료구조, 알고리즘</div>
  </a>
  <a class="course-card" href="https://humbleowl39.github.io/DV_SKOOL/" style="border-style:dashed;">
    <div class="course-card-num">🏠 HOME</div>
    <div class="course-card-title">DV SKOOL 홈</div>
    <div class="course-card-desc">전체 토픽 / 학습 경로 보기</div>
  </a>
</div>

<!-- DV-SKOOL-RELATED-TOPICS:end -->


--8<-- "abbreviations.md"
