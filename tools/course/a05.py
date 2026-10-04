"""ARENA 0.0 第 5 节：基、点积与基变换（按 v3 格式重写，2026-10-04）"""
from unitlib import *
from a05c import C_SPAN, C_DOT, C_CHANGE, C_ORTHO, C_EXPER
from a05_quiz import QUIZ

unit = {
 "id": "u05",
 "title": "基与基变换",
 "en": "Bases, Dot Products & Change of Basis",
 "minutes": 105,
 "objectives": [
  r"理解 **张成空间 (span)**、**线性无关 (linear independence)**、**基 (basis)** 与 **维数 (dimension)**，会用 NumPy 的 `matrix_rank` 判断一组向量能不能当基",
  r"从代数和几何两个角度理解 **点积 (dot product)**、**范数 (norm)**、**投影 (projection)**，会算 **余弦相似度 (cosine similarity)**",
  r"会用 $B\mathbf{c}$ 和 $B^{-1}\mathbf{x}$ 做 **基变换 (change of basis)**，会把变换翻译成 $B^{-1}MB$，并知道换基不改变迹和行列式",
  r"认识 **正交矩阵 (orthogonal matrix)** 与 **标准正交基 (orthonormal basis)**：逆就是转置、保长度保夹角、坐标就是点积",
  r"理解「高维随机方向几乎正交」和「概念方向不一定是神经元轴」这两个事实，这是 ARENA 后面 **特权基 (privileged basis)** 与 **叠加 (superposition)** 的数学基础",
 ],
 "blocks": [
  T(r"""
### 先说这一节要干什么

我们习惯用标准坐标轴描述向量，但那只是**一种**选择。同一个向量，换一把「尺子」（换一组基），数字就全变了，可它还是同一个向量。ARENA 的线性代数清单里专门列了「基与基变换」，因为可解释性研究的一个核心问题就是：**网络学到的「概念」，一定对齐神经元的坐标轴吗？** 要讨论这类问题，就得先能在不同的基之间自如切换，并且会用**点积**衡量两个方向有多接近。

这一节把这些变成能运行的代码：判断一组向量是不是基，算点积与余弦相似度，做基变换，验证正交矩阵的性质，最后用两个小实验看看高维空间里方向的几何。

**学完它你就能看懂这几件事：**

- 注意力机制里 $QK^\top$ 为什么是一堆点积，以及为什么要除以 $\sqrt{d}$（点积的大小会随维度增长）；
- 嵌入向量检索、词向量类比里的**余弦相似度**到底在比较什么；
- 可解释性论文里「特征方向 (feature direction)」「特权基」「叠加」这些词，说的是**换一组基看激活值**；
- 为什么初始化、PCA、QR 分解里到处是**正交矩阵**：它们不放大也不缩小任何东西，数值上最稳定。

**本节安排（约 105 分钟）**：导读与张成、基（15 分钟）→ 视频一（10 分钟）→ 点积与余弦相似度（15 分钟）→ 视频二（14 分钟）→ 基变换（15 分钟）→ 视频三（13 分钟）→ 正交矩阵（10 分钟）→ 高维几何小实验（8 分钟）→「想一想」。视频是英文的，可以打开 YouTube 的中文字幕。

### 张成空间、线性无关与基

> **标准定义 · 线性组合、张成、线性无关、基 (linear combination, span, independence, basis)**
>
> 向量 $\mathbf{v}_1,\dots,\mathbf{v}_k$ 的**线性组合 (linear combination)** 是 $c_1\mathbf{v}_1+\dots+c_k\mathbf{v}_k$（$c_i$ 为实数）。所有线性组合构成的集合叫它们的**张成空间 (span)**。如果其中没有任何一个向量可以由其余向量的线性组合得到，就称它们**线性无关 (linearly independent)**，否则**线性相关 (linearly dependent)**。一组既**线性无关**、又**张成整个空间**的向量叫**基 (basis)**；$n$ 维空间的任何一组基恰好有 $n$ 个向量，这个数 $n$ 称为**维数 (dimension)**。基给每个向量一组**唯一**的坐标：$\mathbf{x}=c_1\mathbf{b}_1+\dots+c_n\mathbf{b}_n$。
>
> *English: A basis is a linearly independent set of vectors that spans the whole space. Every basis of an n-dimensional space has exactly n vectors, and every vector has a unique coordinate vector with respect to it.*

**白话版：「一套不浪费的坐标系」。** 把向量想成你能走的「步子」：线性组合就是每种步子走几次；张成空间就是你能到达的所有地方。如果某种步子可以被别的步子凑出来，它就是**多余的**（线性相关）；基就是「既够用、又没有多余」的一套步子。

算一个例子：$(1,0,0)$、$(0,1,0)$、$(1,1,0)$ 能不能当三维空间的基？第三个等于前两个之和，所以多余；而且三个向量的第三个坐标全是 0，永远走不出 $xy$ 平面。用代码验证，并换一组真正的基：

""" + C_SPAN + r"""

读输出：三个向量拼成的矩阵**秩 (rank) 为 2**，也就是只有两个方向是真正独立的，张成的是二维平面；想组合出 $(0,0,1)$，最好的组合也有误差 1.0，完全够不着。换成 $(1,1,0),(1,-1,0),(0,0,1)$ 后秩是 3、行列式是 $-2$（不为 0，说明可逆）。向量 $(3,1,2)$ 在新基下的坐标是 $(2,1,2)$：$2(1,1,0)+1(1,-1,0)+2(0,0,1)=(3,1,2)$，还原结果与原向量一致。最后一行说明二维里 $(1,2),(2,4)$ 共线，秩只有 1。

**实用判据**：$n$ 个 $n$ 维向量构成基 $\Longleftrightarrow$ 以它们为列的方阵**可逆** $\Longleftrightarrow$ 秩为 $n$ $\Longleftrightarrow$ 行列式不为 0。这四种说法是同一件事，上一节（矩阵性质）已经见过。
"""),
  V("k7RM-ot2NWY", "视频一：Linear combinations, span, and basis vectors（线性代数的本质 第 2 章）", 10),
  T(r"""
### 点积、范数与余弦相似度

> **标准定义 · 点积、范数、余弦相似度 (dot product, norm, cosine similarity)**
>
> 两个向量的**点积 (dot product)** 有两个等价的定义：
>
> $$\mathbf{u}\cdot\mathbf{v}=\sum_i u_iv_i=\|\mathbf{u}\|\,\|\mathbf{v}\|\cos\theta$$
>
> 其中 $\|\mathbf{u}\|=\sqrt{\mathbf{u}\cdot\mathbf{u}}$ 是**长度**（**L2 范数 (L2 norm)**），$\theta$ 是两向量的夹角。点积为 0 就称它们**正交 (orthogonal)**。把点积除以两个长度，得到**余弦相似度 (cosine similarity)** $\cos\theta=\dfrac{\mathbf{u}\cdot\mathbf{v}}{\|\mathbf{u}\|\|\mathbf{v}\|}\in[-1,1]$。$\mathbf{u}$ 在 $\mathbf{v}$ 方向上的**投影 (projection)** 长度是 $\mathbf{u}\cdot\hat{\mathbf{v}}$，其中 $\hat{\mathbf{v}}=\mathbf{v}/\|\mathbf{v}\|$。
>
> *English: The dot product is Σ uᵢvᵢ = ‖u‖‖v‖cos θ. Dividing by both lengths gives cosine similarity, which depends only on direction. The projection of u onto v has length u·v̂.*

**白话版：「两个方向有多顺路」。** 点积大于 0 表示大致同向，等于 0 表示垂直，小于 0 表示大致反向。**余弦相似度只看方向、不看长度**，所以比较两篇文章的主题时，长文章和短文章不会因为长度而吃亏。

""" + C_DOT + r"""

读输出：同一对向量，用「分量相乘再相加」和「长度乘长度乘 $\cos50^\circ$」都得到 3.8567，两个定义确实等价；由点积反推出的夹角正好是 50.0 度。$\mathbf{u}$ 在 $\mathbf{v}$ 方向上的「影子」长 1.2856（就是 $2\cos50^\circ$）。把 $\mathbf{v}$ 放大 10 倍，点积也放大 10 倍（38.57），而余弦相似度仍是 0.6428：**点积会随长度变化，余弦不会**。这就是检索系统常用余弦的原因。玩具词向量里，cat 和 dog 的余弦相似度 0.987（几乎同向），cat 和 car 只有 0.123（接近垂直）。最后一行是经典的 $(3,4)\cdot(4,-3)=0$，两者正交。

**对偶性 (duality)**：和一个固定向量 $\mathbf{v}$ 做点积，本身就是一个「把向量变成一个数」的线性变换，它的矩阵是 $1\times n$ 的 $\mathbf{v}^\top$，所以 $\mathbf{u}\cdot\mathbf{v}=\mathbf{v}^\top\mathbf{u}$。这也是为什么矩阵乘法 $A\mathbf{x}$ 可以读成「$A$ 的每一行和 $\mathbf{x}$ 做点积」：**矩阵乘法就是一批点积**。注意力里的 $QK^\top$ 就是每个查询向量和每个键向量的点积；当维度 $d$ 很大时，点积的方差随 $d$ 增大（第 7 节会看到），所以要除以 $\sqrt{d}$。
"""),
  V("LyGKycYT2v0", "视频二：Dot products and duality（线性代数的本质 第 9 章）", 14),
  T(r"""
### 基变换

> **标准定义 · 基变换 (change of basis)**
>
> 设另一组基 $\mathbf{b}_1,\dots,\mathbf{b}_n$ 用标准坐标写出，把它们作为**列**排成可逆矩阵 $B=[\mathbf{b}_1\ \cdots\ \mathbf{b}_n]$。一个向量在新基下的坐标为 $\mathbf{c}$，在标准坐标下就是 $\mathbf{x}=B\mathbf{c}$；反过来 $\mathbf{c}=B^{-1}\mathbf{x}$。如果 $M$ 是用标准坐标写的线性变换，那么**同一个变换**在新基坐标下的矩阵是 $M_B=B^{-1}MB$。换基不改变变换本身，所以 $\operatorname{tr}(M_B)=\operatorname{tr}(M)$，$\det(M_B)=\det(M)$。
>
> *English: If the columns of B are a new basis written in standard coordinates, then x = Bc converts new coordinates to standard ones and c = B⁻¹x converts back. The same linear map M has matrix B⁻¹MB in the new basis; its trace and determinant are unchanged.*

**白话版：「翻译官」。** 想象另一个人用自己的一套尺子说话：他说「$(3,2)$」，意思是「3 个他的第一把尺加 2 个他的第二把尺」。$B$ 是把他的话翻译成我们的话的翻译官，$B^{-1}$ 翻译回去。要让他的坐标系里做一个变换：**先翻译成我们的话（$B$），用我们的方法做（$M$），再翻译回去（$B^{-1}$）**，从右往左读 $B^{-1}MB$。

""" + C_CHANGE + r"""

读输出：对方基是 $\mathbf{b}_1=(2,1)$、$\mathbf{b}_2=(-1,1)$，他说的 $(3,2)$ 在我们这里是 $3(2,1)+2(-1,1)=(4,5)$，再用 $B^{-1}$ 翻回来得到 $(3,2)$。「逆时针转 90 度」这个变换，在他的坐标里变成了看起来完全不同的矩阵 $M_B$（元素是 0.333、$-0.667$、1.667、$-0.333$）；用两条路线算同一个向量，结果都是 $(-0.333, 4.333)$。最后一行验证：换基后迹仍是 0、行列式仍是 1，因为它们是**变换本身的性质**，不依赖坐标。

这件事和下一节直接相连：**对角化 $A=PDP^{-1}$ 就是选一组「恰好让矩阵变成对角」的基**，也就是 $B^{-1}MB$ 的特例。
"""),
  V("P2LTAUO1TdA", "视频三：Change of basis（线性代数的本质 第 13 章）", 13),
  T(r"""
### 特殊矩阵：对称、正交、旋转

> **标准定义 · 正交矩阵与标准正交基 (orthogonal matrix & orthonormal basis)**
>
> 若方阵 $Q$ 满足 $Q^\top Q=I$（等价于 $Q^{-1}=Q^\top$），就称为**正交矩阵 (orthogonal matrix)**；它的列是两两垂直的**单位向量**，称为**标准正交基 (orthonormal basis)**。正交矩阵保持长度和点积：$\|Q\mathbf{x}\|=\|\mathbf{x}\|$，$(Q\mathbf{x})\cdot(Q\mathbf{y})=\mathbf{x}\cdot\mathbf{y}$，行列式为 $\pm1$（$+1$ 是旋转，$-1$ 含反射）。**对称矩阵 (symmetric matrix)** 满足 $A^\top=A$。
>
> *English: Q is orthogonal if QᵀQ = I, i.e. its columns form an orthonormal basis. Orthogonal maps preserve lengths and angles; det = +1 means a rotation, −1 includes a reflection.*

**白话版：「刚体运动」。** 正交矩阵就是不拉伸、不压扁、只把整个空间当作刚体转一下（或照一下镜子）。**最大的好处：用标准正交基时，坐标就是点积，不用求逆。**

""" + C_ORTHO + r"""

读输出：$30^\circ$ 的旋转矩阵 $Q$ 满足 $Q^\top Q=I$，行列式为 1，逆等于转置；随机向量 $\mathbf{x}$ 的长度在旋转前后都是 0.1824，两个向量的点积旋转前后都是 0.0667（长度和夹角都保持）。关键对比：用 $Q$ 的列作基，坐标直接用点积得到 $(0.0428,-0.1773)$，和「解方程」的结果完全一样；但换成不垂直的基（列 $(1,0)$ 和 $(1,1)$），点积 $(0.1257,-0.0064)$ 就**不是**真实坐标 $(0.2578,-0.1321)$。最后，反射矩阵也满足 $F^\top F=I$，但行列式是 $-1$。

**对称矩阵**（$A^\top=A$）也值得记：协方差矩阵、$X^\top X$ 都是对称的，它们的特征值全是实数、特征向量可以选成互相正交（谱定理），下一节会用到。

### 一个小实验：高维几何与「概念方向」

这一节的最后，用两个实验把上面的工具用到 ARENA 后面真正会遇到的问题上。

""" + C_EXPER + r"""

读输出：**实验一**，随机取两个方向，夹角的余弦绝对值的平均：$d=2$ 时 0.645，$d=10$ 时 0.260，$d=100$ 时 0.078，$d=1000$ 时 0.025，大致按 $1/\sqrt{d}$ 缩小，**维度越高，随机方向越接近正交**。**实验二**：在只有 50 维的空间里放 200 个随机方向（比维数多得多），平均 $|\cos|$ 只有 0.112，最坏的一对也只有 0.51。这说明「比维数更多的、近似互相独立的方向」是可以塞得下的，这正是 ARENA 可解释性章节里 **叠加 (superposition)** 的几何基础：基最多只有 $d$ 个严格正交的方向，但近似正交的方向可以多得多。

**实验三**：两个「概念」强度独立，它们的方向是标准轴旋转后的一对正交方向 $f_1=(0.6,0.8)$ 和 $f_2=(-0.8,0.6)$。看**单个神经元**，神经元 1 同时和概念 1（相关 0.61）、概念 2（相关 $-0.79$）纠缠在一起，神经元 2 也一样；换到以 $f_1,f_2$ 为基的坐标，沿 $f_1$ 的坐标只和概念 1 相关（1.0 对 0.01），沿 $f_2$ 的只和概念 2 相关。**同一份数据，换一组基，结构就清晰了。** 如果网络的激活函数是逐元素的（如 ReLU），神经元的轴就是**特权基 (privileged basis)**，概念有机会对齐它；但像残差流这类没有逐元素操作的地方，没有哪组基是特殊的，要找概念就得「换基去找」。
"""),
  T(r"""
### 这一节你要带走的三句话

1. **基 = 线性无关 + 张成全空间**，$n$ 维空间的基恰好 $n$ 个；判断时看矩阵的秩或可逆性。
2. **点积衡量「顺路程度」**：$\mathbf{u}\cdot\mathbf{v}=\|\mathbf{u}\|\|\mathbf{v}\|\cos\theta$，余弦相似度只看方向；矩阵乘法就是一批点积。
3. **换基是翻译**：$\mathbf{x}=B\mathbf{c}$，变换变成 $B^{-1}MB$；正交矩阵的基最好用，逆就是转置，坐标就是点积。
"""),
  THINK(r"向量 $\mathbf{x}=(5,1)$，新基 $\mathbf{b}_1=(1,1)$、$\mathbf{b}_2=(1,-1)$。(a) 求 $\mathbf{x}$ 在新基下的坐标；(b) 这组基是不是标准正交基？如果不是，怎样改成标准正交基，坐标又会怎样变？", r"""
(a) $B=\begin{bmatrix}1&1\\1&-1\end{bmatrix}$，解 $B\mathbf{c}=\mathbf{x}$：$c_1+c_2=5$，$c_1-c_2=1$，得 $\mathbf{c}=(3,2)$。验证：$3(1,1)+2(1,-1)=(5,1)$。

(b) 两个向量点积 $1\cdot1+1\cdot(-1)=0$，垂直；但长度都是 $\sqrt2$，不是单位向量，所以只是**正交基**。把它们各除以 $\sqrt2$ 就成了标准正交基，此时坐标就是点积：$\mathbf{x}\cdot\hat{\mathbf{b}}_1=6/\sqrt2\approx4.243$，$\mathbf{x}\cdot\hat{\mathbf{b}}_2=4/\sqrt2\approx2.828$。基向量缩短了 $\sqrt2$ 倍，坐标就放大了 $\sqrt2$ 倍（$3\sqrt2\approx4.243$，$2\sqrt2\approx2.828$）。
"""),
  THINK(r"余弦相似度和点积，在比较两个文档向量时各自有什么好处和坏处？如果所有向量都已经归一化成长度 1，两者还有区别吗？", r"""
**点积**同时受方向和长度影响：好处是长度可以携带「强度、置信度」之类的信息；坏处是长文档、范数大的向量会天然得分高。**余弦相似度**去掉了长度，只比较方向，所以更公平，但丢掉了长度里可能有用的信息。如果所有向量长度都是 1，点积 $=\|\mathbf{u}\|\|\mathbf{v}\|\cos\theta=\cos\theta$，两者**完全相同**。所以检索系统常常先把向量归一化，再用点积（实现上更快）。
"""),
  THINK(r"一层网络有 $d=768$ 个神经元。一个研究者发现某个「概念」对应的方向是 $\mathbf{f}=0.6\,\mathbf{e}_3+0.8\,\mathbf{e}_7$（$\mathbf{e}_i$ 是神经元轴）。他只看神经元 3 和神经元 7 的激活值，会漏掉什么？该怎么测量这个概念？", r"""
概念的强度应该是激活向量 $\mathbf{a}$ 在方向 $\mathbf{f}$ 上的坐标，即点积 $\mathbf{a}\cdot\mathbf{f}=0.6a_3+0.8a_7$（$\mathbf{f}$ 是单位向量，因为 $0.6^2+0.8^2=1$）。单独看 $a_3$ 或 $a_7$，每一个都只含有概念信号的一部分，而且还混着别的概念的贡献（上面实验三里神经元 1 同时与两个概念相关）。正确做法是**换基**，把 $\mathbf{f}$ 当作一条新坐标轴再读数。如果网络有很多这样的概念方向，而且数量超过 768，它们只能近似正交，这就是叠加；那时即使换成某一组基也不能同时把所有概念分开。
"""),
  KW(("线性组合","linear combination","数乘再相加：$c_1\\mathbf{v}_1+c_2\\mathbf{v}_2$"),
     ("张成空间","span","所有线性组合构成的集合"),
     ("线性无关 / 线性相关","linearly independent / dependent","有没有「多余」的向量"),
     ("基","basis","线性无关且张成整个空间的一组向量"),
     ("维数","dimension","基里向量的个数"),
     ("秩","rank","线性无关的列的个数，也是像空间的维数"),
     ("点积","dot product","$\\sum_i u_iv_i=\\|\\mathbf{u}\\|\\|\\mathbf{v}\\|\\cos\\theta$"),
     ("L2 范数","L2 norm","向量长度 $\\sqrt{\\sum_i u_i^2}$"),
     ("正交","orthogonal","点积为 0，互相垂直"),
     ("余弦相似度","cosine similarity","只看方向的相似度，范围 $[-1,1]$"),
     ("投影","projection","一个向量在另一个方向上的「影子」"),
     ("基变换","change of basis","$\\mathbf{x}=B\\mathbf{c}$，变换变成 $B^{-1}MB$"),
     ("正交矩阵","orthogonal matrix","$Q^\\top Q=I$，保持长度和夹角"),
     ("标准正交基","orthonormal basis","两两垂直的单位向量，坐标就是点积"),
     ("特权基 / 叠加","privileged basis / superposition","神经元轴是否特殊；比维数更多的概念方向近似正交地挤在一起"),
  ),
 ],
 "references": [
  {"title": "ARENA [0.0] Prerequisites — Linear Algebra 部分", "url": "https://github.com/ARENA-education/ARENA_materials/blob/main/chapter0_fundamentals/instructions/pages/00_%5B0.0%5D_Prerequisites.md", "note": "「基与基变换」「不同类型的矩阵」两条（讲解为自写，未转载原文）"},
  {"title": "3Blue1Brown：Essence of Linear Algebra 全系列", "url": "https://www.youtube.com/playlist?list=PLZHQObOWTQDPD3MizzM2xVFitgF8hE_ab", "note": "本节三集视频所在的完整系列"},
  {"title": "NumPy 文档：numpy.linalg（matrix_rank、solve、inv、lstsq）", "url": "https://numpy.org/doc/stable/reference/routines.linalg.html", "note": "本节代码用到的线性代数函数"},
  {"title": "MIT 18.06 Linear Algebra（Gilbert Strang）", "url": "https://ocw.mit.edu/courses/18-06-linear-algebra-spring-2010/", "note": "选看：线性代数的标准大学课程，对应基、正交、基变换各讲"},
 ],
 "quiz": {"questions": QUIZ},
}

if __name__ == '__main__':
    dump(unit, "arena-0.0", "u05-bases.json")
