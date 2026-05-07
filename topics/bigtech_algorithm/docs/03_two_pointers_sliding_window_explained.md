# Module 03 — Two Pointers & Sliding Window

## 학습 목표 (Learning Objectives)

이 모듈을 마치면:

1. (Remember) Two Pointers 와 Sliding Window 의 정의를 구분할 수 있다.
2. (Understand) 정렬된 배열에서 Two Pointers 가 O(N) 으로 가능한 이유를 설명할 수 있다.
3. (Apply) "최대 부분 합", "K-개 distinct 부분", "정렬된 배열 짝 찾기" 같은 전형 문제를 풀 수 있다.
4. (Analyze) Window 의 expand / shrink 조건을 invariant 로 명세할 수 있다.
5. (Evaluate) Two Pointers vs Hash Map vs Sorting 의 trade-off 를 비교 평가할 수 있다.

## 선수 지식 (Prerequisites)

- Module 01–02 (Big-O, Hash Map)
- 배열 인덱스 조작에 대한 자신감

## 왜 이 모듈이 중요한가 (Why it matters)

Two Pointers / Sliding Window 는 **메모리를 쓰지 않고 O(N) 으로** 푸는 강력한 도구다. Hash Map 으로 풀리는 많은 문제가 정렬 + Two Pointers 로 더 간결해지고, 부분 배열/문자열 문제는 거의 모두 sliding window 로 일반화된다.

---

## Two Pointers — 언제 사용하는가?

```
조건: 정렬된 배열 + 두 값의 관계(합, 차)를 찾는 문제
방법: 양 끝에서 시작, 조건에 따라 한쪽을 이동
복잡도: O(n) 시간, O(1) 공간

패턴 인식:
  "정렬된 배열에서 두 수의 합이 X인 쌍을 찾아라" → Two Pointers
  "정렬된 배열에서 차이가 K인 쌍이 있는가?" → Two Pointers (같은 방향)
```

### Two Sum (정렬 배열) — Dry Run

```
nums = [1, 3, 5, 7, 11], target = 12

  left=0, right=4: 1+11=12 == 12 → Found! [0, 4]

만약 target = 10:
  left=0, right=4: 1+11=12 > 10 → right-- (합이 너무 큼)
  left=0, right=3: 1+7=8 < 10   → left++ (합이 너무 작음)
  left=1, right=3: 3+7=10 == 10 → Found! [1, 3]

왜 동작하는가?
  합이 target보다 크면 → 큰 쪽(right)을 줄여야 → right--
  합이 target보다 작으면 → 작은 쪽(left)을 늘려야 → left++
  → 정렬되어 있으므로 이 이동이 올바른 방향을 보장
```

### 같은 방향 Two Pointers (차이 찾기)

```
nums = [1, 3, 5, 7, 11], diff = 6

  first=0, second=1: 3-1=2 < 6 → second++ (차이 부족)
  first=0, second=2: 5-1=4 < 6 → second++
  first=0, second=3: 7-1=6 == 6 → Found!

주의: while 조건은 "배열 범위 체크" (second < nums.size())
      포인터 비교 (first < second)가 아님!
```

---

## Sliding Window — 언제 사용하는가?

```
조건: "연속 부분 배열/부분 문자열"에 대한 문제
방법: 윈도우를 오른쪽으로 밀면서, 새 원소 추가 + 오래된 원소 제거

두 가지 유형:
  고정 크기: 크기 k인 윈도우 → 합/평균의 최대/최소
  가변 크기: 조건을 만족하는 가장 긴/짧은 부분 배열
```

### 고정 크기 Sliding Window — Dry Run

