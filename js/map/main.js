/* 城邦地图页入口：登录 → 读项目 → 画 3D 地图 → 处理「开到城 / 点亮 / 编辑」。
   3D 部分在 scene.js（动态加载：加载失败或设备不支持 WebGL 时，退回到列表模式，照样能打卡）。 */
import { auth, signInWithGoogle, userCols } from '../firebase.js';
import { ensureDailyLoginBonus, resetDailyBonus } from '../data/dailyBonus.js';
import { loadProjects, saveProject, deleteProject, setStepDone, newProjectId } from '../data/map.js';
import { showToast, openCelebrate, closeCelebrate, closeOnBackdrop, makeConfirmDelete } from '../ui/common.js';
import { escapeHTML as esc } from '../core/html.js';
import { TEMPLATES, PROJECT_COLORS, STEP_POINTS, MAX_ACTIVE_PROJECTS, newProject, freeSlot, progressOf, stagesOf, nextStepId, parseRefs, refsToText, activeCount } from '../core/map.js';

const $ = id => document.getElementById(id);
const M = {cols: null, uid: null, projects: [], selectedId: null, scene: null, noScene: false, card: null, edit: null, sheetOpen: false, renaming: null, busy: false};

const store = {
  get(k){ try{ return localStorage.getItem(k); }catch(e){ return null; } },
  set(k, v){ try{ localStorage.setItem(k, v); }catch(e){ /* 隐私模式等：忽略 */ } },
};
const proj = id => M.projects.find(p => p.id === id) || null;
const selected = () => proj(M.selectedId);
const replaceProject = p => { const i = M.projects.findIndex(x => x.id === p.id); if(i >= 0) M.projects[i] = p; else M.projects.push(p); };
const safeUrl = u => /^https?:\/\//i.test(u || '') ? u : null;

/* ---------- 顶部项目标签 ---------- */
function renderChips(){
  $('chips').innerHTML = M.projects.map(p => {
    const g = progressOf(p);
    return `<button class="chip${p.parked ? ' parked' : ''}" role="tab" aria-selected="${p.id === M.selectedId}" data-id="${p.id}" style="--c:${esc(p.color)}"><span class="dot"></span>${esc(p.icon)} ${esc(p.title)}<span class="cnt">${g.done}/${g.total}</span></button>`;
  }).join('');
}

/* ---------- 底部「下一站」 ---------- */
function renderNext(){
  const p = selected(), el = $('nextCard');
  if(!p){
    el.innerHTML = `<div class="empty">还没有项目。点右上角 ＋ 选一个模板开始，每一步是一座城，做完一步亮一座城。</div>`;
    return;
  }
  const g = progressOf(p);
  const head = `<div class="k" style="--c:${esc(p.color)}"><span class="dot"></span>${esc(p.title)} · ${g.done}/${g.total}</div>`;
  if(p.parked){
    el.innerHTML = `${head}<div class="t">这个项目已停放，不占「同时进行」的名额。</div><div class="row"><button class="go" data-act="unpark">恢复这个项目</button><button class="more" data-act="sheet">列表</button></div>`; return;
  }
  if(g.total === 0){ el.innerHTML = `${head}<div class="t">这个项目还没有步骤。</div><div class="row"><button class="go" data-act="addstep">添加第一步</button></div>`; return; }
  if(g.finished){
    el.innerHTML = `${head}<div class="t">🎉 这个项目的城全部亮了。</div><div class="row"><button class="go" data-act="god">看看整张地图</button><button class="more" data-act="sheet">列表</button></div>`; return;
  }
  const s = p.steps[g.nextIndex], stage = stagesOf(p.steps).find(x => x.idx.includes(g.nextIndex));
  el.innerHTML = `<div class="k" style="--c:${esc(p.color)}"><span class="dot"></span>下一站 · 第 ${g.nextIndex + 1} 步${stage ? ' · ' + esc(stage.name) : ''}</div>
    <div class="t">${esc(s.title)}</div>
    <div class="row"><button class="go" data-act="go">${M.scene ? '🚗 开过去' : '查看这一步'}</button><button class="more" data-act="detail">详情</button></div>`;
}

