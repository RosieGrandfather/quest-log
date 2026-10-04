from runlib import code

C_CHAIN = code('''
import numpy as np

def sigmoid(z):
    return 1 / (1 + np.exp(-z))

# 最简单的网络：每层只有一个神经元，只看最后一层
a_prev, y = 0.5, 1.0               # 上一层的激活值、正确答案
w, b = 0.8, 0.1                    # 这一层唯一的权重和偏置

def cost(w, b, a_prev):
    z = w * a_prev + b             # 加权输入 z
    a = sigmoid(z)                 # 激活值 a
    return (a - y) ** 2            # 平方误差 C0

# 前向：把中间量都存下来（反向传播要用）
z = w * a_prev + b
a = sigmoid(z)
sp = a * (1 - a)                   # sigmoid 的导数 sigma'(z) = a(1-a)
dC_da = 2 * (a - y)                # dC/da

# 反向：链式法则，三个因子相乘
dC_dw = a_prev * sp * dC_da        # dz/dw * da/dz * dC/da
dC_db = 1.0    * sp * dC_da        # dz/db = 1
dC_dprev = w   * sp * dC_da        # dz/da_prev = w（这个就是「往前传」的量）

# 用「微调一下看代价变多少」（中心差分）核对
h = 1e-6
num_w = (cost(w + h, b, a_prev) - cost(w - h, b, a_prev)) / (2 * h)
num_b = (cost(w, b + h, a_prev) - cost(w, b - h, a_prev)) / (2 * h)
num_p = (cost(w, b, a_prev + h) - cost(w, b, a_prev - h)) / (2 * h)

print("z =", round(z, 4), " a =", round(float(a), 4), " C0 =", round(float((a - y) ** 2), 4))
print("dC/dw  公式", round(float(dC_dw), 6), " 数值", round(float(num_w), 6))
print("dC/db  公式", round(float(dC_db), 6), " 数值", round(float(num_b), 6))
print("dC/da' 公式", round(float(dC_dprev), 6), " 数值", round(float(num_p), 6))
''')

C_BACK = code('''
import numpy as np

def sigmoid(z):
    return 1 / (1 + np.exp(-z))

rng = np.random.default_rng(0)
sizes = [3, 4, 2]                                       # 输入 3 维 -> 隐藏 4 -> 输出 2（共 26 个参数）
Ws = [rng.normal(size=(sizes[i + 1], sizes[i])) for i in range(2)]
bs = [rng.normal(size=sizes[i + 1]) for i in range(2)]
x = np.array([0.2, -0.5, 0.9])
y = np.array([1.0, 0.0])

def forward(Ws, bs, x):
    """前向传播：把每层的 z 和 a 都存下来"""
    a_list, z_list = [x], []
    for W, b in zip(Ws, bs):
        z_list.append(W @ a_list[-1] + b)
        a_list.append(sigmoid(z_list[-1]))
    return a_list, z_list

def cost(Ws, bs, x, y):
    return float(np.sum((forward(Ws, bs, x)[0][-1] - y) ** 2))

def backward(Ws, bs, x, y):
    """反向传播：从最后一层往前，每层复用后一层已经算好的量"""
    a_list, z_list = forward(Ws, bs, x)
    dW, db = [None] * len(Ws), [None] * len(Ws)
    dC_da = 2 * (a_list[-1] - y)                        # 起点：代价对输出激活值的导数
    for l in reversed(range(len(Ws))):
        a = a_list[l + 1]
        delta = dC_da * a * (1 - a)                     # delta = dC/dz：乘上 sigma'(z)
        dW[l] = np.outer(delta, a_list[l])              # dC/dW[j,k] = delta[j] * 上一层激活值[k]
        db[l] = delta                                   # dC/db[j] = delta[j]
        dC_da = Ws[l].T @ delta                         # 往前传：对所有路径求和 = 乘 W 的转置
    return dW, db

dW, db = backward(Ws, bs, x, y)
print("梯度的形状：", [g.shape for g in dW], [g.shape for g in db])

# 梯度检验：对每个参数各做一次「加 h、减 h」，数值地算偏导数
h, worst, n_forward = 1e-6, 0.0, 0
for l in range(2):
    for arr, grad in [(Ws[l], dW[l]), (bs[l], db[l])]:
        for idx in np.ndindex(arr.shape):
            old = arr[idx]
            arr[idx] = old + h; c1 = cost(Ws, bs, x, y)
            arr[idx] = old - h; c2 = cost(Ws, bs, x, y)
            arr[idx] = old
            n_forward += 2
            worst = max(worst, abs((c1 - c2) / (2 * h) - grad[idx]))
print("数值梯度共做了", n_forward, "次前向传播；与反向传播的最大差：", f"{worst:.1e}")
print("反向传播只需 1 次前向 + 1 次反向")
''')

