---
title: "08 — Parity"
description: JESD270-4 §6.4 · Command/Address parity와 Data parity, 프로그래머블 PL, 검출 전용이라는 설계 철학
---

:::tip[🎯 Learning Objectives]
이 모듈을 마치면:

- **Compute** CA parity의 대상 신호 집합과 짝수 규칙으로 `AERR` 값을 판정한다.
- **Explain** 패리티 오류가 발생해도 커맨드가 실행되고 write가 완료되는 이유와, 그것이 **에러 주입 이후 기대값**을 왜 어렵게 만드는지 설명한다.
- **Analyze** `PL`(Parity Latency)이 데이터와 `DPAR` 사이에 만드는 시간 어긋남과 그에 따른 추가 스트로브 요구를 분석한다.
- **Determine** `MD`·`WDBI`/`RDBI` 설정에 따라 패리티 대상 집합이 어떻게 달라지는지 판정한다.
- **Construct** `AERR` monitor를 커맨드 이력과 함께 만들고, 귀속이 **추정**임을 반영한다.
- **Evaluate** 규격이 활성화 시점을 구간으로 열어 둔 것이 checker에 **관대 구간**을 요구하는 이유를 판단한다.
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

:::caution[검증에 미치는 영향]
이 성질은 두 가지를 뜻합니다.

1. **복구 책임은 전적으로 호스트에 있습니다.** 장치는 잘못된 주소로 activate를 하거나 엉뚱한 뱅크를 precharge할 수 있고, 컨트롤러가 `AERR`를 보고 상태를 재구성해야 합니다.
2. **`AERR`를 관측하지 않으면 오류가 조용히 지나갑니다.** 데이터가 우연히 맞으면 상위 계층은 아무것도 알아채지 못합니다 — [`hbm_dv`](../../hbm_dv/09_assertion_checker/)에서 말한 **조용한 통과**의 하드웨어적 사례입니다.

**검증 결론**: `AERR`는 "있으면 좋은" 신호가 아니라 **환경이 상시 감시해야 하는 신호**입니다. 감시하지 않으면 데이터가 우연히 맞는 경우에 오류가 통째로 지나갑니다.
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

**검증 결론**: scoreboard는 `DERR`를 받으면 **그 주소를 오염으로 표시**해야 합니다. write parity 오류는 주소를 알기 때문에 이것이 가능하고, 이 장에서 **끝까지 추적 가능한 유일한 오류 유형**입니다 — 5.4 ②.
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

**검증 함의**: `PL` 값을 바꾸면 스트로브 시퀀스 길이가 바뀝니다. [05장](../05_clocking_dbi/)의 **누적 토글 카운터가 `PL`에 따른 추가 펄스를 반영**하지 않으면 짝수 불변식 계산 자체가 틀립니다. 그리고 `PL`은 뒤에서 볼 `WPAR` 비활성화 금지 구간의 길이도 바꿉니다.
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

**검증 결론**: 대상 집합 계산을 **단일 출처 함수**로 두고 reference model과 자극 생성기가 공유해야 합니다(5.2 ③). 두 곳에 따로 구현하면 설정을 바꾸는 순간 **정상 데이터에서 패리티 오류**가 나고, 증상은 데이터 경로 버그처럼 보입니다.
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

핀이 재사용되므로 **monitor의 `DERR` 해석도 모드에 따라 갈라져야** 합니다. 트레이닝 중 `DERR` HIGH를 패리티 오류로 처리하면 존재하지 않는 오류를 보고하고, 로그가 가짜 에러로 덮이면 그 안의 진짜 오류가 보이지 않습니다.

## 🔬 검증 적용

### 5.1 무엇이 깨질 수 있는가

이 장은 **에러 주입의 장**입니다. 그런데 §6.4의 "차단하지 않는다"가 에러 주입 검증을 통상보다 훨씬 어렵게 만듭니다 — **주입 이후 무엇을 기대해야 하는지**가 명확하지 않기 때문입니다.

