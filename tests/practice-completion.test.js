import test from 'node:test';
import assert from 'node:assert/strict';

const records={log:new Map(),progress:new Map()};
const ref=(map,id)=>({id,get:async()=>({exists:map.has(id),data:()=>map.get(id)}),set:async(v)=>map.set(id,{...map.get(id),...v}),map});
const fs={runTransaction:async fn=>fn({get:r=>r.get(),set:(r,v)=>r.map.set(r.id,v)})};
globalThis.firebaseConfig={};
globalThis.firebase={initializeApp(){},auth:()=>({}),firestore:Object.assign(()=>fs,{FieldValue:{}})};
const node=()=>({children:[],hidden:false,style:{},append(...c){this.children.push(...c);},remove(){this.removed=true;},addEventListener(name,fn){this[name]=fn;}});
globalThis.document={createElement:node,getElementById:()=>node()};
const {savePracticeSubmission}=await import('../js/study/practice-save.js');
const {completeUnit}=await import('../js/data/study.js');
const {T}=await import('../js/study/state.js');
const {unitKey}=await import('../js/core/study.js');
const course={id:'test-course'},unit={id:'test-unit',title:'练习',minutes:15,answerFormat:'v1',blocks:[{type:'gre-qset',items:[{n:1,kind:'mc1',txt:{opts:['a','b']},ans:[0]}]}]};
const sum={correct:0,total:1,pct:0};
function setup(){
 records.log.clear();records.progress.clear();T.progress={};
 T.cols={log:{doc:id=>ref(records.log,id),where:()=>({get:async()=>({docs:[...records.log.values()].filter(v=>v.category==='study').map(v=>({data:()=>v}))})})},studyProgress:{doc:id=>ref(records.progress,id)}};
 const host=node();host.querySelector=()=>null;return host;
}

test('submitting a practice lesson saves the score and completes it for 30 points, even with a wrong answer; redo never awards twice',async()=>{
 const host=setup();let completions=0;
 const finish=async()=>{const r=await completeUnit(T.cols,course,unit);if(r.created)completions++;};
 await savePracticeSubmission(host,course,unit,['1'],sum,finish,()=>{});
 const key=unitKey(course.id,unit.id);
 assert.equal(records.progress.get(key).practiceAttempts,1);
 assert.equal(records.progress.get(key).practiceLast.correct,0);
 assert.ok(records.progress.get(key).completedISO);
 assert.equal(records.log.get('study-'+key).amount,30);
 await savePracticeSubmission(host,course,unit,['0'],{correct:1,total:1,pct:100},finish,()=>{});
 assert.equal(records.progress.get(key).practiceAttempts,2);
 assert.equal(completions,1);assert.equal(records.log.size,1);
});

test('retrying a failed completion does not save a second attempt',async()=>{
 const host=setup();let calls=0;
 const error=console.error;console.error=()=>{};
 try{
  await savePracticeSubmission(host,course,unit,['0'],sum,async()=>{if(++calls===1)throw Error('offline');await completeUnit(T.cols,course,unit);},()=>{});
 }finally{console.error=error;}
 assert.equal(records.progress.get(unitKey(course.id,unit.id)).practiceAttempts,1);
 const retry=host.children[0].children[1];assert.equal(retry.textContent,'重试保存');
 await retry.click();
 assert.equal(records.progress.get(unitKey(course.id,unit.id)).practiceAttempts,1);
 assert.equal(records.log.size,1);assert.equal(calls,2);
});

test('a failed score save cannot award completion; retry saves and completes',async()=>{
 const host=setup();let attempts=0,completed=0;
 const doc=T.cols.studyProgress.doc;
 T.cols.studyProgress.doc=id=>{const r=doc(id);return {...r,set:async v=>{if(++attempts===1)throw Error('offline');return r.set(v);}};};
 const error=console.error;console.error=()=>{};
 try{await savePracticeSubmission(host,course,unit,['0'],sum,async()=>{completed++;await completeUnit(T.cols,course,unit);},()=>{});}finally{console.error=error;}
 assert.equal(completed,0);assert.equal(records.log.size,0);
 await host.children[0].children[1].click();
 assert.equal(completed,1);assert.equal(records.progress.get(unitKey(course.id,unit.id)).practiceAttempts,1);
});

