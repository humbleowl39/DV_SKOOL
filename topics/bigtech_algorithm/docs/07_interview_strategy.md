# Module 07 — Interview Strategy

<!-- DV-SKOOL-CH-CTX:start -->
<div class="chapter-context" data-cat="applied">
  <a class="chapter-back" href="../">
    <span class="chapter-back-arrow">←</span>
    <span class="chapter-back-icon">📐</span>
    <span class="chapter-back-text">BigTech Algorithm</span>
  </a>
  <span class="chapter-divider">›</span>
  <span class="chapter-marker">Module 07</span>
</div>
<!-- DV-SKOOL-CH-CTX:end -->

<!-- DV-SKOOL-CH-TOC:start -->
<div class="page-toc">
  <span class="page-toc-label">목차</span>
  <a class="page-toc-link" href="#1-why-care-이-모듈이-왜-필요한가">1. Why care?</a>
  <a class="page-toc-link" href="#2-intuition-비유와-한-장-그림">2. Intuition</a>
  <a class="page-toc-link" href="#3-작은-예-한-문제-two-sum-를-45-분-타임라인에-올려보기">3. 작은 예 — Two Sum 45 분 시뮬레이션</a>
  <a class="page-toc-link" href="#4-일반화-4-축-평가-와-패턴-식별">4. 일반화</a>
  <a class="page-toc-link" href="#5-디테일-타임라인-clarify-edge-case-템플릿-16-문제-로드맵">5. 디테일</a>
  <a class="page-toc-link" href="#6-흔한-오해-와-디버그-체크리스트">6. 흔한 오해 + 디버그</a>
  <a class="page-toc-link" href="#7-핵심-정리-key-takeaways">7. 핵심 정리</a>
</div>
<!-- DV-SKOOL-CH-TOC:end -->

!!! objective "학습 목표"
    이 모듈을 마치면:

    - **Define** 빅테크 코딩 인터뷰 45 분의 표준 타임라인 5 단계를 적을 수 있다.
    - **Explain** 면접관이 평가하는 4 축 (Correctness, Complexity, Code Quality, Communication) 을 설명할 수 있다.
    - **Apply** 한 문제를 받아 5 분 내에 입력→패턴→복잡도→approach 까지 구두로 구성할 수 있다.
    - **Analyze** 자기 모의 면접 녹음을 4 축 기준으로 분석할 수 있다.
    - **Evaluate** "다 못 풀어도 통과하는 답안" 과 "다 풀어도 떨어지는 답안" 을 비교 평가할 수 있다.

!!! info "사전 지식"
    - Module 01–06 (Big-O, Hash Map, Two Pointers, Stack/BS, Tree/BFS-DFS, DP)
    - 모의 면접 1 회 이상 경험 (없으면 이 모듈을 마치고 진행 권장)

---

## 1. Why care? — 이 모듈이 왜 필요한가

알고리즘 실력 ≠ 면접 통과. **시간 관리 + 의사소통 + 엣지케이스 인지** 가 같이 필요합니다. Module 01~06 의 도구를 _45 분 안에_ 작동시키는 메타-스킬이 없으면, 다 풀어도 떨어지고 다 못 풀어도 통과하는 역설이 발생합니다.

이 모듈을 건너뛰면 _연습 문제는 풀리는데 면접에서만 막히는_ 패턴에서 벗어나기 어렵습니다. 반대로 _4 축 평가_ (Correctness, Complexity, Code Quality, Communication) 를 의식하며 풀이하면, _녹음한 모의 면접을 자기 채점_ 할 수 있게 되어 학습 속도가 크게 빨라집니다.

---

## 2. Intuition — 비유와 한 장 그림

!!! tip "💡 한 줄 비유"
    **면접 = 사고 과정 평가** ≈ **요리 시연** — _완성된 요리_ 보다 _재료 손질, 순서, 위생, 설명_ 이 더 큰 비중. 다 끓였는데 손도 안 씻고 침묵으로 끓였다면 위생 점수가 0 이라 탈락.<br>
    **45 분** = 5 코스 식사 — clarify (애피타이저), edge case (수프), approach (메인 1), code (메인 2), test (디저트). 한 코스라도 빠지면 손님(면접관) 이 불만족.

