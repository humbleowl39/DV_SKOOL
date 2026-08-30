---
title: "07 — Column 커맨드와 저전력"
description: JESD270-4 §6.3.3–6.3.4 · READ/WRITE 버스트와 지연, tCCD 세 갈래, MRS 제약, Power-Down과 Self Refresh
---

:::tip[🎯 Learning Objectives]
이 모듈을 마치면:

- **Trace** READ 커맨드부터 첫 유효 데이터까지의 경로를 `RL`·`tDQSS`·스트로브 preamble과 함께 추적한다.
- **Differentiate** READ→READ 간격이 `tCCDL`·`tCCDS`·`tCCDR` 세 갈래로 갈리는 조건을 구분한다.
- **Explain** 비정합(un-matched) WDQS-DQ 경로가 주기적 트레이닝을 요구하는 이유를 설명한다.
- **Sequence** Power-Down과 Self Refresh 진입 조건을 "완료"의 정의와 함께 정리한다.
- **Analyze** CA parity를 켜고 끄는 MRS가 만드는 비대칭 전이를 분석한다.
:::

:::note[Prerequisites]
- [06 — Row 커맨드](../06_row_commands/) — 커맨드 인코딩과 패딩 규칙
- [05 — 클럭킹과 DBIac](../05_clocking_dbi/) — WDQS/RDQS 관계와 짝수 토글 규칙
- [04 — Mode Register](../04_mode_registers/) — `MR1`(WL·PL), `MR2`(RL)
:::

:::caution[인용 고지]
본 장은 **JESD270-4 (2025-04, WIP draft)** §6.3.3–§6.3.4를 근거로 **요약·재구성**한 것입니다. 진리표·타이밍 그림은 옮기지 않고 관계식과 규칙만 서술합니다. 정밀 값은 **JEDEC 원문 우선**.
:::

---

## 1. CNOP — column 버스의 패딩

`CNOP`는 **1 사이클 커맨드**로, 유휴·대기 상태에서 원치 않는 column 커맨드가 등록되는 것을 막습니다(§6.3.3.1). 진행 중인 동작에는 영향을 주지 않으며, mode register에서 활성이면 **패리티가 평가**됩니다.

[06장](../06_row_commands/)의 `RNOP`와 대칭 관계입니다 — row 버스는 `RNOP`로, column 버스는 `CNOP`로 채웁니다. 그리고 규격의 후속 타이밍 그림들은 **명시하지 않는 한 `C[7:0]`에 `CNOP`가 있다고 가정**합니다.

## 2. READ — 버스트와 지연

### 기본 성질

`READ`는 `C[7:0]`에서 받는 **1 사이클 커맨드**이며 CK **상승·하강 양쪽 에지**에서 래치됩니다(§6.3.3.2). 뱅크·PC·SID·column 주소가 함께 전달되고, 그 접근에 대한 **auto precharge 활성/비활성**도 커맨드 안에서 지정됩니다(`RDA` vs `RD`).

버스트에 대한 규정이 단호합니다.

> `READ` 커맨드로 시작되는 버스트의 길이는 **8**이다. column 주소는 그 여덟에 대해 **유일**하다. **read 버스트의 중단(interruption)이나 절단(truncation)은 없다.**

**한 번 시작한 버스트는 끝까지 갑니다.** 스케줄러가 중간에 끼어들 수 없으므로 발행 시점에 전체 점유를 확정할 수 있고, 그만큼 재정렬 여지가 줄어듭니다.

### 지연 관계식

`RL`(Read Latency)은 **`READ`가 발행된 상승 CK 에지**부터 **`tDQSS` 지연이 측정되는 상승 CK 에지**까지로 정의되며, 값은 `MR2` OP[7:0]에 있습니다([04장](../04_mode_registers/)).

첫 유효 데이터의 도달 시점은 네 항의 합입니다.

```
첫 유효 데이터 = RL × tCK + tDQSS + tWDQS2DQ_O + tDQSQ      (READ 상승 에지 기준)
```

### ⚠️ 읽기 데이터를 트리거하는 것은 WDQS다

이 장에서 가장 반직관적인 조문입니다.

