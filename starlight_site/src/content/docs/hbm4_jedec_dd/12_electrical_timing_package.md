---
title: "12 — 전기·타이밍·패키지와 Base Die 종합"
description: JESD270-4 §7–11 · DC 조건과 VDDQ 4종, AC 타이밍의 변동 계수, 신호 지도, 그리고 규격 밖 Base Die 설계
---

:::tip[🎯 Learning Objectives]
이 모듈을 마치면:

- **Interpret** `VDDQ`가 네 가지 전형값을 갖는 구조와 그것이 컨트롤러·PHY에 주는 제약을 해석한다.
- **Quantify** 전압·온도 변동 계수로 지연 이동량을 계산하고 재트레이닝 필요성을 정량적으로 설명한다.
- **Map** 규격의 신호 목록을 채널·DWORD·AWORD 단위로 정리해 설계 인터페이스로 옮긴다.
- **Distinguish** 규격이 정의하는 영역과 Base Die 구현이 책임지는 영역을 구분한다.
- **Synthesize** 12개 장의 설계 제약을 하나의 Base Die 요구사항 목록으로 종합한다.
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

**설계 함의**: PHY I/O에 통상적인 ESD 보호 구조를 넣으면 **기생 용량이 고속 동작을 해칩니다.** 규격이 낮은 값을 허용한 것은 그 트레이드오프를 인정한 것이고, 대신 **조립·취급 과정의 관리**가 전제됩니다.

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

### 12개 장이 만드는 Base Die 요구사항 목록

이 코스에서 도출한 설계 제약을 하나로 모으면 다음과 같습니다.

**구조**

- 채널 컨트롤러 **× 32**, 각 채널 안에 PC별 뱅크 상태·타이밍 카운터 **× 2**, MR 파일·저전력 FSM **× 1** ([01장](../01_landscape_organization/), [04장](../04_mode_registers/))
- 뱅크 상태 머신은 **뱅크마다 한 벌** — 최대 64개/채널 ([02장](../02_addressing_bank_groups/))
- 최대 **32개 독립 클럭 도메인**과 그 경계의 CDC. 채널 내 두 PC는 CK 공유 ([01장](../01_landscape_organization/))
- IEEE 1500은 별도 `WRCK` 도메인으로 전 채널 횡단 ([11장](../11_training_ieee1500/))

**커맨드 경로**

- 커맨드 디코더는 **반 사이클 해상도** — ACT 1.5 사이클을 표현해야 함 ([01장](../01_landscape_organization/), [06장](../06_row_commands/))
- 하강 에지 슬롯 제약 검사 (ACT 후 RNOP / 다른 뱅크 PREpb / 다른 PC PREab만) ([06장](../06_row_commands/))
- 라운딩은 **`0.5 × RU(2·t/tCK)`**, 반 사이클 정수 단위. `tRP` 하강 에지 예외 ([06장](../06_row_commands/))
- `tCCD` **3택** — 그룹·SID 양쪽 의존 ([07장](../07_column_commands/))
- `tRAS` **최대 타이머**(`9 × tREFI`)로 강제 precharge (이 장)
- 공통 커맨드(PDE·PDX·SRE·SRX·MRS)는 **양쪽 PC 조건 AND** ([01장](../01_landscape_organization/))

**데이터 경로**

- WDQS 토글 **패리티 1비트** 불변식. 분주기 재초기화 3시점에 함께 리셋 ([05장](../05_clocking_dbi/))
- DBIac 판정 재현 — 전이 수 4에서 **직전 상태 참조**. ECC·SEV·`DPAR` 제외 ([05장](../05_clocking_dbi/))
- 패리티 대상 집합이 `WDBI`/`RDBI`/`MD`에 **동적으로 의존** ([08장](../08_parity/))
- write **재시도 버퍼** 깊이 = `WL + PL + tPARDQ` ([08장](../08_parity/))
- `SEV` 디코더는 **버스트 후반부만** 샘플링 ([09장](../09_ecc_ecs_sev/))

**초기화·관리**

- `DEVICE_ID` **선행 읽기** → 밀도·RAA 문턱값·ARFM/RXoffC 지원 여부 ([11장](../11_training_ieee1500/))
- MR **20개 전부** 기록 (기본값 없음). MR **섀도 카피 필수** ([04장](../04_mode_registers/))
- lane repair는 **CK 토글 이전**, **한 레인씩 `UpdateWR`**, hard 데이터 **병합** ([03장](../03_init_reset_power/), [10장](../10_test_repair/))
- 트레이닝 순서 **RXoffC → DCA/DCM → VREFD → WDQS-to-CK**, 재수행 시 후속 무효화 ([11장](../11_training_ieee1500/))
- ECS 설정은 초기화 중, **`ECSCEM` 선행**, 이후 동결. **배열 기록이 ECS보다 먼저** ([09장](../09_ecc_ecs_sev/))
- RAA 카운터 **뱅크별**, 하한 0, `RAAMMT`에서 ACT 차단 ([06장](../06_row_commands/))

