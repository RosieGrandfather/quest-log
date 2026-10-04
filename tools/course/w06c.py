from runlib import code

C_RING = code('''
import numpy as np

# 一个环形走廊：8 个格子，格子 0、3、5 有「门」，其余是「墙」。机器人只能看到当前格子是门还是墙（观测），
# 而且传感器只有 90% 准确。它看不到自己在哪个格子（状态）。
N = 8
door = np.array([1, 0, 0, 1, 0, 1, 0, 0])
P_OK = 0.9

def likelihood(o):
    """P(观测 o | 每个格子)，长度为 8 的向量"""
    return np.where(door == o, P_OK, 1 - P_OK)

def predict(b):
    """预测一步：动作是「向右走一格」，但会打滑——80% 走 1 格、10% 原地、10% 走 2 格"""
    return 0.8 * np.roll(b, 1) + 0.1 * b + 0.1 * np.roll(b, 2)

def update(b, o):
    """更新：用观测的似然去乘信念，再归一化（贝叶斯公式）"""
    nb = likelihood(o) * b
    return nb / nb.sum()

def entropy(b):
    b = b[b > 0]
    return float(-(b * np.log2(b)).sum())

rng = np.random.default_rng(3)
cell = 0                                   # 真实状态（机器人看不到）
belief = np.ones(N) / N                    # 一开始完全不知道自己在哪
print("t  真实格  观测  信念最大的格  概率   熵(比特)")
for t in range(9):
    if t > 0:                              # 先动（环境按转移概率变化），信念做「预测」
        cell = (cell + rng.choice([1, 0, 2], p=[0.8, 0.1, 0.1])) % N
        belief = predict(belief)
    o = int(rng.random() < (P_OK if door[cell] else 1 - P_OK))   # 再观测，信念做「更新」
    belief = update(belief, o)
    print(f"{t}  {cell:^6d} {'门' if o else '墙'}    {belief.argmax():^10d} {belief.max():6.3f} {entropy(belief):6.3f}")

# 对比：只看当前这一次观测（没有记忆）能做到多准？
print("只看一次观测，在门前的后验：", np.round(update(np.ones(N) / N, 1), 3))
''')

C_RING2 = code('''
import numpy as np
N = 8
door = np.array([1, 0, 0, 1, 0, 1, 0, 0]); P_OK = 0.9
lik = lambda o: np.where(door == o, P_OK, 1 - P_OK)
predict = lambda b: 0.8 * np.roll(b, 1) + 0.1 * b + 0.1 * np.roll(b, 2)
def update(b, o):
    nb = lik(o) * b
    return nb / nb.sum()

# 随机重复 2000 次，每次走 12 步，比较最后一步「用整段历史的信念」和「只看最后一次观测」猜对格子的比例
rng = np.random.default_rng(0)
hit_belief = hit_memoryless = 0
for _ in range(2000):
    cell, b = rng.integers(N), np.ones(N) / N
    for t in range(12):
        if t > 0:
            cell = (cell + rng.choice([1, 0, 2], p=[0.8, 0.1, 0.1])) % N
            b = predict(b)
        o = int(rng.random() < (P_OK if door[cell] else 1 - P_OK))
        b = update(b, o)
    hit_belief += (b.argmax() == cell)
    # 无记忆：最后一次观测 o 对应的所有「可能格子」里随机猜一个
    cands = np.flatnonzero(lik(o) == lik(o).max())
    hit_memoryless += (rng.choice(cands) == cell)
print("用整段历史的信念猜对的比例：", hit_belief / 2000)
print("只看最后一次观测猜对的比例：", hit_memoryless / 2000)
''')

