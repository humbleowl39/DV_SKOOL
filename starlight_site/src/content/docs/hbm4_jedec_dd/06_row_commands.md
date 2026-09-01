---
title: "06 — Row 커맨드와 Refresh 다섯 갈래"
description: JESD270-4 §6.3.1–6.3.2 · 문맥에 따라 달라지는 RFM, DEVICE_ID에서 오는 RAA 문턱, ACT 후속 슬롯 assertion
---

:::tip[🎯 Learning Objectives]
이 모듈을 마치면:

- **Decode** row 커맨드 인코딩에서 opcode·PC·SID·BA·RA 필드의 배치를 읽어낸다.
- **Apply** HBM4 고유의 라운딩 공식 `nXX = 0.5 × RU(2·tXX/tCK)` 로 커맨드 슬롯을 계산한다.
- **Differentiate** REFab · REFpb · RFM · ARFM · DRFM 다섯 갈래의 목적과 RAA 카운터에 대한 효과를 구분한다.
- **Construct** RAA shadow model을 만들고, 같은 `RFMpb`가 무효과·`DRFMpb`·일반 `RFMpb` 셋으로 갈리는 문맥을 반영한다.
- **Derive** RAA 문턱이 `DEVICE_ID`에서 오기 때문에 coverage bin을 **절대값이 아니라 문턱 대비 위치**로 잡아야 하는 이유를 도출한다.
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

### 진리표 주석에서 나오는 검증 항목

Table 33의 주석 11개 중 검증에 직접 닿는 것들입니다. 주석은 본문보다 검사 조건을 더 많이 담고 있습니다.

**PC 선택의 의미** (Note 5)
> `PC = 0`은 PC0을, `PC = 1`은 PC1을 선택한다. **PC로 선택되지 않은 pseudo channel은 RNOP를 수행한다.**

즉 커맨드는 항상 두 PC 모두에 도달하며, 선택되지 않은 쪽은 자동으로 NOP가 됩니다. 커맨드 버스가 공유이기 때문입니다([01장](../01_landscape_organization/)).

**SID의 사용 범위** (Note 6)
> `SID` 비트는 **`ACT`·`PREpb`·`REFpb`·`RFMpb`와 함께 뱅크 주소 비트로 동작**하며, 관련 타이밍 다이어그램도 그에 따라 해석되어야 한다. **그 외 row 커맨드는 SID를 사용하지 않는다.**

[02장](../02_addressing_bank_groups/)에서 확인한 "SID는 뱅크 주소 확장 비트"가 여기서 **커맨드별로 한정**됩니다. `PREab`·`REFab`·`RFMab`처럼 all-bank 커맨드는 SID를 쓰지 않습니다 — 당연합니다, 전체를 대상으로 하니까요.

**미정의 비트도 구동해야 한다** (Note 2)
> **특정 밀도에서 `SID`나 `RA`가 정의되지 않더라도 `R[9:0]`은 유효한 신호 레벨로 구동되어야 한다.** `APAR`은 **`MR0` OP6에서 CA parity가 비활성이더라도** 유효한 신호 레벨로 구동되어야 한다.

4-high 구성이라 `SID`가 없어도 그 핀을 띄워두면 안 됩니다. parity를 끄더라도 `APAR`은 구동해야 합니다. 이는 DUT가 아니라 **자극 측 검사 항목**입니다 — 시뮬레이션에서 `X`는 눈에 띄지만 실물에서는 미정의 동작이 됩니다.

**패리티는 모든 핀에서 평가된다** (Note 3) — CA parity가 켜지면 일부가 아니라 **전체 핀**이 대상입니다 → [08장](../08_parity/).

**PDX/SRX에서는 패리티를 검사하지 않는다** (Note 8)
> Power-Down Exit 또는 Self Refresh Exit에서는 **패리티가 검사되지 않는다.** CA parity가 활성이면 장치는 power-down exit 기간(`tXP`)과 self refresh exit 기간(`tXS`) 동안 row·column 버스에 각각 **유효한 패리티를 갖는 RNOP와 CNOP**를 요구한다.

검사는 안 하지만 **유효한 값은 요구**합니다. 미묘한 구분이고, 검사가 없으므로 위반해도 드러나지 않습니다 — 자극이 스스로 지켜야 하는 항목입니다.

