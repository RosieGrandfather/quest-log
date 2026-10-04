from runlib import Notebook

nb = Notebook()

# ───────────── 一、异常处理：回顾与进阶 ─────────────
C_REVIEW = nb.cell('''
# 回顾：try / except ... as e，以及怎样问「这是什么异常」
def safe_div(a, b):
    try:
        return a / b
    except ZeroDivisionError as e:          # as e：把异常对象交给变量 e
        print("捕获到：", type(e).__name__, "|", e)
        return None

print(safe_div(6, 3))
print(safe_div(1, 0))

try:
    int("abc")
except (ValueError, TypeError) as e:        # 一个 except 可以用元组同时接几种类型
    print(type(e).__name__, "|", e)
''')

C_EXC = nb.cell('''
def parse_age(s):
    try:
        age = int(s)                        # 可能抛出 ValueError
        result = 100 // age                 # 可能抛出 ZeroDivisionError
    except ValueError as e:
        return f"不是整数：{e}"
    except ZeroDivisionError:
        return "年龄不能是 0"
    else:                                   # 没有异常时才执行
        return f"100 // age = {result}"
    finally:                                # 无论如何都执行（用于清理）
        print("  [finally 执行了]", repr(s))

for s in ["25", "abc", "0"]:
    print(parse_age(s))
''')

C_HIER = nb.cell('''
# 异常是类，有继承关系：except 会匹配它的子类，所以「具体的在前，宽泛的在后」
print(ZeroDivisionError.__mro__[1:4])
print(issubclass(KeyError, LookupError), issubclass(FileNotFoundError, OSError))

try:
    1 / 0
except ArithmeticError:                     # 写的是父类，也能抓住子类 ZeroDivisionError
    print("ZeroDivisionError 被 except ArithmeticError 抓住了")
''')

C_RAISE = nb.cell('''
# 主动抛出：raise；自定义异常：继承 Exception
class InvalidScore(ValueError):
    pass

def check_score(x):
    if not 0 <= x <= 100:
        raise InvalidScore(f"分数必须在 0 到 100 之间，收到 {x}")
    return x

print(check_score(60))
try:
    check_score(120)
except ValueError as e:                     # InvalidScore 是 ValueError 的子类，所以能被抓到
    print(type(e).__name__, "|", e)
''')

C_CUSTOM2 = nb.cell('''
# 进阶：给一个项目设计一套自己的异常层级
class DataError(Exception):                  # 项目的「根异常」：其他自定义异常都继承它
    pass

class MissingColumn(DataError):
    def __init__(self, name, available):
        super().__init__(f"缺少列 {name!r}，现有列：{available}")   # 把信息交给父类保存
        self.name = name                     # 还可以带上额外的字段，方便调用者使用

def get_col(row, name):
    if name not in row:
        raise MissingColumn(name, sorted(row))
    return row[name]

try:
    get_col({"x1": 1, "x2": 2}, "label")
except DataError as e:                       # 只抓「根异常」，就能抓住这个项目里所有的数据错误
    print(type(e).__name__, "|", e)
    print("缺的列：", e.name, "| 是 DataError 吗：", isinstance(e, DataError))
''')

C_FROM = nb.cell('''
# raise ... from ...：保留「原因」，方便排查
def load(d, key):
    try:
        return d[key]
    except KeyError as e:
        raise RuntimeError(f"配置缺少 {key!r}") from e

try:
    load({}, "lr")
except RuntimeError as e:
    print(e)
    print("原因：", repr(e.__cause__))
''')

C_EAFP = nb.cell('''
d = {"a": 1}

# EAFP：先做，出错再处理
try:
    v = d["b"]
except KeyError:
    v = 0

# LBYL：先检查，再做
v2 = d["b"] if "b" in d else 0

v3 = d.get("b", 0)                          # 对字典，更简洁的写法
print(v, v2, v3)
''')

C_FINALLY = nb.cell('''
# finally 与 return：finally 里的内容总会运行
def f():
    try:
        return "try 的返回值"
    finally:
        print("  清理工作先于返回完成")

print(f())
''')

C_BARE = nb.cell('''
# 裸的 except: / except Exception: 会吞掉所有错误，包括你的 bug
def risky(x):
    try:
        return 10 / x
    except Exception:
        return None                          # 看不出是除零、类型错误还是别的

print(risky(0), risky("a"))                  # 两种完全不同的错误，得到同样的 None
''')

# ───────────── 上下文管理器与 with ─────────────
C_WITH1 = nb.cell('''
class Section:                               # 最小的上下文管理器：有 __enter__ 和 __exit__ 两个方法
    def __init__(self, name):
        self.name = name

    def __enter__(self):                     # 进入 with 时调用；返回值交给 as 后面的名字
        print(f"[进入] {self.name}")
        return self

    def __exit__(self, exc_type, exc, tb):   # 离开 with 时一定调用，哪怕里面出了异常
        print(f"[离开] {self.name}，异常：{exc_type.__name__ if exc_type else None}")
        return False                         # False：不吞掉异常，让它继续向外传

with Section("正常") as s:
    print("  做事情，s.name =", s.name)

try:
    with Section("出错"):
        1 / 0
except ZeroDivisionError:
    print("异常继续传出来了")
''')