| 조문 | 위반 형태 | 증상 | 잡히는 시점 |
|---|---|---|---|
| §6.4.1 — 오류와 **무관하게 커맨드 실행** | 모델이 "차단됐다"고 가정 | 모델과 DUT의 뱅크 상태가 갈림 | 주입 이후 전부 |
| §6.4.2 — write를 **차단하지 않는다** | 모델이 배열 오염을 반영 안 함 | 이후 read가 전부 미스매치 | 주입 이후 전부 |
| §6.4.1 — `AERR` **상시 감시** | 감시 안 함 | 데이터가 우연히 맞으면 **조용한 통과** | **없음** |
| §6.4.1 — R/C **구별 불가** | monitor가 어느 버스인지 안다고 가정 | 잘못된 귀속 | 없음 |
| §6.4.1 — 연속 오류 시 `AERR` **HIGH 유지** | 펄스 개수로 오류 수를 셈 | 연속 오류를 1건으로 계수 | 없음 |
| §6.4.1 — 활성화 시점이 **구간으로 규정** | checker가 특정 시점을 가정 | false FAIL 또는 놓친 위반 | 전환 시퀀스 |
| §6.4.1/§6.4.2 — 비활성화 금지 구간이 **셋 다 다름** | 하나로 통일 | 위험 구간에서 비활성화 | 없음 |
| §6.4.2 — `PL` 추가 스트로브 | [05장](../05_clocking_dbi/) 토글 카운터에 미반영 | 짝수 불변식 계산이 틀림 | 지연 |
| Table 47 — 대상 집합이 **설정 의존** | 고정으로 계산 | **정상 데이터에서 패리티 오류** | 즉시(원인 오진) |
| Table 47 — **`SEV`는 어떤 경우에도 미포함** | 포함시킴 | 상시 불일치 | 즉시 |
| §6.4.2 / [05장] — `DERR`의 **두 얼굴** | 모드 미구분 | 트레이닝 중 가짜 오류 | 즉시(잘못된 방향) |

:::caution[에러를 주입한 다음, 무엇을 기대할 것인가]
통상의 에러 주입은 "오류를 넣으면 DUT가 막거나 정정한다"를 확인합니다. 여기서는 **아무것도 막지 않습니다.** 잘못된 커맨드는 실행되고, 잘못된 데이터는 배열에 기록됩니다.

그러면 scoreboard는 주입 이후 무엇과 비교해야 하는가 — 두 갈래로 갈립니다.

**Data parity 오류**는 다룰 수 있습니다. 어느 주소에 잘못된 데이터가 들어갔는지 **알기 때문**입니다. 그 주소를 "오염됨"으로 표시하고, 이후 read를 비교에서 제외하거나 재작성으로 복구합니다.

**CA parity 오류는 다르게 어렵습니다.** 주소 자체가 깨졌으므로 **어느 뱅크·어느 행이 영향을 받았는지 모릅니다.** 게다가 §6.4.1에 따라 row 버스인지 column 버스인지도 구별할 수 없습니다. 곧 모델은 다음 중 하나를 택해야 합니다.

| 전략 | 대가 |
|---|---|
| 영향 가능 범위를 **광범위 무효화** (해당 PC 전체) | 이후 검증 능력이 크게 떨어진다 |
| 주입 직후 **precharge-all + 알려진 상태로 재동기화** | 주입 이후 구간을 검증하지 못한다 |
| 주입을 **테스트 말미에만** 배치 | 오류 이후 동작이 미검증으로 남는다 |

세 번째가 현실적으로 가장 많이 쓰이지만, 그것이 **무엇을 포기하는지는 알고 있어야** 합니다. "CA parity 에러 주입 테스트 통과"가 "오류 이후 복구가 검증됨"을 뜻하지는 않습니다.
:::

:::caution[규격이 시점을 구간으로 열어 두었다]
§6.4.1은 패리티 검사가 켜지는 시점을 **하나로 못 박지 않습니다.**

> 활성화 `MRS` **다음 클럭 사이클부터 검사를 시작할 수 있으며**, 늦어도 그 `MRS` 이후 **`tMOD`가 만료되면 활성화되어 있다.**

