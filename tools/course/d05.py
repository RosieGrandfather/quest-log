"""dsa-0 第 5 节：递归进阶：分治与回溯"""
from unitlib import *
from runlib import code

C_FIB = code('''
calls = 0
def fib_naive(n):                        # 朴素递归：同一个子问题被反复计算
    global calls
    calls += 1
    return n if n < 2 else fib_naive(n - 1) + fib_naive(n - 2)

memo, mcalls = {}, 0
def fib_memo(n):                         # 记忆化：算过的存进字典，下次直接查
    global mcalls
    mcalls += 1
    if n in memo:
        return memo[n]
    memo[n] = n if n < 2 else fib_memo(n - 1) + fib_memo(n - 2)
    return memo[n]

for n in (10, 20, 25, 30):
    calls = mcalls = 0
    memo.clear()
    same = fib_naive(n) == fib_memo(n)
    print(f"n={n:<3} 结果一致 {same}   朴素 {calls:>8} 次调用   记忆化 {mcalls:>3} 次调用")
''')

C_REC = code('''
# 把四种递归关系式直接写成代码，数一数 T(n)，和理论公式对照
def T1(n): return 1 if n <= 1 else T1(n // 2) + 1          # T(n) = T(n/2) + 1     （二分查找）
def T2(n): return 1 if n <= 1 else 2 * T2(n // 2) + n      # T(n) = 2T(n/2) + n    （归并排序）
def T3(n): return 1 if n <= 1 else 2 * T3(n // 2) + 1      # T(n) = 2T(n/2) + 1    （遍历二叉树）
def T4(n): return 1 if n <= 1 else T4(n - 1) + n           # T(n) = T(n-1) + n     （每次只少一个）

print("   n    T1      T2     T3      T4")
for k in (3, 6, 9):
    n = 2 ** k
    print(f"{n:>4} {T1(n):>5} {T2(n):>7} {T3(n):>6} {T4(n):>7}")

# 对照公式：log2(n)+1,  n·log2(n)+n,  2n-1,  n(n+1)/2
ok = all(T1(2**k) == k + 1 and T2(2**k) == k * 2**k + 2**k and
         T3(2**k) == 2 * 2**k - 1 and T4(2**k) == 2**k * (2**k + 1) // 2 for k in range(1, 10))
print("四个公式在 n = 2^1 .. 2^9 上全部成立：", ok)
''')

C_POW = code('''
mults = 0
def power_naive(x, n):                   # 朴素：连乘 n 次
    global mults
    r = 1
    for _ in range(n):
        r *= x
        mults += 1
    return r

def power_fast(x, n):                    # 快速幂：x^n = (x^(n/2))²，每次问题规模减半
    global mults
    if n == 0:
        return 1
    half = power_fast(x, n // 2)         # 只递归一次，把结果存下来用两次
    mults += 1
    if n % 2 == 0:
        return half * half
    mults += 1
    return half * half * x               # n 是奇数，还要多乘一个 x

for n in (10, 100, 1000):
    mults = 0
    a = power_naive(3, n)
    m1 = mults
    mults = 0
    b = power_fast(3, n)
    print(f"n={n:<5} 结果正确 {a == b == 3 ** n}   朴素 {m1} 次乘法   快速幂 {mults} 次乘法")

def pow_mod(x, n, m):                    # 模幂：每一步都取余，数字不会变大；密码学和哈希里常用
    if n == 0:
        return 1
    half = pow_mod(x, n // 2, m)
    r = half * half % m
    return r * x % m if n % 2 else r

print(pow_mod(3, 10**18, 1000007) == pow(3, 10**18, 1000007))   # 10^18 次幂，递归只有约 60 层
''')

