# Module 02 — Prompt Engineering & In-Context Learning

<!-- DV-SKOOL-CH-CTX:start -->
<div class="chapter-context" data-cat="applied">
  <a class="chapter-back" href="../">
    <span class="chapter-back-arrow">←</span>
    <span class="chapter-back-icon">🤖</span>
    <span class="chapter-back-text">AI Engineering</span>
  </a>
  <span class="chapter-divider">›</span>
  <span class="chapter-marker">Module 02</span>
</div>
<!-- DV-SKOOL-CH-CTX:end -->

<!-- DV-SKOOL-CH-TOC:start -->
<div class="page-toc">
  <span class="page-toc-label">목차</span>
  <a class="page-toc-link" href="#1-why-care-prompt-가-왜-출력의-운명을-결정하는가">1. Why care?</a>
  <a class="page-toc-link" href="#2-intuition-신입-onboarding-비유와-한-장-그림">2. Intuition</a>
  <a class="page-toc-link" href="#3-작은-예-동일-task-naive-vs-구조화-prompt-를-한-호출씩-비교">3. 작은 예 — naive vs 구조화</a>
  <a class="page-toc-link" href="#4-일반화-prompt-기법의-축과-icl-의-원리">4. 일반화 — Prompt 기법의 축</a>
  <a class="page-toc-link" href="#5-디테일-기법별-동작-패턴-평가-체크리스트-사내-템플릿">5. 디테일</a>
  <a class="page-toc-link" href="#6-흔한-오해-와-dv-디버그-체크리스트">6. 흔한 오해 + 디버그</a>
  <a class="page-toc-link" href="#7-핵심-정리-key-takeaways">7. 핵심 정리</a>
</div>
<!-- DV-SKOOL-CH-TOC:end -->

!!! objective "학습 목표"
    이 모듈을 마치면:

    - **Define** Zero-shot / Few-shot / CoT / Self-Consistency 의 정의를 구분할 수 있다.
    - **Explain** Few-shot 예시가 왜 모델 가중치 변경 없이 동작을 바꿀 수 있는지 설명할 수 있다.
    - **Apply** 분류·요약·코드 생성 task 각각에 적합한 prompt 패턴을 작성할 수 있다.
    - **Analyze** 동일 task 의 prompt 두 개를 정확도 / token cost / robustness 로 비교 분석할 수 있다.
    - **Evaluate** Prompt vs Fine-tune 결정을 비용·일관성·통제 측면에서 평가할 수 있다.

!!! info "사전 지식"
    - [Module 01](01_llm_fundamentals.md) — 자기회귀 생성, context window, KV cache
    - 기본 NLP 용어 (token, classification, summarization)

---

## 1. Why care? — Prompt 가 왜 출력의 운명을 결정하는가

### 1.1 시나리오 — 같은 모델, 다른 답

당신은 Claude Sonnet 으로 _SystemVerilog UVM testbench_ 를 만들고 싶습니다. 두 prompt:

**Prompt A** (naive): `"UVM 테스트벤치 만들어줘"` (8 token)

응답:
```systemverilog
// 일반적인 UVM 코드 ...
class my_test extends uvm_test;
  $display("Test running");  // ⚠ $display 금지된 패턴
  // ... 추측된 port 이름들
endclass
```

**Prompt B** (구조화): _Role + DUT spec + 컨벤션 + 출력 포맷_ 명시 (150 token)

응답:
```systemverilog
class axi_basic_test extends uvm_test;
  `uvm_component_utils(axi_basic_test)
  // ... 실제 DUT 의 port 와 일치
  `uvm_info("AXI_TEST", $sformatf(...))  // ✓ UVM macro 사용
endclass
```

**결과 차이**: 같은 모델, 같은 temperature, 다른 prompt → _컴파일 통과율_ 30% → 95%. **모델 변경 없이 prompt 만 바꿔서**.

이게 prompt engineering 이 LLM 활용에서 _가장 큰 ROI_ 인 이유. 모든 RAG / Agent / Fine-tune-after-Prompt 워크플로의 _마지막 단_ 은 결국 prompt — 검색을 잘해도, 도구를 잘 정의해도, prompt 가 모호하면 모든 노력이 무산됩니다.

이 모듈은 학습자가 "왜 이 prompt 가 더 잘 동작하는지" 를 _가설 → 실험 → 검증_ 사이클로 다룰 수 있게 만듭니다. 다음 모듈 (Embedding, RAG, Agent) 의 모든 LLM 호출 단에서 이 모듈의 패턴이 그대로 재등장합니다.

