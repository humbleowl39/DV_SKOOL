# Module 01 — DRAM Fundamentals + DDR4/5

<!-- DV-SKOOL-CH-CTX:start -->
<div class="chapter-context" data-cat="memory">
  <a class="chapter-back" href="../">
    <span class="chapter-back-arrow">←</span>
    <span class="chapter-back-icon">💾</span>
    <span class="chapter-back-text">DRAM / DDR</span>
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
  <a class="page-toc-link" href="#3-작은-예-row-conflict-한-번을-사이클-단위로-따라가기">3. 작은 예 — Row Conflict 사이클 추적</a>
  <a class="page-toc-link" href="#4-일반화-주소-계층-명령-시퀀스-세대간-진화">4. 일반화 — 주소 계층 + 명령 + 세대</a>
  <a class="page-toc-link" href="#5-디테일-셀-prefetch-bank-group-mode-register-confluence">5. 디테일</a>
  <a class="page-toc-link" href="#6-흔한-오해-와-dv-디버그-체크리스트">6. 흔한 오해 + DV 디버그 체크리스트</a>
  <a class="page-toc-link" href="#7-핵심-정리-key-takeaways">7. 핵심 정리</a>
</div>
<!-- DV-SKOOL-CH-TOC:end -->

!!! objective "학습 목표"
    이 모듈을 마치면:

    - **Diagram** DRAM cell의 capacitor 동작 + Bank/Row/Column 계층 + sense amplifier 흐름을 그릴 수 있다.
    - **Trace** ACT → RD/WR → PRE → REF의 전체 명령 시퀀스와 각 단계의 timing parameter를 추적할 수 있다.
    - **Distinguish** DDR4와 DDR5의 핵심 차이(2-channel split, on-die ECC, refresh 모드, prefetch)를 식별할 수 있다.
    - **Apply** Burst length, prefetch, bank group 개념을 throughput 계산에 적용할 수 있다.
    - **Justify** Open-page 와 Close-page 정책의 trade-off 를 workload 패턴으로 설명할 수 있다.

!!! info "사전 지식"
    - 디지털 회로 기본 (synchronous logic, FIFO)
    - 캐시 / 메모리 계층 일반 지식
    - PVT (Process / Voltage / Temperature) 변동 개념

---

## 1. Why care? — 이 모듈이 왜 필요한가

### 1.1 시나리오 — 왜 _SRAM 처럼_ 안 만들었나?

당신은 CPU 와 메모리 설계자. SRAM (캐시) 은 _1 cycle_ 에 read/write. DRAM 은 _수십 cycle_ + 복잡한 timing. 왜?

**SRAM cell**: 6 transistor flip-flop. 영구 저장 (전원 켜진 동안). 빠름. **면적 크다**.

**DRAM cell**: 1 transistor + 1 capacitor. _capacitor_ 에 charge 로 저장. **면적 1/6**. 단:
- **Capacitor 누설**: 시간 지나면 data 사라짐 → _refresh 필요_.
- **Destructive read**: 한 번 읽으면 _data 파괴_ → _restore 필요_.
- **Sense amplifier 시간**: capacitor 의 미세 전하 감지에 시간 필요 → _tRCD_.

**Trade-off**:
| 항목 | SRAM | DRAM |
|------|------|------|
| 면적 | 1 (baseline) | 1/6 |
| Latency | 1 cycle | 수십 cycle |
| Refresh | 불필요 | 필수 |
| 비용/bit | 6× | 1× |

**결과**: SRAM 으로는 _GB 단위_ 메모리 _경제적으로_ 불가능. DRAM 이 _수십 cycle latency_ 라는 _대가로_ _대용량_ 가능. 그래서 CPU 는 _SRAM 캐시 + DRAM main memory_ 의 hybrid.

이후 모든 DRAM/DDR 모듈은 한 가정에서 출발합니다 — **"DRAM cell 은 capacitor 이므로 데이터가 시간에 따라 누설되고, 외부에서 한 번 읽으면 파괴되며, 따라서 모든 access 는 row open → column access → row close 라는 stateful 시퀀스를 거친다"**. Memory Controller (MC) 가 왜 그렇게 복잡한 스케줄러를 갖는지, PHY 가 왜 nano-second margin 을 보정해야 하는지, DV TB 가 왜 timing SVA 수십 개를 동시에 보는지 — 전부 이 한 가정의 파생입니다.

이 모듈을 건너뛰면 이후의 모든 timing parameter / refresh 정책 / training 시퀀스 결정이 "그냥 외워야 하는 숫자" 로 보입니다. 반대로 capacitor → destructive read → restore → refresh 의 인과를 정확히 잡고 나면, tRCD / tRP / tRAS / tFAW 가 만나는 모든 디테일에서 _이유_ 가 보입니다.

!!! question "🤔 잠깐 — Row buffer 의 _hit/miss_ 의 비용 차이?"
    Same row 또 access (hit) vs 다른 row access (miss). 시간 비용?

    ??? success "정답"
        - **Row hit**: 이미 _open_ 된 row buffer 에서 column access — _~1 cycle_ (~tCL = 14 cycle).
        - **Row miss (conflict)**: 현재 row close (`PRE`, ~tRP=14) → 새 row open (`ACT`, ~tRCD=14) → column access (~tCL=14). **~42 cycle**.

        **3× 차이**. 그래서 _row buffer locality_ 가 메모리 성능의 _가장 큰 결정 인자_.

        Memory controller 의 _스케줄러_ 가 이걸 활용: _같은 row 의 access 모으기_ (FR-FCFS — First Ready First Come First Served).

---

## 2. Intuition — 비유와 한 장 그림

