---
title: "04 — Mode Register"
description: JESD270-4 §5 · 20개 MR의 기능별 구조, 쓰기·읽기가 갈리는 RAL 구조, "기본값 없음"과 "unspecified operation"이 만드는 검증 부담
---

:::tip[🎯 Learning Objectives]
이 모듈을 마치면:

- **Organize** 20개 Mode Register를 기능 축으로 분류하고 각 축이 제어하는 하드웨어를 지목한다.
- **Calculate** 타이밍 MR 값을 `RU{t/tCK}` 규칙으로 산출한다.
- **Explain** MR이 두 PC에 공유되면서도 일부 필드가 PC별로 존재하는 구조를 설명한다.
- **Construct** 쓰기와 읽기가 서로 다른 인터페이스를 타는 MR을 RAL map 두 개로 모델링하고, `has_reset(0)`이 왜 필요한지 설명한다.
- **Derive** "썼다"가 아니라 "그 설정으로 트래픽이 돌았다"를 세는 coverage 축을 도출한다.
- **Evaluate** "기본값이 정의되지 않는다"와 "unspecified operation" 두 조문이 각각 검증 환경에 부과하는 책임을 판단하고, 후자가 왜 DUT 검증 항목이 될 수 없는지 설명한다.
:::

:::note[Prerequisites]
- [03 — 초기화·리셋·전원 시퀀스](../03_init_reset_power/) — MRS는 초기화의 마지막 단계다
- [01 — 규격 지형도](../01_landscape_organization/) — MR이 두 PC에 공유된다는 사실
:::

:::caution[인용 고지]
본 장은 **JESD270-4 (2025-04, WIP draft)** §5를 근거로 **요약·재구성**한 것입니다. Table 9~30의 배치를 그대로 옮기지 않고 **기능 축으로 재분류**했으며, 필드 값은 설명에 필요한 범위만 인용합니다. 정밀 정의는 **JEDEC 원문 우선**.
:::

---

## 1. 구조 — 무엇이 몇 개인가

§5의 골자는 다섯 줄로 요약됩니다.

- **8비트 폭 Mode Register 20개** (`MR0` ~ `MR19`), Table 10~30에 정의
- **`MR12`와 `MR17`은 벤더 전용 기능을 위해 예약**된 특수 레지스터
- **MR은 두 pseudo-channel(PC0/PC1)에 공통**이다
- MR 재프로그래밍은 **메모리 배열 내용을 바꾸지 않는다**
- MR은 **`MRS` 커맨드**로 프로그램되며, 재프로그램·칩 리셋·전원 상실 전까지 값을 유지한다

레지스터 선택은 `MA[4:0]`로 이뤄집니다 — `MR0`=`00000` 부터 `MR19`=`10011` 까지.

:::caution[기본값이 없다]
> Mode Register에 대해 **별도로 명시된 경우를 제외하면 기본 상태가 정의되지 않는다.** 따라서 사용자는 전원 인가 시 또는 후속 칩 리셋 이후 **모든 Mode Register를 원하는 값으로 완전히 초기화해야 한다.** — §5 (요약)

리셋 직후 MR 값은 **정의되지 않은 상태**입니다. "리셋했으니 기본값일 것"이라는 가정은 성립하지 않습니다.

`MR0`처럼 일부 필드에 (Default) 표기가 있는 경우가 있지만(TM=0, CAPAR=0, DRFM=0, TCSR=1 등), 그것은 **그 필드에 한정**됩니다. 초기화 펌웨어는 **20개 전부를 명시적으로 기록**해야 합니다 — [03장](../03_init_reset_power/)의 6단계 "모든 MRS 커맨드 발행"이 문자 그대로의 요구사항인 이유입니다.
:::

그리고 RFU 처리 규칙이 둘 있습니다.

- **레지스터 전체가 RFU**로 표시된 경우 → HBM4 DRAM이 **지원하지 않는 것**으로 간주하며 내용은 Don't Care
- **레지스터 내 RFU 비트**는 반드시 **0으로 프로그램**해야 한다

## 2. 기능 축으로 다시 묶기

Table 9는 레지스터 번호 순으로 나열하지만, 설계 관점에서는 **무엇을 제어하는가**로 묶는 편이 유용합니다.

### 축 ① — 기능 활성화 스위치 (`MR0`)

`MR0` 한 장에 여덟 개의 on/off가 모여 있습니다.

| 필드 | 비트 | 제어 대상 | 다루는 장 |
|---|---|---|---|
| `TM` (Test Mode) | OP[7] | 벤더 전용 테스트 모드. **활성 시 기능 동작이 규정되지 않음** | — |
| `CAPAR` | OP[6] | Command/Address parity | [08장](../08_parity/) |
| `WPAR` / `RPAR` | OP[5:4] | Write / Read data parity | [08장](../08_parity/) |
| `DRFM` | OP[3] | Directed Refresh Management | [06장](../06_row_commands/) |
| `TCSR` | OP[2] | 온도 보상 self refresh (**기본 Enabled**) | [07장](../07_column_commands/) |
| `WDBI` / `RDBI` | OP[1:0] | Write / Read Data Bus Inversion | [05장](../05_clocking_dbi/) |

`TM`에 붙은 단서가 인상적입니다 — **테스트 모드가 켜진 상태에서는 어떤 기능 동작도 규정되지 않습니다.** 즉 벤더 전용 통로이며, 정상 동작과 섞어 쓸 수 없습니다.

### 축 ② — 지연 파라미터 (`MR1` ~ `MR5`)

컨트롤러 타이밍의 핵심 값들이 다섯 장에 흩어져 있습니다.

