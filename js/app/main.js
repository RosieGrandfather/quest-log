/* 主页面入口：登录 → 初始化 / 迁移用户数据 → 实时订阅 → 渲染 */
import { auth, signInWithGoogle, userCols } from '../firebase.js';
import { ensureUserData } from '../data/userData.js';
import { ensureDailyLoginBonus, resetDailyBonus } from '../data/dailyBonus.js';
import { showToast, closeCelebrate } from '../ui/common.js';
import { S } from './state.js';
import { render } from './render.js';
import { wireTasks } from './tasks.js';
import { wireSections } from './sections.js';
import { wireRewards } from './rewards.js';

let unsubs = [];
function unsubscribeAll(){ unsubs.forEach(u=>u()); unsubs = []; }

function subscribeAll(){
  const { cols } = S;
  const onErr = name => err => console.error(name+' snapshot error', err);
  unsubs.push(cols.log.orderBy('ts','desc').limit(500).onSnapshot(snap=>{
    S.logEntries = snap.docs.map(d=>({id:d.id, ...d.data()}));
    render();
  }, onErr('log')));
  unsubs.push(cols.tasks.orderBy('ts','asc').limit(300).onSnapshot(snap=>{
    S.tasks = snap.docs.map(d=>({id:d.id, ...d.data()})).filter(t=> t.active!==false);
    render();
  }, onErr('tasks')));
  unsubs.push(cols.sections.orderBy('ts','asc').limit(100).onSnapshot(snap=>{
    S.sections = snap.docs.map(d=>({id:d.id, label:d.data().label||'未命名板块', short:d.data().short||'', ts:d.data().ts}));
    render();
  }, onErr('sections')));
  unsubs.push(cols.rewards.orderBy('cost','asc').limit(100).onSnapshot(snap=>{
    S.rewards = snap.docs.map(d=>({id:d.id, ...d.data()})).filter(r=> r.active!==false);
    render();
  }, onErr('rewards')));
}

function checkDailyBonus(){
  if(!S.cols) return;
  ensureDailyLoginBonus(S.cols.log, pts=> showToast(`今日上线 +${pts} 积分 ✨`));
}

function switchTab(name){
  document.querySelectorAll('.tab').forEach(b=> b.classList.toggle('active', b.getAttribute('data-tab')===name));
  document.getElementById('panel-log').hidden = name!=='log';
  document.getElementById('panel-rewards').hidden = name!=='rewards';
  document.getElementById('panel-history').hidden = name!=='history';
}

function wireUI(){
  document.getElementById('tabs').addEventListener('click', e=>{
    const btn = e.target.closest('.tab');
    if(btn) switchTab(btn.getAttribute('data-tab'));
  });
  document.getElementById('closeCelebrate').addEventListener('click', closeCelebrate);
  wireTasks();
  wireSections();
  wireRewards();
}

document.getElementById('signInBtn').addEventListener('click', ()=>{
  signInWithGoogle().catch(e=>{
    document.getElementById('gateNote').textContent = '登录失败：' + (e && e.message ? e.message : '请重试');
  });
});
document.getElementById('signOutBtn').addEventListener('click', ()=>{
  unsubscribeAll();
  resetDailyBonus();
  auth.signOut();
});

wireUI();

auth.onAuthStateChanged(user=>{
  if(user){
    S.uid = user.uid;
    S.cols = userCols(user.uid);
    document.getElementById('gate').hidden = true;
    document.getElementById('appRoot').hidden = false;
    ensureUserData(S.cols).finally(()=>{
      if(S.uid !== user.uid) return;
      subscribeAll();
      checkDailyBonus();
    });
  } else {
    S.uid = null;
    S.cols = null;
    resetDailyBonus();
    unsubscribeAll();
    document.getElementById('gate').hidden = false;
    document.getElementById('appRoot').hidden = true;
  }
});

/* 页面一直开着跨过零点，或者从后台切回来时，也补发当天的签到奖励 */
document.addEventListener('visibilitychange', ()=>{ if(!document.hidden) checkDailyBonus(); });
setInterval(checkDailyBonus, 60*1000);