!!! tip "💡 한 줄 비유"
    **DRAM Bank** ≈ **은행 창구 (한 번에 한 손님만)**.<br>
    한 bank 에 access 중이면 다른 access 는 대기. 여러 bank 가 있으면 동시에 진행 가능 → **Bank-level parallelism**. **Row buffer** 는 창구 책상 위에 펼쳐 둔 서류 — 펴는 데(`ACT`) 시간이 걸리고, 다른 서류를 보려면 먼저 치워야(`PRE`) 한다. 책상 위 서류와 같은 손님(같은 row)이 또 오면 즉시 응대(Row Hit) — 가장 빠름.

### 한 장 그림 — DRAM access 의 세 가지 결말

```d2
direction: down

# unparsed: REQ["요청 도착<br/>(Bank N, Row R)"]
# unparsed: BANK["Bank N<br/>Row Buffer = 현재 open 된 Row (예: Row 5)"]
REQ -> BANK
HIT: "① R == open Row\n**Row HIT**\ntCL 만 기다리면 데이터 나감\n★ 가장 빠름" { style.stroke-width: 3 }
BANK -> HIT
MISS: "② open Row 없음\n**Row MISS**\nACT(tRCD) → RD(tCL)"
BANK -> MISS
CONF: "③ 다른 R 이 open\n**Row CONFLICT**\nPRE(tRP) → ACT(tRCD) → RD(tCL)\n★ 가장 느림" { style.stroke-width: 3; style.stroke-dash: 4 }
BANK -> CONF
```

### 왜 이렇게 설계됐는가 — Design rationale

DRAM cell 은 1T1C — 트랜지스터 하나 + capacitor 하나. 이 단순함이 면적당 bit 밀도를 SRAM 의 ~10× 로 만들어 GB 급 메모리를 가능케 했습니다. 그러나 capacitor 는 **누설** 됩니다. 그래서 (1) **주기적 refresh** 가 필수이고, (2) read 가 capacitor 전하를 sense amplifier 로 끌어내는 순간 **파괴(destructive)** 되므로 즉시 재기록(restore) 이 일어나야 합니다.

이 두 제약에서 **"row 단위로 한 번에 sense → 같은 row 안에서 column 만 옮기며 access → 다른 row 가 필요하면 닫고(precharge) 다시 연다"** 는 stateful access 패턴이 도출됩니다. timing parameter (tRCD/tRP/tRAS/tRFC/tFAW) 는 모두 이 capacitor 물리에서 나오는 최소 보장 시간이고, MC 의 모든 최적화는 결국 "Row Hit 비율을 높이고, capacitor 충전 시간 동안 다른 bank 를 일하게 하는" 두 축으로 수렴합니다.

---

## 3. 작은 예 — Row Conflict 한 번을 사이클 단위로 따라가기

가장 단순한 시나리오. 같은 Bank 에 **현재 Row 5 가 열려 있는 상태** 에서, MC 가 **Row 9 의 Column 0** 을 Read 하려 합니다 (DDR4-3200 기준).

```
        T0 ─── T22 ─── T44 ─── T66 ── T88
   CMD: PRE     ACT     RD      ─       (data out @ T66)
        │       │       │       │
        ▼       ▼       ▼       ▼
   Bank │←tRP=22→│←tRCD=22→│←tCL=22→│
   상태 │ closing │ Row 9   │ R col=0│  → 데이터 → DQ
        │         │ 로딩    │ access │
        │         │ (sense) │        │
        ▼         ▼         ▼        ▼
   Row5 (open) → Idle → Row9 row-buf → 데이터 transfer
   ─ 누가 ─    ─ 무엇을 ─                      ─ 왜 ─
```

| Step | 사이클 | 누가 | 무엇을 | 왜 |
|---|---|---|---|---|
| ① | `T0`        | MC | `PRE` 명령 (Bank N) 발행 | 현재 열린 Row 5 의 sense amp 데이터를 cell 에 restore + bit-line precharge |
| ② | `T0..T22`   | DRAM | sense amp → cell write-back, bit-line 을 VDD/2 로 |  capacitor 가 "써지고" 다음 sense 를 위한 중립 전압 준비 — `tRP` 동안 다른 명령 금지 |
| ③ | `T22`       | MC | `ACT` (Bank N, Row 9) 발행 | Row 9 의 word-line 활성화 → cell 의 작은 전하가 bit-line 으로 |
| ④ | `T22..T44`  | DRAM | sense amplifier 가 mV-level 차이를 0/1 로 증폭 | sense 결과가 Row Buffer 에 자리잡기까지 — `tRCD` |
| ⑤ | `T44`       | MC | `RD` (col=0, BL=8) 발행 | Row Buffer 에서 Column 선택 → DQ 로 보낼 준비 |
| ⑥ | `T44..T66`  | DRAM | column mux → I/O gating → DQ pad | column 선택부터 DQ 가 valid 까지 — `tCL` (CAS Latency) |
| ⑦ | `T66..T70`  | DQ pin | 8-beat (BL8) burst 출력 | prefetch 8n 이라 1번 column access 로 8 비트가 나옴 — DDR 클럭 4 사이클 |
| ⑧ | `T22..T74`  | DRAM | Row 9 는 `tRAS` (≥52 cycle) 동안 open 유지 | Row 가 stable 해질 때까지 PRE 금지 |

```c
// MC scheduler 의 의사 코드 — 이 1 사이클이 어떻게 만들어지는가
if (req.bank.open_row != req.row) {
    if (req.bank.open_row != INVALID) {
        issue(PRE, req.bank);                   // ① Row Conflict
        wait(tRP);                               // ②
    }
    issue(ACT, req.bank, req.row);              // ③ Row open
    wait(tRCD);                                  // ④
}
issue(RD, req.bank, req.col);                   // ⑤ Column access
wait(tCL);                                       // ⑥
return BL_data;                                  // ⑦
// (tRAS 보장은 PRE 발행 시점 검사로 처리)
```

