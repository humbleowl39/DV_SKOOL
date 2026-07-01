---
title: "Module 01 — DRAM Fundamentals + LPDDR5"
---

:::tip[학습 목표]
이 모듈을 마치면:

- **Diagram** DRAM cell의 capacitor 동작 + Bank/Row/Column 계층 + sense amplifier 흐름을 그릴 수 있다.
- **Trace** ACT → RD/WR → PRE → REF의 전체 명령 시퀀스와 각 단계의 timing parameter를 추적할 수 있다.
- **Distinguish** LPDDR5의 핵심 기능(WCK/CK 클럭 분리, BG/8B/16B bank mode, PASR, On-die ECC + Link ECC, DVFSC)을 식별하고, 직전 세대 LPDDR4와의 차이를 설명할 수 있다.
- **Apply** Burst length, prefetch, bank group 개념을 throughput 계산에 적용할 수 있다.
- **Justify** Open-page 와 Close-page 정책의 trade-off 를 workload 패턴으로 설명할 수 있다.
:::
:::note[사전 지식]
- 디지털 회로 기본 (synchronous logic, FIFO)
- 캐시 / 메모리 계층 일반 지식
- PVT (Process / Voltage / Temperature) 변동 개념
:::
---

## 1. Why care? — 이 모듈이 왜 필요한가

### 1.1 시나리오 — 왜 _SRAM 처럼_ 안 만들었나?

SRAM(Static RAM, 정적 메모리 — 전원만 있으면 데이터를 그대로 유지하는 빠른 메모리, CPU 캐시에 쓰임) 캐시는 단 1 cycle 에 read/write 를 완료하는데 DRAM(Dynamic RAM, 동적 메모리 — capacitor 에 전하로 데이터를 저장해 밀도는 높지만 주기적으로 전하를 보충해야 하는 메모리, 메인 메모리에 쓰임) 은 왜 수십 cycle 을 기다려야 할까요? 그 답은 셀(cell — 1비트를 저장하는 가장 작은 메모리 단위) 구조의 근본적인 차이에 있습니다. (`capacitor` = 콘덴서; 전하를 모아 두는 소자로, 충전돼 있으면 1, 비어 있으면 0 으로 본다.)

SRAM 셀은 6개의 트랜지스터로 구성된 flip-flop 입니다. 전원이 켜져 있는 한 데이터를 영구적으로 유지하고, 읽기도 한 사이클에 마칩니다. 단점은 면적입니다. 6개의 트랜지스터를 한 셀에 묶으면 면적이 커지고, 이를 GB 단위로 집적하면 칩 원가가 현실적이지 않게 됩니다.

DRAM 셀은 트랜지스터 하나와 capacitor 하나로 이루어져 있어 면적이 SRAM 의 약 1/6 에 불과합니다. 그러나 이 단순함은 세 가지 물리적 대가를 치릅니다. 첫째, capacitor 는 시간이 지나면 전하가 누설되어 데이터가 사라지므로 **주기적 refresh** 가 반드시 필요합니다. 둘째, 읽기 동작 자체가 capacitor 전하를 sense amplifier 쪽으로 끌어내면서 원래 데이터를 **파괴**하므로, 읽은 직후 동일 row 에 데이터를 복원(restore)해야 합니다. 셋째, capacitor 의 미세 전하를 sense amplifier 가 감지하는 데 물리적인 시간이 걸리는데, 이 대기 시간이 바로 **tRCD** 의 기원입니다.

**Trade-off**:
| 항목 | SRAM | DRAM |
|------|------|------|
| 면적 | 1 (baseline) | 1/6 |
| Latency | 1 cycle | 수십 cycle |
| Refresh | 불필요 | 필수 |
| 비용/bit | 6× | 1× |

결국 SRAM 으로는 GB 단위 메모리를 경제적으로 구현할 수 없습니다. DRAM 은 수십 cycle 이라는 latency 대가를 치르는 대신 대용량을 저비용으로 제공하며, 그래서 CPU 는 SRAM 캐시와 DRAM main memory 를 함께 사용하는 hybrid 구조를 채택합니다.

이후 모든 DRAM/DDR 모듈은 한 가정에서 출발합니다 — **"DRAM cell 은 capacitor 이므로 데이터가 시간에 따라 누설되고, 외부에서 한 번 읽으면 파괴되며, 따라서 모든 access 는 row open → column access → row close 라는 stateful 시퀀스를 거친다"**. Memory Controller (MC) 가 왜 그렇게 복잡한 스케줄러를 갖는지, PHY 가 왜 nano-second margin 을 보정해야 하는지, DV TB 가 왜 timing SVA 수십 개를 동시에 보는지 — 전부 이 한 가정의 파생입니다.

이 모듈을 건너뛰면 이후의 모든 timing parameter / refresh 정책 / training 시퀀스 결정이 "그냥 외워야 하는 숫자" 로 보입니다. 반대로 capacitor → destructive read → restore → refresh 의 인과를 정확히 잡고 나면, tRCD / tRP / tRAS / tFAW 가 만나는 모든 디테일에서 _이유_ 가 보입니다.

:::tip[🤔 잠깐 — Row buffer 의 _hit/miss_ 의 비용 차이?]
Same row 또 access (hit) vs 다른 row access (miss). 시간 비용?

<details>
<summary>정답</summary>

- **Row hit**: 이미 _open_ 된 row buffer 에서 column access — _~1 cycle_ (~tCL = 14 cycle).
- **Row miss (conflict)**: 현재 row close (`PRE`, ~tRP=14) → 새 row open (`ACT`, ~tRCD=14) → column access (~tCL=14). **~42 cycle**.

**3× 차이**. 그래서 _row buffer locality_ 가 메모리 성능의 _가장 큰 결정 인자_.

Memory controller 의 _스케줄러_ 가 이걸 활용: _같은 row 의 access 모으기_ (FR-FCFS — First Ready First Come First Served).

</details>
:::
---

## 2. Intuition — 비유와 한 장 그림

:::tip[💡 한 줄 비유]
**DRAM Bank** ≈ **은행 창구 (한 번에 한 손님만)**.<br>
한 bank 에 access 중이면 다른 access 는 대기. 여러 bank 가 있으면 동시에 진행 가능 → **Bank-level parallelism**. **Row buffer** 는 창구 책상 위에 펼쳐 둔 서류 — 펴는 데(`ACT`) 시간이 걸리고, 다른 서류를 보려면 먼저 치워야(`PRE`) 한다. 책상 위 서류와 같은 손님(같은 row)이 또 오면 즉시 응대(Row Hit) — 가장 빠름.
:::
### 한 장 그림 — DRAM access 의 세 가지 결말

