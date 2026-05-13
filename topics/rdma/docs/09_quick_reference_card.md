# Module 09 — Quick Reference Card

<!-- DV-SKOOL-CH-CTX:start -->
<div class="chapter-context" data-cat="network">
  <a class="chapter-back" href="../">
    <span class="chapter-back-arrow">←</span>
    <span class="chapter-back-icon">⚡</span>
    <span class="chapter-back-text">RDMA</span>
  </a>
  <span class="chapter-divider">›</span>
  <span class="chapter-marker chapter-quickref-marker">★ Quick Reference</span>
</div>
<!-- DV-SKOOL-CH-CTX:end -->

<!-- DV-SKOOL-CH-TOC:start -->
<div class="page-toc">
  <span class="page-toc-label">목차</span>
  <a class="page-toc-link" href="#1-why-care-이-카드를-언제-펴는가">1. Why care?</a>
  <a class="page-toc-link" href="#2-intuition-카드-의-구성-원리">2. Intuition</a>
  <a class="page-toc-link" href="#3-작은-예-자주-펼치는-3-시나리오">3. 작은 예 — 자주 펼치는 3 시나리오</a>
  <a class="page-toc-link" href="#4-일반화-카드-15-영역의-목차">4. 일반화 — 카드 영역 목차</a>
  <a class="page-toc-link" href="#5-디테일-reference-표-전체">5. 디테일 — Reference 표 전체</a>
  <a class="page-toc-link" href="#6-30-second-mental-checklist-와-자주-틀리는-항목">6. 30-sec checklist + 자주 틀리는 항목</a>
  <a class="page-toc-link" href="#7-핵심-정리-다음-단계">7. 핵심 정리 + 다음 단계</a>
</div>
<!-- DV-SKOOL-CH-TOC:end -->

> 한 페이지 cheat sheet. 본문 학습 후 검증/리뷰 시 보조 자료로 사용.

---

## 1. Why care? — 이 카드를 언제 펴는가

코드 리뷰 도중, 디버그 도중, 시뮬레이션 fail 직후 — _기억나야 할 그 표_ 를 빨리 찾는 게 목적입니다. 모듈 01~08 의 정보 중 **자주 인용되는 표/공식/명령어** 만 한 곳에 모았습니다. 처음 학습 용도가 아니라 _이미 아는 사람의 즉시 조회용_.

---

## 2. Intuition — 카드의 구성 원리

기억 nav 의 순서로 배치: **패킷 (1~6) → 객체 (7~10) → 에러 (11~12) → TB (13) → spec (14)**. 위에서 아래로 "wire → host → recovery → 검증" 의 흐름. 검증 중에는 보통 한 번에 1~2 영역만 펴므로 § anchor 가 곧 책갈피.

---

## 3. 작은 예 — 자주 펼치는 3 시나리오

### 시나리오 A. "이 BTH 가 어떤 op 인가?"
1. §3 (BTH field) 와 §4 (RC OpCode) 펴기.
2. OpCode 상위 3-bit → service. 하위 5-bit → operation.
3. 예: `0x06` = `000_00110` = RC `WRITE_FIRST` → RETH 가 따라옴 (§5 xTH).

### 시나리오 B. "WC error 의 root cause 가 뭐지?"
1. §11 (Error & WC Status) 펴기.
2. WC status 로 1차 분류. `WC_REM_ACCESS_ERR` 이면 responder debug flag 도 함께 (§11 의 Debug Flag 표).
3. S5~S9 매핑 (§13) 으로 inject 위치까지 1줄에 찾기.

### 시나리오 C. "QP 가 RTR 진입 안 된다"
1. §7 (QP FSM) 의 진입 attribute 표 펴기.
2. `path_mtu / dest_qp_num / rq_psn / max_dest_rd_atomic / min_rnr_timer / ah_attr` 중 누락 확인.
3. (RoCEv2) §14b 의 사내 default 와 일치하는지 cross check.

---

## 4. 일반화 — 카드 15 영역의 목차

