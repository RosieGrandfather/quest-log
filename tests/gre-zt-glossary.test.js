import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {gradeItem} from '../js/core/qgrade.js';
import {restorePractice,snapshotAnswers} from '../js/core/qreview.js';

const read=p=>JSON.parse(readFileSync(new URL(p,import.meta.url),'utf8'));
const course=read('../courses/gre-zt/course.json');
const meanings=read('../tools/course/grzt/option-meanings.json');

test('first 100 Sections have a Chinese meaning for all 4411 choices, including every blank and distractor',()=>{
 let questions=0,choices=0;const seen=new Set();
 for(const entry of course.units){
  const unit=read('../courses/gre-zt/'+entry.file);
  assert.equal(unit.answerFormat,'gre-zt-v1');
  for(const q of unit.blocks[0].items){
   questions++;
   const opts=q.kind==='tc'?q.txt.cols:q.txt.opts;
   const zh=q.kind==='tc'?q.txt.colsZh:q.txt.optsZh;
   assert.ok(Array.isArray(zh));
   assert.equal(zh.length,opts.length);
   const english=q.kind==='tc'?opts.flat():opts,chinese=q.kind==='tc'?zh.flat():zh;
   if(q.kind==='tc')for(const col of zh)assert.equal(col.length,3);
   for(const [i,word] of english.entries()){
    assert.equal(chinese[i],meanings[word]);assert.match(chinese[i],/[\u4e00-\u9fff]/);
    assert.doesNotMatch(chinese[i],/故意没写|烦请|待补|待翻译/);
    choices++;seen.add(word);
   }
   assert.equal(gradeItem(q,q.ans.join(',')),true);
  }
 }
 assert.equal(course.units.length,100);assert.equal(questions,700);
 assert.equal(choices,4411);assert.equal(seen.size,3137);
 assert.deepEqual([...seen].sort(),Object.keys(meanings).sort());
 assert.equal(meanings.insular,'狭隘的；与外界隔绝的');
 assert.equal(meanings['suffer from'],'遭受；患有');
 assert.equal(meanings['a possible'],'可能的');
 assert.equal(meanings.function,'作用；职能；功能');
 assert.equal(meanings.sophist,'诡辩家');
});

test('Chinese meanings do not change saved English choice snapshots or grading, and are scoped to gre-zt',()=>{
 for(const entry of course.units){
  const unit=read('../courses/gre-zt/'+entry.file);
  const old=structuredClone(unit);
  for(const q of old.blocks[0].items){delete q.txt.optsZh;delete q.txt.colsZh;}
  const answers=old.blocks[0].items.map(q=>q.ans.join(','));
  const snapshot=snapshotAnswers(old.blocks[0].items,answers);
  const restored=restorePractice(unit,{answerItems:snapshot,answerFormat:old.answerFormat,answers,correct:7,total:7});
  assert.deepEqual(restored.answers,answers);assert.equal(restored.summary.correct,7);
  assert.ok(restored.issues.every(x=>!x));
 }
 for(const id of ['gre-zt-101','gre-zt-201']){
  for(const e of read('../courses/'+id+'/course.json').units){
   for(const q of read('../courses/'+id+'/'+e.file).blocks[0].items){
    assert.equal(q.txt.optsZh,undefined);assert.equal(q.txt.colsZh,undefined);
   }
  }
 }
});
