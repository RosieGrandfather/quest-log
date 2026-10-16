/* 官方 Quant 练习套题（block type = 'gre-qset'）：题目是原书截图，下面放作答区。
   做完所有题 → 点「提交」→ 才显示每题对错 + 官方解析（截图）+ 本套总结。判分在 js/core/qgrade.js。 */
import { T } from './state.js';
import { escapeHTML } from '../core/html.js';
import { QKIND_LABEL, QC_TEXT, isAnswered, gradeItem, summarize, answerText, pickedText, isMulti, isGraded, sentenceChoices } from '../core/qgrade.js';
import { unitKey } from '../core/study.js';
import { submitPractice } from '../data/study.js';
import { showToast } from '../ui/common.js';

const L = 'ABCDEFGH';
const img = (b, p, w, cls = '')=> `<img class="qimg ${cls}" src="${escapeHTML(b.base + p)}" ${w ? `style="width:${Math.round(w / 2)}px"` : ''} alt="" loading="lazy">`;
const BLK = ['(i)', '(ii)', '(iii)'];
const tx = t => escapeHTML(t).replace(/____/g, '<span class="qbl"></span>');
const paraHTML = arr => (arr || []).map(x=> `<p>${tx(x)}</p>`).join('');
const hintOf = it => it.kind === 'qc' ? '比较 Quantity A 和 Quantity B，选一项'
  : it.kind === 'mc1' ? '选一项'
  : it.kind === 'mcn' ? '选出所有正确的选项（可能不止一个）'
  : it.kind === 'se' ? '选两个答案：填进去句子通顺，而且两个句子意思相近（选项自上而下是 A–F）'
  : it.kind === 'tc' ? `${it.blanks} 个空，每个空各选一项（每列自上而下是 A、B、C）`
  : it.kind === 'ss' ? (sentenceChoices(it).length ? '点击文章中的一句话作答；点击其他句子可更换。交卷后自评，不计入分数' : '在原文里找出符合题意的那一句；下面写它的序号或开头几个词。这类题交卷后对照答案自评，不计入分数')
  : it.frac ? '分数作答：上面填分子，下面填分母' : '在框里填一个数（可以带小数点；逗号、% 不用管）';

function controlsHTML(it, i){
  if(it.kind === 'ne'){
    return it.frac
      ? `<div class="qne frac"><input type="text" inputmode="numeric" autocomplete="off" data-part="0" aria-label="分子"><span class="qbar"></span><input type="text" inputmode="numeric" autocomplete="off" data-part="1" aria-label="分母"></div>`
      : `<div class="qne"><input type="text" inputmode="decimal" autocomplete="off" aria-label="答案"></div>`;
  }
  if(it.kind === 'ss') return sentenceChoices(it).length ? '' : `<div class="qne ss"><input type="text" autocomplete="off" placeholder="例：第 3 句 / But, in addition…" aria-label="你选的句子"></div>`;
  if(it.kind === 'tc'){
    return `<div class="qtc">${Array.from({length: it.blanks}, (_, j)=>
      `<div class="qblank"><span class="qblank-no">空 ${BLK[j]}</span><div class="qopts tc">${[0, 1, 2].map(k=>
        `<label class="qopt" data-k="${k}" data-b="${j}"><input type="radio" name="q${i}_${j}" value="${k}"><span class="qletter">${L[k]}</span>${it.txt && it.txt.cols ? `<span class="qtext">${tx(it.txt.cols[j][k])}</span>` : ''}<span class="gopt-tag"></span></label>`).join('')}</div></div>`).join('')}</div>`;
  }
  const type = isMulti(it) ? 'checkbox' : 'radio';
  const n = it.kind === 'qc' ? 4 : it.nopt;
  const hasT = !!(it.txt && it.txt.opts);
  return `<div class="qopts ${it.kind}${hasT ? ' has-txt' : ''}">${Array.from({length: n}, (_, k)=>
    `<label class="qopt" data-k="${k}"><input type="${type}" name="q${i}" value="${k}"><span class="qletter">${L[k]}</span>${it.kind === 'qc' ? `<span class="qtext">${QC_TEXT[k]}</span>` : hasT ? `<span class="qtext">${tx(it.txt.opts[k])}</span>` : ''}<span class="gopt-tag"></span></label>`).join('')}</div>`;
}

const origImgs = (it, b)=> (it.imgs || [it.img]).map((p, j)=> `${j ? '<div class="qscroll-tag">↓ 同一题，原文往下滚动后的画面</div>' : ''}${img(b, p, it.w, 'qstem')}`).join('');

