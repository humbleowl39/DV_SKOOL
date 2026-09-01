---
title: "07 — Column 커맨드와 저전력"
description: JESD270-4 §6.3.3–6.3.4 · READ/WRITE 버스트와 지연, tCCD 세 갈래, MRS 제약, Power-Down과 Self Refresh
---

:::tip[🎯 Learning Objectives]
이 모듈을 마치면:

- **Trace** READ 커맨드부터 첫 유효 데이터까지의 경로를 `RL`·`tDQSS`·스트로브 preamble과 함께 추적한다.
- **Differentiate** READ→READ 간격이 `tCCDL`·`tCCDS`·`tCCDR` 세 갈래로 갈리는 조건을 구분한다.
- **Explain** 비정합(un-matched) WDQS-DQ 경로가 주기적 트레이닝을 요구하는 이유를 설명한다.
- **Sequence** Power-Down과 Self Refresh 진입 조건을 "완료"의 정의와 함께 정리하고, 그것을 두 PC AND 술어 함수로 구현한다.
- **Analyze** CA parity를 켜고 끄는 MRS가 만드는 비대칭 전이를 분석하고, 전환 구간 안에 커맨드를 발행해야만 그 비대칭이 검증되는 이유를 설명한다.
- **Evaluate** `tCCD`를 2택으로 판정하면 왜 **놓친 버그**가 되고, WRITE에 `tCCDR`을 적용하면 왜 **false FAIL**이 되는지 판단한다.
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

**검증 함의**: READ→READ 간격 판정이 **2택이 아니라 3택**입니다. 뱅크 그룹만 비교하는 checker는 서로 다른 SID로 가는 seamless READ에서 `tCCDS`를 적용해 기준을 **낮게** 잡고, 그러면 **실제 위반이 조용히 통과**합니다. 반대로 WRITE에까지 `tCCDR`을 적용하면 정상 동작이 FAIL로 보고됩니다 — 틀리는 방향에 따라 결과가 정반대입니다(8.1절).

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

**검증 결론**: 패리티 요구 구간은 `MRS(enable)` **다음 커맨드**부터 `MRS(disable)` **+ `tMOD`** 까지입니다. checker의 구간 경계를 MRS 발행 시점과 일치시키면 양쪽에서 어긋나고, 무엇보다 **전환 구간 안에서 커맨드를 발행하지 않으면 이 비대칭은 한 번도 검증되지 않습니다**(8.4 ②).
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

즉 **금지가 아니라 전력 이득이 지연**될 뿐입니다. 검증에서는 이 구분이 중요합니다 — 진행 중 진입을 checker가 위반으로 보고하면 **false FAIL**입니다. 규격이 허용한 동작이므로 자극도 이 경우를 만들어야 하고(`cp_pd_precond.during_other`), 다만 그 구간의 IDD 규격은 적용되지 않는다는 점을 기대값에 반영해야 합니다.

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

## 🔬 검증 적용

### 8.1 무엇이 깨질 수 있는가

이 장에는 **환경 구조 자체를 바꾸는 조문**이 하나 있습니다 — 읽기 데이터를 트리거하는 것이 WDQS라는 §6.3.3.2입니다. read agent와 write agent를 분리한 환경은 이 조문에서 무너집니다.

