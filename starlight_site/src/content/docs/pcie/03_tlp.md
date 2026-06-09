---
title: "Module 03 — TLP (Transaction Layer Packet)"
---

:::tip[학습 목표]
이 모듈을 마치면:

- **Decode** TLP header (3DW vs 4DW, Fmt/Type/TC/Length/Address) 의 각 필드를 식별한다.
- **Classify** TLP 를 Posted / Non-Posted / Completion 으로 분류하고 ordering 함의를 설명한다.
- **Apply** Address routing vs ID routing vs Implicit routing 을 시나리오에 매핑한다.
- **Trace** Memory Read 의 MRd → CplD 의 송수신 + Tag matching 흐름을 추적한다.
- **Justify** Posted 가 NP 를 추월하도록 spec 가 허용한 이유 (deadlock 회피) 를 producer-consumer 의미와 함께 설명한다.
:::
:::note[사전 지식]
- Module 02 (TL 의 책임)
- 메모리 매핑 IO, BDF 개념
:::
---

## 1. Why care? — 이 모듈이 왜 필요한가

### 1.1 시나리오 — _Tag 가 _안 맞음_

PCIe RC 검증 환경에서 Memory Read TLP 를 보내고 Completion 을 기다리는데 응답으로 전혀 다른 데이터가 돌아오는 경우가 있습니다. 이 증상의 전형적인 원인은 Tag mismatch 입니다. Request TLP 의 Tag 필드는 해당 outstanding request 의 ID 역할을 하며, Completion 은 반드시 같은 Tag 값을 실어 와야 requester 가 어느 request 에 대한 응답인지 알 수 있습니다. RC 가 두 개의 서로 다른 요청에 동일한 Tag 를 할당하면 Completion 이 어느 request 를 위한 것인지 구별하지 못하고 data corruption 이 발생합니다.

PCIe 는 out-of-order completion 을 허용하기 때문에, request 와 completion 을 대응시키려면 Tag 가 반드시 필요합니다.

**TLP 는 PCIe 의 "데이터 path" 입니다.** 모든 driver, NIC, NVMe, GPU 의 통신은 결국 TLP. Header field 의 의미를 알아야 packet trace 를 읽을 수 있고 (검증/디버그), VIP coverage 를 설계할 수 있습니다.

이 모듈의 어휘 — **Fmt/Type, P/NP/Cpl, Tag, Address vs ID routing** — 가 이후 모든 DV scoreboard, AER error 분류, SR-IOV/ATS/CXL 의 기본 단위. 이 layer 모델을 정확히 잡고 나면 처음 보는 TLP 도 _"아, 이게 NP 라 Cpl 매칭이 필요하구나"_ 처럼 행동을 즉시 예측할 수 있습니다.

---

## 2. Intuition — 국제 송장 비유와 한 장 그림

:::tip[💡 한 줄 비유]
**TLP** ≈ **국제 송장**. <br>
**Fmt/Type** = 화물 분류 코드 (Memory Read / Write / Config / Message / Completion). <br>
**Length** = 화물 양. <br>
**Address** (3DW: 32-bit, 4DW: 64-bit) = 주소. <br>
**Tag** = 송장 번호 (요청 ↔ 응답 매칭). <br>
**TC** (Traffic Class) = 우선순위 등급 (express vs standard). <br>
**Requester ID** = 발신자 BDF.
:::
### 한 장 그림 — TLP 포맷과 Switch 의 라우팅

```d2
direction: down

TX: "Sender TLP\n[ Header (12/16 B) | Payload (0..4096) | ECRC (opt) ]\nFmt + Type + Length + Address + Tag + RequesterID …"
SW: "Switch (PCIe routing)\n· Address routing : Header.Address → port\n· ID routing : Header.DestID → port\n· Implicit : Type[2:0] (Msg) → 정의된 경로\n━━━\nECRC 그대로 보존 (end-to-end)\nLCRC 는 매 hop 새로 계산 (Module 02, 04)"
RX: "Receiver TLP\n(Header / Payload 그대로)"
TX -> SW
SW -> RX
```

### 왜 이 디자인인가 — Design rationale

세 가지 요구가 동시에 풀려야 했습니다.

1. **PCI 와의 SW backward compat** → Configuration Space + ordering rules 그대로 유지 → P/NP/Cpl 의 분리.
2. **Producer-Consumer 의 데이터 무결성** → MWr (P) 가 Read Cpl 보다 먼저 도착해야 함 → P 가 NP 추월 가능 + NP 는 P 추월 불가.
3. **Routing flexibility** (memory address / device identity / message type) → 3 가지 routing 메커니즘.

이 세 요구의 교집합이 **Fmt/Type 인코딩 + P/NP/Cpl 분리 + Address/ID/Implicit 3 routing** 입니다.

---

## 3. 작은 예 — MRd 512 byte 가 RC → Switch → EP 1-hop 을 건너는 과정

