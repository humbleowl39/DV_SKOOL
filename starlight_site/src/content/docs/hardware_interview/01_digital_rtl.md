---
title: "Unit 1 — Digital Design / RTL"
---

:::tip[학습 목표]
이 모듈을 마치면:

- **Distinguish** blocking(`=`) 과 non-blocking(`<=`) assignment 의 시뮬레이션 의미 차이를 설명하고 언제 어느 것을 써야 하는지 결정한다.
- **Diagram** Mealy 와 Moore FSM 의 상태 전이 다이어그램을 그리고 출력 타이밍 차이를 설명한다.
- **Compute** flop-logic-flop 경로의 setup/hold 마진을 계산하고 violation 원인을 분류한다.
- **Apply** 두 클럭 도메인 간 1-bit, multi-bit, bus 신호를 안전하게 전달하는 회로를 설계한다.
- **Compare** AXI, AHB, APB, PCIe, I2C, SPI, UART 의 핸드셰이크 / 대역폭 / 사용처 차이를 비교한다.
- **Evaluate** FPGA 와 ASIC 환경에서 RTL 코딩 스타일이 어떻게 달라야 하는지 평가한다.
:::
:::note[사전 지식]
- 디지털 회로 기본 (조합/순차, FF, MUX, latch)
- Verilog `module`/`always`/`assign` 기본 문법
:::
---

## 1. Verilog / SystemVerilog 핵심

먼저 이 모듈 전체에서 거듭 나오는 기본 용어를 한 줄씩 짚고 갑니다. **RTL**(Register-Transfer Level — 회로를 "레지스터 사이를 데이터가 매 클럭 어떻게 이동하는가"로 기술하는 추상화 수준)은 Verilog/SystemVerilog로 하드웨어 동작을 적는 층입니다. **조합 회로**(combinational — 출력이 현재 입력만으로 결정되고 기억이 없는 회로, 예: 덧셈기)와 **순차 회로**(sequential — 클럭과 과거 상태를 기억하는 회로, 예: 레지스터)가 디지털 설계의 두 축입니다. **flip-flop**(FF, 클럭 엣지마다 입력값을 한 번 붙잡아 다음 엣지까지 유지하는 1비트 저장소)은 순차 회로의 기본 소자이고, **MUX**(multiplexer, 여러 입력 중 선택 신호에 따라 하나를 고르는 조합 회로), **latch**(클럭 엣지가 아니라 enable 레벨이 열려 있는 동안 입력을 그대로 통과시키는 저장 소자 — 의도치 않게 생기면 타이밍을 망친다)도 자주 등장합니다.

### 1.1 `always` 블록 3가지 — 가장 자주 묻는 비교

| 블록 | 트리거 | 합성 결과 | 대표 용도 |
|------|--------|-----------|-----------|
| `always @(*)` (또는 `always_comb`) | 우변 신호 변화 | 조합 회로 | MUX, decoder, ALU(arithmetic logic unit, 산술·논리 연산 회로) |
| `always @(posedge clk)` (또는 `always_ff`) | clock edge | flip-flop | register(여러 flop을 묶은 다중 비트 저장소), counter, FSM(finite state machine, 유한 상태 기계) |
| `always @(posedge clk or negedge rst_n)` | clock edge or async reset | async-reset flop | 비동기 reset 사용 시 |

여기서 `always`(특정 신호 변화나 클럭 엣지가 생길 때마다 안에 적힌 동작을 실행하는 SystemVerilog 블록)는 RTL의 동작을 적는 핵심 구문이고, **clock edge**(클럭 신호가 0→1로 바뀌는 순간 — posedge; flop이 값을 붙잡는 기준 시점), **async reset**(클럭과 무관하게 곧바로 회로를 초기 상태로 되돌리는 비동기 리셋)도 표 안에서 처음 등장합니다.

**팁** — SystemVerilog 에서는 `always_comb` / `always_ff` / `always_latch` 를 사용해 *의도* 를 컴파일러에게 알려라. `always @(*)` 보다 *latch 추론* 같은 실수가 잡힌다.

