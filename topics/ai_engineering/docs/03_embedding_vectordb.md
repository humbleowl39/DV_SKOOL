# Module 03 — Embedding & Vector DB

<!-- DV-SKOOL-CH-CTX:start -->
<div class="chapter-context" data-cat="applied">
  <a class="chapter-back" href="../">
    <span class="chapter-back-arrow">←</span>
    <span class="chapter-back-icon">🤖</span>
    <span class="chapter-back-text">AI Engineering</span>
  </a>
  <span class="chapter-divider">›</span>
  <span class="chapter-marker">Module 03</span>
</div>
<!-- DV-SKOOL-CH-CTX:end -->

<!-- DV-SKOOL-CH-TOC:start -->
<div class="page-toc">
  <span class="page-toc-label">목차</span>
  <a class="page-toc-link" href="#1-why-care-context-window-만으로는-안-되는-이유">1. Why care?</a>
  <a class="page-toc-link" href="#2-intuition-도서관-의미-색인-비유와-한-장-그림">2. Intuition</a>
  <a class="page-toc-link" href="#3-작은-예-tlb-flush-쿼리-한-개를-end-to-end-추적">3. 작은 예 — 한 쿼리 추적</a>
  <a class="page-toc-link" href="#4-일반화-임베딩-학습-원리-와-ann-알고리즘-축">4. 일반화 — Embedding + ANN</a>
  <a class="page-toc-link" href="#5-디테일-mteb-faiss-인덱스-종류-chunking-대안-vector-db">5. 디테일</a>
  <a class="page-toc-link" href="#6-흔한-오해-와-dv-디버그-체크리스트">6. 흔한 오해 + 디버그</a>
  <a class="page-toc-link" href="#7-핵심-정리-key-takeaways">7. 핵심 정리</a>
</div>
<!-- DV-SKOOL-CH-TOC:end -->

!!! objective "학습 목표"
    이 모듈을 마치면:

    - **Define** Embedding, ANN, FAISS, BGE 의 정의를 구분할 수 있다.
    - **Explain** Cosine similarity 가 왜 의미 검색의 표준이 되었는지 설명할 수 있다.
    - **Apply** 사내 코드/문서를 chunk → embed → FAISS index 로 만드는 파이프라인을 설계할 수 있다.
    - **Analyze** IVF · HNSW · PQ 의 메모리/지연/정확도 trade-off 를 데이터 규모별로 분석할 수 있다.
    - **Evaluate** 검색 품질을 MRR / nDCG 로 평가하고, 임베딩 모델 후보를 선정할 수 있다.

!!! info "사전 지식"
    - [Module 01](01_llm_fundamentals.md) — context window 한계, KV cache 메모리
    - [Module 02](02_prompt_engineering.md) — Few-shot, ICL
    - 기본 선형대수 (벡터 내적, 노름)
    - 검색 시스템에 대한 직관 (precision / recall)

---

## 1. Why care? — Context window 만으로는 안 되는 이유

LLM 의 context window 만으로는 대규모 문서·코드 베이스를 다룰 수 없습니다. 200K context 라도 사내 IP 스펙 + 코드 + 디자인 문서 _전체_ 를 못 담고, 담더라도 (1) [Module 01](01_llm_fundamentals.md) §5.4 의 KV cache 메모리 폭주, (2) "lost in the middle" 무시 문제, (3) 매 호출마다 200K 의 입력 비용을 부담하게 됩니다.

**임베딩 + 벡터 DB 가 외부 메모리** 역할을 합니다. 이 두 컴포넌트의 품질이 RAG / Agent 시스템의 _상한선_ 입니다 — 검색이 망가지면 그 위에 어떤 LLM 을 얹어도 답이 깨집니다.

---

## 2. Intuition — "도서관 의미 색인" 비유와 한 장 그림

!!! tip "💡 한 줄 비유"
    **Embedding + Vector DB ≈ 도서관 의미 색인** — 키워드(BM25) 가 _제목·저자_ 색인이라면, 임베딩은 _주제·뉘앙스_ 색인.<br>
    "TLB flush" 로 검색해도 "TLB invalidation" 책이 함께 나오는 이유는 두 단어가 _같은 의미 좌표_ 에 살기 때문.

