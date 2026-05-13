# Module 07 — Congestion Control & Error Handling

<!-- DV-SKOOL-CH-CTX:start -->
<div class="chapter-context" data-cat="network">
  <a class="chapter-back" href="../">
    <span class="chapter-back-arrow">←</span>
    <span class="chapter-back-icon">⚡</span>
    <span class="chapter-back-text">RDMA</span>
  </a>
  <span class="chapter-divider">›</span>
  <span class="chapter-marker">Module 07</span>
</div>
<!-- DV-SKOOL-CH-CTX:end -->

<!-- DV-SKOOL-CH-TOC:start -->
<div class="page-toc">
  <span class="page-toc-label">목차</span>
  <a class="page-toc-link" href="#1-why-care-이-모듈이-왜-필요한가">1. Why care?</a>
  <a class="page-toc-link" href="#2-intuition-비유와-한-장-그림">2. Intuition</a>
  <a class="page-toc-link" href="#3-작은-예-한-rkey-위반이-감지에서-recovery-까지-가는-1-cycle">3. 작은 예 — rkey 위반 1 cycle</a>
  <a class="page-toc-link" href="#4-일반화-cc-3단-구조-error-2-클래스-debug-tree">4. 일반화</a>
  <a class="page-toc-link" href="#5-디테일-pfc-ecn-dcqcn-9-시나리오-coverage-confluence">5. 디테일</a>
  <a class="page-toc-link" href="#6-흔한-오해-와-dv-디버그-체크리스트">6. 흔한 오해 + 디버그 체크리스트</a>
  <a class="page-toc-link" href="#7-핵심-정리-key-takeaways">7. 핵심 정리</a>
</div>
<!-- DV-SKOOL-CH-TOC:end -->

!!! objective "학습 목표"
    이 모듈을 마치면:

    - **Explain** Lossless Ethernet 가 RoCEv2 deployment 에서 왜 필요한지, PFC ↔ ECN ↔ DCQCN 가 어떻게 분담하는지 설명한다.
    - **Trace** Local ACK timeout, Implied NAK, RNR retry, Packet Sequence Error 의 흐름을 sender/receiver 양쪽에서 추적한다.
    - **Trace** R-Key violation 한 건이 검출 → NAK → WC error → Error CQ + IRQ → QP recovery 까지 가는 1 cycle 을 따라간다.
    - **Map** 6 가지 Remote Access Error (Access flag, MR bound, PD, R-Key, Operation, Outstanding read) 를 spec/구현 debug flag 에 매핑한다.
    - **Plan** RDMA-TB `vplan/error_handling/` 의 9 시나리오 (S1~S9) 가 각 error class 를 어떻게 커버하는지 설계 관점에서 평가한다.

!!! info "사전 지식"
    - Module 04 (QP FSM, retry_cnt, rnr_retry)
    - Module 06 (PSN, AETH syndrome, Retry timer)
    - Module 05 (Access flag, R_Key/L_Key, PD)

---

## 1. Why care? — 이 모듈이 왜 필요한가

### 1.1 시나리오 — 1000 GPU 가 한 link 에 _동시에_ 보낸다

당신은 1000 GPU 의 _all-to-all_ 통신을 RDMA 로 짭니다. 평소엔 잘 동작합니다. 그런데 _all-reduce ring 의 한 step_ 에서 거의 _모든 GPU_ 가 _하나의 link_ 로 동시에 보내는 incast 가 발생합니다.

다음 세 시나리오를 비교해보세요:

| 시나리오 | Switch buffer | 결과 |
|---------|-------|------|
| **A. CC 없음** | overflow → drop | RC 의 retry → Go-Back-N → throughput 폭락 (수 초 단위 stall) |
| **B. PFC 만** | PAUSE → 상류 link 도 PAUSE → cascading | **Deadlock** (cyclic PAUSE), 또는 head-of-line blocking |
| **C. ECN+DCQCN 만** | mark CE bit → sender 점진 감속 | 반응 시간 ~ µs, 그동안 일부 drop 가능 |
| **D. PFC + ECN + DCQCN** | 즉시 PFC 로 막고, ECN 신호로 sender 가 천천히 감속 | _이중 안전망_ — drop 0, deadlock risk 적음 |

**왜 _3 가지 메커니즘이 동시에 필요_ 한가?**

- **PFC** = 즉각성 (ns scale 의 hop PAUSE) — buffer overflow _직전_ 멈춤. 단점: deadlock risk.
- **ECN** = 신호 (packet 단위 마킹) — sender 가 무엇이 일어났는지 _안다_. 단점: 반응 _이후_.
- **DCQCN** = 적응형 rate control (µs scale) — sender 의 _점진_ 감속/가속 정책. ECN 없이는 신호가 없음.

세 메커니즘의 _time scale_ 이 모두 다르기 때문에 _하나가 다른 것을 대체할 수 없습니다_. 마치 자동차의 ABS + ESP + 안전벨트 같은 _계층화된 안전망_.

**RDMA 의 검증 가치는 "행복 경로" 가 아니라 "에러 경로"** 에 있습니다. 정상 packet 만 보내면 어떤 구현이든 어느 정도 동작 — 진짜 차이는 (1) congestion 발생 시 fairness 와 throughput 회복, (2) error 발생 시 정확한 status 보고와 QP recovery 입니다. RDMA-TB 의 `error_handling` vplan 이 9 시나리오로 거의 모든 error path 를 커버하는 이유.

또한 디버그 시: WC status + debug flag 의 조합이 **root cause 를 1 step 으로 식별 가능한 형태** 로 보고되도록 설계됐기 때문에, 이 매핑을 알면 fail 시 진단이 압도적으로 빠릅니다.

!!! question "🤔 잠깐 — TCP 는 어떻게 풀었나?"
    TCP 도 congestion control 을 합니다 (Cubic, BBR). RDMA 가 _TCP 의 CC 를 그대로 못 쓰는_ 이유는?

    ??? success "정답"
        TCP CC 는 **packet drop 을 _signal 로_ 사용** 합니다 (drop → cwnd 감소). 그런데 RDMA RC 는 _drop = retry 의 비용 폭증_ 이라 drop 을 _signal_ 로 쓸 수 없음. → **drop _전에_ 신호 (ECN) 가 필요**.

        또한 TCP CC 는 _SW_ 가 처리 (RTT 추정, cwnd 관리). RDMA 는 transport offload 가 본질이라 _hardware-level_ 의 빠른 반응 필요 → DCQCN 알고리즘이 hardware-friendly 하게 설계 (probability 기반 rate adjustment).

---

## 2. Intuition — 비유와 한 장 그림

