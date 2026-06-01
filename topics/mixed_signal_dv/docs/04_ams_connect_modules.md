# Ch04. AMS · Verilog-AMS · Connect Module

## 학습 목표

- **(Remember)** Verilog-AMS의 핵심 키워드(`electrical`, `analog`, `<+`, `V(...)`, `I(...)`)를 나열할 수 있다
- **(Understand)** Connect module이 왜 필요하고 어떻게 자동 삽입되는지 설명할 수 있다
- **(Apply)** 간단한 D2A · A2D connect module과 amplifier를 Verilog-AMS로 작성할 수 있다
- **(Analyze)** AMS 시뮬레이션의 병목과 동기화 오버헤드를 분석할 수 있다
- **(Evaluate)** RNM 대비 AMS가 적합한 검증 케이스를 식별할 수 있다

## 1. AMS Simulation 구조

AMS 시뮬레이션을 처음 배울 때 가장 중요한 것은 "두 개의 시뮬레이터가 같은 시간 축 위에서 동시에 동작한다"는 그림을 머릿속에 잡는 것입니다. 한쪽에는 VCS나 Xcelium 같은 디지털 시뮬레이터가 SV testbench와 디지털 RTL을 이벤트 기반으로 처리하고, 다른 한쪽에는 FineSim, HSPICE, Spectre 같은 SPICE 시뮬레이터가 아날로그 넷리스트를 수치 적분으로 풀고 있습니다. 두 엔진은 각자 자신의 영역을 독립적으로 계산하지만, **동일한 wall-clock time**을 공유하면서 주기적으로 동기화 점을 맞춥니다.

```
┌──────────────────────────────────────────────────────────────┐
│                  AMS Simulation Environment                   │
│                                                                │
│  ┌──────────────────────┐         ┌──────────────────────┐   │
│  │ Digital Simulator    │  Sync   │ Analog Simulator     │   │
│  │ (VCS / Xcelium)      │ ←─────→ │ (FineSim / HSPICE /   │   │
│  │                      │         │  Spectre)             │   │
│  │ - SV testbench       │         │ - SPICE netlist       │   │
│  │ - Digital RTL        │         │ - BSIM model          │   │
│  │ - Event-driven       │         │ - Numerical solver    │   │
│  └──────────────────────┘         └──────────────────────┘   │
│              ↑                                ↑                │
│              │     ┌─────────────────────┐    │                │
│              └─────┤   Connect modules   ├────┘                │
│                    │  (D2A, A2D, A2A)    │                     │
│                    └─────────────────────┘                     │
└──────────────────────────────────────────────────────────────┘
```

동기화할 때마다 connect module이 두 도메인 사이의 신호를 변환합니다. 동기화를 자주 할수록 정확도는 올라가지만 두 엔진이 서로 기다리는 오버헤드가 커져 속도가 떨어집니다. 이 정확도 ↔ 속도 trade-off는 AMS 설정의 핵심 파라미터입니다.

## 2. Connect Module — 두 도메인의 다리

### 2.1 왜 필요한가

디지털과 아날로그가 만나는 경계에는 반드시 번역이 필요합니다. 디지털 신호는 1'b1 또는 1'b0이지만, 아날로그 세계에서 "1"은 0.9 V인가요, 0.8 V인가요, 1.1 V인가요? 디지털의 X는 어떤 전압에 해당하나요? 디지털의 Z(tri-state)는 무한 임피던스를 의미하는데 이것을 어떻게 표현할까요?

```
Digital:   1'b1 ─────── electrical: 0.9 V (VDD)?  0.8 V? 1.1 V?
Digital:   1'b0 ─────── electrical: 0.0 V (GND)?
Digital:   1'bX ─────── electrical: ?? (NaN risk!)
Digital:   1'bZ ─────── electrical: tri-state (Hi-Z impedance)
```

