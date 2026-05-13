# Module 05 — Agent Architecture

<!-- DV-SKOOL-CH-CTX:start -->
<div class="chapter-context" data-cat="applied">
  <a class="chapter-back" href="../">
    <span class="chapter-back-arrow">←</span>
    <span class="chapter-back-icon">🤖</span>
    <span class="chapter-back-text">AI Engineering</span>
  </a>
  <span class="chapter-divider">›</span>
  <span class="chapter-marker">Module 05</span>
</div>
<!-- DV-SKOOL-CH-CTX:end -->

<!-- DV-SKOOL-CH-TOC:start -->
<div class="page-toc">
  <span class="page-toc-label">목차</span>
  <a class="page-toc-link" href="#1-why-care-단일-llm-호출로-못-푸는-task-들">1. Why care?</a>
  <a class="page-toc-link" href="#2-intuition-직원-도구-키트-비유와-한-장-그림">2. Intuition</a>
  <a class="page-toc-link" href="#3-작은-예-uvm-에러를-디버그하는-react-loop-한-사이클">3. 작은 예 — ReAct loop 1 사이클</a>
  <a class="page-toc-link" href="#4-일반화-4-구성요소-와-주요-패턴">4. 일반화 — 4 구성요소 + 패턴</a>
  <a class="page-toc-link" href="#5-디테일-function-calling-reflexion-multi-agent-mcp-평가-프레임워크">5. 디테일</a>
  <a class="page-toc-link" href="#6-흔한-오해-와-dv-디버그-체크리스트">6. 흔한 오해 + 디버그</a>
  <a class="page-toc-link" href="#7-핵심-정리-key-takeaways">7. 핵심 정리</a>
</div>
<!-- DV-SKOOL-CH-TOC:end -->

!!! objective "학습 목표"
    이 모듈을 마치면:

    - **Define** Agent 의 4 구성요소 (LLM brain · Tool · Memory · Planner) 를 정의할 수 있다.
    - **Compare** ReAct, Plan-and-Execute, Reflexion 패턴을 비교 설명할 수 있다.
    - **Apply** 다단계 task 를 tool-call 과 memory 로 분해해 동작 가능한 agent loop 를 작성할 수 있다.
    - **Analyze** Agent 가 무한 루프 / 비용 폭주 / 도구 오용에 빠지는 원인을 분석할 수 있다.
    - **Evaluate** MCP 같은 표준이 실무 도입에 가져오는 장단점을 평가할 수 있다.

!!! info "사전 지식"
    - [Module 02](02_prompt_engineering.md) — system prompt, structured output
    - [Module 04](04_rag.md) — RAG 4 단계
    - 기본 함수 호출 / API 디자인 감각

---

## 1. Why care? — 단일 LLM 호출로 못 푸는 task 들

### 1.1 시나리오 — "RTL 디버그를 LLM 에 맡길 수 있을까?"

당신은 simulation fail. 다음 task 를 LLM 한 번 호출로 풀려고 합니다:

```
"이 log 파일을 분석해서 root cause 찾고 fix 제안해줘"
```

LLM 의 한계:
- **파일 못 읽음** — LLM 은 텍스트 입력만 받음. log 가 1 MB 면 prompt 에 직접 붙여야 함.
- **mrun 명령 실행 못 함** — Hypothesis 를 검증하려면 실제 실행 필요.
- **여러 시도 반복 못 함** — 한 응답 = 한 추론. 시도 1 실패 후 시도 2 자동 안 됨.

해법은 **Agent 패턴**:

```
사용자: "log 분석해서 fix"
   ↓
Agent loop:
  ① LLM 추론: "log 읽어야겠다" → read_file(log.txt)
  ② Tool 실행: log 내용 반환
  ③ LLM 추론: "이건 PSN error. RTL 의 PSN 비교 함수 의심" → grep("PSN", rtl/)
  ④ Tool 실행: 파일 위치 반환
  ⑤ LLM 추론: "modulo 비교 누락" → read_file(specific_file)
  ⑥ Tool 실행: 코드 반환
  ⑦ LLM: "fix 제안 + 검증"
```

**핵심**: LLM 이 _도구를 선택_ 하고 _결과를 보고 다음 행동 결정_. 이게 단일 호출과의 차이.

DV / 코딩 / 분석 자동화 등 거의 모든 실무 응용은 결국 agent 형태로 수렴하며, [Module 07](07_dv_application.md) 의 모든 적용 사례도 agent 골격을 가집니다.

