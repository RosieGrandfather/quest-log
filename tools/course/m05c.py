from runlib import Notebook

nb = Notebook()

# ───── 不纯度 ─────
C_IMP = nb.cell('''
import numpy as np

def entropy(counts):                           # 熵（以 2 为底），counts 的最后一维是各类个数
    c = np.asarray(counts, float)
    p = c / c.sum(-1, keepdims=True)
    return 0.0 - (p * np.log2(np.where(p > 0, p, 1))).sum(-1)    # 约定 0 log 0 = 0

def gini(counts):                              # 基尼不纯度 = 1 - sum p_k^2
    c = np.asarray(counts, float)
    p = c / c.sum(-1, keepdims=True)
    return 1 - (p ** 2).sum(-1)

for counts in [[50, 50], [90, 10], [99, 1], [100, 0]]:
    print(counts, f"熵={entropy(counts):.3f} 基尼={gini(counts):.3f}")

# 信息增益：父节点 [40, 40]，按某个特征切成 [30, 10] 和 [10, 30]
gain = entropy([40, 40]) - 0.5 * entropy([30, 10]) - 0.5 * entropy([10, 30])
print(f"信息增益 = {gain:.3f}")
''')

# ───── 数据 ─────
C_DATA = nb.cell('''
def make_data(n, seed, n_noise=3):
    r = np.random.default_rng(seed)
    X = r.normal(size=(n, 3 + n_noise))        # 前 3 列有用，后面全是噪声
    y = ((X[:, 0] + X[:, 1] > 0) & (X[:, 2] > -0.5)).astype(int)
    flip = r.random(n) < 0.1                   # 10% 的标签被随机翻转
    return X, np.where(flip, 1 - y, y)

X_tr, y_tr = make_data(300, 0)
X_te, y_te = make_data(1000, 1)
print(X_tr.shape, "正类比例:", round(y_tr.mean(), 3))
''')

# ───── 最佳分裂 ─────
C_SPLIT = nb.cell('''
def best_split(X, y, feats=None, crit=entropy, K=2):
    n, tot = len(y), np.bincount(y, minlength=K)
    parent = crit(tot)
    best = (0.0, None, None)                   # (增益, 特征编号, 阈值)
    for j in (range(X.shape[1]) if feats is None else feats):
        o = np.argsort(X[:, j]); xs = X[o, j]
        left = np.cumsum(np.eye(K)[y[o]], axis=0)[:-1]   # 在第 i 个间隙切开：左边各类个数
        right = tot - left
        nl = np.arange(1, n)
        gain = parent - (nl * crit(left) + (n - nl) * crit(right)) / n
        gain[xs[:-1] == xs[1:]] = -1           # 取值相同的两点之间不能切
        i = gain.argmax()
        if gain[i] > best[0]:
            best = (gain[i], j, (xs[i] + xs[i + 1]) / 2)
    return best

g, j, t = best_split(X_tr, y_tr)
print(f"熵: 最佳特征 x{j}，阈值 {t:.3f}，信息增益 {g:.3f}")
g, j, t = best_split(X_tr, y_tr, crit=gini)
print(f"基尼: 最佳特征 x{j}，阈值 {t:.3f}，增益 {g:.3f}")
''')

# ───── 递归构树 ─────
C_TREE = nb.cell('''
def build_tree(X, y, depth=0, max_depth=3, min_samples=5, mtry=None, rng=None):
    counts = np.bincount(y, minlength=2)
    leaf = {"leaf": True, "pred": int(counts.argmax()), "counts": counts.tolist()}
    if depth >= max_depth or len(y) < min_samples or counts.max() == len(y):
        return leaf                            # 停止条件：够深 / 太少 / 已经纯了
    feats = None if mtry is None else rng.choice(X.shape[1], mtry, replace=False)
    gain, j, t = best_split(X, y, feats)       # mtry 留给后面的随机森林用
    if j is None:
        return leaf
    m = X[:, j] <= t
    return {"leaf": False, "j": j, "t": t,
            "left": build_tree(X[m], y[m], depth + 1, max_depth, min_samples, mtry, rng),
            "right": build_tree(X[~m], y[~m], depth + 1, max_depth, min_samples, mtry, rng)}

def predict_one(node, x):
    while not node["leaf"]:
        node = node["left"] if x[node["j"]] <= node["t"] else node["right"]
    return node["pred"]

def predict(tree, X):
    return np.array([predict_one(tree, x) for x in X])

def show(node, depth=0):
    pad = "  " * depth
    if node["leaf"]:
        print(f"{pad}预测 {node['pred']}  (类别个数 {node['counts']})")
    else:
        print(f"{pad}x{node['j']} <= {node['t']:.2f} ?")
        show(node["left"], depth + 1); show(node["right"], depth + 1)

tree2 = build_tree(X_tr, y_tr, max_depth=2)
show(tree2)
''')

