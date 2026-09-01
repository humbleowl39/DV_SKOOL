---
title: "12 — 전기·타이밍·패키지와 Base Die 종합"
description: JESD270-4 §7–11 · DC 조건과 VDDQ 4종, AC 타이밍의 변동 계수, 신호 지도, 그리고 규격 밖 Base Die 설계
---

:::tip[🎯 Learning Objectives]
이 모듈을 마치면:

- **Interpret** `VDDQ`가 네 가지 전형값을 갖는 구조와 그것이 컨트롤러·PHY에 주는 제약을 해석한다.
- **Quantify** 전압·온도 변동 계수로 지연 이동량을 계산하고 재트레이닝 필요성을 정량적으로 설명한다.
- **Map** 규격의 신호 목록을 채널·DWORD·AWORD 단위로 정리해 검증 인터페이스로 옮긴다.
- **Distinguish** 규격이 정의하는 영역과 Base Die 구현이 책임지는 영역을 구분한다.
- **Synthesize** 12개 장의 검증 항목을 **수단별 V-Plan 골격**(assertion · reference model · coverage · 자극 제약 · 범위 밖)으로 종합한다.
- **Justify** 디지털 회귀로 검증할 수 없는 항목들을 특정하고, 왜 그것을 V-Plan에 명시해야 하는지 설명한다.
:::

:::note[Prerequisites]
- 앞선 11개 장 전체. 이 장은 **종합**입니다.
- 특히 [05 — 클럭킹](../05_clocking_dbi/) · [07 — Column 커맨드](../07_column_commands/) · [11 — 트레이닝](../11_training_ieee1500/)
:::

:::caution[인용 고지]
본 장의 §1–§3은 **JESD270-4 (2025-04, WIP draft)** §7–§11을 근거로 **요약·재구성**한 것입니다. §4(Base Die 종합)는 **규격이 정의하지 않는 영역**이므로 공개 자료를 근거로 하며 **[확인] / [추론] / [구현 의존]** 등급을 표기합니다. 정밀 값은 **JEDEC 원문 우선**.
:::

---

## 1. 전기적 조건

### `VDDQ`가 넷인 이유

§7.2가 이례적인 설명으로 시작합니다.

> HBM4에서는 HBM4 규격의 요구사항과 **HBM4 수명 기간 동안 예상되는 장치 설계**로 인해 **둘 이상의 `VDDQ` 범위를 정의할 필요**가 생겼다. Table 86에 나열된 전형값은 **발행 시점에 알려진 값**을 나타낸다. — §7.2 (요약)

즉 규격이 **미래에 값이 추가·삭제될 수 있음을 전제**하고 만들어졌습니다.

| 전원 | 전형값 | 성격 |
|---|---|---|
| **`VDDC`** (코어) | **1.05 V** 및/또는 **1.00 V** | 두 가지 |
| **`VDDQ`** (I/O) | **0.9 / 0.8 / 0.75 / 0.7 V** | **네 가지** |
| **`VDDQL`** (TX 드라이버 출력단) | **0.4 V** | 하나 |
| **`VPP`** (펌프) | **1.8 V** | 하나 |

허용 오차는 공통 규칙입니다 — **최소 = 0.97 × 전형값, 최대 = 1.07 × 전형값**. 그리고 **HBM4는 최소 하나의 전형 `VDDQ`를 지원해야** 하며, **실제 값은 벤더 데이터시트**를 봐야 합니다.

:::tip[§2 Features와 §7.2를 함께 읽기]
[01장](../01_landscape_organization/)에서 §2 Features를 인용하며 *"I/O 전압은 vendor specific, Tx driver 0.4 V, DRAM core 1.05 V"* 라고 했습니다. §7.2의 표와 대조하면 **둘은 서로 다른 층위**를 말합니다.

- **§2** — 헤드라인. "I/O는 벤더가 정한다, 드라이버 출력단은 0.4 V, 코어는 1.05 V"
- **§7.2** — 완전한 지원 집합. `VDDQ` 네 값, `VDDC` 두 값, 각각의 허용 오차

모순이 아니라 **요약과 상세**입니다. 규격을 읽을 때 Features 절만 보고 값을 확정하면 선택지를 놓칩니다.
:::

두 개의 부가 조건이 붙습니다.

- **전압 범위는 HBM4 DRAM의 마이크로필러에서 정의**됩니다 — 보드나 인터포저 어딘가가 아니라 **접점 기준**입니다.
- **DC 대역폭은 20 MHz로 제한**됩니다.

### 온도 — 호스트의 의무

§7.3이 호스트에게 **의무**를 부과합니다.

> 동작 온도는 HBM4 DRAM의 **모든 메모리 다이와 선택적 로직 다이의 접합 온도**를 가리킨다. **호스트는 IEEE1500 테스트 포트 명령 `TEMPERATURE`와 `CHANNEL_TEMPERATURE`를 통해 동작 온도를 감시해야 한다.** 호스트는 또한 **`CATTRIP` 출력을 감시해야** 하며, 이는 어느 다이든 접합 온도가 **영구 손상을 초래할 수 있는 파국 트립 지점**을 초과했음을 알린다. — §7.3 Note 1 (요약)

:::caution[온도 감시는 선택이 아니다]
"required"라는 단어가 두 번 쓰였습니다. 컨트롤러는 **온도 감시 루프를 반드시 가져야** 하고, 그 경로는 **IEEE 1500 테스트 포트**입니다.

[11장](../11_training_ieee1500/)에서 *"테스트 포트는 양산 전용이 아니라 부팅에 필수"* 라고 했는데, 여기서 한 걸음 더 나갑니다 — **정상 동작 내내 필수**입니다. `WRST_n`을 상시 LOW로 묶으면 온도 감시 의무를 이행할 수 없습니다.

그리고 [03장](../03_init_reset_power/)에서 본 **`CATTRIP`의 sticky 성질**이 여기서 의미를 갖습니다 — 파국 온도는 영구 손상과 직결되므로 리셋으로 지워지면 안 됩니다.
:::

**확장 온도(`TE`)는 선택**이며, 그 범위에서는 **추가 refresh 주기가 필요할 수 있습니다.** 구체적 범위는 **JESD402-1B 이상과 벤더 사양**을 참조합니다.

### ESD — 두 세계

§7.4의 값들이 HBM의 물리적 위치를 드러냅니다.

| 모델 | 값 |
|---|---|
| PHY Human Body Model | **해당 없음** (HBM DRAM에 적용되지 않음) |
| PHY Charged Device Model | **30 V** |
| DA Human Body Model | **1000 V** |
| DA Charged Device Model | **250 V** |

