from runlib import Notebook

nb = Notebook()

# ───── 为什么不用线性回归 ─────
C_LINBAD = nb.cell('''
import numpy as np

rng = np.random.default_rng(0)
x = np.r_[rng.normal(-1, 1, 50), rng.normal(2, 1, 50)]   # 一个特征
y = np.r_[np.zeros(50), np.ones(50)]                     # 标签只有 0 和 1
A = np.c_[np.ones(100), x]
theta = np.linalg.solve(A.T @ A, A.T @ y)                # 直接用上一节的线性回归
p = A @ theta
print("截距、斜率：", np.round(theta, 3))
print("预测值范围：", round(float(p.min()), 3), "到", round(float(p.max()), 3))
print("小于 0 的个数：", int((p < 0).sum()), " 大于 1 的个数：", int((p > 1).sum()))
''')

# ───── sigmoid ─────
C_SIG = nb.cell('''
def sigmoid(z):                                      # 数值稳定的写法：z 为很大的负数时不会溢出
    z = np.asarray(z, dtype=float)
    out = np.empty_like(z)
    pos = z >= 0
    out[pos] = 1 / (1 + np.exp(-z[pos]))
    ez = np.exp(z[~pos])
    out[~pos] = ez / (1 + ez)
    return out

z = np.array([-10.0, -2.0, 0.0, 2.0, 10.0])
print(np.round(sigmoid(z), 4))
print(sigmoid(np.array([-1000.0, 1000.0])))          # 极端输入也不报溢出
print("对称性 s(-z) = 1 - s(z)：", np.allclose(sigmoid(-z), 1 - sigmoid(z)))
h = 1e-6
num = (sigmoid(z + h) - sigmoid(z - h)) / (2 * h)    # 数值导数
print("导数 s' = s(1 - s)：", np.allclose(num, sigmoid(z) * (1 - sigmoid(z)), atol=1e-8))
''')

C_ODDS = nb.cell('''
p = np.array([0.2, 0.5, 0.8, 0.99])
odds = p / (1 - p)                                   # 几率：发生 / 不发生
logit = np.log(odds)                                 # 对数几率，sigmoid 的反函数
print(np.round(odds, 3))
print(np.round(logit, 3))
print("sigmoid(logit) 还原概率：", np.allclose(sigmoid(logit), p))
''')

# ───── 交叉熵 ─────
C_NLL = nb.cell('''
y_t = np.array([1, 0, 1, 1, 0])                      # 真实标签
p = np.array([0.9, 0.2, 0.6, 0.3, 0.05])             # 模型给出的 P(y=1)
like = np.prod(np.where(y_t == 1, p, 1 - p))         # 每个样本取「真实类别的概率」，再连乘 = 似然
nll = -np.log(like) / len(y_t)                       # 平均负对数似然
bce = -np.mean(y_t * np.log(p) + (1 - y_t) * np.log(1 - p))   # 二元交叉熵公式
print(round(float(like), 5), round(float(nll), 4), round(float(bce), 4), np.isclose(nll, bce))
for q in [0.9, 0.5, 0.1, 0.01]:                      # 给真实类别的概率越小，惩罚越重
    print(f"真实类别的概率 {q:<4}  损失 {-np.log(q):.3f}")
''')

# ───── 数据 ─────
C_DATA = nb.cell('''
rng = np.random.default_rng(0)
n = 400
y = (rng.random(n) < 0.5).astype(float)              # 标签 0 / 1，各约一半
shift = np.where(y[:, None] == 1, [1.2, 1.0], [-1.2, -1.0])     # 两类的中心不同
X = rng.normal(size=(n, 2)) * 1.2 + shift
idx = rng.permutation(n)
tr, te = idx[:300], idx[300:]                        # 300 训练，100 测试
mu, sd = X[tr].mean(axis=0), X[tr].std(axis=0)       # 只用训练集标准化
Xtr, Xte = (X[tr] - mu) / sd, (X[te] - mu) / sd
ytr, yte = y[tr], y[te]
print(Xtr.shape, Xte.shape, round(float(ytr.mean()), 3), round(float(yte.mean()), 3))
''')

