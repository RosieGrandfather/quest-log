"""ARENA 0.0 第 8 节：微积分（按 v3 格式重写，2026-10-04）"""
from unitlib import *
from a08c import C_NUM, C_CHAIN, C_GRAD, C_LOSS, C_EXP
from a08_quiz import QUIZ

unit = {
 "id": "u08",
 "title": "微积分：导数、链式法则与损失函数",
 "en": "Calculus for Machine Learning",
 "minutes": 95,
 "objectives": [
  "理解 **导数 (derivative)** 是变化率与切线斜率，记住深度学习最常用的几个导数，并会用 **数值微分 (numerical differentiation)** 检验自己的推导",
  "理解 **链式法则 (chain rule)** 和 **乘积法则 (product rule)**，说清为什么深层网络会出现 **梯度消失 (vanishing gradient)**",
  "理解 **偏导数 (partial derivative)**、**梯度 (gradient)** 和 **雅可比矩阵 (Jacobian)**，会用一阶 **泰勒展开 (Taylor expansion)** 解释梯度下降为什么有效、学习率太大为什么会失效",
  "会推导 **均方误差 (MSE)** 和 **二元交叉熵 (BCE)** 的导数，知道对 **logit** 求导为什么得到 $\\sigma(z)-y$",
  "会写 **梯度检验 (gradient check)**，并用手推的梯度从零训练一个逻辑回归",
 ],
 "blocks": [
  T(r"""
### 先说这一节要干什么

训练神经网络，说到底就是反复做一件事：算出损失对每个参数的**梯度**，沿负梯度走一小步。ARENA 的要求是**必须**理解求导和偏导，**最好**理解链式法则和泰勒级数等向量微积分的基础。这一节把这些东西讲透，而且每一条结论都用 NumPy 跑一遍，用数字验证。

**学完它你就能看懂这几件事：**

- `loss.backward()` 为什么能算出所有参数的梯度：它就是把链式法则沿着计算图从后往前乘一遍（下一阶段的 PyTorch 会用到）；
- 为什么层数很深的网络难训练：一连串小于 1 的导数相乘，梯度会缩到几乎为 0；
- 为什么语言模型和分类器的损失是交叉熵，而不是均方误差：对 logit 的梯度干净、有界；
- 怎样判断自己写的反向传播对不对：和数值微分对一下，这叫**梯度检验**，写 ARENA 的从零实现练习时非常有用。

**本节安排（约 95 分钟）**：导数与数值微分（15 分钟）→ 视频一（16 分钟）→ 链式法则、乘积法则与梯度消失（15 分钟）→ 视频二（11 分钟）→ 偏导数、梯度、泰勒展开（15 分钟）→ 损失函数的导数（13 分钟）→ 动手实验：手推梯度训练逻辑回归（10 分钟）→「想一想」。视频是英文的，可以打开 YouTube 的中文字幕。

### 导数：变化率

> **标准定义 · 导数 (derivative)**
>
> 函数 $f$ 在 $x$ 处的**导数**是差商的极限：$f'(x)=\lim_{h\to0}\dfrac{f(x+h)-f(x)}{h}$，几何上是曲线在 $x$ 处的**切线斜率**，也是 $f$ 在 $x$ 附近的**瞬时变化率**。当 $h$ 很小时，$f(x+h)\approx f(x)+f'(x)\,h$。
>
> *English: The derivative f'(x) is the limit of the difference quotient (f(x+h) − f(x))/h as h → 0: the slope of the tangent line, or the instantaneous rate of change. For small h, f(x+h) ≈ f(x) + f'(x)h.*

**白话版：「汽车的速度表」。** 位置是 $f$，速度表上的读数就是导数：此刻每多开一点点时间，位置大约多出多少。$f'(x)>0$ 表示「往右走会上升」，$f'(x)<0$ 表示「往右走会下降」，$f'(x)=0$ 是平的（可能是谷底，也可能是山顶）。

常用导数，务必背熟（尤其是后三个，神经网络里天天遇到）：

| 函数 | 导数 | 说明 |
|---|---|---|
| $x^n$ | $n x^{n-1}$ | 幂函数 |
| $e^x$ | $e^x$ | 导数是它自己 |
| $\ln x$ | $1/x$ | 交叉熵损失里到处是 $\log$ |
| $\sigma(x) = \frac{1}{1+e^{-x}}$ | $\sigma(x)\big(1 - \sigma(x)\big)$ | Sigmoid，最大值 0.25 |
| $\text{ReLU}(x) = \max(0, x)$ | $x > 0$ 时为 1，$x < 0$ 时为 0 | 在 0 点不可导，实践中取 0 |
| $\tanh x$ | $1 - \tanh^2 x$ | |

**怎么确认自己推的公式没错？** 不用翻答案：用定义里的「差商」直接量一下。下面的代码用**中心差分** $\frac{f(x+h)-f(x-h)}{2h}$ 当「裁判」，对比手推的公式。后半段还展示了一个很重要的现象：$h$ 不是越小越好。

""" + C_NUM + r"""

读输出：五个函数，手推的导数和数值微分在 6 位小数内完全一致（比如 $x^3$ 在 $x=2$ 处是 $3\times 2^2=12$；Sigmoid 在 0 处是 $0.5\times0.5=0.25$）。这就是「梯度检验」的雏形，后面会反复用。

后半段是单边差分 $\frac{f(x+h)-f(x)}{h}$ 的误差：$h$ 从 $10^{-1}$ 缩到 $10^{-3}$、$10^{-5}$，误差也跟着按比例缩小（0.141、0.00136、0.0000136），因为切线近似越来越准；误差在 $h=10^{-8}$ 附近最小（$6.60\times10^{-9}$），再往下缩反而回升，到 $10^{-11}$ 是 $3.26\times10^{-5}$，到 $10^{-14}$ 回到 $9.34\times10^{-3}$。原因是 $h$ 太小时，$f(x+h)$ 和 $f(x)$ 几乎相等，**两个几乎相等的浮点数相减**会丢掉大部分有效数字。所以数值微分里 $h$ 要取得适中（双精度下通常 $10^{-5}$ 到 $10^{-6}$ 用中心差分），而且**它只用来检验，不用来训练**：每个参数都要多算两次函数，太慢。训练要靠解析的导数，也就是反向传播。
"""),
  V("YG15m2VwSjA", "视频一：Visualizing the chain rule and product rule（微积分的本质 第 4 章）", 16),
  T(r"""
### 链式法则、乘积法则与梯度消失

视频用面积和「推动一串连锁变化」的画面讲了两条规则。先把它们写成严谨的形式：

> **标准定义 · 乘积法则与链式法则 (product rule & chain rule)**
>
> **加法法则** $(f+g)'=f'+g'$。**乘积法则** $(fg)'=f'g+fg'$。**链式法则**：对复合函数 $f(g(x))$，有
>
> $$\frac{d}{dx}f\big(g(x)\big)=f'\big(g(x)\big)\cdot g'(x)$$
>
> 写成莱布尼茨记号，若 $y=f(u)$、$u=g(x)$，则 $\dfrac{dy}{dx}=\dfrac{dy}{du}\cdot\dfrac{du}{dx}$。复合了 $L$ 层函数，导数就是 $L$ 个局部导数的**乘积**。
>
> *English: The product rule gives (fg)' = f'g + fg'. The chain rule gives (f∘g)'(x) = f'(g(x))·g'(x); for a composition of L functions the derivative is the product of the L local derivatives.*

**白话版：「齿轮传动比」。** 一串齿轮，第一个转一圈，第二个转 $g'$ 圈，第三个再把它乘上 $f'$ 圈：总传动比是各级传动比相乘。乘积法则则像长方形的面积：边长 $f$、$g$ 各变一点点，面积的变化来自两条细长条 $f'g$ 和 $fg'$（那个角上的小方块是更高阶的小量，可以忽略）。

先验证几个公式（手推和数值微分对一下），然后做一件重要的事：把 Sigmoid 一层层套起来，看链式法则「一路相乘」会发生什么。

""" + C_CHAIN + r"""

读输出：前三行，链式法则（$\cos(x^2)\cdot2x$、$e^{-x^2}\cdot(-2x)$）和乘积法则（$2x\sin x+x^2\cos x$）算出的值和数值微分完全一致（1.235266、-0.857677、1.276677）。第 4 行 $L=3$ 层嵌套的 Sigmoid，把三层的局部导数相乘得 0.012033，也和数值微分一致。

**最后一段是重点**：每过一层 Sigmoid，导数最多是 0.25，所以层数一多，乘积就迅速缩小：1 层是 0.235，5 层是 $6.08\times10^{-4}$，10 层是 $3.48\times10^{-7}$，20 层 $1.14\times10^{-13}$，50 层 $4.04\times10^{-33}$。**输入端的参数几乎收不到任何梯度信号**，这就是**梯度消失 (vanishing gradient)**。反过来，如果每层的局部导数都大于 1，乘积就会指数增长，叫**梯度爆炸 (exploding gradient)**。这也是 ReLU（正区间导数恒为 1）、残差连接、归一化层这些设计被发明的动机。

### 偏导数、梯度与雅可比矩阵

现实里的函数不止一个输入：一个网络有成千上万个参数。
"""),
  V("AXqhWeUEtQU", "视频二：Partial derivatives, introduction（Khan Academy）", 11),
  T(r"""
> **标准定义 · 偏导数与梯度 (partial derivative & gradient)**
>
> 对多元函数 $f(x_1,\dots,x_n)$，**偏导数** $\dfrac{\partial f}{\partial x_i}$ 是**只让 $x_i$ 变化、其余变量当作常数**时 $f$ 对 $x_i$ 的导数。把所有偏导数排成向量，得到**梯度**
>
> $$\nabla f=\Big(\frac{\partial f}{\partial x_1},\dots,\frac{\partial f}{\partial x_n}\Big)$$
>
> 梯度指向 $f$ **上升最快**的方向，它的长度是那个方向上的最大变化率。若输出也是向量 $\mathbf{y}=F(\mathbf{x})$，所有 $\partial y_i/\partial x_j$ 排成的矩阵叫**雅可比矩阵 (Jacobian)** $J$，其中 $J_{ij}=\partial y_i/\partial x_j$。
>
> *English: A partial derivative differentiates with respect to one variable while holding the others fixed. The gradient ∇f collects all partials and points in the direction of steepest ascent. For a vector-valued function, the matrix of all partials ∂y_i/∂x_j is the Jacobian.*

**白话版：「站在山坡上，脚下最陡的方向」。** 你站在一座山上（$f$ 是海拔，$x,y$ 是经纬度）。往东走一步海拔变多少是 $\partial f/\partial x$，往北走一步是 $\partial f/\partial y$。把这两个数拼起来，就是一个箭头，指向**上坡最陡的方向**；沿它的反方向走，就是最陡的下坡。梯度下降用的就是这个箭头。

**为什么沿负梯度走函数值就会下降？** 这是**一阶泰勒展开 (first-order Taylor expansion)** 的内容：

> **标准定义 · 一阶泰勒展开 (first-order Taylor expansion)**
>
> 在点 $\mathbf{x}$ 附近，用梯度做线性近似：$f(\mathbf{x}+\mathbf{h})\approx f(\mathbf{x})+\nabla f(\mathbf{x})\cdot\mathbf{h}$。误差是 $\mathbf{h}$ 的二阶小量（和 $\|\mathbf{h}\|^2$ 同阶）。取 $\mathbf{h}=-\eta\nabla f$，得 $f(\mathbf{x}-\eta\nabla f)\approx f(\mathbf{x})-\eta\|\nabla f\|^2$，只要 $\eta$ 足够小，函数值就会下降。
>
> *English: Near x, f(x+h) ≈ f(x) + ∇f(x)·h with error of order ‖h‖². Taking h = −η∇f gives a decrease of about η‖∇f‖², valid only for small η.*

**白话版：「近处的地图是平的」。** 站在原地看，脚下一小块地近似一个斜面；斜面上往下坡走，一定变低。但走得太远，地图就不准了（真实的地面会弯）。这就是学习率不能太大的数学原因。下面把这件事量出来：

""" + C_GRAD + r"""

读输出：

- 函数 $f(x,y)=x^2y+3y$ 在 $(2,1)$ 处，手推梯度 $(2xy,\ x^2+3)=(4,7)$，数值梯度也是 $(4,7)$。
- **泰勒近似的误差随步长缩小得很快**：$s=0.1$ 时误差 0.01418，$s=0.01$ 时误差 0.00014，步长缩小到十分之一，误差缩小到约百分之一，印证「误差是二阶小量」；而 $s=1.0$ 时，真实值 0.9490 与近似值 2.5279 差了 1.579，近似已经不可信。
- 沿 $-\nabla f$ 走时，函数值**确实下降**：$\eta=0.001$ 时真实变化 -0.0649，几乎等于一阶预言 -0.0650；但 $\eta$ 越大，真实下降和预言的差距越大（$\eta=0.3$ 时真实 -11.0040，预言 -19.5000）。对这个 $f$ 来说「还在下降」，对别的函数，步子过大可能直接冲到对面的坡上，函数值反而上升。
- 最后一行：线性层 $\mathbf{y}=W\mathbf{x}$ 的雅可比矩阵恰好就是 $W$ 本身（数值验证为 `True`）。**反向传播里，每一层要做的事就是用这层的雅可比矩阵把梯度「往回传」**。

### 损失函数的导数

> **标准定义 · 均方误差与二元交叉熵 (MSE & binary cross-entropy)**
>
> 设 $x$ 是模型输出，$y$ 是目标。**均方误差**：$L=\tfrac12(x-y)^2$，导数 $\dfrac{\partial L}{\partial x}=x-y$。**二元交叉熵**：$x\in(0,1)$ 是模型给出的概率，$y\in\{0,1\}$ 是标签，
>
> $$L=-\big(y\log x+(1-y)\log(1-x)\big),\qquad \frac{\partial L}{\partial x}=-\frac{y}{x}+\frac{1-y}{1-x}$$
>
> 若 $x=\sigma(z)$，$z$ 是进 Sigmoid 之前的原始输出（**logit**），链式法则给出 $\dfrac{\partial L}{\partial z}=\sigma(z)-y$。
>
> *English: For MSE L = ½(x−y)², ∂L/∂x = x − y. For binary cross-entropy with x = σ(z), the chain rule gives ∂L/∂z = σ(z) − y, which is bounded.*

**白话版：「误差越大，推得越用力」。** MSE 的梯度就是误差本身：差 1 就推 1，差 0.1 就推 0.1。BCE 更狠：模型「自信地答错」时（标签是 1 却说概率 0.001），梯度是 $-1000$，推得非常猛；但这个猛劲儿一旦换到 logit 上，就被 Sigmoid 的导数 $x(1-x)$ 抵消成 $\sigma(z)-y$，大小永远不超过 1，不会爆炸。

""" + C_LOSS + r"""

读输出：

- **MSE**：$x$ 离目标 $y=1$ 越远，梯度绝对值越大，正好等于误差 $x-y$（$x=0$ 时 -1.00，$x=0.9$ 时只有 -0.10；$x=1.5$ 超过了目标，梯度变成正的 0.50，会把 $x$ 往回拉）。
- **BCE 对概率 $x$**：标签为 1，$x$ 从 0.5 掉到 0.001，损失从 0.693 涨到 6.908，梯度从 -2.0 一路变成 **-1000.0**，没有上限。
- **BCE 对 logit $z$**：同样是「答错」，$z=-8$ 时梯度是 -0.9997，$z=-2$ 时是 -0.8808，$z=0$ 时 -0.5000，$z=2$ 时 -0.1192：全部落在 $(-1,0)$ 之间，**有界**，并且「错得越狠，梯度越接近 -1」，既强烈又不会爆炸。公式和数值微分对得上。这正是 PyTorch 里 `BCEWithLogitsLoss` 和 `CrossEntropyLoss` 直接吃 logit 的原因，也为后面信息论一节里「语言模型的损失就是交叉熵」做铺垫。

### 动手实验：手推梯度，从零训练一个逻辑回归

把前面所有东西串起来：数据是 6 个点，$x$ 小的标签为 0，大的标签为 1；模型 $p=\sigma(wx+b)$；损失是 BCE。链式法则给出 $\partial L/\partial z=p-y$，而 $z=wx+b$，所以 $\partial z/\partial w=x$，$\partial z/\partial b=1$，于是

$$\frac{\partial L}{\partial w}=\frac1N\sum_i(p_i-y_i)\,x_i,\qquad \frac{\partial L}{\partial b}=\frac1N\sum_i(p_i-y_i)$$

先用数值微分做**梯度检验**，通过之后再放心地训练：

""" + C_EXP + r"""

读输出：梯度检验为 `True`，说明手推的公式没错。起点参数全为 0，模型对每个点都猜 0.5，损失正好是 $\ln2=0.6931$。训练 200 步后，$w$ 增长到 6.069（斜率越来越陡），$b$ 保持在 0（这份数据关于原点对称，所以不需要平移），损失降到 0.0164；最终给出的概率是 $[0,\,0.002,\,0.046,\,0.954,\,0.998,\,1]$，和标签完全吻合。你亲手用「链式法则 + 梯度下降」训练了一个模型。**反向传播做的，就是对任意多层的网络自动地、高效地做同样的事。** 另外，一个有趣的细节：损失下降越来越慢（第 10 步 0.1421，第 50 步 0.0500，第 200 步 0.0164），因为越接近正确，梯度 $p-y$ 越小，步子也越小。

### 这一节你要带走的三句话

1. **链式法则 = 把每一层的局部导数相乘**；层数一多，小于 1 的因子相乘会让梯度消失（Sigmoid 10 层后只剩 $10^{-7}$ 量级），这是深层网络难训练的根源。
2. **梯度指向上升最快的方向；一阶泰勒展开说明沿负梯度走一小步，函数值会下降**，但只在局部成立，学习率太大就失效。
3. **BCE 配 Sigmoid（或交叉熵配 Softmax），对 logit 的梯度就是「预测 − 标签」**，简单、有界；写完任何梯度，都用数值微分检验一下。
"""),
  THINK("用链式法则求 $\\frac{d}{dx} e^{-x^2}$，并在 $x=0.7$ 处算出数值，再说说你要怎样检验它。", r"""
外层 $e^u$ 的导数是 $e^u$，内层 $u = -x^2$ 的导数是 $-2x$：

$$\frac{d}{dx}e^{-x^2} = e^{-x^2}\cdot(-2x) = -2x\,e^{-x^2}$$

代入 $x=0.7$：$-2\times0.7\times e^{-0.49}\approx-0.8577$，和上面代码块里数值微分的结果 -0.857677 一致。检验方法：用中心差分 $\frac{f(x+h)-f(x-h)}{2h}$（$h$ 取 $10^{-5}$ 左右）算一下，两者应该在 6 位小数内一致。
"""),
  THINK("**概念辨析**：Sigmoid 的导数最大值是多少？在哪里取到？为什么说「Sigmoid 网络叠很多层难训练，ReLU 好一些」？", r"""
$\sigma'(x)=\sigma(x)(1-\sigma(x))$，当 $\sigma(x)=0.5$（即 $x=0$）时取最大值 $0.5\times0.5=0.25$，其余地方更小（两端趋近 0）。

链式法则让 $L$ 层的梯度是 $L$ 个局部导数的乘积，Sigmoid 每层的因子最多 0.25，所以 10 层后至多 $0.25^{10}\approx9.5\times10^{-7}$（实验里是 $3.5\times10^{-7}$）：梯度消失，前面的层几乎学不到东西。ReLU 在正区间导数恒为 1，乘积不会缩小，所以更好训练。代价是输入为负时导数为 0，神经元可能「死掉」。
"""),
  THINK("**联系机器学习**：BCE 对概率 $x$ 的梯度可以是 -1000（上面 $x=0.001$ 的情形），为什么实际训练里并不会因此爆炸？实现上还要注意什么？", r"""
实际训练时模型输出的是 logit $z$，损失对 $z$ 的梯度是 $\sigma(z)-y$，绝对值不超过 1：$-1000$ 这个因子被 Sigmoid 的导数 $x(1-x)\approx0.001$ 抵消了。

实现上要注意：**不要先算 `sigmoid` 再算 `log`**。当 $z$ 很负时 $\sigma(z)$ 在浮点数里会变成 0，$\log0=-\infty$。PyTorch 的 `BCEWithLogitsLoss`、`CrossEntropyLoss` 直接从 logit 出发，用 log-sum-exp 之类的技巧一次算完，数值上稳定，所以一般不要自己拆开写。
"""),
  KW(("导数","derivative","瞬时变化率、切线斜率"),
     ("数值微分","numerical differentiation","用差商近似导数，用来检验，不用来训练"),
     ("中心差分","central difference","$(f(x+h)-f(x-h))/2h$，比单边差分更准"),
     ("乘积法则","product rule","$(fg)' = f'g + fg'$"),
     ("链式法则","chain rule","$(f\\circ g)' = f'(g(x))\\,g'(x)$，导数沿层相乘"),
     ("梯度消失 / 爆炸","vanishing / exploding gradient","连乘的因子小于 1 / 大于 1，梯度指数级缩小 / 增大"),
     ("偏导数","partial derivative","只动一个变量时的导数"),
     ("梯度","gradient $\\nabla f$","所有偏导数组成的向量，指向上升最快方向"),
     ("雅可比矩阵","Jacobian","向量对向量的所有偏导数，线性层的雅可比就是 $W$"),
     ("一阶泰勒展开","first-order Taylor expansion","用梯度在一点附近线性近似函数，误差是二阶小量"),
     ("均方误差","mean squared error (MSE)","$\\frac{1}{2}(x-y)^2$，导数 $x - y$"),
     ("二元交叉熵","binary cross-entropy (BCE)","二分类常用的损失，对概率的梯度无界"),
     ("logit","logit","进 Sigmoid / Softmax 之前的原始输出，BCE 对它的梯度是 $\\sigma(z)-y$"),
     ("梯度检验","gradient check","用数值微分核对手写的梯度"),
  ),
 ],
 "references": [
  {"title": "ARENA [0.0] Prerequisites — Calculus 部分", "url": "https://github.com/ARENA-education/ARENA_materials/blob/main/chapter0_fundamentals/instructions/pages/00_%5B0.0%5D_Prerequisites.md", "note": "本节依据的原文大纲和损失函数导数的思考题（讲解为自写，未转载原文）"},
  {"title": "3Blue1Brown：Essence of Calculus 系列", "url": "https://www.3blue1brown.com/topics/calculus", "note": "ARENA 推荐；想从头补微积分可以看第 1–3 章"},
  {"title": "The Matrix Calculus You Need for Deep Learning", "url": "https://explained.ai/matrix-calculus/", "note": "ARENA 选读：从标量求导进阶到矩阵求导，雅可比矩阵讲得很细"},
  {"title": "MIT 18.01 Single Variable Calculus（OpenCourseWare）", "url": "https://ocw.mit.edu/courses/18-01-single-variable-calculus-fall-2006/", "note": "想系统补导数、链式法则时的开放课程"},
 ],
 "quiz": {"questions": QUIZ},
}

if __name__ == '__main__':
    dump(unit, "arena-0.0", "u08-calculus.json")
