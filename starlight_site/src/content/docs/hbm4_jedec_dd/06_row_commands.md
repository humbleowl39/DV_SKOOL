---
title: "06 — Row 커맨드와 Refresh 다섯 갈래"
description: JESD270-4 §6.3.1–6.3.2 · 커맨드 인코딩, 반주기 패딩 규칙, HBM4 고유 라운딩 공식, REFab/REFpb/RFM/ARFM/DRFM
---

:::tip[🎯 Learning Objectives]
이 모듈을 마치면:

- **Decode** row 커맨드 인코딩에서 opcode·PC·SID·BA·RA 필드의 배치를 읽어낸다.
- **Apply** HBM4 고유의 라운딩 공식 `nXX = 0.5 × RU(2·tXX/tCK)` 로 커맨드 슬롯을 계산한다.
- **Differentiate** REFab · REFpb · RFM · ARFM · DRFM 다섯 갈래의 목적과 RAA 카운터에 대한 효과를 구분한다.
- **Design** RAA(Rolling Accumulated ACTIVATE) 카운터와 DRFM 주소 레지스터를 RTL로 설계한다.
- **Evaluate** `DEVICE_ID`의 RFM/ARFM 비트와 `MR8` 레벨 조합에서 불법 설정을 판정한다.
:::

:::note[Prerequisites]
- [02 — 주소 체계와 뱅크 그룹](../02_addressing_bank_groups/) — `{SID, BA}` 뱅크 인덱스
- [04 — Mode Register](../04_mode_registers/) — `MR0` OP3(DRFM), `MR8` OP[5:4](RFM Level)
- [05 — 클럭킹과 DBIac](../05_clocking_dbi/) — DDR 커맨드와 반주기 개념
:::

:::caution[인용 고지]
본 장은 **JESD270-4 (2025-04, WIP draft)** §6.3.1–§6.3.2를 근거로 **요약·재구성**한 것입니다. 진리표(Table 33)와 그림은 옮기지 않고 **구조와 규칙만** 서술합니다. 정밀 인코딩은 **JEDEC 원문 우선**.
:::

---

## 1. 커맨드 인코딩의 구조

### 반주기 단위 체계

§6.3의 첫 문단이 [01장](../01_landscape_organization/)에서 본 사이클 규정을 다시 확인합니다 — 커맨드는 **CK의 양쪽 에지에서 입력**되며, ACTIVATE는 1.5 사이클, 그 외 row 커맨드는 반 사이클, PDE·SRE는 1 사이클, column 커맨드는 1 사이클입니다.

그리고 진리표에는 나오지 않는 신호가 하나 언급됩니다.

> 커맨드 인터페이스는 **예약된 DDR 입력 신호 `ARFU`** 를 포함하며, 이는 후속 진리표에서 생략되지만 **다른 AWORD 입력들과 함께 유효한 신호 레벨로 구동되어야 한다.** — §6.3

**진리표에 없다고 구동하지 않아도 되는 것이 아닙니다.** 이런 항목은 진리표만 보고 구현하면 놓칩니다.

### Row 커맨드 필드 배치

Table 33의 구조를 필드 관점으로 정리하면 이렇습니다.

| 영역 | 신호 | 역할 |
|---|---|---|
| opcode | `R[3:0]` 중 앞부분 | 커맨드 종류 구분 |
| PC 선택 | `R3` (대부분의 커맨드) | PC0/PC1 지정 |
| 뱅크 | `R[9:4]` — `SID0`·`SID1`·`BA[3:0]` | ACT·PREpb·REFpb·RFMpb에서 사용 |
| 행 주소 | 두 번째·세 번째 반주기의 `R[9:2]` | ACT 전용 |

ACTIVATE는 세 개의 반주기에 걸쳐 정보를 나릅니다 — **첫 상승 에지**에 opcode+PC+SID+BA, **하강 에지**에 `RA[14:8]`과 **DRFM 비트**, **다음 상승 에지**에 `RA[7:0]`.

### 진리표 주석에서 나오는 설계 제약

Table 33의 주석 11개 중 설계에 직접 닿는 것들입니다.

**PC 선택의 의미** (Note 5)
> `PC = 0`은 PC0을, `PC = 1`은 PC1을 선택한다. **PC로 선택되지 않은 pseudo channel은 RNOP를 수행한다.**

즉 커맨드는 항상 두 PC 모두에 도달하며, 선택되지 않은 쪽은 자동으로 NOP가 됩니다. 커맨드 버스가 공유이기 때문입니다([01장](../01_landscape_organization/)).

