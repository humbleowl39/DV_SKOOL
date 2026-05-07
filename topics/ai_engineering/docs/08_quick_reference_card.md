# Module 08 — Quick Reference Card

## 학습 목표 (Learning Objectives)

이 모듈을 마치면:

1. (Remember) 7개 모듈의 핵심 키워드를 즉시 떠올릴 수 있다.
2. (Apply) 면접/리뷰에서 30초 이내 답변할 수 있는 답변 템플릿을 갖춘다.
3. (Evaluate) 자기 시스템의 부족한 영역(LLM 선택, RAG 품질, Agent 통제) 을 cheat sheet 와 비교 평가할 수 있다.

## 선수 지식 (Prerequisites)

- Module 01 ~ 07.

## 왜 이 모듈이 중요한가 (Why it matters)

복습 + 인터뷰/리뷰 직전의 1-page cheat sheet. 학습한 내용을 빠르게 인덱스화한다.

---

!!! tip "💡 이해를 위한 비유"
    **AI Engineering 마스터 = 4축 (Prompt/RAG/Agent/Eval) 의 즉답** ≈ **AI 솔루션 아키텍트 — 어떤 비즈니스 case 든 적합한 조합 30초 내 답변**

    Task 특성 → 전략 매핑을 즉시 그리는 것이 마스터. 모든 case 를 RAG 로 풀려고 하면 hammer-nail.

---

## 핵심 정리

| 주제 | 핵심 포인트 |
|------|------------|
| LLM | Transformer + Self-Attention, 다음 토큰 예측, Context Window 한계 |
| LLM 추론 최적화 | KV Cache(재계산 방지), GQA(메모리 절약), Flash Attention(IO 최적화) |
| Positional Encoding | Sinusoidal → Learned → **RoPE**(현재 표준) → ALiBi |
| MoE | Sparse Activation: 총 파라미터↑ 연산↓, Mixtral 8x7B 대표적 |
| Quantization | FP16→INT8→INT4, AWQ/GPTQ로 정밀도 유지, 로컬 배포 핵심 |
| Scaling Laws | Chinchilla: D≈20N 최적, 50B+에서 코드 생성 의미 있는 품질 |
| Prompt Eng. | Role + Context + Task + Constraint + Format = 좋은 프롬프트 |
| 고급 추론 | CoT → Self-Consistency(다수결) → ToT(탐색) → Prompt Chaining(단계) |
| Embedding | Contrastive Learning으로 학습, MTEB 벤치마크로 평가 |
| FAISS | Meta의 벡터 검색 라이브러리, 로컬 실행, GPU 가속 |
| RAG | 검색(Retrieve) → 증강(Augment) → 생성(Generate) |
| Agent | LLM + Tool(Function Calling) + Plan + Memory, ReAct 패턴 |
| Agent 고급 | Reflection(자기검증), Multi-Agent(협업), MCP(도구 표준) |
| Fine-tuning | LoRA/QLoRA로 0.1~1% 파라미터만 학습, DPO/ORPO로 정렬 |
| 전략 선택 | 보안→RAG, 최신성→RAG, 도메인적응→Fine-tune, 빠름→Prompt |

---

## 면접 골든 룰

1. **RAG vs Fine-tuning**: "보안, 최신성, 비용"으로 판단 — DVCon에서 RAG를 선택한 3가지 이유
2. **Hallucination**: "생성 코드는 반드시 컴파일 + 시뮬레이션 검증" — AI 맹신 금지
3. **FAISS 선택 이유**: "로컬(보안) + 라이브러리(통합) + GPU(속도)"
4. **Hybrid Extraction**: "IP-XACT(구조) + IP Spec(시맨틱) = DVCon의 핵심 차별점"
5. **AI = 증강**: "대체가 아닌 증강(Augmentation) — 인간 판단 + AI 처리"
6. **정량적 성과**: 숫자로 말하라 — 293개 Gap, 2.75%, 96.30% Human Oversight
7. **보안**: "반도체 IP는 클라우드 전송 불가 → 로컬 모델(INT4 양자화) + FAISS"
8. **3단계 비전**: "현재(보조) → 단기(자율 디버그) → 장기(자율 V-Plan)"
9. **LLM 내부 이해**: KV Cache, GQA, Flash Attention — 왜 추론이 느린지/빠른지 설명 가능
10. **Agent 패턴**: Function Calling → ReAct → Reflection → Multi-Agent 발전 흐름

---

## 이력서 연결 포인트