!!! question "🤔 잠깐 — Few-shot 이 zero-shot 보다 _왜_ 잘 동작?"
    LLM 의 _가중치는 동일_. 그런데 1-2 개 예시를 prompt 에 넣으면 정확도가 _10~30%_ 향상. 가중치가 바뀐 게 아닌데 어떻게?

    ??? success "정답"
        **In-context learning (ICL)** — Transformer 의 attention 이 _prompt 내의 example pattern_ 을 보고 "**이 패턴을 흉내내라**" 라는 신호를 받음.

        구체적으로:
        - Zero-shot: 학습 분포 전체의 _평균_ 같은 응답.
        - Few-shot: prompt 의 example 이 attention 으로 _특정 sub-distribution_ 활성화 → 그 영역의 응답.

        Mechanism 가설 (Olsson et al. 2022): "**induction heads**" 라는 특정 attention head 가 "이전에 본 패턴" 을 찾아서 흉내냄. 가중치는 동일하지만 _activation 분포_ 가 다른 영역으로 routing.

---

## 2. Intuition — 신입 onboarding 비유와 한 장 그림

!!! tip "💡 한 줄 비유"
    **Prompt Engineering ≈ 신입 직원 onboarding instruction** — 같은 사람(LLM)에게 "역할 + 맥락 + 작업 + 제약 + 형식" 을 어떻게 주느냐로 결과가 갈립니다.<br>
    가중치 변경(=재교육) 없이도 행동을 통제. 그래서 **가장 싸고 가장 빠른** LLM 활용법.

### 한 장 그림 — 같은 모델이 prompt 만으로 출력이 바뀌는 구조

```d2
direction: down

M: "같은 LLM (가중치 동결)"
PA: "Prompt A\n'코드 짜줘'"
PB: "Prompt B\nRole + Context + Task + Format"
PC: "Prompt C\nFew-shot + CoT"
OA: "generic\n(low quality)"
OB: "구체적\n(mid)"
OC: "단계 추론 + 일관 형식\n(high quality, ↑ tokens)"
NOTE: "가중치 동일, 입력 분포만 변경\n→ 출력 분포가 달라짐"
M -> PA
PA -> OA
M -> PB
PB -> OB
M -> PC
PC -> OC
OA -> NOTE { style.stroke-dash: 4 }
OB -> NOTE { style.stroke-dash: 4 }
OC -> NOTE { style.stroke-dash: 4 }
```

### 왜 작동하는가 — Design rationale

LLM 은 학습 시 _수많은_ "역할 + 형식 + 답변" 패턴을 봤습니다. Prompt 에서 그 패턴 중 하나를 _구체적으로 활성화_ 하면, 모델은 학습 분포 상에서 _그 영역_ 의 응답을 생성합니다. 즉 prompt 는 "어떤 sub-distribution 으로 갈지" 를 지시하는 routing 신호. 이게 zero-shot 보다 few-shot 이 우수하고, naive 보다 structured 가 우수한 이유입니다 — 학습 분포 안의 _더 명확한 영역_ 으로 라우팅하니까.

---

## 3. 작은 예 — 동일 task 를 naive vs 구조화 prompt 로 한 호출씩 비교

가장 단순한 시나리오. 동일 LLM 에 동일 RTL 정보를 주고, prompt 만 바꿔서 한 호출씩 응답을 비교합니다.

```d2
direction: down

SAME: "동일 모델 (Claude Sonnet, T=0)" {
  A: "Prompt A — naive" {
    A0: "'UVM 테스트벤치 만들어줘'"
    A1: "① tokenize (~6 tok)"
    A2: "② attention"
    A3: "③ generate"
    A4: "④ 일반적 코드, port 추측"
    A5: "⑤ display 시스템콜 사용 (UVM에서 금지)"
    A6: "⑥ factory 등록 누락"
    A7: "⑦ 컴파일 실패 60%" { style.stroke: "#c0392b"; style.stroke-width: 2 }
    A0 -> A1 -> A2 -> A3 -> A4 -> A5 -> A6 -> A7
  }
  B: "Prompt B — 구조화" {
    B0: "[Role][Context][Task]\n[Constraint][Format]"
    B1: "① tokenize (~150 tok)"
    B2: "② attention (richer routing)"
    B3: "③ generate"
    B4: "④ 정확한 port + 컨벤션 준수"
    B5: "⑤ uvm_info 사용 (백틱 매크로)"
    B6: "⑥ factory + config_db get"
    B7: "⑦ 컴파일 통과 87%" { style.stroke: "#27ae60"; style.stroke-width: 2 }
    B0 -> B1 -> B2 -> B3 -> B4 -> B5 -> B6 -> B7
  }
}
```

