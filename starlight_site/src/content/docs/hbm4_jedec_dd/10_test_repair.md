---
title: "10 — 테스트와 복구"
description: JESD270-4 §6.7·6.8·6.13 · Lane remapping 3계층, MISR/LFSR 루프백, Self Repair
---

:::tip[🎯 Learning Objectives]
이 모듈을 마치면:

- **Explain** lane remapping이 시프트 구조로 동작하는 방식과 여분 레인이 하는 역할을 설명한다.
- **Identify** remapping이 불가능한 신호들을 지목하고 왜 그것들이 제외되는지 판단한다.
- **Derive** DWORD 40비트·AWORD 38비트 MISR 폭을 신호 수와 샘플링 구조로 유도한다.
- **Sequence** Self Repair의 self-test → auto-repair 흐름과 채널·SID 순회 요구를 정리하고, **종료 조건과 최대 시도 횟수**를 갖춘 반복 루프로 구현한다.
- **Evaluate** 한 번에 한 레인만 복구 가능하다는 제약이 **전류 제약**이라 디지털 시뮬로 검증할 수 없음을 판단하고, 자극 측 프로토콜 검사로 대체한다.
- **Construct** MISR reference 모델을 만들고, 서명 일치가 왜 무결의 증명이 아닌지 설명한다.
:::

:::note[Prerequisites]
- [03 — 초기화·리셋·전원](../03_init_reset_power/) — lane repair가 초기화 시퀀스에 끼어드는 지점, soft/hard 덮어쓰기 위험
- [01 — 규격 지형도](../01_landscape_organization/) — 여분 신호(`RD[3:0]`, 여분 주소, `RM`)의 존재
:::

:::caution[인용 고지]
본 장은 **JESD270-4 (2025-04, WIP draft)** §6.7·§6.8·§6.13을 근거로 **요약·재구성**한 것입니다. remapping 표와 그림은 옮기지 않고 **구조와 규칙만** 서술합니다. 정밀 인코딩은 **JEDEC 원문 우선**.
:::

---

## 1. 왜 복구 기능이 필수인가

[01장](../01_landscape_organization/)에서 스택 하나가 요구하는 신호 마이크로범프를 계산했습니다 — **약 3,896개**. 이 규모에서는 조립 후 일부 연결이 불량일 확률이 통계적으로 무시할 수 없습니다.

규격이 목적을 명시합니다.

> HBM4 DRAM은 **SiP 조립 수율을 개선하고 HBM4 스택의 기능을 회복**하기 위해 interconnect lane remapping을 지원한다. — §6.7 (요약)

즉 lane repair는 "고장 대응"이 아니라 **양산 수율 확보 수단**입니다. 그래서 규격이 여분 신호(`RD[3:0]`, 여분 주소, `RM`)를 처음부터 배정해 두었습니다.

## 2. Lane Remapping — 시프트로 밀어내기

### 기본 구조

동작 원리는 단순합니다. **불량 레인을 비활성화하고, 그 뒤의 신호들을 한 칸씩 밀어, 마지막을 여분 레인이 받습니다.**

```d2
direction: right

NORMAL: "정상 (No Repair)" {
  style.fill: "#e8f5e9"; style.font-color: "#0A0F25"
  n: "위치1: R1   위치2: R2   위치3: R3   …   위치10: R9   RA: (미사용)"
}

BROKEN: "위치2 불량 → Repair" {
  style.fill: "#ffebee"; style.font-color: "#0A0F25"
  b: "위치1: R1   위치2: XX   위치3: R2   …   위치10: R8   RA: R9"
}

NOTE: "불량 레인의 입력 버퍼는 꺼지고\n여분 범프(RA)의 버퍼가 켜진다\n→ 모든 기능이 보존된다" {
  style.fill: "#fff8e1"; style.font-color: "#0A0F25"
}

NORMAL -> BROKEN: "SOFT/HARD_LANE_REPAIR"
BROKEN -> NOTE
```

레지스터 인코딩은 **불량 레인이 나르던 신호를 지시**하며, 기본값 `1111`은 "복구 없음"입니다.

> 레인이 remapping된 뒤, **불량 레인의 입력 버퍼는 꺼지고 여분 범프(RA)의 입력 버퍼가 켜진다. 모든 기능이 보존된다.** — §6.7.1 (요약)

### 세 계층

remapping은 세 영역에서 독립적으로 이뤄집니다.

| 계층 | 여분 자원 | 범위 |
|---|---|---|
| **AWORD** | **채널당 여분 레인 1개** | row 커맨드 버스 **또는** column 커맨드 버스 중 **하나** |
| **DWORD** | 더블 바이트당 여분 레인 (`RD`) | 데이터 버스 |
| **WSO** | 여분 WSO (`RM`) | IEEE 1500 직렬 출력 |

**AWORD와 DWORD remapping은 채널마다 독립**입니다.

`WSO`는 배치가 특이합니다 — **`WSO0`~`WSO15`는 채널 1**, **`WSO16`~`WSO31`은 채널 17**에 연관됩니다. 그리고 `WIR[13:8]`이 `01h`(채널 1) 또는 `11h`(채널 17)일 때 **WDR 길이가 45**, 그 외에는 **40**입니다.

### AWORD — 하나뿐인 여분 레인

채널당 여분 AWORD 레인이 **하나**이므로, **row 버스와 column 버스를 통틀어 한 레인만** 복구할 수 있습니다.

- **`APAR`과 `ARFU`는 column 커맨드 버스 복구에 포함**됩니다([06장](../06_row_commands/)에서 본 두 신호가 여기서 복구 대상이 됩니다).
- **`CK_c`, `CK_t`, `AERR`는 remapping할 수 없습니다.**

:::tip[왜 클럭과 AERR은 제외인가]
`CK_t`/`CK_c`는 **차동 쌍**이고 나머지 레인들과 전기적 특성이 다릅니다. 시프트 구조에 끼워 넣으면 클럭 무결성이 깨집니다.