/* ---------- 城的卡片 ---------- */
function openCard(pid, idx, {arrived = false} = {}){
  const p = proj(pid); if(!p || !p.steps[idx]) return;
  const s = p.steps[idx];
  M.card = {pid, idx};
  const refs = (s.refs || []).map(r => { const u = safeUrl(r.url); return u ? `<li><a href="${esc(u)}" target="_blank" rel="noopener noreferrer">${esc(r.title || u)}</a></li>` : `<li><span>${esc(r.title || '')}</span></li>`; }).join('');
  const done = !!s.doneAt;
  const stageName = (stagesOf(p.steps).find(x => x.idx.includes(idx)) || {}).name || '';
  $('cityCard').innerHTML = `
    <span class="stage-tag">${esc(p.title)} · 第 ${idx + 1} 步 · ${esc(stageName)}</span>
    <h3>${arrived ? '到达：' : ''}${esc(s.title)}</h3>
    ${done ? '<p class="lit-note">✓ 这座城已经点亮</p>' : ''}
    ${s.detail ? `<p class="detail">${esc(s.detail)}</p>` : ''}
    ${refs ? `<ul class="refs">${refs}</ul>` : ''}
    <div class="city-actions">
      ${done ? '' : `<button class="btn-primary" data-act="complete">做完了，点亮这座城 +${STEP_POINTS}</button>`}
      ${done ? '<button class="btn-ghost solid" data-act="uncomplete">标记为未完成</button>' : ''}
      ${M.scene && !arrived ? '<button class="btn-ghost solid" data-act="drive">🚗 开过去</button>' : ''}
      <button class="btn-ghost solid" data-act="edit">编辑</button>
      <button class="btn-ghost solid" data-act="close">${arrived && !done ? '稍后再做' : '关闭'}</button>
    </div>`;
  $('cityModal').hidden = false;
}
function closeCard(){ M.card = null; $('cityModal').hidden = true; }

async function complete(pid, stepId, done){
  if(M.busy) return; M.busy = true;
  try{
    const {project, awards} = await setStepDone(M.cols, pid, stepId, done);
    replaceProject(project);
    closeCard();
    if(M.scene) M.scene.setProjects(M.projects, M.selectedId);
    renderAll();
    if(done){
      const total = awards.reduce((a, x) => a + x.amount, 0);
      if(awards.length > 1){
        $('celebrateTitle').textContent = project.steps.every(s => s.doneAt) ? '整个项目亮了！' : '阶段完成！';
        openCelebrate(awards.map(a => `${esc(a.label)}　<b>+${a.amount}</b>`).join('<br>') + `<br><br>共 <b>+${total}</b> 分`);
      } else if(awards.length === 1){
        showToast(`城市亮了 · +${total} 分`);
      } else {
        showToast('这座城亮了（这一步的分之前已经拿过）');
      }
    } else showToast('已标记为未完成（已拿的分不会扣）');
  }catch(e){ console.error(e); showToast('保存失败，请再试一次'); }
  finally{ M.busy = false; }
}

