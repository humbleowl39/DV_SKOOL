---
title: "부록 A — 빠른 참조"
description: 구성·커맨드·Mode Register·타이밍·신호와 검증에서 자주 틀리는 항목을 한 곳에 모은 조회용 요약
---

:::caution[인용 고지]
본 부록은 **JESD270-4 (2025-04, WIP draft)** 의 내용을 **조회 편의를 위해 재구성**한 것입니다. 원문 표를 옮긴 것이 아니며, 정밀 값은 **JEDEC 원문 우선**입니다. 각 항목에 본문 장 링크를 붙였습니다.
:::

---

## 1. 구성 한눈에

| 항목 | 값 | 장 |
|---|---|---|
| 총 인터페이스 폭 | **2048-bit** | [01](../01_landscape_organization/) |
| 채널 | 최대 **32** (완전 독립, **비동기 가능**) | [01](../01_landscape_organization/) |
| Pseudo-channel | 채널당 **2** → 최대 **64** | [01](../01_landscape_organization/) |
| 채널 데이터 폭 | **64 DQ** (DDR) | [01](../01_landscape_organization/) |
| PC 데이터 폭 | **32 DQ** | [01](../01_landscape_organization/) |
| Prefetch | PC당 **256-bit / 접근** | [01](../01_landscape_organization/) |
| Burst Length | **8** (중단·절단 없음) | [07](../07_column_commands/) |
| 페이지 | PC당 **1 KB** (물리 행 2 KB의 절반) | [02](../02_addressing_bank_groups/) |
| 스택 높이 | **4 / 8 / 12 / 16-high** (32채널에 최소 4 die) | [01](../01_landscape_organization/) |
| 채널 밀도 | **3 Gb ~ 16 Gb** | [01](../01_landscape_organization/) |
| 뱅크 | 채널당 **16 / 32 / 48 / 64** | [02](../02_addressing_bank_groups/) |
| 뱅크 그룹 | **2 / 4 / 6 / 8** (연속 8뱅크 = 1그룹) | [02](../02_addressing_bank_groups/) |
| 최대 용량 | **64 GB** (32 Gb × 16-high) | [02](../02_addressing_bank_groups/) |
| 신호 마이크로범프 | 채널당 **120** + 전역 **56** → **약 3,896** [추론] | [01](../01_landscape_organization/) |

## 2. 주소 필드

| 필드 | 폭 | 무효 조합 |
|---|---|---|
| `RA[13:0]` | 14 | **`RA[13:12] = 11`** |
| `CA[4:0]` | 5 | (BL8의 8 UI를 구분하지 않음) |
| `BA[3:0]` | 4 | — |
| `SID[1:0]` | 0~2 (구성별) | **`SID[1:0] = 11`**, **4Hi에서 `SID[0] = 1`** |

- 뱅크 인덱스 = **`{SID, BA[3:0]}`**, 뱅크 그룹 = **`{SID, BA[3]}`** [추론]
- `Page = 2^COLBITS × (Prefetch/8)` = **1 KB**
- **SID는 `ACT`·`PREpb`·`REFpb`·`RFMpb`에서만** 뱅크 주소로 쓰인다 → [02](../02_addressing_bank_groups/)

## 3. 커맨드

### 사이클 길이

| 커맨드 | 사이클 |
|---|---|
| `ACT` | **1.5** |
| 그 외 row 커맨드 | **0.5** |
| `PDE`, `SRE` | **1** |
| column 커맨드 | **1** |

### Row 커맨드

| 심볼 | 이름 | SID 사용 | 장 |
|---|---|---|---|
| `RNOP` | Row No Operation | — | [06](../06_row_commands/) |
| `ACT` | Activate | ✅ | [06](../06_row_commands/) |
| `PREpb` / `PREab` | Precharge per-bank / all-bank | pb만 ✅ | [06](../06_row_commands/) |
| `REFpb` / `REFab` | Refresh per-bank / all-bank | pb만 ✅ | [06](../06_row_commands/) |
| `RFMpb` / `RFMab` | Refresh Management | pb만 ✅ | [06](../06_row_commands/) |
| `PDE` / `PDX` | Power-Down 진입 / 종료 | — | [07](../07_column_commands/) |
| `SRE` / `SRX` | Self Refresh 진입 / 종료 | — | [07](../07_column_commands/) |

