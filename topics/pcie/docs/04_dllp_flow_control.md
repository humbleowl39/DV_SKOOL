# Module 04 — DLLP, Flow Control, ACK/NAK

<div class="learning-meta">
  <span class="meta-badge meta-level-advanced">📊 Advanced</span>
</div>

!!! objective "학습 목표"
    이 모듈을 마치면:

    - **List** DLLP 의 종류 (Ack, Nak, FC Init/Update, PM_*, Vendor) 와 8 byte 포맷을 나열한다.
    - **Trace** ACK/NAK 시퀀스와 Replay Buffer 동작을 timeline 으로 추적한다.
    - **Compute** P/NP/Cpl 별 (Header credit + Data credit) 모델로 송신 가능 여부를 판정한다.
    - **Diagram** Gen6 의 FLIT mode 가 ACK/NAK 메커니즘을 어떻게 단순화하는지 그릴 수 있다.

!!! info "사전 지식"
    - Module 02 (DLL 책임)
    - Module 03 (TLP 의 P/NP/Cpl 분리)

## 왜 이 모듈이 중요한가

**Link 가 동작하지 않을 때 80% 는 DLL 영역의 이슈** (FC credit 부족, ACK/NAK loop, Replay buffer overflow). DLLP 와 FC 의 동작을 정확히 알아야 packet trace 에서 stall 의 원인을 찾을 수 있습니다.

!!! tip "💡 이해를 위한 비유"
    **Flow Control credit** ≈ **음식점 좌석 예약**

    - 좌석이 비어야 (credit 있음) 손님 (TLP) 보낼 수 있음.
    - 좌석 종류 (P/NP/Cpl) 마다 별도 카운트 — VIP 좌석 (Cpl) 이 비어도 일반 (P) 이 차면 못 받음.
    - 손님이 식사 끝내면 (TL 처리 완료) 좌석 반환 (FC Update DLLP).
    - 처음에 "좌석 N 개" 알려줌 (FC Init).

## 핵심 개념

**DLLP 는 TL 의 신호 (Flow Control update, ACK/NAK, Power Management) 를 운반하는 8-byte link-only packet. ACK/NAK + 12-bit Sequence Number + Replay Buffer 가 link 의 신뢰성. Flow Control 은 P/NP/Cpl 의 6 개 그룹 (각 H + D) 으로 credit 추적, 송신 전 credit 확인. Gen6 FLIT mode 는 고정 256B 프레임 + FEC 로 ACK/NAK 의 oepoch 단위 변경.**

!!! danger "❓ 흔한 오해"
    **오해**: "ACK 와 FC Update 는 같은 것이다."

    **실제**: 서로 다른 layer 의 다른 메커니즘.

    - **ACK**: "이 sequence # 까지 LCRC 검증 OK 로 받았다" — DLL의 reliability.
    - **FC Update**: "이만큼 credit 이 다시 비었다, 이 만큼 더 보내도 된다" — TL 의 flow control.

    하나는 packet integrity, 다른 하나는 buffer occupancy. 헷갈리면 stall 분석에서 잘못된 결론.

    **왜 헷갈리는가**: 둘 다 receiver → sender 방향 DLLP 라는 공통점 때문.

---

## 1. DLLP 구조 (8 byte 고정)

```
   Byte 0 (Type)   Byte 1-3 (Type-specific) Byte 4-7 (CRC + LCRC)
   ┌──────────┬─────────────────────────────────────┐
   │ Type 8b  │   payload (3 byte)                  │
   ├──────────┼─────────────────────────────────────┤
   │   16-bit DLLP CRC (separate from TLP LCRC)     │
   └────────────────────────────────────────────────┘
```

| Type | DLLP | 설명 |
|------|------|------|
| `0000_0000` | **ACK** | 누적 ACK — Sequence # 까지 수신 OK |
| `0001_0000` | **NAK** | Sequence Number 부터 재송 요청 |
| `0010_VVVV` | **PM_xxx** | Power Management (Enter_L1, Request_Ack, ...) |
| `0011_xxxx` | **Vendor Specific** | 벤더 확장 |
| `01_VC_TYPE` | **InitFC1 / InitFC2 / UpdateFC** | FC initialization / update — VC 와 type (P/NP/Cpl) 인코딩 |

**InitFC1 → InitFC2 → UpdateFC** 의 3 단계로 FC initialization 완료.

---

## 2. ACK / NAK 타임라인

