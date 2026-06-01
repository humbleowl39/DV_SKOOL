# Quiz — Module 01: LLM Fundamentals

[← Module 01 본문으로 돌아가기](../01_llm_fundamentals.md)

---

## Q1. (Remember)

Transformer 의 핵심 3 컴포넌트는?

??? answer "정답 / 해설"
    정답은 **Self-Attention**, **Position Encoding**, **Feed-Forward Network (FFN)** 세 가지다.

    Self-Attention은 입력 시퀀스의 모든 토큰 쌍 사이의 관련도를 동시에 계산해 "어느 토큰이 어느 토큰에 집중할지" 를 학습한다. 이것이 Transformer의 핵심 능력이며, RNN처럼 순차 처리하지 않고 병렬로 글로벌 문맥을 파악한다. Position Encoding은 Self-Attention이 순서 정보를 자체적으로 갖지 못한다는 약점을 보완하기 위해 각 토큰의 위치 정보를 벡터에 더한다. 이 두 컴포넌트가 없으면 Transformer는 "단어 묶음(bag of words)"와 다를 바 없다. FFN은 각 토큰 위치에서 독립적으로 비선형 변환을 수행해 표현력을 높이며, 파라미터 수의 대부분을 차지한다.

## Q2. (Understand)

LLM 이 "다음 토큰 확률 예측" 을 반복하는 자기회귀(autoregressive) 방식인데도 어떻게 글 전체에 일관성이 유지되는가?

??? answer "정답 / 해설"
    일관성이 유지되는 이유는 자기회귀 LLM이 새로운 토큰을 생성할 때마다 **이전에 생성한 모든 토큰을 입력으로 다시 포함**하기 때문이다. Self-Attention은 이 축적된 컨텍스트 전체를 참조해 "지금까지의 흐름을 감안한 가장 적절한 다음 토큰"을 선택한다. 따라서 앞 문단에서 정한 주어나 논조가 뒤에도 반영된다.

    단, 이 일관성은 **context window 길이 안에서만** 유효하다. context window를 넘어서면 초반 내용이 잘려 모델이 참조할 수 없게 되고, 그 시점부터 일관성이 깨진다. 이것이 long-context 모델, summarization, RAG 같은 기법이 등장한 근본 이유다.

## Q3. (Apply)

사내 IP 보안 때문에 클라우드 LLM 을 못 쓰고 단일 A100 으로 70B 모델을 돌려야 한다. 적합한 조합은?

??? answer "정답 / 해설"
    핵심 조합은 **Quantization(INT4, AWQ/GPTQ) + 추론 최적화 엔진** 이다.

    70B 모델을 FP16으로 올리면 약 140GB가 필요해 A100 80GB 한 장에 들어가지 않는다. INT4 양자화를 적용하면 약 35GB로 줄어 단일 GPU에서 구동 가능하다. 여기에 vLLM이나 TensorRT-LLM 같은 추론 엔진을 더하면 KV cache 공유와 paged attention으로 throughput을 극대화할 수 있다. 클라우드 API를 사용하면 IP가 외부로 전송되므로 이 시나리오에서는 애초에 선택지가 아니다. 품질이 여전히 부족하다면 LoRA fine-tune으로 수백 MB 어댑터만 추가해 도메인 적응할 수 있으며, 전체 재학습보다 훨씬 저렴하다.

## Q4. (Analyze)

Context window 가 두 배가 될 때 메모리/연산이 단순히 두 배가 아닌 이유는?

??? answer "정답 / 해설"
    원인은 Self-Attention의 **O(N²) 복잡도** 에 있다. Attention은 모든 토큰 쌍 사이의 점수를 계산하므로, 시퀀스 길이 N이 2배가 되면 연산량은 4배가 된다. KV cache도 각 레이어마다 N개의 key·value 벡터를 저장하므로 메모리는 N에 비례해 늘어난다.

    직관적으로 생각하면 "단어 2배 = 비교 대상 2배 × 비교 회수 2배"이므로 조합 폭발이 발생한다. "연산이 그냥 2배" 라고 답했다면 FFN의 선형 확장과 혼동한 것이다. Flash-Attention, GQA(Grouped Query Attention), Sliding Window Attention은 이 O(N²) 벽을 우회하기 위한 기법들이다.

## Q5. (Evaluate)

같은 task 에 대해 (a) 70B base 모델 직접 호출 vs (b) 7B + RAG 의 trade-off 를 평가하라.

??? answer "정답 / 해설"
    두 선택지는 **추론 능력** 과 **도메인 지식 접근** 이라는 두 축에서 서로 반대 방향을 가진다.

    (a) 70B 직접 호출은 복잡한 multi-step reasoning이 강점이지만, 모델이 학습 시 본 적 없는 사내 도메인 지식을 필요로 할 때 hallucination이 발생하고 추론 비용이 높다. (b) 7B + RAG는 부족한 파라미터 수를 외부 지식 주입으로 보완하지만, 주입된 컨텍스트를 바탕으로 복잡한 논리 추론을 수행하는 능력은 본질적으로 제한된다.

    따라서 실무 기준은 간단하다. task의 reasoning 깊이가 얕고 도메인 의존도가 높으면 (b), reasoning이 깊고 도메인 독립적이면 (a), 둘 다 필요하면 70B + RAG를 조합한다.
