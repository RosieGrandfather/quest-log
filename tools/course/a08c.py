from runlib import code

C_NUM = code('''
import numpy as np

def num_deriv(f, x, h=1e-5):
    # 中心差分：(f(x+h) - f(x-h)) / (2h)，用「很小的 h」去逼近切线斜率
    return (f(x + h) - f(x - h)) / (2 * h)

sigmoid = lambda x: 1 / (1 + np.exp(-x))

# 左边是我们手推的公式，右边是用数值方法「量」出来的斜率，两者应该一致
cases = [
    ("x^3       @ x=2  ", lambda x: x**3,        lambda x: 3 * x**2,                 2.0),
    ("ln x      @ x=4  ", np.log,                lambda x: 1 / x,                    4.0),
    ("e^x       @ x=1  ", np.exp,                np.exp,                             1.0),
    ("sigmoid   @ x=0  ", sigmoid,               lambda x: sigmoid(x) * (1 - sigmoid(x)), 0.0),
    ("tanh      @ x=1  ", np.tanh,               lambda x: 1 - np.tanh(x) ** 2,      1.0),
]
for name, f, df, x in cases:
    print(name, "公式:", round(float(df(x)), 6), " 数值:", round(float(num_deriv(f, x)), 6))

# h 取多小最好？太大：切线近似不准；太小：两个几乎相等的数相减，浮点误差爆炸
print("--- f = e^x 在 x=1 处，单边差分 (f(x+h)-f(x))/h 的误差 ---")
for k in [1, 3, 5, 8, 11, 14]:
    h = 10.0 ** (-k)
    est = (np.exp(1 + h) - np.exp(1)) / h
    print(f"h=1e-{k:<2d} 误差 {abs(est - np.e):.2e}")
''')

C_CHAIN = code('''
import numpy as np

def num_deriv(f, x, h=1e-5):
    return (f(x + h) - f(x - h)) / (2 * h)

x = 0.7
# 链式法则：d/dx sin(x^2) = cos(x^2) * 2x
f = lambda x: np.sin(x ** 2)
print("sin(x^2)   公式:", round(float(np.cos(x**2) * 2 * x), 6), " 数值:", round(float(num_deriv(f, x)), 6))
# d/dx e^{-x^2} = e^{-x^2} * (-2x)
g = lambda x: np.exp(-x ** 2)
print("e^(-x^2)   公式:", round(float(np.exp(-x**2) * (-2 * x)), 6), " 数值:", round(float(num_deriv(g, x)), 6))
# 乘积法则：(u*v)' = u'v + uv'，取 u = x^2, v = sin x
h = lambda x: x ** 2 * np.sin(x)
print("x^2 sin x  公式:", round(float(2 * x * np.sin(x) + x**2 * np.cos(x)), 6), " 数值:", round(float(num_deriv(h, x)), 6))

# 链式法则 = 一路相乘。把 Sigmoid 一层层套起来：y = s(s(s(...s(x))))，共 L 层
# 每过一层，就把「这一层的局部导数 s'(t) = s(1-s)」乘进去
sigmoid = lambda t: 1 / (1 + np.exp(-t))
def deep_grad(x, L):
    d = 1.0
    for _ in range(L):
        s = sigmoid(x)
        d *= s * (1 - s)                   # 乘上这一层的局部导数
        x = s                              # 输出变成下一层的输入
    return d

# 先核对：L=3 层时，链式法则的结果和数值微分一致
f3 = lambda t: sigmoid(sigmoid(sigmoid(t)))
print("L=3 核对  链式:", round(float(deep_grad(0.5, 3)), 6), " 数值:", round(float(num_deriv(f3, 0.5)), 6))

print("--- 套 L 层 Sigmoid 之后，dy/dx 还剩多少？ ---")
for L in [1, 2, 5, 10, 20, 50]:
    print(f"L={L:<2d}  dy/dx = {deep_grad(0.5, L):.3e}")
print("每层的导数最大 0.25，所以 10 层的乘积不会超过 0.25^10 =", f"{0.25 ** 10:.3e}")
''')

