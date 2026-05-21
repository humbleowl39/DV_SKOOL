# Mixed-Signal DV — SPICE · AMS · RNM

<div class="topic-hero" data-cat="memory">
  <div class="topic-hero-mark">🌊</div>
  <div class="topic-hero-body">
    <div class="topic-hero-title">UVM/SoC DV 경험자를 위한 Mixed-Signal 시뮬레이션 입문</div>
    <p class="topic-hero-sub">SPICE → AMS → RNM 흐름을 한 번에 잡고, DLL · IO Buffer · Sense Amp 3대 mixed-signal 블록을 RNM 코드와 dry-run으로 풀어봅니다.</p>
    <div class="topic-hero-stats">
      <span class="topic-stat"><span class="topic-stat-icon">📚</span><span class="topic-stat-val">11</span><span class="topic-stat-lbl">챕터</span></span>
      <span class="topic-stat"><span class="topic-stat-icon">📎</span><span class="topic-stat-val">3</span><span class="topic-stat-lbl">부록</span></span>
      <span class="topic-stat"><span class="topic-stat-icon">❓</span><span class="topic-stat-val">11</span><span class="topic-stat-lbl">퀴즈 세트</span></span>
      <span class="topic-stat"><span class="topic-stat-icon">🎯</span><span class="topic-stat-val">RNM</span><span class="topic-stat-lbl">중심</span></span>
    </div>
  </div>
</div>

## 이 학습 자료가 다루는 것

대부분의 실제 칩(DRAM, ADC, SerDes, PLL, Power IC)에는 디지털과 아날로그가 공존합니다. 그러나 두 도메인은 **시뮬레이션 패러다임이 완전히 다릅니다.**

- **Digital simulator** (VCS, Xcelium): logic(0/1/X/Z) + 이벤트 기반 → 빠르지만 voltage·노이즈·천이를 표현 못함
- **SPICE** (HSPICE, Spectre): 실수 전압/전류 + 연속시간 수치해석 → 정확하지만 매우 느림
- **RNM** (SystemVerilog `nettype real`): real 값 + 이벤트 기반 → 빠르면서 voltage 표현 가능

이 토픽은 **세 시뮬레이션의 위치와 trade-off**를 잡고, **RNM이 DRAM 검증의 표준이 된 이유**와 그 한계, 그리고 **각 mixed-signal 블록을 어떤 추상화 수준으로 모델링해야 하는지** 결정하는 능력을 길러줍니다.

다른 토픽과의 차이:

- 모든 챕터에 **Bloom's Taxonomy 학습 목표** + **퀴즈 매핑**
- **DLL · IO Buffer · Sense Amp Offset** 3대 블록 deep-dive (RNM 코드 포함)
- DVCon paper 인용한 **검증 방법론** (Ch10) — DMS, EEnet, UDN 등 최신 베스트 프랙티스
- 모든 핵심 식(Pelgrom, charge sharing, reflection coefficient, Newton-Raphson) **dry-run** 포함

## 학습 경로

