import { S } from './state.js';
import { escapeHTML } from '../core/html.js';
import { iconForTask } from '../core/icons.js';
import { localISO } from '../core/dates.js';
import { showToast, openCelebrate, closeOnBackdrop, makeConfirmDelete } from '../ui/common.js';
import { render } from './render.js';
import { openSectionModal, onDeleteSectionClick, sectionDelete } from './sections.js';

/* 「记录」Tab：按板块分组的任务卡片，完成 / 编辑 / 删除 */
let editingTaskId = null;
let taskTarget = null;
const taskDelete = makeConfirmDelete(()=> render());

export function renderTasks(){
  const wrap = document.getElementById('tasksWrap');
  const { tasks, sections } = S;
  if(!tasks.length && !sections.length){
    wrap.innerHTML = '<div class="entry-empty">还没有板块，点下面「添加自定义板块」开始吧</div>';
    return;
  }
  const ORPHAN = '__orphan__';
  const known = new Set(sections.map(c=>c.id));
  const groups = {[ORPHAN]:[]};
  sections.forEach(c=>{ groups[c.id] = []; });
  // 找不到板块的任务（理论上不该出现）放进「未分类」，不会丢
  tasks.forEach(t=>{ groups[known.has(t.category) ? t.category : ORPHAN].push(t); });
  const list = groups[ORPHAN].length ? [...sections, {id:ORPHAN, label:'未分类', fixed:true}] : sections;
  wrap.innerHTML = list.map(c=>{
    const items = groups[c.id] || [];
    const delConfirming = sectionDelete.isPending(c.id);
    const actions = !c.fixed ? `<span class="sec-actions">
        <button class="btn-del" data-rename-sec="${c.id}">改名</button>
        <button class="btn-del ${delConfirming?'confirming':''}" data-del-sec="${c.id}">${delConfirming?'确认删除？':'删除板块'}</button>
      </span>` : '';
    const body = items.length
      ? `<div class="reward-grid">${items.map(taskCardHTML).join('')}</div>`
      : `<div class="entry-empty">这个板块还没有任务，点下面「添加自定义任务」选它就行</div>`;
    return `<div class="tier-block">
      <div class="tier-title">${escapeHTML(c.label)}${actions}</div>
      ${body}
    </div>`;
  }).join('');
  wrap.querySelectorAll('[data-rename-sec]').forEach(btn=>{
    btn.addEventListener('click', ()=> openSectionModal(sections.find(x=>x.id===btn.getAttribute('data-rename-sec'))));
  });
  wrap.querySelectorAll('[data-del-sec]').forEach(btn=>{
    btn.addEventListener('click', ()=> onDeleteSectionClick(btn.getAttribute('data-del-sec')));
  });
  wrap.querySelectorAll('[data-log-task]').forEach(btn=>{
    btn.addEventListener('click', ()=> onLogTaskClick(btn.getAttribute('data-log-task')));
  });
  wrap.querySelectorAll('[data-edit-task]').forEach(btn=>{
    btn.addEventListener('click', ()=> onEditTaskClick(btn.getAttribute('data-edit-task')));
  });
  wrap.querySelectorAll('[data-del-task]').forEach(btn=>{
    btn.addEventListener('click', ()=> onDeleteTaskClick(btn.getAttribute('data-del-task')));
  });
}

function taskCardHTML(t){
  const delConfirming = taskDelete.isPending(t.id);
  return `<div class="reward-card">
    <div class="reward-top">
      <div class="reward-icon-badge" style="background:var(--teal-soft);color:var(--teal)">${iconForTask(t)}</div>
      <div class="reward-name-wrap">
        <div class="reward-name">${escapeHTML(t.name)}</div>
      </div>
      <div class="reward-cost mono">+${t.points} 分</div>
    </div>
    <div class="reward-btn-row">
      <button class="btn-edit" data-edit-task="${t.id}">编辑</button>
      <button class="btn-del ${delConfirming?'confirming':''}" data-del-task="${t.id}">${delConfirming?'确认删除？':'删除'}</button>
      <button class="btn-redeem" data-log-task="${t.id}">完成 ✓</button>
    </div>
  </div>`;
}