| 조문 | 위반 형태 | 증상 | 잡히는 시점 |
|---|---|---|---|
| §6.3.3.2 — **WDQS가 read 데이터를 트리거** | read-only 자극이 WDQS를 공급하지 않음 | 데이터가 나오지 않거나 위상이 어긋남 | 즉시(원인 오진) |
| §6.3.3.2 — preamble/postamble **고정값** | 임의로 바꿈 | [05장](../05_clocking_dbi/) 짝수 불변식이 깨짐 | 지연·간헐 |
| §10 Note 17 — **`tCCDR`** (다른 SID) | READ→READ를 2택으로 판정 | 간격을 **과소 산정** → 실제 위반을 통과시킴 | **없음** |
| §10 Note 17 — `tCCDR`은 **READ 전용** | WRITE에도 적용 | 과보수 → **false FAIL** | 즉시(잘못된 방향) |
| §10 Note 17 — **벤더 지정·주파수 의존** | 상수로 박음 | 다른 장치·주파수에서 틀린 기준 | 없음 |
| §6.3.3.4 — 패리티 전이 **비대칭** | 켜기·끄기를 대칭으로 처리 | 양쪽 경계에서 어긋남 | 전환 시퀀스에서만 |
| §6.3.4.1 — read 완료에 **postamble 포함** | 마지막 데이터로 완료 판정 | 조기 PD 진입 | 없음 |
| §6.3.4.1 — auto-precharge write는 **MR의 `WR` 값** | `tWR`로 판정 | 조기 PD 진입 | 없음 |
| §6.3.4.1 — **어느 한쪽 PC라도** 진행 중이면 금지 | 한 PC만 확인 | 반대 PC의 동작을 자름 | 산발적 |
| §6.3.4.2 — SRE는 **두 PC 모두** precharge | 한쪽만 확인 | 규격 위반 | 없음 |
| §6.3.4.2 — SRE 후 **`PDE` 유지** | 생략 | 진입 실패 | 즉시 |
| §6.3.4.2 — SR 중 **주파수 변경 가능** | 그 창을 안 씀 | DVFS 경로가 통째로 미검증 | 없음 |

:::caution["쓰기" 스트로브가 "읽기" 데이터를 몰고 나온다]
§6.3.3.2은 검증 환경의 **에이전트 경계**를 직접 건드립니다.

일반적인 메모리 TB는 read 경로와 write 경로를 나눕니다. 그런데 HBM4에서는 **read 동작 중에도 컨트롤러가 WDQS를 공급해야** 하고, 그것도 **4펄스 preamble + 2펄스 postamble**이라는 고정 규격으로 공급해야 합니다.

| 동작 | 스트로브 | preamble | postamble | 합 |
|---|---|---|---|---|
| READ | **WDQS** | **4** | 2 | 6 |
| READ | RDQS | 2 | 2 | 4 |
| WRITE | WDQS | 2 | 2 | 4 |

세 합이 전부 짝수인 것이 [05장](../05_clocking_dbi/) 불변식과 맞물립니다. 곧 **read 트랜잭션도 WDQS 토글 카운터에 기여**하며, read만 도는 테스트에서도 짝수 불변식을 확인해야 합니다.

환경 관점의 귀결: **WDQS 구동은 read/write 어느 한쪽 agent의 소유가 아닙니다.** 채널 레벨에서 공급되고 두 방향이 공유하는 자원으로 모델링해야 합니다. read agent만 돌리는 테스트에서 WDQS가 멈춰 있으면 데이터가 나오지 않고, 그 증상은 "DUT가 read에 응답하지 않는다"로 보입니다.
:::

:::caution[`tCCDR` — 틀리는 방향에 따라 결과가 정반대다]
READ→READ 간격은 **3택**입니다.

| 조건 | 파라미터 |
|---|---|
| 같은 뱅크 그룹 | `tCCDL` |
| 다른 그룹, **같은 SID** | `tCCDS` |
| 다른 그룹, **다른 SID** | **`tCCDR`** |

`tCCDR ≥ tCCDS + 1`이므로 방향에 따라 결과가 갈립니다.

- **2택으로 판정하면**(다른 SID에 `tCCDS` 적용) checker가 기준을 **낮게** 잡습니다. 실제 위반이 통과합니다 — **놓친 버그**.
- **WRITE에도 `tCCDR`을 적용하면** 기준을 **높게** 잡습니다. 정상 동작이 실패로 보고됩니다 — **false FAIL**.

첫 번째가 훨씬 위험합니다. 조용하기 때문입니다. 그리고 4-High 프로파일만 도는 회귀에서는 SID가 없어 `tCCDR` 자체가 성립하지 않으므로, **8/12/16-High 구성을 돌리지 않으면 이 경로는 존재조차 확인되지 않습니다.**
:::

