---
title: "N03 — Arm ADI(DAP) & CoreSight"
---

:::tip[학습 목표]
이 모듈을 마치면:

- **Explain** DAP가 DP와 AP로 나뉘는 이유와 각각의 책임을 설명할 수 있다.
- **Differentiate** JTAG-DP / SW-DP / SWJ-DP, MEM-AP(AHB/AXI/APB) / JTAG-AP, ADIv5 / ADIv6의 차이를 구분할 수 있다.
- **Apply** SELECT → CSW → TAR → DRW 레지스터 시퀀스로 MEM-AP가 시스템 버스 트랜잭션을 일으키는 흐름을 구성할 수 있다.
- **Trace** ROM table을 walk해 CoreSight 컴포넌트를 발견하고, trace source→link→sink 경로를 추적할 수 있다.
- **Evaluate** DBGEN/NIDEN/SPIDEN/SPNIDEN 인증 신호가 어떤 디버그를 허용/차단하는지 판단할 수 있다.
:::
:::note[사전 지식]
- [N01 — 왜 DFD인가](../01_why_dfd/), [N02 — JTAG & Boundary Scan](../02_jtag_boundary_scan/)
- 메모리-맵 IO, 주소 디코딩
- AHB/AXI/APB 트랜잭션 기본 ([AMBA 코스](../../amba_protocols/))
:::
---

## 1. Why care? — 직렬 핀을 메모리-맵 버스로 바꾸는 다리

### 1.1 시나리오 — 디버거는 칩 구조를 모른다

디버거는 수많은 종류의 Arm SoC에 붙어야 합니다. 각 칩마다 코어가 몇 개고 trace 블록이 어디 있는지 디버거에 미리 박아 둘 수는 없습니다. 그렇다면 디버거는 어떻게 "이 칩에는 코어 4개, ETM 4개, ETR 1개가 있다"는 걸 알아낼까요?

답은 **표준화된 다리(DAP)** 와 **자기 기술 디렉터리(ROM table)** 입니다. ADI(Arm Debug Interface)는 디버거가 따르는 표준 프로토콜을 정의하고, 모든 Arm SoC는 그 프로토콜로 접근 가능한 DAP를 제공합니다. 디버거는 표준 DAP만 알면 되고, connect 시점에 ROM table을 읽어 그 칩의 구체적인 구성을 _런타임에 발견_합니다. JTAG([N02](../02_jtag_boundary_scan/))이 직렬 통로였다면, DAP는 그 통로를 메모리-맵 버스 접근으로 바꾸는 다리이고, CoreSight는 그 다리 너머의 실제 디버그/trace IP입니다.

### 1.2 ADI 버전

| 버전 | 특징 | 적용 |
|------|------|------|
| **ADIv5** | 32비트 AP 주소 공간, 널리 배포 | Cortex-M / Cortex-A / Cortex-R |
| **ADIv6** | 64비트 주소, 계층적 ROM table, 더 큰 시스템 | 최신·대규모 SoC |

ADIv6는 64비트 주소와 계층적 ROM table을 도입해 ADIv5보다 훨씬 큰 시스템을 표현합니다. SoC 통합 초기에 어느 버전을 쓸지 고정해야 합니다([N01 §7](../01_why_dfd/) 참고).

---

## 2. Intuition — 안내데스크와 엘리베이터, 그리고 한 장 그림

:::tip[💡 한 줄 비유]
**DAP** ≈ **건물 로비의 안내데스크(DP)와 엘리베이터(AP)**.<br>
**DP(Debug Port)** 는 현관(JTAG/SWD 핀)으로 들어온 손님을 맞는 안내데스크 — 물리 프로토콜을 처리하고 "어느 엘리베이터를 탈지(어느 AP)"를 정합니다. **AP(Access Port)**, 그중 **MEM-AP** 는 엘리베이터 — 누른 층 주소(TAR)로 시스템 버스 트랜잭션을 발행해 실제 사무실(CoreSight 레지스터/메모리)에 도착합니다.
:::

### 한 장 그림 — DP + AP로 본 DAP

