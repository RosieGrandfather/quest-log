import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync,existsSync}from 'node:fs';
import {gradeItem,summarize}from '../js/core/qgrade.js';
const read=p=>JSON.parse(readFileSync(new URL(p,import.meta.url),'utf8'));
const course=read('../courses/gre-zq170/course.json');
const audit=read('../tools/course/grzq170/audit.json');
const review=read('../tools/course/grzq170/answer-review.json');
const source=read('../tools/course/grzq170/source-answers.json');
const units=course.units.map(e=>read('../courses/gre-zq170/'+e.file));

test('hard quant follows official 12-question/21-minute and 15-question/26-minute sections without padding the tail',()=>{
 assert.equal(units.length,13);let total=0;
 assert.ok(read('../courses/index.json').courses.some(c=>c.id===course.id));
 for(const[i,u]of units.entries()){
  const b=u.blocks[0],n=i===12?7:i%2?15:12,m=i===12?13:i%2?26:21;
  assert.equal(b.items.length,n);assert.equal(u.minutes,m);assert.equal(course.units[i].minutes,m);
  assert.equal(u.answerFormat,'gre-zq170-v1');
  const answers=[];
  for(const[j,q]of b.items.entries()){
   assert.equal(q.n,j+1);assert.equal(q.sourceQuestion,++total);
   assert.equal(q.sourceAnswer,source[total-1].answer);
   assert.equal(audit.items[total-1].question,total);assert.deepEqual(audit.items[total-1].answer,q.ans);
   assert.ok(q.imgs.length>0);
   for(const image of q.imgs)assert.ok(existsSync(new URL('../courses/gre-zq170/img/'+image,import.meta.url)),image);
   const a=q.kind==='ne'?q.ans:q.ans.join(',');assert.equal(gradeItem(q,a),true);answers.push(a);
   assert.equal(gradeItem(q,''),false);
   if(q.kind==='ne')assert.match(q.ans,/^-?\d+(?:\.\d+)?(?:\/\d+)?$/);
   else assert.deepEqual(q.ans,[...q.sourceAnswer.replaceAll(' ','')].map(c=>c.charCodeAt(0)-65));
  }
  const result=summarize(b.items,answers);assert.equal(result.correct,n);assert.equal(result.total,n);
 }
 assert.equal(total,169);assert.equal(audit.questions,169);
 assert.equal(course.units.reduce((s,u)=>s+u.minutes,0),295);
 assert.match(units.at(-1).objectives.join(' '),/第170项.*不计作数学题/);
});

test('hard quant preserves unusual multi-select controls, cross-page formulas and shared charts across section boundaries',()=>{
 const items=units.flatMap(u=>u.blocks[0].items),get=n=>items[n-1];
 for(const[n,opts]of [[1,3],[2,4],[10,5],[25,5],[53,8],[60,3],[68,3],[80,6],[81,4],[89,8],[90,7],[139,4],[146,4]]){
  assert.equal(get(n).kind,'mcn');assert.equal(get(n).nopt,opts);
 }
 assert.equal(get(121).nopt,7);
 assert.equal(gradeItem(get(121),'2,4'),true);
 assert.equal(gradeItem(get(121),'2,4,5'),false);
 for(const n of [4,5,28,30]){assert.equal(get(n).frac,true);assert.equal(gradeItem(get(n),'2/4'),false);}
 assert.equal(gradeItem(get(5),'8/29'),true);
 assert.equal(get(120).kind,'qc');assert.equal(get(140).nopt,5);
 for(const n of [22,27,33,35,39,43,57,64,94,116,126,131,135,140,154,164])assert.ok(get(n).imgs.length>1,'cross-page '+n);
 for(const n of [53,54,55,56])assert.ok(get(n).imgs.includes('greeting-cards.webp'));
 assert.ok(get(93).imgs.includes('q093-graph.webp'));assert.ok(get(94).imgs.includes('q094-diagram.webp'));
});

test('all hard quant answers have an independent review, with computational evidence and original provenance',()=>{
 assert.equal(review.reviewed,169);assert.equal(review.retained,169);
 assert.equal(review.corrected,0);assert.equal(review.pending,0);
 assert.equal(review.computerCheckedQuestions.length,57);
 assert.deepEqual(review.items.map(r=>r.question),Array.from({length:169},(_,i)=>i+1));
 for(const r of review.items){
  assert.equal(r.sourceAnswer,source[r.question-1].answer);
  assert.equal(r.status,'retained');assert.ok(r.reason.length>=10);
  assert.equal(audit.items[r.question-1].independentAnswer,r.independentAnswer);
 }
 assert.equal(review.computedResults['81'],'(5.5, 5.5, 4.25)');
 assert.equal(review.items[162].independentAnswer,'A');
 assert.match(review.items[162].reason,/-2/);
});
