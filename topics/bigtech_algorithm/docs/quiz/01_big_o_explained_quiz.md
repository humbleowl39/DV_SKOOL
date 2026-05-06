# Quiz — Module 01: Big-O & Pattern Thinking

[← Module 01 본문으로 돌아가기](../01_big_o_explained.md)

---

## Q1. (Remember)

다음 알고리즘의 시간 복잡도를 적어라: 선형 탐색, 이진 탐색, merge sort, naive 모든 쌍 비교.

??? answer "정답 / 해설"
    - 선형 탐색: O(N)
    - 이진 탐색: O(log N)
    - Merge sort: O(N log N)
    - Naive 모든 쌍 비교: O(N²)

## Q2. (Understand)

O(N²) 와 O(N log N) 의 실제 성능 차이가 N=10⁶ 에서 얼마나 큰지 설명하라.

??? answer "정답 / 해설"
    - O(N²) ≈ 10¹² operations → 일반 CPU 로 수십 분 ~ 수 시간.
    - O(N log N) ≈ 10⁶ × 20 = 2×10⁷ operations → 수십 ms.

    같은 컴퓨터에서 5~6 자릿수의 시간 차이. **N 가 100만 이상이면 O(N²) 은 사실상 불가**.

## Q3. (Apply)

```python
def f(arr):
    n = len(arr)
    for i in range(n):
        for j in range(i, n):
            do_something(arr[i], arr[j])
```
의 시간 복잡도를 계산하라.

??? answer "정답 / 해설"
    바깥 루프 i: 0..N-1 (N 번), 안 루프 j: i..N-1 (평균 N/2 번).
    총 연산 ≈ N × N/2 = N²/2 = O(N²).

    하한 항·상수항을 무시하므로 정답은 **O(N²)**.

## Q4. (Analyze)

문제 입력이 N≤10⁵ 이고 query 가 Q≤10⁵ 이며 각 query 가 정렬된 배열에서의 lookup 이라면 어떤 패턴 후보를 생각해야 하는가?

??? answer "정답 / 해설"
    각 query 가 O(log N) 인 binary search 사용 시 총 O(Q log N) ≈ 10⁵ × 17 ≈ 1.7×10⁶ → 충분히 빠름.

    선형 탐색 (O(Q×N) = 10¹⁰) 은 불가. → **이진 탐색 / Hash Map** 후보.

## Q5. (Evaluate)

같은 문제에 (a) O(N log N) 정렬 + Two Pointers 와 (b) O(N) Hash Map 풀이가 모두 가능하다. 면접에서 어느 것을 먼저 제시해야 하는가?

??? answer "정답 / 해설"
    문맥에 따라 다르다.
    - **메모리 제약** 이 명시되면 (a) — 정렬 + Two Pointers 는 O(1) 추가 공간.
    - **단순함 / 빠른 작성** 이 우선이면 (b) — Hash Map 이 보통 더 짧고 명확.

    면접에서는 **두 가지 모두 알고 있다는 신호** 를 주는 것이 가장 좋다 → "(b) 가 더 직관적이지만, 메모리 제약 시 (a) 도 가능합니다" 한 마디가 점수를 높인다.
