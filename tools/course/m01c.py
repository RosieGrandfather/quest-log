from runlib import Notebook

nb = Notebook()

# ───── 三类学习 ─────
C_SUP = nb.cell('''
import numpy as np

rng = np.random.default_rng(0)
X = rng.normal(size=(6, 2))                 # 6 个样本，每个样本 2 个特征
w_true = np.array([2.0, -1.0])
y_reg = X @ w_true + 0.5                    # 回归：标准答案是连续的数
y_cls = (y_reg > 0.5).astype(int)           # 分类：标准答案是类别 0 / 1
print(X.shape, y_reg.shape, y_cls.shape)
print(np.round(y_reg, 2))
print(y_cls)
''')

C_UNSUP = nb.cell('''
rng = np.random.default_rng(1)
A = rng.normal([0, 0], 0.5, size=(50, 2))   # 一团点
B = rng.normal([3, 3], 0.5, size=(50, 2))   # 另一团点
Z = np.vstack([A, B])                       # 只有 X，没有任何标签
centers = Z[[0, 1]].copy()                  # 随便取两个点当初始中心
for it in range(20):
    d = ((Z[:, None, :] - centers[None, :, :]) ** 2).sum(axis=2)   # 每点到每个中心的距离平方
    lab = d.argmin(axis=1)                  # 归到最近的中心
    new = np.array([Z[lab == k].mean(axis=0) for k in range(2)])   # 中心移到本团的均值
    if np.allclose(new, centers):
        break
    centers = new
print(it, np.round(centers, 2).tolist(), np.bincount(lab).tolist())
''')

C_RL = nb.cell('''
rng = np.random.default_rng(2)
p = np.array([0.3, 0.6])                    # 两台老虎机的中奖概率（智能体不知道）
Q = np.zeros(2); N = np.zeros(2)            # 对每台机器的价值估计、尝试次数
total = 0.0
for t in range(1000):
    a = int(rng.integers(2)) if rng.random() < 0.1 else int(Q.argmax())   # 10% 随机探索，其余选当前最好的
    r = float(rng.random() < p[a])          # 只能看到「自己选的那台」的奖励
    N[a] += 1
    Q[a] += (r - Q[a]) / N[a]               # 增量求平均
    total += r
print(N.tolist(), np.round(Q, 2).tolist(), total)
''')

# ───── 四个部分 ─────

C_FOUR = nb.cell('''
rng = np.random.default_rng(0)
x = rng.uniform(0, 1, 30)
y = 2 * x + 1 + rng.normal(0, 0.2, 30)      # 数据：真实规律 y = 2x + 1，加噪声

def model(w, b, x):                         # 模型：一族直线 y = w x + b
    return w * x + b

def loss(w, b):                             # 损失：均方误差
    return np.mean((model(w, b, x) - y) ** 2)

ws = np.linspace(0, 4, 9)                   # 优化：最笨的办法，在网格上试（b 固定为 1）
L = [loss(w, 1.0) for w in ws]
for w, l in zip(ws, L):
    print(f"w={w:.1f}  损失={l:.3f}")
print("最好的 w：", ws[int(np.argmin(L))])
''')

# ───── 三分数据 ─────

C_SPLIT = nb.cell('''
rng = np.random.default_rng(42)
n = 60
x = rng.uniform(0, 1, n)
y = np.sin(2 * np.pi * x) + rng.normal(0, 0.3, n)   # 真实规律是正弦波，加噪声

idx = rng.permutation(n)                    # 先随机打乱，再切
tr, va, te = idx[:20], idx[20:40], idx[40:]
xtr, ytr = x[tr], y[tr]
xva, yva = x[va], y[va]
xte, yte = x[te], y[te]
print(len(tr), len(va), len(te))
print(len(set(tr) & set(va)), len(set(tr) & set(te)), len(set(va) & set(te)))   # 三份互不重叠
''')

C_LEAK = nb.cell('''
rng = np.random.default_rng(3)
Xv, Xt = rng.normal(size=(40, 5)), rng.normal(size=(40, 5))   # 验证集、测试集：5 个特征
yv, yt = rng.integers(0, 2, 40), rng.integers(0, 2, 40)       # 标签是纯随机的，特征和标签毫无关系
W = rng.normal(size=(500, 5))               # 500 个「模型」：每个是一组随机权重，预测 x@w > 0
pv = (Xv @ W.T > 0).astype(int)             # 每个模型在验证集上的预测，形状 (40, 500)
pt = (Xt @ W.T > 0).astype(int)
acc_v = (pv == yv[:, None]).mean(axis=0)    # 500 个验证准确率
acc_t = (pt == yt[:, None]).mean(axis=0)
g = int(acc_v.argmax())                     # 用验证集挑「最好」的那一个
print("验证集上最好的准确率：", acc_v[g])
print("它在测试集上的准确率：", acc_t[g])
print("500 个模型在测试集上的平均准确率：", round(float(acc_t.mean()), 3))
''')

