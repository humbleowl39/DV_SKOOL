---
title: "08 — Parity"
description: JESD270-4 §6.4 · Command/Address parity와 Data parity, 프로그래머블 PL, 검출 전용이라는 설계 철학
---

:::tip[🎯 Learning Objectives]
이 모듈을 마치면:

- **Compute** CA parity의 대상 신호 집합과 짝수 규칙으로 `AERR` 값을 판정한다.
- **Explain** 패리티 오류가 발생해도 커맨드가 실행되고 write가 완료되는 이유와 그 설계 함의를 설명한다.
- **Analyze** `PL`(Parity Latency)이 데이터와 `DPAR` 사이에 만드는 시간 어긋남과 그에 따른 추가 스트로브 요구를 분석한다.
- **Determine** `MD`·`WDBI`/`RDBI` 설정에 따라 패리티 대상 집합이 어떻게 달라지는지 판정한다.
- **Design** 패리티 생성·검사 로직과 활성/비활성 전환 시점의 위험 구간을 설계한다.
:::

:::note[Prerequisites]
- [04 — Mode Register](../04_mode_registers/) — `MR0`의 `CAPAR`·`WPAR`·`RPAR`·`WDBI`/`RDBI`, `MR1`의 `PL`, `MR9`의 `MD`
- [07 — Column 커맨드](../07_column_commands/) — 패리티 활성/비활성 MRS의 비대칭 전이
- [05 — 클럭킹과 DBIac](../05_clocking_dbi/) — `DERR`의 또 다른 용도
:::

:::caution[인용 고지]
본 장은 **JESD270-4 (2025-04, WIP draft)** §6.4를 근거로 **요약·재구성**한 것입니다. 표·그림은 옮기지 않고 규칙과 관계만 서술합니다. 정밀 값은 **JEDEC 원문 우선**.
:::

---

## 1. 두 종류의 패리티

HBM4에는 성격이 다른 패리티 기능이 둘 있습니다.

| | Command/Address Parity | Data Parity |
|---|---|---|
| 제어 | `MR0` OP6 (`CAPAR`) | write `MR0` OP5 (`WPAR`) / read `MR0` OP4 (`RPAR`) |
| 기본값 | **Disabled** | **둘 다 Disabled** |
| 신호 | `APAR` 입력 / `AERR` 출력 | `DPAR` 양방향 / `DERR` 출력 |
| 개수 | **AWORD당 1개** | **DWORD당 1개** |
| 방향 | 호스트 → 장치 (검사) | write는 검사, read는 **생성** |

`DPAR`이 **양방향 DDR I/O**라는 점이 특징입니다 — write에서는 호스트가 보내고, read에서는 장치가 만들어 보냅니다.

## 2. Command/Address Parity

### 대상과 규칙

활성화되면 패리티는 **매 CK 사이클마다, 상승 에지와 하강 에지에 대해 각각 별도로** 계산됩니다. 대상 신호는 넷입니다.

```
R[9:0]  +  C[7:0]  +  ARFU  +  APAR
```

**`ARFU`가 포함된다는 점**에 주목하세요. [06장](../06_row_commands/)에서 *"진리표에 없지만 유효 레벨로 구동해야 한다"* 고 했던 그 신호가 패리티 계산에는 참여합니다. 구동하지 않으면 패리티가 틀립니다.

판정은 **짝수 패리티**입니다.

| HIGH로 수신된 입력의 합 | `AERR` |
|---|---|
| **짝수** | LOW |
| **홀수** | **HIGH** |

### ⚠️ 오류가 나도 커맨드는 실행된다

이 장 전체를 관통하는 조문입니다.

> **HBM4 DRAM은 command/address 패리티 오류와 무관하게 커맨드를 실행한다.** — §6.4.1

패리티는 **차단(blocking) 장치가 아니라 보고(reporting) 장치**입니다. 잘못된 커맨드도 그대로 수행되며, `AERR`로 "그런 일이 있었다"고 알릴 뿐입니다.

:::caution[설계·검증에 미치는 영향]
이 성질은 두 가지를 뜻합니다.

