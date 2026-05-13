# Module 04 — Stack & Binary Search

<!-- DV-SKOOL-CH-CTX:start -->
<div class="chapter-context" data-cat="applied">
  <a class="chapter-back" href="../">
    <span class="chapter-back-arrow">←</span>
    <span class="chapter-back-icon">📐</span>
    <span class="chapter-back-text">BigTech Algorithm</span>
  </a>
  <span class="chapter-divider">›</span>
  <span class="chapter-marker">Module 04</span>
</div>
<!-- DV-SKOOL-CH-CTX:end -->

<!-- DV-SKOOL-CH-TOC:start -->
<div class="page-toc">
  <span class="page-toc-label">목차</span>
  <a class="page-toc-link" href="#1-why-care-이-모듈이-왜-필요한가">1. Why care?</a>
  <a class="page-toc-link" href="#2-intuition-비유와-한-장-그림">2. Intuition</a>
  <a class="page-toc-link" href="#3-작은-예-valid-parentheses-한-문자-한-문자-stack-추적">3. 작은 예 — Valid Parentheses 추적</a>
  <a class="page-toc-link" href="#4-일반화-stack-과-binary-search-의-공통-구조">4. 일반화</a>
  <a class="page-toc-link" href="#5-디테일-monotonic-stack-binary-search-3-원칙-코드">5. 디테일</a>
  <a class="page-toc-link" href="#6-흔한-오해-와-디버그-체크리스트">6. 흔한 오해 + 디버그</a>
  <a class="page-toc-link" href="#7-핵심-정리-key-takeaways">7. 핵심 정리</a>
</div>
<!-- DV-SKOOL-CH-TOC:end -->

!!! objective "학습 목표"
    이 모듈을 마치면:

    - **Define** Stack push/pop 의 LIFO 원리와 Binary Search 의 lower_bound / upper_bound 차이를 적을 수 있다.
    - **Explain** Monotonic Stack 이 왜 "다음으로 큰 원소" 류 문제를 O(N) 으로 푸는지 설명할 수 있다.
    - **Apply** Valid Parentheses, Daily Temperatures, Search-in-Rotated-Array 같은 전형 문제를 풀 수 있다.
    - **Analyze** Binary Search 의 변형(범위, parametric search) 을 invariant 로 정형화할 수 있다.
    - **Evaluate** Stack vs Recursion / Binary Search vs Hash 의 trade-off 를 비교할 수 있다.

!!! info "사전 지식"
    - Module 01–03
    - 재귀와 반복의 동등성 직관, 부등식의 단조성

---

## 1. Why care? — 이 모듈이 왜 필요한가

### 1.1 시나리오 — "_더 빠르게_?" 의 함정

당신은 _Daily Temperatures_ 문제 풀이. 첫 시도 — 각 day 마다 _뒤에_ 더 따뜻한 day 찾기 → **O(N²)**.

면접관: "**N=10⁶ 이면 timeout. 더 빠르게?**"

당신은 _hash map / two pointers_ 적용 시도. _안 됨_. 패턴이 다름.

**답은 Monotonic Stack**:
```
stack 에 _아직 답 못 찾은_ index 저장.
새 day i 의 temp > stack top index 의 temp 면 → pop + 답 채움.
```
Amortized O(N) — 각 element 가 stack 에 _한 번 push + 한 번 pop_.

**Binary Search** 가 답인 경우:
- **Monotonicity**: 어떤 함수 f(x) 가 _단조_. 정렬된 배열은 자명한 예.
- _숨겨진_ monotonicity: "**parameter K 에 대한 yes/no 답이 단조**" — Binary search on answer.

Stack 은 **이전 상태를 미루어 두었다 다시 쓰는** 가장 단순하지만 강력한 도구이고, Binary Search 는 **단조성(monotonicity)** 만 있다면 어디든 통하는 보편 패턴입니다. 이 둘을 패턴으로 익히면 면접에서 "이게 stack/이진 탐색 문제인가?" 를 인지하는 시간이 크게 줄어듭니다.

이 모듈을 건너뛰면 Daily Temperatures / Largest Rectangle / Search Rotated Array 같은 빈출 문제에서 _O(N²) brute force_ 로 떨어지고 면접관이 "더 빠르게?" 라고 되물을 때 막힙니다. 반대로 monotonic stack 의 _amortized O(N)_ 직관과 binary search 3 원칙이 잡히면 이 카테고리의 문제가 _10 분 안에_ 끝납니다.

