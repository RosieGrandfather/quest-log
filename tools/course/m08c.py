from runlib import Notebook

nb = Notebook()

# ───── 数据划分 ─────
C_STRAT = nb.cell('''
import numpy as np

rng = np.random.default_rng(0)
y = np.r_[np.ones(30), np.zeros(970)]                 # 1000 个样本里只有 3% 是正例
counts = [y[rng.choice(1000, 100, replace=False)].sum() for _ in range(2000)]
print("随机抽 100 个当验证集，2000 次里正例个数：最少", int(min(counts)), " 最多", int(max(counts)), " 平均", np.mean(counts))
print("有", int(np.sum(np.array(counts) == 0)), "次验证集里一个正例也没有")

pos, neg = np.where(y == 1)[0], np.where(y == 0)[0]  # 分层抽样：每一类各抽 10%
val = np.r_[rng.choice(pos, 3, replace=False), rng.choice(neg, 97, replace=False)]
print("分层抽样：验证集 100 个样本里的正例个数 =", int(y[val].sum()))
''')

C_GROUP = nb.cell('''
rng = np.random.default_rng(0)
G, per = 40, 10                                        # 40 个客户，每个客户 10 条记录
centers = rng.normal(0, 3, (G, 5))                     # 每个客户在特征空间里有自己的「指纹」
Xg = np.repeat(centers, per, axis=0) + rng.normal(0, 0.3, (G * per, 5))
gid = np.repeat(np.arange(G), per)
yg = np.repeat(rng.integers(0, 2, G), per)             # 标签只由客户决定、纯随机：特征里没有任何真正的规律

def nn1(Xa, ya, Xb):                                   # 1 近邻分类：每个测试点抄最近的训练点的标签
    d = ((Xb[:, None, :] - Xa[None, :, :]) ** 2).sum(-1)
    return ya[d.argmin(1)]

perm = rng.permutation(G * per)
tr, te = perm[:300], perm[300:]                        # 随机按行划分
print("按行随机划分 测试准确率:", (nn1(Xg[tr], yg[tr], Xg[te]) == yg[te]).mean())
te = np.isin(gid, rng.permutation(G)[:10])             # 按客户划分：测试集里的客户训练时从没见过
print("按客户划分   测试准确率:", (nn1(Xg[~te], yg[~te], Xg[te]) == yg[te]).mean())
''')

C_TIME = nb.cell('''
rng = np.random.default_rng(1)
t = np.arange(300.0)
yt = 0.05 * t + 3 * np.sin(t / 20) + rng.normal(0, 0.5, 300)   # 有趋势、有周期、有噪声的时间序列

def knn_time(ttr, ytr, tte, k=5):                      # 预测 = 时间上最近的 k 个训练点的平均
    idx = np.argsort(np.abs(tte[:, None] - ttr[None, :]), axis=1)[:, :k]
    return ytr[idx].mean(1)

perm = rng.permutation(300)
tr, te = perm[:210], perm[210:]                        # 随机划分：测试点的时间邻居大多在训练集里
print("随机划分 平均绝对误差:", round(np.abs(knn_time(t[tr], yt[tr], t[te]) - yt[te]).mean(), 3))
tr, te = np.arange(210), np.arange(210, 300)           # 按时间划分：用过去预测未来
print("时间划分 平均绝对误差:", round(np.abs(knn_time(t[tr], yt[tr], t[te]) - yt[te]).mean(), 3))
print("时间划分 「总是预测训练集平均值」的误差:", round(np.abs(yt[tr].mean() - yt[te]).mean(), 3))
''')