PHY 쪽 CDM이 **30 V**로 극히 낮습니다. 인터포저 위에서 호스트와 직결되는 **보호된 환경**이기 때문입니다. 반면 **DA 포트는 외부 프로빙 대상**이라 HBM 1000 V가 요구됩니다 — [11장](../11_training_ieee1500/)에서 본 *"프로빙용 비배치 영역"* 과 맞물립니다.

**검증 함의**: ESD 내성은 **디지털 회귀의 범위 밖**입니다. 디바이스 특성 시험 영역이며, V-Plan에는 "범위 밖"으로 명시해야 합니다 — 적지 않으면 아무도 안 하고, 안 했다는 사실조차 남지 않습니다(§4 종합표 ⑤).

## 2. AC 타이밍 — 변동 계수가 알려주는 것

### 분류

§10은 타이밍을 묶어 정의합니다. Row Access 계열만 보아도 [02장](../02_addressing_bank_groups/)·[06장](../06_row_commands/)에서 다룬 이름들이 모입니다 — `tRC`, `tRAS`, `tRCDRD`, `tRCDWR`, `tRRDL`/`tRRDS`, `tFAW`, `tRTP`, `tRP`, `tWR`, `tDAL`.

여기서 눈에 띄는 항목이 하나 있습니다.

> **`tRAS`의 최대값 = `9 × tREFI`** — §10 (Table 110)

`tRAS`에 **최대 제약**이 있다는 것은, 행을 **무한정 열어둘 수 없다**는 뜻입니다. 열린 행은 refresh를 받지 못하므로 최대 9 refresh 간격 안에 닫아야 합니다.

:::tip[페이지 정책에 상한이 있다]
"열린 페이지를 오래 유지해 히트율을 높인다"는 스케줄링 전략에 **하드 상한**이 걸립니다. 컨트롤러는 각 열린 행에 대해 **`tRAS` 최대 타이머**를 두고, 만료 전에 강제로 precharge해야 합니다.

이 제약을 구현하지 않으면 저트래픽 구간에서 행이 오래 열린 채 남아 **데이터 보존이 깨집니다.**
:::

### 스큐 예산

데이터 경로 스큐가 계층별로 정의됩니다.

| 항목 | 값 |
|---|---|
| RDQS ↔ DQ 스큐 (바이트 내) `tDQSQtra` | **20 ps** |
| DQ ↔ DQ 스큐 (**바이트 내**) `tDQ2DQtra_O` | **10 ps** |
| DQ ↔ DQ 스큐 (**바이트 간**) `tDQ2DQter_O` | **30 ps** |
| WDQS → read 데이터·RDQS 오프셋 `tWDQS2DQ_O` | **0.2 ~ 2.5 ns** |

**바이트 내(10 ps)와 바이트 간(30 ps)이 3배 차이**입니다. 바이트가 물리적 배치 단위이며, 같은 바이트 안은 배선을 정합시키기 쉽고 바이트를 넘으면 어렵다는 사실이 숫자로 드러납니다.

### ⚠️ 변동 계수 — 재트레이닝이 필요한 이유의 정량적 근거

이 장에서 가장 값진 두 줄입니다.

| 계수 | 값 |
|---|---|
| `tWDQS2DQ_O` **전압 변동** | **2.5 ps / mV** |
| `tWDQS2DQ_O` **온도 변동** | **1.0 ps / °C** |

계산해 보면 규모가 드러납니다.

```
온도 50 °C 변화  →  50 × 1.0  =  50 ps 이동
전압 30 mV 변화  →  30 × 2.5  =  75 ps 이동
                                ─────────
합계                            125 ps

대조: 바이트 내 DQ↔DQ 스큐 예산 tDQ2DQtra_O = 10 ps
      RDQS↔DQ 스큐 예산 tDQSQtra           = 20 ps
```

**정적 스큐 예산의 여러 배**를 동작 조건 변화만으로 이동합니다 **[추론 — Table 109/110 계수로부터 계산]**.

:::caution[이 숫자가 코스 전체를 설명한다]
왜 HBM4가 이렇게 많은 트레이닝·계측 기능을 갖는지가 여기서 답이 됩니다.

- [07장](../07_column_commands/) — **비정합 WDQS-DQ 경로**라 온도·전압에 따라 상대 위상이 흔들린다 → **주기적 트레이닝 필요**
- [11장](../11_training_ieee1500/) — **WOSC**가 그 이동을 측정해 **재트레이닝 시점을 판단**한다
- [11장](../11_training_ieee1500/) — **DCA/DCM**이 듀티 왜곡을 보정·관측한다
- [05장](../05_clocking_dbi/) — **WDQS-to-CK 정렬**이 `tDQSS` 범위를 확보한다

125 ps 규모의 이동을 10~20 ps 예산 안에서 견디려면 **정적 마진으로는 불가능**합니다. **동적 보정 체계**가 필수이고, 규격의 트레이닝 기능들은 그 체계의 구성 요소입니다.
:::

## 3. 신호 지도

§11.1 Table 111이 전체 신호를 정의합니다. 채널 인덱스 `[31:0]`이 모든 신호에 붙는 구조입니다.

### AWORD 계열

| 신호 | 방향 | 비고 |
|---|---|---|
| `CK[31:0]_t/_c` | 입력 | row·column 커맨드가 **양쪽 에지**에서 래치 |
| `R[31:0]_[9:0]` | 입력 | Activate·Precharge·Refresh의 커맨드·뱅크·행 주소 |
| `C[31:0]_[7:0]` | 입력 | Write·Read의 커맨드·뱅크·열 주소, **MRS의 MR 주소와 코드** |
| **`ARFU[31:0]`** | 입력 | **"Reserved for future use: AWORD의 미사용 마이크로범프"** |
| `APAR[31:0]` | 입력 | AWORD당 1개. **`C[7:0]`·`R[9:0]`·`ARFU`와 연관** |
| `AERR[31:0]` | 출력 | AWORD당 1개 |

:::tip[`ARFU`의 정체가 여기서 밝혀진다]
[06장](../06_row_commands/)에서 *"진리표에 없지만 구동해야 한다"*, [08장](../08_parity/)에서 *"패리티 대상"*, [10장](../10_test_repair/)에서 *"MISR 대상"* 으로 계속 등장한 `ARFU`의 정의가 §11.1에 있습니다 — **AWORD의 미사용 마이크로범프, 미래 사용을 위한 예약**입니다.