# ───── 梯度 ─────
C_GRAD = nb.cell('''
def bce_loss(w, b, X, y):                            # 稳定写法：-[y log s(z) + (1-y) log(1-s(z))] = log(1+e^z) - y z
    z = X @ w + b
    return float(np.mean(np.logaddexp(0, z) - y * z))

def grad_lr(w, b, X, y):
    r = sigmoid(X @ w + b) - y                       # 残差：预测概率 - 真实标签
    return X.T @ r / len(y), float(r.mean())         # 和线性回归同一个形状：X^T r / n

w0, b0 = np.array([0.3, -0.2]), 0.1
gw, gb = grad_lr(w0, b0, Xtr, ytr)
eps = 1e-6
num_w = np.array([(bce_loss(w0 + eps * e, b0, Xtr, ytr) - bce_loss(w0 - eps * e, b0, Xtr, ytr)) / (2 * eps)
                  for e in np.eye(2)])
num_b = (bce_loss(w0, b0 + eps, Xtr, ytr) - bce_loss(w0, b0 - eps, Xtr, ytr)) / (2 * eps)
print(np.round(gw, 4), round(gb, 4))
print(np.round(num_w, 4), round(num_b, 4))
print(np.allclose(gw, num_w, atol=1e-6), abs(gb - num_b) < 1e-6)
''')

# ───── 训练 ─────
C_TRAIN = nb.cell('''
def fit(X, y, lr=0.5, steps=300):
    w, b, hist = np.zeros(X.shape[1]), 0.0, []
    for t in range(steps):
        gw, gb = grad_lr(w, b, X, y)
        w, b = w - lr * gw, b - lr * gb
        hist.append(bce_loss(w, b, X, y))
    return w, b, hist

def accuracy(y, yhat):
    return float(np.mean(y == yhat))

w, b, hist = fit(Xtr, ytr)
print("第 1、10、100、300 步的损失：", [round(hist[i], 4) for i in (0, 9, 99, 299)])
print("参数：", np.round(w, 3), round(b, 3))
pte = sigmoid(Xte @ w + b)                           # 预测概率
print("训练准确率：", accuracy(ytr, (sigmoid(Xtr @ w + b) >= 0.5).astype(float)))
print("测试准确率：", accuracy(yte, (pte >= 0.5).astype(float)))
print("多数类基线：", max(yte.mean(), 1 - yte.mean()))
''')

C_TORCH = nb.cell('''
import torch                                         # 用 PyTorch 对照：同样的数据、同样的初值、同样的学习率

Xt = torch.tensor(Xtr, dtype=torch.float64)
yt = torch.tensor(ytr, dtype=torch.float64)
lin = torch.nn.Linear(2, 1).double()
torch.nn.init.zeros_(lin.weight); torch.nn.init.zeros_(lin.bias)
opt = torch.optim.SGD(lin.parameters(), lr=0.5)
lossf = torch.nn.BCEWithLogitsLoss()                 # sigmoid + 交叉熵，内部用稳定写法
for t in range(300):
    opt.zero_grad()
    loss = lossf(lin(Xt).squeeze(1), yt)
    loss.backward()                                  # 自动求导：不需要我们推梯度
    opt.step()
print(np.round(lin.weight.detach().numpy().ravel(), 3), round(lin.bias.item(), 3))
print("与手写版一致：", np.allclose(lin.weight.detach().numpy().ravel(), w), np.isclose(lin.bias.item(), b))
''', static=True)

# ───── 决策边界 ─────
C_BOUND = nb.cell('''
print(f"边界：{w[0]:.3f} * x1 + {w[1]:.3f} * x2 + {b:.3f} = 0")
print("斜率 / 截距：", round(float(-w[0] / w[1]), 3), round(float(-b / w[1]), 3))
for x2 in np.linspace(2.5, -2.5, 11):                # 在标准化后的平面上画一张字符地图
    row = ""
    for x1 in np.linspace(-3, 3, 31):
        row += "#" if sigmoid(np.array([w[0] * x1 + w[1] * x2 + b]))[0] >= 0.5 else "."
    print(row)
''')