!!! question "🤔 잠깐 — Monotonic stack 의 _amortized_?"
    각 element 가 stack 에서 _최대 N 번_ pop 될 수 있는 것처럼 보임 → O(N²) 인 듯?

    ??? success "정답"
        **각 element 가 _전체 동작 동안_ 최대 _1 번 push + 1 번 pop_**.

        - Push: 입력 element 마다 한 번씩. 총 N 번.
        - Pop: 한 번 pop 된 element 는 _다시 안 들어옴_. 총 ≤ N 번.

        합산: 2N 연산 = O(N). _amortized_ 개념의 가장 깔끔한 예.

        면접에서 명시: "_각 element 의 _아 amortized cost 가 O(1)_, 총 N 개 → O(N)_".

---

## 2. Intuition — 비유와 한 장 그림

!!! tip "💡 한 줄 비유"
    **Stack** ≈ **책 더미** — 가장 최근에 올린 책을 가장 먼저 꺼낸다 (LIFO).<br>
    **Binary Search** ≈ **사전 가운데 펼치기** — 찾는 단어가 이쪽 절반에 있는지 저쪽 절반에 있는지만 결정하면, 매번 절반을 _통째로_ 버릴 수 있다.

### 한 장 그림 — 두 패턴의 검색 공간 축소

```
   Stack (LIFO, "최근" 추적)              Binary Search (절반 폐기)
   ───────────────────────────            ───────────────────────────
                                          
       ┌─────┐  ← top (마지막 push)        nums:  1  3  5  7  9 11 13
       │  C  │                                    └──┬──┘└──┬──┘└──┘
       ├─────┤                                        절반     절반
       │  B  │                                                       
       ├─────┤                             Step 1: mid 비교 →        
       │  A  │  ← bottom                           한쪽 절반 폐기    
       └─────┘                                                       
                                          Step 2: 남은 절반에서 mid →
   push(D) → 위에 쌓임                              또 한쪽 폐기      
   pop()   → top 부터 빠짐                                            
                                          Step 3: 1 개 남음 → check 
   "가장 최근 X 와 매칭"                  
   "되돌리기 (undo)"                       검색 공간: n → n/2 → n/4   
   "다음 큰 원소까지 거리"                          → ... → 1        
                                          → log₂(n) step             
```

### 왜 이렇게 설계됐는가 — Design rationale

**Stack** 의 LIFO 는 _시간 역순_ 을 자연스럽게 모델링합니다. "가장 최근에 연 괄호와 닫는 괄호가 매칭" 이라는 _시간 역순 매칭_ 은 stack 이 정확히 풀어주는 구조. Monotonic Stack 은 여기에 _불필요한 후보 제거_ 를 더해 "각 원소가 push 1 번, pop 최대 1 번" 이라는 amortized O(N) 을 얻습니다.

**Binary Search** 의 본질은 정렬이 아닌 **단조 boolean 함수** 입니다. "X 이상에서 조건이 항상 true, X 미만에서 항상 false" 인 _경계_ 가 존재하면, 매 step 에 절반을 폐기할 수 있어 O(log N). 그래서 "정렬된 배열" 외에도 _capacity 가능한가?_ 류 parametric search 가 모두 같은 패턴.

---

## 3. 작은 예 — Valid Parentheses 한 문자 한 문자 Stack 추적

가장 단순한 시나리오. **`s = "([{}])"`** 가 올바른 괄호 문자열인지 stack 으로 판정.

### 단계별 추적

```
   문자:    (    [    {    }    ]    )
   인덱스:  0    1    2    3    4    5

   ┌─ i=0: '(' ──────────┐
   │  여는 괄호 → push    │     stack: [ ( ]
   └──────────────────────┘

   ┌─ i=1: '[' ──────────┐
   │  여는 괄호 → push    │     stack: [ (  [ ]
   └──────────────────────┘

   ┌─ i=2: '{' ──────────┐
   │  여는 괄호 → push    │     stack: [ (  [  { ]
   └──────────────────────┘

   ┌─ i=3: '}' ──────────────────────────────┐
   │  닫는 괄호 → top='{' 와 매칭 → pop         stack: [ (  [ ]
   └──────────────────────────────────────────┘

   ┌─ i=4: ']' ──────────────────────────────┐
   │  닫는 괄호 → top='[' 와 매칭 → pop         stack: [ ( ]
   └──────────────────────────────────────────┘

   ┌─ i=5: ')' ──────────────────────────────┐
   │  닫는 괄호 → top='(' 와 매칭 → pop         stack: [ ]
   └──────────────────────────────────────────┘

   루프 종료 → stack 비어 있음 → return TRUE
```

