"""dsa-0 第 6 节：排序与二分查找"""
from unitlib import *
from runlib import code

C_SORTS = code('''
import random

def insertion_sort(a):                   # 插入排序：把每个元素插到前面已排好的部分里
    a, cmp = a[:], 0
    for i in range(1, len(a)):
        x, j = a[i], i - 1
        while j >= 0:
            cmp += 1
            if a[j] > x:
                a[j + 1] = a[j]          # 比 x 大的往后挪一格
                j -= 1
            else:
                break
        a[j + 1] = x
    return a, cmp

def merge_sort(a):                       # 归并排序：分成两半，各自排序，再合并
    cmp = 0
    def sort(a):
        nonlocal cmp
        if len(a) <= 1:
            return a
        mid = len(a) // 2
        L, R = sort(a[:mid]), sort(a[mid:])
        out, i, j = [], 0, 0
        while i < len(L) and j < len(R):
            cmp += 1
            if L[i] <= R[j]:             # 相等时取左边的：这一点保证了「稳定」
                out.append(L[i]); i += 1
            else:
                out.append(R[j]); j += 1
        return out + L[i:] + R[j:]
    return sort(a), cmp

def quick_sort(a, pivot="random"):       # 快速排序：选基准，小的放左边，大的放右边，分别排序
    cmp = 0
    def sort(a):
        nonlocal cmp
        if len(a) <= 1:
            return a
        p = random.choice(a) if pivot == "random" else a[0]
        less = [x for x in a if x < p]
        equal = [x for x in a if x == p]
        more = [x for x in a if x > p]
        cmp += len(a)                    # 每个元素和基准比较一次（简化计数）
        return sort(less) + equal + sort(more)
    return sort(a), cmp

random.seed(0)
print("随机输入的比较次数：")
print("   n   插入排序     归并排序   快速排序(随机基准)")
for n in (100, 1000, 4000):
    a = [random.random() for _ in range(n)]
    print(f"{n:>5} {insertion_sort(a)[1]:>10} {merge_sort(a)[1]:>12} {quick_sort(a)[1]:>12}")

n = 500
a = list(range(n))                       # 已经排好序的输入
print("已经排好序的输入（n=500）：")
print("  插入排序", insertion_sort(a)[1], "  归并排序", merge_sort(a)[1],
      "  快排(固定取第一个当基准)", quick_sort(a, "first")[1], "  快排(随机基准)", quick_sort(a)[1])
''')

C_STABLE = code('''
students = [("Ming", 90), ("Hong", 85), ("Gang", 90), ("Li", 85), ("Hua", 90)]

# 按分数从高到低排。稳定排序：同分的人保持原来的先后顺序（Ming → Gang → Hua；Hong → Li）
print(sorted(students, key=lambda s: s[1], reverse=True))

# 利用稳定性做「多关键字排序」：先按次要关键字（名字）排，再按主要关键字（分数）排
step1 = sorted(students, key=lambda s: s[0])
step2 = sorted(step1, key=lambda s: s[1], reverse=True)
print(step2)
print(step2 == sorted(students, key=lambda s: (-s[1], s[0])))   # 一次排序，用元组当键，结果相同
''')

C_COUNT = code('''
import random
from math import factorial, log2, ceil

def counting_sort(a, k):                 # 计数排序：元素都是 0..k-1 的整数，不做任何比较
    count = [0] * k
    for x in a:
        count[x] += 1                    # 数每个值出现了几次
    out = []
    for v in range(k):
        out += [v] * count[v]            # 按值从小到大，依次输出
    return out

random.seed(0)
a = [random.randrange(10) for _ in range(20)]
print(a)
print(counting_sort(a, 10), counting_sort(a, 10) == sorted(a))

# 基于比较的排序，最坏情况至少要比较 ⌈log2(n!)⌉ 次（n! 种顺序，每次比较至多排除一半）
for n in (4, 10, 20, 100):
    print(f"n={n:<4} 至少要比较 {ceil(log2(factorial(n)))} 次   n·log2(n) = {n * log2(n):.0f}")
''')

