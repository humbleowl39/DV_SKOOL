# DRAM JEDEC Deep-Dive — DV 실무자용

<div class="topic-hero" data-cat="memory">
  <div class="topic-hero-mark">🧠</div>
  <div class="topic-hero-body">
    <div class="topic-hero-title">LPDDR5 중심 — DDR5 / LPDDR4 / DDR4 비교로 보는 Spec-Driven DV</div>
    <p class="topic-hero-sub">모바일 SoC 메인 메모리인 LPDDR5/5X를 주축으로 JEDEC 표준을 검증 관점에서 deepdive합니다. DDR5(서버/PC), LPDDR4(직전 세대), DDR4(역사적 기준)는 비교축으로 사용합니다. 스펙 원문 인용 → 비교 표 → DV 적용(Coverage / SVA / Scoreboard) → 대표 문제 dry-run.</p>
    <div class="topic-hero-stats">
      <span class="topic-stat"><span class="topic-stat-icon">📚</span><span class="topic-stat-val">12</span><span class="topic-stat-lbl">챕터</span></span>
      <span class="topic-stat"><span class="topic-stat-icon">📎</span><span class="topic-stat-val">3</span><span class="topic-stat-lbl">부록</span></span>
      <span class="topic-stat"><span class="topic-stat-icon">❓</span><span class="topic-stat-val">11</span><span class="topic-stat-lbl">퀴즈 세트</span></span>
      <span class="topic-stat"><span class="topic-stat-icon">🎯</span><span class="topic-stat-val">LPDDR5</span><span class="topic-stat-lbl">중심</span></span>
    </div>
  </div>
</div>

## 왜 DRAM JEDEC DV를 배워야 하는가

모바일 SoC의 메인 메모리인 LPDDR5/5X 컨트롤러 IP를 검증하는 엔지니어가 JEDEC 스펙을 직접 읽지 않으면 무슨 일이 생길까요? tRCD 위반이 DRAM model을 그냥 통과해 silicon에서 간헐적 data corruption으로 터지거나, Rowhammer 시나리오를 아예 테스트 계획에서 누락하거나, LPDDR5의 WCK2CK leveling을 빠뜨린 monitor가 데이터 정렬 오류를 놓치는 일이 발생합니다. 이 자료는 "스펙을 알아야 검증할 수 있다"는 출발점에서, **LPDDR5/5X(JESD209-5)를 주축**으로 JEDEC 표준을 **DV 엔지니어의 시각**으로 재구성합니다. DDR5(JESD79-5, 서버/PC)·LPDDR4(직전 모바일 세대)·DDR4(역사적 기준)는 LPDDR5를 입체적으로 이해하기 위한 **비교축**으로 다룹니다.

스펙을 모르면 막히는 것들이 구체적으로 있습니다. Init 순서를 틀리면 MRW가 DRAM에 조용히 drop 되고, LPDDR5의 Bank 모드(BG/8B/16B)를 모르면 tCCD_L/tCCD_S coverage hole이 생기며, ARFM/DRFM을 모르면 Rowhammer regression이 통과해도 아무 의미가 없습니다. 이 자료는 각 챕터마다 "스펙의 이 부분이 DV에서 이런 구멍을 만든다"는 인과를 명시하므로, 학습 후에는 V-Plan 작성·SVA 설계·coverage 분류를 스펙 근거와 함께 진행할 수 있습니다.

## 이 학습 자료가 다루는 것

스펙 원문을 직접 인용하면서 **DV 엔지니어가 실제로 무엇을 검증해야 하는지**를 잇는 것이 이 자료의 목적입니다. 단순한 스펙 요약이 아니라:

- 모든 챕터에 **DV Application** 섹션 (coverage / SVA / scoreboard 규칙)
- 모든 챕터에 **대표 문제 dry-run** (timing 계산, 시나리오 trace, 코드 추적)
- LPDDR4↔LPDDR5 진화 및 LPDDR5↔DDR5 **비교 표** (DDR4↔DDR5는 보조 비교)
- Ch11은 **DV 전용** end-to-end 예시 (UVM 스켈레톤 + SVA bind + 시나리오 라이브러리 + sign-off 체크리스트)

## 참조 스펙 (4종)

| 표준 | 문서 | 비고 |
|---|---|---|
| DDR4 SDRAM | JESD79-4D | Mode Register, FGR, hPPR/sPPR, CRC, CA Parity |
| DDR5 SDRAM | JESD79-5C.01 v1.31 (2024-07) | MR0~MR254, DFE, RFM(MR58/59), Transparency ECC |
| LPDDR4 | JESD209-4E | CA/DQ VREF Training, CBT, PPR |
| LPDDR5/5X | JESD209-5C | WCK Clocking, DVFS, Link ECC, ARFM/DRFM, Per-pin DFE |

> 본 자료의 인용은 학습 목적의 **요약·참조**이며, 스펙 원문의 복제가 아닙니다. 정밀한 수치/타이밍 표는 항상 원본 JEDEC 문서를 우선으로 합니다.