| 이력서 항목 | 면접 질문 | 핵심 답변 포인트 |
|------------|----------|----------------|
| DVCon 2025 Publication | "논문의 핵심 기여는?" | Hybrid Extraction + RAG/FAISS → 293개 Gap 발견 (2.75%) |
| RAG & FAISS | "왜 FAISS를 선택했나?" | 보안(로컬) + 통합(라이브러리) + 성능(GPU) |
| LLM-Based Test Gen | "어떻게 테스트를 생성했나?" | Few-shot ICL + Structured Output → mrun 명령어 + V-Plan bin |
| Hybrid Extraction | "IP-XACT만으로 부족한 이유는?" | 시맨틱 부족 → 보안 테스트 누락 → IP Spec으로 보완 |
| DAC 2026 (submitted) | "AI 자동화를 어떻게 했나?" | Agent 패턴: RTL 변경감지→코드생성→컴파일검증 루프 |
| AI Expert 자격 | "AI 전문성을 DV에 어떻게 적용하나?" | 이론(삼성+서울대) → 실무(DVCon) → 확장(DAC) |
| 96.30% Human Oversight | "이 수치의 의미는?" | 인간 실수가 검증 갭의 주 원인 → 자동화 필요성 정량 증명 |

---

## 면접 스토리 흐름 (Technical Challenge #3)

```
1. 문제 인식
   "SoC 통합에서 공통 IP 검증 항목이 반복적으로 누락되었다 (3-5%)"

2. 기존 시도의 한계
   "JIRA/Confluence 수동 추적 → 규모 확장 시 한계
    IP-XACT 자동화 → 시맨틱 부족 (보안 테스트 누락)"

3. 해결 (3단계 파이프라인)
   "(1) Hybrid Extraction: IP-XACT(구조) + IP Spec(시맨틱)
    (2) RAG + FAISS: 대규모 IP DB 인덱싱 + 의미 검색
    (3) LLM: Few-shot으로 테스트 명령어 + V-Plan bin 자동 생성"

4. 성과 (정량적)
   "Project A: 293개(2.75%), Project B: 216개(4.99%) Gap 발견
    인간 실수: 96.30%, New IP/Feature 누락 40% 감소"

5. 학술 기여 + 확장
   "DVCon 2025 Publication → DAC 2026 (Agent 확장)"
```

---

## 기술 스택 빠른 참조

```
LLM 모델:    Claude / GPT-4 / Llama (로컬)
Embedding:   OpenAI ada / BGE / Sentence-BERT (로컬)
Vector DB:   FAISS (로컬, GPU 가속)
RAG 프레임워크: LangChain / 직접 구현
Agent:       LangChain Agent / Claude Agent SDK
Fine-tuning: LoRA / QLoRA (Hugging Face + PEFT)
언어:        Python (AI) + SystemVerilog (DV)
```

---

## RAG 파이프라인 빠른 참조

```
오프라인 (Indexing):
  문서 수집 → 파싱 → Chunking → Embedding → FAISS Index

온라인 (Query):
  쿼리 → 임베딩 → FAISS 검색(Top-K) → [Re-ranking] → 프롬프트 삽입 → LLM → 답변

핵심 파라미터:
  Chunk Size:  512~1024 토큰
  Overlap:     50~100 토큰
  Top-K:       3~10 (보통 5)
  Embedding:   768~3072 차원
  FAISS Index: IndexIVFFlat (중규모), IndexFlatL2 (소규모)
```

---

## 다음 학습 추천

| 주제 | 이유 |
|------|------|
| LangChain/LangGraph 실습 | RAG + Agent 구현 프레임워크 |
| LoRA Fine-tuning 실습 | DV 도메인 모델 적응 |
| Evaluation Framework | RAG 품질 평가 자동화 (RAGAS 등) |
| Multi-Agent System | 복잡한 DV 워크플로 자동화 |

---

!!! danger "❓ 흔한 오해"
    **오해**: AI 는 더 큰 모델이면 다 해결

    **실제**: Frontier 모델조차 hallucination, context 한계, retrieval 부재로 실패. 모델 ↑ 보다 "task 분해 + RAG 품질 + Agent loop guard" 가 더 효과적.

    **왜 헷갈리는가**: AI 발전이 "model 크기" 로 매년 보고되어 "크기 = 능력" 단순화.

!!! warning "실무 주의점 — 계측 없는 Agent 배포는 운영 부채"
    **현상**: Agent 파이프라인을 계측 없이 운영하면, 어느 단계(Retrieval, LLM, Tool 호출)에서 실패가 발생했는지 사후에 추적할 수 없어 장애 대응 시간이 수 배 길어진다.

    **원인**: Agent는 단일 API와 달리 다단계 호출 체인이므로, 단계별 latency·성공률·비용을 별도로 수집하지 않으면 전체 응답 시간만 측정된다.

    **점검 포인트**: LangSmith, Langfuse 등의 tracing 도구나 자체 미들웨어로 `retrieval_time`, `llm_time`, `tool_call_count`, `total_cost`를 스텝 단위로 로깅. 도입 첫날부터 대시보드를 구성해 비용 이상 증가 알림을 설정.

## 핵심 정리 (Key Takeaways)

- **LLM 호출만이 끝이 아니다** — Prompt → RAG → Agent → Eval 의 4축으로 구성.
- **품질의 상한 = 검색 품질** — RAG 의 retrieval 단계가 제일 먼저 깨진다.
- **Agent loop 는 비용 폭주에 취약** — max-step / budget guard 필수.
- **계측 없는 도입은 운영 부채** — 도입 첫날부터 metric 수집 파이프라인을 만들어라.

## 다음 단계 (Next Steps)

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
