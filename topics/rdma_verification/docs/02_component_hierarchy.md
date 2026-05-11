# Module 02 — Component 계층 (`lib/base/component/`)

<!-- DV-SKOOL-CH-CTX:start -->
<div class="chapter-context" data-cat="network">
  <a class="chapter-back" href="../">
    <span class="chapter-back-arrow">←</span>
    <span class="chapter-back-icon">🧪</span>
    <span class="chapter-back-text">RDMA Verification</span>
  </a>
  <span class="chapter-divider">›</span>
  <span class="chapter-marker">Module 02</span>
</div>
<!-- DV-SKOOL-CH-CTX:end -->

<!-- DV-SKOOL-CH-TOC:start -->
<div class="page-toc">
  <span class="page-toc-label">목차</span>
  <a class="page-toc-link" href="#1-why-care-이-모듈이-왜-필요한가">1. Why care?</a>
  <a class="page-toc-link" href="#2-intuition-에러-id-prefix--파일-위치-지도">2. Intuition</a>
  <a class="page-toc-link" href="#3-작은-예-한-에러-로그에서-1초-만에-파일까지">3. 작은 예 — 1초 만에 파일까지</a>
  <a class="page-toc-link" href="#4-일반화-7-디렉토리--3-요소-agent--prefix-매핑">4. 일반화 — 7 디렉토리 + 3-요소 agent</a>
  <a class="page-toc-link" href="#5-디테일-디렉토리-요약-pool-util-코드-인용">5. 디테일</a>
  <a class="page-toc-link" href="#6-흔한-오해-와-dv-디버그-체크리스트">6. 흔한 오해 + DV 디버그 체크리스트</a>
  <a class="page-toc-link" href="#7-핵심-정리-key-takeaways">7. 핵심 정리</a>
</div>
<!-- DV-SKOOL-CH-TOC:end -->

!!! objective "학습 목표"
    이 모듈을 마치면:

    - **List** `lib/base/component/` 의 7개 직속 디렉토리를 나열할 수 있다.
    - **Identify** `agent/` 의 driver / handler / sequencer 분리 패턴과 그 의도를 식별할 수 있다.
    - **Compare** `data_env` / `dma_env` / `network_env` 의 검증 영역과 책임을 비교할 수 있다.
    - **Locate** RDMA 리소스 (QP/MR/PD/CQ/SQ/RQ) 의 등록·관리가 어디에서 일어나는지 짚을 수 있다.
    - **Apply** 에러 ID prefix 만 보고 어느 파일을 열지 1초 안에 결정할 수 있다.

!!! info "사전 지식"
    - [Module 01 — TB Overview](01_tb_overview.md) (top env 계층 큰 그림)
    - UVM agent 패턴 — driver / sequencer / monitor

---

## 1. Why care? — 이 모듈이 왜 필요한가

디버깅의 80% 는 "이 에러가 어디서 나왔는지" 를 빠르게 찾는 것입니다. 모든 에러 메시지는 특정 컴포넌트에서 발생하므로, 컴포넌트 계층을 알면 에러 ID prefix (`E-DRV-...`, `E-SB-...`, `F-C2H-...`, `F-CQHDL-...`) 만 보고도 1초 만에 위치를 잡을 수 있습니다.

이 모듈을 건너뛰면 모든 에러 로그에서 grep 으로 파일을 찾아야 합니다. 7 디렉토리 + 3-요소 agent + prefix 매핑을 외워두면 디버그 첫 단계가 자동화됩니다.

---

## 2. Intuition — 에러 ID prefix → 파일 위치 지도

!!! tip "💡 한 줄 비유"
    `lib/base/component/` ≈ **회사의 부서 디렉토리**. config = 인사부 (정책), env = 사업부, model = 연구소, pool = 자산관리부, util = 총무부, custom_phase = 일정관리부, test = 품질관리부. 에러 로그의 prefix 가 부서 코드라서, "E-SB-..." = 사업부 (Scoreboard) 라고 읽으면 어느 책상으로 갈지 결정.

### 한 장 그림 — 7 디렉토리 한눈에

이 디렉토리 트리는 ASCII 로 유지 (구조가 의도적으로 directory listing 형식):