`AERR`는 **출력**이고, 무엇보다 **복구 과정 자체를 관측하는 데 쓰이는 신호**입니다. 그것이 고장 났다면 복구 결과를 확인할 방법이 없어집니다.

일반 원리로 정리하면 — **자기 자신을 관측·구동하는 데 필요한 신호는 복구 대상이 될 수 없습니다.**
:::

### DWORD — 더블 바이트 단위

데이터 버스는 **더블 바이트당 불량 레인 하나**를 복구합니다. 인접한 두 바이트가 쌍을 이루며(`DQ[15:0]`, `DQ[31:16]`, `DQ[47:32]`, `DQ[63:48]`), **각 더블 바이트는 독립적으로 처리**됩니다.

여기에 프로그래밍 규칙이 하나 붙습니다.

> 더블 바이트 안에서 **정상인 바이트에 대해서는 `1111b`를 프로그램해야** 하며, 다른 바이트의 불량 레인은 표에 따라 인코딩한다. — §6.7.2 (요약)

즉 **쌍 단위로 값을 써야** 하고, 손대지 않을 쪽에도 "복구 없음"을 명시해야 합니다.

복구 후 동작도 AWORD와 다릅니다 — 데이터 버스는 양방향이므로 **불량 레인의 입력 버퍼가 꺼지고 출력 드라이버가 tri-state** 되며, **여분 레인(`RD`)의 입력 버퍼가 켜지고 출력 드라이버가 활성화**됩니다.

보존되는 것과 제외되는 것도 명확합니다.

- **DBI 기능은 보존**됩니다 (MR의 DBI 설정이 활성인 한).
- **Data Parity 기능에는 영향이 없습니다.**
- **`WDQS_c`/`WDQS_t`, `RDQS_c`/`RDQS_t`, `PAR`, `DERR`는 remapping할 수 없습니다.**

제외 목록의 논리가 AWORD와 같습니다 — 스트로브는 차동 쌍이고, `PAR`/`DERR`는 무결성 판정 경로입니다.

그리고 read 시 여분 레인의 드라이버 활성 타이밍이 **바이트의 홀짝을 따릅니다.**

> `RD0`과 `RD2`는 **짝수 바이트** 안에 있어 첫 유효 데이터 비트보다 **1 WDQS 사이클 앞서** 활성화되고, `RD1`과 `RD3`은 **홀수 바이트** 안에 있어 **2 WDQS 사이클 앞서** 활성화된다. — §6.7.2 (요약)

[07장](../07_column_commands/)에서 본 *"홀수 바이트는 2 RDQS 펄스, 짝수 바이트는 1 펄스 앞서 구동"* 과 정확히 같은 규칙입니다. 여분 레인도 **자신이 속한 물리 바이트의 타이밍을 그대로 따릅니다.**

### ⚠️ 한 번에 하나만

이 절에서 초기화 펌웨어에 가장 큰 제약입니다.

> **관련 회로의 전류 제약을 제한하기 위해, 한 번에 단일 채널 또는 WSO의 불량 레인 하나만 복구할 수 있다.** 여러 레인을 복구하려면 각 불량 레인에 대한 복구 벡터를 **순차적으로 시프트 인**해야 하며, **다른 모든 레인 복구 설정은 `Fh`로** 두고 **각각의 실제 레인 복구를 별도의 `UpdateWR` 이벤트로 개시**해야 한다. — §6.7 (요약)

:::caution[N개 불량 = N번의 UpdateWR]
불량 레인이 3개면 복구 절차를 3번 반복해야 합니다. 한 번에 벡터를 몰아 넣으면 **전류 제약을 위반**합니다.

```
for 각 불량 레인:
    다른 모든 레인 설정 = Fh
    이 레인의 복구 벡터를 시프트 인
    UpdateWR 이벤트 발생          ← 여기서 실제 복구가 일어난다
```

[03장](../03_init_reset_power/)에서 본 **"soft가 hard를 덮어쓴다"** 규칙과 합치면 초기화 펌웨어의 절차가 완성됩니다.

```
1. hard lane repair 데이터를 읽는다
2. 새로 필요한 repair를 병합한다
3. 병합된 목록을 한 레인씩, UpdateWR로 나눠 적용한다
4. BYPASS (또는 WRST_n LOW)로 정상 모드 복귀
```
:::

### 발행 시점 제약

> `SOFT_LANE_REPAIR`와 `HARD_LANE_REPAIR` 명령은 **장치 초기화의 일부로서, 정상 메모리 동작이 시작되기 전에만** 발행될 수 있다 — 예를 들어 **CK 클럭이 토글을 시작하기 전에.** — §6.7 (요약)

[03장](../03_init_reset_power/)의 초기화 5단계(CK 토글 시작)보다 **앞**이어야 합니다. 정상 동작 중에는 레인 구성을 바꿀 수 없습니다.

그리고 영속성 선택지가 있습니다.

> HBM4 DRAM은 **스택에서 전원이 완전히 제거되어도 remapping된 레인 정보를 유지하도록 프로그램될 수 있다.** — §6.7

이것이 `SOFT_LANE_REPAIR`(휘발)와 `HARD_LANE_REPAIR`(퓨즈, 영속)의 차이입니다.

## 3. MISR/LFSR 루프백 — 링크를 시험하는 회로

### 목적과 배치

> MISR/LFSR 회로가 HBM4의 **AWORD와 DWORD I/O 블록 안에** 정의된다. 이 회로들은 **호스트와 HBM4 장치 사이의 링크를 테스트하고 트레이닝**하기 위한 것이다. — §6.8 (요약)

메모리 배열이 아니라 **링크(I/O)** 를 겨냥한 기능입니다.

### 폭을 유도해 보기

