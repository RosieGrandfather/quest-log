from runlib import Notebook

nb = Notebook()

# ───── 两层 MLP ─────
C_DATA = nb.cell('''
import numpy as np

def make_moons(n, noise, seed):
    """两个互相咬合的半月：上半月是类别 0，下半月是类别 1"""
    rng = np.random.default_rng(seed)
    t = rng.uniform(0, np.pi, n)
    top = np.c_[np.cos(t), np.sin(t)]
    bottom = np.c_[1 - np.cos(t), 0.5 - np.sin(t)]
    is1 = np.arange(n) >= n // 2
    X = np.where(is1[:, None], bottom, top) + rng.normal(0, noise, (n, 2))
    return X, is1.astype(float)

Xtr, ytr = make_moons(200, 0.2, seed=0)       # 训练集
Xva, yva = make_moons(200, 0.2, seed=1)       # 验证集：另一批从同一分布抽的点
print(Xtr.shape, ytr.shape, ytr.mean())
print(np.round(Xtr[:3], 3))
# 线性分类器（逻辑回归）在这份数据上最多能做到多少？用最小二乘的直线粗略估一下
A = np.c_[Xtr, np.ones(len(Xtr))]
w = np.linalg.lstsq(A, 2 * ytr - 1, rcond=None)[0]
print("直线分类的训练准确率:", np.mean((A @ w > 0) == (ytr == 1)))
''')

C_MLP = nb.cell('''
ACT = {"relu": (lambda z: np.maximum(z, 0), lambda z: (z > 0) * 1.0),
       "tanh": (np.tanh, lambda z: 1 - np.tanh(z) ** 2)}

def sigmoid(z):
    e = np.exp(-np.abs(z))                       # 只对非正数取指数，避免溢出
    return np.where(z >= 0, 1 / (1 + e), e / (1 + e))

def init(sizes, seed=0):
    """He 初始化（为什么这样取，后面「权重初始化」一节讲）"""
    rng = np.random.default_rng(seed)
    P = {}
    for i, (m, n) in enumerate(zip(sizes[:-1], sizes[1:])):
        P[f"W{i}"] = rng.normal(0, np.sqrt(2 / m), (m, n))
        P[f"b{i}"] = np.zeros(n)
    return P

def forward(P, X, act="relu"):
    f, L = ACT[act][0], len(P) // 2
    zs, As = [], [X]
    for i in range(L):
        z = As[-1] @ P[f"W{i}"] + P[f"b{i}"]
        zs.append(z)
        As.append(f(z) if i < L - 1 else z)      # 最后一层不加激活：输出的是 logit
    return zs, As

P = init([2, 16, 1])
zs, As = forward(P, Xtr)
print([z.shape for z in zs], As[-1].shape)
''')

C_LOSS = nb.cell('''
def loss_grads(P, X, y, act="relu"):
    zs, As = forward(P, X, act)
    z, L = As[-1][:, 0], len(P) // 2
    loss = np.mean(np.maximum(z, 0) - z * y + np.log1p(np.exp(-np.abs(z))))   # 稳定的二分类交叉熵
    dz = ((sigmoid(z) - y) / len(y))[:, None]                                   # dL/dz = (p - y) / N
    G = {}
    for i in reversed(range(L)):
        G[f"W{i}"], G[f"b{i}"] = As[i].T @ dz, dz.sum(0)
        if i > 0:
            dz = (dz @ P[f"W{i}"].T) * ACT[act][1](zs[i - 1])
    return loss, G

loss, G = loss_grads(P, Xtr, ytr)
print(round(loss, 4), {k: v.shape for k, v in G.items()})
''')

C_GRADCHECK = nb.cell('''
def num_grad(P, key, idx, h=1e-5):
    old = P[key][idx]
    P[key][idx] = old + h; lp = loss_grads(P, Xtr, ytr)[0]
    P[key][idx] = old - h; lm = loss_grads(P, Xtr, ytr)[0]
    P[key][idx] = old
    return (lp - lm) / (2 * h)

for key, idx in [("W0", (0, 3)), ("W0", (1, 7)), ("b0", (5,)), ("W1", (4, 0)), ("b1", (0,))]:
    print(key, idx, f"{G[key][idx]:.6f}  {num_grad(P, key, idx):.6f}")
''')

