---
title: "02 — 주소 체계와 뱅크 그룹"
description: JESD270-4 §3.2–3.3 · 주소 매핑 reference model, 무효 조합 검사, 뱅크 그룹 의존 타이밍 coverage
---

:::tip[🎯 Learning Objectives]
이 모듈을 마치면:

- **Interpret** Table 4의 주소 필드 구성과 주석에서 **주소 결함의 실패 모드**를 도출한다.
- **Calculate** 페이지 크기·채널 밀도·뱅크 수를 규격의 관계식으로 검산한다.
- **Explain** SID가 별도 층 선택 신호가 아니라 **뱅크 주소 확장 비트**로 동작하는 이유를 설명한다.
- **Construct** 주소 매핑 reference model에 **왕복 검사**를, 무효 조합에 인터페이스 assertion을 구현한다.
- **Derive** 뱅크 그룹·SID·page hit/miss에서 coverage 축을 도출하고, 왜 주소 값이 아니라 **선택된 타이밍**을 세야 하는지 설명한다.
- **Analyze** 간이 상태도의 **생략 목록**을 V-Plan 항목으로 옮기고, 각각이 어느 장에서 자극되는지 대응시킨다.
:::

:::note[Prerequisites]
- [01 — 규격 지형도와 조직 구조](../01_landscape_organization/) — 채널·PC·SID의 위치
- DRAM 뱅크·행·열 개념 — [DRAM / DDR](../../dram_ddr/)
:::

:::caution[인용 고지]
본 장은 **JESD270-4 (2025-04, WIP draft)** §3.2–§3.3을 근거로 **요약·재구성**한 것입니다. 표·그림은 옮기지 않고 번호로 지시합니다. 정밀 수치는 **JEDEC 원문 우선**.
:::

---

## 1. 주소 필드 — 무엇으로 무엇을 고르는가

§3.2 Table 4는 밀도·스택 높이 조합별 주소 구성을 정의합니다. 조합은 다르지만 **필드 구조는 하나**입니다.

| 필드 | 폭 | 역할 | 제약 (Table 4 주석) |
|---|---|---|---|
| `RA[13:0]` | 14 | Row Address | **`RA[13:12] = 11` 무효** |
| `CA[4:0]` | 5 | Column Address | BL8의 8 UI를 구분하지 **않음** |
| `BA[3:0]` | 4 | Bank Address | — |
| `SID[1:0]` | 0–2 | Stack ID | **`SID[1:0] = 11` 무효**, 4Hi에서 **`SID[0]=1` 무효** |

`SID`의 폭이 구성에 따라 달라지는 것이 핵심입니다 — 4-high는 SID 없음, 8-high는 `SID[0]`, 12/16-high는 `SID[1:0]`. 스택이 높아질수록 **주소 비트가 늘어나는** 구조입니다.

### SID는 층 선택 신호가 아니다

가장 흔한 오해입니다. SID는 "몇 번째 die인가"를 고르는 별도 제어 신호처럼 보이지만, 규격은 다르게 말합니다.

> `SID`, `SID0`, `SID1`은 **커맨드 실행에서 뱅크 주소 비트로 동작**한다. 특정 AC 타이밍 파라미터 또는 선택된 타이밍 파라미터의 변형이 **SID에 연동될 수 있다.** — Table 4 Note 4 (요약)

두 가지가 따라옵니다.

1. **뱅크 인덱스는 `{SID, BA[3:0]}` 의 연접**이다. 그래서 채널당 뱅크 수가 16 → 32 → 48 → 64로 늘어난다.
2. **타이밍이 SID에 따라 달라질 수 있다.** 물리적으로 다른 die에 있는 뱅크이므로 일부 파라미터가 변형될 수 있습니다. 곧 **타이밍 checker가 SID를 무시하면 안 되고**, coverage도 SID로 갈라야 한다는 뜻입니다 — 고 SID에서만 나는 위반은 낮은 SID만 자극하는 회귀에서 절대 안 보입니다.

[01장](../01_landscape_organization/)에서 확인한 "4-high를 넘는 die는 채널이 아니라 용량·SID·뱅크를 늘린다"는 조문이 여기서 구체화됩니다.

### 버스트 순서는 고정이고, 주소로 지정되지 않는다

Table 4 Note 2가 검증에 직접 닿는 조문입니다.

> Read와 Write의 **버스트 순서는 고정**이며, HBM 장치는 BL8 버스트의 **여덟 UI를 구분하는 column 주소 비트를 배정하지 않는다.** 메모리 컨트롤러가 내부적으로 그런 column 주소 비트를 둘 수는 있으나 **그 비트들은 HBM 장치로 전송되지 않는다.** — Note 2 (요약)

즉 컨트롤러가 바이트 단위 주소를 다루더라도, **장치로 나가는 `CA[4:0]`에는 버스트 내 위치 정보가 실리지 않습니다.** 하위 비트는 컨트롤러 내부에서 소비되고 절단됩니다.

