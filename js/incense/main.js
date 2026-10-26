/* 上香页入口：点「上香」点燃三炷香（烧 3 分钟，可以写个心愿），烧完才能再上；
   下面是电子木鱼，敲一下功德 +1。都不加积分，只记连续上香天数和累计数 */
import { auth, signInWithGoogle, userCols } from '../firebase.js';
import { ensureDailyLoginBonus, resetDailyBonus } from '../data/dailyBonus.js';
import { loadIncenseDay, loadIncenseSince, loadIncenseTotals, lightIncense, addMerit } from '../data/incense.js';
import { showToast } from '../ui/common.js';
import { escapeHTML } from '../core/html.js';
import { localISO, fmtDateLabel } from '../core/dates.js';
import { WISH_PRESETS, cleanWish, burnProgress, isBurning, remainingMs, fmtRemaining, incenseStreak, meritLine } from '../core/incense.js';

const $ = id => document.getElementById(id);
const today = () => localISO(new Date());

const S = {
  cols: null,
  day: null,              // 今天的记录 {sticks, wishes, merit, litAt}
  recent: [],             // 最近 30 天有记录的日子（打开页面时读一次；今天的以 day 为准）
  totals: {totalSticks:0, totalMerit:0},
  pendingMerit: 0, meritTimer: null,
  lighting: false,
};

/* ---- 香炉 ---- */
function renderSticks(){
  const litAt = S.day ? S.day.litAt : 0;
  const p = burnProgress(litAt);
  const burning = p < 1;
  const sticks = $('sticks');
  sticks.style.setProperty('--p', burning ? p.toFixed(4) : 1);
  sticks.classList.toggle('lit', burning);
  sticks.classList.toggle('done', !burning);
  $('timer').textContent = burning ? `香还在烧，剩 ${fmtRemaining(remainingMs(litAt))}` : (S.day && S.day.sticks ? '香已燃尽，可以再上一炷' : '点一炷香，静一静');
  $('lightBtn').disabled = burning || S.lighting || !S.day;
  $('lightBtn').textContent = burning ? '🙏 香火正旺' : '🔥 上香';
}

function renderHeader(){
  const t = today();
  const dates = S.recent.filter(r=> r.sticks > 0).map(r=> r.dateISO);
  if(S.day && S.day.sticks > 0 && !dates.includes(t)) dates.push(t);
  $('streakNum').textContent = incenseStreak(dates);
  const n = S.day ? S.day.sticks : 0;
  $('todayStatus').textContent = n ? `今天上过 ${n} 次香 ✓` : '今天还没上香';
  $('todayStatus').classList.toggle('ok', n > 0);
}

function renderMerit(){
  const m = (S.day ? S.day.merit : 0) + S.pendingMerit;
  $('meritToday').textContent = m;
  $('meritTotal').textContent = S.totals.totalMerit + S.pendingMerit;
  $('sticksTotal').textContent = S.totals.totalSticks;
}

function renderWishes(){
  const t = today();
  const rows = S.recent.filter(r=> r.dateISO !== t).flatMap(r=> r.wishes);
  if(S.day) rows.push(...S.day.wishes);
  rows.sort((a,b)=> b.ts - a.ts);
  $('wishList').innerHTML = rows.length
    ? rows.slice(0, 10).map(w=> `<li><span>${escapeHTML(w.text)}</span><span class="when">${fmtDateLabel(localISO(new Date(w.ts)))}</span></li>`).join('')
    : '<li class="empty">还没有许过愿</li>';
}

const renderAll = () => { renderHeader(); renderSticks(); renderMerit(); renderWishes(); };

/* ---- 上香 ---- */
async function light(){
  if(!S.cols || !S.day || S.lighting || isBurning(S.day.litAt)) return;
  const wish = cleanWish($('wishInput').value);
  S.lighting = true; renderSticks();
  const now = Date.now(), date = today();
  try{
    const ok = await lightIncense(S.cols, date, wish, now);
    if(ok){
      S.day = await loadIncenseDay(S.cols, date);
      S.totals.totalSticks++;
      $('wishInput').value = '';
      showToast(wish ? `香已点上，愿「${wish}」🙏` : '香已点上 🙏');
    } else {
      S.day = await loadIncenseDay(S.cols, date);
      showToast('另一台设备上的香还在烧');
    }
  }catch(e){ showToast('上香失败，请重试'); console.error('light incense failed', e); }
  S.lighting = false;
  renderAll();
}

