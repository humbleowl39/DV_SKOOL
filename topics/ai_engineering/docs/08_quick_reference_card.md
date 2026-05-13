# Module 08 — Quick Reference Card

<!-- DV-SKOOL-CH-CTX:start -->
<div class="chapter-context" data-cat="applied">
  <a class="chapter-back" href="../">
    <span class="chapter-back-arrow">←</span>
    <span class="chapter-back-icon">🤖</span>
    <span class="chapter-back-text">AI Engineering</span>
  </a>
  <span class="chapter-divider">›</span>
  <span class="chapter-marker chapter-quickref-marker">★ Quick Reference</span>
</div>
<!-- DV-SKOOL-CH-CTX:end -->

<!-- DV-SKOOL-CH-TOC:start -->
<div class="page-toc">
  <span class="page-toc-label">목차</span>
  <a class="page-toc-link" href="#1-why-care-cheat-sheet-가-필요한-순간">1. Why care?</a>
  <a class="page-toc-link" href="#2-intuition-4축-즉답-모델">2. Intuition</a>
  <a class="page-toc-link" href="#3-작은-예-이-카드를-펼치는-3-시나리오">3. 작은 예 — 펼치는 3 시나리오</a>
  <a class="page-toc-link" href="#4-일반화-7개-모듈을-한-줄로">4. 일반화 — 7 모듈 한 줄 요약</a>
  <a class="page-toc-link" href="#5-디테일-cheat-sheet-스택-rag-인터뷰">5. 디테일</a>
  <a class="page-toc-link" href="#6-흔한-오해-와-카드-사용-체크리스트">6. 흔한 오해 + 사용 체크리스트</a>
  <a class="page-toc-link" href="#7-핵심-정리-key-takeaways">7. 핵심 정리</a>
</div>
<!-- DV-SKOOL-CH-TOC:end -->

!!! objective "학습 목표"
    이 모듈을 마치면:

    - **Recall** 7개 모듈의 핵심 키워드를 30초 이내에 떠올릴 수 있다.
    - **Apply** 면접/리뷰에서 30초 이내 답변 가능한 답변 템플릿을 갖춘다.
    - **Evaluate** 자기 시스템의 부족한 영역 (LLM 선택, RAG 품질, Agent 통제) 을 cheat sheet 와 비교 평가할 수 있다.
    - **Compare** RAG / Fine-tuning / Prompt 의 선택 기준을 보안 · 최신성 · 비용 축으로 비교할 수 있다.

!!! info "사전 지식"
    - [Module 01 ~ 07](01_llm_fundamentals.md) 모두 학습 완료.

---

## 1. Why care? — Cheat Sheet 가 필요한 순간

이 모듈은 _학습_ 이 아니라 **인덱스** 입니다. 7개 모듈에서 흩어진 약 200개의 키워드 / 표 / 결정 기준을 _한 페이지_ 에 압축하는 목적.

세 가지 상황에서 펼치게 됩니다 — **(1) 면접 30분 전**, **(2) 코드 리뷰 / 디자인 리뷰에서 30초 답변 필요**, **(3) 자기 시스템의 갭 진단**. 이 셋 모두 "처음 배우는 자리" 가 아니라 "이미 한 번 본 것을 빠르게 다시 꺼내는 자리". 그래서 이 카드는 _설명_ 하지 않고 _포인터_ 합니다.

---

## 2. Intuition — "4축 즉답" 모델

!!! tip "💡 한 줄 비유"
    **AI Engineering 마스터** = **AI 솔루션 아키텍트 — 어떤 비즈니스 case 든 적합한 조합 30초 내 답변**.<br>
    4축 (Prompt / RAG / Agent / Eval) 의 어디를 어떻게 박을지 즉시 그리는 것. 모든 case 를 RAG 로 풀려고 하면 hammer-nail 함정.

### 한 장 그림 — 4축 + 결정 매트릭스

```
              ┌──────── 4축 즉답 ────────┐
              │                          │
   Prompt ◀──┼── 빠름, 가벼움, 비결정성  │
   RAG    ◀──┼── 최신성, 보안 (로컬)     │
   Agent  ◀──┼── 다단계, 도구 사용       │
   Eval   ◀──┼── 계측 + sign-off         │
              │                          │
              └──────────────────────────┘
                          │
   ┌──────────────────────┴──────────────────────────┐
   │   결정 기준                                       │
   │   ─────────                                       │
   │   보안 → RAG (로컬 모델 + FAISS)                 │
   │   최신성 → RAG (학습 후에 등장한 정보)            │
   │   도메인 적응 → Fine-tune (LoRA/QLoRA)            │
   │   빠름 → Prompt 만                                │
   │   복잡 워크플로 → Agent (ReAct/Reflection)        │
   │   품질 보장 → Eval (자동 검증 후단)               │
   └───────────────────────────────────────────────────┘
```

