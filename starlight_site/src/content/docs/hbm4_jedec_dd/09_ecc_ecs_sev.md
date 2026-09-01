---
title: "09 — On-die ECC · ECS · SEV"
description: JESD270-4 §6.9 · symbol 기반 ECC 엔진, 자동 스크럽, 실시간 심각도 전달, 그리고 임계값에 가려지는 오류
---

:::tip[🎯 Learning Objectives]
이 모듈을 마치면:

- **Derive** 304비트 codeword의 구성을 데이터·메타데이터·체크비트로 분해한다.
- **Explain** read 시 정정된 데이터를 배열에 되쓰지 않는 규정과 그것이 ECS를 필수로 만드는 이유를 설명한다.
- **Decode** `SEV` 핀의 BL8 버스트 위치별 인코딩으로 NE·CEs·CEm·UE를 판정한다.
- **Analyze** `ERRTH` 임계값이 CEs 보고를 걸러내는 구조를 분석하고, **환경이 원리적으로 관측할 수 없는 구간**을 특정한다.
- **Sequence** Auto ECS의 read-modify-write 다섯 갈래와 설정 동결 규칙을 정리한다.
- **Construct** 실제 판정과 핀에 나가는 값을 분리한 ECC reference model을 만들고, read 정정이 배열을 고치지 않음을 반영한다.
- **Evaluate** ECS 상태가 `RESET` 외에 지워지지 않는 성질이 **회귀 구조**에 부과하는 제약을 판단한다.
:::

:::note[Prerequisites]
- [04 — Mode Register](../04_mode_registers/) — `MR9`의 ECC 관련 8개 필드, `MR8` OP2
- [08 — Parity](../08_parity/) — `SEV`가 패리티 대상에서 제외되는 이유
- ECC 일반 원리 — [RAS 코스](../../ras/)
:::

:::caution[인용 고지]
본 장은 **JESD270-4 (2025-04, WIP draft)** §6.9를 근거로 **요약·재구성**한 것입니다. 표·그림은 옮기지 않고 규칙과 구조만 서술합니다. 정밀 값은 **JEDEC 원문 우선**.
:::

---

## 1. RAS를 구성하는 여섯 갈래

§6.9.1은 HBM4가 시스템 RAS를 달성하는 수단을 여섯 개로 나열합니다.

| 수단 | 이 코스에서 다루는 곳 |
|---|---|
| **symbol 기반 on-die ECC** | 이 장 |
| **read/write 메타데이터(MD) 비트** | 이 장 |
| **오류 스크러빙 메커니즘 (ECS)** | 이 장 |
| **오류 투명성 프로토콜** | 이 장 |
| 인터페이스 전송 패리티 | [08장](../08_parity/) |
| **결함 격리(fault isolation) 한계** | 이 장 |

여섯 갈래가 서로 다른 층에서 동작한다는 점이 중요합니다 — 패리티는 **전송 중** 오류를, ECC는 **저장 중** 오류를, 결함 격리는 **물리 설계**로 오류 확산을 제한합니다.

## 2. Codeword 구조

### 산술로 확인하기

규격이 제시하는 조각들을 맞추면 구조가 나옵니다.

| 요소 | 크기 | 근거 |
|---|---|---|
| 사용자 데이터 (PC당) | **256 b** | 32 DQ 핀 × BL8 |
| 메타데이터 MD (PC당) | **16 b** | 2 ECC 핀 × BL8 |
| **데이터워드** | **272 b** | 256 + 16 |
| 체크비트 | **구현 의존** (예: 32 b — 16b 단일 symbol 정정 가정 시) | §6.9.2 |
| **codeword** | **최소 304 b** | 272 + 32 |

```
256 b (DQ 32핀 × BL8)  +  16 b (ECC 2핀 × BL8)  =  272 b  데이터워드
272 b                  +  32 b (체크비트 예시)   =  304 b  codeword   ✅ "최소 304b"와 일치
```

[01장](../01_landscape_organization/)에서 본 *"채널당 64 DQ + ECC/SEV 핀"* 과 *"PC당 256-bit prefetch"* 가 여기서 결합됩니다. **ECC 핀은 별도 부가 회선이 아니라 codeword의 일부**를 나릅니다.

### 구현에 열린 것

> 사용되는 특정 **ECC H-matrix**, **symbol 크기**, **codeword 개수**는 **구현 의존**이다. — §6.9.2

[01장](../01_landscape_organization/)에서 정리한 "규격이 열어둔 자리" 목록에 하나가 더 붙습니다. 컨트롤러는 **정정 능력의 구체적 형태를 알 수 없고**, 알 필요도 없도록 설계되어 있습니다 — 필요한 것은 결과(심각도)뿐입니다.

### ⚠️ read 시 정정 데이터를 되쓰지 않는다

이 장에서 가장 중요한 조문입니다.

> read에서 DRAM은 **단일 symbol 크기 이하이면서 symbol 경계 안에 있는 모든 오류를 정정**한 뒤 메모리 컨트롤러에 데이터를 반환한다. **DRAM은 read 사이클 동안 정정된 데이터를 배열에 되쓰지 않는다.** — §6.9.2 (요약)

즉 **read는 오류를 고쳐서 주지만 원본은 그대로 둡니다.** 같은 주소를 다시 읽으면 또 정정이 일어납니다.

:::caution[이 규정이 ECS를 필수로 만든다]
정정이 배열에 반영되지 않으므로 **오류는 시간이 지나며 누적**됩니다. 처음에는 정정 가능한 단일 오류였던 것이, 같은 codeword에 두 번째 오류가 더해지면 **정정 불가능(UE)** 이 됩니다.

이것을 막는 유일한 수단이 **ECS(Error Check and Scrub)** 입니다. ECS만이 정정 결과를 **배열에 되씁니다.**

**검증 결론**: reference model의 셀 오류 맵을 **read에서 지우면 안 됩니다.** 지우면 두 번째 read에서 `NE`를 예측하는데 실제 장치는 또 정정합니다. 그리고 이 성질은 **같은 주소를 두 번 이상 읽는 자극**이 없으면 검증되지 않습니다 — 한 번만 읽으면 되쓰는 모델과 안 되쓰는 모델이 똑같이 통과합니다(7.4 ①).

