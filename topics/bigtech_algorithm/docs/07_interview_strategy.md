# Unit 7: 면접 전략

<div class="learning-meta">
  <span class="meta-badge meta-level-intermediate">📊 Intermediate</span>
</div>

## 45분 타임라인

| 시간 | 단계 | 할 일 |
|------|------|------|
| 0-5분 | **이해** | 문제 재진술, 명확화 질문 |
| 5-10분 | **패턴 + Brute Force** | 패턴 식별, O(n²) 먼저 제시 |
| 10-15분 | **최적화** | 최적 접근법 구두로 설명 |
| 15-35분 | **코딩** | 깔끔한 코드 작성, 설명하면서 코딩 |
| 35-40분 | **테스트** | 예시로 Dry Run, 엣지 케이스 확인 |
| 40-45분 | **분석** | 시간/공간 복잡도, 후속 질문 대응 |

## 반드시 할 명확화 질문 5가지

```
1. "입력이 정렬되어 있나요?"
   → YES: Binary Search / Two Pointers
   → NO: Hash Map / Sort 먼저

2. "중복 값이 있을 수 있나요?"
   → 중복 처리 로직 필요 여부 결정

3. "입력 크기 범위는?"
   → n≤1000: O(n²) OK
   → n≤10⁶: O(n) 필요

4. "음수 값이 있을 수 있나요?"
   → 합/곱 계산 시 로직 영향

5. "답이 없으면 무엇을 반환?"
   → -1? 빈 배열? null?
```

## 입력 크기 → 필요 복잡도

| n | 최대 복잡도 | 대표 패턴 |
|---|-----------|----------|
| ≤ 20 | O(2ⁿ) | Backtracking |
| ≤ 1,000 | O(n²) | Brute Force OK |
| ≤ 100,000 | O(n log n) | Sort + Binary Search |
| ≤ 1,000,000 | O(n) | Hash Map, Two Pointers |

## 엣지 케이스 체크리스트

### 배열
- `[]` (빈 배열)
- `[x]` (원소 1개)
- 모든 값 동일
- 이미 정렬됨 / 역순 정렬
- 음수 포함

### 문자열
- `""` (빈 문자열)
- `"a"` (한 글자)
- 모든 문자 동일

### 트리
- `null` (빈 트리)
- 루트만 (단일 노드)
- 편향 트리 (한쪽으로만 — 연결 리스트처럼)

### 숫자
- 0
- 음수
- 정수 오버플로

---

## 의사소통 템플릿

### 1단계: 이해
> "정리하면, [입력]이 주어졌을 때 [출력]을 구하는 문제입니다. 확인할 것이 있는데, 정렬되어 있나요? 중복이 있을 수 있나요? 입력 크기는 어느 정도인가요?"

### 2단계: 접근법
> "Brute Force는 [O(n²) 방법]입니다. 그런데 [관찰]을 보면, [패턴]을 사용하여 O(n)으로 최적화할 수 있습니다."

**핵심**: 반드시 Brute Force를 먼저 말하고, 왜 비효율적인지 분석한 후, 최적화 제시. 바로 최적해를 말하면 "이 문제를 외웠구나" 인상.

### 3단계: 코딩 중
> "지금 [어떤 부분]을 작성하고 있습니다. 이 변수는 [목적]을 추적합니다."

**핵심**: 침묵하면서 코딩하지 마라. 생각을 말하면서 코딩해야 면접관이 사고 과정을 평가할 수 있다.

### 4단계: 검증
> "예시로 추적해보겠습니다... 시간 복잡도는 O(n), 공간 복잡도는 O(1)입니다. 엣지 케이스: 빈 배열, 원소 1개, 모든 값 동일."

---

## 패턴별 1줄 식별 키워드

```
"정렬됨 + 찾기"          → Binary Search
"정렬됨 + 두 값 관계"     → Two Pointers
"연속 부분 배열"          → Sliding Window
"이전에 본 적?"           → Hash Map
"가장 최근 / 매칭"        → Stack
"레벨 / 최단"            → BFS
"깊이 / 경로 / 합"       → DFS
"경우의 수 / 최대·최소"   → DP
"모든 조합"              → Backtracking
```

---

## DV 엔지니어가 알고리즘 면접을 보는 이유

```
빅테크(삼성, Apple, Meta, Google 등)의 채용 프로세스:

  1차: 이력서/포트폴리오 (도메인 전문성)
  2차: 코딩 테스트 (알고리즘) ← 이 자료의 대상
  3차: 기술 면접 (DV 도메인 심화)
  4차: 시스템 설계 / 행동 면접

  DV 엔지니어라도 코딩 테스트를 통과해야 기술 면접 기회가 생긴다.
  → 알고리즘은 "문지기" — 도메인 실력을 보여줄 기회를 얻기 위한 관문

전략:
  - 500문제 풀기 불필요 — 16문제(패턴별 2개)로 패턴 마스터
  - SystemVerilog로도 풀 수 있음 (이 자료의 .sv 파일)
  - 시간 투자: 2-3주, 하루 1-2문제 + 패턴 복습
```

## 16문제 학습 순서 (우선순위)

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
