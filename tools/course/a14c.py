from runlib import code

C_RULE = code('''
import numpy as np

# 用 np.broadcast_shapes 判断两个形状能不能广播、结果是什么
cases = [((5, 3), (3,)), ((3, 4), (1, 4)), ((2, 1, 4), (3, 1)),
         ((7, 1, 5), (1, 6, 1)), ((8, 1, 6, 1), (7, 1, 5)),
         ((6, 2), (6,)), ((2, 3, 4), (2, 1)), ((4, 1), (4,))]
for a, b in cases:
    try:
        print(a, "+", b, "->", np.broadcast_shapes(a, b))
    except ValueError:
        print(a, "+", b, "-> 报错，不能广播")

# 广播到底做了什么：out[i, j] = data[i, j] + vec[j]，用双重循环对拍
rng = np.random.default_rng(0)
data = rng.integers(0, 10, size=(4, 3)).astype(float)
vec = np.array([10., 20., 30.])
loop = np.empty_like(data)
for i in range(4):
    for j in range(3):
        loop[i, j] = data[i, j] + vec[j]
print("广播结果和循环一致：", np.array_equal(data + vec, loop))
''')

C_STRIDE = code('''
import numpy as np

# 广播是「视图」：并没有真的把 vec 复制 1000 份
vec = np.arange(5.)
big = np.broadcast_to(vec, (1000, 5))
print("形状:", big.shape, " 每个维度跳多少字节 strides:", big.strides)
print("vec 自己的 strides:", vec.strides)
print("big 和 vec 共用同一块内存:", np.shares_memory(big, vec), "  big 是只读的:", not big.flags.writeable)

# 真正复制一份：内存才会变大
copy = np.tile(vec, (1000, 1))
print("复制版本的 strides:", copy.strides, " 实际占用字节数:", copy.nbytes, " 和 vec 共用内存:", np.shares_memory(copy, vec))
''')

C_ALIGN = code('''
import numpy as np

x = np.ones((3, 1, 5))
print("x[None].shape        :", x[None].shape)          # 等价于 unsqueeze(0)：在最前面插入长度为 1 的维度
print("x[..., None].shape   :", x[..., None].shape)     # 等价于 unsqueeze(-1)：在最后插入
print("np.squeeze(x, 1)     :", np.squeeze(x, axis=1).shape)   # 去掉第 1 维（长度为 1）
try:
    np.squeeze(x, axis=0)                               # 第 0 维长度是 3，NumPy 会报错
except ValueError as e:
    print("squeeze 第 0 维      : 报错 ->", e)

m = np.arange(12.).reshape(3, 4)
print("sum(axis=1) 形状      :", m.sum(axis=1).shape)
print("sum(axis=1, keepdims) :", m.sum(axis=1, keepdims=True).shape)
centered = m - m.mean(axis=1, keepdims=True)           # 每行减去自己的平均值
print("每行减均值后，各行的均值:", centered.mean(axis=1))

# 如果忘了 keepdims：(3,) 对齐最后一维 4，直接报错
try:
    m - m.mean(axis=1)
except ValueError as e:
    print("忘了 keepdims -> 报错:", e)
''')

C_SILENT = code('''
import numpy as np

# 最危险的情况：形状恰好是方阵，不报错但算错
M = np.arange(9.).reshape(3, 3)            # 3x3，n = d = 3
wrong = M - M.mean(axis=1)                  # 忘了 keepdims：(3,) 被当成「每一列减一个数」
right = M - M.mean(axis=1, keepdims=True)  # 正确：每一行减自己的均值
print("两个结果相等吗：", np.allclose(wrong, right))
print("正确做法下每行均值：", right.mean(axis=1))
print("错误做法下每行均值：", wrong.mean(axis=1))

# 用 assert 守住关键形状，让错误当场暴露
row_mean = M.mean(axis=1, keepdims=True)
assert row_mean.shape == (3, 1)
print("assert 通过，形状 =", row_mean.shape)

# 另一个经典：(4,1) + (4,) 悄悄变成 (4,4)
col = np.arange(4.).reshape(4, 1)
row = np.arange(4.)
print("(4,1) + (4,) 的形状：", (col + row).shape)
''')

