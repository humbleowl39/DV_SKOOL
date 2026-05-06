# Module 01 — LLM Fundamentals

## 학습 목표 (Learning Objectives)

이 모듈을 마치면:

1. (Remember) Transformer 의 self-attention, position embedding, FFN 의 역할을 정의할 수 있다.
2. (Understand) "다음 토큰 확률 예측" 이 어떻게 임의 길이의 텍스트 생성으로 이어지는지 설명할 수 있다.
3. (Apply) 주어진 시나리오(코드 생성, 요약, 추론) 에 적합한 모델 크기/형태(MoE, Quantization) 를 선택할 수 있다.
4. (Analyze) Context window, KV cache, batch size 가 latency/throughput 에 미치는 영향을 분해할 수 있다.
5. (Evaluate) 제품 상황(클라우드 API vs on-prem) 에 맞는 LLM 배포 전략을 평가할 수 있다.

## 선수 지식 (Prerequisites)

- Python · NumPy 기본
- 신경망의 기본 개념 (forward pass, gradient descent)
- 토큰 / 임베딩 / softmax 라는 단어를 들어 본 적이 있어야 함

## 왜 이 모듈이 중요한가 (Why it matters)

LLM 을 "마법 박스" 가 아니라 **자기회귀 토큰 생성기** 로 이해해야 prompt, context, throttling, memory cost 같은 실무 결정을 합리적으로 할 수 있다. 이 모듈은 이후 prompt engineering / RAG / agent 모듈의 모든 결정을 떠받치는 토대다.

---

## 핵심 개념
**LLM = Transformer 아키텍처 기반의 대규모 언어 모델. Self-Attention으로 입력 토큰 간 관계를 학습하고, 다음 토큰을 확률적으로 예측하는 방식으로 텍스트를 생성한다.**

---

## Transformer 아키텍처

### 왜 Transformer가 혁명적인가?

```
이전 (RNN/LSTM):
  토큰1 → 토큰2 → 토큰3 → ... → 토큰N
  순차 처리 → 병렬화 불가, 긴 문장에서 정보 손실

Transformer:
  토큰1 ←→ 토큰2 ←→ 토큰3 ←→ ... ←→ 토큰N
  모든 토큰이 동시에 서로를 참조 → 완전 병렬화, 장거리 의존성 포착
```

| 항목 | RNN/LSTM | Transformer |
|------|---------|-------------|
| 처리 방식 | 순차적 | 병렬 |
| 장거리 의존성 | Vanishing Gradient 문제 | Attention으로 직접 참조 |
| 학습 속도 | 느림 (순차) | 빠름 (GPU 병렬화) |
| 확장성 | 모델 크기 한계 | 수천억 파라미터까지 확장 |

### Transformer 구조 (Decoder-Only, GPT 계열)

```
입력: "The cat sat on the"

+--------------------------------------------------+
|                Token Embedding                    |
|  "The" → [0.1, -0.3, ...] (d_model 차원 벡터)    |
|  "cat" → [0.5, 0.2, ...]                         |
|  ...                                              |
+--------------------------------------------------+
         |
         v
+--------------------------------------------------+
|           Positional Encoding                     |
|  위치 정보 추가 (Transformer는 순서를 모르므로)    |
|  Token Embedding + Position Embedding             |
+--------------------------------------------------+
         |
         v (× N layers, 예: 32, 80, 128 레이어)
+--------------------------------------------------+
|           Transformer Block                       |
|                                                   |
|  +--------------------------------------------+  |
|  | Multi-Head Self-Attention                   |  |
|  | (각 토큰이 다른 모든 토큰을 참조)            |  |
|  +--------------------------------------------+  |
|         |                                         |
|  +--------------------------------------------+  |
|  | Feed-Forward Network (FFN)                  |  |
|  | (비선형 변환)                                |  |
|  +--------------------------------------------+  |
|         |                                         |
|  (+ Residual Connection + Layer Normalization)    |
+--------------------------------------------------+
         |
         v
+--------------------------------------------------+
|           Output Head                             |
|  벡터 → 어휘 크기의 확률 분포                     |
|  argmax → "mat" (다음 토큰 예측)                  |
+--------------------------------------------------+
```

---

## Self-Attention 메커니즘

### 핵심 수식

