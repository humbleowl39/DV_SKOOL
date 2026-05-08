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
  <a class="page-toc-link" href="#왜-이-모듈이-중요한가">왜 이 모듈이 중요한가</a>
  <a class="page-toc-link" href="#핵심-개념">핵심 개념</a>
  <a class="page-toc-link" href="#1-layered-congestion-control">1. Layered Congestion Control</a>
  <a class="page-toc-link" href="#2-error-의-두-클래스">2. Error 의 두 클래스</a>
  <a class="page-toc-link" href="#3-rdma-tb-의-9-error-scenarios-s1s9">3. RDMA-TB 의 9 Error Scenarios (S1~S9)</a>
  <a class="page-toc-link" href="#4-coverage-모델-7-항목">4. Coverage 모델 — 7 항목</a>
  <a class="page-toc-link" href="#5-qp-recovery-흐름">5. QP Recovery 흐름</a>
  <a class="page-toc-link" href="#6-실무-에러-디버그-트리">6. 실무 에러 디버그 트리</a>
  <a class="page-toc-link" href="#7-congestion-검증-시나리오">7. Congestion 검증 시나리오</a>
  <a class="page-toc-link" href="#핵심-정리-key-takeaways">핵심 정리 (Key Takeaways)</a>
  <a class="page-toc-link" href="#다음-모듈">다음 모듈</a>
</div>
<!-- DV-SKOOL-CH-TOC:end -->

!!! objective "학습 목표"
    이 모듈을 마치면:

    - **Explain** Lossless Ethernet 가 RoCEv2 deployment 에서 왜 필요한지, PFC ↔ ECN ↔ DCQCN 가 어떻게 분담하는지 설명한다.
    - **Trace** Local ACK timeout, Implied NAK, RNR retry, Packet Sequence Error 의 흐름을 sender/receiver 양쪽에서 추적한다.
    - **Map** 6 가지 Remote Access Error (Access flag, MR bound, PD, R-Key, Operation, Outstanding read) 를 spec/구현 debug flag 에 매핑한다.
    - **Plan** RDMA-TB `vplan/error_handling/` 의 9 시나리오 (S1~S9) 가 각 error class 를 어떻게 커버하는지 설계 관점에서 평가한다.

!!! info "사전 지식"
    - Module 04 (QP FSM, retry_cnt, rnr_retry)
    - Module 06 (PSN, AETH syndrome, Retry timer)
    - Module 05 (Access flag, R_Key/L_Key, PD)

## 왜 이 모듈이 중요한가

**RDMA 의 검증 가치는 "행복 경로" 가 아니라 "에러 경로"** 에 있습니다. 정상 packet 만 보내면 어떤 구현이든 어느 정도 동작 — 진짜 차이는 (1) congestion 발생 시 fairness 와 throughput 회복, (2) error 발생 시 정확한 status 보고와 QP recovery 입니다. RDMA-TB 의 `error_handling` vplan 이 9 시나리오로 거의 모든 error path 를 커버하는 이유.

!!! tip "💡 이해를 위한 비유"
    **PFC + ECN + DCQCN** ≈ **고속도로 운영 3종 세트**

    - PFC = 톨게이트 일시 차단 (당장 막 안 들어오게)
    - ECN = "이 구간 막힘" 표지판 (운전자 인식)
    - DCQCN = 운전자의 속도 자율 조절 (표지판 보고 점진 감속, 풀리면 점진 가속)

    하나만 쓰면 안 됨 — PFC 만 쓰면 deadlock 위험, ECN 만 쓰면 즉각성 부족, DCQCN 은 ECN 신호가 전제.

## 핵심 개념

**Congestion 은 PFC (즉시 hop-by-hop 제어) + ECN (end-to-end 신호) + DCQCN (sender rate 조절) 의 3단 layered 메커니즘으로 처리. Error 는 (1) Transport timeout/retry 클래스 (Local ACK / PSE / Implied NAK / RNR) 와 (2) Remote Access 클래스 (Access flag / MR bound / PD / R-Key / Operation / Outstanding read) 로 나뉘며, 각각 retry exhaust 후 WC error → QP Err → Modify(Reset) 로 recovery.**

!!! danger "❓ 흔한 오해"
    **오해**: "Congestion 시 PFC PAUSE 받으면 sender 가 멈추니 packet drop 안 일어난다 → 끝."

    **실제**: PFC 만 쓰면 **deadlock + head-of-line blocking + PFC storm** 위험. 여러 priority 가 cyclic 의존을 가지면 PAUSE 가 무한 전파 가능. 그래서 PFC 는 fallback, ECN+DCQCN 이 주된 throttle 메커니즘. **검증 시 PFC 만 enabled 한 환경에서 의도적으로 cyclic traffic 을 만들어 deadlock 검출** 이 핵심 시나리오.

    **왜 헷갈리는가**: PFC 가 spec 상 "lossless 만든다" 는 표현 때문에 만능으로 보임.

---

## 1. Layered Congestion Control

```
   Time scale  ←  Fast (ns)              Slow (ms)
   ───────────  ─────────────────────────────────────
   PFC          : link-level PAUSE, hop 단위
   ECN          : packet 마킹 (CE bit)
   DCQCN        : sender rate 점진 감속/회복
```

### PFC (Priority-based Flow Control, IEEE 802.1Qbb)

```
   Switch buffer 가 차오르면 → upstream port 에 PAUSE frame 송신
   PAUSE 는 priority 별 (0..7) 독립
   Pause time 만큼 sender 는 해당 priority 송신 정지
```

