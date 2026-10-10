/* 词卡上的「会 / 不会」按钮：点一下标记，再点一下取消；标记存在 Firestore（跨设备同步） */
import { T } from './state.js';
import { loadVocabMarks, saveVocabMark } from '../data/study.js';
import { showToast } from '../ui/common.js';

export async function wireVocabMarks(root, course, unit){
  if(!root || !root.querySelector('.vm')) return;
  const paint = (w, v)=> root.querySelectorAll('.vm').forEach(b=>{
    if(b.dataset.w !== w) return;
    const on = b.dataset.v === v;
    b.classList.toggle('on', on); b.setAttribute('aria-pressed', on ? 'true' : 'false');
    b.closest('.vcard').dataset.mark = v || '';
  });
  const marks = {};
  try{ Object.assign(marks, await loadVocabMarks(T.cols, course, unit)); }
  catch(e){ console.error('load vocab marks failed', e); showToast('读取「会/不会」标记失败'); }
  Object.entries(marks).forEach(([w, v])=> paint(w, v));
  root.addEventListener('click', async e=>{
    const b = e.target.closest('.vm'); if(!b) return;
    const w = b.dataset.w, old = marks[w] || '';
    const v = old === b.dataset.v ? '' : b.dataset.v;     // 再点一次取消
    marks[w] = v; paint(w, v);
    try{ await saveVocabMark(T.cols, course, unit, w, v); }
    catch(err){ marks[w] = old; paint(w, old); console.error('save vocab mark failed', err); showToast('保存失败，请检查网络后再点一次'); }
  });
}