### 1.2 Blocking(`=`) vs Non-Blocking(`<=`) — 가장 빈출 질문

**규칙**:
- 조합(`always_comb`) → `=` (blocking)
- 순차(`always_ff`) → `<=` (non-blocking)

**왜?**
순차 회로에서 *동시에* 여러 신호가 클럭 엣지에 갱신되어야 한다. `<=` 는 우변을 *같은 시간 슬롯* 에서 모두 평가한 뒤 다음 슬롯에서 좌변에 대입 — 모든 flop 이 *동시* 갱신.

이 "평가 따로, 대입 따로" 는 SystemVerilog 스케줄러의 **region** 개념에서 나온다. 한 time slot 안에서 시뮬레이터는 정해진 순서의 region 들을 차례로 처리하는데, 핵심은 두 개다 — `<=` 의 _우변 평가_ 는 **Active region** 에서 (현재 값으로) 일어나고, _좌변 대입_ 은 그보다 나중인 **NBA(Non-Blocking Assignment) region** 에서 한꺼번에 일어난다. 그래서 같은 클럭 엣지의 모든 `<=` 가 _서로의 옛 값_ 을 읽고 평가를 끝낸 뒤에야 일제히 대입되므로, 코드 _작성 순서와 무관하게_ 모든 flop 이 동시에 갱신된 것처럼 보이고 race 가 사라진다. 반대로 `=`(blocking)는 Active region 에서 평가-대입이 즉시 끝나 다음 줄이 _새 값_ 을 보게 되므로 조합 논리에 맞다. 이 region 모델은 UVM TB 가 신호를 언제 driving/sampling 해야 race-free 한지의 토대와 같다 — 자세한 driver/monitor 의 clocking·sampling 타이밍은 [UVM Module 02 — Agent/Driver/Monitor](../../uvm/02_agent_driver_monitor/) 참조.

```systemverilog
// ❌ 나쁜 예 — shift register 가 의도대로 안 됨
always_ff @(posedge clk) begin
  q1 = d;     // 즉시 q1 갱신
  q2 = q1;    // 이미 갱신된 q1 사용 → q2 = d (shift 안 됨!)
end

// ✅ 좋은 예
always_ff @(posedge clk) begin
  q1 <= d;
  q2 <= q1;   // 이전 사이클의 q1 사용 → 정상 shift
end
```

### 1.3 `wire` vs `reg` (vs SystemVerilog `logic`)

- `wire` — `assign` 또는 module port 로 *연속 구동*
- `reg` — `always` 블록 *내부* 에서 대입 (조합/순차 *모두* 가능, "register" 라는 이름이 오해를 부른다)
- `logic` — SV 의 통합형. `wire`, `reg` 둘 다 대체 가능 (단, multi-driver 는 `wire` 필요)

:::caution[흔한 오해]
`reg` 는 *flip-flop이라는 뜻이 아니다*. `always_comb` 안에서 `reg` 에 대입하면 조합 회로다. 합성 결과는 *대입 패턴* 으로 결정된다.
:::
### 1.4 `initial` / `fork-join` — 합성 가능?

- `initial` — *시뮬레이션 전용*. 합성 안 됨. testbench 에서만.
- `fork ... join` / `fork ... join_any` / `fork ... join_none` — SV testbench 의 multi-threading. 합성 안 됨.

---

## 2. 상태기계 (FSM) — Mealy vs Moore

| 모델 | 출력 함수 | 출력 타이밍 | 그림 표기 |
|------|-----------|-------------|-----------|
| **Moore** | `out = f(state)` | 상태 진입 후 1 클럭 지연 | 출력은 상태 *원* 안에 |
| **Mealy** | `out = f(state, input)` | 입력에 *즉시* 반응 (조합) | 출력은 *전이 화살표* 위에 |

