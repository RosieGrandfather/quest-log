/* 所有页面共用的界面小工具。依赖页面里有 #toast、#celebrateModal（含 #confettiWrap、#celebrateText、#closeCelebrate） */

let toastTimer = null;
export function showToast(msg){
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.hidden = false;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(()=>{ t.hidden = true; }, 2600);
}

/* 庆祝弹窗 + 撒花。html 由调用方拼好（记得转义用户输入） */
export function openCelebrate(html){
  document.getElementById('celebrateText').innerHTML = html;
  spawnConfetti();
  document.getElementById('celebrateModal').hidden = false;
}
export function closeCelebrate(){
  document.getElementById('celebrateModal').hidden = true;
  document.getElementById('confettiWrap').innerHTML = '';
}
function spawnConfetti(){
  const wrap = document.getElementById('confettiWrap');
  wrap.innerHTML = '';
  const colors = ['#E3A63D','#1C7A68','#7C2049','#48B69D','#C07F1F'];
  for(let i=0;i<28;i++){
    const el = document.createElement('div');
    el.className = 'confetti-piece';
    el.style.left = Math.random()*100+'%';
    el.style.background = colors[i%colors.length];
    el.style.animationDuration = (1.1+Math.random()*0.9)+'s';
    el.style.animationDelay = (Math.random()*0.25)+'s';
    el.style.transform = `rotate(${Math.random()*360}deg)`;
    wrap.appendChild(el);
  }
}

/* 点弹窗外面的遮罩就关闭 */
export function closeOnBackdrop(modalId, close){
  document.getElementById(modalId).addEventListener('click', e=>{ if(e.target.id===modalId) close(); });
}

/* 「点一下变『确认删除？』，4 秒内再点才真删」的通用状态 */
export function makeConfirmDelete(rerender){
  let pendingId = null, timer = null;
  const clear = ()=>{ pendingId = null; clearTimeout(timer); timer = null; };
  return {
    isPending: id => pendingId === id,
    /* 第二次点返回 true（调用方去真删）；第一次点返回 false */
    click(id){
      if(pendingId === id){ clear(); return true; }
      clear();
      pendingId = id;
      rerender();
      timer = setTimeout(()=>{ clear(); rerender(); }, 4000);
      return false;
    },
  };
}
