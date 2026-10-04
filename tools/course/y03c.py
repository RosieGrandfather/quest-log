from runlib import code

C_CLASS = code('''
class Student:
    school = "NUS"                          # 类属性：所有实例共享

    def __init__(self, name, scores):       # 构造方法：创建实例时自动调用
        self.name = name                    # 实例属性：每个实例各自一份
        self.scores = scores

    def average(self):                      # 实例方法：第一个参数 self 是调用它的那个实例
        return sum(self.scores) / len(self.scores)

    def __repr__(self):                     # 让 print / 交互环境显示得有意义
        return f"Student({self.name!r}, {self.scores})"

    @classmethod
    def from_string(cls, s):                # 类方法：第一个参数是类本身，常用作「替代构造函数」
        name, scores = s.split(":")
        return cls(name, [int(x) for x in scores.split(",")])

    @staticmethod
    def is_pass(score):                     # 静态方法：和类放在一起，但不需要 self 或 cls
        return score >= 50

a = Student("Ann", [90, 80])
b = Student.from_string("Bob:50,60,70")
print(a, b)
print(a.average(), b.average(), Student.is_pass(49))
print(a.school, b.school, Student.school)

# 方法调用只是语法糖：a.average() 等价于 Student.average(a)
print(Student.average(a) == a.average())

# 给实例属性赋值，只影响这个实例；它「遮住」了同名的类属性
a.school = "NTU"
print(a.school, b.school, Student.school)

# 陷阱：可变的类属性会被所有实例共享
class Bad:
    items = []                              # 类属性
    def add(self, x): self.items.append(x)
p, q = Bad(), Bad()
p.add(1); q.add(2)
print("共享的类属性：", p.items, q.items, p.items is q.items)

class Good:
    def __init__(self): self.items = []     # 每个实例各自一份
    def add(self, x): self.items.append(x)
p, q = Good(), Good()
p.add(1); q.add(2)
print("实例属性：", p.items, q.items)

# 一切都是对象：类本身也是对象
print(type(a), type(Student), isinstance(a, Student), a.__dict__)
''')

C_DUNDER = code('''
class Vector:
    def __init__(self, *xs):
        self.xs = list(xs)
    def __repr__(self):         return f"Vector({', '.join(map(str, self.xs))})"
    def __len__(self):          return len(self.xs)                       # len(v)
    def __getitem__(self, i):   return self.xs[i]                         # v[i]，同时让 for 循环可用
    def __add__(self, other):   return Vector(*[a + b for a, b in zip(self.xs, other.xs)])   # v + w
    def __mul__(self, k):       return Vector(*[a * k for a in self.xs])                      # v * 3
    def __eq__(self, other):    return isinstance(other, Vector) and self.xs == other.xs      # v == w
    def __bool__(self):         return any(self.xs)                       # bool(v)
    def __call__(self, i):      return self.xs[i] * 10                    # v(1) 像函数一样被调用

v, w = Vector(1, 2, 3), Vector(10, 20, 30)
print(v + w, v * 3, len(v), v[1], v == Vector(1, 2, 3), bool(Vector(0, 0)))
print([x for x in v], sum(v), max(v), v(1))      # 只定义了 __getitem__，for / sum / max 都能用

# 实战：写一个「数据集」。只要实现 __len__ 和 __getitem__，就能被下面这个迷你 DataLoader 使用
class Dataset:
    def __init__(self, n):
        self.xs = list(range(n))
    def __len__(self):
        return len(self.xs)
    def __getitem__(self, i):
        return self.xs[i], self.xs[i] ** 2          # (输入, 标签)

class MiniLoader:
    def __init__(self, dataset, batch_size):
        self.ds, self.bs = dataset, batch_size
    def __iter__(self):                              # 让它成为可迭代对象，内部用生成器
        for i in range(0, len(self.ds), self.bs):
            batch = [self.ds[j] for j in range(i, min(i + self.bs, len(self.ds)))]
            xs, ys = zip(*batch)
            yield list(xs), list(ys)
    def __len__(self):
        return -(-len(self.ds) // self.bs)           # 向上取整

loader = MiniLoader(Dataset(7), batch_size=3)
print("batch 数：", len(loader))
for xs, ys in loader:
    print(xs, ys)

# 用 with 语句：上下文管理器 = __enter__ / __exit__
class Timer:
    def __enter__(self):
        print("进入"); return self
    def __exit__(self, exc_type, exc, tb):
        print("退出，是否出错：", exc_type is not None)
        return False                                  # False：不吞掉异常
with Timer():
    pass
''')

C_INH = code('''
class Module:                                    # 基类：模仿 PyTorch 的 nn.Module 的结构
    def __call__(self, *args):
        return self.forward(*args)               # 调用对象 == 调用 forward
    def forward(self, *args):
        raise NotImplementedError(f"{type(self).__name__} 没有实现 forward")
    def __repr__(self):
        return f"{type(self).__name__}()"

class Linear(Module):                            # 继承：Linear 是一种 Module
    def __init__(self, w, b):
        super().__init__()                       # 调用父类的 __init__
        self.w, self.b = w, b
    def forward(self, x):
        return [sum(wi * xi for wi, xi in zip(row, x)) + bi for row, bi in zip(self.w, self.b)]
    def __repr__(self):
        return f"Linear({len(self.w[0])} -> {len(self.w)})"

class ReLU(Module):
    def forward(self, x):
        return [max(0, v) for v in x]            # 重写 (override)：每个子类有自己的 forward

class Sequential(Module):                        # 组合：一个 Module 里面装着一串 Module
    def __init__(self, *layers):
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

# 多态 (polymorphism)：同一个调用，不同类型有不同行为
for m in (Linear([[1, 2]], [0]), ReLU()):
    print(type(m).__name__, m([3, -4]))

# 没有实现 forward 的子类
class Broken(Module): pass
try:
    Broken()(1)
except NotImplementedError as e:
    print("NotImplementedError:", e)

# 类型检查与继承链
print(isinstance(net, Module), issubclass(ReLU, Module), [c.__name__ for c in Linear.__mro__])
''')

C_PROP = code('''
from dataclasses import dataclass, field

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
print(t.celsius, t.fahrenheit)
t.celsius = 100
print(t.fahrenheit)
try:
    t.celsius = -300
except ValueError as e:
    print("ValueError:", e)
try:
    t.fahrenheit = 0
except AttributeError as e:
    print("AttributeError：只读属性不能赋值")

# dataclass：自动生成 __init__、__repr__、__eq__
@dataclass
class Config:
    lr: float = 1e-3
    layers: list = field(default_factory=lambda: [64, 64])   # 可变默认值要用 default_factory
    name: str = "run"

c1, c2 = Config(), Config(lr=0.1, name="fast")
print(c1)
print(c2, c1 == Config(), c1 == c2)
c1.layers.append(8)
print("每个实例各自的列表：", c1.layers, Config().layers)

@dataclass(frozen=True, order=True)
class Version:                                  # frozen：创建后不能修改；order：自动生成比较
    major: int
    minor: int

print(Version(1, 2) < Version(1, 10), sorted([Version(2, 0), Version(1, 5), Version(1, 2)]))
try:
    Version(1, 0).major = 5
except Exception as e:
    print(type(e).__name__)

@dataclass
class Point:
    x: float
    y: float
    def __post_init__(self):                    # 自动生成的 __init__ 之后调用
        self.norm = (self.x ** 2 + self.y ** 2) ** 0.5
print(Point(3, 4).norm)
''')
