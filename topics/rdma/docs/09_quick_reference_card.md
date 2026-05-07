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
  <a class="page-toc-link" href="#1-rdma-family-at-a-glance">1. RDMA family at a glance</a>
  <a class="page-toc-link" href="#2-ib-packet-layout-ib-rocev2-비교">2. IB Packet Layout (IB / RoCEv2 비교)</a>
  <a class="page-toc-link" href="#3-bth-12-byte-field">3. BTH (12 byte) Field</a>
  <a class="page-toc-link" href="#4-rc-opcode-빠른-참조">4. RC OpCode 빠른 참조</a>
  <a class="page-toc-link" href="#5-xth-카탈로그">5. xTH 카탈로그</a>
  <a class="page-toc-link" href="#6-aeth-syndrome">6. AETH Syndrome</a>
  <a class="page-toc-link" href="#7-qp-fsm">7. QP FSM</a>
  <a class="page-toc-link" href="#8-service-type-비교">8. Service Type 비교</a>
  <a class="page-toc-link" href="#9-psn">9. PSN</a>
  <a class="page-toc-link" href="#10-memory-model">10. Memory Model</a>
  <a class="page-toc-link" href="#11-error-wc-status">11. Error & WC Status</a>
  <a class="page-toc-link" href="#12-congestion-control-rocev2">12. Congestion Control (RoCEv2)</a>
  <a class="page-toc-link" href="#13-rdma-tb-빠른-참조">13. RDMA-TB 빠른 참조</a>
  <a class="page-toc-link" href="#14-spec-인용을-빨리-찾는-법">14. Spec 인용을 빨리 찾는 법</a>
  <a class="page-toc-link" href="#15-30-second-mental-checklist-코드-리뷰-시">15. 30-second mental checklist (코드 리뷰 시)</a>
  <a class="page-toc-link" href="#다음-단계">다음 단계</a>
</div>
<!-- DV-SKOOL-CH-TOC:end -->

> 한 페이지 cheat sheet. 본문 학습 후 검증/리뷰 시 보조 자료로 사용.

---

## 1. RDMA family at a glance

| 항목 | InfiniBand | iWARP | RoCEv1 | **RoCEv2** |
|------|-----------|-------|--------|-----------|
| L1/L2 | IB SerDes/Link | Ethernet | Ethernet | Ethernet |
| L3 | IB GRH | IP | (없음) | **IPv4 / IPv6** |
| L4 | IB Transport (BTH) | TCP/DDP/RDMAP | BTH | **UDP(4791) + BTH** |
| 라우팅 | IB SM | IP | L2 only | **표준 IP** |

→ 데이터센터 표준 = **RoCEv2**.

---

## 2. IB Packet Layout (IB / RoCEv2 비교)

```
   IB :    LRH | GRH? | BTH | xTH? | Payload | ICRC | VCRC
   RoCEv2: Eth | IP   | UDP | BTH  | xTH? | Payload | ICRC | FCS
                                    ──────────────────── 동일 ─────
```

- BTH 부터 ICRC 직전까지 IB ↔ RoCEv2 동일.
- VCRC 는 RoCEv2 에서 사라지고 Eth FCS 가 대체.

---

## 3. BTH (12 byte) Field

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

---

## 4. RC OpCode 빠른 참조

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

---

## 5. xTH 카탈로그

| xTH | Length | When |
|-----|--------|------|
| RETH | 16B | RDMA WRITE FIRST/ONLY, READ Request |
| DETH | 8B | UD all packets (Q_Key + SrcQP) |
| AtomicETH | 28B | CMP_SWAP, FETCH_ADD |
| AETH | 4B | ACK, NAK, READ Response F/L |
| AtomicAckETH | 8B | ATOMIC ACK |
| ImmDt | 4B | *_w_IMM |
| IETH | 4B | *_w_INV |

---

## 6. AETH Syndrome

| Code | 의미 |
|------|------|
| `0_xxxxxxx` | ACK (credit count = 하위 5-bit) |
| `0x60..0x7F` | RNR NAK (timer 인코딩) |
| `0x80` | NAK PSN Sequence Error |
| `0x81` | NAK Invalid Request |
| `0x82` | NAK Remote Access Error |
| `0x83` | NAK Remote Operational Error |
| `0x84` | NAK Invalid R-Key |

