---
title: "Ch11. 도구 지형 — VCS-AMS · AMS Designer · Questa-AMS · IBIS-AMI"
---

## 학습 목표

- **(Remember)** Synopsys / Cadence / Siemens EDA 3대 벤더의 mixed-signal 시뮬레이션 도구를 진술할 수 있다
- **(Understand)** 각 도구의 강점·약점·라이센스 모델을 설명할 수 있다
- **(Apply)** 주어진 검증 task에 적합한 도구 조합을 추천할 수 있다
- **(Evaluate)** RNM-only vs AMS vs IBIS-AMI 도구의 적합성을 결정할 수 있다

## 1. 도구 카테고리 정리

도구를 선택하기 전에 먼저 도구 지형 전체를 한 눈에 볼 필요가 있습니다. (**EDA** = Electronic Design Automation, 반도체 설계·검증을 자동화하는 소프트웨어 분야. **vendor**는 이런 도구를 만드는 공급사 — Synopsys·Cadence·Siemens EDA가 3대 vendor입니다.) mixed-signal 검증에서 쓰이는 도구는 다섯 가지 카테고리로 나뉩니다. SPICE는 정확도의 기준점이지만 느립니다. Fast SPICE는 속도를 높여 DRAM full-chip에도 적용할 수 있습니다. AMS는 digital sim과 SPICE를 결합합니다. Pure RNM은 별도 SPICE 엔진 없이 디지털 시뮬레이터만으로 mixed-signal을 처리합니다. IBIS-AMI는 SerDes와 DDR 같은 고속 인터페이스의 system-level 검증 표준입니다.

| 카테고리 | 대표 도구 | 특징 |
|---|---|---|
| SPICE | HSPICE, Spectre, Eldo, FineSim | 정확도 표준, 느림 |
| Fast SPICE | CustomSim, FineSim Pro, UltraSim | DRAM full-chip 가능 |
| AMS | VCS AMS, AMS Designer, Questa AMS | digital + SPICE 결합 |
| Pure RNM | VCS, Xcelium, Questa | digital simulator만으로 RNM |
| IBIS-AMI | MATLAB SerDes, ADS, HyperLynx | SerDes/DDR system 검증 |

이 중 "어떤 도구를 언제 쓰느냐"의 판단 기준은 단순합니다. 트랜지스터 물리 정밀도가 필요한지, 회로 규모가 얼마인지, 채널 특성까지 봐야 하는지에 따라 선택이 결정됩니다. 자세한 결정 트리는 §7에서 다룹니다.

## 2. SPICE 도구

SPICE 도구들은 정확도 측면에서 silicon에 가장 가깝습니다. 어떤 도구를 쓰느냐보다 "어떤 foundry의 `.lib` 파일을 쓰느냐"가 더 중요합니다. 도구 자체는 벤더와 팀 성향에 따라 선택됩니다.

| 도구 | 벤더 | 특징 |
|------|------|------|
| **HSPICE** | Synopsys | "Gold reference" — silicon 가장 가까움. Sign-off 표준 |
| **Spectre** | Cadence | 아날로그 설계 흐름에서 흔함 (Virtuoso 통합) |
| **FineSim** | Synopsys | 빠른 SPICE. AMS 통합 잘 됨 |
| **Eldo** | Siemens EDA | 군용/항공우주에서 자주 (보안 인증) |

라이센스는 모두 enterprise 수준으로 비쌉니다. node-locked과 floating의 혼합 형태가 일반적이며, 이 비용이 RNM의 비용 우위를 만드는 핵심 배경입니다.

## 3. Fast SPICE 도구

| 도구 | 벤더 | 강점 |
|------|------|------|
| **CustomSim XA** | Synopsys | DRAM full-chip, post-layout 강함 |
| **FineSim Pro** | Synopsys | Fast + accurate 균형 |
| **UltraSim** | Cadence | Spectre 호환 |
| **Eldo Premier** | Siemens EDA | Foundry corner |

→ DRAM 검증에서 거의 필수. 일반 SPICE 대비 **10~100× 속도**.

## 4. AMS 도구

| 도구 | 벤더 | 디지털 엔진 | 아날로그 엔진 |
|------|------|------------|--------------|
| **AMS Designer** | Cadence | Xcelium | Spectre |
| **VCS AMS** | Synopsys | VCS | FineSim / HSPICE / CustomSim |
| **Questa AMS** | Siemens EDA | Questa | Eldo |
| **CustomSim AMS** | Synopsys | VCS | CustomSim |