**SID의 사용 범위** (Note 6)
> `SID` 비트는 **`ACT`·`PREpb`·`REFpb`·`RFMpb`와 함께 뱅크 주소 비트로 동작**하며, 관련 타이밍 다이어그램도 그에 따라 해석되어야 한다. **그 외 row 커맨드는 SID를 사용하지 않는다.**

[02장](../02_addressing_bank_groups/)에서 확인한 "SID는 뱅크 주소 확장 비트"가 여기서 **커맨드별로 한정**됩니다. `PREab`·`REFab`·`RFMab`처럼 all-bank 커맨드는 SID를 쓰지 않습니다 — 당연합니다, 전체를 대상으로 하니까요.

**미정의 비트도 구동해야 한다** (Note 2)
> **특정 밀도에서 `SID`나 `RA`가 정의되지 않더라도 `R[9:0]`은 유효한 신호 레벨로 구동되어야 한다.** `APAR`은 **`MR0` OP6에서 CA parity가 비활성이더라도** 유효한 신호 레벨로 구동되어야 한다.

4-high 구성이라 `SID`가 없어도 그 핀을 띄워두면 안 됩니다. parity를 끄더라도 `APAR`은 구동해야 합니다.

**패리티는 모든 핀에서 평가된다** (Note 3) — CA parity가 켜지면 일부가 아니라 **전체 핀**이 대상입니다 → [08장](../08_parity/).

**PDX/SRX에서는 패리티를 검사하지 않는다** (Note 8)
> Power-Down Exit 또는 Self Refresh Exit에서는 **패리티가 검사되지 않는다.** CA parity가 활성이면 장치는 power-down exit 기간(`tXP`)과 self refresh exit 기간(`tXS`) 동안 row·column 버스에 각각 **유효한 패리티를 갖는 RNOP와 CNOP**를 요구한다.

검사는 안 하지만 **유효한 값은 요구**합니다. 미묘한 구분입니다.

**ACT 이후 슬롯 제약** (Note 9)
> ACT는 1.5 사이클 커맨드다. **ACT 커맨드에 이어 두 번째 사이클의 하강 에지에서 허용되는 것은 RNOP, 다른 뱅크에 대한 `PREpb`, 또는 다른 PC에 대한 `PREab` 뿐이다.**

이것이 커맨드 스케줄러에 직접 반영해야 할 제약입니다.

**RFM 미요구 장치의 동작** (Note 7)
> refresh management를 요구하지 않는 HBM4 DRAM은 `RFMab`·`RFMpb` 대신 **`RNOP` 커맨드를 실행한다.**

오류가 아니라 **조용히 무시**됩니다.

## 2. RNOP — 패딩의 문법

`RNOP`는 `R[9:0]`에서 받는 반주기 커맨드로, **상승·하강 어느 에지에서든(또는 양쪽에서) 래치**됩니다(§6.3.2.1). 유휴·대기 상태에서 원치 않는 row 커맨드가 등록되는 것을 막는 것이 목적이며, **이미 진행 중인 동작에는 영향을 주지 않습니다.**

핵심은 **패딩 규칙**입니다.

> `RNOP` 이외의 row 커맨드는 반 사이클 또는 1.5 사이클 커맨드로 정의되며 **상승 CK 에지에서 시작하고 끝난다.** 이 커맨드들은 **같은 사이클의 하강 CK 에지에 `RNOP`로 패딩되어야 한다.** 대안으로 일부 row 커맨드는 하강 에지에 `RNOP` 대신 **`PREpb` 또는 `PREab`와 짝지어질 수 있으며**, 그 조건은 커맨드마다 명시된다. — §6.3.2.1 (요약)

즉 **하강 에지는 비워둘 수 없습니다.** `RNOP`로 채우거나 precharge를 끼워 넣거나 둘 중 하나입니다. 이 "빈 슬롯 활용"이 HBM4 커맨드 대역폭 설계의 특징입니다.

그리고 **`RNOP`에도 패리티가 평가**됩니다(mode register에서 활성인 경우).

## 3. ACTIVATE와 PRECHARGE

`ACTIVATE`는 뱅크와 행을 함께 선택해 행을 엽니다. 열린 뒤 `tRCD`를 만족하면 READ/WRITE를 발행할 수 있습니다(§6.3.2.2).

1.5 사이클 커맨드이므로 **두 번째 클럭 사이클의 하강 에지**를 어떻게 채울지가 문제이고, 규격은 세 가지만 허용합니다.

