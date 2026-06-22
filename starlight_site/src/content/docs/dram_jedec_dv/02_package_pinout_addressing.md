---
title: "Ch02. 패키지·핀아웃·어드레싱"
---

<div class="chapter-context" data-cat="memory">
  <a class="chapter-back" href="../"><span class="chapter-back-arrow">←</span><span class="chapter-back-icon">📚</span> DRAM JEDEC Deep-Dive</a>
  <span class="chapter-divider">›</span>
  <span class="chapter-marker">CH 02</span>
</div>

## 🎯 Learning Objectives

- **Identify**: DDR4/DDR5의 ball pitch, ballout, x4/x8/x16 organization을 식별한다.
- **Compare**: LPDDR4 다중 패키지 옵션(POP, MCP, Discrete)과 LPDDR5의 패키지 진화를 비교한다.
- **Decompose**: DDR5 어드레싱(Bank Group × Bank × Row × Column)을 분해해 cycle 단위 access path를 추적한다.
- **Apply**: BG/Bank/Row/Column 4축에 대한 coverage covergroup 골격을 작성한다.

## Prerequisites

- [Ch01. JEDEC 표준 지형도](../01_dram_jedec_landscape/)
- 용어: Bank Group, Bank, Row, Column, BL16, BL32

## 1. 왜 패키지·핀아웃이 DV에 중요한가

DV 엔지니어가 testbench에서 다루는 interface는 결국 물리 핀의 추상화입니다. 핀 정의를 정확히 이해해야 **driver**(testbench에서 핀을 직접 흔들어 명령·데이터를 인가하는 컴포넌트)가 올바른 cycle에 올바른 핀을 drive하고, **monitor**(핀의 신호를 관찰해 트랜잭션으로 복원하는 컴포넌트)가 정확한 시점에 신호를 sampling(특정 시점의 신호값을 떠 읽는 것)할 수 있습니다. 본 자료의 주축인 LPDDR5는 CK(명령용)와 WCK(데이터용)를 분리하고 CA[6:0]를 다중 사이클로 전달하므로, monitor가 두 클럭 도메인과 CA 사이클을 정확히 따라가야 명령·주소가 올바르게 decode됩니다. 비교축인 DDR5의 2-cycle command 역시 CA[6:0] 핀이 2 클럭에 걸쳐 서로 다른 정보를 전달한다는 의미입니다. monitor가 이를 모르고 1 클럭만 capture하면 명령이 반만 decode되고, 잘못된 주소로 scoreboard가 채워지게 됩니다.

본 챕터는 비교 기준점으로 DDR4(§2)·DDR5 DIMM(§3)을 먼저 정리한 뒤, 주 검증 대상인 LPDDR4(§4)·LPDDR5(§5)의 패키지·핀·bank 구조를 다룹니다. §6 이후의 어드레싱 dry-run은 BG/Bank/Row/Column 4축 개념을 DDR5 예시로 설명하지만, 동일한 분해 방법이 LPDDR5의 BG/8B/16B 모드에도 그대로 적용됩니다.