!!! note "여기서 잡아야 할 두 가지"
    **(1) 한 read 는 단일 cycle 이 아니라 PRE→ACT→RD 의 직렬 sequence 다.** Row Conflict 라면 `tRP+tRCD+tCL` (DDR4-3200 기준 66 cycle ≈ 41 ns) 가 _그 한 read_ 에 직렬로 누적됨. 이게 MC 가 Row Hit 를 그토록 추구하는 이유.<br>
    **(2) 같은 bank 에서는 직렬, 다른 bank 끼리는 병렬.** Row Conflict 동안 Bank N 은 묶여 있지만 Bank N+1 은 완전히 독립적으로 ACT/RD 를 진행 가능 — 이것이 **Bank-level Parallelism** 이고 MC scheduler 가 다음 모듈에서 본격적으로 활용할 자원입니다.

---

## 4. 일반화 — 주소 계층, 명령 시퀀스, 세대간 진화

### 4.1 DRAM 주소 계층

```d2
direction: down

DRAM: "DRAM Device"
R0: "Rank 0"
R1: "Rank 1"
BG0: "BG0"
BG1: "BG1"
BG2: "BG2"
BG3: "BG3"
B0: "Bank 0"
B1: "Bank 1"
B2: "Bank 2"
B3: "Bank 3"
ROW: "Row 0 .. Row 65535"
COL: "Column 0 .. Column 1023"
DRAM -> R0
DRAM -> R1
R0 -> BG0
R0 -> BG1
R0 -> BG2
R0 -> BG3
BG0 -> B0
BG0 -> B1
BG0 -> B2
BG0 -> B3
B0 -> ROW
ROW -> COL
```

DDR4 예시 (8Gb): 2 Rank · 4 Bank Group · 4 Bank/Group (총 16 Bank) · 65536 Row/Bank · 1024 Column/Row.

접근 시퀀스:

1. **ACTIVATE (ACT)**: Row를 Row Buffer에 로드 (Row Open)
2. **READ/WRITE (RD/WR)**: Column 주소로 데이터 접근
3. **PRECHARGE (PRE)**: Row Buffer 닫기 (다른 Row 접근 전)

### 4.2 Row Hit / Miss / Conflict — 일반화

§3 의 Row Conflict 는 세 가능한 결말 중 하나입니다.

```
Row Hit:    같은 Row가 이미 열려 있음 → ACT 불필요 → tCL 만   ← 가장 빠름
Row Miss:   Row Buffer 비어있음        → ACT 필요   → tRCD + tCL
Row Conflict: 다른 Row가 열려 있음     → PRE + ACT  → tRP + tRCD + tCL  ← 가장 느림

→ Memory Controller의 핵심 목표: Row Hit 비율 극대화
→ 이를 위해 Module 02 의 FR-FCFS, Open/Close page, Address Mapping 이 등장
```

### 4.3 명령 FSM — Bank 별 상태 머신

```d2
direction: right

INITIAL { shape: circle; style.fill: "#333" }
INITIAL -> POWERUP
POWERUP -> IDLE: "MRS / ZQ / Init"
IDLE -> ACTIVE: "ACT (tRCD)"
ACTIVE -> ACTIVE: "RD / WR\n(tCL / tCWL,\ntCCD 간격)"
ACTIVE -> IDLE: "PRE (tRP)\ntRAS 만족 후"
IDLE -> IDLE: "REF (tRFC)\n모든 bank IDLE"
# unparsed: note right of IDLE: precharged
# unparsed: note right of ACTIVE: row open
```

### 4.4 DDR4 vs DDR5 — 무엇이 바뀌었나

| 측면 | DDR4 (`3200`) | DDR5 (`4800`) | 핵심 변경 동기 |
|------|------|------|------|
| 채널 | 1 × 64-bit | **2 × 32-bit** sub-channel | 명령 병렬성 2× |
| Bank Group | 4 | **8** | tCCD_S 활용 기회 증가 |
| Bank/BG | 4 | 4 (총 32 Bank) | Bank-level parallelism 2× |
| Prefetch | 8n | **16n** | I/O 속도 ↑ 흡수 |
| Burst Length | BL8 | **BL16** (BC8 옵션) | prefetch 비례 |
| ECC | 외부 (72-bit DIMM) | **On-die ECC** 내장 | 셀 미세화로 1-bit 에러 ↑ |
| Refresh | All-bank | **Same-bank Refresh** 옵션 | refresh-induced stall ↓ |
| CMD bus | RAS#/CAS#/WE# 개별 | **CA[13:0]** 멀티플렉싱 | 핀 수 절감, 확장성 |
| 전압 (VDD) | 1.2V | 1.1V | 전력 ↓ |

### 4.5 Prefetch + Bank Group 의 결합 — 대역폭의 두 축

```d2
direction: down

CELL: "내부 cell 어레이\n(느림, ~수백 MHz)"
BUF: "Row Buffer / I/O sense"
DQ: "DQ pin\n(빠름, 수 GHz)"
CELL -> BUF: "① Prefetch n bit (BL = n)"
BUF -> DQ: "② Bank Group 별 독립 I/O\n같은 BG: tCCD_L (느림)\n다른 BG: tCCD_S (빠름)"
```

- 한 번의 column access 가 BL beat 의 데이터 전송으로 변환되고,
- MC scheduler 가 연속 access 를 다른 BG 로 분산하면 tCCD_S 로 이어붙임.
- 두 layer 의 곱 = peak bandwidth 효율.

