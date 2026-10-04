"""py-0 第 2 节：推导式、迭代器、生成器"""
from unitlib import *
from y02c import C_COMP, C_ITER, C_GEN, C_ITT

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

### 推导式

> **标准定义 · 推导式 (comprehension)**
>
> **推导式**是用一个表达式**构造容器**的简洁语法：`[expr for x in iterable if cond]`（列表）、`{expr for ...}`（集合）、`{k: v for ...}`（字典）。它等价于「循环遍历 `iterable`，对满足 `cond` 的每个 `x` 计算 `expr`，并把结果收集起来」。多个 `for` 从左到右嵌套，**先写的是外层循环**。
>
> *English: A comprehension builds a list, set or dict from an iterable with an optional filter: [expr for x in iterable if cond]. Multiple for clauses nest left to right.*

**白话版：「流水线上的加工单」。** 一句话说清：「从这堆东西里，挑出符合条件的，每个按这个方式加工一下，装进一个新盒子。」比起写三四行 `for` + `append`，推导式把「做什么」写在一行里。

""" + C_COMP + r"""

几点说明：**一**，`[a if cond else b for x in xs]`（条件表达式）与 `[a for x in xs if cond]`（过滤）位置不同、作用不同：前者每个元素都产出一个值，后者会**丢掉**不满足条件的元素。**二**，嵌套推导式里，**写在前面的 `for` 是外层循环**：`[v for row in matrix for v in row]` 就是「先遍历每一行，再遍历这一行的每个值」。**三**，字典推导式 `{v: k ...}` 在值有重复时会丢信息（上面 `inverted` 里 `'Banana'` 与 `'cherry'` 的长度都是 6，只留下了最后一个）。**四**，推导式有自己的作用域，循环变量不会泄漏到外面。

**什么时候不该用？** 推导式适合「一个表达式、一个简单条件」。如果需要多个条件分支、嵌套三层、或者要产生副作用（比如打印），**写成普通的 `for` 循环**更清楚。「简洁」不等于「聪明」：可读性比一行内塞多少逻辑重要得多。
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

""" + C_ITER + r"""

要点：**迭代器是一次性的**：`list(it)` 第二次得到空列表，因为书签已经翻到底了；而列表本身每次 `iter()` 得到新的迭代器，可以反复遍历。`zip`、`map`、`filter`、`enumerate`、`reversed`、`range` 的结果以及**文件对象**都是惰性的，**不会一次把所有结果算出来**。最后一段里，`zip` 的结果被 `list` 消耗一次之后就空了，这是初学者最常见的坑之一：想用两次就先 `list()` 存起来。`zip` 遇到最短的序列就停（需要补齐时用 `itertools.zip_longest`）；`enumerate(x, start=1)` 从指定的数开始计数。

### 生成器：用函数写迭代器

> **标准定义 · 生成器 (generator)**
>
> 含有 `yield` 的函数称为**生成器函数 (generator function)**，调用它**不会执行函数体**，而是返回一个**生成器对象 (generator object)**，它是一种迭代器。每次 `next()`，函数体运行到下一个 `yield` 就**暂停并返回**该值，**保留所有局部变量的状态**，下次接着往下运行；函数结束时自动抛出 `StopIteration`。把推导式的 `[]` 换成 `()` 得到**生成器表达式 (generator expression)**，同样是惰性的。`yield from iterable` 把另一个可迭代对象的元素逐个转发出去。
>
> *English: A function containing yield is a generator function; calling it returns a generator (an iterator). Each next() resumes the body until the next yield, preserving local state. A generator expression uses parentheses and is lazy.*

**白话版：「会暂停的函数」。** 普通函数 `return` 之后就彻底结束了；生成器函数 `yield` 之后只是**暂停**，像看视频按了暂停键，下次按播放，从刚才停的地方继续。你想要下一个元素时它才工作，这就是**惰性求值**：**不要求的不算**。

""" + C_GEN + r"""

读输出：创建生成器时**什么都没打印**，函数体根本还没跑；每次 `next()` 才运行到下一个 `yield`，可以清楚看到「准备产出 0 → 返回给调用者 → 下一次 next 时才打印『0 已被取走』」的交替。

**为什么要用生成器？** **一，省内存**：一百万个平方数，列表占用 8 MB 以上，生成器表达式只占约 100 字节，因为它**一次只产生一个元素**，`sum` 边取边加。数据量大到装不进内存时（几十 GB 的语料、日志、数据集），这是唯一的办法。**二，能表示无限序列**：`fib()` 永不结束，用 `islice` 取前 12 个。**三，能搭流水线**：`non_empty(strip(read_lines()))` 每一步都只处理一个元素，**整个流程是流式的**。**四，批量产出**：`batches` 就是 `DataLoader` 的雏形。

**注意：** 生成器同样是**一次性**的，不能 `len()`，不能下标访问，不能重新开始（要重来就再调用一次生成器函数）。需要多次遍历或随机访问，就老实用列表。

### `itertools` 与 `collections`

标准库里这两个模块把常见的模式做成了现成的工具，面试题和数据处理里非常常用：

""" + C_ITT + r"""

**`itertools`**：`chain` 把几个序列接起来、`product` 笛卡尔积（遍历超参数网格 grid search 时用）、`combinations` / `permutations` 组合与排列、`accumulate` 前缀和、`islice` 对任何迭代器切片、`groupby` 分组（**只合并相邻的**相同键，所以通常要先 `sorted`：上面第一次分组 `'a'` 出现了两次，正是没排序的结果）。**`collections`**：`Counter` 数频次（`most_common`；没出现的键返回 0 而不是报错）、`defaultdict` 不存在的键自动创建默认值（省去 `if key not in d`）、`deque` 双端队列（两头操作 $O(1)$，加 `maxlen` 就成了「只保留最近 $n$ 个」的滑动窗口，数据结构那一门课的队列和 BFS 用它）、`namedtuple` 带字段名的轻量元组。

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

```python
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
