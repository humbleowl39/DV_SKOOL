---
title: "11 — 트레이닝과 IEEE 1500"
description: JESD270-4 §6.10–6.12·§13 · WOSC·DCA/DCM·Rx offset의 순서 제약, 테스트 포트 두 갈래와 21개 명령
---

:::tip[🎯 Learning Objectives]
이 모듈을 마치면:

- **Order** 네 가지 트레이닝의 선후 제약을 규격 근거와 함께 배열한다.
- **Explain** WOSC가 채널·클럭과 무관하게 동작하는 구조와 정확도 결정 요인을 설명한다.
- **Interpret** `DERR` 핀이 세 가지 문맥에서 갖는 서로 다른 의미를 구분한다.
- **Differentiate** IEEE 1500 포트와 DA 포트의 역할·선택 방식·상호 배타성을 구분한다.
- **Evaluate** DA Test Port Lockout이 어떤 리셋으로도 해제되지 않는다는 성질의 설계 함의를 판단한다.
:::

:::note[Prerequisites]
- [05 — 클럭킹과 DBIac](../05_clocking_dbi/) — WDQS 분주기, WDQS-to-CK 정렬 트레이닝, 짝수 토글 규칙
- [04 — Mode Register](../04_mode_registers/) — `MR6`(DCM·드라이버), `MR8`(WDQS2CK·RxOffC·DA Lockout), `MR10`/`MR11`(DCA)
- [10 — 테스트와 복구](../10_test_repair/) — IEEE 1500 명령이 실제로 하는 일
:::

:::caution[인용 고지]
본 장은 **JESD270-4 (2025-04, WIP draft)** §6.10–§6.12 및 §13을 근거로 **요약·재구성**한 것입니다. 표·그림은 옮기지 않고 규칙과 구조만 서술합니다. 정밀 값은 **JEDEC 원문 우선**.
:::

---

## 1. 트레이닝은 순서가 있다

HBM4의 트레이닝 기능은 독립적이지 않습니다. 규격이 **선후 관계를 명시**하며, 그 순서를 어기면 앞선 결과가 무효가 됩니다.

```d2
direction: down

RX: "① Rx Offset Calibration (RXoffC)\nMR8 OP1 · 선택 기능\nDQ Rx 오프셋 보정\n→ write 캘리브레이션에 영향" {
  style.fill: "#e3f2fd"; style.font-color: "#0A0F25"
}
DCA: "② DCA / DCM\nMR11·MR10 (DCA) · MR6 OP[7:6] (DCM)\nWDQS 듀티 사이클 보정·관측" {
  style.fill: "#e8f5e9"; style.font-color: "#0A0F25"
}
VREF: "③ VREFD 트레이닝\nMR14 · DWORD 입력 기준 전압" {
  style.fill: "#fff8e1"; style.font-color: "#0A0F25"
}
W2C: "④ WDQS-to-CK Alignment\nMR8 OP3 · tDQSS 범위 확보\n(05장)" {
  style.fill: "#f3e5f5"; style.font-color: "#0A0F25"
}
WOSC: "WOSC (WDQS Interval Oscillator)\nIEEE1500 WOSC_RUN / WOSC_COUNT\n채널·클럭 무관 · 재트레이닝 필요 판단" {
  style.fill: "#eceff1"; style.font-color: "#0A0F25"
}

RX -> VREF: "규격 요구"
RX -> W2C: "규격 요구"
DCA -> W2C: "규격 요구"
VREF -> W2C
WOSC -> RX: "재트레이닝 시점 결정"
```

근거는 두 조문입니다.

> Rx offset calibration은 DRAM write 캘리브레이션 트레이닝에 영향을 주므로, **`VREFD` 트레이닝과 WDQS-to-CK 정렬보다 먼저 수행되어야 한다.** — §6.12.1 (요약)

> **duty cycle monitor 시퀀스 유무와 관계없이, duty cycle 조정은 WDQS-to-CK 정렬 트레이닝보다 먼저 수행되어야 한다.** — §6.11.1 (요약)

:::tip[왜 순서가 강제되는가]
각 트레이닝이 **뒤 단계의 전제를 바꾸기** 때문입니다.

- Rx offset은 **수신기의 판정 기준점**을 옮깁니다. 기준점이 바뀌면 그 위에서 잡은 `VREFD`와 위상 정렬이 무의미해집니다.
- DCA는 **WDQS의 듀티 자체**를 바꿉니다. 듀티가 달라지면 CK 대비 위상 관계도 함께 달라집니다.