### 단계별 의미

| Step | 누가 | 무엇을 | 왜 |
|------|------|--------|-----|
| ① | parser | i=0 의 `(` 를 봄 | 여는 괄호 = "나중에 닫혀야 함" |
| ② | stack | `push('(')` | 미래의 매칭 후보를 보관 |
| ③ | parser | i=3 의 `}` 를 봄 | 닫는 괄호 = "가장 최근 여는 것과 매칭" |
| ④ | stack | `top()` 으로 `{` 확인 | LIFO — 가장 최근에 push 된 게 짝 |
| ⑤ | matcher | `{` 와 `}` 가 짝 → OK | 만약 `[` 와 `}` 면 즉시 false |
| ⑥ | stack | `pop()` | 매칭 끝난 후보 제거 |
| ⑦ | end check | stack 이 비었는가? | 비어 있어야 모든 여는 괄호가 닫힘 |

```python
def is_valid(s):
    stack = []
    pair  = {')': '(', ']': '[', '}': '{'}
    for c in s:
        if c in '([{':
            stack.append(c)             # 여는 → push
        else:
            if not stack: return False  # 닫는 인데 stack 비었음
            if stack.pop() != pair[c]: return False
    return not stack                    # 모두 닫혔으면 stack 비어야
```

### 반례: `s = "([)]"`

```
   i=0: '(' → push → [ ( ]
   i=1: '[' → push → [ (  [ ]
   i=2: ')' → top='[', 짝(')'→'(') 불일치! → return FALSE
```

!!! note "여기서 잡아야 할 두 가지"
    **(1) "가장 최근의 여는 것" 과 매칭한다는 _시간 역순_ 이 LIFO 의 본질** — Queue (FIFO) 로는 풀 수 없는 문제. 매칭 짝의 _마지막 push_ 가 _가장 먼저 pop_ 되어야 합니다.<br>
    **(2) 종료 시 stack 이 비어 있는지 확인** — 닫는 괄호로 끝났어도 여는 괄호가 더 많이 push 됐을 수 있음. 마지막 단계의 `return stack.empty()` 가 _빠지면_ `"((("` 같은 입력에 false positive.

---

## 4. 일반화 — Stack 과 Binary Search 의 공통 구조

### 4.1 Stack 신호 매핑

```d2
direction: down

K: "문제의 키워드\n· '가장 최근'\n· '매칭 쌍 / 중첩'\n· '되돌리기 (undo)'\n· '다음으로 큰/작은 원소'\n· '히스토그램 / 빗물'"
P: "Stack 또는\nMonotonic Stack 후보"
K -> P
```

### 4.2 Binary Search 신호 매핑

```d2
direction: down

K: "문제의 키워드\n· '정렬됨'\n· '삽입 위치'\n· '조건 만족 최소/최대'\n· 'rotated 정렬 배열'\n· 'answer ≥ X 가능?' (parametric)"
P: "Binary Search 후보\n(정렬이 아닌 _단조성_이 핵심)"
K -> P
```

### 4.3 두 패턴의 공통점 — "선택적 폐기"

| 패턴 | 폐기 대상 | 폐기 근거 |
|---|---|---|
| Monotonic Stack | "더 이상 답이 될 수 없는 후보" 를 stack 에서 pop | 새 원소가 _더 강한 후보_ 라서 |
| Binary Search | "답이 있을 수 없는 절반" 을 통째 폐기 | 단조성으로 _그쪽엔 답이 없음_ 이 보장 |

둘 다 **"각 원소를 한 번만 본다"** 는 amortized 효율성을 가집니다.

---

## 5. 디테일 — Monotonic Stack, Binary Search 3 원칙, 코드

### 5.1 Stack 기본 — Valid Parentheses

```
키워드: "가장 최근", "매칭 쌍", "중첩", "되돌리기"
원리: LIFO (Last In, First Out) — 마지막에 넣은 것을 먼저 꺼냄

SV 구현: queue + push_back / pop_back / [$] 로 top 접근
```

