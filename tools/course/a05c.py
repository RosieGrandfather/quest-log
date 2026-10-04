"""ARENA 0.0 第 5 节的代码块（NumPy，真实运行）"""
from runlib import code

C_SPAN = code('''
import numpy as np

# 三个三维向量：第三个是前两个之和
v1, v2, v3 = np.array([1, 0, 0]), np.array([0, 1, 0]), np.array([1, 1, 0])
A = np.stack([v1, v2, v3], axis=1)          # 把它们当作列，拼成 3x3 矩阵
print("秩 =", np.linalg.matrix_rank(A))      # 秩 = 线性无关的向量个数 = 张成空间的维数

# 能不能组合出 (0, 0, 1)？用最小二乘找「最接近」的组合
target = np.array([0.0, 0.0, 1.0])
coef, *_ = np.linalg.lstsq(A, target, rcond=None)
print("最佳组合的误差 =", round(float(np.linalg.norm(A @ coef - target)), 3))   # 误差 1 = 完全够不着

# 换一组真正的基：(1,1,0)、(1,-1,0)、(0,0,1)
B = np.array([[1, 1, 0], [1, -1, 0], [0, 0, 1]]).T
print("新基的秩 =", np.linalg.matrix_rank(B), " 行列式 =", round(float(np.linalg.det(B)), 3))
x = np.array([3.0, 1.0, 2.0])
c = np.linalg.solve(B, x)                   # 解 B @ c = x：x 在新基下的坐标
print("坐标 c =", c, " 还原 B @ c =", B @ c)

# 二维里两个共线向量
print("共线 (1,2),(2,4) 的秩 =", np.linalg.matrix_rank(np.array([[1, 2], [2, 4]])))
''')

C_DOT = code('''
import numpy as np

# 构造两个已知夹角的向量：u 长 2、方向 30 度；v 长 3、方向 80 度，夹角 50 度
th_u, th_v = np.deg2rad(30), np.deg2rad(80)
u = 2 * np.array([np.cos(th_u), np.sin(th_u)])
v = 3 * np.array([np.cos(th_v), np.sin(th_v)])

# 定义一：对应分量相乘再相加；定义二：长度 x 长度 x cos(夹角)
print("分量定义 :", round(float(u @ v), 4))
print("几何定义 :", round(float(2 * 3 * np.cos(np.deg2rad(50))), 4))

# 余弦相似度：点积除以两个长度，只剩方向
def cos_sim(a, b):
    return a @ b / (np.linalg.norm(a) * np.linalg.norm(b))

print("夹角 =", round(float(np.degrees(np.arccos(cos_sim(u, v)))), 1), "度")

# 投影：u 在 v 方向上的「影子」长度 = u 和 v 的单位向量的点积
v_hat = v / np.linalg.norm(v)
print("u 在 v 上的投影长度 =", round(float(u @ v_hat), 4))

# 缩放长度不改变余弦相似度；点积却会跟着变
print("v 放大 10 倍：点积", round(float(u @ (10 * v)), 2), " 余弦", round(float(cos_sim(u, 10 * v)), 4))

# 玩具「词向量」（4 维，手编的）
words = {"cat": [0.9, 0.8, 0.1, 0.0], "dog": [0.8, 0.9, 0.2, 0.1], "car": [0.1, 0.0, 0.9, 0.8]}
w = {k: np.array(x) for k, x in words.items()}
print("cat-dog:", round(float(cos_sim(w["cat"], w["dog"])), 3), " cat-car:", round(float(cos_sim(w["cat"], w["car"])), 3))

# (3,4) 与 (4,-3)：点积 0，正交
print("(3,4)·(4,-3) =", np.dot([3, 4], [4, -3]))
''')

C_CHANGE = code('''
import numpy as np

# 对方的基向量，用「我们的」坐标写出：b1 = (2,1)，b2 = (-1,1)；它们当作 B 的列
B = np.array([[2.0, -1.0], [1.0, 1.0]])
c = np.array([3.0, 2.0])                     # 对方说的坐标：「3 个 b1 加 2 个 b2」
x = B @ c                                    # 翻译成我们的坐标
print("我们的坐标 x =", x)
print("再翻译回去 B^-1 x =", np.linalg.inv(B) @ x)

# 一个用我们的坐标写的变换：逆时针旋转 90 度
M = np.array([[0.0, -1.0], [1.0, 0.0]])
M_B = np.linalg.inv(B) @ M @ B               # 同一个变换，在对方坐标下的矩阵
print("M_B =")
print(np.round(M_B, 3))

# 检验：两条路线得到同一个结果
# 路线一：先翻译成我们的坐标，用 M，再翻译回去
route1 = np.linalg.inv(B) @ (M @ (B @ c))
# 路线二：直接在对方坐标里用 M_B
route2 = M_B @ c
print("两条路线一致：", bool(np.allclose(route1, route2)), route2)

# 相似矩阵：换基不改变迹和行列式（它们描述的是变换本身，不是坐标）
print("迹：", np.trace(M), round(float(np.trace(M_B)), 6) + 0.0, "  行列式：", round(float(np.linalg.det(M)), 6), round(float(np.linalg.det(M_B)), 6))
''')

