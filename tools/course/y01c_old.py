from runlib import code

C_ARGS = code('''
def describe(name, age, /, city="Singapore", *, verbose=False):
    # name、age 只能按位置传（/ 之前）；city 可位置可关键字；verbose 只能用关键字传（* 之后）
    s = f"{name}, {age}, {city}"
    return s + " (verbose)" if verbose else s

print(describe("Yijia", 28))
print(describe("Yijia", 28, "Osaka"))
print(describe("Yijia", 28, city="Tokyo", verbose=True))

def total(*nums, **options):
    # *nums 收集多余的位置参数成元组；**options 收集多余的关键字参数成字典
    s = sum(nums)
    return s * options.get("scale", 1), nums, options

print(total(1, 2, 3))
print(total(1, 2, 3, scale=10, debug=True))

# 反过来：调用时用 * 和 ** 把容器「拆开」传入
args = (1, 2, 3)
kw = {"scale": 2}
print(total(*args, **kw))

# 函数可以返回多个值：其实返回的是一个元组，再被「解包」
def min_max(xs):
    return min(xs), max(xs)
lo, hi = min_max([3, 9, 1, 7])
print(lo, hi, type(min_max([1, 2])))

# 错误的调用方式会得到什么
for bad in ("describe('A', 1, 'X', True)", "describe(name='A', age=1)"):
    try:
        eval(bad)
    except TypeError as e:
        print("TypeError:", e)
''')

C_MUT = code('''
# Python 传参：传的是「对象的引用」。可变对象在函数里被修改，外面能看到；重新赋值则不影响外面
def modify(lst, num):
    lst.append(99)          # 原地修改：外面的列表也变了
    lst = [0]               # 让局部名字 lst 指向一个新列表：外面不受影响
    num += 1                # 整数不可变：这是让局部 num 指向新整数
    return lst, num

a, n = [1, 2], 10
print(modify(a, n), a, n)

# 可变默认参数陷阱：默认值只在「定义函数时」创建一次
def bad(x, bucket=[]):
    bucket.append(x)
    return bucket
print(bad(1), bad(2), bad(3))
print("默认值本身：", bad.__defaults__)

def good(x, bucket=None):
    if bucket is None:
        bucket = []
    bucket.append(x)
    return bucket
print(good(1), good(2))

# 同样的原因：[[0]*3]*3 得到的是 3 个「同一个」列表
grid_bad = [[0] * 3] * 3
grid_bad[0][0] = 1
grid_ok = [[0] * 3 for _ in range(3)]
grid_ok[0][0] = 1
print(grid_bad, grid_ok)
print("is 比较身份：", grid_bad[0] is grid_bad[1], grid_ok[0] is grid_ok[1])
''')

C_SCOPE = code('''
x = "global"

def outer():
    x = "enclosing"
    def inner():
        return x                       # 本地没有 → 去外层函数找（Enclosing）
    return inner()

def uses_global():
    return x                           # 找到全局（Global）

def tries_to_modify():
    try:
        x += "!"                       # 赋值使 x 成为局部变量，但它还没有值
    except UnboundLocalError as e:
        return "UnboundLocalError: " + str(e)

print(outer(), uses_global())
print(tries_to_modify())

# 闭包 (closure)：内层函数「记住」了外层函数的变量，即使外层已经返回
def make_counter():
    count = 0
    def counter():
        nonlocal count                 # 声明要修改的是外层的 count
        count += 1
        return count
    return counter

c1, c2 = make_counter(), make_counter()
print(c1(), c1(), c1(), c2())          # 每个闭包有自己独立的 count
print("闭包保存的变量：", c1.__closure__[0].cell_contents)

# 经典陷阱：闭包「晚绑定」(late binding)——它记住的是变量，不是当时的值
funcs_bad = [lambda: i for i in range(3)]
funcs_ok = [lambda i=i: i for i in range(3)]       # 用默认参数把当时的值固定下来
print([f() for f in funcs_bad], [f() for f in funcs_ok])
''')

C_DECO = code('''
import functools, time

# 函数是「一等公民」：可以赋给变量、放进列表、当参数传、当返回值
def square(x): return x * x
ops = [square, abs, str]
print([f(-3) for f in ops])

words = ["banana", "Apple", "cherry", "date"]
print(sorted(words), sorted(words, key=str.lower), sorted(words, key=len, reverse=True))
print(list(map(lambda w: w.upper(), filter(lambda w: len(w) > 4, words))))

# 装饰器 (decorator)：接收一个函数，返回一个「包装过」的新函数
def timer(func):
    @functools.wraps(func)             # 保留原函数的名字和文档字符串
    def wrapper(*args, **kwargs):
        t = time.perf_counter()
        result = func(*args, **kwargs)
        wrapper.last = time.perf_counter() - t
        return result
    return wrapper

@timer                                 # 等价于 slow_sum = timer(slow_sum)
def slow_sum(n):
    """求 1..n 的和"""
    return sum(range(n + 1))

print(slow_sum(10**6), slow_sum.__name__, "|", slow_sum.__doc__)
print("耗时已被记录：", slow_sum.last > 0)

# 带参数的装饰器：多套一层，先接收参数
def repeat(times):
    def deco(func):
        @functools.wraps(func)
        def wrapper(*a, **k):
            return [func(*a, **k) for _ in range(times)]
        return wrapper
    return deco

@repeat(3)
def hello(name): return f"hi {name}"
print(hello("Yijia"))
''')

C_REC = code('''
import sys
from functools import lru_cache

def fact(n):
    if n == 0:                         # 基础情形 (base case)：不再递归
        return 1
    return n * fact(n - 1)             # 递归情形：把问题缩小

print(fact(5), fact(20))

# 调用栈：每次调用占用一个「栈帧」
def depth(n):
    return 0 if n == 0 else 1 + depth(n - 1)
print("默认递归深度上限：", sys.getrecursionlimit())
print(depth(500))
try:
    depth(100000)
except RecursionError as e:
    print("RecursionError:", e)

# 没有基础情形 → 无限递归
def forever(n): return forever(n + 1)
try:
    forever(0)
except RecursionError:
    print("没有基础情形的递归，最终会 RecursionError")

# 朴素递归重复计算 → 用 lru_cache 记忆化
calls = 0
def fib(n):
    global calls; calls += 1
    return n if n < 2 else fib(n - 1) + fib(n - 2)
fib(25); print("朴素 fib(25) 调用次数：", calls)

calls = 0
@lru_cache(maxsize=None)
def fib2(n):
    global calls; calls += 1
    return n if n < 2 else fib2(n - 1) + fib2(n - 2)
fib2(25); print("记忆化 fib(25) 调用次数：", calls, " cache_info:", fib2.cache_info())

# 递归适合「结构本身是嵌套的」：把任意深度嵌套的列表展平
def flatten(x):
    if not isinstance(x, list):
        return [x]
    out = []
    for item in x:
        out += flatten(item)
    return out
print(flatten([1, [2, [3, [4]], 5], [[6]]]))
''')
