"""出课辅助：运行代码并把真实输出自动写进代码块（保证注释里的输出是真的）。"""
import subprocess, sys, textwrap

def code(src, err=False):
    """返回一个 ```python 代码块：源码 + 末尾逐行「# 输出：」真实输出。只用标准库，保证她的电脑上也能复现。"""
    src = textwrap.dedent(src).strip('\n')
    r = subprocess.run([sys.executable, '-c', src], capture_output=True, text=True, timeout=300)
    if err: r.stdout += r.stderr; r.returncode = 0
    if r.returncode:
        raise SystemExit('代码运行出错：\n' + src + '\n' + r.stderr)
    outs = r.stdout.strip().splitlines()
    return '```python\n' + src + '\n' + ''.join(f'# 输出：{l}\n' for l in outs) + '```'


# ───────────── 笔记本式运行：同一节里的代码块共用变量（和网页里「▶ 运行」的规则一致）─────────────
import ast, contextlib, io, os, tempfile, traceback, linecache


class Notebook:
    """一节课的所有 Python 代码块用同一个 Notebook：
        nb = Notebook()
        C_A = nb.cell('''x = 1''')
        C_B = nb.cell('''print(x + 1)''')     # 能直接用上一个块里的 x
    规则（网页里 js/study/pyworker.js 用同一套）：整块 exec；最后一行如果是表达式，像 Jupyter 一样打印它的 repr。
    默认 static=False，生成 ```python（网页里可以运行）；
    需要真实文件 / 子进程 / 装包的块用 static=True，生成 ```python-static（只显示，网页里没有运行按钮；仍然会在这里真实运行）。
    err=True：块里会报错（教学展示报错信息），把 traceback 也写进输出。"""

    def __init__(self, workdir=None):
        self.ns = {'__name__': '__main__'}
        self._tmp = tempfile.TemporaryDirectory() if workdir is None else None
        self.workdir = workdir or self._tmp.name

    def _run(self, src, err):
        buf = io.StringIO()
        old = os.getcwd()
        os.chdir(self.workdir)
        import sys
        if self.workdir not in sys.path:
            sys.path.insert(0, self.workdir)
        failure = None
        try:
            linecache.cache['<cell>'] = (len(src), None, src.splitlines(True), '<cell>')
            tree = ast.parse(src, '<cell>')
            last = None
            if tree.body and isinstance(tree.body[-1], ast.Expr):
                last = ast.Expression(tree.body.pop().value)
            with contextlib.redirect_stdout(buf):
                exec(compile(tree, '<cell>', 'exec'), self.ns)
                if last is not None:
                    v = eval(compile(last, '<cell>', 'eval'), self.ns)
                    if v is not None:
                        print(repr(v))
        except BaseException as e:      # noqa: BLE001
            tb = e.__traceback__
            while tb is not None and tb.tb_frame.f_code.co_filename != '<cell>':
                tb = tb.tb_next
            failure = ''.join(traceback.format_exception(type(e), e, tb)) if tb else ''.join(traceback.format_exception_only(type(e), e))
        finally:
            os.chdir(old)
        return buf.getvalue(), failure

    def cell(self, src, err=False, static=False):
        src = textwrap.dedent(src).strip('\n')
        out, failure = self._run(src, err)
        if failure and not err:
            raise SystemExit('代码运行出错：\n' + src + '\n' + failure)
        text = out + (failure or '')
        outs = text.rstrip('\n').splitlines() if text.strip('\n') else []
        lang = 'python-static' if static else 'python'
        return f'```{lang}\n' + src + '\n' + ''.join(f'# 输出：{l}\n' for l in outs) + '```'
