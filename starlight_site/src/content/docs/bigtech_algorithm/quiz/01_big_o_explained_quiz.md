---
title: "Quiz — Module 01: Big-O & Pattern Thinking"
---

[← Module 01 본문으로 돌아가기](../../01_big_o_explained/)

---

## Q1. (Remember)

다음 알고리즘의 시간 복잡도를 적어라: 선형 탐색, 이진 탐색, merge sort, naive 모든 쌍 비교.

<details>
<summary>정답 / 해설</summary>

- 선형 탐색: O(N)
- 이진 탐색: O(log N)
- Merge sort: O(N log N)
- Naive 모든 쌍 비교: O(N²)

선형 탐색은 원소를 처음부터 끝까지 하나씩 확인하므로 입력 크기 N 에 비례해 시간이 늘어난다. 이진 탐색은 탐색 범위를 매 단계에서 절반으로 줄이기 때문에 N 이 두 배가 되어도 단계 수는 1만 늘어나는 로그 성장을 한다. Merge sort 는 N 개 원소를 재귀적으로 반씩 나눠 정렬한 뒤 합치는데, 분할 깊이가 log N, 각 층에서 합치는 작업이 O(N) 이므로 곱하면 O(N log N) 이다. Naive 모든 쌍 비교는 두 겹의 루프가 각각 N 번 돌기 때문에 O(N²) 이 된다.

</details>
## Q2. (Understand)

O(N²) 와 O(N log N) 의 실제 성능 차이가 N=10⁶ 에서 얼마나 큰지 설명하라.

<details>
<summary>정답 / 해설</summary>

- O(N²) ≈ 10¹² operations → 일반 CPU 로 수십 분 ~ 수 시간.
- O(N log N) ≈ 10⁶ × 20 = 2×10⁷ operations → 수십 ms.

같은 컴퓨터에서 5~6 자릿수의 시간 차이. **N 가 100만 이상이면 O(N²) 은 사실상 불가**.

Big-O 는 상수를 무시하지만, 차수의 차이는 N 이 커질수록 압도적으로 벌어진다. N=10⁶ 에서 O(N²) 은 연산 횟수가 10¹² 에 달해 1 GHz CPU 기준으로도 수천 초가 걸리는 반면, O(N log N) 은 log₂(10⁶) ≈ 20 이므로 약 2×10⁷ 번 연산으로 수십 ms 안에 끝난다. 이 격차가 바로 알고리즘 선택이 최적화의 핵심인 이유다.

</details>
## Q3. (Apply)

```python
def f(arr):
    n = len(arr)
    for i in range(n):
        for j in range(i, n):
            do_something(arr[i], arr[j])
```
의 시간 복잡도를 계산하라.

<details>
<summary>정답 / 해설</summary>

바깥 루프 i: 0..N-1 (N 번), 안 루프 j: i..N-1 (평균 N/2 번).
총 연산 ≈ N × N/2 = N²/2 = O(N²).

하한 항·상수항을 무시하므로 정답은 **O(N²)**.

안쪽 루프의 범위가 `i` 에 따라 달라지기 때문에 단순히 N×N 으로 보면 안 된다고 생각할 수 있다. 그러나 실제 연산 횟수는 N + (N-1) + … + 1 = N(N+1)/2 이고, Big-O 는 최고 차항만 취하므로 1/2 상수는 버리고 O(N²) 이 된다. `j` 가 `0` 이 아닌 `i` 에서 시작한다는 점은 상수 계수에만 영향을 줄 뿐 차수를 바꾸지 못한다.

</details>
## Q4. (Analyze)

문제 입력이 N≤10⁵ 이고 query 가 Q≤10⁵ 이며 각 query 가 정렬된 배열에서의 lookup 이라면 어떤 패턴 후보를 생각해야 하는가?

<details>
<summary>정답 / 해설</summary>

각 query 가 O(log N) 인 binary search 사용 시 총 O(Q log N) ≈ 10⁵ × 17 ≈ 1.7×10⁶ → 충분히 빠름.

선형 탐색 (O(Q×N) = 10¹⁰) 은 불가. → **이진 탐색 / Hash Map** 후보.

입력이 정렬되어 있고 query 마다 특정 값의 존재 여부 또는 위치를 찾아야 한다면, 각 query 에 선형 탐색을 쓰면 O(N) 비용이 Q 번 쌓여 O(Q×N) = 10¹⁰ 이 된다. 반면 이진 탐색은 O(log N) 이므로 총 비용이 O(Q log N) ≈ 1.7×10⁶ 으로 대폭 줄어든다. Hash Map 은 정렬 불필요·lookup O(1) 이라 더 유리하지만, 배열이 이미 정렬된 상황에서는 이진 탐색으로 O(1) 추가 공간만으로 같은 복잡도 클래스를 달성할 수 있다.

</details>
## Q5. (Evaluate)

같은 문제에 (a) O(N log N) 정렬 + Two Pointers 와 (b) O(N) Hash Map 풀이가 모두 가능하다. 면접에서 어느 것을 먼저 제시해야 하는가?

<details>
<summary>정답 / 해설</summary>

문맥에 따라 다르다.
- **메모리 제약** 이 명시되면 (a) — 정렬 + Two Pointers 는 O(1) 추가 공간.
- **단순함 / 빠른 작성** 이 우선이면 (b) — Hash Map 이 보통 더 짧고 명확.

면접에서는 **두 가지 모두 알고 있다는 신호** 를 주는 것이 가장 좋다 → "(b) 가 더 직관적이지만, 메모리 제약 시 (a) 도 가능합니다" 한 마디가 점수를 높인다.

두 방법이 모두 O(N log N) 또는 O(N) 이라도 자원 사용 프로필은 다르다. 정렬 + Two Pointers 는 정렬 비용 O(N log N) 이 추가되지만 보조 공간이 O(1) 이고, Hash Map 풀이는 O(N) 시간이지만 O(N) 추가 공간을 요구한다. 면접에서 어느 하나만 제시하면 trade-off 를 모르는 것처럼 보이므로, 두 가지를 모두 알고 제약에 따라 선택할 수 있다는 점을 보여주는 것이 핵심이다.

</details>
