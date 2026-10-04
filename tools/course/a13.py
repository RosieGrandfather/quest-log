"""ARENA 0.0 第 13 节：einops（按 v3 格式重写，2026-10-04）"""
from unitlib import *
from a13c import C_VS, C_REARR, C_ORDER, C_REDUCE, C_REPEAT, C_ERR, C_PATCH, C_RT
from a13_quiz import QUIZ

unit = {
 "id": "u13",
 "title": "einops：重排、归约、重复",
 "en": "einops: rearrange / reduce / repeat",
 "minutes": 85,
 "objectives": [
  "理解 **einops** 的核心思想：用写出 **维度名字 (axis names)** 的字符串描述张量变形，让「代码即文档」，形状对不上时会报错而不是悄悄算错",
  "会用 **`rearrange`** 做转置、**展平 / 合并 (merge)**、**拆分 (split)**、增减长度为 1 的维度，并能说清 `(h w)` 与 `(w h)` 的 **顺序 (order)** 区别",
  "会用 **`reduce`** 做平均、求和、最大和 **池化 (pooling)**，用 **`repeat`** 沿新维度复制，知道三者靠「箭头右边少了 / 多了哪些维度」区分",
  "能把一个 **reshape / permute** 的写法改写成 einops，并用 NumPy 或 PyTorch 对拍验证两者结果一致",
  "能读懂并写出 Transformer 里的两个典型变形：**多头注意力 (multi-head attention)** 的拆头 / 合头，以及 **图像切块 (patchify)**",
 ],
 "blocks": [
  T(r"""
### 先说这一节要干什么

写深度学习代码，一半的时间在「变形」：一批图片是 `(batch, channel, height, width)`，卷积要这个顺序，画图要 `(h, w, c)`；Transformer 里隐藏向量要先拆成几个注意力头，算完再拼回去。这些操作在 PyTorch / NumPy 里叫 `reshape`、`permute`、`transpose`、`squeeze`、`unsqueeze`、`view`……名字多，还要在脑子里数「第几个维度」，写错了往往**不报错**，只是结果悄悄变错。

**einops** 是一个小库，用一个字符串描述变形：左边写输入每个维度叫什么，右边写输出每个维度怎么排。字符串本身就是注释，库会替你检查形状。ARENA 的第 0 章第 2 天就有 einops 练习，后面的 Transformer、可解释性代码里到处是它。

**学完它你就能看懂这几件事：**

- 多头注意力里那一行 `rearrange(x, "b s (n d) -> b n s d", n=n_heads)` 到底把数据怎么搬了一遍；
- Vision Transformer 为什么能把一张图片变成一串「词」：`"b c (h p1) (w p2) -> b (h w) (p1 p2 c)"`；
- 为什么 `reshape` 得到的形状对了、内容却可能是错的（本节的第一个实验）；
- 「全局平均池化」「最大池化」「把灰度图复制成三通道」，都只是一行字符串的差别。

**本节安排（约 85 分钟）**：导读与视频一（8 分钟）→ `rearrange` 与「顺序」（20 分钟）→ 视频二（12 分钟）→ `reduce`（12 分钟）→ `repeat`（8 分钟）→ 报错、对拍与 Transformer 里的真实用法（15 分钟）→「想一想」。视频是英文的，可以打开中文字幕。代码用到 `numpy`、`einops` 和 `torch`：`pip install einops` 即可。

### 为什么不直接用 reshape 和 permute

先做一个对比实验：把 `(b, c, h, w)` 变成 `(b, h, w, c)`。

""" + C_VS + r"""

读输出：转置（`transpose(0, 2, 3, 1)`）和 `rearrange` 结果完全一致；但 `reshape(2, 2, 2, 3)` 虽然形状同样是 `(2, 2, 2, 3)`，内容却**不一样**（`False`）。位置 `(0,0)` 的三个通道，正确答案是 `[0 4 8]`（三个通道里对应位置的值），而 `reshape` 给出的是 `[0 1 2]`，只是把内存里连续的三个数当成了「三个通道」。这就是为什么说 `reshape` 危险：**它只管「总个数对得上」，不管每个数该去哪**。einops 要求你把每个维度的名字写出来，这类错误几乎写不出来。
"""),
  V("GiAN41N_gtY", "视频一：Einops Makes Tensor Manipulation in Deep Learning a Breeze（Tales Of Tensors）", 3),
  T(r"""
### rearrange：只改排列，不改数据

> **标准定义 · 重排 (rearrange)**
>
> `rearrange(x, "左边 -> 右边")` 把张量 `x` 的元素重新排列，**不改变元素的值，也不改变元素个数**。左边的模式给输入的每个维度起一个**名字 (axis name)**；右边的模式说明输出有哪些维度、按什么顺序排。同一个名字在左右两边必须都出现，且大小相同。括号 `( )` 表示把里面的几个维度**合并**成一个（出现在右边），或者把一个维度**拆开**成几个（出现在左边）。长度为 1 的维度写作 `1`。
>
> *English: rearrange(x, "lhs -> rhs") reorders the elements of a tensor without changing values or count. The left pattern names the input axes; the right pattern names and orders the output axes. Parentheses merge axes (on the right) or split an axis (on the left); an axis of length 1 is written as 1.*

**白话版：「给每个维度起名字，再按名字重新点名」。** 好比一队学生按「年级、班、座号」站成三层的方阵。`rearrange` 就是你喊一句「按『班、座号、年级』重新排」，或者「把年级和班合成一个大队」，人没变，站位变了。名字一旦起了，就不用再记「第 0 维、第 2 维」。

""" + C_REARR + r"""

读输出：第一行是转置，通道从第 2 位挪到最后；第二行用括号 `(c h w)` 把三个维度合成一个，$3\times28\times28=2352$，每张图成了一个向量（`nn.Linear` 要的就是这种输入）；第三、四行说明「合并」可以发生在任何位置：`(b w)` 把批量和宽度合并，得到 `(3, 28, 896)`，$32\times28=896$，相当于 32 张图**横着**拼成一条；`(b h)` 则是**竖着**叠起来，得到 `(896, 28, 3)`。再下面是「拆开」：把 12 个数拆成 3 组，每组 4 个，只需要告诉 einops 其中一个的大小（`g=3`），另一个它自己算。最后是加 / 去长度为 1 的维度，对应 `unsqueeze` / `squeeze`。

### 括号里的顺序：谁变化得快

这是 einops 里**最重要、最容易错**的一点，也是上面「图片拼成长条」能成立的原因。

> **标准定义 · 括号内的顺序 (order within parentheses)**
>
> 括号 `(a b)` 把两个维度合成一个下标 $i = a \cdot |b| + b$，其中 $|b|$ 是 $b$ 的长度：**靠右的维度变化得快，靠左的变化得慢**（与 C 语言 / NumPy 的行优先顺序一致）。因此 `(h w)` 与 `(w h)` 是两种不同的排列。
>
> *English: Inside parentheses the rightmost axis varies fastest (row-major order), so "(h w)" and "(w h)" describe different layouts of the same elements.*

**白话版：「数字时钟的读法」。** `12:34` 里分钟（右边）转得快，小时（左边）转得慢；`(小时 分钟)` 读起来是 12:34，`(分钟 小时)` 读成 34:12。合并和拆分都是这个读法。

""" + C_ORDER + r"""

读输出：同样是 `[0..5]`，`(h w)` 拆成 `[[0 1 2], [3 4 5]]`，连续的数在**同一行**（`w` 在右边，变化快）；`(w h)` 拆成 `[[0 2 4], [1 3 5]]`，连续的数在**同一列**（`h` 在右边，变化快）。后面两个 `True` 说明它们分别等价于 `reshape(2, 3)` 和 `reshape(3, 2).T`。

下面的拼图例子是这个规则最典型的用法：6 张 $2\times2$ 的小图，第 $k$ 张的像素是 $4k$ 到 $4k+3$，用 `"(r c) h w -> (r h) (c w)"` 拼成 2 行 3 列。结果是 `(4, 6)` 的大图：第 0 行 `[0 1 4 5 8 9]`，是三张图（0、1、2 号）各自的第 0 行并排；第 1 行 `[2 3 6 7 10 11]` 是它们各自的第 1 行。关键在 `(r h)` 里 `r`（第几行小图）在左边、`h`（小图内的行）在右边：先走完一张小图的所有行，再换下一行小图。写反成 `(h r)` 后，小图被撕碎，第一行变成 `[0 4 8 1]`，来自不同图片的像素混在一起，**形状仍然是对的，但图是错的**。所以用 einops 时的心法是：**合并时问自己「哪个应该变化得更快」，快的放右边。**
"""),
  V("xGy75Pjsqzo", "视频二：Reshape, Permute, Squeeze, Unsqueeze made simple using einops（Kapil Sachdeva）", 12),
  T(r"""
### reduce：把几个维度汇总掉

> **标准定义 · 归约 (reduce)**
>
> `reduce(x, "左边 -> 右边", 操作)` 对**出现在左边、没有出现在右边**的维度做汇总：`"mean"`（平均）、`"sum"`（求和）、`"max"`、`"min"`，或者一个自己写的函数。出现在右边的维度保留。把一个维度拆成 `(块数 块内位置)` 并对「块内位置」汇总，就得到**池化 (pooling)**。
>
> *English: reduce(x, "lhs -> rhs", op) aggregates over the axes that appear on the left but not on the right, using "mean", "sum", "max", "min" or a custom function. Splitting an axis into (blocks, within-block) and reducing the second part gives pooling.*

**白话版：「班级成绩单，留下想看的列」。** 全校有「年级、班、人」三层成绩，你只想看每个年级的平均分，就把「班」和「人」两个维度从右边拿掉，并说「求平均」。**右边没写的，就是被汇总掉的。**

""" + C_REDUCE + r"""

读输出：`"b c h w -> c"` 把 `b`、`h`、`w` 三个维度都平均掉，剩下 `(3,)`，与 `x.mean(axis=(0, 2, 3))` 对拍结果为 `True`；`"b c h w -> b c"` 只平均 `h` 和 `w`，得到 `(8, 3)`：这就是 CNN 里常见的**全局平均池化 (global average pooling)**；`"-> b"` 配 `"sum"` 则把后三个维度都加起来。

池化那个例子，把 $4\times4$ 的图拆成 $2\times2$ 个块，每块 $2\times2$：取最大得到 `[[5 7], [13 15]]`（左上块 $\{0,1,4,5\}$ 的最大值是 5，右上块 $\{2,3,6,7\}$ 是 7，依此类推），取平均得到 `[[2.5 4.5], [10.5 12.5]]`。最后的双重循环对拍（形状 `(3, 4)`，输出 `True`）说明 `reduce` 与「手写循环」一致。注意 `"mean"` 要求输入是浮点数，整数数组需要先 `astype(float)`，否则 einops 会报错。

### repeat：沿新维度复制

> **标准定义 · 重复 (repeat)**
>
> `repeat(x, "左边 -> 右边")` 在右边**多出**来的维度上复制数据；新维度的大小要用关键字参数给出（如 `c=3`）。新维度出现在括号里时，同样遵循「靠右变化快」：`(d 3)` 是每个元素连续重复 3 次，`(3 d)` 是整段重复 3 次。
>
> *English: repeat(x, "lhs -> rhs") copies data along axes that appear only on the right, whose sizes are given as keyword arguments. Inside parentheses the same rightmost-fastest rule applies.*

**白话版：「复印」。** 灰度图只有一层，想当三通道图用，就沿新的「通道」维度复印 3 份；`(d 3)` 是「每个同学连喊三遍」，`(3 d)` 是「全班从头到尾再来三轮」。

""" + C_REPEAT + r"""

读输出：灰度图 `(2, 2)` 变成 `(2, 2, 3)`，位置 `(0, 1)` 的三个通道都是 1（原值）；`(d 3)` 得到 `[1 1 1 2 2 2]`，对应 `np.repeat`；`(3 d)` 得到 `[1 2 1 2 1 2]`，对应 `np.tile`，两个对拍都是 `True`。最后一例是下一节广播的预告：把长度为 3 的偏置向量复制成 `(2, 3, 2, 2)`，对每个样本、每个像素位置，通道上的值都是 `[10 20 30]`。

### 三个函数怎么选

| 函数 | 箭头两边的维度 | 典型用途 |
|---|---|---|
| `rearrange` | 两边是**同样的一组名字**，只是排列 / 合并 / 拆分不同 | 转置、展平、拆头、拼图 |
| `reduce` | 左边有、右边**没有**的维度被汇总 | 平均、求和、最大、池化 |
| `repeat` | 右边有、左边**没有**的维度被复制 | 灰度转彩色、扩成批量、广播前的展开 |

### 写错了会怎样：einops 会替你检查

""" + C_ERR + r"""

读输出：长度 7 不能被 2 整除、维度个数对不上、`rearrange` 的右边少了维度、拆分时两个大小都没给，四种情况全部抛出 `EinopsError`，而不是悄悄算出一个错的结果。**想丢维度必须用 `reduce`**（最后一行输出 `(2,)`），这条规则把「变形」和「汇总」清楚地分开。当然，einops 只能检查**形状**对不对，查不出「顺序写反了」这类逻辑错误（前面拼图的例子）。所以养成习惯：**写完用一个小例子、或和老写法对拍一次。**

### 真实用法：多头注意力与图像切块

下面两段是 Transformer 里最常见的变形，后面 ARENA 第 1 章会反复遇到。第一段把隐藏向量 `(batch, seq, n_heads×d_head)` 拆成 `n_heads` 个头；第二段是 Vision Transformer 的第一步：把图片切成不重叠的小块，每块展平成一个向量，一张图就变成了一串「词」。

""" + C_PATCH + r"""

读输出：拆头后形状 `(2, 4, 5, 8)`，也就是 `(batch, n_heads, seq, d_head)`；每个头自己算 $5\times5$ 的注意力分数，所以得到 `(2, 4, 5, 5)`；用 `"b n s d -> b s (n d)"` 拼回去，与原来逐元素相同（`True`）；与 PyTorch 老写法 `view(...).transpose(1, 2)` 对拍也是 `True`，所以你在别人的代码里看到 `view + transpose`，可以在脑子里翻译成这一行。切块：`(2, 3, 4, 4)` 的图变成 `(2, 4, 12)`：每张图 $2\times2=4$ 个块，每块 $2\times2\times3=12$ 个数；取第 0 张图的右上角那块手工展平，与 `patches[0, 1]` 完全一致（`True`）。注意 `(p1 p2 c)` 决定了块内展平的顺序：改成 `(c p1 p2)` 也合法，但展平后每个位置的含义就变了，所以**模型训练和加载权重时，这个顺序必须前后一致**。

**最后一个实验：随机对拍。** 每个 `rearrange` 都能「反着写」还原，所以可以随机生成形状，来回变一趟，必须回到原样：

""" + C_RT + r"""

200 组随机形状来回一趟都还原（`True`）。这种「变过去再变回来」的测试，在写 einops 时是最便宜的正确性检查。

### 这一节你要带走的三句话

1. **einops 用「给维度起名字」代替「数第几个维度」**：`rearrange` 只改排列、`reduce` 汇总掉右边没写的维度、`repeat` 复制右边新多出的维度。
2. **括号里靠右的维度变化得快**（`(h w)` 与 `(w h)` 不同）；合并 / 拆分时顺序写反，形状仍对、内容却错，要靠小例子或对拍发现。
3. **多头注意力的拆头 / 合头、图像切块、池化**，都是一行 einops；它会检查形状，但检查不了你的顺序是否合理。
"""),
  THINK("**计算题**：`temps` 是连续 3 天、每天 24 小时的逐小时气温，形状 `(72,)`。用一次 `reduce` 算出每天的平均气温，再说明如果要得到每天**最高**气温该改哪里。", r"""
```python
reduce(temps, "(d 24) -> d", "mean")   # 形状 (3,)
reduce(temps, "(d 24) -> d", "max")    # 最高气温：只改第三个参数
```

把 72 拆成（天数 `d`，每天 24 小时），`d` 在左边变化慢，所以第 0–23 个数属于第 1 天，依此类推；右边没有「24」这一维，它就被汇总掉。如果误写成 `"(24 d) -> d"`，就变成「每隔 3 小时取一个数」的汇总，形状还是 `(3,)`，但含义错了。
"""),
  THINK("**概念辨析**：`rearrange(x, \"b c h w -> b (c h w)\")` 与 `x.reshape(b, -1)` 在什么条件下结果相同？为什么前面的 `reshape(2, 2, 2, 3)` 却不等于 `rearrange(x, \"b c h w -> b h w c\")`？", r"""
`rearrange` 的展平只是把 `c h w` 三个维度**按原来的顺序**并成一个维度，没有改变元素的相对顺序，所以与 `reshape(b, -1)` 完全一致。

而 `b c h w -> b h w c` 是**换了维度的顺序**（转置），元素在内存里的相对位置变了；`reshape` 只会按内存里的顺序重新切分，不会搬动元素，所以得到的形状虽然是 `(b, h, w, c)`，每个格子里的数却是按原来 `(b, c, h, w)` 的顺序切出来的。一句话：**`reshape` 只能合并 / 拆分相邻的维度，要改变维度顺序必须用转置（`permute` / `rearrange`）**。
"""),
  THINK("**和后续内容的联系**：Transformer 里 `x` 的形状是 `(batch, seq, d_model)`，$d_{\\text{model}}=512$，有 8 个头。写出拆头和合头的 einops；如果把 `(n d)` 误写成 `(d n)`，模型会不会报错？会有什么后果？", r"""
```python
heads = rearrange(x, "b s (n d) -> b n s d", n=8)   # d = 512 / 8 = 64
back  = rearrange(heads, "b n s d -> b s (n d)")
```

写成 `(d n)` **不会报错**：只要 `n=8`，512 仍然可以拆成 $64\times8$，形状 `(batch, 8, seq, 64)` 完全一样。区别是「谁变化快」：`(n d)` 里每个头拿到的是 **连续的 64 个维度**，`(d n)` 里每个头拿到的是**每隔 8 个取一个**的 64 个维度。训练时如果前后一致，模型仍然能学（只是维度的编号被打乱了）；但如果加载别人训练好的权重，而你的拆法和别人的不同，输出就会悄悄变错。这就是为什么要对拍、并且明确写出顺序。
"""),
  KW(("重排","rearrange","只改排列：转置、合并、拆分、增减长度为 1 的维度"),
     ("归约","reduce","左边有、右边没有的维度被汇总（mean / sum / max / min）"),
     ("重复","repeat","右边新多出的维度被复制"),
     ("维度名字","axis name","如 `b c h w`，同名维度两边大小必须一致"),
     ("合并维度","merge axes `(a b)`","括号写在右边：多个维度合成一个"),
     ("拆分维度","split an axis","括号写在左边：一个维度拆成多个，需给出其中一个的大小"),
     ("行优先顺序","row-major order","括号内靠右的维度变化得快"),
     ("展平","flatten","把多个维度合并成一维，如 `(c h w)`"),
     ("池化","pooling","把图拆成小块，对块内取最大或平均"),
     ("全局平均池化","global average pooling","`b c h w -> b c` 配 mean"),
     ("转置 / 置换","transpose / permute","PyTorch 里调换维度顺序的方法"),
     ("压缩 / 扩展维度","squeeze / unsqueeze","去掉 / 加上长度为 1 的维度"),
     ("多头注意力","multi-head attention","把隐藏维拆成多个头并行计算"),
     ("图像切块","patchify","把图片切成小块并展平，Vision Transformer 的第一步"),
     ("einops 错误","EinopsError","形状或模式对不上时抛出的异常"),
  ),
 ],
 "references": [
  {"title": "ARENA [0.0] Prerequisites — Einops 部分", "url": "https://github.com/ARENA-education/ARENA_materials/blob/main/chapter0_fundamentals/instructions/pages/00_%5B0.0%5D_Prerequisites.md", "note": "本节依据的原文大纲（讲解为自写，未转载原文）"},
  {"title": "einops 官方教程：Einops basics", "url": "https://einops.rocks/1-einops-basics/", "note": "ARENA 推荐：读到 \"Fancy examples in random order\" 之前"},
  {"title": "einops: powerful library for tensor operations（blopig 博客）", "url": "https://www.blopig.com/blog/2022/05/einops-powerful-library-for-tensor-operations-in-deep-learning/", "note": "ARENA 推荐：为什么用 einops"},
  {"title": "ARENA 0.0 练习 Notebook（Colab）", "url": "https://colab.research.google.com/github/ARENA-education/ARENA_materials/blob/main/chapter0_fundamentals/exercises/part0_prereqs/0.0_Prerequisites_exercises.ipynb", "note": "用图片做的 einops 练习，强烈建议动手做"},
 ],
 "quiz": {"questions": QUIZ},
}

if __name__ == '__main__':
    dump(unit, "arena-0.0", "u13-einops.json")