/* ---------- 编辑步骤 ---------- */
function openEdit(pid, stepId){
  const p = proj(pid); if(!p) return;
  const s = stepId ? p.steps.find(x => x.id === stepId) : null;
  M.edit = {pid, stepId: s ? s.id : null, delArmed: false};
  $('editTitle').textContent = s ? '编辑步骤' : '添加一步';
  $('eTitle').value = s ? s.title : '';
  $('eStage').value = s ? s.stage : (p.steps.length ? p.steps[p.steps.length - 1].stage : '主线');
  $('eDetail').value = s ? s.detail : '';
  $('eRefs').value = s ? refsToText(s.refs) : '';
  $('editMore').hidden = !s;
  $('editDelete').textContent = '删除这步';
  $('editErr').textContent = '';
  $('editModal').hidden = false;
  setTimeout(() => $('eTitle').focus(), 30);
}
async function persist(p, msg){
  try{ await saveProject(M.cols, p); replaceProject(p); if(M.scene) M.scene.setProjects(M.projects, M.selectedId); renderAll(); if(msg) showToast(msg); return true; }
  catch(e){ console.error(e); showToast('保存失败，请再试一次'); return false; }
}
async function saveEdit(){
  const {pid, stepId} = M.edit; const p = proj(pid); if(!p) return;
  const title = $('eTitle').value.trim();
  if(!title){ $('editErr').textContent = '先写一下这一步做什么'; return; }
  const next = {...p, steps: p.steps.map(s => ({...s}))};
  const fields = {title, stage: $('eStage').value.trim() || '主线', detail: $('eDetail').value.trim(), refs: parseRefs($('eRefs').value)};
  if(stepId) Object.assign(next.steps.find(s => s.id === stepId), fields);
  else next.steps.push({id: nextStepId(next), doneAt: null, ...fields});
  if(await persist(next, stepId ? '已保存' : '添加了一座新城，在路的尽头')){ $('editModal').hidden = true; M.edit = null; }
}
async function moveStep(dir){
  const {pid, stepId} = M.edit; const p = proj(pid); if(!p) return;
  const i = p.steps.findIndex(s => s.id === stepId), j = i + dir;
  if(i < 0 || j < 0 || j >= p.steps.length) return;
  const steps = p.steps.map(s => ({...s})); [steps[i], steps[j]] = [steps[j], steps[i]];
  if(await persist({...p, steps}, '已调整顺序')) { $('editModal').hidden = true; M.edit = null; }
}
async function deleteStep(){
  const {pid, stepId} = M.edit; const p = proj(pid); if(!p) return;
  if(!M.edit.delArmed){ M.edit.delArmed = true; $('editDelete').textContent = '再点一次确认删除'; return; }
  if(await persist({...p, steps: p.steps.filter(s => s.id !== stepId)}, '已删除这一步（已拿的分不会扣）')){ $('editModal').hidden = true; M.edit = null; }
}

/* ---------- 列表与编辑面板 ---------- */
const confirmDelProj = makeConfirmDelete(() => renderSheet());
const confirmSwap = makeConfirmDelete(() => renderSheet());
function renderSheet(){
  if(!M.sheetOpen) return;
  const body = $('sheetBody');
  if(!M.projects.length){ body.innerHTML = '<p style="color:var(--ink-soft)">还没有项目。点 ＋ 新建一个。</p>'; return; }
  body.innerHTML = M.projects.map(p => {
    const g = progressOf(p), stages = stagesOf(p.steps);
    const steps = stages.map(st => `<div class="stage-line">${esc(st.name)}${st.done ? ' ✓' : ''}</div>` + st.idx.map(i => {
      const s = p.steps[i];
      return `<div class="step${s.doneAt ? ' done' : ''}" style="--c:${esc(p.color)}"><button class="ck" data-act="toggle" data-pid="${p.id}" data-sid="${s.id}" aria-label="${s.doneAt ? '标记为未完成' : '标记为完成'}">${s.doneAt ? '✓' : ''}</button><div class="tx" data-act="open" data-pid="${p.id}" data-idx="${i}">${i + 1}. ${esc(s.title)}</div><button class="ed" data-act="editstep" data-pid="${p.id}" data-sid="${s.id}" aria-label="编辑这一步">✎</button></div>`;
    }).join('')).join('');
    const colors = PROJECT_COLORS.map(c => `<button style="--c:${c}" data-act="color" data-pid="${p.id}" data-color="${c}" aria-pressed="${p.color === c}" aria-label="颜色 ${c}"></button>`).join('');
    const rename = M.renaming === p.id ? `<input class="rename" id="renameInput" value="${esc(p.title)}" maxlength="40" data-pid="${p.id}">` : '';
    return `<section class="proj" style="--c:${esc(p.color)}">
      <div class="proj-head"><span class="dot"></span><span class="name">${esc(p.icon)} ${esc(p.title)}</span><span class="cnt">${g.done}/${g.total}</span></div>
      <div class="proj-tools">
        <button data-act="select" data-pid="${p.id}">在地图上看</button>
        <button data-act="rename" data-pid="${p.id}">重命名</button>
        <button data-act="park" data-pid="${p.id}">${p.parked ? '恢复' : '停放'}</button>
        <button data-act="swap" data-pid="${p.id}">${M.swapFor === p.id ? '取消换步骤' : '换成模板步骤'}</button>
        <button class="danger" data-act="delproj" data-pid="${p.id}">${confirmDelProj.isPending(p.id) ? '再点一次确认删除' : '删除项目'}</button>
      </div>
      ${rename}
      ${M.swapFor === p.id ? `<div class="swap-box"><p>选一个模板，整个项目的步骤会换成它的（名字、颜色、位置不变；已点亮的城里，标题相同的会保留，其他重置。已拿的分不会扣）：</p>${TEMPLATES.filter(t => t.id !== 'blank').map(t => `<button class="btn-ghost solid" data-act="swaptpl" data-pid="${p.id}" data-tpl="${t.id}">${confirmSwap.isPending(p.id + ':' + t.id) ? '再点一次确认：' : ''}${esc(t.icon)} ${esc(t.name)}（${t.steps.length} 步）</button>`).join('')}</div>` : ''}
      <div class="colors">${colors}</div>
      ${steps}
      <button class="btn-ghost add-step" data-act="addstep" data-pid="${p.id}">＋ 在路的尽头添加一步</button>
    </section>`;
  }).join('');
  const ri = $('renameInput');
  if(ri){ ri.focus(); ri.select(); ri.addEventListener('keydown', e => { if(e.key === 'Enter') ri.blur(); }); ri.addEventListener('blur', () => finishRename(ri)); }
}
async function finishRename(ri){
  const p = proj(ri.dataset.pid); M.renaming = null;
  const t = ri.value.trim();
  if(p && t && t !== p.title) await persist({...p, title: t}, '已重命名'); else renderSheet();
}
function openSheet(){ M.sheetOpen = true; $('sheet').hidden = false; renderSheet(); }
function closeSheet(){ M.sheetOpen = false; $('sheet').hidden = true; }

