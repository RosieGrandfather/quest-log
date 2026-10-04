"""dsa-0 第 9 节：图：表示、BFS、DFS、拓扑排序"""
from unitlib import *
from runlib import code

C_REPR = code('''
from collections import defaultdict

n = 5
edges = [(0, 1), (0, 2), (1, 3), (2, 3), (3, 4)]

# 邻接表 (adjacency list)：每个点记一个「邻居列表」
adj = defaultdict(list)
for u, v in edges:
    adj[u].append(v)                     # 无向图：一条边要记两个方向
    adj[v].append(u)
print(dict(adj))

# 邻接矩阵 (adjacency matrix)：matrix[u][v] = 1 表示 u、v 之间有边
matrix = [[0] * n for _ in range(n)]
for u, v in edges:
    matrix[u][v] = matrix[v][u] = 1
for row in matrix:
    print(row)

# 空间对比：社交网络，10 万个用户，平均每人约 6 个好友，一共约 30 万条边
V, E = 10**5, 3 * 10**5
print("邻接矩阵的格子数：", V * V, "   邻接表存的边的条数：", 2 * E)
''')

C_BFS = code('''
from collections import deque, defaultdict

edges = [(0, 1), (0, 2), (1, 3), (2, 3), (3, 4), (4, 5), (2, 6)]
adj = defaultdict(list)
for u, v in edges:
    adj[u].append(v)
    adj[v].append(u)

def bfs(adj, s):
    dist, parent, order = {s: 0}, {s: None}, []
    q = deque([s])                       # 队列：先发现的先处理，所以是一层一层向外扩
    while q:
        u = q.popleft()
        order.append(u)
        for v in adj[u]:
            if v not in dist:            # 第一次到达 v：此刻的层数就是 s 到 v 的最短距离
                dist[v] = dist[u] + 1
                parent[v] = u            # 记住是从谁那里来的，可以倒推出路径
                q.append(v)
    return order, dist, parent

def path(parent, t):                     # 沿 parent 倒着走回起点，再反转
    p = []
    while t is not None:
        p.append(t)
        t = parent[t]
    return p[::-1]

order, dist, parent = bfs(adj, 0)
print("访问顺序：", order)
print("到各点的最短距离：", dist)
print("0 到 5 的最短路径：", path(parent, 5))
''')

C_DFS = code('''
from collections import defaultdict

edges = [(0, 1), (0, 2), (1, 3), (2, 3), (3, 4), (4, 5), (2, 6)]
adj = defaultdict(list)
for u, v in edges:
    adj[u].append(v)
    adj[v].append(u)

def dfs_rec(adj, u, seen, order):        # 递归版：一条路走到底，走不通再回头
    seen.add(u)
    order.append(u)
    for v in adj[u]:
        if v not in seen:
            dfs_rec(adj, v, seen, order)

def dfs_iter(adj, s):                    # 迭代版：自己维护一个栈，不会受递归深度限制
    seen, order, stack = set(), [], [s]
    while stack:
        u = stack.pop()
        if u in seen:
            continue
        seen.add(u)
        order.append(u)
        for v in reversed(adj[u]):       # 反过来压栈，这样访问顺序和递归版一致
            stack.append(v)
    return order

order = []
dfs_rec(adj, 0, set(), order)
print("递归版访问顺序：", order)
print("迭代版访问顺序：", dfs_iter(adj, 0), "与递归版相同：", dfs_iter(adj, 0) == order)

# 一条很长的链：0-1-2-...-4999。递归版会爆栈，迭代版没问题
chain = defaultdict(list)
for i in range(4999):
    chain[i].append(i + 1)
try:
    dfs_rec(chain, 0, set(), [])
except RecursionError:
    print("递归版：RecursionError")
print("迭代版访问了", len(dfs_iter(chain, 0)), "个节点")
''')