규격이 제시한 숫자들이 신호 구성에서 그대로 나옵니다.

**DWORD — 바이트당 40비트**

```
한 바이트의 신호 : DQ 8개 + DBI 1개 + ECC/SEV 1개  = 10 신호
샘플링          : WDQS 2사이클 × Rise/Fall        =  4 비트/신호
──────────────────────────────────────────────────────────────
                                  10 × 4          = 40 비트  ✅
```

`Q0`~`Q3`가 각 신호의 반 WDQS 사이클을 가리키며, **BL0~BL3이 앞 두 WDQS 사이클의 Q0~Q3에, BL4~BL7이 다음 두 사이클의 Q0~Q3에** 대응합니다.

**AWORD — 38비트**

```
신호 : R[9:0] 10개 + C[7:0] 8개 = 18 커맨드 비트  + ARFU 1개 = 19 신호
샘플 : CK DDR Rise/Fall                          =  2 비트/신호
──────────────────────────────────────────────────────────────
                          19 × 2                  = 38 비트  ✅
```

**여기서도 `ARFU`가 포함됩니다.** [06장](../06_row_commands/)·[08장](../08_parity/)에 이어 세 번째입니다 — 진리표에 없는 신호가 패리티에도, MISR에도 참여합니다.

**읽어내는 양**

```
바이트 4개 × 40비트 = 160비트 (DWORD 1개)
DWORD 2개           = 320비트  ← IEEE 1500 DWORD_MISR로 직렬 시프트 아웃  ✅
AWORD_MISR          =  38비트
```

MISR/LFSR 회로는 **바이트 간에 독립적으로 동작**합니다.

### 네 가지 모드

규격은 "MISR modes"를 네 모드의 총칭으로 씁니다.

| 모드 | 성격 |
|---|---|
| **LFSR mode** | 패턴 **생성** |
| **Register mode** | 값을 직접 적재·판독 |
| **MISR mode** | 수신 데이터를 **서명(signature)으로 압축** |
| **LFSR Compare mode** | 생성 패턴과 수신 데이터를 **비교** |

`MR7`이 DWORD 쪽 제어(**DWORD MISR Control**, **DWORD Read Mux**, **DWORD Loopback Control**)를 담당하고([04장](../04_mode_registers/)), IEEE 1500 쪽에서는 `AWORD_MISR`·`DWORD_MISR`·`MISR_MASK`·`READ_LFSR_COMPARE_STICKY`·`AWORD_MISR_CONFIG` 명령이 관여합니다.

다항식은 **Galois 형 MISR/LFSR** 구조이며, 규격은 `f(x) = X⁴ + X³ + 1`을 **예시로만** 제시하고 실제 정의는 별도 절에서 규정합니다.

:::tip[MISR가 검증에 주는 것]
MISR는 긴 데이터 스트림을 **고정 폭 서명으로 압축**합니다. 호스트가 알려진 패턴을 보내고 장치의 MISR 값을 읽어 기대값과 비교하면, **전 비트를 하나씩 확인하지 않고도** 링크 무결성을 판정할 수 있습니다.

대가는 **압축 손실**입니다 — 서로 다른 오류가 같은 서명을 낼 수 있습니다(aliasing). 그래서 `LFSR Compare mode`처럼 **실시간 비교** 경로가 따로 있고, 그 결과를 `READ_LFSR_COMPARE_STICKY`로 읽습니다. **sticky**라는 이름이 말하듯, 한 번 발생한 불일치는 남습니다.
:::

## 4. Self Repair — 배열 결함을 스스로 고친다

lane repair가 **연결**을 고친다면, Self Repair는 **배열 자체**의 하드 결함을 고칩니다.

> HBM4 DRAM은 **초기화 과정 중에 DRAM의 결함을 스캔하고 복구**함으로써 **SiP 조립 수율을 개선하거나 높은 시스템 신뢰성을 달성**하기 위해 self repair를 지원한다. — §6.13 (요약)

### 두 단계

```
① self-test    : 벤더 지정 패턴으로 하드 결함을 식별
        ↓
② auto-repair  : ①에서 나온 불량 주소를 자동 복구
                  (복구 가능한 주소 개수는 벤더 지정)
```

`REP_TYPE` 필드(`SELF_REP` 명령의 bits[3:2])를 `11b`로 두면 첫 단계인 self-test가 시작됩니다.

### 순회 구조 — 채널과 SID

한 번에 전체를 처리하지 못합니다.

- 명령은 **8채널 또는 16채널 단위**로 동작합니다. `WIR[13:8]`을 `38h`/`39h`로 두면 절반(16채널), `3Ah`~`3Dh`로 두면 1/4(8채널)을 선택합니다.
- **모든 그룹에 대한 병렬 동작은 지원되지 않습니다.**
- **한 번에 하나의 SID만** 처리하며, `SID_SELECT` 필드(bits[5:4])로 지정합니다.

따라서 전 채널·전 SID를 덮으려면 **`SID 수 × 그룹 수`** 만큼 명령을 반복해야 합니다. 8채널 그룹 기준으로 4-high는 4회, 8-high는 8회, 12-high는 12회입니다(Table 82).

:::caution[스택이 높을수록 초기화가 길어진다]
Self Repair 횟수가 **SID 수에 비례**합니다. 16-high 구성은 4-high의 네 배를 돌아야 합니다.

[03장](../03_init_reset_power/)에서 초기화 시간을 `tINIT3`(4 ms)가 지배한다고 했는데, **Self Repair를 수행하면 그 위에 self-test + auto-repair 시간이 SID 수만큼 곱해져 얹힙니다.**

그리고 병렬화가 **규격상 금지**되어 있으므로 이 시간을 줄일 방법이 없습니다.

