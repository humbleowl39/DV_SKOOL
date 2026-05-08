# RDMA (InfiniBand & RoCEv2)

<!-- DV-SKOOL-HERO:start -->
<div class="topic-hero" data-cat="network">
  <div class="topic-hero-mark">⚡</div>
  <div class="topic-hero-body">
    <div class="topic-hero-title">RDMA (InfiniBand & RoCEv2)</div>
    <p class="topic-hero-sub">InfiniBand & RoCEv2, QP/MR, DV 전략</p>
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

## 🎯 학습 목표
- **Explain** RDMA 가 왜 만들어졌고 — kernel bypass / zero-copy / OS bypass — 가 어떤 의미인지 설명할 수 있다.
- **Diagram** InfiniBand 패킷 스택 (LRH/GRH/BTH/Payload/ICRC/VCRC) 과 RoCEv2 매핑 (Eth/IP/UDP/BTH) 을 그릴 수 있다.
- **Trace** QP FSM (Reset → Init → RTR → RTS → SQD/SQErr/Err) 과 PSN/ACK/NAK/Retry 흐름을 추적할 수 있다.
- **Apply** Verbs API (Memory Registration, Post Send/Recv, Poll CQ) 를 시나리오에 맞춰 사용할 수 있다.
- **Evaluate** PFC/ECN/DCQCN 기반 Congestion Control 과 Local ACK timeout/RNR/R-Key error 의 처리 전략을 평가할 수 있다.
- **Plan** RDMA 검증 환경(`vrdmatb`) 의 환경/agent/scoreboard 구조를 기반으로 vplan + coverage 전략을 설계할 수 있다.

## 📋 사전 지식
- TCP/IP 와 Ethernet 기본
- DMA, PCIe 기본 (memory-mapped IO)
- UVM 1.2 / SystemVerilog / VCS / mrun (DV 모듈 한정)

## 🗺️ 개념 맵
<div class="concept-dag">
  <div class="concept-dag-title">개념 의존성 — 순서대로 학습 권장</div>
  <div class="concept-dag-row">
    <a class="concept-dag-node" href="01_rdma_motivation/">
      <span class="concept-dag-node-num">M01</span>
      <span class="concept-dag-node-title">RDMA 동기</span>
    </a>
    <span class="concept-dag-arrow">→</span>
    <a class="concept-dag-node" href="02_ib_protocol_stack/">
      <span class="concept-dag-node-num">M02</span>
      <span class="concept-dag-node-title">IB Stack</span>
    </a>
    <span class="concept-dag-arrow">→</span>
    <a class="concept-dag-node" href="03_rocev2/">
      <span class="concept-dag-node-num">M03</span>
      <span class="concept-dag-node-title">RoCEv2</span>
    </a>
    <span class="concept-dag-arrow">→</span>
    <a class="concept-dag-node" href="04_service_types_qp/">
      <span class="concept-dag-node-num">M04</span>
      <span class="concept-dag-node-title">Service & QP</span>
    </a>
  </div>
  <div class="concept-dag-row">
    <a class="concept-dag-node" href="05_memory_model/">
      <span class="concept-dag-node-num">M05</span>
      <span class="concept-dag-node-title">Memory Model</span>
    </a>
    <span class="concept-dag-arrow">→</span>
    <a class="concept-dag-node" href="06_data_path/">
      <span class="concept-dag-node-num">M06</span>
      <span class="concept-dag-node-title">Data Path</span>
    </a>
    <span class="concept-dag-arrow">→</span>
    <a class="concept-dag-node" href="07_congestion_error/">
      <span class="concept-dag-node-num">M07</span>
      <span class="concept-dag-node-title">CC & Error</span>
    </a>
    <span class="concept-dag-arrow">→</span>
    <a class="concept-dag-node" href="08_rdma_tb_dv/">
      <span class="concept-dag-node-num">M08</span>
      <span class="concept-dag-node-title">RDMA-TB DV</span>
    </a>
  </div>
  <div class="concept-dag-row">
    <span class="concept-dag-arrow">↪</span>
    <a class="concept-dag-node" href="09_quick_reference_card/">
      <span class="concept-dag-node-num">Ref</span>
      <span class="concept-dag-node-title">Quick Reference</span>
    </a>
  </div>
  <div class="concept-dag-row">
    <a class="concept-dag-node" href="10_ultraethernet/">
      <span class="concept-dag-node-num">M10</span>
      <span class="concept-dag-node-title">Ultraethernet</span>
    </a>
    <span class="concept-dag-arrow">→</span>
    <a class="concept-dag-node" href="11_gpuboost_rdma_ip/">
      <span class="concept-dag-node-num">M11</span>
      <span class="concept-dag-node-title">GPUBoost / IP HW</span>
    </a>
    <span class="concept-dag-arrow">→</span>
    <a class="concept-dag-node" href="12_fpga_proto_manuals/">
      <span class="concept-dag-node-num">M12</span>
      <span class="concept-dag-node-title">FPGA Proto / Manuals</span>
    </a>
    <span class="concept-dag-arrow">→</span>
    <a class="concept-dag-node" href="13_background_research/">
      <span class="concept-dag-node-num">M13</span>
      <span class="concept-dag-node-title">Background</span>
    </a>
  </div>
  <div class="concept-dag-legend">각 노드 = 모듈 (클릭하여 이동) · 화살표(→) = 선수 지식 흐름</div>