```
Attention(Q, K, V) = softmax(QK^T / √d_k) × V

Q (Query):  "이 토큰이 알고 싶은 것"
K (Key):    "각 토큰이 제공할 수 있는 정보의 인덱스"
V (Value):  "각 토큰이 실제로 제공하는 정보"

과정:
1. 입력 X에서 Q, K, V를 선형 변환으로 생성
   Q = X × W_Q,  K = X × W_K,  V = X × W_V

2. Q와 K의 내적으로 유사도(Attention Score) 계산
   Score = Q × K^T  (어떤 토큰에 주목할지)

3. √d_k로 나누어 스케일링 (값이 너무 커지는 것 방지)

4. Softmax로 확률화 (합 = 1)

5. V와 곱하여 가중 합산 → 출력
```

### 직관적 이해 — 문장에서의 Attention

```
"The cat sat on the mat because it was tired"

"it"이 참조해야 할 토큰은?
  → "cat" (높은 Attention Score)
  → "mat" (낮은 Score — 의미적으로 "it"은 "cat"을 지칭)

Attention Score (예시):
  it → cat:     0.65  ← 가장 높음
  it → mat:     0.10
  it → sat:     0.08
  it → tired:   0.12
  it → others:  0.05
```

### Multi-Head Attention

```
왜 여러 개의 Head?

  Head 1: 문법적 관계에 주목 (주어-동사)
  Head 2: 의미적 관계에 주목 (대명사-선행사)
  Head 3: 위치적 관계에 주목 (인접 토큰)
  ...

  각 Head가 다른 관점에서 Attention을 수행
  → 결과를 Concatenate → 다양한 관계를 동시에 포착

  MultiHead(Q, K, V) = Concat(head_1, ..., head_h) × W_O
  head_i = Attention(Q × W_Q_i, K × W_K_i, V × W_V_i)
```

---

## Tokenization — 텍스트를 숫자로

### 토큰화 방식

| 방식 | 예시 | 특징 |
|------|------|------|
| Word-level | "playing" → [playing] | 어휘가 매우 커짐, OOV 문제 |
| Character-level | "playing" → [p,l,a,y,i,n,g] | 어휘 작지만 시퀀스 길어짐 |
| **BPE (Byte-Pair Encoding)** | "playing" → [play, ing] | 가장 일반적, 빈도 기반 서브워드 |
| SentencePiece | "playing" → [▁play, ing] | 언어 독립적 BPE |

### BPE 동작 원리

```
1. 초기: 모든 문자를 개별 토큰으로 시작
   "l o w e r" → [l, o, w, e, r]

2. 가장 빈번한 인접 쌍을 병합
   (l, o) → lo    →  [lo, w, e, r]
   (lo, w) → low  →  [low, e, r]
   (e, r) → er    →  [low, er]
   (low, er) → lower → [lower]

3. 설정된 어휘 크기까지 반복
   GPT-4: ~100K 토큰, Claude: ~100K 토큰
```

### 토큰 수와 비용/성능

```
LLM API 비용 = 입력 토큰 수 + 출력 토큰 수

  영어: ~1 토큰 ≈ 4글자 ≈ 0.75 단어
  한국어: ~1 토큰 ≈ 1-2글자 (비효율적 → 비용 높음)
  코드: 변수명, 키워드 등 → 영어와 유사

  Context Window = 최대 처리 토큰 수
  GPT-4o: 128K, Claude: 200K, Gemini: 1M+

  DV 적용 시:
  - SystemVerilog 파일 전체를 Context에 넣을 수 있는가?
  - 대규모 IP 스펙 문서를 처리할 수 있는가?
  → Context 한계 = RAG가 필요한 이유 중 하나
```

---

## Positional Encoding 발전사

### 왜 위치 정보가 필요한가?

```
Transformer는 입력 순서를 모른다 (순열 불변):
  "cat sat on mat" 와 "mat on sat cat"을 동일하게 처리
  → 위치 정보를 별도로 주입해야 함
```

### 발전 과정

| 세대 | 방식 | 원리 | 한계 |
|------|------|------|------|
| 1세대 | **Sinusoidal** (Transformer 원논문) | sin/cos 함수로 절대 위치 인코딩 | 학습된 위치 관계 표현 불가 |
| 2세대 | **Learned Absolute** (GPT-2, BERT) | 위치 임베딩을 학습 파라미터로 | 학습 길이 초과 시 성능 급락 |
| 3세대 | **RoPE** (Rotary Position Embedding) | Q, K 벡터를 위치에 따라 회전 | 현재 가장 널리 사용 |
| 4세대 | **ALiBi** (Attention with Linear Biases) | Attention Score에 거리 비례 페널티 | 별도 임베딩 불필요, 외삽 강점 |

