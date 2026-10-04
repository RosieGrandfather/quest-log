from runlib import code

C_DIJ = code('''
import heapq, random

def dijkstra(adj, s):
    """adj[u] = [(v, w), ...]，要求所有 w >= 0。返回 (dist, parent)"""
    dist, parent = {s: 0}, {s: None}
    pq = [(0, s)]                          # 堆里放 (当前已知距离, 顶点)
    done = set()
    while pq:
        d, u = heapq.heappop(pq)
        if u in done:                      # 过期的旧记录：跳过（惰性删除）
            continue
        done.add(u)                        # 弹出的这一刻，u 的最短距离才确定
        for v, w in adj[u]:
            nd = d + w
            if v not in dist or nd < dist[v]:
                dist[v], parent[v] = nd, u
                heapq.heappush(pq, (nd, v))
    return dist, parent

def path_to(parent, t):
    p = []
    while t is not None:
        p.append(t); t = parent[t]
    return p[::-1]

# 一张小地图：A..F，边上是距离
edges = [("A","B",7), ("A","C",9), ("A","F",14), ("B","C",10), ("B","D",15),
         ("C","D",11), ("C","F",2), ("D","E",6), ("E","F",9)]
adj = {x: [] for x in "ABCDEF"}
for u, v, w in edges:
    adj[u].append((v, w)); adj[v].append((u, w))

dist, parent = dijkstra(adj, "A")
print("距离：", dict(sorted(dist.items())))
print("A 到 E 的路径：", path_to(parent, "E"), " 总长", dist["E"])

# 验证：和 Floyd-Warshall 在 300 张随机带权图上比较
def floyd(n, edge_list):
    INF = float("inf")
    d = [[0 if i == j else INF for j in range(n)] for i in range(n)]
    for u, v, w in edge_list:
        d[u][v] = min(d[u][v], w); d[v][u] = min(d[v][u], w)
    for k in range(n):
        for i in range(n):
            for j in range(n):
                if d[i][k] + d[k][j] < d[i][j]:
                    d[i][j] = d[i][k] + d[k][j]
    return d

random.seed(0)
ok = True
for _ in range(300):
    n = random.randint(2, 9)
    el = [(random.randrange(n), random.randrange(n), random.randint(1, 20))
          for _ in range(random.randint(0, 2 * n))]
    a = {i: [] for i in range(n)}
    for u, v, w in el:
        a[u].append((v, w)); a[v].append((u, w))
    F = floyd(n, el)
    dist, _ = dijkstra(a, 0)
    for v in range(n):
        if F[0][v] != dist.get(v, float("inf")):
            ok = False
print("Dijkstra 与 Floyd-Warshall 在 300 张随机图上一致：", ok)

# 负权边：Dijkstra 会出错。D 的真实最短路是 S→C→B→D = 4 - 3 + 1 = 2
g = {"S": [("A", 2), ("B", 3), ("C", 4)], "A": [], "B": [("D", 1)], "C": [("B", -3)], "D": []}
dist, _ = dijkstra(g, "S")
print("有负权边时 Dijkstra 给出 dist[D] =", dist["D"], "，但真正最短是", 4 + (-3) + 1)
''')

