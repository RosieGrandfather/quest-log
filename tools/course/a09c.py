from runlib import code

C_SURP = code('''
import numpy as np

# 信息量（惊讶度）I(x) = -log p(x)。以 2 为底单位是比特，以 e 为底单位是奈特
for p in [1.0, 0.5, 0.25, 1 / 8, 0.01]:
    print(f"p={p:<7.4g} 信息量 {-np.log2(p) + 0.0:6.3f} 比特 = {-np.log(p) + 0.0:6.3f} 奈特")

# 两个独立事件同时发生：概率相乘，信息量相加（因为 log 把乘法变加法）
p_coin, p_die = 1 / 2, 1 / 6
print("硬币正面 + 骰子掷出 6：", round(-np.log2(p_coin * p_die), 4), "比特")
print("分别相加             ：", round(-np.log2(p_coin) - np.log2(p_die), 4), "比特")

# 单位换算：1 奈特 = 1/ln2 比特
print("1 奈特 =", round(1 / np.log(2), 4), "比特")
''')

C_ENT = code('''
import numpy as np

def entropy(p, base=2):
    p = np.asarray(p, dtype=float)
    p = p[p > 0]                          # 约定 0 * log 0 = 0，所以概率为 0 的结果直接跳过
    return float(-(p * np.log(p)).sum() / np.log(base)) + 0.0

print("公平硬币        :", round(entropy([0.5, 0.5]), 4), "比特")
print("正面 0.99 的硬币:", round(entropy([0.99, 0.01]), 4), "比特")
print("完全确定 (1, 0) :", round(entropy([1.0, 0.0]), 4), "比特")

# n 个等可能结果：熵 = log2(n)
for n in [2, 8, 50257]:
    print(f"均匀分布 n={n:<6d} 熵 {entropy(np.ones(n) / n):.4f} 比特  log2(n)={np.log2(n):.4f}")

# 同样 4 个结果，分布越均匀，熵越大
for p in [(1, 0, 0, 0), (0.7, 0.1, 0.1, 0.1), (0.5, 0.5, 0, 0), (0.25, 0.25, 0.25, 0.25)]:
    print(p, "->", round(entropy(p), 4), "比特")

# 熵的意义：最优编码的平均长度。四个结果的概率是 1/2, 1/4, 1/8, 1/8，
# 给它们分配码字长度 1, 2, 3, 3 位（概率越大码字越短），平均长度正好等于熵
p = np.array([0.5, 0.25, 0.125, 0.125])
lengths = np.array([1, 2, 3, 3])
print("熵 =", entropy(p), " 平均码长 =", float(p @ lengths))

# 随机检验：任意分布的熵都落在 [0, log2 n] 之间，而且都不超过均匀分布
rng = np.random.default_rng(0)
ok = all(0 <= entropy(q) <= np.log2(5) + 1e-12 for q in rng.dirichlet(np.ones(5), size=1000))
print("1000 个随机分布的熵都在 [0, log2 5] 内：", ok)
''')

C_CE = code('''
import numpy as np

def entropy(p):
    p = np.asarray(p, float); p = p[p > 0]
    return float(-(p * np.log2(p)).sum()) + 0.0

def cross_entropy(p, q):
    p, q = np.asarray(p, float), np.asarray(q, float)
    m = p > 0
    return float(-(p[m] * np.log2(q[m])).sum()) + 0.0

def kl(p, q):
    p, q = np.asarray(p, float), np.asarray(q, float)
    m = p > 0
    return float((p[m] * np.log2(p[m] / q[m])).sum())

P = [0.5, 0.5]                # 真实分布：公平硬币
Q = [0.9, 0.1]                # 模型的预测：以为硬币偏向正面
print("H(P)        =", round(entropy(P), 4))
print("H(P, Q)     =", round(cross_entropy(P, Q), 4))
print("KL(P || Q)  =", round(kl(P, Q), 4))
print("H(P)+KL     =", round(entropy(P) + kl(P, Q), 4), "（等于 H(P, Q)）")

# KL 散度不对称：把 P 和 Q 换一下，数字不同
print("KL(Q || P)  =", round(kl(Q, P), 4), "  KL(P || Q) =", round(kl(P, Q), 4))

# 随机检验：对随机的 P、Q，H(P, Q) >= H(P)，KL >= 0，恒等式成立；Q = P 时 KL = 0
rng = np.random.default_rng(1)
good, ident = True, True
for _ in range(2000):
    p, q = rng.dirichlet(np.ones(6)), rng.dirichlet(np.ones(6))
    good &= cross_entropy(p, q) >= entropy(p) - 1e-12 and kl(p, q) >= -1e-12
    ident &= abs(cross_entropy(p, q) - entropy(p) - kl(p, q)) < 1e-9
print("2000 组随机分布：交叉熵 >= 熵 且 KL >= 0 ->", good, "；恒等式 ->", ident)
print("KL(P || P) =", kl(P, P))
''')

