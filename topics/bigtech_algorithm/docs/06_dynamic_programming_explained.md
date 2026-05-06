# Module 06 — Dynamic Programming

## 학습 목표 (Learning Objectives)

이 모듈을 마치면:

1. (Remember) DP 의 두 조건(Optimal Substructure, Overlapping Subproblems) 을 정의할 수 있다.
2. (Understand) Top-down (memoization) 과 Bottom-up (tabulation) 을 비교 설명할 수 있다.
3. (Apply) 1D DP (Climbing Stairs, House Robber), 2D DP (LCS, Edit Distance) 를 구현할 수 있다.
4. (Analyze) DP 의 state 정의가 잘못된 경우의 증상(중복 / 무한 / 답 누락) 을 진단할 수 있다.
5. (Evaluate) 같은 문제에 DP / Greedy / DFS+memo 의 trade-off 를 평가할 수 있다.

## 선수 지식 (Prerequisites)

- Module 01–05
- 재귀 + memoization 한 번이라도 작성한 경험

## 왜 이 모듈이 중요한가 (Why it matters)

DP 는 면접관이 reasoning depth 를 가장 좋아하는 패턴이다. 상태 정의 → 점화식 → 베이스 케이스 → 구현 → 최적화 의 다섯 단계 표준 풀이를 만들 수 있으면 거의 모든 DP 문제를 풀 수 있다. 또한 운영 코드(parsing, scoring, scheduling) 에서도 자주 등장한다.

---

## DP란?

```
DP = 큰 문제를 작은 부분 문제로 나누고, 결과를 저장하여 재사용

DP가 적용되는 2가지 조건:
  1. 최적 부분 구조: 큰 답 = 작은 답들의 조합
  2. 중복 부분 문제: 같은 작은 문제가 여러 번 계산됨

키워드: "경우의 수", "최소 비용", "최대 값", "가능한가?", "이전 선택이 다음에 영향"
```

## DP 3단계 공식 (모든 DP 문제에 적용)

```
1단계: 상태 정의   → dp[i]는 무엇을 의미하는가?
2단계: 점화식      → dp[i] = f(dp[i-1], dp[i-2], ...)
3단계: 기저 조건   → dp[0] = ?, dp[1] = ?

이 3단계를 먼저 정의하고 코드를 작성하라!
코드부터 쓰면 길을 잃는다.
```

## 구현 방식

| 방식 | 원리 | 장단점 |
|------|------|--------|
| Top-down (메모이제이션) | 재귀 + 캐시 | 생각하기 쉬움, 스택 오버플로 위험 |
| **Bottom-up (테이블)** | for 루프 | **면접 선호**, 스택 안전, 공간 최적화 가능 |

```
Top-down:
  function fib(n, memo):
      if memo[n] exists: return memo[n]  // 캐시 히트
      memo[n] = fib(n-1) + fib(n-2)     // 계산 + 저장
      return memo[n]

Bottom-up (면접 선호):
  dp[0] = 0; dp[1] = 1;
  for (i = 2; i <= n; i++):
      dp[i] = dp[i-1] + dp[i-2];
  return dp[n];
```

---

## Climbing Stairs — 대표 문제 Dry Run

```
문제: 1칸 또는 2칸씩 올라갈 수 있다. n번째 계단에 도달하는 경우의 수는?

3단계:
  1. dp[i] = i번째 계단에 도달하는 경우의 수
  2. dp[i] = dp[i-1] + dp[i-2]
     (i-1에서 1칸 올라오기) + (i-2에서 2칸 올라오기)
  3. dp[0] = 1, dp[1] = 1

n = 5:
  dp[0]=1, dp[1]=1
  dp[2] = dp[1] + dp[0] = 1+1 = 2
  dp[3] = dp[2] + dp[1] = 2+1 = 3
  dp[4] = dp[3] + dp[2] = 3+2 = 5
  dp[5] = dp[4] + dp[3] = 5+3 = 8  ← 답

경우들: 11111, 1112, 1121, 1211, 2111, 122, 212, 221 = 8가지
```

### 공간 최적화 (면접 보너스)

