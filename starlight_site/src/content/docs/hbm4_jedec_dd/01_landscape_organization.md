---
title: "01 — 규격 지형도와 조직 구조"
description: JESD270-4 §1–3.1 · 채널·pseudo-channel이 무엇을 공유하는가, 그 공유가 만드는 경합 시나리오와 검증 항목
---

:::tip[🎯 Learning Objectives]
이 모듈을 마치면:

- **Interpret** JESD270-4 §1–2의 Scope·Features 조문을 읽고 그것이 만드는 **실패 모드 목록**으로 옮긴다.
- **Differentiate** 채널과 pseudo-channel이 각각 무엇을 공유하고 무엇을 분리하는지 자원 단위로 구분한다.
- **Calculate** 채널당·전역 신호 수로부터 스택 전체의 신호 마이크로범프 예산을 산출한다.
- **Determine** 검증 환경이 무엇을 채널당·PC당·스택당 몇 벌 모델링해야 하는지 조문 근거로 결정한다.
- **Construct** 공통 커맨드의 "양쪽 PC 조건" 규칙을 assertion으로, MR 공유를 reference model로 옮기고 그 수단 선택을 정당화한다.
- **Derive** 채널 클럭 관계·스택 높이·밀도 조합에서 구성 coverage 축을 도출한다.
- **Justify** 규격이 base logic die를 요구하지도 금지하지도 않는 이유와 그것이 "표준 VIP 부재"로 이어지는 귀결을 설명한다.
:::

:::note[Prerequisites]
- HBM 구조 개괄 — [HBM 아키텍처 Ch03 스택 구조](../../hbm/03_stack_architecture/)
- DRAM 동작 기본(activate/precharge/refresh) — [DRAM / DDR](../../dram_ddr/)
- 본 코스의 [인용·저작권 고지](../)를 먼저 읽으세요.
:::

:::caution[인용 고지]
본 장은 **JESD270-4 (2025-04, WIP draft)** §1–§3.1을 근거로 하되, 조문을 **요약·재구성**한 것입니다. 표·그림은 옮기지 않고 번호로 지시합니다. 정밀 수치는 **JEDEC 원문 우선**.
:::

---

## 1. 규격이 스스로를 정의하는 방식

HBM4 규격의 첫 문단은 짧지만 검증 제약을 세 개 던집니다 (§1 Scope).

1. HBM4 DRAM은 **호스트 연산 다이와 밀결합**되며 인터페이스가 **분산(distributed)** 되어 있다.
2. 인터페이스는 **독립 채널**로 나뉘고, **각 채널은 서로 완전히 독립**이다.
3. 채널들은 **서로 동기일 필요가 없다(not necessarily synchronous)**.

세 번째가 검증에 가장 직접적입니다. 채널이 비동기라는 것은 **최대 32개의 독립 클럭 도메인이 존재할 수 있다**는 뜻이고, 그 사이를 오가는 신호마다 CDC 결함의 여지가 있다는 뜻입니다. "채널이 독립"을 *논리적 독립*으로만 읽으면, 전 채널을 같은 클럭으로 자극하는 환경을 만들고도 이상함을 못 느낍니다 — CDC 경로는 한 번도 안 건드린 채 커버리지는 높게 나옵니다.

그리고 각 채널 인터페이스는 **64-bit 데이터 버스를 DDR로** 운용합니다 (§1).

### Features 조문을 검증 항목으로 옮기기

§2의 항목들은 그대로 검증 체크리스트가 됩니다. 성격별로 묶으면 이렇습니다.

| 분류 | 조문 (§2) | 검증에 주는 것 |
|---|---|---|
| **전송 단위** | 접근당 **256-bit prefetch**, **BL = 8** | 데이터 경로 폭과 버스트 카운터 깊이가 고정된다 |
| **폭** | 채널당 **64 DQ + ECC/SEV 핀**, PC 모드에서 **32 DQ** | PC 단위로 데이터 경로를 쪼갤 근거 |
| **클럭** | 커맨드/주소용 **차동 CK_t/CK_c** | 단일 클럭 쌍이 채널 전체 커맨드를 규율 |
| **커맨드** | **DDR 커맨드/주소**. Row ACTIVATE **1.5 사이클**, 그 외 row **0.5 사이클**, PDE/SRE **1 사이클**, column **1 사이클** | 커맨드 디코더가 **반 사이클 단위**로 동작해야 한다 |
| **인터페이스** | **semi-independent row/column 커맨드 인터페이스** | 두 발행 경로를 병렬로 두되 상호 규칙이 필요 |
| **스트로브** | 단방향 차동 **RDQS_t/_c, WDQS_t/_c — DWORD당 한 쌍** | 읽기·쓰기 스트로브가 분리된 소스 동기 구조 |
| **규모** | 장치당 최대 **32채널**, 채널 밀도 **3 Gb~16 Gb** | 파라미터화 범위 |
| **뱅크** | 채널당 **16 / 32 / 48 / 64 뱅크**, **bank group 지원** | 뱅크 상태 머신의 인스턴스 수가 밀도에 종속 |
| **페이지** | PC당 **1 KB** | 행 버퍼 관리 단위 |
| **전기** | I/O 전압 **vendor specific**, Tx driver **0.4 V**, DRAM core **1.05 V** | 전원 도메인 분리 |
| **종단** | 데이터/주소/커맨드/클럭 **무종단(unterminated)**, 데이터 인터페이스 **비정합(unmatched)** | 신호 무결성 부담이 짧은 거리로 상쇄되는 구조 |

