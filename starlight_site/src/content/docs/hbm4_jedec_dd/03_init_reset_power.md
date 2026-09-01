---
title: "03 — 초기화·리셋·전원 시퀀스"
description: JESD270-4 §4 · 초기화 세 경로, 클럭 없는 구간의 타이밍 검사, 임의 상태 리셋, lane repair 절차 checker
---

:::tip[🎯 Learning Objectives]
이 모듈을 마치면:

- **Sequence** 전원 인가부터 첫 MRS까지의 초기화 단계를 순서와 타이밍 제약과 함께 재구성한다.
- **Explain** 전원 램프 순서가 왜 강제되는지(latch-up 회피)와 각 부등식이 무엇을 보장하는지 설명한다.
- **Construct** 클럭이 토글하지 않는 구간의 타이밍 검사를 시각 기반으로 구현하고, `tINIT6`이 왜 다른 형태여야 하는지 설명한다.
- **Derive** 초기화 경로 세 갈래 × 리셋 진입 상태에서 coverage cross를 도출한다.
- **Analyze** `RESET_n` 기능 리셋과 IEEE 1500 포트 리셋의 상호작용을 구분하고, `HBM_RESET` 경로가 왜 monitor에서 누락되기 쉬운지 판단한다.
- **Evaluate** soft lane repair가 hard lane repair를 덮어쓰는 위험을 평가하고, 그 절차 위반을 잡는 프로토콜 checker를 설계한다.
:::

:::note[Prerequisites]
- [01 — 규격 지형도와 조직 구조](../01_landscape_organization/) — 전역 신호(`RESET_n`·IEEE1500 포트)의 위치
- [02 — 주소 체계와 뱅크 그룹](../02_addressing_bank_groups/) — 상태도가 생략한 "즉시 리셋" 경로
:::

:::caution[인용 고지]
본 장은 **JESD270-4 (2025-04, WIP draft)** §4를 근거로 **요약·재구성**한 것입니다. 표·그림은 옮기지 않고 번호로 지시하며, 타이밍 값은 설명에 필요한 범위에서 **재배열해 인용**합니다. 정밀 수치는 **JEDEC 원문 우선**.
:::

---

## 1. 두 개의 리셋 — 기능 리셋과 테스트 포트 리셋

§4는 본론에 들어가기 전에 `RESET_n`(기능)과 `WRST_n`(IEEE 1500 포트) 사이의 관계를 네 줄로 정리합니다. 설계 판단이 여기서 갈리므로 먼저 봅니다.

| 조문 (§4) | 검증 함의 |
|---|---|
| **기능 리셋은 IEEE 1500 포트도 함께 리셋할 것을 요구한다** | `RESET_n` 어서트 시 `WRST_n`도 함께 내려가는지 **검사 대상**. 둘을 따로 구동하는 자극은 규격 위반이다 |
| **IEEE 1500 포트는 정상 동작에 영향 없이 언제든 리셋할 수 있다** | 역방향은 독립. 테스트 포트만 리셋해도 mission mode는 무사 |
| 포트는 `RESET_n` 해제 후 **최소 시간이 지나야** 리셋에서 빠져나올 수 있고, 그때 **제한된 명령 집합**만 사용 가능 | 시점·명령 집합 모두 assertion 대상. 허용 밖 명령을 발행하는 negative 테스트도 필요 |
| **필요 없으면 정상 동작 내내 `WRST_n = LOW`로 두어도 된다** | 테스트 포트를 안 쓰는 시스템은 아예 리셋에 묶어둘 수 있다 |

두 리셋의 **비대칭성**이 핵심입니다 — 기능 리셋은 테스트 포트를 끌고 가지만, 테스트 포트 리셋은 기능 동작을 건드리지 않습니다.

## 2. 전원 램프 — 순서가 강제되는 이유

§4.1 1단계는 네 개의 전원(`VPP`, `VDDC`, `VDDQ`, `VDDQL`)에 **부등식 제약**을 겁니다. 목적이 명시되어 있습니다 — **여러 전원이 동시에 올라올 때의 latch-up 방지**.

### 부등식 세 개

첫 전원이 300 mV에 도달한 시점 이후로 다음이 유지되어야 합니다(§4.1).

| 관계 | 조건 | 성격 |
|---|---|---|
| `VPP` ↔ `VDDC` | `VPP > VDDC + 200 mV` | 고정 마진 |
| `VDDC` ↔ `VDDQ` | `VDDC > VDDQ + VSP` | **VSP는 vendor specific** |
| `VDDQ` ↔ `VDDQL` | `VDDQ > VDDQL − 200 mV` | 고정 마진 |

그리고 램프 **시작 순서**도 강제됩니다 — `VPP`는 `VDDC`와 동시 또는 먼저, `VDDC`는 `VDDQ`와 동시 또는 먼저, `VDDQ`는 `VDDQL`과 동시 또는 먼저.

권장 방식은 **높은 전압에서 낮은 전압 순으로 순차 인가**하며, 각 전원은 **기울기 반전 없이(without slope reversal)** 올라가야 합니다(§4.1, Figure 4).

:::tip[VSP가 vendor specific인 이유]
`VDDC`와 `VDDQ`의 절대 레벨 자체가 **vendor specific**입니다([01장](../01_landscape_organization/), §2). 두 값이 벤더마다 다르니 그 사이에 필요한 마진도 고정할 수 없고, 그래서 규격은 `VSP`라는 이름만 정의하고 값은 **벤더 데이터시트로 넘깁니다.**

검증 관점에서는 `VSP`가 **환경 파라미터여야 한다**는 뜻입니다. 상수로 박아 두면 벤더를 바꿀 때 검사가 조용히 틀린 값으로 돌아갑니다. 규격이 `vendor specific`이라 쓴 자리는 전부 같은 처리를 받습니다 — **config로 올리고 회귀에서 값을 바꿔 가며 돌린다**([index의 조동사 규칙](../)).
:::

전 전원은 `tINIT0`(최대 200 ms) 안에 정상 동작 범위에 들어와야 하고, 그 램프 구간 동안 `RESET_n`·`WRST_n`을 포함한 모든 입력은 **정의되지 않은 상태(LOW/HIGH/Hi-Z)** 여도 됩니다.

