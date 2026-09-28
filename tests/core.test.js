/* 纯逻辑测试：npm test（或 node --test tests/） */
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { computeStats, computeStreak } from '../js/core/stats.js';
import { levelInfo } from '../js/core/levels.js';
import { localISO, fmtDateLabel } from '../js/core/dates.js';
import { escapeHTML } from '../js/core/html.js';

const NOW = new Date(2026, 8, 28, 10, 0); // 2026-09-28 本地时间
const days = (...offsets)=> new Set(offsets.map(o=>{ const d=new Date(NOW); d.setDate(d.getDate()-o); return localISO(d); }));

test('localISO 补零', ()=>{
  assert.equal(localISO(new Date(2026, 0, 5)), '2026-01-05');
});

test('fmtDateLabel 今天 / 昨天 / 其他日期', ()=>{
  assert.equal(fmtDateLabel('2026-09-28', NOW), '今天');
  assert.equal(fmtDateLabel('2026-09-27', NOW), '昨天');
  assert.equal(fmtDateLabel('2026-09-01', NOW), '2026-09-01');
});

test('连续天数：今天有记录，往前数', ()=>{
  assert.equal(computeStreak(days(0,1,2), NOW), 3);
});
test('连续天数：今天还没记录但昨天有，不断签', ()=>{
  assert.equal(computeStreak(days(1,2), NOW), 2);
});
test('连续天数：昨天和今天都没有 = 0', ()=>{
  assert.equal(computeStreak(days(2,3), NOW), 0);
});
test('连续天数：中间断一天就停', ()=>{
  assert.equal(computeStreak(days(0,1,3,4), NOW), 2);
});
test('连续天数：跨月', ()=>{
  const oct1 = new Date(2026, 9, 1);
  assert.equal(computeStreak(new Set(['2026-10-01','2026-09-30','2026-09-29']), oct1), 3);
});

test('computeStats：积分、兑换、记录次数（签到不算次数但算连续）', ()=>{
  const log = [
    {kind:'earn', category:'daily', amount:5, dateISO:'2026-09-28'},
    {kind:'earn', category:'mind', amount:10, dateISO:'2026-09-27'},
    {kind:'earn', category:'body', amount:15, dateISO:'2026-09-27'},
    {kind:'spend', category:'reward', amount:20, dateISO:'2026-09-27'},
  ];
  const s = computeStats(log, NOW);
  assert.equal(s.totalEarned, 30);
  assert.equal(s.totalSpent, 20);
  assert.equal(s.balance, 10);
  assert.equal(s.entriesCount, 2);
  assert.equal(s.streak, 2);
});
test('computeStats：只有兑换的日子不算连续', ()=>{
  const s = computeStats([{kind:'spend', amount:5, dateISO:'2026-09-28'}], NOW);
  assert.equal(s.streak, 0);
});

test('等级：门槛边界', ()=>{
  assert.deepEqual(levelInfo(0), {name:'新手上路', sub:'Lv.1', curMin:0, nextMin:100});
  assert.equal(levelInfo(99).sub, 'Lv.1');
  assert.equal(levelInfo(100).sub, 'Lv.2');
  assert.equal(levelInfo(20199).sub, 'Lv.19');
});
test('等级：超过最后一级每 5000 分再升一级', ()=>{
  assert.equal(levelInfo(20200).sub, 'Lv.20');
  assert.deepEqual(levelInfo(25200), {name:'传奇远征者', sub:'Lv.21', curMin:25200, nextMin:30200});
});

test('escapeHTML', ()=>{
  assert.equal(escapeHTML(`<b>"a"&'b'</b>`), '&lt;b&gt;&quot;a&quot;&amp;&#39;b&#39;&lt;/b&gt;');
});