checker가 이 구간을 잘못 다루면 양쪽으로 틀립니다.

| checker의 가정 | 결과 |
|---|---|
| "`tMOD` 만료 후부터 검사" | 일찍 켜는 DUT의 오류 보고를 **놓친다** |
| "다음 사이클부터 검사" | 늦게 켜는 DUT에 **false FAIL** |

올바른 처리는 **구간 안에서는 양쪽을 모두 허용**하고, 구간 밖에서만 엄격히 판정하는 것입니다. 그리고 자극 쪽은 **활성화 MRS 직후부터 곧바로 올바른 패리티를 실어야** 합니다 — 그래야 어느 시점에 켜지든 안전합니다.

규격이 `may`로 열어 둔 자리는 이렇게 **checker의 관대 구간**이 됩니다([index의 조동사 규칙](../)).
:::

### 5.2 어떻게 잡는가 — 수단 선택

| 규칙 | 성격 | 수단 | 이유 |
|---|---|---|---|
| `AERR` 상시 감시와 커맨드 귀속 | **이력 대조** | **monitor + 커맨드 히스토리** | `tPARAC` 만큼 과거를 봐야 한다 |
| 패리티 활성 구간 | **구간 기대값** | **SVA (관대 구간 포함)** | 규격이 시점을 열어 두었다 |
| 대상 집합 계산 | **설정 의존 함수** | **단일 출처 함수** | 모델과 checker가 같은 것을 써야 한다 |
| 배열 오염 추적 | **상태** | **scoreboard의 오염 마킹** | 주입 이후 기대값을 유지하려면 |
| `PL` 추가 스트로브 | **누적 불변식** | [05장](../05_clocking_dbi/) **토글 카운터에 반영** | 같은 불변식의 일부다 |

**① `AERR` monitor — 귀속은 추정이지 사실이 아니다**

```systemverilog
// §6.4.1 — AERR 는 tPARAC 후 1 tCK HIGH. 연속 오류면 다음 사이클에도 HIGH 유지.
// 그리고 row/column 어느 버스인지 알려주지 않는다.
class aerr_monitor extends uvm_monitor;
  `uvm_component_utils(aerr_monitor)
  localparam int HIST = T_PARAC + 2;
  protected cmd_record_t m_hist[$];       // 발행 이력

  task run_phase(uvm_phase phase);
    forever begin
      @(posedge vif.ck);
      m_hist.push_front(sample_cmd());
      if (m_hist.size() > HIST) void'(m_hist.pop_back());

      if (vif.aerr) begin
        // tPARAC 전의 사이클이 원인 후보다. 단 "후보"일 뿐이다 —
        // 같은 사이클의 row 와 column 두 커맨드 중 어느 쪽인지 구별할 수 없다.
        cmd_record_t suspect = m_hist[T_PARAC];
        `uvm_info("AERR", $sformatf(
          "패리티 오류 보고. 후보 커맨드: row=%s column=%s (버스 구별 불가, §6.4.1)",
          suspect.row_cmd.name(), suspect.col_cmd.name()), UVM_LOW)
        m_sb.mark_suspect(suspect);        // scoreboard 에 오염 후보를 넘긴다
      end
    end
  endtask
endclass
```

`suspect` 를 **확정된 원인으로 다루면 안 됩니다.** 같은 사이클에 row와 column 커맨드가 동시에 나갈 수 있고(§3.1.3의 이중 인터페이스), `AERR`는 둘을 구별하지 않습니다. monitor가 할 수 있는 것은 **후보를 좁히는 것**까지입니다.

그리고 **연속 오류 처리**를 빠뜨리기 쉽습니다. `AERR`가 두 사이클 연속 HIGH면 오류가 **두 건**입니다. 상승 에지만 세면 한 건으로 계수됩니다.

**② 패리티 활성 구간 — 관대 구간을 명시한다**