1. **복구 책임은 전적으로 호스트에 있습니다.** 장치는 잘못된 주소로 activate를 하거나 엉뚱한 뱅크를 precharge할 수 있고, 컨트롤러가 `AERR`를 보고 상태를 재구성해야 합니다.
2. **`AERR`를 관측하지 않으면 오류가 조용히 지나갑니다.** 데이터가 우연히 맞으면 상위 계층은 아무것도 알아채지 못합니다 — [`hbm_dv`](../../hbm_dv/09_assertion_checker/)에서 말한 **조용한 통과**의 하드웨어적 사례입니다.

**설계 결론**: `AERR`는 "있으면 좋은" 신호가 아니라 **반드시 상시 감시해야 하는 신호**입니다.
:::

### `AERR`의 시간 동작

- 리셋 시 `AERR`는 **LOW로 구동**됩니다.
- 오류마다 `AERR`는 오류 입력의 해당 사이클로부터 **`tPARAC` 후에 1 tCK 동안 HIGH**로 구동됩니다.
- **연속 오류**가 발생하면 `AERR`는 **다음 사이클에도 HIGH를 유지**합니다.

### R과 C를 구별할 수 없다

> **공통 `AERR` 출력 때문에 두 인터페이스에서 발생한 패리티 오류는 구별할 수 없다.** — §6.4.1 (Figure 64 설명)

row 버스에서 났는지 column 버스에서 났는지 `AERR`만으로는 알 수 없습니다. 컨트롤러가 **자신이 발행한 커맨드 이력과 대조**해서 추정해야 합니다.

### 활성화·비활성화 타이밍

[07장](../07_column_commands/)에서 본 비대칭이 여기서 더 구체화됩니다.

> HBM4 DRAM은 패리티 검사 기능을 활성화하는 `MRS` **다음 클럭 사이클부터 검사를 시작할 수 있으며**, 늦어도 그 `MRS` 이후 **`tMOD`가 만료되면 검사가 활성화되어 있다.** — §6.4.1 (요약)

**"다음 사이클부터 ~ `tMOD` 만료까지" 사이 어디선가** 켜집니다. 정확한 시점은 규정되지 않습니다. 따라서 컨트롤러는 **활성화 MRS 직후부터 곧바로 올바른 패리티를 실어야** 안전합니다.

그리고 비활성화 쪽에는 별도 제약이 있습니다.

> **패리티 기능은 access 커맨드 이후 `tPARAC` 이내에 비활성화되어서는 안 된다.** — §6.4.1

`MR0` OP6은 access 커맨드 이후 **최소 `tPARAC` 동안 1로 유지**되어야 합니다. 진행 중인 패리티 검사와 충돌하기 때문입니다.

## 3. Data Parity

### 구조

- **write 검사**는 `WPAR`, **read 생성**은 `RPAR`로 제어되며 **둘 다 기본 비활성**입니다.
- `DPAR` 입력은 write 시 `WPAR`와 함께, `DPAR` 출력은 read 시 `RPAR`와 함께 활성화됩니다. **그 외에는 `DPAR`이 비활성**입니다.
- read에서 장치는 패리티를 **생성**해 DQ·DBI·ECC와 함께 `DPAR`로 전송합니다.
- write에서 장치는 `DPAR` 입력을 DQ·DBI·ECC 입력과 **비교**합니다.

**검사 단위**가 중요합니다.

> 패리티 계산은 write 버스트의 **각 UI마다 별도로** 수행된다. — §6.4.2

그런데 오류 보고는 클럭 사이클 단위입니다.

> write 버스트의 **한 클럭 사이클(D0…D3 또는 D4…D7)** 안에서 단일 또는 복수 UI에 오류가 발생하면, `DERR`는 오류 입력의 해당 사이클로부터 **`tPARDQ` 후 1 tCK 동안 HIGH**로 구동된다. — §6.4.2 (요약)

즉 **계산은 UI 단위, 보고는 반 버스트(4 UI) 단위**입니다. 한 사이클 안에서 오류가 몇 개든 `DERR` 펄스는 하나입니다.

