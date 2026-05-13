# Module 01 — APB & AHB

<!-- DV-SKOOL-CH-CTX:start -->
<div class="chapter-context" data-cat="core">
  <a class="chapter-back" href="../">
    <span class="chapter-back-arrow">←</span>
    <span class="chapter-back-icon">🔄</span>
    <span class="chapter-back-text">AMBA Protocols</span>
  </a>
  <span class="chapter-divider">›</span>
  <span class="chapter-marker">Module 01</span>
</div>
<!-- DV-SKOOL-CH-CTX:end -->

<!-- DV-SKOOL-CH-TOC:start -->
<div class="page-toc">
  <span class="page-toc-label">목차</span>
  <a class="page-toc-link" href="#1-why-care-이-모듈이-왜-필요한가">1. Why care?</a>
  <a class="page-toc-link" href="#2-intuition-비유와-한-장-그림">2. Intuition</a>
  <a class="page-toc-link" href="#3-작은-예-apb-write-한-번을-cycle-단위로-따라가기">3. 작은 예 — APB Write 추적</a>
  <a class="page-toc-link" href="#4-일반화-2-phase-vs-pipelined-와-bridge">4. 일반화 — 2-phase vs Pipelined</a>
  <a class="page-toc-link" href="#5-디테일-신호-버전-burst-error">5. 디테일</a>
  <a class="page-toc-link" href="#6-흔한-오해-와-dv-디버그-체크리스트">6. 흔한 오해 + 디버그 체크리스트</a>
  <a class="page-toc-link" href="#7-핵심-정리-key-takeaways">7. 핵심 정리</a>
</div>
<!-- DV-SKOOL-CH-TOC:end -->

!!! objective "학습 목표"
    이 모듈을 마치면:

    - **Distinguish** APB와 AHB의 핸드셰이크/성능/용도 차이를 _2-phase vs pipelined_ 관점에서 구분할 수 있다.
    - **Trace** APB 트랜잭션의 SETUP → ACCESS → IDLE 흐름과 AHB의 ADDRESS → DATA 파이프라인을 cycle-by-cycle 로 추적할 수 있다.
    - **Implement** AHB-to-APB Bridge 의 동작 원리를 의사코드로 설명할 수 있다.
    - **Identify** APB 버전 진화 (APB3 → APB4 → APB5) 에서 추가된 신호와 그 동기를 매핑할 수 있다.
    - **Justify** AHB 의 ERROR 응답이 왜 2-cycle 인지 파이프라인 구조로 설명할 수 있다.

!!! info "사전 지식"
    - 디지털 회로 기본 (clock, 동기 FSM, setup/hold)
    - Read/Write 트랜잭션의 일반 의미
    - SoC top-level 구조의 감각 (CPU ↔ interconnect ↔ peripheral)

---

## 1. Why care? — 이 모듈이 왜 필요한가

### 1.1 시나리오 — 왜 _AXI 만_ 안 쓰고 APB/AHB 도 있나?

당신은 SoC 를 설계합니다. CPU + DDR + UART + GPIO + Timer + USB Controller + Crypto + DMA + Ethernet MAC + ...

첫 본능: "**AXI 하나로 통일**". 단순하고 일관성.

실제로 해보면:

| Peripheral | Register 수 | 면적 | AXI master slave 추가 면적 | 면적 오버헤드 |
|-----------|-----------|-----|---------------------------|-------------|
| UART | 8 | 5K gates | AXI slave: 20K gates | **400%** |
| GPIO | 4 | 2K gates | AXI slave: 20K gates | **1000%** |
| DDR controller | many | 200K gates | AXI master: 30K | 15% |
| Ethernet MAC | many | 500K gates | AXI master: 30K | 6% |

**UART/GPIO 같은 저속 peripheral 은 _AXI 인터페이스 자체_ 가 IP 본체보다 큼**. 면적/전력 낭비가 큼.

해법: **계층적 bus** —
- **APB**: 저속 peripheral 용. 게이트 적음, 매우 단순. SETUP/ACCESS 2-phase.
- **AHB**: 중속 (legacy IP, 일부 메모리). Pipelined address/data.
- **AXI**: 고속 (DDR, CPU, DMA, 고대역 IP). 5채널, outstanding/OOO.

**APB ↔ AXI bridge** 를 두고 high-speed 영역만 AXI, low-speed 는 APB 로 분리 → 면적 절감 70%+.

이후의 모든 AMBA 모듈은 한 가지 추상에서 출발합니다 — **"한 master 가 한 slave 의 register/memory 에 cycle-deterministic 하게 read/write 한다"**. AXI 의 5채널, AXI-Stream 의 TVALID/TREADY, exclusive monitor, ordering 까지 — 전부 이 가장 단순한 모델 (APB) 과 그 첫 확장 (AHB pipelined) 의 파생입니다.

이 모듈을 건너뛰면 AXI 의 VALID/READY 가 _왜_ 그렇게 정의됐는지 보이지 않습니다. 반대로 APB 의 SETUP/ACCESS 2-phase, AHB 의 address/data 파이프라인을 손으로 한 번 그려 보면 이후 AXI handshake / outstanding / OOO 가 "이미 본 패턴의 확장" 으로 보입니다. **APB = SoC register 접근의 사실상 표준**, **AHB = 레거시 IP 통합과 dual-port memory access 의 이해 모델** 입니다.

