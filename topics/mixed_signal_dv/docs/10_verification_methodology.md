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

이 챕터를 제대로 읽으려면 먼저 용어를 정리해야 합니다. "DMS"는 **Digital Mixed-Signal**의 약자로, 디지털 시뮬레이터만으로 RNM 기반 mixed-signal 검증을 수행하는 방법론을 뜻합니다. "AMS"는 이 챕터에서 Verilog-AMS 언어를 기반으로 digital + SPICE를 결합하는 좁은 의미로 쓰입니다. 실무에서는 두 방식을 경쟁 관계로 보지 않고 **"DMS 우선, AMS 보완"** 원칙으로 조합합니다.

| 항목 | DMS (Digital Mixed-Signal) | AMS (Analog Mixed-Signal) |
|---|---|---|
| 신호 표현 | Real (event-driven) | Electrical (continuous) |
| 시뮬레이터 | Digital만 | Digital + SPICE |
| 모델링 언어 | SystemVerilog (RNM) | Verilog-AMS, SPICE netlist |
| 속도 | 100×~1000× faster | Baseline |
| 정확도 | 모델 정확도에 의존 | SPICE 수준 |
| 적용 | SoC 전체, 시나리오 검증 | 단일 block, sign-off |

DVCon paper들이 반복해서 검증한 메시지는 하나입니다. **"DMS를 우선, AMS를 보완으로"**. 전체 회귀는 DMS로 수천 seed를 하루에 돌리고, SPICE 정확도가 꼭 필요한 critical block의 corner check만 AMS로 별도 진행합니다. 이 구조가 없으면 전체 회귀 속도가 SPICE에 묶여 버립니다.

> **용어 주의:** 이 표의 "AMS"는 **Verilog-AMS 언어** (좁은 의미)입니다. Accellera **"UVM-AMS" working group**이나 EDA 벤더 제품명("VCS-AMS", "AMS Designer", "Questa-AMS")에서 쓰이는 "AMS"는 **RNM까지 포함하는 우산 용어**로, 이 책의 **DMS + AMS를 모두 포괄**합니다. 두 용법의 차이는 Ch02 §5.1 참조.

> **용어 주의:** 이 표의 "AMS"는 **Verilog-AMS 언어** (좁은 의미)입니다. 한편 Accellera **"UVM-AMS" working group**이나 EDA 벤더 제품명("VCS-AMS", "AMS Designer", "Questa-AMS")에서 쓰이는 "AMS"는 **RNM까지 포함하는 우산 용어**로, 이 책의 **DMS + AMS를 모두 포괄**합니다. 두 용법의 차이는 Ch02 §5.1 참조.

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

## 6. 흔한 함정 — RNM 일반 10가지

§5의 DMS-specific 함정에 더해, RNM 일반에서 반복적으로 발견되는 false-pass 패턴입니다. 실무에서 가장 자주 등장하는 순서.

### ① real에는 X가 없다

`real` 변수는 default가 `0.0`. uninitialized supply, 잊고 안 잡은 ADC 입력이 silently 0 V로 보이고, "ADC code = 0"이 spec에 부합하면 testbench가 **잘못된 PASS**를 냅니다.

```systemverilog
// 잘못된 패턴
real vin;
adc u_adc(.vin(vin), .code(code));   // vin 안 잡혔는데 PASS

// 안전 패턴: valid bit 동반
typedef struct { real V; bit valid; } sig_t;
property p_inp_valid;
  @(posedge clk) inp.valid;
endproperty
assert property (p_inp_valid) else $error("input not driven");
```

> 모든 RNM port에 **valid bit 또는 driver-presence assertion**을 강제하세요. tape-out 직전에 발견되는 false-pass의 상당수가 "uninitialized real = 0.0" 패턴입니다.

### ② Multi-driver는 silently 마지막 값

plain `real` variable에 두 곳에서 write하면 simulator가 막지 않습니다. last-write-wins라 race condition이 숨습니다. 반드시 `nettype`으로 만들어 resolution function이 호출되게 하세요 (Ch05 §13).

### ③ Noise는 자동으로 생기지 않는다

