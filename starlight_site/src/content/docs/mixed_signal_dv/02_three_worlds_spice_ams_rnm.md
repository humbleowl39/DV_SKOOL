---
title: "Ch02. 세 가지 시뮬레이션 세계 — Digital · SPICE · RNM"
---

## 학습 목표

- **(Remember)** Digital · SPICE · RNM의 신호 표현·시간 처리·속도·정확도 차이를 표로 재구성할 수 있다
- **(Understand)** AMS와 RNM 두 통합 방식의 차이를 설명할 수 있다
- **(Apply)** 주어진 회로/검증 task에 대해 세 패러다임 중 적합한 것을 선택할 수 있다
- **(Analyze)** 한 칩 내부에서 세 패러다임이 어떻게 공존하는지 분해할 수 있다

## 1. 한 장의 비교표

세 가지 시뮬레이션 세계를 처음 접할 때 가장 중요한 질문은 "이것들이 어떻게 다른가"입니다. 세 세계란 **Digital sim**(신호를 0/1로만 다루는 빠른 디지털 시뮬레이션), **SPICE**(트랜지스터 물리를 정밀하게 풀어 실제 전압 파형을 내는 아날로그 시뮬레이션), **RNM**(Real Number Modeling — 디지털 시뮬레이터 안에서 아날로그 동작을 실수 함수로 근사하는 기법)입니다. 신호 표현 방식이 다르고, 시간을 다루는 방법이 다르며, 그 차이가 속도와 정확도의 근본적인 차이로 이어집니다.

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

RNM이 단순히 SPICE와 디지털 sim의 중간이 아니라, 산업 표준 위치를 차지하게 된 데에는 두 가지 결정적 이유가 있습니다. 첫째, **별도의 SPICE 엔진 없이 일반 디지털 시뮬레이터만으로 동작**합니다. 둘째, IEEE 1800-2012(SystemVerilog 표준) 표준에 정의된 `nettype`(net 값의 타입과 다중 드라이버 합성 방식을 사용자가 정의하는 SV 기능) 기능이 기반이므로 **특정 벤더에 종속되지 않습니다**. 이 두 가지가 맞물려 라이센스 비용 없이 **nightly 회귀**(매일 밤 자동으로 대량의 테스트를 재실행하는 것)를 수천 **시드**(seed — 난수 생성의 시작값; 시드를 바꾸면 다른 무작위 자극이 나옴)로 돌릴 수 있는 현실을 만듭니다.

## 2. 세 세계의 그림 — 한 칩 안에서 어떻게 공존하나

```d2
direction: down

dram_sim: "DRAM 칩 시뮬레이션" {
  digital: "Digital region\n(Command decoder, MR, Refresh ctr...)\n· logic 0/1, event-driven"
  rnm: "RNM region\n(WL driver, BL, Sense amp, IO buffer...)\n· real values, event-driven\n· charge sharing, Pelgrom offset, slew rate"
  spice: "SPICE region (선택)\n(sense amp offset MC corner, VCO)\n· BSIM physics, Newton-Raphson"

  digital -> rnm: "digital command"
  rnm -> spice: "voltage trajectory"
}
```

위 그림의 용어: **WL driver**(word line driver — 메모리 행을 활성화하는 구동 회로), **BL**(bit line — 셀 데이터를 실어 나르는 배선), **MR**(mode register — 칩 동작 모드를 담는 레지스터), **MC corner**(Monte Carlo corner — 제조 편차를 무작위로 변동시켜 최악 경우를 보는 통계적 시뮬레이션 조건)입니다. 대부분의 DRAM 검증은 **위 두 layer**(Digital + RNM)만으로 진행됩니다. SPICE는 **sign-off**(설계가 양산 기준을 모두 통과했다고 최종 확정하는 단계)의 corner check(최악 조건 점검)에 씁니다.

## 3. 두 가지 통합 방식 — AMS vs RNM

### 3.1 AMS (Analog Mixed-Signal Simulation)