### 4.1 Synopsys VCS AMS — 산업 1위 사례

핵심 특징 (공식 datasheet, 2024 기준):

- Native low-power(NLP) 기술 확장 — **UPF**(Unified Power Format — 전원 도메인·전원 끄기 등 저전력 의도를 기술하는 표준) mixed-signal 지원
- SystemVerilog · Verilog · VHDL · Verilog-AMS · SPICE **모두 한 환경에서**
- **Post-layout**(레이아웃 완료 후 실제 배선의 기생 저항·용량을 반영한 단계): SPF · DSPF · SPEF(레이아웃에서 추출한 기생 성분을 담은 표준 파일 형식들) 형식 지원
- AMS Testbench — UVM 기반 mixed-signal 검증 환경
    - Analog node에 assertion/checker
    - Analog node monitoring + sampling
    - Constraint-random for analog driver
- Co-simulation: VCS + CustomSim 결합 — 대용량 칩 가능

### 4.2 Cadence AMS Designer

- Virtuoso 흐름과 깊은 통합
- Xcelium(SV/UVM) + Spectre(SPICE)
- AMS Connect Library — 자동 connectrule 매칭

### 4.3 Siemens EDA Questa AMS

- Questa(SV/UVM) + Eldo(SPICE)
- 공정 corner 라이브러리 강함 (foundry independent)

## 5. Pure RNM — Digital Simulator만으로

RNM은 사실상 **SV 표준 기능**(IEEE 1800-2017 § 6.6.7)이라 도구 종속성이 낮습니다:

| 도구 | 벤더 | wreal/nettype 지원 |
|------|------|------------------|
| **VCS** | Synopsys | ✓ (성숙) |
| **Xcelium** | Cadence | ✓ (성숙) |
| **Questa** | Siemens EDA | ✓ (성숙) |
| Verilator (오픈소스) | — | △ (제한적, 일부 nettype 미지원) |

→ 일반 digital simulator만 있으면 RNM 가능. **AMS 도구 없어도 됩니다.** 이게 RNM의 핵심 장점.

## 6. IBIS-AMI 도구

DDR5/PCIe Gen5+ 등 고속 인터페이스 system 검증용:

| 도구 | 벤더 | 특징 |
|------|------|------|
| **MATLAB SerDes Toolbox** | MathWorks | DDR5 controller/SDRAM IBIS-AMI 라이브러리, back-channel training |
| **Keysight ADS** | Keysight | 고급 channel simulation, statistical eye |
| **HyperLynx SI/PI** | Siemens EDA | PCB 통합, eye/jitter sweep |
| **Cadence Sigrity** | Cadence | PCB + IC 통합 |
| **eCADSTAR** | Zuken | mid-range, IBIS 호환 |

표준: **IBIS 7.x** (2019+) — PAM modulation, back-channel link training (DDR5 spec).

## 7. 도구 선택 결정 트리

```d2
direction: down

start: "검증 task 시작"
q_serdes: "SerDes / DDR5 channel · eye sign-off?" {shape: diamond}
ibis_ami: "IBIS-AMI 도구\n(MATLAB SerDes, ADS, HyperLynx)"
q_size: "Block 크기\n(transistor 수)" {shape: diamond}
spice: "SPICE\n(HSPICE, Spectre)\n< 1k"
fast_spice: "Fast SPICE\n1k ~ 10k"
ams: "AMS\n(VCS AMS / AMS Designer / Questa AMS)\n10k ~ 1M"
rnm: "RNM\n(VCS / Xcelium / Questa)\n+ critical block AMS\n> 1M"

start -> q_serdes
q_serdes -> ibis_ami: "Yes"
q_serdes -> q_size: "No"
q_size -> spice
q_size -> fast_spice
q_size -> ams
q_size -> rnm
```

## 8. 라이센스 / 비용 고려

| 영역 | 일반 비용 (참고) | 라이센스 형식 |
|---|---|---|
| SPICE | 매우 비쌈 (수 만 ~ 수십 만 USD/year per seat) | floating + node-lock |
| Fast SPICE | SPICE보다 추가 | 동일 |
| AMS | digital + SPICE 두 종 라이센스 | 별도 추가 |
| Pure RNM | digital simulator만 | digital sim 라이센스만 |
| IBIS-AMI | MathWorks SerDes Toolbox 라이센스 등 | 비교적 저렴 |

