"""ARENA 0.0 第 12 节：开发工具（按 v3 格式重写，2026-10-04）"""
from unitlib import *
from a12c import C_SHELL, C_CELL, C_NB, C_PDB, C_TYPES, C_PYTEST, C_GIT, C_VENV
from a12_quiz import QUIZ

unit = {
 "id": "u12",
 "title": "开发工具：VS Code、Jupyter、Git、Conda",
 "en": "Developer Tools",
 "minutes": 95,
 "objectives": [
  "知道 ARENA 推荐 **VS Code** 的原因：快捷键、`# %%` **代码单元 (cell)**、**调试器 (debugger)** 与 **断点 (breakpoint)**、**类型提示 (type hints)**，并能用调试器查看张量的形状",
  "分清 **Jupyter / Colab** 与 `.py` 文件各自适合做什么，理解 notebook 的**隐藏状态 (hidden state)** 问题",
  "掌握 **Git** 的三个区域（工作区、暂存区、仓库）与日常操作：`add`、`commit`、`switch -c`、`restore`、`stash`、`push`，分清 `commit` 与 `push`",
  "理解为什么要用 **虚拟环境 (virtual environment)**（`conda` / `venv`），会创建、激活、记录依赖，知道「装的环境和运行的环境不是同一个」是最常见的 `ModuleNotFoundError` 原因",
  "会用常见 **Unix 命令** 与 **管道 (pipe)**、**重定向 (redirection)**，并能用 **pytest** 给函数写最小的测试",
 ],
 "blocks": [
  T(r"""
### 先说这一节要干什么

ARENA 把 **VS Code** 和 **Jupyter / Colab** 标为高优先级，**Git** 和 **Conda** 标为中优先级，Unix 命令是加分项。这些工具本身不难，但在 ARENA 里（以及读 master 之后的所有课程项目）会不停地用到：不会用调试器，只能到处加 `print`；不会管理环境，一个 `pip install` 可能把另一个项目弄坏；不会 Git，没法回退、更没法和别人协作。这一节是**动手型**的：下面每个工具，我们都用真实运行的代码演示它到底做了什么，而不是只列命令。

**学完它你就能看懂这几件事：**

- 为什么你的代码「在我这能跑，在你那报 `ModuleNotFoundError`」，以及怎么用虚拟环境和依赖清单避免；
- notebook 里「从上到下重新运行」和「你手点的顺序」为什么能得出不同的结果；
- ARENA 的练习为什么配有测试函数，以及 `pytest` 的输出怎么读；
- 为什么 `git commit` 不等于「上传」，改坏了怎么回到干净状态，想保留改动先去做别的事怎么办。

**本节安排（约 95 分钟）**：导读与 Unix 命令（12 分钟）→ VS Code：视频一（15 分钟）与快捷键、`# %%`、调试器、类型提示（15 分钟）→ Jupyter / Colab（8 分钟）→ Git：视频二（2 分钟）与动手（15 分钟）→ 虚拟环境：视频三（9 分钟）与动手（10 分钟）→ pytest（5 分钟）→「想一想」。**强烈建议打开电脑跟着敲**，课后可以做 15 分钟的 Learn Git Branching 交互练习。命令行部分在 Windows 上可以用 Git Bash 或 WSL，Mac / Linux 直接用终端。

### 命令行：Unix 命令、管道与重定向

远程 GPU 服务器几乎都是 Linux，没有图形界面，所以命令行迟早要用。

> **标准定义 · 命令行与管道 (shell, pipe, redirection)**
>
> **Shell**（如 bash、zsh）是读入你输入的命令、调用对应程序的**命令解释器**。每个程序有**标准输入 (stdin)** 和**标准输出 (stdout)**。**管道** `A | B` 把 A 的标准输出直接接到 B 的标准输入；**重定向** `> 文件` 把输出写入文件（覆盖），`>> 文件` 追加。每个命令结束时返回一个**退出码 (exit code)**：0 表示成功，非 0 表示失败，shell 里读取特殊变量 `?` 就能得到它。
>
> *English: A shell interprets typed commands and runs programs. Each program has stdin and stdout; A | B pipes A's output into B; > writes output to a file (>> appends). Every command returns an exit code: 0 for success, non-zero for failure, readable through the special shell variable ?.*

**白话版：「流水线上的小工具」。** 每个命令只做一件小事（列文件、过滤、数行数、排序），管道把它们一个接一个连成流水线，上一个的产出就是下一个的原料。

""" + C_SHELL + r"""

读输出：`ls data | grep py` 先列出三个文件，再只保留名字里含 `py` 的两个（`a.py`、`train_cnn.py`）；再接 `wc -l` 就数出 2。`>` 创建并写入日志、`>>` 在后面追加第二行，`cat` 打印出两行。`grep 'epoch 2' ... | cut -d' ' -f4` 找到第二行，再用空格切分取第 4 列，得到 `0.5`：这就是「从训练日志里提取某个数」的典型写法。`grep -q nothing ...` 没找到内容，退出码是 1（非 0 = 失败），脚本和 CI 都靠它判断命令是否成功。常用命令还有：`pwd`（当前目录）、`cd 目录` / `cd ..`、`cp` / `mv` / `rm`（复制 / 移动或改名 / **永久**删除）、`cat`、`head` / `tail`。小心 `rm`：命令行里删除通常没有回收站。
"""),
  V("f8_uF_IDV50", "视频一：Learn Visual Studio Code in 15 minutes（VS Code 官方）", 15),
  T(r"""
### VS Code：快捷键、代码单元、调试器、类型提示

ARENA 建议用 VS Code 做结构化练习，而不是只用 Jupyter。主要理由有四个。

**1. 快捷键**（Windows / Linux 用 Ctrl，Mac 把 Ctrl 换成 Cmd、Alt 换成 Opt）

| 功能 | 快捷键 |
|---|---|
| 命令面板 (Command Palette) | Ctrl + Shift + P |
| 快速打开文件 | Ctrl + P |
| 全局搜索 | Ctrl + Shift + F |
| 选中下一个相同的词（多光标） | Ctrl + D |
| 注释 / 取消注释当前行 | Ctrl + / |
| 删除当前行 | Ctrl + Shift + K |
| 向上 / 向下复制当前行 | Shift + Alt + ↑ / ↓ |
| 显示 / 隐藏侧边栏 | Ctrl + B |
| 触发代码补全 | Ctrl + Space |

**2. `# %%` 代码单元**

> **标准定义 · 代码单元 (cell)**
>
> 在 `.py` 文件里，一行以 `# %%` 开头的注释把文件分成若干**单元**，VS Code 的 Python 扩展可以**单独运行**某个单元，并把输出显示在旁边的交互窗口；对 Python 解释器来说，`# %%` 只是普通注释，所以整个文件仍然是一个可以 `python 文件名.py` 运行、也可以被 `import` 的普通脚本。
>
> *English: In a .py file, a comment line starting with # %% marks the start of a cell that VS Code can run on its own in an interactive window; to the interpreter it is just a comment, so the file remains a normal script that can be run or imported.*

**白话版：「一个文件，两种用法」。** 想边试边看，就像 notebook 一样一块块运行；想交付、复用、写测试，它就是一份普通代码。

""" + C_CELL + r"""

读输出：整个文件当脚本运行，输出 `sum of squares = 30`（$1+4+9+16=30$）；在 VS Code 里则可以只运行「单元 2」看 `total`。对比 notebook，这种写法能被 `import`、能写测试、能被 Git 清晰地比较（`.ipynb` 里夹着输出和元数据，改动很难读）。

**3. 调试器 (debugger)**

> **标准定义 · 断点与调试器 (breakpoint & debugger)**
>
> **断点**是你在某一行设下的暂停标记；用调试器运行程序时，执行到该行就**暂停**，此时可以查看所有变量的值（包括张量的 `.shape`、`.dtype`）、逐行执行、查看调用栈。VS Code 里在行号左边点一下设断点，按 F5 开始调试；命令行里 Python 自带的调试器是 `pdb`（`python -m pdb 文件名.py`，或在代码里写 `breakpoint()`）。
>
> *English: A breakpoint pauses execution at a chosen line so you can inspect variables (including tensor shapes), step through code and see the call stack. VS Code provides a graphical debugger; in the terminal Python ships with pdb.*

**白话版：「按下暂停键看现场」。** 比起到处插 `print`、改完再重跑，调试器让你在出事的那一刻停住，随便问：「这个变量现在是多少？」

下面用 `pdb` 的命令行版演示（VS Code 的图形界面做的是同一件事）：一个「把每列减去均值」的函数，轴写错了：

""" + C_PDB + r"""

读输出：直接运行，报 `ValueError: operands could not be broadcast together with shapes (2,3) (2,)`，说 `(2,3)` 和 `(2,)` 对不上。这条信息提示了问题，但没说是哪两个变量。用调试器在第 5 行（`return x - mean`）设断点（`b 5`）、继续运行（`c`）到那里暂停（`> ./buggy.py(5)center()`），再用 `p` 打印两个变量的形状：`x` 是 `(2, 3)`，`mean` 是 `(2,)`。一眼就看出来了：`axis=1` 是对每一**行**求平均，得到 2 个数；想减去每列均值应该是 `axis=0`，得到 3 个数、`(3,)` 能广播到 `(2, 3)`。这种「暂停、看形状」的方法，下一节广播和后面 Transformer 的形状 bug 里会反复用到。

**4. 类型提示与类型检查**

> **标准定义 · 类型提示 (type hints)**
>
> 在函数参数和返回值后面写上期望的类型（`def f(x: float, k: int) -> float`），称为**类型提示**。Python 运行时**不检查**它们，它们是给读代码的人和**静态类型检查器**（如 mypy、VS Code 的 Pylance）看的：检查器在**不运行代码**的情况下，就能指出类型对不上的调用。
>
> *English: Type hints annotate expected types of parameters and return values. Python does not enforce them at runtime; static checkers such as mypy or Pylance use them to flag mismatches without running the code.*

**白话版：「写在药瓶上的用法说明」。** 说明书不会阻止你吃错药，但会让药剂师（检查器）在你吃之前发现问题。

""" + C_TYPES + r"""

读输出：`get_type_hints` 读出的就是我们写的标注；`scale(2.0, 3)` 得 6.0；而 `scale("ab", 3)` 违反了标注（`x` 应该是 `float`），Python 却照样运行，因为字符串乘整数是合法的，得到 `ababab`。只有开了类型检查（在 VS Code 的 `settings.json` 里设 `"python.analysis.typeCheckingMode": "basic"`，或命令行运行 mypy）才会在运行之前把它标出来。**这里的 mypy 提示没有实际运行**，因为它不是标准库；你装好 mypy 后对这个文件运行 `mypy 文件名.py` 可以自己验证。ARENA 的练习函数大多带类型提示，读标注就能知道每个参数该传什么形状和类型。

VS Code 其他常用功能：内置测试面板（配合 `pytest`）、通过 SSH 在远程 GPU 机器上写代码、Copilot 等 AI 辅助。

### Jupyter Notebook 与 Colab

- **Jupyter**：适合**探索和可视化**，边试边看图。缺点是容易堆出几百个单元，代码难复用。
- **Google Colab**：在线版 Jupyter，**免费提供 GPU**。自学 ARENA、手边没有 GPU 的话，Colab 是最好的选择；本课程每一节的动手练习都可以在 Colab 里做。

notebook 最大的陷阱是**隐藏状态**：所有单元共用同一个内核的变量，而你可以按**任意顺序**运行单元，屏幕上从上到下的代码，未必就是产生当前结果的顺序。

""" + C_NB + r"""

读输出：从上到下运行，`loss` 是 $10\times0.1=1.0$（因为 `lr` 在 `loss` 之后才被改成 0.01）；但如果你实际点击的顺序是 A、C、B（先改了 `lr` 再算 `loss`），`loss` 就是 $10\times0.01=0.1$，差了 10 倍。别人读你的 notebook，看到的是前一种，你的结果却来自后一种。**对策：交付前用「重启内核并全部运行 (Restart & Run All)」跑一遍**，结果一致才算数；要复用的代码写进 `.py` 文件。
"""),
  V("hwP7WQkmECE", "视频二：Git Explained in 100 Seconds（Fireship）", 2),
  T(r"""
### Git：给文件夹加上「存档」功能

> **标准定义 · Git 与它的三个区域**
>
> **Git** 是**版本控制 (version control)** 系统：记录项目文件的每一次**提交 (commit)**（一次带说明的完整快照），可以回到任意历史版本，并支持多条**分支 (branch)** 并行开发。本地有三个区域：**工作区 (working tree)**（你正在编辑的文件）、**暂存区 (staging area / index)**（`git add` 选出的、准备放进下次提交的改动）、**仓库 (repository)**（已经提交的历史）。**远程仓库 (remote)**（如 GitHub 上的那份）通过 `push` 上传、`pull` / `clone` 下载。
>
> *English: Git is a version control system that records snapshots (commits) of a project and supports parallel branches. Changes flow from the working tree, through the staging area (git add), into the repository (git commit); a remote such as GitHub is synchronised with push and pull/clone.*

**白话版：「游戏存档」。** 工作区是你正在玩的进度；`add` 是挑选哪些进度要存；`commit` 是真的存一个档并写备注；分支是「存档的平行宇宙」，在里面随便冒险，不影响主线；`push` 是把存档上传到云端。**`commit` 只是本地存档，没有网络也能做；不 `push`，GitHub 上什么都看不到。**

下面用一个本地「假 GitHub」（一个临时的裸仓库）把整个流程真实走一遍，包括改坏了怎么回退：

""" + C_GIT + r"""

读输出，逐步看：**一**，`git add` 之后 `git status --short` 显示 `A  solutions.py`（第一列 `A` 表示新文件已**暂存**）；`commit` 之后才有历史，`push -u origin main` 把它上传到远程。**二**，`git switch -c exp` 新建并切到 `exp` 分支；改文件后状态是 ` M solutions.py`（第二列的 `M` = 工作区已修改、**未暂存**）；`commit -am` 把已跟踪文件的修改暂存并提交。`git log --format=%s` 显示历史是 `try x = 2` 在上、`first version` 在下（新的在上）。**三**，切回 `main`，`git diff exp --stat` 显示 `solutions.py` 与 `exp` 有 1 行不同。**四，改坏了**：在 `main` 上把文件写成 `broken!!`、没有提交，`git restore solutions.py` 放弃修改，`status` 显示「空：没有任何改动」；注意 `restore` 会**丢掉**未提交的改动，不能撤销。**五，想保留但先去做别的事**：`git stash` 把改动收起来（`status` 为空），`git stash pop` 取回来（又是 ` M solutions.py`）。**六**，`git push origin exp` 之后，`git branch -r` 列出远程有 `origin/exp` 和 `origin/main`。日常最常用的就是：

```bash
git clone <地址>            # 下载仓库（未运行，需要网络上的真实仓库）
git switch -c my-feature    # 新建并切换分支（老写法 git checkout -b）
git status                  # 看改了什么
git add 文件名              # 暂存
git commit -m "说明"        # 本地提交
git push -u origin my-feature   # 上传分支
git pull                    # 拉取别人的更新
```

**最好的习惯：动手改之前先开一个新分支**，改坏了切回 `main` 就是干净的。（上面的 `clone` 示例需要真实的远程仓库，没有在本节运行。）
"""),
  V("1VVCd0eSkYc", "视频三：Master the basics of Conda environments in Python（The Jackson Laboratory）", 9),
  T(r"""
### 虚拟环境：每个项目一个独立的「Python + 库」

> **标准定义 · 虚拟环境 (virtual environment)**
>
> **虚拟环境**是一个独立的目录，里面有自己的 Python **解释器 (interpreter)** 和自己的已安装库。激活后，`python` 和 `pip` 指向这个环境，装、卸库只影响它，不影响系统 Python 和其他环境。Python 自带 `venv`；**Conda** 是另一套环境管理器，除了 Python 库，还能管理 Python 版本本身和非 Python 的依赖。**依赖清单**（`requirements.txt` 或 `environment.yml`）记录了环境里的包和版本，别人据此可以重建同样的环境。
>
> *English: A virtual environment is an isolated directory with its own interpreter and installed packages; activating it makes python and pip refer to it. venv ships with Python; conda also manages the Python version and non-Python dependencies. A requirements file lets others rebuild the same environment.*

**白话版：「每个项目一个独立的工具箱」。** 项目 A 要 PyTorch 2.1，项目 B 要 1.13，混在一个工具箱里必然打架；给每个项目单独一个工具箱，各用各的。下面真实创建一个虚拟环境，观察它是不是真的「独立」：

""" + C_VENV + r"""

读输出：新建的环境里，`sys.prefix` 与系统 Python 不同（`True`），说明它确实是独立的目录；刚建好的环境里**没有** einops（`import` 失败，`False`）；用环境自己的 `pip` 装完之后才能导入（`True`）；`pip freeze` 只列出 `einops` 一个包，说明这个环境里干净得只有我们装的东西（连 numpy 都没有）。把 `pip freeze > requirements.txt` 的结果交给别人，他用 `pip install -r requirements.txt` 就能在新环境里重建同样的依赖，这就是「可复现」。（这段代码需要联网安装 einops。）

Conda 的对应命令（**未在本节运行**，因为需要安装 Conda；它们和上面的 `venv` 做的是同类的事）：

```bash
conda create -n arena python=3.11   # 创建名为 arena 的环境，并指定 Python 版本
conda activate arena                # 激活（命令行前面会显示 (arena)）
pip install -r requirements.txt     # 在环境里装项目依赖
conda env list                      # 列出所有环境
conda deactivate                    # 退出
```

**最常见的坑**：你在命令行里 `conda activate arena` 后装了 PyTorch，但 VS Code 右下角选的是另一个 Python 解释器，于是 `import torch` 报 `ModuleNotFoundError`。排查方法：在代码里运行 `import sys; print(sys.executable)`，看当前到底在用哪个 Python；在 VS Code 里按 Ctrl + Shift + P → *Python: Select Interpreter* 选对环境。

### pytest：让机器替你检查对不对

ARENA 的练习配有测试函数：你写完函数，运行测试，就知道对不对。理解测试怎么写，对你以后做自己的项目很重要。

> **标准定义 · 单元测试与 pytest (unit test & pytest)**
>
> **单元测试**是一个小函数，用 `assert 条件` 断言被测代码在某个输入下的行为；条件为假就算失败。**pytest** 会自动收集名字以 `test_` 开头的函数并运行，汇总通过 / 失败的数量；`@pytest.mark.parametrize` 能用一组参数重复运行同一个测试。运行结束的**退出码**是 0 表示全部通过，非 0 表示有失败。
>
> *English: A unit test asserts that code behaves as expected on some input. pytest collects functions named test_*, runs them, and reports passes and failures; parametrize reruns a test over several inputs. The exit code is 0 if everything passes.*

**白话版：「自动批改作业的答案卷」。** 你先写好「标准答案」，以后每次改了代码，一条命令就能自动批改一遍。

""" + C_PYTEST + r"""

读输出：我们为一个数值稳定的 softmax 写了 4 个测试函数，其中一个用 `parametrize` 展开成 3 个，共 6 个用例：「和为 1」「对 1000 这样的大输入不溢出」「对全 0 输入输出均匀分布（试了 $n=2,5,10$）」都通过了；最后一个**故意写错**的期望值（两个相同输入的输出应该是 0.5，写成了 0.6）失败，进度行里 `.....F` 的 `F` 就是它。末行 `1 failed, 5 passed`，退出码为 1，说明有失败；全部通过时退出码为 0。判断「数值对不对」要用 `np.isclose` / `np.allclose`（张量用 `torch.allclose`），不要用 `==`：第 11 节里看到 `float32` 的 0.1 并不精确等于 0.1。

### 这一节你要带走的三句话

1. **命令行靠管道把小命令连成流水线，靠退出码判断成败；VS Code 的 `# %%` 单元让一个 `.py` 文件兼有 notebook 的交互和脚本的可复用，调试器能让你在出事的那一行直接看形状。**
2. **Git 有工作区、暂存区、仓库三层，`commit` 只是本地存档，`push` 才上传；动手前先开分支，改坏了用 `restore`，要保留就 `stash`。**
3. **每个项目一个虚拟环境，并用依赖清单记录；「装的环境」和「运行的环境」不一致是 `ModuleNotFoundError` 最常见的原因；交付 notebook 前要重启并全部运行，用 pytest 检查关键函数。**
"""),
  THINK("你在 `main` 分支上改坏了代码，还没有提交。怎么回到上一次提交的状态？如果想保留这些修改、先去做别的事呢？", r"""
- **放弃未提交的修改**：`git restore 文件名`（`git restore .` 恢复所有文件）。上面的实验里 `broken!!` 就是这样被丢掉的。注意这会**丢掉**这些改动，没法撤销。
- **想保留修改、先切走**：`git stash` 把改动暂存起来，工作区恢复干净；回来后 `git stash pop` 取回。
- 更好的习惯：动手改之前先 `git switch -c 新分支`，在分支上随便试，出问题了直接切回 `main`。
"""),
  THINK("`pip install torch` 之后，在 VS Code 里运行却报 `ModuleNotFoundError: No module named 'torch'`。最可能的原因是什么？怎么排查？", r"""
**装的环境和运行的环境不是同一个。** 比如你在命令行里 `conda activate arena` 后装了 torch，但 VS Code 用的是另一个 Python 解释器。

排查：在代码里运行 `import sys; print(sys.executable)` 看当前用的是哪个 Python；`python -m pip list` 看它里面装了什么。解决：在 VS Code 里按 Ctrl + Shift + P → *Python: Select Interpreter* 选 `arena` 环境。顺带一个好习惯：用 `python -m pip install ...` 而不是裸的 `pip install ...`，这样装库用的一定是你正在用的那个 Python。
"""),
  THINK("你把项目代码发给同学，他说「跑不起来 / 结果和你不一样」。为了让别人能**复现**你的结果，你应该随代码一起记录哪些东西？为什么这对做研究和写论文很重要？", r"""
至少记录：

1. **依赖清单**：`pip freeze > requirements.txt` 或 `conda env export > environment.yml`，以及 Python 版本；库的版本不同，行为可能不同（比如默认值、数值精度）。
2. **随机种子 (random seed)**：训练里有大量随机性（初始化、数据打乱），固定种子才能比较两次运行（PyTorch 里 `torch.manual_seed(0)`，上一节的实验都是这样做的）。
3. **代码版本**：用 Git 提交，并记下提交的哈希值，保证「得到这个结果的代码」可以找回。
4. **运行方式和数据**：命令、超参数、数据版本。

可复现性是科研可信度的基础：别人无法复现的结果，很难被相信，你自己半年后也无法复现。再配上 `pytest` 检查关键函数，能让「改了一处、悄悄弄坏另一处」更早暴露。
"""),
  KW(("管道","pipe `|`","把一个命令的输出交给下一个"),
     ("重定向","redirection `>` `>>`","把输出写入文件（覆盖 / 追加）"),
     ("退出码","exit code","0 成功、非 0 失败，shell 里读特殊变量 `?`"),
     ("命令面板","Command Palette","Ctrl + Shift + P，VS Code 的万能入口"),
     ("代码单元","`# %%` cell","让 .py 文件像 notebook 一样分块运行"),
     ("断点 / 调试器","breakpoint / debugger","程序暂停，查看变量和形状"),
     ("类型提示","type hints","`def f(x: int) -> float`，运行时不检查"),
     ("隐藏状态","hidden state","notebook 里单元运行顺序造成的变量状态"),
     ("版本控制","version control","记录每一次修改，可回退可协作"),
     ("提交 / 暂存区","commit / staging area","`git add` 选改动，`git commit` 存档"),
     ("分支","branch","独立的开发线，不影响主线"),
     ("远程仓库","remote","GitHub 上的那份，`push` 上传、`pull` 下载"),
     ("虚拟环境","virtual environment","每个项目独立的 Python + 库"),
     ("解释器","interpreter","实际运行代码的那个 Python，`sys.executable`"),
     ("单元测试","unit test (pytest)","用 `assert` 自动检查函数行为"),
  ),
 ],
 "references": [
  {"title": "ARENA [0.0] Prerequisites — Software Engineering 部分", "url": "https://github.com/ARENA-education/ARENA_materials/blob/main/chapter0_fundamentals/instructions/pages/00_%5B0.0%5D_Prerequisites.md", "note": "VS Code 快捷键表、Git 要求的出处（讲解为自写，未转载原文）"},
  {"title": "Learn Git Branching（交互式练习）", "url": "https://learngitbranching.js.org/", "note": "ARENA 推荐，强烈建议做前几关"},
  {"title": "VS Code：Python 交互式窗口（# %% 单元）", "url": "https://code.visualstudio.com/docs/python/jupyter-support-py"},
  {"title": "Conda 官方：Getting started", "url": "https://conda.io/projects/conda/en/latest/user-guide/getting-started.html"},
  {"title": "UC Berkeley UNIX Tutorial", "url": "https://people.ischool.berkeley.edu/~kevin/unix-tutorial/toc.html", "note": "ARENA 推荐：看到第 4 节就够"},
 ],
 "quiz": {"questions": QUIZ},
}

if __name__ == '__main__':
    dump(unit, "arena-0.0", "u12-dev-tools.json")
