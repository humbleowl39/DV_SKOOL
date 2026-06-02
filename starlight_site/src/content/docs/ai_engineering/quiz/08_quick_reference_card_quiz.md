---
title: "Quiz — Module 08: Quick Reference Card"
---

[← Module 08 본문으로 돌아가기](../../08_quick_reference_card/)

---

## Q1. (Remember)

AI Engineering 의 4축은?

<details>
<summary>정답 / 해설</summary>

AI Engineering의 4축은 **Prompt, RAG, Agent, Eval** 이며, 4가지 모두 있어야 실제 운영 가능한 시스템이 된다.

**Prompt**는 LLM과 소통하는 가장 기본적인 레이어로, 입력 구조·형식·지시문을 설계한다. **RAG**는 모델이 모르는 도메인 지식을 외부에서 동적으로 주입해 답변의 사실성을 높인다. **Agent**는 단일 LLM 호출을 넘어서, tool 호출·메모리·다단계 loop를 통해 복잡한 작업을 자율적으로 수행하게 한다. **Eval**은 이 세 축이 실제로 잘 동작하는지 정량·정성 지표로 측정하고 운영 중 이상 징후를 모니터링한다. Eval 없이는 "잘 되고 있는지"를 알 수 없고, 개선 방향도 잡을 수 없다. 이 4축은 독립적이 아니라 서로를 지지하는 구조다.

</details>
## Q2. (Apply)

면접 30초 응답: "RAG 가 fine-tune 보다 좋은 이유?"

<details>
<summary>정답 / 해설</summary>

30초 안에 핵심을 전달하려면 RAG의 구조적 장점 세 가지를 인과적으로 연결해야 한다.

RAG는 지식을 모델 가중치가 아닌 **외부 인덱스**에 저장하므로, 지식이 바뀌면 인덱스만 교체하면 되고 재학습이 필요 없다. 또한 검색된 문서를 출처와 함께 답변에 첨부할 수 있어, 규제·IP 도메인처럼 "이 답이 어디서 나왔는가"가 중요한 곳에서 fine-tune이 줄 수 없는 신뢰성을 제공한다. 수십 개의 문서만으로도 즉시 동작하므로 fine-tune에 필요한 수천~수만 레이블 예시를 준비할 수 없을 때 유일한 현실적 선택이다. 마지막으로 "둘 중 하나"가 아니라 fine-tune이 형식·스타일 내재화에 필요한 경우 RAG와 함께 쓰는 것이 가장 강한 조합임을 덧붙이면 된다.

</details>
## Q3. (Apply)

자기 시스템에 빠진 보안/품질 계층을 빠르게 식별하는 체크리스트는?

<details>
<summary>정답 / 해설</summary>

이 체크리스트는 AI Engineering의 4축(Prompt, RAG, Agent, Eval)에 하나씩 대응하는 안전·품질 계층을 점검한다.

- [ ] Prompt template + version 관리? (Prompt 축 — 변경 이력이 없으면 어느 버전이 좋았는지 알 수 없다)
- [ ] RAG retrieval 평가셋(MRR/Recall) 측정 중? (RAG 축 — 측정 없이는 retrieval이 개선됐는지 알 수 없다)
- [ ] Agent loop에 max-step / max-token / cost guard? (Agent 축 — 이 셋이 없으면 비용 폭주와 무한루프 위험)
- [ ] Hallucination/Faithfulness 정기 측정? (Eval 축 — 시간이 지나면서 drift가 발생하므로 정기 측정이 필요)
- [ ] IP / PII 마스킹 파이프라인? (보안 레이어 — DV 도메인에서 특히 중요)
- [ ] Observability(요청/비용/실패 dashboard)? (운영 레이어 — 문제가 생겼을 때 어디서 생겼는지 즉시 알아야 한다)

체크되지 않은 항목 하나하나가 운영 단계에서 실제 사고로 이어질 수 있는 열린 구멍이다.

</details>
## Q4. (Evaluate)

RAG 시스템의 품질이 안 좋다는 보고가 들어왔다. 어디부터 보아야 하는가?

<details>
<summary>정답 / 해설</summary>

RAG 품질 문제의 원인 탐색은 **가장 빠른 진단 → 비용이 큰 변경** 순서로 진행해야 한다. 많은 팀이 LLM이나 프롬프트를 먼저 바꾸는 실수를 하는데, 대부분의 RAG 문제는 retrieval 단계에서 시작한다.

첫 번째로 **Retrieval 품질 지표**(Recall@k, MRR)를 확인한다. top-k 안에 정답 문서가 있는지조차 확인하지 않으면 모든 후속 작업이 방향을 잡지 못한다. 두 번째로 **Chunking 정책**이다. chunk가 너무 길면 임베딩이 평균화되어 특정 내용을 잃고, 너무 짧으면 컨텍스트가 부족해 LLM이 활용하기 어렵다. 세 번째로 **Embedding 모델**의 도메인 적합성을 본다. 일반 텍스트로 학습된 모델은 코드 식별자나 회로 용어에서 약할 수 있다. 네 번째로 **Hybrid 검색** 적용 여부다. 약어나 짧은 식별자 query는 dense 검색이 아닌 sparse(BM25)에서 잘 잡힌다. 다섯 번째로 **Re-ranker** 적용 여부를 확인한다. 마지막으로 이 모든 단계를 점검한 후에도 문제가 남아 있으면 **Prompt와 LLM** 변경을 고려한다.

</details>
## Q5. (Evaluate)

이 코스 다음에 학습해야 할 4영역은?

<details>
<summary>정답 / 해설</summary>

이 코스는 AI Engineering의 개념과 의사결정 프레임워크를 다뤘다. 다음 학습 4영역은 각각 이 코스의 특정 한계를 채운다.

**LangChain / LangGraph**는 RAG 파이프라인과 Agent 루프를 코드로 구현하는 표준 프레임워크다. 이 코스에서 개념으로 배운 것을 실제 코드로 구현하는 가장 빠른 경로다. **LoRA / PEFT fine-tune**은 대형 모델을 처음부터 재학습하지 않고 소수의 어댑터 파라미터만 학습해 도메인에 적응시키는 기법이다. 코스에서 "fine-tune"을 전략 선택지로 다뤘다면, 여기서는 실제로 어떻게 저렴하게 하는지를 배운다. **RAGAS / TruLens**는 Faithfulness, Recall, Relevance 같은 지표를 자동으로 측정하는 평가 파이프라인을 구축할 수 있게 해준다. Eval 축을 수작업 gold set에서 자동화로 올리는 단계다. **Multi-Agent System**은 planner·executor·critic 같은 역할 분업으로 복잡한 워크플로를 더 안정적으로 처리하는 아키텍처로, 단일 agent의 한계를 넘는 실전 시스템 설계를 다룬다.

</details>