동시에 이 구조가 read 경로를 단순하게 유지합니다 — read가 배열 쓰기를 유발하면 타이밍과 전력이 복잡해집니다. **정정은 실시간으로, 복원은 배경 작업으로** 분리한 설계입니다.
:::

### 메타데이터의 미묘한 규정

`MD`가 `MR9` OP0으로 비활성화되면:

- DRAM은 MD에 해당하는 **16비트에 대해 임의의 값을 가정할 수 있습니다.**
- **인터페이스 MD 기능이 활성인 상태에서 기록된 경우에만** 배열의 MD 비트가 유효함을 보장합니다.
- 다만 **ECC 엔진의 MD 비트 처리 자체는 인터페이스 MD 설정에 영향받지 않습니다.**

즉 MD를 껐다 켜면 **그 사이에 기록된 영역의 MD는 신뢰할 수 없습니다.** ECC 계산에는 계속 참여하므로 codeword 무결성은 유지되지만, MD 값 자체는 의미가 없습니다.

## 3. 결함 격리 — 물리 설계와 ECC의 접점

> 결함 격리는 **od-ECC 동작과 무관하게** 다양한 결함이 유발한 오류를 **특정 경계 안에 가두는** 관리다. 결함 격리 경계는 **다중 비트 결함의 정정 능력을 최대화하도록 ECC symbol 크기에 맞춰** 선택된다. 설계는 **가장 흔한 다중 비트 결함 모드가 정정 가능한 symbol 크기 이하의 오류를 만들도록** 보장해야 한다. — §6.9.3 (요약)

이것은 로직 설계가 아니라 **레이아웃·배열 설계의 요구사항**입니다. 물리적으로 인접한 셀들이 같은 symbol에 매핑되도록 배치해야, 국소적 결함이 여러 symbol에 흩어지지 않고 **한 symbol 안에 갇힙니다.**

:::tip[왜 이것이 규격에 있는가]
ECC는 "symbol 하나"까지 고칠 수 있습니다. 그런데 물리적 결함이 **두 symbol에 걸치면** 정정 불가입니다.

따라서 **ECC 설계와 배열 배치가 함께 결정되어야** 하며, 규격은 그 결합을 요구사항으로 명시했습니다. symbol 크기를 구현 의존으로 열어둔 것도 이 때문입니다 — 벤더의 배열 구조에 맞춰 symbol 크기를 고를 수 있어야 합니다.
:::

## 4. Auto ECS — 배경에서 도는 복원

### 동작 조건

Auto ECS는 on-die ECC를 사용해 **`REFab`과 self refresh(SRF) 기간 동안 배경에서** 동작합니다. 내부적으로 읽고, 오류를 검출·정정하고, **정정된 데이터를 배열에 되씁니다**(스크럽).

### Read-Modify-Write의 다섯 갈래

| 검출 결과 | 동작 |
|---|---|
| **오류 없음** | DRAM이 되쓸지 **선택 가능** |
| **단일 비트 오류 (SBE)** | 정정 후 **되쓰기** |
| **정정 가능 다중 비트 (CEm)** | 정정 후 되쓰기 — **`MR9` OP6(`ECSCEM`)로 활성/비활성** |
| **정정 불가 (UE)** | **비트를 수정하지 않으며, 배열에 되써서는 안 된다** |

UE에서 되쓰지 않는 것이 핵심입니다 — 잘못 "정정"한 값을 배열에 심으면 **원본 정보가 영구히 사라집니다.** 손상된 채로 두어야 나중에 다른 수단으로 복구할 여지가 남습니다.

### 로깅 범위

> Auto ECS 중 on-die ECC가 정정한 **모든 오류는 투명성 레지스터에 기록되어야** 한다. — §6.9.4

그리고 §6.9.1의 특징 목록에 결정적인 한 줄이 있습니다.

> **오류는 ECS 중에만 기록된다.**

:::caution[일반 read의 정정은 로그에 남지 않는다]
정상 동작 중 read에서 발생한 정정은 **실시간으로 `SEV` 핀에 신호될 뿐, 로그에 남지 않습니다.** 기록은 ECS 경로에서만 이뤄집니다.

**검증 함의**: 환경이 `SEV`를 매 read마다 관측하지 않으면 그 정정 사실은 **사라집니다.** 나중에 IEEE 1500으로 로그를 읽어도 나오지 않습니다. 곧 "로그가 비었으니 오류가 없었다"는 결론이 성립하지 않습니다 — 두 경로를 **모두** 수집해야 합니다(7.2 ③).

즉 오류 관측에는 **두 개의 독립된 경로**가 있고 둘 다 필요합니다.
- **실시간 경로**: `SEV` 핀 — read마다, 휘발성
- **기록 경로**: IEEE 1500 레지스터 — ECS 중에만, 영속
:::

### 설정 동결 규칙

ECS 관련 `MR`은 다섯 개이며 **전부 기본 비활성**입니다.

| 설정 | 위치 | 내용 |
|---|---|---|
| `ECSREF` | `MR9` OP4 | `REFab` 경유 Auto ECS |
| `ECSSRF` | `MR9` OP5 | Self Refresh 중 Auto ECS |
| `ECSCEM` | `MR9` OP6 | ECS 중 CEm 정정 |
| `ECSRES` | `MR9` OP7 | 오류 유형·주소 로그 리셋 (**self clearing**) |
| `ECSLOG` | `MR8` OP2 | 로그 읽기 시 오류 로그 리셋 |

순서 제약이 둘 있습니다.

> `MR9` OP[6:4]는 **DRAM 초기화 중에 프로그램되어야** 한다. **`ECSCEM`(OP6)은 `ECSREF`·`ECSSRF`(OP[5:4])보다 먼저 또는 동시에 프로그램되어야 하며, 첫 ECS 동작이 발생한 뒤에는 변경되어서는 안 된다.** 그렇지 않으면 후속 ECS 동작에서 **알 수 없는 동작**이 발생할 수 있다. — §6.9.4 (요약)