**설계 결론**: 초기화 펌웨어의 트레이닝 시퀀스는 순서를 하드코딩해야 하며, 어느 하나를 재수행하면 **그 뒤 단계도 함께 재수행**해야 합니다.
:::

## 2. WOSC — 재트레이닝이 필요한지 판단하는 장치

### 문제 설정

> **전압과 온도가 변하면 WDQS 클럭 트리 지연이 이동하며 재트레이닝이 필요할 수 있다.** HBM4 DRAM은 주어진 시간 구간(컨트롤러가 결정) 동안 지연량을 측정하는 **내부 WDQS 클럭 트리 오실레이터**를 포함해, 컨트롤러가 **트레이닝 당시의 지연값과 이후 시점의 지연값을 비교**할 수 있게 한다. — §6.10.1 (요약)

[07장](../07_column_commands/)에서 본 **비정합 WDQS-DQ 경로**가 주기적 트레이닝을 요구한다고 했는데, WOSC는 **"언제 다시 해야 하는가"를 알려주는 계측기**입니다.

### 독립성

WOSC의 성질이 특이합니다.

- **어떤 채널에도 속하지 않으며**, 채널의 동작 주파수나 상태(bank active/idle, power-down, self refresh)와 **완전히 무관**하게 동작합니다.
- **계수 중에 `CK`, `WDQS`, `WRCK` 어떤 클럭도 필요하지 않습니다.** 내부 링 오실레이터가 **WDQS 클럭 트리의 복제본**을 통과하는 신호 전파 횟수를 셉니다.
- **전원 인가 시 기본 비활성**입니다.

즉 메모리가 저전력 상태에 있어도 측정이 가능합니다. 이것이 **정상 동작을 방해하지 않고 재트레이닝 필요를 감지**하는 근거입니다.

### 동작과 유효성

`WOSC_RUN` WDR의 `WOSC_START_STOP` 비트로 시작·정지하고, `WOSC_COUNT` 명령으로 결과를 읽습니다.

| 항목 | 값 |
|---|---|
| 최대 계수 | **2²⁴ − 1** |
| 오버플로 없는 최장 구간 | `2²⁴ × tRX_DQS2DQ(min)` |
| 유효 표시 | `WOSC_COUNT_VALID` (기본 0 = 무효) |

`WOSC_COUNT_VALID`가 **0(무효)으로 남는 두 경우**가 있습니다.

1. **카운터 오버플로** (2²⁴ 이상)
2. **`RESET_n`을 LOW로 당겨 오실레이터가 중단된 경우**

그런데 반대는 다릅니다.

> **`WRST_n`을 LOW로 당기는 것은 오실레이터 동작에 영향을 주지 않는다.** — §6.10.1

[03장](../03_init_reset_power/)에서 본 **두 리셋의 비대칭**이 여기서 다시 확인됩니다 — 기능 리셋은 WOSC를 죽이지만 테스트 포트 리셋은 그렇지 않습니다.

### 정확도는 측정 시간이 결정한다

```
Granularity Error = 2 × (WDQS 지연) / (Run Time)
Accuracy          = 1 − Granularity Error − Matching Error
```

- **길게 돌릴수록 정확**해집니다 (granularity error가 줄어듭니다).
- 다만 **오버플로 한계** 안에 있어야 합니다.
- **Matching Error**는 WDQS 트레이닝 회로와 실제 WDQS 클럭 트리 사이의 차이이며 **벤더 지정**입니다.

:::tip[측정 시간의 트레이드오프]
짧게 돌리면 부정확하고, 길게 돌리면 정확하지만 오버플로 위험과 측정 지연이 커집니다. 그리고 **matching error는 아무리 길게 돌려도 줄어들지 않습니다** — 정확도에는 상한이 있습니다.

**설계 결론**: 측정 시간을 무작정 늘릴 이유가 없습니다. granularity error가 matching error보다 충분히 작아지는 지점에서 멈추는 것이 합리적이고, matching error 값은 벤더 데이터시트에서 얻어야 합니다.
:::

## 3. DCA와 DCM — 듀티를 고치고 관측한다

### DCA (Duty Cycle Adjuster)

WDQS의 **계통적 듀티 사이클 오차**를 보정합니다. 위치가 중요합니다.

> DCA는 **WDQS 분주기 또는 그에 준하는 것 앞에** 위치한다. DCA는 **Write와 Read 양쪽**의 WDQS 듀티 사이클에 영향을 준다. — §6.11.1 (요약)

[05장](../05_clocking_dbi/)의 클럭 구조도에서 **분주기 이전 단**에 들어간다는 뜻이고, 그래서 read/write 모두에 작용합니다.