# ───── 合成表格数据与特征工程 ─────
C_TABLE = nb.cell('''
def sigmoid(z):
    return 1 / (1 + np.exp(-z))

rng = np.random.default_rng(7)
N = 2400
day = np.sort(rng.integers(0, 300, N))                          # 订单日期，按时间排好
carrier = rng.choice(["A", "B", "C", "D"], N, p=[0.35, 0.3, 0.2, 0.15])
dist = np.exp(rng.normal(5.5, 0.8, N))                          # 运输距离（km），右偏
weight = rng.gamma(2.0, 5.0, N)                                 # 重量（kg）
miss = rng.random(N) < np.where(carrier == "D", 0.20, 0.05)     # D 承运商经常不填距离
ld = np.log(dist) - 5.5
bonus = dict(A=0.0, B=0.4, C=-0.3, D=0.4)
logit = (-2.4 + 1.8 * ld + 0.06 * (weight - 10) + np.array([bonus[c] for c in carrier])
         + (carrier == "D") * -3.4 * ld + 1.0 * miss + 0.003 * (day - 150))
y = (rng.random(N) < sigmoid(logit)).astype(float)              # 1 = 订单延迟
dist = np.where(miss, np.nan, dist)                             # 观测到的距离里有缺失值

tr, va, te = day < 180, (day >= 180) & (day < 240), day >= 240  # 按时间划分：过去训练、之后验证、最后测试
print("样本数 训练/验证/测试:", tr.sum(), va.sum(), te.sum())
print("延迟比例 训练/验证/测试:", [round(float(y[m].mean()), 3) for m in (tr, va, te)])
print("距离缺失比例:", round(float(np.isnan(dist).mean()), 3), "  按承运商:", {c: round(float(np.isnan(dist[carrier == c]).mean()), 2) for c in "ABCD"})
for i in range(3):
    print(day[i], carrier[i], dist[i].round(1), weight[i].round(1), int(y[i]))
''')

C_PREP = nb.cell('''
class Prep:
    """预处理器：只在训练集上 fit（算中位数、类别表、均值和标准差），再 transform 任何数据"""
    def fit(self, dist, weight, carrier):
        self.med = np.nanmedian(np.log(dist))                   # 缺失值用训练集的中位数填
        self.cats = [str(c) for c in sorted(set(carrier))]                        # 类别表来自训练集
        raw = self._raw(dist, weight, carrier)
        self.mu, self.sd = raw[:, :2].mean(0), raw[:, :2].std(0)
        return self

    def _raw(self, dist, weight, carrier):
        ld = np.log(dist)
        missing = np.isnan(ld)
        ld = np.where(missing, self.med, ld)                    # 填补
        onehot = (carrier[:, None] == np.array(self.cats)[None, :]).astype(float)   # 独热编码
        return np.c_[ld, weight, missing, onehot]               # 对数距离、重量、「缺失」指示列、承运商独热

    def transform(self, dist, weight, carrier):
        X = self._raw(dist, weight, carrier)
        X[:, :2] = (X[:, :2] - self.mu) / self.sd               # 只标准化两个连续列
        return X

prep = Prep().fit(dist[tr], weight[tr], carrier[tr])
Xtr, Xva, Xte = [prep.transform(dist[m], weight[m], carrier[m]) for m in (tr, va, te)]
print("特征矩阵形状:", Xtr.shape, " 类别表:", prep.cats, " 训练集填补用的中位数(对数距离):", round(prep.med, 3))
print("训练集前两列 均值", Xtr[:, :2].mean(0).round(3), " 标准差", Xtr[:, :2].std(0).round(3))
print("验证集前两列 均值", Xva[:, :2].mean(0).round(3), " 标准差", Xva[:, :2].std(0).round(3))
print("训练集缺失指示列的均值:", Xtr[:, 2].mean().round(3))
''')

C_PREPDEMO = nb.cell('''
# 线上会出现训练时没见过的类别：独热编码给出全 0，不会报错，但要知道它代表「未知」
new = prep.transform(np.array([400.0]), np.array([10.0]), np.array(["E"]))
print("没见过的承运商 E 的独热部分:", new[0, 3:])

# 泄漏：如果在全部数据上算中位数和均值，测试集的信息就偷偷进了训练过程
print("只用训练集的中位数:", round(np.nanmedian(np.log(dist[tr])), 4), " 用全部数据的中位数:", round(np.nanmedian(np.log(dist)), 4))
print("只用训练集的重量均值:", round(weight[tr].mean(), 3), " 用全部数据的重量均值:", round(weight.mean(), 3))
''')