그리고 되돌릴 수 없습니다.

> **ECS 동작이 시작되면 Auto ECS를 리셋하는 유일한 방법은 장치 RESET이다.** 활성화 후 `ECSREF`나 `ECSSRF`를 비활성화하는 것은 **해당 모드의 ECS 동작만 중단**시킬 뿐이며, **ECS 주소 카운터나 ECS 로그를 리셋하지 않는다.** — §6.9.4 (요약)

:::caution[초기화 순서가 되돌릴 수 없는 결정을 만든다]
[04장](../04_mode_registers/)에서 "초기화 시 20개 MR을 모두 기록해야 한다"고 했는데, 그중 `MR9` OP[6:4]는 **순서까지 규정된** 항목입니다.

```
1. ECSCEM (OP6)  먼저 또는 동시에
2. ECSREF/ECSSRF (OP[5:4])
3. 첫 REFab 또는 SRE → ECS 시작
4. 이후 ECSCEM 변경 금지 (변경 시 동작 미정의)
```

그리고 한 번 시작되면 **장치 RESET 외에는 되돌릴 수 없습니다.** 즉 초기화 펌웨어가 `MR9`를 잘못 쓰면 런타임 복구가 불가능합니다.

또 하나 전제가 있습니다 — *"DRAM은 **ECS 실행 전에 배열 비트가 기록된 경우에만** 유효한 ECS 동작을 보장한다"*(§6.9.4). 초기화 직후 미기록 영역에 ECS가 돌면 체크비트가 무의미합니다. **메모리 초기화(스크러빙 write)가 ECS 활성화보다 앞서야** 합니다.
:::

### 타이밍 파라미터

| 기호 | 의미 |
|---|---|
| `tECSC` | HBM4가 **하나의 ECS 동작을 완료**하는 최대 시간 |
| `tECS` | **모든 codeword**에 대해 ECS를 완료하는 기간 (예: 24시간) |
| `tECSint` | `tECS` 안에 전 codeword를 덮기 위한 **평균 ECS 간격** |
| `ERRTH` | 투명성에 사용되는 **`ERRCNT`의 벤더 지정 필터 임계값** |

`tECSint`의 산출식이 명쾌합니다.

```
tECSint = 86,400 초 ÷ 전체 codeword 수        (tECS = 24시간 기준)
```

codeword 수는 **구성 의존**이므로, 용량이 클수록 ECS 간격이 짧아집니다 — 같은 24시간 안에 더 많은 codeword를 돌아야 하기 때문입니다.

## 5. 투명성 프로토콜 — 두 경로

§6.9.5 Table 66이 전달 수단을 명확히 나눕니다.

| 전달할 것 | 발생 시점 | 수단 |
|---|---|---|
| **실시간 심각도 메타데이터** | `RD`/`RDA` | **PC당 `SEV` 핀 2개** |
| **오류의 주소와 심각도 기록** | **ECS** | **IEEE 1500 레지스터** |

### `SEV` 인코딩 — 버스트 후반부를 쓴다

심각도는 BL8 트랜잭션의 버스트 위치에 실려 전달됩니다. 규칙을 정리하면 이렇습니다 (Table 67).

| 심각도 | 버스트 위치 0~3 | 버스트 위치 4~7 (`SEV[1]`, `SEV[0]`) |
|---|---|---|
| **NE** (오류 없음) | 둘 다 0 | `0`, `0` |
| **CEs** (정정된 단일) | 둘 다 0 | `0`, `1` |
| **CEm** (정정된 다중) | 둘 다 0 | `1`, `1` |
| **UE** (정정 불가) | 둘 다 0 | `1`, `0` |

**버스트 전반부(0~3)는 항상 0**이고, 후반부(4~7)에 `{SEV[1], SEV[0]}` 2비트 코드가 실립니다.

:::tip[왜 후반부인가]
ECC 판정은 codeword 전체를 받아야 가능합니다. BL8의 절반을 받은 시점에는 아직 결론이 없으므로, **후반부에 결과를 실어 보내는 것**이 자연스럽습니다.

**검증 함의**: monitor는 버스트 위치를 추적해야 하며 **위치 4~7의 값만 유효**합니다. 전반부를 함께 샘플링해 OR로 판정하면 **항상 `NE`가 나오고**, 그러면 오류 주입 테스트가 전부 "오류 없음"으로 조용히 통과합니다.

그리고 [08장](../08_parity/)에서 본 *"`SEV`는 패리티 계산에서 제외된다"* 는 규정이 여기서 이해됩니다 — `SEV`는 데이터가 아니라 **데이터에 대한 판정 결과**이므로 데이터 패리티의 대상이 아닙니다.
:::

심각도 신호 자체는 **`MR9` OP1**로 활성/비활성할 수 있습니다.

### ⚠️ `ERRTH`가 CEs를 가린다

Table 68이 정의하는 실제 전송 규칙에 필터가 들어 있습니다.

| on-die ECC 판정 | `SEV`에 실리는 값 |
|---|---|
| NE | NE |
| **CEs** | **`ERRCNT ≤ ERRTH`이면 → NE** / 이전 또는 현재 `ERRCNT > ERRTH`이면 → CEs |
| CEm | CEm (항상) |
| UE | UE (항상) |

그리고 §6.9.1의 특징 목록도 같은 말을 합니다 — **"SBE는 SBE 임계값을 초과한 뒤에만 신호된다."**

:::caution[정정이 일어났는데 NE로 보고된다]
단일 비트 정정이 실제로 발생했는데도, 누적 카운트가 `ERRTH` 이하이면 **`SEV`에는 NE(오류 없음)로 나갑니다.**

의도는 명확합니다 — 산발적인 단일 비트 정정은 정상 동작 범위이므로, 매번 보고하면 호스트가 노이즈에 파묻힙니다. 임계값을 넘어 **추세가 될 때만** 알립니다.

