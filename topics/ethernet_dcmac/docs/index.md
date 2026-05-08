# Ethernet DCMAC

<!-- DV-SKOOL-HERO:start -->
<div class="topic-hero" data-cat="network">
  <div class="topic-hero-mark">🌐</div>
  <div class="topic-hero-body">
    <div class="topic-hero-title">Ethernet DCMAC</div>
    <p class="topic-hero-sub">이더넷 기본부터 100/400G DCMAC 검증까지</p>
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

## 🎯 학습 목표
- **Diagram** Ethernet 프레임 구조와 OSI 1-2 layer 매핑
- **Distinguish** GbE / 10GbE / 100GbE / 400GbE 차이와 DCMAC의 위치
- **Apply** PCS / FEC / MAC layer의 책임 분리 및 검증 시나리오
- **Plan** DCMAC DV 환경 (traffic generator, packet checker, FEC injection)

## 📋 사전 지식
- OSI 모델 (특히 L1/L2)
- MAC vs PHY 분리 개념
- 패킷 / 프레임 / 패딩 같은 네트워킹 기본 용어

## 🗺️ 개념 맵
<div class="concept-dag">
  <div class="concept-dag-title">개념 의존성 — 순서대로 학습 권장</div>
  <div class="concept-dag-row">
    <a class="concept-dag-node" href="01_ethernet_fundamentals/">
      <span class="concept-dag-node-num">M01</span>
      <span class="concept-dag-node-title">Ethernet Fundamentals</span>
    </a>
    <span class="concept-dag-arrow">→</span>
    <a class="concept-dag-node" href="02_dcmac_architecture/">
      <span class="concept-dag-node-num">M02</span>
      <span class="concept-dag-node-title">DCMAC Architecture</span>
    </a>
    <span class="concept-dag-arrow">→</span>
    <a class="concept-dag-node" href="03_dcmac_dv_methodology/">
      <span class="concept-dag-node-num">M03</span>
      <span class="concept-dag-node-title">DV Methodology</span>
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
  <a class="module-card" data-cat="network" href="01_ethernet_fundamentals/">
    <div class="module-num">01</div>
    <div class="module-body">
      <div class="module-title">Ethernet Fundamentals</div>
    </div>
  </a>
  <a class="module-card" data-cat="network" href="02_dcmac_architecture/">
    <div class="module-num">02</div>
    <div class="module-body">
      <div class="module-title">DCMAC Architecture</div>
    </div>
  </a>
  <a class="module-card" data-cat="network" href="03_dcmac_dv_methodology/">
    <div class="module-num">03</div>
    <div class="module-body">
      <div class="module-title">DCMAC DV Methodology</div>
    </div>
  </a>
  <a class="module-card" data-cat="network" href="04_quick_reference_card/">
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
    <div class="pill-title">Ethernet Fundamentals</div>
  </div>
  <div class="path-arrow">▶</div>
  <div class="path-pill tier-core">
    <div class="pill-num">M02</div>
    <div class="pill-title">DCMAC Architecture</div>
  </div>
  <div class="path-arrow">▶</div>
  <div class="path-pill tier-adv">
    <div class="pill-num">M03</div>
    <div class="pill-title">DV</div>
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
  <a class="course-card" href="https://humbleowl39.github.io/DV_SKOOL/toe/">
    <div class="course-card-num">📡 관련</div>
    <div class="course-card-title">TOE</div>
    <div class="course-card-desc">TCP/IP Offload Engine</div>
  </a>
  <a class="course-card" href="https://humbleowl39.github.io/DV_SKOOL/rdma/">
    <div class="course-card-num">⚡ 관련</div>
    <div class="course-card-title">RDMA</div>
    <div class="course-card-desc">InfiniBand & RoCEv2, QP/MR</div>
  </a>
  <a class="course-card" href="https://humbleowl39.github.io/DV_SKOOL/amba_protocols/">
    <div class="course-card-num">🔄 관련</div>
    <div class="course-card-title">AMBA Protocols</div>
    <div class="course-card-desc">APB/AHB/AXI — 표준 버스 프로토콜</div>
  </a>
  <a class="course-card" href="https://humbleowl39.github.io/DV_SKOOL/" style="border-style:dashed;">
    <div class="course-card-num">🏠 HOME</div>
    <div class="course-card-title">DV SKOOL 홈</div>
    <div class="course-card-desc">전체 토픽 / 학습 경로 보기</div>
  </a>
</div>

<!-- DV-SKOOL-RELATED-TOPICS:end -->


--8<-- "abbreviations.md"
