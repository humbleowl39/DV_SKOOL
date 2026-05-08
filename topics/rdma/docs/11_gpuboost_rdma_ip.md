# Module 11 — GPUBoost / RDMA-IP Hardware Architecture

!!! note "Internal — 본 모듈은 사내 *RDMA IP architecture* 트리 (id=22773996) 와 *Latest GPUBoost Specification* (id=1056735249) 의 발췌입니다"
    Spec 본문은 별도 문서 (GPUBoost spec PDF, *High-Level Architecture Description for DV team* id=1211203656). 본 모듈은 학습용 요약. 모든 구체 수치는 spec 본문을 우선합니다.

## 학습 목표 (Bloom)

- (Remember) RDMA-IP 의 wrapper 5종 (`requester_frontend / completer_frontend / completer_retry / responder_frontend / cc_module`) 을 식별한다.
- (Understand) 각 wrapper 의 입출력과 책임을 자기 말로 설명한다.
- (Apply) 한 RDMA 연산 (예: 4KB WRITE) 의 흐름을 wrapper 사이의 stream 으로 트래이스한다.
- (Analyze) HLS timing 보고서에서 II / WNS 가 throughput 에 미치는 영향을 분해한다.
- (Evaluate) 동일 기능을 *frontend* 와 *retry* 두 sub-block 으로 분리한 설계 결정을 평가한다.

## 사전 지식

- M02 헤더, M04 QP FSM, M06 Data path, M08 RDMA-TB DV.

---

## 1. 전체 블록 다이어그램 (개념)

```
   ┌────────────────────────── HOST SIDE ──────────────────────────┐
                                                                   │
   sq_post / cq_poll / mr_reg ──▶ Verb interface  ─┐                │
                                                  │                │
   ┌────────── REQUESTER ─────────┐  ┌──────── COMPLETER ────────┐ │
   │  requester_frontend  ────────┼──│  completer_frontend       │ │
   │                              │  │  completer_retry          │ │
   │   info_arb (SWQ I/F)  ◀─────┼──┘                            │ │
   └──────────────────────────────┘  └───────────────────────────┘ │
              │                              │                     │
              ▼                              ▼                     │
   ┌────────── PAYLOAD ENGINE / DMA ────────────────────────────┐  │
   │  payload_cmd → drop1/drop2/drop3, DMA write address xlate  │  │
   └────────────────────────────────────────────────────────────┘  │
                                                                   │
   ┌────────── RESPONDER ────────────────────────────────────────┐ │
   │  responder_frontend  →  ACK/NAK gen, MSN++, payload write   │ │
   └─────────────────────────────────────────────────────────────┘ │
                                                                   │
   ┌────────── CC MODULE ────────────────────────────────────────┐ │
   │  CNP / DCQCN / RTTCC / SACK info handling                   │ │
   └─────────────────────────────────────────────────────────────┘ │
   ┌────────── MMU / TLB / PTW WRAPPER ──────────────────────────┐ │
   │  IOVA → PA, dereg flush                                     │ │
   └─────────────────────────────────────────────────────────────┘ │
   └─────────────────────────────────────────────── NETWORK ──────┘
```

(Confluence: *High-Level Architecture Description (for DV team)*, id=1211203656; *Completer*, id=1212973064.)

---

## 2. Completer Wrapper 정밀 보기

!!! note "Internal (Confluence: *Completer*, id=1212973064)"
    Completer 는 **요청을 보낸 측 (requester)** 에서 **응답 패킷 (ACK / NAK / Read Response)** 을 처리하는 wrapper.

### 2.1 외부 인터페이스 (요약)

| 그룹 | 대표 포트 | 의미 |
|---|---|---|
| Clock/Reset | `axis_clk`, `axis_rstn` | active-low reset |
| Debug | `s_debug_reg` (AXI4-Lite) | sticky bit · last-PSN read |
| Ingress (slave AXI-Stream) | `s_comp_header_stream` (592b) | incoming response packet header |
|  | `s_qp_control_cmd`, `s_mr_ctrl_stream` | control plane |
|  | `s_data_port_0/3/4` (1024b) | SWQ read responses (`tx_info`) |
|  | `s_set_timer` (24b) | retry timer set |
|  | `s_mmu_flush_rsp`, `s_dereg_rsp` | cleanup ack |
| Egress (master AXI-Stream) | `m_comp_cmpt_stream` (512b) | success CQE (`mb_cqe`) |
|  | `m_comp_err_stream` (512b) | error CQE |
|  | `m_cmd_port_0/1/3/4` | SWQ command channels |
|  | `m_comp_payload_drop1/2/3` | payload drop signals |
|  | `m_ack_info`, `m_nak_info` (64b) | CC notify |
|  | `m_sack_info` (152b) | selective ACK info |
|  | `m_notify_cnp_qpn` (16b) | CNP QPN notify |
|  | `m_comp_payload_cmd_stream`, `m_comp_write_translate` | payload engine cmd |
|  | `m_mmu_flush`, `m_dereg_mr_id` | cleanup req |