**관측**

- `AERR` **상시 감시** — 패리티는 차단하지 않으므로 뱅크 상태 오염 추적 필요 ([08장](../08_parity/))
- `DERR` **모드 디코딩** — 패리티 / 위상 / 듀티 3택 ([05장](../05_clocking_dbi/), [08장](../08_parity/), [11장](../11_training_ieee1500/))
- 온도 감시 **의무** — IEEE1500 `TEMPERATURE`·`CHANNEL_TEMPERATURE` + `CATTRIP` (이 장)
- ECS 로그 **주기적 읽기** — 일반 read 정정은 로그에 안 남음 ([09장](../09_ecc_ecs_sev/))

## ⚙️ 설계 적용 (RTL / Front-end)

### 5.1 `tRAS` 최대 타이머

```systemverilog
// tRAS에는 최대 제약이 있다: 9 × tREFI (§10 Table 110)
// 열린 행은 refresh를 받지 못하므로 강제로 닫아야 한다.
localparam int T_RAS_MAX = 9 * T_REFI_CYCLES;

logic [$clog2(T_RAS_MAX)-1:0] row_open_cnt_q [NUM_BANKS];

always_ff @(posedge ck) begin
  for (int b = 0; b < NUM_BANKS; b++) begin
    if (act_valid && act_bank == b)        row_open_cnt_q[b] <= '0;
    else if (bank_state_q[b] == BANK_ACTIVE) row_open_cnt_q[b] <= row_open_cnt_q[b] + 1;
  end
end

// 만료 전에 강제 precharge — 페이지 정책보다 우선한다
wire [NUM_BANKS-1:0] force_precharge =
  '{default: 0} | (row_open_cnt_q >= (T_RAS_MAX - PRECHARGE_MARGIN));
```

### 5.2 재트레이닝 트리거 — 변동 계수 기반

```systemverilog
// tWDQS2DQ_O 변동: 2.5 ps/mV, 1.0 ps/°C  (§10)
// 트레이닝 시점 대비 누적 이동량이 스큐 예산의 일정 비율을 넘으면 재트레이닝.
localparam int PS_PER_MV   = 25;   // 2.5 ps/mV × 10 (고정소수점)
localparam int PS_PER_DEGC = 10;   // 1.0 ps/°C × 10
localparam int SKEW_BUDGET_PS10 = 200;   // tDQSQtra 20 ps × 10

wire [15:0] drift_ps10 = (delta_mv * PS_PER_MV) + (delta_degc * PS_PER_DEGC);

// WOSC 계수 변화와 함께 판단한다 (11장)
wire retrain_needed = (drift_ps10 > (SKEW_BUDGET_PS10 / 2))
                    | wosc_delta_exceeds_threshold;
```

**온도만으로 판단하지 않는 이유**: 전압 변동 계수가 **2.5배 크므로**, 전원 노이즈나 DVFS 전환이 온도보다 빠르게 마진을 갉아먹을 수 있습니다.

### 5.3 온도 감시 루프

```systemverilog
// 호스트 의무 (§7.3 Note 1) — IEEE1500 경로로 주기적 폴링
typedef enum logic [1:0] { TMON_IDLE, TMON_READ_DEV, TMON_READ_CH, TMON_EVAL } tmon_e;

// CATTRIP은 별도 핀으로 상시 감시 — sticky이므로 리셋 후에도 남는다 (03장)
always_ff @(posedge clk) begin
  if (cattrip_valid && cattrip_i) begin
    thermal_emergency_q <= 1'b1;        // 즉시 트래픽 차단 + 상위 보고
    throttle_level_q    <= THROTTLE_MAX;
  end
end

// 확장 온도 범위에서는 refresh 주기를 늘려야 할 수 있다 (§7.3 Note 2)
wire [15:0] trefi_eff = extended_temp_range ? (T_REFI >> 1) : T_REFI;
```

### 5.4 `ARFU` 처리

```systemverilog
// ARFU는 "AWORD의 미사용 마이크로범프, 미래 사용 예약" (§11.1)
// 기능은 없지만: 유효 레벨 구동(06장) + 패리티 참여(08장) + MISR 참여(10장)
assign arfu_o = 1'b0;                              // 정적 유효 레벨
// 패리티 계산에 반드시 포함
assign apar_o = ^{r_o, c_o, arfu_o};
```

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

**설계 결론**: 페이지 정책은 **`tRAS` 최대 타이머에 종속**되어야 한다. 각 열린 행에 카운터를 두고, 만료 전에 **정책과 무관하게 강제 precharge**해야 한다.

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

