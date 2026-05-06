# Quiz — Module 02: Prompt Engineering

[← Module 02 본문으로 돌아가기](../02_prompt_engineering.md)

---

## Q1. (Remember)

Zero-shot, Few-shot, CoT, Self-Consistency 의 한 줄 정의를 각각 적어라.

??? answer "정답 / 해설"
    - **Zero-shot**: 예시 없이 task 설명만 prompt 에 포함.
    - **Few-shot**: prompt 안에 입력-출력 예시를 N 개 포함.
    - **CoT**: 중간 추론 단계를 출력하도록 유도.
    - **Self-Consistency**: 같은 prompt 를 여러 번 샘플링 → 다수결.

## Q2. (Understand)

Few-shot 이 모델 가중치를 변경하지 않는데도 동작이 바뀌는 이유는?

??? answer "정답 / 해설"
    Transformer 의 self-attention 은 prompt 내 모든 토큰 패턴을 참조한다. 예시들이 prompt 에 들어 있으면 모델은 "최근 본 패턴을 따라서 다음 토큰을 만든다" — 즉, **in-context pattern matching**. 가중치 학습이 아니라 추론 시점에 컨텍스트 분포를 활용하는 것이다.

## Q3. (Apply)

JSON 스키마에 맞는 출력만 받고 싶을 때 사용할 prompt 패턴을 작성하라.

??? answer "정답 / 해설"
    1. **시스템 prompt 에 형식 강제** — "Output MUST be valid JSON matching the schema below. Do not add commentary."
    2. **JSON Schema 본문 포함** — 필드/타입/required 명시.
    3. **Few-shot 예시 1~2개** — 정확한 형식의 예시 출력.
    4. **추가 안전장치** — `response_format={"type":"json_object"}` 같은 API 옵션이 있다면 같이 사용.

## Q4. (Analyze)

CoT prompt 가 항상 정확도를 올리는 것은 아니다. 어떤 task 에서 효과가 미미한가?

??? answer "정답 / 해설"
    - **단순 분류 / 추출 task**: 추론이 거의 필요 없으므로 CoT 가 noise 만 추가.
    - **모델 크기가 작은 경우** (7B 이하): CoT 자체를 잘 못 만들어 결과 악화.
    - **출력 길이 비용이 critical** 한 경우: CoT 로 비용 증가가 정확도 향상보다 클 수 있다.

    → CoT 는 **multi-step reasoning + 충분히 큰 모델** 조합에서 가장 효과.

## Q5. (Evaluate)

"같은 task 에 prompt 만 다른 4가지 버전" 을 비교 평가할 때 권장되는 metric 3가지는?

??? answer "정답 / 해설"
    1. **정확도 (task-specific)** — F1 / Exact Match / Pass@1 등.
    2. **토큰 비용** — 입력 + 출력 토큰 합 (USD 환산).
    3. **Robustness** — 같은 입력에 대한 출력 분산(temperature 별로 N 회 측정) 또는 입력 paraphrase 에 대한 stability.

    셋 모두 측정해야 ROI 가 보인다.