### 5.2 Monotonic Stack — Daily Temperatures (LeetCode #739)

```
핵심: "다음으로 큰/작은 원소까지의 거리" → Monotonic Stack
원리: Stack 에 "아직 답을 못 찾은 인덱스" 를 보관
       현재 값이 stack top 보다 크면 → pop 하며 답 기록
```

#### 사고 과정

```
문제: 각 날에 대해, 더 따뜻한 날까지 몇 일 기다려야 하는가?
      temperatures = [73, 74, 75, 71, 69, 72, 76, 73]
      출력:          [ 1,  1,  4,  2,  1,  1,  0,  0]

Brute Force O(n²): 각 날마다 오른쪽으로 스캔하여 더 큰 값 찾기
최적화: "아직 답을 못 찾은 날들" 을 Stack 에 보관
        새 날의 온도가 Stack top 보다 높으면 → 답을 찾은 것!
```

#### Dry Run

```
temps = [73, 74, 75, 71, 69, 72, 76, 73]
stack = [] (인덱스 저장), result = [0,0,0,0,0,0,0,0]

i=0: temp=73
  stack 비어있음 → push 0
  stack: [0]

i=1: temp=74
  74 > temps[stack.top]=temps[0]=73 → pop 0, result[0]=1-0=1
  stack 비어있음 → push 1
  stack: [1]

i=2: temp=75
  75 > temps[1]=74 → pop 1, result[1]=2-1=1
  stack 비어있음 → push 2
  stack: [2]

i=3: temp=71
  71 < temps[2]=75 → push 만
  stack: [2, 3]

i=4: temp=69
  69 < temps[3]=71 → push 만
  stack: [2, 3, 4]

i=5: temp=72
  72 > temps[4]=69 → pop 4, result[4]=5-4=1
  72 > temps[3]=71 → pop 3, result[3]=5-3=2
  72 < temps[2]=75 → 멈춤, push 5
  stack: [2, 5]

i=6: temp=76
  76 > temps[5]=72 → pop 5, result[5]=6-5=1
  76 > temps[2]=75 → pop 2, result[2]=6-2=4
  stack 비어있음 → push 6
  stack: [6]

i=7: temp=73
  73 < temps[6]=76 → push 만
  stack: [6, 7]

끝: stack 에 남은 [6, 7] 은 답이 없음 → result[6]=0, result[7]=0

result = [1, 1, 4, 2, 1, 1, 0, 0] ✓

시간 O(n): 각 인덱스는 push 1 번, pop 최대 1 번 → 총 2n 연산
공간 O(n): stack 최대 n 개
```

#### Monotonic Stack 활용 정리

```
"다음으로 큰 원소" (Next Greater Element)   → 감소하는 Monotonic Stack
"다음으로 작은 원소" (Next Smaller Element) → 증가하는 Monotonic Stack
"히스토그램 최대 넓이" (Largest Rectangle)  → Monotonic Stack
"빗물 가두기" (Trapping Rain Water)         → Monotonic Stack (또는 Two Pointers)

Stack 다른 활용:
   Undo/Redo: 최근 작업 되돌리기
   Calculator: 연산자 우선순위 처리
```

### 5.3 Binary Search — 3 대 실수 (면접 킬러)

```
실수 1: while (left < right)              ← 틀림!
정답:   while (left <= right)             ← left == right 일 때도 검사

실수 2: mid = (left + right) / 2          ← 오버플로!
정답:   mid = left + (right - left) / 2   ← 안전

실수 3: left = mid / right = mid          ← 무한 루프!
정답:   left = mid + 1 / right = mid - 1  ← 반드시 ±1
```

### 5.4 Binary Search — Dry Run

```
nums = [1, 3, 5, 7, 9, 11, 13], target = 9

   left=0, right=6, mid=3: nums[3]=7 < 9 → left=4
   left=4, right=6, mid=5: nums[5]=11 > 9 → right=4
   left=4, right=4, mid=4: nums[4]=9 == 9 → Found! return 4

target = 6 (없는 값):
   left=0, right=6, mid=3: nums[3]=7 > 6 → right=2
   left=0, right=2, mid=1: nums[1]=3 < 6 → left=2
   left=2, right=2, mid=2: nums[2]=5 < 6 → left=3
   left=3 > right=2 → 루프 종료 → return -1 (Not Found)

   이때 left=3 = "6 이 삽입되어야 할 위치" (Search Insert Position)
```

