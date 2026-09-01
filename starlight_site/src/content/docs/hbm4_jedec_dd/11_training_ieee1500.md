---
title: "11 — 트레이닝과 IEEE 1500"
description: JESD270-4 §6.10–6.12·§13 · WOSC·DCA/DCM·Rx offset의 순서 제약, 테스트 포트 두 갈래와 21개 명령
---

:::tip[🎯 Learning Objectives]
이 모듈을 마치면:

- **Order** 네 가지 트레이닝의 선후 제약을 규격 근거와 함께 배열한다.
- **Explain** WOSC가 채널·클럭과 무관하게 동작하는 구조와 정확도 결정 요인을 설명한다.
- **Interpret** `DERR` 핀이 세 가지 문맥에서 갖는 서로 다른 의미를 구분하고, monitor의 3-way 분기로 구현한다.
- **Differentiate** IEEE 1500 포트와 DA 포트의 역할·선택 방식·상호 배타성을 구분한다.
- **Evaluate** DA Test Port Lockout이 어떤 리셋으로도 해제되지 않는다는 성질을 평가하고, **자극 랜덤화가 검증 환경 자신의 관측 경로를 닫을 위험**을 제약으로 막는다.
- **Construct** 트레이닝 상태 모델을 만들어 앞 단계 재수행 시 **뒤 단계 유효 플래그가 전파 무효화**되도록 구현한다.
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

**검증 결론**: 검사해야 할 것은 "순서를 지켰는가"가 아니라 **"앞 단계를 다시 했을 때 뒤 단계도 다시 했는가"** 입니다. 순서만 보는 checker는 `RXoffC → VREFD → W2C → RXoffC` 를 통과시키는데, 마지막 재수행 때문에 앞의 두 결과가 이미 무효인 상태입니다 — 8.2 ①.
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

**검증 결론**: 측정 시간이 정확도를 정하므로 **자극이 그 값을 흔들어야** 합니다(`cp_wosc`). 짧은 측정만 도는 회귀는 granularity error가 지배하는 구간을 시험하지 못하고, 긴 측정만 도는 회귀는 그 반대입니다. matching error 값은 벤더 데이터시트에서 오므로 **환경 파라미터**입니다.
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

**검증 함의**: 코드 값과 실제 지연 변화가 선형이 아니므로 **자극이 목표 지연을 계산해 한 번에 설정할 수 없습니다.** 트레이닝 시퀀스는 탐색(sweep) 형태여야 하고, 그러면 **종료 조건과 최대 반복 횟수**가 필요합니다 — [10장](../10_test_repair/) Self Repair 루프와 같은 구조입니다.
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

## 🔬 검증 적용

### 8.1 무엇이 깨질 수 있는가

이 장에는 이 코스에서 유일한 결함 유형이 하나 있습니다 — **자극이 검증 환경 자신의 관측 경로를 닫아 버리는** 경우입니다.

| 조문 | 위반 형태 | 증상 | 잡히는 시점 |
|---|---|---|---|
| §13.1.1 — DA Lockout은 **전원 제거로만 해제** | 랜덤 MR 이미지가 `MR8` OP0을 1로 | 그 시뮬 동안 **DA 포트가 영구 잠김** | 잠긴 이후 전부 |
| §13.1.1 — `MR8` OP0은 **채널 0·4에만 정의** | MR 이미지를 전 채널 동일하게 적용 | **의도치 않은 잠금** | 없음 |
| §6.11.1/§6.12.1 — 트레이닝 **선후 제약** | 순서 위반 | 앞 결과가 무효인 채 진행 | 없음 |
| 같은 조문 — 재수행 시 **뒤 단계 무효화** | 앞 단계만 다시 하고 넘어감 | 오래된 뒤 단계 결과를 계속 씀 | 없음 |
| §6.12.1 — Rx offset 중 **DQ를 float** | 자극이 DQ를 구동한 채 시작 | 보정이 어긋남 | 없음 |
| §6.11.3 — DCM **히스테리시스 flip** | 한 방향만 측정 | 측정값이 부정확 | 없음 |
| §6.11 — `fCKDCA` 미만 **미지원** | 저주파 프로파일에서 실행 | 미정의 | 없음 |
| §5·§6.11.3·§8 — `DERR` **세 문맥** | 모드 미분기 | 가짜 오류 또는 잘못된 판독 | 즉시(잘못된 방향) |
| — 두 트레이닝 모드 **동시 활성** | `MR8` OP3와 `MR6` OP6을 함께 1 | `DERR` 해석이 모호 | 없음 |
| §13.1 — `DA12` **상호 배타** | 두 포트가 함께 열려 있다고 가정 | 접근 실패 | 즉시 |
| §13.1 — DA 활성 시 **`CATTRIP` 무효** | 유효로 읽음 | 가짜 과열 보고 | 산발적 |
| §13.2 — `WSO`는 **채널별** | 중재가 필요하다고 가정 | 병렬성 미활용(성능만) | — |
| §13.5 — `DEVICE_ID` **선행 읽기** | 안 읽고 구성 하드코딩 | [02](../02_addressing_bank_groups/)·[06장](../06_row_commands/) 구성이 전부 틀림 | 없음 |