| 하강 에지 슬롯 | 조건 |
|---|---|
| `RNOP` | 항상 가능 |
| `PREpb` | **임의의 뱅크**에 대해 가능 (조건은 아래) |
| `PREab` | **반드시 다른 pseudo channel**에 대한 것이어야 함 |

`PREab`에 걸린 "다른 PC" 조건이 눈에 띕니다 — 방금 ACT로 연 PC에 all-bank precharge를 걸면 자기 자신을 닫는 셈이니 당연한 제약입니다.

## 4. 라운딩 규칙 — HBM4가 공식을 바꾼 이유

§6.3.2.4는 이 장에서 가장 HBM4다운 부분입니다.

### 전통적 공식과 그 한계

기존에는 아날로그 타이밍을 클럭 사이클로 이렇게 변환했습니다.

```
nXX = RU(tXX / tCK)          ← 다음 "상승" 에지로 올림
```

그런데 HBM4는 **`PREpb`와 `PREab`를 상승·하강 양쪽 에지에서 발행할 수 있게** 했습니다. 스케줄링 유연성이 생겼는데 라운딩 공식이 상승 에지만 가정하면 그 유연성을 쓸 수 없습니다.

### HBM4의 공식

```
nXX = 0.5 × RU(2 × tXX / tCK)     ← 다음 "상승 또는 하강" 에지로 올림
```

- 적용 대상은 **`tRAS`, `tRTP`, `tWR`, `tRP` 네 개뿐**입니다.
- 결과는 전통 공식과 **같거나 0.5 nCK 작습니다.**

그리고 예외가 하나 붙습니다.

> **`tRP` 라운딩 결과가 후속 row access 커맨드의 슬롯으로 하강 에지를 지목하면 결과에 0.5 nCK를 더해야 한다.** row precharge에 이어지는 그런 row 커맨드들은 **상승 에지에서만** 발행 가능하기 때문이다. — §6.3.2.4 (요약)

### 규격이 든 예

**예 1 — `tRAS`**

```
tRAS = 33 ns, tCK = 0.7 ns
nRAS = 0.5 × RU(2 × 33 / 0.7) = 0.5 × RU(94.29) = 0.5 × 95 = 47.5
```

→ `ACTIVATE`를 T0에 발행했다면 `PRECHARGE`의 가장 이른 슬롯은 **T47.5(하강 에지)**.

전통 공식이라면 `RU(33/0.7) = RU(47.14) = 48`이 되어 **0.5 사이클을 손해** 봤을 것입니다.

**예 2 — `tRP`와 예외 규칙**

```
tRP = 15 ns, tCK = 0.7 ns
nRP = 0.5 × RU(2 × 15 / 0.7) = 0.5 × RU(42.85) = 0.5 × 43 = 21.5
```

→ `PREpb`를 **T0(상승)** 에 발행하면 T21.5는 하강 에지인데 `ACTIVATE`는 상승 에지에서만 가능하므로 **0.5를 더해 T22**.
→ 같은 `PREpb`를 **T0.5(하강)** 에 발행하면 `0.5 + 21.5 = T22`로 **이미 상승 에지**여서 보정이 필요 없습니다.

:::tip[여기서 얻는 것]
같은 `tRP`인데 **precharge를 하강 에지에 발행하면 후속 ACTIVATE 시점이 같거나 빨라집니다.** 스케줄러가 precharge를 어느 에지에 놓는지가 성능에 반영된다는 뜻이고, HBM4가 공식을 바꾼 이유가 여기 있습니다.

**함정**: 전통 공식을 그대로 쓰면 규격 위반은 아니지만(항상 같거나 더 보수적) **성능을 버립니다.** 반대로 새 공식을 쓰면서 `tRP` 예외를 빠뜨리면 **하강 에지에 ACTIVATE를 발행하는 규격 위반**이 됩니다.
:::

## 5. Refresh 다섯 갈래

§6.3.2.5는 refresh를 다섯 종류로 정의합니다. 목적이 서로 다르므로 하나로 뭉뚱그리면 안 됩니다.

| 커맨드 | 대상 | 목적 |
|---|---|---|
| **`REFab`** | 전 뱅크 | 주기적 전하 복원 |
| **`REFpb`** | 단일 뱅크 | 주기적 전하 복원 (뱅크 단위) |
| **`RFMab`** | 전 뱅크 | 내부 refresh 관리 시간 확보 |
| **`RFMpb`** | 단일 뱅크 | 동일 (뱅크 단위) |
| **`DRFMpb`** | 단일 뱅크 | **지정된 행의 물리적 인접 행** 복원 |

