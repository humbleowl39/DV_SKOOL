# Module 04 — RAG (Retrieval-Augmented Generation)

## 학습 목표 (Learning Objectives)

이 모듈을 마치면:

1. (Remember) RAG 의 기본 4-step (chunk · index · retrieve · generate) 을 나열할 수 있다.
2. (Understand) RAG 가 fine-tune 보다 비용/유지보수에서 유리한 시나리오를 설명할 수 있다.
3. (Apply) Hybrid 검색 + Re-ranker 를 적용한 RAG 파이프라인을 설계할 수 있다.
4. (Analyze) RAG 응답이 실패하는 단계(retrieval / context window / generation) 를 진단할 수 있다.
5. (Evaluate) RAGAS / 자체 metrics 로 RAG 시스템 품질을 평가할 수 있다.

## 선수 지식 (Prerequisites)

- Module 02 (prompt) · Module 03 (embedding/vector DB)
- 검색 시스템 평가 지표 (precision@k, recall@k)

## 왜 이 모듈이 중요한가 (Why it matters)

LLM 이 도메인 지식을 갖게 만드는 가장 비용·운영 효율 좋은 방법이 RAG 다. Fine-tune 은 비싸고 느리며 라이프사이클이 길지만, RAG 는 인덱스만 갱신하면 곧장 반영된다. 사내 IP / 코드 / 문서를 LLM 으로 활용하려는 거의 모든 프로젝트의 표준 패턴이다.

---

!!! tip "💡 이해를 위한 비유"
    **RAG (Retrieval-Augmented Generation)** ≈ **참고서 + 인턴 — 질문이 오면 책상에 reference 펼쳐 두고 답변하라**

    사용자 질의에 대해 외부 DB 에서 관련 chunk 검색 → LLM 입력에 첨부 → 응답. 도메인 지식을 가중치 변경 없이 활용.

---

## 핵심 개념
**RAG = LLM에 외부 지식을 검색하여 주입하는 아키텍처. LLM의 학습 데이터에 없는 최신/도메인 정보를 활용하면서, Fine-tuning의 비용과 Hallucination을 줄이는 실용적 접근법.**

---

## 왜 RAG가 필요한가?

### LLM만으로는 부족한 이유

| LLM 한계 | 설명 | RAG의 해결 |
|----------|------|-----------|
| Knowledge Cutoff | 학습 시점 이후 정보 없음 | 최신 문서 검색하여 주입 |
| Hallucination | 모르는 것을 그럴듯하게 지어냄 | 검색된 근거에 기반한 답변 |
| 도메인 지식 부족 | 반도체 IP 스펙은 학습 데이터에 없음 | 사내 문서 검색하여 주입 |
| Context 한계 | 전체 IP DB를 Context에 넣을 수 없음 | 관련 청크만 선별하여 주입 |
| 프라이버시 | 기밀 정보를 학습시킬 수 없음 | 검색만 — 모델에 저장 안 됨 |

---

## RAG 아키텍처

### 전체 흐름

```
사용자 쿼리: "sysMMU의 TLB invalidation 검증 시나리오는?"
         |
         v
+--------------------------------------------------+
|  1. Query Processing                              |
|     - 쿼리 임베딩 생성                            |
|     - (선택) 쿼리 재작성/확장                      |
+--------------------------------------------------+
         |
         v
+--------------------------------------------------+
|  2. Retrieval (검색)                               |
|     - Vector DB (FAISS)에서 유사 문서 검색          |
|     - Top-K 청크 반환 (예: k=5)                    |
|                                                   |
|     검색 결과:                                     |
|     [1] sysMMU spec: TLB invalidation commands... |
|     [2] sysMMU test plan: invalidation scenarios..|
|     [3] IP-XACT: sysMMU TLB register map...      |
+--------------------------------------------------+
         |
         v
+--------------------------------------------------+
|  3. Augmentation (증강)                            |
|     - 검색된 청크를 프롬프트에 삽입                |
|     "다음 참고 자료를 기반으로 답변하세요:          |
|      [검색 결과 1] [검색 결과 2] [검색 결과 3]     |
|      질문: sysMMU의 TLB invalidation 검증 시나리오"|
+--------------------------------------------------+
         |
         v
+--------------------------------------------------+
|  4. Generation (생성)                              |
|     - LLM이 검색 결과를 근거로 답변 생성           |
|     - 출처 기반 → Hallucination 감소               |
|                                                   |
|     출력:                                         |
|     "sysMMU TLB invalidation 검증 시나리오:        |
|      1. TLBI ALL: 전체 TLB 무효화 후 재접근...     |
|      2. TLBI by VA: 특정 VA만 무효화...            |
|      mrun test --test_name tlb_inv_all ..."       |
+--------------------------------------------------+
```

