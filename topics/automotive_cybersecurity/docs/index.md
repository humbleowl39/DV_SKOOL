# Automotive Cybersecurity

<!-- DV-SKOOL-HERO:start -->
<div class="topic-hero" data-cat="soc">
  <div class="topic-hero-mark">🚗</div>
  <div class="topic-hero-body">
    <div class="topic-hero-title">Automotive Cybersecurity</div>
    <p class="topic-hero-sub">CAN bus부터 자율주행 보안까지, 차량 보안의 모든 것.</p>
    <div class="topic-hero-stats">
      <span class="topic-stat"><span class="topic-stat-icon">📚</span><span class="topic-stat-val">4</span><span class="topic-stat-lbl">모듈</span></span>
      <span class="topic-stat"><span class="topic-stat-icon">⏱</span><span class="topic-stat-val">~2.1h</span><span class="topic-stat-lbl">예상</span></span>
      <span class="topic-stat"><span class="topic-stat-icon">🎯</span><span class="topic-stat-val">중급</span><span class="topic-stat-lbl">난이도</span></span>
    </div>
  </div>
</div>
<!-- DV-SKOOL-HERO:end -->

## 이 코스에서 얻는 것

- **Diagram** CAN bus 동작과 보안 한계
- **Apply** Automotive SoC 보안 (HSM, secure boot, OTA update)
- **Analyze** Tesla FSD jailbreak 사례에서 배우는 보안 약점
- **Plan** Attack surface map과 layered defense 전략

## 사전 지식

- 임베디드 시스템 기본
- 네트워크 / 보안 일반 ([SoC Secure Boot](../../soc_secure_boot/) 참고)

## 🗺️ 학습 경로

<div class="concept-dag">
  <div class="concept-dag-title">개념 의존성 — 순서대로 학습 권장</div>
  <div class="concept-dag-row">
    <a class="concept-dag-node" href="01_can_bus_fundamentals/">
      <span class="concept-dag-node-num">M01</span>
      <span class="concept-dag-node-title">CAN Bus</span>
    </a>
    <span class="concept-dag-arrow">→</span>
    <a class="concept-dag-node" href="02_automotive_soc_security/">
      <span class="concept-dag-node-num">M02</span>
      <span class="concept-dag-node-title">Automotive SoC Security</span>
    </a>
    <span class="concept-dag-arrow">→</span>
    <a class="concept-dag-node" href="03_tesla_fsd_case_study/">
      <span class="concept-dag-node-num">M03</span>
      <span class="concept-dag-node-title">Tesla FSD Case</span>
    </a>
    <span class="concept-dag-arrow">→</span>
    <a class="concept-dag-node" href="04_attack_surface_and_defense/">
      <span class="concept-dag-node-num">M04</span>
      <span class="concept-dag-node-title">Attack & Defense</span>
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

## 학습 모듈

<!-- DV-SKOOL-MODULES:start -->
<div class="module-grid">
  <a class="module-card" data-cat="soc" href="01_can_bus_fundamentals/">
    <div class="module-num">01</div>
    <div class="module-body">
      <div class="module-title">CAN Bus Fundamentals</div>
      <div class="module-meta">
        <span class="module-time">⏱ 22분</span>
        
      </div>
    </div>
  </a>
  <a class="module-card" data-cat="soc" href="02_automotive_soc_security/">
    <div class="module-num">02</div>
    <div class="module-body">
      <div class="module-title">Automotive SoC Security</div>
      <div class="module-meta">
        <span class="module-time">⏱ 30분</span>
        
      </div>
    </div>
  </a>
  <a class="module-card" data-cat="soc" href="03_tesla_fsd_case_study/">
    <div class="module-num">03</div>
    <div class="module-body">
      <div class="module-title">Tesla FSD Case Study</div>
      <div class="module-meta">
        <span class="module-time">⏱ 24분</span>
        
      </div>
    </div>
  </a>
  <a class="module-card" data-cat="soc" href="04_attack_surface_and_defense/">
    <div class="module-num">04</div>
    <div class="module-body">
      <div class="module-title">Attack Surface & Defense</div>
      <div class="module-meta">
        <span class="module-time">⏱ 32분</span>
        
      </div>
    </div>
  </a>
  <a class="module-card" data-cat="soc" href="05_quick_reference_card/">
    <div class="module-num is-special" title="Quick Reference">★</div>
    <div class="module-body">
      <div class="module-title">Quick Reference Card</div>
      <div class="module-meta">
        <span class="module-time">⏱ 17분</span>
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
    <div class="pill-title">CAN Bus</div>
  </div>
  <div class="path-arrow">▶</div>
  <div class="path-pill tier-core">
    <div class="pill-num">M02</div>
    <div class="pill-title">SoC Security</div>
  </div>
  <div class="path-arrow">▶</div>
  <div class="path-pill tier-adv">
    <div class="pill-num">M03</div>
    <div class="pill-title">Tesla Case</div>
  </div>
  <div class="path-arrow">▶</div>
  <div class="path-pill tier-adv">
    <div class="pill-num">M04</div>
    <div class="pill-title">Attack &amp; Defense</div>
  </div>
  <div class="path-arrow">▶</div>
  <div class="path-pill tier-ref">
    <div class="pill-num">M05</div>
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
  <a class="course-card" href="https://humbleowl39.github.io/DV_SKOOL/arm_security/">
    <div class="course-card-num">🛡️ 관련</div>
    <div class="course-card-title">ARM Security</div>
    <div class="course-card-desc">Exception level, TrustZone, TEE</div>
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
