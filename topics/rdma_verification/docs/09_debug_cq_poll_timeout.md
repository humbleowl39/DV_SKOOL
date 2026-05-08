# Module 09 — Debug Case 2: CQ Poll Timeout

<!-- DV-SKOOL-CH-CTX:start -->
<div class="chapter-context" data-cat="network">
  <a class="chapter-back" href="../">
    <span class="chapter-back-arrow">←</span>
    <span class="chapter-back-icon">🧪</span>
    <span class="chapter-back-text">RDMA Verification</span>
  </a>
  <span class="chapter-divider">›</span>
  <span class="chapter-marker">Module 09</span>
</div>
<!-- DV-SKOOL-CH-CTX:end -->

<!-- DV-SKOOL-CH-TOC:start -->
<div class="page-toc">
  <span class="page-toc-label">목차</span>
  <a class="page-toc-link" href="#왜-이-모듈이-중요한가">왜 이 모듈이 중요한가</a>
  <a class="page-toc-link" href="#핵심-개념">핵심 개념</a>
  <a class="page-toc-link" href="#1-대표-에러-메시지">1. 대표 에러 메시지</a>
  <a class="page-toc-link" href="#2-타임아웃-두-조건-둘-다-충족해야-발동">2. 타임아웃 두 조건</a>
  <a class="page-toc-link" href="#3-timeout_count-기본값">3. timeout_count 기본값</a>
  <a class="page-toc-link" href="#4-폴링-중-주기적-로그-10회마다-약-10us-간격">4. 폴링 중 주기적 로그</a>
  <a class="page-toc-link" href="#5단계-디버깅-절차">5단계 디버깅 절차</a>
  <a class="page-toc-link" href="#흔한-원인-매트릭스">흔한 원인 매트릭스</a>
  <a class="page-toc-link" href="#빠른-트리아지--한-줄-결정">빠른 트리아지</a>
  <a class="page-toc-link" href="#폴링-동작-한-줄-흐름">폴링 동작 한 줄 흐름</a>
  <a class="page-toc-link" href="#핵심-정리">핵심 정리</a>
  <a class="page-toc-link" href="#다음-모듈">다음 모듈</a>
</div>
<!-- DV-SKOOL-CH-TOC:end -->

!!! objective "학습 목표"
    이 모듈을 마치면:

    - **Recognize** `E-DRV-TBERR-0001/0002` 에러 ID 와 graceful 종료(`uvm_shutdown_phase`) 흐름을 인식할 수 있다.
    - **Analyze** 타임아웃 두 조건(`try_cnt > timeout_count` AND `!c2h_tracker::active`)을 분석할 수 있다.
    - **Apply** Phase bit / Tail pointer / unprocessed wqe 카운트로 5단계 디버깅을 적용할 수 있다.

!!! info "사전 지식"
    - [Module 03 — Phase & Test Flow](03_phase_test_flow.md) (CQ polling 패턴 3 — `cq_handler.RDMACQPoll`)
    - [Module 07 — H2C/C2H QID Reference](07_h2c_c2h_qid_map.md) (QID 14–17 / 8 / 10–11 의 의미)
    - [RDMA Module 06 — Data Path](../../rdma/06_data_path/) (CQ 의 phase bit, tail pointer)

## 왜 이 모듈이 중요한가
CQ polling 타임아웃은 "DUT 가 내가 보낸 work 를 처리하긴 했나?" 라는 가장 기본적인 질문에 답이 안 오는 상태입니다. 무엇이 멈춘 것인지(SQ doorbell 미인식 / WQE 처리 시작 안 됨 / completion engine 버그 / phase bit 동기화 실패) 단계적으로 좁혀가야 합니다.

