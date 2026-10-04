from runlib import code

C_TOY = code('''
import numpy as np

# 「真实世界」：带控制的阻尼振子，状态 s=(位置 x, 速度 v)。智能体看不到 s，只看到 48 像素的「图像」：
# 状态经过一个固定的随机混合 + tanh 渲染出来，再叠加噪声。
dt = 0.1
def step(s, a):
    x, v = s[..., 0], s[..., 1]
    v2 = v + dt * (-2.0 * x - 0.3 * v + a)
    return np.stack([x + dt * v2, v2], -1)

NP, NOISE = 48, 0.3
M = np.random.default_rng(42).normal(size=(2, NP))
render = lambda s, rng=None: np.tanh(0.8 * (s @ M)) + (0 if rng is None else NOISE * rng.normal(size=s.shape[:-1] + (NP,)))

def trajectories(n, T, rng):
    s = np.c_[rng.uniform(-2, 2, n), rng.uniform(-2, 2, n)]; S, A = [s], []
    for t in range(T):
        a = rng.uniform(-2, 2, n); s = step(s, a); S.append(s); A.append(a)
    return np.stack(S, 1), np.stack(A, 1)           # 形状 (n, T+1, 2) 与 (n, T)

def run(n_train, d=4):
    rng = np.random.default_rng(0)
    S, A = trajectories(n_train, 20, rng); O = render(S, rng)          # 训练数据：带噪声的「视频」
    # 1) 固定编码器：对训练图像做 PCA，取前 d 个主成分。之后编码器不再改变
    mu = O.reshape(-1, NP).mean(0)
    E = np.linalg.svd(O.reshape(-1, NP) - mu, full_matrices=False)[2][:d].T      # NP x d
    enc = lambda o: (o - mu) @ E
    dec = lambda z: z @ E.T + mu
    # 2) 在潜空间里学线性动力学 z' = [z, a, 1] @ W（最小二乘）
    Z = enc(O)
    X = np.concatenate([Z[:, :-1], A[..., None], np.ones_like(A)[..., None]], -1).reshape(-1, d + 2)
    W = np.linalg.lstsq(X, Z[:, 1:].reshape(-1, d), rcond=None)[0]
    # 3) 对照：直接在像素空间学线性动力学 o' = [o, a, 1] @ Wp
    Xp = np.concatenate([O[:, :-1], A[..., None], np.ones_like(A)[..., None]], -1).reshape(-1, NP + 2)
    Wp = np.linalg.lstsq(Xp, O[:, 1:].reshape(-1, NP), rcond=None)[0]

    # 评估：200 条没见过的轨迹，只看带噪声的第 0 帧，然后用动作序列往前「想象」30 步
    rt = np.random.default_rng(5)
    St, At = trajectories(200, 30, rt); Oclean = render(St); Onoisy = render(St, rt)
    z, op, o0 = enc(Onoisy[:, 0]), Onoisy[:, 0].copy(), Onoisy[:, 0]
    out = {"潜空间误差": [], "潜空间相对误差": [], "解码后像素误差": [], "像素空间模型": [], "直接复制第 0 帧": []}
    for k in range(30):
        z = np.c_[z, At[:, k], np.ones(len(z))] @ W                       # 全程只在潜空间里滚动
        op = np.c_[op, At[:, k], np.ones(len(op))] @ Wp
        rms = lambda a, b: float(np.sqrt(((a - b) ** 2).mean()))
        out["潜空间误差"].append(rms(z, enc(Oclean[:, k + 1])))               # 与「真实未来帧编码出的潜变量」比较
        out["潜空间相对误差"].append(rms(z, enc(Oclean[:, k + 1])) / rms(enc(Oclean[:, k + 1]), 0))   # 除以真实潜变量自身的大小
        out["解码后像素误差"].append(rms(dec(z), Oclean[:, k + 1]))           # 解码回像素，与干净的真实帧比较
        out["像素空间模型"].append(rms(op, Oclean[:, k + 1]))
        out["直接复制第 0 帧"].append(rms(o0, Oclean[:, k + 1]))
    # 潜变量里是否真的装着状态？用线性读出从 z 恢复 (x, v)，看 R^2
    Zt = enc(Onoisy[:, 0]); G = np.linalg.lstsq(np.c_[enc(O[:, :-1].reshape(-1, NP)), np.ones((O[:, :-1].size // NP, 1))], S[:, :-1].reshape(-1, 2), rcond=None)[0]
    pred = np.c_[Zt, np.ones(len(Zt))] @ G; true = St[:, 0]
    r2 = 1 - ((pred - true) ** 2).sum(0) / ((true - true.mean(0)) ** 2).sum(0)
    return out, r2

ks = [0, 2, 4, 9, 19, 29]
print("滚动步数 k =", [k + 1 for k in ks])
for n_train in [300, 5]:
    out, r2 = run(n_train)
    print(f"--- 训练用 {n_train} 条轨迹（{n_train * 20} 条转移）；潜变量读出状态的 R^2：位置 {r2[0]:.3f}，速度 {r2[1]:.3f}")
    for name, e in out.items():
        print(f"{name:14s}", np.round(np.array(e)[ks], 3))
''')