그러나 검증·디버그 관점에서는 다릅니다. **"NE가 나왔다"가 "오류가 없었다"를 뜻하지 않습니다.** `ERRTH`는 벤더 지정값이라 그 아래 구간은 관측 자체가 불가능합니다.

이것이 [`hbm_dv`](../../hbm_dv/11_dft_ras/)에서 말한 *"ECC가 결함을 가려 조용히 통과한다"* 의 정확한 메커니즘입니다. 가리는 주체가 ECC 정정만이 아니라 **`ERRTH` 필터**이기도 합니다.

**대응**: ECS 로그(IEEE 1500 경로)를 확인하거나, `ERRTH`를 넘길 만큼 오류를 주입하거나, ECC Engine Test Mode를 쓰는 세 갈래가 있습니다. 각각 덮는 범위가 다르고 **셋 다 덮지 못하는 영역이 남습니다** — 7.1절에서 정리합니다.

(참고로 **on-die ECC를 끄는 수단은 존재하지 않습니다.** `MR9`의 관련 비트는 ECC **핀**(`MD`)·심각도 신호·엔진 테스트 모드를 제어할 뿐이며, 정정 자체를 비활성화하지 않습니다.)
:::

CEm과 UE는 필터 없이 항상 보고된다는 점도 함께 기억할 만합니다 — **다중 비트는 그 자체로 이상 신호**이기 때문입니다.

## 6. ECC Engine Test Mode

> HBM4 장치는 **on-die ECC 엔진만을** 시험하는 방법을 제공하며, **코어로의 오류 접근은 제공하지 않는다.** 오류 주입의 결과는 투명성 프로토콜에 따라 보고된다. — §6.9.6 (요약)

**엔진만 테스트하고 배열은 건드리지 않습니다.** 실제 셀에 오류를 심는 것이 아니라 ECC 로직에 오류 벡터를 넣어 반응을 봅니다.

| 설정 | 위치 | 값 |
|---|---|---|
| ECC Engine Test Mode | `MR9` OP2 | 0 = 정상(기본) / 1 = 테스트 모드 |
| Error Vector Patterns | `MR9` OP3 | 0 = **CW0** — 데이터 `1`이 오류 비트 / 1 = **CW1** — 데이터 `0`이 오류 비트 |

패턴 극성이 반대인 두 가지를 제공하는 것은 **stuck-at 양방향**을 모두 시험하기 위해서입니다.

## 🔬 검증 적용

:::note[이 절과 `hbm_dv` Ch11의 경계]
이 장이 다루는 것은 **규격이 규정한 관측 수단과 그 한계**입니다 — `SEV` 인코딩, `ERRTH` 필터, ECS 로그의 성질.

그 수단으로 **TB를 어떻게 구성하고 오류 주입 전략을 어떻게 세우는가**는 [`hbm_dv` Ch11 DFT·RAS](../../hbm_dv/11_dft_ras/)에서 다룹니다. 여기서는 "무엇이 관측 가능하고 무엇이 구조적으로 가려지는가"까지입니다.
:::

### 7.1 무엇이 깨질 수 있는가

RAS 검증의 근본 어려움은 **검증 대상이 오류를 숨기도록 설계되어 있다**는 점입니다. ECC는 정정하고, `ERRTH`는 필터하고, 로그는 읽으면 지워집니다. 셋 다 정상 동작이며 셋 다 검증을 어렵게 합니다.

| 조문 | 위반 형태 | 증상 | 잡히는 시점 |
|---|---|---|---|
| Table 68 — **`ERRTH` 이하의 `CEs`는 `NE`로 보고** | `NE`를 "오류 없음"으로 해석 | 정정이 실제로 일어났는데 환경이 못 봄 | **구조적으로 불가** |
| §6.9.2 — read 정정을 **배열에 되쓰지 않음** | 모델이 "고쳐졌다"고 예측 | 같은 주소 재read에서 예측 어긋남 | 반복 read 시나리오 |
| §6.9.1 — **오류는 ECS 중에만 기록** | 일반 read 정정을 로그에서 찾음 | 로그가 비어 "오류 없음"으로 결론 | 없음 |
| Table 67 — `SEV`는 **버스트 후반부만 유효** | 전 구간을 OR로 샘플링 | **항상 `NE`** | 즉시(잘못된 방향) |
| §6.9.4 — ECS는 **`RESET` 외에 되돌릴 수 없음** | 테스트 간 상태 이월 | 주소 카운터·로그가 누적 → **테스트 독립성 붕괴** | 산발적·순서 의존 |
| §6.9.4 — `MR9` OP[6:4] **순서·동결** | 순서 위반 또는 시작 후 변경 | "알 수 없는 동작" — 기대값 없음 | 없음 |
| §6.9.4 — ECS 전에 **배열이 기록되어 있어야** | 미기록 영역에 ECS | 체크비트가 무의미 | 없음 |
| `ECSRES`·`ECSLOG` — 로그 **self-clearing** | monitor와 checker가 각각 읽음 | 둘 중 하나가 빈 로그를 봄 | 산발적 |
| §6.9.2 — `MD` off 구간에 쓴 MD는 **무효** | 모델이 유효로 처리 | MD 비교 실패 | MD 토글 시나리오 |
| §6.9.6 — ECC Test Mode는 **배열 미접근** | 실제 셀 오류로 오해 | 배열 내용 기대값이 어긋남 | 즉시 |

:::caution[`NE`는 "오류 없음"이 아니다]
Table 68의 필터가 검증에 만드는 구멍이 이 장의 핵심입니다.

```
실제 on-die ECC 판정      SEV 핀에 실리는 값
─────────────────────────────────────────
NE                    →   NE
CEs, ERRCNT ≤ ERRTH   →   NE      ← 여기
CEs, ERRCNT > ERRTH   →   CEs
CEm                   →   CEm
UE                    →   UE
```

단일 비트 정정이 실제로 일어났는데도 누적 카운트가 `ERRTH` 이하면 **`NE`로 나갑니다.** 그리고 `ERRTH`는 **벤더 지정값**이라 그 아래 구간은 환경이 **원리적으로 관측할 수 없습니다.**

