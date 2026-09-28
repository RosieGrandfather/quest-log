/* 每节一篇笔记：点「📝 笔记」弹出抽屉，边打字边自动保存（停手 0.8 秒后存） */
import { T } from './state.js';
import { saveNote, loadNote } from '../data/study.js';
import { closeOnBackdrop } from '../ui/common.js';

let current = null;   // {course, unit}
let timer = null;
let dirty = false;

const $ = id => document.getElementById(id);
const setStatus = s => { $('noteStatus').textContent = s; };

async function flush(){
  clearTimeout(timer);
  if(!dirty || !current) return;
  dirty = false;
  const { course, unit } = current;
  setStatus('保存中…');
  try{ await saveNote(T.cols, course, unit, $('noteText').value); setStatus('已保存 ✓'); }
  catch(e){ dirty = true; setStatus('保存失败，会自动重试'); console.error('save note failed', e); timer = setTimeout(flush, 3000); }
}

export async function openNotes(course, unit){
  current = {course, unit};
  $('noteUnitTitle').textContent = unit.title;
  $('noteText').value = '';
  $('noteText').disabled = true;
  setStatus('读取中…');
  $('notesDrawer').hidden = false;
  try{
    $('noteText').value = await loadNote(T.cols, course, unit);
    setStatus($('noteText').value ? '已同步' : '还没有笔记，写点什么吧');
  }catch(e){ setStatus('读取失败'); console.error(e); }
  $('noteText').disabled = false;
  $('noteText').focus();
}

async function closeNotes(){
  await flush();
  $('notesDrawer').hidden = true;
  current = null;
}

export function wireNotes(){
  $('noteText').addEventListener('input', ()=>{
    dirty = true;
    setStatus('正在输入…');
    clearTimeout(timer);
    timer = setTimeout(flush, 800);
  });
  $('closeNotes').addEventListener('click', closeNotes);
  closeOnBackdrop('notesDrawer', closeNotes);
  // 切到后台 / 关页面前把没存的存掉
  document.addEventListener('visibilitychange', ()=>{ if(document.hidden) flush(); });
  window.addEventListener('pagehide', flush);
}

export const notesOpen = () => !$('notesDrawer').hidden;
export { closeNotes };
