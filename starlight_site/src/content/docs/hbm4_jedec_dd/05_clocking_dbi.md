---
title: "05 — 클럭킹과 DBIac"
description: JESD270-4 §6.1–6.2 · 조용히 통과하는 짝수 토글 위반, 문맥에 따라 의미가 바뀌는 DERR, 순차 함수인 DBIac reference model
---

:::tip[🎯 Learning Objectives]
이 모듈을 마치면:

- **Explain** 스트로브 주파수가 커맨드 클럭의 두 배라는 사실이 왜 내부 분주기를 요구하는지 설명한다.
- **Derive** preamble·postamble·트레이닝 토글 수가 **짝수여야 한다**는 규칙의 근거와 위반 결과를 도출한다.
- **Sequence** WDQS-to-CK 정렬 트레이닝의 7단계를 위상 검출기 출력 해석과 함께 재구성한다.
- **Apply** DBIac 진리표를 적용해 주어진 데이터 전이 수에 대한 DBI 상태와 반전 여부를 판정한다.
- **Construct** DBIac를 **순차** reference model로 구현하고, 경계값 4의 히스테리시스와 네 리셋 조건을 반영한다.
- **Analyze** 짝수 토글 위반이 왜 기능 검사로 잡히지 않는지 분석하고, 누적 불변식 감시가 유일한 수단인 이유를 설명한다.
- **Differentiate** `DERR`이 트레이닝 모드와 일반 동작에서 갖는 서로 다른 의미를 구분하고, monitor가 그것을 어떻게 알아야 하는지 결정한다.
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

PLL: "PLL\n(공통 소스)" { style.fill: "#e3f2fd"; style.font-color: "#0A0F25" }

CK: "CK_t / CK_c\n커맨드·주소 (DDR)\n기준 주파수 f" { style.fill: "#e8f5e9"; style.font-color: "#0A0F25" }

WDQS: "WDQS_t / WDQS_c\n쓰기 스트로브\n주파수 2f" { style.fill: "#fff8e1"; style.font-color: "#0A0F25" }

DIV: "reset 타입 분주기\nWDQS / 2\n→ 내부 회로는 f 로 동작\n위상(0°/90°/180°/270°) 상태를 가짐" { style.fill: "#ffebee"; style.font-color: "#0A0F25" }

RDQS: "RDQS_t / RDQS_c\n읽기 스트로브\nWDQS에서 생성" { style.fill: "#f3e5f5"; style.font-color: "#0A0F25" }

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

**검증 규칙**: 이 결함은 **기능 검사로 잡을 수 없습니다.** 위상이 뒤집혀도 데이터는 맞기 때문입니다. 잡는 방법은 **불변식을 직접 감시**하는 것뿐이며, 그 불변식은 개별 시퀀스가 아니라 **누적 합**에 대한 조건입니다 — 시퀀스 경계를 넘어 사는 카운터가 필요합니다(5.2 ①).
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

**검증 판단**: 규격이 금지하지 않았으므로 DUT는 이 조합에서도 동작해야 하지만, **트레이닝 정확도는 보장되지 않습니다.** 곧 기대값을 세우기 어려운 구간입니다. 트레이닝 중 refresh는 **정상 회귀에서 제외하고 별도 스트레스 테스트로 격리**하는 편이 결과 해석에 유리합니다 — 5.4 ⑤.
:::

### 위상 검출기 출력 해석

Table 31이 판독을 행동으로 옮기는 규칙을 줍니다.

| CK로 샘플링한 내부 `WDQS/2` (0° 위상) | 위상 판정 | `DERR0`/`DERR1` | 권장 조치 |
|---|---|---|---|
| **HIGH** | Early | **HIGH** | WDQS 지연을 **늘린다** |
| **LOW** | Late | **LOW** | WDQS 지연을 **줄인다** |

`DERR` 신호가 여기서 **데이터 오류 신호가 아니라 위상 검출기 출력**으로 재사용된다는 점이 특이합니다 — 트레이닝 모드에서만 성립하는 의미입니다.

