/* 练习课课程页上的「错题本」：读每节最近一次提交（studyProgress.practiceLast），汇总答错 / 没答的题，可复制或下载 Markdown。
   不另存数据。判错逻辑在 core/mistakes.js。 */
import { T } from './state.js';
import { loadCourse, loadUnit } from './content.js';
import { unitMistakes, countByKind, toMarkdown } from '../core/mistakes.js';
import { escapeHTML } from '../core/html.js';
import { showToast } from '../ui/common.js';

export const hasMistakeExport = course => course.units.some(u=> u.practice);

export const mistakeExportHTML = () => `
  <section class="vx" id="mistakeExport">
    <div class="vx-head">
      <div>
        <div class="vx-title">错题本</div>
        <div class="vx-sub">汇总做过的小节里答错和没答的题（按每节最近一次提交），可复制或下载</div>
      </div>
      <div class="vx-actions" style="margin:0">
        <button type="button" class="btn-ghost" data-scope="course">本课错题</button>
        <button type="button" class="btn-ghost" data-scope="all">所有练习课</button>
      </div>
    </div>
    <div class="vx-body" id="mxBody"></div>
  </section>`;

function download(name, text, type){
  const url = URL.createObjectURL(new Blob([text], {type}));
  const a = document.createElement('a');
  a.href = url; a.download = name; document.body.appendChild(a); a.click(); a.remove();
  setTimeout(()=> URL.revokeObjectURL(url), 1000);
}

/* 有提交记录的小节：[{courseId, unitId}]，按课程、小节原顺序 */
async function submittedUnits(courseIds){
  const out = [];
  for(const cid of courseIds){
    const course = await loadCourse(cid);
    course.units.forEach(u=>{
      if(u.practice && u.file && T.progress[`${cid}__${u.id}`]?.practiceLast) out.push({course, meta:u});
    });
  }
  return out;
}

async function collect(scope, course){
  let ids = [course.id];
  if(scope === 'all') ids = [...new Set(Object.entries(T.progress).filter(([, p])=> p?.practiceLast).map(([, p])=> p.courseId).filter(Boolean))];
  const list = await submittedUnits(ids);
  const rows = [];
  for(const {course:c, meta} of list){
    const {unit} = await loadUnit(c.id, meta.id);
    rows.push(...unitMistakes({courseId:c.id, courseTitle:c.title, unitTitle:meta.title}, unit, T.progress[`${c.id}__${meta.id}`].practiceLast));
  }
  return {rows, nDone:list.length};
}

export function wireMistakeExport(root, course){
  const box = root.querySelector('#mistakeExport'), body = root.querySelector('#mxBody');
  if(!box || !body) return;
  box.querySelector('.vx-head').addEventListener('click', async e=>{
    const btn = e.target.closest('button[data-scope]');
    if(!btn) return;
    const scope = btn.dataset.scope, label = btn.textContent;
    btn.disabled = true; btn.textContent = '读取中…'; body.innerHTML = '';
    try{
      const {rows, nDone} = await collect(scope, course);
      if(!nDone){ body.innerHTML = '<div class="vx-empty">还没有提交过的小节。</div>'; return; }
      if(!rows.length){ body.innerHTML = `<div class="vx-empty">做过的 ${nDone} 节里没有错题。</div>`; return; }
      const now = new Date(), stamp = `${now.getFullYear()}-${String(now.getMonth()+1).padStart(2,'0')}-${String(now.getDate()).padStart(2,'0')}`;
      const title = scope === 'all' ? 'GRE 错题本（所有练习课）' : `GRE 错题本：${course.title}`;
      const md = toMarkdown(rows, {title, date:stamp});
      body.innerHTML = `
        <div class="vx-count">共 <b class="mono">${rows.length}</b> 道错题，来自做过的 ${nDone} 节；${countByKind(rows).map(([k,n])=> `${escapeHTML(k)} ${n}`).join('，')}</div>
        <div class="vx-actions">
          <button type="button" class="btn-ghost" data-act="copy">复制 Markdown</button>
          <button type="button" class="btn-ghost" data-act="md">下载 Markdown</button>
        </div>
        <div class="vx-list">${rows.map(r=>`
          <div class="vx-row"><span class="vx-w">第 ${r.n} 题</span>
            <span class="vx-pos">${escapeHTML(r.kind)}</span>
            <span class="vx-zh">你的：${escapeHTML(r.picked)} → 正确：${escapeHTML(r.correct)}</span>
            <span class="vx-u">${escapeHTML(scope === 'all' ? `${r.courseTitle} · ${r.unitTitle}` : r.unitTitle)}</span></div>`).join('')}</div>`;
      body.querySelector('.vx-actions').addEventListener('click', async ev=>{
        const act = ev.target.closest('button')?.dataset.act;
        if(act === 'md') download(`${scope === 'all' ? 'GRE-错题本' : `${course.id}-错题本`}-${stamp}.md`, md, 'text/markdown;charset=utf-8');
        else if(act === 'copy'){
          try{ await navigator.clipboard.writeText(md); showToast(`已复制 ${rows.length} 道错题`); }
          catch(err){ console.error('copy failed', err); showToast('复制失败，请改用下载'); }
        }
      });
    }catch(err){
      console.error('mistake export failed', err);
      body.innerHTML = '<div class="vx-empty">读取失败，请检查网络后再点一次。</div>';
    }finally{
      btn.disabled = false; btn.textContent = label;
    }
  });
}
