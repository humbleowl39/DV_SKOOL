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
  <a class="page-toc-link" href="#왜-이-모듈이-중요한가">왜 이 모듈이 중요한가</a>
  <a class="page-toc-link" href="#핵심-개념">핵심 개념</a>
  <a class="page-toc-link" href="#1-3-layer-한-장-뷰">1. 3 Layer 한 장 뷰</a>
  <a class="page-toc-link" href="#2-각-layer-의-packet-단위">2. 각 layer 의 packet 단위</a>
  <a class="page-toc-link" href="#3-transaction-layer-tl-책임">3. Transaction Layer (TL) 책임</a>
  <a class="page-toc-link" href="#4-data-link-layer-dll-책임">4. Data Link Layer (DLL) 책임</a>
  <a class="page-toc-link" href="#5-physical-layer-pl-책임">5. Physical Layer (PL) 책임</a>
  <a class="page-toc-link" href="#6-송신-흐름-memory-write-예">6. 송신 흐름 — Memory Write 예</a>
  <a class="page-toc-link" href="#7-수신-측-acknak-의-layer-분리">7. 수신 측 ACK/NAK 의 layer 분리</a>
  <a class="page-toc-link" href="#8-디버그-시-layer-추적">8. 디버그 시 layer 추적</a>
  <a class="page-toc-link" href="#핵심-정리-key-takeaways">핵심 정리 (Key Takeaways)</a>
  <a class="page-toc-link" href="#다음-모듈">다음 모듈</a>
</div>
<!-- DV-SKOOL-CH-TOC:end -->

!!! objective "학습 목표"
    이 모듈을 마치면:

    - **Diagram** PCIe 의 3 계층 (Transaction / Data Link / Physical) 과 sub-block 을 그릴 수 있다.
    - **Distinguish** 각 layer 가 처리하는 packet 단위 (TLP / DLLP / Ordered Set + symbol) 을 구분한다.
    - **Trace** memory write 가 application → TLP → DLL 추가 (sequence #, LCRC) → PHY 추가 (STP/END, encoding) 까지 가는 흐름을 추적한다.
    - **Apply** 각 layer 의 책임 분리가 디버그/검증에서 어떤 이점을 주는지 시나리오에 매핑한다.

!!! info "사전 지식"
    - Module 01 (point-to-point + lane 모델)
    - 일반 OSI 계층 개념

## 왜 이 모듈이 중요한가

**모든 PCIe spec 의 기능 분류와 디버그 분류가 "어느 layer 의 일?"** 에서 출발합니다. AER (Module 07) 의 error class, retry 메커니즘 (Module 04), LTSSM (Module 05) 모두 layer 책임이 명확히 분리된 상태에서 정의됩니다.

!!! tip "💡 이해를 위한 비유"
    **PCIe 3 layer** ≈ **국제 화물 운송**

    - Transaction = 송장 + 화물 명세 (무엇을 어디로)
    - Data Link = 운송중 분실/파손 보험 (sequence #, LCRC, ACK/NAK)
    - Physical = 실제 운송수단 (트럭, 비행기 = serial link, equalization)

    각 단계가 자기 책임만 처리. Transaction layer 는 운송수단을 모르고, Physical 은 화물 내용을 모름.

## 핵심 개념

**PCIe 의 송신 path 는 Transaction Layer (TLP 생성) → Data Link Layer (sequence # + LCRC + replay buffer) → Physical Layer (Framing + 8b/10b or 128b/130b encoding + serialization). 각 layer 가 자신의 packet/wrapper 를 추가하고, 수신 path 는 역순으로 stripping. 디버그/검증은 이 layer 분리 덕에 "어디서 깨졌는지" 가 packet trace 에서 즉시 식별 가능.**

!!! danger "❓ 흔한 오해"
    **오해**: "PCIe 의 reliability 는 PHY 가 책임진다 (BER 낮음)."

    **실제**: Physical 은 raw bit 만 운반하며, **packet-level reliability 는 Data Link Layer 의 ACK/NAK + sequence # + replay buffer** 가 보장. PHY 의 BER 이 아무리 낮아도 0 은 아니므로, 단일 비트 오류가 LCRC 에서 검출되면 DLL 이 재전송. 즉 **PCIe 의 retransmission 은 DLL 의 일**.

    **왜 헷갈리는가**: 일반적으로 "신뢰성 = 물리 quality" 로 단순 연결 짓기 쉬움.

---

## 1. 3 Layer 한 장 뷰

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

---

## 2. 각 layer 의 packet 단위

| Layer | Packet | 길이 | 예 |
|-------|--------|------|----|
| Transaction | **TLP** | 가변 (header 12-16B + payload 0..4096B + opt ECRC 4B) | MRd, MWr, CplD, CfgRd0/1 |
| Data Link | **DLLP** | 8 byte (header + LCRC) | Ack, Nak, FC Init/Update, PM_*, Vendor |
| Physical | **Ordered Set + Symbol** | 가변 | TS1/TS2, FTS, EIOS, EIEOS, SDS, SKP |

→ DLLP 는 Transaction Layer 가 보지 않음. TLP 는 PHY 가 보지 않고 그저 byte stream.

---

## 3. Transaction Layer (TL) 책임

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

---

## 4. Data Link Layer (DLL) 책임

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

---

## 5. Physical Layer (PL) 책임

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

---

## 6. 송신 흐름 — Memory Write 예

```
   Device Core: "host PA 0x10000 에 64 byte write 요청"
        │
        ▼
   TL  : MWr TLP 생성 (Fmt=Memory, Type=Write, Length=16 DW, Address=0x10000, payload 64 byte)
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

---

## 7. 수신 측 ACK/NAK 의 layer 분리

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

---

## 8. 디버그 시 layer 추적

| 증상 | 의심 layer | 확인 |
|------|----------|------|
| Link up 안 됨 | PHY (LTSSM) | LTSSM state, equalization 결과, electrical idle |
| Link up 했지만 packet 안 감 | DLL | DL_Active 진입 여부, FC init complete 여부 |
| TLP 가 가지만 receiver 가 못 받음 | DLL/TL | LCRC error 율, Seq# wraparound, Replay 횟수 |
| Specific TLP 만 fail | TL | Header field 오류 (Fmt/Type/Address), ECRC, ordering 위반 |
| Latency 가 spike | TL/DLL | FC credit 부족, replay 발생 빈도 |
| AER correctable error 카운터 ↑ | DLL/PHY | LCRC, replay number rollover, bad symbol |

---

## 핵심 정리 (Key Takeaways)

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

→ [Module 03 — TLP](03_tlp.md)


--8<-- "abbreviations.md"
--8<-- "_inc/topic_abbr.md"
