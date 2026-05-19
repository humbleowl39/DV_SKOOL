# Ch02. 패키지·핀아웃·어드레싱

<div class="chapter-context" data-cat="memory">
  <a class="chapter-back" href="index.md"><span class="chapter-back-arrow">←</span><span class="chapter-back-icon">📚</span> DRAM JEDEC Deep-Dive</a>
  <span class="chapter-divider">›</span>
  <span class="chapter-marker">CH 02</span>
</div>

## 🎯 Learning Objectives

- **Identify**: DDR4/DDR5의 ball pitch, ballout, x4/x8/x16 organization을 식별한다.
- **Compare**: LPDDR4 다중 패키지 옵션(POP, MCP, Discrete)과 LPDDR5의 패키지 진화를 비교한다.
- **Decompose**: DDR5 어드레싱(Bank Group × Bank × Row × Column)을 분해해 cycle 단위 access path를 추적한다.
- **Apply**: BG/Bank/Row/Column 4축에 대한 coverage covergroup 골격을 작성한다.

## Prerequisites

- [Ch01. JEDEC 표준 지형도](01_dram_jedec_landscape.md)
- 용어: Bank Group, Bank, Row, Column, BL16, BL32

## 1. 왜 패키지·핀아웃이 DV에 중요한가

DV 엔지니어가 testbench에서 다루는 *interface*는 결국 *물리 핀의 추상화*입니다. DDR5의 2-cycle command는 CA[6:0] 핀이 2클럭에 걸쳐 *서로 다른 정보*를 전달한다는 의미이며, 이는 monitor와 driver의 sampling 시점을 결정합니다.

또한 controller IP가 *configurable* 한 경우, 같은 RTL이 *다른 ballout/organization* (x4 vs x8 vs x16)을 지원할 수 있습니다. 이 경우 DV는 각 organization마다 *별도 sanity*와 *cross coverage*를 준비해야 합니다.

---

## 2. DDR4 패키지·핀아웃 — 기준점

> 출처: JESD79-4D §2

### 2.1 Ball pitch와 organization

- Ball pitch: **0.8 mm × 0.8 mm**
- x4/x8: 13 electrical rows × 6 electrical columns (2 sets of 3)
- x16: 16 electrical rows
- 표준 ballout: MO-207 (x4/x8), x16 별도

### 2.2 핵심 신호 핀

| 신호 | 폭 | 역할 |
|---|---|---|
| CK_t / CK_c | 1 pair | 차동 클럭 |
| CKE | 1 | Clock Enable (low-power 진입/탈출) |
| CS_n | 1 (rank별) | Chip Select |
| ACT_n | 1 | Activate (DDR4부터 분리) |
| RAS_n / CAS_n / WE_n | 각 1 | DDR4에서는 ADDR과 multiplex되어 16/15/14 핀에 위치 |
| A[17:0], BG[1:0], BA[1:0] | — | Address + Bank Group + Bank |
| DQ, DQS_t/c, DM_n/DBI_n | x4/x8/x16 | Data + strobe + mask/inversion |
| ODT | 1 | On-Die Termination control |
| ALERT_n | 1 | CA Parity / CRC error 알림 |
| ZQ | 1 | ZQ Calibration reference |
| RESET_n | 1 | Asynchronous reset |

### 2.3 DDR4 Bank/Bank Group 구조

- 4 Bank Groups (BG[1:0])
- BG당 4 Banks (BA[1:0])
- 총 16 banks per device

```
DDR4 Device
├── BG0
│   ├── Bank 0, 1, 2, 3
├── BG1
├── BG2
└── BG3
```

!!! info "DV 시사점 — BG의 의의"
    BG가 다르면 `tCCD_S` (Short), 같으면 `tCCD_L` (Long) 적용. DV에서 BG-aware command sequencing이 필요한 이유.

---

## 3. DDR5 패키지·핀아웃 — 결정적 변화