즉 **기능이 없는 신호인데도 구동·패리티·MISR에 모두 참여**합니다. 이유는 명확합니다 — 미래에 기능이 부여될 때 **전기적·프로토콜적 인프라가 이미 갖춰져 있도록** 하기 위해서입니다.

**설계 교훈**: "기능이 없다"와 "다룰 필요가 없다"는 다릅니다.
:::

### DWORD 계열

| 신호 | 대응 관계 |
|---|---|
| `DQ[31:0]_[63:0]` | **`DQ[31:0]` = PC0**, **`DQ[63:32]` = PC1** |
| `DBI[31:0]_[7:0]` | `DBI0` ↔ `DQ[7:0]`, … , `DBI7` ↔ `DQ[63:56]` (**바이트당 1개**) |
| `ECC[31:0]_[3:0]` | `ECC0`·`ECC1` ↔ `DQ[31:0]` / `ECC2`·`ECC3` ↔ `DQ[63:32]` |
| `SEV[31:0]_[3:0]` | `SEV0`·`SEV1` ↔ `DQ[31:0]` / `SEV2`·`SEV3` ↔ `DQ[63:32]` |
| `DPAR[31:0]_[1:0]` | **DWORD당 1개** |
| `DERR[31:0]_[1:0]` | **DWORD당 1개** |

[01장](../01_landscape_organization/)의 신호 수 표와 [09장](../09_ecc_ecs_sev/)의 codeword 구성이 이 대응 관계에서 나옵니다 — PC당 **32 DQ + 2 ECC**가 codeword를 이루고, **2 SEV**가 그 판정 결과를 나릅니다.

### Bump map

§11.2~11.4는 마이크로범프 위치·치수·bump map을 정의하며, §11.4.1은 **footprint 호환성**을 다룹니다. [11장](../11_training_ieee1500/)에서 본 DA 프로빙 영역(**컬럼 86~94**)도 이 좌표계 위에 있습니다.

설계 관점에서 이 절이 주는 것은 **floorplan 제약**입니다. [01장](../01_landscape_organization/)에서 계산한 약 3,896개 신호 범프의 물리적 배치가 여기서 확정되며, 그것이 Base Die의 PHY 배치와 라우팅을 지배합니다.

## 4. Base Die 종합 — 규격이 끝나는 곳에서

### 규격의 경계

여기서 중요한 구분을 해야 합니다.

> JESD270-4는 **HBM4 DRAM 장치**를 정의합니다. **메모리 컨트롤러와 PHY의 구현은 정의하지 않습니다.**

그리고 [01장](../01_landscape_organization/)에서 확인했듯 **Base Logic Die 자체가 규격의 필수 구성이 아닙니다**(§3). 규격은 호스트가 보는 **인터페이스와 동작**을 정의하고, 그것을 어떤 물리 구조로 만족시킬지는 벤더에게 맡깁니다.

따라서 이 절의 내용은 **규격 밖**이며, 공개 자료를 근거로 등급을 표기합니다.

### 컨트롤러–PHY 경계: DFI

| 사실 | 등급 | 출처 |
|---|---|---|
| HBM3/HBM4 PHY IP가 **DFI 5.0 / 5.1 호환 인터페이스**를 메모리 컨트롤러에 제공 | **[확인]** | Synopsys HBM3/HBM4 PHY IP 제품 문서 |
| 지원 클럭비 **1:1:2 · 1:2:4 · 1:4:8** | **[확인]** | 동일 |
| **PUB**(PHY Utility Block) — RTL 기반, **트레이닝 회로·설정 레지스터·BIST 제어** 포함 | **[확인]** | 동일 |
| HBM4는 이전 세대와 **컨트롤러·PHY IP·base die 모두 비호환** | **[확인]** | Siemens HBM3e/HBM4 IC design guide |
| JEDEC는 HBM4 인터페이스 정의가 **기존 HBM3 컨트롤러와 하위 호환**을 보장한다고 발표 | **[확인]** | JEDEC 보도자료 |

:::caution[상충하는 두 주장 — 층위를 구분해야 한다]
마지막 두 줄이 정면으로 어긋납니다. 폭이 1024 → 2048-bit로 두 배가 되는데 기존 컨트롤러가 그대로 붙을 수는 없습니다.

**해석 [추론]**: 두 주장이 서로 다른 층위를 말하는 것으로 보입니다.

- **JEDEC** — *프로토콜·커맨드 정의 수준*의 호환. 커맨드 체계와 동작 모델이 이어진다는 의미
- **Siemens** — *물리 구현 수준*의 비호환. 폭·채널 수·PHY·base die가 전부 달라 재사용 불가

이 코스가 다룬 내용은 후자를 뒷받침합니다 — 채널 수 16→32, 폭 1024→2048, `tCCDR` 신설([07장](../07_column_commands/)), refresh 5갈래([06장](../06_row_commands/)), MR 20개 구성, IEEE1500 명령 21개. **RTL을 그대로 재사용할 수 있는 규모가 아닙니다.**

**이것은 제 해석이며 [추론]입니다.** 확정적 판단은 각 벤더의 마이그레이션 문서를 확인해야 합니다.
:::

### 컨트롤러 구현의 공개 참조

| 사실 | 등급 | 출처 |
|---|---|---|
| HBM2 컨트롤러가 **8채널 × 2 pseudo-channel** 구조를 노출 | **[확인]** | AMD/Xilinx PG276 |
| **pseudo-channel당 AXI 포트 1개** — 각 AXI 인터페이스가 하나의 PC의 read/write를 담당 | **[확인]** | 동일 |
| **non-global address mode**에서 AXI 포트는 연관된 PC만 접근 가능 | **[확인]** | 동일 |

**[추론]**: HBM4에서 같은 원칙을 적용하면 **64개 pseudo-channel → 64개 포트**가 됩니다. 실제 구현에서는 포트 수를 줄이고 내부 스위치로 분배하는 선택이 가능하지만, 그 경우 **[01장](../01_landscape_organization/)에서 본 채널 독립성·비동기성**을 스위치가 흡수해야 합니다.

### 12개 장이 만드는 검증 항목 종합

이 코스에서 도출한 검증 항목을 **수단별로** 모으면 다음과 같습니다. 이 표가 곧 V-Plan의 골격이며, 각 행의 근거는 조문 번호입니다.

**① Assertion으로 잡는 것 — 시간·불변식 규칙**

