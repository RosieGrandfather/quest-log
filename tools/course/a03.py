"""ARENA 0.0 第 3 节：线性变换与矩阵乘法（按 v3 格式重写，2026-10-04）"""
from unitlib import *
from a03c import C_VEC, C_LINEAR, C_COLS, C_COMP, C_SHAPE, C_FIT
from a03_quiz import QUIZ

unit = {
 "id": "u03",
 "title": "线性变换与矩阵乘法",
 "en": "Linear Transformations & Matrix Multiplication",
 "minutes": 95,
 "objectives": [
  "用几何直觉和代数性质两种方式说清楚 **线性变换 (linear transformation)**：网格线保持平行且等距、原点不动，等价于 $T(\\mathbf{u}+\\mathbf{v})=T(\\mathbf{u})+T(\\mathbf{v})$ 与 $T(c\\mathbf{v})=cT(\\mathbf{v})$，并能用代码检验一个变换是不是线性的",
  "知道矩阵的**每一列**就是基向量变换后的位置，会把 **矩阵乘向量 (matrix-vector product)** 读成**各列的线性组合 (linear combination of columns)**",
  "理解 **矩阵乘法 (matrix multiplication)** = 变换的**复合 (composition)**：顺序从右往左读，满足**结合律 (associativity)**、一般不满足**交换律 (commutativity)**",
  "会判断矩阵乘法的**形状 (shape)**：$(n,m)$ 乘 $(m,l)$ 得 $(n,l)$；理解**非方阵**是在不同维度之间的变换，以及 `nn.Linear` 的 `weight` 为什么是 `(out, in)`",
  "能从输入输出数据里**恢复**（学出）一个线性变换，把「线性回归 = 学一个矩阵」和神经网络训练联系起来",
 ],
 "blocks": [
  T(r"""
### 先说这一节要干什么

上一节你已经看到：神经网络的每一层是 $\mathbf{a}'=\sigma(W\mathbf{a}+\mathbf{b})$，核心是一次**矩阵乘法**。ARENA 把线性代数标为**最高优先级**，第一条就是「线性变换是什么、为什么重要」。这一节换一个看矩阵的方式：**矩阵不是一张数字表格，而是一种对空间的变换**。

数据和 AI 方向的硕士课程里，线性代数是所有东西的地基：线性回归、主成分分析 (PCA)、神经网络、注意力机制，全是「矩阵作用在向量上」的变化。如果只会按公式算乘积，读到 $QK^\top V$ 时只能硬背；如果脑子里有「变换」的画面，就能一眼看出形状、看出这一步在做什么。

**学完它你就能看懂这几件事：**

- `nn.Linear(784, 16)` 为什么存一个 `(16, 784)` 的权重，计算为什么写成 `x @ weight.T + bias`；
- Transformer 里 $W_Q$、$W_K$、$W_V$ 把向量「投影」到另一个空间，究竟是什么意思；
- 为什么 `A @ B` 和 `B @ A` 一般不一样，为什么 `(A @ B) @ C` 和 `A @ (B @ C)` 总是一样（后者决定了先算哪边更省时间）；
- 线性回归、最小二乘本质上就是「从数据里找一个矩阵」。

**本节安排（约 95 分钟）**：导读与向量（10 分钟）→ 视频一（11 分钟）→ 线性变换与「列」的视角（18 分钟）→ 视频二（10 分钟）→ 复合与矩阵乘法（15 分钟）→ 视频三（5 分钟）→ 非方阵与形状（10 分钟）→ 动手实验：从数据里学出矩阵（10 分钟）→「想一想」。视频是英文的，可以打开 YouTube 的中文字幕。

### 先认识向量与基

> **标准定义 · 向量、线性组合与基向量 (vector, linear combination & basis)**
>
> **向量 (vector)** 既可以看作从原点出发的**箭头**，也可以看作一列数 $\begin{bmatrix}x\\y\end{bmatrix}$。向量的**线性组合**是「数乘再相加」：$c_1\mathbf{v}_1+c_2\mathbf{v}_2$。平面的**标准基向量 (standard basis vectors)** 是 $\hat\imath=\begin{bmatrix}1\\0\end{bmatrix}$ 和 $\hat\jmath=\begin{bmatrix}0\\1\end{bmatrix}$，任何向量都是它们的线性组合：$\begin{bmatrix}x\\y\end{bmatrix}=x\hat\imath+y\hat\jmath$，坐标 $(x,y)$ 就是组合的系数。
>
> *English: A vector can be seen as an arrow from the origin or as a list of numbers. A linear combination is a sum of scaled vectors, c₁v₁ + c₂v₂. Every plane vector is a combination of the standard basis vectors î = (1,0) and ĵ = (0,1); its coordinates are the coefficients.*

**白话版：「坐标是配方」。** 向量 $(3,-2)$ 的意思是「取 3 份 $\hat\imath$，再取 $-2$ 份 $\hat\jmath$」。如果换一套「原料」（基向量），同一个箭头就会有不同的配方，这是第 5 节「基变换」的主题。数据科学里一个样本的特征向量，也完全是这个意思：每个坐标是一个特征，有多少「份」。

""" + C_VEC + r"""

读输出：第一行，3 份 $\hat\imath$ 减 2 份 $\hat\jmath$ 正好是 $(3,-2)$。第二行，换成基向量 $(1,1)$ 和 $(1,-1)$，同一个向量的配方变成 $(0.5,2.5)$：$0.5\times(1,1)+2.5\times(1,-1)=(3,-2)$。**箭头没变，变的是描述它的坐标。**
"""),
  V("kYB8IZa5AuE", "视频一：Linear transformations and matrices（线性代数的本质 第 3 章）", 11),
  T(r"""
### 线性变换

看完视频，用定义把它钉牢：

> **标准定义 · 线性变换 (linear transformation)**
>
> 映射 $T:\mathbb{R}^n\to\mathbb{R}^m$ 是**线性的**，当且仅当对所有向量 $\mathbf{u},\mathbf{v}$ 和数 $c$：
>
> $$T(\mathbf{u}+\mathbf{v})=T(\mathbf{u})+T(\mathbf{v}),\qquad T(c\,\mathbf{v})=c\,T(\mathbf{v})$$
>
> 几何上：网格线变换后仍是**直线**，保持**平行且等距**，**原点不动**。线性变换由它对基向量的作用唯一确定：$T(\mathbf{v})=x\,T(\hat\imath)+y\,T(\hat\jmath)$。
>
> *English: T is linear iff T(u+v) = T(u) + T(v) and T(cv) = cT(v). Geometrically, grid lines stay parallel and evenly spaced and the origin stays fixed. A linear map is completely determined by where it sends the basis vectors.*

**白话版：「橡皮网格的拉伸」。** 想象坐标纸是一张橡皮网格，你可以转它、拉它、推歪它，但不能折、不能撕、不能把原点拽走，这样得到的就是线性变换。旋转、缩放、剪切 (shear) 都是；**平移不是**（原点动了）。下面写一个小函数，用随机向量检验这两条性质：

""" + C_LINEAR + r"""

读输出：旋转和剪切都通过了 100 组随机检验；**平移**没通过，一个很直观的信号是原点从 $(0,0)$ 跑到了 $(1,0)$。注意最后一行的 **ReLU**（神经网络的激活函数）也不是线性的，但它的原点没有动：**原点不动只是线性的必要条件，不是充分条件**，所以我们才需要完整检验两条性质。这也解释了上一节的结论：没有激活函数时多层网络等价于一层，正是因为矩阵乘法是线性的，而加了 ReLU 之后就不再是了。

**一个技术细节：** $W\mathbf{x}+\mathbf{b}$（带偏置）严格说也不是线性的（$\mathbf{b}\ne\mathbf{0}$ 时原点会动），而是**仿射变换 (affine transformation)** = 线性变换 + 平移。深度学习里习惯笼统地叫它「线性层」，但要记得两者的区别：线性层的「线性」部分是 $W$，偏置只是在输出端做了一次平移。

### 矩阵的「列」就是基向量的去向

既然线性变换由基向量的去向决定，那只需把这两个去向记下来，就能描述整个变换，这就是矩阵：

> **标准定义 · 矩阵与矩阵乘向量 (matrix & matrix–vector product)**
>
> 线性变换 $T$ 的**矩阵**，是把 $T(\hat\imath)$、$T(\hat\jmath)$ 作为**列**并排得到的：$A=\big[\,T(\hat\imath)\ \ T(\hat\jmath)\,\big]$。矩阵乘向量就是应用这个变换：
>
> $$\begin{bmatrix}a&b\\c&d\end{bmatrix}\begin{bmatrix}x\\y\end{bmatrix}=x\begin{bmatrix}a\\c\end{bmatrix}+y\begin{bmatrix}b\\d\end{bmatrix}=\begin{bmatrix}ax+by\\cx+dy\end{bmatrix}$$
>
> 结果是**矩阵各列的线性组合**，系数就是向量的各个坐标。
>
> *English: The matrix of a linear map has the images T(î), T(ĵ) as its columns. Multiplying a matrix by a vector gives a linear combination of the columns, with the vector's coordinates as coefficients.*

**白话版：「列是新坐标轴，向量是配方」。** 变换之后，原来的 $\hat\imath$、$\hat\jmath$ 变成了两个新箭头（矩阵的两列）；向量 $(x,y)$ 的「配方」没变，还是 $x$ 份第一个、$y$ 份第二个，只是原料换成了新箭头。所以：**矩阵乘向量 = 用新的原料重新做一遍配方。** 也可以按「行」读：每个输出分量是一行与向量的点积。两种读法结果相同，但**按列读**更能看出这个变换在做什么，后面讲秩、列空间时全靠它。

""" + C_COLS + r"""

读输出：逆时针转 90 度后，$\hat\imath$ 落在 $(0,1)$、$\hat\jmath$ 落在 $(-1,0)$，把它们当列并排得到旋转矩阵 $\begin{bmatrix}0&-1\\1&0\end{bmatrix}$。拿它去乘 $(3,-2)$ 得到 $(2,3)$：「按列读」$3\times$第一列 $-2\times$第二列，和「按行读」逐行点积，答案一样。最后看剪切：单位正方形的四个角 $(0,0),(1,0),(1,1),(0,1)$ 被送到 $(0,0),(1,0),(2,1),(1,1)$，正方形变成了平行四边形，**网格线还是平行且等距的**，面积没变，仍是 1（面积变化倍数就是行列式，下一节讲）。
"""),
  V("XkY2DOUCWMU", "视频二：Matrix multiplication as composition（线性代数的本质 第 4 章）", 10),
  T(r"""
### 矩阵乘法 = 变换的复合

> **标准定义 · 矩阵乘法 (matrix multiplication)**
>
> 先做变换 $B$ 再做变换 $A$，总效果仍是线性变换，其矩阵记作 $AB$，满足 $A(B\mathbf{v})=(AB)\mathbf{v}$。**顺序从右往左读**，与函数复合 $f(g(x))$ 相同。乘积的元素是
>
> $$(AB)_{ij}=\sum_k A_{ik}B_{kj}$$
>
> 即 $A$ 的第 $i$ 行与 $B$ 的第 $j$ 列的点积；等价地，$AB$ 的第 $j$ 列 $=A\times(B\text{ 的第 }j\text{ 列})$。**结合律**：$(AB)C=A(BC)$ 总成立；**交换律**：$AB=BA$ 一般不成立。
>
> *English: AB is the matrix of "first B, then A": A(Bv) = (AB)v, read right to left like function composition. (AB)_ij = Σ_k A_ik B_kj, i.e. row i of A dotted with column j of B. Matrix multiplication is associative but in general not commutative.*

**白话版：「流水线」。** $B$ 是第一道工序，$A$ 是第二道工序，$AB$ 是把两道工序合成一道。**换顺序，产品就不一样了**：先转桌子再推歪，和先推歪再转桌子，桌子最后的位置不同（$AB\neq BA$）；但三道工序 $C,B,A$，你先把后两道并成一道、还是先把前两道并成一道，结果一样（结合律）。下面的实验把这几件事都验证一遍：

""" + C_COMP + r"""

读输出：
- 旋转 $R$ 和剪切 $S$ 的两个乘积 $SR=\begin{bmatrix}1&-1\\1&0\end{bmatrix}$、$RS=\begin{bmatrix}0&-1\\1&1\end{bmatrix}$ 不同；作用在 $(3,-2)$ 上，一个得到 $(5,3)$，一个得到 $(2,1)$；
- $(SR)\mathbf{v}$ 和 $S(R\mathbf{v})$ 相同：这就是「乘积矩阵 = 复合变换」；
- 「$AB$ 的第 $j$ 列等于 $A$ 乘 $B$ 的第 $j$ 列」成立：$B$ 把基向量送到哪，$A$ 再把它送到哪；
- 随机的 1000 对 $3\times3$ 整数矩阵里，**结合律 1000 次全部成立，交换律 0 次成立**（这是随机整数矩阵的结果；某些特殊矩阵，如单位矩阵、旋转和同角度旋转，是可交换的，但那是例外）；
- 最后一行呼应上一节：$W_3W_2W_1$ 是 $(10,784)$，形状只看最两头。这正是「没有激活函数，三层网络压缩成一个矩阵」的算式。

**结合律的实际价值：** 同一个乘积 $ABC$ 可以先算 $AB$ 或先算 $BC$，结果一样，但**计算量可能差很多**。例如 $A$ 是 $1000\times2$、$B$ 是 $2\times1000$、$C$ 是 $1000\times1$：先算 $(AB)C$ 要先造一个 $1000\times1000$ 的大矩阵，再乘；先算 $A(BC)$，$BC$ 只是 $2\times1$，$A(BC)$ 只是 $1000\times1$，便宜得多。Transformer 的注意力里，这类「先乘哪边」的选择会直接影响显存。
"""),
  V("v8VSDg_WQlA", "视频三：Nonsquare matrices as transformations between dimensions（线性代数的本质 第 8 章）", 5),
  T(r"""
### 非方阵与形状规则

> **标准定义 · 矩阵的形状与非方阵 (shape & non-square matrix)**
>
> $m\times n$ 矩阵（$m$ 行 $n$ 列）有 $n$ 列、每列是 $m$ 维向量，所以它把 $n$ 维空间映射到 $m$ 维空间：$\mathbb{R}^n\to\mathbb{R}^m$。矩阵乘法可行的条件与结果形状是：
>
> $$\underbrace{A}_{(n,\ m)}\ \underbrace{B}_{(m,\ l)}=\underbrace{AB}_{(n,\ l)}$$
>
> 中间的维度必须相等，结果取两头。
>
> *English: An m×n matrix maps R^n to R^m. The product (n,m)·(m,l) is defined and has shape (n,l); the inner dimensions must match.*

**白话版：「接口对接」。** 想成两节管道：前一节的出口粗细（$m$）必须和后一节的入口粗细一样，整条管道才通；整条管道的入口是 $B$ 的入口 $l$（作为输入维度），出口是 $A$ 的出口 $n$。写代码时遇到形状报错，**先把每个矩阵的形状写出来，检查中间两个数字**，这是最快的排查办法。

""" + C_SHAPE + r"""

读输出：$(3,4)\times(4,5)\to(3,5)$；反过来乘 $(4,5)\times(3,4)$ 直接报错，因为中间的 5 和 3 对不上。一个 $3\times2$ 的矩阵把二维平面映射到三维空间：1000 个二维点变成了 1000 个三维点，形状 `(2, 1000)` → `(3, 1000)`。但这些三维点**并没有铺满三维空间**，而是全部落在平面 $z=x+y$ 上（因为输出只是两个三维列向量的线性组合），点云的**秩**是 2。这个「输出能铺满几维」的问题，下一节用**秩 (rank)** 来回答。最后两行是神经网络的约定：`W` 的形状是 `(16, 784)`（输出维数在前），一个样本 `W @ x` 得到 `(16,)`；**一批样本是行向量堆叠，所以写成 `X @ W.T`**，得到 `(32, 16)`，两种写法对每个样本的结果相同。PyTorch 的 `nn.Linear(784, 16)` 就是这么存的：`weight` 的形状是 `(16, 784)`，计算 `x @ weight.T + bias`。

### 动手实验：从数据里学出一个矩阵

最后把这些串起来做个小实验：有一个「黑箱」线性变换 $A$，你看不到它的矩阵，只能喂输入、看输出。两种办法找出它：

""" + C_FIT + r"""

读输出：**办法一**最直接：把 $\hat\imath=(1,0)$ 和 $\hat\jmath=(0,1)$ 喂进去，输出的两个向量按列排好，就是 $A$ 本身，这正是「矩阵的列 = 基向量的去向」。**办法二**是现实的情形：只有带噪声的随机样本，用**最小二乘 (least squares)** 解出 $\begin{bmatrix}2.003&-1.016\\0.506&3.004\end{bmatrix}$，很接近真值 $\begin{bmatrix}2&-1\\0.5&3\end{bmatrix}$，误差来自噪声。**办法三**用**梯度下降**从全 0 的矩阵出发，200 步就走到了和最小二乘同样的位置（两者在 $10^{-3}$ 内一致）。

这个小实验里有三个很重要的联系：**线性回归**（多输出）就是「从数据里学一个矩阵」；**训练神经网络**用的梯度下降，和办法三的循环是同一种东西，只是代价函数更复杂、层数更多（梯度要靠上一节的反向传播算）；而办法二是「有封闭解」的特殊情形，神经网络因为有非线性，没有这样的公式，只能靠迭代。

### 这一节你要带走的三句话

1. **线性变换 = 网格保持平行等距、原点不动**；它完全由基向量的去向决定，**矩阵的列就是基向量变换后的位置**，矩阵乘向量就是各列的线性组合。
2. **矩阵乘法 = 变换的复合**，顺序从右往左读；满足结合律、一般不满足交换律；形状规则 $(n,m)\cdot(m,l)=(n,l)$，写代码先对中间两个数字。
3. **非方阵在不同维度之间变换**；神经网络的一层就是 `(out, in)` 形状的矩阵乘法（加偏置、过激活函数）；去掉非线性，多层就能合并成一个矩阵。
"""),
  THINK("**计算题**：取 $A=\\begin{bmatrix}1&2\\\\0&1\\end{bmatrix}$、$B=\\begin{bmatrix}0&1\\\\1&0\\end{bmatrix}$。(a) 算 $AB$ 和 $BA$；(b) $B$ 在做什么几何变换？(c) 用「列的线性组合」的读法，说出 $AB$ 的两列各是什么。", r"""
(a) 按 $(AB)_{ij}=\sum_kA_{ik}B_{kj}$：

$$AB=\begin{bmatrix}1\cdot0+2\cdot1&1\cdot1+2\cdot0\\0\cdot0+1\cdot1&0\cdot1+1\cdot0\end{bmatrix}=\begin{bmatrix}2&1\\1&0\end{bmatrix},\qquad BA=\begin{bmatrix}0&1\\1&2\end{bmatrix}$$

两者不同，再次说明 $AB\ne BA$。

(b) $B$ 把 $\hat\imath=(1,0)$ 送到 $(0,1)$、把 $\hat\jmath=(0,1)$ 送到 $(1,0)$：交换两个坐标，几何上是沿直线 $y=x$ 的**反射 (reflection)**。

(c) $AB$ 的第 $j$ 列 $=A\times B$ 的第 $j$ 列。$B$ 的第一列是 $(0,1)$，$A(0,1)^\top=0\cdot(1,0)+1\cdot(2,1)=(2,1)$；$B$ 的第二列是 $(1,0)$，$A(1,0)^\top=(1,0)$。所以 $AB$ 的两列是 $(2,1)$ 和 $(1,0)$，和 (a) 一致。从「按列读」看：右乘一个交换矩阵，等于**把 $A$ 的两列交换位置**（$AB$ 是 $A$ 的列互换），左乘（$BA$）则是**把行互换**。
"""),
  THINK("**概念辨析**：下面哪些是线性变换，哪些不是？(1) 把平面上所有点向右移动 2；(2) 把所有点到原点的距离变成原来的 3 倍；(3) 把 $(x,y)$ 变成 $(x^2,y)$；(4) 神经网络的一层 $\\mathbf{a}'=\\sigma(W\\mathbf{a}+\\mathbf{b})$（$\\sigma$ 是 ReLU）。", r"""
(1) **不是**：原点被移到 $(2,0)$，是平移。验证：$T(\mathbf{0})\ne\mathbf{0}$。

(2) **是**：等于 $T(\mathbf{v})=3\mathbf{v}$，矩阵是 $\begin{bmatrix}3&0\\0&3\end{bmatrix}$。

(3) **不是**：$T(2\mathbf{v})=(4x^2,2y)$，而 $2T(\mathbf{v})=(2x^2,2y)$，不满足 $T(c\mathbf{v})=cT(\mathbf{v})$；几何上网格线会变弯。

(4) **不是**：偏置 $\mathbf{b}$ 是平移（仿射），ReLU 又是非线性的。拆开看，$W\mathbf{a}$ 是线性的，加 $\mathbf{b}$ 是仿射，$\sigma$ 是非线性。**整个网络的表达能力来自非线性；线性部分的作用，是让数据在高维空间里被拉伸、旋转，为非线性做铺垫。**
"""),
  THINK("**联系后续内容**：已知 $W_Q$、$W_K$ 的形状都是 `(d_model, d_head)`，一批 token 向量 $X$ 的形状是 `(seq, d_model)`，注意力分数是 $(XW_Q)(XW_K)^\\top$。写出每一步的形状，并说明最后得到的分数矩阵是什么形状、每个元素是什么。", r"""
- $XW_Q$：`(seq, d_model) @ (d_model, d_head)` → `(seq, d_head)`，每个 token 一个 query 向量（第 $i$ 行）；
- $XW_K$：同理 `(seq, d_head)`，每个 token 一个 key 向量；
- $(XW_K)^\top$：`(d_head, seq)`；
- 相乘：`(seq, d_head) @ (d_head, seq)` → **`(seq, seq)`**。

分数矩阵的第 $(i,j)$ 个元素 $=\mathbf{q}_i\cdot\mathbf{k}_j$：第 $i$ 个 token 的 query 和第 $j$ 个 token 的 key 的点积，表示「第 $i$ 个 token 对第 $j$ 个 token 的关注程度」（还要除以 $\sqrt{d_{\text{head}}}$ 再做 softmax）。两个乘法的中间维度都对上了（$d_{\text{model}}$ 和 $d_{\text{head}}$），转置的作用正是让「每对 token 的点积」一次性算出来。ARENA 第 1 章实现注意力时，每一步都应该先写下这样的形状。
"""),
  KW(("向量","vector","箭头，或一列数"),
     ("基向量","basis vectors $\\hat\\imath,\\hat\\jmath$","标准坐标轴方向的单位向量"),
     ("线性组合","linear combination","$c_1\\mathbf{v}_1+c_2\\mathbf{v}_2$ 这种「数乘再相加」"),
     ("线性变换","linear transformation","保持网格平行等距、原点不动的变换"),
     ("仿射变换","affine transformation","线性变换加平移，$W\\mathbf{x}+\\mathbf{b}$"),
     ("矩阵","matrix","列 = 基向量变换后的位置"),
     ("矩阵乘向量","matrix–vector product","各列的线性组合，系数是向量的坐标"),
     ("矩阵乘法","matrix multiplication","变换的复合，$(AB)_{ij}=\\sum_k A_{ik}B_{kj}$"),
     ("复合","composition","先做一个变换再做另一个，从右往左读"),
     ("交换律 / 结合律","commutativity / associativity","矩阵乘法一般不满足前者、总满足后者"),
     ("剪切","shear","把正方形推成平行四边形的变换"),
     ("形状","shape","$(n,m)(m,l)=(n,l)$，中间维度必须相等"),
     ("非方阵","non-square matrix","在不同维度之间的变换，$m\\times n$ 把 $\\mathbb{R}^n$ 送到 $\\mathbb{R}^m$"),
     ("最小二乘","least squares","让平均平方误差最小的拟合，线性模型有封闭解"),
     ("批量","batch","一次处理多个样本，样本在第一个维度"),
  ),
 ],
 "references": [
  {"title": "ARENA [0.0] Prerequisites — Linear Algebra 部分", "url": "https://github.com/ARENA-education/ARENA_materials/blob/main/chapter0_fundamentals/instructions/pages/00_%5B0.0%5D_Prerequisites.md", "note": "本节依据的原文大纲和思考题（讲解为自写，未转载原文）"},
  {"title": "3Blue1Brown：Essence of Linear Algebra 全系列", "url": "https://www.youtube.com/playlist?list=PLZHQObOWTQDPD3MizzM2xVFitgF8hE_ab", "note": "ARENA 推荐的系列，本节用了第 3、4、8 章"},
  {"title": "mlwiki：Matrix-Matrix Multiplication", "url": "http://mlwiki.org/index.php/Matrix-Matrix_Multiplication", "note": "ARENA 推荐的矩阵乘法讲解，含行列视角的几种读法"},
  {"title": "MIT 18.06 Linear Algebra（Gilbert Strang，OpenCourseWare）", "url": "https://ocw.mit.edu/courses/18-06-linear-algebra-spring-2010/", "note": "选看：前几讲讲矩阵乘法的五种看法，是硕士阶段常用的线性代数教材课程"},
  {"title": "Mathematics for Machine Learning（Deisenroth 等，免费电子书）", "url": "https://mml-book.github.io/", "note": "选读：第 2 章线性代数，第 3 章解析几何；与本节和下面几节对应"},
 ],
 "quiz": {"questions": QUIZ},
}

if __name__ == '__main__':
    dump(unit, "arena-0.0", "u03-linear-transformations.json")
