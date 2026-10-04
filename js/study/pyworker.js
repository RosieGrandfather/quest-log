/* 在浏览器里运行 Python：Pyodide（WebAssembly 版 CPython），放在 Web Worker 里，
   这样死循环不会卡住页面，点「停止」直接结束这个 worker 就行。
   一个 worker = 一个「笔记本内核」：同一节里前面代码块定义的变量，后面的代码块能直接用。
   消息：
     页面 → worker  {type:'run', id, code} / {type:'reset'}
     worker → 页面  {type:'status'|'out'|'done'|'fail', id, s} */
/* global importScripts, loadPyodide */
const PYODIDE_VERSION = '0.29.5';
const BASE = `https://cdn.jsdelivr.net/pyodide/v${PYODIDE_VERSION}/full/`;

/* 和 tools/course/runlib.py 里的 Notebook 用同一套规则：整段 exec；最后一行如果是表达式，像 Jupyter 一样打印它的 repr */
const SETUP = `
import ast, sys, builtins, traceback, linecache
def _no_input(*a, **k):
    raise RuntimeError("网页里不支持 input()，请直接给变量赋值，例如 name = 'Yijia'")
builtins.input = _no_input
_KEEP = set(globals()) | {'_KEEP'}
def _reset():
    for k in list(globals()):
        if k not in _KEEP:
            del globals()[k]
def _run_cell(src):
    linecache.cache['<cell>'] = (len(src), None, src.splitlines(True), '<cell>')
    tree = ast.parse(src, '<cell>')
    last = None
    if tree.body and isinstance(tree.body[-1], ast.Expr):
        last = ast.Expression(tree.body.pop().value)
    exec(compile(tree, '<cell>', 'exec'), globals())
    if last is not None:
        v = eval(compile(last, '<cell>', 'eval'), globals())
        if v is not None:
            print(repr(v))
def _safe(src):
    try:
        _run_cell(src)
        return ''
    except BaseException as e:
        tb = e.__traceback__
        while tb is not None and tb.tb_frame.f_code.co_filename != '<cell>':
            tb = tb.tb_next
        if tb is None:
            return ''.join(traceback.format_exception_only(type(e), e))
        return ''.join(traceback.format_exception(type(e), e, tb))
`;

let pyPromise = null;
let curId = null;
const post = (type, s) => postMessage({type, id: curId, s});

function getPy(){
  if(!pyPromise){
    pyPromise = (async ()=>{
      post('status', '正在加载 Python 运行环境（第一次约 10 MB，之后浏览器会缓存）…');
      importScripts(BASE + 'pyodide.js');
      const py = await loadPyodide({indexURL: BASE});
      py.setStdout({batched: s=> post('out', s + '\n')});
      py.setStderr({batched: s=> post('out', s + '\n')});
      await py.runPythonAsync(SETUP);
      return py;
    })();
  }
  return pyPromise;
}

let chain = Promise.resolve();
onmessage = e => {
  const m = e.data;
  chain = chain.then(async ()=>{
    curId = m.id;
    try{
      const py = await getPy();
      if(m.type === 'reset'){ py.globals.get('_reset')(); post('done', ''); return; }
      await py.loadPackagesFromImports(m.code, {messageCallback: s=> post('status', s), errorCallback: s=> post('status', s)});
      post('status', '');
      const err = py.globals.get('_safe')(m.code);
      post('done', err || '');
    }catch(err){
      pyPromise = null;
      post('fail', String(err && err.message || err));
    }
  });
};