!!! tip "💡 한 줄 비유 — PFC + ECN + DCQCN ≈ 고속도로 운영 3종 세트"
    - **PFC** = 톨게이트 일시 차단 (당장 막 안 들어오게)
    - **ECN** = "이 구간 막힘" 표지판 (운전자 인식)
    - **DCQCN** = 운전자의 속도 자율 조절 (표지판 보고 점진 감속, 풀리면 점진 가속)

    하나만 쓰면 안 됨 — PFC 만 쓰면 deadlock 위험, ECN 만 쓰면 즉각성 부족, DCQCN 은 ECN 신호가 전제.

### 한 장 그림 — Time scale × 메커니즘 분담

**Time scale × 메커니즘 분담**:

| 메커니즘 | Time scale | 역할 |
|---|---|---|
| **PFC** | Fast (ns) | link-level PAUSE, hop 단위 |
| **ECN** | µs | packet 마킹 (CE bit) |
| **DCQCN** | µs ~ ms | sender rate 점진 감속/회복 |

**Error handling 측면 — 2 클래스**:

```d2
direction: down

RETRY: "Transport retry class (4)" {
  direction: down
  T1: "Local ACK timeout"
  T2: "Packet Sequence Error"
  T3: "Implied NAK"
  T4: "RNR (Receiver Not Ready)"
}
ACCESS: "Remote access class (6)" {
  direction: down
  A1: "Access flag violation"
  A2: "MR bound violation"
  A3: "PD violation"
  A4: "R-Key violation"
  A5: "Invalid Op (illegal opcode)"
  A6: "Max read outstanding"
}
RX: "retry_cnt 초과"
QPE: "QP → Err state\nWC status (sender)"
NAKE: "responder NAK + WC\n+ Error CQ + IRQ\ndebug flag 가 정확한\nroot cause 1줄로 보고"
RETRY -> RX
RX -> QPE
ACCESS -> NAKE
```

### 왜 이렇게 설계했는가 — Design rationale

Congestion 의 3단 layered 이유:

- **PFC 만 쓰면**: deadlock + HOL blocking + PFC storm 위험.
- **ECN 만 쓰면**: 마킹은 hop 마다 가능하지만 전파 늦음 — 잠깐 사이 buffer overflow 가능.
- **DCQCN 만 쓰면**: sender 의 자율 조절은 좋지만 link 가 잠시 정지해야 할 때 즉각성이 부족.

→ 빠른 보호 (PFC) + 정밀 신호 (ECN) + 회복 곡선 (DCQCN) 의 조합으로만 균형.

Error 처리의 두 클래스 분리 이유:

- **Transport retry class** = sender 의 retry 메커니즘으로 _자율 회복 가능_ → spec 이 retry timer + retry_cnt 로 정의.
- **Remote access class** = sender 가 잘못한 게 아니라 _권한 부족_ → retry 해도 의미 없음. 즉시 WC error + Error CQ + IRQ 로 별도 path.

debug flag 가 추가된 이유: spec 의 NAK syndrome 만으로는 root cause 가 모호 (예: "Remote Access Error" 가 access flag 인지 PD 인지 range 인지). debug flag 를 추가해 _구현 친화적인 root cause 신호_ 를 제공.

---

## 3. 작은 예 — 한 R-Key 위반이 감지에서 recovery 까지 가는 1 cycle

QP_A (NODE0) 가 QP_B (NODE1) 의 MR_X 에 RDMA WRITE. 그러나 sender 의 packet 의 RETH.rkey 가 corrupt (TX path 에 inject) 되어 잘못된 값.

```
   t=0    NODE0 user code:
            ibv_post_send(QP_A, WRITE, sg_list, remote_va=Va, rkey=Rk_correct)
   t=1    NODE0 HCA: WQE fetch, lkey 검증 통과, packet 생성
   t=2    NODE0 TX adapter (test injection): RETH.rkey ← Rk_corrupt
   t=3    Wire: BTH(WRITE_ONLY, PSN=N) + RETH(va=Va, rkey=Rk_corrupt, len=L) + payload
   t=4    NODE1 HCA: receive packet, 5-step 검증 시작
            (1) rkey lookup: Rk_corrupt → MR 못 찾음 ✗
            → NAK Remote Access Error
            (Error CQ 에 CQE 생성 + debug_flag = WC_FLAG_RESP_RKEY)
            (IB_EVENT_QP_ACCESS_ERR async event)
            (IRQ raise)
   t=5    Wire: BTH(ACKNOWLEDGE) + AETH(syndrome=NAK Remote Access Error)
   t=6    NODE0 HCA: NAK 받음
            → outstanding WQE 의 status = WC_REM_ACCESS_ERR
            → QP_A → Err state
            → in-flight WR 모두 flush (각각 WC error 생성)
   t=7    NODE0 user code: ibv_poll_cq(send_cq) → WC{status=WC_REM_ACCESS_ERR}
            ── 디버그 시:
            검증 환경의 chkWcErrorStatus(t_seqr, qp_num, REM_ACCESS) 통과 (C1)
   t=8    NODE1 user code: ibv_poll_cq(error_cq) → WC{flag=RESP_RKEY}
            ── 검증의 chkWcErrorDebugFlag, chkIrq 통과 (C3, C4, C5)
   t=9    NODE0 user code: Modify(QP_A, Reset)
   t=10   NODE0 user code: Modify(QP_A, Init → RTR → RTS) — 재진입
   t=11   NODE0 user code: ibv_post_send(QP_A, WRITE, ..., rkey=Rk_correct) 정상 IO
            ── 검증의 C6 (recovery) 통과
```

### 단계별 의미

| Step | 위치 | 의미 |
|---|---|---|
| t=0~1 | NODE0 | sender 측은 lkey 만 검증, rkey 는 원본 그대로 |
| t=2 | inject | TB adapter 가 packet TX path 에서 rkey 한 byte 손상 |
| t=4 | NODE1 HCA | 5-step 검증 (M05) 의 첫 단계 (rkey lookup) 에서 실패. 즉시 NAK + Error CQ + IRQ 의 _3-종 통지_ |
| t=5~6 | sender | NAK 받으면 retry 시도조차 안 함 (retry 해도 의미 없는 access 에러) → 즉시 QP Err |
| t=7~8 | both | C1~C6 의 6 check 가 각 점에서 검증 |
| t=9~11 | NODE0 | recovery: Reset → Init → ... → 정상 IO 재시도. 같은 QP 에서 traffic 가능 |

### 만약 transport retry 클래스 (예: ACK drop) 였다면?

```
   같은 시나리오지만 inject 가 NODE0 RX 에 ACK drop:
   t=4'   NODE1 HCA: 정상 처리, ACK 발신
   t=5'   adapter: ACK drop
   t=6'   NODE0 HCA: retry timer 만료 → 같은 PSN 재전송 (retry 1)
   t=7'   adapter: 또 ACK drop
   ... retry_cnt 까지 반복
   t=N    NODE0 HCA: retry exhausted → WC_RETRY_EXC_ERR + QP Err
   ── 차이: NODE1 의 Error CQ 에는 아무 일도 없음 (정상 처리됨)
```

