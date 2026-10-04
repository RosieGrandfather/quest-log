"""dsa-0 第 8 节：堆与优先队列"""
from unitlib import *
from runlib import code

C_HEAP = code('''
import random

class MinHeap:
    # 最小堆，用列表存放：下标 i 的节点，父亲在 (i-1)//2，孩子在 2i+1 和 2i+2
    def __init__(self):
        self.a = []
        self.swaps = 0

    def push(self, x):
        a = self.a
        a.append(x)                      # 先放在最后一个位置，保持「完全二叉树」的形状
        i = len(a) - 1
        while i > 0:                     # 上浮 (sift up)：比父亲小就和父亲交换
            p = (i - 1) // 2
            if a[p] <= a[i]:
                break
            a[p], a[i] = a[i], a[p]
            self.swaps += 1
            i = p

    def pop(self):
        a = self.a
        top = a[0]                       # 最小的永远在堆顶
        last = a.pop()                   # 把最后一个元素拿出来……
        if a:
            a[0] = last                  # ……放到堆顶，然后下沉
            i, n = 0, len(a)
            while True:                  # 下沉 (sift down)：和较小的孩子交换，直到比孩子都小
                l, r, m = 2 * i + 1, 2 * i + 2, i
                if l < n and a[l] < a[m]:
                    m = l
                if r < n and a[r] < a[m]:
                    m = r
                if m == i:
                    break
                a[i], a[m] = a[m], a[i]
                self.swaps += 1
                i = m
        return top

h = MinHeap()
for x in (5, 3, 8, 1, 9, 2):
    h.push(x)
    print("push", x, "→", h.a)
print("依次弹出：", [h.pop() for _ in range(6)])

random.seed(0)
xs = [random.randint(0, 1000) for _ in range(5000)]
h = MinHeap()
for x in xs:
    h.push(x)
print("5000 个随机数，按弹出顺序排成的序列等于 sorted：", [h.pop() for _ in range(len(xs))] == sorted(xs))
''')

C_HEAPIFY = code('''
from math import log2

def heapify(a):                          # 把任意列表原地变成最小堆：从最后一个非叶子节点开始，依次下沉
    swaps, n = 0, len(a)
    for start in range(n // 2 - 1, -1, -1):
        i = start
        while True:
            l, r, m = 2 * i + 1, 2 * i + 2, i
            if l < n and a[l] < a[m]:
                m = l
            if r < n and a[r] < a[m]:
                m = r
            if m == i:
                break
            a[i], a[m] = a[m], a[i]
            swaps += 1
            i = m
    return swaps

def push_all(xs):                        # 一个一个 push 进去
    a, swaps = [], 0
    for x in xs:
        a.append(x)
        i = len(a) - 1
        while i > 0:
            p = (i - 1) // 2
            if a[p] <= a[i]:
                break
            a[p], a[i] = a[i], a[p]
            swaps += 1
            i = p
    return swaps

print("      n   heapify 交换次数   逐个 push 的交换次数   n·log2(n)")
for n in (1000, 10_000, 100_000):
    worst = list(range(n, 0, -1))        # 递减序列：每个新元素都比之前所有的小，要一路上浮到堆顶
    print(f"{n:>7} {heapify(worst[:]):>14} {push_all(worst):>20} {n * log2(n):>14.0f}")
''')