### Naive RAG vs Advanced RAG

```
Naive RAG:
  쿼리 → 임베딩 → 검색 → 프롬프트 삽입 → 생성
  (단순하지만 검색 품질에 크게 의존)

Advanced RAG:
  쿼리 → 쿼리 재작성 → 임베딩 → 하이브리드 검색 → 재랭킹
  → 프롬프트 최적화 → 생성 → 출처 검증
  (복잡하지만 품질 향상)
```

---

## RAG 파이프라인 상세

### Indexing (인덱싱) — 오프라인 단계

```
문서 수집 → 청킹 → 임베딩 → 인덱스 저장

+------------------------------------------------------------------+
|  Source Documents                                                 |
|  +--------+  +--------+  +--------+  +--------+                  |
|  | IP Spec|  | IP-XACT|  | Design |  | Test   |                  |
|  | (PDF)  |  | (XML)  |  | Doc    |  | Plan   |                  |
|  +---+----+  +---+----+  +---+----+  +---+----+                  |
|      |           |            |           |                       |
|      v           v            v           v                       |
|  +--------------------------------------------------+            |
|  |  Document Parser                                  |            |
|  |  - PDF → 텍스트 추출                              |            |
|  |  - XML → 구조적 파싱 (IP-XACT)                   |            |
|  |  - 테이블/다이어그램 처리                          |            |
|  +--------------------------------------------------+            |
|      |                                                            |
|      v                                                            |
|  +--------------------------------------------------+            |
|  |  Chunking                                         |            |
|  |  - 시맨틱 분할 (섹션/테이블/시퀀스)              |            |
|  |  - 메타데이터 보존 (출처, 페이지, IP 이름)        |            |
|  +--------------------------------------------------+            |
|      |                                                            |
|      v                                                            |
|  +--------------------------------------------------+            |
|  |  Embedding + FAISS Index                          |            |
|  |  - 각 청크 → 벡터                                |            |
|  |  - FAISS 인덱스에 저장                            |            |
|  +--------------------------------------------------+            |
+------------------------------------------------------------------+
```

### Retrieval (검색) — 온라인 단계

| 검색 방식 | 원리 | 장단점 |
|----------|------|--------|
| Dense Retrieval | 쿼리/문서 임베딩의 벡터 유사도 | 의미 검색 강함, 정확한 키워드 약함 |
| Sparse Retrieval (BM25) | TF-IDF 기반 키워드 매칭 | 정확한 키워드 강함, 의미 약함 |
| **Hybrid** | Dense + Sparse 결합 | 둘의 장점 결합, 가장 실용적 |

```
Hybrid 검색 (DVCon에서 사용):

  쿼리: "sysMMU TLB invalidation"

  Dense 결과: [TLB flush 관련 문서, MMU 캐시 관련 문서, ...]
  Sparse 결과: [정확히 "TLB invalidation" 포함 문서, ...]

  결합: RRF (Reciprocal Rank Fusion) 또는 가중 합산
  → Dense가 놓친 정확한 매칭 + Sparse가 놓친 의미적 매칭
```

### Re-ranking (재랭킹)

```
검색 Top-20 → Re-ranker 모델 → 최종 Top-5

Re-ranker:
  - 쿼리와 문서를 함께 입력받아 관련도 점수 산출
  - Cross-encoder 방식 (Bi-encoder보다 정확하지만 느림)
  - 검색은 빠른 Bi-encoder로, 순위 정밀화는 Cross-encoder로

  모델 예: ms-marco-MiniLM, Cohere rerank, BGE-reranker
```