| 레지스터 | 필드 | 범위 |
|---|---|---|
| `MR1` OP[7:5] | **`PL`** Parity Latency | 0 ~ 4 nCK |
| `MR1` OP[4:0] | **`WL`** Write Latency | 4 ~ 19 nCK |
| `MR2` OP[7:0] | **`RL`** Read Latency | **17 ~ 90 nCK** |
| `MR3` OP[7:0] | **`WR`** Write Recovery to Auto Precharge | 4 ~ 63 nCK |
| `MR4` OP[7:0] | **`RAS`** Activate to Precharge | 4 ~ 63 nCK |
| `MR5` OP[3:0] | **`RTP`** Read to Auto Precharge | 2 ~ 15 nCK |

`RL`의 범위가 **17~90 nCK**로 유난히 넓습니다. 이는 HBM4가 넓은 동작 주파수 범위를 지원하며, 고속 동작일수록 같은 절대 지연이 더 많은 클럭 사이클로 표현되기 때문입니다.

이 다섯 레지스터에 공통으로 붙는 규칙이 두 개 있고, 둘 다 설계에 직접 닿습니다.

:::tip[규칙 1 — 값은 선택적이지만 지원 범위는 연속이어야 한다]
> 모든 값은 **선택적**이나, 지원되는 **최소~최대 범위는 연속(contiguous)** 이어야 한다. — Table 11~15 각 Note 1 (요약)

장치는 정의된 전 범위를 지원할 의무가 없습니다. 예를 들어 `RL`을 30~50만 지원할 수 있습니다. 다만 그 안에 **구멍이 있어서는 안 됩니다** — 30~40과 45~50만 지원하는 식은 금지입니다.

**검증 함의**: 지원 범위가 `[min, max]` 연속 구간이므로, 랜덤 제약도 `inside {[min:max]}` 한 줄로 끝납니다. 그리고 **범위 밖 값은 `illegal_bins`** 로 두는 것이 맞습니다 — 자극이 만들면 안 되는 값이지 "아직 안 덮은 값"이 아닙니다.
:::

:::tip[규칙 2 — 아날로그 값을 클럭으로 올림한 값 이상]
> `WR`은 `RU{tWR/tCK}` 이상의 값으로 프로그램되어야 한다. `RU`는 **올림(round up)**, `tWR`은 **벤더 데이터시트의 아날로그 값**, `tCK`는 동작 클럭 주기다. HBM4 DRAM이 클럭 사이클 단위의 mode register 정의를 지원하지 않으면 **해당 MR 설정은 무시된다.** — Table 13 Note 2 (요약). `RAS`(Table 14)·`RTP`(Table 15)도 동일한 규칙.

세 가지가 따라옵니다.

1. MR 값은 **주파수 종속**입니다. 클럭을 바꾸면 같은 아날로그 타이밍이라도 MR 값이 달라집니다 → [05장](../05_clocking_dbi/)의 클럭 주파수 변경 시퀀스와 맞물립니다.
2. 기준이 되는 아날로그 값은 **규격이 아니라 벤더 데이터시트**에 있습니다.
3. 장치가 이 기능을 지원하지 않으면 **설정이 조용히 무시**됩니다 — 오류가 나지 않습니다. 컨트롤러는 자체 타이머로도 같은 제약을 지켜야 합니다.
:::

### 축 ③ — 드라이버와 듀티 사이클 (`MR6`, `MR10`, `MR11`)

| 레지스터 | 필드 | 내용 |
|---|---|---|
| `MR6` OP[7] | `DCM Flip` | Duty Cycle Monitor 플립 (기본 Disabled) |
| `MR6` OP[6] | `DCM` | Duty Cycle Monitor (기본 Disabled) |
| `MR6` OP[5:3] | Pullup Driver Strength | 25 / 20 / **16.7 (기본)** / 14.3 Ω |
| `MR6` OP[2:0] | Pulldown Driver Strength | 동일 |
| `MR10` | `DCA` code for **RDQS1(PC1)** / **RDQS0(PC0)** | 읽기 스트로브 듀티 조정 |
| `MR11` | `DCA` code for **WDQS1(PC1)** / **WDQS0(PC0)** | 쓰기 스트로브 듀티 조정 |

상세는 [11장](../11_training_ieee1500/)에서 다룹니다.

:::caution[공유 레지스터 안의 PC별 필드]
`MR10`과 `MR11`을 보면 **하나의 레지스터가 PC0용 필드와 PC1용 필드를 상하 절반씩 나눠 갖습니다.** `MR15`의 DFE 코드도 마찬가지입니다.

즉 **"MR은 두 PC에 공유된다"(§5)는 것은 레지스터 인스턴스가 하나라는 뜻이지, 설정 내용이 PC 무관이라는 뜻이 아닙니다.** 어떤 필드는 채널 전체에 적용되고(예: `MR0`의 parity enable), 어떤 필드는 특정 PC만 겨냥합니다(예: `MR11`의 WDQS0 DCA).

RTL에서 MR 파일을 **채널당 한 벌**로 두는 것은 맞지만, 그 출력을 소비하는 쪽에서는 **필드별로 어느 PC에 배선되는지**를 구분해야 합니다. 파일을 PC별로 복제하면 규격 위반이고, 출력을 구분 없이 양쪽에 배선하면 DCA 코드가 뒤바뀝니다.
:::

### 축 ④ — 테스트·루프백 (`MR7`)

`MR7`은 테스트 인프라 제어가 모인 곳입니다 — `CATTRIP`, **프로그래머블 RDQS Postamble(`tRPST`)**, **DWORD MISR Control**, **DWORD Read Mux**, **DWORD Loopback Control**. 루프백 구조는 [10장](../10_test_repair/)에서 다룹니다.

### 축 ⑤ — Refresh 관리와 복구 (`MR8`)