### 한 장 그림 — Embedding + ANN 검색의 전체 구조

```
       ┌── Offline (Indexing) ──┐                ┌── Online (Query) ──┐
       │                        │                │                    │
       │  IP spec / 코드 / 문서 │                │   사용자 쿼리      │
       │         │              │                │   "TLB flush"      │
       │         ▼ Chunking     │                │         │          │
       │   [chunk₁, chunk₂,...] │                │         ▼ embed    │
       │         │              │                │   q ∈ ℝᵈ           │
       │         ▼ Embedding    │                │         │          │
       │   v₁, v₂, v₃, ... ∈ ℝᵈ │                │         ▼          │
       │         │              │                │  ┌──────────────┐  │
       │         ▼              │                │  │ Vector DB    │  │
       │   ┌──────────────┐     │                │  │ (FAISS / IVF │  │
       │   │ Vector DB    │ ◀───────────── 적재 ─┼──│  HNSW / PQ)  │  │
       │   │ (FAISS index)│     │                │  └──────┬───────┘  │
       │   └──────────────┘     │                │         │ top-k    │
       │                        │                │         ▼          │
       └────────────────────────┘                │   chunk₁₂, chunk₃₇ │
                                                 │         │          │
                                                 │         ▼ LLM      │
                                                 │   답변 + 출처      │
                                                 └────────────────────┘
```

### 왜 이 구조인가 — Design rationale

순진하게 매 쿼리마다 _모든_ chunk 를 LLM 에 넣으면 ① context window 초과, ② 토큰 비용 폭증, ③ "lost in the middle" 로 정확도 저하 — 이 셋이 동시에 깨집니다. 그래서 (1) 의미 좌표(embedding) 로 압축하고 (2) 가까운 좌표만 빠르게 (ANN) 골라 (3) 그 부분만 LLM 에 주입하는 _3 단 분리_ 가 RAG 시스템의 표준이 되었습니다. 이 모듈은 (1)+(2) 의 인프라, [Module 04](04_rag.md) 가 (3) 까지 합치는 단입니다.

---

## 3. 작은 예 — `"TLB flush"` 쿼리 한 개를 end-to-end 추적

가장 단순한 시나리오. 사내 IP 스펙 1000 청크가 이미 인덱싱돼 있고, `"TLB flush"` 라는 쿼리 한 개를 던져 top-3 청크가 나오기까지를 추적합니다.

```
   ┌─── Online query ───┐                              ┌─── FAISS Index (offline 적재됨) ───┐
   │                    │                              │                                     │
   │  query="TLB flush" │                              │  chunk₁  v₁=[0.12,-0.45,...]        │
   │        │           │  ① embed(query) → q ∈ ℝ⁷⁶⁸  │  chunk₂  v₂=[-0.31, 0.22,...]       │
   │        ▼           │                              │  ...                                │
   │   q = [0.11,       │                              │  chunk₂₃ v₂₃=[0.11,-0.43, 0.80,...] │ ← "TLB invalidation" 청크
   │        -0.43,      │                              │  ...                                │
   │        0.80,...]   │                              │  chunk₈₇ v₈₇=[0.55, 0.22,...]       │ ← "page fault" 청크
   │        │           │                              │  ...                                │
   │        ▼ ② IVF probe│                             │  Cluster 0..99 (K-means)            │
   │   nprobe=10        │  ─────────────────────────▶  │                                     │
   │        │           │                              │                                     │
   │        ▼ ③ cosine sim 비교 (10개 클러스터 안만)   │                                     │
   │   distances:       │                              │                                     │
   │     chunk₂₃: 0.95  │ ◀──── ④ top-3 반환 ──────── │                                     │
   │     chunk₅₆: 0.88  │                              │                                     │
   │     chunk₈₇: 0.42  │                              │                                     │
   │        │           │                              │                                     │
   │        ▼ ⑤ chunk text + metadata 회수            │                                     │
   │   "TLBI ALL: 전체 TLB 무효화..." (chunk₂₃)        │                                     │
   │                    │                              │                                     │
   └────────────────────┘                              └─────────────────────────────────────┘
```