**트레이드오프**:
Moore 는 출력이 *flop* 에서 나오기 때문에 glitch(조합 회로의 신호가 최종값으로 안정되기 전 잠깐 튀는 원치 않는 펄스) 없이 clean 한 신호가 나오고 타이밍 closure(모든 경로가 타이밍 제약을 만족하도록 맞추는 작업) 도 용이합니다. 그 대신 상태가 바뀐 *다음 클럭*에야 출력이 나오므로 1-cycle latency(입력에서 결과가 나오기까지의 클럭 지연) 가 생깁니다. 반면 Mealy 는 출력이 *조합 회로*로 만들어지기 때문에 현재 입력에 즉시 반응해 상태 수도 적어집니다. 하지만 input 에 glitch 가 있으면 그대로 출력으로 전파되고, STA 도 복잡해집니다.

**인터뷰 정답 템플릿**: "산업에서는 출력에 1-cycle latency 가 허용되면 Moore 가 안전. 응답 latency 가 critical 하면 Mealy + output flop 으로 절충."

### 2.1 State Encoding 비교

| 인코딩 | 비트 수 (N 상태) | 장점 | 단점 |
|--------|-----------------|------|------|
| Binary | ⌈log2 N⌉ | flop 수 최소 | 디코딩 로직 큼 |
| One-hot | N | 디코딩 단순(flop 한 개로 상태 인식), 빠름 | flop 수 많음 |
| Gray | ⌈log2 N⌉ | 한 비트씩 변화 → CDC 안전 | 전이가 인접 상태로 제한 |

**State encoding**(상태 인코딩 — FSM의 각 상태를 실제 비트 패턴에 어떻게 대응시킬지 정하는 방식)은 위처럼 세 가지가 대표적입니다. **Binary**(상태를 일반 이진수로 번호 매김), **One-hot**(상태마다 전용 flop 하나를 두고 그 비트만 1로 켜는 방식), **Gray**(Gray code — 이웃한 두 값이 정확히 1비트만 다르도록 매긴 인코딩)이며, Gray와 CDC의 관계는 §4에서 다룹니다.

**FPGA**: flop 이 풍부 → one-hot 선호.
**ASIC**: 면적 민감 → binary 또는 gray.

---

## 3. Static Timing Analysis (STA)

**STA**(Static Timing Analysis, 정적 타이밍 분석 — 시뮬레이션 없이 모든 신호 경로의 지연을 계산해 클럭 안에 데이터가 제때 도착하는지 정적으로 검증하는 작업)는 회로가 목표 주파수로 동작할 수 있는지 판정합니다. 두 가지 핵심 제약이 **setup time**(클럭 엣지 *이전*에 데이터가 안정돼 있어야 하는 최소 시간)과 **hold time**(클럭 엣지 *이후*까지 데이터가 유지돼야 하는 최소 시간)입니다.

### 3.1 기본 부등식

$$ t_{ck \to q} + t_{logic} + t_{su} \le T_{clk} - t_{skew} \quad \text{(Setup)} $$

$$ t_{ck \to q} + t_{logic} \ge t_{hold} + t_{skew} \quad \text{(Hold)} $$

여기서 $t_{ck \to q}$ 는 clock-to-Q delay(클럭 엣지가 온 뒤 flop 출력이 실제로 바뀌기까지 걸리는 시간), $t_{logic}$ 은 두 flop 사이 조합 회로의 지연, $T_{clk}$ 는 클럭 주기, $t_{skew}$ 는 skew(아래 정의)입니다.

Setup violation 은 데이터가 *다음 클럭 엣지까지* 도착하지 못하는 경우로, 주파수를 낮추면 사이클 시간이 늘어나므로 해결 여지가 있습니다. Hold violation 은 반대로 데이터가 같은 클럭 엣지에 *너무 빨리* 도착해 이전 사이클의 값을 덮어쓰는 문제입니다. 주파수를 높이거나 낮춰도 타이밍 관계가 변하지 않아 **주파수와 무관**하며, logic 추가나 buffer 삽입으로 경로를 늘려야 해서 **fix 가 더 어렵습니다**.

