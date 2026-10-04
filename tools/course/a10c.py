from runlib import code

C_ARGS = code('''
import sys

# 1. *args / **kwargs：args 是元组，kwargs 是字典
def f(*args, **kwargs):
    return args, kwargs
print(f(1, 2, lr=0.1))

# 解包：调用时用 * 和 ** 把容器「拆开」传进去
def train(model, lr, epochs):
    return f"{model}: lr={lr}, epochs={epochs}"
cfg = {"lr": 0.01, "epochs": 3}
print(train("mlp", **cfg))

# 2. 推导式：一行建出列表 / 集合 / 字典
print([x * x for x in range(5)])
print({x for x in range(10) if x % 2 == 0})
print({w: len(w) for w in ["cat", "tiger"]})

# 3. 生成器：按需一个个产生值，不用一次性存进内存
def count_up(n):
    for i in range(n):
        yield i
g = count_up(3)
print(next(g), next(g), list(g))           # 用过的值不会再出现

big_list = [i for i in range(1_000_000)]   # 列表：一百万个整数全存下来
big_gen = (i for i in range(1_000_000))    # 生成器表达式：只存「怎么生成」
print("列表占用远大于生成器：", sys.getsizeof(big_list) > 1000 * sys.getsizeof(big_gen))
print("两者求和相同：", sum(big_list) == sum(big_gen))

# 4. enumerate 和 zip
for i, (a, b) in enumerate(zip("xy", [10, 20])):
    print(i, a, b)
''')

C_TRAPS = code('''
import functools
from dataclasses import dataclass

# 5. for / else：else 在循环「没有被 break 打断」时执行
def first_even(xs):
    for x in xs:
        if x % 2 == 0:
            print("找到偶数", x)
            break
    else:
        print("没有偶数")
first_even([1, 3, 5])
first_even([1, 4, 5])

# 6. 可变默认参数的坑：默认值只在函数「定义时」创建一次
def add_item(item, box=[]):
    box.append(item)
    return box
print(add_item(1), add_item(2))            # 两次调用共用了同一个列表

def add_item_ok(item, box=None):
    if box is None:
        box = []
    box.append(item)
    return box
print(add_item_ok(1), add_item_ok(2))

# 7. 装饰器：接收函数、返回新函数；这里给函数加一个「调用计数」
def count_calls(fn):
    @functools.wraps(fn)                   # 保留原函数的名字和文档
    def wrapper(*args, **kwargs):
        wrapper.calls += 1
        return fn(*args, **kwargs)
    wrapper.calls = 0
    return wrapper

@count_calls
def double(x):
    return 2 * x

print(double(4), double(5), "调用了", double.calls, "次，函数名仍是", double.__name__)

# 8. 其他常用的：dataclass、f-string、上下文管理器、类型提示
@dataclass
class Config:
    lr: float = 0.1
    layers: int = 2
print(Config(layers=4))                    # 自动生成了 __init__ 和 __repr__

loss = 0.123456
print(f"loss={loss:.3f}, 百分比 {0.256:.1%}")

import tempfile, os
path = os.path.join(tempfile.mkdtemp(), "a.txt")
with open(path, "w") as fh:               # with 结束时自动关闭文件
    fh.write("hello")
print(fh.closed, open(path).read())
''')

C_ARRAY = code('''
import numpy as np

a = np.arange(12).reshape(3, 4)            # 0..11 排成 3 行 4 列
print(a)
print("shape", a.shape, " ndim", a.ndim, " dtype", a.dtype, " size", a.size)

# 各种创建方式
print(np.zeros((2, 3)).shape, np.ones(3), np.linspace(0, 1, 5), np.arange(0, 10, 3))
rng = np.random.default_rng(0)             # 新式随机数生成器，可以固定种子复现
print(rng.random(3).round(3), rng.integers(0, 10, size=3))

# reshape：-1 表示「这一维让 NumPy 自己算」
print(a.reshape(2, -1).shape, a.reshape(-1).shape, a.T.shape)

# dtype：深度学习里一般用 float32；整数和浮点混着算，会「向上转型」
x = np.array([1, 2, 3])
print(x.dtype, (x / 2).dtype, (x * 1.5).dtype, x.astype(np.float32).dtype)
print("float32 占", np.float32(1).nbytes, "字节，float64 占", np.float64(1).nbytes, "字节")
print("0.1 + 0.2 =", 0.1 + 0.2, " float32 下：", np.float32(0.1) + np.float32(0.2))
''')

