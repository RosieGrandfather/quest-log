import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync,existsSync} from 'node:fs';
import {summarize, answerText} from '../js/core/qgrade.js';

const read = relative => JSON.parse(readFileSync(new URL(relative,import.meta.url),'utf8'));
const course=read('../courses/gre-vx/course.json');

test('first section reviewed words and sentences score correctly, and survive regeneration',()=>{
  const unit=read('../courses/gre-vx/u01-2025-01-14-v1.json');
  const items=unit.blocks[0].items;
  // Independent semantic expectations, not a copy of item.ans.
  const words=[['subjective'],['deviates from','caricature'],
    ['suffer reputational losses','tainted','a counterweight to'],
    ['They are not limited to a specific cultural tradition.','They emphasize personal experience over collective history.'],
    null,['disdain for','scorn for'],['insufficient','meager'],['untenable','indefensible'],
    ['demarcation of','lines between'],
    ['considering the work of a particular scholar on a certain subject in contrast to other work on the same subject'],
    ['The circulation of antislavery petitions'],
    ['give an example of evidence used by Jeffrey to support her challenge to the claim that women’s participation in the abolitionist movement became marginalized at the end of the 1830s']];
  const answers=items.map((it,i)=>it.kind==='ss' ? it.txt.sentences[2]
    : words[i].map((word,j)=>(it.kind==='tc'?it.txt.cols[j]:it.txt.opts).indexOf(word)).join(','));
  const score=summarize(items,answers);
  assert.equal(score.correct,11);
  assert.equal(score.total,11);
  assert.deepEqual(score.selfCheck,[4]);
  assert.equal(answerText(items[4]),items[4].txt.sentences[2]);
  assert.notEqual(unit.answerFormat,'gre-vx-text-v2');
  const source=read('../tools/course/grvx/data.json')[0].sections[0];
  assert.equal(source.answerFormat,unit.answerFormat);
  for(const it of items){
    const original=source.items.find(q=>q.n===it.n);
    for(const key of ['ans','ansText','explanation','answerReview','answerPending'])
      assert.deepEqual(it[key],original[key],`question ${it.n}: ${key}`);
    assert.equal(it.answerReview.status,'independently-reviewed');
    assert.ok(it.explanation);
  }
  // The ten previously graded keys all incorrectly rejected the correct answers.
  const previous=items.filter(q=>q.n!==4&&q.n!==5).map(it=>({...it,...it.answerReview.previous}));
  const previousAnswers=answers.filter((a,i)=>i!==3&&i!==4);
  assert.equal(summarize(previous,previousAnswers).correct,0);
});

test('every GRE Verbal 2025 question has text and compatible answer controls',()=>{
  let count=0;
  for(const entry of course.units){
    const unit=read('../courses/gre-vx/'+entry.file);
    assert.equal(unit.id,entry.id);
    assert.ok(unit.answerFormat,'corrected choices must not restore obsolete answer indices');
    for(const item of unit.blocks[0].items){
      count++;
      const at=unit.id+' question '+item.n, tx=item.txt;
      assert.ok(tx?.stem?.length,at+' missing stem');
      assert.ok(tx.stem.every(s=>typeof s==='string'&&s.trim()),at);
      assert.ok(existsSync(new URL('../courses/gre-vx/img/'+item.img,import.meta.url)),at+' image');
      if(item.kind==='tc'){
        assert.equal(tx.cols.length,item.blanks,at+' blank groups');
        assert.equal(tx.stem.join(' ').match(/____/g)?.length,item.blanks,at+' stem blanks');
        assert.ok(tx.cols.every(col=>col.length===3&&col.every(s=>s.trim())),at+' column choices');
      }else if(item.kind==='ss'){
        assert.ok(tx.sentences?.length,at+' missing clickable sentences');
        assert.equal(tx.sentences.join(' '),tx.pass.join(' '),at+' sentence content');
      }else{
        assert.equal(tx.opts.length,item.nopt,at+' choice count');
        assert.ok(tx.opts.every(s=>s.trim()&&!/select (?:one|two|an?)\b.*choice/i.test(s)),at+' instruction in choices');
        if(item.kind==='se')assert.equal(item.nopt,6,at);
      }
      const [date,file]=item.img.split('/');
      const source=read('../tools/course/grvx/ocr/txt-'+date+'.json');
      const original=source[Number(file.split('-')[0])+'-'+item.n];
      const {ok,...sourceText}=original;
      assert.equal(ok,true,at+' generator source');
      assert.deepEqual(sourceText,tx,at+' stale generator text');
    }
  }
  assert.ok(count>0);
});