---

## 5. 디테일 — 셀, Prefetch, Bank Group, Mode Register, Confluence

### 5.1 DRAM 셀 동작

```
1T1C (1 Transistor, 1 Capacitor):

  Word Line (Row 선택)
       |
       +--[Transistor Gate]
       |
  Bit Line ----+---- [Capacitor] ---- GND
  (Column)     |
               저장된 전하 = 0 또는 1

  읽기:
    1. Word Line 활성화 → Transistor ON
    2. Capacitor 전하가 Bit Line으로 흘러나옴
    3. Sense Amplifier가 미세한 전압 차이 감지 → 0/1 판정
    4. 읽기는 파괴적(Destructive Read) → 자동 재쓰기(Restore) 필요

  쓰기:
    1. Word Line 활성화
    2. Bit Line에 원하는 전압 인가
    3. Capacitor 충전/방전

  Refresh:
    커패시터 전하가 시간이 지나면 누설 → 주기적으로 읽고 재쓰기
    DDR4: 64ms 주기 (tREFI = ~7.8μs)
    DDR5: 32ms 주기 (온도에 따라 변동)
```

### 5.2 DDR 세대별 비교 — full table

| 항목 | DDR4 | DDR5 | LPDDR5 |
|------|------|------|--------|
| 속도 | 1600~3200 MT/s | 3200~8800 MT/s | 6400~8533 MT/s |
| 전압 | 1.2V | 1.1V | 1.05V (0.5V core) |
| Prefetch | 8n | **16n** | 16n |
| Bank Group | 4 | **8** | 4~8 |
| Bank/BG | 4 | 4 (총 **32** Bank) | 4~8 |
| Burst Length | 8 | **16** | 16/32 |
| Channel | 1 × 64-bit | **2 × 32-bit** (sub-channel) | 2 × 16-bit |
| ECC | 외부 (72-bit DIMM) | **On-die ECC** 내장 | On-die ECC |
| Refresh | 64ms 전체 | **Same Bank Refresh** 지원 | Per-bank |
| 전력 관리 | CKE | CKE + **LPDDR 스타일 PD** | 다양한 저전력 모드 |
| 용도 | 서버, PC | 차세대 서버/PC | 모바일, 차량 |

### 5.3 DDR5 의 핵심 변경점 — 상세

```
1. 듀얼 Sub-Channel (2 × 32-bit)
   DDR4: 1 × 64-bit 채널 → 한 번에 64-bit 접근
   DDR5: 2 × 32-bit 독립 채널 → 각각 독립 명령 → 효율 향상

   +----------+----------+
   | Sub-Ch A | Sub-Ch B |
   |  32-bit  |  32-bit  |
   | 독립 명령| 독립 명령|
   +----------+----------+

   왜 효율적인가?
   - DDR4: 64-bit 중 32-bit만 필요해도 전체 채널 점유
   - DDR5: Sub-Ch A가 CPU 요청 처리하는 동안 Sub-Ch B는 GPU 요청 처리 가능
   - 각 Sub-Channel이 독립 Activate/Read/Write 명령 발행 → 명령 병렬성 2배

2. Bank Group 증가 (4 → 8)
   → Bank Group 간 접근 시 tCCD_S(짧은 CAS-to-CAS) 적용
   → 인터리빙 효율 향상

3. On-die ECC
   DDR4: 외부 ECC DIMM 필요 (72-bit 버스)
   DDR5: DRAM 칩 내부에서 단일 비트 에러 자동 수정
   → 외부에서 관찰 불가 (투명), 신뢰성 향상
   주의: On-die ECC는 128-bit 워드 내 1-bit 수정만 가능
         Multi-bit 에러 → 외부 ECC(SECDED)가 여전히 필요

4. Same Bank Refresh
   DDR4: All-bank Refresh → Refresh 중 전체 접근 불가
   DDR5: Same Bank Refresh → 다른 Bank 접근 가능 → 성능 향상

5. Command/Address 버스 변경
   DDR4: RAS#, CAS#, WE# (개별 핀)
   DDR5: CA[13:0] (멀티플렉싱) → 핀 수 절감, 미래 확장 용이
```

### 5.4 Prefetch 아키텍처 — DDR 대역폭의 핵심

```
Prefetch = DRAM 내부에서 한 번에 읽어오는 비트 수

문제: DRAM 셀 어레이는 느리다 (내부 클럭 ≈ 수백 MHz)
     하지만 I/O 핀은 빠르다 (DDR5: 4800 MHz 이상)
     → 내부와 외부의 속도 차이를 어떻게 해결?

해결: Prefetch로 내부에서 여러 비트를 한꺼번에 읽고,
     외부 I/O에서 빠른 클럭으로 순차 전송

  DDR4 (8n Prefetch):
    내부: 1회 접근으로 8비트 동시 읽기 (per DQ pin)
    외부: 8비트를 DDR 클럭의 4사이클(상승+하강 × 4)로 전송
    → Burst Length = 8 (BL8)

  DDR5 (16n Prefetch):
    내부: 1회 접근으로 16비트 동시 읽기 (per DQ pin)
    외부: 16비트를 DDR 클럭의 8사이클(상승+하강 × 8)로 전송
    → Burst Length = 16 (BL16)

  시각화 (DDR4, 1 DQ pin):
    DRAM 내부: [b0 b1 b2 b3 b4 b5 b6 b7] ← 8bit 동시 읽기
                         ↓ Serialization
    DQ pin:    b0 b1 b2 b3 b4 b5 b6 b7   ← DDR 클럭 4 사이클

  DDR5 전체 대역폭 계산 (4800 MT/s):
    4800 MT/s × 32-bit(Sub-Ch) × 2(Sub-Ch) = 38.4 GB/s (per channel)

핵심: Prefetch가 클수록 → Burst 길이 증가 → 순차 접근 대역폭 향상
     하지만 작은 데이터(< BL)만 필요할 때도 전체 Burst 전송 → 비효율
     → DDR5는 BL16 외에 BL8도 지원 (Burst Chop)
```

