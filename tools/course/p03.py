"""prob-0 第 3 节：常见分布：二项、泊松、正态（与 u01 同一格式）"""
from unitlib import *
from runlib import code

C_BIN = code('''
from math import comb

n, p = 10, 0.7            # 投篮 10 次，每次命中率 0.7

def binom_pmf(k):
    # 恰好命中 k 次的概率 = 「选哪 k 次命中」的方法数 × 每种方法的概率
    return comb(n, k) * p**k * (1 - p)**(n - k)

for k in range(n + 1):
    print(k, round(binom_pmf(k), 4))

print("至少命中 8 次：", round(sum(binom_pmf(k) for k in range(8, n + 1)), 4))

# 用定义直接算均值和方差，对比公式 np 和 np(1-p)
mean = sum(k * binom_pmf(k) for k in range(n + 1))
var = sum((k - mean) ** 2 * binom_pmf(k) for k in range(n + 1))
print("均值", round(mean, 4), "  n*p =", n * p)
print("方差", round(var, 4), "  n*p*(1-p) =", round(n * p * (1 - p), 4))
''')

C_POI = code('''
from math import comb, exp, factorial

# 一座大城市：1000 个路口，每个路口一天出事故的概率只有 0.003（很小）
n, p = 1000, 0.003
lam = n * p                          # λ = 平均每天的事故数 = 3

def binom(k):  return comb(n, k) * p**k * (1 - p)**(n - k)
def poisson(k): return exp(-lam) * lam**k / factorial(k)   # 泊松公式

print("k   二项     泊松")
for k in range(7):
    print(k, " ", round(binom(k), 4), " ", round(poisson(k), 4))
''')

C_NORM = code('''
from statistics import NormalDist

Z = NormalDist(0, 1)                 # 标准正态分布：均值 0，标准差 1

# 注意：连续分布里，「密度」不是概率
print("密度 f(0) =", round(Z.pdf(0), 4), "（可以不到 1，也可以超过 1，它不是概率）")

# 概率 = 曲线下方的面积 = 累积分布函数 cdf 的差
for k in (1, 2, 3):
    print(f"落在均值 ±{k} 个标准差内：", round(Z.cdf(k) - Z.cdf(-k), 4))

# 一次考试：均值 70，标准差 10。考了 85 分，换算成 z 分数，再看超过了多少人
exam = NormalDist(70, 10)
z = (85 - exam.mean) / exam.stdev
print("85 分的 z 分数：", z)
print("超过的人所占比例：", round(exam.cdf(85), 4))
''')