### 8.2 어떻게 잡는가 — 수단 선택

| 규칙 | 성격 | 수단 | 이유 |
|---|---|---|---|
| `tCCD` 3택 | **시간 관계** | **SVA** | 두 커맨드 사이 간격의 국소 판정 |
| read 중 WDQS 공급 | **불변식** | **SVA** | 모든 read에 성립 |
| 패리티 활성 구간 | **구간 상태** | **구간 모델 + SVA** | 경계가 커맨드가 아니라 `tMOD` 만료다 |
| PD/SR 진입 "완료" | **복합 술어** | **reference model의 술어 함수** | 조건이 여럿이고 두 PC AND다. 한곳에 모아야 한다 |

**① `tCCD` 3택**

```systemverilog
// §10 Note 17 — 다른 SID 로 가는 seamless READ 는 tCCDS 가 아니라 tCCDR.
// WRITE 에는 통상의 tCCDS 가 적용된다.
function automatic int unsigned ccd_min(input bit is_read,
                                        input bit same_group, input bit same_sid);
  if (same_group)      return T_CCDL;
  if (!is_read)        return T_CCDS;      // WRITE 는 SID 를 보지 않는다
  return same_sid ? T_CCDS : T_CCDR;       // READ 만 3택
endfunction

property p_ccd(bit is_read);
  int unsigned req;
  @(posedge ck) disable iff (!rst_n)
    (col_cmd_vld && (col_is_read == is_read),
       req = ccd_min(is_read, (bg == last_bg[pc]), (sid == last_sid[pc])))
      |-> (cycles_since_last_col[pc] >= req);
endproperty
a_ccd_read : assert property (p_ccd(1'b1))
  else `uvm_error("tCCD", "READ→READ 간격 위반 (§10 Note 17)")
