# Module 11 — GPUBoost / RDMA-IP Hardware Architecture

<!-- DV-SKOOL-CH-CTX:start -->
<div class="chapter-context" data-cat="network">
  <a class="chapter-back" href="../">
    <span class="chapter-back-arrow">←</span>
    <span class="chapter-back-icon">⚡</span>
    <span class="chapter-back-text">RDMA</span>
  </a>
  <span class="chapter-divider">›</span>
  <span class="chapter-marker">Module 11</span>
</div>
<!-- DV-SKOOL-CH-CTX:end -->

<!-- DV-SKOOL-CH-TOC:start -->
<div class="page-toc">
  <span class="page-toc-label">목차</span>
  <a class="page-toc-link" href="#1-why-care-이-모듈이-왜-필요한가">1. Why care?</a>
  <a class="page-toc-link" href="#2-intuition-비유와-한-장-그림">2. Intuition</a>
  <a class="page-toc-link" href="#3-작은-예-한-4-kb-rc-write-가-wrapper-들을-통과하는-1-cycle">3. 작은 예 — 4 KB WRITE 의 wrapper 통과</a>
  <a class="page-toc-link" href="#4-일반화-wrapper-와-책임-분리">4. 일반화 — wrapper 와 책임 분리</a>
  <a class="page-toc-link" href="#5-디테일-블록-completer-책임-hls-timing-swq-dv-매핑-gpuboost">5. 디테일</a>
  <a class="page-toc-link" href="#6-흔한-오해-와-dv-디버그-체크리스트">6. 흔한 오해 + 디버그 체크리스트</a>
  <a class="page-toc-link" href="#7-핵심-정리-key-takeaways">7. 핵심 정리</a>
</div>
<!-- DV-SKOOL-CH-TOC:end -->

!!! note "Internal — 본 모듈은 사내 *RDMA IP architecture* 트리 (id=22773996) 와 *Latest GPUBoost Specification* (id=1056735249) 의 발췌입니다"
    Spec 본문은 별도 문서 (GPUBoost spec PDF, *High-Level Architecture Description for DV team* id=1211203656). 본 모듈은 학습용 요약. 모든 구체 수치는 spec 본문을 우선합니다.

!!! objective "학습 목표"
    이 모듈을 마치면:

    - **Identify** RDMA-IP 의 wrapper 5 종 (`requester_frontend / completer_frontend / completer_retry / responder_frontend / cc_module`) 을 식별한다.
    - **Explain** 각 wrapper 의 입출력과 책임을 자기 말로 설명한다.
    - **Trace** 한 RDMA 연산 (예: 4 KB WRITE) 의 흐름을 wrapper 사이의 stream 으로 추적한다.
    - **Analyze** HLS timing 보고서에서 II / WNS 가 throughput 에 미치는 영향을 분해한다.
    - **Evaluate** 동일 기능을 *frontend* 와 *retry* 두 sub-block 으로 분리한 설계 결정을 평가한다.

!!! info "사전 지식"
    - M02 헤더, M04 QP FSM, M06 Data path, M08 RDMA-TB DV.

---

## 1. Why care? — 이 모듈이 왜 필요한가

### 1.1 시나리오 — "scoreboard 가 fail 했는데 _누구_ 책임?"

당신은 RDMA-TB 시뮬을 돌립니다. `WC_REM_ACCESS_ERR` 가 떴습니다. 즉시 두 후보:

- **(a)** sender 의 _requester wrapper_ 가 잘못된 rkey 를 보냈다 (송신측 버그).
- **(b)** receiver 의 _responder wrapper_ 가 valid rkey 를 잘못 reject 했다 (수신측 버그).

이 분기를 즉답하려면 _두 wrapper 의 경계_ 와 _signal 흐름_ 을 알아야 합니다. 단순 spec 만으로 부족 — **구현의 ground truth** 가 필요.

GPUBoost RDMA-IP 는 5 개 wrapper 분업 — **requester / completer / responder / cc / mmu**. 각 wrapper 가 _다른 II_ (handle rate) 와 _다른 latency budget_ 을 가지므로:

- _Scoreboard timing assumption_ 이 wrapper 별로 다름.
- _Inject 위치_ 가 wrapper 경계에 정확히 매핑됨 (e.g. "responder_frontend 의 packet 입력 한계로 inject").
- _Coverage closure_ 가 wrapper 별 corner case 로 분해됨.

또한 HLS 합성 결과의 II/WNS 가 throughput 에 직결되므로 spec 보다 _구현 timing 특성_ 을 봐야 정확한 검증 시나리오 설계가 가능합니다.

이 모듈은 RDMA-TB 의 모든 후속 디버그/시나리오 설계의 **구현 ground truth** 를 제공합니다.

!!! question "🤔 잠깐 — 왜 _wrapper 5 개_ 가 필요한가?"
    한 큰 monolithic RTL 으로 RDMA NIC 을 구현하면 안 되나? Wrapper 분리의 _구체적 trade-off_ 한 가지를 떠올려 보세요.

    ??? success "정답"
        **HLS II (Initiation Interval) 한계**.

        예: requester 의 doorbell 처리는 _1 cycle II_ 가능 (단순). 하지만 responder 의 _5-step access check + DMA 변환_ 은 _4~6 cycle II_ 필요. 한 monolithic RTL 으로 합치면 _가장 느린 II_ 가 전체 throughput 을 결정.

        Wrapper 분리 → 각자 자신의 II 로 동작 + _AXI4 / streaming I/F 로 buffer_ → 전체 throughput 이 _가장 느린 wrapper_ 가 아닌 _bottleneck wrapper_ 의 II 로 결정. 분업의 효과.

---

## 2. Intuition — 비유와 한 장 그림

!!! tip "💡 한 줄 비유 — RDMA-IP ≈ 5인 우체국 팀의 분업"
    **requester** = 발송 창구 (편지 작성), **completer-frontend** = 회신 수령 창구 (들어온 답장 처리), **completer-retry** = 재발송 담당 (응답 없는 편지 재시도), **responder** = 수령 창구 (외부에서 온 편지 처리 + 답장), **cc** = 도로 상황 감시. 각자의 II (handle 가능한 packet rate) 가 다르므로 분업이 필수.

### 한 장 그림 — wrapper 와 데이터 흐름

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

### 왜 이렇게 설계됐는가 — Design rationale

5 wrapper 분리 이유는 **각자의 timing 요구가 다르기 때문**:

- **requester** = host SQ doorbell rate 에 맞춤 (slow, ~us scale)
- **responder-frontend** = wire packet rate 에 맞춤 (fast, packet/cycle)
- **completer-frontend** = response packet rate (fast)
- **completer-retry** = sparse FSM (timer 만료 시에만)
- **cc** = ms scale의 rate adjust

같은 pipeline 안에 두면 sparse retry FSM 이 frontend critical path 를 잠식. 분리해 각자의 II 목표를 독립적으로 만족.

---

## 3. 작은 예 — 한 4 KB RC WRITE 가 wrapper 들을 통과하는 1 cycle

A → B 로 4 KB WRITE. MTU 1 KB 라 4 packet.

```
   ── A 측 (requester) ──                              ── B 측 (responder) ──
   ① user: ibv_post_send (WRITE, 4 KB)
        │
        ▼ BAR doorbell + descriptor
   requester_frontend:
     - SWQ 에서 WQE 메타데이터 fetch
     - BTH + RETH (FIRST) 작성 + payload[0..1KB] fetch
        │
        ▼  packet 1 (PSN=N, WRITE_FIRST, RETH)
   network ──────────────────────────────────────▶  responder_frontend:
                                                       - rkey 검증 (mmu_wrapper 호출: IOVA→PA)
                                                       - DMA write payload[0..1KB]
                                                       - ePSN += 1
                                                       - A=0 → ACK 안 함

   ② requester_frontend 가 packet 2 (PSN=N+1, WRITE_MIDDLE) 보냄
                                                    → 동일 처리, ePSN=N+2
   ③ packet 3 (PSN=N+2, WRITE_MIDDLE)
                                                    → ePSN=N+3
   ④ packet 4 (PSN=N+3, WRITE_LAST, A=1)
                                                    → DMA write payload[3..4KB]
                                                    → A=1 이므로 ACK 생성
                                                    → MSN++ (multi-packet 의 마지막에만)
                                                       │
   network ◀─── ACK PSN=N+3 ─────────────────────────┘
        │
        ▼
   completer_frontend:
     - s_comp_header_stream 으로 ACK packet header 받음
     - QP/QP-state read (qp_rw_port)
     - ACK PSN ≥ outstanding WQE last_psn → 완료
     - drop1/drop2 결정 (정상 ACK 이므로 둘 다 0 — payload engine 에 "data 가져가" 신호)
     - m_comp_cmpt_stream 으로 CQE (`mb_cqe`) 발행
     - m_ack_info → cc_module (CC 가 ACK 받았다 인지)

   ⑤ host: ibv_poll_cq() → WC{status=SUCCESS, opcode=WRITE, byte_len=4096}

   ── retry 경로 (만약 packet 1 이 drop 됐다면) ──
   completer_retry:
     - timer 추적: outstanding WQE 의 last send time 기록
     - timeout 만료 → m_cmd_port 로 info_arb 에 "WQE_id 재발신" 명령
     - requester_frontend 가 다시 packet 1 부터 보냄
     - retry_cnt 까지 시도, 초과 시 QP invalidation → completer_frontend 가 m_comp_err_stream 으로 error CQE
```

