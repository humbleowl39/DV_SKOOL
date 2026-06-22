# DRAM / DDR

<!-- DV-SKOOL-HERO:start -->
<div class="topic-hero" data-cat="memory">
  <div class="topic-hero-mark">💾</div>
  <div class="topic-hero-body">
    <div class="topic-hero-title">DRAM / DDR</div>
    <p class="topic-hero-sub">DRAM 셀부터 LPDDR5 PHY, 메모리 컨트롤러 DV까지 (주축: LPDDR5, 비교: DDR5)</p>
  </div>
</div>
<!-- DV-SKOOL-HERO:end -->

현대 모바일 SoC에서 LPDDR5는 CPU, GPU, NPU가 공유하는 유일한 대용량 main memory다. 이 토픽의 주축은 **LPDDR5**이며, 서버·PC용 **DDR5**를 비교축으로, 직전 세대 **LPDDR4**를 진화 기준으로 둔다. 메모리 컨트롤러(MC)가 JEDEC timing constraint를 한 사이클이라도 위반하면 데이터 손상이 발생하고, PHY training(LPDDR5는 CBT + WCK2CK leveling으로 단계가 가장 많다)이 marginal한 상태로 초기화되면 정상 조건에서는 문제없다가 온도 변화 같은 PVT 스트레스에서 조용히 bit error를 낸다. 이런 결함은 테스트에서 잡지 못하면 field에서 재현하기 극히 어렵다. DRAM DV를 제대로 이해하지 못하면 timing assertion을 "왜 이렇게 복잡하게 만드나" 싶어 건너뛰게 되고, PHY training 검증을 PVT corner 없이 nominal만 돌리게 된다. 이 토픽은 DRAM cell 구조부터 LPDDR5 명령 프로토콜(DDR5 비교 포함), MC 스케줄링, PHY training, 그리고 그것을 검증하는 방법론까지를 하나의 인과 흐름으로 연결한다.

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
- **Trace (분석)** DRAM cell의 charge → ROW activate → COL access → precharge 흐름을 ns 단위로 그릴 수 있다
- **Distinguish (분석)** LPDDR5 vs DDR5 vs LPDDR4의 핵심 차이(WCK/CK 클럭 분리, bank mode, PASR, Link ECC vs on-die ECC, DVFSC)를 식별
- **Apply (적용)** Memory Controller의 read/write reordering, bank interleaving, refresh scheduling
- **Implement (생성)** PHY 레벨의 DLL/PLL, training, write/read leveling 검증 시나리오 설계
- **Plan (생성)** DRAM DV 환경에서 traffic generator, refcheck, performance reference 구조 설계

## 📋 사전 지식
- 디지털 회로 기본 (클럭, 동기 회로, FIFO)
- AMBA AXI / AXI-S 기본 (host interface 측)
- SoC 메모리 서브시스템 개요

