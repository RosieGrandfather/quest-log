import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { unitMistakes, countByKind, toMarkdown } from '../js/core/mistakes.js';
import { encodeSel } from '../js/core/practice.js';

const load = p => JSON.parse(readFileSync(new URL(`../courses/${p}`, import.meta.url), 'utf8'));
const ctx = (courseId, unitTitle)=> ({courseId, courseTitle:courseId, unitTitle});
const right = it => it.kind === 'tc' ? it.ans.join(',') : it.ans.join(',');

test('张巍填空：只收答错和没答的题，带中文释义和答案文字', ()=>{
  const unit = load('gre-zt/u01-test01-s1.json');
  const items = unit.blocks.find(b=> b.type === 'gre-qset').items;
  const answers = items.map(right);
  answers[0] = String((items[0].ans[0] + 1) % 5);   // 第 1 题答错
  answers[1] = '';                                   // 第 2 题没答
  const rows = unitMistakes(ctx('gre-zt', 'T1S1'), unit, {answers, answerFormat:unit.answerFormat});
  assert.deepEqual(rows.map(r=> r.n), [1, 2]);
  assert.equal(rows[0].kind, '单选题');
  assert.equal(rows[0].correct, 'B');
  assert.equal(rows[0].options[0].choices[1].zh, '狭隘的；与外界隔绝的');
  assert.equal(rows[1].picked, '未作答');
  assert.ok(rows[1].blank);
  assert.equal(rows[1].options.length, 2);           // 两个空各一组
});

test('全对时没有错题；没有提交记录时返回空', ()=>{
  const unit = load('gre-zt/u01-test01-s1.json');
  const items = unit.blocks.find(b=> b.type === 'gre-qset').items;
  assert.deepEqual(unitMistakes(ctx('gre-zt','x'), unit, {answers:items.map(right), answerFormat:unit.answerFormat}), []);
  assert.deepEqual(unitMistakes(ctx('gre-zt','x'), unit, null), []);
});

test('张巍阅读：错题带文章，同一篇文章在 Markdown 里只出现一次', ()=>{
  const unit = load('gre-zr/u01-p001-p005.json');
  const items = unit.blocks.find(b=> b.type === 'gre-qset').items;
  const p1 = items.filter(it=> it.passage === 'p1' && it.kind === 'mc1');
  assert.ok(p1.length >= 2);
  const answers = items.map(it=> it.kind === 'ss' ? '' : right(it));
  p1.slice(0, 2).forEach(it=>{ answers[items.indexOf(it)] = String((it.ans[0] + 1) % it.nopt); });
  const rows = unitMistakes(ctx('gre-zr', 'P1-5'), unit, {answers, answerFormat:unit.answerFormat});
  assert.equal(rows.length, 2);
  assert.ok(rows[0].passage.text.length > 100);
  const md = toMarkdown(rows, {title:'t', date:'2026-11-06'});
  assert.equal(md.split('#### Passage').length - 1, 1);
  assert.ok(md.includes('共 2 道错题，来自 1 节'));
});

test('官方 Verbal 12 套（gre-set）：按组判错，多空题分空显示', ()=>{
  const unit = load('gre-vr/u04-tc-easy.json');
  const items = unit.blocks.find(b=> b.type === 'gre-set').items;
  const answers = items.map(it=> encodeSel(it.groups.map(g=> g.correct)));
  const multi = items.findIndex(it=> it.groups.length > 1);
  answers[0] = encodeSel(items[0].groups.map(g=> [(g.correct[0] + 1) % g.options.length]));
  if(multi >= 0) answers[multi] = '';
  const rows = unitMistakes(ctx('gre-vr', 'TC easy'), unit, {answers});
  assert.equal(rows[0].n, 1);
  assert.equal(rows[0].kind, '文本补全');
  assert.ok(rows[0].expl.length > 20);
  if(multi >= 0){
    const r = rows.find(x=> x.n === multi + 1);
    assert.ok(r.blank);
    assert.ok(r.correct.includes('空(i)') || r.correct.includes('Blank'));
  }
});

test('按题型统计', ()=>{
  assert.deepEqual(countByKind([{kind:'a'},{kind:'b'},{kind:'b'}]), [['b',2],['a',1]]);
});