### Column 커맨드

| 심볼 | 이름 | 장 |
|---|---|---|
| `CNOP` | Column No Operation | [07](../07_column_commands/) |
| `RD` / `RDA` | Read / Read with Auto Precharge | [07](../07_column_commands/) |
| `WR` / `WRA` | Write / Write with Auto Precharge | [07](../07_column_commands/) |
| `MRS` | Mode Register Set (**row 버스에 `RNOP` 요구**) | [07](../07_column_commands/) |

### 슬롯 규칙

- row 커맨드는 **같은 사이클 하강 에지를 `RNOP`로 패딩**하거나 precharge로 채운다
- **`ACT` 두 번째 사이클 하강 슬롯**: `RNOP` / **다른 뱅크** `PREpb` / **다른 PC** `PREab` 만 허용
- **PC로 선택되지 않은 pseudo channel은 `RNOP`를 수행**
- 진리표에 없는 **`ARFU`도 유효 레벨로 구동**해야 한다

## 4. Refresh 다섯 갈래

| 커맨드 | 대상 | RAA 효과 | 장 |
|---|---|---|---|
| `REFab` / `REFpb` | 전 뱅크 / 단일 뱅크 | **− `RAADEC`** | [06](../06_row_commands/) |
| `RFMab` / `RFMpb` | 전 뱅크 / 단일 뱅크 | **− `RAAIMT`** (하한 0) | [06](../06_row_commands/) |
| `DRFMpb` | 단일 뱅크 (지목된 행의 이웃) | **감소 없음** | [06](../06_row_commands/) |

**RAA 규칙**
```
ACT           → RAA += 1  (뱅크별)
RAA = RAAMMT  → 그 뱅크에 ACTIVATE 금지
self refresh  → tRAASRF 이상 유지 시에만 0으로 리셋
```
문턱값 `RAAIMT` · `RAAMMT` · `RAADEC`는 **`DEVICE_ID` WDR에서 읽는다**(읽기 전용).

**ARFM 조합** — `RFM`/`ARFM` 비트 × `MR8` OP[5:4]

| `RFM` | `ARFM` | 레벨 `00` | 레벨 `01`/`10`/`11` |
|---|---|---|---|
| 0 | 0 | RNOP | ⚠️ **Illegal** |
| 0 | 1 | RNOP | RFM 실행 |
| 1 | 0 | RFM 실행 | ⚠️ **Illegal** |
| 1 | 1 | RFM 실행 | RFM 실행 |

## 5. Mode Register 지도

**20개 × 8-bit** (`MR0`~`MR19`), `MA[4:0]`로 선택, **두 PC 공유**, **기본값 없음 → 전부 초기화 필요** → [04](../04_mode_registers/)

| MR | 주요 필드 |
|---|---|
| **`MR0`** | `TM` · **`CAPAR`** · **`WPAR`** · **`RPAR`** · **`DRFM`** · `TCSR` · **`WDBI`** · **`RDBI`** |
| **`MR1`** | **`PL`** OP[7:5] (0–4 nCK) · **`WL`** OP[4:0] (4–19 nCK) |
| **`MR2`** | **`RL`** (17–90 nCK) |
| `MR3` | `WR` (4–63 nCK) |
| `MR4` | `RAS` (4–63 nCK) |
| `MR5` | `RTP` (2–15 nCK) |
| `MR6` | **`DCM Flip`** OP7 · **`DCM`** OP6 · Pullup/Pulldown 드라이버 강도 (25/20/**16.7**/14.3 Ω) |
| `MR7` | `CATTRIP` · RDQS Postamble · **DWORD MISR Control** · Read Mux · **Loopback Control** |
| **`MR8`** | `BRC` · **`RFML`** OP[5:4] · **`WDQS2CK`** OP3 · `ECSLOG` OP2 · **`RxOffC`** OP1 · **`DA Port Lockout`** OP0 |
| **`MR9`** | `ECSRES` OP7 · `ECSCEM` OP6 · `ECSSRF` OP5 · `ECSREF` OP4 · `ECCVEC` OP3 · `ECCTM` OP2 · `SEVR` OP1 · **`MD`** OP0 |
| `MR10` | DCA — **RDQS1(PC1) / RDQS0(PC0)** |
| `MR11` | DCA — **WDQS1(PC1) / WDQS0(PC0)** |
| `MR12` | **벤더 전용** |
| `MR13` / `MR14` | `VREFCA` (AWORD) / `VREFD` (DWORD) |
| `MR15` / `MR16` | DFE Code (PC1/PC0) / DFE 예약 |
| `MR17` | **벤더 전용** |
| `MR18` / `MR19` | RFU |