| Step | 누가 | 무엇을 | 의미 |
|---|---|---|---|
| ① | embedding 모델 | 쿼리 텍스트 → 768 차원 벡터 | 인덱싱 시 사용한 _같은_ 모델이어야 함 (벡터 공간 일치) |
| ② | FAISS IVF | nlist=100 클러스터 중 nprobe=10 만 검색 후보로 | 전수 검색 대비 10배 빠름, 일부 누락 가능 |
| ③ | FAISS | nprobe 클러스터 안의 모든 vector 와 cosine 유사도 | dot-product or L2 — 인덱스 빌드 시 결정 |
| ④ | FAISS | top-k 반환 (k=3) | distance + index id |
| ⑤ | 호출자 | id → 원문 chunk + metadata (출처, IP 이름) 회수 | 이게 그대로 LLM prompt 의 context 가 됨 |

```python
import faiss, numpy as np
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("BAAI/bge-large-en-v1.5")

# Step ①
query_vec = model.encode(["TLB flush"], normalize_embeddings=True)  # (1, 768)

# Step ②~④ (인덱스가 IVF 라고 가정)
index = faiss.read_index("ip_spec.ivf.index")
index.nprobe = 10
distances, ids = index.search(query_vec.astype("float32"), k=3)

# Step ⑤
for d, i in zip(distances[0], ids[0]):
    print(f"[{d:.3f}] {chunks[i]['text'][:80]} (src={chunks[i]['source']})")
```

```
Cosine Similarity 예시 결과:

  sim("TLB invalidation", "TLB flush")     = 0.95   ← 매우 유사 (의도한 검색)
  sim("TLB invalidation", "TLB lookup")    = 0.71   ← 비슷하지만 다른 동작
  sim("TLB invalidation", "page fault")    = 0.42   ← 관련 있지만 다름
  sim("TLB invalidation", "boot device")   = 0.08   ← 거의 무관
```

!!! note "여기서 잡아야 할 두 가지"
    **(1) 인덱싱 모델 ≡ 쿼리 모델** — 다른 모델을 섞으면 좌표계가 달라져 무관한 결과가 나옵니다 (§6 의 흔한 오해).<br>
    **(2) ANN 은 정확 검색이 아니라 _근사_ 검색** — IVF/HNSW 는 일부 결과를 놓칠 수 있고, 이 trade-off 가 nlist/nprobe/efSearch 같은 파라미터로 노출됩니다.

---

## 4. 일반화 — 임베딩 학습 원리 와 ANN 알고리즘 축

### 4.1 텍스트 → 벡터 변환의 본질

```
"TLB invalidation" → [0.12, -0.45, 0.78, ..., 0.33]  (768~3072 차원)
"TLB flush"        → [0.11, -0.43, 0.80, ..., 0.31]  (유사한 벡터)
"page fault"       → [0.55, 0.22, -0.10, ..., -0.67] (다른 벡터)

핵심 속성:
  의미가 비슷한 텍스트 → 벡터 공간에서 가까움
  의미가 다른 텍스트 → 벡터 공간에서 멀어짐
```

### 4.2 유사도 측정

| 메트릭 | 수식 | 특징 |
|--------|------|------|
| Cosine Similarity | cos(θ) = A·B / (‖A‖×‖B‖) | 방향 기반, 크기 무관, 가장 일반적 |
| Euclidean Distance | ‖A - B‖₂ | 절대 거리, 정규화 필요 |
| Dot Product | A·B | 빠르지만 벡터 크기에 민감 |

### 4.3 Contrastive Learning — 임베딩이 학습되는 원리

