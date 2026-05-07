# Module 03 — TLP (Transaction Layer Packet)

<!-- DV-SKOOL-CH-CTX:start -->
<div class="chapter-context" data-cat="intercon">
  <a class="chapter-back" href="../">
    <span class="chapter-back-arrow">←</span>
    <span class="chapter-back-icon">🔌</span>
    <span class="chapter-back-text">PCI Express</span>
  </a>
  <span class="chapter-divider">›</span>
  <span class="chapter-marker">Module 03</span>
</div>
<!-- DV-SKOOL-CH-CTX:end -->

<!-- DV-SKOOL-CH-TOC:start -->
<div class="page-toc">
  <span class="page-toc-label">목차</span>
  <a class="page-toc-link" href="#왜-이-모듈이-중요한가">왜 이 모듈이 중요한가</a>
  <a class="page-toc-link" href="#핵심-개념">핵심 개념</a>
  <a class="page-toc-link" href="#1-tlp-format">1. TLP Format</a>
  <a class="page-toc-link" href="#2-tlp-header-3dw-일반-구조">2. TLP Header — 3DW 일반 구조</a>
  <a class="page-toc-link" href="#3-fmt-type-조합-주요-tlp-카탈로그">3. Fmt × Type 조합 — 주요 TLP 카탈로그</a>
  <a class="page-toc-link" href="#4-posted-non-posted-completion">4. Posted / Non-Posted / Completion</a>
  <a class="page-toc-link" href="#5-routing-3-가지">5. Routing — 3 가지</a>
  <a class="page-toc-link" href="#6-memory-read-흐름-tag-matching">6. Memory Read 흐름 (Tag matching)</a>
  <a class="page-toc-link" href="#7-ecrc-end-to-end-crc">7. ECRC — End-to-End CRC</a>
  <a class="page-toc-link" href="#8-atomic-operations">8. Atomic Operations</a>
  <a class="page-toc-link" href="#9-message-tlp">9. Message TLP</a>
  <a class="page-toc-link" href="#핵심-정리-key-takeaways">핵심 정리 (Key Takeaways)</a>
  <a class="page-toc-link" href="#다음-모듈">다음 모듈</a>
</div>
<!-- DV-SKOOL-CH-TOC:end -->

!!! objective "학습 목표"
    이 모듈을 마치면:

    - **Decode** TLP header (3DW vs 4DW, Fmt/Type/TC/Length/Address) 의 각 필드를 식별한다.
    - **Classify** TLP 를 Posted / Non-Posted / Completion 으로 분류하고 ordering 함의를 설명한다.
    - **Apply** Address routing vs ID routing vs Implicit routing 을 시나리오에 매핑한다.
    - **Trace** Memory Read 의 MRd → CplD 의 송수신 + Tag matching 흐름을 추적한다.

!!! info "사전 지식"
    - Module 02 (TL 의 책임)
    - 메모리 매핑 IO, BDF 개념

## 왜 이 모듈이 중요한가

**TLP 는 PCIe 의 "데이터 path" 입니다.** 모든 driver, NIC, NVMe, GPU 의 통신은 결국 TLP. Header field 의 의미를 알아야 packet trace 를 읽을 수 있고 (검증/디버그), VIP coverage 를 설계할 수 있습니다.

!!! tip "💡 이해를 위한 비유"
    **TLP** ≈ **국제 송장**

    - Fmt/Type = 화물 분류 코드 (Memory Read / Write / Config / Message / Completion)
    - Length = 화물 양
    - Address (3DW: 32-bit, 4DW: 64-bit) = 주소
    - Tag = 송장 번호 (요청 ↔ 응답 매칭)
    - TC (Traffic Class) = 우선순위 등급 (express vs standard)
    - Requester ID = 발신자 BDF

## 핵심 개념

**TLP = header (12 byte for 3DW or 16 byte for 4DW) + 0..4096 byte payload + optional 4 byte ECRC. Header 의 Fmt/Type 조합이 TLP 의 종류 (MRd/MWr/CfgRd/CfgWr/CplD/Msg/Atomic) 를 결정. Posted (응답 없음, 예: MWr) / Non-Posted (응답 필요, 예: MRd, CfgRd/Wr) / Completion 의 3 카테고리가 ordering 과 flow control credit 을 분리한다.**