- 0..7 priority class (Ethernet PCP / DSCP 매핑).
- RDMA 트래픽은 보통 priority 3 또는 26 (DSCP 26 = AF31).
- "Lossless" priority 만 PFC enable, 나머지는 일반 best-effort.

**위험**: cyclic dependency → PFC storm → deadlock. → **deadlock 회피는 routing 설계 시 deadlock-free path 보장 또는 watchdog** 필요.

### ECN (Explicit Congestion Notification, RFC 3168)

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

### DCQCN (Data Center QCN)

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

---

## 2. Error 의 두 클래스

### A. Transport / Retry 클래스 — Sender 측 timer 기반

| 에러 | 트리거 | Spec 동작 | WC status |
|------|--------|----------|-----------|
| **Local ACK timeout** | Sender 가 retry timer 안에 ACK/NAK 을 못 받음 | retry_cnt 까지 retransmit | `WC_RETRY_EXC_ERR` |
| **Packet Sequence Error (PSE)** | Responder 가 PSN > ePSN (hole) 봄 → NAK syndrome 0x80 | Sender 가 NAK 의 PSN 부터 retransmit | `WC_RETRY_EXC_ERR` |
| **Implied NAK** | Sender 가 ACK 의 PSN 이 ePSN_send 보다 큼 → 중간 ACK 분실 추정 | Sender 가 누락 부분 retransmit | `WC_RETRY_EXC_ERR` |
| **RNR (Receiver Not Ready)** | RC SEND 시 RQ 에 RECV WR 없음 → RNR NAK | RNR timer 후 retry, rnr_retry 까지 | `WC_RNR_RETRY_EXC_ERR` (별도) |

→ **모두 retry exhaust 시 QP → Err state**, sender 의 send CQ 에 WC error.

### B. Remote Access 클래스 — Responder 측 검증 fail

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

---

## 3. RDMA-TB 의 9 Error Scenarios (S1~S9)

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

---

## 4. Coverage 모델 — 7 항목

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

---

## 5. QP Recovery 흐름

```
   에러 발생
        │
        ▼
   QP → Err state (in-flight WR 모두 flush, WC error)
        │
   ◀── 사용자가 Error CQ poll, status 확인
        │
        ▼
   Modify(QP, Reset)   ── QP 를 리셋
        │
        ▼
   Modify(Init / RTR / RTS) 단계 재진입
        │
        ▼
   다시 정상 IO
```

`min_rnr_timer`, `retry_cnt`, `timeout` 등 attribute 도 새로 set 가능 — recovery 시 parameter 튜닝의 기회.

---

## 6. 실무 에러 디버그 트리

```
   WC error 발견
        │
        ├─ status?
        │
        ├─ WC_RETRY_EXC_ERR?
        │     ├─ ACK 못 받음 (Local ACK timeout)?
        │     ├─ PSN hole (PSE)?
        │     └─ ACK 의 PSN > ePSN (Implied NAK)?
        │           → 모두 retry_cnt 초과
        │
        ├─ WC_RNR_RETRY_EXC_ERR?
        │     └─ Receiver 가 RECV WR 부족 → rnr_retry_cnt 초과
        │
        ├─ WC_REM_ACCESS_ERR?
        │     ├─ debug_flag = WC_FLAG_RESP_ACCESS    (access flag)
        │     ├─ debug_flag = WC_FLAG_RESP_RANGE     (MR bound)
        │     ├─ debug_flag = WC_FLAG_RESP_PD        (PD mismatch)
        │     └─ debug_flag = WC_FLAG_RESP_RKEY      (R-Key invalid)
        │
        └─ WC_REM_INV_RD_REQ_ERR?
              └─ debug_flag = WC_FLAG_RESP_OP       (max read outstanding)
```

→ **Debug flag 만 보면 root cause 가 결정** — 검증이 잘 되면 사용자도 single-glance 디버그 가능.

---

## 7. Congestion 검증 시나리오

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

---

## 8. Confluence 보강 — PFC 의 정확한 동작과 한계

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

## 9. Confluence 보강 — Layered CC 의 사내 구성

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

## 10. Confluence 보강 — Error handling 카테고리 매핑

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

## 11. Confluence 보강 — CCMAD 와 Adaptive Routing

!!! note "Internal (Confluence: CCMAD Protocol, id=290127949; How to enable Adaptive Routing for CX, id=397967495)"
    - **CCMAD (Congestion Control MAD)**: SM (Subnet Manager) 가 CC 파라미터 (예: CCT entry, CN_ROUNDS) 를 노드에 분배할 때 사용하는 IB MAD 클래스. RoCEv2 환경에서는 CC controller 가 같은 의미를 NVMe-oF/host SW 로 대체.
    - **Adaptive Routing (CX)**: switch 가 link load 기반으로 **packet 단위 경로 선택**. RC 의 in-order 가정을 깰 수 있어, RDMA-IP 는 SACK + per-path PSN 추적을 같이 켜야 안전. 사내 검증에서는 이를 *AR mode* 라 부르고 별도 시나리오로 둠.

---

## 핵심 정리 (Key Takeaways)

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

---

## 다음 모듈

→ [Module 08 — RDMA-TB 검증 환경 & DV 전략](08_rdma_tb_dv.md)


--8<-- "abbreviations.md"
--8<-- "_inc/topic_abbr.md"
