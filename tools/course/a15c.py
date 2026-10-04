from runlib import code

C_EIN = code('''
import numpy as np
from einops import einsum

rng = np.random.default_rng(0)
A = rng.integers(-3, 4, size=(3, 4)).astype(float)
B = rng.integers(-3, 4, size=(4, 2)).astype(float)
v = rng.integers(-3, 4, size=4).astype(float)
u = rng.integers(-3, 4, size=3).astype(float)
M = rng.integers(-3, 4, size=(4, 4)).astype(float)

# 每一行：einsum 写法  ==  传统写法
print("矩阵乘法      ", np.allclose(einsum(A, B, "i j, j k -> i k"), A @ B))
print("矩阵乘向量    ", np.allclose(einsum(A, v, "i j, j -> i"), A @ v))
print("内积          ", np.isclose(einsum(v, v, "i, i ->"), v @ v))
print("外积          ", np.allclose(einsum(u, v, "i, j -> i j"), u[:, None] * v[None, :]))
print("迹            ", np.isclose(einsum(M, "i i ->"), np.trace(M)))
print("按行求和      ", np.allclose(einsum(A, "i j -> i"), A.sum(axis=1)))
print("逐元素乘      ", np.allclose(einsum(A, A, "i j, i j -> i j"), A * A))
print("转置          ", np.allclose(einsum(A, "i j -> j i"), A.T))
print("外积的形状    ", einsum(u, v, "i, j -> i j").shape)

# 同一个函数，NumPy 原生写法（下标是单个字母，没有空格）
print("原生 np.einsum", np.allclose(np.einsum("ij,jk->ik", A, B), A @ B))
''')

C_LOOP = code('''
import numpy as np

# einsum 的真正含义：先给「所有出现过的下标」各开一层循环，再把输出里没有的下标累加起来
# 下面手写 "i j, j k -> i k"：i、k 在输出里（保留），j 不在输出里（求和）
def my_matmul(A, B):
    I, J = A.shape
    J2, K = B.shape
    assert J == J2                    # 同一个下标在不同输入里的长度必须一致
    out = np.zeros((I, K))
    for i in range(I):
        for k in range(K):
            for j in range(J):        # j 是被求和的下标
                out[i, k] += A[i, j] * B[j, k]
    return out

rng = np.random.default_rng(1)
A, B = rng.normal(size=(5, 6)), rng.normal(size=(6, 3))
print("手写循环 == A @ B:", np.allclose(my_matmul(A, B), A @ B))

# 换一个例子："i j, i j ->" 两个下标都不在输出里，全部求和 = 逐元素乘积之和
X, Y = rng.normal(size=(4, 5)), rng.normal(size=(4, 5))
total = sum(X[i, j] * Y[i, j] for i in range(4) for j in range(5))
print("einsum('ij,ij->') == 循环:", np.isclose(np.einsum("ij,ij->", X, Y), total))
print("Frobenius 内积 == trace(X^T Y):", np.isclose(total, np.trace(X.T @ Y)))
''')

C_ATTN = code('''
import numpy as np
from einops import einsum

rng = np.random.default_rng(2)
batch, q_pos, k_pos, d = 2, 10, 12, 8
q = rng.normal(size=(batch, q_pos, d))
k = rng.normal(size=(batch, k_pos, d))
v = rng.normal(size=(batch, k_pos, d))

# 注意力分数：每个 query 位置和每个 key 位置的点积（d 被求和，batch 保留）
scores = einsum(q, k, "batch q_pos d, batch k_pos d -> batch q_pos k_pos")
print("scores 形状:", scores.shape)
print("和 q @ k 转置一致:", np.allclose(scores, q @ k.transpose(0, 2, 1)))

# softmax 沿 k_pos 这一维做（每个 query 对所有 key 的权重和为 1），再用权重对 v 做加权平均
scores = scores / np.sqrt(d)
w = np.exp(scores - scores.max(axis=-1, keepdims=True))
w = w / w.sum(axis=-1, keepdims=True)
out = einsum(w, v, "batch q_pos k_pos, batch k_pos d -> batch q_pos d")
print("每个 query 的权重之和（取前 3 个）:", np.round(w.sum(axis=-1)[0, :3], 6))
print("输出形状:", out.shape, " 和 w @ v 一致:", np.allclose(out, w @ v))

# 线性层 x @ W.T：不用手动转置，按名字对齐
x = rng.normal(size=(5, 16))
W = rng.normal(size=(4, 16))
print("线性层一致:", np.allclose(einsum(x, W, "batch d_in, d_out d_in -> batch d_out"), x @ W.T))
''')

