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
