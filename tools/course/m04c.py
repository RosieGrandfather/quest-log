from runlib import Notebook

nb = Notebook()

# ───── 偏差-方差：重复采样 ─────
C_BV1 = nb.cell('''
import numpy as np
rng = np.random.default_rng(0)
sigma = 0.3                                    # 噪声标准差
f = lambda x: np.sin(2 * np.pi * x)            # 真函数（实际中未知）
x_grid = np.linspace(0, 1, 50)                 # 固定的评估点

def poly_fit_predict(x, y, deg, x_new):        # deg 次多项式的最小二乘拟合
    w = np.linalg.lstsq(np.vander(x, deg + 1), y, rcond=None)[0]
    return np.vander(x_new, deg + 1) @ w

def bias_variance(deg, n=20, trials=300):
    x = np.linspace(0, 1, n)                   # 输入固定，只有噪声每次重抽
    preds = np.empty((trials, len(x_grid)))
    for t in range(trials):                    # 每次抽一份全新的训练集
        y = f(x) + sigma * rng.normal(size=n)
        preds[t] = poly_fit_predict(x, y, deg, x_grid)
    bias2 = np.mean((preds.mean(axis=0) - f(x_grid)) ** 2)
    var = np.mean(preds.var(axis=0))
    y_new = f(x_grid) + sigma * rng.normal(size=preds.shape)   # 带噪声的新标签
    return bias2, var, np.mean((preds - y_new) ** 2)

for deg in [0, 1, 3, 5, 9]:
    b2, v, mse = bias_variance(deg)
    print(f"deg={deg}: bias2={b2:.3f} var={v:.3f} noise={sigma**2:.3f} "
          f"三项之和={b2+v+sigma**2:.3f} 实测MSE={mse:.3f}")
''')

C_BV2 = nb.cell('''
# 固定 9 次多项式（容易过拟合），只改变训练集大小 n
for n in [12, 20, 40, 80, 160]:
    b2, v, mse = bias_variance(9, n=n)
    print(f"n={n:3d}: bias2={b2:.3f} var={v:.3f} 实测MSE={mse:.3f}")
''')

# ───── 岭回归 ─────
C_R1 = nb.cell('''
def make_data(n, seed):
    r = np.random.default_rng(seed)
    x = r.uniform(0, 1, n)
    return x, f(x) + sigma * r.normal(size=n)

def poly_feats(x, deg=9):                      # 特征 x, x^2, ..., x^deg（不含常数列）
    return np.column_stack([x ** k for k in range(1, deg + 1)])

def ridge_fit(X, y, lam):
    mu, sd = X.mean(0), X.std(0)               # 标准化后惩罚才公平
    Z, yc = (X - mu) / sd, y - y.mean()        # 截距 b 不惩罚：先把 y 中心化
    w = np.linalg.solve(Z.T @ Z + lam * np.eye(Z.shape[1]), Z.T @ yc)   # 闭式解
    return mu, sd, y.mean(), w

def ridge_predict(m, X):
    mu, sd, b, w = m
    return b + ((X - mu) / sd) @ w

x_tr, y_tr = make_data(20, 1)
x_te, y_te = make_data(200, 2)
Xtr, Xte = poly_feats(x_tr), poly_feats(x_te)
for lam in [1e-8, 1e-3, 1e-1, 1, 10, 100]:
    m = ridge_fit(Xtr, y_tr, lam)
    tr = np.mean((ridge_predict(m, Xtr) - y_tr) ** 2)
    te = np.mean((ridge_predict(m, Xte) - y_te) ** 2)
    print(f"lam={lam:<6g} 训练MSE={tr:.3f} 测试MSE={te:.3f} |w|={np.linalg.norm(m[3]):.1f}")
''')

C_R2 = nb.cell('''
# 同一个目标用梯度下降求：L(w) = 1/2 |yc - Zw|^2 + 1/2 lam |w|^2
lam = 1.0
mu, sd = Xtr.mean(0), Xtr.std(0)
Z, yc = (Xtr - mu) / sd, y_tr - y_tr.mean()
w = np.zeros(Z.shape[1])
lr = 1 / np.linalg.eigvalsh(Z.T @ Z + lam * np.eye(9)).max()   # 步长取 1/L
for step in range(20000):
    grad = -Z.T @ (yc - Z @ w) + lam * w       # 数据项的梯度 + lam * w
    w = w - lr * grad                          # 等价于 w <- (1 - lr*lam) w + lr * Z^T (yc - Zw)
w_closed = ridge_fit(Xtr, y_tr, lam)[3]
print("与闭式解一致:", np.abs(w - w_closed).max() < 1e-6)
''')