```
핵심: "유사한 쌍은 가깝게, 다른 쌍은 멀게" 배치하는 학습

Step 1: 학습 데이터 구성
  긍정 쌍 (Positive): 의미가 같은 문장 쌍
    ("TLB invalidation", "TLB flush operation") → 가까워야 함

  부정 쌍 (Negative): 의미가 다른 문장 쌍
    ("TLB invalidation", "boot sequence") → 멀어야 함

Step 2: Contrastive Loss 학습
  InfoNCE Loss (가장 일반적):

    L = -log( exp(sim(q, k⁺)/τ) / Σ exp(sim(q, kᵢ)/τ) )

    q: 쿼리 임베딩
    k⁺: 긍정 샘플 임베딩
    kᵢ: 전체 샘플 (긍정 + 부정) 임베딩
    τ: Temperature (분포 날카로움 조절)

    → 긍정 쌍의 유사도를 높이고, 부정 쌍의 유사도를 낮추도록 학습

Step 3: Hard Negative Mining
  쉬운 부정 쌍: ("TLB invalidation", "pizza recipe") → 이미 멀어서 학습 효과 적음
  어려운 부정 쌍: ("TLB invalidation", "TLB lookup") → 비슷하지만 다른 의미
  → Hard Negative 를 많이 포함할수록 임베딩 품질 향상

학습 프레임워크:
  - Sentence-BERT: Siamese Network + Contrastive Loss
  - E5: "query: " / "passage: " 프리픽스로 비대칭 검색 최적화
  - BGE: RetroMAE 사전학습 + Contrastive Fine-tuning
```

### 4.4 ANN 알고리즘의 세 갈래

| 알고리즘 | 자료구조 | 장점 | 단점 | 적합 규모 |
|---|---|---|---|---|
| **Brute-force** (Flat) | 전수 검색 | 100% 정확 | O(N) 느림 | < 100K |
| **IVF** (Inverted File) | K-means 클러스터링 | nlist/nprobe 로 trade-off | 학습 단계 필요 | 100K~10M |
| **HNSW** (Hierarchical NSW) | 다층 small-world graph | 빠르고 정확 (~97%) | 메모리 큼 | 10K~100M |
| **PQ** (Product Quantization) | 벡터를 sub-vector 로 양자화 | 메모리 1/8~1/32 | 정확도 일부 손실 | 1M~10B |

각 알고리즘은 _정확도 vs 속도 vs 메모리_ 의 다른 균형점에 위치. 소규모는 Flat, 중규모는 IVF, 고정밀이 필요하면 HNSW, 압도적 규모는 IVF+PQ 조합.

---

## 5. 디테일 — MTEB, FAISS 인덱스 종류, Chunking, 대안 Vector DB

### 5.1 주요 Embedding 모델

| 모델 | 차원 | 특징 | 용도 |
|------|------|------|------|
| OpenAI text-embedding-3-small | 1536 | API 기반, 편리 | 일반적 |
| OpenAI text-embedding-3-large | 3072 | 높은 정확도 | 고정밀 검색 |
| Sentence-BERT (all-MiniLM) | 384 | 오픈소스, 경량 | 로컬 배포 |
| BGE-large | 1024 | 오픈소스, 고성능 | 한국어 포함 |
| Cohere embed-v3 | 1024 | 다국어 강점 | 다국어 RAG |

### 5.2 MTEB 벤치마크 — Embedding 모델 선택 기준

```
MTEB (Massive Text Embedding Benchmark):
  56개 데이터셋, 8개 태스크에서 Embedding 모델 종합 평가

태스크 카테고리:
  - Retrieval: 검색 성능 (RAG 의 핵심)
  - STS: 의미 유사도 (Semantic Textual Similarity)
  - Classification: 텍스트 분류
  - Clustering: 클러스터링 품질
  - Reranking: 재랭킹 정확도

2024-2025 MTEB 상위 모델 (Retrieval 기준):
  | 모델                  | 차원  | Retrieval | 전체 평균 | 크기    |
  |-----------------------|-------|-----------|-----------|---------|
  | Cohere embed-v3       | 1024  | 55.0+     | 64.5+     | API     |
  | OpenAI text-3-large   | 3072  | 54.9      | 64.6      | API     |
  | BGE-large-en-v1.5     | 1024  | 54.3      | 64.2      | 326MB   |
  | E5-mistral-7b-instruct| 4096  | 56.9      | 66.6      | 14GB    |
  | GTE-Qwen2-7B          | 3584  | 57.0+     | 65.0+     | 14GB    |

DV 도메인 선택 가이드:
  보안 필수 (로컬만) + 리소스 제한: BGE-large (326MB, 고성능)
  보안 필수 + GPU 여유: E5-mistral-7b (최고 성능, 도메인 적응 가능)
  보안 무관 + 빠른 구현: OpenAI text-3-small (API, 간편)
  다국어 필요: Cohere embed-v3 (한국어 성능 우수)
```