C_ORTHO = code('''
import numpy as np

th = np.deg2rad(30)
Q = np.array([[np.cos(th), -np.sin(th)], [np.sin(th), np.cos(th)]])   # 逆时针转 30 度

print("Q^T Q =")
print(np.round(Q.T @ Q, 6))                                  # 单位矩阵：Q 是正交矩阵
print("逆 = 转置：", bool(np.allclose(np.linalg.inv(Q), Q.T)), " 行列式 =", round(float(np.linalg.det(Q)), 3))

rng = np.random.default_rng(0)
x = rng.normal(size=2)
print("长度保持：", round(float(np.linalg.norm(x)), 4), "->", round(float(np.linalg.norm(Q @ x)), 4))
y = rng.normal(size=2)
print("点积保持：", round(float(x @ y), 4), "->", round(float((Q @ x) @ (Q @ y)), 4))

# 标准正交基：坐标就是点积，不用求逆
q1, q2 = Q[:, 0], Q[:, 1]                                    # Q 的两列是一组标准正交基
dots = np.array([x @ q1, x @ q2])
print("点积法坐标：", np.round(dots, 4), " 求逆法坐标：", np.round(np.linalg.solve(Q, x), 4))

# 对比：不正交的基，点积不是坐标
B = np.array([[1.0, 1.0], [0.0, 1.0]])                       # 列 (1,0) 和 (1,1)，不垂直
print("非正交基 点积：", np.round(B.T @ x, 4), " 真实坐标：", np.round(np.linalg.solve(B, x), 4))

# 反射矩阵：也是正交的，但行列式 -1
F = np.array([[1.0, 0.0], [0.0, -1.0]])
print("反射 F^T F = I：", bool(np.allclose(F.T @ F, np.eye(2))), " det =", np.linalg.det(F))
''')

C_EXPER = code('''
import numpy as np
rng = np.random.default_rng(0)

# 实验一：高维空间里，随机方向几乎互相垂直
def mean_abs_cos(d, n_pairs=2000):
    a = rng.normal(size=(n_pairs, d)); b = rng.normal(size=(n_pairs, d))
    cos = (a * b).sum(1) / (np.linalg.norm(a, axis=1) * np.linalg.norm(b, axis=1))
    return np.abs(cos).mean()

for d in [2, 10, 100, 1000]:
    print(f"d = {d:5d}  随机两向量 |cos| 的平均 = {mean_abs_cos(d):.3f}")

# 实验二：在 d=50 维里塞进 200 个随机方向，最坏的一对有多接近？
d, k = 50, 200
V = rng.normal(size=(k, d)); V /= np.linalg.norm(V, axis=1, keepdims=True)
G = V @ V.T; np.fill_diagonal(G, 0)
print("200 个方向，d=50：平均 |cos| =", round(float(np.abs(G).mean()), 3), " 最大 |cos| =", round(float(np.abs(G).max()), 3))

# 实验三：两个独立「概念」，方向不是神经元轴，而是旋转后的一对正交方向
f1 = np.array([0.6, 0.8]); f2 = np.array([-0.8, 0.6])
s1, s2 = rng.normal(size=5000), rng.normal(size=5000)        # 每个样本里两个概念各有多强
acts = s1[:, None] * f1 + s2[:, None] * f2                   # 两个「神经元」的激活值（标准基下的坐标）
def corr(a, b):
    return round(float(np.corrcoef(a, b)[0, 1]), 2)
print("神经元 1 与概念 1、概念 2 的相关：", corr(acts[:, 0], s1), corr(acts[:, 0], s2))
print("神经元 2 与概念 1、概念 2 的相关：", corr(acts[:, 1], s1), corr(acts[:, 1], s2))
R = np.stack([f1, f2])                                       # 换基：R 的行是新基，正交，所以坐标 = 点积
new = acts @ R.T
print("沿 f1 的坐标与概念 1、概念 2 的相关：", corr(new[:, 0], s1), corr(new[:, 0], s2))
print("沿 f2 的坐标与概念 1、概念 2 的相关：", corr(new[:, 1], s1), corr(new[:, 1], s2))
''')