첫 클럭 사이클 오류에 대한 `tPARDQ` 구간은 **`WRITE` 커맨드로부터 `(WL + PL)` 클럭 사이클 후**에 시작합니다.

### ⚠️ 여기서도 차단하지 않는다

> 오류가 발생해도 **HBM4 DRAM은 write 데이터를 차단하지 않는다.** 장치는 **write 트랜잭션을 배열까지 정상적으로 완료**한다. — §6.4.2

CA parity와 같은 철학입니다. **잘못된 데이터가 메모리에 그대로 기록**되고, `DERR`로 알릴 뿐입니다.

:::tip[왜 차단하지 않는가]
차단하려면 장치가 **버스트를 중간에 멈추거나 되돌릴 수 있어야** 합니다. 그런데 [07장](../07_column_commands/)에서 본 대로 HBM4는 **버스트의 중단이나 절단이 없습니다.**

즉 "차단 없음"은 게으른 설계가 아니라 **버스트 모델의 일관된 귀결**입니다. 대신 복구를 호스트로 올려서 장치를 단순하게 유지합니다.

**설계 결론**: 컨트롤러는 `DERR`를 받으면 **해당 write를 재수행**할 수 있어야 합니다. 이는 write 데이터를 `DERR` 보고 시점까지 버퍼에 보관해야 한다는 뜻이고, 그 깊이는 `(WL + PL + tPARDQ)` 로 결정됩니다.
:::

### Parity Latency — 데이터와 패리티를 어긋나게 하는 이유

> 데이터 패리티 기능은 해당 데이터와 `DPAR` 신호 사이에 **프로그래머블 parity latency `PL`** 을 포함한다. `PL`은 `MR1` OP[7:5]에 프로그램되며 **write와 read에 동일**하다. 해당 `DPAR` 신호는 **`PL` 사이클 후에 수신·전송**된다. — §6.4.2 (요약)

패리티를 데이터와 **동시에** 보내지 않고 뒤로 미루는 구조입니다. 그러면 송신 측은 데이터를 다 내보낸 뒤 패리티를 계산할 여유가 생기고, 수신 측도 마찬가지입니다. 고속 인터페이스에서 계산 지연을 흡수하는 전형적 기법입니다.

대가가 하나 따라옵니다.

> **WDQS와 RDQS 스트로브는 지연된 `DPAR` 신호를 양쪽 끝에서 래치하기 위해 동일한 preamble·postamble을 갖는 추가 스트로브 사이클을 갖는다.** — §6.4.2 (요약)

데이터가 끝난 뒤에도 `DPAR`를 받아야 하므로 **스트로브를 더 토글해야** 합니다. 규격의 예시에서 **`PL = 2`일 때 `DPAR` 입력 래치를 위해 4개의 추가 WDQS 펄스**가 수신됩니다.

:::tip[짝수 규칙이 또 나온다]
추가 펄스가 **4개 — 짝수**입니다. 그리고 규격은 그 추가 사이클이 **"동일한 preamble·postamble을 갖는다"** 고 명시합니다.

[05장](../05_clocking_dbi/)의 `WDQS/2` 위상 보존 규칙이 여기서도 지켜지도록 설계된 것입니다. `PL`을 켜면 스트로브 토글 수가 늘지만, **늘어나는 양이 짝수**라 위상은 보존됩니다.

**설계 함의**: `PL` 값을 바꾸면 스트로브 시퀀스 길이가 바뀝니다. 컨트롤러의 스트로브 시퀀서는 `PL`을 파라미터로 받아야 하고, 짝수 불변식 검사도 그 값을 반영해야 합니다.
:::

지원되는 `PL` 범위는 **벤더 데이터시트**를 참조해야 합니다([04장](../04_mode_registers/)에서 본 `MR1` OP[7:5]의 0~4 nCK는 규격이 정의한 인코딩 범위이고, 실제 지원 범위는 장치마다 다릅니다).

### 패리티 대상 집합은 고정이 아니다

Table 47이 정의하는 것은 단순한 진리표가 아니라 **설정에 따라 달라지는 대상 집합**입니다.