## 3. 초기화 시퀀스 — 단계와 타이밍

```d2
direction: right

P0: "① 전원 램프\nVPP→VDDC→VDDQ→VDDQL\n부등식 유지 · 기울기 반전 금지" {
  style.fill: "#eceff1"; style.font-color: "#0A0F25"
}
P1: "② RESET_n·WRST_n LOW\n(< 0.2×VDDQ)\n안정 전원에서 유지" {
  style.fill: "#ffebee"; style.font-color: "#0A0F25"
}
P2: "③ CK 정적 구동\nCK_t=L, CK_c=H" {
  style.fill: "#fff8e1"; style.font-color: "#0A0F25"
}
P3: "④ RESET_n HIGH\nR[3:0]=PDE, C[2:0]=CNOP\n내부 퓨즈 적용 + I/O 임피던스 보정\n→ precharged power-down 진입" {
  style.fill: "#e3f2fd"; style.font-color: "#0A0F25"
}
P4: "⑤ CK 토글 시작\n안정 클럭 유지 후\nR[3:0] HIGH (PDX)" {
  style.fill: "#e8f5e9"; style.font-color: "#0A0F25"
}
P5: "⑥ MRS 발행\n응용에 맞게 설정" {
  style.fill: "#f3e5f5"; style.font-color: "#0A0F25"
}
P6: "⑦ 정상 동작" {
  style.fill: "#c8e6c9"; style.font-color: "#0A0F25"
}

P0 -> P1: "tINIT0 내 완료"
P1 -> P2: "tINIT1 유지"
P2 -> P3: "tINIT2 선행"
P3 -> P4: "tINIT3 (퓨즈·보정)"
P4 -> P5: "tINIT4 → tINIT5"
P5 -> P6
```

### 단계별로 무엇이 일어나는가

**② `RESET_n` / `WRST_n` LOW** — `tINIT0` 만료 이전 또는 그 시점에 `0.2 × VDDQ` 아래로 구동합니다. `RESET_n`은 **안정 전원 상태에서 최소 `tINIT1`** 동안 유지됩니다. `tINIT6` 경과 후 장치는 출력을 정적 레벨로 몰아둡니다 — `RDQS_t` LOW / `RDQS_c` HIGH, 그리고 `AERR`·`DERR`·`CATTRIP`을 LOW로.

**③ CK 정적 구동** — `RESET_n`이 HIGH로 올라가기 **`tINIT2` 전에** `CK_t`는 정적 LOW, `CK_c`는 정적 HIGH로 구동되어야 합니다. 아직 토글하지 않습니다.

**④ `RESET_n` HIGH — 여기서 가장 많은 일이 일어난다**

- `R[3:0]`을 **PDE 상태(H, L, H, L)**, `C[2:0]`을 **CNOP 상태(H, H, H)** 로 구동하고 `tINIT7` 동안 유지한 뒤에야 CK를 토글할 수 있습니다.
- `R[9:4]`와 `C[7:3]`은 **정의되지 않은 상태여도 됩니다.**
- 장치는 **precharged power-down 상태로 리셋**됩니다.
- `tINIT3` 동안 장치는 **내부 퓨즈 구성 데이터를 읽어 적용**하고 **I/O 드라이버 임피던스 보정**을 수행합니다.
- 이 시점에 `WRST_n`을 선택적으로 HIGH로 올려 **IEEE 1500 명령의 부분집합**을 쓸 수 있습니다. 그러려면 다른 IEEE1500 입력들을 `tWINIT2` 전에 규정대로 구동해야 합니다.
- `CATTRIP`은 `tINIT6` 종료부터 `tINIT3` 종료까지 **LOW를 유지**해야 하고, 유효 데이터는 `tINIT3` 이후에 시작됩니다.

**⑤ CK 토글과 PDX** — `R[3:0]`/`C[2:0]`을 PDE/CNOP로 유지한 채 CK를 시작하고, **최소 `tINIT4` 동안 안정 클럭**을 유지한 뒤 `R[3:0]`을 HIGH로 구동합니다. 주의할 점 셋:

- `R[3:0]` 중 **`R[0]`은 동기 신호**이므로 클럭에 대한 **셋업 시간 `tIS`** 를 만족해야 합니다.
- **RNOP과 CNOP 커맨드가 `tIS`/`tIH`를 만족한 상태로 등록**되어야 합니다.
- `R[3:0]`이 HIGH로 등록된 후 **`tINIT5`** 를 지나야 첫 MRS를 발행할 수 있습니다.
- `R[3:0]` HIGH 시점 또는 그 이전에 `WDQS_t`는 정적 LOW, `WDQS_c`는 정적 HIGH로 구동되어야 합니다.

그리고 **안정 CK는 계속 유지**되어야 합니다 — 채널이 power-down 또는 self-refresh에 있을 때를 제외하고([07장](../07_column_commands/)).

**⑥–⑦ MRS 발행 후 정상 동작.**

### 타이밍 파라미터 — 단계별로 묶어 읽기

Table 7의 값들을 시퀀스 순서로 재배열하면 이렇습니다.

| 단계 | 파라미터 | 제약 | 성격 |
|---|---|---|---|
| ① | `tINIT0` | 0.01 ~ **200 ms** | 전원 램프 시간 (범위) |
| ② | `tINIT1` | **≥ 200 µs** | 전원 안정 후 `RESET_n` LOW 유지 |
| ② | `tINIT6` | **≤ 100 ns** | 출력 정적 레벨 도달 (**최대** 제약) |
| ③ | `tINIT2` | **≥ 10 ns** | CK 정적 구동 선행 시간 |
| ④ | `tINIT7` | **≥ 2 nCK** | PDE/CNOP 유지 후 CK 토글 |
| ④ | `tINIT3` | **≥ 4 ms** | 퓨즈 적용 + 임피던스 보정 |
| ⑤ | `tINIT4` | **≥ 10 nCK** | `R[3:0]` HIGH 전 안정 클럭 |
| ⑤ | `tINIT5` | **≥ 200 ns** | 첫 MRS 전 유휴 시간 |
| 리셋 | `tPW_RESET` | **≥ 1 µs** | 안정 전원에서 `RESET_n` LOW 폭 |

