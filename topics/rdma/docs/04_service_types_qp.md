# Module 04 — Service Types & QP FSM

<div class="learning-meta">
  <span class="meta-badge meta-level-advanced">📊 Advanced</span>
</div>

!!! objective "학습 목표"
    이 모듈을 마치면:

    - **Compare** RC / UC / UD / XRC 네 가지 service type 의 신뢰성/연결성/지원 opcode 를 표로 비교한다.
    - **Apply** 워크로드 특성을 보고 적절한 service type 을 선택할 수 있다.
    - **Diagram** QP 의 7-state FSM (Reset/Init/RTR/RTS/SQD/SQErr/Err) 과 transition 트리거를 그릴 수 있다.
    - **Trace** Modify QP attribute 호출 시 어떤 attribute 가 어느 상태 transition 에 필요한지 식별한다.

!!! info "사전 지식"
    - Module 02 (BTH OpCode 의 상위 3-bit 가 service type)
    - Verbs API 의 QP 객체 개념 (Module 01)

## 왜 이 모듈이 중요한가

**Service type 선택이 RDMA 시스템 설계의 가장 큰 결정** 입니다 — RC 는 신뢰성을 hardware 가 책임지지만 connection 비용이 크고, UD 는 connectionless 라 scaling 좋지만 user 가 reliability 를 책임집니다. 검증 관점에서도 service type 마다 "어떤 패킷 유형이 합법인가", "어떤 error 가 가능한가" 가 완전히 다릅니다.

QP FSM 은 시스템 검증의 **bring-up 시퀀스의 뼈대** 입니다. RAL 이 Modify QP 의 attribute 를 단계별로 set 하면서 FSM 을 진행시키는 흐름을 정확히 알아야 sequence/test 작성이 가능.

!!! tip "💡 이해를 위한 비유"
    **Service type** ≈ **택배 / 등기우편 / 일반우편 / 그룹발송**

    - RC = 등기 (배송확인 + 분실 시 재배송) ← TCP 와 가장 비슷
    - UC = 일반 택배 (배송, 그러나 분실 시 책임 안 짐) ← 신뢰성 미보장 RDMA
    - UD = 엽서 (1:N 가능, 작은 메시지)
    - XRC = 한 회사 안에서 여러 부서가 같은 수신함 공유

    **QP FSM** ≈ **신용카드 발급 절차**: 신청(Init) → 한도 심사(RTR) → 활성화(RTS) → 정지(SQD/SQErr) → 해지(Err).

## 핵심 개념

**Service Type 은 QP 가 만들어질 때 정해지는 transport semantics: RC (connection + reliable), UC (connection + unreliable), UD (datagram + unreliable, 1:N), XRC (Shared Receive). QP FSM 은 7개 state 로 구성되며, Modify QP verb 가 단계별 attribute 를 set 하면서 Reset → Init → RTR → RTS 를 거쳐야 데이터 송수신이 가능하다.**

!!! danger "❓ 흔한 오해"
    **오해**: "RC 는 packet drop 을 spec 이 보장하므로, 검증 시 packet loss 시나리오는 안 만들어도 된다."

    **실제**: RC 의 reliability 는 **HCA 의 PSN/ACK/retry 메커니즘** 으로 보장됩니다 — 즉 packet drop 은 발생할 수 있고, retry 가 처리. 검증 관점에서 packet drop 시나리오는 **"reliability 가 보장된다는 사실을 확인하기 위해 반드시 inject 해야 하는 시나리오"** 입니다 (RDMA-TB `error_handling/VPLAN_error_handling.md` 의 Local ACK timeout, implied NAK 등).

    **왜 헷갈리는가**: "reliable" 단어를 "packet drop 안 함" 으로 오독.

---

## 1. 네 가지 Service Type

