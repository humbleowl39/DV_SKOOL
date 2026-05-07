# SoC Integration (CCTV)

> **SoC Top Integration & CCTV 마스터 코스** — Top-level 검증 환경 구축, Common Task 패턴, AI 자동화 활용.

<div class="course-header">
  <div class="course-stats">
    <div class="stat-item"><strong>3</strong>개 모듈 + Quick Ref</div>
    <div class="stat-item"><strong>심화 (Advanced)</strong> 난이도</div>
  </div>
</div>

## 이 코스에서 얻는 것

- **Plan** SoC top-level 검증 환경 (multi-IP UVM env, virtual sequence, scoreboard) 설계
- **Apply** Common Task & CCTV (Common Task Coverage Verification) 패턴으로 재사용성 확보
- **Implement** AI 자동화 (LLM 활용) 시퀀스/coverage/디버그 보조 도입
- **Plan** TB Top + multi-Agent + RAL + multi-clock domain 통합

## 사전 지식

- [UVM](../../uvm/) (Agent, Virtual Sequence, RAL)
- [AMBA AXI](../../amba_protocols/) (인터커넥트)
- IP-level 검증 경험 1회 이상

## 🗺️ 학습 경로

<div class="concept-dag">
  <div class="concept-dag-title">개념 의존성 — 순서대로 학습 권장</div>
  <div class="concept-dag-row">
    <a class="concept-dag-node" href="01_soc_top_integration/">
      <span class="concept-dag-node-num">M01</span>
      <span class="concept-dag-node-title">SoC Top Integration</span>
    </a>
    <span class="concept-dag-arrow">→</span>
    <a class="concept-dag-node" href="02_common_task_cctv/">
      <span class="concept-dag-node-num">M02</span>
      <span class="concept-dag-node-title">Common Task & CCTV</span>
    </a>
    <span class="concept-dag-arrow">→</span>
    <a class="concept-dag-node" href="03_tb_top_and_ai/">
      <span class="concept-dag-node-num">M03</span>
      <span class="concept-dag-node-title">TB Top & AI</span>
    </a>
    <span class="concept-dag-arrow">→</span>
    <a class="concept-dag-node" href="04_quick_reference_card/">
      <span class="concept-dag-node-num">Ref</span>
      <span class="concept-dag-node-title">Quick Reference</span>
    </a>
  </div>
  <div class="concept-dag-legend">각 노드 = 모듈 (클릭하여 이동) · 화살표(→) = 선수 지식 흐름</div>
</div>

## 학습 모듈

<div class="course-grid">
  <a class="course-card" href="01_soc_top_integration/">
    <div class="course-card-num">Module 01</div>
    <div class="course-card-title">SoC Top Integration</div>
    <div class="course-card-desc">Top-level 검증 환경, multi-IP env, multi-clock</div>
  </a>
  <a class="course-card" href="02_common_task_cctv/">
    <div class="course-card-num">Module 02</div>
    <div class="course-card-title">Common Task &amp; CCTV</div>
    <div class="course-card-desc">재사용 sequence library, coverage 통합 전략</div>
  </a>
  <a class="course-card" href="03_tb_top_and_ai/">
    <div class="course-card-num">Module 03</div>
    <div class="course-card-title">TB Top &amp; AI Automation</div>
    <div class="course-card-desc">TB 구축 자동화, LLM 시퀀스/coverage/디버그 보조</div>
  </a>
  <a class="course-card" href="04_quick_reference_card/">
    <div class="course-card-num">Module 04</div>
    <div class="course-card-title">Quick Reference Card</div>
    <div class="course-card-desc">SoC 검증 패턴, AI workflow, 흔한 함정</div>
  </a>
</div>

## 학습 경로

<div class="path-chain">
  <div class="path-pill tier-core">
    <div class="pill-num">M01</div>
    <div class="pill-title">SoC Top Integration</div>
  </div>
  <div class="path-arrow">▶</div>
  <div class="path-pill tier-adv">
    <div class="pill-num">M02</div>
    <div class="pill-title">Common Task &amp; CCTV</div>
  </div>
  <div class="path-arrow">▶</div>
  <div class="path-pill tier-adv">
    <div class="pill-num">M03</div>
    <div class="pill-title">TB Top &amp; AI</div>
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
  <a class="course-card" href="https://humbleowl39.github.io/DV_SKOOL/uvm/">
    <div class="course-card-num">🧪 관련</div>
    <div class="course-card-title">UVM</div>
    <div class="course-card-desc">검증 방법론, phase, agent, sequence</div>
  </a>
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
