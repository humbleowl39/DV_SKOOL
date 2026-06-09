---
title: "Module 04 — ARB/MUX & 패브릭 (vLSM, DCD, 멀티레벨 스위칭)"
---

:::tip[학습 목표]
이 모듈을 마치면:

- **Analyze** ARB/MUX가 세 프로토콜(.io/.cache/.mem)을 단일 Flex Bus 링크로 다중화하는 메커니즘을 분석할 수 있다.
- **Explain** vLSM(Virtual Link State Machine)이 프로토콜별 가상 링크 상태를 독립적으로 관리하는 이유와 ALMP의 역할을 설명할 수 있다.
- **Trace** DCD(Dynamic Capacity Device)가 Fabric Manager를 통해 메모리를 온디맨드로 할당/회수하는 흐름을 추적할 수 있다.
- **Differentiate** MLD / G-FAM / PBR / Multi-Level Switch 등 CXL 2.0+ 패브릭 기능을 구분할 수 있다.
:::
:::note[사전 지식]
- [Module 02 — Flex Bus & 3 프로토콜](../02_flexbus_protocols/) — 4계층 스택, Flit
- [Module 03 — 디바이스 타입 & Coherency](../03_device_types_coherency/) — HDM, BISnp
- PCIe 전력 상태(L0/L1/L2) 개념
:::
---

## 1. Why care? — 한 링크에 세 프로토콜, 그리고 여러 호스트가 한 메모리를

### 1.1 시나리오 — 세 프로토콜의 Flit이 뒤섞여 흐른다

M02에서 .io / .cache / .mem 세 프로토콜이 물리적으로는 단 한 가닥의 Flex Bus 링크를 공유한다고 했습니다. 그런데 이 세 프로토콜은 서로 다른 전력 상태에 있을 수 있습니다. 예를 들어 .cache 트래픽은 활발한데 .io는 idle(보낼 것이 없어 노는 상태)이라 절전 상태로 들어가고 싶을 수 있습니다. 만약 물리 링크 하나의 전력 상태가 모든 프로토콜을 한꺼번에 묶어버리면, 한 프로토콜의 idle이 다른 프로토콜을 강제로 깨워야 하거나 반대로 활성 프로토콜이 절전을 막습니다.