---

## RAG 품질 평가 지표

| 지표 | 측정 대상 | 의미 |
|------|----------|------|
| **Retrieval Precision** | 검색된 K개 중 관련 문서 비율 | 검색 정확도 |
| **Retrieval Recall** | 전체 관련 문서 중 검색된 비율 | 검색 포괄성 |
| **Answer Faithfulness** | 생성된 답변이 검색 결과에 기반하는 비율 | Hallucination 방지 |
| **Answer Relevance** | 답변이 질문에 적합한 정도 | 실용성 |

### DVCon 논문의 평가 방법

```
Ground Truth: 인간 전문가가 정의한 검증 시나리오 목록
AI 생성:     RAG 시스템이 생성한 검증 시나리오 목록

평가:
  - 전문가 목록에 있지만 AI가 놓친 것 = Gap (미발견)
  - AI가 발견했지만 전문가가 놓친 것 = 추가 발견 (AI의 가치)
  - 결과: 293개 Critical Gap 발견 (2.75% rate)
```

---

## RAG 실패 모드와 대응

| 실패 모드 | 원인 | 대응 |
|----------|------|------|
| 관련 문서 검색 실패 | 쿼리와 문서의 어휘 차이 | 쿼리 확장, Hybrid 검색 |
| 잘못된 문서 검색 | 임베딩 품질 부족 | 도메인 특화 임베딩, Re-ranking |
| 검색 성공 but 답변 오류 | LLM의 문서 이해 실패 | 더 나은 프롬프트, 긴 Context |
| Chunk 경계에서 정보 분리 | 관련 정보가 다른 Chunk에 | Overlap Chunking, Parent-Child |
| 오래된 문서 | 문서 업데이트 미반영 | 인덱스 갱신 파이프라인 |

---

## DVCon 논문의 RAG 아키텍처 (이력서 직결)

```
+------------------------------------------------------------------+
|  "Engineering Intelligence" Framework                             |
|                                                                   |
|  데이터 소스:                                                     |
|  +--------+  +---------+  +--------+                              |
|  | IP-XACT|  | IP Spec |  | Design |                              |
|  | (구조) |  | (시맨틱)|  | Doc    |                              |
|  +---+----+  +----+----+  +---+----+                              |
|      |            |            |                                   |
|      v            v            v                                   |
|  Hybrid Data Extraction:                                          |
|      IP-XACT → 구조적 데이터 (레지스터, 버스, 메모리맵)            |
|      IP Spec → 시맨틱 데이터 (기능 설명, 동작 모드, 제약)         |
|      결합 → 풍부한 IP 프로파일                                    |
|                                                                   |
|  FAISS 인덱싱:                                                    |
|      IP 프로파일 → Embedding → FAISS Index                        |
|                                                                   |
|  LLM-Based Test Generation:                                       |
|      쿼리 "Feature X 검증" → FAISS 검색 → 관련 IP 정보 반환       |
|      → LLM에 전달 → 테스트 명령어 + V-Plan bin 자동 생성          |
|                                                                   |
|  결과:                                                            |
|      Project A: 293 gaps (2.75%) 발견                             |
|      Project B: 216 gaps (4.99%) 발견                             |
|      Human oversight: 96.30% (소형 프로젝트)                      |
+------------------------------------------------------------------+
```

---

## Q&A

**Q: RAG란 무엇이고 왜 Fine-tuning 대신 사용하는가?**
> "RAG는 LLM에 외부 지식을 검색하여 주입하는 아키텍처다. Fine-tuning 대비 세 가지 이점: (1) 비용 — 모델 재학습 없이 인덱스만 갱신. (2) 최신성 — 문서 업데이트 즉시 반영. (3) 프라이버시 — 기밀 정보가 모델에 저장되지 않고 검색 시에만 사용. 반도체 IP 정보처럼 보안이 중요하고 빈번히 변경되는 도메인에 특히 적합하다."

