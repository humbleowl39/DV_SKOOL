# RDMA Verification

<!-- DV-SKOOL-HERO:start -->
<div class="topic-hero" data-cat="network">
  <div class="topic-hero-mark">🧪</div>
  <div class="topic-hero-body">
    <div class="topic-hero-title">RDMA Verification</div>
    <p class="topic-hero-sub">RDMA-TB 아키텍처 · 에러 처리 · 4대 디버깅 케이스</p>
  </div>
</div>
<!-- DV-SKOOL-HERO:end -->

<!-- DV-SKOOL-TOC:start -->
<div class="page-toc">
  <span class="page-toc-label">목차</span>
  <a class="page-toc-link" href="#학습-목표">🎯 학습 목표</a>
  <a class="page-toc-link" href="#사전-지식">📋 사전 지식</a>
  <a class="page-toc-link" href="#개념-맵">🗺️ 개념 맵</a>
  <a class="page-toc-link" href="#학습-모듈">📚 학습 모듈</a>
  <a class="page-toc-link" href="#참조-자료">📖 참조 자료</a>
</div>
<!-- DV-SKOOL-TOC:end -->

이 코스는 사내 RDMA IP 검증 환경(`RDMA-TB`)을 빠르게 이해하고, 4대 디버깅 케이스(Data Integrity, CQ Poll Timeout, C2H Tracker, Unexpected Error CQE)를 실전적으로 트리아지할 수 있도록 설계되어 있습니다.

기존 [RDMA (IB & RoCEv2)](../rdma/) 코스가 **프로토콜과 IBTA 스펙**을 다룬다면, 이 코스는 **TB 코드와 디버깅 워크플로**에 집중합니다. 모든 사실은 Confluence(Testbench Architecture, Debugging Cases)와 `RDMA-TB/lib` 코드에 그라운딩되어 있습니다.

## 🎯 학습 목표
이 코스를 마치면 다음을 할 수 있습니다.

- **Diagram** RDMA-TB 의 multi-node 환경 계층(`vrdmatb_top_env` → host/node/data/dma/network env)을 그릴 수 있다.
- **Identify** `lib/base/component/` 디렉토리 11개의 역할(config / custom_phase / env / model / pool / test / util)을 식별할 수 있다.
- **Trace** 한 테스트 시퀀스가 UVM phase(build → connect → reset → configure → post_configure → main → shutdown → check)를 따라 어떻게 실행되는지 추적할 수 있다.
- **Apply** Analysis Port 1:N 브로드캐스트 구조에 새 subscriber를 추가하는 패턴(`drv.issued_wqe_ap`, `drv.cqe_ap`, `cq_handler.cqe_validation_cqe_ap`)을 적용할 수 있다.
- **Evaluate** 새 컴포넌트 추가 시 4원칙(Open-Closed / Interface Stability / DRY via AP / Stateless 보존) 위반 여부를 평가할 수 있다.
- **Debug** 4대 디버그 케이스(Data Mismatch, CQ Poll Timeout, C2H Tracker, Unexpected Error CQE)를 에러 메시지 ID와 QID(`H2C/C2H`)만 보고 트리아지할 수 있다.
- **Promote** 의도된 에러 시나리오를 `expected_error` + `RDMAQPDestroy(.err(1))` 패턴으로 정상화할 수 있다.

## 📋 사전 지식
- [RDMA (InfiniBand & RoCEv2)](../rdma/) — 특히 Module 04 (Service & QP FSM), 05 (Memory Model), 06 (Data Path), 08 (RDMA-TB 검증 환경)
- [UVM](../uvm/) — agent / sequence / sequencer / phase / TLM analysis port
- VCS / mrun / SystemVerilog 1800 기본 구문

