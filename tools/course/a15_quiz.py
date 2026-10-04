"""ARENA u15 的 10 道测验（沿用旧版题目；解释里的位置引用已改掉）"""
from unitlib import Q
QUIZ = [
  Q('`einops.einsum(A, B, "i j, j k -> i k")` 等价于？', ['`A * B`', '`A @ B`', '`A.T @ B`', '`(A + B).sum()`'], 1, '`j` 在输入中出现、输出中没有，被求和：$C_{ik} = \\sum_j A_{ij}B_{jk}$，就是矩阵乘法。'),
  Q('在 einsum 里，一个下标**会被求和**的条件是？', ['它在输出里出现', '它只在一个输入里出现', '它在输入里出现、但不在输出（箭头右边）里', '它的名字是 `j`'], 2, '规则只有一条：不在输出里的下标就被求和；在输出里的就保留。'),
  Q('`einops.einsum(M, "i i ->")` 计算的是？', ['$M$ 的迹（对角线之和）', '$M$ 的行列式', '$M$ 所有元素之和', '$M$ 的转置'], 0, '同一个张量里下标重复 `i i` 表示取对角线元素，输出为空表示把它们加起来，就是迹。所有元素之和要写 `"i j ->"`。'),
  Q('`u`、`v` 都是长度为 3 的向量，`einops.einsum(u, v, "i, j -> i j")` 的形状是？', ['标量', '`(3,)`', '`(6,)`', '`(3, 3)`'], 3, '没有共同的下标，也就没有求和，结果是 `[i, j] = u[i] * v[j]` 的 3×3 矩阵，即**外积**。'),
  Q('query 形状 `(b, q, d)`，key 形状 `(b, k, d)`，要得到每个 query 和每个 key 的点积，形状 `(b, q, k)`。正确的写法是？', ['`"b q d, b k d -> b q k"`', '`"b q d, b k d -> b d"`', '`"b q d, b k d -> q k"`', '`"b q d, b q d -> b q"`'], 0, '`d` 求和（点积），`b` 保留（每个批次分开算），`q` 和 `k` 两两组合。输出里漏掉 `b` 会把 batch 也加起来；把 key 的维度名写成和 query 一样（`b q d, b q d`）则变成了 query 自己和自己对位相乘，不是两两配对。'),
  Q('`prices = t.tensor([2., 5., 1.5])`，`items = t.tensor([1, 1, 0])`，`prices[items].sum()` 是多少？', ['8.5', '7.0', '12.0', '3.5'], 2, '`prices[items]` = `[5., 5., 2.]`，求和为 12.0。'),
  Q('`mat` 形状 `(3, 4)`，`mat[t.tensor([0, 2]), t.tensor([1, 3])]` 的结果是？', ['第 0、2 行与第 1、3 列交叉处的 2×2 子矩阵', '两个元素：`mat[0, 1]` 和 `mat[2, 3]`', '报错', '第 0 到 2 行、第 1 到 3 列的切片'], 1, '两个下标张量是**逐对配对**的，得到形状 `(2,)` 的结果。想要 2×2 子矩阵要写 `mat[[0, 2]][:, [1, 3]]`。'),
  Q('对 2 维张量，`input.gather(1, index)` 的规则是？', ['`out[i][j] = input[index[i][j]][j]`', '`out[i][j] = input[i][j] * index[i][j]`', '`out = input[index]`', '`out[i][j] = input[i][index[i][j]]`'], 3, '`dim=1` 表示在第 1 维上按下标取：每一行在自己这一行里取 `index[i][j]` 列的值。A 是 `dim=0` 的规则。'),
  Q('`input.gather(1, index)` 的输出形状是？', ['和 `index` 相同', '和 `input` 相同', '总是一维', '`(input.shape[0],)`'], 0, '输出里每个位置都对应 `index` 里的一个下标，所以形状和 `index` 一样。'),
  Q('`logp` 形状 `(batch, n_classes)`，`target` 形状 `(batch,)`，要取出每个样本正确类别的值，下面哪个写法**正确**？', ['`logp[:, target]`', '`logp[target]`', '`logp[t.arange(batch), target]`', '`logp.gather(0, target)`'], 2, '行下标 `t.arange(batch)` 和列下标 `target` 逐对配对，每个样本取一个值，形状 `(batch,)`。`logp[:, target]` 会得到 `(batch, batch)`；`logp[target]` 取的是整行；`gather(0, target)` 用错了维度，而且 `index` 的维数也不对。'),
]
