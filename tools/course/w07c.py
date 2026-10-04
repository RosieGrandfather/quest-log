from runlib import code

C_DYNA = code('''
import numpy as np
from collections import deque

# 6x9 的迷宫格子世界：从 S 走到 G，每一步 0 奖励，到达 G 奖励 1；撞墙原地不动
ROWS, COLS = 6, 9
WALLS = {(1, 2), (2, 2), (3, 2), (4, 5), (0, 7), (1, 7), (2, 7)}
START, GOAL = (2, 0), (0, 8)
MOVES = [(-1, 0), (1, 0), (0, -1), (0, 1)]          # 上、下、左、右

def env_step(s, a):
    r, c = s[0] + MOVES[a][0], s[1] + MOVES[a][1]
    if not (0 <= r < ROWS and 0 <= c < COLS) or (r, c) in WALLS:
        r, c = s
    return (r, c), (1.0 if (r, c) == GOAL else 0.0), (r, c) == GOAL

# 用广度优先搜索算出真正的最短路长度，作为参照
dist = {START: 0}; dq = deque([START])
while dq:
    s = dq.popleft()
    for a in range(4):
        s2, _, _ = env_step(s, a)
        if s2 not in dist: dist[s2] = dist[s] + 1; dq.append(s2)
print("最短路径长度 =", dist[GOAL], "步")

def run(n_plan, seed, episodes=30, alpha=0.1, gamma=0.95, eps=0.1):
    """n_plan = 每走一步真实环境后，额外做多少次「想象」更新。n_plan=0 就是普通 Q-learning"""
    rng = np.random.default_rng(seed)
    Q = np.zeros((ROWS, COLS, 4)); model = {}; steps_per_ep = []
    for ep in range(episodes):
        s, steps = START, 0
        while True:
            a = rng.integers(4) if rng.random() < eps else int(rng.choice(np.flatnonzero(Q[s] == Q[s].max())))
            s2, r, done = env_step(s, a)                         # 真实交互 1 次
            Q[s][a] += alpha * (r + (0 if done else gamma * Q[s2].max()) - Q[s][a])      # 直接强化学习
            model[(s, a)] = (s2, r, done)                       # 模型学习：记下「在 s 做 a 会到哪」（环境是确定的）
            keys = list(model.keys())
            for _ in range(n_plan):                             # 规划：从学到的模型里随机抽旧经验，再做同样的 Q 更新
                (ps, pa) = keys[rng.integers(len(keys))]
                ps2, pr, pd = model[(ps, pa)]
                Q[ps][pa] += alpha * (pr + (0 if pd else gamma * Q[ps2].max()) - Q[ps][pa])
            s, steps = s2, steps + 1
            if done or steps > 2000: break
        steps_per_ep.append(steps)
    return np.array(steps_per_ep)

show = [0, 1, 2, 4, 9, 19, 29]
print("每个回合到达终点用的步数（10 个随机种子的平均），回合序号：", [i + 1 for i in show])
for n in [0, 5, 50]:
    res = np.mean([run(n, seed) for seed in range(10)], axis=0)
    print(f"n_plan={n:<3d}", np.round(res[show], 1), " 30 回合总共走的真实步数 =", int(res.sum()))
''')