C_BF = code('''
def bellman_ford(n, edges, s):
    """edges = [(u, v, w)]，有向边，w 可以为负。返回 (dist, 是否有从 s 可达的负环)"""
    INF = float("inf")
    dist = [INF] * n
    dist[s] = 0
    for i in range(n - 1):                 # 最多 n-1 轮：最短路径最多 n-1 条边
        changed = False
        for u, v, w in edges:
            if dist[u] + w < dist[v]:
                dist[v] = dist[u] + w
                changed = True
        if not changed:                    # 提前结束
            break
    # 第 n 轮还能更新，说明有负环
    neg = any(dist[u] + w < dist[v] for u, v, w in edges)
    return dist, neg

# 有负权边但没有负环
edges = [(0, 1, 4), (0, 2, 5), (1, 2, -3), (2, 3, 4), (1, 3, 6)]
print("无负环：", bellman_ford(4, edges, 0))

# 加一条 3→1 权重 -2 的边，形成负环 1→2→3→1（总权重 -3+4-2 = -1）
edges2 = edges + [(3, 1, -2)]
print("有负环：", bellman_ford(4, edges2, 0))

# 汇率套利就是负环：把汇率取对数再取负，一个环上乘积 >1 就是和 <0
import math
rates = {("USD","EUR"): 0.9, ("EUR","GBP"): 0.9, ("GBP","USD"): 1.30}
names = ["USD", "EUR", "GBP"]
idx = {x: i for i, x in enumerate(names)}
es = [(idx[a], idx[b], -math.log(r)) for (a, b), r in rates.items()]
print("汇率环乘积 =", round(0.9 * 0.9 * 1.30, 3), "，存在套利（负环）：", bellman_ford(3, es, 0)[1])

# 验证：非负权图上 Bellman-Ford 应与 Dijkstra 一致
import heapq, random
def dijkstra(n, edges, s):
    adj = [[] for _ in range(n)]
    for u, v, w in edges: adj[u].append((v, w))
    dist = [float("inf")] * n; dist[s] = 0
    pq = [(0, s)]
    while pq:
        d, u = heapq.heappop(pq)
        if d > dist[u]: continue
        for v, w in adj[u]:
            if d + w < dist[v]:
                dist[v] = d + w; heapq.heappush(pq, (dist[v], v))
    return dist

random.seed(1)
ok = True
for _ in range(300):
    n = random.randint(2, 9)
    es = [(random.randrange(n), random.randrange(n), random.randint(0, 20)) for _ in range(random.randint(0, 3 * n))]
    d1, neg = bellman_ford(n, es, 0)
    ok &= (d1 == dijkstra(n, es, 0)) and not neg
print("非负权图上 Bellman-Ford 与 Dijkstra 一致：", ok)
''')

C_DAGSP = code('''
# DAG 上的最短（最长）路径：按拓扑序松弛一遍，O(V+E)，负权也没问题
from collections import deque

def dag_shortest(n, edges, s):
    adj = [[] for _ in range(n)]; indeg = [0] * n
    for u, v, w in edges:
        adj[u].append((v, w)); indeg[v] += 1
    q = deque(i for i in range(n) if indeg[i] == 0)
    order = []
    while q:
        u = q.popleft(); order.append(u)
        for v, _ in adj[u]:
            indeg[v] -= 1
            if indeg[v] == 0: q.append(v)
    dist = [float("inf")] * n; dist[s] = 0
    for u in order:
        if dist[u] == float("inf"): continue
        for v, w in adj[u]:
            dist[v] = min(dist[v], dist[u] + w)
    return dist

edges = [(0, 1, 5), (0, 2, 3), (1, 3, 6), (1, 2, 2), (2, 4, 4), (2, 5, 2), (2, 3, 7), (3, 5, 1), (3, 4, -1), (4, 5, -2)]
print("含负权的 DAG 最短路径：", dag_shortest(6, edges, 1))
# 项目排期：把权重取负做最短路 = 最长路（关键路径）
neg = [(u, v, -w) for u, v, w in [(0,1,3),(0,2,2),(1,3,4),(2,3,1),(3,4,2)]]
print("关键路径长度（任务 0→...→4）：", -dag_shortest(5, neg, 0)[4])
''')

