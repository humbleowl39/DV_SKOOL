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
  <a class="page-toc-link" href="#1-why-care-이-카드를-언제-쓰나">1. Why care?</a>
  <a class="page-toc-link" href="#2-intuition-비유와-한-장-그림">2. Intuition</a>
  <a class="page-toc-link" href="#3-작은-예-가장-자주-나오는-시나리오-1-개">3. 작은 예 — 자주 쓰는 시나리오 표</a>
  <a class="page-toc-link" href="#4-일반화-카드의-축과-사용법">4. 일반화 — 카드의 축</a>
  <a class="page-toc-link" href="#5-디테일-요약-표-수치-면접-룰-이력서">5. 디테일 — 요약/수치/면접/이력서</a>
  <a class="page-toc-link" href="#6-흔한-오해-와-언제-카드를-넘어서야-하나">6. 흔한 오해 + 언제 카드를 넘어서야 하나</a>
  <a class="page-toc-link" href="#7-핵심-정리-key-takeaways">7. 핵심 정리</a>
</div>
<!-- DV-SKOOL-CH-TOC:end -->

!!! objective "사용 목적"
    - **Recall** TOE 의 5 대 기능 / 핵심 수치 / FSM 11 상태 / Offload 스펙트럼을 즉시 인출한다.
    - **Apply** 면접 / 리뷰 / 디버그 미팅에서 한 줄로 요약 표현을 사용한다.
    - **Identify** 어느 모듈 (01–04) 으로 돌아가서 깊이 봐야 할지를 카드로 판단한다.
    - **Justify** TOE 가 적합한 워크로드와 부적합한 워크로드를 즉시 구분한다.

!!! info "사전 지식"
    - [Module 01-04](01_tcp_ip_and_toe_concept.md)

---

## 1. Why care? — 이 카드를 언제 쓰나

이 카드는 **5 분 컨텍스트 스위치** 를 위한 것입니다. 면접 직전, 리뷰 회의 준비, 디버그 회의에서 "TOE 의 ssthresh 가 뭐였더라?" 같은 순간 즉시 인출하기 위한 압축. 이 카드의 한 줄로 부족하면 해당 module (01–04) 로 돌아가는 _index_ 역할.

이 카드를 건너뛰면 _개념 회수 비용_ 이 매번 높아져, 실무에서 모듈을 다시 통독해야 합니다. 반대로 이 카드를 외워 두면 일상 대화에서 즉시 "TOE 는 stateful offload 라서 connection table 이 SRAM/DRAM tier 야" 같은 대답이 가능.

---

## 2. Intuition — 비유와 한 장 그림

!!! tip "💡 한 줄 비유"
    **TOE 마스터** ≈ **등기 우편의 모든 예외 케이스를 외운 베테랑**.<br>
    정상 / RTO / Fast Retransmit / SACK / Congestion Event / RST 의 동작을 _즉시 그릴 수 있는 것_ 이 마스터의 정의.

### 한 장 그림 — TOE 의 모든 것을 한 페이지에

```
   ┌─── Why TOE? ──────────────────────────────────────────────────┐
   │ 100Gbps 라인레이트에서 CPU 가 TCP 처리 → 코어 100% → 앱 정지   │
   │ → Stateful HW offload 로 CPU 부하 80–90% 감소, ~µs latency   │
   └─────────────────────────────────────────────────────────────────┘

   ┌─── HW/SW 분리 ────────────────────────────────────────────────┐
   │ 빈도 높은 Data Path  →  HW (TOE)                               │
   │   Checksum / Segmentation / ACK / Retx / Flow / Cong            │
   │ 드문 Control Path    →  SW (CPU)                                │
   │   socket() / connect() / accept() / close() / setsockopt()      │
   └─────────────────────────────────────────────────────────────────┘

   ┌─── 5 대 기능 ──────────────────────────────────────────────────┐
   │ ① Checksum (1 cycle/word)                                       │
   │ ② Segmentation/Reassembly (TSO/LRO + OOO buffer)                │
   │ ③ Retransmission (RTO timer + Fast Retx + SACK)                 │
   │ ④ Flow Control (Window 기반)                                     │
   │ ⑤ Congestion Control (Reno/NewReno/Cubic)                       │
   └─────────────────────────────────────────────────────────────────┘

   ┌─── 검증 4 축 ──────────────────────────────────────────────────┐
   │ Protocol / Functional / Performance / Error Recovery           │
   │   ↑                                                             │
   │   Reference Model + Reactive Network Agent + SVA + Coverage    │
   └─────────────────────────────────────────────────────────────────┘
```

### 왜 이 카드가 필요한가 — Design rationale

