from runlib import code

C_EXC = code('''
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

# 异常是类，有继承关系：except 会匹配它的子类，所以「具体的在前，宽泛的在后」
print(ZeroDivisionError.__mro__[1:4])
print(issubclass(KeyError, LookupError), issubclass(FileNotFoundError, OSError))

# 主动抛出：raise；自定义异常：继承 Exception
class InvalidScore(ValueError):
    pass

def check_score(x):
    if not 0 <= x <= 100:
        raise InvalidScore(f"分数必须在 0 到 100 之间，收到 {x}")
    return x

try:
    check_score(120)
except ValueError as e:                     # InvalidScore 是 ValueError 的子类，所以能被抓到
    print(type(e).__name__, "|", e)

# raise ... from ...：保留「原因」，方便排查
def load(d, key):
    try:
        return d[key]
    except KeyError as e:
        raise RuntimeError(f"配置缺少 {key!r}") from e

try:
    load({}, "lr")
except RuntimeError as e:
    print(e, "| 原因：", repr(e.__cause__))

# 「请求原谅」(EAFP) 与「先检查」(LBYL)
d = {"a": 1}
try:
    v = d["b"]
except KeyError:
    v = 0
v2 = d.get("b", 0)                          # 对字典，更简洁的写法
print(v, v2)

# finally 与 return：finally 里的内容总会运行
def f():
    try:
        return "try 的返回值"
    finally:
        print("  清理工作先于返回完成")
print(f())

# 裸的 except: / except Exception: 会吞掉所有错误，包括你的 bug
def risky(x):
    try:
        return 10 / x
    except Exception:
        return None                          # 看不出是除零、类型错误还是别的
print(risky(0), risky("a"))                 # 两种完全不同的错误，得到同样的 None
''')

C_TB = code('''
import traceback

src = """
def load_config(d):
    return d["lr"] * 2

def train(cfg):
    return load_config(cfg)

train({"epochs": 3})
"""
try:
    exec(compile(src, "train.py", "exec"))
except KeyError:
    traceback.print_exc()
''', err=True)

C_TEST = code('''
import unittest, io

def median(xs):
    s = sorted(xs)
    n = len(s)
    mid = n // 2
    return s[mid] if n % 2 == 1 else (s[mid - 1] + s[mid]) / 2

def buggy_median(xs):                        # 故意写错的版本：偶数个时只取了后一个
    s = sorted(xs)
    return s[len(s) // 2]

def make_tests(fn):
    class TestMedian(unittest.TestCase):
        def test_odd(self):
            self.assertEqual(fn([3, 1, 2]), 2)
        def test_even(self):
            self.assertEqual(fn([4, 1, 3, 2]), 2.5)
        def test_single(self):
            self.assertEqual(fn([7]), 7)
        def test_empty_raises(self):
            with self.assertRaises(IndexError):
                fn([])
        def test_float(self):
            self.assertAlmostEqual(fn([0.1, 0.2]), 0.15)     # 浮点数不要用 ==
    return unittest.defaultTestLoader.loadTestsFromTestCase(TestMedian)

for name, fn in [("buggy_median", buggy_median), ("median", median)]:
    stream = io.StringIO()
    res = unittest.TextTestRunner(stream=stream, verbosity=0).run(make_tests(fn))
    print(f"{name}: 运行 {res.testsRun} 个测试，失败 {len(res.failures)} 个，出错 {len(res.errors)} 个")
    for case, msg in res.failures:
        print("  失败的用例：", case.id().split(".")[-1], "|", msg.strip().splitlines()[-1])
print(0.1 + 0.2 == 0.3, abs((0.1 + 0.2) - 0.3) < 1e-9)
''')

C_LOG = code('''
import logging, sys

logging.basicConfig(stream=sys.stdout, level=logging.INFO,
                    format="%(levelname)-7s %(name)s: %(message)s")
log = logging.getLogger("train")             # 用模块名区分来源

log.debug("这条不会显示：级别低于 INFO")
log.info("开始训练，lr=%s", 1e-3)            # 用 % 占位符，不要提前拼字符串
log.warning("验证集为空，跳过评估")
try:
    1 / 0
except ZeroDivisionError:
    log.exception("训练出错")                # 自动附上完整的 traceback
log.setLevel(logging.ERROR)
log.warning("现在也不会显示了")
log.error("只有 ERROR 及以上才显示")
''', err=True)

C_TYPE = code('''
from typing import Optional, Callable
from dataclasses import dataclass

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

# 类型注解不会在运行时强制检查！
try:
    mean(["a", "b"])
except TypeError as e:
    print("TypeError（由 sum 内部的加法触发，不是注解检查）：", e)
print(parse(3.9))                                    # 注解说是 str|int，传 float 也照样运行

@dataclass
class Sample:
    x: list[float]
    label: int | None = None
print(Sample([0.1, 0.2]))
''')