또한 controller IP가 configurable한 경우 같은 RTL이 x4, x8, x16 등 다른 **organization**(한 DRAM 칩이 가진 DQ 데이터 핀의 폭 — x8이면 8비트 입출력)을 지원합니다. organization이 다르면 DQ 버스 폭, **DM**(data mask, 쓰기 데이터 중 일부 바이트만 무시하게 하는 마스크 신호)/**TDQS**(termination DQS, DM 핀 자리에 종단 기능을 제공하는 신호) 지원 여부, bank 구성이 모두 달라지므로, DV는 각 organization별로 별도 sanity 테스트와 cross coverage를 준비해야 합니다.

---

## 2. DDR4 패키지·핀아웃 — 기준점

> 출처: JESD79-4D §2

### 2.1 Ball pitch와 organization

**Ball pitch**(패키지 바닥의 납땜 공(ball) 사이 중심 간 거리)와 **ballout**(그 ball들에 어떤 신호를 배정했는지의 배치도)은 패키지가 보드에 어떻게 연결되는지를 규정합니다.

- Ball pitch: **0.8 mm × 0.8 mm**
- x4/x8: 13 electrical rows × 6 electrical columns (2 sets of 3)
- x16: 16 electrical rows
- 표준 ballout: MO-207 (x4/x8), x16 별도

### 2.2 핵심 신호 핀

표에 처음 나오는 신호들을 풀어 둡니다 — **차동 클럭**(두 선의 전압 차로 0/1을 판별해 잡음에 강한 클럭 쌍), **rank**(같은 CS_n 신호로 한꺼번에 선택되는 DRAM 칩 묶음), **DQS**(data strobe, 데이터가 유효한 순간을 알려주는 기준 신호), **DBI**(data bus inversion, 1의 개수가 많으면 전체를 반전해 토글·소비전력을 줄이는 기법), **ODT**(on-die termination, 신호 반사를 줄이는 칩 내장 종단 저항), **ZQ Calibration**(외부 기준 저항(보통 240 Ω)에 맞춰 출력 구동/종단 임피던스를 보정하는 절차)입니다.

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

```d2
direction: down

dev: "DDR4 Device — 16 banks" {
  grid-columns: 2
  BG0: "Bank Group 0" { grid-columns: 2; b0: Bank 0; b1: Bank 1; b2: Bank 2; b3: Bank 3 }
  BG1: "Bank Group 1" { grid-columns: 2; b0: Bank 0; b1: Bank 1; b2: Bank 2; b3: Bank 3 }
  BG2: "Bank Group 2" { grid-columns: 2; b0: Bank 0; b1: Bank 1; b2: Bank 2; b3: Bank 3 }
  BG3: "Bank Group 3" { grid-columns: 2; b0: Bank 0; b1: Bank 1; b2: Bank 2; b3: Bank 3 }
}
```

- 4 Bank Groups (BG[1:0]), BG당 4 Banks (BA[1:0]) → 총 16 banks per device

:::note[DV 시사점 — BG의 의의]
BG가 다르면 `tCCD_S` (Short), 같으면 `tCCD_L` (Long) 적용. DV에서 BG-aware command sequencing이 필요한 이유.
:::
---

## 3. DDR5 패키지·핀아웃 — 결정적 변화

> 출처: JESD79-5C.01 v1.31 §2

### 3.1 Ball pitch와 organization

- 표준 ballout: **MO-210**
- x4/x8 (§2.4), x16 (§2.5)
- 핀 수 증가 — Channel A/B 분리로 인한 데이터 경로 2배

### 3.2 핵심 변화 — Two Independent Channels per DIMM

```d2
direction: down

dimm: "DDR5 DIMM (Server) — 64-bit = 32-bit × 2 channels" {
  grid-columns: 2
  CA: "Channel A (32-bit, independent CA/cmd bus)" { grid-columns: 2; a0: "Subchannel A0 (x4/x8)"; a1: "Subchannel A1" }
  CB: "Channel B (32-bit, independent CA/cmd bus)" { grid-columns: 2; b0: "Subchannel B0 (x4/x8)"; b1: "Subchannel B1" }
}
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

:::tip[DDR5의 2-cycle command — DV가 가장 주의할 것]
DDR5 command는 `CA[6:0]` 핀 7개를 *2 클럭에 걸쳐* 전송. 첫 cycle은 OPCODE + 일부 ADDR, 둘째 cycle은 나머지 ADDR. monitor는 *2 클럭 윈도우*를 보고 command를 reconstruct해야 합니다.
:::

2-cycle command 의 본질은 **핀 수와 시간을 맞바꾼 trade-off** 입니다. DDR5 가 한 명령에 담아야 하는 정보(OPCODE + BG + BA + 더 넓어진 Row/Col 주소)는 DDR4 보다 늘었지만, JEDEC 은 명령버스 핀을 오히려 7개(CA[6:0])로 좁혔습니다. 한 클럭에 다 담으려면 14개 안팎의 CA 핀이 필요했을 정보를, 7핀 × 2클럭 = 14 슬롯으로 _시간축에 펼쳐서_ 보내는 것이 2-cycle command 입니다. 왜 굳이 핀을 줄이려 했는가 — 두 가지 이유입니다. 첫째, **핀(ball)은 곧 비용**입니다. 패키지 ball 수와 채널당 PCB 배선 수가 줄면 패키지·기판 원가와 라우팅 난이도가 내려갑니다. 둘째, **신호 무결성(SI)** 입니다. 고속에서는 나란히 달리는 평행 신호선이 많을수록 crosstalk 와 동시 스위칭 노이즈가 커지는데, CA 핀 수를 줄이면 이 잡음원이 줄어 같은 속도에서 더 깨끗한 명령버스를 얻습니다. 즉 명령버스는 데이터버스만큼 폭이 중요하지 않으므로(데이터처럼 매 beat 새 값을 쏟지 않음), 폭을 줄이고 두 클럭에 나눠 보내는 쪽이 비용·SI 면에서 이득인 것입니다.
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

표의 패키지 용어 — **POP**(package-on-package, AP/SoC 칩 위에 메모리 패키지를 얹어 쌓는 형태), **MCP**(multi-chip package, 여러 칩을 한 패키지에 담는 형태), **FBGA**(fine-pitch ball grid array, 촘촘한 ball 격자로 연결하는 패키지), **eMMC/UFS**(스마트폰에 쓰는 플래시 저장장치 규격 — 메모리와 함께 한 패키지에 묶이기도 함)입니다.

| 패키지 | 비고 |
|---|---|
| 272 Ball Quad-Channel POP | AP/SoC와 PoP (Package-on-Package) — 스마트폰 SoC |
| 200 Ball Two-Channel FBGA | 단독 패키지 |
| 432 Ball x64 HDI Discrete | High-density independent |
| 254 Ball eMMC MCP | Multi-Chip Package — eMMC와 결합 |
| 254 Ball UFS MCP | UFS와 결합 |

### 4.2 LPDDR4 의 Dual-Channel Die

LPDDR4 die는 기본적으로 dual-channel 구조입니다. 하나의 die 안에 독립적인 CA, CK, CKE, CS, DQ 버스를 각각 갖춘 두 채널이 공존하고, SoC는 두 채널을 병렬로 활용해 실질 대역폭을 두 배로 늘릴 수 있습니다.

```d2
direction: down

die: "LPDDR4 Die (Dual Channel)" {
  grid-columns: 2
  CA: "Channel A (x16)" { grid-rows: 2; banks: "8 banks"; sig: "DQ_A[15:0], CA_A[5:0]\nCK_A_t/c, CKE_A, CS_A" }
  CB: "Channel B (x16)" { grid-rows: 2; banks: "8 banks"; sig: "DQ_B[15:0], CA_B[5:0]\nCK_B_t/c, CKE_B, CS_B" }
}
```

두 채널이 완전히 독립적이라는 점이 DV에서 중요합니다. 채널 A가 self-refresh에 진입한 상태에서도 채널 B는 정상적인 read/write 명령을 수행할 수 있습니다. 따라서 시나리오 설계 시 각 채널의 독립 동작뿐 아니라, 한 채널이 전력 절약 모드에 있을 때 다른 채널이 정상 동작하는 cross-channel 독립성도 반드시 커버해야 합니다.

:::note[DV 시사점 — channel independence]
채널 A와 채널 B는 *완전히 독립적*. 채널 A가 self-refresh 중에도 채널 B는 정상 동작 가능. DV scenario에서 *cross-channel 독립성*을 cover해야 합니다.
:::
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

LPDDR4까지는 하나의 CK가 command 타이밍과 data 타이밍을 모두 담당했습니다. 그런데 데이터 전송 속도가 올라갈수록 command와 data의 클럭 요구 사항이 달라져서 단일 클럭으로 양쪽을 만족시키기 어려워졌습니다. LPDDR5는 이를 WCK를 별도로 추가함으로써 해결했습니다. CK는 command 버스 동기화에 집중하고, WCK는 데이터 전송에 특화된 빠른 클럭으로 동작합니다. WCK는 CK 대비 4× 또는 2× 빠른데(예: CK=400MHz, WCK=1.6GHz), 이 두 클럭이 정확히 정렬되어야 CAS WCK2CK Sync 비트가 의미를 갖습니다. 정렬이 틀어지면 데이터 corruption이 발생하므로 WCK2CK leveling이 필수 훈련 단계로 추가됩니다.

### 5.2 LPDDR5 Bank 구조 — 3가지 모드

LPDDR4는 BG(Bank Group)가 없는 단순한 **8 banks** 구조였습니다. LPDDR5는 mode register(MR)로 *bank organization을 선택* 가능하며, 세 가지 모드를 정의합니다:

| 모드 | 구성 | 적용 |
|---|---|---|
| 16B mode | 16 banks (no BG) | 최대 bank 병렬성 |
| 8B mode | 8 banks (no BG) | LPDDR4 호환·단순성 우선 |
| BG mode | **4 BG × 4 banks = 16 banks** | tCCD_L/tCCD_S 구분으로 대역폭 향상 |

> 출처: JESD209-5C §2.2.3.1

:::caution[흔한 오해 — BG mode ≠ DDR5 bank 구조]
LPDDR5의 **BG mode는 4 BG × 4 bank = 총 16 banks**입니다. DDR5(x4/x8)의 **8 BG × 4 bank = 32 banks**와는 BG 수도 총 bank 수도 다릅니다. "LPDDR5 BG mode가 DDR5와 유사하다"는 표현은 *BG라는 개념을 도입했다*는 점에서만 맞고, 규모는 절반입니다. 또한 LPDDR5의 16B/8B 모드에는 BG가 아예 없습니다. DV에서 bank 수·BG 수를 그대로 가정하면 어드레스 디코딩과 tCCD coverage가 어긋납니다.
:::

:::tip[DV 시사점 — bank mode 전환 검증]
Bank mode 전환은 *재초기화* 시점에만 가능합니다. 검증 환경에서는 각 모드(16B/8B/BG)별로 *별도 testbench config* + bank mode를 *covergroup의 bin*으로 추가. BG mode일 때만 tCCD_L/tCCD_S 구분이 의미를 가집니다.
:::

### 5.3 폼팩터 — LPDDR5는 DIMM이 없다

이 챕터의 §2~§3은 DDR5 **DIMM** (RCD·on-DIMM PMIC를 포함한 모듈)을 기준으로 핀아웃을 설명했습니다. 그러나 본 자료의 주축인 LPDDR5는 폼팩터 자체가 다릅니다. DV 환경 구성과 핀 모델링이 달라지므로 명확히 구분합니다.

| 항목 | DDR5 (서버/PC) | LPDDR5 (모바일 SoC) |
|---|---|---|
| 폼팩터 | DIMM (모듈 기판에 다수 DRAM 실장) | **PoP**(Package-on-Package, SoC 위에 적층) 또는 discrete/MCP |
| RCD (Registering Clock Driver) | 있음 (RDIMM/LRDIMM) | **없음** — controller가 DRAM과 직접 연결 |
| PMIC | **on-DIMM PMIC** (모듈 위 전원 IC) | **on-package PMIC 없음** — 전원은 SoC 측 PMIC가 공급 |
| Channel 위치 | 모듈 위 다수 device에 분산 | **on-die** (한 die 안에 다수 채널) |

:::caution[DV 시사점 — LPDDR5에는 DIMM/RCD/PMIC 모델이 없다]
LPDDR5 검증 환경에는 RCD 재구동(re-drive) 지연, on-DIMM PMIC 시퀀스, per-DIMM SPD 같은 *DIMM 고유 요소가 존재하지 않습니다*. controller가 PoP/discrete DRAM과 직접 연결되고, 전원은 SoC PMIC가 외부에서 공급하며, 채널은 die 내부에 있습니다. DDR5 DIMM용 TB(RCD/PMIC agent 포함)를 그대로 재사용하면 LPDDR5에는 *불필요한 components*가 생기므로, 폼팩터에 맞는 TB topology를 별도로 구성해야 합니다.
:::
---

## 6. 어드레싱 — Bank Group × Bank × Row × Column

### 6.1 DDR5 어드레싱 분해 (대표)

DDR5에서 특정 데이터를 접근하려면 4개의 좌표를 모두 지정해야 합니다. Bank Group이 어떤 묶음인지를 결정하고, 그 안에서 Bank를 선택하고, 해당 bank 내 Row를 활성화한 뒤, Column으로 실제 데이터 위치를 지정합니다. DDR5의 예시 (16Gb x8 device 가정):

| 차원 | 비트 수 | 비고 |
|---|---|---|
| Bank Group (BG) | 3 | 8 BG |
| Bank (BA) | 2 | per BG |
| Row | 17 | 128K rows per bank |
| Column | 10 | 1K columns per row (BL16 기준) |

총 = BG[2:0] + BA[1:0] + Row[16:0] + Col[9:0] = 32-bit logical address

이 4축 구조가 중요한 이유는 timing parameter에 직접 영향을 주기 때문입니다. 같은 BG 안의 다른 bank끼리 연속 명령을 내리면 `tCCD_L`(Long)을 지켜야 하고, 다른 BG라면 더 짧은 `tCCD_S`(Short)가 적용됩니다. BG를 활용해 명령을 교차 발급하면 실질 대역폭을 높일 수 있고, DV는 이 조합을 모두 coverage로 잡아야 합니다.

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

> CL = CAS Latency(read 명령부터 첫 데이터가 DQ에 나올 때까지의 클럭 지연). DDR5에서 CL은 MR0에 설정. **tCK**(클럭 한 주기의 시간) 단위로 표기. 위에서 **AP**(auto-precharge, RD/WR 명령에 켜 두면 burst가 끝나자마자 자동으로 PRE까지 수행하는 옵션)와 **beat**(클럭 edge마다 한 번씩 DQ로 오가는 데이터 한 조각 — BL16이면 16 beat)도 함께 알아 둡니다.

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

:::caution[coverage 함정 — 모든 row를 bin으로 만들면]
Row가 17-bit (=128K)이고 각 bin = 1 row 이면 *128K bins*. 시뮬레이션 성능과 coverage report 모두 폭발합니다. **range bin**으로 묶고, 특별히 검증해야 할 row만 *named bin*으로 추가하세요.
:::
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

:::tip[Q. DDR5 16Gb x8 device, BG=3'b101, BA=2'b10, Row=17'h0_ABCD, Col=10'h040, BL16. ACT→RD 시퀀스의 cycle-by-cycle CA 동작을 추적하라. tRCD=14 nCK, CL=22 nCK, tCK=0.5ns 가정.]
:::
<details>
<summary>풀이 (사고 과정 + cycle dry-run)</summary>


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

</details>
---

## 9. PDF 정밀 인용 — DDR5 SDRAM 어드레싱 (밀도별)

> 출처: JESD79-5C.01 v1.31 §2.7, Tables 4~8

DDR5는 device 밀도 (8 Gb ~ 64 Gb) 와 organization (x4/x8/x16) 에 따라 BG/BA/Row/Column 비트 수가 달라집니다. controller IP가 *다양한 밀도/organization*을 지원하려면 다음 표를 *parameter*로 모델링해야 합니다.

### 9.1 8 Gb (Table 4)

표의 새 항목 — **Page Size**(한 row를 열었을 때 row buffer에 담기는 데이터 크기), **CID**(chip ID, 한 패키지에 여러 die를 쌓을 때 어느 die인지 고르는 식별 주소), **Stack Height**(한 패키지 안에 수직으로 쌓은 die의 개수, 예: 16H = 16단)입니다.

| Config | 2 Gb × 4 | 1 Gb × 8 | 512 Mb × 16 |
|---|---|---|---|
| BG Address | BG0~BG2 | BG0~BG2 | BG0~BG1 |
| Bank Address in a BG | BA0 | BA0 | BA0 |
| # BG / # Banks per BG / # Banks | 8 / 2 / 16 | 8 / 2 / 16 | 4 / 2 / 8 |
| Row Address | R0~R15 | R0~R15 | R0~R15 |
| Column Address | C0~C10 | C0~C9 | C0~C9 |
| Page Size | 1KB | 1KB | 2KB |
| CID / Max Stack Height | CID0~3 / 16H | CID0~3 / 16H | CID0~3 / 16H |

### 9.2 16 Gb (Table 5)

| Config | 4 Gb × 4 | 2 Gb × 8 | 1 Gb × 16 |
|---|---|---|---|
| BG Address | BG0~BG2 | BG0~BG2 | BG0~BG1 |
| Bank Address in a BG | BA0~BA1 | BA0~BA1 | BA0~BA1 |
| # BG / # Banks per BG / # Banks | 8 / 4 / **32** | 8 / 4 / **32** | 4 / 4 / **16** |
| Row Address | R0~R15 | R0~R15 | R0~R15 |
| Column Address | C0~C10 | C0~C9 | C0~C9 |
| Page Size | 1KB | 1KB | 2KB |

> **핵심 변화 (8 Gb → 16 Gb)**: bank 수가 *2배* (16 → 32 for x4/x8; 8 → 16 for x16). DDR5 §3.2의 "16 Gb 이상은 *32-bank* (8 BG × 4 banks/BG for x4/x8) 또는 *16-bank* (4 BG × 4 banks/BG for x16) 로 *doubling*" 과 일치.

### 9.3 24 Gb (Table 6)

| Config | 6 Gb × 4 | 3 Gb × 8 | 1.5 Gb × 16 |
|---|---|---|---|
| Row Address | **R0~R16** | **R0~R16** | **R0~R16** |
| 나머지 | 16 Gb와 동일 (BG/BA, Page Size, CID) | | |

> **NOTE 1 (스펙 원문 인용)**: "For non-binary memory densities, **a quarter of the row address space is invalid. When the MSB address bit is 'HIGH', the MSB-1 address bit shall be 'LOW'**."
>
> 즉 24 Gb (= non-binary) 에서 row[16] = 1 일 때 row[15] = 0 강제. (**MSB** = most significant bit, 가장 높은 자리 비트; MSB-1은 그 바로 아래 비트)

_왜 1/4 의 주소 공간이 무효가 되는가_ 는 이진 주소와 비이진 용량의 불일치에서 나옵니다. 주소는 본질적으로 2의 거듭제곱 단위로만 공간을 가리킵니다 — n 비트 row 주소는 정확히 2ⁿ 개의 row 만 표현할 수 있습니다. 그런데 24 Gb 는 2의 거듭제곱이 아닙니다(16 Gb 와 32 Gb 사이, 정확히는 16 Gb 의 1.5배). 24 Gb 의 row 수를 담으려면 16 비트(2¹⁶ = 65,536 row)로는 모자라 17 비트(R0~R16)를 써야 하는데, 17 비트는 2¹⁷ = 131,072 row 를 가리킬 수 있어 실제 필요한 양(16 비트분의 1.5배 ≈ 98,304)보다 _넓습니다_. 즉 17 비트 주소 공간의 3/4 만 실제 셀에 대응하고 **나머지 1/4 은 물리적으로 존재하지 않는 빈 공간** 입니다. JEDEC 은 그 빈 1/4 을 "MSB(row[16]) 가 HIGH 이면 MSB-1(row[15]) 은 반드시 LOW" 라는 규칙으로 잘라내어, 접근 불가능한 주소가 명확히 정의되도록 한 것입니다. DV 의 *random row* constraint에 반영 필요:
> ```systemverilog
> constraint c_nonbinary_row {
>     // 24Gb: 1/4 of row space invalid
>     if (density == DENSITY_24Gb) {
>         !(row[16] && row[15]);   // MSB HIGH 일 때 MSB-1 LOW
>     }
> }
> ```

### 9.4 32 Gb (Table 7) / 64 Gb (Table 8)

| Density | Row Address | Column Address | CID / Max Stack |
|---|---|---|---|
| 32 Gb (x4/x8) | R0~R16 | C0~C10 / C0~C9 | CID0~3 / 16H |
| 32 Gb (x16) | R0~R16 | C0~C9 | CID0~3 / 16H |
| 64 Gb (x4/x8) | **R0~R17** | C0~C10 / C0~C9 | **CID0~2 / 8H** |
| 64 Gb (x16) | **R0~R17** | C0~C9 | **CID0~2 / 8H** |

64 Gb 부터는 row 비트가 *R0~R17* (총 18-bit) — 단일 bank당 row 수 = 2^18 = 256K. 또한 stack height 가 16H → 8H로 *감소* (**TSV**(through-silicon via, 적층한 die들을 수직으로 관통해 잇는 배선) / thermal 제약).

### 9.5 핀 정의 정밀 — Table 3 인용

> 출처: JESD79-5C.01 §2.6, Table 3 — Pinout Description (요약 발췌)

| Symbol | Type | 핵심 기능 |
|---|---|---|
| `CK_t`, `CK_c` | Input | Differential clock. address/control은 *CK_t positive edge와 CK_c negative edge의 crossing*에서 sample. |
| `CS_n`, `(CS1_)` | Input | Chip Select. HIGH일 때 모든 명령 mask. multi-rank 의 rank selection + command code 일부. Power-down 진입/탈출에도 사용. |
| `DM_n`, `DMU_n`, `DML_n` | Input | Input Data Mask. **MR5:OP[5]=1**로 enable. **x8 only** (x4는 unsupported). |
| `CA[13:0]` | Input | Command/Address. *Multi-Cycle command 에서 pin은 cycle 간 interchange 불가*. |
| `RESET_n` | Input | Active-low async. CMOS rail-to-rail, *80%~20% of VDDQ*. |
| `DQ` | I/O | Bidirectional data bus. CRC enabled (MR50) 면 burst 끝에 CRC code 추가. |
| `DQS_t/c`, `DQSU_t/c`, `DQSL_t/c` | I/O | Read: *edge-aligned* with data. Write: *center-aligned* with data. **DDR5는 differential strobe만 지원** (single-ended 미지원). |
| `TDQS_t/c` | Output | Termination Data Strobe. **x8 only**. **MR5:OP[4]=1**로 enable. enable 시 DM_n 자리에 termination 제공. |
| `ALERT_n` | I/O | CRC error 검출 시 LOW. Connectivity Test mode에서 input. unused면 *VDDQ로 pull-up*. |
| `TEN` | Input | Connectivity Test mode enable. AC HIGH/LOW = 80%/20% of VDDQ. |
| `MIR` | Input | Mirrored mode strap. VDDQ strap 시 SDRAM 내부적으로 *짝수 CA bit와 다음 홀수 CA bit를 swap*. |
| `CAI` | Input | Command & Address Inversion strap. VDDQ strap 시 internal하게 CA 신호 *invert*. |
| `CA_ODT` | Input | CA용 ODT strap. VSS strap = Group A, VDDQ strap = Group B. |
| `LBDQ`/`LBDQS` | Output | Loopback Data Output/Strobe. **MR53:OP[4:0]**에서 선택. |
| `VDDQ` / `VDD` | Supply | DQ Power / Core Power — 모두 **1.1V** |
| `VPP` | Supply | DRAM Activating Power Supply — **1.8V** |
| `ZQ`, `(ZQ1)` | Reference | ZQ Calibration. **240 Ω RZQ** resistor로 VSS 연결. DDP(dual-die package, 한 패키지에 die 2개를 쌓은 구성) 의 경우 bottom die (Rank 0) 에 연결. |

:::tip[DV 적용 — 핀 정의 검증 포인트]
- **MR5:OP[4]/[5]**: x4 device에서 *DM/TDQS 둘 다 disabled* 인지 SVA로 확인 (x4는 두 기능 모두 unsupported)
- **MIR/CAI strap**: power-on 시 strap 값이 *MR mirror에 정확히 반영*되는지 init coverage
- **ZQ resistor**: simulation model이 *240 Ω 가정*인지 확인 (다른 값이면 calibration fail)
- **Multi-Cycle command pin interchange 금지**: SVA로 *2-cycle 명령의 두 cycle 사이*에 *CA pin assignment 변경*이 없는지 검증
:::
### 9.6 §3.2 Basic Functionality 원문 인용

> JESD79-5C.01 §3.2 (원문 인용):
>
> "The DDR5 SDRAM is a high-speed dynamic random-access memory. To ease transition from DDR4 to DDR5, **the introductory density (8 Gb) shall be internally configured as 16-bank, 8 bank group with 2 banks for each bank group for x4/x8 and 8-bank, 4 bank group with 2 banks for each bank group for x16 DRAM**. When the industry transitions to higher densities (=>16 Gb), **it doubles the bank resources and internally be configured as 32-bank, 8 bank group with 4 banks for each bank group for x4/x8 and 16-bank, 4-bank group with 4 banks for each bank group for x16 DRAM**."

핵심:
- **8 Gb**: x4/x8 → 16 banks (8 BG × 2 BA), x16 → 8 banks (4 BG × 2 BA)
- **16 Gb 이상**: x4/x8 → 32 banks (8 BG × 4 BA), x16 → 16 banks (4 BG × 4 BA)

_왜 16 Gb 이상에서 bank 수를 두 배로 늘리는가_ 는 **bank-level parallelism 유지** 동기로 설명됩니다. 용량을 키우는 방법은 둘입니다 — bank 수는 그대로 두고 bank 하나를 더 크게(더 많은 row) 만들거나, bank 수 자체를 늘리거나. 만약 bank 수를 고정한 채 용량만 키우면, 동시에 "열어 둘 수 있는 row(= active bank 수)" 는 그대로인데 그 bank 들이 전체 용량에서 차지하는 비중은 줄어듭니다. 즉 같은 데이터양을 더 적은 동시 접근 창구로 처리해야 해서, bank conflict 가 늘고 controller 가 Row Hit·병렬화로 숨길 수 있는 여지가 줄어 effective bandwidth 가 떨어집니다. 그래서 JEDEC 은 용량이 한 단계 오를 때 bank 수도 함께 늘려, 용량 대비 동시 접근 가능한 bank 의 비율(parallelism 밀도)을 유지하는 쪽을 택합니다. DDR5 가 BG 를 8개로 둔 것과 결합하면, 늘어난 bank 가 여러 BG 에 분산되어 tCCD_S interleaving 기회까지 함께 커집니다.

### 9.7 16n Prefetch Architecture 원문 인용

> JESD79-5C.01 §3.2 (원문 인용):
>
> "The DDR5 SDRAM uses a **16n prefetch architecture** to achieve high-speed operation. The 16n prefetch architecture is combined with an interface designed to transfer two data words per clock cycle at the I/O pins. **A single read or write operation for the DDR5 SDRAM consists of a single 16n-bit wide, eight clock data transfer at the internal DRAM core and sixteen corresponding n-bit wide, one-half clock cycle data transfers at the I/O pins**."

| 영역 | 폭 | 클럭 |
|---|---|---|
| 내부 DRAM core 전송 | **16n bits wide** | 8 clocks |
| I/O 인터페이스 전송 | n bits wide | **16 half-clocks** (= BL16 × half-tCK) |

여기서 **prefetch**(내부 셀 어레이는 느리므로, 한 번에 여러 비트를 미리 한 묶음으로 읽어 두고 빠른 I/O에서 잘게 나눠 내보내는 구조)가 고속 동작의 핵심입니다. 즉:
- 내부 prefetch = 16n bits (n = DQ width: 4/8/16)
- 외부 I/O 전송 = 16 beats × n bits at half-tCK
- BL16 → 16 beats → 1 burst = *1 internal prefetch*
- BL32 → 32 beats → 2 internal prefetches

### 9.8 Burst Length 옵션 (§3.2 원문)

> JESD79-5C.01 §3.2: "**BC8 on-the-fly (OTF)**, **fixed BL16**, **fixed BL32 (optional)**, or **BL32 OTF (optional)** mode if enabled in the mode register."

| Burst Mode | 의미 | 활용 |
|---|---|---|
| BC8 OTF | Burst Chop 8 — *command 단위*로 선택 | legacy / 짧은 burst |
| Fixed BL16 | 모든 burst가 16-beat (**default**) | 일반 traffic |
| Fixed BL32 (optional) | 모든 burst가 32-beat | sequential 대량 |
| BL32 OTF (optional) | command 단위로 BL16/BL32 선택 | mixed traffic |

```systemverilog
// DV 적용 — burst mode coverage
typedef enum {BURST_BC8_OTF, BURST_BL16_FIXED, BURST_BL32_FIXED, BURST_BL32_OTF} burst_mode_e;

covergroup ddr5_burst_mode_cg with function sample (burst_mode_e mode, int actual_bl);
    cp_mode: coverpoint mode;
    cp_bl: coverpoint actual_bl {
        bins bc8  = {8};
        bins bl16 = {16};
        bins bl32 = {32};
    }
    cx_consistency: cross cp_mode, cp_bl {
        ignore_bins illegal_bc8_with_fixed16 =
            binsof(cp_mode) intersect {BURST_BL16_FIXED} &&
            binsof(cp_bl.bc8);
        // BL16 fixed mode에서 BC8 발급은 illegal
    }
endgroup
```

---

## 10. 핵심 정리 (Key Takeaways)

- DDR5는 *DIMM당 2 channels* 분리. 각 channel은 독립적 address/command bus.
- DDR5 command는 *2 cycles에 걸쳐* CA[13:0] (또는 CA[6:0]) 에 인코딩 — monitor sampling window 2배 확장 필요.
- DDR5 Bank Group은 *8개* (x4/x8) 또는 *4개* (x16). `tCCD_L` vs `tCCD_S` 가 BG 동일성에 따라 적용.
- **밀도별 bank 수**: 8 Gb는 16-bank (x4/x8) 또는 8-bank (x16). 16 Gb 이상은 32-bank (x4/x8) 또는 16-bank (x16) — *bank doubling*.
- **Row address 비트**: 8/16 Gb → R0~R15, 24/32 Gb → R0~R16, 64 Gb → R0~R17. **24 Gb 의 non-binary 제약** (MSB HIGH 시 MSB-1 LOW 강제).
- **16n prefetch**: 내부 16n-bit × 8 클럭 ↔ 외부 n-bit × 16 half-클럭. BL16 = 1 prefetch.
- **Burst Length**: BC8 OTF / Fixed BL16 (default) / Fixed BL32 (opt) / BL32 OTF (opt).
- LPDDR4는 BG 없는 8 banks·dual-channel die가 기본. LPDDR5는 WCK/RDQS 도입, Bank mode 3가지(16B/8B/BG). **BG mode = 4 BG × 4 = 16 banks**로 DDR5의 32 banks(8 BG×4)와는 규모가 다름.
- LPDDR5는 폼팩터가 **PoP**(또는 discrete/MCP)로, DDR5와 달리 **DIMM·RCD·on-package PMIC가 없고** 전원은 SoC PMIC, 채널은 on-die — TB topology를 DDR5 DIMM과 별도로 구성.
- Coverage에서 Row를 *range bin*으로 묶지 않으면 폭발. 4축(BG/BA/Row/Col)을 균형 있게.

## 11. Further Reading

- 이전: [Ch01. DRAM 기본 원리와 JEDEC 표준 지형도](../01_dram_jedec_landscape/)
- 다음: [Ch03. 초기화·Reset·Power 시퀀스](../03_init_reset_power/)
- 부록: [JEDEC Spec 빠른 참조](../appendix_a_quick_reference/)
- 퀴즈: [Ch02 퀴즈](../quiz/ch02_quiz/)

