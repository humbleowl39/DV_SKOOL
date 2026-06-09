---
title: "Module 01 — 왜 CXL인가"
---

:::tip[학습 목표]
이 모듈을 마치면:

- **Explain** CXL이 등장한 두 가지 동기 — Memory Wall(메모리 용량 한계)과 가속기-CPU 간 일관성 비용 — 을 설명할 수 있다.
- **Differentiate** PCIe의 producer-consumer DMA 모델과 CXL의 Load/Store coherent 모델이 메모리 접근에서 어떻게 다른지 구분할 수 있다.
- **Explain** CXL이 PCIe를 대체하지 않고 그 물리 계층 위에 얹히는 이유와 그로 인한 인프라 재사용 이점을 설명할 수 있다.
- **Identify** CXL이 제공하는 세 가지 핵심 가치 — 메모리 확장, 캐시 일관성, 메모리 풀링 — 을 식별할 수 있다.
:::
:::note[사전 지식]
- PCIe 3-layer 프로토콜 스택과 TLP 기반 DMA 개념 — [PCIe 코스](../../pcie/)
- 캐시 일관성의 기본 개념 (캐시라인, snoop, shared/modified 상태)
:::
---

## 1. Why care? — 메모리는 더 못 꽂는데 가속기는 데이터를 더 원한다

### 1.1 시나리오 — 거대 모델 학습 중 메모리가 부족하다

수백 GB 파라미터를 가진 모델을 학습하는 서버를 생각해 봅시다. CPU 메인보드의 **DIMM**(Dual In-line Memory Module, 메인보드에 꽂는 RAM 모듈) 슬롯은 이미 가득 찼고, 더 꽂을 자리가 없습니다. RAM을 늘리려면 서버를 통째로 교체해야 하는데, 정작 비어 있는 것은 **PCIe**(Peripheral Component Interconnect Express, GPU·SSD 등 주변장치를 CPU에 잇는 고속 직렬 버스 표준) 슬롯입니다. 한편 GPU는 호스트 메모리에 있는 데이터를 가져다 연산하려고 매번 PCIe **DMA**(Direct Memory Access, CPU를 거치지 않고 장치가 메모리를 직접 읽고 쓰는 방식)로 복사해 오는데, 이 복사 비용과 일관성 관리 비용이 누적되어 실제 연산보다 데이터 이동에 시간을 더 쓰는 상황이 벌어집니다.

여기서 두 가지 질문이 동시에 떠오릅니다. 첫째, "비어 있는 PCIe 슬롯에 메모리를 꽂을 수는 없을까?" 둘째, "GPU가 호스트 메모리를 매번 복사하지 않고, CPU 캐시와 일관성을 유지한 채 직접 읽고 쓸 수는 없을까?" CXL은 이 두 질문에 동시에 답하기 위해 만들어졌습니다.

PCIe는 본질적으로 **DMA(producer-consumer) 모델**입니다. 여기서 producer-consumer는 한쪽이 데이터를 만들어 메모리에 쌓고(producer) 다른 쪽이 그걸 통째로 가져가는(consumer) 패턴을 말합니다. 디바이스가 호스트 메모리의 한 영역을 통째로 읽거나 쓰는 데에는 효율적이지만, **cacheline**(캐시가 메모리를 다루는 최소 단위 블록, 보통 64바이트) 단위로 수시로 작은 접근을 하기에는 **TLP**(Transaction Layer Packet, PCIe가 읽기/쓰기 요청을 실어 나르는 패킷)의 헤더 오버헤드와 지연이 큽니다. 메모리를 마치 자기 RAM처럼 **Load/Store**(CPU가 메모리 주소에 직접 읽기·쓰기 명령을 내리는 방식)로 접근하려면 다른 프로토콜이 필요합니다. 그것이 CXL의 출발점입니다.