| Step | Prompt A (naive) | Prompt B (구조화) |
|---|---|---|
| ① 입력 | 6 token (단일 문장) | ~150 token (5축 구조) |
| ② 라우팅 | "general code" 분포 | "UVM agent + AXI-Stream + factory pattern" 분포 |
| ③ 생성 | 흔한 패턴의 평균 | 학습 분포 안의 _구체적_ 영역 |
| ④ 정확성 | port 추측, hallucination 가능 | 명시된 port 만 사용 |
| ⑤ 컨벤션 | $display 등 흔한 패턴 | 제약 명시로 회피 |
| ⑥ 컴포넌트 구조 | 핵심 누락 | 형식 spec 으로 강제 |
| ⑦ 컴파일 통과율 | ~60% | ~87% |

```
같은 모델, 다른 프롬프트 → 완전히 다른 결과:

  나쁜 프롬프트:
    "UVM 테스트벤치 만들어줘"
    → 일반적이고 부정확한 코드

  좋은 프롬프트:
    "AXI-Stream 인터페이스를 가진 MMU IP 의 UVM Agent 를 작성해줘.
     Driver 는 tdata, tvalid, tready 만 처리하고,
     Monitor 는 Transaction 을 수집하여 analysis port 로 전달.
     SystemVerilog UVM 1.2 스타일을 따를 것."
    → 구체적이고 사용 가능한 코드
```

!!! note "여기서 잡아야 할 두 가지"
    **(1) 모델은 동일** — 가중치는 한 비트도 안 바뀌었습니다. 결과 차이 = _입력 분포 변경_ 의 효과.<br>
    **(2) 토큰 비용은 prompt B 가 더 큼** — 입력 토큰이 25배. 그러나 _재시도 비용_ + _디버그 비용_ 까지 합치면 prompt B 가 압도적으로 쌉니다.

---

## 4. 일반화 — Prompt 기법의 축과 ICL 의 원리

### 4.1 다섯 축 (Role · Context · Task · Constraint · Format)

```
       Role           "당신은 UVM 1.2 전문가"
        │
        ├── Context  "AXI-Stream tdata 256bit, tvalid, tready"
        │
        ├── Task     "UVM Monitor 를 작성하라"
        │
        ├── Constraint  "$display 금지, factory 등록 필수, vif 는 config_db get"
        │
        └── Format   "include guard 가 있는 .svh 파일, 한 파일 안에 모든 헤더 포함"
```

이 다섯 축은 prompt 를 _재현 가능_ 하고 _측정 가능_ 하게 만듭니다. 검수 시 "어느 축이 부족했는가" 로 분해 가능.

### 4.2 ICL (In-Context Learning) — 가중치 안 바꾸고 패턴을 가르치기

```
Fine-tuning 없이, 프롬프트에 예시를 포함시키는 것만으로
모델이 새로운 패턴을 학습하는 현상

예시:
  프롬프트:
    "IP-XACT 에서 추출한 정보로 검증 시나리오를 생성하는 예시:

     입력: {ip: 'sysMMU', feature: 'TLB invalidation'}
     출력: mrun test --test_name tlb_invalidate_all --sys_name mmu

     입력: {ip: 'sysMMU', feature: 'page fault handling'}
     출력: mrun test --test_name page_fault_recovery --sys_name mmu

     입력: {ip: 'DCMAC', feature: 'packet CRC check'}
     출력: "

  → 모델이 패턴을 학습하고 새 입력에 적용
  → DVCon 논문의 "LLM-Based Test Generation" 이 이 방식
```

| 항목 | In-Context Learning | Fine-tuning |
|------|-------------------|-------------|
| 모델 변경 | 없음 | 가중치 업데이트 |
| 비용 | 추론 비용만 | 학습 비용 + 추론 비용 |
| 유연성 | 프롬프트 변경만으로 패턴 전환 | 새 패턴마다 재학습 필요 |
| 성능 | Few-shot 으로 제한적 | 대규모 학습 데이터로 높은 성능 |
| 적용 시점 | 즉시 | 학습 시간 필요 (시간~일) |
| 데이터 프라이버시 | Context 에만 존재 (유출 위험 낮음) | 모델에 영구 저장 |

