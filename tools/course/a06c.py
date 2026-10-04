"""ARENA 0.0 第 6 节的代码块（NumPy，真实运行）"""
from runlib import code

C_EIG = code('''
import numpy as np

A = np.array([[3.0, 1.0], [0.0, 2.0]])
vals, vecs = np.linalg.eig(A)                 # vals：特征值；vecs 的每一「列」是对应的特征向量（已归一化）
print("特征值：", vals)
print("特征向量（列）：")
print(np.round(vecs, 3))

# 验证定义 A v = lambda v
for lam, v in zip(vals, vecs.T):
    print(f"lambda = {lam:.0f}:  A v = lambda v ？", bool(np.allclose(A @ v, lam * v)))

# 特征多项式 det(A - lambda I) = lambda^2 - 5 lambda + 6，它的根就是特征值
print("特征多项式系数：", np.poly(A), " 根：", np.roots(np.poly(A)))
print("迹 =", np.trace(A), "= 特征值之和", vals.sum(), "；行列式 =", round(float(np.linalg.det(A)), 3), "= 特征值之积", vals.prod())

# 对比：一般向量经过 A 之后，方向通常会变；特征向量不会
def angle(a, b):
    return np.degrees(np.arccos(a @ b / (np.linalg.norm(a) * np.linalg.norm(b))))
for x in [vecs[:, 0], vecs[:, 1], np.array([0.0, 1.0]), np.array([1.0, 1.0])]:
    print("x =", np.round(x, 2), " 与 A x 的夹角 =", round(float(angle(x, A @ x)), 1), "度")

# 没有实特征向量的情形：逆时针旋转 90 度
R = np.array([[0.0, -1.0], [1.0, 0.0]])
print("旋转 90 度的特征值：", np.linalg.eigvals(R))
''')

C_DIAG = code('''
import numpy as np

A = np.array([[3.0, 1.0], [0.0, 2.0]])
vals, P = np.linalg.eig(A)                    # A = P D P^-1
D = np.diag(vals)
print("A = P D P^-1 ？", bool(np.allclose(A, P @ D @ np.linalg.inv(P))))

# 算幂：A^10 = P D^10 P^-1，只需把对角线上的数各自求 10 次方
A10 = P @ np.diag(vals ** 10) @ np.linalg.inv(P)
print("A^10 =")
print(np.round(A10, 1))
print("和连乘 10 次一致：", bool(np.allclose(A10, np.linalg.matrix_power(A, 10))))

# 一个有名的例子：斐波那契。[[1,1],[1,0]]^n 的左下角就是第 n 个斐波那契数
F = np.array([[1.0, 1.0], [1.0, 0.0]])
lam, Q = np.linalg.eig(F)
print("特征值：", np.round(lam, 6), "（最大的是黄金分割比 1.618…）")
F30 = Q @ np.diag(lam ** 30) @ np.linalg.inv(Q)
print("F(30) =", int(round(F30[1, 0])))
print("F(31)/F(30) =", round(float(np.linalg.matrix_power(F, 31)[1, 0] / np.linalg.matrix_power(F, 30)[1, 0]), 6))

# 幂迭代：反复乘 A 再归一化，方向会收敛到「绝对值最大的特征值」的特征向量
x = np.array([1.0, 5.0])
for step in range(1, 31):
    x = A @ x
    x /= np.linalg.norm(x)
    if step in (1, 5, 30):
        print(f"第 {step:2d} 步：x =", np.round(x, 4), " Rayleigh 商 x^T A x =", round(float(x @ A @ x), 4))
''')

C_SYM = code('''
import numpy as np
rng = np.random.default_rng(0)

# 生成二维相关数据：两个特征同升同降
cov_true = np.array([[3.0, 1.5], [1.5, 1.0]])
X = rng.multivariate_normal([0, 0], cov_true, size=2000)
C = np.cov(X.T)                                # 样本协方差矩阵：对称矩阵
print("协方差矩阵：")
print(np.round(C, 2))

vals, V = np.linalg.eigh(C)                    # eigh 专门用于对称矩阵：特征值从小到大，特征向量互相正交
vals, V = vals[::-1], V[:, ::-1]               # 改成从大到小
print("特征值：", np.round(vals, 3))
print("V^T V = I（特征向量互相正交）：", bool(np.allclose(V.T @ V, np.eye(2))))

# 沿第一个特征向量投影，得到的一维数据的方差就是最大特征值（这就是 PCA 的第一主成分）
for i in range(2):
    proj = X @ V[:, i]
    print(f"沿特征向量 {i + 1} 的方差 = {proj.var(ddof=1):.3f}  （特征值 {vals[i]:.3f}）")
print("第一主成分解释的方差比例：", round(float(vals[0] / vals.sum()), 3))

# 任意其他方向的方差都介于两个特征值之间
angles = np.linspace(0, np.pi, 181)
var_by_angle = [(X @ np.array([np.cos(t), np.sin(t)])).var(ddof=1) for t in angles]
print("所有方向里方差的最大值 =", round(float(max(var_by_angle)), 3), " 最小值 =", round(float(min(var_by_angle)), 3))
''')

