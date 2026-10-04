from runlib import code

# ---------------- 1. 为什么需要函数逼近 ----------------
C_FA = code('''
import numpy as np

# 100 个状态排成一排，起点在 50。每一步等概率跳到左右 1~10 格之内的某一格。
# 跳出左端终止并得到 -1，跳出右端终止并得到 +1，其余奖励为 0，不打折。
N, J = 100, 10
P = np.zeros((N, N)); b = np.zeros(N)
for s in range(N):
    for d in list(range(-J, 0)) + list(range(1, J + 1)):
        t = s + d
        if t < 0: b[s] -= 1 / (2 * J)          # 从左边出界：奖励 -1
        elif t >= N: b[s] += 1 / (2 * J)       # 从右边出界：奖励 +1
        else: P[s, t] += 1 / (2 * J)
v_true = np.linalg.solve(np.eye(N) - P, b)     # 贝尔曼方程 v = b + P v 的精确解
print("v(1) =", round(v_true[0], 3), " v(50) =", round(v_true[49], 3), " v(100) =", round(v_true[99], 3))

def episode(rng):
    s, visited = 49, []                        # 下标从 0 数，49 就是状态 50
    while True:
        visited.append(s)
        s += rng.choice(np.r_[-J:0, 1:J + 1])
        if s < 0: return visited, -1.0
        if s >= N: return visited, 1.0

def run(group, n_ep, alpha, seed):
    rng = np.random.default_rng(seed)
    w = np.zeros(N // group)                   # group=1：查表，每个状态一个数；group=10：10 个相邻状态共用一个数
    errs = {}
    for ep in range(1, n_ep + 1):
        vis, G = episode(rng)                  # 奖励只在终点出现，所以每个访问过的状态的回报 G 都等于终点奖励
        for s in vis:
            g = s // group                     # 这个状态属于哪一组
            w[g] += alpha * (G - w[g])         # 梯度蒙特卡洛：w <- w + alpha * (G - v_hat) * 梯度，而 v_hat 对 w[g] 的梯度是 1
        if ep in (10, 50, 200, 1000):
            v_hat = np.repeat(w, group)
            errs[ep] = float(np.sqrt(np.mean((v_hat - v_true) ** 2)))   # 对全部 100 个状态的均方根误差
    return errs

for group, name in [(1, "查表（100 个参数）"), (10, "状态聚合（10 个参数）")]:
    runs = [run(group, 1000, 0.005, sd) for sd in range(10)]            # 10 个随机种子取平均
    print(name, {ep: round(float(np.mean([r[ep] for r in runs])), 3) for ep in (10, 50, 200, 1000)})
''')

C_BAIRD = code('''
import numpy as np

# Baird 反例：7 个状态、8 个权重的线性价值函数。所有奖励都是 0，所以真实价值处处为 0，
# 而且 w = 0 能精确表示它——也就是说「答案就在函数族里」，算法依然会发散。
X = np.zeros((7, 8))                           # 每个状态的特征向量
for i in range(6):
    X[i, i] = 2; X[i, 7] = 1                   # 状态 1~6：v = 2*w[i] + w[7]
X[6, 6] = 1; X[6, 7] = 2                       # 状态 7：v = w[6] + 2*w[7]
gamma, alpha = 0.99, 0.01
w = np.array([1, 1, 1, 1, 1, 1, 10, 1.0])
rng = np.random.default_rng(0)
s = rng.integers(7)
for t in range(1, 10001):
    # 行为策略：6/7 的概率走「虚线」到状态 1~6 之一，1/7 的概率走「实线」到状态 7
    solid = rng.random() < 1 / 7
    s2 = 6 if solid else rng.integers(6)
    rho = 7.0 if solid else 0.0                # 重要性采样比：我们想评价的目标策略永远走实线
    delta = 0.0 + gamma * X[s2] @ w - X[s] @ w # TD 误差（奖励恒为 0）
    w = w + alpha * rho * delta * X[s]         # 半梯度 off-policy TD(0)：自举 + 函数逼近 + 离策略
    s = s2
    if t in (10, 100, 1000, 5000, 10000):
        print(f"t={t:<6d} max|w| = {np.abs(w).max():.4g}")
''')

