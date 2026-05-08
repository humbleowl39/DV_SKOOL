# Module 10 — Debug Case 3: C2H Tracker Error

<!-- DV-SKOOL-CH-CTX:start -->
<div class="chapter-context" data-cat="network">
  <a class="chapter-back" href="../">
    <span class="chapter-back-arrow">←</span>
    <span class="chapter-back-icon">🧪</span>
    <span class="chapter-back-text">RDMA Verification</span>
  </a>
  <span class="chapter-divider">›</span>
  <span class="chapter-marker">Module 10</span>
</div>
<!-- DV-SKOOL-CH-CTX:end -->

<!-- DV-SKOOL-CH-TOC:start -->
<div class="page-toc">
  <span class="page-toc-label">목차</span>
  <a class="page-toc-link" href="#왜-이-모듈이-중요한가">왜 이 모듈이 중요한가</a>
  <a class="page-toc-link" href="#핵심-개념">핵심 개념</a>
  <a class="page-toc-link" href="#1-대표-에러-메시지">1. 대표 에러 메시지</a>
  <a class="page-toc-link" href="#2-ordering-규칙">2. Ordering 규칙</a>
  <a class="page-toc-link" href="#디버깅-단계별">디버깅 단계별</a>
  <a class="page-toc-link" href="#흔한-원인-매트릭스">흔한 원인 매트릭스</a>
  <a class="page-toc-link" href="#빠른-트리아지--한-줄-결정">빠른 트리아지</a>
  <a class="page-toc-link" href="#errqp-와의-상호작용-module-06-연결">ErrQP 와의 상호작용</a>
  <a class="page-toc-link" href="#핵심-정리">핵심 정리</a>
  <a class="page-toc-link" href="#다음-모듈">다음 모듈</a>
</div>
<!-- DV-SKOOL-CH-TOC:end -->

!!! objective "학습 목표"
    이 모듈을 마치면:

    - **Distinguish** 3가지 C2H tracker 실패 — PA 매칭 실패 / ordering 위반 / 크기 초과 — 를 구분할 수 있다.
    - **Apply** RC FIFO 순서 강제 vs OPS/SR out-of-order 허용 규칙을 적용할 수 있다.
    - **Trace** 진단 로그(`W-C2H-MATCH-0001~0003`)에서 unprocessed PA 리스트를 추출하고 expected vs actual PA 를 비교할 수 있다.

!!! info "사전 지식"
    - [RDMA Module 04 — Service Types & QP FSM](../../rdma/04_service_types_qp/) (RC vs OPS/SR 의 ordering 의미)
    - [RDMA Module 05 — Memory Model](../../rdma/05_memory_model/) (IOVA → PA 변환, page table)
    - [Module 06 — Error Handling Path](06_error_handling_path.md) (`is_err_qp_registered`)
    - [Module 07 — H2C/C2H QID Reference](07_h2c_c2h_qid_map.md) (C2H QID 8/9 의 RESP 의미)

## 왜 이 모듈이 중요한가
C2H tracker 는 DUT 가 host 에 쓴 모든 DMA 가 "기대된 위치, 기대된 순서"인지 검증합니다. 매칭 실패는 DUT 의 PTW / QP routing / MR page table 어디든 의심해야 하므로, 진단 로그를 정확히 해석하는 능력이 필수입니다.