C_WITH2 = nb.cell('''
from contextlib import contextmanager

@contextmanager                              # 装饰器：把一个「只 yield 一次的生成器」变成上下文管理器
def opened(name):
    print("打开", name)
    try:
        yield name.upper()                   # yield 之前 = __enter__；yield 的值交给 as
    finally:
        print("关闭", name)                  # yield 之后 = __exit__；finally 保证一定执行

with opened("data.csv") as n:
    print("使用", n)
''')

# ───────────── 二、读 traceback 与调试 ─────────────
C_TB = nb.cell('''
import sys, traceback

src = """
def load_config(d):
    return d["lr"] * 2

def train(cfg):
    return load_config(cfg)

train({"epochs": 3})
"""
try:
    exec(compile(src, "train.py", "exec"))          # 把上面的脚本当作 train.py 运行
except KeyError as e:
    # 跳过最外面一层（我们这个 exec 外壳），只打印 train.py 里的调用栈
    traceback.print_exception(type(e), e, e.__traceback__.tb_next, file=sys.stdout)
''')

C_ASSERT = nb.cell('''
def check_batch(x, batch, dim):
    # assert 条件, "出错信息"：条件不成立时立刻抛出 AssertionError
    assert len(x) == batch, f"batch 大小不对：{len(x)} != {batch}"
    assert all(len(row) == dim for row in x), "每一行的长度应该是 dim"
    return "形状检查通过"

x = [[0.0] * 3 for _ in range(4)]            # 4 行 3 列
print(check_batch(x, 4, 3))
try:
    check_batch(x, 5, 3)
except AssertionError as e:
    print("AssertionError:", e)
''')

# ───────────── 三、单元测试 ─────────────
C_MEDIAN = nb.cell('''
def median(xs):
    s = sorted(xs)
    n = len(s)
    mid = n // 2
    return s[mid] if n % 2 == 1 else (s[mid - 1] + s[mid]) / 2

def buggy_median(xs):                        # 故意写错的版本：偶数个时只取了后一个
    s = sorted(xs)
    return s[len(s) // 2]

# 手动试几个输入：只能验证「现在」，每次都要人眼去比
print(median([3, 1, 2]), median([4, 1, 3, 2]))
print(buggy_median([3, 1, 2]), buggy_median([4, 1, 3, 2]))
''')

C_UNIT = nb.cell('''
import unittest

class TestMedian(unittest.TestCase):         # 一个测试类；每个 test_ 开头的方法是一个用例
    fn = staticmethod(median)                # 被测的函数，放在类属性里，方便换成别的版本
    def test_odd(self):
        self.assertEqual(self.fn([3, 1, 2]), 2)
    def test_even(self):
        self.assertEqual(self.fn([4, 1, 3, 2]), 2.5)
    def test_single(self):
        self.assertEqual(self.fn([7]), 7)
    def test_empty_raises(self):
        with self.assertRaises(IndexError):  # 断言：这里应当抛出 IndexError
            self.fn([])
    def test_float(self):
        self.assertAlmostEqual(self.fn([0.1, 0.2]), 0.15)     # 浮点数不要用 ==

class TestBuggyMedian(TestMedian):           # 继承：同一套测试，换成有 bug 的函数
    fn = staticmethod(buggy_median)
''')

C_UNITRUN = nb.cell('''
import io

def run(label, case):
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(case)
    res = unittest.TextTestRunner(stream=io.StringIO(), verbosity=0).run(suite)
    print(f"{label}: 运行 {res.testsRun} 个测试，失败 {len(res.failures)} 个，出错 {len(res.errors)} 个")
    for t, msg in res.failures:
        print("  失败的用例：", t.id().split(".")[-1], "|", msg.strip().splitlines()[-1])

run("buggy_median", TestBuggyMedian)
run("median", TestMedian)
''')

C_FLOAT = nb.cell('''
import math

print(0.1 + 0.2 == 0.3)                      # 浮点数有舍入误差
print(abs((0.1 + 0.2) - 0.3) < 1e-9)         # 在容差范围内比较
print(math.isclose(0.1 + 0.2, 0.3))          # 标准库现成的写法
''')

C_PYT_SRC = nb.cell('''
from pathlib import Path

# 先写被测的模块 stats.py（真实项目里它就是一个普通的 .py 文件）
Path("stats.py").write_text("""
def median(xs):
    s = sorted(xs)
    n = len(s)
    mid = n // 2
    return s[mid] if n % 2 == 1 else (s[mid - 1] + s[mid]) / 2
""")
print("stats.py 已写入，共", len(Path("stats.py").read_text().splitlines()), "行")
''')