C_POLY = nb.cell('''
def mse(y, yhat):
    return float(np.mean((y - yhat) ** 2))

print("次数  训练MSE  验证MSE")
for d in [0, 1, 3, 5, 9]:
    coef = np.polyfit(xtr, ytr, d)          # 只用训练集拟合 d 次多项式
    print(f"{d:<5d} {mse(ytr, np.polyval(coef, xtr)):.3f}    {mse(yva, np.polyval(coef, xva)):.3f}")
''')

C_POLY2 = nb.cell('''
val = {}
for d in range(0, 10):
    coef = np.polyfit(xtr, ytr, d)
    val[d] = mse(yva, np.polyval(coef, xva))
best = min(val, key=val.get)                # 用验证集选次数
coef = np.polyfit(xtr, ytr, best)
print("验证集选出的次数：", best)
print("测试集 MSE（只看这一次）：", round(mse(yte, np.polyval(coef, xte)), 3))
''')

C_BV = nb.cell('''
def true_f(x):
    return np.sin(2 * np.pi * x)

rng = np.random.default_rng(7)
x0 = 0.25                                   # 在 x=0.25 这一点看预测，真值 sin(pi/2)=1
for d in [1, 3, 9]:
    preds = []
    for _ in range(300):                    # 300 份不同的训练集，每份 20 个点
        xs = rng.uniform(0, 1, 20)
        ys = true_f(xs) + rng.normal(0, 0.3, 20)
        preds.append(np.polyval(np.polyfit(xs, ys, d), x0))
    preds = np.array(preds)
    bias2 = (preds.mean() - true_f(x0)) ** 2
    print(f"次数 {d}: 偏差^2={bias2:.3f}  方差={preds.var():.3f}")
''')

C_METRIC = nb.cell('''
def mae(y, yhat):
    return float(np.mean(np.abs(y - yhat)))

def rmse(y, yhat):
    return float(np.sqrt(mse(y, yhat)))

base = np.full_like(yte, ytr.mean())        # 基线：永远预测训练集的平均值
coef = np.polyfit(xtr, ytr, 3)
fit = np.polyval(coef, xte)
print("          MSE    MAE    RMSE")
print(f"基线      {mse(yte, base):.3f}  {mae(yte, base):.3f}  {rmse(yte, base):.3f}")
print(f"3 次多项式 {mse(yte, fit):.3f}  {mae(yte, fit):.3f}  {rmse(yte, fit):.3f}")
''')

C_ACC = nb.cell('''
rng = np.random.default_rng(5)
y = (rng.random(1000) < 0.05).astype(int)   # 1000 个样本，约 5% 是正类（比如「次品」）
pred = np.zeros(1000, dtype=int)            # 「模型」：永远说是负类
print("正类个数：", int(y.sum()))
print("准确率：", (pred == y).mean())
print("抓到的正类：", int(((pred == 1) & (y == 1)).sum()))
''')

C_ERM = nb.cell('''
def make(n, rng):
    xs = rng.uniform(0, 1, n)
    return xs, np.sin(2 * np.pi * xs) + rng.normal(0, 0.3, n)

rng = np.random.default_rng(11)
xbig, ybig = make(20000, rng)               # 用 20000 个新样本近似「真实风险」
print("n     训练MSE(中位数)  真实MSE(中位数)")
for n in [15, 30, 100, 1000]:
    tr_l, true_l = [], []
    for _ in range(50):
        xs, ys = make(n, rng)
        c = np.polyfit(xs, ys, 5)           # 固定用 5 次多项式
        tr_l.append(mse(ys, np.polyval(c, xs)))
        true_l.append(mse(ybig, np.polyval(c, xbig)))
    print(f"{n:<5d} {np.median(tr_l):.3f}            {np.median(true_l):.3f}")
''')

C_MLE = nb.cell('''
rng = np.random.default_rng(0)
n, s = 30, 0.3
x = rng.uniform(0, 1, n)
y = 2 * x + 1 + rng.normal(0, s, n)         # 噪声是 N(0, 0.3^2)
ws = np.linspace(1, 3, 201)
res = y[None, :] - (ws[:, None] * x[None, :] + 1.0)           # 每个 w 的残差，形状 (201, 30)
mse_w = (res ** 2).mean(axis=1)
loglik = -0.5 * n * np.log(2 * np.pi * s ** 2) - (res ** 2).sum(axis=1) / (2 * s ** 2)
print("MSE 最小的 w：", round(float(ws[mse_w.argmin()]), 2))
print("对数似然最大的 w：", round(float(ws[loglik.argmax()]), 2))
print(np.allclose(loglik, -0.5 * n * np.log(2 * np.pi * s ** 2) - n * mse_w / (2 * s ** 2)))
''')

