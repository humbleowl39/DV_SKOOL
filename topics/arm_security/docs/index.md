# ARM Security

<!-- DV-SKOOL-HERO:start -->
<div class="topic-hero" data-cat="soc">
  <div class="topic-hero-mark">🛡️</div>
  <div class="topic-hero-body">
    <div class="topic-hero-title">ARM Security</div>
    <p class="topic-hero-sub">Exception Level, TrustZone, secure enclave, TEE</p>
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
- **Diagram** ARMv8 4-level Exception Level (EL0-EL3) 구조와 TrustZone 격리
- **Trace** Secure / Non-secure World 전환 흐름과 SMC instruction
- **Apply** Secure Enclave (Apple SEP, Samsung Knox) 및 TEE 계층의 격리 모델
- **Plan** Secure Boot와 ARM Security 연계 (BL31, EL3 secure monitor)

## 📋 사전 지식
- ARM ISA 기본 (ARMv8 architecture overview)
- 권한 / 격리 / 가상 메모리 일반 ([MMU 코스](../../mmu/) 참고)
- [Secure Boot](../../soc_secure_boot/) 코스

## 🗺️ 개념 맵
<div class="concept-dag">
  <div class="concept-dag-title">개념 의존성 — 순서대로 학습 권장</div>
  <div class="concept-dag-row">
    <a class="concept-dag-node" href="01_exception_level_trustzone/">
      <span class="concept-dag-node-num">M01</span>
      <span class="concept-dag-node-title">Exception Level & TrustZone</span>
    </a>
    <span class="concept-dag-arrow">→</span>
    <a class="concept-dag-node" href="02_world_switch_soc_infra/">
      <span class="concept-dag-node-num">M02</span>
      <span class="concept-dag-node-title">World Switch & SoC Infra</span>
    </a>
    <span class="concept-dag-arrow">→</span>
    <a class="concept-dag-node" href="02a_secure_enclave_and_tee_hierarchy/">
      <span class="concept-dag-node-num">M02A</span>
      <span class="concept-dag-node-title">Secure Enclave & TEE</span>
    </a>
    <span class="concept-dag-arrow">→</span>
    <a class="concept-dag-node" href="03_secure_boot_connection/">
      <span class="concept-dag-node-num">M03</span>
      <span class="concept-dag-node-title">Secure Boot Connection</span>
    </a>
  </div>
  <div class="concept-dag-row">
    <span class="concept-dag-arrow">↪</span>
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
  <a class="module-card" data-cat="soc" href="01_exception_level_trustzone/">
    <div class="module-num">01</div>
    <div class="module-body">
      <div class="module-title">Exception Level & TrustZone</div>
    </div>
  </a>
  <a class="module-card" data-cat="soc" href="02_world_switch_soc_infra/">
    <div class="module-num">02</div>
    <div class="module-body">
      <div class="module-title">World Switch & SoC Security Infra</div>
    </div>
  </a>
  <a class="module-card" data-cat="soc" href="03_secure_boot_connection/">
    <div class="module-num">03</div>
    <div class="module-body">
      <div class="module-title">Secure Boot Connection</div>
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
    <div class="pill-title">EL &amp; TrustZone</div>
  </div>
  <div class="path-arrow">▶</div>
  <div class="path-pill tier-core">
    <div class="pill-num">M02</div>
    <div class="pill-title">World Switch</div>
  </div>
  <div class="path-arrow">▶</div>
  <div class="path-pill tier-adv">
    <div class="pill-num">M02A</div>
    <div class="pill-title">Enclave/TEE</div>
  </div>
  <div class="path-arrow">▶</div>
  <div class="path-pill tier-adv">
    <div class="pill-num">M03</div>
    <div class="pill-title">Secure Boot 연계</div>
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
  <a class="course-card" href="https://humbleowl39.github.io/DV_SKOOL/soc_secure_boot/">
    <div class="course-card-num">🔐 관련</div>
    <div class="course-card-title">SoC Secure Boot</div>
    <div class="course-card-desc">RoT, chain of trust, BootROM DV</div>
  </a>
  <a class="course-card" href="https://humbleowl39.github.io/DV_SKOOL/virtualization/">
    <div class="course-card-num">🪟 관련</div>
    <div class="course-card-title">Virtualization</div>
    <div class="course-card-desc">CPU/Mem/IO 가상화, 하이퍼바이저</div>
  </a>
  <a class="course-card" href="https://humbleowl39.github.io/DV_SKOOL/mmu/">
    <div class="course-card-num">🧭 관련</div>
    <div class="course-card-title">MMU</div>
    <div class="course-card-desc">페이지 테이블, TLB, IOMMU/SMMU</div>
  </a>
  <a class="course-card" href="https://humbleowl39.github.io/DV_SKOOL/" style="border-style:dashed;">
    <div class="course-card-num">🏠 HOME</div>
    <div class="course-card-title">DV SKOOL 홈</div>
    <div class="course-card-desc">전체 토픽 / 학습 경로 보기</div>
  </a>
</div>

<!-- DV-SKOOL-RELATED-TOPICS:end -->
