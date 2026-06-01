# Mixed-Signal DV — SPICE · AMS · RNM

<div class="topic-hero" data-cat="memory">
  <div class="topic-hero-mark">🌊</div>
  <div class="topic-hero-body">
    <div class="topic-hero-title">UVM/SoC DV 경험자를 위한 Mixed-Signal 시뮬레이션 입문</div>
    <p class="topic-hero-sub">SPICE → AMS → RNM 흐름을 한 번에 잡고, DLL · IO Buffer · Sense Amp 3대 mixed-signal 블록을 RNM 코드와 dry-run으로 풀어봅니다.</p>
    <div class="topic-hero-stats">
      <span class="topic-stat"><span class="topic-stat-icon">📚</span><span class="topic-stat-val">12</span><span class="topic-stat-lbl">챕터</span></span>
      <span class="topic-stat"><span class="topic-stat-icon">📎</span><span class="topic-stat-val">4</span><span class="topic-stat-lbl">부록</span></span>
      <span class="topic-stat"><span class="topic-stat-icon">❓</span><span class="topic-stat-val">12</span><span class="topic-stat-lbl">퀴즈 세트</span></span>
      <span class="topic-stat"><span class="topic-stat-icon">🎯</span><span class="topic-stat-val">RNM</span><span class="topic-stat-lbl">중심</span></span>
    </div>
  </div>
</div>

## 이 토픽을 배워야 하는 이유

현대 반도체 칩의 검증 엔지니어는 언젠가 이 벽에 부딪힙니다. DRAM의 bit-line 전압이 60 mV밖에 올라가지 않아서 sense amp가 제대로 동작하는지 확인해야 하는데, 순수 디지털 시뮬레이터는 전압을 0과 1로밖에 표현하지 못합니다. SPICE로 돌리자니 수억 개의 셀이 있어 시뮬레이션 완료까지 수 년이 걸립니다. 이 상황에서 어떻게 해야 할까요?

이 토픽을 배우지 않으면, DLL 위상 정렬이 맞는지 timing margin을 정량화하지 못하고, IO buffer 임피던스 mismatch가 eye를 얼마나 좁히는지 계산하지 못하며, Pelgrom mismatch 통계가 칩 yield에 어떻게 연결되는지 추론할 수 없습니다. mixed-signal 블록을 검증 계획에서 "아날로그팀이 알아서 하는 것"으로 넘기게 되고, 그 경계에서 생기는 버그가 tape-out 이후 발견됩니다.

## 이 학습 자료가 다루는 것

대부분의 실제 칩(DRAM, ADC, SerDes, PLL, Power IC)에는 디지털과 아날로그가 공존합니다. 그러나 두 도메인은 **시뮬레이션 패러다임이 완전히 다릅니다.** Digital simulator(VCS, Xcelium)는 logic 0/1/X/Z와 이벤트 기반 엔진으로 동작하여 빠르지만 실수 전압·노이즈·신호 천이를 표현하지 못합니다. SPICE(HSPICE, Spectre)는 실수 전압과 전류를 연속시간 수치 해석으로 정확하게 풀지만 회로 규모에 비례해서 극단적으로 느립니다. RNM(SystemVerilog `nettype real`)은 real 값을 이벤트 기반으로 처리하여 두 접근의 장점을 결합합니다.

이 토픽은 **세 시뮬레이션의 위치와 trade-off**를 잡고, **RNM이 DRAM 검증의 표준이 된 이유**와 그 한계, 그리고 **각 mixed-signal 블록을 어떤 추상화 수준으로 모델링해야 하는지** 결정하는 능력을 길러줍니다. 모든 챕터에 Bloom's Taxonomy 학습 목표와 퀴즈 매핑이 있고, DLL·IO Buffer·Sense Amp Offset 3대 블록의 deep-dive에는 실제 RNM 코드가 포함됩니다. DVCon paper를 인용한 검증 방법론 챕터(Ch10)에서는 DMS, EEnet, UDN 등 최신 베스트 프랙티스를 다루며, Pelgrom 공식·charge sharing·reflection coefficient·Newton-Raphson 같은 핵심 수식은 모두 손으로 계산할 수 있도록 dry-run이 제공됩니다.