C_HMM = code('''
import numpy as np, itertools

# 隐马尔可夫模型 (HMM)：隐藏状态 0=下雨, 1=晴天；观测 0=带伞, 1=没带伞
pi = np.array([0.5, 0.5])                    # 初始状态分布
A = np.array([[0.7, 0.3],                    # A[i, j] = P(明天是 j | 今天是 i)
              [0.4, 0.6]])
B = np.array([[0.9, 0.1],                    # B[i, k] = P(看到观测 k | 状态是 i)
              [0.2, 0.8]])
obs = [0, 0, 1, 0, 1, 1]                     # 6 天的观测

# 前向算法：alpha[t, i] = P(o_1..o_t, z_t = i)
alpha = np.zeros((len(obs), 2))
alpha[0] = pi * B[:, obs[0]]
for t in range(1, len(obs)):
    alpha[t] = (alpha[t - 1] @ A) * B[:, obs[t]]    # 先「预测」(乘 A)，再「更新」(乘观测似然)
print("前向算法得到的观测序列概率 P(o_1..o_6) =", round(alpha[-1].sum(), 6))

# 对拍：把 2^6 = 64 条隐藏状态路径全部枚举出来，逐条累加联合概率
total = 0.0
for path in itertools.product([0, 1], repeat=len(obs)):
    p = pi[path[0]] * B[path[0], obs[0]]
    for t in range(1, len(obs)):
        p *= A[path[t - 1], path[t]] * B[path[t], obs[t]]
    total += p
print("暴力枚举 64 条路径的结果      =", round(total, 6), " 一致：", np.isclose(total, alpha[-1].sum()))

# 归一化的前向算法 = 滤波：每一步除以总和，得到信念 P(z_t | o_1..o_t)
b = pi * B[:, obs[0]]; b /= b.sum()
print("t=1 信念(下雨, 晴天):", np.round(b, 4))
for t in range(1, len(obs)):
    b = (b @ A) * B[:, obs[t]]; b /= b.sum()
    print(f"t={t + 1} 信念(下雨, 晴天):", np.round(b, 4), " 观测：", "带伞" if obs[t] == 0 else "没带伞")

# 数值问题：序列很长时，不归一化的 alpha 会下溢成 0；归一化版本把每步的缩放系数取对数累加，就稳了
rng = np.random.default_rng(1)
long_obs = rng.integers(0, 2, size=3000)
a = pi * B[:, long_obs[0]]
loglik = 0.0
for o in long_obs[1:]:
    a = (a @ A) * B[:, o]
    s = a.sum(); loglik += np.log(s); a /= s
print("3000 步：不归一化的 alpha 会是 0.0；用缩放系数求得的对数似然 =", round(float(loglik), 2))
raw = pi * B[:, long_obs[0]]
for o in long_obs[1:]:
    raw = (raw @ A) * B[:, o]
print("直接连乘得到的概率 =", raw.sum())
''')

C_KF1 = code('''
import numpy as np

# 一维线性高斯状态空间模型：隐藏状态 z 做随机游走，我们只能看到带噪声的测量值 o
#   z_{t+1} = z_t + w,   w ~ N(0, q)      （动力学噪声）
#   o_t     = z_t + v,   v ~ N(0, r)      （观测噪声）
q, r = 0.05, 1.0
rng = np.random.default_rng(7)
T = 300
z = np.cumsum(rng.normal(0, np.sqrt(q), T))        # 真实状态轨迹
o = z + rng.normal(0, np.sqrt(r), T)               # 带噪声的观测

m, P = 0.0, 10.0                                   # 初始信念 N(m, P)：均值 0，方差很大（很不确定）
est, gains = [], []
for t in range(T):
    # ---- 预测：把信念通过动力学往前推一步，不确定性变大 ----
    m_pred, P_pred = m, P + q
    # ---- 更新：用观测修正，K 是卡尔曼增益（相信观测的程度，在 0 到 1 之间）----
    K = P_pred / (P_pred + r)
    m = m_pred + K * (o[t] - m_pred)               # 均值：朝观测方向挪 K 倍的「新息」
    P = (1 - K) * P_pred                           # 方差：每次更新都会变小
    est.append(m); gains.append(K)
est = np.array(est)

rmse = lambda a, b: float(np.sqrt(np.mean((a - b) ** 2)))
print("直接用观测当估计的 RMSE :", round(rmse(o, z), 4))
print("卡尔曼滤波估计的 RMSE   :", round(rmse(est, z), 4))
w = np.convolve(o, np.ones(5) / 5, mode="full")[:T]   # 对比：滑动平均（窗口 5，只用过去数据）
print("滑动平均(5)的 RMSE      :", round(rmse(w[4:], z[4:]), 4), "（从第 5 步起）")
print("卡尔曼增益 K：第 1 步 %.3f，第 2 步 %.3f，第 50 步 %.3f，第 300 步 %.3f" % (gains[0], gains[1], gains[49], gains[-1]))
print("稳态后验方差 P =", round(P, 4))

# 检验：稳态时 P 满足 P = (1 - K)(P + q)，其中 K = (P + q)/(P + q + r)。直接解这个方程：
Pp = (q + np.sqrt(q * q + 4 * q * r)) / 2          # 稳态的「预测方差」P_pred
print("理论稳态：预测方差 %.4f，增益 K = %.4f，后验方差 %.4f" % (Pp, Pp / (Pp + r), Pp * r / (Pp + r)))

# 检验：一步更新 = 两个高斯按精度（方差的倒数）加权相乘
m0, P0, obs0 = 2.0, 4.0, 5.0
K = P0 / (P0 + r)
print("卡尔曼更新的均值 %.4f，方差 %.4f" % (m0 + K * (obs0 - m0), (1 - K) * P0))
prec = 1 / P0 + 1 / r
print("精度加权的均值   %.4f，方差 %.4f" % ((m0 / P0 + obs0 / r) / prec, 1 / prec))
''')

