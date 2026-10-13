/* 每日提醒：7 天一轮，每天早上 7 点之后第一次打开主页面弹一次。纯数据和纯函数，方便测试。
   想改文字，直接改下面这个数组就行（第几天 = 数组第几项，不用改别处） */
import { localISO } from './dates.js';

export const SHOW_AFTER_HOUR = 7;

export const REMINDERS = [
  {boundary:'别人的行为，不定义我的价值。',
   positive:'我有能力学习和掌握新的技能。'},
  {boundary:'我可以反思，但不必反复审判自己。',
   positive:'我已经完成过很多困难的事，过去的成果是真实的。'},
  {boundary:'不是所有问题，都是我的责任。',
   positive:'我有能力解决问题，也有能力创造机会。'},
  {boundary:'我不需要获得所有人的认可。',
   positive:'我的人生有很多可能性，现在的环境不是我的终点。'},
  {boundary:'停止自证，把精力留给成长。',
   positive:'我相信自己的判断，也允许自己犯错和进步。'},
  {boundary:'保持专业，但收回过度投入。',
   positive:'我的时间和精力很宝贵，我有权决定如何使用它们。'},
  {boundary:'不纠缠，不内耗，有计划地向前走。',
   positive:'我有权选择自己的方向，每一个小行动都在扩大我的选择。'},
];

/* 现在该不该弹：已过早上 7 点，且今天还没弹过（lastISO 是上次弹出的日期） */
export const shouldShowReminder = (now, lastISO) =>
  now.getHours() >= SHOW_AFTER_HOUR && lastISO !== localISO(now);

/* 下一次弹第几天（1–7）：没弹过 → Day 1；Day 7 之后回到 Day 1 */
export const nextReminderDay = prev => ((Number(prev) || 0) % REMINDERS.length) + 1;