C_DEPTH = nb.cell('''
def n_leaves(node):
    return 1 if node["leaf"] else n_leaves(node["left"]) + n_leaves(node["right"])

for d in [1, 2, 3, 5, 8, 30]:
    tr = build_tree(X_tr, y_tr, max_depth=d, min_samples=2)
    acc_tr = np.mean(predict(tr, X_tr) == y_tr)
    acc_te = np.mean(predict(tr, X_te) == y_te)
    print(f"max_depth={d:2d} 叶子数={n_leaves(tr):3d} 训练准确率={acc_tr:.3f} 测试准确率={acc_te:.3f}")
''')

# ───── 随机森林 ─────
C_BOOT = nb.cell('''
rng = np.random.default_rng(0)
for n in [10, 100, 10000]:
    idx = rng.integers(0, n, n)                # 自助采样：有放回抽 n 次
    print(f"n={n:5d}: 被抽到过的不同样本占 {len(np.unique(idx)) / n:.3f}")
print("理论值 1 - 1/e =", round(1 - 1 / np.e, 3))
''')

C_FOREST = nb.cell('''
def fit_forest(X, y, n_trees=50, mtry=None, max_depth=8, seed=0):
    rng = np.random.default_rng(seed)
    trees, oob = [], []
    for _ in range(n_trees):
        idx = rng.integers(0, len(y), len(y))              # 自助样本
        trees.append(build_tree(X[idx], y[idx], max_depth=max_depth, mtry=mtry, rng=rng))
        oob.append(np.setdiff1d(np.arange(len(y)), idx))   # 没被抽到的样本：袋外
    return trees, oob

def forest_predict(trees, X):                  # 多数投票
    return (np.mean([predict(t, X) for t in trees], axis=0) > 0.5).astype(int)

def oob_accuracy(trees, oob, X, y):            # 每个样本只让「没见过它」的树投票
    votes, cnt = np.zeros(len(y)), np.zeros(len(y))
    for t, o in zip(trees, oob):
        votes[o] += predict(t, X[o]); cnt[o] += 1
    m = cnt > 0
    return np.mean((votes[m] / cnt[m] > 0.5) == y[m])

single = build_tree(X_tr, y_tr, max_depth=8, min_samples=2)
print("单棵深树 测试准确率:", round(np.mean(predict(single, X_te) == y_te), 3))
for name, mtry in [("bagging(mtry=全部 6 个)", None), ("随机森林(mtry=2)", 2)]:
    trees, oob = fit_forest(X_tr, y_tr, mtry=mtry)
    print(f"{name}: 测试={np.mean(forest_predict(trees, X_te) == y_te):.3f} "
          f"袋外={oob_accuracy(trees, oob, X_tr, y_tr):.3f}")
''')

# ───── 梯度提升 ─────
C_STUMP = nb.cell('''
def fit_stump(x, r):                           # 一维回归树桩：一个阈值，左右各取平均
    o = np.argsort(x); xs, rs = x[o], r[o]
    n, cs = len(x), np.cumsum(rs)[:-1]
    nl = np.arange(1, n)
    score = cs ** 2 / nl + (rs.sum() - cs) ** 2 / (n - nl)   # 最大化它 = 最小化平方误差
    score[xs[:-1] == xs[1:]] = -np.inf
    i = score.argmax()
    return (xs[i] + xs[i + 1]) / 2, rs[:i + 1].mean(), rs[i + 1:].mean()

def stump_predict(s, x):
    return np.where(x <= s[0], s[1], s[2])

r = np.random.default_rng(0)
xb = r.uniform(0, 6, 200); yb = np.sin(xb) + 0.3 * r.normal(size=200)
xt = np.linspace(0, 6, 300); yt = np.sin(xt)             # 无噪声的真曲线
s = fit_stump(xb, yb - yb.mean())
print(f"第一个树桩：x <= {s[0]:.2f} 取 {s[1]:.3f}，否则取 {s[2]:.3f}")
''')

C_BOOST = nb.cell('''
lr, F, Ft = 0.1, np.full(200, yb.mean()), np.full(300, yb.mean())   # F0 = 平均值
for m in range(1, 301):
    resid = yb - F                             # 残差 = 平方损失的负梯度
    s = fit_stump(xb, resid)                   # 用树桩拟合残差
    F, Ft = F + lr * stump_predict(s, xb), Ft + lr * stump_predict(s, xt)
    if m in (1, 5, 20, 50, 100, 300):
        print(f"M={m:3d} 训练MSE={np.mean((yb - F) ** 2):.3f} "
              f"对真曲线的MSE={np.mean((yt - Ft) ** 2):.3f}")
''')

