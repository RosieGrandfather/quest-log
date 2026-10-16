import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync,existsSync} from 'node:fs';

const read = relative => JSON.parse(readFileSync(new URL(relative,import.meta.url),'utf8'));
const course=read('../courses/gre-vx/course.json');

test('every GRE Verbal 2025 question has text and compatible answer controls',()=>{
  let count=0;
  for(const entry of course.units){
    const unit=read('../courses/gre-vx/'+entry.file);
    assert.equal(unit.id,entry.id);
    assert.ok(unit.answerFormat,'corrected choices must not restore obsolete answer indices');
    for(const item of unit.blocks[0].items){
      count++;
      const at=unit.id+' question '+item.n, tx=item.txt;
      assert.ok(tx?.stem?.length,at+' missing stem');
      assert.ok(tx.stem.every(s=>typeof s==='string'&&s.trim()),at);
      assert.ok(existsSync(new URL('../courses/gre-vx/img/'+item.img,import.meta.url)),at+' image');
      if(item.kind==='tc'){
        assert.equal(tx.cols.length,item.blanks,at+' blank groups');
        assert.equal(tx.stem.join(' ').match(/____/g)?.length,item.blanks,at+' stem blanks');
        assert.ok(tx.cols.every(col=>col.length===3&&col.every(s=>s.trim())),at+' column choices');
      }else if(item.kind==='ss'){
        assert.ok(tx.sentences?.length,at+' missing clickable sentences');
        assert.equal(tx.sentences.join(' '),tx.pass.join(' '),at+' sentence content');
      }else{
        assert.equal(tx.opts.length,item.nopt,at+' choice count');
        assert.ok(tx.opts.every(s=>s.trim()&&!/select (?:one|two|an?)\b.*choice/i.test(s)),at+' instruction in choices');
        if(item.kind==='se')assert.equal(item.nopt,6,at);
      }
      const [date,file]=item.img.split('/');
      const source=read('../tools/course/grvx/ocr/txt-'+date+'.json');
      const original=source[Number(file.split('-')[0])+'-'+item.n];
      const {ok,...sourceText}=original;
      assert.equal(ok,true,at+' generator source');
      assert.deepEqual(sourceText,tx,at+' stale generator text');
    }
  }
  assert.ok(count>0);
});
