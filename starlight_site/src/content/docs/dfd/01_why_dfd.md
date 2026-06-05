---
title: "N01 — 왜 DFD인가"
---

:::tip[학습 목표]
이 모듈을 마치면:

- **Explain** post-silicon에서 칩 내부 가시성이 왜 사라지는지, DFD가 그 문제를 어떻게 해결하는지 설명할 수 있다.
- **Trace** 외부 디버거에서 코어/메모리까지 신호가 흐르는 4계층 디버그 스택을 단계별로 추적할 수 있다.
- **Differentiate** invasive(halt/step)와 non-invasive(trace/PMU) 디버그, secure와 non-secure 디버그를 구분할 수 있다.
- **Evaluate** 어떤 디버그 동작이 가능/불가능한지를 인증 신호와 전원·클럭 도메인 격리 관점에서 판단할 수 있다.
:::
:::note[사전 지식]
- 동기 회로, 메모리-맵 IO의 기본 개념
- 멀티코어 SoC와 secure/non-secure 구분의 감각
- 버스 트랜잭션 1개의 구조 ([AMBA 코스](../../amba_protocols/) 참고)
:::
---

## 1. Why care? — 실리콘이 돌아왔는데 안이 안 보인다

### 1.1 시나리오 — bring-up 첫날, 칩이 부팅에서 멈췄다

새 SoC의 첫 실리콘이 도착했습니다. 보드에 올리고 전원을 넣었더니 부팅 로그가 어느 시점에서 멈추고 더 이상 진행되지 않습니다. RTL 시뮬레이션이었다면 파형을 열어 PC(program counter)가 어느 주소에서 무한 루프에 빠졌는지, 어느 핸드셰이크가 안 떨어졌는지 즉시 볼 수 있었을 겁니다. 그러나 실물 칩 안에서는 그 신호들이 외부 핀으로 나오지 않습니다.

이때 살아 있는 유일한 통로가 디버그 포트입니다. 디버거를 JTAG 핀에 연결하고 코어를 halt시킨 뒤, PC와 레지스터를 읽고, 시스템 메모리를 덤프하고, 한 명령씩 single-step으로 진행시켜 어디서 멈추는지 추적합니다. DFD(Design For Debug)는 이 모든 동작이 _칩 설계 단계에서 미리 심어 둔_ 인프라 위에서 동작하게 만드는 일입니다. 디버그 인프라를 설계에 넣지 않으면, 칩이 죽었을 때 진단할 방법이 아예 없습니다.

### 1.2 DFD가 책임지는 두 가지 능력

칩 내부 가시성은 두 가지 서로 다른 능력으로 나뉩니다. 이 구분이 이후 모든 인증/보안 논의의 뼈대가 됩니다.

| 능력 | 영어 | 무엇을 하는가 | 칩을 멈추는가 |
|------|------|--------------|:---:|
| **침습적 디버그** | invasive debug | 코어 halt, single-step, 레지스터/메모리 write, breakpoint | 멈춤 (실행에 개입) |
| **비침습적 디버그** | non-invasive debug | 실시간 trace 수집, 성능 카운터(PMU) 읽기 | 안 멈춤 (관찰만) |

침습적 디버그는 코어 실행에 직접 개입하므로 강력하지만, 동작 중인 시스템의 타이밍을 바꿔 버립니다. 비침습적 디버그는 실행을 건드리지 않고 trace만 뽑으므로 실시간 동작을 그대로 관찰할 수 있습니다. 이 둘이 분리되어 있기 때문에, 뒤에서 볼 인증 신호도 invasive용(DBGEN/SPIDEN)과 non-invasive용(NIDEN/SPNIDEN)으로 나뉩니다.

---

## 2. Intuition — 4층 빌딩, 그리고 한 장 그림

:::tip[💡 한 줄 비유]
**DFD 스택** ≈ **건물에 들어가는 4단계 출입 경로**.<br>
바깥 **현관문(JTAG 핀)** 으로 들어와, **로비의 안내데스크(DAP)** 가 어느 층으로 갈지 정해 주면, **엘리베이터(MEM-AP가 내는 버스)** 를 타고, 실제 사무실(**CoreSight 컴포넌트와 시스템 메모리**)에 도착합니다. 디버거는 사무실 주소(레지스터 주소)만 알면 되고, 어느 문·로비·엘리베이터를 거쳤는지는 각 층이 알아서 처리합니다.
:::

### 한 장 그림 — 외부 디버거에서 코어까지