/* ---------- 新建项目 ---------- */
function openNew(){
  $('tplList').innerHTML = TEMPLATES.map(t => `<button class="tpl" data-tpl="${t.id}"><b>${t.icon} ${esc(t.name)}</b><span>${esc(t.intro)}（${t.steps.length} 步）</span></button>`).join('');
  $('newTitle').value = ''; $('newErr').textContent = ''; $('newModal').hidden = false;
}
async function createProject(tid){
  const slot = freeSlot(M.projects);
  const p = newProject({id: newProjectId(), title: $('newTitle').value.trim(), templateId: tid, slot, now: Date.now()});
  try{ await saveProject(M.cols, p); }catch(e){ console.error(e); $('newErr').textContent = '保存失败，请再试一次'; return; }
  M.projects.push(p); M.selectedId = p.id; store.set('map.sel', p.id);
  $('newModal').hidden = true;
  if(M.scene) { M.scene.setProjects(M.projects, M.selectedId); M.scene.select(p.id); }
  renderAll();
  showToast(activeCount(M.projects) > MAX_ACTIVE_PROJECTS ? `同时进行的项目已经 ${activeCount(M.projects)} 个了：每个都会走得更慢，可以把暂时不做的「停放」` : '新项目建好了，路在首都外面');
}

/* ---------- 选择 / 视角 / 摇杆 ---------- */
function selectProject(id){
  M.selectedId = id; store.set('map.sel', id);
  if(M.scene) M.scene.select(id);
  renderAll();
}
function goNext(){
  const p = selected(); if(!p) return;
  const g = progressOf(p); if(g.nextIndex < 0) return;
  if(M.scene) M.scene.driveTo(p.id, g.nextIndex); else openCard(p.id, g.nextIndex);
}
function setupJoystick(){
  const joy = $('joy'), knob = $('joyKnob'); joy.hidden = false;
  let id = null; const R = 48;
  const set = (cx, cy, e) => {
    const r = joy.getBoundingClientRect(); let dx = e.clientX - (r.left + r.width / 2), dy = e.clientY - (r.top + r.height / 2);
    const d = Math.hypot(dx, dy); if(d > R){ dx = dx / d * R; dy = dy / d * R; }
    knob.style.transform = `translate(${dx}px,${dy}px)`;
    const nx = dx / R, ny = -dy / R, dz = 0.14;
    M.scene.setDrive(Math.abs(nx) < dz ? 0 : nx, Math.abs(ny) < dz ? 0 : ny);
  };
  joy.addEventListener('pointerdown', e => { id = e.pointerId; joy.setPointerCapture(id); set(0, 0, e); });
  joy.addEventListener('pointermove', e => { if(e.pointerId === id) set(0, 0, e); });
  const up = e => { if(e.pointerId !== id) return; id = null; knob.style.transform = ''; M.scene.setDrive(0, 0); };
  joy.addEventListener('pointerup', up); joy.addEventListener('pointercancel', up);
}

