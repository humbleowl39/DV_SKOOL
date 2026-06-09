---
title: "Module 02 — 3-Layer Architecture"
---

:::tip[학습 목표]
이 모듈을 마치면:

- **Diagram** PCIe 의 3 계층 (Transaction / Data Link / Physical) 과 sub-block 을 그릴 수 있다.
- **Distinguish** 각 layer 가 처리하는 packet 단위 (TLP / DLLP / Ordered Set + symbol) 을 구분한다.
- **Trace** memory write 가 application → TLP → DLL 추가 (sequence #, LCRC) → PHY 추가 (STP/END, encoding) 까지 가는 흐름을 추적한다.
- **Apply** 각 layer 의 책임 분리가 디버그/검증에서 어떤 이점을 주는지 시나리오에 매핑한다.
- **Justify** PCIe 의 "신뢰성은 DLL 의 일" 이라는 명제를 PHY BER ≠ 0 이라는 사실과 함께 정당화한다.
:::
:::note[사전 지식]
- Module 01 (point-to-point + lane 모델)
- 일반 OSI 계층 개념
:::
---

## 1. Why care? — 이 모듈이 왜 필요한가

### 1.1 시나리오 — _LCRC error_ vs _ECRC error_ 의 진단

PCIe error log 한 줄을 마주쳤다고 가정합니다.
```
PCI Express: Correctable error: LCRC error
```

이 줄이 담고 있는 정보는 layer 모델을 알면 즉시 풀립니다. LCRC 의 L 은 Link Layer, 곧 DLL(Data Link Layer)의 책임임을 뜻하고, Correctable 은 DLL 의 ACK/NAK retry 가 자동으로 복구했다는 상태입니다. 따라서 시스템은 이미 복구된 상태이지만, 이 오류가 빈도를 높이고 있다면 PHY 의 신호 품질을 의심해야 합니다. 반면 ECRC error 라면 E 가 End-to-end 를 의미하므로 Transaction Layer 의 일이 되고, Endpoint 의 TLP 생성 버그 또는 RC 의 수신 문제로 진단 방향이 전혀 달라집니다.

같은 "CRC error" 라도 어느 layer 의 CRC 인지에 따라 진단 경로가 완전히 갈립니다. Layer 모델 없이 두 오류를 동일 범주로 묶으면 엉뚱한 RTL 영역을 디버깅하게 됩니다.

**모든 PCIe spec 의 기능 분류와 디버그 분류가 "어느 layer 의 일?"** 에서 출발합니다. AER (Module 07) 의 error class, retry 메커니즘 (Module 04), LTSSM (Module 05) 모두 layer 책임이 명확히 분리된 상태에서 정의됩니다.

이 모듈의 어휘 — **Transaction / Data Link / Physical, TLP / DLLP / Ordered Set, ECRC / LCRC** — 가 이후 모든 packet trace, scoreboard 비교, AER 카운터 해석의 기본 단위. 이 layer 모델을 머리에 정확히 넣어 두면 "이 에러는 LCRC error" 라는 한 줄로 즉시 어느 layer 의 어느 메커니즘이 동작했는지 그릴 수 있게 됩니다.

---

## 2. Intuition — 국제 운송의 3 단계 비유와 한 장 그림

:::tip[💡 한 줄 비유]
**PCIe 3 layer** ≈ **국제 화물 운송의 3 단계**.<br>
**Transaction** = 송장 + 화물 명세 (무엇을 어디로). <br>
**Data Link** = 운송중 분실/파손 보험 (sequence #, LCRC, ACK/NAK). <br>
**Physical** = 실제 운송수단 (트럭, 비행기 = serial link, equalization). <br>
각 단계가 자기 책임만 처리. Transaction layer 는 운송수단을 모르고, Physical 은 화물 내용을 모름.
:::
### 한 장 그림 — 송신 path 와 layer 별 wrapper

```d2
direction: down

TX: "Sender — wrapper 추가" {
  direction: down
  TXAPP: "App\nhost PA 0x10000 에 64 B write"
  TXTL: "Transaction Layer\nTLP = Hdr + Payload + (ECRC?)"
  TXDLL: "Data Link Layer\n+Seq# +LCRC · ACK/NAK"
  TXPL: "Physical Layer\nSTP/END · Scramble+Encode\nLane stripe · SerDes"
  TXAPP -> TXTL
  TXTL -> TXDLL: "TLP"
  TXDLL -> TXPL: "TLP+Seq+LCRC, DLLP"
}
RX: "Receiver — wrapper 제거" {
  direction: down
  RXPL: "Physical Layer\nFrame detect · Decode+Descramble\nLane de-stripe · CDR + EQ"
  RXDLL: "Data Link Layer\nLCRC verify · ACK/NAK 송신"
  RXTL: "Transaction Layer\nTLP 분해 + ECRC 검증"
  RXAPP: "App\n메모리에 적용"
  RXPL -> RXDLL
  RXDLL -> RXTL
  RXTL -> RXAPP
}
TX.TXPL -> RX.RXPL: "wire"
RX.RXDLL -> TX.TXDLL: "ACK/NAK" { style.stroke-dash: 4 }
```

세 layer 가 각자의 wrapper 를 추가/제거. **wrapper 추가는 송신, 제거는 수신** — 이 layered 구조 덕에 디버그가 직선화됩니다.

### 왜 이렇게 설계됐는가 — Design rationale

PCIe 가 풀어야 하는 세 문제는 _서로 다른 시간 척도_ 에 있습니다.

1. **무엇을 어디로 보낼까** (transaction) — μs ~ ms 단위, application 의 의도.
2. **이 packet 이 깨졌나, 다시 보낼까** (data link) — ns ~ μs 단위, 매 packet.
3. **이 bit 가 1 인가 0 인가** (physical) — ps ~ ns 단위, 매 symbol.

세 문제를 한 모듈로 풀려고 하면 디버그가 불가능 — 시간 단위가 다른 사건이 섞여 보입니다. **분리된 layer + 명시적 wrapper** 가 이 문제를 풀고, 각 layer 가 다른 hardware/protocol 발전 속도를 흡수할 수 있게 만듭니다 (예: Gen6 의 PAM4/FEC 변경은 PHY 만 손대고 TLP 는 그대로).

---

## 3. 작은 예 — 64 byte MWr 한 개가 3 layer 를 내려가는 과정

가장 단순한 시나리오. Device core 가 host PA `0x10000` 에 **64 byte** 를 write.

```d2
direction: down

TX: "Sender" {
  direction: down
  CORE: "Device Core\nhost PA 0x10000 에 64 B write 요청"
  TXTL: "TL (tx)\nMWr TLP 생성\nFC credit 차감 (P), ECRC 옵션"
  TXDLL: "DLL (tx)\nSeq# = 0x123, LCRC 계산\nReplay Buffer 에 저장"
  TXPL: "PL (tx)\nSTP/END framing\n128b/130b + scramble + lane stripe\nSerDes → wire"
  CORE -> TXTL
  TXTL -> TXDLL
  TXDLL -> TXPL
}
WIRE: "Wire" { shape: oval }
RX: "Receiver" {
  direction: down
  RXPL: "PL (rx)\nCDR · lane de-stripe\n130b→128b decode · descramble"
  RXDLL: "DLL (rx)\nLCRC 검증\nOK → ACK DLLP / FAIL → NAK DLLP"
  RXTL: "TL (rx)\nFC credit 반환 · TLP 처리\nmemory write 적용"
  RXPL -> RXDLL
  RXDLL -> RXTL
}
TX.TXPL -> WIRE
WIRE -> RX.RXPL
```

### 단계별 의미

| Step | 누가 | 무엇을 추가/제거 | 왜 |
|---|---|---|---|
| ① | Device core → TL | "write 64B" 의도 → MWr TLP | application 의 추상화 |
| ② | TL | Header (Fmt/Type/Address/Length) + payload + opt ECRC | TLP 의 자기-기술적 (self-descriptive) packet |
| ③ | TL | FC credit 차감 (P credit) | receiver 의 buffer 만큼만 송신 (Module 04) |
| ④ | DLL | Seq# (12-bit) | 순서 보장 + Replay 단위 |
| ⑤ | DLL | LCRC (32-bit) over [Seq# + TLP] | hop-level 무결성 |
| ⑥ | DLL | Replay Buffer 저장 | ACK 받기까지 보관 |
| ⑦ | PL | STP framing token | TLP 의 시작 표시 |
| ⑧ | PL | 128b/130b encoding + scrambling | DC balance + EMI 분산 |
| ⑨ | PL | Lane stripe (byte-wise round-robin) | x4/x16 의 lane 활용 |
| ⑩ | PL → wire | SerDes 직렬화 → differential pair | analog 신호 |
| ⑪ | wire → PL (rx) | CDR + EQ + 역방향 stripe/decode | lane 별 박자 복원 |
| ⑫ | DLL (rx) | LCRC 검증 → ACK DLLP 송신 | reliability 응답 |
| ⑬ | TL (rx) | TLP 분해 → memory write 적용, FC credit 반환 | 의도 실현 |

```c
// Sender 측 layer wrapper 의 pseudo code — 각 layer 가 자기 책임만
struct tlp build_tlp(struct request *req) {
    return (struct tlp){
        .hdr = encode_header(MWr, req->addr, req->length),
        .payload = req->data,
        .ecrc = compute_ecrc_optional(req),
    };
}
struct dll_pkt wrap_dll(struct tlp t, uint16_t seq) {
    return (struct dll_pkt){
        .seq  = seq,
        .tlp  = t,
        .lcrc = crc32_lcrc(seq, t),  // Seq# + TLP 위로
    };
}
void send_phy(struct dll_pkt p) {
    emit_token(STP);
    emit_scrambled_encoded(p, &lane_stripe);  // 128b/130b + lane round-robin
    emit_token(END);
}
```

:::note[여기서 잡아야 할 두 가지]
**(1) 각 layer 가 자기 책임만 처리한다 — Transaction layer 는 PHY 의 BER 을 모르고, Physical 은 TLP 의 의미를 모른다.** 이 추상화 경계가 디버그에서 "어느 layer 의 증상?" 라는 첫 질문의 정당성.<br>
**(2) Wrapper 는 양방향 비대칭이다 — 송신은 추가, 수신은 제거.** TL/DLL/PL 마다 어떤 wrapper 가 추가됐는지 알아야 packet trace 의 byte stream 을 layer 별로 분해해서 읽을 수 있다.
:::
---

## 4. 일반화 — 3 layer 의 책임 분리와 packet 단위

### 4.1 각 layer 의 packet 단위

| Layer | Packet | 길이 | 예 |
|-------|--------|------|----|
| Transaction | **TLP** | 가변 (header 12-16B + payload 0..4096B + opt ECRC 4B) | MRd, MWr, CplD, CfgRd0/1 |
| Data Link | **DLLP** | 8 byte (header + LCRC) | Ack, Nak, FC Init/Update, PM_*, Vendor |
| Physical | **Ordered Set + Symbol** | 가변 | TS1/TS2, FTS, EIOS, EIEOS, SDS, SKP |

→ DLLP 는 Transaction Layer 가 보지 않음. TLP 는 PHY 가 보지 않고 그저 byte stream.

### 4.2 책임 매트릭스

각 layer 가 어떤 책임을 지는지 한눈에 정리하면 아래와 같습니다. 표를 보기 전에 핵심 원칙을 잡아 두면 좋습니다. Transaction Layer 는 "무엇을 어디로 보내는가"에만 집중하고 wire 의 상태를 전혀 모릅니다. Data Link Layer 는 packet 이 이 hop 을 안전하게 건넜는지만 체크하고 payload 의 의미를 해석하지 않습니다. Physical Layer 는 bit 를 운반하는 것 자체가 역할이며 TLP 의 목적지가 어디인지 알 필요가 없습니다.

| 책임 | TL | DLL | PL |
|------|-----|-----|-----|
| 무엇을 어디로 (address, BDF) | ✓ | | |
| Posted/NP/Cpl ordering | ✓ | | |
| Flow Control credit | ✓ | (DLLP 운반) | |
| ECRC (end-to-end) | ✓ | | |
| Sequence Number | | ✓ | |
| LCRC (hop-level) | | ✓ | |
| ACK/NAK + Replay | | ✓ | |
| DL_Active state | | ✓ | |
| Framing (STP/END/SDP) | | | ✓ |
| Encoding/Scrambling | | | ✓ |
| Lane stripe + SerDes | | | ✓ |
| LTSSM + EQ | | | ✓ |

PHY 의 BER 이 아무리 낮아도 0 은 아니기 때문에, 언젠가는 단 한 비트가 깨질 수 있고, 그 순간 LCRC 가 틀어집니다. 그때 재전송을 결정하는 것은 DLL 의 일입니다. **모든 PCIe link 의 retransmission 은 DLL 책임** — PHY 가 신호 품질을 개선해도 packet-level reliability 는 여전히 DLL 이 보장합니다.

:::note[Flow Control은 왜 의미는 TL인데 운반은 DLL(DLLP)인가]
위 책임 매트릭스에서 "Flow Control credit" 이 TL 에 ✓ 가 있고 DLL 칸에는 "(DLLP 운반)" 이라고만 적힌 것이 의아할 수 있습니다. 이 분업에는 layer 를 가로지르는 이유가 있습니다.

credit 이 *의미* 하는 것은 순전히 TL 의 자원입니다 — "수신 측 TL 의 buffer 에 P/NP/Cpl 별로 TLP 가 몇 개·payload 가 몇 byte 더 들어갈 자리가 있는가". 이 buffer 점유는 TLP 를 만들고 소비하는 TL 만 알 수 있는 상태이므로, credit 의 *생성과 해석* 은 TL 의 책임입니다. 송신 TL 은 "상대 TL buffer 에 자리가 있다" 는 credit 이 있을 때만 TLP 를 내보냅니다.

그런데 이 credit 정보를 *상대에게 전달* 하려면 link 위로 무언가를 보내야 합니다. 만약 credit 갱신을 TLP 로 보낸다면, 그 TLP 자체가 다시 credit 을 소비해야 하는 모순(credit 을 받으려고 credit 을 써야 함)에 빠지고, TLP 라면 LCRC 검증·replay 대상이 되어 무겁습니다. 그래서 credit 갱신은 **DLLP(UpdateFC)** 로 운반합니다 — DLLP 는 DLL 이 만들고 *flow control 의 적용을 받지 않으며*, hop-local 로 가볍게 오갑니다. 즉 "이 정보가 무엇을 뜻하는가(TL buffer 점유)" 와 "이 정보를 어떻게 안전하고 가볍게 나르는가(DLL 의 신뢰 채널 DLLP)" 는 다른 layer 의 일이고, 그래서 credit 은 *의미는 TL, 운반은 DLL* 로 갈립니다. (FC 의 동작 메커니즘은 Module 04 에서 상세히 다룹니다.)
:::

### 4.3 디버그 흐름의 직선화

```d2
direction: right

S: "증상 발견"
Q: "어느 layer 의 일인가?"

TL1: "TLP type / address 잘못 → TL"
DLL1: "LCRC error / replay 빈발 → DLL"
PL1: "Link 자체가 안 올라옴\n→ PL (LTSSM)"
BAR1: "Specific BAR 만 fail\n→ TL (header field) + Module 06"
AER1: "AER counter 증가\n→ AER mapping → 해당 layer"

S -> Q
Q -> TL1
Q -> DLL1
Q -> PL1
Q -> BAR1
Q -> AER1
```

증상을 보고 "어느 layer 의 일인가?" 라는 질문 하나를 먼저 던지면, 디버그 경로가 세 갈래로 바로 갈립니다. TLP 의 주소나 타입이 잘못됐다면 TL, LCRC 나 replay 가 빈발한다면 DLL, link 자체가 올라오지 않는다면 PL 로 시선이 좁혀집니다. 이 한 단계의 분류가 _80% 의 디버그 케이스_ 를 해결합니다.

---

## 5. 디테일 — TL / DLL / PL 의 내부 block 과 규칙

### 5.1 3 Layer 한 장 뷰

```d2
direction: down

APP: "Application / Device Core\n(driver, NIC engine, …)"
TL: "Transaction Layer\n· TLP 생성/분해 (header + payload + ECRC)\n· Flow Control credit 관리\n· TLP type / routing / address translation\n· Ordering rules (P/NP/Cpl)"
DLL: "Data Link Layer\n· Sequence Number 부여\n· LCRC 계산 / 검증\n· ACK/NAK 송신, Replay Buffer\n· DLLP (FC update, ACK/NAK, Power)\n· Link state (DL_Inactive / Init / Active)"
PL: "Physical Layer\n· Framing (STP/END, SDP/EDS)\n· Encoding (8b/10b → 128b/130b → PAM4/FLIT)\n· Scrambling, Lane stripe\n· SerDes (Serializer/Deserializer)\n· LTSSM (link training)\n· Equalization, CDR\n· Ordered Sets (TS1/TS2, EIOS, …)"
APP -> TL: "memory request,\ncompletion, message"
TL -> DLL: "TLP"
DLL -> PL: "TLP + Seq# + LCRC, DLLP"
```

### 5.2 Transaction Layer (TL) 책임

```d2
direction: down

CORE: "from device core"
BLD: "TLP Builder\nheader · payload · ECRC"
FC: "Flow Control\ncredit available 확인 후 송신"
ORD: "Ordering\nP / NP / Cpl 규칙"
RT: "TLP Routing / Type\nMRd · MWr · CfgRd · CfgWr · Cpl · Msg"
DLL: "Data Link Layer"
CORE -> BLD
BLD -> FC
FC -> ORD
ORD -> RT
RT -> DLL: "TLP"
```

| 기능 | 핵심 |
|------|------|
| **TLP 생성** | Fmt + Type + Length + Address (or BDF) + payload |
| **Flow Control** | P / NP / Cpl 별 header credit + data credit 추적, FC DLLP 로 갱신 |
| **Ordering** | Posted (P) ↔ Non-Posted (NP) ↔ Completion (Cpl) 의 strict ordering 규칙 (PCI legacy 호환) |
| **ECRC (optional)** | end-to-end CRC. 라우팅 노드에서 변경 안 됨. |
| **Address translation** | ATS 사용 시 IOVA → PA 변환 결과 캐시 |

:::note[ECRC는 왜 optional인가 — hop LCRC로 충분한 경우 vs switch 내부 corruption]
LCRC 가 매 hop 마다 무결성을 보장하는데 왜 ECRC 가 또 필요하고, 게다가 *optional* 일까요? 답은 *위협 모델* 의 차이에 있습니다.

LCRC 는 **wire 위의 한 hop** 을 지킵니다 — 송신 노드가 LCRC 를 붙이고 수신 노드가 검증하므로, 그 link 구간에서 전송 중 비트가 깨지면 잡힙니다. 그런데 switch 는 TLP 를 받아 다음 hop 으로 forward 할 때 *LCRC 를 벗기고 새로 계산해 다시 붙입니다*(hop 마다 LCRC 가 새 것). 만약 switch 가 TLP 를 그대로 통과(store-and-forward)시키며 payload 를 건드릴 일이 없다면, 매 hop 의 LCRC 만으로 끝까지 무결성이 이어집니다 — 이 경우 ECRC 는 군더더기입니다. 그래서 *기본은 optional* 입니다.

문제는 **switch 내부에서 일어나는 corruption** 입니다. TLP 가 switch 의 내부 buffer/SRAM 에 머무는 동안 soft error(예: 우주선에 의한 bit flip)로 payload 가 바뀌면, switch 는 *바뀐 payload 위에 정상 LCRC 를 새로 계산해* 다음 hop 으로 내보냅니다. 각 hop 의 LCRC 는 모두 통과하지만, 최종 수신자가 받는 데이터는 송신자가 보낸 것과 다릅니다 — LCRC 는 이 경로 *중간 노드 내부* 의 오염을 원리적으로 못 잡습니다. **ECRC** 는 송신 TL 이 붙여 수신 TL 이 검증하며 *경로 내내 변경되지 않으므로*, 이런 end-to-end 오염을 검출합니다. 정리하면: LCRC(hop)만으로 충분한 환경이면 ECRC 를 끄고, switch 내부 soft error 같은 routing 노드 corruption 까지 막아야 하는 high-reliability 환경이면 ECRC 를 켭니다 — 그래서 정책에 따라 켜고 끄는 optional 입니다.
:::

### 5.3 Data Link Layer (DLL) 책임

```d2
direction: down

INTL: "from TL: TLP"
SEQ: "Seq# 부여\n12-bit · 0..4095"
LCRC: "LCRC 계산\n32-bit Link CRC"
REPLAY: "Replay Buffer 저장\nACK 받기까지"
ACK: "ACK/NAK 처리"
DLLP: "DLLP 송신\nFC update · ACK/NAK · PM_*"
PL: "Physical Layer"
INTL -> SEQ -> LCRC -> REPLAY -> ACK -> DLLP
DLLP -> PL: "TLP + Seq# + LCRC, DLLP"
```

| 기능 | 핵심 |
|------|------|
| **Sequence Number** | 12-bit, modulo 4096. 송신 순서대로 부여, receiver 의 Next Receive Seq# 와 비교 |
| **LCRC** | 32-bit, TL 의 ECRC 와 별도. Hop-level 무결성 |
| **Replay Buffer** | Sender 가 ACK 받을 때까지 TLP 저장. NAK 시 그 sequence 부터 재전송 |
| **ACK/NAK** | DLLP 로 송신. ACK = 누적 ACK (해당 seq 까지 수신), NAK = error 발생 |
| **DL Control State** | DL_Inactive → DL_Init → DL_Active. DL_Active 에서만 TLP 송수신 |

→ **모든 PCIe link 의 retransmission 은 DLL 책임.**

### 5.4 Physical Layer (PL) 책임

```d2
direction: down

IN: "from DLL:\nTLP + Seq# + LCRC, DLLP"
FRM: "Framing\nSTP/END (Gen1/2)\nSDP/EDS (Gen3+)"
SCR: "Scrambling\nLFSR-based\nEMI 분산"
ENC: "Encoding\n8b/10b (Gen1/2)\n128b/130b (Gen3+)"
STR: "Lane Stripe\nbyte-wise\nround-robin"
SD: "SerDes\n직렬화\ndifferential pair"
WIRE: "Wire /\nconnector" { shape: oval }

LTSSM: "LTSSM\n(link bring-up\nEQ · recovery)"
OS: "Ordered Sets\n(TS1/TS2 · FTS\nEIOS · SKP)"

IN -> FRM -> SCR -> ENC -> STR -> SD -> WIRE: "analog signal"
LTSSM -> OS -> WIRE: { style.opacity: 0.0 }
```

| 기능 | 핵심 |
|------|------|
| **Framing** | TLP 의 시작/끝 표시 (STP=Start TLP, END), DLLP (SDP=Start DLLP, EDS=End Data Stream) |
| **Scrambling** | EMI 줄이기 위해 LFSR XOR. 양 끝이 같은 LFSR seed 로 동기화 |
| **Encoding** | DC balance, clock recovery 가능한 transition 보장 |
| **Lane Stripe** | x16 link 에서 byte 0 → lane 0, byte 1 → lane 1, …, byte 15 → lane 15, byte 16 → lane 0 |
| **SerDes** | Tx FIFO + serializer + driver / Rx CDR + deserializer + EQ |
| **LTSSM** | 11 state link training + recovery + L0s/L1 entry |
| **Ordered Sets** | TS1/TS2 = training, FTS = fast training, EIOS = electrical idle, SKP = clock comp |

:::tip[차동 신호 (Differential Signaling) 의 노이즈 제거 — 정량 예시]
한 lane 은 TX 2 가닥 + RX 2 가닥 = **총 4 핀** (TX+/TX-/RX+/RX-). 송신 시 데이터를 정상 신호(+) 와 역상 신호(-) 두 개로 나눠 한 쌍으로 송출.

예: 송신 (+0.1V, -0.1V) → **차이 = 0.2V** = 1 로 해석.

중간에 외부 노이즈가 두 선에 동시에 +0.5V 더해진다고 가정 → 도착 시 (+0.6V, +0.4V).

수신 측은 **두 신호의 차이만** 계산: 0.6 − 0.4 = **0.2V**. 노이즈는 상쇄되고 원래 값 그대로.

덕분에 PCIe 는 **수백 mV 수준의 매우 작은 전압 차이** 로도 안정적 통신 가능 — 저전압 + 고속화의 토대.
:::
:::tip[8b/10b vs 128b/130b — encoding 의 본질]
**연속된 0 또는 1 의 공포**: `00000000` 처럼 변화 없는 데이터가 길게 흐르면 수신 측 CDR 이 박자 (clock edge) 를 잃어 동기화 실패.

**8b/10b (Gen1, Gen2) — Lookup Table 방식**:

- 8 bit 데이터 → 사전에 약속된 10 bit 코드로 변환.
- 연속된 0 또는 1 의 길이를 5 개 이하로 제한 + DC balance (0/1 갯수 동일).
- 1 bit 가 아닌 2 bit 추가 이유 — DC 균형 + K-Code (`COM`, `SKP` 등 제어 패턴) 공간 확보. 9 bit (512 조합) 으로는 256 데이터 모두에 대해 DC 균형이 수학적으로 불가.
- 대가: **20% 대역폭 오버헤드**.

**128b/130b (Gen3+) — LFSR 스크램블링 방식**:

- 송수신 양쪽이 같은 LFSR 알고리즘으로 데이터를 무작위 섞음 (encoding table 폐기).
- 무작위 섞인 데이터는 0 또는 1 이 길게 이어질 확률이 매우 낮아짐.
- 추가된 2 bit 의 역할은 에러 검사 아님 — **Sync Header**: "이 128 bit 가 데이터인지 제어 명령인지" 구분.
- 결과: **오버헤드 20% → 1.5%**.
- 가능해진 배경: 정밀해진 CDR + 강력한 EQ (Module 05 참조).
:::
### 5.5 송신 흐름 — Memory Write 예 (전체)

위 §3 의 시나리오를 시간 축으로 다시:

```d2
shape: sequence_diagram

Core: "Device Core"
TX: "Sender (TL/DLL/PL)"
RX: "Receiver (PL/DLL/TL)"

Core -> TX: "host PA 0x10000 에 64 B write 요청"
TX -> TX: "TL — MWr TLP 생성, FC credit 차감, ECRC 옵션"
TX -> TX: "DLL — Seq# + LCRC + Replay Buffer"
TX -> TX: "PL — Framing + 128b/130b + scramble\n+ lane stripe → SerDes"
TX -> RX: "wire"
RX -> RX: "PL — CDR, decode, descramble, framing detect"
RX -> RX: "DLL — LCRC 검증 OK"
RX -> TX: "ACK DLLP" { style.stroke-dash: 4 }
RX -> RX: "TL — FC credit 반환, memory write 적용"
```

### 5.6 수신 측 ACK/NAK 의 layer 분리

```d2
direction: down

A: "PL 가 깨진 비트 받음"
B: "DLL 의 LCRC 검증 fail"
C: "DLL 이 NAK DLLP (with seq# = next expected) 전송\nPHY 통해 sender 로 가지만 PHY 가 만든 게 아님"
D: "Sender DLL 이 NAK 받음\nReplay Buffer 에서 해당 Seq# 부터 다시 송신"
E: "Replay 횟수 한도 초과\n→ DL_Inactive → LTSSM Recovery 진입"
A -> B
B -> C
C -> D
D -> E
```

→ **Layer 책임 분리의 가치**: TLP (TL) 는 retransmit 을 신경 쓰지 않음. DLL 은 LCRC 만 보고 packet 단위 reliability 만 처리. PHY 는 그저 bit 운반.

### 5.7 디버그 시 layer 추적

| 증상 | 의심 layer | 확인 |
|------|----------|------|
| Link up 안 됨 | PHY (LTSSM) | LTSSM state, equalization 결과, electrical idle |
| Link up 했지만 packet 안 감 | DLL | DL_Active 진입 여부, FC init complete 여부 |
| TLP 가 가지만 receiver 가 못 받음 | DLL/TL | LCRC error 율, Seq# wraparound, Replay 횟수 |
| Specific TLP 만 fail | TL | Header field 오류 (Fmt/Type/Address), ECRC, ordering 위반 |
| Latency 가 spike | TL/DLL | FC credit 부족, replay 발생 빈도 |
| AER correctable error 카운터 ↑ | DLL/PHY | LCRC, replay number rollover, bad symbol |

---

## 6. 흔한 오해 와 DV 디버그 체크리스트

### 흔한 오해

:::danger[❓ 오해 1 — 'PCIe 의 reliability 는 PHY 가 책임진다 (BER 낮음)']
**실제**: Physical 은 raw bit 만 운반하며, **packet-level reliability 는 Data Link Layer 의 ACK/NAK + sequence # + replay buffer** 가 보장. PHY 의 BER 이 아무리 낮아도 0 은 아니므로, 단일 비트 오류가 LCRC 에서 검출되면 DLL 이 재전송. 즉 **PCIe 의 retransmission 은 DLL 의 일**.<br>
**왜 헷갈리는가**: 일반적으로 "신뢰성 = 물리 quality" 로 단순 연결 짓기 쉬움.
:::
:::danger[❓ 오해 2 — 'LCRC 와 ECRC 는 같은 CRC 다']
**실제**: 둘 다 32-bit CRC 지만 generator polynomial 이 다르고 _범위/책임_ 이 다름. **LCRC** 는 hop 마다 새로 계산 (DLL 책임), **ECRC** 는 end-to-end (TL 책임, optional). Switch 가 TLP forward 할 때 LCRC 는 매 hop 새로 계산하지만 ECRC 는 그대로 둠 — 그래서 ECRC error 는 path 중간 어디선가의 corruption 을 잡아낸다.<br>
**왜 헷갈리는가**: 둘 다 32-bit, 둘 다 TLP 위에 계산.
:::
:::danger[❓ 오해 3 — 'Memory Write 는 ACK 가 없으니 unreliable 하다']
**실제**: PCIe 의 MWr 은 **TL-level Posted** = TL 응답 없음. 그러나 **DLL 의 ACK/NAK 은 발생** — receiver 의 DLL 이 packet 을 정상 받으면 ACK DLLP 가 sender 로 가고 Replay buffer 에서 해당 entry 가 retire. 따라서 **link-level 신뢰성은 보장**, 단지 application-level "내 write 가 정말 처리됐는가" 는 별도 확인 필요 (Module 03).<br>
**왜 헷갈리는가**: "Posted" 와 "응답 없음" 을 link 전체로 해석.
:::
:::danger[❓ 오해 4 — 'TLP, DLLP 는 같은 channel 의 다른 이름이다']
**실제**: TLP 는 Transaction layer 의 packet, DLLP 는 Data Link layer 의 packet. PHY 위에서는 둘 다 byte stream 이지만 **framing token 이 다름** — TLP 는 STP/END (Gen1/2) 또는 SDP-like (Gen3+), DLLP 는 별도 framing. Trace 도구가 layer 별 column 을 안 보여주면 ACK/NAK timing 추적 불가.
:::
:::danger[❓ 오해 5 — 'Layered 라서 layer 끼리 완전히 독립적이다']
**실제**: 송신 path 의 wrapper 는 _layered_ 지만, 일부 정보는 layer 경계를 넘어 흐른다. 예: DLL 의 FC DLLP 는 sender 의 TL 이 송신 가능 여부 판단에 사용. AER 은 PHY/DLL 의 error 를 TL 의 capability 로 reporting. **Layer 분리 = 책임 분리이지 정보 단절은 아님**.
:::
### DV 디버그 체크리스트 (이 모듈 내용으로 마주칠 첫 실패들)

| 증상 | 1차 의심 | 어디 보나 |
|---|---|---|
| Link 가 LTSSM L0 에 못 감 | PHY (LTSSM stuck) | LTSSM trace, Detect/Polling/Configuration 어디서 멈췄나 (Module 05) |
| L0 진입했지만 packet 0 | DLL (DL_Inactive 또는 FC init 미완료) | DL_Active 진입 여부, InitFC1/2 교환 |
| LCRC error 카운트 증가 | PHY BER 또는 DLL 송신 측 LCRC 계산 버그 | AER correctable counter, replay 횟수 |
| Specific TLP 만 UR | TL header field (Fmt/Type/Address) | Packet trace, TL 의 routing 결과 |
| Replay buffer overflow → recovery | ACK 가 늦거나 NAK 빈발 | DLL 양쪽의 ACK timer + LCRC error rate |
| Switch 통과한 TLP 의 ECRC fail | path 중간 corruption | switch 의 cut-through vs store-forward, 두 LCRC error 패턴 |
| Gen 변경 시 packet drop | LTSSM Recovery + DLL state 동시 처리 | LTSSM trace 와 DLL state 동기화 |
| AER correctable counter 가 천천히 증가 | PHY BER 악화 trend | EQ margin, replay 통계 (Module 07) |

---

## 7. 핵심 정리 (Key Takeaways)

- PCIe 는 **Transaction / Data Link / Physical** 3 층 + 명확한 책임 분리.
- 각 layer 의 packet 단위: TLP / DLLP / Ordered Set + Symbol.
- Reliability 는 **DLL 의 ACK/NAK + Sequence # + Replay Buffer** 로 보장. PHY 의 BER 은 별개 layer 의 문제.
- 송신 path 는 layer 마다 wrapper 추가, 수신 path 는 역순 stripping.
- Layer 분리 덕분에 디버그가 "증상 → layer → field" 의 직선적 흐름.

:::caution[실무 주의점]
- "TLP" 와 "DLLP" 의 구분이 흐려지는 도구가 있음 — packet trace tool 에서 DLLP 를 별도 column 으로 보지 않으면 ACK/NAK timing 추적 불가.
- LCRC 와 ECRC 를 혼동하지 말 것 — LCRC 는 hop, ECRC 는 end-to-end. 둘 다 32-bit CRC 지만 generator polynomial 이 다름.
- Replay buffer 의 size 는 spec 가 아니라 implementation. 작으면 RTT 큰 link 에서 sender stall 발생 (credit 처럼).
- Gen6 FLIT 모드에서는 layer boundary 가 살짝 변경됨 — TLP/DLLP 가 FLIT 안에 함께 들어가 ACK/NAK 메커니즘이 단순화. 자세한 건 Module 04.
:::
### 7.1 자가 점검

:::tip[🤔 Q1 — LCRC vs ECRC (Bloom: Analyze)]
한 packet 의 LCRC 통과, ECRC fail. _어느 layer_ 의 _어떤 시나리오_?

<details>
<summary>정답</summary>

- LCRC 통과 → DLL 의 _link integrity OK_ → wire 전송 자체는 무결.
- ECRC fail → end-to-end 어딘가에서 _data corruption_:
    - Endpoint 의 TLP 생성 시 bug.
    - RC 또는 switch 가 _routing 중_ TLP payload 변경 (예: NAT-like).
    - Memory 의 ECC 처리 실패.

LCRC 만 보면 _안전_ 같지만 ECRC 가 catch.

</details>
:::
:::tip[🤔 Q2 — Layer boundary 책임 (Bloom: Apply)]
AER (Module 07) 가 _correctable error_ 를 카운트. 어느 layer 의 어떤 error?

<details>
<summary>정답</summary>

- **Receiver Error**: PHY layer (8b/10b encoding error, symbol error).
- **Bad TLP / Bad DLLP**: DLL layer (LCRC error).
- **Replay Num Rollover / Timer Timeout**: DLL.

모든 layer 가 _자체 error counter_ → AER 통합. 어느 layer 가 _주된 error source_ 인지 즉시 분류.

</details>
:::
### 7.2 출처

**External**
- PCIe Specification 5.0/6.0
- *PCI Express Technology* — MindShare

---

## 다음 모듈

→ [Module 03 — TLP](../03_tlp/): TL 의 packet (TLP) 의 header 필드, Fmt/Type 인코딩, P/NP/Cpl ordering, routing 3 가지.

[퀴즈 풀어보기 →](../quiz/02_layer_architecture_quiz/)