## 학습 경로

<div class="concept-dag dag-long">
  <div class="concept-dag-title">11 챕터 + 3 부록 — 권장 학습 순서</div>
  <div class="concept-dag-row">
    <a class="concept-dag-node" href="01_dram_jedec_landscape/"><span class="concept-dag-node-num">CH 01</span><span class="concept-dag-node-title">JEDEC 표준 지형도</span></a>
  </div>
  <div class="concept-dag-row"><span class="concept-dag-arrow">▼</span></div>
  <div class="concept-dag-row">
    <a class="concept-dag-node" href="02_package_pinout_addressing/"><span class="concept-dag-node-num">CH 02</span><span class="concept-dag-node-title">패키지·핀아웃·어드레싱</span></a>
  </div>
  <div class="concept-dag-row"><span class="concept-dag-arrow">▼</span></div>
  <div class="concept-dag-row">
    <a class="concept-dag-node" href="03_init_reset_power/"><span class="concept-dag-node-num">CH 03</span><span class="concept-dag-node-title">초기화·Reset·Power</span></a>
  </div>
  <div class="concept-dag-row"><span class="concept-dag-arrow">▼</span></div>
  <div class="concept-dag-row">
    <a class="concept-dag-node" href="04_mode_registers/"><span class="concept-dag-node-num">CH 04</span><span class="concept-dag-node-title">Mode Register 깊이 분석</span></a>
  </div>
  <div class="concept-dag-row"><span class="concept-dag-arrow">▼</span></div>
  <div class="concept-dag-row">
    <a class="concept-dag-node" href="05_commands_burst/"><span class="concept-dag-node-num">CH 05</span><span class="concept-dag-node-title">Command·Burst</span></a>
  </div>
  <div class="concept-dag-row"><span class="concept-dag-arrow">▼</span></div>
  <div class="concept-dag-row">
    <a class="concept-dag-node" href="06_timing_preamble/"><span class="concept-dag-node-num">CH 06</span><span class="concept-dag-node-title">Timing·Preamble</span></a>
  </div>
  <div class="concept-dag-row"><span class="concept-dag-arrow">▼</span></div>
  <div class="concept-dag-row">
    <a class="concept-dag-node" href="07_refresh_rfm/"><span class="concept-dag-node-num">CH 07</span><span class="concept-dag-node-title">Refresh·RFM·Rowhammer</span></a>
  </div>
  <div class="concept-dag-row"><span class="concept-dag-arrow">▼</span></div>
  <div class="concept-dag-row">
    <a class="concept-dag-node" href="08_training/"><span class="concept-dag-node-num">CH 08</span><span class="concept-dag-node-title">Training</span></a>
  </div>
  <div class="concept-dag-row"><span class="concept-dag-arrow">▼</span></div>
  <div class="concept-dag-row">
    <a class="concept-dag-node" href="09_reliability_ecc_crc/"><span class="concept-dag-node-num">CH 09</span><span class="concept-dag-node-title">신뢰성·ECC·CRC·PPR</span></a>
  </div>
  <div class="concept-dag-row"><span class="concept-dag-arrow">▼</span></div>
  <div class="concept-dag-row">
    <a class="concept-dag-node" href="10_dv_methodology/"><span class="concept-dag-node-num">CH 10</span><span class="concept-dag-node-title">DV Methodology 통합</span></a>
  </div>
  <div class="concept-dag-row"><span class="concept-dag-arrow">▼</span></div>
  <div class="concept-dag-row">
    <a class="concept-dag-node" href="11_dv_project_endtoend/"><span class="concept-dag-node-num">CH 11</span><span class="concept-dag-node-title">DV 프로젝트 End-to-End</span></a>
  </div>
  <div class="concept-dag-row"><span class="concept-dag-arrow">▼</span></div>
  <div class="concept-dag-row">
    <a class="concept-dag-node" href="12_vendor_dv_mixed_signal_sta/"><span class="concept-dag-node-num">CH 12</span><span class="concept-dag-node-title">Vendor DV: Mixed-Signal·STA</span></a>
  </div>
  <p class="concept-dag-legend">Ch01~Ch10은 시스템 측 DV (controller IP) 관점, Ch11은 통합 사례, Ch12는 DRAM vendor 측 (Mixed-Signal + STA + Custom 회로) 관점 — 양쪽 다 이해하면 sweet-spot.</p>
</div>

## 챕터 요약