5 모듈의 핵심을 _한 장_ 으로 누르면 회수 비용이 0 에 가까워집니다. 표 형태가 _긴 산문_ 보다 정보 밀도가 높고, 모듈 간 _참조 매트릭스_ 로 즉시 deep-dive 가 가능. 이 카드는 _컨텐츠 자체_ 가 아니라 _컨텐츠로의 인덱스_.

---

## 3. 작은 예 — 가장 자주 나오는 시나리오 1 개

가장 자주 쓰는 시나리오를 한 표로:

| 상황 | 한 줄 답변 | Deep-dive |
|---|---|---|
| "TOE 가 뭐예요?" | "TCP/IP 의 stateful HW offload — CPU 부하 80–90 % 감소, 100 Gbps 라인레이트, ~µs latency" | [M01](01_tcp_ip_and_toe_concept.md) |
| "TOE 와 TSO 차이?" | "TSO 는 segmentation 만, TOE 는 connection state 까지 — TSO ⊂ TOE" | [M01 §5.6](01_tcp_ip_and_toe_concept.md#56-toe-적용-후-효과) |
| "Connection 100 만 개 어떻게?" | "Hot 은 SRAM, cold 는 DRAM 의 LRU swap. 4-tuple hash O(1) lookup" | [M02 §5.5](02_toe_architecture.md#55-메모리-아키텍처-버퍼와-테이블-배치) |
| "RTO timer 100 만 개 어떻게?" | "Hashed Timing Wheel — tick 당 _현재 슬롯_ 만 검사 → O(1)" | [M02 §5.4](02_toe_architecture.md#54-타이머-관리-아키텍처-수백만-연결의-rto) |
| "Fast Retransmit 언제?" | "Dup ACK 3 개 도착 시 RTO 만료 기다리지 않고 즉시 재전송 + cwnd halve" | [M03 §5.3](03_toe_key_functions.md#53-retransmission-재전송) |
| "RTO 어떻게 계산?" | "RFC 6298 — SRTT/RTTVAR EWMA, RTO = SRTT + 4×RTTVAR. α=1/8, β=1/4 → bit shift" | [M03 §5.3](03_toe_key_functions.md#53-retransmission-재전송) |
| "Window Scale 왜 필요?" | "헤더 16 비트 = 64 KB 한도. 100 Gbps × 1 ms RTT = 12.5 MB BDP → 부족. Scale 로 최대 1 GB" | [M03 §5.6](03_toe_key_functions.md#56-tcp-options-toe-가-처리해야-하는-확장) |
| "Reactive Agent 가 뭐?" | "Monitor 가 DUT 출력 캡처 → Responder 가 _보고나서_ ACK/SYN-ACK 만듦. Stateful 프로토콜은 pre-programmed 불가" | [M04 §5.4](04_toe_dv_methodology.md#54-network-agent-설계-에러-주입) |
| "TOE 검증 4 축?" | "Protocol / Functional / Performance / Error Recovery — 하나라도 빠지면 미완성" | [M04 §4.1](04_toe_dv_methodology.md#41-검증-4-축) |
| "SVA 가 vacuous pass 라는데?" | "antecedent 가 한 번도 발생 안 함 → cover property 의 hit 로 확인" | [M04 §5.3](04_toe_dv_methodology.md#53-sva-systemverilog-assertions-프로토콜-준수-검증) |

!!! note "여기서 잡아야 할 두 가지"
    **(1) 한 줄 답변의 끝에 "왜" 또는 "어디" 가 들어 있다** — 단순 정의가 아니라 _이유_ 또는 _hook 위치_ 를 포함. <br>
    **(2) 카드는 _깊이의 시작_ 이지 _끝_ 이 아니다** — 한 줄로 답한 후 deep-dive 링크로 넘어가는 게 정상 흐름.

---

## 4. 일반화 — 카드의 축과 사용법

### 4.1 카드의 4 축

| 축 | 무엇 | 사용 시점 |
|---|---|---|
| **개념 (What)** | TOE 정의, HW/SW 분리, 5 대 기능 | "TOE 가 뭐예요" 류의 일반 질문 |
| **수치 (Numbers)** | MSS 1460, RTO_min 1 s, TIME_WAIT 2 MSL=120 s | spec / config / 면접 수치 질문 |
| **분류 (Compare)** | Checksum ⊂ TSO ⊂ TOE, Reno vs Cubic | "X 와 Y 차이" 질문 |
| **검증 (DV)** | 4 축 / Coverage / SVA / Reactive | 검증 미팅 / 회귀 결과 리뷰 |

### 4.2 언제 어느 축을 쓰나

```
   질문 유형 → 카드 축 매핑
   ─────────────────────────────────────────────────
   "이게 뭐예요?"         → 개념 축 (What)
   "정확한 값?"           → 수치 축 (Numbers)
   "X 와 Y 차이?"          → 분류 축 (Compare)
   "어떻게 검증했어?"      → 검증 축 (DV)
   "왜 이 결정?"          → 개념 축 + Module deep-dive
```

### 4.3 카드 → Module 매핑 (참조 매트릭스)

| 카드 항목 | 해당 Module |
|---|---|
| TOE 한 줄 정의, Offload 스펙트럼 | [M01](01_tcp_ip_and_toe_concept.md) |
| TX/RX path, Connection Table, Timer Wheel, Memory hierarchy | [M02](02_toe_architecture.md) |
| 5 대 기능, RTO 공식, Cubic, Options | [M03](03_toe_key_functions.md) |
| UVM env, Reference, Scoreboard, SVA, Coverage | [M04](04_toe_dv_methodology.md) |

---

## 5. 디테일 — 요약 표 / 수치 / 면접 룰 / 이력서

### 5.1 TOE 한 줄 요약

```
TOE = TCP/IP 프로토콜 처리 (Checksum / Segmentation / Retx / Flow Control)
       를 CPU 에서 전용 HW 로 Offload
       → CPU 부하 80–90 % 감소, 라인 레이트 달성
```

### 5.2 핵심 정리 표

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

### 5.3 TCP 핵심 수치

```
MSS (Maximum Segment Size): 1460 bytes (Ethernet MTU 1500 - IP(20) - TCP(20))
Jumbo Frame: MTU 9000 → MSS 8960
Window Scale: 최대 1GB Window (RFC 7323)
RTO 초기값: 1초 (RFC 6298), 이후 RTT 기반 동적 조정
Fast Retransmit: Dup ACK 3개
TIME_WAIT: 2 × MSL (120초)
```

### 5.4 Offload 수준 비교

```
Checksum Offload ⊂ TSO/LRO ⊂ TOE ⊂ RDMA (TCP 우회)
(부분)            (중간)      (전체)  (다른 범주)
```

### 5.5 면접 골든 룰

1. **왜 TOE**: "100 Gbps 에서 CPU 가 TCP 에 압도" — 성능 수치로 시작
2. **HW/SW 분리**: "빈도 높은 것 = HW, 드문 것 = SW" — 단순 원칙
3. **검증 난이도**: "네트워크의 비결정론적 특성" — 패킷 손실/OOO/지연 조합
4. **Coverage**: "TCP FSM 전이 + Error×Recovery 교차" — 구조적 커버리지
5. **DCMAC**: TOE 와 MAC 의 AXI-S 인터페이스 연동 검증 경험 강조

### 5.6 이력서 연결

| 항목 | 면접 질문 | 핵심 답변 |
|------|----------|----------|
| TOE 시나리오 개발 | "어떤 테스트를 추가했나?" | 복합 에러 (Loss + OOO + Zero Window), DCMAC 연동 에러 |
| Coverage 확장 | "Coverage 를 어떻게 확장했나?" | FSM 전이, Error × Recovery 교차, Congestion 상태 조합 |
| DCMAC 서브시스템 | "DCMAC 과의 연동은?" | AXI-S E2E 무결성, 백프레셔, CRC 에러 전파 |
| 서버급 가속기 | "왜 중요한 IP 인가?" | 100 Gbps SmartNIC/DPU, CPU Offload 필수 |

### 5.7 실무 주의점 — LRO 와 IP Fragment 혼용

!!! warning "실무 주의점 — LRO(Large Receive Offload)와 IP Fragment 혼용"
    **현상**: LRO를 활성화한 환경에서 IP Fragment 패킷이 유입되면 재조합 오류가 발생하거나, 이후 정상 TCP 세그먼트도 LRO로 묶이지 않는다.

    **원인**: LRO는 연속 TCP 세그먼트를 하나의 대형 버퍼로 합산하는 기능인데, IP Fragmented 패킷은 TCP 헤더가 첫 Fragment에만 있어 LRO 엔진이 연속성을 판단하지 못한다. 두 경로가 동일 수신 큐를 공유하면 상태 머신이 충돌한다.

    **점검 포인트**: IP Fragment 패킷과 일반 TCP 세그먼트가 교차하는 시나리오를 시뮬레이션에 포함. `lro_active` 플래그와 `ip_frag_in_progress` 플래그가 동시에 set 되는 사이클을 검출하는 SVA assertion 추가.

---

## 6. 흔한 오해 와 언제 카드를 넘어서야 하나

### 흔한 오해

!!! danger "❓ 오해 1 — 'TOE 가 적용되면 항상 throughput ↑'"
    **실제**: TOE 가 효과 있는 워크로드 (small packet, many connection, CPU bound). large MTU + bulk transfer 에서는 jumbo + GSO 가 더 효과적. <br>
    **왜 헷갈리는가**: "HW = 항상 빠름" 이라는 직관. 실제로는 workload-dependent.

!!! danger "❓ 오해 2 — 'Quick Reference 만 외우면 충분'"
    **실제**: 카드는 _hook_ 일 뿐. 한 줄 답변 뒤에 "_왜 그렇게?_" 가 오면 module 본문으로 가야 합니다. 카드만으로는 deep-dive 질문에 답 못 함. <br>
    **왜 헷갈리는가**: 시간 압박 시 카드만 읽고 끝내려는 유혹.

!!! danger "❓ 오해 3 — '면접 골든 룰 5 개를 다 기억하면 합격'"
    **실제**: 골든 룰은 _시작 문장_. 면접관은 보통 follow-up 으로 "_왜 그게 성립?_" 을 묻습니다. 그 깊이가 진짜 평가 대상. <br>
    **왜 헷갈리는가**: "외운 답변 = 합격" 이라는 false confidence.

!!! danger "❓ 오해 4 — '카드의 수치는 절대값이다'"
    **실제**: MSS 1460 은 Ethernet 표준 가정 — Jumbo (MTU 9000) 환경에선 8960. RTO_min 1 초는 RFC 권장이지만 데이터센터 환경에선 200 ms 까지 줄이는 경우도. _가정 맥락_ 까지 같이 외워야 함. <br>
    **왜 헷갈리는가**: 표가 _절대값_ 으로 보여서.

!!! danger "❓ 오해 5 — '카드를 외우면 검증 능력이 생긴다'"
    **실제**: 카드는 _개념 회수_ 용. 검증 능력은 module 04 의 4 축 (Protocol / Functional / Performance / Error) 을 _실제 TB 에 적용_ 한 경험으로만 생김. <br>
    **왜 헷갈리는가**: "지식 = 기술" 이라는 흔한 혼동.

### 언제 카드를 넘어서야 하나 — Deep-dive trigger

| 신호 | 어느 module 로 |
|---|---|
| "왜 stateful 이 stateless 보다 비싼지 정량 비교" | [M01 §5](01_tcp_ip_and_toe_concept.md#5-디테일-tcpip-스택-tcp-기능-toe-효과) |
| "Connection Table 의 hash 충돌 처리 디테일" | [M02 §5.3](02_toe_architecture.md#53-connection-table-엔트리-구조와-lookup) |
| "Timer Wheel 의 cascade 동작" | [M02 §5.4](02_toe_architecture.md#54-타이머-관리-아키텍처-수백만-연결의-rto) |
| "Cubic 의 W_max 회복 곡선 수식" | [M03 §5.5](03_toe_key_functions.md#55-congestion-control-혼잡-제어) |
| "Karn's Algorithm 정확한 정의" | [M03 §5.3](03_toe_key_functions.md#53-retransmission-재전송) |
| "Reactive Agent 의 Driver/Monitor/Responder 분리" | [M04 §5.4](04_toe_dv_methodology.md#54-network-agent-설계-에러-주입) |
| "SVA 의 vacuous pass 회피 구체 코드" | [M04 §5.3](04_toe_dv_methodology.md#53-sva-systemverilog-assertions-프로토콜-준수-검증) |

---

## 7. 핵심 정리 (Key Takeaways)

- **카드의 정의**: TOE 5 모듈의 핵심을 한 페이지에 압축한 _인덱스_.
- **5 분 컨텍스트 스위치**: 면접/리뷰/디버그 직전에 즉시 회수.
- **참조 매트릭스**: 카드 → Module 깊이 매핑으로 deep-dive 진입.
- **사용 시점**: 한 줄 답변 후 follow-up 시 module 본문으로 이동.
- **외우지 말 것**: 카드 자체보다 _가정 맥락_ 과 _왜_ — 그게 면접/실무의 평가 대상.

!!! warning "실무 주의점"
    - **카드는 starting point**: 실제 토론에서 한 줄 답변 후 _왜_ 가 따라옴. 그때 module 본문 지식이 필요.
    - **수치는 가정 의존**: MSS, RTO_min, TIME_WAIT 등은 _표준 가정_ 의 값. 환경별로 다를 수 있음.
    - **검증 = 적용**: 카드의 검증 4 축 / Coverage / SVA 는 _읽기_ 가 아니라 _구현_ 으로만 체화.

---

## 코스 마무리

5 모듈 (Concept → Architecture → Key Functions → DV → Quick Reference) 을 완주했습니다. 다음 단계:

- 📝 [퀴즈 / 면접 자기검증](quiz/index.md)
- 📚 [용어집](glossary.md)
- 🔗 인접 코스: [Ethernet DCMAC](../../ethernet_dcmac/), [UVM](../../uvm/), [RDMA](../../rdma/)

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


--8<-- "abbreviations.md"
