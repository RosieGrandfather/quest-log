/* 学习页记住上次读到哪：离开 / 刷新 / 关掉再开，都回到上次的位置。
   存在这台设备的浏览器里（localStorage），不同设备之间不同步。 */
import { pickAnchor, worthResuming } from '../core/resume.js';

const keyOf = id => `ql-read:${id}`;
const store = {
  get(k){ try{ return localStorage.getItem(k); }catch(e){ return null; } },
  set(k, v){ try{ localStorage.setItem(k, v); }catch(e){ /* 隐私模式等：忽略 */ } },
};
const SEL = ':scope > :not(.blk-text), :scope > .blk-text > *';
const blocksOf = lesson => [...lesson.querySelectorAll(SEL)];

let cur = null;      // {id, lesson, armed, timers}
let wired = false;
let saveTimer = 0;

function save(){
  clearTimeout(saveTimer);
  if(!cur || !cur.armed) return;
  const a = pickAnchor(blocksOf(cur.lesson).map(b=>{ const r = b.getBoundingClientRect(); return {top:r.top, bottom:r.bottom}; }));
  if(a) store.set(keyOf(cur.id), JSON.stringify({ ...a, t: Date.now() }));
}

function arm(){ if(cur) cur.armed = true; }

function onScroll(){ if(cur && cur.armed){ clearTimeout(saveTimer); saveTimer = setTimeout(save, 250); } }
function onUser(){ if(cur){ cur.userMoved = true; arm(); } }

function wire(){
  if(wired) return;
  wired = true;
  window.addEventListener('scroll', onScroll, {passive:true});
  ['wheel','touchstart','keydown','pointerdown'].forEach(ev=> window.addEventListener(ev, onUser, {passive:true}));
  document.addEventListener('visibilitychange', ()=>{ if(document.hidden) save(); });
  window.addEventListener('pagehide', save);
}

/* 离开学习页（切到别的界面）时调用 */
export function stopResume(){
  save();
  if(cur) cur.timers.forEach(clearTimeout);
  cur = null;
}

/* 学习页渲染完（代码块也处理完）后调用；返回 true 表示已跳回上次位置 */
export function startResume(id, lesson){
  stopResume();
  wire();
  cur = { id, lesson, armed:false, userMoved:false, timers:[] };
  let saved = null;
  try{ saved = JSON.parse(store.get(keyOf(id)) || 'null'); }catch(e){ saved = null; }
  const target = worthResuming(saved) ? blocksOf(lesson)[saved.i] : null;
  const jump = ()=>{
    if(!cur || cur.id !== id || cur.userMoved) return;
    window.scrollTo(0, target.getBoundingClientRect().top + window.scrollY - saved.off);
  };
  if(target){
    jump();
    // 图片 / 视频框 / 公式稍后才撑开高度，会把位置顶偏：用户还没动手时再校正两次
    cur.timers.push(setTimeout(jump, 400), setTimeout(jump, 1200));
  }
  // 程序自己滚动时不记录（否则会把存好的位置覆盖成开头），等稳定或用户一动手再开始记
  cur.timers.push(setTimeout(arm, target ? 1400 : 600));
  return !!target;
}

/* 「回到开头」：并且把记录清掉 */
export function clearResume(id){ store.set(keyOf(id), 'null'); }
