"""py-0 第 5 节：文件、模块与环境"""
from unitlib import *
from y05c import *

unit = {
 "id": "u05",
 "title": "文件、模块与环境",
 "en": "Files, Modules & Environments",
 "minutes": 90,
 "objectives": [
  "会用 `with open(...)` 与 **`pathlib`** 读写文本 / 二进制文件、遍历目录，理解**编码 (encoding)** 为什么要写 `utf-8`",
  "会读写 **JSON** 与 **CSV**，知道 JSON 的类型对应关系与它的局限（元组变列表、集合不能序列化、CSV 读出来全是字符串）",
  "理解 **模块 (module)** 与 **包 (package)**、`import` 的机制、`if __name__ == \"__main__\"` 的作用，会写一个能被导入、也能直接运行的 `.py` 文件",
  "会用 `argparse` 写**命令行程序**，会用**环境变量**存放配置与密钥",
  "理解 **虚拟环境 (virtual environment)** 与包管理（`venv`、`pip`、`requirements.txt`、`uv`）：为什么每个项目要有自己的环境，怎样复现别人的环境",
 ],
 "blocks": [
  T(r"""
### 先说这一节要干什么

前几节写的都是「在一个文件里、对内存里的数据」做事。真实的项目是**很多文件**：数据在磁盘上，代码拆在多个模块里，依赖几十个第三方库，还要在别人的电脑和服务器上跑起来。这一节讲这些**把代码变成项目**的基础：文件读写、模块与包、命令行、环境管理。这是很多人「会写代码，但跑不起来别人的项目」的原因。

**学完它你就能看懂这几件事：**

- 从 GitHub 克隆一个 ML 项目，**怎么把它跑起来**：`python -m venv .venv`、`pip install -r requirements.txt`、`python train.py --lr 0.01 --epochs 5`；
- 项目目录里 `src/`、`__init__.py`、`config.json`、`data/raw/`：每一个是什么，`from src.models import Net` 为什么能工作；
- 为什么你在自己电脑上能跑的代码，换一台机器就报 `ModuleNotFoundError` 或者结果不一样：**环境不一致**；
- 读写数据集（CSV、JSON、JSONL），保存实验配置和结果。

**本节安排（约 90 分钟）**：文件与路径（20 分钟，含视频一）→ JSON 与 CSV（15 分钟）→ 模块、包与 `__main__`（20 分钟，含视频二）→ 命令行与环境变量（10 分钟）→ 虚拟环境与包管理（15 分钟，含视频三）→ 总结与「想一想」（10 分钟）。

本节的代码块可以在网页里直接点「运行」：网页里的 Python 有一个存在内存里的文件系统，普通的 `open()` 读写、`import` 都能用；需要启动子进程、`pip`、`venv` 的内容只展示，不运行。同一节里后面的块会用到前面块定义的变量（比如 `root`、`f`），所以请**从上往下依次运行**。

### 文件与路径

> **标准定义 · 文件对象与路径 (file object & path)**
>
> `open(path, mode, encoding=...)` 返回一个**文件对象**，常用模式：`'r'` 读（默认）、`'w'` 写（**覆盖**）、`'a'` 追加、`'x'` 新建（已存在则报错）、加 `'b'` 为二进制模式。`with open(...) as f:` 在代码块结束时**自动关闭**文件，即使中途出错。文本文件有**编码 (encoding)**，即字符与字节的对应规则，应当总是显式写 `encoding="utf-8"`。**`pathlib.Path`** 把路径当作对象：用 `/` 拼接、`.name` `.stem` `.suffix` `.parent` 取各部分，`.exists()`、`.mkdir()`、`.glob()`、`.read_text()`、`.write_text()` 等方法操作文件。
>
> *English: open() returns a file object; modes r/w/a/x (plus b for binary). A with block closes the file automatically. Text files have an encoding, so always pass encoding="utf-8". pathlib.Path represents paths as objects with operators and methods.*

**白话版：「用完要关门」。** 文件像一间需要钥匙的房间：打开 (`open`) 才能读写，用完必须关闭（否则数据可能没真正写入磁盘，系统里能同时打开的文件数也有限）。`with` 保证了「不管发生什么，离开时一定关门」，所以**永远用 `with open`**。`pathlib` 则是「用对象表示地址」，比拼字符串 `"data/" + name + ".csv"` 安全得多。

**路径：先建一个目录、写一个文件，看看 `Path` 能告诉我们什么。** 为了不弄脏你的电脑，我们在一个临时目录里做所有实验：

""" + C_PATH + r"""

**读输出：** `data_dir = root / "data" / "raw"` 用 `/` 把路径拼起来，不管 Windows 还是 Linux，分隔符都由 `Path` 处理；`mkdir(parents=True, exist_ok=True)` 里，`parents` 表示连中间目录 `data` 一起建，`exist_ok` 表示已经存在也不报错。文件的各部分一目了然：名字 `notes.txt`，后缀 `.txt`，不含后缀的 `notes`，父目录名 `raw`，相对于 `root` 的路径是 `data/raw/notes.txt`。`write_text` 一步写完整个文件，注意我们显式写了 `encoding="utf-8"`。

**读文件：同一个文件，两种读法。** 小文件一次读完，大文件要一行一行读：

""" + C_READ + r"""

**读输出：** `read_text` 返回的是一整个字符串，用 `repr` 打印才能看到里面的 `\n` 换行符：三行文字，每行末尾一个 `\n`。第二种读法里，`for line in fh` 逐行读取，所以打印了 1、2、3 三行；每次内存里始终只有一行，这是上一节讲的**生成器 / 迭代器**思想，**处理大文件时用它，不要 `read()`**。`with` 一结束，文件就自动关闭了。

**写与追加：三种模式的区别。**

""" + C_MODE + r"""

**读输出：** 追加 `'a'` 之后文件变成 4 行（原来的 3 行加上新的 1 行）。**`'w'` 会清空已有的文件**：先写了「第一次写入的内容」，再用 `'w'` 写 `"b"`，读回来只剩 `'b'`，所以写之前想清楚。`'x'` 是更安全的「只新建」：文件已经存在时抛出 `FileExistsError`，不会覆盖任何东西。

**遍历与查找：** 想找出某个目录下的所有 `.csv`，不需要手写循环：

""" + C_GLOB + r"""

**读输出：** `glob("*.csv")` 只在这一个目录里按模式匹配，找到 `a.csv` 和 `b.csv`；`rglob("*")` 则**递归**进入所有子目录，我们再用 `is_file()` 只保留文件，列出了 `data/raw/` 下的 5 个文件（`a.csv`、`b.csv`、`c.txt`，加上前面建的 `notes.txt` 和 `scratch.txt`）。

**文本与二进制、编码，以及文件不存在：**

""" + C_BIN + r"""

**读输出：** 二进制模式读写的是**字节**：`[0, 255, 128]` 就是我们写进去的三个字节，不涉及编码。而**编码**决定了文字怎样变成字节：`"你好"` 在 UTF-8 里占 6 个字节、在 GBK 里占 4 个字节，**用错编码会得到乱码或 `UnicodeDecodeError`**（Windows 上默认编码不一定是 UTF-8，不写 `encoding=` 是跨平台 bug 的常见来源）。最后，读一个不存在的文件会抛出 `FileNotFoundError`（上一节的异常），可以用 `try / except` 接住。

小结这一部分的要点：**写之前想清楚模式**（`'w'` 覆盖、`'x'` 保险）；**大文件逐行迭代**；**编码总是显式写 `utf-8`**；**路径用 `Path` 拼接**。
"""),
  V("0MKcCHrTo0c", "视频一：Reading, Writing, and Appending Files in Python（Alex The Analyst）", 9),
  T(r"""
### JSON 与 CSV

> **标准定义 · JSON 与 CSV**
>
> **JSON (JavaScript Object Notation)**：基于文本的数据交换格式，支持对象（对应 Python 的 `dict`）、数组（`list`）、字符串、数字、`true` / `false`（`True` / `False`）、`null`（`None`）。`json.dumps` / `json.dump` 把 Python 对象转成 JSON 文本，`json.loads` / `json.load` 反向转换。**CSV (comma-separated values)**：每行一条记录、字段用逗号分隔的表格文本；**所有字段读出来都是字符串**，类型要自己转换。
>
> *English: JSON is a text interchange format that maps to dict, list, str, number, bool and None. CSV stores tabular data as comma-separated text; every field is read as a string.*

**白话版：** JSON 是「**带层次**的数据」（配置、API 返回、嵌套的记录），CSV 是「**扁平的表格**」（一行一条样本）。Pandas 的 `read_csv` 背后做的就是 CSV 的解析，再加上类型推断。

**JSON：写出去再读回来，数据还一样吗？**

""" + C_JSON + r"""

**读输出：** `dumps` 把字典变成了 JSON 文本：`True` 变成 `true`，`None` 变成 `null`，`ensure_ascii=False` 让中文直接显示而不是 `\uXXXX`，`indent=2` 让它缩进成可读的样子。再 `loads` 读回来，`back == cfg` 却是 `False`：**JSON 的类型对应是有损的**，元组 `(3, 4)` 写进去再读出来变成了列表 `[3, 4]`，因为 JSON 里只有数组，没有元组。

**JSON 还有哪些做不到的？**

""" + C_JSON_ERR + r"""

**读输出：** **集合、自定义对象不能直接序列化**，会抛出 `TypeError`；字典的键也一律变成字符串（整数键 `1` 变成了 `"1"`）。

**CSV：读出来是什么？**

""" + C_CSV_R + r"""

**读输出：** `DictReader` 把每一行变成一个字典，可以按列名取值。但**每个值都是字符串**：`'90'` 不是 `90`，数字要自己 `int()` / `float()` 转换；Cy 的分数是空字段，读出来是**空字符串 `''`，而不是 `None`**，所以我们用 `if r["score"]` 把它过滤掉，剩下 `[90, 85]`，平均 87.5。缺失值怎么处理，是你自己要决定的事。

**CSV：写出去的时候呢？**

""" + C_CSV_W + r"""

**读输出：** `DictWriter` 先写表头，再一行一行写记录。名字里含逗号的 `含,逗号` 被自动加上了引号 `"含,逗号"`，这样再读回来逗号不会被当成分隔符。**所以不要手写 `line.split(",")` 解析 CSV**，遇到带引号的逗号就会出错，用 `csv` 模块。

**两点补充：** **`pickle`** 能序列化几乎任何 Python 对象，但**不要加载来路不明的 pickle 文件**（可以在加载时执行任意代码）：PyTorch 的 `torch.load` 默认用 pickle，这也是为什么下载别人的模型文件要小心。大型的数据集通常用 **JSONL**（每行一个 JSON）、Parquet 等格式，思路同上。

### 模块与包

> **标准定义 · 模块 (module) 与包 (package)**
>
> **模块**就是一个 `.py` 文件，`import 名字` 会执行它并得到一个**模块对象**，通过 `名字.函数` 使用其中的内容；**包**是含有 `__init__.py` 的文件夹，可以包含多个模块与子包，用点号访问：`from mypkg.tools import double`。模块**只在第一次导入时执行一次**，之后从缓存 `sys.modules` 里取。Python 在 `sys.path` 列出的目录里找模块。每个模块有一个内置变量 **`__name__`**：被**导入**时是模块名，被**直接运行**时是 `"__main__"`，因此 `if __name__ == "__main__":` 下面的代码只在直接运行时才执行。
>
> *English: A module is a .py file; a package is a directory with __init__.py. A module is executed once on first import and cached in sys.modules. __name__ is "__main__" when a file is run directly and the module name when imported, which is what the __main__ guard tests.*

**白话版：「工具箱」与「工具箱柜子」。** 一个 `.py` 文件是一个工具箱，包是装着几个工具箱的柜子。`import` 是「把工具箱搬到桌上」；`if __name__ == "__main__"` 是「**如果这个文件是被单独运行的（而不是被别人拿去用的），才做下面的事**」，这样同一个文件既可以当工具箱被导入，又可以当脚本运行。

**导入一个模块：它被执行几次？** 我们写一个 `mathutils.py` 放进 `root`，再导入两次：

""" + C_MOD + r"""

**读输出：** 第一行是**导入时**打印的：`import mathutils` 执行了整个文件，文件顶部的 `print` 照常运行，此时 `__name__` 是模块名 `mathutils`；而 `if __name__ == "__main__"` 下面的 `square(7)` **没有执行**。第二次 `import mathutils as mu` 没有再打印那一行：**导入两次只会执行一次**，`mu is mathutils` 为 `True`，模块是单例，存在 `sys.modules` 里。

**同一个文件，直接运行会怎样？** 在终端里 `python mathutils.py` 就是「直接运行」；这里用 `runpy` 来模拟它（`run_name="__main__"`）：

""" + C_MAIN + r"""

**读输出：** 这一次 `__name__` 是 `__main__`，所以 `if __name__ == "__main__"` 下面的 `square(7)` 执行了，打印出 49。**同一个文件，被导入时不执行那一段，被直接运行时执行**，这就是这个守卫的作用。下面是在真正的终端里用子进程运行同一个文件的结果（这一块只展示、不在网页里运行），和上面完全一致：

""" + C_MAIN_CLI + r"""

**包：带 `__init__.py` 的文件夹。**

""" + C_PKG + r"""

**读输出：** 我们建了文件夹 `mypkg`，里面有 `__init__.py` 和 `tools.py`。`from mypkg import VERSION` 导入包时，`__init__.py` 被执行，里面的 `VERSION = '0.1'` 就成了包对外暴露的名字；`from mypkg.tools import double` 用点号访问子模块，`double(21)` 得到 42。（`importlib.invalidate_caches()` 只是因为我们在程序运行中才建了新文件，要让导入系统重新扫描目录。）

**找不到模块时：**

""" + C_NOMOD + r"""

**读输出：** `ModuleNotFoundError` 说明 Python 在 `sys.path` 里没找到它：**要么没安装，要么装在了另一个环境里**（这就是下面讲环境的原因）。

**写模块的好习惯：** 文件顶部只放 `import`、常量、函数和类的**定义**，不要有大量**导入时就运行**的代码（否则别人 `import` 你的模块时会有副作用，比如开始训练）；真正的主流程放进 `def main():`，再用 `if __name__ == "__main__": main()` 调用。**避免循环导入**（A 导入 B，B 又导入 A）：把共用的部分提取出来放到第三个模块。**避免 `from x import *`**，来源不清楚，还会覆盖同名变量。
"""),
  V("x5IbdKnvt6k", "视频二：What does if __name__ == '__main__' do in Python?（Tech With Tim）", 5),
  T(r"""
### 命令行程序与环境变量

> **标准定义 · 命令行参数与环境变量**
>
> **`sys.argv`** 是运行脚本时命令行里的各个词组成的列表（第 0 项是脚本名）。标准库 **`argparse`** 在此基础上提供：**位置参数**、**可选参数**（`--lr 0.01`）、类型转换、默认值、自动生成的 `--help` 说明与错误提示。**环境变量 (environment variable)** 是操作系统传给进程的一组键值对，`os.environ` 读取；常用来放**不适合写进代码的配置**，如 API 密钥、数据路径。
>
> *English: sys.argv holds the command-line words; argparse adds typed, documented options with defaults and automatic --help. Environment variables are key-value pairs passed by the OS, read via os.environ, and are used for secrets and deployment-specific config.*

**白话版：** 命令行参数是「**每次运行时告诉程序怎么做**」（学习率多少、训多少轮），环境变量是「**这台机器 / 这个环境的设定**」（密钥是什么）。把它们从代码里分离出来，同一份代码才能不改动地跑不同的实验、在不同的机器上跑。

**用 `argparse` 声明参数。** 我们用一个列表模拟用户在终端里输入的内容：

""" + C_ARGP + r"""

**读输出：** `parse_args` 把命令行转成一个对象：位置参数 `data` 是 `train.csv`；`--lr 0.01` 已经被转成了 `float`；没有写的 `--epochs` 用了默认值 10；开关 `--no-shuffle` 出现了，所以是 `True`。**所有 ML 项目的训练脚本几乎都是这个结构**：`python train.py --lr 0.01 --epochs 5`。

**参数不对时：**

""" + C_ARGP_ERR + r"""

**读输出：** 类型错了（`--epochs abc` 不是整数），`argparse` 会打印用法说明和一句清楚的错误信息，然后以 `SystemExit`（退出码 2）退出，而不是让程序在后面莫名其妙地崩溃。

**环境变量：配置与密钥。**

""" + C_ENV + r"""

**读输出：** `os.environ` 像一个字典：设置过的 `MY_API_KEY` 能取出来，没设置的 `NOT_SET` 用 `.get` 给了默认值 `默认值`；`sys.argv` 是一个列表。**绝对不要把密钥写进代码、更不要提交到 Git**：用环境变量（或 `.env` 文件，并把它加进 `.gitignore`）。（这里的 `os.environ[...] = ...` 只是为了演示，真正的密钥由终端或 `.env` 提供。）

### 虚拟环境与包管理

> **标准定义 · 虚拟环境 (virtual environment) 与包管理**
>
> **第三方包**是别人写好的库（NumPy、PyTorch……），用包管理器安装：`pip install numpy`。**虚拟环境**是一个**独立的文件夹**，里面有自己的 Python 解释器与自己安装的包，**每个项目一个环境**，互不干扰。创建：`python -m venv .venv`，激活后（Windows：`.venv\Scripts\activate`；macOS / Linux：`source .venv/bin/activate`）`pip install` 就装进这个环境。**`requirements.txt`** 记录依赖及版本（`pip freeze > requirements.txt` 生成，`pip install -r requirements.txt` 复现）。**`uv`** 是更快的新一代工具，把虚拟环境、依赖安装与锁定合在一起（`uv venv`、`uv add numpy`、`uv run train.py`）。
>
> *English: Third-party packages are installed with pip. A virtual environment is an isolated directory with its own interpreter and packages, one per project. requirements.txt records dependencies; uv is a fast modern alternative combining environment and dependency management.*

**白话版：「每个项目一间独立的工作室」。** 如果所有项目共用一套全局安装的包：项目 A 需要 NumPy 1.x、项目 B 需要 NumPy 2.x，只能有一个赢；升级一个包，另一个项目就坏了。每个项目一个虚拟环境，各装各的，互不影响，删掉环境文件夹就干净了。

一个典型的流程（在终端里，这些命令改变的是你电脑上的环境，所以只展示、不在网页里运行）：

```bash
python -m venv .venv                  # 1. 创建环境（只做一次）
source .venv/bin/activate             # 2. 激活（Windows：.venv\Scripts\activate）
pip install numpy pandas              # 3. 装依赖（现在装进了 .venv）
pip freeze > requirements.txt         # 4. 记录依赖及版本
# ……换一台机器，或者别人想复现你的环境：
pip install -r requirements.txt
```

**读这五行：** 第 1 步在项目目录里建一个 `.venv` 文件夹，里面有一份独立的 Python；第 2 步「激活」之后，终端里的 `python` 和 `pip` 都指向这个环境（命令行前面会多出 `(.venv)`）；第 3 步装的包只进这个环境；第 4 步把「装了什么、什么版本」写进 `requirements.txt`；最后一步是别人（或你换了电脑之后）按照这份清单复现同样的环境。

**几条经验：** **一**，**每个项目一个虚拟环境**，不要往全局 Python 里装包；**二**，`requirements.txt`（或 `pyproject.toml`）要提交到 Git，而虚拟环境文件夹**不要提交**（写进 `.gitignore`）；**三**，**固定版本**（`numpy==1.26.4`）能让结果可复现，ML 结果受库版本影响的事很常见；**四**，遇到 `ModuleNotFoundError`，先检查「**现在运行的是不是装了这个包的那个 Python**」（`which python` / `python -c "import sys; print(sys.executable)"`）：装在了 A 环境、却在 B 环境里运行，是最常见的原因；**五**，GPU 版本的 PyTorch 对 CUDA 版本有要求，要按官网给的命令安装；**六**，需要可复现的环境时，还有 **conda**（数据科学里常用）与 **Docker**（连操作系统层一起打包）可选，思路相同。
"""),
  V("Y21OR1OPC9A", "视频三：Python Virtual Environments - Full Tutorial for Beginners（Tech With Tim）", 9),
  T(r"""
### 这一节你要带走的三句话

1. **文件用 `with open(..., encoding="utf-8")`，路径用 `pathlib`**；大文件逐行迭代；JSON 适合层次化数据（类型对应有损），CSV 读出来全是字符串。
2. **模块 = `.py` 文件，包 = 带 `__init__.py` 的文件夹**；导入只执行一次；`if __name__ == "__main__"` 让同一个文件既能被导入又能直接运行；命令行参数交给 `argparse`，密钥放环境变量。
3. **每个项目一个虚拟环境，依赖写进 `requirements.txt`（固定版本）**，`ModuleNotFoundError` 通常是「运行的 Python 不是装包的那个」。
"""),
  THINK("你在 Windows 上用默认方式 `open('data.txt').read()` 读一个同事（macOS）给你的、含中文的文本文件，得到了乱码或 `UnicodeDecodeError`。可能的原因是什么？怎么避免？", r"""
**原因：文本文件的编码不一致，而你没有指定编码。** 同事的文件是 UTF-8；而 `open()` 不写 `encoding` 时使用的是**系统的默认编码**，在很多 Windows 中文系统上是 GBK（cp936），用 GBK 去解读 UTF-8 的字节，就会出现乱码或解码错误。

**避免：永远显式写 `encoding="utf-8"`**（`open(path, encoding="utf-8")`、`path.read_text(encoding="utf-8")`），写出文件时也同样指定。如果拿到的文件编码未知，可以先用 `chardet` 之类的库探测，或者让对方明确说明。这是跨平台协作里最常见的小 bug 之一，代价极小、收益很大的习惯。
"""),
  THINK("为什么需要 `if __name__ == \"__main__\":`？如果不写，把一个含训练代码的 `train.py` 被另一个文件 `import train` 会发生什么？", r"""
`import train` 会**执行 `train.py` 里所有顶层的代码**：如果训练的主流程直接写在顶层，那么仅仅是「想复用里面的一个函数」（比如 `from train import build_model`），就会**触发整个训练**，既慢，又有副作用（读数据、写文件、占用 GPU）。

用 `if __name__ == "__main__": main()` 包住主流程之后：直接 `python train.py` 时 `__name__` 是 `"__main__"`，会运行训练；被 `import` 时 `__name__` 是 `"train"`，**只定义函数和类、不会运行训练**。这样同一个文件既是**可复用的模块**，又是**可运行的脚本**。同样的道理也让测试（上一节）能直接导入被测函数而不触发无关的代码。
"""),
  THINK("同事发来一个项目，你 `pip install -r requirements.txt` 之后运行，仍然报 `ModuleNotFoundError: No module named 'torch'`。你会怎么排查？", r"""
按这个顺序：

1. **你装包用的 Python 和运行用的 Python 是不是同一个？** 终端里 `which python`（Windows：`where python`）与 `which pip`，或者用 `python -m pip install ...`（**保证装到的是这个 `python` 对应的环境**）；在 Python 里 `import sys; print(sys.executable)` 看当前解释器；
2. **虚拟环境有没有激活？** 命令行前面有没有 `(.venv)`；在 VS Code / PyCharm 里，**项目选择的解释器**是不是这个环境（IDE 的运行按钮可能用的是另一个 Python）；
3. **安装是不是真的成功了？** 往上翻看有没有报错（尤其是 `torch` 这类大包，可能因为网络、磁盘空间、Python 版本不兼容而失败）；`pip list | grep torch`；
4. `requirements.txt` 里**有没有 `torch`**（有的项目要求按官网命令单独安装 GPU 版）。

第 1 点是占绝大多数的原因。总结：**「找不到模块」几乎总是环境问题，不是代码问题。**
"""),
  KW(("文件对象","file object","`open()` 返回的对象；用 `with` 保证关闭"),
     ("文件模式","file mode","`r` 读、`w` 覆盖写、`a` 追加、`x` 新建、`b` 二进制"),
     ("编码","encoding","字符与字节的对应规则；总是显式写 `utf-8`"),
     ("`pathlib`","pathlib","把路径当对象，用 `/` 拼接，带 `exists`、`glob` 等方法"),
     ("JSON","JSON","带层次的文本数据格式；元组变列表，集合不能序列化"),
     ("CSV","CSV","逗号分隔的表格；读出来全是字符串"),
     ("`pickle`","pickle","序列化任意 Python 对象；不要加载来路不明的文件"),
     ("模块 / 包","module / package","`.py` 文件 / 带 `__init__.py` 的文件夹"),
     ("`__name__`","__name__","直接运行时是 `\"__main__\"`，被导入时是模块名"),
     ("`sys.path` / `sys.modules`","sys.path / sys.modules","模块的搜索目录 / 已导入模块的缓存"),
     ("`argparse`","argparse","解析命令行参数的标准库"),
     ("环境变量","environment variable","操作系统传给进程的键值对，常用来放密钥与配置"),
     ("虚拟环境","virtual environment","每个项目独立的解释器与包目录；`python -m venv`"),
     ("`requirements.txt`","requirements.txt","记录依赖与版本，`pip install -r` 复现环境"),
     ("`uv`","uv","新一代的快速包与环境管理工具"),
  ),
 ],
 "references": [
  {"title": "Think Python 3e（Downey）— 第 13 章 Files and Databases", "url": "https://allendowney.github.io/ThinkPython/chap13.html", "note": "本节大纲依据之一，文件读写与路径，CC BY-NC-SA 4.0"},
  {"title": "Python Tutorial: Pathlib - The Modern Way to Handle File Paths（Corey Schafer，约 35 分钟，选看）", "url": "https://www.youtube.com/watch?v=yxa-DJuuTBI", "note": "pathlib 的完整演示，需要大量处理文件路径时看"},
  {"title": "Python Tutorial: Working with JSON Data（Corey Schafer，约 21 分钟，选看）", "url": "https://www.youtube.com/watch?v=9N6a-VLBa2I", "note": "json 模块的演示，含从网络读取数据"},
  {"title": "Python Tutorial: UV - A Faster, All-in-One Package Manager（Corey Schafer，约 27 分钟，选看）", "url": "https://www.youtube.com/watch?v=AMdG7IjgSPM", "note": "uv 的完整介绍，可以替代 pip 与 venv"},
  {"title": "Python 官方教程：Modules 与 Virtual Environments", "url": "https://docs.python.org/3/tutorial/modules.html", "note": "模块、包与导入的官方说明；同一教程里有 venv 与 pip 的章节"},
 ],
 "quiz": {"questions": [
  Q("为什么推荐写 `with open(path) as f:` 而不是直接 `f = open(path)`？",
    ["因为 `with` 更快", "因为 `with` 保证离开代码块时文件被关闭，即使中途出现异常", "因为 `open` 不能单独使用", "因为只有 `with` 才能读取中文"], 1,
    "`with` 底层用上下文管理器协议（`__enter__` / `__exit__`），保证清理一定执行。"),
  Q("`open(path, 'w')` 打开一个**已存在**的文件时，会发生什么？",
    ["在末尾追加", "报错", "文件内容被清空，从头写入", "什么也不做"], 2,
    "`'w'` 会截断（清空）已有文件；追加要用 `'a'`；`'x'` 则是「已存在就报错」。"),
  Q("读写含中文的文本文件，最稳妥的做法是？",
    ["不写 encoding，让系统自己决定", "总是显式指定 `encoding=\"utf-8\"`", "改成二进制模式再手动转换", "只用英文"], 1,
    "默认编码随系统不同（Windows 中文系统常是 GBK），不显式指定会导致跨平台的乱码或解码错误。"),
  Q("把 `{\"shape\": (3, 4)}` 用 `json.dumps` 再 `json.loads` 读回来，`shape` 的类型是？",
    ["元组 `tuple`", "列表 `list`", "字符串", "报错"], 1,
    "JSON 没有元组类型，元组被写成数组，读回来是列表。集合则无法直接序列化。"),
  Q("用 `csv.DictReader` 读出一个数值列（比如分数），每个值的类型是？",
    ["`int`", "`float`", "`str`，需要自己转换类型并处理缺失值", "取决于内容"], 2,
    "CSV 里没有类型信息，所有字段都是字符串；空字段是空字符串而不是 `None`。"),
  Q("`import mymodule` 被执行两次（比如在两个不同的文件里），模块里的代码会被执行几次？",
    ["两次", "一次，之后从 `sys.modules` 缓存里取", "每次导入都重新执行", "取决于文件大小"], 1,
    "模块只在第一次导入时执行，之后复用缓存的模块对象（单例）。"),
  Q("`if __name__ == \"__main__\":` 下面的代码，什么时候执行？",
    ["每次导入时", "只有这个文件被**直接运行**（如 `python file.py`）时", "只有被别的文件导入时", "永远不会"], 1,
    "直接运行时 `__name__` 是 `\"__main__\"`；被导入时是模块名。这让同一个文件既能被复用又能当脚本。"),
  Q("一个文件夹要被 Python 当作**包**使用，通常需要包含？",
    ["`main.py`", "`__init__.py`", "`setup.exe`", "`config.json`"], 1,
    "含 `__init__.py` 的文件夹是常规包，导入包时它会被执行，可以放包的版本号与对外暴露的名字。"),
  Q("每个项目使用独立的**虚拟环境**，主要的原因是？",
    ["让 Python 运行更快", "不同项目可以安装各自需要的包与版本，互不干扰，并且容易复现", "为了节省硬盘", "因为全局环境不能装包"], 1,
    "否则项目 A 与 B 需要不同版本的同一个库时只能有一个能正常运行，升级一个包还可能破坏另一个。"),
  Q("装了包，运行时却报 `ModuleNotFoundError`，**最常见**的原因是？",
    ["代码有语法错误", "运行代码用的 Python 与安装包用的不是同一个环境", "包太大", "需要重启电脑"], 1,
    "用 `python -m pip install` 保证装到当前 `python` 对应的环境；检查 `sys.executable` 与 IDE 选择的解释器。"),
 ]},
}

TARGET = [0, 2, 3, 1, 2, 0, 1, 3, 2, 1]
for q, t in zip(unit["quiz"]["questions"], TARGET):
    q["options"][q["answer"]], q["options"][t] = q["options"][t], q["options"][q["answer"]]
    q["answer"] = t

if __name__ == '__main__':
    dump(unit, "py-0", "u05-files-modules-envs.json")
