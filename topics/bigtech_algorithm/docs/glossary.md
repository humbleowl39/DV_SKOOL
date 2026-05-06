# BigTech Algorithm 용어집

이 페이지는 **BigTech Algorithm** 코스의 핵심 용어 모음입니다. 각 항목은 ISO 11179 형식(Definition / Source / Related / Example / See also) 을 따릅니다.

---

## B

### BFS (Breadth-First Search)
- **Definition.** 시작 노드로부터 가까운 노드부터 단계별(level by level) 로 방문하는 탐색 알고리즘으로 큐를 사용한다.
- **Source.** Common algorithm textbook (CLRS).
- **Related.** DFS, Queue, Shortest Path.
- **Example.** Word Ladder, Binary Tree Level Order Traversal.
- **See also.** [Module 05](05_tree_bfs_dfs_explained.md).

### Big-O Notation
- **Definition.** 입력 크기 N 이 무한대로 갈 때 알고리즘의 자원 사용량의 상한 차수(asymptotic upper bound) 를 표현하는 수학적 표기.
- **Source.** Bachmann, Landau (수학) / 알고리즘 분석.
- **Related.** Worst-case, Time/Space Complexity.
- **Example.** O(N log N) — merge sort, heap sort.
- **See also.** [Module 01](01_big_o_explained.md).

### Binary Search
- **Definition.** 정렬되거나 단조성을 만족하는 입력에서 탐색 범위를 매 step 절반으로 줄여 O(log N) 안에 답을 찾는 알고리즘.
- **Source.** Common algorithm textbook.
- **Related.** Lower/Upper Bound, Parametric Search.
- **Example.** Search-in-Rotated-Sorted-Array, Find Peak Element.
- **See also.** [Module 04](04_stack_binary_search_explained.md).

### BST (Binary Search Tree)
- **Definition.** 모든 노드에 대해 왼쪽 서브트리의 키 < 노드 키 < 오른쪽 서브트리의 키 가 성립하는 이진 트리.
- **Source.** Common data structure literature.
- **Related.** Inorder Traversal, AVL, Red-Black Tree.
- **Example.** Inorder of BST = sorted sequence.
- **See also.** [Module 05](05_tree_bfs_dfs_explained.md).

---

## D

### DFS (Depth-First Search)
- **Definition.** 시작 노드에서 가능한 한 깊이 먼저 탐색한 뒤 backtrack 하는 탐색 알고리즘으로 stack 또는 재귀로 구현된다.
- **Source.** Common algorithm textbook.
- **Related.** BFS, Backtracking, Stack.
- **Example.** Path Sum, Number of Islands.
- **See also.** [Module 05](05_tree_bfs_dfs_explained.md).

### Dynamic Programming (DP)
- **Definition.** 큰 문제를 부분 문제로 나누고, 부분 문제의 답을 저장(memoize) 해 중복 계산을 피하는 알고리즘 설계 기법.
- **Source.** Bellman, 1957.
- **Related.** Memoization, Tabulation, Optimal Substructure.
- **Example.** LCS, Edit Distance, Coin Change.
- **See also.** [Module 06](06_dynamic_programming_explained.md).

---

## H

### Hash Map
- **Definition.** Key 를 hash function 으로 인덱스로 변환해 평균 O(1) 시간에 lookup/insert/delete 를 제공하는 자료구조.
- **Source.** Common data structure literature.
- **Related.** Hash Function, Collision, Open Addressing, Chaining.
- **Example.** Two Sum 을 O(N) 으로 해결.
- **See also.** [Module 02](02_array_hashmap_explained.md).

---

## L

### LCA (Lowest Common Ancestor)
- **Definition.** 트리에서 두 노드 X, Y 의 공통 조상 중 가장 깊은(낮은) 노드.
- **Source.** Common tree algorithm literature.
- **Related.** Tree Traversal, Tarjan's Algorithm, Euler Tour.
- **Example.** Binary Tree LCA, BST LCA.
- **See also.** [Module 05](05_tree_bfs_dfs_explained.md).

---

## M

