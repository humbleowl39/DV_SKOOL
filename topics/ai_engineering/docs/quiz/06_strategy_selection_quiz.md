# Quiz — Module 06: Strategy Selection

[← Module 06 본문으로 돌아가기](../06_strategy_selection.md)

---

## Q1. (Remember)

Prompt / RAG / Fine-tune 가 각각 무엇을 변경하는가?

??? answer "정답 / 해설"
    - **Prompt** : 입력만 변경, 모델/지식 그대로.
    - **RAG** : 외부 지식을 동적으로 추가, 모델/입력 형식 그대로.
    - **Fine-tune** : 모델 가중치 자체를 변경 (형식/스타일/분포 내재화).

## Q2. (Understand)

같은 task 에 fine-tune 보다 RAG 가 유리한 두 시나리오는?

??? answer "정답 / 해설"
    1. **자주 갱신되는 지식** (예: 매주 바뀌는 정책 / spec). RAG 는 인덱스만 갱신.
    2. **출처 인용 의무** (법률, 규제, 안전 critical). RAG 는 검색 문서 출처를 같이 답변.

## Q3. (Apply)

"사내 SystemVerilog spec 200 페이지 → 질문에 답하는 챗봇" 에 가장 적합한 조합은?

??? answer "정답 / 해설"
    1. **Prompt 만** : 200페이지를 매번 prompt 에 넣을 수 없음 → 단독으론 부적합.
    2. **RAG** : spec 을 chunk → embed → FAISS → top-k 검색 → prompt 주입. 가장 합리적.
    3. **Fine-tune** : 200페이지는 fine-tune 데이터로 너무 작고, 갱신 시 재학습 부담.

    → **RAG + Prompt** (system prompt 로 형식 통제, RAG 로 지식). FT 는 스타일 통일이 추가로 필요할 때만.

## Q4. (Analyze)

같은 task 의 4 조합 (Prompt / RAG / FT / FT+RAG) 비용 trade-off 를 분석하라.

??? answer "정답 / 해설"
    | 조합 | 초기 비용 | 운영 비용 | 갱신 비용 | 정확도 잠재력 |
    |------|----------|----------|----------|--------------|
    | Prompt | 매우 낮음 | 낮음 (토큰만) | 0 | 보통 |
    | RAG | 중간 (인덱스 구축) | 중간 (검색+토큰) | 낮음 (re-index) | 높음 |
    | FT | 높음 (학습+평가) | 낮음 (소형 모델 가능) | 매우 높음 (재학습) | 높음 (도메인 형식) |
    | FT+RAG | 매우 높음 | 중간 | 중간 | 가장 높음 |

    → 실무 표준은 **Prompt → RAG → 필요 시 FT** 순서.

## Q5. (Evaluate)

ROI 를 계산할 때 잊기 쉬운 비용 항목 3가지는?

??? answer "정답 / 해설"
    1. **평가 셋 유지 비용** — gold set 라벨링 / 갱신 / drift 모니터링.
    2. **운영 신뢰성 비용** — 실패 fallback, observability, retry 로직.
    3. **인적 검증 비용** — LLM-as-judge 만으로 부족한 critical 도메인은 인간 reviewer 가 상시 필요.

    이 셋을 빼면 PoC 까지는 ROI 가 좋아 보이지만 실제 운영 단계에서 적자가 된다.
