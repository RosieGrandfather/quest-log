/* 学习区的各个界面：课程列表 → 章节列表 → 学习页 → 测验 → 回顾。
   路由用 URL 的 #：#/  #/c/课程  #/c/课程/u/章节  …/quiz  …/review */
import { T } from './state.js';
import { loadCourses, loadCourse, loadUnit } from './content.js';
import { unitBodyHTML, mdToHTML, renderMath } from './render-content.js';
import { enhanceCode, resetPySession } from './runner.js';
import { openNotes } from './notes.js';
import { escapeHTML } from '../core/html.js';
import { fmtDateLabel } from '../core/dates.js';
import { unitKey, scoreQuiz, UNIT_POINTS, QUIZ_POINTS, QUIZ_PASS_PCT, DAY_UNITS_TARGET, DAY_UNITS_BONUS } from '../core/study.js';
import { completeUnit, submitQuiz } from '../data/study.js';
import { showToast, openCelebrate } from '../ui/common.js';

const $ = id => document.getElementById(id);
const view = () => $('view');
let route = {name:'home'};
let afterCelebrate = null;          // 关掉庆祝弹窗后要做的事（比如问要不要做测验）
export const takeAfterCelebrate = () => { const f = afterCelebrate; afterCelebrate = null; return f; };

export const go = hash => { location.hash = hash; };
const courseHash = cid => `#/c/${encodeURIComponent(cid)}`;
const unitHash = (cid, uid) => `${courseHash(cid)}/u/${encodeURIComponent(uid)}`;