!!! question "🤔 잠깐 — APB 의 SETUP 단계가 _왜_ 필요한가?"
    AXI 는 1 cycle 에 valid + ready 동시 평가. APB 는 _2 phase_ (SETUP → ACCESS). 왜 한 phase 로 끝내지 않나?

    ??? success "정답"
        **저전력 + 저게이트** 최적화.

        - SETUP phase: PSEL = 1, PENABLE = 0. _주소만_ 안정화 (decode 가능). Slave 가 자기 활성화 결정.
        - ACCESS phase: PSEL = 1, PENABLE = 1. 데이터 전송.

        왜 분리? **SETUP 동안 _decoder 만_ 동작 → 다른 slave 들은 _clock gated_ 가능 → 전력 절감**. 또한 _주소 decode_ 와 _데이터 처리_ 가 _다른 cycle_ 이라 _critical path 짧음_ → 낮은 클럭 IP 도 사용 가능.

        AXI 가 1 cycle 인 이유는 _throughput_ 이 본질이라 전력보다 처리량 우선. 두 protocol 의 _다른 목표_ 가 _다른 phase 수_ 로 직결.

---

## 2. Intuition — 비유와 한 장 그림

!!! tip "💡 한 줄 비유"
    **APB** = _신호등이 있는 1차로 골목길_. SETUP 신호로 "갑니다" 알리고, ACCESS 에서 가고, PREADY 가 1 일 때만 다음 차가 출발. 단순 / 느림 / 게이트 작음.<br>
    **AHB** = _신호등 + 파이프라인_. 한 차가 ACCESS 하는 동안 다음 차가 미리 SETUP 자리에 들어옴. 매 cycle throughput.

### 한 장 그림 — APB 2-phase vs AHB pipeline

```
                APB (single transaction = 2 phases)
                ─────────────────────────────────────────
   PCLK    : ─┐ ┌─┐ ┌─┐ ┌─┐ ┌─┐ ┌─
              └─┘ └─┘ └─┘ └─┘ └─┘
   Phase   :   IDLE   SETUP   ACCESS  IDLE
   PSEL    : ───────┘                   └───
   PENABLE : ──────────────┘            └───
   PREADY  : ──────────────────────┘    └───   ← slave 가 ready 라 1
                                   ↑
                            전송 완료 (1 transaction = 2 cycle)


                AHB (address phase 와 data phase 가 1 cycle 겹침)
                ──────────────────────────────────────────────────
   HCLK    : ─┐ ┌─┐ ┌─┐ ┌─┐ ┌─┐ ┌─
              └─┘ └─┘ └─┘ └─┘ └─┘
   ADDR    :   A1   A2   A3   --   --     ← Address Phase (앞선 cycle)
   WDATA   :   --   D1   D2   D3   --     ← Data Phase    (1 cycle 뒤)
                    ▲
              T2 = A2 발행 + D1 데이터 전송이 동시에 발생
              ⇒ 매 cycle 한 transaction throughput
```

### 왜 이렇게 설계됐는가 — Design rationale

ARM AMBA 가 풀어야 했던 두 가지 상충 요구가 있었습니다.

1. **저속 peripheral (UART, GPIO, OTP, timer)** 은 register 한 두 개만 있고 SoC 전체에 수십~수백 개 깔립니다. 인터페이스 게이트가 IP 자체보다 크면 면적 낭비가 큽니다 → **APB 가 가장 단순한 형태로 분리**.
2. **메모리·DMA 접근** 은 throughput 이 본질입니다. 매 cycle 데이터를 주고받지 못하면 라인레이트를 채울 수 없습니다 → **AHB 의 address/data 파이프라인** 으로 시작, 이후 AXI 의 5채널로 확장.

이 분기 — "단순함을 위한 APB" 와 "throughput 을 위한 AHB/AXI" — 가 이후 AMBA family 전체의 골격이고, **하나의 SoC 안에 둘 다 존재** 합니다 (AHB-to-APB Bridge 가 그 접점).

---

## 3. 작은 예 — APB Write 한 번을 cycle 단위로 따라가기

가장 단순한 시나리오. CPU 가 PCLK domain 의 APB slave register 에 **`PADDR=0x40, PWDATA=0xDEAD_BEEF`** 를 write. PREADY 는 1 cycle wait state 가 들어갑니다.

### Cycle-by-cycle timeline

```
   cycle :    T1       T2        T3        T4        T5
              IDLE    SETUP     ACCESS    ACCESS    IDLE
                              (PREADY=0  (PREADY=1
                               wait)     완료)
   PCLK    :  ─┐ ┌──┐ ┌──┐ ┌──┐ ┌──┐ ┌──
                └─┘  └─┘  └─┘  └─┘  └─┘
   PSEL    :        ┌──────────────────┐
                    └ T2 부터 1
   PENABLE :              ┌─────────────┐
                          └ T3 부터 1
   PWRITE  :        ┌──────────────────┐ (Write)
   PADDR   :        ┤      0x40        ├
   PWDATA  :        ┤   0xDEAD_BEEF    ├
   PREADY  :  ─────────────┐    ┌──────  (T3=0, T4=1)
                            └────┘
                                ▲
                          T4 rising edge 에서 transfer 완료
   PSLVERR :        ──────────────  0  ──   (정상 응답)
```

### 단계별 의미

| Step | Cycle | 누가 | 무엇을 | 왜 |
|---|---|---|---|---|
| ① | T1 | bus | IDLE — PSEL=0 | 이전 transaction 종료 |
| ② | T2 | master | SETUP phase 진입 — PSEL=1, PENABLE=0, PADDR/PWDATA/PWRITE 동시 발행 | slave 가 주소를 latch 할 시간 |
| ③ | T3 | master | ACCESS phase 진입 — PENABLE=1 | "이 transaction 을 진행한다" 의 신호 |
| ④ | T3 | slave | PREADY=0 으로 wait state 삽입 | register write 가 1 cycle 더 필요 |
| ⑤ | T3 | master | PADDR/PWDATA/PWRITE/PSEL/PENABLE 모두 hold | wait state 동안 신호 변경 금지 (invariant) |
| ⑥ | T4 | slave | PREADY=1, PSLVERR=0 발행 | transfer 완료 신호 |
| ⑦ | T4 (rising) | bus | data sampled | master/slave 모두 이 edge 에서 transaction 완료로 인지 |
| ⑧ | T5 | bus | IDLE 로 복귀 — PSEL=0, PENABLE=0 | 다음 transaction 또는 idle |