이 번역 규칙 — threshold 전압, rise/fall time, drive strength — 을 정의하는 것이 **connect module**의 역할입니다. 규칙이 없으면 디지털의 "1"이 아날로그 측에 어떤 전압으로 나타나야 하는지 알 수 없고, 아날로그의 전압이 디지털 측에서 어떻게 0 또는 1로 해석되는지도 알 수 없습니다.

### 2.2 자동 삽입

```
Discipline 정의 → simulator가 net 양 끝의 discipline mismatch 감지
       → 매칭되는 connect module 자동 삽입
```

VAMS-2023 LRM은 자동 삽입을 위한 **connection rule(connectrules)** 문법을 제공합니다.

### 2.3 D2A Connect Module 예시

```verilog
// Verilog-AMS
`include "disciplines.vams"

connectmodule d2a_simple(in_d, out_a);
  input  in_d;        // logic
  output out_a;       // electrical
  logic in_d;
  electrical out_a;

  parameter real vh = 0.9;        // high voltage
  parameter real vl = 0.0;        // low voltage
  parameter real trise = 50p;     // rise time
  parameter real tfall = 50p;     // fall time

  analog begin
    V(out_a) <+ transition(
      (in_d === 1'b1) ? vh : vl,
      0,         // delay
      trise,
      tfall
    );
  end
endmodule
```

- `transition(value, delay, rise, fall)`: 이산 변화를 연속 천이로 변환
- `V(out_a) <+ expr`: V를 expr로 "기여(contribute)"

### 2.4 A2D Connect Module 예시

```verilog
connectmodule a2d_simple(in_a, out_d);
  input  in_a;        // electrical
  output out_d;       // logic
  electrical in_a;
  logic out_d;

  parameter real vth = 0.45;

  always begin
    @(cross(V(in_a) - vth, +1)) out_d = 1'b1;
    @(cross(V(in_a) - vth, -1)) out_d = 1'b0;
  end
endmodule
```

- `cross(expr, dir)`: expr이 0을 dir 방향으로 통과할 때 이벤트 발생

### 2.5 X / Z 처리 — 가장 흔한 함정

```verilog
// What if in_d === 1'bx?
analog begin
  if (in_d === 1'bx) begin
    // BAD: NaN 출력 위험
    V(out_a) <+ ???;
  end
end
```

대응:

- X를 mid-voltage(VDD/2)로 매핑하거나, 시뮬레이션을 fatal로 중단
- Z(tri-state)는 driver를 비활성화 (impedance 무한대)

## 3. Verilog-AMS 기본 문법

```verilog
`include "disciplines.vams"

module my_amplifier(in, out);
  input  in;
  output out;
  electrical in, out;     // 둘 다 analog 신호

  parameter real gain = 10;

  analog begin
    V(out) <+ gain * V(in);   // 연속시간 식
  end
endmodule
```

핵심 구문:

| 구문 | 의미 |
|------|------|
| `electrical` | 아날로그 신호 타입 (전압/전류) |
| `analog begin ... end` | 연속시간 동작 블록 |
| `V(node)` | 노드의 전압 |
| `I(branch)` | branch의 전류 |
| `<+` | **기여(contribution) 연산자** — KCL/KVL을 자동으로 풀게 함 |
| `ddt(x)` | 시간 미분 |
| `idt(x)` | 시간 적분 |
| `cross(expr, dir)` | zero-crossing 이벤트 |
| `transition(...)` | 이산→연속 천이 |
| `slew(...)` | slew-rate 제한 출력 |

## 4. Discipline — 신호의 "종류"

```verilog
// disciplines.vams에서 미리 정의
discipline electrical
  potential Voltage;     // 전압 도메인
  flow      Current;     // 전류 도메인
enddiscipline

// 사용자 정의 가능
discipline thermal
  potential Temperature;
  flow      Heat;
enddiscipline
```

Discipline mismatch가 발생하면 connect module이 필요 → simulator가 connectrules로 자동 매칭.

## 5. 실제 회로 예시 — RC 저역통과 필터

```verilog
`include "disciplines.vams"

module rc_lpf(in, out);
  input in;
  output out;
  electrical in, out;
  electrical gnd;

  parameter real R = 1k;
  parameter real C = 1n;

  analog begin
    // KCL at 'out' node:
    //  I_R (in → out)  =  I_C (out → gnd)
    //  (V(in) - V(out))/R  =  C * ddt(V(out))
    I(in, out) <+ (V(in) - V(out)) / R;
    I(out)     <+ C * ddt(V(out));
  end
endmodule
```

- `<+`가 KCL을 자동으로 적용
- 단지 식을 contribute하면 simulator가 노드 평형을 잡음

## 6. AMS의 강점과 약점

AMS의 가장 큰 강점은 SPICE 수준의 정확도를 유지하면서 큰 디지털 부분과 작은 아날로그 부분을 함께 검증할 수 있다는 것입니다. 표준 언어(Verilog-AMS)를 기반으로 하기 때문에 특정 벤더에 종속되지 않는다는 장점도 있습니다.

그러나 SPICE 부분이 언제나 병목입니다. sense amp array처럼 아날로그 블록이 크면 클수록 속도는 SPICE에 가까워지고 AMS의 효용이 줄어듭니다. 두 시뮬레이터 사이의 동기화 오버헤드도 무시할 수 없습니다. 또한 connect module 설정이 복잡하고, discipline mismatch가 발생했을 때 어디서 무엇이 잘못되었는지 추적하기 어렵습니다. 디지털과 아날로그 파형을 동시에 보는 debug 환경도 RNM보다 성숙도가 낮습니다. 이러한 약점들 때문에 AMS는 critical block의 sign-off와 spot check에 주로 쓰이고, 전체 회귀는 RNM으로 돌리는 패턴이 산업 표준이 되었습니다.

## 7. AMS vs RNM 결정 기준

| 검증 task | 추천 |
|----------|------|
| 트랜지스터 mismatch (Pelgrom) 정확 평가 | **AMS** (또는 SPICE) |
| Sense amp의 voltage trajectory만 보면 됨 | **RNM** |
| VCO 위상 노이즈 | **AMS** |
| DLL lock 시간 | **RNM** |
| Charge pump current/voltage 정확 평가 | **AMS** |
| IO buffer eye opening | **RNM (대량) + AMS (corner)** |
| BGR 출력 voltage variation | **AMS** |
| 전체 DRAM 칩 시뮬레이션 | **RNM 압도적** |

## 8. 대표 문제 — Connect Module 설정 오류 디버그

### 문제

다음 상황에서 무엇이 잘못되었나?

```verilog
// Top
module top;
  logic d_signal;
  electrical a_signal;

  digital_block u_d (.out(d_signal));
  analog_block  u_a (.in(a_signal));

  assign a_signal = d_signal;   // ❌ 문제!
endmodule
```

증상: 시뮬레이션이 시작하지만 a_signal 값이 항상 0V 또는 발산.

### 풀이

- `assign`은 digital 영역 — analog `electrical`에 직접 연결 불가
- `electrical` net에 `d_signal`을 연결하려면 **D2A connect module**이 필요

수정:

```verilog
module top;
  logic d_signal;
  electrical a_signal;

  digital_block u_d (.out(d_signal));
  analog_block  u_a (.in(a_signal));

  // D2A 변환
  d2a_simple #(.vh(0.9), .vl(0.0), .trise(50p), .tfall(50p))
    u_d2a (.in_d(d_signal), .out_a(a_signal));
endmodule
```

또는 simulator의 connectrules에 d2a를 등록 → **자동 삽입**.

### 통찰

- AMS 디버그의 1순위 질문: **"이 net의 discipline은?"**
- Discipline mismatch는 simulator 로그에 경고로 나타남 — 무시하면 silently 잘못된 결과

## 9. VAMS-2023 (2024-02) 주요 변경

Verilog-AMS LRM은 2023년 12월 Accellera 위원회 승인, 2024-02 공식 배포. 핵심:

- **자동 connectrule 매칭 강화** — multi-discipline 경계에서 우선순위 규칙 명확화
- **`paramset` 문법** — 동일 module을 다른 파라미터셋으로 인스턴스화
- **`@(driver_update)` 이벤트** — analog가 digital driver 갱신 감지
- 차세대(VAMS-2024+) 작업은 사실상 중단 — SystemVerilog-AMS와 통합 흐름

> Verilog-AMS는 2014년 v2.4 이후 사실상 SystemVerilog와 통합 흐름이 강해졌으며, VAMS-2023이 마지막 메이저 갱신으로 평가됨 (Accellera 발표).

## 10. Multi-Supply Boundary — 여러 전원 도메인 경계

실제 SoC는 같은 칩에 **1.8 V I/O · 0.9 V core · 0.6 V LP 도메인**이 공존합니다. 각 boundary에 맞는 connect rule을 **분리해서 binding**해야 합니다. 한 rule을 chip 전체에 적용하면 voltage swing이 잘못 매핑되어 false-pass/fail이 일어납니다.

```systemverilog
// 1.8 V I/O 도메인
connectrules cr_18v;
  connect e2l_18v input electrical, output wire;
  connect l2e_18v input wire,       output electrical;
  connect e2l_18v use threshold = 0.9, low = 0.0, high = 1.8;
  connect l2e_18v use V_low = 0.0,    V_high = 1.8, drive_strength = St1;
endconnectrules

// 0.9 V core 도메인
connectrules cr_09v;
  connect e2l_09v input electrical, output wire;
  connect l2e_09v input wire,       output electrical;
  connect e2l_09v use threshold = 0.45, low = 0.0, high = 0.9;
  connect l2e_09v use V_low = 0.0,      V_high = 0.9;
endconnectrules
```

각 rule의 핵심 옵션:

- **threshold** — electrical→logic 임계 전압. 보통 V_dd/2. ±band를 둬서 X-region 표현 가능
- **V_low / V_high** — logic→electrical 출력 전압
- **drive_strength** — 변환 element의 출력 임피던스. 다른 driver와 합성될 때 영향
- **tr / tf** — rise/fall time. 너무 짧으면 cosim step 폭증, 너무 길면 timing 부정확
- **supply_sensitive** — VDD가 변하면 V_high가 따라가도록 (PG-aware)

> Connect module은 simulator가 elaboration 시 boundary를 분석해 **자동으로 삽입**합니다. user가 instance를 명시할 필요는 없지만, **어떤 rule이 어디에 적용되는지**를 elaboration log로 확인해야 합니다 — 잘못된 도메인의 rule이 적용되면 silently 0/1 매핑이 비대칭이 됩니다. 새 IP integration 시 회귀의 1차 fail 카테고리가 거의 이것입니다.

## 11. SV-only RNM 환경의 명시적 r2l / l2r

SoC 전체를 SV-RNM으로 가면 `connectrules`가 거의 필요 없습니다. 남는 boundary는 **real → logic** 정도이고, 이건 일반 SV로 명시적으로 작성합니다 — 자동 삽입의 마법이 없어 debug가 명확해지는 장점.

```systemverilog
// real → logic (comparator)
module r2l #(real THRESH = 0.5) (
  input  wAnalog in_a,
  output logic   out_d
);
  always @(in_a.V) out_d = (in_a.V > THRESH);
endmodule

// logic → real (drive with impedance)
module l2r #(real V_LOW = 0.0, real V_HIGH = 1.8, real Z = 50.0) (
  input  logic   in_d,
  output wAnalog out_a
);
  analog_t drv;
  always @(in_d) begin
    drv.V = in_d ? V_HIGH : V_LOW;
    drv.I = 0.0;
    drv.Z = Z;
  end
  assign out_a = drv;