## 🗺️ 개념 맵
<div class="concept-dag">
  <div class="concept-dag-title">개념 의존성 — 순서대로 학습 권장</div>
  <div class="concept-dag-row">
    <a class="concept-dag-node" href="01_tb_overview/">
      <span class="concept-dag-node-num">M01</span>
      <span class="concept-dag-node-title">TB Overview</span>
    </a>
    <span class="concept-dag-arrow">→</span>
    <a class="concept-dag-node" href="02_component_hierarchy/">
      <span class="concept-dag-node-num">M02</span>
      <span class="concept-dag-node-title">Component</span>
    </a>
    <span class="concept-dag-arrow">→</span>
    <a class="concept-dag-node" href="03_phase_test_flow/">
      <span class="concept-dag-node-num">M03</span>
      <span class="concept-dag-node-title">Phase / Test Flow</span>
    </a>
    <span class="concept-dag-arrow">→</span>
    <a class="concept-dag-node" href="04_analysis_port_topology/">
      <span class="concept-dag-node-num">M04</span>
      <span class="concept-dag-node-title">AP Topology</span>
    </a>
  </div>
  <div class="concept-dag-row">
    <a class="concept-dag-node" href="05_extension_principles/">
      <span class="concept-dag-node-num">M05</span>
      <span class="concept-dag-node-title">Extension 4원칙</span>
    </a>
    <span class="concept-dag-arrow">→</span>
    <a class="concept-dag-node" href="06_error_handling_path/">
      <span class="concept-dag-node-num">M06</span>
      <span class="concept-dag-node-title">Error Path</span>
    </a>
    <span class="concept-dag-arrow">→</span>
    <a class="concept-dag-node" href="07_h2c_c2h_qid_map/">
      <span class="concept-dag-node-num">M07</span>
      <span class="concept-dag-node-title">QID Reference</span>
    </a>
  </div>
  <div class="concept-dag-row">
    <a class="concept-dag-node" href="08_debug_data_integrity/">
      <span class="concept-dag-node-num">M08</span>
      <span class="concept-dag-node-title">Data Mismatch</span>
    </a>
    <span class="concept-dag-arrow">→</span>
    <a class="concept-dag-node" href="09_debug_cq_poll_timeout/">
      <span class="concept-dag-node-num">M09</span>
      <span class="concept-dag-node-title">CQ Poll Timeout</span>
    </a>
    <span class="concept-dag-arrow">→</span>
    <a class="concept-dag-node" href="10_debug_c2h_tracker/">
      <span class="concept-dag-node-num">M10</span>
      <span class="concept-dag-node-title">C2H Tracker</span>
    </a>
    <span class="concept-dag-arrow">→</span>
    <a class="concept-dag-node" href="11_debug_unexpected_err_cqe/">
      <span class="concept-dag-node-num">M11</span>
      <span class="concept-dag-node-title">Unexpected Err CQE</span>
    </a>
    <span class="concept-dag-arrow">→</span>
    <a class="concept-dag-node" href="12_debug_cheatsheet/">
      <span class="concept-dag-node-num">M12</span>
      <span class="concept-dag-node-title">Cheatsheet</span>
    </a>
  </div>
  <div class="concept-dag-legend">각 노드 = 모듈 (클릭하여 이동) · 화살표(→) = 선수 지식 흐름 · 1부 끝(M07) → 2부 진입(M08)</div>
</div>

## 📚 학습 모듈

### 1부 — 아키텍처
<!-- DV-SKOOL-MODULES-PART1:start -->
<div class="module-grid">
  <a class="module-card" data-cat="network" href="01_tb_overview/">
    <div class="module-num">01</div>
    <div class="module-body">
      <div class="module-title">TB Overview & Multi-Node 구조</div>
    </div>
  </a>
  <a class="module-card" data-cat="network" href="02_component_hierarchy/">
    <div class="module-num">02</div>
    <div class="module-body">
      <div class="module-title">Component 계층 (lib/base/component)</div>
    </div>
  </a>
  <a class="module-card" data-cat="network" href="03_phase_test_flow/">
    <div class="module-num">03</div>
    <div class="module-body">
      <div class="module-title">UVM Phase & Test Flow</div>
    </div>
  </a>
  <a class="module-card" data-cat="network" href="04_analysis_port_topology/">
    <div class="module-num">04</div>
    <div class="module-body">
      <div class="module-title">Analysis Port Topology</div>
    </div>
  </a>
  <a class="module-card" data-cat="network" href="05_extension_principles/">
    <div class="module-num">05</div>
    <div class="module-body">
      <div class="module-title">Adding New Components — 4원칙</div>
    </div>
  </a>
  <a class="module-card" data-cat="network" href="06_error_handling_path/">
    <div class="module-num">06</div>
    <div class="module-body">
      <div class="module-title">Error Handling Path</div>
    </div>
  </a>
  <a class="module-card" data-cat="network" href="07_h2c_c2h_qid_map/">
    <div class="module-num">07</div>
    <div class="module-body">
      <div class="module-title">H2C / C2H QID Reference</div>
    </div>
  </a>
</div>
<!-- DV-SKOOL-MODULES-PART1:end -->