C_HEAPQ = code('''
import heapq, random

nums = [5, 1, 9, 3, 7, 2, 8]
h = list(nums)
heapq.heapify(h)                         # 原地建堆 O(n)
print(h[0], heapq.heappop(h), heapq.heappop(h))     # h[0] 永远是最小的；heappop 弹出最小的

mh = [-x for x in nums]                  # heapq 只有最小堆；要最大堆，就存负数
heapq.heapify(mh)
print("最大的是", -heapq.heappop(mh))

tasks = []                               # 带优先级的任务：元组先比较第一个元素，数字小的优先
heapq.heappush(tasks, (2, "write report"))
heapq.heappush(tasks, (1, "reply email"))
heapq.heappush(tasks, (3, "meeting"))
while tasks:
    p, name = heapq.heappop(tasks)
    print(p, name)

print(heapq.nlargest(3, nums), heapq.nsmallest(3, nums))

def top_k_stream(stream, k):             # 数据流里找最大的 k 个：只保留一个大小为 k 的最小堆
    h = []
    for x in stream:
        if len(h) < k:
            heapq.heappush(h, x)
        elif x > h[0]:                   # 比堆顶（当前第 k 大）还大，才有资格进来
            heapq.heapreplace(h, x)      # 弹出堆顶并放入新的，O(log k)
    return sorted(h, reverse=True)

random.seed(0)
data = [random.randint(0, 10**6) for _ in range(100_000)]
print("10 万个数里的前 5 大：", top_k_stream(data, 5), top_k_stream(data, 5) == sorted(data, reverse=True)[:5])
''')

C_MERGEK = code('''
import heapq, random

def merge_k(lists):
    # 合并 k 个已排序的列表：堆里始终只放「每个列表当前最小的那一个」，共 k 个
    h = [(l[0], i, 0) for i, l in enumerate(lists) if l]     # (值, 属于第几个列表, 在列表中的位置)
    heapq.heapify(h)
    out = []
    while h:
        v, i, j = heapq.heappop(h)       # 目前所有列表里最小的
        out.append(v)
        if j + 1 < len(lists[i]):         # 从它所在的列表里补充下一个
            heapq.heappush(h, (lists[i][j + 1], i, j + 1))
    return out

random.seed(0)
ok = True
for _ in range(500):
    lists = [sorted(random.randint(0, 50) for _ in range(random.randint(0, 6))) for _ in range(random.randint(1, 6))]
    ok &= merge_k(lists) == sorted(x for l in lists for x in l)
print("500 组随机数据，与「全部放一起再排序」一致：", ok)
print(merge_k([[1, 4, 7], [2, 5, 8], [3, 6, 9]]))
''')

C_MEDIAN = code('''
import heapq, random, statistics

class RunningMedian:
    # 数据流的中位数：用两个堆各存一半。lo 是最大堆（存负数，较小的一半），hi 是最小堆（较大的一半）
    def __init__(self):
        self.lo, self.hi = [], []

    def add(self, x):
        heapq.heappush(self.lo, -x)
        heapq.heappush(self.hi, -heapq.heappop(self.lo))     # 先过一遍 lo，保证 lo 的所有元素 ≤ hi 的所有元素
        if len(self.hi) > len(self.lo):                      # 保持 lo 的元素个数不少于 hi
            heapq.heappush(self.lo, -heapq.heappop(self.hi))

    def median(self):
        if len(self.lo) > len(self.hi):
            return -self.lo[0]                               # 总数是奇数：中位数是 lo 的堆顶
        return (-self.lo[0] + self.hi[0]) / 2                # 总数是偶数：取两个堆顶的平均

rm = RunningMedian()
for x in (5, 15, 1, 3):
    rm.add(x)
    print("加入", x, "→ 中位数", rm.median())

random.seed(0)
ok = True
for _ in range(500):
    xs = [random.randint(0, 20) for _ in range(random.randint(1, 15))]
    rm, seen = RunningMedian(), []
    for x in xs:
        rm.add(x)
        seen.append(x)
        ok &= rm.median() == statistics.median(seen)
print("500 组随机数据，每一步的中位数与重新排序计算的一致：", ok)
''')

C_HSORT = code('''
import random

def heapsort(a):                         # 原地堆排序：不需要额外数组
    n = len(a)
    def sift_down(i, n):                 # 这里用最大堆：父亲不小于孩子
        while True:
            l, r, m = 2 * i + 1, 2 * i + 2, i
            if l < n and a[l] > a[m]:
                m = l
            if r < n and a[r] > a[m]:
                m = r
            if m == i:
                return
            a[i], a[m] = a[m], a[i]
            i = m
    for i in range(n // 2 - 1, -1, -1):  # 第一步：建最大堆，O(n)
        sift_down(i, n)
    for end in range(n - 1, 0, -1):      # 第二步：反复把堆顶（最大的）换到末尾，堆缩小一格后重新调整
        a[0], a[end] = a[end], a[0]
        sift_down(0, end)
    return a

random.seed(0)
tests = ([random.randint(0, 20) for _ in range(random.randint(0, 20))] for _ in range(2000))
print("2000 组随机数据，堆排序与 sorted 一致：", all(heapsort(x[:]) == sorted(x) for x in tests))
''')