endmodule
```

→ 실무 권장:

- 최대한 **SV-RNM으로 통일**해서 connect module 의존을 줄입니다 (license · debug · 회귀 비용 모두 유리)
- VAMS legacy IP는 wrapper로 한 layer 추상화 — connect rule이 wrapper 안에 갇히게
- `connectrules` 파일은 한 곳에 모아두고 IP-side에서 import — chip-wide binding을 한 view로 관리
- 새 도메인 추가 시 회귀 1차로 **elaboration log + boundary connectivity report** 확인

## 12. `interconnect` — 타입 후 결정 placeholder

SoC top에서 한 net을 module 간에 잇고 싶은데, 양쪽이 다른 nettype을 쓰거나 어느 쪽이 정답인지 나중에야 결정되는 경우가 있습니다. `interconnect`는 **net의 타입을 binding 시점까지 미루는 placeholder**입니다 (SV-2012).

```systemverilog
module top;
  interconnect link;           // 타입 미정
  ip_a u_a (.out(link));       // out 포트가 wAnalog
  ip_b u_b (.in(link));        // in 포트도 wAnalog
  // elaborate 시점에 link가 wAnalog로 확정
endmodule
```

가장 유용한 사용처는 **다양한 nettype을 받아들이는 generic IP** (I/O pad, level shifter, repeater, switch fabric):

```systemverilog
// pad는 어떤 nettype이 들어와도 받아준다
module pad (interconnect io, input bit oe);
  // pad 내부 logic은 type-agnostic
