from runlib import code

C_EPS = code('''
import numpy as np

# ε-贪心 (epsilon-greedy)：以概率 1-eps 选当前估计最好的动作（利用），以概率 eps 随机选一个动作（探索）
def eps_greedy_probs(q, eps):
    p = np.full(len(q), eps / len(q))          # 每个动作都有 eps/|A| 的基础概率
    p[int(np.argmax(q))] += 1 - eps            # 当前最好的动作再加 1-eps
    return p
print("q=[1, 3, 2, 0]，eps=0.1 时选择概率：", eps_greedy_probs(np.array([1., 3., 2., 0.]), 0.1))
print("eps=0.4 时                        ：", eps_greedy_probs(np.array([1., 3., 2., 0.]), 0.4))

# 实验：10 臂老虎机。每个臂的真实平均奖励不同、但智能体不知道；每次拉一个臂，得到均值 + 噪声
def run(eps, steps=1000, runs=500, seed=0):
    rng = np.random.default_rng(seed)
    total = np.zeros(steps); best = 0
    for _ in range(runs):
        true = rng.normal(0, 1, 10)            # 10 个臂的真实均值
        Q = np.zeros(10); N = np.zeros(10)     # 估计值与拉动次数（样本平均）
        for t in range(steps):
            a = int(rng.integers(10)) if rng.random() < eps else int(np.argmax(Q))
            r = rng.normal(true[a], 1)
            N[a] += 1; Q[a] += (r - Q[a]) / N[a]   # 增量式样本平均：Q <- Q + (r - Q)/N
            total[t] += r
        best += true.max()
    return total / runs, best / runs
print("eps    前 100 步平均奖励   最后 500 步平均奖励   （最优臂的平均奖励 ≈ 1.5 左右）")
for eps in [0.0, 0.01, 0.1, 0.3]:
    avg, best = run(eps)
    print(f"{eps:<5}  {avg[:100].mean():10.3f}        {avg[500:].mean():10.3f}        最优臂均值 {best:.3f}")
''')

C_PRED = code('''
import numpy as np

# 5 状态随机游走（A B C D E，从 C 出发）：每步等概率向左或向右，走出左端奖励 0，走出右端奖励 +1，gamma = 1
# 真实价值 v = (1/6, 2/6, 3/6, 4/6, 5/6)。目标：只靠交互样本估计 v（无模型预测）
TRUE = np.arange(1, 6) / 6
rng = np.random.default_rng(0)

def episode():
    """返回 (状态序列, 奖励序列)，状态用 0..4 表示；奖励只在结束时是 0 或 1"""
    s, states = 2, []
    while True:
        states.append(s)
        s += 1 if rng.random() < 0.5 else -1
        if s < 0: return states, 0.0          # 走出左端
        if s > 4: return states, 1.0          # 走出右端

def mc_update(V, alpha, states, G):
    # 蒙特卡洛（首次访问）：等整局结束，每个状态用整局的回报 G 做目标：V(s) <- V(s) + alpha * (G - V(s))
    seen = set()
    for s in states:
        if s not in seen:
            seen.add(s); V[s] += alpha * (G - V[s])

def td_update(V, alpha, states, G):
    # TD(0)：每走一步就更新，目标是 r + gamma * V(下一状态)（用下一状态当前的估计，即自举）
    for i, s in enumerate(states):
        if i + 1 < len(states): target = 0.0 + V[states[i + 1]]
        else: target = G                       # 最后一步：走出边界，下一状态价值为 0，奖励为 G
        V[s] += alpha * (target - V[s])

def rms_curve(update, alpha, episodes=100, runs=200):
    err = np.zeros(episodes + 1)
    for _ in range(runs):
        V = np.full(5, 0.5)                    # 初始值全设成 0.5
        err[0] += np.sqrt(((V - TRUE) ** 2).mean())
        for e in range(1, episodes + 1):
            states, G = episode(); update(V, alpha, states, G)
            err[e] += np.sqrt(((V - TRUE) ** 2).mean())
    return err / runs

print("方法            alpha   第10局  第30局  第100局 的 RMS 误差（200 次独立运行的平均）")
for name, upd, alphas in [("TD(0)", td_update, [0.05, 0.1, 0.15]), ("蒙特卡洛", mc_update, [0.01, 0.02, 0.04])]:
    for a in alphas:
        c = rms_curve(upd, a)
        print(f"{name:<9s}     {a:<6}  {c[10]:.3f}   {c[30]:.3f}   {c[100]:.3f}")
''')