C_GRID = code('''
from collections import deque

def count_islands(grid):                 # 连通分量：每遇到一块没访问过的陆地，就把它整块「淹掉」，计数加 1
    R, C = len(grid), len(grid[0])
    seen, count = set(), 0
    for r in range(R):
        for c in range(C):
            if grid[r][c] == "1" and (r, c) not in seen:
                count += 1
                seen.add((r, c))
                stack = [(r, c)]
                while stack:
                    x, y = stack.pop()
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):    # 上下左右四个邻居
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < R and 0 <= ny < C and grid[nx][ny] == "1" and (nx, ny) not in seen:
                            seen.add((nx, ny))
                            stack.append((nx, ny))
    return count

grid = ["11000",
        "11000",
        "00100",
        "00011"]
print("岛屿数量：", count_islands(grid))

def maze_steps(maze):                    # 网格迷宫的最短步数：把每个格子看成一个点，用 BFS
    R, C = len(maze), len(maze[0])
    for r in range(R):
        for c in range(C):
            if maze[r][c] == "S":
                start = (r, c)
    dist, q = {start: 0}, deque([start])
    while q:
        x, y = q.popleft()
        if maze[x][y] == "E":
            return dist[(x, y)]
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if 0 <= nx < R and 0 <= ny < C and maze[nx][ny] != "#" and (nx, ny) not in dist:
                dist[(nx, ny)] = dist[(x, y)] + 1
                q.append((nx, ny))
    return -1                            # 走不到终点

maze = ["S.#....",
        ".##.##.",
        "...#...",
        ".#...#E"]
print("迷宫最短步数：", maze_steps(maze))
''')

C_TOPO = code('''
from collections import deque, defaultdict

# 课程的先修关系：「先修课 → 后修课」
prereq = [("数学", "概率"), ("数学", "算法"), ("编程", "数据结构"),
          ("数据结构", "算法"), ("算法", "机器学习"), ("概率", "机器学习")]
courses = {c for e in prereq for c in e}

def kahn(nodes, edges):                  # Kahn 算法：反复取出「入度为 0」的点（没有未修先修课的课）
    adj, indeg = defaultdict(list), {v: 0 for v in nodes}
    for u, v in edges:
        adj[u].append(v)
        indeg[v] += 1                    # 入度 = 还有几门先修课没修
    q = deque(sorted(v for v in nodes if indeg[v] == 0))
    order = []
    while q:
        u = q.popleft()
        order.append(u)
        for v in adj[u]:
            indeg[v] -= 1                # 修完 u，v 少了一门未修的先修课
            if indeg[v] == 0:
                q.append(v)
    return order                         # 如果长度 < 点数，说明剩下的点在环里

def topo_dfs(nodes, edges):              # DFS 版：后序（完成时间）的逆序就是拓扑序
    adj = defaultdict(list)
    for u, v in edges:
        adj[u].append(v)
    seen, post = set(), []
    def go(u):
        seen.add(u)
        for v in adj[u]:
            if v not in seen:
                go(v)
        post.append(u)                   # u 的所有后续课都处理完了，才记下 u
    for v in sorted(nodes):
        if v not in seen:
            go(v)
    return post[::-1]

print("Kahn：", kahn(courses, prereq))
print("DFS： ", topo_dfs(courses, prereq))

def valid_order(order, edges):           # 检查：每条边 u→v，u 都排在 v 前面
    pos = {v: i for i, v in enumerate(order)}
    return all(pos[u] < pos[v] for u, v in edges)
print("两个结果都合法：", valid_order(kahn(courses, prereq), prereq), valid_order(topo_dfs(courses, prereq), prereq))

# 加一条「机器学习 → 数学」：形成环，不可能排出合法顺序
cyc = prereq + [("机器学习", "数学")]
order = kahn(courses, cyc)
print("有环时只能排出", len(order), "门课（共", len(courses), "门）：存在环 =", len(order) < len(courses))
''')

