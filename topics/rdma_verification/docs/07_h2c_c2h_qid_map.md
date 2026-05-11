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

<!-- DV-SKOOL-CH-TOC:start -->
<div class="page-toc">
  <span class="page-toc-label">목차</span>
  <a class="page-toc-link" href="#1-why-care-이-모듈이-왜-필요한가">1. Why care?</a>
  <a class="page-toc-link" href="#2-intuition-우편물-라벨-번호">2. Intuition</a>
  <a class="page-toc-link" href="#3-작은-예-cq-poll-timeout-때-qid-3-개로-원인-좁히기">3. 작은 예 — QID 로 원인 좁히기</a>
  <a class="page-toc-link" href="#4-일반화-h2c-6-종-c2h-4-종">4. 일반화 — H2C 6 / C2H 4</a>
  <a class="page-toc-link" href="#5-디테일-qid-표-채널-매핑-패턴-매트릭스-fsdb-검증">5. 디테일</a>
  <a class="page-toc-link" href="#6-흔한-오해-와-dv-디버그-체크리스트">6. 흔한 오해 + DV 디버그 체크리스트</a>
  <a class="page-toc-link" href="#7-핵심-정리-key-takeaways">7. 핵심 정리</a>
</div>
<!-- DV-SKOOL-CH-TOC:end -->

!!! objective "학습 목표"
    이 모듈을 마치면:

    - **List** H2C 6 종 / C2H 4 종 QID 와 그 용도를 나열할 수 있다.
    - **Identify** fsdb 의 QDMA 인터페이스에서 QID 를 보고 어느 서브시스템이 DMA 를 일으켰는지 즉시 식별할 수 있다.
    - **Apply** "CQ 폴링 타임아웃 났는데 DUT 가 WQE fetch 했나?" 같은 질문을 QID 로 답할 수 있다.
    - **Differentiate** 단일 채널 QID 와 복수 채널 QID (RECV / CMD H2C, RESP / COMP / ZERO C2H) 를 구분할 수 있다.

!!! info "사전 지식"
    - [Module 02 — Component 계층](02_component_hierarchy.md) (c2h_tracker 의 위치)
    - QDMA bypass interface 기본 — host ↔ card DMA 채널
    - fsdb 신호 검색 방법 (Verdi)

---

## 1. Why care? — 이 모듈이 왜 필요한가

QDMA bypass 인터페이스는 모든 DMA 트랜잭션이 흐르는 단일 지점입니다. QID 만 보면 "지금 DUT 의 어느 서브시스템이 host 와 통신하는가" 를 즉시 알 수 있고, 4 대 디버그 케이스 (M08-M11) 에서 모두 활용됩니다.

이 모듈을 건너뛰면 fsdb 에서 DMA 트랜잭션이 보여도 어느 서브시스템 (Requester / Responder / Recv / Cmd / CQE / Page Walk / CC notify) 인지 모르게 됩니다. 10 종 QID 매트릭스만 외우면 디버그 첫 분기점이 자동화됩니다.

