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
  <a class="page-toc-link" href="#학습-목표">학습 목표</a>
  <a class="page-toc-link" href="#선수-지식">선수 지식</a>
  <a class="page-toc-link" href="#왜-이-모듈이-중요한가">왜 이 모듈이 중요한가</a>
  <a class="page-toc-link" href="#핵심-개념">핵심 개념</a>
  <a class="page-toc-link" href="#embedding이란">Embedding이란?</a>
  <a class="page-toc-link" href="#embedding-모델">Embedding 모델</a>
  <a class="page-toc-link" href="#faiss-facebook-ai-similarity-search">FAISS (Facebook AI Similarity Search)</a>
  <a class="page-toc-link" href="#chunking-전략-문서를-어떻게-분할하는가">Chunking 전략 — 문서를 어떻게 분할하는가</a>
  <a class="page-toc-link" href="#대안-다른-vector-db">대안: 다른 Vector DB</a>
  <a class="page-toc-link" href="#qa">Q&A</a>
  <a class="page-toc-link" href="#핵심-정리">핵심 정리</a>
  <a class="page-toc-link" href="#다음-단계">다음 단계</a>
</div>
<!-- DV-SKOOL-CH-TOC:end -->

## 학습 목표

이 모듈을 마치면:

1. (Remember) Embedding, ANN, FAISS, BGE 의 정의를 구분할 수 있다.
2. (Understand) Cosine similarity 가 왜 의미 검색의 표준이 되었는지 설명할 수 있다.
3. (Apply) 사내 코드/문서를 chunk → embed → FAISS index 로 만드는 파이프라인을 설계할 수 있다.
4. (Analyze) IVF · HNSW · PQ 의 메모리/지연/정확도 trade-off 를 데이터 규모별로 분석할 수 있다.
5. (Evaluate) 검색 품질을 MRR / nDCG 로 평가하고, 임베딩 모델 후보를 선정할 수 있다.

## 선수 지식

- Module 01–02 (LLM 기본, prompt)
- 기본 선형대수 (벡터 내적, 노름)
- 검색 시스템에 대한 직관 (precision / recall)

## 왜 이 모듈이 중요한가

LLM 의 context window 만으로는 대규모 문서·코드 베이스를 다룰 수 없다. **임베딩 + 벡터 DB 가 외부 메모리** 역할을 한다. 이 두 컴포넌트의 품질이 RAG / Agent 시스템의 상한선이다.

---

!!! tip "💡 이해를 위한 비유"
    **Embedding + Vector DB** ≈ **도서관 의미 색인 — "비슷한 의미" 로 검색**

    문서를 의미 보존 벡터로 변환 → 쿼리 벡터와 cosine 유사도 계산 → 가까운 문서 반환. 의미적 검색이 키워드 검색을 대체.

---

## 핵심 개념
**Embedding = 텍스트를 의미를 보존하는 고차원 벡터로 변환. Vector DB = 이 벡터들을 저장하고, 의미적 유사도로 빠르게 검색하는 데이터베이스. RAG의 핵심 인프라.**

!!! danger "❓ 흔한 오해"
    **오해**: Vector DB 가 모든 검색을 대체한다

    **실제**: 의미 검색은 keyword exact match (코드 식별자, 약어) 에 약함. Hybrid (dense + sparse/BM25) 가 production 표준.

    **왜 헷갈리는가**: 최근 hype 로 "vector = 만능" 이라는 인상. 실제로는 보완 관계.
---

## Embedding이란?

### 텍스트 → 벡터 변환

```
"TLB invalidation" → [0.12, -0.45, 0.78, ..., 0.33]  (768~3072 차원)
"TLB flush"        → [0.11, -0.43, 0.80, ..., 0.31]  (유사한 벡터)
"page fault"       → [0.55, 0.22, -0.10, ..., -0.67] (다른 벡터)

핵심 속성:
  의미가 비슷한 텍스트 → 벡터 공간에서 가까움
  의미가 다른 텍스트 → 벡터 공간에서 멀어짐
```

### 유사도 측정

| 메트릭 | 수식 | 특징 |
|--------|------|------|
| Cosine Similarity | cos(θ) = A·B / (‖A‖×‖B‖) | 방향 기반, 크기 무관, 가장 일반적 |
| Euclidean Distance | ‖A - B‖₂ | 절대 거리, 정규화 필요 |
| Dot Product | A·B | 빠르지만 벡터 크기에 민감 |

