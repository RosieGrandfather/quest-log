from runlib import code

C_DET = code('''
import numpy as np

def area(P):
    """多边形面积（鞋带公式）。P 的每一列是一个顶点，按顺序排列"""
    x, y = P
    return 0.5 * abs(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1)))

square = np.array([[0, 1, 1, 0], [0, 0, 1, 1]], dtype=float)           # 单位正方形，面积 1
tri = np.array([[0, 2, 1], [0, 0, 3]], dtype=float)                    # 一个任意三角形

mats = {
    "缩放 2x3": np.array([[2.0, 0], [0, 3]]),
    "旋转 90 度": np.array([[0.0, -1], [1, 0]]),
    "剪切": np.array([[1.0, 1], [0, 1]]),
    "反射(交换 x y)": np.array([[0.0, 1], [1, 0]]),
    "一般矩阵": np.array([[2.0, 1], [1, 3]]),
    "压扁(第2列=2倍第1列)": np.array([[1.0, 2], [2, 4]]),
}
print(f"{'变换':<22}{'det':>7}{'正方形面积':>12}{'三角形面积比':>14}")
for name, M in mats.items():
    print(f"{name:<22}{np.linalg.det(M):>7.2f}{area(M @ square):>12.2f}{area(M @ tri) / area(tri):>14.2f}")

# 乘积的行列式 = 行列式的乘积；和的行列式不等于行列式的和
r = np.random.default_rng(0)
A, B = r.normal(size=(4, 4)), r.normal(size=(4, 4))
print("det(AB) = det(A)det(B) ？", bool(np.isclose(np.linalg.det(A @ B), np.linalg.det(A) * np.linalg.det(B))))
print("det(A+B) = det(A)+det(B) ？", bool(np.isclose(np.linalg.det(A + B), np.linalg.det(A) + np.linalg.det(B))))
''')

C_INV = code('''
import numpy as np

A = np.array([[2.0, 1.0], [1.0, 3.0]])
Ainv = np.linalg.inv(A)
print("det(A) =", round(float(np.linalg.det(A)), 3))
print("A 的逆：\\n", np.round(Ainv, 3))
print("A^-1 @ A = I ？", bool(np.allclose(Ainv @ A, np.eye(2))))

v = np.array([1.0, -2.0])
print("先变换再倒回去，得到原向量：", np.round(Ainv @ (A @ v), 6))

# 解方程 A x = b：x = A^-1 b，但实际用 solve（更快、更稳）
b = np.array([5.0, 10.0])
print("solve:", np.linalg.solve(A, b), " inv@b:", Ainv @ b)

# 压扁的矩阵没有逆：不同输入被送到了同一个输出
S = np.array([[1.0, 2.0], [2.0, 4.0]])
print("S @ (2,0) =", S @ np.array([2.0, 0.0]), "；S @ (0,1) =", S @ np.array([0.0, 1.0]), "（输入不同，输出相同）")
try:
    np.linalg.inv(S)
except np.linalg.LinAlgError as e:
    print("求逆报错：", e)

# 「几乎压扁」的矩阵：行列式很小，数值上很危险
N = np.array([[1.0, 1.0], [1.0, 1.0 + 1e-10]])
print("几乎奇异矩阵的 det =", f"{np.linalg.det(N):.1e}", "；条件数 =", f"{np.linalg.cond(N):.1e}")
''')

C_RANK = code('''
import numpy as np

# 第 3 列 = 第 1 列 + 第 2 列：三个方向里有一个是多余的
M = np.array([[1.0, 0.0, 1.0],
              [0.0, 1.0, 1.0],
              [2.0, 3.0, 5.0]])
print("det(M) =", round(float(np.linalg.det(M)), 6), "；rank(M) =", np.linalg.matrix_rank(M))

# 所有输出都落在一个平面上：把很多随机输入送进去，看输出占几维
X = np.random.default_rng(0).normal(size=(3, 500))
print("500 个输出点的秩：", np.linalg.matrix_rank(M @ X), "（三维空间里的一个平面）")

# 零空间：被送到原点的向量。用 SVD 找到它（SVD 第 6 节讲）
U, s, Vt = np.linalg.svd(M)
print("奇异值：", np.round(s, 4))
null_vec = Vt[-1]                                  # 最小奇异值对应的方向
print("零空间的一个单位向量：", np.round(null_vec, 4), "；M @ 它 =", np.round(M @ null_vec, 6))
print("(1, 1, -1) 也被送到原点：", M @ np.array([1.0, 1.0, -1.0]))

# 秩-零化度定理：列数 = 秩 + 零空间维数。用一个 5x8 的低秩矩阵验证
r = np.random.default_rng(1)
P = r.normal(size=(5, 3)) @ r.normal(size=(3, 8))      # 两个「瘦」矩阵相乘
rank = np.linalg.matrix_rank(P)
_, s2, Vt2 = np.linalg.svd(P)
null_basis = Vt2[rank:].T                                # 8 - rank 个方向组成零空间的基
print("P 的形状", P.shape, "；rank =", rank, "；零空间维数 =", null_basis.shape[1], "；rank + 零空间维数 =", rank + null_basis.shape[1], "= 列数 8")
print("P @ 零空间的基 ≈ 0 ：", bool(np.allclose(P @ null_basis, 0)))
''')