| 항목 | 내용 |
|---|---|
| 제어 | WDQS0(PC0) = `MR11` OP[3:0], WDQS1(PC1) = `MR11` OP[7:4] |
| 범위 | **−7 ~ +7 스텝** |
| 양수 | `tWQSH` 증가, `tWQSL` 감소 |
| 음수 | `tWQSH` 감소, `tWQSL` 증가 |
| 최대 오프셋 | **15 ~ 35 ps** (설계로 보장) |
| 단일 스텝 크기 | **2 ~ 5 ps** — **각 스텝의 비선형성을 반영** |

:::caution[스텝이 균등하지 않다]
단일 스텝 크기가 **2~5 ps 범위**로 주어진 것은, 각 스텝이 같은 양을 움직이지 않는다는 뜻입니다(Table 72 Note 3 — *"단일 스텝 크기는 각 스텝의 비선형성을 반영한다"*).

**설계 함의**: 코드 값과 실제 지연 변화가 선형이 아니므로, "몇 ps 옮기고 싶으니 코드를 몇 단계 바꾼다"는 계산이 성립하지 않습니다. **탐색(sweep)으로 목표에 접근**해야 합니다.
:::

그리고 주파수 제약이 있습니다 — DCA는 **선택 기능**이며 **`fCKDCA`보다 낮은 CK 주파수에서는 지원되지 않습니다.** 그 주파수에서는 DCA 코드를 **기본값 `0000`으로 두어 비활성화**해야 합니다.

### DCM (Duty Cycle Monitor)

DRAM 내부 WDQS 클럭 트리의 **듀티 사이클 왜곡을 관측**합니다. `MR6` OP[7:6]으로 제어합니다.

| 관측 결과 | `DERR0`/`DERR1` |
|---|---|
| WDQS 듀티 **< 50%** | LOW |
| WDQS 듀티 **≥ 50%** | HIGH |

`MR6` OP6을 1로 두면 측정이 시작되고, **최소 `tDCMM`** 후에 `DERR0`(DWORD0/PC0)·`DERR1`(DWORD1/PC1)에 결과가 나타납니다. 결과는 DCM을 끌 때까지 유효하며, 끄면 `DERR`는 **늦어도 `tMOD` 후** 기본 상태로 돌아갑니다.

**여기서도 짝수 규칙이 나옵니다.**

> 측정을 개시하는 `MRS` 커맨드부터 `tDCMM` 타이밍이 충족될 때까지, **측정 사이클의 전 구간에 걸쳐 짝수 개의 연속 WDQS 펄스가 요구된다.** — §6.11.3 (요약)

[05장](../05_clocking_dbi/)의 `WDQS/2` 위상 보존 규칙이 **세 번째로** 등장합니다 — 일반 규칙, WDQS-to-CK 트레이닝 6단계, 그리고 DCM 측정.

### 히스테리시스와 flip

> DCM 회로에 **히스테리시스가 존재하면 결과가 부정확할 수 있다.** 정확도를 높이기 위해 DCM은 **`MR6` OP[7]을 반대 상태로 설정해 입력을 뒤집고** `tDCMM` 후 측정을 반복하는 것을 지원한다. — §6.11.3 (요약)

즉 **no-flip 측정 + flip 측정 두 번**을 수행해 히스테리시스를 상쇄합니다. `MR6` OP7이 그 `DCM Flip` 비트입니다([04장](../04_mode_registers/)).

DCM 모드에서 허용되는 커맨드와 경고는 [05장](../05_clocking_dbi/)의 WDQS-to-CK 트레이닝과 **동일**합니다 — REFab·REFpb·RFMab·RFMpb·RNOP·CNOP·MRS만 허용되고, refresh 계열의 **내부 전류 스파이크가 결과를 해칠 수 있습니다.** DCM 역시 `fCKDCA` 미만 주파수에서는 지원되지 않습니다.

## 4. Rx Offset Calibration

**선택 기능**이며 지원 여부는 **`DEVICE_ID`의 `RXoffC` 비트**로 알립니다. 시작·정지는 **`MR8` OP1**입니다.

시퀀스가 단순합니다.

```
1. MRS 발행 (트레이닝 시작)  ← 이때 호스트가 DQ 채널을 float 해야 한다
2. tOSCAL 대기 (최대 6 μs)
3. MRS 발행 (트레이닝 종료)
```

두 가지가 눈에 띕니다.

- **호스트가 DQ를 float** 해야 합니다. 컨트롤러가 DQ를 구동한 채 시작하면 보정이 어긋납니다.
- 이 트레이닝에 다른 기능이 필요하면 **장치가 자동으로 활성화**하고, 종료 MRS 이후 **`tMOD` 안에 자동으로 비활성화**합니다. 컨트롤러가 관여하지 않습니다.