| § | 영역 | 트리거 (이걸 보고 싶을 때) |
|---|------|---------------------------|
| §5.1 | RDMA family | "RoCEv2 vs IB 빠른 결정" |
| §5.2 | Packet layout | "wire 캡처를 보면서 IB ↔ RoCEv2 매핑" |
| §5.3 | BTH | "한 BTH 의 필드 의미" |
| §5.4 | RC OpCode | "OpCode 값을 보고 op 종류" |
| §5.5 | xTH | "이 op 에 xTH 가 와야 하나?" |
| §5.6 | AETH syndrome | "NAK syndrome 값 디코드" |
| §5.7 | QP FSM | "Modify(...) 진입 안 됨" |
| §5.8 | Service type | "RC vs UC vs UD vs XRC 결정" |
| §5.9 | PSN | "PSN 비교 / wrap 처리" |
| §5.10 | Memory Model | "MR access flag, MW, ODP" |
| §5.11 | WC Status | "WC status 트리거 분류" |
| §5.12 | CC (RoCEv2) | "PFC / ECN / DCQCN" |
| §5.13 | RDMA-TB ref | "mrun 명령, lib 분류, env 목록, S1~S9" |
| §5.14 | Spec 인용 | "어디 spec 절을 찾을지" |
| §5.15 | 사내 default | "MTU / P_Key / retry_cnt …" |

---

## 5. 디테일 — Reference 표 전체

### 5.1 RDMA family at a glance

| 항목 | InfiniBand | iWARP | RoCEv1 | **RoCEv2** |
|------|-----------|-------|--------|-----------|
| L1/L2 | IB SerDes/Link | Ethernet | Ethernet | Ethernet |
| L3 | IB GRH | IP | (없음) | **IPv4 / IPv6** |
| L4 | IB Transport (BTH) | TCP/DDP/RDMAP | BTH | **UDP(4791) + BTH** |
| 라우팅 | IB SM | IP | L2 only | **표준 IP** |

→ 데이터센터 표준 = **RoCEv2**.

### 5.2 IB Packet Layout (IB / RoCEv2 비교)

```
   IB :    LRH | GRH? | BTH | xTH? | Payload | ICRC | VCRC
   RoCEv2: Eth | IP   | UDP | BTH  | xTH? | Payload | ICRC | FCS
                                    ──────────────────── 동일 ─────
```

- BTH 부터 ICRC 직전까지 IB ↔ RoCEv2 동일.
- VCRC 는 RoCEv2 에서 사라지고 Eth FCS 가 대체.

### 5.3 BTH (12 byte) Field

| Field | bits | 용도 |
|-------|------|------|
| OpCode | 8 | service+op |
| SE | 1 | Solicited Event |
| MigReq | 1 | Path migration |
| PadCnt | 2 | Payload pad |
| TVer | 4 | =0 |
| P_Key | 16 | Partition Key |
| FECN/BECN | 1+1 | ECN 신호 |
| DestQP | 24 | dest QPN |
| AckReq | 1 | A bit |
| PSN | 24 | seq number |

### 5.4 RC OpCode 빠른 참조

| OpCode | Hex | xTH | 용도 |
|--------|-----|-----|------|
| SEND_ONLY | 0x04 | — | 단일 SEND |
| SEND_FIRST/MIDDLE/LAST | 0x00/01/02 | — | Multi-packet SEND |
| SEND_LAST_w_IMM | 0x03 | ImmDt | 마지막 + immediate |
| WRITE_ONLY | 0x0A | RETH | 단일 WRITE |
| WRITE_FIRST/MIDDLE/LAST | 0x06/07/08 | (FIRST: RETH) | Multi-packet WRITE |
| READ_REQUEST | 0x0C | RETH | READ 요청 |
| READ_RESPONSE_ONLY/FIRST/MIDDLE/LAST | 0x10/0D/0E/0F | (F/L: AETH) | READ 응답 |
| ACKNOWLEDGE | 0x11 | AETH | ACK / NAK |
| ATOMIC_ACKNOWLEDGE | 0x12 | AETH+AtomicAckETH | ATOMIC 응답 |
| CMP_SWAP | 0x13 | AtomicETH | Compare and Swap |
| FETCH_ADD | 0x14 | AtomicETH | Fetch and Add |
| SEND_LAST_w_INV / ONLY_w_INV | 0x16/17 | IETH | SEND + Invalidate |

