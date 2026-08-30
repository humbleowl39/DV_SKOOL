---
title: "02 — 주소 체계와 뱅크 그룹"
description: JESD270-4 §3.2–3.3 · RA/CA/BA/SID 주소 구성, 뱅크 그룹 의존 타이밍, 간이 상태 천이도
---

:::tip[🎯 Learning Objectives]
이 모듈을 마치면:

- **Interpret** Table 4의 주소 필드 구성과 주석이 강제하는 디코더 제약을 도출한다.
- **Calculate** 페이지 크기·채널 밀도·뱅크 수를 규격의 관계식으로 검산한다.
- **Explain** SID가 별도 층 선택 신호가 아니라 **뱅크 주소 확장 비트**로 동작하는 이유를 설명한다.
- **Design** 뱅크 그룹 판정 로직과 그에 따라 갈리는 타이밍 카운터 선택 경로를 설계한다.
- **Analyze** 간이 상태도가 **의도적으로 생략한 것**들이 설계에서 어디에 숨는지 식별한다.
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
2. **타이밍이 SID에 따라 달라질 수 있다.** 물리적으로 다른 die에 있는 뱅크이므로 일부 파라미터가 변형될 수 있다는 뜻이고, 타이밍 체커가 SID를 무시하면 안 된다는 뜻입니다.

[01장](../01_landscape_organization/)에서 확인한 "4-high를 넘는 die는 채널이 아니라 용량·SID·뱅크를 늘린다"는 조문이 여기서 구체화됩니다.

### 버스트 순서는 고정이고, 주소로 지정되지 않는다

Table 4 Note 2가 설계에 직접 닿는 조문입니다.

> Read와 Write의 **버스트 순서는 고정**이며, HBM 장치는 BL8 버스트의 **여덟 UI를 구분하는 column 주소 비트를 배정하지 않는다.** 메모리 컨트롤러가 내부적으로 그런 column 주소 비트를 둘 수는 있으나 **그 비트들은 HBM 장치로 전송되지 않는다.** — Note 2 (요약)

즉 컨트롤러가 바이트 단위 주소를 다루더라도, **장치로 나가는 `CA[4:0]`에는 버스트 내 위치 정보가 실리지 않습니다.** 주소 디코더의 하위 비트는 컨트롤러 내부에서 소비되고 절단됩니다. 이것을 모르고 `CA`에 하위 비트를 실으면 엉뚱한 열을 접근합니다.

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

:::caution[성능 설계로 직결된다]
뱅크 그룹은 단순한 주소 구획이 아니라 **스케줄러 설계 변수**입니다. 컨트롤러가 요청을 재정렬할 때 **그룹을 번갈아 가며** 발행하면 `tCCDS`(짧은 쪽)를 쓸 수 있고, 같은 그룹에 몰아 보내면 `tCCDL`(긴 쪽)에 묶입니다. 같은 대역폭 요구에도 **주소 매핑과 스케줄링 정책에 따라 실효 성능이 갈립니다.**
:::

## 5. 간이 상태 천이도 — 그리고 그것이 감춘 것

§3.3 Figure 3은 허용된 상태 천이와 그것을 제어하는 커맨드를 간략히 보여줍니다.

```d2
direction: right

PowerOn: "Power On" { style.fill: "#eceff1"; style.font-color: "#0A0F25" }
Reset: "Reset" { style.fill: "#eceff1"; style.font-color: "#0A0F25" }
Config: "Configure Device\n(MRS)" { style.fill: "#fff8e1"; style.font-color: "#0A0F25" }
Idle: "**Bank Idle**" { style.fill: "#e3f2fd"; style.font-color: "#0A0F25" }
Activating: "Activating" { style.fill: "#e8f5e9"; style.font-color: "#0A0F25" }
BankActive: "**Bank Active**" { style.fill: "#e8f5e9"; style.font-color: "#0A0F25" }
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

:::caution[설계 버그가 사는 곳]
생략 목록은 그대로 **설계 위험 목록**입니다. 상태 머신을 Figure 3만 보고 구현하면 다음이 전부 빠집니다.

- **다중 뱅크 동시 상태** — 실제로는 뱅크마다 상태가 있고 서로 다른 상태에 있을 수 있습니다. 채널 단위 단일 FSM으로 모델링하면 처음부터 틀립니다.
- **비동기 리셋 진입** — 임의 상태에서 즉시 reset으로 갈 수 있어야 합니다. FSM의 모든 상태에 그 경로가 있어야 하고, 그 경로는 `RESET_n`과 **IEEE1500 `HBM_RESET`** 양쪽에서 옵니다.
- **테스트 모드와 mission mode의 교차** — 규격이 §13.6을 따로 둘 만큼 복잡한 영역입니다.
- **ECS·DRFM·트레이닝** — 정상 동작 중에 끼어드는 동작들이며, 각각 별도 장에서 다룹니다.

즉 **"간이 상태도"는 뼈대일 뿐이고, 실제 FSM은 이 목록만큼 더 커집니다.**
:::

## ⚙️ 설계 적용 (RTL / Front-end)

### 6.1 주소 디코더 — 컨트롤러 물리 주소에서 장치 필드까지

컨트롤러는 시스템 물리 주소를 받아 채널·PC·뱅크·행·열로 쪼갭니다. 규격 제약을 반영한 구조는 이렇습니다.

```systemverilog
// 파라미터로 구성을 받는다 — 밀도 코드로 런타임 결정 가능 (Table 4 Note 7)
package hbm4_addr_pkg;
  localparam int RA_W  = 14;  // RA[13:0]   (RA[13:12]=11 무효)
  localparam int CA_W  = 5;   // CA[4:0]
  localparam int BA_W  = 4;   // BA[3:0]
  localparam int SID_W = 2;   // 구성에 따라 0/1/2 비트 사용
  localparam int PC_W  = 1;   // PC 선택 비트
  localparam int CH_W  = 5;   // 최대 32채널