/* ---- 木鱼：每下立刻显示，攒 1.5 秒写一次 ---- */
function knock(){
  if(!S.cols || !S.day) return;
  S.pendingMerit++;
  const btn = $('fishBtn');
  btn.classList.remove('hit'); void btn.offsetWidth; btn.classList.add('hit');
  setTimeout(()=> btn.classList.remove('hit'), 90);
  const total = S.day.merit + S.pendingMerit;
  const el = document.createElement('div');
  el.className = 'in-float';
  el.textContent = meritLine(total) || '功德 +1';
  $('floats').appendChild(el);
  setTimeout(()=> el.remove(), 900);
  renderMerit();
  clearTimeout(S.meritTimer); S.meritTimer = setTimeout(flushMerit, 1500);
}

async function flushMerit(){
  clearTimeout(S.meritTimer);
  const n = S.pendingMerit;
  if(!n || !S.cols || !S.day) return;
  S.pendingMerit = 0;
  S.day.merit += n; S.totals.totalMerit += n;
  try{ await addMerit(S.cols, today(), n); }
  catch(e){
    S.day.merit -= n; S.totals.totalMerit -= n; S.pendingMerit += n;
    console.error('save merit failed', e); S.meritTimer = setTimeout(flushMerit, 3000);
  }
  renderMerit();
}

/* ---- 跨零点：换成新一天的记录 ---- */
let lastToday = null;
async function checkNewDay(){
  if(!S.cols) return;
  const t = today();
  if(lastToday === t){ renderSticks(); return; }
  await flushMerit();
  if(lastToday && S.day){
    const prev = lastToday;
    S.recent = S.recent.filter(r=> r.dateISO !== prev).concat({dateISO:prev, ...S.day});
  }
  lastToday = t;
  try{ S.day = await loadIncenseDay(S.cols, t); }catch(e){ console.error(e); }
  renderAll();
}

async function start(cols){
  lastToday = today();
  const from = new Date(); from.setDate(from.getDate() - 30);
  try{
    const [day, recent, totals] = await Promise.all([loadIncenseDay(cols, lastToday), loadIncenseSince(cols, localISO(from)), loadIncenseTotals(cols)]);
    if(S.cols !== cols) return;
    Object.assign(S, {day, recent, totals});
  }catch(e){ showToast('读取失败，请刷新'); console.error('load incense failed', e); return; }
  renderAll();
}

$('presets').innerHTML = WISH_PRESETS.map(w=> `<button class="in-preset" type="button">${escapeHTML(w)}</button>`).join('');
$('presets').addEventListener('click', e=>{
  const b = e.target.closest('.in-preset');
  if(b){ $('wishInput').value = b.textContent; $('wishInput').focus(); }
});
$('wishInput').addEventListener('keydown', e=>{ if(e.key === 'Enter') light(); });
$('lightBtn').addEventListener('click', light);
$('fishBtn').addEventListener('click', knock);
$('signInBtn').addEventListener('click', ()=>{
  signInWithGoogle().catch(e=>{ $('gateNote').textContent = '登录失败：' + (e && e.message ? e.message : '请重试'); });
});
document.addEventListener('visibilitychange', ()=>{
  if(document.hidden) flushMerit();
  else if(S.cols){ ensureDailyLoginBonus(S.cols.log, pts=> showToast(`今日上线 +${pts} 积分 ✨`)); checkNewDay(); }
});
window.addEventListener('pagehide', flushMerit);
setInterval(checkNewDay, 1000);

auth.onAuthStateChanged(user=>{
  clearTimeout(S.meritTimer);
  Object.assign(S, {cols:null, day:null, recent:[], totals:{totalSticks:0, totalMerit:0}, pendingMerit:0, lighting:false});
  if(user){
    S.cols = userCols(user.uid);
    $('gate').hidden = true; $('incenseRoot').hidden = false;
    ensureDailyLoginBonus(S.cols.log, pts=> showToast(`今日上线 +${pts} 积分 ✨`));
    renderAll();
    start(S.cols);
  } else {
    resetDailyBonus();
    $('gate').hidden = false; $('incenseRoot').hidden = true;
  }
});
