# Module 05 — Tree & BFS/DFS

<!-- DV-SKOOL-CH-CTX:start -->
<div class="chapter-context" data-cat="applied">
  <a class="chapter-back" href="../">
    <span class="chapter-back-arrow">←</span>
    <span class="chapter-back-icon">📐</span>
    <span class="chapter-back-text">BigTech Algorithm</span>
  </a>
  <span class="chapter-divider">›</span>
  <span class="chapter-marker">Module 05</span>
</div>
<!-- DV-SKOOL-CH-CTX:end -->

<!-- DV-SKOOL-CH-TOC:start -->
<div class="page-toc">
  <span class="page-toc-label">목차</span>
  <a class="page-toc-link" href="#1-why-care-이-모듈이-왜-필요한가">1. Why care?</a>
  <a class="page-toc-link" href="#2-intuition-비유와-한-장-그림">2. Intuition</a>
  <a class="page-toc-link" href="#3-작은-예-bfs-로-작은-트리를-level-별로-순회">3. 작은 예 — BFS Level Traversal</a>
  <a class="page-toc-link" href="#4-일반화-bfs-vs-dfs-와-dfs-템플릿">4. 일반화</a>
  <a class="page-toc-link" href="#5-디테일-traversal-3-종-path-sum-코드">5. 디테일</a>
  <a class="page-toc-link" href="#6-흔한-오해-와-디버그-체크리스트">6. 흔한 오해 + 디버그</a>
  <a class="page-toc-link" href="#7-핵심-정리-key-takeaways">7. 핵심 정리</a>
</div>
<!-- DV-SKOOL-CH-TOC:end -->

!!! objective "학습 목표"
    이 모듈을 마치면:

    - **Define** Tree, Binary Tree, BST 의 정의와 BFS/DFS (preorder/inorder/postorder) 의 차이를 적을 수 있다.
    - **Explain** BFS 가 최단 경로를, DFS 가 경로 합/조합을 자연스럽게 다루는 이유를 설명할 수 있다.
    - **Apply** Level Order Traversal, LCA, Path Sum 같은 전형 문제를 BFS/DFS 로 풀 수 있다.
    - **Analyze** 재귀 DFS 의 시간/공간 복잡도와 명시적 stack 변환을 분석할 수 있다.
    - **Evaluate** "BFS 가 좋은가, DFS 가 좋은가" 를 메모리/조기 종료 관점에서 평가할 수 있다.

!!! info "사전 지식"
    - Module 01–04
    - 재귀의 호출 stack 동작 이해, 큐 (FIFO) 의 기본

---

## 1. Why care? — 이 모듈이 왜 필요한가

Tree / Graph 탐색은 **인터뷰에서 가장 큰 문제 군** 입니다. 상속 / 트리 / 의존성 / 그래프 모두 같은 패턴 (BFS / DFS) 으로 풀립니다. 이 모듈은 "이 문제가 BFS 인지 DFS 인지" 를 빠르게 분류하는 직관과, DFS 4 줄 템플릿으로 _대부분의 트리 문제를 풀이로 연결하는_ 메타-스킬을 만듭니다.

이 모듈을 건너뛰면 트리/그래프 문제가 매번 _처음부터 풀이를 만들어야 하는_ 일이 됩니다. 반대로 **DFS 템플릿 (base / left / right / combine)** 이 손에 익으면, Max Depth · Tree Sum · Is Balanced · Path Sum 이 모두 _10 줄 안에_ 끝납니다.

---

## 2. Intuition — 비유와 한 장 그림

!!! tip "💡 한 줄 비유"
    **BFS** ≈ **가까운 사람부터 인사** — 같은 거리(레벨) 의 모두에게 인사한 뒤, 다음 레벨로.<br>
    **DFS** ≈ **한 친구 따라 끝까지 갔다 돌아옴** — 한 자식의 끝까지 깊이 들어가고, 막히면 backtrack 해서 형제 노드로.

### 한 장 그림 — 같은 트리, 다른 순회 순서

