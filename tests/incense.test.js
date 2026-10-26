import { test } from 'node:test';
import assert from 'node:assert/strict';
import { BURN_MS, cleanWish, WISH_MAX, burnProgress, isBurning, remainingMs, fmtRemaining, incenseStreak, dayFromDoc, meritLine } from '../js/core/incense.js';

const NOW = new Date(2026, 9, 5, 10, 0); // 2026-10-05

test('cleanWish：去空白、合并空白、截断', ()=>{
  assert.equal(cleanWish('  考试\n\n顺利  '), '考试 顺利');
  assert.equal(cleanWish(undefined), '');
  assert.equal(cleanWish('a'.repeat(100)).length, WISH_MAX);
});

test('burnProgress / isBurning / remainingMs', ()=>{
  const t = 1_000_000;
  assert.equal(burnProgress(0, t), 1);
  assert.equal(burnProgress(t, t), 0);
  assert.equal(burnProgress(t, t + BURN_MS / 2), 0.5);
  assert.equal(burnProgress(t, t + BURN_MS * 2), 1);
  assert.equal(burnProgress(t + 5000, t), 0); // 别的设备时钟快一点也不出负数
  assert.equal(isBurning(t, t + BURN_MS - 1), true);
  assert.equal(isBurning(t, t + BURN_MS), false);
  assert.equal(remainingMs(t, t + 1000), BURN_MS - 1000);
});

test('fmtRemaining', ()=>{
  assert.equal(fmtRemaining(180000), '3:00');
  assert.equal(fmtRemaining(61500), '1:02');
  assert.equal(fmtRemaining(-5), '0:00');
});

test('incenseStreak：今天没上从昨天往前数', ()=>{
  assert.equal(incenseStreak(['2026-10-05','2026-10-04'], NOW), 2);
  assert.equal(incenseStreak(['2026-10-04','2026-10-03'], NOW), 2);
  assert.equal(incenseStreak(['2026-10-03'], NOW), 0);
});

test('dayFromDoc：缺字段给默认值，丢掉坏的心愿', ()=>{
  assert.deepEqual(dayFromDoc(null), {sticks:0, wishes:[], merit:0, litAt:0});
  const d = dayFromDoc({sticks:2, merit:'x', litAt:5, wishes:[{text:'平安', ts:1}, {text:''}, null, {ts:2}]});
  assert.equal(d.sticks, 2); assert.equal(d.merit, 0); assert.equal(d.litAt, 5);
  assert.deepEqual(d.wishes, [{text:'平安', ts:1}]);
});

test('meritLine 只在特定次数出现', ()=>{
  assert.ok(meritLine(108));
  assert.equal(meritLine(7), null);
});
