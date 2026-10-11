/* 写作练习（block type = 'gre-essay'）：题目 + 30 分钟计时 + 打字区（自动保存）→ 写完后看官方评分标准、6–1 分样文和阅卷评语。
   样文和评语都是 ETS 官方英文原文；这里不打分，对照着自己看（想要批改可以把文章贴给 Claude）。 */
import { T } from './state.js';
import { escapeHTML } from '../core/html.js';
import { unitKey } from '../core/study.js';
import { saveEssay, loadEssay } from '../data/study.js';
import { showToast } from '../ui/common.js';

const paras = (arr, cls = '')=> (arr || []).map(p=> `<p${cls ? ` class="${cls}"` : ''}>${escapeHTML(p)}</p>`).join('');
const words = t => (String(t || '').trim().match(/\S+/g) || []).length;
const KIND = {
  issue: {zh: 'Issue（议论文）', tip: '要表明并论证你自己的立场；题目指令里的每一句（比如「考虑什么时候成立、什么时候不成立」）都要回应到。'},
  argument: {zh: 'Argument（论证分析）', tip: '不要写你同不同意；只评价这段论证的推理：找出它依赖的假设、缺的证据，说明这些怎样削弱或加强结论。'},
};
const fmtTime = s => `${String(Math.floor(s / 60)).padStart(2, '0')}:${String(s % 60).padStart(2, '0')}`;

export function essayHTML(b){
  const k = KIND[b.kind];
  const resp = b.responses.map((r, i)=> `<section class="aw-resp" data-score="${r.score}"${i ? ' hidden' : ''}>
      <div class="aw-resp-head"><b>${r.score} 分样文</b><span class="aw-wc">${r.essay.reduce((n, p)=> n + words(p), 0)} 词</span></div>
      <div class="aw-essay">${paras(r.essay)}</div>
      <div class="explain"><strong>阅卷评语（Reader Commentary，英文原文）</strong>${paras(r.commentary)}</div></section>`).join('');
  return `<div class="gset aw" data-kind="${b.kind}">
    <div class="gset-source">来源：${escapeHTML(b.source)}（官方题目、样文与评语，仅供个人学习）</div>
    <section class="aw-prompt"><div class="vp-tag">${k.zh} · 限时 30 分钟</div>${paras(b.prompt)}<p class="aw-tip">${k.tip}</p></section>
    <section class="aw-write">
      <div class="aw-bar">
        <span class="aw-timer mono" id="awTimer">30:00</span>
        <button type="button" class="btn-ghost" data-act="start">开始计时</button>
        <button type="button" class="btn-ghost" data-act="reset" hidden>重置</button>
        <span class="aw-wcnt mono" id="awCount">0 词</span>
        <span class="aw-save" id="awSave"></span>
      </div>
      <textarea id="awText" class="aw-text" rows="18" spellcheck="true" placeholder="在这里打字。自动保存，关掉页面再回来还在。"></textarea>
      <div class="gset-warn form-error" id="awWarn" hidden></div>
      <button type="button" class="btn-primary" data-act="finish">写完了，看官方评分标准和样文</button>
    </section>
    <div class="aw-review" id="awReview" hidden>
      <div class="gsum-card"><div class="gsum-sub">你这篇</div><div id="awMine"></div></div>
      ${b.strategy.length ? `<details class="gq-passage"><summary>官方思路提示（Strategies for This Topic）</summary>${paras(b.strategy)}</details>` : ''}
      <details class="gq-passage" open><summary>官方评分标准（6–1 分）</summary>${b.rubric.map(r=> `<div class="aw-rub"><b>${r.score} 分</b> ${escapeHTML(r.summary)}<ul>${r.bullets.map(x=> `<li>${escapeHTML(x)}</li>`).join('')}</ul></div>`).join('')}</details>
      <div class="gsum-card"><div class="gsum-sub">对照 5 分标准自查（勾着玩，不保存）</div>${b.rubric.find(r=> r.score === 5).bullets.map(x=> `<label class="aw-chk"><input type="checkbox"> ${escapeHTML(x)}</label>`).join('')}</div>
      <div class="aw-tabs" role="tablist">${b.responses.map((r, i)=> `<button type="button" class="fchip${i ? '' : ' on'}" data-score="${r.score}">${r.score} 分</button>`).join('')}</div>
      ${resp}
      <p class="aw-claude">想要有人按这套标准给你的文章打分、逐段改：把文章贴给 Claude，说「按 GRE 评分标准批改」就行。</p>
    </div>
  </div>`;
}

