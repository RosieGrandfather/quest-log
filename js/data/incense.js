/* 电子烧香的数据读写。每天一篇，文档 ID = 日期（YYYY-MM-DD）：
   {dateISO, sticks, wishes:[{text,ts}], merit, litAt}。不进 log，不加积分。
   累计数放在 meta/incense（totalSticks / totalMerit），用 increment 写，手机电脑同时敲也不会丢 */
import { FieldValue } from '../firebase.js';
import { dayFromDoc, isBurning } from '../core/incense.js';

export async function loadIncenseDay(cols, dateISO){
  const snap = await cols.incense.doc(dateISO).get();
  return dayFromDoc(snap.exists ? snap.data() : null);
}

/* 最近 n 天有记录的日子（给连续天数和心愿列表用）。单字段范围查询，不需要建索引 */
export async function loadIncenseSince(cols, fromISO){
  const snap = await cols.incense.where('dateISO','>=',fromISO).get();
  return snap.docs.map(d=>({dateISO:d.data().dateISO || d.id, ...dayFromDoc(d.data())}));
}

export async function loadIncenseTotals(cols){
  const snap = await cols.incenseMeta.get();
  const d = snap.exists ? snap.data() : {};
  return {totalSticks:Number(d.totalSticks)||0, totalMerit:Number(d.totalMerit)||0};
}

/* 上香：还在烧就不让再上（返回 false），否则记一次 */
export async function lightIncense(cols, dateISO, wish, now = Date.now()){
  const ref = cols.incense.doc(dateISO);
  const prev = await ref.get();
  if(prev.exists && isBurning(prev.data().litAt, now)) return false;
  const data = {dateISO, sticks:FieldValue.increment(1), litAt:now, updatedAt:now};
  if(wish) data.wishes = FieldValue.arrayUnion({text:wish, ts:now});
  await ref.set(data, {merge:true});
  await cols.incenseMeta.set({totalSticks:FieldValue.increment(1)}, {merge:true});
  return true;
}

/* 木鱼：攒一批再写（n = 这批敲了几下） */
export async function addMerit(cols, dateISO, n){
  if(!n) return;
  await cols.incense.doc(dateISO).set({dateISO, merit:FieldValue.increment(n), updatedAt:Date.now()}, {merge:true});
  await cols.incenseMeta.set({totalMerit:FieldValue.increment(n)}, {merge:true});
}