C_PATH = code('''
import numpy as np

# 小实验：同样的结果，不同的计算顺序，计算量可以差很多
rng = np.random.default_rng(3)
A = rng.normal(size=(1000, 10))
B = rng.normal(size=(10, 1000))
C = rng.normal(size=(1000, 5))

# (A @ B) @ C：先得到 1000x1000 的大矩阵；A @ (B @ C)：先得到 10x5 的小矩阵
flops_left  = 1000 * 10 * 1000 + 1000 * 1000 * 5
flops_right = 10 * 1000 * 5 + 1000 * 10 * 5
print("(A@B)@C 约需乘加次数:", flops_left)
print("A@(B@C) 约需乘加次数:", flops_right)
print("两种顺序结果一致:", np.allclose((A @ B) @ C, A @ (B @ C)))

# np.einsum 默认逐字照做；optimize=True 会自己找更省的顺序
path, info = np.einsum_path("ij,jk,kl->il", A, B, C, optimize="optimal")
print("einsum_path 选择的收缩顺序:", path)
print("einsum 的 optimize 结果和直接算一致:",
      np.allclose(np.einsum("ij,jk,kl->il", A, B, C, optimize=True), (A @ B) @ C))
''')

C_INDEX = code('''
import numpy as np

# 1. 用下标数组索引：结果的形状 = 下标数组的形状
prices = np.array([2.0, 5.0, 1.5])
items = np.array([0, 2, 2, 1, 0])
print("prices[items]       :", prices[items], " 总价:", prices[items].sum())
print("二维下标数组 -> 二维结果:", prices[np.array([[0, 1], [2, 2]])].shape)

# 2. 取行、取列、逐对取元素
mat = np.arange(12).reshape(3, 4)
print("取第 0、2 行        :", mat[[0, 2]].tolist())
print("取第 1、3 列        :", mat[:, [1, 3]].tolist())
rows, cols = np.array([0, 1, 2]), np.array([3, 0, 1])
print("逐对 (0,3)(1,0)(2,1):", mat[rows, cols])

# 3. 想要「行 x 列」的子矩阵，要用 np.ix_，或者连续做两次索引
print("mat[[0, 2]][:, [1, 3]] :", mat[[0, 2]][:, [1, 3]].tolist())
print("np.ix_ 版本一致        :", np.array_equal(mat[np.ix_([0, 2], [1, 3])], mat[[0, 2]][:, [1, 3]]))

# 4. 两个下标数组也会广播：(3,1) 的行 与 (4,) 的列 -> (3,4)，整张表都取出来
print("下标广播的结果形状     :", mat[np.arange(3)[:, None], np.arange(4)].shape)

# 5. 坐标存成 (n, 2) 的数组：转置后拆成元组
coords = np.array([[0, 3], [1, 0], [2, 1]])
print("mat[tuple(coords.T)]   :", mat[tuple(coords.T)])
''')

C_COPY = code('''
import numpy as np

# 切片是视图（改它会改原数组），整数数组索引是副本
a = np.arange(6)
view = a[1:4]
view[0] = 100
print("切片是视图，原数组被改了:", a)

b = np.arange(6)
copy = b[[1, 2, 3]]
copy[0] = 100
print("数组索引是副本，原数组没变:", b)

# 往数组索引的位置「赋值」是可以的；但下标重复时，+= 只生效一次
z = np.zeros(4)
idx = np.array([0, 1, 1, 1, 3])
z[idx] += 1
print("z[idx] += 1            :", z, "  <- 下标 1 出现了 3 次，却只加了 1")
z2 = np.zeros(4)
np.add.at(z2, idx, 1)
print("np.add.at 才会累加     :", z2)
print("等价于 bincount        :", np.bincount(idx, minlength=4).astype(float))
''')

