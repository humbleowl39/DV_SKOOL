# Ch01. 왜 Mixed-Signal Simulation인가

## 학습 목표

- **(Remember)** Mixed-signal 칩의 5가지 대표 예와 디지털/아날로그 영역을 나열할 수 있다
- **(Understand)** 순수 digital sim과 순수 SPICE의 한계를 설명할 수 있다
- **(Analyze)** 한 칩의 어느 부분이 mixed-signal 검증이 필요한지 식별할 수 있다
- **(Evaluate)** 특정 회로 검증에 어떤 시뮬레이션 패러다임이 적합한지 판단할 수 있다

## 1. 현실의 칩 — 디지털·아날로그 공존

대부분의 실제 칩은 디지털과 아날로그가 섞여 있습니다. 흔히 "디지털 칩"이라고 부르는 DRAM이나 SerDes조차 내부를 들여다보면 아날로그 회로 없이는 동작할 수 없습니다. DRAM의 sense amplifier가 비트 셀에서 흘러 나오는 미세 전하를 증폭하지 않으면 데이터를 읽을 수 없고, SerDes의 CTLE·DFE 같은 수신 이퀄라이저가 없으면 채널을 통과하며 뭉개진 신호에서 비트를 복원할 수 없습니다. DV 엔지니어가 자주 만나는 5종을 도메인별로 정리하면 다음과 같습니다.

| 칩 종류 | 디지털 부분 | 아날로그 부분 |
|--------|------------|--------------|
| DRAM | Command decoder, mode register, refresh counter | **Sense amp, bit line, cell capacitor, DLL, VPP/VBB regulator** |
| ADC | Calibration logic, output formatter | **Comparator, sample & hold, ladder network** |
| SerDes | Protocol layer, FEC | **TX driver, RX equalizer (CTLE/DFE), CDR, PLL** |
| PLL | Divider, lock detect | **VCO, charge pump, loop filter** |
| Power IC | Control FSM | **Power transistor, feedback network** |

> 검증 관점에서 중요한 사실: **이 표의 디지털 부분만 검증하면 칩이 silicon에서 동작하지 않는다.** DRAM sense amp가 100 mV 차이를 증폭하는지, SerDes RX equalizer가 ISI를 보상하는지 — 이것들은 디지털 시뮬레이션으로 절대 검증할 수 없습니다.

## 2. 순수 디지털 시뮬레이션의 한계

디지털 시뮬레이터(VCS, Xcelium, Questa 등)는 신호를 0, 1, X, Z의 네 가지 이산 값으로만 표현합니다. 시간도 이벤트가 발생하는 순간에만 진행하는 event-driven 방식이며, 전압이라는 개념 자체가 없습니다. 이 설계는 디지털 로직 검증에는 완벽하지만, 아날로그 동작 앞에서는 구조적 한계가 드러납니다.

DRAM read 경로의 핵심 동작인 **sense amplifier**가 BL과 BL_ref 사이의 약 100 mV 차이를 검출하고 증폭하는 과정을 생각해 봅시다. 비트 셀에서 비트 라인으로 흘러드는 전하의 양이 "신호"인데, 그 신호의 크기는 두 전압의 차이이지 0 또는 1이 아닙니다. 0/1만 다루는 digital sim에서는 이 동작을 표현조차 할 수 없으며, sense amp가 올바르게 증폭하는지 검증할 방법이 없습니다.

같은 이유로 digital sim이 처리하지 못하는 것들이 있습니다. DDR5 6.4 Gbps IO의 **eye opening**은 voltage swing과 slew rate의 함수인데, 전압이 없는 시뮬레이터에서는 eye 자체를 그릴 수 없습니다. PLL의 **lock 거동**은 VCO 출력 주파수가 control voltage에 따라 연속적으로 달라지는 현상이므로 역시 digital sim으로는 확인 불가능합니다. ADC의 **INL/DNL** — 입력 전압과 출력 코드 사이의 비선형 관계 — 도 마찬가지입니다. 결국 전압·전류·위상이 의미를 갖는 모든 동작이 digital sim의 사각지대에 놓입니다.

## 3. 순수 SPICE의 한계

그렇다면 SPICE(HSPICE, Spectre, FineSim 등)로 전체를 검증하면 어떨까요? SPICE는 신호 값을 실수 전압·전류로 표현하고, 시간을 수치 미분방정식으로 풀며, BSIM4 같은 트랜지스터 물리 모델을 내장합니다. 정확도 면에서는 타의 추종을 불허합니다. 문제는 속도입니다.

SPICE의 계산 복잡도는 회로 규모 N에 대해 O(N²) ~ O(N³)에 가깝습니다. 인버터 몇 개짜리 회로는 수 초면 끝나지만, 1M 트랜지스터 규모의 단순 SoC 블록은 수 일에서 수 주가 걸립니다. 10억 개의 셀을 가진 DRAM 전체를 SPICE로 시뮬레이션하는 것은 사실상 불가능합니다.