C_TRAIN = nb.cell('''
def accuracy(P, X, y, act="relu"):
    return np.mean((forward(P, X, act)[1][-1][:, 0] > 0) == (y == 1))

P = init([2, 16, 1])
for step in range(301):
    loss, G = loss_grads(P, Xtr, ytr)
    if step % 50 == 0:
        print(f"步 {step:3d}  训练损失 {loss:.4f}  训练准确率 {accuracy(P, Xtr, ytr):.3f}  验证准确率 {accuracy(P, Xva, yva):.3f}")
    for k in P:
        P[k] -= 0.5 * G[k]                 # 最朴素的梯度下降，学习率 0.5
''')

# ───── 激活函数 ─────
C_ACT = nb.cell('''
from math import erf
gelu = lambda z: 0.5 * z * (1 + np.vectorize(erf)(z / np.sqrt(2)))   # z * Phi(z)，Phi 是标准正态的分布函数
ACT["gelu"] = (gelu, lambda z: (gelu(z + 1e-5) - gelu(z - 1e-5)) / 2e-5)   # 导数用中心差分近似
ACT["sigmoid"] = (sigmoid, lambda z: sigmoid(z) * (1 - sigmoid(z)))

zs = np.array([-4.0, -2.0, -0.5, 0.0, 0.5, 2.0, 4.0])
print("z       ", " ".join(f"{v:7.3f}" for v in zs))
for name in ["sigmoid", "tanh", "relu", "gelu"]:
    f, df = ACT[name]
    print(f"{name:8s} 值", " ".join(f"{v:7.3f}" for v in f(zs)))
    print(f"{'':8s} 导", " ".join(f"{v:7.3f}" for v in df(zs)))
''')

C_VANISH = nb.cell('''
def grad_flow(act, std_fn, depth=20, width=64, seed=0):
    """把一个随机的「误差信号」从第 depth 层反传回第 1 层，记录每层 dL/dz 的平均长度"""
    rng = np.random.default_rng(seed)
    f, df = ACT[act]
    a, Ws, zl = rng.normal(size=(32, width)), [], []
    for _ in range(depth):
        W = rng.normal(0, std_fn(width), (width, width))
        z = a @ W
        Ws.append(W); zl.append(z); a = f(z)
    dz = rng.normal(size=z.shape)
    norms = [np.linalg.norm(dz, axis=1).mean()]
    for W, z in zip(Ws[::-1][:-1], zl[::-1][1:]):
        dz = (dz @ W.T) * df(z)
        norms.append(np.linalg.norm(dz, axis=1).mean())
    return norms[::-1]                     # 下标 0 是第 1 层（最靠近输入）

xavier, he = (lambda n: np.sqrt(1 / n)), (lambda n: np.sqrt(2 / n))
for act, sf in [("sigmoid", xavier), ("tanh", xavier), ("relu", he)]:
    g = grad_flow(act, sf)
    print(f"{act:8s} 第1层 {g[0]:.2e}  第10层 {g[9]:.2e}  第20层 {g[-1]:.2e}  第1层/第20层 = {g[0] / g[-1]:.2e}")
''')

# ───── 初始化 ─────
C_INITVAR = nb.cell('''
rng = np.random.default_rng(0)
n = 256
x = rng.normal(0, 1, (1000, n))                      # 输入：每个分量均值 0、方差 1
for std in [0.01, 0.1, 1.0]:
    W = rng.normal(0, std, (n, n))
    z = x @ W
    print(f"w 的标准差 {std:<5}  理论 Var(z) = n*Var(w)*Var(x) = {n * std**2:9.4f}   实测 Var(z) = {z.var():9.4f}")
''')

