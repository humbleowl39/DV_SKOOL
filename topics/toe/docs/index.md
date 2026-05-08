# TOE (TCP/IP Offload Engine)

<!-- DV-SKOOL-HERO:start -->
<div class="topic-hero" data-cat="network">
  <div class="topic-hero-mark">📡</div>
  <div class="topic-hero-body">
    <div class="topic-hero-title">TOE (TCP/IP Offload Engine)</div>
    <p class="topic-hero-sub">TCP/IP Offload Engine 아키텍처와 DV</p>
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
- **Trace** TCP/IP 스택 처리를 host SW vs TOE HW로 비교 추적
- **Diagram** TOE의 connection state machine + segment processing pipeline
- **Apply** TX/RX path, ARP, checksum offload, RSS 시나리오 매핑
- **Plan** TOE DV 환경 (packet generator, connection model, error injection)

## 📋 사전 지식
- TCP/IP 스택 (3-way handshake, sliding window, congestion control 기본)
- NIC 동작 원리
- AMBA AXI / AXI-Stream

## 🗺️ 개념 맵
<div class="concept-dag">
  <div class="concept-dag-title">개념 의존성 — 순서대로 학습 권장</div>
  <div class="concept-dag-row">
    <a class="concept-dag-node" href="01_tcp_ip_and_toe_concept/">
      <span class="concept-dag-node-num">M01</span>
      <span class="concept-dag-node-title">TCP/IP & TOE</span>
    </a>
    <span class="concept-dag-arrow">→</span>
    <a class="concept-dag-node" href="02_toe_architecture/">
      <span class="concept-dag-node-num">M02</span>
      <span class="concept-dag-node-title">TOE Architecture</span>
    </a>
    <span class="concept-dag-arrow">→</span>
    <a class="concept-dag-node" href="03_toe_key_functions/">
      <span class="concept-dag-node-num">M03</span>
      <span class="concept-dag-node-title">Key Functions</span>
    </a>
    <span class="concept-dag-arrow">→</span>
    <a class="concept-dag-node" href="04_toe_dv_methodology/">
      <span class="concept-dag-node-num">M04</span>
      <span class="concept-dag-node-title">DV Methodology</span>
    </a>
  </div>
  <div class="concept-dag-row">
    <span class="concept-dag-arrow">↪</span>
    <a class="concept-dag-node" href="05_quick_reference_card/">
      <span class="concept-dag-node-num">Ref</span>
      <span class="concept-dag-node-title">Quick Reference</span>
    </a>
  </div>
  <div class="concept-dag-legend">각 노드 = 모듈 (클릭하여 이동) · 화살표(→) = 선수 지식 흐름</div>
</div>

## 📚 학습 모듈
<!-- DV-SKOOL-MODULES:start -->
<div class="module-grid">
  <a class="module-card" data-cat="network" href="01_tcp_ip_and_toe_concept/">
    <div class="module-num">01</div>
    <div class="module-body">
      <div class="module-title">TCP/IP & TOE Concept</div>
    </div>
  </a>
  <a class="module-card" data-cat="network" href="02_toe_architecture/">
    <div class="module-num">02</div>
    <div class="module-body">
      <div class="module-title">TOE Architecture</div>
    </div>
  </a>
  <a class="module-card" data-cat="network" href="03_toe_key_functions/">
    <div class="module-num">03</div>
    <div class="module-body">
      <div class="module-title">TOE Key Functions</div>
    </div>
  </a>
  <a class="module-card" data-cat="network" href="04_toe_dv_methodology/">
    <div class="module-num">04</div>
    <div class="module-body">
      <div class="module-title">TOE DV Methodology</div>
    </div>
  </a>
  <a class="module-card" data-cat="network" href="05_quick_reference_card/">
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
    <div class="pill-title">Concept</div>
  </div>
  <div class="path-arrow">▶</div>
  <div class="path-pill tier-core">
    <div class="pill-num">M02</div>
    <div class="pill-title">Architecture</div>
  </div>
  <div class="path-arrow">▶</div>
  <div class="path-pill tier-adv">
    <div class="pill-num">M03</div>
    <div class="pill-title">Key Functions</div>
  </div>
  <div class="path-arrow">▶</div>
  <div class="path-pill tier-adv">
    <div class="pill-num">M04</div>
    <div class="pill-title">DV</div>
  </div>
  <div class="path-arrow">▶</div>
  <div class="path-pill tier-ref">
    <div class="pill-num">M05</div>
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
  <a class="course-card" href="https://humbleowl39.github.io/DV_SKOOL/ethernet_dcmac/">
    <div class="course-card-num">🌐 관련</div>
    <div class="course-card-title">Ethernet DCMAC</div>
    <div class="course-card-desc">이더넷 MAC + DCMAC DV</div>
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
