from runlib import Notebook

nb = Notebook()

# ───── 1. 为什么不用全连接 ─────
C_PARAMS = nb.cell('''
H, W, C = 224, 224, 3
n_in = H * W * C                                     # 一张彩色图展平后的元素个数
fc = n_in * 1000 + 1000                              # 全连接：每个输出神经元连到所有输入，再加偏置
print("输入元素个数：", n_in)
print("全连接 1000 个神经元的参数量：", fc)
print("float32 存储约 %.0f MB" % (fc * 4 / 1e6))

c_out, k = 64, 3
conv = c_out * (C * k * k) + c_out                   # 64 个 3x3 卷积核，每个核看 3 个通道，再加偏置
print("64 个 3x3 卷积核的参数量：", conv)

n_out = c_out * H * W                                # 卷积层输出（保持 224x224）的元素个数
print("同样输出 %d 个数，全连接要：" % n_out, n_in * n_out + n_out)
''')

# ───── 2. 互相关 ─────
C_CORR = nb.cell('''
import numpy as np

def conv2d(x, k, stride=1, pad=0):
    if pad:
        x = np.pad(x, pad)                           # 四周补 pad 圈 0
    kh, kw = k.shape
    oh = (x.shape[0] - kh) // stride + 1             # 输出高
    ow = (x.shape[1] - kw) // stride + 1             # 输出宽
    out = np.zeros((oh, ow))
    for i in range(oh):
        for j in range(ow):
            patch = x[i*stride:i*stride+kh, j*stride:j*stride+kw]
            out[i, j] = (patch * k).sum()            # 窗口和核逐元素相乘再求和
    return out

img = np.zeros((6, 6))
img[:, 3:] = 1                                       # 左半暗（0），右半亮（1）：中间有一条竖直边
kx = np.array([[1, 0, -1], [1, 0, -1], [1, 0, -1]])  # 左减右的竖直边缘核
print(img.astype(int))
print(conv2d(img, kx).astype(int))
''')

C_EQUIV = nb.cell('''
rng = np.random.default_rng(0)
big = rng.normal(size=(8, 10))
a, b = big[:, 0:8], big[:, 1:9]                      # b 是 a 整体向左挪 1 列（右侧补进新内容）
k = rng.normal(size=(3, 3))
ya, yb = conv2d(a, k), conv2d(b, k)
print(ya.shape, yb.shape)
print(np.allclose(yb[:, :-1], ya[:, 1:]))            # 输入挪 1 列，输出也挪 1 列
print(k.size, "个参数在所有位置共用")
''')

# ───── 步幅、填充与输出尺寸 ─────
C_SIZE = nb.cell('''
def out_size(n, k, p, s):
    return (n + 2 * p - k) // s + 1                  # floor((n + 2p - k) / s) + 1

ok, cnt = True, 0
for n in range(5, 13):
    for k in range(1, 6):
        for p in range(0, 3):
            for s in range(1, 4):
                if n + 2 * p < k:
                    continue
                got = conv2d(np.ones((n, n)), np.ones((k, k)), stride=s, pad=p).shape[0]
                ok = ok and got == out_size(n, k, p, s)
                cnt += 1
print("检查了", cnt, "组 (n,k,p,s)，公式全部吻合：", ok)
print(out_size(224, 7, 3, 2), out_size(32, 3, 1, 1), out_size(28, 5, 0, 1))
print(all(out_size(n, 3, 1, 1) == n for n in range(3, 50)))   # k=3, p=1, s=1 尺寸不变
''')

# ───── 多通道、多卷积核 ─────
C_MULTI = nb.cell('''
def conv_layer(x, w, b, stride=1, pad=0):
    c_out = w.shape[0]                               # w 的形状 (C_out, C_in, k, k)
    outs = []
    for o in range(c_out):
        acc = sum(conv2d(x[c], w[o, c], stride, pad) for c in range(w.shape[1]))
        outs.append(acc + b[o])                      # 各输入通道的结果相加，再加偏置
    return np.stack(outs)                            # (C_out, H_out, W_out)

rng = np.random.default_rng(0)
x = rng.normal(size=(3, 8, 8))                       # (C_in, H, W)
w = rng.normal(size=(4, 3, 3, 3))                    # 4 个核，每个核 3x3x3
b = rng.normal(size=4)
y = conv_layer(x, w, b, stride=1, pad=1)
print(y.shape, "参数量", w.size + b.size, "乘加次数", y.size * 3 * 3 * 3)
''')

C_MACS = nb.cell('''
def conv_cost(c_in, c_out, k, h_out, w_out):
    params = c_out * c_in * k * k + c_out            # 权重 + 偏置
    macs = c_out * h_out * w_out * c_in * k * k      # 每个输出元素做 c_in*k*k 次乘加
    return params, macs

print(conv_cost(3, 4, 3, 8, 8))                      # 上一块的例子
h = out_size(224, 7, 3, 2)
print(h, conv_cost(3, 64, 7, h, h))                  # 常见的第一层：7x7，步幅 2
print(conv_cost(64, 64, 3, 56, 56))                  # 56x56 特征图上的一层 3x3，64 -> 64
''')