기본 성질도 규정되어 있습니다 — REFRESH 커맨드는 **비지속적(non-persistent)** 이라 필요할 때마다 발행해야 하고, **평균 주기 `tREFI`** 간격으로 발행되어야 합니다.

### RFM과 RAA 카운터

RFM은 refresh 자체가 아니라 **장치가 내부적으로 refresh를 관리할 시간을 주는 것**입니다. 그 필요성을 판단하는 모델이 **RAA(Rolling Accumulated ACTIVATE) 카운트**입니다.

```
각 ACTIVATE  →  해당 뱅크의 RAA += 1
RAA ≥ RAAIMT →  추가 refresh 관리 필요
RFM 발행     →  해당 뱅크(들)의 RAA -= RAAIMT  (하한 0)
REF 발행     →  해당 뱅크(들)의 RAA -= RAADEC
RAA = RAAMMT →  그 뱅크에 ACTIVATE 발행 금지
```

세 개의 문턱값은 모두 **벤더 지정**이며 **`DEVICE_ID` WDR에서 읽습니다**(Table 134).

| 값 | 의미 | 출처 |
|---|---|---|
| `RAAIMT` | Initial Management Threshold — RFM이 필요해지는 지점 | `DEVICE_ID` WDR |
| `RAAMMT` | Maximum Management Threshold — ACTIVATE 금지 지점 | `DEVICE_ID` WDR |
| `RAADEC` | REF 커맨드당 감소량 | `DEVICE_ID` WDR |

:::caution[RFM에 대한 네 가지 오해]
1. **"RFM이 REF를 대신한다"** — 아닙니다. *"RFM 커맨드는 컨트롤러가 주기적 REF 커맨드를 발행할 요구를 대체하지 않으며, 내부 refresh 카운터에도 영향을 주지 않는다"*(§6.3.2.5.3). RFM은 **보너스 시간**입니다.
2. **"RAA를 음수로 만들어 미리 벌어둘 수 있다"** — 아닙니다. 감소는 **하한 0**이며 *"음수나 RFM 커맨드의 'pull-in'은 허용되지 않는다"*.
3. **"RFMpb도 REFpb처럼 전 뱅크를 순회해야 한다"** — 아닙니다. *"REFpb 커맨드를 전 뱅크에 rolling 방식으로 발행해야 하는 요구는 RFMpb에는 적용되지 않는다."*
4. **"self refresh에 들어갔다 나오면 RAA가 초기화된다"** — 조건부입니다. **`tRAASRF` 이상** 유지되어야 0으로 리셋되며, 그보다 짧으면 **진입·종료 자체로는 어떤 감소도 허용되지 않습니다.**
:::

스케줄링 제약은 REF와 같습니다 — `RFMab`은 `REFab`과 동일한 최소 분리 요건 및 `tRFCab` 주기, `RFMpb`는 `REFpb`와 동일한 `tRFCpb` 주기를 따릅니다.

### ARFM — 문턱값을 낮추는 선택지

`RAAIMT`·`RAAMMT`·`RAADEC`는 **읽기 전용**입니다. 그래서 컨트롤러는 장치가 정한 문턱을 그대로 따라야 하는데, **ARFM(Adaptive Refresh Management)** 이 그 경직성을 풉니다.

> ARFM 모드는 컨트롤러가 **추가적인(더 낮은) RFM 문턱 설정**인 "RFM Level"을 선택할 수 있게 한다. RFM 레벨은 컨트롤러가 발행하는 RFM 커맨드를 **DRAM 내부 관리와 정렬**할 수 있게 한다. — §6.3.2.5.4 (요약)

레벨은 **`MR8` OP[5:4]** 로 선택하고, 지원 여부는 `DEVICE_ID` WDR의 **`ARFM` 비트**로 알립니다.

### 무엇이 실행되는가 — 조합 판정

Table 40이 `DEVICE_ID`의 두 비트와 `MR8` 레벨의 조합에 따라 장치가 커맨드를 **어떻게 인식하는지**를 정의합니다.

