/* 学习区入口：登录 → 订阅进度 → 按 URL 的 # 渲染界面 */
import { auth, signInWithGoogle, userCols } from '../firebase.js';
import { ensureDailyLoginBonus, resetDailyBonus } from '../data/dailyBonus.js';
import { showToast, closeCelebrate, closeOnBackdrop } from '../ui/common.js';
import { localISO } from '../core/dates.js';
import { unitKey, studyStreak } from '../core/study.js';
import { T } from './state.js';
import { renderRoute, refreshLive, takeAfterCelebrate } from './views.js';
import { wireNotes } from './notes.js';

const $ = id => document.getElementById(id);
let unsubs = [];
let firstData = false;

function renderHeader(){
  const n = studyStreak(T.studyDates);
  $('studyStreakNum').textContent = n;
  const today = T.studyDates.includes(localISO(new Date()));
  $('todayStatus').textContent = today ? '今天已经学了新章节 ✓' : '今天还没学新章节';
  $('todayStatus').classList.toggle('ok', today);
}

function subscribe(){
  const { cols } = T;
  // 学完记录（首次学完一节时写进 log 的 study 记录）→ 已学章节 + 有效学习日
  unsubs.push(cols.log.where('category','==','study').onSnapshot(snap=>{
    T.completed = {};
    T.studyDates = [];
    snap.docs.forEach(d=>{
      const e = d.data();
      if(e.courseId && e.unitId) T.completed[unitKey(e.courseId, e.unitId)] = e.dateISO;
      if(e.dateISO) T.studyDates.push(e.dateISO);
    });
    renderHeader();
    if(firstData) refreshLive(); else { firstData = true; renderRoute(); }
  }, err=> console.error('study log snapshot error', err)));
  // 测验成绩 / 上次答题
  unsubs.push(cols.studyProgress.onSnapshot(snap=>{
    T.progress = {};
    snap.docs.forEach(d=>{ T.progress[d.id] = d.data(); });
    if(firstData) refreshLive();
  }, err=> console.error('progress snapshot error', err)));
}

function checkDailyBonus(){
  if(!T.cols) return;
  ensureDailyLoginBonus(T.cols.log, pts=> showToast(`今日上线 +${pts} 积分 ✨`));
}

$('signInBtn').addEventListener('click', ()=>{
  signInWithGoogle().catch(e=>{ $('gateNote').textContent = '登录失败：' + (e && e.message ? e.message : '请重试'); });
});
$('closeCelebrate').addEventListener('click', ()=>{
  closeCelebrate();
  const next = takeAfterCelebrate();
  if(next) next();
});
$('quizPromptSkip').addEventListener('click', ()=>{ $('quizPrompt').hidden = true; showToast('好的，之后随时可以回来补做测验'); });
closeOnBackdrop('quizPrompt', ()=>{ $('quizPrompt').hidden = true; });
wireNotes();
window.addEventListener('hashchange', ()=>{ if(T.cols) renderRoute(); });

auth.onAuthStateChanged(user=>{
  unsubs.forEach(u=>u()); unsubs = [];
  if(user){
    T.uid = user.uid;
    T.cols = userCols(user.uid);
    firstData = false;
    $('gate').hidden = true;
    $('studyRoot').hidden = false;
    subscribe();
    checkDailyBonus();
  } else {
    T.uid = null;
    T.cols = null;
    resetDailyBonus();
    $('gate').hidden = false;
    $('studyRoot').hidden = true;
  }
});

document.addEventListener('visibilitychange', ()=>{ if(!document.hidden) checkDailyBonus(); });
setInterval(checkDailyBonus, 60*1000);
