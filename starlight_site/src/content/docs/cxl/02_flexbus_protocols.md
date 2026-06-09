---
title: "Module 02 — Flex Bus & 3 프로토콜 (.io / .cache / .mem)"
---

:::tip[학습 목표]
이 모듈을 마치면:

- **Explain** Flex Bus가 PCIe 물리 계층을 재사용하면서 부팅 시 CXL 모드를 협상하는 과정(TS1/TS2 OS, fallback)을 설명할 수 있다.
- **Differentiate** CXL 4계층 스택(Transaction/Link/ARB-MUX/Physical)에서 각 계층의 역할을 구분할 수 있다.
- **Trace** CXL.cache의 D2H/H2D 채널과 CXL.mem의 M2S/S2M 채널을 따라 한 읽기 요청의 흐름을 추적할 수 있다.
- **Differentiate** CXL.io / CXL.cache / CXL.mem 세 프로토콜의 채널 구조·방향·용도를 구분할 수 있다.
:::
:::note[사전 지식]
- [Module 01 — 왜 CXL인가](../01_motivation/)
- PCIe LTSSM(Link Training and Status State Machine)과 TLP 개념 — [PCIe 코스](../../pcie/)
:::
---

## 1. Why care? — 같은 한 가닥 링크에 세 프로토콜이 섞여 흐른다

### 1.1 시나리오 — 채널을 헷갈려 엉뚱한 곳에서 트랜잭션을 찾는다

CXL 가속기를 검증하는 환경을 구축한다고 합시다. "가속기가 호스트 메모리를 읽는다"는 한 동작을 추적하려는데, 어느 채널을 봐야 하는지부터 막힙니다. 가속기가 **호스트 메모리를 캐싱**하는 읽기라면 CXL.cache의 D2H Req를 봐야 하고, 호스트가 **가속기의 로컬 메모리(HDM)** 를 읽는 거라면 CXL.mem의 M2S Req를 봐야 합니다. 둘은 방향도, 채널도, 프로토콜도 완전히 다릅니다. 여기서 채널을 헷갈리면 scoreboard가 영원히 도착하지 않는 트랜잭션을 기다리며 hang합니다.

게다가 이 세 프로토콜(.io / .cache / .mem)은 **물리적으로는 단 한 가닥의 Flex Bus 링크** 위를 시분할로 흐릅니다. 그래서 검증자는 "지금 이 Flit이 어느 프로토콜의 것인가"를 ARB/MUX 계층(M04)에서 구분할 수 있어야 합니다. 채널 구조와 프로토콜 분리를 먼저 머릿속에 정리하지 않으면 이후 모든 트랜잭션 추적이 흔들립니다.

이 모듈을 건너뛰면 디바이스 타입(M03)도, ARB/MUX 다중화(M04)도 토대가 없습니다. Flex Bus 협상과 3 프로토콜의 채널 구조가 CXL 전체의 골격입니다.

---

## 2. Intuition — 한 줄 비유 와 한 장 그림

:::tip[💡 한 줄 비유]
**Flex Bus** ≈ **한 가닥의 고속도로 + 톨게이트 협상**. 부팅 때 톨게이트(LTSSM)에서 "너 CXL 가능해?"를 물어(TS1/TS2 OS) 합의되면 CXL 차선들(.io/.cache/.mem)을 열고, 안 되면 일반 PCIe 차선만 연다.<br>
**3 프로토콜** ≈ 한 고속도로 위를 달리는 **세 종류 차량**: .io(PCIe 트럭 — 설정/DMA), .cache(가속기↔호스트 일관성 셔틀), .mem(메모리 화물 직행).
:::

### 한 장 그림 — 4계층 스택과 세 프로토콜의 다중화

```d2
direction: down

TX: "**Transaction Layer**" {
  IO: ".io\n(PCIe TLP)"
  CACHE: ".cache\n(D2H / H2D)"
  MEM: ".mem\n(M2S / S2M)"
}
LL: "**Link Layer**" {
  IOLL: ".io LL\n(PCIe DLL)"
  CMLL: ".cachemem LL\n(68B / 256B Flit)"
}
AM: "**ARB / MUX**\nvLSM + Arbiter + Multiplexer\n3 프로토콜 → 1 링크 다중화"
PHY: "**Physical (PHY)**\nLogical PHY (LTSSM, Flex Bus)\n+ Electrical PHY (PCIe 호환)"

TX -> LL
LL -> AM
AM -> PHY
```

