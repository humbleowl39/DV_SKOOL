# AI Engineering 용어집

이 페이지는 **AI Engineering** 코스의 핵심 용어 모음입니다. 각 항목은 ISO 11179 형식(Definition / Source / Related / Example / See also) 을 따릅니다.

---

## A

### Agent
- **Definition.** LLM 을 의사결정 엔진으로 사용해 도구 호출 · 메모리 · 단계별 계획을 통해 다단계 task 를 자율적으로 수행하는 시스템.
- **Source.** Common AI engineering usage; ReAct paper (Yao et al., 2022).
- **Related.** Tool, Memory, Planner, ReAct.
- **Example.** "Repo 검색 → 코드 작성 → 테스트 실행 → 실패 시 수정" 루프를 반복하는 코딩 agent.
- **See also.** [Module 05](05_agent_architecture.md).

### ANN (Approximate Nearest Neighbor)
- **Definition.** 정확한 nearest neighbor 검색 대신 약간의 정확도를 양보하여 대규모 벡터에서 빠르게 후보를 찾는 알고리즘 군.
- **Source.** Information retrieval literature.
- **Related.** FAISS, HNSW, IVF, PQ.
- **Example.** 1억 임베딩에서 top-10 검색을 1ms 안에 수행.
- **See also.** [Module 03](03_embedding_vectordb.md).

---

## C

### Chain-of-Thought (CoT)
- **Definition.** LLM 이 최종 답을 내기 전에 중간 추론 단계를 출력하도록 prompt 로 유도하는 기법.
- **Source.** Wei et al., 2022.
- **Related.** Few-shot, Self-Consistency.
- **Example.** "Let's think step by step" 한 줄 추가만으로 GSM8K 수학 문제 정확도가 크게 오른다.
- **See also.** [Module 02](02_prompt_engineering.md).

### Context Window
- **Definition.** LLM 이 한 번의 호출에서 입력으로 받을 수 있는 토큰 수의 상한.
- **Source.** LLM specifications (e.g., GPT-4, Claude).
- **Related.** Token, KV Cache, Long-Context.
- **Example.** Claude 3 Opus 200k tokens, GPT-4 Turbo 128k tokens.
- **See also.** [Module 01](01_llm_fundamentals.md).

---

## E

### Embedding
- **Definition.** 텍스트(또는 이미지/코드) 를 의미가 보존되도록 고정 차원의 실수 벡터로 변환한 표현.
- **Source.** Common deep learning terminology.
- **Related.** Cosine Similarity, Vector DB, BGE.
- **Example.** "고양이" 와 "냥이" 임베딩의 cosine 유사도가 0.9 이상.
- **See also.** [Module 03](03_embedding_vectordb.md).

---

## F

### FAISS
- **Definition.** Facebook AI Research 가 공개한 대규모 ANN 검색 라이브러리로 IVF/HNSW/PQ 등의 인덱스를 제공한다.
- **Source.** Johnson et al., 2017.
- **Related.** ANN, Vector DB.
- **Example.** `index.search(query, k=10)` 한 줄로 top-10 검색.
- **See also.** [Module 03](03_embedding_vectordb.md).

### Few-shot Learning (In-Context)
- **Definition.** 모델 가중치를 변경하지 않고 prompt 안에 예시를 몇 개 보여주어 모델 동작을 desired pattern 에 맞추는 방식.
- **Source.** Brown et al., 2020 (GPT-3 paper).
- **Related.** Zero-shot, CoT.
- **Example.** 분류 prompt 안에 (입력, 라벨) 쌍을 5개 동봉.
- **See also.** [Module 02](02_prompt_engineering.md).

### Fine-tuning
- **Definition.** 사전학습된 LLM 의 가중치를 도메인 데이터로 추가 학습시켜 형식·스타일·라벨 분포를 모델 내재화하는 방법.
- **Source.** Standard transfer learning.
- **Related.** LoRA, PEFT, RAG, Prompt.
- **Example.** SystemVerilog 코드 데이터셋으로 LoRA fine-tune.
- **See also.** [Module 06](06_strategy_selection.md).

---

## H

### Hallucination
- **Definition.** LLM 이 사실과 무관한 그러나 그럴듯한 출력을 생성하는 현상.
- **Source.** Common LLM failure mode.
- **Related.** RAG, Faithfulness, Grounding.
- **Example.** 존재하지 않는 SystemVerilog 시스템 함수 이름을 자신 있게 호출.
- **See also.** [Module 04](04_rag.md).

---

## L

### LLM (Large Language Model)
- **Definition.** Transformer 기반의 대규모 사전학습 언어 모델로, 입력 토큰 시퀀스로부터 다음 토큰의 확률 분포를 출력한다.
- **Source.** Common AI literature; GPT-3 (Brown et al., 2020).
- **Related.** Transformer, Token, Context Window.
- **Example.** GPT-4, Claude 3, Llama 3.
- **See also.** [Module 01](01_llm_fundamentals.md).

---

## M