> Confluence 출처: [CQ Poll Timeout](https://mangoboost.atlassian.net/wiki/spaces/RDMADV/pages/1335853134/CQ+Poll+Timeout)

## 핵심 개념

### 1. 대표 에러 메시지

| ID | 심각도 | 메시지 | 코드 위치 |
|----|--------|-------|---------|
| `E-DRV-TBERR-0001` | ERROR | `CQ POLLING TIMEOUT : Unprocessed CQE` | `vrdma_driver.svh:1486` |
| `E-DRV-TBERR-0002` | ERROR | `CQ HANDLER: CQ POLLING TIMEOUT` | `vrdma_driver.svh:1488` |

타임아웃 시 동작: **fatal 이 아니라** `uvm_shutdown_phase` 로 점프하여 graceful 종료 — 그래야 outstanding 진단 정보가 보존됨.

### 2. 타임아웃 두 조건 (둘 다 충족해야 발동)

```systemverilog
// vrdma_driver.svh:1484 task exceptionTimeout(); 흐름 (개념)
if((try_cnt > timeout_count) && (!c2h_tracker::active))
  this.exceptionTimeout();
```

| 조건 | 설명 |
|------|-----|
| `try_cnt > timeout_count` | 폴링 반복 횟수 초과 |
| `!c2h_tracker::active` | C2H DMA 활동 없음 (10ms 이상 비활성) |

🔑 **핵심**: c2h_tracker 가 active 인 동안에는 타임아웃이 **무한 지연**됩니다. DUT 가 DMA 를 계속하고 있으면 타임아웃이 안 납니다.

### 3. `timeout_count` 기본값

| 호출 위치 | 기본값 | 실효 시간 |
|----------|-------|----------|
| `vrdma_top_sequence::RDMACQPoll` | 50000 | ~50ms |
| `vrdma_sequence::RDMACQPoll` | 10000 | ~10ms |
| `vrdma_cq_poll_command::new()` | 10000 | ~10ms |
| `monitorErrCQ` (try_once=1) | 10000 | 타임아웃 불가 (try_once 면 1회만) |

### 4. 폴링 중 주기적 로그 (10회마다, 약 10us 간격)

| 필드 | 의미 | 확인 포인트 |
|------|-----|-----------|
| CQ number | 폴링 대상 CQ | 올바른 CQ 인지 |
| Try Count | 폴링 반복 횟수 | timeout_count 와 비교 |
| unprocessed wqe | 미처리 CQE 예상 수 | 0 이면 카운팅 오류 의심 |
| address | CQ phase bit 주소 | DUT 가 쓰는 주소와 일치하는지 |
| PHASE | 기대 phase bit 값 | DUT phase 와 동기 |
| TAIL POINTER | CQ tail pointer 위치 | wrap-around 상태 |

## 5단계 디버깅 절차

### Step 1 — 어떤 CQ 에서 타임아웃인지 확인
- 로그의 `CQ number` 필드, `cq_handler` 인스턴스 이름
- 멀티 CQ 환경이면 어느 CQ 인지 결정

### Step 2 — DUT 가 WQE 를 처리했는지 확인
- [Module 07 QID](07_h2c_c2h_qid_map.md) 적용:
  - QID 14–17 (`RDMA_CMD_H2C_QID`): WQE descriptor fetch 가 일어났나? — DUT 가 SQ doorbell 인식?
  - QID 8 (`RDMA_REQ_H2C_QID`): Requester payload fetch 가 일어났나? — WQE 처리 시작?
- 둘 다 0 회라면 DUT 가 SQ 자체를 모름

### Step 3 — CQE 가 생성되었는지 확인
- DUT 내부 completion engine FSM 추적
- 패킷은 나갔지만 CQE 가 안 만들어졌다면 completion 로직 버그 의심

### Step 4 — Phase bit 동기화 확인
- TB 의 expected `PHASE` vs DUT 가 쓴 phase bit
- CQ depth / wrap-around 후에 phase bit 토글 누락 의심

### Step 5 — C2H tracker active 상태 확인
- 타임아웃이 fire 했다면 `c2h_tracker::active = 0`
- 그러나 c2h_tracker 가 false-active 상태로 남아 있다면 `monitorErrCQ` (try_once=1) 만 fire 가능

```bash
# 로그 검색 키워드
grep -E "c2h_tracker.*active" run.log | tail -20
```

## 흔한 원인 매트릭스

| 원인 | 증상 | 확인 방법 |
|------|------|---------|
| DUT WQE 처리 실패 | Outstanding WQE 가 모두 같은 QP | DUT 내부 SQ dequeue 로직 |
| Doorbell 미전달 | WQE 발행 후 첫 CQE 부터 안 옴 | BAR4 SQ_DB 레지스터 쓰기 확인 |
| Completion engine 버그 | 패킷은 나갔는데 CQE 미생성 | DUT completion engine FSM |
| C2H DMA 경로 고장 | CQE 생성됐으나 host memory 미도착 | C2H DMA controller 상태 (QID 10–11) |
| Phase bit 불일치 | 폴링 주소는 맞는데 phase 안 맞음 | CQ depth / wrap 로직 |
| CQ base address 불일치 | 다른 주소에 CQE 기록 | `configure_phase` CQ 설정 vs DUT |
| Error CQE 가 ERR_CQ 로 도착 | 정상 CQ 대신 에러 CQ 에 기록 | `monitorErrCQ` 로그 확인 |
| `unprocessed_cqe_cnt` 불균형 | unsignaled WQE 가 잘못 카운트 | `signaled` / `sq_sig_type` 설정 |

## 빠른 트리아지 — 한 줄 결정

| 관찰 | 가설 |
|------|------|
| QID 14–17 fetch 없음 | DUT 가 SQ doorbell 인식 못함 — RAL/BAR 추적 |
| QID 14–17 OK, QID 8 없음 | WQE descriptor 는 받았지만 처리 안 함 — DUT WQE parser |
| QID 8 OK, packet 송신 OK, 그러나 CQE QID 10/11 없음 | Completion engine 미생성 |
| QID 10/11 OK, 그러나 PHASE 불일치 | Phase bit 동기화 |
| `unprocessed wqe = 0` 인데 timeout | 카운팅 오류 — `signaled` 설정, sq_sig_type |

## 폴링 동작 한 줄 흐름

```
RDMACQPoll(cq_num, try_once=0)
 → vrdma_cq_poll_command (timeout_count=10000)
   → driver.run_phase 의 cq polling 루프
     → CQ phase bit 주소 read
       → phase 일치? → CQE 처리 (cq_handler)
       → 불일치? → try_cnt++; 다음 시도
     → try_cnt > timeout_count AND !c2h_tracker::active
       → exceptionTimeout()
         → E-DRV-TBERR-0001 / 0002
         → uvm_shutdown_phase
```

## 핵심 정리

- 두 조건이 동시에 만족해야 타임아웃 — `try_cnt > N` AND `c2h_tracker !active`
- c2h_tracker 가 활동 중이면 타임아웃은 무한 지연 — DUT DMA 가 살아있다는 좋은 신호이지만 timeout 진단을 가린다
- 디버깅은 `QID 14–17 → 8 → 10/11 → PHASE` 순서대로 좁혀간다
- 종료는 fatal 이 아니라 graceful (`uvm_shutdown_phase`) — 추가 진단 정보 활용 가능

## 다음 모듈
[Module 10 — C2H Tracker Error](10_debug_c2h_tracker.md): C2H DMA 가 일어났는데 매칭이 실패할 때.

[퀴즈 풀어보기 →](quiz/09_debug_cq_poll_timeout_quiz.md)


--8<-- "abbreviations.md"