### 단계별 의미

| Step | 어떤 wrapper | 의미 |
|---|---|---|
| ① | requester_frontend | SQ doorbell 처리, packet build. SWQ I/F (info_arb) 로 WQE metadata 접근 |
| MTU split | requester | 4 KB → 4 packet 으로 fragmentation. FIRST/MIDDLE/MIDDLE/LAST OpCode |
| RX | responder_frontend | 5-step 검증 (M05) → mmu_wrapper 로 IOVA 변환 → DMA write |
| MSN++ | responder | _마지막 packet 에서만_ MSN 증가 (M02 §12 의 사내 정책) |
| ACK | responder | A=1 packet 에 대해서만 ACK 생성. coalescing |
| 완료 | completer_frontend | ACK PSN ↔ outstanding WQE 매핑. CQE 발행. drop1/drop2 신호 |
| CC notify | completer → cc_module | ACK/NAK/SACK 받음을 CC 에 전달 (rate 조절 입력) |
| retry | completer_retry | timeout 시 info_arb 로 fetch 재발행 |

!!! note "여기서 잡아야 할 두 가지"
    **(1) Wrapper 간 stream 인터페이스가 검증의 진입점** — `s_comp_header_stream`, `m_comp_cmpt_stream` 같은 AXI-Stream 이 wrapper 경계의 transaction 단위. RDMA-TB monitor 는 여기에 hook.<br>
    **(2) Retry 의 책임 분리** — frontend 는 "방금 받은 ACK" 처리, retry 는 "응답 없는 WQE" 처리. 두 사이의 동기화는 SWQ port 다중화 (M05 §5.10 참조) 로.

---

## 4. 일반화 — wrapper 와 책임 분리

### 4.1 5 + 1 wrapper

5 wrapper (데이터 path) + 1 wrapper (MMU). 각자 II 와 책임이 다름.

### 4.2 Wrapper 별 검증 1차/2차 신호

| Scope | 1차 신호 | 2차 신호 | Scoreboard 대상 |
|---|---|---|---|
| `responder_frontend` | incoming request | outgoing ACK | request → ACK 1:1 (RC), MSN 단조성 |
| `completer_frontend` | incoming response | outgoing CQE | response → CQE matching, drop sequence |
| `completer_retry` | timer expire | retry fetch cmd | NAK / SACK / timeout → fetch 정합성 |
| `payload_engine` | payload_cmd | DMA write | payload byte stream vs expected MR |
| `mmu_wrapper` | dereg | flush done | TLB stale, IOVA 변환 정합 |
| `cc_module` | ECN/CNP | rate adjust | DCQCN / RTTCC parameter sweep |

### 4.3 검증의 3-stage

1. **Wrapper standalone** — 각 wrapper 분리 검증 (lib/.../submodule/).
2. **Pair-wise** — `completer_frontend + completer_retry` 같은 강결합.
3. **IP-top** — 두 노드 통합 (M08).

---

## 5. 디테일 — 블록, Completer, 책임, HLS timing, SWQ, DV 매핑, GPUBoost