C_INDEX = code('''
import numpy as np

a = np.arange(12).reshape(3, 4)
print(a[1])                                # 第 1 行
print(a[:, 2])                             # 第 2 列
print(a[1:, :2].tolist())                  # 第 1 行起、前 2 列
print(a[-1, -1], a[::2, ::2].tolist())     # 负下标、步长

# 布尔掩码：条件产生一个同形状的 True/False 数组，用它当索引
mask = a > 6
print(mask.sum(), "个元素大于 6：", a[mask])
print("偶数且大于 3：", a[(a % 2 == 0) & (a > 3)])    # 多个条件用 & |，每个条件要加括号

# 用掩码赋值：把所有负数改成 0（ReLU 的一种写法）
x = np.array([-2.0, 1.5, -0.5, 3.0])
y = x.copy(); y[y < 0] = 0
print(y, np.maximum(x, 0), np.where(x < 0, 0, x))

# 整数数组索引（fancy indexing）：一次取多个位置
print(a[[0, 2], [1, 3]])                   # 取 a[0,1] 和 a[2,3]
print(a[:, [0, 3]].shape)                  # 取第 0、3 列

# 分类里的典型用法：一批样本的 logits，取出每个样本「正确类别」那一格
logits = np.array([[2.0, 0.1, 0.3], [0.2, 1.5, 0.1], [0.1, 0.2, 3.0]])
labels = np.array([0, 1, 2])
print(logits[np.arange(3), labels])
print("预测对了几个：", int((logits.argmax(axis=1) == labels).sum()))
''')

C_AXIS = code('''
import numpy as np

a = np.arange(12).reshape(3, 4)
print("sum 全部   :", a.sum())
print("axis=0     :", a.sum(axis=0), a.sum(axis=0).shape)   # 把第 0 维消掉：每列一个数
print("axis=1     :", a.sum(axis=1), a.sum(axis=1).shape)   # 把第 1 维消掉：每行一个数
print("keepdims   :", a.sum(axis=1, keepdims=True).shape)   # 保留被消掉的维度（大小变成 1）

# keepdims 的用处：配合后面第 14 节的广播，做「每行减去自己的平均值」
x = np.array([[1.0, 2.0, 3.0], [10.0, 20.0, 30.0]])
centered = x - x.mean(axis=1, keepdims=True)
print(centered.tolist())
print("每行平均值都是 0：", np.allclose(centered.mean(axis=1), 0))

# 标准化 (standardize)：每一列减均值、除标准差
rng = np.random.default_rng(0)
data = rng.normal(loc=5, scale=3, size=(1000, 4))
z = (data - data.mean(axis=0)) / data.std(axis=0)
print("均值：", z.mean(axis=0).round(6) + 0.0, " 标准差：", z.std(axis=0).round(6))

# 三维：(batch, 行, 列) 时，axis 是几就消掉第几维
t = np.ones((2, 3, 4))
print(t.sum(axis=0).shape, t.sum(axis=1).shape, t.sum(axis=(1, 2)).shape)
''')

C_VIEW = code('''
import numpy as np

a = np.arange(12).reshape(3, 4)
b = a[0]                                   # 基本切片：视图 (view)，和 a 共享内存
b[0] = 100
print("改了 b，a[0,0] =", a[0, 0], "  共享内存：", np.shares_memory(a, b))

c = a[0].copy()                            # 副本：独立的内存
c[1] = -1
print("改了 copy，a[0,1] =", a[0, 1], "  共享内存：", np.shares_memory(a, c))

# 哪些操作给视图，哪些给副本？
print("基本切片 a[:, 1]     ：", np.shares_memory(a, a[:, 1]))
print("reshape              ：", np.shares_memory(a, a.reshape(4, 3)))
print("转置 a.T             ：", np.shares_memory(a, a.T))
print("整数数组索引 a[[0,1]]：", np.shares_memory(a, a[[0, 1]]))      # fancy indexing 总是副本
print("布尔掩码 a[a > 5]    ：", np.shares_memory(a, a[a > 5]))        # 布尔掩码也是副本

# 一个常见的坑：以为自己在改 a，其实改的是副本
a2 = np.arange(6)
a2[[0, 1]] += 10                           # 对 a2 本身赋值，会生效
sub = a2[[0, 1]]                           # 先取出（副本），再改
sub += 100
print("a2 =", a2, "（取出的副本被修改，不影响 a2）")

# 赋值 b = a 不是复制，只是给同一个数组起了第二个名字
d = a
d[2, 3] = -99
print("a[2,3] =", a[2, 3], " d is a:", d is a)
''')