C_MAXSUB = code('''
import random

def max_sub_dc(a, lo, hi):               # 分治：求 a[lo:hi] 的最大连续子数组之和
    if hi - lo == 1:
        return a[lo]
    mid = (lo + hi) // 2
    # 跨过中点的最优解 = 从中点向左延伸的最大和 + 从中点向右延伸的最大和
    left, s = float('-inf'), 0
    for i in range(mid - 1, lo - 1, -1):
        s += a[i]
        left = max(left, s)
    right, s = float('-inf'), 0
    for i in range(mid, hi):
        s += a[i]
        right = max(right, s)
    # 最优解要么完全在左半边，要么完全在右半边，要么跨过中点
    return max(max_sub_dc(a, lo, mid), max_sub_dc(a, mid, hi), left + right)

def brute(a):                            # 暴力法 O(n²)，用来对照
    return max(sum(a[i:j]) for i in range(len(a)) for j in range(i + 1, len(a) + 1))

a = [-2, 1, -3, 4, -1, 2, 1, -5, 4]
print(max_sub_dc(a, 0, len(a)), brute(a))

random.seed(0)
tests = ([random.randint(-9, 9) for _ in range(random.randint(1, 15))] for _ in range(2000))
print("2000 组随机数据，分治和暴力法一致：", all(max_sub_dc(x, 0, len(x)) == brute(x) for x in tests))
''')

C_BT = code('''
def subsets(nums):
    res, path = [], []
    def dfs(i):                          # 对第 i 个元素：选，还是不选
        if i == len(nums):
            res.append(path[:])          # 一个完整的选择方案；path[:] 是拷贝，否则后面会被改掉
            return
        dfs(i + 1)                       # 不选 nums[i]
        path.append(nums[i])             # 选择 nums[i]
        dfs(i + 1)                       # 探索
        path.pop()                       # 撤销选择，回到之前的状态
    dfs(0)
    return res

def permutations(nums):
    res, path, used = [], [], [False] * len(nums)
    def dfs():
        if len(path) == len(nums):
            res.append(path[:])
            return
        for i in range(len(nums)):
            if used[i]:
                continue
            used[i] = True               # 选择：把 nums[i] 放在当前位置
            path.append(nums[i])
            dfs()                        # 探索：继续安排下一个位置
            path.pop()                   # 撤销选择
            used[i] = False
    dfs()
    return res

print(subsets([1, 2, 3]))
print(permutations([1, 2, 3]))
print(len(subsets(list(range(10)))), len(permutations(list(range(6)))))   # 2^10 和 6!
''')

C_QUEEN = code('''
def solve(n):
    cols, d1, d2 = set(), set(), set()   # 已被占用的列、主对角线 (r-c)、副对角线 (r+c)
    path, sols, nodes = [], [], 0
    def place(r):                        # 在第 r 行放一个皇后
        nonlocal nodes
        nodes += 1
        if r == n:
            sols.append(path[:])
            return
        for c in range(n):
            if c in cols or r - c in d1 or r + c in d2:
                continue                 # 剪枝：这一格会被已有的皇后攻击，整棵子树都不用看了
            path.append(c); cols.add(c); d1.add(r - c); d2.add(r + c)     # 选择
            place(r + 1)                                                  # 探索
            path.pop(); cols.discard(c); d1.discard(r - c); d2.discard(r + c)   # 撤销
    place(0)
    return sols, nodes

print("n  解的个数  剪枝后访问的节点  不剪枝时的节点总数")
for n in range(4, 9):
    sols, nodes = solve(n)
    full = (n ** (n + 1) - 1) // (n - 1)         # 不剪枝：每行 n 种放法，整棵树的节点数
    print(f"{n}  {len(sols):>8}  {nodes:>14}  {full:>16}")

sols, _ = solve(6)
print("n=6 的第一个解：")
for c in sols[0]:
    print("".join("Q" if j == c else "." for j in range(6)))
''')

