"""ARENA 0.0 第 2 节：反向传播（按 v3 格式重写，2026-10-04）"""
from unitlib import *
from a02c import C_CHAIN, C_BACK, C_COST, C_BATCH, C_VANISH, C_XORBP
from a02_quiz import QUIZ

unit = {
 "id": "u02",
 "title": "反向传播",
 "en": "Backpropagation",
 "minutes": 100,
 "objectives": [
  "说清楚 **反向传播 (backpropagation)** 要解决的问题：一次性、高效地算出代价函数对**每一个参数**的**偏导数 (partial derivative)**，并能算出它比「逐个参数微调」省多少",
  "会用 **链式法则 (chain rule)** 写出单个权重、偏置的梯度公式，理解 **加权输入 $z$**、**误差项 $\\delta$** 在公式里的角色",
  "理解为什么必须**从后往前**算、一个神经元的梯度为什么要对**所有路径求和**（矩阵形式就是乘 $W^\\top$），能用 NumPy 写出一个两层网络的反向传播并做**梯度检验 (gradient checking)**",
  "理解 **小批量随机梯度下降 (mini-batch SGD)** 与 **梯度消失 (vanishing gradient)**，知道 PyTorch 的 **自动求导 (autograd)** 和 **计算图 (computational graph)** 在替你做什么",
 ],
 "blocks": [
  T(r"""
### 先说这一节要干什么

上一节说「训练 = 沿负梯度走」，但留下一个没回答的问题：**13,002 个偏导数到底怎么算？** 这一节回答它。答案就是整个深度学习的发动机：**反向传播**。你在 PyTorch 里写的每一句 `loss.backward()`，背后跑的都是这一节的内容。

这一节的目标不是背公式，而是做到：给你一个小网络，你能**自己推出每个参数的梯度、自己用 NumPy 写出来、并且能证明写对了**（梯度检验）。数据科学和 AI 方向的硕士课程里，这是最常见的「从零实现」作业之一。

**学完它你就能看懂这几件事：**

- `loss.backward()` 之后，每个参数的 `.grad` 是怎么来的，为什么它的形状和参数完全一样；
- 为什么训练一个模型比用它做推理贵得多、更占显存（反向要用到前向时存下的中间量）；
- 为什么「网络太深、用 Sigmoid」会训练不动，ReLU 和后来的各种改进（残差连接、归一化）在解决什么；
- 为什么训练循环里是「一批一批」地取数据，而不是每步都用全部数据。

**本节安排（约 100 分钟）**：导读与为什么需要反向传播（10 分钟）→ 视频三（13 分钟，直觉）→ 链式法则与单神经元推导（15 分钟）→ 视频四（10 分钟，微积分）→ 多神经元、矩阵形式与梯度检验（20 分钟）→ 效率账（5 分钟）→ 小批量与动手实验（15 分钟）→ 梯度消失实验（7 分钟）→「想一想」。视频是英文的，可以打开 YouTube 的中文字幕。

### 为什么不能「逐个参数试」

> **标准定义 · 偏导数与数值梯度 (partial derivative & numerical gradient)**
>
> 函数 $C(\theta_1,\dots,\theta_n)$ 对 $\theta_i$ 的**偏导数**是「只动 $\theta_i$、其余不动」时 $C$ 的瞬时变化率：$\dfrac{\partial C}{\partial\theta_i}=\lim_{h\to0}\dfrac{C(\theta_i+h)-C(\theta_i)}{h}$。**数值梯度 (numerical gradient)** 用一个很小的 $h$ 近似它，常用**中心差分**：$\dfrac{C(\theta_i+h)-C(\theta_i-h)}{2h}$。每个参数需要 **2 次**前向传播。
>
> *English: The partial derivative ∂C/∂θ_i is the rate of change of C when only θ_i moves. A numerical gradient approximates it with a small step h, e.g. the central difference (C(θ+h) − C(θ−h)) / 2h, costing two forward passes per parameter.*

**白话版：「一个一个拨旋钮，看指针动多少」。** 网络有 13,002 个旋钮，你想知道每个旋钮对「总扣分」的影响，笨办法就是：拨一下第 1 个，重新答一遍整套卷子，记下扣分变化；再拨第 2 个……下面把账算清楚：

""" + C_COST + r"""

读输出：对视频里的网络，逐个参数微调要做 26,004 次前向传播，约 3.4 亿次乘法；反向传播只相当于约 3 次前向的工作量，约 3.9 万次乘法，**差了将近 9000 倍**。而且这个差距会随参数个数线性增大：对 70 亿参数的模型，逐个微调是完全不可能的。所以我们需要一种「**一次性把所有偏导数都算出来**」的办法。

### 链式法则：反向传播的全部数学

> **标准定义 · 链式法则 (chain rule)**
>
> 若 $y=f(u)$，$u=g(x)$，则 $\dfrac{dy}{dx}=\dfrac{dy}{du}\cdot\dfrac{du}{dx}$。多变量情形：若 $y$ 通过 $u_1,\dots,u_k$ 依赖于 $x$，则 $\dfrac{\partial y}{\partial x}=\sum_{j=1}^{k}\dfrac{\partial y}{\partial u_j}\dfrac{\partial u_j}{\partial x}$，即**对所有路径求和**。
>
> *English: If y = f(u) and u = g(x), then dy/dx = (dy/du)(du/dx). When y depends on x through several intermediate variables u_j, the derivatives of all paths are summed: ∂y/∂x = Σ_j (∂y/∂u_j)(∂u_j/∂x).*

**白话版：「传话链上的放大倍数」。** $x$ 动一点推动 $u$，$u$ 再推动 $y$：每一环有自己的放大倍数，总倍数就是各环**相乘**。如果有多条传话路线（一个人把话同时传给好几个人，这些人又都影响最终结果），就把每条路线的倍数**相加**。神经网络就是一长串这样的传话，反向传播不过是把这条规则用到底，并且聪明地**复用**中间结果。

### 视频三：先建立直觉
"""),
  V("Ilg3gGewQ5U", "视频三：Backpropagation, intuitively（深度学习第 3 集）", 13),
  T(r"""
看完这集，你应该能说出三件事：

1. 想让某个输出神经元更亮，有三条路：调**偏置**，调**权重**（连到越亮的上一层神经元，调它的权重效果越明显），或者改变**上一层的激活值**（权重为正的让它更亮，为负的让它更暗）。前两条我们能直接改，第三条不能直接改，但可以把「希望上一层怎么变」这个要求**往前传**，这就是「反向传播」名字的来由；
2. 上一层每个神经元会同时收到输出层所有神经元的「要求」，要把这些要求**加在一起**；
3. 一个样本只代表一个样本的「愿望」，真正的梯度是**所有训练样本的平均**。

### 单神经元链：把链式法则写出来

先看最简单的网络：**每层只有一个神经元**。对最后一层 $L$，一个训练样本的前向过程是三步，每一步只依赖前一步：

> **标准定义 · 加权输入与前向链 (weighted input & forward chain)**
>
> 对第 $l$ 层的神经元，**加权输入 (weighted input)** $z^{(l)}=w^{(l)}a^{(l-1)}+b^{(l)}$，激活值 $a^{(l)}=\sigma\big(z^{(l)}\big)$；最后一层的平方误差代价 $C_0=\big(a^{(L)}-y\big)^2$。依赖关系是 $w^{(L)}\to z^{(L)}\to a^{(L)}\to C_0$，所以对权重、偏置、上一层激活值的偏导数各是三个因子（或两个因子）的乘积：
>
> $$\frac{\partial C_0}{\partial w^{(L)}}=\underbrace{a^{(L-1)}}_{\partial z/\partial w}\cdot\underbrace{\sigma'\big(z^{(L)}\big)}_{\partial a/\partial z}\cdot\underbrace{2\big(a^{(L)}-y\big)}_{\partial C_0/\partial a}$$
>
> *English: With weighted input z = w·a_prev + b and activation a = σ(z), the cost C0 = (a − y)² depends on w through z and a. The chain rule gives ∂C0/∂w = a_prev · σ'(z) · 2(a − y); similarly ∂C0/∂b = σ'(z) · 2(a − y) and ∂C0/∂a_prev = w · σ'(z) · 2(a − y).*

**白话版：「三个放大倍数连乘」。** $w$ 变一点，$z$ 变多少？倍数是上一层的激活值 $a^{(L-1)}$（上一层越亮，这个权重越有话语权，与视频一致）；$z$ 变一点，$a$ 变多少？倍数是 Sigmoid 在这一点的斜率 $\sigma'(z)$；$a$ 变一点，代价变多少？倍数是 $2(a-y)$（错得越多越敏感）。偏置的第一个因子是 1（$\partial z/\partial b=1$）；而对上一层激活值，第一个因子是 $w$，这个量就是「往前传的要求」。Sigmoid 的导数有个好用的形式 $\sigma'(z)=\sigma(z)\big(1-\sigma(z)\big)=a(1-a)$，不用再算指数。

""" + C_CHAIN + r"""

读输出：$z=0.8\times0.5+0.1=0.5$，激活值 0.6225，离正确答案 1 还差一截，代价 $0.1425$。三个导数都是负的：**增大 $w$、增大 $b$、增大上一层激活值，都会让代价下降**。公式算出来的数和「真的微调一下」算出来的数在小数点后六位全部吻合，这种「用数值微调核对解析公式」的做法就叫**梯度检验**，后面会用它来验证更大的网络。注意 $\partial C_0/\partial b$ 恰好是 $\partial C_0/\partial w$ 的 $1/a^{(L-1)}=2$ 倍：$-0.177447=2\times(-0.088723)$，因为这里 $a^{(L-1)}=0.5$，两个梯度只差第一个因子。
"""),
  V("tIeHLnjs5U8", "视频四：Backpropagation calculus（深度学习第 4 集）", 10),
  T(r"""
这一集把上面的推导走一遍，并推广到每层有多个神经元的情形。听的时候抓住两点：一是「往前传」的那一项 $\partial C_0/\partial a^{(L-1)}$ 会成为下一轮推导的起点，所以同一个公式可以**一层一层往前套**；二是上一层神经元要对**所有**下一层神经元求和。

### 多个神经元：矩阵形式的反向传播

> **标准定义 · 误差项与反向传播公式 (error term δ & backpropagation equations)**
>
> 定义第 $l$ 层的**误差项 (error term)** $\boldsymbol{\delta}^{(l)}=\dfrac{\partial C}{\partial\mathbf{z}^{(l)}}$。对 $\mathbf{z}^{(l)}=W^{(l)}\mathbf{a}^{(l-1)}+\mathbf{b}^{(l)}$，$\mathbf{a}^{(l)}=\sigma(\mathbf{z}^{(l)})$，有：
>
> $$\boldsymbol{\delta}^{(l)}=\dfrac{\partial C}{\partial\mathbf{a}^{(l)}}\odot\sigma'\big(\mathbf{z}^{(l)}\big),\quad\dfrac{\partial C}{\partial W^{(l)}}=\boldsymbol{\delta}^{(l)}\big(\mathbf{a}^{(l-1)}\big)^{\top},\quad\dfrac{\partial C}{\partial\mathbf{b}^{(l)}}=\boldsymbol{\delta}^{(l)},\quad\dfrac{\partial C}{\partial\mathbf{a}^{(l-1)}}=\big(W^{(l)}\big)^{\top}\boldsymbol{\delta}^{(l)}$$
>
> 其中 $\odot$ 表示逐元素相乘。最后一个式子把梯度传到前一层，是对所有路径求和的矩阵写法：$\dfrac{\partial C}{\partial a^{(l-1)}_k}=\sum_j W^{(l)}_{jk}\,\delta^{(l)}_j$。
>
> *English: Define the error term δ = ∂C/∂z at each layer. Then δ = (∂C/∂a) ⊙ σ'(z), ∂C/∂W = δ aᵀ_prev, ∂C/∂b = δ, and the gradient passed to the previous layer is ∂C/∂a_prev = Wᵀ δ, a sum over all paths written as a matrix product.*

**白话版：「每层收一次账，再把账单寄回上一层」。** 每一层做四件事：①拿到从后面寄来的「对我的输出的要求」$\partial C/\partial\mathbf{a}$；②乘上本层激活函数的斜率，得到「对我的加权输入的要求」$\boldsymbol\delta$；③这份 $\boldsymbol\delta$ 乘上上一层的激活值，就是我自己权重的梯度（上一层越亮，梯度越大）；④把 $W^\top\boldsymbol\delta$ 寄给上一层。**乘 $W^\top$ 就是「对所有路径求和」**：上一层第 $k$ 个神经元的账单，是它通向每个下一层神经元的权重，乘以那个神经元的 $\delta$，再全部加起来。注意形状：$\boldsymbol\delta$ 是长度为 $m$ 的向量，$\mathbf{a}^{(l-1)}$ 是长度为 $n$ 的向量，外积 $\boldsymbol\delta\,\mathbf{a}^\top$ 恰好是 $m\times n$，和 $W$ 的形状完全相同，这就是为什么 PyTorch 里 `weight.grad` 的形状总是和 `weight` 一样。

下面用 NumPy 把这四步写成代码：一个 3→4→2 的小网络（共 26 个参数），反向传播算出全部梯度，再用梯度检验证明没写错。

""" + C_BACK + r"""

读输出：梯度的形状 `(4, 3)`、`(2, 4)` 和权重一样，`(4,)`、`(2,)` 和偏置一样。梯度检验里数值方法对 26 个参数各做「加 $h$、减 $h$」，共 52 次前向传播，得到的偏导数与反向传播的结果最大只差 $1.1\times10^{-10}$，这已经是浮点误差的量级，说明公式和代码都对。**以后你自己写任何求导代码，都应该先做这个检验**：它简单、可靠，是排查「训练不收敛到底是不是梯度写错了」的第一步。反向传播本身只用了 1 次前向 + 1 次反向。

### 为什么这样算这么省

**关键在于复用。** 看上面代码的循环：每一层的 `dC_da` 是上一轮（更靠后的那一层）算好的，直接拿来乘；没有任何一个偏导数是从头重新追溯一遍所有路径得到的。如果不复用，一个靠前的参数要把通向输出的所有路径逐条展开，路径数会随层数**指数增长**。把共同的部分提出来、存下来，就把指数爆炸变成了**线性**的工作量。这是一个典型的**动态规划 (dynamic programming)** 思想：「先算后面，后面的结果被前面反复使用」。

**为什么是从后往前？** 我们关心的是**一个数**（代价）对**非常多的参数**的偏导数。从后往前走，每一步传的是「代价对这一层的导数」，一趟就能同时得到所有参数的梯度；从前往后走，每一趟只能得到「某一个输入的变化对后面所有量的影响」，要对每个参数各走一趟。**输出只有一个、输入很多时，反向最省**，这在数学上叫**反向模式自动微分 (reverse-mode automatic differentiation)**。

**代价是内存。** 反向传播要用到前向时算出的每层 $\mathbf{a}$ 和 $\mathbf{z}$（上面代码里 `a_list`、`z_list` 存着），所以训练时必须把这些中间量都存下来；推理时用完就可以丢。这就是训练比推理更占显存的根本原因，也是「梯度检查点 (gradient checkpointing)」这类技巧要解决的问题：用重算换内存。

PyTorch 的 **自动求导 (autograd)** 做的正是这件事：前向时它**记录**每一步运算，形成**计算图 (computational graph)**；你调用 `.backward()`，它就沿着这张图反向应用链式法则，每种运算（矩阵乘法、加法、`sigmoid`……）都预先写好了自己的局部导数。你不用再手写 `backward` 函数，但出了问题时，需要知道里面发生了什么。

### 小批量：真实训练是怎么用梯度的

**代价是所有训练样本的平均**，所以真正的梯度也是所有样本梯度的平均。但每走一步都遍历几十万个样本太贵，于是实际做法是**小批量随机梯度下降**：

> **标准定义 · 小批量随机梯度下降 (mini-batch SGD)**
>
> 把训练集随机打乱，切成大小为 $B$ 的**小批量 (mini-batch)**。每一步用一个小批量上的平均梯度 $\hat g=\dfrac1B\sum_{i\in\text{batch}}\nabla C_i(\theta)$ 更新参数：$\theta\leftarrow\theta-\eta\,\hat g$。$\hat g$ 是真实梯度的**无偏估计 (unbiased estimator)**，但带噪声。把所有小批量用完一遍称为一个 **epoch**。
>
> *English: Shuffle the training set and split it into mini-batches of size B. Each step updates θ ← θ − η·ĝ, where ĝ is the average gradient over one mini-batch. ĝ is an unbiased but noisy estimate of the full gradient. One pass over all mini-batches is an epoch.*

**白话版：「醉汉下山」。** 每一步都精打细算（用全部数据）的人下山很慢；每一步只看一眼周围、方向大致对的醉汉，虽然走得歪歪扭扭，但每一步便宜得多，所以同样的时间里走得更远。下面的实验让网络学会分辨「圆内」和「圆外」的点（一条直线分不开，需要非线性），同样训练 100 个 epoch、同样的学习率，只改批量大小；上面的反向传播代码被改写成了**批量版**，一次处理一整批样本：

""" + C_BATCH + r"""

读输出：第一行证明批量版没有写错：**一批样本的梯度，就等于逐个样本梯度的平均**。训练前随机网络的准确率是 0.405（比抛硬币还差）。然后：全批量（600 个样本一批）一个 epoch 只走 1 步，100 个 epoch 共 100 步，准确率仅 0.595，代价还有 0.2408；批量 50 走了 1200 步，准确率 0.853；批量 10 走了 6000 步，准确率 0.958，代价降到 0.0405。**每一步更便宜、总共走更多步，在固定的 epoch 数下收敛得更快。** 要诚实地说一句：批量越小每步越「噪」，也并不是越小越好，实际中批量大小是需要调的超参数，更小的批量也不能利用 GPU 的并行能力；这个小实验只想说明「用一小批估计梯度」不是偷工减料，而是用噪声换速度。
"""),
  T(r"""
### 梯度消失：为什么深网络难训练

反向传播每经过一层，就要乘一次激活函数的导数（并乘一次 $W^\top$）。如果每次乘的数都小于 1，连乘之后就会越来越小，前面的层几乎收不到梯度。

> **标准定义 · 梯度消失 (vanishing gradient)**
>
> 在反向传播中，靠近输入的层的梯度 $\boldsymbol\delta^{(l)}$ 是一长串因子 $\sigma'(\mathbf{z})$ 和 $W^\top$ 的连乘。若这些因子的尺度普遍小于 1，$\boldsymbol\delta^{(l)}$ 会随着深度**指数衰减**，前面的层几乎不更新，称为梯度消失；反之若因子普遍大于 1，则**梯度爆炸 (exploding gradient)**。Sigmoid 的导数 $\sigma'(z)=\sigma(z)(1-\sigma(z))\le0.25$，是梯度消失的典型原因。
>
> *English: Backpropagated errors are products of many factors σ'(z) and Wᵀ. If these are typically below 1, early layers receive exponentially small gradients (vanishing gradients); if above 1, gradients explode. Sigmoid's derivative is at most 0.25, a classic cause.*

**白话版：「传话传了十层，最后一个人几乎什么都没听见」。** 下面搭一个 10 层、每层 50 个神经元的网络，权重用标准的 $1/\sqrt{n}$ 尺度随机初始化，从最后一层给一个固定的「要求」，看每一层收到的 $\boldsymbol\delta$ 有多大：

""" + C_VANISH + r"""

读输出：Sigmoid 网络里，第 10 层的 $\delta$ 的大小是 $1.7$，到第 1 层只剩 $3.2\times10^{-6}$，**第 1 层与第 10 层的比值只有 $1.9\times10^{-6}$**，和 $0.25^{10}=9.5\times10^{-7}$ 同一量级（0.25 是 Sigmoid 导数的最大值，实际每层的因子还要更小一点点）。前面几层几乎学不动。ReLU 网络里，同样的比值是 0.11：并不是完全没有衰减（这里的权重只是随便初始化的），但**比 Sigmoid 好了约 6 万倍（0.11 对 $1.9\times10^{-6}$）**，因为 ReLU 在正区间的导数恒为 1，不再每层「打折」。后来的残差连接 (residual connection)、归一化 (normalization) 层、更好的初始化方法，都是在不同方向上解决「让梯度顺利传回前面」这个问题，Transformer 的结构就大量依赖它们。

### 用反向传播把 XOR 学会

回到上一节的 XOR 实验。那时我们用「微调」的笨办法算梯度，因为只有 9 个参数；现在用刚学的反向传播，代码只有几行，同样的网络（2→2→1，隐藏层用 Sigmoid）：

""" + C_XORBP + r"""

读输出：种子 0 的网络学会了 XOR：四个输出是 0.02、0.98、0.98、0.02，代价 0.0003，和上一节「微调」得到的结果一致，**只是算梯度快了很多**。10 个随机种子里，有 8 个把代价压到了 0，有 2 个（种子 5 和种子 6）卡在了 0.168 和 0.125，这又一次说明：**梯度下降的结果依赖初始参数，并不保证找到全局最优**。这也是为什么大模型训练里，初始化和学习率都需要仔细设置。

### 这一节你要带走的三句话

1. **反向传播 = 链式法则 + 从后往前复用中间结果**：一次前向（并存下所有中间量）加一次反向，就能得到全部参数的梯度，比逐个微调快了参数个数量级倍。
2. **每层的四步**：$\boldsymbol\delta=\dfrac{\partial C}{\partial\mathbf{a}}\odot\sigma'(\mathbf{z})$；$\dfrac{\partial C}{\partial W}=\boldsymbol\delta\,\mathbf{a}_{\text{prev}}^\top$；$\dfrac{\partial C}{\partial\mathbf{b}}=\boldsymbol\delta$；把 $W^\top\boldsymbol\delta$ 传给前一层（对所有路径求和）。写完一定做**梯度检验**。
3. **真实训练用小批量估计梯度；梯度在深网络里会一层层变小**（Sigmoid 最典型），这是 ReLU、残差连接、归一化存在的理由。自动求导做的就是这套东西，你不用手写，但要看得懂。
"""),
  THINK("**计算题**：单神经元链里，取 $a^{(L-1)}=1$、$w=1$、$b=0$、正确答案 $y=0$，激活函数是 Sigmoid。求 $\\partial C_0/\\partial w$ 和 $\\partial C_0/\\partial b$。（可以对照上面的链式公式，先自己算再看答案）", r"""
前向：$z=wa^{(L-1)}+b=1$，$a=\sigma(1)\approx0.7311$。

三个因子：$\partial z/\partial w=a^{(L-1)}=1$；$\sigma'(z)=a(1-a)\approx0.7311\times0.2689\approx0.1966$；$\partial C_0/\partial a=2(a-y)=2\times0.7311=1.4622$。

所以

$$\frac{\partial C_0}{\partial w}=1\times0.1966\times1.4622\approx0.2875$$

偏置的第一个因子是 1，所以 $\partial C_0/\partial b=0.1966\times1.4622\approx0.2875$，**这里恰好和 $\partial C_0/\partial w$ 相等，因为 $a^{(L-1)}=1$**。两个导数都是正的：增大 $w$ 或 $b$ 会让输出更大、离正确答案 0 更远，所以梯度下降会把它们**减小**。可以用 `np` 写几行中心差分验证，结果是 0.28747。
"""),
  THINK("**概念辨析**：有人说「反向传播是一种学习算法，和梯度下降是两种方法，二选一」。这句话错在哪里？", r"""
错在把两个不同层次的东西当成了并列的选择。

- **反向传播**只负责一件事：**计算梯度**，即把 $\nabla C$ 高效地算出来。它本身不改任何参数。
- **梯度下降（及 SGD、Adam 等优化器）**负责**使用**梯度：拿到 $\nabla C$ 之后怎么更新参数。

训练循环里它们是前后相继的两步：`loss.backward()`（反向传播，填好每个参数的 `.grad`）→ `optimizer.step()`（用 `.grad` 更新参数）。你可以不用反向传播，用「逐个微调」的数值梯度配合梯度下降，只是慢到不可用；也可以用反向传播算出的梯度配合不同的优化器。反过来，反向传播也不只用于神经网络，任何由可导运算组成的函数都能用它求梯度。
"""),
  THINK("**联系后续内容**：训练一个 Transformer 时，显存往往主要被「激活值」占用，而不只是参数。结合反向传播的流程解释为什么，以及「梯度检查点」怎样用时间换显存？", r"""
反向传播里，每一层的 $\boldsymbol\delta$ 和 $\partial C/\partial W$ 都要用到**前向时的激活值**：$\partial C/\partial W=\boldsymbol\delta\,\mathbf{a}_{\text{prev}}^\top$ 需要上一层的 $\mathbf{a}$，$\sigma'(\mathbf{z})$ 需要这一层的 $\mathbf{z}$。所以前向传播时每层的中间结果都得**存着**，直到反向用掉。层数越多、批量越大、序列越长，要存的东西就越多，这部分内存和批量大小成正比，常常比参数本身还大。推理时没有反向，用完就可以丢，所以便宜得多。

**梯度检查点 (gradient checkpointing)** 的做法：前向时只存一部分层的激活值（「检查点」），其余的丢掉；反向传播走到某一段时，从最近的检查点**重新做一遍这一段的前向**，把需要的激活值临时算回来。代价是多做大约一次额外的前向传播（约多出 30% 的计算），换来激活值内存的大幅下降。第 11 节学 PyTorch 时会看到相关的接口。
"""),
  KW(("反向传播","backpropagation","一次反向计算得到所有参数的梯度"),
     ("链式法则","chain rule","复合函数的导数 = 各段导数相乘，多条路径则相加"),
     ("偏导数","partial derivative","只动一个变量时函数的变化率"),
     ("数值梯度 / 梯度检验","numerical gradient / gradient checking","用微调近似偏导数，用来核对解析梯度"),
     ("加权输入","weighted input $z$","$z=wa+b$，进激活函数之前的值"),
     ("误差项","error term $\\delta$","$\\delta=\\partial C/\\partial z$，每层往前传的量"),
     ("逐元素乘法","Hadamard product $\\odot$","对应位置相乘，形状不变"),
     ("动态规划","dynamic programming","存下并复用中间结果，避免重复计算"),
     ("反向模式自动微分","reverse-mode autodiff","一个输出对很多输入求导时的最优方向"),
     ("计算图","computational graph","记录前向每一步运算的图，反向沿它求导"),
     ("自动求导","autograd","PyTorch 自动做反向传播的机制"),
     ("小批量","mini-batch","每一步只用一小部分训练数据"),
     ("随机梯度下降","stochastic gradient descent (SGD)","用小批量估计梯度的梯度下降"),
     ("epoch","epoch","把训练集完整过一遍"),
     ("梯度消失 / 爆炸","vanishing / exploding gradient","梯度随深度指数变小 / 变大"),
  ),
 ],
 "references": [
  {"title": "ARENA [0.0] Prerequisites — Neural Networks 部分", "url": "https://github.com/ARENA-education/ARENA_materials/blob/main/chapter0_fundamentals/instructions/pages/00_%5B0.0%5D_Prerequisites.md", "note": "3B1B 第 3 集为 ARENA 推荐内容；讲解为自写，未转载原文"},
  {"title": "3Blue1Brown：Neural Networks 系列（含文字版讲义）", "url": "https://www.3blue1brown.com/topics/neural-networks", "note": "可对照第 3、4 集的文字版"},
  {"title": "Michael Nielsen：Neural Networks and Deep Learning 第 2 章", "url": "http://neuralnetworksanddeeplearning.com/chap2.html", "note": "反向传播四个基本方程的完整推导（ARENA 选读），本节的 δ 写法与它一致"},
  {"title": "Stanford CS231n：Backpropagation, Intuitions", "url": "https://cs231n.github.io/optimization-2/", "note": "用计算图讲反向传播，局部梯度 × 上游梯度，适合接着理解 autograd"},
  {"title": "PyTorch 文档：Autograd mechanics", "url": "https://pytorch.org/docs/stable/notes/autograd.html", "note": "自动求导如何记录计算图、什么时候保存中间量"},
 ],
 "quiz": {"questions": QUIZ},
}

if __name__ == '__main__':
    dump(unit, "arena-0.0", "u02-backpropagation.json")