C_KF2 = code('''
import numpy as np

# 二维状态：z = [位置, 速度]；我们能控制加速度 a，但只能观测到带噪声的位置，速度根本看不见
#   z_{t+1} = A z_t + B a_t + 过程噪声,   o_t = H z_t + 观测噪声
A = np.array([[1.0, 1.0], [0.0, 1.0]])
B = np.array([0.5, 1.0])
H = np.array([[1.0, 0.0]])
Q = np.diag([0.01, 0.01])            # 过程噪声协方差
R = np.array([[4.0]])                # 观测噪声方差（标准差 2，噪声很大）

rng = np.random.default_rng(11)
T = 200
a = rng.normal(0, 0.3, T)            # 已知的控制输入（动作）
z = np.zeros((T, 2)); o = np.zeros(T)
state = np.array([0.0, 1.0])
for t in range(T):
    z[t] = state
    o[t] = state[0] + rng.normal(0, 2.0)
    state = A @ state + B * a[t] + rng.multivariate_normal([0, 0], Q)

m = np.array([0.0, 0.0]); P = np.eye(2) * 10      # 初始信念：均值和协方差矩阵
est = np.zeros((T, 2))
for t in range(T):
    # 更新：先用当前观测修正（第 t 步的信念以 o_0..o_t 为条件）
    S = H @ P @ H.T + R                            # 新息协方差
    K = P @ H.T @ np.linalg.inv(S)                 # 卡尔曼增益，2x1 矩阵
    m = m + (K @ (o[t] - H @ m)).ravel()
    P = (np.eye(2) - K @ H) @ P
    est[t] = m
    # 预测：用动力学和已知动作把信念推到下一步
    m = A @ m + B * a[t]
    P = A @ P @ A.T + Q

rmse = lambda x, y: float(np.sqrt(np.mean((x - y) ** 2)))
print("位置：直接用观测 RMSE =", round(rmse(o, z[:, 0]), 3), "  卡尔曼 RMSE =", round(rmse(est[:, 0], z[:, 0]), 3))
naive_v = np.diff(o, prepend=o[0])                 # 速度的朴素估计：相邻观测之差
print("速度：观测差分 RMSE   =", round(rmse(naive_v, z[:, 1]), 3), "  卡尔曼 RMSE =", round(rmse(est[:, 1], z[:, 1]), 3))
print("稳态后验协方差对角线（位置方差，速度方差）:", np.round(np.diag(P), 3))
''')

C_GRU = code('''
import numpy as np

sigmoid = lambda x: 1 / (1 + np.exp(-x))
rng = np.random.default_rng(5)
d_in, d_h = 2, 3
# 三组参数：更新门 z、重置门 r、候选状态 n；每组有 W（输入）、U（隐状态）、b（偏置）
Wz, Uz, bz = rng.normal(0, 0.8, (d_h, d_in)), rng.normal(0, 0.8, (d_h, d_h)), np.zeros(d_h)
Wr, Ur, br = rng.normal(0, 0.8, (d_h, d_in)), rng.normal(0, 0.8, (d_h, d_h)), np.zeros(d_h)
Wn, Un, bn = rng.normal(0, 0.8, (d_h, d_in)), rng.normal(0, 0.8, (d_h, d_h)), np.zeros(d_h)

def gru_step(x, h):
    z = sigmoid(Wz @ x + Uz @ h + bz)            # 更新门：越接近 1 越保留旧状态
    r = sigmoid(Wr @ x + Ur @ h + br)            # 重置门：决定算候选状态时用多少旧状态
    n = np.tanh(Wn @ x + Un @ (r * h) + bn)      # 候选新状态
    return (1 - z) * n + z * h, z, r, n          # 新状态 = 新旧两种状态的逐元素加权平均

x = np.array([1.0, -1.0]); h = np.array([0.5, -0.5, 0.0])
h_new, z, r, n = gru_step(x, h)
print("更新门 z =", np.round(z, 4)); print("重置门 r =", np.round(r, 4)); print("候选 n   =", np.round(n, 4))
print("新隐状态 h' =", np.round(h_new, 4))

# 手算核对第 0 维：全部用标量乘加，不用矩阵乘法
z0 = sigmoid(sum(Wz[0, j] * x[j] for j in range(d_in)) + sum(Uz[0, j] * h[j] for j in range(d_h)))
r_all = [sigmoid(sum(Wr[i, j] * x[j] for j in range(d_in)) + sum(Ur[i, j] * h[j] for j in range(d_h))) for i in range(d_h)]
n0 = np.tanh(sum(Wn[0, j] * x[j] for j in range(d_in)) + sum(Un[0, j] * r_all[j] * h[j] for j in range(d_h)))
print("第 0 维手算 h'[0] =", round((1 - z0) * n0 + z0 * h[0], 4), " 与矩阵版一致：", np.isclose((1 - z0) * n0 + z0 * h[0], h_new[0]))

# 更新门的作用：把偏置 bz 调到很大（z 接近 1）= 几乎不更新；调到很小（z 接近 0）= 完全用新状态覆盖
for name, bias in [("z 偏大 (bz=+8)", 8.0), ("z 偏小 (bz=-8)", -8.0)]:
    bz[:] = bias
    hh = np.array([0.5, -0.5, 0.0])
    for t in range(5):
        hh, *_ = gru_step(rng.normal(0, 1, d_in), hh)
    print(name, "：喂 5 个随机输入后 h =", np.round(hh, 3))
''')