let tick = null;
export function wireEssay(root, course, unit){
  const box = root && root.querySelector('.aw');
  if(!box) return;
  clearInterval(tick);
  const key = unitKey(course.id, unit.id), lsKey = `essay:${key}`;
  const $ = s => box.querySelector(s);
  const ta = $('#awText'), saveEl = $('#awSave'), cntEl = $('#awCount'), tEl = $('#awTimer');
  let dirty = false, timer = null, warned = false, left = 1800, running = false;

  const count = ()=>{ cntEl.textContent = `${words(ta.value)} 词`; };
  const lsGet = ()=>{ try{ return JSON.parse(localStorage.getItem(lsKey) || 'null'); }catch(e){ return null; } };
  const lsSet = ()=>{ try{ localStorage.setItem(lsKey, JSON.stringify({text: ta.value, ts: Date.now()})); }catch(e){ /* 无痕模式：只靠云端 */ } };

  async function flush(){
    clearTimeout(timer);
    if(!dirty) return;
    dirty = false; saveEl.textContent = '保存中…';
    try{ await saveEssay(T.cols, course, unit, ta.value); saveEl.textContent = '已保存 ✓'; }
    catch(e){ dirty = true; saveEl.textContent = '云端保存失败，已存在本机，会自动重试'; console.error(e); timer = setTimeout(flush, 4000); }
  }
  ta.addEventListener('input', ()=>{ count(); lsSet(); dirty = true; saveEl.textContent = '…'; clearTimeout(timer); timer = setTimeout(flush, 1200); });
  ta.addEventListener('blur', flush);

  // 先读本机的，再看云端有没有更新的
  const local = lsGet();
  if(local && local.text){ ta.value = local.text; count(); }
  loadEssay(T.cols, course, unit).then(c=>{
    if(c.text && c.ts > ((local && local.ts) || 0) && !dirty && ta.value !== c.text){ ta.value = c.text; count(); lsSet(); saveEl.textContent = '已同步 ✓'; }
  }).catch(e=> console.error('load essay failed', e));

  function paintTimer(){ tEl.textContent = fmtTime(Math.max(0, left)); tEl.classList.toggle('late', left <= 0); }
  function startStop(btn){
    if(running){ running = false; clearInterval(tick); btn.textContent = '继续计时'; return; }
    running = true; btn.textContent = '暂停'; $('[data-act="reset"]').hidden = false;
    clearInterval(tick);
    tick = setInterval(()=>{
      if(!box.isConnected){ clearInterval(tick); return; }
      left -= 1; paintTimer();
      if(left === 0) showToast('30 分钟到了：可以收尾，也可以继续写完');
    }, 1000);
  }

  box.addEventListener('click', e=>{
    const t = e.target.closest && e.target.closest('button');
    if(!t) return;
    if(t.dataset.act === 'start') startStop(t);
    else if(t.dataset.act === 'reset'){ clearInterval(tick); running = false; left = 1800; paintTimer(); const s = $('[data-act="start"]'); s.textContent = '开始计时'; t.hidden = true; }
    else if(t.dataset.act === 'finish'){
      const n = words(ta.value), warn = $('#awWarn');
      if(n < 100 && !warned){
        warned = true; warn.hidden = false;
        warn.textContent = `你现在只写了 ${n} 词。先写完再看样文效果更好（看了样文就很难再当「没看过」来练了）；确定要看就再点一次。`;
        return;
      }
      warn.hidden = true; flush();
      $('#awReview').hidden = false;
      $('#awMine').innerHTML = `${n} 词${left < 1800 ? ` · 计时用了 ${fmtTime(1800 - Math.max(0, left))}${left < 0 ? '（超时）' : ''}` : ''}。这几套样文里 5–6 分的约 380–800 词，4 分约 260–420 词（长度不决定分数，但太短一般发展不够）。`;
      clearInterval(tick); running = false;
      $('#awReview').scrollIntoView({behavior: 'smooth', block: 'start'});
    } else if(t.dataset.score){
      box.querySelectorAll('.aw-tabs .fchip').forEach(x=> x.classList.toggle('on', x === t));
      box.querySelectorAll('.aw-resp').forEach(s=>{ s.hidden = s.dataset.score !== t.dataset.score; });
    }
  });
  ta.addEventListener('input', ()=>{ warned = false; $('#awWarn').hidden = true; });
  count(); paintTimer();
}