```d2
direction: right

DBG: "**External Debugger**\n(host probe)\nGDB / DS-5 등"
PINS: "**JTAG / SWD 핀**\nTCK TMS TDI TDO\n(또는 SWCLK SWDIO)"
DAP: "**DAP (ADI)**\nDP + AP\n물리 ↔ 메모리-맵 변환"
BUS: "**Debug Bus**\nAPB / AHB / AXI\n(MEM-AP가 발행)"
CS: "**CoreSight**\nETM/CTI/ETB...\n+ 시스템 메모리"
CORE: "**Cores / System**\n관찰·제어 대상"

DBG -> PINS: "물리 프로토콜"
PINS -> DAP: "scan / SWD 패킷"
DAP -> BUS: "SELECT/CSW/TAR/DRW"
BUS -> CS: "버스 트랜잭션"
CS -> CORE: "halt / trace / PMU"
```

### 왜 이렇게 4층인가 — Design rationale

세 가지 요구의 교집합입니다.

1. **핀은 최소여야 한다** → 칩 핀은 비싸고 귀합니다. JTAG 4~5핀(또는 SWD 2핀)만으로 칩 전체 메모리 공간에 접근해야 하므로, 직렬 프로토콜(JTAG)을 메모리-맵 접근(DAP)으로 바꾸는 변환 계층이 필요합니다.
2. **디버거는 SoC 내부 구조를 몰라야 한다** → 디버거는 표준 ADI 프로토콜만 알고, 어떤 CoreSight 컴포넌트가 어디 있는지는 ROM table을 읽어 _런타임에_ 발견합니다. 그래서 한 디버거가 여러 칩을 지원합니다.
3. **보안과 분리해야 한다** → 양산 칩에서 디버그를 함부로 열면 보안 위협이 됩니다. 그래서 인증 신호(DBGEN 등)가 각 디버그 동작을 게이팅하는 층이 따로 있습니다.

---

## 3. 작은 예 — "코어를 멈추고 PC를 읽는다" 한 번이 4층을 통과하는 과정

가장 흔한 디버그 동작인 "코어 halt 후 PC 읽기"가 스택을 어떻게 통과하는지 단계로 봅시다.

### 단계별 다이어그램

```d2
direction: down

S1: "**① 디버거가 JTAG 핀 구동**\nTMS로 TAP FSM 이동\nIR에 DAP-access 명령 로드"
S2: "**② DP가 AP 선택**\nSELECT 레지스터 write\n→ APB-AP(또는 AHB/AXI-AP) 지정"
S3: "**③ MEM-AP가 버스 트랜잭션 발행**\nTAR=CTI/디버그 레지스터 주소\nCSW=size/auto-increment\nDRW=halt 요청 데이터"
S4: "**④ CoreSight CTI가 코어 halt**\n코어 실행 정지\n디버그 상태 진입"
S5: "**⑤ PC 읽기**\n같은 경로로 코어 디버그 레지스터 read\nTDO로 값이 직렬 출력"
S1 -> S2 -> S3 -> S4 -> S5
```

### 단계별 의미

| Step | 어느 층 | 무엇이 일어나는가 | 왜 |
|------|--------|------------------|-----|
| ① | JTAG | TMS가 TAP 16-state FSM을 이동시켜 IR에 DAP 접근 명령을 실음 | 직렬 핀만으로 칩 내부 통로를 열기 위해 |
| ② | DAP (DP) | `SELECT` write로 어느 AP, 어느 레지스터 뱅크를 쓸지 지정 | 여러 AP 중 메모리 접근용을 골라야 |
| ③ | DAP (MEM-AP) | `TAR`(주소) → `CSW`(전송 속성) → `DRW`(데이터)로 버스 전송 트리거 | 직렬 접근을 시스템 버스 트랜잭션으로 변환 |
| ④ | CoreSight | CTI(Cross Trigger Interface)가 halt 이벤트를 코어로 라우팅 | 코어 실행을 실제로 멈추기 위해 |
| ⑤ | 전 경로 역방향 | 코어 디버그 레지스터를 read → 값이 TDO로 직렬 출력 | 외부에서 PC 값을 회수 |

:::note[여기서 잡아야 할 핵심]
디버거가 보낸 것은 사실상 **직렬 비트 스트림**(JTAG)이지만, 그 결과는 칩 내부에서 **메모리-맵 버스 트랜잭션**(③)으로 바뀝니다. 이 변환을 하는 것이 DAP이고, 변환 _이후_의 세계가 바로 [AMBA 코스](../../amba_protocols/)에서 배운 APB/AHB/AXI 트랜잭션과 동일합니다.
:::