### 2부 — 디버깅 케이스
<!-- DV-SKOOL-MODULES-PART2:start -->
<div class="module-grid">
  <a class="module-card" data-cat="network" href="08_debug_data_integrity/">
    <div class="module-num">08</div>
    <div class="module-body">
      <div class="module-title">Data Integrity Error</div>
    </div>
  </a>
  <a class="module-card" data-cat="network" href="09_debug_cq_poll_timeout/">
    <div class="module-num">09</div>
    <div class="module-body">
      <div class="module-title">CQ Poll Timeout</div>
    </div>
  </a>
  <a class="module-card" data-cat="network" href="10_debug_c2h_tracker/">
    <div class="module-num">10</div>
    <div class="module-body">
      <div class="module-title">C2H Tracker Error</div>
    </div>
  </a>
  <a class="module-card" data-cat="network" href="11_debug_unexpected_err_cqe/">
    <div class="module-num">11</div>
    <div class="module-body">
      <div class="module-title">Unexpected Error CQE</div>
    </div>
  </a>
  <a class="module-card" data-cat="network" href="12_debug_cheatsheet/">
    <div class="module-num is-special" title="Cheatsheet">★</div>
    <div class="module-body">
      <div class="module-title">Debug Cheatsheet</div>
    </div>
  </a>
</div>
<!-- DV-SKOOL-MODULES-PART2:end -->

### 에러 ID prefix 빠른 인덱스

| Prefix | 컴포넌트 | 모듈 |
|--------|---------|-----|
| `E-DRV-TBERR-*` | `vrdma_driver` | [M09 CQ Poll Timeout](09_debug_cq_poll_timeout.md) |
| `F-CQHDL-TBERR-*` | `vrdma_cq_handler` | [M11 Unexpected Error CQE](11_debug_unexpected_err_cqe.md) |
| `E-SB-MATCH-*` | comparator (1side / 2side / imm) | [M08 Data Integrity](08_debug_data_integrity.md) |
| `F-C2H-MATCH-*` / `E-C2H-MATCH-*` | `vrdma_c2h_tracker` | [M10 C2H Tracker](10_debug_c2h_tracker.md) |

## 📖 참조 자료
- **Confluence — `RDMADV` space** — [Testbench Architecture](https://mangoboost.atlassian.net/wiki/spaces/RDMADV/pages/1224310992/Testbench+Architecture), [Debugging Cases](https://mangoboost.atlassian.net/wiki/spaces/RDMADV/pages/1334608001/Debugging+Cases) (source of truth)
- **`RDMA-TB/lib/`** — RDMA IP 검증 환경 본체 (`base/`, `ext/`, `external/`, `submodule/` 4-layer)
- **`RDMA-TB/lib/base/def/vrdma_defs.svh:75-88`** — H2C/C2H QID 단일 출처
- **[용어집](glossary.md)** — 29 terms (ISO 11179 형식)
- **[퀴즈 인덱스](quiz/index.md)** — 챕터별 학습 점검 (Bloom 단계 라벨)

<!-- DV-SKOOL-RELATED-TOPICS:start -->

## 🔗 관련 토픽
<div class="course-grid">
  <a class="course-card" href="https://humbleowl39.github.io/DV_SKOOL/rdma/">
    <div class="course-card-num">⚡ 자매</div>
    <div class="course-card-title">RDMA (IB & RoCEv2)</div>
    <div class="course-card-desc">프로토콜 / IBTA 스펙 / Verbs API</div>
  </a>
  <a class="course-card" href="https://humbleowl39.github.io/DV_SKOOL/uvm/">
    <div class="course-card-num">🧪 선수</div>
    <div class="course-card-title">UVM</div>
    <div class="course-card-desc">Agent / Sequence / Phase / TLM</div>
  </a>
  <a class="course-card" href="https://humbleowl39.github.io/DV_SKOOL/pcie/">
    <div class="course-card-num">🔌 관련</div>
    <div class="course-card-title">PCI Express</div>
    <div class="course-card-desc">QDMA bypass interface 의 모태</div>
  </a>
  <a class="course-card" href="https://humbleowl39.github.io/DV_SKOOL/" style="border-style:dashed;">
    <div class="course-card-num">🏠 HOME</div>
    <div class="course-card-title">DV SKOOL 홈</div>
    <div class="course-card-desc">전체 토픽 / 학습 경로 보기</div>
  </a>
</div>

<!-- DV-SKOOL-RELATED-TOPICS:end -->


--8<-- "abbreviations.md"