```
문제: 크기 k=3인 연속 부분 배열의 최대 합
nums = [2, 1, 5, 1, 3, 2]

Brute Force O(nk): 매번 k개 원소를 합산
  [2,1,5]=8, [1,5,1]=7, [5,1,3]=9, [1,3,2]=6 → 최대 9

Sliding Window O(n): 새 원소 추가 + 오래된 원소 제거
  초기 윈도우: [2,1,5] sum=8, max=8
  
  i=3: +nums[3] -nums[0] = +1-2 → sum=7, max=8
       윈도우: [1,5,1]

  i=4: +nums[4] -nums[1] = +3-1 → sum=9, max=9
       윈도우: [5,1,3]

  i=5: +nums[5] -nums[2] = +2-5 → sum=6, max=9
       윈도우: [1,3,2]

  답: 9  (O(n), 매 step에서 딱 2번의 연산)
```

### 가변 크기 Sliding Window — 패턴

```
핵심: right를 확장 → 조건 위반 시 left를 축소
용도: "조건을 만족하는 가장 긴/짧은 부분 배열/문자열"

가변 Sliding Window 템플릿:
  left = 0
  for right in range(n):
      window에 s[right] 추가
      while (window 조건 위반):
          window에서 s[left] 제거
          left++
      max_len = max(max_len, right - left + 1)
```

### Longest Substring Without Repeating Characters (LeetCode #3) — 완전 Dry Run

```
문제: 중복 없는 가장 긴 부분 문자열의 길이
s = "abcabcbb"

사고 과정:
  1. "연속 부분 문자열" + "가장 긴" → 가변 Sliding Window
  2. 조건 위반 = "윈도우 안에 중복 문자가 있음"
  3. Hash Map으로 각 문자의 마지막 위치를 추적

Dry Run (seen = 문자의 마지막 인덱스):
  left=0

  right=0: s[0]='a'
    seen에 'a' 없음 → seen['a']=0
    윈도우 "a", 길이=1, max=1

  right=1: s[1]='b'
    seen에 'b' 없음 → seen['b']=1
    윈도우 "ab", 길이=2, max=2

  right=2: s[2]='c'
    seen에 'c' 없음 → seen['c']=2
    윈도우 "abc", 길이=3, max=3

  right=3: s[3]='a'
    seen에 'a' 있음! seen['a']=0 ≥ left(0)
    → left = 0 + 1 = 1  (중복 'a' 다음으로 이동)
    → seen['a']=3
    윈도우 "bca", 길이=3, max=3

  right=4: s[4]='b'
    seen에 'b' 있음! seen['b']=1 ≥ left(1)
    → left = 1 + 1 = 2
    → seen['b']=4
    윈도우 "cab", 길이=3, max=3

  right=5: s[5]='c'
    seen에 'c' 있음! seen['c']=2 ≥ left(2)
    → left = 2 + 1 = 3
    → seen['c']=5
    윈도우 "abc", 길이=3, max=3

  right=6: s[6]='b'
    seen에 'b' 있음! seen['b']=4 ≥ left(3)
    → left = 4 + 1 = 5
    → seen['b']=6
    윈도우 "cb", 길이=2, max=3

  right=7: s[7]='b'
    seen에 'b' 있음! seen['b']=6 ≥ left(5)
    → left = 6 + 1 = 7
    → seen['b']=7
    윈도우 "b", 길이=1, max=3

  답: 3

핵심 포인트:
  - seen[char] >= left 체크가 중요 — 윈도우 밖의 오래된 기록은 무시
  - left는 항상 전진만 함 (후퇴하면 이미 제거한 문자를 다시 포함하게 됨)
```

### 가변 Window — 다른 활용

```
"합이 target 이상인 가장 짧은 부분 배열" (Minimum Size Subarray Sum #209)
  → 조건 위반 = "합 < target" → right 확장
  → 조건 만족 = "합 >= target" → left 축소하며 최소 길이 갱신

"최대 k개의 서로 다른 문자를 포함하는 가장 긴 부분 문자열"
  → 조건 위반 = "서로 다른 문자 > k" → left 축소
```

---

## 면접 팁

**Two Pointers vs Hash Map 선택:**
```
정렬 가능 + 두 값 관계 → Two Pointers (O(1) 공간)
정렬 불가 + 두 값 관계 → Hash Map (O(n) 공간)

면접에서: "정렬 가능한가요?" 질문으로 어떤 패턴을 쓸지 결정
```