RNM은 deterministic. thermal · flicker · supply noise는 손으로 주입해야 합니다. spec에 "noise 5 mVrms"가 있으면 모델에 `$dist_normal`로 매 sample마다 더해줘야 의미 있는 검증.

```systemverilog
real noise;
always @(posedge sample_clk) begin
  noise = $dist_normal(seed, 0, 5000);   // μ=0, σ=5000 (μV)
  vin_noisy = vin + noise * 1e-6;
end
```

> `$dist_normal`은 σ를 integer로 받는 simulator가 있어 단위 스케일을 미리 고려해야 합니다. **noise on/off control bit**를 둬서 functional 회귀와 noise 회귀를 분리하는 것이 일반적.

### ④ Spice cosim boundary가 많으면 100× 느려진다

Spice 도메인의 시간 step은 femto~pico 초, digital은 nano~micro. boundary가 잦으면 cosim simulator가 두 도메인을 synchronize하느라 wall time이 폭증합니다.

**나쁜 partition 신호**: 한 IP를 Spice + RNM로 잘게 쪼개 boundary 다수 / fast switching 신호가 boundary를 가로지름 / cosim wall time이 pure RNM의 100~1000×

### ⑤ real 비교에 `==`를 쓰지 마라

```systemverilog
if (vout == 1.0) ...                          // ❌ 거의 항상 false
if ($abs(vout - 1.0) < 1e-6) ...              // ✓
`define REAL_EQ(a,b,eps) ($abs((a)-(b)) <= (eps))     // 매크로 표준
```

### ⑥ Sub-event step 부족으로 인한 aliasing

sine wave를 step 10개로 그리면 simulator는 그 10개 점에서만 sample을 봅니다. monitor가 zero-crossing을 놓치거나 peak이 잘못 잡힙니다. **cycle 당 100 step 이상**이 일반적 출발점.

### ⑦ Coverage가 의미 없을 수 있다

"`vin`이 0~1.8 V를 100% 채웠다" — bin 100%이지만 실제로는 ramp 한 번 친 것뿐일 수 있습니다. **transition coverage · cross coverage · directed test 결과 조합**이 필요합니다.

### ⑧ behavioral ↔ Spice equivalence는 자동화가 약하다

digital의 LEC에 해당하는 mixed-signal 도구는 성숙도가 낮습니다. 결국 같은 testbench를 두 모델에 돌려 출력 차이를 보는 **회귀 기반 equivalence**가 현실. 차이가 spec tolerance 안인지를 사람이 판정해야 합니다.

### ⑨ Random seed 한계

digital 검증의 "`+ntb_random_seed` 1000개"가 analog 입력 공간 도달도를 자동으로 늘려주지 않습니다. real range를 constraint로 명시하지 않으면 솔버가 항상 비슷한 값을 뽑습니다. **covergroup feedback** 또는 directed corner test로 보완.

### ⑩ 시뮬레이션은 통과해도 silicon이 다를 수 있다

RNM은 spec을 코드화한 것입니다. **실리콘은 spec을 100% 따르지 않습니다**. 검증 통과 = 정확성 보장이 아니라, "spec과 model이 일치한다"의 보장. silicon bring-up에서 model gap이 드러날 가능성을 항상 열어두고, bring-up 측정값을 model에 feedback 하는 흐름을 둬야 다음 세대에 같은 함정을 피합니다.

> mixed-signal 검증의 PASS는 **"이 모델이 본 범위 안에서 spec과 일치"** 이상의 의미를 갖지 않습니다. 모델이 본 것과 안 본 것을 명문화하지 않으면 검증 결과의 신뢰 범위를 잘못 해석할 위험이 큽니다.

## 7. Coverage 전략 심화 — V-plan 매핑과 escape analysis

§2의 Pattern 4가 coverage 작성 패턴이라면, 이 절은 **전략 레벨**입니다. mixed-signal coverage는 **structural coverage가 거의 의미 없고** 대부분의 신뢰는 spec 기반 functional coverage에서 옵니다 — analog DUT가 보통 RTL이 아니라 RNM behavioral 또는 Spice netlist이기 때문.

### 7.1 coverage 종류별 의미

| 종류 | 대상 | MS에서의 의미 |
|---|---|---|
| code coverage (line/branch/cond) | RTL | digital control RTL만 의미. analog 모델엔 적용 안 함 |
| toggle coverage | signal toggling | register 토글 정도, analog real 신호는 의미 없음 |
| FSM coverage | state machine | cal FSM, calibration sequencer에 유용 |
| **functional coverage (covergroup)** | verification 의도 | **MS coverage의 본체** |
| assertion coverage | SVA cover property | spec 조건 도달 여부 |
| scenario / spec coverage | V-plan item | 회귀 보고의 상위 단위 |

### 7.2 V-plan ↔ coverage 1-1 매핑

Verification plan(V-plan)의 항목 하나하나가 coverage point 또는 directed test에 매핑되어야 합니다. 도구가 V-plan을 import해 회귀 결과와 자동 매핑하는 기능(VC Verification Planner, vManager 등)이 있어 활용 권장.

```text
V-plan 항목                          ┌── 자동 매핑 ──┐
"VIN sweep 0~1.8 V"           ←──    cg_adc.cp_vin          (100% 도달 시 close)
"OOB 입력은 saturation"        ←──    cover property p_sat
"PVT corner 9가지"             ←──    cg_pvt.cross
"calibration 5단계 모두"        ←──    fsm_cov[cal_fsm]
"noise on/off 둘 다 회귀"      ←──    directed test list
                                  └──────────────────────┘