검증에서는 이것이 **회귀 시간 문제**가 됩니다. 전 SID × 전 그룹을 도는 테스트는 스택이 높을수록 느려지고, 그렇다고 생략하면 `cp_sid` 가 부분만 차서 **미복구 SID가 있는 채로 회귀가 통과**합니다. 기능 회귀와 전용 테스트를 나누는 것이 현실적인 해법입니다 — 5.4 ⑥.
:::

### 발행 조건과 진행 관측

- `SELF_REP`은 **장치가 제대로 초기화된 뒤 — 구체적으로 `tINIT3`가 충족되고 DRAM이 all-banks-idle 상태일 때 — 언제든** 발행할 수 있습니다.
- 선택된 채널들이 **all-banks-idle 상태**여야 합니다.
- 호스트는 `SR_PROGRESS` 필드를 **폴링**해 진행 상황(self-test 진행 중 / auto-repair 진행 중 / 완료 / 미실행)을 확인합니다.
- **그동안 `SELF_REP` 명령이 WIR에 유지되어야** 합니다.
- 클럭 소스는 `WRCK`(직접 또는 기준)일 수도, **`WRCK`와 I/O 기능 클럭 양쪽으로부터 독립적인 내부 클럭 모드**일 수도 있습니다.
- `SELFR_REF_RATE` 필드(bits[7:6])로 **온도 보상 refresh 속도**를 호스트가 제어해야 합니다.

### 결과 판정

`SELF_REP_RESULTS` 명령으로 **SID별** 결과를 읽습니다. 보고 항목은 네 가지입니다.

1. **결함이 남아 있음**
2. **복구 불가능한 결함이 남아 있음**
3. **`SELF_REP`을 다시 실행해야 함**
4. 초기화 이후 실행되지 않았거나, 최근 실행 후 결함 없음

3번이 있다는 것은 **한 번의 실행으로 끝나지 않을 수 있다**는 뜻입니다. 초기화 펌웨어는 **반복 실행 루프**를 가져야 하고, 종료 조건과 최대 시도 횟수를 정해야 합니다.

## 🔬 검증 적용

### 5.1 무엇이 깨질 수 있는가

이 장의 기능들은 **정상 동작 경로 밖**에 있습니다. 기능 회귀를 아무리 돌려도 lane repair와 Self Repair는 한 번도 실행되지 않을 수 있고, 그 상태로 "전 항목 통과"가 나옵니다.

| 조문 | 위반 형태 | 증상 | 잡히는 시점 |
|---|---|---|---|
| §6.7 — **한 번에 한 레인** (전류 제약) | 여러 복구 벡터를 한 `UpdateWR`로 | **전류 제약 위반 — 디지털 시뮬에 안 나타남** | **디지털 회귀로는 불가** |
| §6.7.2 — 더블 바이트 **쌍 단위**, 정상 쪽에 `1111b` | 한쪽만 프로그램 | 멀쩡한 레인이 잘못 매핑 | 데이터 미스매치 |
| §6.7.1/6.7.2 — **복구 불가 신호 목록** | `CK`·스트로브·`AERR`·`PAR`·`DERR`에 복구 시도 | 무시되거나 미정의 | 없음 |
| §6.7 — 발행은 **CK 토글 이전** | 정상 동작 중 발행 | 미정의 | 없음 |
| §6.7 — soft(휘발) vs hard(퓨즈) | 구분 없이 처리 | **전원 사이클 후 결과가 다름** | 전원 사이클 시나리오 |
| §6.7.2 — `RD0`/`RD2` 짝수, `RD1`/`RD3` 홀수 타이밍 | 여분 레인을 일괄 처리 | 복구된 레인만 위상이 어긋남 | 복구 후 데이터 |
| §6.8 — MISR는 **압축**이다 | 서명 일치를 "무결"로 해석 | aliasing된 오류를 통과 | **원리적 한계** |
| §6.8 — `READ_LFSR_COMPARE_STICKY` | sticky 성질을 모름 | 이전 테스트의 불일치를 현재 것으로 오독 | 순서 의존 |
| §6.13 — **병렬 동작 미지원** | 그룹 병렬 시도 | 미정의 | 없음 |
| §6.13 — `SID 수 × 그룹 수` 순회 | 일부만 수행 | **미복구 영역이 남음** | 없음 |
| §6.13 — "재실행 필요" 결과 | 반복 루프 없음 | 결함이 남은 채 진행 | 없음 |
| §6.13 — 폴링 중 **`SELF_REP`이 WIR에 유지** | 다른 명령 발행 | 동작 중단 | 즉시 |

:::caution[디지털 시뮬로 검증할 수 없는 항목 — 두 번째 사례]
"한 번에 한 레인" 제약의 근거는 **전류**입니다(§6.7). 여러 레인을 동시에 복구하면 관련 회로의 순간 전류가 제약을 넘습니다.

디지털 시뮬레이션에서 이것은 **관측되지 않습니다.** 여러 벡터를 한 번에 시프트 인해도 DUT 모델은 정상적으로 복구를 수행할 것이고, 검사는 통과합니다. [03장](../03_init_reset_power/)의 전원 램프 부등식과 같은 유형입니다.

따라서 이 항목은 **DUT 검증이 아니라 자극 측 프로토콜 검사**입니다. IEEE 1500 명령 스트림을 보고 **`UpdateWR` 사이에 복구 벡터가 하나씩만 들어갔는지**를 확인하는 checker로 잡습니다.

V-Plan에 이 행을 적을 때 "DUT가 다중 복구를 거부하는지 확인"이라고 쓰면 틀립니다. 규격은 거부를 요구하지 않고, 애초에 거부할 수단도 없습니다.
:::

:::caution[MISR 일치는 무결의 증명이 아니다]
MISR는 긴 스트림을 고정 폭 서명으로 **압축**합니다. 압축이므로 **서로 다른 입력이 같은 서명을 낼 수 있습니다**(aliasing).

