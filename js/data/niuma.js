/* 牛马鼓励器的数据：只有一篇文档 users/{uid}/niuma/settings，和积分、日记等其他数据完全分开。
   {start, end, lunchStart, lunchEnd, monthly, leave:[YYYY-MM-DD], updatedAt}。不进 log，不加积分 */
import { FieldValue } from '../firebase.js';
import { settingsFromDoc } from '../core/niuma.js';

export async function loadNiuma(cols){
  const snap = await cols.niuma.get();
  return settingsFromDoc(snap.exists ? snap.data() : null);
}

export async function saveNiumaSettings(cols, s){
  await cols.niuma.set({
    start: s.start, end: s.end, lunchStart: s.lunchStart, lunchEnd: s.lunchEnd,
    monthly: Number(s.monthly), updatedAt: Date.now(),
  }, {merge:true});
}

/* 今天请假 / 取消请假 */
export async function setLeave(cols, dateISO, on){
  await cols.niuma.set({
    leave: on ? FieldValue.arrayUnion(dateISO) : FieldValue.arrayRemove(dateISO),
    updatedAt: Date.now(),
  }, {merge:true});
}
