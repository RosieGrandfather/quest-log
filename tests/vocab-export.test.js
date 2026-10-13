import { test } from 'node:test';
import assert from 'node:assert/strict';
import { collectUnknown, wordsLine, wordsWithMeaning, toCSV } from '../js/core/vocab-export.js';

const U1 = {id:'u01', title:'第 1 组', marks:{annul:'unknown', excavate:'know', brook:'unknown', ghost:'unknown', bad:''},
  items:[{w:'annul', ipa:'[əˈnʌl]', pos:'vt.', zh:'宣告无效', en:'to cancel'}, {w:'excavate', zh:'挖掘'}, {w:'brook', zh:'忍受，容许', pos:'v.'}]};
const U2 = {id:'u02', title:'第 2 组', marks:{x:'know'}, items:[{w:'x'}]};
const U3 = {id:'u03', title:'第 3 组', marks:{nebulous:'unknown'}, items:[{w:'nebulous', zh:'模糊的，星云的'}]};

test('只收「不会」，按词卡顺序，没标或标「会」的不收', ()=>{
  const rows = collectUnknown([U1, U2, U3]);
  assert.deepEqual(rows.map(r=>r.w), ['annul', 'brook', 'ghost', 'nebulous']);
});
test('标了但词卡里找不到的词也保留（释义留空）', ()=>{
  const g = collectUnknown([U1]).find(r=>r.w==='ghost');
  assert.equal(g.zh, ''); assert.equal(g.unit, '第 1 组');
});
test('没有任何不会的词时返回空数组', ()=>{
  assert.deepEqual(collectUnknown([U2]), []);
  assert.deepEqual(collectUnknown([]), []);
});
test('复制格式', ()=>{
  const rows = collectUnknown([U1, U3]);
  assert.equal(wordsLine(rows), 'annul, brook, ghost, nebulous');
  assert.equal(wordsWithMeaning(rows).split('\n')[0], 'annul — 宣告无效');
  assert.equal(wordsWithMeaning(rows).split('\n')[2], 'ghost');
});
test('CSV：带 BOM、含逗号和引号的字段被正确转义', ()=>{
  const csv = toCSV([{unit:'第 1 组', w:'a', ipa:'', pos:'n.', zh:'甲，乙', en:'say "hi"'}]);
  assert.ok(csv.startsWith('﻿'));
  assert.ok(csv.includes('"甲，乙","say ""hi"""'));
});