이것을 모르고 `CA`에 하위 비트를 실으면 엉뚱한 열을 접근하는데, **증상은 데이터 미스매치로 나타납니다.** scoreboard는 "값이 다르다"고만 말하지 "주소가 틀렸다"고 말해 주지 않습니다. 주소를 데이터와 **분리해서 먼저** 검사해야 하는 이유입니다 — 6.2절.

## 2. 페이지 크기 — 관계식으로 검산하기

Note 3이 관계식을 줍니다.

```
Page Size = 2^COLBITS × (Prefetch Size / 8)
```

HBM4에 대입하면 — `COLBITS = 5`(CA[4:0]), `Prefetch = 256 bit`:

```
2^5 × (256 / 8) = 32 × 32 = 1024 byte = 1 KB   ✅ (§2의 "PC당 1 KB page"와 일치)
```

그리고 같은 주석에 설계자가 놓치기 쉬운 한 줄이 붙습니다.

> **RA의 MSB가 열린 2 KB 페이지의 절반을 선택**하는 데 사용된다. — Note 3 (요약)

물리적으로 열리는 행은 **2 KB**이고, PC가 보는 논리적 페이지는 그중 **1 KB 절반**이라는 뜻입니다. `RA[13]`이 그 절반을 고릅니다. 행 버퍼 관리 로직이 이 층위 차이를 반영하지 않으면, "같은 행인데 왜 activate가 또 필요한가" 같은 오해가 생깁니다.

:::note[Note 1도 함께]
prefetch 크기와 page 크기는 **선택적 ECC 비트를 포함하지 않습니다**(Note 1). 데이터 경로 폭을 계산할 때 ECC 핀(§3.1.1의 채널당 4개)을 따로 더해야 합니다.
:::

## 3. 밀도 구성 — 산술이 맞아떨어지는가

Table 4는 24 Gb·32 Gb die를 4/8/12/16-high로 조합한 8가지 구성을 나열합니다. 규격을 외우는 대신 **관계로 검산**하는 편이 실수를 막습니다.

```
스택 총 용량 = 채널당 밀도 × 32채널
             = die 밀도 × 스택 높이
```

| 구성 | 채널당 밀도 | 검산 (×32채널) | die 기준 검산 | 총 용량 |
|---|---|---|---|---|
| 24 Gb 4H | 3 Gb | 96 Gb | 24 × 4 = 96 Gb | 12 GB |
| 24 Gb 8H | 6 Gb | 192 Gb | 24 × 8 = 192 Gb | 24 GB |
| 24 Gb 12H | 9 Gb | 288 Gb | 24 × 12 = 288 Gb | 36 GB |
| 24 Gb 16H | 12 Gb | 384 Gb | 24 × 16 = 384 Gb | 48 GB |
| 32 Gb 4H | 4 Gb | 128 Gb | 32 × 4 = 128 Gb | 16 GB |
| 32 Gb 8H | 8 Gb | 256 Gb | 32 × 8 = 256 Gb | 32 GB |
| 32 Gb 12H | 12 Gb | 384 Gb | 32 × 12 = 384 Gb | 48 GB |
| 32 Gb 16H | 16 Gb | 512 Gb | 32 × 16 = 512 Gb | **64 GB** |

두 검산이 모든 행에서 일치합니다 **[추론 — Table 4 수치로부터 계산]**. 최대 구성 **32 Gb × 16-high = 64 GB**는 JEDEC 발표 수치와도 맞습니다.

:::tip[밀도 코드]
각 구성에는 **밀도 코드**가 배정되며, 이 값은 `DEVICE_ID` Wrapper Data Register의 비트 [43:40]에 인코딩됩니다(Table 4 Note 7, Table 134). 즉 호스트는 **IEEE 1500 테스트 포트로 장치 구성을 읽어올 수 있습니다** → [11장](../11_training_ieee1500/).

컨트롤러가 구성을 하드코딩하지 않고 **부팅 시 읽어서 결정**할 수 있다는 뜻이고, 이것이 하나의 RTL로 여러 구성을 지원하는 근거가 됩니다.
:::

## 4. 뱅크 그룹 — 왜 타이밍이 둘로 갈리는가

### 구성

§3.2.1에 따르면 뱅크는 **2 / 4 / 6 / 8개의 뱅크 그룹**으로 나뉘며, Table 5가 배정을 정의합니다. 규칙은 단순합니다 — **연속한 8개 뱅크가 한 그룹**입니다.

| 뱅크 수 | 그룹 수 | 배정 |
|---|---|---|
| 16 | 2 | A(0–7), B(8–15) |
| 32 | 4 | A~D |
| 48 | 6 | A~F |
| 64 | 8 | A~H |

뱅크 인덱스가 `{SID, BA[3:0]}`이고 그룹이 8뱅크 단위이므로, **그룹 인덱스는 그 연접의 상위 비트** — 즉 `{SID, BA[3]}` 로 정해집니다 **[추론 — Table 5 배정으로부터 도출]**.

### 그룹이 타이밍을 가른다

Table 6이 이 장에서 가장 실무적인 표입니다. **같은 그룹 내 접근과 다른 그룹 간 접근에 서로 다른 타이밍 파라미터가 적용**됩니다.