### 한 장 그림 — 4 축 평가와 시간 분배

```
   45 분 면접의 시간/평가 매트릭스
   ─────────────────────────────────────────────────────────────────
                                                               
      0 분 ────► 5 분 ────► 10 분 ────► 30 분 ────► 40 분 ────► 45 분
      │           │           │            │            │            │
      ▼           ▼           ▼            ▼            ▼            ▼
   Clarify    Edge case   Approach +     Coding       Test +     Q & A
              Examples    Complexity                  Verify      
                                                                  
   평가 4 축이 각 시간 슬롯에 _서로 다른 가중치_ 로 적용:        
                                                                
   Correctness    ──────────────────●────────●────────────►   
   Complexity     ────────●────────●─────────────────●────►   
   Code Quality   ──────────────────────────●──●──────────►   
   Communication ●────────●─────────●───────●──●──●────────►   
                                                              
   ⭐ Communication 은 _전 구간_ 에서 평가. 침묵하면 다 풀어도 감점.
```

### 왜 이렇게 설계됐는가 — Design rationale

빅테크의 코딩 면접은 _자동 채점이 아닙니다_. 면접관은 _사고 과정의 명확성_ 과 _협업 가능성_ 을 보고, "이 사람과 같이 일할 수 있겠는가" 를 결정합니다. 그래서 _완성된 코드_ 보다 _문제 분해 → 명세 합의 → 후보 비교 → 코드 → 검증_ 의 _과정_ 이 점수의 핵심.

또한 45 분이라는 시간 제약은 _가장 중요한 일에 시간 배정_ 하는 능력을 측정합니다. clarify 에 너무 많이 쓰면 코드를 못 끝내고, 코드에 너무 많이 쓰면 verify 를 못 합니다 — _4 축의 균형_ 이 곧 면접 점수.

---

## 3. 작은 예 — 한 문제 (Two Sum) 를 45 분 타임라인에 올려보기

면접관: "정수 배열 nums 와 target 이 주어졌을 때, nums[i] + nums[j] = target 이 되는 두 인덱스 i, j 를 반환하세요."

### 단계별 시뮬레이션

```
   ┌─ 0–5 분: Clarify ──────────────────────────────────────┐
   │  나: "정리하면, 합이 target 인 두 인덱스 한 쌍 반환이요.    │
   │       확인할 게 있는데:                                   │
   │       1. 입력은 정렬됐나요?                                │
   │       2. 음수 값 가능한가요?                               │
   │       3. 답이 항상 존재한다고 가정해도 되나요?              │
   │       4. 같은 인덱스 두 번 사용은 금지죠?                   │
   │       5. 입력 크기 범위 어떻게 되나요?"                     │
   │                                                            │
   │  면접관: "정렬 안 됨, 음수 가능, 답 정확히 1 개, 같은 인덱스 │
   │           불가, n ≤ 10⁵."                                 │
   └────────────────────────────────────────────────────────────┘

   ┌─ 5–10 분: Edge case + Approach ─────────────────────────┐
   │  나: "엣지 케이스 적어볼게요:                               │
   │        - n=2 일 때: [3, 4], target=7 → [0, 1]              │
   │        - 음수: [-1, -2, 5], target=4 → [1, 2]              │
   │        - 중복: [3, 3], target=6 → [0, 1]                   │
   │                                                            │
   │       Brute Force 는 O(n²) — 모든 쌍 확인.                 │
   │       n=10⁵ 라 O(n²)=10¹⁰ → TLE.                           │
   │                                                            │
   │       내부 루프가 'complement 가 존재?' 를 검색하는데,     │
   │       이걸 hash map 으로 O(1) 에 바꾸면 전체 O(n).         │
   │                                                            │
   │       Approach: 한 번 순회하며 (값, 인덱스) hash 저장,     │
   │                 매 step 에 complement = target - 현재값을 │
   │                 hash 에서 lookup. 시간 O(n), 공간 O(n)."    │
   └────────────────────────────────────────────────────────────┘

   ┌─ 10–30 분: Coding (말하면서) ─────────────────────────────┐
   │  나: "seen 이라는 dict 를 둘게요. key=값, value=인덱스.    │
   │       enumerate 로 순회하고, 각 i 에서 complement 계산,   │
   │       seen 에 있으면 즉시 return [seen[complement], i]."   │
   │                                                            │
   │       def two_sum(nums, target):                          │
   │           seen = {}                                       │
   │           for i, v in enumerate(nums):                    │
   │               c = target - v                              │
   │               if c in seen:                               │
   │                   return [seen[c], i]                     │
   │               seen[v] = i                                 │
   │           return []                                       │
   └────────────────────────────────────────────────────────────┘

   ┌─ 30–40 분: Test + Verify ─────────────────────────────────┐
   │  나: "[2, 7, 11, 15], target=9 로 trace 하겠습니다:        │
   │        i=0: c=7, seen 에 없음, seen={2:0}                 │
   │        i=1: c=2, seen 에 있음! return [0, 1] ✓             │
   │                                                            │
   │       엣지 케이스:                                         │
   │        - [3, 3], target=6: i=0 c=3 없음 seen={3:0},        │
   │                            i=1 c=3 있음 return [0, 1] ✓    │
   │        - 답 없는 경우 [1,2,3], target=10: 빈 [] 반환.      │
   │                                                            │
   │       복잡도: 시간 O(n), 공간 O(n)."                       │
   └────────────────────────────────────────────────────────────┘

   ┌─ 40–45 분: Q & A ────────────────────────────────────────┐
   │  면접관: "공간 O(1) 로 줄일 수 있나요?"                    │
   │  나: "정렬 가능하면 Two Pointers 로 O(n log n) 시간 /      │
   │       O(1) 공간 가능. 단, 인덱스 보존이 필요하면 정렬 전   │
   │       (값, 원본 인덱스) tuple 로 저장해야 합니다."          │
   └────────────────────────────────────────────────────────────┘
```

