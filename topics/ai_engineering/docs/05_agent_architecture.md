# Unit 5: Agent 아키텍처

<div class="learning-meta">
  <span class="meta-badge meta-time">⏱ 20분</span>
  <span class="meta-badge meta-level-intermediate">📊 Intermediate</span>
</div>

## 핵심 개념
**Agent = LLM이 외부 도구(Tool)를 사용하고, 계획(Plan)을 세우고, 기억(Memory)을 유지하면서 복잡한 작업을 자율적으로 수행하는 시스템. 단순 Q&A를 넘어 실제 행동을 취하는 AI.**

---

## Agent vs 일반 LLM

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

---

## Agent 핵심 구성요소

```
+------------------------------------------------------------------+
|                         Agent                                     |
|                                                                   |
|  +--------------------+                                           |
|  |  LLM (두뇌)        |  ← 추론, 계획, 의사결정                  |
|  +--------------------+                                           |
|           |                                                       |
|  +--------+--------+--------+--------+                            |
|  |        |        |        |        |                            |
|  v        v        v        v        v                            |
| Tools   Planning  Memory  Observation  Action                     |
|                                                                   |
|  +----------+  +----------+  +----------+                         |
|  | Tool 1:  |  | Tool 2:  |  | Tool 3:  |                         |
|  | 파일 읽기|  | 코드 실행|  | DB 검색  |                         |
|  +----------+  +----------+  +----------+                         |
+------------------------------------------------------------------+
```

### 1. Tool Use (도구 사용)

```
Agent가 사용할 수 있는 도구를 정의:

  tools = [
    {
      "name": "read_file",
      "description": "파일을 읽는다",
      "parameters": {"path": "string"}
    },
    {
      "name": "run_simulation",
      "description": "VCS 시뮬레이션을 실행한다",
      "parameters": {"test_name": "string", "seed": "int"}
    },
    {
      "name": "search_faiss",
      "description": "FAISS 인덱스에서 유사 문서를 검색한다",
      "parameters": {"query": "string", "k": "int"}
    }
  ]

동작:
  LLM이 "이 도구를 이런 인자로 호출하겠다"를 결정
  → 시스템이 실제 도구 실행
  → 결과를 LLM에 전달
  → LLM이 결과를 보고 다음 행동 결정
```

### 2. Planning (계획 수립)

```
복잡한 작업을 하위 작업으로 분해:

  목표: "이 시뮬레이션 실패를 디버그하라"

  계획:
  1. run.log 파일 읽기
  2. 첫 번째 에러 메시지 식별
  3. 에러 발생 컴포넌트의 소스 코드 읽기
  4. 근본 원인 분석
  5. 수정 방안 제시

  각 단계에서 도구를 호출하고, 결과에 따라 계획을 수정
```

### 3. Memory (기억)

```
Short-term Memory:
  - 현재 대화/작업의 컨텍스트
  - LLM의 Context Window에 유지

Long-term Memory:
  - 이전 대화/작업의 결과
  - Vector DB에 저장 → 필요 시 검색
  - 학습된 패턴, 선호도 등

Working Memory:
  - 현재 작업의 중간 결과
  - 변수, 상태, 계산 결과 등
```

---

## Agent 동작 패턴

### ReAct (Reasoning + Acting)

```
가장 일반적인 Agent 패턴:

  Thought: "로그를 읽어서 첫 에러를 찾아야 한다"
  Action:  read_file("vsim/sim_out/run.log")
  Observation: "UVM_ERROR @ 1500ns: Scoreboard mismatch..."

  Thought: "Scoreboard mismatch다. Scoreboard 코드를 확인해야 한다"
  Action:  read_file("lib/vtb/scoreboard.sv")
  Observation: "line 142: expected_data == actual_data..."

  Thought: "비교 로직에서 == 대신 === 를 써야 할 것 같다"
  Action:  (최종 답변 생성)

  → Thought-Action-Observation 루프 반복
```

### Plan-and-Execute

```
먼저 전체 계획을 세우고, 순차적으로 실행:

  Plan:
    Step 1: 로그 파일 읽기
    Step 2: 에러 패턴 분류
    Step 3: 관련 소스 코드 확인
    Step 4: 근본 원인 분석
    Step 5: 수정 방안 제시

  Execute:
    Step 1 결과 → Step 2에 반영 → ...

  장점: 구조적, 추적 가능
  단점: 계획 수립에 시간, 유연성 부족
```