C_PLAN = code('''
import numpy as np

# 一维点质量，状态 (位置 x, 速度 v)，动作是推力 a（限制在 [-1, 1]），带阻力。目标：回到 x=0 并停下
dt = 0.1
def dynamics(x, v, a, mass=1.0, wind=0.0):
    v2 = v + dt * ((a - 0.3 * v) / mass + wind)
    return x + dt * v2, v2
step_cost = lambda x, v, a: x ** 2 + 0.1 * v ** 2 + 0.01 * a ** 2

def rollout_cost(x0, v0, A, model):
    """A 的形状是 (候选数 N, 时长 H)：用模型把 N 条动作序列同时「想象」一遍，返回各自的总代价"""
    N, H = A.shape
    x, v, J = np.full(N, x0), np.full(N, v0), np.zeros(N)
    for h in range(H):
        x, v = model(x, v, A[:, h]); J += step_cost(x, v, A[:, h])
    return J

def plan(x0, v0, model, rng, H=15, N=200, method="shoot", iters=5, elite=20):
    if method == "shoot":                                   # 随机射击：随机抽 N 条，选最好的
        A = rng.uniform(-1, 1, (N, H)); J = rollout_cost(x0, v0, A, model); i = J.argmin()
        return A[i], J[i]
    mu, sd = np.zeros(H), np.ones(H) * 0.7                  # CEM：反复「抽样 → 选精英 → 用精英重新拟合高斯」
    for _ in range(iters):
        A = np.clip(mu + sd * rng.normal(size=(N, H)), -1, 1)
        idx = np.argsort(rollout_cost(x0, v0, A, model))[:elite]
        mu, sd = A[idx].mean(0), A[idx].std(0) + 1e-3
    return mu, rollout_cost(x0, v0, mu[None, :], model)[0]

# 1) 同样的模型、同样的预算（每次约 200 条候选），计划的质量
for m in ["shoot", "cem"]:
    best = [plan(1.0, 0.0, dynamics, np.random.default_rng(s), method=m)[1] for s in range(20)]
    print(f"{m:5s} 找到的计划在模型里的代价（越低越好，20 次平均）：{np.mean(best):.2f}")

# 2) 开环 vs 滚动重规划(MPC)。「真实世界」和模型不一样：质量是 1.5（模型以为是 1.0），还有一股持续的风
world = {"模型完全正确": lambda x, v, a: dynamics(x, v, a),
         "模型有误差  ": lambda x, v, a: dynamics(x, v, a, mass=1.5, wind=-0.15)}
def execute(method, mode, w, seed, T=60):
    rng = np.random.default_rng(seed); x, v, tot = 1.0, 0.0, 0.0
    if mode == "开环": A, _ = plan(x, v, dynamics, rng, H=T, N=300, method=method, iters=8)   # 一次规划完整个 60 步，之后闭眼执行
    for t in range(T):
        if mode == "开环": a = A[t]
        else: a = plan(x, v, dynamics, rng, H=15, method=method)[0][0]          # MPC：每一步都重新规划，只执行第一个动作
        xa, va = world[w](np.array([x]), np.array([v]), np.array([a])); x, v = float(xa[0]), float(va[0])
        tot += step_cost(x, v, a)
    return tot
print("60 步总代价（10 个种子平均）：")
for method in ["shoot", "cem"]:
    for mode in ["开环", "MPC"]:
        print(f"  {method:5s} {mode:3s}", "  ".join(f"{w}: {np.mean([execute(method, mode, w, s) for s in range(10)]):6.2f}" for w in world))
''')

C_ERR = code('''
import numpy as np

# 累积误差的最小模型：真实系统 x_{k+1} = a x_k，学到的模型 x_{k+1} = (a + 0.02) x_k，
# 每一步的误差只有 0.02 倍的状态，看看多步滚动之后差多少
x0 = 1.0
print("步数 k        :", [1, 5, 10, 20, 50])
for a in [0.9, 1.0, 1.1]:
    errs = [abs(a ** k - (a + 0.02) ** k) * x0 for k in [1, 5, 10, 20, 50]]
    print(f"a={a:<4}  |误差|  :", [round(e, 4) for e in errs])

# 递推：误差 e_{k+1} = a e_k + 0.02 x_k。a>1 时旧误差被放大，a<1 时被衰减
for a in [0.9, 1.1]:
    x, e = x0, 0.0
    for k in range(20):
        e = a * e + 0.02 * x; x = a * x
    print(f"a={a}: 20 步后的绝对误差 {e:.4f}，相对误差 {e / x:.4f}")
''')