# ---------------- 2. DQN ----------------
C_DQN = code('''
import numpy as np

# 小环境：一条 0~1 的连续数轴，从 0.5 出发。动作 0 向左 0.05，动作 1 向右 0.05，带一点噪声。
# 走到 x >= 1 得 +1 并结束，每多走一步罚 0.01，最多走 60 步。最优做法：一路向右，约 10 步。
CENTERS = np.linspace(0, 1, 11)
def phi(x): return np.exp(-((x - CENTERS) / 0.1) ** 2)      # 用 11 个径向基函数把一个数变成 11 维特征
def env_step(x, a, rng):
    x2 = float(np.clip(x + (0.05 if a == 1 else -0.05) + rng.normal(0, 0.01), 0, 1))
    return x2, (1.0 if x2 >= 1 else -0.01), x2 >= 1
GAMMA = 0.95

def evaluate(w, n=50):
    rng = np.random.default_rng(123); tot = []
    for _ in range(n):
        x, G = 0.5, 0.0
        for t in range(60):
            a = int(np.argmax(w @ phi(x)))                  # 评估时完全贪心
            x, r, done = env_step(x, a, rng); G += r
            if done: break
        tot.append(G)
    return round(float(np.mean(tot)), 3)

def train(use_target, use_replay, steps=6000, seed=0):
    rng = np.random.default_rng(seed)
    w = np.zeros((2, 11)); w_target = w.copy()              # Q(x, a) = w[a] . phi(x)，w_target 是「冻结的目标网络」
    buf, x, t_ep, hist = [], 0.5, 0, {}
    for t in range(1, steps + 1):
        eps = max(0.05, 1 - t / 2000)                       # epsilon 从 1 线性降到 0.05
        a = int(rng.integers(2)) if rng.random() < eps else int(np.argmax(w @ phi(x)))
        x2, r, done = env_step(x, a, rng); t_ep += 1
        buf.append((x, a, r, x2, done)); buf = buf[-5000:]  # 经验回放缓冲区，只留最近 5000 条
        if done or t_ep >= 60: x, t_ep = 0.5, 0
        else: x = x2
        # 经验回放：随机抽 32 条旧经验来更新；不用回放就只用刚发生的这一条
        batch = [buf[i] for i in rng.integers(len(buf), size=32)] if use_replay else [buf[-1]]
        for (xs, a_s, rs, xn, dn) in batch:
            w_for_y = w_target if use_target else w         # 目标网络：算 TD 目标用冻结的那份权重
            y = rs + (0 if dn else GAMMA * np.max(w_for_y @ phi(xn)))
            delta = y - w[a_s] @ phi(xs)                    # TD 误差
            w[a_s] += 0.05 * delta * phi(xs)                # 对 (y - Q)^2 / 2 做一步梯度下降，y 当常数
        if use_target and t % 100 == 0: w_target = w.copy() # 每 100 步把在线权重复制给目标网络
        if t in (500, 1000, 2000, 6000): hist[t] = evaluate(w)
    return w, hist

for use_target, use_replay in [(True, True), (False, False)]:
    w, hist = train(use_target, use_replay)
    print("目标网络", use_target, "经验回放", use_replay, "贪心策略的平均回报:", hist)
print("训练后 Q(x, 右) - Q(x, 左) 在 x=0.1,0.3,0.5,0.7,0.9 处:",
      [round(float((w[1] - w[0]) @ phi(x)), 3) for x in (0.1, 0.3, 0.5, 0.7, 0.9)])
''')