| 커맨드 시퀀스 | 다른 뱅크 그룹 | 같은 뱅크 그룹 |
|---|---|---|
| ACTIVATE → ACTIVATE | `tRRDS` | `tRRDL` |
| WRITE → WRITE | `tCCDS` | `tCCDL` |
| READ → READ | `tCCDS` 또는 `tCCDR` | `tCCDL` |
| Internal WRITE → READ | `tWTRS` | `tWTRL` |
| READ → PRECHARGE | — | `tRTP` |

접미사 규칙이 보입니다 — **S = Short(다른 그룹), L = Long(같은 그룹)**. 같은 그룹 접근이 더 오래 걸립니다.

**왜 그런가**: 뱅크 그룹은 내부 배열 자원(센스앰프 구동·프리페치 경로 등)을 공유하는 단위입니다. 같은 그룹 안에서 연속 접근하면 그 자원이 회복될 때까지 기다려야 하지만, 다른 그룹은 자원이 분리되어 있어 더 빨리 다음 커맨드를 받을 수 있습니다. 즉 **뱅크 그룹은 "자원 공유 경계"를 주소 공간에 노출한 것**입니다.

READ→READ에만 세 번째 값 `tCCDR`이 있는 것도 이 관점에서 읽힙니다 — 읽기 경로에는 그룹 구분과 다른 축의 제약이 하나 더 있다는 뜻이고, 상세는 [07장](../07_column_commands/)에서 다룹니다.

:::caution[검증에서는 "확률"이 문제가 된다]
뱅크 그룹은 단순한 주소 구획이 아니라 **스케줄러의 동작을 가르는 변수**입니다. 그룹을 번갈아 발행하면 `tCCDS`(짧은 쪽), 몰아 보내면 `tCCDL`(긴 쪽)에 묶입니다.

검증에서 이것이 만드는 문제는 **확률**입니다. 64뱅크 구성에서 무작위로 두 뱅크를 고르면 같은 그룹일 확률은 약 **1/8**입니다. 순수 랜덤 자극만 도는 환경은 `tCCDS`·`tRRDS` 쪽에 히트가 몰리고, **긴 쪽 경로는 훨씬 덜 검증됩니다.** 그룹 관계를 자극의 명시적 축으로 올려야 합니다 — 6.4절.
:::

## 5. 간이 상태 천이도 — 그리고 그것이 감춘 것

§3.3 Figure 3은 허용된 상태 천이와 그것을 제어하는 커맨드를 간략히 보여줍니다.

```d2
direction: right

PowerOn: "Power On" { style.fill: "#eceff1"; style.font-color: "#0A0F25" }
Reset: "Reset" { style.fill: "#eceff1"; style.font-color: "#0A0F25" }
Config: "Configure Device\n(MRS)" { style.fill: "#fff8e1"; style.font-color: "#0A0F25" }
Idle: "Bank Idle" { style.fill: "#e3f2fd"; style.font-color: "#0A0F25" }
Activating: "Activating" { style.fill: "#e8f5e9"; style.font-color: "#0A0F25" }
BankActive: "Bank Active" { style.fill: "#e8f5e9"; style.font-color: "#0A0F25" }
Reading: "Reading" { style.fill: "#e8f5e9"; style.font-color: "#0A0F25" }
Writing: "Writing" { style.fill: "#e8f5e9"; style.font-color: "#0A0F25" }
Precharging: "Precharging" { style.fill: "#e8f5e9"; style.font-color: "#0A0F25" }
Refreshing: "Refreshing" { style.fill: "#fff8e1"; style.font-color: "#0A0F25" }
SelfRefresh: "Self Refresh" { style.fill: "#f3e5f5"; style.font-color: "#0A0F25" }
PrePD: "Precharge\nPower-Down" { style.fill: "#f3e5f5"; style.font-color: "#0A0F25" }
ActPD: "Active\nPower-Down" { style.fill: "#f3e5f5"; style.font-color: "#0A0F25" }

PowerOn -> Reset: "RESET_n = L"
Reset -> Idle: "RESET_n = H"
Idle -> Config: "MRS"
Config -> Idle
Idle -> SelfRefresh: "SRE / SRX"
Idle -> PrePD: "PDE / PDX"
Idle -> Refreshing: "REFab/REFpb\nRFMab/RFMpb"
Refreshing -> Idle
Idle -> Activating: "ACT"
Activating -> BankActive
BankActive -> Reading: "RD"
BankActive -> Writing: "WR"
BankActive -> ActPD: "PDE / PDX"
Reading -> Precharging: "RDA / PREab / PREpb"
Writing -> Precharging: "WRA / PREab / PREpb"
Precharging -> Idle
```

### 규격이 스스로 밝힌 생략 목록

이 절에서 가장 값진 부분은 상태도 자체가 아니라, **무엇을 그리지 않았는지 규격이 명시했다**는 점입니다(§3.3).