C_COSINE = code('''
import numpy as np

# 1. 行归一化 + 余弦相似度矩阵
X = np.array([[3., 4.], [1., 0.], [0., 2.]])
norms = np.linalg.norm(X, axis=1, keepdims=True)    # 每行的 L2 范数，形状 (3, 1)
Xn = X / norms                                      # 每行长度变成 1
print("行范数:", norms.ravel())
print("归一化后每行范数:", np.linalg.norm(Xn, axis=1))
print(np.round(Xn @ Xn.T, 3))                       # [i, j] = 第 i 行和第 j 行的余弦相似度

# 2. 分类准确率
scores = np.array([[0.1, 2.0, 0.3], [1.5, 0.2, 0.1], [0.0, 0.1, 3.0], [2.0, 2.5, 0.0]])
labels = np.array([1, 0, 1, 1])
pred = scores.argmax(axis=1)
print("预测:", pred, " 准确率:", (pred == labels).mean())
''')

C_PAIR = code('''
import numpy as np

rng = np.random.default_rng(1)
A = rng.normal(size=(300, 64))    # 300 个点，每个 64 维
B = rng.normal(size=(200, 64))    # 200 个点

# 写法一：循环（慢，作对照）
D_loop = np.empty((300, 200))
for i in range(300):
    for j in range(200):
        D_loop[i, j] = np.sqrt(((A[i] - B[j]) ** 2).sum())

# 写法二：广播。(300,1,64) - (1,200,64) -> (300,200,64)，再对最后一维求和
diff = A[:, None, :] - B[None, :, :]
D_bc = np.sqrt((diff ** 2).sum(axis=-1))
print("中间张量形状:", diff.shape, " 占内存(MB):", round(diff.nbytes / 1e6, 1))
print("广播 == 循环:", np.allclose(D_bc, D_loop))

# 写法三：展开平方 |a-b|^2 = |a|^2 + |b|^2 - 2 a·b，只用到 (300,200) 的矩阵
sq = (A ** 2).sum(1)[:, None] + (B ** 2).sum(1)[None, :] - 2 * A @ B.T
D_mm = np.sqrt(np.maximum(sq, 0))
print("矩阵乘法版 == 广播版:", np.allclose(D_mm, D_bc))
print("最大差异 < 1e-8:", float(np.abs(D_mm - D_bc).max()) < 1e-8)
print("三种写法的结果形状:", D_loop.shape, D_bc.shape, D_mm.shape)
''')

C_SAMPLE = code('''
import numpy as np

rng = np.random.default_rng(0)
probs = np.array([0.2, 0.3, 0.5])
cum = probs.cumsum()                                    # 累积和 [0.2, 0.5, 1.0]
print("累积和:", cum)

n = 100_000
u = rng.random((n, 1))                                  # (n, 1) 的均匀随机数
samples = (u > cum).sum(axis=1)                         # (n,1) 与 (3,) 广播成 (n,3)，数一数超过了几个边界
freq = np.bincount(samples, minlength=3) / n
print("频率:", np.round(freq, 3), " 目标:", probs)
print("样本取值范围:", samples.min(), "到", samples.max())
''')

C_SOFTMAX = code('''
import numpy as np

z = np.array([1000., 1001., 1002.])
with np.errstate(all="ignore"):
    naive = np.exp(z) / np.exp(z).sum()                 # e^1000 溢出成 inf，inf/inf = nan
print("直接算:", naive)

def softmax(z):
    zs = z - z.max(axis=-1, keepdims=True)              # 减去最大值：最大的指数变成 e^0 = 1
    e = np.exp(zs)
    return e / e.sum(axis=-1, keepdims=True)

print("稳定版:", np.round(softmax(z), 4), " 和为", round(float(softmax(z).sum()), 6))

def logsumexp(z):
    c = z.max(axis=-1, keepdims=True)
    return (c + np.log(np.exp(z - c).sum(axis=-1, keepdims=True))).squeeze(-1)

print("logsumexp:", round(float(logsumexp(z)), 4))

# 平移不变性：给所有 logits 加同一个常数，softmax 不变
z2 = np.array([2.0, 0.5, 0.1])
print("平移不变:", np.allclose(softmax(z2), softmax(z2 + 500)))
''')