권장 시점은 **전원 인가 초기화 과정이든 정상 동작 중이든, 트레이닝을 수행할 때마다**입니다 — 동작 조건 변화에 대응하기 위해서입니다.

## 5. `DERR`의 세 얼굴

이 코스에서 `DERR`가 세 번째로 다른 의미를 갖습니다.

| 문맥 | `DERR`의 의미 | 다루는 장 |
|---|---|---|
| 일반 동작 | **데이터 패리티 오류** | [08장](../08_parity/) |
| WDQS-to-CK 정렬 트레이닝 (`MR8` OP3 = 1) | **위상 검출기 판독** (HIGH = early) | [05장](../05_clocking_dbi/) |
| DCM 활성 (`MR6` OP6 = 1) | **듀티 사이클 측정 결과** (HIGH = ≥50%) | 이 장 |

:::caution[모드 디코딩이 필수다]
`DERR`를 해석하는 로직은 **`MR8` OP3와 `MR6` OP6을 함께 보고 분기**해야 합니다. 어느 하나라도 활성이면 그 값은 패리티 오류가 아닙니다.

```
MR6 OP6 == 1   →  듀티 사이클 측정 결과
MR8 OP3 == 1   →  위상 검출기 판독
그 외          →  데이터 패리티 오류
```

두 트레이닝 모드를 동시에 켜면 `DERR` 해석이 모호해지므로, **한 번에 하나만** 활성화해야 합니다.
:::

## 6. IEEE 1500 테스트 접근 포트

### 구조와 확장

> IEEE Standard 1500 호환 테스트 접근 포트는 호스트와 HBM4 DRAM 사이의 **직접 테스트 연결**을 제공한다. HBM4 DRAM의 테스트 포트는 **표준 사양을 확장해 채널마다 `WSO` 출력을 복제**한다. 이는 일부 명령이 **채널 간 병렬로 실행**될 수 있게 하고, **`WSO`에 대한 채널 간 중재의 필요를 제거**한다. — §13.2 (요약)

[01장](../01_landscape_organization/)에서 전역 신호 표를 볼 때 `WSO`만 **채널당 1개씩 32개**였던 이유가 여기 있습니다. 나머지 IEEE1500 신호는 링크 리던던시를 위해 2개씩 중복 배치되지만, `WSO`는 **채널 병렬성을 위해** 32개입니다.

### 사용 가능 시점

> IEEE 1500 동작은 **장치 초기화 후 언제든**, 그리고 **정상 메모리 동작 중에도**, HBM4 DRAM이 **power-down이나 self refresh 모드에 있을 때를 포함해** 발동될 수 있다. — §13.2 (요약)

그리고 초기화 완료 **이전**에도 일부 명령이 허용됩니다([03장](../03_init_reset_power/) §4.4 — `tINIT3` 이후).

즉 테스트 포트는 **전 생애에 걸쳐 열려 있습니다.** 그래서 규격이 §13.6을 따로 두어 **mission mode와의 상호작용**을 규정합니다.

### 21개 명령의 지형

[S1 인덱스](../)에서 정리한 21개 명령을 역할로 묶으면 이렇습니다.

| 묶음 | 명령 | 다루는 장 |
|---|---|---|
| **기본·리셋** | `BYPASS`, `HBM_RESET` | [03장](../03_init_reset_power/) |
| **식별** | `CHANNEL_ID`, `DEVICE_ID` | [06장](../06_row_commands/) (RAA 문턱값), [02장](../02_addressing_bank_groups/) (밀도 코드) |
| **경계 스캔** | `EXTEST_RX` | [03장](../03_init_reset_power/), §13.8 |
| **배열 시험·복구** | `MBIST`, `SOFT_REPAIR`, `HARD_REPAIR`, `SELF_REP`, `SELF_REP_RESULTS`, `HS_REP_CAP` | [10장](../10_test_repair/) |
| **레인 복구·채널 제어** | `SOFT_LANE_REPAIR`, `CHANNEL_DISABLE` | [10장](../10_test_repair/), [03장](../03_init_reset_power/) |
| **루프백** | `DWORD_MISR`, `AWORD_MISR`, `AWORD_MISR_CONFIG`, `READ_LFSR_COMPARE_STICKY` | [10장](../10_test_repair/) |
| **MR 접근** | `MODE_REGISTER_DUMP_SET` | [04장](../04_mode_registers/) |
| **센서·계측** | `TEMPERATURE`, `CHANNEL_TEMPERATURE`, `WOSC_RUN` | 이 장 |
| **오류 로그** | `ECS Error Log` | [09장](../09_ecc_ecs_sev/) |