### 5.5 Bank Group — 왜 존재하는가?

```
핵심 질문: Bank만 있으면 되지, 왜 Bank Group이라는 계층이 필요한가?

답: DRAM I/O 회로의 물리적 공유 때문

  같은 Bank Group 내 Bank들은 I/O 센스 앰프와 데이터 경로를 공유한다.
  → 같은 BG 내에서 연속 CAS 명령: 공유 회로 재사용 대기 → tCCD_L (긴 간격)
  → 다른 BG 간 연속 CAS 명령: 독립 회로 사용 → tCCD_S (짧은 간격)

  예시 (DDR4-3200):
    같은 BG:  RD(BG0:B0) ──[tCCD_L=8]── RD(BG0:B1)   ← 느림
    다른 BG:  RD(BG0:B0) ──[tCCD_S=4]── RD(BG1:B0)   ← 빠름 (2배)

  DDR4: 4 BG × 4 Bank = 16 Bank
  DDR5: 8 BG × 4 Bank = 32 Bank
  → DDR5는 BG가 2배 → tCCD_S 활용 기회 증가 → 인터리빙 효율 향상

  MC 스케줄러 관점:
    연속 접근을 다른 BG로 분산시키면 tCCD_S로 처리 가능
    → Address Mapping에서 연속 주소가 다른 BG로 매핑되도록 설계
    → 이것이 "Bank Group Interleaving"의 핵심 원리
```

### 5.6 DRAM 타이밍 파라미터 핵심

| 파라미터 | 의미 | DDR4 (3200) | DDR5 (4800) |
|---------|------|------------|------------|
| **tCL** | CAS Latency (RD→데이터 출력) | 22 | 34 |
| **tRCD** | ACT→RD/WR (Row to Column Delay) | 22 | 34 |
| **tRP** | PRE→ACT (Row Precharge) | 22 | 34 |
| **tRAS** | ACT→PRE (Active to Precharge) | 52 | 52 |
| **tRC** | ACT→ACT (같은 Bank) = tRAS + tRP | 74 | 86 |
| **tRFC** | Refresh→ACT (Refresh Cycle) | 350ns | 295ns |
| **tREFI** | Refresh Interval | 7.8μs | 3.9μs |
| **tCCD_S** | CAS→CAS (다른 BG) | 4 | 4 |
| **tCCD_L** | CAS→CAS (같은 BG) | 8 | 8 |
| **tFAW** | Four Activate Window | 30ns | 제거(tRRD만) |

**면접 포인트**: tCL, tRCD, tRP가 "CAS Latency 22-22-22"처럼 스펙에 표기되는 세 수치이다. 이 값이 클수록 느리지만, 클럭이 빠르면 절대 시간(ns)은 유사하다.

### 5.7 LPDDR5 특징 (모바일/SoC)

```
LPDDR5 vs DDR5 차이:

  | 항목      | DDR5        | LPDDR5          | LPDDR5X         |
  |----------|------------|-----------------|-----------------|
  | 전압     | 1.1V       | 1.05V (0.5V core)| 1.05V           |
  | 채널     | 2×32-bit   | 2×16-bit        | 2×16-bit        |
  | 버스 폭  | 64-bit     | 32-bit (×2 ch)  | 32-bit (×2 ch)  |
  | 최대 속도| 8800 MT/s  | 6400 MT/s       | 8533 MT/s       |
  | 패키지   | DIMM       | PoP / 패키지    | PoP / 패키지    |
  | 전력 관리| 기본       | 다양한 저전력   | 더욱 강화       |
  | 용도     | 서버, PC   | 모바일 SoC      | 플래그십 모바일 |
```

#### LPDDR5 고유 핵심 기능

```
1. WCK (Write Clock) — LPDDR5의 가장 큰 구조적 차이
   DDR5: CK(클럭) 하나로 명령 + 데이터 모두 동기화
   LPDDR5: CK(명령용) + WCK(데이터용) 분리

   CK:  저속 (명령/주소 전송)
   WCK: 고속 (DQ 데이터 전송, CK의 2배 또는 4배)

   왜 분리하는가?
   - 명령 버스는 상대적으로 저속으로 충분
   - 데이터 버스만 고속으로 돌려 전력 절감
   - WCK:CK 비율: 2:1 (기본) 또는 4:1 (고속 모드)

   +---+   +---+   +---+   CK  (명령 동기화)
   |   |   |   |   |   |
   +   +---+   +---+   +---

   +-+-+-+-+-+-+-+-+-+-+-+  WCK (데이터 동기화, 2× 속도)
   | | | | | | | | | | | |
   +-+-+-+-+-+-+-+-+-+-+-+

2. DVFSC (Dynamic Voltage and Frequency Scaling Clock)
   - 런타임에 동적으로 클럭 주파수와 전압을 변경
   - 고부하: 최대 속도 → 고성능
   - 저부하: 낮은 속도 → 저전력
   - MC가 트래픽 양을 모니터링하여 자동 전환

   전환 단계 예시:
     F0 (최고 성능) → F1 (절전) → F2 (깊은 절전)
     각 단계에서 WCK:CK 비율과 전압이 함께 조정

3. DSC (Data-copy and Data-Scramble/Compression)
   - 데이터 복사: DRAM 내부에서 Row 간 데이터 복사
     → MC/CPU 개입 없이 DRAM 자체적으로 수행
     → 메모리 복사 오퍼레이션의 대역폭 절감
   - 데이터 스크램블: 전기적 간섭 감소 목적

4. 저전력 모드 (DDR5 대비 훨씬 다양)
   - Deep Sleep: CK 정지, Self-Refresh 유지
   - Partial Array Self-Refresh (PASR): 사용 중인 Bank만 Refresh
     → 미사용 Bank는 Refresh 생략 → 대폭 전력 절감
   - Per-bank Refresh: Bank 단위 Refresh (DDR5의 Same-bank과 유사)
```

