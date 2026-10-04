from runlib import code

C_NEURON = code('''
import numpy as np

def sigmoid(x):
    return 1 / (1 + np.exp(-x))

def relu(x):
    return np.maximum(0, x)

# 一个神经元：对上一层的 3 个激活值做加权和，加上偏置，再过激活函数
a_prev = np.array([0.2, 0.9, 0.5])         # 上一层的激活值
w = np.array([1.5, -2.0, 0.5])             # 权重：对第 2 个输入是「抑制」（负权重）
b = -0.3                                   # 偏置：加权和要超过 0.3，才会明显激活

z = w @ a_prev + b                         # 加权和 + 偏置（激活之前的值，常记作 z）
print("z =", round(z, 3))
print("sigmoid(z) =", round(float(sigmoid(z)), 3), "  relu(z) =", round(float(relu(z)), 3))

# 激活函数长什么样：sigmoid 把任意实数压进 (0, 1)；ReLU 把负数截成 0
xs = np.array([-10, -2, 0, 2, 10])
print("x       :", xs)
print("sigmoid :", np.round(sigmoid(xs), 4))
print("relu    :", relu(xs))
''')

C_LAYER = code('''
import numpy as np

def sigmoid(x):
    return 1 / (1 + np.exp(-x))

rng = np.random.default_rng(0)

# 视频里的网络：784 -> 16 -> 16 -> 10。每一层 = 一个权重矩阵 W 和一个偏置向量 b
sizes = [784, 16, 16, 10]
Ws = [rng.normal(size=(sizes[i + 1], sizes[i])) for i in range(3)]   # W 的形状：(这一层的神经元数, 上一层的神经元数)
bs = [rng.normal(size=sizes[i + 1]) for i in range(3)]

for i, (W, b) in enumerate(zip(Ws, bs), start=1):
    print(f"第 {i} 层：W 的形状 {W.shape}，b 的形状 {b.shape}，参数 {W.size + b.size} 个")
n_w = sum(W.size for W in Ws)
n_b = sum(b.size for b in bs)
print("权重", n_w, "+ 偏置", n_b, "= 参数总数", n_w + n_b)

# 前向传播 (forward pass)：一层一层地「矩阵乘法 + 偏置 + 激活函数」
a = rng.uniform(size=784)                  # 假装这是一张 28x28 图片拉直后的 784 个像素亮度
for W, b in zip(Ws, bs):
    a = sigmoid(W @ a + b)
    print("这一层输出的形状：", a.shape)
print("最后 10 个输出都在 (0,1) 内：", bool(((a > 0) & (a < 1)).all()))
print("网络此刻「认为」是数字：", int(a.argmax()), "（参数是随机的，所以这个答案毫无意义）")

# 一次处理一批图片：把向量换成矩阵，同一段代码就能同时算 32 张
batch = rng.uniform(size=(32, 784))
out = batch
for W, b in zip(Ws, bs):
    out = sigmoid(out @ W.T + b)           # 注意：批量时 W 要转置（行向量 @ W.T）
print("一批 32 张图片的输出形状：", out.shape)
''')

C_LOSS = code('''
import numpy as np

def sigmoid(x):
    return 1 / (1 + np.exp(-x))

rng = np.random.default_rng(0)
sizes = [784, 16, 16, 10]
Ws = [rng.normal(size=(sizes[i + 1], sizes[i])) * 0.1 for i in range(3)]
bs = [np.zeros(sizes[i + 1]) for i in range(3)]

def forward(x):
    for W, b in zip(Ws, bs):
        x = sigmoid(W @ x + b)
    return x

# 代价函数：输出与正确答案（独热编码 one-hot：正确数字的位置是 1，其余是 0）逐个相减、平方、相加
def cost_one(x, label):
    y = np.zeros(10); y[label] = 1
    return float(np.sum((forward(x) - y) ** 2))

x = rng.uniform(size=784)
print("输出：", np.round(forward(x), 3))
print("如果正确答案是 3：", round(cost_one(x, 3), 3))
print("完美的输出（正确位置 1，其余 0）的代价：", float(np.sum((np.eye(10)[3] - np.eye(10)[3]) ** 2)))
print("最差的情形（全部猜反）的代价：", float(np.sum((1 - np.eye(10)[3]) ** 2)))

# 代价函数是「所有训练样本的平均」：越小越好
xs = rng.uniform(size=(100, 784)); labels = rng.integers(0, 10, size=100)
avg = np.mean([cost_one(x, l) for x, l in zip(xs, labels)])
print("随机参数下，100 张图片的平均代价：", round(float(avg), 3), "（输出都在 0.5 左右，每项误差平方约 0.25，十项合计约 2.5）")
''')