!!! question "🤔 잠깐 — Agent vs Chained Prompts 의 차이?"
    Module 02 의 _prompt chaining_ 도 다단계 호출. Agent 와 무엇이 다른가?

    ??? success "정답"
        - **Chained prompts**: 단계가 _미리 정해짐_. 코드가 "1 단계 → 2 단계 → 3 단계" 를 _순서대로_ 호출.
        - **Agent**: 단계가 _LLM 의 선택_ 으로 _동적_ 결정. LLM 이 "이번엔 read_file, 다음엔 grep, 그 다음엔 또 read_file..." 를 결과 보고 결정.

        Chained 가 _predictable_, agent 가 _flexible_. Trade-off: agent 가 _무한 loop_ 또는 _비용 폭주_ 가능 (LLM 이 잘못 결정하면) → guard rail 필수.

---

## 2. Intuition — "직원 + 도구 키트" 비유와 한 장 그림

!!! tip "💡 한 줄 비유"
    **Agent ≈ 직원 + 도구 키트** — 목표를 받고, 도구를 _자율적으로_ 골라 호출하며, 결과를 보고 다음 행동을 결정하는 사람.<br>
    LLM(brain) + Tool + Memory + Planner 의 _loop_. 단일 호출로 못 푸는 다단계 task 를 풀 수 있고, 그래서 _guard 가 없으면_ 비용도 폭발할 수 있음.

### 한 장 그림 — Agent 의 4 구성요소와 ReAct loop

```d2
direction: down

U: "User\n목표 입력"
AG: "Agent — loop until 목표 달성 / max_steps / budget / abort" {
  direction: down
  L: "LLM (brain)\n- 추론, 계획, 의사결정\n- JSON tool_use 응답"
  M: "Memory\n(short / long / working)"
  T: "Tool dispatcher\nread_file\nrun_simulation\nsearch_faiss\n..."
  ENV: "실제 환경\n(FS / VCS / DB)"
  L -> M: "Thought"
  L -> T: "Action (tool_use)"
  T -> ENV
  ENV -> M: "Observation (tool result)"
  M -> L: "context" { style.stroke-dash: 4 }
}
U -> L
```

### 왜 이 구조인가 — Design rationale

LLM 단일 호출은 _stateless_ 입니다 — 매 호출이 독립이고, 외부 세계에 영향을 못 줍니다. Agent 는 그 한계를 (1) **memory** (이전 상태 보존), (2) **tools** (외부 영향), (3) **loop** (관찰 → 결정 → 행동 반복) 로 풀어냅니다. 그 대가로 _guard_ (max_steps, budget, dangerous-action filter) 가 추가로 필요해집니다 — 자율성 ↑ → 위험 ↑ 이라는 trade-off.

---

## 3. 작은 예 — UVM 에러를 디버그하는 ReAct loop 1 사이클

가장 단순한 시나리오. 사용자 목표 = "이 시뮬레이션 실패를 디버그하라". 도구 = `read_file`. ReAct 패턴으로 loop 를 한 번 돌립니다.

```d2
shape: sequence_diagram

U: "User"
A: "Agent (LLM)"
T: "Tool (read_file)"
G: "Guards"

# Note over A: Iteration 1
# Note over A: Iteration 2
# Note over A: Iteration 3 (terminal)
# Note over G: Guards (모든 iteration 체크)\nstep_count ≤ max_steps (10)\ntotal_tokens ≤ budget (50K)\n같은 (tool, args) 반복 금지 (loop detection)
U -> A: "'vsim/sim_out/run.log 의 시뮬 실패를 디버그하라'"
A -> A: "Thought: '먼저 로그를 읽어야 한다'"
A -> T: "Action: read_file('vsim/sim_out/run.log')"
T -> A: "'UVM_ERROR @ 1500ns scoreboard.sv(142):\nexpected=0xDEAD actual=0xBEEF'" { style.stroke-dash: 4 }
A -> A: "Observation: 첫 에러 = scoreboard mismatch"
A -> G: "check (steps, budget, loop)"
A -> A: "Thought: 'scoreboard.sv:142 비교 로직 확인'"
A -> T: "Action: read_file('lib/vtb/scoreboard.sv', lines=130-160)"
T -> A: "'if (expected_data == actual_data) ...'" { style.stroke-dash: 4 }
A -> A: "Observation: == 사용 (4-state X 처리 안 됨)"
A -> G: "check"
A -> A: "Thought: '충분한 정보 수집. 결론 보고'"
A -> U: "'근본원인: scoreboard.sv:142 의 ==\n가 X 를 mismatch 로 처리 못 함. === 로 변경.\n수정: line 142, == → ===\n검증: mrun test --test_name <foo> --seed 0'" { style.stroke-dash: 4 }
```

| Iter | Thought | Action | Observation |
|---|---|---|---|
| 1 | 로그를 읽자 | `read_file(run.log)` | UVM_ERROR @ scoreboard.sv:142 |
| 2 | 비교 로직 확인 | `read_file(scoreboard.sv, 130-160)` | `==` 사용 (4-state 미고려) |
| 3 | 결론 도출 | (no tool) | 근본원인 + 수정 + 검증 명령 |