```systemverilog
// APB master 의 의사 SystemVerilog (synth-friendly FSM)
typedef enum {S_IDLE, S_SETUP, S_ACCESS} state_t;
state_t state, nstate;

always_ff @(posedge PCLK or negedge PRESETn)
  if (!PRESETn) state <= S_IDLE;
  else          state <= nstate;

always_comb begin
  nstate = state;
  unique case (state)
    S_IDLE  : if (req)                    nstate = S_SETUP;
    S_SETUP :                             nstate = S_ACCESS;
    S_ACCESS: if (PREADY)                 nstate = (req ? S_SETUP : S_IDLE);
  endcase
end

assign PSEL    = (state != S_IDLE);
assign PENABLE = (state == S_ACCESS);
// T2~T4 동안 모든 payload 신호 hold — register 를 PREADY 까지 갱신 금지
```

!!! note "여기서 잡아야 할 두 가지"
    **(1) ACCESS 진입 = PENABLE 의 rising edge 1번** — APB 는 SETUP 과 ACCESS 가 _반드시 분리된 cycle_ 입니다. PSEL 과 PENABLE 을 같은 cycle 에 올리는 master FSM = 프로토콜 위반.<br>
    **(2) PREADY=0 동안 모든 payload (PADDR, PWDATA, PWRITE, PSTRB, PPROT) 가 hold** — 가장 흔한 APB 버그. PREADY=1 이 나오기 전까지는 master 도 slave 도 신호를 _바꾸면 안 됩니다_.

---

## 4. 일반화 — 2-phase vs Pipelined 와 Bridge

### 4.1 두 패턴의 일반화

| 패턴 | 한 transaction 의 phase | throughput | wait state 처리 |
|------|------------------------|------------|---------------|
| **2-phase (APB)** | SETUP → ACCESS | 최대 2 cycle 당 1 transaction | PREADY=0 → ACCESS 연장 |
| **Pipelined (AHB)** | Address (T_n) + Data (T_{n+1}) 가 겹침 | 매 cycle 1 transaction | HREADY=0 → 모든 phase stall |

이 두 패턴이 이후 모든 AMBA 의 뼈대입니다. AXI 는 pipelined 를 5개 채널로 _분리_ 한 것 (channel 마다 독립 VALID/READY).

### 4.2 AHB 파이프라인 — 일반 timing

```
   HCLK   : ─┐ ┌─┐ ┌─┐ ┌─┐ ┌─┐ ┌─┐ ┌─
             └─┘ └─┘ └─┘ └─┘ └─┘ └─┘
   HADDR  :   A1   A2   A3   --   --   --      ← Address phase
   HWRITE :    1    1    0    -                ← write/read flag (address phase 와 동기)
   HWDATA :   --   D1   D2   --   --   --      ← Data phase (1 cycle 뒤)
   HRDATA :   --   --   --   R3   --   --      ← Read data phase
   HREADY :    1    1    1    1    1    1
                ▲
        T2 : address phase A2 + data phase D1 동시 발생
```

### 4.3 AHB Wait State 시 모든 phase 동시 stall

```
   T1     T2    T3     T4    T5
   A1     A2    A2     A3    --     ← HADDR : T2 의 stall 중 A2 hold
   --     D1    D1     D2    --     ← HWDATA: T2 의 stall 중 D1 hold
    1     1     0      1     1      ← HREADY: T3 = 0 (slave wait)
                ▲
         "address 와 data 가 함께 stall" — 둘 중 하나만 stall 하면 파이프라인 깨짐
```

### 4.4 AHB-to-APB Bridge — 두 패턴의 접점

```mermaid
flowchart LR
    CPU["CPU"]
    BR["AHB-APB Bridge"]
    SL["APB slave"]
    CPU -- "AHB (pipeline)" --> BR
    BR -- "APB (2-phase)" --> SL

    classDef ep stroke:#1a73e8,stroke-width:2px
    classDef br stroke:#137333,stroke-width:2px
    class CPU,SL ep
    class BR br
```

**Bridge 의 책임**

1. AHB Address phase 에서 PADDR / PWRITE 캡처
2. AHB Data phase 에서 PWDATA 캡처
3. APB SETUP/ACCESS 를 시퀀싱 (2 cycle 추가)
4. APB PREADY 가 1 이 될 때까지 AHB HREADY=0 으로 stall
5. AHB Burst → APB 단일 transfer N 개로 분해
6. HRESP ↔ PSLVERR 매핑

**의사 동작 (AHB Single Write)**

```
   T1: AHB master  : HADDR=0x100, HWRITE=1, HTRANS=NONSEQ, HREADY=1
   T2: AHB master  : HWDATA=0xFF (data phase)
       Bridge      : PSEL=1, PADDR=0x100, PWRITE=1   (APB SETUP)
       Bridge      : HREADY=0  (bridge 가 끝날 때까지 stall)
   T3: Bridge      : PENABLE=1, PWDATA=0xFF          (APB ACCESS)
   T4: APB slave   : PREADY=1
       Bridge      : HREADY=1, HRESP=OKAY            (AHB 완료)
```

→ AHB 1 transaction 이 APB 측에서는 보통 3–4 cycle. AHB Burst (예: INCR4) 는 그대로 4 × 3–4 = 12–16 cycle.

---

## 5. 디테일 — 신호, 버전, Burst, Error

### 5.1 APB 신호 일람

