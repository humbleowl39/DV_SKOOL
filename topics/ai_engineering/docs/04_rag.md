# Unit 4: RAG (Retrieval-Augmented Generation)

<div class="learning-meta">
  <span class="meta-badge meta-time">⏱ 11분</span>
  <span class="meta-badge meta-level-intermediate">📊 Intermediate</span>
</div>

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

<div class="chapter-nav">
  <a class="nav-prev" href="03_embedding_vectordb.md">
    <div class="nav-label">◀ 이전</div>
    <div class="nav-title">Embedding & Vector DB (FAISS)</div>
  </a>
  <a class="nav-next" href="05_agent_architecture.md">
    <div class="nav-label">다음 ▶</div>
    <div class="nav-title">Agent 아키텍처</div>
  </a>
</div>