> **쓰기 스트로브(WDQS)가 읽기 데이터(DQ, DBI, ECC, SEV)와 읽기 데이터 스트로브를 트리거하는 소스**다. — §6.3.3.2

"쓰기" 스트로브가 "읽기" 데이터를 몰고 나옵니다. 이유는 [05장](../05_clocking_dbi/)에 있습니다 — **RDQS는 WDQS에서 생성**되기 때문입니다. 컨트롤러는 읽기 동작 중에도 WDQS를 공급해야 하며, 그래서 다음 규정이 따라옵니다.

> RDQS가 토글을 시작하기 전에 write data strobe는 **고정 4펄스 preamble과 고정 2펄스 postamble**을 제공해야 한다. **RDQS는 고정 2펄스 preamble과 고정 2펄스 postamble**을 제공한다. — §6.3.3.2 (요약)

| 동작 | 스트로브 | preamble | postamble | 합 |
|---|---|---|---|---|
| READ | WDQS | **4** | 2 | **6** |
| READ | RDQS | 2 | 2 | **4** |
| WRITE | WDQS | 2 | 2 | **4** |

:::tip[짝수 규칙이 여기서 확인된다]
[05장](../05_clocking_dbi/)에서 본 *"preamble + postamble의 합은 짝수여야 한다"* 는 요구가 **실제 규정값에서 성립**합니다 — 6, 4, 4 전부 짝수입니다.

즉 규격이 preamble/postamble 개수를 고정한 것은 임의의 선택이 아니라 **내부 `WDQS/2` 분주기 위상을 보존하기 위한 설계**입니다. 이 값들을 임의로 바꾸면 위상이 깨집니다.
:::

### 에지 시점

```
첫 WDQS 에지 = (RL − 2) × tCK + tDQSS
첫 RDQS 에지 = (RL − 1) × tCK + tDQSS + tWDQS2DQ_O
```

그리고 데이터 정렬 규칙이 하나 있습니다.

> read 버스트의 **첫 데이터 비트는 RDQS 스트로브의 세 번째 상승 에지와 동기**된다. 이후 각 데이터 출력은 데이터 스트로브와 **edge-aligned** 다. — §6.3.3.2

RDQS preamble이 2펄스이므로 세 번째 상승 에지가 첫 데이터 지점이 되는 것이 자연스럽습니다.

### 출력 드라이버 타이밍

- 드라이버는 첫 유효 데이터 비트보다 **홀수 바이트는 명목상 2 RDQS 펄스**, **짝수 바이트는 1 RDQS 펄스** 앞서 구동을 시작합니다.
- 첫 `READ`에서 버스 프리컨디셔닝은 **`RDBI` 활성·비활성과 무관하게 LOW** 입니다([05장](../05_clocking_dbi/)과 동일).
- 버스트 완료 후 다른 `READ`가 없으면 드라이버는 **명목상 RDQS 펄스의 1/2 이내에 Hi-Z**가 됩니다.

## 3. WRITE — 비정합 경로와 트레이닝

`WRITE`도 1 사이클 커맨드이며 구조는 `READ`와 대칭입니다 — 버스트 길이 **8**, column 주소 유일, **중단·절단 없음**.

```
첫 유효 데이터 = WL × tCK + tDQSS          (WRITE 상승 에지 기준)
첫 WDQS 에지  = (WL − 1) × tCK + tDQSS
```

`WL`은 `MR1` OP[4:0]에 있습니다.

### 비정합 WDQS-DQ 경로

READ와 결정적으로 다른 점이 여기 있습니다.

> HBM4는 **비정합(un-matched) WDQS-DQ 경로**를 사용하므로, WDQS는 `tDQSS` 안에 머물러야 하고 DQ는 `tDIVW`를 만족하며 **WDQS에 center-aligned 되도록 트레이닝**될 수 있다. DQ 데이터는 `tDIVW`(data input valid window) 동안 유지되어야 하며, **온도·전압 변동에 따른 타이밍 변화를 보상하기 위해 WDQS를 주기적으로 트레이닝**해 `tDIVW` 창 안에서 DQ에 center-aligned 상태를 유지할 수 있다. — §6.3.3.3 (요약)

