# UFS HCI

<!-- DV-SKOOL-HERO:start -->
<div class="topic-hero" data-cat="memory">
  <div class="topic-hero-mark">💿</div>
  <div class="topic-hero-body">
    <div class="topic-hero-title">UFS HCI</div>
    <p class="topic-hero-sub">프로토콜 스택, HCI 아키텍처, UPIU 흐름, DV 방법론.</p>
    <div class="topic-hero-stats">
      <span class="topic-stat"><span class="topic-stat-icon">📚</span><span class="topic-stat-val">4</span><span class="topic-stat-lbl">모듈</span></span>
      <span class="topic-stat"><span class="topic-stat-icon">⏱</span><span class="topic-stat-val">~1.7h</span><span class="topic-stat-lbl">예상</span></span>
      <span class="topic-stat"><span class="topic-stat-icon">🎯</span><span class="topic-stat-val">심화</span><span class="topic-stat-lbl">난이도</span></span>
    </div>
  </div>
</div>
<!-- DV-SKOOL-HERO:end -->

## 이 코스에서 얻는 것

- **Trace** UFS 프로토콜 스택 (UTP/UPIU/UniPro/MIPI M-PHY) 흐름 추적
- **Diagram** HCI 아키텍처 (UTRD, UTMRD, doorbell)와 host ↔ device 통신 흐름
- **Apply** UPIU command/response 흐름과 LU(Logical Unit) 관리 시나리오
- **Plan** UFS HCI DV 환경 설계 (UFS device model, host driver, AXI host interface)

## 사전 지식

- 스토리지 프로토콜 일반 (SATA, NVMe 비교)
- AXI/AHB 인터커넥트
- DMA / queue-based command 모델

## 🗺️ 학습 경로

<div class="concept-dag">
  <div class="concept-dag-title">개념 의존성 — 순서대로 학습 권장</div>
  <div class="concept-dag-row">
    <a class="concept-dag-node" href="01_ufs_protocol_stack/">
      <span class="concept-dag-node-num">M01</span>
      <span class="concept-dag-node-title">UFS Protocol Stack</span>
    </a>
    <span class="concept-dag-arrow">→</span>
    <a class="concept-dag-node" href="02_hci_architecture/">
      <span class="concept-dag-node-num">M02</span>
      <span class="concept-dag-node-title">HCI Architecture</span>
    </a>
    <span class="concept-dag-arrow">→</span>
    <a class="concept-dag-node" href="03_upiu_command_flow/">
      <span class="concept-dag-node-num">M03</span>
      <span class="concept-dag-node-title">UPIU Command Flow</span>
    </a>
    <span class="concept-dag-arrow">→</span>
    <a class="concept-dag-node" href="04_hci_dv_methodology/">
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

## 학습 모듈

<!-- DV-SKOOL-MODULES:start -->
<div class="module-grid">
  <a class="module-card" data-cat="memory" href="01_ufs_protocol_stack/">
    <div class="module-num">01</div>
    <div class="module-body">
      <div class="module-title">UFS Protocol Stack</div>
      <div class="module-meta">
        <span class="module-time">⏱ 18분</span>
        
      </div>
    </div>
  </a>
  <a class="module-card" data-cat="memory" href="02_hci_architecture/">
    <div class="module-num">02</div>
    <div class="module-body">
      <div class="module-title">HCI Architecture</div>
      <div class="module-meta">
        <span class="module-time">⏱ 24분</span>
        
      </div>
    </div>
  </a>
  <a class="module-card" data-cat="memory" href="03_upiu_command_flow/">
    <div class="module-num">03</div>
    <div class="module-body">
      <div class="module-title">UPIU & Command Flow</div>
      <div class="module-meta">
        <span class="module-time">⏱ 20분</span>
        
      </div>
    </div>
  </a>
  <a class="module-card" data-cat="memory" href="04_hci_dv_methodology/">
    <div class="module-num">04</div>
    <div class="module-body">
      <div class="module-title">HCI DV Methodology</div>
      <div class="module-meta">
        <span class="module-time">⏱ 32분</span>
        
      </div>
    </div>
  </a>
  <a class="module-card" data-cat="memory" href="05_quick_reference_card/">
    <div class="module-num is-special" title="Quick Reference">★</div>
    <div class="module-body">
      <div class="module-title">Quick Reference Card</div>
      <div class="module-meta">
        <span class="module-time">⏱ 9분</span>
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
    <div class="pill-title">Protocol Stack</div>
  </div>
  <div class="path-arrow">▶</div>
  <div class="path-pill tier-core">
    <div class="pill-num">M02</div>
    <div class="pill-title">HCI Architecture</div>
  </div>
  <div class="path-arrow">▶</div>
  <div class="path-pill tier-adv">
    <div class="pill-num">M03</div>
    <div class="pill-title">UPIU Flow</div>
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

## 관련 자료

- 📚 [**용어집 (Glossary)**](glossary.md)
- 📝 [**퀴즈 (Quizzes)**](quiz/index.md)
- 📋 [**코스 개요**](_legacy_overview.md)

## 학습 팁

!!! tip "효율적 학습"
    - **5계층을 외워야**: UTP / UPIU / UniPro / M-PHY / Storage. 각 계층의 책임 + 인접 계층과의 인터페이스
    - **UPIU 형식 = SCSI mapping + UFS 확장**: SCSI 기본 + Query/NOP/Reject 같은 UFS-specific
    - **Doorbell ring → UTRD parse → command exec → Interrupt** 흐름이 모든 명령의 표준

<!-- DV-SKOOL-RELATED-TOPICS:start -->

## 관련 토픽

<div class="course-grid">
  <a class="course-card" href="https://humbleowl39.github.io/DV_SKOOL/amba_protocols/">
    <div class="course-card-num">🔄 관련</div>
    <div class="course-card-title">AMBA Protocols</div>
    <div class="course-card-desc">APB/AHB/AXI — 표준 버스 프로토콜</div>
  </a>
  <a class="course-card" href="https://humbleowl39.github.io/DV_SKOOL/dram_ddr/">
    <div class="course-card-num">💾 관련</div>
    <div class="course-card-title">DRAM / DDR</div>
    <div class="course-card-desc">DRAM 컨트롤러, PHY, DDR DV</div>
  </a>
  <a class="course-card" href="https://humbleowl39.github.io/DV_SKOOL/soc_integration_cctv/">
    <div class="course-card-num">🏗️ 관련</div>
    <div class="course-card-title">SoC Integration</div>
    <div class="course-card-desc">Top-level integration, TB top</div>
  </a>
  <a class="course-card" href="https://humbleowl39.github.io/DV_SKOOL/" style="border-style:dashed;">
    <div class="course-card-num">🏠 HOME</div>
    <div class="course-card-title">DV SKOOL 홈</div>
    <div class="course-card-desc">전체 토픽 / 학습 경로 보기</div>
  </a>
</div>

<!-- DV-SKOOL-RELATED-TOPICS:end -->