C_VERIFY = code('''
import random
from collections import deque, defaultdict

def bfs_dist(adj, s):
    dist, q = {s: 0}, deque([s])
    while q:
        u = q.popleft()
        for v in adj[u]:
            if v not in dist:
                dist[v] = dist[u] + 1
                q.append(v)
    return dist

def floyd(n, edges):                     # 对照用：Floyd-Warshall 求所有点对的最短路径，O(n³)
    INF = float("inf")
    d = [[0 if i == j else INF for j in range(n)] for i in range(n)]
    for u, v in edges:
        d[u][v] = d[v][u] = 1
    for k in range(n):
        for i in range(n):
            for j in range(n):
                d[i][j] = min(d[i][j], d[i][k] + d[k][j])
    return d

def is_bipartite(adj, n):                # 二分图：能不能用两种颜色给点染色，使每条边两端颜色不同
    color = {}
    for s in range(n):
        if s in color:
            continue
        color[s] = 0
        q = deque([s])
        while q:
            u = q.popleft()
            for v in adj[u]:
                if v not in color:
                    color[v] = 1 - color[u]      # 邻居染成另一种颜色
                    q.append(v)
                elif color[v] == color[u]:       # 邻居颜色和自己一样：矛盾，不是二分图
                    return False
    return True

def make(n, edges):
    adj = defaultdict(list)
    for u, v in edges:
        adj[u].append(v)
        adj[v].append(u)
    return adj

random.seed(0)
ok = True
for _ in range(300):
    n = random.randint(2, 9)
    edges = list({tuple(sorted(random.sample(range(n), 2))) for _ in range(random.randint(0, 12))})
    adj, fw = make(n, edges), floyd(n, edges)
    for s in range(n):
        d = bfs_dist(adj, s)
        ok &= all(d.get(t, float("inf")) == fw[s][t] for t in range(n))
print("300 张随机图，BFS 的最短距离与 Floyd-Warshall 一致：", ok)

print("4 个点的环（偶环）：", is_bipartite(make(4, [(0, 1), (1, 2), (2, 3), (3, 0)]), 4))
print("3 个点的环（奇环）：", is_bipartite(make(3, [(0, 1), (1, 2), (2, 0)]), 3))
''')