| 필드 | 내용 | 다루는 장 |
|---|---|---|
| `BRC` — DRFM Bounded Refresh Configuration | DRFM 동작 구성 | [06장](../06_row_commands/) |
| `RFML` — RFM Levels | Refresh Management 레벨 | [06장](../06_row_commands/) |
| `WDQS2CK` — WDQS-to-CK Training | 트레이닝 활성 | [05장](../05_clocking_dbi/) |
| `ECSLOG` — ECS error log auto reset | 오류 로그 자동 초기화 | [09장](../09_ecc_ecs_sev/) |
| `Rx Calibration Offset` | 수신 오프셋 보정 | [11장](../11_training_ieee1500/) |
| **`DA Port Lockout`** | Direct Access 테스트 포트 잠금 | [11장](../11_training_ieee1500/) |

`DA Port Lockout`이 MR에 있다는 점이 의미심장합니다 — **테스트 접근 경로를 기능 레지스터로 잠글 수 있다**는 뜻이고, 이는 보안·양산 관점의 요구사항입니다.

### 축 ⑥ — ECC와 심각도 (`MR9`)

`ECSRES`(오류 유형·주소 리셋), `ECSCEM`(다중 비트 오류 정정), `ECSSRF`(self refresh 중 자동 ECS), `ECSREF`(REFab 경유 자동 ECS), `ECCVEC`(오류 벡터 패턴), `ECCTM`(오류 벡터 입력 모드), **`SEVR`(Severity Reporting)**, `MD`(Meta Data). 전부 [09장](../09_ecc_ecs_sev/)에서 다룹니다.

### 축 ⑦ — 수신 기준전압과 등화 (`MR13` ~ `MR16`)

| 레지스터 | 내용 |
|---|---|
| `MR13` | **`VREFCA`** — AWORD 입력 기준 전압 |
| `MR14` | **`VREFD`** — DWORD 입력 기준 전압 |
| `MR15` | **DFE Code** (PC1 / PC0) |
| `MR16` | DFE용 예약 |

AWORD와 DWORD의 기준 전압이 **별도 레지스터**라는 점이 구조를 드러냅니다 — 커맨드/주소 경로와 데이터 경로가 독립적으로 튜닝됩니다.

### 축 ⑧ — 벤더 전용과 예약

`MR12`·`MR17`은 **벤더 전용 기능**, `MR18`·`MR19`는 RFU입니다. 그리고 규격은 **`MR16`~`MR19`가 벤더 선택 레지스터**임을 별도로 명시합니다(Table 9 Note 2).

벤더 선택 기능은 이 밖에도 있습니다 — **프로그래머블 RDQS(`MR7` OP6), Rx Calibration Offset(`MR8` OP1), RDQS DCA(`MR10`)** (Table 9 Note 1).

:::tip[열린 자리의 목록]
[01장](../01_landscape_organization/)에서 "규격이 열어둔 자리가 곧 차별화 지점"이라고 했습니다. MR 맵은 그 목록을 가장 압축적으로 보여줍니다 — **레지스터 두 장(`MR12`·`MR17`)이 통째로 벤더 몫**이고, 레지스터 네 장과 기능 세 개가 **선택 사항**입니다.

컨트롤러 설계 관점에서는 **이 영역에 의존하는 로직을 만들면 이식성을 잃는다**는 뜻입니다.
:::

## 3. 두 갈래 접근 경로

MR을 건드리는 방법은 둘입니다.

```d2
direction: right

CTRL: "메모리 컨트롤러" { style.fill: "#e3f2fd"; style.font-color: "#0A0F25" }
FW: "초기화 펌웨어 / 테스트 호스트" { style.fill: "#fff8e1"; style.font-color: "#0A0F25" }

MRS: "MRS 커맨드\ncolumn 커맨드 경로\n§6.3.3.4" { style.fill: "#e8f5e9"; style.font-color: "#0A0F25" }
IEEE: "MODE_REGISTER_DUMP_SET\nIEEE 1500 테스트 포트\n§13.5.13" { style.fill: "#f3e5f5"; style.font-color: "#0A0F25" }

MR: "Mode Register 파일\n20 × 8-bit · MA[4:0]\n채널당 1벌 (두 PC 공유)" { style.fill: "#bbdefb"; style.font-color: "#0A0F25" }

CTRL -> MRS: "쓰기만"
FW -> IEEE: "쓰기 + 읽기"
MRS -> MR
IEEE -> MR
```

**차이가 결정적입니다.**

| 경로 | 방향 | 전제 조건 | 근거 |
|---|---|---|---|
| `MRS` 커맨드 | **쓰기 전용** | 모든 뱅크 idle, 선행 READ로부터 `tRDMRS` 경과 | §5 |
| IEEE 1500 `MODE_REGISTER_DUMP_SET` | **쓰기 + 읽기** | `tINIT3` 이후 사용 가능 | §5, §13.5.13 |

즉 **MR을 되읽는 유일한 경로는 IEEE 1500 테스트 포트**입니다. 기능 경로(`MRS`)로는 쓸 수만 있고 확인할 수 없습니다.

:::caution[검증·디버그에 직결된다]
컨트롤러가 `MRS`로 설정을 썼는데 장치가 다른 값을 갖고 있다면, **기능 경로만으로는 그 사실을 알아낼 방법이 없습니다.** 설정이 반영됐는지 확인하려면 테스트 포트를 열어 되읽어야 합니다.

이것이 [`hbm_dv`](../../hbm_dv/08_testcase_scenarios/)에서 말한 *"레지스터에 썼다"와 "그 설정이 동작에 반영됐다"는 다른 이야기*의 하드웨어적 근거입니다. HBM4에서는 그 확인 경로가 **아예 다른 인터페이스**에 있습니다.
:::