- **둘 이상의 뱅크가 관여하는 상태 천이**
- **IEEE1500 명령으로 MR을 적재하거나 테스트 기능을 실행할 때의 상호작용**
- `RESET_n`을 LOW로 놓거나 `HBM_RESET` 명령을 적재해 **임의 상태에서 즉시 reset으로 가는 천이**
- **ECS**, ECS 억제(REFab/SRE의 ECS 플래그), **DRFM**, **ECC Engine Test Mode**
- **DCA와 DCM**
- **Loopback Test Mode**
- **WDQS-to-CK Alignment Training**
- **Rx Offset Calibration Training**

그리고 규격은 덧붙입니다 — 장치 동작의 완전한 기술을 위해서는 상태도와 함께 **커맨드 진리표 및 AC 타이밍 규격**을 사용하라고.

:::caution[검증 구멍이 사는 곳]
생략 목록은 그대로 **설계 위험 목록**입니다. 상태 머신을 Figure 3만 보고 구현하면 다음이 전부 빠집니다.

- **다중 뱅크 동시 상태** — 실제로는 뱅크마다 상태가 있고 서로 다른 상태에 있을 수 있습니다. 채널 단위 단일 FSM으로 모델링하면 **모델이 처음부터 틀립니다.**
- **비동기 리셋 진입** — 임의 상태에서 즉시 reset으로 갈 수 있어야 합니다. 곧 **모든 상태에서 리셋을 걸어 보는 시나리오**가 필요하고, 그 경로는 `RESET_n`과 **IEEE1500 `HBM_RESET`** 양쪽에서 옵니다.
- **테스트 모드와 mission mode의 교차** — 규격이 §13.6을 따로 둘 만큼 복잡한 영역입니다.
- **ECS·DRFM·트레이닝** — 정상 동작 중에 끼어드는 동작들이며, 각각 별도 장에서 다룹니다.

즉 **"간이 상태도"는 뼈대일 뿐이고, 실제 검증 대상은 이 목록만큼 더 큽니다.** 6.1절에서 이 목록을 그대로 V-Plan 항목으로 옮깁니다.
:::

## 🔬 검증 적용

### 6.1 무엇이 깨질 수 있는가

이 장의 결함에는 공통점이 하나 있습니다 — **주소가 틀리면 데이터 미스매치로 나타납니다.** scoreboard는 "기대값과 다르다"고만 말하고, 원인이 주소 디코드인지 데이터 경로인지 알려주지 않습니다. 그래서 주소는 **별도로, 먼저** 검사해야 합니다.

| 조문 | 위반 형태 | 증상 | 잡히는 시점 |
|---|---|---|---|
| Table 4 Note 5 — `RA[13:12] = 11` 무효 | 자극이 그 조합을 생성 | DUT 동작 미정의. 모델은 그럴듯한 값을 돌려주므로 **통과할 수도 있다** | **없음** — 버스에 감시를 두지 않으면 |
| Note 6·8 — `SID[1:0]=11`, 4Hi의 `SID[0]=1` 무효 | 구성보다 넓은 SID 범위를 랜덤화 | 존재하지 않는 뱅크 접근 | **없음** |
| Note 2 — BL8 오프셋 비트 **미전송** | 물리 주소 하위 비트를 `CA`에 실음 | 엉뚱한 열 접근 → **데이터 미스매치로 위장** | scoreboard (오진 유발) |
| Note 3 — 물리 행 2 KB, `RA[13]`이 절반 선택 | 행 히트 판정을 잘못된 층위로 | reference model의 page hit/miss 예측이 어긋남 | 타이밍 checker **false FAIL** |
| Table 6 — 그룹 의존 타이밍 | 그룹 판정을 PC 통합으로 유지 | `tRRDL`/`tRRDS` 오선택 → false FAIL 또는 **놓친 위반** | 간헐적 |
| Table 4 Note 4 — SID 연동 타이밍 | checker가 SID를 무시 | 고 SID에서만 나는 타이밍 위반을 못 봄 | **실리콘** |
| Table 6 — `tCCDR` (세 번째 경우) | RD→RD를 같은 그룹/다른 그룹 2택으로 | 세 번째 경우가 통째로 미검사 | 없음 |
| §3.3 생략 목록 — 다중 뱅크 천이 | 상태 모델을 채널당 단일 FSM으로 | 뱅크가 서로 다른 상태에 있는 것을 표현 못함 | 모델이 **처음부터 틀림** |

마지막 줄이 가장 무겁습니다. §3.3 Figure 3을 그대로 모델로 옮기면, 규격이 **"그리지 않았다"고 스스로 밝힌 것**을 그대로 빠뜨립니다. 상태 모델은 **뱅크마다 한 벌**이어야 합니다.

| 계층 | 인스턴스 | 모델이 드는 상태 |
|---|---|---|
| 채널 | × 32 | 저전력(PD/SR), Mode Register — **두 PC 공통** |
| ↳ PC | × 2 | 배열 타이밍 카운터, **마지막 접근 그룹** |
| ↳↳ 뱅크 | × 16/32/48/64 (밀도별) | Idle / Activating / Active / Reading / Writing / Precharging, 열린 행 주소 |

**"마지막 접근 그룹"이 PC 계층에 있는 것**이 핵심입니다. 채널 계층에 두면 PC0의 접근이 PC1의 `tRRD` 선택을 오염시킵니다.