### 왜 이 디자인인가 — Design rationale

1. **PCIe 인프라를 그대로 쓰되 부팅 때 CXL 여부를 정해야** → Flex Bus 협상(LTSSM 확장, TS1/TS2 modified OS). 협상 실패는 PCIe 폴백.
2. **설정/DMA는 PCIe 그대로, 일관성·메모리는 새 프로토콜이어야** → .io(PCIe TLP) + .cache + .mem의 분리.
3. **세 프로토콜이 한 링크를 공유해야** → ARB/MUX가 시분할 다중화 + vLSM으로 프로토콜별 가상 링크 상태 관리.

---

## 3. 작은 예 — CXL.cache로 한 cacheline을 Shared로 읽기

가장 단순한 일관성 시나리오. 가속기(Device)가 호스트 메모리의 한 cacheline을 Shared 상태로 읽어 온다.

### 단계별 다이어그램

```d2
direction: down

D1: "**Device**\n① D2H Req\n(RdShared, Address)"
H1: "**Host**\n② Cache/Directory lookup\n+ coherency check\n+ GO 보장 준비"
H2: "**Host**\n③ H2D Rsp (GO-S: Shared)\n④ H2D Data (Cacheline)"
D2: "**Device**\n⑤ GO + Data 수신\n→ 캐시에 Shared로 저장"

D1 -> H1: "D2H Req 채널"
H1 -> H2
H2 -> D2: "H2D Rsp + H2D Data 채널"
```

### 단계별 의미

| Step | 누가 | 채널 | 무엇을 | 왜 |
|---|---|---|---|---|
| ① | Device | D2H Req | `RdShared(Address)` 요청 | 호스트 메모리를 Shared로 캐싱하려 함 |
| ② | Host | (내부) | 디렉토리/캐시 확인, 코히어런시 처리 | 다른 캐시의 상태 확인 |
| ③ | Host | H2D Rsp | `GO-S` (Global Observation, Shared) | "일관성 있게 관측됨" 보장 |
| ④ | Host | H2D Data | Cacheline 데이터 전달 | 실제 데이터 |
| ⑤ | Device | (내부) | GO+Data 수신 후 Shared로 저장·사용 | GO 이전엔 사용 금지 |

핵심은 **요청(Req)·응답(Rsp)·데이터(Data) 채널이 분리**되어 있다는 점입니다. GO(응답)와 데이터가 별도 채널로 오므로, 디바이스는 둘을 모두 받은 뒤에야 cacheline을 안전하게 사용할 수 있습니다.

```text
Device                                Host
  |  (1) D2H Req (RdShared, Address)    |
  |------------------------------------>|
  |                     Cache/Directory |
  |                     lookup + check  |
  |  (2) H2D Rsp (GO-S: Shared)         |
  |<------------------------------------|
  |  (3) H2D Data (Cacheline)           |
  |<------------------------------------|
  |  Store as Shared in cache           |
```

:::note[여기서 잡아야 할 두 가지]
**(1) CXL.cache는 방향이 디바이스 기준이다.** D2H = Device-to-Host(가속기가 요청), H2D = Host-to-Device(호스트가 응답/snoop). "가속기가 호스트를 캐싱"하는 프로토콜이라 디바이스가 요청 주체.<br>
**(2) Req/Rsp/Data 채널 분리 + GO 보장.** 응답(GO)과 데이터가 다른 채널이며, GO 수신 전 데이터 사용은 프로토콜 위반.
:::
---

## 4. 일반화 — 세 프로토콜의 채널 구조

### 4.1 CXL.io — PCIe TLP 그대로

CXL.io는 PCIe TLP/DLLP 기반입니다. enumeration, configuration access, 인터럽트, 일부 DMA를 처리하며, CXL이 새로 정의한 것이 아니라 PCIe를 그대로 빌려옵니다. CXL 3.1에서는 패브릭 라우팅을 위한 **PBR TLP Header(PTH)** 가 추가됩니다(M04).