### 3.2 Clock Insertion / Skew / Uncertainty

- **Insertion delay** — clock root 에서 flop clock pin 까지 지연
- **Skew** — 두 flop 간 insertion delay 차이 (= launch_clock_insertion − capture_clock_insertion)
- **Uncertainty** — jitter(클럭 엣지가 매 주기 미세하게 흔들리는 시간 오차) + margin (PLL jitter, OCV(On-Chip Variation, 같은 칩 안에서도 위치마다 소자 속도가 달라지는 편차를 STA가 보수적으로 반영하는 보정))

:::tip[Skew 의 부호]
Setup 에는 *positive skew* 가 도움 (capture clock 이 늦게 도착 → 도착 여유). Hold 에는 *positive skew* 가 *나쁨* (도착 너무 일찍). 그래서 *clock buffer 추가* 가 hold fix 의 흔한 수단.
:::
### 3.3 Multi-cycle / False Path

- **Multi-cycle path** — 데이터가 N 사이클에 걸쳐 캡쳐된다고 *설계자가 약속*. SDC(Synopsys Design Constraints, 클럭·예외 경로 등 타이밍 제약을 적는 표준 TCL 포맷) `set_multicycle_path -setup N`.
- **False path** — 두 비동기 도메인 / 테스트 모드 경로 — STA 검사 *제외*. `set_false_path`.

---

## 4. Clock Domain Crossing (CDC)

**Clock domain**(클럭 도메인 — 같은 하나의 클럭으로 동기 동작하는 회로 영역)이 여럿이고 서로 주파수·위상이 무관할 때, 한 도메인의 신호가 다른 도메인으로 건너가는 것을 **CDC**(Clock Domain Crossing, 클럭 도메인 횡단)라고 합니다. 이때 받는 쪽 flop의 setup/hold가 깨질 수 있어 특별한 회로가 필요합니다.

### 4.1 Metastability 의 본질

**Metastability**(준안정성 — flop이 setup/hold 위반으로 0도 1도 아닌 어중간한 전압에서 한동안 머무는 비안정 상태). 서로 다른 클럭 도메인 사이를 직접 연결하면 setup/hold 가 *반드시* 깨지는 순간이 온다 → flop 출력이 *결정되지 않은 전압* 에서 진동 → 다음 stage 에서 *서로 다른 값* 으로 인식 → 시스템 fault.

### 4.2 1-bit 신호 — 2-FF Synchronizer

**Synchronizer**(동기화기 — 비동기 신호를 받는 도메인 클럭으로 안전하게 옮기기 위해 flop을 직렬로 2단 이상 연결한 회로)가 표준 해법입니다.

```systemverilog
always_ff @(posedge clk_dst or negedge rst_n) begin
  if (!rst_n) {sync_q1, sync_q2} <= 2'b0;
  else        {sync_q1, sync_q2} <= {async_in, sync_q1};
end
// 최종 신호: sync_q2
```

- 2 단 (또는 3 단, MTBF 요구가 매우 엄격하면) flop 으로 metastability 가 정착할 시간 부여
- **제약**: 1-bit 펄스만 안전. *multi-bit bus* 에는 못 씀 (각 비트가 *다른 사이클* 에 도착할 수 있음).