:::tip[조문 읽기 요령]
"Row Activate commands require one-and-a-half-cycle"라는 한 줄은 **monitor의 샘플링 해상도**를 결정합니다. 전체 커맨드 집합이 0.5 / 1 / 1.5 사이클로 나뉘므로, 정수 사이클로 샘플링하는 monitor는 1.5 사이클 `ACT`를 놓치거나 두 번 셉니다. 검사가 아니라 **환경의 전제조건**이라 틀려도 에러가 안 나고, 커버리지가 이유 없이 낮게 나오는 형태로만 드러납니다.
:::

## 2. 조직 — 스택, 채널, SID

### 무엇이 몇 개인가

§3 Organization의 골자는 다음과 같습니다.

- 스택당 최대 **32채널 / 64 pseudo-channel**
- **32채널을 만들려면 최소 4개의 DRAM die**가 필요하다
- 스택은 **4 / 8 / 12 / 16-high** 를 지원한다
- **4개를 넘는 die**는 채널을 더 늘리는 게 아니라 **용량 · SID · PC당 뱅크 수**를 늘린다

마지막 항목이 SID(Stack ID)의 정체를 설명합니다. 채널 수가 32에서 멈추므로, 그 위에 쌓는 die는 **같은 채널 안에서 더 깊은 주소 공간**으로 편입됩니다. 그래서 SID는 별도의 "층 선택 신호"가 아니라 **뱅크 주소의 확장 비트**로 동작합니다 — 이 점은 [02장](../02_addressing_bank_groups/)에서 주소 표로 확인합니다.

### 채널의 물리적 배치는 벤더가 정한다

규격은 채널을 die에 어떻게 나눌지를 **강제하지 않습니다**(§3). 한 채널의 메모리가 여러 die에 분산되는 구성도 허용됩니다. 다만 조건이 하나 붙습니다.

> **한 채널 내의 모든 접근은 동일한 레이턴시를 가져야 한다** (§3)

검증 관점에서 이 한 줄이 중요합니다. 물리적으로 다른 die에 있는 뱅크라도 **레이턴시가 같아야** 하므로, 이것은 곧 **검사 가능한 명제**입니다 — SID를 바꿔 가며 읽고 레이턴시 분포가 하나로 모이는지 보면 됩니다. 벤더는 짧은 경로에 지연을 넣어 균등화하며, 그 균등화가 깨지면 **고 SID에서만** read 데이터가 어긋납니다. 낮은 SID만 자극하는 환경은 이 결함을 영원히 못 봅니다.

## 3. 채널과 Pseudo-channel — 무엇을 공유하는가

이 절이 이 장의 핵심입니다. "독립"이라는 단어가 두 층에서 각각 다른 의미를 갖습니다.

```d2
direction: down

CH: "Channel N — 완전 독립\nCK_t/CK_c · R[9:0] · C[7:0] 공유" {
  style.fill: "#e3f2fd"
  style.font-color: "#0A0F25"

  shared: "공유 자원 — 주소의 PC 비트로 대상 선택\n· row/column 커맨드 버스\n· CK 입력\n· Mode Register\n· Power-down / Self-refresh" {
    style.fill: "#fff8e1"
    style.font-color: "#0A0F25"
  }

  pc0: "Pseudo Channel 0\nDWORD0 (DQ[31:0])\n독립 뱅크 집합 · 1 KB page\n256-bit prefetch" {
    style.fill: "#e8f5e9"
    style.font-color: "#0A0F25"
  }

  pc1: "Pseudo Channel 1\nDWORD1 (DQ[63:32])\n독립 뱅크 집합 · 1 KB page\n256-bit prefetch" {
    style.fill: "#e8f5e9"
    style.font-color: "#0A0F25"
  }
}

GLOBAL: "전역 신호 (스택 공통)\nRESET_n · CATTRIP · IEEE1500 테스트 포트\n전원" {
  style.fill: "#eceff1"
  style.font-color: "#0A0F25"
}

GLOBAL -> CH: "채널 무관"
CH.shared -> CH.pc0: "PC = 0" { style.font-color: "#0A0F25" }
CH.shared -> CH.pc1: "PC = 1" { style.font-color: "#0A0F25" }
```

