from runlib import Notebook

nb = Notebook()

# ───────────── 一、类与对象的基本概念 ─────────────
C_CLASS = nb.cell('''
class Student:
    school = "NUS"                          # 类属性：所有实例共享

    def __init__(self, name, scores):       # 构造方法：创建实例时自动调用
        self.name = name                    # 实例属性：每个实例各自一份
        self.scores = scores

    def average(self):                      # 实例方法：第一个参数 self 是调用它的那个实例
        return sum(self.scores) / len(self.scores)

    def __repr__(self):                     # 让 print / 交互环境显示得有意义
        return f"Student({self.name!r}, {self.scores})"

a = Student("Ann", [90, 80])                # 创建实例：自动调用 __init__
b = Student("Bob", [50, 60, 70])
print(a, b)
print(a.average(), b.average())
''')

C_SELF = nb.cell('''
# 方法调用只是语法糖：a.average() 等价于 Student.average(a)
print(Student.average(a) == a.average())

# 实例的属性存放在 __dict__ 字典里；类本身也是对象
print(a.__dict__)
print(type(a), type(Student), isinstance(a, Student))
''')

C_CLSATTR = nb.cell('''
print(a.school, b.school, Student.school)       # 读：实例上没有就去类上找

# 给实例属性赋值，只影响这个实例；它「遮住」了同名的类属性
a.school = "NTU"
print(a.school, b.school, Student.school)
print("school" in a.__dict__, "school" in b.__dict__)
''')

C_CLSMETH = nb.cell('''
class Record:
    def __init__(self, name, scores):
        self.name, self.scores = name, scores

    def __repr__(self):
        return f"Record({self.name!r}, {self.scores})"

    @classmethod
    def from_string(cls, s):                # 类方法：第一个参数是类本身，常用作「替代构造函数」
        name, scores = s.split(":")
        return cls(name, [int(x) for x in scores.split(",")])

    @staticmethod
    def is_pass(score):                     # 静态方法：和类放在一起，但不需要 self 或 cls
        return score >= 50

r = Record.from_string("Bob:50,60,70")      # 用类调用，得到一个新实例
print(r)
print(Record.is_pass(49), r.is_pass(50))    # 静态方法用类或实例调用都行
''')

C_SHARED = nb.cell('''
class Bad:
    items = []                              # 类属性：可变对象，所有实例共用同一个
    def add(self, x): self.items.append(x)

p, q = Bad(), Bad()
p.add(1); q.add(2)
print("共享的类属性：", p.items, q.items, p.items is q.items)

class Good:
    def __init__(self): self.items = []     # 每个实例各自一份
    def add(self, x): self.items.append(x)

p, q = Good(), Good()
p.add(1); q.add(2)
print("实例属性：", p.items, q.items, p.items is q.items)
''')

# ───────────── 二、特殊方法 ─────────────
C_SEQ = nb.cell('''
class Vector:
    def __init__(self, *xs):
        self.xs = list(xs)
    def __repr__(self):         return f"Vector({', '.join(map(str, self.xs))})"
    def __len__(self):          return len(self.xs)         # len(v)
    def __getitem__(self, i):   return self.xs[i]           # v[i]

v = Vector(1, 2, 3)
print(v, len(v), v[1])
print([x for x in v], sum(v), max(v))      # 只定义了 __getitem__，for / sum / max 都能用
''')

C_OPS = nb.cell('''
class Vec:
    def __init__(self, *xs):
        self.xs = list(xs)
    def __repr__(self):         return f"Vec({', '.join(map(str, self.xs))})"
    def __add__(self, other):   return Vec(*[a + b for a, b in zip(self.xs, other.xs)])   # v + w
    def __mul__(self, k):       return Vec(*[a * k for a in self.xs])                      # v * 3
    def __eq__(self, other):    return isinstance(other, Vec) and self.xs == other.xs      # v == w
    def __bool__(self):         return any(self.xs)                                        # bool(v)

v, w = Vec(1, 2, 3), Vec(10, 20, 30)
print(v + w, v * 3)
print(v == Vec(1, 2, 3), v is Vec(1, 2, 3), bool(Vec(0, 0)))
print(Vec.__hash__)                          # 只定义 __eq__：__hash__ 被设成 None
''')

