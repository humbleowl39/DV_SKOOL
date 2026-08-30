---
title: "04 — Mode Register"
description: JESD270-4 §5 · 20개 MR의 기능별 구조, 두 갈래 접근 경로, 프로그래밍 제약과 설계 함의
---

:::tip[🎯 Learning Objectives]
이 모듈을 마치면:

- **Organize** 20개 Mode Register를 기능 축으로 분류하고 각 축이 제어하는 하드웨어를 지목한다.
- **Calculate** 타이밍 MR 값을 `RU{t/tCK}` 규칙으로 산출한다.
- **Explain** MR이 두 PC에 공유되면서도 일부 필드가 PC별로 존재하는 구조를 설명한다.
- **Design** MR 파일 RTL과 설정 변경이 컨트롤러 타이머에 반영되는 경로를 설계한다.
- **Evaluate** "기본값이 정의되지 않는다"는 조문이 초기화 펌웨어에 부과하는 책임을 판단한다.
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

**설계 함의**: 컨트롤러는 장치가 지원하는 범위를 알아야 하고, 그 범위는 `[min, max]` **두 값으로 표현 가능**합니다. 지원 여부를 비트맵으로 관리할 필요가 없습니다.
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

MRS: "**MRS 커맨드**\ncolumn 커맨드 경로\n§6.3.3.4" { style.fill: "#e8f5e9"; style.font-color: "#0A0F25" }
IEEE: "**MODE_REGISTER_DUMP_SET**\nIEEE 1500 테스트 포트\n§13.5.13" { style.fill: "#f3e5f5"; style.font-color: "#0A0F25" }

MR: "**Mode Register 파일**\n20 × 8-bit · MA[4:0]\n채널당 1벌 (두 PC 공유)" { style.fill: "#bbdefb"; style.font-color: "#0A0F25" }

CTRL -> MRS: "쓰기만"
FW -> IEEE: "쓰기 + **읽기**"
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

또한 [01장](../01_landscape_organization/)에서 확인했듯 `MRS`는 **두 PC에 공통인 커맨드**이므로, 발행 시점에 **양쪽 PC 모두**의 타이밍 조건이 충족되어야 합니다(§3.1.2).

## ⚙️ 설계 적용 (RTL / Front-end)

### 5.1 MR 파일 — 채널당 한 벌

```systemverilog
// MR은 두 PC에 공유된다 (§5). 채널당 한 벌이며 PC별로 복제하지 않는다.
localparam int MR_COUNT = 20;   // MR0 ~ MR19
localparam int MR_WIDTH = 8;

logic [MR_WIDTH-1:0] mr_q [MR_COUNT];

always_ff @(posedge ck) begin
  if (mrs_valid && (mrs_ma < MR_COUNT))
    mr_q[mrs_ma] <= mrs_op;
end
```

`MA[4:0]`는 5비트라 32개를 지시할 수 있지만 정의된 것은 20개입니다. **미정의 주소에 대한 쓰기를 무시할지 오류로 처리할지**는 설계 판단이며, 규격이 정하지 않았으므로 컨트롤러 쪽에서 발생 자체를 막는 편이 안전합니다.

### 5.2 필드 배선 — 채널 전역 vs PC별

축 ③에서 본 구조를 배선으로 옮기면 이렇습니다.

```systemverilog
// 채널 전역에 적용되는 필드
wire capar_en = mr_q[0][6];
wire wdbi_en  = mr_q[0][1];
wire rdbi_en  = mr_q[0][0];

// PC별로 갈라지는 필드 — 같은 레지스터의 상·하위 절반
wire [3:0] dca_wdqs_pc0 = mr_q[11][3:0];
wire [3:0] dca_wdqs_pc1 = mr_q[11][7:4];
wire [3:0] dca_rdqs_pc0 = mr_q[10][3:0];
wire [3:0] dca_rdqs_pc1 = mr_q[10][7:4];
```

**흔한 실수 둘**: MR 파일을 PC별로 복제하는 것(규격 위반), 그리고 PC별 필드를 구분 없이 양쪽에 배선하는 것(DCA 코드 교차).