```
   Sender                                         Receiver
   ────────                                       ──────────
   [Replay Buf]
    Seq=10 TLP ───────────────────────────────▶ LCRC OK   → next expected = 11
    Seq=11 TLP ───────────────────────────────▶ LCRC OK   → next expected = 12
    Seq=12 TLP ───────────────────────────────▶ LCRC FAIL → NAK send
                                          ◀── NAK Seq=12
   ↓ NAK 수신
   Replay Buffer 에서 Seq=12 부터 재송신
    Seq=12 TLP ───────────────────────────────▶ LCRC OK   → next expected = 13
    Seq=13 TLP ───────────────────────────────▶ LCRC OK
                                                ACK timer 만료 (또는 packet 누적)
                                          ◀── ACK Seq=13
   ↓ ACK 수신
   Replay Buffer 에서 Seq ≤ 13 entry retire
```

### Replay Buffer

- 송신 후 ACK 받기 전까지 TLP 보관.
- NAK 시 그 Seq# 부터 재송신.
- ACK 시 그 Seq# 까지의 entry retire (메모리 회수).
- **Buffer 가 차면 sender stall** — credit 처럼 동작.

### ACK Coalescing

매 packet 마다 ACK 보내면 비효율. Receiver 는 일정 packet 누적 또는 timer 만료 시 누적 ACK 1 개. spec 의 `AckFactor` parameter 가 양 끝의 협상 결과를 결정.

### Replay Number Rollover

Replay 횟수가 한도 (보통 4) 초과 → DL 가 link recovery 트리거. LTSSM Recovery 단계로 빠짐.

!!! quote "Spec 인용"
    PCIe Base Spec 의 "Data Link Layer Specification > Retry Buffer" 와 "Ack/Nak Protocol" 섹션. (Spec 자체는 PCI-SIG 회원사 비공개)

---

## 3. Sequence Number 12-bit

```
   범위: 0..4095 (modulo 4096)

   Sender
     - Next Transmit Seq# (NTS): 송신할 Seq#
     - Acknowledged Seq# (AckSeq): 마지막 ACK 받은 #

   Receiver
     - Next Receive Seq# (NRS): 받을 것으로 기대하는 Seq#
     - Receive Buffer 의 last good Seq#

   조건: 항상 (NTS - AckSeq) mod 4096 < buffer_size
```

→ Window size = 2048 (modulo 의 절반) 정도가 정상 운영 범위.

---

## 4. Flow Control — 6 Credit Groups

```
   각 Virtual Channel (VC) 마다 독립적으로:
                Header   Data
                ──────   ────
   Posted   :   PH       PD
   Non-Posted:  NPH      NPD
   Completion:  CplH     CplD
```

- Header credit: 1 unit = 4 DW (header size)
- Data credit: 1 unit = 4 DW = 16 byte

**Receiver 의 advertised credit** = receiver 의 RX buffer 가 받을 수 있는 양.

**Sender 의 송신 조건**:

```
   if  TLP 의 header 가 1 unit 이고 payload 가 N DW 이면:
       (used_PH + 1) ≤ credit_limit_PH
       and (used_PD + ceil(N/4)) ≤ credit_limit_PD
   → 만족 시 송신 가능
```

만족 못 하면 **stall** — receiver 가 UpdateFC 로 credit 풀어주기를 기다림.

### Infinite Credit (∞)

일부 카테고리는 spec 가 무한 credit 을 허용 (특히 Completion 의 Header).

→ FC Init1 / Init2 의 "credit advertised value" field 가 0 인 경우 ∞ 의미.

### FC Initialization

```
   Sender                                Receiver
   ─────                                 ────────
   InitFC1 (P, advertised_credit) ────▶
   InitFC1 (NP, ...)              ────▶
   InitFC1 (Cpl, ...)             ────▶
                                      ◀── InitFC1 (P, ...)
                                      ◀── InitFC1 (NP, ...)
                                      ◀── InitFC1 (Cpl, ...)
                                      ◀── InitFC2 (P, ...)
                                      ◀── InitFC2 (NP, ...)
                                      ◀── InitFC2 (Cpl, ...)
   InitFC2 (P) ────▶
   InitFC2 (NP) ────▶
   InitFC2 (Cpl) ────▶

   → 양 끝 모두 FC2 보낸 후 FC initialization complete.
   → DL_Active 상태.
   → 정상 traffic 시작 (UpdateFC 로 credit 갱신).
```

UpdateFC: 현재 credit consumed 의 총합 (modulo) 을 주기적으로 송신.

