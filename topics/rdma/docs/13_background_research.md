# Module 13 — Background & Industry Research

!!! note "Internal — 본 모듈은 사내 *Other materials* (id=32080200), *Paper Study* (id=238716337), *AI Servers* (id=52199880), *RDMA for NRT* (id=1047199830) 트리의 발췌·요약입니다."
    각 논문/페이지의 본문은 Confluence 가 1차. 본 모듈은 **연결 지도 (signpost)** 역할.

## 학습 목표 (Bloom)

- (Remember) 사내 Paper Study 가 다루는 주요 주제 5 가지를 나열한다.
- (Understand) Falcon · ECE · Programmable CC 가 무엇을 해결하려는지 한 문장으로 설명한다.
- (Apply) 연구 논문의 핵심 아이디어를 RDMA-TB 검증 시나리오로 연결한다.
- (Analyze) Multipath RDMA 와 packet spraying 이 IB RC 가정에 미치는 영향을 분석한다.
- (Evaluate) 외부 spec / 논문 / 사내 구현 결정의 우선순위를 평가한다.

## 사전 지식

- M07 (CC), M10 (UEC), M11 (RDMA-IP wrapper).

---

## 1. Paper Study — 주제별 인덱스

(Confluence: *Paper Study*, id=238716337)

### 1.1 AI Training (RDMA + DL)

- **Fast Distributed Deep Learning over RDMA** (id=240484819) — RDMA 가 DL training step time 에 미치는 영향, parameter server 패턴.
- **NetReduce: RDMA-Compatible In-Network Reduction for Distributed DNN Training Acceleration** (id=240484911) — switch 가 reduce 를 in-network 로 처리해 RDMA 트래픽 줄이기.

### 1.2 MultiPathing (multi-path RDMA)

- **Accelerating Distributed Deep Learning using Multi-Path RDMA in Data Center Networks** (id=238780460)
- **Achieving Low Latency for Multipath Transmission in RDMA Based Data Center Network** (id=238780482)
- **Challenging the Need for Packet Spraying in Large-Scale Distributed Training** (id=238683564) — packet spraying 의 한계.
- **Efficient User-Level Multi-Path Utilization in RDMA Networks** (id=238780504)
- **Multi-Path Transport for RDMA in Datacenters** (id=238683537)

검증 의의: multi-path 는 IB / RC 의 strict in-order 가정을 깨므로, **SACK 활성**과 **per-path PSN tracking** 이 동반돼야 한다 (M06 §13, M07 §11, M11).

### 1.3 Useful readings (AI-RNIC)

- **Useful readings for AI-RNIC** (id=252904171) — RDMA + AI 를 위한 산업 동향 / 백서 요약.

---

## 2. 사내 정리 — 시작점

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

---

## 3. 산업 트렌드 — Falcon / Programmable CC / ECE

### 3.1 Falcon (Google)

- Hardware-offloaded reliable transport. PSP, swift CC, multipath 를 hardware 통합.
- 의의: RoCEv2 의 *PFC + DCQCN + RC* 스택을 한 단계 추상화. UEC PDS 와도 비교 대상.

### 3.2 Programmable CC

- 송신측 CC 를 firmware / hardware 가 정의된 inteface 로 swap 가능하게 만드는 추세 (Microsoft, Google, Nvidia).
- 사내 RDMA-IP 의 `cc_module` 도 동일 발상 — DCQCN / RTTCC / 향후 UET-CC 를 알고리즘 모듈로 분리.

### 3.3 ECE (Enhanced Connection Establishment)

- RDMA-CM 의 REQ/REP private data 영역에 **확장 기능 비트맵** 을 실어 양 단이 협상.
- 협상 항목: MPE 지원 여부, AETH variant, multipath 활성, atomic write 지원.
- 검증: ECE 협상이 실패할 때 fallback 동작 (legacy mode).

---

## 4. AI Servers / NRT / GPUBoost — 응용 환경

(Confluence: *AI Servers* id=52199880; *NVIDIA DGX* id=80708265; *RDMA for NRT* id=1047199830)

| 영역 | 핵심 | 검증 함의 |
|---|---|---|
| **AI Servers (DGX, MI325X)** | RCCL/NCCL 워크로드, GPU peer-memory | Large MR, IOVA 매핑, RCCL benchmark |
| **NRT fallback** | RDMA QP 미사용 경로 | NRT path 와 RDMA path 의 시맨틱 동일성 검증 |
| **GPUBoost spec** | 외부 사양 (M11 §7) | spec 의 cap 가 검증 capability 와 일치하는지 |

---

## 5. Competitor Survey — 무엇을 비교하는가

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

## 6. 학습 → 연구 → 검증 의 연결 지도

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

---

## 핵심 정리 (Key Takeaways)

- 사내 Paper Study 는 *AI training, multi-path, OOO/SACK* 의 3 축.
- Falcon · Programmable CC · ECE 는 산업 트렌드 — 사내 IP 의 향후 방향 정렬에 사용.
- AI Servers / NRT / GPUBoost 는 *응용 환경 → 검증 워크로드* 의 진입점.
- Competitor survey 는 cap 조합으로 우선순위 결정.
- 모든 산업 입력은 결국 **RDMA-TB 의 검증 항목** 에 매핑된다 (§6 의 표).

!!! warning "실무 주의점"
    - 논문의 결과는 *환경 (switch, NIC, fabric)* 에 강하게 의존. 동일 알고리즘이 사내 환경에서 같은 결과를 내지 않을 수 있음.
    - "산업이 그렇게 한다" 가 spec 우선 이유가 되지 않음 — 검증의 1차 truth 는 spec / 사내 design.
    - Paper Study 의 idea 를 검증 시나리오로 옮길 때는 **사내 IP capability 와의 매핑 표** 를 먼저 만든다.

---

## 다음 단계

- [Quick Reference Card](09_quick_reference_card.md) 로 핵심 표 한 번 더 훑기 (코스 마무리).
- [용어집](glossary.md) 의 Appendix A/B/C 에서 사내 / UEC / 산업 용어 다시 확인.
- [퀴즈 13](quiz/13_background_research_quiz.md) 으로 이해도 점검.


--8<-- "abbreviations.md"
--8<-- "_inc/topic_abbr.md"