곧 다음 문장이 성립하지 않습니다 — *"`SEV`가 전부 `NE`였으니 오류가 없었다."*

이 구멍을 우회하는 세 방법이 있고, 각각 덮는 범위가 다릅니다.

| 방법 | 덮는 것 | 못 덮는 것 |
|---|---|---|
| `ERRTH`를 넘을 만큼 **오류를 몰아 주입** | 임계값 초과 경로, `CEs` 보고 | 임계값 이하의 실제 동작 |
| **ECS 로그**(IEEE 1500)를 읽는다 | ECS가 정정한 모든 오류 | 일반 read의 정정 — 로그에 안 남는다 |
| **ECC Engine Test Mode**(§6.9.6) | ECC 엔진의 판정 로직 | 배열·셀 — 엔진만 시험한다 |

세 방법 어느 것도 "일반 read에서 `ERRTH` 이하로 일어난 정정"은 덮지 못합니다. **그것은 규격이 관측 수단을 주지 않은 영역**이며, V-Plan에 그렇게 적어야 합니다.
:::

:::caution[ECS는 테스트 사이에 상태를 이월한다]
§6.9.4의 두 조문이 회귀 구조를 건드립니다.

> ECS 동작이 시작되면 Auto ECS를 리셋하는 **유일한 방법은 장치 RESET**이다. 비활성화는 해당 모드의 동작만 중단시킬 뿐 **ECS 주소 카운터나 로그를 리셋하지 않는다.**

보통의 UVM 회귀는 테스트마다 환경을 새로 만들지만, **장치 상태는 그렇게 지워지지 않습니다.** ECS 주소 카운터가 어디까지 갔는지, 로그에 무엇이 쌓였는지가 **이전 테스트에 의존**합니다.

귀결이 둘입니다.

1. **ECS를 켜는 테스트는 device reset으로 시작해야 합니다.** 그렇지 않으면 결과가 실행 순서에 의존하고, 같은 시드가 회귀 위치에 따라 다르게 동작합니다.
2. **`MR9` OP[6:4]는 첫 ECS 이후 바꿀 수 없으므로**, 한 테스트 안에서 ECS 설정을 바꿔 가며 시험할 수 없습니다. 설정 조합마다 **별도 테스트**가 필요합니다.

그리고 전제가 하나 더 있습니다 — *"DRAM은 ECS 실행 전에 배열 비트가 기록된 경우에만 유효한 ECS 동작을 보장한다"*. 초기화 직후 곧바로 ECS를 켜면 미기록 영역의 체크비트가 무의미합니다. **메모리 전체를 채우는 write가 ECS 활성화보다 앞서야** 합니다.
:::

### 7.2 어떻게 잡는가 — 수단 선택

| 규칙 | 성격 | 수단 | 이유 |
|---|---|---|---|
| `SEV` 인코딩 해석 | **위치 의존 디코드** | **monitor** | 버스트 위치를 추적해야 한다 |
| 오류 누적 (되쓰지 않음) | **상태** | **reference model의 셀 오류 맵** | 주소별로 오류가 쌓인다 |
| ECS 설정 순서·동결 | **절차** | **프로토콜 checker** | MRS 순서에 대한 규칙 |
| 두 관측 경로의 통합 | **수집** | **단일 소유자 collector** | 로그가 self-clearing 이다 |

**① `SEV` 디코더 — 후반부만 본다**

```systemverilog
// Table 67 — 버스트 위치 0~3 은 항상 0, 4~7 에 {SEV[1],SEV[0]} 2비트 코드가 실린다.
// 전 구간을 OR 로 샘플링하면 항상 NE 가 나온다.
function automatic sev_e decode_sev(input bit [1:0] sev_by_ui[8]);
  bit [1:0] code = sev_by_ui[4];          // 후반부. 4~7 은 같은 값을 반복한다.
  unique case (code)
    2'b00 : return SEV_NE;
    2'b01 : return SEV_CES;               // {SEV[1],SEV[0]} = 0,1
    2'b11 : return SEV_CEM;
    2'b10 : return SEV_UE;
  endcase
endfunction

// 전반부가 0 이 아니면 규격 위반이거나 샘플링이 어긋난 것이다 — 둘 다 알아야 한다
a_sev_first_half_zero: assert property (@(posedge rdqs) disable iff (!rst_n)
    (burst_pos inside {[0:3]}) |-> (sev == 2'b00))
  else `uvm_error("SEV", $sformatf(
       "버스트 위치 %0d 에서 SEV=%b. 전반부는 0 이어야 한다 (Table 67)", burst_pos, sev))
```

**② 오류 누적 모델 — 정정은 반환값에만 반영된다**

```systemverilog
class ecc_array_model extends uvm_object;
  `uvm_object_utils(ecc_array_model)
  // 주소별 주입된 셀 오류. read 정정은 이것을 지우지 않는다 (§6.9.2).
  protected int m_cell_errors[bit [39:0]];

  function bit [255:0] on_read(bit [39:0] a, output sev_e sev);
    int n = m_cell_errors.exists(a) ? m_cell_errors[a] : 0;
    // symbol 경계 안의 단일 symbol 이하 오류는 정정된다
    sev = (n == 0) ? SEV_NE : (n == 1) ? SEV_CES : (n <= SYMBOL_LIMIT) ? SEV_CEM : SEV_UE;
    // ★ 여기서 m_cell_errors[a] 를 지우지 않는다. read 는 배열을 고치지 않는다.
    return corrected_data(a);
  endfunction

  // ECS 만이 배열을 실제로 복원한다 (§6.9.4)
  function void on_ecs(bit [39:0] a);
    if (m_cell_errors.exists(a) && m_cell_errors[a] <= SYMBOL_LIMIT)
      m_cell_errors.delete(a);            // 정정 결과가 배열에 되쓰인다
  endfunction

  // Table 68 — ERRTH 필터. 모델의 판정과 핀에 나가는 값이 다르다.
  function sev_e to_pin(sev_e actual, int errcnt, int errth);
    if (actual == SEV_CES && errcnt <= errth) return SEV_NE;   // 가려진다
    return actual;
  endfunction
endclass
```

