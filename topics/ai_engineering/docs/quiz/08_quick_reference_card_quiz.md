# Quiz — Module 08: Quick Reference Card

[← Module 08 본문으로 돌아가기](../08_quick_reference_card.md)

---

## Q1. (Remember)

AI Engineering 의 4축은?

??? answer "정답 / 해설"
    1. **Prompt** — 입력 설계.
    2. **RAG** — 외부 지식 결합.
    3. **Agent** — 도구 + 메모리 + 다단계 loop.
    4. **Eval** — 정량/정성 평가 + 운영 모니터링.

## Q2. (Apply)

면접 30초 응답: "RAG 가 fine-tune 보다 좋은 이유?"

??? answer "정답 / 해설"
    - 갱신 비용 ↓ (인덱스만 다시 만들면 됨).
    - 출처 인용 가능 → 규제/IP 도메인에서 유리.
    - 소량 데이터로 즉시 효과.
    - Fine-tune 은 형식·스타일 내재화에 더 유리하지만, 지식 갱신은 부적합. 둘은 대체가 아니라 보완.

## Q3. (Apply)

자기 시스템에 빠진 보안/품질 계층을 빠르게 식별하는 체크리스트는?

??? answer "정답 / 해설"
    - [ ] Prompt template + version 관리?
    - [ ] RAG retrieval 평가셋(MRR/Recall) 측정 중?
    - [ ] Agent loop 에 max-step / max-token / cost guard?
    - [ ] Hallucination/Faithfulness 정기 측정?
    - [ ] IP / PII 마스킹 파이프라인?
    - [ ] Observability (요청/비용/실패 dashboard)?

## Q4. (Evaluate)

RAG 시스템의 품질이 안 좋다는 보고가 들어왔다. 어디부터 보아야 하는가?

??? answer "정답 / 해설"
    1. **Retrieval 품질 지표** (Recall@k, MRR) — 거의 모든 RAG 문제는 retrieval 에서 시작한다.
    2. **Chunking 정책** — chunk 가 너무 길거나 짧지 않은가?
    3. **Embedding 모델** — 도메인 적합성 (코드 vs 일반 텍스트).
    4. **Hybrid 검색** — 약어/식별자/짧은 query 가 dense 만으로 안 잡히는가?
    5. **Re-ranker 적용 여부**.
    6. 마지막으로 **Prompt** 와 **모델** 변경.

## Q5. (Evaluate)

이 코스 다음에 학습해야 할 4영역은?

??? answer "정답 / 해설"
    1. **LangChain / LangGraph** — RAG + Agent 표준 프레임워크.
    2. **LoRA / PEFT fine-tune** — 도메인 모델 적응.
    3. **RAGAS / TruLens** — 자동 평가 파이프라인.
    4. **Multi-Agent System** — 복잡한 워크플로 (planner / executor / critic) 분업.
