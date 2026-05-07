# Module 05 — Quick Reference Card

<!-- DV-SKOOL-CH-CTX:start -->
<div class="chapter-context" data-cat="network">
  <a class="chapter-back" href="../">
    <span class="chapter-back-arrow">←</span>
    <span class="chapter-back-icon">📡</span>
    <span class="chapter-back-text">TOE</span>
  </a>
  <span class="chapter-divider">›</span>
  <span class="chapter-marker chapter-quickref-marker">★ Quick Reference</span>
</div>
<!-- DV-SKOOL-CH-CTX:end -->

<!-- DV-SKOOL-CH-TOC:start -->
<div class="page-toc">
  <span class="page-toc-label">목차</span>
  <a class="page-toc-link" href="#toe-한줄-요약">TOE 한줄 요약</a>
  <a class="page-toc-link" href="#핵심-정리">핵심 정리</a>
  <a class="page-toc-link" href="#면접-골든-룰">면접 골든 룰</a>
  <a class="page-toc-link" href="#이력서-연결">이력서 연결</a>
  <a class="page-toc-link" href="#tcp-핵심-수치">TCP 핵심 수치</a>
  <a class="page-toc-link" href="#offload-수준-비교">Offload 수준 비교</a>
  <a class="page-toc-link" href="#코스-마무리">코스 마무리</a>
</div>
<!-- DV-SKOOL-CH-TOC:end -->

!!! objective "사용 목적"
    참조용 치트시트.

!!! info "사전 지식"
    - [Module 01-04](01_tcp_ip_and_toe_concept.md)

## TOE 한줄 요약
```
TOE = TCP/IP 프로토콜 처리(Checksum/Segmentation/Retx/Flow Control)를 CPU에서 전용 HW로 Offload → CPU 부하 80-90% 감소, 라인 레이트 달성
```

---
!!! warning "실무 주의점 — LRO(Large Receive Offload)와 IP Fragment 혼용"
    **현상**: LRO를 활성화한 환경에서 IP Fragment 패킷이 유입되면 재조합 오류가 발생하거나, 이후 정상 TCP 세그먼트도 LRO로 묶이지 않는다.
    
    **원인**: LRO는 연속 TCP 세그먼트를 하나의 대형 버퍼로 합산하는 기능인데, IP Fragmented 패킷은 TCP 헤더가 첫 Fragment에만 있어 LRO 엔진이 연속성을 판단하지 못한다. 두 경로가 동일 수신 큐를 공유하면 상태 머신이 충돌한다.
    
    **점검 포인트**: IP Fragment 패킷과 일반 TCP 세그먼트가 교차하는 시나리오를 시뮬레이션에 포함. `lro_active` 플래그와 `ip_frag_in_progress` 플래그가 동시에 set 되는 사이클을 검출하는 SVA assertion 추가.

!!! tip "💡 이해를 위한 비유"
    **TOE 마스터 = stateful 흐름의 모든 분기 인지** ≈ **등기 우편의 모든 예외 케이스를 외운 베테랑**

    정상 / RTO / fast retransmit / SACK / congestion event / RST 의 동작을 즉시 그릴 수 있는 것이 마스터.

---

!!! danger "❓ 흔한 오해"
    **오해**: TOE 가 적용되면 항상 throughput ↑

    **실제**: TOE 가 효과 있는 워크로드 (small packet, many connection, CPU bound). large MTU + bulk transfer 에서는 jumbo + GSO 가 더 효과적.

    **왜 헷갈리는가**: "HW = 항상 빠름" 이라는 직관. 실제로는 workload-dependent.

## 핵심 정리

| 주제 | 핵심 포인트 |
|------|------------|
| 왜 TOE? | 100Gbps에서 CPU TCP 처리 → 코어 100% 점유 → 애플리케이션 불가 |
| HW/SW 분리 | Data Path(패킷마다) → HW, Control Path(연결당 1-2회) → SW |
| 5대 Offload | Checksum, Segmentation, Retransmission, Flow Control, Congestion |
| Connection Table | 4-tuple 해시로 O(1) 조회, 연결별 상태(Seq/ACK/Window/Timer) |
| TX Path | DMA → Segmentation → Header → Checksum → Retx 버퍼 → MAC |
| RX Path | MAC → Checksum 검증 → Conn Lookup → Seq 검증 → Reassembly → DMA |
| TCP FSM | 11개 상태, 모든 전이를 HW에서 정확 구현 필요 |
| DCMAC 연동 | AXI-Stream 인터페이스, 백프레셔, 에러 전파 |

---

## 면접 골든 룰

1. **왜 TOE**: "100Gbps에서 CPU가 TCP에 압도" — 성능 수치로 시작
2. **HW/SW 분리**: "빈도 높은 것 = HW, 드문 것 = SW" — 단순 원칙
3. **검증 난이도**: "네트워크의 비결정론적 특성" — 패킷 손실/OOO/지연 조합
4. **Coverage**: "TCP FSM 전이 + Error×Recovery 교차" — 구조적 커버리지
5. **DCMAC**: TOE와 MAC의 AXI-S 인터페이스 연동 검증 경험 강조

---

## 이력서 연결

| 항목 | 면접 질문 | 핵심 답변 |
|------|----------|----------|
| TOE 시나리오 개발 | "어떤 테스트를 추가했나?" | 복합 에러(Loss+OOO+Zero Window), DCMAC 연동 에러 |
| Coverage 확장 | "Coverage를 어떻게 확장했나?" | FSM 전이, Error×Recovery 교차, Congestion 상태 조합 |
| DCMAC 서브시스템 | "DCMAC과의 연동은?" | AXI-S E2E 무결성, 백프레셔, CRC 에러 전파 |
| 서버급 가속기 | "왜 중요한 IP인가?" | 100Gbps SmartNIC/DPU, CPU Offload 필수 |

---

## TCP 핵심 수치

```
MSS (Maximum Segment Size): 1460 bytes (Ethernet MTU 1500 - IP(20) - TCP(20))
Jumbo Frame: MTU 9000 → MSS 8960
Window Scale: 최대 1GB Window (RFC 7323)
RTO 초기값: 1초 (RFC 6298), 이후 RTT 기반 동적 조정
Fast Retransmit: Dup ACK 3개
TIME_WAIT: 2 × MSL (120초)
```

## Offload 수준 비교

```
Checksum Offload ⊂ TSO/LRO ⊂ TOE ⊂ RDMA (TCP 우회)
(부분)            (중간)      (전체)  (다른 범주)
```

---

## 코스 마무리

[퀴즈](quiz/index.md) · [용어집](glossary.md) · 다음: [Ethernet DCMAC](../../ethernet_dcmac/), [UVM](../../uvm/).

<div class="chapter-nav">
  <a class="nav-prev" href="../04_toe_dv_methodology/">
    <div class="nav-label">◀ 이전</div>
    <div class="nav-title">TOE DV 검증 전략</div>
  </a>
  <a class="nav-next" href="../quiz/">
    <div class="nav-label">다음 ▶</div>
    <div class="nav-title">퀴즈로 이동</div>
  </a>
</div>