```d2
direction: down

REQ: "요청 도착\n(Bank N, Row R)"
BANK: "Bank N\nRow Buffer = 현재 open 된 Row (예: Row 5)"
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

가장 단순한 시나리오. 같은 Bank 에 **현재 Row 5 가 열려 있는 상태** 에서, MC(Memory Controller, 메모리 컨트롤러 — CPU 등의 read/write 요청을 DRAM 명령으로 바꿔 발행하는 회로)가 **Row 9 의 Column 0** 을 Read 하려 합니다. (아래 cycle 수는 LPDDR5 의 한 gear 를 가정한 **대표 예시** 입니다 — 실제 cycle 수는 gear/속도(DVFSC)에 따라 달라지고, spec 이 규정하는 것은 절대시간(ns) 이므로 §5.6 에서 다시 봅니다.)

먼저 이 시퀀스에 등장하는 네 명령과 네 타이밍 값을 한 줄씩 풀어 둡니다(자세한 물리는 §4–§5 에서 추적).

- **`ACT`**(Activate, 활성화) — 지정한 Row 한 줄을 통째로 sense amplifier(미세 전하를 0/1 로 키워 붙들어 두는 증폭기)로 끌어올려 "여는" 명령. 이 열린 Row 가 곧 **Row Buffer**(현재 열린 row 를 붙들고 있는 sense amp 들의 모음 = 임시 작업대)입니다.
- **`RD`/`WR`**(Read/Write) — 이미 열린 Row Buffer 안에서 Column 위치만 골라 데이터를 읽거나 쓰는 명령.
- **`PRE`**(Precharge, 프리차지) — 열린 Row 를 "닫고" 다음 Row 를 열 수 있도록 bit-line(셀의 전하가 흘러나오는 세로 배선)을 중립 전압으로 되돌리는 명령.
- **`REF`**(Refresh) — 누설된 전하를 보충하려고 주기적으로 row 내용을 다시 써 넣는 명령.
- 타이밍 값은 모두 "명령 사이에 최소한 기다려야 하는 시간(cycle 수)"입니다 — **tRCD**(ACT→RD/WR 사이), **tRP**(PRE→ACT 사이), **tRAS**(ACT→PRE 최소 간격), **tCL**=CAS Latency(RD 발행→데이터 출력까지). `t` 는 time, 이름은 무엇과 무엇 사이인지를 가리킵니다.

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
| ⑦ | `T66..T70`  | DQ pin | 8-beat (BL8) burst 출력 | prefetch 8n 이라 1번 column access 로 8 비트가 나옴 — DDR 클럭 4 사이클 (`DQ` = 데이터 핀; `burst length`/BL = 한 번의 RD/WR 로 연속해 쏟아지는 데이터 묶음 길이; `prefetch` = 내부에서 한 번에 미리 길어 올리는 비트 수 — §5.4) |
| ⑧ | `T22..T74`  | DRAM | Row 9 는 `tRAS` (≥52 cycle) 동안 open 유지 | Row 가 stable 해질 때까지 PRE 금지 |

```c
// MC scheduler 의 pseudo code — 이 1 사이클이 어떻게 만들어지는가
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

:::note[여기서 잡아야 할 두 가지]
**(1) 한 read 는 단일 cycle 이 아니라 PRE→ACT→RD 의 직렬 sequence 다.** Row Conflict 라면 `tRP+tRCD+tCL` 이 _그 한 read_ 에 직렬로 누적됨(위 예시에서 약 3배). 이게 MC 가 Row Hit 를 그토록 추구하는 이유.<br>
**(2) 같은 bank 에서는 직렬, 다른 bank 끼리는 병렬.** Row Conflict 동안 Bank N 은 묶여 있지만 Bank N+1 은 완전히 독립적으로 ACT/RD 를 진행 가능 — 이것이 **Bank-level Parallelism** 이고 MC scheduler 가 다음 모듈에서 본격적으로 활용할 자원입니다.
:::
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

이 계층의 각 단어는 "주소를 쪼개는 단위"입니다 — 큰 통에서 작은 칸으로 좁혀 갑니다. **Rank**(랭크 — 같은 데이터 버스를 공유하며 한 번에 하나만 선택되는 DRAM 칩 묶음)가 가장 큰 단위이고, 그 안에 여러 **Bank Group**(뱅크 그룹 — I/O 회로를 일부 공유하는 bank 들의 묶음)이 있고, 다시 각 그룹 안에 여러 **Bank**(뱅크 — 서로 독립적으로 동작할 수 있는 메모리 어레이; 한 bank 가 바쁠 때 다른 bank 는 일할 수 있어 병렬성의 원천)가 있습니다. 한 bank 안의 데이터는 격자처럼 깔려 있어, **Row**(행 — 한 번에 통째로 sense amplifier 로 끌어올리는 가로줄, 수만 개 셀 단위)와 **Column**(열 — 그 행 안에서 실제로 읽고 쓸 위치를 고르는 세로 좌표)의 2차원 좌표로 한 칸을 지정합니다.

LPDDR5 예시 (BG 모드): 4 Bank Group · 4 Bank/Group (총 **16 Bank**) · 수만 Row/Bank · 다수 Column/Row. (LPDDR5 는 Mode Register 로 BG 모드(16뱅크)/8B 모드(8뱅크)/16B 모드(16뱅크) 중 하나를 고릅니다 — §4.4.)

접근 시퀀스는 세 단계로 고정됩니다. 먼저 MC 가 **ACTIVATE (ACT)** 명령으로 원하는 Row 번호를 지정하면 DRAM 내부의 word-line 이 활성화되고 해당 행의 전하가 sense amplifier 로 끌려 나와 Row Buffer 에 자리잡습니다. Row Buffer 가 준비된 뒤에야 **READ 또는 WRITE (RD/WR)** 명령으로 Column 주소를 지정하여 실제 데이터를 주고받을 수 있습니다. 마지막으로 다른 Row 에 접근하기 전에 반드시 **PRECHARGE (PRE)** 명령으로 Row Buffer 를 비우고 bit-line 을 중립 전압으로 돌려야 합니다 — 이 단계를 건너뛰면 sense amplifier 가 오염된 상태에서 다음 Row 를 읽어 잘못된 데이터가 나옵니다.

### 4.2 Row Hit / Miss / Conflict — 일반화

§3 의 Row Conflict 는 세 가능한 결말 중 하나입니다. MC 가 특정 Bank 에 access 할 때 그 Bank 의 Row Buffer 에 이미 같은 Row 가 열려 있다면 **Row Hit** 입니다 — ACT 를 다시 발행할 필요 없이 tCL 만 기다리면 데이터가 나오므로 가장 빠릅니다. Row Buffer 가 완전히 비어 있는 경우는 **Row Miss** 인데, ACT 를 한 번 발행해야 하므로 tRCD 가 추가로 소요됩니다. 가장 비싼 경우는 **Row Conflict** 입니다 — 이미 다른 Row 가 열려 있으므로 먼저 PRE 로 닫고(tRP) 다시 ACT 로 원하는 Row 를 열어야(tRCD) 비로소 RD/WR 가 가능합니다(tCL). 따라서 Row Conflict 의 총 대기 시간은 세 값의 직렬 합인 tRP + tRCD + tCL 이며, Hit 대비 약 3배에 달합니다.

이 세 결말의 비용 격차가 바로 Memory Controller 의 핵심 목표를 정의합니다 — **Row Hit 비율을 극대화하는 것**. FR-FCFS 스케줄링, Open/Close page 정책, 그리고 연속 주소를 적절한 Bank 에 매핑하는 Address Mapping 이 모두 이 목표를 위해 등장하며, Module 02 에서 본격적으로 다룹니다.

### 4.3 명령 FSM — Bank 별 상태 머신

```d2
direction: down

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

### 4.4 LPDDR5 의 핵심 기능 — 직전 세대 LPDDR4 와의 차이

이 코스의 주제는 모바일·SoC main memory 인 **LPDDR5** 입니다. LPDDR5 가 무엇인지를 가장 빠르게 잡는 길은 직전 세대 **LPDDR4** 에서 무엇이 바뀌었는지를 보는 것입니다. 아래 표는 그 세대 차이를 정리한 것으로, 왼쪽 열(LPDDR5)이 이 코스가 다루는 대상이고 오른쪽 열(LPDDR4)은 "직전엔 이랬다" 는 대비용입니다.

| 측면 | **LPDDR5** (주제) | LPDDR4 (직전 세대) | 무엇이 바뀌었나 |
|------|------|------|------|
| 클럭 | **CK(명령) + WCK(데이터) 분리**, WCK:CK=2:1/4:1 | CK + DQS (DQS 가 데이터 스트로브) | 전용 **WCK** 도입 — 데이터 버스만 선택적 고속 |
| 채널 | 2 × 16-bit | 1 × 16-bit | 채널 분할로 명령 병렬성 ↑ |
| Bank 구성 | MR 선택: **BG 모드(4 BG×4=16) / 8B(8) / 16B(16)** | BG 없는 8 Bank | **Bank Group 도입** + 모드 가변(최대 16뱅크) |
| Prefetch / BL | 16n / BL16·BL32 | 16n / BL16·BL32 | 동일 (16n 은 LPDDR4부터) |
| ECC | **On-die ECC**(디바이스 의존) + **Link ECC**(신규) | 없음 | 셀 보호(On-die) + 링크 보호(Link) 추가 |
| Refresh | Per-bank + **PASR** | Per-bank | **PASR**(부분배열 self-refresh)로 전력 절감 |
| CMD bus | **CA[6:0]** 다중사이클 → CBT 필수 | CA[5:0] | CA 폭·training(CBT) 강화 |
| 전압 | VDD1 1.8V, **VDD2 ~1.05V, VDDQ 0.5V** | VDDQ 1.1V (LPDDR4X 0.6V) | VDDQ 추가 인하 → 저전력 |
| 전력/주파수 | **DVFSC**(F0~F4 gear) 런타임 전환 | 저전력 모드(고정 주파수 중심) | **동적 전압·주파수 스케일링** 도입 |

### 4.5 Prefetch + Bank Group 의 결합 — 대역폭의 두 축

```d2
direction: down