C_BIASVAR = code('''
import numpy as np

# 偏差与方差：同样是估计 v(s)，蒙特卡洛的目标是整局回报 G，TD 的目标是 r + V(下一状态)
# 在 5 状态随机游走里，对 B、C、D、E 各采样 20 万次，比较两种目标的均值（偏差）和方差
TRUE = np.arange(1, 6) / 6
rng = np.random.default_rng(1)
n = 200000
V_wrong = np.full(5, 0.5)                      # 一个不准的价值估计：处处 0.5
V_right = TRUE.copy()                          # 一个完全准确的估计

def sample(s0, V):
    """从 s0 出发采样一次，返回 (MC 目标 G, TD 目标 r + V(s'))"""
    s, first = s0, True
    td = None
    while True:
        s2 = s + (1 if rng.random() < 0.5 else -1)
        r = 1.0 if s2 > 4 else 0.0
        if first:
            td = r + (V[s2] if 0 <= s2 <= 4 else 0.0)
            first = False
        if s2 < 0 or s2 > 4:
            return r, td
        s = s2

print("状态  真实v   MC目标: 均值  方差    TD目标(V准确): 均值  方差    TD目标(V处处0.5): 均值  方差")
for s0 in [1, 2, 3, 4]:
    out = np.array([sample(s0, V_right) for _ in range(n // 4)])
    bad = np.array([sample(s0, V_wrong)[1] for _ in range(n // 4)])
    print(f"{'ABCDE'[s0]}     {TRUE[s0]:.3f}   {out[:,0].mean():.3f}  {out[:,0].var():.3f}         {out[:,1].mean():.3f}  {out[:,1].var():.3f}              {bad.mean():.3f}  {bad.var():.3f}")
''')

CLIFF_ENV = '''
import numpy as np, random

# ---- 悬崖行走 (cliff walking)：4 行 12 列。起点 S=(3,0)，终点 G=(3,11)，最下面一行中间 10 格是悬崖 ----
ROWS, COLS = 4, 12
START, GOAL = (3, 0), (3, 11)
MOVES = [(-1, 0), (1, 0), (0, -1), (0, 1)]       # 上 下 左 右
ARROWS = "↑↓←→"

def step(state, a):
    r, c = state
    dr, dc = MOVES[a]
    r, c = min(max(r + dr, 0), ROWS - 1), min(max(c + dc, 0), COLS - 1)
    if r == 3 and 1 <= c <= 10:                  # 掉下悬崖：奖励 -100，送回起点（回合不结束）
        return START, -100.0, False
    return (r, c), -1.0, (r, c) == GOAL          # 其余每步奖励 -1，到终点结束

def choose(Q, s, eps, rng):
    if rng.random() < eps:
        return rng.randrange(4)                  # 探索：随机动作
    q = Q[s]; m = max(q)
    return rng.choice([a for a in range(4) if q[a] == m])   # 利用：最大者（并列随机选）

def train(algo, episodes=500, alpha=0.5, eps=0.1, gamma=1.0, seed=0, eps_fn=None):
    rng = random.Random(seed)
    Q = {(r, c): [0.0] * 4 for r in range(ROWS) for c in range(COLS)}
    returns, falls = [], []
    for ep in range(episodes):
        e = eps_fn(ep) if eps_fn else eps
        s, a = START, choose(Q, START, e, rng)
        G, nfall, done = 0.0, 0, False
        while not done:
            s2, r, done = step(s, a)
            nfall += (r == -100.0)
            a2 = choose(Q, s2, e, rng)           # 下一步实际会做的动作（SARSA 要用它）
            if algo == "sarsa":
                target = r + gamma * (0.0 if done else Q[s2][a2])      # 同策略：用实际选的下一个动作
            else:
                target = r + gamma * (0.0 if done else max(Q[s2]))     # 异策略：用下一状态里最好的动作
            Q[s][a] += alpha * (target - Q[s][a])
            s, a = s2, a2
            G += r
        returns.append(G); falls.append(nfall)
    return Q, np.array(returns), np.array(falls)

def greedy_path(Q, limit=60):
    """从起点完全贪心（eps = 0）地走，返回走过的格子和总回报"""
    s, path, G = START, [START], 0.0
    for _ in range(limit):
        q = Q[s]; a = q.index(max(q))
        s, r, done = step(s, a); G += r; path.append(s)
        if done: break
    return path, G

def draw(path):
    on = set(path)
    for r in range(ROWS):
        print("".join("S" if (r, c) == START else "G" if (r, c) == GOAL else "#" if (r == 3 and 1 <= c <= 10)
                      else "*" if (r, c) in on else "." for c in range(COLS)))
'''

