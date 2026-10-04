from runlib import Notebook

nb = Notebook()

# ───── 为什么需要容器 ─────
C_WHY = nb.cell('''
# 三个订单的箱数：每个订单一个变量
qty1 = 12
qty2 = 30
qty3 = 7
print(qty1 + qty2 + qty3)       # 如果有 1000 个订单呢？要写 1000 个变量吗？

# 容器：一个变量装下一批数据
qtys = [12, 30, 7]
print(qtys)
print(len(qtys), sum(qtys), max(qtys))
''')

# ───── 列表 ─────
C_L_CREATE = nb.cell('''
qtys = [12, 30, 7, 25]              # 方括号 + 逗号分隔
names = ["pen", "ink", "pad"]
mixed = [1, "a", 2.5, True]         # 可以混装，但实际中通常装同一类东西
empty = []                          # 空列表
print(type(qtys), len(qtys), len(empty))
print(names, mixed)
print(list("abc"), list(range(4)))  # list(...) 把别的序列转成列表
''')

C_L_INDEX = nb.cell('''
skus = ["A100", "B200", "C300", "D400"]
print(skus[0], skus[1])             # 编号从 0 开始
print(skus[-1], skus[-2])           # 负数：从末尾倒数
print(len(skus))
''')

C_L_INDEXERR = nb.cell('''
print(skus[4])                      # 4 个元素，合法编号只有 0 到 3
''', err=True)

C_L_SLICE = nb.cell('''
nums = [10, 20, 30, 40, 50, 60]
print(nums[1:4])                    # 从编号 1 到 3（不含 4）
print(nums[:3], nums[3:])           # 省略开头 / 结尾
print(nums[::2])                    # 每隔一个取一个
print(nums[::-1])                   # 步长 -1：倒过来
print(nums[1:100])                  # 切片越界不报错，取到末尾为止
print(nums)                         # 切片得到新列表，原来的没变
''')

C_L_SET = nb.cell('''
stock = [50, 20, 0]
stock[2] = 15                       # 通过编号直接改一个元素
print(stock)
stock[0:2] = [1, 2, 3]              # 切片也可以整段替换
print(stock)
''')

C_L_ADD = nb.cell('''
box = ["A", "B"]
box.append("C")                     # 末尾加一个
print(box)
box.insert(0, "Z")                  # 在编号 0 处插入，后面的往后挪
print(box)
box.extend(["X", "Y"])              # 末尾接上另一批
print(box)
''')

C_L_APPEXT = nb.cell('''
a = [1, 2]
a.append([3, 4])                    # 把 [3, 4] 当作「一个」元素放进去
print(a, len(a))
b = [1, 2]
b.extend([3, 4])                    # 把 3 和 4「分别」放进去
print(b, len(b))
''')

C_L_REMOVE = nb.cell('''
q = ["a", "b", "c", "b", "d"]
last = q.pop()                      # 取出并返回最后一个
print(last, q)
first = q.pop(0)                    # 取出并返回编号 0 的
print(first, q)
q.remove("b")                       # 按「值」删，只删第一个匹配的
print(q)
del q[0]                            # 按「编号」删（del 是语句，不是方法）
print(q)
''')

C_L_REMOVEERR = nb.cell('''
q.remove("zzz")                     # 列表里没有 "zzz"
''', err=True)

C_L_IN = nb.cell('''
status = ["new", "paid", "paid", "shipped"]
print("paid" in status, "cancelled" in status)
print("cancelled" not in status)
print(status.index("paid"))         # 第一个 "paid" 的编号
print(status.count("paid"))         # "paid" 出现几次
''')

C_L_SORT = nb.cell('''
days = [7, 3, 10, 5]
print(sorted(days), days)           # sorted：返回新列表，原来的不动
r = days.sort()                     # sort：就地排序，返回 None
print(r, days)
days.sort(reverse=True)             # 从大到小
print(days)
print(sorted(["pear", "fig", "banana"], key=len))   # key=len：按长度比大小
''')

C_L_OPS = nb.cell('''
a = [1, 2, 3]
b = [4]
print(a + b, a * 2)                 # + 拼接，* 重复
print(sum(a), min(a), max(a), len(a))
a.reverse()                         # 就地倒过来（和 sort 一样，返回 None）
print(a)
''')

C_L_NEST = nb.cell('''
grid = [[1, 2, 3], [4, 5, 6]]       # 列表的元素也可以是列表：2 行 3 列
print(grid[0], len(grid))
print(grid[1][2])                   # 先选第 1 行，再选这一行的第 2 个
grid[0][1] = 99
print(grid)
''')

# ───── 元组 ─────
C_T_BASIC = nb.cell('''
point = (3, 4)                      # 圆括号 + 逗号
print(point[0], point[-1], len(point), type(point))
print(point[0:1])                   # 切片也能用，得到新元组
print((1, 2, 2).count(2), (1, 2, 2).index(2))   # 只有两个方法
''')