CELL: "내부 cell 어레이\n(느림, ~수백 MHz)"
BUF: "Row Buffer / I/O sense"
DQ: "DQ pin\n(빠름, 수 GHz)"
CELL -> BUF: "① Prefetch n bit (BL = n)"
BUF -> DQ: "② Bank Group 별 독립 I/O\n같은 BG: tCCD_L (느림)\n다른 BG: tCCD_S (빠름)"
```

한 번의 column access 가 BL 개수만큼의 beat 로 변환되므로, 내부 셀 어레이의 느린 동작 속도를 외부의 고속 DQ pin 이 감추는 구조입니다. 여기에 MC scheduler 가 연속 access 를 다른 BG 로 분산하면 tCCD_S 의 짧은 gap 으로 이어붙일 수 있어 효과적인 대역폭이 극대화됩니다. 결국 DDR 의 대역폭은 Prefetch 와 Bank Group Interleaving 이라는 두 layer 의 곱으로 결정됩니다.

---

## 5. 디테일 — 셀, Prefetch, Bank Group, Mode Register, Confluence

### 5.1 DRAM 셀 동작

DRAM 셀의 구조는 1T1C — 트랜지스터 하나와 커패시터 하나 — 로 이루어져 있습니다. 이 단순한 구조 덕분에 bit 당 면적이 SRAM 의 6분의 1 수준에 불과하지만, 커패시터라는 소자의 본질적 특성이 세 가지 필수 동작을 요구합니다. 첫째, 읽기는 파괴적(destructive)이므로 읽은 직후 반드시 데이터를 재기록(restore)해야 합니다. 둘째, 커패시터는 시간이 지나면 전하가 누설되므로 주기적으로 refresh 를 통해 전하를 보충해야 합니다. 셋째, sense amplifier 가 bit-line 의 mV 단위 전압 차이를 증폭하는 데 시간이 필요하므로, ACT 후 tRCD 동안 은 아무 명령도 넣을 수 없습니다. 아래 다이어그램은 이 세 과정을 물리 수준에서 추적합니다.

<figure markdown>
  <img src="../../img/dram_1t1c_cell.svg" alt="1T1C NMOS DRAM 셀 단면 구조" width="620" style="background:#ffffff; padding:14px 10px; border-radius:8px;" />
  <figcaption><b>1T1C NMOS 셀의 단면 구조</b> — <b>word line</b>이 access transistor의 poly-silicon gate를 제어하고, gate가 열리면 <b>bit line</b>의 N+ 확산영역과 <b>capacitor</b>가 도통한다. capacitor 전하의 유무가 0/1이며, 이 전하가 bit line으로 흘러나오는 순간 원본이 파괴(destructive read)된다.<br><small>출처: Wikimedia Commons, 저자 Cyferz — CC BY-SA 3.0 / GFDL (원본 무수정). 원본 파일: <i>Original 1T1C DRAM design.svg</i></small></figcaption>
</figure>

이 단순한 구조 위에서 세 가지 동작이 일어납니다.

- **읽기(Read)** — word line을 활성화해 transistor를 켜면, capacitor에 갇혀 있던 미세 전하가 bit line으로 흘러나옵니다. sense amplifier가 이 mV 단위 전압 차이를 감지해 0/1을 판정하는데, 이 과정에서 capacitor의 원본 전하가 소실되므로(**destructive read**) 판정 직후 같은 값을 즉시 다시 써 넣는 **restore**가 자동으로 뒤따릅니다.
- **쓰기(Write)** — word line을 활성화한 뒤 bit line에 원하는 전압을 인가하면, 도통된 transistor를 통해 capacitor가 그 전압까지 충전되거나 방전됩니다.
- **Refresh** — capacitor는 시간이 지나면 전하가 누설되므로, 데이터를 잃기 전에 주기적으로 읽고 다시 써 넣어야 합니다. `tREFI` 는 REF 명령의 평균 발행 간격으로, LPDDR5 는 ≈ 3.9 µs(온도에 따라 가변)입니다. LPDDR5 는 per-bank refresh + PASR 로 미사용 array 영역의 refresh 를 생략해 전력을 줄입니다.

그런데 셀 하나만 봐서는 `Row Buffer` 가 어디서 나오는지 보이지 않습니다. 실제 DRAM 에서 셀은 **2차원 격자**로 깔리고, 같은 행의 셀들은 하나의 **word line** 을, 같은 열의 셀들은 하나의 **bit line** 을 공유합니다. 그래서 word line 하나를 활성화하면 그 행의 모든 셀이 **동시에** 자기 bit line 으로 전하를 토해내고, 각 bit line 끝의 **sense amplifier 가 그 값을 latch** 합니다. 한 행 전체를 받아내는 이 **sense amplifier 의 배열이 곧 Row Buffer** 입니다 — 별도의 메모리가 아니라 "지금 열린 row 를 붙들고 있는 sense amp 들의 모음" 입니다. 이후 Column 주소는 이 Row Buffer 안에서 어느 칸을 DQ 로 내보낼지만 고르므로, 같은 row 안의 연속 접근(Row Hit)이 그토록 빠른 것입니다.

#### Sense amplifier 는 어떻게 mV 차이를 0/1 로 키우는가 — charge sharing + 정/부귀환

앞 절들은 sense amplifier 가 "mV 단위 차이를 0/1 로 증폭한다" 는 _결과_ 만 말했습니다. 그 증폭이 실제로 어떻게 일어나는지가 tRCD·tRAS 같은 타이밍의 물리적 뿌리이므로, 두 단계로 나눠 봅니다.

**① Charge sharing — 미세 ΔV 가 만들어지는 단계.** ACT 전에 bit-line 은 미리 VDD/2 (precharge 전압) 로 충전돼 있습니다. 셀 capacitor 의 용량은 bit-line 자체가 갖는 기생 용량보다 훨씬 작은데, word-line 이 열려 둘이 연결되면 셀의 전하가 큰 bit-line 용량과 **나눠 가집니다(charge sharing)**. 그 결과 bit-line 전압은 원래의 VDD/2 에서 아주 조금 — 보통 수십 mV 수준 — 만 움직입니다. 셀이 '1'(VDD 충전) 이었으면 살짝 올라가고, '0'(접지) 이었으면 살짝 내려갑니다. 이 미세한 ΔV 가 저장값의 유일한 증거입니다.

**② 정/부귀환 latch — full rail 로 키우는 단계.** sense amplifier 는 두 개의 인버터를 서로의 입력과 출력에 엇갈려 연결한 **cross-coupled latch** 입니다. 한쪽 bit-line(BL)과 그 짝(BL#, reference 로 VDD/2 유지)을 두 노드로 받는데, ①에서 생긴 작은 불균형이 latch 에 들어가면 **양의 되먹임(positive feedback)** 이 작동합니다 — 조금 높은 쪽은 인버터가 더 끌어올리고, 조금 낮은 쪽은 더 끌어내려, 둘의 차이가 스스로 커집니다. 이 되먹임이 폭주하여 결국 BL 은 VDD 로, BL# 은 GND 로(또는 그 반대로) **full rail 까지 갈라집니다**. 비로소 "0/1" 로 확정된 디지털 값이 됩니다.

이 메커니즘이 앞에서 본 두 가지 제약의 _이유_ 를 동시에 설명합니다.

- **왜 read 가 destructive 인가** — ①의 charge sharing 순간 셀의 원본 전하가 bit-line 으로 빠져나가 흩어집니다. 셀은 더 이상 원래 전압이 아닙니다. 다행히 ②의 latch 가 bit-line 을 full rail 로 몰아붙이면, 같은 word-line 이 아직 열려 있는 동안 그 full-rail 전압이 셀 capacitor 를 원래 값으로 **되써넣습니다(restore)**. 즉 sense → restore 가 한 동작으로 이어지는 것입니다.
- **왜 tRCD·tRAS 가 필요한가** — ①→② 가 full rail 에 도달하기까지 물리적 시간이 걸리므로, ACT 후 그 시간이 지나기 전(=`tRCD` 만료 전)에 column 을 읽으면 아직 갈라지는 중인 불안정한 값을 잡게 됩니다. 그래서 ACT→RD 사이에 tRCD 가 강제됩니다. 또한 latch 가 셀을 충분히 restore 하기까지의 시간이 바로 `tRAS`(ACT→PRE 최소 간격)의 하한이며, restore 가 끝나기 전에 PRE 로 word-line 을 닫으면 셀에 _덜 써진_ 약한 전하만 남아 다음 refresh 전에 데이터를 잃을 위험이 생깁니다.

```d2
direction: down

