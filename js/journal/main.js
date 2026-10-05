/* 日记页入口：每天一页，自动保存，当天有内容就 +5 分 */
import { auth, signInWithGoogle, userCols } from '../firebase.js';
import { ensureDailyLoginBonus, resetDailyBonus } from '../data/dailyBonus.js';
import { loadJournalDay, loadJournalMonth, saveJournalDay } from '../data/journal.js';
import { showToast, openCelebrate, closeCelebrate } from '../ui/common.js';
import { localISO, fmtDateLabel } from '../core/dates.js';
import { JOURNAL_POINTS, hasContent, charCount, journalStreak, weekdayLabel, PLACEHOLDER, monthGrid, shiftMonth } from '../core/journal.js';

const $ = id => document.getElementById(id);
const today = () => localISO(new Date());

const J = {
  cols: null, uid: null,
  viewDate: null,        // 正在编辑的那一天
  lastToday: null,       // 上次检查时的「今天」，用来发现跨零点
  days: {},              // {dateISO: text}，已读到的日记（日历的圆点和打开速度用）
  loaded: new Set(),     // 已经读过的月份 'YYYY-MM'
  month: null,           // 日历正在看的月份
  awardedDates: [],      // 已拿到 +5 的日期（来自 log）
  dirty: false, timer: null, saving: null, unsub: null,
};

const setStatus = s => { $('jStatus').textContent = s; };

function renderHeader(){
  const t = today();
  const got = J.awardedDates.includes(t);
  $('journalStreakNum').textContent = journalStreak(J.awardedDates);
  $('todayStatus').textContent = got ? `今天已经记录 ✓（+${JOURNAL_POINTS} 分）` : `今天还没记录，记录就自动 +${JOURNAL_POINTS} 分`;
  $('todayStatus').classList.toggle('ok', got);
}

function renderPageHead(){
  const d = J.viewDate, t = today();
  $('jDate').textContent = `${d}　${weekdayLabel(d)}`;
  const sub = $('jSub');
  sub.classList.remove('ok');
  if(d === t){
    const got = J.awardedDates.includes(t);
    sub.textContent = got ? `今天 · +${JOURNAL_POINTS} 分已到账 ✓` : `今天 · 记录就自动 +${JOURNAL_POINTS} 分`;
    sub.classList.toggle('ok', got);
  } else {
    sub.textContent = `${fmtDateLabel(d)} · 补写和修改以前的日记不加分`;
  }
  $('backToday').hidden = d === t;
  $('jText').placeholder = PLACEHOLDER;
}

function renderCount(){ const n = charCount($('jText').value); $('jCount').textContent = n ? `${n} 字` : ''; }

function renderCalendar(){
  const t = today();
  $('calTitle').textContent = `${J.month.slice(0,4)}年${Number(J.month.slice(5))}月`;
  $('calNext').disabled = J.month >= t.slice(0,7);
  $('jCal').innerHTML = monthGrid(J.month).flat().map(d=>{
    if(!d) return '<span class="j-day blank"></span>';
    const cls = ['j-day'];
    if(hasContent(J.days[d])) cls.push('has');
    if(d === t) cls.push('today');
    if(d === J.viewDate) cls.push('active');
    return `<button class="${cls.join(' ')}" data-date="${d}"${d > t ? ' disabled' : ''}>${Number(d.slice(8))}</button>`;
  }).join('');
}

async function showMonth(ym){
  J.month = ym;
  renderCalendar();
  if(J.loaded.has(ym)) return;
  try{
    const rows = await loadJournalMonth(J.cols, ym);
    rows.forEach(r=>{ if(!(r.dateISO in J.days)) J.days[r.dateISO] = r.text; });
    J.loaded.add(ym);
  }catch(e){ console.error('load journal month failed', e); }
  if(J.month === ym) renderCalendar();
}

function cacheText(dateISO, text){ J.days[dateISO] = text; }

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
      const { awarded, bonus } = await saveJournalDay(J.cols, date, text, today());
      cacheText(date, text);
      setStatus('已保存 ✓');
      if(awarded) showToast(`今日记录 +${JOURNAL_POINTS} 分 ✨`);
      if(bonus) openCelebrate(`<b>${bonus.title}</b><br>小惊喜 <b>+${bonus.amount}</b> 分 🎁`);
      renderCalendar();
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
  renderPageHead(); renderCalendar();
  try{
    ta.value = (dateISO in J.days) ? J.days[dateISO] : await loadJournalDay(J.cols, dateISO);
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
  if(wasToday){ await showMonth(t.slice(0,7)); await openDay(t); } else { renderPageHead(); renderCalendar(); }
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
  await showMonth(J.lastToday.slice(0,7));
  await openDay(J.lastToday);
}

$('signInBtn').addEventListener('click', ()=>{
  signInWithGoogle().catch(e=>{ $('gateNote').textContent = '登录失败：' + (e && e.message ? e.message : '请重试'); });
});
$('jText').addEventListener('input', ()=>{
  J.dirty = true; renderCount(); setStatus('正在输入…');
  clearTimeout(J.timer); J.timer = setTimeout(flush, 800);
});
$('jCal').addEventListener('click', e=>{
  const b = e.target.closest('.j-day');
  if(b && !b.disabled && !b.classList.contains('blank')) openDay(b.getAttribute('data-date'));
});
$('calPrev').addEventListener('click', ()=> showMonth(shiftMonth(J.month, -1)));
$('calNext').addEventListener('click', ()=>{ if(J.month < today().slice(0,7)) showMonth(shiftMonth(J.month, 1)); });
$('closeCelebrate').addEventListener('click', closeCelebrate);
$('backToday').addEventListener('click', async ()=>{ await showMonth(today().slice(0,7)); openDay(today()); });
document.addEventListener('visibilitychange', ()=>{
  if(document.hidden) flush(); else { checkDailyBonus(); checkNewDay(); }
});
window.addEventListener('pagehide', flush);
setInterval(()=>{ checkDailyBonus(); checkNewDay(); }, 30*1000);

auth.onAuthStateChanged(user=>{
  if(J.unsub){ J.unsub(); J.unsub = null; }
  if(user){
    Object.assign(J, {uid:user.uid, cols:userCols(user.uid), viewDate:null, days:{}, loaded:new Set(), month:null, awardedDates:[], dirty:false});
    $('gate').hidden = true; $('journalRoot').hidden = false;
    checkDailyBonus();
    start();
  } else {
    Object.assign(J, {uid:null, cols:null, viewDate:null, days:{}, loaded:new Set(), month:null, awardedDates:[], dirty:false});
    resetDailyBonus();
    $('gate').hidden = false; $('journalRoot').hidden = true;
  }
});
