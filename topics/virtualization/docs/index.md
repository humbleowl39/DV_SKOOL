# Virtualization

<!-- DV-SKOOL-HERO:start -->
<div class="topic-hero" data-cat="soc">
  <div class="topic-hero-mark">🪟</div>
  <div class="topic-hero-body">
    <div class="topic-hero-title">Virtualization</div>
    <p class="topic-hero-sub">CPU/메모리/IO 가상화, 하이퍼바이저, 컨테이너</p>
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
- **Trace** 시스템 아키텍처 진화 (HW only → process → kernel/user → 가상화)
- **Diagram** CPU / 메모리 / I/O 가상화의 각 layer 동작
- **Distinguish** Type 1 vs Type 2 hypervisor, strict vs passthrough
- **Apply** Container (Docker/K8s) 와 hypervisor 가상화의 trade-off
- **Plan** Modern infrastructure (microVM, gVisor, kata-containers) 적합성

## 📋 사전 지식
- OS 기본 (process, kernel/user mode)
- CPU 권한 모드 (ring, EL)
- 가상 메모리 ([MMU 코스](../../mmu/) 참고)

## 🗺️ 개념 맵
<div class="concept-dag dag-long">
  <div class="concept-dag-title">개념 의존성 — 순서대로 학습 권장</div>
  <div class="concept-dag-row">
    <a class="concept-dag-node" href="01_virtualization_fundamentals/">
      <span class="concept-dag-node-num">M01</span>
      <span class="concept-dag-node-title">Fundamentals</span>
    </a>
    <span class="concept-dag-arrow">→</span>
    <a class="concept-dag-node" href="01a_system_architecture_evolution/">
      <span class="concept-dag-node-num">M01A</span>
      <span class="concept-dag-node-title">Architecture Evolution</span>
    </a>
    <span class="concept-dag-arrow">→</span>
    <a class="concept-dag-node" href="02_cpu_virtualization/">
      <span class="concept-dag-node-num">M02</span>
      <span class="concept-dag-node-title">CPU</span>
    </a>
    <span class="concept-dag-arrow">→</span>
    <a class="concept-dag-node" href="03_memory_virtualization/">
      <span class="concept-dag-node-num">M03</span>
      <span class="concept-dag-node-title">Memory</span>
    </a>
  </div>
  <div class="concept-dag-row">
    <span class="concept-dag-arrow">↪</span>
    <a class="concept-dag-node" href="04_io_virtualization/">
      <span class="concept-dag-node-num">M04</span>
      <span class="concept-dag-node-title">I/O</span>
    </a>
    <span class="concept-dag-arrow">→</span>
    <a class="concept-dag-node" href="05_hypervisor_types/">
      <span class="concept-dag-node-num">M05</span>
      <span class="concept-dag-node-title">Hypervisor Types</span>
    </a>
    <span class="concept-dag-arrow">→</span>
    <a class="concept-dag-node" href="06_strict_vs_passthrough/">
      <span class="concept-dag-node-num">M06</span>
      <span class="concept-dag-node-title">Strict vs Passthrough</span>
    </a>
    <span class="concept-dag-arrow">→</span>
    <a class="concept-dag-node" href="07_containers_and_modern/">
      <span class="concept-dag-node-num">M07</span>
      <span class="concept-dag-node-title">Containers</span>
    </a>
  </div>
  <div class="concept-dag-row">
    <span class="concept-dag-arrow">↪</span>
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
  <a class="module-card" data-cat="soc" href="01_virtualization_fundamentals/">
    <div class="module-num">01</div>
    <div class="module-body">
      <div class="module-title">Virtualization Fundamentals</div>
    </div>
  </a>
  <a class="module-card" data-cat="soc" href="02_cpu_virtualization/">
    <div class="module-num">02</div>
    <div class="module-body">
      <div class="module-title">CPU Virtualization</div>
    </div>
  </a>
  <a class="module-card" data-cat="soc" href="03_memory_virtualization/">
    <div class="module-num">03</div>
    <div class="module-body">
      <div class="module-title">Memory Virtualization</div>
    </div>
  </a>
  <a class="module-card" data-cat="soc" href="04_io_virtualization/">
    <div class="module-num">04</div>
    <div class="module-body">
      <div class="module-title">I/O Virtualization</div>
    </div>
  </a>
  <a class="module-card" data-cat="soc" href="05_hypervisor_types/">
    <div class="module-num">05</div>
    <div class="module-body">
      <div class="module-title">Hypervisor Types</div>
    </div>
  </a>
  <a class="module-card" data-cat="soc" href="06_strict_vs_passthrough/">
    <div class="module-num">06</div>
    <div class="module-body">
      <div class="module-title">Strict vs Passthrough</div>
    </div>
  </a>
  <a class="module-card" data-cat="soc" href="07_containers_and_modern/">
    <div class="module-num">07</div>
    <div class="module-body">
      <div class="module-title">Containers & Modern Virtualization</div>
    </div>
  </a>
  <a class="module-card" data-cat="soc" href="08_quick_reference_card/">
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
    <div class="pill-num">M02-04</div>
    <div class="pill-title">CPU/Mem/IO Virt</div>
  </div>
  <div class="path-arrow">▶</div>
  <div class="path-pill tier-adv">
    <div class="pill-num">M05-06</div>
    <div class="pill-title">Hypervisor Types</div>
  </div>
  <div class="path-arrow">▶</div>
  <div class="path-pill tier-adv">
    <div class="pill-num">M07</div>
    <div class="pill-title">Modern</div>
  </div>
  <div class="path-arrow">▶</div>
  <div class="path-pill tier-ref">
    <div class="pill-num">M08</div>
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
  <a class="course-card" href="https://humbleowl39.github.io/DV_SKOOL/mmu/">
    <div class="course-card-num">🧭 관련</div>
    <div class="course-card-title">MMU</div>
    <div class="course-card-desc">페이지 테이블, TLB, IOMMU/SMMU</div>
  </a>
  <a class="course-card" href="https://humbleowl39.github.io/DV_SKOOL/arm_security/">
    <div class="course-card-num">🛡️ 관련</div>
    <div class="course-card-title">ARM Security</div>
    <div class="course-card-desc">Exception level, TrustZone, TEE</div>
  </a>
  <a class="course-card" href="https://humbleowl39.github.io/DV_SKOOL/pcie/">
    <div class="course-card-num">🔌 관련</div>
    <div class="course-card-title">PCI Express</div>
    <div class="course-card-desc">TLP/DLLP, LTSSM, SR-IOV/CXL</div>
  </a>
  <a class="course-card" href="https://humbleowl39.github.io/DV_SKOOL/" style="border-style:dashed;">
    <div class="course-card-num">🏠 HOME</div>
    <div class="course-card-title">DV SKOOL 홈</div>
    <div class="course-card-desc">전체 토픽 / 학습 경로 보기</div>
  </a>
</div>

<!-- DV-SKOOL-RELATED-TOPICS:end -->