```

### 7.3 covergroup의 5가지 책임

- **① Input space** — 입력 신호 (vin, vref, freq, ampl)의 범위 binning. spec 경계점이 bin edge에 정렬되었는가
- **② Output space** — 출력 (code, lock_status, eoc count)의 도달도. boundary 코드, saturation 코드 명시
- **③ Cross** — 입력 × 환경(PVT) × 모드의 조합. spec이 명시한 corner만 직접 cover
- **④ Sequence** — state machine 전이, retry/abort 같은 시간 의존 패턴
- **⑤ Illegal/Ignore** — OOB는 illegal로 명시, off-mode 조합은 ignore — 도달 안 해도 100%로

### 7.4 도달도 ≠ 검증도 — 회귀 게이트

100% bin hit이 곧 PASS가 아닙니다. **hit + scoreboard pass**가 동시에 성립해야 의미 있는 진척. 단순 hit은 stim이 거기 갔다는 것뿐.

```systemverilog
function void env::report_phase(uvm_phase phase);
  bit pass = 1;
  if (sb.mismatched > 0)                  pass = 0;
  if (cg_adc.get_inst_coverage() < 100.0) pass = 0;
  if (sb.matched < 1000)                  pass = 0;     // 도달 했어도 횟수 sanity
  if (!pass) `uvm_error("RES", "FAIL")
endfunction
```

### 7.5 coverage merge across regressions

UVM 회귀는 보통 수십~수천 seed가 farm에서 병렬로 돕니다. 각 run의 coverage db를 merge해야 진짜 도달도가 나옵니다.

- **VCS**: `urg -dir db1 db2 ...` 또는 `urg -dir <list>`
- **Xcelium**: `imc -execcmd "merge ..."` 또는 IMC GUI
- **Questa**: `vcover merge ...`
- 일관된 testbench config로 돌린 db만 merge — 다른 config는 noise

### 7.6 Escape analysis — 안 본 corner

coverage가 90% 근처에서 정체될 때 남은 10%가 "왜 도달 못 하는가"를 분석해야 합니다.

| 카테고리 | 증상 | 대응 |
|---|---|---|
| constraint 불충분 | random이 좁은 범위만 hit | weighted dist 추가, narrow range 명시 |
| 의미상 도달 불가 | spec이 금지하는 조합 | `illegal_bins` 또는 `ignore_bins`로 명시 |
| solver hint 부족 | cross가 너무 광범위 | `solve before`로 ordering, sub-cross 분해 |
| scenario 누락 | directed로만 도달 가능 | directed test 추가 (random 의존 X) |
| tool bug | vendor coverage 누락 | vendor 문의, workaround |

> escape analysis는 회귀 마무리 단계의 핵심 작업. **"왜 못 도달하는가"**를 한 줄로 답할 수 없으면 그 corner는 검증 안 된 것으로 봅니다. tape-out 직전엔 모든 미도달 bin에 **명시적 이유 + 책임자**가 적힌 표가 있어야 합니다.

