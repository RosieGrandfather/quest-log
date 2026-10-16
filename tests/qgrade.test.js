import test from 'node:test';
import assert from 'node:assert/strict';
import { parseNum, gradeItem, isAnswered, summarize, answerText, pickedText } from '../js/core/qgrade.js';

test('parseNum handles commas, percent and fractions', ()=>{
  assert.equal(parseNum('2,500'), 2500);
  assert.equal(parseNum(' 5/2 '), 2.5);
  assert.equal(parseNum('67%'), 67);
  assert.ok(Number.isNaN(parseNum('abc')));
  assert.ok(Number.isNaN(parseNum('1/0')));
});
test('single choice and qc', ()=>{
  const it = {kind:'mc1', ans:[3]};
  assert.ok(gradeItem(it, '3')); assert.ok(!gradeItem(it, '2')); assert.ok(!gradeItem(it, ''));
  assert.ok(gradeItem({kind:'qc', ans:[0]}, '0'));
});
test('multi choice needs the exact set', ()=>{
  const it = {kind:'mcn', ans:[0, 2]};
  assert.ok(gradeItem(it, '2,0')); assert.ok(!gradeItem(it, '0')); assert.ok(!gradeItem(it, '0,1,2'));
});
test('numeric entry accepts equivalent forms', ()=>{
  const it = {kind:'ne', ans:'2500'};
  assert.ok(gradeItem(it, '2,500')); assert.ok(gradeItem(it, '2500.0')); assert.ok(!gradeItem(it, '2501'));
  const f = {kind:'ne', ans:'5/2', frac:true};
  assert.ok(gradeItem(f, '10/4')); assert.ok(gradeItem(f, '5 / 2')); assert.ok(!gradeItem(f, '5/3'));
  assert.ok(!isAnswered(f, '5')); assert.ok(isAnswered(f, '5/2'));
  assert.ok(gradeItem({kind:'ne', ans:'0.76'}, '.76'));
});
test('summarize and texts', ()=>{
  const items = [{kind:'qc', ans:[1]}, {kind:'ne', ans:'7'}, {kind:'mcn', ans:[0, 1]}];
  const s = summarize(items, ['1', '8', '']);
  assert.equal(s.correct, 1); assert.equal(s.blank, 1); assert.deepEqual(s.wrong, [1, 2]); assert.equal(s.pct, 33);
  assert.equal(answerText(items[2]), 'A、B'); assert.equal(pickedText(items[2], ''), '未作答');
});

test('Verbal kinds: se, tc and self-checked ss', ()=>{
  const se = {kind:'se', ans:[0, 4]};
  assert.ok(gradeItem(se, '4,0')); assert.ok(!gradeItem(se, '0')); assert.ok(!gradeItem(se, '0,3'));
  const tc = {kind:'tc', blanks:3, ans:[2, 1, 1]};
  assert.ok(gradeItem(tc, '2,1,1')); assert.ok(!gradeItem(tc, '1,2,1')); assert.ok(!isAnswered(tc, '2,,1')); assert.ok(!gradeItem(tc, '2,1'));
  assert.equal(answerText(tc), '空(i) C　空(ii) B　空(iii) B'); assert.equal(pickedText(tc, '0,1,2'), '空(i) A　空(ii) B　空(iii) C');
  const ss = {kind:'ss', ansText:'第三句话'};
  const s = summarize([se, tc, ss], ['0,4', '2,1,0', 'x']);
  assert.equal(s.total, 2); assert.equal(s.correct, 1); assert.deepEqual(s.wrong, [1]); assert.deepEqual(s.selfCheck, [2]);
  assert.equal(answerText(ss), '第三句话');
});

test('clickable sentences preserve full text and reject obsolete A–E answers', ()=>{
  const sentences = ['An author writes.', 'Another author disagrees.'];
  const item = {kind:'ss', txt:{sentences}, ansText:'待核对'};
  assert.ok(isAnswered(item, sentences[1]));
  assert.ok(!isAnswered(item, '4'));
  assert.ok(!isAnswered(item, ''));
  assert.ok(!isAnswered(item, 'A sentence not in this passage.'));
  assert.equal(pickedText(item, sentences[1]), sentences[1]);
  assert.equal(pickedText(item, '4'), '未作答');
  const result = summarize([item], [sentences[1]]);
  assert.equal(result.total, 0);
  assert.deepEqual(result.selfCheck, [0]);
});
