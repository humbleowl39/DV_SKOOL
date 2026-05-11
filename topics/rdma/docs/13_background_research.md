# Module 13 — Background & Industry Research

<!-- DV-SKOOL-CH-CTX:start -->
<div class="chapter-context" data-cat="network">
  <a class="chapter-back" href="../">
    <span class="chapter-back-arrow">←</span>
    <span class="chapter-back-icon">⚡</span>
    <span class="chapter-back-text">RDMA</span>
  </a>
  <span class="chapter-divider">›</span>
  <span class="chapter-marker">Module 13</span>
</div>
<!-- DV-SKOOL-CH-CTX:end -->

<!-- DV-SKOOL-CH-TOC:start -->
<div class="page-toc">
  <span class="page-toc-label">목차</span>
  <a class="page-toc-link" href="#1-why-care-이-모듈이-왜-필요한가">1. Why care?</a>
  <a class="page-toc-link" href="#2-intuition-비유와-한-장-그림">2. Intuition</a>
  <a class="page-toc-link" href="#3-작은-예-sack-논문-한-편을-검증-시나리오로-옮기는-flow">3. 작은 예 — 논문 → 검증 시나리오</a>
  <a class="page-toc-link" href="#4-일반화-학습-연구-검증의-연결-지도">4. 일반화 — 연결 지도</a>
  <a class="page-toc-link" href="#5-디테일-paper-study-내부-정리-산업-트렌드-ai-servers-competitor">5. 디테일</a>
  <a class="page-toc-link" href="#6-흔한-오해-와-디버그-체크리스트">6. 흔한 오해 + 디버그 체크리스트</a>
  <a class="page-toc-link" href="#7-핵심-정리-key-takeaways">7. 핵심 정리</a>
</div>
<!-- DV-SKOOL-CH-TOC:end -->

!!! note "Internal — 본 모듈은 사내 *Other materials* (id=32080200), *Paper Study* (id=238716337), *AI Servers* (id=52199880), *RDMA for NRT* (id=1047199830) 트리의 발췌·요약입니다."
    각 논문/페이지의 본문은 Confluence 가 1차. 본 모듈은 **연결 지도 (signpost)** 역할.

!!! objective "학습 목표"
    이 모듈을 마치면:

    - **List** 사내 Paper Study 가 다루는 주요 주제 5 가지를 나열한다.
    - **Explain** Falcon · ECE · Programmable CC 가 무엇을 해결하려는지 한 문장으로 설명한다.
    - **Apply** 연구 논문의 핵심 아이디어를 RDMA-TB 검증 시나리오로 연결한다.
    - **Analyze** Multipath RDMA 와 packet spraying 이 IB RC 가정에 미치는 영향을 분석한다.
    - **Evaluate** 외부 spec / 논문 / 사내 구현 결정의 우선순위를 평가한다.

!!! info "사전 지식"
    - M07 (CC), M10 (UEC), M11 (RDMA-IP wrapper).

---

## 1. Why care? — 이 모듈이 왜 필요한가

RDMA 분야는 **spec 변경 속도가 빠릅니다** — IB Spec 1.4 → 1.7, RoCEv2, UEC v1, Falcon, Programmable CC, packet spraying 등이 1~2 년 간격으로 등장. 산업 동향을 추적하지 않으면 _현재 사내 IP 가 어디에 위치하는지_ 모르고, 검증 우선순위 결정이 _스펙_ 만 보고 의사결정하게 됩니다.

이 모듈은 _학습/연구/검증_ 의 연결 지도 — 새로 발견된 spec 변화나 논문 아이디어를 어디 검증 자산에 hook 할지 즉답 가능하게 합니다.

---

## 2. Intuition — 비유와 한 장 그림

!!! tip "💡 한 줄 비유 — 이 모듈 ≈ RDMA 분야의 _뉴스 룸_"
    매일 새로 발표되는 spec / 논문 / 산업 발표를 _내부 IP 와 검증 자산_ 에 맵핑하는 책상. 1차 출처는 Confluence (혹은 원본 spec/논문), 본 모듈은 _signpost_.

### 한 장 그림 — 입력 → 변환 → 검증

