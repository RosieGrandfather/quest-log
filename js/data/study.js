/* 学习区的数据读写：进度、笔记、积分。
   积分全部写进主页面同一个 log 集合，所以回到主页面积分 / 历史 / 连续打卡都会自动更新。 */
import { awardOnce } from './awards.js';
import { localISO } from '../core/dates.js';
import { UNIT_POINTS, QUIZ_POINTS, QUIZ_PASS_PCT, unitKey, studyStreak, streakBonuses, dayUnitsBonus } from '../core/study.js';

/* 首次学完的日期列表（有效学习日） */
export async function loadStudyDates(cols){
  const snap = await cols.log.where('category','==','study').get();
  return snap.docs.map(d=> d.data().dateISO).filter(Boolean);
}

/* 学完一节：+100（只一次）。如果这是今天第一节新章节，检查连续学习里程碑。
   返回 {created, bonuses:[{amount,title}], streak, todayCount}（todayCount = 今天首次学完的章节数） */
export async function completeUnit(cols, course, unit){
  const today = localISO(new Date());
  const key = unitKey(course.id, unit.id);
  const created = await awardOnce(cols.log, `study-${key}`, {
    category:'study', label:`学完「${unit.title}」`, amount:UNIT_POINTS, dateISO:today,
    courseId:course.id, unitId:unit.id,
  });
  // 只在第一次学完时记完成日期，重复点不会把日期改掉
  if(created) await cols.studyProgress.doc(key).set({courseId:course.id, unitId:unit.id, completedISO:today, completedAt:Date.now()}, {merge:true});
  const dates = await loadStudyDates(cols);
  const streak = studyStreak(dates);
  const todayCount = dates.filter(d=> d===today).length;
  const bonuses = [];
  if(created){
    for(const b of streakBonuses(streak)){
      // ID 里带日期和天数：同一天再学一节不会重复发；断签后重新连到 7 天会再发
      const got = await awardOnce(cols.log, `studystreak-${today}-${streak}-${b.amount}`, {
        category:'studystreak', label:`${b.title}奖励`, amount:b.amount, dateISO:today,
      });
      if(got) bonuses.push(b);
    }
  }
  if(created){
    // 同一天学完 3 节：+100，每天只一次（ID 里只带日期）
    const db = dayUnitsBonus(todayCount);
    if(db){
      const got = await awardOnce(cols.log, `studyday-${today}`, {
        category:'studyday', label:`${db.title}奖励`, amount:db.amount, dateISO:today,
      });
      if(got) bonuses.push(db);
    }
  }
  return {created, bonuses, streak, todayCount};
}

/* 交卷：记录这次答题；第一次达到 80 分 +50（只一次，补做也算）。返回 {score, passed, awarded, progress} */
export async function submitQuiz(cols, course, unit, answers, score){
  const key = unitKey(course.id, unit.id);
  const ref = cols.studyProgress.doc(key);
  const prev = (await ref.get()).data() || {};
  const passed = score >= QUIZ_PASS_PCT;
  const progress = {
    courseId:course.id, unitId:unit.id,
    quizAttempts:(prev.quizAttempts||0)+1,
    quizBest:Math.max(prev.quizBest||0, score),
    quizPassed:!!prev.quizPassed || passed,
    lastAttempt:{answers, score, ts:Date.now()},
  };
  await ref.set(progress, {merge:true});
  let awarded = false;
  if(passed){
    awarded = await awardOnce(cols.log, `quiz-${key}`, {
      category:'quiz', label:`测验达标「${unit.title}」${score} 分`, amount:QUIZ_POINTS, dateISO:localISO(new Date()),
      courseId:course.id, unitId:unit.id,
    });
  }
  return {score, passed, awarded, progress:{...prev, ...progress}};
}

export function saveNote(cols, course, unit, text){
  return cols.studyNotes.doc(unitKey(course.id, unit.id)).set({courseId:course.id, unitId:unit.id, text, updatedAt:Date.now()});
}
export async function loadNote(cols, course, unit){
  const snap = await cols.studyNotes.doc(unitKey(course.id, unit.id)).get();
  return snap.exists ? (snap.data().text || '') : '';
}

/* 写作练习的草稿：和笔记同一个集合，文档 id 加 __essay 后缀，不会和每节的笔记冲突 */
const essayId = (course, unit)=> unitKey(course.id, unit.id) + '__essay';
export function saveEssay(cols, course, unit, text){
  return cols.studyNotes.doc(essayId(course, unit)).set({courseId:course.id, unitId:unit.id, essay:true, text, updatedAt:Date.now()});
}
export async function loadEssay(cols, course, unit){
  const snap = await cols.studyNotes.doc(essayId(course, unit)).get();
  return snap.exists ? {text: snap.data().text || '', ts: snap.data().updatedAt || 0} : {text:'', ts:0};
}

/* 词汇课「会 / 不会」标记：每节一篇文档 {marks:{词:'know'|'unknown'|''}} */
export async function loadVocabMarks(cols, course, unit){
  // 小节合并过（legacyIds 是合并前的旧小节 ID）：旧标记也读进来，新标记盖在上面
  const ids = [...(unit.legacyIds || []), unit.id];
  const snaps = await Promise.all(ids.map(id=> cols.vocabMarks.doc(unitKey(course.id, id)).get()));
  const out = {};
  snaps.forEach(sn=>{ if(sn.exists) Object.assign(out, sn.data().marks || {}); });
  return out;
}
export function saveVocabMark(cols, course, unit, word, value){
  return cols.vocabMarks.doc(unitKey(course.id, unit.id)).set(
    {courseId:course.id, unitId:unit.id, marks:{[word]:value}, updatedAt:Date.now()}, {merge:true});
}

/* 官方练习套题交卷：只记成绩和这次的作答（每题一个字符串，见 core/practice.js），不发积分。返回合并后的进度文档 */
export async function submitPractice(cols, course, unit, answers, sum){
  const key = unitKey(course.id, unit.id);
  const ref = cols.studyProgress.doc(key);
  const prev = (await ref.get()).data() || {};
  const progress = {
    courseId:course.id, unitId:unit.id,
    practiceAttempts:(prev.practiceAttempts||0)+1,
    practiceBest:Math.max(prev.practiceBest||0, sum.correct),
    practiceTotal:sum.total,
    practiceLast:{answers, correct:sum.correct, total:sum.total, ts:Date.now(), answerFormat:unit.answerFormat || null},
  };
  await ref.set(progress, {merge:true});
  return {...prev, ...progress};
}
