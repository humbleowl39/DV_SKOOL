# Ch11. 도구 지형 — VCS-AMS · AMS Designer · Questa-AMS · IBIS-AMI

## 학습 목표

- **(Remember)** Synopsys / Cadence / Siemens EDA 3대 벤더의 mixed-signal 시뮬레이션 도구를 진술할 수 있다
- **(Understand)** 각 도구의 강점·약점·라이센스 모델을 설명할 수 있다
- **(Apply)** 주어진 검증 task에 적합한 도구 조합을 추천할 수 있다
- **(Evaluate)** RNM-only vs AMS vs IBIS-AMI 도구의 적합성을 결정할 수 있다

## 1. 도구 카테고리 정리

| 카테고리 | 대표 도구 | 특징 |
|---|---|---|
| SPICE | HSPICE, Spectre, Eldo, FineSim | 정확도 표준, 느림 |
| Fast SPICE | CustomSim, FineSim Pro, UltraSim | DRAM full-chip 가능 |
| AMS | VCS AMS, AMS Designer, Questa AMS | digital + SPICE 결합 |
| Pure RNM | VCS, Xcelium, Questa | digital simulator만으로 RNM |
| IBIS-AMI | MATLAB SerDes, ADS, HyperLynx | SerDes/DDR system 검증 |

## 2. SPICE 도구

| 도구 | 벤더 | 특징 |
|------|------|------|
| **HSPICE** | Synopsys | "Gold reference" — silicon 가장 가까움. Sign-off 표준 |
| **Spectre** | Cadence | 아날로그 설계 흐름에서 흔함 (Virtuoso 통합) |
| **FineSim** | Synopsys | 빠른 SPICE. AMS 통합 잘 됨 |
| **Eldo** | Siemens EDA | 군용/항공우주에서 자주 (보안 인증) |

라이센스: 모두 enterprise license, node-locked + floating 혼합.

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

- Native low-power(NLP) 기술 확장 — UPF mixed-signal 지원
- SystemVerilog · Verilog · VHDL · Verilog-AMS · SPICE **모두 한 환경에서**
- Post-layout: SPF · DSPF · SPEF 형식 지원
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

```
검증 task 시작
    │
    ▼
SerDes / DDR5 channel · eye sign-off?
    ├─ Yes → IBIS-AMI 도구 (MATLAB SerDes, ADS, HyperLynx)
    └─ No
        │
        ▼
    Block 크기 (transistor 수)
    ├─ < 1k → SPICE (HSPICE, Spectre)
    ├─ 1k~10k → Fast SPICE
    ├─ 10k~1M → AMS (VCS AMS / AMS Designer / Questa AMS)
    └─ > 1M → RNM (VCS / Xcelium / Questa) + critical block AMS
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
2. PMIC buck regulator step-load response analysis
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

## 12. 흔한 오해

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

## 더 읽을거리

- Synopsys VCS AMS datasheet (공식)
- Cadence AMS Designer overview
- IBIS Open Forum: https://ibis.org
- 퀴즈: [Ch11 퀴즈](quiz/ch11_quiz.md)
