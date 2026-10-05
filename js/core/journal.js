import { computeStreak } from './stats.js';

/* 日记：今天记录了（去掉空白后不为空）就自动 +5 分，每天一次 */
export const JOURNAL_POINTS = 5;

export const hasContent = text => typeof text === 'string' && text.trim().length > 0;

/* 一天的日记分五块（顺序就是页面上的顺序）。没有固定格式，哪块空着都行 */
export const JOURNAL_SECTIONS = [
  {id:'body',  label:'身体'},
  {id:'mood',  label:'心情'},
  {id:'study', label:'学习'},
  {id:'work',  label:'工作'},
  {id:'free',  label:'想说的'},
];
export const emptyEntry = () => Object.fromEntries(JOURNAL_SECTIONS.map(s=>[s.id, '']));

/* 数据库文档 → 一天的内容。老版本只有一整段 text，归到「想说的」 */
export function entryFromDoc(data){
  const e = emptyEntry();
  if(!data) return e;
  if(data.sections && typeof data.sections === 'object'){
    JOURNAL_SECTIONS.forEach(s=>{ if(typeof data.sections[s.id] === 'string') e[s.id] = data.sections[s.id]; });
  } else if(typeof data.text === 'string'){
    e.free = data.text;
  }
  return e;
}
export const entryHasContent = e => !!e && JOURNAL_SECTIONS.some(s=> hasContent(e[s.id]));
/* 拼成一段文字（存进文档的 text 字段，方便以后搜索 / 导出；空的块不写） */
export const entryText = e => JOURNAL_SECTIONS.filter(s=> hasContent(e[s.id])).map(s=>`【${s.label}】${e[s.id].trim()}`).join('\n');
export const entryCharCount = e => JOURNAL_SECTIONS.reduce((n,s)=> n + charCount(e[s.id]), 0);

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

/* 预览：取第一行有字的内容，最多 40 字 */
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