[01장](../01_landscape_organization/)에서 §2 Features의 *"비정합(unmatched) 데이터 인터페이스"* 를 보았는데, 그 귀결이 이것입니다.

:::caution[정합 경로였다면 필요 없었을 일]
경로가 정합(matched)이면 WDQS와 DQ가 같은 지연을 겪으므로 한 번 맞춰두면 유지됩니다. 비정합이면 **온도·전압이 변할 때 둘 사이의 상대 위상이 흔들립니다.**

그래서 HBM4의 write 경로는 **일회성 캘리브레이션이 아니라 주기적 트레이닝**을 전제합니다. 컨트롤러는 정상 동작 중에 트레이닝 창을 확보해야 하고, 그 트레이닝의 WDQS 토글 수 역시 **짝수 규칙의 대상**입니다([05장](../05_clocking_dbi/)).

이것이 [`hbm_dv`](../../hbm_dv/05_mixed_level/)에서 PHY가 mixed-level 검증 대상인 이유이기도 합니다 — 트레이닝 수렴은 회로 특성에 의존합니다.
:::

버스트 데이터는 **WDQS의 연속 에지에서 캡처**되며, 스트로브 타이밍은 `WDQS_t`와 `WDQS_c`의 **교차점 기준**으로 측정됩니다([05장](../05_clocking_dbi/)의 에지 정의).

## 4. `tCCD` 세 갈래 — SID가 타이밍을 가르는 실제 사례

[02장](../02_addressing_bank_groups/)에서 Table 6을 보며 *"READ→READ에만 세 번째 값 `tCCDR`이 있다"* 고 예고했습니다. 그 조건이 §6.3.1 Note 7과 AC 타이밍 절에 정의되어 있습니다.

| 연속 READ 조건 | 적용 파라미터 |
|---|---|
| **같은 뱅크 그룹** | `tCCDL` |
| 다른 뱅크 그룹, **같은 SID** | `tCCDS` |
| 다른 뱅크 그룹, **다른 SID** | **`tCCDR`** |

규격의 서술을 요약하면 이렇습니다.

> `tCCDR`은 **8·12·16-High HBM 장치**를 위한 파라미터로, **서로 다른 stack ID(SID) 사이의 seamless 연속 READ 커맨드**에 대해 `tCCDS` 대신 사용된다. **`tCCDR(min)` 값은 벤더 지정**이며 **`tCCDS + 1` ~ `2 nCK` 범위**가 지원된다. `tCCDR(min)`은 **동작 주파수에 의존**하므로 벤더 데이터시트를 참조해야 한다. **seamless WRITE 커맨드에는 통상의 `tCCDS`가 적용된다.** — §10 Note 17 (요약)

:::tip[02장의 예고가 여기서 실현된다]
[02장](../02_addressing_bank_groups/)에서 Table 4 Note 4를 인용하며 *"일부 AC 타이밍 파라미터가 SID에 연동될 수 있다"* 고 했고, 그래서 **타이밍 상수를 SID로 인덱싱 가능한 구조**로 두라고 권했습니다.

`tCCDR`이 바로 그 사례입니다. 그리고 세 가지가 더 드러납니다.

1. **4-High에는 적용되지 않습니다** — SID가 없으니 당연합니다.
2. **READ에만 적용되고 WRITE에는 적용되지 않습니다.** 방향에 따라 SID 의존성이 다릅니다.
3. **값이 벤더 지정이고 주파수 의존적**입니다. 컨트롤러가 상수로 박으면 이식성을 잃습니다.
:::

**설계 함의**: READ→READ 간격 판정이 **2택이 아니라 3택**입니다. 뱅크 그룹만 비교하는 로직은 서로 다른 SID로 가는 seamless READ에서 `tCCDS`를 적용해 **간격을 과소 산정**합니다.

## 5. MRS — 그리고 패리티 전이의 비대칭

`MRS`는 1 사이클 column 커맨드이며 **row 버스에 `RNOP`를 요구**합니다(§6.3.3.4). `MA[4:0]`가 20개 MR 중 하나를 고르고 `OP[7:0]`이 적재할 값입니다.

