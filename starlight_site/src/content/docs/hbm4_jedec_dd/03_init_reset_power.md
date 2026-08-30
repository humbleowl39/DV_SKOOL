---
title: "03 — 초기화·리셋·전원 시퀀스"
description: JESD270-4 §4 · 전원 램프 순서, 초기화 단계별 타이밍, controlled power-off, IEEE 1500 경유 lane repair
---

:::tip[🎯 Learning Objectives]
이 모듈을 마치면:

- **Sequence** 전원 인가부터 첫 MRS까지의 초기화 단계를 순서와 타이밍 제약과 함께 재구성한다.
- **Explain** 전원 램프 순서가 왜 강제되는지(latch-up 회피)와 각 부등식이 무엇을 보장하는지 설명한다.
- **Design** 초기화 FSM을 단계별 타이머와 신호 구동 조건으로 설계한다.
- **Analyze** `RESET_n` 기능 리셋과 IEEE 1500 포트 리셋의 상호작용을 구분한다.
- **Evaluate** soft lane repair가 hard lane repair 데이터를 덮어쓰는 위험과 그 회피 절차를 판단한다.
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

| 조문 (§4) | 설계 함의 |
|---|---|
| **기능 리셋은 IEEE 1500 포트도 함께 리셋할 것을 요구한다** | `RESET_n` 어서트 시 `WRST_n`도 함께 내려야 한다 — 컨트롤러가 둘을 **묶어서** 구동해야 함 |
| **IEEE 1500 포트는 정상 동작에 영향 없이 언제든 리셋할 수 있다** | 역방향은 독립. 테스트 포트만 리셋해도 mission mode는 무사 |
| 포트는 `RESET_n` 해제 후 **최소 시간이 지나야** 리셋에서 빠져나올 수 있고, 그때 **제한된 명령 집합**만 사용 가능 | 초기화 중 테스트 포트 사용에는 시점·명령 제약이 있다 |
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

설계 관점에서는 **PMIC 시퀀서 설정이 벤더 종속**이라는 뜻입니다. HBM 벤더를 바꾸면 전원 시퀀스를 재검토해야 합니다.
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

초기화 FSM의 타이머를 단일 폭 카운터 하나로 만들면 4 ms를 세기 위해 과도하게 넓은 카운터가 필요하고, nCK 단위 제약은 별도 처리가 필요합니다. **시간 단위 타이머와 클럭 카운터를 분리**하는 편이 낫습니다.

그리고 `tINIT6`만 **최대(max) 제약**이라는 점에 주의하세요 — 나머지는 최소값입니다. 장치가 그 안에 출력을 안정시킨다는 보장이지 컨트롤러가 기다려야 할 시간이 아닙니다.
:::

## 4. 안정 전원 상태의 리셋 — 그리고 sticky한 것

§4.2는 전원을 유지한 채 기능 리셋을 하는 경우입니다. 두 가지 경로가 있습니다.

1. **`RESET_n`을 LOW로** 최소 `tPW_RESET` 동안 구동. 이때 `WRST_n`과 `CATTRIP`을 제외한 다른 입력은 미정의 상태여도 됩니다. `R[3:0]`=PDE, `C[2:0]`=CNOP를 `tINIT7` 동안 유지한 뒤 CK 토글.
2. **IEEE 1500 포트의 `HBM_RESET` 명령**을 사용. 이 경우 **`RESET_n`은 HIGH로 유지된 채** 재초기화가 수행됩니다.

이후는 전원 인가 시퀀스의 3~6단계를 따릅니다.

:::caution[CATTRIP은 sticky다]
> `CATTRIP` 출력은 **sticky이며 기능 리셋으로 지워지지 않는다.** — §4.2

파국 온도 이벤트가 한 번 기록되면 리셋해도 남습니다. 안정 전원 리셋 시퀀스(Figure 6)의 주석도 **`CATTRIP`은 `tINIT3` 종료 시점까지 리셋 이전 값을 유지**한다고 명시합니다.

