from runlib import Notebook

nb = Notebook()

# ───── 推导式 ─────
C_LISTCOMP = nb.cell('''
nums = list(range(10))

# 列表推导式 = [表达式 for 变量 in 可迭代对象 if 条件]
squares = [x * x for x in nums]
evens = [x for x in nums if x % 2 == 0]
labels = ["even" if x % 2 == 0 else "odd" for x in nums[:4]]   # 条件表达式放在前面，不是 if 过滤
print(squares)
print(evens, labels)
''')

C_EQUIV = nb.cell('''
# 和普通 for 循环完全等价
squares2 = []
for x in nums:
    squares2.append(x * x)
print("等价：", squares == squares2)
''')

C_NEST = nb.cell('''
# 嵌套：先写的 for 是外层循环
matrix = [[1, 2, 3], [4, 5, 6]]
flat = [v for row in matrix for v in row]
transposed = [[row[j] for row in matrix] for j in range(3)]
print(flat, transposed, list(zip(*matrix)))
''')

C_DICTSET = nb.cell('''
# 字典推导式、集合推导式
words = ["apple", "Banana", "cherry", "apple"]
length = {w: len(w) for w in words}                  # 重复的键会被后面的覆盖
first_letters = {w[0].lower() for w in words}        # 集合自动去重
inverted = {v: k for k, v in length.items()}
print(length, sorted(first_letters), inverted)
''')

C_CSCOPE = nb.cell('''
# 推导式里的变量不会泄漏到外面（Python 3）
x = "outer"
_ = [x for x in range(3)]
print("x 仍然是：", x)
''')

C_COMPLEX = nb.cell('''
# 太复杂时，用循环更清楚：下面这种写法不推荐
pairs = [(i, j) for i in range(4) for j in range(4) if i < j and (i + j) % 2 == 1]
print(pairs)
''')

C_SPEED = nb.cell('''
# 推导式和 for + append 算出的结果完全一样；差别只在写法和（通常很小的）速度
n = 1000
a = [x * x for x in range(n)]
r = []
for x in range(n):
    r.append(x * x)
print("两种写法结果一样：", a == r)
''')


# ───── 迭代器 ─────
C_ITER = nb.cell('''
# 可迭代对象 (iterable)：能被 for 遍历；迭代器 (iterator)：记得自己遍历到哪了
lst = [10, 20, 30]
it = iter(lst)                      # 向可迭代对象要一个迭代器
print(type(lst).__name__, type(it).__name__)
print(next(it), next(it), next(it))
try:
    next(it)
except StopIteration:
    print("StopIteration：迭代器用完了")
''')

C_FORLOOP = nb.cell('''
# for 循环其实就是下面这个流程
it = iter(lst)
while True:
    try:
        x = next(it)
    except StopIteration:
        break
    print("取到", x)
''')

C_ONCE = nb.cell('''
# 迭代器是「一次性」的
it = iter(lst)
print(list(it), list(it))           # 第二次是空的！
print(list(lst), list(lst))         # 列表本身可以反复遍历
''')

C_CLASS = nb.cell('''
# 自己写一个迭代器：实现 __iter__ 和 __next__
class Countdown:
    def __init__(self, start):
        self.n = start
    def __iter__(self):
        return self
    def __next__(self):
        if self.n <= 0:
            raise StopIteration
        self.n -= 1
        return self.n + 1

print(list(Countdown(5)))
print(sum(Countdown(100)), max(Countdown(3)))
''')

C_LAZY = nb.cell('''
# 常见的惰性迭代器：zip、enumerate、map、filter、reversed、range、文件对象
names, scores = ["A", "B", "C"], [90, 85, 70]
z = zip(names, scores)
print(type(z).__name__, list(z), list(z))   # zip 对象也是一次性的
''')

C_ZIP = nb.cell('''
for i, (n, s) in enumerate(zip(names, scores), start=1):
    print(i, n, s)
print(list(zip([1, 2, 3], "ab")))   # 以最短的为准
print(dict(zip(names, scores)))
''')

