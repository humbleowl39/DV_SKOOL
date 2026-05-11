# Module 11 — Debug Case 4: Unexpected Error CQE

<!-- DV-SKOOL-CH-CTX:start -->
<div class="chapter-context" data-cat="network">
  <a class="chapter-back" href="../">
    <span class="chapter-back-arrow">←</span>
    <span class="chapter-back-icon">🧪</span>
    <span class="chapter-back-text">RDMA Verification</span>
  </a>
  <span class="chapter-divider">›</span>
  <span class="chapter-marker">Module 11</span>
</div>
<!-- DV-SKOOL-CH-CTX:end -->

<!-- DV-SKOOL-CH-TOC:start -->
<div class="page-toc">
  <span class="page-toc-label">목차</span>
  <a class="page-toc-link" href="#1-why-care-이-모듈이-왜-필요한가">1. Why care?</a>
  <a class="page-toc-link" href="#2-intuition-경보등의-두-색-진짜-경보-vs-성능-경고">2. Intuition</a>
  <a class="page-toc-link" href="#3-작은-예-실제-fail-log--wc_status--root-cause-까지">3. 작은 예 — fail log → root cause</a>
  <a class="page-toc-link" href="#4-일반화-2-분기--디버그-3-단계">4. 일반화 — 2 분기 + 3 단계</a>
  <a class="page-toc-link" href="#5-디테일-wc_status-원칙-에러-경로-tb-state-promote-패턴">5. 디테일</a>
  <a class="page-toc-link" href="#6-흔한-오해-와-dv-디버그-체크리스트">6. 흔한 오해 + DV 디버그 체크리스트</a>
  <a class="page-toc-link" href="#7-핵심-정리-key-takeaways">7. 핵심 정리</a>
</div>
<!-- DV-SKOOL-CH-TOC:end -->

!!! objective "학습 목표"
    이 모듈을 마치면:

    - **Classify** 에러 CQE 의 `wc_status` 를 RETRY 계열 (조건부 발생) vs 그 외 (DUT 버그) 로 분류할 수 있다.
    - **Justify** "RETRY_EXC 외 모든 에러 CQE 는 정상 시뮬에서 발생하면 안 된다" invariant 를 정당화할 수 있다.
    - **Apply** 의도된 에러는 `cmd.expected_error = 1` 로 promote 해 `F-CQHDL-TBERR-0003` 를 회피할 수 있다.
    - **Trace** 에러 발생 후 TB state (QP / Outstanding / CQ 폴링 / Scoreboard / Sequencer) 의 chained 정리를 추적할 수 있다.

!!! info "사전 지식"
    - [RDMA Module 07 — Congestion / Error Handling](../../rdma/07_congestion_error/) (`wc_status` IBTA 정의)
    - [Module 06 — Error Handling Path](06_error_handling_path.md) (`expected_error`, `setErrState`, `enable_error_cq_poll`)
    - [Module 03 — Phase & Test Flow](03_phase_test_flow.md) (`try_once` 단발 폴링 패턴)

!!! warning "실무 주의점"
    `WC_WR_FLUSH_ERR` (5) 는 항상 **2 차 영향** 입니다. 이 에러를 보고 그 자리부터 디버깅하면 잘못된 가설로 시간을 잃습니다. 시간을 거꾸로 가서 **첫 에러 CQE** 를 찾고, 그것부터 root cause 추적을 시작해야 합니다.

---

## 1. Why care? — 이 모듈이 왜 필요한가

RDMA-TB 의 가장 강한 invariant 중 하나는 **"RETRY_EXC 계열을 제외한 모든 에러 CQE 는 정상 시뮬레이션에서 발생하면 안 된다"** 입니다. 이 invariant 가 깨지면 곧 DUT 버그이거나 TB 시퀀스가 잘못된 lkey/rkey/length 를 발행한 것 — 어느 쪽이든 **사람의 결정** 이 필요합니다. 그래서 TB 는 `F-CQHDL-TBERR-0003` 으로 fatal 을 띄워 시뮬을 멈춥니다.

이 모듈을 건너뛰면 에러 CQE 가 떴을 때 (a) DUT 버그인지 (b) TB 시퀀스 오류인지 (c) 의도된 에러를 promote 누락한 것인지 — 세 가설을 매번 헷갈리게 됩니다. `wc_status` 의 2-분기 (RETRY vs 그 외) 와 `expected_error=1` promote 패턴을 외우면 5 분 안에 트리아지가 끝납니다.