```
DV/EDA 도메인에서의 고려사항:

  1. 도메인 적합성
     - 일반 모델: "TLB" 를 일반 영어로 인식
     - 도메인 특화: "TLB" 를 MMU 의 Translation Lookaside Buffer 로 인식
     → 도메인 문서로 Fine-tune 하거나, Chunk 전략으로 보완

  2. 보안/프라이버시
     - 반도체 IP 정보는 외부 유출 불가
     - 클라우드 API (OpenAI) → 데이터 전송 필요 → 보안 위험
     - 로컬 모델 (Sentence-BERT, BGE) → 사내 서버에서 실행 → 안전
     → DVCon 논문에서 보안 고려가 중요했던 이유

  3. 다국어 지원
     - IP 스펙: 영어
     - 내부 문서: 한국어 혼용
     → 다국어 임베딩 모델 필요
```

### 5.3 FAISS (Facebook AI Similarity Search)

```
FAISS = Meta(Facebook) 가 개발한 대규모 벡터 유사도 검색 라이브러리

핵심 기능:
  - 수백만~수십억 벡터에서 밀리초 단위 검색
  - GPU 가속 지원
  - 다양한 인덱스 타입 (정확도 vs 속도 트레이드오프)
  - Python 바인딩으로 쉬운 통합
```

```python
import faiss
import numpy as np

# 1. 인덱스 생성 (벡터 차원 지정)
dimension = 768
index = faiss.IndexFlatL2(dimension)  # Exact search (L2 거리)

# 2. 벡터 추가
vectors = np.array([...])  # shape: (N, 768)
index.add(vectors)          # N개 벡터 추가

# 3. 검색 (쿼리 벡터와 유사한 k개 반환)
query = np.array([[...]])   # shape: (1, 768)
distances, indices = index.search(query, k=5)
# → indices: 가장 유사한 5개 벡터의 인덱스
# → distances: 각각의 거리
```

| 인덱스 | 검색 방식 | 속도 | 정확도 | 메모리 | 용도 |
|--------|----------|------|--------|--------|------|
| **IndexFlatL2** | 전수 검색 (Brute-force) | 느림 | 100% | 큼 | 소규모 (<100K) |
| **IndexIVFFlat** | 클러스터 기반 근사 검색 | 빠름 | ~95% | 중간 | 중규모 |
| **IndexIVFPQ** | 양자화 + 클러스터 | 매우 빠름 | ~90% | 작음 | 대규모 (수백만+) |
| **IndexHNSW** | 그래프 기반 근사 검색 | 빠름 | ~97% | 큼 | 고정밀 + 속도 |

```
IVF (Inverted File Index) 동작 원리:

1. 학습 단계: K-means 로 벡터들을 nlist 개 클러스터로 분류
   Cluster 0: [v1, v5, v12, ...]
   Cluster 1: [v2, v7, v23, ...]
   ...

2. 검색 단계:
   쿼리 벡터 → 가장 가까운 nprobe 개 클러스터 선택
   → 해당 클러스터 내에서만 정확 검색
   → 전수 검색 대비 nlist/nprobe 배 빠름

   예: nlist=100, nprobe=10 → 10배 빠르지만 일부 결과 누락 가능
```