> 정의 위치: `lib/base/def/vrdma_defs.svh:75-88`
> Confluence 출처: [H2C / C2H QID Reference](https://mangoboost.atlassian.net/wiki/spaces/RDMADV/pages/1334771791/H2C+C2H+QID+Reference)

---

## 2. Intuition — 우편물 라벨 번호

!!! tip "💡 한 줄 비유"
    QID = **우편물의 라벨 번호**. 같은 우체국 (QDMA bypass) 를 통과하지만 라벨 8 번은 "Requester 데이터", 14–17 번은 "Cmd WQE 페치", 10–11 번은 "CQE 쓰기" 식으로 _용도_ 가 1:1 매핑됨. 라벨만 보면 어느 부서가 보낸 우편인지 즉시 결정.

### 한 장 그림 — QID 매트릭스

```
                        H2C (Host → Card)                      C2H (Card → Host)
                        DUT 가 host memory READ                DUT 가 host memory WRITE
                        ────────────────────                   ─────────────────────────
   QID  8              REQ payload fetch                       8–9 RESP data write (2ch)
   QID  9              RSP payload fetch (Read Response)       10–11 CQE write       (2ch)
   QID 10–13           RECV WQE fetch (4ch)                    12–13 ZERO init write (2ch)
   QID 14–17           CMD WQE fetch (4ch)                     14   CC notify
   QID 18              CTRL WQE fetch
   QID 20              MISS_PA fetch (PTW miss)

   디버그 분기 (M09 CQ Poll Timeout 예):
       14–17 fetch 0회       ▶  DUT 가 SQ doorbell 인식 못 함  → BAR/RAL
       14–17 OK, 8 0회       ▶  WQE 받았지만 처리 안 함        → DUT WQE parser
       8 OK, packet OK,      ▶  Completion engine 미생성       → DUT completion FSM
         그러나 10–11 0회
       10–11 OK, PHASE bad   ▶  Phase bit 동기화                → CQ depth/wrap
```

### 왜 이 디자인인가 — Design rationale

세 가지가 동시에 풀려야 했습니다.

1. **단일 QDMA 인터페이스 공유** — 모든 DMA 가 한 인터페이스 통과 → QID 로만 서브시스템 구분.
2. **병렬화 필요한 서브시스템은 복수 채널** — RECV/CMD WQE fetch, RESP/COMP/ZERO write 는 throughput 위해 2~4 채널.
3. **디버그가 1 step 분기** — fsdb 에서 QID 만 잡으면 어느 서브시스템 책임인지 즉시 결정.

이 세 요구의 교집합이 H2C 6 / C2H 4 + 채널 매핑입니다.

---

## 3. 작은 예 — CQ Poll Timeout 때 QID 3 개로 원인 좁히기

`run.log` 에 `[E-DRV-TBERR-0001] CQ POLLING TIMEOUT : Unprocessed CQE` 가 떠서 fsdb 를 열었다고 가정.

### 단계별 추적

```
   Step 1     fsdb 에서 시점 t_timeout 직전 5 ms 의 H2C QID 14–17 검색
              ─────────────────────────────────────────────────────────
              결과: QID 14 에 valid pulse 0 회
                ▶ DUT 가 SQ doorbell 자체를 인식 못 함
                ▶ 가설: BAR4 SQ_DB 레지스터 쓰기 문제
                ▶ 다음 액션: RAL 의 BAR4 write 시점과 DUT 의 SQ_DB capture 비교

   Step 2 (가정: Step 1 에서 QID 14 fetch 가 1 회 이상 있었다면)
              fsdb 에서 QID 8 (REQ payload) 검색
              ─────────────────────────────────────────────────────────
              결과: QID 8 valid pulse 0 회
                ▶ WQE descriptor 는 받았지만 payload fetch 안 함
                ▶ 가설: DUT WQE parser 가 transfer_size 0 으로 해석 (Zero-length drop?)
                ▶ 다음 액션: WQE descriptor 내용 dump

   Step 3 (가정: Step 2 에서 QID 8 가 valid 였다면)
              fsdb 에서 QID 10–11 (CQE write) 검색
              ─────────────────────────────────────────────────────────
              결과: QID 10 valid pulse 0 회
                ▶ Completion engine 이 CQE 를 안 만듦
                ▶ 다음 액션: DUT completion engine FSM 추적
```

### 단계별 의미

| Step | 어느 QID | 무엇을 보나 | 가설 |
|---|---|---|---|
| 1 | H2C 14–17 (CMD) | WQE descriptor fetch 발생 | 0 회 → SQ doorbell 미인식 |
| 2 | H2C 8 (REQ) | Requester payload fetch 발생 | 0 회 → WQE 처리 시작 안 함 |
| 3 | C2H 10–11 (COMP) | CQE write 발생 | 0 회 → Completion engine 버그 |
| 4 | C2H 10–11 + PHASE | CQE write 후 phase bit 일치 | 불일치 → phase bit 동기 |

!!! note "여기서 잡아야 할 두 가지"
    **(1) QID 매트릭스가 디버그를 1 step 분기로 압축** — 4 개 QID (14–17, 8, 10–11, PHASE) 만 보면 timeout 의 4 가설이 1 줄 결정.<br>
    **(2) 복수 채널 QID 는 _모든_ 채널을 함께 검색** — H2C 14–17 = 4 채널 병렬. 채널 1만 봐서 "0 회" 라고 판단하면 오답.

---

## 4. 일반화 — H2C 6 종 / C2H 4 종

### 4.1 H2C QID — Host → Card

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

### 4.2 C2H QID — Card → Host

DUT 가 host 메모리에 **쓰는** 방향.

| QID | 상수명 | 용도 | 무엇을 쓰나 |
|-----|--------|-----|----------|
| 8–9 | `RESP_C2H_QID[0:1]` | Responder 데이터 쓰기 | Write/Send 수신 시 destination 메모리에 payload 쓰기 (2채널) |
| 10–11 | `COMP_C2H_QID[0:1]` | CQE 쓰기 | Completion Queue Entry 를 host CQ 메모리에 쓰기 (2채널) |
| 12–13 | `ZERO_C2H_QID[0:1]` | Zero init 쓰기 | 메모리 초기화 용도 (2채널) |
| 14 | `CC_NOTIFY_C2H_QID` | CC 알림 쓰기 | Congestion Control 이벤트 알림 |

> 코드 인용: `lib/base/def/vrdma_defs.svh:82-88`

### 4.3 채널 매핑

H2C/C2H 일부 QID 는 **복수 채널** 로 구성됩니다. 디버깅 시 모든 채널을 함께 검색해야 합니다.

| 카테고리 | 채널 수 | QID 범위 | 비고 |
|---------|--------|---------|------|
| RECV H2C | 4 | 10, 11, 12, 13 | RQ WQE fetch 병렬화 |
| CMD H2C | 4 | 14, 15, 16, 17 | SQ WQE fetch 병렬화 |
| RESP C2H | 2 | 8, 9 | 데이터 write 병렬화 |
| COMP C2H | 2 | 10, 11 | CQE write 병렬화 |
| ZERO C2H | 2 | 12, 13 | 초기화 write 병렬화 |

---

## 5. 디테일 — QID 표, 채널 매핑, 패턴 매트릭스, fsdb 검증

### 5.1 QID 기반 디버깅 — 패턴 매트릭스

#### H2C QID 로 문제 원인 특정

| 증상 | 어느 QID 확인 | 의미 |
|------|--------------|-----|
| CQ Poll Timeout (M09) | QID 14–17 (CMD) | WQE descriptor fetch 가 일어났는지 → DUT 가 SQ doorbell 인식했나 |
| CQ Poll Timeout (M09) | QID 8 (REQ) | Requester payload fetch 가 일어났는지 → WQE 처리 시작 여부 |
| Data Mismatch (M08) | QID 8 (REQ) / 9 (RSP) 데이터 | H2C 로 읽어온 source 데이터가 올바른지 |
| Recv 미동작 | QID 10–13 (RECV) | Recv WQE fetch — RQ doorbell 인식 여부 |
| Page Table 오류 | QID 20 (MISS_PA) | PTW miss 발생 여부, 어떤 주소의 PTE 를 fetch 했는지 |
| Control 명령 미완료 | QID 18 (CTRL) | Control WQE fetch 여부 |

#### C2H QID 로 문제 원인 특정

| 증상 | 어느 QID 확인 | 의미 |
|------|--------------|-----|
| Data Mismatch (M08) | QID 8–9 (RESP) 주소/데이터 | DUT 가 destination 에 쓴 데이터/주소 |
| CQ Poll Timeout (M09) | QID 10–11 (COMP) | CQE 가 host 메모리에 기록되었는지 |
| C2H Tracker 매칭 실패 (M10) | QID 8–9 (RESP) 주소 | C2H 대상 주소가 expected PA 와 일치하는지 |
| CC 이벤트 미수신 | QID 14 (CC_NOTIFY) | CC notification 발생 여부 |

### 5.2 디버깅 워크플로우

#### Case 1 — 특정 QID 의 DMA 가 아예 안 나옴

1. 시뮬 단계 확인: 해당 QID 의 DMA 가 한 번이라도 발생했는가?
2. `0` 회면 DUT 가 해당 서브시스템 doorbell 을 인식하지 못함 → RAL/BAR 쓰기 추적
3. 발생했지만 끊김 → DUT 의 해당 서브시스템 FSM stall

#### Case 2 — DMA 는 나오지만 주소/데이터가 잘못됨

1. fsdb 에서 해당 QID 의 첫 트랜잭션 추출
2. addr 를 TB 의 expected PA 리스트와 대조 — c2h_tracker 의 `m_qp_tracker` 가 expected
3. data 는 source 메모리 (M08) 또는 WQE descriptor (M09) 와 비교

#### Case 3 — 다른 에러와 교차 분석

- 한 시뮬에서 `F-C2H-MATCH-0002` (PA 매칭 실패) 와 `E-DRV-TBERR-0001` (CQ Polling Timeout) 둘 다 발생 → QID 8/9 의 주소 분석으로 어느 단계에서 mismatch 가 시작되었는지 결정

### 5.3 실전 — fsdb 에서 QID 검증

```bash
# (1) DUT 의 H2C qdma interface signal 확인
verdi -fsdbDump <run.fsdb> -nologo &
# (2) Signal: top.dut.qdma_h2c_qid (예) 추적
# (3) 시간 t 에서 qid 를 읽고 위 표 역참조
```

(실제 신호명은 DUT 의 QDMA wrapper 에 따라 다름 — fsdb 에서 `qid` 로 search)

---

## 6. 흔한 오해 와 DV 디버그 체크리스트

### 흔한 오해

!!! danger "❓ 오해 1 — 'C2H QID 8 = H2C QID 8 동일 서브시스템'"
    **실제**: 방향이 다르면 의미가 다름. **C2H QID 8** = Responder 데이터 write (수신측 destination 메모리), **H2C QID 8** = Requester payload fetch (송신측 source 메모리). 같은 8이지만 서로 다른 서브시스템.<br>
    **왜 헷갈리는가**: 숫자가 같아서.

!!! danger "❓ 오해 2 — 'QID 14 만 검색하면 CMD WQE fetch 다 본다'"
    **실제**: CMD H2C 는 4 채널 (14, 15, 16, 17). load balancing 으로 다른 채널 사용 가능 — 4 채널 모두 검색해야 누락 없음. RECV H2C 도 4 채널 (10–13).

!!! danger "❓ 오해 3 — 'QID 20 (MISS_PA) 는 거의 안 나타난다'"
    **실제**: 첫 transfer 이거나 large MR 의 새 page boundary 마다 PTW miss → QID 20 등장. data mismatch 디버그 시 _첫 mismatch 가 page boundary 와 일치_ 하면 QID 20 도 함께 봐야.

!!! danger "❓ 오해 4 — 'CC_NOTIFY (QID 14) 와 CMD H2C (QID 14) 가 충돌'"
    **실제**: 방향 (H2C vs C2H) 으로 분리. C2H QID 14 = CC_NOTIFY, H2C QID 14 = CMD WQE channel 0. fsdb signal 도 보통 H2C/C2H 별도. 검색 시 방향 명시.

!!! danger "❓ 오해 5 — '복수 채널 QID 는 round-robin 이라 채널 0 만 봐도 됨'"
    **실제**: 구현마다 round-robin 또는 hash-based — 정렬 보장 안 됨. 채널 4 개 다 검색하고 시간순 merge 해야 정확한 시퀀스. 이게 c2h_tracker 의 ordering 검증에서 중요.

### DV 디버그 체크리스트

| 증상 | 1차 의심 | 어느 QID + 어디 |
|---|---|---|
| 시뮬 시작 후 어떤 DMA 도 없음 | DUT reset 미해제 또는 BAR 미설정 | H2C 18 (CTRL) — 첫 CTRL WQE fetch 발생? |
| Send/Write 발행 후 송신 안 됨 | SQ doorbell 미인식 | H2C 14–17 (CMD) — fetch 0 회? |
| 패킷 송신은 되는데 destination 에 데이터 안 옴 | Responder 측 미동작 | C2H 8–9 (RESP) — write 0 회? |
| CQE 가 host 에 안 옴 | Completion engine 또는 C2H DMA | C2H 10–11 (COMP) — CQE write 0 회? |
| Recv WQE post 후 처리 안 됨 | RQ doorbell 미인식 | H2C 10–13 (RECV) — fetch 0 회? |
| 특정 page 에서만 data error | PTW miss 결과 잘못 | H2C 20 (MISS_PA) — 그 시점 PTE fetch 결과 |
| Read Response 후 데이터 안 옴 | Read response payload fetch 단계 | H2C 9 (RSP) — payload fetch 0 회? |
| CC notify 안 옴 | CC 이벤트 미생성 | C2H 14 (CC_NOTIFY) — 0 회? |

---

## 7. 핵심 정리 (Key Takeaways)

- H2C 6 종 / C2H 4 종 QID 가 서브시스템을 1:1 식별.
- 복수 채널인 RECV/CMD H2C, RESP/COMP/ZERO C2H 는 모든 채널을 함께 검색.
- 4 대 디버그 케이스 (M08-M11) 는 모두 QID 매트릭스를 도입부에서 활용.
- 정의는 `lib/base/def/vrdma_defs.svh:75-88` 단일 출처.
- 같은 숫자라도 H2C/C2H 방향이 다르면 다른 서브시스템.

!!! warning "실무 주의점"
    - fsdb 검색 시 QID 와 방향 (H2C/C2H) 둘 다 명시 — 같은 숫자가 양 방향에 있음.
    - 복수 채널 디버그 시 채널 0 만 보면 누락 — 4 채널 시간순 merge.

---

## 다음 모듈

→ [Module 08 — Data Integrity Error](08_debug_data_integrity.md): 데이터 비교 실패 케이스 단계별 디버깅.

[퀴즈 풀어보기 →](quiz/07_h2c_c2h_qid_map_quiz.md)


--8<-- "abbreviations.md"
