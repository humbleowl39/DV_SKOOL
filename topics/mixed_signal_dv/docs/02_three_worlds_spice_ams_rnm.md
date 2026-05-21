# Ch02. 세 가지 시뮬레이션 세계 — Digital · SPICE · RNM

## 학습 목표

- **(Remember)** Digital · SPICE · RNM의 신호 표현·시간 처리·속도·정확도 차이를 표로 재구성할 수 있다
- **(Understand)** AMS와 RNM 두 통합 방식의 차이를 설명할 수 있다
- **(Apply)** 주어진 회로/검증 task에 대해 세 패러다임 중 적합한 것을 선택할 수 있다
- **(Analyze)** 한 칩 내부에서 세 패러다임이 어떻게 공존하는지 분해할 수 있다

## 1. 한 장의 비교표

| 항목 | Digital sim | SPICE | RNM (Real Number Modeling) |
|------|------------|-------|---------------------------|
| 신호 표현 | logic (0/1/X/Z) | 실수 전압/전류 | **실수값 (`real`)** |
| 시간 처리 | 이벤트 기반 | 연속 시간 (수치적분) | **이벤트 기반** |
| 물리 모델 | 없음 | 트랜지스터 BSIM | **사용자 정의 함수** |
| 속도 | 매우 빠름 (참조: 1×) | 매우 느림 (1/10,000×) | **빠름 (1/2 ~ 1/10×)** |
| 정확도 | 디지털 동작만 | 매우 높음 (전기적) | **모델 정확도에 따라 다름** |
| 적용 영역 | RTL | Critical analog (sense amp, PLL VCO) | **Analog behavior 모사** |
| 언어 | Verilog / SV / VHDL | SPICE netlist | **SystemVerilog `real`, `nettype`** |
| 메모리 사용 | 작음 | 큼 (노드 수 비례) | 작음 |
| 도구 종속성 | 낮음 | SPICE engine 필요 | **낮음 (SV 표준 기능)** |

> RNM이 산업 표준이 된 핵심 이유: **digital simulator만으로 동작** + **SV 표준 기능이라 vendor lock-in 없음**.

## 2. 세 세계의 그림 — 한 칩 안에서 어떻게 공존하나

```
┌────────────────────────────────────────────────────────────────┐
│                       DRAM 칩 시뮬레이션                          │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Digital region (Command decoder, MR, Refresh ctr...)      │  │
│  │  - logic 0/1, event-driven                                 │  │
│  └──────────────────────────┬───────────────────────────────┘  │
│                              │ digital                            │
│                              ▼ command                            │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ RNM region (WL driver, BL, Sense amp, IO buffer...)       │  │
│  │  - real values, event-driven                               │  │
│  │  - charge sharing, Pelgrom offset, slew rate              │  │
│  └──────────────────────────┬───────────────────────────────┘  │
│                              │ voltage trajectory               │
│                              ▼                                    │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ SPICE region (선택 — sense amp offset MC corner, VCO)     │  │
│  │  - BSIM physics, Newton-Raphson                            │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                   │
└────────────────────────────────────────────────────────────────┘
```

대부분의 DRAM 검증은 **위 두 layer**(Digital + RNM)만으로 진행됩니다. SPICE는 sign-off 단계의 corner check.

## 3. 두 가지 통합 방식 — AMS vs RNM

### 3.1 AMS (Analog Mixed-Signal Simulation)

```
┌──────────────────────────────────────────────────────────────┐
│                  AMS Simulation Environment                   │
│                                                                │
│  ┌──────────────────────┐         ┌──────────────────────┐   │
│  │ Digital Simulator    │  Sync   │ Analog Simulator     │   │
│  │ (e.g., VCS)          │ ←─────→ │ (e.g., FineSim/HSPICE)│   │
│  └──────────────────────┘         └──────────────────────┘   │
│              ↑                                ↑                │
│              │     ┌─────────────────────┐    │                │
│              └─────┤   Connect modules   ├────┘                │
│                    │  (D2A, A2D, A2A)    │                     │
│                    └─────────────────────┘                     │
└──────────────────────────────────────────────────────────────┘
```

- 두 시뮬레이터(digital + SPICE)를 결합
- 경계에 connect module로 변환
- **정확하지만 SPICE 부분이 병목** → 느림

### 3.2 RNM (Real Number Modeling)