C_INITDEEP = nb.cell('''
def act_stats(act, std_fn, depth=20, width=256, seed=0):
    rng = np.random.default_rng(seed)
    a = rng.normal(size=(500, width))
    out = []
    for l in range(depth):
        a = ACT[act][0](a @ rng.normal(0, std_fn(width), (width, width)))
        out.append(a.std())
    return out

print("tanh 网络，各层激活值的标准差（第 1, 5, 10, 20 层）")
for name, sf in [("std=0.01", lambda n: 0.01), ("std=1", lambda n: 1.0), ("Xavier", xavier)]:
    s = act_stats("tanh", sf)
    print(f"  {name:9s}", [f"{s[i - 1]:.4f}" for i in (1, 5, 10, 20)])
print("ReLU 网络")
for name, sf in [("Xavier", xavier), ("He", he)]:
    s = act_stats("relu", sf)
    print(f"  {name:9s}", [f"{s[i - 1]:.4f}" for i in (1, 5, 10, 20)])
''')

# ───── 优化器 ─────
C_OPT = nb.cell('''
class Opt:
    """kind: sgd / momentum / rmsprop / adam。step(P, G) 原地更新参数字典 P"""
    def __init__(self, kind, lr, beta1=0.9, beta2=0.999, eps=1e-8):
        self.kind, self.lr, self.b1, self.b2, self.eps = kind, lr, beta1, beta2, eps
        self.m, self.v, self.t = {}, {}, 0

    def step(self, P, G, lr=None):
        lr = self.lr if lr is None else lr
        self.t += 1
        for k in P:
            g = G[k]
            m, v = self.m.get(k, 0 * g), self.v.get(k, 0 * g)
            if self.kind == "sgd":
                P[k] -= lr * g
            elif self.kind == "momentum":
                m = self.b1 * m + g                         # 速度：把历史梯度累起来
                P[k] -= lr * m
            elif self.kind == "rmsprop":
                v = 0.9 * v + 0.1 * g * g                   # 每个坐标自己的梯度平方的滑动平均
                P[k] -= lr * g / (np.sqrt(v) + self.eps)
            elif self.kind == "adam":
                m = self.b1 * m + (1 - self.b1) * g
                v = self.b2 * v + (1 - self.b2) * g * g
                mhat, vhat = m / (1 - self.b1 ** self.t), v / (1 - self.b2 ** self.t)   # 偏差修正
                P[k] -= lr * mhat / (np.sqrt(vhat) + self.eps)
            self.m[k], self.v[k] = m, v
''')

C_OPTQUAD = nb.cell('''
# 病态二次函数 f(w) = 0.5*(w0^2 + 50*w1^2)：一个方向平缓，一个方向陡峭
H = np.array([1.0, 50.0])
for kind, lr in [("sgd", 0.03), ("momentum", 0.01), ("rmsprop", 0.05), ("adam", 0.1)]:
    opt, P2 = Opt(kind, lr), {"w": np.array([1.0, 1.0])}
    for t in range(1, 2001):
        opt.step(P2, {"w": H * P2["w"]})
        if 0.5 * np.sum(H * P2["w"] ** 2) < 1e-3:
            break
    print(f"{kind:9s} 学习率 {lr:<5}  第 {t:4d} 步时 f = {0.5 * np.sum(H * P2['w'] ** 2):.6f}")
''')

C_OPTMLP = nb.cell('''
for kind, lr in [("sgd", 0.1), ("momentum", 0.1), ("rmsprop", 0.01), ("adam", 0.01)]:
    P = init([2, 16, 1])                           # 四个优化器从同一个初始点出发
    opt, curve = Opt(kind, lr), []
    for step in range(101):
        loss, G = loss_grads(P, Xtr, ytr)
        curve.append(loss)
        opt.step(P, G)
    print(f"{kind:9s} lr={lr:<5} 损失 第0步 {curve[0]:.3f}  第20步 {curve[20]:.3f}  第50步 {curve[50]:.3f}  第100步 {curve[100]:.3f}")
''')

# ───── 学习率与调度 ─────
C_LR = nb.cell('''
for lr in [0.001, 0.05, 0.5, 5.0, 50.0]:
    P, opt, curve = init([2, 16, 1]), Opt("sgd", lr), []
    for step in range(200):
        loss, G = loss_grads(P, Xtr, ytr)
        curve.append(loss)
        opt.step(P, G)
    print(f"SGD lr={lr:<6}  第0步 {curve[0]:.3f}  第50步 {curve[50]:.3f}  第199步 {curve[-1]:.3f}  最大值 {max(curve):.3f}")
''')