| `MD` (`MR9` OP0) | `WDBI`/`RDBI` (`MR0` OP[1:0]) | DWORD0의 패리티 대상 |
|---|---|---|
| Enabled | Enabled | `DQ[31:0]` + `ECC[1:0]` + `DBI[3:0]` + `DPAR0` |
| Enabled | Disabled | `DQ[31:0]` + `ECC[1:0]` + `DPAR0` |
| Disabled | Enabled | `DQ[31:0]` + `DBI[3:0]` + `DPAR0` |
| Disabled | Disabled | `DQ[31:0]` + `DPAR0` |

DWORD1도 대칭입니다(`DQ[63:32]`, `ECC[3:2]`, `DBI[7:4]`, `DPAR1`).

규칙을 말로 옮기면:

- **DBI 신호**는 `WDBI`/`RDBI`가 활성일 때만 포함됩니다.
- **ECC I/O(메타데이터)** 는 `MR9` OP0의 `MD` 비트가 활성일 때만 포함됩니다.
- **`SEV` 신호는 어떤 경우에도 포함되지 않습니다.**

:::caution[설정 간 결합이 만드는 위험]
패리티 대상이 **다른 두 레지스터의 비트에 의존**합니다. `MR0`의 DBI 설정이나 `MR9`의 `MD` 설정을 바꾸면 **패리티 계산식 자체가 바뀝니다.**

컨트롤러와 장치가 서로 다른 대상 집합으로 계산하면 **정상 데이터에서 패리티 오류가 발생**합니다. 그리고 그 오류는 데이터가 실제로는 멀쩡하므로 원인 추적이 어렵습니다.

**설계 결론**: 패리티 생성·검사 로직은 `WDBI`·`RDBI`·`MD` 세 비트를 **입력으로 받아야** 하며, 이 비트들을 바꾸는 MRS 전후로 **패리티 활성 상태를 정리**해야 합니다.
:::

### 비활성화 위험 구간

두 개의 서로 다른 제약이 있습니다.

| 대상 | 비활성화 금지 구간 | 기준점 |
|---|---|---|
| `WPAR` | **`WL + PL + tPARDQ + 2 tCK`** 이내 | `WRITE` 커맨드 |
| `RPAR` | **`tRDMRS`** 이내 | `READ` 커맨드 |
| `CAPAR` | **`tPARAC`** 이내 | access 커맨드 |

세 값이 모두 다르고 기준점도 다릅니다. "패리티를 끈다"는 한 동작이 **세 개의 서로 다른 대기 조건**을 갖는 셈입니다.

## 4. `DERR`의 두 얼굴

[05장](../05_clocking_dbi/)에서 `DERR0`/`DERR1`이 **WDQS-to-CK 정렬 트레이닝의 위상 검출기 출력**으로 쓰이는 것을 보았습니다. 이 장에서는 같은 신호가 **데이터 패리티 오류 출력**입니다.

| 모드 | `DERR`의 의미 |
|---|---|
| 일반 동작 | **데이터 패리티 오류** 보고 (`tPARDQ` 후 1 tCK HIGH) |
| WDQS-to-CK 트레이닝 (`MR8` OP3 = 1) | **위상 검출기 판독** (HIGH = early, LOW = late) |

핀이 재사용되므로 **컨트롤러의 `DERR` 해석 로직은 모드에 따라 갈라져야** 합니다. 트레이닝 중에 `DERR` HIGH를 패리티 오류로 처리하면 존재하지 않는 오류를 보고하게 됩니다.

## ⚙️ 설계 적용 (RTL / Front-end)

### 5.1 CA 패리티 생성

```systemverilog
// 대상: R[9:0], C[7:0], ARFU, APAR — 짝수 패리티 (§6.4.1)
// 상승/하강 에지에 대해 각각 별도로 계산한다.
function automatic logic ca_parity_bit(input logic [9:0] r, input logic [7:0] c, input logic arfu);
  return ^{r, c, arfu};      // APAR을 더했을 때 전체가 짝수가 되도록
endfunction

// 송신: 계산한 값을 APAR로 내보낸다
assign apar_rise_o = ca_parity_bit(r_rise_o, c_rise_o, arfu_rise_o);
assign apar_fall_o = ca_parity_bit(r_fall_o, c_fall_o, arfu_fall_o);
```