:::caution[규격이 밝힌 생략 목록 = 커버리지 구멍 목록]
§3.3이 "상태도에 그리지 않았다"고 나열한 여덟 항목은, 검증에서는 **자극하지 않으면 절대 안 나오는 시나리오 목록**입니다.

| 생략 항목 | 검증에서의 의미 |
|---|---|
| 둘 이상 뱅크가 관여하는 천이 | 다중 뱅크 동시 Active 시나리오 |
| IEEE1500 MR 적재·테스트 기능 상호작용 | 테스트 모드 × mission mode 교차 ([11장](../11_training_ieee1500/)) |
| 임의 상태에서 즉시 reset | **모든 상태에서** `RESET_n`·`HBM_RESET` 진입 ([03장](../03_init_reset_power/)) |
| ECS · ECS 억제 · DRFM · ECC Test Mode | [06장](../06_row_commands/) · [09장](../09_ecc_ecs_sev/) |
| DCA · DCM | [11장](../11_training_ieee1500/) |
| Loopback Test Mode | [10장](../10_test_repair/) |
| WDQS-to-CK Alignment Training | [05장](../05_clocking_dbi/) |
| Rx Offset Calibration Training | [11장](../11_training_ieee1500/) |

이 목록을 그대로 V-Plan 항목으로 옮기면 됩니다. 규격이 검증 계획의 절반을 대신 써 준 셈입니다.
:::

### 6.2 어떻게 잡는가 — 수단 선택

| 규칙 | 성격 | 수단 | 이유 |
|---|---|---|---|
| 물리 주소 → 장치 필드 매핑 | **함수 정합** | **reference model + 왕복 검사** | 값 하나로 판정되지 않는다. 역변환이 원래 값을 돌려주는지 봐야 한다 |
| 무효 조합이 버스에 나가지 않음 | **불변식** | **인터페이스 SVA** | 모델이 아니라 **핀에서** 봐야 한다. 모델은 무효 조합에도 답을 만들어 준다 |
| 그룹 의존 타이밍 선택 | **시간 관계** | **SVA** | 두 커맨드 사이 간격의 국소 판정 |
| 뱅크 상태 천이 적법성 | **상태** | **shadow model (뱅크당 한 벌)** | 뱅크마다 독립 상태. SVA로 쓰면 뱅크 수만큼 복제된다 |

**① 주소 매핑 — 왕복 검사**

주소 디코더 결함이 데이터 미스매치로 위장하는 문제를 푸는 방법입니다. 인코딩과 디코딩을 **둘 다** 두고, 왕복이 항등이 되는지 봅니다.

```systemverilog
// 물리 주소 <-> 장치 필드 양방향 모델. 왕복이 항등이어야 한다.
class hbm4_addr_model extends uvm_object;
  `uvm_object_utils(hbm4_addr_model)

  hbm4_cfg_t cfg;                       // 구성 (밀도·스택 높이·SID 폭)

  function hbm4_addr_t encode(bit [39:0] pa);
    // BL8 의 8 UI 를 고르는 하위 비트는 장치로 나가지 않는다 (Table 4 Note 2).
    // 여기서 절단하는 것이 이 함수의 계약이다.
    bit [39:0] a = pa >> $clog2(BURST_BYTES);
    encode.ca  = a[CA_W-1:0];                     a = a >> CA_W;
    encode.ba  = a[BA_W-1:0];                     a = a >> BA_W;
    encode.sid = a[cfg.sid_used_bits-1:0];        a = a >> cfg.sid_used_bits;
    encode.ra  = a[RA_W-1:0];
  endfunction

  function bit [39:0] decode(hbm4_addr_t f);
    decode = f.ra;
    decode = (decode << cfg.sid_used_bits) | f.sid;
    decode = (decode << BA_W)              | f.ba;
    decode = (decode << CA_W)              | f.ca;
    decode = decode << $clog2(BURST_BYTES);       // 절단된 오프셋은 0 으로 복원된다
  endfunction

  // 왕복 검사 — 버스트 정렬된 주소에 대해 항등이어야 한다
  function void check_roundtrip(bit [39:0] pa);
    bit [39:0] aligned = pa & ~((1 << $clog2(BURST_BYTES)) - 1);
    if (decode(encode(aligned)) !== aligned)
      `uvm_error("ADDR_MAP", $sformatf(
        "왕복 불일치: pa=%0h -> %0h. 필드 폭 합이 물리 주소 폭과 어긋난다", aligned,
        decode(encode(aligned))))
  endfunction
endclass
```

`decode(encode(x)) == x` 가 깨지는 대표 원인은 **필드 폭의 합이 안 맞는 것**입니다. 그리고 그 결함은 데이터 비교만으로는 "가끔 틀린다"로만 보입니다.

**② 무효 조합 — 핀에서 본다**