### 채널 층 — 완전 독립

각 채널은 **독립적인 커맨드·데이터 인터페이스**를 갖습니다(§3.1). 채널 간에 공유되는 것은 다음뿐입니다.

- `RESET_n` (전역 스택 리셋)
- `CATTRIP` (파국 온도 센서)
- **IEEE 1500 테스트 포트**
- 전원 공급

그리고 채널은 **독립적으로 클럭킹**되며 서로 동기일 필요가 없습니다.

### Pseudo-channel 층 — 준독립(semi-independent)

PC는 채널을 **32 DQ씩 둘로 나눈 하위 채널**이며, 각 PC는 **독립적인 뱅크 집합**에 접근합니다. 한 PC의 요청은 **다른 PC의 데이터에 접근할 수 없습니다**(§3.1.2).

무엇을 공유하고 무엇을 나누는지가 검증 환경의 모델 구조를 가릅니다.

| 자원 | PC 간 | 근거 |
|---|---|---|
| DQ (데이터 경로) | **분리** — DWORD0↔PC0, DWORD1↔PC1 | §3.1.2 |
| 뱅크 집합 | **분리** | §3.1.2 |
| row/column 커맨드 버스 | ⚠️ **공유** | §3.1.2 |
| CK 입력 | ⚠️ **공유** | §3.1 |
| **Mode Register** | ⚠️ **공유** | §3.1.2 |
| 커맨드 decode/실행 | **개별 수행** | §3.1.2 |
| Power-down / Self-refresh | ⚠️ **공통** | §3.1.2 |

커맨드는 주소의 **PC 비트**로 어느 PC를 향하는지 지정됩니다(§3.1.2).

:::caution[여기서 모델이 갈린다]
**배열 접근 타이밍은 PC마다 개별로 셉니다** (§3.1.2, Table 3). PC0에 ACTIVATE를 보낸 직후 PC1에 ACTIVATE를 보낼 수 있고, PC0에 다시 보내려면 그때서야 `tRRD`(PC0)를 기다립니다.

그런데 **두 PC에 공통인 커맨드**(PDE, PDX, SRE, SRX, MRS)는 다릅니다 — 발행 시점에 **양쪽 PC 모두**의 타이밍 조건이 충족되어야 합니다.

즉 타이밍 카운터는 **PC별로 두 벌** 두되, 공통 커맨드 판정은 **두 벌의 AND**여야 합니다. 한 벌만 두면 개별 커맨드에서 false FAIL이 나고, AND로 묶지 않으면 실제 위반을 조용히 통과시킵니다. 이 규칙을 assertion으로 옮기는 방법은 아래 5.2절에서 다룹니다.
:::

Table 3이 PC별로 개별 계수되는 타이밍을 세 묶음으로 나열합니다 — **Row 계열**(tRC·tRAS·tRCDRD·tRCDWR·tRRDL·tRRDS·tFAW·tRTP·tRP·tWR), **Column 계열**(tCCDL·tCCDS·tCCDR·tWTRL·tWTRS·tRTW), **Refresh 계열**(tRFC·tRFCPB·tRREFD·tREFI·tREFIPB).

### AWORD와 DWORD

규격은 신호를 두 묶음으로 부릅니다.

- **DWORD** — 데이터 워드. **DWORD0의 모든 I/O 신호가 PC0에**, **DWORD1이 PC1에** 대응합니다(§3.1.2). 스트로브도 DWORD당 한 쌍입니다(§2).
- **AWORD** — 주소/커맨드 워드. `APAR`(패리티), `AERR`(오류 신호), `RFU`가 **AWORD당 1개**씩 배정됩니다(§3.1.1, Table 1).

이 명명이 중요한 이유는 규격 전반이 이 단위로 기술되기 때문입니다. Lane repair도, loopback MISR도 AWORD/DWORD 단위로 갈립니다([10장](../10_test_repair/)).

### 이중 커맨드 인터페이스

HBM4는 늘어난 신호 수를 활용해 **채널마다 semi-independent한 row/column 커맨드 인터페이스**를 제공합니다(§3.1.3). 목적은 명시적입니다 — **read/write 커맨드를 activate/precharge와 동시에 발행**해 커맨드 대역폭을 높이는 것.