```d2
direction: right

PINS: "JTAG / SWD 핀"
DP: "**DP (Debug Port)**\n물리 측 인터페이스\nJTAG-DP / SW-DP / SWJ-DP\nSELECT로 AP 지정"
APMEM: "**MEM-AP**\nCSW / TAR / DRW\n→ 버스 트랜잭션 발행"
APJTAG: "**JTAG-AP**\n내부 레거시 scan chain"
BUS: "**Debug Bus**\nAPB / AHB / AXI"
ROM: "**ROM table**\nMEM-AP base에 위치\n컴포넌트 디렉터리"
CS: "CoreSight 레지스터\n+ 시스템 메모리"

PINS -> DP
DP -> APMEM: "SELECT (AP 지정)"
DP -> APJTAG
APMEM -> BUS: "TAR/CSW/DRW"
BUS -> ROM: "base 주소"
BUS -> CS
```

### 왜 DP와 AP로 나누는가 — Design rationale

세 가지 요구의 교집합입니다.

1. **물리 프로토콜은 다양해도 시스템 접근은 하나여야 한다** → DP가 물리(JTAG/SWD)를 흡수하고, AP가 시스템 접근을 표준화합니다. SWD로 붙든 JTAG로 붙든 같은 AP를 씁니다.
2. **접근 대상이 여러 종류다** → 메모리-맵 접근은 MEM-AP, 내부 레거시 scan chain은 JTAG-AP. DP의 SELECT로 어느 AP를 쓸지 고릅니다.
3. **디버거가 칩 구성을 런타임에 알아야 한다** → MEM-AP base의 ROM table을 walk해 컴포넌트를 발견. 디버거에 칩별 정보를 박지 않습니다.

---

## 3. 작은 예 — MEM-AP로 CoreSight 레지스터에 32비트 쓰기

DAP의 핵심 동작인 "MEM-AP를 통한 시스템 버스 write"를 단계로 봅시다. Arm Debug Interface 사양의 typical access flow를 그대로 따릅니다.

### 단계별 다이어그램

```d2
direction: down

S1: "**① DP 선택**\n디버거가 JTAG/SWD로 DP에 접근"
S2: "**② SELECT write**\n어느 AP + 어느 AP 레지스터 뱅크\n(예: APB-AP)"
S3: "**③ CSW write**\nsize(워드/하프/바이트)\nauto-increment 설정"
S4: "**④ TAR write**\nTarget Address Register\n= 목표 CoreSight 레지스터 주소"
S5: "**⑤ DRW write**\nData Read/Write\n→ MEM-AP가 버스 트랜잭션 발행"
S6: "**⑥ 버스 트랜잭션**\nAPB/AHB/AXI write가\nCoreSight 레지스터에 도달"
S1 -> S2 -> S3 -> S4 -> S5 -> S6
```

### 단계별 의미

| Step | 레지스터 | 무엇을 | 왜 |
|------|---------|--------|-----|
| ① | — | DP 선택 | 물리 프로토콜 진입점 |
| ② | `SELECT` | AP와 레지스터 뱅크 지정 (예: MEM-AP=APB-AP) | 여러 AP 중 대상 선택 |
| ③ | `CSW` | 전송 size, auto-increment 속성 | 버스 트랜잭션 속성 결정 |
| ④ | `TAR` | 목표 주소 (CoreSight 레지스터 주소) | 어디에 접근할지 |
| ⑤ | `DRW` | 데이터 — 이 write가 버스 전송을 트리거 | 실제 전송 발생 |
| ⑥ | (버스) | APB/AHB/AXI 트랜잭션이 CoreSight에 도달 | 최종 효과 |

:::note[여기서 잡아야 할 핵심]
디버거가 한 일은 DAP 레지스터 몇 개에 값을 쓴 것뿐인데(②~⑤), 그 결과 MEM-AP가 _진짜 시스템 버스 트랜잭션_을 발행합니다(⑥). 이 ⑥의 트랜잭션이 곧 [AMBA 코스](../../amba_protocols/)의 APB/AHB/AXI 트랜잭션과 동일합니다. 대부분의 CoreSight 컴포넌트는 **APB-AP**를 통해 접근됩니다.
:::

#### DRW 접근이 버스 전송을 트리거하는 내부 핸드셰이크