**하나 — 규격의 제약은 대부분 물리에서 온다.**
반 사이클 커맨드 해상도는 DDR 전송에서, 짝수 토글 규칙은 WDQS 분주기 위상에서, 뱅크 그룹 타이밍은 내부 배열 자원 공유에서, 재트레이닝 필요는 125 ps 규모의 전압·온도 드리프트에서 나옵니다. **조문을 외우는 대신 그 물리적 근거를 이해하면 값이 바뀌어도 판단이 섭니다.**

**둘 — 규격이 열어둔 자리가 제품을 만든다.**
Base logic die의 존재 여부, ECC symbol 크기, `VDDQ` 값, `MR12`·`MR17`, Self Repair 패턴 — 규격은 이 자리들을 **의도적으로 비웠습니다.** 그 자리가 벤더 차별화의 공간이고, 동시에 **표준 검증 IP가 존재할 수 없는 이유**입니다([`hbm_dv`](../../hbm_dv/03_custom_uvm_agent/)).

**셋 — 검출과 차단은 다른 이야기다.**
CA parity도, data parity도, on-die ECC도 **장치는 차단하지 않습니다.** 잘못된 커맨드는 실행되고, 깨진 데이터는 기록되며, 정정된 값은 배열에 되쓰이지 않습니다. 장치는 **보고**하고 복구는 **호스트**가 합니다. 그래서 `AERR`·`DERR`·`SEV`·ECS 로그를 관측하지 않으면 **모든 것이 조용히 통과**합니다.

:::tip[다음으로]
- **검증 실무** — [`hbm_dv`](../../hbm_dv/)가 이 조문들을 V-Plan·Agent·Assertion·Coverage로 옮기는 방법을 다룹니다.
- **구조 개괄 복습** — [`hbm`](../../hbm/)
- **빠른 참조** — [부록 A](../appendix_a_quick_reference/) · [용어집](../appendix_b_glossary/) · [검증 패턴](../appendix_c_check_patterns/)
:::

## 핵심 정리

- **`VDDQ`는 네 가지 전형값**(0.9/0.8/0.75/0.7 V), `VDDC`는 두 가지(1.05/1.00 V). 허용 오차는 **0.97× ~ 1.07×**. 규격은 값이 **추가·삭제될 수 있음을 전제**한다.
- **§2 Features와 §7.2는 요약과 상세**의 관계다. Features만 보고 값을 확정하면 선택지를 놓친다.
- 전압은 **마이크로필러 기준**으로 정의되고 **DC 대역폭 20 MHz**로 제한된다.
- **온도 감시는 호스트의 의무**다 — IEEE1500 `TEMPERATURE`·`CHANNEL_TEMPERATURE` + `CATTRIP`. **테스트 포트가 정상 동작 내내 필요**하다는 뜻이다.
- ESD가 **PHY CDM 30 V vs DA HBM 1000 V**로 극단적 차이를 보인다 — 보호된 인터포저 환경과 외부 프로빙 대상의 차이다.
- **`tRAS`에 최대 제약(`9 × tREFI`)이 있다.** 페이지 정책보다 우선하는 **강제 precharge 타이머**가 필요하다.
- 스큐 예산은 **바이트 내 10 ps, 바이트 간 30 ps** — 바이트가 물리 배치 단위임을 드러낸다.
- ⚠️ **변동 계수 2.5 ps/mV, 1.0 ps/°C.** 온도 60 °C + 전압 20 mV 변화만으로 **110 ps** 이동하며, 이는 스큐 예산의 **5~11배**다. **동적 보정 체계 없이는 불가능**하다 — 코스 전체의 트레이닝 기능이 여기서 설명된다.
- **`ARFU`는 "AWORD의 미사용 마이크로범프, 미래 예약"** 이다. 기능이 없어도 **구동·패리티·MISR에 모두 참여**한다.
- 규격은 **장치와의 계약**만 정의한다. 컨트롤러·PHY·Base Die 구현은 **규격 밖**이며, 벤더 데이터시트와 PHY/DFI 사양이 추가로 필요하다.
- HBM4 하위 호환성에 대해 **JEDEC(프로토콜 수준 호환)과 벤더 자료(물리 구현 비호환)가 상충**한다. 층위를 구분해 읽어야 한다 **[추론]**.

## Further Reading

- **규격**: JESD270-4 §7 Operating Conditions (Table 86–88) · §8 Electrical Characteristics · §9 IDD · §10 AC Timings (Table 109–110) · §11 Package (Table 111, Bump Map) · §12 Assembly
- **외부 표준**: JESD402-1B 이상 (동작 접합 온도 범위) · JEP157A (CDM) · JS-001/JS-002 (ESD 측정)
- **부록**: [A 빠른 참조](../appendix_a_quick_reference/) · [B 용어집](../appendix_b_glossary/) · [C 검증 패턴](../appendix_c_check_patterns/)
- **후속 코스**: [HBM 검증 실무](../../hbm_dv/)
- **이해도 점검**: [퀴즈](../quiz/12_electrical_timing_package_quiz/)