```systemverilog
// §6.4.1 — 활성화 시점은 [MRS+1, MRS+tMOD] 구간 어디든 될 수 있다.
// 구간 안에서는 검사 여부를 판정하지 않고, 구간 밖에서만 엄격히 본다.
typedef enum {PAR_OFF, PAR_TURNING_ON, PAR_ON, PAR_TURNING_OFF} par_state_e;
par_state_e par_state;

// 구간 밖 — 켜져 있어야 한다
a_parity_on_after_tmod: assert property (@(posedge ck) disable iff (!rst_n)
    (par_state == PAR_ON && bad_parity_injected) |-> ##[1:T_PARAC+1] aerr)
  else `uvm_error("CAPAR", "패리티 활성 구간의 오류가 AERR 로 보고되지 않았다")

// 구간 밖 — 꺼져 있어야 한다
a_parity_off: assert property (@(posedge ck) disable iff (!rst_n)
    (par_state == PAR_OFF) |-> !aerr)
  else `uvm_error("CAPAR", "패리티 비활성 상태인데 AERR 가 보고되었다")

// PAR_TURNING_ON 구간에는 assertion 을 두지 않는다 — 규격이 열어 둔 자리다.
// 대신 그 구간을 실제로 지나갔는지만 센다.
c_turning_on_window: cover property (@(posedge ck) par_state == PAR_TURNING_ON);
```

**③ 대상 집합 — 단일 출처**

Table 47의 대상 집합이 **다른 두 레지스터**(`MR0`의 DBI, `MR9`의 `MD`)에 의존합니다. 모델과 checker가 각자 구현하면 언젠가 갈립니다.

```systemverilog
// Table 47 — 대상 집합은 설정에 따라 달라진다. SEV 는 어떤 경우에도 포함되지 않는다.
function automatic bit dword_parity(input bit [31:0] dq, input bit [1:0] ecc,
                                    input bit [3:0]  dbi,
                                    input bit md_en, input bit dbi_en);
  dword_parity = ^dq;
  if (md_en)  dword_parity ^= ^ecc;     // MR9 OP0
  if (dbi_en) dword_parity ^= ^dbi;     // MR0 OP1(W) / OP0(R)
  // SEV 는 더하지 않는다 (Table 47)
endfunction
```

이 함수 하나를 reference model과 자극 생성기가 **공유**해야 합니다. 두 곳에 따로 쓰면, `MD`나 DBI 설정을 바꾸는 순간 **정상 데이터에서 패리티 오류가 발생**하고 원인은 데이터 경로처럼 보입니다.

**④ 오염 추적 — scoreboard가 기대값을 유지하는 법**

```systemverilog
// §6.4.2 — write parity 오류가 나도 데이터는 배열에 기록된다.
// 어느 주소인지는 알므로, 그 주소를 오염으로 표시하고 비교에서 제외한다.
function void on_write_parity_error(hbm4_addr_t a);
  m_poisoned[{a.ch, a.pc, a.sid, a.ba, a.ra, a.ca}] = 1'b1;
endfunction

function bit expect_valid(hbm4_addr_t a);
  return !m_poisoned.exists({a.ch, a.pc, a.sid, a.ba, a.ra, a.ca});
endfunction

// 오염된 주소에 정상 write 를 다시 하면 복구된다
function void on_clean_write(hbm4_addr_t a);
  m_poisoned.delete({a.ch, a.pc, a.sid, a.ba, a.ra, a.ca});
endfunction
```

CA parity 오류에는 이 방법을 쓸 수 없습니다 — 주소를 모르기 때문입니다. 5.1절의 세 전략 중 하나를 골라야 합니다.

### 5.3 무엇을 덮었다고 말할 수 있는가