```
DVCon 논문에서의 FAISS 활용:

IP 데이터베이스 인덱싱:

  1. IP 스펙 문서 → 청크(Chunk) 로 분할
  2. 각 청크 → Embedding 모델 → 벡터
  3. 벡터 → FAISS 인덱스에 저장

  검색 시:
  "sysMMU TLB invalidation 검증 시나리오"
  → 쿼리 임베딩 → FAISS 검색 → 관련 IP 스펙 청크 반환
  → LLM 에 전달 → 검증 시나리오 생성

  규모:
  - 수백 개 IP 의 스펙 문서 (수천 페이지)
  - 수만~수십만 청크
  → FAISS 없이는 실시간 검색 불가
```

### 5.4 Chunking 전략 — 문서를 어떻게 분할하는가

```
문제:
  IP 스펙 문서 = 수백 페이지
  Embedding 모델 입력 한계 = 512~8192 토큰
  LLM Context 한계 = 수천~수십만 토큰

  → 문서 전체를 한 번에 Embedding 할 수 없음
  → 적절한 단위로 분할(Chunk) 하여 각각 Embedding
```

| 방법 | 동작 | 장단점 |
|------|------|--------|
| Fixed Size | 고정 토큰 수로 분할 (512 토큰) | 간단하지만 의미 단위 무시 |
| Overlap | 고정 크기 + 겹침 영역 (50 토큰) | 경계에서 정보 손실 방지 |
| Semantic | 문단/섹션 단위로 분할 | 의미 보존, 구현 복잡 |
| Recursive | 큰 단위 → 작은 단위로 재귀 분할 | LangChain 기본, 균형 잡힘 |

```
DV 도메인 Chunking 고려사항:

IP 스펙 문서의 특성:
  - 레지스터 정의 = 테이블 형태 → 테이블 단위 Chunk
  - 프로토콜 시퀀스 = 연속적 흐름 → 시퀀스 단위 Chunk
  - 블록 다이어그램 설명 = 섹션 단위 → 섹션 Chunk

IP-XACT 의 특성:
  - XML 구조 → 태그 단위 파싱
  - 레지스터 맵, 버스 인터페이스, 메모리 맵
  → 구조적 파싱 + 시맨틱 설명 결합 (DVCon 의 Hybrid Extraction)
```

```python
from langchain.text_splitter import RecursiveCharacterTextSplitter
import re

# 방법 1: Recursive (가장 범용적)
splitter = RecursiveCharacterTextSplitter(
    chunk_size=512,       # 청크 최대 크기 (토큰 수 기준)
    chunk_overlap=50,     # 겹침 영역 (경계 정보 손실 방지)
    separators=["\n## ", "\n### ", "\n\n", "\n", " "]
    # 큰 구분자부터 시도 → 의미 단위 보존
)
chunks = splitter.split_text(ip_spec_text)

# 방법 2: IP-XACT 구조적 파싱 (DVCon 방식)
def chunk_ipxact(xml_root):
    """IP-XACT XML 을 의미 단위로 분할"""
    chunks = []

    # 레지스터 맵: 레지스터 단위
    for reg in xml_root.findall('.//register'):
        name = reg.find('name').text
        offset = reg.find('addressOffset').text
        fields = [(f.find('name').text, f.find('bitWidth').text)
                   for f in reg.findall('.//field')]
        chunk = f"Register: {name} (offset: {offset})\nFields: {fields}"
        chunks.append({"text": chunk, "type": "register", "ip": ip_name})

    # 버스 인터페이스: 인터페이스 단위
    for bus in xml_root.findall('.//busInterface'):
        name = bus.find('name').text
        bus_type = bus.find('busType').attrib
        chunk = f"Bus Interface: {name}, Type: {bus_type}"
        chunks.append({"text": chunk, "type": "bus_interface", "ip": ip_name})

    return chunks

# 방법 3: 메타데이터 보강 Chunking
def chunk_with_metadata(text, source_file, ip_name):
    """청크에 메타데이터를 첨부하여 검색 품질 향상"""
    raw_chunks = splitter.split_text(text)
    enriched = []
    for i, chunk in enumerate(raw_chunks):
        enriched.append({
            "text": chunk,
            "metadata": {
                "source": source_file,
                "ip_name": ip_name,
                "chunk_index": i,
                "total_chunks": len(raw_chunks)
            }
        })
    return enriched
```