## 4. 프로그래밍 제약

§5는 `MRS` 발행 조건을 명확히 규정합니다.

- **모든 뱅크가 idle**일 때 적재되어야 한다
- 선행 `READ` 커맨드로부터 **`tRDMRS`가 경과**해야 한다
- 이후 동작을 시작하기 전에 **`tMOD`, `tMRD`, `tRDMRS`, `tWRMRS`** 등 규정 시간을 기다려야 한다
- **이 중 하나라도 위반하면 동작이 규정되지 않는다(unspecified operation)**

"unspecified operation"이라는 표현에 주목할 필요가 있습니다 — 오류가 보고되는 것이 아니라 **무슨 일이 일어날지 규격이 보장하지 않는다**는 뜻입니다. 조용히 잘못 동작할 수 있습니다.

검증에서 이 한 단어의 무게가 큽니다. **정답이 존재하지 않으므로 scoreboard가 기대값을 만들 수 없습니다.** 그래서 이 조건은 "DUT가 잘 처리하는지 확인하는 항목"이 아니라 **"자극이 여기 들어가지 않게 막는 항목"** 이 됩니다 — 5.1절에서 자세히 다룹니다.

또한 [01장](../01_landscape_organization/)에서 확인했듯 `MRS`는 **두 PC에 공통인 커맨드**이므로, 발행 시점에 **양쪽 PC 모두**의 타이밍 조건이 충족되어야 합니다(§3.1.2).

## 🔬 검증 적용

### 5.1 무엇이 깨질 수 있는가

Mode Register는 **설정이지 데이터가 아닙니다.** 그래서 결함의 성격이 다릅니다 — 값이 틀렸다는 사실 자체가 아니라, **틀린 설정으로 동작한 그 이후 전부**가 증상으로 나타납니다.

| 조문 | 위반 형태 | 증상 | 잡히는 시점 |
|---|---|---|---|
| §5 **기본값 미정의** | 모델이 리셋 후 기본값을 가정 | 모델과 장치가 갈림. 20개 중 하나라도 안 쓰면 그 필드는 미정의 | **없음** |
| §5 RFU 비트는 **0으로** | 랜덤화가 RFU를 1로 채움 | unspecified | **없음** |
| §5 `MRS` 전제조건 (전 뱅크 idle · `tRDMRS`) | 조건 미충족 상태에서 발행 | **unspecified operation** — 오류 보고가 **없다** | **없음** |
| §5 `MRS`는 **쓰기 전용** | "썼으니 됐다"고 가정 | 반영 여부를 기능 경로로 확인 불가 | — |
| §3.1.2 MR **공유** | MR을 PC별로 모델링 | PC1이 PC0의 설정으로 동작 | MR을 바꾸는 시퀀스에서만 |
| `MR10`·`MR11` **PC별 필드** | 상·하위 절반을 교차 배선 | DCA 코드가 반대 PC로 감 | 트레이닝 실패 |
| §5 `tMOD`·`tMRD` 후 유효 | 모델이 **즉시** 반영 | 전환 구간에서 모델과 DUT가 다른 지연을 씀 | 간헐 미스매치 |
| Table 13~15 Note 2 `RU{t/tCK}` | 반올림/내림 혼동 | 한 사이클 부족 → 타이밍 위반 | 마진 없는 조건에서만 |
| MR 이미지의 **주파수 종속** | 클럭 변경 후 재적재 누락 | 이전 주파수 기준 지연으로 동작 | DVFS 시나리오에서만 |

세 번째 줄이 이 장에서 가장 다루기 까다롭습니다.

:::caution["unspecified operation"은 기대값을 만들 수 없다는 뜻이다]
§5는 `MRS` 전제조건 위반에 대해 **오류가 보고된다고 말하지 않습니다.** "동작이 규정되지 않는다(unspecified operation)"고 씁니다. 검증에서 이 표현의 의미는 무겁습니다.

- DUT가 **어떻게 반응하든 규격 위반이 아닙니다.** 무시할 수도, 잘못 쓸 수도, 배열을 건드릴 수도 있습니다.
- 따라서 **scoreboard가 기대값을 만들 수 없습니다.** 비교할 정답이 존재하지 않습니다.

그러므로 이 항목은 **DUT 검증 항목이 아니라 자극 측 제약**입니다. 처리 방식이 셋으로 갈립니다.

| 무엇을 | 어떻게 |
|---|---|
| 정상 회귀 | 자극이 **애초에 위반을 만들지 않도록** 제약 + 위반 시 즉시 `uvm_error` (환경 자기 검사) |
| 컨트롤러 DV | 컨트롤러가 **그런 `MRS`를 내보내지 않는지**가 검증 대상 — 여기서는 DUT 검증이 맞다 |
| 장치 모델 | 위반 입력에 대해 **모델이 무엇을 하는지 문서화**해 둔다. 그것이 규격은 아니라는 주석과 함께 |

V-Plan에 이 행을 넣을 때 "DUT가 위반을 거부하는지 확인"이라고 쓰면 틀립니다. 규격은 거부를 요구하지 않습니다.
:::

:::caution[MR을 되읽는 경로가 다른 인터페이스에 있다]
§5의 두 갈래 접근 경로가 검증 환경 구조를 직접 바꿉니다.

```
쓰기 : MRS 커맨드        → column 커맨드 경로  (기능 인터페이스)
읽기 : MODE_REGISTER_DUMP_SET → IEEE 1500 포트 (테스트 인터페이스)
```

일반적인 레지스터 검증은 **같은 인터페이스로 쓰고 읽어** 왕복을 확인합니다. 여기서는 그것이 **불가능**합니다. 쓰기와 읽기가 물리적으로 다른 포트에 있습니다.