| 신호 | 방향 (Master→Slave) | 역할 |
|------|-------------------|------|
| PCLK | - | 클럭 |
| PRESETn | - | 리셋 (Active Low) |
| PSEL | M→S | Slave 선택 |
| PENABLE | M→S | 전송 활성화 (2번째 phase) |
| PWRITE | M→S | 1=Write, 0=Read |
| PADDR | M→S | 주소 |
| PWDATA | M→S | 쓰기 데이터 |
| PRDATA | S→M | 읽기 데이터 |
| PREADY | S→M | Slave 준비 (Wait State 삽입) |
| PSLVERR | S→M | 에러 응답 |

#### 전송 타이밍 (요약 ASCII)

```
         Setup Phase    Access Phase
         (PSEL=1,       (PENABLE=1,
          PENABLE=0)     PREADY로 완료)

PCLK:    ─┐  ┌──┐  ┌──┐  ┌──┐
          └──┘  └──┘  └──┘  └──

PSEL:    ────────────────────
              ┌──────────────

PENABLE: ─────────┌──────────
                   (Access)

PADDR:   ─────XXXX┤ ADDR ├──
PWDATA:  ─────XXXX┤ DATA ├──

PREADY:  ─────────────┐      (1 cycle later = no wait)
                       └──
              또는 여러 cycle 후 = wait state

Write: PSEL + PADDR + PWDATA → PENABLE → PREADY → 완료
Read:  PSEL + PADDR → PENABLE → PREADY + PRDATA → 완료
```

#### Wait State (PREADY)

```
No Wait:     Setup → Access(PREADY=1 즉시) → 완료 (2 cycle)
With Wait:   Setup → Access(PREADY=0) → ... → PREADY=1 → 완료

PREADY가 0인 동안 Access Phase가 연장됨
→ 느린 Slave가 시간을 벌 수 있음
```

#### APB DV 검증 포인트

| 항목 | 시나리오 |
|------|---------|
| 기본 R/W | 모든 레지스터 Write → Read Back |
| Wait State | PREADY 지연 → 데이터 정확 |
| Error | PSLVERR 응답 → 올바른 처리 |
| 리셋 | Reset 후 레지스터 기본값 |
| 연속 접근 | Back-to-back 트랜잭션 |

### 5.2 APB 버전 진화 — APB3 → APB4 → APB5

#### APB3 (AMBA 3, 2003)

원래 APB (AMBA 2) 에는 PREADY/PSLVERR 이 없었다. APB3 에서 추가:

- **PREADY**: Slave 가 wait state 삽입 가능 → 느린 Slave 지원
- **PSLVERR**: 에러 응답 가능 → 잘못된 접근 탐지

#### APB4 (AMBA 4, 2010) — 현재 가장 많이 사용

| 추가 신호 | 역할 |
|----------|------|
| **PPROT[2:0]** | Protection 정보: [0]=Normal/Privileged, [1]=Secure/Non-Secure, [2]=Data/Instruction |
| **PSTRB[N-1:0]** | Write Byte Strobe: 바이트 단위 쓰기 마스크 (AXI 의 WSTRB 과 동일 개념) |

```
PSTRB 예시 (32-bit 데이터 버스):
  PSTRB = 4'b1111 → 4바이트 모두 쓰기 (Full Word)
  PSTRB = 4'b0011 → 하위 2바이트만 쓰기 (Half Word)
  PSTRB = 4'b0001 → 최하위 1바이트만 쓰기 (Byte)
  PSTRB = 4'b1100 → 상위 2바이트만 쓰기

PPROT 예시:
  PPROT = 3'b000 → Normal, Secure, Data access
  PPROT = 3'b001 → Privileged, Secure, Data access
  PPROT = 3'b010 → Normal, Non-Secure, Data access

→ TrustZone 기반 SoC에서 Secure/Non-Secure 접근 구분에 필수
```

#### APB5 (AMBA 5, 2021)

| 추가 신호 | 역할 |
|----------|------|
| **PWAKEUP** | 저전력 모드에서 트랜잭션 전에 Slave 깨우기 (Clock Gating 과 연동) |
| **PAUSER** | User-defined 사이드밴드 (주소 phase) |
| **PWUSER** | User-defined 사이드밴드 (쓰기 데이터 phase) |
| **PRUSER** | User-defined 사이드밴드 (읽기 데이터 phase) |
| **PBUSER** | User-defined 사이드밴드 (응답 phase) |

> **면접 포인트**: "APB4 와 APB5 의 차이?"
> → APB5 는 저전력(PWAKEUP)과 사이드밴드(xUSER)가 핵심. IoT/모바일 SoC 의 전력 관리 요구를 반영.

### 5.3 AHB 신호 (AHB-Lite, single Master)

| 신호 | 방향 | 역할 |
|------|------|------|
| HCLK | - | 클럭 |
| HRESETn | - | 리셋 |
| HADDR | M→S | 주소 |
| HTRANS | M→S | 전송 타입 (IDLE/BUSY/NONSEQ/SEQ) |
| HWRITE | M→S | 1=Write, 0=Read |
| HSIZE | M→S | 전송 크기 (byte/half/word) |
| HBURST | M→S | Burst 타입 (SINGLE/INCR/WRAP) |
| HWDATA | M→S | 쓰기 데이터 (이전 cycle 의 주소에 대응) |
| HRDATA | S→M | 읽기 데이터 |
| HREADY | S→M | Slave 준비 (0=Wait) |
| HRESP | S→M | 응답 (OKAY/ERROR) |

#### AHB 파이프라인 — APB 와의 핵심 차이

```
APB: 주소와 데이터가 같은 phase
AHB: 주소 phase와 데이터 phase가 1 cycle 겹침 (파이프라인)

HCLK:  ─┐ ┌─┐ ┌─┐ ┌─┐ ┌─┐ ┌─
         └─┘ └─┘ └─┘ └─┘ └─┘

HADDR: ─┤A1├─┤A2├─┤A3├─────────  Address Phase
HWDATA:──────┤D1├─┤D2├─┤D3├───  Data Phase (1 cycle 뒤)

  T1: Address A1
  T2: Address A2 + Data D1 ← 파이프라인 겹침!
  T3: Address A3 + Data D2
  T4:            + Data D3

→ 매 cycle 주소와 데이터가 동시 전송 = 대역폭 2배 (APB 대비)
```

