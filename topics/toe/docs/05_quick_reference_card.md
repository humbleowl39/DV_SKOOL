# TOE — Quick Reference Card

<div class="learning-meta">
  <span class="meta-badge meta-level-advanced">📊 Advanced</span>
</div>

## TOE 한줄 요약
```
TOE = TCP/IP 프로토콜 처리(Checksum/Segmentation/Retx/Flow Control)를 CPU에서 전용 HW로 Offload → CPU 부하 80-90% 감소, 라인 레이트 달성
```

---

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

<div class="chapter-nav">
  <a class="nav-prev" href="04_toe_dv_methodology.md">
    <div class="nav-label">◀ 이전</div>
    <div class="nav-title">TOE DV 검증 전략</div>
  </a>
  <a class="nav-next" href="quiz/index.md">
    <div class="nav-label">다음 ▶</div>
    <div class="nav-title">퀴즈로 이동</div>
  </a>
</div>
