---
title: "05 — 클럭킹과 DBIac"
description: JESD270-4 §6.1–6.2 · WDQS 분주기와 짝수 토글 규칙, WDQS-to-CK 정렬 트레이닝, 바이트 단위 데이터 버스 반전
---

:::tip[🎯 Learning Objectives]
이 모듈을 마치면:

- **Explain** 스트로브 주파수가 커맨드 클럭의 두 배라는 사실이 왜 내부 분주기를 요구하는지 설명한다.
- **Derive** preamble·postamble·트레이닝 토글 수가 **짝수여야 한다**는 규칙의 근거와 위반 결과를 도출한다.
- **Sequence** WDQS-to-CK 정렬 트레이닝의 7단계를 위상 검출기 출력 해석과 함께 재구성한다.
- **Apply** DBIac 진리표를 적용해 주어진 데이터 전이 수에 대한 DBI 상태와 반전 여부를 판정한다.
- **Analyze** 내부 DBIac 상태가 리셋되는 네 조건과 그것이 read 경로 설계에 부과하는 요구를 분석한다.
:::

:::note[Prerequisites]
- [04 — Mode Register](../04_mode_registers/) — `MR0`의 `WDBI`/`RDBI`, `MR8`의 `WDQS2CK`
- [01 — 규격 지형도](../01_landscape_organization/) — DWORD와 스트로브의 대응
:::

:::caution[인용 고지]
본 장은 **JESD270-4 (2025-04, WIP draft)** §6.1–§6.2를 근거로 **요약·재구성**한 것입니다. 그림·표는 옮기지 않고 번호로 지시합니다. 정밀 정의는 **JEDEC 원문 우선**.
:::

---

## 1. 두 개의 클럭, 그리고 분주기

### 주파수 관계

HBM4에는 **주파수가 다른 두 종류의 클럭**이 있습니다(§6.1).

| 클럭 | 대상 | 관계 |
|---|---|---|
| `CK_t`/`CK_c` | row·column 커맨드/주소 버스 (DDR) | 기준 |
| `WDQS_t`/`WDQS_c` | 쓰기 데이터 스트로브 (DWORD당 1쌍) | **CK의 2배** |
| `RDQS_t`/`RDQS_c` | 읽기 데이터 스트로브 (DWORD당 1쌍) | WDQS에서 생성 |

생성 관계도 규정되어 있습니다 — **커맨드 클럭과 WDQS는 같은 PLL에서 생성**되고, **RDQS는 WDQS에서 생성**됩니다.

### 왜 분주기가 필요한가

스트로브가 커맨드 클럭의 두 배 속도라는 사실이 **DRAM 내부 회로에 문제**를 만듭니다. 그 속도로 내부 로직을 돌릴 수 없으므로, 규격은 해법을 명시합니다.

> 스트로브 주파수가 커맨드 클럭 주파수의 두 배이므로, HBM4는 **WDQS 클럭 트리에 reset 타입 클럭 분주기**를 가질 것을 요구한다. WDQS를 분주함으로써 **WDQS 도메인의 DRAM 내부 회로 동작 속도가 절반으로 줄어든다.** — §6.1 (요약)

```d2
direction: right

PLL: "**PLL**\n(공통 소스)" { style.fill: "#e3f2fd"; style.font-color: "#0A0F25" }

CK: "**CK_t / CK_c**\n커맨드·주소 (DDR)\n기준 주파수 f" { style.fill: "#e8f5e9"; style.font-color: "#0A0F25" }

WDQS: "**WDQS_t / WDQS_c**\n쓰기 스트로브\n주파수 **2f**" { style.fill: "#fff8e1"; style.font-color: "#0A0F25" }

DIV: "**reset 타입 분주기**\nWDQS / 2\n→ 내부 회로는 f 로 동작\n위상(0°/90°/180°/270°) 상태를 가짐" { style.fill: "#ffebee"; style.font-color: "#0A0F25" }

RDQS: "**RDQS_t / RDQS_c**\n읽기 스트로브\nWDQS에서 생성" { style.fill: "#f3e5f5"; style.font-color: "#0A0F25" }

CORE: "DRAM 내부 WDQS 도메인 회로" { style.fill: "#eceff1"; style.font-color: "#0A0F25" }

PLL -> CK
PLL -> WDQS
WDQS -> DIV
DIV -> CORE: "속도 절반"
WDQS -> RDQS: "파생"
```