C_SCHED = nb.cell('''
def lr_at(t, T, base, warmup):
    """线性 warmup 到 base，然后余弦衰减到 0"""
    if t < warmup:
        return float(base * (t + 1) / warmup)
    progress = (t - warmup) / (T - warmup)
    return float(base * 0.5 * (1 + np.cos(np.pi * progress)))

T = 400
print([round(lr_at(t, T, 0.3, 20), 4) for t in [0, 9, 19, 20, 100, 200, 300, 399]])

def run(schedule, seed, steps=T, batch=16):
    P, opt, rng, tail = init([2, 16, 1]), Opt("adam", 0.01), np.random.default_rng(seed), []
    for t in range(steps):
        idx = rng.integers(0, len(ytr), batch)             # 小批量：每步随机抽 16 个点
        _, G = loss_grads(P, Xtr[idx], ytr[idx])
        opt.step(P, G, lr=schedule(t))
        if t >= steps - 20:
            tail.append(loss_grads(P, Xtr, ytr)[0])        # 最后 20 步，整个训练集上的损失
    return tail[-1], np.std(tail)

for name, sched in [("常数 lr=0.3", lambda t: 0.3), ("warmup + 余弦", lambda t: lr_at(t, T, 0.3, 20))]:
    r = np.array([run(sched, seed) for seed in range(5)])
    print(f"{name:14s} 最终损失（5 个种子）{np.round(r[:, 0], 3)}  均值 {r[:, 0].mean():.3f}  最后 20 步的抖动 {r[:, 1].mean():.4f}")
''')

# ───── 正则化 ─────
C_REGDEF = nb.cell('''
def loss_grads_reg(P, X, y, act="relu", wd=0.0, p_drop=0.0, rng=None):
    """在 loss_grads 上加两样：权重衰减 wd，和对隐藏层的 dropout（p_drop 是丢弃概率）"""
    f, df = ACT[act]; L = len(P) // 2
    zs, As, masks = [], [X], []
    for i in range(L):
        z = As[-1] @ P[f"W{i}"] + P[f"b{i}"]
        zs.append(z)
        if i < L - 1:
            mask = (rng.random(z.shape) >= p_drop) / (1 - p_drop) if p_drop > 0 else np.ones_like(z)
            masks.append(mask); As.append(f(z) * mask)
        else:
            As.append(z)
    z = As[-1][:, 0]
    loss = np.mean(np.maximum(z, 0) - z * y + np.log1p(np.exp(-np.abs(z))))
    dz, G = ((sigmoid(z) - y) / len(y))[:, None], {}
    for i in reversed(range(L)):
        G[f"W{i}"], G[f"b{i}"] = As[i].T @ dz + wd * P[f"W{i}"], dz.sum(0)
        if i > 0:
            dz = (dz @ P[f"W{i}"].T) * masks[i - 1] * df(zs[i - 1])
    return loss, G
''')

C_OVERFIT = nb.cell('''
Xs, ys = make_moons(40, 0.35, seed=5)           # 只有 40 个、噪声较大的训练点
Xv, yv = make_moons(400, 0.35, seed=6)          # 400 个验证点

def fit(sizes, steps=1000, lr=0.01, seed=0, every=100, **kw):
    P, opt, hist = init(sizes, seed), Opt("adam", lr), []
    for t in range(steps + 1):
        loss, G = loss_grads_reg(P, Xs, ys, **kw)
        if t % every == 0:
            hist.append((t, loss_grads(P, Xs, ys)[0], loss_grads(P, Xv, yv)[0]))
        opt.step(P, G)
    return P, hist
P0, hist = fit([2, 64, 64, 1])
print("无正则：步  训练损失  验证损失")
for t, tr, va in hist:
    print(f"        {t:4d}   {tr:.4f}   {va:.4f}")
''')