<div class="module-grid">

  <a class="module-card" data-cat="memory" href="01_dram_jedec_landscape/">
    <span class="module-num">01</span>
    <span class="module-body">
      <span class="module-title">DRAM 기본 원리와 JEDEC 표준 지형도</span>
      <span class="module-desc">DRAM cell부터 JESD79/209 표준 패밀리까지. 왜 DV 엔지니어가 스펙을 직접 읽어야 하는가.</span>
    </span>
  </a>

  <a class="module-card" data-cat="memory" href="02_package_pinout_addressing/">
    <span class="module-num">02</span>
    <span class="module-body">
      <span class="module-title">패키지·핀아웃·어드레싱</span>
      <span class="module-desc">DDR4/5 vs LPDDR4/5의 패키지 옵션, BG/Bank 구조, BL16/BL32 어드레싱.</span>
    </span>
  </a>

  <a class="module-card" data-cat="memory" href="03_init_reset_power/">
    <span class="module-num">03</span>
    <span class="module-body">
      <span class="module-title">초기화·Reset·Power 시퀀스</span>
      <span class="module-desc">Power-up → Reset → MR Write → ready. UVM phase 매핑까지.</span>
    </span>
  </a>

  <a class="module-card" data-cat="memory" href="04_mode_registers/">
    <span class="module-num">04</span>
    <span class="module-body">
      <span class="module-title">Mode Register 깊이 분석</span>
      <span class="module-desc">DDR5 MR0~MR254 카테고리별 분류. RAL register model 연계.</span>
    </span>
  </a>

  <a class="module-card" data-cat="memory" href="05_commands_burst/">
    <span class="module-num">05</span>
    <span class="module-body">
      <span class="module-title">Command·Truth Table·Burst</span>
      <span class="module-desc">2-cycle command(DDR5), BL16/BL32, command coverpoint + SVA.</span>
    </span>
  </a>

  <a class="module-card" data-cat="memory" href="06_timing_preamble/">
    <span class="module-num">06</span>
    <span class="module-body">
      <span class="module-title">Timing·Preamble·Postamble</span>
      <span class="module-desc">tRCD/tRP/tFAW/tCCD_L. Preamble training. ACT→RD timing dry-run.</span>
    </span>
  </a>

  <a class="module-card" data-cat="memory" href="07_refresh_rfm/">
    <span class="module-num">07</span>
    <span class="module-body">
      <span class="module-title">Refresh·tREFI/tRFC·RFM</span>
      <span class="module-desc">DDR5 RFM(MR58/59), LPDDR5 ARFM/DRFM. Rowhammer 시나리오.</span>
    </span>
  </a>

  <a class="module-card" data-cat="memory" href="08_training/">
    <span class="module-num">08</span>
    <span class="module-body">
      <span class="module-title">Training (CA/DQ/DQS/WCK2CK)</span>
      <span class="module-desc">DDR5 DQS Training(MR3), LPDDR5 CBT Mode1/2, WCK2CK Leveling, DCA.</span>
    </span>
  </a>

  <a class="module-card" data-cat="memory" href="09_reliability_ecc_crc/">
    <span class="module-num">09</span>
    <span class="module-body">
      <span class="module-title">신뢰성·ECC·CRC·PPR</span>
      <span class="module-desc">DDR5 Transparency ECC, LPDDR5 Link ECC, CRC, hPPR/sPPR.</span>
    </span>
  </a>

  <a class="module-card" data-cat="memory" href="10_dv_methodology/">
    <span class="module-num">10</span>
    <span class="module-body">
      <span class="module-title">DV Methodology 통합</span>
      <span class="module-desc">Agent/Monitor/Scoreboard 설계, Coverage 카테고리, SVA 패턴, Sign-off.</span>
    </span>
  </a>

  <a class="module-card" data-cat="memory" href="11_dv_project_endtoend/">
    <span class="module-num">11</span>
    <span class="module-body">
      <span class="module-title">DV 프로젝트 End-to-End ⭐</span>
      <span class="module-desc">DDR5 controller IP 검증을 UVM 스켈레톤 + SVA bind + 시나리오 라이브러리로 통합.</span>
    </span>
  </a>

  <a class="module-card" data-cat="memory" href="12_vendor_dv_mixed_signal_sta/">
    <span class="module-num">12</span>
    <span class="module-body">
      <span class="module-title">Vendor DV — Mixed-Signal·STA·Custom 회로 ⭐</span>
      <span class="module-desc">DRAM vendor 관점 — Hspice/PrimeSim, STA, Sense Amp/SWE/X-DEC/Y-DEC, antifuse circuit, MBIST. SK Hynix 설계검증 JD 정렬.</span>
    </span>
  </a>

</div>

## 사전 지식 (Prerequisites)

- SystemVerilog 기본 (always_ff, interface, modport, class)
- UVM 1.2 핵심 (uvm_sequence_item, uvm_driver, uvm_monitor, uvm_scoreboard, uvm_config_db)
- 디지털 회로 기본 (synchronous design, setup/hold, clock domain)
- DRAM 또는 DDR 기초가 있으면 Ch01~Ch03은 빠르게 통과 가능

## 다음 단계

- Ch01부터 순차 학습: [Ch01. DRAM 기본 원리와 JEDEC 표준 지형도](01_dram_jedec_landscape.md)
- 빠른 참조가 필요하다면: [부록 A. JEDEC Spec 빠른 참조](appendix_a_quick_reference.md)
- 용어가 헷갈리면: [부록 B. Glossary](appendix_b_glossary.md)
- 퀴즈로 자가 점검: [퀴즈 인덱스](quiz/index.md)