```
       Connection?         Reliability?        Multicast?
       ──────────          ───────────         ──────────
   RC  : Yes (1:1)         Yes (HW-guaranteed) No
   UC  : Yes (1:1)         No                  No
   UD  : No (datagram)     No                  Yes (multicast)
   XRC : Yes (1:N receive) Yes                 No
   RD  : (deprecated/optional in IB)
```

### 비교 표

| 항목 | RC | UC | UD | XRC |
|------|----|----|----|-----|
| 연결성 | 1:1 connection | 1:1 connection | Connectionless | 1:N (shared SRQ) |
| 신뢰성 | ✓ ACK + retry | ✗ | ✗ | ✓ |
| 순서 보장 | ✓ | (대체로) | ✗ | ✓ |
| Max msg size | 2 GB (per WQE) | 2 GB | MTU (single packet) | 2 GB |
| Multicast | ✗ | ✗ | ✓ | ✗ |
| 지원 opcode | SEND/WRITE/READ/ATOMIC | SEND/WRITE | SEND only | SEND/WRITE/READ/ATOMIC |
| 사용 예 | NVMe-oF, MPI | (드물음) | DHCP-style discovery, 작은 RPC | 분산 KV 의 다대다 |
| BTH OpCode 상위 3-bit | `000` | `001` | `010` | `101` (XRC) |

!!! quote "Spec 인용"
    "RC service shall provide reliable, in-order delivery of messages between two QPs." — IB Spec 1.7, §9.7
    "UC service does not provide reliable delivery; if a packet is lost, the message is silently dropped." — §9.8
    "UD service is connectionless and unreliable; each message is contained in a single packet of at most MTU bytes." — §9.8

### Service type 선택 가이드

```
  메시지 < MTU 이고 1:N 멀티캐스트 필요?     → UD
  Reliable + reliable + reliable?            → RC
  Throughput 만 중요, drop OK?               → UC
  같은 receive queue 를 여러 sender 가 공유? → XRC
  WAN, 대륙간?                               → RDMA 보다 TCP 권장
```

---

## 2. QP State Machine — 7 State

```
        ┌──────┐  Modify(Reset)
        │Reset │ ◀──────────────────────────────────────┐
        └──┬───┘                                          │
   Modify(│Init)                                          │
           ▼                                               │
        ┌──────┐                                           │
        │ Init │                                           │
        └──┬───┘                                           │
   Modify(│RTR)                                            │
           ▼                                               │
        ┌──────┐                                           │
        │ RTR  │  Ready To Receive — RX 가능, TX 불가      │
        └──┬───┘                                           │
   Modify(│RTS)                                            │
           ▼                                               │
        ┌──────┐  Modify(SQD) ┌──────┐                     │
        │ RTS  │ ◀──────────  │  SQD │ Send Queue Drain    │
        └──┬───┘  ─────────▶  └──────┘                     │
           │                                               │
        async error / receive                              │
        WC Error / Local Work Queue Error                  │
           │                                               │
           ▼                                               │
        ┌──────┐  ┌────────┐                              │
        │SQErr │  │  Err   │ ────── Modify(Reset) ───────┘
        │      │  │        │
        └──┬───┘  └────┬───┘
           └─────┬─────┘
                 ▼
              (Modify(Reset) 으로만 빠져나옴)
```

| State | 의미 | RX | TX |
|-------|------|----|----|
| **Reset** | 초기. 모든 attribute 미설정. | ✗ | ✗ |
| **Init** | 기본 attribute (PD, port, P_Key, access flag) 설정됨. | ✗ | ✗ |
| **RTR** (Ready-To-Receive) | Receive 측 attribute (RC: remote QPN, dest LID, PSN; UD: Q_Key) 설정됨. | ✓ | ✗ |
| **RTS** (Ready-To-Send) | Send 측 attribute (timeout, retry count, max read atomic, init PSN) 설정됨. **정상 동작 상태**. | ✓ | ✓ |
| **SQD** (Send Queue Drain) | TX 새로 시작 안 함, 이미 in-flight 만 처리. APM 또는 graceful shutdown 용. | ✓ | (in-flight only) |
| **SQErr** (Send Queue Error) | UD/UC 에서 sender side 에러 발생. RX 는 가능, TX 는 새 WR 못 받음. | ✓ | ✗ |
| **Err** | 어느 상태에서든 fatal error → 모든 in-flight WR flush 됨 (WC error). | ✗ | ✗ |

