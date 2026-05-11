# Module 02 — 3-Layer Architecture

<!-- DV-SKOOL-CH-CTX:start -->
<div class="chapter-context" data-cat="intercon">
  <a class="chapter-back" href="../">
    <span class="chapter-back-arrow">←</span>
    <span class="chapter-back-icon">🔌</span>
    <span class="chapter-back-text">PCI Express</span>
  </a>
  <span class="chapter-divider">›</span>
  <span class="chapter-marker">Module 02</span>
</div>
<!-- DV-SKOOL-CH-CTX:end -->

<!-- DV-SKOOL-CH-TOC:start -->
<div class="page-toc">
  <span class="page-toc-label">목차</span>
  <a class="page-toc-link" href="#1-why-care-이-모듈이-왜-필요한가">1. Why care?</a>
  <a class="page-toc-link" href="#2-intuition-국제-운송의-3-단계-비유와-한-장-그림">2. Intuition</a>
  <a class="page-toc-link" href="#3-작은-예-64-byte-mwr-한-개가-3-layer-를-내려가는-과정">3. 작은 예 — 64B MWr 의 3 layer 통과</a>
  <a class="page-toc-link" href="#4-일반화-3-layer-의-책임-분리와-packet-단위">4. 일반화 — 3 layer 책임 분리</a>
  <a class="page-toc-link" href="#5-디테일-tl-dll-pl-의-내부-block-과-규칙">5. 디테일</a>
  <a class="page-toc-link" href="#6-흔한-오해-와-dv-디버그-체크리스트">6. 흔한 오해 + DV 디버그 체크리스트</a>
  <a class="page-toc-link" href="#7-핵심-정리-key-takeaways">7. 핵심 정리</a>
</div>
<!-- DV-SKOOL-CH-TOC:end -->