"DRW write가 전송을 트리거"의 내부를 한 단계 더 풀면, MEM-AP는 _상태를 미리 래치해 두고 DRW가 도착하는 순간 버스 마스터로 변신_ 하는 구조입니다.

1. **TAR/CSW는 _래치_ 일 뿐 — 접근 시 버스로 안 나간다.** ③에서 CSW에 size/auto-increment 속성을, ④에서 TAR에 목표 주소를 write하면, 이 값들은 MEM-AP 내부 레지스터에 _보관_ 만 됩니다. 아직 시스템 버스에는 아무 일도 일어나지 않습니다(준비 단계).
2. **DRW 접근이 "발사 트리거"다.** ⑤에서 DRW에 write(또는 DRW read)가 도착하는 순간, MEM-AP가 보관해 둔 {주소=TAR, 속성=CSW, 데이터=DRW write값}을 조립해 _시스템 버스의 마스터로서_ 한 건의 트랜잭션을 발행합니다. write면 버스 write, read면 버스 read입니다.
3. **버스 핸드셰이크 완료까지 DP 응답을 보류.** 발행된 버스 트랜잭션이 AHB/AXI/APB 슬레이브로부터 완료 응답을 받을 때까지 MEM-AP는 busy 상태이고, DP는 디버거에게 WAIT/재시도를 돌려줍니다. 완료되면 (read의 경우) 슬레이브가 돌려준 데이터를 DRW 읽기로 회수할 수 있게 합니다.
4. **auto-increment.** CSW의 auto-increment가 켜져 있으면 트랜잭션 완료 후 TAR가 size만큼 자동 증가해, 다음 DRW 접근이 연속 주소로 나갑니다 — 메모리 블록을 매번 TAR를 다시 쓰지 않고 빠르게 덤프할 수 있습니다.

핵심: TAR/CSW는 "조준", DRW 접근이 "발사"입니다. 그래서 TAR만 써서는 버스 전송이 안 일어나고, DRW를 건드려야 MEM-AP가 마스터로서 트랜잭션을 냅니다.

---

## 4. 일반화 — DP/AP 종류, ROM table, CoreSight 생태계

### 4.1 DP 변종

| DP | 물리 | 설명 |
|----|------|------|
| **JTAG-DP** | JTAG TAP | DAP를 JTAG로 접근 |
| **SW-DP** | Serial Wire | DAP를 2핀 SWD로 접근 |
| **SWJ-DP** | JTAG ↔ SW 자동 선택 | 핀에서 두 프로토콜을 자동 전환 |

### 4.2 AP 종류

| AP | 접근 대상 |
|----|----------|
| **MEM-AP** (AHB-AP / AXI-AP / APB-AP) | 메모리-맵 접근. 대부분의 CoreSight는 APB-AP 경유 |
| **JTAG-AP** | SoC 내부의 레거시 JTAG scan chain |

### 4.3 ROM table — connect 시점의 발견

각 MEM-AP의 base 주소에는 ROM table이 놓입니다. ROM table은 그 칩에 존재하는 CoreSight 컴포넌트들의 _주소 목록 디렉터리_입니다. 디버거는 connect 시점에 base부터 ROM table을 읽어 내려가며(walk) 코어, trace source, trigger 블록의 주소를 발견합니다. ADIv6에서는 ROM table이 다른 ROM table을 가리키는 계층 구조를 가져 대규모 시스템을 표현합니다.

**엔트리는 어떻게 디코딩되는가.** ROM table을 "walk"한다는 것의 내부는 다음과 같습니다(아키텍처 수준 일반 형태, 정확한 비트 위치는 사양 확인 필요).