!!! danger "❓ 흔한 오해"
    **오해**: "Memory Write 는 응답 (ACK) 가 없으니 unreliable 하다."

    **실제**: PCIe 에서 Memory Write (MWr) 는 **TL-level Posted** = TL 의 응답 없음. 그러나 **DLL 의 ACK/NAK 은 발생** — receiver 의 DLL 이 packet 을 정상 받았다는 ACK 는 DLLP 로 sender 의 DLL 에 전달되어 Replay buffer 에서 해당 entry 가 retire. 따라서 **link-level 신뢰성은 보장**, 단지 application-level "내 write 가 정말 처리됐는가" 는 별도로 확인해야 함 (예: 다음 Read 로).

    **왜 헷갈리는가**: "Posted" 와 "응답 없음" 을 link 전체로 해석하기 쉬움.

---

## 1. TLP Format

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

---

## 2. TLP Header — 3DW 일반 구조

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

---

## 3. Fmt × Type 조합 — 주요 TLP 카탈로그

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

!!! quote "Spec 인용"
    PCIe Base Spec 에서 Fmt/Type 인코딩은 Section "Transaction Layer Specification > TLP Format" 에 표 형태로 정의. 실제 spec 은 PCI-SIG 회원사 비공개이지만 *PCI Express System Architecture* (MindShare) 가 공개 자료의 표준 인용 소스.

---

## 4. Posted / Non-Posted / Completion

### 정의

| Cat | 응답 (TL) | 예 | Credit 그룹 |
|-----|----------|----|------------|
| **Posted (P)** | 없음 | MWr, MsgD | Posted Header (PH) + Posted Data (PD) |
| **Non-Posted (NP)** | Cpl 또는 CplD 필수 | MRd, IORd, IOWr, CfgRd/Wr, AtomicOp | Non-Posted Header (NPH) + Non-Posted Data (NPD) |
| **Completion (Cpl)** | (응답 자체) | Cpl, CplD | Completion Header (CplH) + Completion Data (CplD) |

### Ordering Rules (단순화)

```
   같은 source 의 P 두 개          : in-order 도착
   P 가 NP 를 추월 가능 (deadlock 회피)
   NP 가 P 를 추월 불가
   Cpl 이 다른 Cpl 을 추월 불가
   Cpl 이 P 를 추월 가능
```

→ **Why?** Producer-Consumer 패턴에서 Producer 의 MWr (P) 가 Consumer 의 MRd Cpl 보다 먼저 도착해야 함. Posted/Non-Posted/Cpl 분리가 PCI legacy 의 ordering 가정과 호환.

!!! example "Write-passes-Read 의 두 얼굴 — Deadlock 방지 + 데이터 무결성"
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

---

## 5. Routing — 3 가지

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

### Type 0 vs Type 1 Configuration TLP

```
   ┌── PCIe ──────────────────────────────────────────┐
   │                                                    │
   │   RC                                               │
   │   │                                                │
   │   ▼ (Bus N)                                        │
   │   Switch (Bus N)                                   │
   │   │                                                │
   │   ▼ (Bus N+1)                                      │
   │   EP (Bus N+1, Dev 0)                              │
   │                                                    │
   └────────────────────────────────────────────────────┘

   RC → Switch 자기 자신 config 접근  : CfgRd0  (Type 0, target = same bus)
   RC → Switch 의 secondary 측 통과   : CfgRd1  (Type 1, switch 가 forwarding)
                                       Switch 가 받은 후 CfgRd0 로 변환해 EP 에 전달
```

→ **Type 1 → 0 변환은 PCI-PCI Bridge / Switch 의 책임**.

---

## 6. Memory Read 흐름 (Tag matching)

```
   Requester EP                           Completer (RC or other EP)
   ────────────                           ───────────────────────────
   MRd Tag=5, Length=16, Addr=0x1000  ──▶
                                          (memory read 수행)
                                          512 byte / 64 byte payload size
                                          → 8 packet 으로 split 가능

   ◀── CplD Tag=5, ByteCount=512, LowAddr=0x00, payload 64B
   ◀── CplD Tag=5, ByteCount=448, LowAddr=0x40, payload 64B
   ◀── CplD Tag=5, ByteCount=384, LowAddr=0x80, payload 64B
   …
   ◀── CplD Tag=5, ByteCount= 64, LowAddr=0x1C0, payload 64B

   Requester 가 모든 Completion 받으면 read 완료.
```

