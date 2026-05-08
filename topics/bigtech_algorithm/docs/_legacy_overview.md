# 빅테크 알고리즘 면접 — 학습 요약

## 핵심 용어집 (Glossary)

### 복잡도 분석

| 용어 | 설명 |
|------|------|
| **Big-O** | 시간/공간 복잡도의 점근 상한 표기법 |
| **O(1)** | 상수 시간 — 입력 크기와 무관 |
| **O(log n)** | 로그 시간 — 매번 절반 제거 (Binary Search) |
| **O(n)** | 선형 시간 — 단일 루프, Hash Map 활용 |
| **O(n log n)** | 선형로그 — 효율적 정렬 (Merge Sort, Quick Sort) |
| **O(n²)** | 이차 시간 — 이중 루프 (최적화 대상) |
| **O(2ⁿ)** | 지수 시간 — 완전 탐색, 부분집합 (피해야 함) |
| **Time Complexity** | 연산 횟수가 입력 크기에 따라 증가하는 정도 |
| **Space Complexity** | 추가 메모리 사용량이 입력에 따라 증가하는 정도 |

### 자료구조

| 용어 | 설명 |
|------|------|
| **Hash Map** | O(1) 키 기반 탐색. exists()로 이중 루프를 단일 루프로 최적화 |
| **Associative Array** | SystemVerilog의 연관 배열. Hash Map과 동일 개념 |
| **Stack** | LIFO (Last In First Out). "가장 최근 X" 문제에 사용 |
| **Queue** | FIFO (First In First Out). BFS, 레벨 순회에 사용 |
| **Monotonic Stack** | 단조 증가/감소 유지 스택. "다음 큰 원소" 패턴 |
| **Priority Queue** | 우선순위 기반 큐 (Heap 구현) |
| **BST** | Binary Search Tree. 왼쪽<부모<오른쪽 정렬 특성 |

### 알고리즘 패턴

| 용어 | 설명 |
|------|------|
| **Two Pointers** | 정렬된 배열의 양 끝 포인터로 O(n) 탐색 |
| **Sliding Window** | 연속 부분 배열/문자열을 윈도우로 처리 |
| **Binary Search** | 정렬 데이터에서 매번 절반 제거하여 O(log n) 탐색 |
| **DFS** | Depth-First Search. 재귀/스택, 경로/깊이 문제 |
| **BFS** | Breadth-First Search. 큐, 레벨 순회/최단 거리 |
| **DP** | Dynamic Programming. 부분 문제 재사용으로 최적화 |
| **Memoization** | Top-down DP (재귀 + 캐시) |
| **Tabulation** | Bottom-up DP (for 루프, 면접에서 선호) |
| **Backtracking** | 전체 탐색 후 되돌리기 (경로 수집, 조합 문제) |
| **Brute Force** | 최적화 전 단순 무식한 방법 (항상 여기서 시작) |

### 문제 풀이 기법

| 용어 | 설명 |
|------|------|
| **Dry Run** | 작은 입력으로 손으로 동작 추적하여 검증 |
| **Optimal Substructure** | 큰 문제의 답이 작은 문제의 답의 조합 (DP 조건) |
| **Overlapping Subproblems** | 같은 부분 문제가 반복 등장 (DP 조건) |
| **Trade-off** | 시간과 공간의 상충 관계 |
| **Lower/Upper Bound** | Binary Search에서 조건 만족하는 최소/최대값 찾기 |

---

## 컨셉 맵

```
                    +--------------------+
                    |  알고리즘 면접      |
                    |  핵심 패턴          |
                    +---------+----------+
              +---------------+---------------+
              v               v               v
       +-----------+   +-----------+   +-----------+
       | 자료구조  |   |  탐색     |   |  최적화   |
       |  패턴     |   |  패턴     |   |  패턴     |
       +-----+-----+   +-----+-----+   +-----+-----+
        +----+----+      +----+----+      +---+---+
        v    v    v      v    v   v       v       v
      Array Hash Stack  BFS  DFS Binary   DP   Greedy
       +Str  Map Queue           Search
        |         |
        v         v
   Two Pointers  Monotonic
   Sliding Window  Stack
```

