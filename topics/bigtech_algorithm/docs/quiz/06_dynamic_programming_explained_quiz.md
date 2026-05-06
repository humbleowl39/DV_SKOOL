# Quiz — Module 06: Dynamic Programming

[← Module 06 본문으로 돌아가기](../06_dynamic_programming_explained.md)

---

## Q1. (Remember)

DP 의 두 조건은?

??? answer "정답 / 해설"
    1. **Optimal Substructure** — 큰 문제의 최적해가 부분 문제의 최적해로 구성됨.
    2. **Overlapping Subproblems** — 같은 부분 문제가 재귀 전개에서 여러 번 등장.

## Q2. (Understand)

Top-Down (memoization) 과 Bottom-Up (tabulation) 의 차이를 설명하라.

??? answer "정답 / 해설"
    - **Top-Down** : 재귀 + cache. 자연스러운 사고 흐름이지만 함수 호출 오버헤드 있음.
    - **Bottom-Up** : 작은 부분 문제부터 표를 채워나감. 함수 호출 ↓, 공간 최적화 가능.

    수학적으론 동등. 실전에서는 자연스러운 쪽으로 작성 후 필요시 변환.

## Q3. (Apply)

Climbing Stairs (계단 N개, 한 번에 1 또는 2 step) 의 DP 점화식과 답을 적어라.

??? answer "정답 / 해설"
    - State: `dp[i]` = i 번째 계단까지 도달 방법 수.
    - 점화식: `dp[i] = dp[i-1] + dp[i-2]`.
    - Base: `dp[0]=1, dp[1]=1`.
    - 결과: dp[N] (Fibonacci 수열).
    - 공간 최적화 → 두 변수만 유지 → O(1) 공간.

## Q4. (Analyze)

DP state 정의가 잘못된 경우의 증상 3가지는?

??? answer "정답 / 해설"
    1. **답이 달라짐 (틀림)** — state 가 부분 문제를 충분히 표현하지 못함 (정보 부족).
    2. **무한 재귀 / 사이클** — state 변환이 단조 감소하지 않음.
    3. **중복 / 과대 계산** — state 가 서로 의존성이 있는 차원을 놓쳐 같은 답을 여러 차원에서 셈.

    해결: state 에 들어가야 할 차원을 "이 문제를 풀려면 무엇을 알아야 하는가" 로 다시 정의.

## Q5. (Evaluate)

같은 문제에 (a) DP (b) Greedy 가 모두 가능할 때 어느 것이 좋은가?

??? answer "정답 / 해설"
    - **Greedy 가 정답이 증명되면** → Greedy. 더 빠르고 간결.
    - **Greedy 가 반례가 있으면** → DP. 안전.

    실무에서는 보통 **DP 가 default + 가능하면 Greedy 로 단순화**. 면접에서는 둘 다 알고 있다는 신호를 주면 점수 ↑.