:::caution[단위가 세 종류다]
`ms` · `µs` · `ns` · `nCK`가 섞여 있습니다. `tINIT3`(4 ms)와 `tINIT2`(10 ns) 사이에는 **여섯 자릿수 차이**가 있고, `tINIT4`·`tINIT7`은 **클럭 사이클 단위**라 주파수에 따라 절대 시간이 달라집니다.

checker도 같은 이유로 갈라집니다. `nCK` 단위 제약(`tINIT4`·`tINIT7`)은 클럭 사이클로 세야 주파수가 바뀌어도 맞고, 시간 단위 제약(`tINIT1`·`tINIT3`)은 **시각으로 세야** 맞습니다. 하나로 통일하려 들면 둘 중 하나가 틀립니다 — 7.2절.

그리고 `tINIT6`만 **최대(max) 제약**이라는 점에 주의하세요 — 나머지는 최소값입니다. 장치가 그 안에 출력을 안정시킨다는 **보장**이지 컨트롤러가 기다려야 할 시간이 아닙니다. 이 하나를 최소로 오해하면 checker의 부등호가 뒤집히고, 정상 동작을 FAIL로 보고합니다.
:::

## 4. 안정 전원 상태의 리셋 — 그리고 sticky한 것

§4.2는 전원을 유지한 채 기능 리셋을 하는 경우입니다. 두 가지 경로가 있습니다.

1. **`RESET_n`을 LOW로** 최소 `tPW_RESET` 동안 구동. 이때 `WRST_n`과 `CATTRIP`을 제외한 다른 입력은 미정의 상태여도 됩니다. `R[3:0]`=PDE, `C[2:0]`=CNOP를 `tINIT7` 동안 유지한 뒤 CK 토글.
2. **IEEE 1500 포트의 `HBM_RESET` 명령**을 사용. 이 경우 **`RESET_n`은 HIGH로 유지된 채** 재초기화가 수행됩니다.

이후는 전원 인가 시퀀스의 3~6단계를 따릅니다.

:::caution[CATTRIP은 sticky다]
> `CATTRIP` 출력은 **sticky이며 기능 리셋으로 지워지지 않는다.** — §4.2

파국 온도 이벤트가 한 번 기록되면 리셋해도 남습니다. 안정 전원 리셋 시퀀스(Figure 6)의 주석도 **`CATTRIP`은 `tINIT3` 종료 시점까지 리셋 이전 값을 유지**한다고 명시합니다.

검증 함의가 둘입니다. 첫째, **참조 모델이 리셋에서 `CATTRIP`을 지우면 안 됩니다** — 지우는 모델과 유지하는 모델을 구분하려면 **`CATTRIP`이 선 상태로 리셋하는 시나리오**가 있어야 하고, 그런 시나리오가 없으면 둘 다 통과합니다. 둘째, 컨트롤러가 리셋 후 `CATTRIP`을 읽고 "리셋했으니 깨끗하다"고 가정하는지가 검사 대상입니다.
:::

## 5. Controlled Power-off

§4.3은 전원을 내리는 순서를 규정합니다. 목적은 램프업과 같습니다 — **latch-up 회피**.

- 내리는 순서는 **가장 낮은 전압부터 가장 높은 전압으로** (램프업의 역순)
- `VDDQL` → `VDDQ` → `VDDC` → `VPP`, 각 단계는 **직전 전원이 300 mV 아래로 떨어진 뒤** 시작
- 램프 다운 중에도 부등식은 유지되어야 합니다 — `VPP > VDDC, VDDQ` / `VDDC > VDDQ + VSP` / `VDDQ > VDDQL − 200 mV` (Table 8)
- 모든 입력 레벨은 `VSS`와 `VDDQ`(또는 `VDDQL`) 사이에 있어야 합니다
- 전 전원이 300 mV 아래로 내려가면 전원 차단 완료이며, `tPOFF` 안에 끝나야 합니다

구간 정의: `Tx`는 **어떤 전원이든 규정 최소값 아래로 떨어지는 시점**, `Tz`는 **모든 전원이 300 mV 아래인 시점**입니다(Table 8 주석).

## 6. IEEE 1500 경유 초기화 — Lane Repair와 Channel Disable

§4.4는 초기화 시퀀스 안에서 테스트 포트를 쓰는 방법을 정의합니다. 이것이 이 장에서 설계상 가장 까다로운 부분입니다.

### 왜 초기화 중에 하는가

`R`/`C` 커맨드 버스는 초기화 과정에서 **RNOP/CNOP로 정확히 구동되어야** 합니다. 그런데 그 버스의 배선이 끊겨 있다면 초기화 자체가 실패합니다. 그래서 규격은 **정상 동작에 진입하기 전에** 결함 연결을 확인하고 고칠 경로를 열어둡니다. 채널 단위 비활성화도 이 시점에 가능하고, DWORD lane repair도 허용됩니다.

### 절차

> **모든 IEEE 1500 포트 명령은 `tINIT3` 이후 전체 초기화 시퀀스를 완료하지 않고도 사용 가능하다.** — §4.4

1. `RESET_n`과 `WRST_n`을 LOW로.
2. `tINIT1`(전원 인가 시) 또는 `tPW_RESET`(안정 전원 시) 경과 후 `RESET_n`을 HIGH로. `tINIT2`도 만족.
3. `tINIT3` 이후 `WRST_n`을 HIGH로 → **IEEE 1500 명령 사용 가능**. 이 시점에 채널 비활성화, 결함 레인 검출, soft lane repair 수행.
4. 이후 전원 인가 시퀀스의 4~6단계를 이어감.

### 순서 제약 두 개

**제약 1 — `EXTEST` 후에는 `RESET_n` 토글이 필수**

> `EXTEST` 동작으로 복구가 필요한 레인을 식별할 수 있다. soft lane repair가 필요하면, **`EXTEST` 명령 동작 후 요구되는 또 한 번의 `RESET_n` 토글 뒤에** `SOFT_LANE_REPAIR`와 `HARD_LANE_REPAIR` 동작을 적용할 수 있다. — §4.4 (요약)

즉 **검출 → 리셋 → 복구**의 3단이며, 중간의 리셋을 생략할 수 없습니다.

