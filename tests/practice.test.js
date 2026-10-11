import { test } from 'node:test';
import assert from 'node:assert/strict';
import { gradeItem, isAnswered, encodeSel, decodeSel, summarize } from '../js/core/practice.js';

const SC = {kind:'tc', groups:[{options:['a','b','c','d','e'], pick:1, correct:[3]}]};
const TC2 = {kind:'tc', groups:[{options:['a','b','c'], pick:1, correct:[0]}, {options:['d','e','f'], pick:1, correct:[2]}]};
const SE = {kind:'se', groups:[{options:['1','2','3','4','5','6'], pick:2, correct:[1,5]}]};
const RC = {kind:'rc', groups:[{options:['x','y','z'], pick:'any', correct:[0,2]}]};

test('单空 / 多空 / 选两项 / 多选：必须全对才算对', ()=>{
  assert.equal(gradeItem(SC, [[3]]), true);
  assert.equal(gradeItem(SC, [[2]]), false);
  assert.equal(gradeItem(TC2, [[0], [2]]), true);
  assert.equal(gradeItem(TC2, [[0], [1]]), false);
  assert.equal(gradeItem(SE, [[5, 1]]), true);       // 顺序无所谓
  assert.equal(gradeItem(SE, [[1]]), false);          // 只选一个不算对
  assert.equal(gradeItem(SE, [[1, 5, 0]]), false);
  assert.equal(gradeItem(RC, [[2, 0]]), true);
  assert.equal(gradeItem(RC, [[0]]), false);
  assert.equal(gradeItem(RC, []), false);
});

test('是否作答：每组至少选了一个', ()=>{
  assert.equal(isAnswered(TC2, [[0], []]), false);
  assert.equal(isAnswered(TC2, [[0], [1]]), true);
  assert.equal(isAnswered(SC, []), false);
});

test('作答编码 / 解码（Firestore 不能存嵌套数组）', ()=>{
  assert.equal(encodeSel([[1, 3]]), '1,3');
  assert.equal(encodeSel([[0], [2]]), '0|2');
  assert.equal(encodeSel([[], [2]]), '|2');
  assert.deepEqual(decodeSel('1,3', SE), [[1, 3]]);
  assert.deepEqual(decodeSel('0|2', TC2), [[0], [2]]);
  assert.deepEqual(decodeSel('|2', TC2), [[], [2]]);
  assert.deepEqual(decodeSel('', SC), [[]]);
  assert.deepEqual(decodeSel(undefined, TC2), [[], []]);
});

test('整套总结：对错数、正确率、分题型、没作答的算错', ()=>{
  const s = summarize([SC, TC2, SE, RC], [[[3]], [[0], [1]], [[1, 5]], []]);
  assert.equal(s.total, 4);
  assert.equal(s.correct, 2);
  assert.equal(s.pct, 50);
  assert.equal(s.blank, 1);
  assert.deepEqual(s.wrong, [1, 3]);
  assert.deepEqual(s.byKind, {tc:{total:2, correct:1}, se:{total:1, correct:1}, rc:{total:1, correct:0}});
  assert.equal(summarize([], []).pct, 0);
});
