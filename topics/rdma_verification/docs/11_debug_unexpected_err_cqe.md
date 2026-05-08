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
  <a class="page-toc-link" href="#왜-이-모듈이-중요한가">왜 이 모듈이 중요한가</a>
  <a class="page-toc-link" href="#핵심-개념">핵심 개념</a>
  <a class="page-toc-link" href="#1-에러-cqe-발생-원칙">1. 에러 CQE 발생 원칙</a>
  <a class="page-toc-link" href="#2-대표-에러-메시지">2. 대표 에러 메시지</a>
  <a class="page-toc-link" href="#3-wc_status-레퍼런스">3. wc_status 레퍼런스</a>
  <a class="page-toc-link" href="#4-에러-발생-경로">4. 에러 발생 경로</a>
  <a class="page-toc-link" href="#디버깅-단계별">디버깅 단계별</a>
  <a class="page-toc-link" href="#에러-발생-후-tb-state">에러 발생 후 TB state</a>
  <a class="page-toc-link" href="#expected-error-로-promote-하는-방법">Expected Error 로 promote 하기</a>
  <a class="page-toc-link" href="#빠른-트리아지--한-줄-결정">빠른 트리아지</a>
  <a class="page-toc-link" href="#핵심-정리">핵심 정리</a>
  <a class="page-toc-link" href="#다음-모듈">다음 모듈</a>
</div>
<!-- DV-SKOOL-CH-TOC:end -->

!!! objective "학습 목표"
    이 모듈을 마치면:

    - **Classify** 에러 CQE 의 `wc_status` 를 RETRY 계열(조건부 발생) vs 그 외(DUT 버그)로 분류할 수 있다.
    - **Justify** "RETRY_EXC 외 모든 에러 CQE 는 정상 시뮬에서 발생하면 안 된다" 원칙을 정당화할 수 있다.
    - **Promote** 의도한 에러는 `cmd.expected_error = 1` 로 promote 하여 `F-CQHDL-TBERR-0003` 를 회피할 수 있다.
    - **Trace** 에러 발생 후 TB state(QP/Outstanding/CQ폴링/Scoreboard/Sequencer)의 변화를 추적할 수 있다.

!!! info "사전 지식"
    - [RDMA Module 07 — Congestion / Error Handling](../../rdma/07_congestion_error/) (`wc_status` IBTA 정의)
    - [Module 06 — Error Handling Path](06_error_handling_path.md) (`expected_error`, `setErrState`, `enable_error_cq_poll`)
    - [Module 03 — Phase & Test Flow](03_phase_test_flow.md) (`try_once` 단발 폴링 패턴)

!!! warning "실무 주의점"
    `WC_WR_FLUSH_ERR` (5) 는 항상 **2차 영향**이다. 이 에러를 보고 그 자리부터 디버깅하면 잘못된 가설로 시간을 잃는다. 시간을 거꾸로 가서 **첫 에러 CQE** 를 찾고, 그것부터 root cause 추적을 시작해야 한다.

## 왜 이 모듈이 중요한가
RDMA-TB 의 가장 강한 invariant 중 하나: **RETRY_EXC 계열을 제외한 모든 에러 CQE 는 정상 시뮬레이션에서 발생하면 안 된다.** 발생하면 곧 DUT 버그입니다. 이 invariant 가 깨졌을 때 어떻게 분류·트리아지하는지가 이 모듈의 주제입니다.