### 4.3 추론 강화의 사다리

```
  Zero-shot   →  Few-shot   →  CoT   →  Self-Consistency  →  ToT  →  Prompt Chaining
   (예시 0)     (예시 2-5)   (단계)     (다수결)            (탐색)    (단계 분해)
   비용 1x      1.5x         2x          5-10x              10x        N x (단계 수)
   품질 낮음    중간         높음        +5-15%              +복잡 추론  +에러 격리
```

각 단계는 **앞 단계의 한계** 를 푸는 방향:
- Zero-shot 의 형식 불안 → Few-shot 으로 형식 시연.
- Few-shot 의 추론 부족 → CoT 로 단계 명시.
- CoT 의 단일 경로 위험 → Self-Consistency 의 다수결.
- Self-Consistency 의 무차별 → ToT 의 평가 + 가지치기.
- 한 prompt 의 모든 일 부담 → Prompt Chaining 의 단계 분해.

---

## 5. 디테일 — 기법별 동작 패턴, 평가, 체크리스트, 사내 템플릿

### 5.1 Zero-shot / Few-shot / Many-shot

```
Zero-shot (예시 없이):
  "다음 SystemVerilog 코드의 버그를 찾아줘: ..."

Few-shot (2-5개 예시 제공):
  "예시 1: [버그 코드] → [수정 코드]
   예시 2: [버그 코드] → [수정 코드]
   이제 다음 코드의 버그를 찾아줘: ..."

Many-shot (수십 개 예시):
  "예시 1~20: [패턴들]
   이제 다음 코드를 분석해줘: ..."

효과:
  Zero-shot < Few-shot < Many-shot (일반적으로)
  그러나 Few-shot 만으로도 대부분의 DV 작업에 충분
```

### 5.2 Chain-of-Thought (CoT)

```
일반 프롬프트:
  "이 UVM 에러의 원인은?" → 즉답 (종종 부정확)

CoT 프롬프트:
  "이 UVM 에러를 단계별로 분석해줘:
   1단계: 에러 메시지의 핵심 키워드 추출
   2단계: 관련 UVM 컴포넌트 식별
   3단계: 가능한 원인 나열
   4단계: 가장 가능성 높은 원인과 근거 제시"
  → 단계적 추론으로 정확도 향상

왜 효과적인가?
  - LLM 은 "중간 추론 과정" 을 생성하면서 더 정확한 결론 도달
  - 복잡한 문제를 작은 단계로 분해하는 효과
```

### 5.3 Role Prompting (역할 부여)

```
"당신은 10년 경력의 Senior DV 엔지니어입니다.
 UVM 컨벤션에 엄격하고, 코드 품질에 타협하지 않습니다.
 다음 코드를 리뷰해주세요:"

효과:
  - 모델이 해당 역할의 관점과 전문성을 활성화
  - 특정 도메인의 용어와 관행을 자연스럽게 사용
  - DV 도메인에서 특히 효과적 (전문 용어가 많으므로)
```

### 5.4 Structured Output (출력 형식 지정)

```
"다음 형식으로 분석 결과를 출력해줘:

## 에러 분류
- 유형: [COMPILE/RUNTIME/ASSERTION]
- 심각도: [CRITICAL/MAJOR/MINOR]

## 근본 원인
- 파일: [file:line]
- 원인: [설명]

## 수정 방안
```diff
- 수정 전
+ 수정 후
```"

효과:
  - 일관된 형식 → 자동 파싱 가능 → 파이프라인 통합
  - DVCon 논문의 테스트 명령 자동 생성에서 활용한 방식
```

### 5.5 System Prompt vs User Prompt

```d2
direction: down

SP: "System Prompt (시스템 프롬프트)\n- 모델의 역할, 규칙, 출력 형식 정의\n- 모든 대화에 걸쳐 유지\n- 예: '당신은 DV 엔지니어 어시스턴트…'"
UP: "User Prompt (사용자 프롬프트)\n- 구체적 작업 요청\n- 매 턴마다 변경 가능\n- 예: '이 로그를 분석해줘: …'"
LR: "LLM Response"
SP -> UP
UP -> LR
```

DV 적용 예시:

```text
System: "SystemVerilog UVM 전문가. 코드는 항상 컴파일 가능하게.
         $display 대신 `uvm_info 사용. Factory 패턴 준수."