검증에서 이것은 **monitor 설계 문제**가 됩니다. 모드를 모르는 monitor는 트레이닝 내내 `DERR` 상승을 데이터 오류로 보고하고, 로그가 가짜 에러로 뒤덮여 그 안의 진짜 오류를 가립니다 — 5.1절.

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

즉 DBI는 **DQ 바이트에만** 적용됩니다. reference model이 ECC/SEV에 반전을 적용하면 그 경로의 비교가 전부 어긋나고, 증상은 **ECC 로직 버그처럼** 보입니다. 그리고 `DPAR`도 별도 취급입니다(아래).
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

**`RDBI` 비활성이어도 프리컨디셔닝이 일어난다**는 점이 중요합니다. DBI 기능을 껐다고 해서 이 동작이 사라지지 않습니다. DBI를 끈 프로파일로만 도는 회귀가 "DBI 관련 동작은 없다"고 가정하면, 리셋 직후 첫 read에서 모델이 어긋납니다.

그리고 `DPAR`은 예외입니다.

> `DPAR` 신호는 **DBI 계산에 포함되지 않으며 LOW로 프리컨디셔닝되지도 않는다.** 초기 상태는 **정의되지 않는다**(LOW 또는 HIGH). — §6.2.1.1

### 연속 READ에서의 상태 유지

read 버스트가 끝나면 DRAM은 **모든 DQ·DBI·ECC 출력 드라이버를 tri-state** 합니다. 그러나 내부적으로는 **DQ·DBI·ECC·SEV의 마지막 데이터 출력을 저장**해 두고, 후속 read의 버스 프리컨디셔닝과 DBIac 계산에 사용합니다(§6.2.1.2).

비연속(non-gapless) read의 경우 프리컨디셔닝 시점이 바이트에 따라 다릅니다.

| 대상 | 첫 유효 데이터 비트 이전 |
|---|---|
| **홀수 바이트** | 명목상 **2 WDQS 사이클** |
| **짝수 바이트** | 명목상 **1 WDQS 사이클** |

## 🔬 검증 적용

### 5.1 무엇이 깨질 수 있는가

이 장에는 검증에서 가장 다루기 어려운 결함 유형이 둘 모여 있습니다 — **조용히 통과하는 결함**과 **문맥에 따라 의미가 바뀌는 신호**입니다.

| 조문 | 위반 형태 | 증상 | 잡히는 시점 |
|---|---|---|---|
| §6.1 **토글 수의 합이 짝수** | 어느 시퀀스가 홀수를 남김 | `WDQS/2` 위상이 뒤집힌 채 지속. **마진이 있으면 통과** | **온도·전압이 바뀐 뒤** — 최악의 유형 |
| §6.1 비활성 구간 스트로브 **정적** | 자극이 유휴 중 토글 | ISI·오샘플 | 간헐 |
| §6.1 에지 = **교차점** | checker가 단일 신호 문턱으로 측정 | 타이밍 측정이 미세하게 어긋남 | 마진 없는 조건에서만 |
| §6.1.1 step 4 — **8펄스 미만은 판독 무효** | 무효 구간의 `DERR`을 사용 | 트레이닝이 잘못된 지연에 수렴 | 없음 |
| Table 31 — 트레이닝 중 `DERR`은 **위상 검출기 출력** | monitor가 데이터 오류로 해석 | 트레이닝 내내 **가짜 에러 폭주** | 즉시(잘못된 방향으로) |
| §6.2.1 DBI 판정의 **경계값 4 히스테리시스** | 모델이 직전 상태를 무시 | 전이 수가 정확히 4일 때만 미스매치 | 산발적 |
| §6.2.1 **ECC·SEV는 DBI 대상 아님** | 모델이 반전을 적용 | 데이터가 깨짐 | DBI가 켜진 경우만 |
| §6.2.1.1 리셋 조건에 **`MRS` 포함** | MR을 건드리면 DBI 기준점이 사라짐을 놓침 | `MRS` 직후 첫 read 미스매치 | MR을 바꾸는 시퀀스에서만 |
| §6.2.1.1 **`RDBI` 비활성이어도 프리컨디셔닝** | "껐으니 없다"고 가정 | 첫 read 미스매치 | DBI off 회귀에서만 |
| §6.2.1.1 `DPAR` 초기 상태 **미정의** | 모델이 특정 값을 가정 | 첫 비교에서 랜덤 실패 | 산발적 |

