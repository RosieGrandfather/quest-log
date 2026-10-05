/* 日记的数据读写。每天一篇，文档 ID = 日期（YYYY-MM-DD），所以当天再进来打开的就是同一页。
   页面不会提前建空文档：第一次有内容保存时才创建。
   日记正文只放在 users/{uid}/journal 里，不进 log；log 里只有一条「写日记 +5」。 */
import { awardOnce } from './awards.js';
import { JOURNAL_POINTS, hasContent } from '../core/journal.js';

export async function loadJournalDay(cols, dateISO){
  const snap = await cols.journal.doc(dateISO).get();
  return snap.exists ? (snap.data().text || '') : '';
}

export async function loadRecentJournal(cols, limit = 60){
  const snap = await cols.journal.orderBy('dateISO','desc').limit(limit).get();
  return snap.docs.map(d=>({dateISO:d.data().dateISO || d.id, text:d.data().text || ''}));
}

/* 保存一天的日记。正文被清空时保留文档（text 为空串），不删除。
   只有「保存的就是今天」且有内容时才发 5 分（awardOnce 保证每天只发一次，补写以前的日子不发）。
   返回 true = 这次新发了积分 */
export async function saveJournalDay(cols, dateISO, text, todayISO){
  const ref = cols.journal.doc(dateISO);
  const prev = await ref.get();
  const now = Date.now();
  await ref.set({
    dateISO, text,
    createdAt: prev.exists ? (prev.data().createdAt || now) : now,
    updatedAt: now,
  });
  if(dateISO === todayISO && hasContent(text)){
    return awardOnce(cols.log, 'journal-'+dateISO,
      {category:'journal', label:'写日记', amount:JOURNAL_POINTS, dateISO});
  }
  return false;
}