C_R2T = nb.cell('''
import torch                                   # 这块只显示，网页里不运行
Zt, yt = torch.tensor(Z), torch.tensor(yc)
wt = torch.zeros(9, dtype=torch.float64, requires_grad=True)
opt = torch.optim.SGD([wt], lr=float(lr), weight_decay=lam)   # weight_decay 就是 L2 正则
for step in range(20000):
    opt.zero_grad()
    loss = 0.5 * ((yt - Zt @ wt) ** 2).sum()   # 只写数据项，L2 项由 weight_decay 加进梯度
    loss.backward()
    opt.step()
print(np.abs(wt.detach().numpy() - w_closed).max() < 1e-6)
''', static=True)

C_R3 = nb.cell('''
U, s, Vt = np.linalg.svd(Z, full_matrices=False)           # Z = U diag(s) V^T
shrink = s ** 2 / (s ** 2 + lam)               # 每个奇异方向被压缩的比例
w_svd = Vt.T @ ((s / (s ** 2 + lam)) * (U.T @ yc))
print("奇异值      :", np.round(s, 2))
print("压缩比例    :", np.round(shrink, 3))
print("与闭式解一致:", np.allclose(w_svd, w_closed))
''')

C_R4 = nb.cell('''
# 用重复采样看 lam 对偏差、方差的影响（9 次多项式，n=20，300 份训练集）
def ridge_bias_variance(lam, n=20, trials=300):
    r = np.random.default_rng(10)
    x, Xg = np.linspace(0, 1, n), poly_feats(x_grid)
    preds = np.empty((trials, len(x_grid)))
    for t in range(trials):
        y = f(x) + sigma * r.normal(size=n)
        preds[t] = ridge_predict(ridge_fit(poly_feats(x), y, lam), Xg)
    return np.mean((preds.mean(0) - f(x_grid)) ** 2), np.mean(preds.var(0))

for lam in [1e-6, 1e-3, 1e-1, 1, 10, 100]:
    b2, v = ridge_bias_variance(lam)
    print(f"lam={lam:<6g} bias2={b2:.3f} var={v:.3f} 合计={b2+v:.3f}")
''')

# ───── Lasso ─────
C_L1 = nb.cell('''
def soft(z, t):                                # 软阈值：把 z 向 0 收缩 t，不够 t 就变成 0
    return np.sign(z) * np.maximum(np.abs(z) - t, 0)

def lasso_cd(Z, y, lam, sweeps=300):           # 目标：1/2 |y - Zw|^2 + lam |w|_1
    w = np.zeros(Z.shape[1])
    r = y - Z @ w                              # 当前残差
    col = (Z ** 2).sum(0)
    for _ in range(sweeps):
        for j in range(Z.shape[1]):            # 一次只优化一个坐标，其余固定
            r += Z[:, j] * w[j]                # 把第 j 个特征的贡献还给残差
            w[j] = soft(Z[:, j] @ r, lam) / col[j]
            r -= Z[:, j] * w[j]
    return w

rng = np.random.default_rng(3)
n, p = 100, 20
X = rng.normal(size=(n, p))
w_true = np.zeros(p); w_true[[0, 3, 7, 12]] = [3, -2, 1.5, 2]  # 只有 4 个特征有用
y = X @ w_true + rng.normal(size=n)
Zl = (X - X.mean(0)) / X.std(0); yl = y - y.mean()
w_l = lasso_cd(Zl, yl, lam=30)
print("非零坐标:", np.nonzero(w_l)[0])
print("非零系数:", np.round(w_l[np.nonzero(w_l)], 2))
''')

