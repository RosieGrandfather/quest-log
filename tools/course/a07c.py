"""ARENA 0.0 第 7 节的代码块（NumPy，真实运行）"""
from runlib import code

C_RULES = code('''
from fractions import Fraction
from itertools import product
import numpy as np

# 用「穷举所有等可能结果」来算两个骰子的概率：36 种结果，每种 1/36
outcomes = list(product(range(1, 7), repeat=2))
def P(event):
    return Fraction(sum(1 for o in outcomes if event(o)), len(outcomes))

print("P(点数和 = 7) =", P(lambda o: o[0] + o[1] == 7))
A = lambda o: o[0] == 3                       # 事件 A：第一个骰子是 3
for s in (7, 8):
    B = lambda o, s=s: o[0] + o[1] == s       # 事件 B：点数和 = s
    pAB = P(lambda o: A(o) and B(o))
    print(f"s={s}: P(A)={P(A)}, P(B)={P(B)}, P(A 且 B)={pAB}, P(A)P(B)={P(A) * P(B)}, 独立？{pAB == P(A) * P(B)}")
    print(f"      条件概率 P(A|B) = P(A 且 B)/P(B) = {pAB / P(B)}")

# 贝叶斯公式：某种病患病率 1%；检测对病人 95% 呈阳性，对健康人 5% 误报阳性
p_d, p_pos_d, p_pos_h = 0.01, 0.95, 0.05
p_pos = p_pos_d * p_d + p_pos_h * (1 - p_d)       # 全概率公式
posterior = p_pos_d * p_d / p_pos                 # 贝叶斯：P(病 | 阳性)
print("P(阳性) =", round(p_pos, 4), "  P(病 | 阳性) =", round(posterior, 4))

# 模拟 100 万人，数一数
rng = np.random.default_rng(0)
sick = rng.random(1_000_000) < p_d
pos = np.where(sick, rng.random(1_000_000) < p_pos_d, rng.random(1_000_000) < p_pos_h)
print("模拟：阳性者中真正患病的比例 =", round(float(sick[pos].mean()), 4))
''')

C_EXPECT = code('''
from fractions import Fraction
import numpy as np
rng = np.random.default_rng(0)

# 离散随机变量：公平骰子，每个点数概率 1/6
xs = range(1, 7)
E = sum(Fraction(x, 6) for x in xs)                    # E[X] = sum x P(X=x)
print("E[X] =", E, "=", float(E))

# 大数定律：模拟的平均值随次数增加而逼近期望
rolls = rng.integers(1, 7, size=1_000_000)
for n in (10, 100, 10_000, 1_000_000):
    print(f"掷 {n:>7d} 次，平均 = {rolls[:n].mean():.4f}")

# 期望的线性性：不需要独立。让 Y = 7 - X（完全依赖于 X）
X = rolls
Y = 7 - X
print("E[3X - Y + 1] 的公式值 =", 3 * float(E) - float(7 - E) + 1, "  模拟值 =", round(float((3 * X - Y + 1).mean()), 3))

# 注意：E[g(X)] 一般不等于 g(E[X])
print("E[X^2] =", sum(Fraction(x * x, 6) for x in xs), "=", round(float(sum(x * x for x in xs)) / 6, 4), "  但 E[X]^2 =", float(E) ** 2)
''')

C_VAR = code('''
from fractions import Fraction
import numpy as np
rng = np.random.default_rng(0)

# 公平骰子的方差：Var(X) = E[X^2] - (E[X])^2
EX = Fraction(7, 2)
EX2 = sum(Fraction(x * x, 6) for x in range(1, 7))
var = EX2 - EX ** 2
print("Var(X) =", var, "=", round(float(var), 4), "  标准差 =", round(float(var) ** 0.5, 4))

# 缩放与平移：Var(aX + c) = a^2 Var(X)
X = rng.integers(1, 7, size=1_000_000).astype(float)
print("Var(X) 模拟      :", round(float(X.var()), 3))
print("Var(3X + 7) 模拟 :", round(float((3 * X + 7).var()), 3), "  公式 9 Var(X) =", round(9 * float(var), 3))

# 总体方差 vs 样本方差：除以 n 还是除以 n-1？
# 从 N(0, 4) 里反复抽 5 个样本，估计方差，看平均估计得准不准
samples = rng.normal(0, 2, size=(200_000, 5))          # 真实方差 = 4
print("真实方差 = 4")
print("除以 n   (ddof=0) 的平均估计 =", round(float(samples.var(axis=1, ddof=0).mean()), 3))
print("除以 n-1 (ddof=1) 的平均估计 =", round(float(samples.var(axis=1, ddof=1).mean()), 3))
print("NumPy 的 np.var 默认 ddof =", 0, "，所以默认是前者")
''')