### 진입 조건 (Modify QP attribute)

| Transition | 필요한 attribute (RC 기준) |
|------------|----------------------------|
| Reset → Init | `qp_state, pkey_index, port_num, qp_access_flags` |
| Init → RTR | `path_mtu, dest_qp_num, rq_psn, max_dest_rd_atomic, min_rnr_timer, ah_attr (DLID, SL, ...)` |
| RTR → RTS | `sq_psn, timeout, retry_cnt, rnr_retry, max_rd_atomic` |
| Any → Err | (자동 — async error) |
| Any → Reset | `qp_state = Reset` (clean-up) |

!!! quote "Spec 인용"
    "A QP shall progress through its states only as defined by the QP state machine; the verbs interface shall enforce this ordering." — IB Spec 1.7, §10.3 (R-351 ~ R-390)

---

## 3. RC 의 신뢰성 메커니즘 요약

```
   sender                                      receiver
   ──────                                      ──────────
   PSN=N      ─────── data ──────────▶
   PSN=N+1    ─────── data ──────────▶
   PSN=N+2    ─────── data (A=1) ────▶
                                              ACK PSN=N+2 (coalesced)
              ◀────── ACK ───────────
   PSN=N+2 까지 SQ 에서 retire

   timeout 안에 ACK 못 받으면:
   PSN=N      ──── retransmit ───────▶
                                              ACK PSN=N (다시)
              ◀────── ACK ───────────
```

| 항목 | 값/의미 |
|------|--------|
| **PSN** | 24-bit, 2^24 modulo. 한 message 의 첫 패킷에 init PSN, 이후 +1. |
| **A (AckReq) bit** | sender 가 receiver 에 ACK 요청. coalescing 위해 모든 패킷마다는 아님. |
| **AETH** (ACK ETH) | ACK 패킷에 들어가는 4 byte: syndrome (ACK/NAK 구분) + MSN (Message Sequence Number) |
| **Retry timer** | sender 가 ACK 못 받으면 timer 만료 시 동일 PSN 재전송 |
| **Retry count** | `retry_cnt` 횟수 만큼 시도, 초과 시 QP → Err state + WC error (`IBV_WC_RETRY_EXC_ERR`) |

→ 자세한 흐름은 [Module 06 Data Path](06_data_path.md) 와 [Module 07 Error](07_congestion_error.md) 에서.

---

## 4. UC, UD, XRC 추가 사항

### UC (Unreliable Connection)

- 1:1 connection 이 있으나 ACK 없음.
- SEND, WRITE 만 지원 (READ, ATOMIC 불가 — reliability 필요).
- Packet drop = 메시지 drop, 사용자/상위 layer 가 책임.
- Sequence error 등 일부 에러는 SQErr 상태로 갈 수 있음.

### UD (Unreliable Datagram)

- Connectionless. QP 하나가 임의의 destination 에 SEND 가능 (목적지 마다 AH = Address Handle).
- SEND only. 한 message = 한 packet (≤ MTU − header).
- BTH 다음에 **DETH (8B)** 가 필수: Q_Key + SrcQP.
- Multicast 가능: DLID = multicast LID, MGID 설정.
- Q_Key 검증 필수 (high bit 1 인 Q_Key 는 privileged).

### XRC (eXtended Reliable Connection)

- 한 receive side QP 를 여러 sender QP 가 공유 (target 측 메모리 절약).
- Hyperscale 환경에서 N×N QP polynomial blow-up 완화 목적.
- BTH OpCode 상위 3-bit `101`. XRC ETH 별도 정의.
- IB Spec 1.2.1 부터 옵션, 1.7 에 통합. RoCEv2 도 지원.

