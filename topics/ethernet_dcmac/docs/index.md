# Ethernet DCMAC

> **Ethernet & DCMAC 마스터 코스** — 프레임 구조부터 100/400G DCMAC 검증까지.

<div class="course-header">
  <div class="course-stats">
    <div class="stat-item"><strong>3</strong>개 모듈 + Quick Ref</div>
    <div class="stat-item"><strong>심화 (Advanced)</strong> 난이도</div>
  </div>
</div>

## 이 코스에서 얻는 것

- **Diagram** Ethernet 프레임 구조와 OSI 1-2 layer 매핑
- **Distinguish** GbE / 10GbE / 100GbE / 400GbE 차이와 DCMAC의 위치
- **Apply** PCS / FEC / MAC layer의 책임 분리 및 검증 시나리오
- **Plan** DCMAC DV 환경 (traffic generator, packet checker, FEC injection)

## 사전 지식

- OSI 모델 (특히 L1/L2)
- MAC vs PHY 분리 개념
- 패킷 / 프레임 / 패딩 같은 네트워킹 기본 용어

## 학습 모듈

<div class="course-grid">
  <a class="course-card" href="01_ethernet_fundamentals/">
    <div class="course-card-num">Module 01</div>
    <div class="course-card-title">Ethernet Fundamentals</div>
    <div class="course-card-desc">프레임 구조, MAC address, VLAN, 100/400GbE 표준</div>
  </a>
  <a class="course-card" href="02_dcmac_architecture/">
    <div class="course-card-num">Module 02</div>
    <div class="course-card-title">DCMAC Architecture</div>
    <div class="course-card-desc">DCMAC 블럭 구조, PCS/FEC/MAC 인터페이스, multi-channel</div>
  </a>
  <a class="course-card" href="03_dcmac_dv_methodology/">
    <div class="course-card-num">Module 03</div>
    <div class="course-card-title">DCMAC DV Methodology</div>
    <div class="course-card-desc">Packet generator, scoreboard, FEC injection, performance</div>
  </a>
  <a class="course-card" href="04_quick_reference_card/">
    <div class="course-card-num">Module 04</div>
    <div class="course-card-title">Quick Reference Card</div>
    <div class="course-card-desc">프레임 형식, FEC RS(528,514), DV 체크리스트</div>
  </a>
</div>

## 학습 경로

<div class="path-chain">
  <div class="path-pill tier-core">
    <div class="pill-num">M01</div>
    <div class="pill-title">Ethernet Fundamentals</div>
  </div>
  <div class="path-arrow">▶</div>
  <div class="path-pill tier-core">
    <div class="pill-num">M02</div>
    <div class="pill-title">DCMAC Architecture</div>
  </div>
  <div class="path-arrow">▶</div>
  <div class="path-pill tier-adv">
    <div class="pill-num">M03</div>
    <div class="pill-title">DV</div>
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