1. **각 엔트리 = base 대비 상대 오프셋 + present 비트.** ROM table은 워드 배열이고, 각 워드 하나가 컴포넌트 하나를 가리킵니다. 워드의 상위 비트들은 _이 ROM table base로부터의 부호 있는 상대 오프셋_ 을 담고, 하위에 **present(valid) 비트** 가 있습니다. present=1이면 "오프셋만큼 떨어진 곳에 컴포넌트가 있다", present=0이면 빈 슬롯입니다. 절대 주소가 아니라 상대 오프셋이라, 같은 ROM table을 어느 base에 배치해도 그대로 동작합니다(재배치 가능).
2. **엔트리 0이 끝 표시(terminator).** 오프셋 0(= 전부 0인 엔트리)을 만나면 그 ROM table의 목록이 끝났다는 신호입니다.
3. **컴포넌트 끝의 ID 레지스터로 종류 식별.** 발견한 각 컴포넌트의 자기 주소 영역 _맨 끝 고정 위치_ 에는 식별 레지스터들(CIDR — Component ID, PIDR — Peripheral/Part ID 계열)이 있습니다. 디버거는 CIDR의 고정 시그니처 패턴으로 "이게 CoreSight 컴포넌트가 맞는지, 또 다른 ROM table인지"를 먼저 확인하고, PIDR의 part number/designer 필드로 "ETM인지 ETR인지 CTI인지"를 판별합니다. ROM table 자신도 같은 ID 레지스터를 가져, 엔트리가 가리킨 곳이 _또 다른 ROM table_ 이면 거기로 내려가 재귀적으로 walk합니다(ADIv6 계층 구조).

### 4.4 CoreSight 컴포넌트 카테고리

CoreSight는 DAP 너머에서 실제로 디버그·trace를 수행하는 IP family입니다.

| 카테고리 | 컴포넌트 | 역할 |
|----------|----------|------|
| **Trace source** | ETM, PTM, ITM, STM, HTM | instruction/data/software/bus trace 스트림 생성 |
| **Trace link** | Funnel, Replicator | trace 스트림 병합 / 복제 |
| **Trace sink** | ETB, ETF, ETR, TPIU, TMC | on-chip 버퍼 / off-chip 내보내기 / 시스템 메모리로 |
| **Control** | CTI, CTM | cross-trigger: halt/restart/trigger를 코어·trace 간 라우팅 |
| **Access** | DAP, APB-AP, ROM table | 위 모든 것의 구성(configuration) 평면 |
| **Security** | 인증 인터페이스(DBGEN/NIDEN/SPIDEN/SPNIDEN) | invasive/non-invasive, secure/non-secure 디버그 게이팅 |

### 4.5 trace 데이터 경로 — source → link → sink

```d2
direction: right

SRC: "**Trace Source**\nETM (코어별 instruction trace)\nITM/STM (software trace)"
LINK: "**Trace Link**\nFunnel (병합)\nReplicator (복제)"
SINK_ON: "**On-chip Sink**\nETB/ETF (SRAM 버퍼)\nETR → 시스템 DRAM(AXI)"
SINK_OFF: "**Off-chip Sink**\nTPIU (병렬 trace port)\nHSSTP (고속 직렬)"

SRC -> LINK: "trace 스트림"
LINK -> SINK_ON
LINK -> SINK_OFF
```

trace 데이터는 source(ETM 등)에서 생성되어, link(Funnel/Replicator)로 병합·복제된 뒤, sink로 버퍼링되거나 off-chip으로 나갑니다. on-chip sink는 ETB/ETF(SRAM 버퍼)와 ETR(AXI 마스터로 시스템 DRAM에 trace를 씀)이고, off-chip은 TPIU(병렬 trace port)나 HSSTP(고속 직렬)입니다. **TMC**는 ETB/ETF/ETR 모드를 구성으로 선택할 수 있는 현대적 블록입니다.

### 4.6 cross-trigger — 멀티코어 동기 halt

여러 코어를 동시에 멈추거나, 한 코어가 멈출 때 trace를 시작시키려면 이벤트를 코어와 trace 블록 사이에 라우팅해야 합니다. 이것이 **CTI(Cross Trigger Interface)** 와 **CTM(Cross Trigger Matrix)** 의 역할입니다. CTI가 각 코어/trace 블록에 붙고, CTM이 CTI들을 연결해, "코어 0이 breakpoint에 걸리면 코어 1,2,3도 동시에 halt"처럼 멀티코어 동기 디버그를 가능하게 합니다.

---

## 5. 디테일 — 인증 신호와 SoC 통합 체크리스트

### 5.1 네 인증 신호