| `RFM` 비트 | `ARFM` 비트 | `MR8` OP[5:4] | 장치가 인식하는 것 |
|---|---|---|---|
| 0 (RFM 불필요) | 0 (ARFM 미지원) | `00` | **RNOP** |
| 0 | 0 | `01`/`10`/`11` | ⚠️ **Illegal** |
| 0 | 1 (ARFM 지원) | `00` | **RNOP** |
| 0 | 1 | `01`/`10`/`11` | `RFMab`/`RFMpb` |
| 1 (RFM 필요) | 0 | `00` | `RFMab`/`RFMpb` |
| 1 | 0 | `01`/`10`/`11` | ⚠️ **Illegal** |
| 1 | 1 | 전부 | `RFMab`/`RFMpb` |

두 가지가 읽힙니다.

- **Illegal 조건의 근거** (Note 1): ARFM을 지원하지 않는 장치는 `MR8` OP[5:4]를 **RFU로 정의**하므로 유일하게 허용되는 설정이 `00`입니다. RFU 비트는 0으로 프로그램해야 한다는 [04장](../04_mode_registers/)의 규칙과 일치합니다.
- **ARFM의 숨은 용도** (Note 2): *"Adaptive RFM은 `RFM = 0`(RFM 불필요)으로 출하된 HBM4 DRAM이 초기 설정을 **재정의(override)** 하고 비기본 RFM 레벨을 프로그램해 Adaptive RFM을 활성화할 수 있게 한다."* 즉 **RFM이 필요 없다고 표시된 장치에서도 RFM을 켤 수 있습니다.**

### DRFM — 지정된 행의 이웃을 복원한다

DRFM은 컨트롤러에게 **데이터 무결성 유지의 추가 수단**을 줍니다(§6.3.2.5.5). 동작은 2단계입니다.

```
① ACT (DRFM 비트 = 1)
     → 행을 열고, 동시에 그 행 주소를 캡처
② RFMpb (같은 뱅크)  ≡ DRFMpb
     → 캡처된 주소의 물리적 인접 이웃 행들을 refresh
```

**기본값은 Disabled**이며 `MR0` OP3으로 켭니다([04장](../04_mode_registers/)).

설계에 직결되는 성질 셋:

1. **각 뱅크가 독립적인 DRFM 주소 레지스터**를 갖습니다. 갱신될 때마다 덮어써서 **가장 최근 샘플만** 유지됩니다.
2. **`DRFMpb`는 RAA 카운트를 감소시키지 않습니다.** RFM 요구사항에 대해 **보충적(supplemental)** 이며, 일반 RFM의 대체재가 아닙니다.
3. **유효한 주소 샘플이 없는 뱅크에 `RFMpb`를 발행하면 일반 `RFMpb`로 실행**됩니다. 즉 같은 커맨드가 문맥에 따라 다르게 동작합니다.

:::tip[왜 "이웃 행"인가]
행 하나를 반복 활성화하면 물리적으로 인접한 행의 전하가 교란됩니다. DRFM은 **교란원이 될 행을 컨트롤러가 지목**하고 그 주변을 선제 복원하는 구조입니다.

`RFM`이 *"활성화가 많으니 알아서 관리할 시간을 주겠다"* 는 **통계적** 접근이라면, `DRFM`은 *"이 행이 문제다"* 라고 **지목**하는 접근입니다. 둘은 대체 관계가 아니라 **보완 관계**이고, 그래서 DRFM이 RAA를 깎지 않습니다.
:::

## ⚙️ 설계 적용 (RTL / Front-end)

### 6.1 커맨드 디코더 — 반주기 파이프라인

ACT가 3개 반주기에 걸치므로 디코더는 **반주기 단위 상태**를 가져야 합니다.

```systemverilog
// R[9:0]을 CK 양 에지에서 캡처한다 (§6.3)
typedef enum logic [1:0] { CMD_IDLE, CMD_ACT_F, CMD_ACT_R2 } row_dec_e;

always_ff @(posedge ck) begin  // 상승 에지 슬롯
  unique case (dec_q)
    CMD_IDLE: if (is_act(r_rise)) begin
      act_pc_q  <= r_rise[3];
      act_sid_q <= r_rise[5:4];
      act_ba_q  <= r_rise[9:6];
      dec_q     <= CMD_ACT_F;
    end
    CMD_ACT_R2: begin
      act_ra_q[7:0] <= r_rise[9:2];        // 세 번째 반주기
      act_valid_q   <= 1'b1;
      dec_q         <= CMD_IDLE;
    end
    default: ;
  endcase
end

always_ff @(negedge ck) begin  // 하강 에지 슬롯
  if (dec_q == CMD_ACT_F) begin
    act_ra_q[14:8] <= r_fall[8:2];         // 두 번째 반주기
    act_drfm_q     <= r_fall[9];           // DRFM 비트
    dec_q          <= CMD_ACT_R2;
  end
end
```

