import { test } from 'node:test';
import assert from 'node:assert/strict';
import { scoreQuiz, studyStreak, streakBonuses, dayUnitsBonus, unitKey } from '../js/core/study.js';

const Q = [{answer:0},{answer:1},{answer:2},{answer:3},{answer:0}];

test('测验得分', ()=>{
  assert.equal(scoreQuiz(Q, [0,1,2,3,0]), 100);
  assert.equal(scoreQuiz(Q, [0,1,2,3,1]), 80);
  assert.equal(scoreQuiz(Q, [0,1,2,null,1]), 60);
  assert.equal(scoreQuiz([], []), 0);
});
test('测验得分四舍五入（3 题对 2 题 = 67）', ()=>{
  assert.equal(scoreQuiz([{answer:0},{answer:0},{answer:0}], [0,0,1]), 67);
});

test('连续学习天数：重复日期只算一天', ()=>{
  const now = new Date(2026, 8, 28);
  assert.equal(studyStreak(['2026-09-28','2026-09-28','2026-09-27'], now), 2);
  assert.equal(studyStreak([], now), 0);
});

test('里程碑奖励', ()=>{
  assert.deepEqual(streakBonuses(1), []);
  assert.deepEqual(streakBonuses(7).map(b=>b.amount), [100]);
  assert.deepEqual(streakBonuses(14).map(b=>b.amount), [100]);
  assert.deepEqual(streakBonuses(29), []);
  assert.deepEqual(streakBonuses(30).map(b=>b.amount), [500]);
  assert.deepEqual(streakBonuses(60), []);
  assert.deepEqual(streakBonuses(63).map(b=>b.amount), [100]);
  assert.deepEqual(streakBonuses(100).map(b=>b.amount), [500]);
  assert.deepEqual(streakBonuses(200).map(b=>b.amount), [500]);
  assert.deepEqual(streakBonuses(300).map(b=>b.amount), [500]);
  assert.deepEqual(streakBonuses(365).map(b=>b.amount), [1000]);
  assert.deepEqual(streakBonuses(0), []);
});

test('unitKey', ()=>{
  assert.equal(unitKey('arena-0.0','u01'), 'arena-0.0__u01');
});

test('同一天学完 3 节额外奖励', ()=>{
  assert.equal(dayUnitsBonus(0), null);
  assert.equal(dayUnitsBonus(2), null);
  assert.equal(dayUnitsBonus(3).amount, 100);
  assert.equal(dayUnitsBonus(4).amount, 100);   // 超过 3 节也只是同一个奖励，发放时用「每天一个 ID」保证只发一次
});

import { pickAnchor, worthResuming } from '../js/core/resume.js';

test('阅读位置：取屏幕顶边处的第一个内容块', ()=>{
  const rects = [{top:-900,bottom:-500},{top:-500,bottom:-3},{top:-3,bottom:300},{top:300,bottom:700}];
  assert.deepEqual(pickAnchor(rects), {i:2, off:-3});
  assert.equal(pickAnchor([{top:-50,bottom:0}]), null);
  assert.equal(pickAnchor([]), null);
});
test('阅读位置：还在开头就不跳', ()=>{
  assert.equal(worthResuming(null), false);
  assert.equal(worthResuming({i:0, off:-50}), false);
  assert.equal(worthResuming({i:0, off:-400}), true);
  assert.equal(worthResuming({i:3, off:20}), true);
  assert.equal(worthResuming({i:'x', off:0}), false);
});