function textHTML(it, i){
  const sentences = sentenceChoices(it);
  const stem = `<div class="qstemtxt">${paraHTML(it.txt.stem)}</div>`;
  if(sentences.length){
    return `${stem}<div class="qpass qsentence-pass"><div class="vp-tag">文章 · 点击一句话作答</div><div class="qsentences" role="radiogroup" aria-label="第 ${it.n} 题：选择文章中的一句话"><p>${sentences.map((s, j)=>
      `<label class="qsentence"><input type="radio" name="q${i}_sentence" value="${escapeHTML(s)}" aria-label="第 ${j + 1} 句：${escapeHTML(s)}"><span>${tx(s)}</span></label>`).join(' ')}</p></div></div>`;
  }
  return `${it.txt.pass ? `<div class="qpass"><div class="vp-tag">文章</div>${paraHTML(it.txt.pass)}</div>` : ''}${stem}`;
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
    ${it.txt ? `<div class="qtxt">${textHTML(it, i)}</div>
    <details class="qorig"><summary>看原图（文字有出入时对照）</summary>${origImgs(it, b)}</details>` : origImgs(it, b)}
    <div class="gq-hint">${hintOf(it)}${it.answerPending ? ' · 原答案待核对，本题暂不计分' : ''}</div>
    ${controlsHTML(it, i)}
    <div class="gq-explain" hidden></div>
  </section>`;
}

export function qsetHTML(b){
  return `<div class="gset qset" data-n="${b.items.length}">
    <div class="gset-source">来源：${escapeHTML(b.source)}${escapeHTML(b.noteTail ?? '（官方原题与解析的截图，仅供个人学习；原书没有标难度）')}</div>
    <div class="gset-prev" hidden></div>
    ${b.items.map((it, i)=> itemHTML(it, i, b)).join('')}
    <div class="gbar" id="gbar"><span class="gbar-count"></span><button type="button" class="btn-primary gbar-submit">提交</button></div>
    <div class="gsummary" hidden></div>
  </div>`;
}

/* 点题图放大：全屏遮罩，再点图片在「适合屏幕」和「放大 2 倍（可滚动）」间切换；点空白处 / ✕ / Esc 关闭 */
function openZoom(src){
  const ov = document.createElement('div');
  ov.className = 'qzoom';
  ov.setAttribute('role', 'dialog'); ov.setAttribute('aria-label', '原图放大');
  ov.innerHTML = `<button type="button" class="qzoom-x" aria-label="关闭">✕</button><div class="qzoom-hint">点图片：放大 / 还原　·　点空白处或按 Esc 关闭</div><div class="qzoom-box"><img src="${escapeHTML(src)}" alt=""></div>`;
  const prevOverflow = document.body.style.overflow;
  const close = ()=> { ov.remove(); document.body.style.overflow = prevOverflow; document.removeEventListener('keydown', onKey, true); };
  const onKey = e=> { if(e.key === 'Escape'){ e.stopPropagation(); close(); } };
  ov.addEventListener('click', e=> {
    if(e.target.tagName === 'IMG') ov.classList.toggle('big');
    else close();
  });
  document.addEventListener('keydown', onKey, true);
  document.body.style.overflow = 'hidden';
  document.body.appendChild(ov);
  ov.querySelector('.qzoom-x').focus();
}

export function wireQset(root, course, unit){
  const box = root && root.querySelector('.qset');
  if(!box) return;
  box.addEventListener('click', e=> { const im = e.target.closest && e.target.closest('img.qimg'); if(im) openZoom(im.currentSrc || im.src); });
  const b = unit.blocks.find(x=> x.type === 'gre-qset');
  const items = b.items;
  const key = unitKey(course.id, unit.id);
  let answers = items.map(()=> '');
  let revealed = false, warned = false, saving = false;
  const $ = s => box.querySelector(s);
  const countEl = $('.gbar-count'), submitBtn = $('.gbar-submit'), sumEl = $('.gsummary'), prevEl = $('.gset-prev');

  const readOne = i => {
    const it = items[i], sec = box.querySelector(`#gq-${i}`);
    if(it.kind === 'tc'){
      answers[i] = Array.from({length: it.blanks}, (_, j)=> { const c = sec.querySelector(`input[name="q${i}_${j}"]:checked`); return c ? c.value : ''; }).join(',');
      if(/^,*$/.test(answers[i])) answers[i] = '';
    } else if(it.kind === 'ss') answers[i] = sentenceChoices(it).length
      ? (sec.querySelector('.qsentence input:checked')?.value || '') : sec.querySelector('.qne input').value.trim();
    else if(it.kind === 'ne'){
      const ins = [...sec.querySelectorAll('.qne input')].map(x=> x.value.trim());
      answers[i] = it.frac ? (ins[0] || ins[1] ? `${ins[0]}/${ins[1]}` : '') : ins[0];
    } else answers[i] = [...sec.querySelectorAll('input:checked')].map(x=> x.value).join(',');
  };
  const paint = ()=> items.forEach((it, i)=>{
    const sec = box.querySelector(`#gq-${i}`), a = answers[i] || '';
    if(it.kind === 'tc'){
      const p = a.split(',');
      sec.querySelectorAll('input').forEach(x=>{ const j = Number(x.name.split('_')[1]); x.checked = p[j] === x.value; });
    } else if(it.kind === 'ss'){
      if(sentenceChoices(it).length) sec.querySelectorAll('.qsentence input').forEach(x=>{ x.checked = x.value === a; });
      else sec.querySelector('.qne input').value = a;
    }
    else if(it.kind === 'ne'){
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
    if(items[Number(sec.dataset.i)].kind === 'se' && sec.querySelectorAll('input:checked').length > 2){
      e.target.checked = false;
      showToast('这题请选择两个答案；先取消一个选项再更换');
    }
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
      if(isGraded(it)){
        sec.classList.add(ok ? 'right' : 'wrong');
        sec.querySelector('.gq-verdict').textContent = ok ? '✓ 答对' : blank ? '✗ 没作答' : '✗ 答错';
      } else sec.querySelector('.gq-verdict').textContent = it.answerPending ? '答案待核对，不计分' : '对照答案自评';
      if(isGraded(it) && it.kind === 'tc'){
        const got = a.split(',');
        sec.querySelectorAll('.qopt').forEach(lab=>{
          const k = Number(lab.dataset.k), j = Number(lab.dataset.b), isC = it.ans[j] === k, picked = got[j] === String(k);
          lab.classList.toggle('correct', isC);
          lab.classList.toggle('chosen-wrong', picked && !isC);
          lab.querySelector('.gopt-tag').textContent = isC && picked ? '✓ 你选对了' : isC ? '正确答案' : picked ? '你的选择' : '';
        });
      } else if(isGraded(it) && it.kind !== 'ne' && it.kind !== 'ss'){
        const got = a.split(',');
        sec.querySelectorAll('.qopt').forEach(lab=>{
          const k = Number(lab.dataset.k), isC = it.ans.includes(k), picked = got.includes(String(k));
          lab.classList.toggle('correct', isC);
          lab.classList.toggle('chosen-wrong', picked && !isC);
          lab.querySelector('.gopt-tag').textContent = isC && picked ? '✓ 你选对了' : isC ? '正确答案' : picked ? '你的选择' : '';
        });
      }
      const ex = sec.querySelector('.gq-explain');
      ex.innerHTML = `<div class="gq-answer"><span>${!isGraded(it) ? '参考答案' : '正确答案'}：<b>${escapeHTML(answerText(it))}</b></span><span class="${!isGraded(it) ? '' : ok ? 'ok' : 'bad'}">你的答案：<b>${escapeHTML(pickedText(it, a))}</b></span></div>
        ${it.explanation ? `<div class="explain"><strong>答案依据（独立复核）</strong><p>${escapeHTML(it.explanation)}</p></div>` : ''}
        ${it.exp ? `<div class="explain"><strong>官方解析（英文原文截图）</strong>${img(b, it.exp, it.ew, 'qexp')}</div>` : ''}`;
      ex.hidden = false;
    });
    $('#gbar').hidden = true;
    const sum = summarize(items, answers);
    sumEl.innerHTML = summaryHTML(sum); sumEl.hidden = false;
    return sum;
  }

  function summaryHTML(sum){
    const kinds = Object.entries(sum.byKind).map(([k, v])=> `<div class="gsum-row"><span>${QKIND_LABEL[k]}</span><b>${v.correct} / ${v.total}</b><span class="gsum-pct">${Math.round(v.correct / v.total * 100)}%</span></div>`).join('');
    const selfc = sum.selfCheck && sum.selfCheck.length
      ? `<div class="gsum-card"><div class="gsum-sub">自评或答案待核对的题目（不计分）</div>${sum.selfCheck.map(i=> `<button type="button" class="gsum-chip" data-goto="${i}">第 ${items[i].n} 题</button>`).join('')}</div>` : '';
    const wrongs = sum.wrong.length
      ? `<div class="gsum-wrong"><div class="gsum-sub">错题（点一下跳到那题）</div>${sum.wrong.map(i=> `<button type="button" class="gsum-chip" data-goto="${i}">第 ${items[i].n} 题</button>`).join('')}</div>`
      : '<div class="gsum-allright">🎉 全对！</div>';
    return `<div class="score-card ${sum.pct >= 80 ? 'pass' : 'fail'}">
      <div class="score-num mono">${sum.correct} / ${sum.total}</div>
      <div>本套正确率 ${sum.pct}%${sum.blank ? ` · 有 ${sum.blank} 题没作答（算错）` : ''}</div></div>
      <div class="gsum-card"><div class="gsum-sub">分题型</div>${kinds}</div>
      ${wrongs}
      ${selfc}
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
    if(unit.answerFormat && last.answerFormat !== unit.answerFormat){
      prevEl.innerHTML = '<span>旧版成绩已保留。题目内容或答案已校正，请重新作答。</span>';
      return;
    }
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
      if(unit.answerFormat && last.answerFormat !== unit.answerFormat) return;
      answers = items.map((it, i)=>{
        const saved = String((last.answers || [])[i] || '');
        // 旧版 A–E 下标不能当作改版后所选句子。
        return sentenceChoices(it).length && !sentenceChoices(it).includes(saved) ? '' : saved;
      });
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
