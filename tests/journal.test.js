import { test } from 'node:test';
import assert from 'node:assert/strict';
import { JOURNAL_POINTS, hasContent, charCount, journalStreak, weekdayLabel, previewText, PLACEHOLDER, journalStreakBonus, monthGrid, shiftMonth } from '../js/core/journal.js';

const NOW = new Date(2026, 9, 5, 10, 0); // 2026-10-05（周一）

test('日记每天 5 分', ()=>{ assert.equal(JOURNAL_POINTS, 5); });

test('hasContent：空白不算有内容', ()=>{
  assert.equal(hasContent(''), false);
  assert.equal(hasContent('  \n\t '), false);
  assert.equal(hasContent(undefined), false);
  assert.equal(hasContent('累'), true);
});

test('charCount 不算空白', ()=>{ assert.equal(charCount('今天 很累\n ok'), 6); });

test('journalStreak：今天没写从昨天往前数，断一天归零', ()=>{
  assert.equal(journalStreak(['2026-10-05','2026-10-04','2026-10-03'], NOW), 3);
  assert.equal(journalStreak(['2026-10-04','2026-10-03'], NOW), 2);
  assert.equal(journalStreak(['2026-10-03'], NOW), 0);
  assert.equal(journalStreak([], NOW), 0);
});

test('weekdayLabel', ()=>{ assert.equal(weekdayLabel('2026-10-05'), '周一'); assert.equal(weekdayLabel('2026-10-04'), '周日'); });

test('previewText 取第一行有字的内容并截断', ()=>{
  assert.equal(previewText('\n\n  第一行  \n第二行'), '第一行');
  assert.equal(previewText('a'.repeat(50), 10), 'a'.repeat(10)+'…');
  assert.equal(previewText(''), '');
});

test('提示语每天一样', ()=>{ assert.equal(PLACEHOLDER, "What's on your mind today?"); });
test('monthGrid：周一在前，补齐空位', ()=>{
  const w = monthGrid('2026-10'); // 10 月 1 日是周四
  assert.deepEqual(w[0].slice(0,4), [null,null,null,'2026-10-01']);
  assert.equal(w.flat().filter(Boolean).length, 31);
  assert.ok(w.every(r=>r.length===7));
  assert.equal(monthGrid('2026-02').flat().filter(Boolean).length, 28);
});
test('shiftMonth 跨年', ()=>{ assert.equal(shiftMonth('2026-01',-1),'2025-12'); assert.equal(shiftMonth('2026-12',1),'2027-01'); });

test('日记连续奖励：只在里程碑天数发，其余为空', ()=>{
  assert.equal(journalStreakBonus(1), null);
  assert.equal(journalStreakBonus(2), null);
  assert.equal(journalStreakBonus(3).amount, 5);
  assert.equal(journalStreakBonus(7).amount, 15);
  assert.equal(journalStreakBonus(8), null);
  assert.equal(journalStreakBonus(66).amount, 66);
  assert.equal(journalStreakBonus(365).amount, 200);
});