### 왜 이렇게 설계됐는가 — Cheat sheet 의 design rationale

면접 답변과 리뷰 답변은 **30초** 가 한계. 그 안에 (1) 결정 기준 하나, (2) 사례 숫자 하나, (3) 트레이드오프 하나를 말할 수 있어야 합니다. 이 카드는 그 세 가지 _만_ 담고 _이유 설명은 본문 모듈에 link_ 합니다.

---

## 3. 작은 예 — 이 카드를 펼치는 3 시나리오

이 카드의 _용도_ 를 step-by-step 으로. 셋 다 30초 안에 답변까지 가는 흐름.

| 시나리오 | 트리거 | 카드의 어느 섹션 | 출력 |
|---|---|---|---|
| **A. 면접 — "RAG vs Fine-tune 언제?"** | 면접관 질문 | §5.1 면접 골든 룰 #1, §2 결정 매트릭스 | "보안·최신성 → RAG / 도메인 적응 → Fine-tune / 빠름 → Prompt. DVCon 에서는 보안+최신성으로 RAG 선택" |
| **B. 리뷰 — "이 agent 가 왜 느린가?"** | 동료의 PR 리뷰 | §5.5 RAG 파이프라인, §6 사용 체크리스트 | "retrieval Top-K 가 너무 큼 + LLM context 폭증. Top-K 를 5 로 줄이고 re-ranking 추가" |
| **C. 자가 진단 — "내 시스템에 뭐가 빠졌나"** | 분기 회고 | §4 한 줄 요약 표 + §5.3 이력서 매트릭스 | "Eval 단계 (계측) 없음 → LangSmith 같은 tracing 도입 우선순위" |

각 시나리오 모두 "본문을 _안 _ 펼치고 카드만 보고 답" 이 목표. 본문 모듈은 _이미 학습_ 한 상태 가정.

!!! note "여기서 잡아야 할 두 가지"
    **(1) 이 카드는 _학습 자료_ 가 아니라 _꺼내 쓰는 도구_** — 첫 학습은 Module 01~07. 이 카드는 이미 한 번 학습한 사람이 _다시 빠르게_ 꺼내는 용도.<br>
    **(2) 답변 패턴: "기준 1개 + 숫자 1개 + 트레이드오프 1개"** — 30초 안에 이 셋이 나와야 마스터.

---

## 4. 일반화 — 7개 모듈을 한 줄로

### 4.1 핵심 키워드 표

| 주제 | 핵심 포인트 |
|------|------------|
| LLM | Transformer + Self-Attention, 다음 토큰 예측, Context Window 한계 |
| LLM 추론 최적화 | KV Cache (재계산 방지), GQA (메모리 절약), Flash Attention (IO 최적화) |
| Positional Encoding | Sinusoidal → Learned → **RoPE** (현재 표준) → ALiBi |
| MoE | Sparse Activation: 총 파라미터 ↑ 연산 ↓, Mixtral 8x7B 대표적 |
| Quantization | FP16 → INT8 → INT4, AWQ/GPTQ 로 정밀도 유지, 로컬 배포 핵심 |
| Scaling Laws | Chinchilla: D≈20N 최적, 50B+ 에서 코드 생성 의미 있는 품질 |
| Prompt Eng. | Role + Context + Task + Constraint + Format = 좋은 프롬프트 |
| 고급 추론 | CoT → Self-Consistency (다수결) → ToT (탐색) → Prompt Chaining (단계) |
| Embedding | Contrastive Learning 으로 학습, MTEB 벤치마크로 평가 |
| FAISS | Meta 의 벡터 검색 라이브러리, 로컬 실행, GPU 가속 |
| RAG | 검색 (Retrieve) → 증강 (Augment) → 생성 (Generate) |
| Agent | LLM + Tool (Function Calling) + Plan + Memory, ReAct 패턴 |
| Agent 고급 | Reflection (자기검증), Multi-Agent (협업), MCP (도구 표준) |
| Fine-tuning | LoRA/QLoRA 로 0.1~1% 파라미터만 학습, DPO/ORPO 로 정렬 |
| 전략 선택 | 보안 → RAG, 최신성 → RAG, 도메인 적응 → Fine-tune, 빠름 → Prompt |

### 4.2 결정 트리 — "내 case 는 무엇을 써야 하나"