C_BS = code('''
from bisect import bisect_left, bisect_right
import random

def lower_bound(a, x):                   # 第一个 >= x 的位置；所有元素都比 x 小则返回 len(a)
    lo, hi = 0, len(a)                   # 搜索区间 [lo, hi)，答案一定在区间里（含 hi）
    while lo < hi:
        mid = (lo + hi) // 2
        if a[mid] < x:
            lo = mid + 1                 # a[mid] 太小了，答案在 mid 右边
        else:
            hi = mid                     # a[mid] 够大了，答案是 mid 或者更靠左
    return lo

def upper_bound(a, x):                   # 第一个 > x 的位置
    lo, hi = 0, len(a)
    while lo < hi:
        mid = (lo + hi) // 2
        if a[mid] <= x:
            lo = mid + 1
        else:
            hi = mid
    return lo

a = [1, 2, 2, 2, 5, 8, 8, 10]
print(lower_bound(a, 2), upper_bound(a, 2), lower_bound(a, 3), lower_bound(a, 11))
print("x=2 出现", upper_bound(a, 2) - lower_bound(a, 2), "次")      # 两个边界相减 = 出现次数

random.seed(0)
ok = True
for _ in range(2000):
    arr = sorted(random.randint(0, 10) for _ in range(random.randint(0, 12)))
    x = random.randint(-1, 11)
    ok &= lower_bound(arr, x) == bisect_left(arr, x) and upper_bound(arr, x) == bisect_right(arr, x)
print("与标准库 bisect 一致：", ok)
''')

C_ANS = code('''
import random

def can(weights, days, cap):             # 判断：运力是 cap 的话，能不能在 days 天内按顺序运完
    need, load = 1, 0
    for w in weights:
        if load + w > cap:               # 今天装不下了，换下一天
            need += 1
            load = 0
        load += w
    return need <= days

def min_capacity(weights, days):         # 二分查找「答案」：最小的、够用的运力
    lo, hi = max(weights), sum(weights)  # 答案一定在 [最重的一件, 全部重量] 之间
    while lo < hi:
        mid = (lo + hi) // 2
        if can(weights, days, mid):
            hi = mid                     # 够用，看看能不能更小
        else:
            lo = mid + 1                 # 不够，必须更大
    return lo

print(min_capacity([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 5))

def brute(weights, days):                # 对照：从小到大逐个试
    cap = max(weights)
    while not can(weights, days, cap):
        cap += 1
    return cap

random.seed(0)
ok = True
for _ in range(500):
    w = [random.randint(1, 20) for _ in range(random.randint(1, 8))]
    d = random.randint(1, len(w))
    ok &= min_capacity(w, d) == brute(w, d)
print("500 组随机数据，与逐个试的结果一致：", ok)
''')