**벤더 자유도가 하나 있습니다** — 내부 `WDQS/2` 전이의 **방향은 벤더 선택**입니다(§6.1). 즉 분주 출력이 어느 에지에서 뒤집히는지는 규격이 정하지 않습니다.

분주기는 **Self Refresh 종료, 전원 인가, Power-down 종료** 이후 **미리 정의된 내부 분주 상태로 초기화**됩니다.

## 2. 짝수 토글 규칙 — 이 장에서 가장 놓치기 쉬운 제약

분주기가 상태(위상)를 갖는다는 사실에서 강력한 제약 하나가 나옵니다.

> READ와 WRITE 양쪽의 **preamble과 postamble의 합**, 그리고 read·write 동작 이전에 수행되는 **트레이닝 동작 중의 WDQS 토글 수의 합**(DCA·DCM, Read DCA 트레이닝, WRITE 트레이닝, 그 밖에 비정합 DQ/DQS 경로 관련 트레이닝 포함)은 **짝수여야 한다.** 그래야 내부 분주기의 상태, 즉 내부 `WDQS/2`의 위상이 유지된다. — §6.1 (요약)

### 그래서 얻는 것

이 규칙을 지키면 보상이 따라옵니다.

> 따라서 **HBM4 WDQS는 READ와 WRITE 동작 전에 별도의 동기화(sync) 동작을 요구하지 않는다.** — §6.1

다른 메모리에서 흔한 "스트로브 동기 시퀀스"가 HBM4에는 없습니다. 대신 **모든 토글 수를 짝수로 유지한다는 규율**이 그 자리를 대신합니다.

:::caution[위반하면 조용히 깨진다]
토글 수가 홀수가 되면 내부 `WDQS/2`의 위상이 뒤집힌 채 남습니다. 그 상태에서 다음 READ/WRITE를 수행하면 **데이터가 반 주기 어긋난 위상으로 처리**됩니다.

문제는 이것이 **즉시 드러나지 않을 수 있다**는 점입니다. 위상이 뒤집혀도 마진이 충분하면 통과하고, 온도·전압이 바뀐 뒤에야 실패합니다. 그리고 원인은 훨씬 앞선 트레이닝 시퀀스에 있습니다.

**설계 규칙**: preamble/postamble 길이와 트레이닝 토글 수를 **컨트롤러가 누적 집계**하고, 각 시퀀스 종료 시 **짝수 불변식(invariant)** 을 확인해야 합니다. 이는 개별 시퀀스마다가 아니라 **합계**에 대한 조건입니다.
:::

### 그 밖의 클럭 규율

- **WDQS는 WRITE/READ 시작 전에 토글을 시작**합니다 — **ISI**(심볼 간 간섭)를 줄이기 위해서입니다.
- **비활성 구간에는 스트로브가 정적**이어야 합니다 — `WDQS_t`/`RDQS_t`는 LOW, `WDQS_c`/`RDQS_c`는 HIGH.
- 비정합 DQ/DQS 경로의 WRITE 트레이닝 시에는 **DQ를 이동시켜 CK와 WDQS가 동기되는 지점에 위상을 맞춥니다.**

### 에지 정의

규격 전반에서 쓰이는 용어를 §6.1이 못 박습니다.

- **상승 에지** = `_t`의 양의 에지와 `_c`의 음의 에지가 **교차**하는 지점
- **하강 에지** = `_t`의 음의 에지와 `_c`의 양의 에지가 교차하는 지점