:::caution[조용히 통과하는 결함 — 짝수 토글 위반]
첫 줄은 성격이 다릅니다. **잘못된 상태에서도 정상 동작하기 때문**입니다.

`WDQS/2` 위상이 뒤집혀도 셋업/홀드 마진이 충분하면 데이터는 정확히 잡힙니다. 회귀는 통과합니다. 마진이 줄어드는 조건 — 고온, 저전압, 최고 속도 등급 — 에서만 실패하고, 그때 원인은 **훨씬 앞선 트레이닝 시퀀스**에 있습니다.

기능 검사로는 잡을 수 없습니다. 데이터가 맞기 때문입니다. 잡는 방법은 하나뿐입니다 — **불변식을 직접 감시**하는 것.

그리고 이 불변식은 **개별 시퀀스가 아니라 누적 합**에 대한 조건입니다(§6.1). preamble 하나, postamble 하나, 트레이닝 하나가 각각 짝수일 필요는 없고 **합계가 짝수**면 됩니다. 그래서 단일 property로 표현되지 않고, **시퀀스 경계를 가로지르는 카운터**가 필요합니다.
:::

:::caution[`DERR`은 문맥에 따라 의미가 바뀐다]
Table 31에서 `DERR0`/`DERR1`이 **위상 검출기 출력**으로 재사용됩니다. 같은 핀이 일반 동작에서는 **데이터 오류 신호**입니다.

monitor가 모드를 모르면 트레이닝 내내 `DERR` 상승을 데이터 오류로 보고합니다. 로그가 에러로 뒤덮이고, 그 안에 진짜 오류가 섞여 있어도 보이지 않습니다.

**monitor는 `MR8`의 `WDQS2CK` 상태를 알고 있어야 합니다.** 이는 monitor가 순수 관측자가 아니라 **설정 상태를 참조하는 구성 요소**가 된다는 뜻입니다 — 그 상태를 어디서 받을지가 환경 설계 항목이 됩니다([`hbm_dv` Ch06](../../hbm_dv/06_env_hierarchy/)).

`DERR`은 세 번째 의미도 갖습니다 — [11장](../11_training_ieee1500/)에서 다룹니다.
:::

### 5.2 어떻게 잡는가 — 수단 선택

| 규칙 | 성격 | 수단 | 이유 |
|---|---|---|---|
| 토글 수 합이 짝수 | **누적 불변식** | **monitor의 누적 카운터 + 체크포인트** | 시퀀스 경계를 넘는 합계. SVA 하나로 표현되지 않는다 |
| 유휴 구간 스트로브 정적 | **불변식** | **SVA** | 국소 조건 |
| DBI 판정 | **순차 함수** | **reference model** | 직전 상태에 의존한다. 조합 함수가 아니다 |
| DBI 상태 리셋 네 조건 | **상태 전이** | **reference model** | 같은 모델 안에서 다뤄야 일관된다 |
| 트레이닝 7단계 순서·허용 커맨드 | **절차** | **프로토콜 checker** | 명령 순서에 대한 규칙 |

**① 짝수 토글 — 누적 카운터**