### 단계별 의미

| Step | 시간 | 평가 4 축 | 핵심 행위 |
|------|------|----------|----------|
| ① | 0–5 분 | Communication 위주 | _내 이해_ 를 면접관과 합의 |
| ② | 5–10 분 | Correctness + Complexity 시작 | edge case 명시, brute → optimal trade-off 말하기 |
| ③ | 10–30 분 | Code Quality + Communication | _말하면서_ 코딩, 변수명 의도 설명 |
| ④ | 30–40 분 | Correctness + Complexity 마무리 | trace + edge + 시공간 복잡도 |
| ⑤ | 40–45 분 | 모든 축 | follow-up 에 trade-off 답변 |

!!! note "여기서 잡아야 할 두 가지"
    **(1) 코드 작성 시간보다 _합의 + 검증_ 시간이 길어야 정상** — 30 분 코딩이지만 0–10 분과 30–45 분의 _25 분_ 이 합의/검증. 이 비율을 줄이면 점수가 떨어집니다.<br>
    **(2) "Brute Force → 비효율 분석 → 최적화" 의 _3 단계 발화_ 는 거의 모든 문제의 표준 진입** — 바로 최적해를 말하면 "외운 거 같다" 는 인상, brute 만 말하고 멈추면 _깊이 부족_. 둘 다 말해야 사고 과정이 보입니다.

---

## 4. 일반화 — 4 축 평가 와 패턴 식별

### 4.1 평가 4 축

| 축 | 의미 | 어떻게 보여주나 |
|---|---|---|
| **Correctness** | 답이 모든 케이스에 맞나 | edge case 명시 + dry run |
| **Complexity** | 시간/공간 분석 | brute 와 optimal 모두 명시 |
| **Code Quality** | 가독성, 변수명, 구조 | 의미 있는 이름, 함수 분리, 일관 스타일 |
| **Communication** | 사고 과정 전달 | clarify, 말하면서 코딩, follow-up 적극 |

→ 4 축 합산이라 _하나라도 0 점_ 이면 통과 어려움. 다 풀어도 communication 0 이면 탈락.

### 4.2 패턴 1 줄 식별 키워드