설계 함의: 컨트롤러가 리셋 후 `CATTRIP`을 읽고 "리셋했으니 깨끗하다"고 가정하면 **과열 이력을 놓칩니다.** 반대로 이 특성 덕분에 리셋을 거쳐도 사건을 추적할 수 있습니다. 어느 쪽이든 **의도적으로 다뤄야 하는 상태**입니다.
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

이것은 RTL이 아니라 **초기화 펌웨어의 책임**입니다. 그래서 이 조문은 하드웨어·소프트웨어 경계에 걸친 요구사항이며, 펌웨어 설계자에게 전달되지 않으면 조용히 위반됩니다.
:::

덧붙여 규격은 **`EXTEST`가 soft lane repair의 선행 조건은 아니라고** 명시합니다. 이전에 파악해 둔 복구 정보를 매 초기화 때마다 적용하는 방식도 가능합니다.

## ⚙️ 설계 적용 (RTL / Front-end)

### 7.1 초기화 FSM의 골격

단계와 타이머를 그대로 상태로 옮깁니다. 타이머를 **시간 기반**과 **클럭 카운트 기반**으로 나누는 것이 핵심입니다.

```systemverilog
typedef enum logic [3:0] {
  INIT_PWR_RAMP,    // tINIT0 — 전원 램프 (외부 PMIC 완료 신호 대기)
  INIT_RESET_LOW,   // tINIT1 / tPW_RESET — RESET_n LOW 유지
  INIT_CK_STATIC,   // tINIT2 — CK 정적 구동
  INIT_RELEASE,     // RESET_n HIGH, R[3:0]=PDE / C[2:0]=CNOP
  INIT_HOLD_PDE,    // tINIT7 — CK 토글 전 유지 (nCK 단위)
  INIT_FUSE_CAL,    // tINIT3 — 퓨즈 적용 + I/O 임피던스 보정
  INIT_CK_STABLE,   // tINIT4 — 안정 클럭 (nCK 단위)
  INIT_PDX,         // R[3:0] HIGH — tIS 만족 필요
  INIT_PRE_MRS,     // tINIT5 — 첫 MRS 전 유휴
  INIT_MRS,         // MRS 발행
  INIT_DONE
} init_state_e;

// 시간 단위 제약(ms/µs/ns)과 클럭 단위 제약(nCK)은 카운터를 분리한다
logic [$clog2(T_INIT3_CYCLES)-1:0] us_timer_q;   // 최장 tINIT3 = 4 ms 를 담을 폭
logic [4:0]                        nck_timer_q;  // tINIT4=10, tINIT7=2 nCK
```

**주의**: `INIT_RELEASE` 이후 `R[3:0]`을 PDE로 유지하는 동안 `R[9:4]`와 `C[7:3]`은 미정의여도 되지만(§4.1 step 4), 컨트롤러가 그 구간에 **의도치 않은 값을 토글하면** 노이즈가 됩니다. 정적 값으로 고정하는 편이 안전합니다.

### 7.2 `R[0]`의 동기 특성

§4.1 step 5의 한 줄이 타이밍 제약을 만듭니다.

> `R[3:0]` 중 `R[0]`은 **동기 신호**이므로 클럭에 대한 셋업 시간 `tIS`를 만족해야 한다.

즉 `R[3:0]`을 HIGH로 올리는 동작은 **비동기 레벨 변경이 아니라 클럭 동기 전이**입니다. 초기화 FSM이 이 신호를 조합 논리로 즉시 바꾸면 `tIS` 위반이 납니다.

```systemverilog
// R[3:0] 구동은 클럭 동기 레지스터를 거친다 — R[0]의 tIS 만족 (§4.1 step 5)
always_ff @(posedge ck) begin
  if (state_q == INIT_CK_STABLE && nck_done)
    r_cmd_q <= 4'b1111;              // PDE -> PDX
  else if (state_q inside {INIT_RELEASE, INIT_HOLD_PDE, INIT_FUSE_CAL, INIT_CK_STABLE})
    r_cmd_q <= 4'b1010;              // PDE = H,L,H,L
end
```