C_INDEP = code('''
import numpy as np
rng = np.random.default_rng(0)
N = 1_000_000

# 构造相关系数为 rho 的两个标准正态变量 X、Y，各自方差 1
def make(rho):
    X = rng.normal(size=N)
    Z = rng.normal(size=N)
    return X, rho * X + np.sqrt(1 - rho ** 2) * Z

print("Var(X+Y) = Var(X) + Var(Y) + 2 Cov(X,Y) = 2 + 2 rho")
for rho in (0.0, 0.8, -0.8, 1.0, -1.0):
    X, Y = make(rho)
    cov = round(float(np.cov(X, Y)[0, 1]), 2) + 0.0
    print(f"rho = {rho:+.1f}：协方差 = {cov:+.2f}，Var(X+Y) 模拟 = {(X + Y).var():.3f}，公式 = {2 + 2 * rho:.1f}，Var(X-Y) = {(X - Y).var():.3f}")

# 独立同分布变量的平均：方差 sigma^2/n，标准差 sigma/sqrt(n)
print("\\n独立变量（sigma = 1）的平均值的标准差：")
for n in (1, 4, 16, 64):
    means = rng.normal(size=(100_000, n)).mean(axis=1)
    print(f"n = {n:2d}：模拟 {means.std():.3f}，公式 1/sqrt(n) = {1 / np.sqrt(n):.3f}")
''')

C_NORMAL = code('''
import numpy as np
rng = np.random.default_rng(0)

# 68-95-99.7 法则
z = rng.normal(size=1_000_000)
for k in (1, 2, 3):
    print(f"|Z| < {k}：占 {(np.abs(z) < k).mean():.4f}")

# 标准化：减均值、除以标准差，得到均值 0、方差 1（LayerNorm 对每个样本的特征做的就是这件事，分母另加一个小常数）
x = rng.normal(loc=5.0, scale=3.0, size=100_000)
x_std = (x - x.mean()) / x.std()
print("标准化前：均值 %.3f，标准差 %.3f" % (x.mean(), x.std()))
print("标准化后：均值 %.3f，标准差 %.3f" % (x_std.mean(), x_std.std()))

# 中心极限定理：把 n 个均匀分布 U(0,1) 的数加起来，和越来越像正态分布
print("\\nn 个 U(0,1) 之和，落在均值 +- 1 / 2 个标准差内的比例（正态分布是 0.683 / 0.954）：")
for n in (1, 2, 3, 30):
    s = rng.random(size=(200_000, n)).sum(axis=1)
    mu, sd = n / 2, np.sqrt(n / 12)                    # 均匀分布均值 1/2、方差 1/12，独立相加
    print(f"n = {n:2d}：{(np.abs(s - mu) < sd).mean():.3f} / {(np.abs(s - mu) < 2 * sd).mean():.3f}")
''')

C_INIT = code('''
import numpy as np
rng = np.random.default_rng(0)

# 一个神经元的预激活 z = sum_i w_i x_i，n = 768 个输入
n = 768
x = rng.normal(size=(2000, n))                          # 输入：均值 0、方差 1
for name, w_var in [("w 方差 = 1", 1.0), ("w 方差 = 1/n", 1.0 / n)]:
    w = rng.normal(scale=np.sqrt(w_var), size=(n, 500))   # 500 个神经元
    z = x @ w
    print(f"{name:12s}：z 的方差 = {z.var():8.2f}，标准差 = {z.std():6.2f}")

# 10 层、宽度 512 的 ReLU 网络，只看每层输出的均方根（RMS）：权重方差取 c / n
width, layers = 512, 10
x0 = rng.normal(size=(200, width))
print("\\n各层输出的 RMS（第 1 / 5 / 10 层）：")
for name, c in [("c = 1   (1/n)", 1.0), ("c = 2   (Kaiming)", 2.0), ("c = 4", 4.0), ("c = n   (方差 1)", float(width))]:
    h = x0
    rms = []
    for layer in range(1, layers + 1):
        W = rng.normal(scale=np.sqrt(c / width), size=(width, width))
        h = np.maximum(0, h @ W)                       # 线性层 + ReLU
        if layer in (1, 5, 10):
            rms.append(np.sqrt((h ** 2).mean()))
    print(f"{name:18s}：" + "  ".join(f"{r:10.3g}" for r in rms))
''')
