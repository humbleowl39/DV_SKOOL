# Module 01 — Big-O Complexity & Pattern Thinking

<!-- DV-SKOOL-CH-CTX:start -->
<div class="chapter-context" data-cat="applied">
  <a class="chapter-back" href="../">
    <span class="chapter-back-arrow">←</span>
    <span class="chapter-back-icon">📐</span>
    <span class="chapter-back-text">BigTech Algorithm</span>
  </a>
  <span class="chapter-divider">›</span>
  <span class="chapter-marker">Module 01</span>
</div>
<!-- DV-SKOOL-CH-CTX:end -->

<!-- DV-SKOOL-CH-TOC:start -->
<div class="page-toc">
  <span class="page-toc-label">목차</span>
  <a class="page-toc-link" href="#학습-목표">학습 목표</a>
  <a class="page-toc-link" href="#선수-지식">선수 지식</a>
  <a class="page-toc-link" href="#왜-이-모듈이-중요한가">왜 이 모듈이 중요한가</a>
  <a class="page-toc-link" href="#왜-패턴인가">왜 패턴인가?</a>
  <a class="page-toc-link" href="#big-o-빠른-참조">Big-O 빠른 참조</a>
  <a class="page-toc-link" href="#brute-force-최적화-사고법">Brute Force → 최적화 사고법</a>
  <a class="page-toc-link" href="#공간-복잡도-space-complexity">공간 복잡도 (Space Complexity)</a>
  <a class="page-toc-link" href="#dry-run-예시-코드-01_big_osv-참조">Dry Run 예시 (코드 01_big_o.sv 참조)</a>
  <a class="page-toc-link" href="#부록-systemverilog-예제-코드">부록: SystemVerilog 예제 코드</a>
  <a class="page-toc-link" href="#핵심-정리">핵심 정리</a>
  <a class="page-toc-link" href="#다음-단계">다음 단계</a>
</div>
<!-- DV-SKOOL-CH-TOC:end -->

## 학습 목표

이 모듈을 마치면:

1. (Remember) O(1), O(log N), O(N), O(N log N), O(N²) 의 의미와 대표 알고리즘을 매핑할 수 있다.
2. (Understand) Time / Space complexity 가 입력 크기 N 의 함수로 어떻게 증가하는지 설명할 수 있다.
3. (Apply) 주어진 코드 한 함수의 worst-case 시간/공간 복잡도를 손으로 계산할 수 있다.
4. (Analyze) "패턴 사고법" 의 5단계 (입력→제약→패턴 매핑→복잡도→코드) 를 새 문제에 적용할 수 있다.
5. (Evaluate) 두 가지 풀이의 복잡도와 가독성/엣지케이스 측면을 비교 평가할 수 있다.

## 선수 지식

- 배열 / 반복문 / 함수 호출 같은 기초 프로그래밍 개념
- 로그·지수의 기본 직관

## 왜 이 모듈이 중요한가

빅테크 코딩 인터뷰의 핵심 평가 기준은 **올바른 복잡도** + **올바른 패턴 선택** 이다. Big-O 직관이 없으면 매번 처음부터 풀이를 만들어야 하지만, 입력 크기를 보고 "이건 N log N 안에 풀려야 하니 정렬 + 이진 탐색 패턴이다" 라고 매핑할 수 있으면 풀이의 절반은 끝난 것이다.

---

## 왜 패턴인가?

```
LeetCode 2000+ 문제를 다 풀 수 없다.
그러나 대부분의 면접 문제는 10~12개 패턴의 변형이다.

패턴을 알면:
  문제 → "이건 Two Pointers 패턴이군" → 템플릿 적용 → 해결

패턴을 모르면:
  문제 → "음... 이중 루프?" → O(n²) → "더 빠르게?" → 막힘
```

## Big-O 빠른 참조

| 복잡도 | 이름 | 예시 | n=10⁶일 때 |
|--------|------|------|-----------|
| O(1) | 상수 | 배열 인덱스 접근 | 1 연산 |
| O(log n) | 로그 | Binary Search | ~20 연산 |
| O(n) | 선형 | 단일 루프 | 10⁶ 연산 |
| O(n log n) | 선형 로그 | 효율적 정렬 (Merge Sort) | ~2×10⁷ 연산 |
| O(n²) | 이차 | 이중 루프 ← **최적화 대상** | 10¹² 연산 (TLE!) |
| O(2ⁿ) | 지수 | 모든 부분집합 ← **피해야 함** | 천문학적 |