### 7.3 두 리셋의 구동 관계

§4 서두의 비대칭을 논리로 옮기면 이렇습니다.

```systemverilog
// 기능 리셋은 테스트 포트 리셋을 동반한다 (§4)
// 역은 성립하지 않는다 — 테스트 포트만 리셋해도 mission mode는 무사하다
assign wrst_n_o = func_reset_req ? 1'b0
                : test_port_used ? wrst_n_ctrl
                : 1'b0;             // 테스트 포트 미사용 시 계속 LOW로 두어도 무방
assign reset_n_o = ~func_reset_req;
```

테스트 포트를 쓰지 않는 시스템이라면 `WRST_n`을 상시 LOW로 묶는 선택지가 규격상 허용됩니다(§4). 다만 그렇게 하면 §4.4의 lane repair 경로도 함께 포기하는 것이므로, **복구 기능이 필요 없다는 판단이 선행**되어야 합니다.

### 7.4 CATTRIP 처리

sticky 특성을 반영한 상태 관리가 필요합니다.

```systemverilog
// CATTRIP은 기능 리셋으로 지워지지 않는다 (§4.2)
// 리셋 후 값을 "새 이벤트"로 오해하지 않도록 리셋 이력과 함께 보관한다
always_ff @(posedge clk or negedge sys_rst_n) begin
  if (!sys_rst_n) begin
    cattrip_seen_q     <= 1'b0;
    cattrip_pre_reset_q<= 1'b0;
  end else begin
    if (func_reset_req) cattrip_pre_reset_q <= cattrip_seen_q;  // 리셋 이전 값 보존
    if (cattrip_valid && cattrip_i) cattrip_seen_q <= 1'b1;
  end
end
```

`cattrip_valid`는 `tINIT3` 이후에만 어서트되어야 합니다 — 그 이전 값은 유효하지 않기 때문입니다(§4.1 step 4).

### 7.5 초기화 중 IEEE 1500 사용 시퀀스

§4.4의 순서 제약을 상태로 옮기면 리셋이 **두 번** 들어갑니다.

```
RESET_n↓ WRST_n↓
   → tINIT1/tPW_RESET → RESET_n↑ → tINIT3 → WRST_n↑
   → [EXTEST] 결함 레인 식별
   → ⚠️ RESET_n 토글 (필수)
   → tINIT3 재경과 → WRST_n↑
   → hard repair 데이터 읽기 → 새 repair와 병합
   → SOFT_LANE_REPAIR 적용 (tSLREP 만족)
   → BYPASS (또는 WRST_n↓) → 정상 모드 복귀
   → 초기화 4~6단계 계속
```

이 흐름을 하드웨어 FSM에 전부 넣을 필요는 없습니다. 규격이 **"모든 IEEE 1500 명령은 `tINIT3` 이후 사용 가능"** 이라고 열어 두었으므로, 초기화 FSM은 `tINIT3` 도달을 알리고 **펌웨어가 테스트 포트를 구동**하는 분업이 자연스럽습니다. 다만 그 경계를 문서화하지 않으면 §4.4의 병합 절차가 누구의 책임인지 모호해집니다.

## 8. 대표 문제 — dry-run

### 문제 1 — 전원 순서 위반 판정

> 시스템이 `VDDC`와 `VDDQ`를 동시에 램프업하도록 설계됐다. 규격 위반인가?

<details>
<summary>풀이</summary>

**시작 순서만으로는 위반이 아니다.** §4.1은 "`VDDC`는 `VDDQ`와 **동시 또는 먼저**(same time or earlier) 램프해야 한다"고 규정하므로 동시 시작은 허용된다.

**그러나 부등식은 별개다.** 첫 전원이 300 mV에 도달한 이후 계속 `VDDC > VDDQ + VSP`가 유지되어야 한다. 동시에 올리더라도 `VDDQ`의 기울기가 더 가팔라 중간에 이 조건이 깨지면 **위반**이다.