### 발행 조건과 대기 시간

| 항목 | 내용 |
|---|---|
| 전제 | **모든 뱅크 idle**, 선행 READ로부터 `tRDMRS` 경과, 선행 WRITE로부터 `tWRMRS` 경과 |
| `tMRD` | MRS 사이클 시간 — **두 MRS 사이의 최소 간격** |
| `tMOD` | MRS → 비-MRS 커맨드 지연 — 장치가 기능을 갱신하는 데 필요. **`RNOP`·`CNOP`는 제외** |

`tMOD`에서 `RNOP`·`CNOP`가 제외된다는 점이 유용합니다 — 대기 구간을 NOP로 채우는 것은 허용됩니다.

### 패리티 전이의 비대칭

> `MRS` 커맨드와 함께 패리티가 평가되는 것은 **이 MRS 이전에 CA parity가 이미 활성화된 경우**다. `MRS` 커맨드로 CA parity가 **활성화되면**, HBM4 DRAM은 **`RNOP`과 `CNOP`을 포함한 모든 후속 커맨드**가 올바른 패리티로 발행될 것을 요구하며, 이는 **CA parity를 비활성화하는 MRS의 `tMOD`가 만료될 때까지** 지속된다. — §6.3.3.4 (요약)

두 방향이 다릅니다.

```
켤 때 : MRS(enable)  자신은 패리티 검사 안 됨 → 그 이후 모든 커맨드는 패리티 필요
끌 때 : MRS(disable) 자신은 패리티 필요       → 그 tMOD 만료 후에야 패리티 불필요
```

:::caution[전환 구간을 놓치기 쉽다]
비활성화 MRS를 발행한 **직후에 패리티 계산을 멈추면 위반**입니다. `tMOD`가 만료될 때까지는 여전히 올바른 패리티가 요구됩니다.

반대로 활성화 MRS **자신**에 패리티를 실으려 하면, 아직 활성화 전이므로 불필요합니다(다만 [06장](../06_row_commands/) Note 2에 따라 `APAR` 핀 자체는 항상 유효 레벨로 구동해야 합니다).

**설계 결론**: 패리티 생성 로직의 활성 구간은 `MRS(enable)` **다음 커맨드**부터 `MRS(disable)` **+ `tMOD`** 까지입니다. MRS 발행 시점과 일치시키면 양쪽 경계에서 어긋납니다.
:::

## 6. Power-Down (PDE, PDX)

### 진입 조건 — "완료"의 정의

> Power-down Entry는 **어느 한쪽 PC에서라도** read 또는 write 동작이 진행 중일 때 발행되어서는 안 된다. — §6.3.4.1

"진행 중"의 반대인 **완료**를 규격이 정확히 정의합니다.

| 동작 | 완료 시점 |
|---|---|
| **read** | 마지막 데이터 요소(**활성 시 패리티 포함**)와 **RDQS postamble**이 출력으로 전송 완료 |
| **write** | 마지막 데이터 요소(패리티 포함)가 `tWR` 만족 상태로 **메모리 배열에 기록 완료**. **auto-precharge write**의 경우 대신 **mode register에 프로그램된 `WR` 클럭 수**가 경과해야 함 |

read 완료에 **postamble까지 포함**된다는 점, write with auto-precharge는 **`tWR`이 아니라 MR의 `WR` 값**을 기준으로 한다는 점이 놓치기 쉽습니다.

### 진행 중이어도 되는 것

> Power-down Entry는 row activation, precharge, auto precharge, refresh 같은 **다른 동작이 진행 중일 때는 발행될 수 있으나**, 그런 동작이 완료될 때까지 **power-down IDD 규격은 적용되지 않는다.** — §6.3.4.1

즉 **금지가 아니라 전력 이득이 지연**될 뿐입니다. 스케줄러가 refresh 완료를 기다릴지, 일찍 진입할지는 설계 판단입니다.

### 두 종류의 Power-Down

| 진입 시 상태 | 명칭 |
|---|---|
| 모든 뱅크 idle | **precharge power-down** |
| 어느 뱅크든 행이 활성 | **active power-down** |

