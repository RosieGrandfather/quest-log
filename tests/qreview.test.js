import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {restorePractice,snapshotAnswers} from '../js/core/qreview.js';

const first=JSON.parse(readFileSync(new URL('../courses/gre-vx/u01-2025-01-14-v1.json',import.meta.url),'utf8'));
const items=first.blocks[0].items;
const good=items.map(it=>it.kind==='ss'?it.txt.sentences[2]:it.ans.join(','));

test('restore the prior text version after an answer-only correction without changing saved answers',()=>{
  const last={answerFormat:'gre-vx-text-v2',answers:good.slice(),correct:0,total:10};
  last.answers[0]='0';
  const original=JSON.stringify(last), result=restorePractice(first,last);
  assert.equal(result.summary.correct,10);
  assert.equal(result.summary.total,11);
  assert.deepEqual(result.summary.wrong,[0]);
  assert.equal(result.issues.some(Boolean),false);
  assert.equal(result.answers[4],items[4].txt.sentences[2]);
  assert.equal(JSON.stringify(last),original);
});

test('snapshot selected words remaps a reordered choice by text and question number',()=>{
  const unit={answerFormat:'new',blocks:[{type:'gre-qset',items:[{n:2,kind:'mc1',nopt:2,ans:[1],txt:{opts:['new','old']}}]}]};
  const last={answerFormat:'old',answers:['0'],answerItems:snapshotAnswers([{n:2,kind:'mc1',txt:{opts:['old','new']}}],['0'])};
  const r=restorePractice(unit,last);
  assert.deepEqual(r.answers,['1']);assert.equal(r.summary.correct,1);
});

test('multi-blank snapshots preserve each selected word independently',()=>{
  const old={n:1,kind:'tc',blanks:2,txt:{cols:[['x','y','z'],['a','b','c']]}};
  const unit={answerFormat:'new',blocks:[{type:'gre-qset',items:[{...old,ans:[1,0],txt:{cols:[['y','x','z'],['c','a','b']]}}]}]};
  const r=restorePractice(unit,{answerFormat:'old',answerItems:snapshotAnswers([old],['0,2'])});
  assert.deepEqual(r.answers,['1,0']);assert.equal(r.summary.correct,1);
});

test('uncertain legacy indices remain visible as raw records and are excluded rather than marked wrong',()=>{
  const r=restorePractice(first,{answers:good});
  assert.equal(r.rawAnswers[0],'1');assert.ok(r.issues[0]);
  assert.equal(r.summary.total,0);assert.deepEqual(r.summary.wrong,[]);
  assert.equal(r.answers[4],items[4].txt.sentences[2]);
});

test('invalid legacy sentence indices are preserved without inventing a chosen sentence',()=>{
  const answers=good.slice();answers[4]='2';
  const r=restorePractice(first,{answerFormat:'gre-vx-text-v2',answers});
  assert.equal(r.rawAnswers[4],'2');assert.equal(r.answers[4],'');assert.ok(r.issues[4]);
  assert.equal(r.summary.correct,11);
});

test('unversioned unchanged courses still restore and grade their saved choices',()=>{
  const unit={blocks:[{type:'gre-qset',items:[{n:1,kind:'mc1',nopt:2,ans:[1]}]}]};
  assert.equal(restorePractice(unit,{answers:['1']}).summary.correct,1);
  assert.equal(restorePractice(unit,{answers:['1'],answerItems:snapshotAnswers(unit.blocks[0].items,['1'])}).summary.correct,1);
});

test('snapshot preserves an unanswered blank when other blanks were submitted',()=>{
  const it={n:1,kind:'tc',blanks:2,ans:[0,1],txt:{cols:[['a','b','c'],['d','e','f']]}};
  const unit={answerFormat:'new',blocks:[{type:'gre-qset',items:[it]}]};
  const r=restorePractice(unit,{answerFormat:'old',answerItems:snapshotAnswers([it],['0,'])});
  assert.deepEqual(r.answers,['0,']);assert.equal(r.summary.blank,1);
});

test('changed question kinds and missing selected text do not guess a mapping',()=>{
  const last={answerFormat:'old',answerItems:[{n:1,kind:'mc1',raw:'1',choices:['removed']}]};
  const unit={answerFormat:'new',blocks:[{type:'gre-qset',items:[{n:1,kind:'se',nopt:6,ans:[1,2],txt:{opts:['a','b','c','d','e','f']}}]}]};
  const r=restorePractice(unit,last);assert.ok(r.issues[0]);assert.equal(r.summary.total,0);
});

test('answer-only review of later sections restores prior text choices',()=>{
  const unit=JSON.parse(readFileSync(new URL('../courses/gre-vx/u02-2025-01-14-v2.json',import.meta.url),'utf8'));
  const answers=unit.blocks[0].items.map(it=>it.kind==='ss'?it.ansText:it.ans.join(','));
  const r=restorePractice(unit,{answerFormat:'gre-vx-text-v2',answers});
  assert.equal(r.summary.correct,15);
  assert.equal(r.issues.some(Boolean),false);
});

test('legacy OCR option indices restore selected words when the displayed options were shifted',()=>{
  const unit=JSON.parse(readFileSync(new URL('../courses/gre-vx/u11-2025-01-02-v1.json',import.meta.url),'utf8'));
  const answers=unit.blocks[0].items.map(()=> '');
  // The old A displayed the actual B word. Restore that word, not the letter.
  answers[3]='0';
  const r=restorePractice(unit,{answerFormat:'gre-vx-text-v2',answers});
  assert.equal(r.answers[3],'1');
  assert.equal(r.issues[3],undefined);
  answers[3]='4'; // obsolete instruction text masquerading as option E
  const bad=restorePractice(unit,{answerFormat:'gre-vx-text-v2',answers});
  assert.equal(bad.rawAnswers[3],'4');assert.ok(bad.issues[3]);
  assert.equal(bad.summary.wrong.includes(3),false);
});