**왜 2-FF 가 metastability 를 "해결" 하나 — 준안정점이 지수적으로 풀리는 물리.** FF 내부는 두 개의 inverter 가 서로 출력을 입력으로 받는 cross-coupled 구조다. 정상 동작에서는 이 양의 되먹임이 0 또는 1 의 안정점으로 빠르게 수렴시키지만, setup/hold 를 위반한 입력이 잡히면 회로가 0 과 1 사이의 _준안정점(metastable point)_ — 비유하면 언덕 꼭대기에 놓인 공 — 에 잠시 머문다. 핵심은 이 상태가 _영원히_ 가지 않는다는 것이다. 준안정점에서의 미세한 편차가 양의 되먹임으로 _지수적으로 증폭_ 되어, 준안정 상태에 남아 있을 확률이 시간 t 에 대해 `e^(−t/τ)` 로 줄어든다 (τ 는 회로의 되먹임 시정수). 즉 시간을 더 주면 줄 수록 아직 풀리지 않았을 확률이 기하급수적으로 0 에 가까워진다. 2-FF synchronizer 가 하는 일이 바로 _이 "시간" 을 한 클럭 주기만큼 벌어 주는_ 것이다 — 첫 FF 가 metastable 해져도 두 번째 FF 가 샘플링하기까지 한 주기 동안 `e^(−T_clk/τ)` 만큼 정착 확률을 높여, 두 번째 FF 가 안정된 0/1 을 받을 확률을 실용적 MTBF(평균 고장 간격) 수준으로 끌어올린다. MTBF 요구가 극히 엄격하면 단을 3 으로 늘려 정착 시간을 한 주기 더 주는 것도 같은 지수 논리다.

### 4.3 Multi-bit Bus — 두 가지 정석

**(A) Handshake (REQ/ACK)** — handshake(보내는 쪽과 받는 쪽이 REQ/ACK 신호를 주고받아 "준비됐다/받았다"를 확인하며 진행하는 약속)의 4-phase 방식. 느리지만 안전.

```
src → dst: REQ ↑ (with data)
dst → src: ACK ↑
src → dst: REQ ↓
dst → src: ACK ↓
```

REQ/ACK 각각 2-FF synchronizer 통과. 데이터는 REQ 동안 *변하지 않음* (Gray code 불필요).

**(B) Async FIFO** — **FIFO**(First-In First-Out, 먼저 넣은 데이터가 먼저 나오는 큐 메모리)를 두 클럭 도메인이 공유하는 형태. 양쪽 도메인이 각자 RD/WR pointer(읽기/쓰기 위치를 가리키는 주소). Pointer 를 *Gray code* 로 변환해 상대 도메인에 전달.

```
src 도메인: WR pointer (binary) → Gray → 2-FF sync → dst 도메인이 비교 (empty/full 판정)
```

**왜 Gray code?** Gray 는 한 번에 1 비트만 변한다 → multi-bit sync 시 *intermediate 값* 이 *유효한 인접 값* 으로만 나옴 → 잘못된 pointer 비교 방지.

---

## 5. Protocols & Interfaces — 1줄 요약

아래 표의 프로토콜은 모두 칩 내부/칩 간 데이터 전송 규약입니다. 자주 보이는 약어를 먼저 풀면: **APB/AHB/AXI**는 ARM **AMBA**(Advanced Microcontroller Bus Architecture, ARM이 정한 SoC 내부 버스 표준군)에 속한 버스, **PCIe**(PCI Express, 칩과 칩을 잇는 고속 직렬 링크), **I2C**(2선 저속 직렬 버스), **SPI**(4선 고속 직렬 버스), **UART**(시작/정지 비트로 동기 없이 보내는 직렬 통신)입니다. 표에 나오는 **OOO**(out-of-order, 요청을 보낸 순서와 다른 순서로 응답이 와도 ID로 짝지어 처리), **burst**(주소를 한 번만 주고 연속된 여러 데이터를 몰아 전송)도 핵심 개념입니다.

| 프로토콜 | 도메인 | 핸드셰이크 | 대역폭 / 특징 |
|----------|--------|-----------|--------------|
| **APB** | SoC peripheral | psel/penable/pready | 단순, 저속, register access |
| **AHB** | SoC bus | hready/hresp | 중속, single master 가 단순 |
| **AXI** | High-perf SoC | 5 channel valid/ready | OOO, burst, ID-based |
| **PCIe** | Chip-to-chip | TLP + DLLP + Physical | GT/s, packet-based, root complex |
| **I2C** | Slow peripheral | SCL/SDA, START/STOP | 100K~3.4M bps, open-drain, multi-slave |
| **SPI** | Fast peripheral | SCLK/MOSI/MISO/CS | 단순, full-duplex, single master |
| **UART** | Serial debug | TX/RX, start/stop bit | async, baud-rate 기반, point-to-point |