### 5.3 타이밍 값 산출 — `RU{t/tCK}`

```systemverilog
// WR/RAS/RTP는 아날로그 값을 클럭으로 올림한 값 이상이어야 한다 (Table 13~15 Note 2)
// 벤더 데이터시트의 아날로그 값(ps)과 동작 tCK(ps)로 계산한다
function automatic int mr_cycles(input int t_analog_ps, input int t_ck_ps);
  return (t_analog_ps + t_ck_ps - 1) / t_ck_ps;   // round up
endfunction

// 예: tWR=15000 ps, tCK=500 ps  ->  30 nCK
localparam int WR_SETTING = mr_cycles(T_WR_PS, T_CK_PS);
```

**두 가지를 함께 지켜야 합니다.**

1. 계산 결과가 장치의 **지원 범위 안**에 들어가는지 확인 — 범위는 연속이므로 `[min, max]` 비교로 충분합니다(규칙 1).
2. 장치가 클럭 단위 MR 정의를 지원하지 않으면 **설정이 무시되므로**, 컨트롤러 내부 타이머도 **동일한 제약을 독립적으로** 지켜야 합니다. MR에만 의존하면 그 장치에서 타이밍 위반이 납니다.

### 5.4 설정 변경이 컨트롤러 타이머에 반영되는 경로

`MRS`로 `RL`·`WL`·`WR`·`RAS`·`RTP`를 바꾸면 컨트롤러의 스케줄링 상수가 함께 바뀌어야 합니다.

```systemverilog
// MR 갱신 -> 타이밍 상수 재로드. tMOD 등 규정 시간 후에 유효화한다 (§5).
always_ff @(posedge ck) begin
  if (mrs_valid) begin
    mr_update_pending_q <= 1'b1;
    mr_settle_cnt_q     <= T_MOD;
  end else if (mr_update_pending_q) begin
    if (mr_settle_cnt_q == 0) begin
      rl_q <= decode_rl(mr_q[2]);
      wl_q <= decode_wl(mr_q[1]);
      // ...
      mr_update_pending_q <= 1'b0;
    end else
      mr_settle_cnt_q <= mr_settle_cnt_q - 1;
  end
end
```

**핵심**: MR 쓰기 시점과 그 값이 유효해지는 시점이 다릅니다. 즉시 반영하면 `tMOD` 구간 동안 잘못된 지연으로 커맨드를 발행하게 됩니다.

### 5.5 초기화 MR 이미지

"기본값 없음" 조문 때문에, 초기화 펌웨어는 **20개 전부의 값을 갖고 있어야** 합니다.

```
MR 이미지 = 벤더 데이터시트(아날로그 타이밍)
          + 동작 주파수 (tCK)
          + 시스템 정책 (parity on/off, DBI on/off, DRFM on/off)
          + 벤더 전용 영역 (MR12·MR17 — 데이터시트 참조)
```

이 이미지가 **주파수 종속**이라는 점이 중요합니다. DVFS로 클럭을 바꾸는 시스템이라면 주파수마다 MR 이미지가 따로 있어야 하고, 전환 시퀀스에서 재적재해야 합니다.

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

**설계 결론**: MR 값 산출 결과가 필드 범위를 넘는지 반드시 검사해야 한다. 넘는 경우 컨트롤러는 **자체 타이머로 `tRAS`를 강제**하고 MR에 의존하지 않아야 한다. 산출값을 무비판적으로 필드 폭으로 잘라 넣으면(80 → 하위 6비트 = 16) 심각한 타이밍 위반이 된다.
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

**설계 결론**: MR 섀도 레지스터를 컨트롤러에 두는 것은 선택이 아니라 **필수**다. 부분 필드 갱신이 필요한 레지스터가 존재하기 때문이다.
</details>

### 문제 3 — 리셋 직후 상태

> 기능 리셋 후 컨트롤러가 `MR0`의 `TCSR`이 기본값 Enabled라고 가정하고 self refresh를 사용했다. 문제가 있는가?

