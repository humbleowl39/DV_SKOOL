# Module 06 — Data Path Operations

<div class="learning-meta">
  <span class="meta-badge meta-level-advanced">📊 Advanced</span>
</div>

!!! objective "학습 목표"
    이 모듈을 마치면:

    - **List** RC service 의 주요 OpCode (SEND/WRITE/READ/ATOMIC) 와 multi-packet 변형 (FIRST/MIDDLE/LAST/ONLY).
    - **Trace** RDMA WRITE 8KB (multi-packet) 의 packet sequence + PSN + ACK 흐름을 시간축으로 추적한다.
    - **Compute** 24-bit PSN 의 wrap-around 와 receiver expected PSN window (2^23) 가정에서 valid/invalid PSN 을 판정한다.
    - **Apply** AETH syndrome (ACK / RNR / Sequence Error / Invalid Request) 을 시나리오에 매핑한다.

!!! info "사전 지식"
    - Module 02 (BTH OpCode 인코딩)
    - Module 04 (RC service, PSN 24-bit)
    - Module 05 (RETH 의 rkey/remote_va)

## 왜 이 모듈이 중요한가

**Data path 가 RDMA 검증의 비중상 80% 입니다.** Connection setup 은 한 번이지만 data path 는 시뮬레이션 매 cycle 마다 동작 — 모든 PSN 산정, OpCode, ACK 발생, retry 행동을 정확히 모델링해야 scoreboard 가 거짓 보고를 안 합니다.

!!! tip "💡 이해를 위한 비유"
    **Multi-packet RDMA WRITE** ≈ **여러 페이지로 나눠 보내는 팩스**

    첫 장 (FIRST) 에 표지(=RETH: 어디로 보내라 + 보호 코드) 를 붙이고, 중간 장 (MIDDLE) 은 페이지 번호 (PSN) 만, 마지막 장 (LAST) 에 "확인 응답 부탁" (A=1) 을 표시. 받는 쪽은 PSN 으로 누락 검출, 마지막에 ACK 한 번.

## 핵심 개념

**Data path 는 OpCode (BTH) 가 정의하는 transaction (SEND/WRITE/READ/ATOMIC) 을, message 단위로 발신하고 multi-packet 인 경우 FIRST/MIDDLE/LAST 변형으로 fragment. PSN 24-bit 가 packet 단위 순서 보장. RC 의 신뢰성은 sender 의 retry timer + receiver 의 ACK + AETH syndrome (ACK/RNR/Seq Err/Inv Req) 으로 구성.**

!!! danger "❓ 흔한 오해"
    **오해**: "RDMA READ 는 1 packet 으로 된다."

    **실제**: RDMA READ Request 는 1 packet (BTH + RETH) 이지만, READ Response 는 Read 길이가 MTU 보다 크면 multi-packet 으로 옴 — `RD_RESP_FIRST`, `RD_RESP_MIDDLE`, `RD_RESP_LAST`, `RD_RESP_ONLY` 의 4 변형. 그리고 multi-outstanding READ 가 있으므로 (RNR/depth) 검증 시 `max_rd_atomic` (sender) ↔ `max_dest_rd_atomic` (responder) 의 일치 여부도 봐야 함.

    **왜 헷갈리는가**: SEND/WRITE 는 sender → receiver 방향만 다루지만 READ 는 양방향이라 모델링이 두 배.

---

## 1. RC OpCode 카탈로그

BTH OpCode 8-bit = 상위 3-bit (service type) + 하위 5-bit (operation).
RC service 의 상위 3-bit = `000`.

