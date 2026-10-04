from runlib import code

# ---------------- 1. 潜变量模型：离散潜变量的混合高斯 ----------------
C_MIX = code('''
import numpy as np

# 一个最小的潜变量模型：潜变量 z 取 0 或 1（比如「这个点来自哪一团」），x 是看得见的数。
# 生成过程：先抽 z ~ p(z)，再抽 x ~ p(x|z)。
pi = np.array([0.7, 0.3]); mu = np.array([-2.0, 3.0]); sd = np.array([1.0, 1.5])
def normal_pdf(x, m, s): return np.exp(-0.5 * ((x - m) / s) ** 2) / (s * np.sqrt(2 * np.pi))
def p_x(x): return sum(pi[k] * normal_pdf(x, mu[k], sd[k]) for k in range(2))      # 边缘似然：对 z 求和

for x in (-2.0, 0.5, 3.0):
    joint = np.array([pi[k] * normal_pdf(x, mu[k], sd[k]) for k in range(2)])      # 联合 p(z, x)
    print(f"x={x:5.1f}  p(x)={p_x(x):.5f}  后验 p(z|x)={np.round(joint / joint.sum(), 4)}")   # 贝叶斯公式

# 检查「先抽 z 再抽 x」生成的数据，是否真的服从 p(x)：把数轴切成 5 段，比较经验频率和模型概率
rng = np.random.default_rng(0); n = 200000
z = rng.choice(2, size=n, p=pi); x = rng.normal(mu[z], sd[z])
edges = np.array([-np.inf, -3, -1, 1, 3, np.inf])
emp = np.histogram(x, bins=edges)[0] / n
grid = np.linspace(-12, 15, 270001); cdf = np.cumsum(p_x(grid)) * (grid[1] - grid[0])   # 数值积分得到累积分布
model = np.diff(np.r_[0, np.interp(edges[1:-1], grid, cdf), 1])
print("经验频率:", np.round(emp, 4))
print("模型概率:", np.round(model, 4))
''')

# ---------------- 2. 边缘似然为什么难算 ----------------
C_INTRACT = code('''
import numpy as np

# 连续潜变量：z ~ N(0, I_8)，x | z ~ N(W z, sigma^2 I_d)。这个模型恰好有精确答案：x ~ N(0, W W^T + sigma^2 I)，
# 所以可以拿它来检查「从先验采样来估计 p(x) = E_{z~p(z)}[p(x|z)]」这个朴素做法有多靠谱。
rng = np.random.default_rng(0)
k, sigma, S = 8, 0.3, 20000
def logmeanexp(a): m = a.max(); return m + np.log(np.mean(np.exp(a - m)))

print("  d    精确 log p(x)   20 次估计的均值   标准差   平均有效样本数")
for d in (8, 16, 32, 64):
    W = rng.normal(size=(d, k)); z0 = rng.normal(size=k); x = W @ z0 + sigma * rng.normal(size=d)
    C = W @ W.T + sigma ** 2 * np.eye(d)
    exact = -0.5 * (d * np.log(2 * np.pi) + np.linalg.slogdet(C)[1] + x @ np.linalg.solve(C, x))
    ests, esss = [], []
    for rep in range(20):
        zs = rng.normal(size=(S, k))                                    # 从先验抽 2 万个 z
        logw = -0.5 * (((x - zs @ W.T) ** 2).sum(1) / sigma ** 2 + d * np.log(2 * np.pi * sigma ** 2))   # log p(x|z)
        ests.append(logmeanexp(logw))                                   # log( 平均的 p(x|z) )
        w = np.exp(logw - logw.max()); esss.append(w.sum() ** 2 / (w ** 2).sum())    # 有效样本数：几个样本在起作用
    print(f"{d:4d}  {exact:12.3f}  {np.mean(ests):12.3f}  {np.std(ests):9.3f}  {np.mean(esss):10.1f}")
''')

