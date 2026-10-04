from runlib import code

C_TENSOR = code('''
import numpy as np
import torch as t

x = t.tensor([[1., 2., 3.], [4., 5., 6.]])        # 从嵌套列表创建
print(x.shape, x.dtype, x.device)                 # 形状、元素类型、所在设备
print(t.tensor([1, 2, 3]).dtype, t.arange(5).dtype, t.randn(2).dtype)   # 整数默认 int64，随机数默认 float32

print(x.sum(dim=0), x.sum(dim=1))                 # dim 就是 NumPy 的 axis
print(x.T.shape, x.reshape(3, 2).shape)           # 转置 / 改形状

# 与 NumPy 互转：from_numpy 不复制数据，两者共用同一块内存
a = np.array([1., 2., 3.])
b = t.from_numpy(a)
a[0] = 100.                                       # 改 NumPy 数组……
print(b)                                          # ……张量跟着变
c = b.clone()                                     # clone 才是真的复制
a[1] = -1.
print(b, c)

# 视图 (view)：reshape / view 通常也不复制，改一个，另一个也变
v = x.view(3, 2)
v[0, 0] = 99.
print(x[0, 0].item(), x.is_contiguous(), x.T.is_contiguous())

# 浮点精度：默认 float32，约 7 位有效数字
print(t.tensor(0.1).item(), t.tensor(0.1, dtype=t.float64).item())
''')

C_AUTOGRAD = code('''
import torch as t

w = t.tensor(3.0, requires_grad=True)             # 告诉 PyTorch：要记录和 w 有关的计算
y = w ** 2 + 2 * w                                # 前向计算，同时建好计算图
print(y.item(), type(y.grad_fn).__name__, w.grad) # y 记着自己是由「加法」算出的；还没反向，所以 w.grad 是 None

y.backward()                                      # 反向传播：dy/dw = 2w + 2
print(w.grad)

y2 = w ** 2 + 2 * w                               # 再算一遍、再反向一次，不清零
y2.backward()
print(w.grad)                                     # 梯度是累加的：8 + 8

w.grad.zero_()                                    # 手动清零（优化器的 zero_grad 做的就是这件事）
print(w.grad)

# 用有限差分验证 autograd：f(v) = v^3 - 2v 在 v = 1.5 处，导数应为 3v^2 - 2 = 4.75
def f(v):
    return v ** 3 - 2 * v
v = t.tensor(1.5, dtype=t.float64, requires_grad=True)
f(v).backward()
eps = 1e-6
numeric = (f(t.tensor(1.5 + eps, dtype=t.float64)) - f(t.tensor(1.5 - eps, dtype=t.float64))) / (2 * eps)
print(v.grad.item(), round(numeric.item(), 6))
''')

C_GRAPH = code('''
import torch as t

# 向量参数：loss 必须是标量，对每个分量各有一个梯度
x = t.tensor([1., 2., 3.], requires_grad=True)
loss = (x ** 2).sum()                              # loss = x1^2 + x2^2 + x3^2，梯度应是 2x
loss.backward()
print(loss.item(), x.grad)

# 对非标量直接 backward 会报错：PyTorch 不知道该怎么把多个输出合成一个数
z = x * 2
try:
    z.backward()
except RuntimeError as e:
    print("RuntimeError:", str(e)[:54])
z.backward(t.ones(3))                              # 显式给出权重（这里每个输出权重 1）就可以
print(x.grad)                                      # 在上一次的 2x = [2,4,6] 上又累加了 [2,2,2]

# 叶子张量与非叶子张量：.grad 只保存在叶子上
a = t.tensor(2.0, requires_grad=True)
b = a * 3
print(a.is_leaf, b.is_leaf, b.requires_grad)

# 不需要梯度时：no_grad 关掉记录（推理、手动更新参数时用）；detach 把张量从图里摘出来
with t.no_grad():
    c = a * 3
print(c.requires_grad, (a * 3).detach().requires_grad)

# 整数张量不能求导
try:
    t.tensor([1, 2, 3], requires_grad=True)
except RuntimeError as e:
    print("RuntimeError:", str(e)[:70])
''')

C_MODULE = code('''
import torch as t
import torch.nn as nn

class TinyNet(nn.Module):
    def __init__(self):
        super().__init__()
        self.fc1 = nn.Linear(4, 8)                 # 子层放在 __init__ 里，会被自动登记
        self.fc2 = nn.Linear(8, 1)
        self.scale = nn.Parameter(t.ones(1))       # 额外的可训练参数
        self.note = t.zeros(3)                     # 普通张量：不会被登记为参数

    def forward(self, x):                          # 前向计算写在 forward 里，调用 model(x) 时执行
        return self.scale * self.fc2(t.relu(self.fc1(x)))

model = TinyNet()
for name, p in model.named_parameters():
    print(f"{name:12s} {tuple(p.shape)!s:8s} {p.numel():3d}  requires_grad={p.requires_grad}")
print("总参数个数：", sum(p.numel() for p in model.parameters()), " = (4*8+8) + (8*1+1) + 1")
print("state_dict 的键：", list(model.state_dict().keys()))
print("note 在参数里吗：", any(p is model.note for p in model.parameters()))
print(type(model.fc1.weight).__name__, model(t.randn(5, 4)).shape)
''')