[03장](../03_init_reset_power/)에서 확인한 *"장치는 precharged power-down 상태로 리셋된다"* 가 여기 연결됩니다.

### 유지 요건

- `PDE`와 `CNOP`를 **`tCPDED` 기간 유지**
- CK 클럭을 **`tCKPDE` 사이클 동안 안정 유지**

## 7. Self Refresh (SRE, SRX)

Self refresh는 **시스템의 나머지가 전원 차단되어도** 데이터를 유지하며, 이 모드에서 장치는 **외부 클럭 없이** 데이터를 보존합니다(§6.3.4.2). 커맨드는 `R[9:0]`에서 받으며 **`C[7:0]`에 `CNOP`를 요구**합니다.

### 진입 조건

> Self refresh entry는 **두 pseudo channel의 모든 뱅크가 precharge**되고 `tRP`가 만족되었을 때, 선행 `READ`의 마지막 데이터 요소가 밀려나갔을 때(`tRDSRE`), 또는 선행 `MRS`로부터 `tMOD`가 충족되었을 때에만 허용된다. Self refresh 모드 진입 후 **`tCPDED`가 만족될 때까지 `PDE`와 `CNOP` 커맨드가 요구된다.** — §6.3.4.2 (요약)

**두 PC 모두** precharge되어야 한다는 점이 중요합니다 — [01장](../01_landscape_organization/)에서 본 *"저전력은 두 PC 공통"* 의 구체적 형태입니다.

그리고 **SRE 이후에 `PDE`를 유지해야 한다**는 규정이 특이합니다. 자기 자신과 다른 커맨드를 이어 붙이는 구조입니다.

### 유지와 종료

- `SRE` 등록 후 **`R0`를 LOW로 유지**해야 self refresh가 지속됩니다.
- **모든 전원 핀**(`VDDC`·`VDDQ`·`VPP`·`VDDQL`)이 유효 레벨이어야 합니다.
- 장치는 진입 후 **`tCKSR` 기간 안에 최소 한 번의 내부 refresh**를 개시합니다.
- **클럭은 내부적으로 비활성화**되어 전력을 절약합니다. 최소 체류 시간은 `tCKSR`입니다.
- 사용자는 `SRE` 등록 후 **`tCKSRE`가 지나면 외부 클럭을 멈추거나 주파수를 바꿀 수 있습니다.**
- 다만 종료 전에 **클럭이 재시작되어 `tCKSRX` 동안 안정**되어야 합니다.
- `RESET_n` 수신기와 `R0` 수신기는 계속 활성이며, **`RESET_n` = HIGH, `R0` = LOW**가 유지되어야 합니다.

:::tip[주파수 변경의 창]
"self refresh 중에 외부 클럭 주파수를 바꿀 수 있다"는 조문이 **DVFS의 실현 경로**입니다. [04장](../04_mode_registers/)에서 타이밍 MR이 주파수 종속이라고 했는데, 그 재설정을 수행할 안전한 구간이 여기입니다.

순서는 이렇습니다 — SRE 진입 → `tCKSRE` 경과 → 클럭 변경 → `tCKSRX` 동안 안정 → SRX → 새 주파수에 맞는 MR 재적재.

그리고 [05장](../05_clocking_dbi/)에서 본 대로 **self refresh 종료 시 WDQS 분주기가 초기화**되므로, 컨트롤러의 토글 패리티도 함께 리셋해야 합니다.
:::

## ⚙️ 설계 적용 (RTL / Front-end)

### 8.1 `tCCD` 3택 판정

[02장](../02_addressing_bank_groups/)의 2택 코드를 확장해야 합니다.

```systemverilog
// READ->READ 간격은 뱅크 그룹과 SID 양쪽에 의존한다 (Table 6 Note 2, §10 Note 17)
wire same_group = (bank_group == last_bank_group_q);
wire same_sid   = (dec.sid    == last_sid_q);

wire [TW-1:0] t_ccd_rd = same_group ? T_CCDL          // 같은 뱅크 그룹
                       : same_sid   ? T_CCDS          // 다른 그룹, 같은 SID
                                    : T_CCDR;         // 다른 그룹, 다른 SID

// WRITE->WRITE는 SID 의존성이 없다 — 2택 그대로
wire [TW-1:0] t_ccd_wr = same_group ? T_CCDL : T_CCDS;
```