상위 3-bit: RC=000 / UC=001 / RD=010 / UD=011 / XRC=101.

### 5.5 xTH 카탈로그

| xTH | Length | When |
|-----|--------|------|
| RETH | 16B | RDMA WRITE FIRST/ONLY, READ Request |
| DETH | 8B | UD all packets (Q_Key + SrcQP) |
| AtomicETH | 28B | CMP_SWAP, FETCH_ADD |
| AETH | 4B | ACK, NAK, READ Response F/L |
| AtomicAckETH | 8B | ATOMIC ACK |
| ImmDt | 4B | *_w_IMM |
| IETH | 4B | *_w_INV |

### 5.6 AETH Syndrome

| Code | 의미 |
|------|------|
| `0_xxxxxxx` | ACK (credit count = 하위 5-bit) |
| `0x60..0x7F` | RNR NAK (timer 인코딩) |
| `0x80` | NAK PSN Sequence Error |
| `0x81` | NAK Invalid Request |
| `0x82` | NAK Remote Access Error |
| `0x83` | NAK Remote Operational Error |
| `0x84` | NAK Invalid R-Key |

### 5.7 QP FSM

```
  Reset → Init → RTR → RTS ←→ SQD
           ↑                   ↓
           └── Modify(Reset)   SQErr / Err
```

| 진입 attribute (RC) |
|-------------------|
| Reset → Init: pkey_index, port_num, qp_access_flags |
| Init → RTR: path_mtu, dest_qp_num, rq_psn, max_dest_rd_atomic, min_rnr_timer, ah_attr |
| RTR → RTS: sq_psn, timeout, retry_cnt, rnr_retry, max_rd_atomic |

### 5.8 Service Type 비교

| | RC | UC | UD | XRC |
|--|----|----|----|-----|
| Connection | 1:1 | 1:1 | none | shared recv |
| Reliable | ✓ | ✗ | ✗ | ✓ |
| Multicast | ✗ | ✗ | ✓ | ✗ |
| Max msg | 2GB | 2GB | MTU | 2GB |
| Opcodes | SEND/WRITE/READ/ATOMIC | SEND/WRITE | SEND only | SEND/WRITE/READ/ATOMIC |

### 5.9 PSN

- **24-bit**, modulo 2^24.
- **Window = 2^23** (절반).
- Receiver: `PSN == ePSN` → 정상 / `[ePSN-W, ePSN-1]` → 중복 / `[ePSN+1, ePSN+W-1]` → 미래 (drop or NAK).

### 5.10 Memory Model

| 객체 | 발급 | 사용 |
|------|------|------|
| **PD** | `ibv_alloc_pd` | 모든 객체의 보호 경계 |
| **MR** | `ibv_reg_mr(pd, addr, len, access)` | DMA 가능 영역 |
| **L_Key** | reg_mr 결과 | sg_list 의 lkey |
| **R_Key** | reg_mr 결과 | RETH/AtomicETH 의 rkey |
| **MW (Type1/2)** | `ibv_alloc_mw` + bind | 짧은 lifetime 의 R_Key 위임 |
| **ODP** | access flag | page-fault 기반, pin 없음 |

#### Access Flag 매트릭스

| Op | sender 측 (lkey) | responder 측 (rkey) |
|----|-----------------|--------------------|
| SEND 발신 | LOCAL_READ | (RECV WR lkey, LOCAL_WRITE) |
| WRITE 발신 | LOCAL_READ | REMOTE_WRITE |
| READ 발신 | LOCAL_WRITE | REMOTE_READ |
| ATOMIC | LOCAL_WRITE | REMOTE_ATOMIC |

