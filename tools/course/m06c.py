from runlib import Notebook

nb = Notebook()

# ───── k-means ─────
C_KM1 = nb.cell('''
import numpy as np

r = np.random.default_rng(0)
centers_true = np.array([[0, 0], [3, 0], [8, 0], [8, 3.5]])      # 4 个簇，前两个靠得近
X = np.vstack([c + 0.8 * r.normal(size=(100, 2)) for c in centers_true])
print(X.shape)

def kmeans(X, init, n_iter=100):
    centers, history = init.copy(), []
    for _ in range(n_iter):
        d = ((X[:, None, :] - centers[None, :, :]) ** 2).sum(-1)    # 每个点到每个中心的距离平方
        labels = d.argmin(1)                                        # 分配步：归到最近的中心
        history.append(d[np.arange(len(X)), labels].sum())          # 目标函数 J（簇内平方和）
        new = np.array([X[labels == j].mean(0) if np.any(labels == j) else centers[j]
                        for j in range(len(centers))])              # 更新步：中心移到簇的均值
        if np.allclose(new, centers):
            break
        centers = new
    return centers, labels, history

init = X[r.choice(len(X), 4, replace=False)]
centers, labels, hist = kmeans(X, init)
print("迭代轮数:", len(hist), " J 的变化:", [round(float(h), 1) for h in hist])
print("J 单调不增:", all(a >= b - 1e-9 for a, b in zip(hist, hist[1:])))
print("最终中心:\\n", np.round(centers[np.argsort(centers[:, 0])], 2))
''')

C_KM2 = nb.cell('''
# 同一份数据，换 40 次随机初始化（从数据点里随机选 4 个当初始中心）
def final_J(init):
    return kmeans(X, init)[2][-1]

rng = np.random.default_rng(1)
Js = np.array([final_J(X[rng.choice(len(X), 4, replace=False)]) for _ in range(40)])
vals, counts = np.unique(np.round(Js, 0), return_counts=True)
for v, c in zip(vals, counts):
    print(f"最终 J ≈ {v:6.0f}  出现 {c:2d} 次")
''')

C_KM3 = nb.cell('''
def kmeanspp_init(X, k, rng):
    centers = [X[rng.integers(len(X))]]                    # 第一个中心：均匀随机
    for _ in range(k - 1):
        d2 = ((X[:, None, :] - np.array(centers)[None]) ** 2).sum(-1).min(1)   # 离最近已选中心的距离平方
        centers.append(X[rng.choice(len(X), p=d2 / d2.sum())])                 # 按 D^2 加权抽下一个
    return np.array(centers)

rng = np.random.default_rng(1)
Jp = np.array([final_J(kmeanspp_init(X, 4, rng)) for _ in range(40)])
vals, counts = np.unique(np.round(Jp, 0), return_counts=True)
for v, c in zip(vals, counts):
    print(f"k-means++ 最终 J ≈ {v:6.0f}  出现 {c:2d} 次")
print("随机初始化 J 的平均:", round(Js.mean(), 1), " k-means++:", round(Jp.mean(), 1))
''')

C_KM4 = nb.cell('''
def best_of(X, k, n_init=10, seed=0):                      # 多次初始化取 J 最小的一次
    rng = np.random.default_rng(seed)
    runs = [kmeans(X, kmeanspp_init(X, k, rng)) for _ in range(n_init)]
    return min(runs, key=lambda t: t[2][-1])

for k in range(1, 9):
    J = best_of(X, k)[2][-1]
    print(f"k={k}: J={J:8.1f}")
''')

C_KM5 = nb.cell('''
def silhouette(X, labels):
    D = np.sqrt(((X[:, None, :] - X[None, :, :]) ** 2).sum(-1))
    s = np.zeros(len(X))
    for i in range(len(X)):
        same = (labels == labels[i]); same[i] = False
        a = D[i, same].mean()                              # 簇内平均距离
        b = min(D[i, labels == c].mean() for c in set(labels) if c != labels[i])   # 最近别的簇的平均距离
        s[i] = (b - a) / max(a, b)
    return s.mean()

for k in range(2, 8):
    labels_k = best_of(X, k)[1]
    print(f"k={k}: 平均轮廓系数 = {silhouette(X, labels_k):.3f}")
''')

# ───── 高斯混合模型与 EM ─────
C_GMM1 = nb.cell('''
r = np.random.default_rng(0)
z = r.random(600) < 0.4                                    # 隐变量：来自哪个成分（我们看不到）
x = np.where(z, r.normal(-2, 0.8, 600), r.normal(3, 1.2, 600))   # 观测
print("真实参数: pi=(0.4, 0.6), mu=(-2, 3), sigma=(0.8, 1.2)")

def normal_pdf(x, mu, var):
    return np.exp(-0.5 * (x - mu) ** 2 / var) / np.sqrt(2 * np.pi * var)

def em_step(x, pi, mu, var):
    dens = pi * normal_pdf(x[:, None], mu, var)            # (n, K)：pi_k N(x_i | mu_k, var_k)
    loglik = np.log(dens.sum(1)).sum()                     # 当前参数下的对数似然
    resp = dens / dens.sum(1, keepdims=True)               # E 步：责任 gamma_ik = P(z=k | x_i)
    Nk = resp.sum(0)                                       # M 步：用责任当权重重新估计参数
    mu = (resp * x[:, None]).sum(0) / Nk
    var = (resp * (x[:, None] - mu) ** 2).sum(0) / Nk
    return Nk / len(x), mu, var, loglik
''')

