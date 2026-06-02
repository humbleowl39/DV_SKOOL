---
title: "Quiz — Module 05: Agent Architecture"
---

[← Module 05 본문으로 돌아가기](../../05_agent_architecture/)

---

## Q1. (Remember)

Agent 의 4 구성요소는?

<details>
<summary>정답 / 해설</summary>

Agent의 4 구성요소는 **LLM brain, Tool, Memory, Planner/Controller** 이며, 각 요소가 없으면 어떤 문제가 생기는지를 알면 역할이 명확히 이해된다.

**LLM brain**이 없으면 의사결정 주체가 없어 단순 스크립트와 다를 바 없다. **Tool**이 없으면 LLM은 텍스트만 출력하고 실제 외부 세계에 아무런 영향을 미치지 못한다. 검색, 코드 실행, API 호출은 모두 tool을 통해 이루어진다. **Memory**가 없으면 multi-turn 대화에서 이전 단계를 잊고 반복하거나, 장기 작업에서 앞서 수집한 정보를 잃어버린다. 단기 메모리는 대화 히스토리, 장기 메모리는 외부 DB에 저장된다. **Planner/Controller**가 없으면 LLM이 loop를 스스로 종료하지 못해 무한 반복하거나, step 간 의존성을 관리하지 못한다. 4 요소가 함께 있을 때 비로소 자율적 다단계 task 수행이 가능하다.

</details>
## Q2. (Understand)

ReAct 와 Plan-and-Execute 의 결정적 차이는?

<details>
<summary>정답 / 해설</summary>

두 패턴의 결정적 차이는 **언제 계획을 세우는가** 에 있다.

**ReAct**는 매 step마다 "현재 상황을 reasoning하고 즉시 다음 action을 결정"하는 방식이다. 중간에 예상치 못한 결과가 나와도 다음 step에서 바로 경로를 수정할 수 있어 적응성이 높다. 반면 각 step이 독립적으로 결정되다 보니 5~10단계가 넘어가면 전체 목표에서 벗어나는 drift가 발생할 수 있다. **Plan-and-Execute**는 처음에 전체 plan을 만들고 그 plan을 순서대로 실행한다. 처음부터 목표와 단계가 명확히 정의되므로 장기 작업에서 일관성이 훨씬 강하다. 그러나 plan이 수립된 뒤 환경이 바뀌면 이를 즉각 반영하기 어렵다. 실무에서는 planner가 큰 plan을 만들고 각 step은 ReAct로 실행하는 hybrid 방식이 두 단점을 상호 보완한다.

</details>
## Q3. (Apply)

"Repo 에서 버그를 찾아 수정 → 테스트 → PR 생성" 을 하는 agent 의 tool list 와 prompt 골격을 작성하라.

<details>
<summary>정답 / 해설</summary>

이 agent는 "버그 파악 → 코드 수정 → 테스트 검증 → PR 생성"이라는 순차적 루프를 수행해야 하므로, tool과 prompt 구조 모두 그 흐름을 지원해야 한다.

**Tools**로는 `search_repo`(버그 위치 탐색), `read_file`(코드 확인), `edit_file`(수정), `run_tests`(검증), `git_diff`(변경 확인), `create_pr`(결과 제출)이 최소 필요 목록이다. 각 tool이 하나의 atomic 동작에 대응해야 agent가 실패 지점을 명확히 알 수 있다. **Prompt 골격**은 시스템 prompt에 역할과 tool 사용 정책을 명시하고, task prompt에 버그 리포트를 전달하며, 루프는 ReAct 형식(Thought / Action / Observation)으로 진행한다. **종료 조건**은 반드시 명시해야 한다. "테스트 통과"가 성공 조건이지만 max-step도 반드시 함께 설정해야 한다. 테스트가 영원히 통과되지 않는 상황에서 종료 조건이 없으면 비용 폭주가 발생한다. 위험한 명령(예: `delete_repo`, `force_push`)은 화이트리스트에서 제외하는 guardrail도 필수다.

</details>
## Q4. (Analyze)

Agent 가 무한 루프 / 비용 폭주 / 도구 오용에 빠지는 주된 원인은?

<details>
<summary>정답 / 해설</summary>

세 가지 실패 패턴은 모두 표면적 원인이 다르지만 **planner/controller의 guardrail 부족** 이라는 공통 근본 원인을 가진다.

**무한 루프**는 agent가 task를 완료하는 조건이 모호하거나, 실패 시 재시도에 횟수 제한이 없을 때 발생한다. LLM은 스스로 멈춰야 한다는 판단을 항상 잘 하지 못하므로 controller가 max-step을 강제해야 한다. **비용 폭주**는 ReAct loop에서 context가 매 step 누적되어 토큰 수가 선형으로 늘고, 각 step에서 외부 API를 호출하면 비용이 step × API cost로 기하급수적으로 불어날 수 있다. max-tokens와 비용 예산을 hard limit으로 설정해야 한다. **도구 오용**은 tool의 input schema가 모호하거나, system prompt에 "어떤 상황에서 어떤 tool을 써야 하는지"가 명시되지 않을 때 LLM이 잘못된 tool을 선택하거나 잘못된 인자를 전달하는 방식으로 나타난다. allow-list와 dry-run(실제 실행 전 의도 확인)이 기본 방어 수단이다.

</details>
## Q5. (Evaluate)

MCP (Model Context Protocol) 가 실무 도입 시 주는 장단점은?

<details>
<summary>정답 / 해설</summary>

MCP의 가치는 "tool을 한 번 구현하면 여러 곳에서 재사용"이라는 명확한 약속에 있지만, 그 약속을 실현하는 데는 비용이 따른다.

**장점** 측면에서, tool을 MCP server로 노출하면 Claude Code, VS Code Copilot, 커스텀 agent 등 MCP를 지원하는 모든 클라이언트에서 재사용할 수 있다. Schema 표준화로 LLM이 잘못된 인자를 전달하는 prompt-tool mismatch도 줄어들고, 권한 관리와 감사 로그를 프로토콜 수준에서 통합할 수 있다. **단점** 측면에서, MCP 스펙은 2024년 기준 아직 진화 중이므로 향후 breaking change 위험이 있다. tool 구현 팀이 MCP server, schema 정의, 인증까지 추가로 구현해야 하는 부담도 있다. 가장 실질적인 단점은 디버깅 경로가 LLM → MCP server → tool 도메인으로 늘어나 문제 발생 시 어느 계층의 잘못인지 추적이 복잡해진다는 점이다. 따라서 도구가 5개 미만이면 native function calling이 더 가볍고, 10개 이상이거나 다중 IDE·다중 팀이 같은 tool을 공유해야 한다면 MCP가 ROI를 낸다.

</details>
