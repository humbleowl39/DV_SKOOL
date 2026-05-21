# Ch10. RNM/AMS 검증 방법론 통합 — DVCon Best Practices

## 학습 목표

- **(Remember)** DMS와 AMS의 차이를 진술할 수 있다
- **(Understand)** UDN/EEnet이 단순 wreal로 부족한 상황을 해결하는 방법을 설명할 수 있다
- **(Apply)** Mixed-signal SoC 검증 환경을 UVM 위에 RNM/AMS layer로 구성할 수 있다
- **(Analyze)** DVCon paper의 100×~1000× 속도 향상 사례를 패턴으로 분해할 수 있다
- **(Evaluate)** 주어진 mixed-signal 검증 task에 어떤 방법론(DMS/AMS/IBIS-AMI)이 적합한지 결정할 수 있다
- **(Create)** RNM/AMS abstraction switching이 가능한 TB 아키텍처를 설계할 수 있다

> 본 챕터의 내용은 DVCon proceedings의 공개 papers(2019~2024)와 산업 white paper에 기반합니다. 인용 원문은 본문 끝 References 참조.

## 1. DMS vs AMS — 핵심 구분

| 항목 | DMS (Digital Mixed-Signal) | AMS (Analog Mixed-Signal) |
|---|---|---|
| 신호 표현 | Real (event-driven) | Electrical (continuous) |
| 시뮬레이터 | Digital만 | Digital + SPICE |
| 모델링 언어 | SystemVerilog (RNM) | Verilog-AMS, SPICE netlist |
| 속도 | 100×~1000× faster | Baseline |
| 정확도 | 모델 정확도에 의존 | SPICE 수준 |
| 적용 | SoC 전체, 시나리오 검증 | 단일 block, sign-off |

DVCon paper들의 공통 메시지: **"DMS를 우선, AMS를 보완으로"**.

## 2. 4가지 DVCon 패턴

### Pattern 1 — Single wreal는 부족하다

단일 real 값(`wreal`)으로 multi-driver, impedance interaction을 표현 못 함:

- 두 driver가 같은 net에 → 어떤 voltage가 net에 나타나나?
- Tristate, pull-up/down, ODT — wreal는 표현 불가
- Power supply의 sag/load regulation — 단순 real로 부족

**해결: User-Defined Nettype (UDN)** — 구조체 + resolution function.

```systemverilog
typedef struct packed {
  real voltage;
  real impedance;  // ohm. 작을수록 강한 driver
} ee_t;

function automatic ee_t resolve_thevenin(input ee_t drivers[]);
  ee_t out;
  real g_sum  = 0;
  real ig_sum = 0;
  foreach (drivers[i]) begin
    real g  = 1.0 / drivers[i].impedance;
    g_sum  += g;
    ig_sum += drivers[i].voltage * g;
  end
  out.voltage   = ig_sum / g_sum;
  out.impedance = 1.0 / g_sum;
  return out;
endfunction

nettype ee_t eenet with resolve_thevenin;
```

- 두 driver가 parallel로 net을 구동하면 **Thevenin equivalent**를 자동 계산
- 산업 사례: Cadence `EE_pkg::EEnet` (Spectre-AMS 표준 라이브러리)

> 출처: *"Enabling Digital Mixed-Signal Verification of Loading Effects in Power Regulation Using SystemVerilog User-Defined Nettypes"*, DVCon

### Pattern 2 — UVM과 통합 (UVM-DMS)

기존 UVM testbench 위에 mixed-signal layer를 얹습니다:

```
┌────────────────────────────────────────────────────────┐
│                    UVM Test                              │
└────────────────────────────────────────────────────────┘
                          │
┌────────────────────────────────────────────────────────┐
│             UVM env  (mixed-signal aware)                │
│                                                          │
│  ┌─────────────┐   ┌─────────────┐   ┌──────────────┐  │
│  │ AXI agent   │   │ Power agent │   │ Voltage      │  │
│  │ (digital)   │   │ (DMS)       │   │ monitor (DMS)│  │
│  └─────────────┘   └─────────────┘   └──────────────┘  │
│                                                          │
│         Scoreboard: digital + real value 비교             │
└────────────────────────────────────────────────────────┘
                          │
                          ▼
                    DUT (RTL + RNM)
```

핵심 아이디어:

- Digital agent는 그대로
- **Power/voltage agent**가 wreal/UDN 신호 monitor + driver
- Scoreboard가 voltage threshold + digital 결과 동시 검사
- Coverage: voltage bin + digital state

> 출처: *"Scalable Re-usable UVM DMS/AMS Based Verification Methodology for Mixed-Signal SoCs"*, DVCon

### Pattern 3 — Abstraction Switching (RNM ↔ AMS ↔ SPICE)

같은 block을 시뮬레이션 중 abstraction level을 바꿉니다:

```
Top
 └─ DUT
      ├─ Digital_block (RTL)
      └─ Analog_block
           ├─ Option A: RNM (default)        — 빠름
           ├─ Option B: Verilog-AMS behavior  — 중간
           └─ Option C: SPICE netlist         — 정확
```

Simulator level의 `config` 또는 `bind` 방식:

```systemverilog
// VCS-AMS 예시: hierarchy override
// sim cmd:
//   vcs +rnm +define+SA_MODE_RNM
//   vcs +ams +define+SA_MODE_SPICE  // for one block

`ifdef SA_MODE_SPICE
  // SPICE netlist instance
`elsif SA_MODE_AMS
  // Verilog-AMS behavioral
`else
  sense_amp_rnm u_sa(.bl(bl), .bl_ref(bl_ref), .data_out(d));
`endif
```

활용:

- Functional regression: 전체 RNM
- Corner regression: critical block만 SPICE
- Sign-off: top critical paths만 AMS

### Pattern 4 — Coverage on Real Values

Functional coverage를 voltage/timing에 적용:

```systemverilog
covergroup cg_sa_input;
  cp_v_diff : coverpoint (bl - bl_ref) {
    bins low_margin   = {[-200:-80]};
    bins mid_negative = {[-80:-20]};
    bins zero         = {[-20:20]};      // ambiguous zone
    bins mid_positive = {[20:80]};
    bins high_margin  = {[80:200]};
  }
  cp_offset : coverpoint $abs(v_offset_mV) {
    bins low  = {[0:20]};
    bins mid  = {[20:40]};
    bins high = {[40:60]};
  }
  cross cp_v_diff, cp_offset;
endgroup
```

→ Margin × Offset 조합 coverage. 모든 worst-case 조합이 hit 되었는지 확인.

## 3. 1000× 속도 향상 — DVCon 사례 분석

### 3.1 PMIC for SSD — 100×~1000× speedup (DVCon)

상황: SSD용 PMIC의 power regulation 검증
- 기존: AMS (Spectre+VCS) → 한 testcase 12 hours
- 신규: SV-RNM only → 한 testcase 30 sec ~ 10 min (~100×~1000×)

핵심 변환:

| Block | Before (AMS) | After (RNM) |
|---|---|---|
| Buck converter | SPICE | EEnet UDN |
| LDO | SPICE | wreal + thermal model |
| Load | SPICE | wreal current source |
| Control logic | RTL | RTL (변화 없음) |

결과:

- 시뮬레이션 시간: 12 hr → 5 min (~140×)
- Regression: 100 testcases가 한 주말에 → 한 시간에
- Coverage: 동일 또는 향상 (voltage bin 추가)

### 3.2 Mixed-Signal SoC UVM-DMS — 산업 적용

상황: 모바일 AP의 PMIC + I/O + ADC 통합 검증
- 단일 UVM-DMS 환경에서 모든 mixed-signal 통합
- AMS는 sign-off corner만

핵심 결과:

- UVM scoreboard가 digital + voltage 동시 검사 가능
- Power state transition coverage 자동화
- 같은 sequence library를 RNM/AMS 양쪽에 재사용

## 4. RNM/AMS 검증 흐름 — 단계별 체크리스트

### Phase 1 — Architectural (early design)

- [ ] DUT을 digital/mixed-signal block으로 분해
- [ ] Mixed-signal block마다 RNM 모델 작성
- [ ] UVM 환경 구축, mixed-signal layer 통합
- [ ] Functional regression — 모든 시나리오 RNM으로

### Phase 2 — Pre-silicon corner

- [ ] Critical block (SA, VCO, BGR)에 대해 SPICE Monte Carlo
- [ ] Process corner (SS/FF) × Temperature (-40/25/125) × Voltage (Vmin/Vnom/Vmax)
- [ ] RNM의 σ를 SPICE Monte Carlo 결과로 backannotate

### Phase 3 — Sign-off

- [ ] AMS로 top-level cycle 한두 개 검증 (sanity)
- [ ] IBIS-AMI로 IO eye margin 검증
- [ ] Coverage closure (voltage bin × digital state)
- [ ] Regression report — pass rate + fail rate analytics

### Phase 4 — Silicon

- [ ] ATE shmoo plot
- [ ] RNM 모델 calibration
- [ ] BIST + redundancy repair → 양산

## 5. 실패 패턴 (Common Pitfalls in DMS)

### 5.1 wreal만으로 multi-driver 충돌 무시

```systemverilog
wreal supply_rail;
// 여러 module이 supply_rail에 voltage를 contribute
// → wreal는 single-driver 가정 → silent overwrite
```

**해결**: UDN + resolution function.

### 5.2 SPICE-RNM 결과 불일치 무시

RNM 모델은 SPICE 결과를 흉내내는 함수. **Process/temp/voltage corner마다 재추출 필요.**

**해결**: 자동 backannotation 스크립트 — SPICE Monte Carlo 결과 → RNM parameter.

### 5.3 Abstraction switching configuration drift

