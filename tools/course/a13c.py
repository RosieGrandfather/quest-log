from runlib import code

C_VS = code('''
import numpy as np
from einops import rearrange

x = np.arange(2 * 3 * 2 * 2).reshape(2, 3, 2, 2)      # 形状 (b, c, h, w) = (2, 3, 2, 2)，里面是 0..23
print("原形状", x.shape)

# 目标：把 (b, c, h, w) 变成 (b, h, w, c)
a = x.transpose(0, 2, 3, 1)                            # NumPy 的写法：要数维度编号 0 2 3 1
b = rearrange(x, "b c h w -> b h w c")                 # einops：直接写名字
print("两种写法结果相同：", np.array_equal(a, b), " 形状", b.shape)

# 常见的坑：用 reshape 凑出同样的形状，不会报错，但数据已经「串位」了
wrong = x.reshape(2, 2, 2, 3)                          # 形状也是 (b, h, w, c)，但这只是重新切分了内存里的数
print("reshape 的形状一样：", wrong.shape == b.shape)
print("但内容一样吗：", np.array_equal(wrong, b))
print("第 0 张图、位置 (0,0) 的三个通道，正确答案：", b[0, 0, 0], "  reshape 给出的：", wrong[0, 0, 0])
''')

C_REARR = code('''
import numpy as np
from einops import rearrange

x = np.zeros((32, 3, 28, 28))                          # 32 张 3 通道 28x28 的图片：b c h w

print(rearrange(x, "b c h w -> b h w c").shape)        # 换顺序（转置）
print(rearrange(x, "b c h w -> b (c h w)").shape)      # 括号 = 合并：每张图展平成一个向量
print(rearrange(x, "b c h w -> c h (b w)").shape)      # 把 32 张图横着拼成一长条
print(rearrange(x, "b c h w -> (b h) w c").shape)      # 把 32 张图竖着叠起来

# 拆开：一个维度拆成两个，要告诉 einops 其中一个的大小（另一个由总数算出）
a = np.arange(12)
print(rearrange(a, "(g k) -> g k", g=3))               # 12 拆成 3 组，每组 4 个

# 加上长度为 1 的维度：直接写 1
img = np.arange(16).reshape(4, 4)
print(rearrange(img, "h w -> 1 h w").shape, rearrange(img, "h w -> h w 1").shape)
# 去掉长度为 1 的维度：左边写成 1，右边不写它
print(rearrange(np.zeros((1, 4, 1, 5)), "1 h 1 w -> h w").shape)
''')

C_ORDER = code('''
import numpy as np
from einops import rearrange

a = np.arange(6)
print(rearrange(a, "(h w) -> h w", h=2))   # w 在括号右边：变化快，连续的数在同一行
print(rearrange(a, "(w h) -> h w", h=2))   # h 在括号右边：变化快，连续的数在同一列

# 规则：括号里的「编号」按行优先展开，最右边的变化最快。
# 用 NumPy 自己验证：这两种写法分别等价于 reshape 和 reshape 再转置
print(np.array_equal(rearrange(a, "(h w) -> h w", h=2), a.reshape(2, 3)))
print(np.array_equal(rearrange(a, "(w h) -> h w", h=2), a.reshape(3, 2).T))

# 一个重要用途：把 6 张 2x2 的小图拼成 2 行 3 列的大图
imgs = np.arange(6 * 2 * 2).reshape(6, 2, 2)           # 第 k 张图的像素是 4k..4k+3
grid = rearrange(imgs, "(r c) h w -> (r h) (c w)", r=2)
print(grid.shape)
print(grid)
# 如果把 h 和 r 的顺序写反，每张小图就被撕碎了：
broken = rearrange(imgs, "(r c) h w -> (h r) (w c)", r=2)
print(broken[:2, :4])
''')

C_REDUCE = code('''
import numpy as np
from einops import reduce

rng = np.random.default_rng(0)
x = rng.normal(size=(8, 3, 4, 4))                      # b c h w

print(reduce(x, "b c h w -> c", "mean").shape)         # 右边没写 b、h、w：这三个维度被求平均
print(reduce(x, "b c h w -> b c", "mean").shape)       # 全局平均池化：每张图每个通道一个数
print(reduce(x, "b c h w -> b", "sum").shape)

# 与 NumPy 对拍
print(np.allclose(reduce(x, "b c h w -> c", "mean"), x.mean(axis=(0, 2, 3))))
print(np.allclose(reduce(x, "b c h w -> b c", "max"), x.max(axis=(2, 3))))

# 2x2 池化：把 h、w 各拆成 (块数, 块内位置)，再对块内位置汇总
img = np.arange(16).reshape(4, 4)
print(img)
print(reduce(img, "(h h2) (w w2) -> h w", "max", h2=2, w2=2))
print(reduce(img.astype(float), "(h h2) (w w2) -> h w", "mean", h2=2, w2=2))

# 用最笨的双重循环对拍随机矩阵
big = rng.normal(size=(6, 8))
fast = reduce(big, "(h h2) (w w2) -> h w", "max", h2=2, w2=2)
slow = np.array([[big[2 * i:2 * i + 2, 2 * j:2 * j + 2].max() for j in range(4)] for i in range(3)])
print(fast.shape, np.array_equal(fast, slow))
''')