| 필드 | 의미 |
|------|------|
| **Tag** | Requester 가 Non-Posted 마다 unique 하게 부여 (8b 또는 10b extended). Completion 매칭. |
| **ByteCount** | "이 completion 까지 받은 후 남은 byte 수" — 마지막 packet 에서 끝의 length 와 일치 |
| **LowAddr** | 첫 byte 의 하위 7 bit address (split 시 위치 표시) |
| **Cpl Status** | Successful / Unsupported Request (UR) / Configuration Request Retry (CRS) / Completer Abort (CA) |

→ **Max Read Request Size** (MRRS) 가 한 번의 MRd 가 요청할 수 있는 최대 byte. Completer 의 **Max Payload Size** (MPS) 가 한 Completion packet 의 최대 payload — 이 둘의 mismatch 가 split 갯수를 결정.

---

## 7. ECRC — End-to-End CRC

- 32-bit CRC, TLP header (특정 변경 가능 field 제외) + payload 위로 계산.
- Switch / Bridge 가 통과시켜도 변경 안 됨 — end-to-end 무결성.
- Optional. AER 의 ECRC error 카운터로 모니터링.
- LCRC 와 다름: LCRC 는 link-by-link.

---

## 8. Atomic Operations

| Op | 의미 |
|----|------|
| **FetchAdd** | mem[addr] += val, return old |
| **Swap** | atomic exchange |
| **CAS** (Compare and Swap) | if mem[addr] == cmp: mem[addr] = swap |

- 4-byte / 8-byte / 128-byte (CAS) operands.
- TL-Atomic 도 NP — Cpl 로 응답.
- Lock-free 분산 데이터 구조에 사용.

---

## 9. Message TLP

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

!!! danger "❓ 흔한 오해 — MSI / MSI-X 는 Message TLP 가 아니다"
    이름에 "Message" 가 들어가지만, MSI/MSI-X 는 실제로는 **Memory Write TLP** 로 전송된다.

    - **MSI**: Configuration Space 에 등록된 한 메모리 주소에 32 vector 까지 (하위 비트만 변경). 개별 mask 불가.
    - **MSI-X**: BAR 영역 안에 별도 **MSI-X Table** 생성. 최대 **2048 vector** (Table Size 11-bit). 각 vector 가 독립적인 주소 + 데이터, 개별 mask 가능.
    - **SR-IOV 환경에서는 MSI-X 필수** — 각 VF 가 자기만의 vector 가 필요.

    Message TLP 와 헷갈리면 **packet trace 의 MSI 식별** 이 안 됨 — Memory Write TLP 의 dst 주소가 MSI 영역인지 보고 판단해야 함.

!!! example "MPS 가 작게 설정되는 진짜 이유 — HOL + 비용"
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

---

## 핵심 정리 (Key Takeaways)

- TLP = header (3DW/4DW) + payload (0..4096B) + opt ECRC.
- Fmt+Type 조합이 TLP 종류 결정 (MRd/MWr/CfgRd/CfgWr/Cpl/Msg/Atomic).
- 3 카테고리: Posted (P) / Non-Posted (NP) / Completion (Cpl), 각자 별도 FC credit + ordering 규칙.
- Routing: Address (Memory/IO), ID (Config/Completion), Implicit (일부 Msg).
- Memory Read 는 MRd → 여러 CplD 로 split, Tag 로 매칭.

!!! warning "실무 주의점"
    - `IOWr` 는 P 가 아니라 **NP** — IO write 는 응답을 받아야 함 (legacy ISA 호환). 모르면 timing 분석에서 큰 오차.
    - `Length` 가 0 = 1024 DW (= 4096 byte). `Length=1` = 1 DW (4 byte). 0 의 의미가 직관과 다름.
    - Tag 가 8b → 10b extended 로 늘어난 것은 outstanding NP 가 256 개 → 1024 개로 확장. Sender 의 max outstanding 추적 필요.
    - Posted 라고 해서 ACK/NAK 까지 없는 게 아님 — DLL ACK 는 발생. 단지 TL 응답 없음.
    - ECRC 는 optional 이라 disabled 인 경우가 흔함. AER 카운터 0 이라고 안전한 게 아니라 ECRC 자체가 꺼져 있을 수 있음.

---

## 다음 모듈

→ [Module 04 — DLLP, Flow Control, ACK/NAK](04_dllp_flow_control.md)