RowDec: "Row Decoder\n(한 번에 word line 1개만 활성화)" { style.fill: "#e8f0fe" }

WL0: "Word line 0" { style.fill: "#fff4e5" }
WL1: "Word line 1" { style.fill: "#fff4e5" }

C00: "1T1C"
C01: "1T1C"
C10: "1T1C"
C11: "1T1C"

BL0: "Bit line 0" { style.fill: "#e6f4ea" }
BL1: "Bit line 1" { style.fill: "#e6f4ea" }

SA0: "Sense Amp 0\n= Row Buffer" { style.fill: "#fce8e6" }
SA1: "Sense Amp 1\n= Row Buffer" { style.fill: "#fce8e6" }

IO: "Column Decoder / MUX → DQ (I/O)"

RowDec -> WL0
RowDec -> WL1
WL0 -> C00
WL0 -> C01
WL1 -> C10
WL1 -> C11
C00 -> BL0
C10 -> BL0
C01 -> BL1
C11 -> BL1
BL0 -> SA0
BL1 -> SA1
SA0 -> IO
SA1 -> IO
```

### 5.2 DDR 세대별 비교 — full table

아래 표는 LPDDR5 의 핵심 사양을 한눈에 정리하고, 오른쪽에 직전 세대 LPDDR4 대비 무엇이 바뀌었는지를 붙였습니다.

| 항목 | **LPDDR5** (주제) | LPDDR4 대비 |
|------|------|------|
| 속도 | 6400~8533 MT/s (LPDDR5X 포함) | 4267 MT/s → 대폭 상승 |
| 전압 | VDD1 1.8V, VDD2 ~1.05V, **VDDQ 0.5V** | VDDQ 1.1V(4X 0.6V) → 추가 인하 |
| 클럭 | **CK + WCK 분리** (WCK:CK 2:1/4:1) | CK + DQS → 전용 WCK 도입 |
| Prefetch / BL | 16n / BL16·BL32 | 동일 |
| Bank 구성 | **MR 선택: BG(4×4=16) / 8B(8) / 16B(16)** | BG 없는 8뱅크 → BG 도입·모드 가변 |
| Channel | 2 × 16-bit | 1 × 16-bit → 채널 분할 |
| ECC | **On-die ECC + Link ECC(신규)** | ECC 없음 → 셀·링크 보호 추가 |
| Refresh | Per-bank + **PASR** | Per-bank → PASR 추가 |
| 전력 관리 | **DVFSC gear(F0~F4) + 저전력 모드** | 저전력 모드 → 동적 스케일링 도입 |
| 용도 | 모바일 SoC, 차량 | 동일(직전 세대) |

:::note[LPDDR5 의 뱅크 수는 모드로 정해진다]
LPDDR5 는 Mode Register 로 **BG 모드(16뱅크) / 8B 모드(8뱅크) / 16B 모드(16뱅크)** 중 하나를 선택하며 **최대 16 뱅크** 입니다. BG 모드에서만 Bank Group(4 BG × 4 = 16) 계층이 존재하고, 8B/16B 모드에서는 BG 없이 평평한 8/16 뱅크로 동작합니다. tCCD_S/tCCD_L 구분은 BG 모드에서만 의미가 있습니다.
:::

### 5.3 LPDDR5 의 핵심 특징 — 상세

LPDDR5 는 직전 세대 LPDDR4 대비 단순한 속도 향상이 아니라 **"모바일 전력 예산 안에서 대역폭을 끌어올리고 데이터 무결성을 강화"** 하는 방향으로 여러 구조를 바꿨습니다. 아래 다섯 가지가 그 축이며, 각각의 물리적 동기와 효과를 순서대로 살펴봅니다. (LPDDR5 고유 기능의 상세는 §5.7 에서 이어집니다.)

1. **CK/WCK 클럭 분리 (WCK 도입)** — 명령 클럭(CK)과 데이터 클럭(WCK)을 나눠, 데이터 버스만 WCK:CK=2:1 또는 4:1 의 고속으로 돌립니다. 명령 버스는 저속으로 충분하므로 불필요한 고속 토글을 줄여 전력을 절감하면서 데이터 대역폭을 확보합니다.
2. **Bank mode 선택 (BG/8B/16B)** — Mode Register 로 뱅크 구성을 고릅니다. 대역폭이 중요한 워크로드는 BG 모드(16뱅크, Bank Group interleaving 으로 tCCD_S 활용), 단순·저전력 구성은 8B/16B 모드를 선택합니다.
3. **On-die ECC + Link ECC** — 두 ECC 는 보호 대상이 **직교** 합니다. On-die ECC 는 DRAM 셀 내부의 soft error 를 (외부에 투명하게) 정정하고, **Link ECC**(LPDDR5 신규)는 DQ 전송경로(링크)의 비트 에러를 별도로 보호합니다.
4. **Per-bank Refresh + PASR** — bank 단위 refresh 로 나머지 bank 를 계속 쓰게 하고, PASR(Partial Array Self-Refresh)로 데이터가 든 array 영역만 self-refresh 하여 빈 영역의 refresh 전력을 아낍니다.
5. **DVFSC (동적 전압·주파수 스케일링)** — 트래픽 부하에 따라 gear(F0~F4)를 런타임에 바꿔 전압·주파수를 함께 조정합니다. gear 가 바뀌면 WCK:CK 비율이 달라지므로 WCK2CK 재정렬이 뒤따릅니다(§5.7).

### 5.4 Prefetch 아키텍처 — LPDDR5 대역폭의 핵심

DRAM 셀 어레이의 내부 동작 주파수는 수백 MHz 에 불과하지만, 외부 DQ pin 은 LPDDR5 에서 수 GHz(WCK 기준)로 동작합니다. 이 속도 간극을 메우는 것이 Prefetch 아키텍처입니다. 한 번의 column access 로 내부에서 n 비트를 한꺼번에 읽어 오고, 그것을 외부의 고속 클럭으로 순차 직렬 전송하는 방식입니다. LPDDR5 는 **16n Prefetch** 로 한 번에 16비트(BL16)를 가져오며(LPDDR4 부터 16n), BL32 도 지원합니다.

여기서 DDR 의 "Double"(양 에지 전송)과 prefetch 가 어떻게 한 메커니즘으로 맞물리는지가 핵심입니다. 둘은 별개의 트릭이 아니라 같은 직렬화 파이프라인의 안과 밖입니다 — **내부**에서는 느린 클럭으로 한 번의 column access 가 n 비트를 _병렬로_ 길어 올리고(prefetch), **외부**에서는 그 n 비트를 고속 WCK 의 **상승 에지와 하강 에지 양쪽**에 하나씩 실어 직렬로 쏟아냅니다(Double Data Rate). 그래서 16n prefetch 는 WCK 8 사이클(상승 8 + 하강 8 = 16 beat)에 정확히 비워집니다. 다시 말해 양 에지 전송이 내부 한 번의 접근으로 모은 비트 다발을 _절반의 클럭 사이클_ 로 내보내 주기 때문에, prefetch 폭과 BL 과 "Double" 이 항상 같은 숫자로 정렬되는 것입니다.

LPDDR5 에서 특히 중요한 것은 이 고속 직렬화가 **WCK(데이터 전용 클럭)** 위에서 일어난다는 점입니다. 명령/주소는 저속 CK 로 받고, 16개 beat 의 데이터만 WCK 로 쏟아내므로 — 데이터 버스가 바쁘지 않을 때는 WCK 를 끄거나 낮은 gear 로 내려 전력을 아낄 수 있습니다. 이것이 LPDDR5 가 대역폭과 전력을 동시에 잡는 방식입니다.

<details>
<summary>Prefetch 동작 예시 — 16n (BL16)</summary>

```
Prefetch = DRAM 내부에서 한 번에 읽어오는 비트 수