### 6.2 ACT 후속 슬롯 제약 검사

Note 9의 제약을 스케줄러 게이팅으로 옮깁니다.

```systemverilog
// ACT 두 번째 사이클의 하강 에지에는 RNOP / 다른 뱅크 PREpb / 다른 PC PREab 만 허용 (Table 33 Note 9)
wire in_act_second_fall = (dec_q == CMD_ACT_F);

wire slot_ok = (fall_cmd == CMD_RNOP)
             | ((fall_cmd == CMD_PREPB) && ({fall_sid, fall_ba} != {act_sid_q, act_ba_q}))
             | ((fall_cmd == CMD_PREAB) && (fall_pc != act_pc_q));

`ifndef SYNTHESIS
  a_act_fall_slot: assert property (@(negedge ck) disable iff (!rst_n)
    in_act_second_fall |-> slot_ok)
    else $error("Illegal command in ACT second-cycle falling slot");
`endif
```

### 6.3 라운딩 공식

```systemverilog
// HBM4 라운딩: 상승/하강 양쪽 에지를 슬롯으로 인정한다 (§6.3.2.4)
// 반환값 단위는 "반 사이클"이다 — 0.5 nCK를 정수로 다루기 위해.
function automatic int hbm4_round_half(input int t_ps, input int tck_ps);
  return (2*t_ps + tck_ps - 1) / tck_ps;    // = RU(2·t/tCK), 단위: 반 사이클
endfunction

localparam int N_RAS_HALF = hbm4_round_half(T_RAS_PS, T_CK_PS);
localparam int N_RTP_HALF = hbm4_round_half(T_RTP_PS, T_CK_PS);
localparam int N_WR_HALF  = hbm4_round_half(T_WR_PS,  T_CK_PS);
localparam int N_RP_HALF  = hbm4_round_half(T_RP_PS,  T_CK_PS);

// tRP 예외: 결과 슬롯이 하강 에지(홀수 반사이클)이면 상승 에지로 올린다 (§6.3.2.4)
// precharge 발행 에지에 따라 최종 위치가 달라지므로 발행 시점 패리티를 함께 본다.
function automatic int rp_slot_half(input int issue_half);  // issue_half: 짝수=상승, 홀수=하강
  int s = issue_half + N_RP_HALF;
  return (s % 2 == 0) ? s : s + 1;          // 하강이면 +0.5 nCK
endfunction
```

**단위를 반 사이클 정수로 다루는 것**이 요령입니다. 0.5를 실수로 다루면 합성이 안 되고 비교도 부정확해집니다.

### 6.4 RAA 카운터

뱅크마다 한 벌입니다.

```systemverilog
// RAA는 뱅크별 (§6.3.2.5.3). 문턱값은 DEVICE_ID WDR에서 읽어온 런타임 값이다.
logic [RAA_W-1:0] raa_q [NUM_BANKS];

always_ff @(posedge ck) begin
  for (int b = 0; b < NUM_BANKS; b++) begin
    if (sref_held_ge_trasrf)                       // tRAASRF 이상 유지 시에만 리셋
      raa_q[b] <= '0;
    else if (act_valid && (act_bank == b))
      raa_q[b] <= raa_q[b] + 1'b1;
    else if (rfm_hit(b))                           // RFMab: 전 뱅크 / RFMpb: 선택 뱅크
      raa_q[b] <= (raa_q[b] > raaimt) ? raa_q[b] - raaimt : '0;   // 하한 0
    else if (ref_hit(b))                           // REFab / REFpb
      raa_q[b] <= (raa_q[b] > raadec) ? raa_q[b] - raadec : '0;
  end
end

// RAAMMT 도달 시 그 뱅크에 ACTIVATE 금지
wire act_blocked = (raa_q[req_bank] >= raammt);
```

**세 가지를 지켜야 합니다.**

1. 감소는 **하한 0** — 언더플로로 음수를 만들면 "pull-in"이 되어 규격 위반입니다.
2. self refresh 리셋은 **`tRAASRF` 이상 유지된 경우만**. 진입·종료 자체로는 감소하지 않습니다.
3. 문턱값은 **컴파일 상수가 아니라 런타임 값**입니다 — `DEVICE_ID` WDR에서 읽어야 하므로 IEEE 1500 경로가 부팅 시퀀스에 포함되어야 합니다([11장](../11_training_ieee1500/)).