DWORD 40비트 서명 기준으로 무작위 오류가 통과할 확률은 대략 `2⁻⁴⁰`이고, 실용적으로는 충분히 낮습니다. 그러나 검증에서 주의할 것은 무작위 오류가 아니라 **구조적 오류**입니다 — 특정 stuck-at 패턴이나 주기적 오류는 다항식의 성질에 따라 서명에 흔적을 남기지 않을 수 있습니다.

그래서 규격이 **`LFSR Compare mode`** 를 따로 둡니다. 이쪽은 압축이 아니라 **실시간 비교**이고, 결과는 `READ_LFSR_COMPARE_STICKY`로 읽습니다.

| 수단 | 성격 | 강도 |
|---|---|---|
| MISR mode | 서명 압축 | 빠르지만 aliasing 가능 |
| LFSR Compare mode | 실시간 비교 | 강하지만 비교 회로가 필요 |

검증 전략은 **둘을 병행**하는 것입니다. MISR로 빠르게 훑고, 의심 구간은 Compare mode로 확인합니다. **MISR만으로 "링크 무결"을 결론짓지 않습니다.**

그리고 **sticky**라는 이름에 주의하세요 — 한 번 선 불일치는 명시적으로 지우기 전까지 남습니다. 테스트마다 지우지 않으면 **이전 테스트의 실패를 현재 테스트의 것으로 읽게** 됩니다([09장](../09_ecc_ecs_sev/)의 ECS 로그와 같은 유형의 문제입니다).
:::

### 5.2 어떻게 잡는가 — 수단 선택

| 규칙 | 성격 | 수단 | 이유 |
|---|---|---|---|
| 한 레인씩 · 쌍 단위 · 시점 | **명령 스트림 절차** | **프로토콜 checker** | 검증 대상이 펌웨어 절차다 |
| 복구 불가 신호 목록 | **불변식** | **코드로 고정한 목록 + 검사** | 목록이 흩어지면 반드시 빠진다 |
| MISR 서명 | **함수** | **reference MISR 모델** | 같은 다항식으로 독립 계산 |
| Self Repair 순회·종료 | **절차 + 종료 조건** | **시퀀스 + 최대 시도 제한** | 무한 루프 위험이 있다 |

**① Lane repair 절차 — [03장](../03_init_reset_power/) checker의 확장**

```systemverilog
// §6.7 — 복구 벡터는 한 번에 하나. 각각 별도의 UpdateWR 로 개시한다.
// 다른 레인 설정은 Fh(복구 없음)로 둔다.
class lane_repair_seq_chk extends uvm_subscriber #(ieee1500_item);
  `uvm_component_utils(lane_repair_seq_chk)
  protected int m_pending_repairs;      // 이번 UpdateWR 로 개시될 복구 수
  protected bit m_ck_toggling;

  function void write(ieee1500_item t);
    case (t.instr)
      SOFT_LANE_REPAIR, HARD_LANE_REPAIR : begin
        // §6.7 — 정상 동작 시작 전에만 발행 가능 (CK 토글 이전)
        if (m_ck_toggling)
          `uvm_error("LANE_REPAIR",
            "CK 토글 이후에 lane repair 명령을 발행했다 (§6.7)")
        m_pending_repairs = count_non_Fh_fields(t.wdr_data);
      end

      UPDATE_WR : begin
        // 전류 제약 때문에 한 번에 하나만 (§6.7).
        // 디지털 시뮬에서 DUT 는 여러 개도 처리하므로, 잡는 쪽은 여기뿐이다.
        if (m_pending_repairs > 1)
          `uvm_error("LANE_REPAIR", $sformatf(
            "한 UpdateWR 에 복구 벡터 %0d 개. 전류 제약상 하나씩 개시해야 한다 (§6.7)",
            m_pending_repairs))
        m_pending_repairs = 0;
      end
      default: ;
    endcase
  endfunction
endclass
```

**② 복구 불가 신호 — 목록을 한곳에 고정한다**

```systemverilog
// §6.7.1 / §6.7.2 — remapping 대상에서 제외되는 신호.
// 원리: 자기 자신을 관측·구동하는 데 필요한 신호는 복구 대상이 될 수 없다.
typedef enum {
  SIG_CK_T, SIG_CK_C,           // 차동 클럭 쌍 (AWORD)
  SIG_AERR,                     // 복구 결과를 관측하는 신호 자체
  SIG_WDQS_T, SIG_WDQS_C,       // 차동 스트로브 쌍 (DWORD)
  SIG_RDQS_T, SIG_RDQS_C,
  SIG_PAR, SIG_DERR             // 무결성 판정 경로
} non_repairable_e;

function automatic bit is_repairable(hbm4_signal_e sig);
  return !(sig inside {SIG_CK_T, SIG_CK_C, SIG_AERR,
                       SIG_WDQS_T, SIG_WDQS_C, SIG_RDQS_T, SIG_RDQS_C,
                       SIG_PAR, SIG_DERR});
endfunction
```

이 목록을 checker와 자극 생성기가 **공유**해야 합니다. 자극이 복구 불가 신호를 대상으로 고르면 그 자체가 자극 버그이고, 목록이 두 곳에 있으면 언젠가 갈립니다.

**③ MISR reference 모델**

```systemverilog
// §6.8 — Galois 형 MISR. 규격의 예시 다항식은 f(x)=X⁴+X³+1 이며
// 실제 정의는 별도 절에 있다. 폭은 DWORD 40 / AWORD 38.
class misr_model #(parameter int W = 40) extends uvm_object;
  `uvm_object_utils(misr_model#(W))
  protected bit [W-1:0] m_sig;
  bit [W-1:0]           poly;            // 구성에서 받는다 — 상수로 박지 않는다

  function void reset(); m_sig = '0; endfunction

  function void absorb(bit [W-1:0] data);
    bit msb = m_sig[W-1];
    m_sig = (m_sig << 1) ^ data;
    if (msb) m_sig ^= poly;              // Galois 피드백
  endfunction

  function bit [W-1:0] signature(); return m_sig; endfunction
endclass
```