```
"정렬됨 + 찾기"          → Binary Search
"정렬됨 + 두 값 관계"     → Two Pointers
"연속 부분 배열"          → Sliding Window
"이전에 본 적?"           → Hash Map
"가장 최근 / 매칭"        → Stack
"레벨 / 최단"             → BFS
"깊이 / 경로 / 합"        → DFS
"경우의 수 / 최대·최소"   → DP
"모든 조합"               → Backtracking
```

### 4.3 입력 크기 → 필요 복잡도 (역산)

| n | 최대 복잡도 | 대표 패턴 |
|---|-----------|----------|
| ≤ 20 | O(2ⁿ) | Backtracking |
| ≤ 1,000 | O(n²) | Brute Force OK |
| ≤ 100,000 | O(n log n) | Sort + Binary Search |
| ≤ 1,000,000 | O(n) | Hash Map, Two Pointers |

---

## 5. 디테일 — 타임라인, Clarify, Edge Case, 템플릿, 16 문제 로드맵

### 5.1 45 분 타임라인 (자주 쓰는 표)

| 시간 | 단계 | 할 일 |
|------|------|------|
| 0-5 분 | **이해** | 문제 재진술, 명확화 질문 |
| 5-10 분 | **패턴 + Brute Force** | 패턴 식별, O(n²) 먼저 제시 |
| 10-15 분 | **최적화** | 최적 접근법 구두로 설명 |
| 15-35 분 | **코딩** | 깔끔한 코드 작성, 설명하면서 코딩 |
| 35-40 분 | **테스트** | 예시로 Dry Run, 엣지 케이스 확인 |
| 40-45 분 | **분석** | 시간/공간 복잡도, 후속 질문 대응 |

### 5.2 반드시 할 명확화 질문 5 가지

```
1. "입력이 정렬되어 있나요?"
   → YES: Binary Search / Two Pointers
   → NO:  Hash Map / Sort 먼저

2. "중복 값이 있을 수 있나요?"
   → 중복 처리 로직 필요 여부 결정

3. "입력 크기 범위는?"
   → n ≤ 1000:  O(n²) OK
   → n ≤ 10⁶:   O(n) 필요

4. "음수 값이 있을 수 있나요?"
   → 합/곱 계산 시 로직 영향

5. "답이 없으면 무엇을 반환?"
   → -1? 빈 배열? null?
```

### 5.3 엣지 케이스 체크리스트

#### 배열
- `[]` (빈 배열)
- `[x]` (원소 1 개)
- 모든 값 동일
- 이미 정렬됨 / 역순 정렬
- 음수 포함

#### 문자열
- `""` (빈 문자열)
- `"a"` (한 글자)
- 모든 문자 동일

#### 트리
- `null` (빈 트리)
- 루트만 (단일 노드)
- 편향 트리 (한쪽으로만 — 연결 리스트처럼)

#### 숫자
- 0
- 음수
- 정수 오버플로

### 5.4 의사소통 템플릿 (각 단계별)

#### 1 단계: 이해
> "정리하면, [입력] 이 주어졌을 때 [출력] 을 구하는 문제입니다. 확인할 것이 있는데, 정렬되어 있나요? 중복이 있을 수 있나요? 입력 크기는 어느 정도인가요?"

#### 2 단계: 접근법
> "Brute Force 는 [O(n²) 방법] 입니다. 그런데 [관찰] 을 보면, [패턴] 을 사용하여 O(n) 으로 최적화할 수 있습니다."

**핵심**: 반드시 Brute Force 를 _먼저_ 말하고, 왜 비효율적인지 분석한 후, 최적화 제시. 바로 최적해를 말하면 "이 문제를 외웠구나" 인상.

#### 3 단계: 코딩 중
> "지금 [어떤 부분] 을 작성하고 있습니다. 이 변수는 [목적] 을 추적합니다."

**핵심**: 침묵하면서 코딩하지 마라. 생각을 말하면서 코딩해야 면접관이 사고 과정을 평가할 수 있다.

#### 4 단계: 검증
> "예시로 추적해보겠습니다... 시간 복잡도는 O(n), 공간 복잡도는 O(1) 입니다. 엣지 케이스: 빈 배열, 원소 1 개, 모든 값 동일."

### 5.5 DV 엔지니어가 알고리즘 면접을 보는 이유