**테스트 포트가 없으면 접근할 수 없는 것들**이 이 목록에 있습니다 — MR 되읽기([04장](../04_mode_registers/)), RAA 문턱값([06장](../06_row_commands/)), ECS 오류 로그([09장](../09_ecc_ecs_sev/)), 장치 구성 코드([02장](../02_addressing_bank_groups/)).

:::tip[부팅 시퀀스에 테스트 포트가 필요하다]
"테스트 포트"라는 이름 때문에 양산 시험 전용으로 오해하기 쉽지만, 실제로는 **정상 부팅에 필수**입니다.

```
DEVICE_ID 읽기  →  밀도 코드 (주소 구성 결정)         ← 02장
                →  RAAIMT / RAAMMT / RAADEC          ← 06장
                →  ARFM 지원 여부 (MR8 값 결정)       ← 06장
                →  RXoffC 지원 여부                   ← 이 장
```

이 값들 없이는 컨트롤러가 올바른 설정을 만들 수 없습니다. 따라서 **`WRST_n`을 상시 LOW로 묶는 선택**([03장](../03_init_reset_power/))은 이 정보들을 포기한다는 뜻이며, 구성을 하드코딩할 수 있는 폐쇄 시스템에서만 가능합니다.
:::

## 7. DA 테스트 포트 — 두 번째 문

IEEE 1500과 별개로 **Direct Access(DA) 테스트 포트**가 있습니다.

| 항목 | 내용 |
|---|---|
| 신호 | `DA[39:0]`, **핀당 마이크로범프 2개** |
| 용도 | **벤더 지정 테스트 구현** |
| 선택 | **`DA12`** — LOW면 IEEE 1500, HIGH면 DA 포트 |
| 배치 | 프로빙용 비배치 영역이 bump map **컬럼 86~94** 부근 |
| 핀 할당 | `DA[19:12]` **8핀 point-to-point** / `DA[39:20][11:0]` **32핀 multi-drop**(최대 4개 장치) |

### 상호 배타

`DA12` = HIGH면 **IEEE 1500 포트가 비활성화**됩니다. 그리고 그 상태에서는 **`CATTRIP` 출력이 활성이지만 값이 유효하지 않을 수 있어 무시해야** 합니다.

`DA12`에는 **내부 풀다운 저항**이 있어, 핀이 떠 있어도 LOW로 유지되어 DA 포트가 비활성 상태로 남습니다. 즉 **기본은 IEEE 1500 쪽**입니다.

두 포트를 모두 쓰지 않는 것도 가능합니다 — `DA12`를 LOW로, `WRST_n`을 LOW로 두면 둘 다 닫힙니다.

### 활성화 조건의 비대칭

DA 포트는 전원 램프 완료(`tINIT0`)와 `tINIT1` 경과 후 **언제든** 활성화할 수 있으며, **`RESET_n`의 레벨은 무관**합니다. 비활성화(`DA12` LOW)한 뒤에는 **장치 초기화를 다시 수행해야** 정상 동작으로 복귀합니다([03장](../03_init_reset_power/) §4.2).

IEEE 1500이 `tINIT3` 이후에 열리는 것과 대비됩니다 — **DA 포트가 더 이른 시점부터 열립니다.**

### ⚠️ DA Test Port Lockout — 되돌릴 수 없는 잠금

> DA 테스트 포트는 **`MR8` OP0 비트를 1로 설정해 비활성화(잠금)** 할 수 있다. 이 비트는 **채널 0 또는 4에만 정의**된다. 일단 1로 설정되면 **HBM4 DRAM에서 전원이 제거되지 않는 한 DA 테스트 포트는 비활성 상태로 남는다.** `RESET_n`을 LOW로 당기거나 IEEE1500 `HBM_RESET` 명령을 통한 어떤 칩 리셋도, `MRS` 커맨드나 `MODE_REGISTER_DUMP_SET`으로 0을 쓰는 것도 **잠금 상태를 해제하지 않는다.** — §13.1.1 (요약)

:::caution[리셋으로도 풀리지 않는 유일한 상태]
이 코스에서 본 sticky 상태들과 비교하면 성격이 다릅니다.

| 상태 | 해제 방법 |
|---|---|
| `CATTRIP` ([03장](../03_init_reset_power/)) | 기능 리셋으로 안 지워짐 — **전원 차단** |
| Auto ECS ([09장](../09_ecc_ecs_sev/)) | **장치 RESET** |
| **DA Port Lockout** | **전원 제거만** — 리셋도, MR에 0을 써도 안 됨 |

