# Quiz — Module 05: Agent Architecture

[← Module 05 본문으로 돌아가기](../05_agent_architecture.md)

---

## Q1. (Remember)

Agent 의 4 구성요소는?

??? answer "정답 / 해설"
    1. **LLM brain** — 의사결정 / 계획 / 합성.
    2. **Tool** — 외부 동작 (검색, 실행, API).
    3. **Memory** — 단기(대화), 장기(외부 저장).
    4. **Planner / Controller** — 다단계 step 관리, loop 종료 조건.

## Q2. (Understand)

ReAct 와 Plan-and-Execute 의 결정적 차이는?

??? answer "정답 / 해설"
    - **ReAct** : 매 step 마다 reasoning + 다음 action 을 짧게 결정 → 빠른 적응성, 단계 간 일관성은 약함.
    - **Plan-and-Execute** : 처음에 전체 plan 을 만들고 step-by-step 실행 → 장시간 task 에 일관성 ↑, 도중 변화 대응이 약함.

    실무에서는 두 패턴을 hybrid 로 사용 (planner 가 큰 plan 만들고, 각 step 은 ReAct 로 미세 조정).

## Q3. (Apply)

"Repo 에서 버그를 찾아 수정 → 테스트 → PR 생성" 을 하는 agent 의 tool list 와 prompt 골격을 작성하라.

??? answer "정답 / 해설"
    - **Tools** : `search_repo`, `read_file`, `edit_file`, `run_tests`, `git_diff`, `create_pr`.
    - **Prompt 골격** :
      1. System: "You are a coding agent. Use the provided tools. After each action, reflect briefly."
      2. Task: "Bug report: <text>. Fix it."
      3. Loop: ReAct (Thought / Action / Observation) until tests pass.
      4. Termination: tests pass OR max-step exceeded.
    - **Guard** : 최대 step / 최대 비용 / 위험 명령 화이트리스트.

## Q4. (Analyze)

Agent 가 무한 루프 / 비용 폭주 / 도구 오용에 빠지는 주된 원인은?

??? answer "정답 / 해설"
    - **무한 루프** : 종료 조건이 모호하거나, 실패 시 재시도 한도가 없어서.
    - **비용 폭주** : context 가 매 step 누적, tool 호출이 비싼 외부 API 일 때.
    - **도구 오용** : tool schema 가 모호하거나, system prompt 에 tool 사용 정책이 없을 때.

    모두 **planner / controller 의 guardrail 부족** 이 근본 원인. max-step, max-tokens, allow-list, dry-run 을 기본 장치로 둔다.

## Q5. (Evaluate)

MCP (Model Context Protocol) 가 실무 도입 시 주는 장단점은?

??? answer "정답 / 해설"
    **장점**:
    - Tool 한 번 구현 → 여러 LLM/IDE 에서 재사용.
    - Schema 표준화로 prompt-tool mismatch 감소.
    - 권한/감사 모델을 표준 프로토콜에 통합 가능.

    **단점**:
    - 표준이 아직 진화 중 → spec 변경 위험.
    - Tool 구현 측 부담 (server, schema, auth).
    - 디버깅이 한 단계 멀어짐 (LLM ↔ MCP server ↔ tool 도메인).

    내부 도구가 5개 미만이면 native function calling 이 더 가볍고, 10개 이상 / 다중 IDE 라면 MCP 가 ROI ↑.