```
빅테크 (삼성, Apple, Meta, Google 등) 의 채용 프로세스:

   1차: 이력서/포트폴리오 (도메인 전문성)
   2차: 코딩 테스트 (알고리즘) ← 이 자료의 대상
   3차: 기술 면접 (DV 도메인 심화)
   4차: 시스템 설계 / 행동 면접

   DV 엔지니어라도 코딩 테스트를 통과해야 기술 면접 기회가 생긴다.
   → 알고리즘은 "문지기" — 도메인 실력을 보여줄 기회를 얻기 위한 관문

전략:
   - 500 문제 풀기 불필요 — 16 문제(패턴별 2 개) 로 패턴 마스터
   - SystemVerilog 로도 풀 수 있음 (이 자료의 .sv 파일)
   - 시간 투자: 2-3 주, 하루 1-2 문제 + 패턴 복습
```

### 5.6 16 문제 학습 순서 (우선순위)

```
Week 1 (기초 패턴):
   Day 1: Two Sum (#1) — Hash Map
   Day 2: Valid Palindrome (#125) — Two Pointers
   Day 3: Max Avg Subarray (#643) — Sliding Window
   Day 4: Valid Parentheses (#20) — Stack
   Day 5: Search Insert (#35) — Binary Search

Week 2 (트리 + DP):
   Day 1: Max Depth (#104) — DFS
   Day 2: Level Order (#102) — BFS
   Day 3: Climbing Stairs (#70) — DP
   Day 4: House Robber (#198) — DP

Week 3 (Medium 도전):
   Day 1: 3Sum (#15) — Two Pointers
   Day 2: Longest Substring (#3) — Sliding Window
   Day 3: Daily Temperatures (#739) — Monotonic Stack
   Day 4: Search Rotated Array (#33) — Binary Search
   Day 5: Path Sum II (#113) — DFS
   Day 6: Right Side View (#199) — BFS
   Day 7: Group Anagrams (#49) — Hash Map
```

---

## 6. 흔한 오해 와 디버그 체크리스트

### 흔한 오해

!!! danger "❓ 오해 1 — '면접 = 풀이 완성하면 통과'"
    **실제**: Communication, edge case, complexity 합의 없이 풀이 시작은 _완성_ 해도 큰 감점. 다 못 풀어도 사고 흐름이 명확하면 통과 가능. 자동 채점 코딩 테스트 (정답 / 오답) 와 _면접_ 의 평가 기준은 다릅니다.<br>
    **왜 헷갈리는가**: 코딩테스트(자동채점) 과 면접의 평가 기준 차이를 체감 못 할 때.

!!! danger "❓ 오해 2 — '바로 최적해를 말하면 똑똑해 보인다'"
    **실제**: 면접관 시각에서는 _문제 외운_ 신호. Brute → 비효율 분석 → 최적화 의 _3 단계 발화_ 가 _사고 과정_ 의 증거. 외운 답이라도 _발화 순서_ 는 brute 부터 시작해야 합니다.<br>
    **왜 헷갈리는가**: 학교/올림피아드 식 채점 (정답만 보면 됨) 의 영향.

!!! danger "❓ 오해 3 — '침묵하며 코딩하면 집중력으로 보인다'"
    **실제**: 면접관은 _코드를 못 보거나_ (전화 면접) _보더라도 의도를 모름_. 변수 의도, 분기 이유, 막힌 지점을 _말하지 않으면_ "사고 과정" 점수가 0. 다 풀어도 communication 0 이면 탈락.<br>
    **왜 헷갈리는가**: 평소 혼자 코딩하는 습관이 면접에 그대로 옮겨감.

!!! danger "❓ 오해 4 — '엣지 케이스는 마지막에 한 번 보면 된다'"
    **실제**: 코딩 _전_ 에 엣지 케이스를 _명시_ 하지 않으면 코드가 그것에 맞춰 설계되지 않습니다. follow-up 에서 "N=0 이면?", "음수면?" 질문이 들어오면 _즉석_ 에서 코드를 뜯어고치다 시간이 다 갑니다. 명세 합의 단계의 _필수 항목_.<br>
    **왜 헷갈리는가**: 시간 압박 → 코드 먼저 → 엣지는 "있으면" 처리.

