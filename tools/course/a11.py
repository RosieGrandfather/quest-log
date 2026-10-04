"""ARENA 0.0 第 11 节：PyTorch（按 v3 格式重写，2026-10-04）"""
from unitlib import *
from a11c import C_TENSOR, C_AUTOGRAD, C_GRAPH, C_MODULE, C_SGD, C_TRAIN, C_LR
from a11_quiz import QUIZ

unit = {
 "id": "u11",
 "title": "PyTorch 入门：张量与自动求导",
 "en": "PyTorch Basics: Tensors & Autograd",
 "minutes": 100,
 "objectives": [
  "说清楚 **张量 (tensor)** 是什么：形状 (shape)、类型 (dtype)、设备 (device)；知道 `from_numpy`、`view` 与 `clone` 谁共用内存、谁是复制",
  "理解 **自动求导 (autograd)**：`requires_grad`、**计算图 (computational graph)**、`.backward()`；梯度存在 **叶子张量 (leaf tensor)** 的 `.grad` 里，而且会**累加**；会用有限差分验证梯度",
  "分清 `nn.Parameter`、`nn.Module`、**损失函数 (loss function)**、**优化器 (optimizer)** 各自的角色，能数出一个模型的参数个数",
  "能写出并读懂完整的 **训练循环 (training loop)** 五步，并验证 `optim.SGD` 就是手写的 $\\theta\\leftarrow\\theta-\\eta\\nabla$",
  "区分 **参数 (parameter)** 与 **超参数 (hyperparameter)**，用实验看学习率过小、过大、忘记 `zero_grad` 各自的后果",
 ],
 "blocks": [
  T(r"""
### 先说这一节要干什么

前面几节你用 NumPy 手写过前向传播，第 2 节学了反向传播的链式法则。真实的深度学习不会手写梯度：**PyTorch** 帮你记录前向计算、自动算出所有梯度，再由优化器更新参数。ARENA 第 0 章一开始就是 PyTorch 练习，它列出 7 个自测问题，如果能清楚回答，这一块就可以跳过：

1. 从高层看，`torch.Tensor` 是什么？
2. `nn.Parameter` 和 `nn.Module` 是什么？
3. 调用 `.backward()` 之后，梯度存在哪里？
4. 什么是损失函数？它一般接收什么参数、返回什么？
5. 优化算法做了什么？
6. 什么是超参数，它和普通参数有什么区别？
7. 举几个超参数的例子。

这一节按这 7 个问题展开，但不只是回答，而是把每个答案都放进代码里**真的运行一遍**，包括验证梯度对不对、手写优化器和 `torch.optim` 是否一致、让网络学会 XOR、对比学习率的影响。

**学完它你就能看懂这几件事：**

- ARENA 之后每一章里的 `class Foo(nn.Module)`、`loss.backward()`、`optimizer.step()` 各在做什么，为什么 `model.parameters()` 能找到所有权重；
- 「7B 模型」的 7B 是怎么数出来的：就是 `sum(p.numel() for p in model.parameters())`；
- 训练时 loss 不降、变成 `nan`、或者降得莫名其妙，最常见的三个原因（学习率、忘了 `zero_grad`、形状 / 类型错了）；
- 第 1 节那个「没有非线性就学不会 XOR」的实验，用 PyTorch 只要几行。

**本节安排（约 100 分钟）**：导读与视频一（8 分钟）→ 张量与视频二（30 分钟）→ 自动求导与视频三（30 分钟）→ `nn.Module`（10 分钟）→ 损失、优化器与训练循环（12 分钟）→ 超参数实验（5 分钟）→「想一想」。视频是英文的，可以打开中文字幕。代码需要 `pip install torch`（CPU 版即可）。
"""),
  V("ORMx45xqWkA", "视频一：PyTorch in 100 Seconds（Fireship）", 3),
  T(r"""
### 1. 张量：能上 GPU、能求导的数组

> **标准定义 · 张量 (tensor)**
>
> `torch.Tensor` 是一个**多维数组**，所有元素有同一个**数据类型 (dtype)**，存放在某个**设备 (device)** 上（`cpu` 或 `cuda`），形状 (shape) 由各维度的长度决定。它在 NumPy 数组的基础上多了两项能力：**可以在 GPU 上并行计算**，以及**可以记录计算过程用于自动求导**（`requires_grad`）。
>
> *English: A torch.Tensor is a multi-dimensional array with a single dtype, living on a device (cpu or cuda). Compared with a NumPy array it can run on GPUs and can record the computation for automatic differentiation.*

**白话版：「会记账的 NumPy 数组」。** 数值计算两者几乎一样；区别是张量可以搬到 GPU 上算得更快，还会把每一步运算「记账」，之后才能倒着把账算回去求梯度。大部分操作和 NumPy 同名，常见差别：`axis` 叫 `dim`，`copy()` 叫 `clone()`，默认浮点类型是 `float32`（NumPy 是 `float64`）。

""" + C_TENSOR + r"""

读输出：**一**，`x` 的形状是 `(2, 3)`，类型 `float32`，在 `cpu` 上；`t.tensor([1, 2, 3])` 和 `t.arange(5)` 默认是 `int64`，`t.randn` 默认是 `float32`。**二**，`dim=0` 沿行方向压缩（每列求和，`[5, 7, 9]`），`dim=1` 沿列方向压缩（每行求和，`[6, 15]`），和 NumPy 的 `axis` 一样。**三，共用内存**：`t.from_numpy(a)` 没有复制数据，改 `a[0]` 后张量 `b` 的第一个数也变成 100；注意 `b` 是 `float64`，因为 NumPy 数组默认就是 64 位浮点；`b.clone()` 才是真复制，之后再改 `a[1]` 为 -1，`b` 变了而 `c` 保持 `[100, 2, 3]`。**四**，`x.view(3, 2)` 也是同一块内存的另一种「看法」，改 `v[0, 0]` 为 99 后 `x[0, 0]` 也是 99.0；`x.is_contiguous()` 为 `True` 而 `x.T.is_contiguous()` 为 `False`，转置只是改了「怎么读」内存，没有搬数据，所以对转置后的张量不能直接 `view`（要先 `.contiguous()` 或改用 `reshape`）。**五**，同样的 0.1，在 `float32` 里存成 0.10000000149011612，`float64` 里才是 0.1：深度学习默认用 `float32`，所以比较两个张量要用 `t.allclose`，不要用 `==`。
"""),
  V("exaWOE8jvy8", "视频二：PyTorch Tutorial 02 - Tensor Basics（Patrick Loeber）", 18),
  T(r"""
### 2. 自动求导：梯度存在哪里

> **标准定义 · 自动求导 (autograd)**
>
> 对设置了 `requires_grad=True` 的张量，PyTorch 在前向计算时把每一步运算记录成一张**计算图 (computational graph)**：节点是张量，边是运算。对一个**标量**张量 $L$ 调用 `L.backward()`，PyTorch 沿计算图**反向**应用链式法则，求出 $L$ 对每个叶子张量 $\theta$ 的偏导数，**累加**到它的 `.grad` 属性里（$\theta$.grad $\mathrel{+}=\partial L/\partial\theta$）。**叶子张量**指用户直接创建、不是由别的运算算出来的张量，例如参数本身。
>
> *English: For tensors with requires_grad=True, PyTorch records each operation in a computational graph. Calling backward() on a scalar L applies the chain rule in reverse and accumulates ∂L/∂θ into θ.grad for every leaf tensor θ.*

**白话版：「边算边记账，最后倒着对账」。** 前向计算时，PyTorch 偷偷记下「这个数是由哪些数、做了什么运算得到的」；`backward()` 就是顺着账本倒推：最后一步对前一步的影响是多少，再乘上前一步对更前一步的影响……这就是第 2 节讲的反向传播，只是由 PyTorch 代你完成。

""" + C_AUTOGRAD + r"""

读输出：$y=w^2+2w$ 在 $w=3$ 处等于 15；`y.grad_fn` 的类型是 `AddBackward0`，意思是「y 是由一次加法算出来的」（这就是计算图的一个节点）；反向之前 `w.grad` 是 `None`。`y.backward()` 之后 `w.grad` 是 8，与 $dy/dw=2w+2=8$ 一致。**第二次**重新算 `y2` 并反向，`w.grad` 变成 16，**不是 8，而是 8+8：梯度默认累加，不会自动清零**，所以训练循环里每一步都要先清零（`zero_()` 之后回到 0）。最后用有限差分验证 autograd：$f(v)=v^3-2v$ 在 $v=1.5$ 的真实导数 $3v^2-2=4.75$，autograd 给出 4.75，中心差分 $\frac{f(v+\epsilon)-f(v-\epsilon)}{2\epsilon}$ 也得到 4.75（用 `float64`，否则精度不够）。**这个「autograd 对有限差分」的检查，是以后你自己写新运算时验证梯度的标准方法。**

""" + C_GRAPH + r"""

读输出：**一**，对向量参数 `x`，标量损失 $L=\sum x_i^2$ 的梯度是 $2x=[2,4,6]$，与输出一致，此时 `L` 为 14.0（$1+4+9$）。**二**，对非标量 `z = 2x` 直接 `backward()` 会抛 `RuntimeError: grad can be implicitly created only for scalar outputs`：多个输出对多个参数有一张雅可比矩阵，PyTorch 不知道你要哪种组合；传入权重 `t.ones(3)` 就是「把三个输出直接加起来再求导」，每个分量得到 2，累加到之前的 $[2,4,6]$ 上变成 $[4,6,8]$（再次印证「累加」）。**三**，`a` 是叶子（`True`），`b = a * 3` 不是叶子（`False`）但仍记录梯度（`True`）；`.grad` 只保存在叶子上。**四**，`with t.no_grad():` 里算出的 `c` 不记录计算（`requires_grad=False`），`detach()` 把张量从图里摘出来，结果同样不再求导：推理、以及手动更新参数时都要关掉记录，否则会白白占内存、还可能把更新步骤错误地算进图里。**五**，整数张量不能求导，因为导数需要连续的数。
"""),
  V("M0fX15_-xrY", "视频三：The Fundamentals of Autograd（PyTorch 官方）", 14),
  T(r"""
### 3. nn.Parameter 与 nn.Module：把参数管起来

> **标准定义 · nn.Parameter 与 nn.Module**
>
> **`nn.Parameter`** 是 `Tensor` 的子类，默认 `requires_grad=True`；把它（或含有它的子模块）赋值为某个 `nn.Module` 的属性时，会被自动**登记**为该模块的**可训练参数**。**`nn.Module`** 是所有网络层和模型的基类：在 `__init__` 里创建子层和参数，在 `forward` 里写「输入如何变成输出」，调用 `model(x)` 时会执行 `forward`；`model.parameters()` 会**递归**地返回所有登记过的参数，`state_dict()` 则按名字保存它们的值。
>
> *English: nn.Parameter is a Tensor subclass with requires_grad=True that is automatically registered as a trainable parameter when assigned as an attribute of an nn.Module. nn.Module is the base class for layers and models: define sub-layers in __init__ and the computation in forward; parameters() lists all registered parameters recursively.*

**白话版：「一个有登记册的积木盒」。** 模块是盒子，里面的层和参数是积木；只要你按规矩把积木放进盒子（赋值为属性），盒子就把它记在登记册上。之后优化器只要拿到登记册 `model.parameters()`，就知道要更新谁；保存模型只要抄一份登记册 `state_dict()`。不在登记册上的普通张量（下面的 `note`），优化器看不见，也就永远不会被训练。

""" + C_MODULE + r"""

读输出：模型一共 5 组参数：`fc1.weight` 形状 `(8, 4)`（还是第 1 节的约定：行数 = 本层神经元数）、`fc1.bias`、`fc2.weight`、`fc2.bias`、再加我们额外放的 `scale`，总数 $32+8+8+1+1=50$，与手算的 $(4\times8+8)+(8\times1+1)+1$ 一致。参数的名字（`fc1.weight`）就是 `state_dict` 的键，保存和加载模型靠的就是这些名字。普通张量 `note` 没有被登记（`False`）。`model(t.randn(5, 4))` 得到 `(5, 1)`：5 个样本、每个一个输出，所以 `forward` 默认是「批量在第一维」。注意 `nn.Linear(4, 8)` 内部做的是 `x @ weight.T + bias`，和第 1 节批量前向传播的写法一致。

### 4. 损失函数、优化器与训练循环

> **标准定义 · 损失函数与优化器 (loss function & optimizer)**
>
> **损失函数**接收**模型输出**和**目标 (target)**，返回一个**标量**张量（形状 `torch.Size([])`），值越小越好，如 `nn.MSELoss()`、`nn.CrossEntropyLoss()`。**优化器**拿到参数列表，在每次 `step()` 时读取各参数的 `.grad` 并按规则更新参数：最简单的 **SGD** 是 $\theta\leftarrow\theta-\eta\,\nabla_\theta L$，常用的 **Adam** 还会为每个参数维护动量和自适应的步长。
>
> *English: A loss function takes the model output and the target and returns a scalar tensor, smaller is better. An optimizer reads each parameter's .grad on step() and updates it: plain SGD uses θ ← θ − η∇L, while Adam adds momentum and per-parameter adaptive step sizes.*

**白话版：「裁判打分，教练改动作」。** 损失函数是裁判，给这一轮表现打一个分；`backward()` 把「每个动作对扣分的责任」算出来（梯度）；优化器是教练，按责任大小调整每个动作。**训练循环固定五步：前向 → 算损失 → 清梯度 → 反向 → 更新。**

先验证「优化器没有魔法」：下面分别用手写更新和 `torch.optim.SGD` 训练同一个线性回归，初始参数相同、数据相同，两个结果必须一致。

""" + C_SGD + r"""

读输出：手写版本（在 `no_grad` 里对每个参数做 `p -= lr * p.grad`）与 `optim.SGD` 训练出的参数**完全一致**（`allclose` 为 `True`）：`optimizer.step()` 的本质就是 $\theta\leftarrow\theta-\eta\nabla$。真实规律是权重 $[1,-2,0.5]$、偏置 $0.3$，50 步后学到 $[0.982,-1.989,0.482]$ 和 $0.308$，已经很接近，最终损失 0.00037。注意手写更新要放在 `with t.no_grad():` 里，否则「更新参数」这个动作本身也会被记进计算图。

再来第 1 节的老朋友：XOR。这次用 `nn.Sequential`、`Adam` 和上面的五步，对比隐藏层有无 ReLU，各试 5 个随机种子：

""" + C_TRAIN + r"""

读输出：有 ReLU 的网络 5 个种子**全部**学会，最终损失都小于 $10^{-8}$，四个输出是 `[0. 1. 1. 0.]`，正好是 XOR；没有 ReLU 的网络 5 个种子损失全部卡在 0.25，四个输出都是 0.5：整个网络只是一个线性函数，对这四个点最好的做法就是全猜 0.5。这与第 1 节的 NumPy 实验结论一致，现在只需要几行 PyTorch，梯度也不用自己推。训练循环里每一行的作用都要能说出来：少了 `zero_grad` 梯度会累加，少了 `backward` 参数不会变，少了 `step` 梯度算了没人用。

### 5. 参数 vs 超参数

> **标准定义 · 参数与超参数 (parameter vs hyperparameter)**
>
> **参数**是模型通过训练从数据中**学出来**的数值（权重、偏置），由优化器根据梯度更新。**超参数**是训练开始前由人**设定**、不被梯度下降更新的量，例如学习率、批量大小 (batch size)、训练轮数 (epochs)、层数和每层宽度、优化器的选择、权重衰减 (weight decay)、dropout 比例。
>
> *English: Parameters are learned from data by the optimizer; hyperparameters are set by the practitioner before training and are not updated by gradient descent, e.g. learning rate, batch size, number of epochs, depth and width, optimizer choice, weight decay, dropout rate.*

**白话版：「身体和训练计划」。** 肌肉是练出来的（参数），一周练几次、每次练多久是教练定的（超参数）。判断标准只有一条：**会不会被优化器根据梯度自动改**。

用一个小实验看超参数的威力：数据是 $y=2x+1$ 加噪声，同一个模型、同样 30 步 SGD，只改学习率，再看看忘了 `zero_grad` 会怎样。

""" + C_LR + r"""

读输出：真实规律是 $w=2,b=1$，噪声标准差 0.1，所以损失最低大约在 $0.01$ 附近。**`lr=0.001` 太小**：30 步后 $w$ 才到 0.608，损失仍有 4.041，还远没学完；**`lr=0.05` 合适**：$w=1.942,b=0.961$，损失 0.01517；**`lr=0.5` 更快**：$w=1.988,b=1.016$，损失 0.008362（略低于噪声水平，说明它已经开始贴合这 100 个点的噪声）；**`lr=1.05` 发散**：损失涨到 $1.596\times10^6$，$w$ 冲到 $-1344$。这个临界值不是巧合：这里损失对 $w$ 的曲率约为 2（因为 $x$ 的方差约为 1），与第 1 节 $C=(\theta-3)^2$ 的曲率一样，所以步长超过约 1 就发散。最后一行：**忘记 `zero_grad`**，同样 `lr=0.05`，损失停在 4.379，$w=3.18,b=2.32$，参数跑到了错误的地方：旧梯度越攒越大，就像悄悄把学习率放大又混入了过期的方向。

### 回到 ARENA 的 7 个问题

| 问题 | 一句话答案 |
|---|---|
| 1. 张量是什么 | 带 dtype / device 的多维数组，能上 GPU、能记录计算用于求导 |
| 2. `nn.Parameter` / `nn.Module` | 前者是会被自动登记的可训练张量；后者是层和模型的基类，在 `forward` 里写计算 |
| 3. `backward()` 后梯度在哪 | 各叶子张量（参数）的 `.grad` 里，会累加 |
| 4. 损失函数 | 输入模型输出和目标，返回标量，越小越好 |
| 5. 优化算法 | 用 `.grad` 更新参数，如 SGD：$\theta\leftarrow\theta-\eta\nabla$ |
| 6. 超参数 | 训练前人为设定、不被梯度更新的量 |
| 7. 举例 | 学习率、批量大小、轮数、层数 / 宽度、优化器、权重衰减、dropout 比例 |

### 这一节你要带走的三句话

1. **张量 = 带 dtype / device 的数组，能自动求导**；`from_numpy` 和 `view` 共用内存，`clone` 才是复制；浮点比较用 `allclose`。
2. **`backward()` 把梯度累加到叶子张量的 `.grad` 里**，所以训练循环固定五步：前向、损失、`zero_grad`、`backward`、`step`；`optim.SGD` 就是 $\theta\leftarrow\theta-\eta\nabla$。
3. **参数由优化器学出来，超参数由人设定**：学习率太小学不动，超过临界值就发散，忘记 `zero_grad` 会悄悄毁掉训练。
"""),
  THINK("**计算题**：`w = t.tensor(2.0, requires_grad=True)`，计算 `y = w ** 3 + 4 * w` 后调用 `y.backward()`，`w.grad` 是多少？如果接着再算一次同样的 `y` 并 `backward()`，不清零，`w.grad` 是多少？", r"""
$dy/dw = 3w^2 + 4 = 3\times4+4 = 16$，所以第一次得到 `tensor(16.)`。

第二次再反向，梯度**累加**：$16+16=32$。要得到干净的 16，必须在两次之间执行 `w.grad.zero_()`（训练时是 `optimizer.zero_grad()`）。可以用有限差分验证：$(f(2+\epsilon)-f(2-\epsilon))/2\epsilon\approx16$，其中 $f(w)=w^3+4w$。
"""),
  THINK("**概念辨析**：`t.from_numpy(a)`、`a_t.clone()`、`a_t.view(...)`、`a_t.detach()` 哪些与原数据共用内存？这在什么场景下会造成难以发现的 bug？", r"""
- `from_numpy(a)`：**共用**内存（改 NumPy 数组，张量跟着变）。
- `clone()`：**复制**，互不影响。
- `view(...)`：**共用**内存，只是换了形状的看法。
- `detach()`：**共用**内存，只是从计算图里摘下来（不再求导）。

典型 bug：把数据预处理里的张量 `detach()` 之后原地修改（如 `x[0] = 0`），原来的张量也被悄悄改了；或者把 `from_numpy` 得到的张量交给训练，同时 NumPy 那边又在原地更新同一个数组。需要独立副本时用 `clone()`（常写作 `x.detach().clone()`）。
"""),
  THINK("**和后续内容的联系**：一个有 $L$ 层、隐藏宽度 $d$ 的纯线性层堆叠，`model.parameters()` 的参数总数怎么算？如果现在想用 `float32` 保存一个 7B（$7\\times10^9$ 个参数）的模型，权重大约占多少显存？训练时用 Adam，还需要多存什么？", r"""
参数总数：每层 $d\times d+d$，共 $L(d^2+d)$（`sum(p.numel() for p in model.parameters())` 就是这个数）。

权重内存：每个 `float32` 占 4 字节，$7\times10^9\times4\text{ B}\approx28\text{ GB}$（`float16` / `bfloat16` 减半）。

用 Adam 训练还要存：**梯度**（与参数同样大，约 28 GB）和 Adam 的**两组动量**（一阶、二阶矩，各与参数同样大，约 56 GB）。所以训练时的显存大约是推理时的 4 倍以上（还不算激活值），这就是大模型训练需要很多 GPU 的原因之一。
"""),
  KW(("张量","tensor","带 dtype / device 的多维数组"),
     ("数据类型","dtype","如 `float32`、`int64`；默认浮点是 `float32`"),
     ("设备","device","`cpu` 或 `cuda`（GPU）"),
     ("视图","view","与原张量共用内存、只改形状的看法"),
     ("自动求导","autograd","沿计算图反向应用链式法则求梯度"),
     ("计算图","computational graph","前向计算时记录的运算节点和依赖关系"),
     ("叶子张量","leaf tensor","用户直接创建的张量，梯度存在它的 `.grad`"),
     ("梯度累加","gradient accumulation","`.grad` 不会自动清零，每次 backward 都累加"),
     ("参数（类）","nn.Parameter","会被模块自动登记的可训练张量"),
     ("模块","nn.Module","层和模型的基类，在 `forward` 里写前向计算"),
     ("损失函数","loss function","输出 + 目标 → 标量，越小越好"),
     ("优化器","optimizer","用梯度更新参数，如 SGD、Adam"),
     ("训练循环","training loop","前向、损失、清梯度、反向、更新"),
     ("超参数","hyperparameter","人为设定、不被训练更新的量，如学习率"),
     ("有限差分","finite difference","用 $(f(x+\\epsilon)-f(x-\\epsilon))/2\\epsilon$ 数值验证梯度"),
  ),
 ],
 "references": [
  {"title": "ARENA [0.0] Prerequisites — PyTorch 部分", "url": "https://github.com/ARENA-education/ARENA_materials/blob/main/chapter0_fundamentals/instructions/pages/00_%5B0.0%5D_Prerequisites.md", "note": "本节 7 个自测题的出处（讲解为自写，未转载原文）"},
  {"title": "PyTorch 官方：Learn the Basics", "url": "https://pytorch.org/tutorials/beginner/basics/intro.html", "note": "ARENA 推荐的入门教程"},
  {"title": "What is torch.nn really?（Jeremy Howard）", "url": "https://pytorch.org/tutorials/beginner/nn_tutorial.html", "note": "ARENA 选读：从零理解 torch.nn"},
  {"title": "PyTorch 官方：A Gentle Introduction to torch.autograd", "url": "https://pytorch.org/tutorials/beginner/blitz/autograd_tutorial.html", "note": "选看：计算图与 backward 的官方说明"},
 ],
 "quiz": {"questions": QUIZ},
}

if __name__ == '__main__':
    dump(unit, "arena-0.0", "u11-pytorch.json")