```systemverilog
// §6.1 — preamble/postamble 합 + 트레이닝 토글 합이 짝수여야 한다.
// 개별 시퀀스가 아니라 "합"에 대한 조건이므로 누적해서 센다.
class wdqs_toggle_tracker extends uvm_component;
  `uvm_component_utils(wdqs_toggle_tracker)
  protected int unsigned m_toggles[2];        // DWORD0 / DWORD1

  function void count(int dword, int n);  m_toggles[dword] += n;  endfunction

  // 체크포인트에서만 판정한다. read/write 직전, 트레이닝 종료 시.
  function void checkpoint(string where);
    foreach (m_toggles[d])
      if (m_toggles[d] % 2 != 0)
        `uvm_error("WDQS_PARITY", $sformatf(
          "%s: DWORD%0d 누적 WDQS 토글 %0d 개로 홀수. 내부 WDQS/2 위상이 뒤집힌다 (§6.1)",
          where, d, m_toggles[d]))
  endfunction

  // 리셋에서만 0 으로 돌아간다 — 시퀀스마다 지우면 "합" 조건이 아니게 된다
  function void on_reset();  foreach (m_toggles[d]) m_toggles[d] = 0;  endfunction
endclass
```

`on_reset()` 에서만 지우는 것이 이 클래스의 계약입니다. 시퀀스마다 카운터를 초기화하면 각 시퀀스는 짝수인데 **합계는 홀수**인 경우를 놓칩니다 — 그리고 그것이 §6.1이 금지하는 바로 그 상황입니다.

**② 유휴 구간 스트로브**

```systemverilog
// §6.1 — 비활성 구간에는 _t 는 LOW, _c 는 HIGH 로 정적이어야 한다
a_wdqs_idle_static: assert property (@(posedge ck) disable iff (!rst_n)
    !wdqs_active |-> (wdqs_t == 1'b0 && wdqs_c == 1'b1))
  else `uvm_error("STROBE", "유휴 구간에 WDQS 가 정적 레벨이 아니다 (§6.1)")

a_rdqs_idle_static: assert property (@(posedge ck) disable iff (!rst_n)
    !rdqs_active |-> (rdqs_t == 1'b0 && rdqs_c == 1'b1))
  else `uvm_error("STROBE", "유휴 구간에 RDQS 가 정적 레벨이 아니다 (§6.1)")
```

**③ DBIac — 순차 reference model**

DBI는 조합 함수가 아닙니다. 직전 상태를 들고 있어야 하고, 그 상태는 네 조건에서만 리셋됩니다.

```systemverilog
class dbi_model extends uvm_object;
  `uvm_object_utils(dbi_model)
  protected bit [7:0] m_prev_byte[8];      // 바이트별 직전 데이터 (D7 시드)
  protected bit       m_prev_dbi [8];      // 바이트별 직전 DBI 상태

  // §6.2.1 — 전이 수와 직전 DBI 상태로 판정. 경계값 4 에서 히스테리시스.
  function void read_beat(input bit [7:0] raw[8], output bit [7:0] bus[8],
                                                  output bit       dbi[8]);
    foreach (raw[b]) begin
      int n = $countones(raw[b] ^ m_prev_byte[b]);
      unique case (1)
        (n <= 3) : dbi[b] = 1'b0;
        (n == 4) : dbi[b] = m_prev_dbi[b];    // ← 직전 상태를 그대로 유지 (히스테리시스)
        default  : dbi[b] = 1'b1;             // 5 ~ 8
      endcase
      bus[b]        = dbi[b] ? ~raw[b] : raw[b];
      m_prev_byte[b] = bus[b];                // 버스에 실린 값이 다음 비교의 기준
      m_prev_dbi [b] = dbi[b];
    end
  endfunction

  // §6.2.1.1 — 내부 DBIac 상태가 LOW 로 리셋되는 네 조건. 그 밖에는 유지된다.
  function void reset_dbi_state(dbi_reset_cause_e cause);
    // RESET_n · MRS · write-to-read 턴어라운드 · Self Refresh 종료
    foreach (m_prev_dbi[b]) begin m_prev_dbi[b] = 1'b0; m_prev_byte[b] = 8'h00; end
  endfunction