---

## 4. 일반화 — 디버그 스택의 세 층과 검증/보안/가상화 관점

### 4.1 세 핵심 층 요약

| 층 | 표준 | 책임 | 다음 모듈 |
|----|------|------|----------|
| **JTAG** | IEEE 1149.1 | 물리 접근 — 직렬 핀으로 칩 진입, 원래 boundary scan용 | [N02](../02_jtag_boundary_scan/) |
| **ADI / DAP** | Arm IHI 0031 | 아키텍처 다리 — 직렬을 메모리-맵 버스 접근으로 변환 | [N03](../03_adi_dap_coresight/) |
| **CoreSight** | Arm IHI 0029 | IP 생태계 — 코어 halt, cross-trigger, 실시간 trace | [N03](../03_adi_dap_coresight/) |

### 4.2 세 가지 관점 — 검증 / 보안 / 가상화

**검증(DV) 관점.** 디버그 서브시스템 자체가 검증 대상입니다. DAP가 ROM table을 통해 모든 CoreSight 컴포넌트를 올바로 노출하는가, MEM-AP의 SELECT/CSW/TAR/DRW 시퀀스가 정확한 버스 트랜잭션을 만드는가, warm/cold reset을 넘어 디버그 접근이 유지되는가를 시뮬레이션과 post-silicon에서 검증합니다.

**보안 관점.** 디버그 인프라는 칩 내부를 들여다보는 강력한 통로이므로, 양산 칩에서 함부로 열리면 보안 키나 펌웨어가 유출될 수 있습니다. 그래서 DBGEN/NIDEN/SPIDEN/SPNIDEN 네 인증 신호가 invasive/non-invasive × secure/non-secure 조합별로 디버그를 게이팅하며, 이 신호들은 보통 fuse나 lifecycle 상태에서 구동됩니다.

**가상화 관점.** 여러 게스트가 한 SoC를 공유하는 환경에서는 디버그 권한도 가상화 경계를 존중해야 합니다. 어떤 게스트의 디버그가 다른 게스트나 hypervisor의 상태를 볼 수 없어야 하며, secure world(예: TrustZone)의 디버그는 SPIDEN/SPNIDEN으로 따로 게이팅됩니다 (추론: HDG는 secure/non-secure 게이팅을 명시하나 가상화별 격리 메커니즘 세부는 명시하지 않음).

### 4.3 디버그 동작과 필요한 인증

```d2
direction: right

INV: "**Invasive**\n(halt/step/breakpoint)" {
  NS_I: "DBGEN\n→ non-secure halt"
  S_I: "SPIDEN\n→ secure halt"
}
NONINV: "**Non-invasive**\n(trace/PMU)" {
  NS_N: "NIDEN\n→ non-secure trace"
  S_N: "SPNIDEN\n→ secure trace"
}
```

각 디버그 동작은 그에 맞는 인증 신호가 _enable_되어 있어야만 동작합니다. 예를 들어 secure world의 코드를 halt하려면 SPIDEN이 켜져 있어야 하고, 이 신호가 fuse로 영구히 막혀 있으면 양산 칩에서는 secure halt가 원천 불가능합니다.

---

## 5. 디테일 — 왜 디버그 로직은 따로 살아야 하는가

### 5.1 전원·클럭 도메인 격리

디버그가 가장 필요한 순간은 시스템이 비정상일 때입니다. 코어가 전원 게이팅으로 꺼져 있거나, 시스템 클럭이 멈췄거나, warm reset이 걸린 직후 같은 상황입니다. 만약 디버그 로직이 코어 전원/클럭에 종속되어 있다면, 정작 문제가 생긴 순간 디버그 통로도 같이 죽어 버립니다.

그래서 디버그 서브시스템은 보통 **독립적인 디버그 클럭(DBG clock)** 과 **always-on 전원 도메인**에 둡니다. 이렇게 해야 코어가 power-gating으로 꺼져 있어도 디버거가 DAP에 붙어 코어를 깨우거나 상태를 읽을 수 있습니다.

| 항목 | 이유 |
|------|------|
| 독립 DBG clock | 코어 클럭이 멈춰도 디버그 접근 유지 |
| always-on 전원 | 코어 power-gating 중에도 DAP 살아 있음 |
| reset isolation | warm/cold reset을 넘어 디버그 세션 유지 가능 |