!!! note "여기서 잡아야 할 두 가지"
    **(1) Remote access class 는 retry 안 함, transport class 는 retry 함** — 같은 "QP Err" 끝맺음이지만 가는 길이 다릅니다. inject 시 어느 path 인지 명확히. <br>
    **(2) debug flag 는 spec 외 사내 확장** — `WC_FLAG_RESP_RKEY/RANGE/PD/ACCESS/OP` 의 5종이 root cause 를 단번에 식별. RDMA-TB 의 이 신호가 디버그 시간을 압도적으로 줄여줍니다.

---

## 4. 일반화 — CC 3단 구조 + Error 2 클래스 + Debug tree

### 4.1 Error 의 두 클래스 (요약)

#### A. Transport / Retry 클래스 — Sender 측 timer 기반

| 에러 | 트리거 | Spec 동작 | WC status |
|------|--------|----------|-----------|
| **Local ACK timeout** | Sender 가 retry timer 안에 ACK/NAK 을 못 받음 | retry_cnt 까지 retransmit | `WC_RETRY_EXC_ERR` |
| **Packet Sequence Error (PSE)** | Responder 가 PSN > ePSN (hole) 봄 → NAK syndrome 0x80 | Sender 가 NAK 의 PSN 부터 retransmit | `WC_RETRY_EXC_ERR` |
| **Implied NAK** | Sender 가 ACK 의 PSN 이 ePSN_send 보다 큼 → 중간 ACK 분실 추정 | Sender 가 누락 부분 retransmit | `WC_RETRY_EXC_ERR` |
| **RNR (Receiver Not Ready)** | RC SEND 시 RQ 에 RECV WR 없음 → RNR NAK | RNR timer 후 retry, rnr_retry 까지 | `WC_RNR_RETRY_EXC_ERR` (별도) |

→ **모두 retry exhaust 시 QP → Err state**, sender 의 send CQ 에 WC error.

#### B. Remote Access 클래스 — Responder 측 검증 fail

| 에러 | 원인 | Sender WC | Responder Error CQ flag |
|------|------|-----------|------------------------|
| **MR Access flag violation** | RDMA WRITE 가 Remote Write 권한 없는 MR 에 도달 | `WC_REM_ACCESS_ERR` | `WC_FLAG_RESP_ACCESS` |
| **MR Bound violation** | (remote_va, len) 가 MR 영역 밖 | `WC_REM_ACCESS_ERR` | `WC_FLAG_RESP_RANGE` |
| **PD violation** | MR 의 PD 와 QP 의 PD 불일치 | `WC_REM_ACCESS_ERR` | `WC_FLAG_RESP_PD` |
| **R-Key violation** | RETH 의 R-Key 가 잘못 / 만료 | `WC_REM_ACCESS_ERR` | `WC_FLAG_RESP_RKEY` |
| **Invalid Request (Op)** | Service type 에 허용 안 된 OpCode (예: UC 에 READ) | `WC_REM_INV_REQ_ERR` | `WC_FLAG_RESP_OP` |
| **Max read outstanding** | Outstanding READ 가 max_dest_rd_atomic 초과 | `WC_REM_INV_RD_REQ_ERR` | `WC_FLAG_RESP_OP` |

→ **Responder 측은 추가로 async event** `IB_EVENT_QP_ACCESS_ERR` 를 Error CQ 에 보고 + IRQ 발생.

(이 분류는 RDMA-TB `vplan/error_handling/VPLAN_error_handling.md` 에 그대로 매핑)

### 4.2 실무 에러 디버그 트리

```d2
direction: down

ROOT: "WC error 발견\n(status?)"
R1: WC_RETRY_EXC_ERR { style.stroke: "#b8860b"; style.stroke-width: 2 }
R2: WC_RNR_RETRY_EXC_ERR { style.stroke: "#b8860b"; style.stroke-width: 2 }
R3: WC_REM_ACCESS_ERR { style.stroke: "#c0392b"; style.stroke-width: 2 }
R4: WC_REM_INV_RD_REQ_ERR { style.stroke: "#c0392b"; style.stroke-width: 2 }

R1a: "ACK 못 받음\n(Local ACK timeout)" { style.stroke: "#b8860b"; style.stroke-width: 2 }
R1b: "PSN hole (PSE)" { style.stroke: "#b8860b"; style.stroke-width: 2 }
R1c: "ACK 의 PSN > ePSN\n(Implied NAK)" { style.stroke: "#b8860b"; style.stroke-width: 2 }
R1note: "모두 retry_cnt 초과"
R2a: "Receiver 가 RECV WR 부족\n→ rnr_retry_cnt 초과" { style.stroke: "#b8860b"; style.stroke-width: 2 }
R3a: "debug_flag = WC_FLAG_RESP_ACCESS\n(access flag)" { style.stroke: "#c0392b"; style.stroke-width: 2 }
R3b: "debug_flag = WC_FLAG_RESP_RANGE\n(MR bound)" { style.stroke: "#c0392b"; style.stroke-width: 2 }
R3c: "debug_flag = WC_FLAG_RESP_PD\n(PD mismatch)" { style.stroke: "#c0392b"; style.stroke-width: 2 }
R3d: "debug_flag = WC_FLAG_RESP_RKEY\n(R-Key invalid)" { style.stroke: "#c0392b"; style.stroke-width: 2 }
R4a: "debug_flag = WC_FLAG_RESP_OP\n(max read outstanding)" { style.stroke: "#c0392b"; style.stroke-width: 2 }

ROOT -> R1 -> R1a
R1 -> R1b
R1 -> R1c
R1a -> R1note
R1b -> R1note
R1c -> R1note
ROOT -> R2 -> R2a
ROOT -> R3 -> R3a
R3 -> R3b
R3 -> R3c
R3 -> R3d
ROOT -> R4 -> R4a
```

→ **Debug flag 만 보면 root cause 가 결정** — 검증이 잘 되면 사용자도 single-glance 디버그 가능.

---

## 5. 디테일 — PFC, ECN, DCQCN, 9 시나리오, Coverage, Confluence 보강

### 5.1 PFC (Priority-based Flow Control, IEEE 802.1Qbb)

```
   Switch buffer 가 차오르면 → upstream port 에 PAUSE frame 송신
   PAUSE 는 priority 별 (0..7) 독립
   Pause time 만큼 sender 는 해당 priority 송신 정지
```

