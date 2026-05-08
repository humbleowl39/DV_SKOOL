# Module 08 — RDMA-TB 검증 환경 & DV 전략

<!-- DV-SKOOL-CH-CTX:start -->
<div class="chapter-context" data-cat="network">
  <a class="chapter-back" href="../">
    <span class="chapter-back-arrow">←</span>
    <span class="chapter-back-icon">⚡</span>
    <span class="chapter-back-text">RDMA</span>
  </a>
  <span class="chapter-divider">›</span>
  <span class="chapter-marker">Module 08</span>
</div>
<!-- DV-SKOOL-CH-CTX:end -->

<!-- DV-SKOOL-CH-TOC:start -->
<div class="page-toc">
  <span class="page-toc-label">목차</span>
  <a class="page-toc-link" href="#왜-이-모듈이-중요한가">왜 이 모듈이 중요한가</a>
  <a class="page-toc-link" href="#핵심-개념">핵심 개념</a>
  <a class="page-toc-link" href="#1-rdma-tb-디렉터리-한-장-뷰">1. RDMA-TB 디렉터리 한 장 뷰</a>
  <a class="page-toc-link" href="#2-lib-분류-기준-base-ext-external-submodule">2. lib 분류 기준 — base / ext / external / submodule</a>
  <a class="page-toc-link" href="#3-vrdmatb_top_env-두-노드-통합-환경">3. `vrdmatb_top_env` — 두 노드 통합 환경</a>
  <a class="page-toc-link" href="#4-agent-와-handler-패턴-gof-strategy">4. Agent 와 Handler 패턴 (GoF Strategy)</a>
  <a class="page-toc-link" href="#5-object-model">5. Object Model</a>
  <a class="page-toc-link" href="#6-sequence-라이브러리-25-files">6. Sequence 라이브러리 — 25+ files</a>
  <a class="page-toc-link" href="#7-coverage-plan-base-와-feature">7. Coverage Plan — base 와 feature</a>
  <a class="page-toc-link" href="#8-sub-ip-검증-환경-submodule">8. Sub-IP 검증 환경 (`submodule/`)</a>
  <a class="page-toc-link" href="#9-mrun-명령-워크플로">9. mrun 명령 워크플로</a>
  <a class="page-toc-link" href="#10-새-feature-추가-시-결정-트리">10. 새 Feature 추가 시 결정 트리</a>
  <a class="page-toc-link" href="#11-검증-가치-우선순위-coverage-driven">11. 검증 가치 우선순위 (Coverage-driven)</a>
  <a class="page-toc-link" href="#12-rdma-tb-검증의-실전-디버그-흐름">12. RDMA-TB 검증의 실전 디버그 흐름</a>
  <a class="page-toc-link" href="#핵심-정리-key-takeaways">핵심 정리 (Key Takeaways)</a>
  <a class="page-toc-link" href="#다음-모듈">다음 모듈</a>
</div>
<!-- DV-SKOOL-CH-TOC:end -->

!!! objective "학습 목표"
    이 모듈을 마치면:

    - **Diagram** RDMA-TB 의 디렉터리 (board / ip_top / plane / sub_ip / module) 와 환경 (host / node / network / data / dma / RAL env) 의 계층 구조를 그릴 수 있다.
    - **Identify** vrdma 의 핵심 객체 (QP, MR, command, CQE) 와 sequence (init, IO base, IO err, top vseq) 를 분류한다.
    - **Trace** Test → Top vseq → Sequencer → Driver → DUT 까지의 stimulus 경로와 Monitor → Scoreboard → Coverage 의 분석 경로를 추적한다.
    - **Plan** 새 feature 추가 시 base/ext/submodule 어디에 배치할지 분류 기준에 따라 결정한다.

!!! info "사전 지식"
    - UVM 1.2 (component, sequence, factory, config_db, RAL)
    - Module 04~07 (QP/Service/Memory/Data path/Error)

## 왜 이 모듈이 중요한가