### RoPE (현재 표준 — LLaMA, Claude, GPT-4 계열)

```
핵심 아이디어:
  Q, K 벡터를 2D 평면에서 위치(m)에 비례하여 회전

  f(q, m) = q × e^(imθ)  (복소수 회전)

  → 두 토큰의 Attention Score가 "상대 위치 (m-n)"에만 의존
  → 절대 위치가 아닌 상대 위치를 자연스럽게 인코딩

왜 강력한가:
  1. 상대 위치 인코딩 → "3번째 뒤의 토큰"이라는 관계를 직접 표현
  2. 외삽 가능 → 학습 시 4K 토큰이어도 추론 시 더 긴 시퀀스 처리 가능
     (NTK-aware scaling, YaRN 등으로 Context 확장)
  3. 구현 간결 → Q, K에만 적용, V는 그대로

DV 적용 관점:
  긴 SystemVerilog 파일(수천 줄)을 처리할 때 위치 외삽이 중요
  → RoPE 기반 모델이 긴 코드 파일에서 더 안정적
```

---

## Attention 복잡도와 최적화

### O(n²) 문제

```
Self-Attention 연산량:
  Q × K^T = (n × d) × (d × n) = n × n 행렬
  
  n = 시퀀스 길이일 때:
    n = 4K   →   16M 연산
    n = 32K  → 1,024M 연산  (64배 증가)
    n = 128K → 16,384M 연산 (1024배 증가)
  
  메모리도 O(n²): Attention Score 행렬 전체를 메모리에 유지해야 함
  → Context Window가 길어질수록 비용이 제곱으로 증가
  → 이것이 긴 Context 처리의 근본적 병목
```

### Flash Attention (Tri Dao, 2022)

```
핵심: Attention 연산을 타일(tile) 단위로 분할하여 GPU SRAM에서 처리

기존:
  전체 QK^T 행렬(O(n²))을 GPU HBM에 저장 → 느린 메모리 접근

Flash Attention:
  블록 단위로 Q, K, V를 SRAM에 로드 → 부분 Attention 계산 → 결합
  → IO 복잡도 O(n²d / M) (M = SRAM 크기)
  → 실측 2-4x 속도 향상, 메모리 O(n)으로 감소

  결과:
  - 같은 GPU에서 더 긴 시퀀스 처리 가능
  - 현재 거의 모든 LLM 학습/추론에 사용
  - Flash Attention 2/3으로 지속 최적화
```

### MQA / GQA (Attention Head 최적화)

```
Multi-Head Attention (MHA):
  Head 수 = h일 때, 각 Head마다 별도 Q, K, V
  KV Cache 크기: h × n × d_k  → 메모리 부담

Multi-Query Attention (MQA):
  Q는 h개 Head, K/V는 1개만 공유
  KV Cache: 1 × n × d_k  → h배 절약
  단점: 품질 약간 하락

Grouped-Query Attention (GQA) — 현재 표준:
  Q는 h개 Head, K/V는 g개 그룹으로 공유 (1 < g < h)
  예: h=32, g=8 → 4개 Q Head가 1개 KV 그룹 공유
  KV Cache: g × n × d_k  → MHA 대비 h/g배 절약
  
  LLaMA 2 70B: GQA 사용 (h=64, g=8)
  → MHA 대비 KV Cache 8배 절약, 품질 거의 동일

  +--------+--------+--------+
  |  MHA   |  GQA   |  MQA   |
  | Q K V  | Q K V  | Q K V  |
  | Q K V  | Q     | Q      |
  | Q K V  | Q K V  | Q      |
  | Q K V  | Q      | Q      |
  +--------+--------+--------+
  KV: h개   KV: g개  KV: 1개
```

---

## KV Cache — 추론 속도의 핵심

### 왜 필요한가?

```
Autoregressive 생성에서의 비효율:

  Step 1: "Write"           → Q,K,V 계산 → "a"
  Step 2: "Write a"         → Q,K,V 전부 재계산 → "UVM"
  Step 3: "Write a UVM"     → Q,K,V 전부 재계산 → "test"
  
  → 이전 토큰의 K, V를 매번 다시 계산 = 낭비

KV Cache:
  Step 1: K₁,V₁ 계산 → 캐시 저장 → "a"
  Step 2: K₂,V₂만 새로 계산 → 캐시에 추가 → "UVM"
  Step 3: K₃,V₃만 새로 계산 → 캐시에 추가 → "test"
  
  → 새 토큰의 Q만 전체 KV 캐시와 Attention → O(n) per step
  → KV Cache 없이는 O(n²) per step
```