**`T_CCDR`은 컴파일 상수로 박으면 안 됩니다.** 벤더 지정이고 주파수 의존적이므로 설정값으로 받아야 하며, 4-High 구성에서는 SID가 없어 이 경로 자체가 무의미합니다.

### 8.2 버스트 점유 모델

중단·절단이 없으므로 스케줄러는 발행 시점에 **전체 점유 구간을 확정**할 수 있습니다.

```systemverilog
// BL8 고정, 중단/절단 없음 (§6.3.3.2, §6.3.3.3)
// 데이터 버스 점유는 발행 시점에 결정된다 — 이후 취소 경로가 없다.
localparam int BL = 8;
localparam int DATA_BEATS_HALF = BL / 2;   // DDR: 8 UI = 4 클럭

always_ff @(posedge ck) begin
  if (rd_issue) dq_busy_until_q <= now + rl_q + DATA_BEATS_HALF;
  else if (wr_issue) dq_busy_until_q <= now + wl_q + DATA_BEATS_HALF;
end
```

**설계 판단**: 중단이 없다는 것은 구현을 단순하게 하지만, **긴급 요청이 들어와도 진행 중인 버스트를 자를 수 없다**는 뜻이기도 합니다. 지연 민감 트래픽이 있다면 발행 시점에 우선순위를 반영해야 하고, 발행 후에는 방법이 없습니다.

### 8.3 스트로브 시퀀서

preamble/postamble 개수가 고정이므로 카운터로 구현합니다.

```systemverilog
// READ:  WDQS 4-pre / 2-post,  RDQS 2-pre / 2-post
// WRITE: WDQS 2-pre / 2-post                        (§6.3.3.2, §6.3.3.3)
localparam int WDQS_PRE_RD = 4, WDQS_PST_RD = 2;
localparam int WDQS_PRE_WR = 2, WDQS_PST_WR = 2;

// 05장의 짝수 불변식과 함께 검사한다 — 규정값 자체가 짝수이므로
// 여기서 홀수가 나오면 시퀀서 버그다.
`ifndef SYNTHESIS
  a_pre_post_even: assert final
    (((WDQS_PRE_RD + WDQS_PST_RD) % 2 == 0) &&
     ((WDQS_PRE_WR + WDQS_PST_WR) % 2 == 0))
    else $error("preamble+postamble must be even (WDQS/2 phase)");
`endif
```

### 8.4 패리티 활성 구간

전이 비대칭을 그대로 옮깁니다.

```systemverilog
// 켤 때: MRS(enable) 다음 커맨드부터
// 끌 때: MRS(disable) + tMOD 만료 후부터            (§6.3.3.4)
always_ff @(posedge ck) begin
  if (mrs_capar_enable)  parity_required_q <= 1'b1;          // 즉시 다음 커맨드부터
  else if (mrs_capar_disable) begin
    disable_pending_q <= 1'b1;
    tmod_cnt_q        <= T_MOD;
  end else if (disable_pending_q) begin
    if (tmod_cnt_q == 0) begin
      parity_required_q <= 1'b0;                              // tMOD 만료 후에야 해제
      disable_pending_q <= 1'b0;
    end else
      tmod_cnt_q <= tmod_cnt_q - 1;
  end
end
```

### 8.5 저전력 진입 게이팅

"완료"의 정의를 논리로 옮깁니다.

```systemverilog
// PDE는 어느 PC에서든 read/write가 진행 중이면 금지 (§6.3.4.1)
// read 완료 = 마지막 데이터 + (패리티) + RDQS postamble 전송 완료
// write 완료 = tWR 만족, 단 auto-precharge write는 MR의 WR 클럭 수 경과
wire rd_done_pc = rd_data_done & rdqs_postamble_done;
wire wr_done_pc = auto_pre_q ? (wr_cnt_q >= mr_wr_cycles) : (wr_cnt_q >= t_wr_cycles);

wire pde_allowed = (rd_done_pc0 & wr_done_pc0)
                 & (rd_done_pc1 & wr_done_pc1);      // 양쪽 PC 모두

// SRE는 더 강한 조건 — 두 PC의 모든 뱅크가 precharge + tRP 만족 (§6.3.4.2)
wire sre_allowed = all_banks_precharged_pc0 & all_banks_precharged_pc1
                 & trp_met & trdsre_met & tmod_met;
```

