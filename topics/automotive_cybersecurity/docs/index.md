# Automotive Cybersecurity

> **Automotive Cybersecurity 마스터 코스** — CAN bus부터 자율주행 보안까지, 차량 보안의 모든 것.

<div class="course-header">
  <div class="course-stats">
    <div class="stat-item"><strong>4</strong>개 모듈 + Quick Ref</div>
    <div class="stat-item"><strong>중급 (Intermediate)</strong> 난이도</div>
  </div>
</div>

## 이 코스에서 얻는 것

- **Diagram** CAN bus 동작과 보안 한계
- **Apply** Automotive SoC 보안 (HSM, secure boot, OTA update)
- **Analyze** Tesla FSD jailbreak 사례에서 배우는 보안 약점
- **Plan** Attack surface map과 layered defense 전략

## 사전 지식

- 임베디드 시스템 기본
- 네트워크 / 보안 일반 ([SoC Secure Boot](../../soc_secure_boot/) 참고)

## 🗺️ 학습 경로

<div class="concept-dag">
  <div class="concept-dag-title">개념 의존성 — 순서대로 학습 권장</div>
  <div class="concept-dag-row">
    <a class="concept-dag-node" href="01_can_bus_fundamentals/">
      <span class="concept-dag-node-num">M01</span>
      <span class="concept-dag-node-title">CAN Bus</span>
    </a>
    <span class="concept-dag-arrow">→</span>
    <a class="concept-dag-node" href="02_automotive_soc_security/">
      <span class="concept-dag-node-num">M02</span>
      <span class="concept-dag-node-title">Automotive SoC Security</span>
    </a>
    <span class="concept-dag-arrow">→</span>
    <a class="concept-dag-node" href="03_tesla_fsd_case_study/">
      <span class="concept-dag-node-num">M03</span>
      <span class="concept-dag-node-title">Tesla FSD Case</span>
    </a>
    <span class="concept-dag-arrow">→</span>
    <a class="concept-dag-node" href="04_attack_surface_and_defense/">
      <span class="concept-dag-node-num">M04</span>
      <span class="concept-dag-node-title">Attack & Defense</span>
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

<div class="course-grid">
  <a class="course-card" href="01_can_bus_fundamentals/">
    <div class="course-card-num">Module 01</div>
    <div class="course-card-title">CAN Bus Fundamentals</div>
    <div class="course-card-desc">CAN 프로토콜, ECU 통신, 보안 한계</div>
  </a>
  <a class="course-card" href="02_automotive_soc_security/">
    <div class="course-card-num">Module 02</div>
    <div class="course-card-title">Automotive SoC Security</div>
    <div class="course-card-desc">HSM, Secure Boot, OTA, ISO 21434</div>
  </a>
  <a class="course-card" href="03_tesla_fsd_case_study/">
    <div class="course-card-num">Module 03</div>
    <div class="course-card-title">Tesla FSD Case Study</div>
    <div class="course-card-desc">FSD jailbreak 사례 분석 (voltage glitch, MMU disable)</div>
  </a>
  <a class="course-card" href="04_attack_surface_and_defense/">
    <div class="course-card-num">Module 04</div>
    <div class="course-card-title">Attack Surface &amp; Defense</div>
    <div class="course-card-desc">차량 attack surface map, layered defense</div>
  </a>
  <a class="course-card" href="05_quick_reference_card/">
    <div class="course-card-num">Module 05</div>
    <div class="course-card-title">Quick Reference Card</div>
    <div class="course-card-desc">CAN/HSM/SecOC 치트시트</div>
  </a>
</div>

## 학습 경로

<div class="path-chain">
  <div class="path-pill tier-core">
    <div class="pill-num">M01</div>
    <div class="pill-title">CAN Bus</div>
  </div>
  <div class="path-arrow">▶</div>
  <div class="path-pill tier-core">
    <div class="pill-num">M02</div>
    <div class="pill-title">SoC Security</div>
  </div>
  <div class="path-arrow">▶</div>
  <div class="path-pill tier-adv">
    <div class="pill-num">M03</div>
    <div class="pill-title">Tesla Case</div>
  </div>
  <div class="path-arrow">▶</div>
  <div class="path-pill tier-adv">
    <div class="pill-num">M04</div>
    <div class="pill-title">Attack &amp; Defense</div>
  </div>
  <div class="path-arrow">▶</div>
  <div class="path-pill tier-ref">
    <div class="pill-num">M05</div>
    <div class="pill-title">Quick Ref</div>
  </div>
</div>

## 관련 자료

- 📚 [**용어집**](glossary.md)
- 📝 [**퀴즈**](quiz/index.md)
- 📋 [**코스 개요**](_legacy_overview.md)