이 모듈을 건너뛰면 이후 모든 내용 — **Flex Bus**(PCIe와 같은 물리 슬롯·배선을 쓰면서 부팅 시 PCIe 모드인지 CXL 모드인지 협상하는 CXL의 물리 인터페이스)가 왜 PCIe 물리 계층을 재사용하는지, .cache와 .mem이 왜 따로 있는지, **Bias**(Type 2 디바이스 메모리의 소유권을 호스트/디바이스 중 누가 갖는지 전환하는 일관성 메커니즘) coherency가 왜 필요한지 — 이 "그냥 그렇게 정의됐다"로만 남습니다. 동기를 이해해야 설계 결정이 인과로 읽힙니다.

---

## 2. Intuition — 한 줄 비유 와 한 장 그림

:::tip[💡 한 줄 비유]
**PCIe DMA** ≈ **택배로 짐 박스를 통째로 주고받기**. 큰 짐을 한 번에 옮기기에 좋지만, 물건 하나를 꺼내 보려고 매번 박스를 받아야 함.<br>
**CXL.mem / .cache** ≈ **같은 사무실의 공유 책상**. 옆자리(CPU)와 내 자리(가속기)가 같은 책상 위 서류를 직접 집어 읽고 쓰며, 누가 무엇을 바꿨는지 서로 즉시 안다(coherency).
:::

### 한 장 그림 — PCIe 위에 얹힌 CXL의 두 길

```d2
direction: down

CPU: "Host CPU\n(+ Home Agent / coherency)"
PCIe: "**PCIe Physical Layer**\n(slot, pins, electricals)\n공유 물리 계층"
IO: "CXL.io\n= PCIe TLP\n(enumeration, config, DMA)"
CACHE: "CXL.cache\nDevice → Host\n호스트 메모리를\n가속기가 일관성 유지하며 캐싱"
MEM: "CXL.mem\nHost → Device Mem\n외부 메모리를\nLoad/Store로 접근"
DEV: "CXL Device\n(가속기 / 메모리 확장기)"

CPU -> PCIe: "same slot"
PCIe -> IO
PCIe -> CACHE
PCIe -> MEM
IO -> DEV
CACHE -> DEV
MEM -> DEV
```

### 왜 이 디자인인가 — Design rationale

세 가지 요구가 CXL의 형태를 결정했습니다.

1. **새 보드/커넥터 없이 기존 인프라를 그대로 써야** → PCIe Electricals·Connector·Retimer를 재사용하는 Flex Bus. 보드 재설계 불필요.
2. **메모리를 cacheline 단위 Load/Store로 저지연 접근해야** → PCIe TLP가 아닌 별도 프로토콜 CXL.mem.
3. **가속기가 호스트 데이터를 복사 없이 일관성 유지하며 캐싱해야** → CXL.cache로 device-to-host 일관성 트래픽 처리.

이 세 요구가 곧 **"PCIe 물리 계층 + 그 위에 .io/.cache/.mem 세 프로토콜"** 이라는 CXL의 구조적 결정입니다.

---

## 3. 작은 예 — 같은 데이터를 PCIe DMA로, 그리고 CXL로 접근하기

가속기가 호스트 메모리의 한 cacheline을 읽어 연산하고 결과를 다시 쓰는 가장 단순한 시나리오를 두 방식으로 비교합니다.

### 단계별 다이어그램

```d2
direction: down

PCIE: "PCIe DMA 방식" {
  direction: down
  A1: "가속기: '이 영역 줘'\nDMA descriptor 설정"
  A2: "PCIe MemRd TLP\n→ 호스트 메모리 영역 복사"
  A3: "가속기 로컬 버퍼에 사본"
  A4: "연산 후 MemWr TLP\n→ 호스트로 되쓰기"
  A5: "일관성? SW가 flush/invalidate 관리"
  A1 -> A2 -> A3 -> A4 -> A5
}
CXL: "CXL.cache 방식" {
  direction: down
  B1: "가속기: D2H Req (RdShared, addr)"
  B2: "Host: 디렉토리 확인 + GO 보장"
  B3: "H2D Rsp (GO-S) + H2D Data"
  B4: "가속기 캐시에 Shared 상태로 보관\n직접 Load/Store"
  B1 -> B2 -> B3 -> B4
}
```