| 항목 | 근거 | 장 |
|---|---|---|
| 공통 커맨드(PDE·PDX·SRE·SRX·MRS)는 **양쪽 PC 조건 AND** | §3.1.2 | [01](../01_landscape_organization/) |
| 무효 주소 조합(`RA[13:12]=11`·`SID=11`·4Hi `SID[0]`)이 **핀에 나가지 않음** | Table 4 Note 5·6·8 | [02](../02_addressing_bank_groups/) |
| 뱅크 그룹·SID 의존 `tRRD` — **PC별 판정** | Table 6 | [02](../02_addressing_bank_groups/) |
| 초기화 단계 순서·`tINIT` — **CK 없는 구간은 시각 기반** | §4.1, Table 7 | [03](../03_init_reset_power/) |
| `MRS` 전제조건 (전 뱅크 idle · `tRDMRS`) | §5 | [04](../04_mode_registers/) |
| 유휴 구간 스트로브 **정적** | §6.1 | [05](../05_clocking_dbi/) |
| ACT 후속 하강 슬롯 **3종만** | Table 33 Note 9 | [06](../06_row_commands/) |
| `tCCD` **3택** (그룹 × SID × 방향) | §10 Note 17 | [07](../07_column_commands/) |
| 패리티 요구 구간 — **관대 구간 포함** | §6.4.1 | [08](../08_parity/) |
| `SEV` 버스트 **전반부는 0** | Table 67 | [09](../09_ecc_ecs_sev/) |
| `tRAS` **최대**(`9 × tREFI`) 초과 전 강제 precharge | §10 | 이 장 |

**② Reference model / scoreboard로 잡는 것 — 상태·함수**

| 항목 | 근거 | 장 |
|---|---|---|
| Mode Register가 **두 PC 공유** (모델에 `pc` 인자 없음) | §3.1.2 | [01](../01_landscape_organization/) |
| 주소 매핑 **왕복 검사** `decode(encode(x)) == x` | Table 4 Note 2 | [02](../02_addressing_bank_groups/) |
| `CATTRIP` **sticky** — 기능 리셋에서 유지 | §4.2 | [03](../03_init_reset_power/) |
| RAL **map 2개** (쓰기 `MRS` / 읽기 IEEE1500), `has_reset(0)` | §5, §13.5.13 | [04](../04_mode_registers/) |
| DBIac **순차** 모델 — 경계값 4 히스테리시스, 네 리셋 조건 | §6.2.1, §6.2.1.1 | [05](../05_clocking_dbi/) |
| RAA 카운터 — 하한 0, `DRFMpb`는 감소 없음, `RFM=0`이면 무효과 | §6.3.2.5 | [06](../06_row_commands/) |
| PD/SR 진입 "완료" 술어 — auto-precharge write는 **MR의 `WR`** 기준 | §6.3.4.1 | [07](../07_column_commands/) |
| 패리티 대상 집합 — `WDBI`/`RDBI`/`MD` **동적 의존**, 단일 출처 함수 | Table 47 | [08](../08_parity/) |
| ECC 셀 오류 맵 — **read가 지우지 않음**, 실제 판정과 핀 값 **분리** | §6.9.2, Table 68 | [09](../09_ecc_ecs_sev/) |
| MISR 서명 — `poly`는 **구성에서 받음** | §6.8 | [10](../10_test_repair/) |
| 트레이닝 유효 플래그 — 앞 단계 재수행 시 **뒤 단계 무효화 전파** | §6.11.1, §6.12.1 | [11](../11_training_ieee1500/) |

**③ Coverage로 확인하는 것 — 도달 여부**

| 축 | 비면 미검증인 것 | 장 |
|---|---|---|
| 채널 클럭 관계 `asynchronous` | CDC 경로 전체 | [01](../01_landscape_organization/) |
| 선택된 타이밍 (`tCCDL/S/R` 등) — 값이 아니라 **분기** | `tCCDR` 경로 (4Hi만 돌면 영원히 0) | [02](../02_addressing_bank_groups/)·[07](../07_column_commands/) |
| 초기화 경로 3 × 리셋 진입 상태 | 임의 상태 리셋 (§3.3 생략 목록) | [03](../03_init_reset_power/) |
| MR × `traffic_ran` | "썼다"가 아니라 "그 설정으로 돌았다" | [04](../04_mode_registers/) |
| 전이 수 4 × 직전 DBI 상태 | DBIac 진리표의 두 행 | [05](../05_clocking_dbi/) |
| RAA `at_mmt` | ACTIVATE 금지 지점 (랜덤으로는 도달 불가) | [06](../06_row_commands/) |
| `RFMpb` × DRFM 샘플 유무 | 같은 커맨드의 두 해석 | [06](../06_row_commands/) |
| 패리티 대상 집합 4조합 × 오류 주입 | 나머지 3조합의 계산식 | [08](../08_parity/) |
| 실제 `CEs` × 핀 `NE` | `ERRTH` 필터의 존재 | [09](../09_ecc_ecs_sev/) |
| 복구 계층 (`none`이 아닌 것) | lane repair·Self Repair 전체 | [10](../10_test_repair/) |
| 재트레이닝 전파 | 무효화 로직 | [11](../11_training_ieee1500/) |

**④ 자극 측 제약으로 막는 것 — DUT 검증이 아닌 항목**

기대값이 존재하지 않거나, 위반이 관측되지 않거나, 환경 자신을 망가뜨리는 항목입니다.

| 항목 | 왜 자극 측인가 | 장 |
|---|---|---|
| `MRS` 전제조건 위반 | **unspecified operation** — 비교할 정답이 없다 | [04](../04_mode_registers/) |
| RFU 비트 = 0 | 규격이 요구하는 프로그래밍 규칙 | [04](../04_mode_registers/) |
| 미정의 `SID`/`RA`도 **유효 레벨 구동** | 시뮬의 `X`는 실물의 미정의 동작 | [06](../06_row_commands/) |
| PDX/SRX 구간의 **유효 패리티 RNOP/CNOP** | 검사가 없어 위반이 드러나지 않는다 | [06](../06_row_commands/) |
| Rx offset 중 **DQ float** | DUT 버그가 아니라 호스트 조건 | [11](../11_training_ieee1500/) |
| `MR8` OP0(DA Lockout) **랜덤화 제외** | 랜덤이 1을 만들면 관측 경로가 영구히 닫힌다 | [11](../11_training_ieee1500/) |
| lane repair **한 `UpdateWR`에 하나** | 전류 제약 — 시뮬에서 위반이 안 보인다 | [10](../10_test_repair/) |

:::caution[⑤ 디지털 회귀로 검증할 수 없는 항목]
이 코스가 반복해서 마주친 유형입니다. **V-Plan에 "검증 완료"로 표시하면 그 자체가 결함**인 항목들입니다.