```python
# Step 1 의 단순화 의사 코드 (Anthropic Claude tool use)
tools = [{
    "name": "read_file",
    "description": "파일을 읽고 내용을 반환",
    "input_schema": {
        "type": "object",
        "properties": {
            "path":  {"type": "string"},
            "lines": {"type": "string", "description": "예: '130-160'"}
        },
        "required": ["path"]
    }
}]

messages = [{"role": "user", "content": "run.log 의 시뮬 실패를 디버그하라"}]

for step in range(MAX_STEPS):
    resp = client.messages.create(model=MODEL, tools=tools, messages=messages)

    if resp.stop_reason == "end_turn":
        break  # 최종 답변

    for block in resp.content:
        if block.type == "tool_use":
            result = dispatch_tool(block.name, block.input)   # 실제 도구 실행
            messages.append({"role": "assistant", "content": resp.content})
            messages.append({"role": "user",
                             "content": [{"type": "tool_result",
                                          "tool_use_id": block.id,
                                          "content": result}]})
```

!!! note "여기서 잡아야 할 두 가지"
    **(1) Loop 의 _종료 조건_ 이 본질** — `end_turn` (자연 종료), `max_steps` (강제), `budget` (비용), `loop detection` (같은 호출 반복) 의 네 가지가 모두 필요. 어느 하나라도 빠지면 §7 의 비용 폭주 위험.<br>
    **(2) Tool 결과는 _구조화된 형태_ 로 LLM 에 돌려줘야 함** — 단순 텍스트면 LLM 이 파싱 실패. JSON 또는 명확한 라벨 (`[FILE: x] [LINES: y-z]`) 가 안전.

---

## 4. 일반화 — 4 구성요소 와 주요 패턴

### 4.1 Agent vs 일반 LLM

```
일반 LLM:
  사용자 → 질문 → LLM → 텍스트 답변
  (텍스트 생성만 가능, 외부 세계에 영향 없음)

Agent:
  사용자 → 목표 → LLM(두뇌) → 계획 수립 → 도구 호출 → 결과 관찰
  → 다음 행동 결정 → 도구 호출 → ... → 목표 달성 → 최종 보고
  (실제 행동을 수행: 파일 읽기, 코드 실행, API 호출 등)
```

| 항목 | 일반 LLM | Agent |
|------|---------|-------|
| 출력 | 텍스트만 | 텍스트 + 행동(도구 호출) |
| 상태 | Stateless (매 호출 독립) | Stateful (대화/작업 기억) |
| 복잡 작업 | 한 번의 답변 | 다단계 계획 + 실행 + 조정 |
| 외부 연동 | 없음 | 파일, DB, API, 코드 실행 |
| 자율성 | 없음 (사용자 주도) | 있음 (목표 설정 후 자율 수행) |

### 4.2 Agent 핵심 4 구성요소

```d2
direction: down

AG: "Agent" {
  direction: down
  L: "LLM (두뇌)\n추론, 계획, 의사결정"
  CAPS: "네 가지 능력" {
    direction: right
    C1: "Tools"
    C2: "Planning"
    C3: "Memory"
    C4: "Observation / Action"
  }
  TOOLS: "Tool 예시" {
    direction: right
    T1: "Tool 1\n파일 읽기"
    T2: "Tool 2\n코드 실행"
    T3: "Tool 3\nDB 검색"
  }
  L -> CAPS
  C1 -> TOOLS
}
```

### 4.3 동작 패턴 — ReAct / Plan-and-Execute / Tool-Augmented RAG

```
ReAct (Reasoning + Acting) — 가장 일반적:

  Thought: "로그를 읽어서 첫 에러를 찾아야 한다"
  Action:  read_file("vsim/sim_out/run.log")
  Observation: "UVM_ERROR @ 1500ns: Scoreboard mismatch..."

  Thought: "Scoreboard mismatch 다. Scoreboard 코드를 확인해야 한다"
  Action:  read_file("lib/vtb/scoreboard.sv")
  Observation: "line 142: expected_data == actual_data..."

  Thought: "비교 로직에서 == 대신 === 를 써야 할 것 같다"
  Action:  (최종 답변 생성)

  → Thought-Action-Observation 루프 반복
```

```
Plan-and-Execute — 먼저 계획, 그 다음 순차 실행:

  Plan:
    Step 1: 로그 파일 읽기
    Step 2: 에러 패턴 분류
    Step 3: 관련 소스 코드 확인
    Step 4: 근본 원인 분석
    Step 5: 수정 방안 제시

  Execute:
    Step 1 결과 → Step 2 에 반영 → ...

  장점: 구조적, 추적 가능
  단점: 계획 수립에 시간, 유연성 부족
```

