/* 练习题每题右上角的「复查」标记：做题中、交卷后都能点；存在 studyProgress.reviewMarks（题号 → true / false），
   课程页的「错题本」导出时，标记过的题即使答对也会一起导出。 */
import { T } from './state.js';
import { unitKey } from '../core/study.js';
import { saveReviewMark } from '../data/study.js';
import { showToast } from '../ui/common.js';

export const flagHTML = n => `<button type="button" class="gq-flag" data-flag="${n}" aria-pressed="false" title="标记这题，导出错题本时一起导出">☆ 复查</button>`;

const paint = (btn, on)=>{
  btn.classList.toggle('on', on);
  btn.setAttribute('aria-pressed', on ? 'true' : 'false');
  btn.textContent = on ? '★ 已标记' : '☆ 复查';
};

export function wireFlags(box, course, unit){
  const key = unitKey(course.id, unit.id);
  const marks = T.progress[key]?.reviewMarks || {};
  box.querySelectorAll('.gq-flag').forEach(btn=> paint(btn, marks[btn.dataset.flag] === true));
  box.addEventListener('click', async e=>{
    const btn = e.target.closest && e.target.closest('.gq-flag');
    if(!btn || !box.contains(btn)) return;
    e.preventDefault();
    const on = !btn.classList.contains('on');
    paint(btn, on);
    try{
      await saveReviewMark(T.cols, course, unit, btn.dataset.flag, on);
      const pr = T.progress[key] || (T.progress[key] = {courseId:course.id, unitId:unit.id});
      pr.reviewMarks = {...(pr.reviewMarks || {}), [btn.dataset.flag]:on};
    }catch(err){
      console.error('review mark failed', err);
      paint(btn, !on);
      showToast('标记没保存成功，请再点一次');
    }
  });
}