C_XOR = nb.cell('''
rng = np.random.default_rng(2)
c = rng.integers(0, 2, (400, 2))                     # 四个角落：(0,0) (0,1) (1,0) (1,1)
Xx = (c * 2 - 1) + rng.normal(0, 0.3, (400, 2))      # 各自加噪声，中心在 (+-1, +-1)
yx = (c[:, 0] != c[:, 1]).astype(float)              # 异或：两个坐标符号不同时为 1
w1, b1, _ = fit(Xx, yx, lr=0.5, steps=500)
print("只用 x1, x2：", accuracy(yx, (sigmoid(Xx @ w1 + b1) >= 0.5).astype(float)))
Xf = np.c_[Xx, Xx[:, 0] * Xx[:, 1]]                  # 加一个特征 x1 * x2
w2, b2, _ = fit(Xf, yx, lr=0.5, steps=500)
print("加上 x1*x2：  ", accuracy(yx, (sigmoid(Xf @ w2 + b2) >= 0.5).astype(float)))
''')

# ───── softmax ─────
C_SOFT = nb.cell('''
def softmax(Z):
    Z = Z - Z.max(axis=1, keepdims=True)             # 每行减最大值，防止 exp 溢出，结果不变
    E = np.exp(Z)
    return E / E.sum(axis=1, keepdims=True)

Z = np.array([[2.0, 1.0, 0.1], [1000.0, 1001.0, 1002.0]])
P = softmax(Z)
print(np.round(P, 3))
print(P.sum(axis=1))                                 # 每行是一个概率分布
print(np.eye(3)[np.array([0, 2, 1])])                # one-hot：类别 -> 单位向量
z = np.array([-1.5, 0.3, 2.0])
print("两类的 softmax = sigmoid：", np.allclose(softmax(np.c_[np.zeros(3), z])[:, 1], sigmoid(z)))
''')

C_SOFTTRAIN = nb.cell('''
rng = np.random.default_rng(1)
means = np.array([[0.0, 2.0], [2.0, -1.0], [-2.0, -1.0]])
y3 = rng.integers(0, 3, 450)
X3 = means[y3] + rng.normal(0, 1.0, (450, 2))
Y3 = np.eye(3)[y3]
Xa, Ya, ya, Xb, yb = X3[:330], Y3[:330], y3[:330], X3[330:], y3[330:]

W, B = np.zeros((2, 3)), np.zeros(3)
for t in range(400):
    R = softmax(Xa @ W + B) - Ya                     # 梯度的形式和二分类一样：P - Y
    W -= 0.5 * Xa.T @ R / 330
    B -= 0.5 * R.mean(axis=0)
P = softmax(Xa @ W + B)
print("训练交叉熵：", round(float(-np.mean(np.log(P[np.arange(330), ya]))), 4))
print("训练准确率：", round(float((P.argmax(axis=1) == ya).mean()), 4))
print("测试准确率：", round(float((softmax(Xb @ W + B).argmax(axis=1) == yb).mean()), 4))
print("权重形状：", W.shape, " 每列是一个类别的权重向量")
''')

# ───── 混淆矩阵与指标 ─────
C_CONF = nb.cell('''
def confusion(y, yhat):
    tp = int(((yhat == 1) & (y == 1)).sum()); fp = int(((yhat == 1) & (y == 0)).sum())
    fn = int(((yhat == 0) & (y == 1)).sum()); tn = int(((yhat == 0) & (y == 0)).sum())
    return tp, fp, fn, tn

def metrics(y, yhat):
    tp, fp, fn, tn = confusion(y, yhat)
    prec = tp / (tp + fp) if tp + fp else 0.0
    rec = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0.0
    return dict(acc=(tp + tn) / len(y), precision=prec, recall=rec, f1=f1)

pred = (pte >= 0.5).astype(float)
tp, fp, fn, tn = confusion(yte, pred)
print("        预测1  预测0")
print(f"真实1   {tp:<6d} {fn}")
print(f"真实0   {fp:<6d} {tn}")
print({k: round(v, 3) for k, v in metrics(yte, pred).items()})
''')