# ───── 基线与模型 ─────
C_METRICS = nb.cell('''
def confusion(y, pred):
    tp = int(((pred == 1) & (y == 1)).sum()); fp = int(((pred == 1) & (y == 0)).sum())
    fn = int(((pred == 0) & (y == 1)).sum()); tn = int(((pred == 0) & (y == 0)).sum())
    return tp, fp, fn, tn

def scores(y, p, thr=0.5):
    tp, fp, fn, tn = confusion(y, (p >= thr).astype(int))
    prec = tp / max(tp + fp, 1); rec = tp / max(tp + fn, 1)
    return dict(acc=(tp + tn) / len(y), prec=prec, rec=rec, f1=2 * prec * rec / max(prec + rec, 1e-12))

def auc(y, s):                                          # AUC = 随机抽一个正例和一个负例，正例得分更高的概率（秩和公式）
    r = np.argsort(np.argsort(s)) + 1.0
    n1, n0 = y.sum(), len(y) - y.sum()
    return (r[y == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)

def nll(y, p):                                          # 平均对数损失（交叉熵）
    p = np.clip(p, 1e-9, 1 - 1e-9)
    return -np.mean(y * np.log(p) + (1 - y) * np.log(1 - p))

ytr, yva, yte = y[tr], y[va], y[te]
base = np.full(len(yva), ytr.mean())                    # 基线 0：永远预测训练集的平均延迟率
print("基线0 总是预测不延迟:", {k: round(v, 3) for k, v in scores(yva, base).items()}, " AUC 0.5（常数预测没有排序能力）")
rule = np.nan_to_num(Xva[:, 0], nan=0.0)                # 基线 1：只看距离，越远越可能延迟
print("基线1 只看距离排序  : AUC", round(auc(yva, rule), 3), "  阈值取 1 倍标准差:", {k: round(v, 3) for k, v in scores(yva, (rule > 1).astype(float)).items()})
''')

C_LOGREG = nb.cell('''
def fit_logreg(X, y, l2=1e-2, lr=0.5, steps=400):
    w, b = np.zeros(X.shape[1]), 0.0
    for _ in range(steps):
        p = sigmoid(X @ w + b)
        w -= lr * (X.T @ (p - y) / len(y) + l2 * w)         # 交叉熵的梯度 + L2
        b -= lr * (p - y).mean()
    return w, b

w, b = fit_logreg(Xtr, ytr)
pva = sigmoid(Xva @ w + b)
print("逻辑回归 验证集:", {k: round(v, 3) for k, v in scores(yva, pva).items()}, " AUC", round(auc(yva, pva), 3))
print("系数（对数距离, 重量, 缺失, A, B, C, D）:", w.round(2))
''')

C_MLP2 = nb.cell('''
def fit_mlp(X, y, h=32, steps=500, lr=0.1, l2=0.0, seed=0):
    rng = np.random.default_rng(seed)
    W1, b1 = rng.normal(0, np.sqrt(2 / X.shape[1]), (X.shape[1], h)), np.zeros(h)
    W2, b2 = rng.normal(0, np.sqrt(1 / h), h), 0.0
    for _ in range(steps):
        z = X @ W1 + b1; a = np.maximum(z, 0)
        d = (sigmoid(a @ W2 + b2) - y) / len(y)                   # 输出层误差 (p - y) / N
        dz = np.outer(d, W2) * (z > 0)                             # 反传到隐藏层
        W2 -= lr * (a.T @ d + l2 * W2); b2 -= lr * d.sum()
        W1 -= lr * (X.T @ dz + l2 * W1); b1 -= lr * dz.sum(0)
    return lambda Xn: sigmoid(np.maximum(Xn @ W1 + b1, 0) @ W2 + b2)

mlp = fit_mlp(Xtr, ytr)
pm = mlp(Xva)
print("MLP    验证集:", {k: round(v, 3) for k, v in scores(yva, pm).items()}, " AUC", round(auc(yva, pm), 3))
print("训练集 AUC: 逻辑回归", round(auc(ytr, sigmoid(Xtr @ w + b)), 3), " MLP", round(auc(ytr, mlp(Xtr)), 3))
''')

