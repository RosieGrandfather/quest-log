/* 城邦地图的数据读写。每个项目一篇文档 users/{uid}/projects/{id}，步骤放在文档里的 steps 数组。
   点亮一座城 = 在事务里把这一步的 doneAt 写上 + 用固定 id 发分（awardOnce，所以重复点、手机电脑同时点都只发一次）。 */
import { fs } from '../firebase.js';
import { awardOnce } from './awards.js';
import { normalizeProject, dueAwards } from '../core/map.js';
import { localISO } from '../core/dates.js';

const plain = p => ({
  title: p.title, templateId: p.templateId, icon: p.icon, slot: p.slot, color: p.color,
  parked: !!p.parked, createdAt: p.createdAt,
  steps: p.steps.map(s => ({id: s.id, title: s.title, detail: s.detail || '', refs: s.refs || [], stage: s.stage || '主线', doneAt: s.doneAt || null})),
});

export function newProjectId(){ return 'p' + Date.now().toString(36) + Math.random().toString(36).slice(2, 5); }

export async function loadProjects(cols){
  const snap = await cols.projects.get();
  return snap.docs.map(d => normalizeProject(d.id, d.data())).sort((a, b) => (a.createdAt || 0) - (b.createdAt || 0));
}
export async function saveProject(cols, project){ await cols.projects.doc(project.id).set(plain(project)); }
export async function deleteProject(cols, id){ await cols.projects.doc(id).delete(); }

/* 标记完成 / 取消完成。返回 {project, awards}：project 是最新的项目，awards 是这次新发出的分 [{label, amount}]。
   取消完成不会扣已经发过的分（再次完成也不会再发）。 */
export async function setStepDone(cols, projectId, stepId, done){
  const ref = cols.projects.doc(projectId);
  const project = await fs.runTransaction(async tx => {
    const snap = await tx.get(ref);
    if(!snap.exists) throw new Error('项目不存在');
    const p = normalizeProject(projectId, snap.data());
    const s = p.steps.find(x => x.id === stepId);
    if(!s) throw new Error('步骤不存在');
    if(done && !s.doneAt) s.doneAt = Date.now();
    if(!done) s.doneAt = null;
    tx.set(ref, plain(p));
    return p;
  });
  const awards = [];
  if(done){
    for(const a of dueAwards(project, stepId)){
      try{
        if(await awardOnce(cols.log, a.id, {category: a.category, label: a.label, amount: a.amount, dateISO: localISO(new Date())})) awards.push({label: a.label, amount: a.amount});
      }catch(e){ console.error('map award failed', e); }
    }
  }
  return {project, awards};
}
