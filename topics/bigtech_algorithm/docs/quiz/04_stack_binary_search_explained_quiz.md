# Quiz — Module 04: Stack & Binary Search

[← Module 04 본문으로 돌아가기](../04_stack_binary_search_explained.md)

---

## Q1. (Remember)

Binary Search 의 lower_bound 와 upper_bound 차이를 한 줄로 적어라.

??? answer "정답 / 해설"
    - **lower_bound** : `value` 이상의 첫 위치 (즉, 같거나 큰 가장 왼쪽).
    - **upper_bound** : `value` 보다 큰 첫 위치 (즉, strictly greater 가장 왼쪽).

    중복 원소가 있을 때 lower / upper 사이가 그 값의 개수.

## Q2. (Understand)

Monotonic Stack 이 "다음 큰 원소" 류 문제를 O(N) 으로 푸는 메커니즘을 설명하라.

??? answer "정답 / 해설"
    Stack 에 후보 인덱스를 단조 감소(다음 큰 원소를 찾는 경우) 로 유지. 새 원소가 stack top 보다 크면 top 의 답이 새 원소로 결정 → pop. 각 원소는 한 번 push, 한 번 pop 되므로 총 연산 O(N). 즉, "기다리는 후보들" 을 stack 으로 관리해 매번 선형 탐색을 피하는 것이다.

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

## Q4. (Analyze)

Binary Search 가 sorted 가 아니어도 적용 가능한 경우는?

??? answer "정답 / 해설"
    조건 함수 f(x) 가 단조(monotonic) 이면 됨. 예를 들어 "k 이상의 capacity 로 ship 가능한가?" 같은 boolean 함수가 k 가 커질수록 true 가 유지된다면, 그 값에 binary search → **parametric search**. Sorted array 는 monotonicity 의 특수 사례일 뿐이다.

## Q5. (Evaluate)

재귀와 명시적 stack 의 trade-off 를 평가하라.

??? answer "정답 / 해설"
    - **재귀** : 코드가 짧고 직관적. 단점은 system call stack 크기 한계 (Python ~1000), tail-call 미최적화 언어에서 깊이 큰 입력에 stack overflow.
    - **명시적 Stack** : heap 위에 자료구조로 stack 을 두므로 깊이 제한이 free memory 까지 확장. 코드는 약간 길지만 디버깅이 쉬움.

    면접: **깊이 ≤ 10⁴** 까지 입력이면 재귀, 그 이상이면 명시적 stack 으로 변환.
