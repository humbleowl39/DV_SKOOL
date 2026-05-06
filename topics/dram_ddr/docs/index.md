# DRAM / DDR

> **DRAM & DDR Memory Controller 마스터 코스** — 셀 동작에서 PHY까지, DDR4/5 spec과 Memory Controller 검증 전략을 통합 학습.

<div class="course-header">
  <div class="course-stats">
    <div class="stat-item"><strong>4</strong>개 모듈 + Quick Ref</div>
    <div class="stat-item"><strong>중급 (Intermediate)</strong> 난이도</div>
  </div>
</div>

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

## 학습 모듈

<div class="course-grid">
  <a class="course-card" href="01_dram_fundamentals_ddr/">
    <div class="course-card-num">Module 01</div>
    <div class="course-card-title">DRAM Fundamentals + DDR4/5</div>
    <div class="course-card-desc">Cell, Bank, ROW/COL, ACT/PRE/RD/WR, DDR4↔DDR5 차이</div>
  </a>
  <a class="course-card" href="02_memory_controller/">
    <div class="course-card-num">Module 02</div>
    <div class="course-card-title">Memory Controller</div>
    <div class="course-card-desc">스케줄러, reordering, bank interleaving, refresh, ECC</div>
  </a>
  <a class="course-card" href="03_memory_interface_phy/">
    <div class="course-card-num">Module 03</div>
    <div class="course-card-title">Memory Interface / PHY</div>
    <div class="course-card-desc">PHY 아키텍처, DLL/PLL, training, write/read leveling</div>
  </a>
  <a class="course-card" href="04_dram_dv_methodology/">
    <div class="course-card-num">Module 04</div>
    <div class="course-card-title">DRAM DV Methodology</div>
    <div class="course-card-desc">검증 환경, traffic generator, refcheck, performance ref</div>
  </a>
  <a class="course-card" href="05_quick_reference_card/">
    <div class="course-card-num">Module 05</div>
    <div class="course-card-title">Quick Reference Card</div>
    <div class="course-card-desc">DDR4/5 timing parameter, MC 명령, DV 체크리스트</div>
  </a>
</div>

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