```
Chunk Size 실험 결과 (일반적 경향):

  Size = 128 토큰: 너무 작음 → 문맥 부족, 검색 정밀도 높지만 Recall 낮음
  Size = 256 토큰: 짧은 정의/설명에 적합 (레지스터 정의 등)
  Size = 512 토큰: 범용적 최적점 (대부분의 RAG 연구 권장)
  Size = 1024 토큰: 긴 문맥 필요 시 (프로토콜 시퀀스, 동작 설명)
  Size = 2048+ 토큰: Context 낭비, 관련 없는 내용 포함 위험

  Overlap = Chunk Size 의 10-20% 권장
    512 → overlap 50~100
    1024 → overlap 100~200

DV 도메인 권장:
  레지스터 정의: 256 토큰 (짧고 독립적)
  프로토콜 설명: 512-1024 토큰 (문맥 필요)
  IP 개요: 1024 토큰 (큰 그림)
  → 문서 타입별로 다른 Chunk Size 적용이 최적
```

### 5.5 대안: 다른 Vector DB

| Vector DB | 특징 | 적합한 경우 |
|-----------|------|-----------|
| **FAISS** | 라이브러리, 자체 서버 불필요, GPU 가속 | 임베디드, 로컬, DV 파이프라인 |
| Chroma | Python 네이티브, 간단한 API | 프로토타이핑, 소규모 |
| Pinecone | 완전 관리형 클라우드 | 프로덕션 서비스 |
| Weaviate | 하이브리드 검색 (벡터 + 키워드) | 복잡한 검색 요구 |
| Milvus | 분산, 대규모 | 수십억 벡터 |
| pgvector | PostgreSQL 확장 | 기존 RDBMS 활용 |

**DVCon 논문에서 FAISS 를 선택한 이유**: (1) 로컬 실행 → IP 보안 유지. (2) 라이브러리 → 별도 서버 불필요 → DV 파이프라인에 직접 통합. (3) GPU 가속 → 대규모 IP DB 에서도 빠른 검색.

---

## 6. 흔한 오해 와 DV 디버그 체크리스트

### 흔한 오해

!!! danger "❓ 오해 1 — 'Vector DB 가 모든 검색을 대체한다'"
    **실제**: 의미 검색은 정확한 _키워드 매칭_ (코드 식별자, 약어, 레지스터 이름) 에 약합니다. `TLB_INV_CTRL` 같은 사내 식별자는 임베딩 모델이 본 적 없어 generic 한 의미만 잡힙니다. **Hybrid (dense + sparse/BM25) 가 production 표준**.<br>
    **왜 헷갈리는가**: 최근 hype 로 "vector = 만능" 인상.

!!! danger "❓ 오해 2 — 'Embedding 모델은 차원이 클수록 좋다'"
    **실제**: 차원 ↑ → 메모리/연산 ↑ + 도메인 적합성과 무관. 1024 차원 BGE-large (326 MB) 가 4096 차원 모델보다 retrieval 점수가 높을 수도 있음. **MTEB Retrieval 점수 + 도메인 적합도** 가 차원보다 우선.

!!! danger "❓ 오해 3 — 'IVF 의 nprobe 는 클수록 정확'"
    **실제**: nprobe = nlist 면 brute-force 와 동일 (정확하지만 느림). 보통 `nprobe = sqrt(nlist)` 부근에서 정확도 95% 와 속도의 균형점이 있고, 그 이상은 비용만 증가.

!!! danger "❓ 오해 4 — '한 번 만든 인덱스는 영원히 쓴다'"
    **실제**: (1) 임베딩 모델을 교체하면 좌표계가 바뀌므로 _전체 재인덱싱_ 필요. (2) 문서가 갱신되면 incremental update — FAISS 는 native incremental delete 가 약하므로 주기적 재빌드.