```
Tool-Augmented RAG (RAG + Agent):

RAG 를 Agent 의 Tool 로 통합:

  Agent 의 도구 중 하나 = FAISS 검색
  → Agent 가 필요할 때 자율적으로 RAG 검색을 수행
  → 검색 결과를 기반으로 다음 행동 결정

  예: "sysMMU 검증 갭을 찾아라"
  1. FAISS 검색: sysMMU 관련 IP 스펙 조회
  2. FAISS 검색: 기존 검증 계획 조회
  3. 두 결과 비교 → 누락된 시나리오 식별
  4. 누락 시나리오에 대한 테스트 명령어 생성
```

---

## 5. 디테일 — Function Calling, Reflexion, Multi-Agent, MCP, 평가 프레임워크

### 5.1 Function Calling — LLM 이 도구를 선택하는 메커니즘

```
기존 (텍스트 파싱):
  LLM 이 "read_file('run.log')를 호출하겠습니다" 라고 텍스트로 출력
  → 정규표현식으로 파싱 → 불안정, 형식 오류 빈번

Function Calling (구조화):
  LLM 이 구조화된 JSON 으로 도구 호출을 출력
  → 파싱 불필요, 타입 안전, 100% 신뢰

동작 흐름:
  1. 시스템이 사용 가능한 도구를 JSON Schema 로 정의
  2. LLM 이 사용자 요청을 분석
  3. LLM 이 적절한 도구와 인자를 JSON 으로 선택
  4. 시스템이 실제 도구 실행
  5. 결과를 LLM 에 반환
  6. LLM 이 결과를 해석하고 다음 행동 결정
```

```python
import anthropic

client = anthropic.Anthropic()

# 도구 정의 (JSON Schema)
tools = [
    {
        "name": "read_simulation_log",
        "description": "VCS 시뮬레이션 로그 파일을 읽어 내용을 반환한다",
        "input_schema": {
            "type": "object",
            "properties": {
                "log_path": {
                    "type": "string",
                    "description": "로그 파일 경로 (예: vsim/sim_out/run.log)"
                },
                "lines": {
                    "type": "integer",
                    "description": "읽을 최대 줄 수 (기본: 전체)"
                }
            },
            "required": ["log_path"]
        }
    },
    {
        "name": "run_test",
        "description": "mrun 으로 시뮬레이션 테스트를 실행한다",
        "input_schema": {
            "type": "object",
            "properties": {
                "test_name": {"type": "string"},
                "seed": {"type": "integer", "default": 0},
                "coverage": {"type": "boolean", "default": False}
            },
            "required": ["test_name"]
        }
    }
]

# LLM 호출 (도구 목록 전달)
response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    tools=tools,
    messages=[{"role": "user", "content": "run.log 를 분석해서 실패 원인을 찾아줘"}]
)

# LLM 의 응답: 도구 호출 JSON
# {
#   "type": "tool_use",
#   "name": "read_simulation_log",
#   "input": {"log_path": "vsim/sim_out/run.log"}
# }
```

```
Parallel Tool Calling:

단일 호출: 도구 A 실행 → 결과 → 도구 B 실행 → 결과 → 답변
병렬 호출: 도구 A + 도구 B 동시 실행 → 결과 → 답변

LLM 이 한 턴에 여러 도구를 동시 호출 요청 가능:
  "run.log 와 scoreboard.sv 를 동시에 읽겠습니다"
  → [read_file("run.log"), read_file("scoreboard.sv")] 병렬 실행
  → 응답 지연 절반으로 감소

DV 적용:
  디버그 시 로그 + 소스 코드 + 이전 실행 결과를 동시에 수집
  → 전체 분석 시간 단축
```

### 5.2 Reflection / Self-Critique 패턴

```
일반 Agent:
  생성 → 출력 (검증 없음)

Reflection Agent:
  생성 → 자기 평가 → 부족하면 재생성 → 재평가 → ... → 출력

동작:
  Step 1 (생성): UVM Driver 코드 작성
  Step 2 (자기 평가):
    "내가 작성한 코드를 리뷰하겠다:
     ✓ factory 등록 있음
     ✗ config_db 에서 vif 를 가져오는 코드 누락
     ✗ reset 처리 없음"
  Step 3 (개선): 누락 사항 추가
  Step 4 (재평가):
    "✓ factory 등록, ✓ config_db get, ✓ reset 처리
     전체 체크리스트 통과"
  Step 5: 최종 출력
```

Reflexion 프레임워크 (Shinn et al., 2023):

```d2
direction: down

A: "Actor: 행동 수행\n코드 생성 / 디버그 분석 / 테스트 작성"
E: "Evaluator: 결과 평가\n컴파일 성공? 테스트 통과? 품질 충족?"
R: "Self-Reflection: 실패 원인 분석\n'config_db 가 env 아닌 test 레벨 set'\n→ 교훈 메모리 저장"
A2: "Actor: 교훈을 반영한 재시도"
A -> E
E -> R
R -> A2
A2 -> E: "다음 라운드" { style.stroke-dash: 4 }
```