**`ARFU`를 빼먹으면 안 됩니다.** 진리표에 없어 존재를 놓치기 쉽지만 패리티 계산에는 참여합니다([06장](../06_row_commands/)).

### 5.2 `AERR` 감시와 커맨드 이력 대조

패리티가 커맨드를 막지 않으므로, 컨트롤러가 **무엇이 잘못 실행되었는지 추정**해야 합니다.

```systemverilog
// AERR는 tPARAC 후에 1 tCK HIGH. 어느 버스에서 났는지는 알 수 없다 (§6.4.1)
// 발행 이력을 tPARAC 깊이로 보관해 두고 역추적한다.
localparam int HIST_DEPTH = T_PARAC + 2;
cmd_record_t cmd_hist_q [HIST_DEPTH];

always_ff @(posedge ck) begin
  cmd_hist_q[0] <= current_cmd;
  for (int i = 1; i < HIST_DEPTH; i++) cmd_hist_q[i] <= cmd_hist_q[i-1];

  if (aerr_i) begin
    suspect_cmd_q  <= cmd_hist_q[T_PARAC];   // 의심 커맨드
    ca_err_count_q <= ca_err_count_q + 1'b1;
    // 해당 뱅크/PC의 상태를 신뢰할 수 없음으로 표시 -> 재동기화 필요
    bank_state_suspect_q[cmd_hist_q[T_PARAC].bank] <= 1'b1;
  end
end
```

**핵심**: 커맨드가 실행되었으므로 **뱅크 상태 모델이 오염**되었을 수 있습니다. 안전한 복구는 해당 뱅크를 precharge해 알려진 상태로 되돌리는 것입니다.

### 5.3 데이터 패리티 — 대상 집합이 동적이다

```systemverilog
// 대상 집합이 MD와 DBI 설정에 의존한다 (Table 47)
// SEV는 어떤 경우에도 포함되지 않는다.
function automatic logic dword_parity(
    input logic [31:0] dq, input logic [1:0] ecc, input logic [3:0] dbi,
    input logic md_en,      input logic dbi_en);
  logic p = ^dq;
  if (md_en)  p ^= ^ecc;
  if (dbi_en) p ^= ^dbi;
  return p;
endfunction

wire md_en_w  = mr_q[9][0];        // MR9 OP0
wire wdbi_en  = mr_q[0][1];        // MR0 OP1
wire rdbi_en  = mr_q[0][0];        // MR0 OP0

assign dpar0_o = dword_parity(dq_o[31:0],  ecc_o[1:0], dbi_o[3:0], md_en_w, wdbi_en);
assign dpar1_o = dword_parity(dq_o[63:32], ecc_o[3:2], dbi_o[7:4], md_en_w, wdbi_en);
```

### 5.4 `PL` 지연과 스트로브 연장

```systemverilog
// DPAR은 데이터보다 PL 사이클 늦게 오간다 (§6.4.2)
// 그만큼 스트로브를 더 토글해야 하며, 추가량은 짝수여야 한다.
wire [2:0] pl = mr_q[1][7:5];

// 데이터 토글 + DPAR 래치용 추가 토글
wire [7:0] wdqs_pulses_total = WDQS_PRE_WR + DATA_PULSES + wdqs_extra_for_pl(pl) + WDQS_PST_WR;

`ifndef SYNTHESIS
  a_pl_extra_even: assert property (@(posedge ck) disable iff (!rst_n)
    (wdqs_pulses_total % 2 == 0))
    else $error("PL extension broke WDQS even-toggle invariant");
`endif
```

`PL`을 바꾸면 시퀀스 길이가 바뀌므로, [05장](../05_clocking_dbi/)의 **짝수 불변식 검사에 `PL`을 반영**해야 합니다.

### 5.5 Write 재시도 버퍼

차단이 없으므로 재시도는 컨트롤러 몫입니다.

