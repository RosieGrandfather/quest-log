from runlib import code

# 每个代码块都要能独立运行，所以环境的构造代码在每块开头重复一次
BUILD = '''
import numpy as np

# ---- 网格世界的模型：与上一节同一个环境，这次把 P 和 R 完整写成数组 ----
N, A = 5, 4
MOVES = [(-1, 0), (1, 0), (0, -1), (0, 1)]          # 上 下 左 右
GOAL, TRAP, START = (4, 4), (2, 3), (0, 0)
S = N * N
idx = lambda r, c: r * N + c
P = np.zeros((S, A, S))                               # P[s, a, s']：转移概率
R = np.zeros((S, A))                                  # R[s, a]：期望即时奖励
terminal = [idx(*GOAL), idx(*TRAP)]
for r in range(N):
    for c in range(N):
        s = idx(r, c)
        if s in terminal:
            P[s, :, s] = 1.0                          # 终止状态：吸收态，奖励 0
            continue
        for a, (dr, dc) in enumerate(MOVES):
            r2, c2 = min(max(r + dr, 0), N - 1), min(max(c + dc, 0), N - 1)
            P[s, a, idx(r2, c2)] = 1.0                # 这个环境的转移是确定的
            R[s, a] = 10.0 if (r2, c2) == GOAL else (-10.0 if (r2, c2) == TRAP else 0.0)
gamma = 0.9
def show(v, fmt="{:7.3f}"):                           # 把长度 25 的向量按 5x5 打印
    for r in range(N):
        print(" ".join(fmt.format(v[idx(r, c)]) for c in range(N)))
'''

C_EVAL = code(BUILD + '''
# 策略评估：固定策略 pi（随机策略，四个动作各 1/4），反复套用「贝尔曼期望备份」
#   v(s) <- sum_a pi(a|s) * [ R(s,a) + gamma * sum_s' P(s'|s,a) * v(s') ]
pi = np.full((S, A), 0.25)
P_pi = np.einsum("sa,sat->st", pi, P)                 # 策略 + MDP -> 马尔可夫链
r_pi = (pi * R).sum(axis=1)

v = np.zeros(S)                                       # 从全 0 开始
for sweep in range(1, 10000):
    v_new = r_pi + gamma * P_pi @ v                   # 一次「扫描」：同时更新所有状态
    delta = np.abs(v_new - v).max()
    v = v_new
    if sweep in (1, 2, 5, 10, 50):
        print(f"第 {sweep:3d} 次扫描后  最大变化 {delta:.6f}  v(起点)={v[idx(*START)]:.4f}")
    if delta < 1e-10:
        break
print(f"共 {sweep} 次扫描收敛，v_pi(起点) = {v[idx(*START)]:.4f}")
print("v_pi（随机策略，gamma=0.9），终点在右下角 (+10)，陷阱在第 3 行第 4 列 (-10)：")
show(v)

# 另一种解法：v = r_pi + gamma * P_pi v 是线性方程组，(I - gamma*P_pi) v = r_pi，直接解
v_exact = np.linalg.solve(np.eye(S) - gamma * P_pi, r_pi)
print("迭代结果与线性方程组的解一致：", np.allclose(v, v_exact, atol=1e-8))

# 上一节蒙特卡洛估计过 v(起点)（gamma=0.9 时是 -0.822 +- 0.012），这里不玩一局就精确算出来了
# 动作价值：q(s,a) = R(s,a) + gamma * sum_s' P(s'|s,a) v(s')，并验证 v = sum_a pi(a|s) q(s,a)
q = R + gamma * np.einsum("sat,t->sa", P, v)
print("起点的 q（上 下 左 右）:", np.round(q[idx(*START)], 3))
print("v(s) = sum_a pi q 对所有状态成立：", np.allclose((pi * q).sum(axis=1), v))
''')

