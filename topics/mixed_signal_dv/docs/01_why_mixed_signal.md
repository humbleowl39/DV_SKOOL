# Ch01. 왜 Mixed-Signal Simulation인가

## 학습 목표

- **(Remember)** Mixed-signal 칩의 5가지 대표 예와 디지털/아날로그 영역을 나열할 수 있다
- **(Understand)** 순수 digital sim과 순수 SPICE의 한계를 설명할 수 있다
- **(Analyze)** 한 칩의 어느 부분이 mixed-signal 검증이 필요한지 식별할 수 있다
- **(Evaluate)** 특정 회로 검증에 어떤 시뮬레이션 패러다임이 적합한지 판단할 수 있다

## 1. 현실의 칩 — 디지털·아날로그 공존

대부분의 실제 칩은 디지털과 아날로그가 섞여 있습니다. DV 엔지니어가 자주 만나는 5종:

| 칩 종류 | 디지털 부분 | 아날로그 부분 |
|--------|------------|--------------|
| DRAM | Command decoder, mode register, refresh counter | **Sense amp, bit line, cell capacitor, DLL, VPP/VBB regulator** |
| ADC | Calibration logic, output formatter | **Comparator, sample & hold, ladder network** |
| SerDes | Protocol layer, FEC | **TX driver, RX equalizer (CTLE/DFE), CDR, PLL** |
| PLL | Divider, lock detect | **VCO, charge pump, loop filter** |
| Power IC | Control FSM | **Power transistor, feedback network** |

> 검증 관점에서 중요한 사실: **이 표의 디지털 부분만 검증하면 칩이 silicon에서 동작하지 않는다.** DRAM sense amp가 100 mV 차이를 증폭하는지, SerDes RX equalizer가 ISI를 보상하는지 — 이것들은 디지털 시뮬레이션으로 절대 검증할 수 없습니다.

## 2. 순수 디지털 시뮬레이션의 한계

```
Digital simulator (VCS, Xcelium, Questa):
  - 신호 값: 0, 1, X, Z (이산)
  - 시간: 이벤트 기반 (event-driven)
  - 전압 개념 없음
  - 노이즈, 천이 시간, charge sharing, 임피던스 매칭 모델링 불가
```

DRAM read 경로의 핵심 동작인 **sense amp**가 BL과 BL_ref의 약 100 mV 차이를 증폭하는 동작을, 0/1만 다루는 digital sim에서는 표현조차 할 수 없습니다.

마찬가지로:

- DDR5 6.4 Gbps IO의 **eye opening** — voltage swing/slew rate의 함수 → digital sim 불가
- PLL의 **lock 거동** — VCO 주파수가 control voltage의 함수 → digital sim 불가
- ADC의 **monotonicity, INL/DNL** — 입력 voltage와 출력 code의 비선형 관계 → digital sim 불가

## 3. 순수 SPICE의 한계

```
SPICE simulator (HSPICE, Spectre, FineSim):
  - 신호 값: 실수 전압/전류 (연속)
  - 시간: 수치 미분방정식 풀이 (연속)
  - 트랜지스터 물리 모델 (BSIM4 등)
  - 매우 정확함
  - 매우 느림 — O(N²)~O(N³) 복잡도
```

예시 (실측 데이터):

| 회로 규모 | SPICE 시뮬레이션 시간 |
|---|---|
| 1k transistor (인버터 chain) | 수 초 |
| 1M transistor (단순 SoC 블록) | 수 일 ~ 수 주 |
| **10B transistor DRAM full** | **사실상 불가능** |

또한:

- **수렴 문제**: Newton-Raphson이 발산하면 시뮬레이션 멈춤
- **메모리**: 노드 수에 비례해 폭발적으로 증가
- **stimulus 작성**: 단순한 reset/clk 패턴도 SPICE netlist로 길게 표현해야 함

## 4. 그래서 — Mixed-Signal Simulation

**핵심 아이디어**: 디지털과 아날로그를 같은 시뮬레이션 안에서 동시에 돌리되, **각 영역에 맞는 알고리즘을 사용**한다.

```
       [전통적 분리 방식]                    [Mixed-Signal 방식]

  ┌──────────────────┐                ┌──────────────────────────┐
  │ Digital sim only │                │ Digital region │ Analog  │
  │ (sense amp 못 검증) │              │ (event-driven) │ (SPICE) │
  └──────────────────┘                │       ↕ Connect module    │
  ┌──────────────────┐                │       ↕                   │
  │ SPICE sim only   │                │ One unified simulation    │
  │ (full chip 불가) │                │                          │
  └──────────────────┘                └──────────────────────────┘
       ✗                                       ✓
```

Mixed-signal simulation에는 두 가지 통합 방식이 있습니다 — Ch02에서 자세히:

1. **AMS (Analog Mixed-Signal Simulation)**: digital sim + SPICE를 같이 돌리고 connect module로 잇기
2. **RNM (Real Number Modeling)**: 모든 것을 digital simulator 안에서 real-valued 함수로 처리

DRAM/SoC 산업의 실제 흐름:

- **RNM 우선** — 전체 칩 검증, 시나리오/coverage
- **Critical block만 AMS/SPICE** — sense amp offset, VCO jitter, charge pump

## 5. DV 엔지니어 입장에서 — 어떤 능력이 필요한가

UVM/SoC DV 경험자가 mixed-signal 영역으로 이동할 때 새로 배워야 할 것:

| 기존 (UVM/디지털 DV) | 추가 학습 (Mixed-Signal DV) |
|---|---|
| `logic`, `always @(posedge clk)` | `real`, `nettype`, `always @(vin)` (값 변화) |
| Constrained random | 동일하나 `real` 값에 적용 |
| Functional coverage (bin) | Voltage bin coverage |
| Scoreboard (transaction 비교) | Threshold·margin 검사 |
| Driver/Monitor/Agent | RNM에서는 inline TB가 더 흔함 |
| 없음 | **물리 모델링 능력** — charge sharing, Pelgrom 등 |
| 없음 | **AMS connect module 설정** |

## 6. 대표 문제 — "어디까지 디지털, 어디부터 mixed-signal인가?"

### 문제

DDR5 메모리 컨트롤러를 검증한다고 가정. 다음 블록 각각에 대해, 어떤 시뮬레이션 패러다임이 적합한지 판단하고 이유를 쓰시오.

1. AXI 명령 디코더
2. Refresh scheduler
3. PHY의 DLL
4. DQ IO buffer
5. ZQ calibration FSM
6. Mode register file

### 풀이

| 블록 | 패러다임 | 이유 |
|---|---|---|
| 1. AXI 디코더 | **Digital** | 순수 로직 — bus protocol, 상태 머신 |
| 2. Refresh scheduler | **Digital** | 카운터 + FSM. tREFI 시간만 정확하면 됨 |
| 3. PHY의 DLL | **RNM (+SPICE corner)** | Lock behavior는 RNM, jitter는 SPICE |
| 4. DQ IO buffer | **RNM 대량 / SPICE 정밀** | Eye, slew는 RNM. Signal integrity는 SPICE/IBIS-AMI |
| 5. ZQ cal FSM | **Digital + RNM** | FSM은 digital, 저항 측정 부분은 RNM (mock current) |
| 6. Mode register file | **Digital** | Reg array. mode register 자체는 디지털 |

### 통찰

- **외부에서 보이는 행동이 voltage·timing에 의존하는가?**가 1차 판단 기준
- **칩 안에 갇혀 있는 디지털 로직**은 그냥 digital sim
- **외부 핀에 닿는 신호** (DQ, CK, CA, DQS) 주변은 mixed-signal 영역
- **칩 내부지만 voltage가 의미를 갖는 블록** (sense amp, charge pump, regulator)도 mixed-signal

## 7. 흔한 오해

1. **"Mixed-signal은 아날로그 설계자만 다룬다"** — 틀림. DDR/SerDes/PCIe 등 모든 고속 인터페이스의 sign-off는 mixed-signal 시뮬레이션을 거칩니다. DV 엔지니어가 stimulus·시나리오·coverage를 책임집니다.
2. **"RNM은 정확도가 떨어지는 sim"** — 맞기도 하고 틀리기도. **모델이 잘 작성되면** 실제 sense amp 동작·DLL lock을 SPICE 결과와 거의 일치시킬 수 있습니다.
3. **"SPICE만 쓰면 sign-off 충분"** — 시간이 무한하면 가능. 현실에서는 critical corner만 SPICE, 나머지는 RNM/AMS로 분담.

## 핵심 정리

1. 현대 칩은 거의 모두 mixed-signal — DV 엔지니어가 피할 수 없음
2. 디지털 sim은 voltage를 못 보고, SPICE는 너무 느림 → 둘을 잇는 mixed-signal 필요
3. 산업 표준: **RNM 우선 + critical block SPICE 보완**
4. UVM 경험은 stimulus·coverage 측에서 활용 가능. 그러나 RNM 모델 작성은 새로 배워야

## 더 읽을거리

- 다음: [Ch02. 세 가지 시뮬레이션 세계 — Digital · SPICE · RNM](02_three_worlds_spice_ams_rnm.md)
- Rabaey, *Digital Integrated Circuits: A Design Perspective* — Ch01에서 디지털·아날로그 경계
- 퀴즈: [Ch01 퀴즈](quiz/ch01_quiz.md)