### 4.2 CXL.cache — D2H / H2D (가속기 ↔ 호스트 일관성)

가속기가 호스트 메모리를 일관성 유지하며 캐싱하기 위한 프로토콜입니다. 방향은 **디바이스 기준**입니다.

| 채널 | 방향 | 용도 |
|------|------|------|
| D2H Req | 장치 → 호스트 | 요청 (예: RdShared) |
| D2H Rsp | 장치 → 호스트 | 응답 |
| D2H Data | 장치 → 호스트 | 데이터 |
| H2D Req | 호스트 → 장치 | 요청 (Snoop 등) |
| H2D Rsp | 호스트 → 장치 | GO 등 응답 |
| H2D Data | 호스트 → 장치 | 데이터 |

### 4.3 CXL.mem — M2S / S2M (호스트 ↔ 디바이스 메모리)

호스트가 디바이스의 로컬 메모리(HDM)를 Load/Store로 접근하기 위한 프로토콜입니다. 방향은 **Master(호스트) / Subordinate(디바이스 메모리) 기준**입니다.

| 채널 | 방향 | 용도 |
|------|------|------|
| M2S Req | Master → Subordinate | 호스트 읽기/메타 요청 |
| M2S RwD | Master → Subordinate | 호스트 쓰기 + 데이터 |
| S2M NDR | Subordinate → Master | No-Data Response |
| S2M DRS | Subordinate → Master | Data Response |
| S2M BISnp | Subordinate → Master | Back-Invalidate Snoop (CXL 3.0+) |

### 4.4 세 프로토콜 한눈 비교

| 프로토콜 | 기반/방향 | 누가 요청 주체 | 용도 |
|---|---|---|---|
| CXL.io | PCIe TLP | 호스트(enumeration) | 설정, 인터럽트, DMA, 발견 |
| CXL.cache | D2H / H2D | 디바이스(가속기) | 가속기가 호스트 메모리 일관성 캐싱 |
| CXL.mem | M2S / S2M | 호스트(Master) | 호스트가 디바이스 메모리 Load/Store |

방향이 헷갈리기 쉽습니다. **.cache는 디바이스가 호스트를 보고(D2H), .mem은 호스트가 디바이스 메모리를 본다(M2S).** "누가 누구의 메모리를 접근하느냐"를 기준으로 잡으면 정리됩니다.

---

## 5. 디테일 — Flex Bus 협상, Flit 모드, 링크 계층

### 5.1 Flex Bus 모드 협상

CXL은 부팅 시 PCIe와 동일한 LTSSM을 거치되, 협상 과정에서 CXL 지원 여부를 확인합니다.

```text
1. Host ↔ Device: 2.5 GT/s (PCIe 호환 속도)에서 시작
2. Host → Device: TS1 OS 송신 (Modified, CXL Capable bit 포함)
3. Device → Host: TS2 OS 응답 (CXL Capable 표시)
4. 양측 CXL 지원 확인 후 속도 협상
5. 8 GT/s 이상 진입 성공 → CXL 모드 (.io + .cache + .mem)
6. 진입 실패 → PCIe Native 모드로 자동 폴백
```

여기서 핵심은 **수정된 TS1/TS2 Ordered Set** 을 통해 CXL Capable bit을 교환한다는 점과, 8 GT/s 이상 진입에 실패하면 **자동으로 PCIe로 폴백**한다는 점입니다. Flex Bus의 물리적 호환성 — PCIe Electricals, Connector, Retimer를 그대로 활용 — 덕분에 보드 재설계 없이 같은 슬롯에서 두 모드가 가능합니다.

| 항목 | 설명 |
|------|------|
| 물리적 호환성 | PCIe Electricals, Connector, Retimer 그대로 활용 → 보드 재설계 불필요 |
| Alternate Protocol Negotiation | 부팅 시 2.5 GT/s에서 LTSSM, 수정된 TS1/TS2 OS로 CXL 지원 확인 |
| Fallback | 8 GT/s 이상 진입 실패 시 자동 PCIe 모드 전환 |

### 5.2 Link Layer — 두 갈래

