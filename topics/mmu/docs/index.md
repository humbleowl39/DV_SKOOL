# MMU

> **Memory Management Unit 마스터 코스** — 가상↔물리 주소 변환의 모든 것. 페이지 테이블, TLB, IOMMU/SMMU, 성능 분석, DV 방법론까지.

<div class="course-header">
  <div class="course-stats">
    <div class="stat-item"><strong>6</strong>개 모듈 + Quick Ref</div>
    <div class="stat-item"><strong>심화 (Advanced)</strong> 난이도</div>
  </div>
</div>

## 이 코스에서 얻는 것

- **Trace (분석)** 가상→물리 주소 변환의 multi-level page table walk 전 과정 추적
- **Diagram (분석)** TLB, multi-level translation, IOMMU의 데이터 흐름과 캐시 계층 그리기
- **Apply (적용)** ARMv8 4-level translation 및 SMMU stage 1/2를 시나리오에 매핑
- **Analyze (분석)** TLB miss penalty, page fault, page walk caching의 성능 영향 정량 분석
- **Design (생성)** Dual-Reference Model 기반 MMU DV 환경 + Custom Thin VIP 설계

## 사전 지식

- **CPU 아키텍처 기본**: 가상/물리 주소 개념, 명령어 사이클
- **캐시 계층 이해**: L1/L2/L3, hit/miss, line size
- **OS 메모리 관리 기초**: 프로세스별 가상 주소 공간, 페이지
- **AMBA AXI** (Module 04 IOMMU에서 transaction 분석 시 도움)

## 🗺️ 학습 경로

<div class="concept-dag">
  <div class="concept-dag-title">개념 의존성 — 순서대로 학습 권장</div>
  <div class="concept-dag-row">
    <a class="concept-dag-node" href="01_mmu_fundamentals/">
      <span class="concept-dag-node-num">M01</span>
      <span class="concept-dag-node-title">MMU Fundamentals</span>
    </a>
    <span class="concept-dag-arrow">→</span>
    <a class="concept-dag-node" href="02_page_table_structure/">
      <span class="concept-dag-node-num">M02</span>
      <span class="concept-dag-node-title">Page Table</span>
    </a>
    <span class="concept-dag-arrow">→</span>
    <a class="concept-dag-node" href="03_tlb/">
      <span class="concept-dag-node-num">M03</span>
      <span class="concept-dag-node-title">TLB</span>
    </a>
    <span class="concept-dag-arrow">→</span>
    <a class="concept-dag-node" href="04_iommu_smmu/">
      <span class="concept-dag-node-num">M04</span>
      <span class="concept-dag-node-title">IOMMU / SMMU</span>
    </a>
  </div>
  <div class="concept-dag-row">
    <span class="concept-dag-arrow">↪</span>
    <a class="concept-dag-node" href="05_performance_analysis/">
      <span class="concept-dag-node-num">M05</span>
      <span class="concept-dag-node-title">Performance</span>
    </a>
    <span class="concept-dag-arrow">→</span>
    <a class="concept-dag-node" href="06_mmu_dv_methodology/">
      <span class="concept-dag-node-num">M06</span>
      <span class="concept-dag-node-title">DV Methodology</span>
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

<div class="course-grid">
  <a class="course-card" href="01_mmu_fundamentals/">
    <div class="course-card-num">Module 01</div>
    <div class="course-card-title">MMU Fundamentals</div>
    <div class="course-card-desc">왜 VA가 필요한가, 주소 변환 기본 원리, MMU의 위치</div>
  </a>
  <a class="course-card" href="02_page_table_structure/">
    <div class="course-card-num">Module 02</div>
    <div class="course-card-title">Page Table Structure</div>
    <div class="course-card-desc">Multi-level page table, ARMv8 4-level translation, granule</div>
  </a>
  <a class="course-card" href="03_tlb/">
    <div class="course-card-num">Module 03</div>
    <div class="course-card-title">TLB</div>
    <div class="course-card-desc">TLB 구조 / replace policy / shootdown / ASID/VMID 태깅</div>
  </a>
  <a class="course-card" href="04_iommu_smmu/">
    <div class="course-card-num">Module 04</div>
    <div class="course-card-title">IOMMU / SMMU</div>
    <div class="course-card-desc">왜 IOMMU 필요? ARM SMMU 아키텍처, Stage 1/2, StreamID</div>
  </a>
  <a class="course-card" href="05_performance_analysis/">
    <div class="course-card-num">Module 05</div>
    <div class="course-card-title">Performance Analysis</div>
    <div class="course-card-desc">TLB miss penalty / page walk caching / Dual-Reference Model</div>
  </a>
  <a class="course-card" href="06_mmu_dv_methodology/">
    <div class="course-card-num">Module 06</div>
    <div class="course-card-title">MMU DV Methodology</div>
    <div class="course-card-desc">검증 아키텍처, Custom Thin VIP, RAL, 시나리오 매트릭스</div>
  </a>
  <a class="course-card" href="07_quick_reference_card/">
    <div class="course-card-num">Module 07</div>
    <div class="course-card-title">Quick Reference Card</div>
    <div class="course-card-desc">주소 변환 / TLB / SMMU 치트시트</div>
  </a>
</div>

## 학습 경로

<div class="path-chain">
  <div class="path-pill tier-core">
    <div class="pill-num">M01</div>
    <div class="pill-title">Fundamentals</div>
  </div>
  <div class="path-arrow">▶</div>
  <div class="path-pill tier-core">
    <div class="pill-num">M02</div>
    <div class="pill-title">Page Table</div>
  </div>
  <div class="path-arrow">▶</div>
  <div class="path-pill tier-core">
    <div class="pill-num">M03</div>
    <div class="pill-title">TLB</div>
  </div>
  <div class="path-arrow">▶</div>
  <div class="path-pill tier-adv">
    <div class="pill-num">M04</div>
    <div class="pill-title">IOMMU/SMMU</div>
  </div>
  <div class="path-arrow">▶</div>
  <div class="path-pill tier-adv">
    <div class="pill-num">M05</div>
    <div class="pill-title">Performance</div>
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

- 📚 [**용어집 (Glossary)**](glossary.md) — MMU 핵심 용어 ISO 11179 형식
- 📝 [**퀴즈 (Quizzes)**](quiz/index.md) — 챕터별 5문항 (Bloom mix)
- 📋 [**코스 개요 & 컨셉 맵**](_legacy_overview.md)

## 학습 팁

!!! tip "효율적 학습"
    - **VA → PA 변환을 손으로**: 4-level walk을 화이트보드에서 직접 그릴 수 있어야 함
    - **TLB miss penalty 정량화**: page walk이 메모리 access N번 → 성능 영향 직관 형성
    - **SMMU와 MMU 차이**: CPU MMU는 cores 내장, SMMU는 SoC-level (DMA 마스터들 보호)

!!! warning "흔한 함정"
    - **TLB stale entry**: page table 업데이트 후 TLB invalidate 누락 → 잘못된 PA 사용
    - **IOMMU bypass**: pre-IOMMU SoC는 DMA가 시스템 메모리 무제한 access → 보안 hole
    - **ASID/VMID 충돌**: 다른 process/VM이 같은 VA를 다른 PA로 매핑할 때 ASID 비교 누락