귀결이 셋입니다.

1. **RAL 모델이 map 두 개를 든다** — write는 `MRS` map, read는 IEEE1500 map. 하나의 map으로 모델링하면 read가 어디로도 갈 수 없습니다.
2. **"썼다"의 확인은 비용이 든다** — IEEE1500 포트를 열어야 하므로, 매 `MRS`마다 되읽는 것은 현실적이지 않습니다. **언제 대조할지**가 검증 계획의 항목이 됩니다.
3. **초기화 중에는 되읽을 수도 없습니다** — IEEE1500 명령은 `tINIT3` 이후에만 쓸 수 있습니다([03장](../03_init_reset_power/)). 그 이전에 발행한 `MRS`는 나중에야 확인 가능합니다.
:::

### 5.2 어떻게 잡는가 — 수단 선택

| 규칙 | 성격 | 수단 | 이유 |
|---|---|---|---|
| MR 값 자체의 정합 | **레지스터 상태** | **RAL (map 2개)** | 표준 레지스터 검증 구조. 단 read/write map이 갈린다 |
| `MRS` 전제조건 (idle · `tRDMRS`) | **시간·상태 조건** | **SVA** | 발행 시점의 국소 판정 |
| RFU = 0 | **불변식** | **SVA + `illegal_bins`** | 자극 실수를 두 겹으로 잡는다 |
| `tMOD` 후 유효화 | **반영 시점** | **reference model의 지연 반영** | 언제 예측을 갱신할지의 문제 |
| PC별 필드 배선 | **매핑** | **RAL 필드 정의 + 되읽기 대조** | 교차 배선은 값 비교로만 드러난다 |

**① RAL — 쓰기와 읽기가 다른 map을 탄다**

```systemverilog
class hbm4_mr_reg extends uvm_reg;
  `uvm_object_utils(hbm4_mr_reg)
  rand uvm_reg_field f;                     // 8비트 (§5)

  function new(string name = "hbm4_mr_reg");
    super.new(name, 8, UVM_NO_COVERAGE);
  endfunction

  virtual function void build();
    f = uvm_reg_field::type_id::create("f");
    // 기본값이 정의되지 않는다 (§5) — reset value 를 등록하지 않는다.
    // has_reset = 0 으로 두면 reset() 후 mirror 가 "모름" 상태로 남고,
    // 초기화가 값을 쓰기 전에 predict 하려 하면 RAL 이 알려 준다.
    f.configure(.parent(this), .size(8), .lsb_pos(0), .access("RW"),
                .volatile(0), .reset(0), .has_reset(0),
                .is_rand(1), .individually_accessible(0));
  endfunction
endclass

class hbm4_mr_block extends uvm_reg_block;
  `uvm_object_utils(hbm4_mr_block)
  rand hbm4_mr_reg mr[20];                  // MR0 ~ MR19
  uvm_reg_map      mrs_map;                 // 쓰기 전용 — MRS 커맨드 경로 (§5)
  uvm_reg_map      w1500_map;               // 읽기 + 쓰기 — IEEE1500 (§13.5.13)

  virtual function void build();
    mrs_map   = create_map("mrs_map",   0, 1, UVM_LITTLE_ENDIAN);
    w1500_map = create_map("w1500_map", 0, 1, UVM_LITTLE_ENDIAN);
    foreach (mr[i]) begin
      mr[i] = hbm4_mr_reg::type_id::create($sformatf("mr%0d", i));
      mr[i].configure(this); mr[i].build();
      // 같은 레지스터가 두 map 에 다른 권한으로 등록된다
      mrs_map.add_reg  (mr[i], i, "WO");    // 기능 경로로는 되읽을 수 없다
      w1500_map.add_reg(mr[i], i, "RW");
    end
    lock_model();
  endfunction
endclass
```

`has_reset(0)` 이 이 모델의 핵심입니다. §5가 "기본 상태가 정의되지 않는다"고 했으므로, **리셋 후 mirror 값은 "0"이 아니라 "모름"** 이어야 합니다. `reset(0)`으로 등록해 두면 초기화가 MR을 쓰지 않고 지나가도 모델은 0을 자신 있게 예측하고, **장치와 갈린 채 회귀가 통과**합니다.

**② `MRS` 전제조건**

```systemverilog
// §5 — 전 뱅크 idle, 선행 READ 로부터 tRDMRS 경과. 위반 시 unspecified operation.
// 이 검사가 잡는 것은 "DUT 버그"가 아니라 "자극이 규격 밖으로 나갔다"는 사실이다.
property p_mrs_all_banks_idle;
  @(posedge ck) disable iff (!rst_n)
    mrs_vld |-> (bank_active_mask == '0);
endproperty
a_mrs_idle: assert property (p_mrs_all_banks_idle)
  else `uvm_error("MRS_PRECOND",
       $sformatf("뱅크가 열린 채 MRS 발행 (active=%0h). §5 — unspecified operation",
                 bank_active_mask))

a_mrs_trdmrs: assert property (@(posedge ck) disable iff (!rst_n)
    mrs_vld |-> (cycles_since_last_rd >= T_RDMRS))
  else `uvm_error("MRS_PRECOND", "선행 READ 로부터 tRDMRS 미경과 (§5)")

// RFU 비트는 0 으로 프로그램되어야 한다 (§5)
a_mr_rfu_zero: assert property (@(posedge ck) disable iff (!rst_n)
    mrs_vld |-> ((mrs_data & RFU_MASK[mrs_addr]) == '0))
  else `uvm_error("MRS_RFU", "RFU 비트가 1 로 프로그램되었다 (§5)")

