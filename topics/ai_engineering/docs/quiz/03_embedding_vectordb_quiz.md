# Quiz — Module 03: Embedding & Vector DB

[← Module 03 본문으로 돌아가기](../03_embedding_vectordb.md)

---

## Q1. (Remember)

FAISS 의 대표 인덱스 3종류는?

??? answer "정답 / 해설"
    1. **IVF** (Inverted File) — k-means 로 cluster, 검색 시 가까운 cluster 만 스캔.
    2. **HNSW** — 그래프 기반, 빠른 검색 + 메모리 큼.
    3. **PQ** (Product Quantization) — 벡터를 sub-vector 로 나눠 quantize → 메모리 ↓.

    실무에서는 **IVF + PQ** 조합이 표준 (예: IVF1024,PQ16).

## Q2. (Understand)

Cosine similarity 가 dot product 가 아닌 정규화된 형태로 자주 쓰이는 이유는?

??? answer "정답 / 해설"
    임베딩 벡터의 길이(노름) 가 문서 길이/단어 수에 따라 달라질 수 있는데, similarity 가 길이에 좌우되면 의미와 무관한 편향이 생긴다. cosine 은 **방향(의미)** 만 비교하므로 더 안정적이다. (단, embedding 모델이 이미 unit-norm 을 출력하면 dot product 와 동일.)

## Q3. (Apply)

사내 코드 100k 파일을 FAISS index 로 만들 때 chunk 단위와 chunk size 를 어떻게 정할 것인가?

??? answer "정답 / 해설"
    - **단위**: 의미 단위(함수 / 클래스 / SystemVerilog module) 가 일반 텍스트 chunk 보다 retrieval 품질이 좋다.
    - **크기**: 256~512 토큰 권장. 너무 짧으면 컨텍스트 부족, 너무 길면 임베딩이 평균화되어 retrieval 정확도 ↓.
    - **Overlap**: 50~100 토큰의 sliding overlap 으로 경계에서의 정보 손실 방지.
    - **Metadata**: 파일 경로, 함수명, 라인 번호를 함께 저장 → re-rank 시 활용.

## Q4. (Analyze)

10M 벡터에서 latency 를 1ms 이하로 유지해야 한다. IVF · HNSW · PQ 의 trade-off 를 분석하라.

??? answer "정답 / 해설"
    - **HNSW** : 가장 빠름 (1ms 이하 가능). 메모리는 벡터 자체의 1.5~2배.
    - **IVF** : nprobe 로 정확도-속도 trade-off 명확. 메모리 효율 ↑.
    - **PQ** : 메모리 ↓↓ (10x 압축) 하지만 정확도 약간 손실.

    10M 정도면 **IVF + HNSW** 또는 **IVF + PQ** 조합이 일반적. 메모리 예산이 빡빡하면 PQ, 정확도 우선이면 HNSW.

## Q5. (Evaluate)

자기 도메인의 retrieval 품질을 평가할 때 권장하는 절차는?

??? answer "정답 / 해설"
    1. **Gold set 50~200개** 만들기 — 사람이 직접 query → relevant 문서 라벨링.
    2. **MRR / Recall@k / nDCG** 측정.
    3. **A/B 비교** — 임베딩 모델 후보 2~3개 (예: BGE-large vs E5-large vs OpenAI text-embedding-3-small) 동시 측정.
    4. **에러 분석** — 잘 안 잡히는 query 패턴(약어, 코드 식별자 등) 을 정리해 hybrid (sparse) 적용 여부 결정.
    5. **운영 측정** — 사용자 클릭/체류 같은 implicit signal 을 retrieval 품질의 proxy 로 추적.
