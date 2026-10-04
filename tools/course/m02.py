"""ml-0 第 2 节：线性回归与梯度下降（v3 格式）"""
from unitlib import *
from m02c import *
from m02_quiz import QUIZ

unit = {
 "id": "u02",
 "title": "线性回归与梯度下降",
 "en": "Linear Regression & Gradient Descent",
 "minutes": 95,
 "objectives": [
  "写出 **线性回归 (linear regression)** 的模型 $\\hat y=Xw+b$ 与 **均方误差 (MSE)** 损失，并用矩阵推导出梯度 $\\nabla_wL=\\frac2nX^\\top(Xw+b\\mathbf 1-y)$，会用 **数值梯度检验 (gradient check)** 验证自己的推导",
  "由梯度为 0 得到 **正规方程 (normal equations)**，用 `np.linalg.solve` 求解析解，知道特征共线时它为什么会出问题",
  "手写 **批量 / 随机 / 小批量梯度下降 (batch / stochastic / mini-batch GD)**，并与解析解对照；理解 **epoch**、批量大小与每步噪声的关系",
  "理解 **学习率 (learning rate)** 太小（慢）与太大（发散）的原因：Hessian 的最大特征值 $L$ 与稳定条件 $\\eta<2/L$；理解 **特征缩放 (feature scaling)** 通过降低 **条件数 (condition number)** 加速收敛",
  "会做 **多项式特征 (polynomial features)**（对参数仍是线性模型）和 **岭回归 (ridge regression)**，会算并解读 **决定系数 $R^2$**；知道向量化与循环结果用 `np.allclose` 比较",
 ],
 "blocks": [
  T(r"""
### 先说这一节要干什么

上一节说过，学习问题 = 数据 + 模型 + 损失 + 优化。这一节把最简单的一套完整地走通：**模型是线性函数，损失是均方误差，优化用梯度下降**。它值得花整整一节，是因为：线性回归有解析解，可以用来**检验**梯度下降写得对不对；它的损失是严格的「碗」，可以把学习率、条件数、特征缩放这些现象**算清楚**；而且之后的逻辑回归、神经网络，用的是同一套「算梯度、走一步」的流程，只是模型和损失换了。

**开始之前你要会：**

- 梯度、偏导数的意思，链式法则（arena-0.0「偏导数、梯度与雅可比矩阵」「链式法则、乘积法则与梯度消失」小节）；
- 矩阵乘法与形状规则、转置（arena-0.0「矩阵乘法 = 变换的复合」「非方阵与形状规则」小节）；
- NumPy 的数组运算、轴与归约、向量化（arena-0.0「轴与归约」「向量化」小节），以及「小批量」这个词（arena-0.0「小批量：真实训练是怎么用梯度的」小节）；
- 上一节：假设类、损失、训练 / 验证集、MSE、过拟合。

**学完它你就能看懂这几件事：**

- PyTorch 训练循环里 `loss.backward(); optimizer.step(); optimizer.zero_grad()` 每一行在做什么，因为我们会先**手写一遍同样的事**；
- 论文里的「learning rate 3e-4」「batch size 256」「we standardize all features」是在调什么、为什么重要；
- 为什么损失曲线有时一路平滑下降、有时锯齿状抖动、有时直接变成 `nan`；
- 岭回归 / 权重衰减 (weight decay) 和过拟合的关系，上一节的「方差」在这里变成一个可以调的旋钮。

**本节安排（约 95 分钟）**：模型与损失（10 分钟）→ 视频一（9 分钟）→ 梯度与正规方程（15 分钟）→ 梯度下降与学习率（15 分钟）→ 视频二（24 分钟）→ 随机与小批量（8 分钟）→ 特征缩放与向量化（8 分钟）→ 多项式特征、岭回归、$R^2$（8 分钟）→ 总结与「想一想」。

**怎么学这一节：** 代码块在页面里都能「▶ 运行」，只用 numpy，按顺序运行，后面用到前面定义的变量（`X`、`y`、`grad`、`gd`……）。每次先猜输出，再运行。

### 线性回归：模型与均方误差

> **标准定义 · 线性回归 (linear regression)**
>
> 给定样本矩阵 $X\in\mathbb R^{n\times d}$（每行一个样本、每列一个特征）和目标 $y\in\mathbb R^n$，线性回归的假设类是 $\hat y=Xw+b\mathbf 1$，其中 $w\in\mathbb R^d$ 是**权重 (weights)**，$b\in\mathbb R$ 是**偏置 (bias / intercept)**，$\mathbf 1$ 是全 1 向量。损失取**均方误差**：
>
> $$L(w,b)=\frac1n\lVert Xw+b\mathbf 1-y\rVert^2=\frac1n\sum_{i=1}^n\big(x_i^\top w+b-y_i\big)^2$$
>
> *English: Linear regression models the target as an affine function of the features, and fits the weights and bias by minimising the mean squared error.*

**白话版：「给每个特征一个权重，加起来再加个基准值」。** 预测一个订单的运费：`运费 = 基础运费 + 每公斤单价 × 重量 + 每公里单价 × 距离`。$w$ 就是各个「单价」，$b$ 就是基础运费；训练就是从历史订单里反推这些价格，使得整体预测误差的平方平均最小。为什么平方？上一节说过：平方损失对应高斯噪声下的最大似然，而且它处处可导、是光滑的「碗」。
""" + C_DATA + r"""

**读输出：** `X.shape` 是 `(200, 3)`，`y.shape` 是 `(200,)`：200 个样本、3 个特征。我们造数据时用了真实参数 $w=(2,-1,0.5)$、$b=3$，噪声标准差 0.5；所以用**真实参数**预测时，MSE 约等于噪声方差 $0.5^2=0.25$，输出是 `0.256`（差一点是样本波动）。这就是上一节说的不可约误差：**再好的模型，MSE 也降不到 0.25 以下**。而什么都不会的 $w=0,b=0$ 的 MSE 是 `13.223`，这就是我们要降下来的距离。这里 `predict` 里的 `X @ w + b` 靠广播把标量 $b$ 加到每个样本上。
"""),
  V("PaFPbb66DxQ", "视频一：The Main Ideas of Fitting a Line to Data（StatQuest with Josh Starmer）", 9),
  T(r"""
**视频一要点：** 用最直观的方式讲「拟合一条直线」：每个点到直线有一个**残差 (residual)**，把残差平方后加起来，平方和最小的那条线就是最小二乘线。我们的 `mse` 只是把这个平方和再除以 $n$。

### 梯度：矩阵形式的推导

怎样让损失降下来？沿着梯度的反方向走。先把梯度**推出来**，再用数值方法检查推得对不对。

**推导。** 记**残差向量** $r=Xw+b\mathbf 1-y\in\mathbb R^n$，则 $L=\frac1n r^\top r$。对 $r$ 取微分：$dL=\frac2n r^\top dr$，而 $dr=X\,dw+\mathbf 1\,db$。所以

$$dL=\frac2n r^\top X\,dw+\frac2n r^\top\mathbf 1\,db$$

读出系数就得到梯度：

$$\nabla_wL=\frac2nX^\top r,\qquad \frac{\partial L}{\partial b}=\frac2n\mathbf 1^\top r=\frac2n\sum_i r_i$$

形状检查：$X^\top$ 是 $(d,n)$，$r$ 是 $(n,)$，乘起来是 $(d,)$，与 $w$ 同形，**梯度总是和参数同形状**。直觉：$\frac2nX^\top r$ 是「每个特征列和残差的相关」：如果第 $j$ 列特征大时残差也总是正的（预测偏高），那么减小 $w_j$ 就能降低损失。

> **标准定义 · 梯度检验 (gradient check)**
>
> 用**中心差分** $\frac{L(\theta+\epsilon e_j)-L(\theta-\epsilon e_j)}{2\epsilon}$（$e_j$ 是第 $j$ 个坐标的单位向量）近似偏导数，与解析梯度比较。$\epsilon$ 取 $10^{-6}$ 左右时，误差量级约为 $\epsilon^2$ 加上浮点舍入。
>
> *English: A gradient check compares an analytic gradient to a central finite-difference approximation to catch derivation or coding bugs.*

**白话版：「用笨办法验算聪明办法」。** 手推的梯度很容易漏个系数或转置，笨办法（真的把参数挪一点点，看损失变多少）虽然慢，但不会错。**每次手写新的梯度，都先做这一步。**
""" + C_GRAD + r"""

**读输出：** 在 $w=(0.5,0.5,0.5),b=0.5$ 这一点，解析梯度是 $\nabla_wL=(-2.7263,\;2.9352,\;0.3379)$，$\partial L/\partial b=-4.6535$；中心差分算出的前后两行完全相同（保留 4 位小数），最后两个 `True` 表示在 $10^{-6}$ 的容差内一致。再看符号：$\partial L/\partial w_1=-2.7263<0$，说明增大 $w_1$ 会让损失下降（真实的 $w_1=2$ 比当前的 0.5 大）；$\partial L/\partial w_2>0$ 说明应当减小 $w_2$（真实的是 $-1$）。**梯度的符号告诉你往哪边走。**

### 正规方程：一步求出解析解

最小值处梯度为 0。为了少写一条 $b$ 的公式，把 $b$ 并进参数：给 $X$ 左边加一列全 1，得到**增广矩阵** $X_a=[\mathbf 1\;X]\in\mathbb R^{n\times(d+1)}$，参数 $\theta=(b,w)$。则 $L=\frac1n\lVert X_a\theta-y\rVert^2$，梯度为 $\frac2nX_a^\top(X_a\theta-y)$。令其为 0：

> **标准定义 · 正规方程 (normal equations)**
>
> $$X_a^\top X_a\,\theta=X_a^\top y$$
>
> 当 $X_a$ 列满秩时 $X_a^\top X_a$ 可逆，唯一解为 $\hat\theta=(X_a^\top X_a)^{-1}X_a^\top y$。此时 $L$ 的 Hessian 为 $\frac2nX_a^\top X_a$，**半正定**，所以 $L$ 是凸函数，梯度为 0 的点就是全局最小点。
>
> *English: Setting the gradient of the squared error to zero gives the normal equations; when X has full column rank the minimiser is unique and equals (XᵀX)⁻¹Xᵀy.*

**白话版：「一步到位的公式」。** 不用试，直接解一个线性方程组。几何上，$X_a\hat\theta$ 是 $y$ 在 $X_a$ 的列空间里的**正交投影**，残差与每一列正交，这正是 $X_a^\top r=0$。**实践里永远不要真的求逆**：用 `np.linalg.solve(A, b)` 直接解方程，比 `inv(A) @ b` 又快又准；条件数差时用 `lstsq`（基于 QR / SVD）。
""" + C_NORMAL + r"""

**读输出：** 解出来的 $\theta=(b,w_1,w_2,w_3)$ 是 `[ 2.982  1.955 -1.048  0.527]`，和真实值 $(3,\,2,\,-1,\,0.5)$ 很接近，差距就是噪声带来的估计误差（样本只有 200 个）。第二行 `True`：`solve` 和 `lstsq` 给出同一个解。第三行 `True`：把 $\hat\theta$ 代回我们前面写的 `grad`，梯度的每个分量都小于 $10^{-10}$，说明它确实是极小点。**这个解析解就是后面梯度下降要逼近的「标准答案」。**

**什么时候它会失效？** 如果两个特征完全一样（共线），$X_a$ 的列线性相关，$X_a^\top X_a$ 不可逆，解不唯一；如果「近似共线」，矩阵病态，解对噪声极其敏感；$d$ 很大时（几万）$O(d^3)$ 的求解也太贵。这时就要用岭回归（本节后面）、`lstsq` 或梯度下降。

### 批量梯度下降

> **标准定义 · 梯度下降 (gradient descent)**
>
> 从某个初值 $\theta_0$ 出发，重复：$\theta_{t+1}=\theta_t-\eta\,\nabla L(\theta_t)$，其中 $\eta>0$ 叫**学习率 (learning rate)**，是步长。**批量 (batch)** 梯度下降每一步用**全部** $n$ 个样本算梯度。
>
> *English: Gradient descent repeatedly moves the parameters a step of size η against the gradient; batch gradient descent uses all training samples to compute each gradient.*

**白话版：「蒙着眼睛下山」。** 你站在碗形的山坡上，看不到碗底，但能感觉到脚下哪边更陡（梯度）；每次朝最陡的下坡方向迈一步，步子大小是 $\eta$。步子太小，走到天黑；步子太大，一脚跨到对面山坡上，越走越高。
""" + C_GD + r"""

**读输出：** 初值 $w=0,b=0$，学习率 0.1，走 200 步。最后的参数 $(w,b)$ 是 `[ 1.955 -1.048  0.527] 2.982`，和正规方程的 `[ 2.982  1.955 -1.048  0.527]` 一致。损失曲线：第 1 步 `8.8648`，第 10 步 `0.478`，第 50 步 `0.25`，第 200 步 `0.25`，**先快后慢，最后停在不可约误差 0.25**。最后一行 `True` 表示和解析解在 $10^{-3}$ 以内一致。**这就是 `loss.backward(); optimizer.step()` 在干的事，只是我们自己写了梯度。**

### 学习率：太小太慢，太大发散

线性回归的损失是二次函数，所以可以算清楚学习率的界限。损失的 **Hessian**（二阶导矩阵）是 $H=\frac2nX_a^\top X_a$，设它的特征值为 $\lambda_{\min}\le\dots\le\lambda_{\max}=L$。对二次函数，每一步在第 $k$ 个特征方向上的误差都乘以 $(1-\eta\lambda_k)$：

- 要所有方向都不发散，需要 $|1-\eta\lambda_k|<1$，即 $\eta<2/\lambda_k$，最严的是最大的 $\lambda_{\max}=L$：**$\eta<2/L$**；
- 收敛有多快，取决于**最慢的方向**，它每步只缩小 $(1-\eta\lambda_{\min})$。取 $\eta=1/L$ 时，每步缩小 $1-1/\kappa$，其中 $\kappa=\lambda_{\max}/\lambda_{\min}$ 是 **条件数 (condition number)**。
""" + C_LR + r"""

**读输出：** 这份数据的 Hessian 最大特征值 $L$ 是 `2.207`，所以稳定学习率上界是 $2/L=$ `0.906`。四个学习率的第 50 步损失：$\eta=0.001$ 时 `11.03`，几乎没怎么动（太小，走得太慢）；$\eta=0.1$ 时 `0.25`，已经到底；$\eta=0.9$ 时 `0.2821`，**接近上界，开始来回振荡**，虽然还在收敛，但比 0.1 慢；$\eta=1.1$ 时 `3.756e+14`，**超过上界，每步越冲越远，损失爆炸**。如果你在训练神经网络时看到损失突然变成 `nan` 或 `inf`，第一怀疑对象就是学习率太大。"""),
  V("sDv4f4s2SB8", "视频二：Gradient Descent, Step-by-Step（StatQuest with Josh Starmer）", 24),
  T(r"""
**视频二要点：** 从一个只有一个参数（截距）的例子开始，把「损失曲线」「斜率」「步长 = 斜率 × 学习率」讲得非常慢，然后扩展到截距与斜率两个参数同时更新，最后说明什么时候停（步长足够小，或达到最大步数）。对照我们的代码：`gw, gb = grad(...)` 是斜率，`w - lr * gw` 就是「步长 = 学习率 × 斜率」。

### 随机与小批量梯度下降

批量梯度下降每走一步都要扫完所有 $n$ 个样本，$n$ 到百万、千万时太贵。观察：损失是各样本损失的平均，所以**随机抽一小撮样本算出的平均梯度，是完整梯度的无偏估计**，只带一点噪声。

> **标准定义 · 随机与小批量梯度下降 (stochastic & mini-batch GD)**
>
> 每一步从训练集随机取一个**小批量 (mini-batch)** $B$（$|B|=m$），用 $g_B=\frac1m\sum_{i\in B}\nabla\ell_i(\theta)$ 代替完整梯度，更新 $\theta\leftarrow\theta-\eta g_B$。$m=1$ 叫**随机梯度下降 (SGD)**，$m=n$ 就是批量梯度下降。把训练集完整过一遍叫一个 **epoch**；每个 epoch 先把样本打乱，再按顺序切成小批量。$\mathbb E[g_B]=\nabla L(\theta)$，方差大致与 $1/m$ 成正比。
>
> *English: SGD and mini-batch GD replace the full gradient by an unbiased estimate from a random subset; one pass over the data is an epoch.*

**白话版：「民意调查」。** 想知道全国人民的意见，不必问遍每一个人，随机问 32 个人就能得到一个差不多的估计，当然有误差；每一步都做一次这样的快速调查，走起路来虽然会晃，但每一步便宜得多，同样的时间里可以走很多步。
""" + C_SGD + r"""

**读输出：** 三种设置各跑 20 个 epoch。批量大小 200（即批量 GD）：每个 epoch 只更新 1 次，共 20 次更新，损失 `0.2545`，离解析解的距离 `0.0707`，还没完全收敛；批量大小 32：每个 epoch 更新 7 次（$\lceil200/32\rceil=7$），共 140 次，损失 `0.2517`，距离 `0.0396`；批量大小 1：每个 epoch 更新 200 次，共 4000 次，损失 `0.2524`，距离 `0.0481`。三者的损失都接近下限 0.25，但是看距离：**同样遍历 20 遍数据，小批量因为更新次数多，进展更大**；批量 1 虽然更新最多，却因为噪声大，最后停在解附近「抖动」，距离反而比批量 32 略大（所以实际训练中常在后期减小学习率）。**批量大小是在「每步的噪声」与「每步的成本 / 并行度」之间折中**，GPU 上通常取 32 到几千。

### 特征缩放：让山谷变圆

前面说过，收敛速度由条件数 $\kappa$ 决定。如果特征的量级相差很大，Hessian 的特征值就相差很大，$\kappa$ 巨大，损失曲面是一条又细又长的山谷：**陡的方向要小学习率才不发散，平的方向又走不动**。

> **标准定义 · 标准化 (standardization)**
>
> 对每个特征 $j$，用**训练集**的均值 $\mu_j$ 和标准差 $\sigma_j$ 变换：$x'_{ij}=(x_{ij}-\mu_j)/\sigma_j$。变换后每个特征均值为 0、标准差为 1。验证集、测试集和以后的新数据**必须用训练集的 $\mu,\sigma$**，不能自己重新算。
>
> *English: Standardisation rescales each feature to zero mean and unit variance using statistics computed on the training set only.*

**白话版：「把单位统一」。** 一个特征是「件数」（个位数），另一个是「重量，克」（几百），同样是「增加 1」，对损失的影响天差地别；统一成「离平均值有几个标准差」之后，所有特征都在同一个尺度上，一个学习率对所有方向都合适。
""" + C_SCALE + r"""

**读输出：** 两个特征，一个量级约为 1，另一个均值 500、标准差 100。原始特征的 Hessian 条件数是 `7.76e+06`（近八百万），标准化后只有 `1.086`（几乎是正圆的碗）。用各自能用的较大学习率跑 300 步：原始特征（学习率只能取 $3\times10^{-6}$，再大就发散）300 步后损失还有 `8.2179`；标准化后（学习率 0.3）损失已经是 `0.2461`，到底了。**注意：均值不为 0 的特征（这里均值 500）还会和截距那一列强相关，这也是条件数巨大的原因，所以「减均值」和「除以标准差」两步都重要。** 另外，缩放不改变线性模型能达到的最低损失，只改变**走得多快**；如果你要解释权重的物理意义，需要把参数换算回原始单位：$w_j^{\text{orig}}=w_j'/\sigma_j$。

### 向量化：把循环交给 numpy

前面所有的 `grad` 都是矩阵乘法写的，没有 Python 循环。这样写既短，又快得多（numpy 底层用 C / BLAS，一次处理整块数据）。但向量化写错的 bug 很难看出来，所以要用一个**慢但明显正确**的循环版本来对拍：
""" + C_VEC + r"""

**读输出：** 两个 `True`：循环版本和向量化版本的结果在浮点误差内一致。注意判断用的是 `np.allclose` / `np.isclose`，而不是 `==`：**浮点数加法不满足结合律**，循环是一个一个加，矩阵乘法用分块、不同的累加顺序，末位可能不同，但相对差在 $10^{-15}$ 量级。这是数值代码里通用的做法：先写一个慢而对的版本，再写快的，用随机输入对拍。（运行时间的差别本节不打印，因为每台机器不同，你可以自己用 `%timeit` 看。）

### 多项式特征：对参数线性、对输入非线性

> **标准定义 · 多项式特征 (polynomial features)**
>
> 把一维输入 $x$ 映射成特征向量 $\phi(x)=(1,x,x^2,\dots,x^k)$，然后对 $\phi(x)$ 做**线性回归**：$\hat y=\sum_{j=0}^kw_jx^j$。这个模型对**参数 $w$ 是线性的**（所以正规方程、梯度下降原样适用），但对输入 $x$ 是非线性的（所以能拟合曲线）。一般地，任何固定的特征映射 $\phi$ 都可以这样用。
>
> *English: Polynomial regression applies linear regression to the feature map (1, x, …, x^k); the model is linear in its parameters although nonlinear in the input.*

**白话版：「用线性回归画曲线」。** 把「$x$ 的平方」当成一个新的特征列，线性回归并不知道这一列是由 $x$ 算出来的，照样给它配一个权重。这个想法是神经网络的前身：神经网络就是让模型自己**学出**特征映射 $\phi$。
""" + C_POLY + r"""

**读输出：** 这里把 $x\in[0,1]$ 先缩放到 $t=2x-1\in[-1,1]$，再造特征 $(1,t,t^2,t^3)$（为什么先缩放：高次幂会让条件数急剧变坏，上一节「特征缩放」讲过）。用正规方程解出 3 次多项式的系数 `[-0.019 -2.658  0.173  2.741]`，第二行 `True` 说明它与 `np.polyfit`（用同一个 $t$）一致。训练 MSE `0.04`，验证 MSE `0.059`，两者接近，都低于噪声方差 $0.09$（只有 20 个点，样本噪声碰巧偏小），没有明显的过拟合。

### 岭回归：把「方差」变成可调的旋钮

上一节看到，9 次多项式把噪声也拟合了。能不能保留 9 次的灵活性，却不让系数乱跳？办法是在损失里加一个**惩罚项**，惩罚大的权重：

> **标准定义 · 岭回归 (ridge regression, $L_2$ 正则化)**
>
> $$L_\lambda(w)=\frac1n\lVert Xw-y\rVert^2+\lambda\lVert w\rVert^2,\qquad \hat w=\Big(X^\top X+n\lambda I\Big)^{-1}X^\top y$$
>
> $\lambda\ge0$ 是**超参数**（用验证集选），不惩罚常数项。$\lambda$ 越大，权重被压得越小。加上 $n\lambda I$ 之后矩阵总是可逆，所以它也解决了共线的问题。深度学习里的**权重衰减 (weight decay)** 与它密切相关。
>
> *English: Ridge regression adds an L2 penalty on the weights; it shrinks the solution, reduces variance, and makes XᵀX + λI always invertible.*

**白话版：「给大步子加税」。** 权重越大，罚得越重，模型就不敢把某个特征的系数拉得很极端；用一点偏差换来方差的大幅下降。
""" + C_RIDGE + r"""

**读输出：** 用 9 次多项式、20 个训练点。$\lambda=0$（普通最小二乘）：训练 MSE 最低 `0.021`，验证 MSE 却高到 `0.176`，过拟合。$\lambda=10^{-6}$：训练 `0.028`、验证 `0.099`；$\lambda=10^{-4}$：训练 `0.034`、验证最低 `0.087`；$\lambda=10^{-2}$：训练 `0.061`、验证 `0.127`，开始欠拟合；$\lambda=1$：训练 `0.372`、验证 `0.585`，压得太狠，几乎是一条直线。**训练误差随 $\lambda$ 单调上升**（模型被限制），**验证误差是 U 形**，最佳的 $\lambda$ 要用验证集选，这就是**偏差-方差折中的一个可以调的旋钮**。

### 决定系数 $R^2$

> **标准定义 · 决定系数 (coefficient of determination, $R^2$)**
>
> $$R^2=1-\frac{\sum_i(y_i-\hat y_i)^2}{\sum_i(y_i-\bar y)^2}=1-\frac{\text{SS}_{\text{res}}}{\text{SS}_{\text{tot}}}$$
>
> 它是「模型比『永远预测均值』好多少」的相对指标：$R^2=1$ 完美拟合，$R^2=0$ 与基线相同，**$R^2<0$ 比基线还差**（在新数据上完全可能）。注意应当用**训练集的均值**当基线，在测试集上算。
>
> *English: R² is the fraction of variance explained relative to the predict-the-mean baseline; it can be negative on held-out data.*

**白话版：「模型把『波动』解释掉了几成」。** $y$ 本来上下波动（总变化量 $\text{SS}_\text{tot}$），模型预测完之后还剩多少没解释（$\text{SS}_\text{res}$）？没解释的占比越小，$R^2$ 越接近 1。它和上一节的基线思想一致，只是把 MSE 换成了一个不依赖单位的相对数。
""" + C_R2 + r"""

**读输出：** 3 次多项式：训练 $R^2$ `0.926`，验证 $R^2$ `0.918`，两者接近，没有过拟合。基线「永远预测训练均值」在验证集上的 $R^2$ 是 `-0.09`：它略差于「用验证集自己的均值」，所以是负数（说明用训练均值当预测，在验证集上不会恰好是 0）。直线（1 次）的验证 $R^2$ 只有 `0.591`，欠拟合；9 次无正则时训练 $R^2$ 高达 `0.961`，验证却只有 `0.755`，**训练 $R^2$ 随复杂度单调上升，不能用来选模型**。$R^2$ 是个方便的相对指标，但永远要看验证集上的数字，并且和 MSE / MAE 一起看，因为 $R^2$ 的大小也会随数据的方差而变。

### 这一节你要带走的三句话

1. **线性回归 = 线性模型 + 平方损失**：梯度是 $\frac2nX^\top(Xw+b\mathbf 1-y)$（形状与参数相同），令它为 0 得正规方程；任何手写的梯度都要用数值梯度检验。
2. **梯度下降**沿负梯度走：学习率要小于 $2/L$（否则发散），收敛速度由条件数决定，特征标准化把条件数降到接近 1；小批量用无偏但有噪声的梯度，用每步便宜换更多步。
3. **模型对参数线性就是线性回归**：多项式特征能拟合曲线，也容易过拟合，岭回归的 $\lambda$ 是控制方差的旋钮；$R^2$ 衡量比基线好多少，在新数据上可以是负的。
"""),
  THINK("**（计算）** 只有一个特征和一个权重（无偏置），损失 $L(w)=\\frac1n\\sum_i(wx_i-y_i)^2$，数据是 $x=(1,2)$，$y=(2,3)$。(1) 写出 $\\frac{dL}{dw}$；(2) 求解析最优的 $w$；(3) 从 $w_0=0$、学习率 $\\eta=0.1$ 走一步，得到 $w_1$。", r"""
$n=2$。

(1) $\frac{dL}{dw}=\frac2n\sum_ix_i(wx_i-y_i)=\sum_ix_i(wx_i-y_i)=(w-2)+2(2w-3)=5w-8$。

(2) 令 $5w-8=0$，得 $w^*=1.6$。（等价于正规方程 $\sum x_i^2\,w=\sum x_iy_i$，即 $5w=8$。）

(3) 在 $w_0=0$ 处梯度是 $-8$，所以 $w_1=0-0.1\times(-8)=0.8$，向 $1.6$ 靠近了一半。这里 Hessian 是 $5$（即 $L=5$），所以稳定上界是 $2/5=0.4$；每一步误差乘以 $1-\eta\cdot5=0.5$，与算出的「走了一半」吻合。
"""),
  THINK("**（概念辨析）** 同学说：「我把全部数据（含测试集）标准化之后再切分训练集和测试集，这样特征的尺度统一了，对吧？」这个做法的问题在哪？在部署模型预测一个新样本时，应该怎样标准化？", r"""
问题是**数据泄漏**：均值和标准差用到了测试样本，测试集的信息通过预处理渗进了训练流程，测试成绩会偏乐观（偏差不一定大，但原则上就不干净）。正确做法：**先切分，再只用训练集计算 $\mu,\sigma$**，然后用这同一组 $(\mu,\sigma)$ 变换验证集、测试集和之后的任何新样本。部署时同理：**训练时用的 $\mu,\sigma$ 必须随模型一起保存**，新样本来了先用它们变换，再送进模型。直接对新样本自己算 $\mu,\sigma$（比如只有一个样本时标准差为 0）是错的。
"""),
  THINK("**（联系深度学习）** 本节的 `gd` 函数里手写了 `w, b = w - lr * gw, b - lr * gb`。PyTorch 里对应哪三行？为什么在神经网络里「条件数」「特征缩放」的思想变成了 BatchNorm、LayerNorm 和 Adam 这类东西？", r"""
对应 `loss.backward()`（算梯度，存进每个参数的 `.grad`）、`optimizer.step()`（用 `.grad` 更新参数，SGD 的 `step` 就是 `p -= lr * p.grad`）、`optimizer.zero_grad()`（清掉旧梯度，否则会累加）。

神经网络的损失不再是二次函数，但在局部可以用 Hessian 近似，条件数仍然决定走得顺不顺：各层、各参数的量级相差很大时，损失曲面就是又窄又长的山谷。**输入标准化**是在数据层面降低条件数；**BatchNorm / LayerNorm** 是在网络内部，对每一层的输入做类似的标准化，使每层看到的尺度稳定；**Adam** 等自适应优化器则给每个参数用不同的有效学习率（按梯度的历史大小缩放），在优化器层面「补偿」尺度不齐。它们都在做同一件事：让损失曲面对一个学习率更友好。
"""),
  KW(("线性回归","linear regression","对参数线性的模型 $\\hat y=Xw+b$，用平方损失拟合"),
     ("权重与偏置","weights & bias","$w$ 是每个特征的系数，$b$ 是截距（基准值）"),
     ("均方误差","mean squared error (MSE)","残差平方的平均，线性回归的损失"),
     ("正规方程","normal equations","梯度为 0 的条件 $X^\\top X\\theta=X^\\top y$，给出解析解"),
     ("梯度检验","gradient check","用中心差分的数值梯度验证手写梯度"),
     ("梯度下降","gradient descent","$\\theta\\leftarrow\\theta-\\eta\\nabla L$，沿负梯度反复走"),
     ("学习率","learning rate","步长 $\\eta$；对二次损失要小于 $2/L$ 才不发散"),
     ("小批量与 epoch","mini-batch & epoch","每步用一小撮样本估计梯度；完整遍历一次训练集叫一个 epoch"),
     ("随机梯度下降","stochastic gradient descent (SGD)","批量大小为 1（或泛指用小批量）的梯度下降，梯度无偏但有噪声"),
     ("Hessian 与条件数","Hessian & condition number","二阶导矩阵；最大与最小特征值之比，越大梯度下降越慢"),
     ("特征缩放（标准化）","feature scaling (standardization)","用训练集的均值与标准差把特征变成均值 0、方差 1"),
     ("向量化","vectorization","用数组运算代替 Python 循环；结果用 `np.allclose` 对拍"),
     ("多项式特征","polynomial features","$(1,x,x^2,\\dots)$，对参数线性、对输入非线性"),
     ("岭回归","ridge regression","加 $\\lambda\\lVert w\\rVert^2$ 惩罚的线性回归，压小权重、降低方差"),
     ("决定系数","coefficient of determination ($R^2$)","$1-\\text{SS}_{\\text{res}}/\\text{SS}_{\\text{tot}}$，相对于预测均值的改进，可以为负"),
  ),
 ],
 "references": [
  {"title": "Stanford CS229 讲义：Linear Regression（LMS、正规方程、概率解释）", "url": "https://cs229.stanford.edu/", "note": "本节大纲依据：Part I 线性回归，含梯度下降、随机 / 批量梯度、正规方程的矩阵推导和高斯噪声下的最大似然解释，只引用不转载"},
  {"title": "An Introduction to Statistical Learning（ISL）第 3 章 Linear Regression、第 6 章 Linear Model Selection and Regularization", "url": "https://www.statlearning.com/", "note": "作者免费公开；第 3 章讲线性回归与 $R^2$，第 6 章讲岭回归与 lasso"},
  {"title": "Machine Learning Specialization（吴恩达）第 1 门课 Week 1–2：线性回归、梯度下降、特征缩放", "url": "https://www.deeplearning.ai/courses/machine-learning-specialization/", "note": "更慢的视频版，学习率、特征缩放、向量化都有专门的短视频"},
  {"title": "Stochastic Gradient Descent, Clearly Explained!!!（StatQuest，约 11 分钟，选看）", "url": "https://www.youtube.com/watch?v=vMh0zPT0tLI", "note": "对应本节「随机与小批量」，用最小的例子演示 SGD"},
  {"title": "Probabilistic Machine Learning: An Introduction（Murphy）第 11 章 Linear Regression", "url": "https://probml.github.io/pml-book/book1.html", "note": "把线性回归写成最大似然与最小二乘，并连到岭回归与贝叶斯观点，作者免费公开"},
 ],
 "quiz": {"questions": QUIZ},
}

TARGET = [2, 0, 3, 1, 3, 0, 1, 2, 0, 3]
for q, t in zip(unit["quiz"]["questions"], TARGET):
    q["options"][q["answer"]], q["options"][t] = q["options"][t], q["options"][q["answer"]]
    q["answer"] = t

if __name__ == '__main__':
    dump(unit, "ml-0", "u02-linear-regression.json")
