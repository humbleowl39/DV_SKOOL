# Module 02 — Prompt Engineering & In-Context Learning

## 학습 목표 (Learning Objectives)

이 모듈을 마치면:

1. (Remember) Zero-shot / Few-shot / CoT / Self-Consistency 의 정의를 구분할 수 있다.
2. (Understand) Few-shot 예시가 왜 모델 가중치 변경 없이 동작을 바꿀 수 있는지 설명할 수 있다.
3. (Apply) 분류·요약·코드 생성 task 각각에 적합한 prompt 패턴을 작성할 수 있다.
4. (Analyze) 동일 task 의 prompt 두 개를 정확도 / token cost / robustness 로 비교 분석할 수 있다.
5. (Evaluate) Prompt vs Fine-tune 결정을 비용·일관성·통제 측면에서 평가할 수 있다.

## 선수 지식 (Prerequisites)

- Module 01 — LLM Fundamentals (자기회귀 생성, context window)
- 기본 NLP 용어 (token, classification, summarization)

## 왜 이 모듈이 중요한가 (Why it matters)

LLM 활용에서 가장 큰 ROI 는 **모델 변경 없이 입력만으로 출력을 통제하는 능력**이다. 모든 RAG / Agent 시스템의 마지막 단은 결국 prompt 다. 이 모듈은 학습자가 "왜 이 prompt 가 더 잘 동작하는지" 를 가설 → 실험 → 검증 사이클로 다룰 수 있게 만든다.

---

!!! tip "💡 이해를 위한 비유"
    **Prompt Engineering** ≈ **신입 직원 onboarding instruction — 문맥과 예시를 어떻게 주느냐로 결과가 결정**

    같은 LLM 이라도 system prompt + few-shot 예시 + 명시적 형식 지시에 따라 결과가 다름. 가중치 변경 없이 행동을 통제.

---

## 핵심 개념
**Prompt Engineering = 모델 가중치 변경 없이, 입력(프롬프트)만으로 LLM의 출력을 원하는 방향으로 유도하는 기법. 가장 비용 효율적인 LLM 활용법이며, RAG/Agent의 기반.**

---

## 왜 Prompt가 중요한가?

```
같은 모델, 다른 프롬프트 → 완전히 다른 결과:

  나쁜 프롬프트:
    "UVM 테스트벤치 만들어줘"
    → 일반적이고 부정확한 코드

  좋은 프롬프트:
    "AXI-Stream 인터페이스를 가진 MMU IP의 UVM Agent를 작성해줘.
     Driver는 tdata, tvalid, tready만 처리하고,
     Monitor는 Transaction을 수집하여 analysis port로 전달.
     SystemVerilog UVM 1.2 스타일을 따를 것."
    → 구체적이고 사용 가능한 코드
```

---

## 핵심 프롬프트 기법

### 1. Zero-shot / Few-shot / Many-shot

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
  그러나 Few-shot만으로도 대부분의 DV 작업에 충분
```

### 2. Chain-of-Thought (CoT)

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
  - LLM은 "중간 추론 과정"을 생성하면서 더 정확한 결론 도달
  - 복잡한 문제를 작은 단계로 분해하는 효과
```

### 3. Role Prompting (역할 부여)

```
"당신은 10년 경력의 Senior DV 엔지니어입니다.
 UVM 컨벤션에 엄격하고, 코드 품질에 타협하지 않습니다.
 다음 코드를 리뷰해주세요:"

효과:
  - 모델이 해당 역할의 관점과 전문성을 활성화
  - 특정 도메인의 용어와 관행을 자연스럽게 사용
  - DV 도메인에서 특히 효과적 (전문 용어가 많으므로)
```

### 4. Structured Output (출력 형식 지정)

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

---

## In-Context Learning (ICL)

### ICL이란?

```
Fine-tuning 없이, 프롬프트에 예시를 포함시키는 것만으로
모델이 새로운 패턴을 학습하는 현상

예시:
  프롬프트:
    "IP-XACT에서 추출한 정보로 검증 시나리오를 생성하는 예시:

     입력: {ip: 'sysMMU', feature: 'TLB invalidation'}
     출력: mrun test --test_name tlb_invalidate_all --sys_name mmu

     입력: {ip: 'sysMMU', feature: 'page fault handling'}
     출력: mrun test --test_name page_fault_recovery --sys_name mmu

     입력: {ip: 'DCMAC', feature: 'packet CRC check'}
     출력: "

  → 모델이 패턴을 학습하고 새 입력에 적용
  → DVCon 논문의 "LLM-Based Test Generation"이 이 방식
```

### ICL vs Fine-tuning

