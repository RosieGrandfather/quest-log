"""dsa-0 第 10 节：加权图：最短路径、最小生成树与并查集"""
from unitlib import *
from d10c import C_DIJ, C_BF, C_DAGSP, C_UF, C_MST

unit = {
 "id": "u10",
 "title": "加权图：最短路径、最小生成树与并查集",
 "en": "Weighted Graphs: Shortest Paths, Minimum Spanning Trees & Union-Find",
 "minutes": 90,
 "objectives": [
  "会写 **Dijkstra 算法 (Dijkstra's algorithm)**，说清它为什么正确、为什么不能有负权边，复杂度 $O((V+E)\\log V)$",
  "会写 **Bellman-Ford 算法**，会用它检测**负环 (negative cycle)**，知道 **DAG 上的最短路径** 只要按拓扑序松弛一遍",
  "理解 **松弛 (relaxation)** 这个所有最短路径算法共用的操作，会按「有无负权、是不是 DAG」选对算法",
  "会写 **Kruskal** 与 **Prim** 求**最小生成树 (minimum spanning tree, MST)**，理解正确性的**切割性质 (cut property)**",
  "会实现 **并查集 (union-find / disjoint-set)**，理解**路径压缩 (path compression)** 与**按秩合并 (union by rank)**",
 ],
 "blocks": [
  T(r"""
### 先说这一节要干什么

上一节的 BFS 只能处理「每条边代价相同」的图。现实里的边几乎都带数值：路的长度、网络的延迟、转账的手续费、汇率。这一节处理**带权图 (weighted graph)** 上的两类问题：**从 A 到 B 最便宜怎么走（最短路径）**，以及**用最少的总代价把所有点连起来（最小生成树）**。顺带学一个小而强的数据结构：**并查集**。

**学完它你就能看懂这几件事：**

- 地图导航、网络路由（OSPF 协议就是 Dijkstra）；**强化学习**里的价值迭代、贝尔曼方程，其实是 Bellman-Ford 的思路：不断用邻居的值更新自己，直到不再变化；
- **聚类**里的**单链接层次聚类 (single-linkage clustering)** 等价于 Kruskal 算法；图像分割、网络设计里也常用最小生成树；
- 并查集：**连通分量**、Kruskal、图像分割里的区域合并，以及面试里大量「朋友圈」「账户合并」题；
- 机器学习里的 **Viterbi 算法**（语音识别、序列标注）本质上是 DAG 上的最短（最长）路径。

**本节安排（约 90 分钟）**：松弛与 Dijkstra（25 分钟，含视频一、二）→ Bellman-Ford 与 DAG（20 分钟，含视频三）→ 并查集（15 分钟，含视频四）→ 最小生成树（25 分钟，含视频五、六）→「想一想」。

### 最短路径与「松弛」

> **标准定义 · 单源最短路径 (single-source shortest path)**
>
> 在带权图 $G=(V,E)$ 中，一条路径的**长度**是它所含各边权重之和。**单源最短路径问题**：给定起点 $s$，求 $s$ 到每个顶点 $v$ 的最短路径长度 $\delta(s,v)$（不可达则为 $\infty$）。所有算法都维护一个估计值 $d[v]\ge\delta(s,v)$，并反复执行**松弛 (relaxation)**：若 $d[u]+w(u,v)<d[v]$，就令 $d[v]\leftarrow d[u]+w(u,v)$。
>
> *English: Single-source shortest path asks for the minimum total weight from a source to every vertex. Algorithms maintain distance estimates and repeatedly apply relaxation: if d[u] + w(u,v) < d[v], update d[v].*

**白话版：「有没有更近的路」。** 你现在认为到 $v$ 要 10，但听说到 $u$ 只要 3，而 $u$ 到 $v$ 的路是 4，那「先到 $u$ 再到 $v$」只要 7，比 10 近，就更新。**所有最短路径算法的区别，只在于「按什么顺序松弛」。** Dijkstra 的顺序是「每次处理当前最近的点」；Bellman-Ford 是「把所有边松弛 $V-1$ 遍」；DAG 上则是「按拓扑序」。

### Dijkstra 算法

> **标准定义 · Dijkstra 算法**
>
> **前提：所有边权 $\ge 0$。** 维护一个**优先队列（最小堆）**，里面是（当前距离估计，顶点）。每次取出估计值最小的顶点 $u$：此时 $d[u]$ 就已经是真正的最短距离（**确定 / 定稿**），然后对 $u$ 的每条出边松弛。使用二叉堆时，时间 $O((V+E)\log V)$。
>
> **正确性（为什么「当前最近」就是最终最近）：** 设 $u$ 是堆中估计值最小的点。任何一条通往 $u$ 的别的路径，必须先经过某个「还没定稿」的点，那个点的估计值 $\ge d[u]$，而之后的边权都 $\ge 0$，路径只会越走越长，不可能比 $d[u]$ 更短。**如果有负权边，这个论证就失效了。**
>
> *English: Dijkstra's algorithm repeatedly extracts the vertex with the smallest tentative distance from a min-heap and relaxes its outgoing edges. It requires non-negative edge weights; running time is O((V+E) log V) with a binary heap.*

**白话版：「从起点扩散的水波，但水波走得快慢不同」。** BFS 是每条路一样长的水波；Dijkstra 是路有长有短，每次让**最先到达的那个点**定稿。它很像 BFS，只是把队列换成了**最小堆**：这正是上一节学堆的目的。

""" + C_DIJ + r"""

两点值得注意：第一，堆里可能出现同一个顶点的多条旧记录（距离变小时我们只是再推入一条，不去修改旧记录），所以弹出时要跳过已经定稿的点，这叫**惰性删除 (lazy deletion)**，因为 Python 的 `heapq` 不支持修改已有元素。第二，最后一段展示了**有负权边时 Dijkstra 会出错**：`B` 先被弹出定稿，之后才发现 `C→B` 是一条负权边、能让 `B` 更近，但 `B` 的后继 `D` 已经用旧的距离算过了，不会再被更新。

**复杂度来自哪里：** 每个顶点定稿一次，每条边最多松弛一次并最多入堆一次，堆里最多 $E$ 个元素，每次堆操作 $O(\log E)=O(\log V)$，所以总共 $O((V+E)\log V)$。如果不用堆而是每次线性扫描找最小，就是 $O(V^2)$，对**稠密图**反而更好。
"""),
  V("_lHSawdgXpI", "视频一：Dijkstra's algorithm in 3 minutes（Michael Sambol）", 3),
  V("GazC3A4OQTE", "视频二：Dijkstra's Algorithm（Computerphile，约 11 分钟，讲思路与例子）", 11),
  T(r"""
### Bellman-Ford 算法：允许负权边

> **标准定义 · Bellman-Ford 算法**
>
> 把**所有边**松弛 $V-1$ 遍。**为什么 $V-1$ 遍够用：** 一条不含环的最短路径最多包含 $V-1$ 条边；第 $k$ 遍结束后，所有「最多含 $k$ 条边」的最短路径都已经被正确求出。若第 $V$ 遍还能松弛成功，说明存在从起点可达的**负环 (negative cycle)**（环上权重之和为负，可以无限绕圈让距离越来越小，最短路径没有意义）。时间 $O(VE)$，**允许负权边**。
>
> *English: Bellman-Ford relaxes every edge V-1 times; it handles negative weights, and a further successful relaxation on the V-th pass reveals a negative cycle. Time O(VE).*

**白话版：「把所有的路都反复核对，直到没有更近的为止」。** 它不聪明，但很稳。**慢（$O(VE)$ 对 $O((V+E)\log V)$），但能处理负权**。

""" + C_BF + r"""

负环的一个现实例子是**货币套利**：`USD→EUR→GBP→USD` 汇率乘积若大于 1，绕一圈就赚钱。把每个汇率取 $-\log$，乘积大于 1 就变成了「和小于 0」，套利就是**负环检测**。负环时算出的距离没有意义（程序里 `[0, 1, -1, 3]` 只是中途停下来的值），所以一般的用法是先判断有没有负环，有就报错。

### DAG 上的最短路径：按拓扑序松弛一遍

如果图是 **DAG**（上一节的拓扑排序），就不需要堆，也不怕负权边：**按拓扑序处理每个点，松弛它的出边，一遍即可**，$O(V+E)$。理由：拓扑序保证处理 $u$ 时，所有能到达 $u$ 的点都已经处理完，$d[u]$ 已经最终确定。

""" + C_DAGSP + r"""

把权重取负再求最短路，就是**最长路**。这在 DAG 上是成立的（一般图里最长路是 NP 难问题）。项目管理里的**关键路径 (critical path)**，即完成整个项目至少要多久，就是任务依赖图（DAG）上的最长路径。**这也是下一节动态规划的预告：DP 的「状态转移」，本质上就是在一个隐含的 DAG 上按拓扑序求最优路径。**

**怎么选算法（背这张表就够了）：**

| 情形 | 算法 | 时间 |
|---|---|---|
| 边权相同（无权图） | BFS | $O(V+E)$ |
| 边权 $\ge0$ | Dijkstra | $O((V+E)\log V)$ |
| 有负权边 | Bellman-Ford | $O(VE)$ |
| DAG（允许负权） | 拓扑序松弛 | $O(V+E)$ |
| 所有点对 | Floyd-Warshall | $O(V^3)$ |
"""),
  V("obWXjtg0L64", "视频三：Bellman-Ford in 5 minutes — Step by step example（Michael Sambol）", 5),
  T(r"""
### 并查集 (union-find)

> **标准定义 · 并查集 (disjoint-set / union-find)**
>
> 维护一组**互不相交的集合**，支持两个操作：**`find(x)`** 返回 $x$ 所在集合的**代表元（根）**；**`union(a, b)`** 合并 $a$、$b$ 所在的两个集合。每个集合用一棵树表示，每个元素存它的父节点，根的父节点是自己。两个优化：**路径压缩 (path compression)**：`find` 时把沿途的节点直接挂到根上；**按秩合并 (union by rank)**：合并时把较矮的树挂到较高的树下面。两个优化合用，每次操作的均摊时间是 $O(\alpha(n))$，其中 $\alpha$ 是**反阿克曼函数 (inverse Ackermann function)**，增长极慢，对任何实际的 $n$ 都不超过 4，可以当作常数。
>
> *English: A disjoint-set (union-find) structure maintains a partition of elements into sets with find and union. With path compression and union by rank, each operation takes amortized O(α(n)) time.*

**白话版：「朋友圈合并」。** 开始每个人自成一个圈；`union(a, b)` 表示「a 和 b 成了朋友，两个圈合并」；`find(x)` 问「x 的圈长是谁」，**两个人圈长相同，就在同一个圈里**。它只回答「是不是同一组」，不回答「具体有谁」，所以比用 BFS 重新数连通分量快得多，尤其是**边是一条一条动态加进来**的时候。

""" + C_UF + r"""

`union` 返回 `False` 表示这两个点**早就在同一个集合里**，这条边连起来就会形成**环**：下面的 Kruskal 就是用这个性质来判环的。最后的对比里，朴素版在一条长链上，每次 `find` 都要走很长的路，$n$ 次操作变成 $O(n^2)$；优化版把树压得很扁，接近 $O(n)$，差了上千倍（具体倍数因机器不同）。还要注意：「均摊」是上一节学的概念，这里的单次 `find` 偶尔会很慢，但**一连串操作的平均**很快。
"""),
  V("ibjEGG7ylHk", "视频四：Union Find Introduction（WilliamFiset）", 6),
  T(r"""
### 最小生成树 (MST)

> **标准定义 · 生成树与最小生成树**
>
> 连通无向图 $G=(V,E)$ 的**生成树 (spanning tree)** 是包含**所有顶点**、恰好有 $V-1$ 条边的**树**（连通且无环）。边带权时，总权重最小的生成树称为**最小生成树 (minimum spanning tree, MST)**。
>
> **切割性质 (cut property)：** 把顶点分成任意两组 $S$ 与 $V\setminus S$，在所有**横跨两组的边**中，**权重最小的那条一定属于某棵最小生成树**（边权互不相同时是唯一的 MST）。Kruskal 与 Prim 的正确性都由此而来。
>
> *English: A spanning tree connects all vertices with V-1 edges and no cycles; a minimum spanning tree has minimum total weight. By the cut property, the lightest edge crossing any cut belongs to some MST.*

**白话版：「用最便宜的方式把所有城市连起来」。** 铺光缆、修路、通水管：只要所有城市互相连通，不需要多余的线，多一条线就会形成环、浪费钱。**注意：MST 是总费用最小，不是每对点之间的距离最短**：最短路径树和最小生成树是两回事。

**切割性质为什么对：** 假设某棵 MST 不包含这条最轻的横跨边 $e$。把 $e$ 加进去就会形成一个环，环必然还会再穿过一次这个切割，那里有另一条横跨边 $f$，$w(f)\ge w(e)$。把 $f$ 换成 $e$，总权重不增加，仍是生成树。所以总存在包含 $e$ 的 MST。

**两种做法，对应两种「贪心」：**

- **Kruskal**：**把所有边按权重从小到大排序**，依次考虑，**不会形成环就加入**（用并查集判断环）。从「边」的角度生长，中间状态是一片森林。时间 $O(E\log E)$，排序是瓶颈。
- **Prim**：**从一个点开始，每次加入连接「已选集合」和「未选集合」的最小边**。从「点」的角度生长，中间状态始终是一棵树，实现几乎就是 Dijkstra，只是堆里放的是「边的权重」而不是「到起点的距离」。时间 $O((V+E)\log V)$。

""" + C_MST + r"""

Kruskal 的 `sorted(edges)` 加上并查集的 `union`，就是它的全部；Prim 是把 Dijkstra 的 `nd = d + w` 换成 `w`。两者结果相同（总费用 30），**与暴力枚举所有生成树取最小值完全一致**。MST 的总权重是唯一的，但边权有相同值时，具体的树可以不唯一。选哪个：稀疏图 Kruskal 好写；稠密图 Prim（配合邻接矩阵 $O(V^2)$）更快。

**一个机器学习里的联系：单链接聚类。** 对 $n$ 个数据点，两两距离作为边权，按距离从小到大合并最近的两个簇，这个过程就是 Kruskal；用到 $k$ 个簇时停下，等价于**去掉 MST 里最长的 $k-1$ 条边**。

### 这一节你要带走的三句话

1. **最短路径的核心是「松弛」**：边权非负用 **Dijkstra**（最小堆，$O((V+E)\log V)$）；有负权用 **Bellman-Ford**（$O(VE)$，还能查负环）；DAG 按拓扑序一遍即可（$O(V+E)$）。
2. **最小生成树是「总费用最小地连通所有点」**：Kruskal 排序边 + 并查集判环，Prim 像 Dijkstra 一样从一个点长出来；正确性来自**切割性质**。
3. **并查集**用「树 + 路径压缩 + 按秩合并」，让「合并 / 是不是同一组」几乎是常数时间，是判环、数连通分量和 Kruskal 的基础。
"""),
  V("71UQH7Pr9kU", "视频五：Kruskal's algorithm in 2 minutes（Michael Sambol）", 2),
  V("cplfcGZmX7I", "视频六：Prim's algorithm in 2 minutes（Michael Sambol）", 2),
  THINK("Dijkstra 为什么不能处理负权边？能不能给所有边加上一个很大的常数，让它们全变成正的，再用 Dijkstra？", r"""
**不能。** 给每条边加上同一个常数 $c$ 之后，一条含 $k$ 条边的路径总长度会增加 $kc$，**边数多的路径被惩罚得更多**，最短路径的**排序会改变**。例如两条路径：一条只有 1 条边、权重 $-1$，另一条有 3 条边、权重各为 $-1$（总共 $-3$，更短）。每条边加 $c=2$ 之后，前者变成 $+1$，后者变成 $+3$：原来最短的路径反而变成最长。

所以「整体平移」不是等价变换。真正能处理负权的做法是 **Johnson 算法**：先用 Bellman-Ford 求出一个「势能 (potential)」$h(v)$，把边权重新定义为 $w'(u,v)=w(u,v)+h(u)-h(v)\ge0$。对任何一条从 $s$ 到 $t$ 的路径，势能项会相互抵消，只剩 $h(s)-h(t)$，**所有路径都平移同一个量，排序保持不变**，这样才能放心用 Dijkstra。这是所有点对最短路径在稀疏图上比 Floyd-Warshall 更快的办法。
"""),
  THINK("Kruskal 的并查集是用来干什么的？如果不用并查集，每次想知道「加入这条边会不会形成环」，朴素的办法要多少时间？", r"""
并查集用来回答「**这条边的两个端点是不是已经连通**」：连通就加入会成环，应当跳过；不连通就可以加入，并合并两个集合。

朴素做法：每次加边前，在目前已选的森林里做一次 BFS / DFS，看两个端点是否已连通，一次 $O(V)$。$E$ 条边就是 $O(VE)$。而并查集每次操作接近 $O(1)$（$O(\alpha(n))$），总时间只剩下**排序的 $O(E\log E)$** 一项，这才让 Kruskal 变得实用。这是「选对数据结构，算法本身不用变」的典型例子。
"""),
  THINK("一个城市有一些道路，要找一个办法让所有路口连通，总修建成本最小（MST）；另一个问题是从家到公司的最短路径。这两个问题的答案「树」会是同一棵吗？举一个反例。", r"""
**不一定。** 取三个点 $A,B,C$，边：$AB=2,\ BC=2,\ AC=3$。MST 是 $\{AB, BC\}$，总权重 4。但以 $A$ 为起点的**最短路径树**：到 $B$ 的最短是 2（经 $AB$），到 $C$ 的最短是 3（直接 $AC$，因为经 $B$ 要 4）。最短路径树是 $\{AB, AC\}$，总权重 5，比 MST 更重。

两个问题的目标不同：MST 要求**所有边加起来最小**，最短路径树要求**每个点到起点的距离最小**。这也是为什么「铺光缆」用 MST，「导航」用 Dijkstra。
"""),
  KW(("带权图","weighted graph","每条边带有数值（距离、代价）的图"),
     ("单源最短路径","single-source shortest path","从一个起点到所有顶点的最小总权重"),
     ("松弛","relaxation","若 $d[u]+w<d[v]$，则更新 $d[v]$；所有最短路径算法的基本操作"),
     ("Dijkstra 算法","Dijkstra's algorithm","用最小堆每次定稿距离最小的点；要求边权非负，$O((V+E)\\log V)$"),
     ("惰性删除","lazy deletion","堆里不修改旧元素，弹出时跳过过期的记录"),
     ("Bellman-Ford 算法","Bellman-Ford algorithm","把所有边松弛 $V-1$ 遍；允许负权，$O(VE)$"),
     ("负环","negative cycle","权重之和为负的环；存在时最短路径无意义"),
     ("关键路径","critical path","任务依赖 DAG 上的最长路径，决定项目最短工期"),
     ("生成树","spanning tree","连接所有顶点、恰有 $V-1$ 条边的树"),
     ("最小生成树","minimum spanning tree (MST)","总权重最小的生成树"),
     ("切割性质","cut property","横跨任一切割的最小边必属于某棵 MST"),
     ("Kruskal 算法","Kruskal's algorithm","按权重排序边，不成环就加入"),
     ("Prim 算法","Prim's algorithm","从一个点出发，每次加入连接已选与未选集合的最小边"),
     ("并查集","union-find / disjoint-set","维护不相交集合的 find / union，近似常数时间"),
     ("路径压缩 / 按秩合并","path compression / union by rank","并查集的两个优化，合用后均摊 $O(\\alpha(n))$"),
  ),
 ],
 "references": [
  {"title": "Runestone：Graphs（章节目录，含 Dijkstra 与 Prim）", "url": "https://runestone.academy/ns/books/published/pythonds/Graphs/index.html", "note": "本节大纲依据，含 Dijkstra 与 Prim 的 Python 实现（CC BY-NC-SA 4.0）"},
  {"title": "MIT OCW 6.006 Introduction to Algorithms（课程主页）", "url": "https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-spring-2020/", "note": "大学课程原版，含 Dijkstra、Bellman-Ford 的正确性证明与松弛的统一框架"},
  {"title": "VisuAlgo：Single-Source Shortest Paths / Minimum Spanning Tree（交互动画）", "url": "https://visualgo.net/en/sssp", "note": "新加坡国立大学的算法可视化网站，可以自己画图、单步执行 Dijkstra、Bellman-Ford、Kruskal、Prim"},
 ],
 "quiz": {"questions": [
  Q("下面哪种情形下 **Dijkstra 算法可能给出错误答案**？",
    ["图是稠密图", "图里有一些权重为 0 的边", "图里有**负权边**", "图是无向图"], 2,
    "Dijkstra 的正确性依赖「路径只会越走越长」，即边权非负。有负权边时，已定稿的点可能被后来发现的负边改善。0 权边没问题。"),
  Q("用二叉堆实现的 Dijkstra，时间复杂度是？",
    ["$O(V+E)$", "$O((V+E)\\log V)$", "$O(V^3)$", "$O(VE)$"], 1,
    "每条边最多入堆一次、每次堆操作 $O(\\log V)$；$V^3$ 是 Floyd-Warshall，$VE$ 是 Bellman-Ford。"),
  Q("**松弛 (relaxation)** 指的是？",
    ["把图里的环去掉", "如果经过 $u$ 到 $v$ 更近（$d[u]+w<d[v]$），就更新 $d[v]$", "把边按权重排序", "合并两个集合"], 1,
    "松弛是所有最短路径算法共用的基本操作；它们的区别只在于松弛的顺序。"),
  Q("Bellman-Ford 把所有边松弛 $V-1$ 遍，原因是？",
    ["为了让时间复杂度变成 $O(V^2)$", "图里最多有 $V-1$ 个环", "不含环的最短路径最多有 $V-1$ 条边，每遍至少多确定一条边", "堆的大小最多是 $V-1$"], 2,
    "第 $k$ 遍后，所有最多含 $k$ 条边的最短路径都已正确。最短路径（无环）最多含 $V-1$ 条边，所以 $V-1$ 遍足够。"),
  Q("如何用 Bellman-Ford 检测**负环**？",
    ["看最终距离是否为负数", "再多做第 $V$ 遍，若还能松弛成功，则存在从起点可达的负环", "统计边数", "看是否有负权边"], 1,
    "没有负环时，$V-1$ 遍后所有距离已稳定；还能更新说明路径可以靠绕负环无限变短。有负权边不一定有负环。"),
  Q("在**有向无环图（DAG）**上求单源最短路径（允许负权），最合适的做法是？",
    ["Dijkstra", "Bellman-Ford，因为它是唯一能处理负权的", "按拓扑序依次松弛每个顶点的出边，$O(V+E)$", "Floyd-Warshall"], 2,
    "拓扑序保证处理 $u$ 时所有指向 $u$ 的边都已松弛过，不需要堆，也不怕负权。"),
  Q("一个有 $V$ 个顶点的连通图，它的**生成树**有多少条边？",
    ["$V$", "$V+1$", "$V-1$", "取决于权重"], 2,
    "树有 $V$ 个点就恰有 $V-1$ 条边；少了不连通，多了有环。"),
  Q("**Kruskal 算法**的步骤是？",
    ["从一个点开始，每次加入连到已选集合的最小边", "把所有边按权重从小到大排序，依次加入不会形成环的边", "对每个点做一次 BFS", "反复删除权重最大的点"], 1,
    "「从一个点开始扩张」描述的是 Prim。Kruskal 用并查集判断加入某条边是否会成环。"),
  Q("**切割性质 (cut property)** 说的是？",
    ["任何一棵树都是最小生成树", "把顶点分成两组，横跨两组的边中权重最小的那条一定属于某棵 MST", "每个环里权重最大的边不属于任何 MST", "MST 里所有边的权重都相等"], 1,
    "这是 Kruskal 与 Prim 贪心正确的依据。「每个环里最重的边不属于任何 MST」是与之对偶的**环性质**，不是切割性质（且边权相同时也不严格成立）。"),
  Q("并查集用了**路径压缩**和**按秩合并**之后，每次操作的均摊时间是？",
    ["$O(n)$", "$O(\\log n)$", "$O(n\\log n)$", "$O(\\alpha(n))$，反阿克曼函数，实际可当作常数"], 3,
    "单用其中一个优化是 $O(\\log n)$ 量级，两个合用可达 $O(\\alpha(n))$，$\\alpha(n)$ 在所有实际的 $n$ 下不超过 4。"),
 ]},
}

TARGET = [2, 0, 3, 1, 2, 0, 3, 1, 0, 2]
for q, t in zip(unit["quiz"]["questions"], TARGET):
    q["options"][q["answer"]], q["options"][t] = q["options"][t], q["options"][q["answer"]]
    q["answer"] = t

if __name__ == '__main__':
    dump(unit, "dsa-0", "u10-shortest-paths-mst.json")