:::caution[자극이 스스로 문을 닫는 경우]
[04장](../04_mode_registers/)에서 초기화 MR 이미지를 랜덤화하는 `mr_image_cfg` 를 만들었습니다. 그 랜덤화가 `MR8` OP0을 1로 만들면 어떻게 되는가 — **DA 테스트 포트가 그 전원 사이클 내내 잠깁니다.**

§13.1.1이 못 박습니다. `RESET_n`도, IEEE1500 `HBM_RESET`도, `MRS`로 0을 쓰는 것도, `MODE_REGISTER_DUMP_SET`도 **해제하지 못합니다.** 전원 제거만이 유일한 방법입니다.

이 코스에서 본 sticky 상태들과 비교하면 가장 강합니다.

| 상태 | 해제 방법 |
|---|---|
| `CATTRIP` ([03장](../03_init_reset_power/)) | 전원 차단 |
| Auto ECS ([09장](../09_ecc_ecs_sev/)) | 장치 `RESET` |
| MISR compare sticky ([10장](../10_test_repair/)) | 명시적 클리어 |
| **DA Port Lockout** | **전원 제거만** |

그리고 함정이 하나 더 있습니다 — 이 비트는 **채널 0 또는 4에만 정의**됩니다. MR 이미지를 전 채널에 동일하게 적용하는 초기화 시퀀스는 그 비트가 **의도치 않게 1로 나가는지** 확인해야 합니다.

검증 환경의 대응은 둘입니다.

1. **랜덤화에서 제외한다** — `mr_image_cfg` 의 제약에 `mr[8][0] == 0` 을 넣습니다. 잠금은 랜덤하게 일어나면 안 되는 사건입니다.
2. **잠금 테스트는 격리한다** — 잠금 이후에는 DA 경로로 아무것도 확인할 수 없으므로, 그 테스트는 잠금 확인만 하고 끝나야 합니다.
:::

:::caution[`DERR`의 세 번째 얼굴]
이 코스에서 `DERR`가 세 번째로 다른 의미를 갖습니다.

```
MR6 OP6 == 1   →  듀티 사이클 측정 결과 (HIGH = ≥50%)      ← 이 장
MR8 OP3 == 1   →  위상 검출기 판독 (HIGH = early)          ← 05장
그 외          →  데이터 패리티 오류                        ← 08장
```

monitor가 **두 MR 비트를 함께 보고 3-way 분기**해야 합니다. 그리고 **두 모드를 동시에 켜면 해석이 모호**해지므로, 자극 쪽에서 상호 배타를 보장해야 합니다.

monitor가 설정 레지스터를 참조한다는 것은 [05장](../05_clocking_dbi/)에서 이미 나온 구조인데, 여기서 참조 대상이 **둘로 늘어납니다.** 이 상태를 어디서 받을지가 환경 설계 항목이 됩니다 — RAL 모델을 monitor에 주입하거나, MR 변경을 analysis port로 방송하는 방식이 있습니다([`hbm_dv` Ch06](../../hbm_dv/06_env_hierarchy/)).
:::

### 8.2 어떻게 잡는가 — 수단 선택

