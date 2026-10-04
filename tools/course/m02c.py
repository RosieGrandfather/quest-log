from runlib import Notebook

nb = Notebook()

# ───── 模型与损失 ─────
C_DATA = nb.cell('''
import numpy as np

rng = np.random.default_rng(0)
n, d = 200, 3
X = rng.normal(size=(n, d))                          # 200 个样本，3 个特征
w_true, b_true = np.array([2.0, -1.0, 0.5]), 3.0
y = X @ w_true + b_true + rng.normal(0, 0.5, n)      # 真实规律 + 标准差 0.5 的噪声

def predict(X, w, b):                                # 模型：y_hat = X w + b
    return X @ w + b

def mse(y, yhat):                                    # 均方误差
    return float(np.mean((y - yhat) ** 2))

print(X.shape, y.shape)
print("用真实参数的 MSE：", round(mse(y, predict(X, w_true, b_true)), 3))
print("w=0, b=0 的 MSE：", round(mse(y, predict(X, np.zeros(d), 0.0)), 3))
''')

# ───── 梯度 ─────
C_GRAD = nb.cell('''
def grad(w, b, X, y):
    r = X @ w + b - y                                # 残差 r = y_hat - y，形状 (n,)
    m = len(y)
    return 2 / m * (X.T @ r), 2 / m * r.sum()        # dL/dw = (2/n) X^T r,  dL/db = (2/n) sum(r)

def loss(w, b, X, y):
    return float(np.mean((X @ w + b - y) ** 2))

w0, b0 = np.array([0.5, 0.5, 0.5]), 0.5
gw, gb = grad(w0, b0, X, y)
eps = 1e-6                                           # 用中心差分做数值检验
num_w = np.zeros(d)
for j in range(d):
    e = np.zeros(d); e[j] = eps
    num_w[j] = (loss(w0 + e, b0, X, y) - loss(w0 - e, b0, X, y)) / (2 * eps)
num_b = (loss(w0, b0 + eps, X, y) - loss(w0, b0 - eps, X, y)) / (2 * eps)
print(np.round(gw, 4), round(gb, 4))
print(np.round(num_w, 4), round(num_b, 4))
print(np.allclose(gw, num_w, atol=1e-6), abs(gb - num_b) < 1e-6)
''')

# ───── 正规方程 ─────
C_NORMAL = nb.cell('''
Xa = np.hstack([np.ones((n, 1)), X])                 # 增广矩阵：加一列 1，把 b 并进参数
theta = np.linalg.solve(Xa.T @ Xa, Xa.T @ y)         # 正规方程 (X^T X) theta = X^T y
print(np.round(theta, 3))                            # 依次是 b, w1, w2, w3
theta_ls = np.linalg.lstsq(Xa, y, rcond=None)[0]     # 最小二乘的另一种求法
print(np.allclose(theta, theta_ls))
gw, gb = grad(theta[1:], theta[0], X, y)
print("解处的梯度几乎为 0：", np.abs(gw).max() < 1e-10 and abs(gb) < 1e-10)
''')

# ───── 批量梯度下降 ─────
C_GD = nb.cell('''
def gd(X, y, lr, steps):
    w, b, hist = np.zeros(X.shape[1]), 0.0, []
    for t in range(steps):
        gw, gb = grad(w, b, X, y)
        w, b = w - lr * gw, b - lr * gb              # 沿负梯度方向走一步
        hist.append(loss(w, b, X, y))
    return w, b, hist

w, b, h = gd(X, y, 0.1, 200)
print(np.round(w, 3), round(b, 3))
print("第 1、10、50、200 步的损失：", [round(h[i], 4) for i in (0, 9, 49, 199)])
print("和正规方程一致：", np.allclose(np.r_[b, w], theta, atol=1e-3))
''')

# ───── 学习率 ─────
C_LR = nb.cell('''
H = 2 / n * Xa.T @ Xa                                # 损失的 Hessian（二阶导矩阵）
lam = np.linalg.eigvalsh(H)
print("Hessian 最大特征值：", round(float(lam.max()), 3), " 稳定学习率上界 2/L：", round(float(2 / lam.max()), 3))
for lr in [0.001, 0.1, 0.9, 1.1]:
    _, _, h = gd(X, y, lr, 50)
    print(f"lr={lr:<6}  第 50 步损失 = {h[-1]:.4g}")
''')

# ───── 小批量 ─────
C_SGD = nb.cell('''
def sgd(X, y, lr, epochs, bs, seed=0):
    r = np.random.default_rng(seed)
    w, b = np.zeros(X.shape[1]), 0.0
    for ep in range(epochs):
        idx = r.permutation(len(y))                  # 每个 epoch 先打乱一遍
        for s in range(0, len(y), bs):
            j = idx[s:s + bs]                        # 这一个小批量的样本下标
            gw, gb = grad(w, b, X[j], y[j])          # 只用这几个样本估计梯度
            w, b = w - lr * gw, b - lr * gb
    return w, b

print("批量大小   损失     离正规方程解的距离")
for bs, lr in [(200, 0.1), (32, 0.05), (1, 0.01)]:
    w, b = sgd(X, y, lr, 20, bs)
    dist = np.linalg.norm(np.r_[b, w] - theta)
    print(f"{bs:<10d} {loss(w, b, X, y):.4f}   {dist:.4f}")
''')