### Tool-Augmented RAG (RAG + Agent)

```
RAG를 Agent의 Tool로 통합:

  Agent의 도구 중 하나 = FAISS 검색
  → Agent가 필요할 때 자율적으로 RAG 검색을 수행
  → 검색 결과를 기반으로 다음 행동 결정

  예: "sysMMU 검증 갭을 찾아라"
  1. FAISS 검색: sysMMU 관련 IP 스펙 조회
  2. FAISS 검색: 기존 검증 계획 조회
  3. 두 결과 비교 → 누락된 시나리오 식별
  4. 누락 시나리오에 대한 테스트 명령어 생성
```

---

## Function Calling — LLM이 도구를 선택하는 메커니즘

### API 수준의 동작 원리

```
기존 (텍스트 파싱):
  LLM이 "read_file('run.log')를 호출하겠습니다" 라고 텍스트로 출력
  → 정규표현식으로 파싱 → 불안정, 형식 오류 빈번

Function Calling (구조화):
  LLM이 구조화된 JSON으로 도구 호출을 출력
  → 파싱 불필요, 타입 안전, 100% 신뢰

동작 흐름:
  1. 시스템이 사용 가능한 도구를 JSON Schema로 정의
  2. LLM이 사용자 요청을 분석
  3. LLM이 적절한 도구와 인자를 JSON으로 선택
  4. 시스템이 실제 도구 실행
  5. 결과를 LLM에 반환
  6. LLM이 결과를 해석하고 다음 행동 결정
```

### 실제 API 호출 예시 (Anthropic Claude)

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
        "description": "mrun으로 시뮬레이션 테스트를 실행한다",
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
    messages=[{"role": "user", "content": "run.log를 분석해서 실패 원인을 찾아줘"}]
)

# LLM의 응답: 도구 호출 JSON
# {
#   "type": "tool_use",
#   "name": "read_simulation_log",
#   "input": {"log_path": "vsim/sim_out/run.log"}
# }
```

### Parallel Tool Calling

```
단일 호출: 도구 A 실행 → 결과 → 도구 B 실행 → 결과 → 답변
병렬 호출: 도구 A + 도구 B 동시 실행 → 결과 → 답변

LLM이 한 턴에 여러 도구를 동시 호출 요청 가능:
  "run.log와 scoreboard.sv를 동시에 읽겠습니다"
  → [read_file("run.log"), read_file("scoreboard.sv")] 병렬 실행
  → 응답 지연 절반으로 감소

DV 적용:
  디버그 시 로그 + 소스 코드 + 이전 실행 결과를 동시에 수집
  → 전체 분석 시간 단축
```

---

## Reflection / Self-Critique 패턴

### 자기 검증 루프

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
     ✗ config_db에서 vif를 가져오는 코드 누락
     ✗ reset 처리 없음"
  Step 3 (개선): 누락 사항 추가
  Step 4 (재평가):
    "✓ factory 등록, ✓ config_db get, ✓ reset 처리
     전체 체크리스트 통과"
  Step 5: 최종 출력
```

### Reflexion 프레임워크 (Shinn et al., 2023)

```
+------------------------------------------------------------------+
|  Actor: 행동 수행                                                 |
|  → 코드 생성 / 디버그 분석 / 테스트 작성                         |
+------------------------------------------------------------------+
       |
       v
+------------------------------------------------------------------+
|  Evaluator: 결과 평가                                             |
|  → 컴파일 성공? 테스트 통과? 품질 기준 충족?                      |
+------------------------------------------------------------------+
       |
       v
+------------------------------------------------------------------+
|  Self-Reflection: 실패 원인 분석                                  |
|  → "config_db 경로가 env가 아닌 test 레벨에서 set되었다"         |
|  → 이 교훈을 메모리에 저장                                       |
+------------------------------------------------------------------+
       |
       v (다음 시도에 교훈 반영)
+------------------------------------------------------------------+
|  Actor: 교훈을 반영한 재시도                                      |
+------------------------------------------------------------------+

효과:
  - 반복 시도마다 성능 향상 (같은 실수 반복 방지)
  - HumanEval (코드 생성) 벤치마크에서 Pass@1: 68% → 91%
  - DV에서: 컴파일 실패 → 원인 분석 → 수정 → 재컴파일 루프 자동화
```

