"""py-0 第 5 节的代码块：一个知识点一块（Notebook：同一节里的块共用变量，顺序 = 讲义里出现的顺序）"""
from runlib import Notebook

nb = Notebook()

# ───────────── 先认识 import ─────────────
C_IMPORT = nb.cell('''
import math                                  # 写法一：拿来整个模块，用「模块名.名字」调用
print(math.sqrt(16), math.pi)

from math import sqrt                        # 写法二：只取出需要的名字，直接用
print(sqrt(25))

import math as m                             # 写法三：给模块起一个短别名
print(m.floor(2.7), type(m).__name__)
''')

# ───────────── 文件与路径 ─────────────
C_PATH = nb.cell('''
import tempfile
from pathlib import Path

root = Path(tempfile.mkdtemp())                  # 一个临时目录（网页里是内存文件系统）
data_dir = root / "data" / "raw"                 # pathlib：用 / 拼接路径，自动处理不同系统的分隔符
data_dir.mkdir(parents=True, exist_ok=True)      # parents：连中间目录一起建；exist_ok：已存在不报错

f = data_dir / "notes.txt"
f.write_text("第一行：你好\\n第二行：hello\\n第三行\\n", encoding="utf-8")
print("存在：", f.exists(), "| 名字：", f.name, "| 后缀：", f.suffix, "| 不含后缀：", f.stem)
print("父目录名：", f.parent.name, "| 相对路径：", f.relative_to(root))
''')

C_READ = nb.cell('''
print(repr(f.read_text(encoding="utf-8")))       # 方式一：一次读完（只适合小文件）

with open(f, encoding="utf-8") as fh:            # 方式二：with open；用完自动关闭，即使中途出错
    for i, line in enumerate(fh, 1):             # 文件对象是迭代器：一次一行，不占内存
        print(i, line.rstrip("\\n"))
''')

C_MODE = nb.cell('''
with open(f, "a", encoding="utf-8") as fh:       # 'a'：追加到末尾
    fh.write("追加的一行\\n")
print(len(f.read_text(encoding="utf-8").splitlines()), "行")

g = data_dir / "scratch.txt"
with open(g, "w", encoding="utf-8") as fh:       # 'w'：覆盖
    fh.write("第一次写入的内容")
with open(g, "w", encoding="utf-8") as fh:
    fh.write("b")
print(repr(g.read_text(encoding="utf-8")))       # 旧内容已经被清空

try:
    open(f, "x")                                 # 'x'：只新建，文件已存在就报错
except FileExistsError:
    print("FileExistsError：x 模式不会覆盖已有文件")
''')

C_GLOB = nb.cell('''
for name in ["a.csv", "b.csv", "c.txt"]:
    (data_dir / name).write_text("x")
print(sorted(p.name for p in data_dir.glob("*.csv")))                       # glob：按模式匹配当前目录
print(sorted(str(p.relative_to(root)) for p in root.rglob("*") if p.is_file()))   # rglob：递归所有子目录
''')

C_BIN = nb.cell('''
b = data_dir / "bytes.bin"
b.write_bytes(bytes([0, 255, 128]))              # 二进制：读写的是字节，不涉及编码
print(list(b.read_bytes()))
print(len("你好".encode("utf-8")), len("你好".encode("gbk")))   # 同一个字符串，不同编码占的字节数不同

try:
    (data_dir / "missing.txt").read_text()
except FileNotFoundError as e:
    print("FileNotFoundError：", type(e).__name__)
''')

# ───────────── JSON 与 CSV ─────────────
C_JSON = nb.cell('''
import json

# JSON：dict / list / str / int / float / bool / None 与 Python 一一对应
cfg = {"lr": 0.001, "layers": [64, 32], "name": "实验一", "use_gpu": True, "dropout": None, "shape": (3, 4)}
s = json.dumps(cfg, ensure_ascii=False, indent=2)    # Python 对象 -> JSON 文本
print(s)
back = json.loads(s)                                 # JSON 文本 -> Python 对象
print(back == cfg, "| tuple 变成了：", type(back["shape"]).__name__)    # 元组 -> 列表：JSON 没有元组
''')

C_JSON_ERR = nb.cell('''
try:
    json.dumps({"x": {1, 2}})                        # 集合不能直接序列化
except TypeError as e:
    print("TypeError:", e)
print(json.dumps({1: "a"}), "| 键变成了字符串")      # 字典的键一律变成字符串
''')

