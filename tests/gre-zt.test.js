import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {gradeItem, summarize} from '../js/core/qgrade.js';

const read = p => JSON.parse(readFileSync(new URL(p, import.meta.url), 'utf8'));
const course = read('../courses/gre-zt/course.json');
const audit = read('../tools/course/grzt/audit.json');

test('Zhang Wei first 50 sections preserve sequence, all 350 answer keys and text-only controls', () => {
  assert.ok(read('../courses/index.json').courses.some(c => c.id === course.id));
  assert.equal(course.units.length, 50);
  let total = 0;
  const counts = {};
  for (const [i, entry] of course.units.entries()) {
    const unit = read('../courses/gre-zt/' + entry.file);
    const block = unit.blocks[0];
    assert.equal(entry.id, `u${String(i+1).padStart(2,'0')}-test${String(Math.floor(i/2)+1).padStart(2,'0')}-s${i%2+1}`);
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
      assert.ok(!('explanation' in q));
      answers.push(expected.join(','));
      assert.ok(gradeItem(q, expected.join(',')));
      const wrong=[...expected]; wrong[0]=(wrong[0]+1)%(q.kind==='tc'?3:q.nopt);
      assert.equal(gradeItem(q,wrong.join(',')),false);
    }
    assert.equal(summarize(block.items,answers).correct,7);
  }
  assert.equal(total,350);
  assert.deepEqual(counts,{mc1:60,tc:115,se:175});
});