# ───── 误差分析 ─────
C_CONF = nb.cell('''
for thr in (0.5, 0.3):
    tp, fp, fn, tn = confusion(yva, (pva >= thr).astype(int))
    print(f"阈值 {thr}:            预测延迟  预测准时")
    print(f"      实际延迟      {tp:5d}    {fn:5d}      召回 = {tp}/{tp + fn} = {tp / (tp + fn):.3f}")
    print(f"      实际准时      {fp:5d}    {tn:5d}      精确率 = {tp}/{tp + fp} = {tp / max(tp + fp, 1):.3f}")
''')

C_SUB = nb.cell('''
cv, mv = carrier[va], np.isnan(dist[va])
print("子群体        样本数  实际延迟率  平均预测  召回@0.3   AUC    对数损失")
for name, m in [("全部", np.ones(len(yva), bool)), ("承运商 A", cv == "A"), ("承运商 B", cv == "B"), ("承运商 C", cv == "C"),
                ("承运商 D", cv == "D"), ("距离缺失", mv), ("距离未缺失", ~mv)]:
    print(f"{name:8s} {m.sum():8d}    {yva[m].mean():.3f}     {pva[m].mean():.3f}     {scores(yva[m], pva[m], 0.3)['rec']:.3f}   "
          f"{auc(yva[m], pva[m]):.3f}    {nll(yva[m], pva[m]):.3f}")
''')

C_ERR = nb.cell('''
loss_i = -(yva * np.log(pva) + (1 - yva) * np.log(1 - pva))   # 每个样本自己的损失
worst = np.argsort(-loss_i)[:30]                          # 损失最大的 30 个样本
print("损失最大的 6 个：")
print("承运商  距离km  重量kg  实际  预测概率  损失")
for i in worst[:6]:
    print(f"  {cv[i]}    {dist[va][i]:7.1f}  {weight[va][i]:6.1f}    {int(yva[i])}    {pva[i]:.3f}   {loss_i[i]:.2f}")
print("这 30 个里承运商 D 占", int((cv[worst] == "D").sum()), "个 =", round(float((cv[worst] == "D").mean()), 3), "  验证集里 D 的占比:", round(float((cv == "D").mean()), 3))
print("这 30 个里距离缺失占", int(mv[worst].sum()), "个 =", round(float(mv[worst].mean()), 3), "  验证集里缺失的占比:", round(float(mv.mean()), 3))
dv = dist[va]
for name, m in [("非 D", cv != "D"), ("D", cv == "D")]:    # 钻进子群体：延迟和准时的订单，距离有什么不同
    print(f"{name:3s} 延迟订单的距离中位数 {np.nanmedian(dv[m & (yva == 1)]):5.0f} km   准时订单的距离中位数 {np.nanmedian(dv[m & (yva == 0)]):5.0f} km")
''')

C_FIX = nb.cell('''
def add_inter(X):                                         # 针对错误加特征：承运商 D × 对数距离 的交互项
    return np.c_[X, X[:, 0] * X[:, 6]]

w2, b2 = fit_logreg(add_inter(Xtr), ytr)
p2 = sigmoid(add_inter(Xva) @ w2 + b2)
D = cv == "D"
print("                逻辑回归   加交互项")
print("全部 AUC        ", round(auc(yva, pva), 3), "     ", round(auc(yva, p2), 3))
print("全部 对数损失   ", round(nll(yva, pva), 3), "     ", round(nll(yva, p2), 3))
print("D 的 AUC        ", round(auc(yva[D], pva[D]), 3), "     ", round(auc(yva[D], p2[D]), 3))
print("D 的 对数损失   ", round(nll(yva[D], pva[D]), 3), "     ", round(nll(yva[D], p2[D]), 3))
print("非 D 的 对数损失", round(nll(yva[~D], pva[~D]), 3), "     ", round(nll(yva[~D], p2[~D]), 3))
''')

