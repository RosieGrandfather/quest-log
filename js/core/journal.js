import { computeStreak } from './stats.js';

/* 日记：每天只要写了内容（去掉空白后不为空）就自动 +5 分，每天一次 */
export const JOURNAL_POINTS = 5;

export const hasContent = text => typeof text === 'string' && text.trim().length > 0;

/* 字数：不算空白（中文按字，英文按字符，够用即可） */
export const charCount = text => (text || '').replace(/\s/g, '').length;

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