속도 문제 외에도 SPICE에는 구조적 약점이 있습니다. Newton-Raphson 반복법이 발산하면 시뮬레이션 자체가 중단되는 수렴 문제가 있고, 노드 수에 비례해 메모리도 폭발적으로 늘어납니다. 게다가 "reset 후 1000 클록 동안 랜덤 패턴을 인가"와 같이 디지털 DV에서는 몇 줄로 쓸 수 있는 stimulus를 SPICE netlist로 표현하려면 수백 줄이 필요합니다. 복잡한 시나리오를 검증할 수 있는 구조를 갖추기 어렵습니다.

## 4. 그래서 — Mixed-Signal Simulation

정리하면, 디지털 sim만으로는 전압을 볼 수 없고 SPICE만으로는 전체 칩 규모를 감당할 수 없습니다. 이 두 가지 한계를 동시에 돌파하는 접근이 **Mixed-Signal Simulation**입니다. 핵심 아이디어는 디지털과 아날로그를 같은 시뮬레이션 안에서 동시에 돌리되, **각 영역에 맞는 알고리즘을 사용**하는 것입니다.

```d2
direction: right

traditional: "전통적 분리 방식 ✗" {
  style.fill: "#fce4ec"
  digital_only: "Digital sim only\n(sense amp 못 검증)"
  spice_only: "SPICE sim only\n(full chip 불가)"
}

mixed: "Mixed-Signal 방식 ✓" {
  style.fill: "#e8f5e9"
  digital_region: "Digital region\n(event-driven)"
  analog_region: "Analog\n(SPICE)"
  connect: "Connect module"
  unified: "One unified simulation"
  digital_region -> connect
  analog_region -> connect
  connect -> unified
}
```

이 통합에는 두 가지 방식이 있습니다. 하나는 **AMS (Analog Mixed-Signal Simulation)**로, digital 시뮬레이터와 SPICE 시뮬레이터를 connect module로 연결해 함께 돌리는 방식입니다. 정확도는 높지만 SPICE 부분이 병목이 되어 느립니다. 다른 하나는 **RNM (Real Number Modeling)**으로, SPICE를 쓰지 않고 디지털 시뮬레이터 안에서 아날로그 동작을 실수(real) 값을 사용하는 함수로 근사합니다. 속도는 훨씬 빠르지만 모델을 잘 작성해야 정확도를 담보할 수 있습니다. 자세한 비교는 Ch02에서 다룹니다.

DRAM과 SoC 산업의 실제 흐름은 이렇습니다. 전체 칩 검증과 시나리오·커버리지 회귀는 **RNM 우선**으로 돌리고, sense amp 오프셋, VCO 지터, charge pump처럼 트랜지스터 물리 정밀도가 반드시 필요한 **critical block만 AMS 또는 SPICE**로 별도 검증합니다.

## 5. DV 엔지니어 입장에서 — 어떤 능력이 필요한가

UVM과 디지털 DV를 해 온 엔지니어가 mixed-signal 영역으로 이동할 때, 익숙한 도구와 기술 중 많은 부분을 그대로 활용할 수 있습니다. constrained-random stimulus, functional coverage, scoreboard 패턴, UVM 컴포넌트 구조는 여전히 유효합니다. 단, 신호 타입이 `logic`에서 `real`로 바뀌고, 시퀀스가 전압 파형을 만들어야 하며, coverage의 bin이 전압 범위를 가리키게 됩니다. 그리고 지금까지 없었던 완전히 새로운 능력, 즉 **물리 모델링 능력**이 추가됩니다. charge sharing, Pelgrom mismatch 같은 아날로그 현상을 SV 코드로 표현하는 것은 기존 디지털 DV에는 없던 작업입니다.

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

## 7. Mixed-Signal 검증의 5가지 핵심 도전

UVM·디지털 DV에서 mixed-signal로 넘어오면 익숙하지 않은 5가지 도전이 동시에 등장합니다. 이후 챕터들이 결국 이 5가지를 어떻게 다루느냐의 변주입니다.

### ① 모델 정확도 ↔ 속도

RNM은 **단순화된 물리(simplified physics)**입니다. 1차 효과(이상적 VCO 주파수, 이상적 ADC 양자화)는 잘 잡지만 noise · jitter · settling 같은 2차 효과는 손으로 주입해야 합니다. 모델을 너무 단순하게 만들면 현실에서 발생하는 문제를 놓치는 false-pass가 생기고, 반대로 너무 정밀하게 만들면 시뮬레이션 속도가 느려져 회귀 비용이 폭발합니다. 적절한 균형점을 찾는 것이 mixed-signal 모델링의 핵심 기술입니다.