`poly` 를 **구성에서 받는 것**이 요점입니다. 규격이 제시한 것은 **예시**이고 실제 다항식은 별도 규정이므로, 상수로 박으면 다른 정의에서 전부 틀립니다.

**④ Self Repair 순회 — 종료 조건이 필수다**

```systemverilog
// §6.13 — SELF_REP_RESULTS 가 "재실행 필요" 를 돌려줄 수 있다.
// 종료 조건과 최대 시도 횟수가 없으면 테스트가 끝나지 않을 수 있다.
task automatic run_self_repair_all();
  foreach (sid_list[s]) begin
    foreach (group_list[g]) begin        // 병렬 동작은 지원되지 않는다 (§6.13)
      int attempts = 0;
      do begin
        issue_self_rep(sid_list[s], group_list[g]);
        poll_sr_progress();              // 이 동안 SELF_REP 이 WIR 에 유지되어야 한다
        attempts++;
        if (attempts > MAX_SELF_REP_ATTEMPTS) begin
          `uvm_error("SELF_REPAIR", $sformatf(
            "SID %0d 그룹 %0d 에서 %0d 회 시도 후에도 재실행 요구가 계속된다",
            sid_list[s], group_list[g], attempts))
          break;
        end
      end while (read_self_rep_results(sid_list[s]) == SR_RERUN_REQUIRED);
    end
  end
endtask
```

### 5.3 무엇을 덮었다고 말할 수 있는가

이 장의 coverage는 **"이 기능이 한 번이라도 실행됐는가"** 에서 시작합니다. 기능 회귀만 도는 환경에서는 전부 0입니다.

```systemverilog
covergroup cg_hbm4_test_repair with function sample(
    repair_layer_e layer, int n_lanes_repaired, int double_byte, int rd_lane,
    persist_e persist, misr_mode_e mmode, sr_result_e sr, int sid, bit sticky_cleared);
  option.per_instance = 1;

  // --- 어느 복구 계층을 실행했는가 ---------------------------------------
  cp_layer : coverpoint layer {
    bins none        = {REPAIR_NONE};
    bins aword       = {REPAIR_AWORD};    // 채널당 여분 레인 1개
    bins dword       = {REPAIR_DWORD};
    bins self_repair = {REPAIR_ARRAY};    // §6.13 — 배열 결함
  }

  // --- 한 번에 하나 (§6.7) — 복수 복구를 순차로 처리해 봤는가 -------------
  cp_n_lanes : coverpoint n_lanes_repaired {
    bins one  = {1};
    bins two  = {2};
    bins many = {[3:$]};                  // N 개면 UpdateWR 도 N 번
  }

  // --- DWORD 는 더블 바이트 4쌍 (§6.7.2) ---------------------------------
  cp_double_byte : coverpoint double_byte { bins db[] = {[0:3]}; }
  // 여분 레인의 타이밍은 물리 바이트의 홀짝을 따른다
  cp_rd_lane : coverpoint rd_lane {
    bins even_byte = {0, 2};              // RD0·RD2 — 1 WDQS 사이클 선행
    bins odd_byte  = {1, 3};              // RD1·RD3 — 2 WDQS 사이클 선행
  }

  // --- 영속성 (§6.7) ------------------------------------------------------
  cp_persist : coverpoint persist {
    bins soft = {REPAIR_SOFT};            // 휘발 — 전원 사이클로 사라진다
    bins hard = {REPAIR_HARD};            // 퓨즈 — 남는다
  }
  // 전원 사이클을 거쳐 두 성질의 차이를 확인했는가
  x_persist_layer : cross cp_persist, cp_layer {
    ignore_bins na = binsof(cp_layer.none) || binsof(cp_layer.self_repair);
  }

  // --- MISR 네 모드 (§6.8) -----------------------------------------------
  cp_misr_mode : coverpoint mmode {
    bins lfsr         = {MISR_LFSR};      // 패턴 생성
    bins register     = {MISR_REGISTER};
    bins misr         = {MISR_SIGNATURE}; // 서명 압축
    bins lfsr_compare = {MISR_COMPARE};   // 실시간 비교 — aliasing 없음
  }
  // sticky 를 테스트 시작 시 지웠는가 — 안 지우면 이전 결과를 읽는다
  cp_sticky : coverpoint sticky_cleared { bins cleared = {1}; }

  // --- Self Repair 결과 네 갈래 (§6.13) ----------------------------------
  cp_sr_result : coverpoint sr {
    bins clean        = {SR_NO_DEFECT};
    bins defect_left  = {SR_DEFECT_REMAINS};
    bins unrepairable = {SR_UNREPAIRABLE};
    bins rerun        = {SR_RERUN_REQUIRED};   // 반복 루프가 있어야 도달한다
  }
  // 전 SID 를 순회했는가 (§6.13 — 한 번에 하나의 SID)
  cp_sid : coverpoint sid { bins s[] = {[0:3]}; }
  x_sr_sid : cross cp_sr_result, cp_sid;
