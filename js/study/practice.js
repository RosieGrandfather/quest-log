/* 官方练习套题（block type = 'gre-set'）：做完所有题 → 点「提交」→ 才显示每题对错 + 解析 + 本套总结。
   页面只负责显示；判分在 js/core/practice.js，成绩存在 studyProgress 文档的 practice* 字段里。 */
import { T } from './state.js';
import { escapeHTML } from '../core/html.js';
import { KIND_LABEL, DIFF_LABEL, isAnswered, gradeItem, encodeSel, decodeSel, summarize } from '../core/practice.js';
import { unitKey } from '../core/study.js';
import { submitPractice } from '../data/study.js';
import { showToast } from '../ui/common.js';

const LETTERS = 'ABCDEFGHIJ';
const paras = (text, cls = '')=> String(text || '').split(/\n\s*\n/).filter(s=> s.trim()).map(p=> `<p${cls ? ` class="${cls}"` : ''}>${escapeHTML(p.trim())}</p>`).join('');
const stemHTML = s => escapeHTML(s).replace(/______/g, '<span class="gblank" aria-label="空格"></span>');

function hintOf(it){
  const g = it.groups;
  if(it.kind === 'se') return '选出两个答案：分别填入空格后，两个句子都通顺且意思相近';
  if(it.kind === 'tc') return g.length > 1 ? '每个空各选一项' : '选一项';
  return g[0].pick === 'any' ? '逐项判断：选出所有正确的选项（可能不止一个）' : '选一项';
}

/* 每道题的选项字母：同一题里连续编号（A B C / D E F），和原书一致 */
function letterBase(it){ let n = 0; return it.groups.map(g=>{ const b = n; n += g.options.length; return b; }); }

function itemHTML(it, i, b, spans){
  const bases = letterBase(it);
  let passage = '';
  if(it.passage){
    const [a, z] = spans[it.passage];
    const range = a === z ? `第 ${a} 题` : `第 ${a}–${z} 题共用`;
    passage = i + 1 === a
      ? `<div class="gq-passage"><div class="vp-tag">阅读文章 · ${range}${'' /* 原书行号未保留：题干里的 line N 请用引号里的词定位 */}</div>${paras(b.passages[it.passage])}</div>`
      : `<details class="gq-passage gq-again"><summary>再看一遍文章（${range}）</summary>${paras(b.passages[it.passage])}</details>`;
  }
  const groups = it.groups.map((g, j)=>{
    const type = g.pick === 1 ? 'radio' : 'checkbox';
    return `<div class="gq-group" data-j="${j}" data-pick="${g.pick}">
      ${g.label ? `<div class="gq-grouplabel">${escapeHTML(g.label)}</div>` : ''}
      ${g.options.map((o, k)=>`<label class="gopt" data-k="${k}"><input type="${type}" name="g${i}_${j}" value="${k}"><span class="gopt-letter">${LETTERS[bases[j] + k]}</span><span class="gopt-text">${escapeHTML(o)}</span><span class="gopt-tag"></span></label>`).join('')}
    </div>`;
  }).join('');
  return `${passage}<section class="gq" id="gq-${i}" data-i="${i}">
    <div class="gq-head"><span class="q-no">${i + 1}</span><span class="gq-kind">${KIND_LABEL[it.kind]}</span><span class="gq-verdict"></span></div>
    <div class="gq-stem">${stemHTML(it.stem)}</div>
    <div class="gq-hint">${hintOf(it)}</div>
    <div class="gq-groups${it.groups.length > 1 ? ' multi' : ''}">${groups}</div>
    <div class="gq-explain" hidden></div>
  </section>`;
}

export function practiceHTML(b){
  const spans = {};
  b.items.forEach((it, i)=>{ if(it.passage){ const s = spans[it.passage] || (spans[it.passage] = [i + 1, i + 1]); s[1] = i + 1; } });
  return `<div class="gset" data-n="${b.items.length}">
    <div class="gset-source">来源：${escapeHTML(b.source)}（官方原题与解析，仅供个人学习；难度照原书标注：${DIFF_LABEL[b.difficulty] || ''}）</div>
    <div class="gset-prev" hidden></div>
    <div class="gset-note">先把全部 ${b.items.length} 题做完，再点最下面的「提交」——提交前不会显示对错。阅读题里的 line N 指原书的行号，本页没有行号，用引号里的词在文章里找就行。</div>
    ${b.items.map((it, i)=> itemHTML(it, i, b, spans)).join('')}
    <div class="gbar" id="gbar"><span class="gbar-count"></span><button type="button" class="btn-primary gbar-submit">提交</button></div>
    <div class="gsummary" hidden></div>
  </div>`;
}

const explainHTML = (it, sel, ok)=>{
  const bases = letterBase(it);
  const fmt = pick => it.groups.map((g, j)=>{
    const ls = (pick[j] || []).slice().sort((x, y)=> x - y).map(k=> LETTERS[bases[j] + k]).join('、') || '未作答';
    return (it.groups.length > 1 ? `${g.label}：` : '') + ls;
  }).join('；');
  return `<div class="gq-answer"><span>正确答案：<b>${escapeHTML(fmt(it.groups.map(g=> g.correct)))}</b></span><span class="${ok ? 'ok' : 'bad'}">你的答案：<b>${escapeHTML(fmt(sel))}</b></span></div>
    <div class="explain"><strong>官方解析（英文原文）</strong>${paras(it.expl)}</div>`;
};

