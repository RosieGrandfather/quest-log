from runlib import code

C_VEC = code('''
import numpy as np

# 基向量：x 轴方向和 y 轴方向的单位向量
i_hat = np.array([1, 0])
j_hat = np.array([0, 1])

v = np.array([3, -2])
combo = 3 * i_hat + (-2) * j_hat       # 线性组合：数乘再相加
print("3*i + (-2)*j =", combo, " 等于 v：", bool((combo == v).all()))

# 换一组基向量，同一个箭头就有不同的坐标（第 5 节会细讲）
u1, u2 = np.array([1, 1]), np.array([1, -1])
print("v 用 u1, u2 表示：", 0.5 * u1 + 2.5 * u2, "（还是 v，只是坐标变成 (0.5, 2.5)）")
''')

C_LINEAR = code('''
import numpy as np

# 三个「变换」：旋转 90 度、剪切、平移（平移不是线性的）
R = np.array([[0, -1], [1, 0]])                 # 逆时针旋转 90 度
S = np.array([[1, 1], [0, 1]])                  # 剪切：把 y 的一部分加到 x 上
T_rot = lambda v: R @ v
T_shear = lambda v: S @ v
T_shift = lambda v: v + np.array([1, 0])        # 整体向右平移 1
T_relu = lambda v: np.maximum(0, v)             # 逐分量取 max(0, .)，神经网络里的激活函数

def is_linear(T, trials=100, seed=0):
    """随机检验两条性质：T(u+v) = T(u)+T(v)；T(c*v) = c*T(v)"""
    r = np.random.default_rng(seed)
    for _ in range(trials):
        u, v, c = r.normal(size=2), r.normal(size=2), r.normal()
        if not np.allclose(T(u + v), T(u) + T(v)): return False
        if not np.allclose(T(c * v), c * T(v)): return False
    return True

for name, T in [("旋转", T_rot), ("剪切", T_shear), ("平移", T_shift), ("ReLU", T_relu)]:
    print(f"{name:<3} 是线性变换吗？{is_linear(T)}   原点去了哪里：{T(np.zeros(2))}")
''')

C_COLS = code('''
import numpy as np

# 矩阵的列 = 基向量变换之后落到的位置
i_new = np.array([0, 1])       # 逆时针转 90 度后，i_hat (1,0) 落在 (0,1)
j_new = np.array([-1, 0])      # j_hat (0,1) 落在 (-1,0)
R = np.column_stack([i_new, j_new])
print("把两个落点当作两列：\\n", R)

v = np.array([3, -2])
print("R @ v          =", R @ v)
print("3*列1 + (-2)*列2 =", 3 * R[:, 0] + (-2) * R[:, 1], "（矩阵乘向量 = 各列的线性组合）")

# 同一个结果的另一种读法：每个输出分量 = 一行与 v 的点积
print("按行读：", [int(R[0] @ v), int(R[1] @ v)])

# 单位正方形的四个角被送到哪里？面积变了吗？
S = np.array([[1, 1], [0, 1]])                  # 剪切
corners = np.array([[0, 0], [1, 0], [1, 1], [0, 1]]).T      # 每列是一个角
print("剪切后的四个角（每列一个）：\\n", S @ corners)
print("剪切前后面积都是 1：", abs(np.linalg.det(S)))
''')