문제: DRAM 셀 어레이는 느리다 (내부 클럭 ≈ 수백 MHz)
     하지만 데이터 I/O(WCK)는 빠르다 (수 GHz)
     → 내부와 외부의 속도 차이를 어떻게 해결?

해결: Prefetch로 내부에서 여러 비트를 한꺼번에 읽고,
     외부 데이터 I/O(WCK)에서 빠른 클럭으로 순차 전송

  LPDDR5 (16n Prefetch):
    내부: 1회 column access 로 16비트 동시 읽기 (per DQ pin)
    외부: 16비트를 WCK 의 8사이클(상승+하강 × 8)로 전송
    → Burst Length = 16 (BL16), BL32 도 지원

  시각화 (1 DQ pin):
    DRAM 내부: [b0 b1 ... b15]  ← 16bit 동시 읽기 (느린 CK 도메인)
                    ↓ Serialization
    DQ pin:    b0 b1 ... b15    ← 고속 WCK 8 사이클 (양 에지)

  Prefetch 가 클수록 Burst 길이가 길어져 순차 접근 대역폭이 향상된다.
  단, 전송 단위(BL)보다 작은 데이터를 요청해도 전체 Burst 를 소비하는 비효율이 있다.
```

</details>

### 5.5 Bank Group — 왜 존재하는가?

Bank 만 있으면 될 것 같은데 왜 Bank Group 이라는 계층이 추가된 걸까요? 이유는 DRAM 내부의 I/O 회로 공유 때문입니다. 같은 Bank Group 안의 Bank 들은 I/O sense amplifier 와 데이터 경로를 물리적으로 공유합니다. 그 공유 회로가 재사용 준비를 마칠 때까지는 다음 CAS 명령을 넣을 수 없어서 tCCD_L(긴 간격)이 적용됩니다. 반면 다른 Bank Group 의 Bank 는 독립된 I/O 회로를 갖고 있어 tCCD_S(짧은 간격)만 기다리면 됩니다. MC 스케줄러가 연속 access 를 다른 BG 로 분산하는 것은 바로 이 tCCD_S 를 활용하는 전략입니다. LPDDR5 에서 Bank Group 계층은 **BG 모드(4 BG × 4 = 16뱅크)** 에서만 존재하며, 8B/16B 모드에서는 BG 없이 평평한 뱅크 구조로 동작해 tCCD_S/tCCD_L 구분이 사라집니다.

이 구분을 정리하면 다음과 같습니다.

- **같은 BG 내 연속 CAS**: 공유 I/O 회로의 재사용을 기다려야 하므로 **tCCD_L**(긴 간격).
- **다른 BG 간 연속 CAS**: 독립 회로를 쓰므로 **tCCD_S**(짧은 간격) — 대략 tCCD_L 의 절반.
- **MC 스케줄러 전략**: 연속 접근이 다른 BG 로 가도록 Address Mapping 을 설계하면 tCCD_S 로 이어붙일 수 있습니다 — 이것이 **Bank Group Interleaving** 의 핵심 원리입니다(Module 02 §5.3·§5.7).

### 5.6 LPDDR5 타이밍 파라미터 핵심

DRAM timing 값은 본질적으로 **절대시간(ns) 최소값** 으로 규정되고, cycle 수는 `ceil(t_ns / tCK)` 로 파생됩니다. LPDDR5 는 DVFSC gear 에 따라 tCK(그리고 WCK 주파수)가 런타임에 바뀌므로 **같은 ns 제약이라도 cycle 수는 gear 마다 달라집니다**. 아래 표의 cycle 값은 한 gear 를 가정한 **대표 예시** 이며, 실제 검증에서는 절대 ns 를 기준으로 봐야 합니다(이 성질이 timing checker 를 SVA 가 아닌 절차적 SV 로 짜는 이유입니다 — Module 04 §5.7).

| 파라미터 | 의미 | 성격 | 예시 (대표 gear) |
|---------|------|------|------|
| **tCL** | CAS Latency (RD→데이터 출력) | cycle (gear 의존) | ~수십 cycle |
| **tRCD** | ACT→RD/WR (Row to Column Delay) | ns 규정 → cycle 파생 | 예: 18 ns |
| **tRP** | PRE→ACT (Row Precharge) | ns 규정 → cycle 파생 | 예: 18 ns |
| **tRAS** | ACT→PRE (Active to Precharge, 최소) | ns 규정 → cycle 파생 | 예: 42 ns |
| **tRC** | ACT→ACT (같은 Bank) = tRAS + tRP | ns 규정 | tRAS + tRP |
| **tRFC** | Refresh→ACT (Refresh Cycle) | ns (밀도 의존) | 밀도별 수백 ns |
| **tREFI** | Refresh Interval (평균) | µs (온도 가변) | ≈ 3.9 µs |
| **tCCD_S** | CAS→CAS (다른 BG) | cycle (BG 모드) | 짧음 |
| **tCCD_L** | CAS→CAS (같은 BG) | cycle (BG 모드) | ≈ 2× tCCD_S |
| **tFAW** | Four Activate Window | ns (전류 제한) | window 당 ACT ≤ 4 |
| **tWTR** | Write→Read turnaround | ns | S/L (BG 구분) |

**면접 포인트**: tCL, tRCD, tRP 는 "22-22-22" 처럼 세 cycle 수치로 표기됩니다. 값이 클수록 느리지만, 이 수치들은 **절대 ns 를 tCK 로 나눈 cycle 수** 이므로 클럭이 빠르면 cycle 수가 커도 절대 시간(ns)은 비슷합니다. LPDDR5 는 gear 마다 tCK 가 다르므로 비교는 항상 절대 ns 로 해야 합니다.

**tFAW 는 전류 제한에서 나온다.** 위 표의 tFAW(Four Activate Window)는 다른 타이밍과 성격이 다릅니다 — Row Hit/Conflict 같은 데이터 정합성이 아니라 **전력**에서 나온 제약입니다. ACT 명령은 word-line 을 부스팅하고 한 행 전체의 sense amplifier 를 한꺼번에 켜는, DRAM 동작 중 순간 전류(inrush current)가 가장 큰 이벤트입니다. 여러 bank 에 ACT 를 너무 촘촘히 몰면 이 순간 전류가 칩의 전원 분배망(power delivery)이 감당할 수 있는 한도를 넘어 전압이 출렁이고 인접 동작이 오작동할 수 있습니다. 그래서 JEDEC 은 "어떤 연속된 tFAW 구간 안에서도 ACT 는 최대 4번까지" 라는 슬라이딩 윈도우 제한을 둡니다. tRRD(ACT→ACT 최소 간격)가 _연속 두 ACT_ 의 간격을 막는다면, tFAW 는 _윈도우당 총 횟수_ 를 막아 평균 전류를 누른다고 보면 됩니다.

### 5.7 LPDDR5 고유 기능 — 모바일/SoC main memory 관점

LPDDR5 는 현대 모바일 SoC 의 main memory 표준이며 이 코스의 주제입니다. 핵심 방향은 **배터리 전력이 허용하는 한도 안에서 최대 성능** 입니다. 그래서 데이터 전압을 VDDQ 0.5 V 까지 낮추고, 명령 클럭(CK)과 데이터 클럭(WCK)을 분리하여 데이터 버스만 선택적으로 고속 동작시키며, 부분 array self-refresh(PASR)로 사용하지 않는 array 의 refresh 를 생략합니다. 아래 표는 직전 세대 LPDDR4 와의 수치 비교이며, 이어지는 절에서 LPDDR5 고유 기능들을 상세히 설명합니다.

| 항목 | **LPDDR5 / LPDDR5X** | LPDDR4 (직전 세대) |
|------|------|------|
| 전압 | VDD2 ~1.05V, **VDDQ 0.5V** | VDDQ 1.1V (LPDDR4X 0.6V) |
| 클럭 | **CK + WCK 분리** (WCK:CK 2:1/4:1) | CK + DQS |
| 채널 | 2 × 16-bit | 1 × 16-bit |
| 최대 속도 | 6400 (LPDDR5X ~8533) MT/s | 4267 MT/s |
| Bank | **BG(16) / 8B(8) / 16B(16)** 모드 | BG 없는 8뱅크 |
| ECC | **On-die + Link ECC** | 없음 |
| 패키지 | PoP (SoC 위 적층) | PoP |
| 전력 관리 | **DVFSC gear + 저전력 모드** | 저전력 모드 |

:::note[한 줄 요약 — LPDDR5 의 정체성]
LPDDR5 = **WCK 도입**(LPDDR4 는 DQS) + **bank mode(BG/8B/16B) 선택** + **DVFSC gear** + **On-die + Link ECC** + PASR + VDDQ 0.5V + PoP. 직전 세대 LPDDR4 는 CK+DQS, BG 없는 8뱅크, VDDQ 1.1V, ECC 없음이었습니다.
:::

#### LPDDR5 고유 핵심 기능

**1. WCK (Write Clock) — LPDDR5 의 가장 큰 구조적 차이.** LPDDR4 는 데이터 스트로브(DQS)를 썼지만, LPDDR5 는 명령용 클럭 **CK** 와 데이터용 클럭 **WCK** 를 분리했습니다. CK 는 저속(명령/주소)으로, WCK 는 고속(DQ 데이터, CK 의 2배 또는 4배)으로 돌립니다. 명령 버스는 저속으로 충분하고 데이터 버스만 고속으로 돌리면 되므로 전력을 아낄 수 있고, WCK:CK 비율은 2:1(기본) 또는 4:1(고속 모드)로 gear 에 따라 바뀝니다.

```
   +---+   +---+   +---+   CK  (명령 동기화, 저속)
   |   |   |   |   |   |
   +   +---+   +---+   +---

   +-+-+-+-+-+-+-+-+-+-+-+  WCK (데이터 동기화, 2× 이상 고속)
   | | | | | | | | | | | |
   +-+-+-+-+-+-+-+-+-+-+-+