```
   lib/base/component/
   │
   ├─ config/        ── 4 file  ── topology / node / driver cfg
   ├─ custom_phase/  ── 2 file  ── host_reset / arm_reset
   ├─ env/           ── 12 file ── 환경 계층 (vrdmatb_top_env 부터)
   │     │
   │     └─ 하위 5 영역 (M01 의 5-부 구조의 구현):
   │            ├─ agent/        : verb 발행 + CQE 처리       [E-DRV-*, F-CQHDL-*]
   │            ├─ data_env/     : 데이터 정합성              [E-SB-MATCH-*]
   │            ├─ dma_env/      : C2H DMA 추적               [F-C2H-*]
   │            ├─ network_env/  : 패킷 모니터                [PKT-*]
   │            └─ (top *.svh)   : 컨테이너
   │
   ├─ model/         ── 1 file  ── network delay model
   ├─ pool/          ── 3 file  ── QP/MR/PD/CQ/SQ/RQ 풀, gen_id
   ├─ test/          ── 1 file  ── base test class
   └─ util/          ── 4 file  ── link / sync / addr / node 변환
```

### 왜 이 디자인인가 — Design rationale

7 디렉토리 분류는 두 가지를 동시에 만족합니다.

1. **검증 영역별 분리** — env/ 안의 4 sub-env (agent / data_env / dma_env / network_env) 가 각자 다른 invariant 를 검증. 한 영역의 변경이 다른 영역에 영향을 안 줌.
2. **lifecycle 별 분리** — pool 은 자원 lifecycle, custom_phase 는 phase lifecycle, util 은 utility 함수. 카테고리가 섞이지 않음.

이 분류 덕분에 에러 ID prefix 가 단일 디렉토리 (대부분 단일 파일) 로 1:1 매핑됩니다.

---

## 3. 작은 예 — 한 에러 로그에서 1초 만에 파일까지

`run.log` 에 다음 한 줄이 떨어졌다고 가정합시다.

```
[E-SB-MATCH-0003] uvm_test_top.env.data_env.write_compare:
   Mismatch[0]: byte 64, local=0x12(0x12), remote=0x00(0x00)
```

### 단계별 추적

| Step | 누가 | 무엇을 | 왜 |
|---|---|---|---|
| ① | 디버거 | prefix `E-SB-MATCH-*` 인식 | "SB" = Scoreboard / Comparator → `data_env` |
| ② | 디버거 | "Write command" 이라는 단서 → 1side comparator | `data_env/vrdma_1side_compare.svh` 만 write/read 1-side 처리 |
| ③ | 디버거 | grep `"E-SB-MATCH-0003"` `vrdma_1side_compare.svh` | line 916 의 `Mismatch[%0d]: byte %0d ...` 메시지 발견 |
| ④ | 디버거 | 해당 함수의 호출 경로 위로 — `processCompletedWrite` | comparator 가 `completed_wqe_ap` 를 받아 검증한 곳 |
| ⑤ | 디버거 | upstream 추적 — `vrdma_driver.svh:1327` `completed_wqe_ap.write(cmd)` | driver 가 발행 |
| ⑥ | 디버거 | 발행 시점의 `cmd` 가 어떤 source/dest 를 가리켰는지 | M08 의 5단계 디버깅으로 진입 |

```
   prefix       →  컴포넌트                 →  디렉토리                                →  모듈
   ─────────       ──────────────────          ──────────────────────────────────────       ─────
   E-DRV-*         vrdma_driver               env/agent/driver/                              M09
   F-CQHDL-*       vrdma_cq_handler           env/agent/handler/                             M11
   E-SB-MATCH-*    vrdma_1/2side/imm_compare  env/data_env/                                  M08
   F-C2H-MATCH-*   vrdma_c2h_tracker          env/dma_env/vrdma_c2h_tracker/                 M10
   E-SB-TBERR-*    vrdma_data_scoreboard      env/data_env/                                  M06
```

!!! note "여기서 잡아야 할 두 가지"
    **(1) prefix 첫 토큰 (E-/F-/W-/I-) 은 심각도** — F=Fatal, E=Error, W=Warn, I=Info. F 가 보이면 시간 거꾸로 가서 첫 E 부터.<br>
    **(2) 두 번째 토큰 = 디렉토리 단서** — DRV→driver, SB→scoreboard/compare, C2H→c2h_tracker, CQHDL→cq_handler. 한 번 외우면 평생 사용.

---

## 4. 일반화 — 7 디렉토리 + 3-요소 agent + prefix 매핑