**설계·보안 함의**: 양산 후 필드에 나가는 제품에서 **벤더 테스트 접근을 영구 차단**하는 수단입니다. 부팅 시퀀스에서 이 비트를 1로 쓰면 그 전원 사이클 동안 DA 포트가 완전히 닫힙니다.

**주의**: 채널 0 또는 4에만 정의된 비트이므로, MR 이미지를 **전 채널에 동일하게 쓰면** 의도치 않게 잠글 수 있습니다. 반대로 잠그려면 그 두 채널 중 하나에 반드시 써야 합니다.
:::

## ⚙️ 설계 적용 (RTL / Front-end)

### 8.1 트레이닝 시퀀서 — 순서와 무효화

```systemverilog
// 순서 제약: RXoffC -> (DCA/DCM) -> VREFD -> WDQS-to-CK   (§6.11.1, §6.12.1)
// 앞 단계를 재수행하면 뒤 단계도 무효가 된다.
typedef enum logic [2:0] {
  TR_IDLE, TR_RXOFFC, TR_DCA_DCM, TR_VREFD, TR_W2C, TR_DONE
} train_state_e;

// 재트레이닝 요청이 오면 해당 단계 이후를 모두 무효화한다
always_ff @(posedge clk) begin
  if (retrain_req) begin
    unique case (retrain_from)
      TR_RXOFFC : {vrefd_valid_q, w2c_valid_q, dca_valid_q} <= '0;
      TR_DCA_DCM: w2c_valid_q <= 1'b0;
      TR_VREFD  : w2c_valid_q <= 1'b0;
      default   : ;
    endcase
  end
end
```

### 8.2 WOSC 측정 시간 산정

```systemverilog
// 오버플로 없는 최장 구간 = 2^24 × tRX_DQS2DQ(min)   (§6.10.1)
// granularity error가 matching error보다 충분히 작아지는 지점에서 멈춘다.
localparam int WOSC_MAX_COUNT = (1 << 24) - 1;

// Granularity Error = 2 × WDQS_delay / RunTime
// 목표: granularity < matching / 4  정도
function automatic int wosc_run_time_ps(input int wdqs_delay_ps, input int matching_err_ppm);
  return (2 * wdqs_delay_ps * 4 * 1000000) / matching_err_ppm;
endfunction

// RESET_n에 의한 중단은 VALID를 0으로 만든다. WRST_n은 영향 없음.
wire wosc_result_usable = wosc_count_valid_i;   // 오버플로/RESET_n 중단 시 0
```

### 8.3 DCA는 탐색으로 접근

```systemverilog
// 스텝 크기가 비선형(2~5 ps)이므로 코드 계산이 아니라 sweep으로 목표에 접근한다 (Table 72)
// DCM 결과(DERR)를 피드백으로 사용한다.
task automatic dca_sweep(input int pc);
  for (int code = -7; code <= 7; code++) begin
    set_dca(pc, code);
    // no-flip 측정
    set_dcm(1'b1, 1'b0); wait_tdcmm(); r_noflip = read_derr(pc);
    // flip 측정 — 히스테리시스 상쇄 (§6.11.3)
    set_dcm(1'b1, 1'b1); wait_tdcmm(); r_flip   = read_derr(pc);
    set_dcm(1'b0, 1'b0); wait_tmod();
    if (r_noflip != r_flip) begin                 // 경계 근처 = 듀티 50% 부근
      best_code[pc] = code; break;
    end
  end
endtask
```

**측정 구간 내내 WDQS 펄스가 짝수여야** 하므로([05장](../05_clocking_dbi/)), 각 측정 사이클의 펄스 수를 함께 관리해야 합니다.

### 8.4 `DERR` 모드 디코딩

```systemverilog
// DERR는 세 가지 의미를 갖는다 (05·08·11장)
typedef enum logic [1:0] { DERR_PARITY, DERR_PHASE, DERR_DUTY } derr_mode_e;

wire dcm_on  = mr_q[6][6];      // MR6 OP6
wire w2c_on  = mr_q[8][3];      // MR8 OP3

assign derr_mode = dcm_on ? DERR_DUTY
                 : w2c_on ? DERR_PHASE
                          : DERR_PARITY;

`ifndef SYNTHESIS
  a_one_training_mode: assert property (@(posedge ck) disable iff (!rst_n)
    !(dcm_on && w2c_on))
    else $error("DCM and WDQS-to-CK training enabled simultaneously — DERR ambiguous");
