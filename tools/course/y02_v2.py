"""py-0 第 2 节：推导式、迭代器、生成器"""
from unitlib import *
from y02c import *

unit = {
 "id": "u02",
 "title": "推导式、迭代器与生成器",
 "en": "Comprehensions, Iterators & Generators",
 "minutes": 90,
 "objectives": [
  "会写 **列表 / 字典 / 集合推导式 (comprehension)**，知道它与 `for` 循环的等价关系，也知道什么时候不该用",
  "分清 **可迭代对象 (iterable)** 与 **迭代器 (iterator)**，说出 `for` 循环背后的 `iter()` / `next()` / `StopIteration` 协议，会写自己的迭代器",
  "会写 **生成器 (generator)**（`yield`、生成器表达式、`yield from`），理解 **惰性求值 (lazy evaluation)** 为什么能省内存、能表示无限序列",
  "熟练使用 `zip`、`enumerate`、`sorted(key=)`、`itertools` 与 `collections`（`Counter`、`defaultdict`、`deque`、`namedtuple`）",
 ],
 "blocks": [
  T(r"""
### 先说这一节要干什么

上一节讲了函数。这一节讲 Python 里**处理一批数据**的方式：怎么简洁地变换一个序列（推导式），`for` 循环背后到底在做什么（迭代器协议），以及怎么**不把所有数据一次装进内存**（生成器）。这些是写「Pythonic」代码的基本功，也是读懂 ML 代码的钥匙。

**学完它你就能看懂这几件事：**

- **PyTorch 的 `DataLoader`**：`for batch in loader` 能工作，因为它是一个**可迭代对象**，每次产出一个 batch，这正是生成器的思路；训练大模型时，数据集大到装不进内存，必须**流式 (streaming)** 读取，也是惰性迭代；
- 代码里满屏的 `[f(x) for x in xs if cond]`、`{k: v for k, v in ...}`、`zip(*batch)`、`enumerate(loader)`；
- `itertools`、`collections.Counter`、`defaultdict`：数据处理与面试题里天天用；
- 数据结构那一门课里的 BFS、堆、哈希表，用 `deque`、`heapq`、`Counter` 写会简洁得多。

**本节安排（约 90 分钟）**：推导式与视频一（25 分钟）→ 迭代器协议（20 分钟）→ 生成器与视频二（25 分钟）→ `itertools` 与 `collections`（10 分钟）→ 总结与「想一想」（10 分钟）。

**怎么学这一节：** 每个知识点都是「一小段代码 → 紧跟着读它的输出」。每个代码块都可以点「▶ 运行」，也可以改一改再跑；同一节里，前面的块定义的变量和函数，后面的块可以直接用，所以请**按顺序**往下跑。

### 推导式

> **标准定义 · 推导式 (comprehension)**
>
> **推导式**是用一个表达式**构造容器**的简洁语法：`[expr for x in iterable if cond]`（列表）、`{expr for ...}`（集合）、`{k: v for ...}`（字典）。它等价于「循环遍历 `iterable`，对满足 `cond` 的每个 `x` 计算 `expr`，并把结果收集起来」。多个 `for` 从左到右嵌套，**先写的是外层循环**。
>
> *English: A comprehension builds a list, set or dict from an iterable with an optional filter: [expr for x in iterable if cond]. Multiple for clauses nest left to right.*

**白话版：「流水线上的加工单」。** 一句话说清：「从这堆东西里，挑出符合条件的，每个按这个方式加工一下，装进一个新盒子。」比起写三四行 `for` + `append`，推导式把「做什么」写在一行里。

**问题一：怎样用一行把一个序列「变换」或「过滤」成新列表？**

""" + C_LISTCOMP + r"""

**读输出：** 第一行是 0 到 9 的平方 `[0, 1, 4, 9, 16, 25, 36, 49, 64, 81]`。第二行 `evens` 是 `[0, 2, 4, 6, 8]`：末尾的 `if` 是**过滤**，不满足条件的元素被丢掉；`labels` 是 `['even', 'odd', 'even', 'odd']`：`[a if cond else b for x in xs]`（条件表达式）与 `[a for x in xs if cond]`（过滤）位置不同、作用不同，前者每个元素都产出一个值，后者会**丢掉**不满足条件的元素。

**问题二：推导式和普通 `for` 循环是什么关系？**

""" + C_EQUIV + r"""

**读输出：** `等价： True`：推导式 `[x * x for x in nums]` 与「建空列表、循环、`append`」得到完全相同的列表。把推导式读成循环：先看 `for`，再看 `if`，最前面的表达式是「每次 `append` 的东西」。

**问题三：两层循环怎么写成推导式？**

""" + C_NEST + r"""

**读输出：** `[1, 2, 3, 4, 5, 6] [[1, 4], [2, 5], [3, 6]] [(1, 4), (2, 5), (3, 6)]`。嵌套推导式里，**写在前面的 `for` 是外层循环**：`[v for row in matrix for v in row]` 就是「先遍历每一行，再遍历这一行的每个值」，得到展平的 `[1, 2, 3, 4, 5, 6]`。`transposed` 是外层按列号 `j`、内层取每一行的第 `j` 个值，得到转置 `[[1, 4], [2, 5], [3, 6]]`；`zip(*matrix)` 把每一行拆开并行遍历，得到同样的结果（只是每列是元组）。

**问题四：能不能直接造字典和集合？**

""" + C_DICTSET + r"""

**读输出：** `{'apple': 5, 'Banana': 6, 'cherry': 6} ['a', 'b', 'c'] {5: 'apple', 6: 'cherry'}`。`length` 里 `apple` 出现了两次，后面的覆盖前面的，所以只有三个键；`first_letters` 是集合，自动去重，取首字母小写后排序得到 `['a', 'b', 'c']`。字典推导式 `{v: k ...}` 在值有重复时会丢信息：`inverted` 里 `'Banana'` 与 `'cherry'` 的长度都是 6，只留下了最后一个 `'cherry'`。

**问题五：推导式里的循环变量会「泄漏」到外面吗？**

""" + C_CSCOPE + r"""

**读输出：** `x 仍然是： outer`：推导式有自己的作用域，循环变量 `x` 不会泄漏到外面，外面的 `x` 没被改。

**什么时候不该用？** 推导式适合「一个表达式、一个简单条件」。看看下面这个例子：

""" + C_COMPLEX + r"""

**读输出：** `[(0, 1), (0, 3), (1, 2), (2, 3)]`：两层循环、两个条件，已经需要停下来想一想才能看懂。如果需要多个条件分支、嵌套三层、或者要产生副作用（比如打印），**写成普通的 `for` 循环**更清楚。「简洁」不等于「聪明」：可读性比一行内塞多少逻辑重要得多。

**推导式比 `for` + `append` 快吗？**

""" + C_SPEED + r"""

**读输出：** `两种写法结果一样： True`。至于谁更快：在常见的 CPython 里，推导式通常比 `for` + `append` 略快（少了每次查找 `append` 方法并调用它的开销），但差别不大，而且随 Python 版本和运行环境而变（网页里的 Python 就可能看不出差别）。所以选推导式的理由是**更短、更清楚**，不是为了速度。
"""),
  V("3dt4OGnU5sM", "视频一：Python Tutorial: Comprehensions - How they work and why you should be using them（Corey Schafer）", 18),
  T(r"""
### 迭代器：`for` 循环背后的协议

> **标准定义 · 可迭代对象与迭代器 (iterable & iterator)**
>
> **可迭代对象 (iterable)**：实现了 `__iter__()`，能返回一个迭代器的对象（列表、元组、字符串、字典、集合、文件、`range`……），可以放在 `for` 的 `in` 后面。**迭代器 (iterator)**：实现了 `__next__()` 与 `__iter__()`（返回自己）的对象；每次 `next()` 返回下一个元素，**没有更多元素时抛出 `StopIteration`**。`for x in obj` 的执行过程是：调用 `iter(obj)` 得到迭代器，反复调用 `next()`，直到遇到 `StopIteration` 为止。
>
> *English: An iterable has __iter__() returning an iterator; an iterator has __next__() which returns the next item or raises StopIteration. A for loop calls iter() once and next() repeatedly.*

**白话版：「书」与「书签」。** 可迭代对象像一本**书**，可以反复读；迭代器像夹在书里的**书签**，记着你读到哪一页，往前翻一页（`next`）就不能再回头，翻到最后一页再翻就是 `StopIteration`。同一本书可以同时有多个书签，互不影响；`iter(lst)` 每次给你一个新书签。

**问题一：列表和「列表的迭代器」是同一种东西吗？用完之后会怎样？**

""" + C_ITER + r"""

**读输出：** 第一行 `list list_iterator`：列表是 `list`，`iter(lst)` 得到的是另一种对象 `list_iterator`，所以列表是**可迭代对象**，不是迭代器。接着三次 `next` 依次给出 `10 20 30`；第四次 `next(it)` 已经没有元素了，抛出 `StopIteration`，所以打印了「StopIteration：迭代器用完了」。

**问题二：`for` 循环到底做了什么？**

""" + C_FORLOOP + r"""

**读输出：** 依次打印 `取到 10`、`取到 20`、`取到 30`，之后第四次 `next` 抛出 `StopIteration`，被 `except` 接住后 `break` 退出。这个 `while` + `try` 就是 `for x in lst:` 背后做的事：`iter()` 一次，`next()` 反复，直到 `StopIteration`。

**问题三：迭代器能反复用吗？**

""" + C_ONCE + r"""

**读输出：** 第一行 `[10, 20, 30] []`：**迭代器是一次性的**，第一次 `list(it)` 把它耗尽，第二次得到空列表，因为书签已经翻到底了。第二行 `[10, 20, 30] [10, 20, 30]`：列表本身每次 `iter()` 都得到新的迭代器，可以反复遍历。

**问题四：怎么自己写一个迭代器？** 实现 `__iter__` 与 `__next__` 两个方法：

""" + C_CLASS + r"""

**读输出：** `[5, 4, 3, 2, 1]`：`Countdown(5)` 每次 `__next__` 返回当前的数并减一，到 0 时抛出 `StopIteration`，`list` 就停止收集。第二行 `5050 3`：同一个迭代器协议让它可以直接交给 `sum`（$100+99+\dots+1 = 5050$）和 `max`（`Countdown(3)` 产出 3、2、1，最大是 3）。凡是实现了这个协议的对象，所有接收可迭代对象的函数都能用。（`class` 的完整写法在第 3 节讲。）

**问题五：`zip`、`map`、`enumerate` 这些内置函数返回的是什么？** 它们返回的都是惰性迭代器，包括 `filter`、`reversed`、`range`（可迭代对象）以及**文件对象**，**不会一次把所有结果算出来**：

""" + C_LAZY + r"""

**读输出：** `zip [('A', 90), ('B', 85), ('C', 70)] []`：`type(z).__name__` 是 `zip`；`z` 被第一个 `list(z)` 消耗之后，第二个 `list(z)` 就是空的，这是初学者最常见的坑之一：想用两次就先 `list()` 存起来。

**问题六：`zip` 与 `enumerate` 怎么用？**

""" + C_ZIP + r"""

**读输出：** 前三行 `1 A 90`、`2 B 85`、`3 C 70`：`enumerate(..., start=1)` 从指定的数开始计数，并与 `zip` 的元组一起解包成 `i, (n, s)`。接着 `[(1, 'a'), (2, 'b')]`：`zip` 遇到最短的序列就停（需要补齐时用 `itertools.zip_longest`），所以 `3` 被丢掉了。最后 `{'A': 90, 'B': 85, 'C': 70}`：`dict(zip(keys, values))` 是由两个列表建字典的惯用写法。

### 生成器：用函数写迭代器

> **标准定义 · 生成器 (generator)**
>
> 含有 `yield` 的函数称为**生成器函数 (generator function)**，调用它**不会执行函数体**，而是返回一个**生成器对象 (generator object)**，它是一种迭代器。每次 `next()`，函数体运行到下一个 `yield` 就**暂停并返回**该值，**保留所有局部变量的状态**，下次接着往下运行；函数结束时自动抛出 `StopIteration`。把推导式的 `[]` 换成 `()` 得到**生成器表达式 (generator expression)**，同样是惰性的。`yield from iterable` 把另一个可迭代对象的元素逐个转发出去。
>
> *English: A function containing yield is a generator function; calling it returns a generator (an iterator). Each next() resumes the body until the next yield, preserving local state. A generator expression uses parentheses and is lazy.*

**白话版：「会暂停的函数」。** 普通函数 `return` 之后就彻底结束了；生成器函数 `yield` 之后只是**暂停**，像看视频按了暂停键，下次按播放，从刚才停的地方继续。你想要下一个元素时它才工作，这就是**惰性求值**：**不要求的不算**。

**问题一：`yield` 到底让函数「暂停」在哪里？** 在函数体里加上打印，看执行的顺序：

""" + C_YIELD + r"""

**读输出：** 第一行 `创建了生成器，函数体还没有运行： generator`：创建生成器时**什么都没打印**，函数体根本还没跑。第一次 `next(g)`：才打印「开始」「准备产出 0」，然后暂停并把 0 返回，所以接着是 `next -> 0`。第二次 `next(g)`：从暂停处继续，先打印「0 已被取走」，循环进入下一轮，打印「准备产出 1」，返回 1，即 `next -> 1`。第三次 `next(g)`：先打印「1 已被取走」，循环结束，打印「结束」，函数体走完，自动抛出 `StopIteration`。可以清楚看到「产出 → 暂停 → 下一次 next 时才继续」的交替。

**为什么要用生成器？** 接下来四个例子对应四个理由。

**一，省内存。** 把推导式的 `[]` 换成 `()`：

""" + C_GENEXP + r"""

**读输出：** 第一行 `True`：一百万个平方数的列表要为每个元素保存一个引用（量级是几个 MB），而生成器表达式只有一个很小的对象（百字节量级），前者比后者大 100 倍以上（具体字节数随系统与版本不同，这里只检查倍数）。第二行 `333332833333500000`：$\sum_{i<10^6} i^2$ 的值，`sum` 边取边加，**内存始终只有一个元素**。数据量大到装不进内存时（几十 GB 的语料、日志、数据集），这是唯一的办法。

**二，能表示无限序列。**

""" + C_INF + r"""

**读输出：** `[0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89]`：`fib()` 里是 `while True`，永不结束，但生成器每次只算一个，`islice` 取前 12 个就停，所以不会卡住。只有惰性才能表示无限序列。

**三，能搭流水线。**

""" + C_PIPE + r"""

**读输出：** `['alpha', 'beta', 'gamma']`：`read_lines` 产出原始行，`strip` 去掉首尾空白，`non_empty` 丢掉空行；`non_empty(strip(read_lines()))` 每一步都只处理一个元素，**整个流程是流式的**，空字符串 `""` 和只有空格的行被过滤掉了。

**四，批量产出。**

""" + C_BATCH + r"""

**读输出：** `[[0, 1, 2, 3], [4, 5, 6, 7], [8, 9]]`：`range(0, 10, 4)` 给出起点 0、4、8，每次切一片，最后一批不足 4 个，只有 `[8, 9]`。`batches` 就是 `DataLoader` 的雏形：每次产出一个 batch。

**`yield from`：转发另一个可迭代对象。**

""" + C_YF + r"""

**读输出：** `[1, 2, 'x', 'y']`：`yield from a` 把 `[1, 2]` 的元素逐个转发，再转发字符串 `"xy"` 的两个字符，效果等于两个 `for ... yield` 循环。

**注意：** 生成器同样是**一次性**的，不能 `len()`，不能下标访问，不能重新开始（要重来就再调用一次生成器函数）。需要多次遍历或随机访问，就老实用列表。

### `itertools` 与 `collections`

标准库里这两个模块把常见的模式做成了现成的工具，面试题和数据处理里非常常用。先看 `itertools`：

""" + C_ITT + r"""

**读输出：** 六行依次是：`chain` 把几个序列接起来，`[1, 2, 3, 'a', 'b']`；`product` 笛卡尔积（遍历超参数网格 grid search 时用），`repeat=2` 得到 `[(0, 0), (0, 1), (1, 0), (1, 1)]`；`combinations("ABC", 2)` 不计顺序选 2 个，`[('A', 'B'), ('A', 'C'), ('B', 'C')]`；`permutations` 排列，4 个元素的全排列数是 `24 = 4! = 24`；`accumulate` 前缀和 `[1, 3, 6, 10]`；`count(1)` 是无限计数器，与 `"abc"` 一起 `zip`，遇到最短的 `"abc"` 就停，得到 `[(1, 'a'), (2, 'b'), (3, 'c')]`。另外 `islice` 可以对任何迭代器切片（上面生成器里已经用过）。

**`groupby` 有一个必须知道的陷阱：**

""" + C_GROUPBY + r"""

**读输出：** `groupby` **只合并相邻的**相同键。第一次没排序，`'a'` 开头的词出现在两处，所以 `'a'` 被分成了两组：`('a', ['apple', 'avocado'])` 和最后的 `('a', ['apricot'])`。第二次先 `sorted`，相同键相邻，三个 `'a'` 词合成一组 `['apple', 'apricot', 'avocado']`，一共三组。所以通常要先排序。

接着看 `collections`。**`Counter`** 数频次：

""" + C_COUNTER + r"""

**读输出：** `[('the', 3), ('and', 2)] 3 0`：`most_common(2)` 给出出现最多的两个词：`the` 3 次、`and` 2 次；`cnt["the"]` 是 3；`cnt["dog"]` 没出现过，返回 0 而不是报错。

**`defaultdict`**：不存在的键自动创建默认值（省去 `if key not in d`）：

""" + C_DDICT + r"""

**读输出：** `{'a': ['apple', 'avocado', 'apricot'], 'b': ['banana', 'blueberry'], 'c': ['cherry']}`：`groups[w[0]]` 第一次遇到某个字母时，自动创建空列表，再 `append`；与 `groupby` 不同，它不需要排序，按键把所有元素分到一起。

**`deque`**：双端队列，两头操作 $O(1)$，加 `maxlen` 就成了「只保留最近 $n$ 个」的滑动窗口（数据结构那一门课的队列和 BFS 用它）：

""" + C_DEQUE + r"""

**读输出：** `只保留最近 3 个： [3, 4, 5]`：依次追加 0 到 5，队列满了 3 个之后，每追加一个就从另一端挤掉最老的，最后只剩 3、4、5。

**`namedtuple`**：带字段名的轻量元组：

""" + C_NT + r"""

**读输出：** `Point(x=3, y=4) 3 4 {'x': 3, 'y': 4}`：既能像元组那样 `p[1]`（得到 4），又能像属性那样 `p.x`（得到 3），`_asdict()` 转成字典。

### 这一节你要带走的三句话

1. **推导式**是「变换 + 过滤一批数据」的简洁写法，等价于 `for` 循环；写不清楚时就写成循环。
2. **`for` 循环 = `iter()` 反复 `next()` 直到 `StopIteration`**；**可迭代对象可以反复遍历，迭代器是一次性的**。
3. **生成器 = 会暂停的函数**，惰性求值：省内存、可表示无限序列、能搭流水线；`DataLoader`、流式读取大数据都是这个思想。
"""),
  V("bD05uGo_sVI", "视频二：Python Tutorial: Generators - How to use them and the benefits you receive（Corey Schafer）", 11),
  THINK("`[x*x for x in range(10**8)]` 与 `(x*x for x in range(10**8))` 这两行，在内存和时间上分别发生了什么？如果接着做 `sum(...)` 呢？", r"""
第一行**立即**把 $10^8$ 个平方数全部算出并放进列表：要占用几个 GB 的内存（每个整数对象加上列表中的指针，量级约 $10^9$ 字节以上），可能直接把内存耗尽，而且在执行完这一行之前什么也得不到。第二行**几乎瞬间完成**：它只创建了一个生成器对象，一个元素都还没算。

接着做 `sum(...)`：对生成器，`sum` 一边向它要下一个元素、一边累加，内存始终只有常数级，总时间还是 $O(10^8)$（和列表版本做的计算量一样，但没有「先全部存下来」的开销）。结论：**只需要遍历一次的大序列，用生成器表达式**；需要多次遍历、随机访问或知道长度时，再用列表。
"""),
  THINK("`for` 循环遍历一个**列表**时，同时在循环里往这个列表里 `append` 元素，会发生什么？遍历一个**字典**时，往字典里加新键呢？为什么？", r"""
对**列表**：列表的迭代器记录的是「下标」，每次检查「下标是否小于当前长度」。如果循环里不断 `append`，长度一直在增加，循环可能**永远不会结束**（比如 `for x in lst: lst.append(x)`）。对**字典**：Python 检测到「遍历过程中字典大小改变」，会直接抛出 `RuntimeError: dictionary changed size during iteration`，因为哈希表插入新键可能触发扩容、重排，迭代器的位置就失效了（数据结构第 4 节讲过哈希表的扩容）。

规则：**不要在遍历一个容器的同时修改它的大小**。想边遍历边增删，就遍历它的**副本**（`for x in list(lst)`），或者先把要做的修改收集起来，遍历结束后再统一执行，或者直接构造一个新的容器（用推导式）。
"""),
  THINK("你要处理一个 50 GB 的文本文件，统计每个单词出现的次数。写出思路，说明为什么不能 `f.read().split()`，并用本节学到的工具写出来。", r"""
`f.read()` 会把整个 50 GB 一次读进内存，直接爆内存。文件对象本身就是**逐行读取的迭代器**，`for line in f` 每次只在内存里放一行。把「读行 → 切词 → 计数」串成流水线：

```python-static
from collections import Counter

def words(path):
    with open(path, encoding="utf-8") as f:
        for line in f:                 # 一次一行
            yield from line.lower().split()

counts = Counter(words("big.txt"))     # Counter 边取边计数
print(counts.most_common(10))
```

内存里只有**一行文本**加上一个「单词 → 次数」的计数字典，字典的大小与**不同单词的个数**成正比，而不是与文件大小成正比。这是 MapReduce 的单机版缩影：流式读取、逐个处理、聚合。如果连不同单词都太多（比如统计 n-gram），就要分块处理再合并，或者用磁盘上的数据库。
"""),
  KW(("推导式","comprehension","用一个表达式构造列表 / 集合 / 字典"),
     ("条件表达式","conditional expression","`a if cond else b`，每个元素都产出一个值"),
     ("可迭代对象","iterable","可以被 `for` 遍历，实现了 `__iter__`"),
     ("迭代器","iterator","记住遍历位置，`next()` 取下一个，用完抛 `StopIteration`"),
     ("迭代器协议","iterator protocol","`__iter__` 与 `__next__` 两个方法"),
     ("生成器","generator","含 `yield` 的函数返回的迭代器，会暂停与恢复"),
     ("生成器表达式","generator expression","用 `()` 写的惰性推导式"),
     ("惰性求值","lazy evaluation","需要时才计算，不提前算出所有结果"),
     ("`yield from`","yield from","把另一个可迭代对象的元素逐个转发"),
     ("`zip` / `enumerate`","zip / enumerate","并行遍历多个序列 / 遍历时附带下标"),
     ("`itertools`","itertools","标准库的迭代器工具：chain、product、combinations、groupby……"),
     ("`Counter` / `defaultdict`","Counter / defaultdict","数频次的字典 / 缺失键自动创建默认值的字典"),
     ("`deque`","deque (double-ended queue)","双端队列，两头 $O(1)$；`maxlen` 实现滑动窗口"),
  ),
 ],
 "references": [
  {"title": "Think Python 3e（Downey）— 第 9 章 Lists 与第 10 章 Dictionaries", "url": "https://allendowney.github.io/ThinkPython/chap09.html", "note": "本节大纲依据之一，列表、字典与它们的常用操作，CC BY-NC-SA 4.0"},
  {"title": "Python Tutorial: Iterators and Iterables（Corey Schafer，约 23 分钟，选看）", "url": "https://www.youtube.com/watch?v=jTYiNjvnHZY", "note": "迭代器协议的详细演示，包括自己写迭代器类"},
  {"title": "Python 文档：itertools — Functions creating iterators", "url": "https://docs.python.org/3/library/itertools.html", "note": "每个函数都有等价的纯 Python 实现，是学习迭代器的好材料，末尾的「Recipes」很实用"},
  {"title": "Python 文档：collections — Container datatypes", "url": "https://docs.python.org/3/library/collections.html", "note": "Counter、defaultdict、deque、namedtuple 的官方说明"},
  {"title": "Harvard CS50P：Introduction to Programming with Python（课程主页）", "url": "https://cs50.harvard.edu/python/", "note": "大学课程原版，列表、字典、循环、生成器的讲义和习题"},
 ],
 "quiz": {"questions": [
  Q("`[x for x in range(6) if x % 2 == 0]` 的结果是？",
    ["`[0, 2, 4]`", "`[1, 3, 5]`", "`[0, 1, 2, 3, 4, 5]`", "`[True, False, True, False, True, False]`"], 0,
    "末尾的 `if` 是过滤条件，只保留偶数；表达式部分是 `x` 本身。"),
  Q("`[v for row in [[1, 2], [3, 4]] for v in row]` 的结果是？",
    ["`[[1, 2], [3, 4]]`", "`[1, 3, 2, 4]`", "`[1, 2, 3, 4]`", "报错"], 2,
    "先写的 `for` 是外层循环：先取每一行，再遍历行里的每个值，结果是展平的列表。"),
  Q("下面哪一种说法**正确**描述了可迭代对象与迭代器？",
    ["列表是迭代器", "迭代器可以反复遍历很多次", "可迭代对象通过 `iter()` 得到迭代器，迭代器通过 `next()` 逐个给出元素，用完抛 `StopIteration`", "`for` 循环只能用于列表"], 2,
    "列表是可迭代对象（不是迭代器）；迭代器是一次性的。`for` 循环就是反复调用 `next()` 并在 `StopIteration` 时停止。"),
  Q("`z = zip([1, 2], 'ab')`，执行 `list(z)` 之后再执行 `list(z)`，第二次得到？",
    ["`[(1, 'a'), (2, 'b')]`", "空列表 `[]`", "报错", "`[(1, 'a')]`"], 1,
    "`zip` 返回的是迭代器，被第一次 `list` 消耗完了；要多次使用，先 `list()` 存起来。"),
  Q("调用一个含 `yield` 的函数 `g()` 时，会发生什么？",
    ["立即执行整个函数体并返回结果", "不执行函数体，返回一个生成器对象；之后每次 `next()` 才运行到下一个 `yield`", "报错，因为没有 `return`", "返回一个列表"], 1,
    "生成器函数调用后只创建生成器对象，函数体是被 `next()` 逐段驱动的。"),
  Q("`sum(x * x for x in range(10**7))` 相比 `sum([x * x for x in range(10**7)])`，主要优势是？",
    ["结果更精确", "不需要先把所有平方数放进内存，内存占用是常数级", "一定快一百倍", "可以重复使用"], 1,
    "生成器表达式是惰性的，一次只产生一个元素。计算量相同，但省去了构造大列表的内存开销。"),
  Q("生成器对象**不能**做的事是？",
    ["用 `for` 遍历", "传给 `sum`、`list`", "用 `len(g)` 求长度，或用 `g[0]` 按下标访问", "用 `next(g)` 取元素"], 2,
    "生成器是惰性的一次性迭代器，不知道总长度，也不支持下标。需要这些就先转成列表。"),
  Q("`itertools.groupby(data, key=...)` 使用时通常要先**排序**，原因是？",
    ["为了让它更快", "它只把**相邻的**相同键合并成一组，不相邻的相同键会被分成多组", "否则会报错", "它会自动去重"], 1,
    "groupby 一遍扫描，遇到键变化就结束一组。排序后相同键才会相邻。"),
  Q("`collections.Counter` 与 `defaultdict(list)` 各自最适合做什么？",
    ["Counter 排序、defaultdict 去重", "Counter 数每个元素出现的次数；defaultdict(list) 按键把元素分组收集", "两者完全等价", "Counter 做队列、defaultdict 做栈"], 1,
    "`Counter(words)` 直接得到频次；`groups[key].append(x)` 在键不存在时自动创建空列表。"),
  Q("要在遍历一个 50 GB 的文本文件时统计单词频次，下面哪种做法**最合适**？",
    ["`f.read().split()` 一次读入", "`for line in f` 逐行读取并更新 `Counter`", "先把整个文件读成列表再去重", "用递归读取"], 1,
    "文件对象本身是逐行读取的迭代器，内存只需要一行加上计数字典。`read()` 会一次读入全部 50 GB。"),
 ]},
}

TARGET = [3, 0, 2, 1, 0, 2, 1, 3, 2, 0]
for q, t in zip(unit["quiz"]["questions"], TARGET):
    q["options"][q["answer"]], q["options"][t] = q["options"][t], q["options"][q["answer"]]
    q["answer"] = t

if __name__ == '__main__':
    dump(unit, "py-0", "u02-comprehensions-iterators.json")
