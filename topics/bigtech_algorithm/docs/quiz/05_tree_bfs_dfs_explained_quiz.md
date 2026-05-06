# Quiz — Module 05: Tree & BFS/DFS

[← Module 05 본문으로 돌아가기](../05_tree_bfs_dfs_explained.md)

---

## Q1. (Remember)

Preorder, Inorder, Postorder 의 방문 순서를 root/left/right 기준으로 적어라.

??? answer "정답 / 해설"
    - **Preorder** : Root → Left → Right.
    - **Inorder** : Left → Root → Right.
    - **Postorder** : Left → Right → Root.

    BST 의 inorder = 정렬된 순서.

## Q2. (Understand)

BFS 가 최단 경로(unweighted)에 자연스러운 이유는?

??? answer "정답 / 해설"
    BFS 는 가까운 노드부터 level by level 로 방문하므로, 처음으로 목표 노드를 만나는 시점이 곧 최소 step 거리. DFS 는 깊이 우선이라 같은 거리의 다른 경로를 더 늦게 발견할 수 있다.

## Q3. (Apply)

Binary Tree Level Order Traversal 을 BFS 로 풀어라.

??? answer "정답 / 해설"
    ```python
    from collections import deque
    def level_order(root):
        if not root: return []
        out, q = [], deque([root])
        while q:
            level = []
            for _ in range(len(q)):
                node = q.popleft()
                level.append(node.val)
                if node.left:  q.append(node.left)
                if node.right: q.append(node.right)
            out.append(level)
        return out
    ```
    각 level 마다 현재 큐 길이를 고정해 같은 level 의 노드만 처리.

## Q4. (Analyze)

DFS 의 시간/공간 복잡도를 분석하라 (V 노드, E 엣지).

??? answer "정답 / 해설"
    - **시간** : O(V + E) — 모든 노드를 한 번 방문, 모든 엣지를 한 번 본다.
    - **공간** : 재귀 stack O(H) (트리 높이) ~ O(V) (skewed tree 의 worst). 명시적 stack 도 동일.

    트리에서 평균 높이 H ≈ log V (균형 잡힌 경우), 최악 V (리스트 형태).

## Q5. (Evaluate)

같은 트리 문제에 BFS vs DFS 중 BFS 가 더 좋은 신호 두 가지는?

??? answer "정답 / 해설"
    1. **최단 경로 / 가장 가까운 X** — BFS 가 자연스럽다.
    2. **Level / Depth 별 처리** — level-order traversal, "k 번째 level 의 합" 같은 문제.

    DFS 는 **경로 reconstruction, 부분 트리 sum, BST inorder** 가 자연스럽다.