### 5.11 Error & WC Status

| WC Status | 트리거 |
|-----------|-------|
| `WC_SUCCESS` | OK |
| `WC_LOC_PROT_ERR` | Local lkey/access fail |
| `WC_RETRY_EXC_ERR` | Local ACK timeout / PSE / Implied NAK retry exhaust |
| `WC_RNR_RETRY_EXC_ERR` | RNR retry exhaust |
| `WC_REM_ACCESS_ERR` | Remote access fail (access/range/PD/rkey) |
| `WC_REM_INV_REQ_ERR` | OpCode/service mismatch |
| `WC_REM_INV_RD_REQ_ERR` | Max read outstanding 위반 |
| `WC_REM_OP_ERR` | Remote operational error |
| `WC_FATAL_ERR` | QP fatal |

#### Responder Debug Flag (RDMA-TB)

| Flag | 의미 |
|------|------|
| `WC_FLAG_RESP_ACCESS` | Access flag fail |
| `WC_FLAG_RESP_RANGE` | MR bound 위반 |
| `WC_FLAG_RESP_PD` | PD mismatch |
| `WC_FLAG_RESP_RKEY` | R-Key invalid |
| `WC_FLAG_RESP_OP` | OpCode/Outstanding read |

### 5.12 Congestion Control (RoCEv2)

| 메커니즘 | 시간축 | 역할 |
|---------|-------|------|
| **PFC** | 즉시 (us) | priority pause, lossless |
| **ECN** | 즉시 | CE 마킹 |
| **CNP** | RTT | receiver → sender 통지 |
| **DCQCN** | ms | sender rate 점진 조절 |

→ PFC만 사용 시 deadlock/storm 위험 → ECN+DCQCN 와 병용.

### 5.13 RDMA-TB 빠른 참조

#### mrun

```bash
source set_env.sh
rdma list                     # workspace 목록
rdma <target>                 # workspace 진입 (mmu_top, ip_top, mblp, ...)
mrun comp vip|rtl|tb|all
mrun elab
mrun test --test_name <name> [--seed N] [--fsdb] [--cov]
mrun regr --test_suite <suite>
mrun clean
```

#### Lib 분류

| Dir | 들어가는 것 |
|-----|-----------|
| `base/` | 모든 feature 가 알아야 하는 핵심 인프라 |
| `ext/` | 특정 feature 만 쓰는 코드 |
| `external/` | 3rd-party VIP wrapper (e.g. VPFC) |
| `submodule/` | Sub-IP 전용 (design hierarchy 따라) |

#### `vrdmatb_top_env` 의 env 들

`host / node / ntw / ntw_model / memory / data / dma / ral / ipshell / lp / elc`

#### Error 시나리오 S1~S9 매핑

| ID | 트리거 | Expected |
|----|--------|----------|
| S1 | RX packet drop | `WC_RETRY_EXC_ERR` + recovery |
| S2 | PSN hole | `WC_RETRY_EXC_ERR` |
| S3 | ACK drop | `WC_RETRY_EXC_ERR` (Implied NAK) |
| S4 | NAK drop | `WC_RNR_RETRY_EXC_ERR` |
| S5 | MR access flag clear | `WC_REM_ACCESS_ERR` + `RESP_ACCESS` |
| S6 | TX length corrupt | `WC_REM_ACCESS_ERR` + `RESP_RANGE` |
| S7 | MR global key override | `WC_REM_ACCESS_ERR` + `RESP_PD` |
| S8 | TX rkey corrupt | `WC_REM_ACCESS_ERR` + `RESP_RKEY` |
| S9 | Read duplicate | `WC_REM_INV_RD_REQ_ERR` + `RESP_OP` |

### 5.14 Spec 인용을 빨리 찾는 법