검증 관점에서는 발행 경로가 둘이 되므로 **두 경로 사이의 순서 규칙**이 통째로 새로운 검사 항목이 됩니다. 그리고 monitor는 두 경로를 **동시에** 관측해야 합니다 — row 경로만 보는 monitor는 동시 발행 구간에서 커맨드를 놓칩니다. 상세는 [06장](../06_row_commands/)·[07장](../07_column_commands/).

## 4. 규격이 열어둔 자리 — Base Logic Die

여기가 이 장에서 가장 자주 오해되는 지점입니다.

> DRAM 벤더는 스택 최하단에 신호 재분배 등의 기능을 제공하는 **선택적 인터페이스 다이를 요구하도록 선택할 수 있다**. 벤더는 통상 DRAM die에 있는 많은 로직 기능을 이 로직 다이에 구현하도록 선택할 수 있다. **본 표준은 그러한 해법을 명시적으로 요구하지도, 금지하지도 않는다.** — §3 (요약)

즉 **base logic die는 JEDEC 규격의 필수 구성이 아닙니다.** 규격이 정의하는 것은 호스트가 보는 **인터페이스와 동작**이고, 그것을 어떤 물리 구조로 만족시킬지는 벤더의 몫입니다.

:::tip[이 조문이 산업 구조를 만든다]
규격이 "요구하지도 금지하지도 않는다"고 쓴 자리가 곧 **제품 차별화 지점**입니다. base die가 규격 밖에 있기 때문에 벤더는 거기에 무엇이든 넣을 수 있고, 그래서 **Custom HBM**이 성립합니다 — 메모리 컨트롤러를 내리든, 고객 전용 가속 로직을 얹든 규격 위반이 아닙니다.

같은 이유로, base die 내부에는 **표준 검증 IP가 존재할 수 없습니다.** 표준이 정의하지 않은 것에 대한 상용 VIP는 만들어질 수 없기 때문입니다. 이것이 [`hbm_dv`](../../hbm_dv/03_custom_uvm_agent/)에서 Custom UVM Agent를 직접 만들어야 하는 근본 이유입니다.
:::

규격이 벤더에게 열어둔 자리는 이것만이 아닙니다. 조문에서 **"vendor specific" / "may choose" / "implementation specific"** 을 찾으면 그 목록이 나옵니다 — I/O 전압(§2), 채널의 die 분산 방식(§3), on-die ECC의 symbol 크기(§6.9) 등.

## 🔬 검증 적용

### 5.1 무엇이 깨질 수 있는가

이 장의 조문은 **구조**를 규정합니다. 구조 규정을 어기는 방식은 대부분 조용합니다 — 즉시 터지지 않고 특정 조합에서만 드러납니다.

| 조문 | 위반 형태 | 증상 | 잡히는 시점 |
|---|---|---|---|
| §3.1.2 공통 커맨드는 **양쪽 PC** 조건 충족 | 한쪽 PC 조건만 보고 `MRS`·`PDE`·`SRE` 발행 | 관대한 모델이면 통과. 실제 장치에서만 실패 | **없음** — 명시 검사를 두지 않으면 안 잡힌다 |
| §3.1.2 Mode Register **공유** | MR을 PC별로 모델링 | PC1 트랜잭션이 PC0가 쓴 설정으로 동작 | MR을 바꾸는 시퀀스에서만 |
| §3.1.2 뱅크 집합 **분리** | PC0 요청이 PC1 데이터에 도달 | 데이터 오염 | scoreboard 미스매치 |
| §3.1 채널 **비동기 가능** | 전 채널을 같은 클럭·같은 위상으로 자극 | CDC 결함이 회귀 내내 잠복 | **실리콘** |
| §3 채널 내 **동일 레이턴시** | die 분산에 따라 SID별 레이턴시 상이 | 특정 SID에서만 read 데이터가 어긋남 | 고 SID를 자극해야만 |
| §3.1.2 배열 타이밍 **PC별 계수** | 타이밍을 채널당 한 벌로 계수 | 과보수 발행 → 성능 손실. checker면 **false FAIL** | 성능 회귀 |
| §2 커맨드 **0.5 / 1 / 1.5 사이클** | monitor가 정수 사이클로 샘플링 | 1.5 사이클 `ACT`를 놓치거나 두 번 센다 | 커버리지가 이상하게 낮음 |

마지막 두 줄이 특히 중요합니다. **검증 환경 자신의 버그**이며, 증상이 "DUT 버그처럼 보이거나" "아무것도 안 보이는" 형태로 나타납니다.