| 항목 | 왜 불가능한가 | 대안 | 장 |
|---|---|---|---|
| 전원 램프 **부등식·기울기** | 전압은 논리값이 아니고 latch-up은 회로 현상 | 레일 `real` 모델 / AMS / 브링업 | [03](../03_init_reset_power/) |
| lane repair **전류 제약** | 순간 전류가 디지털 시뮬에 없다 | 자극 측 프로토콜 검사 | [10](../10_test_repair/) |
| `ERRTH` **이하의 실제 정정** | 규격이 관측 수단을 주지 않았다 | ECS 로그 / 임계 초과 주입 / ECC Test Mode — **셋 다 완전하지 않음** | [09](../09_ecc_ecs_sev/) |
| **ESD** 내성 (PHY CDM 30 V 등) | 전기적 스트레스 | 디바이스 특성 시험 | 이 장 |
| **변동 계수**에 따른 실제 지연 이동 | 온도·전압의 물리적 영향 | SPICE / 실측, 시뮬은 **파라미터 스윕**으로 대리 | 이 장 |

이 다섯 항목을 **명시적으로 "범위 밖"으로 적어 두는 것**이 V-Plan 작성에서 가장 중요한 일 중 하나입니다. 적지 않으면 아무도 안 하고, 아무도 안 했다는 사실조차 남지 않습니다.
:::

## 🔬 검증 적용

### 5.1 무엇이 깨질 수 있는가

이 장의 항목들은 대부분 **전기적 성질**이라, 앞 장들보다 "디지털 회귀로 검증 불가" 비중이 높습니다. 그래서 무엇을 대리 검증할 것인지가 더 중요합니다.

| 조문 | 위반 형태 | 증상 | 잡히는 시점 |
|---|---|---|---|
| §7.2 — `VDDQ`가 **네 가지 전형값** | 하나로 고정한 환경 | 다른 전압 프로파일의 타이밍이 미검증 | 없음 |
| §7.3 — 온도 감시가 **호스트 의무** | 감시 루프 없음 | 과열을 놓침. `WRST_n` LOW 프로파일은 이행 불가 | 없음 |
| §7.3 — `CATTRIP` 감시 의무 | 안 봄 | 파국 온도를 놓침 | 없음 |
| §7.4 — ESD (PHY CDM 30 V) | — | **디지털 시뮬로 검증 불가** | — |
| Table 109/110 — **변동 계수** | 단일 조건에서만 검증 | 온도·전압 변화 시 동작이 미검증 | **실리콘** |
| §10 — `tRAS` **최대**(`9 × tREFI`) | 최소만 검사 | 페이지를 너무 오래 열어 둠 | 없음 |
| §6.3 — `ARFU`는 **진리표에 없지만 구동·패리티 대상** | 자극이 빠뜨림 | 패리티 불일치 | 즉시(원인 오진) |
| §11 — bump map / 신호 배치 | — | 물리 검증 영역 | — |

:::caution[변동 계수 125 ps — 검증에서 이것을 어떻게 다루는가]
본문에서 계산한 값이 검증 전략을 정합니다.

```
온도 50 °C → 50 ps,  전압 30 mV → 75 ps,  합계 125 ps
대조: tDQ2DQtra_O = 10 ps,  tDQSQtra = 20 ps
```

정적 스큐 예산의 **여러 배**가 동작 조건만으로 이동합니다. 순수 디지털 시뮬레이션은 이 이동을 **표현하지 못합니다** — 지연이 고정이기 때문입니다.

대리 수단은 **파라미터 스윕**입니다. 지연 값을 환경 파라미터로 두고 회귀 시드마다 흔듭니다.

| 프로파일 | 무엇을 시험하는가 |
|---|---|
| **nominal** | 기본 동작 |
| **min delay** | 홀드 방향 마진 |
| **max delay** | 셋업 방향 마진 |
| **재트레이닝 후** | 보정이 실제로 마진을 회복시키는가 |

네 번째가 이 장 고유의 항목입니다. **지연을 크게 틀어 놓고 트레이닝을 돌린 뒤 정상 동작이 회복되는지**를 봐야, [11장](../11_training_ieee1500/)의 트레이닝 기능이 목적을 달성하는지 확인됩니다. 트레이닝을 "절차대로 수행했는가"만 검사하면 **절차는 맞는데 효과가 없는 경우**를 놓칩니다.
:::

:::caution[`tRAS`는 최소만 있는 것이 아니다]
대부분의 타이밍 파라미터는 최소값만 갖지만, `tRAS`에는 **최대값**이 있습니다 — `9 × tREFI`([03장](../03_init_reset_power/)의 `tINIT6`에 이어 두 번째 최대 제약입니다).

행을 그보다 오래 열어 두면 refresh 주기를 놓쳐 데이터가 손실됩니다. 그런데 **최소 검사만 두는 checker가 훨씬 흔합니다** — `tRAS` 하면 자동으로 최소를 떠올리기 때문입니다.

그리고 이 위반은 **랜덤 트래픽으로는 거의 안 나옵니다.** 열린 행을 `9 × tREFI` 동안 방치하려면 그 뱅크에 아무 접근도 하지 않아야 하는데, 랜덤 자극은 곧 다른 접근을 만듭니다. **의도적으로 방치하는 시퀀스**가 필요합니다.
:::

### 5.2 어떻게 잡는가 — 수단 선택

| 규칙 | 성격 | 수단 | 이유 |
|---|---|---|---|
| `tRAS` 최대 | **시간 상한** | **SVA (타이머형)** | "이 안에 닫혔는가" — 03장 `tINIT6`과 같은 형태 |
| 온도 감시 의무 | **절차** | **프로토콜 checker** | 호스트가 주기적으로 읽는지 본다 |
| 재트레이닝 효과 | **전후 비교** | **시나리오 + scoreboard** | 절차가 아니라 결과를 본다 |
| 변동 계수 | **파라미터** | **환경 파라미터 스윕** | 시뮬이 표현하지 못하는 것의 대리 |

**① `tRAS` 최대 — 타이머형 assertion**

```systemverilog
// §10 — tRAS 는 최소와 최대를 모두 갖는다. 최대는 9 × tREFI.
// 최소만 검사하는 checker 가 흔하므로 명시적으로 둔다.
property p_tras_max(int bank);
  @(posedge ck) disable iff (!rst_n)
    $rose(bank_active[bank]) |-> ##[1:T_RAS_MAX] $fell(bank_active[bank]);
endproperty

generate for (genvar b = 0; b < NUM_BANKS; b++) begin : g_tras
  a_tras_max: assert property (p_tras_max(b))
    else `uvm_error("tRAS_MAX", $sformatf(
         "뱅크 %0d 가 tRAS(max)=9×tREFI 를 넘겨 열려 있었다 (§10)", b))
  // 경계 근처까지 가 본 적이 있는가 — 없으면 이 검사는 여유 구간만 본 것이다
  c_tras_near_max: cover property (@(posedge ck)
      bank_active[b] && (cycles_open[b] > (T_RAS_MAX * 9 / 10)));