/* ---------- 3D 场景（失败就退回列表） ---------- */
async function initScene(){
  try{
    const mod = await import('./scene.js');
    if(!mod.webglSupported()) throw new Error('这个设备不支持 WebGL');
    M.scene = mod.createScene($('stage'), {
      onArrive(pid, idx){
        const p = proj(pid); if(!p || M.card || !p.steps[idx]) return;
        if(!p.steps[idx].doneAt) openCard(pid, idx, {arrived: true});
      },
      onCityClick(pid, idx){ if(pid !== M.selectedId) selectProject(pid); openCard(pid, idx); },
    });
    M.scene.setProjects(M.projects, M.selectedId);
    setupJoystick();
    renderNext();
  }catch(e){
    console.error('3D 场景加载失败', e);
    M.noScene = true;
    $('viewBtn').hidden = true; $('hint').hidden = true;
    $('fallback').hidden = false;
    $('fallback').innerHTML = `<p>3D 地图在这个设备或网络下没能加载（${esc(e.message || e)}），先用列表模式：点开每一步看说明，做完就打勾。</p>`;
    openSheet(); renderNext();
  }
}

function renderAll(){ renderChips(); renderNext(); renderSheet(); }

async function start(){
  try{ M.projects = await loadProjects(M.cols); }
  catch(e){ console.error(e); showToast('读取项目失败，请刷新重试'); M.projects = []; }
  const saved = store.get('map.sel');
  M.selectedId = (proj(saved) || M.projects.find(p => !p.parked) || M.projects[0] || {}).id || null;
  renderAll();
  await initScene();
  if(!M.projects.length) openNew();
}

