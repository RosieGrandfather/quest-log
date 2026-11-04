import { localISO } from './dates.js';

/* 牛马鼓励器：按「上下班时间 + 午休 + 月薪」现算今天已经赚了多少真钱（新币）。
   不存累计值，每次都按当前时间算，所以一整天不打开，晚上打开看到的也是完整的一天。
   和积分完全分开：不加分、不兑换、不打卡。
   - 周一到周五算工作日，月薪平均摊到当月每个工作日，再按有效工时（不含午休）摊到每一秒
   - 公共假期、请年假都是带薪的，钱照样按上班时间往上涨，只是小猫在睡觉
   - 周末不算钱；过了下班时间就停（不算加班） */

/* 新加坡公共假期（MOM 公布），只列落在周一到周五的日子（含周日顺延到周一的补假）。
   周六的假期本来就不上班，不用列。每年 MOM 公布新一年日期后在这里补上 */
export const SG_HOLIDAYS = new Set([
  // 2026
  '2026-01-01', // 元旦
  '2026-02-17', '2026-02-18', // 农历新年
  '2026-04-03', // 耶稣受难节
  '2026-05-01', // 劳动节
  '2026-05-27', // 哈芝节
  '2026-06-01', // 卫塞节（5/31 周日，顺延）
  '2026-08-10', // 国庆日（8/9 周日，顺延）
  '2026-11-09', // 屠妖节（11/8 周日，顺延）
  '2026-12-25', // 圣诞节
  // 2027
  '2027-01-01', // 元旦
  '2027-02-08', // 农历新年初二（2/7 周日，顺延；初一 2/6 是周六）
  '2027-03-10', // 开斋节
  '2027-03-26', // 耶稣受难节
  '2027-05-17', // 哈芝节
  '2027-05-20', // 卫塞节
  '2027-08-09', // 国庆日
  '2027-10-28', // 屠妖节
]);

/* 'HH:MM' → 当天第几分钟；格式不对返回 NaN */
export function parseHM(s){
  const m = /^(\d{1,2}):(\d{2})$/.exec(String(s || '').trim());
  if(!m) return NaN;
  const h = +m[1], min = +m[2];
  return h < 24 && min < 60 ? h * 60 + min : NaN;
}

/* 检查设置，没问题返回 ''，否则返回一句提示 */
export function settingsError(s){
  const [a, b, c, d] = [s.start, s.lunchStart, s.lunchEnd, s.end].map(parseHM);
  if([a, b, c, d].some(Number.isNaN)) return '时间格式不对';
  if(!(a < d)) return '下班时间要晚于上班时间';
  if(!(a <= b && b < c && c <= d)) return '午休要在上班时间之内，且结束晚于开始';
  const pay = Number(s.monthly);
  if(!(pay > 0) || pay > 1e7) return '请填月薪（大于 0 的数字）';
  return '';
}

/* Firestore 文档 → 设置；没设置过返回 null */
export function settingsFromDoc(d){
  if(!d || settingsError(d)) return null;
  return {
    start: d.start, end: d.end, lunchStart: d.lunchStart, lunchEnd: d.lunchEnd,
    monthly: Number(d.monthly),
    leave: Array.isArray(d.leave) ? d.leave.filter(x=> typeof x === 'string') : [],
  };
}

const isWeekend = date => date.getDay() === 0 || date.getDay() === 6;

/* 当月有几个工作日（周一到周五，公共假期也算，因为带薪） */
export function workdaysInMonth(date){
  const y = date.getFullYear(), m = date.getMonth();
  const days = new Date(y, m + 1, 0).getDate();
  let n = 0;
  for(let d = 1; d <= days; d++) if(!isWeekend(new Date(y, m, d))) n++;
  return n;
}

/* 这一天是什么日子：weekend / holiday / leave / work */
export function dayKind(date, leave = []){
  if(isWeekend(date)) return 'weekend';
  const iso = localISO(date);
  if(SG_HOLIDAYS.has(iso)) return 'holiday';
  if(leave.includes(iso)) return 'leave';
  return 'work';
}