#### Samsung SoC 에서의 LPDDR5

```
Samsung SoC에서의 LPDDR5:
  - AP(CPU) + LPDDR5 PoP (Package on Package)
  - Memory Controller가 AP 내부에 통합
  - BootROM → BL2(DRAM Training) → OS
    BL2가 DRAM 초기화(Training)를 수행하는 이유:
    → Training은 복잡하고 PVT(공정/전압/온도)에 의존
    → BootROM에 넣기엔 코드가 너무 크고 변경이 필요

  LPDDR5 Training 특이사항:
    - WCK2CK Training: WCK와 CK 간 위상 정렬 (DDR5에 없는 항목)
    - CBT (Command Bus Training): CA 핀 타이밍 정렬
    - DVFSC 전환 시 재Training 또는 저장된 값 복원 필요
```

### 5.8 DBI (Data Bus Inversion) — 전력 절감 기법

```
문제: 고속 데이터 전송 시 DQ 핀의 전환(0→1, 1→0)이 많으면
     → 스위칭 전류 증가 → 전력 소모 + SSN(동시 스위칭 노이즈) 증가

DBI 원리:
  전송할 8-bit 데이터에서 '1'이 5개 이상이면 비트를 반전시켜 전송
  → 항상 '1'의 수를 4개 이하로 유지 → 스위칭 횟수 감소

  예시:
    원본:    11110111 (1이 7개 → 스위칭 많음)
    DBI 적용: 00001000 (1이 1개) + DBI# = 0 (반전 표시)
    수신측:   DBI# = 0이면 비트 반전하여 원본 복원

  DBI 모드:
    DC-DBI: '1'의 개수 최소화 (위 예시) → 전력 절감
    AC-DBI: 이전 데이터 대비 전환 횟수 최소화 → SSN 감소

  DDR4: DBI 선택적 (DM/DBI# 핀 공유)
  DDR5: DBI 기본 활성화 (DC-DBI for Write, AC-DBI for Read)
  LPDDR5: DBI 기본 활성화

핵심: DBI는 "공짜" 전력 절감 — 추가 핀 1개(DBI#)로 ~15% 전력 감소
```

### 5.9 Mode Register — DRAM 설정의 핵심

```
Mode Register = DRAM 디바이스의 동작 모드를 설정하는 내부 레지스터

MRS (Mode Register Set) 명령으로 읽기/쓰기:
  MC가 초기화 시 MRS 명령으로 DRAM의 동작 모드를 프로그래밍

DDR4 Mode Register (MR0~MR6):
  MR0: Burst Length, CAS Latency (CL)
  MR1: DLL Enable, Output Driver Impedance, RTT_NOM (ODT)
  MR2: CAS Write Latency (CWL), RTT_WR
  MR3: MPR (Multi-Purpose Register), Fine Granularity Refresh
  MR4: Temperature Sensor, VREF Monitor
  MR5: RTT_PARK, CA Parity, Data Mask
  MR6: VREF Training, tCCD_L

DDR5 Mode Register (MR0~MR63+, 크게 확장):
  MR0: Burst Length, CL
  MR2: Read/Write Preamble
  MR8: Read Preamble Training
  MR12~MR14: DCA (Duty Cycle Adjuster)
  MR37: ODTL (ODT Latency)
  ...기타 다수

  DDR5 변경점:
  - MR 수가 대폭 증가 (7개 → 64개+)
  - 개별 MR이 더 세분화된 제어 제공
  - Per-DRAM Addressability: 개별 칩에 독립 MRS 가능

면접 포인트:
  - "MRS로 DRAM의 CL, CWL, ODT, VREF 등을 프로그래밍한다"
  - "초기화 시퀀스에서 MRS 설정 순서가 중요 — JEDEC 스펙에 정의"
  - "Training 결과(VREF 값 등)도 MRS로 DRAM에 반영"
```

### 5.10 Q&A — 자주 묻는 질문

**Q: DDR5가 DDR4보다 빠른 핵심 이유는?**
> "세 가지: (1) 듀얼 Sub-Channel — 64-bit 단일 채널 대신 2×32-bit 독립 채널로 명령 병렬성 향상. (2) Bank Group 증가(4→8) — 인터리빙 효율이 높아져 대역폭 활용도 증가. (3) Prefetch 16n — Burst Length가 8→16으로 증가하여 한 번의 접근으로 더 많은 데이터 전송. 다만 CAS Latency(절대 ns)는 유사하므로 랜덤 접근 지연은 크게 개선되지 않는다."

**Q: Row Hit/Miss/Conflict의 성능 차이는?**
> "Row Hit은 이미 열린 Row에 접근하므로 tCL만 필요(가장 빠름). Row Miss는 빈 Row Buffer에 새 Row를 여는 tRCD가 추가. Row Conflict는 열린 Row를 닫는 tRP + 새 Row를 여는 tRCD가 모두 필요(가장 느림). Memory Controller의 핵심 목표는 Row Hit 비율을 극대화하는 스케줄링이다."

