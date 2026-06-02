---
title: "Quiz — Module 05: Tree & BFS/DFS"
---

[← Module 05 본문으로 돌아가기](../../05_tree_bfs_dfs_explained/)

---

## Q1. (Remember)

Preorder, Inorder, Postorder 의 방문 순서를 root/left/right 기준으로 적어라.

<details>
<summary>정답 / 해설</summary>

- **Preorder** : Root → Left → Right.
- **Inorder** : Left → Root → Right.
- **Postorder** : Left → Right → Root.

BST 의 inorder = 정렬된 순서.

세 순서는 "루트를 언제 방문하는가"로 구별하면 쉽게 외울 수 있다. Preorder 는 루트를 가장 먼저(pre) 방문하고, Postorder 는 자식을 모두 처리한 후(post) 루트를 방문하며, Inorder 는 왼쪽과 오른쪽 사이(in) 에 루트를 방문한다. BST 에서 inorder 가 정렬된 순서가 되는 이유는 BST 의 정의(왼쪽 < 루트 < 오른쪽)를 재귀적으로 따르면 오름차순으로 방문하게 되기 때문이다.

</details>
## Q2. (Understand)

BFS 가 최단 경로(unweighted)에 자연스러운 이유는?

<details>
<summary>정답 / 해설</summary>

BFS 는 가까운 노드부터 level by level 로 방문하므로, 처음으로 목표 노드를 만나는 시점이 곧 최소 step 거리. DFS 는 깊이 우선이라 같은 거리의 다른 경로를 더 늦게 발견할 수 있다.

BFS 가 최단 경로를 보장하는 이유는 큐의 FIFO 성질에 있다. 거리 k 의 노드가 모두 큐에 들어간 뒤에야 거리 k+1 의 노드가 처리되므로, 목적 노드를 처음 발견하는 순간은 반드시 최소 거리 시점이다. DFS 는 한 방향으로 끝까지 내려가기 때문에 목적 노드에 도달하더라도 그것이 최단 경로인지 보장하지 못한다. 이 성질은 비가중치 그래프에만 적용되며, 가중치가 있는 경우에는 Dijkstra 알고리즘이 필요하다.

</details>
## Q3. (Apply)

Binary Tree Level Order Traversal 을 BFS 로 풀어라.

<details>
<summary>정답 / 해설</summary>

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

`for _ in range(len(q)):` 가 핵심 트릭이다. 반복 시작 전에 큐 길이를 고정함으로써 현재 레벨의 노드 수만 처리하고, 그 안에서 자식을 큐에 추가해도 다음 레벨로 넘어가지 않는다. 이를 빼먹으면 여러 레벨의 노드가 한 배열에 섞여 level 별 그룹화가 불가능하다. 시간 복잡도는 O(N), 공간은 가장 넓은 레벨의 노드 수에 비례하는 O(W) 이다.

</details>
## Q4. (Analyze)

DFS 의 시간/공간 복잡도를 분석하라 (V 노드, E 엣지).

<details>
<summary>정답 / 해설</summary>

- **시간** : O(V + E) — 모든 노드를 한 번 방문, 모든 엣지를 한 번 본다.
- **공간** : 재귀 stack O(H) (트리 높이) ~ O(V) (skewed tree 의 worst). 명시적 stack 도 동일.

트리에서 평균 높이 H ≈ log V (균형 잡힌 경우), 최악 V (리스트 형태).

시간 O(V + E) 는 DFS 가 각 노드를 정확히 한 번 방문하고 각 엣지를 정확히 한 번 탐색한다는 사실에서 나온다. 공간 O(H) 는 재귀 콜 스택의 최대 깊이가 트리 높이에 비례하기 때문이다. 균형 이진 트리(H ≈ log V)와 완전히 기울어진 트리(H = V) 사이에 공간 사용량이 log V 배 차이나므로, 입력 트리의 균형 여부가 실질적인 메모리 소비를 결정한다.

</details>
## Q5. (Evaluate)

같은 트리 문제에 BFS vs DFS 중 BFS 가 더 좋은 신호 두 가지는?

<details>
<summary>정답 / 해설</summary>

1. **최단 경로 / 가장 가까운 X** — BFS 가 자연스럽다.
2. **Level / Depth 별 처리** — level-order traversal, "k 번째 level 의 합" 같은 문제.

DFS 는 **경로 reconstruction, 부분 트리 sum, BST inorder** 가 자연스럽다.

BFS 를 선택해야 하는 신호는 "거리" 또는 "레벨"이라는 단어가 문제에 등장할 때다. BFS 의 큐는 가까운 노드부터 순서대로 꺼내주기 때문에 거리 정보가 자연스럽게 포함된다. 반면 DFS 는 재귀 호출 스택 위에서 경로 정보를 누적하기 쉬워 "루트에서 리프까지 경로", "부분 트리의 합" 같이 경로나 subtree 전체를 다뤄야 할 때 더 적합하다. 문제를 읽자마자 이 구분이 떠오르면 패턴 선택에 걸리는 시간을 크게 줄일 수 있다.

</details>