**Q: DVCon 논문의 RAG 시스템을 설명하라.**
> "Hybrid Data Extraction으로 IP-XACT(구조)와 IP 스펙(시맨틱)을 결합하여 풍부한 IP 프로파일을 생성했다. FAISS로 인덱싱하고, LLM이 검색된 정보를 기반으로 테스트 명령어와 V-Plan bin을 자동 생성한다. IP-XACT만으로는 시맨틱 컨텍스트 부족으로 보안 관련 테스트를 누락했는데, RAG로 IP 스펙까지 결합하여 이를 해결했다. 결과: Project A에서 293개(2.75%), Project B에서 216개(4.99%)의 Critical Gap을 발견했다."

**Q: RAG에서 검색 품질을 어떻게 보장하는가?**
> "세 가지 전략: (1) Hybrid 검색 — Dense(의미) + Sparse(키워드) 결합으로 각각의 약점 보완. (2) 도메인 특화 Chunking — IP 스펙의 섹션/테이블/시퀀스 단위 분할로 의미 보존. (3) Re-ranking — 초기 Top-20을 Cross-encoder로 정밀 재정렬하여 최종 Top-5의 정확도 향상."

---

!!! danger "❓ 흔한 오해"
    **오해**: RAG 가 fine-tune 을 완전히 대체

    **실제**: RAG 는 지식 갱신에 강함, fine-tune 은 형식/스타일 내재화에 강함. 둘은 보완. 실무는 "prompt → RAG → 필요 시 FT" 순서.

    **왜 헷갈리는가**: 최근 RAG hype 가 fine-tune 의 단점만 부각. 실제로는 trade-off.

!!! warning "실무 주의점 — RAG 검색 실패가 Hallucination으로 보이는 문제"
    **현상**: Retrieval 단계에서 관련 문서가 반환되지 않으면 LLM은 학습 지식으로 답변을 생성한다. 사용자 입장에서는 RAG가 작동한 것처럼 보이지만 실제로는 검색이 실패한 응답이므로, 도메인 특화 정보가 틀릴 가능성이 높다.

    **원인**: Retrieval 실패와 성공이 응답 형식에서 구별되지 않으며, `retrieved_context`가 비었을 때 LLM에게 "모른다"고 답하도록 프롬프트로 강제하지 않으면 자연스럽게 hallucination이 발생한다.

    **점검 포인트**: 응답 파이프라인에서 `len(retrieved_docs) == 0`일 때 별도 분기로 "관련 문서 없음" 메시지를 반환하는지 확인. 평가 시 retrieval recall과 생성 답변 정확도를 별도 지표로 측정해 검색 실패가 오답의 원인인지 분리 분석.

## 핵심 정리 (Key Takeaways)

- **RAG = LLM + 외부 검색** — 가중치 변경 없이 도메인 지식 활용.
- **Chunking** — 문서를 의미 단위로 자르는 것이 retrieval 품질의 출발점.
- **Hybrid 검색** — dense + sparse(BM25) 결합으로 OOV / 약어를 보완.
- **Re-ranking** — top-20 을 cross-encoder 로 정밀 재정렬 → top-5 의 정확도 ↑.
- **품질 평가** — Faithfulness, Answer Relevance, Context Recall (RAGAS).

## 다음 단계 (Next Steps)

- 다음 모듈: [Agent Architecture →](../05_agent_architecture/) — RAG 가 도구 호출과 결합되어 자율 agent 가 된다.
- 퀴즈: [Module 04 Quiz](../quiz/04_rag_quiz/) — RAG 4단계, 실패 진단 5문항.
- 실습: 자기 회사 spec 문서로 RAG 시스템을 만들고, 30개 query 에 대해 RAGAS metric 측정.

<div class="chapter-nav">
  <a class="nav-prev" href="../03_embedding_vectordb/">
    <div class="nav-label">◀ 이전</div>
    <div class="nav-title">Embedding & Vector DB (FAISS)</div>
  </a>
  <a class="nav-next" href="../05_agent_architecture/">
    <div class="nav-label">다음 ▶</div>
    <div class="nav-title">Agent 아키텍처</div>
  </a>
</div>
