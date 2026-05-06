# Quiz — Module 07: DV/EDA Application

[← Module 07 본문으로 돌아가기](../07_dv_application.md)

---

## Q1. (Remember)

DV 워크플로에서 AI 가 적용 가능한 5단계는?

??? answer "정답 / 해설"
    1. **Spec / V-Plan** — 자연어 spec 에서 verification plan 추출.
    2. **TB 생성** — interface 추출, agent / driver / monitor 코드 생성.
    3. **Debug** — 로그 / FSDB 분석으로 root cause 후보 좁히기.
    4. **Coverage 분석** — coverage hole → 새 시퀀스 / 제약 제안.
    5. **Triage** — 회귀 결과 묶음에서 같은 패턴 자동 분류.

## Q2. (Understand)

"AI 가 DV 엔지니어를 대체" 가 아니라 "Augmentation" 인 이유를 설명하라.

??? answer "정답 / 해설"
    DV 의 가치는 **틀린 것을 찾아 입증** 하는 것이며, 이 입증 책임은 인간이 진다 (감사·테이프아웃 의사결정). AI 는 후보를 빠르게 만들고 좁히는 도구이지만, 실제 RTL bug 라 단정하거나 fix 를 합치는 결정은 인간이 검증해야 한다. 또한 도메인 IP / 보안 / regulatory 제약 때문에 인간 in-the-loop 가 사라질 수 없다.

## Q3. (Apply)

자기 팀 회귀 결과 1000개 fail 을 자동 triage 하는 agent 의 구성요소는?

??? answer "정답 / 해설"
    - **Tools** : `read_log`, `extract_first_error`, `classify_pattern`, `cluster_by_signature`, `link_to_jira`.
    - **Pipeline** : 로그에서 첫 error 추출 → pattern 매칭(룰) + LLM 분류 → 같은 cluster 묶기 → 대표 sample 만 사람에게 노출.
    - **Guardrail** : 분류 신뢰도가 낮은 fail 은 "unknown" 으로 두고 사람에게 escalation.
    - **Metrics** : triage 시간, 잘못 묶인 비율, 새로운 패턴 발견 시간.

## Q4. (Analyze)

AI 도입 시 발생하는 위험 3가지와 완화책은?

??? answer "정답 / 해설"
    1. **IP 누출** — 로컬 모델 / on-prem LLM / 데이터 마스킹.
    2. **Hallucination on RTL** — RAG 로 spec / RTL 인용 강제, 인간 reviewer 의 sanity check.
    3. **비용 폭주** — token / call budget guard, agent max-step, observability dashboard.

## Q5. (Evaluate)

도입 단계별 우선순위(현재/단기/장기) 를 ROI 기준으로 평가하라.

??? answer "정답 / 해설"
    - **현재 (즉시 도입)** : Copilot 류 코드 보조, 로그 요약, RAG 기반 spec Q&A → 빠른 ROI, 위험 낮음.
    - **단기 (3~6개월)** : Agent 기반 자율 디버그 (log → fix proposal → review) → 시간 절감 ↑↑, guardrail 필요.
    - **장기 (12개월+)** : spec → V-Plan → TB → coverage closure 자율 파이프라인 → 운영 위험 ↑, 검증/감사 체계 필수.

    원칙: **위험 ↓ + ROI ↑** 부터 시작 → 측정 → 다음 단계 escalation.