차동 신호이므로 단일 신호의 문턱 통과가 아니라 **교차점**이 기준입니다. 타이밍 체커를 만들 때 이 정의를 그대로 써야 합니다.

## 3. WDQS-to-CK 정렬 트레이닝

### 목적과 필요 조건

이 트레이닝은 호스트가 **두 PC의 WDQS 스트로브와 CK 사이의 위상 오프셋을 관측**할 수 있게 해서, 그 위상 관계를 **`tDQSS` 규격 범위 안에** 유지하도록 돕습니다(§6.1.1). 제어 비트는 **`MR8` OP3의 `WDQS2CK`** 입니다.

필요 조건이 조건부라는 점이 중요합니다.

> 이 정렬 트레이닝을 수행하지 않고는 **`tDQSS` 타이밍 준수를 보장할 수 없는 경우**, 장치 초기화 후 **최소 한 번** 수행되어야 한다. **`tDQSS`가 충족된다면 필요하지 않다.** — §6.1.1 (요약)

그리고 과최적화를 경고합니다.

> 이 트레이닝 모드를 사용해 WDQS-to-CK 위상 오프셋을 **더 좁히려는 노력은 안정적인 장치 동작을 개선하지 않는다.** — §6.1.1

즉 `tDQSS`를 만족하면 그것으로 충분하고, 더 정밀하게 맞춘다고 이득이 없습니다. **수렴 목표를 "범위 안"으로 잡아야지 "최소값"으로 잡으면 안 됩니다.**

### 7단계 절차

| 단계 | 동작 | 주의 |
|---|---|---|
| 1 | `WDQS2CK` = 1로 진입, **`tMOD` 대기** | 이 모드에서 허용되는 커맨드는 **REFab·REFpb·RFMab·RFMpb·RNOP·CNOP·MRS(종료용)** 뿐 |
| 2 | **WDQS0와 WDQS1 모두 활성화**, 계속 토글 | 매 CK 주기마다 양쪽 위상 검출기에서 유효한 판독을 얻기 위함 |
| 3 | CK 대비 WDQS0/WDQS1 위상을 **천천히 스윕**, `DERR0`/`DERR1` 관측 | 각 검출기가 내부 분주 WDQS의 **0° 위상을 CK 상승 에지로 래치**해 `tWDQS2PD` 후 결과 제공 |
| 4 | **최소 8개의 WDQS 펄스** 수신 후에는 언제든 스트로브 정지 가능 | 정지 상태에서는 검출기 판독이 **무효** — `DERR` 결과 무시 |
| 5 | WDQS 지연을 계속 늘릴 때 출력이 **"early"에서 "late"로 전이**하는 지점이 이상적 정렬 | |
| 6 | `tDQSS` 충족 시 양쪽 스트로브 정지. **이 모드에서 발행한 WDQS 펄스 수가 짝수인지 확인** | 짝수여야 내부 WDQS 상태가 리셋 상태로 복귀 |
| 7 | `WDQS2CK` = 0으로 종료, **`tMOD` 대기** | |

:::caution[1단계의 경고를 그냥 넘기지 마라]
> 이 모드에서 **REFab·REFpb·RFMab·RFMpb 커맨드 사용으로 발생하는 내부 전류 스파이크가 트레이닝 결과에 부정적 영향**을 줄 수 있다. 이 영향을 감안할 수 없는 컨트롤러는 이 모드에서 해당 커맨드 사용을 **피해야 한다.** — §6.1.1 step 1 (요약)

refresh는 이 모드에서 **허용되지만 권장되지 않습니다.** 트레이닝이 길어져 refresh를 건너뛸 수 없는 상황이라면 트레이닝 정확도와 데이터 보존 사이에서 선택해야 합니다.

**설계 판단**: 트레이닝 구간을 `tREFI` 안에 끝낼 수 있도록 짧게 나눠 수행하는 편이, 트레이닝 중 refresh를 섞는 것보다 안전합니다.
:::