### MCP (Model Context Protocol)
- **Definition.** Anthropic 이 제안한 LLM-도구 인터페이스 표준으로, 동일한 도구를 여러 에이전트/IDE 가 재사용할 수 있게 한다.
- **Source.** Anthropic, 2024.
- **Related.** Tool, Agent.
- **Example.** FAISS 검색 도구를 MCP server 로 노출 → Claude Code, VS Code 모두에서 사용.
- **See also.** [Module 05](05_agent_architecture.md).

### MoE (Mixture of Experts)
- **Definition.** 모든 입력 토큰을 모든 파라미터에 통과시키지 않고, 라우터가 선택한 일부 expert 만 활성화하는 sparse 아키텍처.
- **Source.** Shazeer et al., 2017; Mixtral.
- **Related.** Sparse model, Top-K routing.
- **Example.** Mixtral 8x7B 는 47B 총 파라미터 중 토큰당 13B 만 사용.
- **See also.** [Module 01](01_llm_fundamentals.md).

---

## P

### Prompt Engineering
- **Definition.** LLM 의 가중치를 변경하지 않고 입력(prompt) 의 구조·예시·지시문을 설계하여 출력 품질을 개선하는 작업.
- **Source.** Common practice.
- **Related.** Few-shot, CoT, System Prompt.
- **Example.** 역할 지정 + 출력 형식 지정 + few-shot 예시.
- **See also.** [Module 02](02_prompt_engineering.md).

---

## Q

### Quantization
- **Definition.** 모델 가중치/활성을 더 낮은 비트(INT8, INT4 등) 로 표현하여 메모리/연산 비용을 줄이는 기법.
- **Source.** Common deep learning optimization.
- **Related.** AWQ, GPTQ, GGUF.
- **Example.** Llama 3 70B 를 INT4 로 ~35GB 로 줄여 A100 1장에서 실행.
- **See also.** [Module 01](01_llm_fundamentals.md).

---

## R

### RAG (Retrieval-Augmented Generation)
- **Definition.** 사용자 질의에 대해 외부 지식 베이스에서 관련 컨텍스트를 검색해 LLM 입력에 주입함으로써 답변의 사실성과 최신성을 강화하는 아키텍처.
- **Source.** Lewis et al., 2020.
- **Related.** Embedding, Vector DB, Hybrid Search.
- **Example.** "사내 spec 문서를 검색해 답변하는 챗봇".
- **See also.** [Module 04](04_rag.md).

### ReAct
- **Definition.** Reasoning(생각) 과 Acting(도구 호출) 을 번갈아 가며 작동하는 agent 패턴.
- **Source.** Yao et al., 2022.
- **Related.** Plan-and-Execute, Reflexion, Tool-use.
- **Example.** "검색 → 결과 reasoning → 다음 검색" 의 반복.
- **See also.** [Module 05](05_agent_architecture.md).

### Re-ranking
- **Definition.** 1차 검색의 top-N 결과를 cross-encoder 등 정밀 모델로 재정렬하여 상위 결과의 정확도를 끌어올리는 단계.
- **Source.** Information retrieval literature.
- **Related.** Cross-encoder, BM25, Hybrid Search.
- **Example.** ANN top-20 → cross-encoder → top-5.
- **See also.** [Module 04](04_rag.md).

---

## S

### Self-Consistency
- **Definition.** 같은 prompt 로 LLM 을 여러 번 샘플링한 후 다수결/투표로 최종 답을 정하여 robustness 를 높이는 기법.
- **Source.** Wang et al., 2022.
- **Related.** CoT, Sampling Temperature.
- **Example.** 수학 문제를 5번 풀려서 가장 많이 나온 답 채택.
- **See also.** [Module 02](02_prompt_engineering.md).

---

## T

### Token
- **Definition.** LLM 이 처리하는 최소 입력 단위로, 단어/서브워드/문자 단위로 정의된다 (BPE, SentencePiece 등).
- **Source.** Common NLP terminology.
- **Related.** Tokenizer, Context Window, BPE.
- **Example.** "ChatGPT" 는 BPE 로 ["Chat", "G", "PT"] 같이 분할될 수 있다.
- **See also.** [Module 01](01_llm_fundamentals.md).

### Transformer
- **Definition.** Self-Attention 과 FFN 블록을 쌓아 입력 시퀀스 토큰 간 관계를 모델링하는 신경망 아키텍처.
- **Source.** Vaswani et al., 2017.
- **Related.** Self-Attention, Position Embedding, FFN.
- **Example.** GPT, BERT, Llama 모두 Transformer 기반.
- **See also.** [Module 01](01_llm_fundamentals.md).

### Tool (Agent context)
- **Definition.** Agent 가 호출 가능한 외부 함수/API/도메인 동작으로, 입력 schema 와 출력 형식이 명확히 정의된 인터페이스.
- **Source.** Common agent literature.
- **Related.** MCP, Function Calling.
- **Example.** `search_repo`, `run_simulation`, `analyze_log`.
- **See also.** [Module 05](05_agent_architecture.md).