```
   [Spec / 논문 / 산업 발표]            [내부 IP / 정책]                 [DV / RDMA-TB]
   ──────────────────────────         ────────────────────             ──────────────────
   IBTA Annex A17 / A19               cc_module / MPE FLUSH            M07 / M05 §11
   UEC v1 PDS / SES                   (planning)                       M10
   Falcon paper (Google)              ref (competitor)                 M13 §3.1
   SACK / OOO 알고리즘                 m_sack_info                      M06 §13, M11 §2
   Multi-Path RDMA / packet spraying   AR mode                          M07 §11, M12 §3
   MPI / NCCL primer                  (UEC SES 매핑)                    M10 §2.2
   Programmable CC interface          cc_module 의 algorithm swap      M07 §9
   ECE (Enhanced Connection Est.)     RDMA-CM private data             M03 §9
```

### 왜 이런 매핑 자료를 따로 두는가 — Design rationale

산업 입력은 두 함정이 있음:

1. **"논문이 그렇게 하니까 우리도"** — 환경 (switch, NIC, fabric) 의존성이 큼. 같은 알고리즘이 사내 환경에서 같은 결과를 내지 않을 수 있음.
2. **"spec 만 보면 충분"** — 산업 동향이 향후 spec 의 _초기 우선순위_ 를 미리 알려줌. 무시하면 후행 비용 폭증.

연결 지도 형식이 이 둘 사이의 균형을 잡아줍니다 — _각 외부 입력 → 내부 자산 → 검증 항목_ 의 3 hop 으로 의사결정.

---

## 3. 작은 예 — SACK 논문 한 편을 검증 시나리오로 옮기는 flow

**입력**: "An Out-of-Order Packet Processing Algorithm of RoCE Based on Improved SACK" (Confluence id=42599274).

```
   1. 논문의 핵심 아이디어 추출
      "수신측이 받은 PSN 비트맵을 응답 패킷에 실어 송신측이 missing PSN 만 선택적으로 재전송"

   2. 사내 IP 매핑 확인
      → m_sack_info (152-bit) 가 selective ack vector 를 requester 측 completer 에 전달
      → completer_retry 가 SACK 기반 retry 결정
      (M11 §2 / M06 §13)

   3. spec 차이 확인
      → 표준 IB RC 는 strict in-order만 + Go-Back-N
      → SACK 는 spec 확장 (사내 옵션)
      → 호환성: SACK 미지원 peer 와 통신 시 fallback 필요

   4. 검증 시나리오 설계
      4a. 정상 시나리오:
          - traffic 송신
          - 일부 패킷 inject drop (예: PSN N+2 drop)
          - SACK 비트맵에 "N+2 missing" 표시되는지 검증
          - requester 가 PSN N+2 만 재전송 (N+3 재전송 안 함)
      4b. fallback 시나리오:
          - peer 가 SACK 미지원 advertise
          - sender 가 Go-Back-N 으로 회귀
      4c. corner case:
          - SACK 비트맵의 missing PSN 이 wrap 영역 걸침
          - 다중 packet drop (예: PSN N, N+5, N+10) 동시 missing
          - SACK 가 정상 ACK 와 같은 시점에 옴

   5. coverage 추가
      - sack 비트맵의 hit pattern 분포
      - missing PSN 수 1/2/4/N 별
      - fallback 발생 빈도

   6. RDMA-TB 위치 결정
      - lib/base/coverage/ → vrdma_packet_cov 에 SACK 필드 추가
      - lib/ext/component/reliability/ → 새 sequence 추가
      - 디버그 시 m_sack_info 를 monitor 가 캡처

   7. Confluence/PR 흐름
      - PR description 에 "이 코드는 id=42599274 논문의 §3.4 구현" 인용
      - coverage define sync meeting (M08 §14) 에 SACK cov 추가 합의
      - bitfile 통과 후 lab 에서 fio + adaptive routing 환경에서 검증
```

### 단계별 의미

| Step | 의미 |
|---|---|
| 1 | 논문의 _핵심 1줄_ 추출 — 검증 가능한 명제로 |
| 2 | 사내 IP 어디에 _이미_ 구현돼 있는지 / 새로 만들어야 하는지 결정 |
| 3 | spec 표준과 사내 확장의 _경계_ — fallback 필요한가? |
| 4 | 검증 시나리오 (정상 + fallback + corner) |
| 5 | coverage 추가 — 시나리오가 _확인됐다_ 는 증거 |
| 6 | RDMA-TB 디렉터리 결정 (base / ext / submodule) |
| 7 | PR / coverage sync meeting / lab validation |

