from runlib import code

C_SHELL = code('''
import subprocess, tempfile

def sh(cmd, cwd):
    r = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True, executable="/bin/bash")
    print(">", cmd)
    if r.stdout.strip():
        print(r.stdout.strip())

with tempfile.TemporaryDirectory() as d:
    sh("mkdir data logs && touch data/a.py data/b.txt data/train_cnn.py", d)   # 建目录、建空文件
    sh("ls data", d)                                           # 列出文件
    sh("ls data | grep py", d)                                 # 管道：把 ls 的输出交给 grep 过滤
    sh("ls data | grep py | wc -l", d)                         # 再交给 wc -l 数行数
    sh("echo 'epoch 1 loss 0.9' > logs/run.log", d)            # > ：覆盖写入文件
    sh("echo 'epoch 2 loss 0.5' >> logs/run.log", d)           # >> ：追加
    sh("cat logs/run.log", d)
    sh("grep 'epoch 2' logs/run.log | cut -d' ' -f4", d)       # 在日志里找一行，再取第 4 列
    sh("grep -q nothing logs/run.log; echo exit code $?", d)   # 命令的「退出码」：0 成功，非 0 失败
    sh("printf 'b\\\\na\\\\nc\\\\n' | sort", d)                      # 排序
''')

C_CELL = code('''
# 把下面这段保存成 demo.py：在 VS Code 里每个「# %%」是一个可以单独运行的单元，
# 但它仍然是一个普通的 Python 文件，用 python demo.py 一样能整体运行。

# %% 单元 1：准备数据
xs = [1, 2, 3, 4]

# %% 单元 2：计算
total = sum(x * x for x in xs)

# %% 单元 3：查看结果
print("sum of squares =", total)
''')

C_NB = code('''
# 模拟 notebook：每个单元修改同一个「全局状态」，运行顺序不同，结果就不同
cells = {
    "A": "lr = 0.1",
    "B": "loss = 10 * lr",
    "C": "lr = 0.01",
}

def run(order):
    ns = {}                          # 相当于 notebook 的内核变量
    for name in order:
        exec(cells[name], ns)
    return ns["loss"]

print("从上到下运行 A B C :", run("ABC"))     # 读代码的人以为 loss 是用 lr=0.01 算的
print("实际点击顺序 A C B :", run("ACB"))     # 但你先改了 lr 再算 loss，得到另一个数
''')

C_PDB = code('''
import subprocess, sys, tempfile, os

script = """import numpy as np

def center(x):
    mean = x.mean(axis=1)
    return x - mean

print(center(np.arange(6.).reshape(2, 3)))
"""
with tempfile.TemporaryDirectory() as d:
    open(os.path.join(d, "buggy.py"), "w").write(script)
    # 先不用调试器，直接运行：看报错
    r = subprocess.run([sys.executable, "buggy.py"], cwd=d, capture_output=True, text=True)
    print(r.stderr.strip().splitlines()[-1])
    # 再用调试器：在第 5 行（return x - mean）设断点，运行到那里，查看两个变量的形状，然后退出
    cmds = "b 5\\nc\\np x.shape\\np mean.shape\\nq\\n"
    r = subprocess.run([sys.executable, "-m", "pdb", "buggy.py"], cwd=d, input=cmds, capture_output=True, text=True)
    for line in r.stdout.replace(d, ".").splitlines():
        if line.startswith("(Pdb)") or line.startswith("> ") or line.startswith("-> "):
            print(line)
''')

C_TYPES = code('''
from typing import get_type_hints

def scale(x: float, k: int) -> float:       # 类型提示：给人和工具看的标注
    return x * k

print(get_type_hints(scale))
print(scale(2.0, 3))                         # 类型对：6.0
print(scale("ab", 3))                        # 类型错了，Python 运行时并不会拦你：字符串 * 整数也合法
# 如果在 VS Code 里打开类型检查（Pylance basic，或命令行 mypy），上一行会被标出：
# 参数 "x" 期望 float，实际是 str。这类错误在运行前就能发现。
''')