unit = {
 "id": "u06",
 "title": "排序与二分查找",
 "en": "Sorting & Binary Search",
 "minutes": 70,
 "objectives": [
  "说出 **稳定性 (stability)**、**原地 (in-place)** 的含义，会比较插入、归并、快速排序的复杂度与适用场景",
  "理解为什么基于比较的排序有 $\\Omega(n\\log n)$ 的**下界**，以及 **计数排序 (counting sort)** 为什么能突破它",
  "知道 Python `sorted` / `list.sort` 是稳定的 **Timsort**，会用 `key` 和稳定性做多关键字排序",
  "会写**无 bug** 的二分查找：区间 $[lo,hi)$ 与循环不变量、`lower_bound` / `upper_bound`，会用标准库 `bisect`",
  "掌握 **在答案上二分 (binary search on the answer)**：只要「可行性」有单调性，就能把最优化问题变成判定问题",
 ],
 "blocks": [
  T(r"""
### 先说这一节要干什么

排序也许是计算机科学里被研究得最透彻的问题，原因有两个：它自己有用，更重要的是**有序的数据让很多事情变快**，比如二分查找、去重、合并、求中位数。这一节把前几节的工具（复杂度、分治、递归）都用一遍。

**学完它你就能看懂这几件事：**

- 为什么 Python 的 `sorted` 是 $O(n\log n)$，而且为什么它「稳定」，在 pandas 做多列排序时就用到了稳定性；
- 机器学习里到处都是排序和二分：**Top-$k$**、AUC 计算（要先按预测分数排序）、**分位数 (quantile)**、**学习率搜索 / 超参数搜索**；
- 「在答案上二分」：比如**批量大小**、**阈值**的搜索，只要性能关于它单调，就可以用二分；
- 面试的高频考点：快排、归并、`lower_bound`、旋转数组中的二分。

**本节安排（约 70 分钟）**：导读与排序的基本概念（10 分钟）→ 三种经典排序与代码（20 分钟）→ 视频一、二（7 分钟）→ 稳定性与 Python 的排序（8 分钟）→ 下界与计数排序（8 分钟）→ 二分查找与视频三（14 分钟）→ 在答案上二分（8 分钟）→「想一想」。

### 排序的几个基本概念

> **标准定义 · 排序 (sorting)、稳定性 (stability)、原地 (in-place)**
>
> **排序**：把序列重新排列成非降（或非增）的顺序。**稳定排序**保证相等的元素在排序后**保持它们原来的相对顺序**。**原地排序**只使用 $O(1)$（或很少）的额外空间。**基于比较的排序 (comparison sort)** 只通过比较两个元素的大小来决定顺序。
>
> *English: A sort is stable if equal elements keep their original relative order; it is in-place if it uses O(1) extra memory; a comparison sort only uses comparisons between elements.*

**白话版：** 稳定性在「按多个条件排」时很重要：先按名字排，再按分数排，分数相同的人如果仍保持名字顺序，那就是稳定的。

### 三种经典排序

**插入排序 (insertion sort)**：像整理扑克牌，每次拿一张，插到手里已排好的牌中合适的位置。最坏 $O(n^2)$，但**对几乎已排好序的输入是 $O(n)$**，所以实际的混合排序常用它处理小规模数据。

**归并排序 (merge sort)**：用上一节学的**分治**，分成两半，各自排好，再用「双指针」合并两个有序序列。**任何输入都是 $O(n\log n)$**，稳定，但需要 $O(n)$ 的额外空间。

**快速排序 (quicksort)**：选一个**基准 (pivot)**，把小于它的放左边、大于它的放右边，然后分别递归。**平均 $O(n\log n)$**，原地版本空间小、实际很快；但**如果基准选得不好**（比如永远选第一个，而输入已经排好序），每次只分出一个元素，退化成 $O(n^2)$。解决办法是**随机选基准**，这样最坏情况出现的概率可以忽略不计。

用代码数一数比较次数（每个算法都是自己写的）：

""" + C_SORTS + r"""

第一张表：$n$ 从 100 到 1000（10 倍），插入排序的比较次数增加约 100 倍（$O(n^2)$），归并和快排只增加约 15 倍（$O(n\log n)$）；到 $n=4000$ 时，插入排序已经需要约 400 万次，另外两个只有几万次。第二行：在已排好序的输入里，插入排序只需要 $n-1=499$ 次；而**固定取第一个元素当基准的快排退化成 $n^2/2$ 级别**（约 12.5 万次），换成随机基准就恢复了。

| 算法 | 最好 | 平均 | 最坏 | 额外空间 | 稳定 |
|---|---|---|---|---|---|
| 插入排序 | $O(n)$ | $O(n^2)$ | $O(n^2)$ | $O(1)$ | 是 |
| 归并排序 | $O(n\log n)$ | $O(n\log n)$ | $O(n\log n)$ | $O(n)$ | 是 |
| 快速排序 | $O(n\log n)$ | $O(n\log n)$ | $O(n^2)$ | $O(\log n)$ | 否（常见实现） |
| 堆排序（第 8 节） | $O(n\log n)$ | $O(n\log n)$ | $O(n\log n)$ | $O(1)$ | 否 |
"""),
  V("4VqmGXwpLqc", "视频一：Merge sort in 3 minutes（Michael Sambol）", 3),
  V("Hoixgm4-P4M", "视频二：Quick sort in 4 minutes（Michael Sambol）", 4),
  T(r"""
### Python 的排序：Timsort 与稳定性

> **标准定义 · Timsort**
>
> Python 的 `sorted()` 和 `list.sort()` 使用 **Timsort**：一种结合了归并排序和插入排序的**稳定**排序。它先找出输入里天然有序的片段（称为 **run**），再把它们归并起来。最坏 $O(n\log n)$，对**已部分有序**的数据可以接近 $O(n)$。
>
> *English: Timsort is a stable hybrid of merge sort and insertion sort that exploits existing runs in the data.*

**白话版：** 你平时写的 `sorted(...)` 已经是工业级的实现，几乎不需要自己写排序。要掌握的是怎么用它：`key=` 指定按什么排，`reverse=True` 倒序，**稳定性让你可以分多次排**：

""" + C_STABLE + r"""

同分的人（Ming、Gang、Hua）保持了在原列表里的相对顺序；先按名字、再按分数排两次，和一次用元组 `(-分数, 名字)` 当键排序，结果完全一样。**多列排序的两种写法**，都应当会。

### 排序的下界与计数排序

> **标准定义 · 比较排序的下界**
>
> 任何基于比较的排序算法，最坏情况下至少需要 $\Omega(n\log n)$ 次比较。
>
> *English: Any comparison-based sorting algorithm needs Ω(n log n) comparisons in the worst case.*

**白话版：想象一场「猜顺序」的游戏。** $n$ 个元素有 $n!$ 种可能的排列，每次比较的结果只有「大」或「小」两种，最多能把可能性砍掉一半，所以要区分 $n!$ 种情形，至少要比较 $\log_2(n!)$ 次，而 $\log_2(n!)\approx n\log_2n$。也就是说，**归并排序和堆排序在比较排序里已经是最优的了**。

但这个下界只针对「只能比较」的算法。如果元素是**范围有限的整数**，就可以不比较：**计数排序**直接数每个值出现了几次，再按顺序输出，$O(n+k)$（$k$ 是取值范围）。

""" + C_COUNT + r"""

最后一部分输出验证了下界：$n=10$ 至少要 22 次比较，$n=100$ 至少要 525 次，比较接近 $n\log_2n$。计数排序突破了这个下界，因为它**用了「元素是小整数」这个额外信息**。类似的有基数排序 (radix sort)。

### 二分查找

> **标准定义 · 二分查找 (binary search) 与循环不变量 (loop invariant)**
>
> 在**已排序**的数组里，每次比较中间元素，排除一半的候选，直到找到或区间为空，$O(\log n)$。写二分查找最容易出 bug，办法是**始终明确区间的含义，并保持循环不变量**，例如：「答案一定在半开区间 $[lo,hi)$ 里」。
>
> *English: Binary search halves the candidate range each step. A loop invariant, such as "the answer lies in [lo, hi)", keeps the implementation correct.*

**白话版：猜数字游戏。** 我心里想一个 1 到 100 的数，你猜 50，我说「大了」，你就知道答案在 1 到 49，下一次猜 25……每次排除一半，最多猜 7 次。

写成代码最好用「找边界」的形式：**`lower_bound`** 是第一个**大于等于** $x$ 的位置，**`upper_bound`** 是第一个**大于** $x$ 的位置。几乎所有二分问题（查找、插入位置、统计出现次数）都能用这两个函数表达。

""" + C_BS + r"""

读输出：对 `[1, 2, 2, 2, 5, 8, 8, 10]`，2 的 `lower_bound` 是 1、`upper_bound` 是 4，所以 2 出现了 $4-1=3$ 次；查 3 时 `lower_bound` 返回 4，正好是「如果要插入 3，应该放在哪」；查 11 返回 8（等于数组长度，表示放在末尾）。**这两个函数和标准库 `bisect.bisect_left` / `bisect_right` 完全一致**，实际使用直接用标准库就行。

**三条防 bug 规则：** ①用半开区间 $[lo,hi)$，循环条件是 `lo < hi`；②`mid = (lo + hi) // 2` 后，一定要保证 `lo` 或 `hi` 至少有一个**真的在缩小**（`lo = mid + 1` 或 `hi = mid`），否则会死循环；③写完用随机数据和标准库对拍（就像上面做的）。
"""),
  V("fDKIpRe8GW4", "视频三：Binary search in 4 minutes（Michael Sambol）", 4),
  T(r"""
### 在答案上二分

二分查找最有用的推广：**不是在数组里找东西，而是在「答案的取值范围」里找最优的那个**。条件是：对于答案 $x$，有一个**判定函数**「$x$ 可行吗？」，并且它**有单调性**：如果 $x$ 可行，那么所有更大的 $x$ 也都可行（或者反过来）。这时最优化问题（「最小的可行 $x$ 是多少」）就变成了对判定函数的二分查找。

**例子：运货。** 有一串货物，必须按顺序运，每天运的总重量不能超过运力 $c$，问：想在 $D$ 天内运完，**最小的运力**是多少？运力越大，越容易在 $D$ 天内运完（单调），所以对运力二分；判定函数 `can(c)` 只需要扫一遍货物，$O(n)$。总复杂度 $O(n\log(\text{sum}))$。

""" + C_ANS + r"""

`[1..10]` 要在 5 天内运完，最小运力是 15（比如 `1 2 3 4 5`、`6 7`、`8`、`9`、`10`）。**你不需要想明白这个答案怎么凑出来，只要写好判定函数，再二分即可。** 这个套路在算法题和工程里都很常见：比如「最小的批量大小使得显存不爆」「最小的阈值使得误报率低于 5%」「最小的 $k$ 使得……」。

### 这一节你要带走的三句话

1. **插入排序 $O(n^2)$（对几乎有序的输入快）；归并 $O(n\log n)$ 稳定但要 $O(n)$ 空间；快排平均 $O(n\log n)$，要随机选基准防最坏情况**；基于比较的排序下界是 $\Omega(n\log n)$，计数排序靠「小整数」突破它。
2. **Python 的 `sorted` 是稳定的 Timsort**：用 `key` 排序，用稳定性分多次排。
3. **二分查找 = 半开区间 + 循环不变量 + `lower_bound`**；有单调性的最优化问题，都可以**在答案上二分**。
"""),
  THINK("快速排序最坏 $O(n^2)$，归并排序最坏 $O(n\\log n)$。为什么实际中快排却常常比归并更快，更受欢迎？", r"""
几个原因：**常数小**，快排的内层循环非常简单；**原地**，只需要 $O(\log n)$ 的栈空间，不需要像归并那样分配 $O(n)$ 的辅助数组，**缓存友好**，在数组上顺序扫描；而**随机选基准**使得最坏情况的概率小到可以忽略。所以 Big-O 相同（或者更差）的情况下，快排在实践里往往更快。

但归并排序有它的优势：**稳定**、最坏情况有保证、很适合**链表**和**外部排序**（数据大到内存放不下，分块排好再归并）。这就是 Python 选择归并系的 Timsort 的原因，因为它需要稳定性。
"""),
  THINK("二分查找要求数组有序。如果你要在一个**没有排序**、但只会被查询一次的数组里找某个值，应该先排序再二分吗？", r"""
**不应该。** 先排序要 $O(n\log n)$，再二分 $O(\log n)$，总共 $O(n\log n)$；而直接线性扫描一遍只要 $O(n)$。只查一次时线性更快。

如果要**反复查询**很多次（$q$ 次），情况就变了：线性是 $O(nq)$，排序一次再每次二分是 $O(n\log n+q\log n)$，$q$ 较大时二分占优。（再用上一节的哈希表，建表 $O(n)$、每次查询 $O(1)$，总共 $O(n+q)$，通常更快，只是哈希表不支持「找第一个大于等于 $x$ 的」这种有序查询。）这是**预处理 + 多次查询**的取舍，和前缀和、哈希表是同一个模式。
"""),
  THINK("在答案上二分，必须要求判定函数有单调性。请举一个没有单调性、不能用二分的例子，并说明为什么二分会出错。", r"""
例如：「找一个整数 $x$ 使得 $x$ 的各位数字之和是偶数」，判定函数在 $x$ 变大时是「是、否、是、否……」交替的，没有单调性。二分的前提是：比较 `mid` 之后，能**肯定地丢掉一半**。这里 `mid` 不可行，并不能推出 `mid` 左边或右边整片都不可行，所以丢掉哪一半都可能丢掉答案。

可行性必须具有这样的结构：**可行的值集合是一个连续的区间，且连着一端**（如 $[x^*,\infty)$）。这时看到一个可行值，就能肯定地丢掉它右边的（不会更小），看到一个不可行的值，就能肯定地丢掉它左边的。
"""),
  KW(("稳定排序","stable sort","相等元素保持原来的相对顺序"),
     ("原地排序","in-place sort","只用 $O(1)$ 或很少的额外空间"),
     ("插入排序","insertion sort","每次把一个元素插入已排好的部分；对近乎有序的输入是 $O(n)$"),
     ("归并排序","merge sort","分治：排好两半再合并；$O(n\\log n)$，稳定，需要 $O(n)$ 空间"),
     ("快速排序","quicksort","选基准、分成小 / 大两部分再递归；平均 $O(n\\log n)$，最坏 $O(n^2)$"),
     ("基准","pivot","快排里用来划分的元素；随机选可以避免最坏情况"),
     ("Timsort","Timsort","Python 的排序：稳定、利用已有的有序片段"),
     ("比较排序的下界","comparison sort lower bound","基于比较的排序最坏至少 $\\Omega(n\\log n)$ 次比较"),
     ("计数排序","counting sort","对小整数计数后输出，$O(n+k)$，不靠比较"),
     ("二分查找","binary search","在有序数据里每次排除一半，$O(\\log n)$"),
     ("循环不变量","loop invariant","循环每一轮都保持成立的性质，如「答案在 $[lo,hi)$ 里」"),
     ("lower_bound / upper_bound","lower bound / upper bound","第一个 $\\ge x$ / 第一个 $>x$ 的位置；Python 对应 `bisect_left` / `bisect_right`"),
     ("在答案上二分","binary search on the answer","对满足单调性的判定函数二分，求最小可行解"),
  ),
 ],
 "references": [
  {"title": "Runestone：Sorting and Searching（章节目录）", "url": "https://runestone.academy/ns/books/published/pythonds/SortSearch/index.html", "note": "本节的大纲依据，含顺序查找、二分查找、冒泡 / 选择 / 插入 / 归并 / 快速排序的 Python 实现（CC BY-NC-SA 4.0）"},
  {"title": "Python 文档：Sorting HOW TO", "url": "https://docs.python.org/3/howto/sorting.html", "note": "`key`、`reverse`、多关键字排序、稳定性，Python 里排序的权威指南"},
  {"title": "Python 文档：bisect — Array bisection algorithm", "url": "https://docs.python.org/3/library/bisect.html", "note": "标准库的二分查找，`bisect_left` / `bisect_right` / `insort`"},
  {"title": "MIT OCW 6.006 Introduction to Algorithms（课程主页）", "url": "https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-spring-2020/", "note": "大学课程原版，含排序下界、计数 / 基数排序的严格讲法"},
 ],
 "quiz": {"questions": [
  Q("一个排序算法是**稳定**的，意思是？",
    ["排序的结果一定是有序的", "不使用额外空间", "相等的元素在排序后保持它们原来的相对顺序", "运行速度是稳定的"], 2,
    "稳定性只关心「相等元素的相对次序」，对多关键字排序很重要。归并排序和 Python 的 Timsort 是稳定的，常见的快速排序实现不稳定。"),
  Q("Python 内置的 `sorted()` 和 `list.sort()` 使用的是？",
    ["Timsort：稳定，最坏 $O(n\\log n)$", "快速排序", "堆排序", "冒泡排序"], 0,
    "Timsort 是归并排序和插入排序的混合，稳定，并且会利用输入里已有的有序片段。"),
  Q("基于比较的排序算法，最坏情况下比较次数的下界是？",
    ["$\\Omega(n)$", "$\\Omega(\\log n)$", "$\\Omega(n^2)$", "$\\Omega(n\\log n)$"], 3,
    "$n$ 个元素有 $n!$ 种顺序，每次比较至多排除一半，所以至少 $\\log_2(n!)\\approx n\\log_2n$ 次。"),
  Q("对一个**已经排好序**的数组，插入排序的时间复杂度是？",
    ["$O(n^2)$", "$O(n)$", "$O(n\\log n)$", "$O(\\log n)$"], 1,
    "每个元素只需要和前一个元素比较一次就发现位置对了，一共 $n-1$ 次比较。这是插入排序对近乎有序数据很快的原因。"),
  Q("如果快速排序**固定取第一个元素**当基准，对一个已排好序的数组，复杂度是？",
    ["$O(n\\log n)$", "$O(n)$", "$O(n^2)$", "$O(\\log n)$"], 2,
    "每次划分只分出一个元素（基准本身），剩下 $n-1$ 个全在一边，递归深度是 $n$，总共 $n+(n-1)+\\dots=O(n^2)$。随机选基准可以避免这种情况。"),
  Q("归并排序（数组版）的额外空间复杂度是？",
    ["$O(n)$", "$O(1)$", "$O(\\log n)$", "$O(n^2)$"], 0,
    "合并时需要一个辅助数组来存放结果，大小与 $n$ 同阶。这是它相对于原地快排的缺点。"),
  Q("`lower_bound(a, x)` 返回的是？",
    ["最后一个小于等于 $x$ 的位置", "第一个大于等于 $x$ 的位置（所有元素都小于 $x$ 时返回 `len(a)`）", "$x$ 的任意一个出现位置", "$x$ 不存在时返回 $-1$"], 1,
    "它就是「$x$ 应当插入的最靠左的位置」。Python 里对应 `bisect.bisect_left`。"),
  Q("在一个有 $10^9$ 个元素的有序数组里做二分查找，最多比较大约多少次？",
    ["约 10 次", "约 100 次", "约 1000 次", "约 30 次"], 3,
    "$\\log_2 10^9\\approx29.9$，约 30 次。数据量增加 1000 倍，只多 10 次比较。"),
  Q("计数排序（元素是 $0$ 到 $k-1$ 的整数）的时间复杂度是 $O(n+k)$，它为什么没有违反「比较排序下界 $\\Omega(n\\log n)$」？",
    ["它不是基于比较的排序，利用了「元素是小整数」这一额外信息", "下界在 $k$ 很小时不成立", "因为它是递归实现的", "它其实也是 $O(n\\log n)$"], 0,
    "下界只对「仅靠比较元素大小」的算法成立。计数排序直接用元素的值当下标，不比较。代价是需要额外的 $O(k)$ 空间，且 $k$ 不能太大。"),
  Q("「在答案上二分」要求判定函数（「$x$ 是否可行」）满足什么条件？",
    ["数组必须有序", "答案必须是整数", "具有单调性：若 $x$ 可行，则所有更大（或更小）的值也可行", "必须用递归实现"], 2,
    "有单调性，看到一个可行或不可行的值，才能肯定地丢掉一半区间。数组本身不需要存在，答案范围就是搜索空间。"),
 ]},
}

if __name__ == '__main__':
    dump(unit, "dsa-0", "u06-sorting-binary-search.json")