_FIT_HEAD = '''
import numpy as np, time
# 「真实世界」：一个带阻尼的单摆，状态 s=(角度 th, 角速度 om)，动作 a 是力矩。我们把它当黑箱，只用它产生数据
dt, AMAX = 0.05, 8.0
def pend(s, a):
    th, om = s[..., 0], s[..., 1]
    om2 = om + dt * (-9.8 * np.sin(th) - 0.1 * om + a)
    return np.stack([th + dt * om2, om2], -1)

rng = np.random.default_rng(0)
def collect(n):                              # 在状态空间里随机撒点、随机施加动作，记录 (s, a, s')
    S = np.c_[rng.uniform(-2.5, 2.5, n), rng.uniform(-5, 5, n)]
    A = rng.uniform(-AMAX, AMAX, n)
    return S, A, pend(S, A)

def fit_linear(S, A, S2):                    # 线性模型：s' - s = [s, a, 1] @ W，用最小二乘解
    W = np.linalg.lstsq(np.c_[S, A, np.ones(len(S))], S2 - S, rcond=None)[0]
    return lambda s, a: s + np.c_[s, a, np.ones(len(s))] @ W

def fit_mlp(S, A, S2, h=48, epochs=2000, lr=3e-3, seed=1):   # 两层 tanh 网络，预测 s' - s；手写反向传播 + Adam
    X, Y = np.c_[S, A], S2 - S
    mu, sd, ysd = X.mean(0), X.std(0), Y.std(0); Xn, Yn = (X - mu) / sd, Y / ysd
    r = np.random.default_rng(seed)
    P = [r.normal(0, 1 / np.sqrt(3), (3, h)), np.zeros(h), r.normal(0, 1 / np.sqrt(h), (h, h)), np.zeros(h),
         r.normal(0, 1 / np.sqrt(h), (h, 2)), np.zeros(2)]
    def fwd(Xn):
        h1 = np.tanh(Xn @ P[0] + P[1]); h2 = np.tanh(h1 @ P[2] + P[3]); return h1, h2, h2 @ P[4] + P[5]
    m = [np.zeros_like(p) for p in P]; v = [np.zeros_like(p) for p in P]
    for ep in range(1, epochs + 1):
        h1, h2, out = fwd(Xn); d = 2 * (out - Yn) / len(Xn)          # 均方误差的梯度
        dh2 = (d @ P[4].T) * (1 - h2 ** 2); dh1 = (dh2 @ P[2].T) * (1 - h1 ** 2)
        G = [Xn.T @ dh1, dh1.sum(0), h1.T @ dh2, dh2.sum(0), h2.T @ d, d.sum(0)]
        for i in range(6):
            m[i] = 0.9 * m[i] + 0.1 * G[i]; v[i] = 0.999 * v[i] + 0.001 * G[i] ** 2
            P[i] -= lr * (m[i] / (1 - 0.9 ** ep)) / (np.sqrt(v[i] / (1 - 0.999 ** ep)) + 1e-8)
    return lambda s, a: s + fwd((np.c_[s, a] - mu) / sd)[2] * ysd

S, A, S2 = collect(5000)
models = {"线性(5000 条)": fit_linear(S, A, S2),
          "小网络(200 条)": fit_mlp(S[:200], A[:200], S2[:200]),
          "小网络(5000 条)": fit_mlp(S, A, S2)}
'''

C_FIT = code(_FIT_HEAD + '''
# 评估：从 500 个没见过的初始状态出发，施加同一串随机动作，比较「真实世界」和「模型」的多步滚动
Ste = np.c_[rng.uniform(-2, 2, 500), rng.uniform(-3, 3, 500)]
Ate = rng.uniform(-AMAX, AMAX, (500, 50))
def rollout_error(model):
    st, sm, errs = Ste.copy(), Ste.copy(), []
    for k in range(50):
        st = pend(st, Ate[:, k]); sm = model(sm, Ate[:, k])           # 模型从自己上一步的输出继续滚动（不再回到真实状态）
        errs.append(np.sqrt(((st - sm) ** 2).sum(1).mean()))
    return np.array(errs)
ks = [0, 2, 4, 9, 19, 49]
print("滚动步数 k            :", [k + 1 for k in ks])
for name, mod in models.items():
    print(f"{name:14s} 误差(RMS) :", np.round(rollout_error(mod)[ks], 4))

# 为什么 50 步时「小网络(5000 条)」的 RMS 误差忽然跳到 0.5？拆开看：区分「滚动中真实状态是否离开过训练数据的范围」
st, sm, left = Ste.copy(), Ste.copy(), np.zeros(500, bool)
for k in range(50):
    st = pend(st, Ate[:, k]); sm = models["小网络(5000 条)"](sm, Ate[:, k])
    left |= (np.abs(st[:, 0]) > 2.5) | (np.abs(st[:, 1]) > 5)      # 训练数据覆盖 th 在 +-2.5、om 在 +-5 之内
e = np.sqrt(((st - sm) ** 2).sum(1))
print("第 50 步：误差中位数 %.4f；离开过训练范围的轨迹占 %.1f%%" % (np.median(e), 100 * left.mean()))
print("  没离开范围的轨迹 RMS = %.4f；离开过的轨迹 RMS = %.4f" % (np.sqrt((e[~left] ** 2).mean()), np.sqrt((e[left] ** 2).mean())))
''')