- 0..7 priority class (Ethernet PCP / DSCP 매핑).
- RDMA 트래픽은 보통 priority 3 또는 26 (DSCP 26 = AF31).
- "Lossless" priority 만 PFC enable, 나머지는 일반 best-effort.

**위험**: cyclic dependency → PFC storm → deadlock. → **deadlock 회피는 routing 설계 시 deadlock-free path 보장 또는 watchdog** 필요.

### 5.2 ECN (Explicit Congestion Notification, RFC 3168)

```
   IP header 의 ECN field (2 bit):
     00  Non-ECT (Not ECN-Capable)
     01  ECT(1)
     10  ECT(0)
     11  CE  (Congestion Experienced)
```

- Sender 가 ECT 로 표시 → switch 가 buffer 임계 초과 시 CE 로 마킹 (drop 대신).
- Receiver 가 CE 보면 → 그 사실을 sender 에 알려야 함.
- IB 에서는 BTH 의 **FECN bit** 를 receiver 가 다음 packet 에 set 해 sender 가 알게 함.
- 또는 RoCEv2 의 **CNP** (Congestion Notification Packet) 를 receiver 가 sender 에 직접 송신.

### 5.3 DCQCN (Data Center QCN)

CNP/ECN 신호에 따른 **sender 의 rate 조절 알고리즘**:

```
                  RTT
   rate
    ▲                                         _____
    │                                  ____/
    │ initial   ▼CNP                  /
    │ R = R_max  └ rate ÷ 2          / linear increase
    │            ↓                  /
    │          ─────────────________/
    │
    └──────────────────────────────────────────► time
```

- Initial rate = R_max
- CNP 받으면 R *= 0.5 (또는 α 비율)
- CNP 안 받으면 (timer 단위로) R 점진 회복:
  - Fast Recovery → Active Increase → Hyper Increase 단계
- 검증의 핵심은 "fairness" — 두 flow 가 같은 bottleneck 를 share 했을 때 R 분포가 공평한지.

→ 실무에서 DCQCN 의 parameter 튜닝 (α, R_min, recovery time) 이 deployment 별로 다름.

### 5.4 RDMA-TB 의 9 Error Scenarios (S1~S9)

(`/home/jaehyeok.lee/RDMA/RDMA-TB/docs/vplan/error_handling/VPLAN_error_handling.md` 기준)

| ID | 시나리오 | Injection | Expected |
|----|---------|-----------|----------|
| **S1** | Local ACK timeout retry exceed | NODE1 RX 에 packet drop 콜백 | `WC_RETRY_EXC_ERR`, recovery OK |
| **S2** | PSE retry exceed | NODE1 RX 에 PSN 기반 drop | `WC_RETRY_EXC_ERR` |
| **S3** | Implied NAK retry exceed | NODE0 RX 에 ACK drop | `WC_RETRY_EXC_ERR` |
| **S4** | RNR retry exceed | NODE0 RX 에 NAK drop + rnr_retry_exceed_en=1 | `WC_RNR_RETRY_EXC_ERR` (별도 status) |
| **S5** | Remote MR access flag violation | NODE1 의 MR access flag 클리어 | sender `WC_REM_ACCESS_ERR` + responder ErrCQ `WC_FLAG_RESP_ACCESS` |
| **S6** | Remote MR bound violation | NODE0 TX 에 length corrupt | `WC_REM_ACCESS_ERR` + `WC_FLAG_RESP_RANGE` |
| **S7** | Remote PD violation | NODE1 의 MR global key override | `WC_REM_ACCESS_ERR` + `WC_FLAG_RESP_PD` |
| **S8** | Remote R-key violation | NODE0 TX 에 rkey corrupt | `WC_REM_ACCESS_ERR` + `WC_FLAG_RESP_RKEY` |
| **S9** | Max read outstanding violation | NODE1 RX 에 read 중복 inject | `WC_REM_INV_RD_REQ_ERR` + `WC_FLAG_RESP_OP` |

각 시나리오의 검증 흐름:

```
   1) Multi-QP 환경 setup (1 개 QP 가 error inject 대상, 나머지 정상 traffic)
   2) Adapter callback 등록 (drop / corrupt / duplicate)
   3) vrdma_io_err_top_seq 실행
   4) chkWcErrorStatus(t_seqr, qp_num, expected) 검증
   5) (S5~S9) Error CQ poll + chkWcErrorDebugFlag + chkIrq 검증
   6) (S1) QP recovery 검증 — 동일 QP 에 정상 IO 재시도 가능한지
```

→ **검증 항목 (Check ID)** 6 가지 (C1~C6):

| Check | 의미 |
|-------|------|
| C1 | Requester 측 send CQ status 가 expected error |
| C2 | Responder 측 Error CQ 에 IB_EVENT_QP_ACCESS_ERR |
| C3 | Responder 측 debug flag 가 정확히 access/range/PD/rkey/op 중 하나 |
| C4 | Error CQ 에 실제 CQE 가 생성됨 |
| C5 | Error CQ IRQ 가 ERR_IRQ_TIMEOUT_CYCLES 안에 raise |
| C6 | (S1) Error 후 동일 QP 에서 정상 IO 가능 |

### 5.5 Coverage 모델 — 7 항목

(`vrdma_error_handling_cov.svh` 기준)

| Cov | 정의 |
|-----|------|
| COV1 | Send CQ 의 WC status (RETRY_EXC, RNR_RETRY_EXC, REM_ACCESS, REM_INV_RD_REQ, ...) |
| COV2 | Send CQ vs Error CQ 분포 |
| COV3 | Error CQ 의 event type (IB_EVENT_QP_ACCESS_ERR vs other) |
| COV4 | Error 발생 시 outstanding op 의 존재/부재 |
| COV5 | Cross: status × outstanding |
| COV6 | Cross: node × status (요청자 vs 응답자) |
| COV7 | Cross: CQ (send vs err) × status |

→ **모든 시나리오가 hit 해도 cross coverage 가 아직 hole 일 수 있음** — 예: `WC_RNR_RETRY_EXC_ERR × outstanding_exists × NODE1` 이라는 특정 cross. 그래서 **시나리오를 다양한 traffic mix 와 결합해 반복 실행** 하는 것이 closure 전략.

### 5.6 QP Recovery 흐름

```d2
direction: down

E: "에러 발생"
ERR: "QP → Err state\n(in-flight WR 모두 flush, WC error)"
POLL: "사용자가 Error CQ poll, status 확인"
RST: "Modify(QP, Reset)\nQP 를 리셋"
BRINGUP: "Modify(Init / RTR / RTS)\n단계 재진입"
IO: "다시 정상 IO"
E -> ERR
ERR -> POLL
POLL -> RST
RST -> BRINGUP
BRINGUP -> IO
```