</div>

## 📚 학습 모듈
<!-- DV-SKOOL-MODULES:start -->
<div class="module-grid">
  <a class="module-card" data-cat="network" href="01_rdma_motivation/">
    <div class="module-num">01</div>
    <div class="module-body">
      <div class="module-title">RDMA 동기와 핵심 모델</div>
    </div>
  </a>
  <a class="module-card" data-cat="network" href="02_ib_protocol_stack/">
    <div class="module-num">02</div>
    <div class="module-body">
      <div class="module-title">InfiniBand 프로토콜 스택</div>
    </div>
  </a>
  <a class="module-card" data-cat="network" href="03_rocev2/">
    <div class="module-num">03</div>
    <div class="module-body">
      <div class="module-title">RoCEv2: Ethernet 위의 RDMA</div>
    </div>
  </a>
  <a class="module-card" data-cat="network" href="04_service_types_qp/">
    <div class="module-num">04</div>
    <div class="module-body">
      <div class="module-title">Service Types & QP FSM</div>
    </div>
  </a>
  <a class="module-card" data-cat="network" href="05_memory_model/">
    <div class="module-num">05</div>
    <div class="module-body">
      <div class="module-title">Memory Model: PD, MR, L_Key/R_Key, IOVA</div>
    </div>
  </a>
  <a class="module-card" data-cat="network" href="06_data_path/">
    <div class="module-num">06</div>
    <div class="module-body">
      <div class="module-title">Data Path Operations</div>
    </div>
  </a>
  <a class="module-card" data-cat="network" href="07_congestion_error/">
    <div class="module-num">07</div>
    <div class="module-body">
      <div class="module-title">Congestion Control & Error Handling</div>
    </div>
  </a>
  <a class="module-card" data-cat="network" href="08_rdma_tb_dv/">
    <div class="module-num">08</div>
    <div class="module-body">
      <div class="module-title">RDMA-TB 검증 환경 & DV 전략</div>
    </div>
  </a>
  <a class="module-card" data-cat="network" href="09_quick_reference_card/">
    <div class="module-num is-special" title="Quick Reference">★</div>
    <div class="module-body">
      <div class="module-title">Quick Reference Card</div>
    </div>
  </a>
  <a class="module-card" data-cat="network" href="10_ultraethernet/">
    <div class="module-num">10</div>
    <div class="module-body">
      <div class="module-title">Ultraethernet (UEC)</div>
    </div>
  </a>
  <a class="module-card" data-cat="network" href="11_gpuboost_rdma_ip/">
    <div class="module-num">11</div>
    <div class="module-body">
      <div class="module-title">GPUBoost / RDMA-IP HW Architecture</div>
    </div>
  </a>
  <a class="module-card" data-cat="network" href="12_fpga_proto_manuals/">
    <div class="module-num">12</div>
    <div class="module-body">
      <div class="module-title">FPGA Prototyping & Lab Manuals</div>
    </div>
  </a>
  <a class="module-card" data-cat="network" href="13_background_research/">
    <div class="module-num">13</div>
    <div class="module-body">
      <div class="module-title">Background & Industry Research</div>
    </div>
  </a>
</div>
<!-- DV-SKOOL-MODULES:end -->

## 📖 참조 자료
- **InfiniBand Architecture Specification, Volume 1, Release 1.7** — IBTA, 2023-07-11
- **Annex A17: RoCEv2 — RDMA over Converged Ethernet v2** — IBTA
- **`RDMA-TB/`** — 사내 RDMA 2.0 verification environment
- **`PROTOCOL_RULES.md`** — IB Spec 1.7 must-rule 카탈로그 (1079개 규칙)
- **`ROCEV2_RULE_APPLICABILITY.md`** — IB 규칙의 RoCEv2 적용 여부 분류

<!-- DV-SKOOL-RELATED-TOPICS:start -->

## 🔗 관련 토픽
<div class="course-grid">
  <a class="course-card" href="https://humbleowl39.github.io/DV_SKOOL/pcie/">
    <div class="course-card-num">🔌 관련</div>
    <div class="course-card-title">PCI Express</div>
    <div class="course-card-desc">TLP/DLLP, LTSSM, SR-IOV/CXL</div>
  </a>
  <a class="course-card" href="https://humbleowl39.github.io/DV_SKOOL/ethernet_dcmac/">
    <div class="course-card-num">🌐 관련</div>
    <div class="course-card-title">Ethernet DCMAC</div>
    <div class="course-card-desc">이더넷 MAC + DCMAC DV</div>
  </a>
  <a class="course-card" href="https://humbleowl39.github.io/DV_SKOOL/toe/">
    <div class="course-card-num">📡 관련</div>
    <div class="course-card-title">TOE</div>
    <div class="course-card-desc">TCP/IP Offload Engine</div>
  </a>
  <a class="course-card" href="https://humbleowl39.github.io/DV_SKOOL/" style="border-style:dashed;">
    <div class="course-card-num">🏠 HOME</div>
    <div class="course-card-title">DV SKOOL 홈</div>
    <div class="course-card-desc">전체 토픽 / 학습 경로 보기</div>
  </a>
</div>

<!-- DV-SKOOL-RELATED-TOPICS:end -->


--8<-- "abbreviations.md"
--8<-- "_inc/topic_abbr.md"