```
   질문: 사내 IP 가 입력에 포함되나?
        │
        ├─ YES ──▶ 로컬 모델 (INT4 quantized) + FAISS 필수
        │           │
        │           └─ 한 번만 답 필요? → Prompt
        │              여러 문서 검색? → RAG
        │              여러 도구 호출? → Agent
        │
        └─ NO  ──▶ 클라우드 API 가능
                    │
                    └─ 비용 민감? → 작은 모델 + Prompt
                       정확성 민감? → Frontier 모델 + RAG
                       도메인 적응? → Fine-tune (LoRA)
```

이 결정 트리가 §5.5 의 4축 즉답을 시각화한 형태.

---

## 5. 디테일 — Cheat Sheet 스택, RAG, 인터뷰

### 5.1 면접 골든 룰

1. **RAG vs Fine-tuning**: "보안, 최신성, 비용" 으로 판단 — DVCon 에서 RAG 를 선택한 3가지 이유
2. **Hallucination**: "생성 코드는 반드시 컴파일 + 시뮬레이션 검증" — AI 맹신 금지
3. **FAISS 선택 이유**: "로컬 (보안) + 라이브러리 (통합) + GPU (속도)"
4. **Hybrid Extraction**: "IP-XACT (구조) + IP Spec (시맨틱) = DVCon 의 핵심 차별점"
5. **AI = 증강**: "대체가 아닌 증강 (Augmentation) — 인간 판단 + AI 처리"
6. **정량적 성과**: 숫자로 말하라 — 293개 Gap, 2.75%, 96.30% Human Oversight
7. **보안**: "반도체 IP 는 클라우드 전송 불가 → 로컬 모델 (INT4 양자화) + FAISS"
8. **3단계 비전**: "현재 (보조) → 단기 (자율 디버그) → 장기 (자율 V-Plan)"
9. **LLM 내부 이해**: KV Cache, GQA, Flash Attention — 왜 추론이 느린지/빠른지 설명 가능
10. **Agent 패턴**: Function Calling → ReAct → Reflection → Multi-Agent 발전 흐름

### 5.2 흔한 실수와 올바른 답변

| 실수 | 왜 위험한가 | 올바른 답변 |
|------|-----------|-----------|
| "AI 는 더 큰 모델이면 다 해결" | 핵심 미이해 | "task 분해 + RAG 품질 + Agent loop guard 가 더 결정적" |
| "RAG = 항상 정답" | 만능 도구화 | "RAG 는 retrieval 품질이 상한. chunk size / Top-K 가 깨지면 RAG 도 무너짐" |
| "AI 가 DV 엔지니어 대체" | 책임 모델 오해 | "Sign-off 는 인간. AI 는 throughput 증폭" |
| Eval 단계 생략 | 운영 부채 | "도입 첫날부터 metric 수집 파이프라인 필수" |
| 인용 없이 결과만 | 패턴 매칭 | "DVCon 293개 (2.75%), 96.30% human oversight 같은 정량 숫자 인용" |

### 5.3 이력서 연결 포인트

| 이력서 항목 | 면접 질문 | 핵심 답변 포인트 |
|------------|----------|----------------|
| DVCon 2025 Publication | "논문의 핵심 기여는?" | Hybrid Extraction + RAG/FAISS → 293개 Gap 발견 (2.75%) |
| RAG & FAISS | "왜 FAISS 를 선택했나?" | 보안 (로컬) + 통합 (라이브러리) + 성능 (GPU) |
| LLM-Based Test Gen | "어떻게 테스트를 생성했나?" | Few-shot ICL + Structured Output → mrun 명령어 + V-Plan bin |
| Hybrid Extraction | "IP-XACT 만으로 부족한 이유는?" | 시맨틱 부족 → 보안 테스트 누락 → IP Spec 으로 보완 |
| DAC 2026 (submitted) | "AI 자동화를 어떻게 했나?" | Agent 패턴: RTL 변경감지 → 코드생성 → 컴파일검증 루프 |
| AI Expert 자격 | "AI 전문성을 DV 에 어떻게 적용하나?" | 이론 (삼성 + 서울대) → 실무 (DVCon) → 확장 (DAC) |
| 96.30% Human Oversight | "이 수치의 의미는?" | 인간 실수가 검증 갭의 주 원인 → 자동화 필요성 정량 증명 |

### 5.4 면접 스토리 흐름 (Technical Challenge #3)