**두 조건의 강도 차이**에 주의하세요. `PDE`는 read/write만 끝나면 되지만(행이 열려 있어도 active power-down으로 진입), `SRE`는 **모든 뱅크가 닫혀 있어야** 합니다.

## 9. 대표 문제 — dry-run

### 문제 1 — `tCCD` 판정

> 12-High 구성에서 연속 READ를 발행한다. 첫 READ는 `SID=0`, 뱅크 5(Group A), 두 번째는 `SID=1`, 뱅크 20(Group C)이다. 어떤 파라미터를 적용하는가?

<details>
<summary>풀이</summary>

- 뱅크 그룹: 5 → Group A, 20 → Group C. **다른 그룹**
- SID: 0 → 1. **다른 SID**

따라서 **`tCCDR`** 이 적용된다. `tCCDS`가 아니다.

**값의 성격**: `tCCDR(min)`은 벤더 지정이며 **`tCCDS + 1` ~ `2 nCK`** 범위이고 **주파수 의존적**이다(§10 Note 17). 즉 `tCCDS`보다 **길다.**

**함정**: 뱅크 그룹만 비교하는 로직은 `tCCDS`를 적용해 간격을 **과소 산정**하고, seamless READ에서 규격 위반이 난다. 이 위반은 서로 다른 SID로 가는 연속 읽기에서만 나타나므로 **4-High 구성 테스트에서는 재현되지 않는다.**

**참고**: 만약 같은 시퀀스가 WRITE였다면 **`tCCDS`** 가 적용된다 — SID 의존성은 READ에만 있다.
</details>

### 문제 2 — 패리티 비활성화 전환

> CA parity가 켜진 상태에서 `MRS`로 비활성화했다. 그 직후 발행하는 `RNOP`에 올바른 패리티를 실어야 하는가?

<details>
<summary>풀이</summary>

**실어야 한다.**

§6.3.3.4는 CA parity가 MRS로 활성화되면 *"CA parity를 **비활성화하는** MRS의 **`tMOD`가 만료될 때까지**"* 모든 후속 커맨드(**`RNOP`·`CNOP` 포함**)가 올바른 패리티로 발행되어야 한다고 규정한다.

즉 비활성화 MRS를 발행했다고 즉시 꺼지는 것이 아니라, **그 MRS의 `tMOD`가 만료된 이후**부터 패리티가 불필요해진다.

**설계 결론**: 패리티 생성 로직을 MRS 발행과 동시에 끄면 `tMOD` 구간에서 위반이 난다. 활성 구간은 **`MRS(enable)` 다음 커맨드 ~ `MRS(disable)` + `tMOD`** 다.

**대조**: 활성화 방향은 반대다. `MRS(enable)` **자신**은 아직 패리티가 활성이 아니므로 검사되지 않는다.
</details>

### 문제 3 — Power-down 진입 판정

> 컨트롤러가 `WRA`(auto-precharge write)를 발행하고 `tWR` 시간이 경과했다. 이제 `PDE`를 발행해도 되는가?

<details>
<summary>풀이</summary>

**정보가 부족하다.** auto-precharge write의 완료 기준은 `tWR`이 **아니다.**

§6.3.4.1은 write 완료를 *"마지막 데이터 요소가 `tWR` 만족 상태로 메모리 배열에 기록 완료"* 로 정의하면서, **auto-precharge write의 경우 대신 mode register에 프로그램된 `WR` 클럭 수가 경과해야 한다**고 규정한다.

`MR3`의 `WR` 값은 `RU{tWR/tCK}` **이상**으로 프로그램되므로([04장](../04_mode_registers/)), **아날로그 `tWR`보다 길 수 있다.** 아날로그 `tWR`만 보고 진입하면 이르다.

