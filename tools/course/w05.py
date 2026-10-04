"""wm-0 第 5 节：潜变量模型与 VAE（v3 格式，2026-10-04）"""
from unitlib import *
from w05c import C_MIX, C_INTRACT, C_ELBO, C_GAP, C_REPARAM, C_KLG, C_VAE
from w05_quiz import QUIZ

unit = {
 "id": "u05",
 "title": "潜变量模型与 VAE",
 "en": "Latent Variable Models & VAE",
 "minutes": 120,
 "objectives": [
  "理解 **潜变量模型 (latent variable model)** 的生成过程 $p(x,z)=p(z)p(x\\mid z)$，说清 **边缘似然 (marginal likelihood)** $p(x)$ 与 **后验 (posterior)** $p(z\\mid x)$ 各是什么、为什么难算",
  "能用 Jensen 不等式和 KL 分解两种方式推导 **证据下界 (ELBO)**，并知道 $\\log p(x)=\\text{ELBO}+D_{KL}(q\\,\\|\\,p(z\\mid x))$ 这条恒等式的含义",
  "理解 **重参数化技巧 (reparameterization trick)** 解决的是什么问题，知道它和上一节的评分函数估计（REINFORCE）是同一个梯度的两种估计，以及为什么前者方差小得多",
  "能写出 **VAE** 的编码器、解码器和损失，读懂 **重构项 (reconstruction)** 与 **KL 项** 的拉扯，知道 **后验坍缩 (posterior collapse)** 是什么",
  "说得出 VAE 在世界模型里的角色：把高维观测压成低维的潜状态",
 ],
 "blocks": [
  T(r"""
### 先说这一节要干什么

世界模型要做的第一件事，是把「看到的东西」变成「模型能处理的东西」。一帧游戏画面有成千上万个像素，但真正决定接下来会发生什么的，也许只是几个量：小球在哪、有多快、挡板在哪。这几个量你没法直接观测，它们是**潜变量 (latent variable)**。**潜变量模型**就是一整套「假设数据背后有一些看不见的原因，然后从数据里把这些原因学出来」的方法。VAE（变分自编码器）是其中最重要的一个，它是深度学习版的潜变量模型，也是 Ha 和 Schmidhuber 的《World Models》、Dreamer 等一系列工作里观测编码器的基础。

**这一节和世界模型的关系：** 在 World Models 里，视觉模型 V 是一个 VAE：每一帧图像被压成一个小的潜向量 $z$，之后的记忆模型 M 在潜空间里预测下一个 $z$，控制器 C 根据 $z$ 做决策。在这一节里你会把这个 V 从头推出来：为什么需要一个「下界」，下界怎么来，怎么训练。「把观测压成潜状态，再在潜状态里做预测和规划」这个思路，后面第 6 节（状态空间模型）、第 7 节（基于模型的强化学习）和第 8 节（Dreamer、JEPA）都会反复出现。

**学完它你就能看懂这几件事：**

- 论文里 $\mathcal L(\theta,\phi;x)=\mathbb E_{q_\phi(z\mid x)}[\log p_\theta(x\mid z)]-D_{KL}(q_\phi(z\mid x)\,\|\,p(z))$ 这一行每个符号是什么、怎么来的；
- PyTorch VAE 代码里 `mu + torch.exp(0.5 * logvar) * torch.randn_like(mu)` 这一行为什么这么写，以及为什么损失里有一个「KL」；
- 训练日志里「KL 掉到 0」是什么意思，为什么有人会说模型「没有用到潜变量」；
- 为什么用 MSE 训练的 VAE 本质上是在假设解码器输出一个固定方差的高斯。

**本节安排（约 120 分钟）**：潜变量模型（12 分钟）→ 边缘似然为什么难算（10 分钟）→ ELBO 的推导（20 分钟）→ 视频一（15 分钟）→ 重参数化技巧（12 分钟）→ 视频二（18 分钟）→ VAE：编码器、解码器与训练（20 分钟）→ 与世界模型的关系（5 分钟）→「想一想」（8 分钟）。视频是英文的，可以打开 YouTube 的中文字幕；NumPy 的代码直接运行，PyTorch 的部分需要先 `pip install torch`。这一节会用到：ARENA 概率一节的贝叶斯公式和高斯分布、微积分一节的链式法则和梯度、信息论一节的 KL 散度，以及 PyTorch 一节的训练循环。

### 潜变量模型：看不见的原因

> **标准定义 · 潜变量模型 (latent variable model)**
>
> 观测 $x$ 的分布由一个**生成过程**定义：先从**先验 (prior)** $p(z)$ 里抽出看不见的潜变量 $z$，再根据它抽出观测，$x\sim p_\theta(x\mid z)$（$\theta$ 是参数）。联合分布与边缘分布分别是
>
> $$p_\theta(x,z)=p(z)\,p_\theta(x\mid z),\qquad p_\theta(x)=\int p_\theta(x,z)\,dz$$
>
> $p_\theta(x)$ 叫**边缘似然**（或**证据 (evidence)**），训练就是最大化它的对数 $\log p_\theta(x)$。已知 $x$ 时，对 $z$ 的「反推」是**后验** $p_\theta(z\mid x)$。$z$ 是离散变量时积分换成求和。
>
> *English: A latent variable model generates data by first sampling a hidden z from a prior p(z) and then sampling x from p(x|z). Its marginal likelihood p(x) = ∫ p(x,z) dz is the training objective, and the posterior p(z|x) is the inference of the hidden cause given an observation.*

**白话版：「先掷一个看不见的骰子，再据此作画」。** 你看到的 $x$ 是画，潜变量 $z$ 是画家脑子里的「构思」：先有构思（$z$），再有画（$x$）。给定一幅画，猜它的构思是什么，就是后验推断。

最小的例子是**混合高斯**：潜变量 $z\in\{0,1\}$ 是「这个点来自哪一团」，每一团内部是一个高斯。因为 $z$ 只有两个取值，所有的量都能精确算出来，可以作为后面所有概念的小模型：

""" + C_MIX + r"""

读输出：三个点上 $p(x)$ 分别是 0.27957、0.03217、0.07979。后验 $p(z\mid x)$ 用贝叶斯公式 $p(z\mid x)=p(x\mid z)p(z)/p(x)$ 算：$x=-2$ 恰好是第 0 团的中心，几乎肯定来自第 0 团（0.9989）；$x=3$ 是第 1 团的中心，后验几乎全部在第 1 团（四位小数下显示 $[0,1]$）；$x=0.5$ 夹在两团中间，后验是 $(0.3815,0.6185)$，**拿不准**，这就是「推断带不确定性」。后两行验证了生成过程：按「先抽 $z$ 再抽 $x$」生成 20 万个点，落进 5 个区间的经验频率 $(0.1112,0.4789,0.1374,0.1228,0.1497)$ 和从 $p(x)$ 积分得到的模型概率 $(0.1111,0.479,0.1363,0.1236,0.15)$ 相差在 0.002 以内。

### 为什么边缘似然难算

混合高斯里 $p(x)$ 只是两项之和。深度生成模型里，$z$ 是连续的、几十到几百维，$p_\theta(x\mid z)$ 是一个神经网络，$p_\theta(x)=\int p(z)\,p_\theta(x\mid z)\,dz$ 既没有闭式解，也没法数值积分。有两个难点互相纠缠：

- **边缘似然 $p_\theta(x)$ 算不出来**，就没法直接最大化它；
- **后验 $p_\theta(z\mid x)=p_\theta(x\mid z)p(z)/p_\theta(x)$ 的分母正好就是 $p_\theta(x)$**，所以后验也算不出来。

一个自然的想法是蒙特卡洛：从先验抽很多 $z^{(s)}\sim p(z)$，用 $p_\theta(x)=\mathbb E_{z\sim p(z)}[p_\theta(x\mid z)]\approx\frac1S\sum_sp_\theta(x\mid z^{(s)})$。这个估计无偏，但在高维下会失效。下面的实验选了一个有精确答案的线性高斯模型，来检验这个做法有多可靠：

""" + C_INTRACT + r"""

读输出：每一行是一个观测维度 $d$（潜变量固定是 8 维），对同一个 $x$ 重复做 20 次、每次用 2 万个先验样本的估计。$d=8$ 时精确值是 $-14.124$，估计的均值是 $-16.008$，标准差 2.940；$d=16$ 时精确值是 $-24.519$，估计均值掉到 $-74.711$，标准差 20.122；$d=32$ 和 $d=64$ 时偏差更大（均值 $-383.257$、$-786.562$ 对应的精确值是 $-38.390$、$-42.141$）。最后一列是**有效样本数**：2 万个样本里，真正有贡献的只有 1~1.4 个。原因是：观测维度越高，$p(x\mid z)$ 越尖，只有极小的一块 $z$ 能给出像样的概率，先验样本几乎打不到那块区域。（取对数时均值偏低是因为：$p(x)$ 的估计本身无偏，但取对数后因为凹函数而偏低，而这里样本太少，偏低得很严重。）

**结论：需要一个比先验更聪明的提议分布，让采样集中在对 $x$ 有贡献的 $z$ 上。** 这就是下面的**变分推断**：引入一个可以任意设计的分布 $q(z)$，用它来近似后验，并把对 $\log p(x)$ 的最大化换成对一个**下界**的最大化。

### ELBO：证据下界

> **标准定义 · 证据下界 (ELBO, Evidence Lower BOund)**
>
> 对任意满足「$p_\theta(z\mid x)>0$ 的地方 $q(z)>0$」的分布 $q(z)$：
>
> $$\log p_\theta(x)\ \ge\ \mathcal L(q)=\mathbb E_{z\sim q}\big[\log p_\theta(x,z)-\log q(z)\big]=\mathbb E_{q}\big[\log p_\theta(x\mid z)\big]-D_{KL}\big(q(z)\,\|\,p(z)\big)$$
>
> 并且缺口恰好是一个 KL 散度：
>
> $$\log p_\theta(x)=\mathcal L(q)+D_{KL}\big(q(z)\,\|\,p_\theta(z\mid x)\big)$$
>
> 所以当 $q$ 等于真后验时，下界是紧的。
>
> *English: For any q, the ELBO E_q[log p(x,z) − log q(z)] lower-bounds log p(x), and the gap is exactly KL(q(z) ‖ p(z|x)). It equals the log-evidence iff q is the true posterior. It can also be written as reconstruction term minus KL to the prior.*

**白话版：「用一把能量到的尺子，量一座量不到的山」。** 山高 $\log p(x)$ 量不了，但你能量到某个下界 $\mathcal L(q)$，而且它永远不超过山高。你可以通过调 $q$ 把下界抬高，抬到极限时下界就等于山高；在这个过程中，缺口 $D_{KL}(q\|\text{后验})$ 就是你的 $q$ 离真后验还有多远。

**推导一（Jensen 不等式）：**

1. 把 $\log p(x)$ 写成积分，上下同乘 $q(z)$，把积分变成对 $q$ 的期望：$\log p_\theta(x)=\log\int q(z)\frac{p_\theta(x,z)}{q(z)}dz=\log\mathbb E_{z\sim q}\Big[\frac{p_\theta(x,z)}{q(z)}\Big]$；
2. $\log$ 是凹函数，**Jensen 不等式**说「先平均再取对数 ≥ 先取对数再平均」：$\log\mathbb E[w]\ge\mathbb E[\log w]$；
3. 所以 $\log p_\theta(x)\ge\mathbb E_{z\sim q}\Big[\log\frac{p_\theta(x,z)}{q(z)}\Big]=\mathcal L(q)$。

**推导二（KL 分解）：** 对任意 $z$，$\log p(x)=\log\frac{p(x,z)}{p(z\mid x)}$（贝叶斯公式）。两边对 $q(z)$ 取期望，左边与 $z$ 无关，不变：

$$\log p_\theta(x)=\mathbb E_q\Big[\log\frac{p_\theta(x,z)}{q(z)}\Big]+\mathbb E_q\Big[\log\frac{q(z)}{p_\theta(z\mid x)}\Big]=\mathcal L(q)+D_{KL}\big(q(z)\,\|\,p_\theta(z\mid x)\big)$$

KL 非负，所以 $\mathcal L(q)\le\log p(x)$，推导二把推导一里「丢掉了多少」说得清清楚楚。

**换个写法：** $\log p(x,z)=\log p(x\mid z)+\log p(z)$，代进 $\mathcal L(q)$，得到 $\mathcal L(q)=\mathbb E_q[\log p(x\mid z)]-D_{KL}(q(z)\|p(z))$：**重构项**（用 $z$ 能多好地还原 $x$）减去**KL 项**（$q$ 偏离先验多远）。这是 VAE 损失的原型。

下面用一个**有精确答案**的线性高斯模型（$z\sim\mathcal N(0,I_2)$，$x\mid z\sim\mathcal N(Wz,\sigma^2I_5)$）把这些公式全部对拍。这个模型里 $\log p(x)$、真后验、以及高斯 $q$ 的 ELBO 都有闭式解：

""" + C_ELBO + r"""

读输出：

- 精确的 $\log p(x)=-7.449565$。令 $q$ 等于真后验，ELBO 也是 $-7.449565$，差只有 $8.9\times10^{-16}$（浮点误差），其中重构项是 $-5.913$，KL 项是 1.5366，**下界是紧的**；
- 对 1000 个随机的 $q$，ELBO 全部不超过 $\log p(x)$（`True`），而且缺口和 $D_{KL}(q\|\text{后验})$ 最多相差 $4.5\times10^{-13}$，**推导二的恒等式成立**；
- 同一个 $q$ 的三种算法：闭式「重构 − KL」得 $-8.595$，蒙特卡洛 $\mathbb E_q[\log p(x,z)-\log q(z)]$ 得 $-8.5961\pm0.0053$，$\log p(x)-D_{KL}(q\|\text{后验})$ 也是 $-8.595$，三者一致。

再看 Jensen 的缺口，以及一个重要的限制：如果 $q$ 只能取**各维独立（对角）**的高斯，而真后验的两个维度是相关的，缺口还能降到 0 吗？

""" + C_GAP + r"""

读输出：

- 取一个故意偏离后验的 $q$。**先平均再取对数** $\log\mathbb E_q[w]=-7.3968$，接近精确的 $\log p(x)=-7.4496$（差 0.05 来自采样误差）；**先取对数再平均** $\mathbb E_q[\log w]$ 就是 ELBO，$=-13.2784$。两者的差 5.8289，和 $D_{KL}(q\|\text{后验})=5.8303$ 一致（也差在采样误差内）。这直观地说明：**Jensen 不等式丢掉的，恰好是 $q$ 与后验的距离**；
- 真后验的协方差 $\begin{pmatrix}0.1384&-0.0943\\-0.0943&0.1503\end{pmatrix}$，两个维度的相关系数约为 $-0.65$；
- 对角高斯里最优的 $q$（均值取后验均值，方差取后验精度矩阵对角元的倒数），ELBO 是 $-7.728816$，缺口是 0.279251，和预测的 $D_{KL}(q\|\text{后验})=0.279251$ 相同。在这个点附近随机扰动 2000 次，**没有一次**能让 ELBO 更高。也就是说 **$q$ 的函数族不够灵活时，下界永远有缺口**，缺口大小由族与真后验的差距决定。VAE 里的编码器用的正是对角高斯，这是它的已知局限。
"""),
  V("9zKuYvjFFS8", "视频一：Variational Autoencoders（Arxiv Insights）", 15),
  T(r"""
### 重参数化技巧

ELBO 里有一个期望 $\mathbb E_{z\sim q_\phi(z\mid x)}[\,\cdot\,]$，$q_\phi$ 由编码器的参数 $\phi$ 决定。训练要对 $\phi$ 求梯度，困难在于：**采样 $z\sim q_\phi$ 这个操作本身不可导**，反向传播走到这里就断了。有两种办法。

> **标准定义 · 重参数化技巧 (reparameterization trick)**
>
> 把 $z$ 写成参数和一个**与参数无关**的噪声的确定性函数。对高斯：
>
> $$z=\mu_\phi(x)+\sigma_\phi(x)\odot\varepsilon,\qquad\varepsilon\sim\mathcal N(0,I)$$
>
> 于是 $\mathbb E_{z\sim q_\phi}[f(z)]=\mathbb E_{\varepsilon\sim\mathcal N(0,I)}\big[f(\mu_\phi+\sigma_\phi\odot\varepsilon)\big]$，期望里的分布不再依赖 $\phi$，梯度可以直接穿过 $z$：
>
> $$\nabla_\phi\,\mathbb E_{z\sim q_\phi}[f(z)]=\mathbb E_{\varepsilon}\big[\nabla_\phi f(\mu_\phi+\sigma_\phi\odot\varepsilon)\big]$$
>
> *English: Express the sample as a deterministic, differentiable function of the parameters and an independent noise variable ε. The distribution being averaged over no longer depends on the parameters, so gradients can be backpropagated through the sample.*

**白话版：「把掷骰子这一步外包」。** 原来是「编码器决定一个分布，然后掷骰子」，骰子在编码器后面，梯度过不去。现在改成「先在外面掷好一个标准骰子 $\varepsilon$，再让编码器决定怎么平移和缩放它」：骰子的随机性已经固定了，$\mu$ 和 $\sigma$ 只是普通的可导函数，梯度就能走通。

**另一种办法是上一节的评分函数估计**：$\nabla_\phi\mathbb E_{q_\phi}[f(z)]=\mathbb E_{q_\phi}[f(z)\,\nabla_\phi\log q_\phi(z)]$，这和策略梯度是**同一个**公式（$q_\phi$ 是策略，$f$ 是回报）。它只要求能采样、能算 $\log q_\phi$，不要求 $f$ 可导，所以可用于离散变量和不可导的奖励；但方差大。重参数化要求 $f$ 可导、$z$ 能写成这种形式，一旦满足，方差小得多。下面用 $f(z)=z^2$ 实验（此时 $\mathbb E[f]=\mu^2+\sigma^2$，精确梯度 $(2\mu,2\sigma)$ 已知）：

""" + C_REPARAM + r"""

读输出：取 $\mu=1,\sigma=0.5$，精确梯度是 $\partial_\mu=2.0$、$\partial_\sigma=1.0$。20000 次实验、每次 10 个样本，**两种估计的均值都等于精确值**（2.0035、2.0001；1.0081、1.0027），都是无偏的。差别在标准差：对 $\mu$，评分函数估计是 1.4672，重参数化是 0.3154，**小约 4.7 倍**；对 $\sigma$，评分函数是 2.9506，重参数化是 0.7679，**小约 3.8 倍**。要得到同样的精度，评分函数估计大约需要多 15~20 倍的样本（方差比约 22 和 15），这就是 VAE 能用单个样本 $\varepsilon$ 就稳定训练的原因。
"""),
  V("vy8q-WnHa9A", "视频二：The Reparameterization Trick（ML & DL Explained）", 18),
  T(r"""
### VAE：把推断也交给神经网络

到现在，ELBO 对每个数据点都要优化一个 $q(z)$，几百万个数据点就要几百万个 $q$，不现实。VAE 的两个关键设计：

1. **摊销推断 (amortized inference)**：用**一个**神经网络（**编码器 / 推断网络**）根据 $x$ 直接输出 $q_\phi(z\mid x)=\mathcal N\big(\mu_\phi(x),\text{diag}\,\sigma_\phi^2(x)\big)$，所有数据点共用这个网络；
2. 用神经网络（**解码器 / 生成网络**）参数化 $p_\theta(x\mid z)$，两者**联合**训练，最大化整个数据集上的 ELBO。

> **标准定义 · 变分自编码器 (Variational Autoencoder, VAE)**
>
> 先验取 $p(z)=\mathcal N(0,I)$，编码器 $q_\phi(z\mid x)=\mathcal N(\mu_\phi(x),\text{diag}\,\sigma_\phi^2(x))$，解码器 $p_\theta(x\mid z)$（连续数据常取固定方差的高斯，二值数据取伯努利）。对每个数据点的损失是负 ELBO，用重参数化的**单个样本** $z$ 估计第一项：
>
> $$-\mathcal L(\theta,\phi;x)=\underbrace{-\log p_\theta(x\mid z)}_{\text{重构项}}+\underbrace{D_{KL}\big(q_\phi(z\mid x)\,\|\,\mathcal N(0,I)\big)}_{\text{KL 项}},\qquad z=\mu_\phi+\sigma_\phi\odot\varepsilon$$
>
> 第二项对对角高斯有闭式解：$D_{KL}=\tfrac12\sum_j\big(\mu_j^2+\sigma_j^2-1-\ln\sigma_j^2\big)$。
>
> *English: A VAE trains an encoder q_φ(z|x) and a decoder p_θ(x|z) jointly by maximizing the ELBO, using the reparameterization trick for the expectation and a closed-form Gaussian KL term (Kingma & Welling, 2013).*

**白话版：「一个压缩器加一个解压器，但压缩结果必须像从标准正态里抽出来的」。** 普通自编码器只要求「还原得好」，压缩出的 $z$ 可以散落在空间里任何地方，空隙处解码出来是乱码，没法从中采样生成新数据。VAE 加了 KL 项，要求所有数据的 $z$ 都聚在标准正态附近，这样从 $\mathcal N(0,I)$ 里随便抽一个 $z$ 去解码，得到的也是像样的数据。

闭式 KL 先和蒙特卡洛对拍一下：

""" + C_KLG + r"""

读输出：$q=\mathcal N(0.8,0.6^2)$ 对 $\mathcal N(0,1)$，闭式 $\tfrac12(0.64+0.36-1-2\ln0.6)=0.5108$，200 万个样本的蒙特卡洛是 0.5114，吻合。当 $\mu=0,\sigma=1$（编码器完全没把信息放进 $z$）时 KL 恰好是 0。

**两项的拉扯。** 重构项想让 $z$ 尽可能携带 $x$ 的信息（方差小、均值随 $x$ 变化）；KL 项想让 $z$ 靠近先验（方差接近 1、均值接近 0），也就是**不携带信息**。每一个潜变量维度，都要「值得」花这笔 KL 开销才会被用上。如果解码器是方差固定为 $\sigma_x^2$ 的高斯，重构项是 $\|x-\hat x\|^2/(2\sigma_x^2)$ 加一个常数：**$\sigma_x^2$ 越大，重构项的权重越小，KL 项相对越重**。用 MSE 训练的 VAE，其实隐含地选定了 $\sigma_x^2$；把 KL 项乘一个系数 $\beta$ 的做法叫 β-VAE，本质上是在调同一个旋钮。

下面是一个完整的 PyTorch 实验。数据是合成的：真实的潜变量只有 **2 维**，经过固定的非线性映射变成 8 维观测再加噪声；VAE 的潜变量故意给 **4 维**，看看它用不用得上。分别用解码器噪声 $\sigma_x=0.1$（接近真实噪声）和 $\sigma_x=1.0$（很嘈杂）各训练一次：

""" + C_VAE + r"""

读输出：数字都是**每个样本**的平均（单位：奈特），在验证集上算。

- **$\sigma_x=0.1$**：ELBO 从第 1 轮的 $-135.688$ 升到第 10 轮的 $-5.383$，第 50 轮 0.830，第 100 轮 1.775，第 300 轮 2.581。重构项从 $-134.158$ 升到 8.121，KL 在 1.530 到 7.436 之间变化，最终 5.540（先升后降：先学会用潜变量，再把没用的信息收回去）。**每个维度的 KL 是 $(0.001,0.002,2.652,2.885)$**：两个维度几乎为 0，**被模型关掉了**，剩下 2 个维度各付出 2.652 和 2.885 奈特，恰好和数据真实的 2 个自由度对上（这是这一次实验的结果，不是定理）；
- **$\sigma_x=1.0$**：重构项不再值得花代价，ELBO 一直在 $-9.4$ 附近，第 300 轮是 $-9.369$，重构项 $-8.301$，KL 只有 1.068，每个维度的 KL 是 $(0.000,0.364,0.000,0.704)$，两个维度完全关闭，剩下的两个也只携带很少的信息。

**后验坍缩 (posterior collapse)** 指的就是这种现象的极端形式：对所有的 $x$，$q_\phi(z\mid x)\approx p(z)$，KL 接近 0，解码器**不依赖 $z$**，潜变量被「忽略」。一个维度坍缩，说明它不值得；所有维度都坍缩，说明模型变成了一个不用潜变量的普通生成模型。当解码器本身很强（比如逐个 token 预测的自回归模型）、可以不靠 $z$ 就把 $x$ 建得很好时，最容易出现。常见的缓解办法是：KL 项的权重从 0 逐渐增大（KL annealing）、给每个维度保留最低的 KL 额度（free bits）、削弱解码器、减小 $\beta$。看 VAE 训练日志时，**一定要把重构项和 KL 项分开看**，只看总 ELBO 看不出潜变量到底有没有被用上。

### 与世界模型的关系

回到开头。World Models（Ha & Schmidhuber，2018）把智能体拆成三块：**V**（Vision）是一个 VAE，把每一帧压成一个小的潜向量 $z_t$；**M**（Memory）是一个 MDN-RNN，在潜空间里预测下一个 $z_{t+1}$；**C**（Controller）是很小的控制器，根据 $z_t$ 和 M 的隐状态决定动作。这套设计里，**VAE 回答的是「用什么表示观测」**，下一节的序列模型回答「怎样在这个表示上预测未来」，后面的基于模型的强化学习回答「怎样利用预测来选动作」。

你在这一节学到的东西与它的对应关系：编码器 $q_\phi(z\mid x)$ 是「感知」，把观测变成潜状态；解码器 $p_\theta(x\mid z)$ 是「想象出来的观测」，让世界模型在需要时可以把潜状态画成图像；KL 项让潜空间规整、可以从先验采样；重参数化让整条链路可以用梯度训练。后面还会看到它的局限：只靠重构训练的潜变量，会把**像素上占面积大**的信息（背景、纹理）编码得很仔细，而决策真正需要的信息（小而重要的物体）可能被忽略；因此第 8 节里会有不重构像素、只在潜空间里做预测的路线。

### 这一节你要带走的三句话

1. **潜变量模型的训练目标 $\log p_\theta(x)$ 含一个难算的积分**；ELBO $=\mathbb E_q[\log p(x,z)-\log q(z)]$ 是它的下界，缺口恰好是 $D_{KL}(q\,\|\,p(z\mid x))$；最大化 ELBO 同时在训练生成模型、也在让 $q$ 逼近真后验；
2. **重参数化 $z=\mu+\sigma\varepsilon$ 把随机性外包给 $\varepsilon$，梯度才能穿过采样**；它和策略梯度里的评分函数估计是同一个梯度的两种估计，都无偏，但重参数化的方差小得多；
3. **VAE = 编码器 + 解码器 + 负 ELBO（重构项 + KL 项）**：KL 项把后验拉向先验、限制潜变量的信息量；KL 掉到 0 意味着后验坍缩；VAE 在世界模型里负责把观测压成潜状态。
"""),
  THINK(r"一个维度的编码器输出 $q(z\mid x)=\mathcal N(\mu=1,\sigma=0.5)$，先验是 $\mathcal N(0,1)$。用闭式公式算 $D_{KL}$（保留三位小数）。如果 $\mu=0,\sigma=1$ 呢？再说说这两种情形里，哪个意味着「这个维度没有携带信息」。", r"""
$D_{KL}=\tfrac12\big(\mu^2+\sigma^2-1-\ln\sigma^2\big)=\tfrac12\big(1+0.25-1-\ln0.25\big)=\tfrac12(0.25+1.3863)\approx0.818$ 奈特。

$\mu=0,\sigma=1$：$\tfrac12(0+1-1-0)=0$。这时编码器对**所有** $x$ 都输出标准正态，后验等于先验，$z$ 与 $x$ 无关，解码器从 $z$ 里得不到任何关于 $x$ 的信息，这就是该维度「没有携带信息」（坍缩）的样子。前一种情形里 KL 为正，说明这个维度确实在传递信息：均值偏离了 0，方差也小于 1。
"""),
  THINK(r"为什么 VAE 训练的是 ELBO，而不是直接最大化 $\log p_\theta(x)$？ELBO 与 $\log p_\theta(x)$ 的缺口是什么？这个缺口会给训练带来什么后果（对生成模型 $\theta$ 的影响）？", r"""
直接最大化需要算 $\log\int p_\theta(x\mid z)p(z)dz$，这个积分没有闭式解，朴素的蒙特卡洛在高维下几乎无法使用（上面的有效样本数实验）。ELBO 只需要从 $q$ 里采样、算联合密度和 $q$ 的密度，全部可算。

缺口是 $D_{KL}(q_\phi(z\mid x)\,\|\,p_\theta(z\mid x))\ge0$。后果有两层：一是训练同时在做两件事，更新 $\phi$ 让缺口变小（$q$ 更接近后验），更新 $\theta$ 让 $\log p_\theta(x)$ 变大；二是**$q$ 的函数族（比如对角高斯）不够灵活时，缺口降不到 0**（见上面的对角高斯实验），此时 ELBO 最优的 $\theta$ 不一定是 $\log p_\theta(x)$ 最优的 $\theta$，模型会被「推向」那些后验恰好容易被 $q$ 近似的方向，生成模型会因此有一点偏。
"""),
  THINK(r"**联系世界模型：** 一个只用重构损失训练的 VAE，去编码一个有大片变化背景的游戏画面，而游戏里决定胜负的是一个很小的球。这个 VAE 的潜变量可能出什么问题？说一个可以缓解的思路。", r"""
重构损失按像素平均，背景占的像素多，对损失的贡献大；球只占几个像素，即使完全画错，损失增加也很小。于是潜变量的有限容量（KL 的预算）会优先花在背景的细节上，对球的位置可能编码得很粗，甚至忽略，而球恰恰是决策需要的信息。

缓解思路：①调高与任务相关部分的权重（比如对小物体加权重构）；②让潜变量同时被用来预测奖励、动作等与决策有关的量，使得对决策重要的信息必须被保留（后面第 7 节基于模型的强化学习会看到这类做法）；③干脆不重构像素，只要求潜空间里的预测与下一步的潜状态一致（后面第 8 节的 JEPA 一类路线）。
"""),
  KW(("潜变量","latent variable $z$","看不见的、被假设为产生观测的原因"),
     ("先验","prior $p(z)$","生成过程里潜变量的分布，VAE 里取标准正态"),
     ("边缘似然 / 证据","marginal likelihood / evidence $p(x)$","$\\int p(x,z)dz$，训练要最大化它的对数，难算"),
     ("后验","posterior $p(z|x)$","给定观测对潜变量的推断，分母是边缘似然"),
     ("变分推断","variational inference","用一个可处理的 $q$ 去近似后验，把积分换成优化"),
     ("证据下界","ELBO","$\\mathbb E_q[\\log p(x,z)-\\log q(z)]$，$\\log p(x)$ 的下界"),
     ("詹森不等式","Jensen's inequality","凹函数 $\\log$：$\\log\\mathbb E[w]\\ge\\mathbb E[\\log w]$"),
     ("重构项","reconstruction term","$\\mathbb E_q[\\log p(x|z)]$，$z$ 还原 $x$ 的能力"),
     ("KL 项","KL term","$D_{KL}(q(z|x)\\|p(z))$，把后验拉向先验，限制信息量"),
     ("编码器 / 推断网络","encoder / inference network","$x\\to(\\mu,\\sigma)$，输出 $q_\\phi(z|x)$"),
     ("解码器 / 生成网络","decoder / generative network","$z\\to p_\\theta(x|z)$ 的参数"),
     ("摊销推断","amortized inference","所有数据点共用一个编码器，而不是每个点单独优化 $q$"),
     ("重参数化技巧","reparameterization trick","$z=\\mu+\\sigma\\varepsilon$，让梯度穿过采样"),
     ("后验坍缩","posterior collapse","$q(z|x)\\approx p(z)$、KL 接近 0，解码器忽略潜变量"),
     ("世界模型中的 V","V model in World Models","用 VAE 把每帧图像压成一个小的潜向量 $z$"),
  ),
 ],
 "references": [
  {"title": "Kingma & Welling《An Introduction to Variational Autoencoders》（Foundations and Trends in Machine Learning 12(4)，2019；arXiv:1906.02691）", "url": "https://arxiv.org/abs/1906.02691", "note": "本节依据的主要来源：VAE 的作者自己写的综述，含 ELBO、重参数化、摊销推断（讲解为自写，未转载原文）"},
  {"title": "Kingma & Welling《Auto-Encoding Variational Bayes》（arXiv:1312.6114，2013）", "url": "https://arxiv.org/abs/1312.6114", "note": "VAE 的原始论文，短，选读"},
  {"title": "Doersch《Tutorial on Variational Autoencoders》（arXiv:1606.05908，2016）", "url": "https://arxiv.org/abs/1606.05908", "note": "面向初学者的图解教程，适合对照本节的直觉部分"},
  {"title": "Stanford CS236 讲义：Variational autoencoders", "url": "https://deepgenerativemodels.github.io/notes/vae/", "note": "潜变量模型、ELBO（Jensen 推导）、重参数化的课程笔记，可对照推导"},
  {"title": "Ha & Schmidhuber《World Models》（arXiv:1803.10122，2018）", "url": "https://arxiv.org/abs/1803.10122", "note": "V（VAE）、M（MDN-RNN）、C（控制器）三个组件，本节「与世界模型的关系」的出处"},
 ],
 "quiz": {"questions": QUIZ},
}

TARGET = [2, 0, 3, 1, 0, 2, 1, 3, 2, 0]
for q, t in zip(unit["quiz"]["questions"], TARGET):
    q["options"][q["answer"]], q["options"][t] = q["options"][t], q["options"][q["answer"]]
    q["answer"] = t

if __name__ == '__main__':
    dump(unit, "wm-0", "u05-vae.json")