!!! note "여기서 잡아야 할 두 가지"
    **(1) 논문 → 시나리오 mapping 시 fallback 시나리오 필수** — 사내 IP 만 SACK 지원해도 peer 가 미지원이면 fallback. 검증 안 하면 interop 사고.<br>
    **(2) Coverage define sync meeting 의 미팅 어젠다로** — 모듈 별 cov 추가는 격주 sync 에서 합의. 단독 PR 로 진행하면 누락 위험 (M08 §14).

---

## 4. 일반화 — 학습 → 연구 → 검증의 연결 지도

```
[Spec / Industry]                [Internal IP]              [DV / RDMA-TB]
─────────────────                ───────────────             ──────────────
IBTA Annex A17  ────▶ DCQCN  ───▶ cc_module (DCQCN)  ───▶  M07 §1, §3
IBTA Annex A19  ────▶ MPE    ───▶ FLUSH path        ───▶  M05 §11
UEC v1 PDS      ────▶ (TBD)  ───▶ (planning)         ───▶  M10
Falcon paper    ────▶ ref    ───▶ —                  ───▶  M13 §3.1
SACK paper      ────▶ algo   ───▶ m_sack_info       ───▶  M06 §13, M11 §2
Multi-Path RDMA ────▶ algo   ───▶ AR mode           ───▶  M07 §11, M12 §3
MPI primer      ────▶ model  ───▶ (UEC SES 매핑)      ───▶  M10 §2.2
```

3 hop 으로 의사결정:

1. 외부 입력의 핵심 1 줄 추출.
2. 사내 IP 의 어느 자산 (구현되어 있는 / 계획 / 미지원) 인지.
3. RDMA-TB 의 어느 모듈/coverage 에 hook.

---

## 5. 디테일 — Paper Study, 내부 정리, 산업 트렌드, AI Servers, Competitor

### 5.1 Paper Study — 주제별 인덱스

(Confluence: *Paper Study*, id=238716337)

#### AI Training (RDMA + DL)

- **Fast Distributed Deep Learning over RDMA** (id=240484819) — RDMA 가 DL training step time 에 미치는 영향, parameter server 패턴.
- **NetReduce: RDMA-Compatible In-Network Reduction for Distributed DNN Training Acceleration** (id=240484911) — switch 가 reduce 를 in-network 로 처리해 RDMA 트래픽 줄이기.

#### MultiPathing (multi-path RDMA)

- **Accelerating Distributed Deep Learning using Multi-Path RDMA in Data Center Networks** (id=238780460)
- **Achieving Low Latency for Multipath Transmission in RDMA Based Data Center Network** (id=238780482)
- **Challenging the Need for Packet Spraying in Large-Scale Distributed Training** (id=238683564) — packet spraying 의 한계.
- **Efficient User-Level Multi-Path Utilization in RDMA Networks** (id=238780504)
- **Multi-Path Transport for RDMA in Datacenters** (id=238683537)

검증 의의: multi-path 는 IB / RC 의 strict in-order 가정을 깨므로, **SACK 활성**과 **per-path PSN tracking** 이 동반돼야 한다 (M06 §13, M07 §11, M11).

#### Useful readings (AI-RNIC)

- **Useful readings for AI-RNIC** (id=252904171) — RDMA + AI 를 위한 산업 동향 / 백서 요약.

### 5.2 사내 정리 — 시작점

(Confluence: *Other materials*, id=32080200 의 자식들)

