"""py-0 第 4 节：异常、调试、测试、日志与类型注解"""
from unitlib import *
from y04c import C_EXC, C_TB, C_TEST, C_LOG, C_TYPE

unit = {
 "id": "u04",
 "title": "异常、调试、测试与类型注解",
 "en": "Exceptions, Debugging, Testing & Type Hints",
 "minutes": 100,
 "objectives": [
  "会用 `try` / `except` / `else` / `finally` 处理 **异常 (exception)**，会 `raise`、写**自定义异常**、用 `raise ... from`，知道不能写「裸 except」",
  "会**读 traceback（从下往上）**，掌握系统的调试步骤：复现 → 缩小 → 假设 → 验证；会用 `assert`、`print` / `logging`、`breakpoint()` (**pdb**)",
  "会写**单元测试 (unit test)**：`unittest` 与 `pytest` 的基本写法、测边界情况与异常、浮点数比较，理解「测试能先于代码」的价值",
  "会用 **`logging`** 代替 `print` 记录运行信息，知道日志级别",
  "会写 **类型注解 (type hints)**，知道它在运行时**不会被强制检查**，是给人和工具（IDE、`mypy`）看的",
 ],
 "blocks": [
  T(r"""
### 先说这一节要干什么

写代码，出错是常态，不是例外。**专业与业余的区别，不是少出错，而是出错之后能快速找到原因、并且能让同样的错不再出现。** 这一节讲的是这套「工程素养」：怎么处理错误，怎么读报错，怎么定位 bug，怎么用测试把行为「固定」下来。

**学完它你就能看懂这几件事：**

- ML 代码里最常见的几种报错：`RuntimeError: shape mismatch`、`KeyError`（配置里缺字段）、`FileNotFoundError`（数据路径错了）、`CUDA out of memory`：知道是**什么类型的异常**、**在哪一行抛的**、**为什么**；
- 训练跑了 6 小时 loss 变成 `nan`：怎么用 `assert`、日志与断点排查；
- 研究代码库里的 `tests/` 文件夹、`logging.getLogger(__name__)`、`def f(x: torch.Tensor) -> torch.Tensor`：每一样都是这一节的内容；
- 面试里常被问到的「你怎么测试你的代码」「你怎么调试」。

**本节安排（约 100 分钟）**：异常处理与视频一（25 分钟）→ 读 traceback 与调试、视频二（20 分钟）→ 单元测试与视频三（30 分钟）→ 日志与类型注解（15 分钟）→ 总结与「想一想」（10 分钟）。

### 异常处理

> **标准定义 · 异常 (exception)**
>
> **异常**是程序运行中出现错误时，Python 创建并**抛出 (raise)** 的对象。如果没人处理，它会沿着**调用栈向外逐层传播**，直到程序终止并打印 traceback。`try` 块里放可能出错的代码；`except 异常类型 as e` 处理对应类型的异常（可以有多个，也能匹配子类）；`else` 在**没有**异常时执行；`finally` **无论如何**都执行，用于清理。`raise` 主动抛出异常；`raise NewError(...) from e` 在抛出新异常的同时保留**原因**。自定义异常通过继承 `Exception`（或它的子类）创建。
>
> *English: An exception is an object raised when an error occurs and propagates up the call stack until handled. try/except/else/finally handle it; raise throws one; raise ... from keeps the cause; custom exceptions subclass Exception.*

**白话版：「出了事故，先喊一声，谁能处理谁来接手」。** 函数 A 调函数 B，B 里出了事故，B 不处理，就向上喊给 A；A 也不处理，就喊给 A 的调用者……一直喊到有人 `except` 它，或者喊到最外面，程序停止。`finally` 像「不管事故发生没发生，离开房间前都要把灯关掉」。

""" + C_EXC + r"""

要点：**一**，输出里 `finally` 在每种情形下都会执行，哪怕 `try` 里已经 `return`（看 `f()`：先打印清理，再返回）。**二**，**异常是有继承关系的类**：`ZeroDivisionError` 是 `ArithmeticError` 的子类；`except ValueError` 也能抓住 `InvalidScore`，因此**具体的异常写前面，宽泛的写后面**。**三**，`raise ... from e` 保留了原始异常 `__cause__`，排查时能看到「根因」和「被包装后」两层信息。**四**，**不要写裸 `except:` 或笼统的 `except Exception: return None`**：最后一段里除零和类型错误得到同样的 `None`，真正的 bug 被吞掉了。**只抓你知道怎么处理的、范围尽量窄的异常**；处理不了就让它继续向上传。**五**，Python 推崇 **EAFP**（Easier to Ask Forgiveness than Permission，「先做，出错再处理」），例如直接 `d[key]` 并 `except KeyError`，而不是先检查再取（**LBYL**，Look Before You Leap）。但简单情况用 `d.get(key, default)` 更好。

**什么时候该让程序崩溃？** 一个常见的错误观念是「程序不能崩」。事实上，**让错误尽早、清楚地暴露**，比悄悄吞掉然后在下游产生错误结果要好得多：训练出一个静默地用了错误数据的模型，比训练一开始就报错糟糕得多。
"""),
  V("NIWwJbo-9_8", "视频一：Python Tutorial: Using Try/Except Blocks for Error Handling（Corey Schafer）", 11),
  T(r"""
### 读 traceback 与系统地调试

> **标准定义 · 回溯 (traceback) 与调试 (debugging)**
>
> **traceback** 是异常发生时 Python 打印的**调用栈快照**：从最外层的调用开始，一层层列到**抛出异常的那一行**，最后一行是**异常类型与信息**。**调试**是找出并修复错误原因的过程。
>
> *English: A traceback is the call-stack snapshot printed when an exception is raised: calls from the outermost to the line that raised, ending with the exception type and message. Debugging is the process of finding and fixing the cause of a bug.*

**白话版：「事故现场的路线图」。** 它告诉你：程序从哪里开始，经过哪些函数，在哪一行出的事，出了什么事。**读法：先看最后一行**（出了什么异常、说了什么），再**从下往上**看（最下面是出错的位置，往上是「谁调用了它」）。

""" + C_TB + r"""

读这个 traceback：最后一行 `KeyError: 'lr'` 说「字典里没有键 `lr`」；倒数第二行 `line 3, in load_config` 是出错的位置，代码是 `d["lr"] * 2`；再往上，`train` 在第 6 行调用了 `load_config`，整个脚本在第 8 行调用了 `train`。（上面的第一行 `<string>` 是我们用 `exec` 运行的外壳，平时不会出现。）**根因不一定在最后一行**：那里只是「事情暴露的地方」，真正的问题是「调用者传进来的配置里没有 `lr`」。

**系统地调试：**

1. **复现**：先找到一个**稳定触发**错误的最小输入。不能稳定复现，就先想办法让它稳定（固定随机种子、固定数据顺序）。
2. **缩小范围**：用**二分**的思想：在中间位置打印或断言，判断错误是在前半段还是后半段产生的，不断二分。
3. **提出假设，再验证**：不要随机改代码碰运气。先说出「我认为是因为 X」，然后设计一个实验验证它。
4. **修复后写一个测试**，让同样的错误以后不会悄悄回来。

**工具：** `print` 最快，但容易在代码里留下一堆；`assert condition, "message"` 在**假设被破坏时立即报错**，ML 里常用来检查张量形状（`assert x.shape == (batch, dim)`）和数值（`assert not torch.isnan(loss)`）；**`breakpoint()`** 在这一行暂停程序，进入交互式调试器 **pdb**：

```python
def f(x):
    y = x * 2
    breakpoint()        # 程序在这里停下，进入 (Pdb) 提示符
    return y + 1
```

在 `(Pdb)` 提示符下常用命令：`p 变量名`（打印）、`n`（执行下一行）、`s`（进入函数）、`c`（继续运行）、`l`（显示附近代码）、`q`（退出）。VS Code、PyCharm 等 IDE 也有图形化的断点调试，用法相同。**assert 只是调试用的**：用 `python -O` 运行会被忽略，所以**不要用它来检查用户输入**（那种情况应该 `raise ValueError`）。
"""),
  V("bHx8A8tbj2c", "视频二：Start Python Debugging With pdb（Real Python）", 4),
  T(r"""
### 单元测试

> **标准定义 · 单元测试 (unit test)**
>
> 针对程序里**一个小单元**（通常是一个函数或方法）的自动化检查：给定输入，断言输出等于预期。一组测试可以**一键运行**，每次修改代码后重新运行，确认没有破坏原有功能，这叫**回归测试 (regression testing)**。Python 标准库自带 `unittest`；第三方的 **`pytest`** 更简洁（直接写以 `test_` 开头的函数和 `assert`），是业界最常用的。好的测试覆盖：**典型输入**、**边界情况 (edge cases)**（空输入、单个元素、最大最小值）、**错误情况**（应当抛出异常）。
>
> *English: A unit test is an automated check of one small unit: for a given input, assert the expected output. Running the suite after every change catches regressions. unittest is in the standard library; pytest is the popular third-party framework. Good tests cover typical inputs, edge cases and error cases.*

**白话版：「给代码配一个自动验收员」。** 你写了一个函数，除了手动试几个输入，不如把「输入 → 期望输出」写成代码，让机器一次跑完。以后每次改动，点一下就知道有没有改坏。

""" + C_TEST + r"""

我们故意写了一个有 bug 的 `buggy_median`（偶数个元素时只取了后一个中间值），同一套 5 个测试：**有 bug 的版本失败 2 个**，其中 `test_even` 直接指出「得到 3，期望 2.5」，**测试把 bug 定位到了具体的用例**；正确的版本全部通过。最后一行提醒：**浮点数不要用 `==` 比较**（`0.1 + 0.2 == 0.3` 是 `False`），用 `assertAlmostEqual` 或者 `abs(a - b) < 1e-9`（pytest 里是 `pytest.approx`）。`assertRaises` 用来测「应该抛出异常」。

**同样的测试，用 `pytest` 写出来**（不需要写类，直接写函数和 `assert`；在终端里运行 `pytest` 即可）：

```python
# test_stats.py
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
```

**怎么想测试用例：** 典型值、**空输入**、**只有一个元素**、**重复元素**、**非常大 / 非常小的数**、**应该报错的输入**。**测试优先 (test-driven development, TDD)**：先写测试（它定义了「正确」是什么），再写代码让它通过。在 ML 里，测试同样有价值：测数据预处理函数的输入输出形状、测损失函数在已知输入上的值、测「一个 batch 能过拟合」（模型和训练循环是否正确的最小检验）。

**写测试 vs 手动试：** 手动试只能验证「现在」，测试保证「以后也对」。数据结构那一门课里，每一段代码我们都用「随机输入 + 与暴力解法对比」验证过，这就是一种测试方法（**基于性质的测试 property-based testing** 的雏形）。
"""),
  V("mzlH8lp4ISA", "视频三：getting started with pytest (beginner - intermediate)（anthonywritescode）", 13),
  T(r"""
### 日志 (logging)

> **标准定义 · 日志 (logging)**
>
> `logging` 模块用**分级的消息**记录程序运行情况。从低到高的五个**级别 (level)**：`DEBUG`（细节）、`INFO`（正常的进度）、`WARNING`（异常但可继续）、`ERROR`（出错了）、`CRITICAL`（严重故障）。设定一个级别后，**低于它的消息不会输出**。每个模块用 `logging.getLogger(__name__)` 得到自己的 logger；`log.exception(...)` 在 `except` 块里使用，会**自动附上完整的 traceback**。
>
> *English: The logging module records messages at levels DEBUG, INFO, WARNING, ERROR and CRITICAL; messages below the configured level are dropped. log.exception inside an except block includes the traceback.*

**白话版：「有开关的 print」。** `print` 要调试完一个个删掉；日志则是把所有信息按重要程度分级打出，**上线时调高级别，不改代码就能让调试信息消失**，还可以同时输出到文件、带上时间。

""" + C_LOG + r"""

`log.debug` 没有显示（级别低于 `INFO`）；`log.exception` 输出了 `ERROR` 和完整的 traceback；`log.setLevel(logging.ERROR)` 之后 `warning` 也被屏蔽了。**用 `%s` 占位符传参**（`log.info("lr=%s", lr)`）而不是 f-string：只有消息真的要输出时才会格式化，省去不必要的开销。**训练脚本里应该用日志记录超参数、每个 epoch 的 loss、保存模型的路径**：几天后回头看，你才知道「这个结果是怎么跑出来的」。

### 类型注解 (type hints)

> **标准定义 · 类型注解 (type hints / type annotations)**
>
> 在函数参数、返回值与变量后面标注**预期的类型**：`def f(x: int, y: list[float] = None) -> str:`。常用写法：`list[int]`、`dict[str, float]`、`tuple[int, ...]`、`Optional[int]`（等同于 `int | None`）、`Callable[[int], str]`、联合 `int | str`（Python 3.10+）。**注解在运行时不会被强制检查**，Python 解释器不管它；它的作用是给**读代码的人**、**IDE 的补全**和**静态检查工具（如 `mypy`、`pyright`）**看。
>
> *English: Type hints annotate expected types of parameters, return values and variables. They are not enforced at runtime; they serve readers, IDEs and static checkers such as mypy and pyright.*

**白话版：「给函数贴上说明标签」。** 标签写的是「这个槽请放整数」，但没有安检员拦着，你放一个字符串进去，Python 也照样运行（直到某一处真的出错）。**真正的安检员是 `mypy` 之类的工具，在你运行代码之前就能指出「这里类型对不上」。**

""" + C_TYPE + r"""

输出里 `mean.__annotations__` 显示注解只是保存在函数对象里；传入 `["a", "b"]` 时报的 `TypeError` 来自 `sum` 内部的加法，而**不是**因为注解被检查；`parse(3.9)` 不符合 `str | int`，却照常运行。**在 ML 代码里，类型注解（尤其是 `torch.Tensor`、`np.ndarray`）是最好的文档之一**：一眼看出函数要什么、返回什么。

### 这一节你要带走的三句话

1. **异常会沿调用栈向上传播**；只抓你知道怎么处理的、范围尽量窄的异常，**不要吞掉错误**；`finally` 做清理，`raise ... from` 保留原因。
2. **读 traceback：先看最后一行，再从下往上**；调试 = 复现、缩小、假设、验证；`assert`、日志和 `breakpoint()` 是三件基本工具。
3. **测试把「正确」写成代码**：测典型值、边界值、错误情况，浮点数不要用 `==`；修复 bug 之后补一个测试。日志代替 `print`，类型注解是写给人和工具看的。
"""),
  THINK("下面这段代码有什么问题？代码是：`try: model = load_model(path)`，`except Exception: model = None`，后面直接 `model.predict(x)`。", r"""
**问题：用笼统的 `except Exception` 吞掉了真正的错误，并把问题推迟到了后面。** 如果 `path` 写错了（`FileNotFoundError`）、文件损坏了、内存不足了，都会静默地变成 `model = None`，然后在 `model.predict(x)` 处抛出 `AttributeError: 'NoneType' object has no attribute 'predict'`：报错的位置和真正的原因相隔很远，你会花很长时间去查「为什么 model 是 None」。

更好的做法：**只抓能处理的具体异常**，并给出有用的信息；处理不了就让它向上抛：

```python
try:
    model = load_model(path)
except FileNotFoundError as e:
    raise SystemExit(f"找不到模型文件：{path}") from e
```

原则：**越早、越清楚地失败越好**（fail fast）。
"""),
  THINK("你为一个计算「验证集准确率」的函数写测试：`accuracy(preds, labels)`。除了「正常的几个例子」，你至少还会测哪几种情况？", r"""
至少这几类：

- **全对、全错**：准确率应该是 1.0 与 0.0，检查边界；
- **只有一个样本**：长度为 1 的输入；
- **空输入**：`preds` 和 `labels` 都是空列表，除以零！应该报错还是返回 0？这是**需要先决定的规格**，测试会迫使你想清楚；
- **长度不一致**：`preds` 与 `labels` 长度不同，应该抛出 `ValueError`，用 `assertRaises` 测；
- **类别不平衡的数据**：95% 都是类别 0，一个「全猜 0」的预测得到 0.95，函数没错，但这提醒你准确率不是好的指标（统计学里讲过）；
- **浮点比较**：用 `approx` 而不是 `==`。

测试本身就是一份「规格说明」：写的过程会暴露你对「这个函数应该做什么」的模糊之处。
"""),
  THINK("类型注解不会在运行时被检查，那为什么大家还要写？如果想在运行时真的检查类型，有什么办法？", r"""
价值在**别处**：**一，文档**：`def predict(x: np.ndarray, k: int = 5) -> list[int]` 一眼看出怎么用；**二，IDE 补全与导航**：知道 `x` 是什么类型，编辑器才能提示它有哪些方法；**三，静态检查**：`mypy` / `pyright` 在不运行代码的情况下发现类型不匹配，把一类 bug 提前到写代码时；**四，大型代码库的重构**更安全。

要在运行时检查，可以：手写 `isinstance` 检查，或者 `assert isinstance(x, int)`；也可以用第三方库，比如 **Pydantic**（根据类型注解校验并转换数据，FastAPI 与很多配置库都用它）、`beartype`、`typeguard`。ML 项目里的常见做法：**对外的边界（读配置、API 入口）用 Pydantic 校验，内部函数用注解 + `mypy` 静态检查。**
"""),
  KW(("异常","exception","运行时出错时抛出的对象，沿调用栈向外传播"),
     ("`try` / `except` / `else` / `finally`","try / except / else / finally","处理异常 / 无异常时执行 / 无论如何都执行"),
     ("`raise` / `raise ... from`","raise / raise from","主动抛出 / 抛出时保留原因"),
     ("自定义异常","custom exception","继承 `Exception` 创建的异常类"),
     ("EAFP / LBYL","EAFP / LBYL","先做、出错再处理 / 先检查再做"),
     ("回溯","traceback","异常发生时的调用栈快照；先看最后一行，再从下往上"),
     ("断言","assertion (`assert`)","假设被破坏时立即报错，用于调试，不用于检查用户输入"),
     ("断点 / pdb","breakpoint / pdb","`breakpoint()` 暂停程序并进入交互式调试器"),
     ("单元测试","unit test","对一个小单元的自动化检查；`unittest`、`pytest`"),
     ("回归测试","regression testing","修改代码后重跑测试，确认没有破坏原有功能"),
     ("边界情况","edge case","空输入、单元素、极值等容易出错的输入"),
     ("日志级别","log level","DEBUG < INFO < WARNING < ERROR < CRITICAL"),
     ("类型注解","type hints","标注预期类型；运行时不强制检查，供人与工具使用"),
     ("静态类型检查","static type checking","`mypy` / `pyright` 在运行前检查类型是否匹配"),
  ),
 ],
 "references": [
  {"title": "Python 官方教程：Errors and Exceptions", "url": "https://docs.python.org/3/tutorial/errors.html", "note": "语法错误与异常、`try` / `except` / `finally`、自定义异常、异常链的官方说明"},
  {"title": "Harvard CS50P：Exceptions 与 Unit Tests（课程主页）", "url": "https://cs50.harvard.edu/python/", "note": "大学课程原版，异常处理与 pytest 的讲义与习题"},
  {"title": "Python Tutorial: Type Hints（Corey Schafer，约 41 分钟，选看）", "url": "https://www.youtube.com/watch?v=RwH2UzC2rIo", "note": "从基本注解到泛型的完整讲解，需要写大型项目时再看"},
  {"title": "pytest 官方文档：Get Started", "url": "https://docs.pytest.org/en/stable/getting-started.html", "note": "安装、写第一个测试、断言与 fixtures 的入门"},
  {"title": "Python 文档：Logging HOWTO", "url": "https://docs.python.org/3/howto/logging.html", "note": "基础与进阶两部分，含 logger、handler、formatter 的概念"},
 ],
 "quiz": {"questions": [
  Q("`try / except / else / finally` 里，`finally` 块什么时候执行？",
    ["只有发生异常时", "只有没发生异常时", "无论是否发生异常、是否 `return`，都会执行", "只在最后一次循环"], 2,
    "`finally` 用于清理工作，保证一定会执行（除非进程被强制终止）。`else` 才是「没有异常时执行」。"),
  Q("为什么 `except Exception: return None` 这种写法通常是**坏习惯**？",
    ["因为它会让程序崩溃", "因为它把不同种类的错误（包括你的 bug）都吞掉了，问题会在更远的地方以更难懂的方式暴露", "因为 Python 不允许", "因为它运行很慢"], 1,
    "原则：只抓你知道怎么处理的具体异常；让其余的错误尽早、清楚地暴露（fail fast）。"),
  Q("`ZeroDivisionError` 是 `ArithmeticError` 的子类。`except ArithmeticError:` 能抓住 `ZeroDivisionError` 吗？",
    ["不能", "能，`except` 会匹配指定类型及其子类", "只能抓住 `KeyError`", "取决于 Python 版本"], 1,
    "异常是有继承关系的类，所以应当把具体的异常写在前面、宽泛的写在后面。"),
  Q("读 traceback 的正确方法是？",
    ["只看第一行", "先看最后一行（异常类型与信息），再从下往上看（最下面是出错的位置，往上是调用链）", "忽略它，直接重写代码", "只看中间一行"], 1,
    "最后一行说明出了什么错，倒数第二行指出出错的位置，再往上是「谁调用了它」。根因不一定在最后一行。"),
  Q("下面哪项**不是**系统调试的合理步骤？",
    ["找到稳定复现错误的最小输入", "用二分的思想缩小出错的范围", "提出假设再设计实验验证", "随机改动代码，看哪次能运行就保留哪次"], 3,
    "随机改动是碰运气，而且可能在不理解原因的情况下掩盖问题。应先提出假设并验证。"),
  Q("下面哪种情况**不应该**用 `assert` 来检查？",
    ["检查一个内部函数收到的张量形状是否符合预期", "检查训练中 loss 不是 `nan`", "检查用户从命令行传入的参数是否合法", "检查「这里不应该到达」的分支"], 2,
    "`python -O` 会忽略 `assert`，所以不要用它检查外部输入；应该 `raise ValueError` 等异常。"),
  Q("测试一个浮点数计算的结果，推荐的做法是？",
    ["`assert result == 0.3`", "用 `assertAlmostEqual` / `pytest.approx` / 容差比较", "把结果转成字符串再比较", "不需要测试浮点数"], 1,
    "`0.1 + 0.2 == 0.3` 是 `False`，浮点数有舍入误差，应当在容差范围内比较。"),
  Q("为一个 `median(xs)` 函数写测试，下面哪组**最能**暴露潜在 bug？",
    ["只测 `[1, 2, 3]`", "测奇数个、偶数个、单个元素、空列表、有重复元素的输入", "只测很大的列表", "只测已排序的输入"], 1,
    "典型值 + 边界情况 + 错误情况。偶数个元素和空列表是最容易出错的边界。"),
  Q("`logging` 里，设置级别为 `INFO` 后，哪些消息会输出？",
    ["只有 `INFO`", "`DEBUG` 及以上所有", "`INFO`、`WARNING`、`ERROR`、`CRITICAL`", "只有 `ERROR`"], 2,
    "低于设定级别的消息（这里是 `DEBUG`）被丢弃，设定级别及以上的都会输出。"),
  Q("关于 Python 的类型注解，下面说法**正确**的是？",
    ["传错类型时 Python 会自动抛出 `TypeError`", "注解运行时不强制检查，主要供阅读者、IDE 与 `mypy` 等工具使用", "加了注解程序会变快", "没有注解的代码无法运行"], 1,
    "注解只是保存在 `__annotations__` 里的信息。要在运行前发现类型问题，用 `mypy` / `pyright`；要在运行时校验，用 Pydantic 等库。"),
 ]},
}

TARGET = [1, 2, 0, 3, 1, 0, 3, 2, 1, 0]
for q, t in zip(unit["quiz"]["questions"], TARGET):
    q["options"][q["answer"]], q["options"][t] = q["options"][t], q["options"][q["answer"]]
    q["answer"] = t

if __name__ == '__main__':
    dump(unit, "py-0", "u04-exceptions-testing.json")