# ───── 特征缩放 ─────
C_SCALE = nb.cell('''
rng = np.random.default_rng(1)
x1 = rng.normal(size=n)                              # 量级 1 的特征（比如件数）
x2 = rng.normal(size=n) * 100 + 500                  # 量级 100 的特征（比如重量，单位克）
Xr = np.c_[x1, x2]
yr = 3 * x1 + 0.02 * x2 + 1 + rng.normal(0, 0.5, n)

def cond(Xm):                                        # Hessian 的条件数 = 最大特征值 / 最小特征值
    A = np.c_[np.ones(len(Xm)), Xm]
    e = np.linalg.eigvalsh(2 / len(Xm) * A.T @ A)
    return e.max() / e.min()

mu, sd = Xr.mean(axis=0), Xr.std(axis=0)             # 用训练集的均值和标准差标准化
Xs = (Xr - mu) / sd
print("条件数：原始", f"{cond(Xr):.3g}", " 标准化后", round(cond(Xs), 3))
for name, Xm, lr in [("原始 ", Xr, 3e-6), ("标准化", Xs, 0.3)]:   # 各自取不发散的最大学习率附近
    _, _, h = gd(Xm, yr, lr, 300)
    print(f"{name} 300 步后的损失：{h[-1]:.4f}")
''')

# ───── 向量化 ─────
C_VEC = nb.cell('''
def grad_loop(w, b, X, y):                           # 两层 Python 循环的版本，慢但直观
    m, k = X.shape
    gw, gb = np.zeros(k), 0.0
    for i in range(m):
        r = b - y[i]
        for j in range(k):
            r += X[i, j] * w[j]                      # r = y_hat_i - y_i
        for j in range(k):
            gw[j] += 2 / m * r * X[i, j]
        gb += 2 / m * r
    return gw, gb

gw1, gb1 = grad_loop(w0, b0, X, y)
gw2, gb2 = grad(w0, b0, X, y)                        # 前面写的向量化版本
print(np.allclose(gw1, gw2), np.isclose(gb1, gb2))
''')

# ───── 多项式特征 ─────
C_POLY = nb.cell('''
rng = np.random.default_rng(42)
xs = rng.uniform(0, 1, 40)
ys = np.sin(2 * np.pi * xs) + rng.normal(0, 0.3, 40)
xtr, ytr, xva, yva = xs[:20], ys[:20], xs[20:], ys[20:]

def poly_features(x, deg):
    t = 2 * x - 1                                    # 先把 x 从 [0,1] 缩放到 [-1,1]
    return np.vander(t, deg + 1, increasing=True)    # 列依次是 1, t, t^2, ..., t^deg

P = poly_features(xtr, 3)
coef = np.linalg.solve(P.T @ P, P.T @ ytr)           # 对「特征」仍然是线性回归
print(np.round(coef, 3))
print(np.allclose(coef, np.polyfit(2 * xtr - 1, ytr, 3)[::-1]))   # 与 np.polyfit 一致（它把高次项放前面）
print("训练 MSE：", round(mse(ytr, P @ coef), 3), " 验证 MSE：", round(mse(yva, poly_features(xva, 3) @ coef), 3))
''')

C_RIDGE = nb.cell('''
def ridge_fit(P, y, lam):                            # 最小化 MSE + lam * ||w||^2（常数项不惩罚）
    k = P.shape[1]
    R = lam * np.eye(k); R[0, 0] = 0
    return np.linalg.solve(P.T @ P + len(y) * R, P.T @ y)

P9, V9 = poly_features(xtr, 9), poly_features(xva, 9)
print("lambda    训练MSE  验证MSE")
for lam in [0, 1e-6, 1e-4, 1e-2, 1]:
    c = ridge_fit(P9, ytr, lam)
    print(f"{lam:<9g} {mse(ytr, P9 @ c):.3f}    {mse(yva, V9 @ c):.3f}")
''')

# ───── R^2 ─────
C_R2 = nb.cell('''
def r2(y, yhat):
    ss_res = np.sum((y - yhat) ** 2)                 # 模型没解释掉的部分
    ss_tot = np.sum((y - y.mean()) ** 2)             # 总变化量（相对于均值）
    return float(1 - ss_res / ss_tot)

P3, V3 = poly_features(xtr, 3), poly_features(xva, 3)
c3 = ridge_fit(P3, ytr, 0)
print("3 次  训练 R2：", round(r2(ytr, P3 @ c3), 3), " 验证 R2：", round(r2(yva, V3 @ c3), 3))
print("基线（永远预测训练均值）验证 R2：", round(r2(yva, np.full_like(yva, ytr.mean())), 3))
P1, V1 = poly_features(xtr, 1), poly_features(xva, 1)
print("1 次  验证 R2：", round(r2(yva, V1 @ ridge_fit(P1, ytr, 0)), 3))
print("9 次（无正则）  训练 R2：", round(r2(ytr, P9 @ ridge_fit(P9, ytr, 0)), 3), " 验证 R2：", round(r2(yva, V9 @ ridge_fit(P9, ytr, 0)), 3))
''')