**규칙**
- 값은 선택적이나 **지원 범위는 연속** → `[min, max]` 두 값으로 관리
- 타이밍 MR은 **`RU{t/tCK}` 이상**, 미지원 시 **조용히 무시**
- **되읽기는 IEEE1500 `MODE_REGISTER_DUMP_SET` 뿐** → 섀도 카피 필수
- `MRS` 전제: **모든 뱅크 idle** + `tRDMRS` + `tWRMRS`

## 6. 타이밍 파라미터

### 라운딩 (HBM4 고유)

```
nXX = 0.5 × RU(2 × tXX / tCK)          대상: tRAS, tRTP, tWR, tRP
tRP 결과가 하강 에지면 +0.5 nCK        (후속 row 커맨드는 상승 에지 전용)
```
→ [06](../06_row_commands/)

### 뱅크 그룹·SID 의존

| 시퀀스 | 같은 그룹 | 다른 그룹·같은 SID | 다른 그룹·다른 SID |
|---|---|---|---|
| ACT → ACT | `tRRDL` | `tRRDS` | `tRRDS` |
| WR → WR | `tCCDL` | `tCCDS` | `tCCDS` |
| **RD → RD** | `tCCDL` | `tCCDS` | **`tCCDR`** |
| 내부 WR → RD | `tWTRL` | `tWTRS` | `tWTRS` |
| RD → PRE | `tRTP` | — | — |

`tCCDR`: **8/12/16-High 전용**, `tCCDS + 1` ~ `2 nCK`, **벤더 지정·주파수 의존** → [07](../07_column_commands/)

### 초기화

| 기호 | 제약 | 의미 |
|---|---|---|
| `tINIT0` | 0.01 ~ **200 ms** | 전원 램프 |
| `tINIT1` | ≥ **200 µs** | `RESET_n` LOW 유지 |
| `tINIT2` | ≥ **10 ns** | CK 정적 구동 선행 |
| **`tINIT3`** | ≥ **4 ms** | **퓨즈 적용 + I/O 임피던스 보정 (지배적)** |
| `tINIT4` | ≥ **10 nCK** | 안정 클럭 |
| `tINIT5` | ≥ **200 ns** | 첫 MRS 전 유휴 |
| `tINIT6` | ≤ **100 ns** | ⚠️ **유일한 최대 제약** |
| `tINIT7` | ≥ **2 nCK** | PDE/CNOP 유지 |
| `tPW_RESET` | ≥ **1 µs** | 안정 전원 `RESET_n` LOW |

→ [03](../03_init_reset_power/)

### 기타 주요 제약

| 항목 | 값 | 장 |
|---|---|---|
| **`tRAS` 최대** | **`9 × tREFI`** | [12](../12_electrical_timing_package/) |
| `tOSCAL` (Rx offset) | 최대 **6 µs** | [11](../11_training_ieee1500/) |
| WOSC 최대 계수 | **2²⁴ − 1** | [11](../11_training_ieee1500/) |
| `tECSint` | `86,400 s ÷ codeword 수` | [09](../09_ecc_ecs_sev/) |

## 7. 스트로브와 클럭

```
스트로브 주파수 = CK × 2
CK·WDQS ← 같은 PLL      RDQS ← WDQS
WDQS 클럭 트리에 reset 타입 분주기 (내부 회로는 절반 속도)
```

**preamble / postamble (고정)**

| 동작 | 스트로브 | pre | post | 합 |
|---|---|---|---|---|
| READ | WDQS | **4** | 2 | **6** |
| READ | RDQS | 2 | 2 | **4** |
| WRITE | WDQS | 2 | 2 | **4** |

