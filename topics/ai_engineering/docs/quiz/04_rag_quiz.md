# Quiz — Module 04: RAG

[← Module 04 본문으로 돌아가기](../04_rag.md)

---

## Q1. (Remember)

RAG 의 4-step 파이프라인은?

??? answer "정답 / 해설"
    1. **Chunk** — 문서를 의미 단위로 분할.
    2. **Index** — 임베딩 → vector DB 적재.
    3. **Retrieve** — 질의를 임베딩 → top-k 검색 (+ re-rank).
    4. **Generate** — 검색 결과를 prompt 에 합쳐 LLM 호출.

## Q2. (Understand)

RAG 가 fine-tune 보다 운영 측면에서 유리한 시나리오를 설명하라.

??? answer "정답 / 해설"
    - **자주 갱신되는 지식** : RAG 는 인덱스만 갱신하면 즉시 반영, fine-tune 은 매번 재학습.
    - **출처 인용 필요** : RAG 는 검색된 문서 출처를 답변에 첨부 가능, fine-tune 은 어떤 데이터로 답이 나왔는지 추적 불가.
    - **소량 데이터** : fine-tune 은 수천~수만 예시가 필요하지만 RAG 는 수십 문서로도 즉시 동작.

## Q3. (Apply)

Hybrid 검색 (dense + BM25) 에서 두 점수를 어떻게 결합할 것인가?

??? answer "정답 / 해설"
    1. **Weighted sum** : `score = α * dense + (1-α) * bm25`. α 는 validation set 으로 튜닝.
    2. **Reciprocal Rank Fusion (RRF)** : 각 검색의 rank 만 사용해 `1/(k+rank)` 합산. 점수 스케일 차이를 자연스럽게 흡수.
    3. **Re-ranker 로 합치기** : 두 검색의 top-N 합집합을 cross-encoder 로 재정렬.

    RRF 가 대부분의 경우 robust 한 baseline.

## Q4. (Analyze)

RAG 응답이 부정확할 때 단계별 진단 순서를 제시하라.

??? answer "정답 / 해설"
    1. **Retrieval check** : top-k 안에 정답 문서가 있는가? 없으면 → chunking, 임베딩 모델, hybrid 부족이 원인.
    2. **Context window check** : 정답 문서가 너무 길어 truncation 됐는가?
    3. **Prompt check** : 검색 결과를 LLM 이 무시하지 않도록 명확한 지시 ("Cite the source", "Answer only from the provided context") 가 있는가?
    4. **Generation check** : 같은 컨텍스트로 GPT-4 등 더 강한 모델이 풀면 풀리는가? → LLM 한계.

    이 순서는 **싸고 빠른 단계부터** 점검하는 원칙이다.

## Q5. (Evaluate)

RAGAS 의 Faithfulness, Answer Relevance, Context Recall 이 각각 측정하는 바는?

??? answer "정답 / 해설"
    - **Faithfulness** : 답변이 검색된 컨텍스트로부터 grounded 되어 있는가? (hallucination 측정)
    - **Answer Relevance** : 답변이 질의에 적합한가? (off-topic 여부)
    - **Context Recall** : 정답에 필요한 정보가 검색된 컨텍스트 안에 다 들어 있는가? (retrieval 품질)

    셋이 함께 측정되어야 어디가 깨졌는지 진단 가능. 한 가지만 보면 책임 소재가 흐려진다.