end endgenerate
```

**② 온도 감시 — 호스트가 의무를 이행하는가**

§7.3의 "required"는 **DUT가 아니라 호스트에 대한 요구**입니다. 따라서 검사 대상도 자극 쪽입니다.

```systemverilog
// §7.3 — 호스트는 TEMPERATURE·CHANNEL_TEMPERATURE 와 CATTRIP 을 감시해야 한다.
class thermal_monitor_chk extends uvm_component;
  `uvm_component_utils(thermal_monitor_chk)
  time m_last_temp_read;

  task run_phase(uvm_phase phase);
    fork
      forever begin
        #(TEMP_POLL_LIMIT);
        if (($time - m_last_temp_read) > TEMP_POLL_LIMIT)
          `uvm_error("THERMAL", $sformatf(
            "온도를 %0t 동안 읽지 않았다. §7.3 은 호스트의 감시를 요구한다",
            $time - m_last_temp_read))
      end
      forever begin
        @(posedge vif.cattrip);
        // CATTRIP 은 sticky 다 ([03장]) — 환경이 이를 인지하고 반응해야 한다
        `uvm_warning("THERMAL", "CATTRIP 어서트 — 파국 온도 초과")
      end
    join_none
  endtask
endclass
```

`WRST_n` 을 상시 LOW로 두는 프로파일에서는 이 감시가 **불가능**합니다([03장](../03_init_reset_power/)). 그 프로파일을 돌린다면 **온도 감시 항목을 범위 밖으로 명시**해야 합니다.

**③ 재트레이닝 효과 — 절차가 아니라 결과를 본다**

```systemverilog
// 지연을 크게 틀어 놓고 트레이닝을 돌린 뒤 정상 동작이 회복되는지 본다.
// "트레이닝을 절차대로 수행했다" 와 "트레이닝이 효과가 있었다" 는 다른 명제다.
task automatic check_retraining_effect();
  set_delay_profile(DELAY_SKEWED);       // 변동 계수 규모만큼 틀어 놓는다
  run_traffic(.expect_pass(0));          // 이 상태에서는 실패해도 정상
  run_full_training_sequence();          // [11장] 순서대로
  set_scoreboard_strict(1);
  run_traffic(.expect_pass(1));          // 회복되어야 한다
endtask
```

### 5.3 무엇을 덮었다고 말할 수 있는가

```systemverilog
covergroup cg_hbm4_electrical with function sample(
    vddq_e vddq, delay_profile_e dprof, bit retrained, int tras_open_ratio,
    bit temp_polled, bit arfu_driven);
  option.per_instance = 1;

  // --- VDDQ 네 전형값 (§7.2) ----------------------------------------------
  cp_vddq : coverpoint vddq { bins v[] = {VDDQ_A, VDDQ_B, VDDQ_C, VDDQ_D}; }

  // --- 지연 프로파일 — 변동 계수의 디지털 대리 ---------------------------
  cp_delay : coverpoint dprof {
    bins nominal = {DELAY_NOMINAL};
    bins min_d   = {DELAY_MIN};
    bins max_d   = {DELAY_MAX};
    bins skewed  = {DELAY_SKEWED};    // 트레이닝 없이는 실패해야 하는 구간
  }
  // 틀어 놓고 트레이닝해 회복시킨 적이 있는가 — 이 장의 핵심 축
  x_retrain_effect : cross cp_delay, cp_retrained {
    bins recovered = binsof(cp_delay.skewed) && binsof(cp_retrained.yes);
  }
  cp_retrained : coverpoint retrained { bins no = {0}; bins yes = {1}; }

  // --- tRAS 최대 (§10) ----------------------------------------------------
  // 열린 시간이 최대치에 얼마나 근접했는가 (백분율)
  cp_tras_ratio : coverpoint tras_open_ratio {
    bins low       = {[0:49]};
    bins mid       = {[50:89]};
    bins near_max  = {[90:99]};       // 경계에 붙어 봤는가
    illegal_bins over = {[100:$]};    // 넘으면 위반
  }

  // --- 온도 감시 의무 (§7.3) ----------------------------------------------
  cp_temp : coverpoint temp_polled { bins polled = {1}; }

  // --- ARFU (§6.3) — 진리표에 없어 빠뜨리기 쉽다 --------------------------
  cp_arfu : coverpoint arfu_driven { bins driven = {1}; }
endgroup
```

`x_retrain_effect.recovered` 가 이 장의 목표입니다. **틀어 놓고 → 실패 확인 → 트레이닝 → 회복 확인**의 전체 고리를 겪어야, [11장](../11_training_ieee1500/)의 트레이닝 기능이 실제로 마진을 되찾아 주는지 확인됩니다.

`cp_tras_ratio.near_max` 도 잘 빕니다. 랜덤 트래픽은 행을 오래 열어 두지 않기 때문입니다.

### 5.4 어떻게 자극하는가

**① 전압·지연 프로파일 순회** — `VDDQ` 네 값과 지연 프로파일 넷을 회귀 축으로 둡니다. 한 조건에서만 도는 회귀는 변동 계수가 만드는 문제를 전혀 시험하지 않습니다.

**② `tRAS` 최대에 접근한다** — 의도적으로 방치하는 시퀀스입니다.

```systemverilog
// 행을 열고 그 뱅크를 건드리지 않은 채 tRAS(max) 근처까지 기다린다.
// 랜덤 트래픽은 곧 다른 접근을 만들어 이 상태에 도달하지 못한다.
class seq_tras_max_approach extends uvm_sequence #(hbm4_cmd_item);
  `uvm_object_utils(seq_tras_max_approach)
  virtual task body();
    `uvm_do_with(req, { cmd == ACT; bank == TARGET_BANK; })
    // 다른 뱅크로만 트래픽을 보낸다 — TARGET_BANK 는 열린 채 방치된다
    repeat (N) `uvm_do_with(req, { bank != TARGET_BANK; })
    wait_until_ratio(0.95);              // tRAS(max) 의 95 % 지점
    `uvm_do_with(req, { cmd == PREPB; bank == TARGET_BANK; })   // 아슬하게 닫는다
  endtask
endclass
```