### 5.1 Completer Wrapper 정밀 보기

!!! note "Internal (Confluence: *Completer*, id=1212973064)"
    Completer 는 **요청을 보낸 측 (requester)** 에서 **응답 패킷 (ACK / NAK / Read Response)** 을 처리하는 wrapper.

#### 외부 인터페이스 (요약)

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

#### Completer 의 4 가지 책임

1. **응답 패킷 처리** — `s_comp_header_stream` 으로 들어온 ACK/NAK/Read Response 를 받아 QP 메타데이터 read → drop 신호 발행 → 완료 CQE 또는 error CQE 생성. payload 가 있으면 DMA write address translation 까지 수행.
2. **QP control 신호 통과** — Destroy QP 신호는 직접 처리해 cleanup 명령을 info_arb 와 CC 모듈에 보냄. 그 외는 bypass.
3. **MR control 신호 통과** — Deregister MR 시 MMU cleanup 명령 발행. 그 외는 bypass.
4. **Retry 처리 (`completer_retry`)** — QP 별 timer 추적, NAK / SACK / timeout 기반 retransmission 결정. 결정 시 info_arb 에 fetch 명령을 다시 보냄. retry exceed 시 QP invalidation.

#### 입출력 시퀀스 규약

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

### 5.2 Responder / Requester / Retry 의 책임 분담

| Wrapper | Trigger | 주요 출력 | Spec 대응 |
|---|---|---|---|
| **requester_frontend** | host SQ doorbell | network packet | sender 측 packet build |
| **completer_frontend** | response packet 도착 | CQE, payload cmd | sender 측 ACK 처리 |
| **completer_retry** | timer 만료 / NAK / SACK | retry fetch cmd | spec §11.6 |
| **responder_frontend** | request packet 도착 | ACK / Read Response, MSN++ | responder 전체 |

!!! tip "왜 frontend / retry 를 분리했는가"
    Frontend 는 "방금 도착한 응답 1 건의 즉각 처리" 책임. Retry 는 "outstanding WQE 의 timer 기반 재발행" 책임. **두 작업의 II 요구가 다르고** (frontend = packet rate 직접, retry = sparse), pipeline 을 같이 두면 retry 의 sparse FSM 이 frontend critical path 를 잠식. 분리는 timing closure 결정.

### 5.3 HLS Timing — Bitfile 운영의 시각

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

### 5.4 SWQ — 사내 Send-Work-Queue 인프라

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

### 5.5 검증 (DV) 의 wrapper 단위 책임

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

### 5.6 GPUBoost 사양과의 관계

!!! note "Internal (Confluence: *Latest GPUBoost Specification*, id=1056735249)"
    GPUBoost spec 은 **외부 고객용 RNIC 사양** — opcode 지원, 최대 QP / MR 수, supported MTU, supported atomic op, supported CC 알고리즘 등의 cap 를 정의.

    검증 자료는 항상 spec 의 *latest version* 을 1차 truth 로 본다. 본 학습 모듈은 *snapshot* 이며, spec 에서 cap 변경 시 본문 우선.

---

## 6. 흔한 오해 와 DV 디버그 체크리스트

### 흔한 오해

!!! danger "❓ 오해 1 — 'Frontend 와 retry 는 같은 wrapper 안에 두는 게 맞다 (둘 다 completer 책임)'"
    **실제**: 두 wrapper 의 _timing 요구_ 가 다름. frontend = packet rate, retry = sparse. 합치면 retry 의 sparse FSM 이 frontend critical path 를 잠식. 분리는 timing closure 결정.<br>
    **왜 헷갈리는가**: "둘 다 completer 의 책임이라 한 곳에" 같은 직관.

!!! danger "❓ 오해 2 — 'HLS pipelined for-loop 는 1 cycle II 보장'"
    **실제**: pipelined for-loop 는 _최소 1 FSM state 를 소비_. arrival rate 직접 따르는 thread 에서는 II ≥ T_arrival 이면 throughput cliff. unroll / sticky pop 가 더 안전.<br>
    **왜 헷갈리는가**: "pipelined = 1 cycle II" 의 단순화.

