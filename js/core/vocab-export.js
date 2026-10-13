/* 词汇课「不会的词」汇总：纯函数，不碰网络和页面，方便测试。
   输入：每节 {id, title, marks:{词:'know'|'unknown'|''}, items:[{w,ipa,pos,zh,en,...}]}（items 可为空）
   输出：按小节顺序、节内按该节词卡顺序排好的行 */

export function collectUnknown(units){
  const rows = [];
  for(const u of units){
    const marks = u.marks || {};
    const items = u.items || [];
    const byWord = new Map(items.map(it=> [it.w, it]));
    const seen = new Set();
    // 先按词卡顺序，再补上标了但词卡里找不到的词（小节合并过时可能出现）
    for(const it of items){
      if(marks[it.w] === 'unknown'){ rows.push(row(u, it.w, it)); seen.add(it.w); }
    }
    for(const w of Object.keys(marks).sort()){
      if(marks[w] === 'unknown' && !seen.has(w)) rows.push(row(u, w, byWord.get(w)));
    }
  }
  return rows;
}

function row(u, w, it){
  it = it || {};
  return {unitId:u.id, unit:u.title || u.id, w, ipa:it.ipa||'', pos:it.pos||'', zh:it.zh||'', en:it.en||''};
}

/* 复制用：只要单词，逗号隔开 */
export const wordsLine = rows => rows.map(r=> r.w).join(', ');

/* 复制用：每行「词 — 中文释义」 */
export const wordsWithMeaning = rows => rows.map(r=> r.zh ? `${r.w} — ${r.zh}` : r.w).join('\n');

/* 下载用：CSV，前面加 BOM，Excel 打开中文不乱码 */
const q = s => `"${String(s).replace(/"/g, '""')}"`;
export function toCSV(rows){
  const head = ['小节','单词','音标','词性','中文释义','英文释义'];
  const body = rows.map(r=> [r.unit, r.w, r.ipa, r.pos, r.zh, r.en].map(q).join(','));
  return '﻿' + [head.map(q).join(','), ...body].join('\r\n');
}