`min_rnr_timer`, `retry_cnt`, `timeout` 등 attribute 도 새로 set 가능 — recovery 시 parameter 튜닝의 기회.

### 5.7 Congestion 검증 시나리오

(이 부분은 `error_handling` vplan 외 일반적인 RDMA congestion verification 패턴)

| 시나리오 | 목표 |
|---------|------|
| **Incast** | N → 1 traffic, switch buffer 압박, ECN/CNP 발생 빈도 |
| **All-to-all** | M ↔ M, fairness 검증 |
| **PFC pause time variation** | 짧은/긴 pause 가 throughput 에 미치는 영향 |
| **DCQCN parameter sweep** | α, R_min 변경 후 회복 곡선 분석 |
| **PFC deadlock** | 의도적 cyclic dependency, watchdog 동작 검증 |
| **CNP latency** | 마킹 → CNP → rate adjust 까지 RTT |

이런 시나리오는 시스템 레벨 (board / ip_top) 환경에서 수행, sub-IP 단계에서는 보통 inject-only 모델로 추상화.

### 5.8 Confluence 보강 — PFC 의 정확한 동작과 한계

!!! note "Internal (Confluence: Priority-based Flow Control, id=229998593 + 6 sub-pages)"
    PFC 는 **8 priority class** 마다 독립적인 PAUSE / RESUME 메시지를 link partner 에 보낸다.

    - **Pause Frame (802.1Qbb)**: 64-byte Ethernet control frame. `Pause Quanta` (16-bit) 가 *priority 별 정지 시간* 을 512-bit time 단위로 지정. 0 = resume.
    - **Pause Operation**: 큐 임계치 초과 시 ingress 에서 자동 발생. 큐 길이가 임계치 미만으로 떨어지면 RESUME (=Pause 0).
    - **DiffServ / Traffic Class**: PFC priority 는 **Ethernet PCP** 비트 또는 **DSCP→TC** 매핑으로 결정. RoCEv2 는 보통 DSCP 26 (AF31) → PFC priority 3 같은 deployment-specific mapping.
    - **DELL switch 활성화 (참고)**: `dcb-map`, `priority-flow-control mode on`, `service-policy input <pfc-policy>` 의 3-step. 검증 환경 cabinet 의 운영 가이드에 동일.
    - **Limitation**:
      - PFC storm — cyclic dependency 시 dead-lock.
      - HOL (Head-of-Line) blocking — 같은 priority class 의 다른 flow 전체 정지.
      - Switch-vendor 별 buffer hysteresis 가 다름 → throughput dent 발생 위치가 다름.

### 5.9 Confluence 보강 — Layered CC 의 사내 구성

!!! note "Internal (Confluence: Basic Background, CC in IB Spec, DCQCN in detail, RoCEv2 ECN in detail, Google's CC, HPCC, CORN, Zero-touch RoCE, Programmable CC)"
    사내 RDMA-IP 와 검증 자료에서 다루는 CC 알고리즘 계열:

    | 계열 | 신호 | 대표 알고리즘 | 사내 위치 |
    |---|---|---|---|
    | **L2 immediate** | PFC pause | 802.1Qbb | network env |
    | **L3 implicit** | ECN-CE marking | DCQCN | RDMA-IP CC module |
    | **End-to-end RTT** | RTT 측정 | Swift, RTTCC, ZTR | DCQCN 대안 (programmable) |
    | **In-network telemetry** | INT header | HPCC | research / 비교 |
    | **Cloud-fairness** | per-tenant SLA | CORN | research / 비교 |
    | **Hardware reliable transport** | full offload | Falcon, Nvidia BFD | competitor survey |

    !!! tip "검증 결정 트리"
        1. **PFC 만 활성** → buffer overflow 만 검증. ECN/DCQCN 비활성.
        2. **PFC + ECN** → CNP 발생 빈도 확인. DCQCN α/R_min sweep.
        3. **No-PFC (Lossy mode)** → ZTR 또는 DCQCN-only 로 packet loss 회복 검증 — 사내에서는 향후 UEC 호환 모드.

### 5.10 Confluence 보강 — Error handling 카테고리 매핑

!!! note "Internal (Confluence: Error handling in RDMA, id=152502273)"
    Confluence 페이지의 error class 분류는 RDMA-TB 의 vplan S1~S9 와 다음과 같이 매핑된다.

    | Confluence 분류 | RDMA-TB S/C | 노출 |
    |---|---|---|
    | Local PROT (sg lkey/access) | S1 | requester WC `LOC_PROT_ERR` |
    | Remote ACCESS (rkey/access) | S2 | NAK + requester WC `REM_ACCESS_ERR` |
    | Remote OP (illegal opcode) | S3 | NAK syndrome 0x91, WC `REM_INV_REQ_ERR` |
    | PSN sequence error | S4 | NAK syndrome 0x60 |
    | RNR | S5 | NAK syndrome 0x20 + min_rnr_timer 대기 |
    | Implied NAK | S6 | 별도 NAK 없이 PSN 점프 |
    | Local ACK timeout | S7 | timer 만료 → retry |
    | Retry exceeded | S8 | QP → Err, WC `RETRY_EXC_ERR` |
    | RNR retry exceeded | S9 | QP → Err, WC `RNR_RETRY_EXC_ERR` |

    !!! warning "주의"
        spec 의 syndrome 값은 IB Spec 1.4 vs 1.7 에서 일부 reserved → defined 로 변경됨. M03 §8 참조.

### 5.x Fault Classes — Requester / Responder 분류

§4 의 debug tree 가 _"어떤 WC status 가 뜨는가"_ 의 외형이라면, **Fault Class 는 RNIC 내부에서 _어떤 정책으로_ error 를 처리하는가** 의 분류입니다. IBTA 의 §10.x 와 사내 RDMA-IP 설계가 같이 따르는 모델.

#### Requester side — 3 클래스 (A / B / C)

| Class | 의미 | Trigger | 처리 |
|-------|------|---------|------|
| **A (Recoverable)** | retry 만 하면 회복 | • PSE NAK (PSN sequence err)<br>• Implied NAK (missing PSN)<br>• Local-ACK timeout<br>• RNR NAK (retry counter 남아있음) | Go-Back-N 으로 outstanding 전체 재전송. QP **= RTS 유지** |
| **B (Non-recoverable)** | retry 불가 — fatal | • retry_cnt 0 도달<br>• Local protection err (L_Key/R_Key 위반, opcode err)<br>• `IBV_WC_RETRY_EXC_ERR`, `IBV_WC_RNR_RETRY_EXC_ERR`, `IBV_WC_REM_ACCESS_ERR` 류 | **QP → Err**, 모든 outstanding WQE 를 `IBV_WC_WR_FLUSH_ERR` 로 완료. **단** 최초 트리거 WQE 는 본래 status 유지. in-order completion 순서 보존. |
| **C (Ghost — no impact)** | 받았지만 무시 가능 | • PSN 이 outstanding window 밖인 ACK (지각된 unsolicited credit ACK 일 수 있음) | 패킷 폐기. credit 만 update. retry counter 영향 없음 |