**제약 2 — 복구 후 `BYPASS`로 정상 모드 복귀**

`SOFT_LANE_REPAIR` 동작 후에는 모든 HBM4 신호를 정상 기능 모드로 되돌리기 위해 **`BYPASS` 명령을 적용**해야 합니다. 대안으로 `WRST_n`을 LOW로 내려도 됩니다.

### ⚠️ Soft가 Hard를 덮어쓴다

이 절에서 가장 중요한 조문입니다.

> `tINIT3` 기간 동안, `WRST_n`이 HIGH로 구동되기 전에 HBM4 장치는 **이전에 퓨즈된 데이터에 근거해 hard lane repair를 적용**하는 것을 포함해 여러 내부 구성 동작을 수행한다. **`tINIT3` 이후에 soft lane repair 명령을 실행하면 이전에 프로그램된 hard lane repair 데이터를 덮어쓴다.** HBM4 장치에서 **hard lane repair 데이터를 읽어 새 lane repair와 병합한 뒤** 새 soft lane repair 동작을 적용할 것을 권한다. — §4.4 (요약)

:::caution[초기화 소프트웨어가 반드시 지켜야 할 절차]
새로 발견한 결함 레인 하나를 고치려고 `SOFT_LANE_REPAIR`를 그냥 적용하면, **공장에서 퓨즈로 구운 기존 복구가 통째로 사라집니다.** 결과는 "고치려던 레인은 고쳐졌는데 멀쩡하던 레인이 죽는" 상태입니다.

올바른 절차는 **읽기 → 병합 → 쓰기**입니다.

```
1. 장치에서 hard lane repair 데이터를 읽는다
2. 새로 필요한 repair를 그 데이터에 병합한다
3. 병합된 전체를 SOFT_LANE_REPAIR로 적용한다
```

이것은 RTL이 아니라 **초기화 펌웨어의 책임**입니다. 검증 대상이 하드웨어가 아니므로 수단도 달라집니다 — IEEE 1500 **명령 스트림을 관측하는 프로토콜 checker**로 잡습니다(7.2 ③). 하드웨어만 검증하는 환경은 이 위반을 통과시키고, 그 대가는 **퓨즈된 복구가 사라진 실물 장치**로 돌아옵니다.
:::

덧붙여 규격은 **`EXTEST`가 soft lane repair의 선행 조건은 아니라고** 명시합니다. 이전에 파악해 둔 복구 정보를 매 초기화 때마다 적용하는 방식도 가능합니다.

## 🔬 검증 적용

### 7.1 무엇이 깨질 수 있는가

초기화는 검증이 **가장 얕게 되는 영역**입니다. 이유가 구조적입니다 — 모든 테스트가 초기화로 시작하므로 "매번 도는 코드"처럼 보이지만, 실제로는 **똑같은 경로 하나만 수만 번 도는 것**입니다. 초기화 결함은 대부분 실리콘 브링업에서 발견되고, 그때가 가장 비쌉니다.

| 조문 | 위반 형태 | 증상 | 잡히는 시점 |
|---|---|---|---|
| §4.1 전원 부등식 세 개 | 램프 중 `VDDC > VDDQ + VSP` 위반 | latch-up — **전기적 현상이라 디지털 시뮬에 안 나타난다** | **디지털 회귀로는 불가** |
| §4.1 `VSP` **vendor specific** | 상수로 박아 둠 | 벤더를 바꾸면 조용히 위반 | 없음 |
| Table 7 `tINIT6`은 **최대** 제약 | 최소로 오해해 그만큼 대기 | 기능은 맞지만 checker가 **false FAIL** | 즉시(잘못된 방향으로) |
| ⑤ `R[0]`은 **동기** 신호 (`tIS`) | 비동기로 취급 | 셋업 위반이 간헐 실패로 | 재현 안 되는 실패 |
| §4.2 `CATTRIP` **sticky** | 모델이 리셋 시 clear | 실제 장치와 갈림 → 과열 이력 추적 실패 | 리셋을 거치는 시나리오에서만 |
| §4.4 **soft가 hard를 덮어쓴다** | 병합 없이 `SOFT_LANE_REPAIR` | 고치려던 레인은 살고 **멀쩡하던 레인이 죽는다** | 퓨즈된 장치에서만 — **실리콘** |
| §4.4 `EXTEST` 후 `RESET_n` 토글 필수 | 생략 | repair가 적용되지 않음 | 없음(조용히 무시됨) |
| §4.4 복구 후 `BYPASS` 필요 | 생략 | 정상 기능 모드 복귀 실패 | 이후 모든 커맨드 실패 |
| §4 두 리셋의 **비대칭** | `RESET_n`만 내리고 `WRST_n`은 방치 | 테스트 포트에 이전 상태 잔존 | 없음 |
| §3.3 임의 상태에서 즉시 리셋 ([02장](../02_addressing_bank_groups/)) | Idle에서만 리셋 시험 | 미시험 상태 조합이 남음 | 없음 |

**첫 줄을 정직하게 다룰 필요가 있습니다.** 전원 램프 부등식은 순수 디지털 시뮬레이션에서 **관측 자체가 불가능**합니다. 전압은 논리값이 아니고, latch-up은 회로 현상입니다. 이 항목을 디지털 회귀의 V-Plan에 넣고 "검증 완료"로 표시하면 그것 자체가 결함입니다.

세 가지 선택지가 있고, 각각 덮는 범위가 다릅니다.

| 방법 | 덮는 것 | 못 덮는 것 |
|---|---|---|
| 전원 레일을 **실수(real) 신호로 모델링**한 behavioral TB | 부등식의 **논리적** 위반, 순서 뒤바뀜 | 실제 latch-up, 기울기 반전 |
| **Mixed-signal (AMS)** 시뮬레이션 | 램프 파형, 기울기 | 회귀에 넣기엔 너무 느림 |
| **보드/브링업 검증** | 실물 | 시뮬 단계에서 못 잡음 |

현실적인 조합은 **behavioral real 모델로 순서·부등식을 회귀에서 상시 검사**하고, AMS는 소수 시나리오에만 돌리는 것입니다. Mixed-level 운영은 [`hbm_dv` Ch05](../../hbm_dv/05_mixed_level/).