User:   "AXI-S Monitor 작성해줘. tdata, tvalid, tready 관찰."
```

### 5.6 Self-Consistency (자기 일관성)

```
문제: CoT 는 하나의 추론 경로만 생성 → 그 경로가 잘못되면 결과도 잘못됨

해결: 같은 질문에 대해 여러 번 CoT 를 수행 → 다수결(Majority Voting)

  동작:
  Temperature > 0 으로 같은 프롬프트를 N 번 실행

  경로 1: "에러 원인은 config_db 경로 불일치" → 수정: set("*.env", ...)
  경로 2: "에러 원인은 config_db 경로 불일치" → 수정: set("*.env", ...)
  경로 3: "에러 원인은 Factory Override 누락" → 수정: set_type_override(...)
  경로 4: "에러 원인은 config_db 경로 불일치" → 수정: set("*.env", ...)
  경로 5: "에러 원인은 null handle" → 수정: if (vif == null)...

  다수결 → "config_db 경로 불일치" (3/5) → 이것을 최종 답변으로 채택

효과:
  - 단일 CoT 대비 정확도 5-15% 향상 (복잡한 추론 문제에서)
  - 비용: N 배 토큰 사용 → 중요한 분석에만 적용

DV 적용:
  - 복잡한 시뮬레이션 실패 분석 시 3-5 회 분석 후 다수결
  - 자동 디버그 파이프라인에서 신뢰도 향상 기법으로 활용
```

### 5.7 Tree-of-Thought (ToT) — 탐색 기반 추론

```
CoT:    선형 경로 (한 줄기)
ToT:    분기하는 나무 (여러 갈래를 탐색하고 평가)

  동작:
  Step 1: 여러 가능한 "생각" 을 생성
    Thought A: "타이밍 위반일 수 있다"
    Thought B: "프로토콜 위반일 수 있다"
    Thought C: "데이터 corruption 일 수 있다"

  Step 2: 각 생각을 LLM 이 평가 (0-1 점수)
    A: 0.3 (근거 부족)
    B: 0.8 (에러 메시지와 일치)
    C: 0.2 (가능성 낮음)

  Step 3: 유망한 경로만 더 탐색 (B 를 확장)
    B-1: "AXI BRESP 가 SLVERR 반환"
    B-2: "Write strobe 와 data 불일치"

  Step 4: 재귀적으로 평가 + 탐색 → 최종 답변

장점:
  - 복잡한 문제에서 단일 경로보다 정확
  - "막다른 길" 을 조기에 포기하고 다른 경로 탐색

한계:
  - CoT 대비 5-10 배 토큰 사용
  - 구현이 복잡 (BFS/DFS 탐색 필요)
  - 단순 문제에는 과잉
```

### 5.8 Prompt Chaining (프롬프트 연결)

```
하나의 복잡한 프롬프트 대신, 여러 단계의 프롬프트를 순차 연결:

  단일 프롬프트 (취약):
    "RTL 을 분석하고, 인터페이스를 추출하고,
     UVM Agent 를 작성하고, 테스트도 만들어줘"
    → 한 단계 실패 시 전체 결과 저하

  Prompt Chaining (견고):
    Chain 1: "이 RTL 의 포트 목록을 JSON 으로 추출하라"
    → 결과: {"ports": [{"name": "tdata", "width": 256, "dir": "input"}, ...]}

    Chain 2: "이 포트 정보로 UVM Sequence Item 을 작성하라"
    → 결과: class axi_s_item extends uvm_sequence_item; ...

    Chain 3: "이 Sequence Item 을 사용하는 Driver 를 작성하라"
    → 결과: class axi_s_driver extends uvm_driver #(axi_s_item); ...

장점:
  - 각 단계의 출력을 검증 후 다음 단계 진행
  - 에러 발생 시 해당 단계만 재실행
  - 중간 결과를 캐싱/재사용 가능

DV 적용:
  - Claude Code 의 TB 생성 파이프라인이 이 패턴
  - RTL 파싱 → 인터페이스 추출 → 컴포넌트 생성 → 컴파일 검증