### 6.5 DRFM 주소 레지스터

```systemverilog
// 뱅크마다 독립적인 DRFM 주소 레지스터. 최신 샘플만 유지된다 (§6.3.2.5.5)
logic [RA_W-1:0] drfm_addr_q  [NUM_BANKS];
logic            drfm_valid_q [NUM_BANKS];

always_ff @(posedge ck) begin
  if (act_valid && act_drfm_q && drfm_enabled) begin
    drfm_addr_q [act_bank] <= act_ra_q;      // 덮어쓰기 — 최신 것만 남는다
    drfm_valid_q[act_bank] <= 1'b1;
  end
  if (rfmpb_valid && drfm_valid_q[rfm_bank])
    drfm_valid_q[rfm_bank] <= 1'b0;          // 서비스 후 소진
end

// 유효 샘플이 없으면 일반 RFMpb로 동작 -> RAA 감소가 적용된다
wire is_drfmpb = rfmpb_valid && drfm_valid_q[rfm_bank];
wire raa_dec_allowed = rfmpb_valid && !is_drfmpb;
```

**핵심**: 같은 `RFMpb` 커맨드가 유효 샘플 유무에 따라 **DRFMpb** 또는 **일반 RFMpb**로 갈리고, **RAA 감소 여부가 그에 따라 달라집니다.** 이 분기를 놓치면 RAA 추적이 장치와 어긋납니다.

## 7. 대표 문제 — dry-run

### 문제 1 — 라운딩 계산

> `tRP = 12 ns`, `tCK = 0.5 ns`다. `PREpb`를 T0(상승 에지)에 발행했을 때 후속 `ACTIVATE`의 가장 이른 슬롯은?

<details>
<summary>풀이</summary>

```
nRP = 0.5 × RU(2 × 12 / 0.5) = 0.5 × RU(48) = 0.5 × 48 = 24.0
```

T0 + 24.0 = **T24 (상승 에지)** — 정수이므로 하강 에지가 아니다. **예외 규칙 적용 불필요.**

**대조**: 만약 `tRP = 12.1 ns`였다면
```
nRP = 0.5 × RU(2 × 12.1 / 0.5) = 0.5 × RU(48.4) = 0.5 × 49 = 24.5
```
T24.5는 하강 에지이고 `ACTIVATE`는 상승 에지 전용이므로 **+0.5 → T25**.

**설계 함의**: 아날로그 값이 조금만 달라져도 예외 규칙 적용 여부가 갈린다. 라운딩 로직에 예외를 넣지 않으면 특정 타이밍 조합에서만 위반이 나며, 재현이 어렵다.
</details>

### 문제 2 — RFM 설정 조합

> `DEVICE_ID`를 읽으니 `RFM = 1`, `ARFM = 0`이었다. 컨트롤러가 `MR8` OP[5:4]에 `10`을 프로그램하면?

<details>
<summary>풀이</summary>

Table 40에서 `RFM=1, ARFM=0, level=10`은 **Illegal**이다.

**근거**(Note 1): ARFM을 지원하지 않는 장치는 `MR8` OP[5:4]를 **RFU로 정의**하므로 유일하게 허용되는 값은 `00`이다. [04장](../04_mode_registers/)의 "RFU 비트는 0으로 프로그램해야 한다"는 규칙과 같은 이야기다.

**올바른 동작**: `ARFM = 0`이면 `MR8` OP[5:4] = `00`으로 두고, `RAAIMT`/`RAAMMT`/`RAADEC`의 읽기 전용 값을 그대로 사용한다.

**설계 결론**: 부팅 시퀀스는 `DEVICE_ID`를 **먼저 읽고** 그 결과에 따라 `MR8` 값을 결정해야 한다. MR 이미지를 하드코딩하면 이 조합 검사를 건너뛰게 된다.
</details>

### 문제 3 — DRFM과 RAA

> DRFM이 활성인 상태에서 뱅크 3에 `ACT`(DRFM=1) → `PRE` → `RFMpb`(뱅크 3)를 발행했다. 뱅크 3의 RAA 카운트는 어떻게 변하는가?

<details>
<summary>풀이</summary>

```
ACT (DRFM=1)  →  RAA += 1,  그리고 행 주소를 뱅크 3의 DRFM 레지스터에 캡처
PRE           →  RAA 변화 없음
RFMpb (뱅크3) →  유효 샘플이 있으므로 DRFMpb로 실행
                  → 캡처된 행의 인접 행 refresh
                  → ⚠️ RAA 감소 없음
```