### 2.2 4 가지 책임

1. **응답 패킷 처리** — `s_comp_header_stream` 으로 들어온 ACK/NAK/Read Response 를 받아 QP 메타데이터 read → drop 신호 발행 → 완료 CQE 또는 error CQE 생성. payload 가 있으면 DMA write address translation 까지 수행.
2. **QP control 신호 통과** — Destroy QP 신호는 직접 처리해 cleanup 명령을 info_arb 와 CC 모듈에 보냄. 그 외는 bypass.
3. **MR control 신호 통과** — Deregister MR 시 MMU cleanup 명령 발행. 그 외는 bypass.
4. **Retry 처리 (`completer_retry`)** — QP 별 timer 추적, NAK / SACK / timeout 기반 retransmission 결정. 결정 시 info_arb 에 fetch 명령을 다시 보냄. retry exceed 시 QP invalidation.

### 2.3 입출력 시퀀스 규약

(Confluence: *Completer* §3, ordering legend 사용)

- **[TRIGGER]** 은 시퀀스를 시작시키는 stream.
- **[THEN]** 은 strict 직렬.
- **[ANY-ORDER]** 는 형제간 reorder 허용.
- **[ASYNC]** 는 시퀀스와 별개.
- **[COMPILE-TIME: X]** 는 macro X 정의 시에만.

응답 처리의 골격:

```
[TRIGGER] s_comp_header_stream
  ├── [THEN]      QP/QP-state read (qp_rw_port_awd → qp_rw_port_rd)
  ├── [THEN]      Early termination & drop1/drop2 결정
  │                ├── [ANY-ORDER] 종료 조건: invalid QP / not-yet-RTS / IP mismatch
  │                │                     / PSN < ePSN (duplicate) / large-PSN SACK / non-SR SACK
  │                ├── [ANY-ORDER] payload drop sequence
  │                │                     drop1=1 → no drop2  (terminate)
  │                │                     drop1=0 → drop2=1   (terminate)
  │                │                     drop1=0 → drop2=0   (continue)
  │                └── ...
  ├── [THEN]      CQE / error CQE 발행 (m_comp_cmpt_stream / m_comp_err_stream)
  ├── [ASYNC]     CC notify (m_ack_info / m_nak_info / m_sack_info / m_notify_cnp_qpn)
  └── [THEN]      payload engine cmd (m_comp_payload_cmd_stream)
                   + DMA write address xlate (m_comp_write_translate)
```

---

## 3. Responder / Requester / Retry 의 책임 분담

| Wrapper | Trigger | 주요 출력 | Spec 대응 |
|---|---|---|---|
| **requester_frontend** | host SQ doorbell | network packet | sender 측 packet build |
| **completer_frontend** | response packet 도착 | CQE, payload cmd | sender 측 ACK 처리 |
| **completer_retry** | timer 만료 / NAK / SACK | retry fetch cmd | spec §11.6 |
| **responder_frontend** | request packet 도착 | ACK / Read Response, MSN++ | responder 전체 |

!!! tip "왜 frontend / retry 를 분리했는가"
    Frontend 는 "방금 도착한 응답 1 건의 즉각 처리" 책임. Retry 는 "outstanding WQE 의 timer 기반 재발행" 책임. **두 작업의 II 요구가 다르고** (frontend = packet rate 직접, retry = sparse), pipeline 을 같이 두면 retry 의 sparse FSM 이 frontend critical path 를 잠식. 분리는 timing closure 결정.

---

## 4. HLS Timing — Bitfile 운영의 시각

!!! note "Internal (Confluence: *HLS Timing Analysis: completer_frontend & responder_frontend* id=1230209052; *responder_frontend & completer_frontend analysis* id=1229914213)"
    Combined Vivado implementation 에서 CLB regslice 가 폭증 → WNS regression > 3 ns 관찰. 두 wrapper 가 standalone 단계에서 **FSM state explosion** 으로 timing fail 하면 그 영향이 인접 모듈까지 번진다.

    | 지표 | completer_frontend | responder_frontend |
    |---|---|---|
    | 목표 클럭 주기 | 4.0 ns | 4.0 ns |
    | HLS critical path slack | -1.47 ns | -1.47 ns |
    | Worst reg-to-reg slack | -1.36 ns | **-3.33 ns** |
    | 가장 큰 FSM | `and#1213 (th_dma_write)` | `and#1649 (th_psn_check)` |
    | 가장 violation 많은 thread | `th_swq_cmd / th_dma_write` | `th_ack (56)` |

    !!! warning "1 cycle II 차이가 throughput 0 으로 수렴할 수 있다 (id=1276379157)"
        1K MTU + 200G + 250 MHz 환경에서 **T_arrival ≈ 11 cycles**, broken `th_dma_write` II = **12 cycles**, original = **11 cycles**.
        Pipelined for-loop 의 1 FSM state 가 추가되면 **회복 불가 누적 deficit** → input buffer overflow → flow control oscillation → throughput cliff.
        교훈: HLS C++ 의 pipelined for-loop 는 **항상 ≥ 1 FSM state 를 소비**한다. arrival rate 를 직접 따르는 thread 에서는 sticky pop 이나 unrolled if-chain 이 더 안전.

