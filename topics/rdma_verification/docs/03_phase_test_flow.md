# Module 03 — UVM Phase & Test Flow

<!-- DV-SKOOL-CH-CTX:start -->
<div class="chapter-context" data-cat="network">
  <a class="chapter-back" href="../">
    <span class="chapter-back-arrow">←</span>
    <span class="chapter-back-icon">🧪</span>
    <span class="chapter-back-text">RDMA Verification</span>
  </a>
  <span class="chapter-divider">›</span>
  <span class="chapter-marker">Module 03</span>
</div>
<!-- DV-SKOOL-CH-CTX:end -->

!!! objective "학습 목표"
    이 모듈을 마치면:

    - **Sequence** UVM phase 8단계가 RDMA-TB 에서 어떻게 매핑되는지 차례로 설명할 수 있다.
    - **Differentiate** default sequence / `start_item-finish_item` / cq_handler 직접 호출 / 테스트 레벨 시퀀스 시작 4가지 시퀀스 패턴을 구분할 수 있다.
    - **Trace** `top_vseqr` 에서 시작한 `vrdma_top_sequence` 가 어떻게 노드별 `rdma_seqr` 로 라우팅되는지 추적할 수 있다.

## 왜 이 모듈이 중요한가
RDMA-TB 는 **두 노드 + 다수 sub-env** 가 동시에 돌아가므로 phase 가 잘못 구성되면 race / dead-lock 이 쉽게 생깁니다. RDMA-TB 는 이를 해결하기 위해 phase 별 책임을 명확히 나눴고, `post_configure_phase` 에서 default sequence 로 HW 초기화를 자동 수행합니다.

## 핵심 개념

### 1. Phase 별 매핑 (Confluence Test Flow)

| # | Phase | 종류 | RDMA-TB 의 역할 |
|---|-------|-----|----------------|
| 1 | `build_phase` | function | env 인스턴스화 (`vrdmatb_top_env` → 노드/data/dma/network) |
| 2 | `connect_phase` | function | AP/export 연결, sequencer↔driver 연결 |
| 3 | `reset_phase` | task | DUT reset, 메모리 초기화 |
| 4 | `configure_phase` | task | RAL 기반 초기 컨피그 (BAR, MMU, link 설정) |
| 5 | `post_configure_phase` | task | **`vrdma_init_seq` 가 default sequence 로 자동 실행** — QP/CQ/MR 등록 등 HW 초기화 |
| 6 | `main_phase` | task | 테스트 시퀀스 실행, agent 백그라운드 task 동작 |
| 7 | `shutdown_phase` | task | outstanding 마무리, error_cq drain |
| 8 | `check_phase` | function | 모든 comparator/tracker 가 잔존 outstanding 검증 |

