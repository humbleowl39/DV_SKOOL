# Unit 5: Tree & BFS/DFS

<div class="learning-meta">
  <span class="meta-badge meta-level-intermediate">📊 Intermediate</span>
</div>

## 트리 기본 용어

```
Binary Tree (이진 트리): 각 노드가 최대 2개의 자식(left, right)

        5          ← root (루트)
       / \
      3   8        ← depth 1 (깊이 1)
     / \
    1   4          ← leaf (리프, 자식 없음)

  root: 최상위 노드
  leaf: 자식이 없는 노드
  depth: 루트에서의 거리
  height: 가장 깊은 리프까지의 거리 (이 트리: 3)
```

## DFS vs BFS — 언제 어떤 것?

| | DFS (깊이 우선) | BFS (너비 우선) |
|--|----------------|----------------|
| 자료구조 | **재귀 (Stack)** | **큐 (FIFO)** |
| 탐색 순서 | 깊이 먼저 → 백트래킹 | 같은 레벨 먼저 |
| 키워드 | "높이", "깊이", "경로", "합" | "레벨", "최단", "너비" |
| 공간 | O(h) — 트리 높이 | O(w) — 트리 너비 |
| 대표 문제 | Max Depth, Path Sum | Level Order, Right Side View |

## DFS 템플릿 — 대부분의 트리 문제를 이것으로 해결

```
function dfs(node):
    if (node == null) return 기저값;       // 1. 기저 조건
    left_result  = dfs(node.left);         // 2. 왼쪽 재귀
    right_result = dfs(node.right);        // 3. 오른쪽 재귀
    return combine(left_result, right_result); // 4. 결합

문제별 적용:
  Max Depth:   기저=0,  결합=max(L,R)+1
  Tree Sum:    기저=0,  결합=L+R+현재값
  Is Balanced: 기저=0,  결합=abs(L-R)<=1 && L!=-1 && R!=-1
  Path Sum:    기저=현재==target, 결합=L||R (경로 존재?)
```

### Max Depth — Dry Run

```
        5
       / \
      3   8
     / \
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
  return max(2,1)+1 = 3  ← 답

재귀 호출 트리:
  max_depth(5) = 3
    max_depth(3) = 2
      max_depth(1) = 1
      max_depth(4) = 1
    max_depth(8) = 1
```

### DFS 3가지 순서 (Traversal)

```
Pre-order  (전위):  현재 → 왼쪽 → 오른쪽  (5,3,1,4,8)
In-order   (중위):  왼쪽 → 현재 → 오른쪽  (1,3,4,5,8) ← BST에서 정렬!
Post-order (후위):  왼쪽 → 오른쪽 → 현재  (1,4,3,8,5)

면접 팁: In-order + BST = 정렬된 순서 출력
```

## BFS — Level-Order Traversal

```
큐에 루트 삽입 → 큐가 빌 때까지:
  front 꺼냄 → 처리 → 자식을 큐에 삽입

        5
       / \
      3   8
     / \
    1   4

큐: [5]
  pop 5, push 3,8 → 큐: [3, 8]     → 출력: 5
  pop 3, push 1,4 → 큐: [8, 1, 4]  → 출력: 3
  pop 8            → 큐: [1, 4]     → 출력: 8
  pop 1            → 큐: [4]        → 출력: 1
  pop 4            → 큐: []         → 출력: 4

결과: 5, 3, 8, 1, 4 (레벨 순서)
```

### BFS 레벨 구분 패턴 (면접에서 자주 필요)

```
"각 레벨별로 노드를 묶어라" (Level Order Traversal #102)

while (큐 not empty):
    level_size = 큐.size()     ← 현재 레벨의 노드 수
    for i in range(level_size):
        node = 큐.pop()
        현재_레벨에 추가
        자식을 큐에 push
    결과에 현재_레벨 추가

결과: [[5], [3,8], [1,4]]
```

---

## Path Sum (LeetCode #112) — DFS 응용 Dry Run

```
문제: 루트에서 리프까지의 경로 합이 target인 경로가 존재하는가?

        5
       / \
      4   8
     /   / \
    11  13   4
   / \        \
  7   2        1

target = 22

사고 과정:
  1. "경로" + "합" → DFS
  2. 루트에서 리프까지 내려가면서 남은 합(remain)을 줄여감
  3. 리프에서 remain == 0이면 경로 발견

DFS 템플릿 적용:
  기저 조건: node가 리프이고 remain==0 → return 1
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

### Path Sum II (LeetCode #113) — 경로 자체를 수집

```
Path Sum I: 존재 여부만 (return bit)
Path Sum II: 경로를 모두 수집 (return list of paths)

차이점:
  - 현재 경로를 리스트로 유지 (path에 push/pop)
  - 리프에서 remain==0이면 현재 path를 결과에 추가
  - 백트래킹: 재귀 복귀 시 path에서 pop (원래 상태 복원)

이 "push → 재귀 → pop" 패턴이 Backtracking의 핵심!
```

---

## 면접 팁

```
트리 문제 → 먼저 "DFS인가 BFS인가?" 판단:
  "깊이/높이/경로" → DFS (재귀 템플릿)
  "레벨/최단" → BFS (큐 + 레벨 루프)

DFS 풀이 순서:
  1. 기저 조건 (null일 때 뭘 반환?)
  2. 왼쪽/오른쪽 재귀
  3. 결합 (어떻게 합칠까?)

DFS 3가지 순회 — 면접에서 물어보면:
  Pre-order:  "현재 먼저" → 트리 복사, 직렬화
  In-order:   "왼쪽 먼저" → BST에서 정렬된 순서 출력
  Post-order: "자식 먼저" → 삭제, 높이 계산

엣지 케이스:
  - null (빈 트리)
  - 루트만 (단일 노드)
  - 편향 트리 (연결 리스트처럼 한쪽만)
  - 음수 값 포함 (Path Sum에서 주의 — 경로 중간에 합이 target이어도 리프가 아니면 X)
```


---

## 부록: SystemVerilog 예제 코드

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
  // Test: Build tree and run algorithms
  //
  //         5
  //        / \
  //       3   8
  //      / \
  //     1   4
  // ---------------------------------------------------------
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