**ACT 이후 슬롯 제약** (Note 9)
> ACT는 1.5 사이클 커맨드다. **ACT 커맨드에 이어 두 번째 사이클의 하강 에지에서 허용되는 것은 RNOP, 다른 뱅크에 대한 `PREpb`, 또는 다른 PC에 대한 `PREab` 뿐이다.**

이것이 assertion으로 옮겨야 할 제약입니다. 그런데 허용된 셋 중 `RNOP`만 자연히 나오므로, **나머지 둘은 자극이 의도적으로 만들지 않으면 미검증으로 남습니다** — 6.2 ①.

**RFM 미요구 장치의 동작** (Note 7)
> refresh management를 요구하지 않는 HBM4 DRAM은 `RFMab`·`RFMpb` 대신 **`RNOP` 커맨드를 실행한다.**

오류가 아니라 **조용히 무시**됩니다. 검증 환경이 이를 모르면 RAA를 깎아 놓고 실제 장치는 안 깎아서, 모델이 실제보다 낮은 RAA를 예측합니다 — 6.1절의 첫 번째 문맥 의존 사례입니다.

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

## 🔬 검증 적용

### 6.1 무엇이 깨질 수 있는가

이 장에는 **같은 커맨드가 문맥에 따라 다르게 실행되는** 경우가 둘 있습니다. 모델이 그 문맥을 따라가지 못하면, 커맨드는 정상 발행됐는데 이후 상태가 어긋납니다.

| 조문 | 위반 형태 | 증상 | 잡히는 시점 |
|---|---|---|---|
| Table 33 Note 7 — RFM 미요구 장치는 **`RNOP`을 실행** | 환경이 RFM이 먹혔다고 가정 | **오류 없이 조용히 무시.** RAA 모델이 실제와 갈림 | **없음** |
| §6.3.2.5.5 — 유효 샘플 없는 뱅크의 `RFMpb`는 **일반 `RFMpb`** | 모델이 뱅크별 샘플 유효를 추적 안 함 | 같은 커맨드를 다르게 해석 → RAA 어긋남 | 산발적 |
| Table 33 Note 9 — **ACT 후속 슬롯 3종만 허용** | 스케줄러가 다른 커맨드 배치 | 규격 위반이 **조용히** | **없음** |
| §6.3.2.1 — 하강 에지 **패딩 필수** | 슬롯을 비움 | 원치 않는 커맨드 등록 위험 | 간헐 |
| Table 33 Note 6 — SID는 **`ACT`·`PREpb`·`REFpb`·`RFMpb`에만** | all-bank 커맨드에도 SID 적용 | 잘못된 뱅크 대상 | scoreboard |
| Table 33 Note 2 — 미정의 `SID`/`RA`도 **유효 레벨 구동** | 자극이 `X`로 둠 | 시뮬은 `X` 전파로 보이지만 실물은 미정의 동작 | 시뮬에서만 |
| Table 33 Note 8 — PDX/SRX는 **검사 안 하되 유효값 요구** | 유효 패리티 없는 `RNOP` 발행 | 미묘 — 검사가 없어 안 드러남 | 없음 |
| §6.3.2.4 — HBM4 **0.5 해상도 라운딩** | 전통 공식(`RU(t/tCK)`) 사용 | 반 사이클씩 어긋난 기대값 | 마진 없는 조건 |
| §6.3.2.5.3 — RAA 감소는 **하한 0** | 모델이 음수 허용 | 문턱 판정이 어긋남 | RFM 집중 구간 |
| §6.3.2.5.3 — self refresh **`tRAASRF` 이상**일 때만 RAA 리셋 | 진입만 하면 리셋으로 처리 | RAA가 실제보다 낮게 예측됨 | SR 시나리오 |
| §6.3.2.5.5 — **`DRFMpb`는 RAA를 감소시키지 않는다** | 모델이 감소 처리 | 문턱 도달 시점 어긋남 | DRFM 켠 경우만 |
| Table 40 — **Illegal 조합 2행** | 자극이 불법 설정 생성 | unspecified | 없음 |

:::caution[기대값의 출처가 DUT 자신이다]
RAA 모델을 만들려면 세 문턱값이 필요합니다.