C_TORCH = nb.cell('''
import torch, torch.nn as nn, torch.nn.functional as F

ty = F.conv2d(torch.tensor(x)[None], torch.tensor(w), torch.tensor(b), stride=1, padding=1)[0]
print(ty.shape, np.allclose(ty.numpy(), y))          # 手写版本与 F.conv2d 一致
layer = nn.Conv2d(3, 4, kernel_size=3, padding=1)
print(layer.weight.shape, layer.bias.shape)
print(sum(p.numel() for p in layer.parameters()))
''', static=True)

# ───── 池化与感受野 ─────
C_POOL = nb.cell('''
def max_pool2d(x, k=2, stride=None):
    stride = stride or k                             # 默认步幅等于窗口大小
    oh = (x.shape[0] - k) // stride + 1
    ow = (x.shape[1] - k) // stride + 1
    out = np.zeros((oh, ow))
    for i in range(oh):
        for j in range(ow):
            out[i, j] = x[i*stride:i*stride+k, j*stride:j*stride+k].max()
    return out

x = np.array([[1, 3, 2, 0], [4, 2, 1, 5], [0, 1, 7, 2], [3, 6, 4, 8]])
print(max_pool2d(x).astype(int))
x2 = x.copy(); x2[1, 0], x2[0, 0] = 0, 4             # 把左上窗口里的最大值 4 挪到同窗口另一格
print(np.array_equal(max_pool2d(x2), max_pool2d(x)))
''')

C_RF = nb.cell('''
def receptive_field(layers):                         # layers: [(核大小 k, 步幅 s), ...]，从输入端往后排
    r, j = 1, 1                                      # r 感受野；j 相邻输出对应的输入间距
    for k, s in layers:
        r = r + (k - 1) * j
        j = j * s
    return r, j

net = [(3, 1), (3, 1), (2, 2), (3, 1)]               # 卷积3, 卷积3, 池化2(步幅2), 卷积3
print(receptive_field(net))
print(receptive_field([(3, 1)] * 3), receptive_field([(7, 1)]))
''')

C_RFCHECK = nb.cell('''
rng = np.random.default_rng(0)
k1, k2, k3 = (rng.normal(size=(3, 3)) for _ in range(3))
avg = np.ones((2, 2)) / 4                            # 用平均池化代替最大池化（线性的，方便测）
def f(x):
    return conv2d(conv2d(conv2d(conv2d(x, k1), k2), avg, stride=2), k3)

x0 = rng.normal(size=(24, 24))
base = f(x0)
print(base.shape)
hit = []
for i in range(24):
    for j in range(24):
        x1 = x0.copy(); x1[i, j] += 1.0              # 单独扰动一个输入像素
        if abs(f(x1)[4, 4] - base[4, 4]) > 1e-12:    # 输出位置 (4,4) 变了吗？
            hit.append((i, j))
hit = np.array(hit)
print(len(hit), hit.min(axis=0), hit.max(axis=0))
''')

# ───── 最小 CNN ─────
C_STACK = nb.cell('''
def relu(x):
    return np.maximum(x, 0)

rng = np.random.default_rng(1)
x = rng.normal(size=(1, 28, 28))                     # 一张 1 通道 28x28 的图
W1, b1 = rng.normal(size=(8, 1, 3, 3)) * 0.3, np.zeros(8)
W2, b2 = rng.normal(size=(10, 8 * 14 * 14)) * 0.02, np.zeros(10)

trace = []
h = conv_layer(x, W1, b1, stride=1, pad=1);  trace.append(("conv 1->8, 3x3, p=1", h.shape, W1.size + b1.size))
h = relu(h);                                 trace.append(("ReLU", h.shape, 0))
h = np.stack([max_pool2d(c) for c in h]);    trace.append(("maxpool 2x2", h.shape, 0))
h = h.reshape(-1);                           trace.append(("flatten", h.shape, 0))
logits = W2 @ h + b2;                        trace.append(("linear 1568->10", logits.shape, W2.size + b2.size))
for name, shape, n in trace:
    print(f"{name:<22}{str(shape):<14}{n}")
print("总参数量：", sum(n for _, _, n in trace))
''')

C_STACKT = nb.cell('''
model = nn.Sequential(nn.Conv2d(1, 8, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2), nn.Flatten(), nn.Linear(8 * 14 * 14, 10)).double()
with torch.no_grad():                                # 把手写版本的权重拷进去
    model[0].weight.copy_(torch.tensor(W1)); model[0].bias.copy_(torch.tensor(b1))
    model[4].weight.copy_(torch.tensor(W2)); model[4].bias.copy_(torch.tensor(b2))
    t = torch.tensor(x)[None]                        # 加上 batch 维：(1, 1, 28, 28)
    for layer in model:
        t = layer(t)
        print(f"{type(layer).__name__:<10}{tuple(t.shape)}")
    print(np.allclose(t[0].numpy(), logits))
print(sum(p.numel() for p in model.parameters()))
''', static=True)

C_SMALL = nb.cell('''
C = 64
for name, layers, k in [("两个 3x3", [(3, 1)] * 2, 3), ("一个 5x5", [(5, 1)], 5),
                        ("三个 3x3", [(3, 1)] * 3, 3), ("一个 7x7", [(7, 1)], 7)]:
    n_layers = len(layers)
    params = n_layers * C * C * k * k                # 通道数始终为 C，不计偏置
    print(f"{name}  感受野 {receptive_field(layers)[0]}  参数量 {params}")
print(conv_cost(64, 64, 3, 56, 56)[1], conv_cost(128, 128, 3, 28, 28)[1])   # 通道翻倍、空间减半：计算量不变
''')