# ---------------- 3. ELBO ----------------
ELBO_SETUP = '''
import numpy as np
rng = np.random.default_rng(0)

# 线性高斯模型：z ~ N(0, I_k)，x | z ~ N(W z, sigma^2 I_d)，一切都有闭式解，可以拿来对拍。
k, d, sigma = 2, 5, 0.5
W = rng.normal(size=(d, k)); z0 = rng.normal(size=k); x = W @ z0 + sigma * rng.normal(size=d)

# 精确的边缘似然：x ~ N(0, W W^T + sigma^2 I)
C = W @ W.T + sigma ** 2 * np.eye(d)
log_px = -0.5 * (d * np.log(2 * np.pi) + np.linalg.slogdet(C)[1] + x @ np.linalg.solve(C, x))
# 精确的后验：p(z | x) = N(mu_p, Sig_p)
Lam = np.eye(k) + W.T @ W / sigma ** 2; Sig_p = np.linalg.inv(Lam); mu_p = Sig_p @ W.T @ x / sigma ** 2

def elbo(m, S):
    """q(z) = N(m, S) 时的 ELBO = 重构项 - KL(q || 先验)，两项都用闭式解"""
    recon = -0.5 * d * np.log(2 * np.pi * sigma ** 2) - (np.sum((x - W @ m) ** 2) + np.trace(W.T @ W @ S)) / (2 * sigma ** 2)
    kl = 0.5 * (np.trace(S) + m @ m - k - np.linalg.slogdet(S)[1])
    return recon - kl, recon, kl

def kl_gauss(m1, S1, m2, S2):
    """两个高斯之间的 KL( N(m1,S1) || N(m2,S2) )"""
    S2i = np.linalg.inv(S2)
    return 0.5 * (np.trace(S2i @ S1) + (m2 - m1) @ S2i @ (m2 - m1) - len(m1) + np.linalg.slogdet(S2)[1] - np.linalg.slogdet(S1)[1])
'''

C_ELBO = code(ELBO_SETUP + '''
print("精确 log p(x) =", round(float(log_px), 6))

# (1) q 恰好等于真后验时，ELBO 应该正好等于 log p(x)
e, r, kl = elbo(mu_p, Sig_p)
print("q = 真后验   ELBO =", round(float(e), 6), " 重构项 =", round(float(r), 4), " KL(q||先验) =", round(float(kl), 4), " |ELBO - log p(x)| =", f"{abs(e - log_px):.1e}")

# (2) 对 1000 个随机的 q：ELBO <= log p(x)，并且缺口 = KL(q || 真后验)
worst_gap_err, ok = 0.0, True
for t in range(1000):
    m = rng.normal(size=k) * 2; A = rng.normal(size=(k, k)); S = A @ A.T + 0.1 * np.eye(k)
    gap = log_px - elbo(m, S)[0]
    ok &= bool(gap >= 0)
    worst_gap_err = max(worst_gap_err, abs(gap - kl_gauss(m, S, mu_p, Sig_p)))
print("1000 个随机 q，ELBO 都不超过 log p(x):", ok, "  缺口与 KL(q||后验) 的最大差:", f"{worst_gap_err:.1e}")

# (3) 同一个 q 的 ELBO 三种写法：闭式「重构 - KL」；蒙特卡洛 E_q[log p(x,z) - log q(z)]；log p(x) - KL(q||后验)
m = mu_p + np.array([0.3, -0.2]); S = np.diag([0.2, 0.2])
zs = m + rng.normal(size=(200000, k)) * np.sqrt(np.diag(S))
log_joint = -0.5 * (((x - zs @ W.T) ** 2).sum(1) / sigma ** 2 + d * np.log(2 * np.pi * sigma ** 2)) - 0.5 * ((zs ** 2).sum(1) + k * np.log(2 * np.pi))
log_q = -0.5 * (((zs - m) ** 2 / np.diag(S)).sum(1) + np.log(np.diag(S)).sum() + k * np.log(2 * np.pi))
lw = log_joint - log_q
print("闭式 ELBO        =", round(float(elbo(m, S)[0]), 4))
print("蒙特卡洛 ELBO    =", round(float(lw.mean()), 4), "±", round(float(lw.std() / np.sqrt(len(lw))), 4))
print("log p(x) - KL    =", round(float(log_px - kl_gauss(m, S, mu_p, Sig_p)), 4))
''')