```

**2. DVFSC / DVFSQ (동적 전압·주파수 스케일링) — FSP 기반.** DVFSC 는 코어(VDD2) 주파수·전압을 **FSP(Frequency Set Point, MR16)** 단위로 동적 조정하고, DVFSQ 는 I/O 전압 VDDQ 를 0.5V ↔ 0.3V 로 스케일링합니다(DVFSC 와 별개 축; 전환 시 VRCG 로 Vref tracking). MC 가 트래픽 양을 모니터링하여 자동 전환합니다(Enhanced DVFSC 존재). 전환 예: `F0(최고 성능) → F1(절전) → F2(깊은 절전)` — 각 FSP 에서 WCK:CK 비율(2:1/4:1)과 전압이 함께 조정되므로 **gear 전환 시 WCK2CK 재정렬** 이 뒤따릅니다.

**3. Data Copy (저전력 인코딩 — LPDDR5 고유, MR21).** 8-Byte 데이터에 같은 패턴이 반복되면 reference data 만 한 DQ link 로 전송해 IO/core 전력(IDD4W/R)을 절감합니다(DBI 와 유사한 결이며 "행간 메모리 복사 엔진" 이 아닙니다). Write/Read 각각 enable 하며, Read Data Copy 활성 시 Read latency 가 늘 수 있습니다.

**4. Link ECC (LPDDR5 고유 기능).** DQ 전송경로(링크)의 비트 에러를 parity 로 보호합니다(Write Link ECC=MR22 OP[5:4], Read=OP[7:6]; 활성 시 RDQS_t 핀이 write 동안 parity 로 동작). On-die ECC 가 셀 내부 비트(셀 누설/미세화 결함)를 보호하는 것과 달리, Link ECC 는 채널/신호 무결성(SI) 결함을 담당하므로 **보호 대상이 다른 직교(orthogonal) 기법** 입니다.

**5. 다양한 저전력 모드.** Deep Sleep(CK 정지, Self-Refresh 유지), **PASR**(Partial Array Self-Refresh — 사용 중인 array 영역만 self-refresh 하고 미사용 영역은 refresh 를 생략해 전력 대폭 절감), Per-bank Refresh(bank 단위 refresh) 를 제공합니다.

#### 모바일 SoC 에서의 LPDDR5 통합

모바일 SoC 에서 LPDDR5 는 AP(CPU) 위에 **PoP(Package on Package)** 로 적층되고, Memory Controller 는 AP 내부에 통합됩니다. 부팅 흐름은 `BootROM → BL2(DRAM Training) → OS` 이며, DRAM 초기화(Training)를 BootROM 이 아니라 **BL2 가 수행** 하는 이유는 Training 이 복잡하고 PVT(공정/전압/온도)에 의존하여 코드가 크고 자주 바뀌기 때문입니다. LPDDR5 Training 의 특이사항은 다음과 같습니다.

- **WCK2CK Training**: WCK 와 CK 간 위상 정렬 (LPDDR4 의 DQS 방식에는 없던 단계).
- **CBT (Command Bus Training)**: CA 핀 타이밍 정렬.
- **DVFSC 전환 시**: 재Training 또는 저장된 tap 값 복원이 필요.

### 5.8 DBI (Data Bus Inversion) — 전력 절감 기법

고속으로 데이터를 전송할 때 DQ 핀이 0 과 1 사이를 자주 전환하면 스위칭 전류가 늘어나 전력을 낭비하고 동시 스위칭 노이즈(SSN)가 커집니다. DBI 는 이 문제를 "비트를 반전시키는" 매우 단순한 아이디어로 해결합니다. 전송할 8비트 중 '1' 이 5개 이상이면 전체를 반전하여 '1' 의 개수를 항상 4개 이하로 유지함으로써 스위칭 횟수를 줄입니다. 반전 여부는 DBI# 핀 하나로 수신측에 알려 주므로 데이터를 그대로 복원할 수 있습니다. 추가 핀 한 개로 약 15% 전력을 아끼는 "공짜 점심" 에 가까운 기법으로, LPDDR5 에서 활용됩니다.

DBI 에는 두 가지 모드가 있습니다.

- **DC-DBI**: 전송 데이터에서 '1' 의 개수 자체를 최소화 → 종단 전류(전력) 절감.
- **AC-DBI**: 이전 데이터 대비 비트 전환 횟수를 최소화 → SSN(동시 스위칭 노이즈) 감소.

```
DBI 원리 예시 (DC-DBI, 8-bit):
  원본:     11110111  (1이 7개 → 스위칭 많음)
  DBI 적용: 00001000  (1이 1개) + DBI# = 0 (반전했음을 표시)
  수신측:   DBI# = 0 이면 비트 반전하여 원본 복원