**RDMA-TB 는 DV 환경 자체가 RDMA 시스템의 두 노드를 모델링** 합니다 — 즉 sender 와 responder 두 쪽 다 환경 안에 있고, 그 사이에 가짜 네트워크가 있고, 양쪽 host 메모리도 모델로 들어 있습니다. 이 구조를 한 번 잡으면 어떤 시나리오를 만들든 어디에 hook 을 걸어야 할지 즉답할 수 있게 됩니다.

!!! tip "💡 이해를 위한 비유"
    **vrdmatb_top_env** ≈ **두 도시 + 그 사이 도로 + 양쪽 우체국 모델**

    NODE0 / NODE1 = 두 도시 (host + RDMA NIC), `ntw_adptr` = 둘 사이 도로 (drop/duplicate/corrupt 콜백 hook), `host_env` = 우체국, `data_env` = 우편물 분석실, `dma_env` = 화물 트래커. 시나리오 = "이런 우편 N 통이 양 도시 사이를 오갈 때 어떻게 처리되는가" 의 시뮬레이션.

## 핵심 개념

**RDMA-TB 는 (1) work/ 의 design hierarchy (board → ip_top → plane → sub_ip → module) 마다 standalone TB, (2) lib/ 의 base / ext / external / submodule 분류, (3) `vrdmatb_top_env` 가 host/node/network/data/dma/RAL/elc/ipshell/lp/memory env 를 합치는 두 노드 환경 — 으로 구성. 모든 feature 검증은 해당 영역에 맞는 leaf TB 에서 시작해 점차 통합 환경으로 확장.**

!!! danger "❓ 흔한 오해"
    **오해**: "RDMA TB = RTL 위에 UVM agent 만 붙이면 됨".

    **실제**: RDMA 의 정상 동작은 host CPU + host memory + DMA + 두 node + 네트워크 가 동시에 협력해야 가능. 따라서 TB 는 host model, MMU model, network model, memory model 을 모두 포함 — RTL 외에 검증 모델이 RTL 만큼 큼. 그리고 Verbs 호출은 TB 의 sequence 가 RAL 을 통해 BAR register 를 prog 해 흉내냄.

    **왜 헷갈리는가**: 단순 IP 의 TB 와 비교해 system-level 모델링 비용이 압도적으로 큼.

---

## 1. RDMA-TB 디렉터리 한 장 뷰

```
RDMA-TB/
├── lib/
│   ├── base/                  ← MUST-KNOW infrastructure
│   │   ├── component/         (env / agent / driver / handler / sequencer / test / sequence / config / model)
│   │   ├── object/            (QP, MR, command_lib, data_descriptor)
│   │   ├── coverage/          (cqe_cov, packet_cov, error_handling_cov, …)
│   │   ├── def/               (defs, macro, types)
│   │   ├── interface/         (ccmad_if, rdma_command_if)
│   │   ├── ral/               (RAL classes for SOC/MBShell BARs)
│   │   ├── pkg/               (vrdma_class_pkg, vrdmatb_class_pkg)
│   │   └── list/              (vrdma.f, vrdmatb.f)
│   │
│   ├── ext/                   ← FEATURE-specific
│   │   ├── component/
│   │   │   ├── congestion_control/  (ccmad/rtt, ztr, ECN, PCC, adaptive_window)
│   │   │   ├── network/             (network test libs)
│   │   │   ├── error_handling/      (error handling, HW reset tests)
│   │   │   ├── reliability/
│   │   │   ├── sanity/
│   │   │   ├── application/         (cm, spdk)
│   │   │   └── rdma_verbs/          (write, read, send, fast_reg, rand, cache, shared_mr, srq, notify_cq, interrupt)
│   │   ├── sva/                     (wqe_scheduler, adaptive_window_controller, cnp_generator)
│   │   └── sva_if/                  (debug_if, read_debug_if)
│   │
│   ├── external/              ← 3rd party VIP wrapper (e.g. VPFC)
│   └── submodule/             ← Sub-IP 전용 (design hierarchy 따라)
│       ├── data_plane/
│       │   └── crc/           (CRC sub-IP TB: agent, env, seq_lib)
│       └── metadata/
│           ├── mmu/           (MMU sub-IP)
│           │   ├── ptw/       (Page Table Walker module)
│           │   ├── tlb/       (TLB module)
│           │   └── reset/     (MMU reset module)
│           └── rq_fetcher/    (Receive Queue Fetcher)
│
├── work/                      ← Simulation workspace, design hierarchy 기반
│   ├── board/
│   │   └── mblp/              (Board MAC-based loopback)
│   └── ip_top/
│       └── rdma_ip_top/       (IP top-level)
│           ├── data_plane/
│           ├── control_plane/
│           ├── congestion_control/
│           ├── metadata/mmu/{ptw,tlb,reset}/
│           └── dma_subsystem/rq_fetcher/
│
├── docs/
│   ├── class_hier.md
│   ├── CQE_REFERENCE.md
│   ├── log_registry.md
│   ├── spec/protocol/         (PROTOCOL_RULES, ROCEV2_RULE_APPLICABILITY)
│   └── vplan/
│       ├── VPLAN.md
│       └── error_handling/    (이 모듈이 자주 인용)
└── README.md
```

