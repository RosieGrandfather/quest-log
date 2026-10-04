from runlib import code

# 网格世界环境（后面几个代码块都复用同一个环境，每块独立运行，所以环境代码会重复出现）
C_LOOP = code('''
import numpy as np

class GridWorld:
    """5x5 网格世界。状态 = 格子编号 行*5+列。动作：0上 1下 2左 3右。
    起点 (0,0)；终点 (4,4) 奖励 +10；陷阱 (2,3) 奖励 -10；两者都是终止状态；其余每步奖励 0。
    撞墙：留在原地。"""
    N = 5
    MOVES = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    NAMES = ["上", "下", "左", "右"]
    GOAL, TRAP, START = (4, 4), (2, 3), (0, 0)

    def reset(self):
        self.pos = self.START
        return self.pos[0] * self.N + self.pos[1]

    def step(self, a):
        r, c = self.pos
        dr, dc = self.MOVES[a]
        r, c = min(max(r + dr, 0), self.N - 1), min(max(c + dc, 0), self.N - 1)
        self.pos = (r, c)
        s2 = r * self.N + c
        if self.pos == self.GOAL:
            return s2, 10.0, True
        if self.pos == self.TRAP:
            return s2, -10.0, True
        return s2, 0.0, False

# 智能体-环境循环：智能体看到状态 S_t，选动作 A_t；环境返回奖励 R_{t+1} 和新状态 S_{t+1}
env = GridWorld()
rng = np.random.default_rng(3)
s = env.reset()
print("t  状态 动作  奖励  下一状态")
for t in range(12):
    a = int(rng.integers(4))              # 随机策略：四个动作等可能
    s2, r, done = env.step(a)
    print(f"{t:<2d} {s:<4d} {GridWorld.NAMES[a]}    {r:<5.1f} {s2}" + ("   <- 终止" if done else ""))
    s = s2
    if done:
        break
''')

C_MDP = code('''
import numpy as np

# 一个很小的 MDP：3 个状态 {0,1,2}，2 个动作 {0,1}。状态 2 是终止状态（吸收态）。
# P[s, a, s'] = 在状态 s 做动作 a，转移到 s' 的概率；R[s, a] = 期望的即时奖励
P = np.zeros((3, 2, 3))
P[0, 0] = [0.7, 0.3, 0.0]     # 状态 0 做动作 0：大概率留在原地
P[0, 1] = [0.1, 0.9, 0.0]     # 状态 0 做动作 1：大概率前进到状态 1
P[1, 0] = [0.5, 0.5, 0.0]
P[1, 1] = [0.0, 0.2, 0.8]     # 状态 1 做动作 1：80% 到达终止状态
P[2, :] = [0.0, 0.0, 1.0]     # 终止状态：永远留在原地
R = np.array([[0.0, -1.0],    # 状态 0：动作 0 免费，动作 1 要付 1
              [0.0, 5.0],     # 状态 1：动作 1 可能拿到 5
              [0.0, 0.0]])
gamma = 0.9

# 合法性检查：每个 (s, a) 的转移概率之和必须是 1
print("P 的每行和：", P.sum(axis=2).ravel())

# 马尔可夫性：下一状态的分布只取决于「当前状态 + 当前动作」。
# 用采样验证：在 (s=1, a=1) 反复采样，经验频率应当接近 P[1, 1]
rng = np.random.default_rng(0)
samples = rng.choice(3, size=100000, p=P[1, 1])
print("P[1,1] 的真实值  :", P[1, 1])
print("10 万次采样的频率:", np.round(np.bincount(samples, minlength=3) / 100000, 3))

# 把一个策略 pi[s, a] 和 MDP 合起来，得到「只含状态」的马尔可夫链：P_pi[s, s'] = sum_a pi(a|s) P[s, a, s']
pi = np.array([[0.5, 0.5], [0.5, 0.5], [0.5, 0.5]])
P_pi = np.einsum("sa,sat->st", pi, P)
r_pi = (pi * R).sum(axis=1)
print("P_pi =\\n", P_pi)
print("r_pi =", r_pi)
''')