### 위상 검출기 출력 해석

Table 31이 판독을 행동으로 옮기는 규칙을 줍니다.

| CK로 샘플링한 내부 `WDQS/2` (0° 위상) | 위상 판정 | `DERR0`/`DERR1` | 권장 조치 |
|---|---|---|---|
| **HIGH** | Early | **HIGH** | WDQS 지연을 **늘린다** |
| **LOW** | Late | **LOW** | WDQS 지연을 **줄인다** |

`DERR` 신호가 여기서 **데이터 오류 신호가 아니라 위상 검출기 출력**으로 재사용된다는 점이 특이합니다 — 트레이닝 모드에서만 성립하는 의미이며, 일반 동작에서의 `DERR` 의미와 혼동하면 안 됩니다.

## 4. DBIac — 바이트 단위 데이터 버스 반전

### 구조

HBM4는 **바이트 단위(byte granular) DBI**를 지원합니다(§6.2.1). `DBI` 신호는 **DDR I/O**이며 read·write 시 DQ와 함께 구동·샘플링됩니다.

용어 규약이 하나 있습니다 — **"DBI"는 명시적으로 "DBI 신호"라고 하지 않는 한 장치의 내부 상태**를 가리킵니다.

활성화는 방향별로 독립입니다.

| 방향 | 제어 비트 | 비활성 시 |
|---|---|---|
| 쓰기 | `MR0` OP1 (`WDBI`) | **DBI 입력은 Don't care, 입력 수신기 비활성화** |
| 읽기 | `MR0` OP0 (`RDBI`) | **DBI 출력 버퍼 꺼짐** |

:::tip[전력 관점의 부수 효과]
비활성 시 수신기와 출력 버퍼가 꺼진다는 것은 DBI가 **쓰지 않으면 전력을 소비하지 않는다**는 뜻입니다. 반대로 켜면 DQ 한 개분의 I/O가 추가로 동작합니다 — DBI의 이득(전이 수 감소)과 비용(추가 I/O)을 함께 봐야 합니다.
:::

### 판정 규칙

**쓰기**는 단순합니다 — `DBI`가 HIGH로 샘플링되면 DRAM이 write 데이터를 반전하고, LOW면 그대로 둡니다.

**읽기**는 DRAM이 직접 판정합니다. **이전 상태에서 전이하는 DQ 신호의 개수**를 세어 결정합니다.

| 바이트 내 전이 비트 수 | 직전 DBI 상태 | 새 DBI | 데이터 |
|---|---|---|---|
| 0 ~ 3 | 무관 | LOW | 반전 안 함 |
| **4** | **LOW** | LOW | 반전 안 함 |
| **4** | **HIGH** | **HIGH** | **반전** |
| 5 ~ 8 | 무관 | **HIGH** | **반전** |

경계값 4에서 **직전 상태에 따라 갈리는 것**이 이 알고리즘의 특징입니다. 이는 히스테리시스를 주어 DBI 신호 자체가 불필요하게 토글하는 것을 막습니다 — DBI도 I/O이므로 그 전이 역시 비용입니다.

:::caution[ECC와 SEV는 DBIac의 대상이 아니다]
규격이 두 번 명시합니다.

- **write**: "ECC 입력은 DBIac 기능의 영향을 받지 않는다"
- **read**: "ECC와 SEV 출력은 DBIac의 영향을 받지 않는다"

즉 DBI는 **DQ 바이트에만** 적용됩니다. ECC/SEV 경로에 반전 로직을 넣으면 데이터가 깨집니다. 그리고 `DPAR`도 별도 취급입니다(아래).
:::

### 내부 DBIac 상태 — 리셋되는 네 조건

읽기 DBI 판정은 **직전 상태**에 의존하므로, 그 상태가 언제 초기화되는지가 중요합니다. §6.2.1.1은 네 가지를 나열합니다.

내부 DBIac 상태가 **LOW로 리셋되는 경우**:

1. `RESET_n` 신호 **비어서트**
2. **`MRS` 커맨드 수신**
3. **write-to-read 버스 턴어라운드**
4. **Self Refresh 종료**

그 밖의 이벤트나 커맨드에서는 **리셋되지 않고 이전 상태를 계속 사용**합니다.

두 번째가 눈에 띕니다 — `MRS`는 설정 변경 커맨드인데 DBI 상태까지 초기화합니다. 즉 **MR을 건드리면 read DBI 계산의 기준점이 사라집니다.**

### 첫 READ와 버스 프리컨디셔닝

> DBI 리셋 이후 **첫 `READ` 커맨드가 등록되면**, HBM4 DRAM은 **`RDBI`가 활성이든 비활성이든 무관하게** read 데이터 이전에 버스를 **LOW로 프리컨디셔닝**한다. read 버스트의 **마지막 UI에 해당하는 내부 상태 `D7`이 후속 read 버스트의 시드 값으로 내부 저장**된다. — §6.2.1.1 (요약)

**`RDBI` 비활성이어도 프리컨디셔닝이 일어난다**는 점이 중요합니다. DBI 기능을 껐다고 해서 이 동작이 사라지지 않습니다.

그리고 `DPAR`은 예외입니다.

> `DPAR` 신호는 **DBI 계산에 포함되지 않으며 LOW로 프리컨디셔닝되지도 않는다.** 초기 상태는 **정의되지 않는다**(LOW 또는 HIGH). — §6.2.1.1

### 연속 READ에서의 상태 유지

read 버스트가 끝나면 DRAM은 **모든 DQ·DBI·ECC 출력 드라이버를 tri-state** 합니다. 그러나 내부적으로는 **DQ·DBI·ECC·SEV의 마지막 데이터 출력을 저장**해 두고, 후속 read의 버스 프리컨디셔닝과 DBIac 계산에 사용합니다(§6.2.1.2).

비연속(non-gapless) read의 경우 프리컨디셔닝 시점이 바이트에 따라 다릅니다.

| 대상 | 첫 유효 데이터 비트 이전 |
|---|---|
| **홀수 바이트** | 명목상 **2 WDQS 사이클** |
| **짝수 바이트** | 명목상 **1 WDQS 사이클** |

## ⚙️ 설계 적용 (RTL / Front-end)

### 5.1 짝수 토글 불변식 감시

가장 중요한 설계 항목입니다. 컨트롤러는 WDQS 토글 수를 **누적**해야 합니다.