C_HASH = nb.cell('''
try:
    {Vec(1, 2): "a"}                         # 想把实例当字典的键 / 放进集合
except TypeError as e:
    print(type(e).__name__, "| 信息里提到 unhashable：", "unhashable" in str(e))
''')

C_CALL = nb.cell('''
class Scaler:
    def __init__(self, k):
        self.k = k
    def __call__(self, x):                   # 让实例像函数一样被调用
        return x * self.k

triple = Scaler(3)
print(triple(5), triple([1, 2]), callable(triple))
print(triple.__call__(5) == triple(5))       # triple(5) 就是 triple.__call__(5)
''')

C_DATASET = nb.cell('''
class Dataset:                               # 只要实现 __len__ 和 __getitem__
    def __init__(self, n):
        self.xs = list(range(n))
    def __len__(self):
        return len(self.xs)
    def __getitem__(self, i):
        return self.xs[i], self.xs[i] ** 2   # (输入, 标签)

ds = Dataset(7)
print(len(ds), ds[3], ds[6])
''')

C_LOADER = nb.cell('''
class MiniLoader:                            # 迷你 DataLoader：把数据集按 batch 取出
    def __init__(self, dataset, batch_size):
        self.ds, self.bs = dataset, batch_size
    def __iter__(self):                      # 让它成为可迭代对象，内部用生成器
        for i in range(0, len(self.ds), self.bs):
            batch = [self.ds[j] for j in range(i, min(i + self.bs, len(self.ds)))]
            xs, ys = zip(*batch)
            yield list(xs), list(ys)
    def __len__(self):
        return -(-len(self.ds) // self.bs)   # 向上取整

loader = MiniLoader(ds, batch_size=3)        # 直接用上一块的 ds
print("batch 数：", len(loader))
for xs, ys in loader:
    print(xs, ys)
''')

C_WITH = nb.cell('''
class Timer:                                 # 上下文管理器 = __enter__ / __exit__
    def __enter__(self):
        print("进入"); return self
    def __exit__(self, exc_type, exc, tb):
        print("退出，是否出错：", exc_type is not None)
        return False                         # False：不吞掉异常

with Timer():
    print("块内：一切正常")

try:
    with Timer():
        1 / 0                                # 块内出错
except ZeroDivisionError:
    print("异常照常向外传播")
''')

# ───────────── 三、继承、重写与多态 ─────────────
C_INH = nb.cell('''
class Module:                                # 基类：模仿 PyTorch 的 nn.Module 的结构
    def __call__(self, *args):
        return self.forward(*args)           # 调用对象 == 调用 forward
    def forward(self, *args):
        raise NotImplementedError(f"{type(self).__name__} 没有实现 forward")
    def __repr__(self):
        return f"{type(self).__name__}()"

class Linear(Module):                        # 继承：Linear 是一种 Module
    def __init__(self, w, b):
        super().__init__()                   # 调用父类的 __init__
        self.w, self.b = w, b
    def forward(self, x):                    # 子类实现自己的 forward
        return [sum(wi * xi for wi, xi in zip(row, x)) + bi for row, bi in zip(self.w, self.b)]
    def __repr__(self):
        return f"Linear({len(self.w[0])} -> {len(self.w)})"

lin = Linear([[1, 2]], [0])
print(lin)
print(lin([3, -4]), lin.forward([3, -4]))    # lin(x) 等价于 lin.forward(x)
''')

C_POLY = nb.cell('''
class ReLU(Module):
    def forward(self, x):
        return [max(0, v) for v in x]        # 重写 (override)：每个子类有自己的 forward

# 多态 (polymorphism)：同一个调用，不同类型有不同行为
for m in (lin, ReLU()):
    print(type(m).__name__, m([3, -4]))
''')