AMS(Analog Mixed-Signal Simulation)는 디지털 시뮬레이터와 SPICE 시뮬레이터를 동시에 실행하면서 두 도메인을 **connect module**(두 영역의 경계에서 0/1 논리와 실제 전압을 서로 변환하는 어댑터)로 연결하는 방식입니다. 디지털 측은 VCS 같은 이벤트 기반 엔진이, 아날로그 측은 FineSim이나 HSPICE 같은 SPICE 엔진이 각자 자신의 영역을 계산하고, 경계에서는 **D2A·A2D**(Digital-to-Analog / Analog-to-Digital 변환 모듈) connect module이 0/1 논리 신호를 실수 전압으로, 또는 그 반대로 변환합니다.

```d2
direction: down

ams_env: "AMS Simulation Environment" {
  digital_sim: "Digital Simulator\n(e.g., VCS)"
  analog_sim: "Analog Simulator\n(e.g., FineSim / HSPICE)"
  connect_mods: "Connect modules\n(D2A, A2D, A2A)"

  digital_sim <-> analog_sim: "Sync"
  digital_sim -> connect_mods
  analog_sim -> connect_mods
}
```

AMS의 강점은 SPICE 수준의 정확도를 유지하면서 디지털 testbench와 함께 동작한다는 점입니다. 단점은 SPICE 부분이 여전히 병목이라는 것입니다. 아날로그 블록이 크면 클수록 시뮬레이션 속도가 SPICE에 가까워집니다.

### 3.2 RNM (Real Number Modeling)

RNM은 SPICE 엔진을 아예 사용하지 않습니다. 아날로그 동작을 SystemVerilog의 `real` 타입과 `nettype` 기능으로 근사해서, **디지털 시뮬레이터 하나**만으로 모든 것을 처리합니다.

```d2
direction: down

rnm_env: "RNM Simulation Environment" {
  digital_sim: "Digital Simulator\n(VCS / Xcelium / Questa)\n· logic types (0/1/X/Z)\n· real types (voltage, current, impedance)\n· nettype-defined nets (wreal, EEnet, UDN...)\n· all event-driven"
}
```

모든 신호가 이벤트 기반으로 처리되므로 SPICE의 수치 적분 오버헤드가 없습니다. 결과적으로 SPICE 대비 1000배 이상 빠른 경우도 있습니다. 정확도는 모델 품질에 달려 있는데, 잘 작성된 RNM 모델은 DRAM sense amp의 동작이나 DLL의 lock 거동을 SPICE 결과와 높은 일치도로 재현할 수 있습니다.

**왜 event-driven 이 "빠르면서 정확" 한가 — 두 엔진의 일하는 단위가 다르다.** SPICE 는 _연속 시간_ 을 작은 timestep(시간을 잘게 나눈 한 계산 단위) 으로 잘라, _매 timestep 마다_ 전체 회로의 비선형 연립방정식을 Newton-Raphson(반복으로 방정식 해를 찾아가는 기법) 으로 반복하며 그 안에서 Jacobian 행렬(연립방정식의 미분 계수들을 모은 행렬) 을 분해해 푼다 ([Module 03](../03_spice_fundamentals/)) — 신호가 변하지 않아도 시간이 흐르면 계속 계산한다. 반면 RNM 은 _값이 바뀌는 사건(event)_ 이 있을 때만 동작한다: 어떤 net 의 real 값이 변하면 그 net 에 민감한 process 만 깨어나 _함수를 한 번 평가_ 해 새 값을 내고, 변화가 없으면 아무 연산도 하지 않는다. 즉 SPICE 의 비용은 "timestep 수 × (행렬 해 + Newton 반복)" 인데, RNM 의 비용은 "발생한 event 수 × (함수 1회 평가)" 다 — 행렬 분해도, timestep 마다의 반복도 없다. 안정 구간에서는 event 가 드물어 계산이 거의 0 에 가깝고, 그래서 1000배 이상의 속도가 나온다. 정확도를 잃지 않는 이유는 _전압이라는 실수 값 자체는 그대로 표현_ 하되(digital sim 처럼 0/1 로 뭉개지 않음), 그 값을 _얻는 방법_ 만 "행렬 풀이" 대신 "값 변화 시 함수 평가" 로 바꿨기 때문이다.