```systemverilog
covergroup cg_hbm4_parity with function sample(
    par_err_e err, err_bus_e bus, int pl, bit md_en, bit dbi_en,
    par_state_e pstate, disable_case_e dis, bit derr_training_mode);
  option.per_instance = 1;

  // --- 오류 형태 ---------------------------------------------------------
  cp_err : coverpoint err {
    bins none        = {PAR_NONE};
    bins ca_single   = {PAR_CA_SINGLE};
    bins ca_consec   = {PAR_CA_CONSECUTIVE};   // AERR 가 연속 HIGH — 계수 로직 검증
    bins wr_data     = {PAR_WR_DATA};
    bins rd_data     = {PAR_RD_DATA};
  }
  // 주입한 버스는 자극이 안다 (AERR 로는 구별 불가) — 양쪽에 넣어 봤는가
  cp_bus : coverpoint bus iff (err inside {PAR_CA_SINGLE, PAR_CA_CONSECUTIVE}) {
    bins row_bus = {ERR_ROW}; bins col_bus = {ERR_COL};
  }

  // --- 대상 집합 네 조합 (Table 47) --------------------------------------
  cp_md  : coverpoint md_en  { bins off = {0}; bins on = {1}; }
  cp_dbi : coverpoint dbi_en { bins off = {0}; bins on = {1}; }
  x_target_set : cross cp_md, cp_dbi;          // 네 조합 전부
  // 각 대상 집합에서 실제로 오류를 주입해 봤는가
  x_err_target : cross cp_err, cp_md, cp_dbi {
    ignore_bins no_err = binsof(cp_err.none);
  }

  // --- Parity Latency (MR1 OP[7:5]) --------------------------------------
  cp_pl : coverpoint pl {
    bins zero = {0};                  // PL=0 — 추가 스트로브 없음
    bins mid  = {[1:3]};
    bins max  = {4};                  // 추가 스트로브가 가장 많은 경우
  }

  // --- 활성 구간 (§6.4.1) -------------------------------------------------
  cp_pstate : coverpoint pstate {
    bins off         = {PAR_OFF};
    bins turning_on  = {PAR_TURNING_ON};    // 규격이 열어 둔 관대 구간
    bins on          = {PAR_ON};
    bins turning_off = {PAR_TURNING_OFF};
  }

  // --- 비활성화 금지 구간 세 종 (§6.4.1, §6.4.2) -------------------------
  cp_disable : coverpoint dis {
    bins capar_at_tparac = {DIS_CAPAR_BOUNDARY};   // access + tPARAC
    bins wpar_at_window  = {DIS_WPAR_BOUNDARY};    // WL + PL + tPARDQ + 2
    bins rpar_at_trdmrs  = {DIS_RPAR_BOUNDARY};    // READ + tRDMRS
  }

  // --- DERR 문맥 ---------------------------------------------------------
  cp_derr_ctx : coverpoint derr_training_mode {
    bins normal   = {0};       // 데이터 패리티 오류
    bins training = {1};       // 위상 검출기 출력 ([05장])
  }
endgroup
```

네 가지를 지적해 둡니다.

- **`cp_err.ca_consec`** — 연속 오류를 만들지 않으면 `AERR` 계수 로직(상승 에지만 세는 실수)이 검증되지 않습니다.
- **`x_err_target`** — 대상 집합 네 조합 **각각에서** 오류를 주입해야 합니다. 한 조합에서만 주입하면 나머지 셋의 계산식은 미검증입니다.
- **`cp_pl.zero`와 `cp_pl.max`** — `PL`이 추가 스트로브 수를 바꾸므로, 양 끝을 겪어야 [05장](../05_clocking_dbi/) 짝수 불변식이 `PL` 전 범위에서 성립하는지 확인됩니다.
- **`cp_disable` 세 bin** — 세 조건의 기준점과 값이 모두 다릅니다. 하나만 시험하면 나머지 둘은 통일 구현되어 있어도 통과합니다.

### 5.4 어떻게 자극하는가

**① CA parity 오류를 두 버스에 각각** — `AERR`는 구별하지 못하지만 **자극은 어느 쪽에 넣었는지 압니다.** 그 정보로 monitor의 귀속 추정이 합리적인지 평가합니다.

```systemverilog
class seq_ca_parity_inject extends uvm_sequence #(hbm4_cmd_item);
  `uvm_object_utils(seq_ca_parity_inject)
  rand err_bus_e bus;
  rand bit       consecutive;

  virtual task body();
    // 패리티 비트를 뒤집어 짝수 규칙을 깬다. 커맨드 자체는 정상 발행된다 (§6.4.1).
    `uvm_do_with(req, { cmd == ACT; corrupt_parity == 1; corrupt_bus == bus; })
    if (consecutive)
      // 연속 오류 — AERR 가 두 사이클 연속 HIGH 여야 한다
      `uvm_do_with(req, { cmd == PREPB; corrupt_parity == 1; corrupt_bus == bus; })
  endtask