C_GD = code('''
# 最简单的「代价函数」：C(theta) = (theta - 3)^2，最低点在 theta = 3，梯度 dC/dtheta = 2 (theta - 3)
def grad(theta):
    return 2 * (theta - 3)

def descend(lr, steps=20, theta=-5.0):
    path = [theta]
    for _ in range(steps):
        theta = theta - lr * grad(theta)       # 梯度下降：沿负梯度方向走一步
        path.append(theta)
    return path

for lr in (0.01, 0.1, 0.5, 0.95, 1.05):
    p = descend(lr)
    print(f"学习率 {lr:<4}： 第 0 步 {p[0]:7.2f}   第 5 步 {p[5]:8.2f}   第 20 步 {p[20]:9.2f}")
''')

C_XOR = code('''
import numpy as np

# 数据：异或 XOR。(0,0)->0, (0,1)->1, (1,0)->1, (1,1)->0。用一条直线分不开这四个点。
X = np.array([[0, 0], [0, 1], [1, 0], [1, 1]], dtype=float)
Y = np.array([0, 1, 1, 0], dtype=float)

def sigmoid(x): return 1 / (1 + np.exp(-x))

def unpack(p):                              # 2 -> 2 -> 1 的网络，一共 6 + 3 = 9 个参数
    return p[:4].reshape(2, 2), p[4:6], p[6:8], p[8]

def predict(p, X, act):
    W1, b1, W2, b2 = unpack(p)
    h = act(X @ W1 + b1)                    # 隐藏层
    return sigmoid(h @ W2 + b2)             # 输出层（始终用 sigmoid，把输出压进 0 到 1，方便和 0/1 的答案比较）

def cost(p, act):
    return float(np.mean((predict(p, X, act) - Y) ** 2))

def numeric_grad(p, act, eps=1e-5):        # 暂时不用反向传播：对每个参数微调一点点，看代价变化多少
    g = np.zeros_like(p)
    for i in range(len(p)):
        d = np.zeros_like(p); d[i] = eps
        g[i] = (cost(p + d, act) - cost(p - d, act)) / (2 * eps)
    return g

def train(act, seed, lr=2.0, steps=5000):
    p = np.random.default_rng(seed).normal(size=9)
    for _ in range(steps):
        p = p - lr * numeric_grad(p, act)   # 梯度下降
    return p

for name, act in [("有激活函数 (sigmoid)", sigmoid), ("隐藏层没有激活函数 (恒等)", lambda x: x)]:
    p = train(act, seed=1)
    print(name, "：最终代价", round(cost(p, act), 4), "；四个输入的输出", np.round(predict(p, X, act), 2))

# 初始参数是随机的，换个随机种子结果会不同：用 10 个种子各训练一次（有 sigmoid）
costs = [round(cost(train(sigmoid, seed=s), sigmoid), 3) for s in range(10)]
print("10 个种子的最终代价：", costs)
''')

C_COLLAPSE = code('''
import numpy as np
rng = np.random.default_rng(0)

# 去掉激活函数后，三层网络 = 一个线性变换。用随机矩阵直接验证
W1, W2, W3 = rng.normal(size=(16, 784)), rng.normal(size=(16, 16)), rng.normal(size=(10, 16))
b1, b2, b3 = rng.normal(size=16), rng.normal(size=16), rng.normal(size=10)
x = rng.normal(size=784)

deep = W3 @ (W2 @ (W1 @ x + b1) + b2) + b3          # 三层，没有激活函数
W_all = W3 @ W2 @ W1                                  # 合并成一个矩阵
b_all = W3 @ (W2 @ b1 + b2) + b3                      # 合并成一个偏置
print("合并后的 W 形状：", W_all.shape)
print("两种算法结果相同：", bool(np.allclose(deep, W_all @ x + b_all)))
print("三层的参数个数：", W1.size + W2.size + W3.size + 42, "；合并后只需要：", W_all.size + b_all.size)
''')
