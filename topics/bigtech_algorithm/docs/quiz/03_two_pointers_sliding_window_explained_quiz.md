# Quiz — Module 03: Two Pointers & Sliding Window

[← Module 03 본문으로 돌아가기](../03_two_pointers_sliding_window_explained.md)

---

## Q1. (Remember)

Two Pointers 와 Sliding Window 의 한 줄 정의는?

??? answer "정답 / 해설"
    - **Two Pointers** : 두 인덱스를 일정 규칙으로 이동시키며 부분 구간을 탐색.
    - **Sliding Window** : 좌·우 포인터로 표현되는 연속 구간을 유지하며 invariant 가 깨질 때 shrink, 만족하면 expand.

## Q2. (Understand)

정렬된 배열에서 합이 K 인 두 원소를 찾을 때 Two Pointers 가 O(N) 인 이유는?

??? answer "정답 / 해설"
    좌(L) 우(R) 포인터에서 합이 K 보다 크면 R-- (작아져야 함), 작으면 L++ (커져야 함). 정렬돼 있으므로 한 번 지나간 위치는 다시 볼 필요 없음 → 각 포인터가 최대 N 번 이동 → 총 O(N).

## Q3. (Apply)

"중복 없는 가장 긴 부분 문자열" 을 sliding window 로 풀어라 (의사 코드).

??? answer "정답 / 해설"
    ```python
    def longest_unique(s):
        seen = {}      # char -> last index
        L, best = 0, 0
        for R, c in enumerate(s):
            if c in seen and seen[c] >= L:
                L = seen[c] + 1   # shrink past duplicate
            seen[c] = R
            best = max(best, R - L + 1)
        return best
    ```
    각 문자가 한 번 expand, 한 번 shrink 됨 → O(N).

## Q4. (Analyze)

Sliding window 풀이의 invariant 를 글로 적는 것이 왜 디버깅에 도움이 되는가?

??? answer "정답 / 해설"
    "이 window 는 항상 X 를 만족한다" 가 명확하면 expand / shrink 결정 기준이 한 줄로 정해진다. invariant 가 모호하면 보통 두 가지 코드가 나타난다 — expand 의 조건과 shrink 의 조건이 일치하지 않거나, 둘 다 false 인 상태에서 무한 루프. invariant 를 명시하면 이 두 종류 버그가 사라진다.

## Q5. (Evaluate)

같은 문제에 (a) Two Pointers (정렬 후) (b) Sliding Window (c) Hash Map 모두 가능할 때 어떤 기준으로 선택하나?

??? answer "정답 / 해설"
    - **입력이 sorted 이면** (a) Two Pointers — 가장 작은 메모리.
    - **연속 부분 배열 / 문자열 + invariant** 가 명확하면 (b) Sliding Window.
    - **순서가 중요 없고 값-인덱스 lookup 만 필요** 하면 (c) Hash Map.

    면접에서는 두 개를 비교해 trade-off 를 말하면 점수 ↑.