### 단계별 의미

| Step | PCIe DMA | CXL.cache |
|---|---|---|
| 접근 단위 | 큰 버퍼/페이지 (DMA descriptor) | cacheline (Load/Store) |
| 일관성 | SW가 명시적 flush/invalidate 관리 | HW가 GO/snoop으로 자동 유지 |
| 지연 | TLP 설정 + 복사 오버헤드 | cacheline 직접 접근, 저지연 |
| 적합 | 대량 스트리밍 전송 | 세밀하고 잦은 공유 접근 |

CXL.cache 흐름에서 핵심은 **GO(Global Observation)** 입니다. 호스트가 H2D Rsp로 GO-S를 보내기 전까지 디바이스는 데이터를 안전하게 사용할 수 없습니다. GO는 "이 트랜잭션이 시스템 전체에서 일관성 있게 관측되었다"는 보장이며, 이것이 PCIe DMA에는 없는 CXL의 일관성 계약입니다.

:::note[coherency의 방향이 비대칭이다 — host-managed coherence]
위 흐름을 자세히 보면 한 가지 비대칭이 드러납니다. 디바이스는 D2H Req("이 line 공유로 줘")를 *요청* 할 뿐, 그 요청이 시스템 전체에서 일관성 있게 처리되는지를 *판정* 하는 것은 호스트입니다. 즉 CXL.cache에서 디바이스는 호스트의 coherency(여러 캐시가 같은 메모리 주소를 들고 있어도 모두가 같은 최신 값을 보도록 맞추는 성질) 도메인에 **참여(participate)** 만 하고, coherency를 *주관* 하지 않습니다 — directory(누가 어느 line을 어떤 상태로 갖고 있나)와 home agent(요청을 직렬화하고 snoop — 다른 캐시에 "이 주소 갖고 있냐"고 묻는 일관성 질의 — 을 발행하며 최종 권한을 부여하는 주체)를 **호스트가 소유** 합니다.

왜 디바이스가 home agent가 아닐까요? coherency를 보장하려면 한 line에 대한 모든 요청이 *한 곳* 에서 직렬화되어야 합니다(앞 cache coherence 모듈의 ordering point 개념). 시스템에는 CPU 코어들, 다른 CXL 디바이스, 호스트 메모리가 모두 같은 주소 공간을 공유하는데, 이들 전체를 내려다보며 순서를 잡을 수 있는 것은 호스트의 home agent뿐입니다. 디바이스는 그 전역 그림을 못 보므로 home이 될 수 없고, 대신 "요청하고 → 호스트의 판정(GO)을 받고 → 그제서야 사용" 하는 client 역할을 맡습니다. GO가 *호스트* 에서 디바이스로(H2D) 흐르는 방향 자체가 이 비대칭 — host-managed coherence — 의 직접적 표현입니다.
:::

:::note[GO(권한)와 Data(값)가 왜 분리된 채널로 오나]
H2D 응답을 보면 **GO(Rsp)** 와 **Data** 가 서로 다른 메시지/채널로 도착합니다. "권한 줄게(GO)" 와 "값은 이거야(Data)" 를 굳이 나눈 이유가 있습니다.

coherency 결정(이 디바이스가 이 line을 Shared로 가져도 되는가)과 데이터 전송(그 line의 실제 64B 값을 옮기는 일)은 *성격이 다른 작업* 입니다. 권한 판정은 home agent가 directory를 보고 snoop을 정리하면 끝나는 빠른 논리 연산이고, 데이터는 그 값이 어디에 있느냐(호스트 메모리, 다른 캐시의 dirty 사본 등)에 따라 도착 시점이 들쭉날쭉합니다. 이 둘을 한 메시지로 묶으면 *느린 쪽에 빠른 쪽이 끌려갑니다* — 데이터가 준비될 때까지 권한 통지도 못 보냅니다.

