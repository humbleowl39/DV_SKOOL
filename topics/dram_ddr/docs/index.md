# DRAM / DDR

<!-- DV-SKOOL-HERO:start -->
<div class="topic-hero" data-cat="memory">
  <div class="topic-hero-mark">💾</div>
  <div class="topic-hero-body">
    <div class="topic-hero-title">DRAM / DDR</div>
    <p class="topic-hero-sub">셀 동작에서 PHY까지, DDR4/5 spec과 Memory Controller 검증 전략을 통합 학습.</p>
    <div class="topic-hero-stats">
      <span class="topic-stat"><span class="topic-stat-icon">📚</span><span class="topic-stat-val">4</span><span class="topic-stat-lbl">모듈</span></span>
      <span class="topic-stat"><span class="topic-stat-icon">⏱</span><span class="topic-stat-val">~1.5h</span><span class="topic-stat-lbl">예상</span></span>
      <span class="topic-stat"><span class="topic-stat-icon">🎯</span><span class="topic-stat-val">중급</span><span class="topic-stat-lbl">난이도</span></span>
    </div>
  </div>
</div>
<!-- DV-SKOOL-HERO:end -->

## 이 코스에서 얻는 것

- **Trace (분석)** DRAM cell의 charge → ROW activate → COL access → precharge 흐름을 ns 단위로 그릴 수 있다
- **Distinguish (분석)** DDR4 vs DDR5의 핵심 차이(2-channel 분리, refresh, on-die ECC 등)를 식별
- **Apply (적용)** Memory Controller의 read/write reordering, bank interleaving, refresh scheduling
- **Implement (생성)** PHY 레벨의 DLL/PLL, training, write/read leveling 검증 시나리오 설계
- **Plan (생성)** DRAM DV 환경에서 traffic generator, refcheck, performance reference 구조 설계

## 사전 지식

- 디지털 회로 기본 (클럭, 동기 회로, FIFO)
- AMBA AXI / AXI-S 기본 (host interface 측)
- SoC 메모리 서브시스템 개요

## 🗺️ 학습 경로

<div class="concept-dag">
  <div class="concept-dag-title">개념 의존성 — 순서대로 학습 권장</div>
  <div class="concept-dag-row">
    <a class="concept-dag-node" href="01_dram_fundamentals_ddr/">
      <span class="concept-dag-node-num">M01</span>
      <span class="concept-dag-node-title">DRAM / DDR4-5</span>
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

## 학습 모듈

<!-- DV-SKOOL-MODULES:start -->
<div class="module-grid">
  <a class="module-card" data-cat="memory" href="01_dram_fundamentals_ddr/">
    <div class="module-num">01</div>
    <div class="module-body">
      <div class="module-title">DRAM Fundamentals + DDR4/5</div>
      <div class="module-meta">
        <span class="module-time">⏱ 20분</span>
        
      </div>
    </div>
  </a>
  <a class="module-card" data-cat="memory" href="02_memory_controller/">
    <div class="module-num">02</div>
    <div class="module-body">
      <div class="module-title">Memory Controller</div>
      <div class="module-meta">
        <span class="module-time">⏱ 21분</span>
        
      </div>
    </div>
  </a>
  <a class="module-card" data-cat="memory" href="03_memory_interface_phy/">
    <div class="module-num">03</div>
    <div class="module-body">
      <div class="module-title">Memory Interface / PHY</div>
      <div class="module-meta">
        <span class="module-time">⏱ 17분</span>
        
      </div>
    </div>
  </a>
  <a class="module-card" data-cat="memory" href="04_dram_dv_methodology/">
    <div class="module-num">04</div>
    <div class="module-body">
      <div class="module-title">DRAM DV Methodology</div>
      <div class="module-meta">
        <span class="module-time">⏱ 22분</span>
        
      </div>
    </div>
  </a>
  <a class="module-card" data-cat="memory" href="05_quick_reference_card/">
    <div class="module-num is-special" title="Quick Reference">★</div>
    <div class="module-body">
      <div class="module-title">Quick Reference Card</div>
      <div class="module-meta">
        <span class="module-time">⏱ 10분</span>
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

## 관련 자료

- 📚 [**용어집 (Glossary)**](glossary.md)
- 📝 [**퀴즈 (Quizzes)**](quiz/index.md)
- 📋 [**코스 개요**](_legacy_overview.md)

## 학습 팁

!!! tip "효율적 학습"
    - **Timing parameter는 외워야**: tRCD, tRP, tCAS, tRAS 등은 면접/리뷰에서 즉시 떠올라야 함
    - **DDR4 → DDR5 차이 주목**: 2-channel 분리(서버 BW)는 큰 변화. on-die ECC도 중요
    - **PHY는 어려움**: training/leveling 부분은 시간 투자 + 실제 spec(JEDEC) 참고

!!! warning "흔한 함정"
    - **Refresh 누락**: tREFI 기간 내 모든 row를 한 번씩 refresh — 스케줄러 검증의 핵심
    - **Bank conflict**: 같은 bank에 연속 access 시 ACT-PRE 사이클 강제 → throughput 저하
    - **Training 실패**: PHY 초기화 안 끝났는데 traffic 시작 → silent corruption

<!-- DV-SKOOL-RELATED-TOPICS:start -->

## 관련 토픽

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