C_SGD = code('''
import torch as t
import torch.nn as nn

t.manual_seed(0)
X = t.randn(20, 3)
Y = X @ t.tensor([1., -2., 0.5]) + 0.3             # 真实规律：y = x·[1,-2,0.5] + 0.3

def make():
    t.manual_seed(1)                               # 两次创建的初始参数相同
    return nn.Linear(3, 1)

# (a) 手写梯度下降：theta <- theta - lr * grad
m1 = make()
for _ in range(50):
    loss = ((m1(X).squeeze(1) - Y) ** 2).mean()
    m1.zero_grad()
    loss.backward()
    with t.no_grad():                              # 更新参数这件事本身不应被记录进计算图
        for p in m1.parameters():
            p -= 0.1 * p.grad

# (b) 用 torch.optim.SGD 做同样的事
m2 = make()
opt = t.optim.SGD(m2.parameters(), lr=0.1)
for _ in range(50):
    loss = ((m2(X).squeeze(1) - Y) ** 2).mean()
    opt.zero_grad()
    loss.backward()
    opt.step()

print("手写与 optim.SGD 的参数完全一致：", t.allclose(m1.weight, m2.weight) and t.allclose(m1.bias, m2.bias))
print("学到的权重：", m2.weight.detach().squeeze().numpy().round(3), " 偏置：", round(m2.bias.item(), 3))
print("最终损失：", round(loss.item(), 5))
''')

C_TRAIN = code('''
import torch as t
import torch.nn as nn

# XOR：四个点不能用一条直线分开。对比「有 ReLU」和「没有 ReLU」的 2 -> 8 -> 1 网络
X = t.tensor([[0., 0.], [0., 1.], [1., 0.], [1., 1.]])
Y = t.tensor([[0.], [1.], [1.], [0.]])

def train(use_relu, seed, steps=500, lr=0.05):
    t.manual_seed(seed)
    layers = [nn.Linear(2, 8)] + ([nn.ReLU()] if use_relu else []) + [nn.Linear(8, 1)]
    model = nn.Sequential(*layers)
    opt = t.optim.Adam(model.parameters(), lr=lr)
    loss_fn = nn.MSELoss()
    for step in range(steps):
        pred = model(X)                            # 1. 前向
        loss = loss_fn(pred, Y)                    # 2. 损失（标量）
        opt.zero_grad()                            # 3. 清空旧梯度
        loss.backward()                            # 4. 反向传播
        opt.step()                                 # 5. 更新参数
    return loss.item(), model(X).detach().squeeze().numpy().round(2) + 0.0

for use_relu in (True, False):
    losses = [train(use_relu, s)[0] for s in range(5)]
    print("有 ReLU " if use_relu else "无 ReLU ", "5 个随机种子的最终损失：", [f"{l:.1e}" for l in losses])
print("种子 0、有 ReLU 的四个输出：", train(True, 0)[1], "（目标 0 1 1 0）")
print("种子 0、无 ReLU 的四个输出：", train(False, 0)[1])
''')

C_LR = code('''
import torch as t
import torch.nn as nn

t.manual_seed(0)
X = t.randn(100, 1)
Y = 2 * X + 1 + 0.1 * t.randn(100, 1)              # 真实规律 y = 2x + 1，加一点噪声

def fit(lr, zero_grad=True, steps=30):
    t.manual_seed(1)
    model = nn.Linear(1, 1)
    opt = t.optim.SGD(model.parameters(), lr=lr)   # lr 是超参数：人定的，梯度下降不会改它
    for _ in range(steps):
        loss = nn.functional.mse_loss(model(X), Y)
        if zero_grad:
            opt.zero_grad()
        loss.backward()
        opt.step()
    return loss.item(), model.weight.item(), model.bias.item()

for lr in (0.001, 0.05, 0.5, 1.05):
    loss, w, b = fit(lr)
    print(f"lr={lr:<6} 最终损失 {loss:10.4g}  w={w:8.3f}  b={b:8.3f}")

# 忘记 zero_grad：梯度越攒越大，等于悄悄把学习率放大
loss, w, b = fit(0.05, zero_grad=False)
print(f"lr=0.05 但忘了 zero_grad：最终损失 {loss:.4g}  w={w:.3g}  b={b:.3g}")
''')