---

## 7. QP FSM

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

---

## 8. Service Type 비교

| | RC | UC | UD | XRC |
|--|----|----|----|-----|
| Connection | 1:1 | 1:1 | none | shared recv |
| Reliable | ✓ | ✗ | ✗ | ✓ |
| Multicast | ✗ | ✗ | ✓ | ✗ |
| Max msg | 2GB | 2GB | MTU | 2GB |
| Opcodes | SEND/WRITE/READ/ATOMIC | SEND/WRITE | SEND only | SEND/WRITE/READ/ATOMIC |

---

## 9. PSN

- **24-bit**, modulo 2^24.
- **Window = 2^23** (절반).
- Receiver: `PSN == ePSN` → 정상 / `[ePSN-W, ePSN-1]` → 중복 / `[ePSN+1, ePSN+W-1]` → 미래 (drop or NAK).

---

## 10. Memory Model

| 객체 | 발급 | 사용 |
|------|------|------|
| **PD** | `ibv_alloc_pd` | 모든 객체의 보호 경계 |
| **MR** | `ibv_reg_mr(pd, addr, len, access)` | DMA 가능 영역 |
| **L_Key** | reg_mr 결과 | sg_list 의 lkey |
| **R_Key** | reg_mr 결과 | RETH/AtomicETH 의 rkey |
| **MW (Type1/2)** | `ibv_alloc_mw` + bind | 짧은 lifetime 의 R_Key 위임 |
| **ODP** | access flag | page-fault 기반, pin 없음 |

### Access Flag 매트릭스

| Op | sender 측 (lkey) | responder 측 (rkey) |
|----|-----------------|--------------------|
| SEND 발신 | LOCAL_READ | (RECV WR lkey, LOCAL_WRITE) |
| WRITE 발신 | LOCAL_READ | REMOTE_WRITE |
| READ 발신 | LOCAL_WRITE | REMOTE_READ |
| ATOMIC | LOCAL_WRITE | REMOTE_ATOMIC |

---

## 11. Error & WC Status

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

### Responder Debug Flag (RDMA-TB)

| Flag | 의미 |
|------|------|
| `WC_FLAG_RESP_ACCESS` | Access flag fail |
| `WC_FLAG_RESP_RANGE` | MR bound 위반 |
| `WC_FLAG_RESP_PD` | PD mismatch |
| `WC_FLAG_RESP_RKEY` | R-Key invalid |
| `WC_FLAG_RESP_OP` | OpCode/Outstanding read |

---

## 12. Congestion Control (RoCEv2)

| 메커니즘 | 시간축 | 역할 |
|---------|-------|------|
| **PFC** | 즉시 (us) | priority pause, lossless |
| **ECN** | 즉시 | CE 마킹 |
| **CNP** | RTT | receiver → sender 통지 |
| **DCQCN** | ms | sender rate 점진 조절 |

→ PFC만 사용 시 deadlock/storm 위험 → ECN+DCQCN 와 병용.

---

## 13. RDMA-TB 빠른 참조

### mrun

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

### Lib 분류

| Dir | 들어가는 것 |
|-----|-----------|
| `base/` | 모든 feature 가 알아야 하는 핵심 인프라 |
| `ext/` | 특정 feature 만 쓰는 코드 |
| `external/` | 3rd-party VIP wrapper (e.g. VPFC) |
| `submodule/` | Sub-IP 전용 (design hierarchy 따라) |

### `vrdmatb_top_env` 의 env 들

`host / node / ntw / ntw_model / memory / data / dma / ral / ipshell / lp / elc`

### Error 시나리오 S1~S9 매핑

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

---

## 14. Spec 인용을 빨리 찾는 법

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

---

## 15. 30-second mental checklist (코드 리뷰 시)

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

---

## 다음 단계

- [용어집](glossary.md) — 핵심 용어 ISO 11179 형식
- [퀴즈](quiz/index.md) — 모듈별 이해도 체크
- 실 환경 실습: `rdma list` → workspace 선택 → `mrun comp all` → `mrun test`