C_GAP = code(ELBO_SETUP + '''
# (1) Jensen：log E_q[w] >= E_q[log w]，其中 w = p(x, z) / q(z)。
# 左边正是 log p(x)（q 随便取，只要覆盖后验），右边正是 ELBO，两者之差就是 KL(q || 后验)。
m = mu_p + np.array([1.0, -1.0]); S = np.diag([0.3, 0.3])
zs = m + rng.normal(size=(400000, k)) * np.sqrt(np.diag(S))
log_joint = -0.5 * (((x - zs @ W.T) ** 2).sum(1) / sigma ** 2 + d * np.log(2 * np.pi * sigma ** 2)) - 0.5 * ((zs ** 2).sum(1) + k * np.log(2 * np.pi))
log_q = -0.5 * (((zs - m) ** 2 / np.diag(S)).sum(1) + np.log(np.diag(S)).sum() + k * np.log(2 * np.pi))
lw = log_joint - log_q
log_mean_w = lw.max() + np.log(np.mean(np.exp(lw - lw.max())))
print("精确 log p(x)       =", round(float(log_px), 4))
print("log E_q[w]（对 w 先取平均再取对数）=", round(float(log_mean_w), 4))
print("E_q[log w]（先取对数再平均）= ELBO =", round(float(lw.mean()), 4), " 缺口 =", round(float(log_px - lw.mean()), 4), " KL(q||后验) =", round(float(kl_gauss(m, S, mu_p, Sig_p)), 4))

# (2) 如果 q 只能是「对角」高斯（各维独立），而真后验的两个维度相关，缺口就降不到 0。
print("真后验的协方差:\\n", np.round(Sig_p, 4))
S_best = np.diag(1 / np.diag(Lam))                # 对角高斯族里的最优方差 = 1 / 后验精度矩阵的对角元
e_best = elbo(mu_p, S_best)[0]
print("最优对角 q 的 ELBO =", round(float(e_best), 6), " 缺口 =", round(float(log_px - e_best), 6), " KL(q||后验) =", round(float(kl_gauss(mu_p, S_best, mu_p, Sig_p)), 6))
better = 0
for t in range(2000):                              # 在最优点附近随机扰动，看 ELBO 能不能更高
    mm = mu_p + 0.05 * rng.normal(size=k); ss = np.diag(np.diag(S_best) * np.exp(0.1 * rng.normal(size=k)))
    better += bool(elbo(mm, ss)[0] > e_best + 1e-12)
print("2000 次随机扰动里，ELBO 超过它的次数:", better)
''')

# ---------------- 4. 重参数化 ----------------
C_REPARAM = code('''
import numpy as np

# 要算 d/d(mu, sigma) E_{z~N(mu, sigma^2)}[f(z)]，取 f(z) = z^2。此时 E[f] = mu^2 + sigma^2，精确梯度是 (2 mu, 2 sigma)。
rng = np.random.default_rng(0)
mu, sigma = 1.0, 0.5
f = lambda z: z ** 2; fp = lambda z: 2 * z
print("精确梯度: d/dmu =", 2 * mu, "  d/dsigma =", 2 * sigma)

trials, n = 20000, 10                           # 重复 20000 次实验，每次只用 10 个样本估计梯度
eps = rng.normal(size=(trials, n)); z = mu + sigma * eps       # z = mu + sigma * eps，eps ~ N(0,1)：重参数化
# 评分函数估计（REINFORCE）：f(z) * d log q(z) / d(参数)，只需要 f 的数值，不需要 f 可导
sf_mu = (f(z) * (z - mu) / sigma ** 2).mean(1)
sf_sg = (f(z) * ((z - mu) ** 2 / sigma ** 3 - 1 / sigma)).mean(1)
# 重参数化估计：把 z 写成参数的函数，直接用链式法则：d f(z) / d mu = f'(z)，d f(z) / d sigma = f'(z) * eps
rp_mu = fp(z).mean(1); rp_sg = (fp(z) * eps).mean(1)
for name, a in [("评分函数  d/dmu   ", sf_mu), ("重参数化  d/dmu   ", rp_mu), ("评分函数  d/dsigma", sf_sg), ("重参数化  d/dsigma", rp_sg)]:
    print(f"{name} 20000 次估计的均值 {a.mean():.4f}   标准差 {a.std():.4f}")
''')