C_RET = code('''
import numpy as np

def discounted_return(rewards, gamma):
    # 直接按定义：G = R1 + gamma*R2 + gamma^2*R3 + ...
    return sum(gamma ** k * r for k, r in enumerate(rewards))

def discounted_return_backward(rewards, gamma):
    # 递归形式 G_t = R_{t+1} + gamma * G_{t+1}：从后往前算，一遍扫完（后面所有算法都靠这个递推）
    g = 0.0
    for r in reversed(rewards):
        g = r + gamma * g
    return g

rewards = [0, 0, 0, 10]           # 前 3 步没有奖励，第 4 步拿到 10
for gamma in [1.0, 0.9, 0.5, 0.0]:
    print(f"gamma={gamma:<4}  G = {discounted_return(rewards, gamma):6.2f}   递推算出 {discounted_return_backward(rewards, gamma):6.2f}")

# 随机对拍：两种写法在随机奖励序列上一致
rng = np.random.default_rng(0)
ok = all(abs(discounted_return(x, 0.95) - discounted_return_backward(x, 0.95)) < 1e-9
         for x in (rng.normal(size=int(rng.integers(1, 30))) for _ in range(500)))
print("500 条随机奖励序列，两种写法一致：", ok)

# 持续任务：每步奖励恒为 1、永不结束。gamma = 1 时回报发散；gamma < 1 时有限，等于 1/(1-gamma)
for gamma in [0.5, 0.9, 0.99]:
    G = discounted_return([1.0] * 5000, gamma)
    print(f"gamma={gamma:<5} 持续任务回报 {G:8.3f}   1/(1-gamma) = {1 / (1 - gamma):8.3f}   有效视野约 {1 / (1 - gamma):.0f} 步")
print("gamma=1 时，前 100 步的和是", sum([1.0] * 100), "，前 5000 步的和是", sum([1.0] * 5000), "（一直涨，没有极限）")
''')

C_MC = code('''
import numpy as np

class GridWorld:
    N = 5
    MOVES = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    GOAL, TRAP, START = (4, 4), (2, 3), (0, 0)
    def reset(self, start=None):
        self.pos = start or self.START
    def step(self, a):
        r, c = self.pos
        dr, dc = self.MOVES[a]
        self.pos = (min(max(r + dr, 0), self.N - 1), min(max(c + dc, 0), self.N - 1))
        if self.pos == self.GOAL: return 10.0, True
        if self.pos == self.TRAP: return -10.0, True
        return 0.0, False

env = GridWorld()
rng = np.random.default_rng(0)
gammas = [0.5, 0.9, 0.99, 1.0]

def rollout(first_action=None, max_steps=500):
    """用随机策略玩一局，返回奖励序列（可以指定第一步的动作，用来估计 q）"""
    env.reset(); rewards = []
    for t in range(max_steps):
        a = first_action if (t == 0 and first_action is not None) else int(rng.integers(4))
        r, done = env.step(a); rewards.append(r)
        if done: return rewards, True
    return rewards, False

def mc_returns(episodes, gamma):
    return np.array([sum(gamma ** k * r for k, r in enumerate(ep)) for ep in episodes])

# 1) 状态价值：从起点出发，用随机策略玩 20000 局，回报的平均值就是 v_pi(起点) 的蒙特卡洛估计
episodes, finished = zip(*[rollout() for _ in range(20000)])
print("20000 局里在 500 步内结束的比例：", np.mean(finished))
print("episode 长度：平均", round(np.mean([len(e) for e in episodes]), 1), " 最长", max(len(e) for e in episodes))
print("gamma   v(起点) 估计    标准误")
for g in gammas:
    G = mc_returns(episodes, g)
    print(f"{g:<6}  {G.mean():8.3f}      {G.std() / np.sqrt(len(G)):.3f}")

# 2) 动作价值：先强制做第一个动作 a，之后按随机策略；每个动作玩 5000 局（gamma=0.9）
print("起点的动作价值 q(起点, a)，gamma=0.9：")
q = []
for a, name in enumerate(["上", "下", "左", "右"]):
    eps, _ = zip(*[rollout(first_action=a) for _ in range(5000)])
    q.append(mc_returns(eps, 0.9).mean())
    print(f"  q(起点, {name}) = {q[-1]:.3f}")
print("四个动作的平均（随机策略下 v = sum_a pi(a|s) q(s,a)）：", round(float(np.mean(q)), 3))
''')

C_POMDP = code('''
import numpy as np

# 部分可观测：真实状态 z 只有两种 {0:"左房间", 1:"右房间"}，宝藏在其中一个房间里，智能体不知道在哪个。
# 传感器有噪声：宝藏在左房间时，传感器 80% 报告「左」；在右房间时，80% 报告「右」。
# 智能体不能直接看到 z，只能维护一个「信念 (belief)」b = P(z = 左 | 目前所有观测)
rng = np.random.default_rng(5)
z = 0                                        # 真实情况：宝藏在左房间（智能体不知道）
sensor = np.array([[0.8, 0.2],               # sensor[z, o] = P(观测 o | 真实状态 z)
                   [0.2, 0.8]])
belief = np.array([0.5, 0.5])                # 一开始完全不知道
print("真实状态是 0（左）。每次观测后用贝叶斯公式更新信念：")
for t in range(8):
    o = int(rng.choice(2, p=sensor[z]))      # 带噪声的观测
    belief = belief * sensor[:, o]           # 贝叶斯：先验 × 似然
    belief /= belief.sum()                   # 归一化
    print(f"t={t}  观测={'左' if o == 0 else '右'}  信念 P(左)={belief[0]:.3f}")
# 一次观测并不是「状态」，但「观测的历史 -> 信念」可以当作新的状态：它满足马尔可夫性
''')