> 출처: JESD79-5C.01 v1.31 §2

### 3.1 Ball pitch와 organization

- 표준 ballout: **MO-210**
- x4/x8 (§2.4), x16 (§2.5)
- 핀 수 증가 — Channel A/B 분리로 인한 데이터 경로 2배

### 3.2 핵심 변화 — Two Independent Channels per DIMM

```
DDR5 DIMM (Server)
├── Channel A (32-bit data) ─┬─ Subchannel A0 (x4 or x8)
│                            └─ Subchannel A1
└── Channel B (32-bit data) ─┬─ Subchannel B0
                             └─ Subchannel B1
```

- 각 channel은 *독립적인* address/command bus
- 64-bit DIMM은 *논리적으로* 32-bit × 2 channels
- BL16 burst → 채널당 16 beats × 32-bit = 64 bytes / cache line

### 3.3 핵심 신호 핀 (DDR4와 비교)

| 신호 | DDR4 | DDR5 | 비고 |
|---|---|---|---|
| CK_t/c | per device | per subchannel | channel 분리 |
| CS_n | per rank | per rank + per subchannel | 더 세분화 |
| CA[6:0] | — | **CA[6:0]** | DDR5는 multiplexed 7-bit CA |
| CA[13:0] (UI) | — | 2-cycle 결합 시 effective 14-bit | UI 단위 |
| ACT/RAS/CAS/WE | 분리 | CA에 인코딩 | DDR5는 OPCODE 형태 |
| DQS_t/c | bit-level | byte-level (x4 grouped) | DDR5는 DQ4비트별 |
| DM_n | 1 | (없음 — DCA로 대체) | DDR5는 별도 DM 없음 |
| DBI | DDR4 옵션 | (변경) | DDR5 spec 참조 |
| ALERT_n | 1 | 1 | 동일 역할 |
| RFM signaling | — | command-encoded (MR58) | 명령 인코딩 |

!!! tip "DDR5의 2-cycle command — DV가 가장 주의할 것"
    DDR5 command는 `CA[6:0]` 핀 7개를 *2 클럭에 걸쳐* 전송. 첫 cycle은 OPCODE + 일부 ADDR, 둘째 cycle은 나머지 ADDR. monitor는 *2 클럭 윈도우*를 보고 command를 reconstruct해야 합니다.

### 3.4 DDR5 Bank/Bank Group

- **8 Bank Groups** (BG[2:0])
- BG당 4 Banks (per channel)
- 채널당 총 32 banks (8 BG × 4 Bank)

> 출처: JESD79-5C.01 §2.7

---

## 4. LPDDR4 패키지 옵션 — 모바일의 다양성

> 출처: JESD209-4E §2

LPDDR4는 *패키지 옵션이 매우 많은* 것이 특징입니다. 같은 die라도 다른 ball arrangement로 다른 시스템에 들어갑니다.

### 4.1 대표 패키지 (선택 인용)

| 패키지 | 비고 |
|---|---|
| 272 Ball Quad-Channel POP | AP/SoC와 PoP (Package-on-Package) — 스마트폰 SoC |
| 200 Ball Two-Channel FBGA | 단독 패키지 |
| 432 Ball x64 HDI Discrete | High-density independent |
| 254 Ball eMMC MCP | Multi-Chip Package — eMMC와 결합 |
| 254 Ball UFS MCP | UFS와 결합 |

### 4.2 LPDDR4 의 Dual-Channel Die

LPDDR4 die는 *기본적으로 dual-channel*. 각 channel은 16-bit. SoC가 2개 channel을 양쪽에서 access 가능.

```
LPDDR4 Die (Dual Channel)
├── Channel A (x16)
│   ├── 8 banks
│   └── DQ_A[15:0], CA_A[5:0], CK_A_t/c, CKE_A, CS_A
└── Channel B (x16)
    ├── 8 banks
    └── DQ_B[15:0], CA_B[5:0], CK_B_t/c, CKE_B, CS_B
```

