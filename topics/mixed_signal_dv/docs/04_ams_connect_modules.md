# Ch04. AMS · Verilog-AMS · Connect Module

## 학습 목표

- **(Remember)** Verilog-AMS의 핵심 키워드(`electrical`, `analog`, `<+`, `V(...)`, `I(...)`)를 나열할 수 있다
- **(Understand)** Connect module이 왜 필요하고 어떻게 자동 삽입되는지 설명할 수 있다
- **(Apply)** 간단한 D2A · A2D connect module과 amplifier를 Verilog-AMS로 작성할 수 있다
- **(Analyze)** AMS 시뮬레이션의 병목과 동기화 오버헤드를 분석할 수 있다
- **(Evaluate)** RNM 대비 AMS가 적합한 검증 케이스를 식별할 수 있다

## 1. AMS Simulation 구조

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

핵심 메커니즘:

- 두 simulator가 **동일한 wall-clock time**을 공유
- 매 동기화 점에서 connect module을 통해 신호 변환
- 동기화 빈도 = 정확도 ↑ / 속도 ↓ trade-off

## 2. Connect Module — 두 도메인의 다리

### 2.1 왜 필요한가

디지털 신호(logic 0/1)와 아날로그 신호(전압/전류)는 표현이 다릅니다.

```
Digital:   1'b1 ─────── electrical: 0.9 V (VDD)?  0.8 V? 1.1 V?
Digital:   1'b0 ─────── electrical: 0.0 V (GND)?
Digital:   1'bX ─────── electrical: ?? (NaN risk!)
Digital:   1'bZ ─────── electrical: tri-state (Hi-Z impedance)
```

→ 변환 규칙(threshold, rise/fall time, drive strength)을 **connect module**이 정의합니다.

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

### 강점

- **SPICE 정확도** + 디지털의 편리함
- 큰 디지털 부분과 작은 아날로그 부분의 협동 검증 가능
- 표준 언어 (vendor independent)

### 약점

- **SPICE 부분이 병목** — sense amp array처럼 큰 analog 영역이면 느림
- 두 시뮬레이터 사이 **동기화 오버헤드**
- Connect module 설정이 복잡 — discipline mismatch 추적 어려움
- 디버그 도구가 RNM보다 부족 — 두 영역을 동시에 보는 waveform이 필요

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

## 10. 흔한 함정

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

## 더 읽을거리

- 다음: [Ch05. RNM with SystemVerilog](05_rnm_systemverilog.md)
- VAMS-2023 LRM (Accellera): https://www.accellera.org/images/downloads/standards/v-ams/VAMS-LRM-2023.pdf
- Kenneth Kundert, *The Designer's Guide to Verilog-AMS*
- 퀴즈: [Ch04 퀴즈](quiz/ch04_quiz.md)