효과:

- 반복 시도마다 성능 향상 (같은 실수 반복 방지)
- HumanEval (코드 생성) 벤치마크에서 Pass@1: 68% → 91%
- DV 에서: 컴파일 실패 → 원인 분석 → 수정 → 재컴파일 루프 자동화

### 5.3 Multi-Agent 시스템 상세

```
패턴 1: 순차 파이프라인 (Pipeline)
  Agent A (RTL 분석) → Agent B (코드 생성) → Agent C (검증)
  각 Agent 가 전문 영역 담당, 이전 Agent 의 출력을 입력으로 사용

패턴 2: 토론/합의 (Debate)
  Agent A: "이것은 TB 버그다"
  Agent B: "아니다, DUT 버그다. 근거: RTL line 42 에서..."
  Agent A: "근거를 확인했다. DUT 버그에 동의한다"
  → 여러 관점에서 분석하여 정확도 향상

패턴 3: 위계적 위임 (Hierarchical)
  Manager Agent: 전체 계획 수립, 하위 Agent 에 작업 분배
    ├── Analyst Agent: 로그 분석
    ├── Coder Agent: 코드 수정
    └── Tester Agent: 테스트 실행
  Manager 가 결과를 종합하여 최종 보고

패턴 4: 경쟁적 생성 (Competitive)
  Agent A 와 Agent B 가 독립적으로 같은 문제 해결
  → 두 결과를 비교하여 더 나은 것 선택
  → Self-Consistency 의 Agent 버전
```

DV Multi-Agent 예시:

```d2
direction: down

LEAD: "Lead Agent\n전체 검증 전략 수립"
RA: "RTL Analyzer\nDUT 인터페이스 / FSM 분석"
RT: "Tool: RTL 파서, FSDB 리더"
TB: "TB Generator\nUVM 컴포넌트 코드 생성"
TT: "Tool: 코드 생성, 컴파일러"
DG: "Debug Agent\n시뮬레이션 실패 분석"
DT: "Tool: 로그 파서, 파형 분석기"
CG: "Coverage Agent\n커버리지 갭 분석 / 테스트 생성"
CT: "Tool: 커버리지 DB, 테스트 생성기"
LEAD -> RA
RA -> RT
LEAD -> TB
TB -> TT
LEAD -> DG
DG -> DT
LEAD -> CG
CG -> CT
RA -> LEAD: "보고" { style.stroke-dash: 4 }
TB -> LEAD: "보고" { style.stroke-dash: 4 }
DG -> LEAD: "보고" { style.stroke-dash: 4 }
CG -> LEAD: "보고" { style.stroke-dash: 4 }
```

통신: 각 Agent 의 결과가 Lead Agent 에 보고. Lead Agent 가 다음 행동 결정 (추가 분석 요청, 완료 판단 등).

### 5.4 MCP (Model Context Protocol) — 도구 연결의 표준

```text
문제:
  Agent 마다 도구 연동 방식이 다름
  → LangChain 도구 ≠ Claude 도구 ≠ GPT 도구
  → 도구 하나를 여러 Agent 에서 쓰려면 각각 어댑터 필요

MCP (Anthropic 제안, 2024):
  LLM 과 외부 도구/데이터 소스를 연결하는 표준 프로토콜
  비유: USB-C (하나의 표준으로 모든 기기 연결)
```

구조:

```d2
direction: right
H: "MCP Host\n(Claude Code 등)"
S: "MCP Server\n(도구)"
H <-> S: "MCP Protocol\nJSON-RPC 2.0"
```

MCP Server 가 제공하는 것:

- **Tools**: 실행 가능한 기능 (파일 읽기, DB 검색 등)
- **Resources**: 데이터 접근 (파일, DB 레코드 등)
- **Prompts**: 재사용 가능한 프롬프트 템플릿

```
MCP 의 DV 적용 가능성:

VCS MCP Server:
  - Tool: compile(files), elaborate(top), simulate(test, seed)
  - Resource: 컴파일 로그, 시뮬레이션 결과

FAISS MCP Server:
  - Tool: search(query, k), add_documents(docs)
  - Resource: 인덱스 통계, 저장된 문서 목록

Waveform MCP Server:
  - Tool: get_signal(path, time_range), find_transitions(signal)
  - Resource: 신호 목록, 시간 범위 정보

장점:
  - 한 번 구현하면 Claude Code, VS Code, 커스텀 Agent 등 어디서든 사용
  - 도구 간 통일된 인터페이스 → Agent 개발 간소화
  - 커뮤니티에서 공유 가능
```

### 5.5 Agent 평가 — 벤치마크와 성공 지표