> Confluence 출처: [C2H Tracker Error](https://mangoboost.atlassian.net/wiki/spaces/RDMADV/pages/1335656540/C2H+Tracker+Error)
> 코드: `lib/base/component/env/dma_env/vrdma_c2h_tracker/vrdma_c2h_tracker.svh`

## 핵심 개념

### 1. 대표 에러 메시지

#### PA 매칭 실패
| ID | 심각도 | 메시지 | 코드 위치 |
|----|--------|-------|---------|
| `F-C2H-MATCH-0001` | FATAL | `C2H transaction not found for node %s` (빈 노드) | `vrdma_c2h_tracker.svh:775` |
| `F-C2H-MATCH-0002` | FATAL | `C2H transaction not found for QP 0x%h on %s: addr=0x%h, size=0x%h` | `vrdma_c2h_tracker.svh:790` |
| `W-C2H-MATCH-0001` | WARNING | `Current WRITE unprocessed PA List: %p` (fatal 직전 진단) | `vrdma_c2h_tracker.svh:783` |
| `W-C2H-MATCH-0002` | WARNING | `Current READ unprocessed PA List: %p` | `vrdma_c2h_tracker.svh:784` |
| `W-C2H-MATCH-0003` | WARNING | `Current RECV unprocessed PA List: %p` | `vrdma_c2h_tracker.svh:785` |
| `W-C2H-MATCH-0004` | WARNING | `Current SRQ RECV unprocessed PA List: %p` | `vrdma_c2h_tracker.svh:788` |

#### Ordering 위반
| ID | 심각도 | 메시지 | 코드 위치 |
|----|--------|-------|---------|
| `E-C2H-MATCH-0001` | ERROR | Ordering violation — QP, op, tag, actual addr, found idx, expected idx, expected addr | `vrdma_c2h_tracker.svh:1037` |

#### 크기 초과
| ID | 심각도 | 메시지 | 코드 위치 |
|----|--------|-------|---------|
| `F-C2H-MATCH-0003` | FATAL | `Data transfer exceed the expected size for QP ... (OPS)` | `vrdma_c2h_tracker.svh:921` |
| `F-C2H-MATCH-0004` | FATAL | `Data transfer exceed the expected size for QP ... (non-OPS)` | `vrdma_c2h_tracker.svh:962` |
| `F-C2H-MATCH-0005` | FATAL | `Can not find the PA in the queue for QP ...` | `vrdma_c2h_tracker.svh:989` |

### 2. Ordering 규칙

| QP 타입 | 규칙 | Phase 1 동작 |
|--------|------|-------------|
| RC | **FIFO 순서 강제** | index 0 만 체크 |
| OPS / SR | **Out-of-order 허용** | 전체 인덱스 범위 체크 |

이 규칙은 RC 의 본질(reliable connected = 순서 보장)과 OPS/SR(performance/relaxed)의 트레이드오프에서 나옴.

## 디버깅 단계별

### Step 1 — Ordering 위반: 원본 I/O WQE 확인
`E-C2H-MATCH-0001` 발생 시 에러 로그에 **C2H 가 올라와야 하는 순서** 가 표시됩니다.

추적 절차:
1. 에러 로그의 `expected idx`, `expected addr`, `found idx`, `actual addr` 추출
2. `m_qp_tracker[node][qp].write_pa_queue` (또는 read/recv) 를 시간순 dump
3. 두 원본 I/O WQE 의 발행 시점 + DUT 처리 시점 비교

### Step 2 — PA 매칭 실패: C2H QID + 메모리 범위 확인
`F-C2H-MATCH-0002` 발생 시 fatal 직전 진단 로그(`W-C2H-MATCH-0001~0003`)가 출력됩니다.

#### C2H QID 로 원인 분류 ([Module 07](07_h2c_c2h_qid_map.md))
- QID 8–9 (`RESP_C2H_QID`): 데이터 write — 어느 QP 의 write 인가?
- QID 10–11 (`COMP_C2H_QID`): CQE write 가 잘못 매칭되었나? (드물게)

#### 메모리 범위 매핑
1. `addr=0x%h` 를 `m_qp_tracker[*][*].{write,read,recv}_pa_queue` 전체에 cross-reference
2. 어느 QP 의 expected PA 와 일치하는지 확인 — 다른 QP 의 PA 에 우연히 매칭되면 DUT QP routing 오류
3. 어느 PA 에도 없으면 PTW 버그 의심

### Step 3 — TB vs DUT PA 변환 비교
- TB: `m_iova_translator.translateIOVA(iova, mr_id)` → expected PA
- DUT: PTW 결과 (fsdb 에서 PTE entries)
- 두 결과 비교 → 어느 단계에서 갈렸는지 확인

### Step 4 — `trackCommand` 에서 커맨드 등록 여부
- driver 가 cmd 를 발행할 때 c2h_tracker 의 `trackCommand` 가 호출됨
- Zero-length transfer 는 등록 자체가 skip 될 수 있음 (Zero-length drop)
- `m_qp_tracker[node][qp].write_cmd_length_queue` 에 0 이 있으면 안 됨 — `F-C2H-TBERR-0004` 가 잡음

### Step 5 — C2H DMA 트랜잭션 자체 확인
- fsdb 에서 QID, addr, size 시퀀스
- `len > expected size` → `F-C2H-MATCH-0003/0004` (OPS / non-OPS 분리)

## 흔한 원인 매트릭스

| 원인 | 증상 | 확인 방법 |
|------|------|---------|
| DUT PTW 버그 | addr 가 PA 리스트 어디에도 없음 | TB `translateIOVA` vs DUT PTW |
| DUT QP routing 오류 | C2H QID 가 잘못된 QP 가리킴 | C2H QID vs 원본 WQE 의 QP 번호 |
| MR page table 설정 오류 | 특정 MR 의 커맨드만 실패 | `buildPageTable` 로그, PA 범위 |
| DUT out-of-order 처리 (RC) | `E-C2H-MATCH-0001` ordering violation | 원본 WQE 두 개의 DUT 처리 순서 |
| C2H addr 가 다른 QP 의 PA 에 매칭 | 잘못된 QP 의 데이터 | addr 를 전체 QP PA 리스트와 교차 |
| Zero-length drop | 커맨드가 등록 안 됨 | `transfer_size` 확인 |
| QP deregister 타이밍 | 에러 QP 정리 후 지연 C2H 도착 | `err_qp_registered` 상태 (M06) |
| MR re-register race | 구버전 PA 가 사용됨 | `gen_id`, Fast Register 타이밍 |
| C2H 크기 초과 | `F-C2H-MATCH-0003/0004` | DUT C2H size vs WQE transfer_size |

## 빠른 트리아지 — 한 줄 결정

| 관찰 | 가설 |
|------|------|
| `F-C2H-MATCH-0001` (빈 노드) | 노드가 한 번도 트랜잭션 발행 안 함 — c2h_tracker 가 노드 인식 못함 / cfg.num_nodes 오류 |
| `F-C2H-MATCH-0002` + addr 가 다른 QP 의 PA 와 일치 | DUT QP routing — RDMA opcode 의 dest_qp 처리 오류 |
| `F-C2H-MATCH-0002` + addr 가 어느 QP PA 와도 무관 | DUT PTW 또는 IOVA 변환 차이 |
| `E-C2H-MATCH-0001` on RC QP | DUT RC out-of-order 처리 (스펙 위반) |
| `E-C2H-MATCH-0001` on OPS/SR QP | 보통은 정상 — index 범위 내 OoO 면 통과해야 함 |
| `F-C2H-MATCH-0003/0004` | DUT 가 expected 보다 더 많이 씀 — 패딩 / 잘못된 length |

## ErrQP 와의 상호작용 (Module 06 연결)

C2H tracker 는 ErrQP 를 다음과 같이 처리:

```systemverilog
// vrdma_c2h_tracker.svh:346-349
if((outstanding > 0) && !(qp_obj.isErrQP() || err_enabled)) begin
  // 정상 — outstanding 있으면 fatal
end
else if(qp_obj.isErrQP() || err_enabled) begin
  // ErrQP 면 fatal 대신 경고
end
```

또한 `processC2hTransaction` 단계에서 매칭 실패 시 `is_err_qp_registered.size() > 0` 면 fatal 대신 skip — 에러 QP 정리 직후 도착하는 지연 트랜잭션을 처리.

> [Module 06](06_error_handling_path.md) 의 `vrdma_c2h_tracker::err_enabled` 정의(line 98) 참고.

## 핵심 정리

- 3 분류: PA 매칭 / ordering / 크기 초과
- RC FIFO 강제 vs OPS/SR OoO 허용 — error 분류 시 첫 분기점
- `W-C2H-MATCH-*` 진단 로그가 unprocessed PA 큐를 보여줌 — fatal 직전에 반드시 캡처
- ErrQP 정리 시 `is_err_qp_registered` 가 후속 매칭 실패를 silently skip — 의도된 동작

## 다음 모듈
[Module 11 — Unexpected Error CQE](11_debug_unexpected_err_cqe.md): DUT 가 에러 CQE 를 발생시킬 때.

[퀴즈 풀어보기 →](quiz/10_debug_c2h_tracker_quiz.md)