function onLogTaskClick(id){
  const t = S.tasks.find(x=>x.id===id);
  if(!t) return;
  taskTarget = t;
  document.getElementById('taskConfirmText').textContent =
    `确定要记录一次「${t.name}」任务吗？将获得 ${t.points} 积分。`;
  document.getElementById('taskConfirmError').hidden = true;
  document.getElementById('taskConfirmModal').hidden = false;
}
function closeTaskConfirm(){
  document.getElementById('taskConfirmModal').hidden = true;
  taskTarget = null;
}
async function confirmTaskLog(){
  if(!taskTarget) return;
  const t = taskTarget;
  const errEl = document.getElementById('taskConfirmError');
  const btn = document.getElementById('confirmTaskBtn');
  btn.disabled = true;
  try{
    await S.cols.log.add({kind:'earn', category:t.category||'custom', label:t.name, amount:t.points, note:'', dateISO:localISO(new Date()), ts:Date.now()});
    closeTaskConfirm();
    openCelebrate(`你太棒了！完成了一次「${escapeHTML(t.name)}」任务 🎉<br>已添加 <span class="mono">${t.points}</span> 积分！`);
  }catch(e){
    errEl.textContent = '记录失败：' + (e && e.message ? e.message : '请重试');
    errEl.hidden = false;
  }finally{
    btn.disabled = false;
  }
}

function onEditTaskClick(id){
  const t = S.tasks.find(x=>x.id===id);
  if(t) openTaskModal(t);
}
function onDeleteTaskClick(id){
  if(taskDelete.click(id)){
    S.cols.tasks.doc(id).delete().catch(()=>{ showToast('删除失败，请重试'); });
  }
}

function openTaskModal(t){
  const { sections } = S;
  if(!sections.length){ showToast('请先添加一个板块'); return; }
  editingTaskId = t ? t.id : null;
  document.getElementById('taskModalTitle').textContent = t ? '编辑任务' : '添加自定义任务';
  document.getElementById('submitTask').textContent = t ? '保存修改' : '添加';
  document.getElementById('taskCategory').innerHTML = sections.map(c=>`<option value="${c.id}">${escapeHTML(c.label)}</option>`).join('');
  document.getElementById('taskName').value = t ? t.name : '';
  const cur = t && t.category;
  document.getElementById('taskCategory').value = sections.some(c=>c.id===cur) ? cur : sections[0].id;
  document.getElementById('taskPoints').value = t ? t.points : '';
  document.getElementById('taskFormError').hidden = true;
  document.getElementById('taskModal').hidden = false;
}
function closeTaskModal(){ document.getElementById('taskModal').hidden = true; editingTaskId = null; }

function submitTask(){
  const errEl = document.getElementById('taskFormError');
  const name = document.getElementById('taskName').value.trim();
  const category = document.getElementById('taskCategory').value;
  const rawPoints = document.getElementById('taskPoints').value;
  const points = Number(rawPoints);
  if(!name){ errEl.textContent='请填写任务名称'; errEl.hidden=false; return; }
  if(rawPoints===''||isNaN(points)||points<0){ errEl.textContent='请填写一个不小于 0 的积分数'; errEl.hidden=false; return; }
  const btn = document.getElementById('submitTask');
  btn.disabled = true;
  const payload = {name, category, points};
  const wasEditing = !!editingTaskId;
  const op = wasEditing
    ? S.cols.tasks.doc(editingTaskId).update(payload)
    : S.cols.tasks.add({...payload, active:true, ts:Date.now()});
  op.then(()=>{ closeTaskModal(); showToast(wasEditing ? '已保存修改' : '已添加任务'); })
    .catch((err)=>{ errEl.textContent='保存失败：'+(err&&err.message?err.message:'请重试'); errEl.hidden=false; })
    .finally(()=>{ btn.disabled = false; });
}

export function wireTasks(){
  document.getElementById('openAddTask').addEventListener('click', ()=> openTaskModal());
  document.getElementById('cancelTask').addEventListener('click', closeTaskModal);
  document.getElementById('submitTask').addEventListener('click', submitTask);
  closeOnBackdrop('taskModal', closeTaskModal);
  document.getElementById('cancelTaskConfirm').addEventListener('click', closeTaskConfirm);
  document.getElementById('confirmTaskBtn').addEventListener('click', confirmTaskLog);
  closeOnBackdrop('taskConfirmModal', closeTaskConfirm);
}
