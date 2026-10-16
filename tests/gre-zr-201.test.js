import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {gradeItem,summarize} from '../js/core/qgrade.js';
const read=p=>JSON.parse(readFileSync(new URL(p,import.meta.url),'utf8'));
const course=read('../courses/gre-zr-201/course.json');
const parsed=read('../tools/course/grzr201/passages.json');
const review=read('../tools/course/grzr201/answer-review.json');
const units=course.units.map(e=>read('../courses/gre-zr-201/'+e.file));
const items=units.flatMap(u=>u.blocks[0].items);

test('remaining reading course has all 240 passages, 480 reviewed questions, complete text controls and no screenshots',()=>{
  assert.equal(course.units.length,48);
  assert.ok(read('../courses/index.json').courses.some(c=>c.id===course.id));
  assert.deepEqual(units.flatMap(u=>Object.values(u.blocks[0].passages).map(p=>p.number)),Array.from({length:240},(_,i)=>201+i));
  assert.equal(items.length,480);assert.equal(review.items.length,480);
  for(const [li,u]of units.entries()){
    assert.equal(u.minutes,20);assert.equal(Object.keys(u.blocks[0].passages).length,5);
    for(const [i,q]of u.blocks[0].items.entries()){
      assert.equal(q.n,i+1);assert.equal(q.img,undefined);assert.equal(q.imgs,undefined);
      assert.ok(q.txt.stem[0].length>20);
      const p=u.blocks[0].passages[q.passage];assert.ok(p.number>=201+li*5&&p.number<206+li*5);
      for(const h of p.highlights)assert.ok(p.paragraphs.some(t=>t.includes(h)));
      assert.equal(u.blocks[0].items.filter(it=>it.passage===q.passage).length,parsed[p.number-201].items.length);
      if(q.kind==='ss'){
        assert.ok(q.txt.sentences.includes(q.ansText));assert.equal(q.txt.sentences.join(' '),q.txt.pass.join(' '));
        assert.equal(q.txt.sentenceParagraphLengths.reduce((a,b)=>a+b,0),q.txt.sentences.length);
      }else{
        assert.equal(q.txt.opts.length,q.kind==='mcn'?3:5);
        assert.ok(q.txt.opts.every(s=>s.trim()));
        assert.ok(q.ans.every(k=>Number.isInteger(k)&&k>=0&&k<q.nopt));
        if(q.kind==='mc1')assert.equal(q.ans.length,1);
      }
    }
  }
  for(const [i,q]of items.entries()){
    const r=review.items[i];assert.equal(r.passage,Number(q.passage.slice(1)));assert.equal(r.question,q.sourceQuestion);
    assert.ok(r.reason);assert.equal(r.sourceAnswer,q.sourceAnswer);
    assert.deepEqual(r.finalAnswer,q.answerPending?null:q.ans??q.ansText);
    if(q.answerPending){assert.match(q.explanation,/本题答案不确定/);assert.match(q.explanation,/配套答案/);assert.equal(gradeItem(q,q.ans.join(',')),false);}
    else if(q.kind!=='ss')assert.equal(gradeItem(q,q.ans.join(',')),true);
    if(q.explanation)assert.ok(['pending','corrected'].includes(q.answerReview.status));
  }
  const counts={};for(const q of items)counts[q.kind]=(counts[q.kind]||0)+1;
  assert.deepEqual(counts,{mc1:423,mcn:48,ss:9});
  const sum=summarize(items,items.map(q=>q.ans?.join(',')||q.ansText));
  assert.equal(sum.correct,sum.total);assert.equal(sum.total,471-items.filter(q=>q.answerPending).length);
});

test('source layout repairs preserve omitted options, real question boundaries and quoted sentence answers',()=>{
  const get=(p,n)=>items.find(q=>q.passage==='p'+p&&q.sourceQuestion===n);
  assert.equal(get(208,2).nopt,5);assert.match(get(208,2).txt.opts[3],/quality of Dickens/);
  assert.equal(items.filter(q=>q.passage==='p240').length,3);
  assert.match(get(272,1).txt.stem[0],/Leonardo/);assert.equal(get(272,2).nopt,5);
  assert.equal(get(398,1).kind,'mcn');assert.equal(get(398,2).nopt,5);
  assert.ok(get(435,2).ansText.endsWith('catastrophe.”'));assert.ok(!get(435,2).ansText.includes('As an idiom'));
  assert.ok(!get(440,1).txt.opts[4].includes('获取方式'));
  for(const [p,n,source,ans]of [[268,1,'E',[3]],[286,2,'E',[2]],[378,3,'E',[3]]]){
    const q=get(p,n);assert.equal(q.sourceAnswer,source);assert.deepEqual(q.ans,ans);
    assert.equal(gradeItem(q,'4'),false);
  }
  for(const [p,n]of [[240,3],[260,3],[436,2]])assert.equal(get(p,n).answerPending,true);
});