C_CSV_R = nb.cell('''
import csv, io

text = "name,score\\nAnn,90\\nBob,85\\nCy,\\n"
rows = list(csv.DictReader(io.StringIO(text)))       # DictReader：按列名取值（这里用 StringIO 代替文件）
print(rows)
print("读出来都是字符串：", type(rows[0]["score"]).__name__)
scores = [int(r["score"]) for r in rows if r["score"]]   # 类型要自己转，缺失值要自己处理
print(scores, sum(scores) / len(scores))
''')

C_CSV_W = nb.cell('''
out = io.StringIO()
w = csv.DictWriter(out, fieldnames=["name", "score"])
w.writeheader()
w.writerow({"name": "Dee", "score": 70})
w.writerow({"name": "含,逗号", "score": 60})
print(out.getvalue().strip().replace("\\r\\n", " | "))   # 含逗号的字段会被自动加上引号
''')

# ───────────── 模块与包 ─────────────
C_MOD = nb.cell('''
import sys, textwrap
from pathlib import Path

sys.path.insert(0, str(root))                        # 让 Python 到 root 里找模块
sys.modules.pop("mathutils", None)                   # 保证重新运行这一块时也从头导入
(root / "mathutils.py").write_text(textwrap.dedent("""
    print("  [mathutils] 被执行了，__name__ =", __name__)

    def square(x):
        return x * x

    if __name__ == "__main__":
        print("  [mathutils] 作为脚本直接运行：", square(7))
"""))                                                # 一个模块 = 一个 .py 文件

import mathutils                                     # 第一次导入：执行整个文件
import mathutils as mu                               # 再次导入：直接用缓存，不会重新执行
print("square(5) =", mathutils.square(5), "| 同一个模块对象：", mu is mathutils)
print("mathutils 在 sys.modules 里：", "mathutils" in sys.modules)
''')

C_MAIN = nb.cell('''
import runpy

# runpy.run_path(..., run_name="__main__") 模拟「python mathutils.py」：这时 __name__ 是 "__main__"
_ = runpy.run_path(str(root / "mathutils.py"), run_name="__main__")
''')

C_MAIN_CLI = nb.cell('''
import subprocess, sys

r = subprocess.run([sys.executable, "mathutils.py"], cwd=root, capture_output=True, text=True)
print("$ python mathutils.py")
print(r.stdout.rstrip())
''', static=True)

C_PKG = nb.cell('''
import importlib

pkg = root / "mypkg"                                  # 包 = 含有 __init__.py 的文件夹
pkg.mkdir()
(pkg / "__init__.py").write_text("VERSION = '0.1'\\n")
(pkg / "tools.py").write_text("def double(x): return 2 * x\\n")
importlib.invalidate_caches()                         # 刚建了新文件，让导入系统重新扫描目录

from mypkg import VERSION                             # 导入包会执行 __init__.py
from mypkg.tools import double                        # 点号访问子模块
print(VERSION, double(21))
''')

C_NOMOD = nb.cell('''
try:
    import not_a_real_module
except ModuleNotFoundError as e:
    print(type(e).__name__ + ":", e)
''')

# ───────────── 命令行与环境变量 ─────────────
C_ARGP = nb.cell('''
import argparse

def build_parser():
    p = argparse.ArgumentParser(prog="train.py", description="训练脚本")
    p.add_argument("data", help="数据文件路径")                              # 位置参数
    p.add_argument("--lr", type=float, default=1e-3, help="学习率")        # 可选参数
    p.add_argument("--epochs", type=int, default=10)
    p.add_argument("--no-shuffle", action="store_true")                    # 开关
    return p

p = build_parser()
args = p.parse_args(["train.csv", "--lr", "0.01", "--no-shuffle"])        # 用列表模拟终端里输入的内容
print(args)
print(args.data, args.lr, args.epochs, args.no_shuffle)
''')

C_ARGP_ERR = nb.cell('''
import contextlib

msg = io.StringIO()
try:
    with contextlib.redirect_stderr(msg):            # argparse 把错误说明打印到标准错误
        p.parse_args(["train.csv", "--epochs", "abc"])
except SystemExit as e:
    print("argparse 打印用法说明后退出（SystemExit），退出码", e.code)
print(msg.getvalue().strip().splitlines()[-1])
''')

C_ENV = nb.cell('''
import os, sys

os.environ["MY_API_KEY"] = "demo-not-a-real-key"     # 实际中由终端或 .env 提供，不写进代码
print(os.environ.get("MY_API_KEY"), os.environ.get("NOT_SET", "默认值"))
print("sys.argv 是一个：", type(sys.argv).__name__)
''')
