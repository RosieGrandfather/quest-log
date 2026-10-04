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