#### Responder side — 5 클래스 (A / B / C / D / J)

| Class | 의미 | Trigger | 처리 |
|-------|------|---------|------|
| **A (Local QP error)** | responder 자체의 보호 위반 | • L_Key/MR access 위반 (CONSUME 단계의 RECV WQE 의 sg_list 가 invalid) | 현 RQE 를 ERR 로 complete, 나머지 flush, **QP → Err** (NAK 없음 — 자신의 buf 문제이므로) |
| **B (Detected on packet, no local impact)** | 들어온 패킷이 잘못 — 그러나 QP 는 살아있음 | • PSN sequence error 상황 (out-of-order or hole)<br>• RNR (RECV WQE 없음) | NAK 송신, **패킷 폐기**, QP **= RTS 유지** |
| **C (Fatal protocol violation)** | 프로토콜 자체가 깨짐 | • QP flag 위반 (RC 인데 UD 패킷 등)<br>• Atomic VA 가 8B misalign<br>• R_Key 또는 MR flag 위반 (operation 차원)<br>• Opcode sequencing 위반 (LAST 없는 FIRST/MIDDLE) | 현 RQE ERR 로 complete + 나머지 flush, **QP → Err**, NAK 송신 |
| **D (Ignored/Dropped)** | duplicate 인데 cache 없음 | • duplicate ATOMIC/READ 인데 connection context 에 해당 PSN 안 보임 (`max_dest_rd_atomic` 초과로 evicted) | **Silently drop**. requester 는 timeout 으로 인지 → retry counter 깎임. |
| **J (Send_w_INV error)** | invalidate 대상 R_Key 가 잘못 | • IETH 의 R_Key 가 invalid 또는 wrong PD/MR | 현 RQE 를 `IBV_WC_MW_BIND_ERR` 로 complete, 나머지 flush, **QP → Err**, NAK 송신 |

#### 한 장 매핑 — 사내 S1~S9 와의 관계

| Class | 사내 vplan S 시나리오 | C-check 매핑 |
|-------|---------------------|------------|
| Requester-A | S1 (Local ACK timeout), S2 (PSE), S3 (Implied NAK), S4 (RNR) 의 *retry-내* 영역 | (시나리오 자체는 retry 가 일어남을 확인) |
| Requester-B | S1~S4 의 **retry 초과**, S5~S8 (REM_ACCESS) | C1 (WC status), C4 (Error CQ CQE), C5 (IRQ) |
| Requester-C | (직접 시나리오 없음 — coverage 보강 영역) | — |
| Responder-A | (사내 IP 내부 — sg_list 가 invalid 인 RECV) | scoreboard 의 local-prot trap |
| Responder-B | S2 (PSE inject), S4 (RNR inject) | wire dump 의 NAK syndrome |
| Responder-C | S5~S8 (access/range/PD/rkey), S9 (max-rd-atomic 초과) | C2, C3 (debug_flag) |
| Responder-D | duplicate ATOMIC/READ drop — coverage 항목 | COV4·5 의 outstanding cross |
| Responder-J | Send_w_INV inject (corner) | `WC_MW_BIND_ERR` 검출 |

!!! note "왜 분류가 양면이 다른가"
    같은 사건 (예: rkey 위반) 이 양 끝에서 _전혀 다른 의미의 error_ 를 만듭니다.
    Responder 입장 = **Fatal (C)** — 내 메모리 보호가 깨질 뻔; QP 죽임.
    Requester 입장 = **Non-recoverable (B)** — 상대가 NAK 으로 알려주면 retry 가 무의미.
    검증 환경은 양 끝 각각의 처리를 **별도로** 확인해야 합니다 — 한쪽만 보면 false-OK 가 가능.

### 5.y Local-ACK Timer State Machine — requester 시점

§3 의 retry 1-cycle 예시는 ACK timeout 의 _한 trigger_ 만 본 것입니다. 실제 RNIC 의 timer state 는 다음 네 trigger 의 조합으로 움직입니다.

```
                  ┌─────────┐
                  │  IDLE   │  outstanding 없음 / 모든 ACK 처리됨
                  └────┬────┘
                       │ new outstanding request 발생
                       │ (SEND/WRITE with AckReq=1, READ, ATOMIC)
                       ▼
                  ┌─────────┐  valid ACK 도달 (coalesced 포함)
                  │ RUNNING │ ────────────────────────┐
                  │ (timer  │  새 outstanding request │
                  │  활동)  │ ◀───────────────────────┘  → timer restart
                  └────┬────┘
                       │ timer 만료
                       │ (= local_ack_timeout = 4.096µs × 2^attr.timeout)
                       ▼
                  ┌─────────┐  retry_cnt > 0?
                  │ EXPIRED │
                  └────┬────┘
                  ┌────┴────────┐
                  │ Yes         │ No
                  ▼             ▼
        ┌──────────────┐  ┌─────────────────┐
        │  GO-BACK-N    │  │ RETRY_EXC_ERR  │  → QP=Err, flush
        │  retransmit   │  │ Class B (req)  │
        │  retry_cnt--  │  └─────────────────┘
        │  timer restart│
        └──────┬────────┘
               ▼
              RUNNING (다시)
```

| Event | Timer 행동 | retry_cnt |
|-------|----------|-----------|
| new request 발신 (AckReq=1) | IDLE → RUNNING (start) | 영향 없음 |
| valid ACK 도착 (coalesced 포함) | RUNNING 유지, **restart** | 영향 없음 |
| 모든 ack 처리, outstanding=0 | RUNNING → IDLE (stop) | 영향 없음 |
| NAK / Implied NAK 도착 | (RUNNING 유지, 재전송 발생) | `--` |
| RNR NAK 도착 | **RNR timer 별도 가동** (AETH timer field 값) | `rnr_retry --` |
| local_ack_timeout 만료 | RUNNING → EXPIRED → GO-BACK-N | `retry_cnt --` |
| retry_cnt = 0 도달 | → Err | — |

!!! warning "ACK 가 retry_cnt 를 *복원하지 않음*"
    spec 상 retry_cnt 는 **단조 감소**. 일부 정상 ACK 으로 회복되지 않으며, QP 가 Err 후 복구해야 reset 됨. 검증 시나리오에서 "잠시 끊겼다 회복" 이 retry_cnt 0 으로 떨어지는 시점을 정확히 잡아야 false PASS 가 안 남.

### 5.z Three-PSN Paradigm (requester 의 PSN 추적)