### 5.5 Binary Search 변형 — 조건 만족하는 최소/최대 (Lower Bound)

```
"최소 X 를 찾아라 (조건 f(x) 를 만족하는)" → Lower Bound

   left=0, right=n
   while (left < right):
       mid = left + (right - left) / 2
       if (condition(mid)):
           right = mid      ← 조건 만족 → 더 작은 쪽 탐색
       else:
           left = mid + 1   ← 조건 불만족 → 더 큰 쪽 탐색
   return left

예: Search in Rotated Array (#33)
   → 어느 쪽이 정렬되어 있는지 판단 → 해당 범위에서 이분
```

### 5.6 면접 답안 템플릿

```
Stack 문제 인식: "가장 최근", "매칭", "중첩" → Stack
Binary Search 문제 인식: "정렬" + "찾기" → Binary Search

Binary Search 코딩 시:
   1. while (left <= right) — 등호 포함!
   2. mid = left + (right - left) / 2 — 오버플로 방지
   3. left = mid + 1, right = mid - 1 — ±1 필수

   이 세 가지를 "Binary Search 3 원칙" 으로 외우면 실수 방지
```

### 5.7 SystemVerilog 예제 코드

원본 파일: `04_stack_binary_search.sv`

```systemverilog
// =============================================================
// Unit 4: Stack & Binary Search
// =============================================================
// Stack (LIFO):
//   - SV: queue[$] + push_back / pop_back / [$] for top
//   - Keywords: "most recent", "matching pairs", "nested", "undo"
//
// Binary Search:
//   - Sorted data -> O(log n) search
//   - 3 common mistakes to AVOID:
//     1. while (left < right)     -> must be (left <= right)
//     2. mid = (left+right)/2     -> overflow! use left+(right-left)/2
//     3. left = mid / right = mid -> infinite loop! use mid+1 / mid-1
//   - When target not found, `left` = insertion position
// =============================================================

module unit4_stack_bsearch;

  // ---------------------------------------------------------
  // Valid Parentheses: stack for matching
  // ---------------------------------------------------------
  function automatic bit is_valid_parens(string s);
    byte stack[$];

    for (int i = 0; i < s.len(); i++) begin
      byte c = s[i];

      if (c == "(" || c == "[" || c == "{")
        stack.push_back(c);
      else begin
        if (stack.size() == 0) return 0;

        byte top = stack[$];
        stack.pop_back();

        if (c == ")" && top != "(") return 0;
        if (c == "]" && top != "[") return 0;
        if (c == "}" && top != "{") return 0;
      end
    end

    return (stack.size() == 0);
  endfunction

  // ---------------------------------------------------------
  // Binary Search: standard template
  // ---------------------------------------------------------
  function automatic int binary_search(int nums[], int target);
    int left  = 0;
    int right = nums.size() - 1;

    while (left <= right) begin                  // <= not <
      int mid = left + (right - left) / 2;       // overflow safe

      if (nums[mid] == target)
        return mid;
      else if (nums[mid] < target)
        left = mid + 1;                          // +1 not mid
      else
        right = mid - 1;                         // -1 not mid
    end

    return -1;
  endfunction

  // ---------------------------------------------------------
  // Search Insert Position: binary search variant
  // When target not found, `left` = where it should be inserted
  // ---------------------------------------------------------
  function automatic int search_insert(int nums[], int target);
    int left  = 0;
    int right = nums.size() - 1;

    while (left <= right) begin
      int mid = left + (right - left) / 2;

      if (nums[mid] == target)
        return mid;
      else if (nums[mid] < target)
        left = mid + 1;
      else
        right = mid - 1;
    end

    return left;  // insertion point
  endfunction

  // ---------------------------------------------------------
  // Daily Temperatures: Monotonic Stack
  // "How many days until a warmer temperature?"
  // Stack stores indices of days still waiting for answer.
  // When current temp > stack top's temp -> pop and record answer.
  // O(n) time: each index pushed once, popped at most once.
  // ---------------------------------------------------------
  function automatic void daily_temperatures(int temps[], output int result[]);
    int n = temps.size();
    int stack[$];   // stores indices (not values!)
    result = new[n];

    for (int i = 0; i < n; i++) begin
      // Pop all days whose answer is found (current day is warmer)
      while (stack.size() > 0 && temps[i] > temps[stack[$]]) begin
        int idx = stack[$];
        stack.pop_back();
        result[idx] = i - idx;
      end
      stack.push_back(i);
    end
    // Remaining in stack have no warmer day -> result stays 0
  endfunction

  // ---------------------------------------------------------
  // Test
  // ---------------------------------------------------------
  initial begin
    $display("parens ([]): %0b",  is_valid_parens("([])"));  // 1
    $display("parens ([)]: %0b",  is_valid_parens("([)]"));  // 0

    int arr[] = '{1, 3, 5, 7, 9, 11, 13};
    $display("search 9: %0d",  binary_search(arr, 9));   // 4
    $display("search 6: %0d",  binary_search(arr, 6));   // -1

    int arr2[] = '{1, 3, 5, 6};
    $display("insert 5: %0d",  search_insert(arr2, 5));  // 2
    $display("insert 2: %0d",  search_insert(arr2, 2));  // 1
    $display("insert 7: %0d",  search_insert(arr2, 7));  // 4

    // Daily Temperatures
    int temps[] = '{73, 74, 75, 71, 69, 72, 76, 73};
    int dt_result[];
    daily_temperatures(temps, dt_result);
    $write("daily_temps: ");
    foreach (dt_result[i]) $write("%0d ", dt_result[i]);
    $display("");  // Expected: 1 1 4 2 1 1 0 0
  end

endmodule
```