### 5.2 reset isolation

칩을 디버그하다 보면 시스템을 reset해야 할 때가 많습니다. 그런데 reset이 디버그 로직까지 초기화해 버리면, reset 직후의 부팅 동작을 관찰할 수 없습니다. 그래서 디버그 로직은 일반 reset과 분리된 reset 도메인을 가져, warm/cold reset이 걸려도 디버그 세션과 breakpoint 설정이 유지되도록 설계합니다.

### 5.3 ROM table — 런타임 컴포넌트 발견

디버거가 칩에 처음 붙으면, 그 칩에 어떤 CoreSight 컴포넌트가 몇 개 있는지 모릅니다. ADI는 이를 위해 각 MEM-AP의 베이스 주소에 **ROM table**을 두도록 정의합니다. ROM table은 칩 안 CoreSight 컴포넌트들의 _주소 목록 디렉터리_입니다. 디버거는 connect 시점에 ROM table을 walk해서 코어, trace source, trigger 블록을 _발견_합니다. ADIv6에서는 이 ROM table이 계층 구조를 가질 수 있어 더 큰 시스템을 표현합니다.

---

## 6. 흔한 오해 와 DV 디버그 체크리스트

### 흔한 오해

:::danger[❓ 오해 1 — 'JTAG은 boundary scan 전용이다']
**실제**: JTAG(IEEE 1149.1)은 원래 boundary scan(핀 연결 테스트)용으로 정의됐지만, 현대 SoC에서는 _DAP 접근 통로로 재사용_됩니다. 같은 4~5핀이 boundary scan과 디버그 양쪽에 쓰입니다.<br>
**왜 헷갈리는가**: 표준 이름이 "Test Access Port and Boundary-Scan Architecture"라서 boundary scan만 떠올리기 쉬워서.
:::
:::danger[❓ 오해 2 — '디버거를 붙이면 항상 코어를 멈출 수 있다']
**실제**: 코어 halt(invasive)는 `DBGEN`(non-secure) 또는 `SPIDEN`(secure)이 enable되어 있어야만 가능합니다. 양산 칩에서 이 신호가 fuse로 막혀 있으면 디버거가 물리적으로 붙어도 코어를 멈출 수 없습니다.<br>
**왜 헷갈리는가**: bring-up 보드에서는 보통 인증이 다 열려 있어 "항상 된다"고 착각하기 쉬워서.
:::
:::danger[❓ 오해 3 — 'invasive와 non-invasive 권한은 하나다']
**실제**: 둘은 분리됩니다. trace/PMU(non-invasive)는 `NIDEN`/`SPNIDEN`으로, halt/step(invasive)은 `DBGEN`/`SPIDEN`으로 따로 게이팅됩니다. 실시간 trace는 허용하되 실행 개입은 막는 정책이 가능합니다.<br>
**왜 헷갈리는가**: 둘 다 "디버그"라는 한 단어로 묶이기 때문에.
:::
:::danger[❓ 오해 4 — '디버그 로직은 코어 전원/클럭에 묶여 있다']
**실제**: 정반대입니다. 디버그가 필요한 순간(코어 정지/전원 게이팅)에도 살아 있어야 하므로, 보통 독립 DBG clock과 always-on 전원에 격리합니다.<br>
**왜 헷갈리는가**: "디버그는 코어를 보는 것이니 코어에 붙어 있겠지"라는 직관 때문에.
:::

### DV 디버그 체크리스트 (DFD bring-up에서 마주칠 첫 실패들)

| 증상 | 1차 의심 | 어디 보나 |
|---|---|---|
| 디버거가 칩에 connect 실패 | JTAG/SWD 핀 배선·pull-up·TRSTn 전략 | 보드 핀맵, TRSTn 처리 |
| connect는 되는데 컴포넌트가 안 보임 | ROM table 베이스 주소 오류 또는 미구성 | DAP 버전, ROM table base 주소 |
| 코어 halt 명령이 무시됨 | DBGEN/SPIDEN 인증 신호 비활성 | fuse/lifecycle 상태, 인증 신호 소스 |
| trace는 되는데 halt만 안 됨 | NIDEN은 켜졌지만 DBGEN 꺼짐 | invasive vs non-invasive 인증 분리 |
| 코어 전원 게이팅 후 디버그 끊김 | 디버그 도메인이 코어 전원에 종속 | DBG clock/always-on 전원 격리 |
| reset 후 디버그 세션 유실 | reset isolation 미적용 | 디버그 reset 도메인 분리 여부 |

