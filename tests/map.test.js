import { test } from 'node:test';
import assert from 'node:assert/strict';
import { cityPositions, roadPoints, sampleRoad, landDisks, onLand, SPACING, HUB_RADIUS, stagesOf, progressOf, overallProgress, dueAwards, parseRefs, refsToText, TEMPLATES, newProject, freeSlot, normalizeProject, nextStepId, activeCount, STEP_POINTS, STAGE_BONUS, PROJECT_BONUS, hash32 } from '../js/core/map.js';

const dist = (a, b) => Math.hypot(a.x - b.x, a.z - b.z);

test('布局：同样的输入每次结果一样', ()=>{
  assert.deepEqual(cityPositions(2, 'p-abc', 12), cityPositions(2, 'p-abc', 12));
});

test('布局：加步骤不会让前面的城挪位置', ()=>{
  const a = cityPositions(1, 'p-xyz', 5), b = cityPositions(1, 'p-xyz', 30);
  assert.deepEqual(b.slice(0, 5), a);
});

test('布局：相邻两座城的距离在合理范围内（有随机摆动），路在往外长', ()=>{
  const c = cityPositions(0, 'p1', 25);
  for(let i = 1; i < c.length; i++) assert.ok(dist(c[i], c[i-1]) > SPACING * 0.6 && dist(c[i], c[i-1]) < SPACING * 1.5);
  assert.ok(Math.hypot(c[24].x, c[24].z) > Math.hypot(c[2].x, c[2].z) + 60, '越往后离首都越远');
  assert.ok(Math.hypot(c[0].x, c[0].z) > HUB_RADIUS);
});

test('布局：5 个项目各 30 座城，互相不重叠', ()=>{
  const all = [];
  for(let slot = 0; slot < 5; slot++) cityPositions(slot, 'proj-' + slot, 30).forEach((p, i) => all.push({...p, slot, i}));
  let min = Infinity;
  for(let a = 0; a < all.length; a++) for(let b = a + 1; b < all.length; b++){
    if(all[a].slot === all[b].slot) continue;
    min = Math.min(min, dist(all[a], all[b]));
  }
  assert.ok(min > 6, '不同项目的城最近 ' + min.toFixed(1));
});

test('陆地：每座城都在陆地上，路上的点也在', ()=>{
  const roads = [0, 1, 2].map(s => roadPoints(s, 'p' + s, 15));
  const disks = landDisks(roads);
  for(const r of roads) for(const p of r) assert.ok(onLand(disks, p.x, p.z));
  for(const p of sampleRoad(roads[1], 6)) assert.ok(onLand(disks, p.x, p.z));
  assert.equal(onLand(disks, 999, 999), false);
});

const mk = (n, stages) => ({id: 'p1', title: 'T', steps: Array.from({length: n}, (_, i) => ({id: 's' + (i + 1), title: 'x' + (i + 1), stage: stages[i], doneAt: null}))});

test('阶段：按连续相同的阶段名分组', ()=>{
  const p = mk(5, ['A', 'A', 'B', 'B', 'B']);
  const g = stagesOf(p.steps);
  assert.deepEqual(g.map(x => [x.name, x.idx.length]), [['A', 2], ['B', 3]]);
  assert.equal(g[0].done, false);
});

test('进度与下一步', ()=>{
  const p = mk(3, ['A', 'A', 'A']);
  assert.deepEqual(progressOf(p), {done: 0, total: 3, nextIndex: 0, finished: false});
  p.steps[0].doneAt = 1;
  assert.equal(progressOf(p).nextIndex, 1);
  p.steps[1].doneAt = 1; p.steps[2].doneAt = 1;
  assert.equal(progressOf(p).finished, true);
  assert.equal(progressOf({steps: []}).finished, false);
  assert.equal(overallProgress([p, mk(1, ['A'])]), 3 / 4);
});