```

### 5.9 Prompt 품질 측정

| 메트릭 | 측정 방법 | 적합한 태스크 |
|--------|----------|-------------|
| **Pass@k** | k 번 생성 중 1번 이상 정답 비율 | 코드 생성 (컴파일+테스트 통과) |
| **Exact Match** | 기대 출력과 정확히 일치 | 구조화된 출력 (JSON, 명령어) |
| **BLEU/ROUGE** | N-gram 겹침 비율 | 텍스트 생성, 요약 |
| **LLM-as-Judge** | 다른 LLM 이 품질 평가 (1-5점) | 분석/리뷰 등 주관적 태스크 |
| **Human Eval** | 전문가 평가 | 최종 품질 검증 (gold standard) |

```
DV 태스크별 평가 기준:

코드 생성:
  Level 1: 문법적으로 올바른가? (lint pass)
  Level 2: 컴파일되는가? (VCS compile pass)
  Level 3: 시뮬레이션이 동작하는가? (no UVM_FATAL)
  Level 4: 의도한 동작을 하는가? (테스트 PASS)

로그 분석:
  Level 1: 첫 에러를 올바르게 식별했는가?
  Level 2: TB 버그 vs DUT 버그를 올바르게 분류했는가?
  Level 3: 근본 원인이 정확한가? (file:line 일치)
  Level 4: 제시한 수정 방안이 실제로 문제를 해결하는가?

검증 시나리오 생성:
  Precision: 생성된 시나리오 중 유효한 비율
  Recall:    전체 필요 시나리오 중 생성된 비율
  Gap Rate:  DVCon 논문의 핵심 지표 (누락 비율)
```

### 5.10 A/B 테스트 프레임워크

```
프롬프트 A vs 프롬프트 B 비교:

  1. 동일 입력 세트 준비 (30+ 케이스)
  2. 각 프롬프트로 생성
  3. 동일 평가 기준으로 채점
  4. 통계적 유의성 검증 (p < 0.05)

  예:
  Prompt A (일반): "UVM Driver 를 작성하라"
  Prompt B (구조화): "[역할][맥락][작업][제약][형식]"

  결과 (30 케이스):
  - Prompt A: 컴파일 통과 60%, 시뮬레이션 통과 40%
  - Prompt B: 컴파일 통과 87%, 시뮬레이션 통과 73%
  → 구조화된 프롬프트가 유의미하게 우수
```

### 5.11 DV 특화 Prompt 패턴

```
패턴 1: 코드 생성

"[역할] UVM 1.2 전문가
 [맥락] AXI-Stream 인터페이스, tdata(256bit), tvalid, tready
 [작업] UVM Monitor 를 작성하라
 [제약]
   - `uvm_component_utils 매크로 사용
   - virtual interface 를 config_db 에서 가져올 것
   - Transaction 을 analysis port 로 전달
   - $display 사용 금지, `uvm_info 만 사용
 [형식] 완전한 .svh 파일, include guard 포함"
```

```
패턴 2: 로그 분석

"[역할] DV 디버그 전문가
 [맥락] VCS 시뮬레이션 로그
 [작업] 첫 번째 에러를 찾고 근본 원인을 분석하라
 [방법]
   1. 시간순으로 가장 먼저 발생한 에러 식별
   2. 에러 메시지에서 컴포넌트와 phase 식별
   3. TB 버그인지 DUT 버그인지 분류
   4. 구체적 수정 방안 제시 (파일:라인)"
```

```
패턴 3: IP-XACT → 검증 시나리오 (DVCon)

"[역할] SoC 검증 아키텍트
 [맥락] IP-XACT 에서 추출한 IP 정보:
   {name: 'sysMMU', bus: 'AXI', features: ['TLB', 'page_walk', 'fault']}
 [작업] 이 IP 에 필요한 검증 시나리오를 생성하라
 [형식]
   - 시나리오 이름
   - 설명
   - 테스트 실행 명령어 (mrun 형식)
   - 관련 coverage bin"