### KV Cache 메모리 계산

```
KV Cache 크기 = 2 × n_layers × n_kv_heads × seq_len × d_head × dtype_bytes

예: LLaMA 2 70B (GQA)
  n_layers = 80, n_kv_heads = 8, d_head = 128, FP16 (2 bytes)
  seq_len = 4096일 때:
  = 2 × 80 × 8 × 4096 × 128 × 2 = ~1.3 GB per request

  seq_len = 128K일 때:
  = 2 × 80 × 8 × 131072 × 128 × 2 = ~41 GB per request
  → Context가 길어지면 KV Cache가 모델 가중치보다 클 수 있음

DV 관점:
  긴 SystemVerilog 파일을 Context에 넣을 때 KV Cache 메모리가 급증
  → 필요한 부분만 RAG로 검색하여 주입하는 것이 효율적인 이유
```

---

## MoE (Mixture of Experts) 아키텍처

### 핵심 개념

```
기존 (Dense Model):
  모든 입력이 모든 파라미터를 통과
  → 파라미터 수 = 연산량 (비례)

MoE:
  입력마다 일부 Expert만 활성화 (Sparse Activation)
  → 총 파라미터는 크지만, 토큰당 연산량은 적음

  구조:
  +--------------------------------------------------+
  |  Router (Gate Network)                             |
  |  입력 토큰 → 어떤 Expert를 선택할지 결정           |
  |  Top-K 선택 (보통 K=2)                             |
  +--------------------------------------------------+
       |  |  |  |  |  |  |  |
       v  v  v  v  v  v  v  v
  +----+  +----+  +----+  +----+
  | E1 |  | E2 |  | E3 |  | E8 |  ← Expert (각각 FFN)
  +----+  +----+  +----+  +----+
  
  → 8개 Expert 중 2개만 활성화 = 파라미터 8x, 연산 ~2x
```

### 대표 모델

| 모델 | 총 파라미터 | 활성 파라미터 | Expert 수 | Top-K |
|------|-----------|-------------|----------|-------|
| Mixtral 8x7B | 46.7B | 12.9B | 8 | 2 |
| Mixtral 8x22B | 176B | 39B | 8 | 2 |
| GPT-4 (추정) | ~1.8T | ~220B | 16 | 2 |
| DeepSeek-V2 | 236B | 21B | 160 | 6 |

```
트레이드오프:
  장점: 적은 연산으로 큰 모델의 성능 → 추론 비용 대비 고품질
  단점: 총 파라미터가 크므로 GPU 메모리 많이 필요 (로딩)
       Expert 간 불균형 (load balancing) 문제
       학습 불안정성

DV 관점:
  로컬 배포 시 MoE 모델(Mixtral)은 Dense 모델 대비
  적은 연산으로 높은 성능 → DV 파이프라인 통합에 유리
```

---

## Quantization — 모델 경량화

### 핵심 개념

```
원래 모델: FP32 (32-bit 부동소수점)
  7B 모델 = 7 × 10⁹ × 4 bytes = 28 GB

양자화:
  FP32 → FP16 → INT8 → INT4
  정밀도를 낮춰 모델 크기와 연산량 감소

  7B 모델 메모리:
  FP32: 28 GB
  FP16: 14 GB  ← 학습 표준
  INT8:  7 GB  ← 추론 최적화
  INT4:  3.5 GB ← 소비자 GPU에서 실행 가능
```

### 양자화 방법

| 방법 | 원리 | 정밀도 손실 | 속도 |
|------|------|-----------|------|
| **RTN** (Round-to-Nearest) | 단순 반올림 | 높음 | 즉시 |
| **GPTQ** | 레이어별 최적 양자화 | 낮음 | 수 시간 |
| **AWQ** (Activation-aware) | 중요 가중치 보존 | 매우 낮음 | 수 시간 |
| **GGUF** (llama.cpp) | CPU 추론 최적화 포맷 | 낮음 | 즉시 |

```
DV 적용 시:
  - 사내 서버(GPU 제한): INT4/INT8 양자화 모델로 배포
  - 예: Llama 3 70B INT4 → ~35GB → A100 1장에서 실행 가능
  - 코드 생성 품질: INT4에서도 FP16 대비 95%+ 유지
  - 보안 + 성능 균형의 현실적 해법
```

---

## Scaling Laws — 모델 크기와 성능의 관계

### Chinchilla Scaling Law (2022)