```systemverilog
// DERR 보고 시점까지 write 데이터를 보관한다 (§6.4.2)
// 깊이 = WL + PL + tPARDQ 를 덮을 만큼
localparam int WR_RETRY_DEPTH = WL_MAX + PL_MAX + T_PARDQ + 2;
wr_entry_t wr_retry_q [WR_RETRY_DEPTH];

always_ff @(posedge ck) begin
  if (derr_i && !in_wdqs2ck_training)         // 트레이닝 중이면 패리티 오류가 아니다
    retry_req_q <= wr_retry_q[T_PARDQ_IDX];
end
```

**`in_wdqs2ck_training` 게이팅을 빠뜨리면** 트레이닝 중 위상 검출기 출력을 패리티 오류로 오인해 존재하지 않는 재시도를 발생시킵니다.

### 5.6 비활성화 게이팅

```systemverilog
// 세 기능이 각각 다른 대기 조건을 갖는다 (§6.4.1, §6.4.2)
wire capar_disable_ok = (since_last_access >= T_PARAC);
wire wpar_disable_ok  = (since_last_write  >= (wl_q + pl + T_PARDQ + 2));
wire rpar_disable_ok  = (since_last_read   >= T_RDMRS);
```

## 6. 대표 문제 — dry-run

### 문제 1 — CA 패리티 계산

> `R[9:0] = 10'b0110100010`, `C[7:0] = 8'b11000101`, `ARFU = 1`일 때 `APAR`에 실어야 할 값은?

<details>
<summary>풀이</summary>

HIGH의 개수를 센다.
```
R[9:0] = 0110100010 → 1의 개수 = 4
C[7:0] = 11000101   → 1의 개수 = 4
ARFU   = 1          → 1
─────────────────────────────────
합계                = 9  (홀수)
```

`AERR`가 LOW가 되려면 **`APAR`을 포함한 전체 합이 짝수**여야 한다. 현재 9(홀수)이므로 **`APAR = 1`** 을 실어 10(짝수)으로 만든다.

**확인**: 만약 `APAR = 0`을 실으면 합이 9로 홀수 → `AERR` HIGH → 패리티 오류로 보고된다. **다만 커맨드는 그대로 실행된다**(§6.4.1).
</details>

### 문제 2 — 패리티 대상 집합 불일치

> 컨트롤러가 `MR9`의 `MD`를 비활성화하는 MRS를 발행했다. 그런데 패리티 생성 로직은 여전히 `ECC` 비트를 포함해 계산하고 있다. 무슨 일이 생기는가?

<details>
<summary>풀이</summary>

**정상 데이터에서 패리티 오류가 발생한다.**

`MD`가 비활성이면 장치는 **`ECC` I/O를 패리티 검사에서 제외**한다(Table 47). 컨트롤러가 여전히 `ECC`를 넣어 `DPAR`을 계산하면, `ECC` 비트의 패리티가 홀수일 때마다 계산 결과가 어긋나 **`DERR`가 뜬다.**

**진단이 어려운 이유**: 데이터는 실제로 멀쩡하다. write는 정상 완료되고(차단 없음), 나중에 읽어보면 값이 맞다. 그런데 `DERR`만 계속 뜬다. 데이터 경로를 아무리 뒤져도 원인이 안 나온다.

**설계 결론**: 패리티 로직은 `WDBI`·`RDBI`·`MD` 세 비트를 **런타임 입력**으로 받아야 한다. 그리고 이 비트들을 바꾸는 MRS 전후로 **패리티를 잠시 비활성화**하고 `tMOD` 후 재활성화하는 편이 안전하다.
</details>

### 문제 3 — `DERR` 오인

> WDQS-to-CK 정렬 트레이닝 중에 `DERR0`가 HIGH로 관측됐다. 컨트롤러가 write 재시도를 시작했다. 올바른가?

<details>
<summary>풀이</summary>

**틀렸다.** 트레이닝 모드(`MR8` OP3 = 1)에서 `DERR`는 **패리티 오류가 아니라 위상 검출기 판독**이다([05장](../05_clocking_dbi/), Table 31).