// 전제조건 경계에 실제로 붙어 봤는가 — 안 그러면 위 검사는 여유 구간만 본 것이다
c_mrs_at_trdmrs_boundary: cover property (@(posedge ck)
    mrs_vld && (cycles_since_last_rd == T_RDMRS));
```

**③ `tMOD` — 예측을 언제 갱신하는가**

`MRS` 발행 시점과 그 설정이 유효해지는 시점이 다릅니다. 모델이 즉시 갱신하면 **전환 구간에서 DUT와 다른 지연을 기대**합니다.

```systemverilog
// MRS 를 관측하면 값은 받아 두되, tMOD 만료 시점에 유효화한다 (§5).
task automatic on_mrs(int idx, bit [7:0] val);
  m_mr_pending[idx] = val;
  fork
    begin
      repeat (T_MOD) @(posedge ck);
      m_mr[idx] = m_mr_pending[idx];
      recompute_timing_constants();       // RL·WL·WR·RAS·RTP 재산출
    end
  join_none
endtask
```

전환 구간(`MRS` ~ `tMOD` 만료) 동안 **어느 값을 기대할지**가 애매합니다. 규격은 그 구간에 커맨드를 발행하지 말라고 하므로, 가장 안전한 처리는 **그 구간의 커맨드 발행 자체를 assertion으로 금지**하고 모델은 전환을 원자적으로 다루는 것입니다.

### 5.3 무엇을 덮었다고 말할 수 있는가

MR coverage에서 흔한 실수는 **필드 값을 세는 것**입니다. 8비트 × 20개를 다 채우는 것은 불가능하고 의미도 없습니다. 세야 할 것은 **어떤 설정 조합으로 실제 트래픽이 돌았는가**입니다.

```systemverilog
covergroup cg_hbm4_mr with function sample(
    int mr_idx, bit [7:0] val, mr_path_e path, bit readback_ok, mr_ctx_e ctx);
  option.per_instance = 1;

  // --- 초기화가 20개를 전부 썼는가 (§5 기본값 미정의) --------------------
  cp_mr_written : coverpoint mr_idx {
    bins mr[] = {[0:19]};
    // MR12·MR17 은 벤더 전용이지만 "쓰지 않아도 된다"는 뜻은 아니다
  }

  // --- 접근 경로 (§5 두 갈래) -------------------------------------------
  cp_path : coverpoint path {
    bins mrs_write = {MR_PATH_MRS};          // 기능 경로 — 쓰기만
    bins w1500_wr  = {MR_PATH_1500_WRITE};
    bins w1500_rd  = {MR_PATH_1500_READ};    // 되읽기 — 이 bin 이 비면 대조를 안 한 것
  }

  // --- 설정이 동작에 반영되었는가 ----------------------------------------
  // "썼다" 가 아니라 "그 설정으로 트래픽이 돌았다" 를 센다
  cp_ctx : coverpoint ctx {
    bins init_only   = {MR_CTX_INIT};        // 초기화 때 쓰고 끝
    bins traffic_ran = {MR_CTX_TRAFFIC};     // 그 설정으로 read/write 를 수행
    bins reprogram   = {MR_CTX_REPROGRAM};   // 런타임 재프로그램 (DVFS 등)
  }
  x_mr_ctx : cross cp_mr_written, cp_ctx;

  // --- 기능 스위치 조합 (MR0) --------------------------------------------
  cp_capar : coverpoint val[6] iff (mr_idx == 0) { bins off = {0}; bins on = {1}; }
  cp_wdbi  : coverpoint val[1] iff (mr_idx == 0) { bins off = {0}; bins on = {1}; }
  cp_rdbi  : coverpoint val[0] iff (mr_idx == 0) { bins off = {0}; bins on = {1}; }
  // parity × DBI 조합은 데이터 패리티 대상 집합을 바꾼다 ([08장](../08_parity/))
  x_switches : cross cp_capar, cp_wdbi, cp_rdbi;

  // --- 타이밍 필드는 값이 아니라 경계를 센다 -----------------------------
  cp_timing_edge : coverpoint val iff (mr_idx inside {1,2,3,4,5}) {
    bins at_min = {MR_TIMING_MIN};
    bins mid    = {[MR_TIMING_MIN+1 : MR_TIMING_MAX-1]};
    bins at_max = {MR_TIMING_MAX};
    illegal_bins out_of_range = default;     // 지원 범위 밖은 나오면 안 된다
  }

  // --- 되읽기 대조 --------------------------------------------------------
  cp_readback : coverpoint readback_ok { bins matched = {1}; }
endgroup
```

세 가지가 요점입니다.

- **`x_mr_ctx` 가 이 장의 중심 축입니다.** `cp_mr_written` 만 채우면 "초기화가 20개를 다 썼다"까지만 증명됩니다. `traffic_ran` 과 cross해야 **그 설정으로 실제 동작했다**가 증명됩니다.
- **`cp_path.w1500_rd` 가 비어 있으면** MR 값을 한 번도 대조하지 않은 것입니다. 쓰기만 하고 확인하지 않은 회귀는 MR 경로 결함을 통과시킵니다.
- **타이밍 필드는 `at_min`·`at_max` 만 의미가 있습니다.** 중간값은 결함을 드러내지 않습니다.

### 5.4 어떻게 자극하는가

**① 초기화 MR 이미지를 랜덤화한다** — 고정 이미지 하나만 쓰는 것이 가장 흔한 구멍입니다. 20개 전부를 쓰되 값은 합법 범위에서 흔듭니다.

```systemverilog
class mr_image_cfg extends uvm_object;
  `uvm_object_utils(mr_image_cfg)
  rand bit [7:0] mr[20];
  rand int unsigned t_ck_ps;                 // 동작 주파수 — MR 이미지가 여기 종속된다

  // RFU 비트는 반드시 0 (§5)
  constraint c_rfu { foreach (mr[i]) (mr[i] & RFU_MASK[i]) == 0; }

  // 타이밍 MR 은 RU{t/tCK} 로 산출한 값 이상이어야 한다 (Table 13~15 Note 2)
  constraint c_timing {
    mr[3] >= (T_WR_PS  + t_ck_ps - 1) / t_ck_ps;      // WR
    mr[4] >= (T_RAS_PS + t_ck_ps - 1) / t_ck_ps;      // RAS
    mr[5] >= (T_RTP_PS + t_ck_ps - 1) / t_ck_ps;      // RTP
  }
  // 경계값에 붙는 빈도를 올린다 — 중간값은 결함을 드러내지 않는다
  constraint c_edge_bias {
    mr[2] dist { RL_MIN := 3, [RL_MIN+1 : RL_MAX-1] := 1, RL_MAX := 3 };
  }
endclass
```