| 항목 | In-Context Learning | Fine-tuning |
|------|-------------------|-------------|
| 모델 변경 | 없음 | 가중치 업데이트 |
| 비용 | 추론 비용만 | 학습 비용 + 추론 비용 |
| 유연성 | 프롬프트 변경만으로 패턴 전환 | 새 패턴마다 재학습 필요 |
| 성능 | Few-shot으로 제한적 | 대규모 학습 데이터로 높은 성능 |
| 적용 시점 | 즉시 | 학습 시간 필요 (시간~일) |
| 데이터 프라이버시 | Context에만 존재 (유출 위험 낮음) | 모델에 영구 저장 |

---

## System Prompt vs User Prompt

```
+--------------------------------------------------+
|  System Prompt (시스템 프롬프트)                   |
|  - 모델의 역할, 규칙, 출력 형식 정의              |
|  - 모든 대화에 걸쳐 유지                          |
|  - 예: "당신은 DV 엔지니어 어시스턴트입니다..."    |
+--------------------------------------------------+
         |
+--------------------------------------------------+
|  User Prompt (사용자 프롬프트)                     |
|  - 구체적 작업 요청                               |
|  - 매 턴마다 변경 가능                            |
|  - 예: "이 로그를 분석해줘: ..."                  |
+--------------------------------------------------+
         |
+--------------------------------------------------+
|  LLM Response                                     |
+--------------------------------------------------+

DV 적용 예시:
  System: "SystemVerilog UVM 전문가. 코드는 항상 컴파일 가능하게.
           $display 대신 `uvm_info 사용. Factory 패턴 준수."
  User:   "AXI-S Monitor 작성해줘. tdata, tvalid, tready 관찰."
```

---

## 고급 추론 기법

### 5. Self-Consistency (자기 일관성)

```
문제: CoT는 하나의 추론 경로만 생성 → 그 경로가 잘못되면 결과도 잘못됨

해결: 같은 질문에 대해 여러 번 CoT를 수행 → 다수결(Majority Voting)

  동작:
  Temperature > 0으로 같은 프롬프트를 N번 실행

  경로 1: "에러 원인은 config_db 경로 불일치" → 수정: set("*.env", ...)
  경로 2: "에러 원인은 config_db 경로 불일치" → 수정: set("*.env", ...)  
  경로 3: "에러 원인은 Factory Override 누락" → 수정: set_type_override(...)
  경로 4: "에러 원인은 config_db 경로 불일치" → 수정: set("*.env", ...)
  경로 5: "에러 원인은 null handle" → 수정: if (vif == null)...

  다수결 → "config_db 경로 불일치" (3/5) → 이것을 최종 답변으로 채택

효과:
  - 단일 CoT 대비 정확도 5-15% 향상 (복잡한 추론 문제에서)
  - 비용: N배 토큰 사용 → 중요한 분석에만 적용

DV 적용:
  - 복잡한 시뮬레이션 실패 분석 시 3-5회 분석 후 다수결
  - 자동 디버그 파이프라인에서 신뢰도 향상 기법으로 활용
```

### 6. Tree-of-Thought (ToT) — 탐색 기반 추론

```
CoT:    선형 경로 (한 줄기)
ToT:    분기하는 나무 (여러 갈래를 탐색하고 평가)

  동작:
  Step 1: 여러 가능한 "생각"을 생성
    Thought A: "타이밍 위반일 수 있다"
    Thought B: "프로토콜 위반일 수 있다"
    Thought C: "데이터 corruption일 수 있다"

  Step 2: 각 생각을 LLM이 평가 (0-1 점수)
    A: 0.3 (근거 부족)
    B: 0.8 (에러 메시지와 일치)
    C: 0.2 (가능성 낮음)

  Step 3: 유망한 경로만 더 탐색 (B를 확장)
    B-1: "AXI BRESP가 SLVERR 반환"
    B-2: "Write strobe와 data 불일치"

  Step 4: 재귀적으로 평가 + 탐색 → 최종 답변

장점:
  - 복잡한 문제에서 단일 경로보다 정확
  - "막다른 길"을 조기에 포기하고 다른 경로 탐색

한계:
  - CoT 대비 5-10배 토큰 사용
  - 구현이 복잡 (BFS/DFS 탐색 필요)
  - 단순 문제에는 과잉
```

### 7. Prompt Chaining (프롬프트 연결)

```
하나의 복잡한 프롬프트 대신, 여러 단계의 프롬프트를 순차 연결:

  단일 프롬프트 (취약):
    "RTL을 분석하고, 인터페이스를 추출하고,
     UVM Agent를 작성하고, 테스트도 만들어줘"
    → 한 단계 실패 시 전체 결과 저하

  Prompt Chaining (견고):
    Chain 1: "이 RTL의 포트 목록을 JSON으로 추출하라"
    → 결과: {"ports": [{"name": "tdata", "width": 256, "dir": "input"}, ...]}

    Chain 2: "이 포트 정보로 UVM Sequence Item을 작성하라"
    → 결과: class axi_s_item extends uvm_sequence_item; ...

    Chain 3: "이 Sequence Item을 사용하는 Driver를 작성하라"
    → 결과: class axi_s_driver extends uvm_driver #(axi_s_item); ...

