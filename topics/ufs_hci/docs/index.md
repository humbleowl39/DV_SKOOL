# UFS HCI

<!-- DV-SKOOL-HERO:start -->
<div class="topic-hero" data-cat="memory">
  <div class="topic-hero-mark">💿</div>
  <div class="topic-hero-body">
    <div class="topic-hero-title">UFS HCI</div>
    <p class="topic-hero-sub">UFS 프로토콜 스택, HCI, UPIU 흐름</p>
  </div>
</div>
<!-- DV-SKOOL-HERO:end -->

UFS HCI(Host Controller Interface)는 SW 드라이버와 UFS 장치 사이의 유일한 표준 계약입니다. UTRD 하나가 잘못된 메모리 주소를 가리키거나 Doorbell이 한 클럭 일찍 울리면, HCI는 오류 없이 동작하지만 데이터는 조용히 다른 LBA에 쓰입니다. 이런 silent corruption은 기능 테스트를 통과하고도 양산 후에야 드러나므로, HCI 레이어를 이해하고 검증하는 능력은 스토리지 SoC를 다루는 DV 엔지니어의 핵심 역량입니다.

이 토픽을 학습하지 않으면 UTRD 구조나 Doorbell 흐름을 모르는 채로 DV 환경을 설계하게 되고, Task Tag 매칭 오류나 SW·HW 경쟁 조건 같은 가장 위험한 버그 카테고리를 커버리지 목표에 포함시키지 못합니다. M01에서 프로토콜 스택을 잡고, M02에서 HCI 내부 메커니즘을 파악한 뒤, M03에서 UPIU 흐름을 추적하고, M04에서 검증 전략을 직접 설계하는 순서로 진행하면 이 모든 문제를 체계적으로 해결할 수 있습니다.

<!-- DV-SKOOL-TOC:start -->
<div class="page-toc">
  <span class="page-toc-label">목차</span>
  <a class="page-toc-link" href="#학습-목표">🎯 학습 목표</a>
  <a class="page-toc-link" href="#사전-지식">📋 사전 지식</a>
  <a class="page-toc-link" href="#개념-맵">🗺️ 개념 맵</a>
  <a class="page-toc-link" href="#학습-모듈">📚 학습 모듈</a>
  <a class="page-toc-link" href="#모듈-흐름">📊 모듈 흐름</a>
  <a class="page-toc-link" href="#관련-자료">📖 관련 자료</a>
  <a class="page-toc-link" href="#학습-팁">💡 학습 팁</a>
</div>
<!-- DV-SKOOL-TOC:end -->

## 🎯 학습 목표
- **Trace** UFS 프로토콜 스택 (UTP/UPIU/UniPro/MIPI M-PHY) 흐름 추적
- **Diagram** HCI 아키텍처 (UTRD, UTMRD, doorbell)와 host ↔ device 통신 흐름
- **Apply** UPIU command/response 흐름과 LU(Logical Unit) 관리 시나리오
- **Plan** UFS HCI DV 환경 설계 (UFS device model, host driver, AXI host interface)

## 📋 사전 지식
- 스토리지 프로토콜 일반 (SATA, NVMe 비교)
- AXI/AHB 인터커넥트
- DMA / queue-based command 모델

## 🗺️ 개념 맵
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

## 📚 학습 모듈
<!-- DV-SKOOL-MODULES:start -->
<div class="module-grid">
  <a class="module-card" data-cat="memory" href="01_ufs_protocol_stack/">
    <div class="module-num">01</div>
    <div class="module-body">
      <div class="module-title">UFS Protocol Stack</div>
    </div>
  </a>
  <a class="module-card" data-cat="memory" href="02_hci_architecture/">
    <div class="module-num">02</div>
    <div class="module-body">
      <div class="module-title">HCI Architecture</div>
    </div>
  </a>
  <a class="module-card" data-cat="memory" href="03_upiu_command_flow/">
    <div class="module-num">03</div>
    <div class="module-body">
      <div class="module-title">UPIU & Command Flow</div>
    </div>
  </a>
  <a class="module-card" data-cat="memory" href="04_hci_dv_methodology/">
    <div class="module-num">04</div>
    <div class="module-body">
      <div class="module-title">HCI DV Methodology</div>
    </div>
  </a>
  <a class="module-card" data-cat="memory" href="05_quick_reference_card/">
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

## 📖 관련 자료
- 📚 [**용어집 (Glossary)**](glossary.md)
- 📝 [**퀴즈 (Quizzes)**](quiz/index.md)
- 📋 [**코스 개요**](_legacy_overview.md)

## 💡 학습 팁
!!! tip "효율적 학습"
    5계층(Application / UTP·UPIU / UniPro / M-PHY / Storage)을 단순히 외우는 것이 아니라 각 계층이 인접 계층과 어떤 인터페이스로 연결되는지까지 파악해야 합니다. 이 구조를 알면 버그가 발생했을 때 어느 계층에서 문제가 생겼는지 바로 좁힐 수 있습니다.

    UPIU 형식을 이해할 때는 "SCSI CDB를 그대로 쓰지 않고 왜 캡슐화했는가"라는 질문에서 출발하세요. Task Tag, Query, NOP, Reject처럼 UFS-specific 요소를 추가해야 했기 때문이며, 이 추가 요소들이 DV 검증 포인트의 핵심이 됩니다.

    모든 명령 처리는 **Doorbell ring → UTRD fetch → command exec → Interrupt** 네 단계를 거칩니다. 이 흐름을 머릿속에서 동작시킬 수 있을 때 UTRD 필드가 왜 그런 값을 갖는지, interrupt aggregation이 어느 단계에 영향을 주는지를 자연스럽게 이해할 수 있습니다.

<!-- DV-SKOOL-RELATED-TOPICS:start -->

## 🔗 관련 토픽
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


--8<-- "abbreviations.md"
--8<-- "_inc/topic_abbr.md"