```
1. 문제 인식
   "SoC 통합에서 공통 IP 검증 항목이 반복적으로 누락되었다 (3-5%)"

2. 기존 시도의 한계
   "JIRA/Confluence 수동 추적 → 규모 확장 시 한계
    IP-XACT 자동화 → 시맨틱 부족 (보안 테스트 누락)"

3. 해결 (3단계 파이프라인)
   "(1) Hybrid Extraction: IP-XACT (구조) + IP Spec (시맨틱)
    (2) RAG + FAISS: 대규모 IP DB 인덱싱 + 의미 검색
    (3) LLM: Few-shot 으로 테스트 명령어 + V-Plan bin 자동 생성"

4. 성과 (정량적)
   "Project A: 293개 (2.75%), Project B: 216개 (4.99%) Gap 발견
    인간 실수: 96.30%, New IP/Feature 누락 40% 감소"

5. 학술 기여 + 확장
   "DVCon 2025 Publication → DAC 2026 (Agent 확장)"
```

### 5.5 기술 스택 빠른 참조

```
LLM 모델:    Claude / GPT-4 / Llama (로컬)
Embedding:   OpenAI ada / BGE / Sentence-BERT (로컬)
Vector DB:   FAISS (로컬, GPU 가속)
RAG 프레임워크: LangChain / 직접 구현
Agent:       LangChain Agent / Claude Agent SDK
Fine-tuning: LoRA / QLoRA (Hugging Face + PEFT)
언어:        Python (AI) + SystemVerilog (DV)
```

### 5.6 RAG 파이프라인 빠른 참조

```
오프라인 (Indexing):
  문서 수집 → 파싱 → Chunking → Embedding → FAISS Index

온라인 (Query):
  쿼리 → 임베딩 → FAISS 검색 (Top-K) → [Re-ranking] → 프롬프트 삽입 → LLM → 답변

핵심 파라미터:
  Chunk Size:  512~1024 토큰
  Overlap:     50~100 토큰
  Top-K:       3~10 (보통 5)
  Embedding:   768~3072 차원
  FAISS Index: IndexIVFFlat (중규모), IndexFlatL2 (소규모)
```

### 5.7 다음 학습 추천

| 주제 | 이유 |
|------|------|
| LangChain/LangGraph 실습 | RAG + Agent 구현 프레임워크 |
| LoRA Fine-tuning 실습 | DV 도메인 모델 적응 |
| Evaluation Framework | RAG 품질 평가 자동화 (RAGAS 등) |
| Multi-Agent System | 복잡한 DV 워크플로 자동화 |

---

## 6. 흔한 오해 와 카드 사용 체크리스트

### 흔한 오해

!!! danger "❓ 오해 1 — 'AI 는 더 큰 모델이면 다 해결'"
    **실제**: Frontier 모델조차 hallucination, context 한계, retrieval 부재로 실패. 모델 ↑ 보다 "task 분해 + RAG 품질 + Agent loop guard" 가 더 효과적.<br>
    **왜 헷갈리는가**: AI 발전이 "model 크기" 로 매년 보고되어 "크기 = 능력" 단순화.

!!! danger "❓ 오해 2 — 'cheat sheet 면 학습 끝'"
    **실제**: 이 카드는 _이미 학습한 사람_ 의 인덱스. 처음 보는 사람에게는 7개 모듈을 모두 학습한 후에야 useful. 카드만 외우면 면접에서 "왜?" 한 번에 무너집니다.<br>
    **왜 헷갈리는가**: 키워드 표가 짧고 직관적이라 "이거면 된다" 라는 착각.

!!! danger "❓ 오해 3 — 'RAG > Fine-tune 항상'"
    **실제**: 도메인 특수 어휘 (예: 사내 IP 명, 사내 약어) 가 많으면 fine-tune 이 더 빠르고 정확. RAG 는 retrieval 이 잘못된 chunk 를 가져오면 hallucination 으로 빠짐. **선택 기준은 보안 / 최신성 / 도메인 깊이 의 균형**.

!!! danger "❓ 오해 4 — '계측은 나중에 해도 됨'"
    **실제**: Agent 파이프라인을 계측 없이 운영하면 어느 단계에서 실패했는지 사후 추적 불가 → 장애 대응 시간이 수 배 길어짐. **도입 첫날부터 tracing 필요**.

### 카드 사용 체크리스트