```systemverilog
// bind 대상: 채널 인터페이스. 무효 조합은 장치에 도달하면 안 된다 (Table 4 Note 5·6·8).
module hbm4_addr_legal_chk #(parameter int SID_USED = 2, parameter int STACK_HIGH = 16)
                           (input logic ck, rst_n, cmd_vld,
                            input logic [13:0] ra, input logic [1:0] sid);
  import uvm_pkg::*;
  `include "uvm_macros.svh"

  a_ra_legal: assert property (@(posedge ck) disable iff (!rst_n)
      cmd_vld |-> (ra[13:12] != 2'b11))
    else `uvm_error("ADDR_ILLEGAL", "RA[13:12]=11 은 무효 조합이다 (Table 4 Note 5)")

  a_sid_legal: assert property (@(posedge ck) disable iff (!rst_n)
      (cmd_vld && SID_USED == 2) |-> (sid != 2'b11))
    else `uvm_error("ADDR_ILLEGAL", "SID[1:0]=11 은 무효 조합이다 (Note 6)")

  a_sid_4hi: assert property (@(posedge ck) disable iff (!rst_n)
      (cmd_vld && STACK_HIGH == 4) |-> (sid[0] == 1'b0))
    else `uvm_error("ADDR_ILLEGAL", "4-high 에서 SID[0]=1 은 무효다 (Note 8)")

  // 유효 경계값에는 실제로 도달했는가 — 안 그러면 위 검사는 무의미하다
  c_ra_max_legal: cover property (@(posedge ck) cmd_vld && ra[13:12] == 2'b10);
  c_sid_max_legal: cover property (@(posedge ck) cmd_vld && SID_USED == 2 && sid == 2'b10);
endmodule
```

이 검사를 **모델 안**에 두면 안 됩니다. 모델은 무효 조합을 받아도 어떤 답이든 만들어 내므로, 검사가 통과하는 것처럼 보입니다. **핀에서 봐야** 합니다.

**③ 그룹 의존 타이밍**

```systemverilog
// Table 6 — 같은 그룹이면 tRRDL, 다르면 tRRDS. 판정은 PC 별로 유지한다 (§3.1.2).
property p_trrd(int pc);
  logic [2:0] g;
  @(posedge ck) disable iff (!rst_n)
    (act_vld && act_pc == pc, g = bank_group)
      |=> ##[0:$] (act_vld && act_pc == pc)
          |-> (cycles_since_last_act[pc] >= ((g == last_group[pc]) ? T_RRDL : T_RRDS));
endproperty
```

여기서 `last_group` 을 PC로 인덱싱하지 않으면, PC1의 ACTIVATE가 PC0의 그룹 기록을 덮어써서 **잘못된 임계값으로 판정**합니다. 이 결함은 두 PC를 동시에 자극할 때만 나오므로, 단일 PC 테스트만 도는 회귀에서는 영원히 안 보입니다.

### 6.3 무엇을 덮었다고 말할 수 있는가

주소 공간은 넓어서 "전부 자극"이 불가능합니다. 따라서 coverage는 **값**이 아니라 **관계**를 덮어야 합니다.

```systemverilog
covergroup cg_hbm4_addressing with function sample(
    hbm4_addr_t a, hbm4_cfg_t cfg, timing_sel_e tsel, page_res_e page);
  option.per_instance = 1;

  // --- 구조 축 ---------------------------------------------------------
  cp_bank_group : coverpoint a.bank_group { bins g[] = {[0:7]}; }
  cp_sid        : coverpoint a.sid iff (cfg.sid_used_bits > 0) {
    bins s[] = {[0:2]};                     // 3 = 무효 (Note 6)
    illegal_bins bad = {3};
  }
  cp_pc         : coverpoint a.pc { bins pc0 = {0}; bins pc1 = {1}; }

  // RA 의 MSB — 물리 행 2 KB 의 어느 절반인가 (Note 3)
  cp_row_half   : coverpoint a.ra[13] { bins lower = {0}; bins upper = {1}; }
  // RA[13:12]=11 은 무효. 나머지 셋에 모두 도달했는가
  cp_ra_high    : coverpoint a.ra[13:12] { bins ok[] = {2'b00, 2'b01, 2'b10};
                                           illegal_bins bad = {2'b11}; }

  // --- 관계 축 — 이 장의 핵심 ------------------------------------------
  // "어떤 타이밍이 실제로 선택되었는가". 값이 아니라 분기를 센다.
  cp_timing_sel : coverpoint tsel {
    bins rrd_long  = {T_SEL_RRDL};  bins rrd_short = {T_SEL_RRDS};
    bins ccd_long  = {T_SEL_CCDL};  bins ccd_short = {T_SEL_CCDS};
    bins ccd_rd    = {T_SEL_CCDR};             // 세 번째 경우 (Table 6)
    bins wtr_long  = {T_SEL_WTRL};  bins wtr_short = {T_SEL_WTRS};
  }
  cp_page       : coverpoint page { bins hit = {PAGE_HIT}; bins miss = {PAGE_MISS};
                                    bins conflict = {PAGE_CONFLICT}; }

  // 그룹 의존 타이밍이 두 PC 에서 모두 나왔는가 — 6.2 ③ 의 결함을 잡는 축
  x_timing_pc   : cross cp_timing_sel, cp_pc;
  // SID 가 타이밍에 연동될 수 있다 (Note 4) — SID 별로 각 타이밍이 나왔는가
  x_timing_sid  : cross cp_timing_sel, cp_sid;
endgroup
```

세 가지를 지적해 둡니다.

- **`cp_timing_sel` 이 이 장의 중심 축입니다.** 뱅크 그룹 bin이 다 찼다고 해서 `tRRDL`과 `tRRDS`가 **둘 다 선택되었다**는 뜻은 아닙니다. 덮어야 하는 것은 주소가 아니라 **그 주소가 만든 분기**입니다.
- **`ccd_rd`(`tCCDR`) bin이 비는 것**이 이 장에서 가장 흔한 구멍입니다. RD→RD를 2택으로 이해한 환경은 이 bin을 영원히 못 채웁니다.
- **`illegal_bins`** 를 쓴 이유 — 무효 조합은 "안 덮인 것"이 아니라 "나오면 안 되는 것"입니다. 자극 쪽 실수를 커버리지 도구가 직접 잡아 줍니다.

### 6.4 어떻게 자극하는가

**① 그룹 관계를 의도적으로 만든다** — 랜덤 주소만으로는 `tRRDL`이 잘 안 나옵니다. 뱅크 64개 중 같은 그룹은 8개뿐이라 확률이 낮기 때문입니다.

```systemverilog
class seq_bank_group_walk extends uvm_sequence #(hbm4_cmd_item);
  `uvm_object_utils(seq_bank_group_walk)
  rand bit same_group;                        // 두 모드를 명시적으로 나눈다

  virtual task body();
    bit [5:0] b0, b1;
    b0 = $urandom_range(0, 63);
    // 같은 그룹 = 상위 비트 동일, 다른 그룹 = 상위 비트 상이
    b1 = same_group ? {b0[5:3], $urandom_range(0,7)}
                    : {~b0[5:3], $urandom_range(0,7)};
    `uvm_do_with(req, { cmd == ACT; bank == b0; })
    `uvm_do_with(req, { cmd == ACT; bank == b1; })   // 여기서 tRRDL / tRRDS 가 갈린다
  endtask
endclass
```

**② 구성 순회** — SID는 구성마다 유효 범위가 다릅니다(4Hi 0개 · 8Hi 1비트 · 12/16Hi 2비트, 단 `11` 무효). 환경 구성이 하나로 고정되면 `cp_sid` 는 영원히 부분만 찹니다. 구성 프로파일 분리는 [`hbm_dv` Ch06](../../hbm_dv/06_env_hierarchy/).

**③ 무효 조합은 격리된 negative 시퀀스로** — 정상 회귀에서는 자극이 무효 조합을 만들면 안 됩니다(`illegal_bins`). 그러나 컨트롤러의 **방어 로직**을 검증하려면 일부러 만들어 봐야 합니다. 두 목적을 한 시퀀스에 섞으면 정상 회귀가 오염되므로, 별도 테스트로 격리하고 checker를 그때만 비활성화합니다.

**④ 다중 뱅크 동시 Active** — §3.3 생략 목록의 첫 항목입니다. 여러 뱅크를 열어 둔 채로 서로 다른 상태에 놓는 시퀀스가 없으면, 뱅크당 상태 모델을 만들어 놓고도 그 구조를 한 번도 시험하지 않게 됩니다.

```systemverilog
// tFAW 창 안에서 서로 다른 그룹의 뱅크 넷을 연다 — 그다음 각각 다른 커맨드를 보낸다
`uvm_do_with(req, { cmd == ACT; bank == 6'h00; })   // Group A
`uvm_do_with(req, { cmd == ACT; bank == 6'h08; })   // Group B
`uvm_do_with(req, { cmd == ACT; bank == 6'h10; })   // Group C
`uvm_do_with(req, { cmd == ACT; bank == 6'h18; })   // Group D
`uvm_do_with(req, { cmd == RD;  bank == 6'h00; })   // A 는 Reading
`uvm_do_with(req, { cmd == WR;  bank == 6'h08; })   // B 는 Writing 으로 갈라 놓는다
```

## 7. 대표 문제 — dry-run

### 문제 1 — 페이지 크기 검산

> `CA[4:0]`, prefetch 256 bit일 때 PC당 페이지 크기를 관계식으로 구하고, 물리적으로 열리는 행 크기와의 관계를 설명하라.

<details>
<summary>풀이</summary>

```
Page Size = 2^COLBITS × (Prefetch / 8) = 2^5 × (256/8) = 32 × 32 = 1024 B = 1 KB
```

§2의 "PC당 page 1 KB"와 일치한다.

물리적으로 열리는 행은 **2 KB**이고, **`RA`의 MSB(`RA[13]`)가 그 절반을 선택**한다(Note 3). 따라서 논리 페이지(1 KB)와 물리 행(2 KB)이 **1:2**로 대응한다.

**검증 함의**: reference model의 page hit/miss 예측을 `RA[13:0]` 전체로 할지 `RA[12:0]`으로 할지가 갈린다. 두 층위를 섞으면 예측이 어긋나고, 그 결과는 **타이밍 checker의 false FAIL**로 나타난다 — 원인이 주소 모델에 있는데 타이밍 버그처럼 보이는 전형적인 오진 경로다.
</details>

### 문제 2 — 뱅크 그룹 판정

> 64뱅크 구성에서 뱅크 인덱스 11번과 27번에 연속 ACTIVATE를 발행한다. 어떤 타이밍이 적용되는가?

<details>
<summary>풀이</summary>

Table 5 배정: 뱅크 8–15는 **Group B**, 뱅크 24–31은 **Group D**.

- 11번 → Group B
- 27번 → Group D
- **다른 그룹** → **`tRRDS`** (짧은 쪽)

비트로 확인하면, 뱅크 인덱스 = `{SID, BA[3:0]}`이고 그룹 = 인덱스[5:3]:
- 11 = `001011` → 그룹 `001` = B
- 27 = `011011` → 그룹 `011` = D ✅

**만약 11번과 13번이었다면** 둘 다 Group B이므로 `tRRDL`(긴 쪽)이 적용된다. 스케줄러가 그룹을 번갈아 배치하면 같은 요청량에도 더 짧은 간격으로 발행할 수 있다.
</details>

### 문제 3 — 구성 검산

> 32 Gb die를 12-high로 쌓았을 때 채널당 밀도와 총 용량은?

<details>
<summary>풀이</summary>

```
총 밀도 = 32 Gb × 12 = 384 Gb
채널당  = 384 Gb / 32채널 = 12 Gb        ← Table 4와 일치
총 용량 = 384 Gb / 8 = 48 GB
```

**함정**: 12-high이므로 SID는 `SID[1:0]`을 쓰되 **`SID[1:0]=11`은 무효**다(Note 6). 따라서 유효 SID 값은 3개이고, 뱅크 수는 3 × 16 = **48뱅크**, 뱅크 그룹은 **6개**(A~F)다. SID 폭이 2비트라고 해서 4개 값을 모두 쓸 수 있는 것이 아니다.
</details>

## 핵심 정리

- 주소 필드는 **`RA[13:0]` · `CA[4:0]` · `BA[3:0]` · `SID[1:0]`**. 무효 조합이 셋 있다 — `RA[13:12]=11`, `SID[1:0]=11`, 4Hi의 `SID[0]=1`. 셋 다 **핀에서** assertion으로 막고 coverage에서는 `illegal_bins` 로 둔다.
- **SID는 층 선택 신호가 아니라 뱅크 주소 확장 비트**다(Note 4). 뱅크 인덱스는 `{SID, BA}`이고, **일부 AC 타이밍이 SID에 연동될 수 있다.**
- **BL8의 8 UI를 구분하는 column 주소 비트는 장치로 전송되지 않는다**(Note 2). 이것을 틀리면 **데이터 미스매치로 위장**하므로, 주소는 데이터와 분리해 **왕복 검사**(`decode(encode(x)) == x`)로 먼저 본다.
- `Page = 2^COLBITS × (Prefetch/8)` = **1 KB**. 물리 행은 **2 KB**이고 **`RA`의 MSB가 절반을 고른다**(Note 3).
- 뱅크 그룹은 **연속 8뱅크 단위**이고, 그룹 인덱스는 `{SID, BA[3]}` 로 정해진다 [추론].
- 그룹이 타이밍을 가른다 — **S = 다른 그룹(짧음), L = 같은 그룹(김)**. 64뱅크에서 같은 그룹일 확률은 **1/8**이라, 순수 랜덤 자극은 **긴 쪽 경로를 훨씬 덜 덮는다.** 그룹 관계를 자극의 명시 축으로 올려야 한다.
- **간이 상태도는 뼈대일 뿐**이다. 규격이 스스로 밝힌 생략 목록(다중 뱅크·IEEE1500 상호작용·즉시 리셋·ECS/DRFM·DCA/DCM·loopback·트레이닝)이 **그대로 V-Plan 항목**이 된다 — 규격이 검증 계획의 절반을 대신 써 준 셈이다.
- 상태 모델은 **뱅크마다 한 벌**, 마지막 접근 그룹은 **PC마다 한 벌**이다. 후자를 채널 계층에 두면 PC0의 접근이 PC1의 `tRRD` 선택을 오염시킨다.
- coverage는 주소 값이 아니라 **선택된 타이밍**(`tRRDL/S` · `tCCDL/S/R` · `tWTRL/S`)을 센다. `tCCDR` bin이 비는 것이 이 장에서 가장 흔한 구멍이다.

## Further Reading

- **규격**: JESD270-4 §3.2 Channel Addressing (Table 4) · §3.2.1 Bank Groups (Table 5–6) · §3.3 Simplified State Diagram (Figure 3)
- **다음 장**: [03 — 초기화·리셋·전원 시퀀스](../03_init_reset_power/)
- **관련**: [06 — Row 커맨드](../06_row_commands/) (tRRD 적용) · [07 — Column 커맨드](../07_column_commands/) (tCCDR)
- **이해도 점검**: [퀴즈](../quiz/02_addressing_bank_groups_quiz/)