### 3.3 결정 트리

```d2
direction: down

start: "검증 task 시작"
q1: "회로가 트랜지스터 물리에\n강하게 의존?" {shape: diamond}
spice_ams: "SPICE / AMS\n(Sense amp offset, VCO,\ncharge pump, Bandgap)"
q2: "회로 크기가\n1만 트랜지스터 이상?" {shape: diamond}
rnm_fast: "RNM 또는 Fast SPICE"
q3: "Voltage·timing이\n중요한가?" {shape: diamond}
rnm: "RNM"
digital: "Pure digital sim"

start -> q1
q1 -> spice_ams: "Yes"
q1 -> q2: "No"
q2 -> rnm_fast: "Yes"
q2 -> q3: "No"
q3 -> rnm: "Yes"
q3 -> digital: "No"
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

위 표의 용어: **ramp transition**(신호가 한 값에서 다른 값으로 비스듬히 올라가/내려가는 천이), **hysteresis**(히스테리시스 — 올라갈 때와 내려갈 때 임계값이 다른 성질, 잡음에 둔감해짐), **saturation**(포화 — 출력이 한계에 다다라 더 이상 커지지 않는 상태), **charge conservation**(전하 보존 — 커패시터의 전하량 보존 법칙을 모델에 반영). DRAM에서 보통 Level 2~3을 씁니다.

## 5. 표준 / 언어 지형

| 표준 | 발행 | 핵심 기능 |
|------|------|-----------|
| **SPICE** (de-facto) | UCB 1970s ~ | netlist + 분석 (.tran/.ac/.dc) |
| **Verilog-AMS** | IEEE 1364.1 / VAMS-2023 (Accellera, 2024-02) | electrical, `analog begin`, `<+`, connect module |
| **VHDL-AMS** | IEEE 1076.1 | VHDL의 mixed-signal 확장 |
| **SystemVerilog-AMS** | Accellera draft | SV의 mixed-signal 확장 (널리 안 쓰임) |
| **`nettype` (SV 2012)** | IEEE 1800-2012 § 6.6.7 | **RNM의 핵심 표준 기능** |
| **IBIS-AMI** | IBIS 7.x | SerDes RX/TX behavioral model |

위 표의 용어: **Verilog-AMS**(디지털 Verilog에 아날로그 기술을 더한 표준 언어), **electrical**(전압·전류를 갖는 아날로그 노드를 선언하는 discipline 키워드), **`analog begin`**(아날로그 동작 블록을 여는 구문), **`<+`**(아날로그 기여 연산자 — 노드에 전류/전압 방정식을 더하는 기호), **IBIS-AMI**(SerDes 송수신단의 동작을 표준 형식으로 기술한 behavioral model)입니다.

> Verilog-AMS는 2014년의 v2.4 이후 사실상 SystemVerilog와 합쳐지는 흐름. 2023년 VAMS-2023이 Accellera 마지막 메이저 갱신.

## 5.1 ⚠️ "AMS"라는 단어의 두 가지 의미 (혼동 주의)

업계 문서·발표·툴 이름에서 "AMS"는 **두 가지 다른 의미**로 쓰입니다. 이 책은 (1)을 표준으로 쓰지만, 외부 자료를 읽을 때는 (2)도 인식해야 false-pass risk를 줄일 수 있습니다.

| 용법 | 의미 | 포함 범위 |
|---|---|---|
| **(1) 좁은 의미 — 이 책의 정의** | **Verilog-AMS / VHDL-AMS 언어** (`electrical` discipline, KCL/KVL solver, connect module) | SPICE를 sim에 결합하는 mixed-signal **표준 언어** |
| **(2) 넓은 의미 — 우산 용어** | "Analog Mixed-Signal" 일반 — 디지털 sim에 아날로그를 섞는 **모든 방법론** | (1) + RNM(`nettype`/`wreal`) + IBIS-AMI + DMS 등 모두 포함 |

### 실무에서 마주치는 사례

- **Accellera "UVM-AMS" working group** → (2)번 의미. RNM 기반 UVM 통합 패턴도 이 이름 아래 발표됨 (이 책 Ch12 "UVM × RNM Integration"이 산업 문헌에선 종종 "UVM-AMS"로 불림).
- **EDA 제품명 "VCS-AMS", "AMS Designer", "Questa-AMS"** → 제품 안에 **(1) Verilog-AMS 엔진 + RNM 지원**이 모두 들어 있어 이름 자체가 우산 용어. Ch11 §4 도구 비교 참조.
- **DVCon paper 제목에 "AMS"** → 본문을 읽어야 (1) 언어인지 (2) 우산인지 판별됨.

### 이 책의 규약

- 본문에서 "**AMS**"는 별다른 단서가 없는 한 (1) Verilog-AMS 언어를 지칭합니다.
- RNM 기반 mixed-signal 검증을 가리킬 때는 "**RNM**" 또는 "**DMS**" (Digital Mixed-Signal — Ch10 §1 정의) 로 명시합니다.
- 외부 자료를 읽을 때 "AMS"라는 단어가 보이면, **그게 (1) 언어인지 (2) 우산인지 한 번 더 확인**하는 습관을 들여야 합니다.

> Verilog-AMS LRM(VAMS-2023) 자체에는 RNM 개념이 포함되어 있지 않으나, IEEE 1800-2017과 함께 쓰일 때는 `nettype real`이 같은 sim에 호스팅되어 "AMS + RNM"이 한 elaboration 안에 공존할 수 있습니다 — 이 공존이 (2)번 우산 용어가 산업에서 굳어진 배경입니다.

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

VAMS(Verilog-AMS) 시절엔 **`wreal`**(wire-real — 값으로 실수 하나를 갖는 Verilog-AMS의 net 타입) 한 종류만 있었습니다. SV-2012부터 `nettype`이 들어와 더 유연해졌고, **legacy IP**(예전에 만들어져 그대로 재사용되는 설계 블록)가 wreal을 쓸 수 있으니 두 개념을 모두 알아둬야 합니다.

| 측면 | `wreal` (Verilog-AMS) | `nettype` (SV-2012) |
|---|---|---|
| 표현력 | net 값이 real 1개 | struct payload 가능 (V·I·Z 동시) — net 하나가 전압·전류·임피던스 묶음을 운반 |
| Multi-driver | `wreal_resolution` directive로 wired-OR / sum / average 중 택1 | 사용자 정의 resolution function (KCL/KVL 자유롭게) |
| Simulator | VAMS sim 필요한 경우 多 | 일반 SV simulator로 충분 |
| 사용처 | legacy IP | 신규 RNM 코드 표준 |

> 신규 mixed-signal IP는 `nettype` 기반으로 작성하고, legacy wreal IP는 wrapper로 감싸 boundary에서만 변환하는 것이 실무 패턴입니다.

## 8. Partitioning은 검증 가설과 함께 정의해야

실제 SoC tape-out 흐름은 **한 레벨로 통일하지 않고** 섞어 씁니다 — Block-level은 Spice signoff + RNM behavioral acceptance, Subsystem은 RNM이 주력 + 일부 Spice cosim spot check.

파티션을 결정할 때 중요한 것은 "어느 블록을 어떤 도구로"만이 아닙니다. 그 블록에서 **무엇을 보고 무엇을 보지 않는지**를 명시해야 false-pass 위험이 추적됩니다. "PLL을 RNM으로 갈음"이라고만 적으면 안 됩니다. "PLL lock time과 divider 정합성은 RNM으로 검증하고, phase noise는 이 검증 범위에서 제외한다"까지 적어야 silicon bring-up에서 모델 gap의 책임 소재가 명확해집니다. 이 한 줄 차이가 실제 불량 분석 시 수 주의 시간을 절약합니다.

## 9. RNM이 DRAM 산업에서 표준이 된 4가지 이유

왜 DRAM 산업은 RNM을 선택했을까요? 네 가지 이유가 맞물려 있습니다. 첫째, 1Gb 칩의 셀 수가 10⁹개에 달해 SPICE로는 불가능합니다. 둘째, sense amp 동작은 전압을 표현해야 하는데 SPICE는 너무 느리고 digital sim은 전압을 모릅니다 — RNM이 전압을 표현하면서 빠른 유일한 해법입니다. 셋째, `nettype`은 IEEE 1800 표준에 포함된 기능이라 별도 라이선스나 도구 없이 일반 디지털 시뮬레이터만으로 구현됩니다. 넷째, stimulus, coverage, assertion에 UVM과 SV를 그대로 활용할 수 있어 기존 디지털 DV 팀이 환경을 갑자기 뒤집지 않아도 됩니다.

## 10. 대표 문제 — 한 SerDes 검증 task 분해

### 문제

100 Gbps **PAM4**(Pulse Amplitude Modulation 4-level — 한 심볼에 4개 전압 레벨로 2비트를 싣는 변조) SerDes를 검증한다고 가정. (용어: **eye opening**은 신호 파형을 겹쳐 그렸을 때 가운데 벌어지는 깨끗한 영역, **CTLE/DFE**는 수신단 파형 보정 회로, **ISI**는 인접 비트 간 간섭, **CDR**은 데이터에서 클럭을 복원하는 회로입니다.) 다음 7개 시나리오를 어떤 패러다임으로 검증할지 선택하고 이유를 쓰시오.

1. Protocol layer의 **FEC**(Forward Error Correction, 수신 측 오류 정정) encoding/decoding 정확성
2. **PMA**(Physical Medium Attachment — 물리 매체에 직접 붙는 아날로그 송수신 계층)의 PLL이 100 GHz target에서 lock 하는가?
3. TX driver의 eye opening
4. RX equalizer (CTLE + DFE)가 ISI를 잘 보상하는가?
5. CDR이 frequency offset ±200 **ppm**(parts per million — 100만분의 1 단위의 주파수 오차)에서 lock 유지하는가?
6. 한 비트 데이터의 **BER**(Bit Error Rate, 비트 오류율 — 전송 비트 중 잘못 수신된 비율) (1e-12)
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
- BER 1e-12는 일반 sim으론 도달 불가 → **statistical method**(통계적 기법 — 소수 샘플로 분포를 추정해 극히 드문 오류 확률을 외삽; statistical eye는 이렇게 합성한 아이 다이어그램) + behavioral model
- 표준화된 vendor model(IBIS-AMI)이 있으면 그대로 활용 — 직접 모델링 안 함

## 핵심 정리

1. 세 패러다임: **Digital(빠름·logic만) / SPICE(정확·느림) / RNM(빠름·real)**
2. 통합 방식 두 종류: **AMS(두 sim 결합) / RNM(digital sim 안에서 real)**
3. DRAM 산업은 **RNM 표준** — 셀 수·도구 호환성·UVM 공존이 이유
4. 정밀도는 5단계 가능 — DRAM에서 Level 2~3 일반
5. SerDes처럼 표준 모델(IBIS-AMI)이 있는 영역은 그것을 그대로 활용

## 더 읽을거리

- 다음: [Ch03. SPICE / Fast SPICE 기초](../03_spice_fundamentals/)
- Bhattacharya, *"Real Number Modeling for Mixed-Signal Verification"* — DVCon paper
- VAMS-2023 LRM (Accellera, 2024-02)
- 퀴즈: [Ch02 퀴즈](../quiz/ch02_quiz/)