C_KLG = code('''
import numpy as np

# VAE 里 KL(q(z|x) || N(0, I)) 的闭式解：每个维度 0.5 * (mu^2 + sigma^2 - 1 - log sigma^2)。
# 用一个维度的情形，和蒙特卡洛估计 E_q[log q(z) - log p(z)] 对拍。
rng = np.random.default_rng(0)
m, s = 0.8, 0.6
kl_closed = 0.5 * (m ** 2 + s ** 2 - 1 - 2 * np.log(s))
z = m + s * rng.normal(size=2000000)
log_q = -0.5 * ((z - m) / s) ** 2 - np.log(s) - 0.5 * np.log(2 * np.pi)
log_p = -0.5 * z ** 2 - 0.5 * np.log(2 * np.pi)
print("闭式 KL     =", round(float(kl_closed), 4))
print("蒙特卡洛 KL =", round(float((log_q - log_p).mean()), 4), "（200 万个样本）")
print("特殊情形：mu=0, sigma=1 时 KL =", 0.5 * (0 + 1 - 1 - 0.0))
''')

# ---------------- 5. VAE ----------------
C_VAE = code('''
import numpy as np, torch, torch.nn as nn            # 需要先 pip install torch

# 合成数据：真实的潜变量只有 2 维，通过一个固定的非线性映射变成 8 维的观测，再加一点噪声
AB = np.random.default_rng(42); A = AB.normal(size=(2, 8)); B = AB.normal(size=(2, 8))
def make_data(n, seed):
    r = np.random.default_rng(seed); z = r.normal(size=(n, 2))
    x = np.tanh(z @ A) + 0.5 * np.sin(z @ B)
    return torch.tensor(x + 0.05 * r.normal(size=x.shape), dtype=torch.float32)
X, Xv = make_data(4000, 0), make_data(1000, 1)       # 训练集、验证集

class VAE(nn.Module):
    def __init__(s, dx=8, dz=4, h=64):                # 潜变量故意给 4 维，比真实的 2 维多
        super().__init__()
        s.enc = nn.Sequential(nn.Linear(dx, h), nn.Tanh(), nn.Linear(h, 2 * dz))   # 编码器：x -> (mu, log sigma^2)
        s.dec = nn.Sequential(nn.Linear(dz, h), nn.Tanh(), nn.Linear(h, dx))       # 解码器：z -> x 的均值
    def forward(s, x):
        mu, logvar = s.enc(x).chunk(2, dim=1)
        z = mu + torch.exp(0.5 * logvar) * torch.randn_like(mu)                    # 重参数化：z = mu + sigma * eps
        return s.dec(z), mu, logvar

def elbo_terms(model, x, sigma):
    """解码器是方差固定为 sigma^2 的高斯：log p(x|z) = -||x - x_hat||^2 / (2 sigma^2) - (d/2) log(2 pi sigma^2)"""
    xh, mu, logvar = model(x)
    recon = -(((x - xh) ** 2).sum(1) / (2 * sigma ** 2) + 0.5 * x.shape[1] * np.log(2 * np.pi * sigma ** 2))
    kl_dim = 0.5 * (mu ** 2 + logvar.exp() - 1 - logvar)       # 每个潜变量维度的闭式 KL
    return recon, kl_dim

def train(sigma, epochs=300, seed=0):
    torch.manual_seed(seed); model = VAE(); opt = torch.optim.Adam(model.parameters(), lr=2e-3)
    for ep in range(1, epochs + 1):
        perm = torch.randperm(len(X))
        for i in range(0, len(X), 200):
            recon, kl_dim = elbo_terms(model, X[perm[i:i + 200]], sigma)
            loss = -(recon - kl_dim.sum(1)).mean()                  # 最小化 -ELBO
            opt.zero_grad(); loss.backward(); opt.step()
        if ep in (1, 10, 50, 100, 300):
            with torch.no_grad():
                recon, kl_dim = elbo_terms(model, Xv, sigma)
                print(f"  sigma={sigma} 第 {ep:3d} 轮  验证集 ELBO={float((recon - kl_dim.sum(1)).mean()):8.3f}  重构项={float(recon.mean()):8.3f}  KL={float(kl_dim.sum(1).mean()):6.3f}")
    print("  每个潜变量维度的平均 KL:", np.round(kl_dim.mean(0).numpy(), 3))

for sigma in (0.1, 1.0):                                  # 解码器的噪声水平：0.1 贴近真实噪声，1.0 很嘈杂
    train(sigma)
''')
