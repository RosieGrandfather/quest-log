import { S } from './state.js';
import { escapeHTML } from '../core/html.js';
import { iconForReward } from '../core/icons.js';
import { localISO } from '../core/dates.js';
import { TIER_META, TIER_ICON_COLORS } from '../core/constants.js';
import { showToast, openCelebrate, closeOnBackdrop, makeConfirmDelete } from '../ui/common.js';
import { render } from './render.js';

/* 「奖励商店」Tab：三档奖励卡片，兑换 / 编辑 / 删除 */
let editingRewardId = null;
let redeemTarget = null;
const rewardDelete = makeConfirmDelete(()=> render());

export function renderRewards(balance){
  const wrap = document.getElementById('rewardsWrap');
  if(!S.rewards.length){
    wrap.innerHTML = '<div class="entry-empty">还没有奖励，点下面添加第一个吧</div>';
    return;
  }
  const groups = {small:[], medium:[], big:[]};
  // 旧版「添加自定义奖励」有 bug，会存成空档位；这种奖励先放进小奖励里显示出来，编辑一下就能改对
  S.rewards.forEach(r=>{ (groups[r.tier] || groups.small).push(r); });
  wrap.innerHTML = Object.keys(TIER_META).map(tier=>{
    const items = groups[tier];
    if(!items.length) return '';
    const meta = TIER_META[tier];
    return `<div class="tier-block">
      <div class="tier-title"><span class="tier-dot ${meta.cls}"></span>${meta.title}</div>
      <div class="reward-grid">${items.map(r=>rewardCardHTML(r, balance, meta.cls)).join('')}</div>
    </div>`;
  }).join('');
  wrap.querySelectorAll('[data-redeem]').forEach(btn=>{
    btn.addEventListener('click', ()=> onRedeemClick(btn.getAttribute('data-redeem')));
  });
  wrap.querySelectorAll('[data-del]').forEach(btn=>{
    btn.addEventListener('click', ()=> onDeleteClick(btn.getAttribute('data-del')));
  });
  wrap.querySelectorAll('[data-edit]').forEach(btn=>{
    btn.addEventListener('click', ()=> onEditClick(btn.getAttribute('data-edit')));
  });
}

function rewardCardHTML(r, balance, tierCls){
  const pct = Math.min(100, Math.round(balance/r.cost*100));
  const afford = balance >= r.cost;
  const delConfirming = rewardDelete.isPending(r.id);
  const btnLabel = afford ? '兑换' : `还差 ${r.cost-balance} 分`;
  const iconColors = TIER_ICON_COLORS[tierCls] || TIER_ICON_COLORS.small;
  return `<div class="reward-card">
    <div class="reward-top">
      <div class="reward-icon-badge" style="background:${iconColors[0]};color:${iconColors[1]}">${iconForReward(r)}</div>
      <div class="reward-name-wrap">
        <div class="reward-name">${escapeHTML(r.name)}</div>
      </div>
      <div class="reward-cost mono">${r.cost} 分</div>
    </div>
    <div class="reward-bar"><div class="reward-bar-fill ${tierCls}" style="width:${pct}%"></div></div>
    <div class="reward-actions">
      <div class="reward-hint">${afford ? '已经攒够啦 🎉' : pct+'% 已攒够'}</div>
      <div class="reward-btn-row">
        <button class="btn-edit" data-edit="${r.id}">编辑</button>
        <button class="btn-del ${delConfirming?'confirming':''}" data-del="${r.id}">${delConfirming?'确认删除？':'删除'}</button>
        <button class="btn-redeem" data-redeem="${r.id}" ${afford?'':'disabled'}>${btnLabel}</button>
      </div>
    </div>
  </div>`;
}