C_LOWRANK = code('''
import numpy as np
r = np.random.default_rng(0)

# Transformer 里常见的结构：把 768 维压到 64 维再展开回 768 维
W1 = r.normal(size=(768, 64))
W2 = r.normal(size=(64, 768))
W = W1 @ W2
print("W 的形状", W.shape, "，元素个数", W.size, "；两个因子的参数个数", W1.size + W2.size)
print("rank(W1) =", np.linalg.matrix_rank(W1), "，rank(W2) =", np.linalg.matrix_rank(W2), "，rank(W) =", np.linalg.matrix_rank(W), "（上限 min(768,64,768)=64）")

# 秩不等式：rank(AB) <= min(rank A, rank B)。把 A 换成秩 2 的矩阵试试
A = r.normal(size=(6, 2)) @ r.normal(size=(2, 6))
B = r.normal(size=(6, 6))                          # 满秩
print("rank(A) =", np.linalg.matrix_rank(A), "，rank(B) =", np.linalg.matrix_rank(B), "，rank(AB) =", np.linalg.matrix_rank(A @ B), "，rank(BA) =", np.linalg.matrix_rank(B @ A))

# 现实里数据带噪声：低秩矩阵加一点点噪声，「严格的秩」就变成了满秩
Wn = W + 1e-3 * r.normal(size=W.shape)
s = np.linalg.svd(Wn, compute_uv=False)
print("加噪声后默认的 rank =", np.linalg.matrix_rank(Wn))
print("奇异值 第 64 个 =", round(float(s[63]), 1), "，第 65 个 =", round(float(s[64]), 3), "，说明「有效秩」是 64")
print("手动设阈值 tol=1 的 rank =", np.linalg.matrix_rank(Wn, tol=1.0))
''')

C_TRANS = code('''
import numpy as np
r = np.random.default_rng(0)

A = r.normal(size=(3, 4))
B = r.normal(size=(4, 5))
print("A.T 的形状", A.T.shape, "；(AB).T 的形状", (A @ B).T.shape)
print("(AB)^T = B^T A^T ？", bool(np.allclose((A @ B).T, B.T @ A.T)))
try:
    A.T @ B.T                                       # (4,3) @ (5,4)：中间 3 != 5
except ValueError:
    print("A^T B^T 形状对不上，直接报错")

# 点积 = u^T v；A^T A 总是对称的
u, v = np.array([1.0, 2.0, 3.0]), np.array([4.0, -5.0, 6.0])
print("u^T v =", u @ v, "（点积）")
G = A.T @ A
print("A^T A 的形状", G.shape, "；对称：", bool(np.allclose(G, G.T)))
print("rank(A^T) = rank(A) =", np.linalg.matrix_rank(A.T), np.linalg.matrix_rank(A))

# 注意力：Q K^T 一次算出每对 token 的点积
Q = r.normal(size=(6, 4))                           # 6 个 token，每个 query 是 4 维
K = r.normal(size=(6, 4))
scores = Q @ K.T
print("Q K^T 的形状：", scores.shape, "；scores[2,5] = q_2 . k_5 ？", bool(np.isclose(scores[2, 5], Q[2] @ K[5])))
''')

C_TRACE = code('''
import numpy as np
r = np.random.default_rng(0)

A = r.normal(size=(3, 4))
B = r.normal(size=(4, 3))
print("AB 是", (A @ B).shape, "，BA 是", (B @ A).shape, "（形状不同）")
print("tr(AB) =", round(float(np.trace(A @ B)), 6), "，tr(BA) =", round(float(np.trace(B @ A)), 6))

# 线性性与转置
C, D = r.normal(size=(4, 4)), r.normal(size=(4, 4))
print("tr(C+D) = tr(C)+tr(D) ：", bool(np.isclose(np.trace(C + D), np.trace(C) + np.trace(D))))
print("tr(C^T) = tr(C) ：", bool(np.isclose(np.trace(C.T), np.trace(C))))

# 迹 = 特征值之和，行列式 = 特征值之积（第 6 节讲特征值）
S = C + C.T                                          # 对称矩阵，特征值都是实数
eig = np.linalg.eigvalsh(S)
print("tr(S) =", round(float(np.trace(S)), 6), "，特征值之和 =", round(float(eig.sum()), 6))
print("det(S) =", round(float(np.linalg.det(S)), 6), "，特征值之积 =", round(float(eig.prod()), 6))

# 一个常用技巧：tr(A^T B) = A 和 B 所有对应元素乘积之和（相当于把矩阵拉直再做点积）
E, F = r.normal(size=(3, 4)), r.normal(size=(3, 4))
print("tr(E^T F) = sum(E * F) ：", bool(np.isclose(np.trace(E.T @ F), (E * F).sum())))
''')