export function wirePractice(root, course, unit){
  const box = root && root.querySelector('.gset');
  if(!box) return;
  const b = unit.blocks.find(x=> x.type === 'gre-set');
  const items = b.items;
  const key = unitKey(course.id, unit.id);
  const sels = items.map(it=> it.groups.map(()=> []));
  let revealed = false, warned = false, saving = false;
  const $ = s => box.querySelector(s);
  const countEl = $('.gbar-count'), submitBtn = $('.gbar-submit'), sumEl = $('.gsummary'), prevEl = $('.gset-prev');

  const readSels = ()=> items.forEach((it, i)=> it.groups.forEach((g, j)=>{
    sels[i][j] = [...box.querySelectorAll(`input[name="g${i}_${j}"]:checked`)].map(x=> Number(x.value));
  }));
  const updateCount = ()=>{
    const done = items.filter((it, i)=> isAnswered(it, sels[i])).length;
    countEl.textContent = `已做 ${done} / ${items.length}`;
    countEl.classList.toggle('full', done === items.length);
  };
  const paintInputs = ()=> items.forEach((it, i)=> it.groups.forEach((g, j)=>{
    box.querySelectorAll(`input[name="g${i}_${j}"]`).forEach(x=>{ x.checked = sels[i][j].includes(Number(x.value)); });
  }));

  box.addEventListener('change', e=>{
    const inp = e.target.closest && e.target.closest('input');
    if(!inp || revealed) return;
    const grp = inp.closest('.gq-group');
    if(grp.dataset.pick === '2' && grp.querySelectorAll('input:checked').length > 2){
      inp.checked = false; showToast('这题只选两项：先取消一个再选'); return;
    }
    readSels(); updateCount(); warned = false; $('.gset-warn') && $('.gset-warn').remove();
  });

  function reveal(){
    revealed = true;
    box.classList.add('revealed');
    box.querySelectorAll('input').forEach(x=>{ x.disabled = true; });
    items.forEach((it, i)=>{
      const sec = box.querySelector(`#gq-${i}`);
      const ok = gradeItem(it, sels[i]);
      const blank = !isAnswered(it, sels[i]);
      sec.classList.add(ok ? 'right' : 'wrong');
      sec.querySelector('.gq-verdict').textContent = ok ? '✓ 答对' : blank ? '✗ 没作答' : '✗ 答错';
      it.groups.forEach((g, j)=>{
        sec.querySelectorAll(`.gq-group[data-j="${j}"] .gopt`).forEach(lab=>{
          const k = Number(lab.dataset.k), isC = g.correct.includes(k), picked = sels[i][j].includes(k);
          lab.classList.toggle('correct', isC);
          lab.classList.toggle('chosen-wrong', picked && !isC);
          lab.querySelector('.gopt-tag').textContent = isC && picked ? '✓ 你选对了' : isC ? '正确答案' : picked ? '你的选择' : '';
        });
      });
      const ex = sec.querySelector('.gq-explain');
      ex.innerHTML = explainHTML(it, sels[i], ok); ex.hidden = false;
    });
    $('#gbar').hidden = true;
    const sum = summarize(items, sels);
    sumEl.innerHTML = summaryHTML(b, sum);
    sumEl.hidden = false;
    return sum;
  }

  function summaryHTML(b, sum){
    const kinds = Object.entries(sum.byKind).map(([k, v])=> `<div class="gsum-row"><span>${KIND_LABEL[k]}</span><b>${v.correct} / ${v.total}</b><span class="gsum-pct">${Math.round(v.correct / v.total * 100)}%</span></div>`).join('');
    const wrongs = sum.wrong.length
      ? `<div class="gsum-wrong"><div class="gsum-sub">错题（点一下跳到那题）</div>${sum.wrong.map(i=> `<button type="button" class="gsum-chip" data-goto="${i}">第 ${i + 1} 题</button>`).join('')}</div>`
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
    readSels();
    const missing = items.filter((it, i)=> !isAnswered(it, sels[i])).length;
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
      const pr = await submitPractice(T.cols, course, unit, sels.map(encodeSel), sum);
      T.progress[key] = pr; showPrev();
      showToast(`本套 ${sum.correct} / ${sum.total}（${sum.pct}%）已保存`);
    }catch(err){
      console.error(err);
      showToast('成绩没保存成功：' + (err.message || '请检查网络'));
    }finally{ saving = false; submitBtn.disabled = false; }
  }

  function redo(){
    revealed = false; warned = false;
    box.classList.remove('revealed', 'only-wrong');
    items.forEach((it, i)=>{
      sels[i] = it.groups.map(()=> []);
      const sec = box.querySelector(`#gq-${i}`);
      sec.classList.remove('right', 'wrong');
      sec.querySelector('.gq-verdict').textContent = '';
      const ex = sec.querySelector('.gq-explain'); ex.hidden = true; ex.innerHTML = '';
      sec.querySelectorAll('.gopt').forEach(l=>{ l.classList.remove('correct', 'chosen-wrong'); l.querySelector('.gopt-tag').textContent = ''; });
    });
    box.querySelectorAll('input').forEach(x=>{ x.disabled = false; x.checked = false; });
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
      items.forEach((it, i)=>{ sels[i] = decodeSel(last.answers[i], it); });
      paintInputs(); updateCount(); reveal(); sumEl.scrollIntoView({behavior:'smooth', block:'start'});
    }
    else if(t.dataset.goto !== undefined){
      const el = box.querySelector(`#gq-${t.dataset.goto}`);
      if(el) el.scrollIntoView({behavior:'smooth', block:'start'});
    }
  });

  box._refreshPrev = ()=>{ if(!revealed) showPrev(); };    // 进度文档晚到时，views.js 会叫它刷新「上次提交」
  updateCount(); showPrev();
}
