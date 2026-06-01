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

    배열의 인덱스 접근은 메모리 주소 계산 한 번으로 끝나므로 항상 O(1) 이다. 값으로 찾는 경우에는 인덱스를 미리 알 수 없기 때문에 처음부터 끝까지 순회해야 하므로 O(N) 이 된다. Hash Map 은 평균적으로 O(1) 이지만, 모든 키가 같은 버킷에 충돌하는 최악의 경우 그 버킷을 선형 탐색해야 하므로 O(N) 까지 떨어질 수 있다.

## Q2. (Understand)

Hash collision 이 발생해도 평균 O(1) 가 유지되는 이유는?

??? answer "정답 / 해설"
    Load factor 를 낮게 유지(보통 0.75 이하) 하고 hash function 의 출력이 uniform 에 가까우면, 한 bucket 의 평균 길이가 O(1) 로 유지된다. 또한 modern 구현은 collision 이 잦은 bucket 을 트리 구조(예: Java 8 의 TreeNode) 로 변환해 worst 도 O(log K) 까지 낮춘다.

    Hash collision 이 발생하더라도 평균 O(1) 이 유지되는 핵심은 확률적 균등 분포다. Hash function 이 키를 버킷 전체에 균등하게 뿌리면 특정 버킷에 키가 몰릴 확률이 낮고, load factor 가 0.75 이하이면 버킷 수 대비 원소 수가 적어 한 버킷에 모일 수 있는 충돌 수 자체가 작다. 단순히 충돌이 존재한다는 사실이 느린 게 아니라 충돌 빈도와 버킷당 길이가 관건이므로, 좋은 hash function + 낮은 load factor 조합이 평균 O(1) 을 보장한다.

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

    핵심 아이디어는 "지금 보고 있는 원소 x 의 짝꿍 K-x 가 이미 나온 적 있는가?"를 O(1) 으로 확인하는 것이다. Naive 이중 루프처럼 K-x 를 찾기 위해 배열을 다시 순회하는 대신, 지나간 원소를 hash map 에 기록해두면 한 번의 조회로 해결된다. seen[x] = i 를 need 확인 후에 저장하는 이유는 같은 인덱스를 두 번 쓰는 것을 막기 위해서이며, 이 순서가 바뀌면 x + x = K 인 경우에 한 원소를 두 번 사용하는 오답이 나온다.

## Q4. (Analyze)

Naive O(N²) 풀이가 hash map 으로 O(N) 이 되는 핵심은?

??? answer "정답 / 해설"
    Naive: 안쪽 루프가 매번 "이 값이 이전에 있었나?" 를 선형 탐색 → O(N).
    Hash map: 같은 질문을 평균 O(1) 로 답함 → 안쪽 루프가 사라짐 → O(N).

    즉, **"있었나?" 질문의 비용을 N → 1 로 낮춘다**.

    알고리즘 개선의 전형적인 패턴이다. Naive 풀이에서 병목은 안쪽 루프가 "이전에 본 원소 중에 K-x 가 있는가?" 를 O(N) 으로 확인하는 것인데, 이 확인 자체를 자료구조(hash map)로 O(1) 로 낮추면 전체 복잡도가 O(N²) 에서 O(N) 으로 떨어진다. O(N) 추가 공간을 쓰는 대신 시간을 절약하는 전형적인 time-space trade-off 이기도 하다.

## Q5. (Evaluate)

Hash Map 사용이 부적합한 시나리오 2개를 제시하라.

??? answer "정답 / 해설"
    1. **순서 의존 문제** : Hash Map 의 iteration 순서가 보장되지 않음 (Python dict 는 3.7+ 에서 보장하지만 일반화 안 됨). 순서가 중요하면 Array / TreeMap 등 사용.
    2. **메모리 제약** : Hash Map 은 2~3배의 메타데이터 / 버킷 오버헤드를 가진다. 메모리가 한계면 정렬 + Two Pointers 같은 in-place 풀이가 더 적합.

    Hash Map 은 만능 도구처럼 보이지만 구조적 한계가 있다. 순서를 보장하지 않는다는 점은 "k 번째로 작은 값", "삽입 순서대로 출력" 같은 문제에서 오답을 낼 수 있어 위험하다. 또한 버킷 배열, 각 항목의 포인터, 해시값 캐시 등 부가 메모리 때문에 단순 배열에 비해 원소당 3~5배 메모리를 쓰는 경우가 흔하다. 이 두 시나리오를 머릿속에 두면, 문제를 볼 때 hash map 이 적절한지 즉각 판단할 수 있다.
