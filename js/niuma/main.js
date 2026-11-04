/* 牛马鼓励器入口：第一次进来填上下班时间、午休、月薪（存在自己账号里），
   之后按当前时间现算今天已赚多少新币。上班时小奶牛猫绕圈追鱼；午休 / 上班前 / 公假 / 请假时睡觉；
   下班后揣手坐着旁边一副鱼骨头；周末随机玩毛线或打盹。只算真钱，不加积分 */
import { auth, signInWithGoogle, userCols } from '../firebase.js';
import { loadNiuma, saveNiumaSettings, setLeave } from '../data/niuma.js';
import { showToast } from '../ui/common.js';
import { localISO } from '../core/dates.js';
import {
  settingsError, dayKind, phase, nextMarkMs, catMode, earnedToday, monthToDate, dayProgress,
  workedSeconds, workSecondsPerDay, workdaysInMonth, dailyPay, fmtMoney, fmtDuration, fmtHours,
} from '../core/niuma.js';

const $ = id => document.getElementById(id);
const WEEKDAYS = ['周日','周一','周二','周三','周四','周五','周六'];
const pad = n => String(n).padStart(2, '0');

const S = { cols:null, settings:null, saving:false, raf:0 };

/* ---- 每秒刷新：时钟、状态、倒计时、进度、本月 ---- */
function renderSlow(){
  const now = new Date();
  $('clock').textContent = `${localISO(now)} ${WEEKDAYS[now.getDay()]} ${pad(now.getHours())}:${pad(now.getMinutes())}:${pad(now.getSeconds())}`;
  const s = S.settings;
  if(!s) return;
  const mode = catMode(s, now);
  const kind = dayKind(now, s.leave);
  const p = phase(s, now);
  $('phaseLabel').textContent = mode.label;
  setCat(mode.cat);

  const weekend = kind === 'weekend';
  let cd;
  if(weekend) cd = now.getDay() === 6 ? '周末快乐，好好学习、好好休息' : '明天又要上班了，今天好好休息';
  else if(p === 'before') cd = `距离上班还有 <b>${fmtDuration(nextMarkMs(s, now))}</b>`;
  else if(p === 'lunch') cd = `午休还剩 <b>${fmtDuration(nextMarkMs(s, now))}</b>`;
  else if(p === 'work') cd = `距离下班还有 <b>${fmtDuration(nextMarkMs(s, now))}</b>`;
  else cd = now.getDay() === 5 ? '今天辛苦啦，周末快乐' : '今天辛苦啦，明天见';
  $('countdown').innerHTML = cd;

  const prog = dayProgress(s, now);
  $('progressPct').textContent = (prog * 100).toFixed(1) + '%';
  $('progressSub').textContent = `已工作 ${fmtHours(workedSeconds(s, now))} / ${fmtHours(workSecondsPerDay(s))} 小时`;
  $('barFill').style.width = (prog * 100).toFixed(2) + '%';
  $('trackDone').setAttribute('stroke-dasharray', `${(prog * 100).toFixed(2)} 100`);
  $('trackDone').classList.toggle('zero', prog <= 0);
  document.querySelector('.nm-progress').hidden = weekend;
  $('earnedLabel').textContent = weekend ? '周末不上班，不算钱' : (kind === 'holiday' || kind === 'leave') ? '今日已赚 · 带薪' : '今日已赚 · 估算';
  $('earned').hidden = weekend;

  $('monthTotal').textContent = fmtMoney(monthToDate(s, now), 2);
  $('monthSub').textContent = `本月 ${workdaysInMonth(now)} 个工作日，日薪约 ${fmtMoney(dailyPay(s, now), 2)}`;

  const canLeave = kind === 'work' || kind === 'leave';
  $('leaveBtn').hidden = !canLeave || p === 'after';
  $('leaveBtn').textContent = kind === 'leave' ? '↩ 取消今天请假' : '🏖 今天请假';
  $('leaveBtn').disabled = S.saving;
}

/* ---- 每帧刷新：今日已赚（四位小数一直跳） ---- */
function renderFast(){
  if(S.settings) $('earned').textContent = fmtMoney(earnedToday(S.settings, new Date()));
  S.raf = requestAnimationFrame(renderFast);
}