| 벤치마크 | 측정 대상 | 대표 태스크 |
|---------|----------|-----------|
| **SWE-bench** | 실제 GitHub 이슈 해결 | 코드 수정 후 테스트 통과 |
| **WebArena** | 웹 브라우저 작업 자동화 | 정보 검색, 폼 제출 |
| **GAIA** | 다단계 추론 + 도구 사용 | 실세계 문제 해결 |
| **ToolBench** | 도구 선택 및 사용 | 16,000+ API 중 적합 API 선택 |
| **AgentBench** | 종합 Agent 능력 | OS, DB, 게임 등 다양한 환경 |

```
DV Agent 평가 지표:

효과성 (Effectiveness):
  - Task Completion Rate: 주어진 작업을 완료한 비율
  - First-Pass Success: 첫 시도에 성공한 비율
  - Code Compile Rate: 생성 코드가 컴파일되는 비율
  - Test Pass Rate: 시뮬레이션 테스트를 통과하는 비율

효율성 (Efficiency):
  - Steps to Complete: 목표 달성까지 도구 호출 횟수
  - Token Usage: 소비한 총 토큰 수 (비용 지표)
  - Wall Clock Time: 실제 소요 시간
  - Tool Call Accuracy: 불필요한 도구 호출 없이 정확한 선택

안전성 (Safety):
  - Hallucination Rate: 존재하지 않는 파일/함수 참조 비율
  - Infinite Loop Rate: 무한 루프에 빠진 비율
  - Dangerous Action Rate: 위험한 명령(파일 삭제 등) 시도 비율
```

### 5.6 Agent 프레임워크

| 프레임워크 | 특징 | 적합한 경우 |
|-----------|------|-----------|
| **LangChain** | 가장 범용적, 체인/에이전트 패턴 | 일반적 RAG/Agent |
| **LangGraph** | 상태 머신 기반 복잡한 워크플로 | 다단계, 분기/루프 |
| **CrewAI** | 다중 Agent 협업 | 역할 분리된 팀 시뮬레이션 |
| **AutoGen** | Microsoft, 멀티 Agent 대화 | 연구/프로토타이핑 |
| **Claude Agent SDK** | Anthropic 공식, Tool Use 최적화 | Claude 기반 Agent |
| **직접 구현** | API 직접 호출 + 루프 | 완전한 제어, 경량 |

```python
# LangChain Agent 구조 (예시)
from langchain.agents import create_react_agent
from langchain.tools import Tool

# 도구 정의
tools = [
    Tool(name="read_log", func=read_log_file,
         description="시뮬레이션 로그를 읽는다"),
    Tool(name="search_ip_db", func=faiss_search,
         description="IP DB 에서 관련 정보를 검색한다"),
    Tool(name="generate_test", func=gen_test_cmd,
         description="테스트 실행 명령어를 생성한다"),
]

# Agent 생성
agent = create_react_agent(llm, tools, prompt)

# 실행
result = agent.invoke({"input": "sysMMU 검증 갭을 찾아라"})
```

### 5.7 DV 도메인 Agent 설계 (이력서 연결)

DAC 2026: AI-Assisted UVM 환경 자동화 — UVM Environment Automation Agent.
입력: RTL 인터페이스 정의 변경 (스펙 변경).
결과: 스펙 변경 대응 _수 일 → 수 시간_.

```d2
direction: down

IN: "입력\nRTL 인터페이스 정의 변경"
S1: "1. RTL 파서 (Tool)\nRTL 포트 변경 감지"
S2: "2. 템플릿 엔진 (Tool)\nUVM Agent / Driver / Monitor 템플릿 적용"
S3: "3. LLM\n포트별 Driver 로직 생성"
S4: "4. 컴파일러 (Tool)\n생성 코드 컴파일 검증"
S5: "5. LLM\n컴파일 에러 자동 수정"
OUT: "6. 최종 결과물 출력"
IN -> S1
S1 -> S2
S2 -> S3
S3 -> S4
S4 -> S5
S5 -> OUT
S5 -> S4: "재컴파일 루프" { style.stroke-dash: 4 }
```

DVCon 2025: Verification Gap Discovery Agent.

도구:

- **IP-XACT Parser** — 구조적 데이터 추출
- **FAISS Search** — IP 스펙에서 시맨틱 정보 검색
- **V-Plan Analyzer** — 기존 검증 계획 분석
- **Test Generator** — 테스트 명령어 자동 생성

워크플로:

```d2
direction: down

W1: "1. IP-XACT 에서 IP 별 기능 목록 추출"
W2: "2. FAISS 로 각 기능의 검증 요구사항 검색"
W3: "3. 기존 V-Plan 과 비교 → 누락 (Gap) 식별"
W4: "4. 누락 항목 → 테스트 명령어 자동 생성"
W5: "5. 결과 리포트 생성"
W1 -> W2
W2 -> W3
W3 -> W4
W4 -> W5
```