C_COLLAPSE = code('''
import numpy as np

# 在「潜空间里预测下一帧的潜变量」听上去很美，但有一个陷阱：如果编码器也在被训练，
# 它可以把所有输入都编码成同一个常数——这样预测误差恰好为 0。这叫表示坍缩 (collapse)。
dt = 0.1
def step(s, a):
    x, v = s[..., 0], s[..., 1]
    v2 = v + dt * (-2.0 * x - 0.3 * v + a)
    return np.stack([x + dt * v2, v2], -1)
NP = 48
M = np.random.default_rng(42).normal(size=(2, NP))
rng = np.random.default_rng(1)
s = np.c_[rng.uniform(-2, 2, 400), rng.uniform(-2, 2, 400)]; Ocur, Onext = [], []
for t in range(20):                                   # 无动作的自由振荡，足够说明问题
    s2 = step(s, 0.0)
    Ocur.append(np.tanh(0.8 * s @ M) + 0.1 * rng.normal(size=(400, NP)))
    Onext.append(np.tanh(0.8 * s2 @ M) + 0.1 * rng.normal(size=(400, NP))); s = s2
O, On = np.concatenate(Ocur), np.concatenate(Onext); N = len(O)

mean = np.concatenate([O, On]).mean(0); Oc, Onc = O - mean, On - mean      # 减去均值，方便谈「方差」

def train(lam, steps=3000, lr=0.01, d=2):
    """lam = 0：只最小化预测损失；lam > 0：再加一个惩罚，要求潜变量的协方差接近单位阵（方差为 1、互不相关）"""
    r = np.random.default_rng(0)
    E = r.normal(0, 0.3, (NP, d)); A = np.eye(d) * 0.9
    for i in range(steps + 1):
        Z, Zn = Oc @ E, Onc @ E
        R = Zn - Z @ A                                # 预测误差：下一帧的潜变量 - 预测值
        Cz = Z.T @ Z / N                              # 潜变量的协方差矩阵
        if i in (0, 10, 100, steps):
            loss = np.mean((R ** 2).sum(1))
            print(f"  第 {i:4d} 步  预测损失 {loss:8.5f}   潜变量的总方差 {np.trace(Cz):8.5f}   损失 / 方差 = {loss / np.trace(Cz):.3f}")
        dZn, dZ = 2 * R / N, -2 * R @ A.T / N         # 手写梯度：预测损失 = mean(|Zn - Z A|^2)
        dZ = dZ + lam * 4 * Z @ (Cz - np.eye(d)) / N  # 惩罚项 lam * |Cz - I|_F^2 的梯度
        dA = -2 * Z.T @ R / N
        E -= lr * (Onc.T @ dZn + Oc.T @ dZ); A -= lr * dA
    return E

print("没有任何约束：")
train(0.0)
print("加上「潜变量协方差接近单位阵」的惩罚（lam = 1）：")
train(1.0)
''')