**설계 결론**: 동시 램프를 하려면 두 전원의 **기울기 관계**까지 제어해야 하며, `VSP`가 vendor specific이므로 벤더 데이터시트 값으로 마진을 확인해야 한다. 권장 방식(순차 인가)이 안전한 이유가 여기 있다.
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

**설계 함의**: 초기화 시간을 줄이려는 최적화는 `tINIT3`에 손댈 수 없으므로(장치 내부 동작) 의미가 없다. 대신 **여러 채널·여러 스택의 초기화를 병렬로** 수행하는 것이 유효한 최적화다. `RESET_n`이 전역 신호이므로([01장](../01_landscape_organization/)) 스택 내 채널은 자연스럽게 병렬 진행된다.
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

## 🔍 검증 연결

- 초기화 시퀀스를 시나리오로 만들고 타이밍을 assertion으로 감시 → [`hbm_dv` Ch09 Assertion·Checker](../../hbm_dv/09_assertion_checker/)
- 리셋 이후 상태가 규격대로인지 확인하는 체크 → [`hbm_dv` Ch08 시나리오](../../hbm_dv/08_testcase_scenarios/)
- DFT 경로(IEEE1500)와 mission mode의 교차 → [`hbm_dv` Ch11 DFT·RAS](../../hbm_dv/11_dft_ras/)

## 핵심 정리

- **기능 리셋은 IEEE 1500 포트 리셋을 동반**하지만, 테스트 포트 리셋은 정상 동작에 영향을 주지 않는다 — **비대칭**이다(§4).
- 전원 램프는 **순서 + 부등식** 두 층으로 강제된다. `VSP`가 **vendor specific**이므로 전원 시퀀스는 벤더 종속이다.
- 장치는 **precharged power-down 상태로 리셋**되며, `tINIT3` 동안 **내부 퓨즈 적용과 I/O 임피던스 보정**을 수행한다.
- `R[3:0]` 중 **`R[0]`은 동기 신호** — `tIS`를 만족해야 한다. 초기화 FSM이 조합 논리로 구동하면 위반.
- 타이밍 단위가 **ms / µs / ns / nCK** 네 종류로 섞여 있다. **시간 타이머와 클럭 카운터를 분리**하라. `tINIT6`만 **최대** 제약이다.
- **`CATTRIP`은 sticky** — 기능 리셋으로 지워지지 않는다(§4.2). 리셋 후 읽고 "깨끗하다"고 가정하면 과열 이력을 놓친다.
- Power-off는 램프업의 **역순**이며 부등식은 그대로 유지된다.
- 모든 IEEE 1500 명령은 **`tINIT3` 이후** 사용 가능하다 — 전체 초기화를 마치지 않아도 된다(§4.4).
- **`EXTEST` 후에는 `RESET_n` 토글이 필수**이고, 복구 후에는 **`BYPASS`로 정상 모드 복귀**해야 한다.
- ⚠️ **soft lane repair는 hard lane repair 데이터를 덮어쓴다.** 반드시 **읽기 → 병합 → 쓰기**. 이는 **초기화 펌웨어의 책임**이다.

## Further Reading

- **규격**: JESD270-4 §4 Initialization · §4.1 Power-up (Table 7, Figure 4–5) · §4.2 Stable Power (Figure 6) · §4.3 Controlled Power-off (Table 8) · §4.4 IEEE1500 경유 (Figure 7–8)
- **다음 장**: [04 — Mode Register](../04_mode_registers/) — 초기화 마지막 단계에서 발행하는 MRS의 내용
- **관련**: [10 — 테스트와 복구](../10_test_repair/) (lane repair 상세) · [11 — 트레이닝과 IEEE 1500](../11_training_ieee1500/) (테스트 포트 명령)
- **이해도 점검**: [퀴즈](../quiz/03_init_reset_power_quiz/)
