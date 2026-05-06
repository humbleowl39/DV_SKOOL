# AI Engineering for DV — 개요 및 컨셉 맵

## 학습 플랜
- **레벨**: Intermediate → Advanced (RAG/FAISS 실무 구축 경험 + DVCon/DAC 논문 기반)
- **목표**: LLM/RAG/Agent 아키텍처를 화이트보드에 그리며, DV 도메인 적용 전략과 트레이드오프를 논리적으로 설명할 수 있는 수준

## 핵심 용어집 (Glossary)

### 모델 아키텍처

| 약어 | 풀네임 | 설명 |
|------|--------|------|
| **LLM** | Large Language Model | 수십억~수천억 파라미터의 대규모 언어 모델 |
| **Transformer** | Transformer Architecture | Self-Attention 기반 신경망 아키텍처, RNN 대비 병렬화에 유리 |
| **Self-Attention** | Self-Attention Mechanism | 입력 토큰 간 상호 의존성을 학습하는 메커니즘 (Q·K·V 연산) |
| **MoE** | Mixture of Experts | Sparse 활성화로 대규모 모델을 효율적으로 구현하는 구조 |
| **FFN** | Feed-Forward Network | Transformer 내 비선형 변환 레이어 |
| **BPE** | Byte-Pair Encoding | 빈도 기반 서브워드 토큰화 방식 |

### 최적화 기법

| 약어 | 풀네임 | 설명 |
|------|--------|------|
| **KV Cache** | Key-Value Cache | 이전 토큰의 K,V를 캐싱하여 재계산 방지 |
| **GQA** | Grouped-Query Attention | 쿼리와 키/값 헤드 수 비율을 최적화하여 메모리 절감 |
| **Flash Attention** | — | GPU 메모리 계층 최적화로 Attention 연산 가속 |
| **RoPE** | Rotary Position Embedding | 상대 위치를 벡터 회전으로 인코딩하는 기법 |

### 학습 & 파인튜닝

| 약어 | 풀네임 | 설명 |
|------|--------|------|
| **SFT** | Supervised Fine-Tuning | 지시 따르기 능력을 강화하는 지도 학습 |
| **RLHF** | Reinforcement Learning from Human Feedback | 인간 선호도 기반 정렬 학습 |
| **DPO** | Direct Preference Optimization | Reward Model 없이 직접 선호도를 학습 |
| **LoRA** | Low-Rank Adaptation | 0.1~1% 파라미터만 학습하는 경량 파인튜닝 |
| **Quantization** | — | FP32→INT8→INT4로 정밀도를 줄여 모델 경량화 |

### 프롬프트 엔지니어링 & 추론

| 약어 | 풀네임 | 설명 |
|------|--------|------|
| **ICL** | In-Context Learning | 프롬프트 내 예시로 패턴을 학습하는 방식 (Zero/Few-shot) |
| **CoT** | Chain-of-Thought | 단계별 추론 과정을 명시적으로 생성하는 기법 |
| **RAG** | Retrieval-Augmented Generation | 외부 지식을 검색하여 프롬프트에 삽입 후 답변 생성 |
| **ReAct** | Reasoning + Acting | Thought-Action-Observation 루프 기반 Agent 패턴 |

### 임베딩 & 벡터 DB

| 약어 | 풀네임 | 설명 |
|------|--------|------|
| **Embedding** | Text Embedding | 텍스트를 의미 보존 고차원 벡터로 변환 |
| **FAISS** | Facebook AI Similarity Search | Meta의 벡터 유사도 검색 라이브러리 |
| **Vector DB** | Vector Database | 벡터를 저장하고 유사도 기반 검색하는 데이터베이스 |

### DV 도메인 연결

| 약어 | 풀네임 | 설명 |
|------|--------|------|
| **V-Plan** | Verification Plan | 검증 목표, 시나리오, 커버리지를 정의하는 전략 문서 |
| **IP-XACT** | IP eXtensible Attributes and Constraints | IP 메타데이터(주소 맵, 레지스터) 표준 XML 형식 |
| **MCP** | Model Context Protocol | LLM과 외부 도구를 연결하는 표준 프로토콜 |
| **Function Calling** | — | LLM이 JSON으로 도구 호출을 명시하는 기능 |

---

## 컨셉 맵

```
                    +-------------------+
                    |    LLM 기본 구조   |
                    | (Transformer/Attn)|
                    +---------+---------+
                              |
            +-----------------+-----------------+
            |                 |                 |
   +--------+------+  +------+-------+  +------+--------+
   | Prompt Eng.   |  | RAG          |  | Fine-tuning   |
   | & In-Context  |  | (검색 증강)  |  | (모델 학습)   |
   | Learning      |  |              |  |               |
   +--------+------+  +------+-------+  +------+--------+
            |                 |                 |
            |          +------+-------+         |
            |          | Embedding &  |         |
            |          | Vector DB    |         |
            |          | (FAISS)      |         |
            |          +------+-------+         |
            |                 |                 |
            +-----------------+-----------------+
                              |
                    +---------+---------+
                    |   Agent 아키텍처  |
                    | (Tool/Plan/Memory)|
                    +---------+---------+
                              |
                    +---------+---------+
                    | DV/EDA 도메인     |
                    | 적용 사례         |
                    +-------------------+
```

## 학습 단위 (Units)

| # | 단위 | 핵심 질문 |
|---|------|----------|
| 1 | **LLM 기본 구조** | Transformer와 Attention은 어떻게 동작하고, 왜 강력한가? |
| 2 | **Prompt Engineering & In-Context Learning** | LLM의 출력을 어떻게 제어하고 최적화하는가? |
| 3 | **Embedding & Vector DB (FAISS)** | 텍스트를 벡터로 변환하고 유사도를 어떻게 검색하는가? |
| 4 | **RAG (Retrieval-Augmented Generation)** | 외부 지식을 LLM에 어떻게 주입하고, 왜 Fine-tuning 대신 사용하는가? |
| 5 | **Agent 아키텍처** | LLM이 도구를 사용하고 계획을 세우는 자율 시스템은 어떻게 구축하는가? |
| 6 | **Fine-tuning vs RAG vs Prompt — 전략 선택** | 언제 어떤 접근법을 선택해야 하는가? |
| 7 | **DV/EDA 도메인 적용** | AI를 검증 자동화에 어떻게 적용했고, 어떤 성과를 냈는가? |

## 이력서 연결 포인트

| 이력서 항목 | 관련 Unit | 면접 시 활용 |
|------------|----------|-------------|
| RAG & FAISS (DVCon 2025) | Unit 3, 4, 7 | IP DB 인덱싱 → 검증 시나리오 매핑 |
| LLM-Based Test Generation | Unit 1, 2, 7 | 테스트 명령/V-Plan 자동 생성 |
| Hybrid Data Extraction | Unit 4, 7 | IP-XACT + 시맨틱 → RAG 파이프라인 |
| AI-Assisted UVM 자동화 (DAC 2026) | Unit 5, 7 | UVM 컴포넌트 자동 생성 |
| AI Expert (삼성+서울대) | 전체 | AI 전문성의 공식 자격 증명 |
| 293/216 Gap 발견 | Unit 4, 7 | 정량적 성과 (2.75% / 4.99% gap rate) |