<div class="concept-dag dag-long">
  <div class="concept-dag-title">11 챕터 + 3 부록 — 권장 학습 순서</div>
  <div class="concept-dag-row">
    <a class="concept-dag-node" href="01_why_mixed_signal/"><span class="concept-dag-node-num">CH 01</span><span class="concept-dag-node-title">왜 Mixed-Signal Simulation인가</span></a>
  </div>
  <div class="concept-dag-row"><span class="concept-dag-arrow">▼</span></div>
  <div class="concept-dag-row">
    <a class="concept-dag-node" href="02_three_worlds_spice_ams_rnm/"><span class="concept-dag-node-num">CH 02</span><span class="concept-dag-node-title">세 시뮬레이션 세계</span></a>
  </div>
  <div class="concept-dag-row"><span class="concept-dag-arrow">▼</span></div>
  <div class="concept-dag-row">
    <a class="concept-dag-node" href="03_spice_fundamentals/"><span class="concept-dag-node-num">CH 03</span><span class="concept-dag-node-title">SPICE / Fast SPICE</span></a>
    <a class="concept-dag-node" href="04_ams_connect_modules/"><span class="concept-dag-node-num">CH 04</span><span class="concept-dag-node-title">AMS · Connect Module</span></a>
    <a class="concept-dag-node" href="05_rnm_systemverilog/"><span class="concept-dag-node-num">CH 05</span><span class="concept-dag-node-title">RNM with SV</span></a>
  </div>
  <div class="concept-dag-row"><span class="concept-dag-arrow">▼</span></div>
  <div class="concept-dag-row">
    <a class="concept-dag-node" href="06_dram_read_path_partitioning/"><span class="concept-dag-node-num">CH 06</span><span class="concept-dag-node-title">DRAM Read Path 분해</span></a>
  </div>
  <div class="concept-dag-row"><span class="concept-dag-arrow">▼</span></div>
  <div class="concept-dag-row">
    <a class="concept-dag-node" href="07_deepdive_dll_rnm/"><span class="concept-dag-node-num">CH 07</span><span class="concept-dag-node-title">DLL Deep Dive</span></a>
    <a class="concept-dag-node" href="08_deepdive_io_buffer_rnm/"><span class="concept-dag-node-num">CH 08</span><span class="concept-dag-node-title">IO Buffer · IBIS-AMI</span></a>
    <a class="concept-dag-node" href="09_deepdive_sense_amp_offset/"><span class="concept-dag-node-num">CH 09</span><span class="concept-dag-node-title">Sense Amp Offset · MC</span></a>
  </div>
  <div class="concept-dag-row"><span class="concept-dag-arrow">▼</span></div>
  <div class="concept-dag-row">
    <a class="concept-dag-node" href="10_verification_methodology/"><span class="concept-dag-node-num">CH 10</span><span class="concept-dag-node-title">검증 방법론 통합</span></a>
    <a class="concept-dag-node" href="11_tools_ecosystem/"><span class="concept-dag-node-num">CH 11</span><span class="concept-dag-node-title">도구 지형</span></a>
  </div>
  <p class="concept-dag-legend">Ch03~05는 병렬 학습 가능. Ch07~09는 deep-dive로 독립적. Ch10은 통합·전략, Ch11은 도구 카탈로그.</p>
</div>

## 챕터 요약

<div class="module-grid">

  <a class="module-card" data-cat="memory" href="01_why_mixed_signal/">
    <span class="module-num">01</span>
    <span class="module-body">
      <span class="module-title">왜 Mixed-Signal Simulation인가</span>
      <span class="module-desc">디지털 sim의 한계, SPICE의 한계, 두 세계를 잇는 mixed-signal의 필요성.</span>
    </span>
  </a>

  <a class="module-card" data-cat="memory" href="02_three_worlds_spice_ams_rnm/">
    <span class="module-num">02</span>
    <span class="module-body">
      <span class="module-title">세 시뮬레이션 세계</span>
      <span class="module-desc">Digital · SPICE · RNM — 신호 표현, 시간 처리, 속도, 정확도의 trade-off 표.</span>
    </span>
  </a>

  <a class="module-card" data-cat="memory" href="03_spice_fundamentals/">
    <span class="module-num">03</span>
    <span class="module-body">
      <span class="module-title">SPICE / Fast SPICE 기초</span>
      <span class="module-desc">KCL/KVL, BSIM, .tran/.ac, Newton-Raphson, Fast SPICE 가속 기법.</span>
    </span>
  </a>

  <a class="module-card" data-cat="memory" href="04_ams_connect_modules/">
    <span class="module-num">04</span>
    <span class="module-body">
      <span class="module-title">AMS · Verilog-AMS · Connect Module</span>
      <span class="module-desc">Discipline, electrical, D2A/A2D, VAMS-2023 LRM 기반.</span>
    </span>
  </a>

  <a class="module-card" data-cat="memory" href="05_rnm_systemverilog/">
    <span class="module-num">05</span>
    <span class="module-body">
      <span class="module-title">RNM with SystemVerilog</span>
      <span class="module-desc">real · nettype · wreal · UDN/UDR · resolution function. RNM 5단계 정확도 모델.</span>
    </span>
  </a>

  <a class="module-card" data-cat="memory" href="06_dram_read_path_partitioning/">
    <span class="module-num">06</span>
    <span class="module-body">
      <span class="module-title">DRAM Read Path 분해</span>
      <span class="module-desc">Decoder → WL → Cell → BL → SA → IO 각 단계를 어떤 추상화로 검증할지.</span>
    </span>
  </a>

  <a class="module-card" data-cat="memory" href="07_deepdive_dll_rnm/">
    <span class="module-num">07</span>
    <span class="module-body">
      <span class="module-title">DLL Deep Dive</span>
      <span class="module-desc">PD · LF · DL · Replica 4블록 RNM. Lock 시나리오 + Harmonic lock 방지.</span>
    </span>
  </a>

  <a class="module-card" data-cat="memory" href="08_deepdive_io_buffer_rnm/">
    <span class="module-num">08</span>
    <span class="module-body">
      <span class="module-title">IO Buffer · IBIS-AMI</span>
      <span class="module-desc">Driver strength · slew · ZQ cal · ODT · transmission line · IBIS-AMI back-channel.</span>
    </span>
  </a>

  <a class="module-card" data-cat="memory" href="09_deepdive_sense_amp_offset/">
    <span class="module-num">09</span>
    <span class="module-body">
      <span class="module-title">Sense Amp Offset · Monte Carlo</span>
      <span class="module-desc">Pelgrom AVT · σ(ΔVth) · RNM MC · yield 정량 평가.</span>
    </span>
  </a>

  <a class="module-card" data-cat="memory" href="10_verification_methodology/">
    <span class="module-num">10</span>
    <span class="module-body">
      <span class="module-title">RNM/AMS 검증 방법론 통합</span>
      <span class="module-desc">DVCon paper 사례 — DMS, UVM-AMS, UDN, EEnet. 1000x speed-up 결과.</span>
    </span>
  </a>

  <a class="module-card" data-cat="memory" href="11_tools_ecosystem/">
    <span class="module-num">11</span>
    <span class="module-body">
      <span class="module-title">도구 지형</span>
      <span class="module-desc">VCS-AMS · AMS Designer · Questa-AMS · FineSim · CustomSim 비교.</span>
    </span>
  </a>

