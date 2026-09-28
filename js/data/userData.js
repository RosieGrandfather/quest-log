import { fs } from '../firebase.js';
import { SEED_SECTIONS, SEED_TASKS, SEED_REWARDS, LEGACY_SECTIONS, SCHEMA_VERSION } from '../core/constants.js';

/* 登录后先跑一次：新用户写入模板；老账号把代码里的板块迁移进数据库。
   完成后在 meta/app 里记 schemaVersion，之后不再执行。每一步都可以安全地重复执行。 */
export async function ensureUserData(cols){
  try{
    const meta = await cols.meta.get();
    if(meta.exists && (meta.data().schemaVersion||0) >= SCHEMA_VERSION) return;
    const [t, r, sec] = await Promise.all([cols.tasks.limit(1).get(), cols.rewards.limit(1).get(), cols.sections.get()]);
    if(t.empty && r.empty && sec.empty) await seedNewUser(cols);
    else await migrateLegacySections(cols, sec);
    await cols.meta.set({schemaVersion:SCHEMA_VERSION, migratedAt:Date.now()}, {merge:true});
  }catch(e){ console.error('ensureUserData failed', e); }
}

async function seedNewUser(cols){
  const batch = fs.batch();
  SEED_SECTIONS.forEach(({id, ...d})=> batch.set(cols.sections.doc(id), d));
  SEED_TASKS.forEach(({id, ...d})=> batch.set(cols.tasks.doc(id), {...d, active:true}));
  SEED_REWARDS.forEach(({id, ...d})=> batch.set(cols.rewards.doc(id), {...d, active:true}));
  await batch.commit();
}

async function migrateLegacySections(cols, existingSnap){
  const existing = new Set(existingSnap.docs.map(d=>d.id));
  const writes = [];
  // 7 个老板块，已存在的（比如已经改过名）不覆盖。「其他」排在已有自定义板块后面
  LEGACY_SECTIONS.forEach((c, i)=>{
    if(existing.has(c.id)) return;
    const ts = c.id==='custom' ? Date.now() : i+1;
    writes.push(b=> b.set(cols.sections.doc(c.id), {label:c.label, short:c.short, ts}));
  });
  // 上一版自定义板块在任务 / 记录里存成 'sec_' + 文档 ID，统一成直接用文档 ID
  const prefixed = col => col.where('category','>=','sec_').where('category','<','sec_').get();
  const [pt, pl] = await Promise.all([prefixed(cols.tasks), prefixed(cols.log)]);
  [...pt.docs, ...pl.docs].forEach(d=>{
    writes.push(b=> b.update(d.ref, {category: d.data().category.slice(4)}));
  });
  for(let i=0; i<writes.length; i+=400){
    const batch = fs.batch();
    writes.slice(i, i+400).forEach(w=> w(batch));
    await batch.commit();
  }
}