/* 一天的有效工时（秒），不含午休 */
export function workSecondsPerDay(s){
  return ((parseHM(s.end) - parseHM(s.start)) - (parseHM(s.lunchEnd) - parseHM(s.lunchStart))) * 60;
}

/* 到 now 为止今天的有效工时（秒），扣掉午休，下班后封顶 */
export function workedSeconds(s, now){
  const sec = now.getHours() * 3600 + now.getMinutes() * 60 + now.getSeconds() + now.getMilliseconds() / 1000;
  const clip = (from, to) => Math.max(0, Math.min(sec, to * 60) - from * 60);
  return clip(parseHM(s.start), parseHM(s.lunchStart)) + clip(parseHM(s.lunchEnd), parseHM(s.end));
}

/* 现在处在一天里的哪一段：before / work / lunch / after */
export function phase(s, now){
  const sec = now.getHours() * 3600 + now.getMinutes() * 60 + now.getSeconds();
  const [a, b, c, d] = [s.start, s.lunchStart, s.lunchEnd, s.end].map(x=> parseHM(x) * 60);
  if(sec < a) return 'before';
  if(sec >= d) return 'after';
  if(sec >= b && sec < c) return 'lunch';
  return 'work';
}

/* 下一个时间点还剩多少毫秒：上班前 → 上班；上班中 → 下班；午休 → 午休结束；下班后 → null */
export function nextMarkMs(s, now){
  const p = phase(s, now);
  const target = p === 'before' ? s.start : p === 'work' ? s.end : p === 'lunch' ? s.lunchEnd : null;
  if(!target) return null;
  const t = new Date(now); t.setHours(0, parseHM(target), 0, 0);
  return Math.max(0, t - now);
}

export const dailyPay = (s, date) => s.monthly / workdaysInMonth(date);

/* 今天已赚（周末 0） */
export function earnedToday(s, now){
  if(isWeekend(now)) return 0;
  return dailyPay(s, now) * Math.min(1, workedSeconds(s, now) / workSecondsPerDay(s));
}

/* 本月累计 = 本月之前的工作日（整天） + 今天的进度 */
export function monthToDate(s, now){
  let full = 0;
  for(let d = 1; d < now.getDate(); d++) if(!isWeekend(new Date(now.getFullYear(), now.getMonth(), d))) full++;
  return full * dailyPay(s, now) + earnedToday(s, now);
}

/* 今日工时进度 0~1（周末 0） */
export const dayProgress = (s, now) => isWeekend(now) ? 0 : Math.min(1, workedSeconds(s, now) / workSecondsPerDay(s));

/* S$1,234.5678 */
export function fmtMoney(x, digits = 4){
  return 'S$' + Number(x).toLocaleString('en-US', {minimumFractionDigits: digits, maximumFractionDigits: digits});
}

/* 1小时15分58秒 / 15分58秒 / 58秒 */
export function fmtDuration(ms){
  const t = Math.max(0, Math.floor(ms / 1000));
  const h = Math.floor(t / 3600), m = Math.floor(t % 3600 / 60), sec = t % 60;
  if(h) return `${h}小时${m}分${sec}秒`;
  if(m) return `${m}分${sec}秒`;
  return `${sec}秒`;
}

export const fmtHours = sec => (sec / 3600).toFixed(2);

/* 页面显示什么：小猫的状态 + 一句话 */
export function catMode(s, now){
  const kind = dayKind(now, s.leave);
  if(kind === 'weekend') return {cat:'weekend', label:'周末 · 学习和休息时间'};
  const p = phase(s, now);
  if(kind === 'holiday' || kind === 'leave'){
    const what = kind === 'holiday' ? '公共假期' : '请假中';
    return {cat:'sleep', label: p === 'after' ? `${what} · 今天收工` : `${what} · 带薪休息`};
  }
  if(p === 'before') return {cat:'sleep', label:'还没上班'};
  if(p === 'lunch') return {cat:'sleep', label:'午休中'};
  if(p === 'after') return {cat:'done', label:'今天收工啦'};
  return {cat:'run', label:'上班中'};
}