!!! danger "❓ 오해 3 — 'WNS regression 은 한 모듈 안의 문제'"
    **실제**: combined Vivado 단계에서 한 wrapper 의 WNS > 3 ns 가 인접 모듈의 routing 까지 망가뜨림. 그래서 _combined regression diff_ 가 PR 마다 첨부 요건.<br>
    **왜 헷갈리는가**: timing 보고서가 모듈별로 나옴.

!!! danger "❓ 오해 4 — 'SWQ 의 read port 는 단일'"
    **실제**: read port 가 다중화돼 있고 (`s_data_port_0/3/4`), modify / read_init / read 의 ordering 이 channel 별로 보장. 같은 channel 로 들어가야 ordering 정합.<br>
    **왜 헷갈리는가**: 일반 RAM 의 단일 read port 직관.

!!! danger "❓ 오해 5 — 'Debug register 는 reset 후 깨끗'"
    **실제**: sticky bit 가 많아 reset 후 read 해도 잔여 가능. bring-up 직후 `clear-on-read` 패스를 sequence 에 둬야 함.<br>
    **왜 헷갈리는가**: "reset = clean" 일반 직관.

### DV 디버그 체크리스트

| 증상 | 1차 의심 | 어디 보나 |
|---|---|---|
| 200G 환경에서 throughput cliff | HLS II ≥ T_arrival | timing 보고서 + th_dma_write II |
| `completer_frontend` 에서 CQE 못 만듦 | drop1/drop2 sequence 결정 오류 | QP state read + drop signal trace |
| Retry 가 안 일어남 | timer 미설정 또는 `s_set_timer` 누락 | retry timer 설정 path |
| MSN 이 multi-packet 의 중간에 증가 | responder_frontend 의 MSN++ 로직 | last packet 마커 확인 |
| CC 가 ACK 받았다는 사실을 모름 | m_ack_info 미연결 | wrapper 간 stream 연결 |
| Combined regression 에서 WNS 폭증 | 인접 wrapper 의 FSM state 증가 | combined timing report |
| Bring-up 직후 debug reg 가 비정상값 | sticky bit 잔여 | clear-on-read 시퀀스 누락 |
| SWQ port mismatch → ordering 깨짐 | modify 가 다른 channel 사용 | s_data_port_0 vs _3 vs _4 |
| `m_comp_err_stream` 에 error 가 안 옴 | retry exhaust path 동작 안 함 | retry_cnt > limit 시 QP invalidation |
| GPUBoost spec cap 위반 (예: MTU=2K) | sender 측 cap check 누락 | spec 의 latest cap vs config |

---

## 7. 핵심 정리 (Key Takeaways)

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

### 7.1 자가 점검

!!! question "🤔 Q1 — Wrapper 책임 분리 (Bloom: Apply)"
    Sender 의 `WC_REM_ACCESS_ERR` — _어느 wrapper_ 의 _어느 debug register_ 부터 확인해야 가장 효율적인가?

    ??? success "정답"
        Receiver 측 **responder_frontend** 의 `o_responder_frontend_invalid_request_hwcnt` (BAR2 0x38440) — protection check 위반 카운트. 동시에 access flag, MR/PD validity 도 확인. (Confluence: RDMA debug register guide, id=884966146)

!!! question "🤔 Q2 — HLS II bottleneck (Bloom: Analyze)"
    한 wrapper 의 II 가 다른 wrapper 의 두 배. 전체 throughput 에 어떤 영향?

    ??? success "정답"
        Throughput = 1 / max(II_i). 가장 느린 wrapper 가 전체를 결정. 해결: bottleneck wrapper 를 _두 instance 병렬_ 또는 _unroll_ 로 II 1/2 로. 단 area 폭증 가능.

### 7.2 출처

**Internal (Confluence)**
- `High-Level Architecture Description (for DV team)` (id=1211203656)
- `Completer` (id=1212973064)
- `RDMA debug register guide` (id=884966146)
- 사내 GPUBoost spec (NDA)

---

## 다음 모듈

→ [Module 12 — FPGA Prototyping & Lab Manuals](12_fpga_proto_manuals.md)

[퀴즈 풀어보기 →](quiz/11_gpuboost_rdma_ip_quiz.md)


--8<-- "abbreviations.md"
--8<-- "_inc/topic_abbr.md"
