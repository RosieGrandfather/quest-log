/* 日记页入口：每天一页，自动保存，当天有内容就 +5 分 */
import { auth, signInWithGoogle, userCols } from '../firebase.js';
import { ensureDailyLoginBonus, resetDailyBonus } from '../data/dailyBonus.js';
import { loadJournalDay, loadRecentJournal, saveJournalDay } from '../data/journal.js';
import { showToast } from '../ui/common.js';
import { localISO, fmtDateLabel } from '../core/dates.js';
import { escapeHTML } from '../core/html.js';
import { JOURNAL_POINTS, hasContent, charCount, journalStreak, weekdayLabel, previewText } from '../core/journal.js';

const $ = id => document.getElementById(id);
const today = () => localISO(new Date());

const J = {
  cols: null, uid: null,
  viewDate: null,        // 正在编辑的那一天
  lastToday: null,       // 上次检查时的「今天」，用来发现跨零点
  recent: [],            // [{dateISO, text}]，按日期倒序
  awardedDates: [],      // 已拿到 +5 的日期（来自 log）
  dirty: false, timer: null, saving: null, unsub: null,
};

const setStatus = s => { $('jStatus').textContent = s; };

function renderHeader(){
  const t = today();
  const got = J.awardedDates.includes(t);
  $('journalStreakNum').textContent = journalStreak(J.awardedDates);
  $('todayStatus').textContent = got ? `今天已经写了日记 ✓（+${JOURNAL_POINTS} 积分）` : `今天还没写，写一点就有 +${JOURNAL_POINTS} 积分`;
  $('todayStatus').classList.toggle('ok', got);
}

function renderPageHead(){
  const d = J.viewDate, t = today();
  $('jDate').textContent = `${d}　${weekdayLabel(d)}`;
  const sub = $('jSub');
  sub.classList.remove('ok');
  if(d === t){
    const got = J.awardedDates.includes(t);
    sub.textContent = got ? `今天 · +${JOURNAL_POINTS} 积分已到账 ✓` : `今天 · 写了内容就自动 +${JOURNAL_POINTS} 积分`;
    sub.classList.toggle('ok', got);
  } else {
    sub.textContent = `${fmtDateLabel(d)} · 补写和修改以前的日记不加分`;
  }
  $('backToday').hidden = d === t;
}

function renderCount(){ const n = charCount($('jText').value); $('jCount').textContent = n ? `${n} 字` : ''; }

function renderList(){
  const el = $('jList');
  const items = J.recent.filter(x=> hasContent(x.text) && x.dateISO !== today());
  if(!items.length){ el.innerHTML = '<div class="j-empty">还没有以前的日记。每天写一点，这里会慢慢长出来。</div>'; return; }
  el.innerHTML = items.map(x=>`<button class="j-item${x.dateISO===J.viewDate?' active':''}" data-date="${x.dateISO}">
      <span class="j-item-date">${x.dateISO} ${weekdayLabel(x.dateISO)}</span>
      <span class="j-item-prev">${escapeHTML(previewText(x.text))}</span>
    </button>`).join('');
}

function cacheText(dateISO, text){
  const i = J.recent.findIndex(x=>x.dateISO===dateISO);
  if(i>=0) J.recent[i].text = text; else { J.recent.push({dateISO, text}); J.recent.sort((a,b)=> a.dateISO<b.dateISO?1:-1); }
}

/* 把没保存的存掉。保存的是 viewDate 当时的内容；存的过程中又打字会再排一次 */
async function flush(){
  clearTimeout(J.timer);
  if(J.saving) await J.saving;
  if(!J.dirty || !J.viewDate) return;
  J.dirty = false;
  const date = J.viewDate, text = $('jText').value;
  setStatus('保存中…');
  J.saving = (async ()=>{
    try{
      const awarded = await saveJournalDay(J.cols, date, text, today());
      cacheText(date, text);
      setStatus('已保存 ✓');
      if(awarded) showToast(`今天的日记 +${JOURNAL_POINTS} 积分 ✨`);
      renderList();
    }catch(e){
      J.dirty = true; setStatus('保存失败，会自动重试'); console.error('save journal failed', e);
      J.timer = setTimeout(flush, 3000);
    }
  })();
  await J.saving; J.saving = null;
}

async function openDay(dateISO){
  await flush();
  if(J.dirty){ showToast('上一页还没存好，稍等再切换'); return; }
  J.viewDate = dateISO;
  const ta = $('jText');
  ta.disabled = true; ta.value = ''; setStatus('读取中…');
  renderPageHead(); renderList();
  try{
    const cached = J.recent.find(x=>x.dateISO===dateISO);
    ta.value = cached ? cached.text : await loadJournalDay(J.cols, dateISO);
    setStatus(ta.value ? '已同步' : '');
  }catch(e){ setStatus('读取失败，请刷新'); console.error(e); return; }
  if(J.viewDate !== dateISO) return;
  ta.disabled = false; renderCount();
  if(dateISO === today()) ta.focus();
}

/* 页面开着跨过零点：把旧的一页存好，如果正停在「昨天的今天」就翻到新的一页 */
async function checkNewDay(){
  const t = today();
  if(!J.cols || J.lastToday === t) { renderHeader(); return; }
  const wasToday = J.viewDate === J.lastToday;
  J.lastToday = t;
  renderHeader();
  if(wasToday) await openDay(t); else { renderPageHead(); renderList(); }
}

function checkDailyBonus(){
  if(!J.cols) return;
  ensureDailyLoginBonus(J.cols.log, pts=> showToast(`今日上线 +${pts} 积分 ✨`));
}

async function start(){
  J.lastToday = today();
  renderHeader();
  J.unsub = J.cols.log.where('category','==','journal').onSnapshot(snap=>{
    J.awardedDates = snap.docs.map(d=> d.data().dateISO).filter(Boolean);
    renderHeader(); if(J.viewDate) renderPageHead();
  }, err=> console.error('journal log snapshot error', err));
  try{ J.recent = await loadRecentJournal(J.cols); }catch(e){ console.error('load recent journal failed', e); }
  await openDay(J.lastToday);
}

$('signInBtn').addEventListener('click', ()=>{
  signInWithGoogle().catch(e=>{ $('gateNote').textContent = '登录失败：' + (e && e.message ? e.message : '请重试'); });
});
$('jText').addEventListener('input', ()=>{
  J.dirty = true; renderCount(); setStatus('正在输入…');
  clearTimeout(J.timer); J.timer = setTimeout(flush, 800);
});
$('jList').addEventListener('click', e=>{
  const b = e.target.closest('.j-item');
  if(b) openDay(b.getAttribute('data-date'));
});
$('backToday').addEventListener('click', ()=> openDay(today()));
document.addEventListener('visibilitychange', ()=>{
  if(document.hidden) flush(); else { checkDailyBonus(); checkNewDay(); }
});
window.addEventListener('pagehide', flush);
setInterval(()=>{ checkDailyBonus(); checkNewDay(); }, 30*1000);

auth.onAuthStateChanged(user=>{
  if(J.unsub){ J.unsub(); J.unsub = null; }
  if(user){
    Object.assign(J, {uid:user.uid, cols:userCols(user.uid), viewDate:null, recent:[], awardedDates:[], dirty:false});
    $('gate').hidden = true; $('journalRoot').hidden = false;
    checkDailyBonus();
    start();
  } else {
    Object.assign(J, {uid:null, cols:null, viewDate:null, recent:[], awardedDates:[], dirty:false});
    resetDailyBonus();
    $('gate').hidden = false; $('journalRoot').hidden = true;
  }
});