endclass
```

두 줄이 특히 틀리기 쉽습니다.

- `n == 4` 에서 **`m_prev_dbi[b]` 를 그대로 두는 것**. `1'b0` 으로 쓰면 진리표의 세 번째 행(4 전이 + 직전 HIGH → 반전)이 사라집니다.
- `m_prev_byte[b] = bus[b]` — **반전된 값**이 다음 비교의 기준입니다. `raw[b]`를 저장하면 이후 전이 수 계산이 전부 어긋납니다.

**④ 프리컨디셔닝과 `DPAR` 예외**

```systemverilog
// §6.2.1.1 — RDBI 활성 여부와 무관하게 첫 READ 전 버스를 LOW 로 프리컨디셔닝한다.
// "DBI 를 껐으니 이 동작도 없다" 는 가정이 여기서 깨진다.
function void on_first_read_after_reset(bit rdbi_en);
  foreach (m_prev_byte[b]) m_prev_byte[b] = 8'h00;   // rdbi_en 과 무관
  // DPAR 은 예외 — DBI 계산에 포함되지 않고 프리컨디셔닝되지도 않는다.
  // 초기 상태가 정의되지 않으므로 모델은 "모름"으로 두고 첫 비교에서 제외한다.
  m_dpar_known = 1'b0;
endfunction
```

`DPAR`의 초기 상태가 **정의되지 않는다**는 조문을 모델이 그대로 반영해야 합니다. 특정 값을 가정하면 그 값이 나올 때만 통과하는 **50% 확률의 랜덤 실패**가 됩니다.

### 5.3 무엇을 덮었다고 말할 수 있는가

```systemverilog
covergroup cg_hbm4_clocking_dbi with function sample(
    int n_trans, bit prev_dbi, bit new_dbi, dbi_reset_cause_e cause,
    bit rdbi_en, bit wdbi_en, int toggle_parity, train_stage_e stage);
  option.per_instance = 1;

  // --- DBI 판정 (§6.2.1 진리표) ------------------------------------------
  cp_trans : coverpoint n_trans {
    bins low      = {[0:3]};
    bins boundary = {4};              // 히스테리시스가 걸리는 유일한 값
    bins high     = {[5:8]};
  }
  cp_prev : coverpoint prev_dbi { bins was_low = {0}; bins was_high = {1}; }

  // 경계값 4 를 직전 상태 양쪽에서 겪었는가 — 진리표의 두 행이 여기 있다
  x_hysteresis : cross cp_trans, cp_prev {
    bins b4_prev_low  = binsof(cp_trans.boundary) && binsof(cp_prev.was_low);
    bins b4_prev_high = binsof(cp_trans.boundary) && binsof(cp_prev.was_high);
    ignore_bins rest  = binsof(cp_trans.low) || binsof(cp_trans.high);
  }

  // --- DBI 상태 리셋 네 조건 (§6.2.1.1) ---------------------------------
  cp_reset_cause : coverpoint cause {
    bins reset_n   = {DBI_RST_RESET_N};
    bins mrs       = {DBI_RST_MRS};        // MR 을 건드리면 DBI 기준점이 사라진다
    bins wr_to_rd  = {DBI_RST_TURNAROUND};
    bins sref_exit = {DBI_RST_SREF_EXIT};
  }

  // --- 방향별 활성화 조합 (MR0 OP0/OP1) ---------------------------------
  cp_rdbi : coverpoint rdbi_en { bins off = {0}; bins on = {1}; }
  cp_wdbi : coverpoint wdbi_en { bins off = {0}; bins on = {1}; }
  x_dbi_dir : cross cp_rdbi, cp_wdbi;
  // RDBI off 에서도 프리컨디셔닝은 일어난다 — 그 조합을 겪었는가
  x_precond_off : cross cp_rdbi, cp_reset_cause {
    bins off_after_mrs = binsof(cp_rdbi.off) && binsof(cp_reset_cause.mrs);
  }

  // --- 짝수 토글 불변식 --------------------------------------------------
  cp_parity : coverpoint toggle_parity {
    bins even = {0};
    illegal_bins odd = {1};          // 체크포인트에서 홀수는 나오면 안 된다
  }

  // --- 트레이닝 7단계 (§6.1.1) ------------------------------------------
  cp_train : coverpoint stage { bins s[] = {[1:7]}; }
endgroup
```