retry 시 requester 가 _어떤 PSN 부터 재전송할지_ 를 정하려면 한 변수로 부족합니다. 사내 IP 와 IBTA 모델은 세 marker 를 유지합니다.

| Marker | 의미 |
|--------|------|
| **OldestUnackedPSN** | 아직 ACK 못 받은 가장 오래된 outstanding PSN |
| **RetryPSN** | 지금 재전송 중인 PSN (timer-retry 또는 NAK-retry 의 시작점) |
| **MaxForwardPSN** | 지금까지 보낸 가장 큰 PSN (다음 새 request 의 base) |

```
   PSN axis →   100  101  102  103  104  105  106  107  108  109  ...
                ╶─── ACK 받음 ───╴ ╶── outstanding (대기) ──╴ ╶ 보내질 ╴
                                  ▲                            ▲
                          OldestUnackedPSN              MaxForwardPSN
                                  ▲
                            RetryPSN (NAK 받은 이후 재전송 중)
```

- `RetryPSN ≥ OldestUnackedPSN` 항상.
- timer-retry 와 NAK-retry 가 동시에 trigger 되면 (예: 늦은 NAK + 새 timeout) **이미 retry 중인 lower PSN** 을 우선 — `started_retry` flag 로 중첩 재전송 방지.
- coalesced ACK 가 들어오면 `OldestUnackedPSN` 이 점프 → `RetryPSN` 도 같이 점프 (이미 ACK 된 PSN 은 재전송 무의미).

→ 사내 PPTX 의 "Case 1 (request missing) / Case 2 (response missing) / Case 3 (both missing)" 시나리오는 모두 이 세 marker 와 `started_retry` flag 가 trigger 의 조합에서 어떻게 움직이는지를 확인하는 것입니다.

### 5.11 Confluence 보강 — CCMAD 와 Adaptive Routing

!!! note "Internal (Confluence: CCMAD Protocol, id=290127949; How to enable Adaptive Routing for CX, id=397967495)"
    - **CCMAD (Congestion Control MAD)**: SM (Subnet Manager) 가 CC 파라미터 (예: CCT entry, CN_ROUNDS) 를 노드에 분배할 때 사용하는 IB MAD 클래스. RoCEv2 환경에서는 CC controller 가 같은 의미를 NVMe-oF/host SW 로 대체.
    - **Adaptive Routing (CX)**: switch 가 link load 기반으로 **packet 단위 경로 선택**. RC 의 in-order 가정을 깰 수 있어, RDMA-IP 는 SACK + per-path PSN 추적을 같이 켜야 안전. 사내 검증에서는 이를 *AR mode* 라 부르고 별도 시나리오로 둠.

---

## 6. 흔한 오해 와 DV 디버그 체크리스트

### 흔한 오해

!!! danger "❓ 오해 1 — 'Congestion 시 PFC PAUSE 받으면 sender 가 멈추니 packet drop 안 일어난다 → 끝'"
    **실제**: PFC 만 쓰면 **deadlock + head-of-line blocking + PFC storm** 위험. 여러 priority 가 cyclic 의존을 가지면 PAUSE 가 무한 전파 가능. 그래서 PFC 는 fallback, ECN+DCQCN 이 주된 throttle 메커니즘. **검증 시 PFC 만 enabled 한 환경에서 의도적으로 cyclic traffic 을 만들어 deadlock 검출**이 핵심 시나리오.<br>
    **왜 헷갈리는가**: PFC 가 spec 상 "lossless 만든다" 는 표현 때문에 만능으로 보임.

!!! danger "❓ 오해 2 — 'Remote Access Error 는 retry 해서 회복 가능'"
    **실제**: Remote access class 는 retry 없이 **즉시** QP Err. retry 해도 같은 권한 부족이 반복될 뿐. 즉시 recovery 시퀀스 (Reset → Init...) 가 필요.<br>
    **왜 헷갈리는가**: "에러 = retry" 의 일반화.

!!! danger "❓ 오해 3 — 'ACK timeout 과 PSE 와 Implied NAK 는 모두 같은 retry 메커니즘'"
    **실제**: trigger 가 다르고 _누가 먼저 알아채는가_ 가 다릅니다. ACK timeout = sender 의 timer 만료. PSE = responder 의 NAK syndrome. Implied NAK = sender 가 ACK PSN 점프로 추정. 같은 `WC_RETRY_EXC_ERR` 로 끝나지만 _발견 경로_ 검증이 별도.<br>
    **왜 헷갈리는가**: WC status 가 같음.

!!! danger "❓ 오해 4 — 'WRITE/READ 도 RNR 발생 가능'"
    **실제**: RNR 은 RECV WR 을 소비하는 op (SEND, SEND_w_IMM, WRITE_w_IMM) 에서만. WRITE/READ 는 RECV WQE 안 씀.<br>
    **왜 헷갈리는가**: M06 의 같은 오해.

!!! danger "❓ 오해 5 — 'debug flag 도 IB spec 의 일부'"
    **실제**: spec NAK syndrome 만으로는 root cause 가 모호 → **사내 RDMA-IP 의 확장 신호**. 검증 환경에서 매우 유용하지만 spec-portable 코드에서는 가정 금지.<br>
    **왜 헷갈리는가**: 같은 CQE structure 안에 있어 spec 처럼 보임.

!!! danger "❓ 오해 6 — 'DCQCN parameter 는 hard-code 가능'"
    **실제**: vendor 와 deployment 마다 달라서, scoreboard 가 algorithm 가정을 hard-code 하면 다른 algorithm DUT 에 적용 불가. interface 분리 + parameter sweep 으로 검증해야 portable.<br>
    **왜 헷갈리는가**: 한 deployment 에서는 "정답" 처럼 보임.

### DV 디버그 체크리스트

| 증상 | 1차 의심 | 어디 보나 |
|---|---|---|
| `WC_RETRY_EXC_ERR` 후 어떤 path 인지 모름 | ACK drop / PSN hole / Implied NAK 중 하나 | wire dump 의 마지막 ACK PSN, NAK syndrome |
| `WC_REM_ACCESS_ERR` 만 보고 root cause 모름 | debug_flag 미확인 | Error CQ 의 debug_flag 비트 |
| Recovery 시퀀스 후 traffic 안 나감 | QP Reset 안 거친 채 RTR 재진입 시도 | QP state read |
| PFC enable 했는데 deadlock 발생 | cyclic dependency, watchdog 없음 | priority graph + pause duration |
| ECN-CE 마킹했는데 sender rate 변화 없음 | DCQCN 미구현 / CNP 미수신 | CNP 카운터, RTT 측정 |
| Error CQ IRQ 가 안 raise | irq mask / event subscription 누락 | irq_mask register |
| recover 후 첫 traffic 만 silent drop | TLB stale / R_Key epoch 갱신 누락 | TLB log + key_epoch |
| RNR retry 와 일반 retry 카운터 한쪽만 작동 | 둘이 별도임을 모름 | rnr_retry vs retry_cnt attribute |
| Coverage cross hole | scenario × traffic mix 부족 | COV5~7 의 hit map |
| Adaptive Routing mode 에서 PSN out-of-order false fail | scoreboard 의 strict-order 가정 | per-path PSN 추적 + SACK 비트맵 |

