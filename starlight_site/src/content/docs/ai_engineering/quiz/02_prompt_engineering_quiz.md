---
title: "Quiz — Module 02: Prompt Engineering"
---

[← Module 02 본문으로 돌아가기](../../02_prompt_engineering/)

---

## Q1. (Remember)

Zero-shot, Few-shot, CoT, Self-Consistency 의 한 줄 정의를 각각 적어라.

<details>
<summary>정답 / 해설</summary>

네 기법은 모두 "모델 가중치를 건드리지 않고 prompt만으로 동작을 바꾼다"는 점은 같지만 방향이 다르다.

**Zero-shot**은 예시 없이 task 설명만으로 LLM의 사전지식에 의존한다. **Few-shot**은 입력-출력 예시를 N개 포함시켜 모델이 따라야 할 패턴을 명시적으로 보여준다. **CoT**는 최종 답 대신 "생각 과정"을 먼저 출력하도록 유도해, 특히 다단계 수학/논리 문제에서 정확도를 크게 올린다. **Self-Consistency**는 같은 prompt를 여러 번 실행해 다수결로 답을 정함으로써 단일 샘플의 운에 의한 오류를 줄인다. 네 기법은 단독이 아닌 조합으로도 쓰이며, 예컨대 Few-shot + CoT가 가장 흔한 조합이다.

</details>
## Q2. (Understand)

Few-shot 이 모델 가중치를 변경하지 않는데도 동작이 바뀌는 이유는?

<details>
<summary>정답 / 해설</summary>

핵심은 Transformer의 Self-Attention이 **입력 전체를 동시에 참조**한다는 구조적 특성이다. 가중치를 바꾸지 않아도 prompt에 예시가 들어 있으면, 모델은 "이 입력 형식 → 이 출력 형식" 이라는 패턴을 attention을 통해 즉석에서 인식하고 따라한다. 이것이 in-context pattern matching이다.

"가중치가 안 바뀌면 동작도 안 바뀌어야 한다"고 생각하기 쉽지만, 이는 모델의 동작이 입력뿐 아니라 **컨텍스트 분포** 에 의해 결정된다는 점을 간과한 것이다. Few-shot은 추론 시점에 컨텍스트를 통해 분포를 제어하는 기법이므로, 재학습 없이도 효과가 발생한다.

</details>
## Q3. (Apply)

JSON 스키마에 맞는 출력만 받고 싶을 때 사용할 prompt 패턴을 작성하라.

<details>
<summary>정답 / 해설</summary>

JSON을 안정적으로 받으려면 **명시적 지시 + 스키마 제공 + 예시**를 계층으로 쌓아야 한다.

먼저 시스템 prompt에 "Output MUST be valid JSON matching the schema below. Do not add commentary." 같이 형식을 강제한다. 지시만으로는 LLM이 설명 문장을 앞에 붙이거나 Markdown 코드펜스를 씌우는 실수를 하는 경우가 있으므로, 바로 아래에 JSON Schema를 필드·타입·required 포함해 명시한다. 여기에 Few-shot 예시 1~2개를 추가하면 모델이 형식을 "보고 따라" 하므로 준수율이 크게 오른다. 마지막으로 사용 중인 API가 `response_format={"type":"json_object"}` 같은 구조화 출력 옵션을 제공한다면 반드시 함께 사용한다. 이 옵션 없이 프롬프트만 쓰는 것은 모델 의지에 의존하는 것이므로, 옵션이 있다면 사용하지 않을 이유가 없다.

</details>
## Q4. (Analyze)

CoT prompt 가 항상 정확도를 올리는 것은 아니다. 어떤 task 에서 효과가 미미한가?

<details>
<summary>정답 / 해설</summary>

CoT는 만능이 아니며, 효과가 미미하거나 오히려 역효과가 나는 상황이 세 가지 있다.

첫째, **단순 분류·추출 task**에서는 정답 도출에 "추론 단계"가 필요하지 않다. CoT가 강제로 생성하는 중간 단계가 없는 이유를 채우려고 모델이 임의적인 이야기를 만들어 noise가 된다. 둘째, **7B 이하의 소형 모델**은 논리적으로 일관된 CoT 자체를 생성하는 능력이 부족하다. 잘못된 중간 추론이 잘못된 최종 답으로 이어지므로, CoT가 없을 때보다 정확도가 낮아질 수 있다. 셋째, 출력 토큰이 비용과 직결되는 서비스에서는 CoT의 긴 출력이 정확도 향상분보다 비용 증가분이 더 클 수 있다. 결론적으로 CoT는 **multi-step reasoning이 필요하고 모델이 충분히 클 때** 비로소 투자 대비 효과가 난다.

</details>
## Q5. (Evaluate)

"같은 task 에 prompt 만 다른 4가지 버전" 을 비교 평가할 때 권장되는 metric 3가지는?

<details>
<summary>정답 / 해설</summary>

세 가지 metric은 서로 다른 관점을 커버하기 때문에 하나라도 빠지면 판단이 왜곡된다.

**정확도(task-specific)** 는 F1, Exact Match, Pass@1 등 task 목적에 맞는 지표로 "얼마나 잘 맞히는가"를 측정한다. 이것만 보면 가장 비싼 prompt가 이기게 되므로 **토큰 비용**을 함께 봐야 한다. 입력·출력 토큰 합을 USD로 환산하면 "정확도 1% 향상에 비용이 10배"라는 비현실적인 교환을 사전에 걸러낼 수 있다. 마지막으로 **Robustness**는 같은 입력을 여러 번 돌리거나 paraphrase 버전으로 입력했을 때 출력이 얼마나 안정적인지를 본다. 개발 환경에서는 잘 동작해도 운영에서 입력이 조금만 달라지면 무너지는 prompt를 걸러내는 데 필수적이다.

</details>