C_COST = code('''
# 数一数：视频里的 784-16-16-10 网络，两种算梯度的办法各要做多少事
sizes = [784, 16, 16, 10]
n_params = sum(sizes[i + 1] * sizes[i] + sizes[i + 1] for i in range(3))
mults = sum(sizes[i + 1] * sizes[i] for i in range(3))      # 一次前向传播里的乘法次数（只数矩阵乘法）
print("参数个数：", n_params)
print("一次前向传播的乘法次数：", mults)
print("逐个参数微调（中心差分，每个参数 2 次前向）：", 2 * n_params, "次前向 =", 2 * n_params * mults, "次乘法")
# 反向传播：每层要算 W 的梯度（外积）和往前传的量（W 转置乘 delta），各与前向同量级，约 2 倍
print("反向传播：1 次前向 + 约 2 倍前向的反向 =", 3 * mults, "次乘法")
print("相差约", round(2 * n_params * mults / (3 * mults)), "倍，而且参数越多差距越大")
''')

C_BATCH = code('''
import numpy as np

def sigmoid(z):
    return 1 / (1 + np.exp(-z))

rng = np.random.default_rng(1)

# 数据：平面上的点，圆内为 1、圆外为 0（一条直线分不开，需要非线性）
N = 600
X = rng.uniform(-1, 1, size=(N, 2))
Y = ((X ** 2).sum(axis=1) < 0.5).astype(float).reshape(-1, 1)

def init(seed):
    r = np.random.default_rng(seed)
    return [r.normal(size=(2, 8)) * 0.8, np.zeros(8), r.normal(size=(8, 1)) * 0.8, np.zeros(1)]

def loss_and_grads(p, Xb, Yb):
    """批量版反向传播：每一行是一个样本；梯度对批里的样本取平均"""
    W1, b1, W2, b2 = p
    A1 = sigmoid(Xb @ W1 + b1)                      # (B, 8)
    A2 = sigmoid(A1 @ W2 + b2)                      # (B, 1)
    B = len(Xb)
    loss = np.mean((A2 - Yb) ** 2)
    d2 = 2 * (A2 - Yb) * A2 * (1 - A2) / B          # (B, 1)：dC/dz2（已除以 B 做平均）
    d1 = (d2 @ W2.T) * A1 * (1 - A1)                # (B, 8)：往前传
    return loss, [Xb.T @ d1, d1.sum(0), A1.T @ d2, d2.sum(0)]

# 核对：批量梯度 = 逐个样本梯度的平均
p = init(0)
_, g_batch = loss_and_grads(p, X[:5], Y[:5])
g_each = [loss_and_grads(p, X[i:i + 1], Y[i:i + 1])[1] for i in range(5)]
g_mean = [sum(g[k] for g in g_each) / 5 for k in range(4)]
print("批量梯度 = 逐样本梯度的平均：", all(np.allclose(a, b) for a, b in zip(g_batch, g_mean)))

def accuracy(p):
    W1, b1, W2, b2 = p
    pred = sigmoid(sigmoid(X @ W1 + b1) @ W2 + b2) > 0.5
    return float((pred == (Y > 0.5)).mean())

def train(batch_size, lr, epochs, seed=0):
    p, r = init(seed), np.random.default_rng(100 + seed)
    steps = 0
    for ep in range(epochs):
        order = r.permutation(N)                            # 每个 epoch 先随机打乱
        for s in range(0, N, batch_size):
            idx = order[s:s + batch_size]
            _, g = loss_and_grads(p, X[idx], Y[idx])
            for q, gq in zip(p, g):
                q -= lr * gq                                # 梯度下降一步（原地修改）
            steps += 1
    return p, steps

print("训练前准确率", round(accuracy(init(0)), 3))
for bs in [600, 50, 10]:
    p, steps = train(bs, lr=1.0, epochs=100)
    print(f"batch={bs:>3}：走了 {steps:>5} 步，准确率 {accuracy(p):.3f}，最终全集代价 {loss_and_grads(p, X, Y)[0]:.4f}")
''')