C_CTRL = code(_FIT_HEAD + '''
# 用这三个模型来控制真实的单摆：把它从 th=-0.5 推到 th=0.6 并保持，用 CEM 规划
TARGET = 0.6
cost = lambda s, a: (s[..., 0] - TARGET) ** 2 + 0.05 * s[..., 1] ** 2 + 0.001 * a ** 2

def cem(s0, model, r, H=10, N=100, iters=3, elite=10):
    mu, sd = np.zeros(H), np.ones(H) * AMAX / 2
    for _ in range(iters):
        Aseq = np.clip(mu + sd * r.normal(size=(N, H)), -AMAX, AMAX); s = np.tile(s0, (N, 1)); J = np.zeros(N)
        for h in range(H): s = model(s, Aseq[:, h]); J += cost(s, Aseq[:, h])
        idx = np.argsort(J)[:elite]; mu, sd = Aseq[idx].mean(0), Aseq[idx].std(0) + 1e-3
    return mu

def mpc_episode(model, seed, T=40):                 # 每一步重新规划，只执行第一个动作
    r = np.random.default_rng(seed); s = np.array([-0.5, 0.0]); tot = 0.0
    for t in range(T):
        a = r.uniform(-AMAX, AMAX) if model is None else cem(s, model, r)[0]
        s = pend(s, a); tot += cost(s, a)
    return tot

def open_loop_episode(model, seed, T=40):           # 只在开头规划一次完整的 40 步，然后闭眼执行
    r = np.random.default_rng(seed); s0 = np.array([-0.5, 0.0]); mu, sd = np.zeros(T), np.ones(T) * AMAX / 2
    for _ in range(6):
        Aseq = np.clip(mu + sd * r.normal(size=(200, T)), -AMAX, AMAX); s = np.tile(s0, (200, 1)); J = np.zeros(200)
        for h in range(T): s = model(s, Aseq[:, h]); J += cost(s, Aseq[:, h])
        idx = np.argsort(J)[:20]; mu, sd = Aseq[idx].mean(0), Aseq[idx].std(0) + 1e-3
    s, tot = s0.copy(), 0.0
    for t in range(T): s = pend(s, mu[t]); tot += cost(s, mu[t])
    return tot

print("随机动作的总代价      :", round(float(np.mean([mpc_episode(None, sd) for sd in range(5)])), 2))
print("模型              MPC    开环（40 步总代价，越低越好）")
for name, mod in [("真实动力学", pend)] + list(models.items()):
    m = np.mean([mpc_episode(mod, sd) for sd in range(5)]); o = np.mean([open_loop_episode(mod, sd) for sd in range(5)])
    print(f"{name:14s} {m:6.2f} {o:7.2f}")
''')

C_BRANCH = code(_FIT_HEAD.replace("S, A, S2 = collect(5000)", "S, A, S2 = collect(200)") .replace('''models = {"线性(5000 条)": fit_linear(S, A, S2),
          "小网络(200 条)": fit_mlp(S[:200], A[:200], S2[:200]),
          "小网络(5000 条)": fit_mlp(S, A, S2)}''', "model = fit_mlp(S, A, S2)") + '''
# 「想象」预算固定为 500 条合成转移：(a) 从 100 个真实状态出发各滚动 5 步；(b) 从 10 个真实状态出发各滚动 50 步
# 度量：每条合成转移 (s, a) -> s'_模型 与真实 s'_真 的距离，以及模型所处的状态偏离「真实轨迹」多远
def imagine(n_start, length, seed=3):
    r = np.random.default_rng(seed)
    s_real = np.c_[r.uniform(-2, 2, n_start), r.uniform(-3, 3, n_start)]      # 来自真实数据分布的起点
    s_img = s_real.copy(); trans_err, drift = [], []
    for k in range(length):
        a = r.uniform(-AMAX, AMAX, n_start)
        s_next_model = model(s_img, a)
        trans_err.append(np.sqrt(((s_next_model - pend(s_img, a)) ** 2).sum(1)))   # 在「想象出来的状态」上，模型这一步错多少
        s_real = pend(s_real, a); s_img = s_next_model
        drift.append(np.sqrt(((s_img - s_real) ** 2).sum(1)))                       # 想象轨迹偏离真实轨迹多少
    return float(np.concatenate(trans_err).mean()), float(np.concatenate(drift).mean())

for n_start, length in [(100, 5), (10, 50)]:
    te, dr = imagine(n_start, length)
    print(f"{n_start:3d} 个起点 x 滚动 {length:2d} 步（共 {n_start * length} 条）：单步误差均值 {te:.4f}，偏离真实轨迹均值 {dr:.4f}")
''')