endgroup
```

네 가지가 이 장의 목표입니다.

- **`cp_layer` 가 `none` 만 차 있는 것**이 가장 흔한 상태입니다. 복구 기능이 한 번도 실행되지 않았다는 뜻이고, 그런데도 기능 회귀는 전부 통과합니다.
- **`cp_n_lanes.two` 이상** — 복수 레인 복구를 순차로 처리하는 절차가 검증됩니다. 하나만 복구하는 시나리오는 "한 번에 하나" 제약을 시험하지 못합니다.
- **`cp_misr_mode.lfsr_compare`** — MISR만 쓰고 Compare mode를 안 쓰면 aliasing 위험이 그대로 남습니다.
- **`cp_sr_result.rerun`** — "재실행 필요" 결과를 겪어야 반복 루프와 종료 조건이 검증됩니다. 이 bin은 **주입 없이는 나오지 않으므로**, 모델이 그 결과를 낼 수 있어야 합니다.

### 5.4 어떻게 자극하는가

**① 복수 불량 레인 → 순차 복구**

```systemverilog
// 불량 레인 3개를 주입하고, 절차대로 하나씩 UpdateWR 로 복구한다.
// 5.2 ① 의 checker 가 "한 번에 하나" 를 감시한다.
class seq_multi_lane_repair extends uvm_sequence;
  `uvm_object_utils(seq_multi_lane_repair)
  rand int unsigned n_faulty;
  constraint c_n { n_faulty inside {[2:4]}; }   // 1 개면 제약이 시험되지 않는다

  virtual task body();
    int faulty[$] = pick_repairable_lanes(n_faulty);   // 복구 불가 신호는 제외
    read_hard_repair_data();                            // §4.4 — 먼저 읽는다
    foreach (faulty[i]) begin
      set_all_fields_to_Fh();                           // 나머지는 "복구 없음"
      program_repair_vector(faulty[i]);
      issue_update_wr();                                // 여기서 하나만 개시된다
    end
    issue_bypass();                                     // §4.4 — 정상 모드 복귀
  endtask
endclass
```

**② 더블 바이트 쌍 단위** — 한 바이트만 복구할 때도 **짝을 이루는 바이트에 `1111b`** 를 함께 씁니다. 이를 빠뜨리면 손대지 않으려던 바이트가 잘못 매핑됩니다. 네 쌍(`cp_double_byte`)을 모두 순회합니다.

**③ soft/hard 차이를 전원 사이클로 확인** — 이 장에서 **두 성질을 구분하는 유일한 방법**입니다.

```
① soft lane repair 적용 → 동작 확인
② 전원 사이클 → 복구가 사라져야 한다
③ hard lane repair 적용 → 동작 확인
④ 전원 사이클 → 복구가 남아 있어야 한다
```

②와 ④의 **차이**가 검사 지점입니다. 전원 사이클 없이는 두 명령이 똑같이 보입니다.

**④ MISR와 Compare mode 병행** — 같은 패턴을 두 모드로 돌려 결과가 일치하는지 봅니다. 그리고 각 테스트 **시작 시 sticky를 지웁니다** — 지우지 않으면 이전 테스트의 불일치를 현재 것으로 읽습니다.

**⑤ 복구 불가 신호에 대한 negative** — `CK_t`·`AERR`·`WDQS`·`DERR` 등을 복구 대상으로 지정해 봅니다. 규격이 거부를 요구하지 않으므로 **DUT의 반응을 정답과 비교하면 안 되고**, 확인할 것은 5.2 ②의 목록 검사가 자극을 막는지입니다.

**⑥ Self Repair 전 SID 순회와 시간 예산** — `SID 수 × 그룹 수`만큼 반복해야 하고 **병렬이 금지**되어 있으므로, 16-high 구성은 4-high의 네 배가 걸립니다. 회귀에서는 다음을 나눕니다.

| 테스트 | 범위 |
|---|---|
| 기능 회귀 | Self Repair **생략** 또는 1 SID만 |
| 전용 테스트 | 전 SID × 전 그룹 순회 + 재실행 루프 |

전자만 돌면 `cp_sid` 가 부분만 차고, 미복구 SID가 있는 상태로 회귀가 통과합니다. 후자는 느리므로 회귀 주기를 따로 잡습니다.

## 6. 대표 문제 — dry-run

### 문제 1 — 복구 절차

> 초기화 중 `EXTEST`로 채널 5의 row 버스 레인 1개와 채널 12의 DWORD 레인 1개, 총 2개의 불량을 찾았다. 복구 절차를 순서대로 쓰라.

<details>
<summary>풀이</summary>

**두 레인이므로 복구를 두 번 나눠 수행한다**(§6.7 — 한 번에 하나만).

```
0. EXTEST 이후 RESET_n 토글 (필수)              ← 03장 §4.4
   tINIT3 경과 → WRST_n HIGH

1. hard lane repair 데이터를 읽어 새 항목과 병합  ← 03장 (soft가 hard를 덮어씀)

2. [채널 5 row 레인]
   모든 레인 설정 = Fh
   채널 5의 AWORD row 복구 벡터 시프트 인
   UpdateWR                                    ← 실제 복구
   tSLREP 등 타이밍 준수

3. [채널 12 DWORD 레인]
   모든 레인 설정 = Fh
   해당 더블 바이트에 대해 {불량 바이트 enc, 정상 바이트 Fh} 시프트 인
   UpdateWR

4. BYPASS (또는 WRST_n LOW) → 정상 기능 모드 복귀

5. CK 토글 시작 → 초기화 4~6단계 계속
```

**핵심 세 가지**: `EXTEST` 후 리셋 필수 / hard 데이터 병합 / **레인마다 별도 `UpdateWR`**.
</details>

### 문제 2 — MISR 폭 유도

> DWORD 한 바이트의 MISR가 40비트인 이유를 신호 구성으로 유도하라. AWORD가 38비트인 이유도.

<details>
<summary>풀이</summary>

**DWORD 바이트**
```
신호 : DQ 8 + DBI 1 + ECC/SEV 1        = 10
샘플 : WDQS 2사이클 × Rise/Fall        =  4 비트/신호
       (Q0~Q3가 각 신호의 반 WDQS 사이클)
                          10 × 4       = 40 b  ✅
```

**AWORD**
```
신호 : R[9:0] 10 + C[7:0] 8 = 18 커맨드 + ARFU 1 = 19
샘플 : CK DDR Rise/Fall                          =  2 비트/신호
                          19 × 2                 = 38 b  ✅
```