:::caution[구조를 모델링할 때의 실수 지도]
Q: 환경은 무엇을 **몇 벌** 들고 있어야 하는가? 조문이 그대로 답합니다.

| 모델 요소 | 인스턴스 수 | 근거 | 틀리면 |
|---|---|---|---|
| 채널 Agent (커맨드 발행·monitor) | **× 32** | 채널 완전 독립 (§3.1) | — |
| ↳ PC별 뱅크 상태 · 배열 타이밍 카운터 | **× 2 (채널 내)** | PC별 개별 계수 (§3.1.2) | 채널당 한 벌 → false FAIL |
| ↳ Mode Register 모델 | **× 1 (채널 내)** | 두 PC가 공유 (§3.1.2) | PC별로 두면 실제 장치와 갈림 |
| ↳ 저전력 상태 모델 | **× 1 (채널 내)** | PD/SR이 두 PC 공통 (§3.1.2) | PC별로 두면 진입 조건이 헐거워짐 |
| 리셋·온도 감시 | **× 1 (스택)** | `RESET_n`·`CATTRIP` 전역 (§3.1) | — |
| IEEE 1500 접근 | **× 1 (스택)**, `WSO`만 채널별 | 테스트 포트 전역 (Table 2) | — |

**뱅크 상태는 PC별 두 벌, Mode Register는 채널당 한 벌.** 이 두 줄이 반대로 되어 있는 환경을 자주 봅니다.
:::

또 하나, **클럭 도메인의 개수가 곧 자극의 축**입니다.

```
호스트 클럭 도메인
   ├─ CH0  CK 도메인 ─┐
   ├─ CH1  CK 도메인  │  최대 32개의 독립 도메인
   ├─ ...             │  (채널 내 두 PC는 CK 공유 — 같은 도메인)
   └─ CH31 CK 도메인 ─┘
   └─ WRCK 도메인 (IEEE1500) ── 전 채널 횡단
```

채널 사이에는 CDC가 있고 **PC 사이에는 없습니다**. 이 구분을 놓치면 두 방향으로 틀립니다 — PC 간에 없는 비동기를 자극하려 하거나, 채널 간 비동기를 자극하지 않아 CDC를 전혀 안 건드리거나.

### 5.2 어떻게 잡는가 — 수단 선택

규칙의 **성격**이 수단을 정합니다. 규칙 일곱 개를 assertion 일곱 개로 옮기는 것은 답이 아닙니다([`hbm_dv` Ch09](../../hbm_dv/09_assertion_checker/)).

| 규칙 | 성격 | 수단 | 이유 |
|---|---|---|---|
| 공통 커맨드 = 양쪽 PC 조건 AND | **시간 관계** | **SVA** | 발행 시점의 국소 조건. 즉시 판정 가능 |
| MR이 두 PC에 공유됨 | **상태 일치** | **reference model** | 시간 규칙이 아니라 값의 정합. SVA로 쓰면 부자연스럽다 |
| PC0 요청이 PC1 데이터에 닿지 않음 | **데이터 무결성** | **scoreboard** | 주소→데이터 대응을 끝까지 추적해야 판정된다 |
| 채널 내 동일 레이턴시 | **분포** | **scoreboard 통계** | 한 트랜잭션으로는 판정 불가. SID별 레이턴시를 모아 비교 |
| 커맨드 반 사이클 해상도 | **샘플링** | **monitor 구현** | 검사가 아니라 **환경의 전제조건**. 틀리면 모든 검사가 무의미 |

**공통 커맨드 게이팅** — 이 장에서 유일하게 assertion이 정답인 규칙입니다.

```systemverilog
// bind 대상: 채널 컨트롤러. §3.1.2 — PDE/PDX/SRE/SRX/MRS 는
// 발행 시점에 두 PC 모두의 타이밍 조건이 충족되어야 한다.
module hbm4_pc_common_chk (
    input logic       ck, rst_n,
    input logic       common_cmd_vld,   // PDE/PDX/SRE/SRX/MRS 중 하나 발행
    input logic [1:0] pc_timing_ok      // PC별 조건 충족 플래그 (두 벌)
);
  import uvm_pkg::*;
  `include "uvm_macros.svh"

  property p_common_cmd_both_pc;
    @(posedge ck) disable iff (!rst_n)
      common_cmd_vld |-> (&pc_timing_ok);        // AND — OR 로 쓰면 조용히 통과한다
  endproperty

  a_common_cmd_both_pc: assert property (p_common_cmd_both_pc)
    else `uvm_error("PC_COMMON", $sformatf(
         "공통 커맨드 발행 시점에 PC 조건 미충족 (pc_timing_ok=%b)", pc_timing_ok))

  // 이 assertion 이 "한 번도 안 걸렸다"가 의미 있으려면
  // 한쪽만 준비된 상태가 실제로 만들어졌어야 한다.
  c_one_pc_only: cover property (@(posedge ck) disable iff (!rst_n)
      (pc_timing_ok inside {2'b01, 2'b10}) ##1 common_cmd_vld);
endmodule
```