`endif
```

### 8.5 부팅 시 `DEVICE_ID` 선행 읽기

```systemverilog
// 컨트롤러 설정이 DEVICE_ID에 의존한다 — MR을 쓰기 전에 읽어야 한다
// (밀도 코드 / RAAIMT·RAAMMT·RAADEC / ARFM / RXoffC)
typedef enum logic [2:0] {
  BOOT_INIT,         // tINIT3까지
  BOOT_OPEN_1500,    // WRST_n HIGH
  BOOT_READ_DEVID,   // ← MR 이미지 확정에 필요
  BOOT_LANE_REPAIR,  // 필요 시 (CK 토글 이전)
  BOOT_MRS,          // 20개 MR 기록
  BOOT_TRAINING,     // RXoffC -> DCA/DCM -> VREFD -> W2C
  BOOT_NORMAL
} boot_state_e;
```

## 9. 대표 문제 — dry-run

### 문제 1 — 트레이닝 순서

> 정상 동작 중 온도가 크게 올라 WOSC 계수값이 트레이닝 시점 대비 크게 벗어났다. Rx offset calibration을 다시 수행했다. 그 다음에 해야 할 일은?

<details>
<summary>풀이</summary>

**`VREFD` 트레이닝과 WDQS-to-CK 정렬을 다시 수행해야 한다.**

§6.12.1이 *"Rx offset calibration은 DRAM write 캘리브레이션 트레이닝에 영향을 주므로 `VREFD` 트레이닝과 WDQS-to-CK 정렬보다 먼저 수행되어야 한다"* 고 규정한다. 순서가 강제된다는 것은, **앞 단계를 다시 하면 뒤 단계의 전제가 바뀐다**는 뜻이다.

Rx offset은 **수신기의 판정 기준점**을 옮기므로, 그 위에서 잡았던 `VREFD` 값과 위상 정렬이 더 이상 유효하지 않다.

**설계 결론**: 트레이닝 시퀀서는 각 단계의 유효 플래그를 두고, **앞 단계 재수행 시 뒤 단계 플래그를 무효화**해야 한다. Rx offset만 다시 하고 끝내면 잘못된 `VREFD`·위상으로 동작한다.
</details>

### 문제 2 — `DERR` 해석

> 컨트롤러가 `MR6` OP6(DCM)을 1로 두고 측정 중이다. 동시에 write 버스트가 진행되어 `DERR1`이 HIGH로 관측됐다. 데이터 패리티 오류인가?

<details>
<summary>풀이</summary>

**아니다 — 그리고 애초에 이 상황이 만들어지면 안 된다.**

DCM 활성 시 `DERR1`은 **DWORD1(PC1)의 WDQS 듀티 사이클 측정 결과**이며, HIGH는 **듀티 ≥ 50%** 를 뜻한다(Table 75).

게다가 DCM 모드에서 **허용되는 커맨드는 REFab·REFpb·RFMab·RFMpb·RNOP·CNOP·MRS 뿐**이다(§6.11.3). **write 커맨드 자체가 허용되지 않는다.**

**설계 결론**: 두 가지를 지켜야 한다.
1. `DERR` 해석은 `MR6` OP6와 `MR8` OP3를 보고 **모드별로 분기**한다.
2. 트레이닝 모드 진입 시 **정상 트래픽을 차단**한다. 허용 커맨드 목록 밖의 커맨드가 나가면 그 자체가 규격 위반이다.
</details>

### 문제 3 — DA Port Lockout

> 양산 테스트에서 DA 포트를 쓰고 나서 `MR8` OP0을 1로 써서 잠갔다. 이후 디버그가 필요해졌다. `RESET_n`을 당기면 열리는가?

<details>
<summary>풀이</summary>

**열리지 않는다.**

§13.1.1은 잠금이 **전원이 제거되지 않는 한 유지**되며, 다음 어떤 것으로도 해제되지 않는다고 명시한다.
- `RESET_n`을 LOW로 당기는 칩 리셋
- IEEE1500 `HBM_RESET` 명령
- `MRS`로 0을 쓰기
- `MODE_REGISTER_DUMP_SET`으로 0을 쓰기

**유일한 해제 방법은 전원 제거**다.

**대안**: DA 포트가 잠겨 있어도 **IEEE 1500 포트는 살아 있다**(둘은 `DA12`로 선택되는 별개 경로이며, 잠금은 DA 쪽만 닫는다). 따라서 `MBIST`·`SELF_REP`·`MODE_REGISTER_DUMP_SET` 등 표준 명령으로 할 수 있는 디버그는 여전히 가능하다. 잃는 것은 **벤더 지정 테스트 기능**이다.