| 값 | 의미 | 출처 |
|---|---|---|
| `RAAIMT` | RFM이 필요해지는 지점 | **`DEVICE_ID` WDR** (Table 134) |
| `RAAMMT` | ACTIVATE 금지 지점 | **`DEVICE_ID` WDR** |
| `RAADEC` | REF 커맨드당 감소량 | **`DEVICE_ID` WDR** |

셋 다 **읽기 전용이고 벤더 지정**입니다. 곧 검증 환경이 **DUT에서 읽어 와야** 하는 값이며, 상수로 박으면 다른 장치·다른 구성에서 조용히 틀린 기준으로 판정합니다.

여기에 순환이 하나 있습니다 — `DEVICE_ID`는 **IEEE 1500 WDR**에 있고, IEEE1500 명령은 `tINIT3` 이후에만 쓸 수 있습니다([03장](../03_init_reset_power/)). 즉 **초기화가 어느 정도 진행되어야 RAA 모델을 구성할 수 있습니다.**

환경 구성 순서가 이렇게 됩니다.

```
reset → tINIT3 → IEEE1500 열기 → DEVICE_ID 읽기 → RAA 모델 구성 → MR 프로그램 → 트래픽
                                  └ 여기서 얻은 값으로 scoreboard 와 coverage bin 을 만든다
```

`build_phase`에서 covergroup의 bin 경계를 정하려 들면 이 값을 아직 모릅니다. **bin 경계가 런타임에 정해지는** 드문 경우이고, 대안은 상대값(`RAA/RAAIMT` 비율)으로 bin을 잡는 것입니다 — 6.3절.
:::

:::caution[같은 커맨드가 문맥에 따라 달라지는 두 경우]
**① RFM이 조용히 `RNOP`이 되는 경우** (Note 7)

`DEVICE_ID`의 `RFM` 비트가 0인 장치는 `RFMab`/`RFMpb`를 받아도 **`RNOP`을 실행**합니다. 오류를 내지 않습니다. 환경이 이를 모르면 RAA를 `RAAIMT`만큼 깎아 놓고, 실제 장치는 안 깎아서 **모델이 실제보다 낮은 RAA를 예측**합니다. 그 결과 `RAAMMT` 도달 시점이 어긋나고, ACTIVATE 금지 구간에서 ACT를 발행합니다.

**② `RFMpb`가 `DRFMpb`가 되는 경우** (§6.3.2.5.5)

같은 `RFMpb` 커맨드가, 그 뱅크에 **유효한 DRFM 주소 샘플이 있으면** `DRFMpb`로, 없으면 일반 `RFMpb`로 실행됩니다. 그리고 둘은 **RAA에 대한 효과가 반대**입니다 — 일반 `RFMpb`는 `RAAIMT`만큼 깎지만 `DRFMpb`는 깎지 않습니다.

모델은 **뱅크마다 "유효 샘플 있음" 플래그**를 들어야 합니다. 그 플래그는 `ACT`(DRFM 비트=1)에서 서고, `RFMpb` 소비 시 내려갑니다. 이 상태를 안 들면 RAA 예측이 뱅크별로 갈립니다.
:::

### 6.2 어떻게 잡는가 — 수단 선택

| 규칙 | 성격 | 수단 | 이유 |
|---|---|---|---|
| ACT 후속 슬롯 3종 (Note 9) | **국소 시간 규칙** | **SVA** | 인접 두 에지의 판정 |
| 하강 에지 패딩 | **불변식** | **SVA** | 모든 사이클에 성립 |
| RAA 카운트와 문턱 | **누적 상태** | **shadow model (뱅크별)** | 커맨드 이력 전체가 상태를 만든다 |
| 라운딩 공식 | **함수** | **reference 함수** | 기대값 계산에 공유된다 |
| Table 40 설정 적법성 | **구성 제약** | **config 검사 + `illegal_bins`** | 자극이 만들면 안 되는 조합 |
| DRFM 문맥 | **상태 의존 해석** | **같은 shadow model 안에서** | RAA와 분리하면 일관성이 깨진다 |

**① ACT 후속 슬롯 — Note 9**