endpackage

typedef struct packed {
  logic [CH_W-1:0]  ch;
  logic             pc;
  logic [SID_W-1:0] sid;
  logic [BA_W-1:0]  ba;
  logic [RA_W-1:0]  ra;
  logic [CA_W-1:0]  ca;
} hbm4_addr_t;
```

두 가지를 지켜야 합니다.

1. **버스트 내 오프셋 비트는 장치로 내보내지 않는다** (Note 2). 물리 주소의 하위 비트는 컨트롤러 내부에서 버스트 정렬에만 쓰고 절단합니다.
2. **무효 조합을 만들지 않는다** — `RA[13:12] = 11`, `SID[1:0] = 11`, 4Hi에서 `SID[0] = 1`. 디코더가 이 조합을 생성할 수 있는 매핑이면 설계 결함입니다.

```systemverilog
// 무효 조합은 발생 자체를 막고, 그래도 도달하면 즉시 드러나게 한다
always_comb begin
  addr_valid = 1'b1;
  if (dec.ra[13:12] == 2'b11)                    addr_valid = 1'b0;  // Table 4 Note 5
  if (SID_USED == 2 && dec.sid == 2'b11)         addr_valid = 1'b0;  // Note 6
  if (STACK_HIGH == 4 && dec.sid[0])             addr_valid = 1'b0;  // Note 8
end
```

### 6.2 뱅크 그룹 판정과 타이밍 선택

Table 5의 배정에서 그룹 인덱스가 곧바로 나옵니다.

```systemverilog
// 뱅크 인덱스 = {SID, BA}, 그룹은 8뱅크 단위 → 그룹 = 인덱스의 상위 비트
logic [SID_W+BA_W-1:0] bank_index;
logic [SID_W:0]        bank_group;

assign bank_index = {dec.sid, dec.ba};
assign bank_group = bank_index[SID_W+BA_W-1 : 3];   // 하위 3비트가 그룹 내 위치
```

그리고 타이밍 카운터 선택이 이 판정에 걸립니다.

```systemverilog
// 직전 접근과 같은 그룹이면 L(Long), 다르면 S(Short)  — Table 6
wire same_group = (bank_group == last_bank_group_q);

wire [TW-1:0] t_rrd = same_group ? T_RRDL : T_RRDS;   // ACT -> ACT
wire [TW-1:0] t_ccd = same_group ? T_CCDL : T_CCDS;   // WR -> WR, RD -> RD
wire [TW-1:0] t_wtr = same_group ? T_WTRL : T_WTRS;   // internal WR -> RD
```

**주의 두 가지.**

- 이 판정은 **PC별로 따로** 유지해야 합니다. 배열 타이밍이 PC별 개별 계수이기 때문입니다(§3.1.2, [01장](../01_landscape_organization/)).
- READ→READ에는 `tCCDR`이라는 세 번째 경우가 있습니다(Table 6). 그룹 동일 여부만으로 2택 분기하면 그 경우를 놓칩니다 → [07장](../07_column_commands/).

### 6.3 SID 연동 타이밍

Table 4 Note 4가 "일부 AC 타이밍이 SID에 연동될 수 있다"고 열어 두었으므로, 타이밍 상수를 **SID로 인덱싱 가능한 형태**로 두는 편이 안전합니다.

```systemverilog
// 벤더·구성에 따라 SID별로 값이 달라질 수 있다 (Table 4 Note 4)
localparam int T_RCD [0:3] = '{T_RCD_S0, T_RCD_S1, T_RCD_S2, T_RCD_S3};
wire [TW-1:0] t_rcd_sel = T_RCD[dec.sid];
```

전 구성에서 값이 같다면 배열의 모든 원소가 같아질 뿐이고, 다른 구성으로 이식할 때 **구조를 바꾸지 않아도 됩니다.**

### 6.4 뱅크 상태 머신의 인스턴스 수

§3.3의 생략 목록 첫 항목("둘 이상의 뱅크가 관여하는 천이")이 여기로 옵니다.

| 계층 | 인스턴스 | 상태 |
|---|---|---|
| 채널 | × 32 | 저전력(PD/SR), MR — **두 PC 공통** |
| ↳ PC | × 2 | 배열 타이밍 카운터, 마지막 접근 그룹 |
| ↳↳ 뱅크 | × 16/32/48/64 (밀도별) | Idle / Activating / Active / Reading / Writing / Precharging, 열린 행 주소 |

**설계 결론**: 상태 머신은 **뱅크마다 한 벌**입니다. 채널 단위 단일 FSM은 Figure 3을 그대로 옮긴 것처럼 보이지만, 규격이 명시적으로 "다중 뱅크 천이는 그리지 않았다"고 밝힌 부분을 구현에서 빠뜨린 것입니다.

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

**설계 함의**: 행 버퍼 히트 판정을 `RA[13:0]` 전체로 하면 맞지만, "물리적으로 같은 행"을 기준으로 판정하려면 `RA[12:0]`을 봐야 한다. 두 층위를 섞으면 히트/미스 판정이 어긋난다.
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

## 🔍 검증 연결

- 주소 디코드 오류가 데이터 비교를 통과하는 문제 → [`hbm_dv` Ch09 Assertion·Checker](../../hbm_dv/09_assertion_checker/)
- 뱅크 그룹을 coverage 축으로 잡는 방법 → [`hbm_dv` Ch10 Coverage·회귀](../../hbm_dv/10_coverage_regression/)
- 채널·밀도 구성을 설정으로 분리하기 → [`hbm_dv` Ch06 환경 계층](../../hbm_dv/06_env_hierarchy/)

## 핵심 정리

- 주소 필드는 **`RA[13:0]` · `CA[4:0]` · `BA[3:0]` · `SID[1:0]`**. 무효 조합이 셋 있다 — `RA[13:12]=11`, `SID[1:0]=11`, 4Hi의 `SID[0]=1`.
- **SID는 층 선택 신호가 아니라 뱅크 주소 확장 비트**다(Note 4). 뱅크 인덱스는 `{SID, BA}`이고, **일부 AC 타이밍이 SID에 연동될 수 있다.**
- **BL8의 8 UI를 구분하는 column 주소 비트는 장치로 전송되지 않는다**(Note 2). 버스트 순서는 고정이다.
- `Page = 2^COLBITS × (Prefetch/8)` = **1 KB**. 물리 행은 **2 KB**이고 **`RA`의 MSB가 절반을 고른다**(Note 3).
- 뱅크 그룹은 **연속 8뱅크 단위**이고, 그룹 인덱스는 `{SID, BA[3]}` 로 정해진다 [추론].
- 그룹이 타이밍을 가른다 — **S = 다른 그룹(짧음), L = 같은 그룹(김)**. 스케줄러가 그룹을 번갈아 쓰면 실효 성능이 달라진다.
- **간이 상태도는 뼈대일 뿐**이다. 규격이 스스로 밝힌 생략 목록(다중 뱅크·IEEE1500 상호작용·즉시 리셋·ECS/DRFM·DCA/DCM·loopback·트레이닝)이 곧 설계 위험 목록이다.
- 상태 머신은 **뱅크마다 한 벌**이다.

## Further Reading

- **규격**: JESD270-4 §3.2 Channel Addressing (Table 4) · §3.2.1 Bank Groups (Table 5–6) · §3.3 Simplified State Diagram (Figure 3)
- **다음 장**: [03 — 초기화·리셋·전원 시퀀스](../03_init_reset_power/)
- **관련**: [06 — Row 커맨드](../06_row_commands/) (tRRD 적용) · [07 — Column 커맨드](../07_column_commands/) (tCCDR)
- **이해도 점검**: [퀴즈](../quiz/02_addressing_bank_groups_quiz/)