### 입력 크기로 필요 복잡도 역산

| n | 허용 복잡도 | 대표 패턴 |
|---|-----------|----------|
| ≤ 20 | O(2ⁿ) | Backtracking, 완전 탐색 |
| ≤ 1,000 | O(n²) | Brute Force OK |
| ≤ 100,000 | O(n log n) | 정렬 + Binary Search |
| ≤ 1,000,000 | O(n) | Hash Map, Two Pointers, Sliding Window |

**면접 팁**: 문제의 입력 크기를 먼저 확인하라. n=10⁵이면 O(n²)은 안 된다 → O(n) 또는 O(n log n) 패턴을 찾아야 한다.

## Brute Force → 최적화 사고법

```
1단계: Brute Force (무식한 방법)
  "이 문제를 가장 단순하게 푸는 방법은?"
  → 대부분 이중 루프 O(n²)

2단계: 비효율 분석
  "어디서 반복 작업을 하고 있는가?"
  → "내부 루프에서 매번 처음부터 검색하고 있다"

3단계: 패턴 적용
  "이 반복 검색을 제거할 수 있는가?"
  → Hash Map으로 O(1) 검색 → O(n)

예시: Two Sum
  Brute: 모든 쌍 확인 → O(n²)
  분석:  내부 루프가 "complement 존재?" 검색
  최적화: Hash Map에 저장 → exists()로 O(1) 검색 → 전체 O(n)
```

## 공간 복잡도 (Space Complexity)

```
면접에서 "시간/공간 복잡도를 분석해주세요" → 둘 다 대답해야 한다!

시간 복잡도: 연산 횟수가 입력 크기에 따라 어떻게 증가하는가?
공간 복잡도: 추가로 사용하는 메모리가 입력 크기에 따라 어떻게 증가하는가?
            (입력 자체는 제외하고, "추가" 메모리만 카운트)
```

| 공간 복잡도 | 의미 | 예시 |
|------------|------|------|
| O(1) | 변수 몇 개만 사용 | Two Pointers, 변수 swap |
| O(n) | 입력 크기만큼 추가 배열/해시맵 | Hash Map, DP 배열 |
| O(h) | 트리 높이만큼 (재귀 스택) | DFS 재귀 |
| O(n²) | 2차원 배열 | 2D DP 테이블 |

### 패턴별 공간 복잡도 정리

```
O(1) 공간 패턴: Two Pointers, Binary Search, 공간 최적화 DP
O(n) 공간 패턴: Hash Map, Stack, 일반 DP, BFS 큐
O(h) 공간 패턴: DFS 재귀 (h = 트리 높이, 최악 O(n))

면접 팁: "공간 복잡도도 O(1)로 줄일 수 있습니다"라고 말하면 보너스 점수
  예: DP에서 배열 대신 변수 2개 사용 (Unit 6 참조)
  예: Two Pointers는 Hash Map 대신 O(1) 공간 (정렬 가능한 경우)
```

### Dry Run으로 공간 복잡도 비교

```
문제: 배열에서 합이 target인 두 수 찾기

방법 1: Hash Map → 시간 O(n), 공간 O(n)
  추가 메모리: seen[int] 연관 배열 → 최악 n개 저장

방법 2: 정렬 + Two Pointers → 시간 O(n log n), 공간 O(1)
  추가 메모리: left, right 변수 2개만

면접에서 비교를 언급하면:
  "Hash Map은 O(n) 시간, O(n) 공간입니다.
   정렬이 가능하다면 Two Pointers로 O(n log n) 시간, O(1) 공간도 가능합니다.
   시간과 공간의 trade-off입니다."
```

---

## Dry Run 예시 (코드 01_big_o.sv 참조)

### O(n) — 단일 루프

```
sum_array([2, 7, 11, 15]):
  i=0: total = 0 + 2 = 2
  i=1: total = 2 + 7 = 9
  i=2: total = 9 + 11 = 20
  i=3: total = 20 + 15 = 35
  return 35   ← O(n) 시간, O(1) 공간 (변수 total만 사용)
```

### O(n²) — 이중 루프