| 영역 | IB Spec 1.7 chapter | PROTOCOL_RULES.md range |
|------|---------------------|-------------------------|
| Architecture & Address | 3-4 | R-001 ~ R-005 |
| Packet Format | 5 | R-006 ~ R-010 |
| Link Layer | 6-7 | R-011 ~ R-085 |
| Network Layer (GRH) | 8 | R-086 ~ R-103 |
| Transport Headers | 9.1-9.6 | R-104 ~ R-196 |
| RC service | 9.7 | R-197 ~ R-304 |
| UC/UD | 9.8 | R-305 ~ R-347 |
| Error Handling | 9.9-9.11 | R-348 ~ R-350 |
| SW Transport Interface (QP) | 10 | R-351 ~ R-626 |
| Verbs | 11 | R-627 ~ R-665 |
| CM (NOT-APPLICABLE for RoCEv2) | 12 | R-666 ~ R-739 |
| SMP/SA (NOT-APPLICABLE) | 13-15 | R-740 ~ R-890 |

→ RoCEv2 검증에서는 `ROCEV2_RULE_APPLICABILITY.md` 의 분류를 거친 후 사용.

### 5.15 Confluence 보강 — 사내 RDMA-IP Default 한 장

!!! note "Internal — 자주 묻는 사내 default 한 장 요약"

    | 항목 | 사내 default | 출처 |
    |---|---|---|
    | MTU | **1024 byte** (정적) | RDMA headers and header fields |
    | P_Key | `0xFFFF` | RDMA headers and header fields |
    | TVer / Reserved6 / MigReq | 0 zero-fill | RDMA headers and header fields |
    | max_dest_rd_atomic | 16 (= ConnectX-5 호환) | PSN handling & retransmission |
    | local_ack_timeout | `4.096 µs × 2^attr.timeout` | IBTA §11.6.2 |
    | retry_cnt / rnr_retry | 별도 카운터, 별도 exhaust | Error handling in RDMA |
    | MW type | **Type 2 (DH)** 우선 지원 | Memory Window (feat. DH) |
    | APM | 비활성 (default) | Automatic Path Migration |
    | CC | DCQCN (default) + RTTCC option | DCQCN in detail / Zero-touch RoCE |
    | UEC fallback | (향후) PDS / Semantic | Ultraethernet |

### 5.16 UEC vs IB / RoCEv2 한 장 비교

!!! note "Internal (Confluence: Ultraethernet 트리)"

    | 영역 | IB | RoCEv2 | UEC |
    |---|---|---|---|
    | L2 | IB Link | Ethernet | Ethernet (lossy 허용) |
    | L3 | IB Network | IPv4 / IPv6 | IPv4 / IPv6 |
    | L4 | IB Transport | UDP 4791 + IB Transport | UDP + **PDS** |
    | Reliability | per-QP RC | per-QP RC | **per-PDC** + selective retransmission + multipath |
    | Ordering | strict in-order (RC) | strict in-order (RC) | **per-message** (out-of-order packet 허용) |
    | Multicast | UD | UD | **MPI / Collective primitives** (Semantic Sublayer) |
    | CC | CCMAD / DCQCN | DCQCN, RTTCC | UET-CC (예: NSCC) |
    | Security | weak (Q_Key) | weak | TLS-ish framing (UEC Security) |
    | Verb 시맨틱 호환 | — | IB 호환 | RDMA verbs subset 호환 + MPI 시맨틱 추가 |

---

## 6. 30-second mental checklist 와 자주 틀리는 항목

### 코드 리뷰 시 30-second checklist

```
  ✅ OpCode 의 상위 3-bit 가 QP service type 과 일치?
  ✅ RETH 가 WRITE_FIRST / WRITE_ONLY / READ_REQUEST 에만?
  ✅ DETH 가 UD packet 모두에?
  ✅ Multi-packet 의 PSN 단조 +1, modulo 2^24 비교 함수 사용?
  ✅ A bit (AckReq) 가 *_LAST 또는 *_ONLY 에 있나?
  ✅ MR access flag 와 사용 op 의 권한 일치?
  ✅ RC retry_cnt + rnr_retry 별도 처리?
  ✅ Error 후 QP recovery 경로 (Err → Reset → Init → ...) 검증?
```

