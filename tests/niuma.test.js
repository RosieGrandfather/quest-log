import { test } from 'node:test';
import assert from 'node:assert/strict';
import { parseHM, settingsError, settingsFromDoc, workdaysInMonth, dayKind, workSecondsPerDay, workedSeconds, phase, nextMarkMs, earnedToday, monthToDate, dayProgress, fmtMoney, fmtDuration, catMode, SG_HOLIDAYS } from '../js/core/niuma.js';

const S = {start:'09:00', end:'18:00', lunchStart:'12:00', lunchEnd:'13:00', monthly:4400, leave:[]};
const at = (d, h, m = 0, s = 0) => new Date(2026, 10, d, h, m, s); // 2026 年 11 月

test('parseHM', ()=>{
  assert.equal(parseHM('09:30'), 570);
  assert.equal(parseHM('9:05'), 545);
  assert.ok(Number.isNaN(parseHM('25:00')));
  assert.ok(Number.isNaN(parseHM('')));
});

test('settingsError', ()=>{
  assert.equal(settingsError(S), '');
  assert.match(settingsError({...S, end:'08:00'}), /下班/);
  assert.match(settingsError({...S, lunchStart:'13:00', lunchEnd:'12:00'}), /午休/);
  assert.match(settingsError({...S, lunchStart:'08:00'}), /午休/);
  assert.match(settingsError({...S, monthly:''}), /月薪/);
  assert.equal(settingsFromDoc(null), null);
  assert.deepEqual(settingsFromDoc({...S, monthly:'4400'}).leave, []);
});

test('workdaysInMonth / dayKind', ()=>{
  assert.equal(workdaysInMonth(at(1, 9)), 21); // 2026-11
  assert.equal(dayKind(at(7, 10)), 'weekend'); // 周六
  assert.equal(dayKind(at(9, 10)), 'holiday'); // 屠妖节补假
  assert.equal(dayKind(at(4, 10), ['2026-11-04']), 'leave');
  assert.equal(dayKind(at(4, 10)), 'work');
  for(const iso of SG_HOLIDAYS){
    const [y, m, d] = iso.split('-').map(Number);
    const wd = new Date(y, m - 1, d).getDay();
    assert.ok(wd >= 1 && wd <= 5, iso + ' 不是工作日');
  }
});

test('工时：午休不算，下班后封顶', ()=>{
  assert.equal(workSecondsPerDay(S), 8 * 3600);
  assert.equal(workedSeconds(S, at(4, 8)), 0);
  assert.equal(workedSeconds(S, at(4, 11)), 2 * 3600);
  assert.equal(workedSeconds(S, at(4, 12, 30)), 3 * 3600);
  assert.equal(workedSeconds(S, at(4, 14)), 4 * 3600);
  assert.equal(workedSeconds(S, at(4, 20)), 8 * 3600);
});

test('phase / nextMarkMs', ()=>{
  assert.equal(phase(S, at(4, 8, 59)), 'before');
  assert.equal(phase(S, at(4, 9)), 'work');
  assert.equal(phase(S, at(4, 12, 10)), 'lunch');
  assert.equal(phase(S, at(4, 18)), 'after');
  assert.equal(nextMarkMs(S, at(4, 16, 44, 2)), (1 * 3600 + 15 * 60 + 58) * 1000);
  assert.equal(nextMarkMs(S, at(4, 12, 30)), 30 * 60 * 1000);
  assert.equal(nextMarkMs(S, at(4, 19)), null);
});

test('钱：日薪 = 月薪 / 工作日数，按工时摊', ()=>{
  const daily = 4400 / 21;
  assert.equal(earnedToday(S, at(4, 8)), 0);
  assert.ok(Math.abs(earnedToday(S, at(4, 14)) - daily / 2) < 1e-9);
  assert.ok(Math.abs(earnedToday(S, at(4, 23)) - daily) < 1e-9);
  assert.equal(earnedToday(S, at(7, 14)), 0); // 周末
  assert.ok(Math.abs(earnedToday(S, at(9, 23)) - daily) < 1e-9); // 公假照样算
  // 11/4 之前有 11/2、11/3 两个工作日
  assert.ok(Math.abs(monthToDate(S, at(4, 23)) - daily * 3) < 1e-9);
  // 月底下班后 = 整月工资
  assert.ok(Math.abs(monthToDate(S, at(30, 23)) - 4400) < 1e-6);
  assert.equal(dayProgress(S, at(4, 14)), 0.5);
});

test('catMode', ()=>{
  assert.equal(catMode(S, at(4, 10)).cat, 'run');
  assert.equal(catMode(S, at(4, 12, 30)).cat, 'sleep');
  assert.equal(catMode(S, at(4, 8)).cat, 'sleep');
  assert.equal(catMode(S, at(4, 19)).cat, 'done');
  assert.equal(catMode(S, at(7, 10)).cat, 'weekend');
  assert.equal(catMode(S, at(9, 10)).cat, 'sleep');
  assert.equal(catMode({...S, leave:['2026-11-04']}, at(4, 10)).cat, 'sleep');
});

test('格式化', ()=>{
  assert.equal(fmtMoney(1234.56789), 'S$1,234.5679');
  assert.equal(fmtMoney(99.7, 2), 'S$99.70');
  assert.equal(fmtDuration((3600 + 15 * 60 + 58) * 1000), '1小时15分58秒');
  assert.equal(fmtDuration(59_500), '59秒');
});