| 페이지 | 핵심 |
|---|---|
| **About PSN-related fields of CQE (DV spec delivery)** id=1330839982 | CQE 에 추가된 사내 디버그 필드 (M06 §12 참조) |
| **An Out-of-Order Packet Processing Algorithm of RoCE Based on Improved SACK** id=42599274 | SACK 기반 OOO 처리 (M06 §13 참조) |
| **Competitor survey** id=98500876 | 경쟁사 RNIC 기능 비교 |
| **ECE (Enhanced Connection Establishment)** id=265552106 | RDMA-CM 핸드셰이크 확장 (M03 §9 참조) |
| **Falcon specification** id=52953427 | Google 의 hardware reliable transport |
| **How to enable Adaptive Routing for CX** id=397967495 | (M07 §11, M12 §3 참조) |
| **Infiniband device attributes** id=134906105 | `ibv_query_device` 가 노출하는 cap 모음 |
| **MI325X mapping bdf and physical pcie slots** id=618660030 | (M12 §6 참조) |
| **MPI backgrounds** id=97550702 | MPI 통신 모델 — UEC SES 와 직접 연결 |
| **MSI-X study** id=23822539 | (M12 §6 참조) |
| **Programmable congestion control communication scheme** id=75759859 | programmable CC 인터페이스 |
| **Setup leaf-spine** id=421003291 | (M12 §3 참조) |
| **[On-boarding] Implement your toy example on RDMA project** id=126747747 | 신규 인원 토이 검증 |

### 5.3 산업 트렌드 — Falcon / Programmable CC / ECE

#### Falcon (Google)

- Hardware-offloaded reliable transport. PSP, swift CC, multipath 를 hardware 통합.
- 의의: RoCEv2 의 *PFC + DCQCN + RC* 스택을 한 단계 추상화. UEC PDS 와도 비교 대상.

#### Programmable CC

- 송신측 CC 를 firmware / hardware 가 정의된 inteface 로 swap 가능하게 만드는 추세 (Microsoft, Google, Nvidia).
- 사내 RDMA-IP 의 `cc_module` 도 동일 발상 — DCQCN / RTTCC / 향후 UET-CC 를 알고리즘 모듈로 분리.

#### ECE (Enhanced Connection Establishment)

- RDMA-CM 의 REQ/REP private data 영역에 **확장 기능 비트맵** 을 실어 양 단이 협상.
- 협상 항목: MPE 지원 여부, AETH variant, multipath 활성, atomic write 지원.
- 검증: ECE 협상이 실패할 때 fallback 동작 (legacy mode).

### 5.4 AI Servers / NRT / GPUBoost — 응용 환경

(Confluence: *AI Servers* id=52199880; *NVIDIA DGX* id=80708265; *RDMA for NRT* id=1047199830)

| 영역 | 핵심 | 검증 함의 |
|---|---|---|
| **AI Servers (DGX, MI325X)** | RCCL/NCCL 워크로드, GPU peer-memory | Large MR, IOVA 매핑, RCCL benchmark |
| **NRT fallback** | RDMA QP 미사용 경로 | NRT path 와 RDMA path 의 시맨틱 동일성 검증 |
| **GPUBoost spec** | 외부 사양 (M11 §7) | spec 의 cap 가 검증 capability 와 일치하는지 |

### 5.5 Competitor Survey — 무엇을 비교하는가

(Confluence: *Competitor survey*, id=98500876)

비교 축 (사내 자료에 따름):

- 지원 verbs / atomic / MPE / FLUSH.
- 최대 QP / MR 수, max_dest_rd_atomic.
- CC 알고리즘 (DCQCN / RTTCC / Swift / Falcon-style).
- Multipath 지원.
- SR-IOV VF 수.
- UEC 호환 (예고).

검증 의의: cap 조합 별로 *우리 IP 가 어디에 위치하는지* 를 파악하면, 검증 우선순위를 산업 기준에 맞춰 조정할 수 있다.

---

## 6. 흔한 오해 와 디버그 체크리스트

### 흔한 오해

!!! danger "❓ 오해 1 — '논문 결과가 사내 환경에서도 그대로 재현'"
    **실제**: 논문은 _특정 switch, NIC, fabric_ 환경에서의 결과. 같은 알고리즘이 사내 leaf-spine + Dell switch 에서는 다른 throughput 곡선이 나올 수 있음.<br>
    **왜 헷갈리는가**: 그래프가 명확해서.

!!! danger "❓ 오해 2 — '산업 동향이 spec 우선보다 강하다'"
    **실제**: 검증의 1차 truth 는 spec / 사내 design. 산업 동향은 _우선순위 조정_ 용 — 산업 다수가 같은 방향이면 spec 의 다음 버전이 그 방향으로 갈 가능성이 큼 (예: UEC).<br>
    **왜 헷갈리는가**: hyperscaler 발표가 화려해서.