function onRedeemClick(id){
  const reward = S.rewards.find(r=>r.id===id);
  if(!reward) return;
  redeemTarget = reward;
  document.getElementById('redeemConfirmText').textContent =
    `确定要兑换「${reward.name}」吗？将扣除 ${reward.cost} 积分。`;
  document.getElementById('redeemConfirmError').hidden = true;
  document.getElementById('redeemConfirmModal').hidden = false;
}
function closeRedeemConfirm(){
  document.getElementById('redeemConfirmModal').hidden = true;
  redeemTarget = null;
}
async function confirmRedeem(){
  if(!redeemTarget) return;
  const reward = redeemTarget;
  const errEl = document.getElementById('redeemConfirmError');
  const btn = document.getElementById('confirmRedeemBtn');
  btn.disabled = true;
  try{
    await S.cols.log.add({kind:'spend', category:'reward', label:reward.name, amount:reward.cost, dateISO:localISO(new Date()), ts:Date.now()});
    closeRedeemConfirm();
    openCelebrate(`「${escapeHTML(reward.name)}」奖励已兑换 🎉<br>已扣除 <span class="mono">${reward.cost}</span> 积分。<br>奖励商店欢迎下次光临！`);
  }catch(e){
    errEl.textContent = '兑换失败：' + (e && e.message ? e.message : '请重试');
    errEl.hidden = false;
  }finally{
    btn.disabled = false;
  }
}

function onEditClick(id){
  const reward = S.rewards.find(r=>r.id===id);
  if(reward) openRewardModal(reward);
}
function onDeleteClick(id){
  if(rewardDelete.click(id)){
    S.cols.rewards.doc(id).delete().catch(()=>{ showToast('删除失败，请重试'); });
  }
}

function openRewardModal(reward){
  editingRewardId = reward ? reward.id : null;
  document.getElementById('rewardModalTitle').textContent = reward ? '编辑奖励' : '添加自定义奖励';
  document.getElementById('submitReward').textContent = reward ? '保存修改' : '添加';
  document.getElementById('rewardName').value = reward ? reward.name : '';
  document.getElementById('rewardTier').value = reward && TIER_META[reward.tier] ? reward.tier : 'small';
  document.getElementById('rewardCost').value = reward ? reward.cost : '';
  document.getElementById('rewardFormError').hidden = true;
  document.getElementById('rewardModal').hidden = false;
}
function closeRewardModal(){ document.getElementById('rewardModal').hidden = true; editingRewardId = null; }

function submitReward(){
  const errEl = document.getElementById('rewardFormError');
  const name = document.getElementById('rewardName').value.trim();
  const tier = document.getElementById('rewardTier').value;
  const rawCost = document.getElementById('rewardCost').value;
  const cost = Number(rawCost);
  if(!name){ errEl.textContent='请填写奖励名称'; errEl.hidden=false; return; }
  if(rawCost===''||isNaN(cost)||cost<0){ errEl.textContent='请填写一个不小于 0 的积分数'; errEl.hidden=false; return; }
  const btn = document.getElementById('submitReward');
  btn.disabled = true;
  const payload = {name, tier, cost};
  const wasEditing = !!editingRewardId;
  const op = wasEditing
    ? S.cols.rewards.doc(editingRewardId).update(payload)
    : S.cols.rewards.add({...payload, active:true, ts:Date.now()});
  op.then(()=>{ closeRewardModal(); showToast(wasEditing ? '已保存修改' : '已添加奖励'); })
    .catch((err)=>{ errEl.textContent='保存失败：'+(err&&err.message?err.message:'请重试'); errEl.hidden=false; })
    .finally(()=>{ btn.disabled = false; });
}

export function wireRewards(){
  document.getElementById('openAddReward').addEventListener('click', ()=> openRewardModal());
  document.getElementById('cancelReward').addEventListener('click', closeRewardModal);
  document.getElementById('submitReward').addEventListener('click', submitReward);
  closeOnBackdrop('rewardModal', closeRewardModal);
  document.getElementById('cancelRedeemConfirm').addEventListener('click', closeRedeemConfirm);
  document.getElementById('confirmRedeemBtn').addEventListener('click', confirmRedeem);
  closeOnBackdrop('redeemConfirmModal', closeRedeemConfirm);
}
