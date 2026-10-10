/* 学习页记住上次读到哪：离开 / 刷新 / 关掉再开，都回到上次的位置。
   本机存一份（localStorage，离线也能用），同时同步到 Firestore 的 readPos 集合：
   手机上读到一半，电脑上打开同一节会接着读，反过来也一样。 */
import { pickAnchor, worthResuming, newerPos } from '../core/resume.js';

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
let lastCloud = 0;
const CLOUD_EVERY = 10000;   // 滚动时云端最多每 10 秒写一次；离开页面时一定补写一次

function pushCloud(force){
  if(!cur || !cur.cols || !cur.pending) return;
  if(!force && Date.now() - lastCloud < CLOUD_EVERY) return;
  lastCloud = Date.now();
  const pos = cur.pending; cur.pending = null;
  cur.cols.readPos.doc(cur.id).set(pos).catch(e=> console.warn('阅读位置同步失败', e));
}

function save(){
  clearTimeout(saveTimer);
  if(!cur || !cur.armed) return;
  const a = pickAnchor(blocksOf(cur.lesson).map(b=>{ const r = b.getBoundingClientRect(); return {top:r.top, bottom:r.bottom}; }));
  if(!a) return;
  const pos = { ...a, t: Date.now() };
  store.set(keyOf(cur.id), JSON.stringify(pos));
  cur.pending = pos;
  pushCloud(false);
}

function arm(){ if(cur) cur.armed = true; }

function onScroll(){ if(cur && cur.armed){ clearTimeout(saveTimer); saveTimer = setTimeout(save, 250); } }
function flush(){ save(); pushCloud(true); }
function onUser(){ if(cur){ cur.userMoved = true; arm(); } }

function wire(){
  if(wired) return;
  wired = true;
  window.addEventListener('scroll', onScroll, {passive:true});
  ['wheel','touchstart','keydown','pointerdown'].forEach(ev=> window.addEventListener(ev, onUser, {passive:true}));
  document.addEventListener('visibilitychange', ()=>{ if(document.hidden) flush(); });
  window.addEventListener('pagehide', flush);
}

/* 离开学习页（切到别的界面）时调用 */
export function stopResume(){
  flush();
  if(cur) cur.timers.forEach(clearTimeout);
  cur = null;
}

/* 学习页渲染完（代码块也处理完）后调用；返回 true 表示已跳回上次位置。
   cols 是 userCols(uid)，用来读 / 写云端那份；没有就只用本机记录 */
export async function startResume(id, lesson, cols){
  stopResume();
  wire();
  const me = { id, lesson, cols: cols || null, armed:false, userMoved:false, timers:[], pending:null };
  cur = me;
  let local = null;
  try{ local = JSON.parse(store.get(keyOf(id)) || 'null'); }catch(e){ local = null; }
  let remote = null;
  if(me.cols){
    // 云端最多等 1.5 秒，网慢就先用本机记录，不让页面卡住
    remote = await Promise.race([
      me.cols.readPos.doc(id).get().then(d=> d.exists ? d.data() : null).catch(()=> null),
      new Promise(r=> setTimeout(()=> r(null), 1500)),
    ]);
  }
  if(cur !== me) return false;               // 等云端的时候用户已经切走了
  const saved = newerPos(local, remote);
  const target = worthResuming(saved) ? blocksOf(lesson)[saved.i] : null;
  const jump = ()=>{
    if(cur !== me || me.userMoved) return;
    window.scrollTo(0, target.getBoundingClientRect().top + window.scrollY - saved.off);
  };
  if(target){
    jump();
    // 图片 / 视频框 / 公式稍后才撑开高度，会把位置顶偏：用户还没动手时再校正两次
    me.timers.push(setTimeout(jump, 400), setTimeout(jump, 1200));
  }
  // 程序自己滚动时不记录（否则会把存好的位置覆盖成开头），等稳定或用户一动手再开始记
  me.timers.push(setTimeout(arm, target ? 1400 : 600));
  return !!target;
}

/* 「回到开头」：并且把记录清掉 */
export function clearResume(id, cols){
  store.set(keyOf(id), 'null');
  if(cols) cols.readPos.doc(id).set({i:0, off:0, t:Date.now()}).catch(()=>{});
}