```
┌──────────────────────────────────────────────────────────────┐
│              RNM Simulation Environment                       │
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐│
│  │ Digital Simulator (VCS / Xcelium / Questa)               ││
│  │                                                            ││
│  │  - logic types (0/1/X/Z)                                  ││
│  │  - real types (voltage, current, impedance)               ││
│  │  - nettype-defined nets (wreal, EEnet, UDN...)            ││
│  │  - all event-driven                                        ││
│  └──────────────────────────────────────────────────────────┘│
└──────────────────────────────────────────────────────────────┘
```

- **하나의 simulator(digital)만 사용**
- analog 동작을 SV의 `real`/`nettype`으로 표현
- **빠르지만 모델 정확도에 의존**

### 3.3 결정 트리

```
검증 task 시작
    │
    ▼
회로가 트랜지스터 물리에 강하게 의존?
   ├─ Yes → Sense amp offset, VCO, charge pump, Bandgap → SPICE/AMS
   └─ No
       │
       ▼
   회로 크기가 1만 트랜지스터 이상?
      ├─ Yes → RNM 또는 Fast SPICE
      └─ No
          │
          ▼
       Voltage·timing이 중요한가?
          ├─ Yes → RNM
          └─ No → Pure digital sim
```

## 4. 정확도 vs 속도 스펙트럼

같은 inverter라도 RNM 모델의 정밀도를 5단계까지 조절 가능합니다 — Ch05에서 자세히:

| RNM 단계 | 모델링 수준 | 속도 |
|---------|------------|-----|
| Level 0 | 디지털 + delay만 (사실상 RNM 아님) | 매우 빠름 |
| Level 1 | 실수값 출력 (high/low voltage) | 빠름 |
| Level 2 | + Ramp transition (rise/fall time) | 빠름 |
| Level 3 | + Threshold, hysteresis, saturation | 중간 |
| Level 4 | + Noise injection, jitter | 약간 느림 |
| Level 5 | + Charge conservation (capacitance modeling) | 느림 |

DRAM에서 보통 Level 2~3을 씁니다.

## 5. 표준 / 언어 지형

| 표준 | 발행 | 핵심 기능 |
|------|------|-----------|
| **SPICE** (de-facto) | UCB 1970s ~ | netlist + 분석 (.tran/.ac/.dc) |
| **Verilog-AMS** | IEEE 1364.1 / VAMS-2023 (Accellera, 2024-02) | electrical, `analog begin`, `<+`, connect module |
| **VHDL-AMS** | IEEE 1076.1 | VHDL의 mixed-signal 확장 |
| **SystemVerilog-AMS** | Accellera draft | SV의 mixed-signal 확장 (널리 안 쓰임) |
| **`nettype` (SV 2012)** | IEEE 1800-2012 § 6.6.7 | **RNM의 핵심 표준 기능** |
| **IBIS-AMI** | IBIS 7.x | SerDes RX/TX behavioral model |

> Verilog-AMS는 2014년의 v2.4 이후 사실상 SystemVerilog와 합쳐지는 흐름. 2023년 VAMS-2023이 Accellera 마지막 메이저 갱신.

## 6. 속도 감각 잡기 — 상대 속도 비율

절대 수치는 모델 복잡도와 회로 크기에 따라 크게 다르지만, **같은 testbench에서 추상화만 바꿀 때의 상대 비율**은 보통 다음 범위에 들어옵니다. 업체 자료·conference paper에서 흔히 인용되는 수치이며, 자기 환경에서는 실측이 우선입니다.

| 시나리오 | Spice 대비 속도 | 비고 |
|---|---|---|
| Spice (Spectre/HSPICE) | 1× | baseline, full-chip 회귀 비현실적 |
| FastSPICE (FineSim, APS, AFS) | 10~30× | 큰 회로의 전체 transient에 유리 |
| VAMS (electrical + wreal) | 50~500× | connect module이 많을수록 느려짐 |
| SV-RNM | 1000~10000× | digital 회귀와 거의 동급 |
| Pure digital stub | 10000×~ | analog 동작은 못 봄 |

→ RNM은 digital 회귀와 거의 같은 속도라 **nightly seed 수천 개**가 현실적. 이게 SPICE가 줄 수 없는 결정적 강점.

## 7. WREAL vs nettype — 두 real-도메인 net

VAMS 시절엔 `wreal` 한 종류만 있었습니다. SV-2012부터 `nettype`이 들어와 더 유연해졌고, legacy IP가 wreal을 쓸 수 있으니 두 개념을 모두 알아둬야 합니다.

