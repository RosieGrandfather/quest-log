"""py-0 第 1 节：函数、作用域、闭包、装饰器与递归"""
from unitlib import *
from y01c import *

unit = {
 "id": "u01",
 "title": "函数、作用域与递归",
 "en": "Functions, Scope & Recursion",
 "minutes": 100,
 "objectives": [
  "会用 Python 函数的全部参数形式：**默认参数 (default)**、**关键字参数 (keyword)**、`*args` / `**kwargs`、**仅关键字 (keyword-only)** 参数，以及调用时的 `*` / `**` 拆包",
  "说清 Python 的**传参机制 (pass by object reference)**，避开 **可变默认参数** 与 `[[0]*3]*3` 这两个经典陷阱",
  "理解 **作用域 (scope)** 的 **LEGB** 查找规则、`global` / `nonlocal`，以及 **闭包 (closure)** 与其「晚绑定」陷阱",
  "理解函数是 **一等公民 (first-class object)**，会写 **lambda**、`sorted(key=)`，会写简单与带参数的 **装饰器 (decorator)**",
  "会写 **递归 (recursion)**：基础情形、递归情形、调用栈、`RecursionError`，以及用 `lru_cache` 做记忆化",
 ],
 "blocks": [
  T(r"""
### 先说这一节要干什么

函数是 Python 里最基本的复用单位，后面所有内容（类、迭代器、测试、模块）都建立在它上面。这一节的重点不是「会定义函数」（你已经会），而是把那些**读别人的 ML 代码时一定会遇到、而你可能没有系统学过的细节**补齐：`*args` / `**kwargs`、闭包、装饰器，以及 Python 的参数传递到底是怎么回事。

**学完它你就能看懂这几件事：**

- PyTorch / Hugging Face 代码里随处可见的 `def forward(self, x, *args, **kwargs)`、`@torch.no_grad()`、`@torch.compile`、`@lru_cache`、`@dataclass`：这些都是**装饰器**；
- `model(x, mask=m)` 为什么能写得这么灵活：**关键字参数与默认参数**；
- 「我传进去的列表怎么被改了」「为什么这个函数每次调用结果越来越多」：**可变对象与默认参数**；
- 数据结构与算法课里的树、图、分治、动态规划：**递归**。

**本节安排（约 100 分钟）**：参数与传参（20 分钟）→ 作用域与闭包（15 分钟，含视频一）→ 一等函数与装饰器（20 分钟，含视频二）→ 递归（20 分钟，含视频三）→ 总结与「想一想」（15 分钟）。

**怎么学这一节：** 每个知识点都是「一小段代码 → 紧跟着读它的输出」。每个代码块都可以点「▶ 运行」，也可以改一改再跑；同一节里，前面的块定义的变量和函数，后面的块可以直接用，所以请**按顺序**往下跑。

### 参数的所有形式

> **标准定义 · 参数 (parameter) 与实参 (argument)**
>
> **形参 (parameter)** 是函数**定义**中写的名字；**实参 (argument)** 是**调用**时传入的值。Python 的形参有五类：**位置或关键字参数**（最常见）、**默认参数** `name=value`、可变位置参数 `*args`（收集多余的位置实参为 **元组 tuple**）、可变关键字参数 `**kwargs`（收集多余的关键字实参为 **字典 dict**），以及 **仅位置 (positional-only)**（写在 `/` 之前）与 **仅关键字 (keyword-only)**（写在 `*` 之后）参数。
>
> *English: A parameter is a name in a function definition; an argument is the value passed in a call. Python supports positional-or-keyword, default, *args, **kwargs, positional-only (before /) and keyword-only (after *) parameters.*

**白话版：「点菜」。** 位置参数像「按菜单顺序点：第一道、第二道」；关键字参数像「指名道姓：汤要不辣的」；默认参数是「不说就按默认」；`*args` 是「还有什么其他的，都装一个袋子里」；`**kwargs` 是「还有什么其他的『指名要求』，都装一个本子里」。

**问题一：同一个函数里，哪些参数只能按位置传、哪些可以用关键字、哪些必须用关键字？** 下面的 `describe` 把三种都用上了：

""" + C_POS + r"""

**读输出：** 三行分别是 `Yijia, 28, Singapore`、`Yijia, 28, Osaka`、`Yijia, 28, Tokyo (verbose)`。第一次调用只传了 `name` 与 `age`，`city` 用默认值 `Singapore`；第二次把 `"Osaka"` 按位置传给 `city`；第三次用 `city="Tokyo"` 指名，并用 `verbose=True` 打开了仅关键字参数，结果多了 `(verbose)`。`/` 与 `*` 是 Python 3.8+ 的写法，库的作者用它们来**约束调用方式**：仅关键字参数让调用处的意思更清楚（`verbose=True` 比一个孤零零的 `True` 好读得多）。

**问题二：参数个数不固定时怎么办？** 用 `*` 与 `**` 在**定义**里「打包」：

""" + C_VAR + r"""

**读输出：** 第一行 `(6, (1, 2, 3), {})`：三个数被收进元组 `nums = (1, 2, 3)`，没有关键字实参所以 `options` 是空字典，`sum` 为 6，乘以默认的 `scale` 1 仍是 6。第二行 `(60, (1, 2, 3), {'scale': 10, 'debug': True})`：多出来的两个关键字实参被收进字典，`scale=10` 让结果变成 60，`debug=True` 没有被用到但也被收下了。

**问题三：已经有一个元组 / 字典，怎么把它「拆开」传进去？反过来，函数怎么返回多个值？** 调用时的 `*` 与 `**` 是「拆包」：

""" + C_UNPACK + r"""

**读输出：** `total(*args, **kw)` 等价于 `total(1, 2, 3, scale=2)`，所以第一行是 `(12, (1, 2, 3), {'scale': 2})`，`6 * 2 = 12`。可见 `*` 与 `**` 在**调用**时是「拆包」，在**定义**时是「打包」，是互逆的两件事。第二行 `1 9 <class 'tuple'>`：`min_max` 看起来「返回两个值」，其实返回的是一个**元组** `(1, 9)`，调用方再把它**解包**给 `lo` 与 `hi`。

**问题四：调用方式写错时 Python 会怎么说？**

""" + C_BADCALL + r"""

**读输出：** 第一个调用给了 4 个位置实参，而 `describe` 最多接收 3 个位置实参（`name`、`age`、`city`；`verbose` 是仅关键字参数），所以报 `describe() takes from 2 to 3 positional arguments but 4 were given`。第二个调用用关键字传了 `name`、`age`，但它们是仅位置参数，所以报 `got some positional-only arguments passed as keyword arguments: 'name, age'`。（具体措辞随 Python 版本稍有不同，要看的是它能告诉你**哪里不合规则**。）

### Python 怎么传参：传的是「对象的引用」

> **标准定义 · 传对象引用 (pass by object reference / pass by assignment)**
>
> Python 里变量是**名字 (name)**，它**指向 (refer to)** 内存里的一个**对象 (object)**，而不是存放数据的盒子。调用函数时，形参与实参**指向同一个对象**（等价于做了一次赋值）。**可变对象 (mutable)**（列表、字典、集合）能被原地修改，修改对所有指向它的名字可见；**不可变对象 (immutable)**（整数、字符串、元组）不能被修改，「改」只是让名字指向一个新对象。**重新赋值（`name = ...`）只改变这个名字的指向**，不影响别的名字。
>
> *English: Python names refer to objects. Passing an argument binds the parameter to the same object. Mutating a mutable object is visible through every name; rebinding a name only changes that name.*

**白话版：「名字是便利贴，对象是东西」。** 两个人（实参和形参）各拿一张便利贴，贴在同一件东西上。你把东西本身改了（`append`），另一个人看到的也变了；你把自己的便利贴撕下来贴到另一件东西上（`lst = [0]`），对方的便利贴还贴在原处。

**问题：函数里「改」了参数，外面的变量会变吗？** 看三种不同的「改」：

""" + C_MUT + r"""

**读输出：** `([0], 11) [1, 2, 99] 10`。函数返回的是 `([0], 11)`：局部名字 `lst` 被重新指向 `[0]`，局部 `num` 变成 11。但外面的 `a` 是 `[1, 2, 99]`：`append(99)` 改的是**对象本身**，所以外面看得到；而 `lst = [0]` 只让局部名字指向了新列表，不影响外面的 `a`。外面的 `n` 仍是 10：整数不可变，`num += 1` 只是让局部 `num` 指向新整数 11。

**陷阱一：可变默认参数。** **默认值是在 `def` 语句执行的那一刻只创建一次的**，不是每次调用时创建。先看错误写法：

""" + C_DEFBAD + r"""

**读输出：** 三次调用打印出来都是 `[1, 2, 3]`，而不是 `[1] [2] [3]`：不传 `bucket` 时，每次都用**同一个列表**，三次调用返回的是同一个对象，`print` 在三次调用都结束之后才打印，所以三个都已经是 `[1, 2, 3]`。第二行的 `__defaults__` 里直接能看到那个被不断修改的列表 `([1, 2, 3],)`。

**正确写法：用 `None` 做默认值，在函数里创建新的。**

""" + C_DEFGOOD + r"""

**读输出：** `[1] [2]`：每次不传 `bucket` 时，函数里都新建了一个空列表，互不干扰。

**陷阱二：`[[0]*3]*3`。** 同样是「共享了同一个对象」：

""" + C_GRID + r"""

**读输出：** 第一行：`grid_bad` 改了 `[0][0]` 之后变成 `[[1, 0, 0], [1, 0, 0], [1, 0, 0]]`，三行同时变了，因为 `*3` 复制的是**引用**，得到 3 个**同一个**内部列表；`grid_ok` 只有第一行变成 `[[1, 0, 0], [0, 0, 0], [0, 0, 0]]`，因为列表推导式每次循环创建一个新列表（下一节会讲推导式）。第二行 `True False` 用 `is`（比较**身份**，即是不是同一个对象）证实了这一点：`grid_bad[0] is grid_bad[1]` 为 `True`，`grid_ok` 的为 `False`；`==` 比较的则是值是否相等。**在 NumPy / PyTorch 里，切片返回的是「视图 (view)」，与原数组共享内存，也是同样的道理。**
"""),
  T(r"""
### 作用域与闭包

> **标准定义 · 作用域 (scope) 与 LEGB 规则**
>
> 一个名字在代码中**有效的范围**叫做它的**作用域**。Python 查找名字的顺序是 **L**ocal（当前函数内）→ **E**nclosing（外层函数）→ **G**lobal（模块级）→ **B**uilt-in（内置名字，如 `len`），找到就停。在函数内**对名字赋值**，会使它成为该函数的**局部变量**；要修改外层或全局的变量，需用 `nonlocal` 或 `global` 声明。
>
> *English: Python resolves names by the LEGB rule: Local, Enclosing, Global, Built-in. Assigning to a name inside a function makes it local unless declared global or nonlocal.*

> **标准定义 · 闭包 (closure)**
>
> 当一个**内层函数**引用了**外层函数的变量**，并且这个内层函数被**返回或传出**，那么即使外层函数已经执行完毕，内层函数仍然能访问这些变量。这种「函数 + 它所捕获的外层变量」的组合叫做**闭包**。
>
> *English: A closure is an inner function together with the variables from its enclosing scope that it captured; it keeps access to them after the outer function has returned.*

**白话版：「函数带着自己的小背包出门」。** 外层函数创建时，把一些变量装进背包交给内层函数；内层函数被带到别处使用时，背包还在，里面的东西还能读（`nonlocal` 声明之后还能改）。

**问题一：同一个名字 `x` 在三层里都有定义，函数读到的是哪一个？**

""" + C_SCOPE + r"""

**读输出：** `enclosing global`。`outer` 里的 `inner` 自己没有 `x`，就去外层函数找，找到了 `"enclosing"`（Enclosing）；`uses_global` 自己和外层都没有，找到模块级的 `"global"`（Global）。

**问题二：在函数里修改一个外面的变量会怎样？**

""" + C_UNBOUND + r"""

**读输出：** 得到 `UnboundLocalError`（具体错误文字随 Python 版本不同）：函数里有 `x += "!"` 这条赋值，Python 在**编译函数时**就判定 `x` 是局部变量，于是执行时读取一个还没有值的局部变量。解决办法是 `global x` / `nonlocal x`（或者更好：别修改全局状态，把值当作参数传进来、结果返回出去）。

**问题三：外层函数已经返回了，内层函数还能用它的变量吗？** 这就是闭包：

""" + C_CLOSURE + r"""

**读输出：** `1 2 3 1`：`c1` 被调用三次，计数依次是 1、2、3；`c2` 是另一次 `make_counter()` 创建的闭包，有自己独立的 `count`，所以第一次调用就是 1。**闭包给每次调用留下一份独立的状态**，这是不用类、用函数保存状态的方式，装饰器就是它的重要应用。第二行 `闭包保存的变量： 3` 是直接从 `c1.__closure__` 里读出来的：`c1` 背包里的 `count` 现在是 3。`nonlocal count` 是必需的，否则 `count += 1` 会和上一个例子一样触发 `UnboundLocalError`。

**问题四：闭包记住的是「当时的值」，还是「变量本身」？**

""" + C_LATE + r"""

**读输出：** `[2, 2, 2] [0, 1, 2]`。**闭包的晚绑定陷阱：** 闭包捕获的是**变量**，而不是创建那一刻的**值**。`[lambda: i for i in range(3)]` 里三个 lambda 共享同一个 `i`，等循环结束时 `i` 是 2，所以调用结果是 `[2, 2, 2]`。用默认参数 `i=i` 把当时的值固定下来（因为默认值在定义时求值），就得到 `[0, 1, 2]`。
"""),
  V("swU3c34d2NQ", "视频一：Programming Terms: Closures - How to Use Them and Why They Are Useful（Corey Schafer）", 12),
  T(r"""
### 函数是一等公民，以及装饰器

> **标准定义 · 一等函数 (first-class function) 与高阶函数 (higher-order function)**
>
> 在 Python 里，函数是**对象**，与整数、列表一样可以：赋给变量、放进数据结构、作为参数传给别的函数、作为返回值。**接收函数作为参数、或返回函数的函数**叫**高阶函数**。**lambda** 表达式是创建匿名的、只含一个表达式的小函数的语法。
>
> *English: Functions in Python are objects: they can be assigned, stored, passed as arguments and returned. A higher-order function takes or returns functions. A lambda is an anonymous single-expression function.*

> **标准定义 · 装饰器 (decorator)**
>
> **装饰器**是一个接收一个函数、返回一个（通常是「包装过的」）新函数的高阶函数。语法 `@deco` 写在 `def` 上方，等价于 `f = deco(f)`。包装函数通常用 `*args, **kwargs` 接收任意参数，并用 `functools.wraps` 保留原函数的名字与文档字符串。
>
> *English: A decorator is a function that takes a function and returns a (usually wrapped) function. `@deco` above a `def` is shorthand for `f = deco(f)`.*

**白话版：「给函数套一层外壳」。** 不修改函数内部，给它**外面**加上新功能：计时、记日志、检查权限、缓存结果、关闭梯度计算。每个功能写一次，用 `@` 贴到任何函数上。

**问题一：函数真的能像数据一样放进列表吗？**

""" + C_FIRST + r"""

**读输出：** `[9, 3, '-3']`：`ops` 里放的是三个函数 `square`、`abs`、`str`，推导式对每个 `f` 调用 `f(-3)`，依次得到 `9`、`3` 和字符串 `'-3'`。

**问题二：把函数当参数传给别的函数有什么用？** 最常见的是 `sorted(key=...)`、`map`、`filter`：

""" + C_KEY + r"""

**读输出：** 第一行三个结果依次是：默认排序（按字符编码，大写字母在小写之前，所以 `'Cherry'` 排在最前）`['Cherry', 'apple', 'banana', 'date']`；`key=str.lower` 把函数 `str.lower` 传给 `sorted`，实现「不分大小写排序」`['apple', 'banana', 'Cherry', 'date']`；`key=len, reverse=True` 按长度从长到短 `['banana', 'Cherry', 'apple', 'date']`（`banana` 与 `Cherry` 同长，保持原来的先后顺序）。第二行：`filter` 先留下长度大于 4 的词，`map` 再把它们转成大写，得到 `['BANANA', 'CHERRY', 'APPLE']`，`date` 因为只有 4 个字母被过滤掉了。

**问题三：怎样不改函数内部，却给它加上「计时」的功能？** 写一个装饰器：

""" + C_DECO + r"""

**读输出：** 第一行 `500000500000 slow_sum | 求 1..n 的和`：`slow_sum(10**6)` 的结果是 $1+2+\dots+10^6 = 500000500000$；`__name__` 与 `__doc__` 仍是原来的 `slow_sum` 和「求 1..n 的和」，这是 `functools.wraps` 的功劳（不加的话，`slow_sum.__name__` 会变成 `wrapper`，调试和文档工具都会被误导）。`@timer` 把 `slow_sum` 换成了 `timer(slow_sum)` 返回的 `wrapper`，所以第二行 `耗时已被记录： True`：`wrapper.last` 里存了这次调用的耗时（具体数值每台机器不同，所以这里只检查它被记录了）。

**问题四：装饰器本身要带参数怎么办？** 多套一层，先接收参数：

""" + C_DECO2 + r"""

**读输出：** `['hi Yijia', 'hi Yijia', 'hi Yijia']`：`@repeat(3)` 先调用 `repeat(3)`，返回真正的装饰器 `deco`，再由 `deco` 去装饰 `hello`，所以共三层闭包；装饰后的 `hello("Yijia")` 调用了原函数 3 次，把 3 个结果收成列表。

你已经遇到过的装饰器：本节递归部分的 `@lru_cache`，PyTorch 里的 `@torch.no_grad()`，之后会学的 `@property`、`@dataclass`。写一个新的装饰器的机会不多，**但读懂它是读 ML 代码的必备技能**。
"""),
  V("U-G-mSd4KAE", "视频二：Learn Python DECORATORS in 7 minutes!（Bro Code）", 7),
  T(r"""
### 递归

> **标准定义 · 递归 (recursion)**
>
> 一个函数**直接或间接地调用自己**，称为**递归**。每个正确的递归函数必须有两部分：**基础情形 (base case)**：不用再递归就能直接给出答案，保证递归**会停**；**递归情形 (recursive case)**：把问题化为**更小**的同类问题，再用它的结果组合出答案，并且每一步都**更接近基础情形**。
>
> *English: Recursion is when a function calls itself. It needs a base case that stops the recursion and a recursive case that reduces the problem towards the base case.*

**白话版：「俄罗斯套娃」。** 打开一个套娃，里面是更小的同样的套娃，一直打开到最小的实心娃娃（基础情形），再一层层合上。每次函数调用，Python 会在**调用栈 (call stack)** 上放一个**栈帧 (stack frame)** 保存当前的局部变量，调用结束后弹出，所以递归太深会撑满栈，抛出 `RecursionError`。

**问题一：一个最小的递归函数长什么样？**

""" + C_FACT + r"""

**读输出：** `120 2432902008176640000`，即 $5! = 120$ 与 $20! = 2432902008176640000$。`fact(5)` 展开成 `5 * fact(4)`，一路展开到 `fact(0)` 返回 1（基础情形），再一层层乘回来。

**问题二：递归能嵌套多深？**

""" + C_STACK + r"""

**读输出：** 默认递归深度上限是 `1000`（用 `sys.getrecursionlimit()` 查看）：`depth(500)` 没问题，返回 `500`；`depth(100000)` 就会抛出 `RecursionError`（`maximum recursion depth exceeded ...`，后半句随版本不同）。可以用 `sys.setrecursionlimit` 调大，但调得太大会让整个 Python 进程崩溃，**更稳妥的做法是改写成循环或显式栈**（数据结构那一门课的 DFS 就是这么做的）。

**问题三：忘了写基础情形会怎样？**

""" + C_FOREVER + r"""

**读输出：** 没有基础情形的 `forever` 永远不会停，调用栈被撑满，同样以 `RecursionError` 结束，所以会打印那句话。

**问题四：为什么朴素的递归斐波那契很慢？**

""" + C_FIB + r"""

**读输出：** 朴素的 `fib(25)` 调用了 `242785` 次，因为大量子问题被重复计算（`fib(23)` 会被反复重新算）。

**用记忆化修复：**

""" + C_FIB2 + r"""

**读输出：** `@lru_cache` 让每个 $n$ 只算一次，所以只有 `26` 次调用（$n=0,1,\dots,25$ 各一次），而 `cache_info` 里的 `misses=26` 就是这 26 次真正的计算，`hits=23` 是直接从缓存取出结果的次数。这就是**记忆化**，数据结构那一门课的动态规划一节会系统讲。

**问题五：什么时候递归最自然？** 当**结构本身是嵌套的**：嵌套的列表、文件夹里的文件夹、树、JSON、表达式。

""" + C_FLAT + r"""

**读输出：** `[1, 2, 3, 4, 5, 6]`：`flatten` 对任意深度的嵌套列表都能展平；遇到不是列表的元素就是基础情形（返回单元素列表），遇到列表就对每个元素递归，再把结果拼起来。用循环写会很别扭，用递归几行就行。（递归的更深入内容，如主定理、分治与回溯，在「数据结构与算法」的第 5 节。）

### 写函数的几个好习惯

- 一个函数**只做一件事**，名字用动词（`load_data`、`compute_loss`）；
- 用**文档字符串 (docstring)** 说明参数与返回值；类型注解（第 4 节会学）让别人（和 IDE）知道该传什么；
- 尽量**不修改传入的参数、不依赖全局变量**：同样的输入总是得到同样的输出（**纯函数 pure function**）的代码最容易测试和调试；
- 需要修改参数时，在文档里写清楚，并考虑函数名里体现（比如 `sort` 与 `sorted`：前者原地修改，后者返回新列表）。

### 这一节你要带走的三句话

1. **参数有位置、关键字、默认、`*args`、`**kwargs`、仅关键字等形式**；Python 传的是**对象的引用**，可变对象会被函数「改到」，默认参数只在定义时创建一次，所以**不要用 `[]` 做默认值**。
2. **名字按 LEGB 查找；闭包让函数带着外层变量的「背包」出门**，装饰器就是「接收函数、返回新函数」的闭包应用；闭包捕获的是变量，不是值。
3. **递归 = 基础情形 + 递归情形**，靠调用栈实现，深度有限；重复子问题用 `lru_cache` 记忆化，需要很深时改成循环。
"""),
  V("mz6tAJMVmfM", "视频三：Recursion - CS50 Shorts（Harvard CS50）", 14),
  THINK("下面这段代码打印什么？为什么？怎样改才能打印 `[1] [2]`？代码：`def add(x, items=[]): items.append(x); return items`，然后 `print(add(1), add(2))`。", r"""
打印 `[1, 2] [1, 2]`。默认值 `[]` 是在 `def` 执行时**只创建一次**的列表对象，之后每次不传 `items` 都用**同一个**列表，`add(1)` 把 1 加进去，`add(2)` 又把 2 加进同一个列表；两次调用返回的是同一个对象，而 `print` 在两次调用都结束之后才打印，所以两个都显示 `[1, 2]`。

修改：用 `None` 做默认值。

```python
def add(x, items=None):
    if items is None:
        items = []
    items.append(x)
    return items
```

这样每次不传 `items` 时，都在函数内**新建**一个列表。注意要用 `is None` 而不是 `if not items`，后者会把调用者传入的**空列表**也当成「没传」。
"""),
  THINK("写一个装饰器 `count_calls`，让被装饰的函数每被调用一次，就把计数加 1，并且能通过 `func.calls` 读取次数。提示：函数本身也是对象，可以给它加属性。", r"""
```python
import functools

def count_calls(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        wrapper.calls += 1
        return func(*args, **kwargs)
    wrapper.calls = 0
    return wrapper

@count_calls
def hello():
    return "hi"

hello(); hello()
print(hello.calls)   # 2
```

关键：**计数器放在 `wrapper` 这个函数对象的属性上**，每次调用时加 1。用 `*args, **kwargs` 让它能装饰任何参数形式的函数；`functools.wraps` 保留原函数的名字。另一种写法是用闭包里的变量加 `nonlocal`，但那样外面读不到次数，除非再多暴露一个读取的函数。
"""),
  THINK("为什么递归求 $n!$ 在 $n$ 很大（比如 $10^5$）时会失败，而用 `for` 循环写的版本不会？这两种写法的**空间复杂度**分别是多少？", r"""
递归版每次调用都要在**调用栈**上放一个栈帧，$n$ 层嵌套就同时有 $n$ 个栈帧，**空间 $O(n)$**，并且 Python 把深度限制在约 1000，所以 $n=10^5$ 会抛出 `RecursionError`。循环版只用一个累乘变量，**空间 $O(1)$**，没有深度限制。时间上两者都是 $O(n)$ 次乘法。

这引出一个通用的方法：**任何递归都可以改写成循环**，需要保存状态时用一个显式的栈代替隐式的调用栈。有些语言（如 Scheme）会做「尾调用优化」，让某些递归不占用栈；**Python 没有这个优化**，所以 Python 里要把「可能很深」的递归改成循环。
"""),
  KW(("参数 / 实参","parameter / argument","定义时的名字 / 调用时传入的值"),
     ("默认参数","default argument","不传时使用的默认值，只在定义时求值一次"),
     ("可变参数","*args / **kwargs","收集多余的位置 / 关键字实参为元组 / 字典"),
     ("仅关键字参数","keyword-only parameter","写在 `*` 之后，只能用关键字传"),
     ("传对象引用","pass by object reference","形参与实参指向同一个对象；修改可变对象会被外面看到"),
     ("可变 / 不可变","mutable / immutable","列表、字典、集合可原地修改；整数、字符串、元组不可"),
     ("作用域","scope","名字有效的范围；LEGB 查找规则"),
     ("闭包","closure","内层函数 + 它捕获的外层变量"),
     ("晚绑定","late binding","闭包捕获变量而不是值，调用时才取值"),
     ("一等函数","first-class function","函数是对象，可以赋值、传参、返回"),
     ("装饰器","decorator","接收函数、返回新函数；`@deco` 语法糖"),
     ("递归","recursion","函数调用自己；需要基础情形与递归情形"),
     ("调用栈","call stack","保存各层函数调用的局部变量的栈"),
     ("记忆化","memoization","缓存函数结果避免重复计算，如 `lru_cache`"),
  ),
 ],
 "references": [
  {"title": "Think Python 3e（Downey）— 第 3 章 Functions 与第 5 章 Conditionals and Recursion", "url": "https://allendowney.github.io/ThinkPython/chap03.html", "note": "本节大纲依据之一，CC BY-NC-SA 4.0，带 Colab 可运行笔记本"},
  {"title": "Python Tutorial for Beginners 8: Functions（Corey Schafer，约 22 分钟，选看）", "url": "https://www.youtube.com/watch?v=9Os0o3wzS_I", "note": "函数基础与参数形式的详细演示，参数部分不熟时回看"},
  {"title": "Python Tutorial: Variable Scope - LEGB（Corey Schafer，约 21 分钟，选看）", "url": "https://www.youtube.com/watch?v=QVdf0LgmICw", "note": "作用域、`global`、`nonlocal` 的完整讲解"},
  {"title": "Harvard CS50P：Introduction to Programming with Python（课程主页）", "url": "https://cs50.harvard.edu/python/", "note": "大学课程原版，函数、异常、测试、文件等都有视频和习题"},
  {"title": "Python 文档：functools（lru_cache、wraps）", "url": "https://docs.python.org/3/library/functools.html", "note": "记忆化装饰器与 wraps 的官方说明"},
 ],
 "quiz": {"questions": [
  Q("下面的函数调用 `f(1)`、`f(2)` 后，两次返回值打印出来是什么？`def f(x, l=[]): l.append(x); return l`", 
    ["`[1]` 和 `[2]`", "`[1, 2]` 和 `[1, 2]`（同一个列表对象）", "报错", "`[1]` 和 `[1, 2]`"], 1,
    "默认值在定义时创建一次，所有不传 `l` 的调用共享同一个列表，两次返回的是同一个对象，打印时两个都已是 `[1, 2]`。"),
  Q("在 `def f(a, b=2, *args, c, **kwargs)` 中，调用时 `c` 必须怎么传？",
    ["按位置传在 `b` 之后", "用关键字传，如 `c=5`", "可以不传", "放进 `kwargs`"], 1,
    "`*args` 之后的参数是仅关键字参数，没有默认值时必须以 `c=...` 的形式传入。"),
  Q("Python 的参数传递机制最准确的说法是？",
    ["所有参数按值复制", "所有参数按引用传递，函数里的任何赋值都会改变外面的变量", "传的是对象的引用：修改可变对象外面可见，对名字重新赋值外面不受影响", "只有整数按值传递，其余按引用"], 2,
    "形参与实参指向同一个对象。`lst.append()` 改的是对象本身；`lst = [...]` 只改了局部名字的指向。"),
  Q("`grid = [[0] * 3] * 3`，然后 `grid[0][0] = 1`，`grid` 变成什么？",
    ["`[[1,0,0],[0,0,0],[0,0,0]]`", "`[[1,0,0],[1,0,0],[1,0,0]]`（三行是同一个列表）", "`[[1,1,1],[1,1,1],[1,1,1]]`", "报错"], 1,
    "`*3` 复制的是引用，三行是同一个对象。要用 `[[0]*3 for _ in range(3)]`。"),
  Q("Python 查找一个名字的 **LEGB** 顺序是？",
    ["Global → Local → Built-in → Enclosing", "Local → Enclosing → Global → Built-in", "Built-in → Global → Enclosing → Local", "Local → Global → Enclosing → Built-in"], 1,
    "先找当前函数（Local），再找外层函数（Enclosing），然后模块级（Global），最后内置（Built-in）。"),
  Q("在内层函数里想**修改**外层函数里定义的变量 `count`（`count += 1`），需要？",
    ["什么都不用", "`global count`", "在内层函数里声明 `nonlocal count`", "把 `count` 改名"], 2,
    "不声明的话，赋值会让 `count` 成为内层函数的局部变量，读取时会 `UnboundLocalError`。`global` 对应的是模块级变量。"),
  Q("`funcs = [lambda: i for i in range(3)]` 之后，`[f() for f in funcs]` 的结果是？",
    ["`[0, 1, 2]`", "`[2, 2, 2]`", "`[3, 3, 3]`", "报错"], 1,
    "闭包捕获的是变量 `i`，调用时才取值，此时循环已结束，`i` 是 2。用 `lambda i=i: i` 可固定当时的值。"),
  Q("装饰器语法 `@deco` 写在 `def f(): ...` 上方，等价于？",
    ["`f = deco`", "`deco(f())`", "`f = deco(f)`", "`deco = f(deco)`"], 2,
    "装饰器接收原函数，返回新函数，并替换原来的名字。"),
  Q("写装饰器时，在 `wrapper` 上加 `@functools.wraps(func)` 的作用是？",
    ["让函数运行更快", "保留原函数的 `__name__`、`__doc__` 等信息", "让装饰器可以带参数", "防止递归"], 1,
    "不加时，被装饰函数的 `__name__` 会变成 `wrapper`，文档字符串丢失，调试和文档工具会被误导。"),
  Q("一个正确的递归函数**必须**有的两个要素是？",
    ["循环与条件", "基础情形（会停）与递归情形（把问题缩小）", "全局变量与返回值", "装饰器与缓存"], 1,
    "没有基础情形会无限递归；递归情形不使问题变小，同样不会收敛到基础情形。"),
 ]},
}

TARGET = [1, 3, 2, 0, 3, 1, 0, 2, 0, 1]
for q, t in zip(unit["quiz"]["questions"], TARGET):
    q["options"][q["answer"]], q["options"][t] = q["options"][t], q["options"][q["answer"]]
    q["answer"] = t

if __name__ == '__main__':
    dump(unit, "py-0", "u01-functions-recursion.json")