/* ---------- 事件 ---------- */
$('chips').addEventListener('click', e => { const b = e.target.closest('.chip'); if(b) selectProject(b.dataset.id); });
$('newBtn').addEventListener('click', openNew);
$('newCancel').addEventListener('click', () => { $('newModal').hidden = true; });
$('tplList').addEventListener('click', e => { const b = e.target.closest('.tpl'); if(b) createProject(b.dataset.tpl); });
$('listBtn').addEventListener('click', () => (M.sheetOpen ? closeSheet() : openSheet()));
$('sheetClose').addEventListener('click', closeSheet);
$('viewBtn').addEventListener('click', () => {
  if(!M.scene) return;
  const god = M.scene.view !== 'god'; M.scene.setView(god ? 'god' : 'follow');
  $('viewBtn').setAttribute('aria-pressed', String(god)); $('viewBtn').textContent = god ? '🚗' : '🌍';
});
$('nextCard').addEventListener('click', e => {
  const a = e.target.closest('[data-act]'); if(!a) return; const p = selected(); if(!p) return;
  const act = a.dataset.act, g = progressOf(p);
  if(act === 'go') goNext();
  else if(act === 'detail' && g.nextIndex >= 0) openCard(p.id, g.nextIndex);
  else if(act === 'sheet') openSheet();
  else if(act === 'god'){ if(M.scene) $('viewBtn').click(); }
  else if(act === 'unpark') persist({...p, parked: false}, '已恢复');
  else if(act === 'addstep') openEdit(p.id, null);
});
$('cityCard').addEventListener('click', e => {
  const a = e.target.closest('[data-act]'); if(!a || !M.card) return;
  const {pid, idx} = M.card, p = proj(pid); if(!p) return; const s = p.steps[idx];
  if(a.dataset.act === 'complete') complete(pid, s.id, true);
  else if(a.dataset.act === 'uncomplete') complete(pid, s.id, false);
  else if(a.dataset.act === 'drive'){ closeCard(); if(M.scene) M.scene.driveTo(pid, idx); }
  else if(a.dataset.act === 'edit'){ closeCard(); openEdit(pid, s.id); }
  else if(a.dataset.act === 'close') closeCard();
});
closeOnBackdrop('cityModal', closeCard);
$('editCancel').addEventListener('click', () => { $('editModal').hidden = true; M.edit = null; });
$('editSave').addEventListener('click', saveEdit);
$('editUp').addEventListener('click', () => moveStep(-1));
$('editDown').addEventListener('click', () => moveStep(1));
$('editDelete').addEventListener('click', deleteStep);
closeOnBackdrop('editModal', () => { $('editModal').hidden = true; M.edit = null; });
closeOnBackdrop('newModal', () => { $('newModal').hidden = true; });
$('closeCelebrate').addEventListener('click', closeCelebrate);
closeOnBackdrop('celebrateModal', closeCelebrate);
document.addEventListener('keydown', e => { if(e.key === 'Escape'){ if(!$('cityModal').hidden) closeCard(); else if(!$('editModal').hidden) $('editModal').hidden = true; else if(!$('newModal').hidden) $('newModal').hidden = true; else if(M.sheetOpen) closeSheet(); } });
$('sheetBody').addEventListener('click', async e => {
  const a = e.target.closest('[data-act]'); if(!a) return;
  const p = proj(a.dataset.pid), act = a.dataset.act;
  if(act === 'toggle'){ const s = p && p.steps.find(x => x.id === a.dataset.sid); if(s) complete(p.id, s.id, !s.doneAt); }
  else if(act === 'open'){ if(p) openCard(p.id, +a.dataset.idx); }
  else if(act === 'editstep'){ if(p) openEdit(p.id, a.dataset.sid); }
  else if(act === 'addstep'){ if(p) openEdit(p.id, null); }
  else if(act === 'select'){ if(p){ selectProject(p.id); if(M.scene) closeSheet(); } }
  else if(act === 'rename'){ if(p){ M.renaming = p.id; renderSheet(); } }
  else if(act === 'park'){ if(p) await persist({...p, parked: !p.parked}, p.parked ? '已恢复' : '已停放：不占同时进行的名额'); }
  else if(act === 'swap'){ if(p){ M.swapFor = M.swapFor === p.id ? null : p.id; renderSheet(); } }
  else if(act === 'swaptpl'){
    if(p && confirmSwap.click(p.id + ':' + a.dataset.tpl)){
      const t = TEMPLATES.find(x => x.id === a.dataset.tpl); if(!t) return;
      const keep = new Map(p.steps.filter(x => x.doneAt).map(x => [x.title, x.doneAt])), tag = Date.now().toString(36);
      const steps = t.steps.map((x, i) => ({id: 'u' + tag + '-' + (i + 1), title: x.title, detail: x.detail, refs: x.refs, stage: x.stage, doneAt: keep.get(x.title) || null}));
      M.swapFor = null;
      await persist({...p, templateId: t.id, icon: t.icon, steps}, '步骤已换成「' + t.name + '」');
    }
  }
  else if(act === 'color'){ if(p && p.color !== a.dataset.color) await persist({...p, color: a.dataset.color}); }
  else if(act === 'delproj'){
    if(p && confirmDelProj.click(p.id)){
      try{ await deleteProject(M.cols, p.id); M.projects = M.projects.filter(x => x.id !== p.id); if(M.selectedId === p.id) M.selectedId = (M.projects[0] || {}).id || null; if(M.scene){ M.scene.setProjects(M.projects, M.selectedId); M.scene.select(M.selectedId); } renderAll(); showToast('项目已删除（已拿的分不会扣）'); }
      catch(err){ console.error(err); showToast('删除失败，请再试一次'); }
    }
  }
});

$('signInBtn').addEventListener('click', async () => {
  $('gateNote').textContent = '';
  try{ await signInWithGoogle(); }catch(e){ $('gateNote').textContent = '登录没成功：' + (e.message || e); }
});

auth.onAuthStateChanged(user => {
  if(user){
    Object.assign(M, {uid: user.uid, cols: userCols(user.uid), projects: [], selectedId: null});
    $('gate').hidden = true; $('mapRoot').hidden = false;
    ensureDailyLoginBonus(M.cols.log, n => showToast(`每日上线 +${n} 分`));
    start();
  } else {
    if(M.scene){ M.scene.dispose(); M.scene = null; }
    Object.assign(M, {uid: null, cols: null, projects: [], selectedId: null});
    resetDailyBonus();
    $('gate').hidden = false; $('mapRoot').hidden = true;
  }
});