!!! info "DV 시사점 — channel independence"
    채널 A와 채널 B는 *완전히 독립적*. 채널 A가 self-refresh 중에도 채널 B는 정상 동작 가능. DV scenario에서 *cross-channel 독립성*을 cover해야 합니다.

---

## 5. LPDDR5 패키지·핀아웃 — WCK의 등장

> 출처: JESD209-5C §2.2~2.3

### 5.1 핵심 변화 — WCK 추가

```
LPDDR4 핀 패밀리:
  CK_t/c, CKE, CS, CA, DQ, DQS, ZQ, RESET, ODT_CA

LPDDR5 추가:
  WCK_t/c     ← Write Clock (data와 동기)
  RDQS_t/c    ← Read DQS (LPDDR4의 DQS 역할 분리)
```

WCK는 **CK 대비 빠른 클럭** (예: CK=400MHz, WCK=1.6GHz, 4× ratio). 데이터 전송 시점에 WCK가 사용되고, CK는 command 전송용으로 분리됩니다.

### 5.2 LPDDR5 Bank 구조 — 3가지 모드

LPDDR5는 *bank organization을 mode register로 선택* 가능:

| 모드 | 구성 | 적용 |
|---|---|---|
| 16 banks mode | 16 banks (no BG) | 호환성 우선 |
| 8 banks mode | 8 banks | 일부 LPDDR5X 제외 |
| BG mode | 4 BG × 4 banks = 16 banks | DDR5와 유사 |

> 출처: JESD209-5C §2.2.3.1

!!! tip "DV 시사점 — bank mode 전환 검증"
    Bank mode 전환은 *재초기화* 시점에만 가능합니다. 검증 환경에서는 각 모드별로 *별도 testbench config* + bank mode를 *covergroup의 bin*으로 추가.

---

## 6. 어드레싱 — Bank Group × Bank × Row × Column

### 6.1 DDR5 어드레싱 분해 (대표)

DDR5의 예시 (16Gb x8 device 가정):

| 차원 | 비트 수 | 비고 |
|---|---|---|
| Bank Group (BG) | 3 | 8 BG |
| Bank (BA) | 2 | per BG |
| Row | 17 | 128K rows per bank |
| Column | 10 | 1K columns per row (BL16 기준) |

총 = BG[2:0] + BA[1:0] + Row[16:0] + Col[9:0] = 32-bit logical address

> 정확한 비트 수는 device 용량(8Gb/16Gb/32Gb)과 organization(x4/x8/x16)에 따라 다릅니다. JESD79-5C §2.7 표를 참조하세요.

### 6.2 Address path 추적 — 한 cycle씩

DDR5에서 "row 0x12345 of bank 3 of BG 2, column 0x80" 을 read 한다고 가정:

```
[Cycle 0-1] ACT command (2-cycle)
  CA[6:0] cycle 0: OPCODE=ACT, BG[2:0]=3'b010, BA[1:0]=2'b11
  CA[6:0] cycle 1: ROW[16:0]=17'h12345 (분할 인코딩)

[Cycle 2..(2+tRCD-1)] Wait
  → no command on CA (tRCD 시간 동안 row buffer activation)

[Cycle 2+tRCD, +1] RD command (2-cycle)
  CA[6:0] cycle 0: OPCODE=RD, BG=2, BA=3
  CA[6:0] cycle 1: COL[9:0]=10'h080
                    AP=0 (no auto-precharge)

[Cycle 2+tRCD+CL .. +CL+BL/2-1] DQ valid
  → BL16 burst on DQ
```

> CL = CAS Latency. DDR5에서 CL은 MR0에 설정. tCK 단위로 표기.

### 6.3 BL16 vs BL32 — 언제 무엇을 쓰는가