> Confluence 출처: [Test Flow](https://mangoboost.atlassian.net/wiki/spaces/RDMADV/pages/1224605910/Test+Flow)

### 2. 시퀀스 실행 패턴 4종

#### 패턴 1 — Default Sequence (자동 시작)
post_configure_phase 에 `vrdma_init_seq` 가 default 로 등록되어 있어 UVM 이 phase 진입 시 자동으로 생성·시작합니다.

```systemverilog
// agent build_phase 어딘가에서:
uvm_config_db#(uvm_object_wrapper)::set(this, "*.sequencer.post_configure_phase",
                                         "default_sequence", vrdma_init_seq::get_type());
```
> 정의: `lib/base/object/sequence/vrdma_init_seq.svh`

#### 패턴 2 — `start_item / finish_item` (멀티노드 타겟팅)
`vrdma_top_sequence` 의 verb 함수에서 사용. `.sequencer(t_seqr)` 파라미터로 **특정 노드의 `rdma_seqr`** 를 명시적으로 지정합니다.

```systemverilog
// 호출 예 (개념):
vrdma_send_command cmd = ...;
this.start_item(cmd, .sequencer(t_seqr));
assert(cmd.randomize() with { qp_num == ...; });
this.finish_item(cmd);
```

이 패턴이 멀티노드의 핵심입니다. `vrdma_top_sequence` 자체는 `top_vseqr` 에서 실행되지만 개별 verb 는 노드별 `rdma_seqr` 로 라우팅됩니다.

#### 패턴 3 — CQ Polling (직접 호출)
CQ 폴링은 `start_item` / `finish_item` 을 사용하지 **않고** sequencer 의 `cq_handler` 를 직접 호출합니다.

```systemverilog
// vrdma_top_sequence 어디:
t_seqr.cq_handler.RDMACQPoll(...);
```

> 이유: CQ 폴링은 트랜잭션 발행이 아니라 **결과 대기**이므로 driver 의 WQE 발행 큐를 거칠 필요가 없습니다. 폴링 주체는 cq_handler 입니다 — `lib/base/component/env/agent/handler/vrdma_cq_handler.svh`

#### 패턴 4 — 테스트 레벨 시퀀스 시작
Concrete 테스트의 `main_phase` 에서:

```systemverilog
my_top_seq = vrdma_my_top_sequence::type_id::create("my_top_seq");
my_top_seq.cfg = this.cfg;
assert(my_top_seq.randomize());
my_top_seq.start(env.top_vseqr);  // ← top_vseqr 에서 시작
```

### 3. Sequencer 계층

```
top_vseqr (vrdma_top_virtual_sequencer)
├── host_vseqr[0] (vrdma_host_virtual_sequencer)
│   └── rdma_seqr[0] (vrdma_sequencer)  ← node 0 의 verb queue
├── host_vseqr[1] (vrdma_host_virtual_sequencer)
│   └── rdma_seqr[1] (vrdma_sequencer)  ← node 1 의 verb queue
└── ...
```

핵심 규칙:

- **`vrdma_top_sequence` 는 stateless function set** — body() 가 없거나 minimal. 실제 verb 함수만 제공.
- 멀티노드 verb 를 동시에 발행하려면 `fork-join_none` 으로 두 시퀀서에 동시에 `start_item / finish_item`.
- per-QP state (예: outstanding count, error status) 는 `vrdma_sequencer` 가 보유. 시퀀스가 보유하면 시퀀스 재사용 시 stale 됨 ([Module 05](05_extension_principles.md) Stateless 원칙 참고).

## 코드 walkthrough

### Init seq의 default sequence 등록
- 파일: `lib/base/object/sequence/vrdma_init_seq.svh`
- agent의 build_phase에서 sequencer의 default_sequence 로 등록되며, post_configure_phase 진입 시 UVM이 자동으로 create + start.

### Top sequence의 verb 인터페이스
- 파일: `lib/base/object/sequence/vrdma_top_sequence.svh`
- 주요 함수:
  - `RDMASend / RDMAWrite / RDMARead / RDMARecvPost / RDMAQPCreate / RDMAQPDestroy / RDMAMRRegister / RDMACQCreate / RDMACQPoll`
  - 모두 `t_seqr` 파라미터를 받음 → 호출자가 어느 노드에 verb 를 보낼지 결정

### Driver 의 백그라운드 task
- `vrdma_driver` 의 `run_phase` 는 다음을 무한 루프로 돌립니다:
  - `EntryPoint(cmd)` — 시퀀서에서 받은 cmd 처리
  - `chkSQErrQP` — QP 가 ErrQP 면 skip
  - WQE 발행 → outstanding 등록 → `issued_wqe_ap.write(cmd)`
- 자세한 에러 분기는 [Module 06](06_error_handling_path.md).

### 테스트 클래스 구조 (예)
- `lib/base/component/test/vrdmatb_base_test.svh` — `rdma_base_test`
- `lib/ext/test/sanity/vrdmatb_sanity_tests.svh` — sanity 시나리오
- `lib/ext/test/error_handling/vrdmatb_error_handling_test_lib.svh` — 에러 처리 테스트 base

전형적인 패턴:
```systemverilog
class my_test extends rdma_base_test;
  `uvm_component_utils(my_test)
  task main_phase(uvm_phase phase);
    my_top_seq seq = my_top_seq::type_id::create("seq");
    phase.raise_objection(this);
    seq.cfg = this.cfg;
    assert(seq.randomize());
    seq.start(env.top_vseqr);
    phase.drop_objection(this);
  endtask
endclass
```

## 흔한 실수와 회피

| 실수 | 결과 | 해결 |
|------|------|-----|
| 시퀀스에 per-QP state 추가 | 시퀀스 재사용 시 stale state, 멀티노드 cross-talk | state 는 `vrdma_sequencer` 로 옮김 |
| `top_vseqr` 에서 직접 verb 발행 (`.sequencer` 파라미터 누락) | 어느 노드인지 결정 불가, 런타임 에러 | 항상 `t_seqr` 명시 |
| `main_phase` 에서 raise/drop_objection 누락 | phase 가 즉시 종료되어 verb 가 발행되기도 전에 끝남 | objection 패턴 필수 |
| CQ 폴링을 `start_item` 으로 시도 | driver 큐와 충돌, dead-lock | `cq_handler.RDMACQPoll` 직접 호출 |

## 핵심 정리

- 8 phase 중 검증의 골격은 `post_configure` (init seq) → `main` (test seq) → `check` (잔존 검증).
- 시퀀스 패턴 4종은 모두 의도가 다르다 — default(자동), `start_item-finish_item`(노드 타겟팅), `cq_handler` 직접 호출(폴링), `start(top_vseqr)` (테스트 진입).
- 멀티노드의 핵심은 `top_vseqr` 에서 시작하지만 verb 는 `.sequencer(t_seqr)` 로 노드 라우팅.
- state ownership 은 sequencer 에 있다 — 시퀀스에 두면 안 된다.

## 다음 모듈
[Module 04 — Analysis Port Topology](04_analysis_port_topology.md): driver 가 발행한 WQE/CQE 가 어떤 AP를 통해 누구에게 도달하는지.

[퀴즈 풀어보기 →](quiz/03_phase_test_flow_quiz.md)