해법은 **프로토콜마다 독립된 가상 링크 상태(vLSM**, Virtual Link State Machine — 물리 링크는 하나지만 프로토콜마다 별도의 링크 상태를 가진 것처럼 가상화하는 상태 기계)를 두는 것입니다. 물리 링크는 하나지만, 각 프로토콜이 자기만의 **Active**(정상 동작)/**L1**(가벼운 절전)/**L2**(깊은 절전) 상태를 가진 것처럼 가상화합니다. 그리고 이 가상 상태를 양 끝단이 일치시키기 위해 **ALMP**(ARB/MUX Link Management Packet, 양단의 vLSM 상태를 맞추려고 주고받는 작은 관리 패킷)라는 작은 관리 패킷을 주고받습니다.

한 걸음 더 나아가 CXL 2.0+에서는 여러 호스트가 스위치를 통해 하나의 메모리 풀을 공유합니다. 이때 단일 물리 디바이스를 여러 논리 디바이스로 쪼개고(**MLD**, Multi Logical Device — 한 물리 디바이스를 여러 논리 디바이스로 분할), 메모리를 온디맨드로 할당/회수하며(**DCD**, Dynamic Capacity Device — 메모리 용량을 필요할 때 빌리고 반환하는 디바이스), 멀티홉 라우팅(**PBR**, Port-Based Routing — 여러 스위치를 거쳐 패킷을 전달하는 라우팅)으로 패브릭을 확장합니다. 이 모듈은 "한 링크 안의 다중화"부터 "패브릭 전역의 메모리 공유"까지를 다룹니다.

이 모듈을 건너뛰면 CXL이 단일 링크 프로토콜로만 보이고, 메모리 풀링·패브릭이라는 CXL의 가장 큰 가치가 빠집니다.

---

## 2. Intuition — 한 줄 비유 와 한 장 그림

:::tip[💡 한 줄 비유]
**ARB/MUX + vLSM** ≈ **한 가닥 회선을 쓰는 회사의 교환실**. 물리 회선은 하나지만 부서(.io/.cache/.mem)마다 "통화 중/대기/절전" 상태를 따로 관리하고(vLSM), 교환원(Arbiter)이 우선순위로 차례를 정해 한 회선에 시분할로 실어 보낸다(Multiplexer). 양 끝 교환실은 상태표를 작은 쪽지(ALMP)로 맞춘다.
:::

### 한 장 그림 — ARB/MUX 다중화 구조

```d2
direction: down

IO: ".io 트래픽"
CACHE: ".cache 트래픽"
MEM: ".mem 트래픽"

VLSM_IO: "vLSM (.io)"
VLSM_CM: "vLSM (.cachemem)"
ARB: "**Arbiter**\n프로토콜 간 우선순위\n(Round-robin / WRR)"
MUX: "**Multiplexer**\nFlit 시분할 실어 송출"
PHY: "Physical Layer\n(단일 Flex Bus 링크)"

IO -> VLSM_IO
CACHE -> VLSM_CM
MEM -> VLSM_CM
VLSM_IO -> ARB
VLSM_CM -> ARB
ARB -> MUX
MUX -> PHY
```

### 왜 이 디자인인가 — Design rationale

1. **세 프로토콜이 한 물리 링크를 공유하되 전력/상태는 독립이어야** → 프로토콜별 vLSM (가상 링크 상태).
2. **누구의 Flit을 먼저 보낼지 정해야** → **Arbiter**(여러 요청 중 누구 차례인지 정하는 중재기) (Round-robin — 차례를 한 바퀴씩 공평하게 돌리는 방식 / Weighted Round-Robin(WRR) — 우선순위에 가중치를 둔 변형).
3. **양 끝단의 가상 상태가 안전하게 일치해야** → ALMP로 상태 동기화.

---

## 3. 작은 예 — DCD로 메모리 64GB를 온디맨드 할당

호스트가 메모리 부족을 겪을 때 **Fabric Manager**(FM, 메모리 풀의 용량 할당·회수를 중앙에서 조정하는 관리 주체)를 통해 DCD에서 메모리를 동적으로 받아오는 흐름입니다.

### 단계별 다이어그램

```d2
direction: down

H1: "**Host**\n① 메모리 부족\n+64GB 요청"
FM: "**Fabric Manager**\n② Add Capacity\n(Region X, 64GB)"
DCD: "**DCD Memory**\n③ Region 준비\n+ Add 완료 응답"
H2: "**Host**\n④ Region X 매핑\n페이지 테이블 갱신\nHDM 영역 확장 → 사용"
H3: "**Host**\n⑤ Release Region X\n(workload 종료 후)"

H1 -> FM: "Add mem request"
FM -> DCD: "Add Capacity"
DCD -> H2: "Add 완료 → 매핑"
H2 -> H3: "사용 후 반환"
H3 -> FM: "Release → Remove Capacity"
```

### 단계별 의미

| Step | 누가 | 무엇을 | 왜 |
|---|---|---|---|
| ① | Host | Fabric Manager에 +64GB 요청 | 메모리 부족 |
| ② | Fabric Manager | DCD에 Add Capacity(Region X, 64GB) | 풀에서 용량 배정 |
| ③ | DCD | Region 준비 후 Add 완료 응답 | 물리 메모리 확보 |
| ④ | Host | Region X 매핑, 페이지 테이블 갱신, HDM 확장 | 주소 공간에 편입해 사용 시작 |
| ⑤ | Host | workload 종료 후 Release → Remove Capacity | 풀에 반환, 다른 호스트가 재사용 |

DCD의 핵심은 메모리가 **고정 할당이 아니라 풀에서 동적으로 빌려 쓰고 반환**된다는 점입니다. 이것이 데이터센터에서 서버별 메모리 과잉 프로비저닝을 해소하는 메모리 풀링의 실체입니다.

:::note[왜 풀링이 필요한가 — stranded memory 문제]
풀링의 근본 동기는 **stranded(놀고 있는) memory** 입니다. 데이터센터의 각 서버는 메모리가 *고정 장착* 되어 있고, 그 양은 "최악의 경우 이 서버가 쓸 수 있는 최대치" 에 맞춰 over-provisioning 됩니다. 문제는 워크로드가 서버마다, 시간마다 다르다는 것입니다 — 어떤 서버는 CPU는 바쁜데 메모리는 절반만 쓰고, 옆 서버는 메모리가 모자라 작업을 못 받습니다. 그런데 남는 서버의 유휴 메모리를 모자란 서버에 *빌려줄 방법이 없습니다*. 물리적으로 그 서버 보드에 박혀 있기 때문입니다. 그 결과 전체 데이터센터로 보면 막대한 메모리가 *할당돼 있으나 아무도 못 쓰는* 채로 갇혀 있습니다 — 이것이 stranded memory이고, 비용·전력의 순손실입니다.

CXL 메모리 풀링은 메모리를 개별 서버 보드에서 떼어 *공유 풀* 로 모읍니다. 그러면 DCD가 보여 준 것처럼, 모자란 호스트가 필요할 때 풀에서 빌리고 끝나면 반환해 다른 호스트가 재사용합니다. 즉 풀링은 "각 서버가 최악 케이스만큼 따로 들고 있다가 대부분을 놀리는" 구조를, "전체가 한 풀을 공유해 stranded를 회수하는" 구조로 바꾸는 것입니다. DCD의 on-demand Add/Release는 바로 이 회수를 실현하는 메커니즘입니다.
:::

:::note[여기서 잡아야 할 두 가지]
**(1) DCD는 Fabric Manager가 중개한다.** 호스트가 DCD에 직접 명령하지 않고, FM이 풀 전체의 할당/회수를 조정 — 여러 호스트가 한 풀을 공유하므로 중앙 조정자가 필요.<br>
**(2) Add/Release는 호스트 페이지 테이블·HDM 매핑과 연동된다.** 용량을 받으면 매핑하고, 반환 전 매핑을 해제 — 사용 중 회수는 데이터 손실 위험.
:::
---

## 4. 일반화 — ARB/MUX 구성과 vLSM 상태

### 4.1 ARB/MUX 구성 요소

3개 프로토콜을 단일 Flex Bus 링크에 시분할로 실어 보내는 다중화 계층입니다.

| 구성 요소 | 역할 |
|----------|------|
| **vLSM (.io)** | CXL.io 프로토콜의 가상 링크 상태 관리 |
| **vLSM (.cachemem)** | CXL.cache + CXL.mem 공통 가상 링크 상태 관리 |
| **Arbiter** | 프로토콜 간 우선순위 결정 (Round-robin / WRR) |
| **Multiplexer** | Flit을 시분할로 물리 계층에 실어 송출 |

.cache와 .mem이 **하나의 vLSM(.cachemem)** 을 공유하는 점에 주목하세요. 둘은 M02에서 본 것처럼 공통 Link Layer(CXL.cachemem LL)를 쓰므로 가상 링크 상태도 함께 관리됩니다. 반면 .io는 PCIe DLL 기반이라 별도 vLSM을 가집니다.

### 4.2 vLSM 상태

물리 링크는 하나지만, 각 프로토콜이 독립된 상태를 가진 것처럼 가상화합니다.

| 상태 | 의미 | 전이 트리거 |
|------|------|------------|
| **Reset** | 초기 상태 | 전원 인가 / 링크 리셋 |
| **Active** | 정상 동작 중 | 링크 활성화 완료 |
| **L1** | 가벼운 절전 | PM Request → Wake |
| **L2** | 깊은 절전 | 장시간 idle → Wake 시 재초기화 |
| **Retrain** | 재훈련 | 오류 / 폭 조절 필요 |
| **L0p** | Active 내 부분 폭 축소 | 전력 절감 (CXL 3.0+) |

**L0p(CXL 3.0+)** 는 동적 링크 폭 조절입니다. 트래픽이 적을 때 x16 → x8 → x4로 폭을 줄여 전력을 아끼고, 부하가 늘면 다시 확장합니다.

### 4.3 ALMP (ARB/MUX Link Management Packet)

| 항목 | 내용 |
|------|------|
| **크기** | 1 DWORD (4 byte) |
| **용도** | vLSM 상태 동기화 (Active ↔ L1 ↔ L2 ↔ L0p) |
| **주요 메시지** | Status.Active, Request.L1, Request.L2, Request.L0p |
| **동작** | 양 끝단의 vLSM 상태가 일치해야 안전한 전이 가능 |

ALMP는 작지만(4 byte) 중요합니다. 양 끝단의 가상 상태가 어긋난 채 전이하면 한쪽은 절전, 한쪽은 Active로 데이터를 보내는 불일치가 생기므로, **상태 전이 전 ALMP로 합의**하는 것이 핵심입니다.

:::note[왜 2-way handshake가 필수인가 — 분산 상태기계의 동기화]
링크의 양 끝(호스트 측과 디바이스 측)은 *각자 독립적으로 동작하는 두 개의 상태기계* 입니다. 한쪽이 보는 vLSM 상태가 다른 쪽이 보는 상태와 자동으로 같아지지 않습니다 — 둘 사이엔 전파 지연이 있고, 그 사이에도 flit이 link 위를 날아다닙니다. 여기서 한쪽이 *자기 혼자만의 판단으로* "이제 idle이니 L1으로 내려가자" 하고 수신을 멈춰 버리면 어떻게 될까요? 상대는 아직 Active인 줄 알고 flit을 계속 송신하는데, 잠든 쪽은 그걸 못 받습니다 — **in-flight flit이 유실** 됩니다. 반대로 한쪽이 먼저 깨어 데이터를 보내는데 상대가 아직 절전이면 같은 손실이 납니다.

그래서 절전 전이는 *반드시 2-way handshake* 여야 합니다. 한쪽이 `Request.L1`을 보내고, 상대가 "나도 내려갈 준비됐다(더는 송신할 flit 없다)" 를 *명시적으로 응답* 한 뒤에야 둘이 *함께* 전이합니다. 이 합의가 보장하는 것은 "양쪽 모두 더 보낼 것이 없고, 둘 다 같은 시점에 같은 상태로 간다" 는 것 — 즉 전이 경계에서 in-flight flit이 남지 않습니다. 이것은 한 노드가 일방적으로 결정하면 깨지는 *분산 합의(distributed consensus)* 문제이고, ALMP는 그 합의를 나르는 메시지입니다. (이 원리는 PCIe ASPM의 L1 entry handshake와 동일합니다 — [PCIe 전력/AER/Hotplug](../../pcie/07_power_aer_hotplug/) 참고. 분산된 두 끝이 절전을 합의해야 한다는 문제는 프로토콜이 달라도 같은 모양입니다.)
:::

---

## 5. 디테일 — CXL 2.0+ 패브릭 기능

### 5.1 멀티 호스트 패브릭 토폴로지

CXL 3.1에서는 다중 호스트가 다중 디바이스를 공유하는 패브릭이 지원됩니다. 다수의 Host CPU가 CXL Switch를 통해 연결되며, Multi-Hop으로 스위칭됩니다.

| 기능 | 설명 |
|------|------|
| **MLD** (Multi Logical Device) | 단일 물리 디바이스를 여러 Logical Device로 분할 (최대 16 LD) → 다중 호스트가 분할 사용 |
| **G-FAM** (Global-Fabric-Attached Memory) | 패브릭 전역에서 접근 가능한 거대 메모리 풀 |
| **PBR** (Port-Based Routing) | 스위치 multi-hop 통과를 위한 라우팅 메커니즘 |
| **Multi-Level Switch** | CXL 3.1에서 여러 단계 스위치 캐스케이딩 지원 |

MLD는 한 물리 디바이스(예: 큰 메모리 확장기)를 최대 16개의 논리 디바이스로 쪼개, 16개의 호스트가 각자 자기 몫을 가진 것처럼 쓰게 합니다. PBR은 M02에서 언급한 PBR TLP Header(PTH)로 멀티홉 스위치를 통과하는 라우팅을 가능하게 합니다.

```d2
direction: down

H1: "Host A"
H2: "Host B"
SW1: "CXL Switch (Level 1)"
SW2: "CXL Switch (Level 2)\nMulti-Hop (PBR)"
MLD: "MLD Device\n(최대 16 Logical Device)"
GFAM: "G-FAM\n(전역 메모리 풀)"

H1 -> SW1
H2 -> SW1
SW1 -> SW2: "PBR multi-hop"
SW2 -> MLD: "LD 분할 사용"
SW2 -> GFAM
```

### 5.2 DCD (Dynamic Capacity Device) — CXL 3.0+

§3의 흐름이 DCD의 핵심입니다. Fabric Manager를 통해 메모리를 온디맨드로 Add/Release합니다. CXL 3.0에서 기초가 도입되고 CXL 3.1에서 완전 지원됩니다(M05 세대 표 참고).

### 5.3 RAS — Poison과 Viral

CXL은 PCIe **AER**(Advanced Error Reporting, 하드웨어 오류를 분류해 호스트에 보고하는 PCIe 기능)을 확장해 메모리 도메인까지 에러 처리를 제공합니다. 검증 시 에러 주입 시나리오의 토대가 됩니다. (**RAS**(Reliability, Availability, Serviceability — 신뢰성·가용성·정비성, 오류를 감지·격리·보고해 시스템을 견고하게 하는 기능군)의 일부입니다.)

| 메커니즘 | 설명 |
|----------|------|
| **Poison** | 데이터 오류 감지 시 해당 캐시라인에 poison 태그 → 소비자가 읽을 때 에러 보고. 오류 원점 추적 가능 |
| **Viral** | poison 확산 위험 시 링크를 viral 상태로 → 오염 확산 차단 (최후 방어선) |
| **Error Reporting** | PCIe AER + CXL 전용 에러 로그로 호스트 보고. CXL 3.1은 부분 미디어 오류 보고 추가 |

Poison은 데이터 경로를 따라 전파되어 최초 오류 지점부터 최종 소비자까지 추적 가능합니다. Viral은 poison 전파가 통제 불가일 때 링크 전체를 정지시켜 정상 컴포넌트를 보호하는 최후의 방어선입니다.

---

## 6. 흔한 오해 와 DV 디버그 체크리스트

### 흔한 오해

:::danger[❓ 오해 1 — '물리 링크가 하나니 전력 상태도 하나다']
**실제**: 물리 링크는 하나지만 **프로토콜마다 독립된 vLSM** 을 가집니다. .io가 절전(L1)이어도 .cachemem은 Active일 수 있습니다. 전력 상태는 가상 링크 단위이며, 전이는 ALMP로 양단이 합의.<br>
**왜 헷갈리는가**: "물리 = 논리"라는 직관 때문에 가상화를 놓침.
:::
:::danger[❓ 오해 2 — 'DCD 메모리는 한 번 받으면 계속 쓴다']
**실제**: DCD는 **온디맨드 할당/회수**입니다. workload가 끝나면 Release → Remove Capacity로 풀에 반환해 다른 호스트가 재사용합니다. 반환 전 페이지 테이블·HDM 매핑 해제가 선행돼야 — 사용 중 회수는 데이터 손실.<br>
**왜 헷갈리는가**: 일반 RAM처럼 "한 번 할당 = 영구"로 생각.
:::
:::danger[❓ 오해 3 — 'MLD는 디바이스를 물리적으로 쪼갠다']
**실제**: MLD는 **논리적** 분할입니다. 하나의 물리 디바이스를 최대 16개 Logical Device로 보이게 해 여러 호스트가 분할 사용 — 물리 분리가 아니라 자원 파티셔닝.<br>
**왜 헷갈리는가**: "분할"을 물리적 절단으로 오해.
:::

### DV 디버그 체크리스트

| 증상 | 1차 의심 | 어디 보나 |
|---|---|---|
| 한 프로토콜 idle인데 전체 링크가 안 자거나 깸 | vLSM 독립성 오인 — 프로토콜별 상태 미분리 | 각 vLSM 상태, ALMP 메시지 |
| L1/L2 전이 후 데이터 유실 | 양단 vLSM 상태 불일치 (ALMP 미합의) | ALMP Status/Request 교환 순서 |
| DCD Add 후 호스트가 메모리 못 봄 | 페이지 테이블/HDM 매핑 갱신 누락 | Add 완료 → 매핑 단계 |
| 사용 중 DCD 회수로 데이터 손실 | Release 전 매핑 미해제 | Release 순서 (해제 → Remove Capacity) |
| poison 읽었는데 에러 보고 안 됨 | poison 태그 전파/AER 보고 경로 단절 | Poison 경로, Error Reporting |

---

## 7. 핵심 정리 (Key Takeaways)

- **ARB/MUX**: vLSM(프로토콜별 가상 링크 상태) + Arbiter(우선순위) + Multiplexer(시분할 송출)로 세 프로토콜을 단일 링크에 다중화.
- **vLSM 독립성**: 물리 링크는 하나지만 .io와 .cachemem이 각자 Active/L1/L2/L0p 상태를 독립 관리. .cache와 .mem은 vLSM(.cachemem)을 공유.
- **ALMP(4 byte)** 로 양단 vLSM 상태를 동기화 — 전이 전 합의가 안전한 전이의 전제.
- **DCD(CXL 3.0+)**: Fabric Manager 중개로 메모리를 온디맨드 Add/Release. 페이지 테이블·HDM 매핑과 연동.
- **패브릭(CXL 2.0+)**: MLD(논리 분할 ≤16 LD), G-FAM(전역 풀), PBR(멀티홉 라우팅), Multi-Level Switch.
- **RAS**: Poison(오류 태그+추적), Viral(확산 차단 최후 방어선), AER 확장 보고.

:::caution[실무 주의점]
- 전력 상태 디버그는 항상 **프로토콜별 vLSM과 ALMP 합의**부터 — 물리 링크 하나로 뭉뚱그리지 말 것.
- DCD 회수는 반드시 **매핑 해제 → Remove Capacity** 순서 — 역순은 사용 중 메모리 손실.
- MLD/PBR 검증은 "어느 LD/어느 호스트의 트래픽인가" 식별이 scoreboard(실제 출력과 기대값을 비교하는 검증 컴포넌트)의 전제.
:::
### 7.1 자가 점검

:::tip[🤔 Q1 — vLSM 독립성 (Bloom: Analyze)]
.io 트래픽이 오래 idle이라 절전에 들어가고 싶은데 .cache는 한창 활발하다. CXL은 이를 어떻게 처리하며, 만약 vLSM이 없다면 무슨 문제가 생기는가?
<details>
<summary>정답</summary>

- CXL은 **프로토콜별 vLSM**을 둬서 .io는 L1(절전), .cachemem은 Active로 **독립** 관리. ALMP로 양단이 각 가상 링크 상태를 합의.
- vLSM이 없다면 물리 링크 하나의 단일 전력 상태에 모두 묶여, .io를 재우려면 .cache까지 재워야 하거나(성능 저하), .cache가 활성이라 .io가 절대 절전 못 함(전력 낭비). 둘 다 비효율.
- 즉 vLSM은 "물리는 공유, 전력/상태는 분리"를 가능케 하는 가상화.

</details>
:::
:::tip[🤔 Q2 — DCD 회수 순서 (Bloom: Evaluate)]
DCD에서 받은 Region X를 반환하려 한다. 올바른 순서를 정하고, 순서를 어기면 무슨 일이 생기는지 평가하라.
<details>
<summary>정답</summary>

- **올바른 순서**: (1) workload 종료 후 호스트가 Region X **매핑 해제**(페이지 테이블/HDM에서 제거) → (2) Host가 Fabric Manager에 **Release** → (3) FM이 DCD에 **Remove Capacity**.
- **순서를 어기면**(예: 매핑이 살아있는데 Remove Capacity 먼저): 호스트가 여전히 유효하다고 믿는 주소가 물리적으로 회수돼 **사용 중 메모리 손실/오접근**. 다른 호스트에 재할당되면 데이터 오염까지.
- 핵심: 회수는 항상 "사용 중단 → 매핑 해제 → 물리 회수" 순서.

</details>
:::
### 7.2 출처

**External**
- *CXL 3.1 Specification* §5 (ARB/MUX), §7 (Fabric Manager, DCD), §9 (Switching), §12 (RAS) — CXL Consortium

---

## 다음 모듈

→ [Module 05 — 세대 비교 & DV 관점](../05_generations_dv/): CXL 1.1부터 3.1까지 무엇이 추가됐는지 한 표로 정리하고, 검증 엔지니어 관점에서 어디를 어떻게 검증할지 본다.

[퀴즈 풀어보기 →](../quiz/04_arbmux_fabric_quiz/)