# ───── 生成器 ─────
C_YIELD = nb.cell('''
# 生成器函数：用 yield 代替 return；每次 next() 运行到下一个 yield 就暂停
def count_up(n):
    print("  开始")
    for i in range(n):
        print(f"  准备产出 {i}")
        yield i
        print(f"  {i} 已被取走")
    print("  结束")

g = count_up(2)
print("创建了生成器，函数体还没有运行：", type(g).__name__)
print("next ->", next(g))
print("next ->", next(g))
try:
    next(g)
except StopIteration:
    print("StopIteration")
''')

C_GENEXP = nb.cell('''
import sys

# 生成器表达式：把推导式的 [] 换成 ()，惰性求值，几乎不占内存
big_list = [i * i for i in range(1_000_000)]
big_gen = (i * i for i in range(1_000_000))
print("列表占用是生成器的 100 倍以上：", sys.getsizeof(big_list) > 100 * sys.getsizeof(big_gen))
print(sum(big_gen))                  # 一边算一边累加，内存始终只有一个元素
''')

C_INF = nb.cell('''
# 无限序列：只有惰性才能表示；用 islice 取前几个
from itertools import islice
def fib():
    a, b = 0, 1
    while True:
        yield a
        a, b = b, a + b
print(list(islice(fib(), 12)))
''')

C_PIPE = nb.cell('''
# 生成器流水线：每一步只处理一个元素
def read_lines():
    for line in ["  alpha ", "", "beta", "  ", "gamma  "]:
        yield line
def strip(lines):
    for l in lines: yield l.strip()
def non_empty(lines):
    for l in lines:
        if l: yield l
print(list(non_empty(strip(read_lines()))))
''')

C_BATCH = nb.cell('''
# 批量读取：和 DataLoader 的思路一样——每次产出 batch_size 条数据
def batches(data, batch_size):
    for i in range(0, len(data), batch_size):
        yield data[i:i + batch_size]
print(list(batches(list(range(10)), 4)))
''')

C_YF = nb.cell('''
# yield from：把内层可迭代对象的元素逐个转发
def chain_two(a, b):
    yield from a
    yield from b
print(list(chain_two([1, 2], "xy")))
''')

# ───── itertools 与 collections ─────
C_ITT = nb.cell('''
from itertools import chain, product, combinations, permutations, accumulate, groupby, count

print(list(chain([1, 2], [3], "ab")))
print(list(product([0, 1], repeat=2)))                 # 笛卡尔积
print(list(combinations("ABC", 2)))                   # 不计顺序的选 2 个
print(len(list(permutations(range(4)))), "= 4! =", 4*3*2*1)
print(list(accumulate([1, 2, 3, 4])))                 # 前缀和（上一节讲过的思路）
print(list(zip(count(1), "abc")))                     # count 是无限计数器
''')

C_GROUPBY = nb.cell('''
# groupby 只合并「相邻」的相同键，所以通常要先排序
data = ["apple", "avocado", "banana", "blueberry", "cherry", "apricot"]
print([(k, list(g)) for k, g in groupby(data, key=lambda w: w[0])])
print([(k, list(g)) for k, g in groupby(sorted(data), key=lambda w: w[0])])
''')

C_COUNTER = nb.cell('''
from collections import Counter, defaultdict, deque, namedtuple

# Counter：数频次
text = "the cat and the hat and the bat"
cnt = Counter(text.split())
print(cnt.most_common(2), cnt["the"], cnt["dog"])
''')

C_DDICT = nb.cell('''
# defaultdict：不存在的键自动创建默认值
groups = defaultdict(list)
for w in data:
    groups[w[0]].append(w)
print(dict(groups))
''')

C_DEQUE = nb.cell('''
# deque：双端队列，maxlen 让它只保留最近的几个
dq = deque(maxlen=3)
for i in range(6):
    dq.append(i)
print("只保留最近 3 个：", list(dq))
''')

C_NT = nb.cell('''
# namedtuple：带字段名的轻量元组
Point = namedtuple("Point", ["x", "y"])
p = Point(3, 4)
print(p, p.x, p[1], p._asdict())
''')