| OpCode (RC) | 값 | 설명 | xTH |
|-------------|----|------|-----|
| SEND_FIRST | 0x00 | Multi-packet SEND 첫 패킷 | — |
| SEND_MIDDLE | 0x01 | 중간 패킷 | — |
| SEND_LAST | 0x02 | 마지막 (no IMM) | — |
| SEND_LAST_w_IMM | 0x03 | 마지막 + Immediate Data | ImmDt |
| SEND_ONLY | 0x04 | 단일 패킷 SEND | — |
| SEND_ONLY_w_IMM | 0x05 | 단일 + IMM | ImmDt |
| RDMA_WRITE_FIRST | 0x06 | RDMA WRITE 첫 패킷 (RETH 포함) | RETH |
| RDMA_WRITE_MIDDLE | 0x07 | 중간 | — |
| RDMA_WRITE_LAST | 0x08 | 마지막 | — |
| RDMA_WRITE_LAST_w_IMM | 0x09 | 마지막 + IMM | ImmDt |
| RDMA_WRITE_ONLY | 0x0A | 단일 (RETH 포함) | RETH |
| RDMA_WRITE_ONLY_w_IMM | 0x0B | 단일 + IMM | RETH + ImmDt |
| RDMA_READ_REQUEST | 0x0C | READ 요청 (1 패킷) | RETH |
| RDMA_READ_RESPONSE_FIRST | 0x0D | READ 응답 첫 패킷 | AETH |
| RDMA_READ_RESPONSE_MIDDLE | 0x0E | 중간 응답 | — |
| RDMA_READ_RESPONSE_LAST | 0x0F | 마지막 응답 | AETH |
| RDMA_READ_RESPONSE_ONLY | 0x10 | 단일 응답 | AETH |
| ACKNOWLEDGE | 0x11 | ACK / NAK | AETH |
| ATOMIC_ACKNOWLEDGE | 0x12 | Atomic 응답 | AETH + AtomicAckETH |
| CMP_SWAP | 0x13 | Compare and Swap | AtomicETH |
| FETCH_ADD | 0x14 | Fetch and Add | AtomicETH |
| SEND_LAST_w_INV | 0x16 | Send + Invalidate | IETH |
| SEND_ONLY_w_INV | 0x17 | Single Send + Inv | IETH |

(UC/UD 는 다른 prefix; XRC 는 또 다른 prefix. 여기서는 RC 만 다룸)

!!! note "Why _w_IMM, _w_INV?"
    - **IMM (Immediate Data)** 4-byte: receiver 의 RECV WR 에 함께 전달되어 user payload 외 별도 channel 신호. RECV CQE 에 보임.
    - **INV (Invalidate)** : SEND 가 도착하면 receiver 의 특정 R_Key 를 invalidate. one-side RDMA 후 invalidate 전송 패턴.

---

## 2. Multi-packet Message 의 일관성

```
   RC SEND of 12 KB, MTU = 4 KB
   ──────────────────────────────────
   Pkt 1: PSN=N    SEND_FIRST   payload 4 KB
   Pkt 2: PSN=N+1  SEND_MIDDLE  payload 4 KB
   Pkt 3: PSN=N+2  SEND_LAST    payload 4 KB     A=1
                                                 ↑ ACK 요청
   ◀──────  ACK  PSN=N+2 ─────
```

검증해야 할 일관성 (R-rule level):

| 일관성 | Spec 근거 |
|--------|----------|
| RETH 는 RDMA_WRITE_FIRST / RDMA_WRITE_ONLY 에만 존재 | C9-... |
| 같은 message 내 모든 packet 의 PSN 은 단조 +1 | C9-... |
| 각 packet 의 byte length ≤ MTU | C9-..., R-074 |
| FIRST/MIDDLE/LAST 의 sequencing 위반 시 NAK Inv Req | R-218~ |
| RDMA WRITE LAST 의 length 가 RETH 의 selected total length 와 일치 | C9-... |
| ATOMIC 은 single packet (8 byte payload) 으로만 | spec |

---

## 3. PSN 24-bit 와 Window 모델

```
   PSN 공간 = 0 ~ 2^24-1 = 16777215
   Window = 2^23 = 8388608 (절반)

   sender 측 ePSN (expected next to send)
   receiver 측 ePSN (expected next to receive)

   Receiver 가 packet 받으면:
     - PSN == ePSN          → 정상, ePSN += 1, ACK 가능
     - PSN ∈ [ePSN-2^23, ePSN-1]   → 중복(이미 처리), ACK PSN 다시 보내기
     - PSN ∈ [ePSN+1, ePSN+2^23-1] → 미래(out-of-order), drop or NAK Seq Err
     - 나머지                       → 매우 오래된 / 잘못된 — discard
```

```
                ─────── 2^24 modulo arithmetic ───────
   ePSN-2^23           ePSN (next expected)        ePSN+2^23-1
        │                  │                              │
        ◀── 중복 영역 ─────│────── 미래 영역 ─────────────▶
                            ▲
                       정확히 이 값만 정상
```

- **2^23 가 한쪽에 8M packet/4KB MTU = 32 GB 전송분** — 정상 deployment 에서 wrap 까지 도달하기 충분히 김.
- **PSN init** 은 random (보안상). RTR 진입 시 dest_qp 의 init PSN 을 양 끝에서 modify QP 로 합의.

!!! quote "Spec 인용"
    "The PSN window for a given QP shall be 2^23." — IB Spec 1.7, §9.7.2 (R-198)

---

## 4. ACK / NAK / AETH