C_PYTEST = code('''
import re, subprocess, sys, tempfile, os

tests = """import numpy as np
import pytest

def softmax(x):
    e = np.exp(x - x.max())          # 减去最大值，防止 exp 溢出
    return e / e.sum()

def test_sums_to_one():
    assert np.isclose(softmax(np.array([1.0, 2.0, 3.0])).sum(), 1.0)

def test_stable_for_large_inputs():
    assert np.all(np.isfinite(softmax(np.array([1000.0, 1001.0]))))

@pytest.mark.parametrize("n", [2, 5, 10])
def test_uniform_input_gives_uniform_output(n):
    assert np.allclose(softmax(np.zeros(n)), 1.0 / n)

def test_wrong_expectation():
    assert softmax(np.array([0.0, 0.0]))[0] == 0.6      # 故意写错的期望值
"""
with tempfile.TemporaryDirectory() as d:
    open(os.path.join(d, "test_softmax.py"), "w").write(tests)
    r = subprocess.run([sys.executable, "-m", "pytest", "-q", "-rf", "-p", "no:cacheprovider", "--tb=no"],
                       cwd=d, capture_output=True, text=True)
    for line in r.stdout.splitlines():
        line = re.sub(r" in [0-9.]+s", "", line)
        print(line.split(" - ")[0])
    print("退出码：", r.returncode)
''')

C_GIT = code('''
import subprocess, tempfile, os

def g(cwd, *args):
    r = subprocess.run(["git", "-c", "user.name=demo", "-c", "user.email=demo@example.com", *args],
                       cwd=cwd, capture_output=True, text=True)
    out = r.stdout.rstrip()
    print("> git", " ".join(args).replace(ROOT[0], "<远程>"))      # 临时目录的路径每次不同，显示时替换掉
    if out:
        print(out)
    elif args[0] == "status":
        print("（空：没有任何改动）")

ROOT = ["@@"]

def write(cwd, name, text):
    open(os.path.join(cwd, name), "w").write(text)

with tempfile.TemporaryDirectory() as root:
    ROOT[0] = root
    remote = os.path.join(root, "remote.git"); work = os.path.join(root, "work")
    subprocess.run(["git", "init", "--bare", "-q", "-b", "main", remote])      # 假装这是 GitHub 上的仓库
    os.mkdir(work)
    g(work, "init", "-q", "-b", "main")
    write(work, "solutions.py", "x = 1\\n")
    g(work, "add", "solutions.py")                                            # 放进暂存区
    g(work, "status", "--short")                                              # A = 已暂存的新文件
    g(work, "commit", "-q", "-m", "first version")                            # 存档
    g(work, "remote", "add", "origin", remote)
    g(work, "push", "-q", "-u", "origin", "main")                             # 上传到「GitHub」

    g(work, "switch", "-c", "exp")                                            # 新分支，随便试
    write(work, "solutions.py", "x = 2\\n")
    g(work, "status", "--short")                                              # M = 已修改、未暂存
    g(work, "commit", "-q", "-am", "try x = 2")
    g(work, "log", "--format=%s")                                             # 提交历史，新的在上
    g(work, "switch", "-q", "main")
    g(work, "branch", "--show-current")
    g(work, "diff", "exp", "--stat", "--format=")                             # main 与 exp 的差别

    write(work, "solutions.py", "broken!!\\n")                                 # 在 main 上改坏了，还没提交
    g(work, "restore", "solutions.py")                                        # 放弃未提交的修改
    g(work, "status", "--short")                                              # 空：回到干净状态

    write(work, "solutions.py", "x = 3\\n")
    g(work, "stash", "-q")                                                    # 先把改动收起来
    g(work, "status", "--short")
    g(work, "stash", "pop", "-q")                                             # 再取回来
    g(work, "status", "--short")

    g(work, "push", "-q", "origin", "exp")
    g(work, "branch", "-r")                                                   # 远程有哪些分支
''')

C_VENV = code('''
import os, subprocess, sys, tempfile

env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}      # 去掉额外的搜索路径，保证看到的是环境本身
with tempfile.TemporaryDirectory() as d:
    venv = os.path.join(d, "arena-env")
    subprocess.run([sys.executable, "-m", "venv", venv], check=True)     # 创建虚拟环境（conda create 做的是同类的事）
    py = os.path.join(venv, "bin", "python")                             # Windows 下是 Scripts\\\\python.exe

    def run(*args):
        r = subprocess.run([py, *args], capture_output=True, text=True, env=env)
        return r.stdout.strip(), r.returncode

    out, _ = run("-c", "import sys; print(sys.prefix != sys.base_prefix)")
    print("python 位于独立环境内（sys.prefix 与系统 Python 不同）：", out)
    print("装 einops 之前能 import 吗：", run("-c", "import einops")[1] == 0)
    subprocess.run([py, "-m", "pip", "install", "-q", "einops"], capture_output=True, env=env)
    print("装 einops 之后能 import 吗：", run("-c", "import einops")[1] == 0)
    freeze, _ = run("-m", "pip", "freeze")
    print("pip freeze 的包名：", [line.split("==")[0] for line in freeze.splitlines()])
''')