```

### 5.9 Mode Register — DRAM 설정의 핵심

DRAM 이 제 역할을 하려면 Burst Length, Read/Write Latency, ODT 값 등 수많은 동작 파라미터를 사전에 설정해야 합니다. 이 설정을 담는 것이 Mode Register 이고, LPDDR5 는 MC 가 **MRW(Mode Register Write)** 로 쓰고 **MRR(Mode Register Read)** 로 읽습니다. Training 결과(VREF/DCA 값 등)도 MRW 를 통해 DRAM 에 최종 반영되므로, 초기화 순서 중 MR 발행 순서가 JEDEC 스펙(JESD209-5)에 명시되어 있을 만큼 중요합니다.

LPDDR5 에서 특히 알아 둘 Mode Register 는 다음과 같습니다.

| MR | 역할 | 왜 중요한가 |
|----|------|------|
| **MR16** | **FSP(Frequency Set Point)** 선택 | DVFSC gear 전환의 핵심 — 주파수/전압 세트를 고름 |
| **MR21** | **Data Copy** enable | 저전력 인코딩(§5.7-3) |
| **MR22** | **Link ECC** enable (Write OP[5:4] / Read OP[7:6]) | DQ 링크 비트 보호(§5.7-4) |
| MR0~MR수십 | Burst Length, RL/WL, ODT, WCK 설정, VREF/DCA 등 | 기본 동작 파라미터 + training 결과 반영 |

:::note[면접 포인트 — Mode Register]
- "LPDDR5 는 MRW/MRR 명령으로 RL/WL, ODT, WCK 비율, VREF 등을 프로그래밍한다."
- "초기화 시퀀스에서 MR 설정 순서가 중요 — JEDEC(JESD209-5)에 정의."
- "Training 결과(VREF/DCA 값 등)도 MRW 로 DRAM 에 반영되고, DVFSC gear 는 MR16(FSP)로 전환한다."
:::

### 5.10 Q&A — 자주 묻는 질문

**Q: LPDDR5 가 직전 세대 LPDDR4 대비 빠른/좋아진 핵심 이유는?**
> "네 가지: (1) 속도 자체가 4267 → 6400+ MT/s 로 상승. (2) CK/WCK 클럭 분리로 데이터 버스만 고속화하여 전력 대비 대역폭 개선. (3) Bank Group 도입(BG 모드) — 연속 접근을 다른 BG 로 분산하면 tCCD_S 로 이어붙여 인터리빙 효율 향상. (4) On-die + Link ECC 로 데이터 무결성 강화. 다만 tRCD/tCL(절대 ns)은 세대가 바뀌어도 크게 줄지 않으므로 랜덤 접근 지연은 대역폭만큼 개선되지 않는다."

**Q: Row Hit/Miss/Conflict의 성능 차이는?**
> "Row Hit은 이미 열린 Row에 접근하므로 tCL만 필요(가장 빠름). Row Miss는 빈 Row Buffer에 새 Row를 여는 tRCD가 추가. Row Conflict는 열린 Row를 닫는 tRP + 새 Row를 여는 tRCD가 모두 필요(가장 느림). Memory Controller의 핵심 목표는 Row Hit 비율을 극대화하는 스케줄링이다."

**Q: LPDDR5 의 On-die ECC 와 Link ECC 는 어떻게 다른가?**
> "둘은 보호 대상이 직교한다. On-die ECC는 DRAM 칩 내부에서 셀 비트 에러를 자동 수정하며 외부(MC/호스트)에 투명하다(디바이스 의존). 단 워드 내 1-bit만 수정하므로 multi-bit/chipkill 급 결함에는 여전히 상위(시스템) ECC 가 필요하다. **Link ECC**(LPDDR5 고유)는 셀이 아니라 DQ 전송경로(링크)의 비트를 parity 로 보호하는 별개의 직교 기법이다 — On-die(셀 누설/미세화 결함) vs Link(채널/SI 결함)로 담당이 다르다. MR22 로 Write/Read Link ECC 를 각각 enable 한다."

**Q: Prefetch 아키텍처란? LPDDR5 는 왜 16n 인가?**
> "DRAM 내부 셀 어레이는 수백 MHz로 느리지만, 데이터 I/O(WCK)는 수 GHz로 빠르다. Prefetch는 내부에서 한 번에 여러 비트를 읽어와 외부에서 고속으로 순차 전송하는 방식이다. LPDDR5는 16n Prefetch(BL16)로 한 번의 column access 에서 16비트를 가져와 WCK 8사이클(양 에지)에 내보낸다(BL32도 지원). 16n 은 LPDDR4부터 도입되었고, 내부의 느린 셀 속도를 고속 WCK 로 감추는 것이 목적이다."

**Q: Bank Group이 존재하는 이유는?**
> "같은 Bank Group 내 Bank들은 I/O 센스 앰프와 데이터 경로를 물리적으로 공유한다. 그래서 같은 BG 내 연속 CAS는 tCCD_L(긴 간격), 다른 BG 간은 tCCD_S(짧은 간격)가 적용된다. MC 스케줄러가 연속 접근을 다른 BG로 분산하면 tCCD_S를 활용하여 대역폭을 극대화할 수 있다. LPDDR5 에서는 BG 계층이 BG 모드에서만 존재하며, 8B/16B 모드에서는 BG 구분이 사라진다."

**Q: LPDDR5에서 WCK가 CK와 분리된 이유는?**
> "LPDDR5는 명령 버스(CK)와 데이터 버스(WCK)의 클럭을 분리했다. 명령은 상대적으로 저속으로 충분하므로 CK는 낮은 주파수, WCK는 CK의 2배 또는 4배 주파수로 데이터만 고속 전송한다. 이를 통해 불필요한 고속 토글을 줄여 전력을 절감하면서도 데이터 대역폭을 확보한다. DVFSC와 결합하면 부하에 따라 WCK 주파수를 동적으로 변경하여 추가 절전이 가능하다."

---

## 6. 흔한 오해 와 DV 디버그 체크리스트

### 흔한 오해

:::danger[❓ 오해 1 — 'LPDDR 세대 = 속도만 ↑']
**실제**: LPDDR 의 세대 변화는 속도뿐 아니라 _아키텍처_ 변화입니다 — LPDDR4→LPDDR5 에서 전용 WCK 도입, Bank Group(모드) 추가, On-die + Link ECC, DVFSC gear 등이 함께 바뀌었습니다. "double data rate" 라는 이름은 그대로지만 내부는 세대마다 다른 동물.<br>
**왜 헷갈리는가**: 약자 의미만 보고 "double rate" 하나로 단순화하기 쉬움.
:::
:::danger[❓ 오해 2 — 'Open-page 정책이 항상 좋다']
**실제**: Open-page 는 row hit 시 빠르지만 row conflict 시 `tRP+tRCD` 가 직렬로 들어가 페널티가 큽니다. workload 가 random 이거나 working set 이 row buffer 보다 훨씬 크면 close-page 가 더 좋을 수 있습니다.<br>
**왜 헷갈리는가**: "row 열어 두면 다음에 빠름" 만 직관에 강하게 남고, conflict 페널티는 평균 BW 통계에 가려짐.
:::
:::danger[❓ 오해 3 — 'Refresh 는 그냥 주기적인 housekeeping. 큰 영향 없음']
**실제**: refresh 는 tRFC(밀도 의존, 수백 ns) 동안 해당 bank 를 묶어 BW 와 worst-case latency tail 에 직접 영향을 줍니다. LPDDR5 는 이를 완화하려고 **per-bank refresh**(한 bank 만 refresh, 나머지는 사용)와 **PASR**(빈 array 는 refresh 생략)를 제공합니다.
:::
:::danger[❓ 오해 4 — 'On-die ECC 가 있으니 상위 ECC 는 불필요' / 'On-die ECC = Link ECC']
**실제**: LPDDR5 의 on-die ECC 는 _word 안에서 1-bit_(셀 내부 비트)만 수정합니다. multi-bit 에러나 칩 단위 fail(chipkill)은 여전히 상위(시스템) SECDED 가 필요합니다. 또한 **Link ECC**(LPDDR5 고유)는 on-die ECC 와 다른 기법입니다 — Link ECC 는 DQ 전송경로(링크)의 비트를, on-die ECC 는 셀 내부 비트를 보호하는 직교 관계입니다.
:::
:::danger[❓ 오해 5 — 'tCL cycle 수가 작은 설정이 무조건 빠르다']
**실제**: tCL 은 _cycle_ 단위이고 절대 시간 = `tCL × tCK`. LPDDR5 는 gear 마다 tCK 가 달라 같은 ns 제약도 cycle 수가 달라집니다 — 낮은 gear 에서 tCL cycle 수가 작아 보여도 tCK 가 크면 절대 ns 는 오히려 클 수 있습니다. 비교는 항상 절대 ns 로.
:::
### DV 디버그 체크리스트 (DRAM 셀/타이밍 레이어에서 자주 보는 실패)

| 증상 | 1차 의심 | 어디 보나 |
|---|---|---|
| Random read 시 silent data corruption (특정 row 만) | Refresh 누락 / tREFI 위반 / Row Hammer | `tREFI` 타이밍 체커, deferred refresh 카운터, refresh 발행 timestamp |
| Throughput 정상 같다가 특정 패턴에서 급락 | tFAW window 4-ACT 한도 초과 직전 stall | sliding tFAW window 안 ACT 카운트, bank 분포 |
| Read 데이터 왔는데 값이 깨짐 (1-bit 패턴) | LPDDR5 on-die ECC 미커버 비트 (multi-bit) | 같은 word 안 1-bit 인지, ECC syndrome 로그 |
| 같은 row 재접근인데 RD latency 가 spec 보다 큼 | Open Row 가 다른 conflict 로 PRE 됨 (open-page 정책) | bank state tracker, open-row 변경 timestamp |
| MRW 후 ACT/RD 동작 이상 | tMRD/tMRW 경과 전 명령 발행 | MRW 직후 tMRD 경과 시간(ns) 체크 |
| 특정 gear 에서만 fail | WCK2CK alignment / DVFSC 전환 시 retraining 누락 | WCK phase, DVFSC FSM 상태, gear 전환 timestamp |
| BL16 인데 BL8 만 받음 | Burst Chop (BC8) 의도/미의도 | MR0 BL field, RD with BC8 modifier |
| 특정 bank group 에서만 throughput 저하 | tCCD_L vs tCCD_S 매핑 misalignment | address mapper 의 bank-group bit, scheduler 내 BG 추적 |

:::caution[실무 주의점 — tREFI 초과 시 Row Hammer 취약점 노출]
**현상**: Refresh 간격(LPDDR5 tREFI ≈ 3.9μs, 온도 가변) 내에 같은 Row를 반복 ACT/PRE하면 인접 Row의 전하가 누설되어 비트 플립 발생. 보안 공격 및 데이터 손상으로 이어짐.

**원인**: MC가 트래픽 집중 구간에서 Refresh를 지연시키거나, Deferred Refresh 횟수가 JEDEC 허용 한도를 초과할 때 발생. LPDDR5 의 RFM(Refresh Management) 미구현 시 Row Hammer 방어가 무력화됨.

**점검 포인트**: 타이밍 체커(절차적 SV)에서 `tREFI` 위반 감시가 동작하는지 확인. 로그에서 Deferred Refresh 누적 카운터가 허용 한도를 초과하는 시점 탐색. LPDDR5 시뮬 모델에서 RFM 관련 레지스터(Row Activation 임계값) 설정값 검증.
:::
---

## 7. 핵심 정리 (Key Takeaways)

- **Cell = capacitor + access transistor** — 누설되므로 refresh 필수, 읽으면 파괴되므로 restore 필수.
- **계층 구조**: Rank → Bank Group → Bank → Row → Column. Bank 는 동시에 여러 개 active 가능 → parallelism 의 원천.
- **명령 시퀀스**: ACT(row open) → RD/WR (col access) → PRE(close) → REF(주기). 각 단계 timing 종속 (`tRCD`, `tCL`, `tRP`, `tRAS`, `tRC`, `tRFC`, `tREFI`).
- **Row Hit / Miss / Conflict** = MC 의 가장 큰 성능 lever — Hit 비율 ≈ effective BW.
- **LPDDR5 정체성**: CK/WCK 클럭 분리(WCK:CK 2:1/4:1) + bank mode(BG/8B/16B, 최대 16뱅크) + VDDQ 0.5V + On-die ECC + **Link ECC(고유)** + PASR + DVFSC gear + PoP.
- **LPDDR4 → LPDDR5(직전 세대 차이)**: WCK 도입(LPDDR4 는 DQS) + Bank Group 도입 + On-die/Link ECC + PASR + DVFSC.

:::caution[실무 주의점]
- "LPDDR5 빠르다" 는 **prefetch(16n) + double data rate + bank parallelism** 의 곱. 하나라도 빠지면 nominal BW 미달.
- **Open-page 가 항상 좋지 않다** — workload 의 row reuse rate 가 낮으면 close-page 가 더 좋을 수 있음.
- **On-die ECC ≠ 시스템 ECC** — 셀 내부 1-bit 한정. multi-bit 보호는 상위(시스템) SECDED 가 책임.
:::
### 7.1 자가 점검

:::tip[🤔 Q1 — Refresh 비용 계산 (Bloom: Apply)]
LPDDR5 의 평균 _tREFI ≈ 3.9 µs_, refresh 1회당 `tRFC` 를 밀도별 수백 ns 라 하자. _Refresh 가 차지하는 시간 비율_ 은 대략 얼마이고, LPDDR5 는 이를 어떻게 낮추나?

<details>
<summary>정답</summary>

- 예: `tRFC ≈ 200 ns` 라면 비율 ≈ 200 / 3900 = **~5%** (all-bank 가정).
- LPDDR5 는 **per-bank refresh(REFpb)** 로 한 bank 만 묶고 나머지는 계속 사용 → 유효 BW 손실 감소.
- **PASR** 로 빈 array 영역은 refresh 자체를 생략 → refresh 전력·오버헤드 추가 절감.

핵심: refresh 오버헤드는 `tRFC / tREFI` 로 근사하며, per-bank + PASR 가 이를 낮춘다.

</details>
:::
:::tip[🤔 Q2 — Row buffer locality (Bloom: Analyze)]
Workload 의 _row reuse rate 90%_ vs _10%_. Open-page vs close-page?

<details>
<summary>정답</summary>

- **90% reuse**: Open-page 압도. 다음 access 가 같은 row 일 확률 큼 → row hit (1 cycle).
- **10% reuse**: Close-page 우월. 같은 row 안 옴 → 미리 close 하면 다음 access 의 PRE 비용 절감.

Memory controller 는 _workload 측정_ 후 policy 동적 전환 가능.

</details>
:::
### 7.2 출처

**External**
- JEDEC **JESD209-5** *LPDDR5/5X* (본 코스 주 근거)
- *DRAM Refresh Mechanisms* — academic survey
- Mutlu et al. *Row Hammer* papers

---

## 다음 모듈

→ [Module 02 — Memory Controller](../02_memory_controller/): 이 모듈의 ACT/RD/WR/PRE/REF 명령들이 _어떻게_ 스케줄되는가. FR-FCFS, Bank Parallelism, Write Batching, QoS, Refresh 최적화.

[퀴즈 풀어보기 →](../quiz/01_dram_fundamentals_ddr_quiz/)