| 규칙 | 성격 | 수단 | 이유 |
|---|---|---|---|
| 트레이닝 선후·무효화 전파 | **상태 기계** | **시퀀스 상태 모델** | 유효 플래그가 단계마다 있고 전파된다 |
| `DERR` 3-way 해석 | **문맥 의존 디코드** | **monitor + 설정 참조** | 값이 아니라 의미가 바뀐다 |
| DA Lockout | **비가역 상태** | **랜덤화 제약 + 격리 테스트** | 잘못 들어가면 되돌릴 수 없다 |
| Rx offset 중 DQ float | **자극 조건** | **SVA (자극 측 검사)** | DUT 버그가 아니다 |

**① 트레이닝 순서와 무효화 전파**

핵심은 "순서를 지켰는가"가 아니라 **"앞 단계를 다시 했을 때 뒤 단계도 다시 했는가"** 입니다.

```systemverilog
// §6.11.1, §6.12.1 — 앞 단계는 뒤 단계의 전제를 바꾼다.
// 재수행하면 뒤 단계의 유효 플래그를 무효화해야 한다.
class training_state_model extends uvm_object;
  `uvm_object_utils(training_state_model)
  // 순서: RXoffC → (DCA/DCM) → VREFD → WDQS-to-CK
  bit valid_rxoff, valid_dca, valid_vrefd, valid_w2c;

  function void on_rxoff_done();
    valid_rxoff = 1;
    // Rx offset 은 수신기 판정 기준점을 옮긴다 → 그 위에서 잡은 것이 전부 무효
    valid_vrefd = 0; valid_w2c = 0;
  endfunction

  function void on_dca_done();
    valid_dca = 1;
    valid_w2c = 0;                  // 듀티가 바뀌면 CK 대비 위상 관계도 바뀐다
  endfunction

  function void on_vrefd_done(); valid_vrefd = 1; valid_w2c = 0; endfunction
  function void on_w2c_done();   valid_w2c   = 1;                endfunction

  // 정상 동작 진입 전에 확인한다
  function void check_ready();
    if (!valid_dca || !valid_vrefd || !valid_w2c)
      `uvm_error("TRAINING", $sformatf(
        "트레이닝이 완결되지 않았다 (dca=%0b vrefd=%0b w2c=%0b). "
      + "앞 단계를 재수행했다면 뒤 단계도 다시 해야 한다 (§6.11.1, §6.12.1)",
        valid_dca, valid_vrefd, valid_w2c))
  endfunction
endclass
```

`on_rxoff_done()` 이 **뒤 단계 플래그를 내리는 것**이 이 모델의 요점입니다. 순서만 검사하는 checker는 "RXoffC → VREFD → W2C → RXoffC" 를 통과시키는데, 마지막 RXoffC 때문에 앞의 두 결과가 무효가 된 상태입니다.

**② `DERR` 3-way 디코딩**

```systemverilog
// DERR 은 문맥에 따라 세 가지 의미를 갖는다. monitor 가 MR 상태를 알아야 한다.
typedef enum {DERR_PARITY, DERR_PHASE, DERR_DUTY} derr_ctx_e;

function automatic derr_ctx_e derr_context(bit mr8_op3, bit mr6_op6);
  // 두 트레이닝 모드를 동시에 켜면 해석이 모호하다 — 자극 측에서 막아야 한다
  if (mr8_op3 && mr6_op6)
    `uvm_error("DERR_CTX",
      "WDQS2CK 트레이닝과 DCM 을 동시에 활성화했다. DERR 해석이 모호해진다")
  if (mr6_op6) return DERR_DUTY;      // §6.11.3
  if (mr8_op3) return DERR_PHASE;     // §6.1.1 ([05장])
  return DERR_PARITY;                 // §6.4.2 ([08장])
endfunction

// 문맥 밖에서 DERR 을 패리티 오류로 보고하지 않는지 확인
a_no_false_parity_err: assert property (@(posedge ck) disable iff (!rst_n)
    (derr_context(mr8_q[3], mr6_q[6]) != DERR_PARITY) |-> !parity_error_reported)
  else `uvm_error("DERR_CTX", "트레이닝 모드에서 DERR 을 패리티 오류로 보고했다")
```

