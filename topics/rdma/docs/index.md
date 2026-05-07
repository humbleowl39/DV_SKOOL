# RDMA (InfiniBand & RoCEv2)

> **Remote Direct Memory Access 마스터 코스** — InfiniBand 스펙(IB Vol1 r1.7), RoCEv2 Annex17, 그리고 실제 RDMA 검증 환경(`RDMA-TB`)을 한 번에.

<div class="course-header">
  <div class="course-stats">
    <div class="stat-item"><strong>8</strong>개 모듈 + Quick Ref</div>
    <div class="stat-item"><strong>심화 (Advanced)</strong> 난이도</div>
  </div>
</div>

## 이 코스에서 얻는 것

- **Explain** RDMA 가 왜 만들어졌고 — kernel bypass / zero-copy / OS bypass — 가 어떤 의미인지 설명할 수 있다.
- **Diagram** InfiniBand 패킷 스택 (LRH/GRH/BTH/Payload/ICRC/VCRC) 과 RoCEv2 매핑 (Eth/IP/UDP/BTH) 을 그릴 수 있다.
- **Trace** QP FSM (Reset → Init → RTR → RTS → SQD/SQErr/Err) 과 PSN/ACK/NAK/Retry 흐름을 추적할 수 있다.
- **Apply** Verbs API (Memory Registration, Post Send/Recv, Poll CQ) 를 시나리오에 맞춰 사용할 수 있다.
- **Evaluate** PFC/ECN/DCQCN 기반 Congestion Control 과 Local ACK timeout/RNR/R-Key error 의 처리 전략을 평가할 수 있다.
- **Plan** RDMA 검증 환경(`vrdmatb`) 의 환경/agent/scoreboard 구조를 기반으로 vplan + coverage 전략을 설계할 수 있다.

## 사전 지식

- TCP/IP 와 Ethernet 기본
- DMA, PCIe 기본 (memory-mapped IO)
- UVM 1.2 / SystemVerilog / VCS / mrun (DV 모듈 한정)

## 🗺️ 학습 경로

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
  <div class="concept-dag-legend">각 노드 = 모듈 (클릭하여 이동) · 화살표(→) = 선수 지식 흐름</div>
</div>

## 학습 모듈

<div class="course-grid">
  <a class="course-card" href="01_rdma_motivation/">
    <div class="course-card-num">Module 01</div>
    <div class="course-card-title">RDMA 동기와 핵심 모델</div>
    <div class="course-card-desc">Kernel bypass, zero-copy, Verbs, IB ↔ iWARP ↔ RoCE 계보</div>
  </a>
  <a class="course-card" href="02_ib_protocol_stack/">
    <div class="course-card-num">Module 02</div>
    <div class="course-card-title">InfiniBand 프로토콜 스택</div>
    <div class="course-card-desc">5계층, LRH/GRH/BTH/Payload/ICRC/VCRC, VL/SL</div>
  </a>
  <a class="course-card" href="03_rocev2/">
    <div class="course-card-num">Module 03</div>
    <div class="course-card-title">RoCEv2 — Ethernet 위의 RDMA</div>
    <div class="course-card-desc">Eth/IP/UDP(4791)/BTH 매핑, IB ↔ RoCEv2 차이</div>
  </a>
  <a class="course-card" href="04_service_types_qp/">
    <div class="course-card-num">Module 04</div>
    <div class="course-card-title">Service Types & QP FSM</div>
    <div class="course-card-desc">RC/UC/UD/XRC, QP 상태 전이</div>
  </a>
  <a class="course-card" href="05_memory_model/">
    <div class="course-card-num">Module 05</div>
    <div class="course-card-title">Memory Model</div>
    <div class="course-card-desc">PD, MR, L_Key/R_Key, IOVA, MMU/PTW/TLB</div>
  </a>
  <a class="course-card" href="06_data_path/">
    <div class="course-card-num">Module 06</div>
    <div class="course-card-title">Data Path Operations</div>
    <div class="course-card-desc">SEND/WRITE/READ/ATOMIC, Opcode, PSN, ACK/NAK</div>
  </a>
  <a class="course-card" href="07_congestion_error/">
    <div class="course-card-num">Module 07</div>
    <div class="course-card-title">Congestion & Error Handling</div>
    <div class="course-card-desc">PFC/ECN/DCQCN, Timeout/RNR/R-Key, QP recovery</div>
  </a>
  <a class="course-card" href="08_rdma_tb_dv/">
    <div class="course-card-num">Module 08</div>
    <div class="course-card-title">RDMA-TB 검증 환경 & DV 전략</div>
    <div class="course-card-desc">vrdmatb env, agent, vplan, scoreboard, coverage</div>
  </a>
  <a class="course-card" href="09_quick_reference_card/">
    <div class="course-card-num">Quick Ref</div>
    <div class="course-card-title">Quick Reference Card</div>
    <div class="course-card-desc">Opcode/header/state/error 한 장 요약</div>
  </a>
</div>

## 참조 자료

- **InfiniBand Architecture Specification, Volume 1, Release 1.7** — IBTA, 2023-07-11
- **Annex A17: RoCEv2 — RDMA over Converged Ethernet v2** — IBTA
- **`RDMA-TB/`** — 사내 RDMA 2.0 verification environment
- **`PROTOCOL_RULES.md`** — IB Spec 1.7 must-rule 카탈로그 (1079개 규칙)
- **`ROCEV2_RULE_APPLICABILITY.md`** — IB 규칙의 RoCEv2 적용 여부 분류
