/* 官方 Quant 练习套题（block type = 'gre-qset'）：题目是原书截图，下面放作答区。
   做完所有题 → 点「提交」→ 才显示每题对错 + 官方解析（截图）+ 本套总结。判分在 js/core/qgrade.js。 */
import { T } from './state.js';
import { escapeHTML } from '../core/html.js';
import { QKIND_LABEL, QC_TEXT, isAnswered, gradeItem, summarize, answerText, pickedText } from '../core/qgrade.js';
import { unitKey } from '../core/study.js';
import { submitPractice } from '../data/study.js';
import { showToast } from '../ui/common.js';

const L = 'ABCDEFGH';
const img = (b, p, w, cls = '')=> `<img class="qimg ${cls}" src="${escapeHTML(b.base + p)}" ${w ? `style="width:${Math.round(w / 2)}px"` : ''} alt="" loading="lazy">`;
const hintOf = it => it.kind === 'qc' ? '比较 Quantity A 和 Quantity B，选一项'
  : it.kind === 'mc1' ? '选一项'
  : it.kind === 'mcn' ? '选出所有正确的选项（可能不止一个）'
  : it.frac ? '分数作答：上面填分子，下面填分母' : '在框里填一个数（可以带小数点；逗号、% 不用管）';

function controlsHTML(it, i){
  if(it.kind === 'ne'){
    return it.frac
      ? `<div class="qne frac"><input type="text" inputmode="numeric" autocomplete="off" data-part="0" aria-label="分子"><span class="qbar"></span><input type="text" inputmode="numeric" autocomplete="off" data-part="1" aria-label="分母"></div>`
      : `<div class="qne"><input type="text" inputmode="decimal" autocomplete="off" aria-label="答案"></div>`;
  }
  const type = it.kind === 'mcn' ? 'checkbox' : 'radio';
  const n = it.kind === 'qc' ? 4 : it.nopt;
  return `<div class="qopts ${it.kind}">${Array.from({length: n}, (_, k)=>
    `<label class="qopt" data-k="${k}"><input type="${type}" name="q${i}" value="${k}"><span class="qletter">${L[k]}</span>${it.kind === 'qc' ? `<span class="qtext">${QC_TEXT[k]}</span>` : ''}<span class="gopt-tag"></span></label>`).join('')}</div>`;
}

function itemHTML(it, i, b){
  let fig = '';
  if(it.fig){
    const [a, z] = it.figRange;
    fig = i + 1 === a
      ? `<div class="gq-passage qfig"><div class="vp-tag">图表 · 第 ${a}–${z} 题共用</div>${img(b, it.fig, it.figw)}</div>`
      : `<details class="gq-passage gq-again"><summary>再看一遍图表（第 ${a}–${z} 题）</summary>${img(b, it.fig, it.figw)}</details>`;
  }
  return `${fig}<section class="gq qq" id="gq-${i}" data-i="${i}">
    <div class="gq-head"><span class="q-no">${it.n}</span><span class="gq-kind">${QKIND_LABEL[it.kind]}</span><span class="gq-verdict"></span></div>
    ${img(b, it.img, it.w, 'qstem')}
    <div class="gq-hint">${hintOf(it)}</div>
    ${controlsHTML(it, i)}
    <div class="gq-explain" hidden></div>
  </section>`;
}

export function qsetHTML(b){
  return `<div class="gset qset" data-n="${b.items.length}">
    <div class="gset-source">来源：${escapeHTML(b.source)}（官方原题与解析的截图，仅供个人学习；原书没有标难度）</div>
    <div class="gset-prev" hidden></div>
    ${b.items.map((it, i)=> itemHTML(it, i, b)).join('')}
    <div class="gbar" id="gbar"><span class="gbar-count"></span><button type="button" class="btn-primary gbar-submit">提交</button></div>
    <div class="gsummary" hidden></div>
  </div>`;
}

