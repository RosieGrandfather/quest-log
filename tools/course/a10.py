"""ARENA 0.0 第 10 节：Python 与 NumPy 基础（按 v3 格式重写，2026-10-04）"""
from unitlib import *
from a10c import C_ARGS, C_TRAPS, C_ARRAY, C_INDEX, C_AXIS, C_VIEW, C_VEC, C_EXP
from a10_quiz import QUIZ

unit = {
 "id": "u10",
 "title": "Python 与 NumPy 基础",
 "en": "Python & NumPy",
 "minutes": 110,
 "objectives": [
  "查漏补缺 ARENA 期望你掌握的 Python 语法：`*args` 与 `**kwargs`、**推导式 (comprehension)**、**生成器 (generator)**、**装饰器 (decorator)**、`for / else`、可变默认参数的陷阱",
  "理解 NumPy 数组的 **形状 (shape)**、**数据类型 (dtype)**、**轴 (axis)**，会用 `reshape`、`keepdims` 控制形状",
  "熟练使用 **索引与切片 (indexing & slicing)**、**布尔掩码 (boolean mask)** 和 **整数数组索引 (fancy indexing)**，并分清 **视图 (view)** 与 **副本 (copy)**",
  "理解 **向量化 (vectorization)**：用数组运算代替 Python 循环，会把双重循环改写成广播运算并用随机对拍验证",
  "分清逐元素乘法 `*` 和矩阵乘法 `@`，建立「每一步先想形状」的习惯",
 ],
 "blocks": [
  T(r"""
### 先说这一节要干什么

ARENA 说：「Python 要扎实，因为整个项目都用它」，大致标准是熟练掌握 *Intermediate Python* 这本在线书里 **80–90% 的内容，一直到第 21 节 for/else**。NumPy 则是「高性能 Python 的基本功」，而且它的语法和 PyTorch 几乎一样（常见区别：NumPy 用 `axis`，PyTorch 用 `dim`）。这一节把这两块的「必备」都用可运行的代码过一遍，每个代码块末尾的「# 输出：」都是真实运行出来的。

**学完它你就能看懂这几件事：**

- PyTorch 源码和 ARENA 练习里满屏的 `*args, **kwargs`、`@torch.no_grad()`、`model.parameters()`（生成器）、`@dataclass` 是什么；
- 为什么 `x[mask] = 0` 能取代 for 循环；`logits[np.arange(n), labels]` 在做什么（交叉熵里取出正确类别的分数）；
- 为什么 `a.sum(axis=1)` 的形状是 `(3,)`、`keepdims=True` 有什么用，这是下一阶段广播和 einops 的基础；
- 为什么有时候「改了一个数组，另一个也变了」：视图和副本。

**本节安排（约 110 分钟）**：Python 语法速查（25 分钟）→ 视频（24 分钟）→ 数组的形状与 dtype（10 分钟）→ 索引、切片与掩码（15 分钟）→ 轴与归约（10 分钟）→ 视图与副本（8 分钟）→ 向量化（8 分钟）→ 动手实验（10 分钟）→「想一想」。视频是英文的，可以打开 YouTube 的中文字幕。边读边在 Colab / Jupyter 里把代码敲一遍效果最好。

### Python：容易被忽略的几个语法

> **标准定义 · 可变参数、推导式与生成器 (variadic arguments, comprehensions, generators)**
>
> **`*args`** 把多余的**位置参数**收集成一个**元组**，**`**kwargs`** 把多余的**关键字参数**收集成一个**字典**；调用时在容器前加 `*` / `**` 则是反过来「拆开」传入。**推导式**用一行表达式从可迭代对象构造列表、集合或字典，可以带 `if` 过滤。**生成器**用 `yield`（或生成器表达式 `(... for ...)`）**惰性地**按需产生值，不会一次性存下全部结果。
>
> *English: `*args` collects extra positional arguments into a tuple and `**kwargs` collects extra keyword arguments into a dict; a comprehension builds a list/set/dict from an iterable in one expression; a generator produces values lazily, one at a time, so the whole sequence is never stored.*

**白话版：「收纳袋、一行造表、流水线」。** `*args` 是一个收纳袋，不管调用者塞进来多少个东西都装得下；推导式是「一行写完一个 for 循环再装进容器」；生成器是流水线，需要一个才造一个，所以哪怕要处理十亿个数，内存里也只有一个。

""" + C_ARGS + r"""

读输出：`f(1, 2, lr=0.1)` 得到 `((1, 2), {'lr': 0.1})`，位置参数进了元组、关键字参数进了字典；`train("mlp", **cfg)` 把字典拆成关键字参数（PyTorch 里 `Model(**config)` 就是这个用法）。三种推导式分别得到列表、集合、字典。生成器 `g` 先后取出 0、1，再 `list(g)` 只剩 `[2]`：**用过的值不会再出现，生成器只能遍历一次**；`model.parameters()` 返回的就是生成器，想反复用要先 `list(...)`。一百万个整数的列表占用的内存是生成器对象的一千倍以上，而两者求和的结果一样。

下面是几个更容易出错的点：

> **标准定义 · 装饰器与默认参数 (decorator & default arguments)**
>
> **装饰器**是一个「接收函数、返回新函数」的函数，`@d` 写在 `def f` 之上等价于 `f = d(f)`。函数的**默认参数在定义函数时只求值一次**，所以默认值若是可变对象（列表、字典），所有调用会共享同一个对象。`for ... else` 里的 `else` 在循环**没有被 `break` 打断**（正常跑完）时执行。
>
> *English: A decorator is a function that takes a function and returns a new one; @d above def f means f = d(f). Default argument values are evaluated once at definition time, so a mutable default is shared across calls. The else clause of a for loop runs only if the loop finished without hitting break.*

**白话版：「给函数套个外壳；默认值是只印一次的表格；没找到才有 else」。** 装饰器像给函数套个外壳，能在调用前后做点事（计时、计数、关闭梯度）；可变默认参数像办公室里只印了一份的空白表，第一个人填了，第二个人拿到的就是已经填过的；`for/else` 的 `else` 读作「如果没有 break」，适合写「找了一圈没找到」的逻辑。

""" + C_TRAPS + r"""

读输出：`first_even([1, 3, 5])` 没有 `break`，所以执行 `else`，打印「没有偶数」；`[1, 4, 5]` 中途 `break`，不执行 `else`。**可变默认参数的陷阱**：`add_item(1), add_item(2)` 两次都返回 `[1, 2]`，因为它们共用同一个列表；正确写法（默认 `None`，函数里再创建）得到 `[1] [2]`。装饰器 `count_calls` 把 `double` 包了一层：调用两次，计数是 2，`functools.wraps` 保证函数名仍是 `double`。`@dataclass` 自动生成了 `__init__` 和打印格式，`with open(...)` 在块结束后自动关闭文件（`fh.closed` 为 `True`）。
"""),
  V("lLRBYKwP8GQ", "视频：Ultimate Guide to NumPy Arrays（Python Simplified）", 24),
  T(r"""
### 数组的形状与数据类型

视频里讲了数组的创建、索引和常见运算。下面把最重要的几个概念写成严谨的定义，再逐个用代码验证。

> **标准定义 · 数组、形状与数据类型 (ndarray, shape, dtype)**
>
> NumPy 的 **`ndarray`** 是一块**同一类型**元素的连续内存，加上描述如何解读它的元信息：**形状 (shape)** 是各维度大小组成的元组，**维数 `ndim`** 是 `len(shape)`，**数据类型 `dtype`**（如 `int64`、`float32`）决定每个元素占多少字节、怎么解释。元素总数是各维大小的乘积。
>
> *English: An ndarray is a block of homogeneously typed elements plus metadata. Its shape is a tuple of dimension sizes, ndim = len(shape), and its dtype (e.g. int64, float32) fixes how many bytes each element takes and how they are interpreted.*

**白话版：「一排排格子的整齐柜子」。** 形状 `(3, 4)` 是 3 行 4 列的柜子，每个格子装同一类型的东西（都是整数，或都是小数）。**写代码时最常出错的就是形状**，养成随手 `print(x.shape)` 的习惯。

""" + C_ARRAY + r"""

读输出：`np.arange(12).reshape(3, 4)` 得到 3×4 的数组，`shape (3, 4)`、`ndim 2`、`size 12`、`dtype int64`。`reshape(2, -1)` 里的 `-1` 让 NumPy 自己算出该维是 $12/2=6$，得到 `(2, 6)`；`reshape(-1)` 拉成一维 `(12,)`；转置 `a.T` 是 `(4, 3)`。**dtype 会向上转型**：整数数组除以 2 或乘 1.5 都变成 `float64`；`astype(np.float32)` 显式转成 32 位浮点。`float32` 占 4 字节、`float64` 占 8 字节：模型越大，省一半内存越重要，所以**深度学习默认用 `float32`**（甚至 `float16 / bfloat16`）。最后一行提醒你浮点数的「近似」：`0.1 + 0.2` 在 `float64` 下是 `0.30000000000000004`，所以**比较浮点数要用 `np.allclose`，不要用 `==`**。

### 索引、切片与布尔掩码

> **标准定义 · 索引与布尔掩码 (indexing & boolean mask)**
>
> `a[i, j]` 取单个元素；**切片** `a[start:stop:step]` 沿每个维度取一段（`:` 表示整个维度，负数从末尾数）。**布尔掩码**是和 `a` 同形状的 `True/False` 数组，`a[mask]` 取出所有为 `True` 位置的元素，形成一维数组；`a[mask] = v` 则对这些位置赋值。**整数数组索引（fancy indexing）**用整数数组一次取多个位置。
>
> *English: Slicing a[start:stop:step] selects a range along each axis. A boolean mask has the same shape as a and a[mask] selects the elements where it is True (or assigns to them). Integer-array (fancy) indexing selects arbitrary positions at once.*

**白话版：「按坐标取、按条件取、按名单取」。** 切片是「第几行第几列」；布尔掩码是「所有满足条件的」（例如所有大于 6 的）；整数数组索引是「照着名单一个个点名」。

""" + C_INDEX + r"""

读输出：`a[1]` 是第 1 行 `[4 5 6 7]`，`a[:, 2]` 是第 2 列 `[2 6 10]`，`a[1:, :2]` 是第 1 行起、前 2 列 `[[4, 5], [8, 9]]`；`a[-1, -1]` 是 11，`a[::2, ::2]` 是隔一行隔一列取 `[[0, 2], [8, 10]]`。布尔掩码 `a > 6` 里有 5 个 `True`，取出 `[7 8 9 10 11]`；**多个条件要用 `&`、`|` 连接，并给每个条件加括号**（不能用 `and`、`or`）。把负数变成 0 有三种等价写法（掩码赋值、`np.maximum`、`np.where`），这就是 **ReLU**。整数数组索引 `a[[0, 2], [1, 3]]` 同时取 `a[0,1]` 和 `a[2,3]`，得到 `[1 11]`。

最后一段是真实的分类场景：`logits[np.arange(3), labels]` 为每个样本取出「正确类别那一格」的分数（得到 `[2.  1.5 3. ]`），这正是计算交叉熵时的第一步；`logits.argmax(axis=1) == labels` 统计预测对了几个，这里全部 3 个都对。

### 轴与归约

> **标准定义 · 轴与归约 (axis & reduction)**
>
> **归约 (reduction)** 指 `sum`、`mean`、`max`、`argmax` 这类把多个数压成一个数的运算。`axis=k` 表示**沿第 $k$ 维做归约，也就是把第 $k$ 维消掉**；`axis` 也可以是元组。`keepdims=True` 会把被消掉的那一维保留下来，大小变成 1。
>
> *English: A reduction (sum, mean, max, argmax, …) collapses values along an axis. axis=k removes dimension k from the shape; keepdims=True keeps it with size 1.*

**白话版：「把哪一维压扁」。** 形状 `(3, 4)` 的表格，`axis=0` 是「把 3 行压成 1 行」，每一列得到一个数；`axis=1` 是「把 4 列压成 1 列」，每一行得到一个数。**记法：谁被消掉，谁就从形状里消失。**

""" + C_AXIS + r"""

读输出：`a.sum()` 是全部 12 个数的和 66；`axis=0` 得到 `[12 15 18 21]`，形状从 `(3, 4)` 变成 `(4,)`；`axis=1` 得到 `[6 22 38]`，形状 `(3,)`；`keepdims=True` 时形状是 `(3, 1)`。`keepdims` 的用处是让结果能和原数组**广播**：`x - x.mean(axis=1, keepdims=True)` 让每一行减去自己的平均值，输出两行都是均值 0 的结果（`[-1, 0, 1]` 和 `[-10, 0, 10]`）。如果不用 `keepdims`，`(2,)` 的平均值和 `(2, 3)` 的数组没法按行对齐。下面的标准化把每一列变成均值 0、标准差 1，验证结果均值全为 0、标准差全为 1，这是数据预处理里天天在做的事。三维数组里，`axis=0` 消掉第一维得到 `(3, 4)`，`axis=1` 得到 `(2, 4)`，`axis=(1, 2)` 同时消掉两维得到 `(2,)`；PyTorch 里 `axis` 写成 `dim`。

### 视图与副本

> **标准定义 · 视图与副本 (view & copy)**
>
> **视图 (view)** 与原数组**共享同一块内存**，只是换了一种看法（形状、步长）；改视图会改原数组。**副本 (copy)** 拥有自己独立的内存。基本切片、`reshape`、转置通常返回视图；**整数数组索引和布尔掩码索引返回副本**。需要独立的数据时用 `.copy()`（PyTorch 里是 `.clone()`）。
>
> *English: A view shares memory with the original array, so modifying it modifies the original; a copy owns separate memory. Basic slicing, reshape and transpose return views, while integer-array and boolean-mask indexing return copies.*

**白话版：「同一份文件的两个快捷方式 vs 复印件」。** 视图是桌面上的快捷方式，改一处另一处也跟着变；副本是复印件，各改各的。`b = a` 连快捷方式都不算，只是给同一个数组起了第二个名字。

""" + C_VIEW + r"""

读输出：`b = a[0]` 之后改 `b[0] = 100`，`a[0, 0]` 也变成 100，`np.shares_memory` 为 `True`；而 `.copy()` 之后再改，`a[0, 1]` 仍是 1。基本切片、`reshape`、转置都是 `True`（共享内存）；整数数组索引、布尔掩码都是 `False`（副本）。「先取出、再修改」的坑：`sub = a2[[0, 1]]` 取出的是副本，对 `sub` 加 100 不会影响 `a2`；而直接对 `a2[[0, 1]] += 10` 是对 `a2` 本身赋值，会生效。最后，`d = a` 之后改 `d` 也改了 `a`，因为 `d is a` 为 `True`。排查「数据莫名其妙被改了」的 bug 时，先想想是不是视图。

### 向量化

> **标准定义 · 向量化 (vectorization)**
>
> 用**对整个数组的运算**（逐元素运算、广播、矩阵乘法、归约）代替 Python 层面的逐元素 `for` 循环。数组运算由底层预编译的 C / BLAS 代码（以及 GPU）批量完成，省掉了 Python 解释器每次迭代的开销。
>
> *English: Vectorization replaces explicit Python loops over elements with whole-array operations, which run in precompiled low-level code (and on GPUs) instead of the Python interpreter.*

**白话版：「一次搬一整箱，而不是一个个搬」。** ARENA 的练习要求你用张量运算代替循环，这是贯穿整个课程的习惯。

""" + C_VEC + r"""

读输出：对一百万个数算 $\sum(2x^2+1)$，Python 循环和数组运算结果一致（`np.isclose`），数组版至少快 10 倍（实际倍数每台机器不同，一般是几十到几百倍）。最后一行是个常见的坑：形状相同的两个矩阵，`A * B` 是**逐元素**相乘（`[[0, 2], [3, 0]]`），`A @ B` 是**矩阵乘法**（`[[2, 1], [4, 3]]`），两个都不会报错，所以写错了很难发现。

### 动手实验：把循环改写成向量化，并用对拍验证

把前面学到的东西用在三个小任务上。**写向量化代码的好习惯是：先写一个慢但显然正确的循环版本，再写向量化版本，用 `np.allclose` 对拍。**

""" + C_EXP + r"""

读输出：

- **两两距离矩阵**：双重循环、广播写法（`X[:, None, :] - X[None, :, :]`，形状 `(6, 6, 3)`，再沿最后一维求和）结果一致。更省内存的写法用恒等式 $\|a-b\|^2=\|a\|^2+\|b\|^2-2a\cdot b$，只需一次矩阵乘法；它在 $10^{-6}$ 的容差内与循环版一致，但对角线并不「严格」等于 0（`False`）：两个相同的数相减会留下极小的浮点误差，再开方就被放大，所以这种写法要先 `np.maximum(D2, 0)`，比较时也要用 `allclose` 而不是 `==`。矩阵对称、对角线为 0（广播写法）。最近的一对点是第 0 和第 1 个。
- **逐行 softmax**：每行减去该行最大值（数值稳定），`keepdims=True` 让除法按行对齐，每行之和为 1，形状 `(4, 5)`，和逐行循环的结果一致。
- **纯数组运算计数**：1 到 100 中能被 3 或 5 整除的数有 47 个，和是 2418，与普通循环对拍一致。

### 这一节你要带走的三句话

1. **Python 里最常踩的坑**：可变默认参数（默认值只创建一次）、生成器只能遍历一次、`for/else` 的 `else` 是「没有 break」。
2. **NumPy 的核心是形状**：`axis=k` 消掉第 $k$ 维，`keepdims=True` 保留它；切片、`reshape`、转置给**视图**（共享内存），掩码和整数数组索引给**副本**。
3. **用数组运算代替循环**：先写慢而对的版本，再写向量化版本，用 `np.allclose` 对拍；`*` 是逐元素，`@` 是矩阵乘法。
"""),
  THINK("`x` 的形状是 `(5, 3)`。`x.mean(axis=0)` 和 `x.mean(axis=1)` 的形状分别是？怎样做到「每一列减去自己的平均值」？", r"""
- `x.mean(axis=0)`：消掉第 0 维，形状 `(3,)`，是每一**列**的平均值。
- `x.mean(axis=1)`：消掉第 1 维，形状 `(5,)`，是每一**行**的平均值。

每列减去自己的平均值：`x - x.mean(axis=0)`，因为 `(5, 3)` 和 `(3,)` 可以广播（`(3,)` 自动补成 `(1, 3)`）。**每行**减去自己的平均值则要 `x - x.mean(axis=1, keepdims=True)`，因为 `(5,)` 无法和 `(5, 3)` 对齐，必须保留成 `(5, 1)`。第 14 节会专门讲广播的规则。
"""),
  THINK("下面的函数有什么问题？怎么改？再说说：为什么 `a[a > 0]` 得到的数组被修改后，不会影响 `a`？\n\n```python\ndef make_config(name, tags={}):\n    tags[\"name\"] = name\n    return tags\n```", r"""
**可变默认参数**：`tags={}` 这个字典只在定义函数时创建一次，每次调用都在往**同一个**字典里写，结果会互相污染（例如连续调用两次，第二次返回的字典里也带着第一次的内容）。改法：

```python
def make_config(name, tags=None):
    if tags is None:
        tags = {}
    tags["name"] = name
    return tags
```

第二问：布尔掩码索引返回的是**副本**（上面 `np.shares_memory` 为 `False`），所以修改它不会影响 `a`；如果想修改 `a` 里满足条件的元素，要把掩码写在赋值的左边：`a[a > 0] = 0`，这时 NumPy 是对 `a` 本身做原位赋值。
"""),
  THINK("**联系机器学习**：训练里有一批 logits，形状 `(batch, vocab)`，和一个整数数组 `labels`，形状 `(batch,)`。怎样不写循环，算出这一批的平均交叉熵损失？形状每一步分别是什么？", r"""
```python
z = logits - logits.max(axis=1, keepdims=True)                   # (batch, vocab)
log_p = z - np.log(np.exp(z).sum(axis=1, keepdims=True))         # (batch, vocab)，log softmax
loss = -log_p[np.arange(batch), labels].mean()                   # 标量
```

第一步减去每行最大值（`keepdims=True` 保证 `(batch, 1)` 能和 `(batch, vocab)` 广播），保证数值稳定；第二步用 log-sum-exp 得到每个词的对数概率；第三步用整数数组索引 `log_p[np.arange(batch), labels]` 取出每个样本「正确词」那一格，得到形状 `(batch,)`，取负再求平均就是交叉熵损失。这里用到了本节的轴与 `keepdims`、整数数组索引、向量化，和上一节信息论里的「损失 $=-\ln Q(\text{正确词})$」正好对上。
"""),
  KW(("可变参数","*args / **kwargs","任意多个位置 / 关键字参数，调用时可用 * / ** 拆开"),
     ("推导式","comprehension","`[f(x) for x in xs if ...]`，也可以建集合和字典"),
     ("生成器","generator / yield","按需产生值，节省内存，只能遍历一次"),
     ("装饰器","decorator","用 `@` 包装函数，如 `@torch.no_grad()`"),
     ("可变默认参数","mutable default argument","默认值只创建一次，会被各次调用共享"),
     ("数组","ndarray","NumPy 的多维数组，元素类型相同"),
     ("形状","shape","各维度的大小，最常见的出错来源"),
     ("数据类型","dtype","`int64`、`float32` 等，混用时会向上转型"),
     ("轴","axis（PyTorch 中是 dim）","沿哪个维度做归约，`axis=k` 消掉第 k 维"),
     ("keepdims","keepdims","归约后保留被消掉的维度（大小 1），方便广播"),
     ("布尔掩码","boolean mask","`a[a > 6]` 按条件选元素，返回副本"),
     ("整数数组索引","fancy indexing","用整数数组一次取多个位置，返回副本"),
     ("视图 / 副本","view / copy","是否与原数组共享内存；`.copy()` / `.clone()`"),
     ("向量化","vectorization","用数组运算代替 Python 循环"),
     ("逐元素乘 / 矩阵乘","`*` vs `@`","`*` 对应位置相乘，`@` 是矩阵乘法"),
  ),
 ],
 "references": [
  {"title": "ARENA [0.0] Prerequisites — Programming 部分", "url": "https://github.com/ARENA-education/ARENA_materials/blob/main/chapter0_fundamentals/instructions/pages/00_%5B0.0%5D_Prerequisites.md", "note": "本节依据的原文大纲（讲解为自写，未转载原文）"},
  {"title": "Intermediate Python（在线书）", "url": "https://book.pythontips.com/en/latest/", "note": "ARENA 的标准：掌握到第 21 节 for/else"},
  {"title": "NumPy 官方文档：Absolute basics for beginners", "url": "https://numpy.org/doc/stable/user/absolute_beginners.html", "note": "数组、索引、归约的官方入门，可以当作速查手册"},
  {"title": "100 NumPy Exercises", "url": "https://github.com/rougier/numpy-100", "note": "ARENA 推荐的练习，熟练后可以改用 PyTorch 来做"},
  {"title": "Python 官方教程", "url": "https://docs.python.org/3/tutorial/", "note": "更系统的 Python 讲解，选看"},
 ],
 "quiz": {"questions": QUIZ},
}

if __name__ == '__main__':
    dump(unit, "arena-0.0", "u10-python-numpy.json")