C_L2 = nb.cell('''
# 最优性（KKT）检查：非零坐标满足 Z_j^T r = lam * sign(w_j)，零坐标满足 |Z_j^T r| <= lam
r = yl - Zl @ w_l
g = Zl.T @ r
print("非零坐标上 |g| 与 lam 的最大偏差:", round(np.abs(np.abs(g[w_l != 0]) - 30).max(), 6))
print("零坐标上 |g| 的最大值:", round(np.abs(g[w_l == 0]).max(), 2))

# 与岭回归对比：同样的数据，岭回归的 20 个系数一个都不会是 0
w_r = np.linalg.solve(Zl.T @ Zl + 30 * np.eye(p), Zl.T @ yl)
print("岭回归 lam=30 的非零个数:", np.sum(np.abs(w_r) > 1e-8))
for lam in [1, 10, 30, 60, 120, 400]:
    w = lasso_cd(Zl, yl, lam)
    print(f"lasso lam={lam:<4d} 非零个数={np.sum(w != 0):2d}")
''')

# ───── 交叉验证 ─────
C_CV1 = nb.cell('''
def kfold_indices(n, k, seed=0):
    idx = np.random.default_rng(seed).permutation(n)   # 先打乱，再切成 k 份
    return np.array_split(idx, k)

def cv_mse(X, y, lam, k=5, seed=0):
    folds, errs = kfold_indices(len(y), k, seed), []
    for i in range(k):
        va = folds[i]                                   # 第 i 份当验证集
        tr = np.concatenate([folds[j] for j in range(k) if j != i])
        m = ridge_fit(X[tr], y[tr], lam)                # 标准化也只用训练折
        errs.append(np.mean((ridge_predict(m, X[va]) - y[va]) ** 2))
    return np.mean(errs), np.std(errs)

x_a, y_a = make_data(40, 3)                    # 训练 + 验证用的 40 个点
Xa = poly_feats(x_a)
grid = [10.0 ** e for e in range(-6, 3)]
for lam in grid:
    mean, std = cv_mse(Xa, y_a, lam)
    print(f"lam={lam:<8g} 5 折平均 MSE={mean:.3f} (折间标准差 {std:.3f})")
''')

C_CV2 = nb.cell('''
best = min(grid, key=lambda lam: cv_mse(Xa, y_a, lam)[0])
m = ridge_fit(Xa, y_a, best)                   # 选定 lam 后，用全部 40 个点重新训练
print("交叉验证选出的 lam:", best)
print("测试集 MSE（只看这一次）:", round(np.mean((ridge_predict(m, Xte) - y_te) ** 2), 3))

# 对比：只用一次随机划分（30 训练 / 10 验证），换 6 个种子选出的 lam 会怎样？
for seed in range(6):
    perm = np.random.default_rng(100 + seed).permutation(40)
    tr, va = perm[:30], perm[30:]
    errs = [np.mean((ridge_predict(ridge_fit(Xa[tr], y_a[tr], l), Xa[va]) - y_a[va]) ** 2)
            for l in grid]
    print("单次划分选出的 lam:", grid[int(np.argmin(errs))])
''')

# ───── 学习曲线 ─────
C_LC = nb.cell('''
x_pool, y_pool = make_data(200, 5)
x_val, y_val = make_data(400, 6)
Xp, Xv = poly_feats(x_pool), poly_feats(x_val)

def curve(deg, lam, sizes, reps=30):
    out = []
    for n in sizes:
        tr_err, va_err = [], []
        for rep in range(reps):                         # 每个 n 重复抽样取平均
            idx = np.random.default_rng(rep).choice(200, n, replace=False)
            m = ridge_fit(Xp[idx][:, :deg], y_pool[idx], lam)
            tr_err.append(np.mean((ridge_predict(m, Xp[idx][:, :deg]) - y_pool[idx]) ** 2))
            va_err.append(np.mean((ridge_predict(m, Xv[:, :deg]) - y_val) ** 2))
        out.append((n, np.mean(tr_err), np.mean(va_err)))
    return out

for deg, name in [(1, "1 次（偏差大）"), (9, "9 次（方差大）")]:
    print(name)
    for n, tr, va in curve(deg, 1e-4, [12, 20, 40, 80, 160]):
        print(f"  n={n:3d} 训练MSE={tr:.3f} 验证MSE={va:.3f}")
''')

