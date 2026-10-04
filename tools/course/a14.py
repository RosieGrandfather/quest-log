"""ARENA 0.0 第 14 节：广播与张量操作（按 v3 格式重写，2026-10-04）"""
from unitlib import *
from a14c import (C_RULE, C_STRIDE, C_ALIGN, C_SILENT, C_COSINE, C_PAIR,
                  C_SAMPLE, C_SOFTMAX, C_CE, C_STANDARD, C_TORCH)
from a14_quiz import QUIZ

unit = {
 "id": "u14",
 "title": "广播与张量操作",
 "en": "Broadcasting & Tensor Manipulation",
 "minutes": 100,
 "objectives": [
  "掌握 **广播 (broadcasting)** 的两条规则（右对齐补 1、逐维相等或为 1），能一眼判断两个形状能不能广播、结果是什么形状，并知道广播是**视图**而不是复制",
  "会用 `None` / `unsqueeze`、`squeeze`、`keepdims`（PyTorch 里是 `keepdim`）让形状对齐，并用 `assert` 守住关键形状，避开「不报错却算错」的广播 bug",
  "会写几个机器学习里最高频的张量操作：特征标准化、行归一化与 **余弦相似度矩阵 (cosine similarity matrix)**、**两两距离矩阵 (pairwise distance)**、分类准确率、按概率采样",
  "理解 **softmax** 的平移不变性与数值稳定写法，会写 **logsumexp**，并能手写 **交叉熵 (cross-entropy)** 损失",
  "能把同一件事写成循环、广播、矩阵乘法三种形式并对拍，理解它们在内存和速度上的取舍",
 ],
 "blocks": [
  T(r"""
### 先说这一节要干什么

ARENA 0.0 的后半部分，大量练习都在考**广播**。原因很实际：深度学习代码里几乎每一行都在对形状不同的张量做运算，例如「给一批样本的每一行加偏置」「把每个 token 的向量除以自己的长度」「把 logits 变成概率」。广播让你不用写循环就能做到，但它也是**最容易出隐蔽 bug** 的地方：形状对不上时有时会报错，有时却**悄悄算出一个错误的结果**，训练照样能跑，只是模型变差。

这一节分三步：先把广播规则讲清楚，并且真的去验证它（包括它为什么不占内存）；再学会用形状工具和 `assert` 对付隐蔽 bug；最后用广播写出机器学习里最常用的几个操作，包括 softmax、logsumexp 和交叉熵。所有代码都用 NumPy 写并真实运行（你的电脑上也能复现），最后再给出 PyTorch 的对应写法。

**学完它你就能看懂这几件事：**

- Transformer 里 `x / x.norm(dim=-1, keepdim=True)`、`logits - logits.max(dim=-1, keepdim=True).values` 为什么都要写 `keepdim=True`；
- 为什么训练时 loss 突然变成 `nan`（softmax 溢出），以及 PyTorch 里 `F.cross_entropy` 内部做了什么；
- k 近邻、聚类、对比学习、注意力里反复出现的「两两距离 / 两两相似度」是怎么一次算出来的；
- 一行不报错的广播代码，为什么可能是错的，以及怎么提前发现。

**本节安排（约 100 分钟）**：导读（5 分钟）→ 视频（13 分钟）→ 广播规则与判断练习（15 分钟）→ 广播是视图（8 分钟）→ 形状工具与隐蔽 bug（15 分钟）→ 高频操作：标准化、余弦相似度、两两距离、准确率、采样（22 分钟）→ softmax、logsumexp、交叉熵（15 分钟）→ PyTorch 对照与「想一想」（7 分钟）。视频是英文的，可以打开 YouTube 的中文字幕。
"""),
  V("oG1t3qlzq14", "视频：Numpy Array Broadcasting In Python Explained（mCoding）", 13),
  T(r"""
### 广播的两条规则

> **标准定义 · 广播 (broadcasting)**
>
> 对两个形状为 $(a_1,\dots,a_m)$ 和 $(b_1,\dots,b_n)$ 的数组做逐元素运算时：**第一步**，把它们的形状**右对齐**，维数少的那个在**左边补长度为 1 的维度**，使维数相同；**第二步**，逐个维度比较：两个长度**相等**，或者**其中一个为 1**，则这一维兼容，结果取较大者；否则报错。长度为 1 的维度被「拉伸」到另一方的长度，不需要复制数据。
>
> *English: Shapes are aligned from the trailing (rightmost) dimension, padding the shorter one with 1s on the left. Two dimensions are compatible if they are equal or one of them is 1; the result takes the larger size. A dimension of size 1 is stretched to match the other.*

**白话版：「从右边对齐，缺的补 1，1 可以变成任何长度」。** 想象你有一张成绩单 `data`（N 个学生 × k 门课），又有一个长度为 k 的「每门课加分」向量 `vec`。`vec` 只有一行，但它想加到每个学生头上，这就是广播：把这一行「抄」给每个学生。结果 `out[i, j] = data[i, j] + vec[j]`。

下面的代码用 `np.broadcast_shapes` 一次判断八种组合（前面几行就是 ARENA 判断题的类型），最后用双重循环验证广播真的就是「每一行都加上这个向量」：

""" + C_RULE + r"""

读输出：

- `(5, 3) + (3,)`：`(3,)` 补成 `(1, 3)`，第 0 维 5 对 1 兼容，结果 `(5, 3)`。
- `(2, 1, 4) + (3, 1)`：`(3, 1)` 补成 `(1, 3, 1)`，逐维得 `(2, 3, 4)`，**两个张量都被拉伸了**。
- `(8, 1, 6, 1) + (7, 1, 5)`：后者补成 `(1, 7, 1, 5)`，结果 `(8, 7, 6, 5)`，正好是「想一想」第 1 题的形状。
- `(6, 2) + (6,)` 报错：`(6,)` 对齐的是**最后一维** 2，6 和 2 既不相等也都不是 1。想按行相加，应该把它写成 `(6, 1)`。
- `(2, 3, 4) + (2, 1)` 报错：`(2, 1)` 补成 `(1, 2, 1)`，中间一维 3 对 2 不兼容。
- 最后一行 `(4, 1) + (4,)` **不报错**，得到 `(4, 4)`：列向量和行向量相加，变成了一张表。这是最危险的情形，后面专门讲。
- 最后一句 `True`：广播的结果和「每行加 `vec`」的双重循环**完全一样**。

**判断口诀**：写出两个形状，右对齐，从右往左一维一维看——要么相等，要么有一个是 1。只要有一维不满足，就是报错。

### 广播是「视图」：它不占内存

> **标准定义 · 步长 (stride) 与零步长**
>
> NumPy / PyTorch 数组在内存里是一段连续的数据，加上每个维度的**步长 (stride)**：沿这一维走一格，要在内存里跳过多少字节。广播把长度为 1 的维度「拉伸」，靠的是把那一维的步长设为 **0**：不管走到第几格，读的都是同一块内存。因此广播本身**不复制数据**。
>
> *English: Arrays are stored as one block of memory plus a stride per dimension (bytes to skip per step along that axis). Broadcasting stretches a size-1 dimension by giving it stride 0, so every position reads the same memory, and no data is copied.*

**白话版：「复印一千份不用真的复印，只要每次都翻回同一页」。** 用 `np.broadcast_to` 可以亲眼看到：

""" + C_STRIDE + r"""

读输出：把长度 5 的 `vec` 广播成 `(1000, 5)`，`strides` 是 `(0, 8)`：沿第 0 维走一格跳过 0 字节（每一行都是同一份数据），沿第 1 维每格 8 字节（`float64` 占 8 字节）。`np.shares_memory` 为 `True`，而且这个视图是**只读**的。对比真正复制的 `np.tile`：`strides` 变成 `(40, 8)`，实际占用 40000 字节，和原数组不共用内存。**要点**：`data + vec` 这样的广播运算本身很省内存（但**结果**是一个完整的新数组）；真正吃内存的，是你自己用 `repeat` / `tile` 手动复制，或者让广播产生一个巨大的中间张量（后面「两两距离」的实验会看到）。

### 让形状对齐的工具

规则只管「兼容不兼容」，要让两个形状**变得**兼容，靠这几个工具：

| 想做的事 | NumPy | PyTorch |
|---|---|---|
| 在位置 0 插入长度为 1 的维度 | `x[None]` 或 `np.expand_dims(x, 0)` | `x.unsqueeze(0)` |
| 在最后插入长度为 1 的维度 | `x[..., None]` | `x.unsqueeze(-1)` |
| 去掉长度为 1 的维度 | `np.squeeze(x, axis=1)` | `x.squeeze(1)` |
| 归约后保留被归约的维度 | `x.sum(axis=1, keepdims=True)` | `x.sum(dim=1, keepdim=True)` |

""" + C_ALIGN + r"""

读输出：`x` 是 `(3, 1, 5)`。在最前面插入得 `(1, 3, 1, 5)`，在最后插入得 `(3, 1, 5, 1)`，`squeeze` 第 1 维得 `(3, 5)`。一个**框架之间的差别**：对第 0 维（长度是 3，不是 1）做 `squeeze`，NumPy 会报错，而 PyTorch 的 `squeeze(0)` 会**什么也不做**，不报错（本节最后的 PyTorch 块会演示）。同样是 `sum`，不加 `keepdims` 得 `(3,)`，加了得 `(3, 1)`。后者才能和 `(3, 4)` 的原矩阵直接广播，每行减去自己的均值之后，各行的均值是 0。最后一行展示了忘记 `keepdims` 时 NumPy 的报错：`(3,4)` 对 `(3,)`。

### 隐蔽 bug：不报错，但算错了

广播最令人头疼的是：很多时候它**不报错**。

""" + C_SILENT + r"""

读输出：

1. `M` 是 $3\times3$ 的方阵。忘了 `keepdims` 时，`M.mean(axis=1)` 是形状 `(3,)` 的向量，它被当成「对齐最后一维」，也就是**每一列**减一个数，而不是每一行。形状恰好是方阵，所以 `3 == 3`，**不报错**。
2. 两种写法的结果不相等（`False`）。正确做法下每行均值都是 0；错误做法下每行均值是 `[-3. 0. 3.]`，说明行根本没有被居中。
3. 如果这一行出现在训练代码里，模型照样能训练，只是效果莫名其妙变差，很难查。
4. `(4, 1) + (4,)` 得到 `(4, 4)`：你以为是两个长度为 4 的向量相加，实际是一个列向量加一个行向量。

**防御办法**（ARENA 的建议）：**关键位置写 `assert x.shape == (...)`**；不要把很多操作挤在一行里；调试时测试用**不相等的维度**（比如 `n=3, d=4`），这样形状错误会当场变成报错，而不是悄悄算错。

> **一个自检习惯**：每写一行广播，先默念两个形状，右对齐，再想「结果应该是什么形状」。对不上就停下来。

### 高频操作一：特征标准化

> **标准定义 · 标准化 (standardization)**
>
> 对数据矩阵 $X\in\mathbb{R}^{N\times d}$（每行一个样本，每列一个特征），按**列**计算均值 $\mu_j$ 和标准差 $\sigma_j$，令 $Z_{ij}=(X_{ij}-\mu_j)/\sigma_j$。结果每一列均值为 0、标准差为 1。
>
> *English: Standardization subtracts each column's mean and divides by its standard deviation, so every feature has mean 0 and standard deviation 1.*

**白话版：「把不同单位的量，换算到同一把尺子上」。** 身高用厘米、体重用公斤、收入用万元，数字大小天差地别，直接喂给模型，数字大的特征会「压过」小的。标准化就是把每一列都换成「比平均高出几个标准差」。一次写下来只要一行广播：`(X - X.mean(axis=0)) / X.std(axis=0)`，`(N, d)` 对 `(d,)`。

""" + C_STANDARD + r"""

读输出：三个特征的均值分别是 0.01、100.49、-5.0，标准差分别是 1.0、19.95、0.1，量纲差了几百倍。按列标准化后，三列均值都是 0、标准差都是 1（这是**广播**的功劳：`(1000, 3)` 减去 `(3,)`）。最后两行是**反例**：如果错把方向写成按行（每一行减自己的均值），三个特征的差别根本没有被消除：第二列几乎总是同一个值（标准差约 0.0），因为一行里 100 左右的那个数占了绝对主导，信息全被抹掉了。**`axis` 选哪一个，是由「你想让哪个方向上的东西可比」决定的**，不能随便写。

### 高频操作二：行归一化与余弦相似度矩阵

> **标准定义 · 余弦相似度 (cosine similarity)**
>
> 两个非零向量 $\mathbf{a},\mathbf{b}$ 的余弦相似度为 $\cos\theta=\dfrac{\mathbf{a}\cdot\mathbf{b}}{\|\mathbf{a}\|\,\|\mathbf{b}\|}$，取值在 $[-1,1]$，只看**方向**、不看长度。若先把每一行除以自己的 $L_2$ 范数 $\|\mathbf{x}\|_2=\sqrt{\sum_i x_i^2}$，得到行归一化矩阵 $\hat X$，则 $\hat X\hat X^\top$ 的第 $(i,j)$ 个元素就是第 $i$ 行与第 $j$ 行的余弦相似度。
>
> *English: Cosine similarity is a·b / (‖a‖‖b‖), depending only on direction. After normalising each row to unit length, X̂X̂ᵀ is the matrix of all pairwise cosine similarities.*

**白话版：「只比方向，不比长短」。** 两篇文章，一篇是另一篇的两倍长，词频向量的长度差很多，但方向一样，余弦相似度就是 1。词向量、句向量检索、对比学习都用它。

""" + C_COSINE + r"""

读输出：三个向量的范数是 5、1、2，其中 `(3, 4)` 的范数是 $\sqrt{9+16}=5$。归一化后每行的范数都是 1。相似度矩阵里：对角线全是 1（和自己方向相同）；第 0 行和第 1 行是 0.6（$\frac{3\times1+4\times0}{5\times1}=0.6$）；第 0 行和第 2 行是 0.8（$\frac{3\times0+4\times2}{5\times2}=0.8$）；$(1,0)$ 和 $(0,2)$ 垂直，相似度是 0。这里的 `keepdims=True` 非常关键：范数的形状是 `(3, 1)`，才能让 `(3, 2) / (3, 1)` 按行相除。

后半段是**分类准确率**：`argmax(axis=1)` 取出每个样本得分最高的类别，得到 `[1 0 2 1]`，和真实标签 `[1 0 1 1]` 比较，4 个里对了 3 个，准确率 0.75。

### 高频操作三：两两距离矩阵（广播与内存的取舍）

k 近邻、聚类、对比学习、注意力都要「点集 A 里每个点，到点集 B 里每个点的距离」。这是广播最经典的用法，我们顺便做一个小实验，把同一件事写成三种形式并对拍：

""" + C_PAIR + r"""

读输出：

- **写法一（循环）**是最直观的定义，作为「标准答案」。
- **写法二（广播）**：`A[:, None, :]` 是 `(300, 1, 64)`，`B[None, :, :]` 是 `(1, 200, 64)`，相减得到 `(300, 200, 64)` 的中间张量，再对最后一维求和。和循环完全一致（`True`）。但中间张量有 $300\times200\times64$ 个数，约 **30.7 MB**。点数再多一个数量级，内存就会成为瓶颈。
- **写法三（矩阵乘法）**：把 $\|\mathbf{a}-\mathbf{b}\|^2$ 展开为 $\|\mathbf{a}\|^2+\|\mathbf{b}\|^2-2\,\mathbf{a}\cdot\mathbf{b}$，只需要 `(300, 200)` 的矩阵，内存小得多，和广播版一致，最大差异小于 $10^{-8}$。工程里更常用这种写法。外面套的 `np.maximum(sq, 0)` 是因为浮点误差可能让很小的平方距离变成极小的负数，直接开方会出 `nan`。

**经验**：广播很方便，但要留意**它产生的中间张量有多大**。能化成矩阵乘法的，通常更省内存、也更快。

### 高频操作四：按概率分布采样（不写循环）

> **标准定义 · 逆变换采样 (inverse transform sampling)**
>
> 要从取值 $0,1,\dots,K-1$、概率为 $p_0,\dots,p_{K-1}$ 的离散分布采样：取均匀随机数 $U\sim\text{Uniform}(0,1)$，令累积和 $c_k=p_0+\cdots+p_k$，输出 $\#\{k: U>c_k\}$，即 $U$ 超过了几个累积值。这样输出 $k$ 的概率恰好是 $c_k-c_{k-1}=p_k$。
>
> *English: To sample a discrete distribution, draw U ~ Uniform(0,1) and return the number of cumulative sums that U exceeds; this returns k with probability p_k.*

**白话版：「把 0 到 1 的线段按概率切成几段，扔飞镖看落在哪一段」。** 概率 `[0.2, 0.3, 0.5]` 把线段切成 $[0,0.2)$、$[0.2,0.5)$、$[0.5,1)$ 三段，每段的长度就是概率。

""" + C_SAMPLE + r"""

读输出：累积和是 `[0.2 0.5 1.]`。`u` 是 `(n, 1)`，`cum` 是 `(3,)`，广播成 `(100000, 3)`，每一行数「这个随机数超过了几个边界」，求和得 0、1、2 之一。10 万次采样的频率是 `[0.201 0.3 0.499]`，和目标 `[0.2 0.3 0.5]` 很接近。这正是语言模型「按概率抽下一个词」的原理，实际中会用 `np.random.choice` 或 PyTorch 的 `multinomial`，思路相同。

### Softmax、logsumexp 与交叉熵

> **标准定义 · softmax**
>
> 把任意实数向量 $\mathbf{z}$（**logits**）变成概率分布：$\text{softmax}(\mathbf{z})_i=\dfrac{e^{z_i}}{\sum_j e^{z_j}}$。输出每项为正，和为 1。它有**平移不变性**：对任意常数 $c$，$\text{softmax}(\mathbf{z}-c\mathbf{1})=\text{softmax}(\mathbf{z})$。
>
> *English: Softmax maps real logits to a probability distribution, softmax(z)_i = e^{z_i} / Σ_j e^{z_j}. It is invariant to adding a constant to all logits.*

**白话版：「分数越高，占的份额越大，而且保证总份额是 1」。** 但计算机里有个陷阱：$e^{1000}$ 超出了浮点数的范围，变成 `inf`；`inf / inf` 是 `nan`。利用平移不变性，先减去最大值就能避开溢出。

> **标准定义 · logsumexp**
>
> $\text{logsumexp}(\mathbf{z})=\log\sum_i e^{z_i}$。数值稳定的算法：取 $c=\max_i z_i$，则 $\text{logsumexp}(\mathbf{z})=c+\log\sum_i e^{z_i-c}$。它和 log-softmax 的关系是 $\log\text{softmax}(\mathbf{z})_i=z_i-\text{logsumexp}(\mathbf{z})$。
>
> *English: logsumexp(z) = log Σ e^{z_i}, computed stably as c + log Σ e^{z_i − c} with c = max z.*

**白话版：「先把最大的那个提出来，剩下的都不会爆」。**

""" + C_SOFTMAX + r"""

读输出：直接算得到 `[nan nan nan]`，因为 $e^{1000}$ 溢出。减去最大值之后，三个数变成 $e^{-2},e^{-1},e^{0}$ 的比例，得到 `[0.09 0.2447 0.6652]`，和为 1。`logsumexp` 是 1002.4076，等于 $1002+\log(e^{-2}+e^{-1}+1)=1002+0.4076$。最后一行验证了**平移不变性**：给 logits 同时加 500，softmax 不变。注意代码里 `max`、`sum` 都带了 `keepdims=True`，所以对形状 `(batch, classes)` 的批量输入同样适用。

> **标准定义 · 交叉熵损失 (cross-entropy loss)**
>
> 对一个样本，模型给出 logits $\mathbf{z}$，正确类别为 $y$，则损失为 $-\log\text{softmax}(\mathbf{z})_y=\text{logsumexp}(\mathbf{z})-z_y$。对一批样本取平均。它越小，说明模型给正确类别的概率越高；当正确类别的概率是 1，损失为 0。
>
> *English: For logits z and correct class y, the cross-entropy loss is −log softmax(z)_y = logsumexp(z) − z_y, averaged over the batch.*

**白话版：「正确答案被你押了多大的概率，就按 $-\log$ 扣多少分」。** 押得越准扣得越少，押错了会被重罚（概率趋近 0 时，$-\log$ 趋近无穷）。第 9 节信息论会从「惊讶程度」讲它的来源。

""" + C_CE + r"""

读输出：`logsumexp` 保留了维度，形状 `(batch, 1)`，所以 `logits - logsumexp(logits)` 是 `(2, 3) - (2, 1)` 的广播。`logp` 每行取 `exp` 后和为 `[1. 1.]`，验证它确实是对数概率。`logp[np.arange(2), target]` 是**整数数组索引**（下一节详讲）：取出 `logp[0, 0]` 和 `logp[1, 2]`，分别是 -0.3168 和 -0.1148。取负取平均，交叉熵是 0.2158，和 PyTorch 的 `F.cross_entropy` 一致（见下面的对照块），也和直接按概率定义的逐样本写法一致（`True`）。为什么要走 `logsumexp` 这条路，而不是先算 softmax 再取 `log`？因为先算 softmax 可能得到极小的概率（甚至下溢成 0），再取 `log` 就是 `-inf`；用 log-softmax 全程在对数域里，不会出问题。这就是 PyTorch 里 `F.cross_entropy` 直接吃 logits、而不吃概率的原因。

### PyTorch 对照

上面的每一件事，PyTorch 的写法几乎一一对应：`axis` 换成 `dim`，`keepdims` 换成 `keepdim`，`x[None]` 也可以写成 `x.unsqueeze(0)`。注意前面提到的框架差别：PyTorch 里对长度不为 1 的维度调用 `squeeze` 不报错，什么也不做，所以更容易**悄悄出 bug**。

""" + C_TORCH + r"""

### 这一节你要带走的三句话

1. **广播 = 右对齐、缺的补 1、逐维「相等或有一个是 1」**；它是零步长的视图，不复制数据，但结果和中间张量会占内存；忘了 `keepdims` 是最常见的错误来源。
2. **形状对得上 ≠ 算对了**：方阵和 `(4, 1)` 对 `(4,)` 这类情形会悄悄算错，所以关键位置写 `assert`，测试时用互不相等的维度。
3. **softmax 要减最大值，交叉熵要用 logsumexp（log-softmax）**：数学上等价的公式，数值上可能一个能用、一个得 `nan`；训练里的 loss 出现 `nan`，先查这里。
"""),
  THINK("`a` 形状 `(8, 1, 6, 1)`，`b` 形状 `(7, 1, 5)`。`a + b` 的形状是什么？再回答：如果 `b` 的形状改成 `(7, 2, 5)`，会怎样？", r"""
从右往左对齐，`b` 补成 `(1, 7, 1, 5)`：

| | 维 0 | 维 1 | 维 2 | 维 3 |
|---|---|---|---|---|
| a | 8 | 1 | 6 | 1 |
| b | 1 | 7 | 1 | 5 |
| 结果 | 8 | 7 | 6 | 5 |

每一维都是「相等或有一个是 1」，结果是 `(8, 7, 6, 5)`（这和上面 `np.broadcast_shapes` 的输出一致）。

如果 `b` 是 `(7, 2, 5)`，补成 `(1, 7, 2, 5)`，维 2 是 6 对 2，既不相等也都不是 1，**报错**。
"""),
  THINK("想让矩阵 `M`（形状 `(n, d)`）的每一**列**减去该列的平均值，怎么写？每一**行**呢？如果 $n=d$，漏掉 `keepdims=True` 会发生什么，为什么比 $n\\neq d$ 更危险？", r"""
- **每列减列均值**：`M - M.mean(axis=0)`。均值形状 `(d,)`，对齐最后一维，广播没问题（写成 `keepdims=True` 得到 `(1, d)` 也可以）。
- **每行减行均值**：`M - M.mean(axis=1, keepdims=True)`。**必须** `keepdims=True` 得到 `(n, 1)`。
- 漏掉时，`(n,)` 要去对齐最后一维 `d`：$n\neq d$ 时直接报错，你会马上发现；**$n=d$ 时不报错**，变成「每一列减去一个本来属于某一行的数」，结果是错的（本节代码里 $3\times3$ 的例子，行均值变成了 `[-3. 0. 3.]`）。**报错是好事，不报错的错误才可怕**，所以测试时用互不相等的维度。
"""),
  THINK("交叉熵损失为什么通常要「logits 直接进 `log_softmax`」，而不是「先算 softmax 概率，再取 `log`」？这和下面这件事有什么关系：一个 10 万个词的语言模型，某个词的概率可能是 $10^{-50}$？", r"""
先算 softmax 得到概率，再取 `log`，有两个问题：

1. softmax 的分子 $e^{z_i}$ 可能溢出（$z_i$ 很大）；即使用减最大值的办法避开了溢出，**很小的概率**（比如 $e^{-120}$）在 `float32` 里可能下溢成 0，`log(0)` 得到 `-inf`，损失变成 `inf` 或 `nan`。
2. 梯度也会出问题：$\log p$ 对 $p$ 的导数是 $1/p$，$p$ 极小时数值很大且不精确。

直接用 $\log\text{softmax}(\mathbf{z})_i=z_i-\text{logsumexp}(\mathbf{z})$，全程在对数域里计算，$10^{-50}$ 这样的概率只是 $-115$ 左右的一个普通数字，没有任何下溢。语言模型的词表很大，很多词的概率极小，所以这是必须的。这也是 PyTorch 的 `F.cross_entropy` 接受 **logits** 而不是概率的原因：它内部就是这样做的。
"""),
  KW(("广播","broadcasting","右对齐、缺的补 1、逐维相等或为 1，自动「复制」长度为 1 的维度"),
     ("逐元素运算","elementwise operation","对应位置分别计算，如 `+ - * /` 和比较"),
     ("步长","stride","沿某一维走一格要跳过的内存字节数；广播的维度步长为 0"),
     ("视图 / 副本","view / copy","视图共用内存，副本是新内存"),
     ("插入 / 去掉维度","unsqueeze / squeeze","加上 / 去掉长度为 1 的维度，NumPy 里常写 `x[None]`"),
     ("保留维度","keepdims (keepdim)","归约后保留长度为 1 的维度，方便后续广播"),
     ("标准化","standardization","每列减均值、除标准差，使均值 0、标准差 1"),
     ("L2 范数","L2 norm","$\\sqrt{\\sum x_i^2}$，向量的长度"),
     ("余弦相似度矩阵","cosine similarity matrix","行归一化后 `Xn @ Xn.T`，只比较方向"),
     ("两两距离","pairwise distance","`(n,1,d)` 对 `(1,m,d)` 广播，或用展开式 + 矩阵乘法"),
     ("最大值下标","argmax","分数最高的类别，用于分类预测和准确率"),
     ("累积和","cumsum","`[0.2, 0.3, 0.5] → [0.2, 0.5, 1.0]`，用于按概率采样"),
     ("Softmax","softmax","logits → 概率分布，有平移不变性"),
     ("对数-求和-指数","logsumexp","$\\log\\sum e^{z_i}$ 的稳定算法：先减最大值"),
     ("交叉熵","cross-entropy","$-\\log$ 正确类别的概率，等于 logsumexp 减去正确类别的 logit"),
     ("数值稳定性","numerical stability","避免溢出 / 下溢，数学上等价的公式数值上可能差别巨大"),
  ),
 ],
 "references": [
  {"title": "ARENA [0.0] Prerequisites — Broadcasting 与张量操作练习部分", "url": ARENA_URL, "note": "本节依据的原文大纲、广播判断题和练习（讲解为自写，未转载原文）"},
  {"title": "ARENA 0.0 练习 Notebook（Colab）", "url": ARENA_COLAB, "note": "动手做温度归一化、余弦相似度、采样、softmax、交叉熵等练习"},
  {"title": "NumPy 官方：Broadcasting", "url": "https://numpy.org/doc/stable/user/basics.broadcasting.html", "note": "规则的官方说明，含图示"},
  {"title": "The Log-Sum-Exp Trick（Gregory Gundersen）", "url": "https://gregorygundersen.com/blog/2020/02/09/log-sum-exp/", "note": "ARENA 推荐的 logsumexp 讲解"},
  {"title": "PyTorch 文档：Broadcasting semantics", "url": "https://pytorch.org/docs/stable/notes/broadcasting.html", "note": "PyTorch 的广播规则，和 NumPy 一致，另有原地运算的限制"},
 ],
 "quiz": {"questions": QUIZ},
}

if __name__ == '__main__':
    dump(unit, "arena-0.0", "u14-broadcasting.json")