**최종: RAA는 순증 +1.**

**함정**: "RFM 커맨드를 보냈으니 RAA가 `RAAIMT`만큼 줄었겠지"라고 가정하면 컨트롤러의 RAA 추적이 장치와 어긋난다. 그 상태로 계속 ACTIVATE를 발행하면 장치 쪽 RAA가 먼저 `RAAMMT`에 도달해 **ACTIVATE가 거부**된다.

**설계 결론**: `RFMpb` 발행 시 그 뱅크의 DRFM 샘플 유효 여부를 함께 보고, **유효하면 RAA를 깎지 않아야** 한다. DRFM은 RFM의 **보충**이지 대체가 아니다.
</details>

## 🔍 검증 연결

- refresh 다섯 갈래를 coverage 축으로 분리 → [`hbm_dv` Ch10 Coverage·회귀](../../hbm_dv/10_coverage_regression/)
- 커맨드 슬롯 제약을 assertion으로 → [`hbm_dv` Ch09 Assertion·Checker](../../hbm_dv/09_assertion_checker/)
- RAA 문턱 도달 시나리오 작성 → [`hbm_dv` Ch08 시나리오](../../hbm_dv/08_testcase_scenarios/)

## 핵심 정리

- 진리표에 없는 **`ARFU`도 유효 레벨로 구동**해야 한다(§6.3). 진리표만 보고 구현하면 놓친다.
- **PC로 선택되지 않은 pseudo channel은 RNOP를 수행**한다(Note 5). 커맨드는 항상 양쪽에 도달한다.
- **SID는 `ACT`·`PREpb`·`REFpb`·`RFMpb`에서만** 뱅크 주소로 쓰인다(Note 6).
- 밀도상 정의되지 않는 `SID`/`RA` 핀도, parity를 꺼도 `APAR`도 **유효 레벨로 구동**해야 한다(Note 2).
- **PDX/SRX에서는 패리티를 검사하지 않지만** `tXP`·`tXS` 동안 **유효 패리티의 RNOP/CNOP를 요구**한다(Note 8).
- row 커맨드는 **하강 에지를 `RNOP`로 패딩**하거나 precharge로 채운다. ACT 두 번째 사이클 하강 슬롯에는 **RNOP / 다른 뱅크 PREpb / 다른 PC PREab**만 허용된다(Note 9).
- **라운딩 공식이 바뀌었다** — `nXX = 0.5 × RU(2·tXX/tCK)`, 대상은 **`tRAS`·`tRTP`·`tWR`·`tRP`**. `tRP` 결과가 하강 에지면 **+0.5**. 반 사이클 정수 단위로 구현하라.
- Refresh는 **다섯 갈래**다. `RFM`은 **REF를 대체하지 않고** 내부 관리 시간을 주는 **보너스**다.
- RAA는 뱅크별 카운터 — ACT +1, RFM −`RAAIMT`, REF −`RAADEC`, **하한 0**(pull-in 금지), `RAAMMT` 도달 시 **ACTIVATE 금지**. 문턱값은 **`DEVICE_ID` WDR에서 런타임에 읽는다.**
- self refresh로 RAA가 0이 되려면 **`tRAASRF` 이상 유지**되어야 한다.
- **ARFM**은 읽기 전용 문턱값의 경직성을 푼다. `ARFM` 미지원 장치에서 `MR8` OP[5:4]≠`00`은 **Illegal**이다.
- **DRFM은 지목형** refresh다. 뱅크별 주소 레지스터에 **최신 샘플만** 남고, **`DRFMpb`는 RAA를 감소시키지 않는다.** 유효 샘플이 없으면 같은 커맨드가 **일반 RFMpb**로 동작한다.

## Further Reading

- **규격**: JESD270-4 §6.3 Commands · §6.3.1 Truth Tables (Table 33–34) · §6.3.2 Row Commands (Figure 17–32) · §6.3.2.4 Rounding Rules · §6.3.2.5 Refresh (Table 38–40)
- **다음 장**: [07 — Column 커맨드와 저전력](../07_column_commands/)
- **관련**: [04 — Mode Register](../04_mode_registers/) (`MR0` DRFM, `MR8` RFM Level) · [11 — 트레이닝과 IEEE 1500](../11_training_ieee1500/) (`DEVICE_ID` WDR)
- **이해도 점검**: [퀴즈](../quiz/06_row_commands_quiz/)