### 5.1 Valid-Ready 핸드셰이크 — AXI/AMBA 의 핵심

```
master:  valid ────┐  ┌──
                   └──┘
slave:   ready ──┐  ┌────
                 └──┘
transfer 일어나는 순간: valid && ready (같은 클럭)
```

**규칙**:
- `valid` 는 한 번 raise 하면 transfer 까지 *내리면 안 됨*.
- `ready` 는 자유롭게 raise/lower 가능.
- `valid` 가 `ready` 를 기다리는 건 OK. **`ready` 가 `valid` 를 기다리는 건 *deadlock*(서로 상대가 먼저 움직이길 기다려 양쪽 다 영원히 멈추는 교착) 위험** — `ready` 는 `valid` 와 *독립적* 으로 결정되어야 함.

### 5.2 Backpressure

수신 측이 데이터를 받지 못하는 상태 (`ready=0`) → 송신 측이 멈춤. FIFO 가 가득 차면 자연스럽게 backpressure 가 생긴다.

---

## 6. FPGA vs ASIC — 코딩 차이

**FPGA**(Field-Programmable Gate Array — 출하 후 회로 구성을 다시 프로그래밍할 수 있는 칩)와 **ASIC**(Application-Specific Integrated Circuit — 특정 용도로 고정 제작하는 맞춤 칩)은 같은 RTL이라도 코딩 스타일이 달라집니다. 표에 나오는 **LUT**(Look-Up Table, FPGA에서 임의의 조합 논리를 구현하는 작은 진리표 메모리), **BRAM**(Block RAM, FPGA에 내장된 메모리 블록), **DSP block**(곱셈·누산을 빠르게 하는 FPGA 내장 연산 블록), **POR**(Power-On Reset, 전원이 켜질 때 회로를 초기화하는 리셋)도 함께 알아 둡니다.

| 항목 | FPGA | ASIC |
|------|------|------|
| Reset | Sync 또는 async, 둘 다 OK | 보통 **async assert, sync release** |
| Flop | 풍부 (LUT 마다) | 비싸다, 면적 민감 |
| Memory | BRAM block, 정해진 비트 폭 | 자유 — RAM compiler |
| Latch | **금지** (FPGA tool 이 무거운 LUT 합성) | 신중하게 사용 (clock gating cell 내부) |
| State encoding | One-hot 흔함 | Binary/gray |
| Multiplier | DSP block | full-custom 또는 합성 |

**FPGA 빈출 인터뷰**: "초기화 시 flop 값은?" → ASIC 은 *불정* (POR 후 reset 필요), FPGA 는 *bitstream load 시 초기값* 제공 가능 (Xilinx INIT 속성).

---

## 7. 샘플 인터뷰 Q&A

<details>
<summary>Q1. (Understand) `always_ff` 에서 `=` 를 쓰면 어떻게 되나?</summary>

합성 자체는 *대부분의* 도구가 받아들이고 결과는 의도와 같을 *수도* 있다. 그러나:

- 시뮬레이션과 합성 결과 *불일치* 가능 — 두 `always_ff` 가 서로의 출력을 읽는 경우 *evaluation order* 가 비결정.
- 코드 리뷰에서 *항상* 잡히는 안티패턴.
- **답**: "절대 쓰면 안 된다. non-blocking 으로 통일."

</details>
<details>
<summary>Q2. (Apply) 10MHz 신호를 100MHz 도메인으로 보낼 때 단순 2-FF sync 가 안 되는 경우는?</summary>

1. **Pulse 가 src clock 1 cycle 보다 짧을 때** — dst clock 이 미처 못 잡음.
2. **신호가 multi-bit** — 각 비트가 다른 cycle 에 latch 될 수 있음.
3. **연속 변화 신호** — sync 자체는 OK 지만 *값* 이 정확하지 않을 수 있음 (특정 시점 값을 정확히 잡아야 한다면 handshake 필요).