C_TDQN = code('''
import numpy as np, torch, torch.nn as nn     # 需要先 pip install torch

torch.manual_seed(0); rng = np.random.default_rng(0)
def env_step(x, a):                            # 和上一段同一个小环境
    x2 = float(np.clip(x + (0.05 if a == 1 else -0.05) + rng.normal(0, 0.01), 0, 1))
    return x2, (1.0 if x2 >= 1 else -0.01), x2 >= 1
def make(): return nn.Sequential(nn.Linear(1, 32), nn.ReLU(), nn.Linear(32, 32), nn.ReLU(), nn.Linear(32, 2))
qnet, target = make(), make()
target.load_state_dict(qnet.state_dict())      # 目标网络从在线网络复制而来
opt = torch.optim.Adam(qnet.parameters(), lr=1e-3)
T = lambda v: torch.tensor(v, dtype=torch.float32)

def evaluate():
    G_all = []
    for _ in range(20):
        x, G = 0.5, 0.0
        for t in range(60):
            a = int(qnet(T([[x]])).argmax()); x, r, d = env_step(x, a); G += r
            if d: break
        G_all.append(G)
    return round(float(np.mean(G_all)), 3)

buf, x, t_ep, gamma = [], 0.5, 0, 0.95
for t in range(1, 3001):
    eps = max(0.05, 1 - t / 1000)
    with torch.no_grad(): greedy = int(qnet(T([[x]])).argmax())
    a = int(rng.integers(2)) if rng.random() < eps else greedy
    x2, r, done = env_step(x, a); t_ep += 1
    buf.append((x, a, r, x2, float(done))); buf = buf[-5000:]
    if done or t_ep >= 60: x, t_ep = 0.5, 0
    else: x = x2
    if len(buf) >= 64:
        xs, as_, rs, xn, dn = map(T, zip(*[buf[i] for i in rng.integers(len(buf), size=64)]))
        with torch.no_grad():                  # TD 目标：用目标网络算，不参与求导
            y = rs + gamma * (1 - dn) * target(xn[:, None]).max(dim=1).values
        pred = qnet(xs[:, None]).gather(1, as_.long()[:, None]).squeeze(1)   # 取出实际做过的动作的 Q 值
        loss = nn.functional.smooth_l1_loss(pred, y)                          # DQN 常用 Huber 损失
        opt.zero_grad(); loss.backward(); opt.step()
    if t % 200 == 0: target.load_state_dict(qnet.state_dict())               # 周期性同步目标网络
    if t in (500, 1000, 2000, 3000): print("步", t, "贪心策略的平均回报:", evaluate())
''')

# ---------------- 3. 策略梯度定理 ----------------
C_SCORE = code('''
import numpy as np

# 三臂老虎机：只有一个状态，拉哪个臂得到 N(mu, 1) 的奖励。策略 pi = softmax(theta)。
MU = np.array([10.0, 10.5, 11.0])
def softmax(z): e = np.exp(z - z.max()); return e / e.sum()
theta = np.array([0.5, 0.0, -0.5]); pi = softmax(theta)

# (1) 精确梯度：J = sum_i pi_i * mu_i，对 softmax 求导得 dJ/dtheta_i = pi_i * (mu_i - J)
J = pi @ MU; exact = pi * (MU - J)
print("pi =", np.round(pi, 4), " J =", round(float(J), 4))
print("精确梯度  :", np.round(exact, 4))

# (2) 有限差分
Jf = lambda th: softmax(th) @ MU
fd = np.array([(Jf(theta + 1e-6 * np.eye(3)[i]) - Jf(theta - 1e-6 * np.eye(3)[i])) / 2e-6 for i in range(3)])
print("有限差分  :", np.round(fd, 4))

# (3) 评分函数（score function）估计：抽 a ~ pi，r ~ N(mu_a, 1)，g = r * grad log pi(a)
# 对 softmax 策略，grad_theta log pi(a) = onehot(a) - pi
rng = np.random.default_rng(0); n = 200000
a = rng.choice(3, size=n, p=pi); r = rng.normal(MU[a], 1.0)
score = np.eye(3)[a] - pi
g = score * r[:, None]
print("MC 估计   :", np.round(g.mean(0), 4), " 标准误:", np.round(g.std(0) / np.sqrt(n), 4))
print("E[score]  :", np.round(score.mean(0), 4), "（理论上是 0，这是基线不改变期望的原因）")
''')