C_REPEAT = code('''
import numpy as np
from einops import repeat

gray = np.arange(4).reshape(2, 2)
rgb = repeat(gray, "h w -> h w c", c=3)                # 右边多出的维度 c：沿它复制
print(rgb.shape, rgb[0, 1])                            # 第 0 行第 1 列的三个通道是同一个数

v = np.array([1, 2])
print(repeat(v, "d -> (d 3)"))                         # 新维度在右边：每个元素连续重复
print(repeat(v, "d -> (3 d)"))                         # 新维度在左边：整段重复

# 对应 NumPy 的 repeat / tile
print(np.array_equal(repeat(v, "d -> (d 3)"), np.repeat(v, 3)))
print(np.array_equal(repeat(v, "d -> (3 d)"), np.tile(v, 3)))

# 实用例子：给一批图片的每个通道加上不同的偏置，要把形状 (c,) 扩成 (b, c, h, w)
bias = np.array([10, 20, 30])
big = repeat(bias, "c -> b c h w", b=2, h=2, w=2)
print(big.shape, big[1, :, 0, 0])
''')

C_ERR = code('''
import numpy as np
from einops import rearrange, reduce, EinopsError

def try_it(label, fn):
    try:
        fn()
    except EinopsError as e:
        print(label, "-> EinopsError")
    except Exception as e:
        print(label, "->", type(e).__name__)

a = np.arange(7)
try_it("7 拆成 h=2", lambda: rearrange(a, "(h w) -> h w", h=2))
try_it("维度个数对不上", lambda: rearrange(np.zeros((2, 3)), "a b c -> a b c"))
try_it("rearrange 右边少了维度", lambda: rearrange(np.zeros((2, 3)), "a b -> a"))
try_it("拆分时两个大小都没给", lambda: rearrange(np.arange(6), "(h w) -> h w"))
print("reduce 才能丢维度：", reduce(np.zeros((2, 3)), "a b -> a", "sum").shape)
''', err=True)

C_PATCH = code('''
import torch as t
from einops import rearrange

# --- 多头注意力里的形状变换：(batch, seq, n_heads * d_head) <-> (batch, n_heads, seq, d_head) ---
t.manual_seed(0)
batch, seq, n_heads, d_head = 2, 5, 4, 8
x = t.randn(batch, seq, n_heads * d_head)

heads = rearrange(x, "b s (n d) -> b n s d", n=n_heads)   # 拆头 + 把头维度挪到前面
print("拆头后：", tuple(heads.shape))

# 每个头自己算点积分数：(b, n, s, d) 与 (b, n, d, s) 相乘 -> (b, n, s, s)
scores = heads @ rearrange(heads, "b n s d -> b n d s")
print("注意力分数：", tuple(scores.shape))

merged = rearrange(heads, "b n s d -> b s (n d)")         # 反过来：把各头拼回去
print("拼回去后与原来完全相同：", t.equal(merged, x))

# 对拍：PyTorch 的老写法 view + transpose 得到同样的结果
old = x.view(batch, seq, n_heads, d_head).transpose(1, 2)
print("与 view+transpose 相同：", t.equal(old, heads))

# --- 把图片切成小块（Vision Transformer 的第一步）---
img = t.arange(2 * 3 * 4 * 4, dtype=t.float32).reshape(2, 3, 4, 4)       # b c H W，H=W=4
patches = rearrange(img, "b c (h p1) (w p2) -> b (h w) (p1 p2 c)", p1=2, p2=2)
print("块的形状：", tuple(patches.shape), "（每张图 4 个 2x2 小块，每块展平成 12 维）")
# 对拍：手工取第 0 张图的右上角那一块（行 0-1，列 2-3），按 (p1, p2, c) 顺序展平
blk = img[0, :, 0:2, 2:4].permute(1, 2, 0).reshape(-1)
print("与手工取块相同：", t.equal(patches[0, 1], blk))
''')

C_RT = code('''
import numpy as np
from einops import rearrange

# 随机对拍：每个 rearrange 都有「反过来写」的逆操作，来回一趟必须回到原样
rng = np.random.default_rng(1)
ok = True
for _ in range(200):
    b, c, h, w = rng.integers(1, 5, size=4)
    x = rng.normal(size=(b, c, h * 2, w * 3))
    y = rearrange(x, "b c (h h2) (w w2) -> (b h) (c w) h2 w2", h2=2, w2=3)
    z = rearrange(y, "(b h) (c w) h2 w2 -> b c (h h2) (w w2)", b=b, c=c)
    ok = ok and np.array_equal(x, z)
print("200 次来回都还原：", ok)
''')
