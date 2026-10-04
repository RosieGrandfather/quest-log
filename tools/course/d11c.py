from runlib import code

C_FIB = code('''
from functools import lru_cache
import time

calls = 0
def fib_naive(n):
    global calls
    calls += 1
    return n if n < 2 else fib_naive(n - 1) + fib_naive(n - 2)

for n in (10, 20, 25, 30):
    calls = 0
    fib_naive(n)
    print(f"朴素递归 fib({n}) 调用了 {calls} 次")

# 自顶向下 (top-down)：递归 + 记忆化 (memoization)
memo_calls = 0
@lru_cache(maxsize=None)
def fib_memo(n):
    global memo_calls
    memo_calls += 1                 # 只在「真正计算」时才会进到这里
    return n if n < 2 else fib_memo(n - 1) + fib_memo(n - 2)
print("记忆化 fib(30) =", fib_memo(30), "，函数体只执行了", memo_calls, "次")

# 自底向上 (bottom-up)：从小到大填表，只保留最近两个值，空间 O(1)
def fib_dp(n):
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a
print("自底向上 fib(30) =", fib_dp(30))
print("fib(200) =", fib_dp(200), "（Python 的整数不会溢出）")

t = time.perf_counter(); fib_naive(32); t1 = time.perf_counter() - t
t = time.perf_counter(); fib_dp(32); t2 = time.perf_counter() - t
print(f"fib(32)：朴素递归比自底向上慢约 {t1 / t2:.0f} 倍（因机器而异）")
''')

C_COIN = code('''
from functools import lru_cache
from collections import deque

coins, amount = [1, 3, 4], 6

# 贪心：每次拿最大的。能保证最少吗？
def greedy(coins, amount):
    cnt = 0
    for c in sorted(coins, reverse=True):
        cnt += amount // c; amount %= c
    return cnt
print("贪心：6 = 4+1+1 →", greedy(coins, amount), "枚")

# DP：dp[a] = 凑出金额 a 最少需要的硬币数
def coin_change(coins, amount):
    INF = float("inf")
    dp = [0] + [INF] * amount
    choice = [None] * (amount + 1)           # 记下最后一步选了哪种硬币，用来还原方案
    for a in range(1, amount + 1):
        for c in coins:
            if c <= a and dp[a - c] + 1 < dp[a]:
                dp[a] = dp[a - c] + 1
                choice[a] = c
    if dp[amount] == INF:
        return -1, []
    used, a = [], amount
    while a > 0:
        used.append(choice[a]); a -= choice[a]
    return dp[amount], used

print("DP：", coin_change(coins, amount))
print("金额 7，硬币 [2, 4]（凑不出）：", coin_change([2, 4], 7))

# 验证：用 BFS（每一步加一枚硬币，层数 = 硬币数）当参照
def coin_bfs(coins, amount):
    seen, q = {0}, deque([(0, 0)])
    while q:
        a, k = q.popleft()
        if a == amount: return k
        for c in coins:
            if a + c <= amount and a + c not in seen:
                seen.add(a + c); q.append((a + c, k + 1))
    return -1

import random
random.seed(0)
ok = True
for _ in range(500):
    cs = random.sample(range(1, 12), random.randint(1, 4))
    am = random.randint(0, 40)
    ok &= (coin_change(cs, am)[0] == coin_bfs(cs, am))
print("coin_change 与 BFS 在 500 组随机输入上一致：", ok)
''')

C_KNAP = code('''
import itertools, random

# 0/1 背包：n 件物品，各有重量 w、价值 v，背包容量 W，每件至多拿一次，求最大价值
def knapsack_2d(ws, vs, W):
    n = len(ws)
    dp = [[0] * (W + 1) for _ in range(n + 1)]       # dp[i][c] = 只用前 i 件、容量 c 时的最大价值
    for i in range(1, n + 1):
        for c in range(W + 1):
            dp[i][c] = dp[i - 1][c]                  # 不拿第 i 件
            if ws[i - 1] <= c:                       # 拿第 i 件
                dp[i][c] = max(dp[i][c], dp[i - 1][c - ws[i - 1]] + vs[i - 1])
    # 还原：从 dp[n][W] 往回走
    picked, c = [], W
    for i in range(n, 0, -1):
        if dp[i][c] != dp[i - 1][c]:
            picked.append(i - 1); c -= ws[i - 1]
    return dp[n][W], sorted(picked)

def knapsack_1d(ws, vs, W):
    dp = [0] * (W + 1)                               # 只保留一行：空间从 O(nW) 降到 O(W)
    for w, v in zip(ws, vs):
        for c in range(W, w - 1, -1):                # 容量要「从大到小」遍历！
            dp[c] = max(dp[c], dp[c - w] + v)
    return dp[W]

def knapsack_wrong(ws, vs, W):
    dp = [0] * (W + 1)
    for w, v in zip(ws, vs):
        for c in range(w, W + 1):                    # 「从小到大」：同一件物品可能被重复拿
            dp[c] = max(dp[c], dp[c - w] + v)
    return dp[W]

ws, vs, W = [1, 3, 4, 5], [1, 4, 5, 7], 7
print("二维 DP：", knapsack_2d(ws, vs, W))
print("一维 DP：", knapsack_1d(ws, vs, W))
# 只有一件「重 3、值 5」的物品、容量 7：正确答案 5（只能拿一次）
print("一件物品、容量 7：正确", knapsack_1d([3], [5], 7), "；方向写反", knapsack_wrong([3], [5], 7), "（同一件被拿了两次）")

# 验证：枚举所有 2^n 个子集
def brute(ws, vs, W):
    best = 0
    for mask in range(1 << len(ws)):
        w = sum(ws[i] for i in range(len(ws)) if mask >> i & 1)
        if w <= W:
            best = max(best, sum(vs[i] for i in range(len(ws)) if mask >> i & 1))
    return best

random.seed(1)
ok = True
for _ in range(300):
    n = random.randint(1, 8)
    a = [random.randint(1, 9) for _ in range(n)]
    b = [random.randint(1, 20) for _ in range(n)]
    Wc = random.randint(0, 25)
    ok &= (knapsack_2d(a, b, Wc)[0] == knapsack_1d(a, b, Wc) == brute(a, b, Wc))
print("二维 = 一维 = 暴力枚举（300 组随机输入）：", ok)
''')