C_UF = code('''
class UnionFind:
    def __init__(self, n):
        self.parent = list(range(n))       # 每个人一开始自成一组，组长是自己
        self.rank = [0] * n
        self.count = n                     # 当前有几组
    def find(self, x):
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]   # 路径压缩（减半）
            x = self.parent[x]
        return x
    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return False                   # 已经在同一组：这条边会形成环
        if self.rank[ra] < self.rank[rb]:
            ra, rb = rb, ra
        self.parent[rb] = ra               # 矮的树挂到高的树下面（按秩合并）
        if self.rank[ra] == self.rank[rb]:
            self.rank[ra] += 1
        self.count -= 1
        return True

uf = UnionFind(6)
for a, b in [(0, 1), (2, 3), (1, 3), (4, 5), (0, 2)]:
    print(f"union({a},{b}) ->", uf.union(a, b), "  组数 =", uf.count)
print("0 和 3 同组：", uf.find(0) == uf.find(3), "；0 和 4 同组：", uf.find(0) == uf.find(4))

# 速度对比：朴素版（不压缩、不按秩）在「一条链」的最坏输入上 vs 优化版
import time, sys
class Naive:
    def __init__(self, n): self.p = list(range(n))
    def find(self, x):
        while self.p[x] != x: x = self.p[x]
        return x
    def union(self, a, b):
        self.p[self.find(a)] = self.find(b)

n = 20000
t = time.perf_counter(); nv = Naive(n)
for i in range(n - 1): nv.union(i, i + 1)        # 每次把旧根挂到新点下面，形成长链
for i in range(n): nv.find(0)                    # 然后反复从链的最深处查找
t_naive = time.perf_counter() - t
t = time.perf_counter(); u2 = UnionFind(n)
for i in range(n - 1): u2.union(i, i + 1)
for i in range(n): u2.find(0)
t_fast = time.perf_counter() - t
print(f"朴素版比优化版慢约 {t_naive / t_fast:.0f} 倍（量级对即可，具体数字因机器而异）")

# 验证：并查集的组数与 BFS 数连通分量一致
import random
from collections import deque
random.seed(2)
ok = True
for _ in range(300):
    n = random.randint(1, 15)
    es = [(random.randrange(n), random.randrange(n)) for _ in range(random.randint(0, n))]
    u3 = UnionFind(n)
    adj = [[] for _ in range(n)]
    for a, b in es:
        u3.union(a, b); adj[a].append(b); adj[b].append(a)
    seen, comp = set(), 0
    for s in range(n):
        if s in seen: continue
        comp += 1; seen.add(s); q = deque([s])
        while q:
            x = q.popleft()
            for y in adj[x]:
                if y not in seen: seen.add(y); q.append(y)
    ok &= (comp == u3.count)
print("并查集组数 = BFS 连通分量数（300 张随机图）：", ok)
''')

C_MST = code('''
import heapq, random, itertools

class UF:
    def __init__(self, n): self.p = list(range(n))
    def find(self, x):
        while self.p[x] != x:
            self.p[x] = self.p[self.p[x]]; x = self.p[x]
        return x
    def union(self, a, b):
        a, b = self.find(a), self.find(b)
        if a == b: return False
        self.p[a] = b; return True

def kruskal(n, edges):
    """edges = [(w, u, v)]。按权重从小到大，不成环就加入"""
    uf, total, chosen = UF(n), 0, []
    for w, u, v in sorted(edges):
        if uf.union(u, v):
            total += w; chosen.append((u, v, w))
    return total, chosen

def prim(n, edges, s=0):
    adj = [[] for _ in range(n)]
    for w, u, v in edges:
        adj[u].append((w, v)); adj[v].append((w, u))
    seen, total, pq, cnt = set(), 0, [(0, s)], 0
    while pq and len(seen) < n:
        w, u = heapq.heappop(pq)
        if u in seen: continue
        seen.add(u); total += w
        for w2, v in adj[u]:
            if v not in seen: heapq.heappush(pq, (w2, v))
    return total

# 一个小例子：6 个城市之间铺光缆，边上是费用
edges = [(7,0,1),(5,1,2),(8,0,2),(9,1,3),(7,2,3),(5,3,4),(15,2,4),(6,3,5),(8,4,5),(11,4,0)]
total, chosen = kruskal(6, edges)
print("Kruskal 总费用：", total, " 选中的边：", chosen)
print("Prim    总费用：", prim(6, edges))

# 验证：小图上暴力枚举所有「V-1 条边且连通」的子集，取最小
def brute(n, edges):
    best = None
    for sub in itertools.combinations(edges, n - 1):
        uf = UF(n)
        if all(uf.union(u, v) for w, u, v in sub):     # n-1 条边且无环 => 生成树
            s = sum(w for w, u, v in sub)
            best = s if best is None else min(best, s)
    return best

random.seed(3)
ok, tested = True, 0
for _ in range(300):
    n = random.randint(2, 6)
    es = [(random.randint(1, 9), a, b) for a in range(n) for b in range(a + 1, n) if random.random() < 0.7]
    b = brute(n, es)
    if b is None:                                       # 图不连通，没有生成树
        continue
    tested += 1
    ok &= (kruskal(n, es)[0] == b == prim(n, es))
print(f"Kruskal = Prim = 暴力枚举（{tested} 张连通随机图）：", ok)
''')