<details>
<summary>풀이</summary>

**있다.** `MR0`의 `TCSR` 필드 설명에 "1 – Enabled (Default)"가 붙어 있는 것은 사실이지만, §5는 **"별도로 명시된 경우를 제외하면 Mode Register에 기본 상태가 정의되지 않으며, 전원 인가 또는 칩 리셋 후 모든 MR을 완전히 초기화해야 한다"** 고 규정한다.

즉 필드 수준의 (Default) 표기는 **그 값이 권장/기본 설정이라는 의미**이지, **리셋 후 하드웨어가 그 값을 갖는다는 보장이 아니다.** 안전한 해석은 "리셋 후 MR 내용은 미정의"이며, [03장](../03_init_reset_power/) 6단계에서 **모든 MRS를 발행**하는 것이 규격이 요구하는 절차다.

**설계 결론**: 초기화 펌웨어는 20개 MR 전부를 기록한다. 어떤 필드도 "기본값일 것"으로 건너뛰지 않는다.
</details>

## 🔍 검증 연결

- MR 쓰기와 "설정 효과 확인"의 구분 → [`hbm_dv` Ch08 시나리오](../../hbm_dv/08_testcase_scenarios/)
- MR을 RAL로 추상화할 때의 설계 → [`hbm_dv` Ch06 환경 계층](../../hbm_dv/06_env_hierarchy/)
- 설정 프로파일과 체커의 프로파일 독립성 → [`hbm_dv` Ch06](../../hbm_dv/06_env_hierarchy/)

## 핵심 정리

- **8비트 MR 20개(`MR0`~`MR19`)**, `MA[4:0]`로 선택. **`MR12`·`MR17`은 벤더 전용**, `MR16`~`MR19`는 **벤더 선택**.
- **MR은 두 PC에 공유**된다 — 레지스터 인스턴스는 채널당 하나다. 다만 **`MR10`·`MR11`·`MR15`는 하나의 레지스터 안에 PC별 필드**를 갖는다.
- **기본값이 정의되지 않는다.** 리셋 후 20개 전부를 명시적으로 초기화해야 한다. 필드의 (Default) 표기는 권장값이지 리셋값이 아니다.
- 지연 파라미터 범위: `PL` 0–4, `WL` 4–19, **`RL` 17–90**, `WR`·`RAS` 4–63, `RTP` 2–15 nCK.
- 값은 선택적이나 **지원 범위는 연속**이어야 한다 → `[min, max]` 두 값으로 관리 가능.
- 타이밍 MR은 **`RU{t/tCK}` 이상**으로 프로그램한다. **주파수 종속**이며, 기준 아날로그 값은 **벤더 데이터시트**에 있다. 장치가 미지원이면 **조용히 무시**되므로 컨트롤러 자체 타이머가 필요하다.
- **MR을 되읽는 경로는 IEEE 1500 `MODE_REGISTER_DUMP_SET` 뿐**이다. `MRS`는 쓰기 전용.
- 부분 필드 갱신 때문에 컨트롤러의 **MR 섀도 카피는 필수**다.
- `MRS`는 **모든 뱅크 idle** + `tRDMRS` 경과가 전제이며, 위반 시 **unspecified operation**(오류 보고 없음).
- **`DA Port Lockout`이 MR에 있다** — 테스트 접근을 기능 레지스터로 잠근다.

## Further Reading

- **규격**: JESD270-4 §5 Mode Registers (Table 9 개요, Table 10~30 개별 MR)
- **다음 장**: [05 — 클럭킹과 DBIac](../05_clocking_dbi/) — `MR0`의 DBI 비트가 제어하는 대상
- **관련**: [08 — Parity](../08_parity/) (`MR0` CAPAR/WPAR/RPAR, `MR1` PL) · [09 — ECC](../09_ecc_ecs_sev/) (`MR9`) · [11 — 트레이닝](../11_training_ieee1500/) (`MR6`·`MR10`·`MR11`)
- **이해도 점검**: [퀴즈](../quiz/04_mode_registers_quiz/)