test('积分：点亮一步 +50；阶段做完再 +100；项目做完再 +200', ()=>{
  const p = mk(3, ['A', 'A', 'B']);
  p.steps[0].doneAt = 1;
  let a = dueAwards(p, 's1');
  assert.deepEqual(a.map(x => x.amount), [STEP_POINTS]);
  p.steps[1].doneAt = 1;
  a = dueAwards(p, 's2');
  assert.deepEqual(a.map(x => x.amount), [STEP_POINTS, STAGE_BONUS]);
  p.steps[2].doneAt = 1;
  a = dueAwards(p, 's3');
  assert.deepEqual(a.map(x => x.amount), [STEP_POINTS, STAGE_BONUS, PROJECT_BONUS]);
  assert.equal(new Set(a.map(x => x.id)).size, 3, 'id 互不相同');
  assert.deepEqual(dueAwards(p, 'nope'), []);
});

test('积分：只有一个阶段时不重复发阶段奖励', ()=>{
  const p = mk(2, ['A', 'A']);
  p.steps[0].doneAt = 1; p.steps[1].doneAt = 1;
  assert.deepEqual(dueAwards(p, 's2').map(x => x.amount), [STEP_POINTS, PROJECT_BONUS]);
});

test('积分 id 固定：重新标记同一步得到同样的 id', ()=>{
  const p = mk(2, ['A', 'B']); p.steps[0].doneAt = 5;
  assert.equal(dueAwards(p, 's1')[0].id, dueAwards(p, 's1')[0].id);
});

test('引用资料的解析与还原', ()=>{
  const t = '听前一分钟 | https://example.com/a\nhttps://example.com/b\n只是一段文字\n';
  const r = parseRefs(t);
  assert.deepEqual(r, [{title: '听前一分钟', url: 'https://example.com/a'}, {title: 'https://example.com/b', url: 'https://example.com/b'}, {title: '只是一段文字'}]);
  assert.deepEqual(parseRefs(refsToText(r)), r);
  assert.deepEqual(parseRefs(''), []);
});

test('模板：每个模板都有步骤、阶段，步骤标题不为空', ()=>{
  assert.ok(TEMPLATES.length >= 3);
  for(const t of TEMPLATES){
    assert.ok(t.steps.length >= 3);
    for(const s of t.steps){ assert.ok(s.title && s.detail && s.stage); }
  }
  assert.equal(TEMPLATES[0].steps.length, 10);
});

test('新项目与 slot', ()=>{
  const a = newProject({id: 'p1', templateId: 'music-demo', slot: 0, now: 1});
  assert.equal(a.steps.length, 10);
  assert.equal(a.steps[0].id, 's1');
  assert.equal(a.steps.every(s => s.doneAt === null), true);
  const b = newProject({id: 'p2', templateId: 'nope', slot: 1, now: 2});
  assert.equal(b.templateId, 'blank');
  assert.equal(freeSlot([a, b]), 2);
  assert.equal(freeSlot([b]), 0);
});

test('normalizeProject 补齐缺的字段', ()=>{
  const p = normalizeProject('x', {title: 'T', steps: [{title: 'a'}, {id: 's7', title: 'b', doneAt: 3}]});
  assert.equal(p.steps[0].id, 's1'); assert.equal(p.steps[0].stage, '主线'); assert.equal(p.steps[1].doneAt, 3);
  assert.equal(nextStepId(p), 's8');
  assert.equal(normalizeProject('y', null).steps.length, 0);
});

test('同时进行的项目数：停放和做完的不算', ()=>{
  const a = mk(2, ['A', 'A']), b = {...mk(2, ['A', 'A']), parked: true}, c = mk(1, ['A']);
  c.steps[0].doneAt = 1;
  assert.equal(activeCount([a, b, c]), 1);
});

test('hash32 稳定', ()=>{ assert.equal(hash32('abc'), hash32('abc')); assert.notEqual(hash32('abc'), hash32('abd')); });