### 4.1 직속 디렉토리 7종

`lib/base/component/` 직속 디렉토리:

| 디렉토리 | 카테고리 | 파일 수 (Confluence) | 설명 |
|---------|---------|----------------------|------|
| `config/` | Config | 4 | 토폴로지 / 노드 / 드라이버 설정 객체 |
| `custom_phase/` | Custom Phase | 2 | 커스텀 UVM phase (host/arm reset) |
| `env/` | Env Hierarchy | 12 | environment 계층 구조 |
| `model/` | Model | 1 | 네트워크 지연 모델 |
| `pool/` | Pool | 3 | RDMA 리소스 풀 (QP/MR/PD/CQ/SQ/RQ) |
| `test/` | Test | 1 | base test 클래스 |
| `util/` | Util | 4 | 링크 / 동기화 / 주소변환 유틸리티 |

> Confluence 출처: [Component](https://mangoboost.atlassian.net/wiki/spaces/RDMADV/pages/1224867954/Component)

### 4.2 `agent/` 의 3-요소 분리

agent 는 RDMA-TB 의 핵심 워크호스입니다. 3가지 역할로 분리되어 있습니다.

| 역할 | 파일 | 무엇을 하는가 | State 보유? |
|-----|------|--------------|------|
| **Driver** | `agent/driver/vrdma_driver.svh` | WQE 발행, QP/MR/CQ 등록, outstanding 추적, CQ 폴링 진입점 | O (outstanding 큐) |
| **Handler** | `agent/handler/{vrdma_cq_handler, vrdma_send_handler, vrdma_recv_handler, vrdma_write_handler, vrdma_read_handler}.svh` | 특정 op type별 stateless forwarder, CQE 분류·라우팅 | X |
| **Sequencer** | `agent/sequencer/{vrdma_sequencer, vrdma_host_virtual_sequencer, vrdma_top_virtual_sequencer}.svh` | 시퀀스 실행 컨텍스트 + per-QP 에러 상태 (`wc_error_status`, `debug_wc_flag`) 보유 | O (per-QP 에러 큐) |

!!! note "왜 이렇게 나눴나"
    [Module 05 — Extension 4원칙](05_extension_principles.md) 의 "Stateless 보존" 원칙 때문입니다. `*_handler` 들은 **stateless forwarder** 로 설계되어 있고, 상태 (예: per-QP error status) 는 **sequencer 가 소유**합니다. 이를 잘못 섞으면 멀티노드/시퀀스 재사용에서 stale state 가 누적됩니다.

### 4.3 컴포넌트 → 에러 ID prefix 매핑

| 컴포넌트 | 에러 ID prefix | 예 | 모듈 |
|---------|---------------|----|----|
| `vrdma_driver` | `E-DRV-*` / `F-DRV-*` | `E-DRV-TBERR-0001` (CQ Polling Timeout) | [M09](09_debug_cq_poll_timeout.md) |
| `vrdma_cq_handler` | `F-CQHDL-*` | `F-CQHDL-TBERR-0003` (Unexpected Error CQE) | [M11](11_debug_unexpected_err_cqe.md) |
| `vrdma_1/2side/imm_compare` | `E-SB-MATCH-*`, `E-SB-TBERR-*` | `E-SB-MATCH-0003` (byte mismatch) | [M08](08_debug_data_integrity.md) |
| `vrdma_c2h_tracker` | `F-C2H-MATCH-*`, `E-C2H-MATCH-*`, `W-C2H-MATCH-*` | `F-C2H-MATCH-0002` (PA 매칭 실패) | [M10](10_debug_c2h_tracker.md) |
| `vrdma_data_scoreboard` | `E-SB-*` | `E-SB-TBERR-0007~0014` (MR key 불일치) | [M08](08_debug_data_integrity.md) |

이 prefix 만 알면 에러 로그를 보자마자 어느 파일을 열지 결정할 수 있습니다.

---

## 5. 디테일 — 디렉토리 요약, pool, util, 코드 인용

### 5.1 `env/` 의 sub-디렉토리 — 검증 영역별 분리

`lib/base/component/env/` 는 5개 핵심 sub-env 로 다시 나뉩니다:

| sub-env | 책임 | 핵심 컴포넌트 |
|--------|-----|--------------|
| `agent/` | RDMA verb 발행 + CQE 처리 | `vrdma_agent`, `driver/`, `handler/`, `sequencer/` |
| `data_env/` | 데이터 정합성 검증 | `vrdma_1side_compare`, `vrdma_2side_compare`, `vrdma_imm_compare`, `vrdma_data_scoreboard`, `vrdma_cqe_validation_checker`, `vrdma_iova_translator` |
| `dma_env/` | C2H DMA 추적 | `vrdma_c2h_tracker/`, `vrdma_dma_scoreboard` |
| `network_env/` | 패킷 프로토콜 모니터링 | `vrdma_pkt_base_monitor`, `vrdma_pkt_monitor`, `vrdma_ops_monitor`, `vrdma_rc_monitor`, `vrdma_ntw_sb_env` |
| (top-level `*.svh`) | env 컨테이너 | `vrdmatb_top_env`, `vrdma_node_env`, `vrdma_host_env`, `vrdma_ipshell_env`, `vrdma_lp_env`, `vrdma_memory_env`, `vrdma_ntw_env`, `vrdma_ntw_model_env`, `vrdma_ral_env`, `vrdma_mbshell_ral_env`, `vrdma_elc_env` |

### 5.2 `pool/` — RDMA 리소스 등록부

```
pool/
├── vrdma_pool.svh        ← QP / MR / PD / CQ / SQ / RQ 통합 풀
├── vrdma_qpool.svh       ← QP 전용 풀 (자세한 lifecycle)
└── vrdma_gen_id_pool.svh ← gen_id 풀 (Fast Register / re-register 추적)
```

driver 가 RDMA verb 를 실행할 때마다 pool 이 갱신됩니다:

- `RDMAQPCreate` → `qpool` 에 새 QP 객체 등록 + `qp_reg_ap` AP 송출
- `RDMAMRRegister` → MR 풀에 등록 + `mr_reg_ap` 송출
- `RDMAQPDestroy(.err(1))` → 해당 QP 를 ErrQP 로 전이, downstream comparator/tracker 에 deregister 알림

> 코드 위치: `vrdma_driver.svh:638` (`qp_reg_ap.write(Q)`), `:725 / :824` (`mr_reg_ap.write(MR)`).

### 5.3 `util/` — 횡단 유틸리티 4종

| 파일 (예) | 역할 |
|----------|-----|
| `link_util` | 두 노드 간 인터페이스 wiring |
| `sync_util` | 노드/handler 간 sync 이벤트 |
| `addr_util` | IOVA → PA 변환 및 page table 빌드 |
| `node_util` | 노드 ID 변환 / lookup |

(정확한 파일명은 `lib/base/component/util/` 디렉토리에서 확인)

### 5.4 코드 인용 — Driver 의 AP 선언

```systemverilog
// lib/base/component/env/agent/driver/vrdma_driver.svh:56-61
uvm_analysis_export #(vrdma_base_command) issued_wqe_ap;    // Issued WQE
uvm_analysis_export #(vrdma_base_command) completed_wqe_ap; // Completed WQE
uvm_analysis_export #(vrdma_cqe_object)   cqe_ap;           // CQEs
uvm_analysis_export #(vrdma_qp)           qp_reg_ap;        // QP Register
uvm_analysis_export #(vrdma_mr)           mr_reg_ap;        // MR Register
```

이 5개 AP 가 [Module 04 — Analysis Port Topology](04_analysis_port_topology.md) 의 모든 subscriber 의 출처입니다.

### 5.5 코드 인용 — Sequencer 의 per-QP 에러 state

```systemverilog
// lib/base/component/env/agent/sequencer/vrdma_sequencer.svh:19-20
RDMAWCStatus_t wc_error_status[int][$];
RDMAMBWCFlag_t debug_wc_flag[int][$];
```

- 외부 인덱스 `int` = qp_num
- 내부 큐 `[$]` = 시간순 에러 이벤트 리스트
- `clearErrorStatus(qp_num)` (line 179-181) 으로 per-QP 초기화

> 디버깅 시: `t_seqr.wc_error_status[qp_num][0]` 가 **첫 번째** 에러 상태 — [Module 11](11_debug_unexpected_err_cqe.md) 에서 다시 등장.

---

## 6. 흔한 오해 와 DV 디버그 체크리스트

### 흔한 오해

!!! danger "❓ 오해 1 — 'agent 안에 monitor 가 있다'"
    **실제**: 일반 UVM agent 는 driver + monitor + sequencer 3-요소지만, RDMA-TB 의 `vrdma_agent` 는 **driver + handler + sequencer**. monitor 는 별도 `network_env/` 안에 있고 (pkt_monitor) 패킷 단위로 동작. agent 는 **verb-level** 만 처리.<br>
    **왜 헷갈리는가**: UVM 표준 패턴 가정 때문.

!!! danger "❓ 오해 2 — 'handler 가 stateful 이니 거기에 카운터를 넣자'"
    **실제**: `*_handler` (send/recv/write/read) 는 **stateless forwarder**. opcode 따라 라우팅만 하며 자체 state 없음. State 는 **sequencer** (per-QP 에러) 또는 **driver** (outstanding) 가 보유. handler 에 state 추가 시 시퀀스 재사용·flush 시 stale state 누적 — [M05](05_extension_principles.md) #4 위반.

!!! danger "❓ 오해 3 — '에러 ID prefix 가 임의 명명이다'"
    **실제**: 두 번째 토큰이 **디렉토리/컴포넌트 식별자**. DRV=driver, SB=scoreboard, C2H=c2h_tracker, CQHDL=cq_handler. 첫 토큰 (E-/F-/W-/I-) 은 심각도. 디버그 시 prefix 두 토큰만 봐도 80% 위치 결정.

!!! danger "❓ 오해 4 — '`pool/` 은 free-list / allocator 다'"
    **실제**: RDMA-TB 의 `pool/` 은 **등록부 (registry)** — driver 가 발행한 QP/MR/PD/CQ 객체를 저장하고 다른 컴포넌트가 lookup. 메모리 할당 풀이 아닙니다. allocator 는 host_env 안의 memory model 책임.

### DV 디버그 체크리스트

| 증상 | 1차 의심 | 어디 보나 |
|---|---|---|
| `E-DRV-TBERR-*` 발생 | driver 에서 발행 | `vrdma_driver.svh` 안의 line 매칭 (M09 참조) |
| `E-SB-MATCH-*` 발생 | comparator 에서 발행 | `data_env/vrdma_1side_compare.svh`, `2side`, `imm` 중 메시지로 분기 |
| `F-C2H-MATCH-*` 발생 | c2h_tracker | `dma_env/vrdma_c2h_tracker/` |
| `F-CQHDL-*` 발생 | cq_handler | `agent/handler/vrdma_cq_handler.svh` |
| `wc_error_status[qp]` 가 비어있는데 verb skip | sequencer 와 driver 의 ErrQP 상태 동기 안 됨 | `qp.isErrQP()` vs sequencer 의 큐 비교 |
| 새 컴포넌트가 `qp_reg_ap` 를 못 받음 | env 가 sub-env 안에 잘못 배치되어 connect 누락 | top env 직속 + AP connect 확인 |
| 시뮬 시작 시 build_phase fatal | `cfg.num_nodes` 또는 `lib/external/` submodule 누락 | sys_info.json + git submodule status |

---

## 7. 핵심 정리 (Key Takeaways)

- `lib/base/component/` = `config / custom_phase / env / model / pool / test / util` (7종).
- `env/` 안에서 검증은 `agent` (verb 발행) + `data_env` (정합성) + `dma_env` (DMA 추적) + `network_env` (패킷) 4영역으로 분리.
- `agent/` 는 driver (stateful) + handler (stateless forwarder) + sequencer (per-QP state owner) 3-요소 분리.
- 에러 ID prefix → 컴포넌트 매핑이 디버깅의 첫 단계 — 외워두면 1초 안에 파일 결정.
- pool 은 자원 등록부, util 은 횡단 함수, model 은 네트워크 지연 — 각자 책임이 분리.

!!! warning "실무 주의점"
    - State 를 보유한 클래스 (driver, sequencer) 와 stateless 클래스 (handler, top_sequence) 의 구분을 항상 점검.
    - 새 컴포넌트는 카테고리에 맞게 7 디렉토리 중 하나에 배치 — 카테고리 섞으면 lib 분류가 무너짐.

---

## 다음 모듈

→ [Module 03 — UVM Phase & Test Flow](03_phase_test_flow.md) 에서 이 컴포넌트들이 시간 축에서 어떻게 협력하는지 본다.

[퀴즈 풀어보기 →](quiz/02_component_hierarchy_quiz.md)


--8<-- "abbreviations.md"
