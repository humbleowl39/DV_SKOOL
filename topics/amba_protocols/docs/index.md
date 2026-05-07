# AMBA Protocols

<!-- DV-SKOOL-HERO:start -->
<div class="topic-hero" data-cat="core">
  <div class="topic-hero-mark">🔄</div>
  <div class="topic-hero-body">
    <div class="topic-hero-title">AMBA Protocols</div>
    <p class="topic-hero-sub">ARM AMBA — APB, AHB, AXI, AXI-Stream</p>
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
  <a class="page-toc-link" href="#학습-팁">💡 학습 팁</a>
</div>
<!-- DV-SKOOL-TOC:end -->

## 🎯 학습 목표
코스를 마치면 다음을 할 수 있습니다:

- **Distinguish (분석)** APB / AHB / AXI / AXI-Stream의 핵심 차이를 핸드셰이크·신호·용도 기준으로 구분
- **Diagram (분석)** AXI 5채널 구조와 VALID/READY 핸드셰이크 타이밍을 화이트보드로 그리며 설명
- **Apply (적용)** Burst (FIXED/INCR/WRAP), Outstanding, ID 기반 OoO 트래픽을 시나리오로 작성
- **Implement (생성)** AXI-Stream의 TUSER/TKEEP/TLAST를 활용한 패킷 전송 검증 환경 설계
- **Evaluate (평가)** SoC 통합 시 어느 인터페이스에 어느 프로토콜을 쓸지 trade-off 기반 결정

## 📋 사전 지식
다음을 알고 있으면 본문이 매끄럽게 읽힙니다:

- **디지털 회로 기본**: 클럭 도메인, 동기 회로, FIFO
- **Handshake 개념**: ready/valid 류 흐름 제어
- **SystemVerilog 인터페이스 기본** (검증 적용 시)

UVM 검증 환경에서의 프로토콜 적용은 [UVM 코스](../uvm/) 참고.

## 🗺️ 개념 맵
<div class="concept-dag">
  <div class="concept-dag-title">개념 의존성 — 순서대로 학습 권장</div>
  <div class="concept-dag-row">
    <a class="concept-dag-node" href="01_apb_ahb/">
      <span class="concept-dag-node-num">M01</span>
      <span class="concept-dag-node-title">APB & AHB</span>
    </a>
    <span class="concept-dag-arrow">→</span>
    <a class="concept-dag-node" href="02_axi/">
      <span class="concept-dag-node-num">M02</span>
      <span class="concept-dag-node-title">AXI</span>
    </a>
    <span class="concept-dag-arrow">→</span>
    <a class="concept-dag-node" href="03_axi_stream/">
      <span class="concept-dag-node-num">M03</span>
      <span class="concept-dag-node-title">AXI-Stream</span>
    </a>
    <span class="concept-dag-arrow">→</span>
    <a class="concept-dag-node" href="04_quick_reference_card/">
      <span class="concept-dag-node-num">Ref</span>
      <span class="concept-dag-node-title">Quick Reference</span>
    </a>
  </div>
  <div class="concept-dag-legend">각 노드 = 모듈 (클릭하여 이동) · 화살표(→) = 선수 지식 흐름</div>
</div>

## 📚 학습 모듈
순차 학습 권장 (APB→AHB→AXI는 점진적 복잡도 증가):

