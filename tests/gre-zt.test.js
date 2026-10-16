import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {gradeItem, summarize} from '../js/core/qgrade.js';

const read = p => JSON.parse(readFileSync(new URL(p, import.meta.url), 'utf8'));
const COURSES = [
  {id: 'gre-zt', audit: 'audit.json', firstTest: 1, counts: {mc1:116,tc:234,se:350}, pending: []},
  // 校对认为配套答案不可靠的题：保留原答案，但标为待核对、不计分，并附说明
  {id: 'gre-zt-101', audit: 'audit-101.json', firstTest: 51, counts: {mc1:109,tc:241,se:350}, pending: ['u96-test98-s2#5']},
];

for (const {id, audit: auditFile, firstTest, counts: expectedCounts, pending} of COURSES)
test(`Zhang Wei ${id} (Test ${firstTest}–${firstTest+49}) preserves sequence, all 700 answer keys and text-only controls`, () => {
  const course = read(`../courses/${id}/course.json`);
  const audit = read('../tools/course/grzt/' + auditFile);
  assert.ok(read('../courses/index.json').courses.some(c => c.id === course.id));
  assert.equal(course.units.length, 100);
  let total = 0, pendingSeen = 0;
  const counts = {};
  for (const [i, entry] of course.units.entries()) {
    const unit = read(`../courses/${id}/` + entry.file);
    const block = unit.blocks[0];
    assert.equal(entry.id, `u${String(i+1).padStart(2,'0')}-test${String(Math.floor(i/2)+firstTest).padStart(2,'0')}-s${i%2+1}`);
    assert.equal(block.items.length, 7);
    const answers = [];
    for (const [j, q] of block.items.entries()) {
      total++;
      counts[q.kind] = (counts[q.kind] || 0) + 1;
      assert.equal(q.n, j+1);
      assert.ok(q.txt.stem[0].length > 30);
      assert.equal(q.imgs, undefined);
      assert.equal(q.img, undefined);
      assert.equal(q.sourceAnswer, audit.items[i*7+j].sourceAnswer);
      assert.equal(audit.items[i*7+j].unit, entry.id);
      const expected = [...q.sourceAnswer].map((c,k) => c.charCodeAt(0)-65-(q.kind==='tc'?3*k:0));
      assert.deepEqual(q.ans, expected);
      const options = q.kind==='tc' ? q.txt.cols.flat() : q.txt.opts;
      assert.ok(options.every(t=>typeof t==='string' && t.trim()));
      assert.ok(!/GRE\s*\d+|微信公众号/.test(JSON.stringify(q.txt)), 'PDF footer leaked into question');
      if(q.kind==='tc') {
        assert.equal(q.txt.cols.length,q.blanks);
        assert.ok(q.txt.cols.every(c=>c.length===3));
        assert.equal(q.ans.length,q.blanks);
      } else assert.equal(options.length,q.nopt);
      answers.push(expected.join(','));
      if (pending.includes(`${entry.id}#${q.n}`)) {
        assert.equal(q.answerPending, true);
        assert.ok(q.explanation.includes([...q.sourceAnswer].join('/')), 'note names the source key');
        pendingSeen++;
        continue;
      }
      assert.ok(!('explanation' in q) && !('answerPending' in q));
      assert.ok(gradeItem(q, expected.join(',')));
      const wrong=[...expected]; wrong[0]=(wrong[0]+1)%(q.kind==='tc'?3:q.nopt);
      assert.equal(gradeItem(q,wrong.join(',')),false);
    }
    const s = summarize(block.items,answers);
    assert.equal(s.correct, s.total);
  }
  assert.equal(total,700);
  assert.equal(pendingSeen, pending.length);
  assert.deepEqual(counts,expectedCounts);
});