**Sliding Window 키워드:** "연속", "부분 배열", "부분 문자열", "최대/최소 길이"


---

## 부록: SystemVerilog 예제 코드

원본 파일: `03_two_pointers_sliding_window.sv`

```systemverilog
// =============================================================
// Unit 3: Two Pointers & Sliding Window
// =============================================================
// Two Pointers:
//   - Sorted array + find pair relationship -> Two Pointers
//   - Two pointers move based on condition (too big/too small)
//   - O(n) time, O(1) space
//   - IMPORTANT: while condition = ARRAY BOUNDS CHECK, not pointer comparison
//
// Sliding Window:
//   - "Continuous subarray/substring" -> Sliding Window
//   - Fixed window: add new, remove old
//   - Variable window: expand right, shrink left
//   - O(n) time
// =============================================================

module unit3_tp_sw;

  // ---------------------------------------------------------
  // Two Sum (sorted array): two pointers from both ends
  // ---------------------------------------------------------
  function automatic void two_sum_sorted(int nums[], int target);
    int left  = 0;
    int right = nums.size() - 1;

    while (left < right) begin
      int sum = nums[left] + nums[right];

      if (sum == target) begin
        $display("Found: [%0d, %0d]", left, right);
        return;
      end
      else if (sum < target)
        left++;      // need bigger sum -> move left forward
      else
        right--;     // need smaller sum -> move right backward
    end
    $display("Not found");
  endfunction

  // ---------------------------------------------------------
  // Find Diff: two pointers both starting from left
  // IMPORTANT: while checks ARRAY BOUNDS, not pointer relation
  // ---------------------------------------------------------
  function automatic bit has_diff(int nums[], int diff);
    int first  = 0;
    int second = 1;

    while (second < nums.size()) begin       // bounds check!
      if (first == second) begin             // same element guard
        second++;
        continue;
      end

      int result = nums[second] - nums[first];

      if (result == diff)
        return 1;
      else if (result > diff)
        first++;
      else
        second++;
    end
    return 0;
  endfunction

  // ---------------------------------------------------------
  // Max Subarray Sum (fixed window size k): Sliding Window
  // Instead of recalculating k elements each time,
  // add the new element and remove the old one -> O(n)
  // ---------------------------------------------------------
  function automatic int max_sum_window(int nums[], int k);
    int window_sum = 0;
    int max_val;

    // First window
    for (int i = 0; i < k; i++)
      window_sum += nums[i];
    max_val = window_sum;

    // Slide: +new -old
    for (int i = k; i < nums.size(); i++) begin
      window_sum += nums[i];         // new element enters
      window_sum -= nums[i - k];     // old element leaves
      if (window_sum > max_val)
        max_val = window_sum;
    end
    return max_val;
  endfunction

  // ---------------------------------------------------------
  // Longest Substring Without Repeating Characters (LeetCode #3)
  // Variable Sliding Window: expand right, shrink left on violation
  //   - seen[char] tracks last index of each character
  //   - When duplicate found IN window (seen[c] >= left):
  //     move left past the duplicate
  // ---------------------------------------------------------
  function automatic int longest_unique_substr(string s);
    int seen[byte];   // {character: last_index}
    int left    = 0;
    int max_len = 0;

    for (int right = 0; right < s.len(); right++) begin
      byte c = s[right];

      // If char was seen and is inside current window
      if (seen.exists(c) && seen[c] >= left)
        left = seen[c] + 1;  // shrink: move past duplicate

      seen[c] = right;       // update last seen position

      if (right - left + 1 > max_len)
        max_len = right - left + 1;
    end
    return max_len;
  endfunction

  // ---------------------------------------------------------
  // Test
  // ---------------------------------------------------------
  initial begin
    int sorted[] = '{1, 3, 5, 7, 11};
    two_sum_sorted(sorted, 12);      // Expected: Found: [0, 4]

    $display("has_diff(7): %0b", has_diff(sorted, 7));  // Expected: 1
    $display("has_diff(6): %0b", has_diff(sorted, 6));  // Expected: 0

    int arr[] = '{2, 1, 5, 1, 3, 2};
    $display("max_sum(k=3): %0d", max_sum_window(arr, 3)); // Expected: 9

    $display("longest(abcabcbb): %0d", longest_unique_substr("abcabcbb")); // 3
    $display("longest(bbbbb): %0d",    longest_unique_substr("bbbbb"));    // 1
    $display("longest(pwwkew): %0d",   longest_unique_substr("pwwkew"));   // 3
  end

endmodule

```