---

## 6. 흔한 오해 와 디버그 체크리스트

### 흔한 오해

!!! danger "❓ 오해 1 — 'Binary Search = sorted array 에서만 가능'"
    **실제**: 정렬 외에도 _단조 boolean 함수_ (예: "이 capacity 로 가능?" 함수가 X 이상에서 항상 true) 에도 적용 가능. 이걸 _parametric search_ 라 부르며, "최대값을 최소화" / "최소값을 최대화" 류 문제의 표준 도구.<br>
    **왜 헷갈리는가**: 교과서 첫 예시가 항상 "sorted array" 라 "sorted = 필수" 로 일반화.

!!! danger "❓ 오해 2 — '`mid = (lo+hi)/2` 는 항상 안전'"
    **실제**: `lo + hi` 가 `INT_MAX` 를 넘으면 wrap-around → 음수 인덱스 → segfault. 1985 년 JDK `Arrays.binarySearch` 버그로 유명. 작은 입력 테스트는 다 통과해서 production 에서 처음 발견.<br>
    **왜 헷갈리는가**: int overflow 는 small/medium 입력에서 안 일어나고, 큰 배열에서만 발현 → unit test 통과.

!!! danger "❓ 오해 3 — 'Stack 과 재귀는 다른 도구'"
    **실제**: 재귀 호출 = 묵시적 stack. 깊이 큰 트리 / 그래프에서 재귀는 stack overflow 위험 (Python ~1000, C++ thread stack 수만). 깊이 한계가 우려되면 _명시적 stack_ 으로 변환하는 게 표준.<br>
    **왜 헷갈리는가**: 언어 추상화 (재귀 syntax) 가 stack 을 _보이지 않게_ 만들어서.

!!! danger "❓ 오해 4 — 'Monotonic Stack 의 시간 복잡도 = O(N²)'"
    **실제**: 내부 while 루프가 있어 보이지만, _amortized_ 로 O(N). 각 원소는 평생 push 1 번, pop 최대 1 번 → 총 2N 회. while 안의 작업도 한 원소당 한 번이라는 _불변량_ 이 보장됩니다.<br>
    **왜 헷갈리는가**: 이중 루프 모양 (`for + while`) 만 보고 단순히 곱하기.

### 디버그 체크리스트