unit = {
 "id": "u05",
 "title": "递归进阶：分治与回溯",
 "en": "Divide & Conquer, Backtracking",
 "minutes": 75,
 "objectives": [
  "说出 **递归 (recursion)** 的两个必要部分（基准情形 + 递归情形），会画 **递归树 (recursion tree)** 估算调用次数",
  "会写 **递推关系式 (recurrence relation)**，并用 **主定理 (master theorem)** 的思路判断 $T(n)=aT(n/b)+f(n)$ 的量级",
  "理解 **分治 (divide and conquer)** 的三步，会写快速幂与最大子数组",
  "掌握 **回溯 (backtracking)** 的「选择、探索、撤销」模板，会用 **剪枝 (pruning)** 提速，会写子集、排列与 N 皇后",
  "看出朴素递归里「子问题重复」的问题，为第 11 节的动态规划做铺垫",
 ],
 "blocks": [
  T(r"""
### 先说这一节要干什么

前面的数据结构全是「怎么存」，从这一节开始进入「怎么算」，也就是**算法设计**。递归是最重要的设计思想：**把一个大问题拆成同样形状的小问题，小问题的答案拼起来就是大问题的答案**。这一节学两种基于递归的套路：

- **分治**：把问题**分成独立的几块**，各自解决，再合并。排序（第 6 节）、树（第 7 节）都是它。
- **回溯**：问题的答案是一连串**选择**。每一步试一种选择，走不通就**退回来**换一种。数独、迷宫、排列组合都是它。

**学完它你就能看懂这几件事：**

- 为什么归并排序是 $O(n\log n)$：递推关系式 $T(n)=2T(n/2)+n$；
- 为什么朴素斐波那契慢得离谱，记忆化为什么能救它，也就是第 11 节「动态规划」的起点；
- 深度学习里的**反向传播**本质上是在计算图上做递归；**束搜索 (beam search)**、树搜索（如 AlphaGo 的蒙特卡洛树搜索）是在做带剪枝的搜索；
- 面试里最常见的「子集」「排列」「N 皇后」。

**本节安排（约 75 分钟）**：递归与递归树（15 分钟）→ 递推关系式（12 分钟）→ 视频一（7 分钟）→ 分治与快速幂（15 分钟）→ 回溯（15 分钟）→ 视频二、三（25 分钟）→「想一想」。

### 递归

> **标准定义 · 递归 (recursion)**
>
> 一个函数直接或间接调用自身，称为**递归**。一个正确的递归函数需要：**基准情形 (base case)**，不再递归、直接给出答案；**递归情形 (recursive case)**，把问题化为**更小**的同类问题，并保证每次递归都向基准情形靠近。
>
> *English: A recursive function calls itself. It needs a base case that stops the recursion, and a recursive case that reduces the problem towards the base case.*

**白话版：俄罗斯套娃。** 打开一个娃娃，里面是一个更小的同样的娃娃，一直打开，直到最小的那个实心的（基准情形）。没有最小的那个，你就会无穷无尽地打开下去，这就是**无限递归**（Python 里会抛出 `RecursionError`）。

递归的复杂度要看**调用了多少次**，所以要画**递归树**：每次调用是一个节点，它的子调用是孩子。看斐波那契 $F(n)=F(n-1)+F(n-2)$：$F(n)$ 要调用 $F(n-1)$ 和 $F(n-2)$，后两者又各自分叉……

""" + C_FIB + r"""

朴素版的调用次数大约每增加 1 就乘 1.6 倍（实际上是 $2F(n+1)-1$，和斐波那契数本身同阶，约 $1.618^n$），到 $n=30$ 已经 270 万次；而记忆化版本只有 $2n-1$ 次调用。**原因是朴素递归树里有大量重复的子问题**（$F(28)$ 被算了无数次），记忆化把算过的存下来，每个子问题只算一次，这正是第 11 节动态规划的核心想法。

### 递推关系式与主定理

> **标准定义 · 递推关系式 (recurrence relation) 与主定理 (master theorem)**
>
> 若算法把规模 $n$ 的问题分成 $a$ 个规模 $n/b$ 的子问题，解决后用 $\Theta(n^d)$ 的代价合并，则运行时间满足 $T(n)=aT(n/b)+\Theta(n^d)$。比较 $d$ 和 $\log_b a$：
>
> - $d<\log_b a$：$T(n)=\Theta(n^{\log_b a})$（叶子层主导）；
> - $d=\log_b a$：$T(n)=\Theta(n^d\log n)$（每一层代价相同，共 $\log n$ 层）；
> - $d>\log_b a$：$T(n)=\Theta(n^d)$（根节点主导）。
>
> *English: For T(n) = aT(n/b) + Θ(n^d), compare d with log_b a: the answer is dominated by the leaves, balanced across levels, or dominated by the root.*

**白话版：看「分」和「合」哪个更花力气。** 想象递归树：每往下一层，子问题变多（$a$ 倍），但每个更小（$1/b$）。如果「合并」代价小，大部分工作在最底层的叶子；如果合并代价大，大部分工作在最顶上的根；刚好持平，那每一层的工作量相同，总共 $\log n$ 层，乘起来就是 $n^d\log n$。

| 算法 | 递推关系 | $a,b,d$ | 结果 |
|---|---|---|---|
| 二分查找 | $T(n)=T(n/2)+1$ | 1, 2, 0 | $d=\log_21=0$：$\Theta(\log n)$ |
| 归并排序 | $T(n)=2T(n/2)+n$ | 2, 2, 1 | $d=\log_22=1$：$\Theta(n\log n)$ |
| 遍历二叉树 | $T(n)=2T(n/2)+1$ | 2, 2, 0 | $d<1$：$\Theta(n)$ |
| Karatsuba 乘法 | $T(n)=3T(n/2)+n$ | 3, 2, 1 | $d<\log_23\approx1.58$：$\Theta(n^{1.58})$ |
| 每次只少一个 | $T(n)=T(n-1)+n$ | （不是「分」） | $\Theta(n^2)$ |

把前四种直接写成代码数一数，和公式对照：

""" + C_REC + r"""

$T_2$ 一列就是 $n\log_2n+n$：$n=512$ 时 $512\times9+512=5120$，和输出一致，量级是 $n\log n$。注意最后一种 $T(n)=T(n-1)+n$ 不适用主定理（问题只缩小 1，不是按比例），要用求和（$1+2+\dots+n$）。
"""),
  V("2Rr2tW9zvRg", "视频一：Divide And Conquer（Abdul Bari）", 7),
  T(r"""
### 分治

> **标准定义 · 分治 (divide and conquer)**
>
> 分治法分三步：**分解 (divide)**：把问题分成若干个**互相独立**的、规模更小的子问题；**求解 (conquer)**：递归地解决子问题（规模足够小时直接解）；**合并 (combine)**：把子问题的解合并成原问题的解。
>
> *English: Divide the problem into independent subproblems, solve each recursively, then combine their solutions.*

**白话版：「分、治、合」。** 一个班要整理 1000 份试卷，你不会一个人从头排到尾，而是分给 10 个人各排 100 份，每人再分给同学……最后再把排好的合起来。关键是**子问题互不相关**（这一点和 DP 不同，DP 的子问题是重叠的）。

**例一：快速幂。** 计算 $x^n$。朴素做法连乘 $n$ 次，$O(n)$。分治：$x^n=(x^{n/2})^2$（$n$ 为偶数）或 $(x^{(n-1)/2})^2\cdot x$（$n$ 为奇数）。每次把指数减半，递推 $T(n)=T(n/2)+O(1)$，所以是 $O(\log n)$。

""" + C_POW + r"""

$n=1000$ 时，朴素做法 1000 次乘法，快速幂只要十几次。**一个重要的细节**：`half = power_fast(x, n // 2)` 只递归一次，把结果存下来，再平方。如果写成 `power_fast(x, n//2) * power_fast(x, n//2)`，就递归了两次，复杂度会退回 $O(n)$。最后一行：模幂在 $10^{18}$ 次方下也只需约 60 层递归，这是 RSA 加密、哈希计算的基础。

**例二：最大子数组和。** 在一个整数数组里，找和最大的连续一段。分治：最优解要么完全在左半边，要么完全在右半边，要么**跨过中点**，前两种递归求解，第三种用一次线性扫描求出（从中点向左、向右各自延伸的最大和），递推 $T(n)=2T(n/2)+O(n)$，所以是 $O(n\log n)$。

""" + C_MAXSUB + r"""

经典例子 `[-2, 1, -3, 4, -1, 2, 1, -5, 4]` 的答案是 6（子数组 `[4, -1, 2, 1]`）。（这道题其实还有 $O(n)$ 的动态规划解法 Kadane 算法，第 11 节再看，这里主要是练习分治的思路。）

### 回溯

> **标准定义 · 回溯 (backtracking) 与剪枝 (pruning)**
>
> **回溯**是系统地搜索「一连串选择」的所有可能：每一步**选择 (choose)** 一个候选，**探索 (explore)** 它之后的所有可能（递归），然后**撤销选择 (un-choose)**，回到之前的状态，再试下一个候选。若发现当前部分方案**不可能**导出合法解，就立即放弃它，不再往下探索，称为**剪枝**。
>
> *English: Backtracking builds a solution incrementally by choosing, exploring, and undoing the choice; pruning abandons a partial solution as soon as it cannot lead to a valid answer.*

**白话版：走迷宫，碰壁就退回上一个岔路口。** 每个岔路口你选一条走下去，走到死胡同就退回来，换另一条。回溯的核心就是**「撤销」**：递归返回之后，要把状态恢复成进入之前的样子，这样才能干净地试下一个选择。模板只有三行：

```python
选择    ← path.append(x)
探索    ← dfs(下一步)
撤销选择 ← path.pop()
```

下面用三个经典例子来看：**子集**（每个元素选或不选，共 $2^n$ 个）、**排列**（$n!$ 个）、**N 皇后**（在 $n\times n$ 棋盘上放 $n$ 个互不攻击的皇后）。前两个枚举全部可能，不需要剪枝；N 皇后要剪枝。

""" + C_BT + r"""

子集共 $2^{10}=1024$ 个、排列共 $6!=720$ 个。这类题的复杂度本身就是**指数 / 阶乘级**：答案的数量就这么多，没办法更少，所以回溯只适合 $n$ 很小（通常 $n\le20$）的场合。

N 皇后：每行放一个皇后，逐行放；若某一格的列、主对角线、副对角线被占了，就**剪枝**，不用再往下看。

""" + C_QUEEN + r"""

$n=8$ 时有 92 个解；剪枝版访问了约 2000 个节点，而不剪枝要访问约 1900 万个。**剪枝让搜索范围缩小了几个数量级。** 但要注意，回溯在最坏情况下仍然是指数级的，剪枝只是让常见情形快得多。
"""),
  V("p9m2LHBW81M", "视频二：Solve ANY Backtracking Problem on Leetcode (Template + Explanation)（Bitflip）", 7),
  V("Ph95IHmRp5M", "视频三（选看）：N-Queens - Backtracking - Leetcode 51 - Python（NeetCode）", 18),
  T(r"""
### 这一节你要带走的三句话

1. **递归 = 基准情形 + 向基准靠近的递归情形**；复杂度看递归树的节点总数，或者写递推关系式（$T(n)=aT(n/b)+f(n)$）再套主定理。
2. **分治 = 分、治、合**，子问题**互相独立**；若子问题**重叠**（如朴素斐波那契），要用记忆化 / 动态规划。
3. **回溯 = 选择、探索、撤销选择**；**剪枝**能大幅缩小搜索空间，但最坏情况仍是指数级。
"""),
  THINK("斐波那契的朴素递归和归并排序都是「把问题拆成两个小问题」，为什么前者是指数级，后者却只是 $O(n\\log n)$？", r"""
关键在**子问题的规模**和**是否重叠**。归并排序把规模 $n$ 的问题**平分**成两个规模 $n/2$ 的问题，递归树只有 $\log n$ 层，每层总工作量 $O(n)$，合起来 $O(n\log n)$。

斐波那契把规模 $n$ 的问题拆成规模 $n-1$ 和 $n-2$（**只缩小了一点点**），递归树有 $n$ 层深，每层节点数几乎翻倍，加起来指数级；而且这两个子问题**高度重叠**（$F(n-2)$ 在两边各算一次），大量重复工作。所以：**子问题只缩小一点、又互相重叠，就会爆炸**。解决办法是记忆化，把指数降到 $O(n)$。
"""),
  THINK("在快速幂里，如果把 `half = power_fast(x, n // 2)` 写成 `return power_fast(x, n // 2) * power_fast(x, n // 2)`（偶数情形），复杂度会变成多少？用主定理解释。", r"""
递推关系从 $T(n)=T(n/2)+O(1)$ 变成了 $T(n)=2T(n/2)+O(1)$，也就是 $a=2,\ b=2,\ d=0$。$d=0<\log_22=1$，所以 $T(n)=\Theta(n^{\log_22})=\Theta(n)$，退回了线性，跟朴素连乘一样慢。

这个例子说明：分治里**每个子问题只能算一次，要把结果存下来重复使用**。同样的两次调用，只是一个小小的写法差别，复杂度就从 $\log n$ 变成了 $n$。
"""),
  THINK("回溯里「撤销选择」这一步如果忘了写（比如子集代码里漏掉 `path.pop()`），会出什么问题？", r"""
`path` 是一个**共享的列表**，所有层的递归都在同一个对象上操作。不撤销的话，当一层递归结束返回后，它加进去的元素仍然留在 `path` 里，下一个分支在此基础上继续追加，**状态被污染了**：后面生成的「方案」里会混进不该有的元素，数量和内容都会错。

另一个常见错误是保存结果时写 `res.append(path)`（没有拷贝）：`res` 里存的全是同一个 `path` 对象的引用，最后它被所有回溯操作改回空列表，`res` 就变成一堆空列表。要写 `res.append(path[:])` 或 `list(path)`，存一份快照。
"""),
  KW(("递归","recursion","函数调用自身，把问题化为更小的同类问题"),
     ("基准情形","base case","不再递归、直接给出答案的情形"),
     ("递归树","recursion tree","每次调用是一个节点，用来数调用次数"),
     ("递推关系式","recurrence relation","用更小规模的 $T$ 表示 $T(n)$ 的式子"),
     ("主定理","master theorem","判断 $T(n)=aT(n/b)+f(n)$ 的量级：叶子主导 / 均衡 / 根主导"),
     ("分治","divide and conquer","分解成独立子问题、递归求解、合并"),
     ("快速幂","fast exponentiation","$x^n=(x^{n/2})^2$，$O(\\log n)$ 次乘法"),
     ("记忆化","memoization","把算过的子问题答案存起来，避免重复计算"),
     ("回溯","backtracking","选择、探索、撤销选择，系统搜索所有可能"),
     ("剪枝","pruning","发现当前方案不可能得到合法解就不再往下探索"),
     ("子集 / 排列","subsets / permutations","共 $2^n$ 个 / $n!$ 个，回溯的典型例子"),
     ("N 皇后","N-Queens","在 $n\\times n$ 棋盘放 $n$ 个互不攻击的皇后，剪枝的经典例子"),
  ),
 ],
 "references": [
  {"title": "Runestone：Recursion（章节目录）", "url": "https://runestone.academy/ns/books/published/pythonds/Recursion/index.html", "note": "本节的大纲依据之一，含递归三定律、汉诺塔、动态规划引入（CC BY-NC-SA 4.0）"},
  {"title": "MIT OCW 6.006 Introduction to Algorithms（课程主页）", "url": "https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-spring-2020/", "note": "大学课程原版，讲分治的递推式与主定理的严格推导，难度更高"},
  {"title": "Python 文档：itertools（permutations / combinations / product）", "url": "https://docs.python.org/3/library/itertools.html", "note": "标准库已经提供了排列组合的现成实现，实际使用时直接用它"},
 ],
 "quiz": {"questions": [
  Q("一个正确的递归函数必须包含？",
    ["基准情形，否则会无限递归", "一个 `for` 循环", "全局变量", "一个列表"], 0,
    "没有基准情形，递归永远不会停止，Python 会抛出 `RecursionError`。同时递归情形必须使问题向基准情形靠近。"),
  Q("朴素递归计算 $F(n)=F(n-1)+F(n-2)$，调用次数的增长速度是？",
    ["$O(n)$", "$O(n^2)$", "指数级（约 $1.618^n$）", "$O(\\log n)$"], 2,
    "递归树每层几乎翻倍，而且有大量重复子问题。上面的数据：$n=30$ 时已经有 270 万次调用。"),
  Q("给朴素斐波那契加上记忆化（把算过的结果存进字典）后，调用次数变成？",
    ["指数级", "$O(n^2)$", "$O(\\log n)$", "$O(n)$"], 3,
    "每个子问题 $F(0),\\dots,F(n)$ 只会真正计算一次，总调用次数是 $2n-1$ 这个量级，即 $O(n)$。"),
  Q("递推关系 $T(n)=2T(n/2)+n$（如归并排序）的解是？",
    ["$O(n)$", "$O(n\\log n)$", "$O(n^2)$", "$O(\\log n)$"], 1,
    "$a=2,b=2,d=1$，$d=\\log_ba$，每一层代价相同（$n$），共 $\\log n$ 层，总计 $\\Theta(n\\log n)$。"),
  Q("递推关系 $T(n)=T(n/2)+1$（如二分查找）的解是？",
    ["$O(\\log n)$", "$O(n)$", "$O(n\\log n)$", "$O(1)$"], 0,
    "每次问题减半，每层 $O(1)$，一共 $\\log_2 n$ 层，所以是 $O(\\log n)$。"),
  Q("用分治的快速幂算 $x^n$，需要的乘法次数是？",
    ["$O(n)$", "$O(n\\log n)$", "$O(\\log n)$", "$O(1)$"], 2,
    "每次把指数减半，只需递归一次，最多 $\\log_2 n$ 层，每层做 1 到 2 次乘法。"),
  Q("回溯算法每一步的三个动作是？",
    ["排序、查找、返回", "选择、探索（递归）、撤销选择", "分解、求解、合并", "输入、处理、输出"], 1,
    "选择一个候选，递归探索之后的所有可能，然后撤销选择，回到原来的状态再试下一个。分解、求解、合并是分治的三步。"),
  Q("回溯中的「剪枝」指的是？",
    ["把递归改写成循环", "把算过的结果缓存起来", "合并两个子问题的答案", "一旦发现当前方案不可能得到合法解，就不再往下探索"], 3,
    "剪枝是提前放弃没有希望的分支。N 皇后里发现某一格被攻击就跳过，能把搜索范围缩小几个数量级。缓存结果是记忆化。"),
  Q("对 $n=10$ 个不同元素，全部子集的个数和全部排列的个数分别是？",
    ["100 和 1000", "1024 和 100", "1024 和 3628800", "3628800 和 1024"], 2,
    "子集 $2^{10}=1024$，排列 $10!=3628800$。这类枚举本身就是指数或阶乘级，所以只适合小规模的 $n$。"),
  Q("分治法的三个步骤是？",
    ["分解成子问题、递归解决子问题、合并答案", "查表、插入、删除", "压栈、出栈、查看栈顶", "哈希、探测、扩容"], 0,
    "分治 = 分解 (divide)、求解 (conquer)、合并 (combine)。它要求子问题彼此独立，这是和动态规划的一个区别。"),
 ]},
}

if __name__ == '__main__':
    dump(unit, "dsa-0", "u05-divide-backtrack.json")
