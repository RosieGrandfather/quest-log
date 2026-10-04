"""ARENA 0.0 第 15 节：einsum 与高级索引（按 v3 格式重写，2026-10-04）"""
from unitlib import *
from a15c import (C_EIN, C_LOOP, C_ATTN, C_PATH, C_INDEX, C_COPY, C_EMBED,
                  C_GATHER, C_TORCH)
from a15_quiz import QUIZ

unit = {
 "id": "u15",
 "title": "einsum 与高级索引",
 "en": "einsum & Advanced Indexing",
 "minutes": 95,
 "objectives": [
  "理解 **爱因斯坦求和约定 (Einstein summation convention)**：重复出现、但不在输出里的下标就求和；能把任意 einsum 翻译成「开循环再累加」",
  "会用 `einops.einsum` 写出迹、矩阵乘向量、矩阵乘法、内积、外积、批量矩阵乘法、**注意力分数 (attention scores)** 和线性层",
  "掌握 **整数数组索引 (integer array indexing)**：取行、取列、逐对取元素，知道结果形状的规则，以及它与切片（视图 vs 副本）的区别",
  "理解 `torch.gather`（NumPy 的 `take_along_axis`）的规则 `out[i][j] = input[i][index[i][j]]`，并会用它和整数数组索引取出「每个样本正确类别」的值",
  "理解 **词嵌入 (embedding)** 本质上是查表，并知道 `x[idx] += 1` 遇到重复下标时的陷阱",
 ],
 "blocks": [
  T(r"""
### 先说这一节要干什么

前两节学了 `rearrange`（搬动数据）和 `reduce`（对一个张量汇总）。要把**多个**张量「相乘再求和」（矩阵乘法、注意力分数、线性层），需要 **einsum**。另一半是**索引**：从张量里按下标取出元素。「取出每个样本正确类别的概率」「按 token id 查词向量」「按下标把梯度加回去」都靠它。这两样东西合起来，就是 Transformer 实现里绝大部分「不是调现成层」的代码。

这一节同样用 NumPy 和 einops 写并真实运行，最后给出 PyTorch 的对照块。

**学完它你就能看懂这几件事：**

- Transformer 里 `einsum(q, k, "batch q_pos d, batch k_pos d -> batch q_pos k_pos")` 这一行为什么就是 $QK^\top$，为什么 `d` 消失、`batch` 保留；
- `nn.Embedding`、`logits[range(n), y]`、`scores.gather(1, ...)` 分别在做什么，它们之间怎么互相转换；
- 为什么同一个 einsum 的不同计算顺序，速度可以差几十到几百倍；
- 为什么往数组里按下标累加时，重复下标会让结果出错（梯度累加、直方图、稀疏更新里都会遇到）。

**本节安排（约 95 分钟）**：导读（5 分钟）→ 视频（16 分钟）→ einsum 的规则与速查（20 分钟）→ 手写 einsum、注意力与计算顺序实验（15 分钟）→ 整数数组索引（15 分钟）→ 视图 vs 副本、词嵌入（10 分钟）→ gather（10 分钟）→ PyTorch 对照与「想一想」（4 分钟）。视频是英文的，可以打开 YouTube 的中文字幕。
"""),
  V("pkVwUVEHmfI", "视频：Einsum Is All You Need: NumPy, PyTorch and TensorFlow（Aladdin Persson）", 16),
  T(r"""
### einsum 的规则

> **标准定义 · 爱因斯坦求和约定与 einsum**
>
> 张量运算里常见「相乘再对某些下标求和」，例如矩阵乘法 $C_{ik}=\sum_j A_{ij}B_{jk}$。**爱因斯坦求和约定**把求和号省掉：**只在输入里出现、不在输出里出现的下标，就对它求和**；输入和输出里都有的下标保留。**einsum** 就是按这个约定，用一个形如 `"i j, j k -> i k"` 的字符串描述整个运算。同一个下标出现在多个输入里时，这几个输入在该维度上的长度必须一致。
>
> *English: Einstein summation omits the sum sign: any index that appears in the inputs but not in the output is summed over; indices in the output are kept. einsum describes a whole tensor contraction with a string such as "i j, j k -> i k".*

**白话版：「写出每个张量有哪些轴，谁没出现在箭头右边，谁就被压扁（求和）」。** 读法只有两条：

1. 在输入里出现、**在输出（箭头右边）里也出现**的下标：保留；
2. 在输入里出现、**但输出里没有**的下标：沿它**相乘再求和**。

ARENA 用的是 **einops 版本**（`einops.einsum`）：下标可以用完整单词（`"batch seq d_model"`），用空格分隔，可读性比 PyTorch 原生的 `t.einsum("ij,jk->ik", A, B)` 好得多。两者结果相同。先用几个最常见的运算验证：

""" + C_EIN + r"""

读输出：每一行都是「einsum 写法」与「传统写法」的对拍，全部 `True`。几点值得注意：

- **迹** `"i i ->"`：同一个张量里下标重复，表示只取 $i=i$ 的对角线元素；输出为空，表示全部加起来。
- **外积** `"i, j -> i j"`：两个输入没有共同下标，所以**没有求和**，只是两两相乘，得到 $3\times4$ 的矩阵，形状 `(3, 4)`。
- **转置** `"i j -> j i"`：只是改变了输出里下标的顺序。
- **内积** `"i, i ->"`：`i` 在两个输入里都有、输出里没有，所以相乘后求和。

| 运算 | einsum 写法 | 等价于 |
|---|---|---|
| 迹 | `"i i ->"` | `np.trace(M)` |
| 矩阵乘向量 | `"i j, j -> i"` | `A @ v` |
| 矩阵乘法 | `"i j, j k -> i k"` | `A @ B` |
| 内积 | `"i, i ->"` | `u @ v` |
| 外积 | `"i, j -> i j"` | `u[:, None] * v[None, :]` |
| 按行求和 | `"i j -> i"` | `A.sum(axis=1)` |
| 逐元素乘 | `"i j, i j -> i j"` | `A * B` |
| 批量矩阵乘 | `"b i j, b j k -> b i k"` | `x @ y` |

### einsum 到底在算什么：开循环再累加

> **标准定义 · einsum 的语义**
>
> 设表达式里出现的所有下标为 $i_1,\dots,i_r$，每个下标取遍自己的长度。对每一种取值组合，把各输入对应位置的元素**相乘**，再把结果**累加**到输出里「由输出下标决定的那个位置」上。输出里没有的下标，就是被累加掉的下标。
>
> *English: For every assignment of all index values, multiply the corresponding input entries and add the product into the output entry selected by the output indices.*

**白话版：「每个字母一层 for 循环，里面做乘法，累加到输出的格子里」。** 下面手写 `"i j, j k -> i k"`：

""" + C_LOOP + r"""

读输出：手写的三层循环（`i`、`k`、`j`）和 `A @ B` 一致，`j` 就是被求和的那一层。第二个例子 `"ij,ij->"` 两个下标都不在输出里，于是全部累加，得到 $\sum_{i,j}X_{ij}Y_{ij}$，也叫 **Frobenius 内积**，等于 $\text{tr}(X^\top Y)$（最后一行 `True`）。**以后看到任何一个 einsum，都可以用这个办法在脑子里「展开」，不需要背公式。**

### 真实用法：注意力分数与线性层

""" + C_ATTN + r"""

读输出：`q` 是 `(batch, q_pos, d)`，`k` 是 `(batch, k_pos, d)`。`d` 不在输出里，被求和（点积）；`batch` 保留（每个样本分开算）；`q_pos` 和 `k_pos` 两两组合，所以 `scores` 形状是 `(2, 10, 12)`：每个 query 位置对每个 key 位置的点积，等价于 $QK^\top$（`True`）。接着把分数除以 $\sqrt{d}$，沿 `k_pos` 做 softmax（用的就是上一节的减最大值写法），每个 query 的权重之和是 `1`；再用权重对 `v` 加权平均，输出形状 `(2, 10, 8)`，和 `w @ v` 一致。这四行就是**注意力 (attention)** 的全部骨架，ARENA 第 1 章实现 Transformer 时会再写一次。最后一行的线性层：`"batch d_in, d_out d_in -> batch d_out"` 不用手动转置 `W`，因为 einsum 按**名字**对齐维度，这也是它比 `@` 更不容易出形状错的原因。

### 小实验：计算顺序决定速度

einsum 的表达式相同，**收缩的先后顺序**不同，计算量可以差很多。三个矩阵连乘 $ABC$，$A$ 是 $1000\times10$，$B$ 是 $10\times1000$，$C$ 是 $1000\times5$：

""" + C_PATH + r"""

读输出：`(A@B)@C` 先产生一个 $1000\times1000$ 的大矩阵，需要约 1500 万次乘加；`A@(B@C)` 先把 $B$ 和 $C$ 乘成 $10\times5$ 的小矩阵，只需要约 10 万次，**差 150 倍**，结果完全相同（`True`）。`np.einsum_path` 给出的最优顺序 `(1, 2), (0, 1)` 的意思是：先收缩第 1、2 个输入（也就是 $B$ 和 $C$），再和第 0 个（$A$）收缩，正是更省的顺序。**要点**：NumPy 的 `np.einsum` 默认按字面顺序做，加上 `optimize=True` 才会自动找好顺序；PyTorch 的 `torch.einsum` 在装了 `opt_einsum` 库时会自动优化顺序。写多个张量连乘时要想一想顺序。

### 整数数组索引

> **标准定义 · 整数数组索引 (integer array indexing)**
>
> 用**整数数组**（而不是切片或单个整数）作为下标，从张量里取出元素。**一维下标数组**：结果形状等于下标数组的形状，`out[k] = x[idx[k]]`。**多个下标数组**用在不同维度时，它们先**广播**到同一个形状，再**逐位置配对**：`out[k] = x[rows[k], cols[k]]`，而不是「这些行 × 这些列」的子矩阵。整数数组索引返回**副本**。
>
> *English: Indexing with integer arrays picks elements by position. With several index arrays, they are broadcast together and paired element by element, so x[rows, cols] picks the points (rows[k], cols[k]), not a rectangular sub-block. The result is a copy.*

**白话版：「给一张点名册，按名册把人叫出来；两本名册并排看，是一对一对叫，不是排列组合」。**

""" + C_INDEX + r"""

读输出：

1. `prices[items]`：5 件商品，每件对应一个单价，得到 `[2. 1.5 1.5 5. 2.]`，总价 12.0。**结果形状等于下标数组的形状**：二维的下标数组得到二维的结果 `(2, 2)`。
2. 取行 `mat[[0, 2]]`、取列 `mat[:, [1, 3]]` 都很直观。
3. `mat[rows, cols]` 是**配对**：取的是 $(0,3),(1,0),(2,1)$ 三个点，得到 `[3 4 9]`，不是子矩阵。想要「第 0、2 行与第 1、3 列」的 $2\times2$ 子矩阵，要连续索引两次或用 `np.ix_`，两者一致（`True`）。
4. 两个下标数组会**广播**：`np.arange(3)[:, None]`（形状 `(3, 1)`）和 `np.arange(4)`（形状 `(4,)`）一起索引，得到 `(3, 4)`，把整张表都取出来了。可见广播规则在索引里也适用。
5. 坐标如果存成 `(n, 2)` 的数组，`tuple(coords.T)` 把它拆成「行下标数组、列下标数组」的元组，得到 `[3 4 9]`。

上一节手写交叉熵用的 `logp[np.arange(batch), target]` 就是第 3 种写法：每个样本取出自己正确类别那一项。

### 视图 vs 副本，以及重复下标的陷阱

""" + C_COPY + r"""

读输出：**切片**（`a[1:4]`）是视图：改它，原数组也变了（`[0 100 2 3 4 5]`）；**整数数组索引**（`b[[1, 2, 3]]`）是副本：改它，原数组不变。这一点在 PyTorch 里同样成立。第二个陷阱更隐蔽：`z[idx] += 1`，下标 1 出现了 3 次，结果却只加了 1（`[1. 1. 0. 1.]`）。原因是 `z[idx] += 1` 先把 `z[idx]` 读出来（副本），加 1，再写回去，对重复的下标，后写的覆盖先写的，不会累加。要累加必须用 `np.add.at`（PyTorch 里对应 `index_add_` 或 `scatter_add_`），得到 `[1. 3. 0. 1.]`，与 `np.bincount` 一致。**反向传播里，词嵌入的梯度回传到嵌入表上，就要用这种「按下标累加」的操作**：同一个词在一个句子里出现多次，它的梯度要加起来。

### 词嵌入就是查表

""" + C_EMBED + r"""

读输出：`W_E` 是 `(50, 6)` 的嵌入表，`token_ids` 是 `(2, 4)` 的整数数组。`W_E[token_ids]` 的形状是「下标数组的形状 + 取出的那一行的形状」，也就是 `(2, 4, 6)`。同一个 token（`7`，第 0 句的第 1、2 个位置）得到同样的向量（`True`）。它等价于「独热向量乘以矩阵」：`np.eye(50)[token_ids] @ W_E`，结果一样（`True`），但独热张量有 400 个元素，而查表只读取 48 个，**查表更省**。这就解释了 `nn.Embedding` 为什么不是矩阵乘法，而是查表。后半段把「取出每个样本正确类别的概率」写成了索引和独热点乘求和两种形式，结果一致，都是 `[0.7 0.8]`。

### gather

> **标准定义 · gather**
>
> 对 2 维张量，`dim=1` 的 `gather`：$\text{out}[i][j]=\text{input}[i]\big[\text{index}[i][j]\big]$。每一行在自己这一行里，按 `index` 那一行给的**列号**取数；输出形状**和 `index` 一样**；`index` 的维数必须与 `input` 相同。`dim=0` 时则是 $\text{out}[i][j]=\text{input}[\text{index}[i][j]][j]$。NumPy 里对应 `np.take_along_axis`。
>
> *English: torch.gather(input, 1, index) returns out[i][j] = input[i][index[i][j]]. The output has the shape of index, and index must have the same number of dimensions as input.*

**白话版：「每一行各自翻自己的字典」。** `index` 的每一行说「我要这一行的第几列、第几列」。

""" + C_GATHER + r"""

读输出：`mat` 是 $3\times4$ 的 `0..11`，`idx` 的每一行是列号：第 0 行取第 3、0 列得 `[3, 0]`，第 1 行取第 1、1 列得 `[5, 5]`，第 2 行取第 0、2 列得 `[8, 10]`。输出形状和 `idx` 一样（`True`），和按定义写的双重循环一致（`True`）。取每个样本「正确类别的分数」：`gather` 要求 `index` 和 `input` 维数相同，所以要把 `labels` 变成 `(3, 1)`，取完再去掉那一维；用整数数组索引 `scores[np.arange(3), labels]` 更简洁，结果相同（都是 `[2. 1.5 3.]`）。最后随机生成 200 组不同形状的数据，和按定义写的结果对拍，全部通过。

### PyTorch 对照

einops 的 `einsum` 同样支持 `torch` 张量；`gather`、整数数组索引和 `nn.Embedding` 也与上面的 NumPy 对应。

""" + C_TORCH + r"""

### 这一节你要带走的三句话

1. **einsum = 每个下标一层循环，输入元素相乘，累加到输出；不在输出里的下标被求和**；用单词命名下标，比用 `@` 和 `transpose` 更不容易出形状错。多个张量连乘时，计算顺序决定速度。
2. **整数数组索引是「逐对」取元素**，结果形状由下标数组决定，返回副本；多个下标数组会先广播；重复下标的 `+=` 不会累加，要用 `add.at` 一类的专门操作。
3. **`gather` 的规则是 `out[i][j] = input[i][index[i][j]]`**，输出形状等于 `index`；取每个样本的正确类别，`scores[arange, labels]` 和 `gather` 等价，`nn.Embedding` 本质是查表。
"""),
  THINK("写出下面运算的 einsum：给定 `x` 形状 `(batch, d_in)`、`W` 形状 `(d_out, d_in)`，计算线性层 `x @ W.T`；再给定 `A`、`B` 形状都是 `(m, n)`，写出「逐行点积」，得到形状 `(m,)` 的向量。", r"""
```python
einops.einsum(x, W, "batch d_in, d_out d_in -> batch d_out")
einops.einsum(A, B, "m n, m n -> m")
```

线性层里 `d_in` 在两个输入里都有、输出里没有，所以被求和；不用手动转置 `W`，einsum 按名字对齐维度。逐行点积里，`n` 被求和，`m` 保留：$\sum_n A_{mn}B_{mn}$，等价于 `(A * B).sum(axis=1)`。
"""),
  THINK("`einsum(A, B, \"i j, i j ->\")` 算的是什么？它和 `trace(A.T @ B)` 有什么关系？它的计算量（乘加次数）和 `A.T @ B` 再取迹相比如何？", r"""
`i` 和 `j` 都不在输出里，全部求和：$\sum_{i,j}A_{ij}B_{ij}$，是两个矩阵逐元素乘积之和，叫 **Frobenius 内积**。

因为 $\text{tr}(A^\top B)=\sum_i (A^\top B)_{ii}=\sum_i\sum_j A_{ji}B_{ji}$，两者相等（本节 `C_LOOP` 的最后一行验证过）。

计算量：`einsum` 只做 $mn$ 次乘加；先算 `A.T @ B` 要 $n\cdot m\cdot n$ 次乘加（得到 $n\times n$ 矩阵）再取迹，只用到了对角线，大部分计算是浪费的。**直接写成逐元素乘再求和，既短又快**，这就是「知道 einsum 在算什么」的好处。
"""),
  THINK("`scores` 形状 `(batch, n_classes)`，`labels` 形状 `(batch,)`。(1) 用 `gather` 取出每个样本正确类别的分数，得到形状 `(batch,)`；(2) 用整数数组索引再写一遍；(3) 如果 `labels` 里有重复的样本，这两种写法哪个会受重复下标的影响，为什么？", r"""
(1) `scores.gather(1, labels.unsqueeze(1)).squeeze(1)`。`gather` 要求 `index` 与 `input` 维数相同，所以先把 `labels` 变成 `(batch, 1)`，取完再去掉那一维。

(2) `scores[t.arange(batch), labels]`，行下标 `arange` 和列下标 `labels` 逐对配对。

(3) 两种**读取**都不受重复下标影响：读的时候重复下标只是把同一个值读多次。会出问题的是**写入累加**：例如词嵌入的梯度回传，同一个 token 在句子里出现多次，如果写成 `grad[ids] += g`，重复的下标只会生效一次，必须用 `index_add_` / `scatter_add_` 这类按下标累加的操作（本节「视图 vs 副本」的代码块演示过）。
"""),
  KW(("爱因斯坦求和约定","Einstein summation convention","不在输出里的重复下标就求和，省掉求和号"),
     ("einsum","einops.einsum","用下标名字描述「相乘再求和」的整个运算"),
     ("收缩","contraction","沿某些下标相乘并求和，矩阵乘法是最简单的例子"),
     ("内积 / 外积","inner / outer product","`\"i, i ->\"` 求和成标量 / `\"i, j -> i j\"` 两两相乘成矩阵"),
     ("批量矩阵乘法","batched matmul","`\"b i j, b j k -> b i k\"`，batch 维保留"),
     ("注意力分数","attention scores","$QK^\\top$，query 和 key 的点积，`d` 求和"),
     ("Frobenius 内积","Frobenius inner product","$\\sum_{ij} A_{ij}B_{ij}=\\text{tr}(A^\\top B)$"),
     ("收缩顺序","contraction order","多个张量连乘时先算哪两个，计算量可相差数十上百倍"),
     ("整数数组索引","integer array indexing","用下标数组取元素，多个下标数组逐对配对"),
     ("视图 / 副本","view / copy","切片是视图，整数数组索引是副本"),
     ("词嵌入","embedding","`W_E[token_ids]`，按 id 查表，不是矩阵乘法"),
     ("独热向量","one-hot vector","只有一个位置为 1；独热乘矩阵等价于查表"),
     ("gather","torch.gather / take_along_axis","`out[i][j] = input[i][index[i][j]]`，输出形状等于 index"),
     ("按下标累加","add.at / index_add_ / scatter_add_","处理重复下标的累加，`x[idx] += 1` 做不到"),
  ),
 ],
 "references": [
  {"title": "ARENA [0.0] Prerequisites — einsum 与索引练习部分", "url": ARENA_URL, "note": "本节依据的原文大纲和练习（讲解为自写，未转载原文）"},
  {"title": "Einsum is All You Need（Tim Rocktäschel）", "url": "https://rockt.github.io/2018/04/30/einsum", "note": "ARENA 推荐，读到 2.10 节即可"},
  {"title": "einops.einsum 文档", "url": "https://einops.rocks/api/einsum/", "note": "ARENA 使用的 einsum，下标可用完整单词"},
  {"title": "NumPy：Indexing on ndarrays（含 Advanced indexing）", "url": "https://numpy.org/doc/stable/user/basics.indexing.html#integer-array-indexing", "note": "整数数组索引、视图与副本的规则；PyTorch 相同"},
  {"title": "torch.gather 文档", "url": "https://pytorch.org/docs/stable/generated/torch.gather.html", "note": "gather 的规则和维度要求"},
 ],
 "quiz": {"questions": QUIZ},
}

if __name__ == '__main__':
    dump(unit, "arena-0.0", "u15-einsum-indexing.json")