```
Cosine Similarity 예시:

  sim("TLB invalidation", "TLB flush") = 0.95   ← 매우 유사
  sim("TLB invalidation", "page fault") = 0.42  ← 관련 있지만 다름
  sim("TLB invalidation", "boot device") = 0.08 ← 거의 무관
```

---

## Embedding 모델

### 주요 Embedding 모델

| 모델 | 차원 | 특징 | 용도 |
|------|------|------|------|
| OpenAI text-embedding-3-small | 1536 | API 기반, 편리 | 일반적 |
| OpenAI text-embedding-3-large | 3072 | 높은 정확도 | 고정밀 검색 |
| Sentence-BERT (all-MiniLM) | 384 | 오픈소스, 경량 | 로컬 배포 |
| BGE-large | 1024 | 오픈소스, 고성능 | 한국어 포함 |
| Cohere embed-v3 | 1024 | 다국어 강점 | 다국어 RAG |

### Embedding 모델은 어떻게 학습되는가? — Contrastive Learning

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
  → Hard Negative를 많이 포함할수록 임베딩 품질 향상

학습 프레임워크:
  - Sentence-BERT: Siamese Network + Contrastive Loss
  - E5: "query: " / "passage: " 프리픽스로 비대칭 검색 최적화
  - BGE: RetroMAE 사전학습 + Contrastive Fine-tuning
```

### MTEB 벤치마크 — Embedding 모델 선택 기준

```
MTEB (Massive Text Embedding Benchmark):
  56개 데이터셋, 8개 태스크에서 Embedding 모델 종합 평가

태스크 카테고리:
  - Retrieval: 검색 성능 (RAG의 핵심)
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

### Embedding 모델 선택 기준

```
DV/EDA 도메인에서의 고려사항:

  1. 도메인 적합성
     - 일반 모델: "TLB"를 일반 영어로 인식
     - 도메인 특화: "TLB"를 MMU의 Translation Lookaside Buffer로 인식
     → 도메인 문서로 Fine-tune하거나, Chunk 전략으로 보완

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

---

## FAISS (Facebook AI Similarity Search)

### FAISS란?

```
FAISS = Meta(Facebook)가 개발한 대규모 벡터 유사도 검색 라이브러리

핵심 기능:
  - 수백만~수십억 벡터에서 밀리초 단위 검색
  - GPU 가속 지원
  - 다양한 인덱스 타입 (정확도 vs 속도 트레이드오프)
  - Python 바인딩으로 쉬운 통합
```

### FAISS 사용 흐름

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

### FAISS 인덱스 타입

| 인덱스 | 검색 방식 | 속도 | 정확도 | 메모리 | 용도 |
|--------|----------|------|--------|--------|------|
| **IndexFlatL2** | 전수 검색 (Brute-force) | 느림 | 100% | 큼 | 소규모 (<100K) |
| **IndexIVFFlat** | 클러스터 기반 근사 검색 | 빠름 | ~95% | 중간 | 중규모 |
| **IndexIVFPQ** | 양자화 + 클러스터 | 매우 빠름 | ~90% | 작음 | 대규모 (수백만+) |
| **IndexHNSW** | 그래프 기반 근사 검색 | 빠름 | ~97% | 큼 | 고정밀 + 속도 |

### IVF (Inverted File Index) 동작 원리

```
1. 학습 단계: K-means로 벡터들을 nlist개 클러스터로 분류
   Cluster 0: [v1, v5, v12, ...]
   Cluster 1: [v2, v7, v23, ...]
   ...

2. 검색 단계:
   쿼리 벡터 → 가장 가까운 nprobe개 클러스터 선택
   → 해당 클러스터 내에서만 정확 검색
   → 전수 검색 대비 nlist/nprobe 배 빠름

   예: nlist=100, nprobe=10 → 10배 빠르지만 일부 결과 누락 가능
```

### DVCon 논문에서의 FAISS 활용

```
IP 데이터베이스 인덱싱:

  1. IP 스펙 문서 → 청크(Chunk)로 분할
  2. 각 청크 → Embedding 모델 → 벡터
  3. 벡터 → FAISS 인덱스에 저장

  검색 시:
  "sysMMU TLB invalidation 검증 시나리오"
  → 쿼리 임베딩 → FAISS 검색 → 관련 IP 스펙 청크 반환
  → LLM에 전달 → 검증 시나리오 생성

  규모:
  - 수백 개 IP의 스펙 문서 (수천 페이지)
  - 수만~수십만 청크
  → FAISS 없이는 실시간 검색 불가