:::caution[초기화 경로는 하나가 아니다]
이 장에는 서로 다른 초기화 진입 경로가 **셋** 있습니다. 대부분의 환경은 첫 번째만 돌립니다.

| 경로 | 근거 | 특징 |
|---|---|---|
| **전원 인가 초기화** | §4.1 | `tINIT0` 램프부터 전 단계 수행 |
| **안정 전원 `RESET_n` 리셋** | §4.2 | 램프 없음. `tPW_RESET` 부터 시작 |
| **IEEE 1500 `HBM_RESET`** | §4.2 | **`RESET_n`은 HIGH를 유지**한 채 재초기화 |

세 번째가 특히 잘 빠집니다. `RESET_n`이 HIGH인 채로 장치가 재초기화되므로, `RESET_n` 하강을 리셋 트리거로 삼는 monitor·scoreboard는 **재초기화가 일어난 줄도 모릅니다.** 모델 상태는 그대로인데 장치만 초기화되어, 이후 전 트랜잭션이 어긋납니다.
:::

### 7.2 어떻게 잡는가 — 수단 선택

| 규칙 | 성격 | 수단 | 이유 |
|---|---|---|---|
| `tINIT0`~`tINIT7` 단계별 최소/최대 | **시간 관계** | **SVA** | 각 구간의 국소 판정 |
| 단계의 **순서** 자체 | **시퀀스** | **SVA (시퀀스 property)** | 단계 간 순서는 하나의 긴 property로 쓰는 편이 읽힌다 |
| `CATTRIP` sticky | **상태 보존** | **reference model** | 리셋을 가로질러 유지되는 값. SVA로는 표현이 어색 |
| lane repair 읽기→병합→쓰기 | **절차** | **프로토콜 checker** | 명령 **순서**에 대한 규칙. 펌웨어를 검증한다 |
| 전원 부등식 | **아날로그** | **real 모델 + SVA**, 또는 AMS | 7.1 참조 |

**① 단계별 타이밍과 순서 — 클럭이 없는 구간이 있다**

여기에 이 장 고유의 제약이 하나 있습니다. **초기화 구간의 상당 부분에서 CK는 토글하지 않습니다.**

```
① 전원 램프 ──② RESET_n LOW ──③ CK 정적 구동 ──④ RESET_n HIGH ──⑤ CK 토글 시작 ──⑥ MRS
│                                                                │
└────────── CK 정지 구간 (tINIT0·tINIT1·tINIT6·tINIT2·tINIT3) ───┘
                                                                 └── 여기서부터 SVA 가능
```

`@(posedge ck)` 로 쓴 assertion은 클럭이 없는 동안 **한 번도 평가되지 않습니다.** 실패하지 않는 것이 아니라 **아예 돌지 않습니다.** 그런데 리포트에는 "위반 0건"으로 나오므로, 검사가 있다고 착각하기 쉽습니다.

그리고 `tINIT3`(4 ms)·`tINIT1`(200 µs) 같은 **시간 단위** 제약은 클럭 사이클로 세면 주파수에 종속됩니다. 두 문제의 해법이 같습니다 — **시각을 직접 기록해 비교**합니다.