## 핵심 원칙
**면접 문제의 87%는 10~12개 패턴으로 해결된다. 500문제를 외우지 말고, 10개 패턴을 마스터하라. 항상 Brute Force부터 시작하고, 그 다음 최적화하라. 면접관은 정답이 아니라 사고 과정을 평가한다.**

## 학습 단위

| # | 단위 | 핵심 요약 |
|---|------|----------|
| 1 | **Big-O & 패턴 사고법** | 10개 패턴이 87% 해결. Brute Force 먼저, 최적화는 그 다음. |
| 2 | **Array & Hash Map** | Associative Array의 `exists()`가 O(n²) 이중 루프를 O(n)으로. Key = 찾고 싶은 값. |
| 3 | **Two Pointers & Sliding Window** | Two Pointers: 정렬 배열, 양 끝에서 수렴. Sliding Window: 연속 부분 배열, 추가/제거. |
| 4 | **Stack & Binary Search** | Stack: LIFO, "가장 최근 X" 문제. Binary Search: 매번 절반 제거, O(log n). |
| 5 | **Tree & BFS/DFS** | DFS: 재귀, 깊이 우선. BFS: 큐, 레벨 순회. |
| 6 | **Dynamic Programming** | 상태 정의 → 점화식 → 기저 조건. Bottom-up for 루프가 면접에서 선호. |
| 7 | **면접 전략** | 45분 타임라인, 패턴 인식 플로차트, 엣지 케이스 체크리스트. |

## 패턴 인식 플로차트

```
문제 수신
    |
    v
"입력이 정렬되어 있는가?"
    +-- YES → Binary Search 또는 Two Pointers
    |
    v
"연속 부분 배열/부분 문자열?"
    +-- YES → Sliding Window
    |
    v
"두 값의 관계 (합, 차)?"
    +-- YES + 정렬 가능   → Two Pointers
    +-- YES + 정렬 불가   → Hash Map
    |
    v
"트리/그래프 구조?"
    +-- YES + 레벨 순서   → BFS
    +-- YES + 경로/깊이   → DFS
    |
    v
"최대/최소/경우의 수?"
    +-- YES + 이전 선택이 다음에 영향 → DP
    |
    v
"매칭 쌍 / 중첩 구조?"
    +-- YES → Stack
    |
    v
"해당 없음" → Brute Force 먼저, 그 다음 최적화
```

## 추천 연습 문제 (16문제)

| 패턴 | Easy | Medium |
|------|------|--------|
| Hash Map | Two Sum (#1) | Group Anagrams (#49) |
| Two Pointers | Valid Palindrome (#125) | 3Sum (#15) |
| Sliding Window | Max Avg Subarray (#643) | Longest Substring Without Repeat (#3) |
| Stack | Valid Parentheses (#20) | Daily Temperatures (#739) |
| Binary Search | Search Insert (#35) | Search Rotated Array (#33) |
| Tree DFS | Max Depth (#104) | Path Sum II (#113) |
| Tree BFS | Level Order (#102) | Right Side View (#199) |
| DP | Climbing Stairs (#70) | House Robber (#198) |

## 파일 구성

```
00_summary.md              ← 이 파일 (한글 요약)
01_big_o.sv                ← Big-O 코드 예시
01_big_o_explained.md      ← Big-O 한글 상세 설명
02_array_hashmap.sv        ← Hash Map 코드 예시
02_array_hashmap_explained.md
03_two_pointers_sliding_window.sv
03_two_pointers_sliding_window_explained.md
04_stack_binary_search.sv
04_stack_binary_search_explained.md
05_tree_bfs_dfs.sv
05_tree_bfs_dfs_explained.md
06_dynamic_programming.sv
06_dynamic_programming_explained.md
07_interview_strategy.md   ← 면접 전략 (한글)
```


--8<-- "abbreviations.md"