### 5.8 Agent 안전성과 한계

| 위험 | 설명 | 대응 |
|------|------|------|
| Hallucination 행동 | 존재하지 않는 도구/파일에 대해 행동 | 도구 목록 명시, 실행 전 검증 |
| 무한 루프 | Thought-Action 루프 탈출 못 함 | 최대 반복 횟수 설정 |
| 위험한 행동 | 파일 삭제, 시스템 명령 등 | 도구에 권한 제한, 샌드박스 |
| 비용 폭발 | 루프마다 LLM 호출 → 토큰 비용 | 토큰 상한, 루프 제한 |
| 일관성 부족 | 같은 작업에 다른 결과 | Temperature 낮게, 결과 검증 |

---

## 6. 흔한 오해 와 DV 디버그 체크리스트

### 흔한 오해

!!! danger "❓ 오해 1 — 'Agent 는 자동으로 잘 멈춘다'"
    **실제**: Agent loop 는 `max_steps` / `max_token` / cost guard 가 _없으면_ 무한 루프 + 비용 폭주. demo 의 짧은 task 에서는 자율 종료가 자연스러워 보이지만, production 은 4 종 guard (steps, budget, loop detection, abort signal) 모두 필요.<br>
    **왜 헷갈리는가**: 짧은 demo 만 보면 자연 종료가 당연해 보임.

!!! danger "❓ 오해 2 — 'Multi-Agent 가 항상 single Agent 보다 낫다'"
    **실제**: Multi-Agent 는 (1) 통신 오버헤드 (2) 비용 ↑ (3) 디버그 어려움. _전문성 분리가 진짜 필요할 때_ 만 가치. 단순 task 에 multi-agent 를 쓰면 latency·비용만 늘고 품질은 그대로.

!!! danger "❓ 오해 3 — 'Function Calling 이면 도구 호출이 항상 정확하다'"
    **실제**: JSON 형식은 보장되지만 _어떤_ 도구를 _어떤_ 인자로 부를지는 여전히 LLM 추론. 잘못된 path, 존재하지 않는 함수, 스키마 위반 인자가 자주 발생. **도구 실행 전에 입력 validate** 가 필수.

!!! danger "❓ 오해 4 — 'Reflection 은 비용만 늘린다'"
    **실제**: 단순 task 에서는 그렇지만, 복잡 추론 (HumanEval Pass@1) 에서 68% → 91% 향상. _task 복잡도와 매칭_ 해서 적용해야지, 모든 호출에 self-critique 를 넣으면 비용만 N 배.

!!! danger "❓ 오해 5 — 'MCP 만 쓰면 모든 도구가 호환된다'"
    **실제**: MCP 는 _프로토콜_ 만 표준. 도구의 _semantic_ (`read_file` 이 binary 도 받나? size 제한은?) 은 여전히 server 별로 다름. 표준화는 통합을 _쉽게_ 할 뿐 _자동_ 으로 만들지는 않음.

### DV 디버그 체크리스트 (Agent 운용 시 자주 만나는 실패)

| 증상 | 1차 의심 | 어디 보나 |
|---|---|---|
| 같은 (tool, args) 호출이 반복 (loop) | loop detection 부재 | 직전 N 호출과 비교, 같으면 abort |
| API 비용이 예상치의 10배+ | max_steps / budget 가드 미설정 | LangSmith / Langfuse 의 step count |
| Tool 결과가 LLM 에 안 반영됨 | tool_result message 누락 | conversation log 에서 `tool_use` ↔ `tool_result` 짝 |
| 존재하지 않는 파일을 read 시도 | hallucinated path | 실행 전 `os.path.exists` validate |
| LLM 이 도구를 _전혀_ 안 부름 | system prompt 가 도구 사용을 disabling | "도구를 적극 활용하라" 명시 + tool_choice="auto" |
| dangerous action (rm -rf) 시도 | 권한 sandboxing 부재 | tool dispatcher 의 명령 whitelist |
| 응답마다 도구 사용 패턴이 다름 | T > 0 으로 sampling | T=0 + 결정적 mode |
| Multi-agent 토론이 무한 반복 | 합의 종료 조건 부재 | "N 라운드 후 강제 결론" |

---

## 7. 핵심 정리 (Key Takeaways)

- **Agent = LLM + Tool + Memory + Planner** — 한 단계 호출이 아닌 _loop_.
- **ReAct** — 추론(Reason) 과 행동(Act) 을 번갈아 가며 외부와 상호작용.
- **Plan-and-Execute** — 먼저 plan 을 만들고 step-by-step 실행 (장시간 task 에 유리).
- **Reflexion** — 결과를 모델이 스스로 평가/수정.
- **MCP** — 도구 인터페이스 _프로토콜_ 표준화. semantic 호환은 별도 책임.
- **4 종 guard 필수** — `max_steps` · budget · loop detection · dangerous-action filter.