C_RSSM = code('''
import numpy as np
sigmoid = lambda x: 1 / (1 + np.exp(-x))
rng = np.random.default_rng(0)
dh, dz, da, de = 8, 4, 2, 6            # 确定性状态 h、随机状态 z、动作 a、观测嵌入 e 的维度

# RSSM 的几个部件（参数随机，只演示数据流）
Wx = rng.normal(0, 0.5, (3 * dh, dz + da)); Wh = rng.normal(0, 0.5, (3 * dh, dh))    # GRU：输入 [z, a]，状态 h
Wp = rng.normal(0, 0.15, (2 * dz, dh))                                                  # 先验 p(z|h) -> (均值, log 标准差)
Wq = rng.normal(0, 0.15, (2 * dz, dh + de))                                             # 后验 q(z|h, e) -> (均值, log 标准差)

def gru(x, h):                         # 和上一节同样的 GRU，这里把三个门的参数合并在一起
    gx, gh = Wx @ x, Wh @ h
    z = sigmoid(gx[:dh] + gh[:dh]); r = sigmoid(gx[dh:2 * dh] + gh[dh:2 * dh])
    n = np.tanh(gx[2 * dh:] + r * gh[2 * dh:])
    return (1 - z) * n + z * h

h_prev, z_prev, a_prev = rng.normal(size=dh) * 0.5, rng.normal(size=dz), np.array([0.5, -1.0])
e = rng.normal(size=de)                # 观测经过编码器得到的嵌入（这里随机给一个）

h = gru(np.r_[z_prev, a_prev], h_prev)             # 1) 确定性部分：h_t = f(h_{t-1}, z_{t-1}, a_{t-1})
mp, lp = np.split(Wp @ h, 2)                       # 2) 先验：只看 h，没有看新观测（= 预测）
mq, lq = np.split(Wq @ np.r_[h, e], 2)             # 3) 后验：h 加上这一帧的观测嵌入（= 滤波）
sp, sq = np.exp(lp), np.exp(lq)
print("先验均值", np.round(mp, 3), " 后验均值", np.round(mq, 3))

# 4) 先验和后验之间的 KL（对角高斯的闭式解）：训练时要把它压小，让「预测」靠近「看了观测之后的结论」
kl = np.sum(np.log(sp / sq) + (sq ** 2 + (mq - mp) ** 2) / (2 * sp ** 2) - 0.5)
zs = mq + sq * rng.normal(size=(400000, dz))       # 用重参数化从后验采样，蒙特卡洛核对
logq = -0.5 * (((zs - mq) / sq) ** 2).sum(1) - np.log(sq).sum()
logp = -0.5 * (((zs - mp) / sp) ** 2).sum(1) - np.log(sp).sum()
print("KL 闭式解 =", round(float(kl), 4), "  蒙特卡洛估计 =", round(float((logq - logp).mean()), 4))
print("Dreamer 里 KL 低于 3 nats 的部分不再产生梯度（free nats）：本例", "被截断（梯度为 0）" if kl < 3 else "不截断")

# 5) 想象：没有观测，只用先验往前滚动。同一个起点、同样的动作序列，每次采样出的 z 不同
def imagine(seed, steps=3):
    r = np.random.default_rng(seed); h_, z_ = h, mq + sq * r.normal(size=dz)
    for t in range(steps):
        h_ = gru(np.r_[z_, [0.5, -1.0]], h_)
        m_, l_ = np.split(Wp @ h_, 2); z_ = m_ + np.exp(l_) * r.normal(size=dz)
    return z_
samples = np.array([imagine(s) for s in range(1000)])
print("想象 3 步后，z 各维的标准差（1000 次采样）：", np.round(samples.std(0), 3))
''')