!!! danger "❓ 오해 5 — 'Chunk 가 작을수록 정밀'"
    **실제**: Chunk 가 너무 작으면 _문맥_ 이 잘려 의미 임베딩이 부정확 (recall ↓). 보통 256~1024 토큰이 sweet spot. 문서 _타입_ 에 따라 다르게 잘라야 함 (§5.4).

### DV 디버그 체크리스트 (RAG 인덱스 운용 시 자주 만나는 실패)

| 증상 | 1차 의심 | 어디 보나 |
|---|---|---|
| 같은 검색어가 _완전히_ 다른 결과 (이전과 비교) | 임베딩 모델 교체 후 인덱스 미재빌드 | 인덱스 메타의 `model_name` vs 현재 모델 |
| 사내 식별자 (`TLB_INV_CTRL`) 검색이 무관한 청크 반환 | 의미 검색만 사용 (sparse 부재) | BM25 추가 → Hybrid 로 |
| 검색이 너무 느림 (수백 ms+) | brute-force IndexFlat 사용 + N 큼 | IVF/HNSW 로 전환, nprobe 튜닝 |
| 메모리 OOM | HNSW + 큰 차원 + 많은 vector | PQ 양자화 또는 IVF+PQ |
| 청크 경계에서 정보 잘림 (recall ↓) | overlap = 0 또는 chunk_size 너무 작음 | overlap = 10-20% 로 |
| recall 은 좋은데 LLM 답변이 hallucinate | 검색 자체는 OK, LLM 단의 문제 → [Module 04](04_rag.md) §6 |
| 다국어 (한/영) 혼용 검색 품질 낮음 | 단일 언어 모델 사용 | Cohere embed-v3 / BGE-M3 같은 다국어 모델 |
| 인덱스 빌드 후 검색이 원하는 결과를 _전혀_ 못 찾음 | embed normalize 안 함 + cosine vs L2 불일치 | `normalize_embeddings=True` + `IndexFlatIP` 매칭 |

---

## 7. 핵심 정리 (Key Takeaways)

- **Embedding = 의미를 좌표로** — 의미가 비슷한 텍스트가 가까운 벡터.
- **ANN 알고리즘** — IVF (cluster), HNSW (graph), PQ (compression). 선택은 데이터 규모와 메모리 예산.
- **FAISS** — Facebook AI 의 표준 ANN 라이브러리. 수십~수억 벡터를 단일 머신에서 처리.
- **임베딩 모델 선정** — MTEB 벤치마크 + 도메인 특화 fine-tune 검토 + _보안_ (로컬/API).
- **품질 평가** — top-k recall, MRR, nDCG. retrieval 이 망가지면 LLM 이 아무리 좋아도 답이 망가진다.

!!! warning "실무 주의점 — Embedding 모델 교체 시 기존 인덱스 전체 재구축 필요"
    **현상**: RAG 운영 중 더 성능 좋은 Embedding 모델로 교체하면, 기존 벡터 인덱스와 새 모델의 벡터 공간이 달라 검색 결과가 완전히 깨진다. 오류 없이 응답이 나오지만 관련 없는 문서가 검색되어 hallucination 이 증가한다.

    **원인**: 각 Embedding 모델은 고유한 벡터 공간을 가지며, 모델이 다르면 같은 문장도 다른 방향의 벡터로 인코딩된다.

    **점검 포인트**: 모델 교체 후 기존 인덱스의 `model_name` 메타데이터와 현재 사용 모델이 일치하는지 확인. Retrieval 정확도 지표(Top-5 Recall) 를 교체 전후 비교하고, 불일치 시 전체 문서에 대해 재임베딩 및 인덱스 재구축 필수.

---

## 다음 모듈

→ [Module 04 — RAG (Retrieval-Augmented Generation)](04_rag.md): embedding/vector DB 를 LLM 호출과 결합.

[퀴즈 풀어보기 →](quiz/03_embedding_vectordb_quiz.md)


--8<-- "abbreviations.md"