```
// Day 1: SA는 RNM
// Day 30: 누군가 SA를 SPICE로 바꿈
// Day 60: 다시 RNM으로... but spice file의 변경 사항 lost
```

**해결**: 모든 abstraction을 git 관리, regression matrix로 추적.

### 5.4 UVM phase mismatch

RNM 모델 안에서 `initial begin` 으로 random offset 설정 → UVM run phase 시작 전 → seed 동기화 안 됨.

**해결**: `build_phase`에서 RNM parameter override (via `uvm_config_db`).

### 5.5 Coverage가 digital만 — voltage 미반영

```systemverilog
covergroup cg_old;
  cp : coverpoint d_signal {bins zero = {0}; bins one = {1};}
endgroup
// voltage bin이 없음 → corner 누락
```

**해결**: voltage/current/impedance를 coverpoint로 명시.

## 6. 대표 문제 — Mixed-Signal SoC 검증 환경 설계

### 문제

다음 요구사항을 만족하는 mixed-signal SoC 검증 환경을 설계하시오:

1. DDR5 PHY (DLL + IO buffer + SA) — 80% RNM, 20% SPICE corner
2. PMIC (buck + LDO) — 100% DMS (UDN)
3. ADC — 검증은 RNM, MC sign-off는 SPICE
4. UVM-based 환경, 모든 시나리오 single regression
5. 빌드 시간 ≤ 1 hour, 시뮬 시간 ≤ 30 min per testcase

### 풀이

```
┌─────────────────────────────────────────────────────────────┐
│                    Top UVM Test                              │
└─────────────────────────────────────────────────────────────┘
                          │
┌─────────────────────────────────────────────────────────────┐
│                    UVM env                                    │
│  ┌──────────┐  ┌────────────┐  ┌──────────┐  ┌─────────────┐│
│  │ AXI ag.  │  │ Power ag.  │  │ DDR ag.  │  │ ADC ag.     ││
│  │ digital  │  │ UDN-aware  │  │ digital  │  │ wreal in/out││
│  └──────────┘  └────────────┘  └──────────┘  └─────────────┘│
│                       │ coverage + scoreboard                 │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                       DUT                                     │
│                                                                │
│  ┌──────────────────┐  ┌──────────────────┐                  │
│  │ DDR5 PHY         │  │ PMIC             │                  │
│  │  - DLL: RNM      │  │  - Buck: UDN     │                  │
│  │  - IO: RNM       │  │  - LDO: UDN      │                  │
│  │  - SA: RNM/SPICE │  └──────────────────┘                  │
│  └──────────────────┘  ┌──────────────────┐                  │
│                          │ ADC: RNM         │                  │
│                          └──────────────────┘                  │
└─────────────────────────────────────────────────────────────┘
```

핵심 결정:

- **PMIC**: UDN(EEnet) 모델 — Thevenin resolution. Spectre 없이 검증.
- **DDR5 PHY**: 80% RNM. SA는 +define+ 으로 abstraction switching.
- **ADC**: RNM functional, SPICE Monte Carlo는 별 nightly regression.
- **Regression**: nightly 2개 — DMS-only (빠름) + DMS+SPICE corner (sign-off).

### 통찰

- UDN + abstraction switching이 핵심 — wreal 단독 환경으로는 PMIC 불가
- UVM coverage가 voltage + digital 동시 — 새 covergroup 작성 필요
- 1 hour build, 30 min sim 목표는 SA 대부분을 RNM으로 두어야 가능

## 7. 핵심 정리

1. DMS (RNM) 우선, AMS는 sign-off 보완 — 100×~1000× 속도 향상 가능
2. 단순 wreal는 한계 — **UDN/EEnet**으로 multi-driver, impedance 처리
3. UVM 환경에 RNM/AMS layer 통합 — agent · scoreboard · coverage 확장
4. Abstraction switching으로 같은 block을 RNM/SPICE 전환 가능
5. Coverage는 **digital + voltage 동시** — 새 covergroup 작성 필수

## References (DVCon proceedings)

- *"Novel Mixed Signal Verification Methodology using complex UDNs"* — DVCon
- *"Mixed-Signal Design Verification: Leveraging the Best of AMS and DMS"* — DVCon
- *"Enabling Digital Mixed-Signal Verification of Loading Effects in Power Regulation Using SystemVerilog User-Defined Nettypes"* — DVCon
- *"Scalable Re-usable UVM DMS/AMS Based Verification Methodology for Mixed-Signal SoCs"* — DVCon
- *"Harnessing SV-RNM Based Modelling and Simulation Methodology for Verifying a Complex PMIC designed for SSD Applications"* — DVCon
- Ignitarium blog: *"System Verilog EEnet (SV-EEnet) application: Modeling block currents in Mixed Signal Verification"*

## 더 읽을거리

- 다음: [Ch11. 도구 지형](11_tools_ecosystem.md)
- 퀴즈: [Ch10 퀴즈](quiz/ch10_quiz.md)