C_VAR = code('''
import numpy as np

MU = np.array([10.0, 10.5, 11.0])
def softmax(z): e = np.exp(z - z.max()); return e / e.sum()
theta = np.array([0.5, 0.0, -0.5]); pi = softmax(theta)
J = pi @ MU
rng = np.random.default_rng(0); n = 200000
a = rng.choice(3, size=n, p=pi); r = rng.normal(MU[a], 1.0)
score = np.eye(3)[a] - pi                      # grad log pi(a)

# 梯度估计量 g = (r - b) * score。b 不依赖动作时期望不变，只有方差不同。
for name, b in [("b = 0", 0.0), ("b = J（平均回报）", float(J))]:
    g = score * (r - b)[:, None]
    print(f"{name:14s} 均值 {np.round(g.mean(0), 3)}  总方差 {g.var(0).sum():.3f}")

# 使总方差最小的常数基线：b* = E[|score|^2 * r] / E[|score|^2]
w2 = (score ** 2).sum(1); b_star = (w2 * r).sum() / w2.sum()
g = score * (r - b_star)[:, None]
print(f"b* = {b_star:.3f}     均值 {np.round(g.mean(0), 3)}  总方差 {g.var(0).sum():.3f}")
print("精确梯度                ", np.round(pi * (MU - J), 3))
''')

C_BANDIT = code('''
import numpy as np

MU = np.array([10.0, 10.5, 11.0, 12.0])        # 四个臂的平均奖励，都是正数，而且差别很小
def softmax(z): e = np.exp(z - z.max()); return e / e.sum()

def run(use_baseline, seed, steps=2000, lr=0.02):
    rng = np.random.default_rng(seed); th = np.zeros(4); b = 0.0; out = {}
    for t in range(1, steps + 1):
        p = softmax(th); a = rng.choice(4, p=p); r = rng.normal(MU[a], 1.0)
        adv = r - (b if use_baseline else 0.0)  # 先用旧基线算优势，再更新基线，所以基线不依赖这一次的动作
        th += lr * adv * (np.eye(4)[a] - p)     # REINFORCE：theta <- theta + lr * (r - b) * grad log pi(a)
        b += 0.05 * (r - b)                     # 基线 = 奖励的滑动平均
        if t in (100, 500, 2000): out[t] = softmax(th)[3]
    return out

for use_baseline in (False, True):
    runs = [run(use_baseline, s) for s in range(30)]   # 30 个随机种子
    curve = {t: round(float(np.mean([r[t] for r in runs])), 3) for t in (100, 500, 2000)}
    bad = sum(r[2000] < 0.5 for r in runs)
    print("有基线" if use_baseline else "无基线", "P(最优臂) 的平均值:", curve, " 2000 步后仍低于 0.5 的种子数:", bad, "/ 30")
''')

# ---------------- 4. REINFORCE / actor-critic（网格世界） ----------------
GRID_ENV = '''
import numpy as np

# 4x4 网格，从左上角 (0,0) 出发，目标是右下角。每走一步奖励 -1，撞墙原地不动，最多走 40 步。
# 最短路径是 6 步，所以最好的策略平均每个回合 6 步。
N = 4; MOVES = [(-1, 0), (1, 0), (0, -1), (0, 1)]       # 上 下 左 右
def step(s, a):
    r, c = divmod(s, N); dr, dc = MOVES[a]
    r = min(max(r + dr, 0), N - 1); c = min(max(c + dc, 0), N - 1)
    s2 = r * N + c
    return s2, -1.0, s2 == N * N - 1
def softmax(z): e = np.exp(z - z.max()); return e / e.sum()
'''