### 함정 표 (메타-스킬 chapter — 디버그 체크리스트 대신)

| 증상 | 원인 | 수정 |
|---|---|---|
| 코딩 끝났는데 follow-up 마다 코드 뜯어고침 | 입력 제약 / 엣지 케이스를 코딩 전에 적지 않음 | 5 가지(N 범위, 부호, 빈 입력, 단일 원소, 중복) 한 줄씩 _코딩 전_ 에 명시 |
| 다 풀었는데 떨어짐 | 침묵 코딩 — communication 0 점 | 변수 의도, 분기 이유를 _말하면서_ 코딩 |
| 30 분에 코드 끝, 검증 시간 0 | clarify/edge 단계에 5 분 못 씀 | 0–10 분에 _문제 합의_ 강제, 코딩은 30 분 시작 |
| 최적해 곧장 제시 → 면접관 표정 굳음 | "외운 답" 신호 | brute → 비효율 분석 → 최적화 3 단계 _발화_ 강제 |
| Big-O 답을 "잘 모르겠다" | 분석을 _코드 작성 후_ 에 함 | 코딩 _전_ 에 목표 복잡도를 합의, 코드 후 재확인 |
| 입력 크기 안 묻고 시작 | clarify 질문 5 종 누락 | 입력/제약 5 종 질문 외워서 첫 1 분에 |
| 답이 다중 (여러 가능) 인데 한 가지만 반환 | "어떤 답이 정답?" 합의 누락 | "임의 한 개? 모든 답?" clarify 첫 단계에 |
| 같은 패턴이 반복 등장 시 매번 처음부터 풀이 | 패턴 식별 키워드 부재 | 4.2 의 1 줄 키워드 표를 면접 직전 복습 |

---

## 7. 핵심 정리 (Key Takeaways)

- **45 분 타임라인** — ① 이해/clarify (5 분) → ② 예시/엣지 (5 분) → ③ 접근 + 복잡도 합의 (5 분) → ④ 코드 (20 분) → ⑤ 검증/리뷰 (10 분).
- **4 축 평가** — Correctness · Complexity · Code Quality · Communication. 모두 합쳐서 채점된다.
- **소리 내 사고하기** — 면접관은 코드보다 사고 흐름을 본다.
- **엣지케이스 먼저 적기** — 빈 입력, 한 원소, 중복, overflow 를 _코딩 전_ 에 적는 행위 자체가 평가 점수.
- **다 풀지 못해도 패스 가능** — 잘 정의된 접근 + 부분 코드 + 명확한 의사소통 > 완성된 코드 + 침묵.

!!! warning "실무 주의점"
    - **Clarify 시간 절약하지 말기** — 첫 5 분의 명세 합의가 뒤 30 분의 follow-up 폭탄을 막아준다.
    - **Brute → Optimal 발화 순서** — 외운 답이라도 brute 를 먼저 말해 _사고 과정_ 의 증거를 남긴다.
    - **녹음으로 self-review** — 모의 면접을 녹음 후 4 축 기준으로 자기 채점이 가장 빠른 학습 경로.

---

## 다음 단계 (마무리)

이로써 7 개 모듈 학습이 끝났습니다.

- 퀴즈로 마무리: [전체 Quiz Index](../quiz/) — 7 개 모듈 각 5 문항씩, 총 35 문항.
- 실습: 모의 면접 3 회 진행 후 녹음을 4 축 기준으로 self-review.
- 추가 자료: LeetCode Top Interview 150, Cracking the Coding Interview, NeetCode Roadmap.

[퀴즈 풀어보기 →](quiz/07_interview_strategy_quiz.md)

<div class="chapter-nav">
  <a class="nav-prev" href="../06_dynamic_programming_explained/">
    <div class="nav-label">◀ 이전</div>
    <div class="nav-title">Dynamic Programming (DP)</div>
  </a>
  <a class="nav-next" href="../quiz/">
    <div class="nav-label">다음 ▶</div>
    <div class="nav-title">퀴즈로 이동</div>
  </a>
</div>


--8<-- "abbreviations.md"