**답**: "Pulse stretcher + 2-FF sync 또는 handshake 또는 async FIFO 중 상황에 맞게 선택."

</details>
<details>
<summary>Q3. (Analyze) 다음 코드의 버그는?</summary>

```systemverilog
always_ff @(posedge clk) begin
  if (en) data <= in;
  out = data;
end
```
- `out = data` 에서 *blocking* 사용 → out 은 *이전 사이클의 data* 가 아니라 *현재 사이클의 새 data* 를 읽음 (둘은 *같은 always_ff* 안에서 평가).
- 더 큰 문제: `out` 이 `always_ff` 안에서 대입 → flop 추론. 의도가 조합이라면 `always_comb` 로 분리.

**답**: "`out` 을 분리된 `always_comb` 또는 `assign out = data;` 로 빼고, 또는 `out <= data;` 로 통일."

</details>
<details>
<summary>Q4. (Evaluate) AXI vs AHB — 어느 것을 언제 쓰는가?</summary>

- **AHB**: 단순, single-master 인터커넥트. 작은 SoC, 디버그 버스, 펌웨어 영역. 데이터 폭 32~128b, 단일 채널.
- **AXI**: 고성능. 5 채널(AR/R/AW/W/B) 으로 read/write 동시 진행, ID 기반 OOO, burst. 큰 SoC, 메모리 컨트롤러 ↔ NoC(Network-on-Chip, 칩 안의 블록들을 패킷으로 잇는 온칩 네트워크).

**답**: "성능과 OOO 가 필요하면 AXI, 그렇지 않으면 AHB 가 디버그/면적 측면에서 우월."

</details>
<details>
<summary>Q5. (Create) Async FIFO 의 empty / full 판정 로직을 설계해라.</summary>

```
WR domain:  wr_ptr (binary) → wr_ptr_gray → sync to RD domain → rd_side_wr_ptr_gray
RD domain:  rd_ptr (binary) → rd_ptr_gray → sync to WR domain → wr_side_rd_ptr_gray

Empty (RD domain): rd_ptr_gray == rd_side_wr_ptr_gray
Full  (WR domain): wr_ptr_gray == {~rd_side_at_msb_pair, rest of rd_side_rd_ptr_gray}
```

Full 판정은 두 pointer 가 *반 바퀴 차이* — depth 가 2^N 이라 MSB 가 다르면서 나머지는 같으면 full.

</details>
---

## 8. 핵심 정리 (Key Takeaways)

1. `always_ff` → `<=`, `always_comb` → `=` 는 **절대 규칙**.
2. Moore = 안전, Mealy = 빠름. 산업은 *Moore + 필요한 곳만 Mealy*.
3. Setup violation 은 *주파수* 로, Hold violation 은 *로직 / 버퍼* 로 해결.
4. CDC 는 1-bit→2FF, multi-bit→handshake 또는 async FIFO (+Gray code).
5. AXI/AHB/APB 의 valid-ready 핸드셰이크: *`ready` 는 `valid` 와 독립*.
6. FPGA 와 ASIC 은 *같은 RTL 이라도 다른 스타일* — reset, encoding, latch 정책이 다르다.

## 9. Further Reading

- *Verilog HDL Quick Reference Guide* (IEEE 1364 표준 발췌)
- *SystemVerilog for Design* (Sutherland) — `always_ff` / `logic` 등 SV-2012 문법
- Cummings, *Clock Domain Crossing (CDC) Design & Verification Techniques Using SystemVerilog* (SNUG 2008)
- ARM AMBA 5 AXI / AHB / APB spec — [DV SKOOL — AMBA Protocols](https://humbleowl39.github.io/DV_SKOOL/amba_protocols/)
- [Unit 1 퀴즈](../quiz/01_digital_rtl_quiz/) 로 자기 점검