C_REINFORCE = code(GRID_ENV + '''
def reinforce(seed, episodes=600, T=40, lr=0.02):
    rng = np.random.default_rng(seed)
    theta = np.zeros((N * N, 4))                         # 表格式 softmax 策略：每个状态 4 个 logit
    lengths = []
    for ep in range(episodes):
        s, traj = 0, []
        for t in range(T):                               # 1) 用当前策略采样一个完整回合
            p = softmax(theta[s]); a = rng.choice(4, p=p)
            s2, r, done = step(s, a); traj.append((s, a, r)); s = s2
            if done: break
        lengths.append(len(traj))
        G = 0.0; returns = []
        for (_, _, r) in reversed(traj):                 # 2) 从后往前算「未来总回报」G_t（这里不打折）
            G = r + G; returns.append(G)
        returns.reverse()
        for (s_, a_, _), G_t in zip(traj, returns):      # 3) theta <- theta + lr * G_t * grad log pi(a_t | s_t)
            p = softmax(theta[s_])
            theta[s_] += lr * G_t * (np.eye(4)[a_] - p)
    return lengths, theta

L = np.array([reinforce(sd)[0] for sd in range(10)])     # 10 个随机种子
print("回合长度（10 个种子平均）:", {f"{i}-{i+49}": round(float(L[:, i:i + 50].mean()), 1) for i in (0, 100, 250, 550)})
theta = reinforce(0)[1]
arrows = "↑↓←→"
print("种子 0 学到的贪心动作（右下角 G 是终点）：")
for r in range(N):
    print(" ".join("G" if r * N + c == N * N - 1 else arrows[int(np.argmax(theta[r * N + c]))] for c in range(N)))
''')

C_GRID = code(GRID_ENV + '''
def run(method, seed, episodes=600, T=40, lr=0.02, lr_v=0.1):
    rng = np.random.default_rng(seed)
    theta = np.zeros((N * N, 4)); V = np.zeros(N * N); lengths = []
    for ep in range(episodes):
        s, traj = 0, []
        for t in range(T):
            p = softmax(theta[s]); a = rng.choice(4, p=p)
            s2, r, done = step(s, a); traj.append((s, a, r))
            if method == "actor-critic":                  # 单步 actor-critic：每走一步就更新
                delta = r + (0.0 if done else V[s2]) - V[s]       # TD 误差 = 这一步的「优势估计」
                V[s] += lr_v * delta                              # critic：把 V(s) 往 TD 目标推
                theta[s] += lr * delta * (np.eye(4)[a] - p)       # actor：按 delta * grad log pi 更新
            s = s2
            if done: break
        lengths.append(len(traj))
        if method != "actor-critic":                      # 回合结束后再更新（蒙特卡洛回报）
            G = 0.0; returns = []
            for (_, _, r) in reversed(traj):
                G = r + G; returns.append(G)
            returns.reverse()
            for (s_, a_, _), G_t in zip(traj, returns):
                p = softmax(theta[s_])
                if method == "reinforce+baseline":
                    adv = G_t - V[s_]                     # 基线 = 状态价值 V(s)
                    V[s_] += lr_v * (G_t - V[s_])
                else:
                    adv = G_t
                theta[s_] += lr * adv * (np.eye(4)[a_] - p)
    return lengths

print("最后 50 个回合的平均长度（10 个种子，6 是最优），按学习率 lr 对比：")
print("方法                   lr=0.01  lr=0.02  lr=0.05")
for method in ("reinforce", "reinforce+baseline", "actor-critic"):
    row = []
    for lr in (0.01, 0.02, 0.05):
        L = np.array([run(method, sd, lr=lr) for sd in range(10)])
        row.append(round(float(L[:, 550:].mean()), 1))
    print(f"{method:20s}  {row[0]:6.1f}  {row[1]:6.1f}  {row[2]:6.1f}")
''')