- **BL16**: 표준. DDR5/LPDDR5의 기본 burst length.
- **BL32**: 옵션 (DDR5 §4.2.1). 한 번의 명령으로 두 배 데이터 전송 — 더 긴 burst, 더 적은 command overhead. 단, *interrupt*가 어려움 (긴 burst 중간에 다른 bank를 access 못함).

| 시나리오 | 권장 BL |
|---|---|
| 일반 GP traffic, cache line = 64B | BL16 |
| 큰 sequential read (예: DMA copy) | BL32 |
| Latency-sensitive, frequent bank switch | BL16 |
| Bandwidth-sensitive, sequential | BL32 |

---

## 7. DV 적용 — Coverage 모델 골격

### 7.1 BG/Bank/Row/Column 4축 coverage

```systemverilog
// covergroup: DDR5 address access coverage
// 출처: JESD79-5C.01 §2.7 (어드레싱 기준)
covergroup ddr5_addr_cg with function sample (
    bit [2:0] bg,
    bit [1:0] ba,
    bit [16:0] row,
    bit [9:0]  col
);
    option.per_instance = 1;
    option.name = "ddr5_addr_cg";

    cp_bg: coverpoint bg {
        bins each_bg[] = {[0:7]};
    }
    cp_ba: coverpoint ba {
        bins each_ba[] = {[0:3]};
    }
    cp_row: coverpoint row {
        bins low_rows  = {[17'h00000 : 17'h00FFF]};
        bins mid_rows  = {[17'h01000 : 17'h0EFFF]};
        bins high_rows = {[17'h0F000 : 17'h1FFFF]};
    }
    cp_col: coverpoint col {
        bins col_low   = {[10'h000 : 10'h0FF]};
        bins col_mid   = {[10'h100 : 10'h2FF]};
        bins col_high  = {[10'h300 : 10'h3FF]};
    }

    // Cross — BG × Bank 는 다양한 bank 조합이 다 갔는지
    cx_bg_ba: cross cp_bg, cp_ba;
endgroup
```

!!! warning "coverage 함정 — 모든 row를 bin으로 만들면"
    Row가 17-bit (=128K)이고 각 bin = 1 row 이면 *128K bins*. 시뮬레이션 성능과 coverage report 모두 폭발합니다. **range bin**으로 묶고, 특별히 검증해야 할 row만 *named bin*으로 추가하세요.

### 7.2 x4/x8/x16 organization coverage

```systemverilog
typedef enum {ORG_X4, ORG_X8, ORG_X16} dram_org_e;

covergroup ddr5_org_cg with function sample (dram_org_e org);
    cp_org: coverpoint org {
        bins x4  = {ORG_X4};
        bins x8  = {ORG_X8};
        bins x16 = {ORG_X16};
    }
endgroup
```

### 7.3 Channel-independence coverage (DDR5 / LPDDR4 / LPDDR5)

```systemverilog
// 두 channel에서 동시에 활동 (또는 한쪽만 활동) 패턴
covergroup chan_activity_cg with function sample (bit ch_a_active, bit ch_b_active);
    cp_pattern: coverpoint {ch_a_active, ch_b_active} {
        bins both_active = {2'b11};
        bins ch_a_only   = {2'b10};
        bins ch_b_only   = {2'b01};
        bins both_idle   = {2'b00};
    }
endgroup
```

---

## 8. 대표 문제 — DDR5 어드레스 dry-run

!!! question "Q. DDR5 16Gb x8 device, BG=3'b101, BA=2'b10, Row=17'h0_ABCD, Col=10'h040, BL16. ACT→RD 시퀀스의 cycle-by-cycle CA 동작을 추적하라. tRCD=14 nCK, CL=22 nCK, tCK=0.5ns 가정."

