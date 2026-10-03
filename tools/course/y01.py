"""py-0 第 1 节：函数与递归"""
from unitlib import *

unit = {
 "id": "u01",
 "title": "函数与递归",
 "en": "Functions & Recursion",
 "minutes": 45,
 "objectives": [
  "会定义和调用 **函数 (function)**，分清 **参数 (parameter)**、**返回值 (return value)** 和 **作用域 (scope)**",
  "知道可变默认参数的陷阱，并会正确写默认参数",
  "理解 **递归 (recursion)** 的两个要素：**基础情形 (base case)** 和 **递归情形 (recursive case)**，会画调用栈",
  "知道朴素递归为什么会变慢，会用 `functools.lru_cache` 加记忆化",
 ],
 "blocks": [
  T(r"""
### 为什么先学这个

NUS 的 IT5001（Software Development Fundamentals）和 Harvard 的 CS50P 都把**函数和递归**放在最前面，因为后面所有内容都建立在它们上面：

- 数据结构与算法那门课里，树、图、分治、动态规划几乎全是递归；
- 写 ML 代码时，你写的每个训练步骤、每个模块，本质上都是函数；
- 你成绩单上的 Introduction to Programming 是 B，这一节用来检查「函数和递归」是不是真的扎实。

**本节安排（约 45 分钟）**：导读 → 函数要点与陷阱（10 分钟）→ 视频一（14 分钟）→ 递归要点与代码（10 分钟）→ 视频二（6 分钟）→「想一想」（5 分钟）。

> 如果函数这部分你已经很熟，直接跳到「递归」。
"""),
  T(r"""
### 函数：几个要抓牢的点

```python
def area(width, height=1):
    # 返回矩形面积，height 有默认值
    return width * height

print(area(3, 4), area(5), area(height=2, width=3))
# 12 5 6
```

- **参数 (parameter)** 是定义时写的名字，**实参 (argument)** 是调用时传的值；
- 没有 `return` 的函数会返回 `None`；
- 函数里**赋值**的变量是**局部变量**，不会改外面同名的变量（**作用域 (scope)**）：

```python
x = 10
def g():
    x = 5          # 这是局部的 x，和外面的 x 无关
    return x
print(g(), x)
# 5 10
```

**⚠️ 最著名的陷阱：可变默认参数 (mutable default argument)**

默认值是在**定义函数的那一刻**只创建一次的。如果默认值是列表、字典，所有调用会**共用同一个对象**：

```python
def f(x, l=[]):
    l.append(x)
    return l

print(f(1), f(2), f(3))
# [1, 2, 3] [1, 2, 3] [1, 2, 3]
```

三个结果都是同一个列表，而且是三次调用结束后才打印，所以都显示成 `[1, 2, 3]`。正确写法是用 `None` 当默认值：

```python
def f2(x, l=None):
    if l is None:
        l = []
    l.append(x)
    return l

print(f2(1), f2(2))
# [1] [2]
```
"""),
  V("mz6tAJMVmfM", "视频一：Recursion - CS50 Shorts（Harvard CS50）", 14),
  T(r"""
### 递归：自己调用自己

**递归 (recursion)** 就是函数在内部调用自己。一个正确的递归必须有两部分：

1. **基础情形 (base case)**：问题小到能直接回答，不再调用自己；
2. **递归情形 (recursive case)**：把问题缩小一点，交给自己处理，再用结果拼出答案。

经典例子，阶乘 $n!=n\times(n-1)!$，而 $0!=1$：

```python
def fact(n):
    if n <= 1:               # 基础情形
        return 1
    return n * fact(n - 1)   # 递归情形：问题规模减 1

print(fact(5), fact(20))
# 120 2432902008176640000
```

**调用栈 (call stack)**：`fact(3)` 被调用时，Python 会为每次调用留一个「栈帧」：

```
fact(3) 等着 3 * fact(2)
  fact(2) 等着 2 * fact(1)
    fact(1) 直接返回 1         ← 基础情形
  fact(2) 得到 1，返回 2
fact(3) 得到 2，返回 6
```

**两个常见问题**

**1. 没有基础情形，或者永远走不到它**，会无限调用下去。Python 有递归深度上限，超过就报 `RecursionError`：

```python
import sys
print(sys.getrecursionlimit())
# 1000

def bad(n):
    return bad(n + 1)       # 永远没有基础情形

try:
    bad(0)
except RecursionError as e:
    print("RecursionError", str(e)[:35])
# RecursionError maximum recursion depth exceeded
```

**2. 重复计算**。斐波那契数列 $F(n)=F(n-1)+F(n-2)$，朴素递归会把同一个子问题算很多遍。数一下调用次数：

```python
calls = 0
def fib(n):
    global calls
    calls += 1
    return n if n < 2 else fib(n - 1) + fib(n - 2)

for n in (10, 20, 25):
    calls = 0
    print(n, fib(n), calls)
# 10 55 177
# 20 6765 21891
# 25 75025 242785
```

$n$ 每加 5，调用次数大约变成原来的 11 倍，近似**指数级增长**（约 $O(1.6^n)$，粗略也可以说 $O(2^n)$）。解决办法叫**记忆化 (memoization)**：算过的结果存起来，下次直接用。Python 一行就能做到：

```python
from functools import lru_cache

calls = 0
@lru_cache(maxsize=None)
def fib_memo(n):
    global calls
    calls += 1
    return n if n < 2 else fib_memo(n - 1) + fib_memo(n - 2)

print(fib_memo(25), calls)
# 75025 26
print(fib_memo(90))
# 2880067194370816120
```

同样算 `fib(25)`，调用次数从 242785 次降到 **26 次**，复杂度从指数变成 $O(n)$。而且朴素递归算 `fib(90)` 需要约 $10^{18}$ 量级的调用，实际上算不完，记忆化后瞬间就能得到结果。

> 递归的写法三步：① 先写基础情形；② 假设「更小的问题已经被我的函数正确解决了」；③ 用它的结果拼出当前答案。**不要试图在脑子里把整个调用栈展开。**
"""),
  V("ivl5-snqul8", "视频二：Learn RECURSION in 5 minutes!（Bro Code）", 6),
  THINK("不用 `**`，用递归写一个 `power(x, n)` 计算 $x^n$（$n\\ge0$ 的整数）。再想想怎样把复杂度从 $O(n)$ 降到 $O(\\log n)$？", r"""
直接写法 $O(n)$：`power(x, 0)` 返回 1，否则 `x * power(x, n-1)`。

**快速幂 (fast exponentiation)** $O(\log n)$：每次把指数减半。

```python
def power(x, n):
    if n == 0:
        return 1
    half = power(x, n // 2)
    return half * half if n % 2 == 0 else half * half * x

print(power(2, 10), power(3, 13), 3 ** 13)
# 1024 1594323 1594323
```

原理是 $x^n=(x^{n/2})^2$（$n$ 为偶数）或 $x\cdot(x^{(n-1)/2})^2$（$n$ 为奇数）。每次递归指数都减半，所以深度只有 $\log_2 n$。
"""),
  THINK("写一个递归函数 `sum_digits(n)`，返回非负整数各位数字之和，比如 `sum_digits(9875)` 是 29。基础情形和递归情形各是什么？", r"""
基础情形：$n<10$ 时，它自己就是各位和，直接返回 $n$。递归情形：最后一位是 `n % 10`，剩下的数是 `n // 10`，各位和就是 `n % 10 + sum_digits(n // 10)`。

```python
def sum_digits(n):
    return n if n < 10 else n % 10 + sum_digits(n // 10)

print(sum_digits(9875))
# 29
```
"""),
  THINK("写一个递归函数 `flatten(x)`，把任意深度嵌套的列表展平，比如 `[1, [2, [3, [4]], 5]]` 变成 `[1, 2, 3, 4, 5]`。为什么这个问题用递归比用循环更自然？", r"""
```python
def flatten(x):
    out = []
    for item in x:
        if isinstance(item, list):
            out += flatten(item)     # 递归情形：元素本身是列表
        else:
            out.append(item)         # 基础情形：元素不是列表
    return out

print(flatten([1, [2, [3, [4]], 5]]))
# [1, 2, 3, 4, 5]
```

嵌套深度是不确定的，**数据本身的结构就是递归的**（列表里面可以再放列表），用递归写出来和数据长得一样，比用循环加手动维护栈简单得多。后面的树和图也是同样的道理。
"""),
  KW(("函数","function","封装一段可复用的代码，用 `def` 定义"),
     ("参数 / 实参","parameter / argument","定义时的名字 / 调用时传入的值"),
     ("返回值","return value","`return` 后面的值；没有 `return` 就返回 `None`"),
     ("作用域","scope","变量在哪里能被看到；函数内赋值的变量是局部的"),
     ("默认参数","default argument","调用时没传就用默认值；默认值只在定义时创建一次"),
     ("递归","recursion","函数调用自己来解决规模更小的同类问题"),
     ("基础情形","base case","小到可以直接回答的情形，递归在这里停下"),
     ("调用栈","call stack","记录「谁在等谁」的栈，每次调用占一个栈帧"),
     ("递归深度","recursion depth","同时在等待的调用层数，Python 默认上限 1000"),
     ("记忆化","memoization","把算过的结果存起来，避免重复计算"),
     ("指数增长","exponential growth","每增加 1，步数就乘一个固定倍数；朴素斐波那契约乘 1.6"),
  ),
 ],
 "references": [
  {"title": "Think Python 3e（Downey）— 第 3 章 Functions", "url": "https://allendowney.github.io/ThinkPython/chap03.html", "note": "本节大纲依据之一，CC BY-NC-SA 4.0，带 Colab 可运行笔记本"},
  {"title": "Think Python 3e（Downey）— 第 5 章 Conditionals and Recursion", "url": "https://allendowney.github.io/ThinkPython/chap05.html", "note": "递归的基础讲解和练习"},
  {"title": "Harvard CS50P：Introduction to Programming with Python（课程主页）", "url": "https://cs50.harvard.edu/python/", "note": "大学课程原版，函数、异常、测试等都有视频和习题"},
  {"title": "Runestone：What Is Recursion?（Miller & Ranum）", "url": "https://runestone.academy/ns/books/published/pythonds/Recursion/WhatisRecursion.html", "note": "递归的三条法则，和后面数据结构一章衔接"},
  {"title": "Python 文档：functools.lru_cache", "url": "https://docs.python.org/3/library/functools.html", "note": "记忆化装饰器的官方说明"},
 ],
 "quiz": {"questions": [
  Q("下面代码打印什么？\n\n```python\nx = 10\ndef g():\n    x = 5\n    return x\nprint(g(), x)\n```",
    ["5 5", "10 10", "5 10", "10 5"], 2,
    "函数里的 `x = 5` 创建的是局部变量，不会改外面的 `x`。所以 `g()` 返回 5，外面的 `x` 仍是 10。"),
  Q("函数没有写 `return` 语句时，调用它会得到什么？",
    ["`0`", "`None`", "空字符串", "报错"], 1,
    "没有 `return`（或只写 `return`），函数返回 `None`。常见错误是把一个只打印、不返回的函数的结果当成数值用。"),
  Q("下面代码最后打印什么？\n\n```python\ndef f(x, l=[]):\n    l.append(x)\n    return l\nf(1)\nprint(f(2))\n```",
    ["`[2]`", "`[1]`", "`[2, 1]`", "`[1, 2]`"], 3,
    "默认参数 `l=[]` 只在定义函数时创建一次，每次调用都共用同一个列表。第一次调用往里放了 1，第二次又放了 2，所以是 `[1, 2]`。正确写法用 `None` 当默认值。"),
  Q("一个正确的递归函数必须具备什么？",
    ["一个基础情形，和一个会把问题规模缩小的递归情形", "必须使用循环", "至少调用自己两次", "必须返回列表"], 0,
    "基础情形让递归能停下来，递归情形必须让问题越来越小，向基础情形靠近。少了任何一个，要么无限递归，要么答案不对。"),
  Q("`fact(4)` 用上面的递归定义，一共会发生几次对 `fact` 的调用（包括最外层这次）？",
    ["3", "4", "5", "24"], 1,
    "调用链是 `fact(4)→fact(3)→fact(2)→fact(1)`，共 4 次，`fact(1)` 是基础情形。24 是 `fact(4)` 的结果，不是调用次数。"),
  Q("下面这个函数运行时会怎样？\n\n```python\ndef f(n):\n    return f(n - 1)\n```",
    ["返回 0", "返回 `None`", "递归深度超过上限，抛出 `RecursionError`", "无限运行，永远不会报错"], 2,
    "没有基础情形，调用一层套一层，超过 Python 的递归深度上限（默认 1000）后抛出 `RecursionError`。所以 Python 里递归「不会无限运行」，而是会因栈溢出而报错。"),
  Q("朴素的递归斐波那契 `fib(n)` 为什么很慢？",
    ["Python 的递归本身很慢", "它使用了全局变量", "它没有基础情形", "同一个子问题会被重复计算很多次，调用次数近似指数增长"], 3,
    "`fib(25)` 实测要 242785 次调用，而真正不同的子问题只有 26 个。大部分时间花在重复算同样的东西上。"),
  Q("给上面的斐波那契加上 `@lru_cache(maxsize=None)` 后，`fib_memo(25)` 的调用次数变成了多少？",
    ["242785", "约 50000", "26", "25 的平方 625"], 2,
    "每个 $n$ 从 0 到 25 只会真正计算一次，共 26 次，所以复杂度从指数变成了 $O(n)$。这就是记忆化的威力。"),
  Q("`sum_digits(n) = n if n < 10 else n % 10 + sum_digits(n // 10)`，则 `sum_digits(305)` 是多少？",
    ["8", "35", "305", "5"], 0,
    "`305 % 10 = 5`，`305 // 10 = 30`；`30 % 10 = 0`，`30 // 10 = 3`；`3 < 10` 返回 3。总和 5+0+3=8。"),
  Q("下面哪种情形最适合用递归来写？",
    ["遍历一个任意深度嵌套的列表，把里面所有数字取出来", "把 1 到 100 加起来", "打印 5 次 hello", "计算两个数的和"], 0,
    "嵌套深度不确定，数据结构本身就是递归的（列表里再套列表），用递归写出来最自然。前三个用一个简单循环就够了。"),
 ]},
}

if __name__ == '__main__':
    dump(unit, "py-0", "u01-functions-recursion.json")