⚠️ **모든 토글의 합은 짝수여야 한다** (preamble + postamble + 모든 트레이닝). 위반 시 `WDQS/2` 위상이 뒤집힌 채 남는다. → [05](../05_clocking_dbi/)

**유휴 상태**: `_t` = LOW, `_c` = HIGH
**에지 정의**: 차동 **교차점**

**지연 관계식**
```
READ  첫 데이터 = RL × tCK + tDQSS + tWDQS2DQ_O + tDQSQ
      첫 WDQS   = (RL − 2) × tCK + tDQSS
      첫 RDQS   = (RL − 1) × tCK + tDQSS + tWDQS2DQ_O
      첫 데이터 비트 ← RDQS **세 번째 상승 에지**
WRITE 첫 데이터 = WL × tCK + tDQSS
      첫 WDQS   = (WL − 1) × tCK + tDQSS
```

## 8. DBIac

| 바이트 내 전이 수 | 직전 DBI | 새 DBI | 데이터 |
|---|---|---|---|
| 0 ~ 3 | 무관 | LOW | 반전 안 함 |
| **4** | LOW | LOW | 반전 안 함 |
| **4** | HIGH | **HIGH** | **반전** |
| 5 ~ 8 | 무관 | **HIGH** | **반전** |

- **ECC·SEV·`DPAR`은 대상 아님**
- 내부 상태 리셋: **`RESET_n` 비어서트 · `MRS` 수신 · write→read 턴어라운드 · Self Refresh 종료**
- **`RDBI` 비활성이어도 첫 READ 전 프리컨디셔닝은 수행**

→ [05](../05_clocking_dbi/)

## 9. Parity

| | CA Parity | Data Parity |
|---|---|---|
| 제어 | `MR0` OP6 | `MR0` OP5(W) / OP4(R) |
| 대상 | `R[9:0]` + `C[7:0]` + **`ARFU`** + `APAR` | DQ + (DBI) + (ECC) + `DPAR` |
| 규칙 | **짝수 패리티** (홀수 → `AERR` HIGH) | 동일 |
| 오류 시 | ⚠️ **커맨드는 실행됨** | ⚠️ **write는 배열까지 완료됨** |
| 신호 | `APAR` / `AERR` (AWORD당 1) | `DPAR` / `DERR` (DWORD당 1) |

**대상 집합이 동적이다** — DBI는 `WDBI`/`RDBI`, ECC는 `MR9`의 `MD`에 의존. **`SEV`는 언제나 제외.**

**비활성화 금지 구간**: `CAPAR` → `tPARAC` / `WPAR` → `WL+PL+tPARDQ+2tCK` / `RPAR` → `tRDMRS`

→ [08](../08_parity/)

## 10. ECC · ECS · SEV

```
codeword = 256 b (DQ 32핀 × BL8) + 16 b (ECC 2핀 × BL8) + 체크비트 = 최소 304 b
```

- **read는 정정해서 반환하지만 배열에 되쓰지 않는다** → **ECS가 전제 조건**
- **UE는 되쓰지 않는다**
- **오류는 ECS 중에만 기록된다** (일반 read 정정은 `SEV`로만, 휘발성)

**`SEV` 인코딩** (버스트 위치 **4~7**, `{SEV1, SEV0}`)

| 값 | 심각도 |
|---|---|
| `00` | NE |
| `01` | CEs |
| `11` | CEm |
| `10` | UE |

⚠️ **`ERRCNT ≤ ERRTH`이면 CEs가 NE로 보고된다.** CEm·UE는 필터 없음. → [09](../09_ecc_ecs_sev/)

## 11. 테스트와 복구

### Lane repair

| 계층 | 여분 | 범위 |
|---|---|---|
| AWORD | 채널당 **1** | row **또는** column |
| DWORD | 더블 바이트당 `RD` | 데이터 |
| WSO | `RM` | IEEE1500 직렬 출력 |

**복구 불가**: `CK_t`/`CK_c` · `AERR` · `WDQS_t`/`_c` · `RDQS_t`/`_c` · `PAR` · `DERR`