C_REG = nb.cell('''
def report(name, hist):
    best = min(hist, key=lambda h: h[2])
    print(f"{name:22s} 最终 训练 {hist[-1][1]:.3f} 验证 {hist[-1][2]:.3f}   验证最低 {best[2]:.3f}（第 {best[0]} 步）")

report("无正则", hist)
report("权重衰减 wd=0.05", fit([2, 64, 64, 1], wd=0.05)[1])
report("dropout p=0.3", fit([2, 64, 64, 1], p_drop=0.3, rng=np.random.default_rng(1))[1])
report("权重衰减 + dropout", fit([2, 64, 64, 1], wd=0.02, p_drop=0.3, rng=np.random.default_rng(1))[1])

# 早停：每 10 步看一次验证损失，连续 5 次没有创新低就停，并取回最好的那组参数
P, opt, best, best_P, bad = init([2, 64, 64, 1]), Opt("adam", 0.01), 9.9, None, 0
for t in range(1001):
    _, G = loss_grads_reg(P, Xs, ys)
    opt.step(P, G)
    if t % 10 == 0:
        va = loss_grads(P, Xv, yv)[0]
        if va < best - 1e-4:
            best, best_P, bad, best_t = va, {k: v.copy() for k, v in P.items()}, 0, t
        else:
            bad += 1
    if bad >= 5:
        break
print(f"早停：第 {t} 步停止，取回第 {best_t} 步的参数，验证损失 {best:.3f}，验证准确率 {accuracy(best_P, Xv, yv):.3f}")
''')

C_BN = nb.cell('''
def batchnorm(a, gamma, beta, run, train, mom=0.1, eps=1e-5):
    """批归一化：训练时用这一批的均值和方差，同时更新滑动平均；评估时用滑动平均"""
    if train:
        mu, var = a.mean(0), a.var(0)
        run["mu"] = (1 - mom) * run["mu"] + mom * mu
        run["var"] = (1 - mom) * run["var"] + mom * var
    else:
        mu, var = run["mu"], run["var"]
    return gamma * (a - mu) / np.sqrt(var + eps) + beta

rng = np.random.default_rng(0)
a = rng.normal(5.0, 3.0, (64, 4)) * np.array([1, 10, 0.1, 1])      # 四个尺度差别很大的特征
run = {"mu": np.zeros(4), "var": np.ones(4)}
out = batchnorm(a, np.ones(4), np.zeros(4), run, train=True)
print("归一化前 均值", np.round(a.mean(0), 2), " 标准差", np.round(a.std(0), 2))
print("归一化后 均值", np.round(out.mean(0), 2), " 标准差", np.round(out.std(0), 2))

# 把 BN 放进 20 层、初始化很差的网络（std=0.01）：没有 BN，信号逐层消失；有 BN，每层都被拉回标准尺度
x = rng.normal(size=(256, 128))
for use_bn in [False, True]:
    h, run = x, {"mu": np.zeros(128), "var": np.ones(128)}
    for l in range(20):
        h = h @ rng.normal(0, 0.01, (128, 128))
        if use_bn:
            h = batchnorm(h, 1.0, 0.0, run, train=True)
        h = np.tanh(h)
    print("BN" if use_bn else "无 BN", "第 20 层激活值的标准差:", round(h.std(), 4))
''')

# ───── 诊断 ─────
C_DIAG = nb.cell('''
def curve_of(lr, kind="adam", steps=300, labels=None, seed=0):
    P, opt, hist = init([2, 16, 1], seed), Opt(kind, lr), []
    y = ytr if labels is None else labels
    for t in range(steps):
        loss, G = loss_grads(P, Xtr, y)
        hist.append(loss)
        opt.step(P, G)
    return P, hist

shuffled = np.random.default_rng(0).permutation(ytr)            # 故意把标签和输入的对应关系打乱：模拟「数据管线写错了」
cases = {"正常 (Adam 0.01)": curve_of(0.01), "lr 太小 (1e-5)": curve_of(1e-5),
         "lr 太大 (SGD 30)": curve_of(30.0, "sgd"), "标签错位": curve_of(0.01, labels=shuffled)}
print("情形                  第0步  第100步  第299步  验证准确率")
for name, (P, h) in cases.items():
    print(f"{name:20s} {h[0]:6.3f} {h[100]:7.3f} {h[299]:8.3f}   {accuracy(P, Xva, yva):.3f}")
print("二分类、类别各半时，随机猜测的损失 ln2 =", round(np.log(2), 3))
''')