### 5.4 HTRANS (전송 타입)

| 값 | 이름 | 의미 |
|---|------|------|
| 2'b00 | IDLE | 전송 없음 |
| 2'b01 | BUSY | Burst 중이지만 이번 cycle 은 전송 안 함 |
| 2'b10 | NONSEQ | Burst 의 첫 번째 전송 (또는 단독) |
| 2'b11 | SEQ | Burst 의 연속 전송 |

### 5.5 Burst 타입

| HBURST | 이름 | 동작 |
|--------|------|------|
| 3'b000 | SINGLE | 단일 전송 |
| 3'b001 | INCR | 무한 길이 증가 |
| 3'b010 | WRAP4 | 4-beat 래핑 |
| 3'b011 | INCR4 | 4-beat 증가 |
| 3'b100 | WRAP8 | 8-beat 래핑 |
| 3'b101 | INCR8 | 8-beat 증가 |
| 3'b110 | WRAP16 | 16-beat 래핑 |
| 3'b111 | INCR16 | 16-beat 증가 |

### 5.6 HRESP 2-Cycle 에러 응답 프로토콜

AHB 에러 응답은 APB 와 달리 **2 cycle** 이 필요하다. 이유: 파이프라인 때문에 Master 가 이미 다음 주소를 발행한 상태이므로, 에러를 알리면서 동시에 파이프라인을 안전하게 취소해야 한다.

```
HCLK:   ─┐ ┌─┐ ┌─┐ ┌─┐ ┌─┐ ┌─
          └─┘ └─┘ └─┘ └─┘ └─┘

HTRANS: ─┤NONSEQ├─┤  SEQ  ├─┤IDLE├─────────
HADDR:  ─┤  A1  ├─┤  A2  ├─┤ -- ├─────────

HREADY: ─────────┘         └─────┘    ┌────  ← Cycle1: HREADY=0 (stall)
                                       └────  ← Cycle2: HREADY=1 (완료)

HRESP:  ─┤OKAY├──┤ ERROR ├──┤ERROR├────────
                  ↑ Cycle 1   ↑ Cycle 2
                  HREADY=0    HREADY=1

동작 순서:
  Cycle 1: Slave가 HRESP=ERROR + HREADY=0 → Master에 에러 알림 + 파이프라인 스톨
           → Master는 이때 이미 발행한 A2 를 취소할 준비
  Cycle 2: Slave가 HRESP=ERROR + HREADY=1 → 에러 전송 완료
           → Master는 A2를 취소하고 IDLE로 전환 (또는 재시도)

왜 2 cycle인가?
  → 파이프라인 구조에서 1 cycle만으로 에러를 알리면
    Master가 이미 발행한 다음 주소(A2)를 처리할 시간이 없음.
    Cycle 1에서 HREADY=0으로 파이프라인을 멈추고,
    Cycle 2에서 에러를 확정하여 안전하게 복구.
```

### 5.7 WRAP Burst 주소 계산 — 상세 예제

WRAP burst 는 캐시 라인 로드에서 critical-word-first 를 구현할 때 사용된다.

```
설정: HBURST=WRAP4, HSIZE=Word(4byte), 시작 주소=0x0C

Step 1: Wrap Boundary 계산
  Wrap Size = Beat수 × Beat크기 = 4 × 4 = 16 bytes
  Wrap Boundary = 시작 주소를 Wrap Size로 정렬
  Lower Boundary = 0x0C & ~(16-1) = 0x0C & 0xFFFFFFF0 = 0x00
  Upper Boundary = Lower + Wrap Size = 0x00 + 0x10 = 0x10

Step 2: 주소 시퀀스
  Beat 0: 0x0C  (시작 — critical word)
  Beat 1: 0x0C + 4 = 0x10 → 경계(0x10) 도달 → Wrap → 0x00
  Beat 2: 0x00 + 4 = 0x04
  Beat 3: 0x04 + 4 = 0x08

  최종 순서: 0x0C → 0x00 → 0x04 → 0x08
  (0x00~0x0F 범위의 16바이트를 0x0C부터 순환하며 모두 읽음)

INCR4와 비교:
  INCR4: 0x0C → 0x10 → 0x14 → 0x18 (경계를 넘어감!)
  WRAP4: 0x0C → 0x00 → 0x04 → 0x08 (경계 내에서 순환)

다른 예: WRAP8, HSIZE=Word, 시작 주소=0x24
  Wrap Size = 8 × 4 = 32 bytes (0x20)
  Lower Boundary = 0x24 & ~(0x20-1) = 0x20
  Upper Boundary = 0x20 + 0x20 = 0x40
  순서: 0x24 → 0x28 → 0x2C → 0x30 → 0x34 → 0x38 → 0x3C → 0x20
                                                           ↑ Wrap!
```

### 5.8 HPROT (Protection Control)

| 비트 | 의미 |
|------|------|
| HPROT[0] | 0=Opcode fetch, 1=Data access |
| HPROT[1] | 0=User mode, 1=Privileged mode |
| HPROT[2] | 0=Non-bufferable, 1=Bufferable |
| HPROT[3] | 0=Non-cacheable, 1=Cacheable |

> APB4 의 PPROT 과 유사하지만 4비트. Interconnect 에서 접근 권한 필터링에 사용.

### 5.9 AHB DV 검증 포인트