### 7.7 analog spec → coverage 정의 절차

1. spec에서 **입력 범위 · 출력 범위 · 경계값 · PVT corner · operation mode** 추출
2. 경계값을 bin edge로 두고 covergroup 1차 draft
3. illegal/ignore bin을 명시 — 도달 안 해도 좋은 영역
4. V-plan item과 coverage point 1-1 매핑 표 작성
5. directed test list와 random regression의 분담 명시
6. coverage merge 절차 · 게이트 조건 (e.g. 95% 도달 + 0 mismatch) 명시
7. 회귀 시작 후 매 sprint마다 coverage 추이 + escape analysis

> coverage 정의는 "한 번 만들고 끝"이 아닙니다. spec 변경 · 새 silicon 측정 · regression learning이 들어올 때마다 업데이트되어야 합니다. **stale coverage는 stale plan보다 위험** — 100%인데 검증 안 된 corner를 만듭니다.

## 8. Debug 전략 — 책임 소재 좁히기

fail이 발생했을 때 책임 소재가 한 곳이 아닙니다 — **RNM model bug · digital RTL bug · reference model bug · scoreboard tolerance · random seed의 미스코너**까지 다섯 가지 후보가 매번 똑같이 발생합니다. 좋은 debug 전략은 **책임 소재를 빠르게 좁히는 도구**를 미리 갖추는 것.

### 8.1 첫 한 시간 안에 좁힐 5가지

| 카테고리 | 증상 | 1차 확인 |
|---|---|---|
| RNM model bug | 특정 corner에서만 출력 이상 | Spice cosim과 단일 vector 비교 |
| digital RTL bug | register/FSM 시점 어긋남 | RTL 단독 unit test 통과 여부 |
| reference bug | 모든 seed 동일 패턴 mismatch | spec example로 ref unit test |
| scoreboard tolerance | borderline 위반만 다수 | tol 한시적 완화 → 패턴 변화 관찰 |
| seed가 미스코너 | 특정 seed에서만 fail | seed 재현, sub-test 분리 |

### 8.2 wave dump 옵션 — real 신호도 잡혀야

FSDB · VCD · SHM은 default로 digital 신호만 dump합니다. **real 신호와 nettype payload를 dump 옵션에 명시**해야 debug 가능.

```systemverilog
initial begin
  `ifdef DUMP_FSDB
    $fsdbDumpfile("dump.fsdb");
    $fsdbDumpvars(0, tb_top, "+all");
    $fsdbDumpMDA(0, tb_top);           // multi-dim arrays
    $fsdbDumpSVA(0, tb_top);           // assertions
    $fsdbDumpFlush;
  `endif
end
```

- **nettype 신호**는 struct payload 전체가 dump되어야 함 — vendor마다 옵션 다름 (예: `-dump_real`, `-fsdb_dump_real`)
- **`$fsdbDumpvars`** depth를 0으로 — top부터 전부. analog wave는 hierarchy 깊은 곳에 있을 가능성 큼
- **dump 주기**는 sub-event step과 같거나 더 짧게 — sample rate가 dump보다 빠르면 신호가 step처럼 보임

### 8.3 log 규약 — "fail = grep"

UVM의 `uvm_info/uvm_error`를 그냥 쓰면 fail debug가 한 두 시간 더 걸립니다. log를 grep-friendly로:

```systemverilog
`uvm_info("ADC_SB",
  $sformatf("[%0t] vin=%0.6f exp_code=%0d obs_code=%0d diff=%0d",
            $realtime, e.vin_volt, e.code_expected, o.code,
            e.code_expected - o.code),
  UVM_HIGH)