```
                    ┌─ 5 ─┐                         BFS visit 순서:
                    │     │                         ───────────────
                  ┌─3   ┌─8                          5  →  3, 8  →  1, 4
                  │     │                            (level 0) (level 1) (level 2)
                  1     4                                                      
                                                    DFS preorder:        
   (BFS: level by level)                            5  →  3  →  1  →  4  →  8
                                                    (root, then deep left)
   level 0:        5                                                
                  ╱ ╲                               DFS inorder (BST = sorted!):
   level 1:      3   8                              1  →  3  →  4  →  5  →  8
                ╱ ╲                                                
   level 2:    1   4                                DFS postorder:    
                                                    1  →  4  →  3  →  8  →  5
   자료구조:  큐 (FIFO)                              자료구조: 재귀(stack), LIFO
   메모리:    O(width)                               메모리:   O(height)
   강점:      "최단 경로", "가장 가까운 X"          강점:    "경로", "합", "조합"
```

### 왜 이렇게 설계됐는가 — Design rationale

**BFS 의 큐 (FIFO)** 는 _이미 push 된 노드가 가장 먼저 visit_ 되는 구조 → "가까운 노드가 항상 먼저" 라는 _최단 경로의 자연스러운 모델_. weighted 가 아닌 그래프의 BFS 는 _그 자체로 BFS 단계 = 거리_.

**DFS 의 stack (재귀)** 은 _가장 최근에 push 된 노드가 먼저 visit_ → "한 자식의 끝까지 들어가고 돌아옴" 이라는 _경로 추적의 자연스러운 모델_. 경로 합 / 조합 / path reconstruction 이 모두 "들어갔다 나오기" 의 변형.

두 패턴이 _같은 트리에 다른 순서_ 를 주는 이유는 **자료구조의 차이 (Queue vs Stack)** 때문이며, 그래서 _문제의 키워드_ 로 어느 패턴이 자연스러운지 결정해야 합니다.

---

## 3. 작은 예 — BFS 로 작은 트리를 Level 별로 순회