---

## 7. 핵심 정리 (Key Takeaways)

- Congestion 은 PFC (즉시) + ECN (신호) + DCQCN (rate control) 의 layered 메커니즘.
- Error 는 transport-retry 클래스 4개 (Local ACK/PSE/Implied/RNR) + remote-access 클래스 6개 (access/range/PD/rkey/op/outstanding-read).
- RDMA-TB `error_handling` vplan 의 S1~S9 가 모두를 커버, C1~C6 check 가 검증 항목.
- WC status + debug flag 의 조합이 **root cause 를 1 step 으로 식별 가능한 형태** 로 보고됨.
- QP recovery 는 Err → Reset → Init → ... 으로 진행, sequence/test 가 이 path 를 명시적으로 trigger.

!!! warning "실무 주의점"
    - "Lossless Ethernet" 가정이 깨지면 (PFC 미지원 switch 가 path 에 끼어들면) RDMA 성능 cliff. 환경 점검이 검증 시작점.
    - PFC storm 을 catch 하려면 **PFC pause duration 의 분포** 를 cov 에 추가해야 함 — 단순 "PFC 발생/안 발생" 으론 부족.
    - DCQCN parameter 는 vendor-specific. RDMA-TB scoreboard 가 algorithm 가정을 hard-code 하면 다른 algorithm DUT 에 적용 불가 — interface 분리 필요.
    - Error CQ 의 IRQ timeout 은 spec 외 deployment-specific. RDMA-TB 의 `ERR_IRQ_TIMEOUT_CYCLES` 가 그 값. 사양 변경 시 같이 조정.
    - Recovery 후 동일 QP 에서 새 traffic 시작 전 cleanup 필요 (in-flight WR 의 잔여 cleanup → 검증).

### 7.1 자가 점검

!!! question "🤔 Q1 — PFC deadlock 분석 (Bloom: Analyze)"
    당신의 fabric 에서 _PFC storm_ 이 발생. 모든 switch 의 link 가 PAUSE 상태. _왜 deadlock 이 가능한가_? ECN+DCQCN 도 같이 켰는데 왜 deadlock 을 못 막았나?

    ??? success "정답"
        **Cyclic dependency**: switch A 의 link 가 가득 차서 B 에게 PAUSE → B 의 link 도 가득 차서 A 에게 PAUSE → 서로 못 보냄.

        ECN+DCQCN 은 _sender 의 rate_ 를 줄이지만, _이미 buffer 에 쌓인 패킷_ 이 drain 되기 전엔 PFC PAUSE 는 풀리지 않음. 즉 ECN 신호가 _뒤늦게_ 도착.

        해결:
        1. **PFC priority class 분리** — 우선순위 다른 트래픽은 독립적 buffer, deadlock 영역 분리.
        2. **DCQCN 의 빠른 반응** — incast 시작 첫 µs 내 sender 가 감속.
        3. **Edge switch 의 ECN marking aggressiveness** — buffer 50% 부터 미리 mark.

!!! question "🤔 Q2 — `WC_RETRY_EXC_ERR` 원인 분리 (Bloom: Apply)"
    Sender 가 `IBV_WC_RETRY_EXC_ERR` 를 받았습니다. 가능한 _세 가지_ 근본 원인을 분리하시오 (transport / receiver / network).

    ??? success "정답"
        - **Transport 측**: retry_cnt 또는 timeout 너무 작음 → 정상 network jitter 에도 retry exhaust.
        - **Receiver 측**: ACK 못 보냄 — RNR 후 RECV pre-post 못 받았거나, responder 가 silent drop (P_Key/Q_Key 등).
        - **Network 측**: incast → PFC storm → ACK packet 자체가 _delayed_ → sender 가 ACK 받기 전 retry 한도 도달.

        디버그 순서: (1) receiver 의 _NAK syndrome_ 확인 → silent drop 인가 NAK 인가, (2) PFC counter 확인 → storm 인가, (3) retry_cnt / timeout 값 확인.

!!! question "🤔 Q3 — RDMA-TB error 시나리오 설계 (Bloom: Evaluate)"
    당신은 RDMA-TB 의 `error_handling` vplan 을 본다. S1~S9 시나리오가 _모든 fault class_ 를 커버하는지 어떻게 검증하시겠습니까?

    ??? success "정답"
        Fault class matrix (§5 의 Requester A/B/C + Responder A/B/C/D/J) 를 _세로 축_, S1~S9 를 _가로 축_ 으로 표 작성. 각 (row, col) 셀에 "이 시나리오가 이 fault 를 cover 하나?" 표기.

        - 빈 셀 = vplan hole → 추가 시나리오 제안.
        - 한 셀에 여러 ✓ = redundant, 정리 가능.

        Coverage 관점: 단순 시나리오 수 (9) 가 아닌 **fault class × scenario 의 product** 가 진짜 metric. RDMA-TB 의 `vplan/error_handling/cov_*.svh` 가 이런 cross-product 를 cov bin 으로 명시.

### 7.2 출처

**Internal (Confluence)**
- `[RDMA] Drop vs Silent drop` (id=996573316) — packet drop 분류
- `About CC` (id=976453712) — congestion control 사내 정책
- `[RDMA] WRITE` (id=989560925) — retry 시나리오
- `Mango GPUBoost™ 400G RDMA Deployment & Maintenance Guide` (id=989167742) — PFC/ECN tune
- 사내 `RDMA-TB/error_handling/VPLAN_error_handling.md` — S1~S9

**External**
- IBTA Spec 1.7, §9.7 RC service / §9.9 Retry mechanism
- IEEE 802.1Qbb — Priority-based Flow Control (PFC)
- IETF RFC 3168 — ECN
- *DCQCN: Data Center Quantized Congestion Notification* — Zhu et al., SIGCOMM 2015

---

## 다음 모듈

→ [Module 08 — RDMA-TB 검증 환경 & DV 전략](08_rdma_tb_dv.md): 지금까지 본 모든 개념이 RDMA-TB 의 어떤 컴포넌트에서 어떻게 구현되는지.

[퀴즈 풀어보기 →](quiz/07_congestion_error_quiz.md)


--8<-- "abbreviations.md"
--8<-- "_inc/topic_abbr.md"