**Q: On-die ECC란?**
> "DDR5부터 DRAM 칩 내부에서 단일 비트 에러를 자동 수정하는 기능이다. 외부(MC/호스트)에서는 이 ECC 동작이 투명하다. DDR4에서는 ECC를 위해 72-bit DIMM(64 data + 8 ECC)이 필요했지만, DDR5는 On-die ECC가 기본 포함되어 별도 ECC DIMM 없이도 기본적인 에러 보호가 가능하다. 단, On-die ECC는 128-bit 워드 내 1-bit만 수정하므로, 서버 환경에서는 여전히 외부 SECDED ECC가 필요하다."

**Q: Prefetch 아키텍처란? DDR5에서 왜 16n인가?**
> "DRAM 내부 셀 어레이는 수백 MHz로 느리지만, I/O 핀은 수 GHz로 빠르다. Prefetch는 내부에서 한 번에 여러 비트를 읽어와 외부에서 고속으로 순차 전송하는 방식이다. DDR4는 8n Prefetch(BL8), DDR5는 16n(BL16)으로 한 번의 접근에서 2배 데이터를 전송한다. 대역폭은 올라가지만, 작은 데이터 접근 시 불필요한 전송이 생길 수 있어 DDR5는 Burst Chop(BL8)도 지원한다."

**Q: Bank Group이 존재하는 이유는?**
> "같은 Bank Group 내 Bank들은 I/O 센스 앰프와 데이터 경로를 물리적으로 공유한다. 그래서 같은 BG 내 연속 CAS는 tCCD_L(긴 간격), 다른 BG 간은 tCCD_S(짧은 간격)가 적용된다. MC 스케줄러가 연속 접근을 다른 BG로 분산하면 tCCD_S를 활용하여 대역폭을 극대화할 수 있다. DDR5는 BG가 4→8로 증가하여 인터리빙 기회가 더 많다."

**Q: LPDDR5에서 WCK가 CK와 분리된 이유는?**
> "LPDDR5는 명령 버스(CK)와 데이터 버스(WCK)의 클럭을 분리했다. 명령은 상대적으로 저속으로 충분하므로 CK는 낮은 주파수, WCK는 CK의 2배 또는 4배 주파수로 데이터만 고속 전송한다. 이를 통해 불필요한 고속 토글을 줄여 전력을 절감하면서도 데이터 대역폭을 확보한다. DVFSC와 결합하면 부하에 따라 WCK 주파수를 동적으로 변경하여 추가 절전이 가능하다."

---

## 6. 흔한 오해 와 DV 디버그 체크리스트

### 흔한 오해

!!! danger "❓ 오해 1 — 'DDR = 그냥 빠른 SDR. 세대 = 속도만 ↑'"
    **실제**: DDR 의 D 는 Double-rate (rising + falling edge 양쪽 사용) 이지만, 세대 별 변화는 prefetch (DDR3 8n / DDR4 8n / DDR5 16n), bank group 도입, on-die ECC, sub-channel split 등 _아키텍처_ 변화입니다. 같은 이름의 다른 동물.<br>
    **왜 헷갈리는가**: 약자 의미만 보고 "double rate" 하나로 단순화하기 쉬움.

!!! danger "❓ 오해 2 — 'Open-page 정책이 항상 좋다'"
    **실제**: Open-page 는 row hit 시 빠르지만 row conflict 시 `tRP+tRCD` 가 직렬로 들어가 페널티가 큽니다. workload 가 random 이거나 working set 이 row buffer 보다 훨씬 크면 close-page 가 더 좋을 수 있습니다.<br>
    **왜 헷갈리는가**: "row 열어 두면 다음에 빠름" 만 직관에 강하게 남고, conflict 페널티는 평균 BW 통계에 가려짐.

!!! danger "❓ 오해 3 — 'Refresh 는 그냥 주기적인 housekeeping. 큰 영향 없음'"
    **실제**: tREFI 마다 tRFC (DDR4 ~350 ns) 동안 _전체_ bank 가 묶이는 게 DDR4 의 기본 동작. 이는 BW 의 ~5% + worst-case latency tail 의 주된 원인이며, 그래서 DDR5 가 same-bank refresh 를 도입했습니다.

!!! danger "❓ 오해 4 — 'On-die ECC 가 있으니 외부 ECC 는 불필요'"
    **실제**: DDR5 의 on-die ECC 는 _128-bit word 안에서 1-bit_ 만 수정합니다. multi-bit 에러나 칩 단위 fail (chipkill) 은 여전히 외부 SECDED 가 필요하고, 데이터센터/서버는 둘 다 사용합니다.

!!! danger "❓ 오해 5 — 'tCL 이 작은 DRAM 이 무조건 빠르다'"
    **실제**: tCL 은 _cycle_ 단위입니다. 절대 시간 = `tCL × tCK`. 빠른 클럭의 DDR5 는 tCL=34 cycle 이지만 ns 로 환산하면 DDR4 tCL=22 (3200 MT/s) 와 비슷합니다. 비교는 항상 절대 ns 로.

### DV 디버그 체크리스트 (DRAM 셀/타이밍 레이어에서 자주 보는 실패)

