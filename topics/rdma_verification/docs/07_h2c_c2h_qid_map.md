# Module 07 — H2C / C2H QID Reference

<!-- DV-SKOOL-CH-CTX:start -->
<div class="chapter-context" data-cat="network">
  <a class="chapter-back" href="../">
    <span class="chapter-back-arrow">←</span>
    <span class="chapter-back-icon">🧪</span>
    <span class="chapter-back-text">RDMA Verification</span>
  </a>
  <span class="chapter-divider">›</span>
  <span class="chapter-marker">Module 07</span>
</div>
<!-- DV-SKOOL-CH-CTX:end -->

!!! objective "학습 목표"
    이 모듈을 마치면:

    - **List** H2C 6종 / C2H 4종 QID 와 그 용도를 나열할 수 있다.
    - **Identify** fsdb 의 QDMA 인터페이스에서 QID 를 보고 어느 서브시스템이 DMA 를 일으켰는지 즉시 식별할 수 있다.
    - **Apply** "CQ 폴링 타임아웃 났는데 DUT 가 WQE fetch 했나?" 같은 질문을 QID 로 답할 수 있다.

## 왜 이 모듈이 중요한가
QDMA bypass 인터페이스는 모든 DMA 트랜잭션이 흐르는 단일 지점입니다. QID 만 보면 "지금 DUT 의 어느 서브시스템이 host 와 통신하는가" 를 즉시 알 수 있고, 4대 디버그 케이스(M08-M11)에서 모두 활용됩니다.