C_ROC = nb.cell('''
def roc_points(y, score):
    ths = np.r_[np.inf, np.sort(np.unique(score))[::-1]]        # 阈值从高到低
    P, N = (y == 1).sum(), (y == 0).sum()
    tpr = np.array([((score >= t) & (y == 1)).sum() / P for t in ths])
    fpr = np.array([((score >= t) & (y == 0)).sum() / N for t in ths])
    return fpr, tpr

def auc_trapz(fpr, tpr):
    return float(np.sum((fpr[1:] - fpr[:-1]) * (tpr[1:] + tpr[:-1]) / 2))

def auc_rank(y, score):                              # AUC = P(随机正样本的得分 > 随机负样本的得分)，平局算 1/2
    pos, neg = score[y == 1], score[y == 0]
    diff = pos[:, None] - neg[None, :]
    return float((diff > 0).mean() + 0.5 * (diff == 0).mean())

fpr, tpr = roc_points(yte, pte)
print("ROC 点数：", len(fpr), " 起点：", (float(fpr[0]), float(tpr[0])), " 终点：", (float(fpr[-1]), float(tpr[-1])))
print("AUC（梯形法）：", round(auc_trapz(fpr, tpr), 4))
print("AUC（排序法）：", round(auc_rank(yte, pte), 4))
rs = np.random.default_rng(0).random(len(yte))
print("随机打分的 AUC：", round(auc_rank(yte, rs), 3))
''')

C_THRESH = nb.cell('''
print("阈值   精确率  召回率  F1")
for t in [0.1, 0.3, 0.5, 0.7, 0.9]:
    m = metrics(yte, (pte >= t).astype(float))
    print(f"{t:<6} {m['precision']:.3f}   {m['recall']:.3f}   {m['f1']:.3f}")

ths = np.linspace(0.05, 0.95, 91)
costs = []
for t in ths:                                        # 假设漏掉一个正类的代价是误报一个的 5 倍
    tp, fp, fn, tn = confusion(yte, (pte >= t).astype(float))
    costs.append(5 * fn + 1 * fp)
print("代价最小的阈值：", round(float(ths[int(np.argmin(costs))]), 2), " 最小代价：", min(costs))
''')

# ───── 类别不平衡 ─────
C_IMB = nb.cell('''
rng = np.random.default_rng(7)
N = 6000
yi = (rng.random(N) < 0.03).astype(float)            # 只有约 3% 是正类
Xi = rng.normal(size=(N, 2)) * 1.2 + np.where(yi[:, None] == 1, [1.5, 1.2], [-0.2, -0.1])
Xi = (Xi - Xi[:4000].mean(axis=0)) / Xi[:4000].std(axis=0)      # 用训练部分的统计量标准化
Xa, ya, Xb, yb = Xi[:4000], yi[:4000], Xi[4000:], yi[4000:]
wi, bi, _ = fit(Xa, ya, lr=0.5, steps=500)
pb = sigmoid(Xb @ wi + bi)
m = metrics(yb, (pb >= 0.5).astype(float))
print("测试集正类个数：", int(yb.sum()), "/", len(yb))
print("永远预测 0 的准确率：", round(1 - float(yb.mean()), 4))
print("模型（阈值 0.5）：", {k: round(v, 3) for k, v in m.items()})
print("AUC：", round(auc_rank(yb, pb), 3))
''')

C_WEIGHT = nb.cell('''
def fit_weighted(X, y, cw, lr=0.5, steps=500):       # 每个样本的损失乘以类别权重 cw[y]
    w, b = np.zeros(X.shape[1]), 0.0
    sw = np.where(y == 1, cw[1], cw[0])
    for t in range(steps):
        r = (sigmoid(X @ w + b) - y) * sw
        w, b = w - lr * X.T @ r / len(y), b - lr * r.mean()
    return w, b

cw = {0: 1.0, 1: (ya == 0).sum() / (ya == 1).sum()}  # 正类权重 = 负类个数 / 正类个数
ww, bw = fit_weighted(Xa, ya, cw)
pw = sigmoid(Xb @ ww + bw)
m2 = metrics(yb, (pw >= 0.5).astype(float))
print("正类权重：", round(float(cw[1]), 2))
print("加权后（阈值 0.5）：", {k: round(v, 3) for k, v in m2.items()})
print("AUC：", round(auc_rank(yb, pw), 3))
''')

C_PREC = nb.cell('''
tpr_, fpr_ = 0.90, 0.05                              # 一个看起来很不错的筛查：抓到 90%，误报 5%
for prev in [0.5, 0.1, 0.01]:                        # 正类占比（患病率）
    prec = tpr_ * prev / (tpr_ * prev + fpr_ * (1 - prev))
    print(f"正类占比 {prev:<5} 精确率 {prec:.3f}")
''')