C_SEQUENTIAL = nb.cell('''
class Sequential(Module):                    # 组合：一个 Module 里面装着一串 Module
    def __init__(self, *layers):
        super().__init__()
        self.layers = layers
    def forward(self, x):
        for layer in self.layers:
            x = layer(x)
        return x
    def __repr__(self):
        return "Sequential(" + ", ".join(map(repr, self.layers)) + ")"

net = Sequential(Linear([[1, -1], [2, 0], [0, 3]], [0, 0, -5]), ReLU(), Linear([[1, 1, 1]], [0]))
print(net)
print(net([2, 1]))            # 第一层 [1, 4, -2] → ReLU [1, 4, 0] → 求和 [5]
''')

C_MRO = nb.cell('''
class Broken(Module): pass                   # 没有实现 forward 的子类
try:
    Broken()(1)
except NotImplementedError as e:
    print("NotImplementedError:", e)

# 类型检查与继承链
print(isinstance(net, Module), issubclass(ReLU, Module))
print([c.__name__ for c in Linear.__mro__])
''')

# ───────────── 四、@property 与 @dataclass ─────────────
C_PROP = nb.cell('''
class Temperature:
    def __init__(self, celsius):
        self.celsius = celsius                  # 这一句也会走下面的 setter，从而被校验
    @property
    def celsius(self):                          # 读：t.celsius
        return self._celsius
    @celsius.setter
    def celsius(self, value):                   # 写：t.celsius = ...
        if value < -273.15:
            raise ValueError("低于绝对零度")
        self._celsius = value
    @property
    def fahrenheit(self):                       # 只读的「计算属性」
        return self._celsius * 9 / 5 + 32

t = Temperature(25)
print(t.celsius)                                # 看起来是读属性，背后在跑 getter
t.celsius = 100                                 # 看起来是赋值，背后在跑 setter
print(t.celsius)
try:
    t.celsius = -300
except ValueError as e:
    print("ValueError:", e)
try:
    Temperature(-500)                           # 构造时也被校验
except ValueError as e:
    print("构造时：", e)
''')

C_PROP2 = nb.cell('''
print(t.celsius, t.fahrenheit)                  # fahrenheit 由 celsius 现算出来
t.celsius = 0
print(t.celsius, t.fahrenheit)                  # celsius 变了，fahrenheit 自动跟着变
try:
    t.fahrenheit = 0
except AttributeError:
    print("AttributeError：只读属性不能赋值")
print(t.__dict__)                               # 实际存放数据的是 _celsius
''')

C_DC = nb.cell('''
from dataclasses import dataclass, field

@dataclass
class Config:
    lr: float = 1e-3
    layers: list = field(default_factory=lambda: [64, 64])   # 可变默认值要用 default_factory
    name: str = "run"

c1, c2 = Config(), Config(lr=0.1, name="fast")
print(c1)                                       # 自动生成的 __repr__
print(c2)
print(c1 == Config(), c1 == c2)                 # 自动生成的 __eq__：逐字段比较
c1.layers.append(8)
print("每个实例各自的列表：", c1.layers, Config().layers)
''')

C_DCBAD = nb.cell('''
try:
    @dataclass
    class Wrong:
        layers: list = []                       # 直接写可变默认值
except ValueError as e:
    print("ValueError:", e)
''')

C_FROZEN = nb.cell('''
@dataclass(frozen=True, order=True)
class Version:                                  # frozen：创建后不能修改；order：自动生成比较
    major: int
    minor: int

print(Version(1, 2) < Version(1, 10))
print(sorted([Version(2, 0), Version(1, 5), Version(1, 2)]))
try:
    Version(1, 0).major = 5
except Exception as e:
    print(type(e).__name__)
print(hash(Version(1, 2)) == hash(Version(1, 2)), len({Version(1, 2), Version(1, 2)}))
''')

C_POST = nb.cell('''
@dataclass
class Point:
    x: float
    y: float
    def __post_init__(self):                    # 自动生成的 __init__ 之后调用
        self.norm = (self.x ** 2 + self.y ** 2) ** 0.5

p = Point(3, 4)
print(p, p.norm)
''')
