# TOE (TCP/IP Offload Engine)

> **TCP/IP Offload Engine 마스터 코스** — 호스트 CPU의 TCP/IP 처리 부담을 NIC HW로 옮기는 표준 architecture와 DV.

<div class="course-header">
  <div class="course-stats">
    <div class="stat-item"><strong>4</strong>개 모듈 + Quick Ref</div>
    <div class="stat-item"><strong>심화 (Advanced)</strong> 난이도</div>
  </div>
</div>

## 이 코스에서 얻는 것

- **Trace** TCP/IP 스택 처리를 host SW vs TOE HW로 비교 추적
- **Diagram** TOE의 connection state machine + segment processing pipeline
- **Apply** TX/RX path, ARP, checksum offload, RSS 시나리오 매핑
- **Plan** TOE DV 환경 (packet generator, connection model, error injection)

## 사전 지식

- TCP/IP 스택 (3-way handshake, sliding window, congestion control 기본)
- NIC 동작 원리
- AMBA AXI / AXI-Stream

## 🗺️ 학습 경로

<div class="concept-dag">
  <div class="concept-dag-title">개념 의존성 — 순서대로 학습 권장</div>
  <div class="concept-dag-row">
    <a class="concept-dag-node" href="01_tcp_ip_and_toe_concept/">
      <span class="concept-dag-node-num">M01</span>
      <span class="concept-dag-node-title">TCP/IP & TOE</span>
    </a>
    <span class="concept-dag-arrow">→</span>
    <a class="concept-dag-node" href="02_toe_architecture/">
      <span class="concept-dag-node-num">M02</span>
      <span class="concept-dag-node-title">TOE Architecture</span>
    </a>
    <span class="concept-dag-arrow">→</span>
    <a class="concept-dag-node" href="03_toe_key_functions/">
      <span class="concept-dag-node-num">M03</span>
      <span class="concept-dag-node-title">Key Functions</span>
    </a>
    <span class="concept-dag-arrow">→</span>
    <a class="concept-dag-node" href="04_toe_dv_methodology/">
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
  <a class="course-card" href="01_tcp_ip_and_toe_concept/">
    <div class="course-card-num">Module 01</div>
    <div class="course-card-title">TCP/IP &amp; TOE Concept</div>
    <div class="course-card-desc">TCP/IP 기본, TOE 등장 동기, partial vs full offload</div>
  </a>
  <a class="course-card" href="02_toe_architecture/">
    <div class="course-card-num">Module 02</div>
    <div class="course-card-title">TOE Architecture</div>
    <div class="course-card-desc">Connection table, TX/RX pipeline, host interface</div>
  </a>
  <a class="course-card" href="03_toe_key_functions/">
    <div class="course-card-num">Module 03</div>
    <div class="course-card-title">TOE Key Functions</div>
    <div class="course-card-desc">Checksum, ARP, RSS, segmentation, retransmission</div>
  </a>
  <a class="course-card" href="04_toe_dv_methodology/">
    <div class="course-card-num">Module 04</div>
    <div class="course-card-title">TOE DV Methodology</div>
    <div class="course-card-desc">Connection state coverage, packet generator, error scenarios</div>
  </a>
  <a class="course-card" href="05_quick_reference_card/">
    <div class="course-card-num">Module 05</div>
    <div class="course-card-title">Quick Reference Card</div>
    <div class="course-card-desc">TCP state machine, header, DV 체크리스트</div>
  </a>
</div>

## 학습 경로

<div class="path-chain">
  <div class="path-pill tier-core">
    <div class="pill-num">M01</div>
    <div class="pill-title">Concept</div>
  </div>
  <div class="path-arrow">▶</div>
  <div class="path-pill tier-core">
    <div class="pill-num">M02</div>
    <div class="pill-title">Architecture</div>
  </div>
  <div class="path-arrow">▶</div>
  <div class="path-pill tier-adv">
    <div class="pill-num">M03</div>
    <div class="pill-title">Key Functions</div>
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

- 📚 [**용어집**](glossary.md)
- 📝 [**퀴즈**](quiz/index.md)
- 📋 [**코스 개요**](_legacy_overview.md)
