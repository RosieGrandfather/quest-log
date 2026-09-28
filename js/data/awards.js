import { fs } from '../firebase.js';

/* 「只加一次分」：用固定的文档 ID + 事务写一条 log。
   已经存在就什么都不做，所以手机和电脑同时触发也只会记一次。
   返回 true = 这次新加上了；false = 之前已经加过。
   每日签到用 'daily-YYYY-MM-DD'，以后学完一节 / 测验达标也用这个。 */
export async function awardOnce(logCol, docId, entry){
  const ref = logCol.doc(docId);
  return fs.runTransaction(async tx=>{
    const snap = await tx.get(ref);
    if(snap.exists) return false;
    tx.set(ref, {note:'', ts:Date.now(), ...entry, kind:'earn'});
    return true;
  });
}