C_CONTRACT = code(BUILD + '''
# 收缩映射：贝尔曼备份 T(v) = r_pi + gamma * P_pi v 每用一次，两个价值向量之间的最大距离至少缩小 gamma 倍
pi = np.full((S, A), 0.25)
P_pi = np.einsum("sa,sat->st", pi, P)
r_pi = (pi * R).sum(axis=1)
T = lambda v: r_pi + gamma * P_pi @ v
dist = lambda x, y: np.abs(x - y).max()               # 最大范数（无穷范数）

rng = np.random.default_rng(0)
ratios = []
for _ in range(10000):
    v, w = rng.uniform(-100, 100, S), rng.uniform(-100, 100, S)
    ratios.append(dist(T(v), T(w)) / dist(v, w))
print(f"10000 对随机向量：||Tv-Tw|| / ||v-w|| 的最大值 {max(ratios):.4f}，都 <= gamma={gamma}：", max(ratios) <= gamma + 1e-12)

# 极端情形：w 比 v 每个分量都多 5，则 Tw - Tv 每个分量正好多 gamma*5，比值恰好等于 gamma
v = rng.uniform(-100, 100, S)
print("w = v + 5 时比值 =", round(dist(T(v), T(v + 5)) / dist(v, v + 5), 6))

# 最优备份 T*(v)(s) = max_a [R(s,a) + gamma * sum_s' P(s'|s,a) v(s')] 也是收缩映射
Tstar = lambda v: (R + gamma * np.einsum("sat,t->sa", P, v)).max(axis=1)
r2 = max(dist(Tstar(a), Tstar(b)) / dist(a, b) for a, b in (rng.uniform(-100, 100, (2, S)) for _ in range(10000)))
print(f"最优备份：10000 对随机向量的最大比值 {r2:.4f} <= gamma：", r2 <= gamma + 1e-12)

# 因此误差按 gamma^k 的速度几何衰减：||v_k - v_pi|| <= gamma^k ||v_0 - v_pi||
v_pi = np.linalg.solve(np.eye(S) - gamma * P_pi, r_pi)
v = rng.uniform(-100, 100, S)                         # 从一个很坏的初始值出发
e0 = dist(v, v_pi)
print("k    ||v_k - v_pi||    上界 gamma^k * ||v_0 - v_pi||")
for k in range(0, 101):
    if k in (0, 1, 5, 10, 20, 50, 100):
        print(f"{k:<4d} {dist(v, v_pi):14.6g}    {gamma ** k * e0:14.6g}")
    assert dist(v, v_pi) <= gamma ** k * e0 + 1e-9
    v = T(v)
print("每一步都满足上界")
''')

C_VI = code(BUILD + '''
# 价值迭代：每次备份直接取最大值（贝尔曼最优备份），迭代到不动点就得到最优价值 v*
v = np.zeros(S)
for sweep in range(1, 10000):
    q = R + gamma * np.einsum("sat,t->sa", P, v)      # 当前 v 下每个 (s, a) 的价值
    v_new = q.max(axis=1)                             # 贝尔曼最优备份：选最好的动作
    delta = np.abs(v_new - v).max()
    v = v_new
    if delta < 1e-10:
        break
print("价值迭代共", sweep, "次扫描收敛")
print("v*（最优价值，gamma=0.9）：")
show(v)

# 从 v* 读出最优策略：每个状态取 q 最大的动作（可能有并列，全部列出）
q = R + gamma * np.einsum("sat,t->sa", P, v)
arrows = "↑↓←→"
print("最优策略（并列的动作都列出；G=终点，X=陷阱）：")
for r in range(N):
    row = []
    for c in range(N):
        s = idx(r, c)
        if s == idx(*GOAL): row.append("  G ")
        elif s == idx(*TRAP): row.append("  X ")
        else:
            best = np.flatnonzero(q[s] >= q[s].max() - 1e-9)
            row.append(" " + "".join(arrows[a] for a in best).ljust(3))
    print("".join(row))

# 验证：v* 满足贝尔曼最优方程（再备份一次不变）
print("贝尔曼最优方程残差：", float(np.abs(q.max(axis=1) - v).max()))
# 起点离终点 8 步，所以 v*(起点) = 10 * gamma^7
print("v*(起点) =", round(float(v[idx(*START)]), 4), "  10 * 0.9^7 =", round(10 * 0.9 ** 7, 4))
''')