---

## 5. 메시지 ↔ 패킷 매핑 (RC SEND, RC WRITE 의 fragmentation)

```
   RC SEND of 8 KB, MTU = 4 KB
   ────────────────────────────────────────
   Packet 1: OpCode = SEND_FIRST   (PSN=N)
   Packet 2: OpCode = SEND_LAST    (PSN=N+1) ← 마지막에 ACK 요청

   RC SEND of 1 KB, MTU = 4 KB
   ────────────────────────────────────────
   Packet 1: OpCode = SEND_ONLY    (PSN=N) ← 한 번에 끝

   RC WRITE of 8 KB
   ────────────────────────────────────────
   Packet 1: OpCode = WRITE_FIRST  (PSN=N)   + RETH (remote VA, R_Key, len)
   Packet 2: OpCode = WRITE_MIDDLE (PSN=N+1)
   Packet 3: OpCode = WRITE_LAST   (PSN=N+2)
                                              ← LAST 또는 LAST_with_IMM 에 A=1 가능
```

- `*_FIRST/MIDDLE/LAST/ONLY` 의 4 변형이 OpCode 하위 5-bit 로 인코딩.
- LAST_WITH_IMMEDIATE (`*_LAST_W_IMM`) 는 ImmDt header 추가.

---

## 6. RDMA-TB 에서의 QP / Service 검증 포인트

| 검증 영역 | 시나리오 |
|-----------|----------|
| **State transition 합법성** | Reset → RTR (skip Init) 시도 → 거부되어야 함 |
| **Attribute 일관성** | RTR 진입 시 dest_qp_num 미설정 → Modify 실패 |
| **PSN window 확인** | sender PSN 이 expected window 밖 → NAK or silent drop (spec 의해) |
| **Service type 별 illegal opcode** | UC QP 에 RDMA READ → WC error |
| **UD Q_Key 검증** | UD recv 시 wrong Q_Key → silent drop (spec) |
| **Multi-packet message** | FIRST/MIDDLE/LAST 일관성 (RETH 는 FIRST/ONLY 에만) |
| **RC retry 동작** | ACK 일부러 drop → retry 동작, retry_cnt 초과 → QP Err |
| **QP recovery** | Err 상태에서 Reset → Init → ... 재진입 가능해야 함 |

이 시나리오들은 [Module 08 RDMA-TB DV](08_rdma_tb_dv.md) 에서 vplan 과 매핑됨.

---

## 핵심 정리 (Key Takeaways)

- 4 service type — RC/UC/UD/XRC — 각각 신뢰성·연결성·지원 opcode 가 다름.
- QP FSM 7 state — Reset/Init/RTR/RTS/SQD/SQErr/Err — 데이터 송수신 가능 상태는 RTR (RX) / RTS (RX+TX) 만.
- Modify QP 시 **상태마다 필수 attribute 가 정해져 있음** — bring-up sequence 의 뼈대.
- RC 의 reliability 는 PSN + ACK + retry + AETH 로 구성, hardware 책임.
- UD 는 datagram + multicast, DETH 와 Q_Key 검증.

!!! warning "실무 주의점"
    - "init PSN" 이 양 끝에서 다를 수 있음 (RC 는 sender PSN ↔ receiver expected PSN 별도). 검증 시 RAL 으로 read-back 으로 확인.
    - UC 에서 packet drop = 메시지 silent loss → scoreboard 가 그것을 정상으로 처리해야 false fail 안 남.
    - UD 의 max payload 는 MTU − (Eth+IP+UDP+BTH+DETH+ICRC) 로 계산해야 함 — 단순 MTU 가 아님.
    - XRC 검증은 SRQ (Shared Receive Queue) 행동까지 함께 봐야 함.

---

## 다음 모듈

→ [Module 05 — Memory Model: PD/MR/L_Key/R_Key/IOVA](05_memory_model.md)