---

## Multi-Agent 시스템 상세

### 협업 패턴

```
패턴 1: 순차 파이프라인 (Pipeline)
  Agent A (RTL 분석) → Agent B (코드 생성) → Agent C (검증)
  각 Agent가 전문 영역 담당, 이전 Agent의 출력을 입력으로 사용

패턴 2: 토론/합의 (Debate)
  Agent A: "이것은 TB 버그다"
  Agent B: "아니다, DUT 버그다. 근거: RTL line 42에서..."
  Agent A: "근거를 확인했다. DUT 버그에 동의한다"
  → 여러 관점에서 분석하여 정확도 향상

패턴 3: 위계적 위임 (Hierarchical)
  Manager Agent: 전체 계획 수립, 하위 Agent에 작업 분배
    ├── Analyst Agent: 로그 분석
    ├── Coder Agent: 코드 수정
    └── Tester Agent: 테스트 실행
  Manager가 결과를 종합하여 최종 보고

패턴 4: 경쟁적 생성 (Competitive)
  Agent A와 Agent B가 독립적으로 같은 문제 해결
  → 두 결과를 비교하여 더 나은 것 선택
  → Self-Consistency의 Agent 버전
```

### DV Multi-Agent 예시

```
+------------------------------------------------------------------+
|  DV Verification Agent Team                                       |
|                                                                   |
|  [Lead Agent] — 전체 검증 전략 수립                               |
|      |                                                            |
|      ├── [RTL Analyzer] — DUT 인터페이스/FSM 분석                 |
|      |       └── Tool: RTL 파서, FSDB 리더                        |
|      |                                                            |
|      ├── [TB Generator] — UVM 컴포넌트 코드 생성                  |
|      |       └── Tool: 코드 생성, 컴파일러                        |
|      |                                                            |
|      ├── [Debug Agent] — 시뮬레이션 실패 분석                     |
|      |       └── Tool: 로그 파서, 파형 분석기                     |
|      |                                                            |
|      └── [Coverage Agent] — 커버리지 갭 분석/테스트 생성          |
|              └── Tool: 커버리지 DB, 테스트 생성기                  |
|                                                                   |
|  통신: 각 Agent의 결과가 Lead Agent에 보고                        |
|  Lead Agent가 다음 행동 결정 (추가 분석 요청, 완료 판단 등)       |
+------------------------------------------------------------------+
```

---

## MCP (Model Context Protocol) — 도구 연결의 표준

### MCP란?

```
문제:
  Agent마다 도구 연동 방식이 다름
  → LangChain 도구 ≠ Claude 도구 ≠ GPT 도구
  → 도구 하나를 여러 Agent에서 쓰려면 각각 어댑터 필요

MCP (Anthropic 제안, 2024):
  LLM과 외부 도구/데이터 소스를 연결하는 표준 프로토콜
  
  비유: USB-C (하나의 표준으로 모든 기기 연결)
  
  구조:
  +----------+     MCP Protocol    +----------+
  | MCP Host | ←——————————————→   | MCP      |
  | (Claude  |   JSON-RPC 2.0     | Server   |
  |  Code 등)|                     | (도구)   |
  +----------+                     +----------+
  
  MCP Server가 제공하는 것:
  - Tools: 실행 가능한 기능 (파일 읽기, DB 검색 등)
  - Resources: 데이터 접근 (파일, DB 레코드 등)
  - Prompts: 재사용 가능한 프롬프트 템플릿
```

### MCP의 DV 적용 가능성

```
MCP Server 예시:

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

---

## Agent 평가 — 벤치마크와 성공 지표

### 주요 벤치마크

| 벤치마크 | 측정 대상 | 대표 태스크 |
|---------|----------|-----------|
| **SWE-bench** | 실제 GitHub 이슈 해결 | 코드 수정 후 테스트 통과 |
| **WebArena** | 웹 브라우저 작업 자동화 | 정보 검색, 폼 제출 |
| **GAIA** | 다단계 추론 + 도구 사용 | 실세계 문제 해결 |
| **ToolBench** | 도구 선택 및 사용 | 16,000+ API 중 적합 API 선택 |
| **AgentBench** | 종합 Agent 능력 | OS, DB, 게임 등 다양한 환경 |

### DV Agent 평가 지표

```
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