⚠️ **한 번에 한 레인만** (전류 제약) → N개면 **N번의 `UpdateWR`**
⚠️ **soft가 hard를 덮어쓴다** → **읽기 → 병합 → 쓰기**
발행 시점: **CK 토글 이전**

### MISR 폭

```
DWORD 바이트 : (DQ 8 + DBI 1 + ECC/SEV 1) × 4 = 40 b
AWORD        : (R 10 + C 8 + ARFU 1) × 2       = 38 b
DWORD_MISR 읽기 : 40 × 4바이트 × 2 DWORD       = 320 b
```

모드 넷: **LFSR / Register / MISR / LFSR Compare**. 서명은 **aliasing**이 있으므로 `READ_LFSR_COMPARE_STICKY` 병행.

→ [10](../10_test_repair/)

## 12. IEEE 1500 명령 21개

| 묶음 | 명령 |
|---|---|
| 기본·리셋 | `BYPASS` · `HBM_RESET` |
| 식별 | `CHANNEL_ID` · **`DEVICE_ID`** |
| 경계 스캔 | `EXTEST_RX` |
| 배열 시험·복구 | `MBIST` · `SOFT_REPAIR` · `HARD_REPAIR` · `SELF_REP` · `SELF_REP_RESULTS` · `HS_REP_CAP` |
| 레인·채널 | `SOFT_LANE_REPAIR` · `CHANNEL_DISABLE` |
| 루프백 | `DWORD_MISR` · `AWORD_MISR` · `AWORD_MISR_CONFIG` · `READ_LFSR_COMPARE_STICKY` |
| MR 접근 | **`MODE_REGISTER_DUMP_SET`** |
| 센서·계측 | `TEMPERATURE` · `CHANNEL_TEMPERATURE` · `WOSC_RUN` |
| 오류 로그 | `ECS Error Log` |

**`DEVICE_ID`에서 읽어야 하는 것**: 밀도 코드 · `RAAIMT`/`RAAMMT`/`RAADEC` · `ARFM` 지원 · `RXoffC` 지원 → **MR 이미지 확정에 필요**

→ [11](../11_training_ieee1500/)

## 13. 트레이닝 순서

```
① Rx Offset Calibration (MR8 OP1)
② DCA / DCM             (MR11·MR10 / MR6 OP[7:6])
③ VREFD                 (MR14)
④ WDQS-to-CK Alignment  (MR8 OP3)
```
앞 단계 재수행 시 **뒤 단계 무효화**. → [11](../11_training_ieee1500/)

## 14. `DERR`의 세 얼굴

| 조건 | 의미 |
|---|---|
| `MR6` OP6 = 1 | **듀티 사이클 측정** (HIGH = ≥50%) |
| `MR8` OP3 = 1 | **위상 검출기** (HIGH = early) |
| 그 외 | **데이터 패리티 오류** |

두 트레이닝을 **동시에 켜면 안 된다.**

## 15. 전기

| 전원 | 전형값 |
|---|---|
| `VDDC` | **1.05** 및/또는 **1.00 V** |
| `VDDQ` | **0.9 / 0.8 / 0.75 / 0.7 V** |
| `VDDQL` | **0.4 V** |
| `VPP` | **1.8 V** |

허용 오차 **0.97× ~ 1.07×**, **마이크로필러 기준**, DC 대역폭 **20 MHz**

**변동 계수** — `tWDQS2DQ_O`: **2.5 ps/mV**, **1.0 ps/°C**
**스큐 예산** — 바이트 내 DQ↔DQ **10 ps**, 바이트 간 **30 ps**, RDQS↔DQ **20 ps**

→ [12](../12_electrical_timing_package/)

## 16. 되돌릴 수 없는 상태 셋

| 상태 | 해제 방법 | 장 |
|---|---|---|
| `CATTRIP` (sticky) | **전원 차단** | [03](../03_init_reset_power/) |
| Auto ECS 시작 | **장치 RESET** | [09](../09_ecc_ecs_sev/) |
| **DA Port Lockout** (`MR8` OP0) | **전원 제거만** — 어떤 리셋·MR 쓰기로도 불가 | [11](../11_training_ieee1500/) |