C_SEQ = code('''
import itertools, random
from functools import lru_cache

def lcs(a, b):
    m, n = len(a), len(b)
    dp = [[0] * (n + 1) for _ in range(m + 1)]       # dp[i][j] = a[:i] 与 b[:j] 的最长公共子序列长度
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if a[i - 1] == b[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
    # 还原一个具体的 LCS
    i, j, out = m, n, []
    while i > 0 and j > 0:
        if a[i - 1] == b[j - 1]:
            out.append(a[i - 1]); i -= 1; j -= 1
        elif dp[i - 1][j] >= dp[i][j - 1]:
            i -= 1
        else:
            j -= 1
    return dp[m][n], "".join(reversed(out)), dp

L, s, table = lcs("ABCBDAB", "BDCABA")
print("LCS 长度", L, "，一个 LCS：", s)
for row in table:
    print(row)

def edit_distance(a, b):
    m, n = len(a), len(b)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(m + 1): dp[i][0] = i              # a[:i] 变成空串：删 i 次
    for j in range(n + 1): dp[0][j] = j              # 空串变成 b[:j]：插 j 次
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if a[i - 1] == b[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                dp[i][j] = 1 + min(dp[i - 1][j],     # 删除
                                   dp[i][j - 1],     # 插入
                                   dp[i - 1][j - 1]) # 替换
    return dp[m][n]

print("kitten → sitting 的编辑距离：", edit_distance("kitten", "sitting"))
print("intention → execution：", edit_distance("intention", "execution"))

# 验证：LCS 与「枚举 a 的所有子序列」比较；编辑距离与朴素递归比较
def lcs_brute(a, b):
    best = 0
    for r in range(len(a) + 1):
        for sub in itertools.combinations(a, r):
            it = iter(b)
            if all(ch in it for ch in sub):          # 判断 sub 是不是 b 的子序列
                best = max(best, r)
    return best

def ed_rec(a, b):
    @lru_cache(maxsize=None)
    def f(i, j):
        if i == 0: return j
        if j == 0: return i
        if a[i-1] == b[j-1]: return f(i-1, j-1)
        return 1 + min(f(i-1, j), f(i, j-1), f(i-1, j-1))
    return f(len(a), len(b))

random.seed(2)
ok1 = ok2 = True
for _ in range(300):
    a = "".join(random.choice("ABC") for _ in range(random.randint(0, 8)))
    b = "".join(random.choice("ABC") for _ in range(random.randint(0, 8)))
    ok1 &= (lcs(a, b)[0] == lcs_brute(a, b))
    ok2 &= (edit_distance(a, b) == ed_rec(a, b))
print("LCS 与暴力枚举一致：", ok1, "；编辑距离与记忆化递归一致：", ok2)
''')

C_KAD = code('''
import random, bisect

# 最大子数组和（Kadane）：dp[i] = 以 i 结尾的最大子数组和 = max(a[i], dp[i-1] + a[i])
def kadane(a):
    best = cur = a[0]
    for x in a[1:]:
        cur = max(x, cur + x)         # 要么从 x 重新开始，要么接在前面后面
        best = max(best, cur)
    return best

# 最长递增子序列 (LIS)：O(n^2) 的 DP 与 O(n log n) 的「耐心排序」
def lis_dp(a):
    dp = [1] * len(a)                 # dp[i] = 以 a[i] 结尾的 LIS 长度
    for i in range(len(a)):
        for j in range(i):
            if a[j] < a[i]:
                dp[i] = max(dp[i], dp[j] + 1)
    return max(dp, default=0)

def lis_fast(a):
    tails = []                        # tails[k] = 长度为 k+1 的递增子序列里，最小的结尾
    for x in a:
        i = bisect.bisect_left(tails, x)
        if i == len(tails): tails.append(x)
        else: tails[i] = x
    return len(tails)

print("Kadane：", kadane([-2, 1, -3, 4, -1, 2, 1, -5, 4]))
print("LIS：", lis_dp([10, 9, 2, 5, 3, 7, 101, 18]), lis_fast([10, 9, 2, 5, 3, 7, 101, 18]))

# 验证
def kadane_brute(a):
    return max(sum(a[i:j]) for i in range(len(a)) for j in range(i + 1, len(a) + 1))
random.seed(3)
ok = True
for _ in range(500):
    a = [random.randint(-10, 10) for _ in range(random.randint(1, 12))]
    ok &= (kadane(a) == kadane_brute(a))
    ok &= (lis_dp(a) == lis_fast(a))
print("Kadane 与暴力一致、两种 LIS 一致（500 组）：", ok)
''')
