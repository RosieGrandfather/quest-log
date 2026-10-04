"""py-0 第 3 节：类与对象"""
from unitlib import *
from y03c import C_CLASS, C_DUNDER, C_INH, C_PROP

unit = {
 "id": "u03",
 "title": "类与对象",
 "en": "Classes & Objects",
 "minutes": 100,
 "objectives": [
  "会定义 **类 (class)**，分清 **实例属性 / 类属性**、**实例方法 / 类方法 / 静态方法**，理解 `self` 与 `__init__`，避开「可变类属性被共享」的陷阱",
  "会用 **特殊方法 (special / dunder methods)**（`__repr__`、`__len__`、`__getitem__`、`__add__`、`__eq__`、`__call__`、`__enter__` / `__exit__`）让自己的类像内置类型一样工作",
  "理解 **继承 (inheritance)**、`super()`、**方法重写 (override)**、**多态 (polymorphism)** 与 **组合 (composition)**，能读懂 `nn.Module` 式的类结构",
  "会用 **`@property`** 做校验与计算属性，会用 **`@dataclass`** 写数据容器",
 ],
 "blocks": [
  T(r"""
### 先说这一节要干什么

面向对象编程 (OOP) 是几乎所有大型 Python 代码库的组织方式。对你来说它尤其重要：**PyTorch 里的每个模型都是一个类**（继承 `nn.Module`），每个数据集也是一个类（继承 `Dataset`）。读不懂类，就读不懂 ML 代码；而读得懂，你会发现它们的结构就是这一节的几个简单套路。

**学完它你就能看懂这几件事：**

- `class Net(nn.Module): def __init__(self): super().__init__() ... def forward(self, x): ...`：每个词都是什么意思，为什么 `model(x)` 会调用 `forward`；
- `class MyDataset(Dataset): def __len__ ...; def __getitem__ ...`：为什么只要写这两个方法，就能被 `DataLoader` 使用；
- `@dataclass class Config`：实验配置的标准写法（Hugging Face、很多研究代码里都有）；
- `model.parameters()`、`optimizer.step()`、`tensor.shape`：这些点号后面的东西是方法还是属性（`@property`）。

**本节安排（约 100 分钟）**：类的基本概念（20 分钟，含视频一）→ 特殊方法（25 分钟，含视频二）→ 继承与多态（20 分钟）→ `@property` 与 `@dataclass`（20 分钟，含视频三）→ 总结与「想一想」（15 分钟）。

### 类与对象的基本概念

> **标准定义 · 类 (class) 与实例 (instance)**
>
> **类**是创建对象的**模板**，定义了一类对象共有的**属性 (attribute)**（数据）与**方法 (method)**（函数）。由类创建出来的具体对象叫做**实例**。`__init__` 是**构造方法**，创建实例时自动调用，用来初始化**实例属性**。方法的第一个参数 `self` 表示**调用它的那个实例**。直接写在类体里的变量是**类属性**，由所有实例**共享**；写在 `self.xxx = ...` 的是**实例属性**，每个实例各自一份。
>
> *English: A class is a template for objects; an instance is a concrete object created from it. __init__ initialises instance attributes; self refers to the instance. Class attributes are shared by all instances; instance attributes belong to each instance.*

**白话版：「类是图纸，实例是房子」。** 图纸上写了「房子有几个房间（属性）、能开关门（方法）」；照图纸盖出来的每一栋房子是一个实例，每栋有自己的颜色、地址（实例属性）；「这个小区的名字」是大家共用的（类属性）。

""" + C_CLASS + r"""

要点：**一**，`a.average()` 只是语法糖，等价于 `Student.average(a)`：`self` 就是点号前面的那个对象，这个理解很重要。**二**，三种方法：**实例方法**（第一个参数 `self`）、**类方法** `@classmethod`（第一个参数 `cls`，常用作**替代构造函数**，比如 `from_string`，PyTorch 里的 `torch.from_numpy`、Hugging Face 的 `from_pretrained` 都是这种风格）、**静态方法** `@staticmethod`（不需要 `self` 或 `cls`，只是放在类里面的普通函数）。**三**，给实例赋值只会在**这个实例**上创建属性、**遮住**同名的类属性，不会改动类属性。**四，陷阱：可变的类属性被所有实例共享**：`Bad.items = []` 让 `p` 和 `q` 共用同一个列表，这和上一节「可变默认参数」是同一个道理；可变的数据应该在 `__init__` 里用 `self.items = []` 创建。**五**，类本身也是对象（`type(Student)` 是 `type`），实例的属性存放在 `__dict__` 字典里。
"""),
  V("ZDa-Z5JzLYM", "视频一：Python OOP Tutorial 1: Classes and Instances（Corey Schafer）", 15),
  T(r"""
### 特殊方法：让你的类像内置类型一样工作

> **标准定义 · 特殊方法 (special methods / dunder methods)**
>
> 名字以**双下划线**开头和结尾的方法（**d**ouble **under**score，所以叫 **dunder**），如 `__init__`、`__repr__`。你一般**不直接调用**它们，而是由 Python 的**语法或内置函数在背后调用**：`len(x)` 调 `x.__len__()`，`x[i]` 调 `x.__getitem__(i)`，`x + y` 调 `x.__add__(y)`，`x == y` 调 `x.__eq__(y)`，`x(...)` 调 `x.__call__(...)`，`with x:` 调 `__enter__` 与 `__exit__`。这套约定称为 Python 的**数据模型 (data model)**。
>
> *English: Dunder (double-underscore) methods are hooks that Python calls implicitly: len(x) calls __len__, x[i] calls __getitem__, x + y calls __add__, x(...) calls __call__. Implementing them lets your class behave like a built-in type.*

**白话版：「对接口」。** Python 的内置函数和语法提前约定好了暗号：「谁实现了 `__len__`，我就能数它有多长」。你的类只要把相应的暗号方法写出来，就能被 `len`、`for`、`+`、`with` 这些语法直接使用。

""" + C_DUNDER + r"""

重点看两件事：**第一**，`Vector` 只定义了 `__getitem__`，`for`、`sum`、`max` 就都能用了：Python 在没有 `__iter__` 时，会退而用 `__getitem__` 从 0 开始逐个取，直到 `IndexError`。**第二**，这就是 PyTorch **`Dataset` / `DataLoader`** 的原理：数据集只需要告诉别人「**有多少条**（`__len__`）」和「**第 $i$ 条是什么**（`__getitem__`）」，DataLoader 按批取出、打包；真实的 `DataLoader` 还加上了打乱 (shuffle)、多进程加载、拼接 batch，但接口就是这两个方法。

**`__call__`** 让对象像函数一样被调用：`model(x)` 之所以能写，是因为 `nn.Module` 实现了 `__call__`，它在里面调用你写的 `forward`（下一小节演示）。**`__enter__` / `__exit__`** 是 `with` 语句的底层：不管 `with` 块里是否出错，`__exit__` 都一定会被调用，所以文件、锁、数据库连接、`torch.no_grad()` 都用它来保证「用完一定收尾」。**`__repr__` 与 `__str__`**：前者面向开发者（调试时看到的，应当尽量清晰、能还原对象），后者面向用户（`print` 用的）；只写一个的话，写 `__repr__`。

**`==` 与 `is` 的区别：** 默认的 `==` 比较的是**是不是同一个对象**，你需要定义 `__eq__` 才能让「内容相同」的两个对象相等。注意：**定义了 `__eq__` 而不定义 `__hash__`，这个类的实例就不再可哈希**（不能放进集合、不能做字典的键），数据结构第 4 节讲过哈希表对此的要求。
"""),
  V("3ohzBxoFHAY", "视频二：Python OOP Tutorial 5: Special (Magic/Dunder) Methods（Corey Schafer）", 14),
  T(r"""
### 继承、重写与多态

> **标准定义 · 继承 (inheritance) 与多态 (polymorphism)**
>
> **继承**：子类 (subclass) 自动拥有父类 (superclass) 的属性与方法，可以**新增**，也可以**重写 (override)** 同名方法来改变行为；`super()` 用来调用父类的方法（通常是 `super().__init__(...)`）。**多态**：不同类型的对象对**同一个调用**（比如 `.forward(x)`）给出**各自的行为**，调用者不需要关心对象的具体类型。**组合 (composition)** 是另一种复用方式：一个对象**包含**其他对象作为自己的属性（「有一个」，has-a），而继承是「是一种」（is-a）。
>
> *English: A subclass inherits attributes and methods from its superclass and can override them; super() calls the parent's version. Polymorphism lets different types respond differently to the same call. Composition means an object contains other objects (has-a), in contrast to inheritance (is-a).*

**白话版：「继承是『是一种』，组合是『有一个』」。** 狗**是一种**动物（继承）；汽车**有一个**发动机（组合）。多态像遥控器上的「播放」键：对电视、音箱、投影仪按下去，各自播放各自的东西，你不需要知道里面是什么。

下面用一个**迷你版 `nn.Module`** 把这些串起来，它的结构和 PyTorch 的几乎一样：

""" + C_INH + r"""

逐点对应 PyTorch：**一**，`Module.__call__` 调用 `self.forward`，所以 `net(x)` 等价于 `net.forward(x)`；真正的 `nn.Module.__call__` 在调用 `forward` 前后还做了钩子 (hooks) 等处理，这就是**为什么要写 `model(x)` 而不是 `model.forward(x)`**。**二**，`Linear`、`ReLU` 是 `Module` 的**子类**，各自**重写**了 `forward`；`Linear.__init__` 里的 `super().__init__()` 在 PyTorch 里是**必须写**的（它初始化了参数登记等内部结构，忘了写会得到一个令人困惑的报错）。**三**，`Sequential` 是**组合**：它的属性里装着一串 `Module`，再依次调用，这也是为什么大模型是「模块里套模块」的层层结构。**四**，**多态**：循环里 `m([3, -4])` 对 `Linear` 和 `ReLU` 的行为完全不同，调用者不关心。**五**，`Broken` 没有实现 `forward`，调用基类里的版本会抛出 `NotImplementedError`：这是定义「抽象接口」的常用写法。最后一行里的 `__mro__`（方法解析顺序 method resolution order）列出了继承链：Python 沿这个顺序查找方法。

**继承还是组合？** 经验法则：**优先用组合，只有真的「是一种」才用继承**。深层的继承树让人难以理解「这个方法到底从哪来的」；PyTorch 里 `nn.Module` 一层继承（你的模型继承 `nn.Module`）加上大量组合（模型里装着 `Linear`、`Conv2d`……），是一个比较健康的例子。

### `@property` 与 `@dataclass`

> **标准定义 · 属性装饰器 (`@property`)**
>
> `@property` 把一个**方法**变成**像属性一样访问**的东西（不用写括号）。可以再配上 `@x.setter` 定义赋值时的行为。用途：**在赋值时做校验**、**计算属性**（由其他属性算出来，如 `fahrenheit`）、**只读属性**，且调用者的写法不用变，可以先用普通属性写，需要校验时再改成 `property`，不会破坏已有代码。
>
> *English: @property lets a method be accessed like an attribute; with a setter it can validate assignments. It provides computed and read-only attributes without changing how callers write the code.*

> **标准定义 · 数据类 (`@dataclass`)**
>
> `@dataclass` 装饰器根据类体里的**带类型注解的字段**，**自动生成** `__init__`、`__repr__`、`__eq__` 等方法。选项：`frozen=True` 实例不可修改（同时可哈希）；`order=True` 自动生成比较运算符；字段的可变默认值要用 `field(default_factory=...)`；`__post_init__` 在自动生成的 `__init__` 之后调用，用于计算派生字段。
>
> *English: @dataclass generates __init__, __repr__ and __eq__ from annotated fields. frozen=True makes instances immutable and hashable, order=True adds comparisons, field(default_factory=...) is used for mutable defaults, and __post_init__ runs after __init__.*

**白话版：** `@property` 是「**对外看起来是一个变量，对内其实是一段代码**」，像自动门：你走过去（读写属性），背后的传感器（校验逻辑）自动工作。`@dataclass` 是「**只存数据的类**」的模板：你只写有哪些字段，样板代码由它代写。

""" + C_PROP + r"""

注意**两个细节**：`Temperature.__init__` 里的 `self.celsius = celsius` 会经过 `setter`，所以**构造时也被校验**；数据存在 `_celsius`（单下划线是「内部使用，请勿直接访问」的约定，Python 没有真正的私有）。`dataclass` 里可变的默认值**必须用 `default_factory`**，否则每个实例共享同一个列表（又是可变默认值的陷阱）：Python 会直接拒绝 `layers: list = []` 这种写法，并报错提醒你。`Config()` 生成的 `__repr__` 清楚地显示每个字段，`==` 逐字段比较，这在实验配置里非常方便；`frozen=True` 的对象创建后不可修改（尝试修改会抛 `FrozenInstanceError`），适合做配置、做字典的键。

### 这一节你要带走的三句话

1. **类 = 模板，实例 = 具体的对象**；`self` 就是点号前面的那个对象，实例属性在 `__init__` 里创建，**可变的数据不要放在类属性里**。
2. **特殊方法是 Python 的「暗号」**：实现 `__len__` + `__getitem__` 就是一个 `Dataset`，实现 `__call__` 就能像函数一样调用，实现 `__enter__` / `__exit__` 就能用 `with`。
3. **继承 = 「是一种」，重写让子类有自己的行为（多态），组合 = 「有一个」**；`nn.Module` 就是「继承 + `__call__` 调用 `forward` + 模块里套模块」；`@property` 做校验与计算属性，`@dataclass` 省掉样板代码。
"""),
  V("vBH6GRJ1REM", "视频三：Python dataclasses will save you HOURS, also featuring attrs（mCoding）", 9),
  THINK("下面这段代码有什么问题？会输出什么？\n\n`class Bag: items = []` / `def add(self, x): self.items.append(x)` / `a, b = Bag(), Bag(); a.add(1); print(b.items)`。", r"""
`items` 写在类体里，是**类属性**，被所有实例共享：`a.add(1)` 实际修改的是 `Bag.items` 这个**同一个**列表，所以 `b.items` 也是 `[1]`。问题和「可变默认参数」一样：**可变对象被共享了**。修改：在 `__init__` 里写 `self.items = []`，让每个实例创建自己的列表。

判断规则：类属性适合放**所有实例共享的常量**或计数器（如 `school = "NUS"`）；每个实例自己的、尤其是可变的数据，一定放在 `__init__` 里。
"""),
  THINK("你要写一个 `Dataset`，数据存在一个很大的磁盘文件夹里（几十万张图片）。`__init__`、`__len__`、`__getitem__` 里分别应该做什么？为什么不把所有图片都在 `__init__` 里读进内存？", r"""
- `__init__`：只做**轻量**的事，比如记录文件夹路径、列出所有文件名（一个字符串列表）、保存预处理函数。
- `__len__`：返回文件个数（`len(self.files)`）。
- `__getitem__(i)`：**这时才**读取第 $i$ 张图片、做预处理（缩放、归一化等），返回 `(图像, 标签)`。

不在 `__init__` 里全部读入，是因为几十万张图片会占用几十到几百 GB 内存，装不下。放在 `__getitem__` 里**按需读取**，每次只在内存里放一个 batch，这又是**惰性求值**的思想，和上一节的生成器一脉相承。`DataLoader` 还可以开多个**工作进程 (workers)** 并行调用 `__getitem__`，让数据读取和 GPU 计算重叠，这是为什么用 `Dataset` 接口、而不是自己写一个大列表。
"""),
  THINK("`@dataclass` 生成的 `__eq__` 会逐字段比较。如果一个类定义了 `__eq__`，却没有定义 `__hash__`，会有什么后果？怎样让一个 dataclass 的实例能放进集合或当字典的键？", r"""
Python 的规则：**只定义 `__eq__`、不定义 `__hash__` 的类，`__hash__` 会被设为 `None`，实例不可哈希**，放进 `set` 或当 `dict` 的键会报 `TypeError: unhashable type`。原因是：「相等的对象必须有相同的哈希值」，一旦自定义了相等的含义，默认的基于身份的哈希就不再满足这条规则。

对 `dataclass`：**`@dataclass(frozen=True)`**（或 `unsafe_hash=True`）会根据字段生成 `__hash__`。用 `frozen=True` 最安全：对象不可修改，哈希值就不会变（可变对象的哈希值如果变了，在集合 / 字典里就找不到它了，数据结构第 4 节讲过原因）。
"""),
  KW(("类 / 实例","class / instance","模板 / 由模板创建的具体对象"),
     ("属性 / 方法","attribute / method","对象的数据 / 对象的函数"),
     ("`self`","self","方法的第一个参数，代表调用它的实例"),
     ("构造方法","`__init__`","创建实例时自动调用，初始化实例属性"),
     ("类属性 / 实例属性","class attribute / instance attribute","所有实例共享 / 每个实例各自一份"),
     ("类方法 / 静态方法","classmethod / staticmethod","第一个参数是 `cls` / 不需要 `self` 或 `cls`"),
     ("特殊方法","special (dunder) method","`__len__`、`__getitem__`、`__call__` 等，由语法或内置函数在背后调用"),
     ("`__repr__` / `__str__`","repr / str","给开发者看的表示 / 给用户看的表示"),
     ("继承 / 重写","inheritance / override","子类获得父类的功能 / 子类改写同名方法"),
     ("多态","polymorphism","同一个调用，不同类型有不同行为"),
     ("组合","composition","对象包含其他对象作为属性（has-a）"),
     ("方法解析顺序","MRO (method resolution order)","Python 查找方法所沿着的继承链顺序"),
     ("`@property`","property","让方法像属性一样访问，可加校验"),
     ("`@dataclass`","dataclass","根据带类型注解的字段自动生成 `__init__`、`__repr__`、`__eq__`"),
  ),
 ],
 "references": [
  {"title": "Think Python 3e（Downey）— 第 14–17 章：Classes and Functions / Classes and Methods / Classes and Objects / Inheritance", "url": "https://allendowney.github.io/ThinkPython/chap16.html", "note": "本节大纲依据之一，从零开始构建类、方法与继承（此为第 16 章，前后章节相连），CC BY-NC-SA 4.0"},
  {"title": "Python OOP Tutorial 4: Inheritance - Creating Subclasses（Corey Schafer，约 20 分钟，选看）", "url": "https://www.youtube.com/watch?v=RSl87lqOXDE", "note": "继承、`super()`、`isinstance` 的详细演示"},
  {"title": "Python OOP Tutorial 6: Property Decorators（Corey Schafer，约 10 分钟，选看）", "url": "https://www.youtube.com/watch?v=jCzT9XFZ5bw", "note": "getter、setter、deleter 的完整讲解"},
  {"title": "Python 文档：Data model（特殊方法一览）", "url": "https://docs.python.org/3/reference/datamodel.html", "note": "所有特殊方法的权威说明，需要时查阅"},
  {"title": "PyTorch 教程：Datasets & DataLoaders", "url": "https://pytorch.org/tutorials/beginner/basics/data_tutorial.html", "note": "自定义 Dataset（`__len__`、`__getitem__`）的官方示例，学完这一节后可以直接读懂"},
 ],
 "quiz": {"questions": [
  Q("`a.average()` 与 `Student.average(a)` 的关系是？",
    ["完全无关", "等价：方法调用的 `self` 就是点号前面的对象", "前者调用类方法，后者调用静态方法", "后者会报错"], 1,
    "`a.average()` 是语法糖，Python 自动把 `a` 作为第一个参数 `self` 传入。"),
  Q("类体里直接写 `items = []`（类属性），而不是在 `__init__` 里写 `self.items = []`，会有什么问题？",
    ["没有任何问题", "所有实例共享同一个列表，一个实例的修改会影响其他实例", "无法在方法里访问", "会让类无法被实例化"], 1,
    "类属性被所有实例共享，可变对象的修改对所有实例可见。每个实例独有的可变数据应在 `__init__` 里创建。"),
  Q("`@classmethod` 的第一个参数 `cls` 代表什么？常见用途是？",
    ["调用它的实例；做校验", "类本身；作为替代构造函数，如 `from_string`", "父类；调用父类方法", "模块；导入"], 1,
    "类方法的第一个参数是类本身，所以 `cls(...)` 能创建（子类的）实例，常用作替代构造函数。"),
  Q("为了让一个对象支持 `len(obj)` 和 `obj[i]`，需要实现哪两个特殊方法？",
    ["`__init__` 与 `__repr__`", "`__str__` 与 `__eq__`", "`__call__` 与 `__enter__`", "`__len__` 与 `__getitem__`"], 3,
    "这两个方法也正是 PyTorch 的 `Dataset` 所需要的接口。"),
  Q("`model(x)` 能运行，是因为 `nn.Module` 实现了哪个特殊方法？它再调用什么？",
    ["`__call__`，它调用你定义的 `forward`", "`__init__`，它调用 `backward`", "`__getitem__`，它调用 `fit`", "`__enter__`，它调用 `train`"], 0,
    "`__call__` 让对象可像函数一样调用；在里面会调用 `forward`，并处理钩子等额外逻辑，所以应该写 `model(x)` 而不是 `model.forward(x)`。"),
  Q("`with open(path) as f:` 能保证文件一定被关闭，即使块内出错，依赖的是？",
    ["`__len__` 与 `__getitem__`", "`__add__`", "上下文管理器协议：`__enter__` 与 `__exit__`", "`__hash__`"], 2,
    "不管 `with` 块是否出现异常，`__exit__` 都一定会被调用，从而完成关闭等收尾工作。"),
  Q("在子类的 `__init__` 里写 `super().__init__()` 的作用是？",
    ["删除父类", "调用父类的构造方法，让父类部分也得到初始化", "让子类变成静态方法", "创建新的实例"], 1,
    "不调用时，父类 `__init__` 里做的初始化不会发生。在 PyTorch 里忘了它，`nn.Module` 内部的参数登记会缺失。"),
  Q("「一个模型里包含若干个层作为属性」属于？而「`Linear` 是一种 `Module`」属于？",
    ["前者继承，后者组合", "两者都是继承", "前者组合（has-a），后者继承（is-a）", "两者都是多态"], 2,
    "「有一个」是组合；「是一种」是继承。一般优先用组合，真的是「是一种」时才用继承。"),
  Q("`@property` 的典型用途**不包括**？",
    ["在赋值时校验数值范围", "定义由其他属性计算出来的只读属性", "让调用者以属性的写法访问，同时背后运行代码", "让类的所有实例共享同一个可变列表"], 3,
    "共享可变数据是类属性（且通常是陷阱）。`property` 的价值是校验、计算属性和只读属性。"),
  Q("`@dataclass` 里想给字段设置「可变」的默认值，例如一个空列表，正确写法是？",
    ["`layers: list = []`", "`layers: list = field(default_factory=list)`", "`layers: list = None`，什么都不用做", "dataclass 里不能放列表"], 1,
    "直接写 `[]` 会被 `dataclass` 拒绝（否则所有实例共享同一个列表）；`default_factory` 为每个实例创建新列表。"),
 ]},
}

TARGET = [2, 0, 1, 3, 0, 2, 3, 1, 0, 2]
for q, t in zip(unit["quiz"]["questions"], TARGET):
    q["options"][q["answer"]], q["options"][t] = q["options"][t], q["options"][q["answer"]]
    q["answer"] = t

if __name__ == '__main__':
    dump(unit, "py-0", "u03-classes-objects.json")