C_CLIFF = code(CLIFF_ENV + '''
# 同一个环境、同样的 alpha=0.5, eps=0.1, gamma=1，分别训练 SARSA 和 Q-learning，各重复 30 次
runs = 30
stats, Qs = {}, {}
for algo in ["sarsa", "qlearning"]:
    R_, F_, Qs[algo] = [], [], []
    for k in range(runs):
        Q, ret, fall = train(algo, seed=k)
        R_.append(ret); F_.append(fall); Qs[algo].append(Q)
    stats[algo] = (np.mean(R_, axis=0), np.mean(F_, axis=0))
print("算法         前 50 局平均回报   最后 100 局平均回报   最后 100 局平均每局掉崖次数")
for algo, name in [("sarsa", "SARSA     "), ("qlearning", "Q-learning ")]:
    ret, fall = stats[algo]
    print(f"{name}   {ret[:50].mean():9.2f}          {ret[-100:].mean():9.2f}              {fall[-100:].mean():.3f}")

# 把 30 次运行学到的 Q 取平均，看「没有探索时」的贪心路径（* 是经过的格子，# 是悬崖）
for algo, name in [("sarsa", "SARSA"), ("qlearning", "Q-learning")]:
    Qm = {s: [float(np.mean([Q[s][a] for Q in Qs[algo]])) for a in range(4)] for s in Qs[algo][0]}
    path, G = greedy_path(Qm, limit=100)
    print(f"{name} 的平均 Q 的贪心路径：{len(path) - 1} 步，回报 {G:.0f}")
    draw(path)

# 每次运行单独看：贪心策略能不能在 100 步内走到终点，回报是多少
for algo, name in [("sarsa", "SARSA"), ("qlearning", "Q-learning")]:
    out = [greedy_path(Q, limit=100) for Q in Qs[algo]]
    reached = [G for p, G in out if p[-1] == GOAL]
    print(f"{name:<10s} 30 次运行中贪心策略走到终点 {len(reached)} 次；这些次的回报：" +
          ", ".join(f"{g:.0f}×{reached.count(g)}" for g in sorted(set(reached), reverse=True)))
''')

C_DECAY = code(CLIFF_ENV + '''
# 在线回报的差距来自探索：让 eps 逐渐衰减（0.5 -> 0.01），训练 2000 局，各 20 次取平均
decay = lambda ep: max(0.01, 0.5 / (1 + ep / 20))
print("eps 衰减：第 0 局", decay(0), "  第 100 局", round(decay(100), 3), "  第 1999 局", round(decay(1999), 3))
print("算法         固定 eps=0.1：最后 100 局回报     衰减 eps：最后 100 局回报    衰减 eps 的贪心路径回报")
for algo, name in [("sarsa", "SARSA     "), ("qlearning", "Q-learning ")]:
    fixed, dec, greedy = [], [], []
    for k in range(20):
        _, ret, _ = train(algo, episodes=2000, seed=k)
        fixed.append(ret[-100:].mean())
        Q, ret, _ = train(algo, episodes=2000, seed=k, eps_fn=decay)
        dec.append(ret[-100:].mean())
        greedy.append(greedy_path(Q, limit=100)[1])
    print(f"{name}            {np.mean(fixed):8.2f}                    {np.mean(dec):8.2f}                 {np.mean(greedy):8.2f}")
''')