endclass
```

**② write parity 오류 → 오염 → 확인** — 이 장에서 유일하게 **끝까지 추적 가능한** 시나리오입니다.

```
① 정상 write (주소 A) → scoreboard 에 기대값 기록
② write parity 오류 주입 (주소 A) → DERR 보고, 데이터는 배열에 기록됨
③ scoreboard 가 A 를 오염으로 표시
④ read A → 비교에서 제외되는지 확인 (모델이 오염을 모르면 여기서 오탐이 난다)
⑤ 정상 write (주소 A) → 오염 해제
⑥ read A → 이번엔 비교되고 통과해야 한다
```

④와 ⑥의 **차이**가 검사 지점입니다. 오염 추적이 없는 scoreboard는 ④에서 실패를 보고합니다.

**③ 대상 집합 네 조합 순회** — `MD` × DBI 각 조합에서 정상 트래픽과 오류 주입을 모두 돌립니다. 조합을 바꾸는 `MRS` 전후에 패리티를 정리하지 않으면, **정상 데이터에서 패리티 오류**가 나는 것을 관찰하게 됩니다 — 그 자체가 검사 항목입니다.

**④ 비활성화 경계 세 지점** — 각 금지 구간의 **만료 직전과 직후**에 비활성화 `MRS`를 발행합니다.

| 대상 | 기준점 | 금지 구간 |
|---|---|---|
| `CAPAR` | access 커맨드 | `tPARAC` |
| `WPAR` | `WRITE` | `WL + PL + tPARDQ + 2 tCK` |
| `RPAR` | `READ` | `tRDMRS` |

`WPAR` 구간이 **`PL`에 의존**하는 것에 주의하세요 — `PL`을 바꾸면 금지 구간 길이도 바뀝니다. `PL` 순회와 이 경계 테스트를 함께 돌려야 합니다.

**⑤ 트레이닝 모드에서 `DERR` 확인** — [05장](../05_clocking_dbi/)의 `WDQS2CK` 트레이닝을 돌리면서 `DERR`가 패리티 오류로 보고되지 **않는지** 확인합니다. 이는 DUT가 아니라 **환경의 monitor를 검증**하는 테스트입니다.

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

**검증 결론**: 대상 집합 네 조합 **각각에서** 오류를 주입해야 한다(`x_err_target`). 한 조합에서만 주입하면 나머지 셋의 계산식은 미검증으로 남고, 설정을 바꾸는 시퀀스에서야 드러난다.
</details>

### 문제 3 — `DERR` 오인

> WDQS-to-CK 정렬 트레이닝 중에 `DERR0`가 HIGH로 관측됐다. 컨트롤러가 write 재시도를 시작했다. 올바른가?

<details>
<summary>풀이</summary>

**틀렸다.** 트레이닝 모드(`MR8` OP3 = 1)에서 `DERR`는 **패리티 오류가 아니라 위상 검출기 판독**이다([05장](../05_clocking_dbi/), Table 31).

`DERR0` HIGH는 *"내부 `WDQS/2`의 0° 위상이 CK로 샘플링했을 때 HIGH → WDQS가 **early**"* 를 뜻하며, **권장 조치는 WDQS 지연을 늘리는 것**이다.

**검증 결론**: monitor의 `DERR` 해석은 **모드에 따라 분기**해야 하고, 이를 확인하는 테스트는 **DUT가 아니라 환경을 검증**한다 — 트레이닝을 돌리면서 패리티 오류가 보고되지 *않는지* 본다(5.4 ⑤).

```
MR8 OP3 == 1  →  위상 검출기 판독 (early/late)
MR8 OP3 == 0  →  데이터 패리티 오류
```

게다가 트레이닝 모드에서는 애초에 write 버스트가 진행 중이지 않으므로, 재시도할 대상 자체가 없다. 이 오인은 **존재하지 않는 트랜잭션의 재시도**를 만들어 컨트롤러 상태를 망가뜨린다.
</details>

## 핵심 정리

- CA parity 대상은 **`R[9:0]` + `C[7:0]` + `ARFU` + `APAR`**, **짝수 패리티**, **상승·하강 에지 각각** 계산된다. **`ARFU`를 빼면 안 된다.**
- ⚠️ **패리티는 검출 전용이다.** CA 오류가 나도 **커맨드는 실행**되고, data 오류가 나도 **write는 배열까지 완료**된다. 곧 에러 주입 이후 **모델이 오염된 상태를 따라가야** 하며, 이것이 이 장의 검증을 어렵게 만드는 핵심이다.
- 차단하지 않는 것은 **버스트에 중단·절단이 없다**는 모델의 일관된 귀결이다. 복구는 호스트 몫이다.
- **`AERR`만으로는 row/column 어느 버스인지 구별할 수 없다.** 커맨드 이력 대조는 **후보를 좁히는 추정**이지 확정이 아니다. 연속 오류 시 `AERR`가 HIGH를 유지하므로 **상승 에지만 세면 오류 수를 놓친다.**
- **write parity 오류는 주소를 알기에 오염 추적이 가능**하지만, **CA parity 오류는 주소 자체가 깨져 어디가 오염됐는지 모른다.** 광범위 무효화 · 재동기화 · 테스트 말미 배치 중 하나를 택해야 하고, 각각 무엇을 포기하는지 알아야 한다.
- 패리티 활성화는 **"MRS 다음 사이클 ~ `tMOD` 만료" 사이 어디선가** 일어난다. checker는 그 구간을 **관대 구간**으로 두고 밖에서만 엄격히 판정해야 한다 — 한쪽으로 못 박으면 **false FAIL** 아니면 **놓친 위반**이 된다. 자극은 활성화 MRS 직후부터 즉시 올바른 패리티를 싣는다.
- data parity는 **계산은 UI 단위, 보고는 반 버스트(4 UI) 단위**다. 첫 사이클 오류의 `tPARDQ`는 `(WL + PL)` 후에 시작한다.
- **`PL`은 데이터와 `DPAR`을 어긋나게** 해 계산 여유를 만든다. 대가로 **추가 스트로브 토글**이 필요하며, 그 추가량도 **짝수**로 설계되어 있다(`PL=2` → 4펄스).
- **패리티 대상 집합은 고정이 아니다.** DBI는 `WDBI`/`RDBI`, ECC는 `MR9`의 `MD`에 의존한다. **`SEV`는 언제나 제외**다.
- 비활성화 금지 구간이 셋 다 다르다 — `CAPAR`은 `tPARAC`, `WPAR`은 `WL+PL+tPARDQ+2tCK`, `RPAR`은 `tRDMRS`. **`WPAR` 구간은 `PL`에 의존**하므로 `PL` 순회와 경계 테스트를 함께 돌려야 한다.
- **`DERR`는 두 얼굴을 갖는다** — 일반 동작에서는 패리티 오류, WDQS-to-CK 트레이닝에서는 위상 검출기 판독이다. 모드를 구분하지 않는 monitor는 트레이닝 내내 가짜 오류를 쏟아내 진짜 오류를 가린다.

## Further Reading

- **규격**: JESD270-4 §6.4.1 Command/Address Parity (Table 46, Figure 61–64) · §6.4.2 Data Parity (Table 47, Figure 65–69)
- **다음 장**: [09 — On-die ECC · ECS · SEV](../09_ecc_ecs_sev/)
- **관련**: [04 — Mode Register](../04_mode_registers/) (`MR0`·`MR1`·`MR9`) · [05 — 클럭킹](../05_clocking_dbi/) (`DERR`의 다른 용도) · [06 — Row 커맨드](../06_row_commands/) (`ARFU`)
- **이해도 점검**: [퀴즈](../quiz/08_parity_quiz/)