C_LM = code('''
import numpy as np

def softmax(z):
    z = z - z.max()                        # 先减最大值，避免 exp 溢出
    e = np.exp(z)
    return e / e.sum()

def cross_entropy_loss(logits, target):
    # 独热目标时，交叉熵只剩一项：-ln Q(正确的词)；用 log-sum-exp 写法，数值稳定
    z = logits - logits.max()
    return float(np.log(np.exp(z).sum()) - z[target])

V = 50257                                  # GPT-2 的词表大小
logits = np.zeros(V)                       # 全 0 的 logit = 均匀分布
print("均匀猜测的损失 :", round(cross_entropy_loss(logits, 123), 4), " ln(50257) =", round(float(np.log(V)), 4))

# 一个小例子：4 个词的词表，正确词是下标 2
logits = np.array([1.0, 0.5, 2.0, -1.0])
q = softmax(logits)
print("softmax 概率 :", np.round(q, 4), " 和 =", round(float(q.sum()), 4))
print("损失         :", round(cross_entropy_loss(logits, 2), 4), " = -ln(", round(float(q[2]), 4), ") =", round(float(-np.log(q[2])), 4))

# 概率和损失的对应关系：损失 = -ln(给正确词的概率)
for p in [1.0, 0.5, 0.25, 0.05, 0.01]:
    print(f"给正确词的概率 {p:<5} -> 损失 {-np.log(p) + 0.0:.3f}")

# 困惑度 = e^loss：相当于「在多少个等可能的词里猜」
for loss in [10.8249, 4.0, 3.0, 1.0]:
    print(f"loss {loss:<8} -> 困惑度 {np.exp(loss):.1f}")

# 朴素写法在 logit 很大时会溢出，稳定写法不会
big = np.array([1000.0, 0.0, 0.0])
with np.errstate(all="ignore"):
    naive = -np.log(np.exp(big[0]) / np.exp(big).sum())
print("朴素写法 :", naive, "  稳定写法 :", cross_entropy_loss(big, 0))
''')

C_FIT = code('''
import numpy as np

def softmax(z):
    e = np.exp(z - z.max()); return e / e.sum()

P = np.array([0.5, 0.25, 0.15, 0.10])      # 「语言」的真实分布（四个词）
H = float(-(P * np.log(P)).sum())          # 熵，自然对数（奈特）
print("H(P) =", round(H, 4), "奈特")

z = np.zeros(4)                            # 模型：只有 4 个 logit，初始为均匀分布
eta = 0.5
print("目标：把交叉熵压到 H(P)，同时 KL 压到 0")
for step in range(0, 201):
    Q = softmax(z)
    ce = float(-(P * np.log(Q)).sum())
    kl = ce - H
    if step in (0, 1, 5, 20, 50, 200):
        print(f"第 {step:3d} 步  交叉熵 {ce:.4f}  KL {kl:.5f}  Q = {np.round(Q, 3)}")
    z = z - eta * (Q - P)                  # 交叉熵对 logit 的梯度正好是 Q - P（微积分那一节的结论）

# 梯度检验：Q - P 真的是交叉熵对 logit 的梯度吗？
z0 = np.array([0.3, -0.2, 0.5, 0.1])
f = lambda z: float(-(P * np.log(softmax(z))).sum())
num = np.array([(f(z0 + 1e-6 * e) - f(z0 - 1e-6 * e)) / 2e-6 for e in np.eye(4)])
print("梯度检验：", np.allclose(num, softmax(z0) - P, atol=1e-7))
''')