---

## 7. 핵심 정리 (Key Takeaways)

- **DFD는 post-silicon 가시성 인프라**. 실물 칩 내부는 외부에서 안 보이므로, 설계 단계에 심어 둔 디버그 통로(JTAG→DAP→CoreSight)로 관찰·제어한다.
- **4계층 스택**: External Debugger ⇄ JTAG/SWD 핀 ⇄ DAP(ADI) ⇄ CoreSight & 시스템 메모리. 직렬 핀 접근이 DAP에서 메모리-맵 버스 트랜잭션으로 바뀐다.
- **invasive vs non-invasive**: halt/step(개입)과 trace/PMU(관찰)는 분리되며, 각각 다른 인증 신호로 게이팅된다.
- **네 인증 신호**: DBGEN(NS invasive) / NIDEN(NS non-invasive) / SPIDEN(secure invasive) / SPNIDEN(secure non-invasive). 보통 fuse/lifecycle에서 구동.
- **격리가 핵심**: 디버그 로직은 독립 DBG clock + always-on 전원 + reset isolation으로, 코어가 죽어도 살아 있어야 한다.
- **ROM table**로 디버거가 connect 시점에 칩의 CoreSight 컴포넌트를 런타임 발견한다.

:::caution[실무 주의점]
- DAP 버전(ADIv5 vs ADIv6)과 ROM table base 주소는 SoC 통합 _초기에_ 고정해야 한다.
- 인증 신호 소스(fuse/lifecycle)를 security 정책에 맞춰 명확히 정의 — bring-up과 양산에서 다를 수 있다.
- 디버그 전원/클럭 도메인을 코어 power-gating과 _독립_으로 둔다.
:::

### 7.1 자가 점검

:::tip[🤔 Q1 — 4계층 추적 (Bloom: Analyze)]
디버거가 보낸 "코어 halt" 요청이 어느 층에서 _직렬 비트_에서 _메모리-맵 버스 트랜잭션_으로 바뀌는가?
<details>
<summary>정답</summary>

**DAP(ADI) 층, 구체적으로 MEM-AP**에서 바뀝니다. JTAG/SWD 핀으로 들어온 직렬 데이터는 DP가 디코딩해 어느 AP를 쓸지 정하고(SELECT), MEM-AP가 TAR(주소)/CSW(속성)/DRW(데이터)를 받아 비로소 APB/AHB/AXI 버스 트랜잭션을 발행합니다. 그 트랜잭션이 CoreSight CTI에 닿아 코어를 halt시킵니다. 즉 핀↔직렬은 JTAG의 세계, 그 너머는 AMBA 버스의 세계이고, DAP가 둘 사이의 변환기입니다.

</details>
:::
:::tip[🤔 Q2 — 인증과 가능성 (Bloom: Evaluate)]
양산 칩에서 "실시간 trace는 되는데 코어 halt만 안 된다"는 보고가 들어왔다. 가장 가능성 높은 원인은?
<details>
<summary>정답</summary>

**non-invasive 인증(NIDEN)은 enable이지만 invasive 인증(DBGEN)이 disable**된 상태입니다. trace/PMU는 non-invasive라 NIDEN으로 동작하지만, halt/step은 invasive라 DBGEN이 필요합니다. 양산 칩에서 실행 개입은 막되 진단용 trace는 허용하는 정책은 흔하므로, fuse/lifecycle 상태가 DBGEN을 끄고 NIDEN만 켰을 가능성이 높습니다. secure 코드라면 SPIDEN/SPNIDEN을 같은 논리로 확인합니다.

</details>
:::
### 7.2 출처

**Internal (HDG / Confluence)**
- `DFD` (Confluence import, `wiki/common/dfd_spec.md`) — §0 intro(스택 조망), §3 CoreSight 보안 신호, §5 DFD 통합 체크리스트

**External**
- IEEE Std 1149.1 — Standard Test Access Port and Boundary-Scan Architecture
- Arm IHI 0031 — Arm Debug Interface Architecture Specification (ADIv5 / ADIv6)
- Arm IHI 0029 — CoreSight Architecture Specification

---

## 다음 모듈

→ [N02 — JTAG & Boundary Scan](../02_jtag_boundary_scan/): 4계층 스택의 가장 아래층, 물리 핀과 TAP controller FSM이 어떻게 칩 안으로 들어가는지 신호 레벨로 본다.

[퀴즈 풀어보기 →](../quiz/01_why_dfd_quiz/)