## 17. 검증에서 자주 틀리는 것 20가지

**모델·monitor 쪽**

1. monitor를 **정수 사이클**로 샘플링 → ACT 1.5 사이클을 놓치거나 두 번 셈. 에러 없이 **커버리지만 낮아진다** · [01](../01_landscape_organization/)
2. Mode Register를 **PC별로 모델링** → 두 PC 공유가 반영 안 됨 · [04](../04_mode_registers/)
3. 뱅크 상태를 **채널당 한 벌**로 → 뱅크마다 필요. 마지막 접근 그룹은 **PC마다** · [02](../02_addressing_bank_groups/)
4. RAL을 **`reset(0)`** 으로 등록 → 기본값이 미정의인데 모델이 0을 자신 있게 예측 · [04](../04_mode_registers/)
5. DBIac을 **조합 함수**로 → 전이 수 4의 히스테리시스가 사라짐. 다음 기준은 `raw`가 아니라 **버스 값** · [05](../05_clocking_dbi/)
6. ECC 모델이 read에서 **셀 오류를 지움** → 되쓰지 않는다는 §6.9.2가 미반영 · [09](../09_ecc_ecs_sev/)
7. **`SEV` 전반부를 함께 샘플링** → 항상 NE. 오류 주입이 전부 조용히 통과 · [09](../09_ecc_ecs_sev/)
8. **`DERR`를 모드 구분 없이** 패리티 오류로 해석 → 트레이닝 중 가짜 에러 폭주 · [11](../11_training_ieee1500/)

**checker 쪽**

9. `tCCD`를 **2택**으로 판정 → 기준을 낮게 잡아 **실제 위반을 통과**. 반대로 WRITE에 `tCCDR`을 쓰면 **false FAIL** · [07](../07_column_commands/)
10. **`tRAS`를 최소만** 검사 → `9 × tREFI` 최대 누락 · [12](../12_electrical_timing_package/)
11. **`tINIT6`을 최소로** 오해 → 부등호가 뒤집혀 정상 동작을 FAIL로 보고 · [03](../03_init_reset_power/)
12. 초기화 검사를 **`@(posedge ck)` SVA**로 → CK가 없는 구간에서 **평가조차 안 되면서 "위반 0건"** · [03](../03_init_reset_power/)
13. 패리티 활성화 시점을 **한쪽으로 못 박음** → false FAIL 또는 놓친 위반. 구간은 **관대하게** · [08](../08_parity/)
14. assertion에 **짝 cover property가 없음** → 무해한지 무력한지 구분 불가 · [06](../06_row_commands/)
15. ECS 로그를 **두 곳에서 읽음** → self-clearing이라 하나가 빈 값을 봄 · [09](../09_ecc_ecs_sev/)

**자극 쪽**

16. **`ARFU`를 구동/패리티/MISR에서 누락** → 패리티가 어긋나고 원인은 패리티 로직처럼 보임 · [06](../06_row_commands/)·[08](../08_parity/)·[10](../10_test_repair/)
17. 문턱값(`RAAIMT`·`ERRTH`·`tCCDR`·`VSP`)을 **상수로 박음** → 다른 장치에서 조용히 틀린 기준 · [06](../06_row_commands/)·[09](../09_ecc_ecs_sev/)
18. MR 이미지 랜덤화가 **`MR8` OP0을 1로** → DA 포트가 영구 잠김. 자극이 **관측 경로를 스스로 닫음** · [11](../11_training_ieee1500/)
19. 채널을 **전부 같은 클럭으로** 자극 → CDC 경로가 통째로 미검증 · [01](../01_landscape_organization/)
20. 복구 레인 **1개만** 시험 → "한 번에 하나" 제약이 시험되지 않음 · [10](../10_test_repair/)

:::caution[V-Plan에 "범위 밖"으로 적어야 하는 다섯]
전원 램프 부등식 · lane repair 전류 제약 · `ERRTH` 이하의 실제 정정 · ESD · 변동 계수의 물리적 영향.

디지털 회귀로 검증할 수 없습니다. 적지 않으면 아무도 안 하고, **안 했다는 사실조차 남지 않습니다** · [12장 §4](../12_electrical_timing_package/)
:::