```
find_pair_brute([2,7,11,15], target=9):
  i=0, j=1: 2+7=9 == 9 → Found! [0, 1]
  → O(n²) 시간, 최악 n(n-1)/2번 비교
  → O(1) 공간 (추가 메모리 없음)
  → Hash Map으로 O(n) 시간, O(n) 공간에 가능 (Unit 2)
```

### O(log n) — 반씩 줄이기

```
binary_search_simple([1, 3, 5, 7, 9, 11, 13], target=9):
  left=0, right=6
  
  반복 1: mid=3, nums[3]=7 < 9  → left=4  (왼쪽 절반 제거)
  반복 2: mid=5, nums[5]=11 > 9 → right=4 (오른쪽 절반 제거)
  반복 3: mid=4, nums[4]=9 == 9 → Found!
  
  → 7개 원소에서 3번만에 찾음
  → O(log n) 시간, O(1) 공간

왜 O(log n)인가?
  n=7 → 3번 (2³=8 ≥ 7)
  n=100 → 7번 (2⁷=128 ≥ 100)
  n=1,000,000 → 20번 (2²⁰=1,048,576 ≥ 1,000,000)
  → 매번 절반을 제거하므로 log₂(n)번이면 충분
```

---

## 부록: SystemVerilog 예제 코드

원본 파일: `01_big_o.sv`

```systemverilog
// =============================================================
// Unit 1: Why Patterns? + Big-O Complexity
// =============================================================
// Key Insight: 87% of interview questions use only 10-12 patterns.
//   - Don't memorize 500 problems. Master 10 patterns.
//   - Always start with brute force, then optimize.
//   - Interviewers evaluate THINKING PROCESS, not just the answer.
//
// Big-O Quick Reference:
//   O(1)       - constant    : array index access
//   O(log n)   - logarithmic : binary search
//   O(n)       - linear      : single loop
//   O(n log n) - linearithmic: efficient sort
//   O(n^2)     - quadratic   : nested loops  <-- optimize this!
//   O(2^n)     - exponential : all subsets    <-- avoid!
//
// Space Complexity (interview asks BOTH time and space!):
//   O(1) space : Two Pointers, Binary Search, optimized DP
//   O(n) space : Hash Map, Stack, DP array, BFS queue
//   O(h) space : DFS recursion (h = tree height, worst O(n))
// =============================================================

module unit1_big_o;

  // ---------------------------------------------------------
  // O(n) time, O(1) space - Single loop
  // ---------------------------------------------------------
  function automatic int sum_array(int nums[]);
    int total = 0;
    foreach (nums[i])
      total += nums[i];
    return total;
  endfunction

  // ---------------------------------------------------------
  // O(n^2) time, O(1) space - Nested loop: slow, needs optimization
  // The inner loop searches "does complement exist?" every time
  // -> This repeated search is what we optimize with Hash Map
  // ---------------------------------------------------------
  function automatic void find_pair_brute(int nums[], int target);
    for (int i = 0; i < nums.size(); i++)
      for (int j = i + 1; j < nums.size(); j++)
        if (nums[i] + nums[j] == target) begin
          $display("Brute: Found [%0d, %0d] = %0d + %0d", i, j, nums[i], nums[j]);
          return;
        end
    $display("Brute: Not found");
  endfunction

  // ---------------------------------------------------------
  // O(log n) time, O(1) space - Halving each time
  // Every iteration eliminates half the search space
  // n=1,000,000 -> only ~20 comparisons needed
  // (Full template with edge cases in Unit 4)
  // ---------------------------------------------------------
  function automatic int binary_search_simple(int nums[], int target);
    int left  = 0;
    int right = nums.size() - 1;

    while (left <= right) begin
      int mid = left + (right - left) / 2;  // overflow-safe

      if (nums[mid] == target)
        return mid;
      else if (nums[mid] < target)
        left = mid + 1;   // discard left half
      else
        right = mid - 1;  // discard right half
    end
    return -1;
  endfunction

  // ---------------------------------------------------------
  // O(n) time, O(n) space - Uses hash map (extra memory)
  // Compare: brute force is O(n^2) time O(1) space
  //          hash map is   O(n)   time O(n) space <- trade-off!
  // (Full explanation in Unit 2)
  // ---------------------------------------------------------
  function automatic void find_pair_hashmap(int nums[], int target);
    int seen[int];

    for (int i = 0; i < nums.size(); i++) begin
      int complement = target - nums[i];
      if (seen.exists(complement)) begin
        $display("HashMap: Found [%0d, %0d] = %0d + %0d",
                 seen[complement], i, nums[complement], nums[i]);
        return;
      end
      seen[nums[i]] = i;
    end
    $display("HashMap: Not found");
  endfunction

  // ---------------------------------------------------------
  // Test: compare all complexities on the same problem
  // ---------------------------------------------------------
  initial begin
    int arr[] = '{2, 7, 11, 15};

    $display("=== O(n) : sum_array ===");
    $display("sum = %0d", sum_array(arr));  // 35

    $display("");
    $display("=== O(n^2) vs O(n) : find pair sum=9 ===");
    find_pair_brute(arr, 9);    // O(n^2) time, O(1) space
    find_pair_hashmap(arr, 9);  // O(n)   time, O(n) space

    $display("");
    $display("=== O(log n) : binary search ===");
    int sorted[] = '{1, 3, 5, 7, 9, 11, 13};
    $display("search  9: index=%0d", binary_search_simple(sorted, 9));   // 4
    $display("search  6: index=%0d", binary_search_simple(sorted, 6));   // -1
    $display("search  1: index=%0d", binary_search_simple(sorted, 1));   // 0
    $display("search 13: index=%0d", binary_search_simple(sorted, 13));  // 6
  end

endmodule

```

