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
</div>

## 📚 학습 모듈

### 1부 — 아키텍처 (Module 01-07)

| 모듈 | 핵심 내용 | 핵심 파일 |
|------|----------|----------|
| [M01 TB Overview](01_tb_overview.md) | Multi-node TB top, env 계층 | `lib/base/component/env/vrdmatb_top_env.svh` |
| [M02 Component 계층](02_component_hierarchy.md) | 11 디렉토리(config / pool / agent / data_env / dma_env / network_env / …) | `lib/base/component/` |
| [M03 Phase & Test Flow](03_phase_test_flow.md) | UVM phase, default sequence, 시퀀서 계층 | `vrdma_top_sequence`, `vrdma_init_seq` |
| [M04 Analysis Port Topology](04_analysis_port_topology.md) | `issued_wqe_ap` / `completed_wqe_ap` / `cqe_ap` / `qp_reg_ap` / `mr_reg_ap` | `vrdma_driver.svh:56-61` |
| [M05 Extension 4원칙](05_extension_principles.md) | Open-Closed / Interface / DRY / Stateless | Confluence Adding New Components |
| [M06 Error Handling Path](06_error_handling_path.md) | `isErrQP` / `expected_error` / static `err_enabled` | `vrdma_driver`, `vrdma_cq_handler`, comparator/tracker |
| [M07 H2C / C2H QID Reference](07_h2c_c2h_qid_map.md) | 10가지 QID 정의 + 채널 매핑 | `lib/base/def/vrdma_defs.svh:75-88` |

### 2부 — 디버깅 케이스 (Module 08-12)

| 모듈 | 케이스 | 대표 에러 ID |
|------|------|-----------|
| [M08 Data Integrity Error](08_debug_data_integrity.md) | 1side / 2side / IMM compare 실패 | `E-SB-MATCH-0001~0005` |
| [M09 CQ Poll Timeout](09_debug_cq_poll_timeout.md) | CQE 미생성 → polling 타임아웃 | `E-DRV-TBERR-0001/0002` |
| [M10 C2H Tracker Error](10_debug_c2h_tracker.md) | PA 매칭 실패 / ordering 위반 / 크기 초과 | `F-C2H-MATCH-0001~0005`, `E-C2H-MATCH-0001` |
| [M11 Unexpected Error CQE](11_debug_unexpected_err_cqe.md) | 예상치 못한 에러 CQE → DUT 버그 의심 | `F-CQHDL-TBERR-0003` |
| [M12 Debug Cheatsheet](12_debug_cheatsheet.md) | 통합 디버그 cheatsheet | (요약) |

## 📖 참조 자료
- Confluence space `RDMADV` — Testbench Architecture / Debugging Cases (Source of truth)
- Code base: `/home/jaehyeok.lee/RDMA/RDMA-TB/lib/`
- 용어 정의: [용어집](glossary.md)
- 학습 점검: [퀴즈 인덱스](quiz/index.md)
