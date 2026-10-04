"""ARENA 0.0 第 7 节：概率与统计（按 v3 格式重写，2026-10-04）"""
from unitlib import *
from a07c import C_RULES, C_EXPECT, C_VAR, C_INDEP, C_NORMAL, C_INIT
from a07_quiz import QUIZ

unit = {
 "id": "u07",
 "title": "概率与统计：期望、方差、正态分布",
 "en": "Probability & Statistics",
 "minutes": 115,
 "objectives": [
  r"掌握概率的基本规则：**条件概率 (conditional probability)**、**独立 (independence)**、**全概率公式**与**贝叶斯公式 (Bayes' rule)**，会用穷举和模拟验证",
  r"理解 **随机变量 (random variable)** 与 **期望 (expected value)**，会用期望的 **线性性 (linearity)**（不需要独立），知道 $\mathbb{E}[g(X)]\neq g(\mathbb{E}[X])$",
  r"理解 **方差 (variance)**、**标准差 (standard deviation)**，掌握 $\operatorname{Var}(aX+c)=a^2\operatorname{Var}(X)$，并说清为什么样本方差要除以 $n-1$（**贝塞尔校正 (Bessel's correction)**）",
  r"掌握独立与相关时的方差加法 $\operatorname{Var}(X+Y)=\operatorname{Var}(X)+\operatorname{Var}(Y)+2\operatorname{Cov}(X,Y)$，以及平均值的方差 $\sigma^2/n$",
  r"认识 **正态分布 (normal distribution)**、**标准化 (standardization)**、**中心极限定理 (central limit theorem)**，并能用「方差相加」推出为什么权重初始化的方差要取 $1/n$（Xavier / Kaiming）",
 ],
 "blocks": [
  T(r"""
### 先说这一节要干什么

ARENA 对概率的要求是：**必须**理解概率的基本规则、期望和标准差，**最好**理解独立性和正态分布。深度学习里到处是概率：语言模型的输出就是**下一个词的概率分布**；权重用**随机分布**初始化；LayerNorm 把激活值调整成均值 0、方差 1；训练用随机抽取的小批量，梯度本身就是个随机变量。对准备做数据和 AI 的人来说，这一节还是统计推断、A/B 测试、贝叶斯方法的共同起点。

这一节每个概念都有三件事：**严格的定义**，**用穷举或大量模拟验证它**，**它在深度学习里的用处**。最后用一个小实验，把方差的加法法则用到一个真实问题上：为什么神经网络的权重不能随便初始化。

**学完它你就能看懂这几件事：**

- 为什么权重初始化要用 $\mathcal{N}(0,1/n)$ 之类带 $1/n$ 的方差（Xavier / Kaiming 初始化），初始化错了，10 层网络的信号会消失或爆炸；
- 注意力公式里为什么要除以 $\sqrt{d_k}$；
- `torch.var` 和 LayerNorm 里的方差为什么不一样（除以 $n-1$ 还是 $n$）；
- 小批量越大梯度噪声越小，但 4 倍的批量只让噪声减半；
- 为什么「99% 准确的检测，阳性结果却只有 16% 可信」，这是评估分类器时的**基础比率谬误 (base rate fallacy)**。

**本节安排（约 115 分钟）**：导读与概率的基本规则（15 分钟）→ 视频一（14 分钟）→ 期望（10 分钟）→ 视频二（14 分钟）→ 方差与贝塞尔校正（12 分钟）→ 独立、协方差与方差的加法（12 分钟）→ 视频三（5 分钟）→ 正态分布与中心极限定理（10 分钟）→ 权重初始化小实验（10 分钟）→「想一想」。视频是英文的，可以打开 YouTube 的中文字幕。

### 概率的基本规则

> **标准定义 · 条件概率、独立、贝叶斯公式 (conditional probability, independence, Bayes' rule)**
>
> 事件 $A$ 的概率 $P(A)\in[0,1]$；互斥事件的概率可以相加，所有可能结果的概率之和为 1。在 $B$ 已发生的条件下 $A$ 的**条件概率**是 $P(A\mid B)=\dfrac{P(A\cap B)}{P(B)}$。若 $P(A\cap B)=P(A)P(B)$（等价于 $P(A\mid B)=P(A)$），则称 $A$、$B$ **独立 (independent)**：知道 $B$ 发生，不改变对 $A$ 的判断。**全概率公式**：$P(B)=P(B\mid A)P(A)+P(B\mid A^c)P(A^c)$。**贝叶斯公式**：$P(A\mid B)=\dfrac{P(B\mid A)P(A)}{P(B)}$。
>
> *English: P(A|B) = P(A∩B)/P(B). Events are independent if P(A∩B) = P(A)P(B). Bayes' rule reverses the conditioning: P(A|B) = P(B|A)P(A)/P(B), with P(B) from the law of total probability.*

**白话版：「缩小范围再数一数」。** 条件概率就是「已知 $B$ 发生了，把世界缩小到 $B$ 里，再数 $A$ 占多少」。独立，就是缩小范围前后占比没变。贝叶斯公式则是「把『已知原因算结果』的概率，反过来变成『已知结果猜原因』」，这正是机器学习里「根据数据推断模型」的基本思路。

""" + C_RULES + r"""

读输出：用两个骰子的 36 种等可能结果穷举。点数和为 7 的概率是 1/6；**「第一个骰子是 3」与「点数和是 7」是独立的**（$P(A\cap B)=1/36=\tfrac16\cdot\tfrac16$，条件概率 $P(A\mid B)=1/6$，没有变）；但「点数和是 8」就**不独立**：$P(A\cap B)=1/36$，而 $P(A)P(B)=5/216$，知道和是 8 后，第一个骰子是 3 的概率从 1/6 升到 1/5。**贝叶斯**：患病率 1%、检测对病人 95% 阳性、对健康人 5% 误报，则阳性的总概率是 0.059，而阳性者里真正患病的只有 0.161（模拟 100 万人得到 0.1612，吻合）。原因是健康人数量太多，5% 的误报盖过了真阳性。**测一个罕见的事件，即使检测很准，阳性结果的可信度也可能很低**。评估罕见类别的分类器时，必须同时看精确率和召回率，而不能只看准确率。
"""),
  V("KLs_7b7SKi4", "视频一：Expected Values, Main Ideas（StatQuest）", 14),
  T(r"""
### 随机变量与期望

> **标准定义 · 随机变量与期望 (random variable & expected value)**
>
> **随机变量 (random variable)** $X$ 是把随机试验的结果映射成数的函数（如骰子的点数）。离散随机变量的**期望 (expected value)** 是按概率加权的平均：$\mathbb{E}[X]=\sum_x x\,P(X=x)$；对函数 $g(X)$，$\mathbb{E}[g(X)]=\sum_x g(x)P(X=x)$。**期望的线性性 (linearity)**：对任意随机变量（**不要求独立**）和常数，$\mathbb{E}[aX+bY+c]=a\,\mathbb{E}[X]+b\,\mathbb{E}[Y]+c$。
>
> *English: The expected value E[X] = Σ x·P(X=x) is the probability-weighted average. It is linear, E[aX+bY+c] = aE[X]+bE[Y]+c, with no independence needed. In general E[g(X)] ≠ g(E[X]).*

**白话版：「长期平均下来会是多少」。** 期望不是「最可能出现的值」，也不一定是能取到的值（骰子的期望是 3.5）。它是把一个随机过程重复很多很多次后，平均值会稳定到的位置，这个事实叫**大数定律 (law of large numbers)**。

""" + C_EXPECT + r"""

读输出：公平骰子 $\mathbb{E}[X]=7/2=3.5$。掷的次数越多，平均值越接近 3.5：10 次是 2.8000，100 次是 3.6200，10000 次是 3.5045，一百万次是 3.5022（再多一些会更近，但每次都有随机波动）。**线性性不需要独立**：令 $Y=7-X$（$Y$ 完全由 $X$ 决定，极度相关），公式值 $3\times3.5-3.5+1=8.0$，模拟值 8.009，吻合。最后一行提醒：$\mathbb{E}[X^2]=91/6\approx15.1667$，而 $(\mathbb{E}[X])^2=12.25$，**函数的期望不等于期望的函数**，两者的差正是下面的方差。
"""),
  V("SzZ6GpcfoQY", "视频二：Calculating the Mean, Variance and Standard Deviation（StatQuest）", 14),
  T(r"""
### 方差与标准差

> **标准定义 · 方差与标准差 (variance & standard deviation)**
>
> 记 $\mu=\mathbb{E}[X]$，**方差 (variance)** $\operatorname{Var}(X)=\mathbb{E}\big[(X-\mu)^2\big]=\mathbb{E}[X^2]-\mu^2$ 衡量取值偏离均值的平方的平均；**标准差 (standard deviation)** $\sigma=\sqrt{\operatorname{Var}(X)}$，单位与 $X$ 相同。缩放与平移：$\operatorname{Var}(aX+c)=a^2\operatorname{Var}(X)$。对 $n$ 个样本，**样本方差**用 $\dfrac{1}{n-1}\sum_i(x_i-\bar{x})^2$ 来估计总体方差（**贝塞尔校正 (Bessel's correction)**），除以 $n-1$ 才是**无偏 (unbiased)** 的。
>
> *English: Var(X) = E[(X−μ)²] = E[X²] − μ²; the standard deviation is its square root. Var(aX+c) = a²Var(X). The sample variance divides by n−1 (Bessel's correction) so that it is an unbiased estimator of the population variance.*

**白话版：「离均值平均有多远（平方后）」。** 平移整组数据，不会改变它们的分散程度；放大 $a$ 倍，分散程度（标准差）放大 $|a|$ 倍，方差放大 $a^2$ 倍。**为什么样本方差要除以 $n-1$？** 因为样本均值 $\bar{x}$ 是从这同一批数据算出来的，已经「贴着」这批数据，所以数据离 $\bar{x}$ 的距离比离真实均值的距离平均要小一些，除以 $n$ 会系统性地**低估**方差；少除一个 1，恰好补回来。

""" + C_VAR + r"""

读输出：骰子的 $\operatorname{Var}(X)=35/12=2.9167$，标准差 1.7078，和模拟值（2.917）一致。缩放：$\operatorname{Var}(3X+7)$ 模拟得 26.257，公式 $9\operatorname{Var}(X)=26.25$，平移的 7 没有任何影响。**贝塞尔校正实验**：从方差为 4 的正态分布里反复抽 5 个样本，除以 $n$ 的估计平均只有 3.196（正好约是 $4\times\frac45=3.2$，系统性偏低），除以 $n-1$ 的平均是 3.995，几乎恰好是真实值 4。**工程提醒**：NumPy 的 `np.var` 默认除以 $n$，PyTorch 的 `torch.var` 默认除以 $n-1$，而 LayerNorm 内部用的是除以 $n$（有偏）的方差；ARENA 的练习里会遇到，对 `torch.var` 要传 `unbiased=False`（或 `correction=0`）才能和 LayerNorm 对上。这一点这里没有运行（VM 里没有 PyTorch），请在做 ARENA 练习时核对。

### 独立、协方差与方差的加法

> **标准定义 · 协方差与方差的加法 (covariance & variance of a sum)**
>
> **协方差 (covariance)** $\operatorname{Cov}(X,Y)=\mathbb{E}[(X-\mu_X)(Y-\mu_Y)]$；**相关系数 (correlation)** $\rho=\operatorname{Cov}(X,Y)/(\sigma_X\sigma_Y)\in[-1,1]$。**独立**的变量协方差为 0（反过来不一定成立）。对任意 $X,Y$：
>
> $$\operatorname{Var}(X+Y)=\operatorname{Var}(X)+\operatorname{Var}(Y)+2\operatorname{Cov}(X,Y)$$
>
> 独立时最后一项为 0。对 $n$ 个独立同分布、方差为 $\sigma^2$ 的变量，**平均值**的方差是 $\sigma^2/n$。
>
> *English: Var(X+Y) = Var(X) + Var(Y) + 2Cov(X,Y). For independent variables the covariance term vanishes. The mean of n i.i.d. variables with variance σ² has variance σ²/n.*

**白话版：「同向的波动会叠加，反向的会抵消」。** 两个独立的东西各自晃，合起来晃得更大一点（方差相加）；如果它们总是同时往一个方向晃（正相关），合起来晃得更厉害；如果一个上去另一个下来（负相关），就互相抵消。

""" + C_INDEP + r"""

读输出：令 $X,Y$ 都是方差 1 的正态变量，相关系数为 $\rho$。独立（$\rho=0$）时 $\operatorname{Var}(X+Y)=2$（模拟 1.999）；正相关 $\rho=0.8$ 时变大到 3.6（模拟 3.598）；负相关 $\rho=-0.8$ 时缩到 0.4（模拟 0.400）。极端情况：$\rho=1$ 时 $Y=X$，$X+Y=2X$，方差是 $4\sigma^2=4$（模拟 3.996）；$\rho=-1$ 时 $X+Y$ 恒等于 0，方差为 0。**减法也不例外**：$\operatorname{Var}(X-Y)=\operatorname{Var}(X)+\operatorname{Var}(Y)-2\operatorname{Cov}(X,Y)$，独立时同样是 2.000，**方差永远不会因为「减」而相减**。**平均值**的标准差按 $1/\sqrt{n}$ 缩小：$n=4$ 时 0.501、$n=16$ 时 0.251、$n=64$ 时 0.125。这就是为什么**小批量越大，梯度估计越准，但收益递减**：批量扩大 4 倍，噪声只减半。
"""),
  V("rzFX5NWojp0", "视频三：The Normal Distribution, Clearly Explained（StatQuest）", 5),
  T(r"""
### 正态分布、标准化与中心极限定理

> **标准定义 · 正态分布与中心极限定理 (normal distribution & central limit theorem)**
>
> **正态分布 (normal / Gaussian distribution)** $X\sim\mathcal{N}(\mu,\sigma^2)$ 的概率密度是 $f(x)=\dfrac{1}{\sigma\sqrt{2\pi}}e^{-(x-\mu)^2/(2\sigma^2)}$，由均值 $\mu$ 和**方差** $\sigma^2$ 完全决定（注意第二个参数是方差，不是标准差）。约 68% / 95% / 99.7% 的值落在 $\mu\pm\sigma$ / $\pm2\sigma$ / $\pm3\sigma$ 内。**标准化 (standardization)** $Z=(X-\mu)/\sigma$ 把它变成标准正态 $\mathcal{N}(0,1)$。独立正态变量之和仍是正态：$\mathcal{N}(\mu_1,\sigma_1^2)+\mathcal{N}(\mu_2,\sigma_2^2)=\mathcal{N}(\mu_1+\mu_2,\sigma_1^2+\sigma_2^2)$。**中心极限定理 (central limit theorem)**：很多独立同分布、方差有限的随机变量之和（或平均），经过标准化后趋近正态分布，不管原来的分布长什么样。
>
> *English: X ~ N(μ, σ²) is fully determined by its mean and variance; about 68/95/99.7% of the mass lies within 1/2/3 standard deviations. Sums of independent normals are normal, and by the central limit theorem standardized sums of many i.i.d. variables approach a normal distribution.*

**白话版：「很多小随机叠在一起，就是钟形」。** 身高、测量误差、一堆随机权重的加权和，都是「很多小因素叠加」的结果，所以长得像钟形曲线。**标准化**就是换成「以标准差为单位、以均值为原点」的尺子，LayerNorm 对每个样本的特征做的就是这件事。

""" + C_NORMAL + r"""

读输出：标准正态里，$|Z|<1$ 占 0.6823，$|Z|<2$ 占 0.9544，$|Z|<3$ 占 0.9973，和 68–95–99.7 法则吻合。标准化：$\mathcal{N}(5,3^2)$ 的数据，处理前均值 4.999、标准差 2.996，处理后均值 0.000、标准差 1.000。**中心极限定理实验**：$n=1$ 个均匀分布的数本身根本不是钟形，落在 $\pm1\sigma$ 内的比例是 0.577、$\pm2\sigma$ 内是 1.000（均匀分布有「硬边界」）；加起来 $n=2$ 是 0.651 / 0.967，$n=3$ 是 0.668 / 0.959，$n=30$ 时是 0.681 / 0.955，已经几乎和正态分布的 0.683 / 0.954 无法区分。

### 一个小实验：为什么初始化的方差要取 $1/n$

把上面的方差法则用到真实问题上。一个神经元的预激活是 $z=\sum_{i=1}^n w_ix_i$。设 $w_i$、$x_i$ 独立、均值为 0，$x_i$ 方差为 1，则每一项 $w_ix_i$ 的均值为 0、方差为 $\operatorname{Var}(w_i)\cdot1$，$n$ 项独立相加，**方差相加**：$\operatorname{Var}(z)=n\operatorname{Var}(w)$。要让 $z$ 的方差保持在 1，就需要 $\operatorname{Var}(w)=1/n$。

""" + C_INIT + r"""

读输出：$n=768$ 时，权重方差取 1，$z$ 的方差 766.81，标准差 27.69，每个神经元的输出比输入大了近 28 倍；权重方差取 $1/n$，方差 1.00，标准差 1.00，完全稳定。第二个实验是 10 层、宽度 512 的 ReLU 网络，看每层输出的均方根（RMS），权重方差取 $c/n$：**$c=1$**（方差 $1/n$）时，因为 ReLU 把一半的值截成 0，信号逐层衰减：第 1、5、10 层分别是 0.705、0.168、0.0293；**$c=2$**（Kaiming 初始化，恰好补回被 ReLU 截掉的那一半）最稳定：0.999、0.928、0.754（10 层后有一些漂移，因为这是随机的，但量级没变）；**$c=4$** 开始爆炸：1.41、5.15、33.6；**方差取 1（$c=n$）**直接冲到 $10^{12}$：15.9、$1.03\times10^6$、$1.06\times10^{12}$。**一个看似无关紧要的「方差取多少」，决定了 10 层网络能不能训练。** 同样的计算也解释了注意力里的 $\sqrt{d_k}$：若查询和键的分量独立、方差为 1，$\mathbf{q}\cdot\mathbf{k}$ 有 $d_k$ 项相加，方差是 $d_k$，所以要除以 $\sqrt{d_k}$ 把方差拉回 1，否则 softmax 会饱和。
"""),
  T(r"""
### 这一节你要带走的三句话

1. **期望是线性的（不需要独立），方差不是**：$\operatorname{Var}(aX+c)=a^2\operatorname{Var}(X)$，$\operatorname{Var}(X+Y)=\operatorname{Var}(X)+\operatorname{Var}(Y)+2\operatorname{Cov}(X,Y)$；独立时协方差为 0，$n$ 个独立变量的平均值的方差是 $\sigma^2/n$。
2. **正态分布由均值和方差决定**；独立正态变量之和仍是正态（均值相加、方差相加）；中心极限定理解释了它为什么无处不在；标准化就是减均值、除以标准差。
3. **方差的加法法则能直接推出初始化**：$n$ 项独立相加，方差变成 $n$ 倍，所以权重方差要取 $1/n$（ReLU 网络取 $2/n$）；样本方差除以 $n-1$ 是无偏的，LayerNorm 里用的是除以 $n$。
"""),
  THINK(r"$X_1\sim\mathcal{N}(1,4)$ 和 $X_2\sim\mathcal{N}(2,9)$，相关系数 $\rho=0.5$。求 $X_1+X_2$ 的期望和方差。如果它们独立呢？如果 $\rho=-1$ 呢？（ARENA 的思考题）", r"""
期望不依赖相关性：$\mathbb{E}[X_1+X_2]=1+2=3$。方差：$\sigma_1=2$，$\sigma_2=3$，$\operatorname{Cov}=\rho\sigma_1\sigma_2=0.5\times2\times3=3$，所以 $\operatorname{Var}=4+9+2\times3=19$。

独立：协方差为 0，方差是 $4+9=13$（而且和仍是正态，$\mathcal{N}(3,13)$）。$\rho=-1$：$\operatorname{Cov}=-6$，方差是 $4+9-12=1$，标准差为 $|\sigma_1-\sigma_2|=1$：两者完全反向时，波动大部分抵消，只剩标准差之差。**相关时，和不一定还是正态的**，除非它们是**联合**正态（这里默认是）。
"""),
  THINK(r"一个医院的疾病筛查对病人 99% 阳性，对健康人 2% 误报，患病率是 0.5%。(a) 一个人检测呈阳性，真的患病的概率是多少？(b) 这对「用准确率评价罕见类别分类器」有什么启示？", r"""
(a) 用贝叶斯公式：$P(\text{阳性})=0.99\times0.005+0.02\times0.995=0.00495+0.0199=0.02485$，$P(\text{病}\mid\text{阳性})=0.00495/0.02485\approx0.199$，约 **19.9%**，也就是阳性者里 5 个人中只有 1 个真的患病。

(b) 当正类很罕见时，即使误报率只有 2%，误报的人数也会远超过真正患病者的人数。一个「永远预测阴性」的模型，在这个数据上准确率 99.5%，却一点用也没有。所以要看**精确率 (precision)**、**召回率 (recall)**、PR 曲线这类指标，而不只是准确率；对应到公式里，就是「先验」（患病率）和「似然」（检测的准确性）都要考虑。
"""),
  THINK(r"你训练一个模型，用小批量估计梯度，每个样本的梯度噪声标准差是 $\sigma$，样本之间独立。(a) 批量大小 $B=32$ 时，梯度估计的噪声标准差是多少？(b) 要把噪声减半，批量要增大多少倍？(c) 注意力里为什么要把 $\mathbf{q}\cdot\mathbf{k}$ 除以 $\sqrt{d_k}$？", r"""
(a) 小批量梯度是 $B$ 个样本梯度的平均，方差是 $\sigma^2/B$，标准差是 $\sigma/\sqrt{B}=\sigma/\sqrt{32}\approx0.177\sigma$。

(b) 标准差按 $1/\sqrt{B}$ 缩小，要减半，需要 $B$ 增大 **4 倍**（例如 32 到 128）；要缩小到十分之一，需要 100 倍。所以批量越大收益越递减，这也是大批量训练常要调高学习率的原因之一。

(c) 若 $\mathbf{q}$、$\mathbf{k}$ 的各个分量独立、均值 0、方差 1，则 $\mathbf{q}\cdot\mathbf{k}=\sum_{i=1}^{d_k}q_ik_i$ 是 $d_k$ 个方差为 1 的独立项之和，方差为 $d_k$。除以 $\sqrt{d_k}$ 后方差回到 1，softmax 的输入尺度不随维度变化，避免 softmax 饱和成接近 one-hot（那样梯度几乎为 0）。
"""),
  KW(("条件概率","conditional probability","$P(A\\mid B)=P(A\\cap B)/P(B)$：已知 $B$ 发生时 $A$ 的概率"),
     ("独立","independence","$P(A\\cap B)=P(A)P(B)$，知道一个不改变另一个"),
     ("贝叶斯公式","Bayes' rule","把 $P(B\\mid A)$ 反过来变成 $P(A\\mid B)$"),
     ("随机变量","random variable","把随机结果映射成数"),
     ("期望","expected value $\\mathbb{E}[X]$","按概率加权的平均"),
     ("线性性","linearity of expectation","$\\mathbb{E}[aX+bY]=a\\mathbb{E}[X]+b\\mathbb{E}[Y]$，不需独立"),
     ("大数定律","law of large numbers","样本平均随次数增加逼近期望"),
     ("方差","variance","偏离均值的平方的期望，$\\mathbb{E}[X^2]-\\mu^2$"),
     ("标准差","standard deviation","方差的平方根，单位与数据相同"),
     ("贝塞尔校正","Bessel's correction","样本方差除以 $n-1$ 才无偏"),
     ("协方差 / 相关","covariance / correlation","两个变量一起变动的程度"),
     ("正态分布","normal / Gaussian distribution","$\\mathcal{N}(\\mu,\\sigma^2)$，钟形曲线，第二个参数是方差"),
     ("标准化","standardization","减均值、除以标准差，变成均值 0、方差 1"),
     ("中心极限定理","central limit theorem","独立变量之和（标准化后）趋近正态"),
     ("Xavier / Kaiming 初始化","Xavier / Kaiming initialization","权重方差取 $1/n$ 或 $2/n$，让信号逐层保持尺度"),
  ),
 ],
 "references": [
  {"title": "ARENA [0.0] Prerequisites — Probability & Statistics 部分", "url": "https://github.com/ARENA-education/ARENA_materials/blob/main/chapter0_fundamentals/instructions/pages/00_%5B0.0%5D_Prerequisites.md", "note": "含「正态变量之和」思考题（讲解为自写，未转载原文）"},
  {"title": "Expected Value, Variance, and Standard Deviation（Medium）", "url": "https://medium.com/jun94-devpblog/prob-stats-3-expected-value-variance-and-standard-deviation-bce9303d8da8", "note": "ARENA 推荐的入门文章"},
  {"title": "StatQuest：Population and Estimated Parameters（选看，讲 n−1）", "url": "https://www.youtube.com/watch?v=vikkiwjQqfU", "note": "为什么样本方差除以 n−1"},
  {"title": "MIT 6.041 Probabilistic Systems Analysis and Applied Probability", "url": "https://ocw.mit.edu/courses/6-041sc-probabilistic-systems-analysis-and-applied-probability-fall-2013/", "note": "选看：概率论的标准大学课程，对应本节的基本规则、期望方差与正态分布"},
 ],
 "quiz": {"questions": QUIZ},
}

if __name__ == '__main__':
    dump(unit, "arena-0.0", "u07-probability.json")
