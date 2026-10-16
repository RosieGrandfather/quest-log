/* Save once, then complete the lesson. A failed completion can be retried
   without recording the same submitted answers as a second attempt. */
import {submitPractice} from '../data/study.js';
import {unitKey} from '../core/study.js';
import {T} from './state.js';
import {showToast} from '../ui/common.js';

export async function savePracticeSubmission(host, course, unit, answers, sum, onComplete, onSaved){
  let saved = false, busy = false, errorBox;
  async function save(){
    if(busy) return;
    busy = true;
    const redo = host.querySelector('[data-act="redo"]');
    if(redo) redo.disabled = true;
    if(errorBox) errorBox.remove();
    try{
      if(!saved){
        T.progress[unitKey(course.id,unit.id)] = await submitPractice(T.cols,course,unit,answers,sum);
        saved = true;
        onSaved();
      }
      if(onComplete) await onComplete();
      else showToast(`本套 ${sum.correct} / ${sum.total}（${sum.pct}%）已保存`);
    }catch(err){
      console.error(err);
      errorBox = document.createElement('div');
      errorBox.className = 'practice-save-error form-error';
      const message = document.createElement('p');
      message.textContent = saved ? '成绩已保存，完成记录未保存成功。' : '提交未保存成功。';
      const retry = document.createElement('button');
      retry.type = 'button'; retry.className = 'btn-primary'; retry.textContent = '重试保存';
      retry.addEventListener('click',save);
      errorBox.append(message,retry);host.append(errorBox);
    }finally{
      busy = false;
      if(redo) redo.disabled = false;
    }
  }
  await save();
}