a_ccd_write: assert property (p_ccd(1'b0))
  else `uvm_error("tCCD", "WRITE→WRITE 간격 위반")

// 세 분기를 모두 겪었는가. tCCDR 은 8Hi 이상 구성에서만 성립한다.
c_ccdl: cover property (@(posedge ck) col_cmd_vld && (bg == last_bg[pc]));
c_ccds: cover property (@(posedge ck) col_cmd_vld && (bg != last_bg[pc]) && (sid == last_sid[pc]));
c_ccdr: cover property (@(posedge ck) col_cmd_vld &&  col_is_read
                                   && (bg != last_bg[pc]) && (sid != last_sid[pc]));
```

`T_CCDR` 은 **환경 파라미터**여야 합니다. 벤더 지정이고 주파수 의존이므로(§10 Note 17), 다른 프로파일로 갈 때 값이 바뀝니다.

**② 패리티 활성 구간 — 비대칭을 그대로 모델링한다**

경계가 커맨드 자체가 아니라 **`tMOD` 만료**에 걸려 있고, 켜기와 끄기가 다릅니다.

```systemverilog
// §6.3.3.4
//   켤 때 : MRS(enable) 자신은 검사 안 됨 → 그 다음 커맨드부터 패리티 필요
//   끌 때 : MRS(disable) 자신은 패리티 필요 → tMOD 만료 후에야 불필요
// 두 경계를 같은 시점으로 두면 양쪽에서 어긋난다.
bit parity_required;

always @(posedge ck) begin
  if (mrs_vld && mrs_enables_capar)
    fork begin @(posedge ck); parity_required <= 1'b1; end join_none   // 다음 커맨드부터
  else if (mrs_vld && mrs_disables_capar)
    fork begin repeat (T_MOD) @(posedge ck); parity_required <= 1'b0; end join_none
end

// 요구 구간 안의 모든 커맨드 — RNOP·CNOP 포함 — 는 올바른 패리티를 가져야 한다
a_parity_in_window: assert property (@(posedge ck) disable iff (!rst_n)
    (parity_required && any_cmd_vld) |-> parity_correct)
  else `uvm_error("CAPAR", "패리티 요구 구간에서 잘못된 패리티 (§6.3.3.4)")

// 전환 구간에 실제로 커맨드를 발행해 봤는가 — 안 그러면 비대칭은 미검증이다
c_cmd_in_disable_window: cover property (@(posedge ck)
    mrs_vld && mrs_disables_capar ##1 any_cmd_vld[->1] ##0 parity_required);
```

**③ PD/SR 진입 "완료" — 술어를 한곳에 모은다**

조건이 여럿이고 **두 PC 모두**에 대해 성립해야 하므로, 흩어 놓으면 반드시 빠집니다.

```systemverilog
// §6.3.4.1 — "완료" 의 정의가 동작마다 다르다.
function automatic bit pc_ready_for_pd(int pc);
  // read: 마지막 데이터 + 패리티 + RDQS postamble 까지 전송 완료
  if (rd_in_flight[pc] || rdqs_postamble_active[pc]) return 1'b0;
  // write: tWR 만족 후 배열 기록 완료.
  // 단 auto-precharge write 는 tWR 이 아니라 MR 에 프로그램된 WR 클럭 수 기준.
  if (wr_in_flight[pc]) begin
    if (wr_was_auto_precharge[pc]) begin
      if (cycles_since_wr[pc] < mr_wr_cycles) return 1'b0;
    end else begin
      if (cycles_since_wr[pc] < T_WR)         return 1'b0;
    end
  end
  return 1'b1;
endfunction

// 어느 한쪽 PC 라도 진행 중이면 금지 (§6.3.4.1) — AND 다
a_pde_both_pc: assert property (@(posedge ck) disable iff (!rst_n)
    pde_vld |-> (pc_ready_for_pd(0) && pc_ready_for_pd(1)))
  else `uvm_error("PDE", "read/write 진행 중 PDE 발행 (§6.3.4.1)")

// SRE 는 더 강하다 — 두 PC 의 모든 뱅크가 precharge 되고 tRP 만족 (§6.3.4.2)
a_sre_precharged: assert property (@(posedge ck) disable iff (!rst_n)
    sre_vld |-> (bank_active_mask[0] == '0 && bank_active_mask[1] == '0
                 && trp_met[0] && trp_met[1]))
  else `uvm_error("SRE", "두 PC 가 모두 precharge 되지 않은 상태에서 SRE (§6.3.4.2)")
```

`wr_was_auto_precharge[pc]` 분기가 이 함수의 요점입니다. 두 경우를 같게 처리하면 **auto-precharge write 직후에 조기 진입**하게 되고, MR의 `WR` 값이 `tWR`보다 크게 설정된 프로파일에서만 드러납니다.

### 8.3 무엇을 덮었다고 말할 수 있는가

```systemverilog
covergroup cg_hbm4_column with function sample(
    ccd_sel_e ccd, bit is_read, pd_precond_e precond, pd_type_e pdtype,
    bit parity_window, bit freq_changed_in_sr, int stack_high);
  option.per_instance = 1;

  // --- tCCD 세 갈래 (§10 Note 17) ---------------------------------------
  cp_ccd : coverpoint ccd {
    bins ccdl = {CCD_L};
    bins ccds = {CCD_S};
    bins ccdr = {CCD_R};                  // 8/12/16-Hi 에서만 성립
  }
  cp_dir : coverpoint is_read { bins rd = {1}; bins wr = {0}; }
  // tCCDR 은 READ 에만 있다 — WRITE 쪽에 히트가 나면 자극이나 모델이 틀린 것
  x_ccd_dir : cross cp_ccd, cp_dir {
    illegal_bins wr_ccdr = binsof(cp_ccd.ccdr) && binsof(cp_dir.wr);
  }
  // 스택 높이를 함께 본다 — 4Hi 만 돌면 ccdr 은 영원히 빈다
  cp_stack : coverpoint stack_high { bins h4 = {4}; bins h8 = {8};
                                     bins h12 = {12}; bins h16 = {16}; }
  x_ccdr_stack : cross cp_ccd, cp_stack {
    bins ccdr_on_tall = binsof(cp_ccd.ccdr) && binsof(cp_stack) intersect {8,12,16};
    ignore_bins rest  = binsof(cp_ccd.ccdl) || binsof(cp_ccd.ccds);
  }

  // --- Power-down 진입 전제 (§6.3.4.1) — "완료" 네 갈래 ------------------
  cp_pd_precond : coverpoint precond {
    bins after_read        = {PD_AFTER_READ};          // postamble 까지 끝난 직후
    bins after_write       = {PD_AFTER_WRITE};         // tWR 기준
    bins after_write_ap    = {PD_AFTER_WRITE_AP};      // MR 의 WR 클럭 수 기준
    bins during_other      = {PD_DURING_ACT_OR_REF};   // 허용되지만 IDD 규격 미적용
  }
  cp_pd_type : coverpoint pdtype {
    bins precharge_pd = {PD_PRECHARGE};
    bins active_pd    = {PD_ACTIVE};
  }

  // --- 패리티 전환 구간 (§6.3.3.4) ---------------------------------------
  // MRS(disable) 이후 tMOD 만료 전에 커맨드를 발행해 봤는가
  cp_parity_window : coverpoint parity_window {
    bins outside = {0};
    bins inside  = {1};                   // 비대칭이 실제로 검증되는 지점
  }

  // --- Self refresh 중 주파수 변경 (§6.3.4.2) ---------------------------
  cp_sr_freq : coverpoint freq_changed_in_sr {
    bins no_change = {0};
    bins changed   = {1};                 // DVFS 경로 — 비면 통째로 미검증
  }
endgroup
```

세 bin이 특히 잘 빕니다.

- **`cp_ccd.ccdr`** — 4-High 프로파일만 돌면 영원히 0입니다. `x_ccdr_stack` 이 그 사실을 드러냅니다.
- **`cp_pd_precond.after_write_ap`** — auto-precharge write 직후 PD 진입은 의도적으로 만들어야 나옵니다.
- **`cp_sr_freq.changed`** — self refresh 중 주파수를 바꾸는 시퀀스가 없으면 DVFS 경로 전체가 미검증입니다. 그리고 그 경로에는 [04장](../04_mode_registers/)의 MR 재적재와 [05장](../05_clocking_dbi/)의 WDQS 분주기 리셋이 함께 걸려 있습니다.

### 8.4 어떻게 자극하는가

**① SID를 건너뛰는 seamless READ** — `tCCDR` 경로를 만드는 유일한 방법입니다.

```systemverilog
// 다른 뱅크 그룹 + 다른 SID 로 연속 READ. 8Hi 이상 구성에서만 의미가 있다.
class seq_ccdr_walk extends uvm_sequence #(hbm4_cmd_item);
  `uvm_object_utils(seq_ccdr_walk)
  virtual task body();
    if (cfg.sid_used_bits == 0) return;          // 4-High 에는 tCCDR 이 없다
    `uvm_do_with(req, { cmd == RD; sid == 0; bank[5:3] == 3'd0; })
    `uvm_do_with(req, { cmd == RD; sid == 1; bank[5:3] == 3'd1; })  // SID·그룹 둘 다 변경
  endtask
endclass
```

**② 패리티 전환의 양쪽 경계** — 비대칭이 실제로 검증되려면 **전환 구간 안에서 커맨드를 발행**해야 합니다.

```systemverilog
// (a) 켜기 — MRS(enable) 직후 첫 커맨드부터 패리티가 요구된다
`uvm_do_with(req, { cmd == MRS; mr == 0; op[6] == 1; })    // CAPAR enable
`uvm_do_with(req, { cmd == RNOP; parity_valid == 1; })     // 여기부터 필요

// (b) 끄기 — MRS(disable) 의 tMOD 만료 전까지는 여전히 필요하다
`uvm_do_with(req, { cmd == MRS; mr == 0; op[6] == 0; })    // CAPAR disable
`uvm_do_with(req, { cmd == RNOP; parity_valid == 1; })     // tMOD 전 — 아직 필요
// negative: 여기서 parity_valid == 0 을 발행하면 checker 가 잡아야 한다
```

**③ PD 진입을 네 전제 각각의 직후에** — 특히 **auto-precharge write 직후**를 빼먹지 않습니다. 그리고 MR의 `WR` 값을 `tWR`보다 크게 잡은 프로파일에서 돌려야 두 기준의 차이가 드러납니다.

**④ read 전용 테스트에서도 WDQS를 검사한다** — read agent만 돌리는 테스트에서 WDQS preamble 4펄스가 나오는지, 그리고 그 토글이 [05장](../05_clocking_dbi/)의 누적 카운터에 반영되는지 확인합니다. read만 도는 회귀가 짝수 불변식을 건너뛰면, WDQS 기여분이 통째로 빠집니다.

**⑤ self refresh 중 주파수 변경** — 이 장에서 가장 긴 시퀀스이고, 세 장이 함께 걸립니다.

```
SRE 진입 → tCKSRE 경과 → 클럭 주파수 변경 → tCKSRX 동안 안정 → SRX
  → 새 주파수 기준으로 MR 재적재 ([04장])
  → WDQS 분주기가 리셋되므로 토글 패리티 카운터도 리셋 ([05장])
  → RAA 가 tRAASRF 이상 유지되었다면 0 ([06장])
```

이 시퀀스가 없으면 세 항목이 **동시에** 미검증으로 남습니다. 그리고 각 장에서 따로 보면 놓치기 쉬운, **장을 가로지르는 시나리오**입니다.

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

**검증 결론**: 이 비대칭은 **전환 구간 안에 커맨드가 있어야만 드러난다.** `MRS(disable)` 직후 `tMOD` 만료 전에 `RNOP`을 발행해 보는 시퀀스가 없으면, 대칭으로 구현된 checker도 회귀를 통과한다.

**대조**: 활성화 방향은 반대다. `MRS(enable)` **자신**은 아직 패리티가 활성이 아니므로 검사되지 않는다.
</details>

### 문제 3 — Power-down 진입 판정

> 컨트롤러가 `WRA`(auto-precharge write)를 발행하고 `tWR` 시간이 경과했다. 이제 `PDE`를 발행해도 되는가?

<details>
<summary>풀이</summary>

**정보가 부족하다.** auto-precharge write의 완료 기준은 `tWR`이 **아니다.**

§6.3.4.1은 write 완료를 *"마지막 데이터 요소가 `tWR` 만족 상태로 메모리 배열에 기록 완료"* 로 정의하면서, **auto-precharge write의 경우 대신 mode register에 프로그램된 `WR` 클럭 수가 경과해야 한다**고 규정한다.

`MR3`의 `WR` 값은 `RU{tWR/tCK}` **이상**으로 프로그램되므로([04장](../04_mode_registers/)), **아날로그 `tWR`보다 길 수 있다.** 아날로그 `tWR`만 보고 진입하면 이르다.

**검증 결론**: "완료" 술어를 **한 함수에 모아** 두 PC AND로 판정한다(8.2 ③). 조건이 흩어지면 auto-precharge write 분기가 반드시 빠지고, 그 결함은 **MR의 `WR` 값을 `tWR`보다 크게 잡은 프로파일에서만** 드러난다.

**덧붙임**: 만약 refresh가 진행 중이라면 `PDE` 발행 자체는 **허용**된다. 다만 refresh가 끝날 때까지 power-down IDD 규격이 적용되지 않으므로 **전력 이득이 지연**될 뿐이다.
</details>

## 핵심 정리

- READ/WRITE 모두 **버스트 길이 8, column 주소 유일, 중단·절단 없음**. 발행 시점에 버스 점유가 확정된다.
- ⚠️ **읽기 데이터를 트리거하는 것은 WDQS다** — RDQS가 WDQS에서 생성되기 때문이다. 곧 **WDQS 구동은 read/write 어느 한쪽 agent의 소유가 아니다.** read 전용 테스트에서 WDQS가 멈춰 있으면 데이터가 안 나오고, 증상은 "DUT가 read에 응답하지 않는다"로 보인다.
- preamble/postamble은 **고정**이다 — READ의 WDQS **4+2**, RDQS **2+2**, WRITE의 WDQS **2+2**. **전부 짝수**이며 [05장](../05_clocking_dbi/)의 위상 보존 규칙과 일치한다 — 곧 **read 트랜잭션도 WDQS 토글 누적 카운터에 기여한다.**
- read 버스트의 **첫 데이터 비트는 RDQS의 세 번째 상승 에지**와 동기된다.
- **HBM4는 비정합 WDQS-DQ 경로**를 쓴다 → **주기적 트레이닝**으로 온도·전압 변동을 보상해야 한다. 일회성 캘리브레이션으로는 부족하다.
- **`tCCD`는 3택**이다 — 같은 그룹 `tCCDL` / 다른 그룹·같은 SID `tCCDS` / **다른 그룹·다른 SID `tCCDR`**. `tCCDR`은 **READ 전용**, **8·12·16-High 전용**, **벤더 지정·주파수 의존**이다. 2택 판정은 **놓친 버그**를, WRITE 적용은 **false FAIL**을 만든다. 4-High만 도는 회귀에서는 이 경로가 존재조차 확인되지 않는다.
- `MRS`는 **row 버스에 `RNOP`를 요구**하며, **모든 뱅크 idle** + `tRDMRS` + `tWRMRS`가 전제다. `tMOD`에서 **`RNOP`·`CNOP`는 제외**된다.
- 패리티 전이는 **비대칭**이다 — 켤 때는 다음 커맨드부터, 끌 때는 **`tMOD` 만료 후**부터. **전환 구간 안에 커맨드를 발행하지 않으면** 대칭으로 구현된 checker도 통과한다.
- `PDE` 금지 조건은 **양쪽 PC의 read/write 진행 중**이다. read 완료에는 **postamble**이, auto-precharge write 완료에는 **MR의 `WR` 클럭 수**가 포함된다.
- refresh 등이 진행 중이어도 `PDE` 발행은 **허용**되며, 전력 이득만 지연된다.
- `SRE`는 **두 PC의 모든 뱅크 precharge**를 요구하고, 진입 후 `tCPDED`까지 **`PDE`와 `CNOP`를 유지**해야 한다. **`R0` LOW 유지**가 self refresh 지속 조건이다.
- self refresh 중 **외부 클럭 정지·주파수 변경이 가능**하다 — DVFS의 실현 경로다. 이 시퀀스 하나가 **네 장을 가로지른다** — MR 재적재([04장](../04_mode_registers/)) · WDQS 분주기와 토글 패리티 리셋([05장](../05_clocking_dbi/)) · `tRAASRF` 기준 RAA 리셋([06장](../06_row_commands/)). 없으면 셋이 동시에 미검증으로 남는다.

## Further Reading

- **규격**: JESD270-4 §6.3.3 Column Commands (Figure 33–50) · §6.3.4 Power-Mode Commands (Figure 51–60) · §10 AC Timings (`tCCDR`)
- **다음 장**: [08 — Parity](../08_parity/) — CA parity와 데이터 패리티, `PL`
- **관련**: [04 — Mode Register](../04_mode_registers/) (`MR1` WL·PL, `MR2` RL, `MR3` WR) · [05 — 클럭킹](../05_clocking_dbi/) (짝수 규칙)
- **이해도 점검**: [퀴즈](../quiz/07_column_commands_quiz/)