## 🗺️ 개념 맵
<div class="concept-dag">
  <div class="concept-dag-title">개념 의존성 — 순서대로 학습 권장</div>
  <div class="concept-dag-row">
    <a class="concept-dag-node" href="01_dram_fundamentals_ddr/">
      <span class="concept-dag-node-num">M01</span>
      <span class="concept-dag-node-title">DRAM / LPDDR5</span>
    </a>
    <span class="concept-dag-arrow">→</span>
    <a class="concept-dag-node" href="02_memory_controller/">
      <span class="concept-dag-node-num">M02</span>
      <span class="concept-dag-node-title">Memory Controller</span>
    </a>
    <span class="concept-dag-arrow">→</span>
    <a class="concept-dag-node" href="03_memory_interface_phy/">
      <span class="concept-dag-node-num">M03</span>
      <span class="concept-dag-node-title">Memory Interface / PHY</span>
    </a>
    <span class="concept-dag-arrow">→</span>
    <a class="concept-dag-node" href="04_dram_dv_methodology/">
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
  <a class="module-card" data-cat="memory" href="01_dram_fundamentals_ddr/">
    <div class="module-num">01</div>
    <div class="module-body">
      <div class="module-title">DRAM Fundamentals + LPDDR5</div>
    </div>
  </a>
  <a class="module-card" data-cat="memory" href="02_memory_controller/">
    <div class="module-num">02</div>
    <div class="module-body">
      <div class="module-title">Memory Controller</div>
    </div>
  </a>
  <a class="module-card" data-cat="memory" href="03_memory_interface_phy/">
    <div class="module-num">03</div>
    <div class="module-body">
      <div class="module-title">Memory Interface / PHY</div>
    </div>
  </a>
  <a class="module-card" data-cat="memory" href="04_dram_dv_methodology/">
    <div class="module-num">04</div>
    <div class="module-body">
      <div class="module-title">DRAM DV Methodology</div>
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
    <div class="pill-title">DRAM Fundamentals</div>
  </div>
  <div class="path-arrow">▶</div>
  <div class="path-pill tier-core">
    <div class="pill-num">M02</div>
    <div class="pill-title">MC</div>
  </div>
  <div class="path-arrow">▶</div>
  <div class="path-pill tier-adv">
    <div class="pill-num">M03</div>
    <div class="pill-title">PHY</div>
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
    tRCD, tRP, tCAS, tRAS 같은 timing parameter는 코드 리뷰나 면접에서 즉시 떠올릴 수 있어야 하므로 반복 암기가 필요하다. 주축인 LPDDR5에서 가장 큰 구조적 특징은 CK(명령)/WCK(데이터) 클럭 분리와 Link ECC·PASR·DVFSC 같은 모바일 전력 기능이므로, 이들이 검증 시나리오(특히 WCK2CK leveling, DVFSC gear 전환 시 retraining)에 어떤 영향을 주는지 집중적으로 파악하는 것이 좋다. 서버용 DDR5와의 차이(단일 CK, 32뱅크, Link ECC 부재)는 비교 기준으로 함께 익히면 이해가 빠르다. PHY training과 leveling은 아날로그 신호 특성이 섞여 있어 이해하는 데 시간이 걸리는 영역인데, 각 training 단계의 목적(무엇을 정렬하는가)을 먼저 이해한 뒤 실제 JEDEC spec을 참조하면 학습 효율이 높아진다.

!!! warning "흔한 함정"
    Refresh 검증은 단순히 "REF 명령이 발행되는가"를 확인하는 것으로 끝나지 않는다. tREFI 기간 내 모든 row가 한 번 이상 refresh를 받았는지 카운터 기반 assertion으로 구조적으로 보장해야 한다. Bank conflict는 같은 bank에 연속 접근이 발생할 때 ACT-PRE cycle이 강제되어 throughput이 크게 저하되는데, 이를 성능 저하가 아닌 스케줄러 버그로 분류해 다뤄야 한다. PHY training이 완료되지 않은 상태에서 traffic을 시작하면 bit error가 발생하지만 즉각 드러나지 않고 특정 패턴에서만 나타나는 silent corruption 형태를 띠므로, training 완료 신호와 traffic 시작 시퀀스를 assertion으로 반드시 순서 보장해야 한다.

<!-- DV-SKOOL-RELATED-TOPICS:start -->

## 🔗 관련 토픽
<div class="course-grid">
  <a class="course-card" href="https://humbleowl39.github.io/DV_SKOOL/mmu/">
    <div class="course-card-num">🧭 관련</div>
    <div class="course-card-title">MMU</div>
    <div class="course-card-desc">페이지 테이블, TLB, IOMMU/SMMU</div>
  </a>
  <a class="course-card" href="https://humbleowl39.github.io/DV_SKOOL/ufs_hci/">
    <div class="course-card-num">💿 관련</div>
    <div class="course-card-title">UFS HCI</div>
    <div class="course-card-desc">UFS 프로토콜, HCI, UPIU</div>
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