C_SVD = code('''
import numpy as np
rng = np.random.default_rng(1)

# 一个 5x3 的矩阵：不是方阵，没有特征分解，但有 SVD
A = rng.normal(size=(5, 3))
U, S, Vt = np.linalg.svd(A, full_matrices=False)   # 精简版 SVD
print("形状 U, S, Vt：", U.shape, S.shape, Vt.shape)
print("奇异值（从大到小）：", np.round(S, 3))
print("重建 A = U diag(S) Vt ？", bool(np.allclose(U @ np.diag(S) @ Vt, A)))
print("U 的列正交、Vt 的行正交：", bool(np.allclose(U.T @ U, np.eye(3))), bool(np.allclose(Vt @ Vt.T, np.eye(3))))

# 与特征值的联系：A^T A 的特征值 = 奇异值的平方
eig = np.sort(np.linalg.eigvalsh(A.T @ A))[::-1]
print("A^T A 的特征值：", np.round(eig, 3))
print("奇异值的平方  ：", np.round(S ** 2, 3))

# 秩 = 非零奇异值的个数：造一个秩为 2 的 5x3 矩阵
B = rng.normal(size=(5, 2)) @ rng.normal(size=(2, 3))
print("B 的奇异值：", np.round(np.linalg.svd(B, compute_uv=False), 6), " 秩 =", np.linalg.matrix_rank(B))

# 几何：单位圆经过 M 变成椭圆，半轴长就是奇异值
M = np.array([[3.0, 1.0], [0.0, 2.0]])
t = np.linspace(0, 2 * np.pi, 3601)
circle = np.stack([np.cos(t), np.sin(t)])           # 单位圆上的点（每列一个）
lengths = np.linalg.norm(M @ circle, axis=0)        # 变换后各点到原点的距离
print("椭圆最长半轴 =", round(float(lengths.max()), 3), " 最短半轴 =", round(float(lengths.min()), 3))
print("M 的奇异值   =", np.round(np.linalg.svd(M, compute_uv=False), 3))
print("奇异值之积 =", round(float(np.prod(np.linalg.svd(M, compute_uv=False))), 3), "= |det M| =", abs(round(float(np.linalg.det(M)), 3)))
''')

C_LOWRANK = code('''
import numpy as np
rng = np.random.default_rng(0)

# 造一个「本质上秩为 3」的 100x80 权重矩阵，再加一点噪声
m, n, r = 100, 80, 3
W = rng.normal(size=(m, r)) @ np.diag([30.0, 20.0, 10.0]) @ rng.normal(size=(r, n)) / 10 + 0.05 * rng.normal(size=(m, n))
U, S, Vt = np.linalg.svd(W, full_matrices=False)
print("前 6 个奇异值：", np.round(S[:6], 2))
print("第 4 个以后的最大奇异值：", round(float(S[3]), 3))

def rank_k(k):
    return U[:, :k] @ np.diag(S[:k]) @ Vt[:k]            # 只保留最大的 k 个奇异值

total = np.linalg.norm(W)                               # Frobenius 范数
for k in [1, 2, 3, 5, 10]:
    err = np.linalg.norm(W - rank_k(k))
    theory = np.sqrt((S[k:] ** 2).sum())               # 被丢掉的奇异值的平方和再开方
    print(f"k = {k:2d}  相对误差 = {err / total:.4f}  公式 = {theory / total:.4f}")

# Eckart-Young：随机选一个 3 维列空间做投影，一定比 SVD 的秩 3 近似差
Q, _ = np.linalg.qr(rng.normal(size=(m, 3)))
print("随机 3 维投影的相对误差 =", round(float(np.linalg.norm(W - Q @ Q.T @ W) / total), 4))

# 省了多少参数
print("秩 3 分解的参数数：", 3 * (m + n + 1), "，原矩阵：", m * n)
print("768x3072 的矩阵，秩 8：", 8 * (768 + 3072), "对", 768 * 3072, "，约为", round(768 * 3072 / (8 * (768 + 3072))), "分之一")
''')
