"""出课辅助：运行代码并把真实输出自动写进代码块（保证注释里的输出是真的）。"""
import subprocess, sys, textwrap

def code(src):
    """返回一个 ```python 代码块：源码 + 末尾逐行「# 输出：」真实输出。只用标准库，保证她的电脑上也能复现。"""
    src = textwrap.dedent(src).strip('\n')
    r = subprocess.run([sys.executable, '-c', src], capture_output=True, text=True, timeout=300)
    if r.returncode:
        raise SystemExit('代码运行出错：\n' + src + '\n' + r.stderr)
    outs = r.stdout.strip().splitlines()
    return '```python\n' + src + '\n' + ''.join(f'# 输出：{l}\n' for l in outs) + '```'