C_EMBED = code('''
import numpy as np

# 词嵌入 = 查表：W_E 形状 (词表大小, 嵌入维度)；token_ids 形状 (batch, seq)
rng = np.random.default_rng(4)
vocab, d_model = 50, 6
W_E = rng.normal(size=(vocab, d_model))
token_ids = np.array([[3, 7, 7, 0], [49, 1, 3, 3]])      # 2 句话，每句 4 个 token
emb = W_E[token_ids]                                     # 下标数组形状 + 取出的行形状
print("token_ids 形状:", token_ids.shape, "-> 嵌入形状:", emb.shape)
print("相同 token 得到相同的向量:", np.array_equal(emb[0, 1], emb[0, 2]))

# 等价写法：独热向量 @ 矩阵（慢得多，只是为了说明「查表 = 乘以独热向量」）
one_hot = np.eye(vocab)[token_ids]                       # (2, 4, 50)
emb2 = one_hot @ W_E                                     # (2, 4, 50) @ (50, 6) -> (2, 4, 6)
print("独热矩阵乘法结果相同:", np.allclose(emb, emb2))
print("独热张量元素数:", one_hot.size, " 查表读取的元素数:", emb.size)

# 取出「每个样本正确类别的概率」：和上一节手写交叉熵是同一个操作
probs = np.array([[0.7, 0.2, 0.1], [0.1, 0.1, 0.8]])
target = np.array([0, 2])
print("probs[arange, target]:", probs[np.arange(2), target])
print("独热点乘求和版本     :", (probs * np.eye(3)[target]).sum(axis=1))
''')

C_GATHER = code('''
import numpy as np

mat = np.arange(12).reshape(3, 4)
idx = np.array([[3, 0], [1, 1], [0, 2]])

# torch.gather(input, 1, index) 在 NumPy 里叫 take_along_axis
out = np.take_along_axis(mat, idx, axis=1)
print(out.tolist())
print("输出形状和 index 一样:", out.shape == idx.shape)

# 按定义手写：out[i][j] = input[i][index[i][j]]
manual = np.empty_like(idx)
for i in range(idx.shape[0]):
    for j in range(idx.shape[1]):
        manual[i, j] = mat[i, idx[i, j]]
print("和定义一致:", np.array_equal(out, manual))

# 用 gather 取每个样本正确类别的分数：index 必须和 input 维数相同，所以要先加一维
scores = np.array([[0.1, 2.0, 0.3], [1.5, 0.2, 0.1], [0.0, 0.1, 3.0]])
labels = np.array([1, 0, 2])
via_gather = np.take_along_axis(scores, labels[:, None], axis=1)[:, 0]
via_index = scores[np.arange(3), labels]
print("gather 版:", via_gather, " 数组索引版:", via_index, " 一致:", np.array_equal(via_gather, via_index))

# 对拍：随机形状下 gather 与定义一致
rng = np.random.default_rng(5)
ok = True
for _ in range(200):
    n, m, k = rng.integers(1, 6, size=3)
    X = rng.normal(size=(n, m))
    I = rng.integers(0, m, size=(n, k))
    ref = np.array([[X[i, I[i, j]] for j in range(k)] for i in range(n)])
    ok &= np.array_equal(np.take_along_axis(X, I, axis=1), ref)
print("200 组随机对拍通过:", bool(ok))
''')

C_TORCH = code('''
import torch as t
import einops
from einops import einsum

# einops.einsum 对 torch 张量同样适用
A, B = t.randn(3, 4), t.randn(4, 2)
print("矩阵乘法:", t.allclose(einsum(A, B, "i j, j k -> i k"), A @ B, atol=1e-6))
M = t.randn(4, 4)
print("迹:", t.allclose(einsum(M, "i i ->"), t.trace(M), atol=1e-6))

q, k = t.randn(2, 10, 8), t.randn(2, 12, 8)
print("注意力分数形状:", tuple(einsum(q, k, "batch q_pos d, batch k_pos d -> batch q_pos k_pos").shape))

# 整数数组索引与 gather
mat = t.arange(12).reshape(3, 4)
idx = t.tensor([[3, 0], [1, 1], [0, 2]])
print("gather:", mat.gather(1, idx).tolist())
print("逐对索引:", mat[t.tensor([0, 1, 2]), t.tensor([3, 0, 1])].tolist())

# gather 与数组索引取「正确类别」的分数
scores = t.tensor([[0.1, 2.0, 0.3], [1.5, 0.2, 0.1], [0.0, 0.1, 3.0]])
labels = t.tensor([1, 0, 2])
a = scores.gather(1, labels.unsqueeze(1)).squeeze(1)
b = scores[t.arange(3), labels]
print("gather:", a.tolist(), " 数组索引:", b.tolist(), " 一致:", bool((a == b).all()))

# 词嵌入：nn.Embedding 的本质就是查表
emb = t.nn.Embedding(50, 6)
ids = t.tensor([[3, 7, 7, 0], [49, 1, 3, 3]])
print("Embedding 输出形状:", tuple(emb(ids).shape), " 等价于 weight[ids]:", bool((emb(ids) == emb.weight[ids]).all()))
''')