**③ DA Lockout — 자극 제약이 먼저다**

```systemverilog
// §13.1.1 — MR8 OP0 은 채널 0·4 에만 정의되고, 1 로 쓰면 전원 제거 전까지 풀리지 않는다.
// 정상 회귀의 MR 이미지 랜덤화에서 반드시 제외한다 ([04장]의 mr_image_cfg 확장).
class mr_image_cfg_ext extends mr_image_cfg;
  `uvm_object_utils(mr_image_cfg_ext)
  rand int unsigned channel;

  // 잠금은 랜덤하게 일어나면 안 되는 사건이다
  constraint c_no_accidental_lockout { mr[8][0] == 1'b0; }

  // 전 채널에 같은 이미지를 쓰는 시퀀스라면, 채널 0·4 에서 특히 확인한다
  constraint c_lockout_channels {
    (channel inside {0, 4}) -> (mr[8][0] == 1'b0);
  }
endclass
```

잠금 동작 자체를 검증하려면 **별도 테스트**로 격리합니다. 그리고 그 테스트는 잠금 이후 DA 경로로 아무것도 확인할 수 없으므로, **잠금 확인만 하고 종료**해야 합니다.

**④ Rx offset 중 DQ float — 자극 측 검사**

```systemverilog
// §6.12.1 — 트레이닝 시작 MRS 시점에 호스트가 DQ 를 float 해야 한다.
// DUT 버그가 아니라 자극이 지켜야 할 조건이다.
a_rxoff_dq_float: assert property (@(posedge ck) disable iff (!rst_n)
    rxoff_training_active |-> (dq_oe === '0))
  else `uvm_error("RXOFFC", "Rx offset 트레이닝 중 자극이 DQ 를 구동하고 있다 (§6.12.1)")
```

### 8.3 무엇을 덮었다고 말할 수 있는가

```systemverilog
covergroup cg_hbm4_training with function sample(
    train_stage_e stage, bit retrained_downstream, derr_ctx_e dctx,
    bit dcm_flip, port_sel_e port, bit lockout_tested, int wosc_time);
  option.per_instance = 1;

  // --- 네 트레이닝을 각각 수행했는가 --------------------------------------
  cp_stage : coverpoint stage {
    bins rxoffc = {TRAIN_RXOFFC};      // 선택 기능 — DEVICE_ID 로 지원 확인
    bins dca    = {TRAIN_DCA};
    bins dcm    = {TRAIN_DCM};
    bins vrefd  = {TRAIN_VREFD};
    bins w2c    = {TRAIN_WDQS2CK};
  }

  // --- 재수행 시 무효화 전파 — 이 장의 핵심 축 ---------------------------
  // 앞 단계를 다시 한 뒤 뒤 단계도 다시 했는가
  cp_retrain : coverpoint retrained_downstream {
    bins not_applicable = {0};
    bins propagated     = {1};        // 이 bin 이 비면 무효화 전파는 미검증
  }

  // --- DERR 세 문맥 -------------------------------------------------------
  cp_derr : coverpoint dctx {
    bins parity = {DERR_PARITY};      // [08장]
    bins phase  = {DERR_PHASE};       // [05장]
    bins duty   = {DERR_DUTY};        // 이 장
  }

  // --- DCM 히스테리시스 (§6.11.3) ----------------------------------------
  // no-flip 과 flip 두 방향을 모두 측정해야 히스테리시스가 상쇄된다
  cp_dcm_flip : coverpoint dcm_flip { bins no_flip = {0}; bins flipped = {1}; }

  // --- 포트 선택 (§13.1) --------------------------------------------------
  cp_port : coverpoint port {
    bins ieee1500  = {PORT_IEEE1500};   // DA12 = LOW (기본, 내부 풀다운)
    bins da        = {PORT_DA};         // DA12 = HIGH — IEEE1500 비활성
    bins both_shut = {PORT_NONE};       // DA12 LOW + WRST_n LOW
  }
  // DA 활성 중 CATTRIP 은 무효다 — 그 상태를 겪어 봤는가
  x_da_cattrip : cross cp_port, cp_derr {
    ignore_bins rest = binsof(cp_port.ieee1500) || binsof(cp_port.both_shut);
  }

  // --- Lockout — 격리 테스트에서만 -----------------------------------------
  cp_lockout : coverpoint lockout_tested { bins tested = {1}; }

  // --- WOSC 측정 시간이 정확도를 정한다 (§6.10) ---------------------------
  cp_wosc : coverpoint wosc_time {
    bins short  = {[1:99]};      // 짧으면 정확도가 낮다
    bins normal = {[100:999]};
    bins long   = {[1000:$]};
  }
endgroup
```

세 축이 목표입니다.

- **`cp_retrain.propagated`** — 앞 단계 재수행 후 뒤 단계도 다시 했는가. 이 bin이 비면 무효화 전파 로직이 통째로 미검증이고, 순서만 지키는 checker는 그것을 알려 주지 않습니다.
- **`cp_derr` 세 bin** — 세 문맥을 모두 겪어야 monitor의 3-way 분기가 검증됩니다. 트레이닝을 안 돌리는 회귀는 `parity` 만 차 있습니다.
- **`cp_dcm_flip` 두 bin** — 히스테리시스 상쇄는 **두 방향 측정이 짝을 이룰 때만** 성립합니다. 한 방향만 돌면 그 보정 자체가 검증되지 않습니다.

### 8.4 어떻게 자극하는가

**① 트레이닝 순서 — 정상과 재수행 두 갈래**

```systemverilog
// (a) 정상 순서
run_rxoff_calibration();     // §6.12.1 — VREFD·W2C 보다 먼저
run_dca();                   // §6.11.1 — W2C 보다 먼저
run_vrefd_training();
run_wdqs2ck_alignment();     // [05장]

// (b) 재수행 — 여기가 검사 지점이다
run_rxoff_calibration();     // 다시 하면 VREFD·W2C 가 무효가 된다
// 여기서 곧바로 정상 동작에 들어가면 8.2 ① 의 check_ready() 가 잡아야 한다
run_vrefd_training();        // 올바른 처리 — 뒤 단계를 다시 한다
run_wdqs2ck_alignment();
```

(b)의 **중간 지점**이 negative 테스트입니다 — 재수행 후 뒤 단계를 건너뛰고 정상 동작에 진입해 보고, 환경이 그것을 잡는지 확인합니다.

**② `DERR` 세 문맥을 각각** — 각 모드에서 `DERR`를 관측하고, **패리티 오류로 보고되지 않는지** 확인합니다. 이는 DUT가 아니라 **환경의 monitor를 검증**하는 테스트입니다([08장](../08_parity/) 5.4 ⑤와 같은 성격).

그리고 **두 모드 동시 활성** negative — `MR8` OP3와 `MR6` OP6을 함께 1로 써 보고 8.2 ②의 검사가 잡는지 봅니다.

**③ DCM은 반드시 쌍으로** — `MR6` OP7(flip)을 0과 1로 각각 측정하고 `tDCMM` 대기를 지킵니다. 한 방향 측정만으로 결론짓는 시퀀스는 히스테리시스 보정을 건너뛴 것입니다.

**④ DA Lockout 격리 테스트**

```
① 정상 회귀 : mr_image_cfg 제약으로 MR8 OP0 = 0 강제 (8.2 ③)
② 격리 테스트 : 채널 0 에 MR8 OP0 = 1 을 쓴다
   → DA 포트 접근이 실패해야 한다
   → RESET_n · HBM_RESET · MRS(0) · MODE_REGISTER_DUMP_SET(0) 모두
      해제하지 못하는지 각각 확인한다  ← 네 경로를 다 시험해야 의미가 있다
   → 테스트 종료 (이후 DA 경로로는 아무것도 못 한다)
③ 별도 테스트 : 전 채널 동일 MR 이미지를 쓰는 초기화가
   채널 0·4 에서 OP0 을 1 로 내보내지 않는지 확인
```

②의 **네 경로**가 요점입니다. 하나만 시험하면 "리셋으로 안 풀린다"까지만 확인되고, MR에 0을 써도 안 풀린다는 성질은 미검증으로 남습니다.

**⑤ `DEVICE_ID` 선행 읽기를 환경 구성에 넣는다** — [06장](../06_row_commands/)에서 본 순서가 여기서 완성됩니다.

```
reset → tINIT3 → WRST_n HIGH → DEVICE_ID 읽기
   → 밀도 코드      → 주소 구성 ([02장])
   → RAAIMT/MMT/DEC → RAA 모델 ([06장])
   → ARFM 지원      → MR8 값 결정 ([06장])
   → RXoffC 지원    → 이 장의 ① 수행 여부
   → 그 뒤에야 MR 프로그램과 트래픽
```

`WRST_n` 을 상시 LOW로 두는 프로파일도 규격이 허용하지만([03장](../03_init_reset_power/)), 그 경우 위 값들을 **전부 하드코딩**해야 합니다. 두 프로파일을 모두 돌려야 환경이 양쪽에 대응하는지 확인됩니다.

## 9. 대표 문제 — dry-run

### 문제 1 — 트레이닝 순서

> 정상 동작 중 온도가 크게 올라 WOSC 계수값이 트레이닝 시점 대비 크게 벗어났다. Rx offset calibration을 다시 수행했다. 그 다음에 해야 할 일은?

<details>
<summary>풀이</summary>

**`VREFD` 트레이닝과 WDQS-to-CK 정렬을 다시 수행해야 한다.**

§6.12.1이 *"Rx offset calibration은 DRAM write 캘리브레이션 트레이닝에 영향을 주므로 `VREFD` 트레이닝과 WDQS-to-CK 정렬보다 먼저 수행되어야 한다"* 고 규정한다. 순서가 강제된다는 것은, **앞 단계를 다시 하면 뒤 단계의 전제가 바뀐다**는 뜻이다.

Rx offset은 **수신기의 판정 기준점**을 옮기므로, 그 위에서 잡았던 `VREFD` 값과 위상 정렬이 더 이상 유효하지 않다.

**검증 결론**: `training_state_model` 이 각 단계의 유효 플래그를 들고, **앞 단계 재수행 시 뒤 단계 플래그를 무효화**한다(8.2 ①). 그리고 `cp_retrain.propagated` bin이 비어 있으면 이 전파 로직은 **한 번도 시험되지 않은 것**이다.
</details>

### 문제 2 — `DERR` 해석

> 컨트롤러가 `MR6` OP6(DCM)을 1로 두고 측정 중이다. 동시에 write 버스트가 진행되어 `DERR1`이 HIGH로 관측됐다. 데이터 패리티 오류인가?

<details>
<summary>풀이</summary>

**아니다 — 그리고 애초에 이 상황이 만들어지면 안 된다.**

DCM 활성 시 `DERR1`은 **DWORD1(PC1)의 WDQS 듀티 사이클 측정 결과**이며, HIGH는 **듀티 ≥ 50%** 를 뜻한다(Table 75).

게다가 DCM 모드에서 **허용되는 커맨드는 REFab·REFpb·RFMab·RFMpb·RNOP·CNOP·MRS 뿐**이다(§6.11.3). **write 커맨드 자체가 허용되지 않는다.**

**검증 결론**: 두 가지를 지켜야 한다.
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

**검증 주의**: `MR8` OP0은 **채널 0 또는 4에만 정의**된 비트다. 두 가지를 지켜야 한다 — ① MR 이미지 랜덤화에서 **이 비트를 제외**한다(랜덤이 1을 만들면 자극이 관측 경로를 영구히 닫는다), ② 전 채널에 같은 이미지를 쓰는 초기화 시퀀스가 **채널 0·4에서 이 비트를 1로 내보내지 않는지** 확인한다.
</details>

## 핵심 정리

- 트레이닝에는 **순서 제약**이 있다 — **RXoffC → (DCA/DCM) → VREFD → WDQS-to-CK**. 앞 단계를 재수행하면 **뒤 단계도 무효**다. 검사할 것은 순서가 아니라 **무효화 전파**이며, `cp_retrain.propagated` 가 비면 그 로직은 미검증이다.
- **WOSC는 채널·클럭과 무관**하게 동작하며 계수 중 `CK`·`WDQS`·`WRCK`가 필요 없다. **전원 인가 시 기본 비활성**이다.
- WOSC 결과는 **오버플로**(2²⁴ 이상)나 **`RESET_n` 중단**에서 무효가 된다. **`WRST_n`은 영향이 없다** — 두 리셋의 비대칭이 여기서도 확인된다.
- 정확도는 **측정 시간이 길수록** 좋아지지만 **matching error(벤더 지정)가 상한**을 만든다. 무작정 길게 돌릴 이유가 없다.
- **DCA는 분주기 앞단**에 있어 **read/write 양쪽**에 작용한다. 범위 **−7~+7**, 최대 오프셋 **15~35 ps**, **스텝이 비선형(2~5 ps)** 이므로 **탐색으로 접근**해야 한다.
- DCA·DCM 모두 **`fCKDCA` 미만 주파수에서는 미지원**이며, 그때는 DCA 코드를 **기본값 `0000`** 으로 둔다.
- DCM은 **히스테리시스 상쇄를 위해 flip 측정을 함께** 수행한다. 측정 구간 내내 **WDQS 펄스가 짝수**여야 한다 — 짝수 규칙의 세 번째 등장.
- Rx offset 트레이닝은 **호스트가 DQ를 float** 해야 하며, 필요한 부속 기능은 **장치가 자동으로 켜고 끈다**. `tOSCAL` 최대 **6 μs**.
- **`DERR`는 세 가지 의미**를 갖는다 — 패리티 오류 / 위상 검출기 판독 / 듀티 측정 결과. monitor가 **`MR8` OP3와 `MR6` OP6을 함께 보고 3-way 분기**해야 하며, 두 모드 동시 활성은 자극 측에서 막는다. 세 문맥을 다 겪지 않은 회귀는 `parity` bin만 차 있다.
- IEEE 1500은 **`WSO`를 채널마다 복제**해 채널 병렬 실행을 가능하게 한다. **초기화 후 전 생애에 걸쳐**, power-down·self refresh 중에도 사용 가능하다.
- **테스트 포트는 양산 전용이 아니라 부팅에 필수**다 — `DEVICE_ID`에서 밀도 코드·RAA 문턱값·ARFM/RXoffC 지원 여부를 읽어야 MR 이미지를 확정할 수 있다. 환경도 같은 순서를 따라야 하고, `WRST_n`을 상시 LOW로 두는 프로파일에서는 그 값들을 **전부 하드코딩**해야 한다 — 두 프로파일을 모두 돌려야 환경이 양쪽에 대응하는지 확인된다.
- DA 포트는 **`DA12`로 IEEE 1500과 배타 선택**되며, 내부 풀다운으로 **기본은 IEEE 1500** 쪽이다. DA 활성 시 **`CATTRIP` 값은 무시**해야 한다.
- ⚠️ **DA Port Lockout(`MR8` OP0)은 전원 제거로만 해제된다.** 어떤 리셋으로도, MR에 0을 써도 풀리지 않는다. **채널 0 또는 4에만 정의된 비트**다.
- 그래서 **MR 이미지 랜덤화에서 이 비트를 제외**해야 한다. 랜덤이 1을 만들면 **자극이 검증 환경 자신의 관측 경로를 영구히 닫는다** — 이 코스에서 유일한 유형의 결함이다. 잠금 검증은 격리된 테스트로 두고, **네 해제 경로(RESET_n · HBM_RESET · MRS(0) · MODE_REGISTER_DUMP_SET(0))를 모두** 시험해야 의미가 있다.

## Further Reading

- **규격**: JESD270-4 §6.10 WOSC · §6.11 DCA/DCM (Table 72, 75, Figure 86–90) · §6.12 Rx Offset Calibration (Table 79–80, Figure 91) · §13 Test and Boundary Scan (Table 117–148)
- **다음 장**: [12 — 전기·타이밍·패키지와 Base Die 종합](../12_electrical_timing_package/)
- **관련**: [05 — 클럭킹](../05_clocking_dbi/) (짝수 규칙, WDQS-to-CK) · [08 — Parity](../08_parity/) (`DERR`) · [10 — 테스트와 복구](../10_test_repair/) (IEEE 1500 명령)
- **이해도 점검**: [퀴즈](../quiz/11_training_ieee1500_quiz/)