CoreSight는 디버그 동작을 네 신호로 게이팅합니다. 각 신호가 enable되어 있어야 해당 디버그가 동작합니다.

| 신호 | enable하는 디버그 |
|------|------------------|
| **DBGEN** | Non-secure invasive (halt, single-step) |
| **NIDEN** | Non-secure non-invasive (trace, PMU) |
| **SPIDEN** | Secure invasive |
| **SPNIDEN** | Secure non-invasive |

```d2
direction: down

SEC: "**보안 정책**\nfuse / lifecycle 상태" {
  D: "DBGEN → NS halt"
  N: "NIDEN → NS trace"
  SI: "SPIDEN → secure halt"
  SN: "SPNIDEN → secure trace"
}
```

이 신호들은 보통 secure 컨트롤러가 fuse나 lifecycle 상태에서 구동합니다. bring-up 단계에서는 대개 다 열려 있지만, 양산 칩에서는 보안 정책에 따라 일부(특히 SPIDEN)가 영구히 막힐 수 있습니다. DFD bring-up 시 이 신호들의 소스를 반드시 확인해야 합니다.

**신호가 디버그를 _게이팅하는 회로적 지점_.** "enable되어야 동작"의 내부는 단순합니다 — 인증 신호가 디버그 동작 경로의 **AND 게이트**(또는 동등한 qualifier)로 들어갑니다. 예를 들어 코어의 halt 요청 경로는 대략 `halt_effective = halt_request AND DBGEN` 형태라, 디버거가 halt를 요청해도 DBGEN=0이면 AND 출력이 0이 되어 _요청 자체가 무시_ 됩니다(코어는 멈추지 않음). trace enable도 마찬가지로 `trace_on = trace_enable_reg AND NIDEN` 식이라 NIDEN=0이면 ETM이 trace 스트림을 내보내지 못합니다. secure 측은 비밀 상태에 접근하는 동작에만 SPIDEN/SPNIDEN이 추가 AND로 끼어, secure 영역의 halt/trace를 따로 막습니다. 핵심: 이 신호들은 "구성 레지스터"가 아니라 디버그 경로에 _하드와이어된 qualifier_ 라, SW가 디버그 레지스터를 아무리 설정해도 신호가 0이면 그 동작은 회로 레벨에서 통과하지 못합니다. 그래서 검증에서는 "DBGEN=0인데 halt 요청 → 코어가 안 멈추는가"를 음성 케이스로 자극해야 합니다.

### 5.2 SoC 통합 체크리스트

DFD 통합 체크리스트입니다. 검증/통합 엔지니어가 새 SoC에서 점검해야 할 항목들입니다.

| 항목 | 확인 내용 |
|------|----------|
| 핀·전기 | JTAG/SWD 패드 pinout, pull-up, TRSTn 전략 정의 |
| DAP 버전 | ADIv5 vs ADIv6 선택, ROM table base 주소 고정 |
| ROM table | 모든 CoreSight 컴포넌트가 ROM table에 열거 → 디버거 probe로 검증 |
| 클럭·전원 | DBG clock, always-on 전원이 코어 power-gating과 독립인지 |
| 인증 | DBGEN/NIDEN/SPIDEN/SPNIDEN 소스(fuse/lifecycle)를 정책대로 |
| cross-trigger | CTI↔코어, CTI↔trace 토폴로지, CTM 연결 정의 |
| trace 대역 | on-chip 버퍼(ETB/ETF) 크기 또는 off-chip(TPIU/HSSTP/ETR→DRAM) 경로 |
| reset 격리 | warm/cold reset 넘어 디버그 접근 유지 |

### 5.3 검증 관점 — 무엇을 시뮬레이션에서 잡는가

DAP/CoreSight 서브시스템을 검증할 때 핵심 시나리오는 다음과 같습니다.

- **ROM table 열거 정합성**: ROM table을 walk해 발견한 컴포넌트가 RTL의 실제 인스턴스와 일치하는가.
- **MEM-AP 트랜잭션 정확성**: SELECT/CSW/TAR/DRW 시퀀스가 올바른 주소·size·auto-increment의 버스 트랜잭션을 만드는가([AMBA 코스](../../amba_protocols/)의 프로토콜 체크와 연결).
- **인증 게이팅**: DBGEN=0일 때 halt가 차단되고, NIDEN=1일 때 trace는 동작하는가.
- **reset isolation**: warm reset 후 디버그 세션·breakpoint가 유지되는가.