가장 단순한 시나리오. CPU 가 EP (NVMe) 의 BAR 영역 `0x80001000` 에서 **512 byte** Memory Read 를 발행. MRRS=512, MPS=128 가정 → 응답은 4 packet 으로 split.

### 단계별 추적

```d2
shape: sequence_diagram

RC: "Requester (RC, 00:00.0)"
SW: "Switch"
EP: "Completer (EP, 01:00.0)"

# Note over EP: ⑧ 모든 split 송신 완료
# Note over RC: ⑨ 4 packet 모두 수신 + Tag=5 매칭 → read 완료
RC -> SW: "① MRd 4DW (Type=00000, Length=128 DW=512 B,\nTC=0, ReqID=00:00.0, Tag=0x05,\nAddr=0x80001000, Cat=NP)"
SW -> EP: "Address routing\n(Addr 가 EP 의 BAR 범위)"
EP -> EP: "② MRd 수신 → ③ memory read 실행"
EP -> SW: "④ CplD #1 (Tag=5, ByteCount=512, LowAddr=0x00, payload 128 B)"
SW -> RC: "ID routing (DestID=ReqID)"
EP -> RC: "⑤ CplD #2 (Tag=5, ByteCount=384, LowAddr=0x80, 128 B)"
EP -> RC: "⑥ CplD #3 (Tag=5, ByteCount=256, LowAddr=0x100, 128 B)"
EP -> RC: "⑦ CplD #4 (Tag=5, ByteCount=128, LowAddr=0x180, 128 B)"
```

### 단계별 의미

| Step | 누가 | 무엇을 | 왜 |
|---|---|---|---|
| ① | RC TL | MRd TLP 생성 | Driver 의 read 요청 |
| ② | Switch | Header.Address 보고 outgoing port 결정 | Address routing |
| ③ | EP TL | Address 검증, memory read | BAR 영역 hit |
| ④–⑦ | EP TL | 512 B 를 MPS=128 단위로 split | Receiver 의 buffer 한계 |
| ④–⑦ | EP TL | 각 CplD 에 같은 Tag=5, 다른 LowAddr/ByteCount | Requester 가 위치 + 잔량 추적 |
| ④–⑦ | Switch | DestID = Requester ID 보고 RC 방향 forward | ID routing |
| ⑨ | RC TL | Tag=5 의 모든 split 받으면 read 완료 통지 | Tag matching |

```c
// MRd 측 pseudo code — ReqID/Tag 가 Cpl 매칭의 핵심
struct tlp build_mrd(uint64_t addr, uint16_t length_dw, uint8_t tag) {
    return (struct tlp){
        .fmt    = 0b01,  // 4DW, no data
        .type   = 0b00000, // MRd
        .length = length_dw,
        .req_id = REQ_BDF,
        .tag    = tag,
        .addr   = addr,
    };
    // Cat = NP → Cpl 응답을 Tag 로 매칭해야 함
}

// CplD 측 — split 마다 같은 Tag, 다른 ByteCount/LowAddr
void send_cpld(uint8_t tag, uint16_t total_remaining, uint8_t low_addr_7b,
               uint8_t *payload, uint16_t payload_len) {
    struct tlp t = {
        .fmt    = 0b10,  // 3DW + data
        .type   = 0b01010, // Cpl with data
        .length = payload_len / 4,
        .req_id = req_id_received,  // 응답 destination
        .tag    = tag,
        .byte_count = total_remaining,
        .low_addr   = low_addr_7b,
    };
    send(t, payload, payload_len);
}
```

:::note[여기서 잡아야 할 두 가지]
**(1) Memory Read 는 NP — 응답이 필수다.** Tag 가 그 매칭의 키. Tag pool 이 고갈되면 새 MRd 못 보내고 stall (Module 04). <br>
**(2) 한 read 가 여러 split 으로 쪼개진다 — MRRS (요청 측) 와 MPS (응답 측) 의 mismatch 가 split 갯수를 결정한다.** Tag 는 같고 LowAddr/ByteCount 가 위치를 구분.
:::
---

## 4. 일반화 — TLP 의 3 축 (Fmt × Type × Routing × Category)

### 4.1 TLP Format

```
   ┌─────────────────────────────────────────────────┐
   │ Header (3DW=12B 또는 4DW=16B)                    │
   ├─────────────────────────────────────────────────┤
   │ Data Payload (0..4096 byte, 4-byte aligned)     │
   ├─────────────────────────────────────────────────┤
   │ ECRC (optional, 4 byte)                          │
   └─────────────────────────────────────────────────┘

   상위 layer 가 보는 packet 단위. DLL 이 Seq# + LCRC 를 추가하면 그 결과가 PHY 로 내려감.
```

**Header 길이 결정**:

- **3DW (12 byte)**: 32-bit address (예: x86 legacy 호환), Configuration, Completion
- **4DW (16 byte)**: 64-bit address (modern memory request)