unit = {
 "id": "u08",
 "title": "堆与优先队列",
 "en": "Heaps & Priority Queues",
 "minutes": 70,
 "objectives": [
  "说出 **优先队列 (priority queue)** 与 **堆 (heap)** 的定义，理解堆为什么能用数组存储（下标公式）",
  "会写堆的 **上浮 (sift up)** 与 **下沉 (sift down)**，知道 push / pop 是 $O(\\log n)$，peek 是 $O(1)$",
  "理解 **建堆 (heapify)** 为什么是 $O(n)$ 而不是 $O(n\\log n)$，会写 **堆排序 (heapsort)**",
  "熟练使用 Python 的 `heapq`（只有最小堆，最大堆存负数；元组做优先级）",
  "会用堆解决 **Top-$k$**、**合并 $k$ 个有序列表**、**数据流中位数**，为 Dijkstra（第 10 节）做铺垫",
 ],
 "blocks": [
  T(r"""
### 先说这一节要干什么

很多场景里，你不需要把所有数据排好序，只要**反复快速地拿到「最重要的那一个」**：急诊室先看最危重的病人，操作系统先跑优先级最高的任务，导航算法先扩展「离起点最近的」路口。这个需求叫**优先队列**，它的标准实现就是**堆**：取最大（或最小）$O(1)$，插入和删除 $O(\log n)$，而且只用一个数组就够了。

**学完它你就能看懂这几件事：**

- **Dijkstra 最短路径、A\* 搜索**（第 10 节）靠优先队列来决定「下一个展开谁」；
- **束搜索 (beam search)**（语言模型解码）每一步保留得分最高的 $k$ 个候选，本质是 Top-$k$；
- 推荐系统、检索系统的「Top-$k$ 召回」，数据流里的「最近邻」；
- 面试高频：Top-$k$、合并 $k$ 个有序链表、数据流中位数。

**本节安排（约 70 分钟）**：优先队列与堆的定义（12 分钟）→ 视频一、二（16 分钟）→ 实现上浮与下沉（15 分钟）→ 建堆与堆排序（12 分钟）→ `heapq` 与应用（15 分钟）→「想一想」。

### 优先队列与堆

> **标准定义 · 优先队列 (priority queue) 与 二叉堆 (binary heap)**
>
> **优先队列**是一种 ADT：每个元素带有**优先级**，支持 `push`（插入）和 `pop`（取出并删除**优先级最高**的元素），以及 `peek`（只看不取）。**二叉堆**是它最常见的实现：一棵**完全二叉树 (complete binary tree)**（除最后一层外每层都是满的，最后一层从左到右排列），并且满足**堆序性**：
>
> - **最小堆 (min-heap)**：每个节点的值**不大于**它的孩子，所以堆顶是最小的；
> - **最大堆 (max-heap)**：每个节点的值**不小于**它的孩子，所以堆顶是最大的。
>
> *English: A priority queue supports insertion and removal of the highest-priority element. A binary heap implements it as a complete binary tree in which every node is no larger (min-heap) or no smaller (max-heap) than its children.*

**白话版：公司的「职级树」，上级一定比下属职位高。** 堆只保证「父亲比孩子更优先」，**兄弟之间没有顺序**，也不要求整棵树有序，这比 BST 的要求宽松得多，所以更新起来也更省力：它只需要保证最大（小）的在最上面。

**为什么可以用数组存？** 因为堆是**完全二叉树**：节点按层从上到下、从左到右依次排列，**中间没有空洞**。所以用下标就能直接算出亲戚关系（下标从 0 开始）：

$$\text{parent}(i)=\left\lfloor\frac{i-1}{2}\right\rfloor,\qquad \text{left}(i)=2i+1,\qquad \text{right}(i)=2i+2$$

不需要任何指针，既省内存又缓存友好。堆顶就是数组的第 0 个元素。
"""),
  V("0wPlzMU-k00", "视频一：Heaps in 3 minutes — Intro（Michael Sambol）", 3),
  V("XycnarZEBvQ", "视频二：Heaps Visually Explained (Priority Queues)（ByteQuest）", 12),
  T(r"""
### 上浮与下沉

堆只有两个核心操作，都是沿着一条「根到叶」的路径走，所以都是 $O(\log n)$（完全二叉树的高度是 $\lfloor\log_2n\rfloor$）：

> **标准定义 · 上浮 (sift up) 与 下沉 (sift down)**
>
> **插入 `push`：** 把新元素放在数组**末尾**（保持完全二叉树的形状），然后**上浮**：只要它比父亲**更优先**，就和父亲交换，直到不再比父亲优先，或者到达根。
>
> **取出 `pop`：** 取走堆顶，把数组**最后一个元素**移到堆顶，然后**下沉**：和较优先的那个孩子比较，若孩子更优先就交换，直到它比两个孩子都优先，或者成为叶子。
>
> *English: Insert by appending and sifting up; extract by moving the last element to the root and sifting down. Each takes O(log n).*

**白话版：新人从底层往上晋升，直到遇到比他强的上级；老总走了，让最底层的人暂代，再一层层往下「降级」到合适的位置。**

""" + C_HEAP + r"""

看 push 的过程：加入 1 时，堆是 `[3, 5, 8]`，它先放在末尾（下标 3），它的父亲是下标 1 的 5，1 比 5 小，交换；再和根 3 比较，又比 3 小，再交换，一路上浮到堆顶，得到 `[1, 3, 8, 5]`。**数组 `[1, 3, 2, 5, 9, 8]` 并不是排好序的**（5 在 2 的后面），只满足「父亲不大于孩子」，这就是堆和排序的区别。不断弹出堆顶，得到的恰好是升序序列。

| 操作 | 复杂度 |
|---|---|
| `peek`（看堆顶） | $O(1)$ |
| `push`（上浮） | $O(\log n)$ |
| `pop`（下沉） | $O(\log n)$ |
| 建堆 `heapify` | $O(n)$ |
| 查找任意元素 | $O(n)$（堆没有顺序可利用） |

### 建堆：为什么是 $O(n)$

要把一个无序的列表变成堆，最直接的是一个一个 `push`，每次 $O(\log n)$，总共 $O(n\log n)$。但有一个更快的办法：**从最后一个非叶子节点开始，倒着依次对每个节点做下沉**。

> **标准定义 · 建堆 (heapify) 的复杂度**
>
> 对 $n$ 个元素自底向上建堆，总的交换次数是 $O(n)$。原因：高度为 $k$ 的节点最多有 $\lceil n/2^{k+1}\rceil$ 个，每个至多下沉 $k$ 层，所以总代价
>
> $$\sum_{k=0}^{\lfloor\log_2n\rfloor}\frac{n}{2^{k+1}}\cdot k=n\sum_{k\ge0}\frac{k}{2^{k+1}}\le n\cdot1=O(n)$$
>
> *English: Bottom-up heap construction costs O(n), because most nodes are near the leaves and sift down only a few levels.*

**白话版：「大多数人在底层，他们几乎不用动」。** 一半的节点是叶子，根本不用处理；四分之一的节点离叶子只有一层，最多下沉一次；只有极少数靠近根的节点需要下沉很多层。加权求和是一个收敛的级数，所以总量只是 $O(n)$。用代码对比：

""" + C_HEAPIFY + r"""

$n$ 翻倍，`heapify` 的交换次数也大约翻倍（线性），始终不到 $n$；而在最坏的输入（递减序列）下，逐个 `push` 的交换次数接近 $n\log_2n-n$ 的量级，$n=100000$ 时是 `heapify` 的十几倍。（注意：对**随机**输入，逐个 `push` 平均也很快，因为新元素通常只上浮一两层；但最坏情况 `heapify` 仍有保证。）

### 堆排序

有了「建堆 $O(n)$」和「弹出堆顶 $O(\log n)$」，排序就水到渠成：先建一个**最大堆**，然后反复**把堆顶（最大的）和末尾交换**，堆的大小缩小一格，再对堆顶下沉。每一步都把当前最大的放到它最终的位置。

""" + C_HSORT + r"""

堆排序：$O(n\log n)$ 最坏时间保证、**原地**（$O(1)$ 额外空间），但**不稳定**，而且对缓存不友好，所以实际中通常比快排慢；它的价值在于「最坏情况有保证、省空间」，上一节表格里已经列出。
"""),
  T(r"""
### Python 的 `heapq` 与常见应用

Python 标准库的 `heapq` 模块直接在**普通列表**上实现了**最小堆**：`heappush`、`heappop`、`heapify`、`heapreplace`、`nlargest`、`nsmallest`。要注意两点：它**只有最小堆**，要最大堆就把元素**取负数**；要带优先级，就放进**元组**，元组按位置依次比较，**第一个元素就是优先级**。

""" + C_HEAPQ + r"""

最后两行是堆最常见的用法：**数据流里的 Top-$k$**。技巧是**保持一个大小为 $k$ 的最小堆**，堆顶是「目前第 $k$ 大」；新来的数只要比堆顶大，就把堆顶换掉。每个元素最多做一次 $O(\log k)$ 的操作，总共 $O(n\log k)$，比全部排序的 $O(n\log n)$ 好，而且**空间只要 $O(k)$**，不需要把数据全存下来，对海量数据流很重要。

**应用二：合并 $k$ 个有序列表。** 堆里始终只放「每个列表当前最小的那一个」（共 $k$ 个），弹出最小的，再把它所在列表的下一个放进去。总共 $N$ 个元素，每个元素进出堆一次，$O(N\log k)$。这是**外部排序**（数据大到内存放不下，分块排好再合并）的核心。

""" + C_MERGEK + r"""

**应用三：数据流的中位数。** 数据不断到来，随时要报告中位数。办法是用**两个堆**把数据分成「较小的一半」和「较大的一半」：较小的一半用**最大堆**（堆顶是它们的最大值），较大的一半用**最小堆**（堆顶是它们的最小值）。两个堆的堆顶就是正中间的两个数。每次加入一个数 $O(\log n)$，取中位数 $O(1)$。

""" + C_MEDIAN + r"""

### 这一节你要带走的三句话

1. **堆 = 完全二叉树 + 堆序性**，用数组存（父 $\lfloor(i-1)/2\rfloor$、左 $2i+1$、右 $2i+2$）；`peek` $O(1)$，`push` / `pop` $O(\log n)$，建堆 $O(n)$。
2. **`heapq` 只有最小堆**：最大堆存负数，优先级放元组的第一个位置；它在 Top-$k$、合并有序列表、数据流中位数里都是首选工具。
3. **只需要「最重要的几个」时用堆，不要排序**：Top-$k$ 是 $O(n\log k)$，比排序的 $O(n\log n)$ 好，空间也更省。
"""),
  THINK("为什么 `pop` 时把「最后一个元素」放到堆顶再下沉，而不是直接把堆顶的某个孩子提上来填补空位？", r"""
关键是要**保持完全二叉树的形状**。数组的形状由「长度」决定：删除一个元素后，数组必须少一个，而最自然的就是去掉**最后一个位置**。所以我们把最后一个元素拿出来填补堆顶的空缺，形状立刻保持正确，只是堆序性可能被破坏（这个元素可能比孩子大），再下沉修复。

如果提拔一个孩子填补空位，会在那个孩子原来的位置留下新的空缺，一路向下传递，最后在某个叶子留下一个空洞，而这个空洞可能在最后一层的中间，破坏「完全二叉树」的结构，不能再用简单的下标公式表示。
"""),
  THINK("找一个有 $n=10^7$ 个数的数组里最大的 100 个数。「排序后取前 100」和「用大小为 100 的最小堆」，分别需要多少步和多少额外空间？", r"""
**排序**：$O(n\log n)\approx10^7\times23\approx2.3\times10^8$ 步；如果原数组不能被修改，还要复制一份，额外空间 $O(n)$。

**堆**：$O(n\log k)=10^7\times\log_2100\approx10^7\times7\approx7\times10^7$ 步，额外空间只有 $O(k)=O(100)$。而且大多数元素比堆顶小，一次比较就跳过，实际更快。更关键的是：堆的做法**不需要把全部数据读进内存**，一边读一边处理，数据流都能用。（如果 $k$ 接近 $n$，两者差别就小了；还有一种平均 $O(n)$ 的 **快速选择 (quickselect)**，也可以做「第 $k$ 大」。）
"""),
  THINK("数据流中位数的做法里，要求「`lo` 的所有元素都不大于 `hi` 的所有元素」，并且两个堆的大小至多相差 1。这两个条件为什么足以保证中位数就在两个堆顶？", r"""
两个条件合起来说明：**把所有元素排好序，前一半恰好在 `lo`，后一半恰好在 `hi`**（第一个条件保证了「前一半都不大于后一半」，第二个条件保证了「一半一半」）。

于是：若总数是奇数，多出来的那一个放在 `lo`，它是 `lo` 里最大的，也就是排序后正中间的那个，即 `lo` 的堆顶；若总数是偶数，正中间有两个数，一个是 `lo` 里最大的、一个是 `hi` 里最小的，也就是两个堆顶，取平均就是中位数。每次加入新元素后，上面代码里「先过一遍 `lo` 再转给 `hi`、必要时再挪回来」的两步，正是在维护这两个性质。
"""),
  KW(("优先队列","priority queue","每次取出优先级最高的元素的 ADT"),
     ("二叉堆","binary heap","完全二叉树 + 堆序性，优先队列的标准实现"),
     ("完全二叉树","complete binary tree","除最后一层外都是满的，最后一层靠左排列；可以无空洞地存在数组里"),
     ("最小堆 / 最大堆","min-heap / max-heap","父亲不大于 / 不小于孩子；堆顶是最小 / 最大"),
     ("堆序性","heap property","父节点比子节点更优先；兄弟之间没有顺序"),
     ("上浮","sift up","新元素在末尾，比父亲优先就交换，直到不再优先"),
     ("下沉","sift down","堆顶被替换后，和更优先的孩子交换，直到比孩子都优先"),
     ("建堆","heapify","把任意数组原地变成堆，$O(n)$"),
     ("堆排序","heapsort","建最大堆后反复把堆顶换到末尾；$O(n\\log n)$、原地、不稳定"),
     ("Top-$k$","top-k","用大小为 $k$ 的最小堆，$O(n\\log k)$，空间 $O(k)$"),
     ("`heapq`","heapq","Python 标准库的最小堆，作用在普通列表上"),
     ("外部排序","external sorting","数据放不下内存时，分块排序再用堆合并"),
  ),
 ],
 "references": [
  {"title": "Runestone：Priority Queues with Binary Heaps", "url": "https://runestone.academy/ns/books/published/pythonds/Trees/PriorityQueuesWithBinaryHeaps.html", "note": "本节的大纲依据，含二叉堆的结构、上浮下沉、建堆的 Python 实现（CC BY-NC-SA 4.0）"},
  {"title": "Python 文档：heapq — Heap queue algorithm", "url": "https://docs.python.org/3/library/heapq.html", "note": "含优先队列的实现要点、任务优先级的例子，以及 `heapq.merge`"},
  {"title": "MIT OCW 6.006 Introduction to Algorithms（课程主页）", "url": "https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-spring-2020/", "note": "大学课程原版，含堆与堆排序的严格分析"},
 ],
 "quiz": {"questions": [
  Q("最小堆满足的性质是？",
    ["每个节点的左孩子小于右孩子", "整棵树的中序遍历是升序", "每一层都是降序排列", "每个节点的值不大于它的孩子，所以堆顶是最小的"], 3,
    "堆序性只约束「父亲 vs 孩子」，兄弟之间、不同子树之间都没有顺序。BST 的中序升序是另一种结构。"),
  Q("用数组（下标从 0 开始）存二叉堆，下标为 $i$ 的节点，它的父节点的下标是？",
    ["$\\lfloor(i-1)/2\\rfloor$", "$\\lfloor i/2\\rfloor$", "$2i$", "$i-1$"], 0,
    "孩子是 $2i+1$ 和 $2i+2$，所以父亲是 $\\lfloor(i-1)/2\\rfloor$。（若下标从 1 开始，则父亲是 $\\lfloor i/2\\rfloor$。）"),
  Q("二叉堆的 `push` 和 `pop` 的时间复杂度分别是？",
    ["$O(1)$ 和 $O(1)$", "$O(n)$ 和 $O(n)$", "都是 $O(\\log n)$", "$O(n\\log n)$ 和 $O(n\\log n)$"], 2,
    "完全二叉树的高度是 $\\log n$，上浮和下沉最多走一条根到叶的路径。"),
  Q("把一个无序的列表原地变成堆（`heapify`），时间复杂度是？",
    ["$O(n\\log n)$", "$O(n)$", "$O(\\log n)$", "$O(n^2)$"], 1,
    "自底向上建堆，大多数节点在底层、几乎不用下沉，加权求和是 $O(n)$，比逐个 `push` 的 $O(n\\log n)$ 最坏情况要好。"),
  Q("Python 标准库 `heapq` 实现的是？",
    ["最大堆", "二叉搜索树", "双端队列", "最小堆（要最大堆需把元素取负数）"], 3,
    "`heapq` 只有最小堆，作用在普通列表上。要最大堆，存入时取负、取出时再取负。"),
  Q("在 $n$ 个数的数据流中找最大的 $k$ 个数，用大小为 $k$ 的最小堆，时间复杂度是？",
    ["$O(n\\log k)$", "$O(n\\log n)$", "$O(nk)$", "$O(k\\log n)$"], 0,
    "每个元素最多做一次 $O(\\log k)$ 的堆操作；而且额外空间只要 $O(k)$。"),
  Q("合并 $k$ 个已排序的列表（共 $N$ 个元素），用堆的做法时间复杂度是？",
    ["$O(Nk)$", "$O(N\\log N)$", "$O(N\\log k)$", "$O(N)$"], 2,
    "堆里始终只有 $k$ 个元素，每个元素进出堆各一次，每次 $O(\\log k)$，共 $O(N\\log k)$。"),
  Q("关于堆排序，下面说法正确的是？",
    ["稳定，需要 $O(n)$ 额外空间", "原地（$O(1)$ 额外空间），最坏 $O(n\\log n)$，但不稳定", "稳定且原地", "最坏情况是 $O(n^2)$"], 1,
    "堆排序在原数组上建堆并交换，不需要额外数组，最坏也是 $O(n\\log n)$；但交换会打乱相等元素的相对次序，所以不稳定。"),
  Q("要在数据流里随时报告中位数，应该怎样用堆？",
    ["用一个最大堆存较小的一半、一个最小堆存较大的一半，两个堆顶就是中间的数", "用一个最小堆", "每次都排序后取中间", "用哈希表"], 0,
    "两个堆各存一半，堆大小至多差 1，且前一半都不大于后一半，所以中位数由两个堆顶决定；每次加入 $O(\\log n)$，取中位数 $O(1)$。"),
  Q("为什么二叉堆可以用普通数组存储，不需要指针？",
    ["因为堆是满二叉树", "因为堆是二叉搜索树", "因为堆是完全二叉树，节点按层连续排列没有空洞，父子关系可以用下标公式算出来", "因为数组一定比指针快"], 2,
    "完全二叉树按层从左到右排列，没有空位，所以第 $i$ 个节点的亲戚位置只与 $i$ 有关。这也是堆缓存友好的原因。"),
 ]},
}

if __name__ == '__main__':
    dump(unit, "dsa-0", "u08-heaps.json")