분리하면 둘을 **독립적으로 파이프라인** 할 수 있습니다. 권한(GO)을 먼저 확정해 보내 두고 데이터는 준비되는 대로 따로 보내거나, 반대로 데이터를 먼저 흘려보내고 GO로 "이제 써도 안전" 을 나중에 확정하는 식으로, 두 흐름이 서로의 latency에 묶이지 않습니다. coherence 결정과 값 전송을 따로 굴려 link 활용도와 처리량을 높이는 것이 채널 분리의 메커니즘적 이점입니다. (그래서 검증에서 "GO 전 데이터 사용 금지" 가 중요해집니다 — 데이터가 GO보다 먼저 도착할 수 있기 때문에, 디바이스는 GO를 본 시점에야 그 값을 안전하다고 믿어야 합니다.)
:::

:::note[여기서 잡아야 할 두 가지]
**(1) CXL.cache는 접근 단위가 cacheline이고 일관성을 HW가 보장한다.** PCIe DMA처럼 SW가 flush(캐시의 수정본을 메모리에 강제로 내려쓰기)/invalidate(캐시에 든 사본을 무효로 버리기)를 손으로 관리할 필요가 없어, 가속기가 호스트 데이터를 "자기 캐시처럼" 다룰 수 있습니다.<br>
**(2) GO를 받기 전에는 데이터를 쓰면 안 된다.** GO는 일관성 관측의 약속이며, 검증 시 "GO 이전 데이터 사용"은 대표적인 프로토콜 위반 시나리오입니다.
:::
---

## 4. 일반화 — CXL의 세 가지 핵심 가치

CXL이 제공하는 가치는 세 축으로 정리됩니다. 이 세 가지가 곧 디바이스 타입(M03)과 프로토콜 선택(M02)을 결정합니다.

| 핵심 가치 | 무엇을 해결하나 | 주로 쓰는 프로토콜 |
|---|---|---|
| **메모리 확장 (Memory Expansion)** | PCIe 슬롯에 메모리 카드를 꽂아 시스템 RAM 용량 즉시 증가 (Memory Wall 해소) | CXL.mem |
| **캐시 일관성 (Cache Coherency)** | 가속기와 CPU가 데이터를 복사 없이 일관성 유지하며 공유 | CXL.cache |
| **메모리 풀링 (Memory Pooling)** | 여러 호스트가 거대한 메모리 풀을 공유하고 필요한 만큼 동적 할당 | CXL.mem + 패브릭 (CXL 2.0+) |

세 가치는 독립적이지 않습니다. 메모리 확장기(Type 3)는 CXL.mem만으로 충분하지만, GPU 같은 가속기(Type 2)는 자기 로컬 메모리를 호스트에 노출하면서(.mem) 동시에 호스트 메모리도 일관성 유지하며 캐싱(.cache)해야 하므로 세 프로토콜을 모두 씁니다. 디바이스가 무엇을 하느냐가 어느 프로토콜·어느 타입인지를 결정합니다.

```d2
direction: right

T1: "Type 1\nSmartNIC/FPGA\n(.io + .cache)\n가속기 일관성"
T2: "Type 2\nGPU/AI 가속기\n(.io + .cache + .mem)\n일관성 + 자기 메모리 노출"
T3: "Type 3\n메모리 확장기\n(.io + .mem)\n메모리 확장/풀링"

T1 -> T2: "+ 로컬 메모리"
T2 -> T3: "- 가속 연산\n(메모리만)"
```

---

## 5. 디테일 — PCIe와의 관계, 그리고 왜 "대체"가 아닌가

### 5.1 CXL은 PCIe를 대체하지 않는다

흔한 오해는 CXL이 PCIe를 밀어내는 차세대 버스라는 것입니다. 실제로는 정반대에 가깝습니다. CXL은 PCIe의 **물리 계층(electricals, connector, retimer)을 그대로 빌려** 동작합니다. 같은 슬롯, 같은 핀을 쓰며, 보드 설계자는 PCIe 보드를 거의 그대로 재사용합니다. 부팅 시 Flex Bus 협상에서 양단이 CXL을 지원하면 CXL 모드로, 아니면 PCIe Native 모드로 동작합니다(M02에서 상세).