링크 계층은 프로토콜에 따라 둘로 갈립니다. CXL.io는 PCIe의 Data Link Layer(DLL)를 그대로 쓰고, CXL.cache와 CXL.mem은 공통의 **CXL.cachemem LL** 에서 Flit 단위로 패킹됩니다.

:::note[왜 .cache/.mem은 공통 LL이고 .io만 PCIe DLL인가]
세 프로토콜이 굳이 두 종류의 link layer로 갈리는 데는 *요구하는 특성이 다르다* 는 이유가 있습니다.

CXL.cache/.mem은 본질적으로 **메모리·coherency 트래픽** 입니다 — Load/Store와 snoop은 코어를 stall시키는 critical path 위에 있어, latency 한 푼이 곧 성능입니다. 그래서 이들은 *고정 포맷의 작은 단위(Flit)* 를 *저지연* 으로 끊임없이 흘려보내야 합니다. PCIe DLL은 이 용도에 맞지 않습니다 — PCIe는 *가변 길이 TLP* 를 다루고, 신뢰성을 위해 ACK/NAK 기반의 무거운 replay(전체 TLP 재전송) 메커니즘과 큐잉을 전제로 합니다. 가변 포맷은 파싱이 더 걸리고, TLP 단위 replay는 latency 변동(jitter)을 키웁니다. 메모리 트래픽에 이 오버헤드를 그대로 씌우면 저지연 목표가 깨집니다.

그래서 CXL은 .cache/.mem을 위해 *별도의 flit 기반 LL* 을 둡니다 — 고정 크기 Flit(68B/256B), 그 안에 여러 메시지를 슬롯으로 packing, 그리고 flit 단위의 경량 신뢰성(CRC + LLR retry, §5.3)을 씁니다. 고정 포맷이라 디코딩이 빠르고 예측 가능하며, flit 단위 retry는 TLP 단위보다 가볍습니다. 반면 CXL.io는 enumeration·config·DMA처럼 *PCIe 의미 그대로* 가 필요하고 latency도 덜 민감하므로, 검증·호환성 측면에서 이득이 큰 PCIe DLL을 그대로 재사용합니다. 즉 LL이 둘로 갈린 것은 "저지연 고정포맷 메모리 트래픽" 과 "PCIe 호환 가변 TLP 트래픽" 의 요구 차이가 만든 결과입니다.
:::

```text
====== 68B Flit (CXL 1.1 / 2.0) ======
+----------+-------------------------------------+--------+
| Proto ID |          Payload (4 Slots)          |  CRC   |
|  16-bit  |  Slot0   Slot1   Slot2   Slot3      | 16-bit |
+----------+-------------------------------------+--------+
                        68 Bytes total

====== 256B Flit (CXL 3.0+) ======
+--------+--------------------------------------+--------+-----+
| Header |      Payload (multi-message)         |  CRC   | FEC |
|   6B   |            240 Bytes                 |   8B   |  2B |
+--------+--------------------------------------+--------+-----+
                       256 Bytes total
```

68B Flit은 CXL 1.1/2.0의 기본 단위로, 16-bit Proto ID + 4개 16B Slot + 16-bit CRC로 구성됩니다. CXL 3.0+의 256B Flit은 헤더에 멀티메시지 페이로드를 담고 FEC(Forward Error Correction)를 포함하는데, 이는 PAM4 시그널링(M05)에서 신호 마진이 줄어든 것을 보상하기 위함입니다. 256B에는 Half-Flit을 조기 디코딩하는 Latency-Optimized 변형도 있어 지연을 더 줄입니다.

:::note[flit이 커지면 FEC는 이득, latency는 손해 — 그래서 half-flit이 생겼다]
68B에서 256B로 flit이 커진 데는 인과가 있습니다. 핵심은 **FEC(오류 정정 코드)의 효율은 flit이 클수록 좋아진다** 는 점입니다. FEC는 매 flit에 정정용 redundancy(parity)를 붙이는데, 작은 flit에 충분한 FEC를 넣으면 redundancy 비율이 높아 대역폭 낭비가 큽니다. 큰 flit(256B)에 FEC를 묶으면 같은 정정 능력을 *더 낮은 오버헤드 비율* 로 얻습니다 — 큰 블록에 한 번 강한 코드를 거는 것이 효율적입니다. PAM4(M05)로 raw 오류율이 올라간 고속 세대에서 FEC가 사실상 필수가 되자, FEC를 감당할 만한 큰 flit이 자연스러운 선택이 됩니다.