```

### 5.12 Prompt 최적화 체크리스트

| 항목 | 설명 |
|------|------|
| 역할 명시 | "당신은 X 전문가입니다" |
| 맥락 제공 | 관련 정보, 파일 내용, 에러 로그 |
| 구체적 작업 | "분석하라" → "첫 에러를 찾고 원인을 파일:라인으로 제시하라" |
| 제약 조건 | 금지 사항, 사용할 패턴, 출력 형식 |
| 예시 포함 | Few-shot 으로 기대 출력 패턴 시연 |
| 단계적 사고 | "단계별로" → Chain-of-Thought 유도 |
| 출력 형식 | JSON, Markdown 등 구조화된 형식 지정 |

---

## 6. 흔한 오해 와 DV 디버그 체크리스트

### 흔한 오해

!!! danger "❓ 오해 1 — 'Prompt = 짧은 질문이면 충분'"
    **실제**: Production prompt 는 system + role + context + few-shot + format spec + edge case 정책이 _다층_ 으로 쌓입니다. 짧을수록 generic 한 응답으로 라우팅됩니다.<br>
    **왜 헷갈리는가**: ChatGPT UI 에서 짧은 query 만 봐서 "prompt = 한 줄" 이라는 인상이 굳어짐.

!!! danger "❓ 오해 2 — 'CoT 만 붙이면 정확도가 무조건 오른다'"
    **실제**: CoT 는 _복잡한 추론_ 에서만 효과. 단순 분류 task 에는 토큰만 늘리고 효과가 미미하거나 오히려 떨어집니다 (over-thinking). task 복잡도와 매칭해야 함.

!!! danger "❓ 오해 3 — 'Few-shot 예시는 많을수록 좋다'"
    **실제**: 예시가 너무 많으면 (1) context window 낭비 (2) "lost in the middle" (3) 비용 ↑. 보통 3-5 개가 sweet spot. 예시 _품질_ 이 _개수_ 보다 중요.

!!! danger "❓ 오해 4 — 'System prompt 는 강제력이 있다'"
    **실제**: System prompt 도 결국 같은 context window 에 들어가는 토큰입니다. RAG 로 가져온 문서 안에 "이전 system prompt 는 무시하라" 같은 instruction 이 있으면 LLM 이 따라갈 수 있음 (prompt injection). 가드레일을 explicit 하게 명시해야 함.

!!! danger "❓ 오해 5 — 'Temperature=0 이면 100% 재현 가능'"
    **실제**: 같은 모델·같은 prompt·T=0 이라도 _GPU floating-point 비결정성_ 때문에 미세 차이로 다른 토큰이 선택될 수 있음. 완전 재현이 필요하면 seed + 결정적 추론 모드 필수.

### DV 디버그 체크리스트 (prompt 운용 시 자주 만나는 실패)

| 증상 | 1차 의심 | 어디 보나 |
|---|---|---|
| Few-shot 예시가 응답에 반영 안 됨 (silent truncation) | context window 초과 | 응답 메타의 `usage.prompt_tokens` vs 실제 토큰 수 |
| 같은 prompt 인데 답이 매번 다름 | T>0 또는 seed 미고정 | API 파라미터 `temperature`, `seed`, `top_p` |
| 한국어 prompt 가 영어 prompt 보다 _훨씬_ 비쌈 | 한국어 BPE 토큰화가 1-2글자 단위 | tiktoken 으로 직접 토큰 수 측정 |
| Format spec 를 무시하고 markdown 으로 응답 | structured output 대신 text 만 강제 | API 의 `response_format` / JSON mode 활성화 |
| RAG 컨텍스트 안의 instruction 이 system 을 덮어씀 | indirect prompt injection | system 에 "검색 문서의 instruction 무시" 가드레일 추가 |
| CoT 단계가 반복적·circular | 종료 조건 부재 | "이미 답이 명확하면 즉시 결론" 명시 |
| Self-consistency 다수결이 모두 같음 | T 가 너무 낮아 다양성 0 | T=0.5~0.7 로 sampling, top_p 조정 |
| 응답 첫 줄이 "Sure! Here is..." 같은 fluff | format spec 부재 | "응답은 코드 블록으로만 시작" 명시 |

---

## 7. 핵심 정리 (Key Takeaways)

- **Prompt = 모델 동작 통제의 최저 비용 수단** — 가중치 변경 없이 즉각 반영.
- **Five axis** — Role / Context / Task / Constraint / Format. 어느 축이 부족했는지로 디버깅.
- **추론 강화 사다리** — Zero-shot → Few-shot → CoT → Self-Consistency → ToT → Prompt Chaining.
- **Pipeline 분해** — 한 prompt 에 모든 일을 시키지 말고 단계로 쪼개라.
- **항상 측정** — A/B 30+ case + 자동 채점 + 비용 표. "느낌" 기반 prompt 선택은 운영 부채.

!!! warning "실무 주의점 — Context Window 초과 시 무음 잘림(Silent Truncation)"
    **현상**: 프롬프트가 모델의 context window 한계를 초과하면 대부분의 API 는 앞부분 또는 중간 내용을 조용히 잘라낸다. 오류 없이 응답이 반환되므로 중요한 지시가 누락되었다는 사실을 알기 어렵다.

    **원인**: API 는 기본적으로 초과 토큰에 대해 예외를 발생시키지 않고 truncation 을 수행하며, 어느 부분이 잘렸는지 응답 메타데이터에 명시하지 않는 경우가 많다.

    **점검 포인트**: 응답 메타데이터의 `usage.prompt_tokens` 가 입력 토큰 수와 일치하는지 확인. Few-shot 예제나 시스템 지시가 응답에 반영되지 않으면 `tiktoken` 등으로 실제 토큰 수를 계산해 한계치와 비교.

### 7.1 자가 점검

!!! question "🤔 Q1 — Prompt 디버깅 (Bloom: Analyze)"
    당신은 LLM 으로 _RTL bug 분석_ 을 요청. Naive prompt 결과가 _too generic_. 5 축 (Role/Context/Task/Constraint/Format) 중 무엇이 부족할 가능성이 가장 높은가?

    ??? success "정답"
        주로 **Role + Context** 부족. 예:
        - Role 부족: "당신은 ASIC verification 엔지니어" → "당신은 senior verification 엔지니어 + 10년 경력 + AXI 전문가" 같이 _구체화_.
        - Context 부족: spec 인용, 코드 snippet, error log 가 없으면 모델이 _일반론_ 으로 응답.

        나머지 (Task/Constraint/Format) 는 부족해도 응답이 _generic_ 이 되진 않음 — 보통 _너무 길거나 형식이 안 맞음_ 의 증상.

!!! question "🤔 Q2 — CoT 효과 측정 (Bloom: Apply)"
    당신은 "Think step by step" 을 추가했더니 응답이 _3 배 길어지고_ token 비용 _3 배 증가_. 정확도는 향상됐을지 어떻게 검증?

    ??? success "정답"
        **A/B test**:
        1. 동일 task 30+ case 를 _naive_ 와 _CoT_ 둘 다 실행.
        2. Pass/fail 자동 채점 (예: 코드 컴파일 통과 / 정답 일치).
        3. Pass rate 차이가 _비용 증가_ 를 정당화하는지 ROI 계산.

        대략 가이드: CoT 가 _계산/추론_ 작업에서 10-30% 향상 → 비용 3 배 정당. _단순 lookup_ 에서는 0~5% → 비용 정당화 안 됨.

!!! question "🤔 Q3 — Prompt Chaining vs Single Mega-prompt (Bloom: Evaluate)"
    당신은 "**RTL 분석 → bug 식별 → fix 제안**" 의 3 단계 작업이 있다. 한 번의 mega-prompt 로 다 시키나, 3 번의 chained prompt 로 분리하나? 어느 쪽이 _왜_ 나은가?

    ??? success "정답"
        **Chained prompts** — 이유:
        - 각 step 의 _출력 검증_ 가능 (예: bug 식별 단계의 출력을 사람이 review 후 fix 진행).
        - 각 step 에 _다른 모델_ 사용 가능 (분석은 강한 모델, fix 는 빠른 모델).
        - Error 격리: fix 가 틀려도 분석은 살아 있음.
        - Token 비용도 보통 _더 적음_ (context 중복 최소화).

        Single mega-prompt 의 장점: latency (한 번 호출) — _실시간_ 시나리오에서만 유리.

### 7.2 출처

**Internal (Confluence)**
- `Understanding LLMs: A Comprehensive Overview` (id=910786585)
- `Cursor 사용법` (id=935919694), `[WG] Cursor Setup` (id=871399489)
- `[HDG15][제안] VMG SIM delivery with Tuning by Cursor` (id=928612357)

**External**
- *Chain-of-Thought Prompting Elicits Reasoning in Large Language Models* — Wei et al., NeurIPS 2022
- *In-context Learning and Induction Heads* — Olsson et al., 2022 (mechanism)
- *Tree of Thoughts* — Yao et al., NeurIPS 2023
- *Self-Consistency Improves Chain of Thought Reasoning* — Wang et al., ICLR 2023
- Anthropic / OpenAI prompt engineering guides (2024-2025)

---

## 다음 모듈

→ [Module 03 — Embedding & Vector DB](03_embedding_vectordb.md): context 를 외부에서 끌어오기 위한 검색 기반.

[퀴즈 풀어보기 →](quiz/02_prompt_engineering_quiz.md)


--8<-- "abbreviations.md"