C_PYT_TEST = nb.cell('''
# 再写 pytest 风格的测试文件 test_stats.py：不需要写类，直接写函数和 assert
Path("test_stats.py").write_text("""
import pytest
from stats import median

def test_odd():
    assert median([3, 1, 2]) == 2

def test_even():
    assert median([4, 1, 3, 2]) == 2.5

def test_float():
    assert median([0.1, 0.2]) == pytest.approx(0.15)

@pytest.mark.parametrize("xs, expected", [([1], 1), ([1, 2], 1.5), ([5, 1, 3], 3)])
def test_many(xs, expected):          # 一组输入，自动展开成多个测试
    assert median(xs) == expected

def test_empty():
    with pytest.raises(IndexError):
        median([])
""")
print(len(Path("test_stats.py").read_text().split("def test_")) - 1, "个测试函数")
''')

C_PYT_RUN = nb.cell('''
import sys, io, contextlib, importlib, pytest

class Collect:                               # 一个小插件：把每个用例的结果收集起来，方便打印
    def __init__(self):
        self.results = []
    def pytest_runtest_logreport(self, report):
        if report.when == "call":
            msg = report.longrepr.reprcrash.message.splitlines()[0] if report.failed else ""
            self.results.append((report.nodeid.split("::")[-1], report.outcome, msg))

def run_pytest():
    sys.dont_write_bytecode = True
    for m in ("stats", "test_stats"):        # 重新读取刚写的文件，不用缓存的旧模块
        sys.modules.pop(m, None)
    importlib.invalidate_caches()
    c = Collect()
    with contextlib.redirect_stdout(io.StringIO()):     # 屏蔽 pytest 自己打印的进度和统计
        code = pytest.main(["-q", "-s", "-p", "no:cacheprovider", "test_stats.py"], plugins=[c])
    print("退出码：", int(code))              # 0 表示全部通过
    for name, outcome, msg in c.results:
        print(f"  {name}: {outcome} {msg}".rstrip())

run_pytest()
''')

C_PYT_BUG = nb.cell('''
# 把 stats.py 换成有 bug 的版本，再用同一份测试跑一遍
Path("stats.py").write_text("""
def median(xs):
    s = sorted(xs)
    return s[len(s) // 2]
""")
run_pytest()
''')

# ───────────── 四、日志 ─────────────
C_LOG = nb.cell('''
import logging, sys

def setup(level=logging.INFO):               # 真实脚本只在入口处配置一次；这里每次重新指向当前输出区
    logging.basicConfig(stream=sys.stdout, level=level, force=True,
                        format="%(levelname)-7s %(name)s: %(message)s")
    logging.getLogger("train").setLevel(logging.NOTSET)

setup()
log = logging.getLogger("train")             # 用模块名区分来源

log.debug("这条不会显示：级别低于 INFO")
log.info("开始训练，lr=%s", 1e-3)            # 用 % 占位符，不要提前拼字符串
log.warning("验证集为空，跳过评估")
''')

C_LOGEXC = nb.cell('''
setup()
try:
    1 / 0
except ZeroDivisionError:
    log.exception("训练出错")                # 自动附上完整的 traceback
''')

C_LOGLEVEL = nb.cell('''
setup()
log.setLevel(logging.ERROR)                  # 只让 ERROR 及以上通过
log.warning("现在也不会显示了")
log.error("只有 ERROR 及以上才显示")
''')

# ───────────── 五、类型注解 ─────────────
C_TYPE = nb.cell('''
from typing import Optional, Callable

def mean(xs: list[float]) -> float:                  # 参数和返回值的类型注解
    return sum(xs) / len(xs)

def find(d: dict[str, int], key: str) -> Optional[int]:   # Optional[int] 就是 int | None
    return d.get(key)

def apply(f: Callable[[int], int], xs: list[int]) -> list[int]:
    return [f(x) for x in xs]

def parse(s: str | int) -> int:                      # Python 3.10+ 的联合类型写法
    return int(s)

print(mean([1, 2, 3]), find({"a": 1}, "b"), apply(lambda x: x + 1, [1, 2]), parse("7"))
print(mean.__annotations__)
''')

C_TYPE2 = nb.cell('''
# 类型注解不会在运行时强制检查！
try:
    mean(["a", "b"])
except TypeError as e:
    print("TypeError（由 sum 内部的加法触发，不是注解检查）：", e)
print(parse(3.9))                                    # 注解说是 str|int，传 float 也照样运行
''')

C_TYPE3 = nb.cell('''
from dataclasses import dataclass

@dataclass
class Sample:
    x: list[float]
    label: int | None = None

print(Sample([0.1, 0.2]))
print(Sample.__annotations__)
''')