### 4.2 3 카테고리 (P / NP / Cpl)

| Cat | 응답 (TL) | 예 | Credit 그룹 |
|-----|----------|----|------------|
| **Posted (P)** | 없음 | MWr, MsgD | Posted Header (PH) + Posted Data (PD) |
| **Non-Posted (NP)** | Cpl 또는 CplD 필수 | MRd, IORd, IOWr, CfgRd/Wr, AtomicOp | Non-Posted Header (NPH) + Non-Posted Data (NPD) |
| **Completion (Cpl)** | (응답 자체) | Cpl, CplD | Completion Header (CplH) + Completion Data (CplD) |

### 4.3 Routing 3 가지

Switch 가 TLP 를 어느 port 로 내보낼지 결정하는 방법은 TLP 의 종류에 따라 세 가지로 나뉩니다. 가장 흔한 Memory Read/Write 는 header 의 주소 필드를 port 별 Memory Base/Limit 범위와 비교하는 **Address Routing** 으로 처리됩니다. Configuration 이나 Completion 처럼 특정 BDF 를 목적지로 삼는 TLP 는 Destination BDF 를 직접 보는 **ID Routing** 을 씁니다. 일부 Message TLP 는 "항상 RC 방향으로" 또는 "RC 가 브로드캐스트" 처럼 TLP 의 Type 필드 자체가 경로를 암묵적으로 결정하는 **Implicit Routing** 을 따릅니다.

```
   Address Routing (Memory, IO)
   ─────────────────────────────
   TLP 의 Address 를 보고 switch 가 outgoing port 결정.
   각 port 의 [Memory Base, Memory Limit] 범위 비교.

   ID Routing (Configuration, Completion, ID-routed Msg)
   ────────────────────────────────────────────────────
   TLP 의 Destination BDF (Bus/Device/Function) 로 라우팅.
   Configuration 의 경우 Type 0 (직접) vs Type 1 (Bridge 통과).

   Implicit Routing (일부 Msg)
   ────────────────────────────
   "to RC" / "broadcast from RC" / "to local" 등 implicit 정의.
```

### 4.4 Ordering Rules

PCIe 의 ordering 규칙은 "어느 TLP 가 어느 TLP 를 앞지를 수 있는가"를 정의합니다. 핵심 논리는 Producer-Consumer 패턴에서 출발합니다. GPU 가 결과를 메모리에 Write(P) 한 뒤 CPU 가 Read 응답(Cpl) 을 받는 상황을 떠올리면, Write 가 Read 응답보다 반드시 먼저 도착해야 CPU 가 올바른 값을 읽을 수 있습니다. 반대로 Read 가 Write 를 추월해버리면 CPU 는 아직 Write 되지 않은 쓰레기 값을 읽게 됩니다. 그래서 P 는 NP 를 앞지를 수 있지만 NP 는 P 를 앞지를 수 없으며, 이 규칙이 PCI legacy 의 ordering 가정과도 호환을 맞춥니다.

```
   같은 source 의 P 두 개          : in-order 도착
   P 가 NP 를 추월 가능 (deadlock 회피)
   NP 가 P 를 추월 불가
   Cpl 이 다른 Cpl 을 추월 불가
   Cpl 이 P 를 추월 가능
```

---

## 5. 디테일 — 필드 카탈로그, routing 규칙, special TLP

### 5.1 TLP Header — 3DW 일반 구조

```
   Byte 0    Byte 1    Byte 2    Byte 3
   ┌────┬───┬────────┬────────┬────────┐
   │Fmt │Typ│ TC R Th│   ATTR │  Length │  ← DW0
   │ 2b │5b │ 3 1 1  │   2b   │  10b    │
   └────┴───┴────────┴────────┴────────┘
   ┌─────────────────┬─────────┬─────────┐
   │ Requester ID    │  Tag    │  BE     │  ← DW1 (혹은 routing field)
   │ 16b (Bus/Dev/Fn)│  8b     │ 4b last │
   └─────────────────┴─────────┴─────────┘
   ┌─────────────────────────────────────┐
   │ Address [31:2]                      │  ← DW2 (3DW Memory)
   └─────────────────────────────────────┘
```

| Field | 길이 | 설명 |
|-------|-----|------|
| **Fmt** | 2 | 00 = 3DW header, no data; 01 = 4DW header, no data; 10 = 3DW + data; 11 = 4DW + data; (Gen3+: 추가 인코딩) |
| **Type** | 5 | Type 별 의미는 Fmt 와 조합. 표 아래 참고 |
| **TC** (Traffic Class) | 3 | 0..7. VC (Virtual Channel) 매핑에 사용 |
| **R** (Reserved) / **Th** (TLP Hint) / etc | 1 each | TPH 등의 추가 hint |
| **ATTR** | 2 | RO (Relaxed Ordering), NS (No Snoop) bit |
| **Length** | 10 | DW 단위 payload 길이. 0 = 1024 DW (= 4096 byte) |
| **Requester ID** | 16 | BDF (Bus 8b + Device 5b + Function 3b) |
| **Tag** | 8 | (10 bit Gen2.1+ extended) Non-Posted Request 의 ID, Completion 매칭용 |
| **Last DW BE** | 4 | 마지막 DW 의 byte enable |
| **First DW BE** | 4 | 첫 DW 의 byte enable |
| **Address** | 30 (3DW) or 62 (4DW) | DW-aligned address |