### 자주 틀리는 카드 사용 (흔한 오해)

!!! danger "❓ 오해 — '카드의 OpCode 표 만 보면 시나리오 디버그 끝'"
    **실제**: OpCode 는 _어떤 op_ 일 뿐. xTH 의 존재/위치, PSN 정합성, AETH syndrome, access flag, debug flag 까지 함께 봐야 root cause 결정. 표 하나만 보면 흔히 false root cause.

!!! danger "❓ 오해 — 'IB OpCode 표가 RoCEv2 에도 그대로 통한다'"
    **실제**: BTH/OpCode 는 그대로지만 LRH/VCRC/VL 관련 spec rule 은 NOT-APPLICABLE. 카드 §14 의 spec range 표에서 R-001~085 영역을 RoCEv2 에 그대로 옮기면 false positive.

!!! danger "❓ 오해 — '사내 default (§5.15) 가 spec 가정'"
    **실제**: 사내 default 는 _배포 결정_. 다른 vendor 와의 interop 검증에서는 그쪽 default 와 비교해야 함.

---

## 7. 핵심 정리 + 다음 단계

- 이 카드는 _이미 아는 사람의 즉시 조회용_. 처음 학습은 모듈 01~08 본문으로.
- 한 fail 디버그 시 보통 **2~3 영역만** 보면 됨 (§3 시나리오 A/B/C 참고).
- 사내 default + RoCEv2 NOT-APPLICABLE 영역은 spec 가정이 아니라는 점 항상 의식.

### 7.1 자가 점검

!!! question "🤔 Q1 — RC vs UC 즉답 (Bloom: Apply)"
    "RC 와 UC 의 _재전송_ 차이?"
    ??? success "정답"
        ACK/NAK 의 유무가 핵심:
        - **RC** (Reliable Connected): ACK/NAK + PSN 단조 + 자동 재전송 → drop 무시 가능.
        - **UC** (Unreliable Connected): ACK 없음 → drop 시 데이터 손실, 상위가 복구.
        - **trade-off**: RC 는 retry HW + state machine 비용 ↑, UC 는 throughput ↑ + complexity ↓.
        - 결론: GPU/storage workload = RC, 일부 collective = UC.

!!! question "🤔 Q2 — RoCEv2 NOT-APPLICABLE 의의 (Bloom: Evaluate)"
    카드에서 "RoCEv2 영역 NOT-APPLICABLE" 의 _spec 적_ 의미?
    ??? success "정답"
        IB 의 일부 기능은 RoCEv2 에서 _대체_ 됨:
        - **IB SL (Service Level)**: RoCEv2 는 IP DSCP 로 대체 → IB SL field 무의미.
        - **IB Partition Key (P_Key)**: RoCEv2 는 IP 기반 isolation → P_Key 무의미.
        - **IB Subnet Manager**: Ethernet 의 표준 L2 (DCBX/PFC) 로 대체.
        - 결론: "NOT-APPLICABLE" 는 spec 적 답변 ("RoCEv2 에서는 다른 메커니즘으로 대체됨").
        - 안티패턴: "RoCEv2 가 IB 와 같음" 답변 → follow-up 에서 무너짐.

### 7.2 출처

**Internal (Confluence)**
- `RDMA Curriculum` — 모듈 01–08 + 카드 매핑
- `Site Default Policy` — 사내 default vs spec

**External**
- IBTA *InfiniBand Architecture Specification Vol 1/2*
- IBTA *Annex A17 — RoCEv2*
- IETF RFC 8825 *Transport Mappings* (RoCEv2 의 UDP)

### 다음 단계

- [용어집](glossary.md) — 핵심 용어 ISO 11179 형식
- [퀴즈](quiz/index.md) — 모듈별 이해도 체크
- 실 환경 실습: `rdma list` → workspace 선택 → `mrun comp all` → `mrun test`


--8<-- "abbreviations.md"
--8<-- "_inc/topic_abbr.md"
