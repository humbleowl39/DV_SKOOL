# Quiz — Module 04: Stack & Binary Search

[← Module 04 본문으로 돌아가기](../04_stack_binary_search_explained.md)

---

## Q1. (Remember)

Binary Search 의 lower_bound 와 upper_bound 차이를 한 줄로 적어라.

??? answer "정답 / 해설"
    - **lower_bound** : `value` 이상의 첫 위치 (즉, 같거나 큰 가장 왼쪽).
    - **upper_bound** : `value` 보다 큰 첫 위치 (즉, strictly greater 가장 왼쪽).

    중복 원소가 있을 때 lower / upper 사이가 그 값의 개수.

    두 개념이 헷갈리는 이유는 "같을 때" 포함 여부 때문이다. lower_bound 는 배열에서 `value` 가 처음 등장하는 위치를 찾고, upper_bound 는 `value` 보다 큰 원소가 처음 등장하는 위치를 찾는다. 따라서 `upper_bound - lower_bound` 를 계산하면 정렬된 배열에서 `value` 의 등장 횟수를 O(log N) 에 구할 수 있다. 두 함수를 한 세트로 기억하면 범위 기반 질의에 즉시 활용 가능하다.

## Q2. (Understand)

Monotonic Stack 이 "다음 큰 원소" 류 문제를 O(N) 으로 푸는 메커니즘을 설명하라.

??? answer "정답 / 해설"
    Stack 에 후보 인덱스를 단조 감소(다음 큰 원소를 찾는 경우) 로 유지. 새 원소가 stack top 보다 크면 top 의 답이 새 원소로 결정 → pop. 각 원소는 한 번 push, 한 번 pop 되므로 총 연산 O(N). 즉, "기다리는 후보들" 을 stack 으로 관리해 매번 선형 탐색을 피하는 것이다.

    Naive 방법은 각 원소에 대해 오른쪽을 선형 탐색하므로 O(N²) 이다. Monotonic Stack 이 O(N) 인 이유는 "아직 답을 모르는 원소들"을 stack 에 대기시키고, 새 원소가 들어올 때 그 원소보다 작은 후보들을 한꺼번에 처리(pop) 하기 때문이다. N 개 원소가 각각 최대 1번 push, 1번 pop 되므로 총 연산은 2N = O(N) 이다. "단조 감소" 라는 조건이 이 연쇄 처리를 가능하게 하는 핵심이다.

## Q3. (Apply)

Valid Parentheses 를 stack 으로 풀어라.

??? answer "정답 / 해설"
    ```python
    def is_valid(s):
        st = []
        pair = {')': '(', ']': '[', '}': '{'}
        for c in s:
            if c in pair:
                if not st or st.pop() != pair[c]:
                    return False
            else:
                st.append(c)
        return not st
    ```
    - 열리면 push, 닫히면 pop 하여 짝 확인.
    - 끝나서 stack 이 비어 있으면 valid.

    Stack 이 이 문제에 자연스러운 이유는 괄호의 "가장 최근에 열린 것이 가장 먼저 닫혀야 한다"는 LIFO 구조와 stack 이 정확히 일치하기 때문이다. 닫는 괄호가 나올 때 stack 이 비어 있으면 짝이 없는 것이고, top 이 다른 종류의 여는 괄호이면 순서가 잘못된 것이다. 마지막에 stack 이 비어 있지 않으면 닫히지 않은 여는 괄호가 남아 있는 상태이므로 invalid 다.

## Q4. (Analyze)

Binary Search 가 sorted 가 아니어도 적용 가능한 경우는?

??? answer "정답 / 해설"
    조건 함수 f(x) 가 단조(monotonic) 이면 됨. 예를 들어 "k 이상의 capacity 로 ship 가능한가?" 같은 boolean 함수가 k 가 커질수록 true 가 유지된다면, 그 값에 binary search → **parametric search**. Sorted array 는 monotonicity 의 특수 사례일 뿐이다.

    "정렬된 배열에서만 이진 탐색"이라는 믿음은 잘못된 제약이다. 이진 탐색이 요구하는 것은 탐색 공간에서 "left 쪽은 false, right 쪽은 true"(또는 그 반대)인 단조 분할이 존재하는 것이다. 정렬 배열은 값 자체가 단조 증가하는 특수 사례일 뿐, "capacity k 로 하루 안에 운송 가능한가?" 같은 판별 함수도 k 가 증가할수록 결과가 false→true 로 단조 변화하면 같은 원리를 쓸 수 있다. 이 관점에서 바라보면 Binary Search 의 적용 범위가 크게 넓어진다.

## Q5. (Evaluate)

재귀와 명시적 stack 의 trade-off 를 평가하라.

??? answer "정답 / 해설"
    - **재귀** : 코드가 짧고 직관적. 단점은 system call stack 크기 한계 (Python ~1000), tail-call 미최적화 언어에서 깊이 큰 입력에 stack overflow.
    - **명시적 Stack** : heap 위에 자료구조로 stack 을 두므로 깊이 제한이 free memory 까지 확장. 코드는 약간 길지만 디버깅이 쉬움.

    면접: **깊이 ≤ 10⁴** 까지 입력이면 재귀, 그 이상이면 명시적 stack 으로 변환.

    재귀와 명시적 stack 은 알고리즘적으로 동등하지만 자원 사용 위치가 다르다. 재귀는 OS 가 관리하는 call stack 을 사용하므로 언어별 한계(Python 기본값 약 1000, Java 수천 프레임)를 넘으면 런타임 오류가 난다. 명시적 stack 은 heap 에 직접 할당하는 자료구조이므로 사용 가능 메모리 전체가 상한이 된다. 면접에서는 재귀로 먼저 작성한 뒤 "입력 깊이가 매우 크면 stack overflow 위험이 있어 명시적 stack 으로 변환할 수 있습니다"라고 한 마디 붙이면 trade-off 인지 능력을 보여줄 수 있다.