장점:
  - 각 단계의 출력을 검증 후 다음 단계 진행
  - 에러 발생 시 해당 단계만 재실행
  - 중간 결과를 캐싱/재사용 가능

DV 적용:
  - Claude Code의 TB 생성 파이프라인이 이 패턴
  - RTL 파싱 → 인터페이스 추출 → 컴포넌트 생성 → 컴파일 검증
```

---

## Prompt 품질 측정

### 정량적 평가 방법

| 메트릭 | 측정 방법 | 적합한 태스크 |
|--------|----------|-------------|
| **Pass@k** | k번 생성 중 1번 이상 정답 비율 | 코드 생성 (컴파일+테스트 통과) |
| **Exact Match** | 기대 출력과 정확히 일치 | 구조화된 출력 (JSON, 명령어) |
| **BLEU/ROUGE** | N-gram 겹침 비율 | 텍스트 생성, 요약 |
| **LLM-as-Judge** | 다른 LLM이 품질 평가 (1-5점) | 분석/리뷰 등 주관적 태스크 |
| **Human Eval** | 전문가 평가 | 최종 품질 검증 (gold standard) |

### DV 태스크별 평가 기준

```
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

### A/B 테스트 프레임워크

```
프롬프트 A vs 프롬프트 B 비교:

  1. 동일 입력 세트 준비 (30+ 케이스)
  2. 각 프롬프트로 생성
  3. 동일 평가 기준으로 채점
  4. 통계적 유의성 검증 (p < 0.05)

  예:
  Prompt A (일반): "UVM Driver를 작성하라"
  Prompt B (구조화): "[역할][맥락][작업][제약][형식]"

  결과 (30 케이스):
  - Prompt A: 컴파일 통과 60%, 시뮬레이션 통과 40%
  - Prompt B: 컴파일 통과 87%, 시뮬레이션 통과 73%
  → 구조화된 프롬프트가 유의미하게 우수
```

---

## DV 특화 Prompt 패턴

### 패턴 1: 코드 생성

```
"[역할] UVM 1.2 전문가
 [맥락] AXI-Stream 인터페이스, tdata(256bit), tvalid, tready
 [작업] UVM Monitor를 작성하라
 [제약]
   - `uvm_component_utils 매크로 사용
   - virtual interface를 config_db에서 가져올 것
   - Transaction을 analysis port로 전달
   - $display 사용 금지, `uvm_info만 사용
 [형식] 완전한 .svh 파일, include guard 포함"
```

### 패턴 2: 로그 분석

```
"[역할] DV 디버그 전문가
 [맥락] VCS 시뮬레이션 로그
 [작업] 첫 번째 에러를 찾고 근본 원인을 분석하라
 [방법]
   1. 시간순으로 가장 먼저 발생한 에러 식별
   2. 에러 메시지에서 컴포넌트와 phase 식별
   3. TB 버그인지 DUT 버그인지 분류
   4. 구체적 수정 방안 제시 (파일:라인)"
```

### 패턴 3: IP-XACT → 검증 시나리오 (DVCon)

```
"[역할] SoC 검증 아키텍트
 [맥락] IP-XACT에서 추출한 IP 정보:
   {name: 'sysMMU', bus: 'AXI', features: ['TLB', 'page_walk', 'fault']}
 [작업] 이 IP에 필요한 검증 시나리오를 생성하라
 [형식]
   - 시나리오 이름
   - 설명
   - 테스트 실행 명령어 (mrun 형식)
   - 관련 coverage bin"
```

---

## Prompt 최적화 체크리스트

| 항목 | 설명 |
|------|------|
| 역할 명시 | "당신은 X 전문가입니다" |
| 맥락 제공 | 관련 정보, 파일 내용, 에러 로그 |
| 구체적 작업 | "분석하라" → "첫 에러를 찾고 원인을 파일:라인으로 제시하라" |
| 제약 조건 | 금지 사항, 사용할 패턴, 출력 형식 |
| 예시 포함 | Few-shot으로 기대 출력 패턴 시연 |
| 단계적 사고 | "단계별로" → Chain-of-Thought 유도 |
| 출력 형식 | JSON, Markdown 등 구조화된 형식 지정 |

---

## Q&A

**Q: Prompt Engineering이 왜 중요한가?**
> "LLM의 출력 품질은 프롬프트에 크게 의존한다. 같은 모델이라도 프롬프트에 역할, 맥락, 제약, 형식을 명시하면 전문가 수준의 출력을, 그렇지 않으면 일반적이고 부정확한 출력을 생성한다. Fine-tuning 없이도 프롬프트만으로 80% 이상의 성능 향상이 가능하며, 비용과 유연성 면에서 가장 효율적인 LLM 활용법이다."

