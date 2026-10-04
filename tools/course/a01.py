"""ARENA 0.0 第 1 节：神经网络是什么（按 v3 格式重写，2026-10-04）"""
from unitlib import *
from a01c import C_NEURON, C_LAYER, C_COLLAPSE, C_LOSS, C_GD, C_XOR
from a01_quiz import QUIZ

unit = {
 "id": "u01",
 "title": "神经网络是什么",
 "en": "Neural Networks",
 "minutes": 85,
 "objectives": [
  "说清楚一个 **神经元 (neuron)** 里装的是什么，它的值是怎么由 **权重 (weight)**、**偏置 (bias)**、**激活函数 (activation function)** 算出来的",
  "会把一层网络写成矩阵形式 $\\mathbf{a}' = \\sigma(W\\mathbf{a} + \\mathbf{b})$，算出每个矩阵的 **形状 (shape)** 和 **参数 (parameter)** 个数，能用 NumPy 写出 **前向传播 (forward pass)**",
  "理解为什么必须有 **非线性 (nonlinearity)**：没有激活函数，多少层都等价于一层",
  "理解 **代价函数 (cost / loss function)** 与 **梯度下降 (gradient descent)** 怎样让网络「学习」，知道 **学习率 (learning rate)** 过大过小各会怎样",
  "知道「网络表现好」不等于「我们知道它在做什么」，这正是 ARENA 后面 **可解释性 (interpretability)** 要研究的问题",
 ],
 "blocks": [
  T(r"""
### 先说这一节要干什么

ARENA 后面的所有内容——Transformer、可解释性 (interpretability)、强化学习 (reinforcement learning)——都建立在神经网络之上。ARENA 的前置清单里，这一项被标为**最高优先级**，推荐的正是 3Blue1Brown 的神经网络系列前两集。

这一节要建立两个直觉：**神经网络到底是什么**（一堆矩阵乘法加一点非线性），以及**它怎么「学」**（把一个衡量「有多差」的数字，沿着梯度一步步变小）。除了看视频，我们会用 NumPy 把每一步真的写出来、跑出来：形状、参数个数、前向传播、梯度下降，后面每一节都会反复用到。

**学完它你就能看懂这几件事：**

- Transformer 里每个「MLP 层」就是这一节的「线性变换 + 激活函数」；`nn.Linear(784, 16)` 里的权重形状为什么是 `(16, 784)`；
- 一个模型「有多少参数」是怎么数出来的（7B、70B 模型的 B 指的就是它）；
- 训练循环里 `loss.backward()`、`optimizer.step()` 在做什么：前者算梯度（下一节），后者就是这一节的梯度下降；
- 为什么说「看起来表现很好的网络，我们未必知道它在做什么」。

**本节安排（约 85 分钟）**：导读与神经元（10 分钟）→ 视频一（19 分钟）→ 矩阵形式、参数个数与前向传播（15 分钟）→ 为什么需要非线性（5 分钟）→ 代价函数（8 分钟）→ 视频二（21 分钟）→ 梯度下降与动手实验（12 分钟）→「想一想」。视频是英文的，可以打开 YouTube 的中文字幕。

### 神经元与层

视频用的例子是**识别手写数字**：输入一张 28×28 像素的灰度图片，输出它是 0–9 中的哪个数字（这个经典数据集叫 **MNIST**）。

> **标准定义 · 神经元与前馈神经网络 (neuron & feedforward neural network)**
>
> 一个**神经元 (neuron)** 是一个把若干输入映射为一个数的函数：对输入 $a_1,\dots,a_n$ 做**加权和**再加上**偏置**，得到 $z=\sum_k w_k a_k + b$，然后经过一个**激活函数** $\sigma$，输出 **激活值 (activation)** $a=\sigma(z)$。神经元按**层 (layer)** 排列：**输入层**接收数据，**输出层**给出结果，中间的是**隐藏层 (hidden layer)**。在**前馈网络**里，每一层的激活值只由上一层的激活值算出，信息从输入一路流向输出，没有回路。全部的权重和偏置合称网络的**参数 (parameters)**。
>
> *English: A neuron computes a weighted sum of its inputs plus a bias, z = Σ w·a + b, and passes it through an activation function σ to produce its activation a = σ(z). Neurons are arranged in layers (input, hidden, output); in a feedforward network each layer's activations depend only on the previous layer. All weights and biases together are the network's parameters.*

**白话版：「一个会打分的小评委」。** 每个神经元是一个评委：他看上一层所有人给的分（激活值），**对不同的人信任程度不同**（权重大 = 很看重，权重为负 = 反着看），加上自己的**起评门槛**（偏置），最后用一个函数把总分「整理」成 0 到 1 之间的一个数。整个网络就是一排排评委：一层评委的打分，是下一层评委的输入。

视频里的网络：输入层 784 个神经元（对应 28×28 = 784 个像素的亮度），两个隐藏层各 16 个，输出层 10 个（对应数字 0–9，哪个激活值最大，网络就认为图片是哪个数字）。整个网络就是一个「输入 784 个数、输出 10 个数」的函数。先看单个神经元怎么算：

""" + C_NEURON + r"""

读输出：加权和 $z=1.5\times0.2+(-2.0)\times0.9+0.5\times0.5-0.3=-1.55$，是负数，所以 Sigmoid 给出很小的 0.175（几乎没亮），ReLU 直接截成 0。第二个输入的负权重 $-2.0$ 就是「抑制」：它的激活值越大，越把总分往下拉。下面三行展示了两种激活函数的形状：**Sigmoid 把任意实数压进 (0, 1)**（$x=\pm10$ 时已经几乎是 0 和 1，曲线非常平）；**ReLU 把负数截成 0、正数原样通过**。
"""),
  V("aircAruvnKk", "视频一：But what is a neural network?（深度学习第 1 集）", 19),
  T(r"""
### 矩阵形式、参数个数与前向传播

视频的核心是：一整层神经元的计算，合起来就是一次**矩阵乘法**。

> **标准定义 · 全连接层与前向传播 (fully connected layer & forward pass)**
>
> 设上一层有 $n$ 个神经元、这一层有 $m$ 个。**全连接层 (fully connected / linear layer)** 由一个**权重矩阵** $W\in\mathbb{R}^{m\times n}$ 和一个**偏置向量** $\mathbf{b}\in\mathbb{R}^{m}$ 组成，计算 $\mathbf{a}'=\sigma(W\mathbf{a}+\mathbf{b})$：$W$ 的第 $j$ 行就是第 $j$ 个神经元的权重。这一层有 $mn+m$ 个参数。把各层依次应用，从输入算出输出，称为**前向传播 (forward pass)**。
>
> *English: A fully connected layer with n inputs and m outputs has a weight matrix W of shape m×n and a bias vector b of length m, computing a' = σ(Wa + b); it has mn + m parameters. Applying the layers in turn from input to output is the forward pass.*

**白话版：「一次算完所有评委」。** 单个神经元是「一行权重 × 上一层的向量」；一层的 16 个神经元，就是把 16 行权重叠成一个 $16\times784$ 的矩阵，一次乘出 16 个加权和。**形状的记法：`W` 的行数 = 这一层的神经元数，列数 = 上一层的神经元数。** 记不住就按「维度要对得上」推：要把 784 维变成 16 维，$W$ 只能是 $16\times784$。

""" + C_LAYER + r"""

要点：**一**，三层的参数个数是 12,560、272、170，总共 **13,002**（权重 12,960 + 偏置 42），与视频里的数字一致；一层的参数个数 = $mn+m$，要会心算。**二**，前向传播就是一个循环：「乘 $W$、加 $b$、过激活函数」。参数是随机的，所以输出毫无意义，**训练的目的就是把它们调好**。**三**，**批量计算**：真实训练一次处理一批图片，把输入从向量变成矩阵（`32 × 784`），同一个循环就算出 `32 × 10` 的输出。这时要写成 `x @ W.T + b`，因为 batch 在**第一个维度**。**PyTorch 的 `nn.Linear(784, 16)` 就是这样存的：`weight` 的形状是 `(16, 784)`，计算 `x @ weight.T + bias`。** 这也解释了为什么下一阶段要学线性代数：神经网络的计算，大部分就是矩阵乘法。

### 为什么必须有激活函数

> **标准定义 · 非线性 (nonlinearity)**
>
> 函数 $f$ 是**线性的**，如果 $f(\mathbf{x}+\mathbf{y})=f(\mathbf{x})+f(\mathbf{y})$ 且 $f(c\mathbf{x})=cf(\mathbf{x})$（带偏置的 $W\mathbf{x}+\mathbf{b}$ 严格说是**仿射 (affine)** 的，性质相同）。**线性（仿射）函数的复合仍然是线性（仿射）的**。激活函数是**非线性**的（如 Sigmoid、ReLU），才使得多层网络能表达线性函数表达不了的东西。
>
> *English: A composition of linear (affine) maps is again linear (affine). Non-linear activation functions are what let deep networks represent functions that a single linear map cannot.*

**白话版：「叠再多层直线，也只是一条直线」。** 如果不加激活函数，网络的每一层只是在做拉伸、旋转，叠十层和叠一层没有区别。**非线性，才是「深」的意义。**

""" + C_COLLAPSE + r"""

三层、13,002 个参数的「线性网络」，可以被**精确地**压缩成一个 $10\times784$ 的矩阵加一个偏置（7,850 个参数）：算出的结果完全相同（`allclose` 为 `True`）。这一点，后面 XOR 的实验里会看到它的后果。

### 代价函数：先得有个打分标准

> **标准定义 · 代价函数 / 损失函数 (cost function / loss function)**
>
> 衡量网络输出与正确答案**差多远**的一个**数**，越小越好。分类时正确答案常写成**独热向量 (one-hot vector)** $\mathbf{y}$（正确类别的位置为 1，其余为 0）。视频用的是**平方误差**：对一个样本 $C=\sum_{j}(a^{(L)}_j-y_j)^2$；对所有训练样本取平均，得到整个训练集的代价。**对固定的训练数据，代价是网络参数的函数**。
>
> *English: A cost (loss) function measures how far the network's output is from the correct answer: smaller is better. With a one-hot target y, the squared-error cost of one example is Σ (a_j − y_j)²; averaging over the training set gives the total cost, which, for fixed data, is a function of the parameters.*

**白话版：「模拟考的扣分」。** 每道题答错一点就扣一点，全部题目扣分的平均就是代价。关键的视角转换是：这个平均扣分，是**那 13,002 个参数的函数**；「学习」，就是在一个 13,002 维的空间里，找让它尽量小的点。

""" + C_LOSS + r"""

随机参数的网络，十个输出都在 0.5 左右，每一项的误差平方约 0.25，十项合起来约 2.5，所以平均代价 2.695。**训练的目标就是把它往 0 压**（完美输出的代价是 0；全部猜反的最大值是 9）。实际做分类时，更常用的是**交叉熵 (cross-entropy)** 代价（第 9 节信息论会讲），但「用一个数衡量差多少，再让它变小」的思路完全一样。
"""),
  V("IHZwWFHWa-w", "视频二：Gradient descent, how neural networks learn（深度学习第 2 集）", 21),
  T(r"""
### 梯度下降

> **标准定义 · 梯度下降 (gradient descent)**
>
> **梯度 (gradient)** $\nabla C$ 是代价 $C$ 对每个参数的**偏导数 (partial derivative)** 组成的向量，指向 $C$ **增加最快**的方向。**梯度下降**反复把参数沿**负梯度**方向移动一小步：$\theta\leftarrow\theta-\eta\,\nabla C(\theta)$，其中 $\eta>0$ 是**学习率 (learning rate)**，控制每一步走多远。它能找到一个**局部最小值 (local minimum)**，但不保证是全局最小值。
>
> *English: The gradient ∇C points in the direction of steepest increase of the cost. Gradient descent repeatedly updates θ ← θ − η∇C(θ), with learning rate η; it finds a local minimum, not necessarily the global one.*

**白话版：「在大雾里下山」。** 你站在山坡上，看不见山谷，只能感觉脚下哪个方向坡最陡（梯度的反方向），就朝那个方向迈一小步，再感觉、再迈。步子（学习率）太小，下得太慢；太大，可能一步跨过山谷到对面的山坡上，来回震荡，甚至越走越高。

先用最简单的「山」：$C(\theta)=(\theta-3)^2$，最低点在 $\theta=3$，梯度 $2(\theta-3)$。同一座山，换五种学习率：

""" + C_GD + r"""

读结果：**$\eta=0.01$** 太小：20 步后还停在 $-2.34$，离 3 差得远；**$\eta=0.1$** 合适：20 步后到了 2.91；**$\eta=0.5$** 在这座特殊的山上一步就跳到最低点（只是因为这个函数恰好是二次函数，别当成普遍规律）；**$\eta=0.95$** 太大：在 3 的两边来回「弹」（第 5 步在 7.72，第 20 步又回到 2.03），虽然这座山上还勉强在收敛，但已经很不稳；**$\eta=1.05$** 越过了临界值：每一步都冲得更远，20 步后到了 $-50.82$，**发散**。真实网络里没有这么干净的临界值，所以学习率是训练中最重要的超参数之一。

**那 13,002 个偏导数具体怎么算？** 对每个参数各自「微调一下看代价变化多少」太慢（要做 13,002 次前向传播）。**反向传播 (backpropagation)** 能一次性把全部偏导数高效地算出来，这就是下一节的内容。下面的实验故意用「微调」的笨办法，只因为网络只有 9 个参数，让你先不依赖反向传播，亲眼看到「学习」发生：

**实验：让网络学会 XOR（异或）。** 四个输入点 $(0,0),(0,1),(1,0),(1,1)$ 的正确输出是 $0,1,1,0$。这四个点**不可能用一条直线分开**，所以线性模型做不到。用一个 2→2→1 的小网络（9 个参数），分别在「隐藏层有激活函数」和「隐藏层没有激活函数」两种情况下训练（输出层都用 Sigmoid，把输出压进 0 到 1），同时试 10 个不同的随机初始值：

""" + C_XOR + r"""

结论很清楚：**有 Sigmoid 的网络把四个点学会了**（输出 0.02、0.98、0.98、0.02，代价 0.0003）；**隐藏层去掉激活函数后，隐藏层本身可以压缩掉**（上面「压缩」的结论），整个网络只剩「一个线性函数再套一个 Sigmoid」（相当于逻辑回归），无论训练多久，最好也只能让四个输出都停在 0.5，代价卡在 0.25。这正是「非线性才是深的意义」的实验证据。另一个观察：10 个随机起点里，9 个学会了，**有 1 个（种子 6）卡在了 0.125**，说明梯度下降确实可能停在不够好的地方，**结果依赖于初始参数**。

**梯度下降的实用版本：** 真实的训练集有几十万甚至几十亿个样本，每走一步都用全部样本算梯度太贵。**随机梯度下降 (stochastic gradient descent, SGD)** 每次只用一小批 (mini-batch) 样本估计梯度，走一步；Adam 等优化器是在它的基础上加了「动量」和「每个参数自己的学习率」。你在 PyTorch 里写的 `optimizer.step()`，做的就是 $\theta\leftarrow\theta-\eta\,\nabla C$ 这一类更新。

### 网络真的学到了「笔画」吗？

训练后的网络在没见过的测试图片上能达到约 96% 的准确率。但视频后半段把隐藏层的权重画出来一看：它们**并不像**我们期待的「笔画」「圆圈」，更像一团杂乱的图案；给网络喂一张随机噪声图，它也会很自信地给出一个数字。

**网络表现好，不代表它是按我们以为的方式在工作**，弄清楚网络内部到底在做什么，正是 ARENA 后面 **机制可解释性 (mechanistic interpretability)** 要研究的核心问题。

### 这一节你要带走的三句话

1. **神经网络 = 一层层「矩阵乘法 + 偏置 + 激活函数」**；形状记法是 `W: (这一层神经元数, 上一层神经元数)`，一层有 $mn+m$ 个参数，视频里的网络共 13,002 个。
2. **没有非线性，叠多少层都等价于一层**（可以压缩成一个矩阵）；XOR 实验里没有激活函数的网络永远学不会。
3. **学习 = 定义一个衡量「差多少」的代价，再沿负梯度一步步让它变小**；学习率太小学得慢、太大会震荡发散；梯度怎么高效算出来，是下一节的反向传播。
"""),
  THINK("为什么神经网络能表达的函数，比 **线性回归 (linear regression)** 丰富得多？", r"""
两个关键原因：

1. **非线性 (nonlinearity)**：每一层之后都有激活函数（Sigmoid / ReLU），让网络能表达弯曲、复杂的函数；线性回归只能表达直线 / 平面这类线性关系。上面 XOR 的实验就是一个具体的证据：线性模型怎么训练都卡在 0.25。
2. **参数是学出来的**：网络的参数靠梯度下降从数据里自动找，而不是人手工设计规则，所以它的能力不受「人能想出多聪明的算法」的限制。

（还有一个定理级别的事实：**万能近似定理 (universal approximation theorem)** 说，只要隐藏层足够宽、激活函数合适，一个隐藏层的网络就可以任意逼近很大一类连续函数。但它只说「存在」这样的参数，不保证梯度下降能找到，更不说需要多少神经元。）
"""),
  THINK("如果把 784 → 16 → 16 → 10 这个网络里所有的激活函数都去掉，它会变成什么？它还剩多少「有效」的参数？", r"""
会退化成**一个线性变换**：

$$W_3(W_2(W_1\mathbf{a} + \mathbf{b}_1) + \mathbf{b}_2) + \mathbf{b}_3 = W'\mathbf{a} + \mathbf{b}'$$

其中 $W' = W_3W_2W_1$ 是一个 10 × 784 的矩阵，$\mathbf{b}'=W_3(W_2\mathbf{b}_1+\mathbf{b}_2)+\mathbf{b}_3$。**多个线性变换组合起来仍然是线性的**，叠再多层也只相当于一层。

「有效」参数：这个线性网络的全部能力，只需要 $10\times784+10=7{,}850$ 个数就能描述（上面的代码验证过），而原来有 13,002 个参数，**多出来的 5,152 个是冗余的**。激活函数带来的非线性，才是「深」的意义所在。第 3 节学线性变换时会再遇到这个结论。
"""),
  THINK("现代网络为什么更喜欢 **ReLU**，而不是 Sigmoid？", r"""
- **缓解梯度消失 (vanishing gradient)**：Sigmoid 在输入很大或很小时几乎是平的（上面代码里 $x=\pm10$ 时输出已是 0 和 1），导数接近 0；很多层连乘之后梯度会变得极小，前面的层几乎学不动。ReLU 在正区间的导数恒为 1，不存在这个问题。
- **计算更便宜**：$\max(0, x)$ 比指数运算简单得多。

ARENA 在这里还特别提醒：机器学习里经常是**先在实验中发现某个做法效果更好，之后才找到理论解释**，ReLU 就是一个例子。ReLU 也有缺点：输入为负时导数为 0，神经元可能「死掉」，所以有 Leaky ReLU、GELU 等变种（Transformer 里常用 GELU）。
"""),
  KW(("神经元","neuron","装着一个数（激活值）的单元"),
     ("激活值","activation","神经元里的那个数 $a=\\sigma(z)$"),
     ("输入层 / 隐藏层 / 输出层","input / hidden / output layer","网络的三类层"),
     ("权重","weight","决定关注上一层的哪些神经元，可以为负"),
     ("偏置","bias","激活的门槛"),
     ("激活函数","activation function","引入非线性，如 Sigmoid、ReLU"),
     ("非线性","nonlinearity","没有它，多层网络等价于一层"),
     ("参数","parameters","所有权重 + 偏置，训练就是找参数；一层有 $mn+m$ 个"),
     ("前向传播","forward pass","一层层「乘 $W$、加 $b$、过激活函数」算出输出"),
     ("代价函数 / 损失函数","cost / loss function","衡量网络有多差，越小越好"),
     ("梯度","gradient","代价函数上升最快的方向"),
     ("梯度下降","gradient descent","沿负梯度一步步减小代价"),
     ("学习率","learning rate","每一步走多远；太小慢、太大发散"),
     ("局部最小值","local minimum","附近最低但不一定全局最低的点"),
     ("随机梯度下降","stochastic gradient descent (SGD)","每次用一小批样本估计梯度"),
  ),
 ],
 "references": [
  {"title": "ARENA [0.0] Prerequisites — Neural Networks 部分", "url": "https://github.com/ARENA-education/ARENA_materials/blob/main/chapter0_fundamentals/instructions/pages/00_%5B0.0%5D_Prerequisites.md", "note": "本节依据的原文大纲和思考题（讲解为自写，未转载原文）"},
  {"title": "3Blue1Brown：Neural Networks 系列（含文字版讲义）", "url": "https://www.3blue1brown.com/topics/neural-networks", "note": "两集视频的文字版，可以对照着读"},
  {"title": "预习下一节：Backpropagation, intuitively（第 3 集）", "url": "https://www.youtube.com/watch?v=Ilg3gGewQ5U", "note": "下一节的视频，梯度是怎么高效算出来的"},
  {"title": "PyTorch 文档：torch.nn.Linear", "url": "https://pytorch.org/docs/stable/generated/torch.nn.Linear.html", "note": "全连接层的官方说明，可以核对 `weight` 的形状是 (out_features, in_features)"},
 ],
 "quiz": {"questions": QUIZ},
}

if __name__ == '__main__':
    dump(unit, "arena-0.0", "u01-neural-networks.json")
