# Unit 1 — Digital Design / RTL

!!! objective "학습 목표"
    이 모듈을 마치면:

    - **Distinguish** blocking(`=`) 과 non-blocking(`<=`) assignment 의 시뮬레이션 의미 차이를 설명하고 언제 어느 것을 써야 하는지 결정한다.
    - **Diagram** Mealy 와 Moore FSM 의 상태 전이 다이어그램을 그리고 출력 타이밍 차이를 설명한다.
    - **Compute** flop-logic-flop 경로의 setup/hold 마진을 계산하고 violation 원인을 분류한다.
    - **Apply** 두 클럭 도메인 간 1-bit, multi-bit, bus 신호를 안전하게 전달하는 회로를 설계한다.
    - **Compare** AXI, AHB, APB, PCIe, I2C, SPI, UART 의 핸드셰이크 / 대역폭 / 사용처 차이를 비교한다.
    - **Evaluate** FPGA 와 ASIC 환경에서 RTL 코딩 스타일이 어떻게 달라야 하는지 평가한다.

!!! info "사전 지식"
    - 디지털 회로 기본 (조합/순차, FF, MUX, latch)
    - Verilog `module`/`always`/`assign` 기본 문법

---

## 1. Verilog / SystemVerilog 핵심

### 1.1 `always` 블록 3가지 — 가장 자주 묻는 비교

| 블록 | 트리거 | 합성 결과 | 대표 용도 |
|------|--------|-----------|-----------|
| `always @(*)` (또는 `always_comb`) | 우변 신호 변화 | 조합 회로 | MUX, decoder, ALU |
| `always @(posedge clk)` (또는 `always_ff`) | clock edge | flip-flop | register, counter, FSM |
| `always @(posedge clk or negedge rst_n)` | clock edge or async reset | async-reset flop | 비동기 reset 사용 시 |

**팁** — SystemVerilog 에서는 `always_comb` / `always_ff` / `always_latch` 를 사용해 *의도* 를 컴파일러에게 알려라. `always @(*)` 보다 *latch 추론* 같은 실수가 잡힌다.

### 1.2 Blocking(`=`) vs Non-Blocking(`<=`) — 가장 빈출 질문

**규칙**:
- 조합(`always_comb`) → `=` (blocking)
- 순차(`always_ff`) → `<=` (non-blocking)

**왜?**
순차 회로에서 *동시에* 여러 신호가 클럭 엣지에 갱신되어야 한다. `<=` 는 우변을 *같은 시간 슬롯* 에서 모두 평가한 뒤 다음 슬롯에서 좌변에 대입 — 모든 flop 이 *동시* 갱신.

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

!!! warning "흔한 오해"
    `reg` 는 *flip-flop이라는 뜻이 아니다*. `always_comb` 안에서 `reg` 에 대입하면 조합 회로다. 합성 결과는 *대입 패턴* 으로 결정된다.

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
- Moore — 출력이 *flop* 에서 나옴 → glitch 없음, 타이밍 closure 쉬움. **단점**: 1-cycle latency.
- Mealy — 출력이 *조합* → 빠르고 상태 수 적음. **단점**: input glitch 가 출력으로 전파, STA 어려움.

**인터뷰 정답 템플릿**: "산업에서는 출력에 1-cycle latency 가 허용되면 Moore 가 안전. 응답 latency 가 critical 하면 Mealy + output flop 으로 절충."

### 2.1 State Encoding 비교

| 인코딩 | 비트 수 (N 상태) | 장점 | 단점 |
|--------|-----------------|------|------|
| Binary | ⌈log2 N⌉ | flop 수 최소 | 디코딩 로직 큼 |
| One-hot | N | 디코딩 단순(flop 한 개로 상태 인식), 빠름 | flop 수 많음 |
| Gray | ⌈log2 N⌉ | 한 비트씩 변화 → CDC 안전 | 전이가 인접 상태로 제한 |