</div>

## 학습 목표 (전체)

이 토픽을 모두 학습하면 다음을 할 수 있게 됩니다 (Bloom's Taxonomy):

### Remember
- SPICE, AMS, RNM의 정의
- Sense amp, DLL, IO buffer의 구성 요소
- Pelgrom's law, charge sharing 식

### Understand
- 세 시뮬레이션 방법론의 속도/정확도 trade-off
- DLL이 lock을 잡는 메커니즘
- ZQ calibration의 필요성
- Mismatch가 sense amp offset을 만드는 원리

### Apply
- `nettype real` 기반 RNM 모듈 작성
- Charge sharing 물리를 RNM 코드로 구현
- DLL, IO buffer, SA의 RNM 모델 작성
- Pelgrom's law 적용한 random offset 주입

### Analyze
- DRAM read 경로를 분해하여 어느 블록을 어떤 방법으로 검증할지 결정
- Lock failure 원인 진단 (harmonic lock 포함)
- Eye opening의 IO 파라미터 영향 분석

### Evaluate
- Sense margin이 yield에 미치는 영향 정량 평가
- ODT 설정이 signal integrity에 미치는 영향 판단
- 주어진 검증 task에 RNM vs SPICE 중 어떤 게 적합한지 결정

### Create
- DRAM read 경로 RNM 모델을 설계하고 SA offset MC 검증까지 완성
- 새로운 mixed-signal 블록(예: PLL, regulator)의 RNM testbench 아키텍처 설계

## 선수 지식

- SystemVerilog 기초 (`logic`, `always`, `module`)
- 기본 회로 (저항, 캐패시터, MOSFET 동작 개념)
- UVM 경험 있으면 도움이 되나 필수 아님 — RNM은 inline TB가 더 흔함

## 참조 표준

| 표준 | 발행 | 내용 |
|---|---|---|
| IEEE 1800-2017 | SystemVerilog LRM | `real`, `nettype`, resolution function |
| VAMS-2023 | Accellera (Feb 2024) | Verilog-AMS LRM (마지막 메이저 갱신) |
| IBIS 7.2 | IBIS Open Forum | IBIS-AMI back-channel, PAM, DDR5 link training |
| JESD79-5C | JEDEC | DDR5 SDRAM |
| JESD235D | JEDEC | HBM3 |

> 본 자료의 표준 인용은 학습 목적의 요약·참조이며, 원문 복제가 아닙니다. 정밀한 수치/타이밍은 해당 원본 표준 문서를 우선으로 합니다.

## 부록

- **A. Quick Reference** — 식·상수·도구 표
- **B. Code Examples** — Inverter / DRAM Cell+SA / PLL Lock 3종 RNM 예제 (EN+KO)
- **C. Glossary** — ISO 11179 정의 (EN+KO)