### Memoization
- **Definition.** 함수의 입력을 키로 그 결과를 캐시에 저장해 같은 입력에 대한 재계산을 피하는 최적화 기법.
- **Source.** Common DP technique.
- **Related.** Top-Down DP, Tabulation.
- **Example.** Fibonacci 의 재귀 해법에 dict 캐시.
- **See also.** [Module 06](06_dynamic_programming_explained.md).

### Monotonic Stack
- **Definition.** 스택 내 원소가 항상 증가(또는 감소) 순으로 유지되도록 push 시 위반 원소를 pop 하는 stack 운용 패턴.
- **Source.** Common competitive programming usage.
- **Related.** Next Greater Element, Histogram.
- **Example.** Daily Temperatures.
- **See also.** [Module 04](04_stack_binary_search_explained.md).

---

## O

### Optimal Substructure
- **Definition.** 문제의 최적 해가 부분 문제의 최적 해로부터 구성될 수 있는 성질로, DP / 그리디 적용 가능성의 핵심 조건.
- **Source.** Bellman; CLRS.
- **Related.** DP, Overlapping Subproblems.
- **Example.** 최단 경로의 부분 경로도 최단 경로.
- **See also.** [Module 06](06_dynamic_programming_explained.md).

### Overlapping Subproblems
- **Definition.** 같은 부분 문제가 재귀 전개 중 여러 번 등장하는 성질로, DP 가 효과적인 두 번째 전제 조건.
- **Source.** CLRS.
- **Related.** DP, Memoization.
- **Example.** Naive 재귀 Fibonacci 가 같은 부분을 지수적으로 반복 계산.
- **See also.** [Module 06](06_dynamic_programming_explained.md).

---

## P

### Parametric Search
- **Definition.** 답을 직접 찾는 대신 "X 이상이 가능한가?" 같은 단조 boolean 함수에 binary search 를 적용하여 최적 X 를 찾는 기법.
- **Source.** Megiddo, 1983.
- **Related.** Binary Search, Monotonicity.
- **Example.** Capacity to Ship Packages, Split Array Largest Sum.
- **See also.** [Module 04](04_stack_binary_search_explained.md).

### Pattern Thinking (패턴 사고법)
- **Definition.** 입력 형태와 제약을 보고 후보 알고리즘 패턴을 빠르게 좁힌 뒤 복잡도 목표를 정해 코드를 작성하는 5단계 풀이 절차.
- **Source.** This course (Module 01).
- **Related.** Big-O, Algorithm Family.
- **Example.** N≤10⁴ + 부분 합 → "Two Pointers / Sliding Window 후보".
- **See also.** [Module 01](01_big_o_explained.md).

---

## S

### Sliding Window
- **Definition.** 연속 부분 배열/문자열을 이동시키며 invariant 를 유지하기 위해 좌/우 포인터를 expand/shrink 하는 패턴.
- **Source.** Common competitive programming pattern.
- **Related.** Two Pointers, Deque.
- **Example.** Longest Substring Without Repeating Characters.
- **See also.** [Module 03](03_two_pointers_sliding_window_explained.md).

### Stack
- **Definition.** Last-In-First-Out (LIFO) 순서로 push/pop 이 동작하는 자료구조.
- **Source.** Common data structure literature.
- **Related.** Recursion, Monotonic Stack.
- **Example.** Valid Parentheses.
- **See also.** [Module 04](04_stack_binary_search_explained.md).

---

## T

### Tabulation
- **Definition.** Bottom-up 방향으로 부분 문제 답을 표(table) 에 채워가며 최종 답에 도달하는 DP 구현 방식.
- **Source.** Common DP technique.
- **Related.** Memoization, Top-Down.
- **Example.** Iterative Fibonacci `dp[i] = dp[i-1] + dp[i-2]`.
- **See also.** [Module 06](06_dynamic_programming_explained.md).

### Two Pointers
- **Definition.** 한 배열 위에 두 인덱스를 두고 둘의 이동 규칙으로 부분 구간의 성질을 유지·탐색하는 패턴.
- **Source.** Common competitive programming pattern.
- **Related.** Sliding Window, Sorted Array.
- **Example.** 3Sum, Container With Most Water.
- **See also.** [Module 03](03_two_pointers_sliding_window_explained.md).