```systemverilog
// Table 33 Note 9 — ACT 는 1.5 사이클. 두 번째 사이클 하강 에지에 허용되는 것은
// RNOP, 다른 뱅크에 대한 PREpb, 다른 PC 에 대한 PREab 뿐이다.
property p_act_follow_slot;
  logic [5:0] b; logic pc;
  @(posedge ck) disable iff (!rst_n)
    (act_vld, b = act_bank, pc = act_pc) |-> ##1 @(negedge ck)
      ( (row_cmd == RNOP)
      || (row_cmd == PREPB && row_bank != b)        // "다른 뱅크"
      || (row_cmd == PREAB && row_pc   != pc) );    // "다른 PC"
endproperty
a_act_follow_slot: assert property (p_act_follow_slot)
  else `uvm_error("ACT_SLOT", $sformatf(
       "ACT 후속 하강 에지에 허용되지 않은 커맨드 %s (Table 33 Note 9)", row_cmd.name()))

// 세 허용 형태를 모두 겪었는가 — RNOP 만 나오면 나머지 두 분기는 미검증이다
c_act_slot_rnop : cover property (@(posedge ck) act_vld ##1 @(negedge ck) row_cmd == RNOP);
c_act_slot_prepb: cover property (@(posedge ck) act_vld ##1 @(negedge ck) row_cmd == PREPB);
c_act_slot_preab: cover property (@(posedge ck) act_vld ##1 @(negedge ck) row_cmd == PREAB);
```

세 `cover property` 가 없으면 이 assertion은 **`RNOP`만 확인하고 통과**합니다. 규격이 허용한 나머지 두 형태는 스케줄러가 그것을 쓸 때만 나오므로, **자극이 그 최적화를 안 하면 영원히 미검증**입니다.

**② RAA shadow model — 다섯 갈래와 DRFM 문맥을 한곳에서**

```systemverilog
class raa_model extends uvm_object;
  `uvm_object_utils(raa_model)

  // 문턱은 DEVICE_ID 에서 읽어 온다. 상수로 박으면 다른 장치에서 틀린다.
  int unsigned raaimt, raammt, raadec;
  bit          dev_rfm_required;      // DEVICE_ID RFM 비트
  bit          dev_arfm_supported;    // DEVICE_ID ARFM 비트
  bit          mr0_drfm_en;           // MR0 OP3

  protected int unsigned m_raa   [64];   // 뱅크별 RAA
  protected bit          m_drfm_v[64];   // 뱅크별 DRFM 주소 샘플 유효
  protected bit [13:0]   m_drfm_a[64];

  function void on_act(int bank, bit [13:0] row, bit drfm_bit);
    m_raa[bank]++;
    // §6.3.2.5.5 — DRFM 비트가 선 ACT 는 행 주소를 캡처한다. 최근 것만 남는다.
    if (mr0_drfm_en && drfm_bit) begin
      m_drfm_a[bank] = row;
      m_drfm_v[bank] = 1'b1;
    end
  endfunction

  function void on_rfm_pb(int bank);
    // Note 7 — RFM 을 요구하지 않는 장치는 RNOP 을 실행한다. 아무 효과도 없다.
    if (!effective_rfm_enabled()) return;

    if (m_drfm_v[bank]) begin
      // DRFMpb 로 실행된다 — 이웃 행을 복원하지만 RAA 는 깎지 않는다 (§6.3.2.5.5)
      m_drfm_v[bank] = 1'b0;
    end else begin
      // 일반 RFMpb — RAAIMT 만큼 감소, 하한 0 (§6.3.2.5.3)
      m_raa[bank] = (m_raa[bank] > raaimt) ? m_raa[bank] - raaimt : 0;
    end
  endfunction

  function void on_ref_pb(int bank);
    m_raa[bank] = (m_raa[bank] > raadec) ? m_raa[bank] - raadec : 0;
  endfunction

  // §6.3.2.5.3 — self refresh 는 tRAASRF 이상 유지된 경우에만 RAA 를 0 으로 만든다.
  // 그보다 짧으면 진입·종료 자체로는 어떤 감소도 허용되지 않는다.
  function void on_sref_exit(time held);
    if (held >= T_RAASRF) foreach (m_raa[b]) m_raa[b] = 0;
  endfunction

  // Table 40 — DEVICE_ID 두 비트와 MR8 레벨의 조합이 실제 동작을 정한다
  function bit effective_rfm_enabled();
    if (dev_rfm_required)   return 1'b1;
    if (dev_arfm_supported) return (mr8_rfm_level != 2'b00);  // ARFM override
    return 1'b0;                                              // RNOP 으로 실행됨
  endfunction

  function bit act_allowed(int bank);   // RAA = RAAMMT 면 ACTIVATE 금지
    return (m_raa[bank] < raammt);
  endfunction
endclass
```

`on_rfm_pb()` 의 분기가 이 모델의 핵심입니다. **같은 커맨드가 세 가지로 갈립니다** — 무효과(`RNOP`), `DRFMpb`(RAA 유지), 일반 `RFMpb`(RAA 감소). 이 셋을 하나로 처리하면 RAA 예측이 반드시 어긋납니다.

**③ 라운딩 — 기대값 계산의 단일 출처**

```systemverilog
// §6.3.2.4 — HBM4 는 0.5 nCK 해상도를 갖는다. 전통 공식과 결과가 다르다.
// nXX = 0.5 × RU(2 × tXX / tCK)
function automatic int hbm4_round_half(input int t_ps, input int tck_ps);
  return (2*t_ps + tck_ps - 1) / tck_ps;      // 반사이클 정수 단위로 반환
endfunction

// checker 와 시퀀스가 같은 함수를 쓴다. 두 곳에 따로 구현하면 언젠가 갈린다.
localparam int N_RRDL_HALF = hbm4_round_half(T_RRDL_PS, T_CK_PS);
```

**④ 설정 조합 적법성 — Table 40**

```systemverilog
// 자극 구성 단계에서 검사한다. 불법 조합은 만들지 않는 것이 원칙이다.
function void check_rfm_config(bit rfm, bit arfm, bit [1:0] mr8_level);
  // ARFM 미지원 장치에서 MR8 OP[5:4] 는 RFU — 0 만 허용된다 (Table 40 Note 1)
  if (!arfm && mr8_level != 2'b00)
    `uvm_error("RFM_CFG", $sformatf(
      "ARFM 미지원(DEVICE_ID ARFM=0)인데 MR8 RFM Level=%b. Table 40 Illegal", mr8_level))
endfunction
```

### 6.3 무엇을 덮었다고 말할 수 있는가

```systemverilog
covergroup cg_hbm4_row_cmd with function sample(
    refresh_kind_e kind, int raa, int raaimt, int raammt,
    act_slot_e slot, bit drfm_valid, bit rfm_effective,
    bit dev_rfm, bit dev_arfm, bit [1:0] mr8_lvl, sref_dur_e sref);
  option.per_instance = 1;

  // --- refresh 다섯 갈래 (§6.3.2.5) — 하나로 뭉치면 안 된다 ----------------
  cp_kind : coverpoint kind {
    bins refab  = {REF_AB};   bins refpb  = {REF_PB};
    bins rfmab  = {RFM_AB};   bins rfmpb  = {RFM_PB};
    bins drfmpb = {DRFM_PB};                    // RFMpb 가 DRFM 으로 실행된 경우
  }

  // --- RAA 문턱. 절대값이 아니라 문턱 대비 위치로 bin 을 잡는다 -----------
  // RAAIMT/RAAMMT 가 DEVICE_ID 에서 오므로 build 시점에 값을 모른다.
  cp_raa_zone : coverpoint raa_zone(raa, raaimt, raammt) {
    bins zero        = {RAA_ZERO};
    bins below_imt   = {RAA_BELOW_IMT};
    bins at_imt      = {RAA_AT_IMT};       // RFM 이 필요해지는 지점
    bins between     = {RAA_BETWEEN};
    bins at_mmt      = {RAA_AT_MMT};       // ACTIVATE 금지 지점 — 여기가 목표
  }

  // --- ACT 후속 슬롯 세 형태 (Note 9) -----------------------------------
  cp_act_slot : coverpoint slot {
    bins rnop  = {SLOT_RNOP};
    bins prepb = {SLOT_PREPB_OTHER_BANK};
    bins preab = {SLOT_PREAB_OTHER_PC};
  }

  // --- DRFM 문맥 (§6.3.2.5.5) -------------------------------------------
  // 같은 RFMpb 를 유효 샘플 유무 양쪽에서 겪었는가
  cp_drfm_ctx : coverpoint drfm_valid iff (kind inside {RFM_PB, DRFM_PB}) {
    bins no_sample   = {0};      // 일반 RFMpb 로 실행 → RAA 감소
    bins has_sample  = {1};      // DRFMpb 로 실행     → RAA 유지
  }

  // --- Table 40 조합 -----------------------------------------------------
  cp_rfm_cfg : coverpoint {dev_rfm, dev_arfm, mr8_lvl} {
    bins no_rfm_no_arfm    = {4'b00_00};
    bins arfm_override_off = {4'b01_00};
    bins arfm_override_on  = {4'b01_01, 4'b01_10, 4'b01_11};  // RFM=0 인데 RFM 활성
    bins rfm_default       = {4'b10_00};
    bins rfm_and_arfm      = {4'b11_00, 4'b11_01, 4'b11_10, 4'b11_11};
    illegal_bins bad       = {4'b00_01, 4'b00_10, 4'b00_11,
                              4'b10_01, 4'b10_10, 4'b10_11};
  }
  // RFM 이 조용히 무시되는 조합에서 실제로 트래픽을 돌려 봤는가 (Note 7)
  cp_rfm_eff : coverpoint rfm_effective { bins ignored = {0}; bins effective = {1}; }

  // --- self refresh 와 RAA 리셋 (§6.3.2.5.3) ----------------------------
  cp_sref : coverpoint sref {
    bins shorter_than_raasrf = {SREF_SHORT};   // RAA 가 유지되어야 한다
    bins at_least_raasrf     = {SREF_LONG};    // RAA 가 0 이 되어야 한다
  }

  x_kind_zone : cross cp_kind, cp_raa_zone;
endgroup
```

세 가지가 이 장의 목표입니다.

- **`cp_raa_zone.at_mmt`** — ACTIVATE 금지 지점에 도달해 본 적이 있는가. 랜덤 트래픽으로는 거의 안 나옵니다. `RAAMMT`까지 RAA를 올리려면 **같은 뱅크에 ACTIVATE를 집중**해야 하고, 그건 의도적으로 만들어야 하는 패턴입니다.
- **`cp_drfm_ctx` 두 bin** — 같은 `RFMpb`를 샘플 유무 양쪽에서 겪어야 6.2 ②의 분기가 검증됩니다.
- **`cp_rfm_eff.ignored`** — RFM이 조용히 무시되는 구성에서도 트래픽을 돌려 봤는가. 이 bin이 비면 Note 7의 동작은 미검증입니다.

`cp_raa_zone` 이 **절대값이 아니라 문턱 대비 위치**로 정의된 것에 주의하세요. `RAAIMT`·`RAAMMT`가 `DEVICE_ID`에서 오므로 `build_phase`에서는 값을 모릅니다. 상대 zone으로 bin을 잡으면 그 문제가 사라집니다.

### 6.4 어떻게 자극하는가

**① RAA 문턱까지 밀어 올린다** — 이 장에서 가장 중요한 directed 시퀀스입니다.

```systemverilog
// 한 뱅크에 ACTIVATE 를 집중해 RAA 를 RAAMMT 까지 올린다.
// 랜덤 트래픽은 뱅크를 골고루 쓰므로 이 지점에 절대 도달하지 못한다.
class seq_raa_climb extends uvm_sequence #(hbm4_cmd_item);
  `uvm_object_utils(seq_raa_climb)
  rand int unsigned target_bank;
  raa_model         model;                  // DEVICE_ID 에서 읽은 문턱을 들고 있다

  virtual task body();
    while (model.get_raa(target_bank) < model.raammt) begin
      `uvm_do_with(req, { cmd == ACT; bank == target_bank; })
      `uvm_do_with(req, { cmd == PREPB; bank == target_bank; })   // 닫고 다시 연다
    end
    // 여기서 ACTIVATE 는 금지되어야 한다. 발행해 보고 컨트롤러가 막는지 확인한다.
    check_act_blocked(target_bank);
  endtask
endclass
```

**② `RFMpb`를 샘플 유무 양쪽에서** — `cp_drfm_ctx`의 두 bin을 채웁니다.

```systemverilog
// (a) 유효 샘플 없이 — 일반 RFMpb 로 실행, RAA 가 RAAIMT 만큼 감소해야 한다
`uvm_do_with(req, { cmd == ACT;   bank == B; drfm_bit == 0; })
`uvm_do_with(req, { cmd == RFMPB; bank == B; })

// (b) 유효 샘플 있음 — DRFMpb 로 실행, RAA 는 감소하지 않아야 한다
`uvm_do_with(req, { cmd == ACT;   bank == B; drfm_bit == 1; })   // 주소 캡처
`uvm_do_with(req, { cmd == RFMPB; bank == B; })
```

두 시퀀스의 **RAA 변화가 달라야** 합니다. 같으면 모델이나 DUT 중 하나가 문맥을 무시하고 있는 것입니다.

**③ ACT 후속 슬롯 세 형태를 강제한다** — 스케줄러가 자연히 만들지 않으므로 directed로 씁니다.

```systemverilog
// Note 9 가 허용한 세 가지를 각각 발행한다
`uvm_do_with(req, { cmd == ACT; bank == 6'h00; pc == 0; })
`uvm_do_with(req, { cmd == PREPB; bank == 6'h08; });   // 다른 뱅크 — 허용
// ...
`uvm_do_with(req, { cmd == ACT; bank == 6'h00; pc == 0; })
`uvm_do_with(req, { cmd == PREAB; pc == 1; });         // 다른 PC — 허용
```

그리고 **negative**로 금지된 조합(같은 뱅크 `PREpb`, 같은 PC `PREab`)을 발행해 6.2 ①의 assertion이 잡는지 확인합니다.

**④ `DEVICE_ID` 구성 순회** — Table 40의 조합을 환경 구성으로 순회합니다. 특히 **`RFM=0`인 장치 프로파일**을 반드시 포함해야 `cp_rfm_eff.ignored` 가 찹니다. 그 프로파일에서는 RFM을 발행해도 RAA가 안 깎이는 것이 정상입니다.

**⑤ self refresh `tRAASRF` 경계** — 진입 유지 시간을 `tRAASRF` **직전과 직후**로 나눠 두 시나리오를 만듭니다. 짧은 쪽에서 RAA가 유지되는지, 긴 쪽에서 0이 되는지가 갈립니다. 항상 길게만 유지하면 조건부 리셋이 무조건 리셋으로 구현돼 있어도 통과합니다.

**⑥ 미정의 비트 구동 확인** — 4-high 구성처럼 `SID`가 정의되지 않는 프로파일에서, 자극이 해당 핀을 `X`가 아니라 **유효 레벨로 구동**하는지 검사합니다(Note 2). 시뮬레이션에서 `X`는 눈에 띄지만 실물에서는 미정의 동작이 되므로, 이는 **자극 측 검사**입니다.

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

**검증 함의**: 아날로그 값이 조금만 달라져도 예외 규칙 적용 여부가 갈린다. checker와 시퀀스가 **같은 라운딩 함수를 공유**해야 하는 이유이며(6.2 ③), 두 곳에 따로 구현하면 특정 타이밍 조합에서만 어긋나 재현이 어렵다.
</details>

### 문제 2 — RFM 설정 조합

> `DEVICE_ID`를 읽으니 `RFM = 1`, `ARFM = 0`이었다. 컨트롤러가 `MR8` OP[5:4]에 `10`을 프로그램하면?

<details>
<summary>풀이</summary>

Table 40에서 `RFM=1, ARFM=0, level=10`은 **Illegal**이다.

**근거**(Note 1): ARFM을 지원하지 않는 장치는 `MR8` OP[5:4]를 **RFU로 정의**하므로 유일하게 허용되는 값은 `00`이다. [04장](../04_mode_registers/)의 "RFU 비트는 0으로 프로그램해야 한다"는 규칙과 같은 이야기다.

**올바른 동작**: `ARFM = 0`이면 `MR8` OP[5:4] = `00`으로 두고, `RAAIMT`/`RAAMMT`/`RAADEC`의 읽기 전용 값을 그대로 사용한다.

**검증 결론**: 검증 환경도 같은 순서를 따라야 한다 — `tINIT3` 이후 IEEE1500으로 `DEVICE_ID`를 읽고, 그 값으로 RAA 모델과 `MR8` 설정을 구성한다. 문턱값을 상수로 박은 환경은 다른 장치 프로파일에서 **조용히 틀린 기준으로 판정**한다(6.1절).
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

**검증 결론**: shadow model이 **뱅크마다 "유효 샘플 있음" 플래그**를 들어야 한다. 이 상태 없이는 같은 `RFMpb`를 항상 같게 해석하게 되고, RAA 예측이 뱅크별로 갈린다. 두 경우를 각각 자극해 **RAA 변화가 실제로 다른지** 확인하는 것이 검사다(6.4 ②).
</details>

## 핵심 정리

- 진리표에 없는 **`ARFU`도 유효 레벨로 구동**해야 한다(§6.3). 진리표만 보고 구현하면 놓친다.
- **PC로 선택되지 않은 pseudo channel은 RNOP를 수행**한다(Note 5). 커맨드는 항상 양쪽에 도달한다.
- **SID는 `ACT`·`PREpb`·`REFpb`·`RFMpb`에서만** 뱅크 주소로 쓰인다(Note 6).
- 밀도상 정의되지 않는 `SID`/`RA` 핀도, parity를 꺼도 `APAR`도 **유효 레벨로 구동**해야 한다(Note 2).
- **PDX/SRX에서는 패리티를 검사하지 않지만** `tXP`·`tXS` 동안 **유효 패리티의 RNOP/CNOP를 요구**한다(Note 8).
- row 커맨드는 **하강 에지를 `RNOP`로 패딩**하거나 precharge로 채운다. ACT 두 번째 사이클 하강 슬롯에는 **RNOP / 다른 뱅크 PREpb / 다른 PC PREab**만 허용된다(Note 9). 셋 중 `RNOP`만 자연히 나오므로 **나머지 둘은 directed로 만들지 않으면 미검증**이다.
- **라운딩 공식이 바뀌었다** — `nXX = 0.5 × RU(2·tXX/tCK)`, 대상은 **`tRAS`·`tRTP`·`tWR`·`tRP`**. `tRP` 결과가 하강 에지면 **+0.5**. checker와 시퀀스가 **같은 함수를 공유**해야 한다 — 두 곳에 따로 구현하면 언젠가 갈린다.
- Refresh는 **다섯 갈래**다. `RFM`은 **REF를 대체하지 않고** 내부 관리 시간을 주는 **보너스**다.
- RAA는 뱅크별 카운터 — ACT +1, RFM −`RAAIMT`, REF −`RAADEC`, **하한 0**(pull-in 금지), `RAAMMT` 도달 시 **ACTIVATE 금지**. 문턱값은 **`DEVICE_ID` WDR에서 런타임에 읽는다** — 상수로 박으면 다른 장치에서 조용히 틀린 기준이 되고, coverage bin도 **절대값이 아니라 문턱 대비 위치**로 잡아야 한다.
- `RAAMMT` 도달은 **랜덤 트래픽으로 거의 안 나온다.** 한 뱅크에 ACTIVATE를 집중하는 directed 시퀀스가 필요하다.
- self refresh로 RAA가 0이 되려면 **`tRAASRF` 이상 유지**되어야 한다.
- **ARFM**은 읽기 전용 문턱값의 경직성을 푼다. `ARFM` 미지원 장치에서 `MR8` OP[5:4]≠`00`은 **Illegal**이다.
- **DRFM은 지목형** refresh다. 뱅크별 주소 레지스터에 **최신 샘플만** 남고, **`DRFMpb`는 RAA를 감소시키지 않는다.** 유효 샘플이 없으면 같은 커맨드가 **일반 RFMpb**로 동작한다.
- 같은 `RFMpb`가 **세 가지로 갈린다** — 무효과(`RFM=0` 장치, Note 7) · `DRFMpb`(RAA 유지) · 일반 `RFMpb`(RAA 감소). 셋을 하나로 처리하는 모델은 RAA 예측이 반드시 어긋난다.

## Further Reading

- **규격**: JESD270-4 §6.3 Commands · §6.3.1 Truth Tables (Table 33–34) · §6.3.2 Row Commands (Figure 17–32) · §6.3.2.4 Rounding Rules · §6.3.2.5 Refresh (Table 38–40)
- **다음 장**: [07 — Column 커맨드와 저전력](../07_column_commands/)
- **관련**: [04 — Mode Register](../04_mode_registers/) (`MR0` DRFM, `MR8` RFM Level) · [11 — 트레이닝과 IEEE 1500](../11_training_ieee1500/) (`DEVICE_ID` WDR)
- **이해도 점검**: [퀴즈](../quiz/06_row_commands_quiz/)