# ───── 校准 ─────
C_CALIB = nb.cell('''
def reliability(y, p, bins=5):
    edges = np.linspace(0, 1, bins + 1)
    ids = np.minimum(np.digitize(p, edges) - 1, bins - 1)
    ece = 0.0
    print("预测概率区间    样本数  平均预测  实际延迟率")
    for k in range(bins):
        m = ids == k
        if m.sum():
            print(f"[{edges[k]:.1f}, {edges[k + 1]:.1f})  {m.sum():8d}   {p[m].mean():.3f}     {y[m].mean():.3f}")
            ece += m.mean() * abs(p[m].mean() - y[m].mean())
    return ece

small = np.random.default_rng(0).permutation(np.where(tr)[0])[:200]    # 只拿 200 个训练样本，故意让模型过拟合
big = fit_mlp(prep.transform(dist[small], weight[small], carrier[small]), y[small], h=64, steps=1500, lr=0.3)
po = big(Xva)
print("过拟合的 MLP，验证集 AUC:", round(auc(yva, po), 3))
print("ECE =", round(reliability(yva, po), 3))
''')

C_TEMP = nb.cell('''
def logit_of(p):
    p = np.clip(p, 1e-6, 1 - 1e-6)
    return np.log(p / (1 - p))

half = len(yva) // 2                                    # 验证集一分为二：前半用来拟合温度 T，后半用来检验
zc, yc, zt, yt2 = logit_of(po[:half]), yva[:half], logit_of(po[half:]), yva[half:]
Ts = np.linspace(0.5, 6, 111)
T = Ts[np.argmin([nll(yc, sigmoid(zc / t)) for t in Ts])]   # 一维搜索：让 sigmoid(z / T) 的负对数似然最小
print("拟合出的温度 T =", round(T, 2))
print("后半验证集 NLL: 校准前", round(nll(yt2, sigmoid(zt)), 3), " 校准后", round(nll(yt2, sigmoid(zt / T)), 3))
print("AUC 不变（T 只是单调变换）:", round(auc(yt2, sigmoid(zt)), 3), round(auc(yt2, sigmoid(zt / T)), 3))
print("校准后 ECE =", round(reliability(yt2, sigmoid(zt / T)), 3))
''')

# ───── 实验记录与不确定性 ─────
C_LOG = nb.cell('''
import hashlib, json

def run_experiment(cfg):
    """一次实验 = 一个配置字典；返回配置 + 数据指纹 + 结果，保证能原样重跑"""
    Xa, Xb = Xtr, Xva
    if cfg["inter"]:
        Xa, Xb = add_inter(Xa), add_inter(Xb)
    w_, b_ = fit_logreg(Xa, ytr, l2=cfg["l2"], steps=cfg["steps"])
    p_ = sigmoid(Xb @ w_ + b_)
    data_id = hashlib.md5(np.ascontiguousarray(Xa).tobytes() + ytr.tobytes()).hexdigest()[:8]
    return dict(cfg=cfg, data=data_id, val_auc=round(auc(yva, p_), 4), val_loss=round(nll(yva, p_), 4))

base_cfg = dict(inter=False, l2=1e-2, steps=400)
log = [run_experiment(base_cfg)]
log.append(run_experiment({**base_cfg, "inter": True}))                 # 一次只改一件事：加交互项
log.append(run_experiment({**base_cfg, "inter": True, "l2": 1e-1}))     # 再只改一件事：加大 L2
for r in log:
    print(json.dumps(r, ensure_ascii=False))
print("原样重跑第一次实验，结果完全相同:", run_experiment(base_cfg) == log[0])
''')

C_BOOT = nb.cell('''
rng = np.random.default_rng(0)
def boot_ci(y, s, n=1000):
    vals = []
    for _ in range(n):
        i = rng.integers(0, len(y), len(y))              # 有放回地重采样验证集
        vals.append(auc(y[i], s[i]))
    return np.percentile(vals, [2.5, 97.5])

print("验证集样本数:", len(yva), " 正例数:", int(yva.sum()))
print("逻辑回归 AUC =", round(auc(yva, pva), 3), " 95% 区间", boot_ci(yva, pva).round(3))
print("加交互项 AUC =", round(auc(yva, p2), 3), " 95% 区间", boot_ci(yva, p2).round(3))
''')