### 5.2 Fmt × Type 조합 — 주요 TLP 카탈로그

| Fmt[1:0] | Type[4:0] | TLP 명 | Cat | xH 길이 | 설명 |
|---------|-----------|--------|-----|---------|------|
| 00 / 01 | 00000 | MRd | NP | 3DW/4DW | Memory Read Request |
| 10 / 11 | 00000 | MWr | P | 3DW/4DW | Memory Write |
| 00 | 00010 | IORd | NP | 3DW | IO Read |
| 10 | 00010 | IOWr | NP | 3DW | IO Write (NP! TL-level 응답 필요) |
| 00 | 00100 | CfgRd0 | NP | 3DW | Configuration Read Type 0 |
| 10 | 00100 | CfgWr0 | NP | 3DW | Configuration Write Type 0 |
| 00 | 00101 | CfgRd1 | NP | 3DW | Configuration Read Type 1 |
| 10 | 00101 | CfgWr1 | NP | 3DW | Configuration Write Type 1 |
| 00 | 01010 | Cpl | Cpl | 3DW | Completion (no data) |
| 10 | 01010 | CplD | Cpl | 3DW | Completion with Data |
| 00 | 01011 | CplLk | Cpl | 3DW | Locked Completion |
| 10 | 01011 | CplDLk | Cpl | 3DW | Locked Completion with Data |
| 01/11 | 11rrr | Msg / MsgD | P | 4DW | Message (Type[2:0] = routing) |
| 10/11 | 01100/01101 | FetchAdd, Swap | NP | 3DW/4DW | AtomicOps |
| 11 | 01110 | CAS | NP | 4DW | Compare and Swap |

> **Cat** = Posted (P), Non-Posted (NP), Completion (Cpl)

:::note[Spec 인용]
PCIe Base Spec 에서 Fmt/Type 인코딩은 Section "Transaction Layer Specification > TLP Format" 에 표 형태로 정의. 실제 spec 은 PCI-SIG 회원사 비공개이지만 *PCI Express System Architecture* (MindShare) 가 공개 자료의 표준 인용 소스.
:::
### 5.3 Posted / Non-Posted / Completion 의 ordering 의미

:::tip[Write-passes-Read 의 두 얼굴 — Deadlock 방지 + 데이터 무결성]
**Strong ordering 의 기본 원칙**: 먼저 출발한 Memory Write 는 무조건 먼저 도착해야 한다 (FIFO). Write 32-bit / 64-bit 모두 Posted 로 동일 취급.

**Write 가 Read 를 새치기 가능 — Why?**

- Read 는 응답을 기다리는 transaction. 만약 Read 가 길을 막은 채 Write 가 그 뒤에 줄 서 있으면, Read 의 응답을 기다리는 쪽도 그 Write 가 있어야 진행 → **circular wait → deadlock**.
- 그래서 spec 가 명시적으로 "Write **MUST PASS** Read" 허용.

**Read 가 Write 를 새치기 절대 불가 — Why?**

- Producer-Consumer: GPU 가 RAM 에 결과 Write → CPU 가 그 영역 Read.
- 만약 Read 가 Write 를 추월하면 CPU 가 **이전 (쓰레기) 데이터** 를 받음 → 무결성 파괴.

**Relaxed Ordering (RO) 의 책임**:

- TLP 헤더의 RO bit 가 1 이면 "순서 섞여도 OK" 선언 — switch 가 ordering 무시하고 우선순위로 처리.
- Switch 는 주소 검사 안 함 → 같은 주소도 섞을 수 있음.
- 책임은 **sender** 에게. 순서가 중요한 제어 명령에는 절대 RO 금지.
:::

:::note[ATTR 의 두 bit — RO 와 NS 의 의미와 위험]
TLP header 의 ATTR 2 bit 는 각각 ordering 과 coherency 의 *완화* 를 선언하는 hint 입니다. 둘 다 "성능을 위해 보장을 일부 포기" 하는 것이라, 잘못 쓰면 조용한 데이터 버그를 만듭니다.