export function wireQset(root, course, unit){
  const box = root && root.querySelector('.qset');
  if(!box) return;
  const b = unit.blocks.find(x=> x.type === 'gre-qset');
  const items = b.items;
  const key = unitKey(course.id, unit.id);
  let answers = items.map(()=> '');
  let revealed = false, warned = false, saving = false;
  const $ = s => box.querySelector(s);
  const countEl = $('.gbar-count'), submitBtn = $('.gbar-submit'), sumEl = $('.gsummary'), prevEl = $('.gset-prev');

  const readOne = i => {
    const it = items[i], sec = box.querySelector(`#gq-${i}`);
    if(it.kind === 'ne'){
      const ins = [...sec.querySelectorAll('.qne input')].map(x=> x.value.trim());
      answers[i] = it.frac ? (ins[0] || ins[1] ? `${ins[0]}/${ins[1]}` : '') : ins[0];
    } else answers[i] = [...sec.querySelectorAll('input:checked')].map(x=> x.value).join(',');
  };
  const paint = ()=> items.forEach((it, i)=>{
    const sec = box.querySelector(`#gq-${i}`), a = answers[i] || '';
    if(it.kind === 'ne'){
      const ins = sec.querySelectorAll('.qne input');
      if(it.frac){ const [p, q] = a.split('/'); ins[0].value = p || ''; ins[1].value = q || ''; } else ins[0].value = a;
    } else {
      const set = a.split(',');
      sec.querySelectorAll('input').forEach(x=>{ x.checked = set.includes(x.value); });
    }
  });
  const updateCount = ()=>{
    const done = items.filter((it, i)=> isAnswered(it, answers[i])).length;
    countEl.textContent = `已做 ${done} / ${items.length}`;
    countEl.classList.toggle('full', done === items.length);
  };
  const onInput = e=>{
    if(revealed) return;
    const sec = e.target.closest('.qq'); if(!sec) return;
    readOne(Number(sec.dataset.i)); updateCount(); warned = false;
    const w = $('.gset-warn'); if(w) w.remove();
  };
  box.addEventListener('change', onInput);
  box.addEventListener('input', onInput);

  function reveal(){
    revealed = true;
    box.classList.add('revealed');
    box.querySelectorAll('input').forEach(x=>{ x.disabled = true; });
    items.forEach((it, i)=>{
      const sec = box.querySelector(`#gq-${i}`), a = answers[i] || '';
      const ok = gradeItem(it, a), blank = !isAnswered(it, a);
      sec.classList.add(ok ? 'right' : 'wrong');
      sec.querySelector('.gq-verdict').textContent = ok ? '✓ 答对' : blank ? '✗ 没作答' : '✗ 答错';
      if(it.kind !== 'ne'){
        const got = a.split(',');
        sec.querySelectorAll('.qopt').forEach(lab=>{
          const k = Number(lab.dataset.k), isC = it.ans.includes(k), picked = got.includes(String(k));
          lab.classList.toggle('correct', isC);
          lab.classList.toggle('chosen-wrong', picked && !isC);
          lab.querySelector('.gopt-tag').textContent = isC && picked ? '✓ 你选对了' : isC ? '正确答案' : picked ? '你的选择' : '';
        });
      }
      const ex = sec.querySelector('.gq-explain');
      ex.innerHTML = `<div class="gq-answer"><span>正确答案：<b>${escapeHTML(answerText(it))}</b></span><span class="${ok ? 'ok' : 'bad'}">你的答案：<b>${escapeHTML(pickedText(it, a))}</b></span></div>
        <div class="explain"><strong>官方解析（英文原文截图）</strong>${img(b, it.exp, it.ew, 'qexp')}</div>`;
      ex.hidden = false;
    });
    $('#gbar').hidden = true;
    const sum = summarize(items, answers);
    sumEl.innerHTML = summaryHTML(sum); sumEl.hidden = false;
    return sum;
  }

  function summaryHTML(sum){
    const kinds = Object.entries(sum.byKind).map(([k, v])=> `<div class="gsum-row"><span>${QKIND_LABEL[k]}</span><b>${v.correct} / ${v.total}</b><span class="gsum-pct">${Math.round(v.correct / v.total * 100)}%</span></div>`).join('');
    const wrongs = sum.wrong.length
      ? `<div class="gsum-wrong"><div class="gsum-sub">错题（点一下跳到那题）</div>${sum.wrong.map(i=> `<button type="button" class="gsum-chip" data-goto="${i}">第 ${items[i].n} 题</button>`).join('')}</div>`
      : '<div class="gsum-allright">🎉 全对！</div>';
    return `<div class="score-card ${sum.pct >= 80 ? 'pass' : 'fail'}">
      <div class="score-num mono">${sum.correct} / ${sum.total}</div>
      <div>本套正确率 ${sum.pct}%${sum.blank ? ` · 有 ${sum.blank} 题没作答（算错）` : ''}</div></div>
      <div class="gsum-card"><div class="gsum-sub">分题型</div>${kinds}</div>
      ${wrongs}
      <div class="gsum-btns">
        ${sum.wrong.length ? '<button type="button" class="btn-ghost" data-act="only-wrong">只看错题</button>' : ''}
        <button type="button" class="btn-primary" data-act="redo">重做本套</button>
      </div>`;
  }

  async function onSubmit(){
    if(revealed || saving) return;
    items.forEach((_, i)=> readOne(i));
    const missing = items.filter((it, i)=> !isAnswered(it, answers[i])).length;
    if(missing && !warned){
      warned = true;
      let w = $('.gset-warn');
      if(!w){ w = document.createElement('div'); w.className = 'gset-warn form-error'; countEl.closest('.gbar').before(w); }
      w.textContent = `还有 ${missing} 题没做完，没答的算错。想继续做就接着做；确定就再点一次「提交」。`;
      return;
    }
    saving = true; submitBtn.disabled = true;
    const sum = reveal();
    sumEl.scrollIntoView({behavior:'smooth', block:'start'});
    try{
      const pr = await submitPractice(T.cols, course, unit, answers.slice(), sum);
      T.progress[key] = pr; showPrev();
      showToast(`本套 ${sum.correct} / ${sum.total}（${sum.pct}%）已保存`);
    }catch(err){
      console.error(err);
      showToast('成绩没保存成功：' + (err.message || '请检查网络'));
    }finally{ saving = false; submitBtn.disabled = false; }
  }

  function redo(){
    revealed = false; warned = false; answers = items.map(()=> '');
    box.classList.remove('revealed', 'only-wrong');
    items.forEach((it, i)=>{
      const sec = box.querySelector(`#gq-${i}`);
      sec.classList.remove('right', 'wrong');
      sec.querySelector('.gq-verdict').textContent = '';
      const ex = sec.querySelector('.gq-explain'); ex.hidden = true; ex.innerHTML = '';
      sec.querySelectorAll('.qopt').forEach(l=>{ l.classList.remove('correct', 'chosen-wrong'); l.querySelector('.gopt-tag').textContent = ''; });
    });
    box.querySelectorAll('input').forEach(x=>{ x.disabled = false; x.checked = false; if(x.type === 'text') x.value = ''; });
    sumEl.hidden = true; sumEl.innerHTML = '';
    $('#gbar').hidden = false; updateCount(); showPrev();
    window.scrollTo({top:0, behavior:'smooth'});
  }

  function showPrev(){
    const pr = T.progress[key];
    const last = pr && pr.practiceLast;
    if(!last){ prevEl.hidden = true; return; }
    prevEl.hidden = false;
    prevEl.innerHTML = `<span>上次提交 <b>${last.correct} / ${last.total}</b> · 最高 ${pr.practiceBest} · 做过 ${pr.practiceAttempts} 次</span><button type="button" class="btn-ghost" data-act="view-last">查看上次作答</button>`;
  }

  box.addEventListener('click', e=>{
    const t = e.target.closest && e.target.closest('button');
    if(!t) return;
    if(t.classList.contains('gbar-submit')) onSubmit();
    else if(t.dataset.act === 'redo') redo();
    else if(t.dataset.act === 'only-wrong'){ box.classList.toggle('only-wrong'); t.textContent = box.classList.contains('only-wrong') ? '显示全部题' : '只看错题'; }
    else if(t.dataset.act === 'view-last'){
      if(revealed) return;
      const last = T.progress[key].practiceLast;
      answers = items.map((_, i)=> String((last.answers || [])[i] || ''));
      paint(); updateCount(); reveal(); sumEl.scrollIntoView({behavior:'smooth', block:'start'});
    }
    else if(t.dataset.goto !== undefined){
      const el = box.querySelector(`#gq-${t.dataset.goto}`);
      if(el) el.scrollIntoView({behavior:'smooth', block:'start'});
    }
  });

  box._refreshPrev = ()=>{ if(!revealed) showPrev(); };
  updateCount(); showPrev();
}