> Confluence 출처: [Unexpected Error CQE](https://mangoboost.atlassian.net/wiki/spaces/RDMADV/pages/1335099464/Unexpected+Error+CQE)

## 핵심 개념

### 1. 에러 CQE 발생 원칙

| 분류 | 에러 코드 | 정상 발생 가능 | 설명 |
|------|---------|--------------|-----|
| **조건부 발생 가능** | `WC_RETRY_EXC_ERR` (12) | O | HW 내부 리소스 부족 / 처리 성능 부족으로 패킷 드롭 → 재전송 한도 초과 |
| **조건부 발생 가능** | `WC_RNR_RETRY_EXC_ERR` (13) | O | HW 내부 리소스 부족으로 Recv 처리 지연 |
| **절대 발생 불가** | 그 외 모든 에러 | X | 발생 시 DUT 버그 — TB 설정이 올바르다면 DUT 내부 문제 |

🔑 RETRY_EXC 계열은 DUT 의 **성능 한계** 신호입니다. 트래픽 부하 / 동시성을 조절하면 회피 가능.

### 2. 대표 에러 메시지

| ID | 심각도 | 메시지 | 코드 위치 |
|----|--------|-------|---------|
| `F-CQHDL-TBERR-0003` | FATAL | `Unexpected Error Handler: <cqe.sprint()>` | `vrdma_cq_handler.svh:244` |

발생 조건 (둘 다 충족):
- `cqe.wc_status != IB_WC_SUCCESS` (에러 CQE)
- `cmd.expected_error == 0` (예상하지 않음)

### 3. wc_status 레퍼런스

#### RETRY 계열 (조건부 발생)
| 값 | 이름 | 의미 | 원인 |
|----|------|-----|-----|
| 12 | `WC_RETRY_EXC_ERR` | 재시도 횟수 초과 | HW 리소스 부족 → 패킷 드롭 → retry 한도 초과 |
| 13 | `WC_RNR_RETRY_EXC_ERR` | RNR 재시도 초과 | HW 리소스 부족 → Recv WQE 처리 지연 |

#### 나머지 (DUT 버그)
| 값 | 이름 | 의미 | DUT 버그 유형 |
|----|------|-----|--------------|
| 1 | `WC_LOC_LEN_ERR` | 로컬 길이 에러 | DUT SGE 처리 로직 |
| 2 | `WC_LOC_QP_OP_ERR` | QP 상태 머신 에러 | DUT QP FSM 잘못된 상태 |
| 4 | `WC_LOC_PROT_ERR` | 로컬 보호 에러 | DUT lkey 검증 |
| 5 | `WC_WR_FLUSH_ERR` | WQE flush | 선행 에러의 2차 영향 — 선행 에러부터 추적 |
| 8 | `WC_LOC_ACCESS_ERR` | 로컬 접근 에러 | DUT MR 접근 권한 체크 |
| 9 | `WC_REM_INV_REQ_ERR` | 리모트 잘못된 요청 | DUT 가 잘못된 요청 패킷 생성 |
| 10 | `WC_REM_ACCESS_ERR` | 리모트 접근 에러 | DUT rkey 검증 또는 MR 경계 체크 |
| 11 | `WC_REM_OP_ERR` | 리모트 operation 에러 | DUT Responder 처리 로직 |
| 19 | `WC_FATAL_ERR` | DUT 내부 fatal | DUT assertion 또는 복구 불가 |
| 20 | `WC_RESP_TIMEOUT_ERR` | 응답 타임아웃 | DUT ACK 생성 로직 |
| 0xBF | `WC_BF_FATAL_ERR` | HW fatal | HW 레벨 복구 불가 |

### 4. 에러 발생 경로

#### 경로 A — 데이터 CQ 에서 발견
1. driver 가 cq polling 진행
2. cq_handler 가 CQE decode → `wc_status != SUCCESS`
3. `cmd.expected_error == 0` → `F-CQHDL-TBERR-0003`

#### 경로 B — Error CQ 백그라운드 모니터에서 발견
1. `vrdma_cq_handler::enable_error_cq_poll = 1` (default)
2. `monitorErrCQ` 백그라운드 task 가 ERR_CQ 폴링
3. ERR_CQ 에 에러 CQE 도착 → 동일 경로

## 디버깅 단계별

### Step 1 — `wc_status` 로 에러 분류
- RETRY 계열인가? → Step 2A
- 그 외? → Step 2B

### Step 2A — RETRY_EXC: HW 리소스/성능 디버깅
1. **트래픽 부하 확인** — 동시 발행 outstanding WQE 수, MTU 대비 burst size
2. **DUT 내부 큐/버퍼** — 어느 단계에서 drop 이 발생했나
3. **타이밍** — RNR timeout, retry count 설정값
4. **대응** — 동시성 줄이기, retry / RNR timeout 늘리기

> 관련 cfg: `lib/ext/test/error_handling/vrdmatb_error_handling_test_lib.svh:14-19` 의 `timeout`, `retry_cnt`, `rnr_retry_exceed_en`, `min_rnr_timeout`

### Step 2B — 나머지 에러: DUT 버그 디버깅
이 에러들은 TB 설정이 올바르다면 DUT 내부 문제입니다.

`wc_status` 별 우선 의심:

| 값 | 의심 위치 |
|----|---------|
| 1 (LEN_ERR) | DUT SGE 처리, transfer_size 누적 |
| 2 (QP_OP_ERR) | DUT QP FSM (Reset/Init/RTR/RTS/SQErr/Err) 전이 |
| 4 (LOC_PROT_ERR) | DUT lkey 검증, MR access perm |
| 5 (FLUSH_ERR) | 이 에러가 first 가 아님 — 시간 거꾸로 가서 선행 에러 찾기 |
| 8 (LOC_ACCESS_ERR) | DUT MR 경계 체크, page table walk |
| 10 (REM_ACCESS_ERR) | Remote 의 rkey 검증 또는 MR 경계 |

### Step 3 — 시퀀스 로직 확인 (TB 설정 오류 배제)
- WQE 의 lkey/rkey 가 올바른 MR 인가?
- iova / length 가 MR 범위 내인가?
- QP 의 peer_qp 가 올바른 destination 인가?
- TB cfg 가 의도한 시나리오를 만들었나?

이 단계에서 TB 버그가 잡히면 DUT 버그가 아닙니다.

## 에러 발생 후 TB state

| 항목 | 동작 |
|------|-----|
| QP 상태 | `setErrState(1)` → 이후 모든 command skip (`vrdma_cq_handler.svh:223`) |
| Outstanding WQE | 전체 flush (`completeOutstanding` 호출) |
| CQ 폴링 | `cmd.error_occured = 1` → 루프 즉시 종료 (`vrdma_cq_handler.svh:217`) |
| Scoreboard | 에러 CQE 는 `cqe_ap` 로 전달되지 않음 (validation checker 에만) |
| Sequencer | `wc_error_status[qp]`, `debug_wc_flag[qp]` 에 기록 |

이 chained 정리 메커니즘이 [Module 06](06_error_handling_path.md) 의 ErrQP 게이트.

## Expected Error 로 promote 하는 방법

에러가 의도된 테스트 시나리오라면:

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

## 빠른 트리아지 — 한 줄 결정

| `wc_status` | 첫 가설 |
|------------|--------|
| 12 / 13 (RETRY) | 트래픽 부하 — DUT 성능 한계 (DUT 버그 아님) |
| 5 (FLUSH) | 이 cqe 의 시간 직전을 봐 — 선행 에러부터 |
| 4 / 8 (LOC_PROT/ACCESS) | TB 가 잘못된 lkey 또는 잘못된 length 발행 안했는지 먼저 확인 |
| 10 (REM_ACCESS) | Remote 의 rkey 또는 MR 경계 — 둘 다 정상이면 DUT |
| 2 (QP_OP) | QP 가 wrong state 에서 verb 받음 — destroy 후 verb 발행 등 시퀀스 오류 가능 |
| 19 (FATAL) / 0xBF | DUT 내부 fatal — fsdb 에서 DUT assertion 추적 |

## 핵심 정리

- RETRY_EXC / RNR_RETRY_EXC_ERR 외 모든 에러 CQE = DUT 버그 의심
- 의도된 에러는 per-cmd `expected_error=1` 로 promote
- 에러 발생 시 QP→Outstanding→CQ폴링→Scoreboard→Sequencer 가 chained 정리 (Module 06)
- `WC_WR_FLUSH_ERR` (5) 는 항상 2차 영향 — 시간 거꾸로 가서 선행 에러부터 디버깅

## 다음 모듈
[Module 12 — Debug Cheatsheet](12_debug_cheatsheet.md): 4개 케이스의 통합 cheatsheet.

[퀴즈 풀어보기 →](quiz/11_debug_unexpected_err_cqe_quiz.md)


--8<-- "abbreviations.md"