```
최적 학습 조건:
  모델 파라미터 수(N)와 학습 토큰 수(D)를 동시에 늘려야 함
  최적 비율: D ≈ 20 × N

  예: 70B 모델 → 최소 1.4T 토큰으로 학습해야 최적
      7B 모델 → 최소 140B 토큰

이전 접근 (GPT-3): 큰 모델 + 적은 데이터
Chinchilla 접근: 적절한 모델 + 충분한 데이터
  → 같은 연산 예산으로 더 좋은 성능

결과:
  Chinchilla 70B > Gopher 280B (4배 작지만 더 우수)
  → 이후 LLaMA, Mistral 등 "효율적 학습" 트렌드
```

### Emergent Abilities (창발 능력)

```
모델 크기가 특정 임계점을 넘으면 갑자기 나타나는 능력:

  ~10B: 기본 언어 이해, 간단한 코드
  ~50B: CoT 추론, 복잡한 코드 생성
  ~100B+: 수학 추론, 멀티스텝 계획, 도구 사용

  DV 적용 시:
  - SystemVerilog 코드 생성 → ~50B+ 모델에서 의미 있는 품질
  - UVM 패턴 이해 + 적용 → ~70B+ 권장
  - 작은 모델은 RAG/Few-shot으로 보완 필수
```

---

## LLM의 학습 단계

```
Phase 1: Pre-training (사전 학습)
  - 대규모 텍스트 코퍼스 (수 TB)
  - Next Token Prediction (자기지도 학습)
  - 수천 GPU × 수 주~수 개월
  - 결과: 언어의 일반적 패턴 학습
  - 비용: 수백만~수천만 달러

Phase 2: SFT (Supervised Fine-Tuning)
  - 사람이 작성한 고품질 (질문, 답변) 쌍
  - 수만~수십만 예시
  - 결과: 지시 따르기(Instruction Following) 능력

Phase 3: RLHF / DPO (Human Alignment)
  - 사람이 선호하는 출력을 학습
  - 안전성, 유용성, 정확성 강화
  - 결과: 실용적인 AI 어시스턴트
```

---

## 추론 (Inference) 과정

### Autoregressive Generation

```
입력: "Write a UVM"

Step 1: "Write a UVM" → P(next) → " test"
Step 2: "Write a UVM test" → P(next) → "bench"
Step 3: "Write a UVM testbench" → P(next) → " for"
...

한 번에 하나의 토큰만 생성 → 순차적 (병렬화 불가)
→ 이것이 LLM 추론이 느린 근본 이유
```

### 디코딩 전략

| 전략 | 동작 | 특징 |
|------|------|------|
| Greedy | 매 step 최고 확률 토큰 선택 | 빠르지만 단조로운 출력 |
| Top-k | 확률 상위 k개 중 샘플링 | 다양성 + 품질 균형 |
| Top-p (Nucleus) | 누적 확률 p 이내에서 샘플링 | 동적 후보 크기 |
| Temperature | 확률 분포를 sharp/flat 조절 | T<1: 보수적, T>1: 창의적 |

```
Temperature 효과:

  T = 0.0: 항상 같은 출력 (Greedy와 동일) → 코드 생성, 정확성 필요 시
  T = 0.3: 약간의 변동 → 일반적 코드/분석
  T = 0.7: 적당한 다양성 → 문서 생성
  T = 1.0: 원래 분포 → 창의적 작문

  DV 적용 시: T = 0.0~0.3 권장 (코드 정확성 중요)
```

---

## 핵심 파라미터 정리

| 파라미터 | 의미 | 대표값 |
|---------|------|--------|
| d_model | 토큰 임베딩 차원 | 4096~12288 |
| n_layers | Transformer Block 수 | 32~128 |
| n_heads | Attention Head 수 | 32~128 |
| d_ff | FFN 히든 차원 | 4 × d_model |
| vocab_size | 어휘 크기 | 32K~128K |
| context_length | 최대 입력 토큰 수 | 4K~1M+ |
| params | 총 파라미터 수 | 7B~405B+ |

---

## Q&A

**Q: Transformer의 Self-Attention이 왜 강력한가?**
> "두 가지 이유: (1) 장거리 의존성 — RNN과 달리 모든 토큰이 직접 참조하므로 문장 시작의 정보가 끝까지 손실 없이 전달된다. (2) 병렬화 — 모든 토큰 쌍의 Attention을 동시에 계산할 수 있어 GPU 병렬화에 최적. 이 두 특성이 대규모 모델 학습을 가능하게 했다."

