# Quiz — Module 02: Array & Hash Map

[← Module 02 본문으로 돌아가기](../02_array_hashmap_explained.md)

---

## Q1. (Remember)

Array 와 Hash Map 의 평균 / 최악 lookup 시간 복잡도는?

??? answer "정답 / 해설"
    | 자료구조 | 평균 lookup | 최악 lookup |
    |---------|-------------|-------------|
    | Array (by index) | O(1) | O(1) |
    | Array (by value) | O(N) | O(N) |
    | Hash Map | O(1) | O(N) (모든 key collision 시) |

## Q2. (Understand)

Hash collision 이 발생해도 평균 O(1) 가 유지되는 이유는?

??? answer "정답 / 해설"
    Load factor 를 낮게 유지(보통 0.75 이하) 하고 hash function 의 출력이 uniform 에 가까우면, 한 bucket 의 평균 길이가 O(1) 로 유지된다. 또한 modern 구현은 collision 이 잦은 bucket 을 트리 구조(예: Java 8 의 TreeNode) 로 변환해 worst 도 O(log K) 까지 낮춘다.

## Q3. (Apply)

배열에서 합이 K 인 두 원소의 인덱스를 찾는 문제를 hash map 으로 O(N) 에 풀어라.

??? answer "정답 / 해설"
    ```python
    def two_sum(arr, K):
        seen = {}  # value -> index
        for i, x in enumerate(arr):
            need = K - x
            if need in seen:
                return [seen[need], i]
            seen[x] = i
        return []
    ```
    각 원소를 한 번 보면서 보완 값(K-x) 을 hash 로 즉시 lookup → O(N) 시간, O(N) 공간.

## Q4. (Analyze)

Naive O(N²) 풀이가 hash map 으로 O(N) 이 되는 핵심은?

??? answer "정답 / 해설"
    Naive: 안쪽 루프가 매번 "이 값이 이전에 있었나?" 를 선형 탐색 → O(N).
    Hash map: 같은 질문을 평균 O(1) 로 답함 → 안쪽 루프가 사라짐 → O(N).

    즉, **"있었나?" 질문의 비용을 N → 1 로 낮춘다**.

## Q5. (Evaluate)

Hash Map 사용이 부적합한 시나리오 2개를 제시하라.

??? answer "정답 / 해설"
    1. **순서 의존 문제** : Hash Map 의 iteration 순서가 보장되지 않음 (Python dict 는 3.7+ 에서 보장하지만 일반화 안 됨). 순서가 중요하면 Array / TreeMap 등 사용.
    2. **메모리 제약** : Hash Map 은 2~3배의 메타데이터 / 버킷 오버헤드를 가진다. 메모리가 한계면 정렬 + Two Pointers 같은 in-place 풀이가 더 적합.