# ───── kNN 与维数灾难 ─────
C_KNN = nb.cell('''
def knn_predict(Xtr, ytr, Xte, k):
    d = ((Xte[:, None, :] - Xtr[None, :, :]) ** 2).sum(-1)    # 所有测试点到所有训练点的距离平方
    nn = np.argsort(d, axis=1)[:, :k]                         # 每行取最近的 k 个
    return (ytr[nn].mean(1) > 0.5).astype(int)                # 多数投票

for k in [1, 3, 5, 15, 45]:
    acc_tr = np.mean(knn_predict(X_tr, y_tr, X_tr, k) == y_tr)
    acc_te = np.mean(knn_predict(X_tr, y_tr, X_te, k) == y_te)
    print(f"k={k:2d} 训练准确率={acc_tr:.3f} 测试准确率={acc_te:.3f}")
''')

C_CURSE1 = nb.cell('''
# 给数据再添加 m 个纯噪声特征，k=15 的 kNN 会怎样？
for m in [0, 10, 50, 200]:
    Xa, ya = make_data(300, 0, n_noise=3 + m)
    Xb, yb2 = make_data(1000, 1, n_noise=3 + m)
    print(f"多加 {m:3d} 个噪声特征: 测试准确率={np.mean(knn_predict(Xa, ya, Xb, 15) == yb2):.3f}")
''')

C_CURSE2 = nb.cell('''
r = np.random.default_rng(0)
for d in [2, 10, 100, 1000]:
    P = r.random((500, d))                     # 单位超立方体里的 500 个随机点
    q = r.random(d)
    dist = np.sqrt(((P - q) ** 2).sum(1))
    print(f"d={d:4d}: 最远/最近 = {dist.max() / dist.min():5.2f}  "
          f"要装下 1% 的数据，小方块边长需 {0.01 ** (1 / d):.3f}")
''')

# ───── 朴素贝叶斯 ─────
C_NB = nb.cell('''
def fit_gnb(X, y):                             # 每个类别、每个特征各拟合一个高斯
    return [(np.mean(y == c), X[y == c].mean(0), X[y == c].var(0) + 1e-9) for c in (0, 1)]

def predict_gnb(model, X):                     # log 先验 + 各特征的 log 似然之和（特征条件独立）
    scores = []
    for prior, mu, var in model:
        ll = -0.5 * (np.log(2 * np.pi * var) + (X - mu) ** 2 / var)
        scores.append(np.log(prior) + ll.sum(1))
    return np.argmax(scores, axis=0)

r = np.random.default_rng(0)                   # 数据 A：特征在类内相互独立，每个特征都有一点区分力
def blobs(n):
    return np.vstack([r.normal(0, 1, (n, 4)), r.normal(1, 1, (n, 4))]), np.repeat([0, 1], n)
(Xa, ya), (Xb, yb3) = blobs(200), blobs(500)
print("数据 A 朴素贝叶斯:", round(np.mean(predict_gnb(fit_gnb(Xa, ya), Xb) == yb3), 3))

def xor_data(n):                               # 数据 B：标签 = 两个特征符号的异或
    X = r.normal(size=(n, 2)); return X, ((X[:, 0] > 0) ^ (X[:, 1] > 0)).astype(int)
(Xc, yc), (Xd, yd) = xor_data(300), xor_data(1000)
print("数据 B 朴素贝叶斯:", round(np.mean(predict_gnb(fit_gnb(Xc, yc), Xd) == yd), 3))
for d in [2, 4]:
    tree = build_tree(Xc, yc, max_depth=d)
    print(f"数据 B 深度 {d} 的决策树:", round(np.mean(predict(tree, Xd) == yd), 3))
''')

# ───── SVM 与核技巧 ─────
C_KERNEL = nb.cell('''
def phi(x):                                    # 二维输入的显式二次特征映射（6 维）
    s2 = np.sqrt(2)
    return np.array([1, s2 * x[0], s2 * x[1], x[0] ** 2, x[1] ** 2, s2 * x[0] * x[1]])

def poly_kernel(x, z):                         # 核函数：不显式升维，直接算内积
    return (x @ z + 1) ** 2

r = np.random.default_rng(0)
x, z = r.normal(size=2), r.normal(size=2)
print("显式升到 6 维再做内积:", round(phi(x) @ phi(z), 6))
print("直接用核函数 (x·z+1)^2 :", round(poly_kernel(x, z), 6))
print("RBF 核 exp(-|x-z|^2/2)  :", round(float(np.exp(-0.5 * np.sum((x - z) ** 2))), 6))
''')