**FPGA**: flop 이 풍부 → one-hot 선호.
**ASIC**: 면적 민감 → binary 또는 gray.

---

## 3. Static Timing Analysis (STA)

### 3.1 기본 부등식

$$ t_{ck \to q} + t_{logic} + t_{su} \le T_{clk} - t_{skew} \quad \text{(Setup)} $$

$$ t_{ck \to q} + t_{logic} \ge t_{hold} + t_{skew} \quad \text{(Hold)} $$

- **Setup violation** — 다음 클럭 엣지까지 도착 못함. *주파수 낮춰* 해결 가능.
- **Hold violation** — 같은 클럭 엣지에 너무 *빨리* 도착해 이전 값을 덮어씀. *주파수와 무관*. **fix 가 어렵다** (logic 추가 / buffer 삽입).

### 3.2 Clock Insertion / Skew / Uncertainty

- **Insertion delay** — clock root 에서 flop clock pin 까지 지연
- **Skew** — 두 flop 간 insertion delay 차이 (= launch_clock_insertion − capture_clock_insertion)
- **Uncertainty** — jitter + margin (PLL jitter, OCV)

!!! tip "Skew 의 부호"
    Setup 에는 *positive skew* 가 도움 (capture clock 이 늦게 도착 → 도착 여유). Hold 에는 *positive skew* 가 *나쁨* (도착 너무 일찍). 그래서 *clock buffer 추가* 가 hold fix 의 흔한 수단.

### 3.3 Multi-cycle / False Path

- **Multi-cycle path** — 데이터가 N 사이클에 걸쳐 캡쳐된다고 *설계자가 약속*. SDC `set_multicycle_path -setup N`.
- **False path** — 두 비동기 도메인 / 테스트 모드 경로 — STA 검사 *제외*. `set_false_path`.

---

## 4. Clock Domain Crossing (CDC)

### 4.1 Metastability 의 본질

서로 다른 클럭 도메인 사이를 직접 연결하면 setup/hold 가 *반드시* 깨지는 순간이 온다 → flop 출력이 *결정되지 않은 전압* 에서 진동 → 다음 stage 에서 *서로 다른 값* 으로 인식 → 시스템 fault.

### 4.2 1-bit 신호 — 2-FF Synchronizer

```systemverilog
always_ff @(posedge clk_dst or negedge rst_n) begin
  if (!rst_n) {sync_q1, sync_q2} <= 2'b0;
  else        {sync_q1, sync_q2} <= {async_in, sync_q1};
end
// 최종 신호: sync_q2
```

- 2 단 (또는 3 단, MTBF 요구가 매우 엄격하면) flop 으로 metastability 가 정착할 시간 부여
- **제약**: 1-bit 펄스만 안전. *multi-bit bus* 에는 못 씀 (각 비트가 *다른 사이클* 에 도착할 수 있음).

### 4.3 Multi-bit Bus — 두 가지 정석

**(A) Handshake (REQ/ACK)** — 4-phase handshake. 느리지만 안전.

```
src → dst: REQ ↑ (with data)
dst → src: ACK ↑
src → dst: REQ ↓
dst → src: ACK ↓
```

REQ/ACK 각각 2-FF synchronizer 통과. 데이터는 REQ 동안 *변하지 않음* (Gray code 불필요).

**(B) Async FIFO** — 양쪽 도메인이 각자 RD/WR pointer. Pointer 를 *Gray code* 로 변환해 상대 도메인에 전달.

```
src 도메인: WR pointer (binary) → Gray → 2-FF sync → dst 도메인이 비교 (empty/full 판정)
```

**왜 Gray code?** Gray 는 한 번에 1 비트만 변한다 → multi-bit sync 시 *intermediate 값* 이 *유효한 인접 값* 으로만 나옴 → 잘못된 pointer 비교 방지.

---

## 5. Protocols & Interfaces — 1줄 요약

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
- `valid` 가 `ready` 를 기다리는 건 OK. **`ready` 가 `valid` 를 기다리는 건 *deadlock* 위험** — `ready` 는 `valid` 와 *독립적* 으로 결정되어야 함.