**③ 재트레이닝 효과 고리** — 5.2 ③의 시나리오를 회귀에 넣습니다. 중간의 **"실패해야 정상"** 구간이 있으므로 scoreboard를 일시적으로 느슨하게 두는 제어가 필요합니다.

**④ `ARFU`를 자극에 포함한다** — 진리표(Table 33)에 없어 빠뜨리기 쉽지만 **패리티 계산에 참여**합니다([06장](../06_row_commands/), [08장](../08_parity/)). 자극이 `ARFU`를 구동하지 않으면 패리티가 어긋나고, 원인은 패리티 로직처럼 보입니다.

**⑤ 온도 감시 루프를 환경에 상주시킨다** — 특정 테스트가 아니라 **모든 테스트에서** 도는 백그라운드 프로세스여야 합니다. §7.3이 요구하는 것은 일회성 확인이 아니라 지속적 감시이기 때문입니다.

## 6. 대표 문제 — dry-run

### 문제 1 — 변동량 계산

> 시스템이 25 °C에서 트레이닝했고, 부하 상승으로 접합 온도가 85 °C, `VDDQ`가 20 mV 하강했다. `tWDQS2DQ_O`는 얼마나 이동하는가? 재트레이닝이 필요한가?

<details>
<summary>풀이</summary>

```
온도 : (85 − 25) × 1.0 ps/°C  =  60 ps
전압 :  20 × 2.5 ps/mV        =  50 ps
                                ──────
                                110 ps  [추론 — §10 계수로부터 계산]
```

**대조 기준**: `tDQSQtra`(RDQS↔DQ 스큐) **20 ps**, `tDQ2DQtra_O`(바이트 내 DQ↔DQ) **10 ps**.

이동량이 스큐 예산의 **5~11배**다. 정적 마진으로 흡수할 수 없다.

**결론: 재트레이닝이 필요하다.** 그리고 [11장](../11_training_ieee1500/)의 순서 제약에 따라 Rx offset부터 다시 하면 `VREFD`와 WDQS-to-CK도 함께 해야 한다.

**부가 관찰**: 전압 계수가 온도 계수의 **2.5배**다. 20 mV 변동이 50 ps를 만드는 반면 같은 크기의 효과를 온도로 얻으려면 50 °C가 필요하다. **전원 안정도가 온도 관리보다 타이밍에 더 크게 기여한다.**
</details>

### 문제 2 — `tRAS` 최대

> 컨트롤러가 페이지 히트율을 높이려고 행을 최대한 오래 열어두는 정책을 쓴다. 저트래픽 구간에서 한 행이 10 × `tREFI` 동안 열려 있었다. 문제가 있는가?

<details>
<summary>풀이</summary>

**규격 위반이다.** §10 Table 110은 `tRAS`의 **최대값을 `9 × tREFI`** 로 규정한다.

**이유**: 열린 행은 refresh를 받지 못한다. 최대 제약이 없으면 저트래픽 구간에서 행이 무한정 열린 채 남아 **데이터 보존이 깨진다.**

**검증 결론**: `tRAS`에는 **최소와 최대가 모두** 있는데, 최소만 검사하는 checker가 훨씬 흔하다. 최대 검사는 "이 안에 닫혔는가" 형태이며([03장](../03_init_reset_power/)의 `tINIT6`와 같은 반대 형태), **랜덤 트래픽으로는 경계에 접근조차 못 하므로** 방치 시퀀스가 별도로 필요하다(5.4 ②).

**흔한 함정**: `tRAS`를 최소 제약으로만 구현하는 것. DDR 계열에서 `tRAS`는 보통 최소값으로만 다뤄지므로, 기존 컨트롤러 IP를 이식할 때 이 최대 제약을 놓치기 쉽다.
</details>

### 문제 3 — 규격의 경계

> "HBM4 컨트롤러 RTL을 JESD270-4만 보고 완성할 수 있는가?"

<details>
<summary>풀이</summary>

**불가능하다.** 규격이 정의하지 않는 것이 세 부류 있다.

**① 벤더 데이터시트가 필요한 값들**
- 아날로그 타이밍 `tWR`·`tRAS`·`tRTP` (MR 값 산출의 기준) — [04장](../04_mode_registers/)
- `RAAIMT`·`RAAMMT`·`RAADEC` (읽기는 `DEVICE_ID`로 가능하나 설계 시점 예산에는 사양 필요) — [06장](../06_row_commands/)
- `tCCDR(min)`, `VSP`, `ERRTH`, WOSC matching error, 실제 `VDDQ` 값 — [07](../07_column_commands/)·[03](../03_init_reset_power/)·[09](../09_ecc_ecs_sev/)·[11](../11_training_ieee1500/)장
- 지원되는 `PL` 범위, 각 latency의 실제 지원 구간 — [08장](../08_parity/)

**② 구현 의존으로 열린 것들**
- ECC H-matrix·symbol 크기·codeword 개수 — [09장](../09_ecc_ecs_sev/)
- `MR12`·`MR17`(벤더 전용), `MR16`~`MR19`(벤더 선택) — [04장](../04_mode_registers/)
- 내부 `WDQS/2` 전이 방향 — [05장](../05_clocking_dbi/)
- Self Repair 패턴과 복구 가능 개수 — [10장](../10_test_repair/)
- Base logic die의 존재 여부와 내용 — [01장](../01_landscape_organization/)

**③ 규격 범위 밖**
- 컨트롤러 내부 구조, 스케줄러 정책, 호스트 인터페이스(AXI·CHI 등)
- PHY 구현과 DFI 경계

**결론**: JESD270-4는 **장치와의 계약**을 정의한다. 컨트롤러를 만들려면 그 위에 **벤더 데이터시트**와 **PHY/DFI 사양**, 그리고 시스템 요구가 더해져야 한다. 규격은 필요조건이지 충분조건이 아니다.
</details>

## 7. 코스를 마치며

12개 장을 관통한 것을 세 문장으로 요약하면 이렇습니다.

**하나 — 규격의 제약은 대부분 물리에서 오고, 그래서 일부는 디지털 회귀로 검증할 수 없다.**
반 사이클 커맨드 해상도는 DDR 전송에서, 짝수 토글 규칙은 WDQS 분주기 위상에서, 뱅크 그룹 타이밍은 배열 자원 공유에서, 재트레이닝 필요는 125 ps 규모의 드리프트에서 나옵니다. 물리적 근거를 이해하면 값이 바뀌어도 판단이 서고, 동시에 **무엇이 시뮬레이션의 범위 밖인지**도 보입니다 — 전원 부등식, lane repair 전류 제약, ESD, `ERRTH` 이하의 정정. **그 목록을 V-Plan에 적는 것이 이 코스의 실질적 산출물입니다.**