→ **RNM의 비용 우위**: 추가 SPICE 라이센스 없이 mixed-signal 검증 가능.

## 9. 표준 / 언어 지형

| 표준 | 발행 | 핵심 기능 |
|------|------|-----------|
| **SPICE** (de-facto) | UCB 1973~ | netlist + 분석 |
| **Verilog-AMS** | IEEE 1364.1 / VAMS-2023 (Accellera 2024-02) | electrical, analog begin, `<+` |
| **VHDL-AMS** | IEEE 1076.1 | VHDL mixed-signal |
| **SystemVerilog-AMS** | Accellera draft | SV mixed-signal (널리 안 쓰임) |
| **nettype (SV 2012)** | IEEE 1800-2012 § 6.6.7 | RNM 핵심 |
| **IBIS** | IBIS Open Forum 7.2 | SerDes 표준 |
| **IBIS-AMI** | IBIS 7.x | back-channel, PAM |

## 10. 대표 문제 — 도구 조합 선택

### 문제

다음 4개 검증 task에 어떤 도구 조합이 적합한가?

1. DDR5 SDRAM PHY full-chip functional regression (5,000 testcases)
2. PMIC buck regulator step-load response analysis (부하 전류가 계단처럼 급변할 때 출력 전압이 어떻게 회복되는지 분석)
3. PCIe Gen5 link training back-channel training 검증
4. Bandgap reference voltage corner sign-off

### 풀이

| Task | 도구 조합 | 이유 |
|---|---|---|
| 1. DDR5 PHY full-chip | VCS (RNM) + UVM | 5000 testcase는 RNM 필수. AMS 너무 느림 |
| 2. PMIC buck | VCS AMS (RNM + corner SPICE) 또는 Spectre AMS | Power loop dynamics는 RNM, voltage accuracy는 SPICE corner |
| 3. PCIe Gen5 back-channel | MATLAB SerDes / ADS (IBIS-AMI 7.0+) | back-channel training 표준 |
| 4. BGR voltage sign-off | HSPICE (Monte Carlo) | BGR은 작은 회로 — SPICE로 충분 |

### 통찰

- 도구 선택은 **블록 크기 + 검증 type + 정확도 요구**의 함수
- DDR5 PHY 같은 거대 mixed-signal block은 RNM이 유일 현실적 선택
- BGR 같은 작은 critical block은 SPICE Monte Carlo가 적합
- SerDes는 IBIS-AMI가 표준 — 자체 모델보다 벤더 모델 활용

## 11. 추천 학습 경로

UVM/SoC DV 경험자가 mixed-signal 도구를 익힐 때:

1. **VCS / Xcelium / Questa**의 RNM (`nettype`, `wreal`) — 가장 쉬움
2. **Spectre / HSPICE**의 transient 분석 — 작은 회로부터
3. **VCS AMS / AMS Designer**의 connectrule + abstraction switching
4. **CustomSim / FineSim Pro**의 Fast SPICE — DRAM 검증
5. **MATLAB SerDes Toolbox / ADS** — IBIS-AMI

## 12. Tool 호환성 체크리스트 — 새 IP를 받을 때

같은 RNM 코드의 portability는 보장되지 않습니다. 새 IP를 받으면 다음을 **elaborate 시점에** 확인해야 vendor lock-in으로 인한 회귀 실패를 줄일 수 있습니다.

| 항목 | 확인 방법 | 실패 시 증상 |
|---|---|---|
| `nettype` resolution function 지원 (특히 struct payload) | 최소 모델 elaborate | elaboration error 또는 silent type mismatch |
| `interconnect` 지원과 nettype binding 규칙 | top-level instance binding | port type resolve 실패 |
| `real` covergroup binning 지원 | 간단한 covergroup sample 후 report 확인 | bin 0%로 표시되거나 warning |
| `rand real` 지원과 constraint 솔버 한계 | rand class 1개 randomize | UVM_ERROR with constraint conflict |
| `$realtime` precision (`timeprecision`과의 상호작용) | 다른 timeunit 모듈과 boundary 테스트 | timing rounding drift |
| Cross-language: VAMS `wreal` ↔ SV `nettype` 자동 변환 | mixed instance elaborate | implicit conversion missing |

