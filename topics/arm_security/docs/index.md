# ARM Security

> **ARM Security Architecture 마스터 코스** — Exception Level, TrustZone, Secure Enclave, TEE 계층, Secure Boot 연계.

<div class="course-header">
  <div class="course-stats">
    <div class="stat-item"><strong>4</strong>개 모듈 + Quick Ref</div>
    <div class="stat-item"><strong>심화 (Advanced)</strong> 난이도</div>
  </div>
</div>

## 이 코스에서 얻는 것

- **Diagram** ARMv8 4-level Exception Level (EL0-EL3) 구조와 TrustZone 격리
- **Trace** Secure / Non-secure World 전환 흐름과 SMC instruction
- **Apply** Secure Enclave (Apple SEP, Samsung Knox) 및 TEE 계층의 격리 모델
- **Plan** Secure Boot와 ARM Security 연계 (BL31, EL3 secure monitor)

## 사전 지식

- ARM ISA 기본 (ARMv8 architecture overview)
- 권한 / 격리 / 가상 메모리 일반 ([MMU 코스](../../mmu/) 참고)
- [Secure Boot](../../soc_secure_boot/) 코스

## 🗺️ 학습 경로

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

## 학습 모듈

<div class="course-grid">
  <a class="course-card" href="01_exception_level_trustzone/">
    <div class="course-card-num">Module 01</div>
    <div class="course-card-title">Exception Level &amp; TrustZone</div>
    <div class="course-card-desc">EL0-EL3, secure/non-secure, NS bit</div>
  </a>
  <a class="course-card" href="02_world_switch_soc_infra/">
    <div class="course-card-num">Module 02</div>
    <div class="course-card-title">World Switch &amp; SoC Infra</div>
    <div class="course-card-desc">SMC instruction, secure monitor, sysMMU/peripheral 보안</div>
  </a>
  <a class="course-card" href="02a_secure_enclave_and_tee_hierarchy/">
    <div class="course-card-num">Module 02A</div>
    <div class="course-card-title">Secure Enclave &amp; TEE Hierarchy</div>
    <div class="course-card-desc">SEP, Knox, OP-TEE, Trusty 계층 구조</div>
  </a>
  <a class="course-card" href="03_secure_boot_connection/">
    <div class="course-card-num">Module 03</div>
    <div class="course-card-title">Secure Boot Connection</div>
    <div class="course-card-desc">Secure Boot와 ARM Security 통합 (BL31 = EL3)</div>
  </a>
  <a class="course-card" href="04_quick_reference_card/">
    <div class="course-card-num">Module 04</div>
    <div class="course-card-title">Quick Reference Card</div>
    <div class="course-card-desc">EL/TrustZone 다이어그램, SMC, 흔한 위협</div>
  </a>
</div>

## 학습 경로

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

## 관련 자료

- 📚 [**용어집**](glossary.md)
- 📝 [**퀴즈**](quiz/index.md)
- 📋 [**코스 개요**](_legacy_overview.md)

<!-- DV-SKOOL-RELATED-TOPICS:start -->

## 관련 토픽

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