<!-- DV-SKOOL-MODULES:start -->
<div class="module-grid">
  <a class="module-card" data-cat="core" href="01_apb_ahb/">
    <div class="module-num">01</div>
    <div class="module-body">
      <div class="module-title">Unit 1: APB & AHB</div>
    </div>
  </a>
  <a class="module-card" data-cat="core" href="02_axi/">
    <div class="module-num">02</div>
    <div class="module-body">
      <div class="module-title">AXI (Advanced eXtensible Interface)</div>
    </div>
  </a>
  <a class="module-card" data-cat="core" href="03_axi_stream/">
    <div class="module-num">03</div>
    <div class="module-body">
      <div class="module-title">AXI-Stream</div>
    </div>
  </a>
  <a class="module-card" data-cat="core" href="04_quick_reference_card/">
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
    <div class="pill-title">APB &amp; AHB</div>
  </div>
  <div class="path-arrow">▶</div>
  <div class="path-pill tier-core">
    <div class="pill-num">M02</div>
    <div class="pill-title">AXI</div>
  </div>
  <div class="path-arrow">▶</div>
  <div class="path-pill tier-adv">
    <div class="pill-num">M03</div>
    <div class="pill-title">AXI-Stream</div>
  </div>
  <div class="path-arrow">▶</div>
  <div class="path-pill tier-ref">
    <div class="pill-num">M04</div>
    <div class="pill-title">Quick Ref</div>
  </div>
</div>

**언제 어느 프로토콜?** APB = 레지스터 접근, AHB = 레거시 중간 성능, AXI = 고성능 메모리/IP 인터커넥트, AXI-Stream = 패킷/프레임 데이터 패스.

## 📖 관련 자료
- 📚 [**용어집 (Glossary)**](glossary.md) — AMBA 핵심 용어 ISO 11179 형식 정의
- 📝 [**퀴즈 (Quizzes)**](quiz/index.md) — 챕터별 5문항 (Bloom mix)
- 📋 [**코스 개요 & 컨셉 맵**](_legacy_overview.md) — AMBA 진화 역사와 SoC 적용 매핑

## 💡 학습 팁
!!! tip "효율적 학습"
    - **APB는 빠르게**: 가장 단순. SETUP→ACCESS 2단계 핸드셰이크만 이해하면 됨
    - **AXI는 깊게**: 5채널 분리 + outstanding이 핵심. VALID/READY 데드락 패턴 반드시 숙지
    - **AXI-Stream은 모델 차이로**: 주소 없는 데이터 패스 — memory-mapped와 다른 사고방식

!!! warning "흔한 버그"
    - **VALID 데드락**: Source가 READY 기다리며 VALID 안 올림 (절대 금지)
    - **WSTRB 누락**: AXI write에서 strobe 무시 → DUT가 잘못된 바이트 덮어씀
    - **AxLEN 오프셋**: AXI4 burst length는 N-1 인코딩 (16-beat = AxLEN=15)

<!-- DV-SKOOL-RELATED-TOPICS:start -->

## 🔗 관련 토픽
<div class="course-grid">
  <a class="course-card" href="https://humbleowl39.github.io/DV_SKOOL/uvm/">
    <div class="course-card-num">🧪 관련</div>
    <div class="course-card-title">UVM</div>
    <div class="course-card-desc">검증 방법론, phase, agent, sequence</div>
  </a>
  <a class="course-card" href="https://humbleowl39.github.io/DV_SKOOL/pcie/">
    <div class="course-card-num">🔌 관련</div>
    <div class="course-card-title">PCI Express</div>
    <div class="course-card-desc">TLP/DLLP, LTSSM, SR-IOV/CXL</div>
  </a>
  <a class="course-card" href="https://humbleowl39.github.io/DV_SKOOL/mmu/">
    <div class="course-card-num">🧭 관련</div>
    <div class="course-card-title">MMU</div>
    <div class="course-card-desc">페이지 테이블, TLB, IOMMU/SMMU</div>
  </a>
  <a class="course-card" href="https://humbleowl39.github.io/DV_SKOOL/formal_verification/">
    <div class="course-card-num">✅ 관련</div>
    <div class="course-card-title">Formal Verification</div>
    <div class="course-card-desc">SVA, JasperGold — 정형 검증</div>
  </a>
  <a class="course-card" href="https://humbleowl39.github.io/DV_SKOOL/" style="border-style:dashed;">
    <div class="course-card-num">🏠 HOME</div>
    <div class="course-card-title">DV SKOOL 홈</div>
    <div class="course-card-desc">전체 토픽 / 학습 경로 보기</div>
  </a>
</div>

<!-- DV-SKOOL-RELATED-TOPICS:end -->
