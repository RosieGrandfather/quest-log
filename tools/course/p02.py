"""prob-0 第 2 节：随机变量、期望与方差（与 u01 同一格式：先中英文标准定义，再白话版，面向高中生）"""
from unitlib import *
from runlib import code

C_PMF = code('''
from collections import Counter
from fractions import Fraction

# 两个骰子共有 6 × 6 = 36 种等可能的结果，数一数每个「点数之和」出现几次
counts = Counter(a + b for a in range(1, 7) for b in range(1, 7))

# 次数 ÷ 36，就是每个取值的概率（用分数显示，更清楚）
pmf = {s: Fraction(c, 36) for s, c in sorted(counts.items())}
for s, p in pmf.items():
    print(s, p)

# 所有概率加起来必须等于 1
print("合计", sum(pmf.values()))
''')

C_EXP = code('''
import random

# 公平骰子：每个点数的概率都是 1/6
faces = [1, 2, 3, 4, 5, 6]
E = sum(x * (1 / 6) for x in faces)       # 期望 = Σ 取值 × 概率
print("按定义算：", round(E, 4))

# 用模拟验证：掷 10 万次，看平均值
random.seed(0)                            # 固定随机种子，每次运行结果相同
rolls = [random.choice(faces) for _ in range(100_000)]
print("掷 10 万次的平均：", round(sum(rolls) / len(rolls), 3))

# 一个小游戏：花 2 元抽奖，1% 的概率中 100 元
prize, price, p_win = 100, 2, 0.01
print("每玩一次平均赚：", round(prize * p_win - price, 2), "元")
''')

C_LIN = code('''
import random
random.seed(1)

# 线性性：两个骰子之和的期望 = 各自期望之和，哪怕它们不独立也成立
# 这里让 Y 完全依赖 X（Y = 7 - X，也是一个骰子点数），看 E[X + Y]
xs = [random.randint(1, 6) for _ in range(100_000)]
ys = [7 - x for x in xs]                       # Y 完全由 X 决定，两者强相关
mean = lambda v: sum(v) / len(v)
print("E[X] =", round(mean(xs), 3), " E[Y] =", round(mean(ys), 3))
print("E[X+Y] =", round(mean([x + y for x, y in zip(xs, ys)]), 3))
''')

C_VAR = code('''
import statistics as st

# 两位射手，每人 5 枪，平均环数都是 8
A = [7, 8, 8, 8, 9]       # 射手 A：很稳
B = [4, 6, 8, 10, 12]     # 射手 B：忽高忽低

for name, s in [("A", A), ("B", B)]:
    print(name, "平均", st.mean(s),
          "方差", round(st.pvariance(s), 2),         # pvariance：除以 n 的方差
          "标准差", round(st.pstdev(s), 2))
''')

C_RULE = code('''
from fractions import Fraction

# 以骰子点数 X 为例，用精确的分数计算
faces = range(1, 7)
p = Fraction(1, 6)
E = sum(x * p for x in faces)
var = sum((x - E) ** 2 * p for x in faces)      # 方差 = E[(X − E[X])²]
print("Var(X) =", var, "≈", round(float(var), 4))

# 规则一：Var(aX + b) = a² Var(X)，加常数 b 不影响，乘 a 倍则方差乘 a²
a, b = 3, 2
vals = [a * x + b for x in faces]
Ev = sum(v * p for v in vals)
var_ab = sum((v - Ev) ** 2 * p for v in vals)
print("Var(3X+2) =", var_ab, "= 9 × Var(X) =", 9 * var)

# 规则二：两个独立骰子之和，方差相加（枚举 36 种结果验证）
sums = [x + y for x in faces for y in faces]
Es = Fraction(sum(sums), 36)
var_sum = sum((s - Es) ** 2 for s in sums) / 36
print("Var(X+Y) =", var_sum, "= 2 × Var(X) =", 2 * var)
''')