> Confluence 출처: [Unexpected Error CQE](https://mangoboost.atlassian.net/wiki/spaces/RDMADV/pages/1335099464/Unexpected+Error+CQE)

---

## 2. Intuition — 경보등의 두 색 (진짜 경보 vs 성능 경고)

!!! tip "💡 한 줄 비유"
    에러 CQE = **공장 라인의 경보등**. 빨간 (RETRY_EXC) 은 _과부하 → 자동 retry → 한도 초과_ 신호 — 라인을 천천히 돌리면 사라짐 (DUT 성능 한계, 버그 아님). 파란 (그 외 모든 status) 은 _기계 자체 고장_ 신호 — 라인을 멈추고 사람이 봐야 함. TB 는 파란 등 = `F-CQHDL-TBERR-0003` fatal 로 자동 멈춤. 의도된 빨간/파란 등이라면 _사전에_ "이 라인에서는 켜질 수 있음" 으로 등록 (`expected_error=1`).

### 한 장 그림 — 에러 CQE 의 두 분기

```
                        DUT 가 CQ 또는 ERR_CQ 에 CQE 기록
                                  │
                                  ▼
                ┌──── vrdma_cq_handler 가 CQE decode ──────┐
                │                                          │
                │   cqe.wc_status == IB_WC_SUCCESS ?       │
                │       YES                                │
                │       └─→ 정상 처리, scoreboard 로       │
                │                                          │
                │       NO  (에러 CQE)                      │
                │       │                                  │
                │       ▼                                  │
                │   cmd.expected_error == 1 ?              │
                │       YES                                │
                │       └─→ 의도된 에러 — 통과 (promote)   │
                │                                          │
                │       NO                                 │
                │       │                                  │
                │       ▼                                  │
                │   wc_status 분류                          │
                │       │                                  │
                │     RETRY_EXC / RNR_RETRY_EXC?           │
                │       YES                                │
                │       └─→ 성능 한계 — 트래픽 부하 조절   │
                │           (조건부 발생 가능)              │
                │                                          │
                │       NO                                 │
                │       └─→ F-CQHDL-TBERR-0003 (FATAL)     │
                │           DUT 버그 또는 TB 시퀀스 오류   │
                │                                          │
                │   에러 발생 시 chained 정리:              │
                │   ─ QP: setErrState(1)                   │
                │   ─ Outstanding: flush                   │
                │   ─ CQ 폴링: error_occured=1 종료        │
                │   ─ Sequencer: wc_error_status 기록      │
                └──────────────────────────────────────────┘
```

### 왜 이 디자인인가 — Design rationale

세 가지가 동시에 풀려야 했습니다.

1. **에러 CQE 두 종류의 의미 차이** — RETRY_EXC 는 _DUT 의 성능 한계 / 부하_ 신호 (정상 시뮬에서도 부하가 높으면 발생 가능), 그 외는 _버그_ 신호 (정상 시뮬에서 절대 안 됨) → 한쪽만 fatal.
2. **의도된 에러 시나리오** — error injection 테스트는 일부러 에러 CQE 를 만들어 DUT 의 에러 처리 로직을 검증 → per-cmd `expected_error=1` 게이트로 promote.
3. **에러 발생 직후 cascade 차단** — 한 QP 가 에러 나면 그 QP 의 후속 outstanding WQE 도 줄줄이 실패 → chained 정리 (QP/Outstanding/CQ 폴링/Sequencer) 로 한 번에 멈춤.

이 세 요구의 교집합이 RETRY 2-분기 + `expected_error` promote + chained 정리입니다.

---

## 3. 작은 예 — 실제 fail log → `wc_status` → root cause 까지

### Fail log

```
[F-CQHDL-TBERR-0003] Unexpected Error Handler:
  CQE: qp_num=0x07, opcode=RDMA_READ, wc_status=10 (WC_REM_ACCESS_ERR),
       byte_len=0, src_qp=0x05, vendor_err=0x00
  cmd: qp_num=0x07, opcode=RDMA_READ, rkey=0x12345678,
       remote_addr=0x9000_0040, length=0x40, expected_error=0
  vrdma_cq_handler.svh:244
```

### Step-by-step root cause

```
   Step 1   에러 ID = F-CQHDL-TBERR-0003 → Unexpected Error CQE
            wc_status = 10 (WC_REM_ACCESS_ERR)
              ▶ remote 측 rkey 검증 실패 또는 MR 경계 위반

   Step 2   wc_status 분류 — RETRY 계열인가?
            ─────────────────────────────────────────
            wc_status = 10 != {12, 13}
              ▶ RETRY 계열 아님 → DUT 버그 or TB 시퀀스 오류
              ▶ 다음: TB 시퀀스 확인부터 (배제 절차)

   Step 3   TB 시퀀스 정합성 확인
            ─────────────────────────────────────────
            cmd.rkey = 0x12345678, remote_addr = 0x9000_0040, length = 0x40
              ▶ 시퀀스 코드 grep: assert(read_cmd.randomize() with { ... })
              ▶ rkey 0x12345678 가 remote 노드의 어느 MR rkey 인지 확인
                  → m_mr_table[remote_node] dump
                  → 0x12345678 = MR_3 (base=0x9000_0000, len=0x1000)
              ▶ remote_addr (0x9000_0040) 가 MR_3 범위 내인가?
                  → MR_3 끝 = 0x9000_1000, 0x9000_0040 < 끝 → 범위 내 OK
              ▶ TB 시퀀스 정상 → DUT 버그 의심으로 진행

   Step 4   DUT 측 rkey 검증 로직 추적
            ─────────────────────────────────────────
            fsdb 에서 DUT 의 RX RDMA READ 처리:
              ▶ RETH.RKey = 0x12345678 받음 OK
              ▶ DUT 의 MR table lookup → 0x12345678 매칭 OK
              ▶ DUT 의 access flag 검사 → IBV_ACCESS_REMOTE_READ 비트 == 0 !
              ▶ root cause: DUT 가 RDMA_READ verb 인데도
                            local-only MR (REMOTE_READ flag 꺼짐) 에 접근 시도
                            → REM_ACCESS_ERR 정당

   Step 5   진짜 원인은 TB cfg
            ─────────────────────────────────────────
            MR_3 의 access flag 가 testcase cfg 에서
              IBV_ACCESS_LOCAL_WRITE 만 켜져 있고 REMOTE_READ 가 빠짐
              ▶ root cause: TB cfg 의 MR access flag 누락
              ▶ fix: REMOTE_READ 추가 → 에러 사라짐
              ▶ (이 케이스는 DUT 버그가 아니라 TB cfg 오류 — Step 3 에서 그냥
                  cmd.rkey 만 보면 놓치고, MR access flag 까지 봐야 잡힘)
```

### 단계별 의미

| Step | 보는 것 | 발견 | 가설 |
|---|---|---|---|
| 1 | fatal log | wc_status=10 (REM_ACCESS) | remote MR/rkey 위반 |
| 2 | RETRY 분류 | RETRY 아님 | DUT 버그 or TB 시퀀스 |
| 3 | TB 시퀀스 정합성 | rkey + addr 모두 정상 | DUT 의심 |
| 4 | DUT rkey 검증 fsdb | access flag REMOTE_READ=0 | DUT 거부 정당 |
| 5 | TB MR cfg | REMOTE_READ 누락 | TB cfg 누락 |

!!! note "여기서 잡아야 할 두 가지"
    **(1) RETRY 계열 배제가 항상 첫 분기** — `wc_status` 가 12/13 인지부터. RETRY 면 DUT 부하 / 성능 이슈, 디버그 방향이 완전히 다름.<br>
    **(2) "DUT 버그 의심" 결론을 내기 전 반드시 TB 시퀀스 + cfg 까지 확인** — §3 의 worked example 처럼 root cause 가 TB cfg 일 때, DUT fsdb 만 파면 무한 루프. cmd.rkey → MR table → access flag → 길이 순서로 일관성 체크.

---

## 4. 일반화 — 2 분기 + 디버그 3 단계

### 4.1 에러 CQE 의 2 분기

```
   wc_status ?
        │
        ├─ 12 WC_RETRY_EXC_ERR / 13 WC_RNR_RETRY_EXC_ERR
        │       └─→ 조건부 발생 가능 (DUT 성능 한계)
        │            ─ 동시 outstanding WQE 수 줄이기
        │            ─ MTU / burst 조절
        │            ─ retry / RNR timeout 늘리기
        │            ─ (DUT 버그 아님)
        │
        └─ 그 외 (1/2/4/5/8/9/10/11/19/20/0xBF …)
                └─→ 절대 발생 불가
                     1. TB 시퀀스 + cfg 정합성 먼저 (배제)
                     2. 정상이면 DUT 버그 추적
                     3. WC_WR_FLUSH_ERR (5) 는 항상 2차 — 시간 거꾸로
```

### 4.2 디버그 3 단계

| Step | 무엇을 보나 | 어디 |
|---|---|---|
| 1 | `wc_status` 분류 (RETRY vs 그 외) | `F-CQHDL-TBERR-0003` 의 CQE dump |
| 2 | RETRY → 부하 디버그 / 그 외 → TB 시퀀스 + cfg 정합성 | TB cfg + sequence code |
| 3 | TB 정상이면 DUT 버그 추적 (fsdb) | DUT 의 해당 wc_status 책임 모듈 |

---

## 5. 디테일 — `wc_status` 원칙, 에러 경로, TB state, promote 패턴

### 5.1 에러 CQE 발생 원칙

| 분류 | 에러 코드 | 정상 발생 가능 | 설명 |
|------|---------|--------------|-----|
| **조건부 발생 가능** | `WC_RETRY_EXC_ERR` (12) | O | HW 내부 리소스 부족 / 처리 성능 부족으로 패킷 드롭 → 재전송 한도 초과 |
| **조건부 발생 가능** | `WC_RNR_RETRY_EXC_ERR` (13) | O | HW 내부 리소스 부족으로 Recv 처리 지연 |
| **절대 발생 불가** | 그 외 모든 에러 | X | 발생 시 DUT 버그 또는 TB 시퀀스 오류 — 정상 시뮬에서 절대 발생 안 함 |

🔑 RETRY_EXC 계열은 DUT 의 **성능 한계** 신호입니다. 트래픽 부하 / 동시성을 조절하면 회피 가능.

### 5.2 대표 에러 메시지

| ID | 심각도 | 메시지 | 코드 위치 |
|----|--------|-------|---------|
| `F-CQHDL-TBERR-0003` | FATAL | `Unexpected Error Handler: <cqe.sprint()>` | `vrdma_cq_handler.svh:244` |

발생 조건 (둘 다 충족):

- `cqe.wc_status != IB_WC_SUCCESS` (에러 CQE)
- `cmd.expected_error == 0` (예상하지 않음)

### 5.3 `wc_status` 레퍼런스

#### RETRY 계열 (조건부 발생)

| 값 | 이름 | 의미 | 원인 |
|----|------|-----|-----|
| 12 | `WC_RETRY_EXC_ERR` | 재시도 횟수 초과 | HW 리소스 부족 → 패킷 드롭 → retry 한도 초과 |
| 13 | `WC_RNR_RETRY_EXC_ERR` | RNR 재시도 초과 | HW 리소스 부족 → Recv WQE 처리 지연 |

#### 나머지 (DUT 버그 또는 TB 시퀀스 오류)

| 값 | 이름 | 의미 | 의심 위치 |
|----|------|-----|--------------|
| 1 | `WC_LOC_LEN_ERR` | 로컬 길이 에러 | DUT SGE 처리 / TB 의 transfer_size |
| 2 | `WC_LOC_QP_OP_ERR` | QP 상태 머신 에러 | DUT QP FSM / TB 의 verb 시퀀스 (destroy 후 발행 등) |
| 4 | `WC_LOC_PROT_ERR` | 로컬 보호 에러 | DUT lkey 검증 / TB 의 lkey 설정 |
| 5 | `WC_WR_FLUSH_ERR` | WQE flush | 선행 에러의 2 차 영향 — 선행 에러부터 추적 |
| 8 | `WC_LOC_ACCESS_ERR` | 로컬 접근 에러 | DUT MR 경계 체크 / TB 의 length 범위 |
| 9 | `WC_REM_INV_REQ_ERR` | 리모트 잘못된 요청 | DUT 가 잘못된 요청 패킷 생성 |
| 10 | `WC_REM_ACCESS_ERR` | 리모트 접근 에러 | DUT rkey 검증 / TB 의 remote MR access flag |
| 11 | `WC_REM_OP_ERR` | 리모트 operation 에러 | DUT Responder 처리 로직 |
| 19 | `WC_FATAL_ERR` | DUT 내부 fatal | DUT assertion 또는 복구 불가 |
| 20 | `WC_RESP_TIMEOUT_ERR` | 응답 타임아웃 | DUT ACK 생성 로직 |
| 0xBF | `WC_BF_FATAL_ERR` | HW fatal | HW 레벨 복구 불가 |

### 5.4 에러 발생 경로

#### 경로 A — 데이터 CQ 에서 발견

1. driver 가 cq polling 진행
2. cq_handler 가 CQE decode → `wc_status != SUCCESS`
3. `cmd.expected_error == 0` → `F-CQHDL-TBERR-0003`

#### 경로 B — Error CQ 백그라운드 모니터에서 발견

1. `vrdma_cq_handler::enable_error_cq_poll = 1` (default)
2. `monitorErrCQ` 백그라운드 task 가 ERR_CQ 폴링
3. ERR_CQ 에 에러 CQE 도착 → 동일 경로

### 5.5 디버깅 단계별 — 자세히

#### Step 1 — `wc_status` 로 에러 분류

- RETRY 계열 (12, 13) 인가? → Step 2A
- 그 외? → Step 2B

#### Step 2A — RETRY_EXC: HW 리소스 / 성능 디버깅

1. **트래픽 부하 확인** — 동시 발행 outstanding WQE 수, MTU 대비 burst size
2. **DUT 내부 큐 / 버퍼** — 어느 단계에서 drop 이 발생했나
3. **타이밍** — RNR timeout, retry count 설정값
4. **대응** — 동시성 줄이기, retry / RNR timeout 늘리기

> 관련 cfg: `lib/ext/test/error_handling/vrdmatb_error_handling_test_lib.svh:14-19` 의 `timeout`, `retry_cnt`, `rnr_retry_exceed_en`, `min_rnr_timeout`

#### Step 2B — 나머지 에러: TB 시퀀스 / cfg 정합성부터

먼저 _배제 절차_ 로 TB 측 오류를 제거합니다 (§3 의 worked example 이 이 케이스):

- WQE 의 lkey/rkey 가 올바른 MR 인가?
- iova / length 가 MR 범위 내인가?
- MR 의 access flag (LOCAL_WRITE / REMOTE_READ / REMOTE_WRITE / REMOTE_ATOMIC) 가 verb 와 일치?
- QP 의 peer_qp 가 올바른 destination 인가?
- TB cfg 가 의도한 시나리오를 만들었나?

이 단계에서 TB 오류가 잡히면 DUT 버그가 아닙니다.

#### Step 3 — DUT 측 추적 (TB 정상이라면)

`wc_status` 별 우선 의심:

| 값 | 의심 위치 |
|----|---------|
| 1 (LEN_ERR) | DUT SGE 처리, transfer_size 누적 |
| 2 (QP_OP_ERR) | DUT QP FSM (Reset/Init/RTR/RTS/SQErr/Err) 전이 |
| 4 (LOC_PROT_ERR) | DUT lkey 검증, MR access perm |
| 5 (FLUSH_ERR) | 이 에러가 first 가 아님 — 시간 거꾸로 가서 선행 에러 찾기 |
| 8 (LOC_ACCESS_ERR) | DUT MR 경계 체크, page table walk |
| 10 (REM_ACCESS_ERR) | Remote 의 rkey 검증 또는 MR 경계 |

### 5.6 에러 발생 후 TB state

| 항목 | 동작 |
|------|-----|
| QP 상태 | `setErrState(1)` → 이후 모든 command skip (`vrdma_cq_handler.svh:223`) |
| Outstanding WQE | 전체 flush (`completeOutstanding` 호출) |
| CQ 폴링 | `cmd.error_occured = 1` → 루프 즉시 종료 (`vrdma_cq_handler.svh:217`) |
| Scoreboard | 에러 CQE 는 `cqe_ap` 로 전달되지 않음 (validation checker 에만) |
| Sequencer | `wc_error_status[qp]`, `debug_wc_flag[qp]` 에 기록 |

이 chained 정리 메커니즘이 [Module 06](06_error_handling_path.md) 의 ErrQP 게이트.

### 5.7 Expected Error 로 promote 하는 방법

에러가 의도된 테스트 시나리오라면 — error injection 테스트는 일부러 잘못된 rkey / length / state 로 에러 CQE 를 만들어 DUT 의 에러 처리 로직을 검증합니다. 이때 `expected_error=1` 로 promote 하지 않으면 매 에러 CQE 마다 `F-CQHDL-TBERR-0003` 으로 시뮬이 죽습니다.

```systemverilog
class err_inject_seq extends vrdma_top_sequence;
  task body();
    // 1. 정상 등록
    this.RDMAQPCreate(.t_seqr(seqr), .qp_num(qp_num));
    this.RDMAMRRegister(.t_seqr(seqr), .mr_id(mr_id));

    // 2. 에러 expected verb
    vrdma_read_command read_cmd = ...;
    read_cmd.expected_error = 1; // ← per-cmd gate
    this.start_item(read_cmd, .sequencer(t_seqr));
    assert(read_cmd.randomize() with {
      qp_num   == qp_num;
      rkey     == bad_key;       // 의도된 잘못된 rkey
    });
    this.finish_item(read_cmd);

    // 3. CQ 폴링 (단발 — try_once)
    this.RDMACQPoll(.t_seqr(seqr), .cq_num(cq_num), .try_once(1));

    // 4. 에러 발생 검증
    if(t_seqr.wc_error_status[qp_num].size() > 0) begin
      RDMAWCStatus_t status = t_seqr.wc_error_status[qp_num][0];
      // 예: WC_REM_ACCESS_ERR 가 와야 함
    end

    // 5. 에러 QP 정리
    this.RDMAQPDestroy(.t_seqr(seqr), .qp_num(qp_num), .err(1));
    t_seqr.clearErrorStatus(qp_num);
  endtask
endclass
```

### 5.8 빠른 트리아지 — 한 줄 결정

| `wc_status` | 첫 가설 |
|------------|--------|
| 12 / 13 (RETRY) | 트래픽 부하 — DUT 성능 한계 (DUT 버그 아님) |
| 5 (FLUSH) | 이 cqe 의 시간 직전을 봐 — 선행 에러부터 |
| 4 / 8 (LOC_PROT / ACCESS) | TB 가 잘못된 lkey 또는 잘못된 length 발행 안했는지 먼저 확인 |
| 10 (REM_ACCESS) | Remote 의 rkey 또는 MR 경계 (access flag 포함) — 둘 다 정상이면 DUT |
| 2 (QP_OP) | QP 가 wrong state 에서 verb 받음 — destroy 후 verb 발행 등 시퀀스 오류 가능 |
| 19 (FATAL) / 0xBF | DUT 내부 fatal — fsdb 에서 DUT assertion 추적 |

---

## 6. 흔한 오해 와 DV 디버그 체크리스트

### 흔한 오해

!!! danger "❓ 오해 1 — '에러 CQE 떴으니 무조건 DUT 버그'"
    **실제**: 두 가지 분기를 먼저 해야. (1) RETRY 계열 (12/13) 이면 DUT 의 성능 한계 — 버그 아님. (2) RETRY 아니라도 TB 시퀀스 / cfg 오류 (잘못된 lkey, MR access flag 누락, QP 상태 위반) 가 더 흔함. §3 의 worked example 이 정확히 이 케이스 (TB MR cfg 가 root cause).<br>
    **왜 헷갈리는가**: fatal 메시지가 "Unexpected" 라 DUT 책임으로 들림.

!!! danger "❓ 오해 2 — '`WC_WR_FLUSH_ERR` (5) 도 그 시점이 root cause'"
    **실제**: FLUSH 는 항상 **2 차 영향** — 같은 QP 의 _선행_ 에러 (예: WC_REM_ACCESS_ERR) 가 setErrState 를 트리거하면 outstanding 의 모든 후속 WQE 가 FLUSH 로 마감됨. FLUSH 의 시점은 cleanup 의 시점이지 root cause 의 시점이 아님. 시간 거꾸로 가서 첫 non-FLUSH 에러를 찾아야.<br>
    **왜 헷갈리는가**: 가장 마지막에 보이는 에러라 가장 최근으로 오인.

!!! danger "❓ 오해 3 — '`expected_error=1` 을 시퀀스 전체에 걸어두면 안전'"
    **실제**: `expected_error` 는 _per-cmd_ 게이트. 의도된 에러 verb 1 개에만 켜고, 후속 정상 verb 에는 꺼야. 전체에 켜두면 진짜 DUT 버그도 silently 통과 — 가장 위험한 false-negative.

!!! danger "❓ 오해 4 — 'ERR_CQ 에 안 떨어지면 에러 아님'"
    **실제**: 에러 CQE 는 _데이터 CQ_ 에도 떨어질 수 있음 (경로 A). DUT 구현에 따라 다름. `enable_error_cq_poll=1` 이라도 두 경로 모두 감시. monitorErrCQ 만 보면 데이터 CQ 의 에러 CQE 누락.

!!! danger "❓ 오해 5 — 'RETRY_EXC 가 떴으니 그냥 retry 늘리면 됨'"
    **실제**: RETRY 가 _계속_ 떨어지면 DUT 의 처리량이 부하를 못 따라가는 본질적 문제. retry 만 늘리면 latency 가 늘 뿐 throughput 은 그대로. 동시 outstanding WQE 수 / MTU / burst size 를 조절해야 근본 해소.

### DV 디버그 체크리스트

| 증상 | 1차 의심 | 어디 보나 |
|---|---|---|
| `F-CQHDL-TBERR-0003` (wc_status=12/13) | DUT 성능 한계 / 부하 | outstanding 수, MTU/burst, retry/RNR timeout |
| `F-CQHDL-TBERR-0003` (wc_status=4/8 LOC_PROT/ACCESS) | TB 의 lkey / length 오류 가능 | cmd.lkey vs MR table, length vs MR.len |
| `F-CQHDL-TBERR-0003` (wc_status=10 REM_ACCESS) | Remote MR access flag 누락 가능 | MR cfg 의 REMOTE_READ/WRITE/ATOMIC bit |
| `F-CQHDL-TBERR-0003` (wc_status=2 QP_OP_ERR) | TB 가 destroy 후 verb 발행 | sequence 의 verb 시점 vs QP destroy 시점 |
| `F-CQHDL-TBERR-0003` (wc_status=5 FLUSH) | 시점 직전의 선행 에러 | 시간 거꾸로 grep `wc_status` |
| `F-CQHDL-TBERR-0003` (wc_status=19/0xBF FATAL) | DUT 내부 assertion | DUT log + fsdb assertion |
| 의도된 에러 시나리오 중인데 fatal | `expected_error=1` promote 누락 | sequence 의 해당 verb 직전 `read_cmd.expected_error = 1` |
| 에러 CQE 가 안 잡힘 | enable_error_cq_poll=0 또는 경로 A 미감시 | M06 의 cq_handler flag |

---

## 7. 핵심 정리 (Key Takeaways)

- 에러 CQE 의 2-분기: RETRY (12/13) = 성능 한계, 그 외 = DUT 버그 또는 TB 시퀀스 오류.
- RETRY 아니라도 DUT 버그 결론 전 **반드시** TB cfg / 시퀀스 정합성부터 (lkey, MR access flag, length, QP state).
- `WC_WR_FLUSH_ERR` (5) 는 항상 2 차 — 시간 거꾸로 가서 선행 에러부터.
- 의도된 에러는 per-cmd `expected_error=1` 로 promote — 시퀀스 전체에 걸지 말 것.
- 에러 발생 시 QP→Outstanding→CQ 폴링→Scoreboard→Sequencer 가 chained 정리 (Module 06).

!!! warning "실무 주의점"
    - `expected_error=1` 은 per-cmd 게이트 — 전체 시퀀스에 걸면 진짜 DUT 버그를 silently 통과 (가장 위험한 false-negative).
    - RETRY 가 반복되면 retry 만 늘리지 말고 동시 outstanding / MTU / burst 부터 조절.
    - 에러 CQE 는 데이터 CQ 와 ERR_CQ 양쪽에 떨어질 수 있음 — `enable_error_cq_poll=1` 외에 데이터 CQ 도 감시 필요.

---

## 다음 모듈

→ [Module 12 — Debug Cheatsheet](12_debug_cheatsheet.md): 4 개 디버그 케이스 (M08–M11) 의 통합 cheatsheet — 에러 ID → 모듈 → 첫 액션.

[퀴즈 풀어보기 →](quiz/11_debug_unexpected_err_cqe_quiz.md)


--8<-- "abbreviations.md"
