/* 学习区的纯规则（不碰浏览器和 Firebase，可以测试） */
import { computeStreak } from './stats.js';

export const UNIT_POINTS = 100;        // 学完一节，只加一次
export const QUIZ_POINTS = 50;         // 测验第一次达到及格线，只加一次
export const QUIZ_PASS_PCT = 80;
export const DAY_UNITS_TARGET = 3;     // 同一天学完 3 节新章节
export const DAY_UNITS_BONUS = 100;    // 额外奖励，每天只一次

/* 进度 / 笔记文档 ID：一门课的一节 */
export const unitKey = (courseId, unitId) => `${courseId}__${unitId}`;

/* 测验得分（百分制，四舍五入）。answers[i] 是第 i 题选的选项下标，没答为 null */
export function scoreQuiz(questions, answers){
  if(!questions.length) return 0;
  const correct = questions.filter((q, i)=> answers[i] === q.answer).length;
  return Math.round(correct / questions.length * 100);
}

/* 连续学习天数：只有「那天学完了至少一节新章节」才算有效学习日。
   studyDates = 所有首次学完章节的日期（log 里 category 为 'study' 的 dateISO） */
export function studyStreak(studyDates, now = new Date()){
  return computeStreak(new Set(studyDates), now);
}

/* 连续学到第 n 天时的额外奖励（可能为空）。
   每满 7 天 +100；第 30 天 +500（只一次）；第 100 / 200 / 300 天 +500；第 365 天 +1000 */
export function streakBonuses(n){
  const out = [];
  if(n > 0 && n % 7 === 0) out.push({amount:100, title:`连续学习 ${n} 天`});
  if(n === 30) out.push({amount:500, title:'连续学习 30 天'});
  if(n === 100 || n === 200 || n === 300) out.push({amount:500, title:`连续学习 ${n} 天`});
  if(n === 365) out.push({amount:1000, title:'连续学习 365 天'});
  return out;
}

/* 同一天学完 n 节新章节时的额外奖励：满 3 节 +100，每天只发一次（再多学也不重复发）。
   n 是「今天首次学完的章节数」，没达到返回 null */
export function dayUnitsBonus(n){
  if(n >= DAY_UNITS_TARGET) return {amount:DAY_UNITS_BONUS, title:`同一天学完 ${DAY_UNITS_TARGET} 节`};
  return null;
}
