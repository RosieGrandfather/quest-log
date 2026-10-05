"""dl-0 第 1 节：卷积神经网络（v3 格式，直接按 ≤50 分钟写）"""
from unitlib import *
from dl01c import *
from dl01_quiz import QUIZ

unit = {
 "id": "u01",
 "title": "卷积神经网络",
 "en": "Convolutional Neural Networks",
 "minutes": 50,
 "objectives": [
  "说清图像为什么不适合直接用全连接层：会算 $224\\times224\\times3$ 输入接 1000 个神经元的参数量，并解释 **局部连接 (local connectivity)**、**参数共享 (parameter sharing)** 与 **平移等变性 (translation equivariance)**",
  "手写单通道的 **卷积（互相关）(convolution / cross-correlation)**，用边缘检测核验证；会用 **步幅 (stride)** 与 **填充 (padding)** 的输出尺寸公式 $\\lfloor (n+2p-k)/s\\rfloor+1$，并用循环验证它",
  "理解 **多输入通道、多卷积核**：权重形状 $(C_{out},C_{in},k,k)$，手算 **参数量** 与 **乘加次数 (MACs)**，并和 PyTorch 的 `nn.Conv2d` 对照",
  "手写 **最大池化 (max pooling)**，会用递推公式计算多层堆叠后的 **感受野 (receptive field)**",
  "能逐层追踪一个最小 CNN（卷积 → ReLU → 池化 → 展平 → 线性）的输出形状与参数量，并说出 LeNet 到 VGG 的设计趋势",
 ],
 "blocks": [
  T(r"""
### 先说这一小节要干什么

上一阶段你用全连接层（MLP）做过分类：输入是一个向量，每一层都是「矩阵乘法 + 非线性」。可图像不是普通的向量：它有**空间结构**，相邻像素有关系，同一个物体出现在左上角或右下角还是同一个物体。卷积神经网络 (CNN) 就是把这两点写进网络结构里。这一小节把 CNN 的零件从头手写一遍：卷积、步幅与填充、多通道、池化、感受野，最后把它们堆成一个最小的 CNN，只追踪每一层的形状和参数量。

**开始之前你要会：**

- ml-0「神经网络与训练实践」里的全连接层、ReLU、参数量的数法；
- arena-0.0「线性变换与矩阵乘法」「非方阵与形状规则」里的矩阵乘法与形状规则；
- arena-0.0「Python 与 NumPy 基础」里的数组形状、切片、`reshape`，以及「PyTorch 入门：张量与自动求导」里 `nn.Module` 的基本用法。

**学完它你就能看懂这几件事：**

- 论文和代码里 `Conv2d(64, 128, kernel_size=3, stride=2, padding=1)` 每个数字是什么，输出形状和参数量怎么手算；
- 「这一层有多少 FLOPs、多少 MACs」这类说法是怎么数出来的；
- 为什么现代网络几乎只用 $3\times3$ 的小核、一路堆叠，而不是一个大核；
- 后面残差网络、迁移学习，甚至把图像切块送进 Transformer 的做法，都建立在这里的形状与参数量计算上。

**本小节安排（约 50 分钟）**：导读（2 分钟）→ 视频（15 分钟）→ 为什么图像不用全连接（5 分钟）→ 卷积运算、步幅与填充（8 分钟）→ 多通道与多卷积核（7 分钟）→ 池化与感受野（6 分钟）→ 把它们堆起来（4 分钟）→ 总结与「想一想」（3 分钟）。

**怎么学：** 代码块在页面里可以「▶ 运行」，只用 numpy，按顺序运行，后面的块直接用前面定义的函数（`conv2d`、`out_size`、`conv_layer` 等）。标明「只显示」的 PyTorch 对照块没有运行按钮，输出是在装了 PyTorch 的环境里真实运行得到的。训练一个 CNN 不在本小节，后面的小节和项目会做；这里只做前向计算。
"""),
  V("HGwBXDKFk9I", "视频：Neural Networks Part 8: Image Classification with Convolutional Neural Networks (CNNs)（StatQuest with Josh Starmer）", 15),
  T(r"""
**看视频时留意三个词：** 滤波器 (filter)、池化 (pooling)、展平后接全连接层。它们就是下面要手写的卷积核、`max_pool2d` 和最后一层线性层；先有直观印象，再看公式和代码。

### 为什么图像不用全连接

先算一笔账：一张 $224\times224$ 的彩色图有 $224\times224\times3=150528$ 个数。如果把它展平，接一个有 1000 个神经元的全连接层，每个神经元要连到全部输入。
""" + C_PARAMS + r"""

**读输出：** 仅这一层就有 `150529000` 个参数（约 1.5 亿），按 float32 存储约 `602` MB，还没有任何「深度」。相比之下，64 个 $3\times3$ 卷积核只有 `1792` 个参数，相差约 8.4 万倍；而且它的输出是 $64\times224\times224=$ `3211264` 个数，远比 1000 个多。如果用全连接层得到同样大小的输出，需要 `483388358656` 个参数（约 $4.8\times10^{11}$），根本不可能训练。省下这么多参数靠的是对图像的两条假设：

> **标准定义 · 局部连接与参数共享 (local connectivity & parameter sharing)**
>
> **局部连接**：输出的每个位置只依赖输入中一个小窗口（核的大小 $k\times k$），而不是整张图。**参数共享**：同一个卷积核在所有空间位置重复使用同一组权重。因此一层的参数量只取决于核的大小与通道数，与图像的高和宽无关。
>
> *English: Each output unit depends only on a small local window of the input, and the same kernel weights are reused at every spatial position, so the parameter count is independent of image size.*

**白话版：「同一个放大镜扫遍整张照片」。** 找一道竖线，不需要每个位置各配一个专门的检测器，用同一个「竖线放大镜」从左到右、从上到下扫一遍就行。

> **标准定义 · 平移等变性 (translation equivariance)**
>
> 设 $T_\delta$ 表示把图像平移 $\delta$ 的算子。若 $f(T_\delta x)=T_\delta f(x)$，则称 $f$ 对平移**等变**；若 $f(T_\delta x)=f(x)$，则称对平移**不变 (invariant)**。卷积层（忽略边界）是平移等变的。
>
> *English: A map f is translation equivariant if shifting the input shifts the output by the same amount; it is invariant if the output does not change at all.*

**白话版：「物体挪了位置，检测结果跟着挪，但内容不变」。** 下面先写出卷积本身，再验证这一点。

### 卷积（互相关）运算

> **标准定义 · 二维卷积（互相关）(2D convolution / cross-correlation)**
>
> 输入 $x\in\mathbb R^{H\times W}$，卷积核 $K\in\mathbb R^{k_h\times k_w}$，步幅 $s$，则输出
>
> $$y[i,j]=\sum_{u=0}^{k_h-1}\sum_{v=0}^{k_w-1}x[si+u,\,sj+v]\,K[u,v]$$
>
> 即核在输入上滑动，每个位置做「对应相乘再求和」。严格的数学卷积要先把核上下左右翻转，深度学习库（包括 PyTorch）实现的其实是上式的**互相关**，仍然叫「卷积」；核的权重是学出来的，翻不翻转不影响能学到什么。
>
> *English: A convolution layer slides a kernel over the input and, at each position, sums the elementwise products of the kernel and the window; deep-learning libraries implement cross-correlation (no kernel flip).*

**白话版：「拿一块小模板在图上滑，看哪里和模板最像」。** 模板（核）和窗口越相似，求和得到的数越大。下面用一个竖直边缘核（左边减右边）检验：图像左半是 0、右半是 1。
""" + C_CORR + r"""

**读输出：** 输入是 $6\times6$，核是 $3\times3$，没有填充、步幅 1，所以输出是 $4\times4$。平坦的区域（窗口里全是 0 或全是 1）响应是 `0`；只有窗口跨过那条竖直边的两列响应是 `-3`（窗口左列全是 0、右列全是 1，$0-3=-3$）。核的符号决定边的方向：取负号核就得到 `3`。**一个只有 9 个数的核，把「竖直边在哪里」检测出来了**，这就是卷积核做的事：检测某种局部模式。
""" + C_EQUIV + r"""

**读输出：** `b` 是 `a` 整体向左挪一列，两者的输出都是 $6\times6$；`yb[:, :-1]` 与 `ya[:, 1:]` 完全相同，输出也跟着挪了一列，这就是平移等变性。`9` 个参数在全部位置共用，参数共享也体现在这里。

> **标准定义 · 步幅与填充 (stride & padding)**
>
> **步幅 $s$**：核每次滑动的格数；**填充 $p$**：在输入四周各补 $p$ 圈 0。输入边长 $n$、核边长 $k$ 时，输出边长为
>
> $$n_{\text{out}}=\left\lfloor\frac{n+2p-k}{s}\right\rfloor+1$$
>
> *English: With input size n, kernel size k, padding p and stride s, the output size is floor((n + 2p − k)/s) + 1.*

**白话版：「窗口能放下几次」。** 补完 0 后边长是 $n+2p$，窗口的左端从 0 开始，每次走 $s$ 格，最后一个窗口的左端不能超过 $n+2p-k$，所以能放下 $\lfloor(n+2p-k)/s\rfloor+1$ 次。常用的「same」填充是 $s=1,\;p=(k-1)/2$（$k$ 为奇数），输出和输入一样大。
""" + C_SIZE + r"""

**读输出：** 对 8×5×3×3=`360` 组不同的 $(n,k,p,s)$，用循环实际跑出的输出边长和公式完全一致。三个例子：$224$ 输入、$7\times7$ 核、$p=3,s=2$ 得到 `112`（这是很多网络的第一层）；$32$、$k=3,p=1,s=1$ 得到 `32`；$28$、$k=5$、无填充得到 `24`。最后一行 `True`：$k=3,p=1,s=1$ 时任何边长都保持不变。向下取整的含义是：窗口放不满的边角直接丢掉。

### 多输入通道与多个卷积核

真实图像有 3 个通道，中间层的特征图有几十上百个通道。

> **标准定义 · 多通道卷积层 (multi-channel convolution layer)**
>
> 输入 $X\in\mathbb R^{C_{in}\times H\times W}$，权重 $W\in\mathbb R^{C_{out}\times C_{in}\times k\times k}$，偏置 $b\in\mathbb R^{C_{out}}$，则
>
> $$Y[o,i,j]=b_o+\sum_{c=1}^{C_{in}}\sum_{u,v}X[c,\,si+u,\,sj+v]\,W[o,c,u,v]$$
>
> 参数量为 $C_{out}(C_{in}k^2+1)$；每个输出元素要做 $C_{in}k^2$ 次乘加，所以总**乘加次数 (MACs, multiply-accumulate operations)** 为 $C_{out}H_{out}W_{out}C_{in}k^2$（浮点运算数 FLOPs 约是它的 2 倍）。
>
> *English: A convolution layer has C_out kernels, each spanning all C_in input channels; it has C_out(C_in k² + 1) parameters and C_out H_out W_out C_in k² multiply-accumulates.*

**白话版：「每个输出通道有自己的一组模板，每组模板要同时看所有输入通道」。** 一个核是一个 $C_{in}\times k\times k$ 的小立方体；$C_{out}$ 个核就产生 $C_{out}$ 张新的特征图。
""" + C_MULTI + r"""

**读输出：** 输入 `(3, 8, 8)`，4 个 $3\times3\times3$ 的核，$p=1$ 保持边长，输出形状 `(4, 8, 8)`。参数量 $4\times3\times9+4=$ `112`，乘加次数 $4\times8\times8\times27=$ `6912`，与代码里数出来的一致。注意参数量和输入的高宽无关，而乘加次数与输出的高宽成正比。
""" + C_MACS + r"""

**读输出：** 第一行 `(112, 6912)` 就是上一块的例子，手算和公式一致。第二行是常见的第一层（$3\to64$，$7\times7$，$s=2$，$p=3$）：输出边长 `112`，参数 `9472`，乘加约 `118013952`（1.18 亿）。第三行是 $56\times56$ 特征图上的一层 $3\times3$、$64\to64$：参数只有 `36928`，乘加却有 `115605504`（约 1.16 亿）。**卷积层的参数少、计算量大**：计算量随特征图变大而增加，参数不会。另外，核大小 $k=1$ 的「$1\times1$ 卷积」只在通道之间做线性组合，不看空间邻居。

下面与 PyTorch 对照（只显示，不在网页里运行）：PyTorch 的张量布局是 `(N, C, H, W)`，权重形状正是 $(C_{out},C_{in},k,k)$。
""" + C_TORCH + r"""

**读输出：** `F.conv2d` 的结果与手写的 `conv_layer` 在数值上一致（`True`）；`nn.Conv2d(3, 4, 3, padding=1)` 的权重形状是 `(4, 3, 3, 3)`，偏置 `(4,)`，参数共 `112`，与手算相同。

### 池化与感受野

> **标准定义 · 最大池化 (max pooling)**
>
> 在每个通道上，把输入切成大小 $k\times k$ 的窗口（步幅默认等于 $k$），每个窗口只保留最大值。它**没有可学习参数**，不改变通道数，窗口 $2\times2$、步幅 2 时空间边长减半。
>
> *English: Max pooling keeps the maximum value in each window, per channel; it has no learnable parameters and downsamples the spatial size.*

**白话版：「每个小区域只留最强的信号」。** 既减小了后面各层的计算量，也让输出对窗口内的小位移不敏感。
""" + C_POOL + r"""

**读输出：** $4\times4$ 的输入变成 $2\times2$：四个窗口的最大值依次是 `4 5 / 6 8`。第二问把左上窗口里的最大值 4 挪到同一窗口的另一格，池化结果完全不变（`True`），这就是池化带来的**局部平移不变性**；只在窗口范围内成立，把 4 挪到别的窗口就变了。

一层卷积只能看到 $k\times k$ 的窗口，但网络越深，一个输出位置能「间接看到」的输入区域越大。

> **标准定义 · 感受野 (receptive field)**
>
> 某一层上一个位置所依赖的**输入像素区域**的边长，叫这个位置的感受野。设第 $l$ 层的核大小为 $k_l$、步幅为 $s_l$，令 $r_0=1,\;j_0=1$（$j$ 是相邻两个输出位置在输入上的间距），则
>
> $$r_l=r_{l-1}+(k_l-1)\,j_{l-1},\qquad j_l=j_{l-1}\,s_l$$
>
> 池化层同样按核大小和步幅代入。以上是忽略填充的理论值；实践中中心像素的影响远大于边缘，**有效感受野**通常比理论值小。
>
> *English: The receptive field of a unit is the region of the input that can influence it; it grows by (k − 1) times the cumulative stride at each layer.*

**白话版：「越往后，一个点『看』得越广」。** 每多一层 $k\times k$，向外多看 $(k-1)$ 个「当前间距」；步幅会让间距变大，之后的层看得更快。
""" + C_RF + r"""

**读输出：** 网络「卷积3 → 卷积3 → 池化2（步幅2）→ 卷积3」的感受野是 `10`，间距 $j=2$：前两层得到 $r=5$，池化后 $r=6,j=2$，最后一层 $r=6+2\times2=10$。三个步幅 1 的 $3\times3$ 卷积与一个 $7\times7$ 卷积的感受野都是 `7`。下面用扰动实验验证（池化换成线性的平均池化，方便检测）：逐个扰动输入像素，看输出位置 $(4,4)$ 是否变化。
""" + C_RFCHECK + r"""

**读输出：** 输入 $24\times24$，输出 $8\times8$。会影响输出 $(4,4)$ 的输入像素共 `100` 个，行和列都恰好是 `8` 到 `17`，是一个 $10\times10$ 的方块，与公式算出的感受野 10 一致。

### 把它们堆起来：最小 CNN 与设计趋势

最小的 CNN 是「卷积 → ReLU → 池化 → 展平 → 线性」。我们只做前向，逐层追踪形状和参数量（权重是随机的，不训练）。
""" + C_STACK + r"""

**读输出：** 输入 `(1, 28, 28)`：卷积（1→8，$3\times3$，$p=1$）输出 `(8, 28, 28)`，参数 $8\times9+8=$ `80`；ReLU 不改形状；$2\times2$ 池化把空间减半成 `(8, 14, 14)`；展平成 $8\times14\times14=$ `1568` 维；线性层 $1568\to10$ 有 $1568\times10+10=$ `15690` 个参数。总共 `15770`，**绝大部分参数在最后的全连接层**，卷积层本身只有 80 个。
""" + C_STACKT + r"""

**读输出：** 同样的结构用 `nn.Sequential` 搭出来，每层输出形状（多了 batch 维）与手写版完全对应；把手写版的权重拷进去后，输出与手写的 `logits` 一致（`True`），总参数量也是 `15770`。

**LeNet → VGG 的设计趋势。** 早期的 LeNet（1998，手写数字识别）就是「卷积 + 池化」重复几次、最后接全连接层，参数量在几万量级。后来的 VGG（2014）把这条路线推到规整：全部使用 $3\times3$ 卷积、$2\times2$ 最大池化，每经过一次池化，**空间边长减半、通道数翻倍**（$224\to112\to56\to28\to14\to7$，通道 $64\to128\to256\to512$）。这样设计有两个理由，下面用代码验证：
""" + C_SMALL + r"""

**读输出：** **小核堆叠**：两个 $3\times3$ 的感受野是 5、参数量 `73728`，比一个 $5\times5$（`102400`）少约 28%；三个 $3\times3$ 的感受野是 7，参数 `110592`，只有一个 $7\times7$（`200704`）的约 55%，而且中间多了非线性，表达能力更强。**通道翻倍、空间减半**：$64\times56\times56$ 变成 $128\times28\times28$ 后，一层 $3\times3$ 的乘加次数都是 `115605504`，每个阶段的计算量大致相同，网络变深时靠通道数「接住」被池化丢掉的空间分辨率。顺便手算：VGG-16 展平后是 $7\times7\times512=25088$ 维，接第一个 4096 的全连接层就有 $25088\times4096\approx1.03$ 亿个参数，这就是全连接层占去大部分参数的原因，后来的网络多用全局平均池化来替代它（下一小节的残差网络就是这样）。

### 这一小节你要带走的三句话

1. **图像用卷积是因为两条假设**：局部性与平移等变，换来参数共享；一层的参数量 $C_{out}(C_{in}k^2+1)$ 只取决于通道和核，与图像大小无关，计算量 $C_{out}H_{out}W_{out}C_{in}k^2$ 则随特征图变大。
2. **形状要会手算**：输出边长 $\lfloor(n+2p-k)/s\rfloor+1$，感受野递推 $r_l=r_{l-1}+(k_l-1)j_{l-1}$，权重形状 $(C_{out},C_{in},k,k)$，PyTorch 张量布局 `(N, C, H, W)`。
3. **经典设计**是小核堆叠、通道翻倍、空间减半，卷积提取特征、池化降采样、最后展平接线性层分类；大部分参数在全连接层，大部分计算在卷积层。
"""),
  THINK("**（计算）** 输入是 $3\\times32\\times32$ 的图，经过 `Conv2d(3, 16, kernel_size=5, stride=1, padding=0)`（带偏置）。求输出形状、参数量和乘加次数 (MACs)。", r"""
输出边长 $\lfloor(32+0-5)/1\rfloor+1=28$，所以输出形状是 $16\times28\times28$。

参数量：$16\times(3\times25+1)=16\times76=1216$。

乘加次数：$16\times28\times28\times(3\times25)=12544\times75=940800$。

注意：参数量只与 $C_{in},C_{out},k$ 有关；输入若换成 $64\times64$，参数量不变，乘加次数会随输出面积增加。
"""),
  THINK("**（概念辨析）** 同学说：「卷积层具有平移不变性，所以 CNN 能认出被挪动过的猫。」这句话哪里不严谨？", r"""
卷积层本身是**等变**的，不是不变的：输入平移，输出的特征图也跟着平移，内容并没有「不变」。（严格地说，步幅大于 1 时只对步幅整数倍的平移等变；填充与边界也会破坏它。）真正向**不变性**靠近的是后面的池化和最后的汇聚：窗口内的小位移被最大池化吸收，最终分类前再把空间信息汇总（展平后接线性层、或对整张图做全局池化），对位置的依赖才被削弱。而且这种不变性只是近似的，对大幅度平移、缩放、旋转，CNN 仍需靠数据增强来学。
"""),
  THINK("**（联系后续）** 后面会看到把图像切成 $16\\times16$ 的小块再送进 Transformer 的做法。切块并做线性映射，等价于一个 `Conv2d(3, 768, kernel_size=16, stride=16)`。对 $224\\times224$ 的输入，输出形状和参数量是多少？", r"""
输出边长 $\lfloor(224+0-16)/16\rfloor+1=14$，所以输出形状是 $768\times14\times14$，也就是 $14\times14=196$ 个块、每块一个 768 维的向量。

参数量：$768\times(3\times16\times16+1)=768\times769=590592$。

核大小等于步幅，窗口不重叠，每个小块只被映射一次，「切块 + 共享的线性映射」正是参数共享的卷积；这个例子说明本小节的形状和参数量公式，在非 CNN 的网络里同样有用。
"""),
  KW(("卷积（互相关）","convolution / cross-correlation","核在输入上滑动，每个位置做对应相乘再求和；深度学习库里不翻转核"),
     ("卷积核（滤波器）","kernel / filter","一组可学习权重，形状 $(C_{in},k,k)$，检测某种局部模式"),
     ("局部连接","local connectivity","每个输出只依赖输入中一个小窗口"),
     ("参数共享","parameter sharing","同一个核在所有空间位置用同一组权重"),
     ("平移等变性","translation equivariance","输入平移，输出特征图同样平移"),
     ("步幅","stride","核每次滑动的格数，大于 1 会缩小输出"),
     ("填充","padding","在输入四周补 0；$s=1,p=(k-1)/2$ 时尺寸不变"),
     ("特征图与通道","feature map & channel","卷积层输出的每个通道是一张特征图，形状 $(C,H,W)$"),
     ("乘加次数","multiply-accumulate (MAC)","$C_{out}H_{out}W_{out}C_{in}k^2$，FLOPs 约为其 2 倍"),
     ("最大池化","max pooling","窗口内取最大值，无参数，降低空间分辨率"),
     ("感受野","receptive field","一个输出位置所依赖的输入区域；递推 $r_l=r_{l-1}+(k_l-1)j_{l-1}$"),
     ("展平","flatten","把 $(C,H,W)$ 的特征图拉成一维向量，接全连接层"),
  ),
 ],
 "references": [
  {"title": "Stanford CS231n 课程笔记：Convolutional Neural Networks (CNNs / ConvNets)", "url": "https://cs231n.github.io/convolutional-networks/", "note": "本小节大纲依据：卷积层、输出尺寸公式、参数共享、池化、层的排列规律，只引用不转载"},
  {"title": "Goodfellow、Bengio、Courville《Deep Learning》第 9 章 Convolutional Networks", "url": "https://www.deeplearningbook.org/contents/convnets.html", "note": "作者免费公开；从卷积运算的动机（稀疏连接、参数共享、等变表示）讲到池化"},
  {"title": "Dive into Deep Learning (d2l.ai)：Convolutions for Images（卷积层、互相关、填充与步幅所在章节）", "url": "https://d2l.ai/chapter_convolutional-neural-networks/conv-layer.html", "note": "带可运行代码的版本，可对照本小节手写的 conv2d"},
  {"title": "Dive into Deep Learning (d2l.ai)：Convolutional Neural Networks (LeNet)", "url": "https://d2l.ai/chapter_convolutional-neural-networks/lenet.html", "note": "完整的 LeNet 结构与训练，训练部分会在后面的小节和项目里做"},
  {"title": "Simonyan & Zisserman, Very Deep Convolutional Networks for Large-Scale Image Recognition (VGG)", "url": "https://arxiv.org/abs/1409.1556", "note": "选看：小核堆叠与通道翻倍的原始论文"},
 ],
 "quiz": {"questions": QUIZ},
}

TARGET = [1, 3, 0, 2, 1]
for q, t in zip(unit["quiz"]["questions"], TARGET):
    q["options"][q["answer"]], q["options"][t] = q["options"][t], q["options"][q["answer"]]
    q["answer"] = t

if __name__ == '__main__':
    dump(unit, "dl-0", "u01-cnn.json", n_questions=5)