그런데 *큰 flit에는 대가* 가 따릅니다 — **small-message latency** 입니다. flit은 어느 정도 채워져야 전송·정정·디코딩이 시작되는데, 작은 메시지 하나(예: snoop 한 건)를 보내려 해도 256B flit이 *채워지거나 마감될 때까지* 기다려야 하고, 수신 측도 flit 전체와 FEC를 받아야 디코딩을 끝냅니다. 즉 큰 flit은 대역폭 효율·오류 내성은 좋지만, 작고 latency-민감한 coherency 메시지에는 "채워질 때까지의 대기" 가 그대로 지연으로 더해집니다.

이 상충을 풀려고 나온 것이 **Latency-Optimized(half-flit) 변형** 입니다. 256B flit을 절반(half)으로 나눠, 앞쪽 half가 도착·검사되면 *전체 flit을 다 기다리지 않고* 그 절반을 먼저 디코딩·처리합니다. FEC의 효율(큰 flit)은 유지하면서, 작은 메시지가 flit 전체 완성을 기다리는 latency 페널티를 줄이는 절충입니다. 정리하면: flit↑ → FEC 효율↑ + small-message latency↑ 라는 trade-off가 있고, half-flit은 그 latency 쪽을 되찾기 위한 장치입니다.
:::

### 5.3 Link Layer Retry (LLR) — HW 수준 신뢰성

전송 오류가 나면 송신 측 Retry Buffer에 저장된 Flit을 재전송합니다.

```text
1. Sender가 Flit N, N+1, N+2 송신 (Retry Buffer에 보관)
2. Receiver: Flit N+2에서 CRC Mismatch 감지
3. Receiver → Sender: RETRY.Req (N+2부터 재전송 요청)
4. Sender: Retry Buffer에서 N+2부터 재전송
5. Receiver: 정상 수신 → ACK
6. Sender: ACK된 Flit을 Retry Buffer에서 제거
```

이 LLR은 소프트웨어 개입 없이 링크 계층에서 오류를 복구하므로, 검증 시 CRC 주입 → RETRY.Req → 재전송 → ACK 시퀀스가 올바른지를 점검 대상으로 삼습니다.

---

## 6. 흔한 오해 와 DV 디버그 체크리스트

### 흔한 오해

:::danger[❓ 오해 1 — '.cache와 .mem은 둘 다 메모리 접근이니 거의 같다']
**실제**: 방향과 주체가 정반대입니다. **.cache(D2H)는 가속기가 호스트 메모리를 캐싱**하고, **.mem(M2S)는 호스트가 디바이스 메모리를 접근**합니다. 트랜잭션을 추적할 때 방향을 헷갈리면 엉뚱한 채널을 봅니다.<br>
**왜 헷갈리는가**: 둘 다 "메모리 읽기"라는 표면적 유사성 때문에.
:::
:::danger[❓ 오해 2 — 'CXL 디바이스를 꽂으면 무조건 CXL 모드로 동작한다']
**실제**: Flex Bus 협상에서 양단 CXL 지원 확인 + 8 GT/s 이상 진입에 성공해야 CXL 모드입니다. 실패하면 **PCIe Native로 폴백**합니다. 링크가 PCIe로만 올라오면 협상 단계부터 의심.<br>
**왜 헷갈리는가**: "CXL 카드 = CXL 동작"이라는 단순화 때문에.
:::

### DV 디버그 체크리스트

| 증상 | 1차 의심 | 어디 보나 |
|---|---|---|
| Scoreboard가 응답 없이 hang | .cache/.mem 채널 혼동 — 엉뚱한 채널 모니터링 | 트랜잭션 방향(D2H/H2D vs M2S/S2M) 재확인 |
| CXL 미동작, PCIe만 링크업 | Flex Bus 협상 실패, 8 GT/s 미진입 | LTSSM 로그, TS1/TS2 CXL Capable bit |
| 데이터는 왔는데 디바이스가 안 씀 | GO(H2D Rsp) 미수신 — Rsp/Data 채널 분리 | H2D Rsp 채널의 GO 발행 여부 |
| CRC 오류 후 데이터 손실 | LLR 재전송 시퀀스 미동작 | Retry Buffer, RETRY.Req/ACK 흐름 |