| 항목 | 시나리오 |
|------|---------|
| 파이프라인 | 연속 전송에서 주소/데이터 정렬 정확 |
| Burst | INCR/WRAP 주소 계산 정확 |
| Wait State | HREADY=0 중 파이프라인 유지 (주소/데이터 변하지 않음) |
| Error | HRESP=ERROR 시 2-cycle 응답: Cycle1(HREADY=0)+Cycle2(HREADY=1) |
| IDLE/BUSY | Burst 중 BUSY 삽입 시 동작 |
| WRAP 경계 | Wrap 주소 계산이 경계에서 정확히 순환하는지 |

### 5.10 APB vs AHB 비교

| 항목 | APB | AHB |
|------|-----|-----|
| 복잡도 | 가장 단순 | 중간 |
| 파이프라인 | 없음 (2-phase) | 있음 (주소/데이터 겹침) |
| Burst | 없음 | INCR/WRAP 지원 |
| 최대 대역폭 | 낮음 | 중간 |
| Wait 메커니즘 | PREADY | HREADY |
| 용도 | 설정 레지스터 | DMA, 레거시 IP |
| SoC 위치 | 말단 Slave | Bridge 뒤 중간 |

### 5.11 Q&A — 핵심 질의응답

**Q: APB 가 왜 존재하는가? AHB 나 AXI 로 통일하면 안 되나?**
> "게이트 비용이다. APB 는 PSEL/PENABLE/PREADY 몇 개 신호로 동작하여 HW 면적이 극히 작다. 타이머, UART, GPIO 같은 저속 주변장치에 AXI 를 붙이면 인터페이스 로직이 IP 자체보다 클 수 있다. SoC 는 수십~수백 개의 레지스터 인터페이스가 있으므로 APB 의 면적 절약이 누적적으로 크다."

**Q: AHB 파이프라인의 주의점은?**
> "주소와 데이터가 1 cycle 차이로 겹치므로, HREADY=0(Wait State) 때 파이프라인 스톨이 발생한다. 이때 현재 주소와 이전 데이터가 모두 유지되어야 한다. DV 에서 가장 흔한 버그는 Wait State 중 데이터가 갱신되거나 주소가 바뀌는 경우이다."

**Q: AHB HRESP 에러가 왜 2 cycle 인가?**
> "AHB 파이프라인 구조 때문이다. Master 가 에러 응답을 받을 때 이미 다음 주소를 발행한 상태이므로, Cycle 1 에서 HREADY=0 으로 파이프라인을 멈추고 Master 에 에러를 알리고, Cycle 2 에서 HREADY=1 로 에러를 확정하며 Master 가 다음 주소를 취소할 시간을 준다. 1 cycle 만으로는 파이프라인에 이미 들어간 다음 전송을 안전하게 취소할 수 없다."

**Q: APB4 에서 PSTRB 이 추가된 이유는?**
> "APB3 까지는 byte 단위 쓰기가 불가능했다. 32-bit 레지스터의 특정 바이트만 수정하려면 Read-Modify-Write 가 필요했는데, 이는 원자성 문제 (status 레지스터의 W1C 비트 등) 와 성능 문제를 유발했다. PSTRB 으로 byte-level write 가 가능해져 이 문제가 해결되었다."

### 5.12 연습문제

#### 문제 1: AHB WRAP4 주소 계산

**문제**: AHB WRAP4 burst, HSIZE=Half-Word(2 byte), 시작 주소 0x06 일 때 4개 beat 의 주소 시퀀스를 구하라.

**사고 과정**:
1. Wrap Size 를 먼저 계산한다: Beat 수 × Beat 크기 = 4 × 2 = 8 bytes
2. Wrap Boundary 를 구한다: Lower = 0x06 & ~(8-1) = 0x06 & 0xF8 = 0x00, Upper = 0x08
3. 각 beat 에서 주소를 +2 하되, Upper Boundary (0x08) 도달 시 Lower (0x00) 로 wrap

**Dry Run**:
```
Beat 0: 0x06 (시작)
Beat 1: 0x06 + 2 = 0x08 → Upper(0x08) 도달 → Wrap → 0x00
Beat 2: 0x00 + 2 = 0x02
Beat 3: 0x02 + 2 = 0x04

답: 0x06 → 0x00 → 0x02 → 0x04
```

#### 문제 2: AHB 파이프라인 타이밍

**문제**: AHB Master 가 3 개 연속 Write (A1=0x00/D1, A2=0x04/D2, A3=0x08/D3) 를 수행하는데, A2 의 Data Phase 에서 Slave 가 HREADY=0 을 1 cycle 삽입한다. 각 cycle 에서 HADDR, HWDATA, HREADY 값을 추적하라.

**사고 과정**:
1. AHB 파이프라인에서 Address Phase 는 Data Phase 보다 1 cycle 앞선다
2. HREADY=0 이면 현재 cycle 이 연장되고, 모든 신호가 유지된다
3. Data Phase 의 stall 은 다음 Address Phase 도 함께 stall 시킨다

**Dry Run**:
```
Cycle  | HADDR | HWDATA | HREADY | 설명
-------|-------|--------|--------|----
  T1   |  A1   |   -    |   1    | A1 Address Phase
  T2   |  A2   |  D1    |   0    | A2 Addr + D1 Data → Slave가 HREADY=0 (stall)
  T3   |  A2   |  D1    |   1    | stall 유지: A2, D1 모두 변하지 않음!
  T4   |  A3   |  D2    |   1    | stall 해제 → A3 Addr + D2 Data
  T5   |  --   |  D3    |   1    | D3 Data Phase

핵심: T2→T3에서 HREADY=0이면 HADDR(A2)와 HWDATA(D1) 모두 유지.
이것을 틀리면(T3에서 A3로 바꾸면) → 가장 흔한 AHB 버그.
```

#### 퀴즈 (모듈 본문 연습용)

1. APB 에서 PREADY 가 항상 1 이면 모든 전송은 몇 cycle 에 완료되는가?
   <details><summary>정답</summary>2 cycle (Setup + Access). Wait state 없는 최소 전송 시간.</details>

