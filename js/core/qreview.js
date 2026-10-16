/* Restore submitted choices independently of the answer key. Never write a
   new attempt merely because a corrected key changes the displayed score. */
import {summarize, sentenceChoices} from './qgrade.js';

const parts = a => String(a ?? '').split(',');
const indices = a => parts(a).every(x=>/^\d+$/.test(x));
const textKey = s => String(s).normalize('NFKC').replace(/[’‘]/g,"'").replace(/\s+/g,' ').trim();
const findChoice = (list, word) => {
  const matches=(list || []).map((s,i)=>textKey(s)===textKey(word)?i:-1).filter(i=>i>=0);
  return matches.length===1 ? matches[0] : -1;
};

export function snapshotAnswers(items, answers){
  return items.map((it,i)=>{
    const raw=String(answers[i] ?? '');
    const choices=it.kind==='tc' && it.txt?.cols ? parts(raw).map((k,j)=>k===''?'':it.txt.cols[j]?.[Number(k)] ?? '')
      : ['mc1','mcn','se'].includes(it.kind) && it.txt?.opts && raw ? parts(raw).map(k=>it.txt.opts[Number(k)] ?? '') : [];
    return {n:it.n, kind:it.kind, raw, choices};
  });
}

export function restorePractice(unit, last){
  const items=unit.blocks.find(b=>b.type==='gre-qset').items;
  const rawAnswers=[], issues=[];
  // text-v2 and its answer-only revision share exactly the same choices.
  const answerOnlyUpdate=unit.answerFormat?.startsWith('gre-vx-text-v2-answers-') && last.answerFormat==='gre-vx-text-v2';
  const sameChoices=last.answerFormat===unit.answerFormat || answerOnlyUpdate;
  const answers=items.map((it,i)=>{
    const saved=last.answerItems?.find(q=>q.n===it.n);
    const raw=String(saved?.raw ?? last.answers?.[i] ?? '');
    rawAnswers[i]=raw;
    if(!raw) return '';
    const unresolved=()=>{issues[i]='旧作答的选项或题型已变，保留原记录供核对，本题暂不参与复核计分';return '';};
    if(it.kind==='ss'){
      const sentences=sentenceChoices(it);
      if(!sentences.length) return raw;
      const k=findChoice(sentences,raw);
      return k>=0 ? sentences[k] : unresolved();
    }
    if(saved){
      if(saved.kind!==it.kind) return unresolved();
      if((it.kind==='tc' || ['mc1','mcn','se'].includes(it.kind)) && saved.choices?.length){
        const mapped=saved.choices.map((s,j)=>!s && parts(raw)[j]==='' ? '' : s ? findChoice(it.kind==='tc'?it.txt?.cols?.[j]:it.txt?.opts,s) : -1);
        if(mapped.some(k=>k!=='' && k<0)) return unresolved();
        return mapped.join(',');
      }
    }
    // Some formerly broken OCR options were repaired during answer review.
    // Restore what the learner actually saw, rather than reusing its old index.
    if(answerOnlyUpdate && it.answerReview?.previousChoices){
      const previous=it.answerReview.previousChoices;
      if(!indices(raw))return unresolved();
      const mapped=parts(raw).map(k=>previous[Number(k)] ? findChoice(it.txt?.opts,previous[Number(k)]) : -1);
      if(mapped.some(k=>k<0))return unresolved();
      return mapped.join(',');
    }
    if(unit.answerFormat && !sameChoices) return unresolved();
    if(it.kind==='tc'){
      if(parts(raw).length!==it.blanks || !indices(raw) || parts(raw).some(k=>Number(k)>2))return unresolved();
    }else if(it.kind!=='ne'){
      if(!indices(raw) || parts(raw).some(k=>Number(k)>=(it.kind==='qc'?4:it.nopt)))return unresolved();
    }
    return raw;
  });
  const gradedItems=items.map((it,i)=>issues[i]?{...it,answerPending:true}:it);
  return {answers,rawAnswers,issues,gradedItems,summary:summarize(gradedItems,answers)};
}