---

!!! danger "❓ 흔한 오해"
    **오해**: Two Pointers / Sliding Window 는 같은 패턴

    **실제**: Two Pointers = 양방향 좁힘 (보통 정렬된 입력), Sliding Window = invariant 유지 expand/shrink. 입력 조건과 invariant 가 다른 패턴.

    **왜 헷갈리는가**: 둘 다 "포인터 두 개" 사용 → 시각적 유사성 때문에 같은 것으로 묶임.

!!! warning "실무 주의점 — while 조건의 off-by-one (`lo<hi` vs `lo<=hi`)"
    **현상**: 정렬된 배열의 two-sum 에서 `[a, a]` 같은 동일 원소 두 번 사용 케이스를 놓치거나, 반대로 같은 인덱스를 두 번 더해 false positive 가 난다.

    **원인**: `lo < hi` (서로 다른 두 인덱스) 와 `lo <= hi` (자기 자신 허용) 의 의미 차이를 명세 없이 한 쪽으로 결정한 결과. invariant 가 글로 적혀 있지 않으면 매번 흔들린다.

    **점검 포인트**: "두 포인터가 가리키는 인덱스가 서로 달라야 하는가" 를 문제 제약과 맞춰 한 줄로 적었는가, 그리고 양 끝/싱글톤/중복 입력에 dry-run 했는가.

!!! tip "💡 이해를 위한 비유"
    **Two Pointers / Sliding Window** ≈ **양 끝에서 좁혀가는 사진 trim / 신축 가능한 봉투**

    정렬된 배열의 양끝에서 좁히기 (Two Pointers) 또는 연속 부분 invariant 유지 (Sliding Window). hash map 없이 O(N).

---

## 핵심 정리 (Key Takeaways)

- **Two Pointers** — 보통 정렬된 배열 / 양 끝에서 좁혀가는 구조.
- **Sliding Window** — 부분 배열/문자열의 invariant 유지 (window expand → 조건 위반 → shrink).
- **Window 조건의 명세** — invariant 를 글로 적어 보면 버그가 줄어든다.
- **메모리 ↓** — hash map 풀이 대비 공간을 거의 쓰지 않는다.
- **정렬 비용 고려** — 입력이 정렬 가능하면 O(N log N) + O(N) 이 hash map 의 O(N) 보다 종종 깔끔.

## 다음 단계 (Next Steps)

- 다음 모듈: [Stack & Binary Search →](../04_stack_binary_search_explained/) — 정렬된 배열의 또 다른 도구.
- 퀴즈: [Module 03 Quiz](../quiz/03_two_pointers_sliding_window_explained_quiz/) — 5문항.
- 실습: "Longest Substring Without Repeating", "Minimum Window Substring", "3Sum" 을 모두 풀고 invariant 를 주석으로 적는다.

<div class="chapter-nav">
  <a class="nav-prev" href="../02_array_hashmap_explained/">
    <div class="nav-label">◀ 이전</div>
    <div class="nav-title">Array & Hash Map (연관 배열)</div>
  </a>
  <a class="nav-next" href="../04_stack_binary_search_explained/">
    <div class="nav-label">다음 ▶</div>
    <div class="nav-title">Stack & Binary Search</div>
  </a>
</div>