**설계 결론**: 저전력 진입 게이팅에서 일반 write와 auto-precharge write의 완료 조건을 **분리**해야 한다. 그리고 이 판정은 **두 PC 모두**에 대해 이뤄져야 한다.

**덧붙임**: 만약 refresh가 진행 중이라면 `PDE` 발행 자체는 **허용**된다. 다만 refresh가 끝날 때까지 power-down IDD 규격이 적용되지 않으므로 **전력 이득이 지연**될 뿐이다.
</details>

## 🔍 검증 연결

- 버스트 타이밍과 지연 관계를 assertion으로 → [`hbm_dv` Ch09 Assertion·Checker](../../hbm_dv/09_assertion_checker/)
- `tCCD` 3택을 coverage 축으로 분리 → [`hbm_dv` Ch10 Coverage·회귀](../../hbm_dv/10_coverage_regression/)
- 비정합 경로 트레이닝이 mixed 검증인 이유 → [`hbm_dv` Ch05 Mixed-Level](../../hbm_dv/05_mixed_level/)

## 핵심 정리

- READ/WRITE 모두 **버스트 길이 8, column 주소 유일, 중단·절단 없음**. 발행 시점에 버스 점유가 확정된다.
- ⚠️ **읽기 데이터를 트리거하는 것은 WDQS다** — RDQS가 WDQS에서 생성되기 때문이다. 읽기 중에도 컨트롤러가 WDQS를 공급해야 한다.
- preamble/postamble은 **고정**이다 — READ의 WDQS **4+2**, RDQS **2+2**, WRITE의 WDQS **2+2**. **전부 짝수**이며, 이는 [05장](../05_clocking_dbi/)의 `WDQS/2` 위상 보존 규칙과 일치한다.
- read 버스트의 **첫 데이터 비트는 RDQS의 세 번째 상승 에지**와 동기된다.
- **HBM4는 비정합 WDQS-DQ 경로**를 쓴다 → **주기적 트레이닝**으로 온도·전압 변동을 보상해야 한다. 일회성 캘리브레이션으로는 부족하다.
- **`tCCD`는 3택**이다 — 같은 그룹 `tCCDL` / 다른 그룹·같은 SID `tCCDS` / **다른 그룹·다른 SID `tCCDR`**. `tCCDR`은 **READ 전용**, **8·12·16-High 전용**, **벤더 지정·주파수 의존**이다.
- `MRS`는 **row 버스에 `RNOP`를 요구**하며, **모든 뱅크 idle** + `tRDMRS` + `tWRMRS`가 전제다. `tMOD`에서 **`RNOP`·`CNOP`는 제외**된다.
- 패리티 전이는 **비대칭**이다 — 켤 때는 다음 커맨드부터, 끌 때는 **`tMOD` 만료 후**부터.
- `PDE` 금지 조건은 **양쪽 PC의 read/write 진행 중**이다. read 완료에는 **postamble**이, auto-precharge write 완료에는 **MR의 `WR` 클럭 수**가 포함된다.
- refresh 등이 진행 중이어도 `PDE` 발행은 **허용**되며, 전력 이득만 지연된다.
- `SRE`는 **두 PC의 모든 뱅크 precharge**를 요구하고, 진입 후 `tCPDED`까지 **`PDE`와 `CNOP`를 유지**해야 한다. **`R0` LOW 유지**가 self refresh 지속 조건이다.
- self refresh 중 **외부 클럭 정지·주파수 변경이 가능**하다 — DVFS의 실현 경로다.

## Further Reading

- **규격**: JESD270-4 §6.3.3 Column Commands (Figure 33–50) · §6.3.4 Power-Mode Commands (Figure 51–60) · §10 AC Timings (`tCCDR`)
- **다음 장**: [08 — Parity](../08_parity/) — CA parity와 데이터 패리티, `PL`
- **관련**: [04 — Mode Register](../04_mode_registers/) (`MR1` WL·PL, `MR2` RL, `MR3` WR) · [05 — 클럭킹](../05_clocking_dbi/) (짝수 규칙)
- **이해도 점검**: [퀴즈](../quiz/07_column_commands_quiz/)