`c_timing` 이 **`t_ck_ps` 에 종속**된 것이 핵심입니다. 주파수를 랜덤화하면서 MR 값을 고정하면 `RU{t/tCK}` 규칙을 위반하는 이미지가 생깁니다 — 자극이 스스로 규격을 벗어나는 경우입니다.

**② 되읽기 대조 지점을 정한다** — 매 `MRS`마다 IEEE1500으로 확인하는 것은 비현실적이므로, 대조 시점을 정책으로 정합니다.

- 초기화 완료 직후 **1회 전량 대조** (`tINIT3` 이후여야 가능 — [03장](../03_init_reset_power/))
- 런타임 재프로그램 **직후 해당 MR만**
- 테스트 종료 시 **1회 전량 대조** — 도중에 예상치 못한 변경이 없었는지

```systemverilog
task automatic mr_dump_and_compare();
  uvm_status_e st; uvm_reg_data_t v;
  foreach (mr_blk.mr[i]) begin
    // 되읽기는 IEEE1500 map 으로만 가능하다 (§5, §13.5.13)
    mr_blk.mr[i].read(st, v, .path(UVM_FRONTDOOR), .map(mr_blk.w1500_map));
    if (v !== mr_blk.mr[i].get())
      `uvm_error("MR_MISMATCH", $sformatf("MR%0d 기대 %0h, 실제 %0h", i,
                                          mr_blk.mr[i].get(), v))
  end