### 5.2 Backpressure

수신 측이 데이터를 받지 못하는 상태 (`ready=0`) → 송신 측이 멈춤. FIFO 가 가득 차면 자연스럽게 backpressure 가 생긴다.

---

## 6. FPGA vs ASIC — 코딩 차이

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

??? question "Q1. (Understand) `always_ff` 에서 `=` 를 쓰면 어떻게 되나?"
    합성 자체는 *대부분의* 도구가 받아들이고 결과는 의도와 같을 *수도* 있다. 그러나:

    - 시뮬레이션과 합성 결과 *불일치* 가능 — 두 `always_ff` 가 서로의 출력을 읽는 경우 *evaluation order* 가 비결정.
    - 코드 리뷰에서 *항상* 잡히는 안티패턴.
    - **답**: "절대 쓰면 안 된다. non-blocking 으로 통일."

??? question "Q2. (Apply) 10MHz 신호를 100MHz 도메인으로 보낼 때 단순 2-FF sync 가 안 되는 경우는?"
    1. **Pulse 가 src clock 1 cycle 보다 짧을 때** — dst clock 이 미처 못 잡음.
    2. **신호가 multi-bit** — 각 비트가 다른 cycle 에 latch 될 수 있음.
    3. **연속 변화 신호** — sync 자체는 OK 지만 *값* 이 정확하지 않을 수 있음 (특정 시점 값을 정확히 잡아야 한다면 handshake 필요).

    **답**: "Pulse stretcher + 2-FF sync 또는 handshake 또는 async FIFO 중 상황에 맞게 선택."

??? question "Q3. (Analyze) 다음 코드의 버그는?"
    ```systemverilog
    always_ff @(posedge clk) begin
      if (en) data <= in;
      out = data;
    end
    ```
    - `out = data` 에서 *blocking* 사용 → out 은 *이전 사이클의 data* 가 아니라 *현재 사이클의 새 data* 를 읽음 (둘은 *같은 always_ff* 안에서 평가).
    - 더 큰 문제: `out` 이 `always_ff` 안에서 대입 → flop 추론. 의도가 조합이라면 `always_comb` 로 분리.

    **답**: "`out` 을 분리된 `always_comb` 또는 `assign out = data;` 로 빼고, 또는 `out <= data;` 로 통일."

??? question "Q4. (Evaluate) AXI vs AHB — 어느 것을 언제 쓰는가?"
    - **AHB**: 단순, single-master 인터커넥트. 작은 SoC, 디버그 버스, 펌웨어 영역. 데이터 폭 32~128b, 단일 채널.
    - **AXI**: 고성능. 5 채널(AR/R/AW/W/B) 으로 read/write 동시 진행, ID 기반 OOO, burst. 큰 SoC, 메모리 컨트롤러 ↔ NoC.

    **답**: "성능과 OOO 가 필요하면 AXI, 그렇지 않으면 AHB 가 디버그/면적 측면에서 우월."

??? question "Q5. (Create) Async FIFO 의 empty / full 판정 로직을 설계해라."
    ```
    WR domain:  wr_ptr (binary) → wr_ptr_gray → sync to RD domain → rd_side_wr_ptr_gray
    RD domain:  rd_ptr (binary) → rd_ptr_gray → sync to WR domain → wr_side_rd_ptr_gray

    Empty (RD domain): rd_ptr_gray == rd_side_wr_ptr_gray
    Full  (WR domain): wr_ptr_gray == {~rd_side_at_msb_pair, rest of rd_side_rd_ptr_gray}
    ```

    Full 판정은 두 pointer 가 *반 바퀴 차이* — depth 가 2^N 이라 MSB 가 다르면서 나머지는 같으면 full.

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
- [Unit 1 퀴즈](quiz/01_digital_rtl_quiz.md) 로 자기 점검