`&pc_timing_ok` 를 `|pc_timing_ok` 로 쓰면 검사가 **항상 통과**합니다. 그리고 그 사실을 알아채는 유일한 방법이 함께 둔 `cover property` 입니다 — **한쪽 PC만 준비된 상황이 실제로 발생했는가**를 세지 않으면, assertion이 무해한지 무력한지 구분할 수 없습니다.

**MR 공유** — 이쪽은 assertion이 아니라 모델입니다.

```systemverilog
// 채널당 한 벌. PC 번호를 인자로 받지 않는 것이 이 클래스의 요점이다.
class hbm4_mr_model extends uvm_object;
  `uvm_object_utils(hbm4_mr_model)
  protected bit [7:0] m_mr[20];        // MR0~MR19 (§5)

  function void write_mr(int idx, bit [7:0] val);
    m_mr[idx] = val;                   // 어느 PC가 썼든 채널 전체에 반영된다
  endfunction

  // 조회에 PC 인자가 없다 — 있으면 그 자체가 설계 오류다
  function bit [7:0] read_mr(int idx);
    return m_mr[idx];
  endfunction
endclass
```

MR 모델에 `pc` 인자가 있으면 그것이 곧 버그입니다. **인터페이스에서 실수를 불가능하게** 만드는 편이, 나중에 값이 갈렸는지 검사하는 것보다 낫습니다.

### 5.3 무엇을 덮었다고 말할 수 있는가

이 장의 조문은 대부분 **구성(configuration)** 을 규정합니다. 따라서 coverage도 트랜잭션이 아니라 **구성 공간**을 덮어야 합니다.

```systemverilog
covergroup cg_hbm4_organization with function sample(hbm4_cfg_t cfg, cmd_e cmd, int pc);
  option.per_instance = 1;

  // --- 구성 축 (§3.2, Table 4) --------------------------------------------
  cp_stack_height : coverpoint cfg.height  { bins h[] = {4, 8, 12, 16}; }
  cp_density      : coverpoint cfg.density { bins d[] = {24, 32}; }        // Gb
  cp_sid_bits     : coverpoint cfg.sid_used_bits { bins b[] = {0, 1, 2}; }
  cp_num_ch       : coverpoint cfg.num_ch  { bins min = {1}; bins mid = {[2:31]}; bins max = {32}; }

  // 규격이 정의한 조합만 유효하다. 나머지에 히트가 나면 환경이 불법 구성을 만든 것.
  x_capacity : cross cp_stack_height, cp_density;

  // --- 공유 자원 경합 (§3.1.2) --------------------------------------------
  cp_pc           : coverpoint pc { bins pc0 = {0}; bins pc1 = {1}; }
  cp_cmd_class    : coverpoint cmd {
    bins per_pc  = {ACT, PRE, RD, WR};      // PC 개별
    bins common  = {MRS, PDE, PDX, SRE, SRX};  // 두 PC 공통
  }
  // 공통 커맨드를 두 PC 어느 쪽 문맥에서도 발행해 봤는가
  x_common_pc : cross cp_cmd_class, cp_pc {
    ignore_bins na = binsof(cp_cmd_class.per_pc);
  }

  // --- 채널 클럭 관계 (§3.1 — 채널은 비동기일 수 있다) ----------------------
  cp_ch_clk_rel : coverpoint cfg.ch_clk_relation {
    bins synchronous  = {SYNC};        // 전 채널 동일 주파수·위상
    bins phase_offset = {PHASE};       // 동일 주파수, 위상 차
    bins asynchronous = {ASYNC};       // 주파수 자체가 다름  ← 여기가 비면 CDC 미검증
  }