---
!!! warning "실무 주의점 — Amortized vs Worst-Case 혼동"
    **현상**: `vector::push_back` 을 N 번 호출하는 루프를 O(N) 이라 적었는데, 면접관이 "한 번 호출의 worst-case 는?" 이라고 되묻자 답이 막힌다.

    **원인**: amortized O(1) 과 single-call worst-case O(N) (재할당 시점) 을 동일시한 것. 평균과 최악을 분리해서 보지 않음.

    **점검 포인트**: 자료구조의 연산 비용이 amortized 인지 worst-case 인지 명시했는가, 그리고 "면접 기본은 worst-case" 기준으로 다시 합산했는가.

!!! tip "💡 이해를 위한 비유"
    **Big-O** ≈ **운동 능력 측정 — 짐 무게(N) 가 늘 때 시간이 어떻게 늘어나는가**

    고정된 횟수 (O(1)) vs 짐 비례 (O(N)) vs 짐의 제곱 (O(N²)). N 이 작을 땐 차이 미미하지만 N=10⁶ 가 되면 우주의 시간.

---

!!! danger "❓ 흔한 오해"
    **오해**: O(1) = 무조건 빠름

    **실제**: O(1) 이라도 그 상수가 클 수 있음 (예: hash map insert 의 hash 계산 + collision 처리). N 이 작으면 O(N) 이 더 빠를 수도.

    **왜 헷갈리는가**: "상수 = 작음" 이라는 직관 + 학교에서 "O(1) > O(N)" 만 강조한 학습 패턴.

## 핵심 정리

- **상수항 / 하한 항 무시** — 입력이 커질수록 지배 항(highest order) 만 살아남는다.
- **N 의 크기로 패턴이 정해진다** — N≤10 → 백트래킹, N≤10⁴ → O(N²), N≤10⁶ → O(N log N), N≤10⁹ → O(log N) 또는 수학.
- **Best / Average / Worst** 는 다르다 — 면접에서는 worst case 가 기본.
- **공간 복잡도** 도 동일 분석 — 재귀 호출 stack 도 공간이다.
- **패턴 사고법** 으로 30초 안에 후보 알고리즘 군을 좁힌다.

## 다음 단계

- 다음 모듈: [Array & Hash Map →](../02_array_hashmap_explained/) — 가장 자주 등장하는 자료구조 패턴.
- 퀴즈: [Module 01 Quiz](../quiz/01_big_o_explained_quiz/) — Big-O, 패턴 매핑 5문항.
- 실습: 평소 푸는 LeetCode 5문제를 풀기 전, 입력 제약만 보고 "후보 패턴 → 목표 복잡도" 를 적어 본 뒤 풀이와 비교한다.

<div class="chapter-nav">
  <a class="nav-prev" href="../">
    <div class="nav-label">◀ 이전</div>
    <div class="nav-title">코스 홈</div>
  </a>
  <a class="nav-next" href="../02_array_hashmap_explained/">
    <div class="nav-label">다음 ▶</div>
    <div class="nav-title">Array & Hash Map (연관 배열)</div>
  </a>
</div>


--8<-- "abbreviations.md"