### AETH (4 byte)

```
 Byte 0:  Syndrome (8 bit)
 Byte 1-3: Message Sequence Number (MSN, 24 bit)
```

**Syndrome 인코딩**:

| Syndrome | 의미 |
|---------|------|
| `0_xxxxxxx` (top bit 0) | ACK — credit count 가 하위 5-bit |
| `01100000` (0x60) | RNR NAK — Receiver Not Ready |
| `01100001 ~ 01111111` | (RNR timer values 인코딩) |
| `10000000` (0x80) | NAK PSN Sequence Error |
| `10000001` (0x81) | NAK Invalid Request |
| `10000010` (0x82) | NAK Remote Access Error |
| `10000011` (0x83) | NAK Remote Operational Error |
| `10000100` (0x84) | NAK Invalid R-Key (RNR variant 으로 호환) |

→ 사용자 표현은 보통 `IBV_WC_*` (e.g., `IBV_WC_REM_ACCESS_ERR`) 로 매핑.

### ACK Coalescing

매 패킷마다 ACK 보내면 비효율 → 일정 packet 마다 한 번 (`A` bit 가 켜진 패킷에서). 마지막 packet (`*_LAST`/`*_ONLY`) 은 보통 A=1.

```
   Pkt N    A=0
   Pkt N+1  A=0
   Pkt N+2  A=0
   Pkt N+3  A=1   ← 여기에 ACK 발생, PSN=N+3 한 번에 ack (coalesced)
```

→ 검증 시 sender 가 A=1 보낸 후 timeout 안에 ACK 못 받으면 retry.

### Retry Timer

```
   timeout = 4.096 us × 2^retry_timer
   (retry_timer 4-bit, 0..14, 15 reserved)
```

`retry_timer = 14` ≈ 0.5 sec.
`retry_cnt` 는 별도 (몇 번 retry 시도). 초과 시 **`IBV_WC_RETRY_EXC_ERR`** + QP → Err.

!!! quote "Spec 인용"
    "The local ACK timeout value shall be 4.096 × 2^Local ACK Timeout microseconds." — IB Spec 1.7, §9.7.5

---

## 5. RNR — Receiver Not Ready

RC SEND 가 도착했는데 receiver 의 RQ 에 사용가능한 RECV WR 이 없으면:

- responder 가 **RNR NAK** (syndrome 0x60..0x7F) 보냄, syndrome 의 하위 비트가 sender 가 기다려야 할 시간
- sender 는 RNR 만큼 기다린 뒤 retransmit
- `rnr_retry` 횟수 (0..7, 7 = infinite) 초과 시 QP → Err + `IBV_WC_RNR_RETRY_EXC_ERR`

```
   sender ────── SEND PSN=N ───────▶
                                       (RQ 비어있음)
          ◀───── AETH RNR (timer 5) ──
   wait …
   sender ────── SEND PSN=N (retry) ─▶
                                       (이번에 RQ 에 WR 있음)
          ◀───── ACK PSN=N ──────────
```

→ **WRITE/READ 는 RNR 안 일어남** (RECV WR 필요 없음).

---

## 6. RDMA READ — 양방향 흐름

```
   requester                                    responder
   ────────                                     ──────────
   Post WR: RDMA_READ_REQUEST                   (대기)
   Pkt 1: PSN=N, OpCode=READ_REQUEST,  ────▶
            RETH(remote_va, len, rkey)

                                               (rkey 검증, IOVA 변환,
                                                local memory 읽기)

                                               len > MTU 면 multi-packet
                                               응답 생성
          ◀── PSN=N    READ_RESP_FIRST   AETH(ACK) + payload
          ◀── PSN=N+1  READ_RESP_MIDDLE        + payload
          ◀── PSN=N+2  READ_RESP_LAST    AETH(ACK) + payload
   (모든 응답 받으면 WC 생성)
```

### 핵심 attribute

- **`max_rd_atomic`** (sender side) : 동시 outstanding READ/ATOMIC 갯수
- **`max_dest_rd_atomic`** (responder side) : 동시 처리 가능한 RDMA READ/ATOMIC depth
- 두 값의 mismatch 가 자주 검증되는 corner.

### Read 의 PSN 사용 규칙

- READ Request packet: PSN = N
- READ Response packets: 동일하게 PSN = N, N+1, N+2 ... (응답이 PSN 영역을 차지)
- 즉 READ 1번이 response 길이 만큼 PSN 을 소비.

---

## 7. ATOMIC — CMP_SWAP, FETCH_ADD