→ **Hierarchy 5 단계**: board → ip_top → plane → sub_ip → module. 각 단계마다 `set_env.sh`, `vlist/`, `vsim/`, `vtb/` 가 있음.

---

## 2. lib 분류 기준 — base / ext / external / submodule

**판단 질문**: "다른 feature 를 검증할 때 이 정보를 알아야 하는가?"

| Directory | 원칙 | 대상 |
|-----------|------|------|
| **base/** | 모든 feature 가 알아야 하는 핵심 인프라 | Agent, Driver, Env, Handler, base Sequence, Command, Config |
| **ext/** | 특정 feature 작업 시에만 필요 | ECN, Interrupt, CCMAD, PCC, network monitors, test_lib |
| **external/** | 3rd party VIP wrapper | VPFC |
| **submodule/** | Sub-IP 전용 verification (design hierarchy 따라) | MMU agents, RQ fetcher agents, CRC agents |

→ **Yes** → base, **No (해당 feature 만)** → ext.

---

## 3. `vrdmatb_top_env` — 두 노드 통합 환경

```
              ┌────────────────── vrdmatb_top_env ─────────────────────────┐
              │                                                              │
              │   ┌──────────── NODE0 ─────────┐  ┌──────────── NODE1 ────┐  │
              │   │                              │  │                       │  │
              │   │  vrdma_host_env              │  │  vrdma_host_env       │  │
              │   │   - host model (memory,     │  │                       │  │
              │   │     IOVA, MMU)              │  │                       │  │
              │   │   - vrdma_agent              │  │  vrdma_agent          │  │
              │   │     (driver / monitor /     │  │                       │  │
              │   │      sequencer / handlers)  │  │                       │  │
              │   │                              │  │                       │  │
              │   │  vrdma_ral_env (BAR0/2/4)   │  │  vrdma_ral_env        │  │
              │   │  vrdma_ipshell_env          │  │                       │  │
              │   │                              │  │                       │  │
              │   └──────────────┬───────────────┘  └──────────┬────────────┘  │
              │                  │                              │               │
              │                ┌─┴────────── ntw_adptr ─────────┴─┐             │
              │                │  vrdma_ntw_env / ntw_model_env   │             │
              │                │  (drop / duplicate / corrupt cb)│             │
              │                └────────────────────────────────┘              │
              │                                                                 │
              │   vrdma_data_env  (data path validation)                        │
              │     - cqe_handler, cmd_compare, iova_translator                │
              │     - 1side_compare / 2side_compare / imm_compare              │
              │     - data_scoreboard, cqe_validation_checker                  │
              │     - cqe_cov_collector                                         │
              │                                                                 │
              │   vrdma_dma_env   (DMA transfer tracking)                       │
              │     - vrdma_c2h_tracker                                         │
              │     - dma_scoreboard                                            │
              │                                                                 │
              │   vrdma_memory_env  (memory model)                              │
              │   vrdma_lp_env      (link partner / LP)                         │
              │   vrdma_elc_env     (ECN/CC reporter)                           │
              │                                                                 │
              └─────────────────────────────────────────────────────────────────┘
```

(`/home/jaehyeok.lee/RDMA/RDMA-TB/lib/base/component/env/` 디렉토리와 `class_hier.md` 기준)

### 각 env 역할

| Env | 책임 |
|-----|------|
| `vrdma_host_env` | Host CPU/메모리 모델, Verbs 호출 시뮬레이션 |
| `vrdma_node_env` | 노드 단위 RDMA 자원 (QP/MR/CQ pool) |
| `vrdma_ntw_env` | 네트워크 (link, switch) 모델 + drop/dup/corrupt callback |
| `vrdma_ntw_model_env` | Topology 모델 (latency/bandwidth) |
| `vrdma_memory_env` | 메모리 model — host memory contents 추적 |
| `vrdma_data_env` | Data path validation — packet → CQE 까지 |
| `vrdma_dma_env` | DMA tracker — descriptor → DMA transfer 의 정합성 |
| `vrdma_ral_env` | BAR0/2/4 register 접근 |
| `vrdma_ipshell_env` | IP shell (top-level wrapper) 환경 |
| `vrdma_lp_env` | Link Partner — 상대 노드의 행동 모델 |
| `vrdma_elc_env` | ECN / CC 리포터 |

---

## 4. Agent 와 Handler 패턴 (GoF Strategy)

```
   vrdma_agent
     ├── driver/    vrdma_driver
     ├── sequencer/ vrdma_sequencer
     │             ├── vrdma_host_virtual_sequencer
     │             └── vrdma_top_virtual_sequencer
     └── handler/   ← GoF Strategy
                    ├── vrdma_cq_handler      (CQ polling, error 보고)
                    ├── vrdma_send_handler    (SEND op 처리)
                    ├── vrdma_recv_handler    (RECV op 처리)
                    ├── vrdma_read_handler    (READ op)
                    └── vrdma_write_handler   (WRITE op)
```

**Handler 분리의 이유**: 각 OpCode 마다 처리 단계 (sg_list 검증, RETH 구성, ACK 대기, completion 생성) 가 다름 → 한 Driver 가 모든 OpCode 를 if/else 로 처리하면 거대해짐. Strategy 패턴으로 OpCode → Handler 매핑 → 새 OpCode 추가가 쉬움.

---

## 5. Object Model

```
   object/
     ├── vrdma_qp           (QP attribute, state)
     ├── vrdma_mr           (PD, key, addr, length, access)
     ├── vrdma_cqe_object   (CQE)
     ├── vrdma_q            (Queue base)
     ├── command_lib/
     │    ├── vrdma_base_command
     │    ├── io/           (send/recv/read/write/atomic command items)
     │    └── non_io/       (qp_create, mr_register, modify_qp, ...)
     └── data_descriptor/
          ├── vrdma_rdma_dd       (RDMA data descriptor)
          └── vrdma_dd_process    (descriptor processing)
```

→ Sequence 가 `vrdma_base_command` 의 sub-class 를 randomize 해 driver 가 RAL 로 doorbell + descriptor write 를 발생시키는 흐름.

---

## 6. Sequence 라이브러리 — 25+ files

핵심 sequence 흐름:

```
   Test
    └─▶ vrdmatb_init_vseq           (top-level virtual sequence)
          ├─▶ vrdma_init_seq        (RDMA bring-up: QP create, MR reg, modify QP → RTS)
          ├─▶ vrdma_cc_config_seq   (Congestion control config)
          └─▶ vrdma_io_base_seq     (CQ/MR/QP setup, operations, completion)
                ├─▶ vrdma_io_random_top_seq  (mixed traffic)
                └─▶ vrdma_io_err_top_seq     (error injection traffic)
                      └─▶ Adapter callback inject (drop, corrupt, duplicate)
```

| Sequence | 역할 |
|----------|------|
| `vrdma_init_seq` | 시스템 초기화 (BAR write, QP/MR/CQ allocation) |
| `vrdma_cc_config_seq` | DCQCN/PCC parameter set |
| `vrdma_io_base_seq` | 일반 IO base — CQ/MR/QP setup, op 실행, completion |
| `vrdma_io_random_top_seq` | Mixed Send/Write/Read traffic |
| `vrdma_io_err_top_seq` | Error injection 시 IO traffic (S1~S9 의 부모) |
| `vrdmatb_rc_send_seq` | RC SEND 단일 시나리오 |
| `vrdmatb_cm_seq` | CM 시나리오 (connection management) |

→ Test 는 `vrdmatb_base_test` 를 extend, factory 로 sequence 교체 가능.

---

## 7. Coverage Plan — base 와 feature

`lib/base/coverage/`:

| Cov | 내용 |
|-----|------|
| `vrdma_q_cov` | Queue (QP/CQ) state distribution |
| `vrdma_cqe_cov` | CQE 의 status / opcode / byte count |
| `vrdma_desc_cov` | Descriptor field distribution |
| `vrdma_packet_cov` | Packet header field (OpCode, PSN, length, etc.) |
| `vrdma_error_handling_cov` | (Module 07 에서 다룸) |
| `vrdma_scenario_cov` | High-level scenario hit |
| `vrdma_pcc_coverage_collector` | Programmable Congestion Control coverage |

→ **Coverage 는 base + feature 별 ext 의 합** 으로 구성.

---

## 8. Sub-IP 검증 환경 (`submodule/`)

`metadata/mmu/` 가 대표 예시:

```
   submodule/metadata/mmu/
   ├── agent/         (mmu agent)
   ├── base/          (base classes)
   ├── cov/
   ├── def/
   ├── filelist/
   ├── if/            (interface)
   ├── monitor/
   ├── ptw/           (PTW module sub-TB)
   ├── tlb/           (TLB module sub-TB)
   └── reset/         (reset module sub-TB)
```

| Module | 검증 포커스 |
|--------|------------|
| **PTW (Page Table Walker)** | 다단계 page walk, ATS 응답 latency, miss → walk → fill |
| **TLB** | Cache hit/miss, eviction policy, invalidate broadcast |
| **Reset** | MMU 전역 reset 시 in-flight 변환 cleanup |
| **RQ Fetcher** | Receive Queue 의 WQE prefetch, doorbell 처리 |
| **CRC** | ICRC 계산기 (data plane) |

→ Sub-IP TB 는 IP-top TB 로 통합되기 전 **빠른 corner case 검증 (몇 시간 시뮬)** 에 적합. IP-top 은 system 통합 시 transaction 단위 시나리오.

---

## 9. mrun 명령 워크플로

```
   $ source set_env.sh
   $ rdma list                    # 사용 가능한 target 목록
   $ rdma mmu_top                 # MMU top-level workspace 진입
   $ mrun comp vip                # VIP compile
   $ mrun comp rtl                # RTL compile
   $ mrun comp tb                 # TB compile
   $ mrun elab                    # Elaboration
   $ mrun test --test_name <name> # 테스트 실행
   $ mrun test --test_name <name> --fsdb --cov  # 파형 + 커버리지
   $ mrun regr --test_suite <suite_name>  # 회귀
```

→ Workspace 는 design hierarchy 단위. 각 leaf 에 `set_env.sh`, `pkg/`, `vlib/`, `vlist/`, `vsim/`, `vtb/`.

---

## 10. 새 Feature 추가 시 결정 트리

```
   Q1: 기존 service / opcode / op 의 변형 ?
     ├ Yes  → ext/component/rdma_verbs/<area>/ 에 test 추가
     └ No

   Q2: 새 sub-IP 의 standalone 검증 ?
     ├ Yes  → submodule/<plane>/<sub_ip>/ 디렉토리 신설
     └ No

   Q3: Congestion / Reliability / Application 같은 feature 영역 ?
     ├ Yes  → ext/component/<feature>/
     └ No

   Q4: 모든 feature 가 알아야 하는 인프라 ?
     ├ Yes  → base/component/ 또는 base/object/
     └ No   → 다시 분류 점검
```

---

## 11. 검증 가치 우선순위 (Coverage-driven)

```
   1. Sanity                    (가장 먼저 — 기본 path)
   2. RDMA verbs (write/read/send + RC)
   3. Memory (MR registration, fast reg, shared MR)
   4. Error handling (S1~S9)
   5. Congestion (ECN, CCMAD/RTT, PCC, adaptive window)
   6. Reliability (long-running stress, robustness)
   7. Application (CM, SPDK 의 사용 패턴)
   8. Network (network monitor 의 검증)
```

→ **Closure 전략**: 각 단계의 sanity + corner 가 모두 통과 후 다음 단계로. Coverage hole 은 cross 단위 (status × outstanding × node × CQ) 로 추적.

---

## 12. RDMA-TB 검증의 실전 디버그 흐름

```
  Test fail
    │
    ├─ 1. Log 첫 error 위치 확인 (UVM_FATAL / UVM_ERROR)
    ├─ 2. Phase 식별 (build / connect / run / extract)
    ├─ 3. 분류:
    │     - VIP / TB / DUT 책임 ?
    │     - Sequence 의 setup 누락 ?
    │     - RAL 의 register 미설정 ?
    │     - RTL 의 protocol 위반 ?
    │
    ├─ 4. 보고:
    │     ├─ TB 버그   → vrdma_seq / handler 수정
    │     ├─ DUT 버그  → bug ticket + waveform 첨부
    │     └─ Spec 문제 → ROCEV2_RULE_APPLICABILITY 확인
```

Log file 위치는 `mrun` 의 `vsim/<test>/run.log`. FSDB 는 `vsim/<test>/wave.fsdb`.

---

## 13. Confluence 보강 — RDMA-IP 모듈 구성과 Wrapper 책임

!!! note "Internal (Confluence: RDMA IP architecture, High-Level Architecture Description for DV team, Completer)"
    사내 RDMA-IP 는 다음 wrapper 들로 구성된다 (DV 관점 ground-truth, M11 에 상세).

    | Wrapper | 역할 | 외부 spec 대응 |
    |---|---|---|
    | **requester_frontend** | SQ → packet build, BTH/RETH 채움, retry 시 fetch | (없음 — 송신 전체) |
    | **completer_frontend** | 응답 패킷(ACK/NAK/Read Response) 처리, WQE 완료, CQE 생성 | requester 측 ACK 처리 |
    | **completer_retry** | timer / NAK / SACK 기반 재전송 결정 | spec §11.6 retry |
    | **info_arb** | WQE metadata (`tx_info`) 보관·중재 | (사내 SWQ 인프라) |
    | **payload engine** | drop / DMA write 경로 결정 | (사내) |
    | **responder_frontend** | incoming 요청 처리, 메모리 access, ACK 생성, MSN 증가 | responder 전체 |
    | **mmu wrapper** | IOVA→PA 변환, TLB, dereg flush | IBTA address translation |
    | **cc_module** | DCQCN / RTTCC 등 CC 알고리즘 구현 | Annex A17 + 사내 |

    Scoreboard 는 wrapper 경계마다 transaction 단위로 설치 — packet (network 측) ↔ WQE/CQE (host 측) ↔ DMA (memory 측) 의 3 종 transaction 비교가 핵심.

## 14. Confluence 보강 — Coverage 정의 운영

!!! note "Internal (Confluence: Coverage define, Coverage define module list, Meeting - coverage define sync)"
    사내 coverage 운영 표준:

    1. 모듈별로 **base coverage** (필수 closure) + **feature coverage** (옵션 sub-IP) 를 분리. M07 §4 의 7 항목은 base.
    2. **Coverage define module list** 페이지가 단일 진실 — 모듈 PR 시 이 목록 갱신이 PR 체크리스트.
    3. 격주 **coverage sync meeting** 에서 hole / dropped bin / cross 추가를 확정. 마지막 회의 (10/22) 에서 결정된 항목은 `lib/vtb/coverage/` 에 반영됨.
    4. 새 feature 의 first PR 에는 **min cov plan 한 단락** 이 description 에 들어가야 함.

## 15. Confluence 보강 — Debug Register / Bitfile 운용

!!! note "Internal (Confluence: RDMA debug register guide id=884966146; Debug register 정리 id=381845599; Bitfile status id=1228931074 — 운영 페이지는 본문 미반영)"
    - **Debug register**: 각 wrapper 가 `s_debug_reg` (AXI4-Lite slave) 를 노출. RDMA-TB RAL 에서 `vrdma_dbg_reg_block` 으로 모델. failure triage 시 `last_psn`, `last_opcode`, `error_code` 같은 sticky bit 를 먼저 read.
    - **검증 시 의무 항목**: bring-up 직후 모든 wrapper 의 dbg reg 가 초기값을 갖는지 RAL `mirror_check`.
    - **Bitfile / FPGA prototype**: emulation 환경의 bitfile 은 별도 페이지에서 추적 — 여기서는 *어떤 bitfile 이 어떤 testset 을 통과했는지* 운영 정보. 학습 자료는 본문에 포함하지 않고 M12 의 운영 가이드로만 링크.

## 16. Confluence 보강 — Bitwidth Trimming / FIFO 최적화

!!! note "Internal (Confluence: [SKRP-371] module list for bitwidth trimming, id=683212851; Fifo optimization, id=357269665)"
    PPA 개선의 정기적 활동.

    - **Bitwidth trimming**: HLS C++ 에서 32-bit 로 표현된 카운터·필드를 spec 상한에 맞춰 줄여 ResourceUtil↓. 예: PSN 카운터는 24-bit 면 충분, MSN 24-bit, R_Key index 14-bit 등.
    - **FIFO 최적화**: 데이터 path FIFO 의 depth × width 를 Little's law (depth ≥ throughput × max-stall) 로 재산정. 검증 영향: FIFO almost-full 도달 빈도가 변하므로 backpressure coverage 갱신.
    - 검증 의무: trimming PR 마다 **regression diff** 첨부, FIFO 변경 PR 마다 **buffer-occupancy cov** 비교.

---

## 핵심 정리 (Key Takeaways)

- RDMA-TB 는 work/ (design hierarchy 별 TB) + lib/ (base/ext/external/submodule) 의 두 축.
- `vrdmatb_top_env` 가 두 노드 + 네트워크 + 데이터/ DMA / 메모리 / RAL env 를 합치는 통합 환경.
- Agent 는 GoF Strategy 패턴으로 OpCode 별 handler 를 가짐 (send/recv/read/write/cq).
- 25+ Sequence 가 init / IO base / IO error / CC config 등 다양한 시나리오 빌딩 블록 제공.
- Sub-IP 검증 (MMU/PTW/TLB/Reset, RQ fetcher, CRC) 은 별도 standalone TB → IP-top 통합 단계로 점진.
- Coverage 는 base + feature 의 합. Cross coverage 가 closure 의 핵심.

!!! warning "실무 주의점"
    - "base 에 넣고 싶지만 사실 한 feature 만 쓰는" 코드는 ext 로 — base 가 비대해지면 모든 사용자가 불필요한 의존성을 갖게 됨.
    - Sub-IP TB 와 IP-top TB 의 sequence 호환성 확보가 자주 깨짐 — common base sequence 를 lib/base/component/sequence/ 에 두고 reuse.
    - `vrdma_io_err_top_seq` 의 callback 메커니즘이 매우 강력 — 새 error 시나리오는 99% 새 callback 추가로 해결, 새 sequence 작성보다 callback 작성을 먼저 시도.
    - Cross-node coverage 는 NODE0/NODE1 양쪽에서 같은 op 를 hit 해야 close — 시나리오 설계 시 양방향 traffic 비대칭 주의.
    - `mrun comp` 단계에서 깨지면 99% filelist (`*.f`) 누락 — 새 파일 추가 시 해당 영역의 `vlist/` 또는 `lib/.../filelist/` 갱신 필수.

---

## 다음 모듈

→ [Module 09 — Quick Reference Card](09_quick_reference_card.md)


--8<-- "abbreviations.md"
--8<-- "_inc/topic_abbr.md"