---

## 6. 흔한 오해 와 DV 디버그 체크리스트

### 흔한 오해

:::danger[❓ 오해 1 — 'DP와 AP는 같은 것이다']
**실제**: DP(Debug Port)는 _물리 측_(JTAG/SWD 프로토콜 처리, AP 선택), AP(Access Port)는 _시스템 측_(메모리-맵 접근 발행)입니다. 하나의 DP가 여러 AP를 거느리며, SELECT 레지스터로 어느 AP를 쓸지 고릅니다.<br>
**왜 헷갈리는가**: 둘 다 DAP의 부품이라 한 덩어리로 보여서.
:::
:::danger[❓ 오해 2 — 'TAR에 주소만 쓰면 바로 read/write가 일어난다']
**실제**: TAR는 _주소만_ 설정합니다. 실제 버스 전송은 `DRW`(데이터) 접근이 트리거합니다. write면 DRW write가, read면 DRW read가 버스 트랜잭션을 일으킵니다. SELECT(AP 선택)→CSW(속성)→TAR(주소)→DRW(전송) 순서가 핵심.<br>
**왜 헷갈리는가**: "Target Address"라는 이름이 주소 쓰면 끝날 것 같아서.
:::
:::danger[❓ 오해 3 — 'CoreSight 컴포넌트는 종류가 다 같다']
**실제**: source(생성: ETM/ITM/STM), link(병합/복제: Funnel/Replicator), sink(저장/내보내기: ETB/ETF/ETR/TPIU)는 trace 파이프라인의 _다른 단계_입니다. CTI/CTM은 trace가 아니라 cross-trigger(제어)입니다. 역할을 섞으면 trace 경로 구성이 틀립니다.<br>
**왜 헷갈리는가**: 약어가 많고 다 "trace 관련"이라 뭉뚱그려서.
:::
:::danger[❓ 오해 4 — 'ETR은 그냥 on-chip 버퍼다']
**실제**: ETR은 AXI 마스터로서 trace를 _시스템 DRAM_에 씁니다. on-chip SRAM 버퍼는 ETB이고, ETF는 FIFO link입니다. TMC는 이 세 모드를 구성으로 선택하는 블록입니다.<br>
**왜 헷갈리는가**: 셋 다 "trace 버퍼"로 묶여서.
:::

### DV 디버그 체크리스트

| 증상 | 1차 의심 | 어디 보나 |
|---|---|---|
| 디버거 connect 후 컴포넌트 미발견 | ROM table base 오류 또는 미열거 | DAP 버전, ROM table base, 컴포넌트 등록 |
| MEM-AP write가 효과 없음 | DRW 미접근(주소만 설정) 또는 CSW size 오류 | SELECT/CSW/TAR/DRW 순서, CSW size |
| 모든 AP 접근 실패 | DP가 잘못 선택됨 또는 SWJ 전환 실패 | DP 종류(JTAG/SW/SWJ), 물리 프로토콜 |
| halt만 안 되고 trace는 됨 | DBGEN=0, NIDEN=1 | 인증 신호 소스(fuse/lifecycle) |
| secure 코드 halt 불가 | SPIDEN 비활성 | secure 인증 신호 |
| 멀티코어 동기 halt 안 됨 | CTI↔CTM 토폴로지 미구성 | cross-trigger 연결 |
| trace가 off-chip으로 안 나옴 | TPIU/HSSTP 경로 미구성 또는 sink 모드 오류 | trace sink(TMC 모드), 대역 계획 |

---

## 7. 핵심 정리 (Key Takeaways)