# ───── 超参数搜索 ─────
C_HP = nb.cell('''
def cv_cfg(deg, lam):                           # 一组超参数的 5 折交叉验证误差
    return cv_mse(poly_feats(x_a, deg), y_a, lam)[0]

degs, lams = [1, 3, 5, 7, 9], [1e-6, 1e-3, 1e-1, 10.0]
grid_cfgs = [(d, l) for d in degs for l in lams]          # 网格：5 x 4 = 20 组
r = np.random.default_rng(7)
rand_cfgs = [(int(r.integers(1, 10)), 10 ** r.uniform(-6, 2))   # 随机：同样 20 组
             for _ in range(20)]
for name, cfgs in [("网格", grid_cfgs), ("随机", rand_cfgs)]:
    scores = [cv_cfg(d, l) for d, l in cfgs]
    d, l = cfgs[int(np.argmin(scores))]
    m = ridge_fit(poly_feats(x_a, d), y_a, l)
    te = np.mean((ridge_predict(m, poly_feats(x_te, d)) - y_te) ** 2)
    n_lam = len(set(round(c[1], 9) for c in cfgs))
    print(f"{name}: {n_lam} 个不同 lam，最好 CV={min(scores):.3f}，"
          f"deg={d} lam={l:.2g}，测试MSE={te:.3f}")
''')

# ───── 数据泄漏 ─────
C_LEAK1 = nb.cell('''
rng = np.random.default_rng(0)
n, p = 50, 2000
X = rng.normal(size=(n, p))                    # 2000 个纯噪声特征
y = rng.integers(0, 2, n) * 2 - 1              # 随机 ±1 标签：理论上没有任何规律

def top_k(X, y, k=20):                         # 选出与标签相关性最大的 k 个特征
    return np.argsort(-np.abs((X - X.mean(0)).T @ (y - y.mean())))[:k]

def centroid_acc(Xtr, ytr, Xva, yva):          # 最近类中心分类器
    c1, c0 = Xtr[ytr == 1].mean(0), Xtr[ytr == -1].mean(0)
    pred = np.where(((Xva - c0) ** 2).sum(1) > ((Xva - c1) ** 2).sum(1), 1, -1)
    return np.mean(pred == yva)

def cv_acc(leaky, k=5):
    sel_all = top_k(X, y)                      # 泄漏：用了全部样本（含验证折）的标签
    folds, accs = kfold_indices(n, k), []
    for i in range(k):
        va = folds[i]
        tr = np.concatenate([folds[j] for j in range(k) if j != i])
        cols = sel_all if leaky else top_k(X[tr], y[tr])   # 正确：只用训练折选特征
        accs.append(centroid_acc(X[tr][:, cols], y[tr], X[va][:, cols], y[va]))
    return np.mean(accs)

print("先选特征再交叉验证（泄漏）:", round(cv_acc(True), 3))
print("折内选特征（正确）        :", round(cv_acc(False), 3))
''')

C_LEAK2 = nb.cell('''
# 重复测量：每个对象有 3 条几乎相同的记录，标签是随机的
rng = np.random.default_rng(1)
base = rng.normal(size=(300, 5)); ybase = rng.integers(0, 2, 300)
X = np.repeat(base, 3, axis=0) + 0.01 * rng.normal(size=(900, 5))
y = np.repeat(ybase, 3)
group = np.repeat(np.arange(300), 3)           # 记录属于哪个对象

def one_nn_acc(tr, te):
    d = ((X[te][:, None, :] - X[tr][None, :, :]) ** 2).sum(-1)
    return np.mean(y[tr][d.argmin(1)] == y[te])

perm = rng.permutation(900)                    # 按记录随机划分：同一对象的记录会跨训练 / 测试
print("按记录划分:", round(one_nn_acc(perm[:600], perm[600:]), 3))
g_perm = rng.permutation(300)                  # 按对象划分：同一对象只出现在一边
tr_mask = np.isin(group, g_perm[:200])
print("按对象划分:", round(one_nn_acc(np.nonzero(tr_mask)[0], np.nonzero(~tr_mask)[0]), 3))
''')

C_TEST = nb.cell('''
rng = np.random.default_rng(0)
y_test = rng.integers(0, 2, 100)               # 100 个测试标签
guesses = rng.integers(0, 2, (200, 100))       # 200 个“模型”：全是随机乱猜
acc = (guesses == y_test).mean(1)
best = int(acc.argmax())                       # 在测试集上挑最好的那个
print("200 个乱猜模型的平均测试准确率:", round(acc.mean(), 3))
print("挑出来的“最好”的测试准确率    :", round(acc[best], 3))
y_fresh = rng.integers(0, 2, 100)              # 一份从没看过的新数据
print("它在新数据上的准确率          :", round(np.mean(guesses[best] == y_fresh), 3))
''')
