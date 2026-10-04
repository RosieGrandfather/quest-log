/* 学习页里的 Python 代码块变成「可以运行的笔记本单元」：▶ 运行、可以改代码、同一节里变量共用。
   规则：Markdown 里用 ```python 的块可以运行；不能在网页里运行的（读写真实文件、启动子进程、装包等）写成 ```python-static，只显示。
   块末尾的「# 输出：…」行是出课时真实运行的结果，会拆出来显示成「预期输出」，点运行后换成这次的运行结果。 */
import { escapeHTML } from '../core/html.js';

let worker = null;
let seq = 0;
const pending = new Map();     // id → {cell, onDone}

function ensureWorker(){
  if(worker) return worker;
  worker = new Worker(new URL('./pyworker.js', import.meta.url));
  worker.onmessage = e=>{
    const {type, id, s} = e.data;
    const p = pending.get(id);
    if(!p) return;
    if(type === 'status') p.cell.setStatus(s);
    else if(type === 'out') p.cell.appendOut(s);
    else if(type === 'done'){ pending.delete(id); p.cell.finish(s); }
    else if(type === 'fail'){ pending.delete(id); p.cell.fail(s); }
  };
  worker.onerror = ()=>{ failAll('Python 运行环境出错了，可以点「停止」后重试'); };
  return worker;
}

function failAll(msg){
  for(const [, p] of pending) p.cell.fail(msg);
  pending.clear();
}

export function stopPython(){
  if(worker){ worker.terminate(); worker = null; }
  for(const [, p] of pending) p.cell.stopped();
  pending.clear();
}

/* 进入新的一节时清空变量（不重新下载 Python） */
export function resetPySession(){
  if(!worker) return;
  const id = ++seq;
  worker.postMessage({type:'reset', id});
}

function splitOutput(src){
  const lines = src.replace(/\n+$/, '').split('\n');
  const out = [];
  while(lines.length && lines[lines.length-1].startsWith('# 输出：')){
    out.unshift(lines.pop().slice('# 输出：'.length));
  }
  return {code: lines.join('\n'), out: out.join('\n')};
}

function makeCell(original, expected){
  const box = document.createElement('div');
  box.className = 'py-cell';
  box.innerHTML = `
    <textarea class="py-code" spellcheck="false" autocapitalize="off" autocomplete="off" wrap="off"></textarea>
    <div class="py-bar">
      <button type="button" class="py-run">▶ 运行</button>
      <button type="button" class="py-stop" hidden>■ 停止</button>
      <button type="button" class="py-restore" hidden>还原代码</button>
      <button type="button" class="py-reset" title="清空这一节里已经定义的变量">清空变量</button>
      <span class="py-status"></span>
    </div>
    <div class="py-out-wrap" ${expected ? '' : 'hidden'}><div class="py-out-label">预期输出</div><pre class="py-out"></pre></div>`;
  const ta = box.querySelector('.py-code');
  const runBtn = box.querySelector('.py-run');
  const stopBtn = box.querySelector('.py-stop');
  const restoreBtn = box.querySelector('.py-restore');
  const resetBtn = box.querySelector('.py-reset');
  const status = box.querySelector('.py-status');
  const outWrap = box.querySelector('.py-out-wrap');
  const outLabel = box.querySelector('.py-out-label');
  const outPre = box.querySelector('.py-out');
  ta.value = original;
  outPre.textContent = expected;

  const fit = ()=>{ ta.style.height = 'auto'; ta.style.height = (ta.scrollHeight + 2) + 'px'; };
  let running = false;

  const cell = {
    setStatus(s){ status.textContent = s || ''; },
    appendOut(s){ outPre.appendChild(document.createTextNode(s)); },
    finish(err){
      running = false; runBtn.disabled = false; stopBtn.hidden = true; status.textContent = '';
      if(err){ const e = document.createElement('span'); e.className = 'py-err'; e.textContent = err; outPre.appendChild(e); }
      else if(!outPre.textContent){ outPre.textContent = '（运行完成，没有输出）'; }
    },
    fail(msg){
      running = false; runBtn.disabled = false; stopBtn.hidden = true; status.textContent = '';
      outWrap.hidden = false; outLabel.textContent = '运行结果';
      const e = document.createElement('span'); e.className = 'py-err';
      e.textContent = /Failed to fetch|importScripts|NetworkError|network/i.test(msg)
        ? '没能加载 Python 运行环境（可能是网络拦截了 cdn.jsdelivr.net，公司网络下常见）。可以先换手机热点试试，或把这段代码复制到本地 Python 里运行。\n' + msg
        : msg;
      outPre.appendChild(e);
    },
    stopped(){
      running = false; runBtn.disabled = false; stopBtn.hidden = true; status.textContent = '已停止（变量已清空，需要的话从上面的代码块重新运行）';
    },
  };

  const run = ()=>{
    if(running) return;
    running = true; runBtn.disabled = true; stopBtn.hidden = false;
    outWrap.hidden = false; outLabel.textContent = '运行结果'; outPre.textContent = '';
    status.textContent = '运行中…';
    const id = ++seq;
    pending.set(id, {cell});
    ensureWorker().postMessage({type:'run', id, code: ta.value});
  };
  runBtn.addEventListener('click', run);
  stopBtn.addEventListener('click', stopPython);
  resetBtn.addEventListener('click', ()=>{
    if(!worker){ status.textContent = '还没有运行过，没有变量可清空'; return; }
    resetPySession(); status.textContent = '已清空这一节的变量，请从上面的代码块重新运行';
  });
  restoreBtn.addEventListener('click', ()=>{ ta.value = original; restoreBtn.hidden = true; fit(); });
  ta.addEventListener('input', ()=>{ restoreBtn.hidden = ta.value === original; fit(); });
  ta.addEventListener('keydown', e=>{
    if(e.key === 'Enter' && (e.shiftKey || e.ctrlKey || e.metaKey)){ e.preventDefault(); run(); return; }
    if(e.key === 'Tab' && !e.shiftKey){
      e.preventDefault();
      const s = ta.selectionStart, t = ta.selectionEnd;
      ta.setRangeText('    ', s, t, 'end');
      ta.dispatchEvent(new Event('input'));
    }
  });
  requestAnimationFrame(fit);
  window.addEventListener('resize', fit);
  box._fit = fit;
  return box;
}

/* 把 root 里所有 ```python 代码块换成可运行的单元 */
export function enhanceCode(root){
  root.querySelectorAll('pre > code.language-python').forEach(codeEl=>{
    const pre = codeEl.parentElement;
    const {code, out} = splitOutput(codeEl.textContent);
    const cell = makeCell(code, out);
    pre.replaceWith(cell);
    if(cell._fit) cell._fit();
  });
}