endmodule

// supply rail에 사용
wSupply vdd_core;
pad u_pad_vdd (.io(vdd_core), .oe(1'b1));

// signal에 재사용
wAnalog ana_in;
pad u_pad_ana (.io(ana_in), .oe(1'b0));
```

제약과 함정:

- `interconnect` 자체에는 procedural assignment 불가 (`always` 안에서 `=`로 못 씀)
- SVA / covergroup의 직접 인자로 쓰면 type을 모르므로 에러 — 양 끝 port의 nettype이 resolve된 뒤에 사용
- `inout`만 의미가 보존됨. `input/output`은 양쪽 nettype이 일치해야
- 한 모듈 안의 두 곳에서 다른 nettype으로 binding 되면 elaboration error

> `interconnect`는 generic IP 한두 곳에만 등장하도록 제한합니다. 그 외 모든 곳에서는 nettype을 명시하는 것이 가독성·debug·검증 의도 추적 모두에 유리합니다.

## 13. 흔한 함정

| 함정 | 결과 | 대응 |
|------|------|------|
| Connect module 임계값 부적절 | 천이 타이밍 어긋남 | VDD/2 근처로 설정 |
| X-propagation 무시 | NaN 시뮬레이션 실패 | X→VDD/2 mapping 명시 |
| Discipline mismatch 경고 무시 | Silent 잘못된 결과 | 모든 경고 검토 |
| 너무 빈번한 sync | 시뮬레이션 매우 느림 | min_step 조정 |
| 너무 드문 sync | 빠른 천이 놓침 | 이벤트 기반 trigger |

## 핵심 정리

1. AMS = digital sim + SPICE를 connect module로 잇기
2. `electrical` net과 `logic` net 사이에는 반드시 D2A/A2D 필요
3. `V(...) <+ ...` 가 KCL을 자동 적용 — SPICE-like 식 표현 가능
4. 표준 LRM: VAMS-2023 (Accellera, 2024-02) — 사실상 마지막 메이저 갱신
5. AMS는 정확하지만 SPICE 병목 — RNM이 빠른 대안
6. Multi-supply SoC는 도메인별 connectrules를 분리해 binding — elaboration log 확인이 회귀 절차의 일부
7. SV-only RNM 흐름은 `connectrules` 의존을 최소화하고 명시적 `r2l`/`l2r` wrapper로 대체
8. `interconnect`는 generic IP에만 제한적으로 — 그 외에는 nettype 명시

## 더 읽을거리

- 다음: [Ch05. RNM with SystemVerilog](05_rnm_systemverilog.md)
- VAMS-2023 LRM (Accellera): https://www.accellera.org/images/downloads/standards/v-ams/VAMS-LRM-2023.pdf
- Kenneth Kundert, *The Designer's Guide to Verilog-AMS*
- 퀴즈: [Ch04 퀴즈](quiz/ch04_quiz.md)