C_T_IMMUT = nb.cell('''
point[0] = 9                        # 元组不允许改
''', err=True)

C_T_ONE = nb.cell('''
a = (5)                             # 括号只是括号
b = (5,)                            # 逗号才是元组
c = 5,                              # 连括号都可以省
print(type(a), type(b), type(c))
print(b, c, ())                     # () 是空元组
''')

C_T_PACK = nb.cell('''
t = 12, "pen", 3.5                  # 打包：几个值用逗号连起来，就是一个元组
print(t, type(t))
qty, name, price = t                # 解包：按位置拆给三个变量
print(qty, name, price)
x, y = [10, 20]                     # 任何序列都能解包，不只是元组
print(x, y)
''')

C_T_FUNC = nb.cell('''
# 函数：起了名字的一小段代码；def 定义它，return 把结果交出来
def min_max(nums):
    return min(nums), max(nums)     # return a, b：返回的就是一个元组

result = min_max([4, 9, 2, 7])
print(result, type(result))
lo, hi = min_max([4, 9, 2, 7])      # lo 和 hi 是两个变量，用逗号隔开
print(lo, hi)
''')

C_T_SWAP = nb.cell('''
a, b = 1, 2
a, b = b, a                         # 交换：右边先打包成 (2, 1)，再解包给 a, b
print(a, b)
''')

C_T_STAR = nb.cell('''
first, *rest = [10, 20, 30, 40]     # * 让 rest 接住「剩下的全部」，结果是列表
print(first, rest)
*init, last = [10, 20, 30, 40]
print(init, last)
head, *middle, tail = [10, 20, 30, 40]
print(head, middle, tail)
a, _, c = ("pen", 12, 3.5)          # _ 约定：这个值我不要
print(a, c)
''')

C_T_MISMATCH = nb.cell('''
a, b = (1, 2, 3)                    # 左边 2 个变量，右边 3 个值
''', err=True)

C_T_MISMATCH2 = nb.cell('''
a, b, c = (1, 2)                    # 左边 3 个，右边只有 2 个
''', err=True)

C_T_INNER = nb.cell('''
t = ([1, 2], "x")                   # 元组里装了一个列表
t[0].append(3)                      # 改的是列表本身，元组没有换掉任何一个格子
print(t)
''')

# ───── 字典 ─────
C_D_BASIC = nb.cell('''
stock = {"A100": 50, "B200": 20, "C300": 0}     # 花括号，键: 值
print(stock["A100"])                # 用键取值
print(len(stock), type(stock))
print(stock)
''')

C_D_KEYERR = nb.cell('''
print(stock["Z999"])                # 没有这个键
''', err=True)

C_D_GET = nb.cell('''
print(stock.get("Z999"))            # 找不到：返回 None，不报错
print(stock.get("Z999", 0))         # 找不到：返回你给的默认值 0
print(stock.get("A100", 0))         # 找得到：返回真正的值，默认值不起作用

options = {"mode": "fast"}
scale = options.get("scale", 1)     # 没有 scale 这个设置，就当它是 1
print(scale)
''')

C_D_MODIFY = nb.cell('''
stock["D400"] = 8                   # 键不存在：新增
stock["A100"] = 45                  # 键已存在：覆盖
print(stock)
del stock["C300"]                   # 删除一个键值对
print(stock)
removed = stock.pop("B200")         # 取出并返回值，同时删掉
print(removed, stock)
print(stock.pop("Z999", "没有这个键"))   # pop 也可以给默认值
''')

C_D_IN = nb.cell('''
stock["A100"] = 50
print("A100" in stock, "Z999" in stock)    # in 查的是键
print(50 in stock)                  # 50 是值，不是键
print(50 in stock.values())         # 查值要用 .values()
''')

C_D_KVI = nb.cell('''
prices = {"pen": 3, "ink": 12, "pad": 8}
print(prices.keys())                # 所有的键
print(prices.values())              # 所有的值
print(prices.items())               # 所有的 (键, 值) 对，每对是一个元组
print(list(prices.keys()), sum(prices.values()), len(prices))
''')

C_D_ITER = nb.cell('''
# for 变量 in 容器: 缩进的那几行，对容器里的每个元素各执行一次
for sku in prices:                  # 遍历字典，拿到的是键
    print(sku)
for sku, price in prices.items():   # 每个元素是 (键, 值) 元组，直接解包
    print(sku, "->", price)
''')

C_D_METHODS = nb.cell('''
names = dir({})                     # dir：列出一个对象有哪些方法
public = []
for n in names:
    if not n.startswith("_"):       # 跳过下划线开头的（内部用的）
        public.append(n)
print(public)
''')