C_NM1 = code('''
import random, statistics as st
random.seed(0)

# 总体：标准正态分布，真实方差是 1。每次只抽 5 个样本，重复 10 万次
n, trials = 5, 100_000
sum_n = sum_n1 = 0
for _ in range(trials):
    s = [random.gauss(0, 1) for _ in range(n)]
    sum_n += st.pvariance(s)       # 除以 n
    sum_n1 += st.variance(s)       # 除以 n − 1
print("除以 n   的平均：", round(sum_n / trials, 3))
print("除以 n-1 的平均：", round(sum_n1 / trials, 3))
print("真实方差：1")
''')

unit = {
 "id": "u02",
 "title": "随机变量、期望与方差",
 "en": "Random Variables, Expectation & Variance",
 "minutes": 60,
 "objectives": [
  "说出 **随机变量 (random variable)** 和 **概率质量函数 (PMF)** 的定义，会列出简单随机变量的分布表",
  "会算 **期望 (expected value)**，并理解它是「长期平均」而不是「最可能的值」",
  "会用 **期望的线性性 (linearity of expectation)** 简化计算",
  "会算 **方差 (variance)** 和 **标准差 (standard deviation)**，知道 $\\text{Var}(aX+b)=a^2\\text{Var}(X)$",
  "理解 **样本方差 (sample variance)** 为什么除以 $n-1$",
 ],
 "blocks": [
  T(r"""
### 先说这一节要干什么

上一节讲的是「事件」：下雨、有病、抛出正面。但机器学习里处理的大多是**数**：一个像素的亮度、一个预测的误差、一个模型的损失 (loss)。这一节学怎么用概率描述「一个会随机变化的数」，并且用两个数把它概括出来：**平均是多少（期望）**、**波动有多大（方差）**。

**学完它你就能看懂这几件事：**

- 训练时的 **损失 (loss)** 其实是「期望」：真正想最小化的是 $E[\text{损失}]$，实际算的小批量平均只是它的估计；
- 为什么要做 **标准化 (standardization)**：减均值、除以标准差，就是把数据变成「均值 0、方差 1」；
- 为什么 **权重初始化 (weight initialization)** 要看方差：层数一深，方差一旦乘错倍数就会爆炸或消失。

**本节安排（约 60 分钟）**：导读与随机变量（8 分钟）→ 视频一（6 分钟）→ 期望（12 分钟）→ 视频二（14 分钟）→ 方差与代码（12 分钟）→ 视频三（14 分钟，选看）→「想一想」（5 分钟）。

### 随机变量与概率质量函数

> **标准定义 · 随机变量 (random variable)**
>
> 设一次随机试验的样本空间为 $\Omega$。**随机变量** $X$ 是一个函数 $X:\Omega\to\mathbb{R}$，它把试验的每一个结果映射成一个实数。若 $X$ 只取有限个或可列个值，称为 **离散随机变量 (discrete random variable)**。
>
> *English: A random variable is a function that assigns a real number to each outcome of a random experiment.*

**白话版：给每个结果贴一个数字标签。** 抛两个骰子，结果可能是「(3, 5)」，这不是一个数。但你可以规定 $X=$「两个点数之和」，于是 (3, 5) 就变成 8。你并没有改变随机性，只是**决定关心结果的哪一方面**，并把它变成数。

名字里的「变量」容易误导：它其实是个**函数**；「随机」是因为输入（试验结果）是随机的。习惯上，大写 $X$ 表示随机变量本身，小写 $x$ 表示它取到的某个具体值。

> **标准定义 · 概率质量函数 (probability mass function, PMF)**
>
> 离散随机变量 $X$ 的 **概率质量函数** 为 $p_X(x)=P(X=x)$。它满足 $p_X(x)\ge 0$，且所有取值的概率之和 $\sum_x p_X(x)=1$。
>
> *English: The PMF gives the probability that a discrete random variable takes each particular value; the probabilities sum to 1.*

**白话版：一张「取每个值的概率」的表。** 下面让电脑数一数，两个骰子点数之和的分布：

""" + C_PMF + r"""

看输出：和为 7 的概率最大（$6/36=1/6$），和为 2 或 12 的最小（$1/36$）。每个值的概率都是「有几种组合 ÷ 36」。这张表就是 $X$ 的**分布 (distribution)**，随机变量的一切性质都来自它。
"""),
  V("3v9w79NhsfI", "视频一：Random variables（Khan Academy）", 6),
  T(r"""
### 期望

> **标准定义 · 期望 (expected value / expectation)**
>
> 离散随机变量 $X$ 的 **期望** 定义为
>
> $$E[X]=\sum_x x\,P(X=x)$$
>
> *English: The expected value E[X] is the probability-weighted average of the values X can take.*

**白话版：长期平均。** 把每个可能的值，按它出现的概率加权，再加起来。它回答的是：「这件事重复无数次，平均每次得到多少？」

注意三点。**第一，期望不一定是能取到的值**：骰子的期望是 3.5，但你永远掷不出 3.5。**第二，期望不是「最可能的值」**。**第三，它是「长期」的平均**，只掷一次不保证接近它。下面用代码看，并算一个抽奖游戏：

""" + C_EXP + r"""

模拟的平均值非常接近 3.5。抽奖游戏每玩一次平均**亏 1 元**：中奖那 1% 的 100 元，只抵得上 2 元的成本里的 1 元。**偶尔赢一次，长期是亏的。** 看一个游戏值不值得玩，要看期望，不是看奖金多大。

> **标准定义 · 期望的线性性 (linearity of expectation)**
>
> 对任意随机变量 $X$、$Y$ 和常数 $a$、$b$：
>
> $$E[aX+bY]=aE[X]+bE[Y]$$
>
> 这个等式**不要求 $X$ 与 $Y$ 独立**。
>
> *English: Expectation is linear: E[aX + bY] = aE[X] + bE[Y], and this holds whether or not X and Y are independent.*

**白话版：平均可以拆开算。** 两个骰子之和的期望，就是各自的期望相加：$3.5+3.5=7$，不用把 36 种结果都列一遍。这条规则最厉害的地方是**不管两个变量有没有关系都成立**。下面故意让 $Y$ 完全由 $X$ 决定（$Y=7-X$，强相关），看看还成不成立：

""" + C_LIN + r"""

$E[X]$ 和 $E[Y]$ 都约等于 3.5，而 $X+Y$ 恒等于 7，期望正好是 $3.5+3.5=7$。**平均能拆开，但后面会看到，方差就没有这么好的性质。**
"""),
  V("KLs_7b7SKi4", "视频二：Expected Values, Main Ideas!!!（StatQuest）", 14),
  T(r"""
### 方差与标准差

只知道平均是不够的。看这个例子：两位射手，每人打 5 枪，平均环数一样，但表现显然不同。

> **标准定义 · 方差 (variance) 与标准差 (standard deviation)**
>
> 设 $\mu=E[X]$。$X$ 的 **方差** 定义为
>
> $$\text{Var}(X)=E\big[(X-\mu)^2\big]=E[X^2]-(E[X])^2$$
>
> **标准差** 为 $\sigma=\sqrt{\text{Var}(X)}$。
>
> *English: The variance is the expected squared deviation from the mean; the standard deviation is its square root.*

**白话版：数据平均离「平均值」有多远。** 做法：每个值减去平均数（得到「偏差」），平方（避免正负抵消，也让大偏差更突出），再取平均。平方之后单位也被平方了（环数变成环数²），所以再开方得到**标准差**，单位就回到和原数据相同。

""" + C_VAR + r"""

两个人平均都是 8，但射手 B 的方差（8.0）比射手 A（0.4）大得多。**期望告诉你「中心在哪」，方差告诉你「散得多开」。**

> **标准定义 · 方差的运算规则 (properties of variance)**
>
> 1. $\text{Var}(aX+b)=a^2\,\text{Var}(X)$（加常数不改变方差；乘以 $a$，方差乘以 $a^2$）。
> 2. 若 $X$、$Y$ **独立 (independent)**，则 $\text{Var}(X+Y)=\text{Var}(X)+\text{Var}(Y)$，且 $\text{Var}(X-Y)=\text{Var}(X)+\text{Var}(Y)$。
>
> *English: Var(aX + b) = a² Var(X). For independent X and Y, variances add: Var(X ± Y) = Var(X) + Var(Y).*

**白话版：** 规则一：给所有数都加 2，整体平移，散布程度不变；把所有数都放大 3 倍，距离也放大 3 倍，平方后是 9 倍。规则二：两个**独立**的波动叠在一起，总波动是**相加**的（注意减法也是加！因为「波动」不会因为你做减法而抵消）。**这条只有独立才成立**；没有独立，需要再加上一个「协方差」项，后面的课会讲。下面用精确的分数验证：

""" + C_RULE + r"""

规则一和规则二都验证成立。一个提醒：$\text{Var}(X+X)$ 不是 $2\text{Var}(X)$，因为 $X$ 和它自己**一点也不独立**，$\text{Var}(X+X)=\text{Var}(2X)=4\text{Var}(X)$。

### 样本方差为什么除以 n−1

> **标准定义 · 样本方差 (sample variance)**
>
> 给定样本 $x_1,\dots,x_n$，样本均值 $\bar x=\frac1n\sum x_i$，**样本方差** 定义为
>
> $$s^2=\frac{1}{n-1}\sum_{i=1}^n (x_i-\bar x)^2$$
>
> 除以 $n-1$ 使它成为总体方差的 **无偏估计 (unbiased estimator)**：$E[s^2]=\sigma^2$。
>
> *English: The sample variance divides by n − 1 (Bessel's correction) so that it is an unbiased estimator of the population variance.*

**白话版：** 真实的均值 $\mu$ 我们不知道，只能用样本自己的平均 $\bar x$ 代替。但样本均值天然「贴着」样本点，所以量出来的偏差**总是偏小**。除以 $n-1$ 而不是 $n$，正是为了把这个偏小补回来。用代码看这是不是真的：

""" + C_NM1 + r"""

除以 $n$ 的平均只有 0.8 左右，系统性偏小（$(n-1)/n=4/5$）；除以 $n-1$ 的平均接近真实值 1。当样本很大时，两者差别可以忽略。Python 里 `statistics.variance` 默认除以 $n-1$，而 NumPy 的 `np.var` 默认除以 $n$，要用 `ddof=1`，这是常见的坑。

### 这一节你要带走的三句话

1. **随机变量 = 给试验结果贴数字标签的函数**；它的分布（PMF）就是「每个值的概率表」。
2. **期望 = 长期平均**，对任意随机变量都能「拆开算」（线性性）。
3. **方差 = 离平均的平均平方距离**：$\text{Var}(aX+b)=a^2\text{Var}(X)$；独立时方差相加；用样本估计要除以 $n-1$。
"""),
  V("SzZ6GpcfoQY", "视频三（选看）：Calculating the Mean, Variance and Standard Deviation, Clearly Explained!!!（StatQuest）", 15),
  THINK("买一张彩票 2 元，中奖概率 1%，奖金 100 元。只买一次，你可能赚 98 元，也可能亏 2 元。期望是亏 1 元，那「买一次」的结果和期望是什么关系？如果有一万个人各买一次，总体会怎样？", r"""
只买一次，结果只能是「赚 98」或「亏 2」，**永远不会正好是亏 1 元**，期望并不是你会得到的值。

但一万个人各买一次，每个人的结果是独立的，平均每人亏接近 1 元，总共亏约 1 万元，而且这个「长期平均」会越来越稳。这就是期望的意义：**不预测单次，描述大量重复的平均**。（这个现象在下一节叫「大数定律」。）保险公司、赌场的生意，靠的就是这一点。
"""),
  THINK("你要给模型的输入做标准化：对每个特征减去均值、再除以标准差。如果原数据均值是 $\\mu$、方差是 $\\sigma^2$，处理后的数据均值和方差分别是多少？用本节的规则推一推。", r"""
设新变量 $Z=(X-\mu)/\sigma=\frac1\sigma X-\frac\mu\sigma$，这是 $aX+b$ 的形式，其中 $a=1/\sigma$。

均值：由线性性，$E[Z]=\frac1\sigma\mu-\frac\mu\sigma=0$。方差：由规则一，$\text{Var}(Z)=\frac1{\sigma^2}\sigma^2=1$（减去常数不改变方差）。所以处理后均值 0、方差 1，这正是「标准化」的名字来源。
"""),
  THINK("为什么用样本估计总体方差时，样本量 $n=1$ 的时候除以 $n-1$ 会出问题？这件事说明了什么？", r"""
$n=1$ 时，样本只有一个数，样本均值就是这个数本身，偏差必然是 0，分子是 0，分母 $n-1=0$，变成 $0/0$，**没有定义**。

这件事的含义是：**只有一个数据点，根本看不出「波动」**。你至少需要 2 个点才能谈散布。更一般地，估计均值用掉了 1 个「自由度 (degrees of freedom)」，剩下的 $n-1$ 个才是真正用于判断波动的信息，这也是除以 $n-1$ 的另一种理解。
"""),
  KW(("随机变量","random variable","把试验的每个结果对应到一个数的函数"),
     ("离散随机变量","discrete random variable","只取有限个或可数个值的随机变量"),
     ("概率质量函数","probability mass function (PMF)","离散变量取每个值的概率：$p_X(x)=P(X=x)$"),
     ("分布","distribution","随机变量取各个值（或各区间）的概率规律"),
     ("期望","expected value / expectation","按概率加权的平均值，长期平均：$E[X]=\\sum xP(X=x)$"),
     ("线性性","linearity of expectation","$E[aX+bY]=aE[X]+bE[Y]$，无需独立"),
     ("方差","variance","偏离均值的平方的期望：$E[(X-\\mu)^2]$"),
     ("标准差","standard deviation","方差的平方根，单位与数据相同"),
     ("独立","independence","一个变量的取值不提供另一个的信息；独立时方差可以相加"),
     ("样本方差","sample variance","用样本估计总体方差，除以 $n-1$"),
     ("无偏估计","unbiased estimator","估计量的期望等于真实值"),
     ("自由度","degrees of freedom","样本里真正独立提供信息的个数，估计方差时为 $n-1$"),
  ),
 ],
 "references": [
  {"title": "Harvard Statistics 110 Lecture 9：Expectation, Indicator Random Variables, Linearity（大学课程原视频，约 50 分钟，选看）", "url": "https://www.youtube.com/watch?v=LX2q356N2rU", "note": "期望与线性性的严格讲法，附很多巧妙的例子"},
  {"title": "Harvard Statistics 110 Lecture 8：Random Variables and Their Distributions（选看）", "url": "https://www.youtube.com/watch?v=k2BB0p8byGA", "note": "随机变量与分布的完整讲法"},
  {"title": "MIT OCW 6.041 Probabilistic Systems Analysis（课程主页，含讲义与习题）", "url": "https://ocw.mit.edu/courses/6-041sc-probabilistic-systems-analysis-and-applied-probability-fall-2013/", "note": "选做其中离散随机变量、期望与方差的习题"},
 ],
 "quiz": {"questions": [
  Q("下面哪一句最准确地描述 **随机变量**？",
    ["一个取值固定不变的数", "一个随机发生的事件", "一个把随机试验的每个结果对应成一个实数的函数", "一个取值在 0 到 1 之间的概率"], 2,
    "随机变量本质上是**函数**：输入是试验的结果，输出是一个数。事件是结果的集合，概率是 0 到 1 的数，二者都不是随机变量。"),
  Q("一枚公平的六面骰子，点数 $X$ 的期望 $E[X]$ 是多少？",
    ["3.5", "3", "4", "21"], 0,
    "$E[X]=(1+2+3+4+5+6)\\times\\frac16=21/6=3.5$。21 是各点数之和（忘了乘概率），3 和 4 是把期望当成「最可能的值」或取了中间的整数。"),
  Q("一个游戏：掷骰子，掷出 6 你赢 12 元，否则你输 2 元。每玩一次，你的平均收益（期望）是多少？",
    ["−2 元", "0 元", "2 元", "约 0.33 元（1/3 元）"], 3,
    "$E=12\\times\\frac16+(-2)\\times\\frac56=2-\\frac{10}6=\\frac13\\approx0.33$。这个游戏长期对你略有利。「2 元」只算了赢的那一半，没有减去输的部分。"),
  Q("已知 $E[X]=2$，$E[Y]=5$，则 $E[3X-Y+1]$ 等于？",
    ["0", "2", "6", "8"], 1,
    "由线性性，$E[3X-Y+1]=3E[X]-E[Y]+1=6-5+1=2$。6 是忘了减 $E[Y]$ 和加 1。"),
  Q("随机变量 $X$ 取 0 和 10 的概率各为 0.5，则 $\\text{Var}(X)$ 等于？",
    ["0", "10", "25", "5"], 2,
    "均值 $\\mu=5$，每个值与均值的距离都是 5，平方是 25，所以 $\\text{Var}(X)=25$。5 是标准差，不是方差。"),
  Q("已知 $\\text{Var}(X)=4$，则 $\\text{Var}(3X-2)$ 等于？",
    ["36", "10", "34", "12"], 0,
    "$\\text{Var}(aX+b)=a^2\\text{Var}(X)=9\\times4=36$。减 2 是平移，不改变方差；乘以 3 要把 3 平方。"),
  Q("$X$、$Y$ 相互独立，$\\text{Var}(X)=3$，$\\text{Var}(Y)=5$，则 $\\text{Var}(X-Y)$ 等于？",
    ["2", "8", "15", "$\\sqrt{8}$"], 1,
    "独立时方差相加，**减法也是加**：$\\text{Var}(X-Y)=\\text{Var}(X)+\\text{Var}(Y)=8$。$-Y$ 的方差仍是 $(-1)^2\\text{Var}(Y)=5$。"),
  Q("下面哪个说法是**错的**？",
    ["$E[X+Y]=E[X]+E[Y]$ 对任意随机变量 $X$、$Y$ 都成立", "$X$、$Y$ 独立时，$\\text{Var}(X+Y)=\\text{Var}(X)+\\text{Var}(Y)$", "标准差和 $X$ 本身的单位相同", "方差可以是负数"], 3,
    "方差是「平方的平均」，永远 $\\ge 0$，不可能是负数。其余三句都对：期望的线性性不需要独立；独立时方差可加；标准差是方差开方，单位回到原来的单位。"),
  Q("用样本估计总体方差时，通常除以 $n-1$ 而不是 $n$，主要原因是？",
    ["样本均值贴着样本点，使离差平方和偏小，除以 $n-1$ 可以修正这个偏差", "除以 $n-1$ 总是让结果更大，所以更保险", "样本里有一个数据必须扔掉", "因为除以 $n-1$ 计算起来更简单"], 0,
    "用样本均值代替未知的真实均值，会让偏差系统性偏小；除以 $n-1$ 后，$s^2$ 的期望正好等于总体方差（无偏）。不是「更保险」，也不是扔数据。"),
  Q("$\\text{Var}(X)=1$，则 $\\text{Var}(X+X)$ 等于？",
    ["2", "4", "1", "0"], 1,
    "$X+X=2X$，所以 $\\text{Var}(2X)=4\\text{Var}(X)=4$。注意 $X$ 和它自己完全相关，不独立，所以不能直接把两个方差相加得 2。"),
 ]},
}

if __name__ == '__main__':
    dump(unit, "prob-0", "u02-random-variables.json")
