# UVM (Universal Verification Methodology)

> **검증 엔지니어를 위한 UVM 마스터 코스** — 클래스 계층, Phase, Agent, Sequence, Factory, TLM, Coverage까지 6년+ 실무자 관점으로 통합 학습.

<div class="course-header">
  <div class="course-stats">
    <div class="stat-item"><strong>7</strong>개 모듈 + Quick Ref</div>
    <div class="stat-item"><strong>심화 (Advanced)</strong> 난이도</div>
  </div>
</div>

## 이 코스에서 얻는 것

코스를 마치면 다음을 할 수 있습니다:

- **Diagram (분석)** UVM 클래스 계층 전체와 Phase 실행 순서를 화이트보드로 그리며 설계 의사결정을 설명
- **Design (생성)** Agent/Driver/Monitor 구조를 Active/Passive 모드를 구분해 설계
- **Apply (적용)** Sequence + Virtual Sequence + Factory Override로 다양한 시나리오를 재사용 가능하게 구성
- **Analyze (분석)** config_db 계층 전달, TLM 포트 연결, Scoreboard 비교 로직을 트레이스
- **Evaluate (평가)** UVM 실무 패턴/안티패턴을 식별하고 코드 리뷰에서 근거 있는 피드백 제공

## 사전 지식

이 코스는 **심화** 과정입니다. 다음 항목을 알고 있어야 본문이 매끄럽게 읽힙니다:

- **SystemVerilog 객체지향**: class, virtual function/task, polymorphism, parameterized class
- **랜덤화**: `randomize()`, constraint, `rand`/`randc` 차이
- **Interface & modport**: virtual interface 개념
- **시뮬레이터 사용 경험**: VCS / Questa / Xcelium 중 하나로 +runtest, +UVM_TESTNAME 등의 경험