- **RO (Relaxed Ordering).** 기본 PCIe ordering 은 producer-consumer 무결성을 위해 strong ordering 을 강제합니다(앞의 Write-passes-Read 규칙). RO=1 은 "이 TLP 들 사이엔 그런 순서 의존이 없으니 자유롭게 재배치해도 된다" 는 선언입니다. *언제 안전한가* — 서로 *독립적인 데이터* 일 때입니다. 예: 큰 DMA 버퍼의 서로 다른 영역을 여러 TLP 로 쓰는데, 그 조각들 사이엔 "먼저/나중" 의미가 없는 경우. 재배치를 허용하면 switch/RC 가 throughput 을 높입니다. *위험* — 만약 그 TLP 들 사이에 실제로는 순서 의존(예: 데이터 write 후 완료 flag write)이 있는데 RO 를 켜면, flag 가 데이터보다 먼저 보여 consumer 가 미완성 데이터를 읽습니다. RO 의 안전성 판단 책임은 전적으로 *sender* 에게 있습니다.
- **NS (No Snoop).** 기본적으로 host 로 향하는 메모리 접근은 CPU 캐시와의 coherency 를 위해 snoop 됩니다(host 가 그 line 의 dirty 사본을 들고 있으면 그것을 반영). NS=1 은 "이 접근은 snoop 을 생략해도 된다" 는 선언으로, snoop 경로를 건너뛰어 latency 와 host 측 coherency 트래픽을 줄입니다. *언제 안전한가* — 그 메모리 영역이 CPU 캐시에 caching 되지 않음이 보장될 때(예: 드라이버가 non-cacheable 로 매핑한 DMA 영역). *위험* — CPU 가 그 영역을 캐시에 들고 있는데 NS 로 snoop 을 생략하면, device 는 DRAM 의 stale 값을 읽거나 device 의 write 가 CPU 캐시와 어긋나 coherency 가 깨집니다. NS 역시 "정말 non-coherent 해도 되는가" 의 판단을 sender/소프트웨어가 책임집니다.

검증에서 RO/NS 는 coverage 와 위험 시나리오의 핵심입니다 — RO=1 TLP 가 실제로 재배치돼도 결과가 맞는지, NS=1 인데 host 캐시에 사본이 있는 위험 케이스를 잡는지를 확인해야 합니다.
:::
### 5.4 Routing 상세 — Type 0 vs Type 1 Configuration TLP

```d2
direction: down

RC: "RC"
SW: "Switch (Bus N)"
EP: "EP (Bus N+1, Dev 0)"
RC -> SW: "Bus N"
SW -> EP: "Bus N+1"
```

- **RC → Switch 자기 자신 config 접근**: `CfgRd0` (Type 0, target = same bus).
- **RC → Switch 의 secondary 측 통과**: `CfgRd1` (Type 1) — switch 가 받아 `CfgRd0` 로 변환해 EP 에 전달.

→ **Type 1 → 0 변환은 PCI-PCI Bridge / Switch 의 책임**.

### 5.5 Memory Read 흐름 (Tag matching)

```d2
shape: sequence_diagram

REQ: "Requester EP"
CMP: "Completer (RC 또는 다른 EP)"

# Note over CMP: memory read 수행\n512 byte / 64 byte payload size\n→ 8 packet 으로 split 가능
# Note over REQ: …
# Note over REQ: 모든 Completion 받으면 read 완료
REQ -> CMP: "MRd Tag=5, Length=16, Addr=0x1000"
CMP -> REQ: "CplD Tag=5, ByteCount=512, LowAddr=0x00, 64 B" { style.stroke-dash: 4 }
CMP -> REQ: "CplD Tag=5, ByteCount=448, LowAddr=0x40, 64 B" { style.stroke-dash: 4 }
CMP -> REQ: "CplD Tag=5, ByteCount=384, LowAddr=0x80, 64 B" { style.stroke-dash: 4 }
CMP -> REQ: "CplD Tag=5, ByteCount=64, LowAddr=0x1C0, 64 B" { style.stroke-dash: 4 }
```

| 필드 | 의미 |
|------|------|
| **Tag** | Requester 가 Non-Posted 마다 unique 하게 부여 (8b 또는 10b extended). Completion 매칭. |
| **ByteCount** | "이 completion 까지 받은 후 남은 byte 수" — 마지막 packet 에서 끝의 length 와 일치 |
| **LowAddr** | 첫 byte 의 하위 7 bit address (split 시 위치 표시) |
| **Cpl Status** | Successful / Unsupported Request (UR) / Configuration Request Retry (CRS) / Completer Abort (CA) |

→ **Max Read Request Size** (MRRS) 가 한 번의 MRd 가 요청할 수 있는 최대 byte. Completer 의 **Max Payload Size** (MPS) 가 한 Completion packet 의 최대 payload — 이 둘의 mismatch 가 split 갯수를 결정.

:::note[Tag 수는 왜 무한정 못 늘리나 — outstanding NP = completion buffer 예약]
Tag 를 늘리면 더 많은 NP 를 동시에(outstanding) 던질 수 있어 throughput 이 오를 것 같지만, Tag 수에는 *물리적 상한* 이 있습니다 — 그 상한을 정하는 것이 **completion buffer** 입니다.

