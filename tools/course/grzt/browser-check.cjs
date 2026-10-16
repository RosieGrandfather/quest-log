// Local-only browser QA. Firebase is replaced with an in-memory module.
const {chromium}=require(process.env.CODEX_NODE_MODULES+'/playwright');
const fs=require('fs');
const path=require('path');
(async()=>{
 const browser=await chromium.launch({executablePath:'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',headless:true});
 const page=await browser.newPage({viewport:{width:1100,height:900}});
 const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.route('**/js/firebase.js',r=>r.fulfill({contentType:'text/javascript',body:'export const fs={}; export const auth={}; export const FieldValue={};'}));
 await page.route('**/__gre-zt-check',r=>r.fulfill({contentType:'text/html',body:'<html><head><meta charset="utf-8"><link rel="stylesheet" href="/css/base.css"><link rel="stylesheet" href="/css/app.css"><link rel="stylesheet" href="/css/study.css"></head><body><div id="root"></div><div id="toast" hidden></div></body></html>'}));
 await page.goto('http://127.0.0.1:8016/__gre-zt-check');
 const result=await page.evaluate(async()=>{
  const {qsetHTML,wireQset}=await import('/js/study/qset.js');
  const {T}=await import('/js/study/state.js');
  const course=await(await fetch('/courses/gre-zt/course.json')).json();
  const root=document.querySelector('#root');let total=0,writes=0;
  T.cols={studyProgress:{doc:()=>({get:async()=>({data:()=>({})}),set:async()=>{writes++;}})}};
  for(const entry of course.units){
   T.progress={};
   const unit=await(await fetch('/courses/gre-zt/'+entry.file)).json();
   const b=unit.blocks[0];root.innerHTML=qsetHTML(b);wireQset(root,course,unit);
   if(root.querySelectorAll('.qq').length!==7)throw Error(entry.id+' rendering');
   if(root.querySelector('.qorig, .qimg'))throw Error(entry.id+' unexpected original image');
   if([...root.querySelectorAll('.gq-explain')].some(e=>!e.hidden))throw Error('premature answers');
   for(const [i,q]of b.items.entries()){
    for(const [j,k]of q.ans.entries()){
     const name=q.kind==='tc'?`q${i}_${j}`:`q${i}`;
     const input=root.querySelector(`input[name="${name}"][value="${k}"]`);
     if(!input)throw Error(entry.id+' missing input');
     input.click();
    }
    total++;
   }
   root.querySelector('.gbar-submit').click();
   await new Promise(r=>setTimeout(r,15));
   if(root.querySelectorAll('.qq.right').length!==7)throw Error(entry.id+' grading');
   if([...root.querySelectorAll('.gq-explain')].some(e=>e.hidden||!e.textContent.includes('正确答案')))throw Error('answer reveal');
   if(root.querySelector('.explain'))throw Error('unrequested explanation');
  }
  return {sections:course.units.length,questions:total,mockSaves:writes};
 });
 await page.setViewportSize({width:390,height:844});
 await page.evaluate(async()=>{
  const {qsetHTML,wireQset}=await import('/js/study/qset.js');
  const c=await(await fetch('/courses/gre-zt/course.json')).json();
  const u=await(await fetch('/courses/gre-zt/'+c.units[0].file)).json();
  const {T}=await import('/js/study/state.js');T.progress={};
  const root=document.querySelector('#root');root.innerHTML=qsetHTML(u.blocks[0]);wireQset(root,c,u);
 });
 if(process.env.GRE_ZT_SCREENSHOT)await page.screenshot({path:process.env.GRE_ZT_SCREENSHOT,fullPage:true});
 if(errors.length)throw Error(errors.join('\n'));
 console.log(JSON.stringify(result));await browser.close();
})().catch(e=>{console.error(e);process.exit(1);});