/* ---- 小猫 ---- */
let weekendTimer = null, twitchTimer = null;
function setCat(cat){
  const stage = $('stage');
  if(stage.dataset.cat === cat) return;
  stage.dataset.cat = cat;
  clearTimeout(weekendTimer);
  if(cat === 'weekend') weekendPose();
  else delete stage.dataset.pose;
}
/* 周末：玩毛线 / 打盹随机切换 */
function weekendPose(){
  const stage = $('stage');
  stage.dataset.pose = Math.random() < 0.5 ? 'play' : 'nap';
  weekendTimer = setTimeout(weekendPose, 8000 + Math.random() * 14000);
}
/* 不跑步的时候，时不时甩一下尾巴、动一下头 */
function twitch(){
  const stage = $('stage');
  if(stage.dataset.cat !== 'run'){
    stage.classList.add('twitch');
    setTimeout(()=> stage.classList.remove('twitch'), 1200);
  }
  twitchTimer = setTimeout(twitch, 4000 + Math.random() * 9000);
}

/* ---- 设置弹窗 ---- */
const FIELDS = {start:'fStart', end:'fEnd', lunchStart:'fLunchStart', lunchEnd:'fLunchEnd', monthly:'fMonthly'};
function openSettings(){
  const s = S.settings;
  if(s) for(const [k, id] of Object.entries(FIELDS)) $(id).value = s[k];
  $('formError').textContent = '';
  $('cancelSettings').hidden = !s; // 第一次必须填完
  $('settingsModal').hidden = false;
}
async function saveSettings(){
  if(S.saving || !S.cols) return;
  const v = {};
  for(const [k, id] of Object.entries(FIELDS)) v[k] = $(id).value.trim();
  const err = settingsError(v);
  if(err){ $('formError').textContent = err; return; }
  S.saving = true; $('saveSettings').disabled = true;
  try{
    await saveNiumaSettings(S.cols, v);
    S.settings = {...v, monthly:Number(v.monthly), leave: S.settings ? S.settings.leave : []};
    $('settingsModal').hidden = true;
    showToast('已保存');
  }catch(e){ $('formError').textContent = '保存失败，请重试'; console.error('save niuma settings failed', e); }
  S.saving = false; $('saveSettings').disabled = false;
  renderSlow();
}

/* ---- 今天请假 ---- */
async function toggleLeave(){
  const s = S.settings;
  if(!s || !S.cols || S.saving) return;
  const t = localISO(new Date());
  const on = !s.leave.includes(t);
  S.saving = true; renderSlow();
  try{
    await setLeave(S.cols, t, on);
    s.leave = on ? [...s.leave, t] : s.leave.filter(x=> x !== t);
    showToast(on ? '请假啦，工资照涨，小猫去睡了 💤' : '已取消请假');
  }catch(e){ showToast('保存失败，请重试'); console.error('toggle leave failed', e); }
  S.saving = false; renderSlow();
}

async function start(cols){
  try{
    const s = await loadNiuma(cols);
    if(S.cols !== cols) return;
    S.settings = s;
  }catch(e){ showToast('读取失败，请刷新'); console.error('load niuma failed', e); return; }
  if(!S.settings) openSettings();
  renderSlow();
}

$('openSettings').addEventListener('click', openSettings);
$('cancelSettings').addEventListener('click', ()=>{ $('settingsModal').hidden = true; });
$('saveSettings').addEventListener('click', saveSettings);
$('settingsModal').addEventListener('keydown', e=>{ if(e.key === 'Enter') saveSettings(); });
$('leaveBtn').addEventListener('click', toggleLeave);
$('signInBtn').addEventListener('click', ()=>{
  signInWithGoogle().catch(e=>{ $('gateNote').textContent = '登录失败：' + (e && e.message ? e.message : '请重试'); });
});

setInterval(renderSlow, 1000);
twitch();

auth.onAuthStateChanged(user=>{
  cancelAnimationFrame(S.raf);
  Object.assign(S, {cols:null, settings:null, saving:false});
  $('settingsModal').hidden = true;
  if(user){
    S.cols = userCols(user.uid);
    $('gate').hidden = true; $('niumaRoot').hidden = false;
    renderSlow(); renderFast();
    start(S.cols);
  } else {
    $('gate').hidden = false; $('niumaRoot').hidden = true;
  }
});
