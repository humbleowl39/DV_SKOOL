# SoC Integration (CCTV)

<!-- DV-SKOOL-HERO:start -->
<div class="topic-hero" data-cat="soc">
  <div class="topic-hero-mark">🏗️</div>
  <div class="topic-hero-body">
    <div class="topic-hero-title">SoC Integration (CCTV)</div>
    <p class="topic-hero-sub">Top-level 검증 환경 구축, Common Task 패턴, AI 자동화 활용.</p>
    <div class="topic-hero-stats">
      <span class="topic-stat"><span class="topic-stat-icon">📚</span><span class="topic-stat-val">3</span><span class="topic-stat-lbl">모듈</span></span>
      <span class="topic-stat"><span class="topic-stat-icon">⏱</span><span class="topic-stat-val">~1.7h</span><span class="topic-stat-lbl">예상</span></span>
      <span class="topic-stat"><span class="topic-stat-icon">🎯</span><span class="topic-stat-val">심화</span><span class="topic-stat-lbl">난이도</span></span>
    </div>
  </div>
</div>
<!-- DV-SKOOL-HERO:end -->

## 이 코스에서 얻는 것

- **Plan** SoC top-level 검증 환경 (multi-IP UVM env, virtual sequence, scoreboard) 설계
- **Apply** Common Task & CCTV (Common Task Coverage Verification) 패턴으로 재사용성 확보
- **Implement** AI 자동화 (LLM 활용) 시퀀스/coverage/디버그 보조 도입
- **Plan** TB Top + multi-Agent + RAL + multi-clock domain 통합

## 사전 지식

- [UVM](../../uvm/) (Agent, Virtual Sequence, RAL)
- [AMBA AXI](../../amba_protocols/) (인터커넥트)
- IP-level 검증 경험 1회 이상

## 🗺️ 학습 경로

<div class="concept-dag">
  <div class="concept-dag-title">개념 의존성 — 순서대로 학습 권장</div>
  <div class="concept-dag-row">
    <a class="concept-dag-node" href="01_soc_top_integration/">
      <span class="concept-dag-node-num">M01</span>
      <span class="concept-dag-node-title">SoC Top Integration</span>
    </a>
    <span class="concept-dag-arrow">→</span>
    <a class="concept-dag-node" href="02_common_task_cctv/">
      <span class="concept-dag-node-num">M02</span>
      <span class="concept-dag-node-title">Common Task & CCTV</span>
    </a>
    <span class="concept-dag-arrow">→</span>
    <a class="concept-dag-node" href="03_tb_top_and_ai/">
      <span class="concept-dag-node-num">M03</span>
      <span class="concept-dag-node-title">TB Top & AI</span>
    </a>
    <span class="concept-dag-arrow">→</span>
    <a class="concept-dag-node" href="04_quick_reference_card/">
      <span class="concept-dag-node-num">Ref</span>
      <span class="concept-dag-node-title">Quick Reference</span>
    </a>
  </div>
  <div class="concept-dag-legend">각 노드 = 모듈 (클릭하여 이동) · 화살표(→) = 선수 지식 흐름</div>
</div>

## 학습 모듈

<!-- DV-SKOOL-MODULES:start -->
<div class="module-grid">
  <a class="module-card" data-cat="soc" href="01_soc_top_integration/">
    <div class="module-num">01</div>
    <div class="module-body">
      <div class="module-title">SoC Top Integration</div>
      <div class="module-meta">
        <span class="module-time">⏱ 27분</span>
        
      </div>
    </div>
  </a>
  <a class="module-card" data-cat="soc" href="02_common_task_cctv/">
    <div class="module-num">02</div>
    <div class="module-body">
      <div class="module-title">Common Task & CCTV</div>
      <div class="module-meta">
        <span class="module-time">⏱ 28분</span>
        
      </div>
    </div>
  </a>
  <a class="module-card" data-cat="soc" href="03_tb_top_and_ai/">
    <div class="module-num">03</div>
    <div class="module-body">
      <div class="module-title">TB Top & AI Automation</div>
      <div class="module-meta">
        <span class="module-time">⏱ 35분</span>
        
      </div>
    </div>
  </a>
  <a class="module-card" data-cat="soc" href="04_quick_reference_card/">
    <div class="module-num is-special" title="Quick Reference">★</div>
    <div class="module-body">
      <div class="module-title">Quick Reference Card</div>
      <div class="module-meta">
        <span class="module-time">⏱ 10분</span>
        <span class="module-tag">Quick Ref</span>
      </div>
    </div>
  </a>
</div>
<!-- DV-SKOOL-MODULES:end -->

## 학습 경로

<div class="path-chain">
  <div class="path-pill tier-core">
    <div class="pill-num">M01</div>
    <div class="pill-title">SoC Top Integration</div>
  </div>
  <div class="path-arrow">▶</div>
  <div class="path-pill tier-adv">
    <div class="pill-num">M02</div>
    <div class="pill-title">Common Task &amp; CCTV</div>
  </div>
  <div class="path-arrow">▶</div>
  <div class="path-pill tier-adv">
    <div class="pill-num">M03</div>
    <div class="pill-title">TB Top &amp; AI</div>
  </div>
  <div class="path-arrow">▶</div>
  <div class="path-pill tier-ref">
    <div class="pill-num">M04</div>
    <div class="pill-title">Quick Ref</div>
  </div>
</div>

## 관련 자료

- 📚 [**용어집**](glossary.md)
- 📝 [**퀴즈**](quiz/index.md)
- 📋 [**코스 개요**](_legacy_overview.md)

<!-- DV-SKOOL-RELATED-TOPICS:start -->

## 관련 토픽

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
  <a class="course-card" href="https://humbleowl39.github.io/DV_SKOOL/mmu/">
    <div class="course-card-num">🧭 관련</div>
    <div class="course-card-title">MMU</div>
    <div class="course-card-desc">페이지 테이블, TLB, IOMMU/SMMU</div>
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
