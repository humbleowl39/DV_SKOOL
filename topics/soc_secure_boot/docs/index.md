# SoC Secure Boot

> **SoC Secure Boot 마스터 코스** — Hardware Root of Trust부터 BootROM DV까지, 안전한 부팅의 모든 것.

<div class="course-header">
  <div class="course-stats">
    <div class="stat-item"><strong>6</strong>개 모듈 + Quick Ref</div>
    <div class="stat-item"><strong>심화 (Advanced)</strong> 난이도</div>
  </div>
</div>

## 이 코스에서 얻는 것

- **Trace** 부팅 단계별 신뢰 체인 (BootROM → BL1 → BL2 → BL31 → kernel)
- **Apply** Hardware Root of Trust 구현 (eFuse, OTP, secure key storage)
- **Identify** Secure Boot에 사용되는 암호 알고리즘 (RSA, ECDSA, SHA-256/384, AES)
- **Analyze** 공격 표면 (fault injection, side-channel, supply chain)과 방어 메커니즘
- **Plan** BootROM DV 검증 방법론 (시나리오 매트릭스, golden image, fault injection)

## 사전 지식

- 암호 기본 (해시, 서명, 대칭/비대칭)
- 부팅 sequence 일반 (POR, reset, boot loader)
- ARM TrustZone 기본 ([ARM Security 코스](../../arm_security/) 참고)

## 🗺️ 학습 경로

<div class="concept-dag dag-long">
  <div class="concept-dag-title">개념 의존성 — 순서대로 학습 권장</div>
  <div class="concept-dag-row">
    <a class="concept-dag-node" href="01_hardware_root_of_trust/">
      <span class="concept-dag-node-num">M01</span>
      <span class="concept-dag-node-title">HW Root of Trust</span>
    </a>
    <span class="concept-dag-arrow">→</span>
    <a class="concept-dag-node" href="02_chain_of_trust_boot_stages/">
      <span class="concept-dag-node-num">M02</span>
      <span class="concept-dag-node-title">Chain of Trust</span>
    </a>
    <span class="concept-dag-arrow">→</span>
    <a class="concept-dag-node" href="03_crypto_in_boot/">
      <span class="concept-dag-node-num">M03</span>
      <span class="concept-dag-node-title">Crypto in Boot</span>
    </a>
    <span class="concept-dag-arrow">→</span>
    <a class="concept-dag-node" href="04_boot_device_and_boot_mode/">
      <span class="concept-dag-node-num">M04</span>
      <span class="concept-dag-node-title">Boot Device / Mode</span>
    </a>
  </div>
  <div class="concept-dag-row">
    <span class="concept-dag-arrow">↪</span>
    <a class="concept-dag-node" href="05_attack_surface_and_defense/">
      <span class="concept-dag-node-num">M05</span>
      <span class="concept-dag-node-title">Attack & Defense</span>
    </a>
    <span class="concept-dag-arrow">→</span>
    <a class="concept-dag-node" href="06_quick_reference_card/">
      <span class="concept-dag-node-num">M06</span>
      <span class="concept-dag-node-title">Quick Reference</span>
    </a>
    <span class="concept-dag-arrow">→</span>
    <a class="concept-dag-node" href="07_bootrom_dv_methodology/">
      <span class="concept-dag-node-num">M07</span>
      <span class="concept-dag-node-title">BootROM DV</span>
    </a>
  </div>
  <div class="concept-dag-legend">각 노드 = 모듈 (클릭하여 이동) · 화살표(→) = 선수 지식 흐름</div>
</div>

## 학습 모듈

<div class="course-grid">
  <a class="course-card" href="01_hardware_root_of_trust/">
    <div class="course-card-num">Module 01</div>
    <div class="course-card-title">Hardware Root of Trust</div>
    <div class="course-card-desc">eFuse/OTP, secure key storage, immutable boot code</div>
  </a>
  <a class="course-card" href="02_chain_of_trust_boot_stages/">
    <div class="course-card-num">Module 02</div>
    <div class="course-card-title">Chain of Trust & Boot Stages</div>
    <div class="course-card-desc">BootROM → BL1 → BL2 → BL31 → kernel, 단계별 검증</div>
  </a>
  <a class="course-card" href="03_crypto_in_boot/">
    <div class="course-card-num">Module 03</div>
    <div class="course-card-title">Crypto in Boot</div>
    <div class="course-card-desc">RSA/ECDSA 서명, SHA hash, AES 암호화</div>
  </a>
  <a class="course-card" href="04_boot_device_and_boot_mode/">
    <div class="course-card-num">Module 04</div>
    <div class="course-card-title">Boot Device &amp; Boot Mode</div>
    <div class="course-card-desc">eMMC/UFS/QSPI, boot mode strap, fail-over</div>
  </a>
  <a class="course-card" href="05_attack_surface_and_defense/">
    <div class="course-card-num">Module 05</div>
    <div class="course-card-title">Attack Surface &amp; Defense</div>
    <div class="course-card-desc">Fault injection, side-channel, supply chain 방어</div>
  </a>
  <a class="course-card" href="07_bootrom_dv_methodology/">
    <div class="course-card-num">Module 06</div>
    <div class="course-card-title">BootROM DV Methodology</div>
    <div class="course-card-desc">시나리오 매트릭스, golden image, fault injection</div>
  </a>
  <a class="course-card" href="06_quick_reference_card/">
    <div class="course-card-num">Module 07</div>
    <div class="course-card-title">Quick Reference Card</div>
    <div class="course-card-desc">Boot flow, crypto algo, attack 패턴 치트시트</div>
  </a>
</div>

## 학습 경로

<div class="path-chain">
  <div class="path-pill tier-core">
    <div class="pill-num">M01</div>
    <div class="pill-title">HW RoT</div>
  </div>
  <div class="path-arrow">▶</div>
  <div class="path-pill tier-core">
    <div class="pill-num">M02</div>
    <div class="pill-title">Chain of Trust</div>
  </div>
  <div class="path-arrow">▶</div>
  <div class="path-pill tier-core">
    <div class="pill-num">M03</div>
    <div class="pill-title">Crypto</div>
  </div>
  <div class="path-arrow">▶</div>
  <div class="path-pill tier-adv">
    <div class="pill-num">M04</div>
    <div class="pill-title">Boot Device</div>
  </div>
  <div class="path-arrow">▶</div>
  <div class="path-pill tier-adv">
    <div class="pill-num">M05</div>
    <div class="pill-title">Attack &amp; Defense</div>
  </div>
  <div class="path-arrow">▶</div>
  <div class="path-pill tier-adv">
    <div class="pill-num">M06</div>
    <div class="pill-title">DV</div>
  </div>
  <div class="path-arrow">▶</div>
  <div class="path-pill tier-ref">
    <div class="pill-num">M07</div>
    <div class="pill-title">Quick Ref</div>
  </div>
</div>

## 관련 자료

- 📚 [**용어집**](glossary.md)
- 📝 [**퀴즈**](quiz/index.md)
- 📋 [**코스 개요**](_legacy_overview.md)