---

## 5. 디버그 — Stall 의 원인 분류

```
   Sender 가 packet 못 보냄
       │
       ├─ Replay Buffer full ?
       │      → ACK 늦거나 NAK 빈발
       │      → Receiver LCRC error 확인
       │      → Link 의 BER 또는 PHY 문제
       │
       ├─ FC credit 부족 ?
       │      → 어느 그룹? (PH/PD/NPH/NPD/CplH/CplD)
       │      → Receiver 의 TL 이 packet 처리 못 따라가는가
       │      → UpdateFC 주기가 비정상으로 느린가
       │
       ├─ Outstanding NP 한도 초과 ?
       │      → Tag pool 고갈
       │      → 가장 흔한 원인: Completion 늦게 오거나 timeout
       │
       └─ DL_Inactive 로 빠짐 ?
              → LTSSM Recovery 발생
              → 더 깊은 PHY 진단 필요 (Module 05)
```

---

## 6. Gen6 FLIT mode

```
   Pre-Gen6:   가변 길이 TLP/DLLP
   Gen6 FLIT:  고정 256-byte FLIT 프레임
               ┌──────────┬──────────────────────┬──────┬──────┐
               │ FLIT Hdr │ TLP / DLLP payload   │ CRC  │ FEC  │
               │  6 byte  │      236 byte        │ 8B   │ 6B   │
               └──────────┴──────────────────────┴──────┴──────┘
```

| 변화 | 효과 |
|------|------|
| 고정 프레임 | Framing 단순화 (STP/END token 불필요) |
| FEC (Forward Error Correction) | PAM4 의 BER 증가를 보완, single-bit 정정 |
| 통합 ACK/NAK | FLIT 단위로 매 frame ACK 가능 → 늦은 ACK 문제 ↓ |
| FLIT mode 만 지원 | Gen6 이상 link 는 FLIT mode 강제 |

→ Gen5 이하의 ACK/NAK 메커니즘은 그대로 살아 있지만, **Gen6 부터 spec 의 default 가 FLIT mode**.

---

## 7. 검증 (DV) 시 자주 보는 시나리오

| 시나리오 | 목표 |
|---------|------|
| **Replay 강제** | LCRC corruption inject → NAK → replay 정상 동작 확인 |
| **Replay overflow** | ACK 일부러 drop → Replay 횟수 한도 → Recovery 진입 |
| **FC stall** | Receiver TL 의 처리 속도 강제 저하 → credit 부족 → sender stall 검증 |
| **Tag exhaustion** | NP 8b/10b tag pool 고갈 직전 시나리오 |
| **FC update timing** | UpdateFC 주기 변화에 따른 throughput 영향 |
| **Sequence # wraparound** | 4096 packet 보내 wrap 동작 확인 |
| **DLLP CRC fail** | DLLP 자체에 CRC corruption — 어떻게 처리되는지 |

---

## 핵심 정리 (Key Takeaways)

- DLLP = 8-byte link-level packet (Ack, Nak, FC Init/Update, PM_*, Vendor) — TL 이 보지 않음.
- ACK/NAK + Sequence # (12-bit) + Replay Buffer 가 link reliability.
- Flow Control 은 P/NP/Cpl × Header/Data 의 6 credit 그룹 (per VC).
- FC Init: InitFC1 → InitFC1 양방향 → InitFC2 양방향 → DL_Active.
- Gen6 FLIT 는 256B 고정 프레임 + FEC + 단순화된 ACK 메커니즘.

!!! warning "실무 주의점"
    - "Link up 됐는데 traffic 0" 의 99%: FC initialization 미완료 또는 credit advertised = 0 으로 시작.
    - DLLP CRC 와 LCRC 와 ECRC 는 모두 다른 메커니즘 — packet trace 에서 명확히 구분.
    - Replay buffer 는 DUT 마다 size 가 다름. RTT 가 큰 retimer 환경에서는 작은 buffer 가 throughput 의 발목.
    - "ACK 가 안 옴" 의 원인 진단: receiver 가 link 가 down (LTSSM 빠짐) / receiver 의 ACK timer 가 너무 길게 설정 / DLLP 자체가 PHY 에서 깨짐.
    - Gen6 FLIT 모드 검증은 기존 ACK/NAK packet trace 도구가 적용 안 될 수 있음 — FLIT-aware analyzer 필요.

---

## 다음 모듈

→ [Module 05 — Physical Layer & LTSSM](05_phy_ltssm.md)
