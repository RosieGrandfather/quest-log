/* 词汇课课程页上的「不会的词」汇总：把所有小节里标了「不会」的词读出来，可复制、可下载 CSV。
   读取的是 Firestore 里同一份「会 / 不会」标记（vocab-marks.js 写入的那份），不另存数据。 */
import { T } from './state.js';
import { loadUnit } from './content.js';
import { loadVocabMarks } from '../data/study.js';
import { collectUnknown, wordsLine, wordsWithMeaning, toCSV } from '../core/vocab-export.js';
import { escapeHTML } from '../core/html.js';
import { showToast } from '../ui/common.js';

/* 哪些课程有「会 / 不会」词卡 */
const VOCAB_COURSES = ['gre-v'];
export const hasVocabExport = course => VOCAB_COURSES.includes(course.id);

export const vocabExportHTML = () => `
  <section class="vx" id="vocabExport">
    <div class="vx-head">
      <div>
        <div class="vx-title">不会的词汇</div>
        <div class="vx-sub">汇总你在所有小节里标了「不会」的词，可复制或下载</div>
      </div>
      <button type="button" class="btn-ghost" id="vxLoad">汇总</button>
    </div>
    <div class="vx-body" id="vxBody"></div>
  </section>`;

function download(name, text, type){
  const url = URL.createObjectURL(new Blob([text], {type}));
  const a = document.createElement('a');
  a.href = url; a.download = name; document.body.appendChild(a); a.click(); a.remove();
  setTimeout(()=> URL.revokeObjectURL(url), 1000);
}

async function copy(text, okMsg){
  try{ await navigator.clipboard.writeText(text); showToast(okMsg); }
  catch(e){ console.error('copy failed', e); showToast('复制失败，请改用下载 CSV'); }
}

export function wireVocabExport(root, course){
  const btn = root.querySelector('#vxLoad'), body = root.querySelector('#vxBody');
  if(!btn || !body) return;
  btn.addEventListener('click', async ()=>{
    btn.disabled = true; btn.textContent = '读取中…'; body.innerHTML = '';
    try{
      const metas = course.units.filter(u=> u.file);
      // 所有小节的标记并行读取；只有标过「不会」的小节才去读它的词卡内容
      const marksList = await Promise.all(metas.map(m=> loadVocabMarks(T.cols, course, m)));
      const units = [];
      for(let i=0; i<metas.length; i++){
        const marks = marksList[i];
        if(!Object.values(marks).includes('unknown')) continue;
        const { unit } = await loadUnit(course.id, metas[i].id);
        const items = unit ? unit.blocks.filter(b=> b.type==='vocab').flatMap(b=> b.items) : [];
        units.push({id:metas[i].id, title:metas[i].title, marks, items});
      }
      const rows = collectUnknown(units);
      if(!rows.length){ body.innerHTML = '<div class="vx-empty">还没有标过「不会」的词。</div>'; return; }
      const nUnits = new Set(rows.map(r=> r.unitId)).size;
      body.innerHTML = `
        <div class="vx-count">共 <b class="mono">${rows.length}</b> 个词，来自 ${nUnits} 节</div>
        <div class="vx-actions">
          <button type="button" class="btn-ghost" data-act="words">复制单词</button>
          <button type="button" class="btn-ghost" data-act="meaning">复制单词+释义</button>
          <button type="button" class="btn-ghost" data-act="csv">下载 CSV</button>
        </div>
        <div class="vx-list">${rows.map(r=>`
          <div class="vx-row"><span class="vx-w">${escapeHTML(r.w)}</span>
            <span class="vx-pos">${escapeHTML(r.pos)}</span>
            <span class="vx-zh">${escapeHTML(r.zh)}</span>
            <span class="vx-u">${escapeHTML(r.unit)}</span></div>`).join('')}</div>`;
      body.querySelector('.vx-actions').addEventListener('click', e=>{
        const act = e.target.closest('button')?.dataset.act;
        if(act === 'words') copy(wordsLine(rows), `已复制 ${rows.length} 个单词`);
        else if(act === 'meaning') copy(wordsWithMeaning(rows), `已复制 ${rows.length} 个词和释义`);
        else if(act === 'csv') download('gre-v-不会的词.csv', toCSV(rows), 'text/csv;charset=utf-8');
      });
    }catch(e){
      console.error('vocab export failed', e);
      body.innerHTML = '<div class="vx-empty">读取失败，请检查网络后再点一次。</div>';
    }finally{
      btn.disabled = false; btn.textContent = '重新汇总';
    }
  });
}