```

---

## Chunking 전략 — 문서를 어떻게 분할하는가

### 왜 Chunking이 필요한가?

```
문제:
  IP 스펙 문서 = 수백 페이지
  Embedding 모델 입력 한계 = 512~8192 토큰
  LLM Context 한계 = 수천~수십만 토큰

  → 문서 전체를 한 번에 Embedding할 수 없음
  → 적절한 단위로 분할(Chunk)하여 각각 Embedding
```

### Chunking 방법

| 방법 | 동작 | 장단점 |
|------|------|--------|
| Fixed Size | 고정 토큰 수로 분할 (512 토큰) | 간단하지만 의미 단위 무시 |
| Overlap | 고정 크기 + 겹침 영역 (50 토큰) | 경계에서 정보 손실 방지 |
| Semantic | 문단/섹션 단위로 분할 | 의미 보존, 구현 복잡 |
| Recursive | 큰 단위 → 작은 단위로 재귀 분할 | LangChain 기본, 균형 잡힘 |

### DV 도메인 Chunking 고려사항

```
IP 스펙 문서의 특성:
  - 레지스터 정의 = 테이블 형태 → 테이블 단위 Chunk
  - 프로토콜 시퀀스 = 연속적 흐름 → 시퀀스 단위 Chunk
  - 블록 다이어그램 설명 = 섹션 단위 → 섹션 Chunk

IP-XACT의 특성:
  - XML 구조 → 태그 단위 파싱
  - 레지스터 맵, 버스 인터페이스, 메모리 맵
  → 구조적 파싱 + 시맨틱 설명 결합 (DVCon의 Hybrid Extraction)
```

### Chunking 실전 코드 예시

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
    """IP-XACT XML을 의미 단위로 분할"""
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

### Chunk Size 튜닝 가이드

```
Chunk Size 실험 결과 (일반적 경향):

  Size = 128 토큰: 너무 작음 → 문맥 부족, 검색 정밀도 높지만 Recall 낮음
  Size = 256 토큰: 짧은 정의/설명에 적합 (레지스터 정의 등)
  Size = 512 토큰: 범용적 최적점 (대부분의 RAG 연구 권장)
  Size = 1024 토큰: 긴 문맥 필요 시 (프로토콜 시퀀스, 동작 설명)
  Size = 2048+ 토큰: Context 낭비, 관련 없는 내용 포함 위험

  Overlap = Chunk Size의 10-20% 권장
    512 → overlap 50~100
    1024 → overlap 100~200

DV 도메인 권장:
  레지스터 정의: 256 토큰 (짧고 독립적)
  프로토콜 설명: 512-1024 토큰 (문맥 필요)
  IP 개요: 1024 토큰 (큰 그림)
  → 문서 타입별로 다른 Chunk Size 적용이 최적