---

## Agent 프레임워크

### 주요 프레임워크 비교

| 프레임워크 | 특징 | 적합한 경우 |
|-----------|------|-----------|
| **LangChain** | 가장 범용적, 체인/에이전트 패턴 | 일반적 RAG/Agent |
| **LangGraph** | 상태 머신 기반 복잡한 워크플로 | 다단계, 분기/루프 |
| **CrewAI** | 다중 Agent 협업 | 역할 분리된 팀 시뮬레이션 |
| **AutoGen** | Microsoft, 멀티 Agent 대화 | 연구/프로토타이핑 |
| **Claude Agent SDK** | Anthropic 공식, Tool Use 최적화 | Claude 기반 Agent |
| **직접 구현** | API 직접 호출 + 루프 | 완전한 제어, 경량 |

### LangChain Agent 구조 (예시)

```python
from langchain.agents import create_react_agent
from langchain.tools import Tool

# 도구 정의
tools = [
    Tool(name="read_log", func=read_log_file,
         description="시뮬레이션 로그를 읽는다"),
    Tool(name="search_ip_db", func=faiss_search,
         description="IP DB에서 관련 정보를 검색한다"),
    Tool(name="generate_test", func=gen_test_cmd,
         description="테스트 실행 명령어를 생성한다"),
]

# Agent 생성
agent = create_react_agent(llm, tools, prompt)

# 실행
result = agent.invoke({"input": "sysMMU 검증 갭을 찾아라"})
```

---

## DV 도메인 Agent 설계 (이력서 연결)

### DAC 2026: AI-Assisted UVM 환경 자동화

```
+------------------------------------------------------------------+
|  UVM Environment Automation Agent                                 |
|                                                                   |
|  입력: RTL 인터페이스 정의 변경 (스펙 변경)                       |
|                                                                   |
|  Agent 동작:                                                      |
|  1. [Tool: RTL 파서] RTL 포트 변경 사항 감지                      |
|  2. [Tool: 템플릿 엔진] UVM Agent/Driver/Monitor 템플릿 적용      |
|  3. [LLM] 포트별 적절한 Driver 로직 생성                         |
|  4. [Tool: 컴파일러] 생성된 코드 컴파일 검증                      |
|  5. [LLM] 컴파일 에러 시 자동 수정                               |
|  6. 최종 결과물 출력                                              |
|                                                                   |
|  결과: 스펙 변경 대응 수 일 → 수 시간                             |
+------------------------------------------------------------------+
```

### DVCon 2025: 검증 갭 발견 Agent

```
+------------------------------------------------------------------+
|  Verification Gap Discovery Agent                                 |
|                                                                   |
|  도구:                                                            |
|  - IP-XACT Parser: 구조적 데이터 추출                             |
|  - FAISS Search: IP 스펙에서 시맨틱 정보 검색                     |
|  - V-Plan Analyzer: 기존 검증 계획 분석                           |
|  - Test Generator: 테스트 명령어 자동 생성                        |
|                                                                   |
|  워크플로:                                                        |
|  1. IP-XACT에서 IP별 기능 목록 추출                               |
|  2. FAISS로 각 기능의 검증 요구사항 검색                          |
|  3. 기존 V-Plan과 비교 → 누락(Gap) 식별                          |
|  4. 누락 항목에 대한 테스트 명령어 자동 생성                      |
|  5. 결과 리포트 생성                                              |
+------------------------------------------------------------------+
```

---

## Agent 안전성과 한계

| 위험 | 설명 | 대응 |
|------|------|------|
| Hallucination 행동 | 존재하지 않는 도구/파일에 대해 행동 | 도구 목록 명시, 실행 전 검증 |
| 무한 루프 | Thought-Action 루프 탈출 못 함 | 최대 반복 횟수 설정 |
| 위험한 행동 | 파일 삭제, 시스템 명령 등 | 도구에 권한 제한, 샌드박스 |
| 비용 폭발 | 루프마다 LLM 호출 → 토큰 비용 | 토큰 상한, 루프 제한 |
| 일관성 부족 | 같은 작업에 다른 결과 | Temperature 낮게, 결과 검증 |