```

- **id field**를 IP/agent별로 분리 — "ADC_SB", "PLL_DRV" → grep으로 즉시 좁혀짐
- 각 줄에 **`$realtime`** 강제 — race 분석의 첫 단서
- **`%0.6f`** 명시 — default `%f` 6자리 round-off 함정
- fail 직후 **관련 신호 dump**를 한 번 더 출력 — "compare fail이면 ±N cycle dump"

### 8.4 Replay — fail seed 재현

random regression의 fail은 **seed로 재현 가능**해야 합니다. 그렇지 않으면 debug 불가능.

- UVM seed는 `+ntb_random_seed` 또는 `UVM_TESTNAME`과 함께 기록
- SystemVerilog의 `$urandom` 직접 호출 금지 — 항상 sequence_item 내부 randomize
- DPI seed도 sequence_item에서 받아 전달
- 회귀 결과에 seed list + fail seed subset 자동 보관

```bash
$ ./run_one.sh +UVM_TESTNAME=adc_sweep +ntb_random_seed=4214113 \
                +DUMP_FSDB +UVM_VERBOSITY=UVM_HIGH \
                +TOL_RELAX=2
# dump.fsdb + run.log 가 생성 → Verdi에서 dump.fsdb 열고 log timestamp로 점프
```

### 8.5 Model bug vs DUT bug 구별법

scoreboard fail이 났을 때 RNM model이 잘못된 건지 진짜 digital RTL이 잘못된 건지를 빠르게 가르는 방법.

| 실험 | 결과 → 의심 |
|---|---|
| Spice netlist로 같은 입력 cosim | Spice도 fail → DUT bug, Spice pass → RNM model bug |
| RNM model을 spec example로 unit test | example도 fail → model bug |
| reference로 직접 spec table 값 비교 | reference가 spec과 안 맞음 → reference bug |
| 이전 RTL revision으로 회귀 | 이전엔 pass → 최근 RTL 변경이 원인 |
| tolerance를 spec band까지 완화 | 그래도 fail → 의미 있는 위반, 좁은 corner |

### 8.6 Flaky test — "가끔 fail"이 아니라 "가끔 pass인 fail"

가끔 fail이 나는 test가 가장 무섭습니다. 보통 다음 패턴:

- **race condition** — `clocking` block 누락, NBA region 의존
- **numerical 누적** — FP 라운딩 누적이 seed에 따라 다르게 떨어짐 — tolerance를 후하게
- **uninitialized real** — 첫 cycle 동안만 fail — power-on assertion 보강
- **jitter/noise 모델 변동** — Box-Muller seed 분리 누락

> flaky test는 "가끔 fail이라 무시"가 아니라 **"가끔 pass인 fail"**로 봐야 합니다. tape-out에 가까울수록 위험. 발견 즉시 isolate해서 별도 fix branch로 옮기고, root cause 명시 전까지 회귀에서 제외하지 말 것 (silently 약해집니다).

### 8.7 Nightly regression 운영 권장

- seed 리스트는 빌드와 함께 commit → 재현성
- fail 자동 분류 (logged `uvm_error` id → 카테고리) → triage 부담 ↓
- pass rate trend를 매일 보고 — 갑작스런 떨어짐은 회귀 신호
- FSDB는 fail seed만 보관 (대용량) → storage 비용 관리
- coverage db는 누적, fail log는 일정 기간 후 archive
- 매주 escape analysis: 도달 안 한 corner의 책임자/대응 명시

## 9. 대표 문제 — Mixed-Signal SoC 검증 환경 설계

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

## 10. 핵심 정리

1. DMS (RNM) 우선, AMS는 sign-off 보완 — 100×~1000× 속도 향상 가능
2. 단순 wreal는 한계 — **UDN/EEnet**으로 multi-driver, impedance 처리
3. UVM 환경에 RNM/AMS layer 통합 — agent · scoreboard · coverage 확장
4. Abstraction switching으로 같은 block을 RNM/SPICE 전환 가능
5. Coverage는 **digital + voltage 동시** — 새 covergroup 작성 필수
6. RNM 일반 함정 10가지 — `real`엔 X 없음, last-write-wins multi-driver, deterministic noise, ==, aliasing, 의미 없는 100%, equivalence gap, seed 한계, sim ≠ silicon
7. Coverage 전략: V-plan 1-1 매핑 → 도달도+scoreboard 게이트 → escape analysis 의무화
8. Debug 전략: 첫 한 시간 5가지 후보 triage, real wave dump 옵션, grep-friendly log, seed 재현, model vs DUT bug 분리 실험

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