| 증상 | 1차 의심 | 어디 보나 |
|---|---|---|
| Binary Search 가 무한 루프 | `left = mid` 또는 `right = mid` (±1 누락) | left/right 갱신문 — 반드시 `mid+1` 또는 `mid-1` |
| `target` 이 마지막 원소인데 -1 반환 | `while (left < right)` (등호 누락) | 부등호 — `left <= right` 인지 |
| 큰 배열에서 segfault / 음수 인덱스 | `mid = (lo+hi)/2` 의 int overflow | `mid = lo + (hi-lo)/2` 로 작성 |
| Valid Parentheses 가 `"((("` 에 true | 종료 시 stack 비었나 미확인 | `return stack.empty()` 가 마지막에 있는지 |
| Daily Temperatures 가 같은 답을 두 번 기록 | pop 안 하고 단순 비교만 | while 안의 `pop` + `result[idx]` 갱신 한 셋트 |
| Monotonic Stack 이 O(N²) 처럼 느림 | stack 에 인덱스가 아닌 _값_ 을 넣음 | stack=[idx] 로 저장하고 `temps[stack[$]]` 로 lookup |
| Search Rotated Array 가 무한루프 | 어느 쪽이 정렬됐는지 판단 누락 | `nums[lo] <= nums[mid]` 로 왼쪽 정렬 확인 |
| Lower Bound 가 마지막 인덱스 +1 반환 | 모든 원소가 조건 불만족 | answer 범위 = `[0, n]` 인지 _밖의 값_ 을 의미 있게 처리 |

---

## 7. 핵심 정리 (Key Takeaways)

- **Stack** — LIFO. Bracket matching, monotonic stack 류 문제의 단골 도구.
- **Monotonic Stack** — "다음 큰/작은 원소" 류 문제를 amortized O(N) 으로 푼다.
- **Binary Search 의 본질 = 단조성** — sorted 가 아니라 "조건 함수가 단조" 면 적용 가능 (parametric search).
- **lower_bound / upper_bound** 차이 명확히 — off-by-one 의 주요 원인.
- **재귀 vs Stack** — 깊이 큰 트리/그래프에서 재귀는 stack overflow 위험, 명시적 stack 으로 변환.

!!! warning "실무 주의점"
    - **Integer overflow** — `mid = lo + (hi-lo)/2` 가 표준. 한 번 잘못 적으면 production 에서만 발현.
    - **±1 누락** — `left = mid` 또는 `right = mid` 는 즉시 무한루프. 면접관이 가장 먼저 보는 실수.
    - **Stack overflow vs heap** — 재귀 깊이 한계는 언어/OS 환경 의존. N=10⁴ 이상 깊이는 위험 신호.

### 7.1 자가 점검

!!! question "🤔 Q1 — Search rotated sorted array (Bloom: Analyze)"
    `[4,5,6,7,0,1,2]` 에서 `0` 찾기. 정렬돼 있지만 회전. Binary search?

    ??? success "정답"
        가능. _Mid 가 어느 정렬 partition_ 결정:
        ```
        if (arr[lo] <= arr[mid]):  # 왼쪽 partition 정렬됨
            if (arr[lo] <= target < arr[mid]):  # target 이 왼쪽에
                hi = mid - 1
            else:
                lo = mid + 1
        else:  # 오른쪽 partition 정렬됨
            ...
        ```
        O(log N). _완전 정렬 가정_ binary search 의 변형.

!!! question "🤔 Q2 — Monotonic stack 의 적용 (Bloom: Apply)"
    "Daily Temperatures" — 매 day 마다 _다음 더 따뜻한 day 까지 며칠_?

    ??? success "정답"
        ```python
        stack = []  # index 의 stack, temps 가 decreasing
        result = [0] * len(temps)
        for i, t in enumerate(temps):
            while stack and temps[stack[-1]] < t:
                j = stack.pop()
                result[j] = i - j
            stack.append(i)
        ```
        O(N) amortized. Stack 안의 index 의 _temps decreasing 한 성질_ 유지.

### 7.2 출처

**External**
- *Introduction to Algorithms* — CLRS
- LeetCode patterns: Monotonic Stack, Binary Search

---

## 다음 모듈

→ [Module 05 — Tree & BFS/DFS](05_tree_bfs_dfs_explained.md): 재귀 stack 의 가장 자연스러운 응용 — 트리 탐색 + 명시적 큐 BFS.

[퀴즈 풀어보기 →](quiz/04_stack_binary_search_explained_quiz.md)

<div class="chapter-nav">
  <a class="nav-prev" href="../03_two_pointers_sliding_window_explained/">
    <div class="nav-label">◀ 이전</div>
    <div class="nav-title">Two Pointers & Sliding Window</div>
  </a>
  <a class="nav-next" href="../05_tree_bfs_dfs_explained/">
    <div class="nav-label">다음 ▶</div>
    <div class="nav-title">Tree & BFS/DFS</div>
  </a>
</div>


--8<-- "abbreviations.md"
