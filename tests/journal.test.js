import { test } from 'node:test';
import assert from 'node:assert/strict';
import { JOURNAL_POINTS, hasContent, charCount, journalStreak, weekdayLabel, previewText } from '../js/core/journal.js';

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