2. AHB HRESP ERROR 가 1 cycle 이 아닌 2 cycle 인 이유를 한 문장으로 설명하라.
   <details><summary>정답</summary>파이프라인에 이미 진입한 다음 전송 (주소) 을 안전하게 취소할 시간이 필요하기 때문.</details>

3. APB4 의 PPROT[1]=1 이 의미하는 것은?
   <details><summary>정답</summary>Non-Secure access. TrustZone 에서 Secure 영역 접근이 차단되어야 하는 트랜잭션.</details>

4. AHB WRAP8, HSIZE=Word(4byte), 시작 주소 0x14 일 때 Wrap Boundary 의 Lower/Upper 는?
   <details><summary>정답</summary>Wrap Size = 8×4 = 32(0x20). Lower = 0x14 & ~0x1F = 0x00, Upper = 0x20.</details>

5. AHB-to-APB Bridge 에서 AHB INCR4 burst 는 APB 측에서 어떻게 처리되는가?
   <details><summary>정답</summary>4 개의 독립적인 APB 단일 전송으로 분해된다. APB 는 burst 를 지원하지 않으므로.</details>

---

## 6. 흔한 오해 와 DV 디버그 체크리스트

### 흔한 오해

!!! danger "❓ 오해 1 — 'AHB 가 APB 보다 항상 좋다'"
    **실제**: APB 는 register / 저속 peripheral 에 의도적으로 단순 — 게이트 비용 ↓, 검증 부담 ↓. AHB 의 파이프라인은 "고속 + DMA" 환경에서만 의미. 한 SoC 안에서 둘은 _공존_ 하며 각자 적합한 자리에 배치됩니다.<br>
    **왜 헷갈리는가**: "새 버전 = 항상 더 좋음" 의 직관 + APB / AHB 가 동시 등장한 역사적 맥락을 모르면 trade-off 가 안 보임.

!!! danger "❓ 오해 2 — 'PSEL 과 PENABLE 을 같은 cycle 에 올리면 빠르다'"
    **실제**: APB 는 SETUP 과 ACCESS 가 _반드시 분리된 cycle_ 입니다. 같은 cycle 에 둘 다 1 이면 slave 가 SETUP 단계를 못 인지 → 프로토콜 위반. 게다가 어차피 ACCESS phase 는 별도 cycle 이 필요해서 빨라지지도 않습니다.<br>
    **왜 헷갈리는가**: 두 신호 모두 master 가 발행하니 "묶어서 한 번에" 직관이 강함.

!!! danger "❓ 오해 3 — 'AHB Wait State 동안 Master 가 다음 주소를 미리 발행해도 된다'"
    **실제**: HREADY=0 이면 _현재 address phase 와 data phase 가 동시에 stall_ — Master 는 HADDR/HWDATA 모두 hold. 다음 주소를 미리 발행하면 receiver 가 어느 cycle 의 값을 latch 할지 미정의. 시뮬은 우연히 통과해도 실제 SoC 에서 random fail.<br>
    **왜 헷갈리는가**: 파이프라인이라는 단어가 "쉬지 않고 흐름" 을 연상시켜, stall 구간에도 next phase 가 진행 가능하다고 착각.

!!! danger "❓ 오해 4 — 'AHB ERROR 응답은 1 cycle 이면 충분'"
    **실제**: 파이프라인에 이미 진입한 다음 transaction 을 안전하게 취소하려면 _Cycle 1: HREADY=0+HRESP=ERROR_ → _Cycle 2: HREADY=1+HRESP=ERROR_ 의 2-cycle 시퀀스가 필수. 1-cycle 로 끝내면 master 가 다음 주소를 막을 시간이 없음.<br>
    **왜 헷갈리는가**: 단순 "에러는 한 신호로 알리면 끝" 이라는 직관.

!!! danger "❓ 오해 5 — 'APB 에서 PSTRB=4'b0 도 valid write'"
    **실제**: APB4 spec 상 PSTRB 가 모두 0 이면 _쓸 byte 가 없는_ write transaction. slave 구현에 따라 noop 으로 처리하거나 PSLVERR 로 거부할 수 있음 — 사내 IP 정책으로 명시 필요.<br>
    **왜 헷갈리는가**: "valid 신호가 1 이니 쓰기는 발생" 의 직관.

### DV 디버그 체크리스트

#### APB 디버그

| 증상 | 1차 의심 | 어디 보나 |
|---|---|---|
| Slave 가 register 를 못 잡는다 | SETUP/ACCESS phase 분리 안 됨 (동시 1) | PSEL, PENABLE 의 cycle 분리 — `PENABLE && !$past(PSEL)` 검사 |
| Random wrong-data | PREADY=0 wait state 중 PWDATA/PADDR 변경 | SVA: `(PSEL && !PREADY) |=> $stable(PADDR) && $stable(PWDATA)` |
| PSLVERR 무시되고 데이터 깨짐 | master 가 PSLVERR 미처리 | master FSM 의 error path |
| PSTRB=4'b0 transaction 이 silently 통과 | slave 가 strobe 검사 안 함 | RTL 의 byte-write enable 로직 |
| 연속 transaction 사이 1 cycle gap 발생 | FSM 이 IDLE 을 거쳐서 다음 SETUP | back-to-back 시 IDLE 우회 가능한 path |
| Read 시 PRDATA 가 wrong cycle 에 sample | PRDATA 가 PREADY=1 cycle 이전 valid 가정 | PRDATA 가 PREADY=1 인 cycle 에서만 valid 라는 spec 확인 |

#### AHB 디버그