- **DAP = DP + AP**. DP는 물리 측(JTAG/SWD 처리, SELECT로 AP 선택), AP는 시스템 측. MEM-AP가 메모리-맵 접근을 버스 트랜잭션으로 발행.
- **MEM-AP 접근 시퀀스**: SELECT(AP 선택) → CSW(size/auto-inc) → TAR(주소) → DRW(데이터, 전송 트리거). 대부분의 CoreSight는 APB-AP 경유.
- **ROM table**이 MEM-AP base에 있어, 디버거가 connect 시점에 walk해 컴포넌트를 런타임 발견. ADIv6는 계층적.
- **CoreSight 생태계**: source(ETM/ITM/STM) → link(Funnel/Replicator) → sink(ETB/ETF/ETR/TPIU). CTI/CTM은 cross-trigger(멀티코어 동기 halt).
- **ETB(SRAM) / ETF(FIFO) / ETR(AXI로 DRAM)** 구분, TMC가 세 모드 선택. off-chip은 TPIU/HSSTP.
- **네 인증 신호**: DBGEN/NIDEN/SPIDEN/SPNIDEN이 invasive/non-invasive × secure/non-secure 디버그를 게이팅. fuse/lifecycle에서 구동.

:::caution[실무 주의점]
- explicit하게 DRW를 접근해야 버스 전송이 일어난다 — TAR만 쓰면 주소만 설정될 뿐.
- ROM table base와 DAP 버전은 통합 초기에 고정.
- 양산 칩에서 인증 신호(특히 SPIDEN)는 막힐 수 있으니 bring-up 가정을 양산에 그대로 옮기지 말 것.
:::

### 7.1 자가 점검

:::tip[🤔 Q1 — 접근 시퀀스 구성 (Bloom: Apply)]
디버거가 `0x80001000`(어떤 CoreSight 레지스터)에 `0x1`을 쓰려 한다. MEM-AP 레지스터 접근 순서를 쓰고 각 단계의 의미를 설명하라.
<details>
<summary>정답</summary>

`SELECT` → `CSW` → `TAR` → `DRW` 순서입니다.
1. **SELECT**: 사용할 AP(예: APB-AP)와 AP 레지스터 뱅크를 지정.
2. **CSW**: 전송 size(32비트 워드)와 auto-increment 여부 설정.
3. **TAR**: `0x80001000`을 Target Address Register에 write — 어디에 접근할지.
4. **DRW**: `0x1`을 Data R/W에 write — _이 접근이_ MEM-AP에 APB write 버스 트랜잭션을 발행하게 함.
TAR만 쓰면 주소만 설정되고 전송은 일어나지 않습니다. DRW 접근이 트리거입니다.

</details>
:::
:::tip[🤔 Q2 — trace 경로 평가 (Bloom: Evaluate)]
"off-chip trace port(TPIU) 핀을 둘 여유가 없는데, 코어 4개의 instruction trace를 길게 수집하고 싶다." 어떤 CoreSight 구성이 적절한가?
<details>
<summary>정답</summary>

**ETR(또는 TMC를 ETR 모드)로 trace를 시스템 DRAM에 쓰는** 구성이 적절합니다. 4개 코어의 ETM(trace source)을 Funnel(link)로 병합한 뒤, sink를 off-chip TPIU 대신 ETR로 두면 ETR이 AXI 마스터로서 trace를 시스템 DRAM에 기록합니다. 이렇게 하면 off-chip trace 핀이 필요 없고, DRAM 용량만큼 길게 수집할 수 있습니다. 이후 디버거가 DAP(MEM-AP)로 DRAM의 trace 버퍼를 읽어 갑니다. 대역이 매우 높으면 HSSTP(고속 직렬)도 대안이지만 핀이 필요합니다.

</details>
:::
### 7.2 출처

**External**
- Arm IHI 0031 — Arm Debug Interface Architecture Specification (ADIv5 / ADIv6, DP/AP/MEM-AP)
- Arm IHI 0029 — CoreSight Architecture Specification
- Arm DDI 0480 — CoreSight SoC technical reference manuals

---

## 다음 모듈

이로써 DFD의 세 핵심 층(JTAG → DAP → CoreSight)을 모두 다뤘습니다. 용어를 다지고 이해도를 점검하세요.

→ [용어집 (Glossary)](../glossary/): DFD 핵심 용어 ISO 11179 형식 정의.

[퀴즈 풀어보기 →](../quiz/03_adi_dap_coresight_quiz/)