```systemverilog
module hbm4_init_chk (input logic ck, reset_n, wrst_n, ck_static, ck_toggling,
                      input logic [3:0] r, input logic [2:0] c,
                      input logic mrs_vld, rdqs_t, rdqs_c, aerr, derr);
  import uvm_pkg::*;
  `include "uvm_macros.svh"

  localparam time T_INIT1 = 200us, T_INIT2 = 10ns, T_INIT3 = 4ms,
                  T_INIT5 = 200ns, T_INIT6_MAX = 100ns, T_PW_RESET = 1us;
  localparam int  N_INIT4 = 10, N_INIT7 = 2;         // nCK 단위는 따로 둔다

  time t_reset_fall, t_reset_rise, t_ck_static;

  // ---- CK 정지 구간: 시각 기반 검사 ------------------------------------
  always @(negedge reset_n) t_reset_fall = $time;
  always @(posedge ck_static) t_ck_static = $time;

  always @(posedge reset_n) begin
    t_reset_rise = $time;
    // ② 안정 전원에서 RESET_n LOW 최소 유지 (§4.1 ②, §4.2)
    if (($time - t_reset_fall) < T_INIT1)
      `uvm_error("INIT", $sformatf("RESET_n LOW 유지 %0t < tINIT1 %0t",
                                   $time - t_reset_fall, T_INIT1))
    // ③ CK 정적 구동이 RESET_n 상승보다 tINIT2 먼저 (§4.1 ③)
    if (!ck_static || ($time - t_ck_static) < T_INIT2)
      `uvm_error("INIT", "RESET_n 상승 전 CK 정적 구동이 tINIT2 에 미달 (§4.1 ③)")
  end

  // tINIT6 만 최대 제약이다 — "이 안에 끝났는가"를 묻는다.
  // 최소 제약으로 잘못 쓰면 컨트롤러를 불필요하게 기다리게 만드는 checker 가 된다.
  always @(negedge reset_n) begin
    fork
      begin : watch_init6
        #(T_INIT6_MAX);
        if (!(rdqs_t == 1'b0 && rdqs_c == 1'b1 && !aerr && !derr))
          `uvm_error("INIT", "tINIT6(최대 100 ns) 안에 출력이 정적 레벨에 도달하지 않았다")
      end
      begin @(posedge reset_n) disable watch_init6; end   // 리셋이 먼저 풀리면 취소
    join_any
  end

  // ---- CK 토글 이후: 여기서부터 SVA 를 쓸 수 있다 ------------------------
  // ④ PDE/CNOP 를 tINIT7 유지한 뒤에야 CK 토글
  a_init7: assert property (@(posedge ck) disable iff (!reset_n)
      $rose(ck_toggling) |-> $past((r == 4'b1010) && (c == 3'b111), N_INIT7))
    else `uvm_error("INIT", "CK 토글 전 PDE/CNOP 유지가 tINIT7 에 미달 (§4.1 ④)")

  // ⑤ R[3:0] 이 HIGH 로 등록된 뒤에야 첫 MRS (그 사이 tINIT5)
  a_init5: assert property (@(posedge ck) disable iff (!reset_n)
      mrs_vld |-> ($past(r) == 4'b1111))
    else `uvm_error("INIT", "PDX 없이 MRS 가 발행되었다 (§4.1 ⑤)")

  // 클럭 없는 구간의 검사가 실제로 돌았는지 확인하는 장치
  c_init_full_path: cover property (@(posedge ck) $rose(ck_toggling));
endmodule
```

**`tINIT6`이 유일한 최대 제약**이라는 사실이 코드 형태를 바꿉니다. 나머지는 "이만큼 기다렸는가"라 이벤트 시점에 비교하면 되지만, `tINIT6`은 "이 안에 끝났는가"라 **타이머를 걸고 만료 시 확인**해야 합니다. 이 하나를 최소 제약으로 잘못 쓰면 컨트롤러를 불필요하게 100 ns 기다리게 만드는 checker가 됩니다.

**② `CATTRIP` sticky — 모델이 들어야 하는 상태**

```systemverilog
class hbm4_device_model extends uvm_object;
  `uvm_object_utils(hbm4_device_model)
  protected bit m_cattrip;             // sticky (§4.2)

  function void on_functional_reset();
    // 기능 리셋은 대부분의 상태를 지우지만 CATTRIP 은 지우지 않는다.
    reset_banks();
    reset_mode_registers();
    // m_cattrip 은 건드리지 않는다 — 이 한 줄이 없는 것이 이 함수의 계약이다
  endfunction

  function void on_thermal_event(); m_cattrip = 1'b1; endfunction
  function bit  cattrip();          return m_cattrip; endfunction
endclass
```

주석이 코드보다 긴 이유가 있습니다 — **하지 않는 일**이 계약이기 때문입니다. 나중에 누군가 `on_functional_reset()` 에 "빠진 것 같은" `m_cattrip = 0;` 을 추가하면 모델이 조용히 틀립니다.

**③ lane repair 절차 — 펌웨어를 검증한다**

§4.4의 "읽기 → 병합 → 쓰기"는 RTL 규칙이 아니라 **초기화 소프트웨어의 절차**입니다. 검증 대상이 하드웨어가 아니므로 수단도 다릅니다 — IEEE 1500 명령 스트림을 관측하는 **프로토콜 checker**입니다.

```systemverilog
// IEEE1500 명령 순서를 감시한다. 대상은 DUT 가 아니라 초기화 시퀀스 자신이다.
class lane_repair_protocol_chk extends uvm_subscriber #(ieee1500_item);
  `uvm_component_utils(lane_repair_protocol_chk)
  protected bit m_hard_data_read;
  protected bit m_extest_done;
  protected bit m_reset_after_extest;

  function void write(ieee1500_item t);
    case (t.instr)
      EXTEST            : begin m_extest_done = 1; m_reset_after_extest = 0; end
      HBM_RESET         : m_reset_after_extest = 1;
      HARD_LANE_REPAIR  : if (t.is_read) m_hard_data_read = 1;

      SOFT_LANE_REPAIR : begin
        // §4.4 — soft 는 hard 를 덮어쓴다. 병합 없이 쓰면 퓨즈된 복구가 사라진다.
        if (!m_hard_data_read)
          `uvm_error("LANE_REPAIR",
            "hard lane repair 데이터를 읽지 않고 SOFT_LANE_REPAIR 를 적용했다. "
          + "기존 퓨즈 복구가 덮어써진다 (§4.4)")
        // §4.4 — EXTEST 로 검출했다면 그 뒤 RESET_n 토글이 필수다
        if (m_extest_done && !m_reset_after_extest)
          `uvm_error("LANE_REPAIR",
            "EXTEST 후 요구되는 리셋 토글 없이 복구를 적용했다 (§4.4)")
      end
      default: ;
    endcase
  endfunction
endclass
```

이 checker가 잡는 결함은 **DUT 버그가 아니라 펌웨어 버그**입니다. 그래도 검증 환경이 잡아야 합니다 — 실리콘에서 발견하면 "멀쩡하던 레인이 죽은" 장치를 손에 들고 원인을 찾아야 하기 때문입니다.

### 7.3 무엇을 덮었다고 말할 수 있는가

초기화 coverage의 핵심은 **경로**와 **진입 상태**입니다. "초기화가 몇 번 돌았는가"는 의미가 없습니다.

```systemverilog
covergroup cg_hbm4_init with function sample(
    init_path_e path, dev_state_e from_state, repair_mode_e repair,
    bit wrst_used, bit cattrip_before);
  option.per_instance = 1;

  // --- 초기화 경로 세 갈래 (§4.1, §4.2) ---------------------------------
  cp_path : coverpoint path {
    bins power_up   = {INIT_POWER_UP};      // §4.1 전 단계
    bins reset_pin  = {INIT_RESET_N};       // §4.2 RESET_n
    bins hbm_reset  = {INIT_HBM_RESET};     // §4.2 IEEE1500 — RESET_n 은 HIGH 유지
  }

  // --- 어느 상태에서 리셋했는가 (§3.3 생략 목록의 "임의 상태 즉시 리셋") --
  cp_from : coverpoint from_state {
    bins idle       = {ST_IDLE};
    bins active     = {ST_BANK_ACTIVE};
    bins reading    = {ST_READING};
    bins writing    = {ST_WRITING};
    bins refreshing = {ST_REFRESHING};
    bins self_ref   = {ST_SELF_REFRESH};
    bins power_down = {ST_POWER_DOWN};
  }
  // 두 리셋 경로 × 모든 진입 상태 — 여기가 이 장의 진짜 커버리지 목표
  x_reset_from : cross cp_path, cp_from {
    ignore_bins pu = binsof(cp_path.power_up);   // 전원 인가는 진입 상태가 없다
  }

  // --- lane repair (§4.4) ----------------------------------------------
  cp_repair : coverpoint repair {
    bins none        = {REPAIR_NONE};
    bins hard_only   = {REPAIR_HARD_ONLY};      // 퓨즈된 것만, soft 미적용
    bins soft_merged = {REPAIR_SOFT_MERGED};    // 읽기→병합→쓰기 (정상 절차)
    // soft_overwrite 는 illegal — 7.2 ③ 의 checker 가 에러를 낸다
    illegal_bins soft_overwrite = {REPAIR_SOFT_OVERWRITE};
  }
  cp_wrst : coverpoint wrst_used {     // 초기화 중 테스트 포트를 썼는가 (§4.4)
    bins unused = {0}; bins used = {1};
  }

  // --- sticky 검증 (§4.2) ------------------------------------------------
  // 리셋 직전에 CATTRIP 이 서 있던 적이 있는가 — 없으면 sticky 는 미검증이다
  cp_cattrip : coverpoint cattrip_before { bins clear = {0}; bins set = {1}; }
  x_cattrip_reset : cross cp_cattrip, cp_path;
endgroup
```

`x_reset_from` 이 이 장의 목표입니다. [02장](../02_addressing_bank_groups/)에서 §3.3이 "임의 상태에서 즉시 reset으로 가는 천이는 그리지 않았다"고 밝힌 항목이 여기서 **구체적인 cross bin**이 됩니다. Idle에서만 리셋을 걸어 본 환경은 이 cross의 대부분이 빕니다.

`cp_cattrip.set` 도 마찬가지입니다. `CATTRIP`이 한 번도 서지 않은 상태로만 리셋했다면, sticky 여부는 **한 번도 검사되지 않은 것**입니다.

### 7.4 어떻게 자극하는가

**① 세 경로를 모두 돌린다** — 대부분의 환경은 전원 인가 경로만 돕니다. 나머지 둘은 **명시적으로 만들어야** 합니다.

```systemverilog
class seq_reinit extends uvm_sequence #(hbm4_cmd_item);
  `uvm_object_utils(seq_reinit)
  rand init_path_e path;
  constraint c_path { path inside {INIT_RESET_N, INIT_HBM_RESET}; }  // 재초기화 두 갈래

  virtual task body();
    if (path == INIT_RESET_N) begin
      drive_reset_n_low(T_PW_RESET);          // §4.2 경로 1
      drive_reset_n_high();
    end else begin
      // §4.2 경로 2 — RESET_n 은 HIGH 를 유지한다.
      // monitor 가 RESET_n 하강만 보고 있으면 이 재초기화를 놓친다.
      ieee1500_issue(HBM_RESET);
    end
    wait_tinit3();
    // 두 경로 모두 §4.1 의 ③~⑥ 단계를 이어서 수행한다
    run_init_stages_3_to_6();
  endtask
endclass
```

**② 임의 상태에서 리셋** — `x_reset_from` 을 채우는 시퀀스입니다. 정해진 시점이 아니라 **진행 중인 동작 위로** 리셋을 겁니다.

```systemverilog
// 무작위 트래픽을 돌리다가 임의 시점에 리셋한다 (§3.3 생략 목록)
fork
  begin traffic_seq.start(sqr); end
  begin
    #($urandom_range(100, 10000) * 1ns);
    reinit_seq.start(sqr);        // Reading/Writing/Refreshing 한복판일 수 있다
  end
join_any
disable fork;
```

리셋 시점을 랜덤화하면 `cp_from` 의 bin이 자연히 찹니다. 다만 **Self Refresh·Power-Down 진입 중**처럼 확률이 낮은 상태는 별도 directed 시퀀스로 유도해야 합니다.

**③ lane repair 병합 시나리오** — 정상 절차와 위반 절차를 **분리된 테스트**로 둡니다.

- 정상: `HARD_LANE_REPAIR` 읽기 → 병합 → `SOFT_LANE_REPAIR` → `BYPASS`
- 위반(negative): 읽기를 건너뛰고 `SOFT_LANE_REPAIR` → 7.2 ③의 checker가 에러를 내는지 확인

두 번째는 **checker 자신을 검증**하는 테스트입니다. `cp_repair.illegal_bins` 때문에 정상 회귀에는 들어가면 안 되므로, checker의 기대 에러를 등록하는 별도 테스트로 격리합니다.

**④ `CATTRIP`을 세워 놓고 리셋** — sticky 검증의 유일한 방법입니다. 온도 이벤트를 주입해 `CATTRIP`을 세운 뒤 세 경로 각각으로 리셋하고, 리셋 후에도 값이 남아 있는지 확인합니다. 이 시퀀스가 없으면 `CATTRIP`을 clear하는 모델과 유지하는 모델이 **똑같이 통과**합니다.

**⑤ 타이밍 경계값** — `tINIT` 파라미터를 최소값에 **딱 맞춰** 발행하는 모드와 여유 있게 발행하는 모드를 나눕니다. 항상 여유 있게만 돌면 경계 조건은 한 번도 시험되지 않고, 항상 최소로만 돌면 실제 시스템의 마진 있는 동작이 검증되지 않습니다.

## 8. 대표 문제 — dry-run

### 문제 1 — 전원 순서 위반 판정

> 시스템이 `VDDC`와 `VDDQ`를 동시에 램프업하도록 설계됐다. 규격 위반인가?

<details>
<summary>풀이</summary>

**시작 순서만으로는 위반이 아니다.** §4.1은 "`VDDC`는 `VDDQ`와 **동시 또는 먼저**(same time or earlier) 램프해야 한다"고 규정하므로 동시 시작은 허용된다.

**그러나 부등식은 별개다.** 첫 전원이 300 mV에 도달한 이후 계속 `VDDC > VDDQ + VSP`가 유지되어야 한다. 동시에 올리더라도 `VDDQ`의 기울기가 더 가팔라 중간에 이 조건이 깨지면 **위반**이다.

**검증 결론**: 이 판정은 **디지털 논리로 표현되지 않는다.** 전압 부등식이므로 레일을 `real` 신호로 모델링한 TB에서만 검사할 수 있고, `VSP`가 vendor specific이라 **환경 파라미터로 받아야** 한다. 상수로 박은 checker는 벤더가 바뀌는 순간 틀린 기준으로 통과시킨다 — 7.1절.
</details>

### 문제 2 — 초기화 최소 소요 시간

> 전원이 이미 안정된 상태에서 기능 리셋을 수행할 때, `RESET_n` LOW부터 첫 MRS 발행까지의 최소 시간을 지배하는 항목은?

<details>
<summary>풀이</summary>

경로를 따라가면:

```
tPW_RESET (≥ 1 µs)   RESET_n LOW 폭
 + tINIT3  (≥ 4 ms)   퓨즈 적용 + I/O 임피던스 보정   ← 지배적
 + tINIT4  (≥ 10 nCK) 안정 클럭
 + tINIT5  (≥ 200 ns) 첫 MRS 전 유휴
```

**`tINIT3`(4 ms)가 압도적으로 지배**한다. 나머지를 다 합쳐도 µs 단위이므로 세 자릿수 이상 차이가 난다.

**검증 함의**: `tINIT3`(4 ms)가 전체의 대부분을 차지하고, 그동안 **CK는 토글하지 않는다.** 곧 초기화 시뮬레이션은 클럭 기반 검사가 거의 돌지 않는 4 ms를 매 테스트마다 소모한다는 뜻이다. 두 가지가 따라온다 — ① 이 구간의 검사는 **시각 기반**이어야 하고(7.2 ①), ② 회귀 시간을 위해 `tINIT3`를 축약한 fast-init 모드를 두더라도 **실제 값으로 도는 테스트를 최소 하나는 남겨야** 한다.
</details>

### 문제 3 — Lane repair 절차

> 부팅 시 `EXTEST`로 DWORD 레인 하나의 결함을 찾았다. 곧바로 `SOFT_LANE_REPAIR`로 그 레인을 고치면 어떤 문제가 생기는가?

<details>
<summary>풀이</summary>

두 가지 문제가 있다.

1. **`RESET_n` 토글이 빠졌다.** `EXTEST` 동작 후에는 `RESET_n` 토글이 **요구**되며, 그 뒤에야 `SOFT_LANE_REPAIR`를 적용할 수 있다(§4.4).
2. **기존 hard lane repair가 지워진다.** `tINIT3` 동안 장치는 퓨즈된 hard repair를 적용해 둔 상태다. 그 위에 soft repair를 쓰면 **이전 데이터를 덮어쓴다.** 공장에서 복구해 둔 레인들이 원상복구되어 죽는다.

**올바른 절차**: `EXTEST` → `RESET_n` 토글 → `tINIT3` → hard repair 데이터 **읽기** → 새 repair와 **병합** → `SOFT_LANE_REPAIR` 적용 → `BYPASS`(또는 `WRST_n` LOW)로 정상 모드 복귀.

이 병합 책임은 **초기화 펌웨어**에 있다.
</details>

## 핵심 정리

- **기능 리셋은 IEEE 1500 포트 리셋을 동반**하지만, 테스트 포트 리셋은 정상 동작에 영향을 주지 않는다 — **비대칭**이다(§4).
- 초기화 진입 경로는 **셋**이다 — 전원 인가 · `RESET_n` · IEEE1500 `HBM_RESET`. 세 번째는 **`RESET_n`이 HIGH를 유지**하므로, `RESET_n` 하강만 보는 monitor는 재초기화를 놓친다.
- 전원 램프는 **순서 + 부등식** 두 층으로 강제된다. 이 항목은 **디지털 회귀로 검증 불가** — 레일을 `real`로 모델링하거나 AMS가 필요하다. V-Plan에 "검증 완료"로 표시하면 그 자체가 결함이다. `VSP`는 vendor specific이므로 **환경 파라미터**로 받는다.
- 장치는 **precharged power-down 상태로 리셋**되며, `tINIT3` 동안 **내부 퓨즈 적용과 I/O 임피던스 보정**을 수행한다.
- `R[3:0]` 중 **`R[0]`은 동기 신호** — `tIS`를 만족해야 한다. 자극 시퀀스가 이를 비동기로 구동하면 재현 안 되는 간헐 실패가 된다.
- 초기화의 **상당 구간에서 CK가 토글하지 않는다.** `@(posedge ck)` assertion은 그 구간에서 **아예 평가되지 않으면서 "위반 0건"으로 보고**된다. 시각 기반 checker로 써야 한다.
- 타이밍 단위가 **ms / µs / ns / nCK** 네 종류다. nCK 제약은 사이클로, 시간 제약은 시각으로 센다. **`tINIT6`만 최대 제약**이라 타이머를 걸고 만료 시 확인하는 반대 형태가 된다.
- **`CATTRIP`은 sticky** — 기능 리셋으로 지워지지 않는다(§4.2). **`CATTRIP`이 선 상태로 리셋하는 시나리오가 없으면**, 지우는 모델과 유지하는 모델이 똑같이 통과한다.
- Power-off는 램프업의 **역순**이며 부등식은 그대로 유지된다.
- 모든 IEEE 1500 명령은 **`tINIT3` 이후** 사용 가능하다 — 전체 초기화를 마치지 않아도 된다(§4.4).
- **`EXTEST` 후에는 `RESET_n` 토글이 필수**이고, 복구 후에는 **`BYPASS`로 정상 모드 복귀**해야 한다.
- ⚠️ **soft lane repair는 hard lane repair 데이터를 덮어쓴다.** 반드시 **읽기 → 병합 → 쓰기**. 검증 대상이 하드웨어가 아니라 **펌웨어 절차**이므로, IEEE1500 명령 스트림을 보는 **프로토콜 checker**로 잡는다.
- 이 장의 커버리지 목표는 **초기화 경로 3 × 리셋 진입 상태**의 cross다. Idle에서만 리셋을 걸어 본 환경은 그 대부분이 빈다.

## Further Reading

- **규격**: JESD270-4 §4 Initialization · §4.1 Power-up (Table 7, Figure 4–5) · §4.2 Stable Power (Figure 6) · §4.3 Controlled Power-off (Table 8) · §4.4 IEEE1500 경유 (Figure 7–8)
- **다음 장**: [04 — Mode Register](../04_mode_registers/) — 초기화 마지막 단계에서 발행하는 MRS의 내용
- **관련**: [10 — 테스트와 복구](../10_test_repair/) (lane repair 상세) · [11 — 트레이닝과 IEEE 1500](../11_training_ieee1500/) (테스트 포트 명령)
- **이해도 점검**: [퀴즈](../quiz/03_init_reset_power_quiz/)