**읽어내는 총량**
```
DWORD_MISR : 40 × 4바이트 × 2 DWORD = 320 b
AWORD_MISR :                          38 b
```

**함정**: AWORD에서 `ARFU`를 빼면 36비트가 되어 맞지 않는다. `ARFU`는 진리표에 없지만 **구동 대상이고, 패리티 대상이고, MISR 대상**이다([06장](../06_row_commands/), [08장](../08_parity/)).
</details>

### 문제 3 — 부팅 시간 예산

> 16-high 구성에서 Self Repair를 8채널 그룹 단위로 전 채널·전 SID에 대해 수행하려 한다. 몇 번의 `SELF_REP` 명령이 필요하며, 병렬로 줄일 수 있는가?

<details>
<summary>풀이</summary>

16-high는 SID가 **4개**(`SID0`~`SID3`)이고, 32채널을 8채널 그룹으로 나누면 **4그룹**이다.

```
4 SID × 4 그룹 = 16회        ← Table 82와 일치
```

**병렬화는 불가능하다.** §6.13이 *"8 또는 16채널의 모든 그룹에 대한 Self Repair 병렬 동작은 지원되지 않는다"* 고 명시한다. `SELF_REP`은 **한 번에 하나의 SID**만 처리한다.

**부팅 시간 함의**: 4-high(4회)의 **네 배**다. 각 회차는 self-test + auto-repair 시간을 포함하며, 결과가 "다시 실행 필요"로 나오면 더 반복해야 한다.

**검증 결론**: 이 시간이 **회귀 예산을 지배**한다. 전 SID 순회 테스트는 별도 주기로 돌리고 기능 회귀에서는 축약하되, **축약했다는 사실을 커버리지로 드러내야** 한다(`cp_sid`). 그리고 `SELF_REP_RESULTS`의 "재실행 필요" 결과 때문에 반복 루프가 필요하므로, **최대 시도 횟수 없이 짜면 테스트가 끝나지 않을 수 있다**(5.2 ④).
</details>

## 핵심 정리

- lane repair는 고장 대응이 아니라 **SiP 조립 수율 확보 수단**이다. 약 3,896개 신호 범프 규모에서 필수다.
- 동작 원리는 **시프트** — 불량 레인을 끄고 뒤를 한 칸씩 밀어 **여분 레인이 마지막을 받는다.**
- 계층은 셋 — **AWORD**(채널당 1개, row **또는** column), **DWORD**(더블 바이트당 `RD`), **WSO**(`RM`).
- **복구할 수 없는 신호**: `CK_t`/`CK_c`, `AERR`, `WDQS_t`/`_c`, `RDQS_t`/`_c`, `PAR`, `DERR`. **자기 자신을 관측·구동하는 신호는 복구 대상이 아니다.**
- DWORD는 **쌍 단위로 프로그램**한다 — 정상 바이트에도 `1111b`를 명시해야 한다.
- ⚠️ **한 번에 한 레인만.** 근거가 **전류 제약**이라 디지털 시뮬에서는 위반이 관측되지 않는다 — DUT 검증이 아니라 **IEEE1500 명령 스트림을 보는 자극 측 프로토콜 검사**로 잡는다. N개면 **N번의 `UpdateWR`** 이 필요하고, **1개만 복구하는 시나리오는 이 제약을 시험하지 못한다.**
- lane repair는 **CK 토글 이전**, 즉 초기화 중에만 가능하다. `HARD_LANE_REPAIR`는 **전원이 제거되어도 유지**된다 — soft와 hard의 차이는 **전원 사이클을 거쳐야만** 구분되며, 그 시나리오가 없으면 두 명령이 똑같이 보인다.
- MISR 폭은 신호 구성에서 유도된다 — **DWORD 바이트 40b**(10 신호 × 4), **AWORD 38b**(19 신호 × 2). **`ARFU`가 포함**된다.
- 모드는 넷 — **LFSR / Register / MISR / LFSR Compare**. **MISR 서명 일치는 무결의 증명이 아니다** — 압축이므로 aliasing이 있고, 특히 구조적 오류에 취약하다. **Compare mode를 병행**하고, sticky는 **테스트 시작 시 지운다**(안 지우면 이전 테스트 결과를 읽는다).
- MISR 다항식은 규격이 **예시만** 제시한다. 모델의 `poly`는 **구성에서 받아야** 하고 상수로 박으면 다른 정의에서 전부 틀린다.
- Self Repair는 **self-test → auto-repair** 2단계이며, **패턴과 복구 가능 개수가 벤더 지정**이다.
- Self Repair는 **SID 하나씩, 채널 그룹 하나씩** 순회한다. **병렬 실행은 규격상 금지**이므로 **부팅 시간이 스택 높이에 비례**한다.
- `SELF_REP_RESULTS`에 **"다시 실행 필요"** 상태가 있다 — 검증 시퀀스도 **반복 루프와 최대 시도 횟수**를 가져야 하며, 없으면 테스트가 끝나지 않을 수 있다.
- 이 장의 커버리지는 **"이 기능이 한 번이라도 실행됐는가"** 에서 시작한다. 기능 회귀만 도는 환경은 `cp_layer` 가 `none` 만 차 있고, 그런데도 전 항목이 통과한다.

## Further Reading

- **규격**: JESD270-4 §6.7 Interconnect Redundancy Remapping (Table 48–54, Figure 70) · §6.8 Loopback Test Modes (Figure 71–76) · §6.13 Self Repair (Table 82)
- **다음 장**: [11 — 트레이닝과 IEEE 1500](../11_training_ieee1500/)
- **관련**: [03 — 초기화](../03_init_reset_power/) (soft/hard 덮어쓰기) · [04 — Mode Register](../04_mode_registers/) (`MR7`) · [07 — Column 커맨드](../07_column_commands/) (홀짝 바이트 타이밍)
- **이해도 점검**: [퀴즈](../quiz/10_test_repair_quiz/)