`DERR0` HIGH는 *"내부 `WDQS/2`의 0° 위상이 CK로 샘플링했을 때 HIGH → WDQS가 **early**"* 를 뜻하며, **권장 조치는 WDQS 지연을 늘리는 것**이다.

**설계 결론**: `DERR` 해석 로직은 **모드에 따라 분기**해야 한다.

```
MR8 OP3 == 1  →  위상 검출기 판독 (early/late)
MR8 OP3 == 0  →  데이터 패리티 오류
```

게다가 트레이닝 모드에서는 애초에 write 버스트가 진행 중이지 않으므로, 재시도할 대상 자체가 없다. 이 오인은 **존재하지 않는 트랜잭션의 재시도**를 만들어 컨트롤러 상태를 망가뜨린다.
</details>

## 🔍 검증 연결

- `AERR`/`DERR`가 뜨는 시나리오를 의도적으로 만드는 에러 주입 → [`hbm_dv` Ch08 시나리오](../../hbm_dv/08_testcase_scenarios/)
- 패리티 오류가 데이터 비교를 통과하는 문제 → [`hbm_dv` Ch09 Assertion·Checker](../../hbm_dv/09_assertion_checker/)
- 설정 조합(MD·DBI·PL)을 coverage 축으로 → [`hbm_dv` Ch10 Coverage·회귀](../../hbm_dv/10_coverage_regression/)

## 핵심 정리

- CA parity 대상은 **`R[9:0]` + `C[7:0]` + `ARFU` + `APAR`**, **짝수 패리티**, **상승·하강 에지 각각** 계산된다. **`ARFU`를 빼면 안 된다.**
- ⚠️ **패리티는 검출 전용이다.** CA 오류가 나도 **커맨드는 실행**되고, data 오류가 나도 **write는 배열까지 완료**된다. 차단하지 않는다.
- 차단하지 않는 것은 **버스트에 중단·절단이 없다**는 모델의 일관된 귀결이다. 복구는 호스트 몫이다.
- **`AERR`만으로는 row/column 어느 버스인지 구별할 수 없다.** 커맨드 이력과 대조해야 한다.
- 패리티 활성화는 **"MRS 다음 사이클 ~ `tMOD` 만료" 사이 어디선가** 일어난다 — 정확한 시점이 규정되지 않으므로 **즉시 올바른 패리티를 실어야** 안전하다.
- data parity는 **계산은 UI 단위, 보고는 반 버스트(4 UI) 단위**다. 첫 사이클 오류의 `tPARDQ`는 `(WL + PL)` 후에 시작한다.
- **`PL`은 데이터와 `DPAR`을 어긋나게** 해 계산 여유를 만든다. 대가로 **추가 스트로브 토글**이 필요하며, 그 추가량도 **짝수**로 설계되어 있다(`PL=2` → 4펄스).
- **패리티 대상 집합은 고정이 아니다.** DBI는 `WDBI`/`RDBI`, ECC는 `MR9`의 `MD`에 의존한다. **`SEV`는 언제나 제외**다.
- 비활성화 금지 구간이 셋 다 다르다 — `CAPAR`은 `tPARAC`, `WPAR`은 `WL+PL+tPARDQ+2tCK`, `RPAR`은 `tRDMRS`.
- **`DERR`는 두 얼굴을 갖는다** — 일반 동작에서는 패리티 오류, WDQS-to-CK 트레이닝에서는 위상 검출기 판독이다.

## Further Reading

- **규격**: JESD270-4 §6.4.1 Command/Address Parity (Table 46, Figure 61–64) · §6.4.2 Data Parity (Table 47, Figure 65–69)
- **다음 장**: [09 — On-die ECC · ECS · SEV](../09_ecc_ecs_sev/)
- **관련**: [04 — Mode Register](../04_mode_registers/) (`MR0`·`MR1`·`MR9`) · [05 — 클럭킹](../05_clocking_dbi/) (`DERR`의 다른 용도) · [06 — Row 커맨드](../06_row_commands/) (`ARFU`)
- **이해도 점검**: [퀴즈](../quiz/08_parity_quiz/)