> 가능하면 **같은 RNM 코드가 두 vendor 이상에서 elaborate 되는 것**을 **CI**(Continuous Integration, 코드 변경 시마다 자동으로 빌드·테스트하는 체계)로 강제하세요. 한 vendor에 묶이면(**vendor lock-in**) model bug workaround가 vendor-specific으로 누적되고, vendor 교체 시 대대적 rewrite가 필요해집니다.

## 13. License 경계와 비용 영향

대량 회귀의 핵심 변수는 **AMS feature가 활성화되는지 여부**입니다. 같은 testbench라도 다음 두 경우 license cost가 10배 차이날 수 있습니다.

| 환경 | License | 회귀 규모 |
|---|---|---|
| Pure SV-RNM | 일반 SV simulator (VCS / Xcelium / Questa) | nightly로 수천 seed |
| AMS feature 의존 | AMS license 추가 (보통 별도 라인) | seed 수 제한 |

> RNM 모델이 **의도치 않게 AMS 기능에 의존**하면 (예: `real_net` implicit conversion) 일반 SV license로는 elaborate 안 됩니다. 처음부터 **pure SV로 elaborate 되는지**를 CI로 강제해야 license cost가 통제됩니다.

## 14. 팀 성향별 실무 선택 가이드

조직의 기존 흐름을 따라가는 것이 가장 안전합니다.

### Analog 팀이 Cadence 위주

→ Xcelium AMS로 통일. Virtuoso · Spectre 흐름과 모델 swap이 편하고, connect module 자동 삽입(CMI — Connect Module Insertion)이 강합니다. UVM도 Xcelium에서 잘 돕니다.

### Digital 팀이 Synopsys 위주

→ VCS-AMS + CustomSim 조합. UVM regression 친화적이고, VC formal · VC LP 등 동일 vendor 도구와 통합이 쉽습니다. DRAM full-chip RNM에 가장 자주 보입니다.

### Foundry corner / 군용·항공우주

→ Siemens EDA Questa AMS + Eldo. corner 라이브러리가 강하고 보안 인증(예: DO-254 — 항공 전자 하드웨어 인증 표준)에 활용 사례가 많습니다.

## 15. Verilator 등 오픈소스 도구 현황

**Verilator**는 SV synthesizable subset 중심이라 mixed-signal에는 한계가 큽니다 (`real` 일부 지원, `nettype`은 제한적). 오픈소스로 mixed-signal 본격 회귀는 아직 어렵고, **학습 · prototype 용도**입니다. 상용 tape-out 흐름은 위 3개 vendor 중 하나가 사실상 표준.

## 16. 흔한 오해

| 오해 | 사실 |
|---|---|
| "AMS = mixed-signal sign-off 필수" | RNM only로 시작, AMS는 corner만 |
| "SPICE 도구 없으면 mixed-signal 불가" | RNM만으로 80% 이상 검증 가능 |
| "IBIS-AMI는 PCB 엔지니어용" | DDR5/PCIe Gen5+ DV의 필수 도구 |
| "도구 종속성 때문에 mixed-signal 어렵다" | `nettype`은 표준 — vendor 독립 |
| "Fast SPICE는 부정확" | Partition + adaptive step — 일반 SPICE와 거의 동일 정확도 |

## 핵심 정리

1. 4대 카테고리: SPICE / Fast SPICE / AMS / Pure RNM / IBIS-AMI
2. Pure RNM은 **vendor 독립** — digital sim만으로 가능
3. AMS는 **digital + SPICE 결합** — connectrule이 핵심
4. DDR5/PCIe Gen5+ system 검증은 **IBIS-AMI** 표준
5. 도구 선택은 **블록 크기 × 정확도 × 비용** 함수
6. 호환성 체크리스트를 elaborate 시점에 통과시키는 것을 CI에 강제
7. 팀 성향(Cadence/Synopsys/Siemens)에 맞춰 통일 — 혼합 흐름은 디버그 비용 큼

## 더 읽을거리

- Synopsys VCS AMS datasheet (공식)
- Cadence AMS Designer overview
- IBIS Open Forum: https://ibis.org
- 퀴즈: [Ch11 퀴즈](../quiz/ch11_quiz/)
