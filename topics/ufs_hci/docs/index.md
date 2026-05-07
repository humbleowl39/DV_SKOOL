# UFS HCI

> **UFS Host Controller Interface 마스터 코스** — 프로토콜 스택, HCI 아키텍처, UPIU 흐름, DV 방법론.

<div class="course-header">
  <div class="course-stats">
    <div class="stat-item"><strong>4</strong>개 모듈 + Quick Ref</div>
    <div class="stat-item"><strong>심화 (Advanced)</strong> 난이도</div>
  </div>
</div>

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

<div class="course-grid">
  <a class="course-card" href="01_ufs_protocol_stack/">
    <div class="course-card-num">Module 01</div>
    <div class="course-card-title">UFS Protocol Stack</div>
    <div class="course-card-desc">5계층 (UTP/UPIU/UniPro/M-PHY/Storage), JEDEC vs MIPI 매핑</div>
  </a>
  <a class="course-card" href="02_hci_architecture/">
    <div class="course-card-num">Module 02</div>
    <div class="course-card-title">HCI Architecture</div>
    <div class="course-card-desc">Register, UTRD/UTMRD, doorbell, interrupt aggregation</div>
  </a>
  <a class="course-card" href="03_upiu_command_flow/">
    <div class="course-card-num">Module 03</div>
    <div class="course-card-title">UPIU &amp; Command Flow</div>
    <div class="course-card-desc">UPIU 형식, SCSI command 매핑, READ/WRITE/QUERY 흐름</div>
  </a>
  <a class="course-card" href="04_hci_dv_methodology/">
    <div class="course-card-num">Module 04</div>
    <div class="course-card-title">HCI DV Methodology</div>
    <div class="course-card-desc">UFS device model, command coverage, error injection</div>
  </a>
  <a class="course-card" href="05_quick_reference_card/">
    <div class="course-card-num">Module 05</div>
    <div class="course-card-title">Quick Reference Card</div>
    <div class="course-card-desc">UPIU 형식, register map, DV 체크리스트</div>
  </a>
</div>

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