| 상황 | 펼치는 섹션 | 30초 내 답변 패턴 |
|---|---|---|
| 면접 — "RAG vs Fine-tune" | §2 결정 매트릭스 + §5.1 #1 | "보안/최신성 → RAG, 도메인 → Fine-tune, 빠름 → Prompt. 내 사례는 X" |
| 면접 — "AI 가 DV 대체?" | §5.2 실수 #3 | "Sign-off 는 인간. AI 는 throughput 증폭" |
| 면접 — "FAISS 왜?" | §5.1 #3 | "로컬 (보안) + 라이브러리 (통합) + GPU (속도)" |
| 리뷰 — "agent 느림" | §5.6 RAG 파라미터 | "Top-K 줄이고 re-ranking. Chunk size 점검" |
| 자가진단 — "갭 점검" | §4.1 표 vs 내 시스템 | "Eval / 계측 / Agent guard 셋 중 빠진 것 찾기" |
| 회고 — "도입 성과" | §5.3 정량 항목 | "Gap N 개, time saved X%, defect ↓ Y%" |

---

!!! warning "실무 주의점 — 계측 없는 Agent 배포는 운영 부채"
    **현상**: Agent 파이프라인을 계측 없이 운영하면, 어느 단계 (Retrieval, LLM, Tool 호출) 에서 실패가 발생했는지 사후에 추적할 수 없어 장애 대응 시간이 수 배 길어진다.

    **원인**: Agent 는 단일 API 와 달리 다단계 호출 체인이므로, 단계별 latency·성공률·비용을 별도로 수집하지 않으면 전체 응답 시간만 측정된다.

    **점검 포인트**: LangSmith, Langfuse 등의 tracing 도구나 자체 미들웨어로 `retrieval_time`, `llm_time`, `tool_call_count`, `total_cost` 를 스텝 단위로 로깅. 도입 첫날부터 대시보드를 구성해 비용 이상 증가 알림을 설정.

---

## 7. 핵심 정리 (Key Takeaways)

- **LLM 호출만이 끝이 아니다** — Prompt → RAG → Agent → Eval 의 4축으로 구성.
- **품질의 상한 = 검색 품질** — RAG 의 retrieval 단계가 제일 먼저 깨진다.
- **Agent loop 는 비용 폭주에 취약** — max-step / budget guard 필수.
- **계측 없는 도입은 운영 부채** — 도입 첫날부터 metric 수집 파이프라인을 만들어라.
- **답변 패턴 = 기준 1개 + 숫자 1개 + 트레이드오프 1개** — 30초 답변의 황금 비율.

### 7.1 자가 점검

!!! question "🤔 Q1 — 카드 사용 trigger (Bloom: Apply)"
    "RAG 도입할까?" 라는 질문에 이 카드를 펴면 어디부터?
    ??? success "정답"
        §4.2 결정 트리 → §5.6 RAG 파이프라인 → §6 흔한 오해:
        - **§4.2**: workload 가 fact-heavy 인가, reasoning-heavy 인가 판별 → fact-heavy 면 RAG, 아니면 fine-tune 고려.
        - **§5.6**: chunk size / retrieval top-K / re-rank 의 default 값 확인.
        - **§6**: "RAG = LLM 만 갈아끼우면 됨" 같은 오해 회피.
        - 카드의 가치: 30 초 안에 의사결정 + 빠진 고려사항 회피.

!!! question "🤔 Q2 — Agent 비용 폭주 (Bloom: Evaluate)"
    면접에서 "Agent 도입 후 30 일 운영 비용이 예측치의 10 배" 사례. 카드로 정답할 답변 패턴?
    ??? success "정답"
        기준 + 숫자 + trade-off:
        - **기준**: max-step / budget guard 누락이 90% 의 root cause.
        - **숫자**: 1 query × avg 8 tool call × $0.02/call = $0.16 → 1000 query/day = $160/day.
        - **trade-off**: hard cap → robustness ↓ (작업 미완료), soft cap (warning + degrade) → cost predictable.
        - 결론: 계측 없이 launch = 운영 부채 1 위.

### 7.2 출처

**Internal (Confluence)**
- `AI Engineering Curriculum` — 모듈 1–7 매핑
- `Agent Cost Audit` — max-step / budget 정책

**External**
- *LangChain Documentation* — Agent / RAG 패턴
- OpenAI *Cookbook* — production guardrails

## 다음 단계

- 퀴즈로 마무리: [전체 Quiz Index](../quiz/) — 8개 모듈 각 5문항씩, 총 40문항.
- 추가 학습: LangChain/LangGraph, LoRA fine-tune, RAGAS, Multi-agent system.

<div class="chapter-nav">
  <a class="nav-prev" href="../07_dv_application/">
    <div class="nav-label">◀ 이전</div>
    <div class="nav-title">DV/EDA 도메인 적용 사례</div>
  </a>
  <a class="nav-next" href="../quiz/">
    <div class="nav-label">다음 ▶</div>
    <div class="nav-title">퀴즈로 이동</div>
  </a>
</div>


--8<-- "abbreviations.md"