endtask
```

**③ 런타임 재프로그램 — 주파수 전환 시나리오** — MR 이미지가 주파수 종속이므로, 클럭을 바꾸는 시스템은 전환마다 재적재해야 합니다. 이 시퀀스가 없으면 `cp_ctx.reprogram` 이 영원히 빕니다.

**④ `tMOD` 경계** — `MRS` 직후 `tMOD` 만료 **정확히 그 시점**에 커맨드를 발행하는 directed 시퀀스를 둡니다. 항상 여유 있게 기다리는 자극만 돌면, 반영 시점 처리의 오차가 드러나지 않습니다.

**⑤ 전제조건 위반은 격리된 negative 테스트로** — 뱅크를 열어 둔 채 `MRS`를 발행하는 시퀀스입니다. 다만 5.1에서 본 대로 **기대값이 존재하지 않으므로**, 이 테스트로 확인할 수 있는 것은 "환경의 checker가 위반을 잡는가"뿐입니다. DUT의 반응을 정답과 비교하려 들면 안 됩니다.

## 6. 대표 문제 — dry-run

### 문제 1 — 타이밍 MR 값 산출

> 벤더 데이터시트가 `tRAS = 32 ns`, 동작 클럭이 `tCK = 0.4 ns`일 때 `MR4`(RAS)에 넣을 값은? 그 값이 유효한가?

<details>
<summary>풀이</summary>

```
RU{tRAS / tCK} = RU{32 / 0.4} = RU{80} = 80 nCK
```

**그런데 `MR4`의 범위는 4~63 nCK다** (Table 14). 80은 표현할 수 없다.

이것이 의미하는 바는 둘 중 하나다.
- 이 주파수·타이밍 조합이 해당 장치의 지원 범위를 벗어난다, 또는
- 장치가 **클럭 사이클 단위 MR 정의를 지원하지 않는** 경우에 해당해 설정이 무시된다(Note 2).

**검증 결론**: 자극의 MR 이미지 생성 제약에 **범위 검사가 반드시 들어가야 한다.** 산출값을 필드 폭으로 무비판적으로 잘라 넣으면(80 → 하위 6비트 = 16) 자극이 스스로 심각한 타이밍 위반을 만들고, 그 결과는 DUT 버그처럼 보인다. `mr_image_cfg` 의 `c_timing` 제약이 이 계산을 그대로 담는 이유다(5.4 ①).
</details>

### 문제 2 — 공유 MR과 PC별 필드

> 컨트롤러가 PC0의 WDQS 듀티만 조정하려 한다. `MR11`에 어떻게 써야 하는가?

<details>
<summary>풀이</summary>

`MR11`은 **하위 절반이 WDQS0(PC0), 상위 절반이 WDQS1(PC1)** 의 DCA 코드다. 레지스터는 하나이므로 **8비트를 통째로 쓰는 `MRS` 한 번**으로 갱신된다.

따라서 PC0만 바꾸려면 **PC1의 현재 값을 보존한 채 병합**해야 한다.

```
새 MR11 = {기존 PC1 코드, 새 PC0 코드}
```

**문제**: 기능 경로(`MRS`)로는 MR을 **되읽을 수 없다**(§5). 따라서 기존 PC1 값을 알려면 ⓐ 컨트롤러가 자신이 쓴 값을 **섀도 카피**로 보관하고 있거나, ⓑ IEEE 1500 `MODE_REGISTER_DUMP_SET`으로 읽어와야 한다.

**검증 결론**: RAL 모델이 **필드 단위로 쪼개져 있어야** 한다. 레지스터를 8비트 통짜로 두면 부분 필드 갱신을 예측할 수 없고, 되읽기 대조에서 어느 필드가 틀렸는지도 알 수 없다. 그리고 기능 경로로는 되읽을 수 없으므로(§5) **모델의 섀도가 유일한 기준값**이다 — 그 모델이 틀리면 대조할 것이 없다.
</details>

### 문제 3 — 리셋 직후 상태

> 기능 리셋 후 컨트롤러가 `MR0`의 `TCSR`이 기본값 Enabled라고 가정하고 self refresh를 사용했다. 문제가 있는가?

<details>
<summary>풀이</summary>

**있다.** `MR0`의 `TCSR` 필드 설명에 "1 – Enabled (Default)"가 붙어 있는 것은 사실이지만, §5는 **"별도로 명시된 경우를 제외하면 Mode Register에 기본 상태가 정의되지 않으며, 전원 인가 또는 칩 리셋 후 모든 MR을 완전히 초기화해야 한다"** 고 규정한다.

즉 필드 수준의 (Default) 표기는 **그 값이 권장/기본 설정이라는 의미**이지, **리셋 후 하드웨어가 그 값을 갖는다는 보장이 아니다.** 안전한 해석은 "리셋 후 MR 내용은 미정의"이며, [03장](../03_init_reset_power/) 6단계에서 **모든 MRS를 발행**하는 것이 규격이 요구하는 절차다.

**검증 결론**: 초기화 시퀀스가 20개 MR 전부를 기록하는지가 **검사 대상**이다. `cp_mr_written` 의 bin 20개가 다 차지 않으면 그 자체가 결함이며, RAL 쪽은 `has_reset(0)` 으로 "모름" 상태를 유지해 **쓰지 않은 MR을 예측하려 들면 알려 주도록** 만든다(5.2 ①).
</details>

## 핵심 정리

- **8비트 MR 20개(`MR0`~`MR19`)**, `MA[4:0]`로 선택. **`MR12`·`MR17`은 벤더 전용**, `MR16`~`MR19`는 **벤더 선택**.
- **MR은 두 PC에 공유**된다 — 레지스터 인스턴스는 채널당 하나다. 다만 **`MR10`·`MR11`·`MR15`는 하나의 레지스터 안에 PC별 필드**를 갖는다.
- **기본값이 정의되지 않는다.** 리셋 후 20개 전부를 명시적으로 초기화해야 한다. RAL은 **`has_reset(0)`** 으로 두어 mirror가 "0"이 아니라 **"모름"** 이 되게 한다 — `reset(0)`으로 등록하면 초기화가 빼먹은 MR을 모델이 자신 있게 0으로 예측하고 회귀가 통과한다.
- 지연 파라미터 범위: `PL` 0–4, `WL` 4–19, **`RL` 17–90**, `WR`·`RAS` 4–63, `RTP` 2–15 nCK.
- 값은 선택적이나 **지원 범위는 연속**이어야 한다 → `[min, max]` 두 값으로 관리 가능.
- 타이밍 MR은 **`RU{t/tCK}` 이상**으로 프로그램한다. **주파수 종속**이며, 기준 아날로그 값은 **벤더 데이터시트**에 있다. 장치가 미지원이면 **조용히 무시**되므로 컨트롤러 자체 타이머가 필요하다.
- **MR을 되읽는 경로는 IEEE 1500 `MODE_REGISTER_DUMP_SET` 뿐**이다. `MRS`는 쓰기 전용 — RAL이 **map 두 개**(쓰기=MRS, 읽기=IEEE1500)를 들어야 하고, 초기화 중에는 `tINIT3` 전이라 **되읽기 자체가 불가능**하다.
- 부분 필드 갱신 때문에 **RAL은 필드 단위로 쪼개져 있어야** 한다. 기능 경로로 되읽을 수 없으므로 **모델의 섀도가 유일한 기준값**이다.
- `MRS`는 **모든 뱅크 idle** + `tRDMRS` 경과가 전제이며, 위반 시 **unspecified operation**(오류 보고 없음). 정답이 없으므로 **scoreboard가 기대값을 만들 수 없다** — 이 항목은 DUT 검증이 아니라 **자극 측 제약**이다.
- 설정 반영은 `tMOD` 후다. 모델이 **즉시** 갱신하면 전환 구간에서 DUT와 다른 지연을 기대한다.
- coverage는 "MR을 썼다"가 아니라 **"그 설정으로 트래픽이 돌았다"**(`x_mr_ctx`)를 센다. 타이밍 필드는 **`at_min`·`at_max`** 만 의미가 있다.
- **`DA Port Lockout`이 MR에 있다** — 테스트 접근을 기능 레지스터로 잠근다.

## Further Reading

- **규격**: JESD270-4 §5 Mode Registers (Table 9 개요, Table 10~30 개별 MR)
- **다음 장**: [05 — 클럭킹과 DBIac](../05_clocking_dbi/) — `MR0`의 DBI 비트가 제어하는 대상
- **관련**: [08 — Parity](../08_parity/) (`MR0` CAPAR/WPAR/RPAR, `MR1` PL) · [09 — ECC](../09_ecc_ecs_sev/) (`MR9`) · [11 — 트레이닝](../11_training_ieee1500/) (`MR6`·`MR10`·`MR11`)
- **이해도 점검**: [퀴즈](../quiz/04_mode_registers_quiz/)