**둘 — 규격이 열어둔 자리는 환경 파라미터가 된다.**
Base logic die의 존재 여부, ECC symbol 크기, `VDDQ` 값, `MR12`·`MR17`, Self Repair 패턴, `RAAIMT`·`ERRTH`·`tCCDR`·`VSP` — 규격은 이 자리들을 **의도적으로 비웠습니다.** 검증에서 이것들은 전부 **상수가 아니라 config**여야 하고, 상당수는 **`DEVICE_ID`에서 런타임에 읽어야** 합니다. 그리고 그 자리가 비어 있다는 것이 **표준 검증 IP가 존재할 수 없는 이유**이기도 합니다([`hbm_dv`](../../hbm_dv/03_custom_uvm_agent/)).

**셋 — 검출과 차단은 다르고, 그 차이가 기대값을 어렵게 만든다.**
CA parity도, data parity도, on-die ECC도 **장치는 차단하지 않습니다.** 잘못된 커맨드는 실행되고, 깨진 데이터는 기록되며, 정정된 값은 배열에 되쓰이지 않습니다. 그래서 `AERR`·`DERR`·`SEV`·ECS 로그를 관측하지 않으면 **모든 것이 조용히 통과**합니다.

그리고 관측하더라도 문제가 남습니다 — 에러를 주입한 뒤 scoreboard가 **오염된 상태를 따라가야** 하고, CA parity 오류는 어디가 오염됐는지조차 알 수 없습니다([08장](../08_parity/)). "에러 주입 테스트 통과"가 "오류 이후 복구가 검증됨"을 뜻하지 않는다는 것이 이 코스에서 가장 자주 반복된 경고입니다.

:::tip[다음으로]
- **검증 환경 구축** — [`hbm_dv`](../../hbm_dv/)가 여기서 도출한 항목들을 Agent·VIP·env 계층·회귀 운영으로 옮기는 방법을 다룹니다. 이 코스가 **무엇을 검증할 것인가**였다면, 저기는 **그것을 어떻게 짤 것인가**입니다.
- **구조 개괄 복습** — [`hbm`](../../hbm/)
- **빠른 참조** — [부록 A](../appendix_a_quick_reference/) · [용어집](../appendix_b_glossary/) · [검증 패턴](../appendix_c_check_patterns/)
:::

## 핵심 정리

- **`VDDQ`는 네 가지 전형값**(0.9/0.8/0.75/0.7 V), `VDDC`는 두 가지(1.05/1.00 V). 허용 오차는 **0.97× ~ 1.07×**. 규격은 값이 **추가·삭제될 수 있음을 전제**한다.
- **§2 Features와 §7.2는 요약과 상세**의 관계다. Features만 보고 값을 확정하면 선택지를 놓친다.
- 전압은 **마이크로필러 기준**으로 정의되고 **DC 대역폭 20 MHz**로 제한된다.
- **온도 감시는 호스트의 의무**다 — IEEE1500 `TEMPERATURE`·`CHANNEL_TEMPERATURE` + `CATTRIP`. 검사 대상이 DUT가 아니라 **자극 쪽**이며, 모든 테스트에서 도는 **백그라운드 감시**여야 한다. `WRST_n`을 상시 LOW로 두는 프로파일에서는 이행 불가이므로 **범위 밖으로 명시**한다.
- ESD가 **PHY CDM 30 V vs DA HBM 1000 V**로 극단적 차이를 보인다 — 보호된 인터포저 환경과 외부 프로빙 대상의 차이다. **디지털 회귀의 범위 밖** 항목이다.
- **`tRAS`에 최대 제약(`9 × tREFI`)이 있다.** 최소만 검사하는 checker가 훨씬 흔하고, **랜덤 트래픽으로는 경계에 접근조차 못 한다** — 행을 의도적으로 방치하는 시퀀스가 필요하다.
- 스큐 예산은 **바이트 내 10 ps, 바이트 간 30 ps** — 바이트가 물리 배치 단위임을 드러낸다.
- ⚠️ **변동 계수 2.5 ps/mV, 1.0 ps/°C.** 온도 60 °C + 전압 20 mV 변화만으로 **110 ps** 이동하며, 이는 스큐 예산의 **5~11배**다. 순수 디지털 시뮬은 이 이동을 표현하지 못하므로 **지연 프로파일 스윕**으로 대리하고, **틀어 놓고 → 실패 확인 → 트레이닝 → 회복 확인**의 고리로 트레이닝의 *효과*를 검증한다. 절차만 검사하면 **절차는 맞는데 효과가 없는 경우**를 놓친다.
- **`ARFU`는 "AWORD의 미사용 마이크로범프, 미래 예약"** 이다. 기능이 없어도 **구동·패리티·MISR에 모두 참여**하므로, 자극이 빠뜨리면 패리티가 어긋나고 원인은 패리티 로직처럼 보인다.
- 규격은 **장치와의 계약**만 정의한다. 컨트롤러·PHY·Base Die 구현은 **규격 밖**이며, 벤더 데이터시트와 PHY/DFI 사양이 추가로 필요하다 — 검증 계획의 첫 작업은 **규격이 답을 주는 경계선을 긋는 것**이다([01장](../01_landscape_organization/)).
- 12개 장의 검증 항목은 **수단별 다섯 묶음**으로 정리된다 — assertion · reference model · coverage · 자극 측 제약 · **디지털 회귀 범위 밖**. 마지막 묶음을 V-Plan에 명시하지 않으면 아무도 안 하고, **안 했다는 사실조차 남지 않는다.**
- HBM4 하위 호환성에 대해 **JEDEC(프로토콜 수준 호환)과 벤더 자료(물리 구현 비호환)가 상충**한다. 층위를 구분해 읽어야 한다 **[추론]**.

## Further Reading

- **규격**: JESD270-4 §7 Operating Conditions (Table 86–88) · §8 Electrical Characteristics · §9 IDD · §10 AC Timings (Table 109–110) · §11 Package (Table 111, Bump Map) · §12 Assembly
- **외부 표준**: JESD402-1B 이상 (동작 접합 온도 범위) · JEP157A (CDM) · JS-001/JS-002 (ESD 측정)
- **부록**: [A 빠른 참조](../appendix_a_quick_reference/) · [B 용어집](../appendix_b_glossary/) · [C 검증 패턴](../appendix_c_check_patterns/)
- **후속 코스**: [HBM 검증 실무](../../hbm_dv/)
- **이해도 점검**: [퀴즈](../quiz/12_electrical_timing_package_quiz/)