unit = {
 "id": "u03",
 "title": "常见分布：二项、泊松、正态",
 "en": "Common Distributions: Binomial, Poisson, Normal",
 "minutes": 70,
 "objectives": [
  "说出 **分布 (distribution)** 的含义，分清 **PMF（概率质量函数）** 和 **PDF（概率密度函数）**",
  "认识 **伯努利 (Bernoulli)** 和 **二项分布 (binomial distribution)**，会算 $P(X=k)$，记住均值 $np$、方差 $np(1-p)$",
  "认识 **泊松分布 (Poisson distribution)**：描述「单位时间内稀有事件发生的次数」，均值和方差都是 $\\lambda$",
  "认识 **正态分布 (normal distribution)**，记住 **68-95-99.7 法则**，会算 **z 分数 (z-score)**",
  "知道每种分布各自适合描述什么样的现象，并能说出它们在机器学习里的位置",
 ],
 "blocks": [
  T(r"""
### 先说这一节要干什么

上一节学的是「怎么用均值和方差概括一个随机变量」。这一节反过来：**有几种「模板」特别常见，现实里很多随机现象都能套上去**。认识这几个模板，你面对新问题时就不用从零开始建模。

**学完它你就能看懂这几件事：**

- 分类器最后一层的 softmax 输出的是一个 **类别分布 (categorical distribution)**，二分类时就是伯努利分布；
- 神经网络权重 **初始化 (initialization)** 时「从正态分布随机取值」到底在取什么；
- 回归里用 **均方误差 (MSE)**，背后是假设误差服从正态分布（下一节之后会说明）。

**本节安排（约 70 分钟）**：分布概论（5 分钟）→ 视频一（6 分钟）→ 伯努利与二项（15 分钟）→ 视频二（16 分钟）→ 泊松（10 分钟）→ 视频三（9 分钟）→ 正态（15 分钟）→ 视频四（6 分钟）→「想一想」（5 分钟）。

### 什么是分布，离散与连续

> **标准定义 · 分布 (distribution)**
>
> 随机变量的 **分布** 指它取各个值（或落在各个区间）的概率规律。对 **离散** 随机变量，用 **概率质量函数 (PMF)** $p(x)=P(X=x)$；对 **连续 (continuous)** 随机变量，用 **概率密度函数 (probability density function, PDF)** $f(x)$，概率由面积给出：
>
> $$P(a\le X\le b)=\int_a^b f(x)\,dx$$
>
> *English: A distribution describes how probability is spread over the values of a random variable. Discrete variables use a PMF; continuous variables use a PDF, where probabilities are areas under the curve.*

**白话版：** 离散的像「骰子点数」：能一个一个数，每个值有自己的概率。连续的像「身高」「等车时间」：值有无穷多种，精确等于 170.000000… 厘米的人**概率是 0**。所以连续的情况不问「恰好等于某个值的概率」，而问「落在某个区间里的概率」，这个概率等于曲线下方的**面积**。曲线的高度叫「**密度**」，它不是概率，可以大于 1。
"""),
  V("oI3hZJqXJuc", "视频一：Main Ideas behind Probability Distributions（StatQuest）", 6),
  T(r"""
### 伯努利分布与二项分布

> **标准定义 · 伯努利分布 (Bernoulli distribution)**
>
> 一次试验只有两种结果（成功 / 失败）。令 $X=1$ 表示成功，$X=0$ 表示失败，$P(X=1)=p$，则 $X$ 服从参数为 $p$ 的 **伯努利分布**，记作 $X\sim\text{Bernoulli}(p)$。它的期望 $E[X]=p$，方差 $\text{Var}(X)=p(1-p)$。
>
> *English: A Bernoulli(p) variable is 1 with probability p and 0 with probability 1 − p.*

**白话版：一次「是或否」的抛硬币。** 抛硬币、一封邮件是不是垃圾、一个病人阳性还是阴性，都是它。二分类模型输出的那个概率，就是伯努利分布的参数 $p$。

> **标准定义 · 二项分布 (binomial distribution)**
>
> 做 $n$ 次相互独立的伯努利试验，每次成功概率都是 $p$。成功的总次数 $X$ 服从 **二项分布**，记作 $X\sim\text{Binomial}(n,p)$，
>
> $$P(X=k)=\binom{n}{k}p^k(1-p)^{n-k},\quad k=0,1,\dots,n$$
>
> 其中 $\binom nk=\frac{n!}{k!(n-k)!}$ 是「从 $n$ 次里选 $k$ 次」的方法数。期望 $E[X]=np$，方差 $\text{Var}(X)=np(1-p)$。
>
> *English: The number of successes in n independent Bernoulli(p) trials follows a Binomial(n, p) distribution.*

**白话版：数「成功了几次」。** 公式其实只有两个想法。**第一**：某一种具体的结果，比如「前 3 次中、后 7 次不中」，概率是 $p^3(1-p)^7$（独立事件的概率相乘）。**第二**：成功 3 次的排列方式不止一种，一共有 $\binom{10}{3}$ 种，每种概率相同，所以乘上方法数。

均值和方差也有直观的理由：$X$ 是 $n$ 个独立伯努利变量之和，由上一节的线性性，期望是 $n\cdot p$；由独立时方差相加，方差是 $n\cdot p(1-p)$。下面用代码看一个投篮的例子，并验证公式：

""" + C_BIN + r"""

命中 7 次的概率最大（约 0.267），和均值 $np=7$ 一致。均值和方差按定义算出来，和公式 $np$、$np(1-p)$ 完全吻合。
"""),
  V("J8jNoF-K8E8", "视频二：The Binomial Distribution and Test, Clearly Explained!!!（StatQuest）", 16),
  T(r"""
### 泊松分布

> **标准定义 · 泊松分布 (Poisson distribution)**
>
> 在固定的时间（或空间）范围内，某类稀有事件平均发生 $\lambda$ 次，且各次发生彼此独立，则事件发生的次数 $X$ 服从参数为 $\lambda$ 的 **泊松分布**，记作 $X\sim\text{Poisson}(\lambda)$，
>
> $$P(X=k)=\frac{e^{-\lambda}\lambda^k}{k!},\quad k=0,1,2,\dots$$
>
> 期望与方差都等于 $\lambda$：$E[X]=\text{Var}(X)=\lambda$。
>
> *English: The Poisson(λ) distribution counts how many rare, independent events occur in a fixed interval when the average is λ; its mean and variance are both λ.*

**白话版：数「稀有事件发生了几次」。** 一小时内一家店接到的电话数，一页书里的错别字数，一天里一个路口的事故数。它们的共同点是：**可能发生的机会很多（每分钟、每个字、每辆车），但每个机会发生的概率都很小**。

泊松分布和二项分布是亲戚：如果 $n$ 很大、$p$ 很小，二项分布就非常接近泊松分布，其中 $\lambda=np$。看一个数值对比：

""" + C_POI + r"""

两列数几乎一模一样。好处是：泊松分布只需要一个参数 $\lambda$，计算更简单。**均值等于方差**是它的特征：如果你看到一组计数数据，方差远大于均值，就说明泊松分布不够用了（实际工作中叫「过度离散」 overdispersion）。
"""),
  V("jmqZG6roVqU", "视频三：An Introduction to the Poisson Distribution（jbstatistics）", 9),
  T(r"""
### 正态分布

> **标准定义 · 正态分布 (normal / Gaussian distribution)**
>
> 若连续随机变量 $X$ 的概率密度为
>
> $$f(x)=\frac{1}{\sigma\sqrt{2\pi}}\exp\!\left(-\frac{(x-\mu)^2}{2\sigma^2}\right)$$
>
> 则称 $X$ 服从均值为 $\mu$、方差为 $\sigma^2$ 的 **正态分布**，记作 $X\sim\mathcal N(\mu,\sigma^2)$。$\mu=0,\sigma=1$ 时称为 **标准正态分布 (standard normal distribution)**。
>
> *English: A normal (Gaussian) distribution is the bell-shaped distribution fully specified by its mean μ and variance σ².*

**白话版：钟形曲线。** 它以均值 $\mu$ 为中心，左右对称，离中心越远越罕见。**$\mu$ 决定钟的位置，$\sigma$ 决定钟的胖瘦。** 身高、测量误差、很多「由许多小因素叠加而成」的量，都近似服从它（下一节的中心极限定理会解释为什么）。

> **标准定义 · 68-95-99.7 法则 与 z 分数 (z-score)**
>
> 对 $X\sim\mathcal N(\mu,\sigma^2)$：落在 $\mu\pm\sigma$、$\mu\pm2\sigma$、$\mu\pm3\sigma$ 之内的概率分别约为 $68\%$、$95\%$、$99.7\%$。**z 分数** 定义为
>
> $$z=\frac{x-\mu}{\sigma}$$
>
> 它表示 $x$ 比均值高（或低）了几个标准差。若 $X\sim\mathcal N(\mu,\sigma^2)$，则 $z$ 服从标准正态分布。
>
> *English: About 68%, 95% and 99.7% of a normal distribution lies within 1, 2 and 3 standard deviations of the mean. The z-score measures how many standard deviations a value is above the mean.*

**白话版：** 这是正态分布的「口诀」：大多数值离均值不超过 2 个标准差，超过 3 个标准差的几乎不存在。z 分数把任何正态数据换算到同一把尺子（标准正态）上，这样「语文 85 分」和「数学 90 分」就可以比较了：哪门课的 z 分数高，哪门课你考得更好。这和上一节学的**标准化**完全是同一件事。

""" + C_NORM + r"""

输出里的 0.6827、0.9545、0.9973 就是口诀的精确值。这次考试 85 分，z 分数是 1.5，比 93% 左右的人高。注意第一行：标准正态在 0 处的密度约 0.3989，说明「密度」不是概率。
"""),
  V("rzFX5NWojp0", "视频四：The Normal Distribution, Clearly Explained!!!（StatQuest）", 6),
  T(r"""
### 这一节你要带走的三句话

1. **二项数「成功几次」，泊松数「稀有事件几次」，正态描述「许多小因素叠加出来的连续量」**；它们各有一个简单的公式，参数只有一两个。
2. **二项**：$E=np$、$\text{Var}=np(1-p)$；**泊松**：$E=\text{Var}=\lambda$；**正态**：由 $\mu$ 和 $\sigma$ 完全决定，$z=(x-\mu)/\sigma$。
3. **连续分布里，概率 = 面积，不是函数值**；单点的概率是 0。

在机器学习里：二分类对应伯努利、多分类对应类别分布，权重初始化与噪声建模常用正态，计数数据（点击、事件）常用泊松。
"""),
  THINK("有人说：「一个公平的硬币，抛 10 次，正面的次数一定是 5 次附近，不太可能是 8 次或 9 次。」用二项分布检查一下：10 次里恰好 5 次、恰好 8 次的概率各是多少？这句话对不对？", r"""
$P(X=5)=\binom{10}{5}/2^{10}=252/1024\approx0.246$，$P(X=8)=\binom{10}{8}/2^{10}=45/1024\approx0.044$。

所以「恰好 5 次」也只有约 25% 的把握，不到四分之一；8 次虽然少见（约 4.4%），但绝不是不可能。这句话「一定」说得过头了。标准差是 $\sqrt{10\times0.5\times0.5}\approx1.58$，8 次比均值多 3 次，约 1.9 个标准差，属于「少见但会发生」。**随机性比直觉预期的要大。**
"""),
  THINK("一个模型输出「这封邮件是垃圾邮件的概率是 0.9」。如果你有 100 封这样被模型给出 0.9 的邮件，其中垃圾邮件的数量服从什么分布？「校准良好」意味着什么？", r"""
把每封看成独立的伯努利试验，成功概率 $p=0.9$，那么 100 封里真正的垃圾邮件数服从 $\text{Binomial}(100,0.9)$，均值 90，标准差 $\sqrt{100\times0.9\times0.1}=3$。

**校准良好 (well-calibrated)** 就是：模型说 0.9 的这一类邮件里，真的垃圾的比例约为 90%，也就是在 87 到 93 之间的数（大约一个标准差内）上下波动。如果实际只有 70 封是垃圾，就说明模型「过度自信」。这是本模块后面要用到的核心想法：**把预测的概率当成伯努利参数，用数据检验。**
"""),
  THINK("某网站平均每分钟 2 次访问（泊松）。上一节我们说「均值等于方差」。如果你统计了一周，发现每分钟访问数的均值是 2，方差却是 10，说明什么？该怎么办？", r"""
说明泊松分布**不适合**这份数据：泊松要求「方差 = 均值」，现在方差是均值的 5 倍，出现了**过度离散**。常见原因是访问不是各自独立的，比如有时会因为一条热搜突然涌入一大批人（事件成团出现）。

办法：换更灵活的模型，比如**负二项分布 (negative binomial distribution)**，它有额外的参数来控制方差；或者把时间分段，每段单独建模。重点是学会这个检查：**用均值与方差的关系判断分布合不合适。**
"""),
  KW(("分布","distribution","随机变量取各个值（或区间）的概率规律"),
     ("概率质量函数","PMF","离散变量取每个值的概率"),
     ("概率密度函数","PDF","连续变量的密度；概率 = 曲线下面积，密度本身不是概率"),
     ("伯努利分布","Bernoulli distribution","一次是/否试验，$P(X=1)=p$"),
     ("二项分布","binomial distribution","$n$ 次独立伯努利试验的成功次数；均值 $np$，方差 $np(1-p)$"),
     ("组合数","binomial coefficient","$\\binom nk$：从 $n$ 个里选 $k$ 个的方法数"),
     ("泊松分布","Poisson distribution","稀有事件在固定范围内发生的次数；均值 = 方差 = $\\lambda$"),
     ("过度离散","overdispersion","方差明显大于均值，说明泊松不合适"),
     ("正态分布","normal / Gaussian distribution","钟形曲线，由 $\\mu$ 和 $\\sigma^2$ 决定"),
     ("标准正态分布","standard normal distribution","$\\mu=0$、$\\sigma=1$ 的正态分布"),
     ("z 分数","z-score","$(x-\\mu)/\\sigma$：比均值高几个标准差"),
     ("68-95-99.7 法则","68-95-99.7 rule","±1、±2、±3 个标准差内的概率约 68%、95%、99.7%"),
     ("累积分布函数","cumulative distribution function (CDF)","$F(x)=P(X\\le x)$"),
  ),
 ],
 "references": [
  {"title": "Harvard Statistics 110 Lecture 11：The Poisson distribution（大学课程原视频，约 43 分钟，选看）", "url": "https://www.youtube.com/watch?v=TD1N4hxqMzY", "note": "泊松分布的来龙去脉，以及它与二项分布的关系"},
  {"title": "Harvard Statistics 110 Lecture 13：Normal distribution（选看）", "url": "https://www.youtube.com/watch?v=72QjzHnYvL0", "note": "正态分布的严格讲法"},
  {"title": "MIT OCW 6.041 Probabilistic Systems Analysis（课程主页，含讲义与习题）", "url": "https://ocw.mit.edu/courses/6-041sc-probabilistic-systems-analysis-and-applied-probability-fall-2013/", "note": "选做其中常见分布的习题"},
 ],
 "quiz": {"questions": [
  Q("$X\\sim\\text{Bernoulli}(0.3)$，则 $E[X]$ 和 $\\text{Var}(X)$ 分别是？",
    ["0.3 和 0.3", "0.3 和 0.21", "0.5 和 0.25", "0.21 和 0.3"], 1,
    "伯努利：$E[X]=p=0.3$，$\\text{Var}(X)=p(1-p)=0.3\\times0.7=0.21$。方差不等于均值（那是泊松分布的特点）。"),
  Q("一枚公平硬币抛 4 次，恰好 2 次正面的概率是多少？",
    ["0.25", "0.5", "0.375", "0.1875"], 2,
    "$P=\\binom42/2^4=6/16=0.375$。0.25 是把「恰好 2 次」当成了 $1/4$；0.5 是以为一半对应一半。"),
  Q("$X\\sim\\text{Binomial}(100,0.2)$，则 $E[X]$ 和 $\\text{Var}(X)$ 分别是？",
    ["20 和 20", "16 和 20", "20 和 4", "20 和 16"], 3,
    "$E[X]=np=20$，$\\text{Var}(X)=np(1-p)=100\\times0.2\\times0.8=16$。「20 和 4」把标准差（4）当成了方差。"),
  Q("某客服中心平均每小时接到 4 个电话（泊松分布）。一小时内一个电话也没有的概率是？",
    ["$e^{-4}\\approx0.018$", "$4e^{-4}\\approx0.073$", "0", "0.25"], 0,
    "$P(X=0)=\\frac{e^{-4}4^0}{0!}=e^{-4}\\approx0.018$。$4e^{-4}$ 是恰好 1 个电话的概率。"),
  Q("$X\\sim\\text{Poisson}(\\lambda)$，下面哪个正确？",
    ["均值 $\\lambda$，方差 $\\lambda^2$", "均值 $\\lambda$，方差 $\\sqrt\\lambda$", "均值 $\\lambda$，方差 $\\lambda$", "均值 $\\lambda^2$，方差 $\\lambda$"], 2,
    "泊松分布的特点：均值等于方差，都是 $\\lambda$。"),
  Q("某地成年男性身高近似服从均值 170 cm、标准差 6 cm 的正态分布。约 95% 的人身高落在哪个区间？",
    ["158 到 182", "164 到 176", "152 到 188", "170 到 182"], 0,
    "95% 对应均值 ±2 个标准差：$170\\pm12$，即 158 到 182。164 到 176 是 ±1 个标准差（约 68%）。"),
  Q("考试均值 70、标准差 10。小明考了 85 分，他的 z 分数是多少？",
    ["15", "0.15", "−1.5", "1.5"], 3,
    "$z=(85-70)/10=1.5$，表示比均值高 1.5 个标准差。15 只是分数差，没有除以标准差。"),
  Q("$X$ 是连续随机变量，$P(X=3)$ 等于多少？",
    ["等于密度函数 $f(3)$ 的值", "0", "$1/3$", "无法判断"], 1,
    "连续变量取单个值的概率是 0，概率只在区间上才有（等于面积）。密度 $f(3)$ 不是概率。"),
  Q("某网站平均每分钟有 2 次访问，各次访问独立、随机地到达。一分钟内的访问次数最适合用哪种分布描述？",
    ["泊松分布", "伯努利分布", "标准正态分布", "均匀分布"], 0,
    "这是典型的「固定时间内稀有事件的次数」，用泊松分布。伯努利只描述一次是或否。"),
  Q("$X\\sim\\text{Binomial}(1000,0.003)$。下面哪个是它最合适的近似？",
    ["标准正态分布", "泊松分布，$\\lambda=3$", "伯努利分布，$p=0.003$", "泊松分布，$\\lambda=1000$"], 1,
    "$n$ 很大、$p$ 很小时，二项分布近似泊松分布，$\\lambda=np=3$。"),
 ]},
}

if __name__ == '__main__':
    dump(unit, "prob-0", "u03-distributions.json")