C_PI = code(BUILD + '''
# 策略迭代：(1) 策略评估（这里直接解线性方程组）(2) 策略改进（对 q 取贪心），重复到策略不再变化
def evaluate(policy):                                  # policy[s] 是确定性动作
    P_pi = P[np.arange(S), policy]                     # (S, S)
    r_pi = R[np.arange(S), policy]
    return np.linalg.solve(np.eye(S) - gamma * P_pi, r_pi)

policy = np.zeros(S, dtype=int)                        # 初始策略：处处向上（一个很差的策略）
for it in range(1, 100):
    v = evaluate(policy)                               # 评估
    q = R + gamma * np.einsum("sat,t->sa", P, v)
    new_policy = q.argmax(axis=1)                      # 改进：对当前 q 取贪心
    changed = int((new_policy != policy).sum())
    v0 = round(float(v[idx(*START)]), 4) + 0.0            # 加 0.0 避免打印出 -0.0000
    print(f"第 {it} 轮  v(起点) = {v0:7.4f}  本轮改变了 {changed:2d} 个状态的动作")
    if changed == 0:
        break
    policy = new_policy

# 和价值迭代的结果对比
v_star = np.zeros(S)
for _ in range(2000):
    v_star = (R + gamma * np.einsum("sat,t->sa", P, v_star)).max(axis=1)
print("策略迭代得到的价值 = 价值迭代的 v*：", np.allclose(v, v_star, atol=1e-8))

# 随机对拍：随机生成 20 个 MDP（每个 6 状态 3 动作），两种算法得到同样的最优价值
rng = np.random.default_rng(0)
ok = True
for _ in range(20):
    Pr = rng.dirichlet(np.ones(6), size=(6, 3)); Rr = rng.normal(size=(6, 3)); g = 0.8
    pol = np.zeros(6, dtype=int)
    while True:
        vv = np.linalg.solve(np.eye(6) - g * Pr[np.arange(6), pol], Rr[np.arange(6), pol])
        npol = (Rr + g * np.einsum("sat,t->sa", Pr, vv)).argmax(axis=1)
        if (npol == pol).all(): break
        pol = npol
    vs = np.zeros(6)
    for _ in range(3000): vs = (Rr + g * np.einsum("sat,t->sa", Pr, vs)).max(axis=1)
    ok &= bool(np.allclose(vv, vs, atol=1e-8))
print("20 个随机 MDP 上，策略迭代与价值迭代一致：", ok)
''')

C_HORIZON = code(BUILD + '''
from functools import lru_cache

# 把「最多再走 k 步」当作一个带时间的动态规划：V_k(s) = max_a [ R(s,a) + gamma * sum_s' P(s'|s,a) V_{k-1}(s') ]，V_0 = 0
# 写法一：自底向上制表（k 从 1 到 K 一行一行填）
K = 100
table = np.zeros((K + 1, S))
for k in range(1, K + 1):
    table[k] = (R + gamma * np.einsum("sat,t->sa", P, table[k - 1])).max(axis=1)

# 写法二：自顶向下带记忆化的递归（和 dsa-0 第 11 节的斐波那契、背包是同一类写法）
@lru_cache(maxsize=None)
def V(k, s):
    if k == 0:
        return 0.0
    return max(R[s, a] + gamma * sum(P[s, a, t] * V(k - 1, t) for t in range(S) if P[s, a, t] > 0) for a in range(A))

print("两种写法在 k=30 时一致：", all(abs(V(30, s) - table[30, s]) < 1e-9 for s in range(S)))
v_star = table[K]
print("k    V_k(起点)")
for k in (1, 4, 7, 8, 9, 20, 50, 100):
    print(f"{k:<4d} {table[k, idx(*START)]:.4f}")
print("v*(起点) =", round(float(v_star[idx(*START)]), 4), "，k=100 与 v* 的最大差距：", float(np.abs(table[100] - v_star).max()))
''')