---

## Q&A

**Q: Agent와 일반 LLM 호출의 차이는?**
> "일반 LLM은 텍스트만 생성하고 외부 세계에 영향을 줄 수 없다. Agent는 LLM을 두뇌로 사용하면서 도구(파일 읽기, 코드 실행, DB 검색)를 호출하여 실제 행동을 수행한다. 핵심은 Thought-Action-Observation 루프로, LLM이 관찰 결과를 보고 다음 행동을 자율적으로 결정한다는 것이다."

**Q: DV에서 Agent를 어떻게 활용했나?**
> "두 가지 사례: (1) DVCon — IP-XACT 파서, FAISS 검색, V-Plan 분석기를 도구로 갖춘 Agent가 검증 갭을 자율적으로 발견하고 테스트 명령어를 생성. (2) DAC — RTL 포트 변경 감지 → UVM 컴포넌트 자동 재생성 → 컴파일 검증까지 수행하는 자동화 Agent. 두 경우 모두 '도구 정의 + LLM 추론 + 루프'라는 Agent 패턴을 적용했다."

**Q: Function Calling이 텍스트 파싱보다 나은 이유는?**
> "구조적 신뢰성이다. 텍스트 파싱은 LLM이 'read_file(run.log)'라고 출력해야 하는데, 형식이 약간만 달라도 파싱 실패한다. Function Calling은 JSON Schema로 도구를 정의하고, LLM이 구조화된 JSON으로 호출하므로 타입 안전하고 100% 파싱 가능하다. 또한 LLM이 어떤 도구를 사용할지의 결정 자체가 학습되어 있어, 도구 선택 정확도도 높다."

**Q: Reflection 패턴은 왜 Agent 품질을 향상시키는가?**
> "인간 개발자와 같은 원리다. 코드를 작성하고 바로 제출하는 것보다, 한 번 더 리뷰하면 품질이 올라간다. Reflection Agent는 (1) 생성, (2) 자기 평가, (3) 개선을 루프로 반복한다. HumanEval 벤치마크에서 Pass@1이 68%에서 91%로 향상된 사례가 있다. DV에서는 컴파일 실패→원인 분석→수정→재컴파일 루프를 자동화하는 데 이 패턴을 적용한다."

**Q: Multi-Agent 시스템은 언제 단일 Agent보다 유리한가?**
> "세 가지 경우: (1) 전문성 분리가 필요할 때 — RTL 분석, 코드 생성, 디버그 각각의 전문 프롬프트와 도구가 다름. (2) 검증이 필요할 때 — 생성 Agent와 리뷰 Agent를 분리하면 자기 검증의 한계를 넘을 수 있음. (3) 병렬 작업이 가능할 때 — 로그 분석과 RTL 분석을 동시 수행. 단점은 Agent 간 통신 오버헤드와 비용 증가이므로, 단일 Agent로 충분한 작업에는 과잉이다."

**Q: MCP란 무엇이고 DV에서의 가치는?**
> "Model Context Protocol은 Anthropic이 제안한 LLM-도구 연결 표준이다. USB-C처럼 하나의 표준으로 어떤 LLM/Agent에서든 도구를 사용할 수 있게 한다. DV에서의 가치는 VCS 컴파일러, FAISS 검색, 파형 분석기 등을 MCP Server로 한 번 구현하면, Claude Code, VS Code Copilot, 커스텀 Agent 어디서든 동일하게 사용 가능하다는 것이다."

<div class="chapter-nav">
  <a class="nav-prev" href="04_rag.md">
    <div class="nav-label">◀ 이전</div>
    <div class="nav-title">RAG (Retrieval-Augmented Generation)</div>
  </a>
  <a class="nav-next" href="06_strategy_selection.md">
    <div class="nav-label">다음 ▶</div>
    <div class="nav-title">Fine-tuning vs RAG vs Prompt — 전략 선택</div>
  </a>
</div>
