import { test } from 'node:test';
import assert from 'node:assert/strict';
import { REMINDERS, shouldShowReminder, nextReminderDay } from '../js/core/reminders.js';

const at = (h, m = 0, day = 13) => new Date(2026, 9, day, h, m);

test('一共 7 天，每天都有边界提醒和正向鼓励', ()=>{
  assert.equal(REMINDERS.length, 7);
  REMINDERS.forEach(r=>{ assert.ok(r.boundary && r.positive); });
});
test('早上 7 点前不弹，7:00 起可以弹', ()=>{
  assert.equal(shouldShowReminder(at(6, 59), '2026-10-12'), false);
  assert.equal(shouldShowReminder(at(7, 0), '2026-10-12'), true);
  assert.equal(shouldShowReminder(at(23, 30), '2026-10-12'), true);
});
test('今天已经弹过就不再弹，第二天可以再弹', ()=>{
  assert.equal(shouldShowReminder(at(9), '2026-10-13'), false);
  assert.equal(shouldShowReminder(at(9, 0, 14), '2026-10-13'), true);
});
test('从来没弹过（lastISO 为空）→ 可以弹', ()=>{
  assert.equal(shouldShowReminder(at(8), undefined), true);
});
test('Day 顺序：没弹过 → 1，1→2 … 7→1', ()=>{
  assert.equal(nextReminderDay(undefined), 1);
  assert.equal(nextReminderDay(1), 2);
  assert.equal(nextReminderDay(6), 7);
  assert.equal(nextReminderDay(7), 1);
});
