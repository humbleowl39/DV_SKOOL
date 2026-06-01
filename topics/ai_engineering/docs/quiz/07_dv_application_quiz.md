# Quiz — Module 07: DV/EDA Application

[← Module 07 본문으로 돌아가기](../07_dv_application.md)

---

## Q1. (Remember)

DV 워크플로에서 AI 가 적용 가능한 5단계는?

??? answer "정답 / 해설"
    DV 워크플로에서 AI가 적용 가능한 5단계는 **Spec/V-Plan, TB 생성, Debug, Coverage 분석, Triage** 이며, 각 단계에서 AI가 줄이는 것은 결국 "반복적인 수작업 시간"이다.

    **Spec/V-Plan**에서는 자연어로 작성된 spec에서 "무엇을 검증해야 하는가"를 추출하는 작업을 AI가 보조한다. 사람이 spec을 읽고 V-Plan을 쓰는 데 드는 시간을 줄이지만, 최종 계획의 타당성은 DV 엔지니어가 검토해야 한다. **TB 생성**에서는 인터페이스 추출과 agent/driver/monitor 코드의 초안 생성을 AI가 담당하고, 엔지니어는 검토와 도메인별 커스터마이즈에 집중할 수 있다. **Debug**에서는 방대한 로그와 FSDB에서 첫 번째 오류와 근본 원인 후보를 빠르게 좁히는 데 AI가 유용하다. **Coverage 분석**은 커버리지 홀을 식별하고 어떤 시퀀스나 제약을 추가해야 할지 제안하는 데 쓰인다. **Triage**는 수백~수천 개의 회귀 실패를 패턴별로 자동 분류해 사람이 봐야 할 대표 케이스만 추려내는 데 가장 즉각적인 ROI를 낸다.

## Q2. (Understand)

"AI 가 DV 엔지니어를 대체" 가 아니라 "Augmentation" 인 이유를 설명하라.

??? answer "정답 / 해설"
    "AI가 대체한다"는 전제는 DV의 책임 구조를 오해한 데서 나온다.

    DV의 핵심 가치는 **틀린 것을 찾아 입증**하는 것이고, 이 입증 책임은 감사·테이프아웃 의사결정 과정에서 인간이 진다. AI는 root cause 후보를 빠르게 좁히고 코드 초안을 만들어 주는 도구이지만, "이것이 실제 RTL 버그다"라고 단정하거나 수정을 commit하는 결정은 반드시 인간이 검증해야 한다. 또한 사내 IP, RTL 코드, 검증 데이터가 외부 LLM 서비스로 전송될 수 없는 보안·regulatory 제약도 인간 in-the-loop가 사라질 수 없는 이유다. AI는 DV 엔지니어가 더 중요한 판단에 집중할 수 있도록 반복적 수작업을 대신하는 "Augmentation" 역할이 정확한 표현이다.

## Q3. (Apply)

자기 팀 회귀 결과 1000개 fail 을 자동 triage 하는 agent 의 구성요소는?

??? answer "정답 / 해설"
    1000개 fail의 자동 triage는 "모든 fail을 AI가 판단"하는 것이 아니라 "사람이 봐야 할 것만 걸러내는 것"이 목표다.

    **Tools**로는 `read_log`(로그 읽기), `extract_first_error`(첫 번째 오류 추출 — cascading error에 속지 않기 위해 첫 오류가 중요), `classify_pattern`(알려진 패턴과 매칭), `cluster_by_signature`(같은 오류 signature를 가진 fail 묶기), `link_to_jira`(기존 티켓 연결)가 필요하다. **Pipeline**은 로그에서 첫 error를 추출 → 룰 기반 pattern 매칭 먼저 (빠르고 비용 저렴) → 나머지를 LLM으로 분류 → 같은 cluster로 묶어 대표 sample만 사람에게 제시하는 구조다. **Guardrail**이 핵심인데, 분류 신뢰도가 낮은 fail은 강제로 분류하지 않고 "unknown" 버킷으로 분리해 사람에게 escalation해야 한다. 잘못된 분류보다 모름을 인정하는 것이 낫다. **Metrics**로는 triage 소요 시간, 잘못 묶인 비율, 새로운 패턴 발견 시간을 추적해 agent의 실효성을 측정한다.

## Q4. (Analyze)

AI 도입 시 발생하는 위험 3가지와 완화책은?

??? answer "정답 / 해설"
    DV 도메인 AI 도입의 세 가지 위험은 각각 다른 공격 벡터를 가지며, 완화책도 다르다.

    첫째, **IP 누출**이다. RTL 코드, spec, 검증 데이터는 기업의 핵심 자산이다. 이를 외부 클라우드 LLM API로 보내는 순간 NDA 위반이나 IP 유출 위험이 생긴다. 완화책은 로컬 모델 사용, on-prem LLM 배포, 또는 외부로 나가기 전 민감 정보를 마스킹하는 것이다. 둘째, **Hallucination on RTL**이다. LLM이 존재하지 않는 신호 이름이나 잘못된 타이밍을 자신 있게 제시하면, DV 엔지니어가 이를 신뢰해 잘못된 방향으로 디버그할 수 있다. RAG로 spec·RTL을 인용하도록 강제하고 인간 reviewer의 sanity check를 의무화해야 한다. 셋째, **비용 폭주**다. Agent가 대규모 로그 파일을 매 step마다 context에 누적하거나, 비싼 API를 반복 호출하면 예상 외의 비용이 발생한다. token/call 예산 hard limit, agent max-step, observability dashboard로 이상 징후를 실시간으로 감지해야 한다.

## Q5. (Evaluate)

도입 단계별 우선순위(현재/단기/장기) 를 ROI 기준으로 평가하라.

??? answer "정답 / 해설"
    도입 단계를 ROI와 위험 기준으로 정렬하면, **"값싸고 안전한 것부터 시작해서 측정하고 다음 단계로 올라가는"** 원칙이 일관되게 적용된다.

    **현재(즉시 도입)**는 Copilot류 코드 보조, 로그 요약, RAG 기반 spec Q&A다. 이 작업들은 사람이 최종 결과를 검토하는 human-in-the-loop 구조여서 AI 오류의 파급이 작고, 도입 즉시 체감 효과가 크다. **단기(3~6개월)**는 agent 기반 자율 디버그로, 로그에서 root cause를 찾고 fix proposal을 생성한 뒤 사람이 review하는 반자율 파이프라인이다. 시간 절감 효과는 크지만 guardrail(max-step, 비용 예산, IP 마스킹)을 갖추지 않으면 현재 단계보다 위험이 높다. **장기(12개월+)**는 spec에서 V-Plan, TB, coverage closure까지 이어지는 자율 파이프라인으로, 완성 시 가장 큰 가치를 내지만 각 단계의 오류가 다음 단계로 전파되므로 검증·감사 체계 없이는 도입하면 안 된다. 이 순서를 건너뛰고 장기 단계부터 시작하면 ROI 검증 없이 큰 위험을 감수하게 된다.
