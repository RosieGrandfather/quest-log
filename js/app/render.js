import { S } from './state.js';
import { computeStats } from '../core/stats.js';
import { levelInfo } from '../core/levels.js';
import { fmtDateLabel } from '../core/dates.js';
import { escapeHTML } from '../core/html.js';
import { CAT_SHORT } from '../core/constants.js';
import { renderTasks } from './tasks.js';
import { renderRewards } from './rewards.js';

/* 任何数据变化后整页重画一遍（数据量很小，不需要局部更新） */
export function render(){
  const s = computeStats(S.logEntries);
  document.getElementById('balanceNum').textContent = s.balance;
  document.getElementById('totalNum').textContent = s.totalEarned;
  document.getElementById('entriesNum').textContent = s.entriesCount;
  document.getElementById('streakNum').textContent = s.streak;
  const lvl = levelInfo(s.totalEarned);
  document.getElementById('levelName').textContent = lvl.name;
  document.getElementById('levelSub').textContent = lvl.sub;
  const span = lvl.nextMin - lvl.curMin;
  const pct = span>0 ? Math.min(100, Math.max(0, (s.totalEarned-lvl.curMin)/span*100)) : 100;
  document.getElementById('xpFill').style.width = pct+'%';
  document.getElementById('xpNowLabel').textContent = s.totalEarned+' XP';
  document.getElementById('xpNextLabel').textContent = `/ ${lvl.nextMin} 到下一级`;
  renderRecent();
  renderHistory();
  renderRewards(s.balance);
  renderTasks();
}

/* 板块全部来自数据库的 sections 集合（按 ts 排序），任务的 category = 板块文档 ID */
function categoryShort(id){
  if(CAT_SHORT[id]) return CAT_SHORT[id];
  const sec = S.sections.find(x=>x.id===id);
  return sec ? (sec.short || sec.label) : '其他';
}

function entryCardHTML(e){
  const chipCls = e.kind==='spend' ? 'entry-chip spend' : 'entry-chip';
  const chipText = e.kind==='spend' ? '兑换' : categoryShort(e.category);
  const sign = e.kind==='spend' ? '-' : '+';
  const amtCls = e.kind==='spend' ? 'spend' : 'earn';
  const meta = [fmtDateLabel(e.dateISO)];
  if(e.note) meta.push(e.note);
  return `<div class="entry-card">
    <span class="${chipCls}">${chipText}</span>
    <div class="entry-body">
      <div class="entry-label">${escapeHTML(e.label||'')}</div>
      <div class="entry-meta">${escapeHTML(meta.join(' · '))}</div>
    </div>
    <div class="entry-amount ${amtCls} mono">${sign}${e.amount}</div>
  </div>`;
}

function renderRecent(){
  const el = document.getElementById('recentList');
  const items = S.logEntries.slice(0,6);
  el.innerHTML = items.length ? items.map(entryCardHTML).join('') : '<div class="entry-empty">还没有记录，点上面的按钮记下第一笔吧</div>';
}

function renderHistory(){
  const el = document.getElementById('historyList');
  if(!S.logEntries.length){ el.innerHTML = '<div class="entry-empty">还没有历史记录</div>'; return; }
  const byDate = {};
  S.logEntries.forEach(e=>{
    const key = e.dateISO || '未知日期';
    (byDate[key] = byDate[key]||[]).push(e);
  });
  const dates = Object.keys(byDate).sort((a,b)=> a<b?1:-1);
  el.innerHTML = dates.map(d=>`
    <div class="history-day">
      <div class="history-day-label">${fmtDateLabel(d)}</div>
      ${byDate[d].map(entryCardHTML).join('')}
    </div>`).join('');
}