function parseHash(){
  const p = location.hash.replace(/^#\/?/, '').split('/').map(decodeURIComponent);
  if(p[0]==='c' && p[1]){
    if(p[2]==='u' && p[3]) return {name: p[4]==='quiz' ? 'quiz' : p[4]==='review' ? 'review' : 'unit', cid:p[1], uid:p[3]};
    return {name:'course', cid:p[1]};
  }
  return {name:'home'};
}

export async function renderRoute(){
  route = parseHash();
  window.scrollTo(0, 0);
  view().innerHTML = '<div class="loading">加载中…</div>';
  try{
    if(route.name==='home') await renderHome();
    else if(route.name==='course') await renderCourse(route.cid);
    else if(route.name==='unit') await renderUnit(route.cid, route.uid);
    else if(route.name==='quiz') await renderQuiz(route.cid, route.uid);
    else if(route.name==='review') await renderReview(route.cid, route.uid);
  }catch(e){
    console.error(e);
    view().innerHTML = `<div class="entry-empty">出错了：${escapeHTML(e.message||e)}<br><a href="#/">回到课程列表</a></div>`;
  }
}

/* 进度数据（其他设备上学完 / 交卷）变化时调用：只刷新不影响阅读位置的部分 */
export async function refreshLive(){
  if(route.name==='home') await renderHome();
  else if(route.name==='course') await renderCourse(route.cid);
  else if(route.name==='unit') await renderUnitActions(route.cid, route.uid);
}

/* ---------- 课程列表 ---------- */
function courseProgress(course){
  const total = course.units.length;
  const done = course.units.filter(u=> T.completed[unitKey(course.id, u.id)]).length;
  return {total, done, pct: total ? Math.round(done/total*100) : 0};
}

/* 建议学习顺序：course.json 里的 order / order_note；小时数由各节 minutes 加总 */
const TIER_LABEL = {core:'必修', elective:'选修', track:'方向课'};
const TIER_HEAD = {core:'必修基础：学完它们，就可以开始自己做研究', elective:'选修：按需学（申请 Master 常要的数据结构、读论文要的进阶数学）', track:'方向课：学完必修基础后，选定方向再学'};
function stepLine(c){
  if(!c.order) return '';
  const hours = Math.round(c.units.reduce((s,u)=>s+(u.minutes||0),0)/60);
  const tier = TIER_LABEL[c.tier] ? `<span class="tier tier-${c.tier}">${TIER_LABEL[c.tier]}${c.track ? '：'+escapeHTML(c.track) : ''}</span> ` : '';
  return `<div class="course-step">${tier}<span class="step-no">第 ${c.order} 步</span> ${escapeHTML(c.order_note||'')} <span class="mono">· 约 ${hours} 小时</span></div>`;
}

async function renderHome(){
  const courses = await loadCourses();
  const full = await Promise.all(courses.map(c=> loadCourse(c.id)));
  const card = c=>{
    const p = courseProgress(c);
    return `<a class="course-card" href="${courseHash(c.id)}">
      ${stepLine(c)}
      <div class="course-title">${escapeHTML(c.title)}</div>
      <div class="course-sub">${escapeHTML(c.subtitle||'')}</div>
      <div class="reward-bar"><div class="reward-bar-fill small" style="width:${p.pct}%"></div></div>
      <div class="course-meta mono">已学 ${p.done} / ${p.total} 节</div>
    </a>`;
  };
  let html = `<h2 class="view-title">我的课程</h2><div class="course-sub">按「第 N 步」的顺序学。先学完「必修基础」，就可以开始自己做研究；选修按需；方向课在选定方向后再学</div>`;
  for(const tier of ['core','elective','track']){
    const group = full.filter(c=> (c.tier||'core')===tier);
    if(!group.length) continue;
    const hours = Math.round(group.reduce((s,c)=>s+c.units.reduce((t,u)=>t+(u.minutes||0),0),0)/60);
    html += `<div class="tier-head tier-head-${tier}">${TIER_HEAD[tier]} <span class="mono">· 约 ${hours} 小时</span></div>` + group.map(card).join('');
  }
  view().innerHTML = html;
}

/* ---------- 章节列表 ---------- */
function unitBadges(course, u){
  const key = unitKey(course.id, u.id);
  const done = T.completed[key];
  const pr = T.progress[key] || {};
  const out = [];
  if(!u.file) out.push('<span class="badge soon">即将上线</span>');
  else if(done) out.push(`<span class="badge done">已学 · ${escapeHTML(fmtDateLabel(done))}</span>`);
  if(u.file && u.hasQuiz !== false){
    if(pr.quizPassed) out.push(`<span class="badge quiz-pass">测验 ${pr.quizBest}% ⭐</span>`);
    else if(pr.quizAttempts) out.push(`<span class="badge quiz-try">测验最高 ${pr.quizBest}%</span>`);
    else if(done) out.push('<span class="badge quiz-none">测验未做</span>');
  }
  return out.join('');
}

async function renderCourse(cid){
  const course = await loadCourse(cid);
  const p = courseProgress(course);
  view().innerHTML = `
    <a class="crumb" href="#/">← 所有课程</a>
    <h2 class="view-title">${escapeHTML(course.title)}</h2>
    <div class="course-sub">${escapeHTML(course.subtitle||'')}</div>
    ${stepLine(course)}
    ${course.source ? `<div class="course-source">内容依据：<a href="${escapeHTML(course.source.url)}" target="_blank" rel="noopener">${escapeHTML(course.source.name)}</a>（讲解为自编，未转载原文）</div>` : ''}
    <div class="reward-bar" style="margin-top:12px"><div class="reward-bar-fill small" style="width:${p.pct}%"></div></div>
    <div class="course-meta mono">已学 ${p.done} / ${p.total} 节</div>
    <div class="unit-list">${course.units.map((u, i)=>{
      const done = !!T.completed[unitKey(cid, u.id)];
      const cls = !u.file ? 'soon' : done ? 'done' : 'todo';
      const inner = `<div class="unit-mark">${done ? '✓' : i+1}</div>
        <div class="unit-body">
          <div class="unit-title">${escapeHTML(u.title)}</div>
          <div class="unit-en">${escapeHTML(u.en||'')}${u.minutes?` · 约 ${u.minutes} 分钟`:''}</div>
          ${u.covers ? `<div class="unit-covers">要讲：${escapeHTML(u.covers)}</div>` : ''}
          <div class="unit-badges">${unitBadges(course, u)}</div>
        </div>`;
      return u.file ? `<a class="unit-row ${cls}" href="${unitHash(cid, u.id)}">${inner}</a>` : `<div class="unit-row ${cls}">${inner}</div>`;
    }).join('')}</div>`;
}

/* ---------- 学习页 ---------- */
async function renderUnit(cid, uid){
  const { course, unit, meta } = await loadUnit(cid, uid);
  if(!unit){
    view().innerHTML = `<a class="crumb" href="${courseHash(cid)}">← ${escapeHTML(course.title)}</a><h2 class="view-title">${escapeHTML(meta.title)}</h2><div class="entry-empty">这一节还在准备中</div>`;
    return;
  }
  const idx = course.units.findIndex(u=>u.id===uid);
  const prev = course.units.slice(0, idx).reverse().find(u=>u.file);
  const next = course.units.slice(idx+1).find(u=>u.file);
  view().innerHTML = `
    <a class="crumb" href="${courseHash(cid)}">← ${escapeHTML(course.title)}</a>
    <div class="unit-kicker">第 ${idx+1} 节 · 约 ${unit.minutes||45} 分钟</div>
    <h2 class="view-title">${escapeHTML(unit.title)}</h2>
    <div class="unit-en-big">${escapeHTML(unit.en||'')}</div>
    <article class="lesson">${unitBodyHTML(unit)}</article>
    <div id="unitActions" class="unit-actions"></div>
    <nav class="unit-nav">
      ${prev ? `<a href="${unitHash(cid, prev.id)}">← ${escapeHTML(prev.title)}</a>` : '<span></span>'}
      ${next ? `<a href="${unitHash(cid, next.id)}">${escapeHTML(next.title)} →</a>` : '<span></span>'}
    </nav>
    <button class="notes-fab" id="notesFab">📝 笔记</button>`;
  renderMath(view());
  resetPySession();               // 每进一节，变量清空，像新开一个 notebook
  enhanceCode(view());
  $('notesFab').addEventListener('click', ()=> openNotes(course, unit));
  await renderUnitActions(cid, uid);
}

async function renderUnitActions(cid, uid){
  const box = $('unitActions');
  if(!box) return;
  const { course, unit } = await loadUnit(cid, uid);
  const key = unitKey(cid, uid);
  const done = T.completed[key];
  const pr = T.progress[key] || {};
  const hasQuiz = unit.quiz && unit.quiz.questions && unit.quiz.questions.length;
  let quizPart = '';
  if(hasQuiz){
    const status = pr.quizPassed ? `已达标，最高 ${pr.quizBest} 分 ⭐`
      : pr.quizAttempts ? `最高 ${pr.quizBest} 分，还没到 ${QUIZ_PASS_PCT} 分（达标 +${QUIZ_POINTS}）`
      : `${unit.quiz.questions.length} 道题 · 约 10 分钟 · 达到 ${QUIZ_PASS_PCT} 分 +${QUIZ_POINTS}`;
    quizPart = `<div class="quiz-box">
      <div class="quiz-box-title">小测验</div>
      <div class="quiz-box-status">${status}</div>
      <div class="quiz-box-btns">
        ${pr.lastAttempt ? `<a class="btn-ghost" href="${unitHash(cid, uid)}/review">查看上次答题</a>` : ''}
        <a class="btn-primary" href="${unitHash(cid, uid)}/quiz">${pr.quizAttempts ? '重做测验' : '做测验'}</a>
      </div>
    </div>`;
  }
  box.innerHTML = done
    ? `<div class="done-banner">✅ 已学完这一节 · ${escapeHTML(fmtDateLabel(done))}</div>${quizPart}`
    : `<button class="btn-primary btn-complete" id="completeBtn">学完了 ✓ <span class="mono">+${UNIT_POINTS}</span></button>
       <div class="complete-hint">看完视频和讲解后点这里；只有第一次学完新章节才算今天的有效学习</div>${quizPart}`;
  const btn = $('completeBtn');
  if(btn) btn.addEventListener('click', ()=> onComplete(course, unit, btn));
}

async function onComplete(course, unit, btn){
  btn.disabled = true;
  try{
    const r = await completeUnit(T.cols, course, unit);
    if(!r.created){ showToast('这一节之前已经学完过了'); return; }
    let html = `你太棒了！学完了「${escapeHTML(unit.title)}」🎉<br>已添加 <span class="mono">${UNIT_POINTS}</span> 积分！`;
    html += `<br><span class="celebrate-sub">🔥 已连续学习 <span class="mono">${r.streak}</span> 天</span>`;
    if(r.todayCount < DAY_UNITS_TARGET){
      html += `<br><span class="celebrate-sub">📚 今天已学完 <span class="mono">${r.todayCount}</span> 节，学满 ${DAY_UNITS_TARGET} 节再得 <span class="mono">${DAY_UNITS_BONUS}</span> 分</span>`;
    }
    r.bonuses.forEach(b=>{
      html += `<div class="celebrate-bonus">🏆 恭喜${escapeHTML(b.title)}！<br>奖励额外 <span class="mono">${b.amount}</span> 分</div>`;
    });
    const hasQuiz = unit.quiz && unit.quiz.questions && unit.quiz.questions.length;
    if(hasQuiz) afterCelebrate = ()=> openQuizPrompt(course, unit);
    openCelebrate(html);
  }catch(e){
    console.error(e);
    showToast('记录失败：' + (e.message || '请重试'));
  }finally{
    btn.disabled = false;
  }
}

function openQuizPrompt(course, unit){
  $('quizPromptText').innerHTML = `要不要做个小测验？${unit.quiz.questions.length} 道题，大约 10 分钟。<br>达到 ${QUIZ_PASS_PCT} 分可以再得 <span class="mono">${QUIZ_POINTS}</span> 分。<br><span class="complete-hint">跳过也没关系，之后随时可以回来补做。</span>`;
  $('quizPromptGo').onclick = ()=>{ $('quizPrompt').hidden = true; go(`${unitHash(course.id, unit.id)}/quiz`); };
  $('quizPrompt').hidden = false;
}

/* ---------- 测验 ---------- */
async function renderQuiz(cid, uid){
  const { course, unit } = await loadUnit(cid, uid);
  if(!unit || !unit.quiz) { go(unitHash(cid, uid)); return; }
  const qs = unit.quiz.questions;
  view().innerHTML = `
    <a class="crumb" href="${unitHash(cid, uid)}">← 返回本节</a>
    <h2 class="view-title">小测验</h2>
    <div class="course-sub">${escapeHTML(unit.title)} · ${qs.length} 道单选题 · ${QUIZ_PASS_PCT} 分及格</div>
    <form id="quizForm" class="quiz">${qs.map((q, i)=>`
      <fieldset class="q">
        <legend><span class="q-no">${i+1}</span>${mdToHTML(q.q)}</legend>
        ${q.options.map((o, j)=>`<label class="opt"><input type="radio" name="q${i}" value="${j}"><span>${mdToHTML(o)}</span></label>`).join('')}
      </fieldset>`).join('')}
      <div class="form-error" id="quizError" hidden></div>
      <button class="btn-primary btn-complete" type="submit" id="quizSubmit">交卷</button>
    </form>`;
  renderMath(view());
  $('quizForm').addEventListener('submit', async e=>{
    e.preventDefault();
    const answers = qs.map((_, i)=>{ const c = document.querySelector(`input[name="q${i}"]:checked`); return c ? Number(c.value) : null; });
    const missing = answers.filter(a=>a===null).length;
    if(missing && !$('quizError').dataset.warned){
      $('quizError').textContent = `还有 ${missing} 道题没选，没选的算错。再点一次「交卷」确认提交。`;
      $('quizError').hidden = false;
      $('quizError').dataset.warned = '1';
      return;
    }
    $('quizSubmit').disabled = true;
    try{
      const score = scoreQuiz(qs, answers);
      const r = await submitQuiz(T.cols, course, unit, answers, score);
      T.progress[unitKey(cid, uid)] = r.progress;   // 不等实时同步，回顾页马上能读到这次成绩
      go(`${unitHash(cid, uid)}/review`);
      if(r.awarded){
        openCelebrate(`测验 <span class="mono">${score}</span> 分，达标啦 🎉<br>已添加 <span class="mono">${QUIZ_POINTS}</span> 积分！`);
      } else if(r.passed){
        showToast(`${score} 分！这节的测验奖励之前已经拿过了`);
      } else {
        showToast(`${score} 分，差一点点～看看讲解再试一次`);
      }
    }catch(err){
      console.error(err);
      $('quizError').textContent = '提交失败：' + (err.message || '请重试');
      $('quizError').hidden = false;
      $('quizSubmit').disabled = false;
    }
  });
}

/* ---------- 回顾 ---------- */
async function renderReview(cid, uid){
  const { unit } = await loadUnit(cid, uid);
  const pr = T.progress[unitKey(cid, uid)] || {};
  const last = pr.lastAttempt;
  if(!unit || !unit.quiz || !last){ go(unitHash(cid, uid)); return; }
  const qs = unit.quiz.questions;
  const passed = last.score >= QUIZ_PASS_PCT;
  view().innerHTML = `
    <a class="crumb" href="${unitHash(cid, uid)}">← 返回本节</a>
    <h2 class="view-title">答题回顾</h2>
    <div class="score-card ${passed?'pass':'fail'}">
      <div class="score-num mono">${last.score}</div>
      <div>${passed ? '达标 ✓' : `还差一点，${QUIZ_PASS_PCT} 分及格`} · 共做了 ${pr.quizAttempts||1} 次 · 最高 ${pr.quizBest||last.score} 分</div>
    </div>
    <div class="quiz review">${qs.map((q, i)=>{
      const mine = last.answers[i];
      const right = mine === q.answer;
      return `<div class="q ${right?'right':'wrong'}">
        <div class="q-head"><span class="q-no">${i+1}</span><span class="q-verdict">${right?'✓ 答对':'✗ 答错'}</span></div>
        <div class="q-text">${mdToHTML(q.q)}</div>
        ${q.options.map((o, j)=>{
          const cls = j===q.answer ? 'correct' : j===mine ? 'chosen' : '';
          const tag = j===q.answer ? '<span class="opt-tag">正确答案</span>' : j===mine ? '<span class="opt-tag">你的选择</span>' : '';
          return `<div class="opt ${cls}">${mdToHTML(o)}${tag}</div>`;
        }).join('')}
        ${mine===null ? '<div class="opt chosen"><em>没有作答</em></div>' : ''}
        <div class="explain"><strong>讲解</strong>${mdToHTML(q.explain)}</div>
      </div>`;
    }).join('')}</div>
    <div class="quiz-box-btns" style="margin-top:16px">
      <a class="btn-ghost" href="${unitHash(cid, uid)}">返回本节</a>
      <a class="btn-primary" href="${unitHash(cid, uid)}/quiz">重做测验</a>
    </div>`;
  renderMath(view());
}