C_NAN = nb.cell('''
# 原因一：学习率大到参数爆炸，最终溢出成 inf / nan
P, opt = init([2, 16, 1]), Opt("sgd", 1e4)
with np.errstate(all="ignore"):
    for t in range(100):
        loss, G = loss_grads(P, Xtr, ytr)
        if not np.isfinite(loss):
            print("lr=1e4：第", t, "步损失变成", loss)
            break
        opt.step(P, G)

# 原因二：自己写 log(sigmoid(z))，logit 太极端时概率变成 0
with np.errstate(all="ignore"):
    z, y = np.array([-800.0, 3.0]), np.array([0.0, 1.0])
    p = 1 / (1 + np.exp(-z))
    naive = -(y * np.log(p) + (1 - y) * np.log(1 - p))
    stable = np.maximum(z, 0) - z * y + np.log1p(np.exp(-np.abs(z)))
print("p =", p, " 朴素公式:", naive, " 稳定公式:", np.round(stable, 4))
''')

C_SANITY = nb.cell('''
# 检查一：随机初始化时，损失应该接近 ln(类别数)
def init_loss(scale_out, seed):
    P = init([2, 16, 1], seed)
    P["W1"] = P["W1"] * scale_out                       # 把输出层权重缩小：初始预测就接近 0.5
    return loss_grads(P, Xtr, ytr)[0]

print("输出层不缩小:", np.round([init_loss(1.0, s) for s in range(5)], 3))
print("输出层缩小 10 倍:", np.round([init_loss(0.1, s) for s in range(5)], 3), " (ln2 = 0.693)")

# 检查二：只拿 8 个样本，应该能把损失压到接近 0（连这都做不到，说明代码或模型有问题）
P, opt = init([2, 16, 1]), Opt("adam", 0.01)
Xb, yb = Xtr[::25], ytr[::25]
for t in range(400):
    loss, G = loss_grads(P, Xb, yb)
    opt.step(P, G)
print("8 个样本上过拟合 400 步后的损失:", round(loss, 5), " 样本数", len(yb))
''')

# ───── PyTorch 对照 ─────
C_TORCH = nb.cell('''
import torch, torch.nn as nn

torch.manual_seed(0)
model = nn.Sequential(nn.Linear(2, 16), nn.ReLU(), nn.Linear(16, 1)).double()
P = {"W0": model[0].weight.detach().numpy().T.copy(), "b0": model[0].bias.detach().numpy().copy(),
     "W1": model[2].weight.detach().numpy().T.copy(), "b1": model[2].bias.detach().numpy().copy()}

xt, yt = torch.tensor(Xtr), torch.tensor(ytr)
lossf = nn.BCEWithLogitsLoss()
loss_t = lossf(model(xt).squeeze(1), yt)
loss_t.backward()                                         # autograd 反向传播
loss_np, G = loss_grads(P, Xtr, ytr)                      # 我们手写的反向传播，同一组权重
print("损失  torch", round(loss_t.item(), 6), " numpy", round(loss_np, 6))
print("W0 梯度与手写版本的最大差小于 1e-12:", bool(np.abs(model[0].weight.grad.numpy().T - G["W0"]).max() < 1e-12))
print("b1 梯度与手写版本的最大差小于 1e-12:", bool(np.abs(model[2].bias.grad.numpy() - G["b1"]).max() < 1e-12))

opt = torch.optim.AdamW(model.parameters(), lr=0.01, weight_decay=0.01)
sched = torch.optim.lr_scheduler.OneCycleLR(opt, max_lr=0.02, total_steps=300, pct_start=0.1, anneal_strategy="cos")
for step in range(300):
    opt.zero_grad()
    lossf(model(xt).squeeze(1), yt).backward()
    opt.step(); sched.step()
with torch.no_grad():
    acc = lambda X, y: ((model(torch.tensor(X)).squeeze(1) > 0).double() == torch.tensor(y)).double().mean().item()
    print("300 步后 训练损失", round(lossf(model(xt).squeeze(1), yt).item(), 4), " 训练准确率", acc(Xtr, ytr), " 验证准确率", acc(Xva, yva))
''', static=True)