C_D_UPDATE = nb.cell('''
inv = {"A": 10}
inv.update({"B": 5, "A": 12})       # 合并另一个字典：已有的键被覆盖
print(inv)
inv.setdefault("C", 0)              # 键不存在才设置；存在就什么都不做
inv.setdefault("A", 999)
print(inv)
print(inv.setdefault("D", 1))       # 返回的是这个键最后对应的值
''')

C_D_COUNT = nb.cell('''
words = ["pen", "ink", "pen", "pad", "pen"]
count = {}
for w in words:
    count[w] = count.get(w, 0) + 1  # 没见过：0 + 1；见过：旧次数 + 1
print(count)
''')

C_D_TUPKEY = nb.cell('''
loc = {("W1", "R3"): 40, ("W1", "R4"): 0}   # 用 (仓库, 货架) 元组当键
print(loc[("W1", "R3")])
''')

C_D_BADKEY = nb.cell('''
bad = {[1, 2]: "x"}                 # 列表是可变的，不能当键
''', err=True)

C_D_NEST = nb.cell('''
order = {"id": 1001, "customer": "ACME", "items": {"pen": 10, "ink": 2}}
print(order["customer"])
print(order["items"]["pen"])        # 先取 "items"，再取里面的 "pen"
order["items"]["ink"] = 5
print(order["items"])
''')

C_D_LIST = nb.cell('''
orders = [
    {"id": 1001, "qty": 12, "status": "paid"},
    {"id": 1002, "qty": 30, "status": "new"},
    {"id": 1003, "qty": 7, "status": "paid"},
]
print(len(orders), orders[1]["qty"])    # 先选第几个订单，再选字段
orders.append({"id": 1004, "qty": 5, "status": "new"})
total = 0
for o in orders:
    total = total + o["qty"]
print(total, orders[-1]["id"])
''')

C_D_GROUP = nb.cell('''
by_status = {}
for o in orders:
    by_status.setdefault(o["status"], []).append(o["id"])   # 没有就先造空列表
print(by_status)
''')

# ───── 集合 ─────
C_S_DEDUP = nb.cell('''
ids = [3, 1, 3, 2, 1, 3]
uniq = set(ids)                     # 列表 -> 集合：重复的自动去掉
print(uniq, len(uniq))
print(sorted(uniq))                 # 要有顺序，就 sorted 一下，得到列表
''')

C_S_IN = nb.cell('''
allowed = {"A100", "B200", "C300"}
print("A100" in allowed, "Z" in allowed)
allowed.add("D400")                 # 加入
allowed.add("A100")                 # 已经有了：什么都不发生
print(len(allowed))
allowed.discard("B200")             # 删除（不存在也不报错）
print(sorted(allowed))
''')

C_S_OPS = nb.cell('''
mon = {"A", "B", "C"}               # 周一出过货的 SKU
tue = {"B", "C", "D"}               # 周二出过货的 SKU
print(sorted(mon | tue))            # 并集：任一天出过
print(sorted(mon & tue))            # 交集：两天都出过
print(sorted(mon - tue))            # 差集：周一有、周二没有
print(sorted(mon ^ tue))            # 只在其中一天出现
''')

C_S_EMPTY = nb.cell('''
a = {}
b = set()
print(type(a).__name__, type(b).__name__)   # {} 是空字典！
print(set("hello") == set("olleh"))         # 集合不在乎顺序
''')

C_S_SUBS = nb.cell('''
s = {10, 20, 30}
print(s[0])                         # 集合没有「第几个」
''', err=True)

# ───── 可变与别名 ─────
C_A_ALIAS = nb.cell('''
a = [1, 2, 3]
b = a                               # 不是复制！只是给同一个列表再贴一个名字
b.append(4)
print(a, b)
print(a is b)                       # is：是不是同一个对象
''')

C_A_COPY = nb.cell('''
a = [1, 2, 3]
c = a.copy()                        # 真的复制一份（a[:] 和 list(a) 同样效果）
c.append(4)
print(a, c, a is c)
''')

C_A_DEEP = nb.cell('''
import copy
grid = [[1, 2], [3, 4]]
g2 = grid.copy()                    # 浅复制：只复制外层，里面的小列表还是共用的
g2[0].append(99)
print(grid)
g3 = copy.deepcopy(grid)            # 深复制：里里外外全部复制
g3[1].append(77)
print(grid, g3)
''')

C_A_IMMUT = nb.cell('''
x = 5
y = x
y = y + 1                           # 整数不可变：y 指向了新的整数 6
print(x, y)
s = "abc"
t = s.upper()                       # 字符串不可变：upper 返回新字符串
print(s, t)
''')

C_A_FUNC = nb.cell('''
def add_item(box, item):
    box.append(item)                # 改的就是调用者传进来的那个列表

cart = ["pen"]
add_item(cart, "ink")
print(cart)                         # 函数没 return，cart 却变了
''')