**설계 주의**: `MR8` OP0은 **채널 0 또는 4에만 정의**된 비트다. MR 이미지를 전 채널에 동일하게 적용하는 펌웨어라면, 그 비트가 의도치 않게 1로 나가지 않는지 확인해야 한다.
</details>

## 🔍 검증 연결

- 트레이닝 시퀀스를 시나리오로 구성 → [`hbm_dv` Ch08 시나리오](../../hbm_dv/08_testcase_scenarios/)
- DFT 경로와 mission mode 교차 → [`hbm_dv` Ch11 DFT·RAS](../../hbm_dv/11_dft_ras/)
- 트레이닝 수렴이 mixed-level 검증인 이유 → [`hbm_dv` Ch05 Mixed-Level](../../hbm_dv/05_mixed_level/)

## 핵심 정리

- 트레이닝에는 **순서 제약**이 있다 — **RXoffC → (DCA/DCM) → VREFD → WDQS-to-CK**. 앞 단계를 재수행하면 **뒤 단계도 무효**다.
- **WOSC는 채널·클럭과 무관**하게 동작하며 계수 중 `CK`·`WDQS`·`WRCK`가 필요 없다. **전원 인가 시 기본 비활성**이다.
- WOSC 결과는 **오버플로**(2²⁴ 이상)나 **`RESET_n` 중단**에서 무효가 된다. **`WRST_n`은 영향이 없다** — 두 리셋의 비대칭이 여기서도 확인된다.
- 정확도는 **측정 시간이 길수록** 좋아지지만 **matching error(벤더 지정)가 상한**을 만든다. 무작정 길게 돌릴 이유가 없다.
- **DCA는 분주기 앞단**에 있어 **read/write 양쪽**에 작용한다. 범위 **−7~+7**, 최대 오프셋 **15~35 ps**, **스텝이 비선형(2~5 ps)** 이므로 **탐색으로 접근**해야 한다.
- DCA·DCM 모두 **`fCKDCA` 미만 주파수에서는 미지원**이며, 그때는 DCA 코드를 **기본값 `0000`** 으로 둔다.
- DCM은 **히스테리시스 상쇄를 위해 flip 측정을 함께** 수행한다. 측정 구간 내내 **WDQS 펄스가 짝수**여야 한다 — 짝수 규칙의 세 번째 등장.
- Rx offset 트레이닝은 **호스트가 DQ를 float** 해야 하며, 필요한 부속 기능은 **장치가 자동으로 켜고 끈다**. `tOSCAL` 최대 **6 μs**.
- **`DERR`는 세 가지 의미**를 갖는다 — 패리티 오류 / 위상 검출기 판독 / 듀티 측정 결과. **모드 디코딩이 필수**이며 두 트레이닝을 동시에 켜면 안 된다.
- IEEE 1500은 **`WSO`를 채널마다 복제**해 채널 병렬 실행을 가능하게 한다. **초기화 후 전 생애에 걸쳐**, power-down·self refresh 중에도 사용 가능하다.
- **테스트 포트는 양산 전용이 아니라 부팅에 필수**다 — `DEVICE_ID`에서 밀도 코드·RAA 문턱값·ARFM/RXoffC 지원 여부를 읽어야 MR 이미지를 확정할 수 있다.
- DA 포트는 **`DA12`로 IEEE 1500과 배타 선택**되며, 내부 풀다운으로 **기본은 IEEE 1500** 쪽이다. DA 활성 시 **`CATTRIP` 값은 무시**해야 한다.
- ⚠️ **DA Port Lockout(`MR8` OP0)은 전원 제거로만 해제된다.** 어떤 리셋으로도, MR에 0을 써도 풀리지 않는다. **채널 0 또는 4에만 정의된 비트**다.

## Further Reading

- **규격**: JESD270-4 §6.10 WOSC · §6.11 DCA/DCM (Table 72, 75, Figure 86–90) · §6.12 Rx Offset Calibration (Table 79–80, Figure 91) · §13 Test and Boundary Scan (Table 117–148)
- **다음 장**: [12 — 전기·타이밍·패키지와 Base Die 종합](../12_electrical_timing_package/)
- **관련**: [05 — 클럭킹](../05_clocking_dbi/) (짝수 규칙, WDQS-to-CK) · [08 — Parity](../08_parity/) (`DERR`) · [10 — 테스트와 복구](../10_test_repair/) (IEEE 1500 명령)
- **이해도 점검**: [퀴즈](../quiz/11_training_ieee1500_quiz/)
