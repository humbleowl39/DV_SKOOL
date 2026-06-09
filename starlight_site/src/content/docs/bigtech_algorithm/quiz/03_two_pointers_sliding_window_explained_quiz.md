---
title: "Quiz — Module 03: Two Pointers & Sliding Window"
---

[← Module 03 본문으로 돌아가기](../../03_two_pointers_sliding_window_explained/)

---

## Q1. (Remember)

Two Pointers 와 Sliding Window 의 한 줄 정의는?

<details>
<summary>정답 / 해설</summary>

- **Two Pointers** : 두 인덱스를 일정 규칙으로 이동시키며 부분 구간을 탐색.
- **Sliding Window** : 좌·우 포인터로 표현되는 연속 구간을 유지하며 invariant 가 깨질 때 shrink, 만족하면 expand.

두 패턴은 모두 포인터 두 개를 쓰지만 목적이 다르다. Two Pointers 는 정렬된 배열에서 두 원소의 합이나 차 같은 관계를 찾을 때 쓰이며, 두 포인터가 서로 다른 방향으로 수렴하는 경우가 많다. Sliding Window 는 "연속 구간" 전체의 속성(합, 유일 원소 수 등)을 유지하면서 구간을 오른쪽으로 밀어나가는 패턴으로, 구간의 크기가 상황에 따라 늘고 줄어든다는 점이 핵심이다.

</details>
## Q2. (Understand)

정렬된 배열에서 합이 K 인 두 원소를 찾을 때 Two Pointers 가 O(N) 인 이유는?

<details>
<summary>정답 / 해설</summary>

좌(L) 우(R) 포인터에서 합이 K 보다 크면 R-- (작아져야 함), 작으면 L++ (커져야 함). 정렬돼 있으므로 한 번 지나간 위치는 다시 볼 필요 없음 → 각 포인터가 최대 N 번 이동 → 총 O(N).

O(N) 이 성립하는 이유는 두 포인터가 절대 뒤로 돌아가지 않는다는 단조성에 있다. 정렬이 보장되어 있기 때문에 "합이 크다 → R 을 줄이면 합이 작아진다"는 인과 관계가 확실하고, 이 규칙대로만 이동하면 각 포인터는 최대 N 번 움직인다. 정렬이 없으면 "줄여야 한다"는 방향 자체가 불확실해지기 때문에 Two Pointers 는 일반적으로 정렬된 입력을 전제로 한다.

</details>
## Q3. (Apply)

"중복 없는 가장 긴 부분 문자열" 을 sliding window 로 풀어라 (pseudo code).

<details>
<summary>정답 / 해설</summary>

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

`seen[c] >= L` 조건이 없으면 이미 window 밖으로 나간 문자의 이전 인덱스를 보고 L 을 잘못 이동시키는 버그가 생긴다. R 이 오른쪽으로 이동할 때 window 가 expand 되고, 중복이 발견되면 L 을 그 중복 위치 바로 다음으로 점프시켜 shrink 한다. 각 문자는 R 이 지나가는 한 번, L 이 추월하는 한 번 — 최대 두 번만 처리되므로 전체 시간 복잡도가 O(N) 이 된다.

</details>
## Q4. (Analyze)

Sliding window 풀이의 invariant 를 글로 적는 것이 왜 디버깅에 도움이 되는가?

<details>
<summary>정답 / 해설</summary>

"이 window 는 항상 X 를 만족한다" 가 명확하면 expand / shrink 결정 기준이 한 줄로 정해진다. invariant 가 모호하면 보통 두 가지 코드가 나타난다 — expand 의 조건과 shrink 의 조건이 일치하지 않거나, 둘 다 false 인 상태에서 무한 루프. invariant 를 명시하면 이 두 종류 버그가 사라진다.

예를 들어 "window 내 중복이 없다"가 invariant 라면, 새 문자를 넣을 때 중복이 생기면 즉시 shrink 해야 한다는 행동 규칙이 자동으로 도출된다. invariant 를 명시하지 않으면 expand 할 타이밍과 shrink 할 타이밍이 각자 다른 조건으로 작성되어 충돌하거나, 어느 쪽 조건도 만족하지 않는 경계 상태에서 루프가 멈추지 않는 버그가 발생한다. invariant 를 먼저 글로 쓰는 것은 코드를 작성하기 전에 알고리즘 명세를 정형화하는 작업이다.

</details>
## Q5. (Evaluate)

같은 문제에 (a) Two Pointers (정렬 후) (b) Sliding Window (c) Hash Map 모두 가능할 때 어떤 기준으로 선택하나?

<details>
<summary>정답 / 해설</summary>

- **입력이 sorted 이면** (a) Two Pointers — 가장 작은 메모리.
- **연속 부분 배열 / 문자열 + invariant** 가 명확하면 (b) Sliding Window.
- **순서가 중요 없고 값-인덱스 lookup 만 필요** 하면 (c) Hash Map.

면접에서는 두 개를 비교해 trade-off 를 말하면 점수 ↑.

세 패턴은 각각 다른 입력 구조를 전제로 한다. 정렬은 Two Pointers 가 방향 결정을 할 수 있게 해주는 조건이고, "연속 구간"이라는 구조는 Sliding Window 가 expand/shrink 로 O(N) 을 달성하게 해주는 조건이다. Hash Map 은 이러한 구조적 전제 없이 임의 접근을 O(1) 로 만드는 범용 도구지만 추가 공간을 소비한다. 세 후보를 구조 → 비용 순으로 평가하는 습관이 면접에서 빠른 패턴 선택으로 이어진다.

</details>