!!! danger "❓ 오해 3 — 'Paper Study idea 는 검증 시 직접 인용해야'"
    **실제**: idea 는 _시나리오 설계 input_ 일 뿐. 검증의 ground truth 는 spec + 사내 design. 시나리오 description 에 인용은 허용 (PR 가독성).<br>
    **왜 헷갈리는가**: 학술 인용 문화.

!!! danger "❓ 오해 4 — 'Competitor 가 지원하는 cap 는 우리도 다 지원해야'"
    **실제**: cap 조합은 _전략 결정_. 모두 따라가면 칩 크기/timing 부담. survey 는 _우선순위 정렬_ 도구지 _to-do 리스트_ 가 아님.<br>
    **왜 헷갈리는가**: 표가 직관적이라 "다 채우자" 같은 느낌.

!!! danger "❓ 오해 5 — 'Falcon / UEC 같은 industry 입력은 다음 분기 작업'"
    **실제**: 일부는 _현재_ 작업에 영향 (cap 협상 시 ECE 활용, AR mode 검증 시 SACK 활성). 즉시 검증 시나리오에 hook 할 부분과 _향후 계획_ 부분을 구분.<br>
    **왜 헷갈리는가**: "spec 가 정식 출시되면 그때" 같은 단순화.

### 디버그 체크리스트 (이 모듈 내용으로 마주칠 함정)

| 증상 | 1차 의심 | 어디 보나 |
|---|---|---|
| 논문 idea 시나리오가 사내 IP 에서 동작 안 함 | 매핑 step 2 누락 (구현 안 됨) | M11 §2 의 wrapper 목록 |
| SACK 시나리오가 fallback 안 함 | fallback path 미구현 | peer SACK advertise 검증 |
| ECE 협상 실패 시 legacy 안 됨 | RDMA-CM private data 처리 부재 | M03 §9 의 CM 핸드셰이크 |
| Programmable CC 의 algorithm swap 안 됨 | cc_module 의 interface 분리 안 됨 | M07 §9 의 interface 분리 |
| Falcon / UEC 비교 자료에 사내 IP 가 없음 | competitor survey 갱신 안 됨 | id=98500876 의 최신 |
| Coverage define sync meeting 에 새 항목 누락 | meeting 어젠다에 추가 안 함 | M08 §14 의 sync 프로세스 |
| Lab 결과가 시뮬 결과와 다름 | 환경 (AR/SR-IOV/leaf-spine) 차이 | M12 §3, §4 의 환경 변수 |
| 새 idea 의 검증 위치 (base/ext/submodule) 모호 | M08 §10 의 결정 트리 미사용 | M08 의 분류 기준 |

---

## 7. 핵심 정리 (Key Takeaways)

- 사내 Paper Study 는 *AI training, multi-path, OOO/SACK* 의 3 축.
- Falcon · Programmable CC · ECE 는 산업 트렌드 — 사내 IP 의 향후 방향 정렬에 사용.
- AI Servers / NRT / GPUBoost 는 *응용 환경 → 검증 워크로드* 의 진입점.
- Competitor survey 는 cap 조합으로 우선순위 결정.
- 모든 산업 입력은 결국 **RDMA-TB 의 검증 항목** 에 매핑된다 (§4 의 표).

!!! warning "실무 주의점"
    - 논문의 결과는 *환경 (switch, NIC, fabric)* 에 강하게 의존. 동일 알고리즘이 사내 환경에서 같은 결과를 내지 않을 수 있음.
    - "산업이 그렇게 한다" 가 spec 우선 이유가 되지 않음 — 검증의 1차 truth 는 spec / 사내 design.
    - Paper Study 의 idea 를 검증 시나리오로 옮길 때는 **사내 IP capability 와의 매핑 표** 를 먼저 만든다.

---

## 다음 단계 — 코스 마무리

- [Quick Reference Card](09_quick_reference_card.md) 로 핵심 표 한 번 더 훑기.
- [용어집](glossary.md) 의 Appendix A/B/C 에서 사내 / UEC / 산업 용어 다시 확인.
- [퀴즈 13](quiz/13_background_research_quiz.md) 으로 이해도 점검.


--8<-- "abbreviations.md"
--8<-- "_inc/topic_abbr.md"