---

## 7. 핵심 정리 (Key Takeaways)

- **4계층 스택**: Transaction(.io/.cache/.mem) → Link(io LL / cachemem LL) → ARB/MUX(다중화) → Physical(LTSSM, Flex Bus).
- **Flex Bus 협상**: 2.5 GT/s 시작 → 수정된 TS1/TS2 OS로 CXL Capable 교환 → 8 GT/s 이상 성공 시 CXL 모드, 실패 시 PCIe 폴백.
- **세 프로토콜의 방향**: .io(PCIe TLP), .cache(D2H/H2D — 가속기가 호스트 캐싱), .mem(M2S/S2M — 호스트가 디바이스 메모리 접근).
- **채널 분리 + GO**: Req/Rsp/Data가 별도 채널이며, GO(Global Observation) 수신 전 데이터 사용 금지.
- **Flit 모드**: 68B(1.1/2.0), 256B + FEC(3.0+), Latency-Optimized Half-Flit. LLR로 HW 수준 재전송.

:::caution[실무 주의점]
- 트랜잭션 추적 전에 **누가 누구의 메모리를 접근하는지**부터 정하라 — 그래야 .cache인지 .mem인지, 어느 방향 채널인지가 정해진다.
- CXL 미동작 디버그는 항상 Flex Bus 협상 단계(폴백 여부)부터 — 상위 프로토콜을 보기 전에.
:::
### 7.1 자가 점검

:::tip[🤔 Q1 — 채널 방향 추적 (Bloom: Trace)]
"가속기가 자신의 로컬 메모리에 호스트가 쓴 값을 호스트가 다시 읽는다." 이 동작은 어느 프로토콜·어느 채널로 흐르는가?
<details>
<summary>정답</summary>

- 가속기의 로컬 메모리(HDM)를 **호스트가 접근**하므로 **CXL.mem**.
- 호스트(Master)가 디바이스 메모리(Subordinate)를 읽으므로 **M2S Req**로 요청.
- 디바이스 메모리는 데이터를 **S2M DRS(Data Response)** 로 돌려줌. 데이터 없는 응답이면 S2M NDR.
- 주의: 이건 .cache가 아님 — .cache는 가속기가 *호스트* 메모리를 캐싱하는 반대 방향.

</details>
:::
:::tip[🤔 Q2 — Flex Bus 협상 실패 (Bloom: Evaluate)]
CXL 디바이스를 꽂았는데 링크가 PCIe Native로만 올라왔다. 가능한 원인과 확인 순서를 평가하라.
<details>
<summary>정답</summary>

- **원인 후보**: (1) 디바이스/호스트 한쪽이 CXL 미지원(TS1/TS2의 CXL Capable bit 미설정), (2) 8 GT/s 이상 진입 실패로 자동 폴백, (3) 보드 신호 무결성 문제로 고속 진입 불가.
- **확인 순서**: LTSSM 로그에서 (a) 수정된 TS1/TS2 OS 교환과 CXL Capable bit 확인 → (b) 속도 협상이 8 GT/s 이상 도달했는지 → (c) Recovery 단계에서 폴백 분기 발생 여부.
- 협상은 8 GT/s 이상 성공이 CXL 모드의 전제이므로, 속도 진입 실패가 가장 흔한 폴백 트리거.

</details>
:::
### 7.2 출처

**External**
- *CXL 3.1 Specification* §3 (Transaction Layer), §4 (Link Layer), §6 (Flex Bus Physical) — CXL Consortium
- *PCI Express Base Specification* — LTSSM, Ordered Sets

---

## 다음 모듈

→ [Module 03 — 디바이스 타입 & Coherency](../03_device_types_coherency/): 세 프로토콜을 어떻게 조합하느냐가 디바이스 타입(Type 1/2/3)을 정한다. HDM 유형과 Bias-based coherency, BISnp를 본다.

[퀴즈 풀어보기 →](../quiz/02_flexbus_protocols_quiz/)