| 증상 | 1차 의심 | 어디 보나 |
|---|---|---|
| Random read 시 silent data corruption (특정 row 만) | Refresh 누락 / tREFI 위반 / Row Hammer | `tREFI` SVA, deferred refresh 카운터 (≤8), refresh 발행 timestamp |
| Throughput 정상 같다가 특정 패턴에서 급락 | tFAW window 4-ACT 한도 초과 직전 stall | sliding tFAW window 안 ACT 카운트, bank 분포 |
| Read 데이터 왔는데 값이 깨짐 (1-bit 패턴) | DDR5 on-die ECC 미커버 비트 | 같은 word 안 1-bit 인지, ECC syndrome 로그 |
| 같은 row 재접근인데 RD latency 가 spec 보다 큼 | Open Row 가 다른 conflict 로 PRE 됨 (open-page 정책) | bank state tracker, open-row 변경 timestamp |
| MRS 후 ACT/RD 동작 이상 | tMRD/tMOD 경과 전 명령 발행 | MRS 직후 tMRD 사이클 SVA |
| LPDDR5 만 fail (DDR5 OK) | WCK2CK alignment / DVFSC 전환 시 retraining 누락 | WCK phase, DVFSC FSM 상태 |
| BL16 인데 BL8 만 받음 | Burst Chop (BC8) 의도/미의도 | MR0 BL field, RD with BC8 modifier |
| 특정 bank group 에서만 throughput 저하 | tCCD_L vs tCCD_S 매핑 misalignment | address mapper 의 bank-group bit, scheduler 내 BG 추적 |

!!! warning "실무 주의점 — tREFI 초과 시 Row Hammer 취약점 노출"
    **현상**: Refresh 간격(tREFI = 7.8μs @ 85°C 이하) 내에 같은 Row를 반복 ACT/PRE하면 인접 Row의 전하가 누설되어 비트 플립 발생. 보안 공격 및 데이터 손상으로 이어짐.

    **원인**: MC가 트래픽 집중 구간에서 Refresh를 지연시키거나, Deferred Refresh 횟수가 JEDEC 허용 한도(최대 8개)를 초과할 때 발생. DDR5의 RFM(Refresh Management) 미구현 시 Row Hammer 방어가 무력화됨.

    **점검 포인트**: Timing SVA에서 `tREFI` 위반 assertion 동작 여부 확인. 로그에서 Deferred Refresh 누적 카운터가 8을 초과하는 시점 탐색. DDR5 시뮬 모델에서 `RAAIMT` 레지스터(Row Activation Threshold) 설정값 검증.

---

## 7. 핵심 정리 (Key Takeaways)

- **Cell = capacitor + access transistor** — 누설되므로 refresh 필수, 읽으면 파괴되므로 restore 필수.
- **계층 구조**: Rank → Bank Group → Bank → Row → Column. Bank 는 동시에 여러 개 active 가능 → parallelism 의 원천.
- **명령 시퀀스**: ACT(row open) → RD/WR (col access) → PRE(close) → REF(주기). 각 단계 timing 종속 (`tRCD`, `tCL`, `tRP`, `tRAS`, `tRC`, `tRFC`, `tREFI`).
- **Row Hit / Miss / Conflict** = MC 의 가장 큰 성능 lever — Hit 비율 ≈ effective BW.
- **DDR4 → DDR5**: 2-channel split + BG 4→8 + Prefetch 8n→16n + On-die ECC + Same-Bank REF + CA 멀티플렉싱.

!!! warning "실무 주의점"
    - "DDR 빠르다" 는 **prefetch + DDR + bank parallelism** 의 곱. 하나라도 빠지면 nominal BW 미달.
    - **Open-page 가 항상 좋지 않다** — workload 의 row reuse rate 가 낮으면 close-page 가 더 좋을 수 있음.
    - **On-die ECC ≠ 시스템 ECC** — 1-bit / 128-bit 한정. multi-bit 보호는 외부 SECDED 가 책임.

### 7.1 자가 점검

!!! question "🤔 Q1 — Refresh 비용 계산 (Bloom: Apply)"
    DDR4 의 _tREFI = 7.8 µs_ × 8192 row. _Refresh 가 차지하는 시간 비율_?

    ??? success "정답"
        - 매 7.8 µs 마다 1 refresh.
        - 1 refresh = `tRFC` ~350 ns @ 8 Gb DRAM.
        - 비율 = 350 / 7800 = **~4.5%**.

        DDR5 with same-bank refresh: 비율 _감소_ (bank-level 병렬 refresh).

!!! question "🤔 Q2 — Row buffer locality (Bloom: Analyze)"
    Workload 의 _row reuse rate 90%_ vs _10%_. Open-page vs close-page?

    ??? success "정답"
        - **90% reuse**: Open-page 압도. 다음 access 가 같은 row 일 확률 큼 → row hit (1 cycle).
        - **10% reuse**: Close-page 우월. 같은 row 안 옴 → 미리 close 하면 다음 access 의 PRE 비용 절감.

        Memory controller 는 _workload 측정_ 후 policy 동적 전환 가능.

### 7.2 출처

**External**
- JEDEC JESD79 *DDR4* / JESD79-5 *DDR5*
- *DRAM Refresh Mechanisms* — academic survey
- Mutlu et al. *Row Hammer* papers

---

## 다음 모듈

→ [Module 02 — Memory Controller](02_memory_controller.md): 이 모듈의 ACT/RD/WR/PRE/REF 명령들이 _어떻게_ 스케줄되는가. FR-FCFS, Bank Parallelism, Write Batching, QoS, Refresh 최적화.

[퀴즈 풀어보기 →](quiz/01_dram_fundamentals_ddr_quiz.md)

<div class="chapter-nav">
  <a class="nav-prev" href="../">
    <div class="nav-label">◀ 이전</div>
    <div class="nav-title">코스 홈</div>
  </a>
  <a class="nav-next" href="../02_memory_controller/">
    <div class="nav-label">다음 ▶</div>
    <div class="nav-title">Memory Controller 아키텍처</div>
  </a>
</div>


--8<-- "abbreviations.md"