CXL.io 프로토콜 자체가 PCIe TLP/**DLLP**(Data Link Layer Packet, 링크 계층이 흐름 제어·ACK 등에 쓰는 작은 패킷) 그대로입니다. **enumeration**(부팅 시 버스에 어떤 장치가 꽂혀 있는지 차례로 발견·등록하는 과정), configuration(발견한 장치의 레지스터를 설정하는 단계), 인터럽트, 일부 DMA는 여전히 PCIe 방식으로 처리됩니다. CXL이 새로 추가한 것은 그 위에 얹은 **.cache와 .mem** 이라는 두 coherent 프로토콜입니다.

### 5.2 왜 TLP로는 메모리 접근이 비효율적인가

PCIe TLP는 패킷 헤더 오버헤드와 ordering 규칙, 그리고 producer-consumer 의미를 전제로 설계되었습니다. CPU가 메모리를 읽을 때처럼 cacheline 단위로 수시로 작은 접근을 하기에는 헤더 오버헤드 비율이 높고 round-trip 지연이 큽니다. CXL.mem(M2S/S2M)은 이 접근을 메모리 컨트롤러 수준의 간결한 요청/응답으로 단순화해, 외부에 꽂힌 메모리를 로컬 DRAM에 가깝게 Load/Store로 접근하게 합니다.

| 관점 | PCIe TLP | CXL.mem |
|---|---|---|
| 의미 모델 | Producer-Consumer (DMA) | Load/Store (memory) |
| 헤더 오버헤드 | 상대적으로 큼 | 메모리 요청에 최적화 |
| 지연 특성 | round-trip + 큐잉 | 저지연 cacheline 접근 |
| 일관성 | SW 관리 | HW (.cache와 결합) |

---

## 6. 흔한 오해 와 DV 디버그 체크리스트

### 흔한 오해

:::danger[❓ 오해 1 — 'CXL은 PCIe를 대체하는 차세대 버스다']
**실제**: CXL은 PCIe 물리 계층 위에 얹히는 **대안 프로토콜**이며, CXL.io는 PCIe TLP 그대로입니다. 같은 슬롯·핀을 재사용하고, 협상 실패 시 PCIe로 폴백합니다.<br>
**왜 헷갈리는가**: "더 빠르고 새롭다"는 인상 때문에 세대 교체로 오해. 실제로는 PCIe 인프라 재사용이 핵심 설계 의도.
:::
:::danger[❓ 오해 2 — '가속기가 호스트 메모리를 캐싱하면 그냥 빨라진다']
**실제**: 캐싱하는 순간 **일관성 문제**가 생깁니다. CPU가 같은 데이터를 바꾸면 가속기 캐시가 stale해집니다. CXL.cache의 GO/snoop 메커니즘이 이걸 HW로 보장하기에 비로소 안전합니다.<br>
**왜 헷갈리는가**: "캐시 = 빠름"만 보고 일관성 비용을 간과.
:::

### DV 디버그 체크리스트 (동기/개념 단계에서 마주치는 첫 혼동)

| 증상 | 1차 의심 | 어디 보나 |
|---|---|---|
| CXL 링크가 안 올라오고 PCIe로만 동작 | Flex Bus 협상 실패 (8 GT/s 미진입 등) → PCIe 폴백 | M02 Flex Bus 협상, LTSSM 로그 |
| 가속기가 stale 데이터를 읽음 | GO 수신 전 데이터 사용, 또는 snoop 누락 | CXL.cache GO/snoop 시퀀스 (M03) |
| "메모리는 늘었는데 성능이 안 나옴" | TLP DMA로 접근 중 (.mem 미사용) | 프로토콜 선택 — .mem Load/Store인지 |

---

## 7. 핵심 정리 (Key Takeaways)

- **CXL의 두 동기**: Memory Wall(슬롯 한계로 RAM 확장 불가)과 가속기-CPU 간 일관성 비용. PCIe 슬롯을 활용해 둘 다 해결.
- **PCIe 위에 얹힌다**: 물리 계층·커넥터·리타이머를 재사용하고, CXL.io는 PCIe TLP 그대로. 새로 추가된 것은 .cache와 .mem.
- **Load/Store vs DMA**: CXL.mem/.cache는 cacheline 단위 Load/Store + HW 일관성. PCIe DMA는 producer-consumer 복사 + SW 일관성.
- **세 가지 핵심 가치**: 메모리 확장(.mem), 캐시 일관성(.cache), 메모리 풀링(.mem + 패브릭).
- **GO(Global Observation)** 는 CXL.cache의 일관성 계약 — GO 수신 전 데이터 사용 금지.

:::caution[실무 주의점]
- CXL은 PCIe를 "끄는" 것이 아니라 협상으로 모드를 고른다 — 디버그 시 PCIe 모드 폴백 여부부터 확인.
- 가속기가 호스트 메모리를 캐싱하는 순간 일관성은 공짜가 아니다 — GO/snoop를 HW가 처리한다는 전제를 잊지 말 것.
:::
### 7.1 자가 점검

:::tip[🤔 Q1 — PCIe vs CXL 메모리 접근 (Bloom: Analyze)]
같은 외부 메모리를 PCIe DMA로 접근할 때와 CXL.mem으로 접근할 때, 일관성 관리 책임은 각각 누구에게 있는가?
<details>
<summary>정답</summary>

- **PCIe DMA**: 일관성은 **소프트웨어(드라이버/OS)** 책임. 디바이스가 호스트 메모리를 복사해 가면, SW가 명시적으로 cache flush/invalidate를 호출해 stale을 막아야 함.
- **CXL.mem/.cache**: 일관성은 **하드웨어** 책임. GO, snoop, 디렉토리로 호스트와 디바이스 캐시 상태를 자동 동기화. SW는 일관성을 신경 쓰지 않고 Load/Store만.
- 그래서 CXL은 "복사 없이 공유"가 가능 — 잦고 세밀한 접근에서 PCIe DMA보다 유리.

</details>
:::
:::tip[🤔 Q2 — 왜 .io와 .mem이 따로 있나 (Bloom: Evaluate)]
CXL.io(=PCIe TLP)가 이미 메모리 읽기/쓰기 TLP를 지원하는데, 왜 별도로 CXL.mem을 두는가?
<details>
<summary>정답</summary>

- TLP는 producer-consumer DMA 의미에 최적화되어 헤더 오버헤드와 ordering 규칙이 cacheline 단위 잦은 접근에 비효율적.
- CXL.mem(M2S/S2M)은 메모리 컨트롤러 수준의 간결한 요청/응답으로 **저지연 Load/Store**를 제공 — 외부 메모리를 로컬 DRAM에 가깝게 다룸.
- 또한 .mem은 .cache와 결합해 HW 일관성을 제공하지만, .io의 MemRd/MemWr TLP는 일관성을 SW에 맡김.
- 결론: 같은 "메모리 접근"이라도 목적(대량 전송 vs 세밀 공유)이 달라 두 프로토콜이 공존.

</details>
:::
### 7.2 출처

**External**
- *CXL 3.1 Specification* §1 (Introduction) — CXL Consortium
- *A Primer on Memory Consistency and Cache Coherence* (Nagarajan, Sorin et al.) — 일관성 배경

---

## 다음 모듈

→ [Module 02 — Flex Bus & 3 프로토콜](../02_flexbus_protocols/): PCIe 물리 계층 위에서 세 프로토콜이 어떻게 협상되고 다중화되는지, 그리고 .io / .cache / .mem의 채널 구조를 본다.

[퀴즈 풀어보기 →](../quiz/01_motivation_quiz/)