endgroup
```

`cp_ch_clk_rel.asynchronous` 가 **0인 채로 회귀가 100% 통과하는 것**이 이 장에서 가장 흔한 거짓 안심입니다. 채널이 비동기일 수 있다는 조문(§3.1)을 자극으로 옮기지 않으면, CDC 경로는 한 번도 검증되지 않은 채 커버리지 수치는 높게 나옵니다.

`x_capacity` 도 마찬가지입니다. 스택 높이 × 밀도 조합은 여덟 가지인데(Table 4), 환경이 기본 구성 하나만 쓰면 나머지 일곱 개의 주소 폭·SID 비트 수가 전혀 자극되지 않습니다.

### 5.4 어떻게 자극하는가

위 bin에 도달하려면 무엇을 발행해야 하는가입니다. 세 갈래로 나뉩니다.

**① 구성 랜덤화** — 채널 수·밀도·스택 높이는 트랜잭션이 아니라 **환경 구성**입니다. 시퀀스가 아니라 `uvm_config_db` 로 주입되고, 회귀 시드마다 달라져야 합니다. 구성 프로파일을 어떻게 나누는지는 [`hbm_dv` Ch06](../../hbm_dv/06_env_hierarchy/).

**② 클럭 관계 자극** — 채널별 클럭 생성기를 독립 randomize 합니다.

```systemverilog
class ch_clk_cfg extends uvm_object;
  rand int unsigned period_ps[32];
  rand int unsigned phase_ps [32];
  rand clk_rel_e    relation;

  // §3.1 — 채널은 서로 동기일 필요가 없다. 세 관계를 모두 만든다.
  constraint c_relation {
    (relation == SYNC)  -> foreach (period_ps[i]) { period_ps[i] == period_ps[0];
                                                    phase_ps[i]  == 0; }
    (relation == PHASE) -> foreach (period_ps[i]) { period_ps[i] == period_ps[0];
                                                    phase_ps[i] inside {[0 : period_ps[0]-1]}; }
    (relation == ASYNC) -> foreach (period_ps[i]) { period_ps[i] inside {[625 : 1250]}; }
  }
  // 채널 내 두 PC 는 CK 를 공유하므로 PC 별 클럭 항목은 두지 않는다 (§3.1)
endclass
```

**③ 공유 자원 경합 시퀀스** — 이 장 고유의 시나리오입니다. 한쪽 PC를 바쁘게 만들어 두고 공통 커맨드를 발행합니다.

```systemverilog
// PC0 을 tRRD 가 아직 안 끝난 상태로 만들어 두고 MRS 를 시도한다.
// 목표: c_one_pc_only cover 를 히트시켜 5.2 의 assertion 이 무력하지 않음을 증명한다.
class seq_pc_contention extends uvm_sequence #(hbm4_cmd_item);
  `uvm_object_utils(seq_pc_contention)

  virtual task body();
    `uvm_do_with(req, { cmd == ACT; pc == 0; })     // PC0 을 바쁘게
    `uvm_do_with(req, { cmd == ACT; pc == 1; })     // PC1 은 기다리지 않는다 (§3.1.2)
    // 여기서 PC0 의 tRRD 는 아직 진행 중 — 공통 커맨드가 막혀야 한다
    `uvm_do_with(req, { cmd == MRS; })
  endtask
endclass
```

시나리오를 어떤 단위로 재사용 가능하게 쪼개는지는 [`hbm_dv` Ch08](../../hbm_dv/08_testcase_scenarios/)에서 다룹니다. 여기서 확인할 것은 **무엇을 자극해야 하는가**뿐입니다.

:::tip[base die가 규격 밖이라는 사실의 검증상 귀결]
§3이 base logic die를 요구도 금지도 하지 않는다는 것은, 그 안의 동작에 대해 **참조할 규격이 없다**는 뜻입니다. 따라서

- base die 내부 로직에는 **상용 VIP가 존재할 수 없습니다.** 표준이 정의하지 않은 것에 대한 VIP는 만들어질 수 없기 때문입니다 → Custom Agent를 직접 만드는 근본 이유([`hbm_dv` Ch03](../../hbm_dv/03_custom_uvm_agent/)).
- 반대로 **DRAM die 인터페이스는 규격이 정의**하므로, 그 경계에서는 규격을 기대값으로 쓸 수 있습니다.

검증 계획의 첫 작업은 이 **경계선을 긋는 것**입니다. 어디까지가 "규격이 답을 주는 영역"이고 어디부터가 "벤더 문서와 내부 사양이 답을 주는 영역"인가 — 12장에서 종합합니다.
:::

## 6. 대표 문제 — dry-run

### 문제 1 — Pseudo-channel 타이밍 계수

> 채널 0에서 다음 순서로 커맨드를 발행하려 한다.
> `ACT PC0` → `ACT PC1` → `ACT PC0` → `MRS`
> 각 단계에서 무엇을 기다려야 하는가?

<details>
<summary>풀이</summary>

1. **`ACT PC0`** — 즉시 발행 가능(다른 제약이 없다면).
2. **`ACT PC1`** — **기다리지 않는다.** 배열 접근 타이밍은 PC별로 개별 계수되므로(§3.1.2), PC0의 `tRRD`는 PC1 발행을 막지 않는다. 단 커맨드 버스는 공유이므로 **버스 점유 충돌만** 피하면 된다.
3. **`ACT PC0`(두 번째)** — **`tRRD`(PC0)** 를 기다린다. 같은 PC에 대한 연속 ACTIVATE이므로. 뱅크 그룹이 같으면 `tRRDL`, 다르면 `tRRDS`([02장](../02_addressing_bank_groups/)).
4. **`MRS`** — **두 PC 모두**의 타이밍 조건이 충족되어야 한다(§3.1.2). PC0만 보고 발행하면 PC1이 아직 조건을 만족하지 못한 상태일 수 있다.

**검증 결론**: 4단계가 이 장의 핵심 시나리오다. 3단계까지는 어떤 환경에서도 나오지만, 4단계의 "PC0은 아직 바쁜데 MRS 발행"은 **의도적으로 만들지 않으면 나오지 않는다.** 5.4절의 `seq_pc_contention` 이 이 순서를 그대로 발행하는 시퀀스다.
</details>

### 문제 2 — 신호 예산

> 16-high 스택 한 개가 요구하는 **신호** 마이크로범프 수는? (전원 제외)

<details>
<summary>풀이</summary>

채널 수는 스택 높이와 무관하게 최대 **32**로 고정된다(§3). 4-high를 넘는 die는 채널을 늘리지 않고 용량·SID·뱅크를 늘린다.

```
120 (채널당, Table 1) × 32 = 3,840
                     + 56 (전역, Table 2)
                     = 3,896