C_GRAD = code('''
import numpy as np

# f(x, y) = x^2 y + 3y，偏导数手推：df/dx = 2xy，df/dy = x^2 + 3
f = lambda p: p[0] ** 2 * p[1] + 3 * p[1]
def num_grad(f, p, h=1e-6):
    # 对每个坐标分别「只动它一个」，其余固定，就是偏导数；拼起来就是梯度
    g = np.zeros_like(p)
    for i in range(len(p)):
        e = np.zeros_like(p); e[i] = h
        g[i] = (f(p + e) - f(p - e)) / (2 * h)
    return g

p = np.array([2.0, 1.0])
print("手推梯度  :", np.array([2 * p[0] * p[1], p[0] ** 2 + 3]))
print("数值梯度  :", np.round(num_grad(f, p), 5))

# 一阶泰勒展开：f(p + h) ≈ f(p) + grad · h。看看误差随步长 h 怎么变
grad = num_grad(f, p)
d = np.array([1.0, -2.0]) / np.sqrt(5)       # 一个单位长度的方向
print("--- 沿同一方向走不同的步长 s，一阶近似的误差 ---")
for s in [1.0, 0.3, 0.1, 0.03, 0.01]:
    exact = f(p + s * d)
    approx = f(p) + s * (grad @ d)
    print(f"s={s:<5}  真实 {exact:8.4f}  一阶近似 {approx:8.4f}  误差 {abs(exact - approx):.5f}")

# 沿负梯度走：近似说函数值会下降 eta * |grad|^2。步长小时对，大了就失效
print("--- 沿 -grad 走 eta：f 的变化 (真实 vs 一阶预言) ---")
for eta in [0.001, 0.01, 0.05, 0.1, 0.3]:
    q = p - eta * grad
    print(f"eta={eta:<5}  真实变化 {f(q) - f(p):9.4f}  预言 {-eta * (grad @ grad):9.4f}")

# 雅可比矩阵：线性层 y = W x 的 Jacobian 就是 W 自己
rng = np.random.default_rng(0)
W = rng.integers(-3, 4, size=(2, 3)).astype(float)
x0 = rng.normal(size=3)
J = np.stack([(W @ (x0 + e) - W @ (x0 - e)) / 2e-6 for e in 1e-6 * np.eye(3)], axis=1)
print("Jacobian 等于 W：", np.allclose(J, W, atol=1e-6))
''')

C_LOSS = code('''
import numpy as np

sigmoid = lambda z: 1 / (1 + np.exp(-z))
def num_d(f, x, h=1e-6):
    return (f(x + h) - f(x - h)) / (2 * h)

# ---- 均方误差：L = 0.5 (x - y)^2，dL/dx = x - y ----
y = 1.0
mse = lambda x: 0.5 * (x - y) ** 2
print("MSE：输出 x 离目标 y=1 越远，梯度越大（和误差成正比）")
for x in [0.0, 0.5, 0.9, 1.5]:
    print(f"  x={x:<4} 公式 {x - y:6.2f}  数值 {num_d(mse, x):6.2f}")

# ---- 二元交叉熵：L = -(y log x + (1-y) log(1-x)) ----
bce = lambda x, y: -(y * np.log(x) + (1 - y) * np.log(1 - x))
d_bce = lambda x, y: -y / x + (1 - y) / (1 - x)
print("BCE（标签 y=1）：对概率 x 的梯度 -1/x，x 越接近 0，梯度的绝对值越大")
for x in [0.5, 0.1, 0.01, 0.001]:
    print(f"  x={x:<6} L={bce(x, 1):7.3f}  dL/dx={d_bce(x, 1):9.1f}  数值 {num_d(lambda t: bce(t, 1), x, 1e-8):9.1f}")

# ---- 对 logit z 求导：x = sigmoid(z) 之后，梯度变成 sigmoid(z) - y，有界 ----
print("BCE 对 logit z 求导（标签 y=1）：公式 sigmoid(z) - y，数值 = 数值微分")
for z in [-8.0, -2.0, 0.0, 2.0]:
    form = sigmoid(z) - 1
    num = num_d(lambda t: bce(sigmoid(t), 1), z)
    print(f"  z={z:<5} 公式 {float(form):8.4f}  数值 {float(num):8.4f}")
''')

C_EXP = code('''
import numpy as np

sigmoid = lambda z: 1 / (1 + np.exp(-z))

# 小实验：一维逻辑回归。数据：x 小的标签 0，x 大的标签 1，模型 p = sigmoid(w x + b)
xs = np.array([-2.0, -1.0, -0.5, 0.5, 1.0, 2.0])
ys = np.array([0.0, 0.0, 0.0, 1.0, 1.0, 1.0])

def loss(w, b):
    p = sigmoid(w * xs + b)
    return float(np.mean(-(ys * np.log(p) + (1 - ys) * np.log(1 - p))))

def grad(w, b):
    p = sigmoid(w * xs + b)
    dz = (p - ys) / len(xs)                # 上一块的结论：dL/dz = p - y（再对样本取平均）
    return np.array([np.sum(dz * xs), np.sum(dz)])   # 链式法则：dz/dw = x，dz/db = 1

# 先「梯度检验」：手推的梯度对不对？用数值微分核对
w, b, h = 0.3, -0.2, 1e-6
num = np.array([(loss(w + h, b) - loss(w - h, b)) / (2 * h), (loss(w, b + h) - loss(w, b - h)) / (2 * h)])
print("梯度检验：", np.allclose(grad(w, b), num, atol=1e-7))

# 梯度下降
w, b, eta = 0.0, 0.0, 1.0
print("起点 loss =", round(loss(w, b), 4))      # 全部猜 0.5，loss = ln 2
for step in range(1, 201):
    gw, gb = grad(w, b)
    w, b = w - eta * gw, b - eta * gb
    if step in (1, 10, 50, 200):
        print(f"第 {step:3d} 步  w={w:.3f}  b={b:.3f}  loss={loss(w, b):.4f}")
print("最后给每个点的概率：", np.round(sigmoid(w * xs + b), 3))
''')