| 측면 | `wreal` (Verilog-AMS) | `nettype` (SV-2012) |
|---|---|---|
| 표현력 | net 값이 real 1개 | struct payload 가능 (V·I·Z 동시) |
| Multi-driver | `wreal_resolution` directive로 wired-OR / sum / average 중 택1 | 사용자 정의 resolution function (KCL/KVL 자유롭게) |
| Simulator | VAMS sim 필요한 경우 多 | 일반 SV simulator로 충분 |
| 사용처 | legacy IP | 신규 RNM 코드 표준 |

> 신규 mixed-signal IP는 `nettype` 기반으로 작성하고, legacy wreal IP는 wrapper로 감싸 boundary에서만 변환하는 것이 실무 패턴입니다.

## 8. Partitioning은 검증 가설과 함께 정의해야

실제 SoC tape-out 흐름은 **한 레벨로 통일하지 않고** 섞어 씁니다 — Block-level은 Spice signoff + RNM behavioral acceptance, Subsystem은 RNM이 주력 + 일부 Spice cosim spot check.

> Partition을 적을 때 "PLL을 RNM으로 갈음"이라고만 적으면 안 됩니다. **"PLL lock time, divider 정합성은 RNM으로 보고 phase noise는 보지 않는다"**까지 명시해야 false-pass risk가 추적됩니다. 이 한 줄이 silicon bring-up에서 모델 gap의 책임을 명확히 합니다.

## 9. RNM이 DRAM 산업에서 표준이 된 4가지 이유

1. **DRAM 셀 수가 너무 많다** — 1Gb 칩이면 10⁹ cell. SPICE 불가.
2. **Sense amp 동작은 정확도 필요** — 그런데 SPICE는 느림. RNM이 voltage 표현하면서 빠른 유일 해법.
3. **표준 SV 기능** — `nettype`만 있으면 됨. 별도 라이선스/도구 불필요.
4. **UVM과 공존** — stimulus·coverage·assertion에 UVM/SV를 그대로 활용 가능.

## 10. 대표 문제 — 한 SerDes 검증 task 분해

### 문제

100 Gbps PAM4 SerDes를 검증한다고 가정. 다음 7개 시나리오를 어떤 패러다임으로 검증할지 선택하고 이유를 쓰시오.

1. Protocol layer의 FEC encoding/decoding 정확성
2. PMA의 PLL이 100 GHz target에서 lock 하는가?
3. TX driver의 eye opening
4. RX equalizer (CTLE + DFE)가 ISI를 잘 보상하는가?
5. CDR이 frequency offset ±200 ppm에서 lock 유지하는가?
6. 한 비트 데이터의 BER (1e-12)
7. 전체 protocol layer의 link establishment FSM

### 풀이

| # | 시나리오 | 패러다임 | 이유 |
|---|---------|--------|------|
| 1 | FEC 정확성 | Digital | 순수 알고리즘. UVM이 적합 |
| 2 | PLL lock | RNM (+SPICE corner) | Lock behavior는 RNM, phase noise는 SPICE |
| 3 | TX eye opening | RNM + IBIS-AMI | RNM driver model + 실측 IBIS-AMI |
| 4 | RX equalizer | **IBIS-AMI** | 표준 — vendor 모델 그대로 사용 |
| 5 | CDR | RNM | Loop dynamics는 RNM이면 충분 |
| 6 | BER 1e-12 | **Statistical eye + IBIS-AMI** | RNM 단일 sim으론 1e-12 sample 부족 |
| 7 | Link FSM | Digital | 순수 protocol FSM |

### 통찰

- 같은 SerDes 안에서 **digital · RNM · IBIS-AMI**가 모두 등장
- BER 1e-12는 일반 sim으론 도달 불가 → **statistical method** + behavioral model
- 표준화된 vendor model(IBIS-AMI)이 있으면 그대로 활용 — 직접 모델링 안 함

## 핵심 정리

1. 세 패러다임: **Digital(빠름·logic만) / SPICE(정확·느림) / RNM(빠름·real)**
2. 통합 방식 두 종류: **AMS(두 sim 결합) / RNM(digital sim 안에서 real)**
3. DRAM 산업은 **RNM 표준** — 셀 수·도구 호환성·UVM 공존이 이유
4. 정밀도는 5단계 가능 — DRAM에서 Level 2~3 일반
5. SerDes처럼 표준 모델(IBIS-AMI)이 있는 영역은 그것을 그대로 활용

## 더 읽을거리

- 다음: [Ch03. SPICE / Fast SPICE 기초](03_spice_fundamentals.md)
- Bhattacharya, *"Real Number Modeling for Mixed-Signal Verification"* — DVCon paper
- VAMS-2023 LRM (Accellera, 2024-02)
- 퀴즈: [Ch02 퀴즈](quiz/ch02_quiz.md)