**Q: DV 도메인에서 어떤 Prompt 기법을 사용했나?**
> "DVCon 논문에서 세 가지를 활용했다: (1) Few-shot ICL — IP-XACT 데이터 → 검증 시나리오 매핑 패턴을 예시로 제공. (2) Structured Output — 테스트 명령어와 V-Plan bin을 일관된 JSON 형식으로 출력하여 자동 파싱. (3) Role Prompting — SoC 검증 아키텍트 역할을 부여하여 도메인 특화 추론을 유도."

**Q: Self-Consistency와 CoT의 차이는?**
> "CoT는 단일 추론 경로를 따르지만, Self-Consistency는 같은 문제에 대해 여러 CoT를 병렬 생성하고 다수결로 최종 답을 선택한다. 비유하면 CoT는 한 명의 전문가 의견, Self-Consistency는 위원회 투표다. 비용은 N배이지만 복잡한 추론에서 5-15% 정확도 향상을 얻는다. DV에서는 자동 디버그 파이프라인에서 신뢰도를 높이는 데 활용할 수 있다."

**Q: Prompt Chaining은 왜 단일 프롬프트보다 효과적인가?**
> "세 가지 이유: (1) 에러 격리 — 한 단계 실패 시 해당 단계만 재실행, 전체 재생성 불필요. (2) 중간 검증 — 각 단계 출력을 확인하고 다음 단계 진행, 오류 전파 방지. (3) 복잡도 분산 — 하나의 어려운 문제를 여러 쉬운 문제로 분해하여 각각의 정확도를 높인다. DAC 논문의 TB 자동화 파이프라인(RTL 파싱→인터페이스 추출→코드 생성→컴파일 검증)이 이 패턴이다."

---

!!! danger "❓ 흔한 오해"
    **오해**: Prompt = 짧은 질문이면 충분

    **실제**: Production prompt 는 system prompt + role + context + few-shot + format spec + edge case + ToT 등 다층. 짧을수록 generic.

    **왜 헷갈리는가**: ChatGPT UI 에서 짧은 query 만 봐서 "prompt = 한 줄" 로 단순화.

!!! warning "실무 주의점 — Context Window 초과 시 무음 잘림(Silent Truncation)"
    **현상**: 프롬프트가 모델의 context window 한계를 초과하면 대부분의 API는 앞부분 또는 중간 내용을 조용히 잘라낸다. 오류 없이 응답이 반환되므로 중요한 지시가 누락되었다는 사실을 알기 어렵다.

    **원인**: API는 기본적으로 초과 토큰에 대해 예외를 발생시키지 않고 truncation을 수행하며, 어느 부분이 잘렸는지 응답 메타데이터에 명시하지 않는 경우가 많다.

    **점검 포인트**: 응답 메타데이터의 `usage.prompt_tokens`가 입력 토큰 수와 일치하는지 확인. Few-shot 예제나 시스템 지시가 응답에 반영되지 않으면 `tiktoken` 등으로 실제 토큰 수를 계산해 한계치와 비교.

## 핵심 정리 (Key Takeaways)

- **Prompt = 모델 동작 통제의 최저 비용 수단** — 가중치 변경 없이 즉각 반영.
- **Few-shot** — 형식·스타일·라벨 분포를 예시로 전달.
- **CoT (Chain-of-Thought)** — 모델이 중간 추론 단계를 출력하면 정확도가 오른다.
- **Self-Consistency** — 같은 prompt 를 여러 번 샘플링 → 다수결로 robust.
- **Pipeline 분해** — 한 prompt 에 모든 일을 시키지 말고 단계로 쪼개라.

## 다음 단계 (Next Steps)

- 다음 모듈: [Embedding & Vector DB →](../03_embedding_vectordb/) — context 를 외부에서 끌어오기 위한 검색 기반.
- 퀴즈: [Module 02 Quiz](../quiz/02_prompt_engineering_quiz/) — Few-shot, CoT, prompt 비교 5문항.
- 실습: 자기 task 1개에 zero-shot / few-shot / CoT / self-consistency 4가지를 모두 적용해 정확도와 토큰 비용을 표로 정리한다.

<div class="chapter-nav">
  <a class="nav-prev" href="../01_llm_fundamentals/">
    <div class="nav-label">◀ 이전</div>
    <div class="nav-title">LLM 기본 구조</div>
  </a>
  <a class="nav-next" href="../03_embedding_vectordb/">
    <div class="nav-label">다음 ▶</div>
    <div class="nav-title">Embedding & Vector DB (FAISS)</div>
  </a>
</div>