???+ answer "풀이 (사고 과정 + cycle dry-run)"

    **Step 1 — 명령 인코딩 확인**

    DDR5 2-cycle command (출처: JESD79-5C.01 §4.1):
    - ACT: 2 cycles에 걸쳐 CA[6:0]에 인코딩
    - RD: 마찬가지로 2 cycles

    **Step 2 — Cycle 추적**

    | nCK | 시간(ns) | CA[6:0] | 설명 |
    |---|---|---|---|
    | 0 | 0.0 | ACT_op[1] + BG[2:0]=101 + BA[1:0]=10 + Row 일부 | ACT 1st cycle |
    | 1 | 0.5 | ACT_op[2] + Row 나머지 (Row=0_ABCD) | ACT 2nd cycle |
    | 2..13 | 1.0..6.5 | NOP | tRCD 대기 (14 nCK) |
    | 14 | 7.0 | NOP | tRCD 막 만료, 아직 1 cycle 더 |
    | 16 | 8.0 | RD_op[1] + BG=101 + BA=10 + Col 일부 | RD 1st cycle |
    | 17 | 8.5 | RD_op[2] + Col 나머지 (Col=0x040) + AP=0 | RD 2nd cycle |
    | 18..37 | 9.0..18.5 | — | CL=22 대기 (data 도착 전) |
    | 38..45 | 19.0..22.5 | — | DQ valid (BL16 = 8 nCK 동안) |

    > 정확한 timing은 speed grade와 MR 설정에 따라 다릅니다 (DDR5 speed bin 표 참조).

    **Step 3 — DV 함의**

    - Monitor는 *2-cycle 윈도우*를 모아 ACT 명령을 reconstruct
    - Scoreboard는 ACT의 `(BG, BA, Row)` 와 후속 RD의 `(BG, BA, Col)` 가 일치하는지 검증
    - SVA: `tRCD` 위반 (ACT 후 14 nCK 이전에 RD 발생) → assertion fail
    - covergroup `ddr5_addr_cg` 에 `bg=5, ba=2, row=0_ABCD, col=0x040` sample 호출 → `cp_bg.each_bg[5]`, `cp_ba.each_ba[2]`, `cp_row.mid_rows`, `cp_col.col_low` 모두 hit

---

## 9. 핵심 정리 (Key Takeaways)

- DDR5는 *DIMM당 2 channels* 분리. 각 channel은 독립적 address/command bus.
- DDR5 command는 *2 cycles에 걸쳐* CA[6:0]에 인코딩 — monitor sampling window 2배 확장 필요.
- DDR5 Bank Group은 *8개*, BG당 4 banks (channel당). `tCCD_L` vs `tCCD_S` 가 BG 동일성에 따라 적용.
- LPDDR4는 dual-channel die가 기본 — 채널 독립성을 cover해야 함.
- LPDDR5는 WCK/RDQS 도입 — data 클럭이 CK와 분리 (CK=command, WCK=data).
- LPDDR5 Bank mode가 3가지 (16/8/BG mode) — MR 설정으로 전환, 재초기화 필요.
- Coverage에서 Row를 *range bin*으로 묶지 않으면 폭발. 4축(BG/BA/Row/Col)을 균형 있게.

## 10. Further Reading

- 이전: [Ch01. DRAM 기본 원리와 JEDEC 표준 지형도](01_dram_jedec_landscape.md)
- 다음: [Ch03. 초기화·Reset·Power 시퀀스](03_init_reset_power.md)
- 부록: [JEDEC Spec 빠른 참조](appendix_a_quick_reference.md)
- 퀴즈: [Ch02 퀴즈](quiz/ch02_quiz.md)

<div class="chapter-nav">
  <a class="nav-prev" href="01_dram_jedec_landscape.md">
    <div class="nav-label">← 이전</div>
    <div class="nav-title">Ch01. JEDEC 표준 지형도</div>
  </a>
  <a class="nav-next" href="03_init_reset_power.md">
    <div class="nav-label">다음 →</div>
    <div class="nav-title">Ch03. 초기화·Reset·Power</div>
  </a>
</div>