```
dp[i]가 dp[i-1]과 dp[i-2]에만 의존
→ 배열 전체가 아닌 변수 2개만으로 충분!

prev2 = 1 (dp[i-2])
prev1 = 1 (dp[i-1])

i=2: curr = 1+1=2, prev2=1, prev1=2
i=3: curr = 2+1=3, prev2=2, prev1=3
i=4: curr = 3+2=5, prev2=3, prev1=5
i=5: curr = 5+3=8

→ O(n) 시간, O(1) 공간 (배열 O(n) → 변수 O(1))
→ 면접에서 "공간 최적화도 할 수 있다"고 말하면 보너스 점수
```

---

## House Robber — Dry Run

```
문제: 인접한 집은 동시에 털 수 없다. 최대 금액은?

3단계:
  1. dp[i] = i번째 집까지 고려했을 때 최대 금액
  2. dp[i] = max(dp[i-1],              ← i번째 집 건너뛰기
                 dp[i-2] + houses[i])   ← i번째 집 털기
  3. dp[0] = houses[0]
     dp[1] = max(houses[0], houses[1])

houses = [2, 7, 9, 3, 1]:
  dp[0] = 2
  dp[1] = max(2, 7) = 7
  dp[2] = max(7, 2+9) = max(7, 11) = 11
  dp[3] = max(11, 7+3) = max(11, 10) = 11
  dp[4] = max(11, 11+1) = 12  ← 답

선택: 집0(2) + 집2(9) + 집4(1) = 12
또는: 집1(7) + 집3(3) = 10 (차선)
```

---

## DP 유형별 키워드

| 키워드 | DP 유형 | 대표 문제 |
|--------|---------|----------|
| "경우의 수" | Counting DP | Climbing Stairs, Unique Paths |
| "최소 비용" | Optimization DP | Min Cost Stairs, Coin Change |
| "최대 값" | Optimization DP | House Robber, Maximum Subarray |
| "가능한가?" | Boolean DP | Word Break, Partition Equal Subset |
| "가장 긴" | LIS/LCS | Longest Increasing Subsequence |

---

## 면접 팁

```
DP 문제를 받으면:

1. "이 문제가 DP인가?" 판단
   → 이전 선택이 다음에 영향? → YES → DP
   → 최대/최소/경우의 수? → 아마 DP

2. 3단계 공식을 먼저 말하기 (코드 전에!)
   "dp[i]는 ~을 의미합니다"
   "점화식은 dp[i] = max(dp[i-1], dp[i-2] + val) 입니다"
   "기저 조건은 dp[0]=X, dp[1]=Y 입니다"

3. Bottom-up으로 코딩
   → for 루프가 면접에서 선호 (재귀보다 안전)

4. 공간 최적화 언급 (보너스)
   "dp[i]가 dp[i-1], dp[i-2]에만 의존하므로 변수 2개로 줄일 수 있습니다"
```


---

## 부록: SystemVerilog 예제 코드

원본 파일: `06_dynamic_programming.sv`