C_CE = code('''
import numpy as np

def logsumexp(z):
    c = z.max(axis=-1, keepdims=True)
    return c + np.log(np.exp(z - c).sum(axis=-1, keepdims=True))   # 保留维度 (batch, 1)

logits = np.array([[2.0, 0.5, 0.1], [0.2, 0.2, 3.0]])
target = np.array([0, 2])
logp = logits - logsumexp(logits)                       # log softmax：(2,3) - (2,1) 广播
picked = logp[np.arange(2), target]                     # 整数数组索引：取 logp[0,0] 和 logp[1,2]
print("logp 每行 exp 后求和:", np.exp(logp).sum(axis=1))
print("每个样本正确类别的 log 概率:", np.round(picked, 4))
print("交叉熵 =", round(float(-picked.mean()), 4))

# 对拍：逐样本用概率的定义算
probs = np.exp(logits) / np.exp(logits).sum(axis=1, keepdims=True)
ref = np.mean([-np.log(probs[i, target[i]]) for i in range(2)])
print("和定义式一致:", np.isclose(-picked.mean(), ref))
''')

C_STANDARD = code('''
import numpy as np

# 小实验：对「特征」做标准化（每一列减均值、除标准差）。这就是机器学习里最常见的数据预处理
rng = np.random.default_rng(3)
X = rng.normal(loc=[0, 100, -5], scale=[1, 20, 0.1], size=(1000, 3))   # 三个量纲差别极大的特征
fmt = lambda v: [round(float(x), 2) + 0.0 for x in v]
print("标准化前 每列均值:", fmt(X.mean(axis=0)))
print("标准化前 每列标准差:", fmt(X.std(axis=0)))
Z = (X - X.mean(axis=0)) / X.std(axis=0)             # (1000,3) 与 (3,) 广播
print("标准化后 每列均值:", fmt(Z.mean(axis=0)))
print("标准化后 每列标准差:", fmt(Z.std(axis=0)))

# 如果错把 axis 写成按行（每一行自己减自己的均值），三列的差别并没有被消除
Z_bad = (X - X.mean(axis=1, keepdims=True)) / X.std(axis=1, keepdims=True)
print("按行标准化后 每列均值:", fmt(Z_bad.mean(axis=0)))
print("按行标准化后 每列标准差:", fmt(Z_bad.std(axis=0)))
''')

C_TORCH = code('''
import torch as t
import torch.nn.functional as F

# PyTorch 的写法和 NumPy 几乎一一对应：unsqueeze / squeeze / keepdim
x = t.ones(3, 1, 5)
print("unsqueeze(0):", tuple(x.unsqueeze(0).shape), " unsqueeze(-1):", tuple(x.unsqueeze(-1).shape))
print("squeeze(1)  :", tuple(x.squeeze(1).shape), " squeeze(0) 不报错、什么也不做:", tuple(x.squeeze(0).shape))

m = t.arange(12.).reshape(3, 4)
print("每行减均值后的行均值:", (m - m.mean(dim=1, keepdim=True)).mean(dim=1).tolist())

# softmax / logsumexp / 交叉熵：和我们手写的版本对照
z = t.tensor([1000., 1001., 1002.])
print("t.softmax:", [round(v, 4) for v in t.softmax(z, dim=0).tolist()])
print("t.logsumexp:", round(t.logsumexp(z, dim=0).item(), 4))

logits = t.tensor([[2.0, 0.5, 0.1], [0.2, 0.2, 3.0]])
target = t.tensor([0, 2])
logp = logits - t.logsumexp(logits, dim=1, keepdim=True)
mine = -logp[t.arange(2), target].mean()
print("手写交叉熵:", round(mine.item(), 4), " F.cross_entropy:", round(F.cross_entropy(logits, target).item(), 4))

# 采样：torch 里有现成的 multinomial，和我们手写的 cumsum 技巧得到同样的分布
t.manual_seed(0)
probs = t.tensor([0.2, 0.3, 0.5])
s = t.multinomial(probs, 100000, replacement=True)
print("multinomial 频率:", [round(v, 2) for v in (t.bincount(s) / 100000).tolist()])
''')
