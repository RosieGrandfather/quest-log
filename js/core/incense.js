import { computeStreak } from './stats.js';

/* 电子烧香：点「上香」点燃三炷香，烧完之前不能再上；每天可以上多次，不加积分。
   另有电子木鱼：敲一下功德 +1，只是计数 */

/* 一炷香烧多久（毫秒）。真香要半小时以上，这里取 3 分钟，够静下心来 */
export const BURN_MS = 3 * 60 * 1000;

/* 常用的心愿，点一下填进输入框；也可以自己写 */
export const WISH_PRESETS = ['考试顺利', '身体健康', '平平安安', '心想事成', '工作顺利', '早睡早起'];
export const WISH_MAX = 60;

/* 心愿去掉首尾空白、合并连续空白，超长截断；空串 = 不许愿只上香 */
export const cleanWish = text => (text || '').replace(/\s+/g, ' ').trim().slice(0, WISH_MAX);

/* 烧到哪儿了：0 = 刚点着，1 = 烧完（没点过也算烧完） */
export function burnProgress(litAt, now = Date.now()){
  if(!litAt) return 1;
  return Math.min(1, Math.max(0, (now - litAt) / BURN_MS));
}
export const isBurning = (litAt, now = Date.now()) => burnProgress(litAt, now) < 1;
export const remainingMs = (litAt, now = Date.now()) => Math.round((1 - burnProgress(litAt, now)) * BURN_MS);

/* 剩余时间显示成 m:ss */
export function fmtRemaining(ms){
  const s = Math.ceil(Math.max(0, ms) / 1000);
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`;
}

/* 连续上香天数：今天还没上时从昨天往前数 */
export function incenseStreak(dates, now = new Date()){
  return computeStreak(new Set(dates), now);
}

/* 数据库文档 → 一天的记录。sticks = 当天上了几次香，wishes = [{text, ts}]，merit = 当天敲木鱼次数 */
export function dayFromDoc(data){
  const d = {sticks:0, wishes:[], merit:0, litAt:0};
  if(!data) return d;
  if(Number.isFinite(data.sticks)) d.sticks = data.sticks;
  if(Number.isFinite(data.merit)) d.merit = data.merit;
  if(Number.isFinite(data.litAt)) d.litAt = data.litAt;
  if(Array.isArray(data.wishes)) d.wishes = data.wishes.filter(w=> w && typeof w.text === 'string' && w.text);
  return d;
}

/* 敲到这些次数时说一句吉利话（当天累计） */
const MERIT_LINES = {10:'心静了一点', 33:'三十三下，诸事顺遂', 108:'一百零八下，烦恼尽消', 300:'功德圆满', 1000:'木鱼都快被你敲穿了'};
export const meritLine = n => MERIT_LINES[n] || null;