# ---------------- 5. PPO ----------------
C_PPO = code('''
import numpy as np

EPS = 0.2
def clip_obj(r, A):                                       # PPO 的裁剪目标：min(r*A, clip(r, 1-eps, 1+eps)*A)
    return np.minimum(r * A, np.clip(r, 1 - EPS, 1 + EPS) * A)
print("ratio   A=+1 时的目标   A=-1 时的目标")
for r in [0.5, 0.8, 1.0, 1.2, 1.5, 2.0]:
    print(f"{r:4.1f}   {clip_obj(r, 1.0):12.3f}   {clip_obj(r, -1.0):12.3f}")

# 同一批数据反复做 300 步梯度上升：对比有没有裁剪时，新策略离旧策略跑了多远
def softmax(z): e = np.exp(z - z.max()); return e / e.sum()
MU = np.array([0.0, 0.5, 1.0])
rng = np.random.default_rng(0)
theta0 = np.zeros(3); pi_old = softmax(theta0)
n = 64
a = rng.choice(3, size=n, p=pi_old); r = rng.normal(MU[a], 1.0)
A = r - r.mean()                                          # 优势：用批内均值当基线
def optimize(clip, steps=300, lr=0.05):
    th = theta0.copy(); out = {}
    for k in range(1, steps + 1):
        p = softmax(th); ratio = p[a] / pi_old[a]
        g = np.zeros(3)
        for i in range(n):
            dead = clip and ((A[i] > 0 and ratio[i] > 1 + EPS) or (A[i] < 0 and ratio[i] < 1 - EPS))
            if not dead:                                  # 被裁剪的样本梯度为 0；否则 grad(ratio*A) = A*ratio*grad log pi
                g += A[i] * ratio[i] * (np.eye(3)[a[i]] - p)
        th += lr * g / n
        if k in (10, 50, 300):
            p = softmax(th)
            out[k] = (round(float(np.abs(p / pi_old - 1).max()), 3), round(float((pi_old * np.log(pi_old / p)).sum()), 4))
    return out, np.round(p, 3)
for clip in (False, True):
    out, p_final = optimize(clip)
    print("有 clip" if clip else "无 clip", "(max|ratio-1|, KL(旧||新)):", out, " 第 300 步的新策略:", p_final)
''')

# ---------------- 6. RLHF 的 KL 正则 ----------------
C_RLHF = code('''
import numpy as np

# 把「语言模型」缩成 4 种回答的老虎机：参考策略 ref（预训练模型）、奖励模型给的分数 rew。
# RLHF 的目标：最大化 E[r] - beta * KL(pi || ref)。理论上最优解是 pi*(a) 正比于 ref(a) * exp(r(a) / beta)。
def softmax(z): e = np.exp(z - z.max()); return e / e.sum()
ref = np.array([0.5, 0.3, 0.15, 0.05])
rew = np.array([0.0, 1.0, 2.0, 3.0])
for beta in (10.0, 1.0, 0.3, 0.05):
    star = ref * np.exp(rew / beta); star /= star.sum()           # 解析解
    th = np.log(ref).copy()                                       # 从参考策略出发做梯度上升
    for _ in range(20000):
        p = softmax(th)
        f = rew - beta * (np.log(p / ref) + 1)                    # 目标对概率 p_i 的偏导
        th += 0.05 * p * (f - p @ f)                              # 通过 softmax 链式法则得到对 logit 的梯度
    p = softmax(th)
    print(f"beta={beta:<5} 解析解 {np.round(star, 3)}  梯度上升 {np.round(p, 3)}  E[r]={float(p @ rew):.3f}  KL={float((p * np.log(p / ref)).sum()):.3f}")
''')

C_TPG = code('''
import torch                                   # 需要先 pip install torch

torch.manual_seed(0)
mu = torch.tensor([10.0, 10.5, 11.0, 12.0])    # 四臂老虎机，和前面的 NumPy 实验同一个问题
logits = torch.zeros(4, requires_grad=True)    # 策略参数：4 个 logit
opt = torch.optim.SGD([logits], lr=0.02)
baseline = 0.0
for step in range(1, 2001):
    dist = torch.distributions.Categorical(logits=logits)
    a = dist.sample((16,))                     # 一批 16 个动作（采样本身不产生梯度）
    r = mu[a] + torch.randn(16)                # 带噪声的奖励
    adv = (r - baseline).detach()              # 优势当常数，不参与求导
    loss = -(dist.log_prob(a) * adv).mean()    # 取负号：优化器是最小化，而我们要最大化 E[adv * log pi]
    opt.zero_grad(); loss.backward(); opt.step()
    baseline = 0.95 * baseline + 0.05 * r.mean().item()
    if step in (1, 100, 500, 2000):
        print("步", step, "策略概率:", torch.softmax(logits, 0).detach().numpy().round(3))
''')