C_VEC = code('''
import numpy as np, time

rng = np.random.default_rng(0)
x = rng.normal(size=1_000_000)

# 任务：计算 sum(2*x^2 + 1) —— Python 循环 vs 数组运算
def loop_version(x):
    total = 0.0
    for v in x:
        total += 2 * v * v + 1
    return total

t0 = time.perf_counter(); r1 = loop_version(x);              t_loop = time.perf_counter() - t0
t0 = time.perf_counter(); r2 = float((2 * x ** 2 + 1).sum()); t_vec = time.perf_counter() - t0
print("结果一致：", np.isclose(r1, r2))
print("向量化至少快 10 倍：", t_loop / t_vec > 10)       # 具体倍数每台机器不同，一般是几十到几百倍

# 逐元素乘法 (*) 和矩阵乘法 (@) 完全不同，而且形状相同时不会报错
A = np.array([[1, 2], [3, 4]]); B = np.array([[0, 1], [1, 0]])
print("A * B =", (A * B).tolist(), "  A @ B =", (A @ B).tolist())
''')

C_EXP = code('''
import numpy as np

rng = np.random.default_rng(0)
X = rng.normal(size=(6, 3))                # 6 个点，每个点 3 维

# 任务一：两两距离矩阵 D[i, j] = ||X[i] - X[j]||，先用双重循环写（慢但直观）
def dist_loop(X):
    n = len(X)
    D = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            D[i, j] = np.sqrt(((X[i] - X[j]) ** 2).sum())
    return D

# 向量化写法：广播。X[:, None, :] 形状 (6,1,3)，X[None, :, :] 形状 (1,6,3)，相减得 (6,6,3)
def dist_vec(X):
    diff = X[:, None, :] - X[None, :, :]
    return np.sqrt((diff ** 2).sum(axis=-1))

# 更省内存的写法：|a-b|^2 = |a|^2 + |b|^2 - 2 a·b，只用一次矩阵乘法
def dist_gram(X):
    sq = (X ** 2).sum(axis=1)
    D2 = sq[:, None] + sq[None, :] - 2 * X @ X.T
    return np.sqrt(np.maximum(D2, 0))      # 浮点误差可能让 D2 出现极小的负数，要截成 0

print("循环 = 广播写法：", np.allclose(dist_loop(X), dist_vec(X)))
print("循环 = Gram 写法（容许 1e-6 的误差）：", np.allclose(dist_loop(X), dist_gram(X), atol=1e-6))
print("Gram 写法的对角线是否「严格」为 0：", bool((np.diag(dist_gram(X)) == 0).all()))
print("对角线都是 0、矩阵对称：", np.allclose(np.diag(dist_vec(X)), 0), np.allclose(dist_vec(X), dist_vec(X).T))
i, j = np.unravel_index(np.argmin(dist_vec(X) + np.eye(6) * 1e9), (6, 6))   # 对角线加个大数，免得选中自己
print("最近的两个点：", int(i), int(j))

# 任务二：对一批 logits 的每一行做 softmax（每行和为 1），一行代码、不写循环
logits = rng.normal(size=(4, 5)) * 3
z = logits - logits.max(axis=1, keepdims=True)         # 每行减最大值，数值更稳定
p = np.exp(z) / np.exp(z).sum(axis=1, keepdims=True)
print("每行之和：", p.sum(axis=1).round(6), " 形状", p.shape)

# 对拍：逐行用循环算一遍
p2 = np.stack([np.exp(r - r.max()) / np.exp(r - r.max()).sum() for r in logits])
print("与逐行循环一致：", np.allclose(p, p2))

# 任务三：只用数组运算，数出 1..100 里能被 3 或 5 整除的数有多少个，并求和
n = np.arange(1, 101)
m = (n % 3 == 0) | (n % 5 == 0)
print("个数", int(m.sum()), "和", int(n[m].sum()), " 对拍：", sum(k for k in range(1, 101) if k % 3 == 0 or k % 5 == 0))
''')