```systemverilog
// 내부 WDQS/2 위상 유지를 위해 preamble+postamble+트레이닝 토글의 "합"이 짝수여야 한다 (§6.1)
// 개별 시퀀스가 아니라 누적 합에 대한 조건이므로 패리티 1비트로 충분하다.
logic wdqs_toggle_parity_q;

always_ff @(posedge ck or negedge rst_n) begin
  if (!rst_n)
    wdqs_toggle_parity_q <= 1'b0;                 // 분주기 리셋 상태와 정렬
  else if (wdqs_divider_reload)                    // SR exit / power-up / PD exit
    wdqs_toggle_parity_q <= 1'b0;
  else if (wdqs_toggle_en)
    wdqs_toggle_parity_q <= wdqs_toggle_parity_q ^ 1'b1;
end

// 각 시퀀스(트레이닝·버스트) 종료 시점에 짝수인지 확인한다
`ifndef SYNTHESIS
  a_wdqs_even: assert property (@(posedge ck) disable iff (!rst_n)
    seq_done |-> (wdqs_toggle_parity_q == 1'b0))
    else $error("WDQS toggle count is odd — internal WDQS/2 phase inverted");
`endif
```

**핵심**: 상태는 1비트(패리티)면 충분합니다. 전체 개수를 셀 필요가 없습니다.

그리고 분주기가 재초기화되는 세 시점(**Self Refresh 종료 · 전원 인가 · Power-down 종료**)에 패리티도 함께 리셋해야 합니다 — 그렇지 않으면 컨트롤러의 추적이 장치 실제 상태와 어긋납니다.

### 5.2 스트로브 유휴 상태 구동

```systemverilog
// 비활성 구간에는 정적 레벨 (§6.1)
assign wdqs_t_o = wdqs_active ? wdqs_gen_t : 1'b0;   // idle: LOW
assign wdqs_c_o = wdqs_active ? wdqs_gen_c : 1'b1;   // idle: HIGH
```

이 규정은 [03장](../03_init_reset_power/)의 초기화 5단계(`R[3:0]` HIGH 시점 또는 그 이전에 `WDQS_t` LOW / `WDQS_c` HIGH 구동)와 같은 요구입니다 — 초기화 때만이 아니라 **모든 유휴 구간**에 적용됩니다.

### 5.3 WDQS-to-CK 트레이닝 시퀀서

7단계를 상태로 옮기되, 두 가지를 반영합니다.

```systemverilog
typedef enum logic [2:0] {
  W2C_IDLE,
  W2C_ENTER,      // WDQS2CK=1, tMOD 대기
  W2C_RUN,        // 양 PC 스트로브 토글, 위상 스윕
  W2C_SETTLE,     // tWDQS2PD 후 DERR 판독
  W2C_ADJUST,     // DERR HIGH -> 지연 증가 / LOW -> 지연 감소
  W2C_ALIGNED,    // early->late 전이 확인
  W2C_EXIT        // 펄스 수 짝수 확인 후 WDQS2CK=0, tMOD 대기
} w2c_state_e;

// 4단계: 최소 8 펄스 이후에만 정지 허용
wire may_halt = (wdqs_pulse_cnt_q >= 8);

// 6단계: 종료 시 펄스 수가 짝수여야 한다
wire ok_to_exit = may_halt && (wdqs_pulse_cnt_q[0] == 1'b0);
```

**주의**: 5단계의 판정 기준은 `DERR`의 절대값이 아니라 **"early에서 late로의 전이"** 입니다. 단일 샘플로 판단하면 안 되고, 스윕 과정에서 **전이 지점을 탐색**해야 합니다.

### 5.4 DBIac 판정 로직

읽기 방향은 DRAM이 수행하지만, 컨트롤러는 **동일한 판정을 재현**해 수신 데이터를 복원해야 합니다.

```systemverilog
// 바이트 단위 전이 수를 세고 진리표를 적용한다 (Table 32)
function automatic logic dbi_decide(input logic [7:0] cur, prev, input logic prev_dbi);
  int unsigned n = $countones(cur ^ prev);
  if (n > 4)              return 1'b1;            // 5~8 : 반전
  else if (n == 4)        return prev_dbi;        // 4    : 직전 상태 유지 (히스테리시스)
  else                    return 1'b0;            // 0~3 : 반전 안 함
endfunction

// 수신 측 복원 — DBI 신호가 HIGH면 되돌린다
assign rx_byte = dbi_sig ? ~rx_raw_byte : rx_raw_byte;
```

**세 가지를 지켜야 합니다.**

1. **ECC·SEV 경로는 이 로직을 통과시키지 않습니다**(§6.2.1). 반전 대상은 DQ 바이트뿐입니다.
2. **`DPAR`도 제외**이며 초기 상태가 정의되지 않으므로, 프리컨디셔닝 구간의 `DPAR` 값을 신뢰해서는 안 됩니다.
3. 전이 수 4에서 **직전 DBI 상태를 참조**하므로, 컨트롤러도 그 상태를 추적해야 합니다.

### 5.5 내부 DBI 상태 추적

```systemverilog
// 리셋 조건 네 가지 (§6.2.1.1)
wire dbi_state_reset = reset_n_deassert     // RESET_n 비어서트
                     | mrs_received          // MRS 수신
                     | wr_to_rd_turnaround   // write-to-read 턴어라운드
                     | sref_exit;            // Self Refresh 종료

always_ff @(posedge ck) begin
  if (dbi_state_reset)
    dbi_state_q <= 1'b0;                     // LOW로 리셋
  else if (rd_data_valid)
    dbi_state_q <= dbi_sig;                  // 마지막 UI(D7)가 다음 버스트의 시드
end
```

**주의**: `MRS`가 리셋 조건에 포함되므로, 설정을 바꾸는 동작이 read 데이터 복원 상태에 영향을 줍니다. MR 갱신 시퀀스와 read 파이프라인이 겹치면 복원이 어긋날 수 있으니, [04장](../04_mode_registers/)에서 본 `tMOD` 대기와 함께 다뤄야 합니다.

## 6. 대표 문제 — dry-run

### 문제 1 — DBI 판정

> 직전 바이트가 `8'b0101_0101`, 현재 논리 데이터가 `8'b1010_1010`이고 직전 DBI 상태가 LOW다. 새 DBI 상태와 실제로 버스에 나가는 값은?

<details>
<summary>풀이</summary>

전이 수 = `popcount(0101_0101 ^ 1010_1010)` = `popcount(1111_1111)` = **8**

Table 32에서 5~8 구간이므로 직전 상태와 무관하게:
- **새 DBI = HIGH**
- **데이터 반전** → 버스에는 `8'b0101_0101`이 나간다

**결과**: 실제 버스 전이 수는 8에서 **0**으로 줄었다. DBI 신호 자체가 LOW→HIGH로 한 번 전이하므로 **총 전이는 8 → 1**이다. 이것이 DBI의 이득이다.

**만약 전이 수가 4였다면** 직전 DBI가 LOW이므로 반전하지 않고 DBI도 LOW를 유지한다. DBI 신호가 토글하지 않는 쪽을 택하는 것이다.
</details>

### 문제 2 — 짝수 토글 규칙

> 초기화 후 트레이닝 시퀀스에서 WDQS를 **15회** 토글하고 종료했다. 이어서 WRITE 버스트를 수행하면 무슨 일이 생기는가?

<details>
<summary>풀이</summary>

토글 수가 **홀수**이므로 내부 `WDQS/2` 분주기의 위상이 **리셋 상태와 반대**로 남는다(§6.1).

그 상태에서 WRITE를 수행하면 내부 WDQS 도메인이 **반 주기 어긋난 위상**으로 데이터를 처리한다. HBM4는 READ/WRITE 전에 별도 동기화 동작을 하지 않으므로([§6.1]) 이 어긋남을 **바로잡을 기회가 없다.**

**증상의 성격**: 마진이 충분하면 통과할 수 있어 즉시 드러나지 않는다. 온도·전압·주파수가 바뀐 뒤 간헐 실패로 나타나며, 원인은 훨씬 앞선 트레이닝에 있어 추적이 어렵다.

**설계 대응**: 시퀀스 종료마다 토글 **패리티**를 확인한다(1비트면 충분). 15회로 끝났다면 한 번 더 토글해 16으로 맞춘 뒤 종료해야 한다.

**주의**: 조건은 **개별 시퀀스가 아니라 합계**에 대한 것이다. preamble·postamble·모든 트레이닝 토글을 함께 세야 한다.
</details>

### 문제 3 — 트레이닝 중 refresh

> WDQS-to-CK 정렬 트레이닝이 `tREFI`보다 오래 걸린다. `REFab`을 중간에 넣어도 되는가?

<details>
<summary>풀이</summary>

**허용되지만 권장되지 않는다.** §6.1.1 step 1은 `REFab`·`REFpb`·`RFMab`·`RFMpb`를 이 모드의 허용 커맨드로 명시하면서, 동시에 **"내부 전류 스파이크가 트레이닝 결과에 부정적 영향을 줄 수 있으며, 이 영향을 감안할 수 없는 컨트롤러는 사용을 피해야 한다"** 고 경고한다.

**권장 대응**: 트레이닝을 **`tREFI` 안에 끝나는 단위로 분할**하고, 구간 사이에 정상 모드로 나와 refresh를 수행한 뒤 다시 진입한다.

**단, 주의할 것**: 진입·종료마다 `tMOD` 대기가 필요하고(1·7단계), 매 구간의 WDQS 펄스 수가 **짝수**여야 한다(6단계). 분할 횟수가 늘수록 오버헤드와 실수 여지가 커지므로, 분할 단위를 지나치게 잘게 잡지 않는 편이 좋다.
</details>

## 🔍 검증 연결

- 스트로브·클럭 위상 관계를 assertion으로 감시 → [`hbm_dv` Ch09 Assertion·Checker](../../hbm_dv/09_assertion_checker/)
- 트레이닝 시퀀스를 시나리오로 구성 → [`hbm_dv` Ch08 시나리오](../../hbm_dv/08_testcase_scenarios/)
- PHY·스트로브가 mixed 영역인 이유 → [`hbm_dv` Ch05 Mixed-Level](../../hbm_dv/05_mixed_level/)

## 핵심 정리

- **스트로브 주파수 = 커맨드 클럭의 2배**. 그래서 **WDQS 클럭 트리에 reset 타입 분주기**가 요구되며, 내부 회로는 절반 속도로 동작한다.
- **CK와 WDQS는 같은 PLL**에서, **RDQS는 WDQS**에서 생성된다. 내부 `WDQS/2` 전이 **방향은 벤더 선택**이다.
- ⚠️ **preamble + postamble + 트레이닝 토글의 합은 짝수여야 한다.** 그 대가로 HBM4는 **READ/WRITE 전 별도 동기화가 불필요**하다. 위반하면 위상이 뒤집힌 채 남고 **간헐 실패**로 나타난다. 추적은 **패리티 1비트**면 충분하다.
- 분주기는 **Self Refresh 종료 · 전원 인가 · Power-down 종료** 시 초기화된다 — 컨트롤러의 패리티도 함께 리셋해야 한다.
- **비활성 구간 스트로브는 정적**(`_t` LOW, `_c` HIGH)이며, WDQS는 **ISI 저감을 위해 동작 전에 미리 토글**한다.
- 에지는 **차동 교차점**으로 정의된다.
- WDQS-to-CK 트레이닝은 **`tDQSS`를 만족하면 불필요**하고, **더 좁히려는 시도는 이득이 없다**. 판정 기준은 절대값이 아니라 **early→late 전이**다.
- 트레이닝 중 **refresh는 허용되나 전류 스파이크로 결과를 해칠 수 있다.**
- DBIac은 **바이트 단위**이며 read/write **독립 제어**(`MR0` OP1/OP0)다. 전이 수 **4에서 직전 상태에 따라 갈리는 히스테리시스**가 있다.
- **ECC·SEV·`DPAR`은 DBIac 대상이 아니다.** `DPAR`은 프리컨디셔닝도 되지 않고 초기 상태가 미정의다.
- 내부 DBI 상태는 **`RESET_n` 비어서트 · `MRS` 수신 · write→read 턴어라운드 · Self Refresh 종료**에 LOW로 리셋된다. **`RDBI` 비활성이어도 첫 READ 전 프리컨디셔닝은 수행된다.**

## Further Reading

- **규격**: JESD270-4 §6.1 Clocking Overview (Figure 9–11) · §6.1.1 WDQS-to-CK Alignment Training (Table 31, Figure 12) · §6.2 DBIac (Table 32, Figure 13–16)
- **다음 장**: [06 — Row 커맨드](../06_row_commands/)
- **관련**: [04 — Mode Register](../04_mode_registers/) (`MR0` DBI, `MR8` WDQS2CK) · [11 — 트레이닝과 IEEE 1500](../11_training_ieee1500/) (DCA·DCM)
- **이해도 점검**: [퀴즈](../quiz/05_clocking_dbi_quiz/)
