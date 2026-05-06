# Quiz — Module 01: LLM Fundamentals

[← Module 01 본문으로 돌아가기](../01_llm_fundamentals.md)

---

## Q1. (Remember)

Transformer 의 핵심 3 컴포넌트는?

??? answer "정답 / 해설"
    1. **Self-Attention** — 토큰 간 관계 가중치 계산.
    2. **Position Encoding** — 시퀀스 순서 정보 주입.
    3. **Feed-Forward Network (FFN)** — 토큰별 비선형 변환.

## Q2. (Understand)

LLM 이 "다음 토큰 확률 예측" 을 반복하는 자기회귀(autoregressive) 방식인데도 어떻게 글 전체에 일관성이 유지되는가?

??? answer "정답 / 해설"
    이전 토큰들이 매번 입력에 포함되어 attention 으로 참조된다. 즉, "이전 컨텍스트 전체에 대한 확률 분포" 를 매 step 새로 계산하므로 일관성이 유지된다. context window 가 끝나면 일관성이 깨진다 — 그래서 long-context, summarization, RAG 같은 보완 기법이 필요.

## Q3. (Apply)

사내 IP 보안 때문에 클라우드 LLM 을 못 쓰고 단일 A100 으로 70B 모델을 돌려야 한다. 적합한 조합은?

??? answer "정답 / 해설"
    - **Quantization (INT4, AWQ/GPTQ)** — 70B FP16 약 140GB → INT4 약 35GB → A100 80GB 한 장에 들어간다.
    - **vLLM / TensorRT-LLM** 같은 추론 엔진으로 KV cache, paged attention 활용.
    - 품질이 부족하면 LoRA fine-tune 으로 소형 어댑터만 추가.

## Q4. (Analyze)

Context window 가 두 배가 될 때 메모리/연산이 단순히 두 배가 아닌 이유는?

??? answer "정답 / 해설"
    Self-Attention 의 연산은 시퀀스 길이 N 에 대해 **O(N²)**. 메모리도 KV cache 가 N 에 비례해 늘어 attention 행렬은 N² 셀이 된다. 그래서 길이 2배 → 메모리 ~2배 + 연산 ~4배. Flash-Attention / GQA / Sliding Window 같은 기법으로 완화한다.

## Q5. (Evaluate)

같은 task 에 대해 (a) 70B base 모델 직접 호출 vs (b) 7B + RAG 의 trade-off 를 평가하라.

??? answer "정답 / 해설"
    - **(a) 70B 직접**: 추론 능력 ↑, 도메인 지식 부족 시 hallucination, 비용 ↑.
    - **(b) 7B + RAG**: 도메인 지식은 RAG 가 채워줌, 추론 한계가 있어 복잡 reasoning 에서 실패 가능, 비용 ↓.

    실무 결정은 **task 의 reasoning 깊이** 와 **도메인 의존도** 의 곱. reasoning 이 얕고 도메인 의존도 ↑ → (b). reasoning 이 깊고 일반적 → (a). 둘 다 깊으면 70B + RAG 조합.