!!! objective "학습 목표"
    이 모듈을 마치면:

    - **Diagram** PCIe 의 3 계층 (Transaction / Data Link / Physical) 과 sub-block 을 그릴 수 있다.
    - **Distinguish** 각 layer 가 처리하는 packet 단위 (TLP / DLLP / Ordered Set + symbol) 을 구분한다.
    - **Trace** memory write 가 application → TLP → DLL 추가 (sequence #, LCRC) → PHY 추가 (STP/END, encoding) 까지 가는 흐름을 추적한다.
    - **Apply** 각 layer 의 책임 분리가 디버그/검증에서 어떤 이점을 주는지 시나리오에 매핑한다.
    - **Justify** PCIe 의 "신뢰성은 DLL 의 일" 이라는 명제를 PHY BER ≠ 0 이라는 사실과 함께 정당화한다.

!!! info "사전 지식"
    - Module 01 (point-to-point + lane 모델)
    - 일반 OSI 계층 개념

---

## 1. Why care? — 이 모듈이 왜 필요한가

**모든 PCIe spec 의 기능 분류와 디버그 분류가 "어느 layer 의 일?"** 에서 출발합니다. AER (Module 07) 의 error class, retry 메커니즘 (Module 04), LTSSM (Module 05) 모두 layer 책임이 명확히 분리된 상태에서 정의됩니다.

이 모듈의 어휘 — **Transaction / Data Link / Physical, TLP / DLLP / Ordered Set, ECRC / LCRC** — 가 이후 모든 packet trace, scoreboard 비교, AER 카운터 해석의 기본 단위. 이 layer 모델을 머리에 정확히 넣어 두면 "이 에러는 LCRC error" 라는 한 줄로 즉시 어느 layer 의 어느 메커니즘이 동작했는지 그릴 수 있게 됩니다.

---

## 2. Intuition — 국제 운송의 3 단계 비유와 한 장 그림

!!! tip "💡 한 줄 비유"
    **PCIe 3 layer** ≈ **국제 화물 운송의 3 단계**.<br>
    **Transaction** = 송장 + 화물 명세 (무엇을 어디로). <br>
    **Data Link** = 운송중 분실/파손 보험 (sequence #, LCRC, ACK/NAK). <br>
    **Physical** = 실제 운송수단 (트럭, 비행기 = serial link, equalization). <br>
    각 단계가 자기 책임만 처리. Transaction layer 는 운송수단을 모르고, Physical 은 화물 내용을 모름.

### 한 장 그림 — 송신 path 와 layer 별 wrapper

```
       Sender                                                Receiver
       ──────                                                ────────
   App: "host PA 0x10000 에 64 B write"                  App: 메모리에 적용
            │                                                  ▲
            ▼                                                  │
   ┌── Transaction Layer ───┐                       ┌── Transaction Layer ─┐
   │  TLP = [Hdr | Payload  │                       │  TLP 분해 + ECRC 검증│
   │        | (ECRC?)]      │                       └─────────▲────────────┘
   └─────────┬──────────────┘                                 │
             │ TLP                                            │ TLP
             ▼                                                │
   ┌── Data Link Layer ─────┐                       ┌── Data Link Layer ───┐
   │  +Seq# +LCRC           │ ─── Replay Buffer ──▶ │  LCRC verify         │
   │  ACK/NAK 처리           │                       │  ACK/NAK 송신        │
   └─────────┬──────────────┘                       └─────────▲────────────┘
             │ TLP+Seq+LCRC, DLLP                             │ TLP+Seq+LCRC
             ▼                                                │
   ┌── Physical Layer ──────┐                       ┌── Physical Layer ────┐
   │  STP/END framing       │                       │  Frame detect        │
   │  Scrambling+Encoding   │                       │  Decode+Descramble   │
   │  Lane stripe           │                       │  Lane de-stripe      │
   │  SerDes                │ ────────  wire ─────▶ │  CDR + EQ            │
   └────────────────────────┘                       └──────────────────────┘
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

```
   Device Core: "host PA 0x10000 에 64 byte write 요청"
        │
        ▼
   TL  : MWr TLP 생성 (Fmt=10, Type=00000, Length=16 DW, Address=0x10000, payload 64 byte)
        │
        ▼
   TL  : FC credit 차감 (P credit), ECRC 옵션 추가
        │
        ▼
   DLL : Seq# = 0x123, LCRC 계산 ([Seq# + TLP] 위로 32-bit CRC), Replay Buffer 에 [Seq#=0x123, TLP] 저장
        │
        ▼
   PL  : Framing (STP token + TLP + END token), 128b/130b encoding, scrambling, lane stripe → SerDes → wire
        │
        ▼
   ──── Wire ────
        │
        ▼
   PL  (rx): CDR, lane de-stripe, 130b → 128b decoding, descrambling, framing detect
        │
        ▼
   DLL (rx): LCRC 검증 OK → Seq# 수락 → ACK DLLP 송신
                                        Seq# 실패 → NAK DLLP 송신
        │
        ▼
   TL  (rx): FC credit 반환, TLP 처리 (memory write 적용), payload 수신 완료
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
// Sender 측 layer wrapper 의 의사코드 — 각 layer 가 자기 책임만
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

!!! note "여기서 잡아야 할 두 가지"
    **(1) 각 layer 가 자기 책임만 처리한다 — Transaction layer 는 PHY 의 BER 을 모르고, Physical 은 TLP 의 의미를 모른다.** 이 추상화 경계가 디버그에서 "어느 layer 의 증상?" 라는 첫 질문의 정당성.<br>
    **(2) Wrapper 는 양방향 비대칭이다 — 송신은 추가, 수신은 제거.** TL/DLL/PL 마다 어떤 wrapper 가 추가됐는지 알아야 packet trace 의 byte stream 을 layer 별로 분해해서 읽을 수 있다.

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

→ **모든 PCIe link 의 retransmission 은 DLL 책임.** PHY 의 BER 이 아무리 낮아도 0 이 아니므로 packet-level reliability 가 필요.

### 4.3 디버그 흐름의 직선화

```
   증상 발견
      │
      ▼
   어느 layer 의 일인가?
      │
      ├─ TLP type / address 잘못          → TL
      ├─ LCRC error / replay 빈발         → DLL
      ├─ Link 자체가 안 올라옴            → PL (LTSSM)
      ├─ Specific BAR 만 fail            → TL (header field) + Module 06
      └─ AER counter 증가                 → AER mapping → 해당 layer
```

이 한 단계의 분류가 _80% 의 디버그 케이스_ 를 해결합니다.

---

## 5. 디테일 — TL / DLL / PL 의 내부 block 과 규칙

### 5.1 3 Layer 한 장 뷰

```
   ┌──────────────────────────────────────────────────────┐
   │  Application / Device Core (driver, NIC engine, …)   │
   └────────────────────┬─────────────────────────────────┘
                         │ memory request, completion, message
                         ▼
   ┌──────────────────────────────────────────────────────┐
   │  Transaction Layer                                    │
   │  - TLP 생성/분해 (header + payload + ECRC)            │
   │  - Flow Control credit 관리                            │
   │  - TLP type / routing / address translation           │
   │  - Ordering rules (Posted/Non-Posted/Cpl)            │
   └────────────────────┬─────────────────────────────────┘
                         │ TLP
                         ▼
   ┌──────────────────────────────────────────────────────┐
   │  Data Link Layer                                      │
   │  - Sequence Number 부여                                │
   │  - LCRC 계산 / 검증                                    │
   │  - ACK/NAK 송신, Replay Buffer                        │
   │  - DLLP 송수신 (FC update, ACK/NAK, Power)            │
   │  - Link state (DL_Inactive / Init / Active)          │
   └────────────────────┬─────────────────────────────────┘
                         │ TLP + Seq# + LCRC, DLLP
                         ▼
   ┌──────────────────────────────────────────────────────┐
   │  Physical Layer                                       │
   │  - Framing (STP/END, SDP/EDS)                         │
   │  - Encoding (8b/10b → 128b/130b → PAM4/FLIT)         │
   │  - Scrambling, Lane stripe                            │
   │  - Serializer/Deserializer (SerDes)                  │
   │  - LTSSM (link training)                              │
   │  - Equalization, CDR                                   │
   │  - Ordered Sets (TS1/TS2, EIOS, …)                   │
   └──────────────────────────────────────────────────────┘
```

### 5.2 Transaction Layer (TL) 책임

```
   from device core
        │
        ▼
   ┌────────────────────────┐
   │ TLP Builder            │ ← header, payload, ECRC
   ├────────────────────────┤
   │ Flow Control           │ ← credit available 확인 후 송신
   ├────────────────────────┤
   │ Ordering               │ ← Posted/Non-Posted/Completion 규칙
   ├────────────────────────┤
   │ TLP Routing/Type        │ ← MRd/MWr/CfgRd/CfgWr/Cpl/Msg
   └─────────┬──────────────┘
             │ TLP
             ▼
        Data Link Layer
```

| 기능 | 핵심 |
|------|------|
| **TLP 생성** | Fmt + Type + Length + Address (or BDF) + payload |
| **Flow Control** | P / NP / Cpl 별 header credit + data credit 추적, FC DLLP 로 갱신 |
| **Ordering** | Posted (P) ↔ Non-Posted (NP) ↔ Completion (Cpl) 의 strict ordering 규칙 (PCI legacy 호환) |
| **ECRC (optional)** | end-to-end CRC. 라우팅 노드에서 변경 안 됨. |
| **Address translation** | ATS 사용 시 IOVA → PA 변환 결과 캐시 |

### 5.3 Data Link Layer (DLL) 책임

```
   from TL: TLP
        │
        ▼
   ┌────────────────────────┐
   │ Seq# 부여                │  ← 12-bit sequence number 0..4095
   ├────────────────────────┤
   │ LCRC 계산                │  ← 32-bit Link CRC
   ├────────────────────────┤
   │ Replay Buffer 저장       │  ← ACK 받기까지 보관
   ├────────────────────────┤
   │ ACK/NAK 처리             │  ← 받은 순서대로 ACK, error 시 NAK + replay
   ├────────────────────────┤
   │ DLLP 송신                │  ← FC update, ACK/NAK, PM_*
   └─────────┬──────────────┘
             │ TLP + Seq# + LCRC, DLLP
             ▼
        Physical Layer
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

```
   from DLL: TLP + Seq# + LCRC, DLLP
        │
        ▼
   ┌────────────────────────┐
   │ Framing                 │  ← STP/END (Gen1/2), SDP/EDS (Gen3+)
   ├────────────────────────┤
   │ Scrambling              │  ← LFSR-based, EMI 분산
   ├────────────────────────┤
   │ Encoding                │  ← 8b/10b (Gen1/2) or 128b/130b (Gen3+)
   ├────────────────────────┤
   │ Lane Stripe             │  ← byte-wise round-robin 분산
   ├────────────────────────┤
   │ SerDes                  │  ← 직렬화 → differential pair
   ├────────────────────────┤
   │ LTSSM                   │  ← link bring-up, EQ, recovery
   ├────────────────────────┤
   │ Ordered Sets            │  ← TS1/TS2, FTS, EIOS, SKP
   └─────────┬──────────────┘
             │ analog signal
             ▼
        Wire / connector
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

!!! example "차동 신호 (Differential Signaling) 의 노이즈 제거 — 정량 예시"
    한 lane 은 TX 2 가닥 + RX 2 가닥 = **총 4 핀** (TX+/TX-/RX+/RX-). 송신 시 데이터를 정상 신호(+) 와 역상 신호(-) 두 개로 나눠 한 쌍으로 송출.

    예: 송신 (+0.1V, -0.1V) → **차이 = 0.2V** = 1 로 해석.

    중간에 외부 노이즈가 두 선에 동시에 +0.5V 더해진다고 가정 → 도착 시 (+0.6V, +0.4V).

    수신 측은 **두 신호의 차이만** 계산: 0.6 − 0.4 = **0.2V**. 노이즈는 상쇄되고 원래 값 그대로.

    덕분에 PCIe 는 **수백 mV 수준의 매우 작은 전압 차이** 로도 안정적 통신 가능 — 저전압 + 고속화의 토대.

!!! example "8b/10b vs 128b/130b — encoding 의 본질"
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

### 5.5 송신 흐름 — Memory Write 예 (전체)

위 §3 의 시나리오를 시간 축으로 다시:

```
   Device Core: "host PA 0x10000 에 64 byte write 요청"
        │
        ▼
   TL  : MWr TLP 생성, FC credit 차감, ECRC 옵션
        │
        ▼
   DLL : Seq# + LCRC + Replay Buffer
        │
        ▼
   PL  : Framing + 128b/130b encoding + scrambling + lane stripe → SerDes → wire
        │
        ▼
   ──── Wire ────
        │
        ▼
   PL  (rx): CDR, decode, descramble, framing detect
        │
        ▼
   DLL (rx): LCRC 검증 OK → ACK DLLP 송신
        │
        ▼
   TL  (rx): FC credit 반환, TLP 처리, memory write 적용
```

### 5.6 수신 측 ACK/NAK 의 layer 분리

```
   PL 가 깨진 비트 받음
        │
        ▼
   DLL 의 LCRC 검증 fail
        │
        ▼
   DLL 이 NAK DLLP (with seq# = next expected) 전송
        │ 이 NAK 은 PHY 통해 sender 로 가는데, PHY 자신이 packet 을 만든 게 아님
        ▼
   Sender DLL 이 NAK 받음 → Replay Buffer 에서 해당 Seq# 부터 다시 송신
        │
        ▼
   Replay 횟수 한도 초과 → DL_Inactive → LTSSM Recovery 단계로 넘어감
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

!!! danger "❓ 오해 1 — 'PCIe 의 reliability 는 PHY 가 책임진다 (BER 낮음)'"
    **실제**: Physical 은 raw bit 만 운반하며, **packet-level reliability 는 Data Link Layer 의 ACK/NAK + sequence # + replay buffer** 가 보장. PHY 의 BER 이 아무리 낮아도 0 은 아니므로, 단일 비트 오류가 LCRC 에서 검출되면 DLL 이 재전송. 즉 **PCIe 의 retransmission 은 DLL 의 일**.<br>
    **왜 헷갈리는가**: 일반적으로 "신뢰성 = 물리 quality" 로 단순 연결 짓기 쉬움.

!!! danger "❓ 오해 2 — 'LCRC 와 ECRC 는 같은 CRC 다'"
    **실제**: 둘 다 32-bit CRC 지만 generator polynomial 이 다르고 _범위/책임_ 이 다름. **LCRC** 는 hop 마다 새로 계산 (DLL 책임), **ECRC** 는 end-to-end (TL 책임, optional). Switch 가 TLP forward 할 때 LCRC 는 매 hop 새로 계산하지만 ECRC 는 그대로 둠 — 그래서 ECRC error 는 path 중간 어디선가의 corruption 을 잡아낸다.<br>
    **왜 헷갈리는가**: 둘 다 32-bit, 둘 다 TLP 위에 계산.

!!! danger "❓ 오해 3 — 'Memory Write 는 ACK 가 없으니 unreliable 하다'"
    **실제**: PCIe 의 MWr 은 **TL-level Posted** = TL 응답 없음. 그러나 **DLL 의 ACK/NAK 은 발생** — receiver 의 DLL 이 packet 을 정상 받으면 ACK DLLP 가 sender 로 가고 Replay buffer 에서 해당 entry 가 retire. 따라서 **link-level 신뢰성은 보장**, 단지 application-level "내 write 가 정말 처리됐는가" 는 별도 확인 필요 (Module 03).<br>
    **왜 헷갈리는가**: "Posted" 와 "응답 없음" 을 link 전체로 해석.

!!! danger "❓ 오해 4 — 'TLP, DLLP 는 같은 channel 의 다른 이름이다'"
    **실제**: TLP 는 Transaction layer 의 packet, DLLP 는 Data Link layer 의 packet. PHY 위에서는 둘 다 byte stream 이지만 **framing token 이 다름** — TLP 는 STP/END (Gen1/2) 또는 SDP-like (Gen3+), DLLP 는 별도 framing. Trace 도구가 layer 별 column 을 안 보여주면 ACK/NAK timing 추적 불가.

!!! danger "❓ 오해 5 — 'Layered 라서 layer 끼리 완전히 독립적이다'"
    **실제**: 송신 path 의 wrapper 는 _layered_ 지만, 일부 정보는 layer 경계를 넘어 흐른다. 예: DLL 의 FC DLLP 는 sender 의 TL 이 송신 가능 여부 판단에 사용. AER 은 PHY/DLL 의 error 를 TL 의 capability 로 reporting. **Layer 분리 = 책임 분리이지 정보 단절은 아님**.

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

!!! warning "실무 주의점"
    - "TLP" 와 "DLLP" 의 구분이 흐려지는 도구가 있음 — packet trace tool 에서 DLLP 를 별도 column 으로 보지 않으면 ACK/NAK timing 추적 불가.
    - LCRC 와 ECRC 를 혼동하지 말 것 — LCRC 는 hop, ECRC 는 end-to-end. 둘 다 32-bit CRC 지만 generator polynomial 이 다름.
    - Replay buffer 의 size 는 spec 가 아니라 implementation. 작으면 RTT 큰 link 에서 sender stall 발생 (credit 처럼).
    - Gen6 FLIT 모드에서는 layer boundary 가 살짝 변경됨 — TLP/DLLP 가 FLIT 안에 함께 들어가 ACK/NAK 메커니즘이 단순화. 자세한 건 Module 04.

---

## 다음 모듈

→ [Module 03 — TLP](03_tlp.md): TL 의 packet (TLP) 의 header 필드, Fmt/Type 인코딩, P/NP/Cpl ordering, routing 3 가지.

[퀴즈 풀어보기 →](quiz/02_layer_architecture_quiz.md)

--8<-- "abbreviations.md"
--8<-- "_inc/topic_abbr.md"
