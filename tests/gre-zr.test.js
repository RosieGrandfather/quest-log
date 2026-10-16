import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {summarize, gradeItem, isGraded} from '../js/core/qgrade.js';

const read = name => JSON.parse(readFileSync(new URL(name,import.meta.url),'utf8'));
const course=read('../courses/gre-zr/course.json');
const audit=read('../tools/course/grzr/audit.json');
const parsed=read('../tools/course/grzr/passages.json');

test('40 reading lessons cover exactly Passages 1–200 with source keys, complete options and selectable sentences',()=>{
  assert.equal(course.units.length,40);
  assert.ok(read('../courses/index.json').courses.some(c=>c.id===course.id));
  const passageIds=[],counts={};let n=0,sentenceCount=0;
  for(const [i,entry] of course.units.entries()){
    const u=read('../courses/gre-zr/'+entry.file),b=u.blocks[0];
    assert.equal(u.minutes,20);assert.equal(entry.minutes,20);
    assert.equal(Object.keys(b.passages).length,5);
    for(const [id,p] of Object.entries(b.passages)){
      passageIds.push(p.number);
      assert.equal(p.number,Number(id.slice(1)));
      assert.ok(p.number>=i*5+1 && p.number<=i*5+5);
      assert.ok(p.paragraphs.every(t=>t.length>20));
      for(const h of p.highlights)assert.ok(p.paragraphs.some(t=>t.includes(h)),id);
      const source=parsed[p.number-1];
      assert.equal(b.items.filter(q=>q.passage===id).length,source.items.length);
    }
    const answers=[];
    for(const [j,q] of b.items.entries()){
      n++;counts[q.kind]=(counts[q.kind]||0)+1;
      assert.equal(q.n,j+1);
      assert.ok(b.passages[q.passage]);
      assert.ok(q.txt.stem[0].length>20);
      assert.equal(q.img,undefined);assert.equal(q.imgs,undefined);
      if(q.explanation)assert.ok(['pending','corrected'].includes(q.answerReview?.status));
      assert.ok(!/微信公众号|【|】/.test(JSON.stringify(q.txt)));
      if(/highlight|boldface|underlin/i.test(q.txt.stem[0]))assert.ok(b.passages[q.passage].highlights.length);
      const record=audit.items[n-1];
      assert.equal(record.unit,u.id);assert.equal(record.passage,b.passages[q.passage].number);
      assert.equal(record.question,q.sourceQuestion);assert.equal(record.sourceAnswer,q.sourceAnswer);
      if(q.kind==='ss'){
        sentenceCount++;
        assert.ok(q.txt.sentences.includes(q.ansText));
        assert.equal(q.txt.sentences.join(' '),q.txt.pass.join(' '));
        assert.equal(q.txt.sentenceParagraphLengths.reduce((a,b)=>a+b,0),q.txt.sentences.length);
        assert.ok(!q.txt.sentences.some(s=>s==='Ph.D.'||s==='Dr.'));
        answers.push(q.ansText);
      }else{
        assert.equal(q.nopt,q.kind==='mcn'?3:5);
        assert.equal(q.txt.opts.length,q.nopt);
        assert.ok(q.txt.opts.every(s=>s.trim()));
        if(q.answerReview?.status!=='corrected')assert.deepEqual(q.ans,[...q.sourceAnswer].map(c=>c.charCodeAt(0)-65));
        if(q.kind==='mc1')assert.equal(q.ans.length,1);
        const a=q.ans.join(',');assert.equal(gradeItem(q,a),isGraded(q));answers.push(a);
        assert.equal(gradeItem(q,''),false);
      }
    }
    const sum=summarize(b.items,answers);
    assert.equal(sum.correct,sum.total);assert.equal(sum.blank,0);
    assert.equal(sum.selfCheck.length,b.items.filter(q=>!isGraded(q)).length);
  }
  assert.deepEqual(passageIds,Array.from({length:200},(_,i)=>i+1));
  assert.equal(n,413);assert.equal(sentenceCount,11);
  assert.deepEqual(counts,{mc1:340,ss:11,mcn:62});
});

test('reading review covers all 413 questions and separates correction from unresolved source keys',()=>{
  const review=read('../tools/course/grzr/answer-review.json');
  assert.equal(review.items.length,413);
  assert.deepEqual(review.counts,{agrees:399,pending:9,corrected:1,'retained-after-review':4});
  const items=course.units.flatMap(e=>read('../courses/gre-zr/'+e.file).blocks[0].items);
  const comet=items.find(q=>q.passage==='p38'&&q.sourceQuestion===1);
  assert.equal(comet.sourceAnswer,'AC');assert.deepEqual(comet.ans,[0,1,2]);
  assert.equal(gradeItem(comet,'0,2'),false);assert.equal(gradeItem(comet,'0,1,2'),true);
  const pending=items.filter(q=>q.answerPending);
  assert.equal(pending.length,9);
  for(const q of pending){assert.equal(gradeItem(q,q.ans.join(',')),false);assert.ok(q.explanation);}
  assert.equal(summarize(items,items.map(q=>q.ans?.join(',')||q.ansText)).total,393);
  for(const [i,q] of items.entries()){
    const r=review.items[i];assert.equal(r.passage,Number(q.passage.slice(1)));assert.equal(r.question,q.sourceQuestion);
    assert.ok(r.reason);assert.equal(r.sourceAnswer,q.sourceAnswer);
    assert.deepEqual(r.finalAnswer,q.answerPending?null:q.ans??q.ansText);
  }
});

test('source answer typos and sentence anchors do not shift later reading answers',()=>{
  const get = (p,q) => {
    const entry=course.units[Math.floor((p-1)/5)];
    return read('../courses/gre-zr/'+entry.file).blocks[0].items.find(it=>it.passage==='p'+p&&it.sourceQuestion===q);
  };
  assert.equal(get(92,1).sourceAnswer,'D'); // TXT heading PASSAEG 92
  assert.equal(get(177,1).sourceAnswer,'AB'); // TXT heading PASASGE 177
  assert.equal(get(154,1).sourceAnswer,'A'); // The source explicitly corrects an old C.
  assert.ok(get(2,1).ansText.startsWith('While we cannot know'));
  assert.ok(get(18,2).ansText.startsWith('Often written'));
  assert.ok(get(175,1).ansText.startsWith('Women harvest'));
  assert.ok(get(191,3).ansText.startsWith('I am not advocating'));
});