`on_read()` 가 `m_cell_errors` 를 **지우지 않는 것**이 이 모델의 계약입니다. 지우면 두 번째 read에서 `NE`를 예측하는데 실제 장치는 또 정정합니다. 그리고 `to_pin()` 이 **모델의 실제 판정과 핀에 보이는 값을 분리**합니다 — 이 분리가 없으면 `ERRTH` 필터를 표현할 수 없습니다.

**③ 두 경로를 한 소유자가 수집한다**

로그가 self-clearing이므로, **읽는 주체가 둘이면 하나는 빈 값을 봅니다.**

```systemverilog
// ECS 로그는 읽으면 지워질 수 있다 (ECSLOG / ECSRES).
// 반드시 한 컴포넌트만 읽고, 나머지는 그 결과를 구독한다.
class ras_collector extends uvm_component;
  `uvm_component_utils(ras_collector)
  uvm_analysis_port #(ras_event_s) ap;

  // 실시간 경로 — read 마다, 휘발성 (§6.9.5)
  function void on_sev(hbm4_addr_t a, sev_e s);
    ap.write('{src: SRC_SEV_PIN, addr: a, sev: s});
  endfunction

  // 기록 경로 — ECS 중에만, 영속 (§6.9.4). 이 태스크만 로그를 읽는다.
  task read_ecs_log();
    ecs_log_entry_s e[];
    ieee1500_read(ECS_ERROR_LOG, e);      // 읽는 순간 지워질 수 있다
    foreach (e[i]) ap.write('{src: SRC_ECS_LOG, addr: e[i].addr, sev: e[i].sev});
  endtask
endclass
```

**④ ECS 설정 순서 checker**

```systemverilog
// §6.9.4 — ECSCEM(OP6) 은 ECSREF/ECSSRF(OP[5:4]) 보다 먼저 또는 동시에.
// 첫 ECS 동작 이후에는 변경 금지.
function void on_mr9_write(bit [7:0] val);
  bit cem = val[6], ref_en = val[5] | val[4];

  if (ref_en && !m_cem_programmed && cem == 1'b0)
    `uvm_error("ECS_ORDER",
      "ECSREF/ECSSRF 를 켜기 전에 ECSCEM 이 프로그램되지 않았다 (§6.9.4)")
  if (m_ecs_started && (cem != m_cem_value))
    `uvm_error("ECS_ORDER",
      "첫 ECS 동작 이후 ECSCEM 을 변경했다. 후속 동작이 미정의가 된다 (§6.9.4)")
  m_cem_programmed = 1'b1; m_cem_value = cem;
endfunction
```

### 7.3 무엇을 덮었다고 말할 수 있는가

```systemverilog
covergroup cg_hbm4_ras with function sample(
    sev_e actual, sev_e on_pin, errth_zone_e zone, ecs_mode_e ecs,
    bit ecscem, bit md_en, ecc_tm_e tm, int reread_count);
  option.per_instance = 1;

  // --- 심각도 네 갈래 (Table 67) ------------------------------------------
  // 모델의 실제 판정과 핀에 나온 값을 따로 센다. 둘이 갈리는 지점이 ERRTH 필터다.
  cp_actual : coverpoint actual { bins ne = {SEV_NE}; bins ces = {SEV_CES};
                                  bins cem = {SEV_CEM}; bins ue = {SEV_UE}; }
  cp_on_pin : coverpoint on_pin { bins ne = {SEV_NE}; bins ces = {SEV_CES};
                                  bins cem = {SEV_CEM}; bins ue = {SEV_UE}; }

  // --- ERRTH 필터 (Table 68) — 이 장의 중심 축 ---------------------------
  cp_errth : coverpoint zone {
    bins below = {ERRTH_BELOW};      // CEs 가 NE 로 가려지는 구간
    bins at    = {ERRTH_AT};         // 경계
    bins above = {ERRTH_ABOVE};      // CEs 가 실제로 보고되는 구간
  }
  // "정정이 일어났는데 핀에는 NE" 조합을 실제로 만들어 봤는가
  x_masked_ces : cross cp_actual, cp_on_pin {
    bins masked = binsof(cp_actual.ces) && binsof(cp_on_pin.ne);   // 가려진 경우
    bins visible = binsof(cp_actual.ces) && binsof(cp_on_pin.ces); // 보이는 경우
    ignore_bins rest = binsof(cp_actual.ne) || binsof(cp_actual.cem)
                    || binsof(cp_actual.ue);
  }

  // --- read 정정이 배열을 고치지 않음 (§6.9.2) ---------------------------
  // 같은 주소를 몇 번 다시 읽었는가 — 1 회면 누적 성질이 미검증이다
  cp_reread : coverpoint reread_count { bins once = {1}; bins twice = {2};
                                        bins many = {[3:$]}; }

  // --- ECS 모드와 설정 (§6.9.4) ------------------------------------------
  cp_ecs : coverpoint ecs {
    bins off       = {ECS_OFF};
    bins via_refab = {ECS_REFAB};    // MR9 OP4
    bins via_sref  = {ECS_SREF};     // MR9 OP5
    bins both      = {ECS_BOTH};
  }
  cp_ecscem : coverpoint ecscem { bins off = {0}; bins on = {1}; }
  x_ecs_cem : cross cp_ecs, cp_ecscem { ignore_bins no_ecs = binsof(cp_ecs.off); }

  // --- ECC Engine Test Mode (§6.9.6) -------------------------------------
  cp_tm : coverpoint tm {
    bins normal = {ECC_TM_OFF};
    bins cw0    = {ECC_TM_CW0};      // 데이터 1 이 오류 비트
    bins cw1    = {ECC_TM_CW1};      // 데이터 0 이 오류 비트 — stuck-at 양방향
  }

  // --- MD 토글 (§6.9.2) ---------------------------------------------------
  cp_md : coverpoint md_en { bins off = {0}; bins on = {1}; }
endgroup
```

세 축이 이 장의 목표입니다.

- **`x_masked_ces.masked`** — 정정이 일어났는데 핀에는 `NE`로 나오는 조합. 이 bin이 비면 `ERRTH` 필터의 존재 자체가 미검증입니다. 그리고 이 bin이 **차 있다는 것**은 환경이 "실제 판정"과 "핀 값"을 따로 알고 있다는 뜻이기도 합니다 — 그 분리가 없으면 애초에 샘플할 수 없습니다.
- **`cp_reread.twice` 이상** — 같은 주소를 두 번 이상 읽어야 §6.9.2의 "되쓰지 않는다"가 검증됩니다. 한 번만 읽는 자극은 되쓰는 모델과 안 되쓰는 모델을 구분하지 못합니다.
- **`cp_tm.cw0`와 `cw1`** — 극성이 반대인 두 패턴을 모두 돌려야 stuck-at 양방향이 시험됩니다.

### 7.4 어떻게 자극하는가

**① 같은 주소를 반복해서 읽는다** — §6.9.2를 검증하는 유일한 방법입니다.

```systemverilog
// 오류를 하나 심고 같은 주소를 여러 번 읽는다.
// 매번 정정된 값이 나오되, SEV 는 매번 오류를 보고해야 한다 (배열이 안 고쳐지므로).
class seq_read_no_writeback extends uvm_sequence #(hbm4_cmd_item);
  `uvm_object_utils(seq_read_no_writeback)
  virtual task body();
    inject_cell_error(TARGET_ADDR, .n_bits(1));
    repeat (4) begin
      `uvm_do_with(req, { cmd == RD; addr == TARGET_ADDR; })
      // 4 회 모두 동일한 심각도가 나와야 한다. 회를 거듭하며 NE 로 바뀌면
      // 장치가 되쓰기를 하고 있거나 모델이 오류를 지운 것이다.
    end
    // ECS 를 한 번 돌린 뒤 다시 읽으면 이번엔 NE 여야 한다
    trigger_ecs(TARGET_ADDR);
    `uvm_do_with(req, { cmd == RD; addr == TARGET_ADDR; })
  endtask
endclass
```

마지막 두 read의 **차이**가 검사 지점입니다 — ECS 전에는 오류가 보고되고 후에는 안 되어야 합니다. 이 대비가 없으면 ECS가 실제로 배열을 고쳤는지 확인할 방법이 없습니다.

**② `ERRTH`를 넘긴다** — `x_masked_ces` 두 bin을 모두 채웁니다.

`ERRTH`는 벤더 지정값이라 환경이 **`DEVICE_ID` 또는 벤더 프로파일에서 받아야** 합니다([06장](../06_row_commands/)의 RAA 문턱과 같은 구조입니다). 그 값을 모르면 "몇 개를 주입해야 넘는지" 알 수 없습니다.

```
① ERRTH 이하로 주입 → SEV 는 NE 여야 한다 (가려짐 확인)
② ECS 로그를 읽는다  → 로그에는 남아 있어야 한다 (두 경로의 차이 확인)
③ ERRTH 초과로 주입 → SEV 가 CEs 로 바뀌어야 한다
```

②가 핵심입니다. **핀은 `NE`인데 로그에는 있는 상태**가 두 관측 경로가 독립임을 증명합니다.

**③ ECS 설정 조합은 테스트를 나눈다** — `MR9` OP[6:4]는 첫 ECS 이후 변경 불가이므로, 한 테스트에서 조합을 순회할 수 없습니다. `cp_ecs` × `cp_ecscem` 조합마다 **device reset으로 시작하는 별도 테스트**를 둡니다.

그리고 각 테스트는 **메모리를 채우는 write를 먼저** 수행해야 합니다 — 미기록 영역에 ECS를 돌리면 §6.9.4의 전제가 깨집니다.

**④ ECC Engine Test Mode** — `CW0`/`CW1` 두 극성을 모두 돌립니다. 이 모드는 **배열에 접근하지 않으므로**, 테스트 전후로 배열 내용이 변하지 않는 것도 함께 확인합니다. 배열이 바뀌었다면 모드 해석이 틀린 것입니다.

**⑤ ECS 로그 self-clearing 확인** — 로그를 **연속 두 번** 읽습니다. `ECSLOG`가 활성이면 두 번째는 비어야 합니다. 이 성질을 모르는 환경은 monitor와 checker가 각각 읽어 한쪽이 조용히 빈 값을 보게 됩니다.

## 7. 대표 문제 — dry-run

### 문제 1 — Codeword 구성

> PC당 데이터워드가 272비트인 근거를 핀 수와 버스트 길이로 유도하라. 그리고 "최소 304b codeword"와의 관계는?

<details>
<summary>풀이</summary>

```
사용자 데이터 : 32 DQ 핀 × BL8 = 256 b
메타데이터 MD :  2 ECC 핀 × BL8 =  16 b
────────────────────────────────────────
데이터워드                        272 b
```

PC당 DQ가 32개인 것은 [01장](../01_landscape_organization/)의 *"PC 모드에서 32 DQ"*, ECC 핀이 2개인 것은 *"32 DQ당 ECC 2개"* 에서 나온다.

체크비트는 **구현 의존**이지만 규격이 예시로 든 값(**16b 단일 symbol 정정 가정 시 32b**)을 더하면:

```
272 b + 32 b = 304 b   ← "최소 304b codeword"와 일치 ✅
```

**"최소"인 이유**: symbol 크기와 정정 능력을 더 크게 잡으면 체크비트가 늘어 codeword도 커진다. 규격은 하한만 정하고 나머지는 벤더에 열어 두었다.
</details>

### 문제 2 — read 정정과 오류 누적

> 어떤 codeword에 단일 비트 오류가 있다. 호스트가 그 주소를 1000번 읽었다. 배열의 상태는 어떻게 되는가?

<details>
<summary>풀이</summary>

**1000번 모두 정정된 올바른 데이터를 받지만, 배열의 오류는 그대로 남아 있다.**

§6.9.2는 *"DRAM은 read 사이클 동안 정정된 데이터를 배열에 되쓰지 않는다"* 고 규정한다. read는 정정 결과를 **출력에만** 반영한다.

**위험**: 그 codeword에 **두 번째 오류**가 발생하면 정정 능력을 초과해 **UE**가 된다. 첫 오류를 방치한 만큼 UE 확률이 누적된다.

**해소 경로는 ECS 뿐이다.** Auto ECS의 read-modify-write만이 정정 결과를 배열에 되쓴다.

**검증 결론**: ECS 전후로 같은 주소를 읽어 **심각도가 달라지는지**가 검사 지점이다. ECS 전에는 오류가 보고되고 후에는 `NE` 여야 한다. 이 대비가 없으면 ECS가 실제로 배열을 복원했는지 확인할 방법이 없다(7.4 ①).
</details>

### 문제 3 — `SEV`의 NE 해석

> 데이터 경로 결함을 주입하는 테스트를 돌렸다. 모든 read에서 `SEV`가 NE를 반환했다. 결함이 없다고 결론지어도 되는가?

<details>
<summary>풀이</summary>

**안 된다.** 두 겹으로 가려질 수 있다.

**겹 1 — ECC 정정**: 주입한 결함이 단일 symbol 안에 들어가면 on-die ECC가 정정해 **올바른 데이터가 반환**된다. 데이터 비교로는 잡히지 않는다.

**겹 2 — `ERRTH` 필터**: 정정이 일어났더라도 누적 `ERRCNT`가 **`ERRTH` 이하이면 `SEV`에 CEs가 아니라 NE가 실린다**(Table 68). `ERRTH`는 **벤더 지정값**이라 그 아래 구간은 관측 자체가 되지 않는다.

즉 **"NE"는 "오류 없음"이 아니라 "보고 임계 미만"** 일 수 있다.

**올바른 대응** 세 가지:
1. 기능 검증 시 **ECC를 비활성화**하거나 `ECC Engine Test Mode`(`MR9` OP2)를 사용
2. **ECS 로그를 IEEE 1500으로 읽어** 정정 발생 자체를 확인
3. **`ERRTH`를 넘길 만큼** 오류를 주입해 CEs가 실제로 나타나게 함

**참고**: CEm과 UE는 필터를 거치지 않으므로 다중 비트 결함은 임계값과 무관하게 보고된다.
</details>

## 핵심 정리

- codeword는 **256b 데이터 + 16b MD = 272b 데이터워드**에 체크비트를 더해 **최소 304b**다. **H-matrix·symbol 크기·codeword 개수는 구현 의존**이다.
- ⚠️ **read는 정정해서 반환하지만 배열에 되쓰지 않는다.** 그래서 **오류가 누적**되고, 이를 막는 유일한 수단이 **ECS**다. 모델의 셀 오류 맵도 read에서 지우면 안 되며, **같은 주소를 두 번 이상 읽는 자극**이 없으면 이 성질은 미검증이다.
- **UE는 되쓰지 않는다** — 잘못 정정한 값을 심으면 원본이 영구히 사라지기 때문이다.
- **결함 격리는 물리 설계 요구사항**이다. 흔한 다중 비트 결함이 **한 symbol 안에 갇히도록** 배열을 배치해야 한다.
- **오류는 ECS 중에만 기록된다.** 일반 read의 정정은 **`SEV`로 실시간 통보될 뿐 로그에 남지 않는다.** 관측 경로가 **둘**이며 둘 다 필요하다.
- ECS 설정은 **초기화 중**에, **`ECSCEM`을 먼저 또는 동시에**, 첫 ECS 이후 **변경 금지**. 시작되면 **장치 RESET 외에는 되돌릴 수 없다** — 곧 ECS 상태가 **테스트 사이에 이월**된다. ECS 테스트는 device reset으로 시작해야 하고, 설정 조합마다 **별도 테스트**가 필요하다.
- ECS 전에 **배열이 기록되어 있어야** 유효한 체크비트가 생긴다 — 메모리 초기화가 ECS 활성화보다 앞서야 한다.
- `SEV`는 BL8의 **후반부(위치 4~7)** 에만 유효한 2비트 코드를 싣는다. 전반부를 함께 샘플링하면 항상 NE가 나온다.
- ⚠️ **`ERRTH` 이하의 CEs는 `SEV`에 NE로 보고된다.** **"NE ≠ 오류 없음"** 이다. `ERRTH`가 벤더 지정값이라 **그 아래 구간은 원리적으로 관측 불가**이며, V-Plan에 그렇게 적어야 한다. 모델은 **실제 판정과 핀 값을 분리**해 들어야 그 차이를 표현할 수 있다.
- ECS 로그는 **읽으면 지워질 수 있다**(`ECSLOG`/`ECSRES`). 읽는 주체가 둘이면 하나는 빈 값을 본다 — **단일 소유자**가 읽고 나머지는 구독한다.
- ECC Engine Test Mode는 **엔진만** 시험하며 코어에 오류를 심지 않는다. 벡터 극성이 **CW0/CW1 두 가지**다.

## Further Reading

- **규격**: JESD270-4 §6.9.1 Overview (Figure 77) · §6.9.2 Requirements · §6.9.3 Fault Isolation · §6.9.4 ECS (Table 62–63, Figure 78–80) · §6.9.5 Transparency (Table 66–68, Figure 81) · §6.9.6 ECC Engine Test Mode (Table 69, Figure 82–83)
- **다음 장**: [10 — 테스트와 복구](../10_test_repair/)
- **관련**: [04 — Mode Register](../04_mode_registers/) (`MR9`) · [08 — Parity](../08_parity/) (`SEV` 제외 이유) · [11 — 트레이닝과 IEEE 1500](../11_training_ieee1500/) (ECS 로그 읽기)
- **이해도 점검**: [퀴즈](../quiz/09_ecc_ecs_sev_quiz/)
