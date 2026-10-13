/* 每日提醒弹窗：每天早上 7 点之后第一次打开主页面弹一次，Day 1–7 轮流。
   「上次弹出的日期 + 第几天」存在 Firestore 的 meta/app 文档里（dailyReminder），所以手机和电脑共用同一份，
   今天在一台设备上弹过，另一台就不再弹。弹出的那一刻就记下来，不用点「知道了」。
   页面一直开着跨过 7 点时也会弹（由 main.js 每分钟检查一次，和每日上线奖励同一个时机）。 */
import { S } from './state.js';
import { localISO } from '../core/dates.js';
import { REMINDERS, shouldShowReminder, nextReminderDay } from '../core/reminders.js';
import { closeOnBackdrop } from '../ui/common.js';

let busy = false, shownISO = null;

export function resetDailyReminder(){ busy = false; shownISO = null; }

const modal = () => document.getElementById('reminderModal');
const closeReminder = () => { modal().hidden = true; };

export function wireReminder(){
  document.getElementById('closeReminder').addEventListener('click', closeReminder);
  closeOnBackdrop('reminderModal', closeReminder);
  document.addEventListener('keydown', e=>{ if(e.key === 'Escape' && !modal().hidden) closeReminder(); });
}

function openReminder(day){
  const r = REMINDERS[day - 1];
  document.getElementById('remDay').textContent = `Day ${day}`;
  document.getElementById('remBoundary').textContent = r.boundary;
  document.getElementById('remPositive').textContent = r.positive;
  modal().hidden = false;
}

export async function ensureDailyReminder(){
  const cols = S.cols;
  if(!cols || busy) return;
  const now = new Date(), today = localISO(now);
  if(shownISO === today || now.getHours() < 7) return;
  // 别的弹窗（添加任务、庆祝等）正开着就先不打扰，下一分钟再看
  if(document.querySelector('.modal-backdrop:not([hidden])')) return;
  busy = true;
  try{
    const snap = await cols.meta.get();
    const prev = (snap.exists && snap.data().dailyReminder) || {};
    if(S.cols !== cols) return;                       // 读的时候换了账号
    if(!shouldShowReminder(now, prev.lastISO)){ shownISO = today; return; }
    const day = nextReminderDay(prev.day);
    shownISO = today;
    openReminder(day);
    await cols.meta.set({dailyReminder:{lastISO:today, day}}, {merge:true});
  }catch(e){
    console.error('daily reminder failed', e);
  }finally{
    busy = false;
  }
}