MRd 같은 NP 를 하나 발행한다는 것은 "그 응답(Completion)이 언젠가 돌아올 텐데, 그걸 받아 둘 자리를 내가 미리 비워 둔다" 는 약속입니다. PCIe 의 flow control 상 requester 는 *자신이 받을 completion 을 담을 buffer 가 있다고 보고* NP 를 내보내야 하고(completion 은 보통 무한 credit 으로 광고되므로 — Module 04), 그 buffer 는 requester 안의 유한한 SRAM 입니다. 따라서 *동시에 떠 있을 수 있는 NP 의 개수* 는 곧 *그 completion 들을 한꺼번에 받아 둘 buffer 용량* 과 묶입니다. Tag 는 그 outstanding NP 하나하나를 식별하는 라벨이므로, "동시 outstanding 수 = 필요한 completion buffer 크기 = 필요한 Tag 수" 가 한 사슬로 엮입니다.

그래서 Tag 를 256 → 1024(extended Tag)로 늘리려면, requester 는 그만큼 많은 in-flight completion 을 받아 둘 buffer 도 함께 키워야 합니다 — buffer 없이 Tag 만 늘리면, 응답이 몰려 들어올 때 받아 둘 자리가 없어 link 가 막히거나 completion 을 흘립니다. 즉 Tag 수를 무한정 못 늘리는 이유는 인코딩 비트가 아니라 *완료 데이터를 보관할 on-chip 메모리 비용* 입니다. (그래서 device 는 자기가 감당 가능한 Tag 수를 capability 로 광고합니다.)
:::

:::note[MPS/MRRS는 어떻게 link 양단에서 협상·강제되나]
MPS 와 MRRS 는 한쪽이 마음대로 정하는 값이 아니라, *hierarchy 전체* 가 합의해야 하는 값입니다. 특히 MPS 는 강한 제약이 있습니다 — **시스템의 모든 참여자(RC, 중간 switch, endpoint)가 지원하는 MPS 의 *최소값* 으로 통일** 해야 합니다.

왜 최소값일까요? TLP 하나가 RC → switch → EP 처럼 여러 hop 을 거치는데, 경로상 어느 한 노드라도 그 payload 크기를 받을 buffer 가 없으면 그 노드에서 처리가 불가능합니다. 가장 작은 MPS 를 가진 노드가 경로의 *병목* 이므로, 전체를 그 최소값에 맞춰야 어떤 TLP 도 경로 어디서든 안전하게 처리됩니다. enumeration(Module 06) 단계에서 OS/firmware 가 각 device 의 MPS capability 를 읽어, hierarchy 전체의 최소값을 골라 모든 device 의 MPS *control* 레지스터에 그 값을 프로그램합니다.

그럼 누군가 이 합의를 어기고 더 큰 payload 를 보내면? 그 TLP 는 수신 측에서 **Malformed TLP** 로 처리됩니다 — payload 길이가 협상된 MPS 를 초과하면 spec 위반으로 간주되어 에러(AER 의 Malformed TLP, 보통 Fatal 급)로 보고되고 폐기됩니다. 즉 MPS 는 "최소값으로 통일" 이라는 *협상* 과, "초과 시 Malformed" 라는 *강제* 의 두 단계로 지켜집니다. (MRRS 는 read 요청 크기 상한이라 강제 양상은 다르지만, 마찬가지로 각 device 의 control 레지스터로 설정됩니다.)
:::

### 5.6 ECRC — End-to-End CRC

- 32-bit CRC, TLP header (특정 변경 가능 field 제외) + payload 위로 계산.
- Switch / Bridge 가 통과시켜도 변경 안 됨 — end-to-end 무결성.
- Optional. AER 의 ECRC error 카운터로 모니터링.
- LCRC 와 다름: LCRC 는 link-by-link.

### 5.7 Atomic Operations

| Op | 의미 |
|----|------|
| **FetchAdd** | mem[addr] += val, return old |
| **Swap** | atomic exchange |
| **CAS** (Compare and Swap) | if mem[addr] == cmp: mem[addr] = swap |

- 4-byte / 8-byte / 128-byte (CAS) operands.
- TL-Atomic 도 NP — Cpl 로 응답.
- Lock-free 분산 데이터 구조에 사용.

### 5.8 Message TLP

Routing field (Type[2:0]) 이 destination 결정:

| Type[2:0] | Routing |
|-----------|---------|
| 000 | Routed to Root Complex |
| 010 | Routed by Address |
| 011 | Routed by ID |
| 100 | Broadcast from RC |
| 101 | Local — terminated at receiver |
| 110 | Gather (rare) |

용도:

- Power Management (PME_Turn_Off, PME_TO_Ack)
- Hot Plug events
- Vendor-defined messages
- Error signaling (ERR_COR, ERR_NONFATAL, ERR_FATAL)

