# PCI Express (PCIe)

<!-- DV-SKOOL-HERO:start -->
<div class="topic-hero" data-cat="intercon">
  <div class="topic-hero-mark">🔌</div>
  <div class="topic-hero-body">
    <div class="topic-hero-title">PCI Express (PCIe)</div>
    <p class="topic-hero-sub">PCIe — 3-layer, TLP/DLLP, LTSSM, SR-IOV/CXL</p>
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
  <a class="page-toc-link" href="#참조-자료">📖 참조 자료</a>
</div>
<!-- DV-SKOOL-TOC:end -->

## 🎯 학습 목표
- **Explain** PCI parallel → PCIe serial point-to-point 전환의 동기와 Gen1~Gen7 진화의 핵심을 설명한다.
- **Diagram** Transaction / Data Link / Physical 3-layer 의 책임과 데이터 흐름을 그릴 수 있다.
- **Decode** TLP header (Fmt/Type/Length/Address) 와 DLLP 의 type/sequence number 를 해독한다.
- **Trace** LTSSM 의 11 상태 전이와 Gen3+ equalization 단계를 추적한다.
- **Apply** Configuration Space (Type 0/1) 와 BAR sizing 을 이용해 enumeration 시퀀스를 직접 수행한다.
- **Evaluate** Power state (D/L/ASPM), AER, Hot Plug 가 운영 안정성에 미치는 영향을 평가한다.
- **Compare** SR-IOV, ATS+IOMMU, P2P, CXL.io/cache/mem 의 차이와 사용 시점을 비교한다.

## 📋 사전 지식
- 일반 디지털 시스템 (직렬/병렬 인터페이스, clock, encoding)
- 메모리 매핑 IO, 인터럽트 (MSI/MSI-X) 기본
- TCP/이더넷 등 layered protocol 경험 (선택)

## 🗺️ 개념 맵
<div class="concept-dag">
  <div class="concept-dag-title">개념 의존성 — 순서대로 학습 권장</div>
  <div class="concept-dag-row">
    <a class="concept-dag-node" href="01_pcie_motivation/">
      <span class="concept-dag-node-num">M01</span>
      <span class="concept-dag-node-title">PCIe 동기</span>
    </a>
    <span class="concept-dag-arrow">→</span>
    <a class="concept-dag-node" href="02_layer_architecture/">
      <span class="concept-dag-node-num">M02</span>
      <span class="concept-dag-node-title">3-Layer</span>
    </a>
    <span class="concept-dag-arrow">→</span>
    <a class="concept-dag-node" href="03_tlp/">
      <span class="concept-dag-node-num">M03</span>
      <span class="concept-dag-node-title">TLP</span>
    </a>
    <span class="concept-dag-arrow">→</span>
    <a class="concept-dag-node" href="04_dllp_flow_control/">
      <span class="concept-dag-node-num">M04</span>
      <span class="concept-dag-node-title">DLLP &amp; FC</span>
    </a>
  </div>
  <div class="concept-dag-row">
    <a class="concept-dag-node" href="05_phy_ltssm/">
      <span class="concept-dag-node-num">M05</span>
      <span class="concept-dag-node-title">PHY &amp; LTSSM</span>
    </a>
    <span class="concept-dag-arrow">→</span>
    <a class="concept-dag-node" href="06_config_enumeration/">
      <span class="concept-dag-node-num">M06</span>
      <span class="concept-dag-node-title">Config &amp; Enum</span>
    </a>
    <span class="concept-dag-arrow">→</span>
    <a class="concept-dag-node" href="07_power_aer_hotplug/">
      <span class="concept-dag-node-num">M07</span>
      <span class="concept-dag-node-title">Power/AER/HP</span>
    </a>
    <span class="concept-dag-arrow">→</span>
    <a class="concept-dag-node" href="08_advanced/">
      <span class="concept-dag-node-num">M08</span>
      <span class="concept-dag-node-title">SR-IOV / CXL</span>
    </a>
  </div>
  <div class="concept-dag-row">
    <span class="concept-dag-arrow">↪</span>
    <a class="concept-dag-node" href="09_quick_reference_card/">
      <span class="concept-dag-node-num">Ref</span>
      <span class="concept-dag-node-title">Quick Reference</span>
    </a>
  </div>
  <div class="concept-dag-legend">각 노드 = 모듈 (클릭하여 이동) · 화살표(→) = 선수 지식 흐름</div>