부족한 부분이 있다면 [SystemVerilog IEEE 1800](https://standards.ieee.org/ieee/1800/) 사양서나 *SystemVerilog for Verification* (Spear) 1-7장을 먼저 보세요.

## 🗺️ 학습 경로

<div class="concept-dag dag-long">
  <div class="concept-dag-title">개념 의존성 — 순서대로 학습 권장</div>
  <div class="concept-dag-row">
    <a class="concept-dag-node" href="01_architecture_and_phase/">
      <span class="concept-dag-node-num">M01</span>
      <span class="concept-dag-node-title">Architecture & Phase</span>
    </a>
    <span class="concept-dag-arrow">→</span>
    <a class="concept-dag-node" href="02_agent_driver_monitor/">
      <span class="concept-dag-node-num">M02</span>
      <span class="concept-dag-node-title">Agent / Driver / Monitor</span>
    </a>
    <span class="concept-dag-arrow">→</span>
    <a class="concept-dag-node" href="03_sequence_and_item/">
      <span class="concept-dag-node-num">M03</span>
      <span class="concept-dag-node-title">Sequence & Item</span>
    </a>
    <span class="concept-dag-arrow">→</span>
    <a class="concept-dag-node" href="04_config_db_factory/">
      <span class="concept-dag-node-num">M04</span>
      <span class="concept-dag-node-title">config_db & Factory</span>
    </a>
  </div>
  <div class="concept-dag-row">
    <span class="concept-dag-arrow">↪</span>
    <a class="concept-dag-node" href="05_tlm_scoreboard_coverage/">
      <span class="concept-dag-node-num">M05</span>
      <span class="concept-dag-node-title">TLM / Scoreboard / Coverage</span>
    </a>
    <span class="concept-dag-arrow">→</span>
    <a class="concept-dag-node" href="06_practical_patterns/">
      <span class="concept-dag-node-num">M06</span>
      <span class="concept-dag-node-title">실무 패턴</span>
    </a>
    <span class="concept-dag-arrow">→</span>
    <a class="concept-dag-node" href="07_quick_reference_card/">
      <span class="concept-dag-node-num">Ref</span>
      <span class="concept-dag-node-title">Quick Reference</span>
    </a>
  </div>
  <div class="concept-dag-legend">각 노드 = 모듈 (클릭하여 이동) · 화살표(→) = 선수 지식 흐름</div>
</div>

## 학습 모듈

순차 학습을 권장합니다 (특히 1→4까지). 5~7은 토픽 단위로도 가능합니다.

<div class="course-grid">
  <a class="course-card" href="01_architecture_and_phase/">
    <div class="course-card-num">Module 01</div>
    <div class="course-card-title">UVM 아키텍처 &amp; Phase</div>
    <div class="course-card-desc">클래스 계층, Phase 실행 모델, Top-Down vs Bottom-Up</div>
  </a>
  <a class="course-card" href="02_agent_driver_monitor/">
    <div class="course-card-num">Module 02</div>
    <div class="course-card-title">Agent / Driver / Monitor</div>
    <div class="course-card-desc">DUT 인터페이스 컴포넌트, Active/Passive 분리, VIF 연결</div>
  </a>
  <a class="course-card" href="03_sequence_and_item/">
    <div class="course-card-num">Module 03</div>
    <div class="course-card-title">Sequence &amp; Sequence Item</div>
    <div class="course-card-desc">자극 생성 모델, body() 패턴, Virtual Sequence 조합</div>
  </a>
  <a class="course-card" href="04_config_db_factory/">
    <div class="course-card-num">Module 04</div>
    <div class="course-card-title">config_db &amp; Factory</div>
    <div class="course-card-desc">계층 설정 전달, Type/Instance Override 의사결정</div>
  </a>
  <a class="course-card" href="05_tlm_scoreboard_coverage/">
    <div class="course-card-num">Module 05</div>
    <div class="course-card-title">TLM, Scoreboard, Coverage</div>
    <div class="course-card-desc">Analysis Port 통신, 비교 모델, 커버리지 클로저</div>
  </a>
  <a class="course-card" href="06_practical_patterns/">
    <div class="course-card-num">Module 06</div>
    <div class="course-card-title">실무 패턴 &amp; 안티패턴</div>
    <div class="course-card-desc">현장에서 반복되는 좋은 설계 vs 피해야 할 함정</div>
  </a>
  <a class="course-card" href="07_quick_reference_card/">
    <div class="course-card-num">Module 07</div>
    <div class="course-card-title">Quick Reference Card</div>
    <div class="course-card-desc">실무 치트시트 — 매크로, 패턴, 디버그 팁</div>
  </a>
</div>

## 학습 경로

코어(Module 01-04) → 심화(05-06) → 참조(07) 순서로 의존성이 있습니다.

<div class="path-chain">
  <div class="path-pill tier-core">
    <div class="pill-num">M01</div>
    <div class="pill-title">아키텍처 &amp; Phase</div>
  </div>
  <div class="path-arrow">▶</div>
  <div class="path-pill tier-core">
    <div class="pill-num">M02</div>
    <div class="pill-title">Agent/Drv/Mon</div>
  </div>
  <div class="path-arrow">▶</div>
  <div class="path-pill tier-core">
    <div class="pill-num">M03</div>
    <div class="pill-title">Sequence</div>
  </div>
  <div class="path-arrow">▶</div>
  <div class="path-pill tier-core">
    <div class="pill-num">M04</div>
    <div class="pill-title">config_db &amp; Factory</div>
  </div>
  <div class="path-arrow">▶</div>
  <div class="path-pill tier-adv">
    <div class="pill-num">M05</div>
    <div class="pill-title">TLM/SB/Coverage</div>
  </div>
  <div class="path-arrow">▶</div>
  <div class="path-pill tier-adv">
    <div class="pill-num">M06</div>
    <div class="pill-title">실무 패턴</div>
  </div>
  <div class="path-arrow">▶</div>
  <div class="path-pill tier-ref">
    <div class="pill-num">M07</div>
    <div class="pill-title">Quick Ref</div>
  </div>
</div>

**Tier 색상**: <span style="color:#1976d2">■</span> 코어 (M01-M04, 강한 의존) ・ <span style="color:#6a1b9a">■</span> 심화 (M05-M06) ・ <span style="color:#e65100">■</span> 참조 (M07, 치트시트)

## 코스 운영 방식

각 모듈은 다음 순서로 구성됩니다:

1. **학습 목표** — 모듈 완료 후 할 수 있는 것 (Bloom's Taxonomy 동사)
2. **사전 지식** — 본 모듈에 필요한 선행 학습 항목
3. **본문** — 핵심 개념 + 예제 코드 + 다이어그램
4. **워크스루 (Walkthrough)** — 단계별 실습 시나리오
5. **연습문제** — 직접 풀어보는 문항 + 모범 답안
6. **핵심 정리** — 5~7개의 압축된 takeaway
7. **퀴즈** — 이해도 점검 (별도 페이지)

## 관련 자료

- 📚 [**용어집 (Glossary)**](glossary.md) — UVM 핵심 용어 ISO 11179 형식 정의
- 📝 [**퀴즈 (Quizzes)**](quiz/index.md) — 챕터별 5-8문항 (Bloom mix)
- 📋 [**코스 개요 & 컨셉 맵**](_legacy_overview.md) — 학습 단위 개요와 이력서 매핑

## 학습 팁

!!! tip "효율적 학습"
    - **순서 고수**: Module 01-04는 강한 의존이 있으므로 순차 학습
    - **퀴즈 즉시**: 각 모듈 끝나면 바로 퀴즈 풀고 본문 재방문
    - **코드 직접 작성**: 본문 코드는 읽기만 말고 실제 시뮬레이터에서 컴파일/실행
    - **다이어그램 화이트보드**: 클래스 계층/Phase 흐름은 자기 손으로 그릴 수 있어야 함

!!! warning "안티패턴 경계"
    UVM 실무에서 가장 자주 발생하는 문제는 **Phase 오해**, **config_db 경로 불일치**, **Factory Override 누락**입니다. Module 06에서 별도 다룹니다.

<!-- DV-SKOOL-RELATED-TOPICS:start -->

## 관련 토픽

<div class="course-grid">
  <a class="course-card" href="https://humbleowl39.github.io/DV_SKOOL/amba_protocols/">
    <div class="course-card-num">🔄 관련</div>
    <div class="course-card-title">AMBA Protocols</div>
    <div class="course-card-desc">APB/AHB/AXI — 표준 버스 프로토콜</div>
  </a>
  <a class="course-card" href="https://humbleowl39.github.io/DV_SKOOL/formal_verification/">
    <div class="course-card-num">✅ 관련</div>
    <div class="course-card-title">Formal Verification</div>
    <div class="course-card-desc">SVA, JasperGold — 정형 검증</div>
  </a>
  <a class="course-card" href="https://humbleowl39.github.io/DV_SKOOL/soc_integration_cctv/">
    <div class="course-card-num">🏗️ 관련</div>
    <div class="course-card-title">SoC Integration</div>
    <div class="course-card-desc">Top-level integration, TB top</div>
  </a>
  <a class="course-card" href="https://humbleowl39.github.io/DV_SKOOL/bigtech_algorithm/">
    <div class="course-card-num">📐 관련</div>
    <div class="course-card-title">BigTech Algorithm</div>
    <div class="course-card-desc">Big-O, 자료구조, 알고리즘</div>
  </a>
  <a class="course-card" href="https://humbleowl39.github.io/DV_SKOOL/" style="border-style:dashed;">
    <div class="course-card-num">🏠 HOME</div>
    <div class="course-card-title">DV SKOOL 홈</div>
    <div class="course-card-desc">전체 토픽 / 학습 경로 보기</div>
  </a>
</div>

<!-- DV-SKOOL-RELATED-TOPICS:end -->
