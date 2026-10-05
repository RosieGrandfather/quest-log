import { computeStreak } from './stats.js';

/* 日记：今天记录了（去掉空白后不为空）就自动 +5 分，每天一次 */
export const JOURNAL_POINTS = 5;

export const hasContent = text => typeof text === 'string' && text.trim().length > 0;

/* 字数：不算空白（中文按字，英文按字符，够用即可） */
export const charCount = text => (text || '').replace(/\s/g, '').length;

/* 连续写日记到第 n 天时的小惊喜（没有就返回 null）。页面上不提前显示，到了才弹出来。
   总额不大：第一个月额外共 120，第 66 天（养成习惯的那个说法）+66，100 天 +100，365 天 +200 */
export const JOURNAL_STREAK_BONUS = {3:5, 7:15, 14:20, 21:30, 30:50, 50:50, 66:66, 100:100, 200:100, 365:200};
export function journalStreakBonus(n){
  const amount = JOURNAL_STREAK_BONUS[n];
  return amount ? {amount, title:`连续写日记 ${n} 天`} : null;
}

/* 连续写日记的天数：今天还没写时从昨天往前数 */
export function journalStreak(dates, now = new Date()){
  return computeStreak(new Set(dates), now);
}

const WEEK = ['周日','周一','周二','周三','周四','周五','周六'];
export function weekdayLabel(iso){
  const [y,m,d] = iso.split('-').map(Number);
  return WEEK[new Date(y, m-1, d).getDay()];
}

/* 列表里的预览：取第一行有字的内容，最多 40 字 */
export function previewText(text, max = 40){
  const line = (text || '').split('\n').map(s=>s.trim()).find(Boolean) || '';
  return line.length > max ? line.slice(0, max) + '…' : line;
}

/* 输入框里的提示语：每天一样 */
export const PLACEHOLDER = "What's on your mind today?";

/* 日历：ym = 'YYYY-MM'，周一在最前。返回按周分好的格子，空位是 null */
export function monthGrid(ym){
  const [y,m] = ym.split('-').map(Number);
  const first = new Date(y, m-1, 1);
  const lead = (first.getDay()+6)%7;
  const n = new Date(y, m, 0).getDate();
  const cells = Array(lead).fill(null);
  for(let d=1; d<=n; d++) cells.push(`${ym}-${String(d).padStart(2,'0')}`);
  while(cells.length % 7) cells.push(null);
  const weeks = [];
  for(let i=0; i<cells.length; i+=7) weeks.push(cells.slice(i, i+7));
  return weeks;
}

export function shiftMonth(ym, delta){
  const [y,m] = ym.split('-').map(Number);
  const d = new Date(y, m-1+delta, 1);
  return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}`;
}