:::danger[❓ 흔한 오해 — MSI / MSI-X 는 Message TLP 가 아니다]
이름에 "Message" 가 들어가지만, MSI/MSI-X 는 실제로는 **Memory Write TLP** 로 전송된다.

- **MSI**: Configuration Space 에 등록된 한 메모리 주소에 32 vector 까지 (하위 비트만 변경). 개별 mask 불가.
- **MSI-X**: BAR 영역 안에 별도 **MSI-X Table** 생성. 최대 **2048 vector** (Table Size 11-bit). 각 vector 가 독립적인 주소 + 데이터, 개별 mask 가능.
- **SR-IOV 환경에서는 MSI-X 필수** — 각 VF 가 자기만의 vector 가 필요.

Message TLP 와 헷갈리면 **packet trace 의 MSI 식별** 이 안 됨 — Memory Write TLP 의 dst 주소가 MSI 영역인지 보고 판단해야 함.
:::
:::tip[MPS 가 작게 설정되는 진짜 이유 — HOL + 비용]
Length 필드 10 bit × 4 byte = **이론상 최대 4096 byte payload**. 그런데 실무 시스템은 보통 128 / 256 / 512 byte.

| MPS | 헤더 오버헤드 | 사용처 |
|-----|--------------|--------|
| 128 B | ~17% | PC 일반 |
| 256 B | ~9% | PC 기본 |
| 512 B | ~4.5% | 서버급 |
| 4096 B | ~0.5% | 이론적 최고, 실무 거의 미사용 |

**작게 쓰는 이유**:

1. **Head-of-Line (HOL) Blocking**: 4096-byte 화물차가 차선을 점유하는 동안 뒤에서 급한 인터럽트 (MSI Memory Write) 가 기다려야 함. 잘게 쪼개면 끼워 넣을 틈이 생김.
2. **수신 측 SRAM 비용**: MPS 가 4096 이면 모든 device 의 RX buffer / Replay Buffer 가 그만큼 커야 함 → 칩 면적, 발열, 단가 폭등.

→ 즉 MPS 결정은 **"최고 효율 vs 빠른 반응성 + 저렴한 단가"** 의 trade-off. 현대 시스템은 오버헤드를 감수하고 반응성 / 비용 측을 선택.
:::
---

## 6. 흔한 오해 와 DV 디버그 체크리스트

### 흔한 오해

:::danger[❓ 오해 1 — 'Memory Write 는 응답 (ACK) 가 없으니 unreliable 하다']
**실제**: PCIe 에서 Memory Write (MWr) 는 **TL-level Posted** = TL 의 응답 없음. 그러나 **DLL 의 ACK/NAK 은 발생** — receiver 의 DLL 이 packet 을 정상 받았다는 ACK 는 DLLP 로 sender 의 DLL 에 전달되어 Replay buffer 에서 해당 entry 가 retire. 따라서 **link-level 신뢰성은 보장**, 단지 application-level "내 write 가 정말 처리됐는가" 는 별도로 확인해야 함 (예: 다음 Read 로).<br>
**왜 헷갈리는가**: "Posted" 와 "응답 없음" 을 link 전체로 해석하기 쉬움.
:::
:::danger[❓ 오해 2 — 'IOWr 는 Memory Write 처럼 Posted 다']
**실제**: IOWr 는 **Non-Posted** — TL-level 응답이 필수입니다. Legacy ISA bus 의 IO write 가 응답을 기다리는 동작과 호환을 위해. 모르면 timing 분석에서 큰 오차 — IOWr 후 Cpl 까지 기다려야 다음 transaction 가능.<br>
**왜 헷갈리는가**: "Write 는 Posted" 라는 단순 매핑.
:::
:::danger[❓ 오해 3 — 'Length=0 이면 0 byte payload 다']
**실제**: Length 필드는 **DW 단위 payload 길이** + **0 = 1024 DW (= 4096 byte)** 의 special encoding. Length=1 이 1 DW (4 byte). 0 의 의미가 직관과 정반대 — TLP 분석 도구에서 흔히 잘못 표시되는 함정.<br>
**왜 헷갈리는가**: 일반적으로 0 = 빈 packet 으로 가정.
:::
:::danger[❓ 오해 4 — 'Tag 는 어차피 8-bit 면 256 outstanding NP 가능']
**실제**: Gen2.1 부터 **Extended Tag** (10-bit) 가 추가되어 1024 outstanding 까지 가능. SR-IOV / PASID 환경에서는 더 많은 outstanding 이 필요 — Tag pool 관리 정책이 throughput 의 발목. 또한 device 마다 실제 지원 Tag 수가 capability 로 결정.<br>
**왜 헷갈리는가**: legacy 8-bit 만 보고 외움.
:::
:::danger[❓ 오해 5 — 'ECRC 카운터가 0 이면 path 가 깨끗하다']
**실제**: ECRC 는 _optional_ 이므로 disabled 되어 있을 수 있음. AER 의 ECRC error counter 가 0 이라고 안전한 게 아니라 **ECRC 자체가 enable 되었는지** 부터 확인 필요. AER Capability 의 Control register 에서 enable bit 검사.
:::
### DV 디버그 체크리스트 (이 모듈 내용으로 마주칠 첫 실패들)