**`x_hysteresis` 가 이 장의 중심 축입니다.** 전이 수가 정확히 4인 경우는 랜덤 데이터에서도 꽤 자주 나오지만(8비트 중 4비트 전이), 그것을 **직전 DBI가 LOW일 때와 HIGH일 때 양쪽에서** 겪었는지는 별개입니다. 두 bin이 다 차야 진리표의 두 행이 검증됩니다.

**`cp_reset_cause.mrs` 와 `x_precond_off.off_after_mrs`** 도 잘 빕니다. MR을 바꾸는 시퀀스가 드물고, DBI를 끈 채로 도는 회귀에서 프리컨디셔닝을 확인하는 경우는 더 드뭅니다.

### 5.4 어떻게 자극하는가

**① 짝수 토글 — 위반을 의도적으로 만든다**

정상 회귀에서는 홀수가 나오면 안 됩니다(`illegal_bins`). 그러나 **불변식 감시가 살아 있는지**는 확인해야 합니다.

```systemverilog
// negative 테스트 — 트레이닝에서 홀수 개의 WDQS 펄스를 남기고 종료한다.
// 확인 대상은 DUT 가 아니라 wdqs_toggle_tracker 가 이를 잡는지 여부다.
class seq_odd_toggle_negative extends uvm_sequence #(hbm4_cmd_item);
  `uvm_object_utils(seq_odd_toggle_negative)
  virtual task body();
    enter_wdqs2ck_training();
    drive_wdqs_pulses(9);              // §6.1.1 step 6 이 요구하는 짝수를 어긴다
    exit_wdqs2ck_training();
    // tracker.checkpoint("post-training") 에서 UVM_ERROR 가 나야 정상
  endtask
