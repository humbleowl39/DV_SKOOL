# SoC Integration (CCTV)

<!-- DV-SKOOL-HERO:start -->
<div class="topic-hero" data-cat="soc">
  <div class="topic-hero-mark">🏗️</div>
  <div class="topic-hero-body">
    <div class="topic-hero-title">SoC Integration (CCTV)</div>
    <p class="topic-hero-sub">SoC top integration, 공통 task, TB top, AI 활용</p>
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
</div>
<!-- DV-SKOOL-TOC:end -->

## 왜 이 토픽을 배워야 하는가

IP-level 검증을 아무리 완벽하게 마쳐도, 수십 개의 IP를 하나의 SoC에 통합하는 순간 새로운 결함이 등장한다. 신호가 잘못 연결되거나, 서로 다른 clock domain 간 metastability가 발생하거나, 인터럽트가 잘못된 컨트롤러로 라우팅되는 문제는 각 IP의 독립 검증 환경에서는 보이지 않는다. 이 토픽을 배우지 않으면 SoC 수준에서만 드러나는 이 결함 카테고리들을 체계적으로 커버할 방법이 없고, 어떤 IP에 어떤 공통 시나리오가 적용되었는지를 추적하는 수단도 없어서 검증 완료 기준을 명확히 정의하기 어려워진다.

이 토픽은 그 공백을 채우기 위한 두 가지 핵심을 다룬다. 첫째, SoC top-level에서만 수행할 수 있는 검증의 범위와 기법을 이해한다. 둘째, CCTV(Common Task Coverage Verification) 방법론을 통해 SoC 내 모든 IP에 공통 시나리오가 빠짐없이 적용되었는지를 2차원 매트릭스로 추적하고, 그 결과를 sign-off 기준으로 활용하는 방법을 익힌다.

---

## 🎯 학습 목표
- **Plan** SoC top-level 검증 환경 (multi-IP UVM env, virtual sequence, scoreboard) 설계
- **Apply** Common Task & CCTV (Common Task Coverage Verification) 패턴으로 재사용성 확보
- **Implement** AI 자동화 (LLM 활용) 시퀀스/coverage/디버그 보조 도입
- **Plan** TB Top + multi-Agent + RAL + multi-clock domain 통합

## 📋 사전 지식
- [UVM](../../uvm/) (Agent, Virtual Sequence, RAL)
- [AMBA AXI](../../amba_protocols/) (인터커넥트)
- IP-level 검증 경험 1회 이상

## 🗺️ 개념 맵
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

## 📚 학습 모듈
<!-- DV-SKOOL-MODULES:start -->
<div class="module-grid">
  <a class="module-card" data-cat="soc" href="01_soc_top_integration/">
    <div class="module-num">01</div>
    <div class="module-body">
      <div class="module-title">SoC Top Integration</div>
    </div>
  </a>
  <a class="module-card" data-cat="soc" href="02_common_task_cctv/">
    <div class="module-num">02</div>
    <div class="module-body">
      <div class="module-title">Common Task & CCTV</div>
    </div>
  </a>
  <a class="module-card" data-cat="soc" href="03_tb_top_and_ai/">
    <div class="module-num">03</div>
    <div class="module-body">
      <div class="module-title">TB Top & AI Automation</div>
    </div>
  </a>
  <a class="module-card" data-cat="soc" href="04_quick_reference_card/">
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

## 📖 관련 자료
- 📚 [**용어집**](glossary.md)
- 📝 [**퀴즈**](quiz/index.md)
- 📋 [**코스 개요**](_legacy_overview.md)

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


--8<-- "abbreviations.md"
