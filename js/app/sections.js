import { S } from './state.js';
import { FieldValue } from '../firebase.js';
import { showToast, closeOnBackdrop, makeConfirmDelete } from '../ui/common.js';
import { render } from './render.js';

/* 板块：新建 / 改名 / 删除（板块里还有任务时不让删） */
let editingSectionId = null;
export const sectionDelete = makeConfirmDelete(()=> render());

export function openSectionModal(sec){
  editingSectionId = sec ? sec.id : null;
  document.getElementById('sectionModalTitle').textContent = sec ? '板块改名' : '添加自定义板块';
  document.getElementById('submitSection').textContent = sec ? '保存修改' : '添加';
  document.getElementById('sectionName').value = sec ? sec.label : '';
  document.getElementById('sectionFormError').hidden = true;
  document.getElementById('sectionModal').hidden = false;
  document.getElementById('sectionName').focus();
}
function closeSectionModal(){ document.getElementById('sectionModal').hidden = true; editingSectionId = null; }

function submitSection(){
  const errEl = document.getElementById('sectionFormError');
  const label = document.getElementById('sectionName').value.trim();
  if(!label){ errEl.textContent='请填写板块名称'; errEl.hidden=false; return; }
  const dup = S.sections.some(c=> c.label===label && c.id!==editingSectionId);
  if(dup){ errEl.textContent='已经有同名板块了'; errEl.hidden=false; return; }
  const btn = document.getElementById('submitSection');
  btn.disabled = true;
  const wasEditing = !!editingSectionId;
  // 改名后删掉 short（老板块迁移时带的简称），之后历史记录标签显示新名字
  const op = wasEditing
    ? S.cols.sections.doc(editingSectionId).update({label, short:FieldValue.delete()})
    : S.cols.sections.add({label, ts:Date.now()});
  op.then(()=>{ closeSectionModal(); showToast(wasEditing ? '已保存修改' : '已添加板块'); })
    .catch((err)=>{ errEl.textContent='保存失败：'+(err&&err.message?err.message:'请重试'); errEl.hidden=false; })
    .finally(()=>{ btn.disabled = false; });
}

export function onDeleteSectionClick(id){
  const sec = S.sections.find(x=>x.id===id);
  if(!sec) return;
  if(S.tasks.some(t=>t.category===id)){
    showToast('板块里还有任务，先把任务删掉或移到别的板块');
    return;
  }
  if(sectionDelete.click(id)){
    S.cols.sections.doc(sec.id).delete().catch(()=>{ showToast('删除失败，请重试'); });
  }
}

export function wireSections(){
  document.getElementById('openAddSection').addEventListener('click', ()=> openSectionModal());
  document.getElementById('cancelSection').addEventListener('click', closeSectionModal);
  document.getElementById('submitSection').addEventListener('click', submitSection);
  document.getElementById('sectionName').addEventListener('keydown', e=>{ if(e.key==='Enter') submitSection(); });
  closeOnBackdrop('sectionModal', closeSectionModal);
}