| 증상 | 1차 의심 | 어디 보나 |
|---|---|---|
| HRDATA 가 잘못된 cycle 의 값 | data phase 와 address phase 매핑 1-cycle off | 해당 transaction 의 HADDR (이전 cycle) ↔ HRDATA (현재 cycle) 정렬 |
| Wait state 후 data 가 깨짐 | HREADY=0 중 HADDR/HWDATA 변경 | SVA: `(!HREADY) |=> $stable(HADDR) && $stable(HWDATA)` |
| ERROR 후 master 가 다음 transaction 을 막지 못함 | 1-cycle ERROR 응답 (2-cycle 미준수) | HRESP=ERROR 의 cycle 1 (HREADY=0) 검사 |
| Burst 끝나기 전 IDLE 진입 | BUSY → IDLE 잘못 천이 | HTRANS 시퀀스 추적 |
| WRAP burst 가 경계 안 감 | wrap_boundary 계산 오류 | 시작 주소와 wrap_size 로 lower/upper boundary 재계산 |
| HSIZE 와 byte alignment 어긋남 | HSIZE=word 인데 HADDR[1:0]≠0 | spec: `HADDR mod (1<<HSIZE) == 0` |

---

## 7. 핵심 정리 (Key Takeaways)

- **APB 는 단순함이 무기**: SETUP→ACCESS 2-phase, PSEL/PENABLE/PREADY 만으로 동작 → 게이트 비용 최소.
- **AHB 는 파이프라인**: 주소-데이터 1 cycle 차이. HREADY=0 시 stall — 모든 신호 유지가 핵심 (가장 흔한 버그가 stall 중 신호 변경).
- **AHB-to-APB Bridge**: AHB burst 를 APB 단일 전송 N 개로 분해. 면적과 성능의 trade-off.
- **버전 진화**: APB3 에서 PREADY/PSLVERR 정식화, APB4 에서 PSTRB(byte write)/PPROT, APB5 에서 PWAKEUP/xUSER.
- **DV pitfall**: AHB Wait State 중 HADDR/HWDATA 변경, APB SETUP 단계에서 PSEL=0, HRESP ERROR 1-cycle 처리.

!!! warning "실무 주의점 — APB ACCESS / AHB stall 중 신호 변경"
    **현상**: APB slave 가 PREADY=0 으로 wait state 를 유지하는 동안 master 가 PWDATA 또는 PADDR 을 바꾸거나, AHB master 가 HREADY=0 인 사이클에 HADDR/HWDATA 를 변경한다. 시뮬레이션은 통과하지만 실제 SoC 에서 random 하게 wrong-data 가 기록된다.

    **원인**: 두 프로토콜 모두 "transfer 완료 신호 (PREADY/HREADY) 가 1 이 될 때까지 모든 신호를 hold" 가 필수 invariant 다. master/slave 어느 쪽이든 wait state 동안 신호를 바꾸면 받는 쪽이 어느 사이클의 값을 sample 할지 정의되지 않는다.

    **점검 포인트**: SVA 로 `assert property (@(posedge PCLK) (PSEL && !PREADY) |=> $stable(PADDR) && $stable(PWDATA))` 같은 stable 속성 작성. 리뷰 시 RTL master 의 wait state handling 코드에서 register-update 가 PREADY/HREADY 조건과 묶여 있는지 확인.

### 7.1 자가 점검

!!! question "🤔 Q1 — APB vs AHB 선택 (Bloom: Apply)"
    32 개의 8-bit register 를 가진 control peripheral. APB / AHB 중?

    ??? success "정답"
        **APB**. 이유:
        - Register count 적음 (32 × 32-bit = 1 KB) → throughput 불필요.
        - Wait state 거의 없음 → 단순 2-phase 로 충분.
        - 면적/전력 절감 ★.

        AHB 는 _legacy memory_ 또는 _DMA target_ 처럼 매 cycle throughput 이 필요한 경우. Control register 에는 over-engineered.

!!! question "🤔 Q2 — SVA stable assertion (Bloom: Analyze)"
    AHB master 가 `HREADY=0` 인 사이클에 `HADDR` 을 _다른 값_ 으로 바꿈. _시뮬은 통과_ 했는데 실제 chip 에서 random data corruption. 왜?

    ??? success "정답"
        Slave 가 _어느 cycle_ 의 HADDR 을 sample 할지 _spec 정의 안 됨_:
        - Slave A: HREADY=0 첫 cycle 의 HADDR sample → 정상 동작.
        - Slave B: HREADY=1 마지막 cycle 의 HADDR sample → 변경된 (잘못된) HADDR.

        시뮬에서 _slave A 모델_ 이라 통과. 실제 chip 의 slave 가 _slave B_ 같으면 corruption. → **SVA `$stable(HADDR) until HREADY` 로 catch**.

### 7.2 출처

**Internal (Confluence)**
- 사내 AXI / AHB / APB 통합 가이드
- `[SIRH] SoC-infra Main Branch Release Note` (id=8159663)
- `HLS design practice in MangoBoost` (id=214663975)

**External**
- ARM, *AMBA APB Protocol Specification* (IHI 0024C)
- ARM, *AMBA AHB Protocol Specification* (IHI 0033B)
- *AXI Handshaking Rules* — ZipCPU blog (2021)

---

## 다음 단계

- 📝 [**Module 01 퀴즈**](quiz/01_apb_ahb_quiz.md) — 5 문항으로 이해도 점검
- ➡️ [**Module 02 — AXI**](02_axi.md) — 5 채널 / Burst / Outstanding 의 핵심

<div class="chapter-nav">
  <a class="nav-prev" href="../">
    <div class="nav-label">◀ 이전</div>
    <div class="nav-title">코스 홈</div>
  </a>
  <a class="nav-next" href="../02_axi/">
    <div class="nav-label">다음 ▶</div>
    <div class="nav-title">AXI (Advanced eXtensible Interface)</div>
  </a>
</div>


--8<-- "abbreviations.md"
--8<-- "_inc/topic_abbr.md"