!!! warning "실무 주의점 — Agent Infinite Loop 로 인한 비용 폭주"
    **현상**: ReAct Agent 가 도구 호출 실패나 모호한 결과를 만나면 동일한 Action 을 반복 시도하는 루프에 빠져, 수백 번의 LLM 호출이 발생하고 API 비용이 폭주한다.

    **원인**: Agent loop 에 최대 스텝 수 제한(`max_steps`) 이 없거나, 이전 시도와 동일한 Action 을 재시도할 때 중단하는 탈출 조건이 없는 경우 발생한다.

    **점검 포인트**: Agent 프레임워크 설정에서 `max_iterations` 또는 `max_steps` 값이 설정되어 있는지 확인. 운영 환경의 LLM API 호출 로그에서 동일 tool + 동일 input 의 반복 호출 패턴을 모니터링하고, 비용 알림 임계값을 설정.

### 7.1 자가 점검

!!! question "🤔 Q1 — Tool 정의의 명확성 (Bloom: Apply)"
    당신은 `run_simulation` 라는 tool 을 agent 에 노출. Agent 가 _계속_ 잘못된 인자로 호출. 어떻게 _tool spec_ 을 개선?

    ??? success "정답"
        4 가지 개선:
        1. **Description 명확화**: "_DUT 의 testbench 를 실행한다_" → "_SystemVerilog testbench 를 VCS 로 컴파일 + 실행한다. 필요: test_name, optional: seed, fsdb_."
        2. **JSON schema strict**: `test_name` 을 enum (가능한 test 이름 목록) 으로.
        3. **Example 추가**: tool description 에 _valid 예시 1-2 개_.
        4. **Error 반환 명확화**: tool 이 실패하면 _LLM 이 이해 가능한 에러_ (예: "test_name 'foo' 가 존재 안 함. 사용 가능: a, b, c").

        Tool 의 좋은 spec 이 agent 정확도의 _가장 큰_ 결정 인자.

!!! question "🤔 Q2 — Multi-agent 통신 비용 (Bloom: Analyze)"
    당신은 _3 개_ specialized agent (analyzer, fixer, reviewer) 을 만들어 multi-agent 시스템 구성. 단일 agent 보다 token 비용 _얼마나_ 증가?

    ??? success "정답"
        보통 **3~10×**. 이유:
        - 각 agent 가 _자체 system prompt + 도구 정의_ 를 가짐 → 중복 토큰.
        - Agent 간 _통신_ 도 LLM call (예: analyzer 가 fixer 에게 결과 전달).
        - 한 agent 의 _맥락_ 이 다른 agent 와 _공유 안 됨_ → context 재구축 필요.

        Multi-agent 가 정당화되는 경우: 단일 agent 의 _system prompt 가 너무 길어서_ (~10K token) 한 호출에 다 못 넣을 때. 또는 _병렬화 ROI_ 가 큰 경우 (예: 100 파일을 동시 분석).

!!! question "🤔 Q3 — Guard rail 설계 (Bloom: Evaluate)"
    당신의 agent 가 _production_ 환경에서 1주일에 _10000 회_ 호출. 필수 guard 4 종을 _우선순위_ 로 설계.

    ??? success "정답"
        1. **Dangerous-action filter** (1순위): `rm -rf`, `git push --force` 같은 _복구 불가_ 명령은 agent 가 _제안만_ 하고 _사용자 confirm_ 필요. 비용보다 _안전성_ 우선.
        2. **Max steps** (2순위): 한 호출당 _N 회 도구 호출_ 제한 (예: 20). Infinite loop 방지.
        3. **Budget cap** (3순위): 일/월 단위 token 비용 한도. 폭주 시 자동 차단.
        4. **Loop detection** (4순위): 같은 action 이 _3 회 이상 반복_ 되면 break. Subtle infinite loop 잡기.

### 7.2 출처

**Internal (Confluence)**
- `How to run LangGraph` (id=999030785)
- `[Low-end] AI-Agents` (id=1237811201)
- `Report: Open-sourced Agent AI Trajectories with Human-in-the-Loop` (id=1214218318)

**External**
- *ReAct: Synergizing Reasoning and Acting in Language Models* — Yao et al., ICLR 2023
- *Reflexion: Language Agents with Verbal Reinforcement Learning* — Shinn et al., NeurIPS 2023
- *Plan-and-Solve Prompting* — Wang et al., ACL 2023
- Anthropic *Model Context Protocol (MCP)* spec, 2024
- Claude Code, Cursor agent docs (2024-2025)

---

## 다음 모듈

→ [Module 06 — Strategy Selection](06_strategy_selection.md): prompt vs RAG vs fine-tune 결정 기준.

[퀴즈 풀어보기 →](quiz/05_agent_architecture_quiz.md)


--8<-- "abbreviations.md"
