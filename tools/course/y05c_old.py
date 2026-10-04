from runlib import code

C_FILE = code('''
import tempfile
from pathlib import Path

with tempfile.TemporaryDirectory() as tmp:           # 临时目录，用完自动删除
    root = Path(tmp)                                 # pathlib：把路径当对象，而不是字符串
    data_dir = root / "data" / "raw"                 # 用 / 拼接路径，自动处理不同系统的分隔符
    data_dir.mkdir(parents=True, exist_ok=True)

    f = data_dir / "notes.txt"
    f.write_text("第一行：你好\\n第二行：hello\\n第三行\\n", encoding="utf-8")
    print("存在：", f.exists(), "| 名字：", f.name, "| 后缀：", f.suffix, "| 不含后缀：", f.stem)
    print("父目录名：", f.parent.name, "| 相对路径：", f.relative_to(root))

    # 读文件：三种方式
    print(repr(f.read_text(encoding="utf-8")))       # 一次读完（小文件）
    with open(f, encoding="utf-8") as fh:            # with：用完自动关闭，即使中途出错
        for i, line in enumerate(fh, 1):             # 文件对象是迭代器：一次一行，不占内存
            print(i, line.rstrip("\\n"))

    # 写与追加：'w' 覆盖，'a' 追加，'x' 文件已存在则报错
    with open(f, "a", encoding="utf-8") as fh:
        fh.write("追加的一行\\n")
    print(len(f.read_text(encoding="utf-8").splitlines()), "行")
    try:
        open(f, "x")
    except FileExistsError:
        print("FileExistsError：x 模式不会覆盖已有文件")

    # 遍历与查找
    for name in ["a.csv", "b.csv", "c.txt"]:
        (data_dir / name).write_text("x")
    print(sorted(p.name for p in data_dir.glob("*.csv")))
    print(sorted(str(p.relative_to(root)) for p in root.rglob("*") if p.is_file()))

    # 文本与二进制
    b = data_dir / "bytes.bin"
    b.write_bytes(bytes([0, 255, 128]))
    print(list(b.read_bytes()), len("你好".encode("utf-8")), len("你好".encode("gbk")))
    try:
        (data_dir / "missing.txt").read_text()
    except FileNotFoundError as e:
        print("FileNotFoundError：", type(e).__name__)
''')

C_FMT = code('''
import json, csv, io

# JSON：最常用的数据交换格式；dict / list / str / int / float / bool / None 一一对应
cfg = {"lr": 0.001, "layers": [64, 32], "name": "实验一", "use_gpu": True, "dropout": None, "shape": (3, 4)}
s = json.dumps(cfg, ensure_ascii=False, indent=2)
print(s)
back = json.loads(s)
print(back == cfg, "| tuple 变成了：", type(back["shape"]).__name__)    # 元组 → 列表：JSON 没有元组
try:
    json.dumps({"x": {1, 2}})                                          # 集合不能直接序列化
except TypeError as e:
    print("TypeError:", e)

# CSV：表格数据。用 DictReader 按列名取值
text = "name,score\\nAnn,90\\nBob,85\\nCy,\\n"
rows = list(csv.DictReader(io.StringIO(text)))
print(rows)
print("读出来的都是字符串：", type(rows[0]["score"]).__name__)
scores = [int(r["score"]) for r in rows if r["score"]]                # 要自己转类型、处理缺失值
print(scores, sum(scores) / len(scores))

out = io.StringIO()
w = csv.DictWriter(out, fieldnames=["name", "score"])
w.writeheader(); w.writerow({"name": "Dee", "score": 70}); w.writerow({"name": "含,逗号", "score": 60})
print(out.getvalue().strip().replace("\\r\\n", " | "))                 # 含逗号的字段会被自动加上引号
''')

C_MOD = code('''
import subprocess, sys, tempfile, textwrap
from pathlib import Path

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    # 一个模块 = 一个 .py 文件
    (root / "mathutils.py").write_text(textwrap.dedent("""
        print("  [mathutils] 被执行了，__name__ =", __name__)

        def square(x):
            return x * x

        if __name__ == "__main__":
            print("  [mathutils] 作为脚本直接运行：", square(7))
    """))
    (root / "main.py").write_text(textwrap.dedent("""
        import mathutils                      # 第一次导入：执行整个文件
        import mathutils as mu                # 再次导入：直接用缓存，不会重新执行
        from mathutils import square
        print("  [main] square(5) =", square(5), "| 同一个模块对象：", mu is mathutils)
        import sys
        print("  [main] mathutils 在 sys.modules 里：", "mathutils" in sys.modules)
    """))

    def run(*args):
        r = subprocess.run([sys.executable, *args], cwd=root, capture_output=True, text=True)
        print(r.stdout.rstrip() or r.stderr.rstrip().splitlines()[-1])

    print("$ python mathutils.py        # 直接运行")
    run("mathutils.py")
    print("$ python main.py             # 被导入")
    run("main.py")
    # 包 (package)：含有 __init__.py 的文件夹
    pkg = root / "mypkg"; pkg.mkdir()
    (pkg / "__init__.py").write_text("VERSION = '0.1'\\n")
    (pkg / "tools.py").write_text("def double(x): return 2 * x\\n")
    (root / "use_pkg.py").write_text("from mypkg import VERSION\\nfrom mypkg.tools import double\\nprint('  ', VERSION, double(21))\\n")
    print("$ python use_pkg.py          # 使用包")
    run("use_pkg.py")
    # 找不到模块
    (root / "bad.py").write_text("import not_a_real_module\\n")
    print("$ python bad.py")
    run("bad.py")
''')

C_CLI = code('''
import argparse, os, sys

# 命令行程序：argparse 解析参数（这里用列表模拟用户在终端里输入的内容）
def build_parser():
    p = argparse.ArgumentParser(prog="train.py", description="训练脚本")
    p.add_argument("data", help="数据文件路径")                              # 位置参数
    p.add_argument("--lr", type=float, default=1e-3, help="学习率")        # 可选参数
    p.add_argument("--epochs", type=int, default=10)
    p.add_argument("--no-shuffle", action="store_true")                    # 开关
    return p

p = build_parser()
args = p.parse_args(["train.csv", "--lr", "0.01", "--no-shuffle"])
print(args)
print(args.data, args.lr, args.epochs, args.no_shuffle)

try:
    p.parse_args(["train.csv", "--epochs", "abc"])
except SystemExit:
    print("参数类型不对：argparse 打印用法说明后退出（SystemExit）")

# 环境变量：用来放不该写进代码里的配置（密钥、路径）
os.environ["MY_API_KEY"] = "demo-not-a-real-key"
print(os.environ.get("MY_API_KEY"), os.environ.get("NOT_SET", "默认值"))
print("sys.argv 是脚本名加参数：", type(sys.argv).__name__)
''', err=True)