C_RES = code('''
import numpy as np

# 实验：隐状态能不能装下「历史」？还是用环形走廊（观测只有门/墙，动作永远是向右走），
# 用一个随机权重的 GRU 当「编码器」，只训练最后一层线性读出，看能否从隐状态猜出真实格子。
sigmoid = lambda x: 1 / (1 + np.exp(-x))
N, P_OK = 8, 0.9
door = np.array([1, 0, 0, 1, 0, 1, 0, 0])
rng = np.random.default_rng(0)
d_in, d_h = 2, 64
Wz, Wr, Wn = [rng.normal(0, 1.0, (d_h, d_in)) for _ in range(3)]
Uz, Ur, Un = [rng.normal(0, 1.0 / np.sqrt(d_h), (d_h, d_h)) for _ in range(3)]
bz, br, bn = np.zeros(d_h), np.zeros(d_h), np.zeros(d_h)

def gru_step(x, h):
    z = sigmoid(Wz @ x + Uz @ h + bz); r = sigmoid(Wr @ x + Ur @ h + br)
    n = np.tanh(Wn @ x + Un @ (r * h) + bn)
    return (1 - z) * n + z * h

def episode(T=20):
    cell = rng.integers(N); h = np.zeros(d_h); xs, hs, cells = [], [], []
    for t in range(T):
        if t > 0: cell = (cell + rng.choice([1, 0, 2], p=[0.8, 0.1, 0.1])) % N
        o = int(rng.random() < (P_OK if door[cell] else 1 - P_OK))
        x = np.eye(2)[o]; h = gru_step(x, h)
        xs.append(x); hs.append(h.copy()); cells.append(cell)
    return np.array(xs), np.array(hs), np.array(cells)

def dataset(n):
    X, Hs, Y = [], [], []
    for _ in range(n):
        xs, hs, c = episode(); X += list(xs[5:]); Hs += list(hs[5:]); Y += list(c[5:])   # 丢掉前 5 步的预热期
    return np.array(X), np.array(Hs), np.array(Y)

Xtr, Htr, Ytr = dataset(300); Xte, Hte, Yte = dataset(100)

def ridge_readout(F, Y, lam=1e-2):                  # 最小二乘线性读出（岭回归），目标是格子的独热编码
    F1 = np.c_[F, np.ones(len(F))]
    return np.linalg.solve(F1.T @ F1 + lam * np.eye(F1.shape[1]), F1.T @ np.eye(N)[Y])

def acc(F, Y, W): return float(((np.c_[F, np.ones(len(F))] @ W).argmax(1) == Y).mean())

print("随机猜（1/8）:", 1 / N)
print("只用当前观测做特征 :", round(acc(Xte, Yte, ridge_readout(Xtr, Ytr)), 3))
print("用 GRU 隐状态做特征:", round(acc(Hte, Yte, ridge_readout(Htr, Ytr)), 3))
''')

C_LAT = code('''
import numpy as np

# 潜在动力学模型：p(z_{t+1} | z_t, a_t)。这里是一个一维、非线性、带噪声的例子，
# 同样的起点和动作序列，每次采样出来的未来都不同：它描述的是一个「分布」，不是一个确定的数。
rng = np.random.default_rng(0)
def step(z, a, noise=0.1):
    return z + 0.5 * np.sin(z) + a + noise * rng.normal(size=z.shape)

def rollout(actions, n=5000, z0=0.0):
    z = np.full(n, z0)
    for a in actions:
        z = step(z, a)
    return z

for name, acts in [("动作 (+0.3, +0.3, +0.3)", [0.3] * 3), ("动作 (-0.3, -0.3, -0.3)", [-0.3] * 3)]:
    z3 = rollout(acts)
    print(f"{name}: 3 步后 z 的均值 {z3.mean():+.3f}，标准差 {z3.std():.3f}")

# 观测模型 p(o | z)：潜变量到观测的「渲染」。这里 o = 2z + 噪声，由模型把观测和潜变量连起来
z3 = rollout([0.3] * 3, n=5)
print("5 个采样的潜变量 z_3 :", np.round(z3, 3))
print("对应的观测样本 o_3   :", np.round(2 * z3 + 0.2 * rng.normal(size=5), 3))
''')