C_SEEDS = nb.cell('''
aucs = []
for seed in range(5):
    f = fit_mlp(Xtr, ytr, seed=seed)                    # 同一个配置，只换初始化的随机种子
    aucs.append(auc(yva, f(Xva)))
print("MLP 5 个种子的验证 AUC:", np.round(aucs, 3), " 均值", round(np.mean(aucs), 3), " 标准差", round(np.std(aucs), 3))
''')

# ───── 端到端 ─────
C_PIPE = nb.cell('''
def run_pipeline(train_mask, eval_mask, inter=True, l2=1e-2):
    """从原始表格到评估：划分已经给定 -> fit 预处理 -> 特征 -> 训练 -> 预测"""
    pr = Prep().fit(dist[train_mask], weight[train_mask], carrier[train_mask])
    Xa = pr.transform(dist[train_mask], weight[train_mask], carrier[train_mask])
    Xb = pr.transform(dist[eval_mask], weight[eval_mask], carrier[eval_mask])
    if inter:
        Xa, Xb = add_inter(Xa), add_inter(Xb)
    w_, b_ = fit_logreg(Xa, y[train_mask], l2=l2)
    return sigmoid(Xb @ w_ + b_)

pv = run_pipeline(tr, va)                               # 第一步：在验证集上做所有决定（特征、模型、阈值）
print("验证集 AUC", round(auc(yva, pv), 3), " 召回@0.3", round(scores(yva, pv, 0.3)["rec"], 3), " 精确率@0.3", round(scores(yva, pv, 0.3)["prec"], 3))
''')

C_FINAL = nb.cell('''
pt = run_pipeline(tr | va, te)                          # 第二步：决定全部做完，训练 + 验证合并重训，测试集只看这一次
print("测试集  AUC", round(auc(yte, pt), 3), " 召回@0.3", round(scores(yte, pt, 0.3)["rec"], 3), " 精确率@0.3", round(scores(yte, pt, 0.3)["prec"], 3))
cte = carrier[te]
for c in "ABCD":
    m = cte == c
    print(f"  承运商 {c}: 样本 {m.sum():3d}  延迟率 {yte[m].mean():.3f}  AUC {auc(yte[m], pt[m]):.3f}")
base_rate = scores(yte, np.full(len(yte), ytr.mean()))
print("对照：总是预测准时的准确率", round(base_rate["acc"], 3), " 本模型@0.3 的准确率", round(scores(yte, pt, 0.3)["acc"], 3))
print("训练 + 验证的延迟率", round(y[tr | va].mean(), 3), " 测试延迟率", round(yte.mean(), 3))
''')

# ───── 接下来学什么 ─────
C_CONV = nb.cell('''
x = np.arange(1.0, 9.0)                                 # 长度 8 的输入
k = np.array([1.0, 0.0, -1.0])                          # 一个长度 3 的卷积核
n_out = len(x) - len(k) + 1
W = np.zeros((n_out, len(x)))
for i in range(n_out):
    W[i, i:i + len(k)] = k                              # 每一行都是同一个核，只是向右平移一格
print(W.astype(int))
print("矩阵乘法 W @ x 与卷积结果相同:", np.allclose(W @ x, np.correlate(x, k, mode="valid")))
print("同样形状的全连接层有", W.size, "个参数，卷积层只有", k.size, "个（共享 + 稀疏）")
''')

C_RNN = nb.cell('''
rng = np.random.default_rng(0)
Q, _ = np.linalg.qr(rng.normal(size=(16, 16)))          # 一个正交矩阵：只旋转，不改变长度
for rho in (0.9, 1.0, 1.1):
    W = rho * Q                                         # 循环权重 W，放大系数 rho
    g = np.eye(16)
    for t in range(50):
        g = W.T @ g                                     # 梯度每往前一个时间步，就乘一次 W 的转置
    print(f"rho = {rho}: 反传 50 个时间步后，梯度的大小是原来的 {np.linalg.norm(g, 2):.4g} 倍   (rho^50 = {rho ** 50:.4g})")
''')