```systemverilog
// =============================================================
// Unit 6: Dynamic Programming (DP)
// =============================================================
// Key Insight: DP = save and reuse sub-problem results
//
// 3-Step Formula (apply to EVERY DP problem):
//   Step 1: Define state   -> dp[i] means what?
//   Step 2: Recurrence     -> dp[i] = f(dp[i-1], dp[i-2], ...)
//   Step 3: Base case      -> dp[0] = ?, dp[1] = ?
//
// Two conditions for DP:
//   1. Optimal substructure: big answer = combination of small answers
//   2. Overlapping subproblems: same sub-problem computed multiple times
//
// Implementation:
//   - Top-down (memoization): recursion + cache (easier to think)
//   - Bottom-up (tabulation): for loop (preferred in interviews)
//
// Space optimization: if dp[i] only depends on dp[i-1] and dp[i-2],
//   use two variables instead of array -> O(1) space (bonus points!)
//
// DP Keywords:
//   "number of ways"           -> counting DP
//   "minimum cost / maximum"   -> optimization DP
//   "is it possible"           -> boolean DP
//   "previous choice affects"  -> state transition = DP
// =============================================================

module unit6_dp;

  // ---------------------------------------------------------
  // Climbing Stairs: dp[i] = dp[i-1] + dp[i-2]
  // (1 or 2 steps at a time, how many ways to reach step n?)
  // ---------------------------------------------------------

  // Array version (easy to understand)
  function automatic int climb_stairs(int n);
    int dp[];
    dp = new[n + 1];

    dp[0] = 1;
    dp[1] = 1;

    for (int i = 2; i <= n; i++)
      dp[i] = dp[i-1] + dp[i-2];

    return dp[n];
  endfunction

  // Space-optimized version O(1) (interview bonus!)
  function automatic int climb_stairs_opt(int n);
    if (n <= 1) return 1;

    int prev2 = 1;  // dp[i-2]
    int prev1 = 1;  // dp[i-1]
    int curr;

    for (int i = 2; i <= n; i++) begin
      curr  = prev1 + prev2;
      prev2 = prev1;
      prev1 = curr;
    end
    return curr;
  endfunction

  // ---------------------------------------------------------
  // Min Cost Climbing Stairs
  // dp[i] = cost[i] + min(dp[i-1], dp[i-2])
  // ---------------------------------------------------------
  function automatic int min_cost_stairs(int cost[]);
    int n = cost.size();
    int dp[];
    dp = new[n];

    dp[0] = cost[0];
    dp[1] = cost[1];

    for (int i = 2; i < n; i++) begin
      int min_prev = (dp[i-1] < dp[i-2]) ? dp[i-1] : dp[i-2];
      dp[i] = cost[i] + min_prev;
    end

    return (dp[n-1] < dp[n-2]) ? dp[n-1] : dp[n-2];
  endfunction

  // ---------------------------------------------------------
  // House Robber: can't rob adjacent houses
  // dp[i] = max(dp[i-1],              <- skip house i
  //             dp[i-2] + houses[i])   <- rob house i
  // ---------------------------------------------------------
  function automatic int rob(int houses[]);
    int n = houses.size();
    if (n == 0) return 0;
    if (n == 1) return houses[0];

    int prev2 = houses[0];
    int prev1 = (houses[0] > houses[1]) ? houses[0] : houses[1];

    for (int i = 2; i < n; i++) begin
      int curr = (prev1 > prev2 + houses[i]) ? prev1 : prev2 + houses[i];
      prev2 = prev1;
      prev1 = curr;
    end
    return prev1;
  endfunction

  // ---------------------------------------------------------
  // Test
  // ---------------------------------------------------------
  initial begin
    $display("climb(5): %0d", climb_stairs(5));        // 8
    $display("climb_opt(5): %0d", climb_stairs_opt(5));// 8

    int cost[] = '{10, 15, 20};
    $display("min_cost: %0d", min_cost_stairs(cost));  // 15

    int h1[] = '{1, 2, 3, 1};
    $display("rob: %0d", rob(h1));                     // 4

    int h2[] = '{2, 7, 9, 3, 1};
    $display("rob: %0d", rob(h2));                     // 12
  end

endmodule

```

---

## 핵심 정리 (Key Takeaways)

- **DP 두 조건** — Optimal Substructure + Overlapping Subproblems.
- **5단계 표준 풀이** — state 정의 → 점화식 → base case → 구현(memo / tabulation) → 공간 최적화.
- **State 정의가 잘못되면 모두 잘못된다** — 중복 / 누락 / 무한 → state 재설계.
- **Memoization vs Tabulation** — 재귀가 자연스러우면 memo, iteration 이 자연스러우면 tabulation.
- **공간 최적화** — 보통 1D DP 는 O(N) → O(1), 2D DP 는 O(N×M) → O(min(N,M)) 으로 줄일 수 있다.

## 다음 단계 (Next Steps)

- 다음 모듈: [Interview Strategy →](../07_interview_strategy/) — 모듈 1~6 을 면접 시간 안에 적용하는 법.
- 퀴즈: [Module 06 Quiz](../quiz/06_dynamic_programming_explained_quiz/) — 5문항.
- 실습: "Climbing Stairs", "House Robber", "LCS", "Edit Distance", "Coin Change" 모두 5단계 표준 풀이로 작성.

<div class="chapter-nav">
  <a class="nav-prev" href="../05_tree_bfs_dfs_explained/">
    <div class="nav-label">◀ 이전</div>
    <div class="nav-title">Tree & BFS/DFS</div>
  </a>
  <a class="nav-next" href="../07_interview_strategy/">
    <div class="nav-label">다음 ▶</div>
    <div class="nav-title">면접 전략</div>
  </a>
</div>