```

**함정**: "16-high니까 신호도 4배"라고 계산하면 틀린다. 채널 수가 고정이므로 **신호 수는 스택 높이에 무관**하고, 늘어나는 것은 SID 비트로 표현되는 **주소 공간**이다.
</details>

## 핵심 정리

- 채널은 **완전 독립이고 비동기일 수 있다**(§1) — 최대 32개 클럭 도메인. **비동기 관계를 자극하지 않으면 CDC는 미검증인 채 커버리지만 올라간다.**
- 4-high를 넘는 die는 채널이 아니라 **용량·SID·뱅크**를 늘린다. **신호 수는 스택 높이에 무관**하다.
- 한 채널 내 모든 접근은 **동일 레이턴시**여야 한다(§3) — 곧 **SID별 레이턴시 분포가 하나로 모이는지**가 검사 가능한 명제다.
- PC는 **DQ·뱅크는 분리, 커맨드 버스·CK·Mode Register·저전력 상태는 공유**한다(§3.1.2).
- 배열 타이밍은 **PC별 개별 계수**, 공통 커맨드(PDE·PDX·SRE·SRX·MRS)는 **양쪽 조건 AND**. 모델은 뱅크 상태를 **PC별 두 벌**, Mode Register를 **채널당 한 벌** 든다.
- **DWORD0↔PC0, DWORD1↔PC1**. `APAR`·`AERR`·`RFU`는 **AWORD당 1개**.
- 커맨드는 **0.5 / 1 / 1.5 사이클**로 나뉜다 — monitor는 **반 사이클 해상도**로 샘플링해야 한다. 틀려도 에러가 안 나고 커버리지만 낮아진다.
- **Base logic die는 규격의 필수 구성이 아니다**(§3). 그 열린 자리가 Custom HBM과 **"표준 VIP 부재"** 를 동시에 설명한다 — 검증 계획의 첫 작업은 규격이 답을 주는 경계선을 긋는 것이다.
- 채널당 120 + 전역 56 → **스택당 약 3,896 신호 범프** [추론]. 이 규모에서 결함 범프는 통계적으로 발생하므로 lane repair는 선택 기능이 아니라 **반드시 검증해야 할 mission 기능**이다([10장](../10_test_repair/)).

## Further Reading

- **규격**: JESD270-4 §1 Scope · §2 Features · §3 Organization · §3.1 Channel Definition (Table 1–3, Figure 1–2)
- **다음 장**: [02 — 주소 체계와 뱅크 그룹](../02_addressing_bank_groups/) — SID가 뱅크 주소로 동작하는 방식
- **개괄 복습**: [HBM 아키텍처 Ch03 스택 구조](../../hbm/03_stack_architecture/) · [Ch04 채널·Pseudo-channel](../../hbm/04_channels_addressing/)
- **이해도 점검**: [퀴즈](../quiz/01_landscape_organization_quiz/)