```
   AtomicETH (28 byte):
     virtual address (8B)  ← 8-byte aligned target
     R_Key             (4B)
     swap_data (or add)(8B)
     compare_data      (8B)
```

```
   sender ─── CMP_SWAP PSN=N, AtomicETH(VA, rkey, swap, cmp) ──▶
                                          (responder 가 atomically:
                                            old = mem[VA]
                                            if old == cmp: mem[VA] = swap )
          ◀── ATOMIC_ACK PSN=N, AETH + AtomicAckETH(orig_data) ──
```

### 일관성

- ATOMIC 은 항상 single packet (payload 8B).
- Multiple ATOMIC 동시 처리는 `max_dest_rd_atomic` 에 포함.
- ATOMIC vs ordinary RDMA WRITE 는 ordering 규칙이 다름 (spec §9.6.5).

---

## 8. Ordering Rules — Transaction Ordering

IB spec §9.6 에는 transaction ordering 의 정밀한 규칙이 있음. 핵심:

| 규칙 | 내용 |
|------|------|
| Same-QP same-stream 의 packet 은 in-order | RC/UC/UD 모두 |
| RDMA WRITE 의 byte order 는 정의됨 (LSB → MSB?) | spec 의 word ordering 그림 |
| ATOMIC 은 별도 ordering category — 다른 ATOMIC, RDMA READ 와의 순서 관계 | §9.6.5 |
| RDMA READ Response 의 도착 순서 | sender 의 send 순서와 같지 않을 수 있음, but PSN 으로 정렬 |
| Fence 옵션 | WR 에 `IBV_SEND_FENCE` 주면 이 WR 이전의 모든 RDMA READ/ATOMIC 가 완료된 후 발신 |

검증 관점: **scoreboard 가 spec 의 ordering 모델을 정확히 알아야 false positive 없음**. RDMA-TB 의 `vrdma_data_scoreboard` 가 이를 처리.

---

## 9. Data Path Timing (RC SEND 8KB, MTU=4KB) 상세 예

```
   t0:  sender post WR (8 KB SEND, A=1 on last)
   t1:  sender HCA 가 sg_list lkey 검증
   t2:  sender HCA 가 packet 1 fetch (4KB)
   t3:  Packet on wire: PSN=100 SEND_FIRST
   t4:  Packet on wire: PSN=101 SEND_LAST   A=1
   t5:  Receiver HCA 가 packet 1 받음, RQ 에서 RECV WR fetch
   t6:  IOVA→PA 변환, DMA write 4 KB
   t7:  Receiver HCA 가 packet 2 받음 (PSN=101)
   t8:  나머지 4 KB DMA write
   t9:  Receiver HCA 가 ACK PSN=101 + RECV CQE 생성
   t10: Sender HCA 가 ACK 받음, SQ 에서 WR retire, SEND CQE 생성
```

→ RDMA-TB 의 cycle-accurate sim 에서는 t1~t10 의 순서/지연이 모두 정해진 spec 또는 design 의 promise. scoreboard 는 이 시퀀스가 깨지면 fail.

---

## 핵심 정리 (Key Takeaways)

- OpCode 가 모든 transaction 을 정의. RC 만 해도 25개 가량.
- Multi-packet message 는 FIRST/MIDDLE/LAST/ONLY + RETH/AETH 위치 규칙을 따라야 함.
- PSN 24-bit + 2^23 window 가 receiver 의 정상/중복/미래 분류의 기준.
- AETH syndrome 이 ACK/RNR/Seq Err/Inv Req/Access Err 등 모든 transport 에러 신호.
- RDMA READ 는 양방향 multi-packet, ATOMIC 은 always single + 별도 ordering.
- Ordering rule (§9.6) 은 scoreboard 의 핵심 — fence/barrier/atomic 별로 차등 적용.

!!! warning "실무 주의점"
    - "PSN 단조 증가" 는 modulo 2^24 — wrap 시 비교 함수가 modulo-aware 여야 함. 단순 `>` 비교는 버그.
    - RNR retry 와 일반 retry 의 counter 가 분리 — 둘 다 spec 상 별도 attribute.
    - RDMA READ Response 의 첫 패킷에 AETH 가 들어감 (ACK 의 역할 겸용). MIDDLE 에는 AETH 없음 — 이걸 헷갈리면 packet decoder 가 깨짐.
    - ATOMIC 은 8-byte align 강제 — spec 에서 misalign 시 NAK Inv Req. 검증에서 일부러 inject 해 거부되는지 확인.

---

## 다음 모듈

→ [Module 07 — Congestion Control & Error Handling](07_congestion_error.md)