**Q: LLM이 '이해'하는 것인가, 패턴 매칭인가?**
> "학술적으로 논쟁 중이지만, 실용적 관점에서 중요한 것은 '올바른 출력을 생성하는가'이다. DV 적용에서는 LLM이 SystemVerilog 구문과 UVM 패턴을 '이해'하는지보다, 생성된 코드가 컴파일되고 의도한 동작을 하는지가 핵심이다. 따라서 출력 검증 파이프라인(린트, 컴파일, 시뮬레이션)을 반드시 후단에 배치한다."

**Q: Context Window의 한계는 무엇이고 어떻게 극복하는가?**
> "Context Window는 한 번에 처리할 수 있는 토큰 수의 상한이다. 대규모 IP 스펙이나 코드베이스는 이 한계를 초과한다. 극복 방법: (1) RAG — 필요한 부분만 검색하여 Context에 주입. (2) Chunking — 문서를 의미 단위로 분할. (3) Summarization — 요약 후 Context에 포함. DVCon 논문에서 RAG + FAISS로 대규모 IP DB를 처리한 것이 바로 이 한계를 극복한 사례다."

**Q: KV Cache란 무엇이고 왜 중요한가?**
> "Autoregressive 생성에서 이전 토큰의 Key, Value를 캐싱하여 재계산을 방지하는 기법이다. KV Cache 없이는 토큰 생성마다 O(n²) 연산이 필요하지만, 캐싱으로 O(n)으로 줄인다. 다만 시퀀스 길이에 비례하여 메모리를 소비하므로, 긴 Context에서는 GQA(Grouped-Query Attention)로 KV Head 수를 줄여 메모리를 절감한다."

**Q: MoE 아키텍처의 장단점은?**
> "Mixture of Experts는 토큰마다 전체 Expert 중 일부(Top-K)만 활성화하는 Sparse 아키텍처다. 장점은 총 파라미터 대비 적은 연산량으로 높은 성능을 달성하는 것이다. 예를 들어 Mixtral 8x7B는 47B 파라미터지만 토큰당 13B만 활성화된다. 단점은 전체 파라미터를 GPU 메모리에 올려야 하므로 로딩 메모리는 크다는 것과 Expert 간 load balancing 문제가 있다."

**Q: 로컬 LLM 배포 시 Quantization을 어떻게 활용하는가?**
> "반도체 IP 보안상 클라우드 API를 쓸 수 없을 때, INT4/INT8 양자화로 모델 크기를 1/4~1/8로 줄여 사내 GPU에서 실행한다. 예: Llama 3 70B를 INT4로 양자화하면 ~35GB로 A100 1장에서 실행 가능하며, 코드 생성 품질은 FP16 대비 95% 이상 유지된다. AWQ나 GPTQ 같은 고급 양자화 기법으로 정밀도 손실을 최소화한다."

---

## 핵심 정리 (Key Takeaways)

- **Transformer = Self-Attention + Position Encoding + FFN** — 토큰 간 관계를 한 번의 행렬곱으로 계산.
- **자기회귀 생성** — "다음 토큰 확률 분포 → 샘플링" 의 반복.
- **Context window 는 비싸다** — 길이의 제곱으로 메모리/연산 증가, KV cache 가 큰 요인.
- **MoE / Quantization** — 활성 파라미터 ↓, 메모리 ↓ 를 통해 큰 모델을 실용적으로 만든다.
- **모델 = 정책 결정의 출발점이 아니라 도구** — 프롬프트/검색/도구 호출 설계가 실제 품질을 만든다.

## 다음 단계 (Next Steps)

- 다음 모듈: [Prompt Engineering →](../02_prompt_engineering/) — 같은 모델로도 결과를 바꾸는 입력 설계 기법.
- 퀴즈: [Module 01 Quiz](../quiz/01_llm_fundamentals_quiz/) — Transformer, MoE, Quantization 5문항.
- 실습: 동일 프롬프트를 3개 모델 크기(7B / 70B / API frontier) 로 돌려 latency · 품질 · 비용 표를 만들어 본다.

<div class="chapter-nav">
  <a class="nav-prev" href="../">
    <div class="nav-label">◀ 이전</div>
    <div class="nav-title">코스 홈</div>
  </a>
  <a class="nav-next" href="../02_prompt_engineering/">
    <div class="nav-label">다음 ▶</div>
    <div class="nav-title">Prompt Engineering & In-Context Learning</div>
  </a>
</div>