| 증상 | 1차 의심 | 어디 보나 |
|---|---|---|
| MRd 보냈는데 Cpl 안 옴 (timeout) | Tag pool 고갈 또는 Address 잘못 | Tag tracking + AER Completion Timeout counter |
| Cpl 의 Tag 가 보낸 적 없는 값 | Unexpected Completion (UR) | Tag matching state, 다른 source 의 BDF 충돌 |
| Cpl status = UR | EP 가 처리 못 하는 TLP | EP 의 BAR 범위, Fmt/Type 지원 여부 |
| Cpl 이 split 으로 오는데 LowAddr 가 안 맞음 | EP 의 split 로직 버그 | ByteCount 와 LowAddr 의 일관성 |
| Switch 통과 후 ECRC error | path 중간 corruption 또는 switch 의 잘못된 wrapper | LCRC 카운터와 비교 (LCRC OK 인데 ECRC fail = 의심) |
| MWr 보낸 후 다음 MRd 결과가 stale | Producer-Consumer ordering 위반 또는 RO bit set | TLP 의 Attribute(RO) bit, switch 의 ordering |
| Cfg access 가 EP 못 도달 | Type 1 → Type 0 변환 실패 (Bridge) | Bridge 의 Sec/Sub Bus number, BDF |
| MSI vector 가 도착 안 함 | MSI 는 MWr 인데 destination 주소가 잘못 매핑 | MSI-X Table 의 message address |

---

## 7. 핵심 정리 (Key Takeaways)

- TLP = header (3DW/4DW) + payload (0..4096B) + opt ECRC.
- Fmt+Type 조합이 TLP 종류 결정 (MRd/MWr/CfgRd/CfgWr/Cpl/Msg/Atomic).
- 3 카테고리: Posted (P) / Non-Posted (NP) / Completion (Cpl), 각자 별도 FC credit + ordering 규칙.
- Routing: Address (Memory/IO), ID (Config/Completion), Implicit (일부 Msg).
- Memory Read 는 MRd → 여러 CplD 로 split, Tag 로 매칭.

:::caution[실무 주의점]
- `IOWr` 는 P 가 아니라 **NP** — IO write 는 응답을 받아야 함 (legacy ISA 호환). 모르면 timing 분석에서 큰 오차.
- `Length` 가 0 = 1024 DW (= 4096 byte). `Length=1` = 1 DW (4 byte). 0 의 의미가 직관과 다름.
- Tag 가 8b → 10b extended 로 늘어난 것은 outstanding NP 가 256 개 → 1024 개로 확장. Sender 의 max outstanding 추적 필요.
- Posted 라고 해서 ACK/NAK 까지 없는 게 아님 — DLL ACK 는 발생. 단지 TL 응답 없음.
- ECRC 는 optional 이라 disabled 인 경우가 흔함. AER 카운터 0 이라고 안전한 게 아니라 ECRC 자체가 꺼져 있을 수 있음.
:::
### 7.1 자가 점검

:::tip[🤔 Q1 — Posted vs Non-Posted (Bloom: Apply)]
MemWr (32-bit), MemRd, IOWr, CfgWr. 각각 P / NP / Cpl?

<details>
<summary>정답</summary>

- **MemWr**: **P** (Posted) — write 보내고 응답 없음. Fast.
- **MemRd**: **NP** (Non-Posted) — completion 으로 data 받아야.
- **IOWr**: **NP** — legacy ISA 호환, completion 요구.
- **CfgWr**: **NP** — config register 변경 후 completion 확인.

직관 깨짐: write 가 _대부분_ P 이지만 _config / IO_ 는 NP.

</details>
:::
:::tip[🤔 Q2 — Length encoding (Bloom: Analyze)]
Length field = 10 bit. 표현 가능한 _가장 큰 payload_?

<details>
<summary>정답</summary>

Length = 0 → **1024 DW** (= 4096 byte). 10 bit binary 0 이 _최대값_ 의미.
Length = 1 → 1 DW (4 byte).
Length = 1023 → 1023 DW.

직관 반대: 0 이 최대, 1 이 최소.

</details>
:::
### 7.2 출처

**External**
- PCIe Specification 5.0 / 6.0
- Mindshare *PCI Express Technology* book

---

## 다음 모듈

→ [Module 04 — DLLP, Flow Control, ACK/NAK](../04_dllp_flow_control/): TL 의 packet 이 link 위에서 어떻게 reliability 를 얻는지 — DLL 의 Sequence + LCRC + ACK/NAK + Replay.

[퀴즈 풀어보기 →](../quiz/03_tlp_quiz/)