</div>

## 📚 학습 모듈
<!-- DV-SKOOL-MODULES:start -->
<div class="module-grid">
  <a class="module-card" data-cat="intercon" href="01_pcie_motivation/">
    <div class="module-num">01</div>
    <div class="module-body">
      <div class="module-title">PCIe 동기와 진화</div>
    </div>
  </a>
  <a class="module-card" data-cat="intercon" href="02_layer_architecture/">
    <div class="module-num">02</div>
    <div class="module-body">
      <div class="module-title">3-Layer Architecture</div>
    </div>
  </a>
  <a class="module-card" data-cat="intercon" href="03_tlp/">
    <div class="module-num">03</div>
    <div class="module-body">
      <div class="module-title">TLP (Transaction Layer Packet)</div>
    </div>
  </a>
  <a class="module-card" data-cat="intercon" href="04_dllp_flow_control/">
    <div class="module-num">04</div>
    <div class="module-body">
      <div class="module-title">DLLP, Flow Control, ACK/NAK</div>
    </div>
  </a>
  <a class="module-card" data-cat="intercon" href="05_phy_ltssm/">
    <div class="module-num">05</div>
    <div class="module-body">
      <div class="module-title">Physical Layer & LTSSM</div>
    </div>
  </a>
  <a class="module-card" data-cat="intercon" href="06_config_enumeration/">
    <div class="module-num">06</div>
    <div class="module-body">
      <div class="module-title">Configuration Space & Enumeration</div>
    </div>
  </a>
  <a class="module-card" data-cat="intercon" href="07_power_aer_hotplug/">
    <div class="module-num">07</div>
    <div class="module-body">
      <div class="module-title">Power Management, AER, Hot Plug</div>
    </div>
  </a>
  <a class="module-card" data-cat="intercon" href="08_advanced/">
    <div class="module-num">08</div>
    <div class="module-body">
      <div class="module-title">SR-IOV, ATS, P2P, CXL</div>
    </div>
  </a>
  <a class="module-card" data-cat="intercon" href="09_quick_reference_card/">
    <div class="module-num is-special" title="Quick Reference">★</div>
    <div class="module-body">
      <div class="module-title">Quick Reference Card</div>
    </div>
  </a>
</div>
<!-- DV-SKOOL-MODULES:end -->

## 📖 참조 자료
- **PCI Express Base Specification 6.0 / 7.0** — PCI-SIG (회원사 비공개, 일부 white paper 공개)
- **PCI Express System Architecture (MindShare)** — 학습용 표준 참고서
- **Linux Kernel `Documentation/PCI/`** — 공개, 실 구현 관점
- **OS / Hypervisor IOMMU 문서** — Intel VT-d, ARM SMMU
- **CXL Consortium Specifications** — CXL 1.1 / 2.0 / 3.0 / 3.1 (공개 white paper)

<!-- DV-SKOOL-RELATED-TOPICS:start -->

## 🔗 관련 토픽
<div class="course-grid">
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
  <a class="course-card" href="https://humbleowl39.github.io/DV_SKOOL/virtualization/">
    <div class="course-card-num">🪟 관련</div>
    <div class="course-card-title">Virtualization</div>
    <div class="course-card-desc">CPU/Mem/IO 가상화, 하이퍼바이저</div>
  </a>
  <a class="course-card" href="https://humbleowl39.github.io/DV_SKOOL/rdma/">
    <div class="course-card-num">⚡ 관련</div>
    <div class="course-card-title">RDMA</div>
    <div class="course-card-desc">InfiniBand & RoCEv2, QP/MR</div>
  </a>
  <a class="course-card" href="https://humbleowl39.github.io/DV_SKOOL/" style="border-style:dashed;">
    <div class="course-card-num">🏠 HOME</div>
    <div class="course-card-title">DV SKOOL 홈</div>
    <div class="course-card-desc">전체 토픽 / 학습 경로 보기</div>
  </a>
</div>

<!-- DV-SKOOL-RELATED-TOPICS:end -->


--8<-- "abbreviations.md"
--8<-- "_inc/topic_abbr.md"
