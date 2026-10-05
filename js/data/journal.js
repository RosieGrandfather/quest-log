/* 日记的数据读写。每天一篇，文档 ID = 日期（YYYY-MM-DD），所以当天再进来打开的就是同一页。
   页面不会提前建空文档：第一次有内容保存时才创建。
   日记正文只放在 users/{uid}/journal 里，不进 log；log 里只有一条「写日记 +5」。 */
import { awardOnce } from './awards.js';
import { JOURNAL_POINTS, hasContent, journalStreak, journalStreakBonus } from '../core/journal.js';

export async function loadJournalDay(cols, dateISO){
  const snap = await cols.journal.doc(dateISO).get();
  return snap.exists ? (snap.data().text || '') : '';
}

/* 读一个月（ym = 'YYYY-MM'）的日记，给日历用。单字段范围查询，不需要建索引 */
export async function loadJournalMonth(cols, ym){
  const snap = await cols.journal.where('dateISO','>=',ym+'-01').where('dateISO','<=',ym+'-31').get();
  return snap.docs.map(d=>({dateISO:d.data().dateISO || d.id, text:d.data().text || ''}));
}

/* 保存一天的日记。正文被清空时保留文档（text 为空串），不删除。
   只有「保存的就是今天」且有内容时才发 5 分（awardOnce 保证每天只发一次，补写以前的日子不发）。
   今天这 5 分是第一次发出时，顺便看连续天数到没到小惊喜（ID 带日期和天数：同一天不会重复发，断签后重新连到再发）。
   返回 {awarded, bonus}：awarded = 这次新发了 5 分；bonus = 这次拿到的连续奖励 {amount,title} 或 null */
export async function saveJournalDay(cols, dateISO, text, todayISO){
  const ref = cols.journal.doc(dateISO);
  const prev = await ref.get();
  const now = Date.now();
  await ref.set({
    dateISO, text,
    createdAt: prev.exists ? (prev.data().createdAt || now) : now,
    updatedAt: now,
  });
  const out = {awarded:false, bonus:null};
  if(dateISO === todayISO && hasContent(text)){
    out.awarded = await awardOnce(cols.log, 'journal-'+dateISO,
      {category:'journal', label:'写日记', amount:JOURNAL_POINTS, dateISO});
    if(out.awarded){
      try{
        const snap = await cols.log.where('category','==','journal').get();
        const n = journalStreak(snap.docs.map(d=> d.data().dateISO).filter(Boolean), new Date());
        const b = journalStreakBonus(n);
        if(b && await awardOnce(cols.log, `journalstreak-${dateISO}-${n}`,
            {category:'journalstreak', label:b.title+'奖励', amount:b.amount, dateISO})) out.bonus = b;
      }catch(e){ console.error('journal streak bonus failed', e); }
    }
  }
  return out;
}
