# Module 04 — Stack & Binary Search

## 학습 목표 (Learning Objectives)

이 모듈을 마치면:

1. (Remember) Stack push/pop 의 LIFO 원리와 Binary Search 의 lower_bound / upper_bound 차이를 적을 수 있다.
2. (Understand) Monotonic Stack 이 왜 "다음 큰 원소" 류 문제를 O(N) 으로 푸는지 설명할 수 있다.
3. (Apply) Valid Parentheses, Daily Temperatures, Search-in-Rotated-Array 같은 전형 문제를 풀 수 있다.
4. (Analyze) Binary Search 변형(범위, parametric search) 을 invariant 로 정형화할 수 있다.
5. (Evaluate) Stack vs Recursion / Binary Search vs Hash 의 trade-off 를 비교할 수 있다.

## 선수 지식 (Prerequisites)

- Module 01–03
- 재귀와 반복의 동등성 직관

## 왜 이 모듈이 중요한가 (Why it matters)

Stack 은 **이전 상태를 미루어 두었다 다시 쓰는** 가장 단순하지만 강력한 도구이고, Binary Search 는 **단조성(monotonicity)** 만 있다면 어디든 통하는 보편적 패턴이다. 이 둘을 패턴으로 익히면 면접에서 "이게 stack/이진 탐색 문제인지" 를 인지하는 시간이 크게 줄어든다.

---

## Stack — 언제 사용하는가?

```
키워드: "가장 최근", "매칭 쌍", "중첩", "되돌리기"
원리: LIFO (Last In, First Out) — 마지막에 넣은 것을 먼저 꺼냄

SV 구현: queue + push_back / pop_back / [$]로 top 접근
```

### Valid Parentheses — Dry Run

```
문제: 괄호 문자열이 올바른지 판단
s = "([{}])"

  i=0: '(' → 여는 괄호 → push → stack: ['(']
  i=1: '[' → 여는 괄호 → push → stack: ['(', '[']
  i=2: '{' → 여는 괄호 → push → stack: ['(', '[', '{']
  i=3: '}' → 닫는 괄호 → top='{' → 매칭! pop → stack: ['(', '[']
  i=4: ']' → 닫는 괄호 → top='[' → 매칭! pop → stack: ['(']
  i=5: ')' → 닫는 괄호 → top='(' → 매칭! pop → stack: []
  
  stack 비어있음 → return 1 (올바름)

s = "([)]"
  i=0: '(' → push → ['(']
  i=1: '[' → push → ['(', '[']
  i=2: ')' → top='[' → 불일치! → return 0 (올바르지 않음)

왜 Stack인가?
  "가장 최근에 열린 괄호"와 매칭해야 하므로 → LIFO
```

### Monotonic Stack — Daily Temperatures (LeetCode #739)

```
핵심: "다음으로 큰/작은 원소까지의 거리" → Monotonic Stack
원리: Stack에 "아직 답을 못 찾은 인덱스"를 보관
      현재 값이 stack top보다 크면 → pop하며 답 기록
```

#### 사고 과정

```
문제: 각 날에 대해, 더 따뜻한 날까지 몇 일 기다려야 하는가?
      temperatures = [73, 74, 75, 71, 69, 72, 76, 73]
      출력:          [ 1,  1,  4,  2,  1,  1,  0,  0]

Brute Force O(n²): 각 날마다 오른쪽으로 스캔하여 더 큰 값 찾기
최적화: "아직 답을 못 찾은 날들"을 Stack에 보관
        새 날의 온도가 Stack top보다 높으면 → 답을 찾은 것!
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
  71 < temps[2]=75 → push만
  stack: [2, 3]

i=4: temp=69
  69 < temps[3]=71 → push만
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
  73 < temps[6]=76 → push만
  stack: [6, 7]

끝: stack에 남은 [6, 7]은 답이 없음 → result[6]=0, result[7]=0

result = [1, 1, 4, 2, 1, 1, 0, 0] ✓

시간 O(n): 각 인덱스는 push 1번, pop 최대 1번 → 총 2n 연산
공간 O(n): stack 최대 n개
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

---

## Binary Search — 언제 사용하는가?

```
조건: 정렬된 데이터에서 값을 찾는 문제
원리: 매번 탐색 범위를 절반으로 줄임 → O(log n)
키워드: "정렬됨", "검색", "삽입 위치", "최소/최대 만족 조건"
```

### Binary Search 3대 실수 (면접 킬러)

```
실수 1: while (left < right)     ← 틀림!
정답:   while (left <= right)    ← left == right일 때도 검사해야 함

실수 2: mid = (left + right) / 2      ← 오버플로!
정답:   mid = left + (right - left) / 2  ← 안전

실수 3: left = mid / right = mid       ← 무한 루프!
정답:   left = mid + 1 / right = mid - 1  ← 반드시 +1/-1
```

### Binary Search — Dry Run

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

  이때 left=3 = "6이 삽입되어야 할 위치" (Search Insert Position)
```

### Binary Search 변형 — 조건 만족하는 최소/최대

```
"최소 X를 찾아라 (조건 f(x)를 만족하는)" → Lower Bound

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

---

## 면접 팁

```
Stack 문제 인식: "가장 최근", "매칭", "중첩" → Stack
Binary Search 문제 인식: "정렬" + "찾기" → Binary Search

Binary Search 코딩 시:
  1. while (left <= right) — 등호 포함!
  2. mid = left + (right - left) / 2 — 오버플로 방지
  3. left = mid + 1, right = mid - 1 — ±1 필수

  이 세 가지를 "Binary Search 3원칙"으로 외우면 실수 방지
```


---

## 부록: SystemVerilog 예제 코드

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

## 핵심 정리 (Key Takeaways)

- **Stack** — LIFO. Bracket matching, monotonic stack 류 문제의 단골 도구.
- **Monotonic Stack** — "다음 큰/작은 원소" 류 문제를 O(N) 으로 푼다.
- **Binary Search 의 본질 = 단조성** — sorted 가 아니라 "조건 함수가 단조" 면 적용 가능 (parametric search).
- **lower_bound / upper_bound** 차이 명확히 — off-by-one 의 주요 원인.
- **재귀 vs Stack** — 깊이 큰 트리에서 재귀는 stack overflow 위험, 명시적 stack 으로 변환.

## 다음 단계 (Next Steps)

- 다음 모듈: [Tree & BFS/DFS →](../05_tree_bfs_dfs_explained/).
- 퀴즈: [Module 04 Quiz](../quiz/04_stack_binary_search_explained_quiz/) — 5문항.
- 실습: "Daily Temperatures", "Search-in-Rotated-Array", "Find Peak Element", "Median of Two Sorted Arrays" 풀이.

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