unit = {
 "id": "u09",
 "title": "图：表示、BFS、DFS 与拓扑排序",
 "en": "Graphs: Representation, BFS, DFS & Topological Sort",
 "minutes": 90,
 "objectives": [
  "说出 **图 (graph)** 的基本术语（顶点、边、有向 / 无向、度、路径、环、连通、DAG），会画出一个问题的图模型",
  "会比较 **邻接矩阵 (adjacency matrix)** 与 **邻接表 (adjacency list)** 的空间与操作代价，知道稀疏图用邻接表",
  "会写 **BFS** 与 **DFS**（含迭代版），知道各自的复杂度 $O(V+E)$、用什么结构，以及 BFS 如何求**无权图的最短路径**",
  "会用遍历解决：**连通分量**、网格问题（岛屿数量、迷宫最短路）、**二分图判定**",
  "掌握 **拓扑排序 (topological sort)**（Kahn 算法与 DFS 版）和**环检测**",
 ],
 "blocks": [
  T(r"""
### 先说这一节要干什么

树是「没有环的、只有一个根」的特殊图。现实里更多的关系是**一般的图**：社交网络（谁关注谁）、地图（路口和道路）、网页之间的超链接、课程的先修关系、神经网络的**计算图**。这一节学图的表示方法和两个最基本的遍历算法，后面所有图算法（最短路径、最小生成树、网络流）都建立在它们上面。

**学完它你就能看懂这几件事：**

- **PyTorch 反向传播**：计算图是一个**有向无环图 (DAG)**，自动微分要沿着它的**拓扑序的逆序**传递梯度，就是这一节的拓扑排序；
- **图神经网络 (GNN)** 的输入是图，邻接矩阵 / 邻接表是它的数据格式；**知识图谱**、推荐系统里的用户-物品图；
- 搜索引擎怎样「爬网页」：BFS；
- 面试里最高频的「岛屿数量」「课程表」「单词接龙」「迷宫最短路」。

**本节安排（约 90 分钟）**：图的术语与表示（15 分钟）→ 视频一（11 分钟）→ BFS 与代码（15 分钟）→ 视频二（4 分钟）→ DFS 与代码（15 分钟）→ 网格与连通分量（10 分钟）→ 拓扑排序与视频三（20 分钟）→ 验证与二分图（10 分钟）→「想一想」。

### 图的基本概念

> **标准定义 · 图 (graph)**
>
> 一个**图** $G=(V,E)$ 由一个**顶点 (vertex / node)** 的集合 $V$ 和一个**边 (edge)** 的集合 $E$ 组成，每条边连接两个顶点。若边**有方向**（$u\to v$ 与 $v\to u$ 不同），称为**有向图 (directed graph)**；否则称为**无向图 (undirected graph)**。若边带有数值（距离、代价），称为**带权图 (weighted graph)**。顶点的**度 (degree)** 是与它相连的边数。**路径 (path)** 是顶点序列，相邻的两个顶点之间有边；起点和终点相同的路径称为**环 (cycle)**。若任意两个顶点之间都有路径，称图是**连通的 (connected)**；不连通的图可分成若干**连通分量 (connected components)**。没有环的有向图称为**有向无环图 (DAG)**。
>
> *English: A graph G = (V, E) is a set of vertices and edges; edges may be directed or undirected, and weighted or unweighted. A DAG is a directed acyclic graph.*

**白话版：「点」和「线」。** 把东西画成点，把关系画成线，就是图。**树是一种特殊的图：连通且没有环**，所以有 $n$ 个点的树恰有 $n-1$ 条边；一个有 $n$ 个点的连通图至少有 $n-1$ 条边。一般图的边数 $E$ 最多是 $O(V^2)$（任意两点之间都有边，叫**稠密图 dense**），而现实里的图大多是**稀疏图 (sparse)**，$E$ 只有 $O(V)$ 的量级：你的好友再多，也不会和地球上所有的人都有关系。

### 怎么存一个图

> **标准定义 · 邻接矩阵与邻接表**
>
> **邻接矩阵**：一个 $V\times V$ 的二维数组，`matrix[u][v]=1` 表示 $u$ 到 $v$ 有边（带权图里存权重）。空间 $O(V^2)$；判断两点之间是否有边 $O(1)$；遍历一个点的所有邻居 $O(V)$。
>
> **邻接表**：为每个顶点存一个**邻居列表**。空间 $O(V+E)$；判断两点是否相邻 $O(\deg)$；遍历一个点的所有邻居 $O(\deg)$。
>
> *English: An adjacency matrix is a V×V table using O(V²) space; an adjacency list stores each vertex's neighbours and uses O(V+E) space.*

**白话版：「班级座位表」对「通讯录」。** 邻接矩阵像一张所有人对所有人的「认识吗」表格，不管认不认识都占一个格子；邻接表像每个人手机里的通讯录，只记认识的人。

""" + C_REPR + r"""

稀疏图（社交网络这一类）用邻接矩阵，需要 $10^{10}$ 个格子（约 10 GB，放不下），而邻接表只存 60 万个条目。所以**几乎所有图算法默认用邻接表**；只有图很小或很稠密、需要频繁问「$u$、$v$ 有没有边」时，才用邻接矩阵。无向图要把每条边存两次（两个方向）。

| | 邻接矩阵 | 邻接表 |
|---|---|---|
| 空间 | $O(V^2)$ | $O(V+E)$ |
| 判断 $u$、$v$ 是否有边 | $O(1)$ | $O(\deg u)$ |
| 遍历 $u$ 的所有邻居 | $O(V)$ | $O(\deg u)$ |
| 遍历所有边 | $O(V^2)$ | $O(V+E)$ |
| 适合 | 稠密图、小图 | 稀疏图（绝大多数） |
"""),
  V("xlVX7dXLS64", "视频一：Breadth First Search (BFS): Visualized and Explained（Reducible）", 11),
  T(r"""
### 广度优先搜索 (BFS)

> **标准定义 · 广度优先搜索 (breadth-first search, BFS)**
>
> 从起点 $s$ 出发，**先访问距离 $s$ 为 1 的所有顶点，再访问距离为 2 的……**，一层一层向外扩展。实现上使用**队列 (queue)**，并用一个集合（或距离字典）记录已经**发现**的顶点，防止重复访问。时间 $O(V+E)$（每个顶点入队一次、每条边检查常数次），空间 $O(V)$。
>
> **性质：** 在**无权图**中，BFS 第一次到达某个顶点时经过的边数，就是起点到它的**最短距离**。
>
> *English: BFS explores the graph layer by layer using a queue; in an unweighted graph it finds shortest paths from the source.*

**白话版：往水里扔一块石头，水波一圈一圈扩散。** 第一圈是你的直接好友，第二圈是好友的好友（二度人脉）……每个人第一次被波浪碰到的那一圈，就是他和你之间的最短关系链。因为先入队的先处理，所以所有距离为 $d$ 的点，都会在距离为 $d+1$ 的点之前被处理。

""" + C_BFS + r"""

输出：访问顺序 `[0, 1, 2, 3, 6, 4, 5]` 是一层一层的：第 0 层 `0`，第 1 层 `1, 2`，第 2 层 `3, 6`，第 3 层 `4`，第 4 层 `5`。`dist` 字典同时起到「**已发现**」和「**距离**」的作用；`parent` 记下每个点是从谁那里被发现的，所以可以倒着走回起点，还原出最短路径 `[0, 1, 3, 4, 5]`。**注意是在「发现」时就标记已访问（入队时标记），而不是出队时标记**，否则同一个点可能被重复入队很多次。
"""),
  V("Urx87-NMm6c", "视频二：Depth-first search in 4 minutes（Michael Sambol）", 4),
  T(r"""
### 深度优先搜索 (DFS)

> **标准定义 · 深度优先搜索 (depth-first search, DFS)**
>
> 从起点出发，**沿着一条路径一直走到不能再走为止，再回溯到上一个有未访问邻居的顶点**，继续探索。实现上用**递归**（隐含地使用调用栈）或**显式的栈**，同样要记录已访问的顶点。时间 $O(V+E)$，空间 $O(V)$。
>
> *English: DFS follows one path as deep as possible, then backtracks; it can be implemented recursively or with an explicit stack.*

**白话版：走迷宫，一条路走到黑，碰壁再退回上一个岔路口。** 和 BFS 的「波浪」相反，DFS 像一个探险者，每到一个路口就选一条没走过的路一直走下去。

""" + C_DFS + r"""

迭代版和递归版访问顺序一样（注意迭代版要**反过来压栈**，因为栈是后进先出）。最后那条长度 5000 的链，递归版触发了 `RecursionError`，迭代版没有问题：**图很大或很深时，用显式栈**（还记得第 3 节的调用栈吗）。

| | BFS | DFS |
|---|---|---|
| 容器 | **队列** | **栈**（或递归） |
| 访问顺序 | 一层一层向外 | 一条路走到底再回溯 |
| 复杂度 | $O(V+E)$ | $O(V+E)$ |
| 能求最短路径（无权图） | **能** | 不能保证 |
| 典型用途 | 最短路径、层次关系 | 连通分量、环检测、拓扑排序、回溯 |
| 内存 | 可能同时存一整层（很宽的图较大） | 存当前路径（很深的图较大） |

**BFS 与 DFS 的关系：** 完全是同一个模板，只是把「队列」换成「栈」。回溯（第 5 节）本质上就是在**隐式的图**（所有选择构成的状态图）上做 DFS。

### 用遍历解决问题：连通分量、网格、迷宫

很多问题表面上没有「图」，但**只要定义清楚「什么是点、什么是边」**，就能用遍历。**例一：岛屿数量**，把网格里的每个陆地格子看成一个点，上下左右相邻的陆地之间有边；一个岛屿就是一个**连通分量**，数连通分量的个数：遍历所有格子，遇到一个没访问过的陆地，就用 DFS（或 BFS）把整座岛屿「淹掉」，计数加 1。**例二：迷宫最短步数**，每个空格是一个点，相邻的空格之间有一条权重为 1 的边，用 BFS 求最短路径。

""" + C_GRID + r"""

岛屿的例子里有 3 个连通的 `1` 块。迷宫里，从 S 走到 E 最少要走多少步，BFS 的第一次到达就给出了答案；如果 BFS 结束了都没到 E，就说明不可达，返回 `-1`。这类「把状态当成点，把一次操作当成边」的建模方式很强大：单词接龙、华容道、魔方的最少步数，都是 BFS。
"""),
  T(r"""
### 拓扑排序

> **标准定义 · 拓扑排序 (topological sort)**
>
> 对**有向无环图 (DAG)** 的所有顶点排成一个线性序列，使得对每一条边 $u\to v$，$u$ 都排在 $v$ 前面。**图有拓扑序，当且仅当它是 DAG（没有环）。** 一个 DAG 可以有多个合法的拓扑序。
>
> *English: A topological order lists the vertices of a DAG so that for every edge u → v, u appears before v. It exists if and only if the graph has no directed cycle.*

**白话版：做事情的先后顺序。** 学「机器学习」之前要先学「算法」和「概率」，学「算法」之前要先学「数据结构」和「数学」……有了这些**先修关系**（有向边），拓扑排序就是排出一个**合法的修课顺序**。如果出现循环依赖（A 要先于 B、B 要先于 A），就排不出来，这就是**环**。

两种做法：

**Kahn 算法（基于 BFS）：** 反复取出**入度为 0** 的顶点（即没有未完成的前置任务），输出它，并把它指向的顶点的入度各减 1；若某个顶点入度减到 0，就入队。若最终输出的顶点数**少于** $V$，说明剩下的顶点互相依赖，**存在环**。

**DFS 版：** 对每个顶点做 DFS，**当一个顶点的所有后续顶点都处理完（后序）时，把它记下来**，最后把记录的顺序**反转**，就是拓扑序。

""" + C_TOPO + r"""

两种方法给出了不同的顺序，**但都是合法的**（`valid_order` 验证了每条边都满足「先修课在前」）：拓扑序往往不唯一。最后，加了一条「机器学习 → 数学」后形成环，Kahn 算法只能取出一部分课程，**输出的顶点数少于 $V$，就说明有环**，这也是检测有向图是否有环的标准办法。两种算法的复杂度都是 $O(V+E)$。
"""),
  V("GYmq98CVm2c", "视频三：Topological sort in 5 minutes（Inside code）", 5),
  T(r"""
### 验证一下：BFS 的最短路径对不对

BFS 能求无权图的最短路径，这是一个很强的结论，应该用独立的算法验证：**Floyd-Warshall** 算法（$O(V^3)$，下一节会再见）可以求出所有点对之间的最短路径。在 300 张随机图上对比：

""" + C_VERIFY + r"""

BFS 和 Floyd-Warshall 在所有图、所有点对上完全一致（包括不连通的点，距离是无穷大）。最后顺便展示一个 BFS 的应用：**二分图判定**。**二分图 (bipartite graph)** 是可以把顶点分成两组、使每条边的两端分属不同组的图（比如「学生 - 课程」：边只出现在学生和课程之间）。用 BFS 给顶点**交替染色**：邻居必须染成另一种颜色，如果遇到一个已经染了**同样颜色**的邻居，就矛盾了。**图是二分图，当且仅当没有奇数长度的环**，所以偶环（4 个点）是，奇环（3 个点）不是。

### 这一节你要带走的三句话

1. **图 = 点 + 边**，用**邻接表**存（空间 $O(V+E)$）；稀疏图几乎都用邻接表。
2. **BFS 用队列、一层层扩展，能求无权图的最短路径；DFS 用栈（或递归）、一条路走到底**；两者都是 $O(V+E)$，大图的 DFS 要改成显式栈。
3. **只要定义清楚「点」和「边」，网格、状态、依赖关系都能变成图**：连通分量、迷宫最短路、拓扑排序（Kahn / DFS，检测环）都是遍历的应用。
"""),
  THINK("BFS 的实现里，为什么要在「把邻居放进队列的时候」就把它标记为已访问，而不是等「从队列里取出来的时候」再标记？", r"""
如果等到取出时才标记，那么在一个节点被取出之前，它可能被**多个**不同的邻居各发现一次，每次都把它放进队列，导致它在队列里**重复出现很多次**。极端情形下，队列里的元素个数可能达到 $O(E)$ 甚至更多，每个重复的元素还要再展开一遍邻居，复杂度可能退化为 $O(V^2)$ 或更差。

在**入队时**就标记，保证每个节点**只会入队一次**，所以总共 $O(V)$ 次出队，再加上每条边最多检查常数次，总复杂度才是 $O(V+E)$。同时，因为 BFS 是一层层扩展，第一次发现某个点时的层数就是它的最短距离，之后再遇到它的路径只会更长或一样，不会更短，所以第一次标记就是正确的。
"""),
  THINK("社交网络里要找「你和某个陌生人之间的最少几度关系」。可以用 BFS 从你出发搜索。但如果网络有 10 亿人，BFS 会非常慢。有什么办法加速？", r"""
一个经典办法是**双向 BFS (bidirectional BFS)**：同时从**你**和**对方**出发，各自 BFS，两边的波浪相遇就找到了最短路径。直觉上，单向 BFS 要探索到深度 $d$，每层大约扩展 $b$ 倍（$b$ 是平均好友数），要访问约 $b^d$ 个点；双向 BFS 每边只需要探索到深度 $d/2$，一共访问约 $2b^{d/2}$ 个点，**指数级的节省**。比如 $b=100,\ d=6$：单向约 $10^{12}$，双向约 $2\times10^6$。

这个思路也是很多搜索、路径规划算法（A\* 搜索、Dijkstra 的双向版本）的基础。另外，如果能提前预处理（比如给图建立某种索引），也能加速，但那就是更高级的话题了。
"""),
  THINK("拓扑排序和「先修课」的例子对应起来：你有一个任务依赖图，想知道**完成所有任务至少要多少轮**（每一轮里，没有依赖关系的任务可以同时进行）。这和拓扑排序有什么关系？", r"""
答案是 **DAG 里最长路径的长度**（按顶点数计）。这可以用 Kahn 算法**按层**取出：每一轮，取出当前所有入度为 0 的顶点（这些任务彼此没有未完成的依赖，可以并行），把它们作为一层，然后删除它们、更新入度。轮数就是层数。

这与 BFS 的「分层」是同一回事。换成课程：最少需要多少个学期才能修完（每学期可以修任意多门课，只要先修课已修完）？答案就是先修关系里最长的一条链的长度。**这个想法在 PyTorch 里对应：计算图里没有依赖关系的算子可以并行执行**，调度器就是按拓扑序、分层并行。
"""),
  KW(("图","graph","顶点和边组成的结构，$G=(V,E)$"),
     ("有向图 / 无向图","directed / undirected graph","边有方向 / 没有方向"),
     ("带权图","weighted graph","边带有数值（距离、代价）"),
     ("度","degree","与顶点相连的边数；有向图分入度和出度"),
     ("路径 / 环","path / cycle","顶点序列，相邻顶点有边 / 起点终点相同的路径"),
     ("连通分量","connected component","互相可达的最大顶点集合"),
     ("有向无环图","DAG (directed acyclic graph)","没有有向环的有向图，计算图和依赖关系都是 DAG"),
     ("稀疏图 / 稠密图","sparse / dense graph","$E=O(V)$ / $E$ 接近 $V^2$"),
     ("邻接表","adjacency list","每个顶点存邻居列表；空间 $O(V+E)$"),
     ("邻接矩阵","adjacency matrix","$V\\times V$ 的二维数组；空间 $O(V^2)$"),
     ("广度优先搜索","BFS (breadth-first search)","用队列一层层扩展；无权图的最短路径"),
     ("深度优先搜索","DFS (depth-first search)","用栈 / 递归一条路走到底再回溯"),
     ("拓扑排序","topological sort","DAG 顶点的线性排列，使每条边 $u\\to v$ 中 $u$ 在 $v$ 前"),
     ("Kahn 算法","Kahn's algorithm","反复取出入度为 0 的顶点；取不完则有环"),
     ("二分图","bipartite graph","顶点可分两组使每条边跨组；当且仅当没有奇环"),
  ),
 ],
 "references": [
  {"title": "Runestone：Graphs（章节目录）", "url": "https://runestone.academy/ns/books/published/pythonds/Graphs/index.html", "note": "本节的大纲依据，含图的表示、BFS、DFS、拓扑排序的 Python 实现与骑士巡游、单词接龙例子（CC BY-NC-SA 4.0）"},
  {"title": "BFS 与 DFS 的对比视频（Abdul Bari，约 18 分钟，选看）", "url": "https://www.youtube.com/watch?v=pcKY4hjDrxk", "note": "用图示一步步走一遍 BFS 与 DFS，对遍历顺序不确定时回看"},
  {"title": "MIT OCW 6.006 Introduction to Algorithms（课程主页）", "url": "https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-spring-2020/", "note": "大学课程原版，含 BFS / DFS 的正确性证明与拓扑排序"},
 ],
 "quiz": {"questions": [
  Q("对于边数远少于 $V^2$ 的稀疏图，最合适的存储方式是？",
    ["邻接矩阵，空间 $O(V^2)$", "哈希表", "邻接表，空间 $O(V+E)$", "三维数组"], 2,
    "邻接表只存实际存在的边，空间 $O(V+E)$；邻接矩阵无论有没有边都要占 $V^2$ 个格子。"),
  Q("用邻接表表示的图，BFS 的时间复杂度是？",
    ["$O(V+E)$", "$O(V\\cdot E)$", "一定是 $O(V^2)$", "$O(E\\log V)$"], 0,
    "每个顶点入队、出队一次，每条边在检查邻居时被看到常数次，所以是 $O(V+E)$。"),
  Q("在**无权图**里求一个起点到其他所有点的最短路径，最合适的算法是？",
    ["DFS", "必须用 Dijkstra", "Floyd-Warshall", "BFS：第一次到达某点时的层数就是最短距离"], 3,
    "BFS 一层层向外，先到达的一定经过的边最少。DFS 不保证最短；Dijkstra 是针对带权图的；Floyd 是求所有点对，更慢。"),
  Q("BFS 和 DFS 分别使用什么数据结构？",
    ["BFS 用栈，DFS 用队列", "BFS 用队列，DFS 用栈（或递归）", "都用队列", "都用堆"], 1,
    "BFS 先发现的先处理，是先进先出的队列；DFS 要沿最近发现的路径继续，是后进先出的栈（递归的调用栈）。"),
  Q("在一个很深（比如一条长链）的大图上，用递归写 DFS 可能出现什么问题？",
    ["结果不正确", "时间变成 $O(V^2)$", "递归过深，会触发 `RecursionError`；可以改写成显式栈的迭代版", "无法访问到所有节点"], 2,
    "Python 的递归深度有限（默认约 1000）。把递归改成显式栈，就没有深度限制了。"),
  Q("一个图存在拓扑排序，当且仅当它是？",
    ["有向无环图 (DAG)", "连通图", "树", "二分图"], 0,
    "有向环里的点互相依赖，没法排出先后顺序；没有环就一定能排出。"),
  Q("Kahn 算法的做法，以及如何判断有环？",
    ["每次删除度最大的顶点", "随机取一个顶点", "按顶点编号取", "反复取出入度为 0 的顶点并删除它的出边；若最终取出的顶点数少于 $V$，说明有环"], 3,
    "入度为 0 表示没有未完成的前置任务。有环时，环上的点入度永远不为 0，取不出来。"),
  Q("给一个由 `0` 和 `1` 组成的网格，数其中「岛屿」（上下左右相连的 `1`）的数量，本质上是？",
    ["二分查找", "求连通分量：对每个未访问的 `1` 做一次 BFS / DFS", "排序", "必须用动态规划"], 1,
    "把每个 `1` 看成一个点，相邻的 `1` 之间有边，一座岛屿就是一个连通分量。"),
  Q("无向图是**二分图**，当且仅当？",
    ["可以用两种颜色给顶点染色，使每条边的两端颜色不同（等价于没有奇数长度的环）", "图中没有环", "图是树", "边数是偶数"], 0,
    "二分图可以含有（偶数长度的）环，所以「没有环」不是必要条件；树是二分图，但二分图不一定是树。"),
  Q("一个有 $V$ 个顶点的**连通**无向图，至少有多少条边？",
    ["$V$", "$V+1$", "$V-1$", "$V/2$"], 2,
    "要把 $V$ 个点连通，至少要 $V-1$ 条边，此时恰好是一棵树；再多的边就会形成环。"),
 ]},
}

if __name__ == '__main__':
    dump(unit, "dsa-0", "u09-graphs-bfs-dfs.json")