> 정의 위치: `lib/base/def/vrdma_defs.svh:75-88`
> Confluence 출처: [H2C / C2H QID Reference](https://mangoboost.atlassian.net/wiki/spaces/RDMADV/pages/1334771791/H2C+C2H+QID+Reference)

## 핵심 개념

### 1. H2C QID — Host → Card

DUT 가 host 메모리에서 **읽어오는** 방향.

| QID | 상수명 | 용도 | 무엇을 읽어오나 |
|-----|--------|-----|---------------|
| 8 | `RDMA_REQ_H2C_QID` | Requester 데이터 fetch | Send/Write 시 source 메모리에서 payload 읽기 |
| 9 | `RDMA_RSP_H2C_QID` | Responder 데이터 fetch | Read Response 시 source 메모리에서 payload 읽기 |
| 10–13 | `RDMA_RECV_H2C_QID[0:3]` | Recv WQE fetch | RQ 에서 Recv WQE descriptor 읽기 (4채널) |
| 14–17 | `RDMA_CMD_H2C_QID[0:3]` | Command WQE fetch | SQ 에서 Send/Write/Read WQE descriptor 읽기 (4채널) |
| 18 | `RDMA_CTRL_H2C_QID` | Control WQE fetch | CTRL_QP 의 SQ 에서 QP/MR/CQ 관리 명령 읽기 |
| 20 | `RDMA_MISS_PA_H2C_QID` | Page Table Miss fetch | PTW miss 시 page table entry 읽기 |

> 코드 인용: `lib/base/def/vrdma_defs.svh:75-80`
> ```systemverilog
> localparam RDMA_REQ_H2C_QID = 8;
> localparam RDMA_RSP_H2C_QID = 9;
> localparam int RDMA_RECV_H2C_QID [4]= {10,11,12,13};
> localparam int RDMA_CMD_H2C_QID  [4]= {14,15,16,17};
> localparam RDMA_CTRL_H2C_QID = 18;
> localparam RDMA_MISS_PA_H2C_QID = 20;
> ```

### 2. C2H QID — Card → Host

DUT 가 host 메모리에 **쓰는** 방향.

| QID | 상수명 | 용도 | 무엇을 쓰나 |
|-----|--------|-----|----------|
| 8–9 | `RESP_C2H_QID[0:1]` | Responder 데이터 쓰기 | Write/Send 수신 시 destination 메모리에 payload 쓰기 (2채널) |
| 10–11 | `COMP_C2H_QID[0:1]` | CQE 쓰기 | Completion Queue Entry 를 host CQ 메모리에 쓰기 (2채널) |
| 12–13 | `ZERO_C2H_QID[0:1]` | Zero init 쓰기 | 메모리 초기화 용도 (2채널) |
| 14 | `CC_NOTIFY_C2H_QID` | CC 알림 쓰기 | Congestion Control 이벤트 알림 |

> 코드 인용: `lib/base/def/vrdma_defs.svh:82-88`

### 3. 채널 매핑

H2C/C2H 일부 QID 는 **복수 채널**로 구성됩니다. 디버깅 시 모든 채널을 함께 검색해야 합니다.

| 카테고리 | 채널 수 | QID 범위 | 비고 |
|---------|--------|---------|------|
| RECV H2C | 4 | 10, 11, 12, 13 | RQ WQE fetch 병렬화 |
| CMD H2C | 4 | 14, 15, 16, 17 | SQ WQE fetch 병렬화 |
| RESP C2H | 2 | 8, 9 | 데이터 write 병렬화 |
| COMP C2H | 2 | 10, 11 | CQE write 병렬화 |
| ZERO C2H | 2 | 12, 13 | 초기화 write 병렬화 |

## QID 기반 디버깅 — 패턴 매트릭스

### H2C QID 로 문제 원인 특정

| 증상 | 어느 QID 확인 | 의미 |
|------|--------------|-----|
| CQ Poll Timeout (M09) | QID 14–17 (CMD) | WQE descriptor fetch 가 일어났는지 → DUT 가 SQ doorbell 인식했나 |
| CQ Poll Timeout (M09) | QID 8 (REQ) | Requester payload fetch 가 일어났는지 → WQE 처리 시작 여부 |
| Data Mismatch (M08) | QID 8 (REQ) / 9 (RSP) 데이터 | H2C 로 읽어온 source 데이터가 올바른지 |
| Recv 미동작 | QID 10–13 (RECV) | Recv WQE fetch — RQ doorbell 인식 여부 |
| Page Table 오류 | QID 20 (MISS_PA) | PTW miss 발생 여부, 어떤 주소의 PTE 를 fetch 했는지 |
| Control 명령 미완료 | QID 18 (CTRL) | Control WQE fetch 여부 |

### C2H QID 로 문제 원인 특정

| 증상 | 어느 QID 확인 | 의미 |
|------|--------------|-----|
| Data Mismatch (M08) | QID 8–9 (RESP) 주소/데이터 | DUT 가 destination 에 쓴 데이터/주소 |
| CQ Poll Timeout (M09) | QID 10–11 (COMP) | CQE 가 host 메모리에 기록되었는지 |
| C2H Tracker 매칭 실패 (M10) | QID 8–9 (RESP) 주소 | C2H 대상 주소가 expected PA 와 일치하는지 |
| CC 이벤트 미수신 | QID 14 (CC_NOTIFY) | CC notification 발생 여부 |

## 디버깅 워크플로우

### Case 1 — 특정 QID 의 DMA 가 아예 안 나옴
1. 시뮬 단계 확인: 해당 QID 의 DMA 가 한 번이라도 발생했는가?
2. `0` 회면 DUT 가 해당 서브시스템 doorbell 을 인식하지 못함 → RAL/BAR 쓰기 추적
3. 발생했지만 끊김 → DUT 의 해당 서브시스템 FSM stall

### Case 2 — DMA 는 나오지만 주소/데이터가 잘못됨
1. fsdb 에서 해당 QID 의 첫 트랜잭션 추출
2. addr 를 TB 의 expected PA 리스트와 대조 — c2h_tracker 의 `m_qp_tracker` 가 expected
3. data 는 source 메모리(M08) 또는 WQE descriptor (M09) 와 비교

### Case 3 — 다른 에러와 교차 분석
- 한 시뮬에서 `F-C2H-MATCH-0002` (PA 매칭 실패) 와 `E-DRV-TBERR-0001` (CQ Polling Timeout) 둘 다 발생 → QID 8/9 의 주소 분석으로 어느 단계에서 mismatch 가 시작되었는지 결정

## 실전 — fsdb 에서 QID 검증

```bash
# (1) DUT 의 H2C qdma interface signal 확인
verdi -fsdbDump <run.fsdb> -nologo &
# (2) Signal: top.dut.qdma_h2c_qid (예) 추적
# (3) 시간 t 에서 qid 를 읽고 위 표 역참조
```

(실제 신호명은 DUT 의 QDMA wrapper 에 따라 다름 — fsdb 에서 `qid` 로 search)

## 핵심 정리

- H2C 6종 / C2H 4종 QID 가 서브시스템을 1:1 식별
- 복수 채널인 RECV/CMD H2C, RESP/COMP/ZERO C2H 는 모든 채널을 함께 검색
- 4대 디버그 케이스(M08-M11)는 모두 QID 매트릭스를 도입부에서 활용
- 정의는 `lib/base/def/vrdma_defs.svh:75-88` 단일 출처

## 다음 모듈
[Module 08 — Data Integrity Error](08_debug_data_integrity.md): 데이터 비교 실패 케이스 단계별 디버깅.

[퀴즈 풀어보기 →](quiz/07_h2c_c2h_qid_map_quiz.md)