---

## 5. SWQ — 사내 Send-Work-Queue 인프라

(Confluence: *Completer* §1.3 / §1.4, *Untitled live doc 2025-10-01* id=565837906)

WQE metadata 는 외부 spec 의 SQ 와는 독립된 사내 SWQ 인프라가 보관한다. 핵심 필드:

```
swq_head, swq_tail
dispatch
window
completed_byte
completed_rd_atomic
ib_mtu_qp_type
retry
```

여러 wrapper 가 동시에 read/write 하므로 read port 가 다중화돼 있다 — `s_data_port_0` (modify/delete), `s_data_port_3` (read_init), `s_data_port_4` (read). 같은 channel 로만 modify 와 retry fetch 가 들어가야 ordering 이 보장된다.

---

## 6. 검증 (DV) 의 wrapper 단위 책임

| Scope | 1차 신호 | 2차 신호 | Scoreboard 대상 |
|---|---|---|---|
| `responder_frontend` | incoming request | outgoing ACK | request → ACK 1:1 (RC), MSN 단조성 |
| `completer_frontend` | incoming response | outgoing CQE | response → CQE matching, drop sequence |
| `completer_retry` | timer expire | retry fetch cmd | NAK / SACK / timeout → fetch 정합성 |
| `payload_engine` | payload_cmd | DMA write | payload byte stream vs expected MR |
| `mmu_wrapper` | dereg | flush done | TLB stale, IOVA 변환 정합 |
| `cc_module` | ECN/CNP | rate adjust | DCQCN / RTTCC parameter sweep |

!!! tip "사내 검증 패턴"
    1. **Wrapper standalone TB** — 각 wrapper 를 분리해 `lib/.../submodule/` 의 standalone 환경에서 검증.
    2. **Pair-wise** — `completer_frontend + completer_retry`, `responder_frontend + mmu_wrapper` 처럼 강결합 페어를 같이 묶어 검증.
    3. **IP-top** — `vrdmatb_top_env` 두 노드 환경에서 통합. (M08 §3 참조)

---

## 7. GPUBoost 사양과의 관계

!!! note "Internal (Confluence: *Latest GPUBoost Specification*, id=1056735249)"
    GPUBoost spec 은 **외부 고객용 RNIC 사양** — opcode 지원, 최대 QP / MR 수, supported MTU, supported atomic op, supported CC 알고리즘 등의 cap 를 정의.

    검증 자료는 항상 spec 의 *latest version* 을 1차 truth 로 본다. 본 학습 모듈은 *snapshot* 이며, spec 에서 cap 변경 시 본문 우선.

---

## 핵심 정리 (Key Takeaways)

- RDMA-IP 는 5 + 1 wrapper 구조 (requester / completer-frontend / completer-retry / responder / cc + mmu).
- Completer 는 4 책임 (응답 처리, QP/MR 통과, retry).
- HLS II ↔ packet T_arrival 의 1 cycle 차이가 throughput cliff 로 직결될 수 있다.
- SWQ read port 다중화로 channel 별 ordering 이 보장된다.
- DV 는 wrapper 별 standalone → pair-wise → IP-top 의 3 단계.

!!! warning "실무 주의점"
    - HLS pipelined for-loop 는 1 FSM state 소비 — 핫 패스에서는 unroll / sticky pop 우선.
    - WNS > 3 ns 인 모듈 하나가 인접 모듈의 routing 까지 망가뜨린다 — *combined* 단계 regression diff 를 PR 마다 첨부.
    - Wrapper 별 debug register 는 sticky bit 가 많아 reset 후 read 해도 잔여 — bring-up 직후 `clear-on-read` 패스를 sequence 에 둔다.
    - Spec 변경 (cap) 시 본 모듈 본문보다 GPUBoost spec 이 우선. 학습용 표는 *예시 default*.

---

## 다음 모듈

→ [Module 12 — FPGA Prototyping & Lab Manuals](12_fpga_proto_manuals.md)

→ [퀴즈 11](quiz/11_gpuboost_rdma_ip_quiz.md)


--8<-- "abbreviations.md"
--8<-- "_inc/topic_abbr.md"