endclass
```

**② DBI 경계값을 직전 상태 양쪽에서** — `x_hysteresis` 의 두 bin을 채웁니다. 직전 비트를 먼저 만들어 놓고 그 위에 정확히 4비트 전이를 얹습니다.

```systemverilog
// 직전 DBI 를 HIGH 로 만든 뒤(전이 5개 이상), 다음 비트에서 정확히 4개만 전이시킨다
`uvm_do_with(req, { cmd == WR; data[0] == 8'h00; })
`uvm_do_with(req, { cmd == WR; $countones(data[0] ^ 8'h00) >= 5; })  // prev_dbi <= HIGH
`uvm_do_with(req, { cmd == WR; $countones(data[0] ^ prev_bus) == 4; })  // 경계값
```

**③ 네 리셋 조건을 각각** — `RESET_n` · `MRS` · write-to-read 턴어라운드 · Self Refresh 종료. 각각 직후에 **read를 발행**해야 리셋이 실제로 반영됐는지 보입니다. 리셋만 하고 read를 안 하면 모델과 DUT의 차이가 드러나지 않습니다.

**④ `RDBI` 비활성 상태의 첫 read** — DBI를 끈 회귀에서도 프리컨디셔닝이 일어납니다. DBI off 프로파일에서 리셋 직후 첫 read를 반드시 포함시켜야 합니다.

**⑤ 트레이닝 절차의 경계** — §6.1.1의 두 지점이 directed 대상입니다.

- **step 4** — WDQS 펄스 **8개 미만**에서 정지하고 `DERR`을 읽는 시퀀스. 판독이 무효인 구간을 환경이 무효로 다루는지 확인합니다.
- **step 1** — 트레이닝 모드에서 허용 커맨드(`REFab`·`REFpb`·`RFMab`·`RFMpb`·`RNOP`·`CNOP`·종료 `MRS`) **밖의 커맨드**를 발행하는 negative 시퀀스.

refresh는 이 모드에서 **허용되지만 권장되지 않습니다**(전류 스파이크). 자극 정책을 정해 두어야 합니다 — 권장되지 않는 조합을 회귀에서 돌릴 것인가. 규격이 금지하지 않았으므로 DUT는 동작해야 하지만, 트레이닝 정확도는 보장되지 않습니다. **정상 회귀에서는 제외하고 별도 스트레스 테스트로 두는 편**이 결과 해석에 유리합니다.

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

## 핵심 정리

- **스트로브 주파수 = 커맨드 클럭의 2배**. 그래서 **WDQS 클럭 트리에 reset 타입 분주기**가 요구되며, 내부 회로는 절반 속도로 동작한다.
- **CK와 WDQS는 같은 PLL**에서, **RDQS는 WDQS**에서 생성된다. 내부 `WDQS/2` 전이 **방향은 벤더 선택**이다.
- ⚠️ **preamble + postamble + 트레이닝 토글의 합은 짝수여야 한다.** 그 대가로 HBM4는 **READ/WRITE 전 별도 동기화가 불필요**하다. 위반해도 **마진이 있으면 데이터는 맞으므로 기능 검사로는 잡히지 않는다** — 불변식을 직접 감시하는 것이 유일한 수단이고, 카운터는 **시퀀스가 아니라 리셋에서만** 지운다.
- 분주기는 **Self Refresh 종료 · 전원 인가 · Power-down 종료** 시 초기화된다 — 컨트롤러의 패리티도 함께 리셋해야 한다.
- **비활성 구간 스트로브는 정적**(`_t` LOW, `_c` HIGH)이며, WDQS는 **ISI 저감을 위해 동작 전에 미리 토글**한다.
- 에지는 **차동 교차점**으로 정의된다.
- WDQS-to-CK 트레이닝은 **`tDQSS`를 만족하면 불필요**하고, **더 좁히려는 시도는 이득이 없다**. 판정 기준은 절대값이 아니라 **early→late 전이**다.
- 트레이닝 중 **refresh는 허용되나 전류 스파이크로 결과를 해칠 수 있다** — 기대값을 세우기 어려우므로 정상 회귀에서 격리한다.
- 트레이닝 모드의 **`DERR`은 데이터 오류가 아니라 위상 검출기 출력**이다(Table 31). 모드를 모르는 monitor는 가짜 에러로 로그를 덮어 진짜 오류를 가린다.
- DBIac은 **바이트 단위**이며 read/write **독립 제어**(`MR0` OP1/OP0)다. 전이 수 **4에서 직전 상태에 따라 갈리는 히스테리시스**가 있어 **조합 함수가 아니라 순차 모델**이어야 한다. 다음 비교의 기준은 `raw`가 아니라 **버스에 실린 반전 후 값**이다.
- **ECC·SEV·`DPAR`은 DBIac 대상이 아니다.** `DPAR`은 프리컨디셔닝도 되지 않고 초기 상태가 미정의다.
- 내부 DBI 상태는 **`RESET_n` 비어서트 · `MRS` 수신 · write→read 턴어라운드 · Self Refresh 종료**에 LOW로 리셋된다. **`RDBI` 비활성이어도 첫 READ 전 프리컨디셔닝은 수행된다.**
- 커버리지의 중심은 **전이 수 4 × 직전 DBI 상태**의 cross다. 두 bin이 다 차야 진리표의 두 행이 검증된다. 네 리셋 조건은 각각 **직후에 read를 발행**해야 반영 여부가 드러난다.

## Further Reading

- **규격**: JESD270-4 §6.1 Clocking Overview (Figure 9–11) · §6.1.1 WDQS-to-CK Alignment Training (Table 31, Figure 12) · §6.2 DBIac (Table 32, Figure 13–16)
- **다음 장**: [06 — Row 커맨드](../06_row_commands/)
- **관련**: [04 — Mode Register](../04_mode_registers/) (`MR0` DBI, `MR8` WDQS2CK) · [11 — 트레이닝과 IEEE 1500](../11_training_ieee1500/) (DCA·DCM)
- **이해도 점검**: [퀴즈](../quiz/05_clocking_dbi_quiz/)