C_COMP = code('''
import numpy as np

R = np.array([[0, -1], [1, 0]])               # 旋转 90 度
S = np.array([[1, 1], [0, 1]])                # 剪切
v = np.array([3, -2])

print("先旋转再剪切 S@R =\\n", S @ R)
print("先剪切再旋转 R@S =\\n", R @ S)
print("S@R == R@S ？", bool((S @ R == R @ S).all()), "；对 v：", S @ R @ v, "和", R @ S @ v)
print("(S@R)@v 与 S@(R@v) 相同：", bool(((S @ R) @ v == S @ (R @ v)).all()))

# AB 的第 j 列 = A 乘以 B 的第 j 列
A = np.random.default_rng(0).integers(-3, 4, size=(3, 3))
B = np.random.default_rng(1).integers(-3, 4, size=(3, 3))
print("AB 的第 j 列 = A @ B 的第 j 列：", all((A @ B)[:, j].tolist() == (A @ B[:, j]).tolist() for j in range(3)))

# 结合律成立；交换律一般不成立：随机试 1000 对 3x3 矩阵
r = np.random.default_rng(2)
assoc, comm = 0, 0
for _ in range(1000):
    X, Y, Z = (r.integers(-3, 4, size=(3, 3)) for _ in range(3))
    assoc += bool(((X @ Y) @ Z == X @ (Y @ Z)).all())
    comm += bool((X @ Y == Y @ X).all())
print("1000 次里 结合律成立：", assoc, "次；交换律成立：", comm, "次")

# 上一节的结论：去掉激活函数，三层网络合并成一个矩阵（形状只看两头）
W1, W2, W3 = (np.random.default_rng(k).normal(size=s) for k, s in [(3, (16, 784)), (4, (16, 16)), (5, (10, 16))])
print("W3 @ W2 @ W1 的形状：", (W3 @ W2 @ W1).shape)
''')

C_SHAPE = code('''
import numpy as np
rng = np.random.default_rng(0)

A = rng.normal(size=(3, 4))
B = rng.normal(size=(4, 5))
print("(3,4) @ (4,5) ->", (A @ B).shape)
try:
    B @ A                                           # (4,5) @ (3,4)：中间维度 5 != 3
except ValueError as e:
    print("(4,5) @ (3,4) 报错：", str(e)[:60])

# 非方阵 = 在不同维度之间的变换。M 是 3x2：把二维平面送进三维空间
M = np.array([[1., 0.], [0., 1.], [1., 1.]])        # 两列各是一个三维向量
pts2d = rng.normal(size=(2, 1000))                  # 1000 个二维点（每列一个）
pts3d = M @ pts2d
print("输入形状", pts2d.shape, "-> 输出形状", pts3d.shape)
print("所有输出都落在平面 z = x + y 上：", bool(np.allclose(pts3d[2], pts3d[0] + pts3d[1])))
print("输出点云的秩（占几维）：", np.linalg.matrix_rank(pts3d), "（三维空间里只有一个平面）")

# 神经网络的写法：一批样本，每行一个样本，W 的形状是 (输出维数, 输入维数)
W = rng.normal(size=(16, 784))
X = rng.normal(size=(32, 784))
print("单个样本 W @ x:", (W @ X[0]).shape, "；一批 X @ W.T:", (X @ W.T).shape)
print("两种写法的结果一致：", bool(np.allclose((X @ W.T)[0], W @ X[0])))
''')

C_FIT = code('''
import numpy as np
rng = np.random.default_rng(0)

A_true = np.array([[2.0, -1.0], [0.5, 3.0]])     # 一个「黑箱」线性变换，我们假装不知道它

# 办法一：直接问它「i_hat 和 j_hat 去哪了」，得到的就是两列
print("把 (1,0) 和 (0,1) 喂进去，输出按列排好：\\n", np.column_stack([A_true @ [1, 0], A_true @ [0, 1]]))

# 办法二：只能拿到带噪声的随机样本，用最小二乘从数据里「学」出矩阵
X = rng.normal(size=(50, 2))                        # 50 个输入，每行一个样本
Y = X @ A_true.T + 0.05 * rng.normal(size=(50, 2))  # 观测到的输出，带一点噪声
W_hat = np.linalg.lstsq(X, Y, rcond=None)[0].T      # 解 X W^T = Y
print("最小二乘恢复的矩阵：\\n", np.round(W_hat, 3))

# 办法三：梯度下降（和神经网络训练同一个思路）。代价 = 平均平方误差
W = np.zeros((2, 2))
for step in range(200):
    pred = X @ W.T
    grad = 2 / len(X) * (pred - Y).T @ X            # dC/dW，用上一节的链式法则推出
    W -= 0.1 * grad
print("梯度下降 200 步后：\\n", np.round(W, 3))
print("两种办法接近：", bool(np.allclose(W, W_hat, atol=1e-3)))
''')