가장 단순한 시나리오. 다음 트리를 BFS 로 _레벨별로_ 출력 (Level Order Traversal #102).

```
            5
           ╱ ╲
          3   8
         ╱ ╲
        1   4
```

### 단계별 추적

```
   초기:  queue = [5]
                   ▲ root push

   ┌─ 반복 1 (level 0) ─────────────────────────────┐
   │  level_size = queue.size() = 1                  │
   │  for i in 0..1:                                 │
   │    pop 5  →  level=[5]                           │
   │    push 5.left=3, 5.right=8                      │
   │  result.append([5])                              │
   │  queue = [3, 8]                                  │
   └──────────────────────────────────────────────────┘

   ┌─ 반복 2 (level 1) ─────────────────────────────┐
   │  level_size = 2                                 │
   │  for i in 0..2:                                 │
   │    pop 3  →  level=[3]                           │
   │    push 3.left=1, 3.right=4                      │
   │    pop 8  →  level=[3,8]                         │
   │    8.left=null, 8.right=null  (push 안 함)        │
   │  result.append([3, 8])                           │
   │  queue = [1, 4]                                  │
   └──────────────────────────────────────────────────┘

   ┌─ 반복 3 (level 2) ─────────────────────────────┐
   │  level_size = 2                                 │
   │  for i in 0..2:                                 │
   │    pop 1, pop 4  →  level=[1, 4]                 │
   │    둘 다 leaf → push 없음                          │
   │  result.append([1, 4])                           │
   │  queue = []  →  while 종료                       │
   └──────────────────────────────────────────────────┘

   결과: [[5], [3, 8], [1, 4]]
```

### 단계별 의미

| Step | 누가 | 무엇을 | 왜 |
|------|------|--------|-----|
| ① | init | `queue.push(root=5)` | 시작점 |
| ② | level snap | `level_size = queue.size()` | _현재 레벨_ 의 노드 수를 _다음 push 가 일어나기 전_ 에 고정 |
| ③ | dequeue | `pop 5` | FIFO — 들어온 순서로 visit |
| ④ | enqueue | `push 3, push 8` | 다음 레벨 노드를 큐 끝에 |
| ⑤ | level done | `result.append([5])` | level_size 만큼 처리하면 한 레벨 끝 |
| ⑥ | next level | `queue=[3,8]`, level_size=2 | level_size 가 _다음 레벨의 정확한 개수_ |
| ⑦ | empty queue | while 종료 | 모든 노드 visit 완료 |

```python
from collections import deque
def level_order(root):
    if not root: return []
    q, result = deque([root]), []
    while q:
        level_size = len(q)              # 핵심: snapshot of current level
        level = []
        for _ in range(level_size):
            node = q.popleft()
            level.append(node.val)
            if node.left:  q.append(node.left)
            if node.right: q.append(node.right)
        result.append(level)
    return result
```

!!! note "여기서 잡아야 할 두 가지"
    **(1) `level_size = queue.size()` 의 _스냅샷_ 이 핵심** — push 가 새로 일어나기 _전에_ 고정해야 _현재 레벨만_ 처리합니다. 이 한 줄을 빼면 모든 레벨이 한 덩어리로 섞입니다.<br>
    **(2) FIFO 가 곧 "거리 단조 증가"** — 큐에서 먼저 나오는 노드가 항상 _root 에서 더 가깝거나 같다_. 이게 unweighted 그래프 BFS 가 _최단 경로 알고리즘_ 인 이유.

---

## 4. 일반화 — BFS vs DFS 와 DFS 템플릿

### 4.1 신호 매핑 표

| 문제 키워드 | 자연스러운 패턴 |
|---|---|
| "레벨 / 깊이별 그룹" | BFS |
| "최단 거리 / 가장 가까운 X" | BFS |
| "경로 합 / 경로 reconstruction" | DFS |
| "트리 높이 / 직경 / sum" | DFS |
| "Inorder of BST → 정렬된 출력" | DFS (inorder) |
| "Cycle 감지" | DFS + visited |
| "Topological sort" | DFS post-order 또는 BFS (Kahn) |

### 4.2 DFS / BFS 비교 표

| | DFS (깊이 우선) | BFS (너비 우선) |
|--|----------------|----------------|
| 자료구조 | **재귀 (Stack)** | **큐 (FIFO)** |
| 탐색 순서 | 깊이 먼저 → 백트래킹 | 같은 레벨 먼저 |
| 키워드 | "높이", "깊이", "경로", "합" | "레벨", "최단", "너비" |
| 공간 | O(h) — 트리 높이 | O(w) — 트리 너비 |
| 대표 문제 | Max Depth, Path Sum | Level Order, Right Side View |

### 4.3 DFS 4 줄 템플릿 — 대부분의 트리 문제를 이것으로

```
function dfs(node):
    if (node == null) return 기저값;             # ① 기저 조건
    left_result  = dfs(node.left);               # ② 왼쪽 재귀
    right_result = dfs(node.right);              # ③ 오른쪽 재귀
    return combine(left_result, right_result);   # ④ 결합

문제별 적용:
   Max Depth:   기저=0,           결합=max(L,R)+1
   Tree Sum:    기저=0,           결합=L+R+현재값
   Is Balanced: 기저=0,           결합=abs(L-R)<=1 && ...
   Path Sum:    기저=현재==target, 결합=L||R (경로 존재?)
```

이 4 줄에 _기저값_ 과 _combine_ 만 바꾸면 거의 모든 DFS 문제가 풀립니다.

---

## 5. 디테일 — Traversal 3 종, Path Sum, 코드

### 5.1 트리 기본 용어

```
Binary Tree (이진 트리): 각 노드가 최대 2 개의 자식 (left, right)

         5          ← root (루트)
        ╱ ╲
       3   8        ← depth 1 (깊이 1)
      ╱ ╲
     1   4          ← leaf (리프, 자식 없음)

   root: 최상위 노드
   leaf: 자식이 없는 노드
   depth: 루트에서의 거리
   height: 가장 깊은 리프까지의 거리 (이 트리: 3)
```

### 5.2 Max Depth — Dry Run (DFS 템플릿 적용)

```
         5
        ╱ ╲
       3   8
      ╱ ╲
     1   4

max_depth(5):
   max_depth(3):
     max_depth(1):
       max_depth(null) = 0  (left)
       max_depth(null) = 0  (right)
       return max(0,0)+1 = 1
     max_depth(4):
       return max(0,0)+1 = 1
     return max(1,1)+1 = 2
   max_depth(8):
     return max(0,0)+1 = 1
   return max(2,1)+1 = 3   ← 답

재귀 호출 트리:
   max_depth(5) = 3
     max_depth(3) = 2
       max_depth(1) = 1
       max_depth(4) = 1
     max_depth(8) = 1
```

### 5.3 DFS 3 가지 순서 (Traversal)

```
Pre-order  (전위):  현재 → 왼쪽 → 오른쪽   (5,3,1,4,8)
In-order   (중위):  왼쪽 → 현재 → 오른쪽   (1,3,4,5,8)  ← BST 에서 정렬!
Post-order (후위):  왼쪽 → 오른쪽 → 현재   (1,4,3,8,5)

면접 팁: In-order + BST = 정렬된 순서 출력
```

### 5.4 BFS — 단일 큐 (level 구분 없음)

```
큐에 루트 삽입 → 큐가 빌 때까지:
   front 꺼냄 → 처리 → 자식을 큐에 삽입

         5
        ╱ ╲
       3   8
      ╱ ╲
     1   4

큐: [5]
   pop 5, push 3,8 → 큐: [3, 8]     → 출력: 5
   pop 3, push 1,4 → 큐: [8, 1, 4]  → 출력: 3
   pop 8            → 큐: [1, 4]     → 출력: 8
   pop 1            → 큐: [4]        → 출력: 1
   pop 4            → 큐: []         → 출력: 4

결과: 5, 3, 8, 1, 4 (레벨 순서)
```

### 5.5 BFS 레벨 구분 패턴 (§3 의 일반화)

```
"각 레벨별로 노드를 묶어라" (Level Order Traversal #102)

while (큐 not empty):
    level_size = 큐.size()      ← 현재 레벨의 노드 수 _스냅샷_
    for i in range(level_size):
        node = 큐.pop()
        현재_레벨에 추가
        자식을 큐에 push
    결과에 현재_레벨 추가

결과: [[5], [3,8], [1,4]]
```

### 5.6 Path Sum (LeetCode #112) — DFS 응용 Dry Run

```
문제: 루트에서 리프까지의 경로 합이 target 인 경로가 존재하는가?

         5
        ╱ ╲
       4   8
      ╱   ╱ ╲
     11  13  4
    ╱ ╲       ╲
   7   2       1

target = 22

사고 과정:
   1. "경로" + "합" → DFS
   2. 루트에서 리프까지 내려가면서 남은 합(remain) 을 줄여감
   3. 리프에서 remain == 0 이면 경로 발견

DFS 템플릿 적용:
   기저 조건: node 가 리프이고 remain==0 → return 1
   결합: 왼쪽 || 오른쪽 (하나만 성공해도 OK)

Dry Run (remain = target - 현재값):
   has_path(5, 22):  remain = 22-5 = 17
     has_path(4, 17):  remain = 17-4 = 13
       has_path(11, 13): remain = 13-11 = 2
         has_path(7, 2):  remain = 2-7 = -5
           리프, remain≠0 → return 0
         has_path(2, 2):  remain = 2-2 = 0
           리프, remain==0 → return 1 ✓
         return 0 || 1 = 1 ✓
       return 1 (왼쪽이 성공했으므로 전파)
     return 1

   경로: 5 → 4 → 11 → 2 = 22 ✓
```

#### Path Sum II (LeetCode #113) — 경로 자체를 수집

```
Path Sum I:  존재 여부만 (return bit)
Path Sum II: 경로를 모두 수집 (return list of paths)

차이점:
   - 현재 경로를 리스트로 유지 (path 에 push/pop)
   - 리프에서 remain==0 이면 현재 path 를 결과에 추가
   - 백트래킹: 재귀 복귀 시 path 에서 pop (원래 상태 복원)

이 "push → 재귀 → pop" 패턴이 Backtracking 의 핵심!
```

### 5.7 면접 팁 — 트리 문제 풀이 순서

```
트리 문제 → 먼저 "DFS 인가 BFS 인가?" 판단:
   "깊이/높이/경로" → DFS (재귀 템플릿)
   "레벨/최단" → BFS (큐 + 레벨 루프)

DFS 풀이 순서:
   1. 기저 조건 (null 일 때 뭘 반환?)
   2. 왼쪽/오른쪽 재귀
   3. 결합 (어떻게 합칠까?)

DFS 3 가지 순회 — 면접에서 물어보면:
   Pre-order:  "현재 먼저" → 트리 복사, 직렬화
   In-order:   "왼쪽 먼저" → BST 에서 정렬된 순서 출력
   Post-order: "자식 먼저" → 삭제, 높이 계산

엣지 케이스:
   - null (빈 트리)
   - 루트만 (단일 노드)
   - 편향 트리 (연결 리스트처럼 한쪽만)
   - 음수 값 포함 (Path Sum 에서 주의 — 경로 중간에 합이 target 이어도 리프가 아니면 X)
```

### 5.8 SystemVerilog 예제 코드

원본 파일: `05_tree_bfs_dfs.sv`

```systemverilog
// =============================================================
// Unit 5: Tree & BFS/DFS
// =============================================================
// Tree Basics:
//   - Binary Tree: each node has at most 2 children (left, right)
//   - root: top node, leaf: no children, depth: distance from root
//
// DFS (Depth-First Search):
//   - Go deep first, backtrack when stuck
//   - Uses: recursion (stack)
//   - Keywords: "height", "depth", "path", "sum"
//   - 3 orders: pre-order (root,L,R), in-order (L,root,R), post-order (L,R,root)
//
// BFS (Breadth-First Search):
//   - Visit all nodes at same level first
//   - Uses: queue (FIFO)
//   - Keywords: "level", "shortest", "breadth"
//
// DFS Template (covers most tree problems):
//   function dfs(node):
//       if (node == null) return base_value;       // 1. base case
//       left_result  = dfs(node.left);             // 2. left
//       right_result = dfs(node.right);            // 3. right
//       return combine(left_result, right_result); // 4. combine
// =============================================================

module unit5_tree;

  // ---------------------------------------------------------
  // Tree Node class
  // ---------------------------------------------------------
  class TreeNode;
    int val;
    TreeNode left;
    TreeNode right;

    function new(int v);
      val   = v;
      left  = null;
      right = null;
    endfunction
  endclass

  // ---------------------------------------------------------
  // DFS: Pre-order traversal (root -> left -> right)
  // Use: tree copy, serialization
  // ---------------------------------------------------------
  function automatic void dfs_preorder(TreeNode node);
    if (node == null) return;

    $display("%0d", node.val);     // visit current FIRST
    dfs_preorder(node.left);       // then left
    dfs_preorder(node.right);      // then right
  endfunction

  // ---------------------------------------------------------
  // DFS: In-order traversal (left -> root -> right)
  // Use: BST -> sorted output (most common in interviews)
  // ---------------------------------------------------------
  function automatic void dfs_inorder(TreeNode node);
    if (node == null) return;

    dfs_inorder(node.left);        // left FIRST
    $display("%0d", node.val);     // then current
    dfs_inorder(node.right);       // then right
  endfunction

  // ---------------------------------------------------------
  // DFS: Post-order traversal (left -> right -> root)
  // Use: delete tree, calculate height
  // ---------------------------------------------------------
  function automatic void dfs_postorder(TreeNode node);
    if (node == null) return;

    dfs_postorder(node.left);      // left first
    dfs_postorder(node.right);     // right second
    $display("%0d", node.val);     // current LAST
  endfunction

  // ---------------------------------------------------------
  // DFS: Max depth of binary tree
  // Template: base=0, combine=max(L,R)+1
  // ---------------------------------------------------------
  function automatic int max_depth(TreeNode node);
    if (node == null) return 0;

    int left_d  = max_depth(node.left);
    int right_d = max_depth(node.right);

    if (left_d > right_d)
      return left_d + 1;
    else
      return right_d + 1;
  endfunction

  // ---------------------------------------------------------
  // DFS: Sum of all node values
  // Template: base=0, combine=left+right+current
  // ---------------------------------------------------------
  function automatic int tree_sum(TreeNode node);
    if (node == null) return 0;
    return tree_sum(node.left) + tree_sum(node.right) + node.val;
  endfunction

  // ---------------------------------------------------------
  // BFS: Level-order traversal using queue
  // ---------------------------------------------------------
  function automatic void bfs(TreeNode root);
    TreeNode queue[$];
    if (root == null) return;

    queue.push_back(root);

    while (queue.size() > 0) begin
      TreeNode node = queue[0];      // front of queue (FIFO)
      queue.delete(0);

      $display("%0d", node.val);

      if (node.left != null)
        queue.push_back(node.left);
      if (node.right != null)
        queue.push_back(node.right);
    end
  endfunction

  // ---------------------------------------------------------
  // BFS with level separation (Level Order Traversal #102)
  // Key pattern: use level_size = queue.size() to process
  // all nodes at the same level before moving to next level.
  // ---------------------------------------------------------
  function automatic void bfs_by_level(TreeNode root);
    TreeNode queue[$];
    int level = 0;
    if (root == null) return;

    queue.push_back(root);

    while (queue.size() > 0) begin
      int level_size = queue.size();  // nodes at this level

      $write("Level %0d: ", level);
      for (int i = 0; i < level_size; i++) begin
        TreeNode node = queue[0];
        queue.delete(0);

        $write("%0d ", node.val);

        if (node.left != null)
          queue.push_back(node.left);
        if (node.right != null)
          queue.push_back(node.right);
      end
      $display("");
      level++;
    end
  endfunction

  // ---------------------------------------------------------
  // DFS: Path Sum — does root-to-leaf path with given sum exist?
  // Template: base=leaf check, combine=left||right
  // ---------------------------------------------------------
  function automatic bit has_path_sum(TreeNode node, int remain);
    if (node == null) return 0;

    remain -= node.val;

    // Leaf node: check if remaining sum is 0
    if (node.left == null && node.right == null)
      return (remain == 0);

    // Recurse: either left or right path works
    return has_path_sum(node.left, remain) ||
           has_path_sum(node.right, remain);
  endfunction

  // ---------------------------------------------------------
  // Test: Build tree and run all algorithms
  //
  //         5
  //        / \
  //       3   8
  //      / \
  //     1   4
  // ---------------------------------------------------------
  initial begin
    TreeNode n1 = new(5);
    TreeNode n2 = new(3);
    TreeNode n3 = new(8);
    TreeNode n4 = new(1);
    TreeNode n5 = new(4);

    n1.left  = n2; n1.right = n3;
    n2.left  = n4; n2.right = n5;

    // --- Three DFS traversal orders ---
    $display("--- DFS Pre-order (root,L,R) ---");
    dfs_preorder(n1);                // 5, 3, 1, 4, 8

    $display("--- DFS In-order (L,root,R) ---");
    dfs_inorder(n1);                 // 1, 3, 4, 5, 8 (sorted for BST!)

    $display("--- DFS Post-order (L,R,root) ---");
    dfs_postorder(n1);               // 1, 4, 3, 8, 5

    // --- DFS applications ---
    $display("--- Max Depth ---");
    $display("%0d", max_depth(n1));  // 3

    $display("--- Tree Sum ---");
    $display("%0d", tree_sum(n1));   // 21

    // --- BFS ---
    $display("--- BFS Level-order ---");
    bfs(n1);                         // 5, 3, 8, 1, 4

    $display("--- BFS by Level ---");
    bfs_by_level(n1);
    // Level 0: 5
    // Level 1: 3 8
    // Level 2: 1 4

    // --- Path Sum ---
    // Path 5->3->1 = 9, 5->3->4 = 12, 5->8 = 13
    $display("--- Path Sum ---");
    $display("sum=9:  %0b", has_path_sum(n1, 9));   // 1 (5->3->1)
    $display("sum=12: %0b", has_path_sum(n1, 12));   // 1 (5->3->4)
    $display("sum=13: %0b", has_path_sum(n1, 13));   // 1 (5->8)
    $display("sum=10: %0b", has_path_sum(n1, 10));   // 0 (no path)
  end

endmodule
```

---

## 6. 흔한 오해 와 디버그 체크리스트

### 흔한 오해

!!! danger "❓ 오해 1 — 'BFS 와 DFS 는 같은 결과를 다른 순서로 줄 뿐'"
    **실제**: BFS 는 _최단 경로_ 를 자연스럽게 보장 (FIFO 가 거리 순), DFS 는 _경로 reconstruction_ 에 자연스러움 (stack 이 backtrack). _최단 경로_ 가 답인 문제에서 DFS 를 쓰면 _모든 경로_ 를 다 봐야 하므로 비효율 + 잘못된 첫 답을 줄 수 있음.<br>
    **왜 헷갈리는가**: "순회" 라는 같은 카테고리 → 같은 결과로 단순화. 실제는 다른 의도.

!!! danger "❓ 오해 2 — '재귀 DFS 는 stack overflow 가 안 난다'"
    **실제**: skewed tree / 긴 linked-list 형태 그래프에서 DFS 재귀가 도중에 죽습니다. Python 은 `sys.setrecursionlimit` 기본값 ~1000, C++ 는 thread stack 크기 (보통 ~1 MB → 프레임당 수십 byte 가정 시 수만 깊이). 깊이가 한계에 닿으면 _명시적 stack_ 으로 변환.<br>
    **왜 헷갈리는가**: 균형 잡힌 트리 (h ≈ log N) 에 익숙해 깊이가 N 에 닿는 케이스를 잊음.

!!! danger "❓ 오해 3 — 'Path Sum 은 어떤 경로도 OK'"
    **실제**: LeetCode #112 의 path sum 은 _root → leaf_ 경로만. 중간에 합이 target 이어도 leaf 가 아니면 false. 이 경계 조건을 놓쳐 false positive 가 흔합니다. 음수 값이 있으면 경로 중간 합 = target 인데 끝까지 가야 하는 경우도 발생.<br>
    **왜 헷갈리는가**: "경로 합" 이라는 표현이 모호 — 어떤 경로의 합인지 명확히 하지 않으면 답이 다양해짐.

!!! danger "❓ 오해 4 — 'level_size 없이도 BFS 레벨 구분 가능'"
    **실제**: `level_size = queue.size()` 의 _스냅샷_ 없이 그냥 while 만 돌면 모든 레벨이 한 덩어리. _현재 레벨의 노드 수_ 를 push 가 일어나기 _전_ 에 고정해야 정확히 그만큼만 처리할 수 있습니다.<br>
    **왜 헷갈리는가**: 단순 BFS (출력만) 와 level-order 의 차이를 코드 한 줄로 본 결과.

### 디버그 체크리스트

| 증상 | 1차 의심 | 어디 보나 |
|---|---|---|
| 빈 트리에 대해 NPE/segfault | 기저 조건 (`node == null`) 누락 | DFS 첫 줄 — 반드시 null check |
| Skewed tree 에서 stack overflow | 재귀 깊이 한계 | 입력 N 과 언어 한계 비교, 명시적 stack 으로 변환 |
| Path Sum 이 중간 노드에서 true | "leaf 인지" 체크 누락 | `node.left == null && node.right == null` 인지 확인 |
| Level Order 가 모든 레벨 합쳐짐 | `level_size` 스냅샷 누락 | for 루프가 `range(queue.size())` 가 아닌 `range(level_size)` 인지 |
| BST inorder 가 정렬 안 됨 | left → current → right 순서 틀림 | `dfs(left)` 가 `print` 보다 _먼저_ 인지 |
| Right Side View 가 가운데 노드 출력 | 마지막 노드 = right 라 가정 | 각 레벨의 _마지막 push 된 노드_ 가 가장 right 인지 (level_size 끝 인덱스) |
| Cycle 있는 그래프에서 무한 루프 | `visited` set 누락 | DFS 진입 시 visited 표시, BFS 도 enqueue 시 표시 |
| LCA 가 부모 노드를 반환 | postorder 결합 로직 오류 | left/right 모두 찾으면 현재 노드, 아니면 non-null 쪽 |

---

## 7. 핵심 정리 (Key Takeaways)

- **BFS** — Queue, level by level. 최단 경로 / 가장 가까운 X 류 문제.
- **DFS** — Stack 또는 재귀, 깊이 우선. 경로 합 / 조합 / Path Reconstruction.
- **DFS 4 줄 템플릿** — base / left / right / combine. 기저값과 combine 만 바꾸면 대부분 풀린다.
- **Inorder traversal of BST = sorted** — 자주 활용되는 성질.
- **메모리** — BFS 는 가장 넓은 level 만큼, DFS 는 깊이만큼.

!!! warning "실무 주의점"
    - **Stack overflow** — skewed tree 에서 재귀 깊이 한계 도달 가능. 입력 N 큰 케이스는 명시적 stack 검토.
    - **Visited 표시** — 그래프 (트리 아님) 에서 cycle 무한 루프 방지의 핵심.
    - **Level snapshot** — BFS level-order 에서 `level_size = queue.size()` 한 줄을 빠뜨리면 모든 레벨이 섞임.

---

## 다음 모듈

→ [Module 06 — Dynamic Programming](06_dynamic_programming_explained.md): DFS + memoization 의 자연스러운 확장 — 부분 문제 답을 저장해 재사용.

[퀴즈 풀어보기 →](quiz/05_tree_bfs_dfs_explained_quiz.md)

<div class="chapter-nav">
  <a class="nav-prev" href="../04_stack_binary_search_explained/">
    <div class="nav-label">◀ 이전</div>
    <div class="nav-title">Stack & Binary Search</div>
  </a>
  <a class="nav-next" href="../06_dynamic_programming_explained/">
    <div class="nav-label">다음 ▶</div>
    <div class="nav-title">Dynamic Programming (DP)</div>
  </a>
</div>


--8<-- "abbreviations.md"