C_GMM2 = nb.cell('''
pi, mu, var = np.array([0.5, 0.5]), np.array([x.min(), x.max()]), np.array([1.0, 1.0])
logliks = []
for it in range(1, 61):
    pi, mu, var, ll = em_step(x, pi, mu, var)
    logliks.append(ll)
    if it in (1, 2, 3, 5, 10, 30, 60):
        print(f"迭代 {it:2d}: 对数似然={ll:9.3f} pi={np.round(pi, 3)} mu={np.round(mu, 2)}")
print("对数似然单调不减:", all(b >= a - 1e-9 for a, b in zip(logliks, logliks[1:])))
print("估计的 sigma:", np.round(np.sqrt(var), 2))
''')

# ───── PCA ─────
C_PCA1 = nb.cell('''
r = np.random.default_rng(0)
n = 500
Z = r.normal(size=(n, 2)) * np.array([3.0, 1.0])           # 2 个隐变量，尺度 3 和 1
W = r.normal(size=(2, 5))                                  # 线性地混合进 5 个观测特征
X5 = Z @ W + 0.3 * r.normal(size=(n, 5))                   # 再加一点噪声
Xc = X5 - X5.mean(0)                                       # 第一步：中心化

S = Xc.T @ Xc / (n - 1)                                    # 协方差矩阵 (5 x 5)
evals, evecs = np.linalg.eigh(S)                           # eigh 给的是升序，翻成降序
evals, evecs = evals[::-1], evecs[:, ::-1]
print("特征值（各主成分方向上的方差）:", np.round(evals, 3))
print("解释方差比:", np.round(evals / evals.sum(), 3))
print("累计解释方差比:", np.round(np.cumsum(evals) / evals.sum(), 3))
''')

C_PCA2 = nb.cell('''
U, s, Vt = np.linalg.svd(Xc, full_matrices=False)          # Xc = U diag(s) V^T
print("奇异值平方 / (n-1) 与协方差特征值一致:", np.allclose(s ** 2 / (n - 1), evals))
print("V 的列与特征向量一致（至多差一个符号）:", np.allclose(np.abs(Vt.T), np.abs(evecs)))
scores = Xc @ evecs[:, :2]                                 # 投影到前 2 个主成分：每个样本的新坐标
print("得分的方差:", np.round(scores.var(0, ddof=1), 3))
print("得分之间的协方差接近 0:", abs(np.cov(scores.T)[0, 1]) < 1e-9)
''')

C_PCA3 = nb.cell('''
# 两种推导的数值检验：最大方差 / 最小重构误差
rng = np.random.default_rng(1)
dirs = rng.normal(size=(2000, 5)); dirs /= np.linalg.norm(dirs, axis=1, keepdims=True)
var_along = np.array([(Xc @ d).var(ddof=1) for d in dirs])
print(f"随机单位方向上的投影方差: 最大 {var_along.max():.3f} <= 第一特征值 {evals[0]:.3f}")

for k in range(1, 5):
    Vk = evecs[:, :k]
    err = ((Xc - Xc @ Vk @ Vk.T) ** 2).sum() / (n - 1)     # 重构误差（平方和 / (n-1)）
    print(f"保留 k={k}: 重构误差={err:.4f}  被丢掉的特征值之和={evals[k:].sum():.4f}")
''')

C_PCA4 = nb.cell('''
r = np.random.default_rng(2)
Z = r.normal(size=(400, 5)) * np.array([5, 3, 2, 1, 0.5])  # 5 个隐变量，强度递减
Xh = Z @ r.normal(size=(5, 30)) + 0.5 * r.normal(size=(400, 30))   # 观测是 30 维
Xh = Xh - Xh.mean(0)
sv = np.linalg.svd(Xh, compute_uv=False)
ratio = sv ** 2 / (sv ** 2).sum()
cum = np.cumsum(ratio)
print("前 8 个主成分的解释方差比:", np.round(ratio[:8], 3))
print("累计:", np.round(cum[:8], 3))
for target in (0.80, 0.95, 0.99):
    print(f"累计解释方差达到 {target:.0%} 需要 {int(np.searchsorted(cum, target)) + 1} 个主成分")
''')

C_AE = nb.cell('''
# 线性自编码器：5 维 -> 2 维 -> 5 维，用梯度下降最小化重构误差（没有任何非线性）
rng = np.random.default_rng(0)
We = 0.1 * rng.normal(size=(5, 2)); Wd = 0.1 * rng.normal(size=(2, 5))
lr = 0.01
for step in range(5000):
    H = Xc @ We                                            # 编码
    R = H @ Wd - Xc                                        # 解码后的重构残差
    gWd = H.T @ R * (2 / n); gWe = Xc.T @ (R @ Wd.T) * (2 / n)
    Wd -= lr * gWd; We -= lr * gWe

mse = np.mean(((Xc @ We @ Wd - Xc) ** 2).sum(1))
pca_mse = evals[2:].sum() * (n - 1) / n                    # PCA 在 k=2 时的最小可能值
print(f"线性自编码器的重构误差 {mse:.4f}  PCA 的最小值 {pca_mse:.4f}")
Q_ae, _ = np.linalg.qr(Wd.T)                               # 解码器张成的 2 维子空间
P_ae, P_pca = Q_ae @ Q_ae.T, evecs[:, :2] @ evecs[:, :2].T
print("两个子空间的投影矩阵之差（Frobenius 范数）:", round(float(np.linalg.norm(P_ae - P_pca)), 4))
''')