### ② Equivalence 부재

디지털 DV에는 LEC(logic equivalence checking)라는 강력한 도구가 있어 RTL과 게이트 넷리스트가 같은 논리를 구현하는지 자동으로 확인합니다. mixed-signal에는 이에 해당하는 성숙한 도구가 없습니다. spec 수식 ↔ behavioral RNM 모델 ↔ SPICE 넷리스트 사이의 동등성을 자동으로 검증하기 어렵기 때문에, 검증 엔지니어가 **assertion · coverage · cross-check**을 통해 신뢰성을 직접 쌓아야 합니다.

### ③ X 부재 위험

디지털에서 `logic` 타입은 초기화하지 않으면 X가 됩니다. X가 전파되면 어딘가에서 assertion이 울리거나 시뮬레이션이 이상하게 흘러 문제를 발견할 수 있습니다. 그러나 `real` 타입에는 X가 없습니다. 초기화하지 않으면 `0.0`이 됩니다. 드라이버를 빠뜨린 ADC 입력이 조용히 0 V로 동작하고, "ADC 코드 = 0"이 스펙에 맞으면 testbench가 그냥 PASS를 냅니다. 모든 RNM 입력에 `bit valid` 신호를 동반하거나 driver-presence assertion을 강제해야 이 함정을 피할 수 있습니다 — Ch10의 "흔한 함정"에서 다시 다룹니다.

### ④ Multi-Driver Resolution

두 드라이버가 한 wire를 잡으면 디지털은 X를 내고 아날로그 물리는 KCL/KVL에 따라 합성된 전압을 만들어 냅니다. 그런데 plain `real` 변수는 last-write-wins입니다. 마지막으로 쓴 값이 조용히 이긴다는 뜻입니다. 임피던스 상호 작용이나 공급 전압 강하 같은 현상을 올바르게 표현하려면 **nettype + resolution function**으로 KCL/KVL을 명시해야 합니다. Ch05에서 자세히 다룹니다.

### ⑤ Coverage 정의

"analog 신호 X가 충분히 스윕되었는가"를 cycle 기반 coverage로 판단하기는 어렵습니다. 0 V에서 1.8 V까지 ramp를 한 번 인가해도 0~1.8 V 범위 전체의 coverage가 100%처럼 보일 수 있기 때문입니다. 의미 있는 coverage를 만들려면 **range binning · threshold crossing · transition pattern**을 covergroup으로 변환해야 합니다.

> 이 5가지는 **항상 동시에** 등장합니다. 한 가지만 잘 다루는 환경은 결국 다른 4가지에서 false-pass를 흘립니다.

## 8. 흔한 오해

1. **"Mixed-signal은 아날로그 설계자만 다룬다"** — 틀림. DDR/SerDes/PCIe 등 모든 고속 인터페이스의 sign-off는 mixed-signal 시뮬레이션을 거칩니다. DV 엔지니어가 stimulus·시나리오·coverage를 책임집니다.
2. **"RNM은 정확도가 떨어지는 sim"** — 맞기도 하고 틀리기도. **모델이 잘 작성되면** 실제 sense amp 동작·DLL lock을 SPICE 결과와 거의 일치시킬 수 있습니다.
3. **"SPICE만 쓰면 sign-off 충분"** — 시간이 무한하면 가능. 현실에서는 critical corner만 SPICE, 나머지는 RNM/AMS로 분담.

## 9. 이 토픽이 다루는 범위

- **중점**: SV-RNM 언어 기능(nettype, interconnect, real), UVM + RNM env 통합 패턴, analog IP별 검증 패턴 (PLL · ADC · DAC · LDO · SerDes), 흔한 함정과 회피
- **보조**: VAMS·Spice cosim — 보조 도구로만 다룹니다. 실제 tape-out 흐름에서도 **99%의 회귀는 RNM**에서 돌고, **1% spot check만 Spice**로 가는 것이 일반적입니다.

## 핵심 정리

1. 현대 칩은 거의 모두 mixed-signal — DV 엔지니어가 피할 수 없음
2. 디지털 sim은 voltage를 못 보고, SPICE는 너무 느림 → 둘을 잇는 mixed-signal 필요
3. 산업 표준: **RNM 우선 + critical block SPICE 보완**
4. UVM 경험은 stimulus·coverage 측에서 활용 가능. 그러나 RNM 모델 작성은 새로 배워야

## 더 읽을거리

- 다음: [Ch02. 세 가지 시뮬레이션 세계 — Digital · SPICE · RNM](02_three_worlds_spice_ams_rnm.md)
- Rabaey, *Digital Integrated Circuits: A Design Perspective* — Ch01에서 디지털·아날로그 경계
- 퀴즈: [Ch01 퀴즈](quiz/ch01_quiz.md)