```

---

## 대안: 다른 Vector DB

| Vector DB | 특징 | 적합한 경우 |
|-----------|------|-----------|
| **FAISS** | 라이브러리, 자체 서버 불필요, GPU 가속 | 임베디드, 로컬, DV 파이프라인 |
| Chroma | Python 네이티브, 간단한 API | 프로토타이핑, 소규모 |
| Pinecone | 완전 관리형 클라우드 | 프로덕션 서비스 |
| Weaviate | 하이브리드 검색 (벡터 + 키워드) | 복잡한 검색 요구 |
| Milvus | 분산, 대규모 | 수십억 벡터 |
| pgvector | PostgreSQL 확장 | 기존 RDBMS 활용 |

**DVCon 논문에서 FAISS를 선택한 이유**: (1) 로컬 실행 → IP 보안 유지. (2) 라이브러리 → 별도 서버 불필요 → DV 파이프라인에 직접 통합. (3) GPU 가속 → 대규모 IP DB에서도 빠른 검색.

---

## Q&A

**Q: Embedding이란 무엇이고 왜 필요한가?**
> "텍스트를 의미를 보존하는 고차원 벡터로 변환하는 것이다. 의미가 유사한 텍스트는 벡터 공간에서 가깝고, 다른 텍스트는 멀다. 이를 통해 키워드가 아닌 의미 기반 검색이 가능해진다. 예를 들어 'TLB flush'를 검색하면 'TLB invalidation'도 함께 찾아준다 — 키워드 검색으로는 불가능한 것이다."

**Q: FAISS를 왜 선택했나?**
> "세 가지 이유: (1) 보안 — 반도체 IP 정보를 클라우드에 전송하지 않고 로컬에서 실행 가능. (2) 통합 용이성 — 별도 서버 없이 Python 라이브러리로 DV 파이프라인에 직접 통합. (3) 성능 — GPU 가속으로 수만 청크에서도 밀리초 단위 검색. IndexIVFFlat으로 정확도 95% 이상을 유지하면서 검색 속도를 10배 이상 향상시켰다."

**Q: Chunking 전략은 어떻게 결정했나?**
> "DV 도메인의 문서 특성에 맞춰 Hybrid 방식을 사용했다. IP-XACT는 XML 구조적 파싱(레지스터, 버스 인터페이스 단위), IP 스펙은 섹션 기반 시맨틱 Chunking을 적용했다. 이 두 소스를 결합한 것이 DVCon 논문의 'Hybrid Data Extraction'이다."

**Q: Embedding 모델은 어떻게 학습되는가?**
> "Contrastive Learning으로 학습된다. 의미가 유사한 문장 쌍(긍정 쌍)은 벡터 공간에서 가깝게, 다른 문장 쌍(부정 쌍)은 멀게 배치하도록 InfoNCE Loss를 최적화한다. 핵심은 Hard Negative Mining — 'TLB invalidation'과 'TLB lookup'처럼 비슷하지만 다른 의미의 쌍을 부정 샘플로 사용하여 모델이 미세한 의미 차이를 구분하도록 학습한다."

**Q: Embedding 모델을 어떻게 비교/선택하나?**
> "MTEB(Massive Text Embedding Benchmark)가 표준이다. 56개 데이터셋에서 Retrieval, STS, Classification 등 8개 태스크 성능을 종합 평가한다. DV 도메인에서는 보안 요구사항(로컬 실행 필수)이 가장 먼저 필터링 기준이 되고, 그 다음 Retrieval 성능, 마지막으로 모델 크기/속도를 고려한다. 로컬 실행 시 BGE-large(326MB, Retrieval 54.3)가 성능-크기 균형이 좋다."

---
!!! warning "실무 주의점 — Embedding 모델 교체 시 기존 인덱스 전체 재구축 필요"
    **현상**: RAG 운영 중 더 성능 좋은 Embedding 모델로 교체하면, 기존 벡터 인덱스와 새 모델의 벡터 공간이 달라 검색 결과가 완전히 깨진다. 오류 없이 응답이 나오지만 관련 없는 문서가 검색되어 hallucination이 증가한다.

    **원인**: 각 Embedding 모델은 고유한 벡터 공간을 가지며, 모델이 다르면 같은 문장도 다른 방향의 벡터로 인코딩된다.

    **점검 포인트**: 모델 교체 후 기존 인덱스의 `model_name` 메타데이터와 현재 사용 모델이 일치하는지 확인. Retrieval 정확도 지표(Top-5 Recall)를 교체 전후 비교하고, 불일치 시 전체 문서에 대해 재임베딩 및 인덱스 재구축 필수.

## 핵심 정리

- **Embedding = 의미를 좌표로** — 의미가 비슷한 텍스트가 가까운 벡터.
- **ANN 알고리즘** — IVF (cluster), HNSW (graph), PQ (compression). 선택은 데이터 규모와 메모리 예산.
- **FAISS** — Facebook AI 의 표준 ANN 라이브러리. 수십~수억 벡터를 단일 머신에서 처리.
- **임베딩 모델 선정** — MTEB 벤치마크 + 도메인 특화 fine-tune 검토.
- **품질 평가** — top-k recall, MRR, nDCG. retrieval 이 망가지면 LLM 이 아무리 좋아도 답이 망가진다.

## 다음 단계

- 다음 모듈: [RAG →](../04_rag/) — embedding/vector DB 를 LLM 호출과 결합.
- 퀴즈: [Module 03 Quiz](../quiz/03_embedding_vectordb_quiz/) — ANN, FAISS, 모델 선택 5문항.
- 실습: 자기 프로젝트 문서 1000개를 chunking → embedding → FAISS index → top-5 검색까지 직접 만들고, 5개 query 에 대해 정성 평가.

<div class="chapter-nav">
  <a class="nav-prev" href="../02_prompt_engineering/">
    <div class="nav-label">◀ 이전</div>
    <div class="nav-title">Prompt Engineering & In-Context Learning</div>
  </a>
  <a class="nav-next" href="../04_rag/">
    <div class="nav-label">다음 ▶</div>
    <div class="nav-title">RAG (Retrieval-Augmented Generation)</div>
  </a>
</div>