C_VANISH = code('''
import numpy as np

def sigmoid(z):
    return 1 / (1 + np.exp(-z))

def delta_norms(act, dact, depth=10, width=50, seed=0):
    """前向走 depth 层，再从输出往回传，记录每一层 delta = dC/dz 的大小"""
    r = np.random.default_rng(seed)
    Ws = [r.normal(size=(width, width)) / np.sqrt(width) for _ in range(depth)]   # 标准的 1/sqrt(n) 初始化
    a, zs, As = r.normal(size=width), [], []
    for W in Ws:
        z = W @ a
        zs.append(z); a = act(z); As.append(a)
    g = np.ones(width)                                # 假设 dC/da(最后一层) 每个分量都是 1
    norms = []
    for l in reversed(range(depth)):
        delta = g * dact(zs[l], As[l])                # 乘上这一层的激活函数导数
        norms.append(np.linalg.norm(delta))
        g = Ws[l].T @ delta                           # 传给前一层
    return norms[::-1]                                # 第 1 层在前

sig = delta_norms(sigmoid, lambda z, a: a * (1 - a))
rel = delta_norms(lambda z: np.maximum(0, z), lambda z, a: (z > 0).astype(float))
print("层号      :", list(range(1, 11)))
print("sigmoid   :", [f"{v:.1e}" for v in sig])
print("ReLU      :", [f"{v:.1e}" for v in rel])
print("第 1 层与第 10 层的比值  sigmoid:", f"{sig[0] / sig[-1]:.1e}", " ReLU:", f"{rel[0] / rel[-1]:.2f}")
print("sigmoid 导数的最大值：", sigmoid(0) * (1 - sigmoid(0)), "；0.25 的 10 次方 =", f"{0.25 ** 10:.1e}")
''')

C_XORBP = code('''
import numpy as np

def sigmoid(z):
    return 1 / (1 + np.exp(-z))

X = np.array([[0, 0], [0, 1], [1, 0], [1, 1]], dtype=float)
Y = np.array([[0], [1], [1], [0]], dtype=float)

def train(seed, steps=5000, lr=2.0):
    r = np.random.default_rng(seed)
    W1, b1 = r.normal(size=(2, 2)), np.zeros(2)
    W2, b2 = r.normal(size=(2, 1)), np.zeros(1)
    for _ in range(steps):
        A1 = sigmoid(X @ W1 + b1)
        A2 = sigmoid(A1 @ W2 + b2)
        d2 = 2 * (A2 - Y) * A2 * (1 - A2) / 4        # 反向传播：输出层
        d1 = (d2 @ W2.T) * A1 * (1 - A1)             # 反向传播：隐藏层
        W2 -= lr * A1.T @ d2; b2 -= lr * d2.sum(0)
        W1 -= lr * X.T @ d1;  b1 -= lr * d1.sum(0)
    out = sigmoid(sigmoid(X @ W1 + b1) @ W2 + b2)
    return out.ravel(), float(np.mean((out - Y) ** 2))

out, c = train(0)
print("种子 0 的输出：", np.round(out, 2), " 代价", round(c, 4))
costs = [round(train(s)[1], 3) for s in range(10)]
print("10 个种子的最终代价：", costs)
''')