## 학습 경로

<div class="concept-dag dag-long">
  <div class="concept-dag-title">12 챕터 + 4 부록 — 권장 학습 순서</div>
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
  <div class="concept-dag-row"><span class="concept-dag-arrow">▼</span></div>
  <div class="concept-dag-row">
    <a class="concept-dag-node" href="12_uvm_rnm_integration/"><span class="concept-dag-node-num">CH 12</span><span class="concept-dag-node-title">UVM × RNM Integration</span></a>
    <a class="concept-dag-node" href="appendix_d_analog_ip_catalogue/"><span class="concept-dag-node-num">APP D</span><span class="concept-dag-node-title">Analog IP Catalogue (8종)</span></a>
  </div>
  <p class="concept-dag-legend">Ch03~05는 병렬 학습 가능. Ch07~09는 deep-dive로 독립적. Ch10은 통합·전략, Ch11은 도구 카탈로그. Ch12는 UVM 통합 패턴, Appendix D는 IP별 카탈로그 참고용.</p>
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

  <a class="module-card" data-cat="memory" href="12_uvm_rnm_integration/">
    <span class="module-num">12</span>
    <span class="module-body">
      <span class="module-title">UVM × RNM Integration</span>
      <span class="module-desc">Env · vif · agent · sequence · ref model · scoreboard — UVM testbench 위에 mixed-signal layer 얹기.</span>
    </span>
  </a>

</div>

## 학습 목표 (전체)

이 토픽을 모두 학습하면 다음을 할 수 있게 됩니다 (Bloom's Taxonomy).

**Remember** 수준에서는 SPICE·AMS·RNM의 정의를 recall할 수 있고, Sense amp·DLL·IO buffer 각각의 구성 요소를 나열하며, Pelgrom's law와 charge sharing 수식을 쓸 수 있습니다.

**Understand** 수준에서는 세 시뮬레이션 방법론의 속도·정확도 trade-off를 설명하고, DLL이 lock을 잡는 feedback 메커니즘과 ZQ calibration이 왜 주기적으로 필요한지를 인과 관계로 서술할 수 있습니다.

**Apply** 수준에서는 `nettype real` 기반 RNM 모듈을 직접 작성하고, charge sharing 물리를 RNM 코드로 구현하며, Pelgrom's law를 적용한 random offset 주입 패턴을 사용할 수 있습니다.

**Analyze** 수준에서는 DRAM read 경로를 7-stage로 분해하여 각 블록의 적합한 검증 패러다임을 결정하고, DLL lock failure의 원인(harmonic lock 포함)을 진단하며, eye opening에 영향을 미치는 IO 파라미터를 분석할 수 있습니다.

**Evaluate** 수준에서는 sense margin이 yield에 미치는 영향을 Pelgrom 통계로 정량 평가하고, ODT 설정 변경이 signal integrity에 어떤 결과를 낳는지 판단하며, 주어진 검증 task에 RNM과 SPICE 중 어느 것이 적합한지 근거와 함께 결정할 수 있습니다.

**Create** 수준에서는 DRAM read 경로의 RNM 모델을 설계하고 SA offset Monte Carlo 검증까지 완성하며, PLL이나 regulator 같은 새로운 mixed-signal 블록의 RNM testbench 아키텍처를 처음부터 설계할 수 있습니다.

## 선수 지식

이 토픽의 시작에는 SystemVerilog의 기초인 `logic`, `always`, `module` 문법을 알고 있으면 충분합니다. 회로 이론은 저항·캐패시터의 동작과 MOSFET이 트랜지스터로서 스위칭한다는 개념을 이해하는 수준이면 됩니다. UVM 경험이 있으면 Ch12의 testbench 통합 챕터에서 도움이 되지만 필수는 아닙니다 — RNM 모델 대부분은 UVM 없이 inline TB로 작성됩니다.

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
- **D. Analog IP Catalogue** — PLL · ADC · DAC · LDO · Bandgap · PMU · Sensors · SerDes 8종 카탈로그 (spec 표 + 최소 RNM 모델 + 검증 시나리오 + coverage + 함정)
